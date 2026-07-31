"""test_intraday_arm_flag_v89.py — Faz 4 INTRADAY_ARM dosya bayrağı (HALT ikizi)."""
from meridian import health


def test_default_is_unarmed(sandbox_state):
    assert health.intraday_armed() is False               # dosya yok = SİLAHSIZ (gözlem)


def test_toggle_arm_flag(sandbox_state):
    assert health.set_intraday_arm(True) is True
    assert health.intraday_armed() is True
    assert health.intraday_arm_path().exists()
    assert health.set_intraday_arm(False) is False
    assert health.intraday_armed() is False
    assert not health.intraday_arm_path().exists()


def test_arm_path_is_under_state(sandbox_state):
    from meridian import config
    assert health.intraday_arm_path() == config.STATE / "INTRADAY_ARM"
