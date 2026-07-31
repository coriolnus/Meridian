"""test_canslim_v94 — O'Neil CANSLIM büyüme-lideri (FMP-kapılı, Faz C: helper'ın arkasında DORMANT).

canslim'in ayrımı: N/S/L teknik bileşenleri OHLCV'den deterministik, ama C/A/I çekirdeği TEMELE (FMP)
dayanır. `earnings.canslim_fundamentals` + FMP nokta-zamanlı önbelleği HENÜZ inşa edilmedi → evaluate_canslim
bugün DAİMA None (güvenli no-op). Bu yüzden scan_all'a KOŞAR ama 'canslim-screener' ENGINE_IMPLEMENTED'a
EKLENMEZ (pipeline_run 'invoked' yalanı kurmasın). Helper eklenince setup GERÇEKTEN ateşler — bunu
monkeypatch'le kanıtlıyoruz: kör kod değil, veri-kapılı gerçek bir setup.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import meridian.strategy as strat
import meridian.skills as skills
import meridian.earnings as earn
from meridian.guard import DISCIPLINE_MIN_RR


def _leader_bars(n: int = 300, seed: int = 7) -> pd.DataFrame:
    """252+ barlık trend-şablonu geçen bir lider; 52-hafta zirvesinde hacim-teyitli kırılım günü; son 60
    barda hem yukarı hem aşağı günler (birikim ölçülebilsin), up-günü hacmi daha yüksek (accumulation)."""
    rng = np.random.default_rng(seed)
    rets = 0.004 + rng.normal(0, 0.011, n)
    close = 100.0 * np.cumprod(1 + rets)
    close[-1] = max(close[-1], close[:-1].max() * 1.002)     # taze 52-hafta zirvesi
    openp = close / (1 + rets * 0.5)
    high = np.maximum(openp, close) * (1 + np.abs(rng.normal(0, 0.003, n)))
    low = np.minimum(openp, close) * (1 - np.abs(rng.normal(0, 0.003, n)))
    up = np.r_[True, np.diff(close) > 0]
    vol = np.where(up, 2.2e6, 1.1e6) + rng.integers(0, 200000, n)
    vol[-1] = 3.5e6; high[-1] = close[-1] * 1.001            # kırılım-günü hacmi (vr≥1.4)
    return pd.DataFrame({"date": pd.bdate_range("2021-01-04", periods=n), "open": openp, "high": high,
                         "low": low, "close": close, "volume": vol.astype(float)})


_GOOD_FUND = {"eps_qoq_growth": 42.0, "eps_cagr_3yr": 33.0, "inst_ownership": 55.0}


def test_dormant_no_op_without_helper():
    """Helper YOKKEN (bugünün gerçek durumu) her girdide None — güvenli no-op."""
    assert not hasattr(earn, "canslim_fundamentals"), "helper beklenmedik biçimde mevcut"
    assert strat.evaluate_canslim(_leader_bars(), {}, 95, "T") is None
    assert strat.evaluate_canslim(_leader_bars(120), {}, 95, "T") is None   # <252 bar da None


def test_scan_all_unchanged_by_dormant_canslim():
    """canslim scan_all'da KOŞAR ama helper yokken çıktıya HİÇBİR anahtar eklemez → determinizm korunur."""
    df = _leader_bars()
    by_setup = strat.scan_all(df, {}, 95, "T")
    assert "canslim" not in by_setup


def test_not_engine_implemented_until_helper():
    """DÜRÜSTLÜK KAPISI: veri yolu yapısal olarak yokken 'invoked' loglanmamalı (declared-only kalır)."""
    assert "canslim-screener" not in skills.ENGINE_IMPLEMENTED


def test_fires_when_helper_present(monkeypatch):
    """Helper eklenince (Faz C simülasyonu) setup GERÇEKTEN ateşler → kör kod değil, veri-kapılı gerçek setup."""
    monkeypatch.setattr(earn, "canslim_fundamentals", lambda t, d: dict(_GOOD_FUND), raising=False)
    sig = strat.evaluate_canslim(_leader_bars(), {}, 95, "T")
    assert sig is not None, "temel veri sağlanınca ateşlemeliydi"
    assert sig.setup == "canslim"
    assert sig.stop < sig.entry_trigger < sig.profit_target
    assert sig.r_per_share > 0
    rr = (sig.profit_target - sig.entry_trigger) / sig.r_per_share
    assert rr >= DISCIPLINE_MIN_RR - 1e-9


def test_no_fabricated_growth(monkeypatch):
    """C/A çekirdeği eksik temel veriyle UYDURULMAZ: eps_qoq/eps_cagr yoksa (helper var ama boş) None."""
    monkeypatch.setattr(earn, "canslim_fundamentals", lambda t, d: {"inst_ownership": 55.0}, raising=False)
    assert strat.evaluate_canslim(_leader_bars(), {}, 95, "T") is None
    monkeypatch.setattr(earn, "canslim_fundamentals", lambda t, d: None, raising=False)
    assert strat.evaluate_canslim(_leader_bars(), {}, 95, "T") is None
    # zayıf büyüme O'Neil asgarisinin altında → None (uydurma "lider" yok)
    monkeypatch.setattr(earn, "canslim_fundamentals",
                        lambda t, d: {"eps_qoq_growth": 5.0, "eps_cagr_3yr": 8.0}, raising=False)
    assert strat.evaluate_canslim(_leader_bars(), {}, 95, "T") is None


def test_no_look_ahead_with_helper(monkeypatch):
    monkeypatch.setattr(earn, "canslim_fundamentals", lambda t, d: dict(_GOOD_FUND), raising=False)
    df = _leader_bars(); L = len(df)
    base = strat.evaluate_canslim(df, {}, 95, "T")
    assert base is not None
    fut = pd.concat([df, df.tail(5).copy()], ignore_index=True)
    fut.loc[L:, ["open", "high", "low", "close"]] *= 4.0
    fut.loc[L:, "volume"] *= 9.0
    after = strat.evaluate_canslim(fut.iloc[:L], {}, 95, "T")
    assert after is not None
    assert base.as_row() == after.as_row()


def test_dormant_not_armed(monkeypatch):
    assert "canslim" not in strat.ARMED_SETUPS
    monkeypatch.setattr(earn, "canslim_fundamentals", lambda t, d: dict(_GOOD_FUND), raising=False)
    df = _leader_bars()
    by_setup = strat.scan_all(df, {}, 95, "T")
    assert "canslim" in by_setup                       # helper varken ölçülür
    armed = strat.scan_entry(df, {}, 95, "T")
    assert armed is None or armed.setup in strat.ARMED_SETUPS


def test_screener_attribution_wired():
    assert skills.screener_for("canslim") == "canslim-screener"
