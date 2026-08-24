#!/usr/bin/env python3
"""TÜRKÇE GLİF HAYATTA MI — 08-07 `turkish_test.py`nin uyarlanmış kopyası.

ORİJİNAL: research/olcumler/yazi_tipi_2026-08-07/turkish_test.py (DONMUŞ, dokunulmadı).

NE DEĞİŞTİ (1-4)
[1] FACES LİSTESİ. Orijinal on aday yüz çiftini tarıyordu; burada ÖLÇÜLEN ŞEY bu turun İKİ
    KESİTİ. Karşılaştırma için 08-07'nin Recursive çifti REFERANS satırı olarak ekli
    (frozen dizinden SALT-OKUNUR; o dosyalar kesit DEĞİL, tam yüzdür — satır etiketinde yazıyor).
    Yollar artık FACES içinde TAM YOL olarak duruyor (iki ayrı dizinden okunuyor).
[2] SERT ÖLÇÜM EKLENDİ. Orijinal yalnız PNG üretiyordu; "hayatta mı" sorusu göze bırakılıyordu.
    Bu turun asıl sorusu subset'in glifi DÜŞÜRÜP DÜŞÜRMEDİĞİ, o yüzden `hayatta_mi()` eklendi:
    her Türkçe karakter için (a) cmap girdisi var mı, (b) eşlendiği glif BOŞ KONTUR mu
    (subset bazen glifi bırakıp konturu boşaltabilir), (c) advance sıfır mı. Üçü de JSON'a yazılır.
[3] ÇIKTI. PNG'ler `kanit/turkce/`, sert ölçüm `kanit/turkce_glif.json`.
[4] Geri kalan (DAY/NIGHT temaları, PROBE dizgisi, 6x nearest-neighbour büyütme, boyutlar
    10/11/12/13, ağırlıklar 400/700, `coords`/`load`/`sheet` gövdeleri) BİREBİR AYNI.
"""
import json
import pathlib
import sys

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

BURASI = pathlib.Path(__file__).resolve().parent
TTFD = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else BURASI / "kanit" / "ttf"
OD = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else BURASI / "kanit" / "turkce"
DONMUS = BURASI.parent / "yazi_tipi_2026-08-07" / "fonts"
OD.mkdir(parents=True, exist_ok=True)

DAY = {"bg": (255, 255, 255), "ink": (5, 5, 5), "mut": (143, 139, 134), "name": "gunduz"}
NIGHT = {"bg": (30, 30, 30), "ink": (212, 212, 212), "mut": (138, 133, 128), "name": "gece"}

# [1] (etiket, sans yolu, mono yolu)
FACES = [
    ("Inter/Geist KESIT", TTFD / "inter-vf.ttf", TTFD / "geist-mono-vf.ttf"),
    ("Recursive TAM(ref)", DONMUS / "RecursiveSansLinear-VF.ttf",
     DONMUS / "RecursiveMonoLinear-VF.ttf"),
    ("Geist TAM(ref)", DONMUS / "Geist-VF.ttf", DONMUS / "GeistMono-VF.ttf"),
]

# 12 Türkçe karakter — tests/test_yazitipi_v201.py::TURKCE ile BİREBİR aynı küme.
TURKCE = {0x0131: "ı", 0x0130: "İ", 0x015F: "ş", 0x015E: "Ş",
          0x011F: "ğ", 0x011E: "Ğ", 0x00E7: "ç", 0x00C7: "Ç",
          0x00F6: "ö", 0x00D6: "Ö", 0x00FC: "ü", 0x00DC: "Ü"}

# the marks that carry meaning in Turkish, next to the letters they must not become
PROBE = "ö o ü u ğ g ş s ç c ı i İ I"


def coords(path, wght):
    f = TTFont(str(path))
    if "fvar" not in f:
        return None
    return [max(a.minValue, min(a.maxValue, wght)) if a.axisTag == "wght" else a.defaultValue
            for a in f["fvar"].axes]


def load(path, size, wght):
    fnt = ImageFont.truetype(str(path), size)
    c = coords(path, wght)
    if c:
        try:
            fnt.set_variation_by_axes(c)
        except Exception:
            pass
    return fnt


# ---------------------------------------------------------------------------------------------
# [2] SERT ÖLÇÜM — "cmap'te var" YETMEZ. Boş kontur da bir kayıptır ve sessizdir.
# ---------------------------------------------------------------------------------------------
def hayatta_mi(path: pathlib.Path) -> dict:
    f = TTFont(str(path))
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    glyf = f["glyf"] if "glyf" in f else None
    hm = f["hmtx"]
    sonuc = {}
    for cp, ch in sorted(TURKCE.items()):
        anahtar = f"U+{cp:04X} {ch}"
        if cp not in cmap:
            sonuc[anahtar] = {"cmapte": False, "glif": None, "kontur_var": None,
                              "advance": None, "HAYATTA": False,
                              "neden": "cmap girdisi YOK — subset kod noktasını düşürmüş"}
            continue
        g = cmap[cp]
        adv = hm[g][0]
        kontur_var = None
        if glyf is not None and g in glyf.glyphOrder:
            gl = glyf[g]
            # bileşik glif (ö = o + dieresis) numberOfContours == -1 taşır; ikisi de "dolu".
            kontur_var = bool(gl.numberOfContours) or bool(getattr(gl, "components", None))
        sonuc[anahtar] = {"cmapte": True, "glif": g, "kontur_var": kontur_var,
                          "advance": adv,
                          "HAYATTA": bool(kontur_var) and adv > 0}
    return sonuc


def sheet(th, kind, wght, sizes=(10, 11, 12, 13), S=6):
    W = 560
    lines = []
    for name, sf, mf in FACES:
        p = mf if kind == "mono" else sf
        if p.is_file():
            lines.append((name, p))
    H = 16 + len(lines) * (sum(sizes) + len(sizes) * 4 + 10)
    img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    small = ImageFont.load_default()
    d.text((6, 4), f"TR aksan · {kind} · wght {wght} · {th['name']}", font=small, fill=th["mut"])
    y = 18
    for name, p in lines:
        d.text((6, y), name[:18], font=small, fill=th["mut"])
        yy = y
        for s in sizes:
            f = load(p, s, wght)
            d.text((96, yy), f"{s}", font=small, fill=th["mut"])
            d.text((150, yy), PROBE, font=f, fill=th["ink"])
            yy += s + 4
        y = yy + 8
    img = img.crop((0, 0, W, min(H, y)))
    return img.resize((W * S, img.height * S), Image.NEAREST)


def main() -> int:
    sert = {}
    for p in sorted(TTFD.glob("*.ttf")):
        sert[p.stem] = hayatta_mi(p)
    (BURASI / "kanit" / "turkce_glif.json").write_text(
        json.dumps(sert, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for ad, tablo in sert.items():
        olu = [k for k, v in tablo.items() if not v["HAYATTA"]]
        print(f"{ad:<16} 12 Türkçe glif → "
              f"{'HEPSİ HAYATTA' if not olu else 'ÖLÜ: ' + ', '.join(olu)}")

    for th in (DAY, NIGHT):
        for kind in ("sans", "mono"):
            for w in (400, 700):
                sheet(th, kind, w).save(OD / f"turkce_{kind}_w{w}_{th['name']}.png")
    print("PNG →", OD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
