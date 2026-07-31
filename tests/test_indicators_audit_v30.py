"""test_indicators_audit_v30.py — indicators denetimi (2026-07-21, tur 15).

7. soru: modül "her fonksiyon deterministik ve ileri-dönük değil" diyor — ama bunu KANITLAYAN bir
test yoktu. Tek bir merkezi rolling (center=True), bir bfill ya da bir shift(-1) her şeyi sessizce
bozar: backtest'te muhteşem, canlıda ölü bir strateji üretir ve mevcut testlerin hiçbiri kırılmaz.

  I1 ÖNEK KARARLILIĞI: bir seriyi KESİP hesaplayınca, örtüşen indekslerdeki değerler DEĞİŞMEMELİ.
     (Geleceği kullanan her formül burada patlar.)
  I2 rs_rating çapraz-kesitseldir (tasarım gereği tüm evreni görür) → sınır + determinizm testi
  I3 yetersiz veri → NaN/None, UYDURMA değer değil (Hard Rule 7)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from meridian import indicators as ind
from tests.conftest import make_bars


BARS = make_bars(320, seed=11, trend=0.0007, breakout_at=250)
SERIES_FNS = {
    "true_range": lambda df: ind.true_range(df),
    "atr": lambda df: ind.atr(df, 14),
    "sma50": lambda df: ind.sma(df["close"], 50),
    "trailing_return": lambda df: ind.trailing_return(df["close"], 60),
    "volume_ratio": lambda df: ind.volume_ratio(df["volume"], 50),
    "pivot_high": lambda df: ind.pivot_high(df["high"], 40, 1),
    "trend_template": lambda df: ind.trend_template(df),
}


@pytest.mark.parametrize("name", sorted(SERIES_FNS))
def test_i1_prefix_stability_no_lookahead(name):
    """ALTIN KURAL: geçmişin değeri, gelecekteki barlar eklendiğinde DEĞİŞMEZ."""
    fn = SERIES_FNS[name]
    full = fn(BARS)
    cut = fn(BARS.iloc[:250].copy())
    a = full.iloc[:250].to_numpy(dtype=float)
    b = cut.to_numpy(dtype=float)
    same = np.isclose(a, b, rtol=1e-12, atol=1e-12, equal_nan=True)
    assert same.all(), f"{name}: {int((~same).sum())} değer gelecekteki barlarla DEĞİŞTİ → ileri-dönük"


@pytest.mark.parametrize("name", sorted(SERIES_FNS))
def test_i1b_deterministic(name):
    fn = SERIES_FNS[name]
    x, y = fn(BARS), fn(BARS)
    assert np.isclose(x.to_numpy(dtype=float), y.to_numpy(dtype=float), equal_nan=True).all()


def test_i3_insufficient_data_is_nan_not_a_guess():
    short = BARS.iloc[:10].copy()
    assert pd.isna(ind.atr(short, 14).iloc[-1])
    assert pd.isna(ind.sma(short["close"], 50).iloc[-1])
    assert pd.isna(ind.trend_template(short).iloc[-1]) or ind.trend_template(short).iloc[-1] == 0.0


def test_pivot_high_excludes_the_current_bar():
    """Kırılım pivotu BUGÜNÜN yükseğini içerirse her bar kendi kendine 'kırılım' olur."""
    df = BARS.copy()
    df.loc[df.index[-1], "high"] = df["high"].max() * 5           # bugün uçtu
    piv = ind.pivot_high(df["high"], 40, 1)
    assert piv.iloc[-1] < df["high"].iloc[-1], "pivot bugünün yükseğini içeriyor (kendi kendine kırılım)"


def test_trend_template_is_a_fraction():
    v = ind.trend_template(BARS).dropna()
    assert len(v) and float(v.min()) >= 0.0 and float(v.max()) <= 1.0


# ---------- I2: çapraz-kesitsel RS ----------
def test_i2_rs_rating_bounds_and_order():
    rets = {"A": 0.5, "B": 0.1, "C": -0.2, "D": 0.0}
    r = ind.rs_rating(rets)
    assert set(r) == set(rets)
    assert all(1 <= v <= 99 for v in r.values())
    assert r["A"] > r["B"] > r["D"] > r["C"]                      # sıralama korunur


def test_i2b_rs_rating_deterministic_and_tie_stable():
    rets = {"A": 0.2, "B": 0.2, "C": 0.1}
    assert ind.rs_rating(rets) == ind.rs_rating(rets)
    assert ind.rs_rating(rets)["A"] == ind.rs_rating(rets)["B"]   # beraberlik aynı puanı alır


def test_i2c_rs_rating_handles_degenerate_input():
    assert ind.rs_rating({}) == {}
    one = ind.rs_rating({"A": 0.3})
    assert set(one) == {"A"} and 1 <= one["A"] <= 99


# ---------- korelasyon ----------
def test_corr_max_needs_enough_points():
    c = BARS["close"]
    assert ind.corr_max(c, [], 60, 20) == 0.0                     # karşılaştıracak bir şey yok
    tiny = [np.array([0.01, -0.02, 0.03])]
    assert ind.corr_max(c, tiny, 60, 20) == 0.0                   # min_pts altında UYDURMA yok


def test_corr_max_detects_a_perfect_twin():
    c = BARS["close"]
    twin = ind.returns_tail(c, 60)
    assert ind.corr_max(c, [twin], 60, 20) == pytest.approx(1.0, abs=1e-6)


def test_i2d_rs_rating_is_independent_of_input_order():
    """Aynı evren, farklı sırayla verilince AYNI puanlar çıkmalı — aksi halde sözlük sırası bir
    sembolü silahlandırıp diğerini eleyebilir (rs_rating_min sert eşik)."""
    rets = {"A": 0.3, "B": 0.3, "C": 0.1, "D": -0.4, "E": 0.0}
    shuffled = {k: rets[k] for k in ("D", "B", "E", "A", "C")}
    assert ind.rs_rating(rets) == ind.rs_rating(shuffled)
