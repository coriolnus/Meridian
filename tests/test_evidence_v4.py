"""test_evidence_v4.py — kanıt bant genişliği katmanı (öneriler #1-#5, 2026-07-19 gecesi).

#1 karşı-olgusal defter: motor yasası aynası (giriş boşluk korumaları, stop-önce bar yürüyüşü,
   zaman stopu), tek-seans doldurma penceresi, SIFIR YETKİ (kapı kaynağında adı bile geçmez).
#2 MFE/MAE su işaretleri: pozisyon ömrü boyunca izlenir, kapanış satırına R cinsinden damgalanır.
#3 skor ağırlıkları: varsayılanlar eski sabitlerin birebiri (regresyon), ağırlık oynayınca skor
   değişir, bounds.yaml'da tunable; kalibrasyon raporu monoton veride pozitif IC verir.
#4 kapı meta-kalibrasyonu: sistematik iyimserlikte eşik OTOMATİK yükselir, kanıt yokken birebir eski
   davranış (0.80), yalnız sıkılaştırır.
#5 çapraz-doğrulama: aynı-gün sapma 'diverged', gecikmeli kaynak suç değil ('source_lagging')."""
import inspect
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from meridian import config, store, strategy as strat
from meridian import counterfactual as cf
from meridian.broker import PaperBroker
from tests.conftest import make_bars


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


def _per(ticker: str, rows: list) -> dict:
    """rows: [(date, o, h, l, c)] → loop'un per sözlüğü biçiminde {ticker: df(index=date)}"""
    df = pd.DataFrame([{"date": pd.Timestamp(d), "open": o, "high": h, "low": l, "close": c,
                        "volume": 1e6} for d, o, h, l, c in rows]).set_index("date")
    return {ticker: df}


def _plan(ticker="TST", trigger=100.0, stop=95.0, target=110.0, score=75, verdict="NO_GO"):
    return {"id": f"P-2026-07-01-{ticker}", "ticker": ticker, "entry_trigger": trigger, "size_r": 1.0,
            "stop": stop, "profit_target": target, "targets": [target], "score": score,
            "r_multiple_expected": round((target - trigger) / (trigger - stop), 2),
            "setup": "breakout_vcp", "regime_at_plan": "trend_up", "gate_verdict": verdict}


# ---------------- #1: karşı-olgusal defter ----------------
def test_cf_fills_next_session_and_hits_target(seeded_sandbox):
    cf.collect("2026-07-01", [_plan()], set(), [], time_stop_days=15)
    assert len(store.read_json(cf.OPEN_FILE, [])) == 1
    per = _per("TST", [("2026-07-02", 101.0, 112.0, 100.5, 111.0)])
    cf.advance(per, pd.Timestamp("2026-07-02"), "2026-07-02")
    rows = cf.resolved_rows()
    assert len(rows) == 1 and rows[0]["exit_reason"] == "target"
    slip = 5 / 10000.0
    entry = 101.0 * (1 + slip)
    rps = entry - 95.0
    assert rows[0]["r_multiple"] == pytest.approx((110.0 * (1 - slip) - entry) / rps, abs=1e-3)
    assert rows[0]["mfe_r"] == pytest.approx((112.0 - entry) / rps, abs=1e-3)   # hedef günü dahil izlenir
    assert rows[0]["mae_r"] == pytest.approx((entry - 100.5) / rps, abs=1e-3)
    assert store.read_json(cf.OPEN_FILE, []) == []                              # açık liste temizlendi


def test_cf_gap_guards_mirror_engine_law(seeded_sandbox):
    from meridian.broker import MAX_ENTRY_GAP_PCT
    cf.collect("2026-07-01", [_plan(ticker="GAP"), _plan(ticker="GDN", trigger=100, stop=95)], set(), [], 15)
    per = {**_per("GAP", [("2026-07-02", 100.0 * (1 + MAX_ENTRY_GAP_PCT) + 0.5, 120, 105, 118)]),
           **_per("GDN", [("2026-07-02", 94.0, 96.0, 93.0, 95.5)])}
    cf.advance(per, pd.Timestamp("2026-07-02"), "2026-07-02")
    by = {r["ticker"]: r for r in cf.resolved_rows(entered_only=False)}
    assert by["GAP"]["status"] == "no_fill_gap" and not by["GAP"]["entered"]       # boşluk kovalanmaz
    assert by["GDN"]["status"] == "no_fill_gap_stop" and not by["GDN"]["entered"]  # stop-altı açılışa girilmez


def test_cf_stop_first_conservatism_and_time_stop(seeded_sandbox):
    cf.collect("2026-07-01", [_plan(ticker="SF"), _plan(ticker="TS", target=500.0)], set(), [], time_stop_days=2)
    per = {**_per("SF", [("2026-07-02", 100.0, 115.0, 94.0, 96.0)]),      # aynı bar hem stop hem hedef
           **_per("TS", [("2026-07-02", 100.0, 101.0, 99.0, 100.5),
                         ("2026-07-03", 100.5, 101.5, 99.5, 101.0)])}
    cf.advance(per, pd.Timestamp("2026-07-02"), "2026-07-02")
    cf.advance(per, pd.Timestamp("2026-07-03"), "2026-07-03")
    by = {r["ticker"]: r for r in cf.resolved_rows()}
    assert by["SF"]["exit_reason"] == "stop"          # stop-önce: belirsiz barda iyimser hedef yazılmaz
    assert by["SF"]["r_multiple"] < 0
    assert by["TS"]["exit_reason"] == "time_stop"     # 2 bar sonra kapanışta çıkış


def test_cf_single_session_window_and_dedupe(seeded_sandbox):
    cf.collect("2026-07-01", [_plan()], set(), [], 15)
    cf.collect("2026-07-01", [_plan()], set(), [], 15)                    # aynı gün ikinci çağrı → dedupe
    assert len(store.read_json(cf.OPEN_FILE, [])) == 1
    per = _per("TST", [("2026-07-01", 99, 100, 98, 99.5)])                # açıldığı GÜN ilerletilmez
    cf.advance(per, pd.Timestamp("2026-07-01"), "2026-07-01")
    assert store.read_json(cf.OPEN_FILE, [])[0]["status"] == "pending"


def test_cf_dormant_signals_recorded(seeded_sandbox):
    df = make_bars(120, seed=3, trend=0.002)
    df.loc[df.index[-1], "open"] = df["close"].iloc[-2] * 1.08
    df.loc[df.index[-1], "close"] = df["close"].iloc[-2] * 1.09
    df.loc[df.index[-1], "high"] = df["close"].iloc[-2] * 1.10
    df.loc[df.index[-1], "volume"] = df["volume"].iloc[-51:-1].mean() * 4.0
    last_d = str(df["date"].iloc[-1])[:10]
    (seeded_sandbox / "earnings.csv").write_text(f"ticker,date\nTST,{last_d}\n")
    from meridian import earnings; earnings.clear_cache()
    allsigs = strat.scan_all(df, {}, 80, "TST")
    dormant = [s for s in allsigs.values() if s.setup not in strat.ARMED_SETUPS]
    assert any(s.setup == "episodic_pivot" for s in dormant)              # uyuyan ateşleme artık atılmıyor
    cf.collect(last_d, [], set(), dormant, 15)
    rows = store.read_json(cf.OPEN_FILE, [])
    assert any(r["setup"] == "episodic_pivot" and r["dormant"] and r["verdict"] == "DORMANT" for r in rows)


def test_cf_has_zero_gate_authority():
    """Defter hiçbir kapı/karar yolunda geçmez — şema değil KAYNAK denetimi (gölge model emsali)."""
    from meridian import guard, reflect, probgate
    for fn in (guard.classify_gate, reflect._gate_eval, reflect.submit,
               probgate.PairedProbabilisticGate.evaluate):
        assert "counterfactual" not in inspect.getsource(fn)


# ---------------- #2: MFE/MAE su işaretleri ----------------
def test_mfe_mae_stamped_on_close(seeded_sandbox):
    b = PaperBroker(100_000, slippage_bps=0, commission_per_share=0.0)
    pos = b.fill_entry(_plan(verdict="GO"), next_open=100.0, ts="2026-07-02", equity=100_000)
    assert pos is not None and pos.hi_water == 100.0 and pos.lo_water == 100.0
    pos.hi_water = max(pos.hi_water, 108.0); pos.lo_water = min(pos.lo_water, 97.0)   # loop yürüyüşü
    row = b.close_position("TST", 104.0, "time_stop", "2026-07-10")
    assert row["mfe_r"] == pytest.approx(8.0 / 5.0, abs=1e-3)
    assert row["mae_r"] == pytest.approx(3.0 / 5.0, abs=1e-3)


def test_mfe_mae_none_for_legacy_positions(seeded_sandbox):
    b = PaperBroker(100_000, 0, 0.0)
    pos = b.fill_entry(_plan(verdict="GO"), 100.0, "2026-07-02", 100_000)
    pos.hi_water = 0.0; pos.lo_water = 0.0                    # eski portfolio.json'dan yüklenmiş gibi
    row = b.close_position("TST", 104.0, "target", "2026-07-05")
    assert row["mfe_r"] is None and row["mae_r"] is None      # uydurma damga yok


# ---------------- #3: skor ağırlıkları + kalibrasyon ----------------
def _vcp_bars():
    """Deterministik kusursuz VCP: uzun trend + derin-ama-toparlanan taban + taze hacimli kırılım.
    (RR kapısı taban yüksekliği ≥ 2R ister — sığ tabanlar screener'dan hiç çıkmaz.)"""
    rng = np.random.default_rng(2); n = 320
    up = np.linspace(60, 100, 240) * (1 + rng.normal(0, 0.004, 240))
    dip = np.linspace(100, 94, 30)
    recover = np.linspace(94, 100, 49) * (1 + rng.normal(0, 0.002, 49))
    close = np.concatenate([up, dip, recover, [101.2]])
    high = close * 1.004; low = close * 0.996; high[-1] = 101.8; low[-1] = 100.6
    vol = np.full(n, 1e6); vol[-1] = 3.2e6
    return pd.DataFrame({"date": pd.bdate_range("2022-01-03", periods=n), "open": close * 0.999,
                         "high": high, "low": low, "close": close, "volume": vol})


def test_score_weights_default_regression_and_sensitivity():
    df = _vcp_bars()
    loose = {"entry.pivot_proximity_pct": 8.0, "entry.min_volume_ratio": 1.0, "entry.min_score": 40}
    base = strat.evaluate_entry(df, loose, 85, "TST")
    assert base is not None
    explicit = strat.evaluate_entry(df, {**loose, "entry.w_rs": 0.35, "entry.w_tight": 0.30,
                                         "entry.w_vol": 0.20, "entry.w_prox": 0.15}, 85, "TST")
    assert explicit is not None and explicit.score == base.score          # varsayılan = eski sabitler, birebir
    heavy_rs = strat.evaluate_entry(df, {**loose, "entry.w_rs": 0.60, "entry.w_tight": 0.05,
                                         "entry.w_vol": 0.05, "entry.w_prox": 0.0}, 85, "TST")
    assert heavy_rs is not None and heavy_rs.score != base.score          # ağırlık gerçekten etkili


def test_score_weights_are_tunable_in_bounds():
    for k in ("entry.w_rs", "entry.w_tight", "entry.w_vol", "entry.w_prox"):
        assert k in config.bounds(), k


def test_score_calibration_positive_ic_on_monotone_data(seeded_sandbox, monkeypatch):
    from meridian import analytics
    rng = np.random.default_rng(11)
    trades = [{"score": s, "r_multiple": (s - 60) / 20.0 + rng.normal(0, 0.3)}
              for s in rng.integers(40, 100, 60).tolist()]
    monkeypatch.setattr(analytics, "_trades", lambda: trades)
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: [])
    cal = analytics.score_calibration()
    assert cal is not None and cal["n"] == 60 and cal["rank_ic"] > 0.3
    assert len(cal["quintiles"]) == 5 and cal["monotone_hint"] is True
    monkeypatch.setattr(analytics, "_trades", lambda: trades[:10])        # <30 örneklem → istatistik uydurulmaz
    assert analytics.score_calibration() is None


# ---------------- #4: kapı meta-kalibrasyonu ----------------
def test_meta_calibration_tightens_on_systematic_optimism(seeded_sandbox):
    from meridian import probgate
    assert probgate.PairedProbabilisticGate.p_required_for(1) == 0.80     # kanıt yok → birebir eski davranış
    for i in range(6):
        store.append_jsonl("hypotheses.jsonl", {"id": f"H{i}", "status": "promoted",
                                                "predicted_delta": 0.30, "realized_delta": 0.03})
    out = probgate.refresh_meta_calibration()
    assert out["extra_p"] == 0.05 and out["n_measured"] == 6              # medyan 0.1 < 0.25 → +0.05
    # FORMÜL DEĞİŞTİ (2026-07-22): doğrusal `0.80 + 0.01·(K−1)` yerine GERÇEK Bonferroni
    # `1 − α_aile/K`, α_aile = (1 − P_BASE) − meta_ofset. Eski formül K=16'da 0.95 tavanına çarpıp
    # DONUYORDU: 40 sonda da 400 sonda da aynı çıta, aile hata olasılığı %87.
    # Meta ofset artık α_aile'yi KÜÇÜLTEREK sıkılaştırıyor — tavanın altında yutulmuyor.
    assert probgate.PairedProbabilisticGate.p_required_for(1) == pytest.approx(0.85)   # 1−0.15/1
    assert probgate.PairedProbabilisticGate.p_required_for(3) == pytest.approx(0.95)   # 1−0.15/3
    # Tavan yalnız SAYISAL güvenlik sınırıdır (p=1.0 olsaydı hiçbir aday geçemez, kapı ölürdü):
    assert probgate.PairedProbabilisticGate.p_required_for(99) == pytest.approx(0.9985, abs=1e-4)


def test_meta_calibration_needs_min_evidence_and_never_loosens(seeded_sandbox):
    from meridian import probgate
    for i in range(3):                                                    # META_MIN_N altında → ayar yok
        store.append_jsonl("hypotheses.jsonl", {"id": f"H{i}", "predicted_delta": 0.3, "realized_delta": 0.0})
    assert probgate.refresh_meta_calibration()["extra_p"] == 0.0
    store.write_jsonl("hypotheses.jsonl", [{"id": f"H{i}", "predicted_delta": 0.10,
                                            "realized_delta": 0.50} for i in range(8)])
    out = probgate.refresh_meta_calibration()                             # gerçekleşen > öngörülen (temkinli kapı)
    assert out["extra_p"] == 0.0                                          # asla gevşetmez, yalnız sıkılaştırır
    assert probgate.PairedProbabilisticGate.p_required_for(1) == 0.80


# ---------------- #5: endeks çapraz-doğrulama ----------------
def test_crosscheck_statuses(seeded_sandbox, monkeypatch):
    from meridian.adapters import data as da
    assert str(da._cache_path("SPY")).startswith(str(seeded_sandbox))     # izolasyon: sandbox'a yazar, gerçeğe ASLA
    spy = pd.DataFrame({"date": pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=30),
                        "open": 500.0, "high": 505.0, "low": 495.0, "close": 500.0, "volume": 1e6})
    spy.to_csv(da._cache_path("SPY"), index=False)
    same_day = str(spy["date"].iloc[-1].date())
    monkeypatch.setattr(da, "_fetch_cboe", lambda t, timeout: pd.DataFrame(
        {"date": [same_day], "close": [501.0]}))
    assert da.crosscheck_index()["status"] == "ok"                        # %0.2 sapma → sorun değil
    monkeypatch.setattr(da, "_fetch_cboe", lambda t, timeout: pd.DataFrame(
        {"date": [same_day], "close": [510.0]}))
    out = da.crosscheck_index()
    assert out["status"] == "diverged" and out["divergence"] > 0.015      # aynı gün %2 sapma → data_bad besler
    monkeypatch.setattr(da, "_fetch_cboe", lambda t, timeout: pd.DataFrame(
        {"date": [str(spy["date"].iloc[0].date())], "close": [500.0]}))
    assert da.crosscheck_index()["status"] == "source_lagging"            # gecikmeli kaynak suç DEĞİL
    old = spy.copy(); old["date"] = old["date"] - pd.Timedelta(days=45)   # bayat önbellek → karşılaştırma YOK
    old.to_csv(da._cache_path("SPY"), index=False)
    assert da.crosscheck_index()["status"] == "cache_stale"               # canlıdaki yanlış-pozitifin dersi


# ---------------- entegrasyon: gölge model karşı-olgusaldan öğrenir, terfi gerçek kalır ----------------
def test_shadow_dataset_grows_with_cf_but_promotion_stays_real(seeded_sandbox, monkeypatch):
    from meridian.shadow_model import ShadowTradeOutcomeModel as SM
    monkeypatch.setattr(SM, "_plan_index", classmethod(lambda cls: {}))
    rng = np.random.default_rng(5)
    cfrows = [{"entered": True, "regime": "trend_up", "score": int(s),
               "rr_expected": 2.0, "r_multiple": float(r)}
              for s, r in zip(rng.integers(40, 100, 50), rng.normal(0.1, 1.0, 50))]
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: cfrows)
    monkeypatch.setattr(store, "read_jsonl", lambda name, limit=None: [])   # gerçek işlem yok
    X, y, n = SM._dataset()
    assert n == 50                                                        # eğitim seti defterle büyüdü
    assert "trades.jsonl" in inspect.getsource(SM.evaluate_promotion)     # terfi yargısı gerçek defterde
    assert "counterfactual" not in inspect.getsource(SM.evaluate_promotion)
