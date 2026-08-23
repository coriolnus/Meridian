"""test_opt_faz1_kablolama_v276.py — OPT FAZ-1 KABLOLAMA (WP3-B madde 10 (1), 2026-08-23).

BU TURUN İDDİASI ŞU DEĞİL: "bu düğmeler iyileştiriyor." Öyle bir iddia ancak ön-kayıt kartı +
kapıdan geçen ölçümle kurulabilir. Bu turun iddiası üç cümledir (emsal: test_derisk_rampa_kablosu_v237
— "OPT Faz-1'in İLK kalemi" — ve test_turnover_kablolama_v149):

  1. KABLONUN KENDİSİ HİÇBİR SAYIYI DEĞİŞTİRMEDİ — anahtar params'ta YOKKEN her aday, bugünkü
     fonksiyon-gövdesi sabitinin BİREBİR aynısını üretir (özdeşlik çivileri).
  2. DÜĞME GERÇEKTEN BAĞLI — anahtar verildiğinde okunur ve davranışı ölçülebilir yönde oynatır
     (pozitif kontroller). Kablo bağlanmamış bir parametre en tehlikeli yalancı düğmedir.
  3. ARAMA UZAYINA HENÜZ GİRMEDİLER — bounds.yaml'a satır YAZILMADI (sınırlar operatör onaylı;
     öneri docs/ONERI-OPT-FAZ1-BOUNDS-2026-08-23.md'de). Bugün Hermes bu adları ÖNEREMEZ.

KABLOLANAN YENİ ADAYLAR (fonksiyon-gövdesi sabitiydiler):
  exit.trail_arm_r        (1.0)  — ATR-trail + chandelier silahlanma eşiği ("kâr > 1R" sabiti)
  exit.giveback_arm_r     (1.0)  — giveback zirve-kâr silahlanma eşiği ("peak > 1R" sabiti)
  entry.vol_score_sat     (3.0)  — vol_score doyma noktası (min(vr/3, 1) sabiti)
  entry.rvol_band_center  (1.75) — rvol bant merkezi (RVOL_BAND_CENTER)
  entry.rvol_band_halfwidth (0.75) — rvol bant yarı-genişliği (RVOL_BAND_HALFWIDTH)
  entry.rs_dual_pace      (3.0)  — çift-ufuk RS pro-rata çarpanı (yalnız rs_dual_horizon=1 iken)

WP3-B'NİN ANDIĞI BEŞLİ (ölçüldü — dördü ZATEN kablolu, biri beyan istedi):
  derisk bandı → broker.derisk_ramp (goal limits; v237) · max_open → limits+LIMIT_KEYS ·
  position_size_r → bounds satırı var · chandelier → bounds + manage_position ·
  scale_out → bounds + broker.scale_out AMA silahlanması EDG-027 hükmüne tabidir; o beyanın
  kaynak yorumunda durması bu dosyada çivilenir (aşağıda D bölümü).
"""
from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from meridian import broker, config, guard, shadow_lifecycle as sl, strategy as strat
from tests.conftest import make_bars
from tests.test_learning_roundtrip_v76 import staircase_bars

# Kapıları gevşetilmiş param seti (test_score_rebuild_v115 / test_turnover_kablolama_v149 emsali):
# bu dosyanın sorusu "kaç sinyal geçiyor" değil "geçen sinyalin SKORU/KARARI değişti mi".
LOOSE = {"entry.pivot_proximity_pct": 8.0, "entry.min_volume_ratio": 1.0, "entry.min_score": 40}

YENI_ANAHTARLAR = ("exit.trail_arm_r", "exit.giveback_arm_r", "entry.vol_score_sat",
                   "entry.rvol_band_center", "entry.rvol_band_halfwidth", "entry.rs_dual_pace")


def _duz_bars(n=60, close_last=104.0, hi_last=None, seed=3):
    """Küçük ATR'li, son barı kontrol edilebilir sentetik seri (manage_position girdisi)."""
    rng = np.random.default_rng(seed)
    base = 100.0 + rng.normal(0, 0.2, n).cumsum() * 0.1
    close = base.copy()
    close[-1] = close_last
    high = close + 0.5
    if hi_last is not None:
        high[-1] = hi_last
    low = close - 0.5
    openp = close - 0.1
    vol = np.full(n, 1_000_000.0)
    return pd.DataFrame({"open": openp, "high": high, "low": low, "close": close, "volume": vol})


def _poz(entry=100.0, stop=95.0):
    return {"entry": entry, "stop": stop, "trail_stop": stop, "r_per_share": entry - stop}


def _sinyaller(df: pd.DataFrame, params: dict, rs: int = 85, ticker: str = "T"):
    for i in range(400, len(df)):
        sub = df.iloc[:i + 1].reset_index(drop=True)
        sig = strat.evaluate_entry(sub, params, rs, ticker)
        if sig is not None:
            yield sub, sig


def _ilk_sinyal(df, params, rs: int = 85):
    for sub, sig in _sinyaller(df, params, rs):
        return sub, sig
    return None, None


# =================================================================================================
# A) ÖZDEŞLİK ÇİVİLERİ — anahtar YOKKEN kablo hiçbir sayıyı değiştirmedi
# =================================================================================================
def test_a1_yeni_anahtarlar_NE_bounds_ta_NE_varsayilan_params_ta(sandbox_state):
    """Bu tur bounds.yaml'a satır YAZMADI (operatör onayı bekler) ve tohum params'a da girmedi
    (config sözleşmesi: 'Every value sits inside bounds.yaml'). Yani bugün Hermes öneremez,
    canlı strategy.yaml taşımıyor, her okuma kod varsayılanına düşüyor."""
    b = config.bounds()
    p = config.default_strategy()["params"]
    for k in YENI_ANAHTARLAR:
        assert k not in b, f"{k} bounds'a sızmış — sınırlar operatör onaylıdır"
        assert k not in p, f"{k} tohum params'a sızmış — bounds'suz tohum sözleşmeyi bozar"
    v = guard.validate_change({"variable": "exit.trail_arm_r", "new": 0.5}, p, b,
                              config.goal(), [], 0)
    assert not v.ok and any("bounds" in r for r in v.reasons)   # Hermes bugün ÖNEREMEZ


def test_a2_manage_position_ozdesligi_anahtar_yokken():
    """Varsayılan params ile {anahtar: varsayılan-değer} params AYNI kararı ve AYNI trail'i verir —
    üç senaryoda (kâr<1R, kâr>1R, giveback tetiklenen zirve-geri-verme)."""
    esli = {"exit.trail_arm_r": 1.0, "exit.giveback_arm_r": 1.0}
    senaryolar = [
        (_duz_bars(close_last=104.0), {}, 5),                              # kâr 4 < 1R=5 → ratchet yok
        (_duz_bars(close_last=120.0), {}, 5),                              # kâr 20 = 4R → ratchet var
        (_duz_bars(close_last=110.0, hi_last=130.0), {"exit.giveback_pct": 0.3}, 5),
    ]
    for bars, ek, held in senaryolar:
        d0 = strat.manage_position(bars, _poz(), {**ek}, bars_held=held, regime_ok=True)
        d1 = strat.manage_position(bars, _poz(), {**ek, **esli}, bars_held=held, regime_ok=True)
        assert (d0.exit_now, d0.exit_reason, d0.trail_stop) == (d1.exit_now, d1.exit_reason, d1.trail_stop)


def test_a3_evaluate_entry_ozdesligi_anahtar_yokken():
    """Giriş tarafı: skor, anahtarlar yokken ve açıkça varsayılan değerleriyle verildiğinde BİREBİR."""
    df = staircase_bars()
    esli = {"entry.vol_score_sat": 3.0, "entry.rvol_band_center": 1.75,
            "entry.rvol_band_halfwidth": 0.75, "entry.rs_dual_pace": 3.0,
            "entry.w_rvolband": 0.2}
    sub, sig0 = _ilk_sinyal(df, {**LOOSE, "entry.w_rvolband": 0.2})
    assert sig0 is not None, "staircase kırılımı sinyal üretmeli (deterministik tohum)"
    sig1 = strat.evaluate_entry(sub, {**LOOSE, **esli}, 85, "T")
    assert sig1 is not None and sig1.score == sig0.score


def test_a4_rvol_band_score_varsayilan_yolu_birebir():
    """Fonksiyonun eski tek-argümanlı çağrısı aynen yaşar (test_score_rebuild_v115:207 çivisiyle
    uyumlu) ve açık varsayılanlarla çağrı aynı sayıyı verir."""
    assert strat.rvol_band_score(strat.RVOL_BAND_CENTER) == 100.0
    for rv in (0.9, 1.75, 2.4, 3.1):
        assert strat.rvol_band_score(rv) == strat.rvol_band_score(
            rv, center=strat.RVOL_BAND_CENTER, halfwidth=strat.RVOL_BAND_HALFWIDTH)
    assert strat.rvol_band_score(None) is None                      # uydurma yasağı: ölçülemeyen None


# =================================================================================================
# B) KABLO GERÇEKTEN BAĞLI — anahtar verildiğinde okunuyor (pozitif kontroller)
# =================================================================================================
def test_b1_trail_arm_r_okunuyor_iki_yonde():
    bars = _duz_bars(close_last=104.0)                              # kâr 4 = 0.8R
    p_yok = {}
    p_erken = {"exit.trail_arm_r": 0.5}                             # 0.5R'de silahlan → ratchet VAR
    d_yok = strat.manage_position(bars, _poz(), p_yok, bars_held=5, regime_ok=True)
    d_erken = strat.manage_position(bars, _poz(), p_erken, bars_held=5, regime_ok=True)
    assert d_erken.trail_stop > d_yok.trail_stop                    # düğme okundu, trail erken sıkılaştı

    bars2 = _duz_bars(close_last=120.0)                             # kâr 4R — varsayılan ratchet'ler
    p_gec = {"exit.trail_arm_r": 99.0, "exit.breakeven_r": 0.0}     # breakeven'ı izole et
    d_var = strat.manage_position(bars2, _poz(), {"exit.breakeven_r": 0.0}, bars_held=5, regime_ok=True)
    d_gec = strat.manage_position(bars2, _poz(), p_gec, bars_held=5, regime_ok=True)
    assert d_var.trail_stop > d_gec.trail_stop                      # 99R eşiği ratchet'i kapattı
    assert d_gec.trail_stop == _poz()["stop"]                       # hiç silahlanmadı → sert stopta


def test_b2_trail_arm_r_chandelier_i_de_kapsar():
    """Chandelier aynı silahlanma eşiğini okur (aynı 'kâr > arm·R' sabitiydi, tek düğme)."""
    bars = _duz_bars(close_last=120.0, hi_last=140.0)
    ortak = {"exit.chandelier_lookback": 10, "exit.breakeven_r": 0.0}
    d_acik = strat.manage_position(bars, _poz(), ortak, bars_held=5, regime_ok=True)
    d_kapali = strat.manage_position(bars, _poz(), {**ortak, "exit.trail_arm_r": 99.0},
                                     bars_held=5, regime_ok=True)
    assert d_acik.trail_stop > d_kapali.trail_stop


def test_b3_giveback_arm_r_okunuyor():
    bars = _duz_bars(close_last=110.0, hi_last=130.0)               # zirve kârı 30=6R, geri-verme %66
    p = {"exit.giveback_pct": 0.3}
    d_var = strat.manage_position(bars, _poz(), p, bars_held=5, regime_ok=True)
    assert d_var.exit_now and d_var.exit_reason == "giveback"       # bugünkü davranış (arm=1R)
    d_gec = strat.manage_position(bars, _poz(), {**p, "exit.giveback_arm_r": 99.0},
                                  bars_held=5, regime_ok=True)
    assert not d_gec.exit_now                                       # 99R eşiği giveback'i silahsızlandırdı


def test_b4_vol_score_sat_okunuyor(sandbox_state):
    df = staircase_bars()
    sub, sig0 = _ilk_sinyal(df, dict(LOOSE))
    assert sig0 is not None
    sig1 = strat.evaluate_entry(sub, {**LOOSE, "entry.vol_score_sat": 1.0}, 85, "T")
    # doyma 1.0'a inince vol_score=100'e oturur; staircase kırılım vr'si ~2.5 < 3 olduğundan
    # varsayılan vol_score < 100 idi → bileşik skor YUKARI oynar (yön ölçülü, işaret belli).
    assert sig1 is not None and sig1.score > sig0.score
    # işaretli düşüş çivisi: sat<=0 bozuk elle-yazımdır, formül 3.0 varsayılanına düşer (YASA 4)
    sig2 = strat.evaluate_entry(sub, {**LOOSE, "entry.vol_score_sat": 0.0}, 85, "T")
    assert sig2 is not None and sig2.score == sig0.score


def test_b5_rvol_band_merkez_ve_genislik_okunuyor():
    assert strat.rvol_band_score(2.0, center=2.0, halfwidth=0.75) == 100.0
    assert strat.rvol_band_score(1.75, center=2.0, halfwidth=0.75) == pytest.approx(
        100.0 * (1.0 - 0.25 / 0.75))
    assert strat.rvol_band_score(1.75, center=1.75, halfwidth=0.25) == 100.0
    # işaretli düşüş: yarı-genişlik <= 0 bölme-sıfırı üretirdi; modül varsayılanına düşer (YASA 4)
    assert strat.rvol_band_score(1.0, halfwidth=0.0) == strat.rvol_band_score(1.0)

    df = staircase_bars()
    p0 = {**LOOSE, "entry.w_rvolband": 0.2}
    sub, sig0 = _ilk_sinyal(df, p0)
    assert sig0 is not None
    sig1 = strat.evaluate_entry(sub, {**p0, "entry.rvol_band_center": 2.5}, 85, "T")
    assert sig1 is not None and sig1.score != sig0.score            # merkez kaydı → bileşik skor oynadı


def test_b6_rs_dual_pace_okunuyor():
    """Çift-ufuk kapısı açıkken (rs_dual_horizon=1) pro-rata çarpanı params'tan okunur. Ölçülen
    momentumlardan iki pace türetilir: biri kapıyı GEÇİRTEN, biri KESEN — düğme iki yönde bağlı."""
    df = staircase_bars()
    aday = None
    for sub, _sig in _sinyaller(df, dict(LOOSE)):
        c = sub["close"]
        ms = float(c.iloc[-1] / c.iloc[-22] - 1.0)
        ml = float(c.iloc[-1] / c.iloc[-64] - 1.0)
        if ms > 1e-6 and ml > 1e-6:                                 # iki yöne de çevrilebilir örnek
            aday = (sub, ms, ml)
            break
    assert aday is not None, "staircase'te iki-momentumu-pozitif sinyal olmalı (deterministik tohum)"
    sub, ms, ml = aday
    oran = ml / ms
    p1 = {**LOOSE, "entry.rs_dual_horizon": 1}
    gecen = strat.evaluate_entry(sub, {**p1, "entry.rs_dual_pace": oran * 2.0}, 85, "T")
    kesen = strat.evaluate_entry(sub, {**p1, "entry.rs_dual_pace": oran * 0.5}, 85, "T")
    assert gecen is not None and kesen is None
    # özdeşlik: anahtar yokken sonuç, pace=3.0 ile birebir aynı (kablonun kendisi nötr)
    v0 = strat.evaluate_entry(sub, p1, 85, "T")
    v3 = strat.evaluate_entry(sub, {**p1, "entry.rs_dual_pace": 3.0}, 85, "T")
    assert (v0 is None) == (v3 is None)


# =================================================================================================
# C) YAŞAM-DÖNGÜSÜ TABLOSU — yeni okunan anahtarlar no-op dedektörünün kopya-tablosunda
# =================================================================================================
def test_c1_lifecycle_tablosu_yeni_anahtarlari_tasiyor():
    """manage_position'da okunan her yaşam-döngüsü anahtarı LIFECYCLE_READ_DEFAULTS'ta durur
    (tablo bir KOPYADIR; AST çivisi test_golge_v2_yasam_dongusu_v132 kaynakla eşitliğini ayrıca
    denetler). Giriş anahtarları tabloya BİLEREK girmez (tablonun kendi gerekçesi)."""
    assert sl.LIFECYCLE_READ_DEFAULTS["exit.trail_arm_r"] == (1.0, "strategy.manage_position")
    assert sl.LIFECYCLE_READ_DEFAULTS["exit.giveback_arm_r"] == (1.0, "strategy.manage_position")
    for k in ("entry.vol_score_sat", "entry.rvol_band_center", "entry.rvol_band_halfwidth",
              "entry.rs_dual_pace"):
        assert k not in sl.LIFECYCLE_READ_DEFAULTS


# =================================================================================================
# D) WP3-B BEŞLİSİ — ölçülen mevcut durum çivilenir (dördü kablolu, scale_out beyan taşır)
# =================================================================================================
def test_d1_scale_out_silahlanma_beyani_kaynak_yorumunda():
    """scale_out kablosu bounds+params'ta VAR ama alet KAPALI: EDG-2026-027/029 hükmü + WP1-C
    latent kusur. 'Silahlanması 027 hükmüne tabidir' beyanı kaynak yorumunda DURMAK ZORUNDA —
    düğme bir gün açılacaksa önce o hüküm ve kusur masaya döner (emsal: test_ops_v11 kaynak çivisi)."""
    src = inspect.getsource(broker.PaperBroker.scale_out)
    assert "EDG-2026-027" in src and "WP1-C" in src and "silahlanma" in src.lower()


def test_d2_bes_adayin_olculen_konumu(sandbox_state):
    """Envanter çivisi: derisk bandı goal-limits kablosunda (LIMIT_KEYS — arama GÖREMEZ, operatör
    kalemi), max_open aynı sınıfta; position_size_r / scale_out / chandelier bounds'ta ARANabilir."""
    assert {"derisk_full_dd", "derisk_floor_dd", "max_open_positions"} <= guard.LIMIT_KEYS
    b = config.bounds()
    for k in ("position_size_r", "exit.scale_out_r", "exit.scale_out_frac", "exit.chandelier_lookback"):
        assert k in b
    for k in ("derisk_full_dd", "derisk_floor_dd", "max_open_positions"):
        assert k not in b                       # risk vanası arama uzayına girmez (yürürlükteki politika)
    # derisk fail-safe kablosu yaşıyor (v237'nin özeti — monkeypatch'siz ölçülebilir)
    assert broker.derisk_ramp({})["kaynak"] == {"full_dd": "kod varsayilani",
                                                "floor_dd": "kod varsayilani"}
