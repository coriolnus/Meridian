"""Batch J — learning-loop honesty: skill_chain from setup (#4/#25), regime vocab alignment (#3),
magnitude-aware bandit reward (#29), and the honest learning scorecard (#40)."""
import pytest

from meridian import skills, reflect, guard, config, analytics, regime as regime_mod


def test_screener_for_maps_setup():
    assert skills.screener_for("breakout_vcp") == "vcp-screener"       # matches the registry entry (no star)
    assert skills.screener_for("pullback") == "pullback-screener"
    assert skills.screener_for("unknown") == "vcp-screener"


def test_regime_vocab_matches_what_the_engine_emits():
    assert set(config.VALID_REGIMES) == {regime_mod.TREND_UP, regime_mod.TREND_DOWN,
                                         regime_mod.CHOP, regime_mod.HIGH_VOL}
    assert "risk_off" not in config.VALID_REGIMES                       # phantom regime dropped
    bounds, goal, params = config.bounds(), config.goal(), config.default_strategy()["params"]
    ok = guard.validate_change({"variable": "entry.min_score@high_vol", "new": params["entry.min_score"] + 1},
                               params, bounds, goal, [], 0)
    assert ok.ok                                                       # a real emitted regime is now tunable
    bad = guard.validate_change({"variable": "entry.min_score@risk_off", "new": params["entry.min_score"] + 1},
                                params, bounds, goal, [], 0)
    assert not bad.ok and "regime" in bad.reasons[0]


def test_bandit_reward_is_magnitude_aware():
    # same ship status, but one held up (+delta, promoted) and one got rolled back (−delta)
    good = [{"variable": "A", "status": "promoted", "realized_delta": 0.08}]
    bad = [{"variable": "B", "status": "rolled_back", "realized_delta": -0.08}]
    sg = reflect._ledger_stats(good)["A"]
    sb = reflect._ledger_stats(bad)["B"]
    assert sg["reward"] > sb["reward"]                                 # magnitude, not binary ship
    # regime knobs credit the base variable
    rk = reflect._ledger_stats([{"variable": "A@chop", "status": "live", "realized_delta": 0.05}])
    assert "A" in rk and "A@chop" not in rk


def test_learning_scorecard_is_honest(monkeypatch, sandbox_state):
    monkeypatch.setattr(analytics, "_trades", lambda: [])
    monkeypatch.setattr(analytics.memory, "all_hypotheses", lambda: [])
    monkeypatch.setattr(analytics.store, "read_json", lambda *a, **k: {"versions": {}})
    sc = analytics.learning_scorecard()
    assert sc["shipped"] == 0 and sc["outcomes_measured"] == 0
    assert "hipotez yok" in sc["verdict"]                              # no vanity — says the loop hasn't run
    # with a measured, calibrated outcome it reports learning
    hyps = [{"status": "promoted", "realized_delta": 0.06, "calibration_hit": True, "predicted_delta": 0.03}
            for _ in range(3)]
    monkeypatch.setattr(analytics.memory, "all_hypotheses", lambda: hyps)
    sc2 = analytics.learning_scorecard()
    assert sc2["outcomes_measured"] == 3 and sc2["promoted"] == 3
