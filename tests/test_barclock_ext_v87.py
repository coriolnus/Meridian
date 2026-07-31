"""test_barclock_ext_v87.py — barclock age_s/is_fresh (Faz 4 additive). v86'ya dokunmaz."""
import datetime as dt

import pytest

from meridian import barclock as bc

UTC = dt.timezone.utc


@pytest.fixture(autouse=True)
def _reset_clock():
    yield
    bc.reset_clock()


def test_age_s_is_time_since_close():
    t = "2026-07-23T13:45:00Z"     # kapanış 13:46:00
    assert bc.age_s(t, dt.datetime(2026, 7, 23, 13, 46, 0, tzinfo=UTC)) == 0.0
    assert bc.age_s(t, dt.datetime(2026, 7, 23, 13, 47, 0, tzinfo=UTC)) == 60.0
    assert bc.age_s(t, dt.datetime(2026, 7, 23, 13, 45, 0, tzinfo=UTC)) == -60.0   # forming (negatif)
    assert bc.age_s("garbage") is None
    assert bc.age_s(None) is None


def test_is_fresh_requires_closed_and_recent():
    t = "2026-07-23T13:45:00Z"     # kapanış 13:46:00
    # forming (13:45:30, henüz kapanmadı) → fresh DEĞİL (age negatif)
    assert bc.is_fresh(t, 120, dt.datetime(2026, 7, 23, 13, 45, 30, tzinfo=UTC)) is False
    # kapanışta → fresh
    assert bc.is_fresh(t, 120, dt.datetime(2026, 7, 23, 13, 46, 0, tzinfo=UTC)) is True
    # 60s sonra, tol 120 → fresh
    assert bc.is_fresh(t, 120, dt.datetime(2026, 7, 23, 13, 47, 0, tzinfo=UTC)) is True
    # 200s sonra, tol 120 → bayat
    assert bc.is_fresh(t, 120, dt.datetime(2026, 7, 23, 13, 49, 20, tzinfo=UTC)) is False
    assert bc.is_fresh("garbage", 120) is False
