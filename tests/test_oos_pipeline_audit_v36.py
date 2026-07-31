"""test_oos_pipeline_audit_v36.py — oos_pipeline denetimi (2026-07-21, tur 22).

Modülün merkezi iddiası: "Confirm-OOS, aramanın ASLA dokunmadığı dilimdir." Kazananın-laneti
savunmasının tamamı buna dayanıyor. 7. soru: bu ayrıklık NEREDE kanıtlanıyor? Hiçbir yerde —
dilimleri backtest kuruyor, kapı onları hazır alıyor, ve ikisinin kesişmediğini kimse doğrulamıyordu.

  OP1 arama/teyit dilimleri AYRIK olmalı (tek bir işlem bile ikisinde birden olamaz)
  OP2 teyit dilimi arama diliminden SONRA gelmeli (kronoloji)
  OP3 sınırı AŞAN işlem (segmentte açılıp sonrasında kapanan) HİÇBİR dilime sayılmaz — purge
  OP4 dilim yoksa legacy yasaya dürüstçe düşülür (sessiz 'geçti' YOK)
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from meridian import backtest, config
from meridian.oos_pipeline import OutOfSamplePipeline, split_date, SEARCH_FRACTION
from tests.conftest import make_bars


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _wf():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150)}
    return backtest.walk_forward(config.default_strategy()["params"], bars, idx, config.goal(),
                                 "2022-06-01", "2022-10-01", "2023-04-01", "2023-06-01",
                                 oos_folds=["2022-10-01", "2023-01-01", "2023-04-01"], embargo_days=5)


def _ids(rows):
    return {(t.get("ticker"), str(t.get("ts_open"))[:10], str(t.get("ts_close"))[:10]) for t in rows}


# ---------- OP1/OP2: ayrıklık ve kronoloji ----------
def test_op1_search_and_confirm_slices_are_disjoint(seeded):
    wf = _wf()
    assert OutOfSamplePipeline.has_slices(wf)
    overlap = _ids(wf["_trades_search"]) & _ids(wf["_trades_confirm"])
    assert not overlap, f"aynı işlem HEM aramada HEM teyitte: {list(overlap)[:3]}"


def test_op2_confirm_is_strictly_after_search(seeded):
    wf = _wf()
    sp = wf["oos_split"]
    assert sp["search_end"] == sp["confirm_start"]
    for t in wf["_trades_search"]:
        assert str(t["ts_open"])[:10] < sp["search_end"]
    for t in wf["_trades_confirm"]:
        assert str(t["ts_open"])[:10] >= sp["confirm_start"]


def test_op3_straddling_trades_are_purged_from_both():
    """Sınırı aşan işlem (dilimde açılıp SONRASINDA kapanan) hiçbir dilime sayılmaz: sızıntı değil,
    purge. Aksi halde teyit dilimi, arama döneminin fiyat hareketiyle kirlenir."""
    t = {"ts_open": "2025-01-05", "ts_close": "2025-03-01"}
    assert backtest._in_segment(t, "2025-01-01", "2025-02-01") is False   # kapanış dilim dışında
    assert backtest._in_segment(t, "2025-02-01", "2025-04-01") is False   # açılış dilim öncesinde
    inside = {"ts_open": "2025-01-05", "ts_close": "2025-01-20"}
    assert backtest._in_segment(inside, "2025-01-01", "2025-02-01") is True


def test_op3b_boundary_date_belongs_to_exactly_one_segment():
    t = {"ts_open": "2025-02-01", "ts_close": "2025-02-10"}
    a = backtest._in_segment(t, "2025-01-01", "2025-02-01")               # yarı-açık: üst sınır hariç
    b = backtest._in_segment(t, "2025-02-01", "2025-03-01")
    assert (a, b) == (False, True)


def test_split_date_is_the_declared_fraction():
    import datetime as dt
    sd = split_date("2024-07-01", "2025-12-31")
    d0, d1 = dt.date(2024, 7, 1), dt.date(2025, 12, 31)
    assert sd == (d0 + dt.timedelta(days=int(round((d1 - d0).days * SEARCH_FRACTION)))).isoformat()


# ---------- OP4: dilim yoksa dürüst legacy ----------
def test_op4_missing_slices_never_silently_pass(seeded):
    pipe = OutOfSamplePipeline(config.goal(), n_boot=50)
    bare = {"oos_score": 0.5}
    s = pipe.evaluate_search(bare, bare)
    c = pipe.confirm(bare, bare)
    assert s.law == "legacy" and s.passes is False and "legacy" in s.why
    assert c.law == "legacy" and c.passes is False


def test_op4b_confirm_bar_is_not_lower_than_it_claims(seeded):
    from meridian.probgate import P_CONFIRM
    pipe = OutOfSamplePipeline(config.goal(), n_boot=50)
    assert pipe.p_confirm == P_CONFIRM and 0.5 < P_CONFIRM <= 1.0


# ---------- teyit gerçekten veto edebiliyor mu ----------
def test_confirm_vetoes_a_search_only_edge(seeded):
    """Kazananın-laneti senaryosu uçtan uca: edge yalnız arama diliminde varsa TEYİT reddetmeli."""
    from tests.test_decision_v3 import synth_trades, wf_fix
    from tests import wf_fixtures as wf
    goal = config.goal()
    inc = synth_trades(111, seed=11)
    # EDGE SINIRI, wf_fix'in GERÇEK Search/Confirm sınırıyla hizalı olmalı. wf_fix merkezi fabrikaya
    # taşınınca OOS penceresi wf.OOS_START/OOS_END (tek kaynak) oldu; sabit "2024-07-01" edge'i eski
    # bir sınıra koyuyordu ve enjekte edilen üstünlük wf_fix'in Confirm dilimine TAŞIYORDU — teyit de
    # haklı olarak geçiyordu (senaryonun tam tersi). Edge'i wf.S_END'den ÖNCEye koy: yalnız Search'te
    # görünsün, Confirm dokunulmamış kalsın (2026-07-23, çapraz-dosya fikstür sürüklenmesi).
    s_end = wf.S_END
    cand = [{**t, "r_multiple": t["r_multiple"] + (0.6 if t["ts_open"] < s_end else -0.1),
             "pnl_dollars": t["pnl_dollars"] + (600 if t["ts_open"] < s_end else -100)} for t in inc]
    pipe = OutOfSamplePipeline(goal, n_boot=400, seed=42)
    inc_wf, cand_wf = wf_fix(inc, goal), wf_fix(cand, goal)
    assert pipe.evaluate_search(inc_wf, cand_wf).passes is True
    assert pipe.confirm(inc_wf, cand_wf).passes is False
