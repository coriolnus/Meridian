"""test_learning_loop_repair_v78.py — ÖĞRENME DÖNGÜSÜ ONARIMI (2026-07-22).

Denetim şunu buldu: kum havuzunda döngü kapanıyor, CANLIDA kapanmıyor. `evaluate_outcomes` her
turda sessizce `return None` ediyordu çünkü v4'ün ebeveyn skoru yoktu — ve "kanıt bekliyorum" ile
"ÖLÇEMİYORUM" aynı görünüyordu. Ajan meşgul görünüyor, hiçbir hipotez terminale ulaşmıyor,
kalibrasyon n=0 kalıyor.

Dört onarım, dördü de burada kilitli:
  1. YETİM SÜPÜRMESİ  — süperseded `live` hipotezler terminale taşınır (H00029/H00026 sonsuza dek
     `live` kalıyordu; sonradan işlem biriktirseler bile kimse onlara bakmıyordu).
  2. AÇIK DÖNGÜ OLAYI — ölçüm yapılamıyorsa bu bir OLAYDIR, sessizlik değil.
  3. GEÇİŞ YASASI     — `promoted → proposed` geri dönüşü ve uydurma statüler reddedilir.
  4. KİMLİK İŞARETİ   — defter tamamen silinse bile numaralar geri sarmaz.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from meridian import config, memory, rollback, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _strateji(version: int, parent=None) -> None:
    import yaml
    s = config.default_strategy()
    s["version"], s["parent"] = version, parent
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(s))


def _hyp(hid: str, status: str, version_to=None, **extra) -> dict:
    row = {"id": hid, "ts": memory.now_iso(), "variable": "entry.min_score",
           "status": status, "version_to": version_to, **extra}
    store.append_jsonl(memory.HYP, row)
    return row


# ---------------- 1) YETİM SÜPÜRMESİ ----------------
def test_superseded_live_hypotheses_reach_a_terminal_state(seeded):
    """CANLI KANIT: H00029 (v2→v3, `live`, realized_delta yok) ve H00026 sonsuza kadar açıktı.
    `evaluate_outcomes` yalnız GÜNCEL sürüme bakar; v2 min_sample'a ulaşmadan v3 ship edilirse
    v2'nin hipotezi bir daha HİÇ okunmaz — sonradan işlem biriktirse bile."""
    _strateji(4, parent=3)
    _hyp("H00026", "live", version_to=2, realized_delta=-0.0364)
    _hyp("H00029", "live", version_to=3)
    _hyp("H00031", "live", version_to=4)              # GÜNCEL sürüm — dokunulmaz
    _hyp("H00030", "promoted", version_to=2)          # zaten terminal

    kapanan = rollback.sweep_orphan_hypotheses()
    assert set(kapanan) == {"H00026", "H00029"}, f"yanlış süpürme: {kapanan}"
    by_id = {h["id"]: h for h in memory.all_hypotheses()}
    assert by_id["H00026"]["status"] == "superseded"
    assert by_id["H00026"]["realized_delta"] == -0.0364, "ölçülmüş delta KORUNMALI"
    assert "ölçülemeden" in by_id["H00029"]["note"], "ölçülemeyen kapanış dürüstçe söylenmeli"
    assert by_id["H00031"]["status"] == "live", "GÜNCEL sürümün hipotezi kapatıldı — hüküm sürüyor"
    assert by_id["H00030"]["status"] == "promoted"


def test_sweep_is_idempotent_and_quiet_when_nothing_is_orphaned(seeded):
    """Kurt masalı yasağı: süpürülecek bir şey yoksa hiçbir şey olmamalı."""
    _strateji(2, parent=1)
    _hyp("H00001", "live", version_to=2)
    assert rollback.sweep_orphan_hypotheses() == []
    assert memory.all_hypotheses()[0]["status"] == "live"


# ---------------- 2) AÇIK DÖNGÜ OLAYI ----------------
def test_unmeasurable_loop_is_an_event_not_silence(seeded):
    """CANLI OLAY: v4'ün ebeveyn satırı karnede yoktu → `par_score=None` → sessiz `return None`,
    her turda, kalıcı olarak. 'Kanıt bekliyorum' ile 'ölçemiyorum' ayırt edilemiyordu."""
    _strateji(4, parent=3)
    g = config.goal()
    n = int(g["min_sample"])
    store.write_jsonl("trades.jsonl", [
        {"id": f"T{i}", "strategy_version": 4, "r_multiple": 0.4, "pnl_dollars": 100.0,
         "ts_open": "2026-01-02", "ts_close": f"2026-01-{2 + (i % 25):02d}", "ticker": "AAA",
         "plan_id": f"P-2026-01-{(i % 25) + 1:02d}-AAA", "regime": "chop", "score": 70,
         "setup": "breakout_vcp"} for i in range(n + 5)])
    store.write_json("scoreboard.json", {"current_version": 4, "versions": {"4": {}}})  # ebeveyn YOK

    assert rollback.evaluate_outcomes(g) is None
    rec = store.read_json(rollback.OPEN_LOOP_FILE, {})
    assert rec.get("reason") == "no_parent_score" and rec.get("n") >= 1
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "learning_loop_open" in blob, "döngü sessizce kapandı — olay yok"


def test_the_open_loop_record_clears_when_the_loop_closes(seeded):
    """Bayat kırmızı bırakma: ölçüm yapılabilir hâle gelince kayıt silinmeli."""
    store.write_json(rollback.OPEN_LOOP_FILE, {"reason": "no_parent_score", "n": 9})
    rollback._close_loop()
    assert store.read_json(rollback.OPEN_LOOP_FILE, {}) == {}


def test_waiting_for_evidence_is_not_reported_as_an_open_loop(seeded):
    """AYRIM: min_sample dolmadıysa bu SABIRDIR, arıza değil — olay üretilmemeli."""
    _strateji(2, parent=1)
    store.write_jsonl("trades.jsonl", [{"id": "T1", "strategy_version": 2, "r_multiple": 0.5}])
    assert rollback.evaluate_outcomes(config.goal()) is None
    assert not store.read_json(rollback.OPEN_LOOP_FILE, {}), "sabır, arıza diye raporlandı"


# ---------------- 3) GEÇİŞ YASASI ----------------
def test_terminal_status_cannot_be_reopened(seeded):
    """`promoted → proposed` öğrenme geçmişini yeniden yazardı ve aynı değişiklik ikinci kez
    aylık kotadan slot yakardı."""
    _hyp("H00001", "promoted", version_to=2)
    assert memory.update_status("H00001", "proposed") is None
    assert memory.all_hypotheses()[0]["status"] == "promoted"


def test_unknown_status_is_refused(seeded):
    _hyp("H00001", "live", version_to=2)
    assert memory.update_status("H00001", "muz") is None
    assert memory.all_hypotheses()[0]["status"] == "live"
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "illegal_hypothesis_status" in blob


def test_legal_forward_transition_still_works(seeded):
    """POZİTİF KONTROL: yasa meşru ilerlemeyi engellememeli."""
    _hyp("H00001", "proposed", version_to=2)
    assert memory.update_status("H00001", "live") is not None
    assert memory.update_status("H00001", "promoted") is not None
    assert memory.all_hypotheses()[0]["status"] == "promoted"


# ---------------- 4) KİMLİK YÜKSEK-SU İŞARETİ ----------------
def test_ids_do_not_rewind_after_a_full_ledger_wipe(seeded):
    """`max+1` KISALMAYA dayanıklıydı ama SİLİNMEYE değil: defter boşalınca numaralar H00001'den
    başlıyor ve ARŞİVLENMİŞ satırlarla çakışıyordu."""
    ilk = [memory.record({"variable": "entry.min_score", "new": 60 + i, "status": "proposed"})["id"]
           for i in range(3)]
    assert ilk[-1] == "H00003"
    store.write_jsonl(memory.HYP, [])                       # defteri TAMAMEN sil
    yeni = memory.record({"variable": "entry.min_score", "new": 70, "status": "proposed"})["id"]
    assert yeni == "H00004", f"kimlik geri sardı: {yeni} (arşivdeki H00004 ile çakışırdı)"


def test_the_high_water_mark_is_monotonic(seeded):
    a = memory.record({"variable": "entry.min_score", "new": 61, "status": "proposed"})["id"]
    store.write_json(memory.ID_HWM_FILE, {"max": 1})        # işareti geri çekmeyi DENE
    b = memory.record({"variable": "entry.min_score", "new": 62, "status": "proposed"})["id"]
    assert int(b[1:]) > int(a[1:]), "işaret geri sardı"
