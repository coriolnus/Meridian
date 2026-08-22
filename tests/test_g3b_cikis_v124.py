"""G3b kod-seviyesi çıkış reformu (ROADMAP §5.2 "G3b", 2026-07-30) — DÖRT MEKANİZMA, HEPSİ DEFAULT-OFF.

① exit.early_kill_pivot   — pivot-altı kapanış → ertesi açılış çık (TEK yasa, iki tüketici)
② stop_mode / stop_buffer_atr — yapı-tabanlı stop (pivot − tampon), R-nötr
③ backtest.holding_day_r_curve — time-stop kalibrasyon eğrisi (ölçüm, knob değil)
④ config.REGIME_EXIT_KEYS — çıkış anahtarlarının rejim başına çözülmesi

Bu dosyanın ASIL işi SIFIR-ETKİ ÇİVİSİDİR: yeni knob'lar kapalıyken replay BİREBİR eski sonucu
üretir. Çivinin tek başına yeterli olmadığını da test ediyoruz — knob AÇIKKEN sonuç DEĞİŞMELİ,
aksi hâlde "sıfır etki" ölü kodun tautolojisi olurdu (bkz. test_..._acikken_replay_degisir).
"""
import numpy as np
import pandas as pd
import pytest

from meridian import backtest, broker, config, strategy
from tests.conftest import make_bars


# =================================================================================================
# 0. BOUNDS: dört satır var, canlı strategy.yaml onları TAŞIMIYOR (default-off kanıtı)
# =================================================================================================
G3B_KNOBS = ("exit.early_kill_pivot", "exit.early_kill_bars", "stop_mode", "stop_buffer_atr")


def test_g3b_knoblari_bounds_ta_tanimli():
    b = config.bounds()
    for k in G3B_KNOBS:
        assert k in b, f"{k} bounds.yaml'da yok — Hermes kum havuzunda arayamaz"
    assert (b["exit.early_kill_pivot"]["min"], b["exit.early_kill_pivot"]["max"]) == (0, 1)
    assert b["exit.early_kill_pivot"]["type"] == "int"
    assert (b["stop_mode"]["min"], b["stop_mode"]["max"]) == (0, 1)
    assert b["stop_mode"]["type"] == "int"
    assert (b["stop_buffer_atr"]["min"], b["stop_buffer_atr"]["max"]) == (0.1, 1.0)
    assert b["stop_buffer_atr"]["step"] == 0.1
    assert b["exit.early_kill_bars"]["min"] == 1


def test_g3b_knoblari_canli_params_ta_YOK():
    """Batch L deseninin ta kendisi: bounds'ta var, flat params'ta yok → canlı etki SIFIR.
    Bu test kırılırsa biri knob'u canlı parametre setine sokmuş demektir ve o AYRI bir karardır
    (OOS kapısı)."""
    canli = config.load_strategy().get("params", {})
    for k in G3B_KNOBS:
        assert k not in canli, f"{k} canlı params'a girmiş — G3b turunun ALTIN KURALI ihlali"
    assert all(k not in config.default_strategy()["params"] for k in G3B_KNOBS)


# =================================================================================================
# ② YAPI-TABANLI STOP
# =================================================================================================
def test_structural_stop_varsayilan_birebir_eski_atr_yasasi():
    # knob hiç yokken VE açıkça 0 iken: ikisi de eski formül
    for params in ({}, {"stop_mode": 0}, {"stop_mode": 0, "stop_buffer_atr": 0.9}):
        s = strategy.structural_stop(entry_ref=100.0, pivot=99.0, atr=2.0,
                                     params={**params, "stop_loss_atr_mult": 2.0})
        assert s == pytest.approx(96.0), f"params={params}"


def test_structural_stop_pivot_alti_modu():
    s = strategy.structural_stop(entry_ref=100.0, pivot=99.0, atr=2.0,
                                 params={"stop_mode": 1, "stop_buffer_atr": 0.5,
                                         "stop_loss_atr_mult": 2.0})
    assert s == pytest.approx(99.0 - 0.5 * 2.0)          # pivot − tampon; ATR stopu (96.0) DEĞİL
    # tampon knob'u gerçekten okunuyor
    s2 = strategy.structural_stop(100.0, 99.0, 2.0,
                                  {"stop_mode": 1, "stop_buffer_atr": 1.0})
    assert s2 == pytest.approx(97.0)


def test_structural_stop_pivot_olculemezse_atr_ya_duser():
    """pivot ≤ 0 (ölçülemez) iken pivot_alti modu UYDURMA bir seviye üretmez, eski yasaya döner."""
    s = strategy.structural_stop(100.0, 0.0, 2.0,
                                 {"stop_mode": 1, "stop_buffer_atr": 0.5, "stop_loss_atr_mult": 2.0})
    assert s == pytest.approx(96.0)


def test_stop_mode_R_notrlugunu_bozmaz():
    """İKİ modda da pozisyonun taşıdığı DOLAR riski aynıdır (1R = risk_pct·equity·size_r).
    Değişen tek şey R'nin fiyat cinsinden genişliği ve dolayısıyla hisse adedi."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    genis = b.size_position(entry_fill=100.0, stop=96.0, size_r=1.0, equity=100_000)
    sikı = b.size_position(entry_fill=100.0, stop=98.0, size_r=1.0, equity=100_000)
    assert genis[1] == sikı[1] == pytest.approx(1.0 * broker.RISK_PCT_PER_R * 100_000)
    # sıkı stop → 2 kat hisse (aynı dolar riski, yarı genişlik)
    assert sikı[0] == pytest.approx(genis[0] * 2, rel=0.01)


def test_evaluate_entry_stop_mode_sinyali_gercekten_degistirir():
    """Kum havuzunda knob AÇIKKEN evaluate_entry'nin ürettiği stop yapıya demirlenir."""
    bars = make_bars(320, seed=7, breakout_at=290)     # taze zirve → breakout_vcp gerçekten ateşler
    base = dict(config.default_strategy()["params"])
    # kurulumun ateşlediği bir bar bulmak yerine fonksiyonu doğrudan çağırmak yeterli değil —
    # evaluate_entry'nin structural_stop'u GERÇEKTEN çağırdığını, taze bir kırılımda sınıyoruz.
    atesledi = 0
    for i in range(260, len(bars)):
        sub = bars.iloc[: i + 1].reset_index(drop=True)
        sig_atr = strategy.evaluate_entry(sub, base, 95, ticker="X")
        sig_piv = strategy.evaluate_entry(sub, {**base, "stop_mode": 1, "stop_buffer_atr": 0.5},
                                          95, ticker="X")
        if sig_atr and sig_piv:
            atesledi += 1
            assert sig_piv.stop == pytest.approx(sig_piv.pivot - 0.5 * sig_piv.atr)
            assert sig_atr.stop == pytest.approx(sig_atr.entry_trigger - 2.0 * sig_atr.atr)
            assert sig_piv.stop > sig_atr.stop          # pivot−0.5ATR, kapanış−2ATR'den DAHA SIKI
    assert atesledi > 0, "fikstür kırılım üretmiyor — testin kendisi ölçmüyor demektir"


# =================================================================================================
# ① ERKEN İTLAF (pivot-altı)
# =================================================================================================
def _pos(pivot=100.0, entry=101.0):
    return {"entry": entry, "stop": entry * 0.95, "trail_stop": entry * 0.95,
            "r_per_share": entry * 0.05, "pivot": pivot}


def _bars_kapanis(close: float, n: int = 40) -> pd.DataFrame:
    df = make_bars(n, seed=3)
    df = df.copy()
    df.loc[df.index[-1], "close"] = close
    df.loc[df.index[-1], "high"] = max(close, float(df["high"].iloc[-1]))
    df.loc[df.index[-1], "low"] = min(close, float(df["low"].iloc[-1]))
    return df


def test_early_kill_kapali_iken_pivot_altinda_bile_atil():
    bars = _bars_kapanis(95.0)                           # kapanış pivotun (100) ALTINDA
    for params in ({}, {"exit.early_kill_pivot": 0}, config.default_strategy()["params"]):
        assert strategy.early_kill_pivot_exit(bars, _pos(), params, bars_held=1) is False


def test_early_kill_acikken_pivot_alti_kapanis_atesler():
    p = {"exit.early_kill_pivot": 1}
    assert strategy.early_kill_pivot_exit(_bars_kapanis(95.0), _pos(), p, bars_held=1) is True
    # pivotun ÜSTÜNDE kapanış → tez ayakta → çıkış yok
    assert strategy.early_kill_pivot_exit(_bars_kapanis(105.0), _pos(), p, bars_held=1) is False
    # TAM pivotta kapanış çıkış DEĞİL (kural "ALTINDA", eşitlik değil)
    assert strategy.early_kill_pivot_exit(_bars_kapanis(100.0), _pos(), p, bars_held=1) is False


def test_early_kill_penceresi_varsayilan_1_bar():
    bars = _bars_kapanis(95.0)
    p = {"exit.early_kill_pivot": 1}                     # early_kill_bars yok → varsayılan 1
    assert strategy.early_kill_pivot_exit(bars, _pos(), p, bars_held=1) is True
    assert strategy.early_kill_pivot_exit(bars, _pos(), p, bars_held=2) is False
    assert strategy.early_kill_pivot_exit(bars, _pos(), p, bars_held=0) is False   # henüz kapanış yok
    p5 = {**p, "exit.early_kill_bars": 5}
    assert strategy.early_kill_pivot_exit(bars, _pos(), p5, bars_held=5) is True
    assert strategy.early_kill_pivot_exit(bars, _pos(), p5, bars_held=6) is False


@pytest.mark.parametrize("pivot", [None, 0.0, -1.0, float("nan"), "abc"])
def test_early_kill_olculemeyen_pivot_UYDURMA_cikis_uretmez(pivot):
    bars = _bars_kapanis(1.0)                            # kapanış her seviyenin altında
    pos = _pos()
    if pivot is None:
        pos.pop("pivot")
    else:
        pos["pivot"] = pivot
    assert strategy.early_kill_pivot_exit(bars, pos, {"exit.early_kill_pivot": 1}, 1) is False


def test_manage_position_erken_itlaf_sebebi_yazar():
    bars = _bars_kapanis(95.0)
    dec = strategy.manage_position(bars, _pos(), {"exit.early_kill_pivot": 1}, bars_held=1,
                                   regime_ok=True)
    assert dec.exit_now is True and dec.exit_reason == "early_kill_pivot"
    # trail geri ALINMAZ: itlaf kararı da güncellenmiş trail'i taşır
    assert dec.trail_stop >= _pos()["stop"]


def test_manage_position_varsayilan_davranis_birebir():
    """Yeni knob'lar YOKKEN manage_position'ın hükmü, knob'lar açıkça KAPALI verildiğindekiyle
    birebir aynı — ve hiçbiri 'early_kill_pivot' sebebi üretmez."""
    bars = _bars_kapanis(95.0)
    base = config.default_strategy()["params"]
    a = strategy.manage_position(bars, _pos(), base, bars_held=1, regime_ok=True)
    b = strategy.manage_position(bars, _pos(), {**base, "exit.early_kill_pivot": 0,
                                                "exit.early_kill_bars": 1}, 1, True)
    assert (a.exit_now, a.exit_reason, a.trail_stop) == (b.exit_now, b.exit_reason, b.trail_stop)
    assert a.exit_reason != "early_kill_pivot"


def test_pivot_pozisyona_tasiniyor_ve_pivotsuz_cagiran_atil():
    """TEK YASA'nın veri dikişi: fill_entry(pivot=…) → Position.pivot → early_kill_pivot_exit.

    PİVOT PLAN SÖZLÜĞÜNDE DEĞİL AYRI ARGÜMANDA: plan defteri şeması iki motorda AYNI kalmak
    zorundadır (test_differential_v60 replay-only alana allowlist TUTMAZ — replay'in bilip canlının
    bilmediği alan §4 ayrışmasıdır). Pivot bir defter alanı değil İCRA girdisidir."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="d1", equity=100_000, pivot=99.5)
    assert pos.pivot == pytest.approx(99.5)
    assert "pivot" not in plan, "pivot plan SÖZLÜĞÜNE sızmamalı (şema ayrışması)"
    # pivot GEÇİRMEYEN çağıran (bugünkü canlı loop.py yolu) → 0.0 → erken itlaf ateşlemez
    b2 = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos2 = b2.fill_entry({**plan, "ticker": "Y"}, next_open=100.0, ts="d1", equity=100_000)
    assert pos2.pivot == 0.0
    assert strategy.early_kill_pivot_exit(
        _bars_kapanis(1.0), {"entry": pos2.entry, "stop": pos2.stop, "trail_stop": pos2.trail_stop,
                             "r_per_share": pos2.r_per_share, "pivot": pos2.pivot},
        {"exit.early_kill_pivot": 1}, 1) is False


# =================================================================================================
# ③ TIME-STOP GÜN-GÜN R EĞRİSİ
# =================================================================================================
def test_r_egrisi_bos_girdi_uydurma_sifir_uretmez():
    out = backtest.holding_day_r_curve([])
    assert out["n"] == 0 and out["ort_r"] is None and out["gunler"] == [] and out["kumulatif"] == []
    # eksik alanlı satırlar SAYILMAZ
    assert backtest.holding_day_r_curve([{"bars_held": None, "r_multiple": 1.0}])["n"] == 0


def test_r_egrisi_gun_bazli_muhasebe():
    trades = [
        {"bars_held": 1, "r_multiple": -1.0, "exit_reason": "stop"},
        {"bars_held": 1, "r_multiple": -0.5, "exit_reason": "stop_gap"},
        {"bars_held": 3, "r_multiple": 2.5, "exit_reason": "target"},
        {"bars_held": 15, "r_multiple": -0.2, "exit_reason": "time_stop"},
    ]
    out = backtest.holding_day_r_curve(trades)
    assert out["n"] == 4 and out["n_atlanan"] == 0
    assert out["ort_r"] == pytest.approx((-1.0 - 0.5 + 2.5 - 0.2) / 4)
    g = {x["gun"]: x for x in out["gunler"]}
    assert g[1]["n"] == 2 and g[1]["ort_r"] == pytest.approx(-0.75)
    assert g[1]["sebepler"] == {"stop": 1, "stop_gap": 1}
    assert g[3]["toplam_r"] == pytest.approx(2.5)
    # KUYRUK: gün 3 ve sonrası = 2.5 + (−0.2) = 2.3  → geç günler burada POZİTİF
    k = {x["gun"]: x for x in out["kumulatif"]}
    assert k[3]["kuyruk_toplam_r"] == pytest.approx(2.3)
    assert k[15]["kuyruk_toplam_r"] == pytest.approx(-0.2)
    assert k[15]["n_kumulatif"] == 4 and k[15]["kumulatif_ort_r"] == pytest.approx(0.2)
    assert k[1]["kuyruk_toplam_r"] == pytest.approx(0.8)          # tüm işlemler = toplam R


def test_r_egrisi_max_day_kovasi():
    out = backtest.holding_day_r_curve([{"bars_held": 999, "r_multiple": 1.0}], max_day=40)
    assert [x["gun"] for x in out["gunler"]] == [40]              # taşan tutuşlar son kovaya toplanır


# =================================================================================================
# ④ REJİM-KOŞULLU ÇIKIŞ ALTYAPISI
# =================================================================================================
def test_resolve_params_bos_rejim_haritasi_birebir_kopya():
    """SIFIR-ETKİ: bugünün canlı durumu (boş harita) → dönen sözlük flat params'ın kopyası."""
    p = dict(config.default_strategy()["params"])
    bos = {r: {} for r in config.VALID_REGIMES}
    assert config.resolve_params(p, bos, "trend_up") == p
    assert config.resolve_params(p, None, "trend_up") == p


def test_resolve_params_cikis_anahtari_flat_params_ta_olmasa_da_uygulanir():
    """G3b ④: yeni çıkış knob'u flat params'ta YOK — eskiden override SESSİZCE DÜŞÜYORDU."""
    p = dict(config.default_strategy()["params"])
    assert "exit.early_kill_pivot" not in p
    eff = config.resolve_params(p, {"chop": {"exit.early_kill_pivot": 1,
                                             "stop_mode": 1, "stop_buffer_atr": 0.7}}, "chop")
    assert eff["exit.early_kill_pivot"] == 1 and eff["stop_mode"] == 1
    assert eff["stop_buffer_atr"] == 0.7
    # BAŞKA rejimde etkisiz
    assert "exit.early_kill_pivot" not in config.resolve_params(
        p, {"chop": {"exit.early_kill_pivot": 1}}, "trend_up")


def test_resolve_params_liste_disi_anahtar_hala_DUSER():
    """`k in params` kuralının VAR OLMA SEBEBİ knob İCADINI engellemek — izin ADIYLA verilir."""
    p = dict(config.default_strategy()["params"])
    eff = config.resolve_params(p, {"chop": {"exit.time_stop_dayz": 99, "uydurma.knob": 1}}, "chop")
    assert "exit.time_stop_dayz" not in eff and "uydurma.knob" not in eff


def test_regime_exit_keys_hepsi_bounds_ta_var():
    b = config.bounds()
    for k in config.REGIME_EXIT_KEYS:
        assert k in b, f"REGIME_EXIT_KEYS'te bounds'ta olmayan anahtar: {k}"


# =================================================================================================
# SIFIR-ETKİ ÇİVİSİ — REPLAY BİREBİR (+ knob açıkken GERÇEKTEN değişir)
# =================================================================================================
def _mini_evren(n=340, seed=4):
    bars, tickers = {}, ("AAPL", "MSFT", "NVDA", "JPM", "XOM", "UNH")
    for i, t in enumerate(tickers):
        bars[t] = make_bars(n, seed=seed + i, trend=0.0008, breakout_at=200 + 7 * i)
    index = make_bars(n, seed=seed + 99, trend=0.0005)
    return bars, index


def _replay(params, bars, index, goal):
    res = backtest.replay(params, bars, index, goal, "2022-01-03", "2023-04-28")
    return [(t["ticker"], t["ts_open"], t["ts_close"], t["r_multiple"], t["exit_reason"])
            for t in res.trades], res


def test_SIFIR_ETKI_CIVISI_yeni_knoblar_kapaliyken_replay_birebir():
    goal = config.goal()
    bars, index = _mini_evren()
    base = dict(config.default_strategy()["params"])
    kapali = {**base, "exit.early_kill_pivot": 0, "exit.early_kill_bars": 1,
              "stop_mode": 0, "stop_buffer_atr": 0.5}
    a, res_a = _replay(base, bars, index, goal)
    b, _ = _replay(kapali, bars, index, goal)
    assert a == b, "yeni knob'lar KAPALIYKEN replay eski sonucu birebir üretmiyor"
    assert len(a) > 0, "çivi boş bir replay üzerinde kurulamaz (işlem yok)"
    # PLAN ŞEMASI DEĞİŞMEDİ: pivot yan kanaldan taşınır, defter alanı olmaz (bkz. differential_v60)
    assert not any("pivot" in p for p in res_a.plan_log), "pivot plan defterine sızmış — şema ayrışması"
    assert not any(t[4] == "early_kill_pivot" for t in a)


def test_civi_tautoloji_degil_knob_ACIKKEN_replay_DEGISIR():
    """Sıfır-etki çivisi tek başına ölü kodu da 'ispatlar'. Bu test mekanizmanın replay yolunda
    GERÇEKTEN ulaşılabilir olduğunu gösterir: açıkken sonuç değişmeli."""
    goal = config.goal()
    bars, index = _mini_evren()
    base = dict(config.default_strategy()["params"])
    a, _ = _replay(base, bars, index, goal)
    e1, _ = _replay({**base, "exit.early_kill_pivot": 1, "exit.early_kill_bars": 5}, bars, index, goal)
    e2, _ = _replay({**base, "stop_mode": 1, "stop_buffer_atr": 0.5}, bars, index, goal)
    assert e1 != a, "early_kill_pivot=1 replay'i hiç etkilemiyor — mekanizma ulaşılamaz (ölü kod)"
    assert e2 != a, "stop_mode=1 replay'i hiç etkilemiyor — mekanizma ulaşılamaz (ölü kod)"
    assert any(t[4] == "early_kill_pivot" for t in e1), "erken itlaf hiç ateşlemedi"


def test_rejim_kosullu_cikis_replay_yolunda_gercekten_etkili():
    """④ altyapısının UÇTAN UCA kanıtı: yalnız params_by_regime üzerinden verilen (flat params'ta
    BULUNMAYAN) bir çıkış knob'u replay sonucunu değiştirir. Eskiden bu aday incumbent'la BİREBİR
    aynı replay ediyordu ve kapı 'no-op' diye reddediyordu — yani hipotez hiç sınanmamış oluyordu."""
    goal = config.goal()
    bars, index = _mini_evren()
    base = dict(config.default_strategy()["params"])
    duz, _ = _replay(base, bars, index, goal)
    res = backtest.replay(base, bars, index, goal, "2022-01-03", "2023-04-28",
                          params_by_regime={r: {"exit.early_kill_pivot": 1,
                                                "exit.early_kill_bars": 5}
                                            for r in config.VALID_REGIMES})
    rejimli = [(t["ticker"], t["ts_open"], t["ts_close"], t["r_multiple"], t["exit_reason"])
               for t in res.trades]
    assert rejimli != duz
    assert any(t[4] == "early_kill_pivot" for t in rejimli)


def test_r_egrisi_gercek_replay_isleminden_uretilebilir():
    goal = config.goal()
    bars, index = _mini_evren()
    res = backtest.replay(dict(config.default_strategy()["params"]), bars, index, goal,
                          "2022-01-03", "2023-04-28")
    egri = backtest.holding_day_r_curve(res.trades)
    assert egri["n"] == len(res.trades) and egri["gunler"]
    assert sum(g["n"] for g in egri["gunler"]) == egri["n"]
    assert egri["kumulatif"][-1]["n_kumulatif"] == egri["n"]
