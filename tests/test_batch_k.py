"""Batch K — risk & capital: hard aggregate-heat cap (#18), real correlation concentration (#16),
block-bootstrap tail (#22), Kelly analytic (#19)."""
import numpy as np
import pandas as pd
import pytest

from meridian import guard, indicators, score, config


def test_hard_heat_cap_is_no_go():
    goal, params = config.goal(), config.default_strategy()["params"]
    regime = {"exposure_budget_pct": 60}
    plan = {"ticker": "X", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 2.5, "score": 90}
    # OPERATÖR KARARI 2026-08-03 (d01ccb5): heat_hard_r 4,5→5,0R — senaryo tavanın üstüne taşındı.
    # 4.5R already open + 1.0R new = 5.5R > HEAT_HARD_R(5.0) -> NO_GO.
    # open_risk_r SENTETİKTİR (4 pozisyon × max_position_r=1,0 zarfının üstünde) ve BİLEREK öyle:
    # tavan artık zarfa EŞİT olduğu için, ısı vetosunu open_positions vetosundan AYRIŞTIRAN tek
    # kurulum budur — open_positions 4'te kalır, düşen tek sert kural heat_hard'dır.
    v, r = guard.classify_gate(plan, {"open_positions": 4, "sector_counts": {}, "day_pnl_pct": 0,
                                      "open_risk_r": 4.5}, regime, goal, params)
    assert v == "NO_GO" and any("sert tavan" in x for x in r)


def test_correlation_flag_reviews_concentrated_add():
    goal, params = config.goal(), config.default_strategy()["params"]
    regime = {"exposure_budget_pct": 60}
    plan = {"ticker": "X", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 2.5, "score": 90}
    v, r = guard.classify_gate(plan, {"open_positions": 1, "sector_counts": {}, "day_pnl_pct": 0,
                                      "max_corr": 0.93}, regime, goal, params)
    assert v == "REVIEW" and any("korelasyon" in x for x in r)


def test_corr_max_detects_comovement():
    base = pd.Series(np.linspace(100, 140, 90) + np.sin(np.arange(90)))
    twin = base * 1.5 + 3                              # perfectly co-moving
    indep = pd.Series(100 + np.cos(np.arange(90) * 2.7) * 5)
    assert indicators.corr_max(twin, [indicators.returns_tail(base)]) > 0.9
    assert indicators.corr_max(indep, [indicators.returns_tail(base)]) < 0.9
    assert indicators.corr_max(base, []) == 0.0        # nothing held -> 0


def test_block_bootstrap_tail_still_ordered_and_deterministic():
    winners = [{"r_multiple": 2.0} for _ in range(20)] + [{"r_multiple": -1.0} for _ in range(10)]
    losers = [{"r_multiple": 0.5} for _ in range(10)] + [{"r_multiple": -1.0} for _ in range(20)]
    a1, a2 = score.tail_risk(winners), score.tail_risk(winners)
    assert a1 == a2                                    # deterministic (seeded)
    assert score.tail_risk(losers)["cvar_r"] > a1["cvar_r"]
    assert a1["var_r"] <= a1["cvar_r"]


def test_kelly_fraction_from_realized_edge():
    trades = [{"r_multiple": 2.0} for _ in range(6)] + [{"r_multiple": -1.0} for _ in range(6)]
    k = score.kelly_fraction(trades)
    assert k is not None and k["win_rate"] == 0.5 and k["win_loss_ratio"] == pytest.approx(2.0)
    assert k["full_kelly"] == pytest.approx(0.25, abs=1e-2) and k["half_kelly"] >= 0
    assert score.kelly_fraction([{"r_multiple": 0.1}] * 5) is None   # below min sample
