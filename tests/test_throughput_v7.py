"""test_throughput_v7.py — kanıt debisi katmanı (öneriler 2→3→4→5→1, 2026-07-20).

#2 rejim-hedefli arka plan yansıması: ufku DOLU canlı-dışı rejim seçilir; taban aynı kanıta ikinci
   yansımayı engeller; canlı rejim asla arka plandan seçilmez.
#3 sonda önbelleği diskte birikir; yeniden başlatma sonrası isabet; bar-revizyonu (clear_wf_caches)
   diski de geçersizler.
#4 LLM görüşleri cf defterine damgalanır ve çözülmüş satıra taşınır; cf çiftleri YALNIZ gösterge —
   terfiyi asla tetikleyemez.
#5 Nasdaq anahtarsız takvim birincil; boş dönerse FMP'ye düşer; mevcut csv ile BİRLEŞİR.
#1 evren tam 251 tekil sembol ve her biri sektör haritasında (250 → 251: 2026-07-30 FISV)."""
import shutil
from pathlib import Path

import pandas as pd
import pytest

from meridian import config, store, analytics
from meridian import hermes_runtime as hr


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


def _t(regime, close, r=0.5):
    return {"regime": regime, "ts_close": close, "r_multiple": r}


# ---------------- #2: rejim-hedefli arka plan yansıması ----------------
def test_bg_regime_picks_ready_nonlive_and_respects_baseline(monkeypatch):
    trades = ([_t("trend_up", f"2025-{m:02d}-15") for m in range(1, 11)]       # 10 işlem · 9 ay yayılım
              + [_t("chop", "2026-07-01"), _t("chop", "2026-07-10")])
    monkeypatch.setitem(hr._state, "bg_reflect_by_regime", {})
    assert hr._bg_ready_regime(trades, every=5, live_reg="chop") == "trend_up"
    assert hr._bg_ready_regime(trades, every=5, live_reg="trend_up") is None   # canlı rejim arka plana giremez
    monkeypatch.setitem(hr._state, "bg_reflect_by_regime", {"trend_up": len(trades)})
    assert hr._bg_ready_regime(trades, every=5, live_reg="chop") is None       # taban: aynı kanıta ikinci yok
    assert hr._bg_ready_regime(trades[:4], every=5, live_reg="chop") is None   # sayı tabanı (katı-VE)


# ---------------- #3: sonda önbelleği diskte ----------------
def test_probe_cache_persists_across_restart_and_rev_invalidates(seeded_sandbox, monkeypatch):
    from meridian import reflect
    calls = {"n": 0}
    monkeypatch.setattr(reflect.backtest, "walk_forward",
                        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or {"oos_score": 0.1})
    cand = {"version": 1, "params": {"stop_loss_atr_mult": 2.0}, "params_by_regime": {}}
    w = ("2022-01-01", "2023-01-01", "2024-01-01", "2024-06-01", ["2023-06-01"], 5)
    reflect.clear_wf_caches()                                          # temiz başlangıç (rev+1, dosya yok)
    calls["n"] = 0
    reflect._probe_wf(cand, "stop_loss_atr_mult", 2.1, 1, None, None, config.goal(), w)
    reflect._probe_wf(cand, "stop_loss_atr_mult", 2.1, 1, None, None, config.goal(), w)
    assert calls["n"] == 1                                             # bellek isabeti
    reflect._PROBE_CACHE.clear(); reflect._PROBE_DISK_LOADED = False   # 'yeniden başlatma'
    reflect._probe_wf(cand, "stop_loss_atr_mult", 2.1, 1, None, None, config.goal(), w)
    assert calls["n"] == 1                                             # DİSK isabeti — iş birikti
    reflect.clear_wf_caches()                                          # bar revizyonu değişti
    reflect._probe_wf(cand, "stop_loss_atr_mult", 2.1, 1, None, None, config.goal(), w)
    assert calls["n"] == 2                                             # bayat önbellek diskten dönemedi


# ---------------- #4: görüşler cf defterinde — yalnız gösterge ----------------
def test_cf_opinion_flow_and_no_promotion_from_sim(seeded_sandbox, monkeypatch):
    from meridian import hermes, counterfactual as cf
    store.write_jsonl("trade_plans.jsonl", [])
    store.write_json("cf_open.json", [{"id": "CF-2026-07-20-AAA-breakout_vcp", "date": "2026-07-20",
                                       "ticker": "AAA", "setup": "breakout_vcp", "score": 70,
                                       "entry_trigger": 100.0, "stop": 95.0, "target": 110.0,
                                       "rr_expected": 2.0, "regime": "chop", "verdict": "NO_GO",
                                       "taken": False, "dormant": False, "status": "pending",
                                       "time_stop_days": 15, "bars_held": 0}])
    hermes._stamp_llm_opinions("2026-07-20", [{"ticker": "AAA", "opinion": "karşı"}])
    assert store.read_json("cf_open.json", [])[0]["llm_opinion"] == "karşı"
    per = {"AAA": pd.DataFrame([{"date": pd.Timestamp("2026-07-21"), "open": 101.0, "high": 112.0,
                                 "low": 100.0, "close": 111.0, "volume": 1e6}]).set_index("date")}
    cf.advance(per, pd.Timestamp("2026-07-21"), "2026-07-21")
    rows = cf.resolved_rows()
    assert rows and rows[0]["llm_opinion"] == "karşı"                  # görüş çözülmüş satıra taşındı
    monkeypatch.setattr(analytics, "_trades", lambda: [])              # GERÇEK çift sıfır
    out = analytics.llm_opinion_calibration()
    assert out["cf_buckets"]["karşı"]["n"] == 1 and out["cf_pairs"] == 1
    assert out["promoted"] is False and out["n_pairs"] == 0            # sim çiftler terfiyi TETİKLEYEMEZ


# ---------------- #5: nasdaq birincil + fmp yedeği + birleşme ----------------
def test_earnings_refresh_nasdaq_primary_and_merge(seeded_sandbox, monkeypatch):
    from meridian import earnings
    from meridian.adapters import data as da
    (seeded_sandbox / "earnings.csv").write_text("ticker,date\nMSFT,2026-07-01\n")   # mevcut çapa korunmalı
    earnings.clear_cache()
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        lambda s, e, **k: {"AAPL": ["2026-07-22"], "ZZZZ": ["2026-07-23"]})
    n = earnings.refresh(["AAPL", "MSFT"])
    assert n == 1                                                      # evren süzgeci: ZZZZ atıldı
    txt = (seeded_sandbox / "earnings.csv").read_text()
    assert "AAPL,2026-07-22" in txt and "MSFT,2026-07-01" in txt       # BİRLEŞTİ, silinmedi
    assert earnings.days_since_report("AAPL", "2026-07-23") is True
    monkeypatch.setattr(da, "nasdaq_earnings_window", lambda s, e, **k: {})
    monkeypatch.setattr(earnings, "refresh_from_fmp", lambda t: 7)
    assert earnings.refresh(["AAPL"]) == 7                             # nasdaq boş → FMP yedeği


# ---------------- #1: evren boyu ----------------
def test_universe_is_unique_with_sectors():
    from meridian.adapters.data import REPLAY_UNIVERSE
    from meridian.backtest import SECTORS
    # 250 → 251 (2026-07-30, FISV). 251 → 248 (TSK-143, 2026-09-05: EA/AVB/EQR gerçek delist
    # çıktı, RETIRED_SYMBOLS'a taşındı — bkz. tests/test_evren_emekliligi_v134.py).
    assert len(REPLAY_UNIVERSE) == 248 and len(set(REPLAY_UNIVERSE)) == 248
    missing = [t for t in REPLAY_UNIVERSE if t not in SECTORS]
    assert not missing, f"sektörsüz: {missing[:8]}"
