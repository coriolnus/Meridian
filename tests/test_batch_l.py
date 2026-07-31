"""Batch L — strategy edge & exits: partial scale-out folded into one trade (#8), give-back exit (#10),
extension climax filter (#13), and that every new knob is tunable but OFF by default (baseline intact)."""
import numpy as np
import pandas as pd
import pytest

from meridian import broker, strategy, config, guard
from tests.conftest import make_bars


def test_scale_out_folds_two_legs_into_one_trade():
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="d1", equity=100_000)   # entry 100, R/share=10, qty=100
    q0 = pos.qty
    params = {"exit.scale_out_r": 2.0, "exit.scale_out_frac": 0.5}
    assert b.scale_out(pos, {"high": 120.0}, params) is True             # high hits entry+2R -> bank half
    assert pos.scaled_out and pos.qty == q0 - q0 // 2
    assert pos.trail_stop >= pos.entry                                   # runner locked at breakeven
    row = b.close_position("X", raw_exit=130.0, reason="target", ts="d2")
    banked = (q0 // 2) * (120 - 100)                                     # 50 * 20 = 1000
    runner = (q0 - q0 // 2) * (130 - 100)                                # 50 * 30 = 1500
    assert row["r_multiple"] == pytest.approx((banked + runner) / pos.risk_dollars, abs=0.02)  # ~2.5R
    assert row["scaled_out"] is True and row["pnl_dollars"] == pytest.approx(banked + runner, abs=2)


def test_scale_out_off_by_default_is_noop():
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="d1", equity=100_000)
    assert b.scale_out(pos, {"high": 200.0}, config.default_strategy()["params"]) is False   # frac=0 -> off
    assert not pos.scaled_out


def test_new_exit_knobs_default_off_leave_manage_unchanged():
    bars = make_bars(120, breakout_at=90)
    pos = {"entry": float(bars["close"].iloc[80]), "stop": float(bars["close"].iloc[80]) * 0.95,
           "trail_stop": float(bars["close"].iloc[80]) * 0.95, "r_per_share": float(bars["close"].iloc[80]) * 0.05}
    base = config.default_strategy()["params"]
    dec = strategy.manage_position(bars, pos, base, bars_held=5, regime_ok=True)
    # giveback/chandelier off by default -> no premature 'giveback' exit
    assert dec.exit_reason != "giveback"


def test_all_batch_l_knobs_are_tunable():
    b, g, p = config.bounds(), config.goal(), config.default_strategy()["params"]
    for k in ("exit.giveback_pct", "exit.chandelier_lookback", "entry.max_ext_atr",
              "entry.rs_dual_horizon", "exit.scale_out_r", "exit.scale_out_frac"):
        assert k in p and k in b
        step = b[k]["step"]
        v = guard.validate_change({"variable": k, "new": p[k] + step if p[k] + step <= b[k]["max"] else b[k]["min"]},
                                  p, b, g, [], 0)
        assert v.ok, f"{k} not tunable: {v.reasons}"
