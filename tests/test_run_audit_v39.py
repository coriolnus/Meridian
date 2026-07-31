"""test_run_audit_v39.py — run denetimi (2026-07-21, tur 26).

run.py'nin `--replay` yolu sistemdeki EN YIKICI işlem: state'i sıfırdan kurar. 7. soru:
  RU1 "re-seed yalnız silahlı planları riske atar" → HAYIR: scoreboard.json'u TEK sürümlük yeni bir
     sözlükle EZİYORDU. v2/v3 ship edildikten sonraki bir re-seed tüm sürüm karnesini (live_score,
     backtest_oos, terfi kaydı) yok eder — ve rollback'in ebeveyn-skoru geri düşüşü oradan beslendiği
     için geri alma da körleşirdi. Silahlı-plan koruması vardı, öğrenme-geçmişi koruması YOKTU.
  RU2 "yıkıcı yol açık niyet ister" → zorlama bayrağı olmadan geçilememeli; zorlansa bile ARŞİVLEMELİ
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, run, store


@pytest.fixture
def seeded(sandbox_state, monkeypatch):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    monkeypatch.delenv("MERIDIAN_FORCE_RESEED", raising=False)
    yield sandbox_state
    config.reload_config()


def _history(n_versions=2):
    store.write_json("scoreboard.json", {
        "current_version": n_versions,
        "versions": {str(v): {"live_score": 0.1 * v, "params": {}, "parent": v - 1 or None}
                     for v in range(1, n_versions + 1)}})


# ---------- RU1/RU2: öğrenme geçmişi ----------
def test_ru1_reseed_refuses_to_destroy_the_scoreboard(seeded):
    _history(3)
    out = run.replay_seed("2024-01-01", "2024-02-01")
    assert out.get("error") == "scoreboard_history_present"
    assert len(store.read_json("scoreboard.json", {})["versions"]) == 3, "karne yine de silindi"


def test_ru1b_forced_reseed_archives_the_old_scoreboard(seeded, monkeypatch):
    _history(3)
    monkeypatch.setenv("MERIDIAN_FORCE_RESEED", "1")
    # replay'in ağır kısmını kısa devre yap: arşivleme kontrolünden SONRA patlasın
    monkeypatch.setattr(run, "bootstrap_v01", lambda: (_ for _ in ()).throw(RuntimeError("dur")))
    with pytest.raises(RuntimeError):
        run.replay_seed("2024-01-01", "2024-02-01")
    archived = list((config.HISTORY).glob("scoreboard-*.json"))
    assert archived, "zorlanan re-seed eski karneyi ARŞİVLEMEDEN sildi"
    doc = json.loads(archived[0].read_text())
    assert len(doc["versions"]) == 3


def test_ru1c_single_version_reseed_is_allowed(seeded, monkeypatch):
    _history(1)
    monkeypatch.setattr(run, "bootstrap_v01", lambda: (_ for _ in ()).throw(RuntimeError("dur")))
    with pytest.raises(RuntimeError):                       # kontrolü geçti, ağır kısımda durduk
        run.replay_seed("2024-01-01", "2024-02-01")


# ---------- silahlı plan koruması (mevcut, kilitleniyor) ----------
def test_armed_plans_still_block_a_reseed(seeded):
    store.write_json("portfolio.json", {"armed": [{"ticker": "NVDA", "id": "P-1"}]})
    out = run.replay_seed("2024-01-01", "2024-02-01")
    assert out.get("error") == "armed_plans_present" and out["armed"] == ["NVDA"]


def test_armed_guard_is_overridable_with_intent(seeded, monkeypatch):
    store.write_json("portfolio.json", {"armed": [{"ticker": "NVDA", "id": "P-1"}]})
    monkeypatch.setenv("MERIDIAN_FORCE_RESEED", "1")
    monkeypatch.setattr(run, "bootstrap_v01", lambda: (_ for _ in ()).throw(RuntimeError("dur")))
    with pytest.raises(RuntimeError):
        run.replay_seed("2024-01-01", "2024-02-01")         # açık niyet → geçer


# ---------- CLI yüzeyi ----------
def test_cli_dispatch_is_explicit(seeded, monkeypatch):
    seen = {}
    monkeypatch.setattr(run, "replay_seed", lambda s, e: seen.setdefault("replay", (s, e)) or {})
    monkeypatch.setattr(run, "once", lambda: seen.setdefault("once", True) or {})
    run.main(["--replay", "2024-01-01:2024-02-01"])
    assert seen["replay"] == ("2024-01-01", "2024-02-01")
    run.main(["--once"])
    assert seen.get("once") is True


def test_bootstrap_writes_v01_and_its_snapshot(seeded):
    strat = run.bootstrap_v01()
    assert strat["version"] == 1 and (config.STATE / "strategy.yaml").exists()
    assert (config.HISTORY / "v0001.yaml").exists(), "geri alma için ebeveyn anlık görüntüsü şart"
