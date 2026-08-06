#!/usr/bin/env python3
"""Recursive ships Sans and Mono in ONE variable file via the MONO axis.
Pin MONO/CASL/slnt/CRSV, keep wght live -> two deployable faces."""
import pathlib
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

D = pathlib.Path(sys.argv[1])
src = D / "Recursive-VF.ttf"

f = TTFont(str(src))
print("axes:", {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in f["fvar"].axes})

for name, loc in (("RecursiveSansLinear-VF.ttf", {"MONO": 0.0, "CASL": 0.0, "slnt": 0.0, "CRSV": 0.0}),
                  ("RecursiveMonoLinear-VF.ttf", {"MONO": 1.0, "CASL": 0.0, "slnt": 0.0, "CRSV": 0.0})):
    ft = TTFont(str(src))
    out = instancer.instantiateVariableFont(ft, loc, inplace=False, updateFontNames=False)
    p = D / name
    out.save(str(p))
    print(f"{name}: {p.stat().st_size} bytes, axes left =",
          {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in out["fvar"].axes}
          if "fvar" in out else "none")
