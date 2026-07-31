"""Batch M — data realism: SPY benchmark-relative alpha (#33), the extended completeness gate (#34),
and the keyless PIT-constituents scaffold (#36)."""
import datetime as dt

import pandas as pd
import pytest

from meridian import analytics
from meridian.adapters import data, constituents


def _codes(issues):
    return {i["code"] for i in issues}


def test_completeness_gate_flags_zero_volume_and_gap():
    today = dt.date.today()
    dates = pd.to_datetime([today - dt.timedelta(days=x) for x in (40, 39, 5, 4, 3)])  # a big gap 39->5
    df = pd.DataFrame({"date": sorted(dates), "open": [10, 10, 10, 10, 10], "high": [11, 11, 11, 11, 11],
                       "low": [9, 9, 9, 9, 9], "close": [10, 10, 10, 10, 10], "volume": [1e6, 0, 1e6, 1e6, 1e6]})
    ok, issues = data.validate_bars(df, "X")
    assert ok                                          # all soft -> still tradeable, but flagged
    assert "zero_volume" in _codes(issues) and "calendar_gap" in _codes(issues)


def test_completeness_gate_flags_stale_ticker():
    old = pd.to_datetime([dt.date(2020, 1, 2) + dt.timedelta(days=i) for i in range(5)])
    df = pd.DataFrame({"date": old, "open": [10] * 5, "high": [11] * 5, "low": [9] * 5,
                       "close": [10] * 5, "volume": [1e6] * 5})
    ok, issues = data.validate_bars(df, "DEAD")
    assert "stale_ticker" in _codes(issues)


def test_benchmark_relative_excess(monkeypatch):
    trades = [{"pnl_dollars": 500, "ts_open": "2024-01-02", "ts_close": "2024-02-02"},
              {"pnl_dollars": 500, "ts_open": "2024-02-05", "ts_close": "2024-03-05"},
              {"pnl_dollars": 500, "ts_open": "2024-03-06", "ts_close": "2024-04-06"},
              {"pnl_dollars": 500, "ts_open": "2024-04-07", "ts_close": "2024-05-07"},
              {"pnl_dollars": 500, "ts_open": "2024-05-08", "ts_close": "2024-06-08"}]
    monkeypatch.setattr(analytics, "_trades", lambda: trades)
    # SPY doubled over the window -> +100% benchmark; strategy made +2500/100000 = +2.5% -> big NEGATIVE excess
    spy = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-06-08"]), "close": [100.0, 200.0]})
    monkeypatch.setattr(data, "load_bars", lambda *a, **k: spy)
    br = analytics.benchmark_relative()
    assert br is not None and br["benchmark_return"] == pytest.approx(1.0)
    assert br["excess_return"] < 0 and br["beat_benchmark"] is False   # honest: lost to beta


def test_constituents_as_of_walks_changelog(sandbox_state):
    from meridian import store
    # NOT (denetim turu 3, 2026-07-21): bu fixture'ın ta kendisi bir zamanlar GERÇEK state klasörüne
    # sızmış ve üretimde "S&P 500 = 3 sembol" olarak duruyordu. Artık makullük kapısı (>=400 sembol)
    # ve gelecek-tarih reddi var; fixture da gerçekçi boyutta ve geçerli tarihli.
    filler = [f"S{i:03d}" for i in range(460)]
    store.write_json("sp500_constituents.json", {"as_of": "2026-07-21",
        "current": ["AAA", "BBB", "CCC"] + filler,
        "changes": [{"date": "2025-06-01", "added": "CCC", "removed": "ZZZ"}]})
    # before 2025-06-01: CCC not yet added, ZZZ still a member
    members = constituents.as_of("2025-01-01")
    assert "CCC" not in members and "ZZZ" in members and "AAA" in members
