"""test_earnings_audit_v26.py — earnings denetimi (2026-07-21, tur 11).

7. soru:
  E1 "in_blackout False = temiz"      → 'kontrol edildi, temiz' ile 'HİÇ VERİ YOK' aynı görünüyordu.
     CANLI: 250 sembollük evrenin 181'i biliniyor; kalan 69'unda guard sessizce KAPALI
  E2 "takvim güncel kalır"            → gelecek tarih kalmazsa (bayat dosya) guard HERKES için kapanır
     ve 'sert guard' listede görünmeye devam ederdi
"""
from __future__ import annotations

import datetime as dt
import inspect

from meridian import earnings, watchdog


def _write(sandbox, rows):
    (sandbox / "earnings.csv").write_text("ticker,date\n" + "".join(f"{t},{d}\n" for t, d in rows))
    earnings.clear_cache()


# ---------- E1: bilinmiyor ≠ temiz ----------
def test_e1_known_separates_unknown_from_clear(sandbox_state):
    fut = (dt.date.today() + dt.timedelta(days=40)).isoformat()
    _write(sandbox_state, [("AAA", fut)])
    assert earnings.known("AAA") is True and earnings.known("BBB") is False
    assert earnings.in_blackout("AAA", dt.date.today().isoformat()) is False   # temiz (40 gün uzak)
    assert earnings.in_blackout("BBB", dt.date.today().isoformat()) is False   # ama BU 'veri yok'


def test_e1b_coverage_counts_the_unprotected_names(sandbox_state):
    fut = (dt.date.today() + dt.timedelta(days=10)).isoformat()
    _write(sandbox_state, [("AAA", fut), ("BBB", fut)])
    cov = earnings.coverage(["AAA", "BBB", "CCC", "DDD"])
    assert cov["known_tickers"] == 2 and cov["unknown"] == 2 and cov["covered_pct"] == 50.0
    assert "CCC" in cov["unknown_sample"]


def test_e1c_plan_log_records_calendar_coverage():
    from meridian import loop
    src = inspect.getsource(loop.daily_cycle)
    assert 'earnings.known(' in src and '"coverage": "known" if _ek else "no_calendar_data"' in src


# ---------- E2: bayat takvim = kapalı guard ----------
def test_e2_stale_calendar_is_reported_inert(sandbox_state):
    past = (dt.date.today() - dt.timedelta(days=60)).isoformat()
    _write(sandbox_state, [("AAA", past), ("BBB", past)])
    cov = earnings.coverage()
    assert cov["inert"] is True and cov["future_dates"] == 0
    rep = watchdog.production_report()
    assert any(s["name"] == "earnings_calendar" for s in rep["starved"]), \
        "bayat takvim 'aç kalmış mekanizma' olarak görünmeli"


def test_e2b_fresh_calendar_is_not_flagged(sandbox_state):
    fut = (dt.date.today() + dt.timedelta(days=20)).isoformat()
    _write(sandbox_state, [("AAA", fut)])
    assert earnings.coverage()["inert"] is False
    assert not any(s["name"] == "earnings_calendar" for s in watchdog.production_report()["starved"])


# ---------- guard davranışı kilitli ----------
def test_blackout_window_boundaries(sandbox_state):
    today = dt.date.today()
    _write(sandbox_state, [("AAA", (today + dt.timedelta(days=5)).isoformat())])
    assert earnings.in_blackout("AAA", today.isoformat()) is True            # 5 gün = sınır İÇİNDE
    _write(sandbox_state, [("AAA", (today + dt.timedelta(days=6)).isoformat())])
    assert earnings.in_blackout("AAA", today.isoformat()) is False           # 6 gün = dışında
    _write(sandbox_state, [("AAA", (today - dt.timedelta(days=1)).isoformat())])
    assert earnings.in_blackout("AAA", today.isoformat()) is False           # GEÇMİŞ rapor engellemez


def test_radar_says_empty_instead_of_pretending_clear(sandbox_state):
    (sandbox_state / "earnings.csv").unlink(missing_ok=True)
    earnings.clear_cache()
    r = earnings.blackout_radar(["AAA"], dt.date.today().isoformat())
    assert r["empty"] is True and r["blackout"] == []


def test_cache_follows_file_mtime(sandbox_state):
    fut = (dt.date.today() + dt.timedelta(days=3)).isoformat()
    _write(sandbox_state, [("AAA", fut)])
    assert earnings.in_blackout("AAA", dt.date.today().isoformat()) is True
    _write(sandbox_state, [("ZZZ", fut)])
    assert earnings.in_blackout("AAA", dt.date.today().isoformat()) is False   # yeniden yazım görüldü


# ---------- dedektörün kendisi: eklenen kontroller GERÇEKTEN koşuyor mu? ----------
def test_extra_starved_checks_actually_run(sandbox_state, monkeypatch):
    """Bu denetim sırasında BULUNDU: sonradan eklenen iki kontrol (`sp500_membership`,
    `earnings_calendar`) `starved` listesi TANIMLANMADAN önce yazılmıştı → NameError, ve blokların
    `except Exception: pass`'i onu yutuyordu. Yani sessiz-hata dedektörünün içinde sessiz hata vardı."""
    from meridian.adapters import constituents as con
    monkeypatch.setattr(con, "health", lambda: {"ok": False, "error": "HTTP 403"})
    names = [s["name"] for s in watchdog.production_report()["starved"]]
    assert "sp500_membership" in names


def test_detector_failure_is_not_swallowed(sandbox_state, monkeypatch):
    from meridian.adapters import constituents as con
    monkeypatch.setattr(con, "health", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    names = [s["name"] for s in watchdog.production_report()["starved"]]
    assert "sp500_membership" in names          # dedektör çökse bile SESSİZ kalmaz
