"""test_rollback_audit_v38.py — rollback denetimi (2026-07-21, tur 25).

Bu modül öğrenme döngüsünü KAPATAN yer: canlı sürüm ebeveynini geçemezse geri alır, geçerse terfi
ettirir. 7. soru:
  RB1 "iki yol aynı sayıyı görür" → `evaluate_outcomes` ve `check_and_rollback` skorları/geri-düşüşleri
     AYRI AYRI hesaplıyor. İlki "geri al" deyip ikincisini çağırıyor; ikincisi kendi hesabında eşiği
     geçmezse HİÇBİR ŞEY olmaz ve bu sessizdir — kapının 'geri alındı' sandığı sürüm canlıda kalır.
  RB2 "kanıt yetersizken asla geri alınmaz" → min_sample altında gürültüyle sürüm devrilmemeli
  RB3 "rejim ship'i KENDİ diliminde ölçülür" → global skorla kıyaslamak sahte delta üretir
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, memory, rollback, store, versioning


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _trades(n, version, r, regime="trend_up", start_day=1):
    return [{"id": f"T{version}{i}", "strategy_version": version, "regime": regime,
             "r_multiple": r, "pnl_dollars": r * 1000,
             "ts_open": f"2026-0{1 + (i % 6)}-{(i % 27) + 1:02d}",
             "ts_close": f"2026-0{1 + (i % 6)}-{(i % 27) + 2:02d}",
             "score": 70, "r_multiple_expected": 2.5} for i in range(n)]


def _ship(version=2, parent=1, variable="entry.min_score", inc_oos=0.30):
    # ebeveynin anlık görüntüsü OLMALI — geri alma onu yükler (yoksa ayrı bir alarm yolu var, aşağıda)
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    (config.HISTORY / f"v{parent:04d}.yaml").write_text(yaml.safe_dump(
        {"version": parent, "parent": None, "params": config.default_strategy()["params"]}))
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {"version": version, "parent": parent, "params": config.default_strategy()["params"]}))
    memory.record({"id": "H00001", "version_to": version, "status": "live", "variable": variable,
                   "predicted_delta": 0.05, "backtest": {"incumbent_oos": inc_oos}})


# ---------- RB1: iki yol tek karar ----------
def test_rb1_a_rollback_decision_is_never_silently_dropped(seeded):
    """evaluate_outcomes "geri al" dediyse GERÇEKTEN geri alınmalı: iki ayrı hesap ayrışırsa karar
    sessizce buharlaşır ve kötü sürüm canlıda kalır."""
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    store.write_jsonl("trades.jsonl", _trades(n, 2, -0.9) + _trades(n, 1, 0.8))
    out = rollback.evaluate_outcomes(goal)
    assert out is not None and out.get("rolled_back_from") == 2, f"karar buharlaştı: {out}"
    assert int(config.load_strategy()["version"]) == 1, "strategy.yaml ebeveyne dönmedi"
    h = memory.all_hypotheses()[0]
    assert h["status"] == "rolled_back" and h["realized_delta"] < 0


def test_rb1b_a_clear_win_is_promoted(seeded):
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    store.write_jsonl("trades.jsonl", _trades(n, 2, 0.9) + _trades(n, 1, -0.2))
    out = rollback.evaluate_outcomes(goal)
    assert out and out["promoted"] is True and out["rolled_back"] is False
    assert memory.all_hypotheses()[0]["status"] == "promoted"
    assert int(config.load_strategy()["version"]) == 2      # kazanan canlı kalır


def test_rb1c_neutral_hold_writes_the_outcome_without_promoting(seeded):
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    store.write_jsonl("trades.jsonl", _trades(n, 2, 0.30) + _trades(n, 1, 0.30))
    out = rollback.evaluate_outcomes(goal)
    assert out and out["promoted"] is False and out["rolled_back"] is False
    h = memory.all_hypotheses()[0]
    assert h["status"] == "live" and h.get("realized_delta") is not None   # döngü yine de KAPANDI


# ---------- RB2: kanıt eşiği ----------
def test_rb2_below_min_sample_nothing_happens(seeded):
    goal = config.goal()
    _ship()
    store.write_jsonl("trades.jsonl", _trades(max(1, int(goal["min_sample"]) - 1), 2, -2.0))
    assert rollback.evaluate_outcomes(goal) is None
    assert rollback.check_and_rollback(goal) is None
    assert int(config.load_strategy()["version"]) == 2, "gürültüyle geri alındı"


def test_rb2b_v1_has_nothing_to_roll_back_to(seeded):
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {"version": 1, "parent": None, "params": config.default_strategy()["params"]}))
    store.write_jsonl("trades.jsonl", _trades(50, 1, -3.0))
    assert rollback.evaluate_outcomes(config.goal()) is None


# ---------- RB3: rejim ship'i kendi diliminde ----------
def test_rb3_regime_ship_is_measured_inside_its_regime(seeded):
    """var@chop bir ship, GLOBAL defterle değil CHOP dilimiyle ölçülmeli; aksi halde trend_up'ın
    bolluğu sahte bir 'başarı' (ya da başarısızlık) üretir."""
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship(variable="entry.min_score@chop")
    # chop diliminde v2 KÖTÜ, trend_up diliminde parlak — global bakılsaydı geri alınmazdı
    store.write_jsonl("trades.jsonl",
                      _trades(n, 2, -0.9, regime="chop") + _trades(n, 1, 0.8, regime="chop")
                      + _trades(n * 2, 2, 2.0, regime="trend_up"))
    out = rollback.evaluate_outcomes(goal)
    assert out and out.get("rolled_back_from") == 2, "rejim dilimi yerine global sayı kullanılmış"


def test_rb3b_regime_ship_scoreboard_stays_regime_tagged(seeded):
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship(variable="entry.min_score@chop")
    store.write_jsonl("trades.jsonl", _trades(n, 2, 0.35, regime="chop") + _trades(n, 1, 0.30, regime="chop"))
    rollback.evaluate_outcomes(goal)
    v = versioning.scoreboard().get("versions", {}).get("2", {})
    assert any(k.startswith("live_score@") for k in v), \
        "rejim ship'i GLOBAL live_score'u kirletiyor — sonraki çocuklar bozuk tabana karşı yarışır"


def test_alarm_and_notification_on_rollback(seeded):
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    store.write_jsonl("trades.jsonl", _trades(n, 2, -0.9) + _trades(n, 1, 0.8))
    rollback.evaluate_outcomes(goal)
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "ROLLBACK" in blob                                # operatör panel açmadan duyar (obs turu 20)


def test_missing_parent_snapshot_is_loud_not_silent(seeded):
    """Geri alma BAŞARISIZ olursa (ebeveyn anlık görüntüsü kayıp) kötü sürüm canlı kalır — bu,
    jenerik bir uyarıya gömülmemeli: operatörün elle müdahale etmesi gereken bir alarm."""
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    (config.HISTORY / "v0001.yaml").unlink()                 # anlık görüntü kayboldu
    store.write_jsonl("trades.jsonl", _trades(n, 2, -0.9) + _trades(n, 1, 0.8))
    out = rollback.evaluate_outcomes(goal)
    assert out and out.get("error") == "parent snapshot missing"
    assert int(config.load_strategy()["version"]) == 2        # dürüst: hâlâ canlı
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "GERİ ALMA BAŞARISIZ" in blob and "ROLLBACK" in blob
