"""Robustness & reconciliation patch — Phase 1 (broker/sim split-brain), Phase 2 (corporate-action cache
defense), Phase 3 (Hermes overfitting horizon). Alpaca is mocked (no live account); no heavy backtests."""
from pathlib import Path
import shutil

import pandas as pd
import pytest

from meridian import config, store


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ============ PHASE 1 — broker/simulator reconciliation ============
def test_exit_fill_price_extracts_the_filled_leg():
    from meridian.adapters import alpaca
    filled = {"legs": [{"status": "canceled", "filled_avg_price": None},
                       {"status": "filled", "filled_avg_price": "108.90"}]}
    assert alpaca.exit_fill_price(filled) == 108.9
    assert alpaca.exit_fill_price({"legs": [{"status": "new"}]}) is None
    assert alpaca.exit_fill_price(None) is None


def test_reconcile_strips_dead_orders_and_audits_divergence(seeded_sandbox, monkeypatch):
    from meridian import loop, obs
    from meridian.adapters import alpaca
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    orders = [
        {"client_order_id": "P-DEAD", "status": "rejected", "legs": []},          # armed locally, dead on Alpaca
        {"client_order_id": "P-FILL", "status": "filled",                          # exit filled at 120 on Alpaca...
         "legs": [{"status": "filled", "filled_avg_price": "120.00"}]},
    ]
    seen_kwargs = {}
    def _orders(status="open", limit=50, nested=False):
        seen_kwargs.update(status=status, nested=nested)
        return orders
    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [])   # position reconciliation exercised in test_regime_patch
    meta = {"armed": [{"id": "P-DEAD", "ticker": "AAA"}, {"id": "P-KEEP", "ticker": "BBB"}]}
    store.append_jsonl("trades.jsonl", {"id": "T1", "plan_id": "P-FILL", "ticker": "CCC", "exit": 100.0})  # sim exit 100
    alarms = []
    monkeypatch.setattr(obs, "alarm", lambda token, msg, **k: alarms.append(token))
    out = loop.reconcile_broker_state(meta, "2026-07-14", [{"plan_id": "P-FILL", "ticker": "CCC", "exit": 100.0}])
    assert seen_kwargs["nested"] is True                                           # MUST fetch nested (live legs live on the parent)
    assert [p["id"] for p in meta["armed"]] == ["P-KEEP"]                          # dead arm stripped, live kept
    assert out["drift"] and obs.ALARM_MIRROR_DRIFT in alarms                       # 20% gap > 0.5% → alarm
    tr = store.read_jsonl("trades.jsonl")[-1]
    assert tr["alpaca_fill_price"] == 120.0                                        # real fill backfilled to trades.jsonl
    assert store.read_json("broker_reconcile.json", {})["mirror_drift"] is True    # dashboard flag


def test_reconcile_is_noop_on_internal_broker(seeded_sandbox, monkeypatch):
    from meridian import loop
    monkeypatch.setattr(config, "BROKER", "internal")
    assert loop.reconcile_broker_state({"armed": []}, "2026-07-14", [])["checked"] is False


def test_submit_plan_tags_client_order_id(monkeypatch):
    from meridian.adapters import alpaca
    cap = {}
    monkeypatch.setattr(alpaca, "submit_bracket",
                        lambda *a, **k: cap.update(k) or {"ok": True})
    # `submit_plan` submit_bracket'tan ÖNCE `asset_tradable(ticker)` çağırır (LULD vekili, aynı
    # modülün global'i). Yamalanmadığında bu test CANLI Alpaca assets ucuna gidiyordu ve "X"
    # (US Steel) delist edildiği için `False` dönüp emir hiç gönderilmiyordu — yani test, ölçmek
    # istediği şeye (client_order_id etiketi) ağ üzerinden bağımlıydı. Ölçülen şey emir etiketi;
    # işlenebilirlik sorgusunun KENDİSİ burada ölçülmüyor, sabitleniyor.
    monkeypatch.setattr(alpaca, "asset_tradable", lambda *a, **k: True)
    alpaca.submit_plan({"id": "P-42", "ticker": "X", "entry_trigger": 100.0, "stop": 95.0,
                        "profit_target": 110.0, "size_r": 1.0}, equity=100_000)
    assert cap.get("client_order_id") == "P-42"           # join key set so the reconciler can match


# ============ PHASE 2 — corporate-action cache defense ============
def test_corporate_action_detects_split_but_ignores_legit_move():
    from meridian.adapters import data
    dates = pd.bdate_range("2024-01-01", periods=5)
    cached = pd.DataFrame({"date": dates, "close": [100, 101, 102, 103, 104]})
    resplit = pd.DataFrame({"date": dates, "close": [25, 25.25, 25.5, 25.75, 26]})   # 4:1 split re-adjusts series
    assert data._corporate_action(cached, resplit) is True
    # a legit +35% move is IDENTICAL in cache and fetch → NOT a corporate action (no false positive)
    same = pd.DataFrame({"date": dates, "close": [100, 101, 102, 103, 140]})
    assert data._corporate_action(same, same.copy()) is False


def test_load_bars_discards_stale_scale_cache_on_split(seeded_sandbox, monkeypatch):
    from meridian.adapters import data
    dates = pd.bdate_range("2024-01-01", periods=6)
    # stale cache on the OLD (pre-split) scale
    cp = data._cache_path("ZZZ")
    cp.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"date": dates, "open": [100]*6, "high": [101]*6, "low": [99]*6,
                  "close": [100, 101, 102, 103, 104, 105], "volume": [1e6]*6}).to_csv(cp, index=False)
    # fresh fetch: fully re-adjusted (post-split) — same dates, ~1/4 the price
    fresh = pd.DataFrame({"date": dates, "open": [25]*6, "high": [25.3]*6, "low": [24.8]*6,
                          "close": [25, 25.25, 25.5, 25.75, 26, 26.25], "volume": [4e6]*6})
    # **_ : `fetch` imzası büyüyebilir (2026-07-29'da `incremental_ok` eklendi). Katı imzalı bir
    # taklit, üretim koduyla ilgisi olmayan bir TypeError ile düşer ve testin ölçtüğü şeyi gizler.
    monkeypatch.setattr(data, "fetch", lambda t, s, e, timeout=30.0, **_: fresh)
    out = data.load_bars("ZZZ", "2024-01-01", "2024-01-10", use_cache=False)
    # the merged series must be the fresh single scale (no spliced discontinuity)
    assert out["close"].max() < 30 and out["close"].min() > 20    # all on the post-split scale, no 100→25 cliff


# ============ PHASE 3 — Hermes overfitting horizon ============
def test_horizon_defers_when_trades_cluster_in_one_short_window():
    from meridian import hermes_runtime as hr
    trades = [{"ts_close": "2026-07-10", "regime": "trend_up"},
              {"ts_close": "2026-07-12", "regime": "trend_up"},
              {"ts_close": "2026-07-14", "regime": "trend_up"}]     # 4-day span, single regime
    assert hr._horizon_ok(trades, 0, min_days=30) is False


def test_horizon_is_strict_and_no_multi_regime_bypass():
    """Dynamic-regime patch: the >=min_days calendar floor is a STRICT AND — merely touching 2 regimes
    inside a few days must NOT bypass it (the old OR-branch did exactly that)."""
    from meridian import hermes_runtime as hr
    two_regimes = [{"ts_close": "2026-07-10", "regime": "trend_up"},
                   {"ts_close": "2026-07-12", "regime": "chop"}]     # 2-day span, 2 regimes
    long_span = [{"ts_close": "2026-01-01", "regime": "trend_up"},
                 {"ts_close": "2026-03-01", "regime": "trend_up"}]   # 60 days, one regime
    assert hr._horizon_ok(two_regimes, 0, min_days=30) is False      # no more OR-bypass
    assert hr._horizon_ok(long_span, 0, min_days=30) is True
    assert hr._horizon_ok([], 0) is False                            # no new trades → defer


def test_market_regime_telemetry_string():
    from meridian import rollback
    assert rollback._market_regime([{"regime": "trend_up"}, {"regime": "chop"}, {"regime": "trend_up"}]) == "chop|trend_up"
    assert rollback._market_regime([]) == "unknown"


def test_hermes_context_carries_regime_window(seeded_sandbox):
    import json
    from meridian import hermes, store
    store.write_json("regime.json", {"regime": "trend_up"})
    store.append_jsonl("trades.jsonl", {"id": "T1", "regime": "trend_up", "r_multiple": 1.0})
    store.append_jsonl("trades.jsonl", {"id": "T2", "regime": "chop", "r_multiple": -0.5})
    ctx = json.loads(hermes.build_context())
    rw = ctx["regime_window"]
    assert rw["current"] == "trend_up" and rw["distinct_regimes"] == 2
    assert rw["recent_trade_regimes"].get("chop") == 1
