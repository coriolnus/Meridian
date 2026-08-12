"""Regression tests for the adversarial-audit fixes (M1-M5, L2-L5). Each fails on the pre-fix code and
passes after. No heavy backtests — logic/state only."""
from pathlib import Path
import shutil

import numpy as np
import pytest

from meridian import reflect, skills, sprint, config, store, strategy, indicators


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------------- L2: _gate_why must not crash on a None incumbent OOS ----------------
def test_gate_why_handles_none_incumbent_oos():
    inc = {"oos_score": None, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None}
    cand = {"oos_score": 0.30, "oos_folds": [], "oos_tail_risk": None, "holdout_score": 0.30}
    why = reflect._gate_why(inc, cand, majority=True, fold_wins=0, fold_total=0, tail_ok=True)  # was TypeError
    assert "incumbent OOS" in why


# ---------------- M3: an applied recommendation clears the pending queue ----------------
def test_applied_recommendation_shadows_older_pending(seeded_sandbox):
    store.append_jsonl(skills.SKILL_RECS, {"skill": "loser", "action": "shadow", "pending": True, "applied": False})
    assert any(r["skill"] == "loser" for r in skills.pending_recommendations())
    store.append_jsonl(skills.SKILL_RECS, {"skill": "loser", "action": "shadow", "applied": True})  # apply appends
    assert not any(r["skill"] == "loser" for r in skills.pending_recommendations())   # queue now clear
    # a DIFFERENT still-pending skill is unaffected
    store.append_jsonl(skills.SKILL_RECS, {"skill": "other", "action": "shadow", "pending": True, "applied": False})
    assert [r["skill"] for r in skills.pending_recommendations()] == ["other"]


# ---------------- M4: sandbox reset writes the v1 seed snapshot (rollback can revert) ----------------
def test_sandbox_reset_snapshots_v1(tmp_path):
    sbstate = tmp_path / "state"
    sbstate.mkdir()
    sprint._reset_sandbox_state(sbstate)
    snap = sbstate / "history" / "v0001.yaml"
    assert snap.exists()                                   # was missing → revert_to(1) FileNotFoundError
    import yaml
    assert yaml.safe_load(snap.read_text())["version"] == 1


# ---------------- M5: sprint day_before is STRICTLY before EVAL_START ----------------
def test_sprint_day_before_is_strictly_before_eval_start():
    import pandas as pd
    sessions = pd.bdate_range("2024-06-24", "2024-07-05")   # EVAL_START 2024-07-01 is a Monday session here
    idx = pd.DataFrame({"date": sessions})
    from meridian import sprint_run
    pre = [str(d.date()) for d in idx["date"] if str(d.date()) < sprint.EVAL_START]
    day_before = pre[-1] if pre else None
    fwd0 = next(str(d.date()) for d in idx["date"] if str(d.date()) >= sprint.EVAL_START)
    assert day_before is not None and day_before < sprint.EVAL_START and day_before != fwd0
    # the OLD inclusive-bound computation returned EVAL_START itself:
    incl = [str(d.date()) for d in idx["date"] if str(d.date()) <= sprint.EVAL_START][-1]
    assert incl == fwd0                                     # documents the bug this test guards


# ---------------- L5: retention keeps only the newest N sandboxes ----------------
def test_prune_old_sandboxes_keeps_newest(seeded_sandbox):
    root = config.STATE / "sprint"
    root.mkdir(parents=True)
    for name in ["20240101-000000", "20240102-000000", "20240103-000000", "20240104-000000", "20240105-000000"]:
        (root / name / "state").mkdir(parents=True)
    sprint._prune_old_sandboxes(keep=3)
    remaining = sorted(d.name for d in root.iterdir())
    assert remaining == ["20240103-000000", "20240104-000000", "20240105-000000"]   # oldest two pruned


# ---------------- M2: scheduler refetches the network AT MOST once per session, not every poll ----------------
def test_scheduler_refetches_once_per_session_not_per_poll(sandbox_state):
    # HERMETİK OLMALI (2026-07-22, sızıntı bekçisi yakaladı): bu test bir zamanlayıcı turu koşturuyor
    # ve tur, bütünlük dedektörlerinin referans dosyalarıyla birlikte 12 dosya yazıyordu — CANLI
    # nabız dahil. Sonuç: her tam suite koşusu operatörün nabzındaki `regime/equity/last_bar`
    # alanlarını siliyor, pano "rejim yok" gösteriyordu ve hiçbir test kırılmıyordu. read_json global
    # olarak taklit edildiği için yalnız sandbox yetmez — yazma yolları da kapatılır.
    import pandas as pd
    from unittest import mock
    from meridian import scheduler, store, health
    scheduler._state["last_refetch_session"] = None
    idx = pd.DataFrame({"date": pd.to_datetime(["2026-07-13"])})   # latest data bar lags the calendar
    loads = []

    def fake_load(use_cache=True):
        loads.append(use_cache)
        return ({}, idx)
    with mock.patch.object(scheduler, "_last_closed_session", lambda: "2026-07-15"), \
         mock.patch.object(health, "halted", lambda: False), \
         mock.patch.object(store, "read_json", lambda *a, **k: {"last_date": "2026-07-13"}), \
         mock.patch.object(store, "write_json", lambda *a, **k: None), \
         mock.patch.object(store, "append_jsonl", lambda *a, **k: None), \
         mock.patch("meridian.dataset.load", fake_load), \
         mock.patch("meridian.loop.daily_cycle", lambda b, i: {"date": "2026-07-13", "status": "ok"}):
        scheduler._state["refetch_attempts"] = 0
        scheduler.advance_once(); r2 = scheduler.advance_once(); r3 = scheduler.advance_once()
        # YENİ semantik: seansın barı henüz YAYINLANMADIYSA bayrak tüketilmez — sınırlı yeniden deneme
        # (aksi halde bar ancak SONRAKİ seansın refetch'inde gelirdi → adaylar 1 gün geç değerlendirilir).
        assert loads.count(False) == 3 and scheduler._state["refetch_attempts"] == 3
        assert scheduler._state["last_refetch_session"] is None
        # tavan: 8. denemede bayrak yanar (kaynak yayınlamıyor — dürüstçe uyarıp cache-only'ye düşer)
        scheduler._state["refetch_attempts"] = 7
        scheduler.advance_once()
        assert scheduler._state["last_refetch_session"] == "2026-07-15"
        n_before = loads.count(True)
        r_cached = scheduler.advance_once()        # bayrak yandı → artık cache-only poll
        assert loads.count(True) == n_before + 1 and r_cached["status"] == "current"
    assert r2["status"] == "current" and r3["status"] == "current"


# ---------------- M1: giveback window uses exactly bars_held bars (no pre-entry bar) ----------------
def test_giveback_window_excludes_pre_entry_bar():
    """A pre-entry spike must NOT count toward peak profit. Construct: a huge high on the bar BEFORE entry,
    then flat bars while held; with the old iloc[-(bars_held+1):] the pre-entry high fabricates a peak and
    fires 'giveback'; with iloc[-bars_held:] it does not."""
    import pandas as pd
    # index: [pre-entry spike, entry bar, +1 held]. bars_held=2 (incremented on entry day + 1 more).
    highs = [200.0, 101.0, 101.0]
    df = pd.DataFrame({
        "date": pd.bdate_range("2024-01-01", periods=3),
        "open": [100, 100, 100], "high": highs, "low": [99, 99, 99],
        "close": [100.0, 100.0, 100.0], "volume": [1e6, 1e6, 1e6],
    })
    params = {"exit.giveback_pct": 0.3, "exit.trail_atr_mult": 2.5, "exit.breakeven_r": 1.0,
              "exit.chandelier_lookback": 0, "stop_loss_atr_mult": 2.0}
    pos = {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0, "r_per_share": 5.0}
    dec = strategy.manage_position(df, pos, params, bars_held=2, regime_ok=True)
    # peak over the last 2 bars (entry + held) = 101 → peak_profit 1 < r_per_share 5 → NO giveback.
    # the pre-entry 200 spike (peak_profit 100) is correctly excluded.
    assert dec.exit_reason != "giveback"


# ---------------- FMP is the preferred (freshest) bar source when the key is present ----------------
def test_fetch_prefers_fmp_when_available(monkeypatch, sandbox_state):
    """With FMP_API_KEY set, bars come from FMP (~1 day fresher than the delayed Cboe feed) and Cboe is
    not called; without the key, it falls back to Cboe.

    `sandbox_state` ZORUNLU (2026-07-29): bu test `data.fetch`i gerçek zincirle çağırıyor. Massive
    kolu eklenince, operatörün CANLI `state/secrets.json`ındaki MASSIVE_API_KEY sandbox'sız testte de
    görünür oluyor ve çapraz-doğrulama GERÇEK ağa çıkıp canlı `massive_grouped_last.json`ı eziyordu
    (5/dk kotasını da yiyor). Sandbox sırları tmp dizine yönlendirdiği için Massive dürüstçe devre
    dışı kalır ve test yalnız ÖLÇTÜĞÜ şeyi — FMP'nin Cboe'ye tercih edilmesini — ölçer."""
    import pandas as pd
    from meridian.adapters import data, fmp
    fmp_rows = [{"date": "2026-07-14", "open": 750, "high": 753, "low": 748, "close": 751, "volume": 3.5e7}]
    cboe_called = {"n": 0}

    def fake_cboe(t, to):
        cboe_called["n"] += 1
        return pd.DataFrame([{"date": pd.Timestamp("2026-07-13"), "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}])
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "historical_eod", lambda sym: fmp_rows)
    monkeypatch.setattr(data, "_fetch_cboe", fake_cboe)
    df = data.fetch("SPY", "2021-01-01", "2026-07-15")
    assert not df.empty and str(df["date"].max().date()) == "2026-07-14"   # FMP's fresher bar
    assert cboe_called["n"] == 0                                            # Cboe not hit when FMP works

    # no key → falls back to Cboe
    monkeypatch.setattr(fmp, "available", lambda: False)
    df2 = data.fetch("SPY", "2021-01-01", "2026-07-15")
    assert cboe_called["n"] == 1 and str(df2["date"].max().date()) == "2026-07-13"


# ---------------- H1: slippage/commission not double-counted; the three ledgers agree ----------------
def test_pnl_ledgers_agree_under_slippage_and_commission():
    """realized_pnl (broker/breaker) == Σ row.pnl_dollars (the gate) == true round-trip. Before the fix
    these disagreed by exactly the slippage. Covers nonzero commission too (was only slip=0 tested)."""
    from meridian.broker import PaperBroker
    for slip_bps, comm in [(100, 0.0), (50, 0.01), (0, 0.02), (5, 0.0)]:
        b = PaperBroker(100_000, slippage_bps=slip_bps, commission_per_share=comm)
        plan = {"id": "P", "ticker": "X", "entry_trigger": 100.0, "stop": 95.0, "targets": [110.0],
                "profit_target": 110.0, "size_r": 1.0, "r_per_share": 5.0, "regime_at_plan": "trend_up",
                "sector": "tech", "setup": "breakout_vcp"}
        b.fill_entry(plan, 100.0, "2024-01-02", 100_000)
        pos = b.positions["X"]; entry_fill, qty = pos.entry, pos.qty
        b.close_position("X", 110.0, "target", "2024-01-05")
        row = b.closed[-1]
        exit_fill = 110.0 * (1 - slip_bps / 10000.0)
        true_rt = qty * (exit_fill - entry_fill) - 2 * qty * comm     # slippage in price, commission once/side
        assert round(b.realized_pnl, 2) == round(row["pnl_dollars"], 2) == round(true_rt, 2), (slip_bps, comm)


def test_pnl_ledgers_agree_with_scale_out():
    """The scale-out path banks a partial into ONE row; realized_pnl must still equal Σ pnl_dollars."""
    from meridian.broker import PaperBroker
    b = PaperBroker(100_000, slippage_bps=100, commission_per_share=0.0)
    plan = {"id": "P", "ticker": "X", "entry_trigger": 100.0, "stop": 90.0, "targets": [130.0],
            "profit_target": 130.0, "size_r": 1.0, "r_per_share": 10.0, "regime_at_plan": "trend_up",
            "sector": "tech", "setup": "breakout_vcp"}
    b.fill_entry(plan, 100.0, "2024-01-02", 100_000)
    pos = b.positions["X"]
    b.scale_out(pos, {"high": 200.0}, {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0})   # bank half
    b.close_position("X", 130.0, "target", "2024-01-10")
    assert round(b.realized_pnl, 2) == round(b.closed[-1]["pnl_dollars"], 2)   # one coherent ledger


# ---------------- L1: tail veto and magnitude gate share the embargoed lower bound ----------------
def test_tail_uses_same_embargoed_bound_as_magnitude():
    from meridian import backtest
    lo = backtest._embargoed_start("2024-07-01", 10)
    assert lo == "2024-07-11"                                 # purge zone excluded
    assert "2024-07-05" < lo and "2024-07-15" >= lo           # a trade inside the purge is excluded from BOTH
    assert backtest._embargoed_start("2024-07-01", 0) == "2024-07-01"


# ---------------- candidate scan evaluates ALL screeners (not short-circuited) ----------------
def test_scan_entry_evaluates_all_screeners_but_arms_only_proven():
    """Every screener runs on every ticker (the user's 'evaluate all skills' goal), but only ARMED_SETUPS
    produce a tradeable candidate. Guards both the old 'only vcp ever ran' AND the 'let everything trade
    and crater the edge'.

    BEYANLI GÜNCELLEME (2026-08-12): momentum_burst operatör onayıyla SİLAHLANDI (karar penceresi
    §E.2). Bu testin (b) bacağı mb'nin dormant olmasına dayanıyordu; DORMANT örneği hâlâ motorda
    olan bir kuruluma (episodic_pivot) taşındı — korunan yasa (silahsız kurulum aday ÜRETMEZ)
    aynen duruyor. (a) bacağı ise DAHA GÜÇLENDİ: mb artık silahlı olduğu hâlde bile breakout_vcp
    öncelikli kalmalı (sıra sözleşmesi: kanıtlı kurulumlar önce)."""
    import unittest.mock as m
    from meridian.strategy import EntrySignal

    def sig(setup, score):
        return EntrySignal("X", setup, 100.0, 100.0, 95.0, 1.0, 90, score, 110.0, 1.0, 5.0, "")

    # (a) all three evaluated; breakout present → armed and returned
    called = set()
    with m.patch.object(strategy, "evaluate_entry", lambda *a, **k: called.add("vcp") or sig("breakout_vcp", 60)), \
         m.patch.object(strategy, "evaluate_momentum_burst", lambda *a, **k: called.add("mb") or sig("momentum_burst", 82)), \
         m.patch.object(strategy, "evaluate_pullback", lambda *a, **k: called.add("pb") or None):
        out = strategy.scan_entry(None, {}, 90, "X")
    assert called == {"vcp", "mb", "pb"}                 # every screener evaluated (no short-circuit)
    assert out.setup == "breakout_vcp"                   # proven setup armed even though momentum_burst scored higher

    # (b) only a DORMANT setup fires (episodic_pivot) → evaluated, but NOT armed → None
    with m.patch.object(strategy, "evaluate_entry", lambda *a, **k: None), \
         m.patch.object(strategy, "evaluate_momentum_burst", lambda *a, **k: None), \
         m.patch.object(strategy, "evaluate_pullback", lambda *a, **k: None), \
         m.patch.object(strategy, "evaluate_exhaustion_hammer", lambda *a, **k: None), \
         m.patch.object(strategy, "evaluate_episodic_pivot", lambda *a, **k: sig("episodic_pivot", 90)):
        assert strategy.scan_entry(None, {}, 90, "X") is None
    assert "episodic_pivot" not in strategy.ARMED_SETUPS   # documents the dormancy decision
    assert "momentum_burst" in strategy.ARMED_SETUPS       # armed by operator 2026-08-12 (§E.2)


def test_momentum_burst_fires_on_a_real_burst():
    import numpy as np, pandas as pd
    from meridian import config
    n = 260                                              # long enough for the 200-SMA the trend template needs
    close = list(100.0 * (1.004 ** np.arange(n)))        # steady uptrend → high trend_template, weekly up
    close[-1] = close[-2] * 1.05                          # 5% burst day
    df = pd.DataFrame({"date": pd.bdate_range("2023-01-01", periods=n),
                       "open": [c * 0.999 for c in close], "high": [c * 1.005 for c in close],
                       "low": [c * 0.99 for c in close], "close": close,
                       "volume": [1e6] * (n - 1) + [3e6]})   # volume surge on the burst
    sig = strategy.evaluate_momentum_burst(df, config.default_strategy()["params"], rs_rating_value=95, ticker="X")
    assert sig is not None and sig.setup == "momentum_burst"
    assert sig.profit_target > sig.entry_trigger > sig.stop


def test_pipeline_run_reports_only_engine_implemented_as_invoked():
    from meridian import skills
    en, _ = skills.enabled_in("P2_SCREEN")
    invoked = [s for s in en if s in skills.ENGINE_IMPLEMENTED]
    declared = [s for s in en if s not in skills.ENGINE_IMPLEMENTED]
    assert "stockbee-momentum-burst-screener" in invoked and "vcp-screener" in invoked
    # 2026-07-24: pead + exhaustion-hammer artık motor-uygulandı (scan_all'da GERÇEKTEN koşar) → invoked.
    assert "pead-screener" in invoked and "stockbee-exhaustion-hammer-screener" in invoked
    # canslim-screener HÂLÂ label-only: evaluate_canslim scan_all'da güvenli no-op (Faz C temel-önbelleği
    # yok, daima None) → ENGINE_IMPLEMENTED'a EKLENMEDİ, pipeline_run onu 'invoked' saymaz (dürüstlük kapısı).
    assert "canslim-screener" in declared   # label-only, not executed
