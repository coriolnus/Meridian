#!/usr/bin/env python3
"""ÜÇLÜ BÜTÇE — Inter + Geist Mono kesitleri ÖLÇÜLÜR, Satoshi'nin TAM dosyası eklenir.

NİYE BU AJAN ÖLÇÜYOR. `tests/test_yazitipi_v201.py::test_dagitim_boyutu_BUTCEDE` bir TOPLAM'a
bakar (`< 120 KB`). Satoshi'nin tek başına boyutu o kapıya "sığar mı" sorusunu cevaplamaz;
soru üç yüzün toplamıdır. Inter/Geist EDİNİMİ paralel bir iş akışının işi ve onların kesit
sayısı henüz yok — bu yüzden burada BAĞIMSIZ bir üst-sınır ölçümü yapılır.

BU SAYILAR PARALEL İŞ AKIŞININ HÜKMÜ DEĞİLDİR. Parametreler 08-07 borusundan alındı
(aynı kod-noktası kümesi, aynı YALIN_OZELLIKLER, `wght 400-700`). Inter/Geist iş akışı
Dub'ın daha DAR ağırlık isteklerini (Inter 400/500/600, Geist Mono 400/500) kullanırsa
sayı DAHA KÜÇÜK çıkar — yani buradaki toplam bir TAVANDIR, bir kehanet değil.

Satoshi KESİLEMEZ (FFL §02) — onun payı ITF'nin kendi WOFF2'sinin TAM boyudur, sabit.

Çıktı woff2'leri depoya DEĞİL, geçici dizine yazılır: bu bir bütçe ölçümüdür, bir dağıtım
değil. Kayıt `kanit/butce.json`.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

BURASI = pathlib.Path(__file__).resolve().parent
DEPO = BURASI.parents[3]
EDINME = BURASI.parent / "edinme"

# 08-07 borusundan BİREBİR alındı (build_web_fonts.py).
YALIN_OZELLIKLER = "ccmp,locl,kern,mark,mkmk,rlig,calt,tnum,zero,case"
WGHT_ARALIK = (400, 700)

GUVENLIK_KUMESI = (
    list(range(0x0020, 0x0100))
    + [0x0131, 0x0130, 0x011E, 0x011F, 0x015E, 0x015F]
    + [0x0152, 0x0153, 0x0160, 0x0161, 0x0178, 0x017D, 0x017E]
    + [0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306,
       0x0307, 0x0308, 0x030A, 0x030B, 0x030C, 0x0327, 0x0328]
    + [0x0394, 0x03A3, 0x03C3, 0x03C4]
    + [0x2010, 0x2011, 0x2013, 0x2014, 0x2018, 0x2019,
       0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2021,
       0x2022, 0x2026, 0x2030, 0x2039, 0x203A, 0x2044]
    + [0x20AC, 0x20BA]
    + [0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x2197, 0x21D2]
    + [0x2212, 0x221A, 0x222A, 0x2248, 0x2260, 0x2264, 0x2265]
    + [0x2303, 0x2304, 0x2318, 0x21E7, 0x2325, 0x23CE]
    + [0x25A0, 0x25A1, 0x25AA, 0x25AB, 0x25B2, 0x25B3, 0x25B6,
       0x25B8, 0x25BC, 0x25BE, 0x25C6, 0x25C7, 0x25C8, 0x25CB,
       0x25CF, 0x25D0]
    + [0x2713, 0x2715, 0x2717, 0x27E8, 0x27E9]
)

KAYNAKLAR = [
    {"ad": "Inter",      "yol": EDINME / "inter" / "acilmis" / "InterVariable.ttf",
     "sabit": {"opsz": 14.0}},
    {"ad": "Geist Mono", "yol": EDINME / "geist" / "extract" / "GeistMono[wght].ttf",
     "sabit": {}},
]

SATOSHI_WOFF2 = (BURASI / "fonts" / "Satoshi_Complete" / "Fonts" / "WEB" / "fonts"
                 / "Satoshi-Variable.woff2")

BUTCE_BAYT = 120 * 1024   # tests/test_yazitipi_v201.py::test_dagitim_boyutu_BUTCEDE


def kapsam() -> set[int]:
    """Panonun gerçekten yazdığı karakterler — 08-07 borusundaki `olcum_kapsami()` ile aynı."""
    hedefler = sorted((DEPO / "meridian" / "web").glob("*.html"))
    hedefler += sorted((DEPO / "meridian" / "web").glob("*.js"))
    hedefler += [DEPO / "meridian" / "api.py"]
    cps: set[int] = set()
    for p in hedefler:
        if p.is_file():
            cps |= {ord(ch) for ch in p.read_text(encoding="utf-8", errors="replace")}
    return cps


def gvar_tam_doldur(font: TTFont) -> None:
    if "gvar" not in font:
        return
    mevcut = dict(font["gvar"].variations)
    font["gvar"].variations = {g: mevcut.get(g, []) for g in font.getGlyphOrder()}


def olc(kaynak: dict, istenen: set[int], gecici: pathlib.Path) -> dict:
    if not kaynak["yol"].is_file():
        return {"aile": kaynak["ad"], "bayt": None,
                "neden": f"ÖLÇÜLEMEDİ — kaynak dosya yok: {kaynak['yol']}"}
    font = TTFont(str(kaynak["yol"]))
    kaynak_cmap = set(font.getBestCmap())
    yer = dict(kaynak["sabit"]); yer["wght"] = WGHT_ARALIK
    font = instancer.instantiateVariableFont(font, yer, inplace=False, updateFontNames=False)
    gvar_tam_doldur(font)

    opts = subset.Options()
    opts.layout_features = YALIN_OZELLIKLER.split(",")
    opts.flavor = "woff2"
    opts.desubroutinize = False
    opts.hinting = True
    opts.legacy_kern = False
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    opts.name_legacy = True
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.drop_tables += ["DSIG"]
    s = subset.Subsetter(options=opts)
    s.populate(unicodes=sorted(istenen & kaynak_cmap))
    s.subset(font)

    p = gecici / f"{kaynak['ad'].lower().replace(' ', '-')}-vf.woff2"
    font.flavor = "woff2"
    font.save(str(p))
    return {"aile": kaynak["ad"], "kaynak": kaynak["yol"].name,
            "bayt": p.stat().st_size, "kb": round(p.stat().st_size / 1024, 1),
            "kesildi": True, "cmap": len(TTFont(str(p)).getBestCmap())}


def main() -> int:
    istenen = set(GUVENLIK_KUMESI) | {c for c in kapsam() if c >= 0x20}
    with tempfile.TemporaryDirectory() as td:
        gecici = pathlib.Path(td)
        satirlar = [olc(k, istenen, gecici) for k in KAYNAKLAR]

    if SATOSHI_WOFF2.is_file():
        satirlar.append({
            "aile": "Satoshi", "kaynak": SATOSHI_WOFF2.name,
            "bayt": SATOSHI_WOFF2.stat().st_size,
            "kb": round(SATOSHI_WOFF2.stat().st_size / 1024, 1),
            "kesildi": False,
            "not": "KESİLEMEZ — FFL §02. ITF'nin kendi WOFF2'si, TAM kod noktası kümesi.",
            "cmap": 431,
        })
    else:
        satirlar.append({"aile": "Satoshi", "bayt": None,
                         "neden": "ÖLÇÜLEMEDİ — paket açılmamış, WOFF2 diskte yok"})

    olculebilenler = [s for s in satirlar if s.get("bayt") is not None]
    toplam = sum(s["bayt"] for s in olculebilenler)
    rapor = {
        "parametreler": {"wght_aralik": list(WGHT_ARALIK),
                         "yalin_ozellikler": YALIN_OZELLIKLER.split(","),
                         "istenen_kod_noktasi": len(istenen)},
        "yuzler": satirlar,
        "olculemeyen": [s["aile"] for s in satirlar if s.get("bayt") is None],
        "toplam_bayt": toplam,
        "toplam_kb": round(toplam / 1024, 1),
        "butce_bayt": BUTCE_BAYT,
        "butce_kb": 120.0,
        "sigiyor_mu": toplam < BUTCE_BAYT,
        "fark_kb": round((BUTCE_BAYT - toplam) / 1024, 1),
        "mevcut_recursive_cifti_bayt": 81168,
    }
    (BURASI / "kanit" / "butce.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for s in satirlar:
        print(f"{s['aile']:<11} {s.get('kb', 'ÖLÇÜLEMEDİ')} KB  kesildi={s.get('kesildi')}")
    print(f"TOPLAM {rapor['toplam_kb']} KB / bütçe 120.0 KB → "
          f"{'SIĞIYOR' if rapor['sigiyor_mu'] else 'SIĞMIYOR'} (fark {rapor['fark_kb']} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
