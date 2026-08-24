#!/usr/bin/env python3
"""KANITLAYICI HAZIRLIĞI — kesit woff2'lerini TTF kabına geri açar.

NİYE GEREK VAR. 08-07 turunun üç kanıtlayıcısı (`turkish_test.py`, `tnum_proof.py`,
`weights_and_stems.py`) argv[1] olarak bir DİZİN alır ve içindeki `*.ttf`leri gezer.
İkisi PIL/FreeType ile RASTERİZE eder; FreeType woff2 okumaz. Kanıtlayıcıları
woff2 okuyacak şekilde yeniden yazmak yerine (o zaman "kanıtlayıcı da değişti"
sorusu doğardı), KABI değiştiriyoruz: `TTFont(woff2).flavor = None` ile aynı
tablolar sıkıştırmasız TTF olarak yazılır.

BU BİR YENİDEN KESİT DEĞİLDİR. Kaynak, `kesit_uret.py`nin ürettiği woff2'nin TA KENDİSİDİR;
glif kümesi, cmap, GSUB/GPOS, fvar aynen taşınır — yalnız woff2 sıkıştırması açılır.
Doğrulama için her iki kabın da sha256'sı ve glif/cmap sayımı kayda geçer: sayımlar
eşleşmezse kap dönüşümü bir şey düşürmüş demektir ve bu GÖRÜNÜR olur.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

from fontTools.ttLib import TTFont

BURASI = pathlib.Path(__file__).resolve().parent
WOFF2 = BURASI / "woff2"
TTF = BURASI / "kanit" / "ttf"


def main() -> int:
    TTF.mkdir(parents=True, exist_ok=True)
    kayit = []
    for p in sorted(WOFF2.glob("*.woff2")):
        f = TTFont(str(p))
        once = {"glif": f["maxp"].numGlyphs, "cmap": len(f.getBestCmap())}
        f.flavor = None
        hedef = TTF / (p.stem + ".ttf")
        f.save(str(hedef))
        g = TTFont(str(hedef))
        sonra = {"glif": g["maxp"].numGlyphs, "cmap": len(g.getBestCmap())}
        kayit.append({
            "woff2": p.name,
            "woff2_bayt": p.stat().st_size,
            "woff2_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "ttf": hedef.name,
            "ttf_bayt": hedef.stat().st_size,
            "ttf_sha256": hashlib.sha256(hedef.read_bytes()).hexdigest(),
            "woff2_sayim": once,
            "ttf_sayim": sonra,
            "KAP_DONUSUMU_KAYIPSIZ": once == sonra,
        })
        print(f"{p.name} → {hedef.name}  glif {once['glif']}→{sonra['glif']}  "
              f"cmap {once['cmap']}→{sonra['cmap']}  kayipsiz={once == sonra}")
    (BURASI / "kanit" / "kap_donusumu.json").write_text(
        json.dumps(kayit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
