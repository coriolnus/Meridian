#!/usr/bin/env python3
"""The Turkish diacritics at the sizes the interface actually uses.

cmap presence proves the glyph EXISTS. It does not prove it SURVIVES at 10px.
At 10-11px an umlaut is ~1px per dot and antialiasing can fuse the two dots into
a macron - at which point ö and ō are the same mark to the eye. Rendered at 6x
nearest-neighbour so the fusion is visible instead of asserted.
"""
import pathlib
import sys

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FD = pathlib.Path(sys.argv[1])
OD = pathlib.Path(sys.argv[2])

DAY = {"bg": (255, 255, 255), "ink": (5, 5, 5), "mut": (143, 139, 134), "name": "gunduz"}
NIGHT = {"bg": (30, 30, 30), "ink": (212, 212, 212), "mut": (138, 133, 128), "name": "gece"}

FACES = [
    ("Recursive", "RecursiveSansLinear-VF.ttf", "RecursiveMonoLinear-VF.ttf"),
    ("Atkinson", "AtkinsonHyperlegibleNext-VF.ttf", "AtkinsonHyperlegibleMono-VF.ttf"),
    ("Source", "SourceSans3-VF.ttf", "SourceCodePro-VF.ttf"),
    ("RedHat", "RedHatText-VF.ttf", "RedHatMono-VF.ttf"),
    ("Spline", "SplineSans-VF.ttf", "SplineSansMono-VF.ttf"),
    ("Noto", "NotoSans-VF.ttf", "NotoSansMono-VF.ttf"),
    ("Chivo", "Chivo-VF.ttf", "ChivoMono-VF.ttf"),
    ("Reddit", "RedditSans-VF.ttf", "RedditMono-VF.ttf"),
    ("Overpass", "Overpass-VF.ttf", "OverpassMono-VF.ttf"),
    ("Geist(mevcut)", "Geist-VF.ttf", "GeistMono-VF.ttf"),
]

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


def sheet(th, kind, wght, sizes=(10, 11, 12, 13), S=6):
    W = 560
    rowh = 0
    lines = []
    for name, sf, mf in FACES:
        p = FD / (mf if kind == "mono" else sf)
        lines.append((name, p))
    H = 16 + len(lines) * (sum(sizes) + len(sizes) * 4 + 10)
    img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    small = ImageFont.load_default()
    d.text((6, 4), f"TR aksan · {kind} · wght {wght} · {th['name']}", font=small, fill=th["mut"])
    y = 18
    for name, p in lines:
        d.text((6, y), name[:14], font=small, fill=th["mut"])
        yy = y
        for s in sizes:
            f = load(p, s, wght)
            d.text((96, yy), f"{s}", font=small, fill=th["mut"])
            d.text((118, yy), PROBE, font=f, fill=th["ink"])
            yy += s + 4
        y = yy + 8
    img = img.crop((0, 0, W, min(H, y)))
    return img.resize((W * S, img.height * S), Image.NEAREST)


for th in (DAY, NIGHT):
    for kind in ("sans", "mono"):
        for w in (400, 700):
            sheet(th, kind, w).save(OD / f"turkce_{kind}_w{w}_{th['name']}.png")
print("ok")
