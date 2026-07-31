"""test_efficiency_v8.py — verimlilik/etkinlik katmanı (öneriler 1→5, 2026-07-20 akşam).

#1 cf tavanı 250-evrene göre (2500). #2 incumbent önbelleği diskte + bar-revizyonuyla düşer;
paralel havuz env kapalıyken KESİN no-op (testler/sandbox güvenliği). #3 silahlanma değerlendiricisi:
cf eşiği → kapı ölçümü → rapor; ARMED_SETUPS'a ASLA dokunmaz (operatör onayı). entry.armed_extra
yalnız param kanalı. #4 çıkış verimliliği muhasebesi + UCB'nin sınırlı exit.* dürtmesi. #5 kanıt
paketi prompt'a girer; boş state'te boş dize (uydurma yok)."""
import shutil
from pathlib import Path

import pandas as pd
import pytest

from meridian import config, store, analytics, reflect
from meridian import counterfactual as cf


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------------- #1 ----------------
def test_cf_cap_scaled_for_250_universe():
    assert cf.MAX_OPEN == 2500


# ---------------- #2 ----------------
def test_incumbent_cache_persists_and_rev_invalidates(seeded_sandbox, monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(reflect.backtest, "walk_forward",
                        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or {"oos_score": 0.2})
    w = ("2022-01-01", "2023-01-01", "2024-01-01", "2024-06-01", ["2023-06-01"], 5)
    reflect.clear_wf_caches(); calls["n"] = 0
    reflect._wf_cached({"stop_loss_atr_mult": 2.0}, 1, None, None, config.goal(), None, windows=w)
    reflect._wf_cached({"stop_loss_atr_mult": 2.0}, 1, None, None, config.goal(), None, windows=w)
    assert calls["n"] == 1
    reflect._INC_CACHE.clear(); reflect._INC_DISK_LOADED = False          # "yeniden başlatma"
    reflect._wf_cached({"stop_loss_atr_mult": 2.0}, 1, None, None, config.goal(), None, windows=w)
    assert calls["n"] == 1                                                # disk isabeti — incumbent bedava
    reflect.clear_wf_caches()                                             # bar revizyonu
    reflect._wf_cached({"stop_loss_atr_mult": 2.0}, 1, None, None, config.goal(), None, windows=w)
    assert calls["n"] == 2


def test_parallel_prefill_is_noop_without_env(seeded_sandbox, monkeypatch):
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    before = dict(reflect._PROBE_CACHE)
    cur = config.load_strategy()
    reflect._parallel_prefill_probes([("stop_loss_atr_mult", 2.1), ("stop_loss_atr_mult", 1.9)],
                                     cur, 1, config.goal(),
                                     ("2022-01-01", "2023-01-01", "2024-01-01", "2024-06-01", ["2023-06-01"], 5),
                                     None)
    assert reflect._PROBE_CACHE == before                                 # bayrak kapalı → kesin no-op


# ---------------- #3 ----------------
def _cf_row(setup, r, regime="chop"):
    return {"entered": True, "setup": setup, "r_multiple": r, "regime": regime,
            "mfe_r": max(r, 0) + 0.5, "mae_r": 0.3, "exit_reason": "target" if r > 0 else "stop"}


def test_setup_report_and_evaluate_flow(seeded_sandbox, monkeypatch):
    from meridian import arming, strategy as strat
    rows = [_cf_row("episodic_pivot", 0.6) for _ in range(35)] + [_cf_row("momentum_burst", -0.2) for _ in range(12)]
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: rows)
    rep = arming.setup_report()
    assert rep["episodic_pivot"]["n"] == 35 and rep["episodic_pivot"]["avg_r"] == 0.6
    # eşik: EP geçer (n≥30, R>0) → ölçüm koşar; burst geçmez (negatif R) → insufficient
    monkeypatch.setattr(arming, "_measure", lambda s2, b=None, i=None: {"status": "gate_passed", "search_p": 0.91})
    out = arming.evaluate(bars={}, index={})
    assert out["measurements"]["episodic_pivot"]["status"] == "gate_passed"
    assert out["measurements"]["momentum_burst"]["status"] == "insufficient_cf"
    assert store.read_json("arming_report.json", {})["measurements"]["episodic_pivot"]["search_p"] == 0.91
    assert "episodic_pivot" not in strat.ARMED_SETUPS                     # ölçüm SİLAHLAMAZ — operatör onayı


def test_armed_extra_param_channel_only(seeded_sandbox):
    """entry.armed_extra: ölçüm kanalı — param verilince uyuyan kurulum silahlanır, verilmeyince asla."""
    from meridian import strategy as strat, earnings
    import numpy as np
    rng = np.random.default_rng(3)
    df = pd.DataFrame({"date": pd.bdate_range("2026-02-02", periods=120)})
    close = 100 + rng.normal(0, 0.5, 120).cumsum() * 0.1
    df["open"] = close * 0.999; df["close"] = close
    df["high"] = close * 1.004; df["low"] = close * 0.996; df["volume"] = 1e6
    df.loc[df.index[-1], ["open", "close", "high", "volume"]] = [close[-2] * 1.08, close[-2] * 1.09,
                                                                 close[-2] * 1.10, 4e6]
    (seeded_sandbox / "earnings.csv").write_text(f"ticker,date\nTST,{str(df['date'].iloc[-1])[:10]}\n")
    earnings.clear_cache()
    assert strat.scan_all(df, {}, 80, "TST").get("episodic_pivot") is not None   # sinyal var
    assert strat.scan_entry(df, {}, 80, "TST") is None or \
           strat.scan_entry(df, {}, 80, "TST").setup in strat.ARMED_SETUPS      # paramsız: uyuyan silahsız
    sig = strat.scan_entry(df, {"entry.armed_extra": ["episodic_pivot"]}, 80, "TST")
    assert sig is not None and sig.setup == "episodic_pivot"                     # kanal: yalnız ölçümde


# ---------------- #4 ----------------
def test_exit_efficiency_and_ucb_nudge(seeded_sandbox, monkeypatch):
    trades = [{"exit_reason": "time_stop", "mfe_r": 1.4, "r_multiple": 0.1} for _ in range(8)]
    cfrows = [{"entered": True, "exit_reason": "stop", "mfe_r": 0.2, "r_multiple": -1.0} for _ in range(6)]
    monkeypatch.setattr(analytics, "_trades", lambda: trades)
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: cfrows)
    ee = analytics.exit_efficiency()
    assert ee["n"] == 14 and ee["worst_reason"] == "time_stop"
    assert ee["reasons"]["time_stop"]["left_r"] == pytest.approx(1.3)
    assert ee["nudge_active"] is True                                     # ort. masada-kalan > 0.5R
    hyps = [{"variable": "exit.trail_atr_mult", "status": "rejected_by_backtest"},
            {"variable": "entry.min_score", "status": "rejected_by_backtest"}]
    ranked = reflect._ucb_rank(["exit.trail_atr_mult", "entry.min_score"], hyps)
    assert ranked[0] == "exit.trail_atr_mult"                             # eşit defterde dürtme öne alır
    store.write_json("exit_efficiency.json", {"nudge_active": False})
    ranked2 = reflect._ucb_rank(["exit.trail_atr_mult", "entry.min_score"], hyps)
    assert ranked2[0] == "entry.min_score"                                # dürtme kapalı → alfabetik taban


def test_exit_efficiency_needs_min_sample(seeded_sandbox, monkeypatch):
    monkeypatch.setattr(analytics, "_trades", lambda: [])
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: [])
    assert analytics.exit_efficiency() is None                            # <10 → istatistik uydurulmaz


# ---------------- #5 ----------------
def test_evidence_pack_reads_reports_and_stays_honest(seeded_sandbox):
    from meridian import hermes
    assert hermes.evidence_pack() == ""                                   # boş state → boş paket
    store.write_json("score_calibration.json", {"rank_ic": 0.31, "n": 44, "monotone_hint": True})
    store.write_json("exit_efficiency.json", {"avg_left_r": 0.7, "worst_reason": "time_stop",
                                              "worst_left_r": 1.3, "nudge_active": True})
    pack = hermes.evidence_pack()
    assert "EVIDENCE PACK" in pack and '"rank_ic": 0.31' in pack and "time_stop" in pack
    assert pack in hermes._user_prompt()                                  # öneri prompt'una gerçekten giriyor
