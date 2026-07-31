"""test_broker_audit_v24.py — broker denetimi (2026-07-21, tur 9).

broker, SAYILAN P&L'i üreten yer. 7. soru:
  K1 "muhasebe kapanıyor"     → özdeşlik hiçbir yerde İDDİA EDİLMİYORDU: tüm pozisyonlar kapandığında
     equity() == start + Σ pnl_dollars olmalı. Bu tam olarak bir kez KIRILDI (H1: kayma iki kez
     ücretlendirildi → kapı bir öz sermayeyi, devre kesici başka birini okuyordu) ve testler susmuştu.
  K2 "stop asla gevşemez"     → iz süren stop yalnız YUKARI gitmeli; kural manage_position içinde
     dağınık (üç ayrı max()) ama sınırda tek bir iddia yoktu
  K3 "kısmi satış tek satır"  → scale_out banked_pnl'i final satıra katlamalı; aksi halde min_sample
     ve fold n'leri sessizce şişerdi
"""
from __future__ import annotations

import pandas as pd
import pytest

from meridian import backtest, config, strategy
from meridian.broker import PaperBroker, derisk_mult, max_positions_at
from tests.conftest import make_bars


def _plan(tid="P1", ticker="AAA", trigger=100.0, stop=95.0, target=115.0, size_r=1.0):
    return {"id": tid, "ticker": ticker, "entry_trigger": trigger, "stop": stop,
            "profit_target": target, "size_r": size_r}


# ---------- K1: muhasebe özdeşliği ----------
def test_k1_accounting_identity_after_close():
    b = PaperBroker(equity=100_000, slippage_bps=5, commission_per_share=0.005)
    pos = b.fill_entry(_plan(), next_open=100.0, ts="2026-01-02", equity=100_000)
    assert pos is not None
    row = b.close_position("AAA", raw_exit=110.0, reason="target", ts="2026-01-09")
    assert b.equity() == pytest.approx(100_000 + row["pnl_dollars"], abs=0.01)
    assert b.realized_pnl == pytest.approx(row["pnl_dollars"], abs=0.01)


def test_k1b_identity_holds_across_many_trades_including_scale_out():
    """ASIL koruma: çok işlemli bir dizide (kısmi satış dahil) broker öz sermayesi kapalı satırların
    toplamıyla BİREBİR tutmalı. H1 hatası (kaymanın ikinci kez ücretlenmesi) tam burada patlardı:
    kapı pnl_dollars'ı, devre kesici realized_pnl'i okuyordu ve ikisi kaymanın tam kadarı ayrılmıştı."""
    b = PaperBroker(equity=100_000, slippage_bps=7, commission_per_share=0.005)
    seq = [("AAA", 100.0, 95.0, 115.0, 112.0, "target"),
           ("BBB", 50.0, 47.0, 60.0, 46.5, "stop"),
           ("CCC", 200.0, 190.0, 230.0, 205.0, "time_stop")]
    for i, (tk, op, st, tg, ex, why) in enumerate(seq):
        pos = b.fill_entry(_plan(f"P{i}", tk, op, st, tg), next_open=op, ts="2026-01-02",
                           equity=b.equity())
        assert pos is not None
        if tk == "CCC":                                        # bir tanesinde kısmi satış da olsun
            b.scale_out(pos, {"open": op * 1.05, "high": op + 2.2 * pos.r_per_share,
                              "low": op * 1.04, "close": op * 1.06},
                        {"exit.scale_out_frac": 0.4, "exit.scale_out_r": 2.0})
        b.close_position(tk, raw_exit=ex, reason=why, ts="2026-01-10")
    total = sum(r["pnl_dollars"] for r in b.closed)
    assert len(b.closed) == 3                                  # kısmi satış EKSTRA satır üretmedi
    assert b.equity() == pytest.approx(100_000 + total, abs=0.02)
    assert b.realized_pnl == pytest.approx(total, abs=0.02)


def test_k1c_scale_out_is_folded_into_one_row():
    """K3: kısmi satış AYRI bir işlem satırı üretmemeli — üretirse n şişer, min_sample yalan söyler."""
    b = PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos = b.fill_entry(_plan(), next_open=100.0, ts="2026-01-02", equity=100_000)
    params = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0}
    bar = {"open": 108.0, "high": 112.0, "low": 107.0, "close": 111.0}
    assert b.scale_out(pos, bar, params) is True
    assert len(b.closed) == 0                                  # kısmi satış SATIR ÜRETMEZ
    row = b.close_position("AAA", raw_exit=112.0, reason="target", ts="2026-01-10")
    assert len(b.closed) == 1
    assert row["scaled_out"] is True
    assert row["pnl_dollars"] == pytest.approx(b.realized_pnl, abs=0.01)   # bankalanan da içinde


# ---------- K2: stop monotonluğu ----------
def test_k2_trail_never_loosens():
    bars = make_bars(120, seed=5, trend=0.002)
    params = config.default_strategy()["params"]
    pos = {"entry": float(bars["close"].iloc[60]), "stop": float(bars["close"].iloc[60]) * 0.95,
           "r_per_share": float(bars["close"].iloc[60]) * 0.05,
           "trail_stop": float(bars["close"].iloc[60]) * 0.95}
    prev = pos["trail_stop"]
    for i in range(61, 120):
        dec = strategy.manage_position(bars.iloc[:i + 1], pos, params, bars_held=i - 60, regime_ok=True)
        assert dec.trail_stop >= prev - 1e-9, f"iz süren stop GEVŞEDİ: {prev} → {dec.trail_stop}"
        assert dec.trail_stop >= pos["stop"] - 1e-9, "trail sert stop'un ALTINA indi"
        prev = dec.trail_stop
        pos["trail_stop"] = dec.trail_stop
        if dec.exit_now:
            break


def test_k2b_scale_out_ratchets_to_breakeven():
    b = PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos = b.fill_entry(_plan(), next_open=100.0, ts="2026-01-02", equity=100_000)
    before = pos.trail_stop
    b.scale_out(pos, {"open": 108.0, "high": 112.0, "low": 107.0, "close": 111.0},
                {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0})
    assert pos.trail_stop >= before and pos.trail_stop >= pos.entry


def test_k2c_scale_out_refused_when_bar_breached_the_stop():
    """Kayıt: aynı bar hem stop'u hem +2R'yi görüyorsa OHLC sırasını bilemeyiz — iyimser bankalama yasak."""
    b = PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos = b.fill_entry(_plan(), next_open=100.0, ts="2026-01-02", equity=100_000)
    bar = {"open": 108.0, "high": 112.0, "low": 90.0, "close": 95.0}      # low stop'u kırdı
    assert b.scale_out(pos, bar, {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0}) is False


# ---------- risk kısıcıları: sürekli ve monoton ----------
def test_derisk_is_monotone_and_continuous():
    prev = 1.0
    for i in range(0, 101):
        dd = i / 1000.0                                        # %0 → %10 drawdown
        m = derisk_mult(100_000 * (1 - dd), 100_000)
        assert 0.0 <= m <= 1.0 and m <= prev + 1e-9, "de-risk çarpanı drawdown arttıkça ARTAMAZ"
        prev = m
    assert derisk_mult(92_000, 100_000) == 0.0                 # %8 tabanında sıfır
    assert max_positions_at(92_000, 100_000, 5) == 0
    assert max_positions_at(100_000, 100_000, 5) == 5


def test_entry_guards_block_chasing_and_gap_through_stop():
    b = PaperBroker(equity=100_000, slippage_bps=5, commission_per_share=0.005)
    assert b.fill_entry(_plan(), next_open=120.0, ts="t", equity=100_000) is None    # %20 gap → kovalama yok
    assert b.fill_entry(_plan(), next_open=94.0, ts="t", equity=100_000) is None     # stop'un altında açılış
    assert b.fill_entry(_plan(), next_open=100.5, ts="t", equity=100_000) is not None


def test_notional_cap_bounds_single_name():
    b = PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos = b.fill_entry(_plan(stop=99.9), next_open=100.0, ts="t", equity=100_000)     # çok dar stop
    assert pos is not None
    assert pos.qty * pos.entry <= 0.25 * 100_000 + 1e-6                               # MAX_NOTIONAL_PCT
