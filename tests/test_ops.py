"""Batch H — operability: the Hermes spend ledger + monthly budget guard that keeps a self-improving
agent from silently running up an LLM bill (it falls back to the free deterministic proposer)."""
import pytest

from meridian import spend


def test_estimate_cost():
    # 10k input @ $15/M + 2k output @ $75/M = 0.15 + 0.15 = 0.30
    assert spend.estimate_cost(10_000, 2_000) == pytest.approx(0.30, abs=1e-4)


def test_spend_ledger_and_budget_guard(sandbox_state, monkeypatch):
    monkeypatch.setattr(spend, "MONTHLY_BUDGET_USD", 1.0)
    r = spend.record(10_000, 2_000, "claude-x", note="reflect", ts="2026-07-10T09:00:00")
    assert r["cost_usd"] == pytest.approx(0.30, abs=1e-4)
    assert spend.month_spend("2026-07") == pytest.approx(0.30, abs=1e-4)
    assert not spend.over_budget(month="2026-07")             # under the $1 cap

    spend.record(20_000, 8_000, "claude-x", ts="2026-07-11T09:00:00")   # +0.90 -> $1.20 total
    assert spend.over_budget(month="2026-07")                 # cap exhausted -> Hermes must fall back

    s = spend.summary("2026-07")
    assert s["calls_this_month"] == 2 and s["over_budget"] and s["remaining_usd"] == 0.0
    # a different month is unaffected by this month's spend
    assert spend.month_spend("2026-08") == 0.0
