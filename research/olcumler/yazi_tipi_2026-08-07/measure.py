#!/usr/bin/env python3
"""Binary-level font measurement for Meridian D4 typeface selection.

Same standard DESIGN.md set for Geist Mono: glyf contour dump, hmtx advances,
GSUB FeatureList, OS/2 x-height/cap-height, cmap presence proof.
No claim here is inferred; every number is read from the binary.
"""
import json
import pathlib
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

FONTS = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])

# Turkish set, as the bar names it.
TR = {
    "ı": "i noktasiz (dotless i)",
    "İ": "I noktali (dotted capital I)",
    "ş": "s cedilla kucuk",
    "Ş": "S cedilla buyuk",
    "ğ": "g breve kucuk",
    "Ğ": "G breve buyuk",
    "ç": "c cedilla kucuk",
    "Ç": "C cedilla buyuk",
    "ö": "o umlaut kucuk",
    "Ö": "O umlaut buyuk",
    "ü": "u umlaut kucuk",
    "Ü": "U umlaut buyuk",
}

PAIRS = {
    "zero": "0", "O": "O", "one": "1", "l": "l", "I": "I",
    "i": "i", "dotlessi": "ı", "Idotaccent": "İ",
}


def contours(glyphset, gname):
    """Per-contour (point count, bbox) via pen -> composites decomposed."""
    pen = DecomposingRecordingPen(glyphset)
    glyphset[gname].draw(pen)
    out, cur = [], None
    for op, args in pen.value:
        if op == "moveTo":
            if cur:
                out.append(cur)
            cur = [args[0]]
        elif op in ("lineTo",):
            cur.append(args[0])
        elif op == "qCurveTo":
            cur.extend(p for p in args if p is not None)
        elif op == "curveTo":
            cur.extend(args)
        elif op == "closePath":
            if cur:
                out.append(cur)
                cur = None
    if cur:
        out.append(cur)
    res = []
    for c in out:
        xs = [p[0] for p in c]
        ys = [p[1] for p in c]
        res.append({"pts": len(c), "bbox": [min(xs), min(ys), max(xs), max(ys)],
                    "w": max(xs) - min(xs), "h": max(ys) - min(ys)})
    return res


def measure(path):
    f = TTFont(str(path), lazy=False)
    upem = f["head"].unitsPerEm
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    rev = {}
    for cp, gn in cmap.items():
        rev.setdefault(gn, cp)

    r = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "family": f["name"].getDebugName(1),
        "subfamily": f["name"].getDebugName(2),
        "version": f["name"].getDebugName(5),
        "license_url": f["name"].getDebugName(14),
        "license_desc": (f["name"].getDebugName(13) or "")[:120],
        "upem": upem,
        "numGlyphs": f["maxp"].numGlyphs,
        "isFixedPitch_post": bool(f["post"].isFixedPitch),
    }

    # --- fvar axes (variable weight bar item 7) ---
    if "fvar" in f:
        r["axes"] = {a.axisTag: [a.minValue, a.defaultValue, a.maxValue]
                     for a in f["fvar"].axes}
        r["named_instances"] = len(f["fvar"].instances)
    else:
        r["axes"] = None
        r["named_instances"] = 0

    # --- OS/2 vertical metrics (bar item 6) ---
    os2 = f["OS/2"]
    sx = getattr(os2, "sxHeight", None)
    sc = getattr(os2, "sCapHeight", None)
    r["os2_version"] = os2.version
    r["sxHeight"] = sx
    r["sCapHeight"] = sc
    r["usWeightClass"] = os2.usWeightClass
    for label, v in (("x", sx), ("cap", sc)):
        if v:
            for px in (10, 11, 12, 13, 28):
                r[f"{label}_at_{px}px"] = round(v / upem * px, 3)
    r["ascender_hhea"] = f["hhea"].ascender
    r["descender_hhea"] = f["hhea"].descender
    r["lineGap_hhea"] = f["hhea"].lineGap

    # --- cmap: Turkish presence, PROVEN, plus non-empty outline ---
    tr = {}
    for ch, desc in TR.items():
        cp = ord(ch)
        gn = cmap.get(cp)
        if gn is None:
            tr[ch] = {"cp": f"U+{cp:04X}", "desc": desc, "in_cmap": False}
            continue
        cs = contours(gs, gn)
        tr[ch] = {"cp": f"U+{cp:04X}", "desc": desc, "in_cmap": True,
                  "glyph": gn, "contours": len(cs),
                  "pts": sum(c["pts"] for c in cs),
                  "adv": f["hmtx"][gn][0]}
    r["turkish"] = tr
    r["turkish_all_present"] = all(v["in_cmap"] and v.get("contours", 0) > 0
                                   for v in tr.values())

    # --- hmtx: digit advances (bar item 3, structural half) ---
    digits = {}
    for d in "0123456789":
        gn = cmap.get(ord(d))
        digits[d] = f["hmtx"][gn][0] if gn else None
    r["digit_advances"] = digits
    vals = [v for v in digits.values() if v is not None]
    r["digits_uniform_width"] = len(set(vals)) == 1 and len(vals) == 10
    r["digit_advance"] = vals[0] if r["digits_uniform_width"] else None

    # true-monospace check across a wider sample
    sample = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,-+%"
    advs = set()
    for ch in sample:
        gn = cmap.get(ord(ch))
        if gn:
            advs.add(f["hmtx"][gn][0])
    r["monospaced_all_latin"] = len(advs) == 1
    r["latin_advance_variants"] = len(advs)

    # --- GSUB FeatureList (bar item 3, feature half) ---
    tags = set()
    if "GSUB" in f and f["GSUB"].table.FeatureList:
        for fr in f["GSUB"].table.FeatureList.FeatureRecord:
            tags.add(fr.FeatureTag)
    r["gsub_features"] = sorted(tags)
    r["has_tnum"] = "tnum" in tags
    r["has_zero"] = "zero" in tags        # slashed-zero feature
    r["has_pnum"] = "pnum" in tags
    r["has_lnum"] = "lnum" in tags
    r["has_onum"] = "onum" in tags
    r["has_ss01"] = "ss01" in tags
    r["has_locl"] = "locl" in tags
    r["has_case"] = "case" in tags
    gpos = set()
    if "GPOS" in f and f["GPOS"].table.FeatureList:
        for fr in f["GPOS"].table.FeatureList.FeatureRecord:
            gpos.add(fr.FeatureTag)
    r["gpos_features"] = sorted(gpos)

    # --- glyf contour dump for the disambiguation pairs (bar item 4) ---
    g = {}
    for key, ch in PAIRS.items():
        gn = cmap.get(ord(ch))
        if gn is None:
            g[key] = None
            continue
        cs = contours(gs, gn)
        xs = [c["bbox"][0] for c in cs] or [0]
        ys = [c["bbox"][1] for c in cs] or [0]
        xe = [c["bbox"][2] for c in cs] or [0]
        ye = [c["bbox"][3] for c in cs] or [0]
        g[key] = {
            "glyph": gn, "adv": f["hmtx"][gn][0],
            "n_contours": len(cs), "n_pts": sum(c["pts"] for c in cs),
            "bbox": [min(xs), min(ys), max(xe), max(ye)],
            "w": max(xe) - min(xs), "h": max(ye) - min(ys),
            "contours": cs,
        }
    r["glyphs"] = g

    # --- zero vs O: is there a slash/dot inside? ---
    z, O = g.get("zero"), g.get("O")
    if z and O:
        extra = z["n_contours"] - O["n_contours"]
        r["zero_extra_contours"] = extra
        mark = None
        if extra > 0:
            # the extra contour = the smallest one strictly inside the bowl
            inner = sorted(z["contours"], key=lambda c: c["w"] * c["h"])
            cand = inner[0]
            ratio = cand["h"] / cand["w"] if cand["w"] else 999
            mark = {"pts": cand["pts"], "bbox": cand["bbox"],
                    "w": cand["w"], "h": cand["h"],
                    "aspect_h_over_w": round(ratio, 2)}
            # 4-point tall parallelogram => slash; small round blob => dot
            if cand["pts"] <= 6 and ratio > 1.4:
                mark["kind"] = "SLASH (diagonal, few points, tall)"
            elif ratio < 1.6 and cand["w"] < z["w"] * 0.35:
                mark["kind"] = "DOT/nokta (compact)"
            else:
                mark["kind"] = "UNKNOWN mark - inspect render"
        r["zero_mark"] = mark
        r["zero_vs_O_width"] = {"zero_w": z["w"], "O_w": O["w"],
                                "delta": z["w"] - O["w"],
                                "delta_px_at_10": round((z["w"] - O["w"]) / upem * 10, 3)}

    # --- dotless i / dotted I sanity (Turkish correctness, not just presence) ---
    di, ii = g.get("dotlessi"), g.get("i")
    if di and ii:
        r["dotlessi_correct"] = di["n_contours"] < ii["n_contours"]
        r["dotlessi_contours"] = di["n_contours"]
        r["i_contours"] = ii["n_contours"]
    Id, Ip = g.get("Idotaccent"), g.get("I")
    if Id and Ip:
        r["Idotaccent_correct"] = Id["n_contours"] > Ip["n_contours"]
        r["Idotaccent_contours"] = Id["n_contours"]
        r["I_contours"] = Ip["n_contours"]

    # --- 1 vs l vs I separation, measured (bar item 4) ---
    one, el, eye = g.get("one"), g.get("l"), g.get("I")
    if one and el:
        r["one_vs_l"] = {
            "contours": [one["n_contours"], el["n_contours"]],
            "pts": [one["n_pts"], el["n_pts"]],
            "w": [one["w"], el["w"]],
            "h": [one["h"], el["h"]],
            "w_delta": one["w"] - el["w"],
            "w_delta_px_at_10": round(abs(one["w"] - el["w"]) / upem * 10, 3),
        }
    if one and eye:
        r["one_vs_I"] = {
            "contours": [one["n_contours"], eye["n_contours"]],
            "pts": [one["n_pts"], eye["n_pts"]],
            "w": [one["w"], eye["w"]],
            "w_delta": one["w"] - eye["w"],
            "w_delta_px_at_10": round(abs(one["w"] - eye["w"]) / upem * 10, 3),
        }
    return r


def main():
    files = sorted(FONTS.glob("*.ttf"))
    out = {}
    for p in files:
        try:
            out[p.stem] = measure(p)
            print(f"measured {p.stem}")
        except Exception as e:
            out[p.stem] = {"file": p.name, "ERROR": repr(e)}
            print(f"ERROR {p.stem}: {e}")
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"-> {OUT}")


main()
