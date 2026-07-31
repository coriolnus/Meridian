"""test_recompute_v62.py — AYNI SORUYU İKİ YOLDAN (2026-07-22).

Bu dosyanın tek işi şunu kanıtlamak: bir sayı sessizce bozulduğunda, İKİNCİ yol bunu görür.
Testlerin her biri gerçek bir canlı olayın minyatürüdür — uydurma senaryo yok.

Dikkat: her denetimin "temiz" hali de test edilir. Sürekli kırmızı yanan bir dedektör,
operatörün görmezden gelmeyi öğrendiği bir dedektördür; yani hiç olmamasından beterdir.
"""
from __future__ import annotations

import pytest

from meridian import recompute as rc, store
from meridian.score import START_EQUITY


def _row(rep, name):
    return next((r for r in rep["rows"] if r["check"] == name), None)


def _trades(n=10, pnl=100.0):
    return [{"id": f"T{i}", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAA",
             "r_multiple": 0.4, "pnl_dollars": pnl, "plan_id": f"P-2026-01-{i+1:02d}-AAA",
             "regime": "chop", "score": 70, "setup": "breakout_vcp", "strategy_version": 1}
            for i in range(n)]


# ---------- 1) gerçekleşen K/Z: broker muhasebesi ↔ defter ----------
def test_lost_trade_is_caught_by_the_second_path(sandbox_state):
    """Bir işlem defterden düşerse hiçbir istisna fırlamaz; yalnız toplam küçülür. İkinci yol
    (broker'ın koşan muhasebesi) küçülmediği için fark görünür hale gelir."""
    t = _trades(10)
    store.write_jsonl("trades.jsonl", t[:-1])                     # bir satır KAYIP
    store.write_json("portfolio.json", {"cash": START_EQUITY + 1000, "realized_pnl": 1000.0,
                                        "positions": {}})
    r = _row(rc.report(), "realized_pnl")
    assert r and r["ok"] is False
    assert "AYRIŞMA" in r["detail"] and r["a"] == 1000.0 and r["b"] == 900.0


def test_consistent_book_is_quiet(sandbox_state):
    store.write_jsonl("trades.jsonl", _trades(10))
    store.write_json("portfolio.json", {"cash": START_EQUITY + 1000, "realized_pnl": 1000.0,
                                        "positions": {}})
    rep = rc.report()
    assert _row(rep, "realized_pnl")["ok"] is True
    assert _row(rep, "cash_identity")["ok"] is True


def test_cash_identity_breaks_when_book_drifts(sandbox_state):
    store.write_jsonl("trades.jsonl", _trades(10))
    store.write_json("portfolio.json", {"cash": START_EQUITY + 250, "realized_pnl": 1000.0,
                                        "positions": {}})
    assert _row(rc.report(), "cash_identity")["ok"] is False


def test_two_paths_are_genuinely_independent(sandbox_state):
    """Tasarım kuralının testi: iki yol AYNI kaynağı okuyorsa denetim hiçbir şey kanıtlamaz."""
    store.write_jsonl("trades.jsonl", _trades(10))
    store.write_json("portfolio.json", {"cash": START_EQUITY + 1000, "realized_pnl": 1000.0,
                                        "positions": {}})
    for r in rc.report()["rows"]:
        assert r["a_yol"] and r["b_yol"], r
        assert r["a_yol"] != r["b_yol"], f"{r['check']}: iki yol aynı — bu denetim değersiz"


# ---------- 4) karne ↔ defter ----------
def test_scoreboard_sample_mismatch_is_caught(sandbox_state):
    """Karnedeki n, terfi/geri-alma kararının dayanağı. Yanlış n = yanlış skor = yanlış karar."""
    store.write_jsonl("trades.jsonl", _trades(10))
    store.write_json("scoreboard.json", {"current_version": "4",
                                         "versions": {"4": {"n_trades": 90}}})
    r = _row(rc.report(), "scoreboard_n_trades")
    assert r["ok"] is False and r["a"] == 90 and r["b"] == 10


# ---------- 5) karşı-olgusal korunumu ----------
def test_double_counted_evidence_is_caught(sandbox_state):
    """cf_backfill iki kez koşarsa aynı kanıt iki kez sayılır ve her kalibrasyon şişer.
    Canlıda bu riske karşı dedup eklendi; burada dedup'ın BOZULMASI yakalanıyor."""
    rows = [{"id": f"CF-2026-01-{i+1:02d}-AAA-x", "date": "2026-01-02", "ticker": "AAA",
             "setup": "breakout_vcp", "regime": "chop", "status": "closed"} for i in range(6)]
    store.write_jsonl("counterfactuals.jsonl", rows + rows[:2])          # 2 satır TEKRAR
    store.write_json("cf_open.json", [rows[0]])                          # 1 kimlik İKİ kümede
    r = _row(rc.report(), "cf_conservation")
    assert r["ok"] is False and "çift sayılıyor" in r["detail"]


# ---------- 6) kalibrasyon paydası: "gerçek 0 / simüle 241" ----------
def test_silently_dropped_rows_show_up_as_a_shrunken_denominator(sandbox_state):
    """CANLI OLAY: trades.jsonl satırlarında score/setup yoktu → 90 gerçek işlemin 90'ı da
    kalibrasyondan sessizce elendi. Tüketici 'n_real: 0' yazdı, kaynakta 90 satır vardı."""
    store.write_jsonl("trades.jsonl", _trades(90))
    store.write_jsonl("counterfactuals.jsonl",
                      [{"id": f"CF-2026-01-01-A{i}", "date": "2026-01-02", "ticker": "AAA",
                        "setup": "breakout_vcp", "regime": "chop", "status": "closed",
                        "entered": True, "r_multiple": 0.3} for i in range(200)])
    store.write_json("score_calibration.json", {"n": 200, "n_real": 0, "n_cf": 200})
    rep = rc.report()
    assert _row(rep, "calibration_real_denominator")["ok"] is False
    assert "GERÇEK işlemler kalibrasyona girmiyor" in _row(rep, "calibration_real_denominator")["detail"]
    assert _row(rep, "calibration_denominator")["ok"] is True     # cf tarafı sağlam → sessiz kalmalı


def test_cf_denominator_shrink_is_caught(sandbox_state):
    store.write_jsonl("counterfactuals.jsonl",
                      [{"id": f"CF-2026-01-01-A{i}", "date": "2026-01-02", "ticker": "AAA",
                        "setup": "breakout_vcp", "regime": "chop", "status": "closed",
                        "entered": True, "r_multiple": 0.3} for i in range(200)])
    store.write_json("score_calibration.json", {"n": 40, "n_real": 0, "n_cf": 40})
    r = _row(rc.report(), "calibration_denominator")
    assert r["ok"] is False and "SESSİZCE elenmiş" in r["detail"]


# ---------- 7) hipotez kimliği geri sarmaz ----------
def test_reused_hypothesis_id_is_caught(sandbox_state):
    """Kimlik geri sararsa geçmiş üzerine yazılır ve öğrenme kaydı sessizce yok olur
    (canlıda wf_rev sayacı 4→1 geri sardı — aynı sınıf)."""
    store.write_jsonl("hypotheses.jsonl", [{"id": "H00001", "ts": "t", "variable": "v",
                                            "status": "proposed"} for _ in range(5)])
    r = _row(rc.report(), "hypothesis_ids")
    assert r["ok"] is False and "GERİ SARMIŞ" in r["detail"]


# ---------- boş durum dürüstlüğü ----------
def test_empty_state_makes_no_claims(sandbox_state):
    """Veri yokken dedektör HİÇBİR ihlal uydurmamalı. Yalnız her-turda-koşan orphan taraması
    çalışır (boş dizinde 0 orphan → temiz); veri-bağımlı denetimlerin hepsi susar."""
    rep = rc.report()
    assert rep["ok"] is True
    assert all(r["ok"] for r in rep["rows"])
    # veri-bağımlı hiçbir denetim örneklem olmadan konuşmaz — yalnız orphan taraması kalır
    assert {r["check"] for r in rep["rows"]} <= {"orphan_state_files"}


# ---------- dedektörün kendi arızası sessiz kalmaz ----------
def test_detector_failure_is_itself_a_finding(sandbox_state, monkeypatch):
    """En sinsi hata, sessiz-hata dedektörünün İÇİNDEKİ sessiz hataydı (starved olayı).
    Yeniden hesap çalışamazsa bu 'temiz' değil, BULGU olarak raporlanır."""
    import meridian.recompute as _rc
    monkeypatch.setattr(_rc, "_start_equity", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    store.write_jsonl("trades.jsonl", _trades(3))
    store.write_json("portfolio.json", {"cash": 1.0, "realized_pnl": 300.0, "positions": {}})
    with pytest.raises(RuntimeError):
        _rc.report()          # sessizce yutulmuyor: yukarı fırlıyor ve görünür oluyor


def test_deep_universe_recompute_reports_its_own_blindness(sandbox_state):
    """deep hesap kaynaksız kalırsa 'temiz' demez — ne yapamadığını söyler."""
    r = rc._universe_recompute()
    assert r["check"] == "universe_recompute"
    assert r["detail"] and ("yeniden hesap yapılmadı" in r["detail"] or "ÇALIŞMADI" in r["detail"]
                            or "seans" in r["detail"])


# ---------- makullük dedektörüne bağlı mı ----------
def test_wired_into_the_parity_detector(sandbox_state):
    """Üretilip tüketilmeyen kanıt, bu denetimin bulduğu hata sınıfının kendisi."""
    from meridian import watchdog as wd
    store.write_jsonl("trades.jsonl", _trades(10))
    store.write_json("portfolio.json", {"cash": START_EQUITY, "realized_pnl": 400.0,
                                        "positions": {}})     # defter 1000$, muhasebe 400$
    checks = [r["check"] for r in wd.parity_report()["rows"]]
    assert "yeniden_hesap:realized_pnl" in checks
    bad = next(r for r in wd.parity_report()["rows"] if r["check"] == "yeniden_hesap:realized_pnl")
    assert bad["ok"] is False and "A=" in bad["detail"]      # iki yol panoda görünür
