#!/usr/bin/env python3
"""Prove (or disprove) that `tnum` actually delivers uniform advances.

Declaring `font-variant-numeric: tabular-nums` is not evidence. DESIGN.md already
caught one inert declaration (cv11/ss01 on Geist). So: walk the GSUB `tnum`
feature, resolve its single-substitution lookups on the ten digits, and read the
SUBSTITUTED glyphs' hmtx advances. Uniform or not - measured, not assumed.
"""
import json
import pathlib
import sys

from fontTools.ttLib import TTFont

D = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
DIGITS = "0123456789"


def resolve(font, tag):
    g = font.get("GSUB")
    if not g or not g.table.FeatureList:
        return None
    fl, ll = g.table.FeatureList, g.table.LookupList
    idxs = []
    for fr in fl.FeatureRecord:
        if fr.FeatureTag == tag:
            idxs.extend(fr.Feature.LookupListIndex)
    if not idxs:
        return None
    mapping = {}
    for li in idxs:
        lk = ll.Lookup[li]
        for st in lk.SubTable:
            t = type(st).__name__
            if t == "SingleSubst":
                mapping.update(st.mapping)
            elif t == "ExtensionSubst" and hasattr(st, "ExtSubTable"):
                ext = st.ExtSubTable
                if type(ext).__name__ == "SingleSubst":
                    mapping.update(ext.mapping)
    return mapping


def main():
    out = {}
    for p in sorted(D.glob("*.ttf")):
        f = TTFont(str(p))
        cmap = f.getBestCmap()
        hm = f["hmtx"]
        base = {d: cmap[ord(d)] for d in DIGITS if ord(d) in cmap}
        base_adv = {d: hm[g][0] for d, g in base.items()}
        e = {
            "default_advances": base_adv,
            "default_uniform": len(set(base_adv.values())) == 1,
        }
        for tag in ("tnum", "zero", "lnum", "ss01", "ss02", "cv01"):
            m = resolve(f, tag)
            if not m:
                e[tag] = None
                continue
            sub = {d: m.get(g, g) for d, g in base.items()}
            changed = {d: (base[d], sub[d]) for d in base if sub[d] != base[d]}
            adv = {d: hm[sub[d]][0] for d in sub}
            e[tag] = {
                "feature_present": True,
                "digits_substituted": len(changed),
                "substitutions": changed,
                "advances_after": adv,
                "uniform_after": len(set(adv.values())) == 1,
                "value_after": sorted(set(adv.values())),
                "INERT_for_digits": len(changed) == 0,
            }
        out[p.stem] = e
        t, z = e.get("tnum"), e.get("zero")
        if not t:
            ts = "absent"
        elif t["INERT_for_digits"]:
            ts = "PRESENT-but-INERT"
        else:
            ts = f"{t['digits_substituted']}sub uniform={t['uniform_after']}"
        if not z:
            zs = "absent"
        elif z["INERT_for_digits"]:
            zs = "PRESENT-but-INERT"
        else:
            zs = f"{z['digits_substituted']}sub"
        print(f"{p.stem:<28} defaultUniform={str(e['default_uniform']):<5} "
              f"tnum={ts:<22} zeroFeat={zs}")
    OUT.write_text(json.dumps(out, indent=1))
    print("->", OUT)


main()
