"""test_hermes_runtime_audit_v29.py — hermes_runtime denetimi (2026-07-21, tur 14).

Bu modül AŞIRI-UYUM KAPISININ zamanlayıcısı: ne zaman düşünüleceğine karar verir. 7. soru:
  HR1 "ufuk koşulu tek yerde" → HAYIR: `_horizon_ok` (karar) ve `_horizon_progress(...)["ready"]`
     (panoya yazılan) AYNI koşulu İKİ kez hesaplıyor. Ayrışırlarsa pano "hazır" derken döngü
     reddeder (ya da tersi) — guard'daki iki-yüzey hatasının aynısı, burada da kimse kıyaslamıyordu.
  HR2 "aynı anda tek yansıma"  → kilit var, testi yoktu
  HR3 "yeniden başlatma takvim saatini sıfırlamaz" → livelock'a yol açan hata (audit); kilitlensin
  HR4 "arka plan rejimi CANLI rejimi hedeflemez"   → hedeflerse guardrail'in amacı çöker
"""
from __future__ import annotations

import datetime as dt
import itertools

import pytest

from meridian import hermes_runtime as hr, store


def _trades(n, span_days, regime="trend_up", start="2026-01-01"):
    d0 = dt.date.fromisoformat(start)
    if n <= 1:
        return [{"ts_close": start, "regime": regime}] * n
    step = span_days / (n - 1)
    return [{"ts_close": str(d0 + dt.timedelta(days=int(round(i * step)))), "regime": regime}
            for i in range(n)]


# ---------- HR1: karar ile panonun AYNI koşulu ----------
def test_hr1_decision_and_progress_never_disagree():
    """144 senaryo: _horizon_ok (karar) ile _horizon_progress.ready (pano) birebir aynı olmalı."""
    checked = 0
    for n, span, min_tr in itertools.product((0, 1, 2, 5, 12), (0, 5, 29, 30, 45), (1, 5, 10)):
        tr = _trades(n, span)
        ok = hr._horizon_ok(tr, 0, min_trades=min_tr)
        ready = hr._horizon_progress(tr, 0, None, min_tr)["ready"]
        assert ok == ready, f"ayrışma: n={n} span={span} min_trades={min_tr} → {ok} vs {ready}"
        checked += 1
    assert checked >= 60


def test_hr1b_calendar_floor_cannot_be_bypassed_by_count():
    """Aşırı-uyumun klasik yolu: 30 işlem 3 güne sıkışsın. Sayı yeter, TAKVİM yetmez → HAYIR."""
    clustered = _trades(30, span_days=3)
    assert hr._horizon_ok(clustered, 0, min_trades=5) is False
    spread = _trades(6, span_days=40)
    assert hr._horizon_ok(spread, 0, min_trades=5) is True


def test_hr1c_regime_slice_is_measured_within_the_regime():
    mixed = _trades(6, 40, regime="chop") + _trades(6, 40, regime="trend_up")
    assert hr._horizon_ok(mixed, 0, regime="chop", min_trades=5) is True
    assert hr._horizon_ok(mixed, 0, regime="high_vol", min_trades=5) is False   # o rejimde kanıt yok


# ---------- HR2: tek yansıma ----------
def test_hr2_second_reflection_is_refused_while_one_runs(sandbox_state, monkeypatch):
    hr._reflect_lock.acquire()
    try:
        out = hr.reflect_now()
        assert out["status"] == "busy"
    finally:
        hr._reflect_lock.release()


def test_hr2b_manual_trigger_reports_horizon_state_honestly(sandbox_state, monkeypatch):
    """Elle tetikleme ufku BİLEREK atlar — ama bunu gizlemez (dürüst durum bildirimi)."""
    monkeypatch.setattr(hr, "status", lambda: {"horizon": {"ready": False, "trades": 2,
                                                           "trades_needed": 5, "span_days": 3,
                                                           "min_days": 30}})
    monkeypatch.setattr(hr.threading, "Thread", lambda **k: type("T", (), {"start": lambda s: None})())
    out = hr.reflect_now()
    assert out["status"] == "started" and out["horizon_ready"] is False
    assert "ufuk kapısı" in out["detail"]


# ---------- HR3: taban geri sarmaz ----------
def test_hr3_baseline_is_restored_not_reset(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}"} for i in range(50)])
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": 12})
    assert hr._restored_baseline() == 12, "yeniden başlatma takvim saatini sıfırlarsa livelock"


def test_hr3b_baseline_clamped_to_a_reseeded_ledger(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": "T1"}])
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": 999})
    assert hr._restored_baseline() == 1


def test_hr3c_first_ever_run_does_not_reflect_on_the_backlog(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}"} for i in range(7)])
    assert hr._restored_baseline() == 7


# ---------- HR4: arka plan rejimi ----------
def test_hr4_background_regime_never_targets_the_live_one(sandbox_state, monkeypatch):
    monkeypatch.setitem(hr._state, "bg_reflect_by_regime", {})
    trades = _trades(8, 45, regime="chop") + _trades(8, 45, regime="trend_up")
    got = hr._bg_ready_regime(trades, every=5, live_reg="chop")
    assert got != "chop"                                        # canlı rejim arka planda hedeflenmez
    assert got in (None, "trend_up")


def test_hr4b_background_regime_needs_a_full_horizon(sandbox_state, monkeypatch):
    monkeypatch.setitem(hr._state, "bg_reflect_by_regime", {})
    clustered = _trades(20, 2, regime="chop")                   # sayı çok, takvim yok
    assert hr._bg_ready_regime(clustered, every=5, live_reg="trend_up") is None
