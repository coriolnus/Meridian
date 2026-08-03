"""DUMAN TESTİ — harness kablolaması (kanca alanları, kaçan-dolum hesabı, kötümser ikiz sütun)
kısa pencere + küçük evrenle sınanır. KARNE DEĞİL: skorlar anlamsızdır, yalnız kod yolu denenir.
Kullanım: duman.py <kol_state_kaynagi> <n_sembol> <oos_end> <holdout_end>"""
from __future__ import annotations

import shutil
import sys
import pathlib

KAYNAK = sys.argv[1] if len(sys.argv) > 1 else "b_mkt"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
SB = pathlib.Path(__file__).resolve().parent
if (SB / "state_duman").exists():
    shutil.rmtree(SB / "state_duman")
shutil.copytree(SB / f"state_{KAYNAK}", SB / "state_duman", symlinks=True)

sys.argv = ["kosum.py", "duman"]

import kosum  # noqa: E402

kosum.GEOM = dict(is_start="2022-01-01", oos_start="2023-01-01", oos_end="2024-01-01",
                  holdout_end="2024-04-01",
                  folds=["2023-01-01", "2023-07-01", "2024-01-01"])

_orig = kosum.dataset.load_cached


def _kucuk():
    bars, index = _orig()
    keys = sorted(bars)[:N]
    return {k: bars[k] for k in keys}, index


kosum.dataset.load_cached = _kucuk
kosum.main()
