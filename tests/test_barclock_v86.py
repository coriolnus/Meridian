"""test_barclock_v86.py — intraday LOOK-AHEAD saati (Faz 4). Enjekte edilen saatle deterministik."""
import datetime as dt

import pytest

from meridian import barclock as bc

UTC = dt.timezone.utc


@pytest.fixture(autouse=True)
def _reset_clock():
    yield
    bc.reset_clock()


def test_close_ts_is_open_plus_60s():
    assert bc.close_ts("2026-07-23T13:45:00Z") == dt.datetime(2026, 7, 23, 13, 46, 0, tzinfo=UTC)
    assert bc.close_ts("2026-07-23T13:45:00+00:00") == dt.datetime(2026, 7, 23, 13, 46, 0, tzinfo=UTC)


def test_admissible_only_after_close():
    t = "2026-07-23T13:45:00Z"     # kapanış 13:46:00
    assert bc.is_admissible(t, dt.datetime(2026, 7, 23, 13, 45, 30, tzinfo=UTC)) is False  # 60s erken = look-ahead
    assert bc.is_admissible(t, dt.datetime(2026, 7, 23, 13, 45, 59, tzinfo=UTC)) is False
    assert bc.is_admissible(t, dt.datetime(2026, 7, 23, 13, 46, 0, tzinfo=UTC)) is True    # tam kapanış
    assert bc.is_admissible(t, dt.datetime(2026, 7, 23, 13, 47, 0, tzinfo=UTC)) is True


def test_malformed_or_missing_timestamp_is_not_admissible():
    for bad in (None, "", "garbage", "2026-13-99T99:99:99Z"):
        assert bc.is_admissible(bad, dt.datetime(2030, 1, 1, tzinfo=UTC)) is False   # fail-closed


def test_admissible_bars_filters_out_the_forming_bar():
    bc.set_clock(lambda: dt.datetime(2026, 7, 23, 13, 46, 30, tzinfo=UTC))
    bars = [{"t": "2026-07-23T13:44:00Z", "c": 1},   # kapandı (13:45)
            {"t": "2026-07-23T13:45:00Z", "c": 2},   # kapandı (13:46)
            {"t": "2026-07-23T13:46:00Z", "c": 3}]   # FORMING (kapanış 13:47 > 13:46:30) → dışlanır
    assert [b["c"] for b in bc.admissible_bars(bars)] == [1, 2]


def test_injected_clock_drives_now():
    bc.set_clock(lambda: dt.datetime(2030, 1, 1, tzinfo=UTC))
    assert bc.now() == dt.datetime(2030, 1, 1, tzinfo=UTC)


def test_ny_session_gate_is_dst_aware():
    # yaz (EDT, UTC-4): 14:00 UTC = 10:00 ET → açık; 13:00 UTC = 09:00 ET → kapalı
    assert bc.is_market_open(dt.datetime(2026, 7, 23, 14, 0, tzinfo=UTC)) is True
    assert bc.is_market_open(dt.datetime(2026, 7, 23, 13, 0, tzinfo=UTC)) is False
    assert bc.is_market_open(dt.datetime(2026, 7, 23, 21, 0, tzinfo=UTC)) is False   # 17:00 ET
    # kış (EST, UTC-5): 14:30 UTC = 09:30 ET → açık; 14:00 UTC = 09:00 ET → kapalı
    assert bc.is_market_open(dt.datetime(2026, 1, 15, 14, 30, tzinfo=UTC)) is True
    assert bc.is_market_open(dt.datetime(2026, 1, 15, 14, 0, tzinfo=UTC)) is False
    # hafta sonu → kapalı (2026-07-25 Cmt)
    assert bc.is_market_open(dt.datetime(2026, 7, 25, 14, 0, tzinfo=UTC)) is False


def test_session_date_is_et_calendar_day():
    # 2026-07-24 01:00 UTC = 2026-07-23 21:00 ET → ET seans tarihi hâlâ 07-23
    assert bc.session_date(dt.datetime(2026, 7, 24, 1, 0, tzinfo=UTC)) == "2026-07-23"
