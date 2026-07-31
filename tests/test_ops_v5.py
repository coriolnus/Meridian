"""test_ops_v5.py — Operasyon ve Teşhis katmanı (Faz 0-3, 2026-07-20).

Faz 0: karantina zorlaması (bozuk barlı ticker taramadan DIŞLANIR), trail PATCH reddi → alarm.
Faz 1: IO gecikme telemetrisi, hayalet emir tespiti mantığı, deflasyon istatistiği, karartma radarı.
Faz 3: kademeli kriz kontrolleri (HALT / LEARN_HALT / cancel-open koruyucu-bacak ayrımı),
       yapılandırılmış karar ağacı (davranış birebir), debug export secrets DIŞARIDA."""
import inspect
import io
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from meridian import config, store, health, guard, loop
from tests.conftest import make_bars


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------------- Faz 0.1: karantina zorlaması ----------------
def _coherent(df):
    """make_bars ara sıra open>high üretir (validate 'hard' sayar) — OHLC'yi tutarlılaştır."""
    df = df.copy()
    df["high"] = df[["open", "close", "high"]].max(axis=1) * 1.001
    df["low"] = df[["open", "close", "low"]].min(axis=1) * 0.999
    return df


def test_quarantined_ticker_is_excluded_from_scan(seeded_sandbox):
    """5 ticker'dan 1'i bozuk (high<low) → data_bad eşiği (%25) AŞILMAZ, döngü koşar; ama bozuk
    ticker aday üretemez ve data_quality'de listelenir. Eski davranış: listelenir AMA taranırdı."""
    bars = {f"T{i}": _coherent(make_bars(360, seed=i, breakout_at=340)) for i in range(4)}
    bad = _coherent(make_bars(360, seed=9, breakout_at=340))
    bad.loc[bad.index[-20:], "high"] = bad["low"].iloc[-20:] * 0.5      # 20 bar high<low → hard fail
    bars["BAD"] = bad
    idx = _coherent(make_bars(360, seed=42))
    res = loop.daily_cycle(bars, idx)
    dq = store.read_json("data_quality.json", {})
    assert "BAD" in dq.get("tickers_failed", [])
    assert dq.get("data_halt") is False                                  # 1/5 = %20 < %25 → halt yok
    cands = store.read_jsonl("candidates.jsonl")
    assert all(c["ticker"] != "BAD" for c in cands)                      # karantina: aday YOK
    assert res.get("status") != "noop"


# ---------------- Faz 0.2: trail PATCH reddi → alarm ----------------
def test_trail_patch_reject_fires_alarm(monkeypatch):
    from meridian import obs
    fired = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: fired.append((tok, kw)))
    loop._trail_patch_alarm("NVDA", {"ok": False, "detail": "42210 rejected"}, 100.0, 105.0)
    assert fired and fired[0][0] == obs.ALARM_TRAIL_DESYNC and fired[0][1]["ticker"] == "NVDA"
    fired.clear()
    loop._trail_patch_alarm("NVDA", {"ok": True}, 100.0, 105.0)          # başarılı PATCH → alarm yok
    assert not fired
    # kaynak denetimi: reconcile gerçekten bu yardımcıyı çağırıyor
    assert "_trail_patch_alarm(" in inspect.getsource(loop.reconcile_broker_state)


# ---------------- Faz 1: IO telemetrisi ----------------
def test_io_stats_records_writes(seeded_sandbox):
    before = store.io_stats()["writes"]
    for i in range(25):
        store.write_json(f"io_probe_{i}.json", {"i": i})
    st = store.io_stats()
    assert st["writes"] >= before + 25 and st["p50_ms"] is not None and st["p95_ms"] is not None


# ---------------- Faz 1: deflasyon + karartma radarı ----------------
def test_deflate_stats_measures_search_optimism(seeded_sandbox):
    from meridian import analytics
    store.append_jsonl("hypotheses.jsonl", {"id": "H1", "variable": "x",
                                            "predicted_delta_search": 0.40, "predicted_delta": 0.10})
    store.append_jsonl("hypotheses.jsonl", {"id": "H2", "variable": "y",
                                            "predicted_delta_search": 0.20, "predicted_delta": 0.20})
    d = analytics.deflate_stats()
    assert d["n"] == 2
    assert d["last"][0]["deflation_pct"] == 75.0 and d["last"][1]["deflation_pct"] == 0.0
    assert d["avg_deflation_pct"] == pytest.approx(37.5)


def test_blackout_radar_empty_vs_active(seeded_sandbox):
    from meridian import earnings
    earnings.clear_cache()
    r = earnings.blackout_radar(["AAPL", "MSFT"], "2026-07-20")
    assert r["empty"] is True and r["blackout"] == []                    # boş CSV ≠ 'karartma yok'
    (seeded_sandbox / "earnings.csv").write_text("ticker,date\nAAPL,2026-07-23\n")
    earnings.clear_cache()
    r = earnings.blackout_radar(["AAPL", "MSFT"], "2026-07-20")
    assert r["empty"] is False
    assert [b["ticker"] for b in r["blackout"]] == ["AAPL"] and r["blackout"][0]["days_left"] == 3


# ---------------- Faz 3: kademeli kontroller ----------------
def test_halt_and_learn_halt_flags(seeded_sandbox):
    assert health.halted() is False and health.learn_halted() is False
    assert health.set_halt(True) is True and health.halted() is True
    assert health.set_halt(False) is False
    assert health.set_learn_halt(True) is True and health.learn_halted() is True
    assert health.set_learn_halt(False) is False


def test_learn_halt_blocks_ship_not_trading(seeded_sandbox):
    from meridian import reflect
    health.set_learn_halt(True)
    res = reflect.submit({"variable": "stop_loss_atr_mult", "new": 2.1, "source": "t"})
    assert res["status"] == "learning_halted"                            # ship YOK
    assert health.halted() is False                                      # işlem durdurma AYRI bayrak


def test_cancel_open_spares_protective_legs(monkeypatch):
    """Kademe-2'nin yasası: dolmamış giriş iptal edilir; dolu parent'ın koruyucu bacaklarına dokunulmaz."""
    from meridian.adapters import alpaca
    orders = [
        {"id": "o1", "symbol": "AAA", "status": "new", "filled_qty": "0", "client_order_id": "P-2026-07-21-AAA"},
        {"id": "o2", "symbol": "BBB", "status": "filled", "filled_qty": "10", "client_order_id": "P-2026-07-21-BBB"},
        {"id": "o3", "symbol": "CCC", "status": "partially_filled", "filled_qty": "4", "client_order_id": "P-2026-07-21-CCC"},
    ]
    cancelled = []
    monkeypatch.setattr(alpaca, "orders", lambda **kw: orders)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: cancelled.append(oid) or {"ok": True})
    res = alpaca.cancel_open_entries()
    assert cancelled == ["o1"]                                           # yalnız dolmamış giriş
    assert {k["symbol"] for k in res["kept"]} == {"BBB", "CCC"}          # koruyucu bacaklılar korundu


def test_asset_tradable_fail_open(monkeypatch):
    from meridian.adapters import alpaca
    import httpx
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("net")))
    assert alpaca.asset_tradable("NVDA") is None                         # ağ hatası işlem engeli DEĞİL
    src = inspect.getsource(alpaca.submit_plan)
    assert "is False" in src                                             # yalnız KESİN 'kapalı' engeller


# ---------------- Faz 3: yapılandırılmış karar ağacı ----------------
def test_classify_gate_detail_records_passes_and_fails():
    goal = config.goal()
    params = config.default_strategy()["params"]
    regime = {"exposure_budget_pct": 60, "leading_sectors": []}
    port = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0, "open_risk_r": 0.0, "max_corr": 0.0}
    plan = {"ticker": "X", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 3.0, "score": 90}
    checks = []
    v, reasons = guard.classify_gate(plan, port, regime, goal, params, detail_out=checks)
    v2, r2 = guard.classify_gate(plan, port, regime, goal, params)       # detail_out'suz — birebir aynı karar
    assert (v, reasons) == (v2, r2)
    names = {c["check"] for c in checks}
    assert {"exposure_budget", "max_open_positions", "rr_floor", "heat_hard"} <= names
    assert all(c["passed"] for c in checks if c["severity"] == "hard")   # GEÇEN kontroller de kayıtlı
    checks2 = []
    v3, _ = guard.classify_gate(plan, port, {**regime, "exposure_budget_pct": 0}, goal, params,
                                detail_out=checks2)
    bad = next(c for c in checks2 if c["check"] == "exposure_budget")
    assert v3 == "NO_GO" and bad["passed"] is False and "bütçe" in bad["note"] or "exposure" in bad["note"]


# ---------------- Faz 3: debug export — secrets ASLA çıkmaz ----------------
def test_debug_export_excludes_secrets(seeded_sandbox):
    from fastapi.testclient import TestClient
    from meridian.api import app
    store.write_json("secrets.json", {"FMP_API_KEY": "GIZLI-DEGER"})
    store.write_json("harmless.json", {"ok": True})
    with TestClient(app) as client:
        r = client.get("/api/debug_export")
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert "state/harmless.json" in names and "manifest.json" in names
    assert not any("secrets" in n for n in names)                        # anahtar sızıntısı yok
    assert b"GIZLI-DEGER" not in r.content


def test_diagnostics_contract_has_hud_and_gatekeeper(seeded_sandbox):
    """Cam Kokpit v2 sözleşmesi: HUD ve karar-ağacı blokları BOŞ state'te bile şekil korur —
    UI hiçbir alan için uydurma varsayılana düşmek zorunda kalmaz."""
    from fastapi.testclient import TestClient
    from meridian.api import app
    with TestClient(app) as client:
        r = client.get("/api/diagnostics")
    assert r.status_code == 200
    d = r.json()
    assert {"hud", "scheduler", "gatekeeper", "reconcile", "risk", "mlops", "pipeline", "ledgers"} <= set(d)
    assert {"mode", "explore_mode", "halted", "learn_halted", "stream_ok"} <= set(d["hud"])
    assert "plans" in d["gatekeeper"] and isinstance(d["gatekeeper"]["plans"], list)
    assert {"ticks", "every"} <= set(d["mlops"]["warmup"])
