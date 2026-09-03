"""v397 — TSK-117 K-2: literal Tailwind renk sınıfları anlam jetonlarına göçer; sayım aile başına
YALNIZ DÜŞER (bedel yasası: her dilim önce/sonra). Tavanlar ölçüm günü (2026-09-03) değerleridir,
göç dilimi ailesini 0'a çeker. (TSK-117, 2026-09-03)"""
import pathlib, re
from meridian import config

UI = pathlib.Path(config.ROOT) / "ui" / "src"
DESEN = re.compile(r"\b(?:bg|text|border|ring|from|to|fill|stroke)-(amber|emerald|green|red|sky)-[0-9]{2,3}\b")
# Görev 3 sonrası: amber 0. Görev 4: emerald+green 0. Görev 5: red 0. Görev 6: sky 0.
LITERAL_TAVAN = {"amber": 0, "emerald": 130, "green": 5, "red": 31, "sky": 12}
ESLEME = {"amber": "uyari", "emerald": "basari", "green": "basari", "red": "kritik", "sky": "bilgi"}

def _sayim():
    s = {k: 0 for k in LITERAL_TAVAN}
    for p in UI.rglob("*.tsx"):
        for m in DESEN.finditer(p.read_text(encoding="utf-8")):
            s[m.group(1)] += 1
    return s

def test_literal_sinif_sayimi_tavani_asmaz():
    s = _sayim()
    asan = {k: (v, LITERAL_TAVAN[k]) for k, v in s.items() if v > LITERAL_TAVAN[k]}
    assert not asan, f"literal renk sınıfı geri geldi (aile: (bulunan, tavan)): {asan} — jeton: {ESLEME}"

def test_gocen_aileler_anlam_utility_kullaniyor():
    # 0'a çekilmiş her aile için en az bir dosya karşılık gelen utility'yi kullanmalı (göç silme değil dönüştürme)
    metin = "\n".join(p.read_text(encoding="utf-8") for p in UI.rglob("*.tsx"))
    for aile, tavan in LITERAL_TAVAN.items():
        if tavan == 0:
            assert re.search(rf"\b(?:bg|text|border|ring)-{ESLEME[aile]}(?:-t|-h)?\b", metin), \
                f"{aile} 0'a indi ama {ESLEME[aile]} utility'si hiç kullanılmıyor — sınıflar silinmiş, dönüştürülmemiş"
