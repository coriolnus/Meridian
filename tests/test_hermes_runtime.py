"""Hermes in-process supervisor — status, on-demand reflection, and the single-reflection lock. The
real reflect_once (which runs walk-forwards) is mocked so these stay fast and data-free."""
import shutil
from pathlib import Path

import pytest

from meridian import hermes_runtime, secrets, config


def _seed_goal(sandbox):
    real = Path(config.__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy(real / f, sandbox / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()


def test_brain_is_deterministic_without_key(sandbox_state, monkeypatch):
    _seed_goal(sandbox_state)
    secrets.clear_cache()
    from meridian import hermes
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)   # makinede kurulu yerel ajan testi etkilemesin
    st = hermes_runtime.status()
    assert st["brain"] == "deterministic"       # no HERMES/ANTHROPIC key present
    assert st["active"] is False                 # thread not started


def test_brain_is_claude_with_key(sandbox_state, monkeypatch):
    _seed_goal(sandbox_state)
    monkeypatch.setenv("HERMES_API_KEY", "sk-ant-xxx")
    secrets.clear_cache()
    assert hermes_runtime.status()["brain"] == "claude"


def test_reflect_now_runs_and_records(sandbox_state, monkeypatch):
    _seed_goal(sandbox_state)
    calls = {"n": 0}

    def fake_reflect_once():
        calls["n"] += 1
        return {"status": "rejected_by_backtest", "hypothesis": {"variable": "entry.min_score"}}

    from meridian import hermes
    monkeypatch.setattr(hermes, "reflect_once", fake_reflect_once)
    res = hermes_runtime.reflect_now()
    assert res["status"] == "started"       # async contract: returns immediately, search runs in a thread
    # the reflection runs in a background daemon thread — wait for it to land
    import time
    for _ in range(60):
        if calls["n"] == 1 and not hermes_runtime._reflect_lock.locked():
            break
        time.sleep(0.05)
    assert calls["n"] == 1
    st = hermes_runtime.status()
    assert st["last_result"] == "rejected_by_backtest" and st["last_variable"] == "entry.min_score"


def test_reflect_now_refuses_when_locked(sandbox_state, monkeypatch):
    _seed_goal(sandbox_state)
    hermes_runtime._reflect_lock.acquire()      # simulate a reflection already in progress
    try:
        assert hermes_runtime.reflect_now()["status"] == "busy"
    finally:
        hermes_runtime._reflect_lock.release()
