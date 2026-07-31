"""Axis-2 skill self-improvement — the catalog Hermes reasons with, attribution-driven recommendations,
the operator-gated apply, and the hard protection of the enforcement skills."""
import pytest

from meridian import skills, store, analytics


def _seed_reg(sandbox):
    reg = {"skills": {
        "vcp-screener": {"category": "swing", "fmp": "req", "alpaca": "-", "enabled": True,
                         "mode": "active", "style_active": True, "pipeline": "P2_SCREEN"},
        "pre-trade-discipline-gate": {"category": "meta", "fmp": "-", "alpaca": "-", "enabled": True,
                                      "mode": "active", "style_active": True, "pipeline": "P3_PLAN"},
        "loser-skill": {"category": "x", "fmp": "-", "alpaca": "-", "enabled": True,
                        "mode": "active", "style_active": True, "pipeline": "P2_SCREEN"},
    }}
    store.write_json("skills_registry.json", reg)


def _mock_attr(monkeypatch):
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": [
        {"skill": "loser-skill", "n": 12, "win_rate": 0.25, "avg_r": -0.4, "total_r": -4.8},
        {"skill": "vcp-screener", "n": 15, "win_rate": 0.6, "avg_r": 0.4, "total_r": 6.0},
        {"skill": "pre-trade-discipline-gate", "n": 20, "win_rate": 0.3, "avg_r": -0.5, "total_r": -10},
    ]})


def test_catalog_has_descriptions_and_protection(sandbox_state):
    _seed_reg(sandbox_state)
    cat = {c["name"]: c for c in skills.catalog()}
    assert cat["vcp-screener"]["description"]                    # real SKILL.md one-liner
    assert cat["pre-trade-discipline-gate"]["protected"] is True # enforcement skill is protected
    assert cat["loser-skill"]["protected"] is False


def test_apply_action_reversible_and_refuses_protected(sandbox_state):
    _seed_reg(sandbox_state)
    assert not skills.apply_skill_action("pre-trade-discipline-gate", "shadow")["ok"]   # protected
    assert not skills.apply_skill_action("nope", "shadow")["ok"]                        # unknown
    assert not skills.apply_skill_action("loser-skill", "delete")["ok"]                 # bad action
    r = skills.apply_skill_action("loser-skill", "shadow")
    assert r["ok"] and skills.registry()["skills"]["loser-skill"]["shadow"] is True
    skills.apply_skill_action("loser-skill", "activate")                                # reversible
    assert skills.registry()["skills"]["loser-skill"]["shadow"] is False


def test_recommendations_flag_loser_and_winner(sandbox_state, monkeypatch):
    _seed_reg(sandbox_state)
    _mock_attr(monkeypatch)
    recs = {r["skill"]: r for r in skills.recommend_from_attribution()}
    assert recs["loser-skill"]["action"] == "shadow"            # chronic negative -> shadow
    assert recs["vcp-screener"]["action"] == "lean_in"          # strong positive -> lean in
    assert "pre-trade-discipline-gate" not in recs              # protected, never recommended


def test_record_dedups_and_refuses_protected(sandbox_state):
    _seed_reg(sandbox_state)
    assert skills.record_recommendation({"skill": "loser-skill", "action": "shadow", "rationale": "x"})
    assert not skills.record_recommendation({"skill": "loser-skill", "action": "shadow", "rationale": "x"})  # dup
    assert not skills.record_recommendation({"skill": "pre-trade-discipline-gate", "action": "shadow", "rationale": "x"})
    pend = skills.pending_recommendations()
    assert [r["skill"] for r in pend] == ["loser-skill"]
