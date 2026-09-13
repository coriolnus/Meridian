"""ops/dolum_geri_dolum.py — TSK-182: geçmiş `live_paper` işlemlerinin BOŞ dolum alanlarının
Alpaca kapalı-emir geçmişinden GERİ DOLUMU (as-of damgalı, yalnız boş alana, tek transaction).

ÖLÇÜLEN HÂL (Rol-1, A1 2026-09-13). `trades` tablosunda kaynak=`live_paper` 24 satırın 13'ünde
`extra_json.dolum_ts` YOK: 8 Ağustos işlemi (08-06…08-20) çıkış dolum-yamasının görünürlük alanı
doğmadan ÖNCE kapandı (`loop._exit_fill_yamasi` E-kod [5] ile 08-2x'te geldi), 5 Eylül işleminde
`alpaca_fill_price` de yok (yama o satırlarda hiç koşmadı). Sonuç: EDG-2026-069 ADIM-0 DÜŞTÜ
(n_uygun 11 < 30 · `dolum_ts` eksik oranı 0,54 > 0,30) — veri kilidi, kill değil.

NE YAPAR. `--db`deki `trades` tablosunda kaynak damgası `live_paper` olan satırları okur, dolum
alanları BOŞ olanlar için Alpaca'nın KAPALI emir geçmişini (`alpaca.orders(status="closed",
nested=True, after=…)`, sayfalı) tarar ve `plan_id == client_order_id` eşleşmesinden broker
OLGUSUNU satırın `extra_json`una yazar. YALNIZ BOŞ ALANA yazar; dolu alan ASLA ezilmez (broker
farklı bir değer veriyorsa `ayrisma` sınıfıyla RAPORLANIR, yazılmaz).

DÖRT ALAN, İKİ AİLE — ADLAR KODDAN TÜRETİLDİ, UYDURULMADI:
  · ÇIKIŞ dolumu → `dolum_ts` + `alpaca_fill_price`. Bunlar motorun KENDİ yazdığı alanlardır
    (`loop._exit_fill_yamasi` kilitli yamasının anahtarları) ve geri dolum o yamanın geçmişe
    uygulanmasından başka bir şey DEĞİLDİR — başka bir semantik yazmak defterin 11 dolu satırıyla
    13 geri doldurulan satırını sessizce ayrıştırırdı.
  · GİRİŞ dolumu → `giris_dolum_ts` + `giris_dolum_fiyat`. ÖLÇÜM: `trades` satırında giriş dolumu
    için KANONİK BİR ALAN YOKTUR — motor giriş dolumunu AYRI bir deftere yazar
    (`loop.ENTRY_LEDGER`, `loop._patch_entry_slippage`: orada ad `fill`, zaman alanı yine
    `dolum_ts`). O adları buraya taşımak iki defterde aynı ada iki AYRI anlam verirdi
    (`dolum_ts` burada ÇIKIŞ'tır), `fill` ise `trades` satırında hiç yaşamaz. Bu yüzden giriş
    ailesi AYRIK ve KENDİNİ ANLATAN adlar alır.
  · AS-OF damgası → `dolum_kaynak` = `alpaca_orders_geri_dolum_<utc-iso>`. Satırda ZATEN varsa
    KORUNUR (`ledgerstamp.stamp`in "var olan damga ezilmez" yasasıyla aynı sınıf: ilk geri
    dolumun kanıtı sonraki bir koşum tarafından silinmez).

AÇIK KALEM — RAPORDA VE BURADA (Rol-1'e): EDG-2026-069 kartı `dolum_ts`i GİRİŞ dolum anı olarak
okuyor ("tetik kırılma saniyesi ile broker dolum anı arasındaki gecikme"), kod ise o alana ÇIKIŞ
dolumunu yazıyor. Bu betik ayrışmayı ÇÖZMEZ (kart hükmü Rol-1'dedir): iki aileyi de doldurur,
adlarıyla ayırır ve ayrımı raporun başında BEYAN eder. Kartın ölçümü hangi aileyi kullanacaksa
o karar karta yazılmalıdır.

PIT. Geri yazılan şey BROKER OLGUSUDUR (emrin kendi gövdesindeki dolum zamanı/fiyatı), bir HESAP
değil: `mirror_divergence` gibi türetilmiş alanlar BU BETİKTEN YAZILMAZ. `kaynak` kolonuna (=
`ledgerstamp.FIELD`) HİÇ DOKUNULMAZ — SQL yalnız `extra_json` kolonunu günceller ve doğrulama
`kaynak` dahil tüm tipli kolonların değişmediğini ÖLÇER.

OKUMA KURALLARI İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası). Dolum fiyatı/zamanı okuma ölçütü
motorun kendi yüzeylerindedir ve buraya YENİDEN YAZILMAZ: `loop._entry_fill_price` (emrin KENDİ
dolumu — bracket parent'ının girişi ve `DELETE /positions`ın doğurduğu karar-kapatma emri),
`alpaca.exit_fill_price` / `alpaca.exit_fill_ts` (dolan TP/SL bacağı, fiyat ve zaman AYNI bacak
seçimiyle), `alpaca.is_engine_order` (motor sahipliği), `loop._EMIR_PENCERESI_SAYFA_TAVANI`
(sayfa tavanı). Çivi: `tests/test_dolum_geri_dolum_v475.py::test_okuma_kurallari_ITHAL_EDILIR_
kopyalanmaz` — betiğin kaynak metninde dolum fiyatı alan adının ELLE geçmediğini de ölçer.

`meridian.obs`A ULAŞIR — BİLİNÇLİ VE SINIRLI. `ops/` betiklerinin varsayılan kuralı "obs'a ulaşma"
olsa da (pytest dışı koşumda canlı yerel deftere yazar) bu araç `--uygula`da TEK bir olay
(`dolum_geri_dolum`) yazar: canlı deftere yazan bir aracın yazdığını kaydetmemesi daha kötü bir
sessizliktir. KURU KOŞUMDA HİÇ OLAY YAZILMAZ (çivi K1) — kuru koşum canlı defteri kirletmez.

WORKER KAPISI YOK (bilinçli, `trade_id_yeniden_numarala` emsali): `--uygula` öncesi canlı worker'ı
Rol-1 KENDİSİ durdurur (`./ops/stop-worker.sh`); bu betik kilit/healthz kontrolü YAPMAZ, yalnız
bu docstring ve `--uygula` çıktısı bunu söyler.

KULLANIM:
    python ops/dolum_geri_dolum.py --db state/meridian.db                      # KURU (varsayılan)
    python ops/dolum_geri_dolum.py --db state/meridian.db --kuru               # aynı, açık
    python ops/dolum_geri_dolum.py --db state/meridian.db --baslangic 2026-08-01 --tavan 200
    python ops/dolum_geri_dolum.py --db state/meridian.db --uygula \\
        [--yedek-dizin backups]                                                # YAZ

ÇIKIŞ KODU: 0 = kuru koşum tamam / uygulandı (yapacak iş yoksa da 0) · 1 = doğrulama düştü
(ROLLBACK yapıldı, DB değişmedi) ya da beklenmedik hata · 2 = kullanım hatası (DB yok, çelişen kip
bayrağı) · 3 = broker erişilemez (kimlik yok ya da ilk sayfa taşıma arızası — [] "emir yok"
DEĞİLDİR, ARIZADIR).

Çivi: tests/test_dolum_geri_dolum_v475.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

from meridian import obs
from meridian.adapters import alpaca
from meridian.loop import _EMIR_PENCERESI_SAYFA_TAVANI, _entry_fill_price

BETIK_ADI = "ops/dolum_geri_dolum.py"
OLAY = "dolum_geri_dolum"

# ---- İTHAL EDİLEN OKUMA KURALLARI (tek-kaynak; gövde motorun kendi yüzeyindedir) --------------
giris_dolum_fiyati = _entry_fill_price      # emrin KENDİ dolum fiyatı (bracket parent'ı / karar emri)
cikis_dolum_fiyati = alpaca.exit_fill_price  # dolan TP/SL bacağının fiyatı
cikis_dolum_zamani = alpaca.exit_fill_ts     # AYNI bacağın zaman ikizi
motor_emri_mi = alpaca.is_engine_order       # coid sahiplik süzgeci
SAYFA_TAVANI = _EMIR_PENCERESI_SAYFA_TAVANI  # kaç sayfa geriye sayfalanır (tavan aşımı BEYANLI)

# ---- ALAN SÖZLEŞMESİ --------------------------------------------------------------------------
ALAN_CIKIS_TS = "dolum_ts"            # motorun yazdığı ad (`loop._exit_fill_yamasi` yaması)
ALAN_CIKIS_FIYAT = "alpaca_fill_price"
ALAN_GIRIS_TS = "giris_dolum_ts"      # `trades` satırında giriş ailesi için kanonik ad YOKTU
ALAN_GIRIS_FIYAT = "giris_dolum_fiyat"
ALAN_DAMGA = "dolum_kaynak"
ALAN_KAPATMA_EMRI = "close_order_id"  # varsa çıkış "karar" kolundan okunur
HEDEF_ALANLAR = (ALAN_GIRIS_TS, ALAN_GIRIS_FIYAT, ALAN_CIKIS_TS, ALAN_CIKIS_FIYAT)
DAMGA_ONEKI = "alpaca_orders_geri_dolum_"

KAYNAK_KOLONU = "kaynak"              # = ledgerstamp.FIELD — DOKUNULMAZ
CANLI_DAMGA = "live_paper"            # = ledgerstamp.LIVE_PAPER
FIYAT_ONDALIK = 4                     # motor yamasının yuvarlaması ile AYNI


class BrokerErisilemez(RuntimeError):
    """Broker okunamadı — dönen boş liste VERİ DEĞİL ARIZADIR (`alpaca.transport` A1 deseni)."""


# ---- SAF YARDIMCILAR (DB'YE/AĞA DOKUNMAZ) ----------------------------------------------------
def damga(simdi: dt.datetime | None = None) -> str:
    """As-of damgası: önek + ÖLÇÜLEN UTC an (uydurulmaz, `dt.datetime.now(utc)`)."""
    an = simdi or dt.datetime.now(dt.timezone.utc)
    return f"{DAMGA_ONEKI}{an.isoformat(timespec='seconds')}"


def extra_coz(ham: str | None) -> tuple[dict | None, str | None]:
    """`extra_json` → (sözlük, hata). Bozuk/sözlük-olmayan içerik ONARILMAZ: `(None, neden)` döner
    ve çağıran o satıra HİÇ DOKUNMAZ — bozuk bir zarfı yeniden yazmak, taşıdığı serbest alanları
    sessizce düşürme riskidir."""
    if not ham:
        return {}, None
    try:
        veri = json.loads(ham)
    except json.JSONDecodeError as e:  # sessiz-yutma: SESSİZ DEĞİL — neden çağırana DÖNER ve satır 'atlandi' olarak ADIYLA raporlanır; onarım bu aracın kapsamı dışıdır
        return None, f"extra_json çözülemedi ({e.__class__.__name__}) — satıra dokunulmadı"
    if not isinstance(veri, dict):
        return None, f"extra_json sözlük değil ({type(veri).__name__}) — satıra dokunulmadı"
    return veri, None


def _fiyat(ham) -> float | None:
    """Sayıya çevrilebilen değer → float; değilse None (uydurma yasağı: 0 yazılmaz)."""
    if ham in (None, ""):
        return None
    try:
        return float(ham)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek değer; alan None kalır ve kalemin nedeninde görünür — ikame edilmiş bir fiyat sessiz bir yalan olurdu
        return None


def _esit_fiyat(a, b) -> bool:
    fa, fb = _fiyat(a), _fiyat(b)
    if fa is None or fb is None:
        return False
    return round(fa, FIYAT_ONDALIK) == round(fb, FIYAT_ONDALIK)


def canli_mi(satir: dict, extra: dict | None) -> bool:
    """Satır canlı kâğıt damgası taşıyor mu? `storage._cols_to_row` okuma kuralıyla AYNI: varsa
    `extra_json` KAZANIR (tipli kolon sorgulanabilirlik içindir, doğruluk kaynağı değil)."""
    deger = (extra or {}).get(KAYNAK_KOLONU, satir.get(KAYNAK_KOLONU))
    return deger == CANLI_DAMGA


# ---- BROKER OKUMASI --------------------------------------------------------------------------
def emirleri_cek(alpaca_mod, baslangic: str, tavan: int) -> tuple[list, dict]:
    """KAPALI emirleri sayfalı çek (en yeniden geriye). Dönüş: (emirler, pencere özeti).

    Sayfalama `loop._alpaca_emir_penceresi` deseninin AYNISIDIR ama o fonksiyon İTHAL EDİLMEZ:
    sözleşmesi farklıdır (`status="all"`, `after` yok) ve kapsanamayan pencerede KENDİSİ
    `obs.warn` atar — bu araç kuru koşumda olay YAZMAMAK zorundadır. Beyan bu yüzden olaya değil
    RAPORA düşer.

    İLK sayfanın taşıma arızası `BrokerErisilemez`dir (çıkış 3); sonraki sayfaların arızası
    eldekini düşürmez ama pencere `kapsandi=False` + nedenle döner — yarım pencere, tam pencere
    GİBİ konuşamaz."""
    pencere = {"sayfa": 0, "n_emir": 0, "kapsandi": True, "en_eski": None,
               "baslangic": baslangic, "neden": None}
    toplam: list = []
    gorulen: set = set()
    until = None
    while True:
        pencere["sayfa"] += 1
        kw = {"status": "closed", "limit": int(tavan), "nested": True, "after": baslangic}
        if until:
            kw["until"] = until
        sayfa = alpaca_mod.orders(**kw)
        if not alpaca_mod.transport()["ok"]:
            if pencere["sayfa"] == 1:
                raise BrokerErisilemez(alpaca_mod.transport().get("error")
                                       or "alpaca taşıma arızası (ilk sayfa okunamadı)")
            pencere.update({"kapsandi": False,
                            "neden": f"sayfa {pencere['sayfa']} okunamadı (taşıma arızası) — "
                                     f"pencere yarım, başlangıca varılamadı"})
            break
        yeni = [o for o in (sayfa or []) if str(o.get("id") or id(o)) not in gorulen]
        gorulen |= {str(o.get("id") or id(o)) for o in yeni}
        toplam.extend(yeni)
        damgalar = [str(o.get("submitted_at") or "") for o in (sayfa or []) if o.get("submitted_at")]
        en_eski = min(damgalar) if damgalar else None
        if en_eski:
            pencere["en_eski"] = en_eski[:10]
        if len(sayfa or []) < int(tavan):
            break                                   # tarihçenin sonu — pencere tam
        if en_eski is None:
            pencere.update({"kapsandi": False,
                            "neden": "sayfada submitted_at okunamadı — geriye sayfalanamaz"})
            break
        if en_eski[:10] <= str(baslangic):
            break                                   # başlangıca ulaşıldı — kapsandı
        if pencere["sayfa"] >= SAYFA_TAVANI:
            pencere.update({"kapsandi": False,
                            "neden": f"sayfa tavanı ({SAYFA_TAVANI}×{tavan}) aşıldı — "
                                     f"{baslangic} penceresine inilemedi"})
            break
        until = en_eski
    pencere["n_emir"] = len(toplam)
    return toplam, pencere


def emir_indeksleri(emirler: list) -> tuple[dict, dict]:
    """(by_coid, by_id). `by_coid` YALNIZ motor emirlerini taşır (`alpaca.is_engine_order`):
    operatörün elle girdiği bir emir plan kimliğiyle eşleşemez ve eşleşiyor GİBİ görünmemelidir."""
    by_coid: dict = {}
    by_id: dict = {}
    for o in emirler or []:
        oid = o.get("id")
        if oid:
            by_id[str(oid)] = o
        if motor_emri_mi(o):
            by_coid.setdefault(str(o.get("client_order_id")), o)
    return by_coid, by_id


def dolum_oku(extra: dict, plan_id, by_coid: dict, by_id: dict, alpaca_mod) -> dict:
    """Bir işlemin GİRİŞ ve ÇIKIŞ dolumunu broker gövdelerinden okur — hiçbir şey yazmaz.

    Dönüş: `{giris_ts, giris_fiyat, cikis_ts, cikis_fiyat, cikis_kaynak, nedenler}`. Okunamayan
    her değer `None` + `nedenler` listesinde ADIYLA bir satır (UYDURMA YASAĞI)."""
    out = {"giris_ts": None, "giris_fiyat": None, "cikis_ts": None, "cikis_fiyat": None,
           "cikis_kaynak": None, "nedenler": []}
    parent = by_coid.get(str(plan_id))
    if parent is None:
        out["nedenler"].append(
            f"plan kimliği {str(plan_id)!r} kapalı emir penceresinde YOK (motor emri bulunamadı)")
    else:
        af = giris_dolum_fiyati(parent)
        if af is None:
            out["nedenler"].append(
                f"giriş emri dolum fiyatı okunamadı (status={str(parent.get('status') or '?')})")
        else:
            out["giris_fiyat"] = round(af, FIYAT_ONDALIK)
        ts = parent.get("filled_at")
        if ts:
            out["giris_ts"] = str(ts)
        else:
            out["nedenler"].append("giriş emri gövdesinde dolum zamanı boş — zaman uydurulmadı")

    oid = (extra or {}).get(ALAN_KAPATMA_EMRI)
    if oid:
        # "KARAR" KOLU: `DELETE /v2/positions` kapatmasının doğurduğu DÜZ market emri; coid'i
        # Alpaca üretimidir ve plan kimliğiyle ASLA eşleşmez — kimlikle tekil okunur.
        out["cikis_kaynak"] = "karar"
        o = by_id.get(str(oid)) or alpaca_mod.order_by_id(str(oid))
        if o is None:
            out["nedenler"].append(f"kapatma emri {str(oid)[:24]!r} okunamadı (pencere/kimlik)")
        else:
            af = giris_dolum_fiyati(o)     # karar emri DÜZ bir emirdir: dolum kendi gövdesinde
            if af is None:
                out["nedenler"].append(
                    f"kapatma emrinde dolum fiyatı yok (status={str(o.get('status') or '?')})")
            else:
                out["cikis_fiyat"] = round(af, FIYAT_ONDALIK)
            ts = o.get("filled_at")
            if ts:
                out["cikis_ts"] = str(ts)
            else:
                out["nedenler"].append("kapatma emri gövdesinde dolum zamanı boş")
    elif parent is not None:
        # "BACAK" KOLU: parent bracket'ın dolan TP/SL bacağı; fiyat ve zaman AYNI bacak seçimiyle.
        out["cikis_kaynak"] = "bacak"
        af = cikis_dolum_fiyati(parent)
        if af is None:
            out["nedenler"].append(
                "bracket bacağında dolum yok (bacak dolmadı/iptal) ve satırda kapatma emri kimliği "
                "yok — çıkış dolumu ÖLÇÜLEMEDİ")
        else:
            out["cikis_fiyat"] = round(af, FIYAT_ONDALIK)
            out["cikis_ts"] = cikis_dolum_zamani(parent)
            if out["cikis_ts"] is None:
                out["nedenler"].append("dolan bacakta zaman damgası yok — zaman uydurulmadı")
    return out


# ---- PLAN KURULUMU ---------------------------------------------------------------------------
def plan_kur(satirlar: list[dict], by_coid: dict, by_id: dict, alpaca_mod,
             damga_str: str) -> tuple[list[dict], list[dict], dict]:
    """Aday satırlardan YAZIM PLANINI ve KALEM RAPORUNU kurar — DB'ye dokunmaz, saf.

    Kural: yalnız BOŞ hedef alana yazılır. Alan DOLUYSA broker değeri onunla kıyaslanır ve FARKLI
    ise `ayrisma` sınıflı bir kayıt doğar — kayıt RAPORDADIR, DEFTERDE DEĞİL (dolu alan ezilmez).
    `dolum_kaynak` damgası satırda zaten varsa KORUNUR."""
    plan: list[dict] = []
    kalemler: list[dict] = []
    ozet = {"aday": 0, "yazilacak": 0, "atlandi": 0, "eslesmedi": 0, "n_alan": 0,
            "n_ayrisma": 0, "damga_korunan": 0}
    for s in satirlar:
        extra, hata = extra_coz(s.get("extra_json"))
        if extra is None or not canli_mi(s, extra):
            if extra is None and canli_mi(s, None):
                ozet["aday"] += 1
                ozet["atlandi"] += 1
                kalemler.append({"seq": s["seq"], "id": s.get("id"), "plan_id": s.get("plan_id"),
                                 "ticker": s.get("ticker"), "durum": "atlandi", "neden": hata,
                                 "cikis_kaynak": None, "yazilacak": {}, "ayrismalar": []})
            continue
        ozet["aday"] += 1
        bos = [a for a in HEDEF_ALANLAR if extra.get(a) in (None, "")]
        kalem = {"seq": s["seq"], "id": s.get("id"), "plan_id": s.get("plan_id"),
                 "ticker": s.get("ticker"), "durum": None, "neden": "", "cikis_kaynak": None,
                 "yazilacak": {}, "ayrismalar": [], "okunan": {}}
        if not bos:
            kalem.update({"durum": "atlandi",
                          "neden": "dört dolum alanı da DOLU — geri doldurulacak boşluk yok"})
            ozet["atlandi"] += 1
            kalemler.append(kalem)
            continue

        okunan = dolum_oku(extra, s.get("plan_id"), by_coid, by_id, alpaca_mod)
        kalem["cikis_kaynak"] = okunan["cikis_kaynak"]
        kalem["okunan"] = {ALAN_GIRIS_TS: okunan["giris_ts"], ALAN_GIRIS_FIYAT: okunan["giris_fiyat"],
                           ALAN_CIKIS_TS: okunan["cikis_ts"], ALAN_CIKIS_FIYAT: okunan["cikis_fiyat"]}

        for alan, deger in kalem["okunan"].items():
            if deger is None:
                continue
            mevcut = extra.get(alan)
            if mevcut in (None, ""):
                kalem["yazilacak"][alan] = deger
                continue
            ayni = (_esit_fiyat(mevcut, deger) if alan in (ALAN_GIRIS_FIYAT, ALAN_CIKIS_FIYAT)
                    else str(mevcut) == str(deger))
            if not ayni:
                kalem["ayrismalar"].append({"alan": alan, "sinif": "ayrisma", "defterde": mevcut,
                                            "brokerda": deger,
                                            "hukum": "dolu alan EZİLMEDİ — yalnız raporlandı"})
                ozet["n_ayrisma"] += 1

        if not kalem["yazilacak"]:
            if all(v is None for v in kalem["okunan"].values()):
                kalem.update({"durum": "eslesmedi",
                              "neden": "; ".join(okunan["nedenler"]) or "dolum okunamadı"})
                ozet["eslesmedi"] += 1
            else:
                kalem.update({"durum": "atlandi",
                              "neden": "okunan her alan defterde ZATEN dolu"
                                       + (f"; {len(kalem['ayrismalar'])} ayrışma raporlandı"
                                          if kalem["ayrismalar"] else "")})
                ozet["atlandi"] += 1
            kalemler.append(kalem)
            continue

        yeni_extra = dict(extra)
        yeni_extra.update(kalem["yazilacak"])
        if yeni_extra.get(ALAN_DAMGA):
            ozet["damga_korunan"] += 1
        else:
            yeni_extra[ALAN_DAMGA] = damga_str
        kalem.update({"durum": "yazilacak",
                      "neden": "; ".join(okunan["nedenler"]) if okunan["nedenler"] else ""})
        ozet["yazilacak"] += 1
        ozet["n_alan"] += len(kalem["yazilacak"])
        kalemler.append(kalem)
        plan.append({"seq": s["seq"], "id": s.get("id"), "plan_id": s.get("plan_id"),
                     "ticker": s.get("ticker"), "yazilacak": dict(kalem["yazilacak"]),
                     "yeni_extra": json.dumps(yeni_extra, ensure_ascii=False)})
    return plan, kalemler, ozet


# ---- DB OKUMA / ANLIK / DOĞRULAMA -------------------------------------------------------------
def oku_satirlar(conn: sqlite3.Connection) -> list[dict]:
    """Plan için gereken ALTI kolon, `seq` sırasıyla. `SELECT *` KULLANILMAZ: gerçek şema ~30
    kolon taşır, sentetik test tablosu altı — `SELECT *` çağıranı şema varsayımına bağlardı."""
    cur = conn.execute(f'SELECT seq, id, plan_id, ticker, {KAYNAK_KOLONU}, extra_json '
                       f'FROM trades ORDER BY seq')
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def anlik(conn: sqlite3.Connection) -> dict:
    """Uygulama ÖNCESİ tam anlık görüntü: satır sayısı + her `seq`in TAM satırı (`SELECT *`, şema
    ne olursa olsun) + hedef alanların doluluk sayacı. `dogrula_sonrasi` bunu yazımdan SONRA
    yeniden ölçüp kıyaslar."""
    cur = conn.execute("SELECT * FROM trades ORDER BY seq")
    cols = [d[0] for d in cur.description]
    satirlar = {r[cols.index("seq")]: dict(zip(cols, r)) for r in cur.fetchall()}
    return {"n": len(satirlar), "satirlar": satirlar, "dolu": _dolu_alan_sayisi(satirlar.values())}


def _dolu_alan_sayisi(satirlar) -> int:
    """Hedef alanların defter genelindeki DOLULUK sayacı — brief'in ikinci doğrulama değişmezi."""
    n = 0
    for r in satirlar:
        extra, _ = extra_coz(r.get("extra_json"))
        for a in HEDEF_ALANLAR:
            if (extra or {}).get(a) not in (None, ""):
                n += 1
    return n


def dogrula_sonrasi(conn: sqlite3.Connection, once: dict, plan: list[dict]) -> list[str]:
    """Yazımdan SONRA (henüz COMMIT edilmemiş transaction içinde) DÖRT değişmezi ölçer. Boş liste
    dönerse `uygula_plan` COMMIT eder, aksi hâlde ROLLBACK.

      1. satır sayısı değişmedi,
      2. plan DIŞI her satır TAM olarak eskisi (tek karakter bile değişmedi),
      3. plan İÇİ her satır DB'de VAR, `extra_json`u tam beklenen değerde ve `extra_json` DIŞINDAKİ
         tüm kolonları (`kaynak` dahil) DEĞİŞMEDİ,
      4. hedef alanların doluluk sayacı = önceki + planlanan yeni alan sayısı (ne eksik ne fazla)."""
    hatalar: list[str] = []
    cur = conn.execute("SELECT * FROM trades ORDER BY seq")
    cols = [d[0] for d in cur.description]
    sonra = {r[cols.index("seq")]: dict(zip(cols, r)) for r in cur.fetchall()}
    if len(sonra) != once["n"]:
        hatalar.append(f"satır sayısı değişmezi KIRILDI: {once['n']} → {len(sonra)}")
        return hatalar                       # sayı kırıksa aşağıdaki kıyaslar anlamsız
    planli = {e["seq"]: e for e in plan}
    for seq, eski in once["satirlar"].items():
        yeni = sonra.get(seq)
        if yeni is None:
            hatalar.append(f"seq={seq} yazımdan sonra DB'de YOK")
            continue
        if seq not in planli:
            if yeni != eski:
                hatalar.append(f"PLAN DIŞI satır (seq={seq}) DEĞİŞTİ — dokunulmaması gerekiyordu")
            continue
        if yeni.get("extra_json") != planli[seq]["yeni_extra"]:
            hatalar.append(f"seq={seq}: extra_json beklenen değere yazılmadı")
        for k in eski:
            if k == "extra_json":
                continue
            if yeni.get(k) != eski.get(k):
                hatalar.append(f"seq={seq}: `{k}` kolonu DEĞİŞTİ — yalnız extra_json yazılmalıydı")
    for seq in planli:
        if seq not in sonra:
            hatalar.append(f"planlanan seq={seq} DB'de YOK — yazım hiçbir satıra düşmedi")
    beklenen = once["dolu"] + sum(len(e["yazilacak"]) for e in plan)
    olculen = _dolu_alan_sayisi(sonra.values())
    if olculen != beklenen:
        hatalar.append(f"dolu alan sayacı değişmezi KIRILDI: beklenen {beklenen}, ölçülen {olculen}")
    return hatalar


def uygula_plan(conn: sqlite3.Connection, plan: list[dict], once: dict) -> dict:
    """Planı TEK `BEGIN IMMEDIATE…COMMIT/ROLLBACK` transaction'ında uygular. Yalnız `extra_json`
    kolonuna yazar — `kaynak` (ledgerstamp damgası) ve diğer tipli kolonlar SQL'e HİÇ girmez.

    Dönüş `{ok, hatalar, n_yazilan}`. `ok=False` ise ROLLBACK yapılmıştır ve DB çağrı öncesiyle
    bit-bit aynıdır — yarım uygulanmış bir geri dolum hiç uygulanmamış olandan daha kötüdür."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        for e in plan:
            conn.execute("UPDATE trades SET extra_json=? WHERE seq=?", (e["yeni_extra"], e["seq"]))
        hatalar = dogrula_sonrasi(conn, once, plan)
        if hatalar:
            conn.execute("ROLLBACK")
            return {"ok": False, "hatalar": hatalar, "n_yazilan": 0}
        conn.execute("COMMIT")
        return {"ok": True, "hatalar": [], "n_yazilan": len(plan)}
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def yedek_al(conn: sqlite3.Connection, db_yolu: Path, yedek_dizin: Path) -> Path:
    """`sqlite3` ÇEVRİMİÇİ YEDEK API'siyle TUTARLI kopya — `storage.backup_to` ile AYNI gerekçe:
    WAL modunda defterin bir kısmı `-wal` dosyasındadır ve `cp`/`tar` kopyası EKSİK ya da YARIŞLI
    olur. Yazımdan hemen sonra açılabilirlik DOĞRULANIR: sessizce bozuk bir yedek, yedek
    olmamasından daha kötüdür (geri yükleme gününe kadar görünmez)."""
    yedek_dizin.mkdir(parents=True, exist_ok=True)
    an = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    hedef = yedek_dizin / f"{db_yolu.name}.{an}.bak"
    dst = sqlite3.connect(str(hedef))
    try:
        conn.backup(dst)
    finally:
        dst.close()
    dogrula = sqlite3.connect(str(hedef))
    try:
        dogrula.execute("SELECT COUNT(*) FROM trades").fetchone()
    finally:
        dogrula.close()
    return hedef


# ---- KOŞUM -----------------------------------------------------------------------------------
def calistir(db_yolu, *, uygula: bool, baslangic: str, tavan: int,
             yedek_dizin=None, alpaca_mod=None) -> dict:
    """Tek koşum: oku → broker penceresi → plan → (kuru: dur | uygula: yedek+transaction+doğrula).

    `BrokerErisilemez` YUKARI FIRLAR (çağıran `main` onu çıkış 3'e çevirir): boş emir listesini
    "dolum yok" diye okumak, tam olarak bu betiğin kovaladığı sessizlik sınıfıdır."""
    mod = alpaca_mod or alpaca
    db_yolu = Path(db_yolu)
    if not mod.paper_available():
        raise BrokerErisilemez("Alpaca kâğıt kimliği yok — emir geçmişi okunamaz")
    conn = sqlite3.connect(str(db_yolu))
    try:
        satirlar = oku_satirlar(conn)
        emirler, pencere = emirleri_cek(mod, baslangic, tavan)
        by_coid, by_id = emir_indeksleri(emirler)
        plan, kalemler, ozet = plan_kur(satirlar, by_coid, by_id, mod, damga())
        rapor = {"mod": ("uygula" if uygula else "kuru"), "db": str(db_yolu), "pencere": pencere,
                 "kalemler": kalemler, "ozet": {**ozet, "defter_satiri": len(satirlar)},
                 "plan": plan, "yazildi": False, "yedek": None, "hatalar": [], "rc": 0}
        if not uygula or not plan:
            return rapor
        yedek = yedek_al(conn, db_yolu, Path(yedek_dizin) if yedek_dizin else db_yolu.parent)
        rapor["yedek"] = str(yedek)
        sonuc = uygula_plan(conn, plan, anlik(conn))
        rapor["yazildi"] = bool(sonuc["ok"])
        rapor["hatalar"] = sonuc["hatalar"]
        rapor["rc"] = 0 if sonuc["ok"] else 1
        return rapor
    finally:
        conn.close()


def _bas(rapor: dict) -> None:
    """İnsan okuyucusu (Rol-1) için satır dökümü + makine okuyucusu için tek JSON gövdesi.

    YASA 6 — OKUYUCU: (a) Rol-1 kuru koşumu okur ve `--uygula` kararını buradan verir; (b) betiğin
    KENDİSİ ikinci koşumda aynı alanları OKUR ve 'zaten dolu' der (idempotans); (c) EDG-2026-069
    ADIM-0 tekrarı geri dolum sonrası `dolum_ts` doluluğunu ölçer."""
    o = rapor["ozet"]
    print(f"=== dolum_geri_dolum — {rapor['mod'].upper()}"
          + ("" if rapor["mod"] == "uygula" else " KOŞU (varsayılan, DB'ye DOKUNULMADI)") + " ===")
    print(f"db: {rapor['db']}")
    print(f"AD AYRIMI: `{ALAN_CIKIS_TS}`/`{ALAN_CIKIS_FIYAT}` ÇIKIŞ dolumudur (motorun kendi "
          f"alanları); GİRİŞ dolumu `{ALAN_GIRIS_TS}`/`{ALAN_GIRIS_FIYAT}` alanlarına yazılır.")
    p = rapor["pencere"]
    print(f"emir penceresi: {p['n_emir']} emir · {p['sayfa']} sayfa · en eski {p['en_eski']} · "
          f"kapsandı={p['kapsandi']}" + (f" · NEDEN: {p['neden']}" if p["neden"] else ""))
    print(f"defter satırı: {o['defter_satiri']} · canlı aday: {o['aday']} · yazılacak: "
          f"{o['yazilacak']} ({o['n_alan']} alan) · atlandı: {o['atlandi']} · eşleşmedi: "
          f"{o['eslesmedi']} · ayrışma: {o['n_ayrisma']}")
    for k in rapor["kalemler"]:
        ok = k.get("okunan") or {}
        print(f"  [{k['durum']:>10}] seq={k['seq']} {str(k['id']):8} {str(k['ticker']):6} "
              f"{str(k['plan_id']):28} çıkış-kaynak={k['cikis_kaynak'] or '-'}")
        print(f"      giriş: ts={ok.get(ALAN_GIRIS_TS)} fiyat={ok.get(ALAN_GIRIS_FIYAT)} · "
              f"çıkış: ts={ok.get(ALAN_CIKIS_TS)} fiyat={ok.get(ALAN_CIKIS_FIYAT)}")
        if k.get("yazilacak"):
            print(f"      yazılacak: {k['yazilacak']}")
        for a in k.get("ayrismalar") or []:
            print(f"      AYRIŞMA [{a['sinif']}] {a['alan']}: defterde={a['defterde']!r} "
                  f"brokerda={a['brokerda']!r} — {a['hukum']}")
        if k.get("neden"):
            print(f"      neden: {k['neden']}")
    if rapor["mod"] == "kuru":
        print("\nHiçbir şey YAZILMADI. Uygulamak için: --uygula (yedek alınır; bu betik canlı "
              "worker'ın durup durmadığını KONTROL ETMEZ — Rol-1 önce worker'ı durdurmalı).")
    else:
        print(f"\nyedek: {rapor['yedek']}")
        if rapor["hatalar"]:
            print("!! DOĞRULAMA DÜŞTÜ — ROLLBACK yapıldı, DB DEĞİŞMEDİ:", file=sys.stderr)
            for h in rapor["hatalar"]:
                print(f"   · {h}", file=sys.stderr)
        else:
            print(f"{o['yazilacak']} satır ({o['n_alan']} alan) yazıldı · doğrulama GEÇTİ.")
    print(json.dumps({k: v for k, v in rapor.items() if k != "plan"},
                     ensure_ascii=False, indent=1, default=str))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python ops/dolum_geri_dolum.py",
        description="live_paper işlemlerinin BOŞ dolum alanlarını Alpaca emir geçmişinden geri "
                    "doldurur (TSK-182) — kuru koşum varsayılan")
    ap.add_argument("--db", required=True, help="SQLite işlem defteri yolu (örn. state/meridian.db)")
    ap.add_argument("--kuru", action="store_true",
                    help="yalnız planı bas, DB'ye dokunma (VARSAYILAN davranış)")
    ap.add_argument("--uygula", action="store_true",
                    help="YAZ: yedek al, boş alanları tek transaction'da doldur, doğrula")
    ap.add_argument("--baslangic", default="2026-08-01",
                    help="emir geçmişinin geriye dek tarandığı tarih (Alpaca `after` süzgeci)")
    ap.add_argument("--tavan", type=int, default=200, help="sayfa başına emir sayısı (sayfalama)")
    ap.add_argument("--yedek-dizin", default=None,
                    help="yedek DB'nin yazılacağı dizin (varsayılan: <db-dizini>)")
    a = ap.parse_args(argv)

    if a.kuru and a.uygula:
        print("KULLANIM HATASI: --kuru ve --uygula birlikte verilemez (kip bayrağı TEK olmalı)",
              file=sys.stderr)
        return 2
    db_yolu = Path(a.db)
    if not db_yolu.exists():
        print(f"DB bulunamadı: {db_yolu}", file=sys.stderr)
        return 2
    if a.tavan < 1:
        print(f"KULLANIM HATASI: --tavan ≥ 1 olmalı ({a.tavan} verildi)", file=sys.stderr)
        return 2

    try:
        rapor = calistir(db_yolu, uygula=bool(a.uygula), baslangic=a.baslangic, tavan=a.tavan,
                         yedek_dizin=a.yedek_dizin)
    except BrokerErisilemez as e:
        print(f"BROKER ERİŞİLEMEZ: {e} — hiçbir şey yazılmadı ([] 'emir yok' DEĞİL, ARIZADIR)",
              file=sys.stderr)
        return 3
    _bas(rapor)
    if a.uygula:
        # TEK OLAY, YALNIZ UYGULAMA YOLUNDA (kuru koşum canlı defteri kirletmez).
        obs.log(OLAY, db=str(db_yolu), n_yazilan=rapor["ozet"]["yazilacak"] if rapor["yazildi"] else 0,
                n_eslesmeyen=rapor["ozet"]["eslesmedi"], n_alan=rapor["ozet"]["n_alan"],
                n_ayrisma=rapor["ozet"]["n_ayrisma"], yazildi=rapor["yazildi"],
                pencere_kapsandi=rapor["pencere"]["kapsandi"], yedek=rapor["yedek"],
                betik=BETIK_ADI,
                detail="geçmiş live_paper dolum alanları Alpaca emir geçmişinden geri dolduruldu "
                       "(yalnız BOŞ alan; dolu alan ezilmedi)")
    return rapor["rc"]


if __name__ == "__main__":
    raise SystemExit(main())
