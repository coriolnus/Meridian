"""Batch D — capital-preservation gates: graded de-risk ladder, entry gap breaker, Monte Carlo
tail risk (VaR/CVaR), portfolio-heat REVIEW flag, and the earnings blackout."""
import csv
import pytest

from meridian import broker, score, guard, earnings, config


# ---------------- graded de-risk ladder ----------------
def test_derisk_mult_continuous_ramp():
    assert broker.derisk_mult(100_000, 100_000) == 1.0     # at peak — full size
    assert broker.derisk_mult(98_000, 100_000) == 1.0      # <=3% dd — full size
    assert broker.derisk_mult(96_000, 100_000) == pytest.approx(0.8, abs=1e-3)   # 4% dd — linear
    assert broker.derisk_mult(93_000, 100_000) == pytest.approx(0.2, abs=1e-3)   # 7% dd — linear
    assert broker.derisk_mult(90_000, 100_000) == 0.0      # >=8% dd — no new size
    assert broker.derisk_mult(100_000, 0) == 1.0           # undefined peak — safe default
    # monotonic non-increasing as drawdown deepens
    seq = [broker.derisk_mult(e, 100_000) for e in (100_000, 97_000, 95_000, 93_000, 91_000)]
    assert all(a >= b for a, b in zip(seq, seq[1:]))


def test_position_throttle_cuts_count_on_drawdown():
    assert broker.max_positions_at(100_000, 100_000, 5) == 5    # at peak — full slate
    assert broker.max_positions_at(95_000, 100_000, 5) == 3     # 5% dd (mult 0.6) -> 3
    assert broker.max_positions_at(90_000, 100_000, 5) == 0     # past the floor -> none


def test_notional_cap_bounds_single_name(monkeypatch):
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    # very tight stop -> sizing wants a huge share count; notional cap must clamp it to 25% of equity
    plan = {"id": "P1", "ticker": "X", "stop": 99.9, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000)
    assert pos is not None
    assert pos.qty * pos.entry <= 0.25 * 100_000 + 1     # notional within 25% of equity


def test_size_mult_shrinks_risk():
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 120.0, "size_r": 1.0}
    full = b.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000, size_mult=1.0)
    b2 = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    half = b2.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000, size_mult=0.5)
    assert half.qty == pytest.approx(full.qty // 2, abs=1)   # half the risk -> ~half the shares


# ---------------- entry gap breaker ----------------
def test_gap_up_above_trigger_is_skipped():
    """E1 (WP-E, 2026-07-31) — İDDİA SIKILAŞTI. Eskiden tetiğin %2 üstünde açılan bir bar DOLARdI
    (yalnız %4 max-chase bağlıyordu); artık `broker.entry_law` limit tavanı (varsayılan %1) daha
    SIKI olan taraftır ve İKİ MOTORDA da bağlar. %4 chase tavanı dış zarf olarak yerinde kalır."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0, "size_r": 1.0}
    # opens 6% above the trigger (> MAX_ENTRY_GAP_PCT) -> no chase
    assert b.fill_entry(plan, next_open=106.0, ts="2024-01-02", equity=100_000) is None
    # opens 2% above the trigger -> LİMİT TAVANI (%1) reddeder, sebebi adıyla kaydedilir
    rej = {}
    assert b.fill_entry(plan, next_open=102.0, ts="2024-01-02", equity=100_000, reject_out=rej) is None
    assert rej["reason"] == broker.EV_MISSED_LIMIT
    # tavanın ALTINDA açılış (%0.5) -> dolar
    assert b.fill_entry(plan, next_open=100.5, ts="2024-01-02", equity=100_000) is not None


def test_gap_through_stop_is_skipped():
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0, "size_r": 1.0}
    assert b.fill_entry(plan, next_open=94.0, ts="2024-01-02", equity=100_000) is None   # opened below the stop


# ---------------- ADV liquidity cap + price impact ----------------
def test_adv_caps_order_and_adds_impact():
    plan = {"id": "P1", "ticker": "X", "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0, "size_r": 1.0}
    # unconstrained sizing wants ~200 shares ($1000 risk / $5 per share) on a 1R/$100k book
    b0 = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    free = b0.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000)
    # ADV of 5000 shares -> cap = 2% * 5000 = 100 shares; order is clipped to the liquidity cap
    b1 = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    capped = b1.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000, adv=5000)
    assert capped.qty == 100 and capped.qty < free.qty
    assert capped.entry > 100.0                       # participation impact pushed the fill up
    # a deep-liquidity name (huge ADV) fills the full size with negligible impact
    b2 = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    deep = b2.fill_entry(plan, next_open=100.0, ts="2024-01-02", equity=100_000, adv=50_000_000)
    assert deep.qty == free.qty and deep.entry == pytest.approx(100.0, abs=1e-3)


# ---------------- Monte Carlo tail risk ----------------
def test_tail_risk_none_below_min_sample():
    few = [{"r_multiple": 0.3} for _ in range(5)]
    assert score.tail_risk(few) is None


def test_tail_risk_is_deterministic_and_ordered():
    winners = [{"r_multiple": 2.0} for _ in range(20)] + [{"r_multiple": -1.0} for _ in range(10)]
    losers = [{"r_multiple": 0.5} for _ in range(10)] + [{"r_multiple": -1.0} for _ in range(20)]
    a1 = score.tail_risk(winners)
    a2 = score.tail_risk(winners)
    assert a1 == a2                                    # deterministic (fixed seed, same draw)
    b = score.tail_risk(losers)
    assert b["cvar_r"] > a1["cvar_r"]                  # loss-heavy sample has worse expected shortfall
    assert a1["var_r"] <= a1["cvar_r"]                 # CVaR (mean tail loss) is never below VaR


# ---------------- portfolio heat REVIEW flag ----------------
def test_portfolio_heat_flags_review():
    goal = config.goal()
    params = config.default_strategy()["params"]
    regime = {"exposure_budget_pct": 60}
    plan = {"ticker": "X", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 2.5, "score": 90}
    # 3.0R already open + 1.0R new = 4.0R > HEAT_REVIEW_R(3.5) -> REVIEW
    v, r = guard.classify_gate(plan, {"open_positions": 3, "sector_counts": {}, "day_pnl_pct": 0,
                                      "open_risk_r": 3.0}, regime, goal, params)
    assert v == "REVIEW" and any("ısı" in x for x in r)


def test_leading_sectors_as_dicts_do_not_crash_classify_gate():
    """Regression: loop.daily_cycle fills regime['leading_sectors'] with DICTS (sector_momentum output),
    but classify_gate joined them as strings -> a live cycle with a candidate in a non-leading sector
    raised `TypeError: sequence item 0: expected str instance, dict found`. The backtest left the field []
    which hid the bug; the learning sprint (510 live-style sessions) surfaced it. The gate must normalize
    dict->name so it neither crashes nor mis-classifies membership."""
    goal = config.goal()
    params = config.default_strategy()["params"]
    regime = {"exposure_budget_pct": 60,
              "leading_sectors": [{"sector": "health", "momentum": 0.05, "n": 3},
                                  {"sector": "energy", "momentum": 0.03, "n": 2}]}
    port = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0, "open_risk_r": 0.0, "max_corr": 0.0}
    plan = {"ticker": "X", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 3.0, "score": 90}
    v, reasons = guard.classify_gate(plan, port, regime, goal, params)   # would TypeError on the old code
    assert v in ("GO", "REVIEW")
    assert any("lider sektörlerinde değil" in x and "health" in x for x in reasons)   # names extracted, joined
    # a plan already IN a leading sector must NOT get the "not a leader" flag
    _, reasons_in = guard.classify_gate({**plan, "sector": "health"}, port, regime, goal, params)
    assert not any("lider sektörlerinde değil" in x for x in reasons_in)


# ---------------- earnings blackout ----------------
def test_earnings_blackout(tmp_path, monkeypatch):
    st = tmp_path / "state"
    st.mkdir()
    monkeypatch.setattr(config, "STATE", st)
    earnings.clear_cache()
    with (st / "earnings.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "date"])          # header tolerated
        w.writerow(["AAPL", "2026-02-01"])
    earnings.clear_cache()
    assert earnings.in_blackout("AAPL", "2026-01-28") is True    # 4 days before -> blackout
    assert earnings.in_blackout("AAPL", "2026-01-20") is False   # 12 days before -> clear
    assert earnings.in_blackout("AAPL", "2026-02-05") is False   # after the report -> clear
    assert earnings.in_blackout("MSFT", "2026-01-28") is False   # unknown ticker -> never blocks
