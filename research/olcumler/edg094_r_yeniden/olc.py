"""EDG-2026-094 / EDG-2026-095 ADIM-1 — kapanmış CANLI işlemlerin R çarpanını GİRİŞ RİSKİ
paydasıyla yeniden ölçer.

İKİ KART, TEK KOD YOLU (`--kart`, varsayılan EDG-2026-094 — geriye uyumlu). Hükümler (R1–R6)
ikisinde de AYNIDIR; ayrışan yalnız EŞİKLERDİR ve eşikler artık KARTIN KENDİSİNDEN okunur
(`research/cards/<kart>-*.yaml` `esikler:` bloğu). Selef 094 mutlak `|ΔR| ≤ 0,01` koluyla KALDI;
ardıl 095 aynı soruyu GÖRELİ sorar (`|1 − payda_oran| ≤ 0,05`, küme = benimsemesiz VE plan-stop)
ve iki ölçü ekler: damgalı kontrol asgarisi (`kontrol_asgari_n`; altındaysa PK-1 GEÇMİŞ değil
BİLGİSİZDİR) ve `yazim_kumesi` (ADIM-2'nin yazacağı satırlar — düşük güvenli stop'lular DIŞARIDA).
094 kipinin ÇIKTI YÜZEYİ DONUKTUR: alanları, sıraları ve dosya adı (`sonuc_094_*.json`)
değişmez — regresyonu tests/test_edg095_goreli_ozdeslik_v494.py T5 ölçer.

NE YAPAR. `trades` defterindeki kapanmış canlı satırlar için `r_multiple_giris` =
pnl_dollars / (qty_giris × r_per_share) hesaplanır ve defterdeki eski (bütçe paydalı)
`r_multiple` ile kıyaslanır. HİÇBİR ŞEY YAZILMAZ: bağlantı `file:…?mode=ro` URI'siyle
SALT-OKUR açılır, yazım ADIM-2'nin işidir (ops betiği, Rol-1, bakım penceresi).

OKUYUCUSU KİM (Yasa 6 — okuyucusuz yazım yok). İki artefakt üretilir ve ikisinin de adı konmuş
bir okuyucusu vardır:
  * `sonuc_<kart no>_<UTCts>.json` → ADIM-2 yazım betiği (`ops/r_giris_yeniden_yaz.py`, `--olcum`
    argümanı) onu GİRDİ olarak okur; hangi satıra ne yazılacağı oradan türer.
  * `RAPOR_<kart no>_<UTCts>.md` → Rol-1 hükmü ve kart (ölçümün koştuğu kart dosyası) okur.
Bu betik `research/` altındadır; `meridian` kökünü tarayan statik artefakt grafı buraya
BAKMAZ, yani beyan (DECLARED_SINKS) gerekmez — okuyucu yine de burada ADIYLA yazılıdır.

MERIDIAN İTHAL EDİLMEZ. `meridian.*` ithali gözlem defterine (`obs`) ulaşır ve pytest DIŞINDA
koşan her betik canlı YEREL deftere yazar (CLAUDE.md §2, üç vaka 2026-08-30). Bu yüzden yalnız
standart kütüphane kullanılır. Bedeli: motorun `R_PAYDA_GIRIS` damgası burada KOPYADIR — kopya
sessizce ayrışmasın diye eşitliği tests/test_edg094_r_yeniden_v492.py çivisi ölçer (tek-kaynak
yasası: kopya kaçınılmazsa türetme + ayrışma çivisi).

UYDURMA YASAĞI. Ölçülemeyen her değer `None` + `neden`dir; sıfır ile "bilmiyorum" ayrı alanlarda
durur. Eşikler kartta donmuştur ve buraya KOPYALANMAZ — koşum anında YAML'dan okunur (tek-kaynak
yasası; donuk kopya sessizce ayrışırdı, vaka sınıfı ×3 2026-08-30); TOPLAM HÜKÜM YAZILMAZ
(`hukum` alanı "YOK — Rol-1"), yalnız tetiklenen kill-list kalemleri listelenir.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sqlite3
import statistics

import yaml

#: R PAYDASI DAMGASI — KAYNAĞI motordaki `broker.R_PAYDA_GIRIS` sabitidir. Burada dizge olarak
#: tekrarlanır (yukarıdaki "MERIDIAN İTHAL EDİLMEZ" gerekçesi); ayrışma çivisi v492'dedir.
R_PAYDA_GIRIS = "giris_riski"

#: `trades.kaynak` sütununda BEKLENEN değerler. Bunun dışında bir değer görülürse ölçüm DURUR
#: (R1) — bilinmeyen bir kaynağı sessizce "canlı değil" saymak uydurma olurdu.
BILINEN_KAYNAKLAR = ("live_paper", "replay_seed")

#: KART DİZİNİ — eşiklerin TEK KAYNAĞI. Buradaki YAML koşum anında okunur; kodda donuk eşik
#: sözlüğü YOKTUR (eskiden vardı ve kartla ayrışma riski taşıyordu — ardıl dilim onu kaldırdı).
KART_DIZINI = pathlib.Path(__file__).resolve().parents[2] / "cards"

#: `--kart` verilmezse bu kart koşar. GERİYE UYUMLULUK: v492'nin bütün çağrı yerleri ve
#: operatörün eski komut satırı 094 kipini bekler.
VARSAYILAN_KART = "EDG-2026-094"

#: YAZIM KÜMESİ BİLDİREN KARTLAR. `yazim_kumesi` alanı ADIM-2'nin hedef listesidir ve yalnız
#: onu kill-list'inde TANIMLAYAN kart için üretilir (EDG-2026-095 kill-list 5: düşük güvenli
#: stop'lu satırlar yazım kümesine girmez). 094'e eklemek onun DONUK çıktı yüzeyini bozardı.
YAZIM_KUMESI_KARTLARI = frozenset({"EDG-2026-095"})

#: DÜŞÜK GÜVEN ETİKETİ — `GUVEN` sözlüğünün koruma_oco değeri. Yazım kümesi bu etikete göre
#: budanır; ops betiğindeki eşi aynı dizgeyi kullanır ve eşitliği v494 T7 ölçer.
DUSUK_GUVEN = "dusuk"

#: ROL-1 HÜKÜMLERİ — kartın boş bıraktığı tanımlar, brief'teki SÖZCÜKLERİYLE. Metnin sha256'sı
#: çıktıya yazılır: ölçüm hangi tanım kümesiyle koştuysa o, sonradan yeniden yazılamaz.
HUKUMLER = {
    "R1": ('"canlı" = kaynak == "live_paper"; replay_seed KAPSAM DIŞI (kill-list 4). '
           "Başka kaynak değeri görürsen ölçüm DURUR (hata, uydurma yok)."),
    "R2": ("qty_giris = TSK-187 qty_taban'ın kapanışta alacağı değer: satırın ticker'ı için "
           "ts_open ≤ olay.ts ≤ ts_close penceresinde adet_benimsendi olayı varsa SON olayın "
           "yeni'si (benimsenmis_mi=True, qty_giris_kaynak=\"adet_benimsendi\"), yoksa giriş "
           "adedi = trades.qty (qty_giris_kaynak=\"trades.qty\"; scaled_out=0 olduğu için giriş "
           "adedi = kapanış adedi). SIRA (B3, EDG-2026-095 ardıl dilimi): extra_json.qty_taban "
           "varsa (bugün defterde yok, TSK-187 ile gelir) o BİRİNCİ kaynaktır ve olay yolunun "
           "sağlaması olan çapraz kontrol UYGULANMAZ — qty_taban motorun kendi kaydıdır, olay "
           "çıkarımının doğrulamasına ihtiyacı yoktur. Çapraz kontrol YALNIZ OLAY YOLUNDA: "
           "qty_taban yokken benimsenmişte SON yeni == trades.qty olmalı; tutmuyorsa satır "
           "olculemedi + neden \"benimseme yeni≠qty\"."),
    "R3": ("r_per_share = trades.entry − stop (motor tanımı: fill − stop). stop kaynağı sırası: "
           "(a) trade_plans.stop (plan_id eşleşmesi) → stop_kaynak=\"plan\"; (b) olaylarda "
           "ticker + pencere içindeki İLK mirror_trail_synced.from_stop → \"trail_from_stop\"; "
           "(c) İLK koruma_oco_gonderildi.stop → \"koruma_oco\" (giriş stop'u olmayabilir; "
           "guven=\"dusuk\"); (d) yok → olculemedi + neden \"stop yok\". Kaynak ve güven satıra "
           "yazılır."),
    "R4": ("r_eski = trades.r_multiple; r_yeni = pnl_dollars / (qty_giris × r_per_share); "
           "dR = r_yeni − r_eski; dR_oran = |dR| / |r_eski| (r_eski=0 ise None). Ek teşhis "
           "sütunu: payda_eski_ima = pnl_dollars / r_eski (r_eski≠0) ve payda_oran = "
           "payda_eski_ima / (qty_giris × r_per_share). Bu sütunlar eşik DEĞİLDİR, Rol-1 "
           "hükmüne girdidir."),
    "R5": ("Eşikler KARTTAN okunur (sayı burada TEKRARLANMAZ — tek kaynak kart YAML'ı): "
           "benimsenmiş medyan dR_oran alt sınırı; benimsemesiz özdeşlik toleransı (094 MUTLAK "
           "|dR|, 095 GÖRELİ |1 − payda_oran| ve küme = benimsemesiz VE stop_kaynak==\"plan\"); "
           "ölçülemeyen üst oranı; PK-1 eşitlik toleransı; (095) PK-1 asgari damgalı satır "
           "sayısı. Sonuç JSON'da her eşik için deger, esik, yon, n, gecti (bool|None) alanları; "
           "toplam hüküm YAZMA (hüküm Rol-1'in) — yalnız kill_list_tetik listesi."),
    "R6": ("PK-1 (damgalı gerçek satır eşitliği): bugün gerçek veride n=0 → sonuçta "
           "pk1: {n:0, gecti:null, neden:\"damgalı kapanmış işlem yok\"}; 095 kipinde kart "
           "`kontrol_asgari_n` koyduğu için aynı durum \"damgalı satır < asgari\" nedenine ve "
           "kill_list_tetik'te \"PK-1 n=0 → bilgisiz, yazım YOK\" kalemine düşer — GEÇMİŞ değil "
           "BİLGİSİZ. Hesap yolu SENTETİK damgalı satırla testte doğrulanır. PK-2 sentetik iki "
           "vaka testte. PK-3 = ADIM-2 betiğinin kuru koşumu."),
}

#: BRIEF'İN DOLDURMADIĞI İKİ BOŞLUK, AÇIKÇA (uydurma yasağı — sessiz varsayım yerine yazılı not):
#: (1) `guven` sözlüğü: plan → "yuksek", trail_from_stop → "orta", koruma_oco → "dusuk". Brief
#:     yalnız (c) için "dusuk" diyor; diğer ikisine ad verilmeliydi, verildi ve burada durur.
#: (2) payda ≤ 0 (r_per_share ≤ 0 ya da qty_giris ≤ 0) → satır `olculemedi`. Sıfıra bölmek ya da
#:     0.0 yazmak ÖLÇÜM DEĞİLDİR; motor da aynı durumda damgayı `olculemedi` yapar.
GUVEN = {"plan": "yuksek", "trail_from_stop": "orta", "koruma_oco": "dusuk"}


# ---------------------------------------------------------------------------
# yardımcılar
# ---------------------------------------------------------------------------
def sha256_dosya(yol) -> str:
    """Dosyanın sha256'sı (künye için). Büyük DB kopyası da parça parça okunur."""
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def kart_yolu(kart_id: str) -> pathlib.Path:
    """`EDG-2026-095` → `research/cards/EDG-2026-095-*.yaml`. TAM BİR eşleşme yoksa ölçüm DURUR:
    yanlış karttan eşik okumak, eşiği sonradan değiştirmenin sessiz hâli olurdu."""
    adaylar = sorted(KART_DIZINI.glob(f"{kart_id}-*.yaml"))
    if len(adaylar) != 1:
        raise ValueError(
            f"kart dosyası TEK olmalı — `{kart_id}` için {len(adaylar)} eşleşme bulundu "
            f"({[a.name for a in adaylar]}), dizin: {KART_DIZINI}")
    return adaylar[0]


def esikler_oku(kart_id: str = VARSAYILAN_KART) -> dict:
    """Kartın `esikler:` bloğu — ölçümün TEK eşik kaynağı. Blok yoksa ölçüm DURUR (eşiksiz
    ölçüm hüküm üretemez; boş sözlükle koşmak "hepsi geçti" yanılsaması verirdi)."""
    yol = kart_yolu(kart_id)
    with open(yol, "r", encoding="utf-8") as f:
        kart = yaml.safe_load(f)
    esikler = (kart or {}).get("esikler") if isinstance(kart, dict) else None
    if not isinstance(esikler, dict) or not esikler:
        raise ValueError(f"kartta `esikler:` bloğu YOK ya da boş: {yol}")
    return esikler


def hukum_sha() -> str:
    """R1–R6 metninin sha256'sı — ölçümün hangi tanım kümesiyle koştuğunun damgası."""
    ham = json.dumps(HUKUMLER, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(ham.encode("utf-8")).hexdigest()


def gun(ts):
    """Zaman damgasının GÜN parçası (ilk 10 karakter) ya da None.

    Pencere kıyası neden gün düzeyinde: `trades.ts_open`/`ts_close` GÜN dizgesidir
    ("2026-08-31"), olay `ts`'i tam ISO damgadır ("2026-08-31T20:54:30+00:00"). Ham dizge
    kıyası kapanış GÜNÜNDE düşen bir olayı sessizce pencere DIŞI sayardı (dizge olarak
    "2026-08-31T20:54:30+00:00" > "2026-08-31"), yani benimsemeyi kaçırırdı.
    """
    if ts is None:
        return None
    m = str(ts)
    return m[:10] if len(m) >= 10 else m


def pencerede_mi(olay_ts, ts_open, ts_close) -> bool:
    """Olay, işlemin [ts_open, ts_close] GÜN penceresinde mi (iki uç dahil)?"""
    o, a, k = gun(olay_ts), gun(ts_open), gun(ts_close)
    if o is None or a is None or k is None:
        return False
    return a <= o <= k


def _f(x):
    """Sayıya çevir ya da None döndür — dizge/None karışık defter alanları için."""
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):   # sessiz-yutma: sayıya çevrilemeyen alan ÖLÇÜLEMEZ; None döner ve çağıran `neden` yazar
        return None


def extra_oku(ham) -> dict:
    """`extra_json` metnini sözlüğe çevirir. Bozuk/boş JSON boş sözlüktür ve bu bir ÖLÇÜMDÜR:
    alan yokluğu ile alan-değeri-None ayrı sorulardır (`.get` None ≠ anahtar yok dersi)."""
    if not ham:
        return {}
    try:
        veri = json.loads(ham)
    except (TypeError, ValueError):   # sessiz-yutma: bozuk extra_json satırı düşürmez, alanları YOK sayılır ve neden satıra yazılır
        return {}
    return veri if isinstance(veri, dict) else {}


def olaylari_oku(yol) -> list:
    """Olay çıkarımı JSON listesi (ts'e göre sıralı kopya döner)."""
    with open(yol, "r", encoding="utf-8") as f:
        veri = json.load(f)
    if not isinstance(veri, list):
        raise ValueError(f"olay dosyası JSON LİSTE olmalı: {yol}")
    return sorted(veri, key=lambda e: str(e.get("ts") or ""))


def olaylari_sec(olaylar, ad, ticker, ts_open, ts_close) -> list:
    """`ad` türünden, `ticker`a ait, pencere içindeki olaylar — ts sırasıyla."""
    return [e for e in olaylar
            if e.get("event") == ad and e.get("ticker") == ticker
            and pencerede_mi(e.get("ts"), ts_open, ts_close)]


# ---------------------------------------------------------------------------
# R2 — giriş adedi
# ---------------------------------------------------------------------------
def qty_giris_olc(trade: dict, extra: dict, olaylar: list) -> dict:
    """R2: qty_giris + kaynağı + benimsenmiş mi + (varsa) neden."""
    benimsemeler = olaylari_sec(olaylar, "adet_benimsendi", trade.get("ticker"),
                                trade.get("ts_open"), trade.get("ts_close"))
    benimsenmis = bool(benimsemeler)
    son_yeni = _f(benimsemeler[-1].get("yeni")) if benimsemeler else None
    qty = _f(trade.get("qty"))

    # KART SIRASI — B3 (EDG-2026-095 ardıl dilimi, inceleme bulgusu 2026-09-14): extra_json.
    # qty_taban BİRİNCİ kaynaktır ve bu dal ÇAPRAZ KONTROLDEN ÖNCE gelir. Gerekçe: qty_taban
    # motorun kapanışta yazdığı KENDİ kaydıdır; olay çıkarımının (adet_benimsendi) doğrulamasına
    # ihtiyacı yoktur. Eski sıra çapraz kontrolü qty_taban VARKEN de uygulayıp, motorun kaydı
    # elde dururken satırı "ölçülemedi" yapabilirdi — bilgi varken bilgisizlik beyanı.
    if "qty_taban" in extra:
        taban = _f(extra.get("qty_taban"))
        if taban is not None and taban > 0:
            return {"qty_giris": taban, "qty_giris_kaynak": "extra_json.qty_taban",
                    "benimsenmis_mi": benimsenmis, "neden": None}

    # ÇAPRAZ KONTROL (R2) — YALNIZ OLAY YOLUNDA: benimsenmiş satırda SON `yeni` defterdeki qty
    # ile aynı olmalı. scaled_out=0 olduğu için giriş adedi = kapanış adedi; tutmazsa hangi
    # sayının doğru olduğunu BİLMİYORUZ ve satır ölçülemedi olur (uydurma yasağı).
    if benimsenmis and (son_yeni is None or qty is None or son_yeni != qty):
        return {"qty_giris": None, "qty_giris_kaynak": None, "benimsenmis_mi": True,
                "neden": "benimseme yeni≠qty"}

    if benimsenmis:
        return {"qty_giris": son_yeni, "qty_giris_kaynak": "adet_benimsendi",
                "benimsenmis_mi": True, "neden": None}

    if qty is None or qty <= 0:
        return {"qty_giris": None, "qty_giris_kaynak": None, "benimsenmis_mi": False,
                "neden": "qty yok"}
    return {"qty_giris": qty, "qty_giris_kaynak": "trades.qty",
            "benimsenmis_mi": False, "neden": None}


# ---------------------------------------------------------------------------
# R3 — stop ve hisse-başı risk
# ---------------------------------------------------------------------------
def stop_olc(trade: dict, plan: dict | None, olaylar: list) -> dict:
    """R3: stop + kaynağı + güveni. Sıra: plan → trail from_stop → koruma_oco → yok."""
    if plan is not None:
        s = _f(plan.get("stop"))
        if s is not None:
            return {"stop": s, "stop_kaynak": "plan", "guven": GUVEN["plan"], "neden": None}

    trailler = olaylari_sec(olaylar, "mirror_trail_synced", trade.get("ticker"),
                            trade.get("ts_open"), trade.get("ts_close"))
    for e in trailler:                       # İLK sync'in from_stop'u = o ana kadarki stop
        s = _f(e.get("from_stop"))
        if s is not None:
            return {"stop": s, "stop_kaynak": "trail_from_stop",
                    "guven": GUVEN["trail_from_stop"], "neden": None}

    korumalar = olaylari_sec(olaylar, "koruma_oco_gonderildi", trade.get("ticker"),
                             trade.get("ts_open"), trade.get("ts_close"))
    for e in korumalar:                      # koruma emri GİRİŞ stop'u olmayabilir → güven düşük
        s = _f(e.get("stop"))
        if s is not None:
            return {"stop": s, "stop_kaynak": "koruma_oco",
                    "guven": GUVEN["koruma_oco"], "neden": None}

    return {"stop": None, "stop_kaynak": None, "guven": None, "neden": "stop yok"}


# ---------------------------------------------------------------------------
# satır ölçümü
# ---------------------------------------------------------------------------
def satiri_olc(trade: dict, plan: dict | None, olaylar: list) -> dict:
    """Bir `trades` satırı → ölçüm satırı (R2 + R3 + R4). Ölçülemeyen değer None + neden."""
    extra = extra_oku(trade.get("extra_json"))
    out = {
        "seq": trade.get("seq"), "id": trade.get("id"), "ticker": trade.get("ticker"),
        "ts_open": trade.get("ts_open"), "ts_close": trade.get("ts_close"),
        "qty": trade.get("qty"), "entry": _f(trade.get("entry")),
        "pnl_dollars": _f(trade.get("pnl_dollars")),
        "damgali_mi": extra.get("r_payda") == R_PAYDA_GIRIS,
        "qty_giris": None, "qty_giris_kaynak": None, "benimsenmis_mi": False,
        "stop": None, "stop_kaynak": None, "guven": None, "r_per_share": None,
        "r_eski": _f(trade.get("r_multiple")), "r_yeni": None, "dR": None, "dR_oran": None,
        "payda": None, "payda_eski_ima": None, "payda_oran": None,
        "olculebildi": False, "neden": None,
    }

    adet = qty_giris_olc(trade, extra, olaylar)
    out["qty_giris"] = adet["qty_giris"]
    out["qty_giris_kaynak"] = adet["qty_giris_kaynak"]
    out["benimsenmis_mi"] = adet["benimsenmis_mi"]

    st = stop_olc(trade, plan, olaylar)
    out["stop"], out["stop_kaynak"], out["guven"] = st["stop"], st["stop_kaynak"], st["guven"]
    if out["entry"] is not None and out["stop"] is not None:
        out["r_per_share"] = out["entry"] - out["stop"]

    for neden in (adet["neden"], st["neden"]):
        if neden and out["neden"] is None:
            out["neden"] = neden
    if out["neden"] is not None:
        return out
    if out["r_per_share"] is None:
        out["neden"] = "stop yok"
        return out
    if out["pnl_dollars"] is None:
        out["neden"] = "pnl_dollars yok"
        return out
    if out["r_eski"] is None:
        out["neden"] = "r_multiple yok"
        return out

    payda = out["qty_giris"] * out["r_per_share"]
    out["payda"] = payda
    if payda <= 0:
        out["neden"] = "payda ≤ 0"
        return out

    out["r_yeni"] = out["pnl_dollars"] / payda
    out["dR"] = out["r_yeni"] - out["r_eski"]
    if out["r_eski"] != 0:
        out["dR_oran"] = abs(out["dR"]) / abs(out["r_eski"])
        out["payda_eski_ima"] = out["pnl_dollars"] / out["r_eski"]
        out["payda_oran"] = out["payda_eski_ima"] / payda
    out["olculebildi"] = True
    return out


# ---------------------------------------------------------------------------
# okuma + özet
# ---------------------------------------------------------------------------
def trades_oku(con: sqlite3.Connection, kaynak: str) -> list:
    """R1: kaynak sütunu DOĞRULANIR, sonra yalnız istenen kaynağın satırları döner."""
    con.row_factory = sqlite3.Row
    gorulen = sorted({r[0] for r in con.execute("SELECT DISTINCT kaynak FROM trades")
                      if r[0] is not None})
    bilinmeyen = [k for k in gorulen if k not in BILINEN_KAYNAKLAR]
    if bilinmeyen:
        raise ValueError(
            f"R1 DURDU — `trades.kaynak` bilinmeyen değer(ler) taşıyor: {bilinmeyen}. "
            f"Bilinen küme: {list(BILINEN_KAYNAKLAR)}. Kapsamı tahmin etmek uydurma olurdu.")
    return [dict(r) for r in
            con.execute("SELECT * FROM trades WHERE kaynak = ? ORDER BY seq", (kaynak,))]


def planlari_oku(con: sqlite3.Connection) -> dict:
    """plan_id → plan satırı haritası."""
    con.row_factory = sqlite3.Row
    return {r["id"]: dict(r) for r in con.execute("SELECT * FROM trade_plans")
            if r["id"] is not None}


def ozetle(satirlar: list, kart_esikleri: dict, yazim_kumesi_yaz: bool = False) -> dict:
    """R5 + R6: eşik alanları, PK-1 ve tetiklenen kill-list kalemleri. HÜKÜM YOK.

    HANGİ EŞİK ÖLÇÜLÜR SORUSUNU KART CEVAPLAR: çıktıdaki eşik bloğu `kart_esikleri`nde BULUNAN
    anahtarlardan türer. Bu yüzden 094 (mutlak özdeşlik kolu) ile 095 (göreli kol + damgalı
    kontrol asgarisi) aynı koddan, kendi kartlarının söylediği ölçülerle çıkar; kartta olmayan
    bir ölçü çıktıya da GİRMEZ (094'ün çıktı yüzeyi bu sayede DONUK kalır)."""
    n = len(satirlar)
    olculen = [s for s in satirlar if s["olculebildi"]]
    olculemeyen = [s for s in satirlar if not s["olculebildi"]]
    benimsenmis = [s for s in olculen if s["benimsenmis_mi"]]
    benimsemesiz = [s for s in olculen if not s["benimsenmis_mi"]]

    oranlar = [s["dR_oran"] for s in benimsenmis if s["dR_oran"] is not None]
    medyan = statistics.median(oranlar) if oranlar else None
    max_abs_dR = max((abs(s["dR"]) for s in benimsemesiz if s["dR"] is not None), default=None)
    olculemeyen_oran = (len(olculemeyen) / n) if n else None

    # GÖRELİ ÖZDEŞLİK KÜMESİ (095): benimsemesiz VE stop'u PLANDAN gelen satırlar. Düşük güvenli
    # (koruma_oco) ve orta güvenli (trail) stop'lar dışarıdadır — kartın adım-1 metni: "düşük
    # güvenli stop'lu satırlar özdeşlik kümesine ve YAZIM kümesine girmez (ayrı sayılır)".
    goreli_kume = [s for s in benimsemesiz if s["stop_kaynak"] == "plan"]
    goreli_sapmalar = [abs(1.0 - s["payda_oran"]) for s in goreli_kume
                       if s["payda_oran"] is not None]
    max_goreli = max(goreli_sapmalar, default=None)

    damgalilar = [s for s in satirlar if s["damgali_mi"]]
    damgali_olculen = [s for s in damgalilar if s["olculebildi"] and s["r_eski"] is not None]
    pk1_farklar = [abs(s["r_yeni"] - s["r_eski"]) for s in damgali_olculen]
    if not damgalilar:
        pk1 = {"n": 0, "gecti": None, "neden": "damgalı kapanmış işlem yok", "max_fark": None}
    elif len(damgali_olculen) != len(damgalilar):
        pk1 = {"n": len(damgalilar), "gecti": None,
               "neden": "damgalı satırların bir kısmı ölçülemedi",
               "max_fark": max(pk1_farklar) if pk1_farklar else None}
    else:
        mf = max(pk1_farklar)
        pk1 = {"n": len(damgalilar), "gecti": mf <= kart_esikleri["kontrol_esitlik_tol"],
               "neden": None, "max_fark": mf}

    # ASGARİ DAMGALI SATIR (095): eşiğin altındaki n, "geçti" DEĞİL "bilgisiz"dir. Sıfır ile
    # bilmiyorum ayrı şeylerdir; asgari altındaki bir eşitlik ölçümü hesap yolunu DOĞRULAMAZ.
    asgari = kart_esikleri.get("kontrol_asgari_n")
    asgari_eksik = asgari is not None and pk1["n"] < asgari
    if asgari_eksik:
        pk1 = dict(pk1, gecti=None, neden="damgalı satır < asgari")

    esikler = {}
    if "benimsenmis_ayrisma_medyan_alt" in kart_esikleri:
        alt = kart_esikleri["benimsenmis_ayrisma_medyan_alt"]
        esikler["benimsenmis_ayrisma_medyan_alt"] = {
            "deger": medyan, "esik": alt, "yon": ">=", "n": len(oranlar),
            "gecti": None if medyan is None else medyan >= alt}
    if "benimsemesiz_ozdeslik_tol" in kart_esikleri:          # 094: MUTLAK |ΔR|
        tol = kart_esikleri["benimsemesiz_ozdeslik_tol"]
        esikler["benimsemesiz_ozdeslik_tol"] = {
            "deger": max_abs_dR, "esik": tol, "yon": "<=", "n": len(benimsemesiz),
            "gecti": None if max_abs_dR is None else max_abs_dR <= tol}
    if "benimsemesiz_goreli_ozdeslik_tol" in kart_esikleri:   # 095: GÖRELİ |1 − payda_oran|
        tol = kart_esikleri["benimsemesiz_goreli_ozdeslik_tol"]
        esikler["benimsemesiz_goreli_ozdeslik_tol"] = {
            "deger": max_goreli, "esik": tol, "yon": "<=", "n": len(goreli_kume),
            "gecti": None if max_goreli is None else max_goreli <= tol}
    if "olculemeyen_ust_oran" in kart_esikleri:
        ust = kart_esikleri["olculemeyen_ust_oran"]
        esikler["olculemeyen_ust_oran"] = {
            "deger": olculemeyen_oran, "esik": ust, "yon": "<=", "n": n,
            "gecti": None if olculemeyen_oran is None else olculemeyen_oran <= ust}
    if "kontrol_esitlik_tol" in kart_esikleri:
        esikler["kontrol_esitlik_tol"] = {
            "deger": pk1["max_fark"], "esik": kart_esikleri["kontrol_esitlik_tol"], "yon": "<=",
            "n": pk1["n"], "gecti": pk1["gecti"]}
    if asgari is not None:
        esikler["kontrol_asgari_n"] = {
            "deger": pk1["n"], "esik": asgari, "yon": ">=", "n": pk1["n"],
            "gecti": pk1["n"] >= asgari}

    tetik = []
    if pk1["gecti"] is False:
        tetik.append("PK-1 (damgalı satır eşitliği) tutmadı → hesap yolu bozuk, yazım YOK")
    if asgari_eksik:
        tetik.append(f"PK-1 n={pk1['n']} → bilgisiz, yazım YOK")
    if esikler.get("benimsemesiz_ozdeslik_tol", {}).get("gecti") is False:
        tetik.append("benimsemesiz işlemlerde özdeşlik bozuldu → payda/veri kusuru, yazım YOK")
    if esikler.get("benimsemesiz_goreli_ozdeslik_tol", {}).get("gecti") is False:
        tetik.append("benimsemesiz plan-stop satırlarda göreli özdeşlik bozuldu → payda/veri "
                     "kusuru, yazım YOK")
    if esikler.get("olculemeyen_ust_oran", {}).get("gecti") is False:
        tetik.append("ölçülemeyen payı > %10 → yazım YOK (yarım alan, kıyas kirletir)")

    ozet = {
        "n": n, "benimsenmis_n": len(benimsenmis), "benimsemesiz_n": len(benimsemesiz),
        "olculen_n": len(olculen), "olculemeyen_n": len(olculemeyen),
        "olculemeyen_oran": olculemeyen_oran,
        "benimsenmis_medyan_dR_oran": medyan, "benimsemesiz_max_abs_dR": max_abs_dR,
        "esikler": esikler, "pk1": pk1, "kill_list_tetik": tetik,
    }
    if yazim_kumesi_yaz:
        # ADIM-2'NİN HEDEF LİSTESİ + BEDELİ: dışlanan düşük güvenli satır sayısı da yazılır,
        # çünkü kazanç ölçülüp bedel ölçülmezse körlüğün belirtisi hiçbir şeydir (bedel yasası).
        yazilacak = [s for s in olculen if s["guven"] != DUSUK_GUVEN]
        ozet["yazim_kumesi"] = {
            "seq": [s["seq"] for s in yazilacak], "n": len(yazilacak),
            "dislanan_dusuk_guven_n": len(olculen) - len(yazilacak)}
    return ozet


def olc(db_yolu, olaylar_yolu, kaynak: str = "live_paper", on_dokum_yolu=None,
        kart: str = VARSAYILAN_KART) -> dict:
    """Tam ölçüm: künye + satırlar + özet. DB SALT-OKUR açılır. Eşikler `kart`tan okunur."""
    kart_esikleri = esikler_oku(kart)
    db_yolu = pathlib.Path(db_yolu)
    olaylar_yolu = pathlib.Path(olaylar_yolu)
    olaylar = olaylari_oku(olaylar_yolu)

    con = sqlite3.connect(f"file:{db_yolu}?mode=ro", uri=True)
    try:
        trades = trades_oku(con, kaynak)
        planlar = planlari_oku(con)
    finally:
        con.close()

    satirlar = [satiri_olc(t, planlar.get(t.get("plan_id")), olaylar) for t in trades]

    kunye = {
        "db": {"yol": str(db_yolu), "sha256": sha256_dosya(db_yolu), "rol": "ölçüm girdisi"},
        "olaylar": {"yol": str(olaylar_yolu), "sha256": sha256_dosya(olaylar_yolu),
                    "rol": "ölçüm girdisi"},
    }
    if on_dokum_yolu:
        on_dokum_yolu = pathlib.Path(on_dokum_yolu)
        kunye["on_dokum"] = {"yol": str(on_dokum_yolu), "sha256": sha256_dosya(on_dokum_yolu),
                             "rol": "oryantasyon (ölçüme GİRMEZ)"}

    return {
        "kart_id": kart, "adim": "ADIM-1 ölçüm (salt-okur)",
        "kaynak_suzgeci": kaynak, "olculdu_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "girdi_kunyesi": kunye,
        "hukumler": HUKUMLER, "hukumler_sha256": hukum_sha(),
        "r_payda_giris": R_PAYDA_GIRIS,
        "satirlar": satirlar,
        "ozet": ozetle(satirlar, kart_esikleri, kart in YAZIM_KUMESI_KARTLARI),
        "hukum": "YOK — Rol-1",
    }


# ---------------------------------------------------------------------------
# rapor
# ---------------------------------------------------------------------------
def _g(x, basamak=4):
    """Rapor hücresi: None ise em-dash, sayıysa yuvarlanmış. JSON'da DEĞER YUVARLANMAZ."""
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "evet" if x else "hayır"
    if isinstance(x, float):
        return f"{x:.{basamak}f}"
    return str(x)


def rapor_metni(sonuc: dict) -> str:
    """RAPOR gövdesi (okuyucu: Rol-1 hükmü + ölçümün koştuğu kart)."""
    oz = sonuc["ozet"]
    sut = ("id", "ticker", "ts_close", "qty", "qty_giris", "qty_giris_kaynak", "stop_kaynak",
           "r_eski", "r_yeni", "dR", "dR_oran", "payda_oran", "benimsenmis_mi")
    satir = [f"# {sonuc['kart_id']} ADIM-1 — R paydası GİRİŞ RİSKİ ile yeniden ölçüm",
             "",
             f"Ölçüm: {sonuc['olculdu_utc']} · kaynak süzgeci: `{sonuc['kaynak_suzgeci']}` · "
             f"hüküm metni sha256: `{sonuc['hukumler_sha256'][:16]}…`",
             "",
             "HÜKÜM BU BELGEDE YOK — Rol-1'indir. Aşağısı ölçümdür.",
             "",
             "## Girdi künyesi", ""]
    for ad, k in sonuc["girdi_kunyesi"].items():
        satir.append(f"- **{ad}** ({k['rol']}): `{k['yol']}` · sha256 `{k['sha256']}`")
    satir += ["", "## İşlem tablosu", "",
              "| " + " | ".join(sut) + " |",
              "|" + "|".join(["---"] * len(sut)) + "|"]
    for s in sonuc["satirlar"]:
        satir.append("| " + " | ".join(_g(s.get(k)) for k in sut) + " |")

    satir += ["", "## Özet", "",
              f"- n = {oz['n']} · benimsenmiş {oz['benimsenmis_n']} · "
              f"benimsemesiz {oz['benimsemesiz_n']} · ölçülemeyen {oz['olculemeyen_n']} "
              f"(oran {_g(oz['olculemeyen_oran'])})",
              f"- benimsenmiş medyan dR_oran = {_g(oz['benimsenmis_medyan_dR_oran'])}",
              f"- benimsemesiz max |dR| = {_g(oz['benimsemesiz_max_abs_dR'])}",
              "", "### Eşikler (kart)", "",
              "| eşik | değer | yön | eşik değeri | n | geçti |",
              "|---|---|---|---|---|---|"]
    for ad, e in oz["esikler"].items():
        gecti = "—" if e["gecti"] is None else ("EVET" if e["gecti"] else "HAYIR")
        satir.append(f"| {ad} | {_g(e['deger'])} | {e['yon']} | {e['esik']} | {e['n']} | {gecti} |")

    pk1 = oz["pk1"]
    satir += ["", "### PK-1 (damgalı satır eşitliği)", "",
              f"- n = {pk1['n']} · geçti = "
              f"{'—' if pk1['gecti'] is None else ('EVET' if pk1['gecti'] else 'HAYIR')} · "
              f"max fark = {_g(pk1['max_fark'], 6)}"
              + (f" · neden: {pk1['neden']}" if pk1["neden"] else "")]
    if "yazim_kumesi" in oz:
        yk = oz["yazim_kumesi"]
        satir += ["", "## Yazım kümesi (ADIM-2 hedefleri)", "",
                  f"- yazılacak satır: {yk['n']} · seq: "
                  + (", ".join(str(s) for s in yk["seq"]) if yk["seq"] else "—"),
                  f"- dışlanan düşük güvenli (koruma_oco) satır: {yk['dislanan_dusuk_guven_n']}"]
    satir += ["", "### Ölçülemeyenler", ""]
    olcsuz = [s for s in sonuc["satirlar"] if not s["olculebildi"]]
    if not olcsuz:
        satir.append("- yok")
    for s in olcsuz:
        satir.append(f"- `{s['id']}` {s['ticker']} ({s['ts_close']}): {s['neden']}")

    satir += ["", "### Tetiklenen kill-list kalemleri", ""]
    if not oz["kill_list_tetik"]:
        satir.append("- yok")
    for t in oz["kill_list_tetik"]:
        satir.append(f"- {t}")
    satir.append("")
    return "\n".join(satir)


# ---------------------------------------------------------------------------
# komut satırı
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="EDG-2026-094 / EDG-2026-095 ADIM-1: canlı trades satırlarının R'sini giriş "
                    "riski paydasıyla yeniden ölçer (SALT-OKUR).")
    ap.add_argument("--db", required=True, help="sqlite defter kopyası (salt-okur açılır)")
    ap.add_argument("--olaylar", required=True, help="olay çıkarımı JSON listesi")
    ap.add_argument("--cikti", required=True, help="çıktı dizini (sonuc + RAPOR buraya)")
    ap.add_argument("--kaynak", default="live_paper", help="trades.kaynak süzgeci (R1)")
    ap.add_argument("--kart", default=VARSAYILAN_KART,
                    help="eşiklerin okunacağı kart kimliği (örn. EDG-2026-095); kart dosyası "
                         f"{KART_DIZINI} altında TEK eşleşme vermeli")
    ap.add_argument("--on-dokum", default=None,
                    help="oryantasyon dökümü (yalnız künyeye yazılır, ölçüme GİRMEZ)")
    a = ap.parse_args(argv)

    sonuc = olc(a.db, a.olaylar, a.kaynak, a.on_dokum, a.kart)
    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # DOSYA ADI KART NUMARASINI TAŞIR: iki kartın çıktısı aynı dizinde karışmaz ve ops betiğinin
    # `--olcum` girdisi (`sonuc_094_*.json`) eski adıyla yerinde kalır.
    kart_no = a.kart.rsplit("-", 1)[-1]
    dizin = pathlib.Path(a.cikti)
    dizin.mkdir(parents=True, exist_ok=True)
    js = dizin / f"sonuc_{kart_no}_{damga}.json"
    md = dizin / f"RAPOR_{kart_no}_{damga}.md"
    js.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    md.write_text(rapor_metni(sonuc), encoding="utf-8")
    print(f"sonuc: {js}")
    print(f"rapor: {md}")
    oz = sonuc["ozet"]
    print(f"n={oz['n']} benimsenmis={oz['benimsenmis_n']} olculemeyen={oz['olculemeyen_n']} "
          f"kill_list_tetik={len(oz['kill_list_tetik'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
