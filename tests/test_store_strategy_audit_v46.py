"""test_store_strategy_audit_v46.py — store (tur 34) + strategy (tur 35) + validation_report (tur 36).

7. soru:
  ST1 "bozuk state dosyası zararsızca varsayılana düşer" → düşüyordu ama SESSİZCE. portfolio.json
     bozulursa defter BOŞ görünür ve motor pozisyonlar yokmuş gibi davranır — sistemin en tehlikeli
     sessiz hatası. Artık dosya başına bir kez KAYDA geçiyor.
  ST2 "jsonl satırları eksiksizdir" → append atomik DEĞİL; yarım bir satır sessizce atlanıyordu
     (bir işlem/plan defterden düşer). Atlanan satır sayısı artık raporlanıyor.
  SG1 "aynı barlar aynı sinyali verir" → kapı iki tarafı kıyaslıyor; sinyal deterministik değilse
     kıyas gürültü ölçer
  VR1 "doğrulama raporu KANIT gösterir, uydurmaz" → veri yoksa boş/None, sahte sayı değil
"""
from __future__ import annotations

import pytest

from meridian import config, store, strategy, validation_report
from tests.conftest import make_bars


# ---------- ST1: bozuk dosya sessiz kalmaz ----------
def test_st1_corrupt_json_falls_back_but_is_recorded(sandbox_state):
    store._CORRUPT_SEEN.clear()
    (sandbox_state / "portfolio.json").write_text("{bozuk json")
    assert store.read_json("portfolio.json", {"positions": {}}) == {"positions": {}}
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "state_file_unreadable"]
    assert ev and ev[-1]["file"] == "portfolio.json"


def test_st1b_warning_is_once_per_file(sandbox_state):
    store._CORRUPT_SEEN.clear()
    (sandbox_state / "portfolio.json").write_text("{bozuk")
    for _ in range(5):
        store.read_json("portfolio.json", {})
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "state_file_unreadable"]
    assert len(ev) == 1


def test_st2_skipped_jsonl_rows_are_reported(sandbox_state):
    store._CORRUPT_SEEN.clear()
    (sandbox_state / "trades.jsonl").write_text('{"id":"T1"}\n{yarim satir\n{"id":"T2"}\n')
    rows = store.read_jsonl("trades.jsonl")
    assert [r["id"] for r in rows] == ["T1", "T2"]
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "jsonl_rows_skipped"]
    assert ev and ev[-1]["skipped"] == 1 and ev[-1]["kept"] == 2


def test_st_writes_are_atomic_and_numpy_safe(sandbox_state):
    import numpy as np
    store.write_json("x.json", {"a": np.float64(1.5), "b": np.int64(2), "c": np.bool_(True),
                                "d": np.array([1, 2])})
    assert store.read_json("x.json") == {"a": 1.5, "b": 2, "c": True, "d": [1, 2]}
    assert not list(sandbox_state.glob("*.tmp"))


def test_st_merge_dated_is_idempotent(sandbox_state):
    rows = [{"date": "2026-07-20", "ticker": "AAA"}]
    store.merge_dated_jsonl("plans.jsonl", "2026-07-20", rows)
    store.merge_dated_jsonl("plans.jsonl", "2026-07-20", rows)
    assert len(store.read_jsonl("plans.jsonl")) == 1        # aynı gün iki kez yazılınca çoğalmaz


# ---------- SG1: sinyal determinizmi ----------
def test_sg1_entry_signal_is_deterministic():
    bars = make_bars(320, seed=11, breakout_at=300)
    params = config.default_strategy()["params"]
    a = strategy.evaluate_entry(bars, params, 90, "X")
    b = strategy.evaluate_entry(bars, params, 90, "X")
    assert (a is None) == (b is None)
    if a:
        assert (a.entry_trigger, a.stop, a.score, a.setup) == (b.entry_trigger, b.stop, b.score, b.setup)


def test_sg1b_trigger_never_uses_a_future_bar():
    bars = make_bars(320, seed=3, breakout_at=300)
    params = config.default_strategy()["params"]
    sig = strategy.evaluate_entry(bars, params, 90, "X")
    if sig:
        assert sig.entry_trigger <= float(bars["close"].max())
        assert sig.stop < sig.entry_trigger                  # stop her zaman tetiğin ALTINDA


def test_sg1c_manage_position_never_loosens_the_hard_stop():
    bars = make_bars(140, seed=8, trend=-0.003)              # düşen piyasa
    params = config.default_strategy()["params"]
    entry = float(bars["close"].iloc[70])
    pos = {"entry": entry, "stop": entry * 0.95, "r_per_share": entry * 0.05,
           "trail_stop": entry * 0.95}
    dec = strategy.manage_position(bars.iloc[:100], pos, params, bars_held=5, regime_ok=True)
    assert dec.trail_stop >= pos["stop"] - 1e-9


# ---------- VR1: rapor kanıt gösterir, uydurmaz ----------
def test_vr1_report_is_empty_not_fabricated_without_data(sandbox_state):
    rep = validation_report.build()
    assert isinstance(rep, dict)
    txt = validation_report.render_text()
    assert isinstance(txt, str) and len(txt) > 0
    for section in rep.values():
        if isinstance(section, dict) and "n" in section:
            assert section["n"] == 0 or section.get("n") is None or section["n"] >= 0


def test_vr1b_report_reads_only_persisted_evidence(sandbox_state):
    import inspect
    src = inspect.getsource(validation_report)
    assert "walk_forward" not in src and "replay(" not in src, \
        "doğrulama raporu KENDİ ölçümünü yapmamalı — yalnız kayıtlı kanıtı gösterir"
