"""test_memory_audit_v32.py — memory denetimi (2026-07-21, tur 17).

Hipotez defteri = öğrenmenin BELLEĞİ. Bozulursa sistem aynı ölü sonu tekrar tekrar dener. 7. soru:
  ME1 "kimlikler benzersizdir"      → `len(...)+1` kullanılıyordu: defter KISALIRSA (yeniden tohumlama,
     elle temizlik, yarım yazım) kimlikler GERİ SARAR ve iki hipotez aynı kimliği taşır
  ME2 "terfi tek yönlü mandaldır"   → promoted bir satırın sonucu sonradan piyasa sürüklenmesiyle
     yeniden yazılırsa otonomi merdiveninin kalibrasyon kapısı zıplar (audit #21)
  ME3 "durum damgası GEÇİŞLERİ işaretler" → nötr yenileme ship tarihini tazelerse aylık kota kalıcı
     olarak yanlış sayar (audit #20)
"""
from __future__ import annotations

from meridian import memory, store


def _seed(rows):
    store.write_jsonl(memory.HYP, rows)


# ---------- ME1: kimlik tek yönlü ----------
def test_me1_ids_never_rewind_when_the_ledger_shrinks(sandbox_state):
    _seed([{"id": "H00001"}, {"id": "H00002"}, {"id": "H00003"}])
    assert memory.next_id() == "H00004"
    _seed([{"id": "H00003"}])                      # defter kısaldı (yeniden tohumlama)
    assert memory.next_id() == "H00004", "kimlik geri sardı — iki hipotez aynı kimliği taşır"


def test_me1b_ids_survive_non_numeric_rows(sandbox_state):
    _seed([{"id": "H00007"}, {"id": "elle-eklenmis"}, {}])
    assert memory.next_id() == "H00008"


def test_me1c_record_assigns_unique_ids(sandbox_state):
    _seed([])
    ids = {memory.record({"variable": "x", "new": i})["id"] for i in range(5)}
    assert len(ids) == 5


# ---------- ME2: terfi mandalı ----------
def test_me2_promoted_outcome_is_frozen(sandbox_state):
    _seed([{"id": "H1", "version_to": 4, "status": "promoted", "predicted_delta": 0.1,
            "realized_delta": 0.2, "realized_detail": {"n": 40}}])
    out = memory.writeback_outcome(4, realized_delta=-0.9, realized_detail={"n": 99})
    assert out["realized_delta"] == 0.2, "terfi etmiş sonucun üzerine yazıldı (audit #21 nüksü)"


def test_me2b_live_outcome_is_written_once_and_calibration_scored(sandbox_state):
    _seed([{"id": "H1", "version_to": 4, "status": "live", "predicted_delta": 0.1}])
    out = memory.writeback_outcome(4, 0.25, {"n": 40, "market_regime": "chop"})
    assert out["realized_delta"] == 0.25 and out["calibration_hit"] is True
    assert out["market_regime"] == "chop"          # üst düzey, greplenebilir alan
    miss = memory.writeback_outcome(4, -0.3, {"n": 41})
    assert miss["calibration_hit"] is False        # canlı satır güncellenebilir (terfi etmemiş)


def test_me2c_writeback_on_unknown_version_is_none(sandbox_state):
    _seed([{"id": "H1", "version_to": 4, "status": "live"}])
    assert memory.writeback_outcome(9, 0.1, {}) is None


# ---------- ME3: durum damgası ve kota ----------
def test_me3_status_ts_stamps_transitions_only(sandbox_state):
    _seed([{"id": "H1", "status": "live", "status_ts": "2026-01-01T00:00:00+00:00"}])
    memory.update_status("H1", "live", note="nötr yenileme")
    assert memory.all_hypotheses()[0]["status_ts"] == "2026-01-01T00:00:00+00:00"
    memory.update_status("H1", "promoted")
    assert memory.all_hypotheses()[0]["status_ts"] != "2026-01-01T00:00:00+00:00"


def test_me3b_monthly_quota_counts_this_month_only(sandbox_state):
    _seed([{"id": "H1", "status": "live", "status_ts": "2026-07-02T00:00:00+00:00"},
           {"id": "H2", "status": "promoted", "status_ts": "2026-07-20T00:00:00+00:00"},
           {"id": "H3", "status": "live", "status_ts": "2026-06-11T00:00:00+00:00"},
           {"id": "H4", "status": "rejected_by_backtest", "status_ts": "2026-07-05T00:00:00+00:00"}])
    assert memory.accepted_this_month("2026-07-21T00:00:00+00:00") == 2


def test_me3c_lessons_are_regenerated_from_the_ledger(sandbox_state):
    _seed([{"id": "H1", "variable": "entry.min_score", "predicted_direction": "up",
            "status": "rejected_by_backtest", "regime": "chop", "new": 70}])
    text = memory.distill_lessons()
    assert "entry.min_score" in text and isinstance(text, str)
