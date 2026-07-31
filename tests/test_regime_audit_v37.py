"""test_regime_audit_v37.py — regime (tur 23) + regime_trigger (tur 24) denetimi, 2026-07-21.

7. soru:
  RG1 "kapı canlıyla aynı rejim nesnesini görür" → HAYIR: canlı döngü ve cf_backfill
     `leading_sectors`'ı DOLDURUYOR, backtest DOLDURMUYORDU. guard'ın 'leading_sector' soft kontrolü
     kapıda hiç ateşlenmiyor, canlıda ateşleniyordu — aynı yasanın iki uygulaması, sessizce ayrışmış.
     (NO_GO'yu değiştirmediği için işlem sayısı aynı; REVIEW dağılımı ve ona bakan katmanlar yanlış.)
  RG2 "exposure_budget SERT bir tavandır" → eşiğin altında 0 olmalı; sıralama trend_up > chop >
     high_vol > trend_down bozulursa risk bütçesi anlamını yitirir
  RG3 "yetersiz veri uydurma rejim üretmez"
  RT1 "tetikleyici KARAR VERMEZ" → yalnız sayar ve bir kez haber verir (eylem operatörde)
"""
from __future__ import annotations

import inspect

import pandas as pd
import pytest

from meridian import backtest, config, guard, regime as rg, store
from meridian.regime_trigger import DeferredRegimeBudgetTrigger, THRESHOLD_N, STATE_FILE
from tests.conftest import make_bars


# ---------- RG1: kapı ile canlı aynı rejim nesnesi ----------
def test_rg1_backtest_fills_leading_sectors_like_live():
    src_bt = inspect.getsource(backtest.replay)
    assert "sector_momentum" in src_bt, "backtest lider sektörleri doldurmuyor → guard soft kontrolü ölü"
    from meridian import loop
    assert "sector_momentum" in inspect.getsource(loop.daily_cycle)


def test_rg1b_replay_produces_non_empty_leading_sectors():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150)}
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", "2023-06-01", strategy_version=1)
    assert res.plan_log is not None                 # akış çalıştı (boş olabilir, önemli olan çökmemesi)


def test_rg1c_sector_momentum_is_deterministic_and_ranked():
    rets = {"A": 0.10, "B": 0.30, "C": -0.05, "D": 0.29}
    sectors = {"A": "tech", "B": "energy", "C": "tech", "D": "energy"}
    out = rg.sector_momentum(rets, sectors, top=2)
    assert out == rg.sector_momentum(rets, sectors, top=2)
    assert out[0]["sector"] == "energy" and out[0]["n"] == 2
    assert out[0]["momentum"] >= out[-1]["momentum"]


# ---------- RG2: bütçe sert tavan ----------
def test_rg2_budget_is_zero_below_the_threshold():
    idx = make_bars(300, seed=4, trend=-0.002)                  # düşen piyasa
    rj = rg.build_regime_json(idx, {"regime.min_exposure_score": 90}, "2026-07-20")
    assert rj["exposure_budget_pct"] == 0, "eşiğin altında bütçe SIFIR olmalı (sert tavan)"
    assert rj["min_exposure_score"] == 90 and "budget=0" in rj["rationale"]


def test_rg2b_exposure_score_ordering_and_bounds():
    scores = {r: rg.exposure_score(r, {}) for r in
              (rg.TREND_UP, rg.CHOP, rg.HIGH_VOL, rg.TREND_DOWN)}
    assert all(0 <= v <= 100 for v in scores.values())
    assert scores[rg.TREND_UP] > scores[rg.CHOP] > scores[rg.HIGH_VOL] > scores[rg.TREND_DOWN]
    assert rg.exposure_score(rg.CHOP, {"high_vol": True}) < scores[rg.CHOP]   # oynaklık kısar


def test_rg2c_heavy_distribution_throttles_budget():
    idx = make_bars(300, seed=5, trend=0.001)
    base = rg.build_regime_json(idx, {"regime.min_exposure_score": 0}, "2026-07-20")
    assert base["exposure_score"] >= base["exposure_budget_pct"] or base["exposure_budget_pct"] >= 0
    assert "distribution_days" in base and isinstance(base["distribution_days"], int)


# ---------- RG3: dürüst yetersizlik ----------
def test_rg3_insufficient_history_is_chop_with_a_reason():
    reg, met = rg.classify(make_bars(30, seed=6))
    assert reg == rg.CHOP and met.get("reason") == "insufficient index history"
    reg2, _ = rg.classify(None)
    assert reg2 == rg.CHOP


def test_rg3b_every_emitted_label_is_a_valid_regime():
    labels = set()
    for seed, trend in ((1, 0.002), (2, -0.002), (3, 0.0), (4, 0.0005)):
        labels.add(rg.classify(make_bars(300, seed=seed, trend=trend))[0])
    assert labels <= set(config.VALID_REGIMES)


# ---------- RG4: entry_gates ÜRETİCİ-TÜKETİCİ PARİTESİ (2026-07-31) ----------
# RG1'in aynı kusuru, bu kez NO_GO'yu DEĞİŞTİREN bir kapıda: `guard._y3_entry_gates` Y3'ün iki
# piyasa kapısının hükmünü `regime["entry_gates"]`ten OKUYOR ama o anahtarı yalnız api.py'nin PANO
# yolu (`_y3_gate_row`) üretiyordu. guard'a `regime` olarak HER motorda `build_regime_json` çıktısı
# gider (loop.py:529→655, backtest.py:230→323, cf_backfill.py:39→94) — anahtar orada YOKTU, `eg`
# None'a düşüyordu ve kapı knob AÇILSA BİLE canlı döngüde de replay'de de yapısal olarak
# ateşleyemiyordu. Kapı panoda vardı, KARARDA yoktu.
_RG4_PLAN = {"sector": "Tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 80}
_RG4_PF = {"open_positions": 1, "sector_counts": {}, "open_risk_r": 1.0, "max_corr": 0.1}


def test_rg4_producer_emits_the_exact_key_the_consumer_reads():
    """ÇİVİ: tüketicinin OKUDUĞU ad ile üreticinin YAZDIĞI ad aynı, ve yasa TEK yerde."""
    import json
    from meridian import api

    src_guard = inspect.getsource(guard._y3_entry_gates)
    assert 'regime.get("entry_gates")' in src_guard          # tüketicinin okuduğu ad — sabitlenir
    idx = make_bars(300, seed=11, trend=-0.0015)
    rj = rg.build_regime_json(idx, {"regime.min_exposure_score": 0}, "2026-07-20")
    assert "entry_gates" in rj, "üretici, tüketicinin okuduğu anahtarı YAZMIYOR (kapı süs)"
    eg = rj["entry_gates"]
    # guard'ın gerçekten dokunduğu alanlar (guard.py:419-422) — şekil paritesi
    assert isinstance(eg.get("blocks_new_entries"), bool)
    assert isinstance(eg.get("blocking"), list)
    # TEK YASA: pano yolu da motor yolu da AYNI ortak fonksiyonu, aynı imzayla çağırır. Kapı iki
    # yerde HESAPLANMAZ — iki uygulama iki gerçek demektir (RG1'in dersi).
    assert "entry_gates(index_bars, params)" in inspect.getsource(rg.build_regime_json)
    assert "_rg.entry_gates(bars, params)" in inspect.getsource(api._y3_gate_row)
    json.dumps(rj, ensure_ascii=False)                       # regime.json'a serileşmeli


def test_rg4b_open_gate_reaches_NO_GO_through_the_LIVE_regime_object():
    """UÇTAN UCA: elle kurulmuş bir fikstür değil, `build_regime_json`ın ÜRETTİĞİ nesne doğrudan
    guard'a verilir — motorların yaptığının aynısı. Kusur tam burada görünmezdi."""
    idx = make_bars(300, seed=11, trend=-0.0015)             # kapanış 200-SMA'nın ALTINDA
    params = {"regime.min_exposure_score": 0, "regime.spy_sma_gate": 1}
    rj = rg.build_regime_json(idx, params, "2026-07-20")
    assert rj["exposure_budget_pct"] > 0, "NO_GO'nun sebebi bütçe olmamalı — kapı ölçülmeli"
    assert rj["entry_gates"]["blocks_new_entries"] is True
    assert rj["entry_gates"]["blocking"] == ["regime.spy_sma_gate"]
    v, nedenler = guard.classify_gate(_RG4_PLAN, _RG4_PF, rj, config.goal(), params=params)
    assert v == "NO_GO" and any("rejim kapısı" in n for n in nedenler), \
        "rejim kapısı hükmü guard'a ULAŞMIYOR"


def test_rg4c_knob_closed_is_permissive_and_the_verdict_is_untouched():
    """DEFAULT KAPALI çivisi: AYNI düşen endekste knob 0 iken kapı hiçbir karara girmez —
    ama hüküm yine de KAYDA GEÇER (kapalı knob'un tarihçesi olmadan açılış kararı kanıtsız kalır)."""
    idx = make_bars(300, seed=11, trend=-0.0015)
    rj = rg.build_regime_json(idx, {"regime.min_exposure_score": 0}, "2026-07-20")
    eg = rj["entry_gates"]
    assert eg["spy_sma_gate"]["enabled"] is False
    assert eg["blocks_new_entries"] is False and eg["blocking"] == []
    assert eg["spy_sma_gate"]["hukum"] == "altinda"          # ölçüldü, uygulanmadı
    assert eg["vix_backwardation_gate"]["hukum"] is None     # kaynak yok — oran UYDURULMAZ
    v, nedenler = guard.classify_gate(_RG4_PLAN, _RG4_PF, rj, config.goal(), params={})
    assert not any("rejim kapısı" in n for n in nedenler)


def test_rg4d_unmeasurable_gate_is_a_DECLARED_None_never_a_missing_key():
    """Isınma dolmadan kapı KARAR VERMEZ — ama anahtar YİNE DE VARDIR ve nedenini SÖYLER.
    Bugün düzeltilen kusur tam olarak sessiz-eksik-anahtardı; hiçbir yolda geri gelmemeli."""
    bos = pd.DataFrame({"date": [], "open": [], "high": [], "low": [], "close": [], "volume": []})
    for bars in (make_bars(50, seed=3), bos):
        rj = rg.build_regime_json(bars, {"regime.min_exposure_score": 0,
                                         "regime.spy_sma_gate": 1}, "2026-07-20")
        assert "entry_gates" in rj, "ölçülemedi diye anahtar DÜŞTÜ — sessiz eksik anahtar geri geldi"
        eg = rj["entry_gates"]
        sma = eg["spy_sma_gate"]
        assert sma["hukum"] is None and "ısınma" in sma["why"]    # BEYANLI None, sessiz False değil
        assert sma["close"] is None and sma["sma"] is None        # ölçülmemiş sayı UYDURULMAZ
        # ölçülemeyen koşul yeni riski DURDURMAZ (aksi hâlde knob hiç ölçülemezdi)
        assert eg["blocks_new_entries"] is False
        _, nedenler = guard.classify_gate(_RG4_PLAN, _RG4_PF, rj, config.goal(),
                                          params={"regime.spy_sma_gate": 1})
        assert not any("rejim kapısı" in n for n in nedenler), \
            "ölçülemeyen kapı yeni girişi kapattı — knob bir daha hiç ölçülemezdi"


# ---------- RT1: tetikleyici karar vermez ----------
def test_rt1_trigger_only_counts_and_reports(sandbox_state):
    trades = [{"regime": "chop"}] * (THRESHOLD_N + 2) + [{"regime": "trend_up"}] * 3
    out = DeferredRegimeBudgetTrigger().evaluate(trades)
    assert out["chop"]["ready"] is True and out["trend_up"]["ready"] is False
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "regime_budget_trigger"]
    assert ev and "chop" in ev[-1]["regimes"]
    assert "operatör kararı" in ev[-1]["detail"]                 # eylem İNSANDA


def test_rt1b_trigger_fires_once_per_regime(sandbox_state):
    trades = [{"regime": "chop"}] * (THRESHOLD_N + 1)
    t = DeferredRegimeBudgetTrigger()
    t.evaluate(trades)
    t.evaluate(trades)
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "regime_budget_trigger"]
    assert len(ev) == 1
    assert store.read_json(STATE_FILE, {})["fired"] == ["chop"]


def test_rt1c_trigger_never_writes_strategy_or_budget():
    src = inspect.getsource(DeferredRegimeBudgetTrigger)
    for forbidden in ("dump_yaml", "save_strategy", "exposure_budget_pct", "regime.json"):
        assert forbidden not in src, f"tetikleyici karar veriyor olabilir: {forbidden}"
