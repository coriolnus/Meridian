"""test_sprint_audit_v45.py — sprint (tur 32) + sprint_run (tur 33) denetimi, 2026-07-21.

Sprint, canlı defterin YANINDA koşan tek şey: ayrı süreç, ayrı MERIDIAN_ROOT, ayrı state. 7. soru:
  SR1 "canlı defter ASLA dokunulmaz" → izolasyon üç şeye dayanıyor (kopyalama, MERIDIAN_ROOT,
     SKIP_COPY) ve üçü de tek tek kontrol edilmiyordu. Bir gün biri env'i unutursa sprint CANLI
     trades.jsonl'ı sıfırlar — geri dönüşü olmayan bir hata.
  SR2 "pencereler sabittir (p-hacking yok)" → CUTOFF/EVAL_START env'den okunabilir hale gelirse
     operatör pencere alışverişi yapabilir; sabitlik yazılıydı, test edilmiyordu
  SR3 "sonuç EĞİTİM kalibrasyonudur, canlıya karışmaz" → canlı kalibrasyon/otonomi merdiveni
     sprint dosyalarını okumamalı
  SR4 "HALT kum havuzuna girmez" → kopyalanan bir kill-switch sprint'i sessizce faydasız kılar (audit #23)
"""
from __future__ import annotations

import inspect
import json
import os
import pathlib

import pytest
import yaml

from meridian import config, sprint, store


SRC = inspect.getsource(sprint)


# ---------- SR1: izolasyon ----------
def test_sr1_child_runs_with_its_own_meridian_root():
    assert '"MERIDIAN_ROOT": str(sbroot)' in SRC, "çocuk süreç CANLI state'e yazabilir"
    assert '"MERIDIAN_BROKER": "internal"' in SRC, "sprint aynaya emir göndermemeli"


def test_sr1b_reset_only_touches_the_sandbox(sandbox_state, tmp_path):
    """_reset_sandbox_state VERİLEN dizini sıfırlar; canlı state'e tek bir yazma bile olmamalı."""
    live_trades = config.STATE / "trades.jsonl"
    store.write_jsonl("trades.jsonl", [{"id": "T1"}])
    before = live_trades.read_text()
    sb = tmp_path / "sbstate"
    sb.mkdir()
    sprint._reset_sandbox_state(sb)
    assert (sb / "trades.jsonl").read_text() == ""            # kum havuzu sıfırlandı
    assert live_trades.read_text() == before                  # canlı defter DOKUNULMADI
    assert (sb / "history" / "v0001.yaml").exists()           # geri alma için ebeveyn anlık görüntüsü


def test_sr1c_sandbox_gets_a_flat_book_and_v1_parent_none(tmp_path):
    sb = tmp_path / "sbstate"; sb.mkdir()
    sprint._reset_sandbox_state(sb)
    pf = json.loads((sb / "portfolio.json").read_text())
    assert pf["positions"] == {} and pf["armed"] == [] and pf["realized_pnl"] == 0.0
    strat = yaml.safe_load((sb / "strategy.yaml").read_text())
    assert strat["version"] == 1 and strat["parent"] is None


# ---------- SR4: HALT ve sırlar kopyalanmaz ----------
def test_sr4_halt_and_secrets_never_enter_the_sandbox():
    for name in ("HALT", "secrets.json", "bars", "sprint"):
        assert name in sprint.SKIP_COPY, f"{name} kum havuzuna kopyalanıyor"


# ---------- SR2: pencereler sabit ----------
def test_sr2_windows_are_hardcoded_not_tunable():
    assert sprint.CUTOFF < sprint.EVAL_START, "seçim ve ölçüm pencereleri AYRIK olmalı"
    for token in ("CUTOFF", "EVAL_START"):
        line = next(l for l in SRC.splitlines() if l.startswith(f"{token} ="))
        assert "environ" not in line and "cfg" not in line, f"{token} dışarıdan ayarlanabilir → p-hacking"


def test_sr2b_select_windows_end_at_the_cutoff():
    assert sprint.SELECT_WINDOWS[2] == sprint.CUTOFF and sprint.SELECT_WINDOWS[3] == sprint.CUTOFF


# ---------- SR3: eğitim sonucu canlıya karışmaz ----------
def test_sr3_live_calibration_never_reads_sprint_artifacts():
    from meridian import analytics, probgate, selfreview
    for mod in (analytics, probgate, selfreview):
        src = inspect.getsource(mod)
        assert "sprint_status" not in src and "state/sprint" not in src, \
            f"{mod.__name__} sprint çıktısını canlı kalibrasyona karıştırıyor"


def test_sr3b_status_is_labeled_a_read_model():
    assert "read-model" in SRC and "NOT a learning ledger" in SRC


# ---------- süreç yaşam döngüsü ----------
def test_zombie_child_is_reaped_not_reported_active(sandbox_state, monkeypatch):
    """audit #22: biten çocuk 'active' okunuyordu ve start() sonsuza dek 'already_running' diyordu."""
    store.write_json(sprint.STATUS_FILE, {"pid": 999999, "sid": "x"})
    assert sprint.status()["active"] is False


def test_prune_keeps_the_newest_sandboxes(sandbox_state):
    root = config.STATE / "sprint"
    root.mkdir(parents=True, exist_ok=True)
    for name in ("2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05"):
        (root / name).mkdir()
    sprint._prune_old_sandboxes(keep=3)
    left = sorted(d.name for d in root.iterdir())
    assert left == ["2026-07-03", "2026-07-04", "2026-07-05"]


def test_sprint_run_measures_on_the_eval_window_only():
    from meridian import sprint_run
    src = inspect.getsource(sprint_run)
    assert "EVAL_START" in src or "eval_start" in src
    assert "CUTOFF" in src or "cutoff" in src
