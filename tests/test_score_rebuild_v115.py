"""test_score_rebuild_v115.py — G2 SKOR YENİDEN İNŞASI, BİRİNCİ TUR (2026-07-29).

BU TURUN İDDİASI ŞU DEĞİL: "yeni skor daha iyi." Öyle bir iddia ancak kapıdan geçen bir ölçümle
kurulabilir ve o ölçüm bir sonraki turun işidir. Bu turun iddiası şudur: **üç yeni bileşen üretim
koduna girdi ve CANLI DAVRANIŞ ZERRE DEĞİŞMEDİ.** Bir "sıfır etkili ekleme" turunun tek gerçek
kanıtı, sıfırlığın kendisinin çivilenmesidir — yoksa "varsayılan kapalı" cümlesi bir niyet
beyanından ibaret kalır ve bir sonraki tur onun üstüne inşa eder.

ÇİVİLENEN YASALAR:
  A. Göstergeler nedenseldir, ısınmadan NaN döner ve rvol20'nin tanımı ÖLÇÜLEN tanımdır.
  B. SIFIR-ETKİ ÇİVİSİ: 20 sembolde bileşik skor, G2 ÖNCESİ formülün birebir aynısıdır.
  C/D. Bant ve rütbe şekilleri kanıt tablosunun söylediği biçimdedir (bant MONOTON DEĞİL).
  E. CANLI/BACKTEST PARİTESİ: 340 barlık kuyruk ile tam seri AYNI sayıyı üretir — mom rütbe
     penceresi (63) tam olarak bu yüzden 88'in altında seçildi; bu test o seçimin bekçisidir.
  F. Bileşenler deftere ALAN olarak yazılır, `notes` METNİNE değil (component_ic'in 1. tasarım
     kararında teşhis edilen hatanın tekrarlanmadığının kanıtı).
  G. rvol taban filtresi varsayılan KAPALI; açıkken ölçülemeyen rvol'ü GEÇİRMEZ.
  H. bounds.yaml'a EKLEME yapıldı, mevcut satırlar DEĞİŞMEDİ.
  I. component_ic yeni bileşenleri ölçer ve ölçek beyanını çıktısına taşır.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import pytest
import yaml

from meridian import component_ic, config, indicators as ind, store, strategy as strat
from tests.test_learning_roundtrip_v76 import staircase_bars

REPO = pathlib.Path(__file__).resolve().parent.parent

# Kapıları gevşetilmiş param seti: bu dosyanın sorusu "kaç sinyal geçiyor" değil, "geçen sinyalin
# SKORU değişti mi" — eşikler dar kalsaydı ölçülecek örneklem kalmazdı.
LOOSE = {"entry.pivot_proximity_pct": 8.0, "entry.min_volume_ratio": 1.0, "entry.min_score": 40}


def _uzun_seri(n: int = 700, seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1 + rng.normal(0.0005, 0.01, n))
    high = close * (1 + np.abs(rng.normal(0, 0.003, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.003, n)))
    return pd.DataFrame({"date": pd.bdate_range("2021-01-04", periods=n), "open": close * 0.999,
                         "high": high, "low": low, "close": close,
                         "volume": rng.integers(1_000_000, 3_000_000, n).astype(float)})


def _endeks_serisi(n: int = 700, seed: int = 9, tarihli: bool = True) -> pd.Series:
    """Endeks (SPY vekili) kapanışları. `tarihli=False` → KONUM indeksli: `_uzun_seri`nin satır
    ekseniyle doğrudan hizalı, yani göstergeyi hizalama katmanı OLMADAN çağıran testler için."""
    rng = np.random.default_rng(seed)
    c = 400.0 * np.cumprod(1 + 0.0004 + rng.normal(0, 0.006, n))
    return pd.Series(c, index=pd.bdate_range("2021-01-04", periods=n) if tarihli else range(n))


def _ilk_sinyal(df: pd.DataFrame, params: dict, rs: int = 85, ticker: str = "T"):
    """Merdiven serisinde ATEŞLEYEN ilk kırılım barını bul → (dilim, sinyal)."""
    for i in range(400, len(df)):
        sub = df.iloc[:i + 1].reset_index(drop=True)
        sig = strat.evaluate_entry(sub, params, rs, ticker)
        if sig is not None:
            return sub, sig
    return None, None


# =================================================================================================
# A) GÖSTERGE YASALARI
# =================================================================================================
_A_BARS = _uzun_seri()
_A_INDEX = _endeks_serisi(tarihli=False)          # ham gösterge çağrısı: etiketler birebir hizalı
_A_FNS = {
    "rvol20": lambda df: ind.rvol20(df["volume"]),
    "mom_12_1": lambda df: ind.mom_12_1(df["close"]),
    "residual_momentum": lambda df: ind.residual_momentum(df["close"], _A_INDEX),
}


@pytest.mark.parametrize("ad", sorted(_A_FNS))
def test_a1_yeni_gostergeler_ILERI_DONUK_DEGIL(ad):
    """ALTIN KURAL (indicators_audit_v30 I1): geçmişin değeri, gelecek barlar eklenince DEĞİŞMEZ.

    Yeni bileşenler bu batarya yazıldıktan sonra eklendiği için oradaki kayıt onları görmüyordu;
    üstelik oradaki fikstür 320 barlık ve mom/rmom orada TAMAMEN NaN olurdu — yani test geçer ama
    hiçbir şey ölçmezdi. Bu yüzden yasa burada, ısınmayı DOLDURAN 700 barlık seride koşturulur."""
    fn = _A_FNS[ad]
    kesik = 600
    tam = fn(_A_BARS).iloc[:kesik].to_numpy(dtype=float)
    kes = fn(_A_BARS.iloc[:kesik].copy()).to_numpy(dtype=float)
    ayni = np.isclose(tam, kes, rtol=1e-12, atol=1e-12, equal_nan=True)
    assert ayni.all(), f"{ad}: {int((~ayni).sum())} değer gelecek barlarla DEĞİŞTİ → ileri-dönük"
    assert np.isfinite(tam).any(), f"{ad}: 600 barda tek ölçülebilen değer yok — test boş koşuyor"


def test_a2_isinma_dolmadan_NaN_uydurma_yok():
    """Isınma penceresi TAM olmalı: yarım pencereyle hesaplanmış bir sayı ölçülmüş gibi dönmez."""
    assert ind.rvol20(_A_BARS["volume"]).first_valid_index() == ind.RVOL_WINDOW - 1
    assert ind.mom_12_1(_A_BARS["close"]).first_valid_index() == ind.MOM_LOOKBACK
    # rmom iki katmanlı ısınır: beta 252 + artık penceresi 231 + atlama 21 → ilk değer 503. bar.
    beklenen = ind.BETA_WINDOW + ind.RESID_WINDOW + ind.MOM_SKIP - 1
    assert ind.residual_momentum(_A_BARS["close"], _A_INDEX).first_valid_index() == beklenen


def test_a3_endeks_yoksa_rmom_TAMAMEN_olculemedi():
    """Endeks serisi olmadan artık momentum TANIMSIZDIR — 0.0 değil NaN (uydurma yasağı)."""
    bos = ind.residual_momentum(_A_BARS["close"], None)
    assert len(bos) == len(_A_BARS) and bool(bos.isna().all())


def test_a4_rvol20_OLCULEN_tanimla_birebir_ve_volume_ratio_DEGIL():
    """rvol20'nin paydası BUGÜNÜ İÇERİR ve bu, `volume_ratio`nun bilinçli tersidir (docstring'de
    gerekçeli). Bu test iki şeyi birden çiviler: (1) kod, g2_olcum'un ölçtüğü tanımın ta kendisi;
    (2) iki tanım GERÇEKTEN farklı sayı üretiyor — yani "aynı şey, ne fark eder" savunması yanlış.
    Bant kenarları (1.5/2.0/1.75±0.75) ölçülen tanıma aittir; tanım kayarsa kenarlar anlamsızlaşır."""
    vol = _A_BARS["volume"]
    olculen = vol / vol.rolling(20).mean()                 # g2_olcum.py satır 72 ile BİREBİR
    assert np.allclose(ind.rvol20(vol).to_numpy(dtype=float),
                       olculen.to_numpy(dtype=float), equal_nan=True)
    haric = vol / vol.shift(1).rolling(20, min_periods=20).mean()   # volume_ratio biçimi
    fark = (ind.rvol20(vol) - haric).abs().dropna()
    assert float(fark.max()) > 0.01, "iki tanım aynı sayıyı veriyor — testin ayırt ettiği şey yok"


# =================================================================================================
# B) SIFIR-ETKİ ÇİVİSİ — TURUN ASIL İDDİASI
# =================================================================================================
def _g2_oncesi_skor(df: pd.DataFrame, params: dict, rs: int) -> int:
    """G2 ÖNCESİ bileşik skor formülü, satır satır (strategy.py 2026-07-29 öncesi hâli).

    Referansı testin içinde YENİDEN YAZMAK bilinçli: üretim koduna bakıp "sıfır ekledik, değişmez"
    demek bir muhakemedir, ölçüm değil. Burada eski formül bağımsız olarak kurulur ve yeni kodun
    çıktısıyla karşılaştırılır — ikisi ayrışırsa test kırılır, gerekçe ne olursa olsun."""
    piv = float(ind.pivot_high(df["high"], strat.PIVOT_LOOKBACK, exclude_recent=1).iloc[-1])
    c = float(df["close"].iloc[-1])
    vr = float(ind.volume_ratio(df["volume"], 50).iloc[-1])
    tt = float(ind.trend_template(df).iloc[-1])
    prox_max = float(params.get("entry.pivot_proximity_pct", 2.0))
    prox_pct = (c - piv) / piv * 100.0
    prox_score = 100.0 * (1.0 - min(prox_pct / prox_max, 1.0)) if prox_max > 0 else 0.0
    vol_score = 100.0 * min(vr / 3.0, 1.0)
    w_rs = float(params.get("entry.w_rs", 0.35)); w_tt = float(params.get("entry.w_tight", 0.30))
    w_vol = float(params.get("entry.w_vol", 0.20)); w_px = float(params.get("entry.w_prox", 0.15))
    w_sum = max(w_rs + w_tt + w_vol + w_px, 1e-9)
    return int(round((w_rs * rs + w_tt * (tt * 100.0)
                      + w_vol * vol_score + w_px * prox_score) / w_sum))


def test_b1_YIRMI_sembolde_skor_G2_ONCESIYLE_BIREBIR():
    """ÇİVİ: varsayılan parametrelerle üretilen her sinyalin skoru, G2 öncesi formülün aynısı."""
    olculen = 0
    for seed in range(20):
        df = staircase_bars(n=600, seed=seed)
        sub, sig = _ilk_sinyal(df, LOOSE, rs=85, ticker=f"S{seed}")
        if sig is None:
            continue
        olculen += 1
        assert sig.score == _g2_oncesi_skor(sub, LOOSE, 85), \
            f"seed={seed}: skor G2 öncesinden SAPTI ({sig.score})"
    assert olculen >= 15, f"20 sembolün yalnız {olculen}'inde sinyal doğdu — çivi örneklemsiz kaldı"


def test_b2_yeni_dugmeler_ACIKCA_SIFIR_verilince_de_ayni():
    """Düğmeler param sözlüğünde YOKKEN (varsayılan) ve AÇIKÇA 0.0 iken aynı sonucu vermeli —
    aksi hâlde "varsayılan kapalı" ile "sıfıra ayarlı" iki farklı davranış olurdu."""
    df = staircase_bars(n=600, seed=1)
    sub, taban = _ilk_sinyal(df, LOOSE, 85)
    assert taban is not None
    acik = strat.evaluate_entry(sub, {**LOOSE, "entry.w_rvolband": 0.0, "entry.w_mom": 0.0,
                                      "entry.min_rvol": 0.0}, 85, "T")
    assert acik is not None and acik.as_row() == taban.as_row()


def test_b3_agirlik_ACILINCA_skor_gercekten_degisir():
    """Sıfır-etki çivisi ancak düğmenin AÇIKKEN etkili olduğu gösterilirse anlamlıdır; yoksa test
    "hiçbir şey yapmayan kod hiçbir şey yapmıyor" demekten ibaret olurdu."""
    df = staircase_bars(n=600, seed=1)
    sub, taban = _ilk_sinyal(df, LOOSE, 85)
    assert taban is not None
    degisenler = set()
    for anahtar in ("entry.w_rvolband", "entry.w_mom"):
        s = strat.evaluate_entry(sub, {**LOOSE, anahtar: 0.40}, 85, "T")
        if s is not None and s.score != taban.score:
            degisenler.add(anahtar)
    assert degisenler == {"entry.w_rvolband", "entry.w_mom"}, \
        f"açıldığı hâlde skoru değiştirmeyen düğme(ler) var: {degisenler}"


def test_b4_agirlikli_bilesen_OLCULEMEZSE_kurulum_YOK():
    """Isınması dolmamış bir bileşen ağırlıklıyken skor "kalanlara göre" normalize EDİLMEZ.
    Üç bileşenden hesaplanmış bir sayıyı dört bileşenlik gibi raporlamak, trend_template'in
    2026-07-22'de düzeltilen hatasının aynısıdır."""
    df = staircase_bars(n=600, seed=1)
    sub, taban = _ilk_sinyal(df, LOOSE, 85)
    assert taban is not None
    kisa = sub.tail(300).reset_index(drop=True)          # mom rütbe penceresi (252+63) DOLMAZ
    assert strat.mom_rank_score(ind.mom_12_1(kisa["close"])) is None
    assert strat.evaluate_entry(kisa, {**LOOSE, "entry.w_mom": 0.30}, 85, "T") is None
    assert strat.evaluate_entry(kisa, LOOSE, 85, "T") is not None, \
        "ağırlık 0 iken ölçülemeyen bileşen sembolü elemiş — sıfır-etki ihlali"


# =================================================================================================
# C) RVOL BANT ŞEKLİ
# =================================================================================================
def test_c1_bant_tepesi_kanit_bandinin_ortasinda():
    assert strat.rvol_band_score(strat.RVOL_BAND_CENTER) == 100.0
    assert strat.rvol_band_score(1.5) == pytest.approx(100.0 * (1 - 0.25 / 0.75))
    assert strat.rvol_band_score(2.0) == pytest.approx(100.0 * (1 - 0.25 / 0.75))
    for uc in (1.0, 2.5, 3.0, 10.0, 0.0):
        assert strat.rvol_band_score(uc) == 0.0


def test_c2_bant_MONOTON_DEGIL_kanit_boyle_soyluyor():
    """Kanıt (g2_olcum cf, 20 bar): 0.8-1.5 → -0.52%, 1.5-2.0 → +1.84%, 2.0+ → +1.44%. Yani "ne
    kadar çok hacim o kadar iyi" YANLIŞ. Mevcut `vol_score` (min(vr/3,1)) monotondur; yeni bileşen
    onun yerine geçmez, YANINDA durur ve hangisinin doğru olduğunu kapı ölçer."""
    assert strat.rvol_band_score(1.2) < strat.rvol_band_score(1.75)      # sol kol yükselir
    assert strat.rvol_band_score(2.4) < strat.rvol_band_score(1.75)      # sağ kol düşer
    assert strat.rvol_band_score(4.0) < strat.rvol_band_score(1.6), \
        "çok yüksek hacim tatlı noktadan daha iyi puanlanıyor — bant yapısı kaybolmuş"


def test_c3_olculemeyen_rvol_bant_puani_UYDURMAZ():
    assert strat.rvol_band_score(None) is None
    assert strat.rvol_band_score(float("nan")) is None


# =================================================================================================
# D) MOM YÜZDELİK RÜTBESİ
# =================================================================================================
def test_d1_rutbe_araliktadir_ve_momentumla_ARTAR():
    artan = pd.Series(np.linspace(-0.5, 0.5, 200))
    azalan = pd.Series(np.linspace(0.5, -0.5, 200))
    assert strat.mom_rank_score(artan) == pytest.approx(100.0)
    assert strat.mom_rank_score(azalan) == pytest.approx(100.0 / strat.MOM_RANK_WINDOW)
    for seri in (artan, azalan):
        assert 0.0 < strat.mom_rank_score(seri) <= 100.0


def test_d2_pencere_dolmadan_None():
    assert strat.mom_rank_score(pd.Series(np.arange(strat.MOM_RANK_WINDOW - 1, dtype=float))) is None
    yarim = pd.Series([np.nan] * 10 + list(np.arange(strat.MOM_RANK_WINDOW, dtype=float)))
    assert strat.mom_rank_score(yarim.iloc[-strat.MOM_RANK_WINDOW - 5:]) is not None
    delikli = pd.Series(np.arange(strat.MOM_RANK_WINDOW, dtype=float))
    delikli.iloc[0] = np.nan
    assert strat.mom_rank_score(delikli) is None, "pencerede NaN varken yüzdelik uydurulmuş"


# =================================================================================================
# E) CANLI/BACKTEST PARİTESİ — §4'ün doğrudan uygulaması
# =================================================================================================
def test_e1_340_BARLIK_KUYRUK_tam_seriyle_AYNI_karari_verir():
    """Canlı tarama (loop/cf_backfill/backtest, hepsi tail(340)) ile tam seriyi okuyan yol AYNI
    sayıyı üretmeli. mom rütbe penceresi 63 tam olarak bunun için seçildi: mom_12_1 ilk değerini
    253. barda verdiğinden 340 barlık kuyrukta yalnız 88 okuma vardır; pencere 88'i aşsaydı iki
    yol sessizce ayrışır ve her backtest sayısı bir yalana dönerdi. Bu test o seçimin bekçisidir —
    biri MOM_RANK_WINDOW'u büyütürse burada kırılır."""
    assert ind.MOM_LOOKBACK + strat.MOM_RANK_WINDOW <= 340, \
        "mom rütbe penceresi canlı kuyruğa sığmıyor — canlı ve backtest ayrışır"
    agirlikli = {**LOOSE, "entry.w_rvolband": 0.30, "entry.w_mom": 0.25}
    karsilastirilan = 0
    for seed in range(6):
        df = staircase_bars(n=800, seed=seed)
        sub, sig = _ilk_sinyal(df, agirlikli, 85, f"S{seed}")
        if sig is None:
            continue
        kuyruk = sub.tail(340).reset_index(drop=True)
        kuyruk_sig = strat.evaluate_entry(kuyruk, agirlikli, 85, f"S{seed}")
        assert kuyruk_sig is not None, f"seed={seed}: kuyrukta sinyal KAYBOLDU"
        assert kuyruk_sig.as_row() == sig.as_row(), f"seed={seed}: kuyruk/tam seri AYRIŞTI"
        karsilastirilan += 1
    assert karsilastirilan >= 4, f"yalnız {karsilastirilan} karşılaştırma yapıldı — parite ölçülmedi"


def test_e2_rmom_canli_kuyrukta_OLCULEMEZ_ve_bu_yazili():
    """indicators.residual_momentum docstring'inin iddiası: 340 barlık kuyruk rmom'un ısınmasını
    (~483 bar) doldurmaz. İddia testle bağlanmazsa docstring bir gün sessizce yanlış olur."""
    df = _uzun_seri(700)
    idx = _endeks_serisi(700, tarihli=False)
    assert not pd.isna(ind.residual_momentum(df["close"], idx).iloc[-1])
    kuyruk = df.tail(340).reset_index(drop=True)
    kuyruk_idx = idx.tail(340).reset_index(drop=True)
    assert pd.isna(ind.residual_momentum(kuyruk["close"], kuyruk_idx).iloc[-1])


def test_e3_hizasiz_endeks_serisi_SESSIZ_KALMAZ():
    """Tarih-indeksli endeks + konum-indeksli bar kuyruğu = klasik hizalama tuzağı. Sessiz NaN,
    'ölçülemedi' kılığında bir hata raporlardı; artık adıyla patlar. (Tarama yolu bu tuzağa
    düşmez: `strategy._align_index_close` hizayı önce kurar — bkz. test_f3.)"""
    df = _uzun_seri(700)
    with pytest.raises(ValueError, match="ortak etiket"):
        ind.residual_momentum(df["close"], _endeks_serisi(700, tarihli=True))


# =================================================================================================
# F) DEFTER ALANLARI — "notes metnine gömme" hatası tekrarlanmadı
# =================================================================================================
def test_f1_bilesenler_ALAN_olarak_yazilir_METNE_gomulmez():
    df = staircase_bars(n=600, seed=1)
    sub, sig = _ilk_sinyal(df, LOOSE, 85)
    assert sig is not None
    row = sig.as_row()
    for alan in ("rvol20", "mom_12_1", "rmom"):
        assert alan in row, f"'{alan}' defter satırında ALAN olarak yok"
    assert row["rvol20"] is not None and row["mom_12_1"] is not None
    # `notes` DEĞİŞMEMELİ: bileşeni bir daha metne gömmek, ölçümü string biçimine bağımlı yapardı.
    for iz in ("rvol", "mom", "rmom"):
        assert iz not in row["notes"], f"yeni bileşen `notes` metnine sızmış: {row['notes']}"


def test_f2_olculemeyen_bilesen_None_kalir_SIFIR_olmaz():
    """Her alan KENDİ ısınmasına göre ayrı ayrı dürüst: 300 barlık bir kuyrukta rvol ve ham mom
    ölçülebilir, ama mom'un 63-barlık yüzdelik penceresi (252+63) dolmaz ve rmom'un endeksi yoktur.
    Ölçülemeyen her biri None kalır — 0.0 yazmak "hacim yok / momentum sıfır" demek olurdu ve
    gelecekteki IC ölçümü o sıfırları gerçek gözlem sanardı."""
    df = staircase_bars(n=600, seed=1)
    sub, _ = _ilk_sinyal(df, LOOSE, 85)
    kisa = sub.tail(300).reset_index(drop=True)
    sig = strat.evaluate_entry(kisa, LOOSE, 85, "T")
    assert sig is not None
    assert sig.rvol20 is not None and sig.rvol20 > 0
    assert sig.mom_12_1 is not None                       # ham 12-1 için 253 bar yeter
    assert strat.mom_rank_score(ind.mom_12_1(kisa["close"])) is None      # rütbe penceresi dolmadı
    assert sig.rmom is None and sig.as_row()["rmom"] is None


def test_f2b_diger_kurulumlar_bilesenleri_UYDURMAZ():
    """breakout dışındaki kurulumlar bu bileşenleri HESAPLAMAZ; satırlarında alan None olmalı.
    0.0 yazılsaydı, defterdeki 'rvol20=0' satırları ölçüm zamanı gerçek gözlem sayılırdı."""
    sig = strat.EntrySignal(ticker="T", setup="pullback", entry_trigger=10.0, pivot=9.0, stop=8.0,
                            atr=0.5, rs_rating=80, score=70, profit_target=12.0, size_r=1.0,
                            r_per_share=2.0, notes="pullback")
    assert (sig.rvol20, sig.mom_12_1, sig.rmom) == (None, None, None)
    row = sig.as_row()
    assert row["rvol20"] is None and row["mom_12_1"] is None and row["rmom"] is None


def test_f3_rmom_endeks_verilince_olculur():
    """Alan bugün None çünkü çağıran endeks vermiyor — ama dikiş yeri GERÇEKTEN çalışmalı."""
    df = _uzun_seri(700, seed=5)
    idx = _endeks_serisi(700)
    gevsek = {**LOOSE, "entry.min_score": 0, "entry.rs_rating_min": 0}
    for i in range(560, 700):
        sub = df.iloc[:i + 1].reset_index(drop=True)
        sig = strat.evaluate_entry(sub, gevsek, 85, "T", index_close=idx.iloc[:i + 1])
        if sig is not None:
            assert sig.rmom is not None, "endeks verildiği hâlde rmom ölçülmedi"
            assert strat.evaluate_entry(sub, gevsek, 85, "T").rmom is None
            return
    pytest.skip("bu seride 700 barda kırılım doğmadı — dikiş yeri ölçülemedi")


# =================================================================================================
# G) RVOL TABAN FİLTRESİ (kalem C)
# =================================================================================================
def test_g1_taban_filtresi_VARSAYILAN_KAPALI():
    df = staircase_bars(n=600, seed=1)
    sub, taban = _ilk_sinyal(df, LOOSE, 85)
    assert taban is not None
    assert strat.evaluate_entry(sub, {**LOOSE, "entry.min_rvol": 0.0}, 85, "T").as_row() == taban.as_row()


def test_g2_taban_filtresi_ACILINCA_ELER():
    df = staircase_bars(n=600, seed=1)
    sub, taban = _ilk_sinyal(df, LOOSE, 85)
    assert taban is not None and taban.rvol20 is not None
    altinda = round(taban.rvol20 - 0.2, 4)
    ustunde = round(taban.rvol20 + 0.2, 4)
    assert strat.evaluate_entry(sub, {**LOOSE, "entry.min_rvol": altinda}, 85, "T") is not None
    assert strat.evaluate_entry(sub, {**LOOSE, "entry.min_rvol": ustunde}, 85, "T") is None


def test_g3_olculemeyen_rvol_FILTREYI_GECEMEZ():
    """Kapı girdisi ölçülemiyorsa kapı "serbest" demez — motorun her yerinde (vr/tt) kural budur."""
    df = staircase_bars(n=600, seed=1)
    sub, taban = _ilk_sinyal(df, LOOSE, 85)
    assert taban is not None
    kor = sub.copy()
    kor.loc[kor.index[-20:], "volume"] = np.nan          # rvol20 penceresi NaN → ölçülemedi
    assert pd.isna(ind.rvol20(kor["volume"]).iloc[-1])
    assert strat.evaluate_entry(kor, {**LOOSE, "entry.min_rvol": 1.0}, 85, "T") is None


# =================================================================================================
# H) BOUNDS — EKLEME serbest, mevcut satır DEĞİŞMEZ
# =================================================================================================
_YENI_BOUNDS = {"entry.w_rvolband": (0.0, 0.4, 0.05),
                "entry.w_mom": (0.0, 0.4, 0.05),
                "entry.min_rvol": (0.0, 2.0, 0.1)}


@pytest.mark.parametrize("anahtar", sorted(_YENI_BOUNDS))
def test_h1_yeni_dugmeler_bounds_da_ve_KAPALI_hali_araligin_icinde(anahtar):
    b = config.bounds().get(anahtar)
    assert b, f"{anahtar} bounds.yaml'da yok — Hermes onu arayamaz"
    lo, hi, step = _YENI_BOUNDS[anahtar]
    assert float(b["min"]) == lo and float(b["max"]) == hi and float(b["step"]) == step
    assert float(b["min"]) == 0.0, "varsayılan KAPALI değer aralığın dışında kalıyor"


def test_h2_mevcut_bounds_satirlari_DEGISMEDI():
    """Bu tur yalnız EKLEME yapar. Mevcut bir satırın min/max/step'i değişseydi, öğrenme döngüsünün
    geçmişte ürettiği her hipotezin arama uzayı geriye dönük olarak başka bir şey olurdu."""
    b = yaml.safe_load((REPO / "state" / "bounds.yaml").read_text())
    beklenen = {"entry.rs_rating_min": (60, 95, 1), "entry.pivot_proximity_pct": (0.5, 8.0, 0.1),
                "entry.min_volume_ratio": (1.0, 4.0, 0.1), "entry.min_score": (40, 90, 1),
                "entry.w_rs": (0.10, 0.60, 0.05), "entry.w_tight": (0.05, 0.55, 0.05),
                "entry.w_vol": (0.05, 0.45, 0.05), "entry.w_prox": (0.00, 0.40, 0.05),
                "exit.profit_target_r": (2.0, 6.0, 0.5), "stop_loss_atr_mult": (0.8, 4.0, 0.1)}
    for k, (lo, hi, st) in beklenen.items():
        assert (float(b[k]["min"]), float(b[k]["max"]), float(b[k]["step"])) == (lo, hi, st), \
            f"{k} bounds satırı DEĞİŞMİŞ — bu tur yalnız ekleme yapmalıydı"


def test_h3_strategy_yaml_DOKUNULMADI():
    """Canlı davranışın değişmediğinin ikinci çivisi: yeni düğmelerin hiçbiri canlı param setinde
    YOK, yani `_f` varsayılanı (0.0) geçerli."""
    params = yaml.safe_load((REPO / "state" / "strategy.yaml").read_text())["params"]
    for k in _YENI_BOUNDS:
        assert k not in params, f"{k} canlı strategy.yaml'a sızmış — bu tur ship turu DEĞİL"


# =================================================================================================
# I) COMPONENT_IC GENİŞLETMESİ
# =================================================================================================
def _mini_evren(monkeypatch, n_gun: int = 400):
    idx = pd.date_range("2024-01-01", periods=n_gun, freq="D")
    df = pd.DataFrame({"open": [100.0 + i * 0.1 for i in range(n_gun)],
                       "high": [100.5 + i * 0.1 for i in range(n_gun)],
                       "low": [99.5 + i * 0.1 for i in range(n_gun)],
                       "close": [100.0 + i * 0.1 for i in range(n_gun)],
                       "volume": [1_000_000 + (i % 7) * 10_000 for i in range(n_gun)]}, index=idx)
    monkeypatch.setattr(component_ic, "_load_universe", lambda: {"AAA": df})
    monkeypatch.setattr(component_ic, "_load_index_close", lambda: df["close"] * 0.5)
    return idx


def test_i1_yeni_bilesenler_TABLODA_ve_agirlik_esleismesi_dogru():
    assert set(component_ic.COMPONENTS) >= {"rvol20", "mom12_1", "rmom"}
    assert set(component_ic.COMPONENTS) >= {"rs", "tight", "vol", "prox"}, \
        "eski bileşenler düşmüş — yeni çekirdeğin kıyas tabanı yok olur"
    assert component_ic.COMPONENT_WEIGHT_KEY["rvol20"] == "entry.w_rvolband"
    assert component_ic.COMPONENT_WEIGHT_KEY["mom12_1"] == "entry.w_mom"
    assert component_ic.COMPONENT_WEIGHT_KEY["rmom"] is None, \
        "rmom'a ağırlık düğmesi bağlanmış — yedek aday skora giremez"


def test_i2_gece_kosusu_yeni_satirlari_URETIR(sandbox_state, monkeypatch):
    idx = _mini_evren(monkeypatch)
    gunler = [str(d.date()) for d in idx[250:340]]
    store.write_jsonl("trades.jsonl", [
        {"id": f"T{i:05d}", "plan_id": f"P-{g}-AAA", "score": 70, "r_multiple": 0.1}
        for i, g in enumerate(gunler)])
    doc = component_ic.component_ic()
    assert doc is not None
    for c in ("rvol20", "mom12_1", "rmom"):
        assert c in doc["components"] and c in doc["tablo"]["gercek"], f"{c} tabloda yok"
        for h in doc["horizons"]:
            hucre = doc["tablo"]["gercek"][c][str(h)]
            assert "ic" in hucre and "n" in hucre
    assert doc["agirliklar"]["rmom"] is None, "ağırlığı olmayan bileşene 0.0 yazılmış"
    assert doc["agirliklar"]["rvol20"] == 0.0 and doc["agirliklar"]["mom12_1"] == 0.0
    assert "MONOTON" in (doc.get("yeni_bilesen_notu") or "").upper(), \
        "ham seri / skor dönüşümü ayrımı çıktıda beyan edilmemiş"


def test_i3_bilesen_frame_yeni_sutunlari_tasir():
    df = _uzun_seri(700)
    frame = component_ic._component_frame(df.set_index("date"), 2.3, _endeks_serisi(700))
    for c in ("rvol20", "mom12_1", "rmom"):
        assert c in frame.columns, f"{c} bileşen çerçevesinde yok"
    assert frame["rvol20"].notna().sum() > 600
    assert frame["mom12_1"].notna().sum() > 400
    assert frame["rmom"].notna().sum() > 100, "rmom hiç ölçülememiş — endeks yolu kopuk"
