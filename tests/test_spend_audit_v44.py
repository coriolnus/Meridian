"""test_spend_audit_v44.py — spend denetimi (2026-07-21, tur 31).

Bütçe muhafızı: dolunca LLM katmanı kapanır ve motor deterministik yola düşer. 7. soru:
  SP1 "maliyet çağrılan modele göre hesaplanır" → HAYIR: tek bir global fiyat vardı ve `record()`
     model adını YOK SAYIYORDU. Ücretsiz katmandaki Gemini / yerel Nous çağrıları Opus listesiyle
     ($15/$75 per M) fiyatlanıyor, HARCANMAMIŞ para bütçeyi doldurup beyni sessizce kapatabiliyordu.
  SP2 "defter saatleri karşılaştırılabilir" → spend YEREL saatti, sistemin geri kalanı UTC
  SP3 "bütçe sıfır/negatifse kapı kapanmaz" → kapatma yalnız gerçek bir tavanla olur
"""
from __future__ import annotations

import datetime as dt

import pytest

from meridian import spend, store


# ---------- SP1: model başına fiyat ----------
def test_sp1_free_tier_calls_do_not_consume_the_budget(sandbox_state):
    spend.record(500_000, 200_000, "gemini-3.1-pro", note="reflect (gemini)")
    spend.record(500_000, 200_000, "Hermes-4-405B", note="reflect (nous)")
    assert spend.month_spend() == 0.0, "ücretsiz sağlayıcı çağrıları bütçe yiyor"
    assert spend.over_budget() is False


def test_sp1b_paid_models_are_priced_by_family(sandbox_state):
    opus = spend.estimate_cost(1_000_000, 1_000_000, "claude-opus-4-8")
    sonnet = spend.estimate_cost(1_000_000, 1_000_000, "claude-sonnet-5")
    haiku = spend.estimate_cost(1_000_000, 1_000_000, "claude-haiku-4-5")
    assert opus > sonnet > haiku > 0


def test_sp1c_unknown_model_falls_back_to_the_conservative_default(sandbox_state):
    unknown = spend.estimate_cost(1_000_000, 0, "bilinmeyen-model-x")
    assert unknown == pytest.approx(spend.PRICE_IN_PER_M)      # muhafazakâr: eski davranış


def test_sp1d_row_carries_the_model_and_its_own_cost(sandbox_state):
    row = spend.record(1000, 1000, "claude-opus-4-8", note="reflect")
    assert row["model"] == "claude-opus-4-8" and row["cost_usd"] > 0
    assert store.read_jsonl("spend.jsonl")[-1]["cost_usd"] == row["cost_usd"]


# ---------- SP2: saat dilimi ----------
def test_sp2_ledger_timestamps_are_utc(sandbox_state):
    row = spend.record(10, 10, "claude-opus-4-8")
    assert row["ts"].endswith("+00:00"), "spend defteri yerel saatte — olay defteriyle kıyaslanamaz"
    assert row["ts"][:7] == dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")


def test_sp2b_month_grouping_uses_the_row_stamp(sandbox_state):
    spend.record(1_000_000, 0, "claude-opus-4-8", ts="2026-05-01T00:00:00+00:00")
    spend.record(1_000_000, 0, "claude-opus-4-8", ts="2026-06-01T00:00:00+00:00")
    assert spend.month_spend("2026-05") == pytest.approx(spend.PRICE_IN_PER_M)
    assert spend.month_spend("2026-06") == pytest.approx(spend.PRICE_IN_PER_M)
    assert spend.month_spend("2026-07") == 0.0


# ---------- SP3: bütçe kapısı ----------
def test_sp3_budget_gate_opens_and_closes_honestly(sandbox_state):
    assert spend.over_budget(budget=10.0) is False
    spend.record(1_000_000, 0, "claude-opus-4-8")             # ~$15
    assert spend.over_budget(budget=10.0) is True
    assert spend.over_budget(budget=0.0) is False             # tavan yok → kapı yok


def test_sp3b_summary_is_internally_consistent(sandbox_state):
    spend.record(200_000, 100_000, "claude-opus-4-8")
    s = spend.summary()
    assert s["spent_usd"] == spend.month_spend()
    assert s["remaining_usd"] == pytest.approx(max(0.0, s["budget_usd"] - s["spent_usd"]))
    assert s["calls_this_month"] == 1
    assert s["over_budget"] == (s["budget_usd"] > 0 and s["spent_usd"] >= s["budget_usd"])


def test_sp3c_hermes_checks_the_budget_before_paying():
    import inspect
    from meridian import hermes
    src = inspect.getsource(hermes.propose_with_claude) + inspect.getsource(hermes.propose_with_llm)
    assert "over_budget()" in src, "ücretli çağrıdan ÖNCE bütçe kontrolü yok"
