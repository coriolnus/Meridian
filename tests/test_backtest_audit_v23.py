"""test_backtest_audit_v23.py — backtest denetimi (2026-07-21, tur 8).

backtest KAPININ TA KENDİSİ: her öğrenme kararı bu sayılara dayanıyor. 7. soru:
  B1 "ileri-dönük veri sızmıyor"   → docstring'de ANLATILIYOR, hiçbir yerde KANITLANMIYORDU.
     Kanıt yöntemi: geleceği KESİP aynı replay'i koş — geçmişteki işlemler BİREBİR aynı çıkmalı.
     Tek bir 'df.iloc[i+1]' hatası bu testi kırar, ama eski testlerden hiçbirini kırmazdı.
  B2 "aynı girdi aynı sonuç"        → kapı iki tarafı kıyaslıyor; replay deterministik değilse
     kıyas gürültü ölçer (bu oturumda incumbent 0.2043→0.0988 sürüklenmesi tam da buydu)
  B3 "sektör haritası evreni kapsar" → SECTORS elle bakımlı; evren değişince (bu hafta 7 sembol
     değişti) haritada delik kalırsa o isimler tek '?' kovasına düşer ve sektör tavanı yanlış çalışır
"""
from __future__ import annotations

import pandas as pd
import pytest

from meridian import backtest, config
from meridian.adapters.data import REPLAY_UNIVERSE
from tests.conftest import make_bars


PARAMS = config.default_strategy()["params"]


def _universe():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def _cut(df, cutoff):
    return df[df["date"] <= pd.Timestamp(cutoff)].reset_index(drop=True)


def _rows(trades):
    return [(t.get("ticker"), str(t.get("ts_open"))[:10], str(t.get("ts_close"))[:10],
             round(float(t.get("entry") or 0), 6), round(float(t.get("exit") or 0), 6))
            for t in trades]


# ---------- B1: ileri-dönük sızıntı ----------
def test_b1_truncating_the_future_does_not_change_the_past():
    """ALTIN KURAL testi: 2023-01-01'den sonrasını hiç görmeyen bir koşu, gören koşuyla AYNI
    geçmiş işlemleri üretmeli. Fark çıkarsa motor geleceğe bakıyor demektir."""
    bars, idx = _universe()
    cutoff = "2023-01-01"
    full = backtest.replay(PARAMS, bars, idx, config.goal(), "2022-06-01", cutoff, strategy_version=1)
    cut_bars = {t: _cut(df, cutoff) for t, df in bars.items()}
    blind = backtest.replay(PARAMS, cut_bars, _cut(idx, cutoff), config.goal(),
                            "2022-06-01", cutoff, strategy_version=1)
    assert _rows(full.trades) == _rows(blind.trades)


def test_b1b_plan_log_is_also_future_blind():
    bars, idx = _universe()
    cutoff = "2023-01-01"
    full = backtest.replay(PARAMS, bars, idx, config.goal(), "2022-06-01", cutoff, strategy_version=1)
    cut_bars = {t: _cut(df, cutoff) for t, df in bars.items()}
    blind = backtest.replay(PARAMS, cut_bars, _cut(idx, cutoff), config.goal(),
                            "2022-06-01", cutoff, strategy_version=1)
    key = lambda log: [(p["date"], p.get("ticker"), p["gate_verdict"]) for p in log]
    assert key(full.plan_log) == key(blind.plan_log)


def test_b1c_entry_is_never_filled_on_the_signal_bar():
    """Kural: D kapanışında silahlanan emir EN ERKEN D+1 açılışında dolar."""
    bars, idx = _universe()
    res = backtest.replay(PARAMS, bars, idx, config.goal(), "2022-06-01", "2023-06-01", strategy_version=1)
    armed = {(p["date"], p.get("ticker")) for p in res.plan_log if p.get("gate_verdict") == "GO"}
    for t in res.trades:
        assert (str(t.get("ts_open"))[:10], t.get("ticker")) not in armed, \
            "giriş, sinyalin doğduğu barın kendisinde dolmuş — ileri-dönük dolum"


# ---------- B2: determinizm ----------
def test_b2_replay_is_deterministic():
    bars, idx = _universe()
    a = backtest.replay(PARAMS, bars, idx, config.goal(), "2022-06-01", "2023-06-01", strategy_version=1)
    b = backtest.replay(PARAMS, bars, idx, config.goal(), "2022-06-01", "2023-06-01", strategy_version=1)
    assert _rows(a.trades) == _rows(b.trades) and len(a.plan_log) == len(b.plan_log)


def test_b2b_walk_forward_is_deterministic():
    bars, idx = _universe()
    args = (PARAMS, bars, idx, config.goal(), "2022-06-01", "2022-10-01", "2023-04-01", "2023-06-01")
    kw = {"oos_folds": ["2022-10-01", "2023-01-01", "2023-04-01"], "embargo_days": 5}
    w1 = backtest.walk_forward(*args, **kw)
    w2 = backtest.walk_forward(*args, **kw)
    assert w1["oos_score"] == w2["oos_score"]
    assert [f["avg_r"] for f in w1["oos_folds"]] == [f["avg_r"] for f in w2["oos_folds"]]


def test_b2c_param_change_actually_changes_the_result():
    """Determinizm testinin ikizi: motor girdiye DUYARLI mı? (Hep aynı sonucu veren bir motor da
    'deterministik'tir ama hiçbir şey ölçmez.)"""
    bars, idx = _universe()
    p2 = {**PARAMS, "stop_loss_atr_mult": float(PARAMS.get("stop_loss_atr_mult", 2.0)) * 2.0}
    a = backtest.replay(PARAMS, bars, idx, config.goal(), "2022-06-01", "2023-06-01", strategy_version=1)
    b = backtest.replay(p2, bars, idx, config.goal(), "2022-06-01", "2023-06-01", strategy_version=1)
    assert _rows(a.trades) != _rows(b.trades) or not a.trades


# ---------- B3: sektör haritası ----------
def test_b3_sector_map_covers_the_universe_exactly():
    missing = [t for t in REPLAY_UNIVERSE if t not in backtest.SECTORS]
    extra = [t for t in backtest.SECTORS if t not in REPLAY_UNIVERSE]
    assert not missing, f"sektör haritasında YOK: {missing} → hepsi '?' kovasına düşer, tavan yanlış çalışır"
    assert not extra, f"evrende olmayan sembol haritada: {extra}"


def test_b3b_live_and_backtest_share_one_map():
    """Kapı canlıyla aynı haritayı kullanmalı; iki ayrı harita = kapının ölçtüğü tavan canlıda yok."""
    from meridian import loop
    assert loop.SECTORS is backtest.SECTORS
