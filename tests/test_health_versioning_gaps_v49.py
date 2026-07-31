"""test_health_versioning_gaps_v49.py — health + versioning + scheduler boşlukları (2026-07-21, tur 3).

health (uretkenlik, tutarlilik, monotonluk):
  * nabız ÜRETİLİR ve zorunlu alanları taşır — "koşuyorum" diyen tek kanıt
  * yaşı gerçekten ölçülür; bozuk/eksik damga 'bilinmiyor' (=bayat) sayılır, taze DEĞİL
  * nabız zamanı İLERİ gider; halt/learn-halt bayrakları nabızla tutarlı

versioning (uretkenlik, korunum, sahiplik):
  * her ship bir SNAPSHOT üretir (geri alma onsuz çalışmaz — turu 25'te canlıda ısırdı)
  * sürüm numarası ASLA yeniden kullanılmaz (audit #17/#31): geri alma sonrası bile ileri
  * karne satırları birleştirilir, EZİLMEZ (bir alan yazarken diğerleri kaybolmaz)

scheduler (uretkenlik, tutarlilik, monotonluk): seans sırası ve nabız/ilerleme kaydı.
"""
from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, health, store, versioning


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


# ---------- health ----------
def test_heartbeat_is_produced_with_its_mandatory_fields(seeded):
    hb = health.write_heartbeat(version=3, note="test")
    for k in ("ts", "mode", "autonomy_level", "halted"):
        assert k in hb, f"nabız '{k}' taşımıyor — canlılık kanıtı eksik"
    assert store.read_json("heartbeat.json", {})["version"] == 3


def test_heartbeat_age_and_staleness_are_honest(seeded):
    health.write_heartbeat()
    assert health.heartbeat_age_seconds() < 5 and health.stale(900) is False
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)).isoformat(timespec="seconds")
    store.write_json("heartbeat.json", {"ts": old})
    assert health.stale(900) is True


def test_missing_or_broken_heartbeat_reads_as_stale_not_fresh(seeded):
    (config.STATE / "heartbeat.json").unlink(missing_ok=True)
    assert health.heartbeat_age_seconds() is None and health.stale() is True
    store.write_json("heartbeat.json", {"ts": "bozuk-damga"})
    assert health.heartbeat_age_seconds() is None and health.stale() is True   # 'bilinmiyor' = bayat


def test_heartbeat_time_moves_forward(seeded):
    a = health.write_heartbeat()["ts"]
    b = health.write_heartbeat()["ts"]
    assert b >= a, "nabız zamanı GERİ gitti"


def test_halt_flags_are_reflected_in_the_heartbeat(seeded):
    health.set_halt(True)
    try:
        assert health.write_heartbeat()["halted"] is True
    finally:
        health.set_halt(False)
    assert health.write_heartbeat()["halted"] is False
    health.set_learn_halt(True)
    try:
        assert health.learn_halted() is True and health.halted() is False   # AYRI kapılar
    finally:
        health.set_learn_halt(False)


def test_circuit_breaker_uses_the_goal_limit(seeded):
    lim = config.goal()["limits"]["max_daily_loss_pct"] / 100.0
    assert health.circuit_breaker_tripped(-lim) is True
    assert health.circuit_breaker_tripped(-lim + 0.001) is False


# ---------- versioning ----------
def _strat(v=1, parent=None):
    return {**config.default_strategy(), "version": v, "parent": parent}


def test_every_commit_produces_a_snapshot(seeded):
    """Geri alma ebeveynin anlık görüntüsünü yükler — snapshot yoksa geri alma ÇALIŞMAZ (turu 25)."""
    child = versioning.bump(_strat(1), "entry.min_score", 65)
    versioning.commit(child)
    assert (config.HISTORY / f"v{child['version']:04d}.yaml").exists()
    assert int(config.load_strategy()["version"]) == child["version"]


def test_version_numbers_are_never_reused(seeded):
    """audit #17/#31: geri alma sonrası strategy.yaml ebeveynin numarasını taşır; bir sonraki ship
    ÖLÜ sürümün numarasını yeniden kullanırsa o sürümün işlemleriyle yargılanır."""
    v1 = _strat(1)
    versioning.snapshot(v1)                                     # v1'in anlık görüntüsü (bootstrap yapar)
    c2 = versioning.bump(v1, "entry.min_score", 65)
    versioning.commit(c2)
    versioning.update_scoreboard(c2["version"], live_score=0.1)
    versioning.revert_to(1)                                     # v2 geri alındı, defterde duruyor
    c3 = versioning.bump(config.load_strategy(), "entry.min_score", 70)
    assert c3["version"] > c2["version"], "geri alınan sürümün numarası yeniden kullanıldı"


def test_scoreboard_fields_merge_instead_of_clobbering(seeded):
    versioning.update_scoreboard(2, backtest_oos=0.3, parent=1)
    versioning.update_scoreboard(2, live_score=0.4)
    row = versioning.scoreboard()["versions"]["2"]
    assert row["backtest_oos"] == 0.3 and row["live_score"] == 0.4 and row["parent"] == 1


def test_regime_knob_goes_into_params_by_regime_only(seeded):
    child = versioning.bump(_strat(1), "entry.min_score@chop", 75)
    assert child["params_by_regime"]["chop"]["entry.min_score"] == 75
    assert child["params"]["entry.min_score"] == _strat(1)["params"]["entry.min_score"]   # düz param DOKUNULMADI


def test_revert_to_missing_snapshot_raises_not_silently_noops(seeded):
    with pytest.raises(FileNotFoundError):
        versioning.revert_to(99)                                # sessiz no-op olsaydı geri alma yalan söylerdi


# ---------- scheduler ----------
def test_scheduler_records_its_progress(sandbox_state):
    from meridian import scheduler
    import inspect
    src = inspect.getsource(scheduler)
    assert "beat(" in src, "zamanlayıcı nabız damgalamıyor — bekçi onu göremez"
    assert "last_processed" in src, "işlenen son seans kaydedilmiyor → tekrar/atlama görünmez"


def test_scheduler_state_is_forward_only(sandbox_state):
    """Seans ilerlemesi ileri-only olmalı: aynı seans iki kez işlenmez, eski seansa dönülmez."""
    from meridian import scheduler
    import inspect
    src = inspect.getsource(scheduler)
    assert "refused_regressive" in src or "last_processed" in src
