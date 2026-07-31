"""Batch I — foundation: cache-merge integrity (#31), the symmetric outcome/rollback loop (#1/#24),
survivorship-fixed universe (#32), and the honest breaker-count ladder criterion (#5)."""
import pandas as pd
import pytest

from meridian import config, store, versioning, memory, rollback


# ---------------- #31 cache merge keeps the FRESH bar ----------------
def test_cache_merge_fresh_bar_overrides_stale(sandbox_state, monkeypatch):
    from meridian.adapters import data
    from meridian import config as _cfg
    _cfg.BARS.mkdir(parents=True, exist_ok=True)   # izolasyon düzeltmesi: data.BARS anlık görüntüsü kaldırıldı — artık sandbox'a yazar
    cp = data._cache_path("ZZZ")
    # stale cache: a WRONG (pre-split) close on 2024-06-03, plus an old last bar so freshness fails
    pd.DataFrame({"date": pd.to_datetime(["2024-06-03", "2024-06-04"]),
                  "open": [98, 98], "high": [101, 101], "low": [97, 97],
                  "close": [100, 100], "volume": [1e6, 1e6]}).to_csv(cp, index=False)

    def fake_fetch(t, s, e, **_):   # a retroactive split-adjustment corrects 2024-06-03 to 50
        return pd.DataFrame({"date": pd.to_datetime(["2024-06-03", "2024-06-05"]),
                             "open": [49, 10], "high": [51, 11], "low": [48, 9],
                             "close": [50, 25], "volume": [2e6, 1e6]})
    monkeypatch.setattr(data, "fetch", fake_fetch)

    out = data.load_bars("ZZZ", "2024-06-01", "2024-06-30", use_cache=True)
    row = out[out["date"] == pd.Timestamp("2024-06-03")]
    assert float(row["close"].iloc[0]) == 50.0        # fresh corrected bar won, not stale 100


# ---------------- #32 survivorship-fixed universe integrity ----------------
def test_universe_widened_and_fully_sectored():
    from meridian.adapters import data
    from meridian.backtest import SECTORS
    assert len(data.REPLAY_UNIVERSE) >= 50            # laggards added
    assert {"INTC", "PYPL", "PFE", "MRNA"} <= set(data.REPLAY_UNIVERSE)
    missing = [t for t in data.REPLAY_UNIVERSE if t not in SECTORS]
    assert not missing, f"tickers missing a sector: {missing}"


# ---------------- #1/#24 symmetric outcome loop ----------------
def _goal():
    return {"schema_version": 1, "universe": "T", "style": "swing_momentum", "session_tz": "America/New_York",
            "target_return_30d": 0.07, "min_sharpe": 1.2, "max_drawdown": 0.08, "failure_below": -0.04,
            "reflection_every": 5, "min_sample": 3, "one_variable_only": True, "backtest_gate": True,
            "rollback_if_worse_by": 0.10, "explore_rate": 0.15, "max_accepted_changes_per_month": 8,
            "commission_per_share": 0.0, "slippage_bps": 5, "fill": "next_bar_open",
            "limits": {"autonomy_level": 0, "max_position_r": 1.0, "max_open_positions": 5,
                       "max_daily_loss_pct": 3.0, "max_sector_exposure_pct": 40.0,
                       "no_trade_before_bars": 3, "kill_switch_file": "state/HALT"}}


def _seed_versions(sandbox, v2_r, v1_r):
    config.dump_yaml(_goal(), sandbox / "goal.yaml"); config.goal.cache_clear()
    v1 = {"version": 1, "parent": None, "params": {"entry.min_score": 60}}
    v2 = {"version": 2, "parent": 1, "params": {"entry.min_score": 65}}
    versioning.snapshot(v1); versioning.snapshot(v2)
    config.dump_yaml(v2, config.strategy_path())
    for i in range(4):
        store.append_jsonl("trades.jsonl", {"strategy_version": 1, "r_multiple": v1_r, "pnl_dollars": v1_r * 1000,
                                            "ts_open": f"2024-01-0{i+1}", "ts_close": f"2024-02-0{i+1}"})
    for i in range(4):
        store.append_jsonl("trades.jsonl", {"strategy_version": 2, "r_multiple": v2_r, "pnl_dollars": v2_r * 1000,
                                            "ts_open": f"2024-03-0{i+1}", "ts_close": f"2024-04-0{i+1}"})
    memory.record({"variable": "entry.min_score", "old": 60, "new": 65, "version_to": 2,
                   "status": "live", "predicted_delta": 0.05})


def test_evaluate_outcomes_promotes_a_winner(sandbox_state):
    _seed_versions(sandbox_state, v2_r=0.9, v1_r=-0.5)     # v2 clearly beats v1
    res = rollback.evaluate_outcomes(config.goal())
    assert res and res["promoted"] is True and res["rolled_back"] is False
    h = [x for x in memory.all_hypotheses() if x.get("version_to") == 2][0]
    assert h["status"] == "promoted"
    assert h.get("realized_delta") is not None and h["realized_delta"] > 0
    assert h.get("calibration_hit") is True                # predicted +, realized + → hit
    assert int(config.load_strategy()["version"]) == 2     # NOT reverted


def test_evaluate_outcomes_rolls_back_a_loser(sandbox_state):
    _seed_versions(sandbox_state, v2_r=-0.9, v1_r=0.8)     # v2 clearly worse than v1
    res = rollback.evaluate_outcomes(config.goal())
    assert res and res.get("rolled_back_from") == 2        # routed to check_and_rollback
    assert int(config.load_strategy()["version"]) == 1     # reverted to parent
    assert any(h["status"] == "rolled_back" for h in memory.all_hypotheses())


# ---------------- #5 ladder counts REAL breaker trips ----------------
def test_ladder_breaker_criterion_is_real(sandbox_state):
    from meridian import obs, analytics
    config.dump_yaml(_goal(), sandbox_state / "goal.yaml"); config.goal.cache_clear()
    lad = analytics.autonomy_ladder(config.goal())
    breaker_crit = [c for c in lad["l0_to_l1"] if "breaker" in c["label"].lower()][0]
    assert breaker_crit["met"] is True and "0 observed" in breaker_crit["detail"]   # none yet
    obs.alarm(obs.ALARM_CIRCUIT_BREAKER, "test breaker trip", day_pnl_pct=-0.03)
    lad2 = analytics.autonomy_ladder(config.goal())
    breaker_crit2 = [c for c in lad2["l0_to_l1"] if "breaker" in c["label"].lower()][0]
    assert breaker_crit2["met"] is False                   # a real trip flips the criterion
