"""olc.py — EDG-2026-091: canlı `r_multiple` PAYDASININ kaynağı (ADIM-0 + ölçüm).

NE ÖLÇER. Kartın (`research/cards/EDG-2026-091-canli-r-paydasi-kaynagi.yaml`) birincil ölçüsü:
donmuş A1 çekimindeki her canlı işlem için

    payda_turetilen = |pnl_dollars / (r_multiple · qty)|        (R'nin HİSSE BAŞI paydası, $)
    plan_riski      = |entry_trigger − plan.stop|               (gölge/replay'in kullandığı mesafe)
    oran            = payda_turetilen / plan_riski

dağılımı, `oran ∉ esikler.oran_bant` olan işlemlerin payı ve o işlemlerde bir STOP SIKILAŞTIRMA
olayının bulunup bulunmadığı (2×2). Tanı olarak giriş riski (|gerçek dolum − plan.stop|), broker
SL bacağının `stop_price`ı, defter fiyatı ↔ ayna dolumu bps farkı ve adet ayrışması.

HÜKÜM YAZMAZ. Kart hükmü Rol-1'indir; bu betik yalnız ölçer ve PK düşerse hiçbir sayı yaymaz
(kart kill#4). Canlı motoru DEĞİŞTİRMEZ (kill#2): motoru ithal bile etmez — tek motor teması
`R_MULTIPLE_ALT` sabitinin EDG-088 sayım modülünden İTHALİDİR (tek-kaynak yasası: eşik burada
yeniden yazılsaydı iki kopya sessizce ayrışırdı).

KOMUT SATIRI (sözleşme `main()` değil KOMUT SATIRIdır):

    .venv/bin/python research/olcumler/edg091_r_paydasi/olc.py \
        --cikti-dizin research/olcumler/edg091_r_paydasi

    --girdi        donmuş A1 çekimi (varsayılan: girdi/a1_cekim_2026-09-13.json)
    --sha-dosya    manifesto (varsayılan: girdi/SHA256SUMS) — tutmazsa kill#3, çıkış 1
    --cikti-dizin  sonuç JSON'unun dizini (varsayılan: betiğin kendi dizini)
    --state-dizin  motorun state kökü olarak DAYATILACAK geçici dizin; deponun `state/` ağacının
                   ALTINDA olamaz (`_ortak.state_izni`). Varsayılan: çıktı dizininin altında
                   OLUŞTURULMAYAN bir sanal yol — buraya bir yazım denemesi olursa sessizce canlı
                   deftere değil, var olmayan bir yola gider ve GÜRÜLTÜLÜ düşer.

ÇIKIŞ: 0 ölçüldü · 2 PK düştü / kill tetiklendi (sayı yayılmaz) · 1 ön şart tutmadı (Blok).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import statistics
import sys

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]
EDG088 = KOK / "research" / "olcumler" / "edg088_golge_pilot"
# BETİK DOĞRUDAN KOŞULUR: `sys.path[0]` bu dizindir, depo kökü yolda DEĞİLDİR. Kök ÖNE konur ki
# `meridian` kurulu kopyaya (ana checkout) değil BU ağaca çözülsün — worktree'de koşan bir ölçümün
# başka bir ağacın motorunu ölçmesi sınıfı. `edg088` dizini `_ortak`/`sayim` ithali için gerekir.
for _p in (str(EDG088), str(KOK)):
    while _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import _ortak  # noqa: E402  — Blok, yolu_kur, state_izni (EDG-088 ile TEK kaynak)

Blok = _ortak.Blok


class PKDustu(Exception):
    """Pozitif kontrol tutmadı → çıkış 2, hiçbir ölçüm sayısı yayılmaz (kart kill#4)."""


VARSAYILAN_GIRDI = SANDBOX / "girdi" / "a1_cekim_2026-09-13.json"
VARSAYILAN_SHA = SANDBOX / "girdi" / "SHA256SUMS"
PK3_GOLGE = EDG088 / "pk3_selef" / "sonuc_20260913T145834+0000.json"
PK3_REPLAY = (KOK / "research" / "olcumler" / "edg049_dormant_2026-08-23"
              / "islemler_tam_dormant_acik.json")

# ---- KARTIN EŞİKLERİ (kart DEĞİŞMEZ; burada yalnız OKUNUR biçimde durur) -------------------------
ORAN_BANT = (0.95, 1.05)      # kart: esikler.oran_bant
SIKLASTIRMA_ESLESME_ALT = 0.80  # kart: esikler.siklastirma_eslesme_alt
N_ORAN_ALT = 15               # kart: esikler.n_oran_alt (ADIM-0 kapısı)
PK_TOLERANS = 0.01            # kart pozitif_kontrol: "birebir (±0,01)"

# ==================================================================================================
# ADIM-0 (1) — ÜÇ YOLUN R PAYDASI (KOD OKUMASI). Çapalar SEMBOLdür, satır değil.
# ==================================================================================================
#: Her kayıt ÖLÇÜLMÜŞ bir okumadır: `capa` gerçekten var olan bir tanımı gösterir (çivi bunu
#: kaynak dosyada arar — çapa çürürse test kırmızıya döner, `.md`'deki gibi sessizce ölmez).
PAYDA_TANIMLARI = {
    "canli": {
        "capa": "meridian/broker.py::PaperBroker.close_position",
        "dosya": "meridian/broker.py",
        "semboller": ["PaperBroker.close_position", "PaperBroker.size_position",
                      "PaperBroker.fill_entry"],
        "ifade": "r_multiple = pnl / pos.risk_dollars",
        "payda_birimi": "POZİSYON ($) — hisse başı karşılığı `pos.risk_dollars / pos.qty`",
        "payda_kaynagi": (
            "`pos.risk_dollars`, `PaperBroker.size_position` içinde `size_r · RISK_PCT_PER_R · "
            "equity` ile kurulan DOLAR BÜTÇESİdir; `qty` bu bütçenin hisse başı riske BÖLÜNÜP "
            "AŞAĞI YUVARLANMASIYLA doğar (`math.floor`), yani `qty · (dolum − stop) ≤ "
            "risk_dollars`. Bütçe yalnız İKİ dalda yeniden türetilir (`fill_entry`: ADV tavanı ve "
            "notional tavanı → `risk_dollars = qty · (base_fill − stop)`)."),
        "stop_kaynagi": "plan[\"stop\"] (giriş anında dondurulur)",
        "siklastirma_etkisi": (
            "YOK. `manage_position` yalnız `pos.trail_stop`u taşır, `_touch_exit` yalnız "
            "`eff_stop`u okur; `pos.risk_dollars` giriş anından sonra HİÇBİR dalda yazılmaz "
            "(tarama: meridian/ içinde `risk_dollars` atamaları yalnız `fill_entry` gövdesinde)."),
        "qty_kaynagi": (
            "`pos.qty` — giriş anında `size_position`dan doğar, ama `meridian/loop.py::"
            "_adet_benimse` dolumdan sonra AYNANIN adedini BENİMSER (`poz.qty = yeni`) ve "
            "`pos.risk_dollars`a DOKUNMAZ → hisse başı payda (`risk_dollars / qty`) sessizce kayar."),
    },
    "golge": {
        "capa": "meridian/golge_icra.py::_kapanis_satiri",
        "dosya": "meridian/golge_icra.py",
        "semboller": ["_kapanis_satiri", "_pozisyon_nesnesi"],
        "ifade": "R = (çıkış − giriş) / poz[\"r_per_share\"]",
        "payda_birimi": "HİSSE BAŞI ($)",
        "payda_kaynagi": (
            "`r_per_share = dolum − stop` (GİRİŞ riski). `_pozisyon_nesnesi` `qty=1` ve "
            "`risk_dollars = r_per_share` NOMİNAL değerlerini kurar: defter plan düzeyindedir, "
            "bütçe/yuvarlama yolu hiç koşmaz."),
        "stop_kaynagi": "kayit[\"stop\"] (plan stopu)",
        "siklastirma_etkisi": "YOK (payda giriş anında dondurulur, trail yalnız çıkışı belirler).",
        "qty_kaynagi": "sabit 1 (nominal)",
    },
    "replay": {
        "capa": "meridian/backtest.py::replay",
        "dosya": "meridian/backtest.py",
        "semboller": ["replay"],
        "ifade": "canlıyla AYNI fabrika: PaperBroker.close_position",
        "payda_birimi": "POZİSYON ($) — hisse başı karşılığı `risk_dollars / qty`",
        "payda_kaynagi": (
            "`replay` canlı ile AYNI `PaperBroker`ı kurar ve aynı `fill_entry`/`close_position` "
            "çiftini çağırır → payda yine BÜTÇEdir. Canlıdan tek yapısal farkı: replay'de ayna "
            "yoktur, yani `_adet_benimse` yolu HİÇ koşmaz ve `qty` bütçeyle tutarlı kalır "
            "(sapma yalnız `floor` artığı kadardır: oran ∈ [1, 1 + 1/qty))."),
        "stop_kaynagi": "plan[\"stop\"]",
        "siklastirma_etkisi": "YOK (canlıyla aynı gerekçe).",
        "qty_kaynagi": "`size_position` — benimseme yolu yok",
    },
}

#: AYRIŞMA — ADIYLA (kart `olcum_plani` üçüncü madde; tek-kaynak yasası tespiti).
PAYDA_AYRISMALARI = [
    {"ad": "birim_ayrismasi",
     "taraflar": ["canli", "replay", "golge"],
     "beyan": ("Canlı/replay paydası POZİSYON BÜTÇESİDİR (`risk_dollars`), gölge paydası HİSSE "
               "BAŞI GİRİŞ RİSKİDİR (`dolum − stop`). İkisi ancak `qty = risk_dollars / "
               "(dolum − stop)` TAM BÖLÜNDÜĞÜNDE eşittir; `math.floor` her zaman ≥ yönünde artık "
               "bırakır.")},
    {"ad": "adet_benimseme",
     "taraflar": ["canli"],
     "beyan": ("`meridian/loop.py::_adet_benimse` (Ö-53/D) kitabın adedini aynanınkiyle "
               "DEĞİŞTİRİR ama `risk_dollars` bütçesini OLDUĞU GİBİ bırakır. Fonksiyonun kendi "
               "belgesi iki tarafın FARKLI hisse-başı risk kullandığını söylüyor: ayna "
               "`tetik − stop`, kitap `dolum − stop`. Benimseme sonrası canlı R'nin paydası "
               "artık İKİ defterin KARIŞIMIdır — ne bütçe/ayna-adedi ne de plan riski.")},
    {"ad": "replay_benimseme_yok",
     "taraflar": ["replay", "canli"],
     "beyan": ("Aynı fabrika, farklı sonuç: replay'de benimseme yolu yok, canlıda var. Bu, iki "
               "defterin R birimini kod özdeşliğine RAĞMEN ayrıştırır.")},
]


# ==================================================================================================
# YARDIMCILAR
# ==================================================================================================
def _sha256(yol: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def manifesto_dogrula(girdi: pathlib.Path, sha_dosya: pathlib.Path) -> dict:
    """Donmuş girdinin SHA256SUMS kaydı — TUTMAZSA `Blok` (kart kill#3).

    Manifesto satırı `<sha>  <dosya adı>` biçimindedir; yalnız `girdi`nin ADINI taşıyan satır
    aranır (manifesto birden çok dosya taşıyabilir).
    """
    if not sha_dosya.exists():
        raise Blok(f"SHA256SUMS yok: {sha_dosya} — donmuş girdi doğrulanamaz (kill#3)")
    beyan = None
    for satir in sha_dosya.read_text(encoding="utf-8").splitlines():
        parca = satir.split()
        if len(parca) >= 2 and parca[-1].lstrip("*") == girdi.name:
            beyan = parca[0]
            break
    if beyan is None:
        raise Blok(f"manifesto {girdi.name} satırını taşımıyor: {sha_dosya} (kill#3)")
    olculen = _sha256(girdi)
    if olculen != beyan:
        raise Blok(f"SHA256 TUTMADI: beyan {beyan} ≠ ölçülen {olculen} — girdi donmuş değil (kill#3)")
    return {"yol": str(girdi), "yol_goreli": str(girdi.relative_to(KOK)),
            "sha256": olculen, "beyan": beyan, "dogrulandi": True}


def _sayi(x) -> float | None:
    """Sayıya çevrilebiliyorsa float, değilse None — 0.0 UYDURULMAZ."""
    try:
        d = float(x)
    except (TypeError, ValueError):  # sessiz-yutma: alan yok/biçimsiz; çağıran None'ı ADLI nedenle raporlar, sıfır uydurulmaz
        return None
    return d if math.isfinite(d) else None


def _bps(defter: float | None, ayna: float | None) -> float | None:
    """Defter fiyatının ayna dolumuna göre farkı (bps). Biri ölçülemediyse None."""
    if defter is None or ayna is None or ayna <= 0:
        return None
    return round((defter / ayna - 1.0) * 10000.0, 2)


def _r_ulp(satirlar: list[dict], alan: str = "r_multiple") -> float:
    """Defterin `r_multiple` YUVARLAMA ADIMI — VARSAYILMAZ, defterin kendisinden ölçülür.

    Satırların ondalık hane sayısının AZAMİSİ alınır: `-0,35` iki haneli yazılmış olsa da defterin
    tamamı üç hane taşıyorsa adım 1e-3'tür (tersini varsaymak hata payını KÜÇÜK gösterirdi).
    Hiç ölçülemezse 1.0 döner: adım 1 birim kabul edilir, yani bant AZAMİ genişler. Bu bilinçli
    olarak GEVŞEK taraftır (yanlış NO-GO üretmemek için) ve ölçülen değer sonuçta (`r_ulp_olculen`)
    durur — okuyucu bandın hangi adımdan türediğini görür.
    """
    en_cok = 0
    for r in satirlar:
        v = r.get(alan)
        if v is None:
            continue
        metin = repr(float(v))
        if "e" in metin or "E" in metin:   # bilimsel gösterim: hane sayımı anlamsız
            continue
        if "." in metin:
            en_cok = max(en_cok, len(metin.split(".")[1]))
    return 10.0 ** (-en_cok) if en_cok else 1.0


def _yuzdelik(seri: list[float], p: float) -> float | None:
    """Doğrusal interpolasyonlu yüzdelik. n<2 ise None (tek noktadan dağılım uydurulmaz)."""
    if len(seri) < 2:
        return None
    s = sorted(seri)
    k = (len(s) - 1) * p
    alt, ust = math.floor(k), math.ceil(k)
    if alt == ust:
        return round(s[int(k)], 6)
    return round(s[alt] + (s[ust] - s[alt]) * (k - alt), 6)


# ==================================================================================================
# PAYDA TÜRETİMİ — TEK YÜKLEM (her çağıran BURAYI çağırır; ikinci kopya yok)
# ==================================================================================================
def payda_turet(satir: dict, r_alt: float) -> tuple[float | None, str | None]:
    """`|pnl_dollars / (r_multiple · qty)|` — ölçülemeyen her hâlde `(None, neden)`.

    `r_alt` EDG-088'in `sayim.R_MULTIPLE_ALT`ıdır (İTHAL, kopya değil): defterdeki `r_multiple`
    3 ondalıklıdır, |R| küçüldükçe yuvarlama paydayı şişirir. Altındaki satırlarda payda
    ÖLÇÜLEMEDİ sayılır — uydurulmuş bir payda oranı hak etmeden bant dışına atardı.
    """
    r = _sayi(satir.get("r_multiple"))
    pnl = _sayi(satir.get("pnl_dollars"))
    qty = _sayi(satir.get("qty"))
    if r is None or pnl is None or qty is None:
        return None, ("işlem satırında `r_multiple`/`pnl_dollars`/`qty` alanlarından biri "
                      "yok ya da sayı değil — payda TÜRETİLEMEDİ")
    if qty <= 0:
        return None, f"işlem satırının adedi pozitif değil (qty={qty:g}) — payda TÜRETİLEMEDİ"
    if r == 0.0:
        return None, "işlem satırının `r_multiple`ı 0 — payda tanımsız (0'a bölme)"
    if abs(r) < r_alt:
        return None, (f"|r_multiple|={abs(r):.3f} < R_MULTIPLE_ALT={r_alt} — 3 ondalıklı R ile "
                      "türetilen payda hassasiyetsiz, ÖLÇÜLEMEDİ (sıfır-R tanı kümesi)")
    payda = abs(pnl / (r * qty))
    if not math.isfinite(payda) or payda <= 0:
        return None, "türetilen payda pozitif/sonlu çıkmadı — ÖLÇÜLEMEDİ"
    return payda, None


def plan_riski_olc(plan: dict | None, plan_id) -> tuple[float | None, str | None]:
    """`|entry_trigger − stop|` — plan satırı yoksa ya da alanlar ölçülemezse `(None, neden)`."""
    if plan is None:
        return None, (f"plan satırı donmuş çekimde YOK (plan_id={plan_id!r}) — plan riski "
                      "ÖLÇÜLEMEDİ (defterden türetme yapılmaz)")
    trig, stop = _sayi(plan.get("entry_trigger")), _sayi(plan.get("stop"))
    if trig is None or stop is None:
        return None, "plan satırında `entry_trigger`/`stop` yok ya da sayı değil — ÖLÇÜLEMEDİ"
    risk = abs(trig - stop)
    if risk <= 0:
        return None, "plan riski |entry_trigger − stop| pozitif değil — ÖLÇÜLEMEDİ"
    return risk, None


# ==================================================================================================
# SIKILAŞTIRMA OLAYI — ADLAR DONMUŞ GİRDİDEN ÖLÇÜLÜR
# ==================================================================================================
#: Stop BACAĞI taşıyan olay adları (girdi notu, Rol-1 çekimi). Kalan 242−N olay ALARM METNİdir
#: (MIRROR_DRIFT/NAKED_POSITION …) ve stop DEĞİŞİKLİĞİ değildir — bu ayrım sonuca yazılır.
TRAIL_OLAYI = "mirror_trail_synced"
KORUMA_OLAYLARI = ("koruma_oco_gonderildi",)
STOP_TASIYAN_ADLAR = (TRAIL_OLAYI,) + KORUMA_OLAYLARI + ("koruma_kur_istegi", "koruma_kur_ozet",
                                                         "korumasiz_motor_disi_pozisyon")


def siklastirma_bul(olaylar: list[dict], ticker: str, ts_open: str, ts_close: str,
                    plan_stop: float | None) -> dict:
    """İşlem penceresinde SIKILAŞTIRMA olayı var mı? ÖLÇÜLÜR, varsayılmaz.

    · `mirror_trail_synced` → `to_stop > from_stop` ise sıkılaştırma (alanlar olayın kendisinden).
    · `koruma_oco_gonderildi` → olayın `stop`u plan stopunun ÜSTÜNDEyse sıkılaştırma; eşit/altındaysa
      KORUMA KURULUMU (ilk SL bacağı), sıkılaştırma DEĞİL. Plan stopu ölçülemediyse bu olay için
      hüküm `olculemedi`dir — "0 olay" ile karıştırılmaz.

    Dönen `var` ÜÇ DEĞERLİ: True · False ("0 olay" — pencerede stop taşıyan olay yok ya da hiçbiri
    stopu yukarı taşımadı) · None (ölçülemedi).
    """
    pencere, olculemedi = [], []
    for o in olaylar:
        if str(o.get("ticker") or "") != ticker:
            continue
        gun = str(o.get("ts") or "")[:10]
        if not (ts_open <= gun <= ts_close):
            continue
        ad = str(o.get("event") or "")
        if ad == TRAIL_OLAYI:
            frm, to = _sayi(o.get("from_stop")), _sayi(o.get("to_stop"))
            if frm is None or to is None:
                olculemedi.append({"ad": ad, "ts": o.get("ts"),
                                   "neden": "olayda `from_stop`/`to_stop` yok — yön ÖLÇÜLEMEDİ"})
                continue
            if to > frm:
                pencere.append({"ad": ad, "ts": o.get("ts"), "from_stop": frm, "to_stop": to,
                                "olcut": "to_stop > from_stop"})
        elif ad in KORUMA_OLAYLARI:
            st = _sayi(o.get("stop"))
            if st is None or plan_stop is None:
                olculemedi.append({"ad": ad, "ts": o.get("ts"),
                                   "neden": ("olayın `stop`u ya da plan stopu ölçülemedi — bu "
                                             "olayın sıkılaştırma olup olmadığı BİLİNMİYOR")})
                continue
            if st > plan_stop:
                pencere.append({"ad": ad, "ts": o.get("ts"), "from_stop": plan_stop, "to_stop": st,
                                "olcut": "koruma stopu plan stopunun ÜSTÜNDE"})
    if pencere:
        return {"var": True, "olaylar": pencere, "olculemedi": olculemedi}
    if olculemedi:
        return {"var": None, "olaylar": [], "olculemedi": olculemedi,
                "neden": "pencerede yön/eşik ölçülemeyen stop olayı var — hüküm YOK"}
    return {"var": False, "olaylar": [], "olculemedi": [],
            "neden": "pencerede stopu YUKARI taşıyan olay YOK (0 olay — 'ölçülemedi' DEĞİL)"}


# ==================================================================================================
# AYNA (ALPACA) TARAFI
# ==================================================================================================
def ayna_bak(emirler: list[dict], plan_id) -> dict:
    """Plan kimliğine (`client_order_id`) bağlı kapalı emir: parent dolumu + SL/TP bacakları."""
    bos = {"bulundu": False, "neden": f"aynada `client_order_id`={plan_id!r} emri YOK",
           "qty": None, "filled_qty": None, "parent_filled_avg": None,
           "sl_stop_price": None, "sl_filled_avg": None, "cikis_bacagi": None}
    for o in emirler:
        if str(o.get("client_order_id") or "") != str(plan_id):
            continue
        sl = tp = None
        for lg in (o.get("legs") or []):
            if str(lg.get("order_type") or "") == "stop":
                sl = lg
            elif str(lg.get("order_type") or "") == "limit":
                tp = lg
        dolan = None
        for lg in (sl, tp):
            if lg is not None and _sayi(lg.get("filled_qty")) and _sayi(lg.get("filled_avg_price")):
                dolan = lg
                break
        return {"bulundu": True, "neden": None,
                "qty": _sayi(o.get("qty")), "filled_qty": _sayi(o.get("filled_qty")),
                "parent_filled_avg": _sayi(o.get("filled_avg_price")),
                "sl_stop_price": _sayi(sl.get("stop_price")) if sl else None,
                "sl_filled_avg": _sayi(sl.get("filled_avg_price")) if sl else None,
                "cikis_bacagi": (None if dolan is None else
                                 {"tip": dolan.get("order_type"),
                                  "filled_avg": _sayi(dolan.get("filled_avg_price")),
                                  "stop_price": _sayi(dolan.get("stop_price"))})}
    return bos


def qty_tanisi(qty: float, risk_dollars: float | None, plan_riski: float | None,
               giris_riski: float | None, ayna_qty: float | None) -> dict:
    """Adedin hangi tabandan geldiği — ÖLÇÜLÜR, sınıflandırılır, uydurulmaz.

    `risk_dollars = |pnl/r|` (satırın kendi özdeşliğinden). Üç aday taban:
      · `ic_dolum`  : floor(risk_dollars / giriş riski) — `PaperBroker.fill_entry`in kendi yolu
      · `ayna_tetik`: floor(risk_dollars / plan riski)  — aynanın dolum-ÖNCESİ yolu
      · `ayna_qty`  : aynanın GERÇEK dolan adedi (`_adet_benimse` benimsemesi)
    Hiçbiri tutmazsa sınıf `aciklanamadi` + adaylar raporda durur (uydurma yasağı).
    """
    adaylar = {}
    if risk_dollars and giris_riski:
        adaylar["ic_dolum"] = math.floor(risk_dollars / giris_riski)
    if risk_dollars and plan_riski:
        adaylar["ayna_tetik"] = math.floor(risk_dollars / plan_riski)
    if ayna_qty:
        adaylar["ayna_qty"] = int(ayna_qty)
    tutan = sorted(k for k, v in adaylar.items() if v == int(qty))
    return {"qty": int(qty), "adaylar": adaylar, "tutan": tutan,
            "sinif": (tutan[0] if len(tutan) == 1 else
                      "coklu_tutan" if tutan else "aciklanamadi"),
            "neden": (None if tutan else
                      "adet hiçbir ölçülebilir tabanla üretilemedi — kaynağı donmuş girdiden "
                      "ÖLÇÜLEMEDİ (uydurulmaz)")}


# ==================================================================================================
# POZİTİF KONTROLLER
# ==================================================================================================
def pk1_sentetik(r_alt: float) -> dict:
    """PK (1) — SENTETİK. Bilinen giriş/stop/çıkış/adetle kurulan üç sahne, EL HESABIYLA.

    (a) TEMİZ: payda = plan riski → oran 1,000 TAM.
        giriş 100 · plan stop 90 · çıkış 80 · qty 20 · risk_dollars = 20·(100−90) = 200
        pnl = 20·(80−100) = −400 → r = −400/200 = −2,0 → payda = |−400/(−2·20)| = 10 = plan riski.
    (b) SIKILAŞTIRILMIŞ PAYDA (kartın hipotezinin imzası): payda stop 95'ten kurulursa
        risk_dollars = 20·(100−95) = 100 → r = −4,0 → payda = |−400/(−4·20)| = 5 → oran 5/10 = 0,500.
    (c) BÜTÇE + AŞAĞI YUVARLAMA (motorun gerçek yolu): bütçe 207 · plan riski 10 →
        qty = floor(207/10) = 20 · pnl = −400 → r = −400/207 = −1,932367 →
        payda = |pnl/(r·qty)| = 207/20 = 10,35 → oran 1,035 (bant İÇİ, ama 1 DEĞİL).
    """
    sahneler = []

    def _sahne(ad, pnl, risk_dollars, qty, plan_riski, beklenen_oran):
        r = pnl / risk_dollars
        satir = {"r_multiple": round(r, 3), "pnl_dollars": pnl, "qty": qty}
        # EL HESABI yuvarlanmamış r ile yapılır; defterin 3 ondalığı ayrıca ölçülür.
        payda_ham = abs(pnl / (r * qty))
        payda_defter, neden = payda_turet(satir, r_alt)
        oran_ham = payda_ham / plan_riski
        sahneler.append({
            "ad": ad, "r_ham": r, "r_defter": satir["r_multiple"], "qty": qty,
            "risk_dollars": risk_dollars, "plan_riski": plan_riski,
            "payda_ham": round(payda_ham, 6), "payda_defter": payda_defter,
            "payda_defter_neden": neden,
            "oran_ham": round(oran_ham, 6), "beklenen_oran": beklenen_oran,
            "gecti": abs(oran_ham - beklenen_oran) <= 1e-9})

    _sahne("temiz", -400.0, 200.0, 20, 10.0, 1.0)
    _sahne("siklastirilmis_payda", -400.0, 100.0, 20, 10.0, 0.5)
    _sahne("butce_asagi_yuvarlama", -400.0, 207.0, 20, 10.0, 207.0 / 20.0 / 10.0)
    return {"sahneler": sahneler, "gecti": all(s["gecti"] for s in sahneler)}


#: PK (2) — kartın ÜST YORUMUNDAKİ Rol-1 ön ölçümü (2026-09-13 19:4xZ). Sayılar KARTTANdır ve
#: burada yeniden hesaplanmaz; betik bunları ÜRETMEK zorundadır (±0,01).
#: Kartın "×" sütunu BÜYÜK/KÜÇÜK oranıdır (VRTX'te plan riski paydanın 2,03 katı, ötekilerde payda
#: plan riskinin ~1,0 katı) — yön farkı kartın kendi yazımındadır, sayılar aynıdır.
PK2_BEKLENEN = {
    "ECL": {"payda": 11.77, "plan_riski": 11.62, "kat": 1.01},
    "REGN": {"payda": 43.07, "plan_riski": 41.19, "kat": 1.05},
    "MU": {"payda": 59.95, "plan_riski": 59.30, "kat": 1.01},
    "VRTX": {"payda": 13.17, "plan_riski": 26.68, "kat": 2.03},
}


def pk2_gercek(islemler: list[dict]) -> dict:
    """PK (2) — GERÇEK. Kartın dört ön ölçümü betikle birebir (±0,01) üretilmeli."""
    satirlar, gecti = [], True
    by_tic = {i["ticker"]: i for i in islemler if i["ticker"] in PK2_BEKLENEN}
    for tic, bek in sorted(PK2_BEKLENEN.items()):
        i = by_tic.get(tic)
        if i is None or i["payda_turetilen"] is None or i["plan_riski"] is None:
            satirlar.append({"ticker": tic, "gecti": False,
                             "neden": "ölçümde bu sembolün paydası/plan riski ÖLÇÜLEMEDİ"})
            gecti = False
            continue
        p, pr = i["payda_turetilen"], i["plan_riski"]
        kat = max(p, pr) / min(p, pr)
        ok = (abs(p - bek["payda"]) <= PK_TOLERANS
              and abs(pr - bek["plan_riski"]) <= PK_TOLERANS
              and abs(kat - bek["kat"]) <= PK_TOLERANS)
        gecti = gecti and ok
        satirlar.append({"ticker": tic, "payda_olculen": round(p, 4),
                         "payda_beklenen": bek["payda"],
                         "plan_riski_olculen": round(pr, 4),
                         "plan_riski_beklenen": bek["plan_riski"],
                         "kat_olculen": round(kat, 4), "kat_beklenen": bek["kat"],
                         "oran": round(p / pr, 6), "gecti": ok})
    return {"tolerans": PK_TOLERANS, "satirlar": satirlar, "gecti": gecti}


def pk3_capraz(golge_yolu: pathlib.Path, replay_yolu: pathlib.Path, r_alt: float) -> dict:
    """PK (3) — ÇAPRAZ. Aynı oran formülü GÖLGE ve REPLAY yollarında 1,000 vermeli.

    (a) GÖLGE ayağı: `sonuc_…json` içindeki her `pullback` satırı için
        payda = |(çıkış − giriş)/R| ve plan riski = giriş − stop → oran 1,000 ± PK_TOLERANS.
        Gölge paydası TANIMI GEREĞİ giriş riskidir; oran 1'den saparsa formül ya da veri bozuktur.
    (b) REPLAY ayağı: EDG-049 defterinin AYNI planları için payda = |pnl/(r·qty)| ve plan riski =
        `entry − gölge stopu` (replay defteri stop TAŞIMAZ; stop gölge satırından gelir).
        Beklenen sapma SIFIR DEĞİLDİR ve İKİ ARTIKTAN TÜRETİLİR:
          · `size_position`ın AŞAĞI yuvarlaması → payda ∈ [hisse riski, hisse riski·(1 + 1/qty))
          · defterin `r_multiple` YUVARLAMASI → bağıl hata yarım-ulp/|r|; ulp defterin KENDİSİNDEN
            ölçülür (`_r_ulp`: satırların ondalık sayısının AZAMİSİ), varsayılmaz.
        Kabul bandı = [1 − eps_r, 1 + 1/qty + eps_r]: gevşetilmiş bir tolerans değil, ÖLÇÜLMÜŞ bir
        banttır. Kartın düz "±0,01" ifadesi AYRICA raporlanır (hangi işlem sağlıyor, hangisi neden
        sağlamıyor) — iki ölçüt de sonuçta durur, biri ötekini gizlemez.
    """
    if not golge_yolu.exists() or not replay_yolu.exists():
        raise Blok(f"PK (3) girdisi yok: {golge_yolu} / {replay_yolu}")
    g = json.loads(golge_yolu.read_text(encoding="utf-8"))
    replay_satirlari = json.loads(replay_yolu.read_text(encoding="utf-8"))
    replay = {r.get("plan_id"): r for r in replay_satirlari}
    ulp = _r_ulp(replay_satirlari)
    golge_satir, replay_satir = [], []
    for kayit in (g.get("golge") or {}).values():
        s = kayit.get("satir") or {}
        if str(s.get("kurulum") or "") != "pullback":
            continue
        giris, stop, cikis, R = (_sayi(s.get("giris_fiyat")), _sayi(s.get("stop")),
                                 _sayi(s.get("cikis_fiyat")), _sayi(s.get("R")))
        if None in (giris, stop, cikis, R) or R == 0 or giris - stop <= 0:
            golge_satir.append({"plan_id": s.get("plan_id"), "gecti": False,
                                "neden": "gölge satırında giriş/stop/çıkış/R ölçülemedi"})
            continue
        oran = abs((cikis - giris) / R) / (giris - stop)
        golge_satir.append({"plan_id": s.get("plan_id"), "ticker": s.get("ticker"),
                            "oran": round(oran, 6),
                            "gecti": abs(oran - 1.0) <= PK_TOLERANS})
        rr = replay.get(kayit.get("plan_id_049"))
        if rr is None:
            replay_satir.append({"plan_id": kayit.get("plan_id_049"), "gecti": False,
                                 "neden": "EDG-049 defterinde bu planın işlem satırı YOK"})
            continue
        payda, neden = payda_turet(rr, r_alt)
        entry, qty, r = _sayi(rr.get("entry")), _sayi(rr.get("qty")), _sayi(rr.get("r_multiple"))
        if payda is None or entry is None or qty is None or not qty or entry - stop <= 0:
            replay_satir.append({"plan_id": kayit.get("plan_id_049"), "gecti": False,
                                 "neden": neden or "replay satırından payda/plan riski ölçülemedi"})
            continue
        oran_r = payda / (entry - stop)
        # TÜRETİLMİŞ BANT: `floor` artığı (1/qty) + defterin R yuvarlamasının bağıl hatası
        # (yarım-ulp / |r|; ulp defterden ÖLÇÜLDÜ). Yuvarlama İKİ yöne de kayar → bant simetrik.
        eps_r = (0.5 * ulp / abs(r)) if r else 0.0
        taban, tavan = 1.0 - eps_r, 1.0 + 1.0 / qty + eps_r
        replay_satir.append({"plan_id": kayit.get("plan_id_049"), "ticker": rr.get("ticker"),
                             "qty": int(qty), "r_multiple": r, "payda": round(payda, 6),
                             "plan_riski_golge_stopuyla": round(entry - stop, 6),
                             "oran": round(oran_r, 6), "r_ulp": ulp,
                             "turetilmis_bant": [round(taban, 6), round(tavan, 6)],
                             "gecti": taban <= oran_r <= tavan,
                             "kart_duz_tolerans_saglandi": abs(oran_r - 1.0) <= PK_TOLERANS})
    gecti = (bool(golge_satir) and all(s["gecti"] for s in golge_satir)
             and bool(replay_satir) and all(s["gecti"] for s in replay_satir))
    duz = [s for s in replay_satir if not s.get("kart_duz_tolerans_saglandi")]
    return {"golge": golge_satir, "replay": replay_satir, "gecti": gecti, "r_ulp_olculen": ulp,
            "kart_duz_tolerans_disi": [
                {"plan_id": s["plan_id"], "oran": s["oran"], "qty": s.get("qty"),
                 "neden": ("floor artığı 1/qty + 2 ondalıklı `r_multiple` yuvarlaması kartın düz "
                           "±0,01'ini AŞIYOR; türetilmiş tavan içinde kalıyor")}
                for s in duz],
            "kaynak": {"golge": str(golge_yolu.relative_to(KOK)),
                       "replay": str(replay_yolu.relative_to(KOK))}}


# ==================================================================================================
# ÖLÇÜM
# ==================================================================================================
def olc(girdi: pathlib.Path, sha_dosya: pathlib.Path, r_alt: float) -> dict:
    kunye = manifesto_dogrula(girdi, sha_dosya)
    ham = json.loads(girdi.read_text(encoding="utf-8"))
    trades = ham.get("trades") or []
    plans = {p.get("id"): p for p in (ham.get("plans") or [])}
    emirler = ham.get("orders") or []
    olaylar = ham.get("stop_olaylari") or []

    islemler = []
    for t in sorted(trades, key=lambda x: (str(x.get("ts_close")), str(x.get("ticker")))):
        pid = t.get("plan_id")
        plan = plans.get(pid)
        payda, payda_neden = payda_turet(t, r_alt)
        plan_riski, plan_neden = plan_riski_olc(plan, pid)
        plan_stop = _sayi(plan.get("stop")) if plan else None
        entry, exit_ = _sayi(t.get("entry")), _sayi(t.get("exit"))
        giris_riski = (abs(entry - plan_stop) if (entry is not None and plan_stop is not None
                                                  and abs(entry - plan_stop) > 0) else None)
        r = _sayi(t.get("r_multiple"))
        risk_dollars = (abs(_sayi(t.get("pnl_dollars")) / r)
                        if (r and _sayi(t.get("pnl_dollars")) is not None) else None)
        ayna = ayna_bak(emirler, pid)
        sik = siklastirma_bul(olaylar, str(t.get("ticker")), str(t.get("ts_open")),
                              str(t.get("ts_close")), plan_stop)
        oran = (payda / plan_riski) if (payda is not None and plan_riski) else None
        sl_stop = ayna.get("sl_stop_price")
        islemler.append({
            "id": t.get("id"), "ticker": t.get("ticker"), "plan_id": pid,
            "ts_open": t.get("ts_open"), "ts_close": t.get("ts_close"),
            "setup": t.get("setup"), "exit_reason": t.get("exit_reason"),
            "qty": t.get("qty"), "r_multiple": r, "pnl_dollars": _sayi(t.get("pnl_dollars")),
            "scaled_out": t.get("scaled_out"),
            "risk_dollars_turetilen": (round(risk_dollars, 4) if risk_dollars else None),
            "payda_turetilen": (round(payda, 6) if payda is not None else None),
            "payda_olculemedi_neden": payda_neden,
            "plan_riski": (round(plan_riski, 6) if plan_riski else None),
            "plan_riski_olculemedi_neden": plan_neden,
            "giris_riski": (round(giris_riski, 6) if giris_riski else None),
            "giris_riski_neden": (None if giris_riski else
                                  "plan stopu ya da defter girişi ölçülemedi — giriş riski YOK"),
            "oran": (round(oran, 6) if oran else None),
            "oran_bantta": (None if oran is None else ORAN_BANT[0] <= oran <= ORAN_BANT[1]),
            "oran_giris_riskine": (round(payda / giris_riski, 6)
                                   if (payda is not None and giris_riski) else None),
            "siklastirma": sik,
            "broker_sl": {
                "stop_price": sl_stop, "plan_stop": plan_stop,
                "esit_mi": (None if (sl_stop is None or plan_stop is None)
                            else abs(sl_stop - plan_stop) <= 0.01),
                "fark": (None if (sl_stop is None or plan_stop is None)
                         else round(sl_stop - plan_stop, 4)),
                "neden": (None if (sl_stop is not None and plan_stop is not None)
                          else "aynada SL bacağı ya da plan stopu ölçülemedi")},
            "ayna": {**ayna,
                     "giris_bps_defter_vs_ayna": _bps(entry, ayna.get("parent_filled_avg")),
                     "cikis_bps_defter_vs_ayna": _bps(
                         exit_, (ayna.get("cikis_bacagi") or {}).get("filled_avg"))},
            "qty_tanisi": qty_tanisi(_sayi(t.get("qty")) or 0, risk_dollars, plan_riski,
                                     giris_riski, ayna.get("filled_qty")),
        })

    # ---- kapı + birincil ----
    oranli = [i for i in islemler if i["oran"] is not None]
    oranlar = [i["oran"] for i in oranli]
    kapi = {"n_oran": len(oranli), "esik": N_ORAN_ALT, "gecti": len(oranli) >= N_ORAN_ALT,
            "n_islem": len(islemler),
            "n_plansiz": sum(1 for i in islemler if i["plan_riski"] is None),
            "n_payda_olculemedi": sum(1 for i in islemler if i["payda_turetilen"] is None)}
    birincil = {
        "medyan": round(statistics.median(oranlar), 6) if oranlar else None,
        "p10": _yuzdelik(oranlar, 0.10), "p90": _yuzdelik(oranlar, 0.90),
        "min": round(min(oranlar), 6) if oranlar else None,
        "max": round(max(oranlar), 6) if oranlar else None,
        "bant": list(ORAN_BANT),
        "n_bantta": sum(1 for i in oranli if i["oran_bantta"]),
        "n_bant_disi": sum(1 for i in oranli if not i["oran_bantta"]),
        "pay_bant_disi": (round(sum(1 for i in oranli if not i["oran_bantta"]) / len(oranli), 6)
                          if oranli else None),
        "medyan_giris_riskine": (
            round(statistics.median([i["oran_giris_riskine"] for i in oranli
                                     if i["oran_giris_riskine"] is not None]), 6)
            if any(i["oran_giris_riskine"] is not None for i in oranli) else None),
    }

    # ---- 2×2 (oran ∉ bant) × (sıkılaştırma) ----
    hucre = {"bant_disi_sik": 0, "bant_disi_sik_yok": 0, "bant_disi_sik_olculemedi": 0,
             "bantta_sik": 0, "bantta_sik_yok": 0, "bantta_sik_olculemedi": 0}
    for i in oranli:
        yon = "bantta" if i["oran_bantta"] else "bant_disi"
        v = i["siklastirma"]["var"]
        ek = "_sik" if v is True else "_sik_yok" if v is False else "_sik_olculemedi"
        hucre[yon + ek] += 1
    n_bd = birincil["n_bant_disi"]
    eslesme = (hucre["bant_disi_sik"] / n_bd) if n_bd else None
    tablo = {
        "tanim": ("satır: oran ∉ [0,95; 1,05] · sütun: işlem penceresinde stopu YUKARI taşıyan "
                  "olay. 'sik_yok' = 0 OLAY (ölçüldü), 'sik_olculemedi' = hüküm YOK — ikisi "
                  "AYRI sütundur."),
        "hucreler": hucre,
        "eslesme_orani": (round(eslesme, 6) if eslesme is not None else None),
        "eslesme_alt": SIKLASTIRMA_ESLESME_ALT,
        "eslesme_gecti": (None if eslesme is None else eslesme >= SIKLASTIRMA_ESLESME_ALT),
        "eslesme_neden": (None if eslesme is not None else
                          "bant dışı işlem YOK — eşleşme oranı tanımsız (0/0 uydurulmaz)"),
        "siklastirma_olayi_toplam": sum(1 for i in islemler if i["siklastirma"]["var"] is True),
        "olay_sozlugu": {"stop_tasiyan_adlar": list(STOP_TASIYAN_ADLAR),
                         "trail_olayi": TRAIL_OLAYI,
                         "beyan": ("donmuş çekimdeki 242 olayın çoğu ALARM METNİdir "
                                   "(MIRROR_DRIFT/NAKED_POSITION …) ve stop DEĞİŞİKLİĞİ değildir; "
                                   "sıkılaştırma yalnız yukarıdaki adlarla ve olayın KENDİ "
                                   "alanlarıyla ölçülür")},
    }

    # ---- tanı ----
    kirilim = {}
    for i in oranli:
        anahtar = f"{i['setup']}"
        d = kirilim.setdefault(anahtar, {"n": 0, "oranlar": []})
        d["n"] += 1
        d["oranlar"].append(i["oran"])
    for d in kirilim.values():
        d["medyan"] = round(statistics.median(d["oranlar"]), 6)
        d.pop("oranlar")
    giris_bps = [i["ayna"]["giris_bps_defter_vs_ayna"] for i in islemler
                 if i["ayna"]["giris_bps_defter_vs_ayna"] is not None]
    cikis_bps = [i["ayna"]["cikis_bps_defter_vs_ayna"] for i in islemler
                 if i["ayna"]["cikis_bps_defter_vs_ayna"] is not None]
    tani = {
        "kurulum_kirilimi": kirilim,
        "defter_vs_ayna_bps": {
            "giris": {"n": len(giris_bps),
                      "medyan": round(statistics.median(giris_bps), 2) if giris_bps else None,
                      "min": min(giris_bps) if giris_bps else None,
                      "max": max(giris_bps) if giris_bps else None},
            "cikis": {"n": len(cikis_bps),
                      "medyan": round(statistics.median(cikis_bps), 2) if cikis_bps else None,
                      "min": min(cikis_bps) if cikis_bps else None,
                      "max": max(cikis_bps) if cikis_bps else None},
            "beyan": ("EXE-2026-007 sınıfı TANI — hüküm değil: defter fiyatı iç modeldir, ayna "
                      "dolumu ayrı bir olgudur")},
        "sl_bacagi_plan_stopuna_esit": {
            "esit": sum(1 for i in islemler if i["broker_sl"]["esit_mi"] is True),
            "farkli": sum(1 for i in islemler if i["broker_sl"]["esit_mi"] is False),
            "olculemedi": sum(1 for i in islemler if i["broker_sl"]["esit_mi"] is None)},
        "qty_tabani": {},
        "sifir_r_kumesi": [
            {"id": i["id"], "ticker": i["ticker"], "r_multiple": i["r_multiple"],
             "neden": i["payda_olculemedi_neden"]}
            for i in islemler if i["payda_turetilen"] is None and i["r_multiple"] is not None],
    }
    for i in islemler:
        s = i["qty_tanisi"]["sinif"]
        tani["qty_tabani"][s] = tani["qty_tabani"].get(s, 0) + 1

    return {"islemler": islemler, "kapi": kapi, "birincil": birincil, "tablo_2x2": tablo,
            "tani": tani, "girdi": kunye,
            "olculemeyenler": [{"id": i["id"], "ticker": i["ticker"],
                                "payda": i["payda_olculemedi_neden"],
                                "plan_riski": i["plan_riski_olculemedi_neden"]}
                               for i in islemler
                               if i["payda_turetilen"] is None or i["plan_riski"] is None]}


def kos(girdi: pathlib.Path, cikti_dizin: pathlib.Path, state_dizin: pathlib.Path,
        sha_dosya: pathlib.Path, golge_yolu: pathlib.Path = PK3_GOLGE,
        replay_yolu: pathlib.Path = PK3_REPLAY) -> tuple[dict, pathlib.Path]:
    """Ölçümü koşar, sonucu yazar. PK düşerse `PKDustu` (çıkış 2) — sayı yayılmaz."""
    state_dizin = _ortak.state_izni(state_dizin, KOK)
    # Motorun state kökü GEÇİCİ yola DAYATILIR: bu betik motoru çağırmaz, ama `sayim` ithali
    # üzerinden gelen herhangi bir tembel yazım denemesi canlı deftere DEĞİL buraya gitsin.
    os.environ["MERIDIAN_ROOT"] = str(state_dizin.parent)
    import sayim  # noqa: E402  — TEK KAYNAK: `R_MULTIPLE_ALT` burada yeniden yazılmaz
    r_alt = float(sayim.R_MULTIPLE_ALT)

    sonuc = olc(girdi, sha_dosya, r_alt)
    pk = {"pk1_sentetik": pk1_sentetik(r_alt),
          "pk2_gercek": pk2_gercek(sonuc["islemler"]),
          "pk3_capraz": pk3_capraz(golge_yolu, replay_yolu, r_alt)}
    pk["hepsi_gecti"] = all(pk[k]["gecti"] for k in ("pk1_sentetik", "pk2_gercek", "pk3_capraz"))

    kunye = {
        "kart": "EDG-2026-091", "olculdu_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "motor_yolu": str(KOK), "state_dizin_dayatilan": str(state_dizin),
        "r_multiple_alt": r_alt,
        "r_multiple_alt_kaynagi": "research/olcumler/edg088_golge_pilot/sayim.py::R_MULTIPLE_ALT",
        "esikler": {"oran_bant": list(ORAN_BANT), "siklastirma_eslesme_alt": SIKLASTIRMA_ESLESME_ALT,
                    "n_oran_alt": N_ORAN_ALT, "pk_tolerans": PK_TOLERANS},
        "payda_tanimlari": PAYDA_TANIMLARI, "payda_ayrismalari": PAYDA_AYRISMALARI,
        "hukum": "YOK — kart hükmü Rol-1'indir (bu betik yalnız ölçer)",
    }
    if not pk["hepsi_gecti"]:
        raise PKDustu(json.dumps({**kunye, "pk": pk}, ensure_ascii=False, indent=1))

    tam = {**kunye, "pk": pk, **sonuc}
    cikti_dizin.mkdir(parents=True, exist_ok=True)
    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S+0000")
    yol = cikti_dizin / f"sonuc_{damga}.json"
    yol.write_text(json.dumps(tam, ensure_ascii=False, indent=1), encoding="utf-8")
    return tam, yol


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-091 canlı R paydası ölçümü")
    ap.add_argument("--girdi", type=pathlib.Path, default=VARSAYILAN_GIRDI)
    ap.add_argument("--sha-dosya", type=pathlib.Path, default=VARSAYILAN_SHA)
    ap.add_argument("--cikti-dizin", type=pathlib.Path, default=SANDBOX)
    ap.add_argument("--state-dizin", type=pathlib.Path, default=None)
    a = ap.parse_args(argv)
    state = a.state_dizin or (a.cikti_dizin / "_sanal_state_koku" / "state")
    try:
        tam, yol = kos(a.girdi, a.cikti_dizin, state, a.sha_dosya)
    except PKDustu as e:
        print("PK DÜŞTÜ — hiçbir ölçüm sayısı yayılmaz (kart kill#4):", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 2
    except Blok as e:
        print(f"BLOK (ön şart tutmadı): {e}", file=sys.stderr)
        return 1
    print(f"sonuç: {yol}")
    k, b = tam["kapi"], tam["birincil"]
    print(f"ADIM-0 kapısı: n_oran={k['n_oran']} (eşik {k['esik']}) → "
          f"{'GEÇTİ' if k['gecti'] else 'DÜŞTÜ'}")
    print(f"oran medyanı={b['medyan']} p10={b['p10']} p90={b['p90']} "
          f"bant dışı {b['n_bant_disi']}/{k['n_oran']}")
    print(f"2×2: {tam['tablo_2x2']['hucreler']} eşleşme={tam['tablo_2x2']['eslesme_orani']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
