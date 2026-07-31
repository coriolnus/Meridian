"""test_signal_math_v73.py — SİNYAL MATEMATİĞİ denetimi (2026-07-22).

Tespit bataryası (7 bütünlük deseni, defter sözleşmesi, düşüş muhasebesi, recompute, kod-yasası,
mutasyon kapsaması) TESİSATI ölçer: satır üretildi mi, korundu mu, birleşti mi, tüketildi mi.
Hiçbiri ARİTMETİĞİN doğru olup olmadığını göremez. Yanlış bir gösterge formülü kusursuz görünen
float'lar üretir, her defter doğrulanır, her dedektör yeşil kalır — ve motor o sayıyla işlem yapar.

Bu dosyadaki her test ya BİR kusuru elle-doğrulanabilir bir girdiyle yeniden üretir, ya da doğru
olduğu ölçülmüş bir davranışı KİLİTLER (pozitif kontrol — yoksa geçen test boş bir tören olur).

  V1  volume_ratio paydası BUGÜNÜ içeriyordu → oran 1.0'a doğru sıkışıyordu (kusur)
  T1  trend_template'in "52 haftalık" penceresi 100 barda açılıyordu; ısınma sabiti 220'ydi (kusur)
  C1  chandelier trail penceresi GİRİŞTEN ÖNCEYE uzanıyordu (kusur, bugün uykuda)
  R1  regime.classify 200 bar yokken 59-150 barlık ortalamayı "sma200" diye raporluyor,
      220 bar yokken "200g ortalama yükseliyor" koşulunu KANITSIZ geçiriyordu (kusur)
  P*  pozitif kontroller: ATR gerçekten Wilder; dört kurulumun hiçbirinde ileri-dönük bilgi yok
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import pytest

from meridian import config, indicators as ind, regime as rg, strategy as strat

REPO = pathlib.Path(__file__).resolve().parent.parent
BARS_DIR = REPO / "state" / "bars"          # SALT OKUNUR — canlı önbellek, hiçbir test yazmaz


def _real(ticker: str, since: str = "2021-01-01") -> pd.DataFrame:
    """Gerçek önbelleklenmiş barlar. Yoksa test atlanır (kanıt uydurmayız)."""
    p = BARS_DIR / f"{ticker.lower()}.csv"
    if not p.exists():
        pytest.skip(f"gerçek bar önbelleği yok: {p.name}")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df[df["date"] >= pd.Timestamp(since)].reset_index(drop=True)
    if len(df) < 300:
        pytest.skip(f"{ticker}: {len(df)} bar — kanıt için yetersiz")
    return df


def _linear_bars(n: int, first: float, last: float, start: str = "2020-01-01") -> pd.DataFrame:
    """Elle hesaplanabilir seri: kapanış doğrusal, gün içi aralık kapanışın ±%0.1'i, hacim sabit."""
    close = np.linspace(first, last, n)
    return pd.DataFrame({"date": pd.bdate_range(start, periods=n), "open": close,
                         "high": close * 1.001, "low": close * 0.999, "close": close,
                         "volume": np.full(n, 1_000_000.0)})


# =================================================================================================
# V1 — volume_ratio: "bugünün hacmi / GEÇMİŞ ortalaması" (payda bugünü içeremez)
# =================================================================================================
def test_v1_volume_ratio_denominator_excludes_the_current_bar():
    """ELLE: 50 seans boyunca hacim 100, bugün 300 → oran TAM 3.0.

    Eski formül (`volume.rolling(50)`) bugünü kendi ortalamasının içine koyuyordu:
    300 / ((49·100 + 300)/50) = 300/104 = 2.8846 — yani %3,85 EKSİK. Sapma tam olarak
    50/(49+r) çarpanıdır: oranı her zaman 1.0'a doğru sıkıştırır."""
    v = pd.Series([100.0] * 50 + [300.0])
    got = ind.volume_ratio(v, 50).iloc[-1]
    assert got == pytest.approx(3.0, abs=1e-12), "payda hâlâ bugünü içeriyor"

    eski = 300.0 / ((49 * 100.0 + 300.0) / 50.0)
    assert eski == pytest.approx(2.8846153846, abs=1e-9)      # eski sayının ta kendisi
    assert got - eski == pytest.approx(0.1153846154, abs=1e-9)


def test_v1b_the_old_denominator_silently_failed_breakouts_that_truly_cleared_the_gate():
    """entry.min_volume_ratio SERT bir eşik: 1.5. Gerçek oranı 1.51 olan bir kırılım bugün geçiyor,
    eski formülde 1.4948 çıkıp ELENİYORDU. Gerçek barlarda ölçülen: 45.422 kırılım barının 284'ü
    (%0,63) yalnızca bu sapma yüzünden hacim kapısında ölmüştü."""
    v = pd.Series([100.0] * 50 + [151.0])
    got = float(ind.volume_ratio(v, 50).iloc[-1])
    eski = 151.0 / ((49 * 100.0 + 151.0) / 50.0)
    assert got == pytest.approx(1.51, abs=1e-12)
    assert eski == pytest.approx(1.4948, abs=1e-4)
    assert got >= 1.5 > eski, "eşik etrafındaki sapma yeniden üretilemedi"


def test_v1c_volume_ratio_is_the_same_law_the_burst_and_ep_setups_use():
    """AYNI KAVRAM, TEK UYGULAMA. momentum_burst `vol.iloc[-21:-1].mean()`, episodic_pivot
    `vol.iloc[-51:-1].mean()` kullanıyor — ikisi de bugünü DIŞLIYOR. volume_ratio artık onlarla
    birebir aynı sayıyı vermeli, yoksa aynı yasanın iki farklı uygulaması olur."""
    df = _real("AAPL")
    vol = df["volume"]
    assert float(ind.volume_ratio(vol, 20).iloc[-1]) == pytest.approx(
        float(vol.iloc[-1] / vol.iloc[-21:-1].mean()), rel=1e-12), "momentum_burst ile ayrışıyor"
    assert float(ind.volume_ratio(vol, 50).iloc[-1]) == pytest.approx(
        float(vol.iloc[-1] / vol.iloc[-51:-1].mean()), rel=1e-12), "episodic_pivot ile ayrışıyor"


def test_v1d_volume_ratio_positive_controls():
    """POZİTİF KONTROL: sabit hacimde oran TAM 1.0; pencere dolmadan NaN (yarım pencereyle
    hesaplanmış bir '50 günlük ortalama' ölçülmüş gibi raporlanmaz)."""
    v = pd.Series([777.0] * 60)
    assert float(ind.volume_ratio(v, 50).iloc[-1]) == pytest.approx(1.0, abs=1e-12)
    assert pd.isna(ind.volume_ratio(pd.Series([100.0] * 50), 50).iloc[-1]), \
        "50 ÖNCEKİ bar yokken sayı üretiliyor"
    assert ind.volume_ratio(pd.Series([100.0] * 51), 50).notna().iloc[-1]   # tam dolunca ÜRETİYOR


# =================================================================================================
# T1 — trend_template: "52 haftalık" pencere gerçekten 52 hafta mı?
# =================================================================================================
def _tt_old(df: pd.DataFrame) -> pd.Series:
    """Kusurlu HÂLİN birebir kopyası (52w serileri min_periods=100). Kusuru kanıtlamak için gerekli:
    düzeltilmiş kodla artık çağrılamaz."""
    close = df["close"]
    s50, s150, s200 = ind.sma(close, 50), ind.sma(close, 150), ind.sma(close, 200)
    s200p = s200.shift(20)
    hi = close.rolling(252, min_periods=100).max()
    lo = close.rolling(252, min_periods=100).min()
    conds = [close > s50, s50 > s150, s150 > s200, s200 > s200p,
             close >= hi * 0.75, close >= lo * 1.30]
    score = pd.concat(conds, axis=1).astype(float).mean(axis=1)
    unknown = (s50.isna() | s150.isna() | s200.isna() | s200p.isna() | hi.isna() | lo.isna())
    return score.where(~unknown)


def test_t1_warmup_equals_the_genuinely_longest_window():
    """Isınma sabiti 220'ydi ve gerekçesi "en uzun pencere 200g ortalama + 20 barlık eğim"di.
    Şablonun 5. ve 6. koşulu 52 HAFTALIK yüksek/düşük üzerinedir: 252 bar > 220."""
    assert ind.TREND_TEMPLATE_WARMUP == 252
    tt = ind.trend_template(_linear_bars(400, 100.0, 200.0))
    assert int(np.argmax(tt.notna().to_numpy())) == ind.TREND_TEMPLATE_WARMUP - 1 == 251
    assert tt.iloc[:251].isna().all(), "ısınma dolmadan sayı üretiliyor"


def test_t1b_the_reported_52w_score_changed_when_older_bars_existed():
    """KUSURUN KANITI. AYNI son bar, AYNI 240 barlık yakın geçmiş — tek fark, seride 60 bar daha
    ESKİ (tamamen geçerli) veri olması. Eski formül bu iki durumda FARKLI puan veriyordu:

      * yalnız 240 bar → 52w dip = 100.0 (mevcut en düşük kapanış) → 125 >= 130 YANLIŞ
      * 300 bar       → 252 barlık gerçek pencere 40.0'a uzanır    → 125 >= 52 DOĞRU

    Yani 240 barla raporlanan sayı "52 haftalık şablon" DEĞİLDİ; öyle etiketlenmiş başka bir
    ölçümdü. Bir bar için doğru cevap tek olmalıdır — iki farklı cevap veriyorsa, en az biri uydurma.
    Doğru davranış: pencere dolmadan NaN."""
    eski_blok = _linear_bars(60, 40.0, 40.0, start="2019-01-01")
    yakin = _linear_bars(240, 100.0, 125.0, start="2019-04-01")
    tam = pd.concat([eski_blok, yakin], ignore_index=True)

    yalniz_yakin = _tt_old(yakin).iloc[-1]
    tam_gecmis = _tt_old(tam).iloc[-1]
    assert not pd.isna(yalniz_yakin), "fikstür kusuru tetiklemiyor (240 bar puan üretmeliydi)"
    assert tam_gecmis - yalniz_yakin == pytest.approx(1.0 / 6.0, abs=1e-12), \
        "aynı barın eski-formül puanı geçmiş eklenince 1/6 kaymalıydı"

    # DÜZELTİLMİŞ HÂL: 240 barla cevap DÜRÜSTÇE yok; 300 barla ölçüm gerçekten yapılabiliyor.
    assert pd.isna(ind.trend_template(yakin).iloc[-1]), "252 bar yokken hâlâ sayı üretiliyor"
    assert ind.trend_template(tam).iloc[-1] == pytest.approx(tam_gecmis, abs=1e-12)


def test_t1c_the_defect_was_reachable_on_real_cached_bars():
    """GERÇEK VERİ: KVUE'nin ilk barı 2023-05-04 (istenen başlangıç 2021-01-01). 220. barından
    252. barına kadarki seanslarda eski formül puan üretiyordu ve o puan "52 haftalık" diye
    raporlanıyordu — oysa sembolün 52 haftalık geçmişi henüz YOKTU. Bu, ısınma düzeltmesinin
    (2026-07-22) tam olarak kapatmak istediği sınıfın açık kalan yarısıydı."""
    df = _real("KVUE")
    if len(df) < 252 or df["date"].iloc[0] <= pd.Timestamp("2021-01-05"):
        pytest.skip("KVUE artık genç bir sembol değil — kusur bu önbellekte üretilemez")
    eski, yeni = _tt_old(df), ind.trend_template(df)
    band = eski.notna() & yeni.isna()
    assert int(band.sum()) > 0, "kusur gerçek veride üretilemedi"
    bars_at = np.flatnonzero(band.to_numpy()) + 1
    assert bars_at.min() >= 220 and bars_at.max() <= 251, \
        f"beklenen 220-251 bar bandı değil: {bars_at.min()}-{bars_at.max()}"
    # o barlarda 52w penceresi GERÇEKTEN eksikti (kanıt: mevcut bar sayısı < 252)
    assert bars_at.max() < 252


def test_t1d_trend_template_positive_controls():
    """POZİTİF KONTROL: elle türetilebilir iki uçta şablon TAM 1.0 ve TAM 0.0 vermeli.
    Yükselen doğrusal seride altı koşul da sağlanır; düşende hiçbiri sağlanmaz."""
    yukselen = ind.trend_template(_linear_bars(300, 100.0, 200.0)).iloc[-1]
    dusen = ind.trend_template(_linear_bars(300, 200.0, 100.0)).iloc[-1]
    assert yukselen == pytest.approx(1.0, abs=1e-12)
    assert dusen == pytest.approx(0.0, abs=1e-12)


# =================================================================================================
# C1 — chandelier trail: demir GİRİŞTEN BU YANAKİ zirvedir, keyfî bir pencerenin zirvesi değil
# =================================================================================================
def _chandelier_bars() -> pd.DataFrame:
    """300 bar: uzun düz seyir, GİRİŞTEN 8 BAR ÖNCE tek bir dev zirve (150), sonra 110'a yerleşme.
    Pozisyon son 2 barda tutuluyor, yani zirve pozisyonun HİÇ görmediği bir fiyat."""
    close = np.full(300, 100.0)
    close[292:] = 110.0
    high = close * 1.002
    low = close * 0.998
    high[290] = 150.0                       # girişten önceki dev zirve (giriş: 298. bar)
    return pd.DataFrame({"date": pd.bdate_range("2020-01-01", periods=300), "open": close,
                         "high": high, "low": low, "close": close,
                         "volume": np.full(300, 1_000_000.0)})


def _pos(entry=100.0, stop=96.0):
    return {"entry": entry, "stop": stop, "trail_stop": stop, "r_per_share": entry - stop}


def test_c1_chandelier_anchor_cannot_reach_before_the_entry():
    """KUSURUN KANITI. `bars["high"].iloc[-chand_lb:]` sabit 20 barlık bir pencereydi: pozisyon
    2 bar tutulmuşken 18 bar GİRİŞ ÖNCESİNE uzanıyordu. Aşağıdaki fikstürde giriş öncesi zirve
    150; doğru chandelier demiri ise son 2 barın zirvesi (110.22).

    Gerçek barlarda ölçüldü (chand_lb=20, trail 2.5·ATR, 1-5 bar tutuş, kârda olan yönetim barları):
    %22,0'ında eski pencere stop'u gerçek chandelier'den DAHA SIKI yapıyor, %3,70'inde stop'u
    GÜNCEL KAPANIŞIN ÜSTÜNE çıkarıyordu (ertesi bar kesin çıkış) — gerçek chandelier çıkarmıyordu.
    Bu, giveback için ZATEN düzeltilmiş olan hatanın (aynı fonksiyon, iki satır aşağısı) aynısıydı."""
    bars = _chandelier_bars()
    params = {"exit.trail_atr_mult": 2.5, "exit.breakeven_r": 0.0, "exit.chandelier_lookback": 20,
              "exit.giveback_pct": 0.0, "exit.time_stop_days": 15}
    held = 2
    a = float(ind.atr(bars, strat.ATR_PERIOD).iloc[-1])
    close = float(bars["close"].iloc[-1])
    hh_since = float(bars["high"].iloc[-held:].max())       # DOĞRU demir: girişten bu yana
    hh_eski = float(bars["high"].iloc[-20:].max())          # ESKİ demir: 150 (giriş öncesi zirve)
    assert hh_eski == 150.0 and hh_since == pytest.approx(110.0 * 1.002)

    dec = strat.manage_position(bars, _pos(), params, held, regime_ok=True)

    beklenen = max(_pos()["stop"], close - 2.5 * a, hh_since - 2.5 * a)
    assert dec.trail_stop == pytest.approx(beklenen, abs=1e-9), "trail girişten bu yanaki zirveden gelmiyor"
    # eski pencere AYNI barda hem daha sıkı, hem de fiyatın ÜSTÜNDE bir stop üretiyordu:
    assert hh_eski - 2.5 * a > dec.trail_stop
    assert hh_eski - 2.5 * a > close >= dec.trail_stop, \
        "eski davranış 'ertesi bar kesin çıkış' üretmiyor — fikstür kusuru göstermiyor"


def test_c1b_a_high_made_AFTER_the_entry_still_ratchets_the_trail():
    """POZİTİF KONTROL: chandelier ÖLDÜRÜLMEDİ. Zirve giriş SONRASINA konunca trail yükselmeli —
    yoksa yukarıdaki test 'trail hiç çalışmıyor' diye de geçerdi (vakumlu test)."""
    bars = _chandelier_bars()
    bars.loc[bars.index[-1], "high"] = 150.0          # zirve artık tutuş penceresinin İÇİNDE
    params = {"exit.trail_atr_mult": 2.5, "exit.breakeven_r": 0.0, "exit.chandelier_lookback": 20,
              "exit.giveback_pct": 0.0, "exit.time_stop_days": 15}
    a = float(ind.atr(bars, strat.ATR_PERIOD).iloc[-1])
    dec = strat.manage_position(bars, _pos(), params, 2, regime_ok=True)
    assert dec.trail_stop == pytest.approx(150.0 - 2.5 * a, abs=1e-9)


def test_c1c_zero_bars_held_does_not_open_the_window_to_the_whole_series():
    """`iloc[-0:]` TÜM seriyi döndürür — pencereyi bars_held ile sınırlarken klasik tuzak.
    bars_held=0 (giriş barından önceki yönetim çağrısı) en fazla SON barı görmeli."""
    bars = _chandelier_bars()
    params = {"exit.trail_atr_mult": 2.5, "exit.breakeven_r": 0.0, "exit.chandelier_lookback": 20,
              "exit.giveback_pct": 0.0, "exit.time_stop_days": 15}
    a = float(ind.atr(bars, strat.ATR_PERIOD).iloc[-1])
    dec = strat.manage_position(bars, _pos(), params, 0, regime_ok=True)
    assert dec.trail_stop == pytest.approx(
        max(96.0, float(bars["close"].iloc[-1]) - 2.5 * a,
            float(bars["high"].iloc[-1]) - 2.5 * a), abs=1e-9)
    assert dec.trail_stop < 150.0 - 2.5 * a


def test_c1d_chandelier_is_off_by_default_so_live_behaviour_is_unchanged():
    """Bugün canlıda uykuda (strategy.yaml: 0) — düzeltme mevcut işlemleri DEĞİŞTİRMEZ; kusur
    bounds.yaml'ın arama döngüsüne açtığı 0-30 aralığında uyanacaktı."""
    b = config.bounds()["exit.chandelier_lookback"]
    assert b["min"] == 0 and b["max"] == 30
    assert float(config.load_strategy()["params"]["exit.chandelier_lookback"]) == 0.0


# =================================================================================================
# R1 — regime.classify: ölçülmemiş 200 günlük ortalama, ölçülmüş gibi raporlanıyordu
# =================================================================================================
def test_r1_short_history_does_not_report_a_fabricated_sma200():
    """60 barlık bir endeksle eski kod `sma(close, 59)` hesaplayıp metriklere `"sma200"` adıyla
    yazıyordu. 59 barlık bir ortalama 200 günlük ortalama DEĞİLDİR; üstelik 50 ile 59 barlık
    ortalamaları karşılaştırmak (sma50 > sma200) trend değil gürültü ölçer."""
    spy = _real("SPY", since="2004-01-01")
    kisa = spy.iloc[:60].reset_index(drop=True)

    uydurma = float(ind.sma(kisa["close"], min(len(kisa) - 1, 150)).iloc[-1])   # eski ifadenin ta kendisi
    assert np.isfinite(uydurma), "fikstür eski uydurmayı üretmiyor"
    assert pd.isna(ind.sma(kisa["close"], 200).iloc[-1]), "60 barda gerçek sma200 var olamaz"

    reg, met = rg.classify(kisa)
    assert met.get("sma200") is None, f"hâlâ uydurma bir sma200 raporlanıyor: {met.get('sma200')}"
    assert reg == rg.CHOP and met.get("reason") == "insufficient index history"


def test_r1b_the_rising_200sma_condition_is_no_longer_granted_without_evidence():
    """GERÇEK VERİ. 220 bar yokken eski kod `sma200_prev = sma200` atıyordu; yani "200 günlük
    ortalama YÜKSELİYOR" koşulu KANIT OLMADAN geçiyordu. Gerçek SPY serisinde diğer iki TREND_UP
    koşulunu sağlayan 3.132 barın 108'inde (%3,4) 200g ortalama DÜŞÜYOR — 219 barlık bir görüşle
    bakıldığında o günler TREND_UP (maruziyet 80) etiketi alırdı; tam geçmişle almaz.
    exposure_budget_pct SERT bir tavan olduğu için bu doğrudan gün içi risk bütçesidir."""
    spy = _real("SPY", since="2004-01-01")
    c = spy["close"]
    s50, s200 = ind.sma(c, 50), ind.sma(c, 200)
    s200p = s200.shift(20)
    aday = (c > s50) & (s50 > s200) & s200p.notna() & (s200 < s200p)
    idx = np.flatnonzero(aday.to_numpy())
    idx = idx[idx >= 219]
    assert len(idx) > 0, "gerçek seride bu kesit yok — test bir şey kanıtlamıyor"

    i = int(idx[len(idx) // 2])
    dilim = spy.iloc[i - 218: i + 1].reset_index(drop=True)          # tam 219 bar: eğim ölçülemez
    assert len(dilim) == 219
    # aynı takvim günü, aynı fiyatlar: eski otomatik-geçiş üç koşulu da doğru yapardı
    assert float(c.iloc[i]) > float(s50.iloc[i]) > float(s200.iloc[i])
    assert float(s200.iloc[i]) < float(s200p.iloc[i]), "200g ortalama düşmüyor — fikstür yanlış"
    assert pd.isna(ind.sma(dilim["close"], 200).shift(20).iloc[-1]), "219 barda eğim ölçülebiliyor?"

    reg, met = rg.classify(dilim)
    assert reg != rg.TREND_UP, "kanıtsız TREND_UP hâlâ veriliyor"
    assert met.get("reason") == "insufficient index history" and met.get("bars") == 219


def test_r1c_regime_positive_controls():
    """POZİTİF KONTROL: ısınma dolduğunda sınıflandırıcı GERÇEKTEN çalışıyor (yoksa yukarıdaki
    testler 'her şey CHOP' yüzünden de geçerdi) ve <60 bar için eski gerekçe dizesi korunuyor."""
    spy = _real("SPY", since="2004-01-01")
    c = spy["close"]
    s50, s200 = ind.sma(c, 50), ind.sma(c, 200)
    s200p = s200.shift(20)
    iyi = (c > s50) & (s50 > s200) & (s200 >= s200p)
    idx = [j for j in np.flatnonzero(iyi.to_numpy()) if j >= 400]
    assert idx, "gerçek seride hiç sağlıklı yükseliş kesiti yok?"
    i = int(idx[len(idx) // 2])
    reg, met = rg.classify(spy.iloc[: i + 1].reset_index(drop=True))
    assert reg in (rg.TREND_UP, rg.HIGH_VOL)          # high_vol yalnız TREND_UP DIŞINDA bastırır
    assert reg == rg.TREND_UP or met["high_vol"] is True
    assert met["sma200"] is not None and met["sma50"] is not None

    from tests.conftest import make_bars
    r2, m2 = rg.classify(make_bars(30, seed=6))
    assert r2 == rg.CHOP and m2["reason"] == "insufficient index history"


# =================================================================================================
# POZİTİF KONTROLLER — burada kusur ARANDI ve BULUNMADI; bir daha aynı yere bakmamak için kilit
# =================================================================================================
def test_p1_atr_really_is_wilder_smoothing():
    """ATR yanlışsa HER pozisyon yanlış boyutlanır ve HER stop yanlış yere konur. Bağımsız bir
    Wilder uygulamasıyla karşılaştırıldı (ilk ATR = TR[1..14] ortalaması, sonra özyineleme):
    gerçek AAPL barlarında sapma 100. barda %0,024, 150. barda %0,0005, 252. barda 1,4e-7'dir.
    Tohum farkı (pandas ewm TR[0]'dan başlar) yalnız ISINMADA görünür ve giriş yolu zaten
    TREND_TEMPLATE_WARMUP=252 bar istiyor; yani üretimde ATR pratikte TAM Wilder. KUSUR YOK."""
    df = _real("AAPL", since="2004-01-01")
    tr = ind.true_range(df).to_numpy(dtype=float)
    p = 14
    ref = np.full(len(tr), np.nan)
    ref[p] = np.nanmean(tr[1:p + 1])
    for i in range(p + 1, len(tr)):
        ref[i] = (ref[i - 1] * (p - 1) + tr[i]) / p
    impl = ind.atr(df, p).to_numpy(dtype=float)
    for k, tol in ((150, 1e-5), (ind.TREND_TEMPLATE_WARMUP, 1e-8)):
        rel = np.abs(impl[k:] - ref[k:]) / ref[k:]
        assert np.nanmax(rel) < tol, \
            f"ATR {k}. bardan sonra Wilder'dan sapıyor: en kötü %{np.nanmax(rel) * 100:.5f}"


def test_p1b_atr_equals_the_range_on_a_hand_built_constant_range_series():
    """ELLE: her barda high-low = 2 ve boşluk yok → her barın TR'si tam 2 → ATR tam 2."""
    n = 100
    close = np.full(n, 100.0)
    df = pd.DataFrame({"date": pd.bdate_range("2021-01-01", periods=n), "open": close,
                       "high": close + 1.0, "low": close - 1.0, "close": close,
                       "volume": np.full(n, 1e6)})
    assert float(ind.atr(df, 14).iloc[-1]) == pytest.approx(2.0, abs=1e-12)
    assert float(ind.true_range(df).iloc[0]) == pytest.approx(2.0, abs=1e-12)   # ilk bar: high-low


def test_p2_no_setup_reads_a_future_bar_on_real_data():
    """İLERİ-DÖNÜK TARAMASI. Gerçek barlarda 240 karar noktasında dört kurulum da çalıştırıldı;
    karar barından SONRAKİ tüm barlar 4× fiyat / 9× hacimle bozuldu. Tek bir karar bile değişmedi.
    (Tek eksik `.shift()` bu testte patlar; backtest iyimser, canlı ölü olurdu.)"""
    params = config.default_strategy()["params"]
    kontrol, atesleme = 0, 0
    for t in ("AAPL", "MSFT", "NVDA", "JPM"):
        df = _real(t, since="2004-01-01")
        if len(df) < 900:
            continue
        for i in range(600, min(len(df) - 5, 900), 5):
            once = df.iloc[: i + 1].reset_index(drop=True)
            bozuk = df.copy()
            bozuk.loc[i + 1:, ["open", "high", "low", "close"]] *= 4.0
            bozuk.loc[i + 1:, "volume"] *= 9.0
            sonra = bozuk.iloc[: i + 1].reset_index(drop=True)
            a = strat.scan_all(once.tail(340), params, 90, t)
            b = strat.scan_all(sonra.tail(340), params, 90, t)
            kontrol += 1
            atesleme += len(a)
            assert {k: v.as_row() for k, v in a.items()} == {k: v.as_row() for k, v in b.items()}, \
                f"{t} @ {df['date'].iloc[i].date()}: karar GELECEK barlarla değişti"
    assert kontrol >= 100, "yeterli karar noktası taranmadı"
    assert atesleme > 0, "hiçbir kurulum ateşlemedi — test vakumlu olurdu (pozitif kontrol)"


def test_p3_pivot_and_base_windows_exclude_the_signal_bar():
    """Kırılım pivotu ve taban dibi BUGÜNÜ içerirse her bar kendi kendine 'kırılım' olur ve
    ölçülen taban yüksekliği (dolayısıyla R:R hedefi) bugünün barıyla kirlenir."""
    df = _real("AAPL")
    piv = ind.pivot_high(df["high"], strat.PIVOT_LOOKBACK, exclude_recent=1)
    beklenen = float(df["high"].iloc[-1 - strat.PIVOT_LOOKBACK:-1].max())
    assert float(piv.iloc[-1]) == pytest.approx(beklenen, rel=1e-12)
    df2 = df.copy()
    df2.loc[df2.index[-1], "high"] = float(df["high"].max()) * 10.0
    assert float(ind.pivot_high(df2["high"], strat.PIVOT_LOOKBACK, 1).iloc[-1]) == pytest.approx(beklenen, rel=1e-12)
