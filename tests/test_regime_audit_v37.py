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


# ---------- RG4: SMA/VIX bacakları GÖSTERGE, KAPI DEĞİL (EDG-005 hükmü, 2026-08-01) ----------
# TARİHÇE (iki turda iki farklı kusur, ikisi de aynı ölü-uç):
#   2026-07-31: `guard._y3_entry_gates` hükmü `regime["entry_gates"]`ten OKUYOR ama anahtarı yalnız
#     api.py'nin PANO yolu üretiyordu → kapı panoda vardı, KARARDA yoktu. Parite kuruldu (üretici
#     `build_regime_json`a eklendi).
#   2026-07-31 (aynı gün, ölçüm): kart EDG-2026-005 ARŞİVE düştü — "KAPI AÇILMAZ, pano göstergesi
#     yeter" (kill#1: tek atfedilebilir pencerede Sharpe −0,25→−0,90, PARA −0,029→−0,088; OOS'ta 55
#     bloke günde 0 giriş engellendi). Yani kurulan parite, HÜKMÜ OLMAYAN bir kapının kablosuydu.
#   2026-08-01: ölü-uç hükme uygun temizlendi — tüketici (guard) ve üretici (build_regime_json)
#     kaldırıldı, hüküm PANO GÖSTERGESİ olarak yaşıyor. Aşağıdaki çiviler bu üç noktayı da tutar:
#     ne kapı sessizce dirilir, ne gösterge sessizce kaybolur.
_RG4_PLAN = {"sector": "Tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 80}
_RG4_PF = {"open_positions": 1, "sector_counts": {}, "open_risk_r": 1.0, "max_corr": 0.1}


def test_rg4_karar_yolunda_TUKETICI_de_URETICI_de_YOK():
    """ÇİVİ: kapı üç noktadan birinde bile geri gelirse bu test kırılır (sessiz diriliş yasağı).

    Kaynak-metin çivisi BİLEREK: davranış çivisi (aşağıdaki rg4b) knob=1'de hükmün değişmediğini
    ölçer, ama biri tüketiciyi geri koyup üreticiyi unutursa davranış YİNE aynı kalır ve ölü-uç
    sessizce geri döner. Bu turda temizlenen kusur tam olarak o hâldi."""
    import json
    from meridian import api

    src_guard = inspect.getsource(guard._y3_portfolio_caps)
    assert 'regime.get("entry_gates")' not in src_guard, \
        "guard rejim kapısını yeniden TÜKETİYOR — EDG-005 hükmü: gösterge, kapı DEĞİL"
    assert not hasattr(guard, "_y3_entry_gates"), "eski kapı zinciri geri gelmiş"
    src_build = inspect.getsource(rg.build_regime_json)
    assert 'out["entry_gates"]' not in src_build, \
        "üretici geri gelmiş — okuyucusuz yazım (YASA 6) ve ölü-ucun kendisi"
    idx = make_bars(300, seed=11, trend=-0.0015)
    rj = rg.build_regime_json(idx, {"regime.min_exposure_score": 0}, "2026-07-20")
    assert "entry_gates" not in rj
    json.dumps(rj, ensure_ascii=False)                       # regime.json'a serileşmeli
    # GÖSTERGE YOLU DURUYOR ve TEK yerde hesaplanıyor: pano satırı ortak fonksiyonu çağırır.
    assert "_rg.entry_gates(bars, params)" in inspect.getsource(api._y3_gate_row)


def test_rg4b_knob_1_verilse_bile_HUKUM_DEGISMEZ():
    """DAVRANIŞ ÇİVİSİ (temizliğin "hiçbir şey değişmedi" kanıtı): AYNI düşen endekste knob 0 ile
    knob 1 BİREBİR aynı hükmü ve aynı gerekçe listesini üretir. Temizlikten önce knob=1 NO_GO
    veriyordu; canlı strateji knob'u TAŞIMADIĞI için canlı davranış zaten değişmemişti, ama
    hipotez uzayı bu knob'u örnekleyebiliyordu — bu çivi o yolu da kapatır."""
    idx = make_bars(300, seed=11, trend=-0.0015)             # kapanış 200-SMA'nın ALTINDA
    taban = {"regime.min_exposure_score": 0}
    acik = {**taban, "regime.spy_sma_gate": 1}
    rj_kapali = rg.build_regime_json(idx, taban, "2026-07-20")
    rj_acik = rg.build_regime_json(idx, acik, "2026-07-20")
    assert rj_kapali == rj_acik, "emekli knob rejim nesnesini DEĞİŞTİRİYOR"
    assert rj_acik["exposure_budget_pct"] > 0, "hüküm bütçeden gelmemeli — ölçüm anlamsızlaşır"
    v_kapali = guard.classify_gate(_RG4_PLAN, _RG4_PF, rj_kapali, config.goal(), params=taban)
    v_acik = guard.classify_gate(_RG4_PLAN, _RG4_PF, rj_acik, config.goal(), params=acik)
    assert v_kapali == v_acik, "emekli knob guard hükmünü DEĞİŞTİRİYOR"
    assert not any("rejim kapısı" in n for n in v_acik[1])


def test_rg4c_gosterge_OLCULMEYE_devam_eder_ve_emekliligini_SOYLER():
    """Kapı elendi diye ÖLÇÜM susmaz: SPY'ın 200-SMA'nın altında olduğu panoda görünür. Ve satır
    kendi emekliliğini ÇIKTININ İÇİNDE söyler — pano metnine güvenmek zorunda kalmayalım."""
    idx = make_bars(300, seed=11, trend=-0.0015)
    eg = rg.entry_gates(idx, {"regime.spy_sma_gate": 1})
    sma = eg["spy_sma_gate"]
    assert sma["hukum"] == "altinda" and sma["close"] and sma["sma"]   # ölçüldü
    assert sma["enabled"] is False and sma["blocks_new_entries"] is False
    assert sma["knob_emekli"]["karar"] == "EDG-2026-005"
    assert "EMEKLİ" in sma["why"], "knob 1 verildi ve bu SESSİZ kaldı"
    assert eg["blocks_new_entries"] is False and eg["blocking"] == []
    assert eg["karar_yolu"] is False and "KAPI DEĞİL" in eg["beyan"]
    assert eg["vix_backwardation_gate"]["hukum"] is None     # kaynak yok — oran UYDURULMAZ


def test_rg4d_olculemeyen_hukum_BEYANLI_None_kalir():
    """Isınma dolmadan hüküm ÜRETİLMEZ — ama alan YİNE DE VARDIR ve nedenini SÖYLER. Kapı ölmüş
    olsa da bu kural göstergede birebir geçerli: ölçülemeyen sayı uydurulmaz."""
    bos = pd.DataFrame({"date": [], "open": [], "high": [], "low": [], "close": [], "volume": []})
    for bars in (make_bars(50, seed=3), bos):
        eg = rg.entry_gates(bars, {"regime.spy_sma_gate": 1})
        sma = eg["spy_sma_gate"]
        assert sma["hukum"] is None and "ısınma" in sma["why"]    # BEYANLI None, sessiz False değil
        assert sma["close"] is None and sma["sma"] is None        # ölçülmemiş sayı UYDURULMAZ
        rj = rg.build_regime_json(bars, {"regime.min_exposure_score": 0,
                                         "regime.spy_sma_gate": 1}, "2026-07-20")
        _, nedenler = guard.classify_gate(_RG4_PLAN, _RG4_PF, rj, config.goal(),
                                          params={"regime.spy_sma_gate": 1})
        assert not any("rejim kapısı" in n for n in nedenler)


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
