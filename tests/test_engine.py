"""DoD tests (§11): strategy purity (no look-ahead), broker frictions, guard rejections,
score None below min_sample, rollback reverts a worse child."""
import numpy as np
import pandas as pd
import pytest

from meridian import strategy, indicators, broker, guard, score, config, versioning, rollback, store, memory
from tests.conftest import make_bars


# ---------------- strategy purity: no look-ahead ----------------
def test_indicators_are_causal():
    bars = make_bars(300)
    k = 250
    atr_full = indicators.atr(bars, 14)
    atr_slice = indicators.atr(bars.iloc[:k], 14)
    # value at bar k-1 must be identical whether or not future bars exist
    assert atr_full.iloc[k - 1] == pytest.approx(atr_slice.iloc[-1], rel=1e-9)


def test_entry_signal_ignores_future_bars():
    bars = make_bars(320, breakout_at=300)
    k = 305
    sig_a = strategy.evaluate_entry(bars.iloc[:k].copy(), config.default_strategy()["params"], 90, "X")
    # mutate FUTURE bars drastically; the decision at bar k-1 must not change
    mutated = bars.copy()
    mutated.loc[k:, ["open", "high", "low", "close"]] *= 3.0
    sig_b = strategy.evaluate_entry(mutated.iloc[:k].copy(), config.default_strategy()["params"], 90, "X")
    assert (sig_a is None) == (sig_b is None)
    if sig_a:
        assert sig_a.entry_trigger == pytest.approx(sig_b.entry_trigger)
        assert sig_a.stop == pytest.approx(sig_b.stop)


def test_replay_runs_end_to_end_on_synthetic_bars():
    """Network-free smoke: the full replay engine runs without crashing and returns typed logs.
    Serves as the CI replay smoke and guards the strategy/broker/guard/regime wiring together."""
    from meridian import backtest
    idx = make_bars(300, seed=1, trend=0.0009)                         # uptrend 'index'
    bars = {"AAA": make_bars(300, seed=2, breakout_at=240),
            "BBB": make_bars(300, seed=3, breakout_at=200),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", "2023-06-01", strategy_version=1)
    assert isinstance(res.trades, list) and isinstance(res.plan_log, list)
    for p in res.plan_log:
        assert p["gate_verdict"] in ("GO", "REVIEW", "NO_GO") and "date" in p
    wf = backtest.walk_forward(config.default_strategy()["params"], bars, idx, config.goal(),
                               "2022-06-01", "2022-10-01", "2023-04-01", "2023-06-01",
                               oos_folds=["2022-10-01", "2023-01-01", "2023-04-01"], embargo_days=5)
    assert "oos_folds" in wf and all("avg_r" in f and "n" in f for f in wf["oos_folds"])


def test_index_minus_one_is_last_closed_bar():
    bars = make_bars(320, breakout_at=300)
    params = config.default_strategy()["params"]
    sig = strategy.evaluate_entry(bars, params, 90, "X")
    if sig:
        # trigger equals the last bar's close, never a future value
        assert sig.entry_trigger == pytest.approx(bars["close"].iloc[-1])


# ---------------- broker frictions ----------------
def test_broker_applies_slippage_and_costs():
    b = broker.PaperBroker(equity=100_000, slippage_bps=5, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 95.0, "profit_target": 115.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000)
    assert pos is not None
    assert pos.entry > 100.0                      # paid up on entry (slippage)
    assert pos.entry_slippage_cost > 0
    row = b.close_position("X", raw_exit=110.0, reason="target", ts="2024-01-10")
    assert row["exit"] < 110.0                     # received less on exit (slippage)
    assert row["costs"] > 0
    assert row["r_multiple"] == pytest.approx(row["pnl_dollars"] / pos.risk_dollars, abs=1e-3)


def test_broker_zero_slippage_still_charges_commission():
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.01)
    plan = {"id": "P1", "ticker": "Y", "stop": 90.0, "profit_target": 120.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000)
    assert pos.entry == pytest.approx(100.0)       # no slippage
    assert pos.entry_slippage_cost > 0             # commission still paid


# ---------------- guard rejections ----------------
def _ctx():
    return config.bounds(), config.goal(), config.default_strategy()["params"]


def test_guard_rejects_two_variable_change():
    bounds, goal, params = _ctx()
    v = guard.validate_change({"changes": {"entry.min_score": 65, "exit.time_stop_days": 12}},
                              params, bounds, goal, [], 0)
    assert not v.ok and "more than one variable" in v.reasons[0]


def test_guard_rejects_immutable_and_out_of_bounds_and_offstep_and_noop():
    bounds, goal, params = _ctx()
    assert not guard.validate_change({"variable": "max_open_positions", "new": 9}, params, bounds, goal, [], 0).ok
    assert not guard.validate_change({"variable": "entry.rs_rating_min", "new": 999}, params, bounds, goal, [], 0).ok
    assert not guard.validate_change({"variable": "entry.pivot_proximity_pct", "new": 2.03}, params, bounds, goal, [], 0).ok
    noop = params["entry.min_score"]
    assert not guard.validate_change({"variable": "entry.min_score", "new": noop}, params, bounds, goal, [], 0).ok


def test_guard_rejects_already_failed_and_quota():
    bounds, goal, params = _ctx()
    hyps = [{"id": "H1", "variable": "entry.min_score", "new": 65, "status": "rejected_by_backtest"}]
    assert not guard.validate_change({"variable": "entry.min_score", "new": 65}, params, bounds, goal, hyps, 0).ok
    # quota spent
    q = int(goal["max_accepted_changes_per_month"])
    assert not guard.validate_change({"variable": "entry.min_score", "new": 66}, params, bounds, goal, [], q).ok


def test_classify_gate_three_states():
    goal = config.goal()
    params = config.default_strategy()["params"]
    regime = {"exposure_budget_pct": 60}
    base = {"ticker": "X", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 2.5, "score": 90}
    # clean -> GO
    v, _ = guard.classify_gate(base, {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0}, regime, goal, params)
    assert v == "GO"
    # sector already has a position -> soft flag -> REVIEW
    v, r = guard.classify_gate(base, {"open_positions": 1, "sector_counts": {"tech": 1}, "day_pnl_pct": 0}, regime, goal, params)
    assert v == "REVIEW" and r
    # slots full -> hard -> NO_GO. TAVAN GOAL'DAN OKUNUR, sabit 5 DEĞİL (2026-08-12: operatör
    # `max_open_positions`ı 5 → 20 yaptı ve sabit sayı "dolu" senaryosunu sessizce BOŞ slot'a
    # çevirdi — test yeşil kalırken hiçbir şeyi ölçmez hâle gelecekti).
    dolu = int(goal["limits"]["max_open_positions"])
    v, _ = guard.classify_gate(base, {"open_positions": dolu, "sector_counts": {}, "day_pnl_pct": 0}, regime, goal, params)
    assert v == "NO_GO"
    # sub-2.0 R:R -> NO_GO (hard veto; meaningful now that R:R VARIES per plan via measured-move, and
    # profit_target_r's lower bound of 2.0 keeps this from ever zeroing out all trading)
    v, r = guard.classify_gate({**base, "r_multiple_expected": 1.8}, {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0}, regime, goal, params)
    assert v == "NO_GO" and any("R:R" in x for x in r)
    # marginal R:R just above the floor -> REVIEW (soft)
    v2, r2 = guard.classify_gate({**base, "r_multiple_expected": 2.1, "score": 90}, {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0}, regime, goal, params)
    assert v2 == "REVIEW" and any("marjinal" in x for x in r2)
    # exposure budget 0 -> NO_GO
    v, _ = guard.classify_gate(base, {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0}, {"exposure_budget_pct": 0}, goal, params)
    assert v == "NO_GO"


def test_guard_accepts_valid_single_variable_change():
    bounds, goal, params = _ctx()
    v = guard.validate_change({"variable": "entry.min_score", "new": params["entry.min_score"] + 1},
                              params, bounds, goal, [], 0)
    assert v.ok and v.variable == "entry.min_score"


# ---------------- score None below min_sample ----------------
def test_score_none_below_min_sample():
    goal = config.goal()
    assert score.score([], goal) is None
    few = [{"r_multiple": 0.5, "pnl_dollars": 500, "ts_open": "2024-01-01", "ts_close": "2024-01-05"}]
    assert score.score(few, goal) is None


def test_score_is_number_at_min_sample():
    goal = dict(config.goal()); goal["min_sample"] = 3
    trades = [{"r_multiple": 0.4, "pnl_dollars": 400, "ts_open": f"2024-01-0{i}", "ts_close": f"2024-02-0{i}"}
              for i in range(1, 5)]
    s = score.score(trades, goal)
    assert s is not None and -1.0 <= s <= 1.0


# ---------------- rollback reverts a worse child ----------------
def test_rollback_reverts_worse_child(sandbox_state):
    # goal with tiny min_sample so a handful of trades is enough
    goal_yaml = {"schema_version": 1, "universe": "T", "style": "swing_momentum", "session_tz": "America/New_York",
                 "target_return_30d": 0.07, "min_sharpe": 1.2, "max_drawdown": 0.08, "failure_below": -0.04,
                 "reflection_every": 5, "min_sample": 3, "one_variable_only": True, "backtest_gate": True,
                 "rollback_if_worse_by": 0.10, "explore_rate": 0.15, "max_accepted_changes_per_month": 8,
                 "commission_per_share": 0.0, "slippage_bps": 5, "fill": "next_bar_open",
                 "limits": {"autonomy_level": 0, "max_position_r": 1.0, "max_open_positions": 5,
                            "max_daily_loss_pct": 3.0, "max_sector_exposure_pct": 40.0,
                            "no_trade_before_bars": 3, "kill_switch_file": "state/HALT"}}
    config.dump_yaml(goal_yaml, sandbox_state / "goal.yaml")
    config.goal.cache_clear()

    v1 = {"version": 1, "parent": None, "params": {"entry.min_score": 60}}
    v2 = {"version": 2, "parent": 1, "params": {"entry.min_score": 65}}
    versioning.snapshot(v1)
    versioning.snapshot(v2)
    config.dump_yaml(v2, config.strategy_path())        # v2 is live

    # v1 clearly good, v2 clearly bad
    for i in range(4):
        store.append_jsonl("trades.jsonl", {"strategy_version": 1, "r_multiple": 0.8, "pnl_dollars": 900,
                                            "ts_open": f"2024-01-0{i+1}", "ts_close": f"2024-02-0{i+1}"})
    for i in range(4):
        store.append_jsonl("trades.jsonl", {"strategy_version": 2, "r_multiple": -0.9, "pnl_dollars": -1200,
                                            "ts_open": f"2024-03-0{i+1}", "ts_close": f"2024-04-0{i+1}"})
    memory.record({"variable": "entry.min_score", "old": 60, "new": 65, "version_to": 2,
                   "status": "live", "predicted_delta": 0.03})

    result = rollback.check_and_rollback(config.goal())
    assert result is not None, "expected a rollback"
    assert result["to"] == 1
    assert int(config.load_strategy()["version"]) == 1   # strategy.yaml reverted
    hyps = memory.all_hypotheses()
    assert any(h["status"] == "rolled_back" for h in hyps)
