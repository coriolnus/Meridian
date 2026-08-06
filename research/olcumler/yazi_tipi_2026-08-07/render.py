#!/usr/bin/env python3
"""Two-ground specimens at Meridian's real token values and real ramp sizes.

Day   : ground #ffffff, ink #050505, muted #8f8b86      (PRODUCT.md brand block)
Night : ground #1E1E1E, ink #D4D4D4, muted #8a8580      (no pure black, no pure white)
Sizes : 10 / 11 / 12 / 13 / 28  (the ramp steps the bar names)

Every specimen is drawn at the TRUE pixel size and then also shown at 4x
nearest-neighbour, because a 10px sample no human can see proves nothing.
"""
import pathlib
import sys

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FD = pathlib.Path(sys.argv[1])
OD = pathlib.Path(sys.argv[2])
OD.mkdir(parents=True, exist_ok=True)

DAY = {"bg": (255, 255, 255), "ink": (5, 5, 5), "mut": (143, 139, 134), "name": "gunduz"}
NIGHT = {"bg": (30, 30, 30), "ink": (212, 212, 212), "mut": (138, 133, 128), "name": "gece"}

PAIRS = [
    ("Recursive", "RecursiveSansLinear-VF.ttf", "RecursiveMonoLinear-VF.ttf"),
    ("AtkinsonHyperlegibleNext", "AtkinsonHyperlegibleNext-VF.ttf", "AtkinsonHyperlegibleMono-VF.ttf"),
    ("SourceSans3", "SourceSans3-VF.ttf", "SourceCodePro-VF.ttf"),
    ("RedHat", "RedHatText-VF.ttf", "RedHatMono-VF.ttf"),
    ("SplineSans", "SplineSans-VF.ttf", "SplineSansMono-VF.ttf"),
    ("NotoSans", "NotoSans-VF.ttf", "NotoSansMono-VF.ttf"),
    ("Chivo", "Chivo-VF.ttf", "ChivoMono-VF.ttf"),
    ("Reddit", "RedditSans-VF.ttf", "RedditMono-VF.ttf"),
    ("Overpass", "Overpass-VF.ttf", "OverpassMono-VF.ttf"),
    ("ZZ-Geist-incumbent", "Geist-VF.ttf", "GeistMono-VF.ttf"),
]

FIGS = ["108.001,10", "1.284,05", "-12,40", "0,00", "9.999,99", "0,10"]
DISAMB = "0O1lI  Il1O0  0O 1l"
TRTEXT = "İIıi ŞşĞğÇçÖöÜü"
TRSENT = "Açık risk · İşlem günü · ÖLÇÜLEMEDİ · sığ örneklem"
LABEL = "AÇIK RİSK"
BODY = ("Gecelik döngü 04:12'de bitti; iki aday kapıdan geçti, biri "
        "likidite kapısında düştü. Ölçülemedi ≠ 0.")


def axis_coords(path, wght):
    """Build the fvar coordinate list in the font's own axis order."""
    f = TTFont(str(path))
    if "fvar" not in f:
        return None
    out = []
    for a in f["fvar"].axes:
        if a.axisTag == "wght":
            out.append(max(a.minValue, min(a.maxValue, wght)))
        else:
            out.append(a.defaultValue)
    return out


def load(path, size, wght):
    fnt = ImageFont.truetype(str(path), size)
    co = axis_coords(path, wght)
    if co:
        try:
            fnt.set_variation_by_axes(co)
        except Exception:
            pass
    return fnt


def tracked(d, xy, text, font, fill, track=0.0):
    """Draw with letter-spacing (PIL has none); track is in px per char."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track
    return x


def specimen(name, sans, mono, th, scale=1):
    W, H = 760, 470
    img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    y = 14
    x0 = 16

    hdr = load(sans, 17, 500)
    d.text((x0, y), f"{name}  —  {th['name']}  (1:1)", font=hdr, fill=th["ink"])
    y += 28

    # --- label idiom: mono 10px UPPERCASE, 0.16em tracking ---
    lab = load(mono, 10, 700)
    tracked(d, (x0, y), LABEL, lab, th["mut"], track=10 * 0.16)
    y += 16

    # --- 28px figure, mono 400 ---
    big = load(mono, 28, 400)
    d.text((x0, y), "108.001,10", font=big, fill=th["ink"])
    d.text((x0 + 210, y), "0O1lI", font=big, fill=th["ink"])
    y += 38

    # --- right-aligned numeric column at 12px mono: the alignment proof ---
    m12 = load(mono, 12, 400)
    colr = x0 + 150
    d.text((x0, y), "sayı sütunu 12px:", font=load(sans, 12, 400), fill=th["mut"])
    yy = y + 16
    for s in FIGS:
        w = d.textlength(s, font=m12)
        d.text((colr - w, yy), s, font=m12, fill=th["ink"])
        yy += 15
    # ruler proving the right edge
    d.line([(colr + 3, y + 16), (colr + 3, yy - 3)], fill=th["mut"], width=1)

    # --- ramp: mono disambiguation at each size ---
    xr = x0 + 210
    yy2 = y + 16
    for px in (10, 11, 12, 13):
        f = load(mono, px, 400)
        d.text((xr, yy2), f"{px}px", font=load(sans, 10, 400), fill=th["mut"])
        d.text((xr + 34, yy2), DISAMB, font=f, fill=th["ink"])
        yy2 += 15
    # 700 weight row (label weight) at 10px
    d.text((xr, yy2), "10/700", font=load(sans, 10, 400), fill=th["mut"])
    d.text((xr + 34, yy2), DISAMB, font=load(mono, 10, 700), fill=th["ink"])

    y = max(yy, yy2) + 18

    # --- Turkish, sans + mono, at the small ramp steps ---
    d.text((x0, y), "Türkçe (sans / mono):", font=load(sans, 12, 400), fill=th["mut"])
    y += 17
    for px in (10, 11, 12, 13):
        d.text((x0, y), f"{px}", font=load(sans, 10, 400), fill=th["mut"])
        d.text((x0 + 20, y), TRTEXT, font=load(sans, px, 400), fill=th["ink"])
        d.text((x0 + 190, y), TRTEXT, font=load(mono, px, 400), fill=th["ink"])
        y += 15
    d.text((x0 + 20, y), TRSENT, font=load(sans, 13, 400), fill=th["ink"])
    y += 22

    # --- body prose 14px + heading 20px/500 ---
    d.text((x0, y), BODY[:70], font=load(sans, 14, 400), fill=th["ink"])
    y += 20
    d.text((x0, y), BODY[70:], font=load(sans, 14, 400), fill=th["ink"])
    y += 24
    d.text((x0, y), "Bugün · Karar · Sağlık", font=load(sans, 20, 500), fill=th["ink"])

    if scale > 1:
        img = img.resize((W * scale, H * scale), Image.NEAREST)
    return img


def zoom_strip(name, mono, sans, th):
    """4x nearest-neighbour zoom of the two things that decide this: the
    disambiguation set and a numeric column, at 10 and 11px."""
    W, H, S = 430, 120, 4
    img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    y = 6
    for px in (10, 11):
        for wt in (400, 700):
            d.text((6, y), f"{px}/{wt}", font=load(sans, 9, 400), fill=th["mut"])
            d.text((44, y), "0O 1lI Il1 O0  0,00 1.284,05",
                   font=load(mono, px, wt), fill=th["ink"])
            y += px + 5
    y += 4
    d.text((6, y), "sans", font=load(sans, 9, 400), fill=th["mut"])
    d.text((44, y), "İIıi ŞşĞğÇçÖöÜü 0O1lI", font=load(sans, 11, 400), fill=th["ink"])
    y += 16
    d.text((6, y), "mono", font=load(sans, 9, 400), fill=th["mut"])
    d.text((44, y), "İIıi ŞşĞğÇçÖöÜü 0O1lI", font=load(mono, 11, 400), fill=th["ink"])
    return img.crop((0, 0, W, y + 18)).resize((W * S, (y + 18) * S), Image.NEAREST)


def comparison(th, size, weight, kind):
    """All candidates, same string, same size - the only fair way to compare."""
    rows = []
    for name, s, m in PAIRS:
        rows.append((name, FD / (m if kind == "mono" else s)))
    # columns must be laid out from the widest actual advance, not guessed,
    # or the 28px sheet overlaps itself and proves nothing
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cols = ["0O1lI Il1O0", "İIıi ŞşĞğÇçÖö", "108.001,10", "-12,40  0,00"]
    widths = []
    for c in cols:
        widths.append(max(probe.textlength(c, font=load(p, size, weight))
                          for _, p in rows))
    x0 = 180
    xs, acc = [], x0
    for w in widths:
        xs.append(acc)
        acc += w + max(14, size)
    W = int(acc + 20)
    rowh = max(22, int(size * 1.55))
    img = Image.new("RGB", (W, rowh * len(rows) + 40), th["bg"])
    d = ImageDraw.Draw(img)
    lbl = ImageFont.load_default()
    d.text((12, 10), f"{kind} · {size}px · wght {weight} · {th['name']}",
           font=lbl, fill=th["mut"])
    y = 32
    for name, path in rows:
        f = load(path, size, weight)
        d.text((12, y + (rowh - size) // 2), name[:26], font=lbl, fill=th["mut"])
        for x, c in zip(xs, cols):
            d.text((x, y), c, font=f, fill=th["ink"])
        y += rowh
    scale = 2 if size <= 13 else 1
    return img.resize((W * scale, img.height * scale), Image.NEAREST)


def main():
    for name, sf, mf in PAIRS:
        s, m = FD / sf, FD / mf
        for th in (DAY, NIGHT):
            specimen(name, s, m, th).save(OD / f"{name}_{th['name']}.png")
            zoom_strip(name, m, s, th).save(OD / f"{name}_{th['name']}_zoom4x.png")
        print("rendered", name)
    for th in (DAY, NIGHT):
        for kind in ("mono", "sans"):
            for size, wt in ((10, 400), (11, 400), (10, 700)):
                comparison(th, size, wt, kind).save(
                    OD / f"karsilastirma_{kind}_{size}px_w{wt}_{th['name']}.png")
        comparison(th, 28, 400, "mono").save(OD / f"karsilastirma_mono_28px_w400_{th['name']}.png")
    print("-> ", OD)


main()
