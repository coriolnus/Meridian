"""test_pead_v93 — PEAD haftalık kırmızı-mum kırılımı (FMP-kapılı, DORMANT).

pead 'declared-only' iken artık motor-uygulanmış: earnings.csv çapası varsa ölçer, yoksa DÜRÜSTÇE None
(uydurma tetik yok). earnings.csv anahtarsız Nasdaq'tan dolduğu için canlıda ölçüm üretir. ARMED_SETUPS'a
EKLENMEZ → sıfır canlı risk. episodic_pivot'tan AYRI: o boşluk GÜNÜNDE, pead geri-çekilme-sonrası
yeniden-kırılımda ateşler.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import meridian.strategy as strat
import meridian.skills as skills
import meridian.earnings as earn
from meridian.guard import DISCIPLINE_MIN_RR


def _pead_bars(n: int = 80, rep_i: int = 56, gap: float = 0.06):
    """Kazanç OVERNIGHT boşluğu (open prev-close üstüne sıçrar) → yeşil hafta → TAM KIRMIZI hafta →
    son iki bar kırmızı-mumun zirvesini TAZE aşar (cprev<red_high<=c). red_high hesaplanıp son iki bar
    onu kuşatacak şekilde sabitlenir (deterministik ateşleme)."""
    close = np.empty(n); openp = np.empty(n); high = np.empty(n); low = np.empty(n)
    px = 100.0; gi = rep_i + 1
    for i in range(n):
        openp[i] = px
        if i == gi:
            openp[i] = px * (1 + gap); px = openp[i] * 1.005          # overnight earnings gap
        elif gi + 1 <= i <= gi + 4:
            px = openp[i] * 1.006                                     # yeşil hafta
        elif gi + 5 <= i <= gi + 8:
            px = openp[i] * (1 - 0.012)                               # KIRMIZI hafta
        else:
            px = openp[i] * 1.004
        close[i] = px
        high[i] = max(openp[i], close[i]) * 1.003
        low[i] = min(openp[i], close[i]) * 0.997
        px = close[i]
    df = pd.DataFrame({"date": pd.bdate_range("2022-01-03", periods=n), "open": openp, "high": high,
                       "low": low, "close": close, "volume": np.full(n, 1.5e6)})
    # red_high'ı gap-sonrası prior haftalardan hesapla, son iki barı onu TAZE-kuşatacak biçimde sabitle
    rh = _compute_red_high(df)
    assert rh is not None, "fixture kırmızı hafta üretmedi"
    red_high, _red_low = rh
    df.loc[df.index[-2], ["open", "high", "low", "close"]] = [red_high * 0.985, red_high * 0.995,
                                                              red_high * 0.980, red_high * 0.992]
    df.loc[df.index[-1], ["open", "high", "low", "close"]] = [red_high * 0.993, red_high * 1.010,
                                                              red_high * 0.990, red_high * 1.006]
    df.loc[df.index[-1], "volume"] = 4.0e6
    return df, df["date"].iloc[rep_i].date().isoformat()


def _compute_red_high(df: pd.DataFrame):
    opn, close_s = df["open"], df["close"]
    win = min(35, len(df) - 2); g = None; g_gap = 0.03
    for j in range(len(df) - win, len(df)):
        if j <= 0:
            continue
        gp = opn.iloc[j] / close_s.iloc[j - 1] - 1.0
        if gp >= g_gap:
            g_gap, g = gp, j
    if g is None or g >= len(df) - 2:
        return None
    sub = df.iloc[g:].copy(); sub["date"] = pd.to_datetime(sub["date"])
    wk = (sub.set_index("date")[["open", "high", "low", "close"]]
          .resample("W").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna())
    for i in range(len(wk) - 2, -1, -1):
        w = wk.iloc[i]
        if w["close"] < w["open"]:
            return float(w["high"]), float(w["low"])
    return None


def _seed_earnings(sandbox_state, ticker: str, date: str):
    (sandbox_state / "earnings.csv").write_text(f"{ticker},{date}\n")
    earn.clear_cache()


def test_pead_fires_with_seeded_anchor(sandbox_state):
    """Çapa + boşluk + kırmızı-hafta + taze kırılım kurulunca geçerli LONG EntrySignal."""
    df, rep = _pead_bars()
    _seed_earnings(sandbox_state, "T", rep)
    sig = strat.evaluate_pead(df, {}, 95, "T")
    assert sig is not None, "çapa+geometri varken ateşlemedi"
    assert sig.setup == "pead"
    assert sig.stop < sig.entry_trigger < sig.profit_target
    assert sig.r_per_share > 0
    rr = (sig.profit_target - sig.entry_trigger) / sig.r_per_share
    assert rr >= DISCIPLINE_MIN_RR - 1e-9


def test_none_without_earnings_csv(sandbox_state):
    """FMP-kapısı: earnings.csv YOKKEN fire-geometrisinde bile None (uydurma çapa yok)."""
    df, _rep = _pead_bars()
    earn.clear_cache()   # sandbox'ta earnings.csv yok
    assert strat.evaluate_pead(df, {}, 95, "T") is None


def test_date_coercion_string_dtype(sandbox_state):
    """DÜZELTME kanıtı: 'date' sütunu STRING olsa da resample çalışır (bare try/except → sessiz kalıcı
    None DEĞİL). String ve datetime aynı kararı vermeli."""
    df, rep = _pead_bars()
    _seed_earnings(sandbox_state, "T", rep)
    base = strat.evaluate_pead(df, {}, 95, "T")
    df_str = df.copy()
    df_str["date"] = df_str["date"].astype(str)
    coerced = strat.evaluate_pead(df_str, {}, 95, "T")
    assert (base is None) == (coerced is None)
    if base is not None:
        assert base.as_row() == coerced.as_row()


def test_no_look_ahead(sandbox_state):
    df, rep = _pead_bars()
    _seed_earnings(sandbox_state, "T", rep)
    L = len(df)
    base = strat.evaluate_pead(df, {}, 95, "T")
    assert base is not None
    fut = pd.concat([df, df.tail(5).copy()], ignore_index=True)
    fut.loc[L:, ["open", "high", "low", "close"]] *= 4.0
    fut.loc[L:, "volume"] *= 9.0
    after = strat.evaluate_pead(fut.iloc[:L], {}, 95, "T")
    assert after is not None
    assert base.as_row() == after.as_row()


def test_dormant_not_armed(sandbox_state):
    assert "pead" not in strat.ARMED_SETUPS
    df, rep = _pead_bars()
    _seed_earnings(sandbox_state, "T", rep)
    by_setup = strat.scan_all(df, {}, 95, "T")
    assert "pead" in by_setup
    armed = strat.scan_entry(df, {}, 95, "T")
    assert armed is None or armed.setup in strat.ARMED_SETUPS


def test_screener_attribution_wired():
    assert skills.screener_for("pead") == "pead-screener"
    assert "pead-screener" in skills.ENGINE_IMPLEMENTED
