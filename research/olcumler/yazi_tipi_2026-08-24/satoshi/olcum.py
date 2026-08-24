#!/usr/bin/env python3
"""Satoshi'yi ÖLÇER — hiçbir şey ÜRETMEZ, hiçbir şey DEĞİŞTİRMEZ.

Bu betik yalnızca OKUR: name/fvar/cmap/GSUB tablolarını açar ve sayıları JSON'a döker.
Türetilmiş bir ikili YAZMAZ. FFL §02 "modify, edit, adapt ... subsetting, format conversion"
yasağı ÜRETİME bakar; kapsama ölçmek için tabloyu okumak bir Derivative Work doğurmaz
(FFL Definitions: Derivative Work = "modified, adapted, altered or otherwise derived
VERSION of the Font Software" — bu betik bir sürüm üretmiyor).

Koşum: <scratch>/fontenv/bin/python .../satoshi/olcum.py
"""
import json, pathlib
from fontTools.ttLib import TTFont

BURASI = pathlib.Path(__file__).resolve().parent
PAKET = BURASI / "fonts" / "Satoshi_Complete"

TURKCE = {0x0131: "ı", 0x0130: "İ", 0x015F: "ş", 0x015E: "Ş",
          0x011F: "ğ", 0x011E: "Ğ", 0x00E7: "ç", 0x00C7: "Ç",
          0x00F6: "ö", 0x00D6: "Ö", 0x00FC: "ü", 0x00DC: "Ü"}

# Kesit borusunun (build_web_fonts.py) İSTEDİĞİ kod noktası kümesi — Satoshi'de kesit
# ALINAMIYOR ama "tam dosya bu kümeyi karşılıyor mu" sorusu hâlâ ölçülebilir.
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


def ozellikler(f):
    t = set()
    for tag in ("GSUB", "GPOS"):
        if tag in f:
            for fr in f[tag].table.FeatureList.FeatureRecord:
                t.add(fr.FeatureTag)
    return sorted(t)


def olc(p: pathlib.Path) -> dict:
    f = TTFont(str(p))
    cmap = f.getBestCmap()
    d = {
        "dosya": p.name,
        "bayt": p.stat().st_size,
        "kb": round(p.stat().st_size / 1024, 1),
        "nameID0_telif": f["name"].getDebugName(0),
        "nameID1_aile": f["name"].getDebugName(1),
        "nameID5_surum": f["name"].getDebugName(5),
        "nameID6_ps": f["name"].getDebugName(6),
        "nameID13_lisans": f["name"].getDebugName(13),
        "nameID14_lisans_url": f["name"].getDebugName(14),
        "nameID16_tipografik_aile": f["name"].getDebugName(16),
        "unitsPerEm": f["head"].unitsPerEm,
        "usWeightClass": f["OS/2"].usWeightClass,
        "fsType_gomme_izni": f["OS/2"].fsType,
        "glif": f["maxp"].numGlyphs,
        "cmap_boyu": len(cmap),
        "fvar": ({a.axisTag: [a.minValue, a.defaultValue, a.maxValue]
                  for a in f["fvar"].axes} if "fvar" in f else None),
        "adlandirilmis_kesitler": ([
            (f["name"].getDebugName(i.subfamilyNameID), i.coordinates)
            for i in f["fvar"].instances] if "fvar" in f else None),
        "ozellikler": ozellikler(f),
        "tnum_var": "tnum" in ozellikler(f),
    }
    # TÜRKÇE — tek tek, "muhtemelen var" yok
    d["turkce"] = {f"U+{cp:04X} {ch}": (cp in cmap) for cp, ch in TURKCE.items()}
    d["turkce_eksik"] = [f"U+{cp:04X} {ch}" for cp, ch in TURKCE.items() if cp not in cmap]
    # locl (Türkçe i-noktası dönüşümü) var mı
    d["locl_var"] = "locl" in d["ozellikler"]
    # Kesit borusunun istediği küme
    istenen = set(GUVENLIK_KUMESI)
    d["boru_kumesi_istenen"] = len(istenen)
    d["boru_kumesi_fontta_yok"] = [f"U+{c:04X}" for c in sorted(istenen - set(cmap))]
    # Rakam advance'ları — tabular yapısal mı?
    if all((0x30 + i) in cmap for i in range(10)):
        d["rakam_advance"] = sorted({f["hmtx"][cmap[0x30 + i]][0] for i in range(10)})
    else:
        d["rakam_advance"] = None
    return d


def main():
    hedefler = [
        PAKET / "Fonts" / "TTF" / "Satoshi-Variable.ttf",
        PAKET / "Fonts" / "WEB" / "fonts" / "Satoshi-Variable.woff2",
    ]
    cikti = {"olculen": []}
    for p in hedefler:
        if not p.is_file():
            cikti["olculen"].append({"dosya": str(p), "hata": "DOSYA YOK — ölçülemedi"})
            continue
        cikti["olculen"].append(olc(p))
    yol = BURASI / "kanit" / "satoshi_olcum.json"
    yol.write_text(json.dumps(cikti, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(cikti, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
