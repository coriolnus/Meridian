"""test_arming_audit_v22.py — arming denetimi (2026-07-21, tur 7).

7. soru:
  R1 "yalnız ÖLÇER, silahlandırmaz" → modülün MERKEZİ güvenlik iddiası docstring'de yazılıydı ama
     hiçbir yerde ZORLANMIYORDU; bir gün eklenecek tek satır (ARMED_SETUPS.append) canlı davranışı
     operatör onayı olmadan değiştirirdi
  R2 "ölçülemedi = reddedildi"      → CANLIDA: momentum_burst raporda 'gate_rejected' görünüyor ama
     gerekçe "candidate OOS undefined (below min_sample)" — yani ölçüm YAPILAMAMIŞTI. 'Denedik ve
     kaybetti' diye okunup kurulumu haksızca gömüyordu
"""
from __future__ import annotations

import inspect
import shutil
from pathlib import Path

import pytest

from meridian import arming, config, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml", "strategy.json"):
        if (repo / f).exists():
            shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------- R1: sahiplik — ölçen, silahlandırmaz ----------
def test_r1_arming_never_mutates_live_armed_set():
    src = inspect.getsource(arming)
    assert "ARMED_SETUPS.append" not in src and "ARMED_SETUPS +=" not in src
    assert "ARMED_SETUPS =" not in src.replace("strat.ARMED_SETUPS]", "")   # okuma serbest, YAZMA yok
    assert "save_strategy" not in src, "arming canlı stratejiyi yazamaz — silahlanma operatör kararı"


def test_r1b_evaluate_leaves_armed_setups_untouched(sandbox_state, monkeypatch):
    """UYUYAN ÖRNEK ADI DEĞİŞTİ (2026-08-12, BEYANLI): momentum_burst → episodic_pivot. mb o gün
    operatör onayıyla silahlandı (§E.2), yani `_dormant_setups()` onu artık döndürmüyor ve
    `evaluate` onu ölçmüyor. Ölçülen YASA aynı: kapı GEÇSE bile canlı silahlı küme değişmez."""
    from meridian import strategy
    before = list(strategy.ARMED_SETUPS)
    monkeypatch.setattr(arming, "setup_report", lambda: {"episodic_pivot": {"n": 999, "avg_r": 1.0,
                                                                            "win_rate": 0.6, "regimes": {}}})
    monkeypatch.setattr(arming, "_measure", lambda s, b, i: {"status": "gate_passed", "search_p": 0.99})
    out = arming.evaluate(bars={}, index=None)
    assert out["measurements"]["episodic_pivot"]["status"] == "gate_passed"
    assert list(strategy.ARMED_SETUPS) == before, "kapı geçse BİLE canlı set değişemez"


def test_r1c_gate_pass_only_alarms(sandbox_state, monkeypatch):
    monkeypatch.setattr(arming, "setup_report", lambda: {"episodic_pivot": {"n": 999, "avg_r": 1.0,
                                                                            "win_rate": 0.6, "regimes": {}}})
    monkeypatch.setattr(arming, "_measure", lambda s, b, i: {"status": "gate_passed", "search_p": 0.99})
    arming.evaluate(bars={}, index=None)
    ev = [e for e in store.read_jsonl("events.jsonl")
          if e.get("event") == "alarm" or "ARMING_READY" in str(e)]
    assert ev, "operatöre haber verilmeli — ama karar insanda"


# ---------- R2: ölçülemedi ≠ reddedildi ----------
def test_r2_undefined_measurement_is_not_a_rejection(seeded, monkeypatch):
    from meridian import reflect, dataset, config
    monkeypatch.setattr(dataset, "load", lambda **k: ({}, None))
    monkeypatch.setattr(reflect, "_default_windows", lambda: ("a", "b", "c", "d", [], 10))
    monkeypatch.setattr(reflect, "_wf_cached", lambda *a, **k: {"oos_score": None})
    monkeypatch.setattr(reflect.backtest, "walk_forward", lambda *a, **k: {"oos_score": None})
    monkeypatch.setattr(reflect, "_gate_eval",
                        lambda inc, cand, k_probes=1: (False, {"search_p": None, "incumbent_oos": None,
                                                               "candidate_oos": None, "fold_wins": "0/0"},
                                                       "candidate OOS score undefined (below min_sample)"))
    res = arming._measure("momentum_burst", bars={}, index=None)
    assert res["status"] == "gate_undefined"                  # 'denedik ve kaybetti' DEĞİL
    assert "undefined" in (res["why"] or "")


def test_r2b_real_rejection_still_says_rejected(seeded, monkeypatch):
    from meridian import reflect, dataset
    monkeypatch.setattr(dataset, "load", lambda **k: ({}, None))
    monkeypatch.setattr(reflect, "_default_windows", lambda: ("a", "b", "c", "d", [], 10))
    monkeypatch.setattr(reflect, "_wf_cached", lambda *a, **k: {"oos_score": 0.2})
    monkeypatch.setattr(reflect.backtest, "walk_forward", lambda *a, **k: {"oos_score": 0.1})
    monkeypatch.setattr(reflect, "_gate_eval",
                        lambda inc, cand, k_probes=1: (False, {"search_p": 0.41, "incumbent_oos": 0.2,
                                                               "candidate_oos": 0.1, "fold_wins": "1/3"},
                                                       "P below required"))
    assert arming._measure("momentum_burst", bars={}, index=None)["status"] == "gate_rejected"


# ---------- korunum: her uyuyan kurulum kayıtlı bir terminale ulaşır ----------
def test_conservation_every_dormant_setup_has_a_status(sandbox_state, monkeypatch):
    monkeypatch.setattr(arming, "setup_report", lambda: {})
    out = arming.evaluate(bars={}, index=None)
    for s in arming._dormant_setups():
        assert s in out["measurements"] and out["measurements"][s].get("status")
