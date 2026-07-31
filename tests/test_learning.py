"""Batch E — advanced learning loop: UCB bandit variable selection (explore) and regime-conditional
parameters (base@regime knobs), both preserving the immutable one_variable_only invariant."""
import pytest

from meridian import reflect, guard, versioning, config


# ---------------- UCB bandit proposer ----------------
def test_ucb_prefers_untried_variables():
    # one variable has a bad track record; another was never tried -> untried wins (optimism/+inf)
    hyps = [{"variable": "entry.min_score", "new": 61, "status": "rejected_by_backtest"},
            {"variable": "entry.min_score", "new": 62, "status": "rolled_back"}]
    rank = reflect._ucb_rank(["entry.min_score", "stop_loss_atr_mult"], hyps)
    assert rank[0] == "stop_loss_atr_mult"          # never tried -> explored first


def test_ucb_rank_is_deterministic():
    hyps = [{"variable": "exit.time_stop_days", "new": 12, "status": "live"},
            {"variable": "exit.time_stop_days", "new": 13, "status": "rejected_by_backtest"}]
    cands = ["exit.time_stop_days", "entry.rs_rating_min", "position_size_r"]
    assert reflect._ucb_rank(cands, hyps) == reflect._ucb_rank(cands, hyps)   # same ledger -> same order


def test_explore_proposal_is_single_variable_and_in_bounds():
    p = reflect.propose_deterministic(explore=True)
    assert p["variable"] and p["new"] is not None
    base = p["variable"].split("@", 1)[0]
    b = config.bounds()[base]
    assert b["min"] <= p["new"] <= b["max"]         # still a valid single-variable move


# ---------------- regime-conditional params ----------------
def test_resolve_params_overlays_only_named_regime():
    base = {"entry.min_score": 60, "stop_loss_atr_mult": 2.0}
    by = {"chop": {"entry.min_score": 70}, "trend_up": {"stop_loss_atr_mult": 2.5}}
    assert config.resolve_params(base, by, "chop")["entry.min_score"] == 70
    assert config.resolve_params(base, by, "chop")["stop_loss_atr_mult"] == 2.0   # untouched
    assert config.resolve_params(base, by, "trend_up")["entry.min_score"] == 60   # other regime
    assert config.resolve_params(base, None, "chop") == base                      # no overrides -> identity


def test_resolve_params_ignores_unknown_base_key():
    base = {"entry.min_score": 60}
    by = {"chop": {"not_a_real_param": 999}}          # can retune existing knobs only, never invent one
    assert config.resolve_params(base, by, "chop") == base


def test_guard_accepts_regime_knob_and_rejects_bad_regime():
    bounds, goal, params = config.bounds(), config.goal(), config.default_strategy()["params"]
    ok = guard.validate_change({"variable": "entry.min_score@chop", "new": params["entry.min_score"] + 1},
                               params, bounds, goal, [], 0)
    assert ok.ok and ok.variable == "entry.min_score@chop"
    bad = guard.validate_change({"variable": "entry.min_score@nonsense", "new": 61},
                                params, bounds, goal, [], 0)
    assert not bad.ok and "regime" in bad.reasons[0]
    # immutable base is still immutable even with a regime suffix
    imm = guard.validate_change({"variable": "max_open_positions@chop", "new": 4},
                                params, bounds, goal, [], 0)
    assert not imm.ok


def test_bump_routes_regime_knob_into_params_by_regime():
    current = config.default_strategy()
    child = versioning.bump(current, "entry.min_score@chop", 70, note="chop tighten")
    assert child["params"]["entry.min_score"] == current["params"]["entry.min_score"]  # flat untouched
    assert child["params_by_regime"]["chop"]["entry.min_score"] == 70                  # override written


# ---------------- Axis-2 skill attribution ----------------
def test_skill_attribution_ranks_worst_first(monkeypatch):
    from meridian import analytics
    trades = [{"r_multiple": 1.5, "skill_chain": ["good-skill", "shared"]},
              {"r_multiple": 1.0, "skill_chain": ["good-skill", "shared"]},
              {"r_multiple": -1.0, "skill_chain": ["bad-skill", "shared"]},
              {"r_multiple": -0.8, "skill_chain": ["bad-skill", "shared"]}]
    monkeypatch.setattr(analytics, "_trades", lambda: trades)
    attr = analytics.skill_attribution()
    assert attr["n_trades"] == 4
    assert attr["skills"][0]["skill"] == "bad-skill"          # worst avg_r surfaces first
    good = next(s for s in attr["skills"] if s["skill"] == "good-skill")
    assert good["avg_r"] == pytest.approx(1.25) and good["win_rate"] == 1.0
    shared = next(s for s in attr["skills"] if s["skill"] == "shared")
    assert shared["n"] == 4                                   # counted once per trade, across all 4
