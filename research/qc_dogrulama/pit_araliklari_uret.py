#!/usr/bin/env python3
"""EDG-2026-021 · PIT S&P 500 üyelik ARALIKLARI üreticisi (YEREL — QC'ye bağlanmaz).

NE YAPAR: `research/pit_universe/sp500_uyelik_tarihi.csv` dosyasını okur, ticker → üyelik
aralıklarına sıkıştırır ve QC defterinin `qc_defter_021_d.py` (gerekirse `_e.py`, `_f.py` …)
parçalarını ÜRETİR. Parça dosyaları QC Research'e yüklenir; defter oradan `pit_uyeler(t)`
çağırır.

NE İTHAL ETMEZ: `meridian`. (CLAUDE.md §2 — pytest DIŞI koşan ve `meridian.obs`'a ulaşan
betik canlı YEREL deftere yazar; bu üretici bilerek stdlib'de kalır.)

KAYNAK BİÇİMİ — ÖLÇÜLDÜ 2026-09-03, VARSAYILMADI:
    2.718 satır · 1996-01-02 → 2026-06-30 · satır başına 487–507 ticker.
    Satırlar GÜNLÜK DEĞİL: 2020-2026 aralığında yılda yalnız 12–19 satır var ve ardışık 2.717
    satır çiftinin 2.024'ü BİREBİR AYNI kümeyi taşıyor. Yani dosya bir "her gün" defteri değil,
    ADIM FONKSİYONU örneklemesidir.
    → BUNUN SONUCU (brief'ten SAPMA, ölçümle): "art arda GÜNLER tek aralık" okuması bu dosyada
      YANLIŞ olurdu — satır tarihleri arasındaki günler boş kalır, QC evreni günlerin çoğunda
      BOŞ dönerdi. Doğru okuma AS-OF'tur: bir satır, kendisinden SONRAKİ satıra kadar geçerlidir.
      Aralık = [satır tarihi, sonraki satır tarihi − 1 gün]; art arda SATIRLARDA görünen ticker
      için aralıklar birleşir. Son satırda hâlâ üye olan ticker'ın aralığı VERİ SONUNDA biter —
      ötesi taşınmaz (uydurma yasağı; `pit_uyeler` boş küme döner).

ÜRETİLEN DOSYA — saf Python, dış bağımlılıksız, deterministik:
    PIT_ARALIKLARI = {"AAPL": ((0, 11137),), ...}   # gün ofsetleri, PIT_EPOK'tan sayılı
    pit_uyeler(tarih) -> set[str]                   # as-of üyelik
    pit_veri_icinde(tarih) -> bool                  # veri penceresi kapısı
    pit_butunluk() -> dict                          # eksik parça bekçisi
    PIT_KAYNAK_SHA256 · PIT_URETIM_DAMGASI          # kaynak kimliği (SAAT TAŞIMAZ → bayt-aynı)

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    python research/qc_dogrulama/pit_araliklari_uret.py            # üret ve YAZ
    python research/qc_dogrulama/pit_araliklari_uret.py --kontrol  # yeniden üret, diskle kıyasla
    python research/qc_dogrulama/pit_araliklari_uret.py --tavan 32000
    python research/qc_dogrulama/pit_araliklari_uret.py --ozet     # yalnız sayıları bas
Çıkış kodu: 0 = tamam / bayt-aynı · 1 = ayrışma ya da tavan aşımı.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import date, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
KAYNAK_CSV = KOK / "research" / "pit_universe" / "sp500_uyelik_tarihi.csv"
HEDEF_DIZIN = KOK / "research" / "qc_dogrulama"
HEDEF_ONEK = "qc_defter_021_"
# QC dosya başına karakter sınırı — ÖLÇÜLDÜ (v3 turu). Tavan AŞILIRSA alfabetik bölünür.
QC_TAVAN = 32_000
PARCA_HARFLERI = "defghijklmnopqrstuvwxyz"


# ----------------------------------------------------------------------- okuma / sıkıştırma

def csv_oku(yol: Path = KAYNAK_CSV) -> list[tuple[date, set[str]]]:
    """(tarih, ticker kümesi) satırları — artan tarihte."""
    with yol.open(newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        baslik = next(r)
        if baslik[:2] != ["date", "tickers"]:
            raise SystemExit(f"beklenmedik başlık: {baslik!r}")
        satirlar = [(date.fromisoformat(a[0]), {t for t in a[1].split(",") if t}) for a in r]
    for i in range(len(satirlar) - 1):
        if satirlar[i][0] >= satirlar[i + 1][0]:
            raise SystemExit(f"tarihler artan değil: {satirlar[i][0]} → {satirlar[i + 1][0]}")
    return satirlar


def araliklara_sikistir(satirlar) -> dict[str, list[tuple[int, int]]]:
    """ticker → [(bas_ofset, bit_ofset)] · AS-OF adım fonksiyonu (bkz. modül şerhi).

    Bir ticker art arda SATIRLARDA görünüyorsa aralık birleşir. Aralığın BİTİŞİ, ticker'ın
    kaybolduğu ilk satırın tarihinden bir gün ÖNCEsidir (o güne kadar üye sayılır); ticker son
    satırda hâlâ üyeyse bitiş VERİ SONUdur (ötesi bilinmiyor, taşınmaz).
    """
    epok = satirlar[0][0]
    n = len(satirlar)

    def ofs(d: date) -> int:
        return (d - epok).days

    gorunum: dict[str, list[int]] = {}
    for i, (_d, tickerlar) in enumerate(satirlar):
        for t in tickerlar:
            gorunum.setdefault(t, []).append(i)

    araliklar: dict[str, list[tuple[int, int]]] = {}
    for t, idx in gorunum.items():
        kosular, bas, onceki = [], idx[0], idx[0]
        for i in idx[1:]:
            if i == onceki + 1:
                onceki = i
                continue
            kosular.append((bas, onceki))
            bas = onceki = i
        kosular.append((bas, onceki))
        araliklar[t] = [
            (ofs(satirlar[a][0]),
             ofs(satirlar[b + 1][0]) - 1 if b + 1 < n else ofs(satirlar[b][0]))
            for a, b in kosular
        ]
    return dict(sorted(araliklar.items()))


def uyeler_as_of(satirlar, gun: date) -> set[str]:
    """Bağımsız ikinci okuyucu (çivi ve öz-denetim için): gun'e kadarki SON satırın kümesi."""
    if gun < satirlar[0][0] or gun > satirlar[-1][0]:
        return set()
    sec = set()
    for d, ts in satirlar:
        if d > gun:
            break
        sec = ts
    return sec


# ------------------------------------------------------------------------------- yazım

def _literal_satirlari(araliklar) -> list[str]:
    out = []
    for t, ar in araliklar.items():
        govde = ",".join(f"({a},{b})" for a, b in ar)
        out.append(f'"{t}":({govde},),' if len(ar) == 1 else f'"{t}":({govde}),')
    return out


BASLIK_SABLONU = '''"""EDG-2026-021 · defter v4 PARÇA {harf} — PIT S&P 500 üyelik aralıkları (ÜRETİLMİŞ).

ELLE DÜZENLENMEZ. Üretici: research/qc_dogrulama/pit_araliklari_uret.py
Kaynak: {kaynak} (sha256 {sha_kisa}…, {n_satir} satır, {veri_bas} → {veri_son})

AS-OF OKUMA: kaynak dosya GÜNLÜK DEĞİL, adım fonksiyonudur (ölçüldü 2026-09-03: 2.717 ardışık
satır çiftinin 2.024'ü aynı kümeyi taşıyor; 2020-2026'da yılda 12-19 satır). Bir satır kendinden
SONRAKİ satıra kadar geçerlidir. Veri sonundan (\'{veri_son}\') SONRAKİ günler TAŞINMAZ —
`pit_uyeler` BOŞ küme döner (uydurma yasağı). Defterin penceresi bu tarihi aşıyorsa aşan günler
evren DIŞInda kalır ve defter bunu `evren.kapsama` altında SAYAR.

Aralıklar PIT_EPOK=\'{epok}\' gününden sayılan GÜN OFSETLERİdir (kapsayıcı iki uç).
"""

PIT_KAYNAK = "{kaynak}"
PIT_KAYNAK_SHA256 = "{sha}"
PIT_EPOK = "{epok}"
PIT_VERI_BAS = "{veri_bas}"
PIT_VERI_SON = "{veri_son}"
PIT_PARCALAR = {parcalar!r}
PIT_BEKLENEN_TICKER = {n_ticker}
PIT_URETIM_DAMGASI = {{
    "uretici": "research/qc_dogrulama/pit_araliklari_uret.py",
    "kaynak_sha256": "{sha}",
    "kaynak_satir": {n_satir},
    "ticker": {n_ticker},
    "aralik": {n_aralik},
    "parca": {n_parca},
    "beyan": "damga DUVAR SAATİ taşımaz: taşısaydı --kontrol her koşumda ayrışır, "
             "determinizm ÖLÇÜLEMEZ olurdu. Kimlik kaynak sha256 + sayımlardır.",
}}

'''

YARDIMCI = '''

def _pit_ymd(tarih):
    """date/datetime/pandas.Timestamp/'YYYY-MM-DD' → (yil, ay, gun). SAF PYTHON."""
    if isinstance(tarih, str):
        p = tarih[:10].split("-")
        return int(p[0]), int(p[1]), int(p[2])
    return int(tarih.year), int(tarih.month), int(tarih.day)


def _pit_sira(y, a, g):
    """Proleptik Gregoryen gün sırası (Hinnant days_from_civil), ithalsiz.
    `date.toordinal` ile AYNI DEĞİL: ondan SABİT 1 eksiktir. Burada yalnız FARK alındığı için
    (ofset = sira(t) - sira(epok)) sabit sadeleşir; toordinal ile kıyaslama YAPILMAZ."""
    y2 = y - (a <= 2)
    era = (y2 if y2 >= 0 else y2 - 399) // 400
    yoe = y2 - era * 400
    doy = (153 * (a + (-3 if a > 2 else 9)) + 2) // 5 + g - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468 + 719162


_PIT_EPOK_SIRA = _pit_sira(*_pit_ymd(PIT_EPOK))
_PIT_SON_OFS = _pit_sira(*_pit_ymd(PIT_VERI_SON)) - _PIT_EPOK_SIRA
_PIT_ONBELLEK = {}


def pit_gun_ofseti(tarih):
    """Tarih → PIT_EPOK'tan gün ofseti (negatif olabilir)."""
    return _pit_sira(*_pit_ymd(tarih)) - _PIT_EPOK_SIRA


def pit_veri_icinde(tarih):
    """Kaynak dosyanın KAPSADIĞI gün mü? Dışarısı 'üye yok' DEĞİL, 'BİLİNMİYOR'dur."""
    return 0 <= pit_gun_ofseti(tarih) <= _PIT_SON_OFS


def pit_uyeler(tarih):
    """O günün S&P 500 üyeliği (as-of). Veri penceresi dışında BOŞ küme (taşıma YOK)."""
    o = pit_gun_ofseti(tarih)
    if o < 0 or o > _PIT_SON_OFS:
        return set()
    hazir = _PIT_ONBELLEK.get(o)
    if hazir is None:
        hazir = {t for t, ar in PIT_ARALIKLARI.items()
                 if any(a <= o <= b for a, b in ar)}
        _PIT_ONBELLEK[o] = hazir
    return hazir


def pit_butunluk():
    """Tüm parçalar yüklendi mi? Eksik parça evreni SESSİZCE yarılar — bu bekçi bağırır."""
    n = len(PIT_ARALIKLARI)
    return {"tam": n == PIT_BEKLENEN_TICKER, "yuklu_ticker": n,
            "beklenen_ticker": PIT_BEKLENEN_TICKER, "parcalar": PIT_PARCALAR,
            "neden": None if n == PIT_BEKLENEN_TICKER else
                     "eksik parça: qc_defter_021_%s.py dosyalarının HEPSİ yüklenmeli"
                     % ",".join(PIT_PARCALAR)}


'''

# Bütünlük bekçisi SON PARÇANIN sonuna konur (ek parçalarda da aynı metin). d.py tek parçalıysa
# burası d.py'nin sonudur; çok parçalıysa d.py YÜKLENİRKEN tablo zaten eksiktir ve bekçi burada
# patlarsa e.py'nin update()'ine hiç sıra gelmezdi — o yüzden bekçi ARALIK LİTERALİNİN SONUNA
# değil, PARÇA ZİNCİRİNİN SONUNA aittir (ölçüldü: totoloji koşul ölü koddu, K-1).
BEKCI = '''

if not pit_butunluk()["tam"]:
    raise RuntimeError("PIT parçaları eksik — hepsini yükle: %r" % (pit_butunluk(),))
'''

EK_BASLIK = '''"""EDG-2026-021 · defter v4 PARÇA {harf} — PIT aralıkları (ÜRETİLMİŞ, EK PARÇA).

ELLE DÜZENLENMEZ. `qc_defter_021_d.py` YÜKLENDİKTEN SONRA aynı namespace'te koşar.
"""

if "PIT_ARALIKLARI" not in globals():
    raise RuntimeError("ÖNCE qc_defter_021_d.py koşmalı (aynı namespace)")

PIT_ARALIKLARI.update({{
'''


def parcalari_uret(araliklar, sha: str, satirlar, tavan: int = QC_TAVAN) -> dict[str, str]:
    """{dosya adı: içerik} — alfabetik, her parça `tavan` karakterin ALTINDA."""
    epok, veri_bas, veri_son = satirlar[0][0], satirlar[0][0], satirlar[-1][0]
    n_aralik = sum(len(v) for v in araliklar.values())
    govde = _literal_satirlari(araliklar)

    for n_parca in range(1, len(PARCA_HARFLERI) + 1):
        parcalar = tuple(PARCA_HARFLERI[:n_parca])
        ortak = dict(kaynak=KAYNAK_CSV.relative_to(KOK).as_posix(), sha=sha, sha_kisa=sha[:12],
                     epok=epok.isoformat(), veri_bas=veri_bas.isoformat(),
                     veri_son=veri_son.isoformat(), n_satir=len(satirlar),
                     n_ticker=len(araliklar), n_aralik=n_aralik, n_parca=n_parca,
                     parcalar=parcalar, son_harf=parcalar[-1])
        # gövdeyi n_parca dilime böl (alfabetik sıra korunur, ticker sınırında kesilir)
        adim = -(-len(govde) // n_parca)
        dilimler = [govde[i:i + adim] for i in range(0, len(govde), adim)]
        if len(dilimler) != n_parca:
            continue
        dosyalar, tasti = {}, False
        for i, (harf, dilim) in enumerate(zip(parcalar, dilimler)):
            if i == 0:
                metin = (BASLIK_SABLONU.format(harf=harf.upper(), **ortak)
                         + "PIT_ARALIKLARI = {\n" + _sar(dilim) + "}\n" + YARDIMCI)
            else:
                metin = EK_BASLIK.format(harf=harf.upper()) + _sar(dilim) + "})\n"
            if i == n_parca - 1:
                metin += BEKCI
            if len(metin) >= tavan:
                tasti = True
                break
            dosyalar[f"{HEDEF_ONEK}{harf}.py"] = metin
        if not tasti:
            return dosyalar
    raise SystemExit(f"aralık literali {len(PARCA_HARFLERI)} parçaya bile sığmadı")


def _sar(satirlar, genislik: int = 96) -> str:
    """Literal satırlarını ~96 sütuna sarar (ticker sınırında; sözdizimi etkilenmez)."""
    out, hat = [], ""
    for s in satirlar:
        if hat and len(hat) + len(s) > genislik:
            out.append(hat)
            hat = ""
        hat += s
    if hat:
        out.append(hat)
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------------------- öz-denetim

def oz_denetim(dosyalar: dict[str, str], satirlar) -> dict:
    """Üretilen literali BAĞIMSIZ okuyucuyla kıyasla — üretici kendi kendini doğrular."""
    alan: dict = {}
    for ad in sorted(dosyalar):
        exec(compile(dosyalar[ad], ad, "exec"), alan)
    # TÜKETİCİ tarama (örnekleme DEĞİL): her satır tarihi + her satırın BİR GÜN ÖNCESİ.
    # Örnekleme, tek ticker'ın tek günlük sınır kaymasını KAÇIRIR (ölçüldü). Maliyet ~1 sn.
    ayrik = [d.isoformat() for d, ts in satirlar if alan["pit_uyeler"](d) != ts]
    ara_ayrik, n_sinir = [], 0
    for i in range(1, len(satirlar)):
        onceki = satirlar[i][0] - timedelta(days=1)
        if onceki <= satirlar[i - 1][0]:
            continue
        n_sinir += 1
        if alan["pit_uyeler"](onceki) != satirlar[i - 1][1]:
            ara_ayrik.append(onceki.isoformat())
    return {"taranan_gun": len(satirlar) + n_sinir, "ayrik_gun": ayrik,
            "satir_arasi_ayrik": ara_ayrik, "butunluk": alan["pit_butunluk"]()}


# ------------------------------------------------------------------------------ komut satırı

def _uret(tavan: int):
    satirlar = csv_oku()
    sha = hashlib.sha256(KAYNAK_CSV.read_bytes()).hexdigest()
    araliklar = araliklara_sikistir(satirlar)
    dosyalar = parcalari_uret(araliklar, sha, satirlar, tavan=tavan)
    return satirlar, araliklar, dosyalar, sha


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PIT S&P 500 üyelik aralıkları → QC defter parçaları")
    ap.add_argument("--kontrol", action="store_true",
                    help="yeniden üret, DİSKLE bayt-bayt kıyasla, YAZMA")
    ap.add_argument("--ozet", action="store_true", help="yalnız sayıları bas, YAZMA")
    ap.add_argument("--tavan", type=int, default=QC_TAVAN, help=f"parça sınırı (öntanım {QC_TAVAN})")
    a = ap.parse_args(argv)

    satirlar, araliklar, dosyalar, sha = _uret(a.tavan)
    denetim = oz_denetim(dosyalar, satirlar)
    print(f"kaynak   : {KAYNAK_CSV.relative_to(KOK)} · satır={len(satirlar)} · sha={sha[:12]}…")
    print(f"aralık   : ticker={len(araliklar)} · aralık={sum(len(v) for v in araliklar.values())}")
    print(f"parça    : {len(dosyalar)} → " + ", ".join(
        f"{ad} ({len(m)} kr)" for ad, m in sorted(dosyalar.items())))
    print(f"öz-denetim: taranan_gün={denetim['taranan_gun']} ayrık={denetim['ayrik_gun']} "
          f"satır-arası ayrık={denetim['satir_arasi_ayrik']} bütünlük={denetim['butunluk']['tam']}")
    if denetim["ayrik_gun"] or denetim["satir_arasi_ayrik"] or not denetim["butunluk"]["tam"]:
        print("HATA: üretilen aralıklar CSV ile AYRIŞIYOR — yazılmadı")
        return 1

    if a.ozet:
        return 0

    if a.kontrol:
        ayrik = []
        for ad, metin in sorted(dosyalar.items()):
            p = HEDEF_DIZIN / ad
            if not p.exists():
                ayrik.append(f"{ad}: DİSKTE YOK")
            elif p.read_text(encoding="utf-8") != metin:
                ayrik.append(f"{ad}: içerik ayrık")
        fazla = [p.name for p in HEDEF_DIZIN.glob(f"{HEDEF_ONEK}[d-z].py")
                 if p.name not in dosyalar]
        ayrik += [f"{ad}: DİSKTE FAZLA (bayat parça)" for ad in fazla]
        if ayrik:
            print("AYRIK: " + " · ".join(ayrik))
            return 1
        print("BAYT-AYNI: disk üretimle birebir")
        return 0

    for ad, metin in sorted(dosyalar.items()):
        (HEDEF_DIZIN / ad).write_text(metin, encoding="utf-8")
        print(f"yazıldı  : research/qc_dogrulama/{ad}")
    for p in HEDEF_DIZIN.glob(f"{HEDEF_ONEK}[d-z].py"):
        if p.name not in dosyalar:
            print(f"UYARI    : bayat parça diskte duruyor → {p.name} (elle sil)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
