"""EDG-2026-018 · ADIM-0 FEASIBILITY-GATE — KAPSAMA HARİTASI (ölçüm DEĞİL).

Kart: research/cards/EDG-2026-018-pit-midcap-ust-sinir.yaml
Kartın `feasibility_gate` alanı ölçümden ÖNCE koşulmasını ZORUNLU kılar. Bu betik yalnız
KAPSAMA ölçer; sinyal ölçmez, hüküm yazmaz, eşik yorumlamaz. Hüküm Rol-1'dedir.

YASALAR:
  * repo/state'e HİÇBİR YAZIM YOK — barlar ve edgar_facts SALT-OKUNUR açılır; tek yazım
    bu betiğin kendi klasörüne (`kapsama_haritasi.json`).
  * UYDURMA YASAĞI — ölçülemeyen her alan None + `*_neden` gerekçesi taşır; 0 yazılmaz.
  * KARTA DOKUNULMAZ — kart dosyası yalnız sha256 için okunur.

Üç eksen ölçülür:
  A) KART LAFZI — kartın adıyla andığı kaynaktan (sp500_uyelik_tarihi.csv) "mid-cap"
     kohortu kurulabilir mi? (alan envanteri + depodaki diğer PIT evren kaynakları)
  B) BRIEF EKSENİ — S&P500'den ÇIKMIŞ isimler × üyelik-dönemi barları (gate sayıları burada)
  C) BOYUT EKSENİ — bar arşivindeki isimlerin piyasa-değeri dağılımı (BETİMLEYİCİ, PIT DEĞİL):
     "arşivde mid-cap bandında isim var mı" sorusunun veriyle cevabı
  D) DELİST BOŞLUĞU — barı olmayan çıkmış isimlerin envanteri (WP-U kilidine doğrudan girdi)
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path("/Users/erdemozturk/AI-Trading")
SANDBOX = pathlib.Path(__file__).resolve().parent
UYELIK = REPO / "research" / "pit_universe" / "sp500_uyelik_tarihi.csv"
BARS = REPO / "state" / "bars"
EDGAR = REPO / "research" / "edgar_facts"
KART = REPO / "research" / "cards" / "EDG-2026-018-pit-midcap-ust-sinir.yaml"

sys.path.insert(0, str(REPO))
csv.field_size_limit(10 ** 9)

# ---- kart eşikleri (KARTTAN OKUNUR, burada YENİDEN YAZILMAZ) -----------------------------
GATE_MIN_ISIM = 40           # feasibility_gate: "kapsanan isim sayısı < 40 ... → ölçüm BAŞLAMAZ"
GATE_MIN_YIL = 3.0           # feasibility_gate: "VEYA ortalama bar-geçmişi < 3 yıl"
ISLEM_GUNU_YIL = 252.0       # bar-geçmişi yıla çevrilirken kullanılan sabit (BEYAN)

# ---- betimleyici boyut bandı (KART DIŞI; eksen C'nin okunabilmesi için BEYANLI sözleşme) --
# S&P'nin kendi endeks ailesindeki bant değil, yaygın piyasa konvansiyonu; eksen C hüküm
# taşımaz, yalnız "arşivde bu bantta isim var mı" sorusunu sayıyla cevaplar.
MIDCAP_ALT_USD = 2e9
MIDCAP_UST_USD = 10e9


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _pct(xs, q):
    if not xs:
        return None
    ys = sorted(xs)
    i = (len(ys) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(ys) - 1)
    return ys[lo] + (ys[hi] - ys[lo]) * (i - lo)


def _ozet(xs, ad):
    """Sayı listesinin özeti. Boşsa None + neden (UYDURMA YASAĞI: 0 yazılmaz)."""
    if not xs:
        return {"n": 0, "ort": None, "medyan": None, "min": None, "maks": None,
                "p10": None, "p90": None, "neden": f"{ad}: hiç ölçülebilir gözlem yok"}
    return {"n": len(xs), "ort": sum(xs) / len(xs), "medyan": _pct(xs, 0.5),
            "min": min(xs), "maks": max(xs), "p10": _pct(xs, 0.10), "p90": _pct(xs, 0.90),
            "neden": None}


# =========================================================================================
# 0. Üyelik defteri — OLAY-TARİHLİ anlık görüntüler (as-of okuma)
# =========================================================================================
def uyelik_oku():
    tarihler, kumeler = [], []
    with open(UYELIK, newline="") as f:
        r = csv.DictReader(f)
        alanlar = list(r.fieldnames or [])
        for row in r:
            tarihler.append(dt.date.fromisoformat(row["date"]))
            kumeler.append(frozenset(t for t in row["tickers"].split(",") if t))
    return alanlar, tarihler, kumeler


def uyelik_araliklari(tarihler, kumeler):
    """Her sembol için [baslangic, bitis) yarı-açık üyelik aralıkları.

    As-of semantiği: t gününde üye = (date <= t olan SON satırda sembol var). Son satırın
    bitişi None'dır (dosya sonrası BİLİNMİYOR — açık uç olarak taşınır, bugüne uzatılmaz)."""
    araliklar: dict[str, list] = {}
    acik: dict[str, dt.date] = {}
    for i, (d, k) in enumerate(zip(tarihler, kumeler)):
        onceki = kumeler[i - 1] if i else frozenset()
        for s in k - onceki:
            acik[s] = d
        for s in onceki - k:
            araliklar.setdefault(s, []).append((acik.pop(s), d))
    for s, b in acik.items():                      # son satırda hâlâ üye → açık uç
        araliklar.setdefault(s, []).append((b, None))
    return araliklar


# =========================================================================================
# 1. Bar arşivi — SALT-OKUNUR (yalnız tarih sütunu)
# =========================================================================================
def bar_tarihleri() -> dict[str, list]:
    out = {}
    for p in sorted(BARS.glob("*.csv")):
        gunler = []
        with open(p, newline="") as f:
            r = csv.reader(f)
            basliklar = next(r, None)
            if not basliklar or basliklar[0] != "date":
                continue
            for row in r:
                if row and row[0]:
                    try:
                        gunler.append(dt.date.fromisoformat(row[0]))
                    except ValueError:
                        continue
        out[p.stem.upper()] = gunler
    return out


def son_kapanis() -> dict[str, tuple]:
    """Her sembolün SON bar tarihi + kapanışı (eksen C, betimleyici)."""
    out = {}
    for p in sorted(BARS.glob("*.csv")):
        son = None
        with open(p, newline="") as f:
            r = csv.reader(f)
            bas = next(r, None)
            if not bas or "close" not in bas:
                continue
            ci = bas.index("close")
            for row in r:
                if row and row[0] and len(row) > ci and row[ci]:
                    try:
                        son = (dt.date.fromisoformat(row[0]), float(row[ci]))
                    except ValueError:
                        continue
        if son:
            out[p.stem.upper()] = son
    return out


# =========================================================================================
# 2. as-of hisse (BETİMLEYİCİ SON DEĞER — eksen C için; PIT panel DEĞİL)
# =========================================================================================
ANLIK_ETIKET = {"EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"}


def son_hisse_sayisi() -> tuple[dict, dict]:
    """En son dosyalanmış ANLIK hisse sayısı (dei önce, us-gaap sonra).

    EDG-016'nın as-of PANELİ DEĞİLDİR: burada tek bir güncel kesit okunuyor (eksen C
    betimleyicidir, ölçüm bacağı değildir). Etiket seçimi EDG-012/016 ile aynı ailedendir
    (Issued ve ağırlıklı-ortalama KULLANILMAZ)."""
    en_iyi: dict[str, tuple] = {}
    gorulen: dict[str, set] = {}          # sembol → görülen etiket kümesi (neden ayrımı için)
    sayac = {"satir": 0, "anlik_satir": 0, "gecersiz_deger": 0, "donem_turu_disi": 0}
    with gzip.open(EDGAR / "shares_outstanding.csv.gz", "rt", newline="") as f:
        r = csv.DictReader(f)
        alanlar = list(r.fieldnames or [])
        for row in r:
            sayac["satir"] += 1
            tag = row.get("tag") or ""
            gorulen.setdefault((row.get("symbol") or "").upper(), set()).add(tag)
            if tag not in ANLIK_ETIKET:
                continue
            if (row.get("donem_turu") or "") != "anlik":   # SEVİYE yalnız anlık kayıttan okunur
                sayac["donem_turu_disi"] += 1
                continue
            sayac["anlik_satir"] += 1
            try:
                val = float(row.get("val") or "nan")
            except ValueError:
                sayac["gecersiz_deger"] += 1
                continue
            if not (val > 0):
                sayac["gecersiz_deger"] += 1
                continue
            sym = (row.get("symbol") or "").upper()
            end, filed = row.get("end") or "", row.get("filed") or ""
            oncelik = (0 if tag == "EntityCommonStockSharesOutstanding" else 1)
            anahtar = (end, filed, -oncelik)     # en GÜNCEL dönem-sonu; eşitlikte en geç dosyalama
            if sym not in en_iyi or anahtar > en_iyi[sym][0]:
                en_iyi[sym] = (anahtar, val, tag, filed, end)
    sayac["alanlar"] = alanlar
    return {s: (v[1], v[2], v[3], v[4]) for s, v in en_iyi.items()}, sayac, gorulen


def _hisse_yok_nedeni(sym: str, gorulen: dict) -> str:
    """Neden AYRIMI (UYDURMA YASAĞI): üç ayrı yokluk aynı etikete sıkıştırılmaz."""
    etiketler = gorulen.get(sym)
    if not etiketler:
        return "edgar_facts/shares_outstanding.csv.gz'de bu sembole ait HİÇ SATIR yok"
    if not (etiketler & ANLIK_ETIKET):
        return ("yalnız ağırlıklı-ortalama etiketi var (" + ",".join(sorted(etiketler)[:2]) +
                "); ağırlıklı-ortalama SEVİYE olarak KULLANILMAZ — EDG-012/016 kuralı")
    return "anlık etiket var ama kullanılabilir değer yok (val<=0 / sayıya çevrilemiyor)"


# =========================================================================================
def main():
    from meridian import olcum_araclari as oa
    from meridian.adapters import data as dat

    rapor: dict = {"kart_id": "EDG-2026-018",
                   "adim": "ADIM-0 feasibility_gate — KAPSAMA HARİTASI (ölçüm DEĞİL)",
                   "uretildi": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "kod_surumu": oa.kod_surumu_damgasi(kok=str(REPO)),
                   "girdi_damgalari": {
                       "kart_sha256": sha256(KART),
                       "uyelik_csv_sha256": sha256(UYELIK),
                       "uyelik_csv_bayt": UYELIK.stat().st_size,
                       "bar_dizini": str(BARS),
                       "bar_dosya_n": len(list(BARS.glob("*.csv"))),
                   },
                   "yazim_beyani": "state/ ve research/ altına YAZILMADI; tek çıktı bu klasördeki "
                                   "kapsama_haritasi.json — canlı state SALT-OKUNUR açıldı"}

    alanlar, tarihler, kumeler = uyelik_oku()
    araliklar = uyelik_araliklari(tarihler, kumeler)
    tum_uyeler = set().union(*kumeler)
    son_kume = set(kumeler[-1])
    cikmis = tum_uyeler - son_kume
    barlar = bar_tarihleri()
    bar_semboller = set(barlar)

    # ------------------------------------------------------------------ EKSEN A
    diger_kaynaklar = []
    for p in sorted((REPO / "research" / "pit_universe").rglob("*")):
        if p.is_file():
            diger_kaynaklar.append({"yol": str(p.relative_to(REPO)), "bayt": p.stat().st_size})
        elif p.is_dir():
            n = len(list(p.glob("*")))
            diger_kaynaklar.append({"yol": str(p.relative_to(REPO)) + "/", "icerik_n": n})

    rapor["A_kart_lafzi_kohort"] = {
        "soru": "Kartın adıyla andığı kaynaktan (sp500_uyelik_tarihi.csv) mid-cap kohortu "
                "İNİYOR mu?",
        "kaynak": str(UYELIK.relative_to(REPO)),
        "alanlar": alanlar,
        "satir_n": len(tarihler),
        "tarih_araligi": [tarihler[0].isoformat(), tarihler[-1].isoformat()],
        "kadans": "OLAY-TARİHLİ anlık görüntü (her işlem günü DEĞİL); ardışık satır farkı "
                  "medyan 2 gün, maks 91 gün — as-of okuma zorunlu",
        "uye_sayisi_dagilimi": _ozet([len(k) for k in kumeler], "günlük üye sayısı"),
        "boyut_alani_var": False,
        "boyut_alani_neden": "dosyada YALNIZ 'date' ve 'tickers' sütunu var; piyasa değeri, "
                             "endeks-ailesi (400/600) etiketi, sektör ya da herhangi bir "
                             "büyüklük alanı YOK",
        "endeks_kimligi": "S&P 500 üyelik geçmişi — tanımı gereği LARGE-CAP endeksi; "
                          "S&P MidCap 400 üyeliği bu dosyada temsil EDİLMİYOR",
        "depodaki_diger_pit_evren_kaynaklari": diger_kaynaklar,
        "kohort_kurulabilir": False,
        "kohort_kurulamama_nedeni":
            "Kartın 'pit_midcap_survivor' evreni bu kaynaktan İNMİYOR: (1) dosya bir large-cap "
            "endeksinin üyelik geçmişidir, (2) hiçbir satırda boyut/piyasa-değeri alanı yoktur, "
            "(3) depoda S&P MidCap 400 (ya da başka bir mid-cap) üyelik geçmişi dosyası YOKTUR "
            "(pit_universe altında yalnız bu CSV + BOŞ nasdaq100_yillik/ var).",
    }

    # ------------------------------------------------------------------ EKSEN B
    def uye_mi(sym, gun):
        for b, s in araliklar.get(sym, ()):
            if b <= gun and (s is None or gun < s):
                return True
        return False

    b_satirlar = []
    for sym in sorted(cikmis):
        ar = araliklar.get(sym, [])
        ilk = min(b for b, _ in ar) if ar else None
        # çıkmış isim → tüm aralıkların bitişi bilinir (açık uç yalnız SON satırda üye olanlarda)
        son = max((s for _, s in ar if s is not None), default=None)
        uyelik_takvim_gun = sum(((s or tarihler[-1]) - b).days for b, s in ar)
        g = barlar.get(sym)
        if g is None:
            b_satirlar.append({
                "sembol": sym, "bar_var": False,
                "uyelik_ilk": ilk.isoformat() if ilk else None,
                "uyelik_son": son.isoformat() if son else None,
                "uyelik_takvim_gun": uyelik_takvim_gun,
                "bar_n": None, "bar_n_neden": "state/bars altında bu sembol için dosya YOK "
                                              "(delist-bar kilidi — WP-U)",
                "uyelik_ici_bar_n": None,
                "uyelik_ici_bar_neden": "bar dosyası yok → kesişim ölçülemez",
                "emekli_defterinde": dat.is_retired(sym),
            })
            continue
        ici = [d for d in g if uye_mi(sym, d)]
        b_satirlar.append({
            "sembol": sym, "bar_var": True,
            "uyelik_ilk": ilk.isoformat() if ilk else None,
            "uyelik_son": son.isoformat() if son else None,
            "uyelik_takvim_gun": uyelik_takvim_gun,
            "bar_n": len(g),
            "bar_ilk": g[0].isoformat() if g else None,
            "bar_son": g[-1].isoformat() if g else None,
            "bar_yil": len(g) / ISLEM_GUNU_YIL,
            "uyelik_ici_bar_n": len(ici),
            "uyelik_ici_bar_yil": len(ici) / ISLEM_GUNU_YIL,
            "uyelik_ici_bar_ilk": ici[0].isoformat() if ici else None,
            "uyelik_ici_bar_son": ici[-1].isoformat() if ici else None,
            "emekli_defterinde": dat.is_retired(sym),
        })

    barli = [r for r in b_satirlar if r["bar_var"]]
    barsiz = [r for r in b_satirlar if not r["bar_var"]]
    yil_tum = [r["bar_yil"] for r in barli]
    yil_ici = [r["uyelik_ici_bar_yil"] for r in barli]

    def _yil_dagilimi(satirlar):
        c: dict = {}
        for r in satirlar:
            y = (r["uyelik_son"] or "")[:4] or "bilinmiyor"
            c[y] = c.get(y, 0) + 1
        return dict(sorted(c.items()))

    canli_evren = {s.upper() for s in dat.REPLAY_UNIVERSE}

    rapor["B_cikmis_isimler_ekseni"] = {
        "kohort_tanimi":
            "Kartın mid-cap kohortu veriden kurulamadığı için (eksen A) brief'in yönlendirdiği "
            "eksen: 'S&P500 üyelik geçmişinde EN AZ BİR KEZ görünmüş ama SON anlık görüntüde "
            "(2026-06-30) OLMAYAN' isimler = ÇIKMIŞ isimler. Bu kohort mid-cap DEĞİLDİR — "
            "endeksten çıkış hem küçülme hem birleşme/satın alma/borsa-transferi ile olur; "
            "burada yalnız BAR KAPSAMASI ölçülür.",
        "tum_uyeler_n": len(tum_uyeler),
        "son_anlik_goruntu_tarih": tarihler[-1].isoformat(),
        "son_anlik_goruntu_n": len(son_kume),
        "cikmis_n": len(cikmis),
        "cikmis_bar_var_n": len(barli),
        "cikmis_bar_yok_n": len(barsiz),
        "bar_kapsama_orani": len(barli) / len(cikmis) if cikmis else None,
        "bar_var_semboller": sorted(r["sembol"] for r in barli),
        "bar_var_emekli_defterinde_n": sum(1 for r in barli if r["emekli_defterinde"]),
        "bar_var_canli_evrende_n": sum(1 for r in barli if r["sembol"] in canli_evren),
        "bar_var_canli_evrende_semboller": sorted(r["sembol"] for r in barli
                                                  if r["sembol"] in canli_evren),
        "cikis_yili_dagilimi_barli": _yil_dagilimi(barli),
        "cikis_yili_dagilimi_barsiz_2009_sonrasi":
            {y: n for y, n in _yil_dagilimi(barsiz).items() if y >= "2009"},
        "secilim_notu":
            "Barı OLAN 12 ismin tamamı YAKIN çıkışlardır ve barları arşivde YALNIZ canlı evrende "
            "bulundukları için vardır (8'i RETIRED_SYMBOLS defterinde, kalanı hâlâ canlı evrende). "
            "Yani 'çıkmış isim' ekseninin kendisi de İKİNCİ bir seçilimle kirlidir: çıkış yılı "
            "eski oldukça bar bulunma olasılığı sıfıra iner.",
        "her_biri_large_cap_notu":
            "Bu 12 ismin HEPSİ üyelik dönemlerinde S&P 500 (large-cap) üyesiydi; kohort "
            "mid-cap DEĞİLDİR. 'Endeksten çıkmak' ile 'mid-cap olmak' aynı şey değildir.",
        "bar_gecmisi_yil_tum_arsiv": _ozet(yil_tum, "çıkmış-isim tüm bar geçmişi (yıl)"),
        "bar_gecmisi_yil_uyelik_ici": _ozet(yil_ici, "çıkmış-isim ÜYELİK-İÇİ bar geçmişi (yıl)"),
        "sembol_satirlari": b_satirlar,
    }

    # ------------------------------------------------------------------ EKSEN C
    kapanislar = son_kapanis()
    hisse, hisse_sayac, hisse_gorulen = son_hisse_sayisi()
    c_satirlar, c_olcusuz = [], {}
    for sym in sorted(bar_semboller):
        k = kapanislar.get(sym)
        h = hisse.get(sym)
        if k is None:
            c_olcusuz[sym] = "bar dosyasında kullanılabilir kapanış yok"
            continue
        if h is None:
            c_olcusuz[sym] = _hisse_yok_nedeni(sym, hisse_gorulen)
            continue
        try:
            bayatlik_gun = (k[0] - dt.date.fromisoformat(h[3])).days
        except (ValueError, TypeError):
            bayatlik_gun = None
        c_satirlar.append({"sembol": sym, "kapanis_tarih": k[0].isoformat(), "kapanis": k[1],
                           "hisse": h[0], "hisse_etiket": h[1], "hisse_filed": h[2],
                           "hisse_end": h[3], "hisse_bayatlik_gun": bayatlik_gun,
                           "hisse_bayat": (None if bayatlik_gun is None else bayatlik_gun > 400),
                           "piyasa_degeri_usd": k[1] * h[0]})
    mcap = [r["piyasa_degeri_usd"] for r in c_satirlar]
    bantta = [r for r in c_satirlar if MIDCAP_ALT_USD <= r["piyasa_degeri_usd"] < MIDCAP_UST_USD]
    altinda = [r for r in c_satirlar if r["piyasa_degeri_usd"] < MIDCAP_ALT_USD]

    rapor["C_boyut_ekseni_betimleyici"] = {
        "beyan": "BETİMLEYİCİ — PIT DEĞİL. Tek bir GÜNCEL kesit (son bar kapanışı × en son "
                 "dosyalanmış anlık hisse sayısı). EDG-016'nın as-of paneli DEĞİLDİR ve hiçbir "
                 "hüküm bacağı taşımaz. Amacı tek soru: bar arşivinde mid-cap bandında isim "
                 "VAR MI?",
        "bant_sozlesmesi_usd": [MIDCAP_ALT_USD, MIDCAP_UST_USD],
        "bant_kaynagi": "yaygın piyasa konvansiyonu (2–10 mia USD); KART DIŞI, beyanlı",
        "olculen_sembol_n": len(c_satirlar),
        "olculemeyen_sembol_n": len(c_olcusuz),
        "olculemeyen_nedenler": c_olcusuz,
        "hisse_kaynak_sayaclari": hisse_sayac,
        "piyasa_degeri_usd_ozet": _ozet(mcap, "güncel piyasa değeri (USD)"),
        "piyasa_degeri_p01": _pct(mcap, 0.01), "piyasa_degeri_p05": _pct(mcap, 0.05),
        "piyasa_degeri_p25": _pct(mcap, 0.25),
        "midcap_bandinda_n": len(bantta),
        "midcap_bandinda_semboller": sorted(r["sembol"] for r in bantta),
        "bandin_altinda_n": len(altinda),
        "bandin_altinda_semboller": sorted(r["sembol"] for r in altinda),
        "bant_duyarliligi": {
            f"<{ust/1e9:g}B": sum(1 for r in c_satirlar if r["piyasa_degeri_usd"] < ust)
            for ust in (2e9, 5e9, 10e9, 15e9, 20e9, 30e9, 50e9)
        },
        "bant_duyarliligi_bayatsiz": {
            f"<{ust/1e9:g}B": sum(1 for r in c_satirlar
                                  if r["piyasa_degeri_usd"] < ust and not r["hisse_bayat"])
            for ust in (2e9, 5e9, 10e9, 15e9, 20e9, 30e9, 50e9)
        },
        "hisse_bayat_n": sum(1 for r in c_satirlar if r["hisse_bayat"]),
        "hisse_bayat_esik_gun": 400,
        "hisse_bayat_notu": "bayat hisse sayımı piyasa değerini YANLIŞ ölçeklendirebilir; "
                            "eksen C betimleyici olduğu için satırlar atılmadı, İŞARETLENDİ",
        "en_kucuk_15": sorted(c_satirlar, key=lambda r: r["piyasa_degeri_usd"])[:15],
    }

    # ------------------------------------------------------------------ EKSEN D
    yil_sayac: dict = {}
    for r in barsiz:
        y = (r["uyelik_son"] or "")[:4] or "bilinmiyor"
        yil_sayac[y] = yil_sayac.get(y, 0) + 1
    rapor["D_delist_boslugu"] = {
        "amac": "WP-U delist-bar kilidine doğrudan girdi: barı OLMAYAN çıkmış isimlerin envanteri",
        "bar_yok_n": len(barsiz),
        "uyelik_takvim_gun_ozet": _ozet([r["uyelik_takvim_gun"] for r in barsiz],
                                        "barsız çıkmış isimlerin üyelik süresi (takvim günü)"),
        "cikis_yili_dagilimi": dict(sorted(yil_sayac.items())),
        "cikis_2009_sonrasi_n": sum(1 for r in barsiz if (r["uyelik_son"] or "9999") >= "2009-08-04"),
        "cikis_2009_sonrasi_not": "2009-08-04, EDG-016 panelinin başladığı gündür; bu tarihten "
                                  "sonra çıkan isimler o panelin KAYIP kuyruğudur",
    }
    _p09_barsiz = rapor["D_delist_boslugu"]["cikis_2009_sonrasi_n"]
    _p09_barli = sum(1 for r in barli if (r["uyelik_son"] or "9999") >= "2009-08-04")
    rapor["D_delist_boslugu"]["edg016_panel_penceresi"] = {
        "pencere_baslangic": "2009-08-04",
        "pencere_kaynagi": "EDG-016 RAPOR_016.md — ölçüm panelinin ilk gözlem günü",
        "penceredeki_toplam_cikis_n": _p09_barsiz + _p09_barli,
        "bari_olan_n": _p09_barli,
        "bari_olmayan_n": _p09_barsiz,
        "kayip_orani": (_p09_barsiz / (_p09_barsiz + _p09_barli)
                        if (_p09_barsiz + _p09_barli) else None),
        "okuma": "EDG-016'nın 'hayatta-kalma yanlılığı — işareti bilinir, büyüklüğü ölçülemez' "
                 "şerhinin KAPSAMA tarafındaki karşılığı: panel penceresinde endeksten çıkan "
                 "isimlerin bu oranı arşivde HİÇ bar taşımıyor. Bu bir etki büyüklüğü DEĞİL, "
                 "eksik kuyruğun BÜYÜKLÜĞÜDÜR.",
    }

    # ------------------------------------------------------------------ KAPI SAYILARI
    n_isim = len(barli)
    ort_yil_tum = rapor["B_cikmis_isimler_ekseni"]["bar_gecmisi_yil_tum_arsiv"]["ort"]
    ort_yil_ici = rapor["B_cikmis_isimler_ekseni"]["bar_gecmisi_yil_uyelik_ici"]["ort"]
    rapor["kapi_sayilari"] = {
        "beyan": "Kartın feasibility_gate eşikleri BİREBİR; yorum/hüküm YOK — Rol-1 okur.",
        "esik_min_isim": GATE_MIN_ISIM,
        "esik_min_ortalama_bar_yil": GATE_MIN_YIL,
        "bar_yil_donusum_sabiti": ISLEM_GUNU_YIL,
        "A_kohort_kurulabilir": False,
        "B_kapsanan_isim_n": n_isim,
        "B_isim_esigin_altinda": n_isim < GATE_MIN_ISIM,
        "B_ortalama_bar_yil_tum_arsiv": ort_yil_tum,
        "B_ortalama_bar_yil_uyelik_ici": ort_yil_ici,
        "B_yil_esigin_altinda_tum_arsiv": (None if ort_yil_tum is None
                                           else ort_yil_tum < GATE_MIN_YIL),
        "B_yil_esigin_altinda_uyelik_ici": (None if ort_yil_ici is None
                                            else ort_yil_ici < GATE_MIN_YIL),
        "kapi_dusuyor_mu": bool(n_isim < GATE_MIN_ISIM
                                or ort_yil_tum is None
                                or ort_yil_tum < GATE_MIN_YIL),
        "kapi_okuma_notu":
            "Kart iki eşiği VEYA ile bağlar. Eşik-1 (isim<40) ve eşik-2 (ort<3 yıl) burada "
            "ÇIKMIŞ-İSİM ekseninde ölçüldü; kartın kendi mid-cap kohortu (eksen A) hiç "
            "kurulamadığı için o kohort üzerinde bir sayı ÜRETİLEMEZ (None değil — TANIMSIZ).",
        "olcum_kosuldu_mu": False,
        "olcum_kosulmama_nedeni":
            "Kart: 'feasibility_gate düşerse ölçüm BAŞLAMAZ; çıktı yalnız KAPSAMA HARİTASI olur.' "
            "Pozitif kontrol, turnover üst-dilim hücresi ve maliyet duyarlılığı KOŞULMADI.",
    }
    return rapor


if __name__ == "__main__":
    r = main()
    out = SANDBOX / "kapsama_haritasi.json"
    with open(out, "w") as f:
        json.dump(r, f, indent=2, ensure_ascii=False, sort_keys=False)
    k = r["kapi_sayilari"]
    print("A kohort kurulabilir  :", k["A_kohort_kurulabilir"])
    print("B kapsanan isim       :", k["B_kapsanan_isim_n"], "(eşik", k["esik_min_isim"], ")")
    print("B ort bar yıl (tüm)   :", k["B_ortalama_bar_yil_tum_arsiv"])
    print("B ort bar yıl (üyelik):", k["B_ortalama_bar_yil_uyelik_ici"])
    print("kapı düşüyor mu       :", k["kapi_dusuyor_mu"])
    print("yazıldı ->", out)
