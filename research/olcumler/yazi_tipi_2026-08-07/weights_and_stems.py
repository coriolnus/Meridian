#!/usr/bin/env python3
"""Two things the default-instance dump cannot answer:

1. Do digit advances stay uniform across the weights the interface actually uses?
   (hmtx varies through HVAR; a font can be tabular at 400 and not at 700.)
2. Stroke weight and stroke contrast -> the halation argument for the night ground.
   Measured by rasterising at high ppem and counting ink runs, not by eyeballing.
"""
import json
import pathlib
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont

D = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
WEIGHTS = (400, 500, 700)
PPEM = 400  # raster size for stem measurement


def runs(vals, thresh=128):
    """[(start,len)] of ink runs in a 1-D sample line."""
    out, s = [], None
    for i, v in enumerate(vals):
        ink = v < thresh          # black ink on white
        if ink and s is None:
            s = i
        elif not ink and s is not None:
            out.append((s, i - s))
            s = None
    if s is not None:
        out.append((s, len(vals) - s))
    return out


def raster_metrics(path, wght):
    """Stem width of 'l' and stroke contrast of 'o', in units/em."""
    try:
        f = ImageFont.truetype(str(path), PPEM)
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    except Exception as e:
        return {"ERROR": repr(e)}
    res = {}
    for ch, key in (("l", "stem_l"), ("H", "stem_H"), ("o", "o")):
        img = Image.new("L", (PPEM * 2, PPEM * 2), 255)
        d = ImageDraw.Draw(img)
        d.text((PPEM // 2, PPEM // 2), ch, font=f, fill=0)
        px = img.load()
        bbox = img.getbbox() if img.getbbox() else None
        inv = Image.eval(img, lambda v: 255 - v)
        bb = inv.getbbox()
        if not bb:
            continue
        x0, y0, x1, y1 = bb
        midy = (y0 + y1) // 2
        row = [px[x, midy] for x in range(x0, x1)]
        rr = runs(row)
        if ch in ("l", "H"):
            if rr:
                res[key] = round(min(r[1] for r in rr) / PPEM * 1000)
        else:
            # 'o': mid row gives the two vertical stems; mid column gives top/bottom bars
            if len(rr) >= 2:
                res["o_stem_vert"] = round(
                    sum(sorted(r[1] for r in rr)[:2]) / 2 / PPEM * 1000)
            midx = (x0 + x1) // 2
            col = [px[midx, y] for y in range(y0, y1)]
            cr = runs(col)
            if len(cr) >= 2:
                res["o_bar_horiz"] = round(
                    sum(sorted(r[1] for r in cr)[:2]) / 2 / PPEM * 1000)
    if res.get("o_bar_horiz"):
        res["stroke_contrast"] = round(res["o_stem_vert"] / res["o_bar_horiz"], 2)
    return res


def digit_advances_at(path, wght):
    f = TTFont(str(path))
    if "fvar" not in f:
        return None
    tags = {a.axisTag for a in f["fvar"].axes}
    if "wght" not in tags:
        return None
    ax = next(a for a in f["fvar"].axes if a.axisTag == "wght")
    w = max(ax.minValue, min(ax.maxValue, wght))
    inst = instancer.instantiateVariableFont(f, {"wght": w}, inplace=False)
    cmap = inst.getBestCmap()
    advs = {d: inst["hmtx"][cmap[ord(d)]][0] for d in "0123456789" if ord(d) in cmap}
    return {"requested": wght, "applied": w, "advances": advs,
            "uniform": len(set(advs.values())) == 1, "value": sorted(set(advs.values()))}


def main():
    out = {}
    for p in sorted(D.glob("*.ttf")):
        if p.stem == "Recursive-VF":
            continue  # measured through its two pinned instances instead
        e = out.setdefault(p.stem, {})
        for w in WEIGHTS:
            e[f"w{w}"] = {"tabular": digit_advances_at(p, w),
                          "raster": raster_metrics(p, w)}
        print(p.stem, {w: e[f"w{w}"]["tabular"]["uniform"] if e[f"w{w}"]["tabular"] else None
                       for w in WEIGHTS},
              "stem_l@400=", e["w400"]["raster"].get("stem_l"),
              "contrast=", e["w400"]["raster"].get("stroke_contrast"))
    OUT.write_text(json.dumps(out, indent=1))
    print("->", OUT)


main()
