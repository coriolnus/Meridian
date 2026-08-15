"""indicators.py — kapalı OHLCV barları üzerinde saf, determinist teknik gösterge kütüphanesi.

Ne yapar: strateji katmanının tükettiği tüm gösterge serilerini üretir — oynaklık (true_range,
atr), ortalamalar (sma), hacim (volume_ratio, rvol20, med_volume21, turnover21), momentum
(trailing_return, mom_12_1, residual_momentum), yapı (pivot_high, trend_template,
weekly_uptrend) ve kesitsel yardımcılar (rs_rating, returns_tail, corr_max). Canlı ve backtest
yolları bu fonksiyonların birebir aynısını koşar; ayrışma yapısal olarak imkânsızdır.

Değişmezler: I/O yok, saat yok, ağ yok — yalnız numpy/pandas ve verilen seriler. Her pencere
NEDENSELdir (bar yalnız kendi geçmişine bakar, ileri-dönük yok) ve ısınma dolmadan NaN döner:
yarım pencereyle hesaplanmış bir "ortalama/uç değer" ölçülmüş gibi raporlanmaz; trend_template
ısınması gerçek en uzun pencereye (52 hafta = 252 bar) bağlıdır ve girdisi eksik bar için skor
tanımsızdır (NaN, 0 değil — "veri yok" ile "trend zayıf" aynı şey değildir). volume_ratio'nun
paydası bugünü DIŞLAR (sert bir eşiğin bölenidir; bugünü içermek eşiği geçen kırılımları sessizce
elerdi), rvol20'ninki bilinçli olarak İÇERİR (bant kenarları o tanımla ölçüldü) — ikisi ayrı
büyüklüktür, tanımı "düzeltmek" ölçülmemiş bir ölçek uydurmak olur. turnover21'in fiziksel bekçisi
(devir > 1 → NaN) veri-kalitesi kuralıdır, sinyal eşiği değil; sıfır varyans/sapma "ölçülemedi"
demektir, sonsuz değil. rs_rating beraberliklere aynı puanı verir (aynı kanıt zıt karar üretemez)
ve tek isimli kesitte nötr 50 döner; hizasız endeks serisi sessiz NaN yerine ValueError yükseltir.

Okur/yazar: hiçbir dosyaya dokunmaz; girdi serilerini değiştirmez, yeni seri döndürür."""
from __future__ import annotations
import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder-style ATR via EMA of true range."""
    tr = true_range(df)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).mean()


def trailing_return(close: pd.Series, lookback: int) -> pd.Series:
    """Simple return over `lookback` bars — the raw material for a relative-strength proxy."""
    return close / close.shift(lookback) - 1.0


def volume_ratio(volume: pd.Series, period: int = 50) -> pd.Series:
    """Today's volume vs its trailing average — the classic breakout confirmation.

    PAYDA BUGÜNÜ İÇERMEZ. Eskiden `volume.rolling(period)` idi:
    bugünün hacmi KENDİ ortalamasının içindeydi ve oran tam olarak 50/(49+r) çarpanıyla 1.0'a doğru
    SIKIŞIYORDU — gerçek 1.50 → ölçülen 1.485, gerçek 3.00 → ölçülen 2.885. `min_volume_ratio` SERT
    bir eşik olduğu için bu, eşiği gerçekten geçen kırılımları sessizce eliyordu: gerçek barlarda
    45.422 kırılımın 284'ü (%0,63) yalnızca bu yüzden hacim kapısında öldü.
    Üstelik AYNI kavramın iki farklı uygulaması vardı — momentum_burst `vol.iloc[-21:-1]`,
    episodic_pivot `vol.iloc[-51:-1]` kullanıyor, yani ikisi de bugünü DIŞLIYOR. Tek yasa, tek uygulama.
    min_periods de artık tam pencere: yarım pencereyle hesaplanmış bir "50 günlük ortalama" ölçülmüş
    gibi raporlanmaz (giriş yolunda zaten ısınma kapısı vardı, burada kural olarak kapatıldı)."""
    avg = volume.shift(1).rolling(period, min_periods=period).mean()
    return volume / avg


# =================================================================================================
# SKOR YENİDEN İNŞASI (2026-07-29). Üç yeni bileşen göstergesi.
# Hepsi NEDENSEL yuvarlanan pencerelerdir ve ısınma dolmadan NaN döner (uydurma yasağı).
# Bu turda SKORA ETKİLERİ SIFIRDIR (bkz. strategy.evaluate_entry, entry.w_* varsayılanları 0.0).
# =================================================================================================
RVOL_WINDOW = 20          # ölçümde (g2_olcum.py) kullanılan pencere — bant kenarları buna ait
MOM_LOOKBACK = 252        # 12 ay
MOM_SKIP = 21             # atlanan son 1 ay (kısa-vade dönüş kirliliğini dışarıda bırakır)
RESID_WINDOW = MOM_LOOKBACK - MOM_SKIP   # 231 bar = [t-252, t-21] aralığının uzunluğu
BETA_WINDOW = 252         # yuvarlanan piyasa betası penceresi


def rvol20(volume: pd.Series, period: int = RVOL_WINDOW) -> pd.Series:
    """SİNYAL GÜNÜNÜN GÖRECELİ HACMİ: volume / SMA(volume, 20). Kırpma YOK, bant AYRI (skor tarafında).

    NEDEN VAR (kanıt, 2026-07-29 g2_olcum ölçümü, n_eşleşen=2201): projenin İLK ÇİFT-KATMAN-ANLAMLI
    bileşeni. Gerçek katman @5 bar IC 0.234 (n=95, CI [0.034, 0.416]) ve @10 bar 0.219 (CI [0.017,
    0.403]) — gerçek defterde bugüne dek HİÇBİR bileşen anlamlı çıkmamıştı. cf katmanında @10 0.047
    (CI [0.004, 0.090]) ve @20 0.062 (CI [0.019, 0.104]). Aynı ölçümde bant tablosu (cf, 20 bar ort.
    ileri getiri): 0.8-1.5 → -0.52% (n=269), **1.5-2.0 → +1.84% (n=955)**, 2.0+ → +1.44% (n=857).
    Yani ilişki MONOTON DEĞİL; bu yüzden skora giren büyüklük ham rvol değil onun BANT dönüşümüdür
    (strategy.rvol_band_score) ve ham seri burada kırpılmadan/dönüştürülmeden bırakılır.

    `volume_ratio`DAN FARKI VE PAYDA TERCİHİNİN GEREKÇESİ. İki şey ayrı: (1) pencere 50 değil 20;
    (2) PAYDA BUGÜNÜ İÇERİR. İkincisi `volume_ratio`nun bilerek verdiği kararın TERSİ
    ve bu bilinçlidir: orada payda SERT bir eşiğin (min_volume_ratio) böleniydi ve bugünü içermek
    eşiği gerçekten geçen kırılımları eliyordu. Buradaki büyüklük ise bir eşiğin böleni değil, bant
    kenarları ÖLÇÜLMÜŞ bir ölçektir — ve o ölçüm tam olarak bu tanımla (bugün dahil) yapıldı. Aynı
    bar için bugünü dışlayan tanım ~%5 daha büyük bir sayı üretir (dahil 1.75 ≈ hariç 1.83), yani
    tanımı "düzeltmek" 1.5/2.0/1.75±0.75 kenarlarını HİÇ ÖLÇÜLMEMİŞ bir ölçeğe kaydırırdı. Ölçülen
    tanım neyse kod odur; ölçek tercihini yeniden açmak bir SONRAKİ ölçüm turunun işidir.
    İleri-dönük DEĞİLDİR: SMA20 penceresi [t-19, t] bar kapanışında tamamen bilinir."""
    return volume / volume.rolling(period, min_periods=period).mean()


def mom_12_1(close: pd.Series) -> pd.Series:
    """KLASİK 12-1 MOMENTUM: close[t-21]/close[t-252]-1 — son ayı ATLAYAN 11 aylık getiri.

    KANIT (g2_olcum, 2026-07-29): cf katmanı @20 bar IC +0.055 (n=2093, CI [0.012, 0.098]) ANLAMLI;
    @5 ve @10 anlamsız. Gerçek katmanda @20 IC 0.174 ama n=93 → aralık sıfırı kapsıyor. Yani kanıt
    UZUN ufuktadır ve tek katmandan gelir; rvol'den zayıftır ve ağırlığı da öyle olmalıdır.
    Son ayın ATLANMASI klasik tanımın parçasıdır (kısa-vade dönüş etkisini karıştırmamak için) —
    aynı ölçümde ATLANMAYAN kısa-vade momentum (stm21) devir-koşullu kesitte ANLAMLI NEGATİF çıktı
    (-0.056 @20, üst-yarı devir, n=1266), yani burada momentum ve dönüş gerçekten karışıyor."""
    return close.shift(MOM_SKIP) / close.shift(MOM_LOOKBACK) - 1.0


def residual_momentum(close: pd.Series, index_close: pd.Series | None) -> pd.Series:
    """ARTIK (residual) 12-1 MOMENTUM, artık oynaklığıyla ÖLÇEKLİ (Blitz-Huij-Martens ailesi).

    FORMÜL (g2_olcum.py'deki ölçülen tanımla BİREBİR — ikinci bir tanım yazılmaz):
        r      = close.pct_change()                       # sembolün günlük getirisi
        s      = index_close.pct_change()                 # endeksin (SPY) günlük getirisi
        beta   = rolling_cov(r, s, 252) / rolling_var(s, 252)
        resid  = r - beta * s                             # piyasadan ARINDIRILMIŞ günlük getiri
        rmom   = sum(resid, 231).shift(21) / std(resid, 231).shift(21)
    Yani pay [t-252, t-21] aralığındaki artıkların toplamı, bölen aynı aralığın artık standart
    sapmasıdır: ham 12-1 getiri yerine "piyasa hareketiyle açıklanamayan ve KENDİ gürültüsüne göre
    ne kadar büyük" ölçüsü. Isınma iki katmanlıdır: beta 252 bar ister, artık toplamı üstüne 231
    bar daha → ilk ~483 barda NaN. Bu, canlı yolun 340 barlık kuyruğundan UZUNDUR; dolayısıyla
    canlı tarama bu bileşeni bugün ÖLÇEMEZ ve alan None kalır (bkz. strategy.evaluate_entry).
    Bileşenin ölçüldüğü yer tam seriyi okuyan `component_ic`dir.

    STATÜ: YEDEK ADAY. g2_olcum'da zayıf pozitif ama HİÇBİR ufukta anlamlı değil (cf @20 IC 0.036,
    CI [-0.007, 0.079]). Bu yüzden skor formülüne GİRMEZ ve ona ait bir ağırlık düğmesi de yoktur;
    yalnız defterde alan ve `component_ic` tablosunda satır olarak ölçülür ki bir sonraki turda
    kanıt birikince kararı ölçüm versin. Endeks serisi yoksa TAMAMEN NaN döner — uydurma yok.

    HİZALAMA ETİKET ÜZERİNDENDİR ve hizasızlık SESSİZ KALMAZ. İki seri farklı indekslenmişse
    (klasik tuzak: biri tarih-indeksli endeks serisi, diğeri konum-indeksli bar kuyruğu) pandas
    reindex'i uyarısız BOŞ seri üretir ve sonuç "artık momentum ölçülemedi" diye raporlanırdı —
    oysa gerçek sebep bir HİZALAMA HATASIdır ve ikisi aynı şey değildir. Hiç ortak etiket yoksa
    ValueError yükselir; kısmî örtüşme ise gerçekten eksik veridir ve NaN olarak kalır.
    Endeksin getirisi KENDİ takviminde hesaplanır, sonra hizalanır (g2_olcum.py ile birebir)."""
    if index_close is None or len(index_close) == 0:
        return pd.Series(np.nan, index=close.index, dtype=float)
    r = close.pct_change()
    s = index_close.pct_change()
    if not s.index.equals(close.index):
        if len(s.index.intersection(close.index)) == 0:
            raise ValueError(
                "residual_momentum: index_close ile close HİÇ ortak etiket taşımıyor "
                f"(endeks {type(index_close.index).__name__}, seri {type(close.index).__name__}). "
                "Sessizce NaN dönmek, hizalama hatasını 'ölçülemedi' kılığında raporlardı.")
        s = s.reindex(close.index)
    var = s.rolling(BETA_WINDOW).var()
    # SIFIR VARYANS = BETA ÖLÇÜLEMEDİ, sonsuz beta DEĞİL. Pratikte 252 barlık endeks varyansı sıfır
    # olmaz; ama bölme sonsuz üretirse o sonsuz artıklara, oradan da toplama sızar ve "ölçüldü"
    # kılığında bir sayı olarak raporlanırdı. Aynı gerekçe artık-std için de geçerli.
    beta = r.rolling(BETA_WINDOW).cov(s) / var.where(var > 0)
    resid = r - beta * s
    num = resid.rolling(RESID_WINDOW).sum().shift(MOM_SKIP)
    den = resid.rolling(RESID_WINDOW).std().shift(MOM_SKIP)
    return num / den.where(den > 0)


# =================================================================================================
# EDG-2026-016 — TURNOVER (devir hızı). Kartın hükmü SUCCESS: üst-%20 dilim
# evren-fazlası @10 +0,31% CI[+0,15,+0,49] · @20 +0,65% CI[+0,34,+1,01]; rvol20+mom21 kontrolünden
# sonra ARTIK üç yöntemle birden sağ (kova-tabanı +0,56%, kova-içi +0,77%, artık-IC @20 0,0284);
# q5 TEKDÜZE MONOTON; maliyet-sonrası net +0,55% (20bps duyarlılıkta +0,45%).
# =================================================================================================
TURNOVER_WINDOW = 21          # ölçümdeki pencere (ortak.bar_paneli: rolling(21, min_periods=21))
TURNOVER_FIZIKSEL_TAVAN = 1.0  # medyan-21g hacim dolaşımdaki hissenin TAMAMINI aşamaz


def med_volume21(volume: pd.Series, period: int = TURNOVER_WINDOW) -> pd.Series:
    """21 barlık MEDYAN hacim. Pencere dolmadan NaN (yarım pencereyle "medyan" raporlanmaz).

    NEDEN MEDYAN VE NEDEN ORTALAMA DEĞİL: bu büyüklük devir hızının PAYIDIR ve tek bir kazanç-günü
    ya da endeks-yeniden-dengeleme hacmi ortalamayı katlarken medyanı kıpırdatmaz. Ölçüm bu tanımla
    yapıldı (üç devir kartında da aynı satır); ortalamaya çevirmek, kartın ölçtüğü büyüklükten
    BAŞKA bir seriyi aynı adla skora sokmak olurdu."""
    return volume.rolling(period, min_periods=period).median()


def turnover21(volume: pd.Series, shares) -> pd.Series:
    """DEVİR HIZI: medyan21(hacim) / as_of_shares(t) — ölçüm kartının ölçtüğü seri, BİREBİR.

    `shares` bir SAYI (o barın as-of hisse sayımı) ya da `volume` ile HİZALI bir seri olabilir;
    None/NaN olduğu yerde sonuç NaN'dır — "ölçülemedi", sıfır değil (UYDURMA YASAĞI).

    İKİ TARAF DA GÜNCEL BAZDA — YAZILI OLSUN. Bar hacmi (FMP/Cboe) split-DÜZELTİLMİŞTİR, yani
    bugünün hisse birimindedir; EDGAR'ın bildirdiği sayım ise DOSYALAMA GÜNÜNÜN birimindedir ve
    `adapters.edgar_shares` onu güncel baza çevirerek verir. İki uç aynı bazda olduğu için oran
    bölünmeden BAĞIMSIZDIR; birini çevirmeyi unutmak AAPL 2019'da 4×, GOOGL 2021'de 20× hatalı bir
    devir üretirdi.

    FİZİKSEL BEKÇİ (VERİ KALİTESİ — SİNYAL EŞİĞİ DEĞİL, BEYANLI). Devir > 1 ise hücre NaN'dır: bir
    şirketin günlük MEDYAN işlem hacmi dolaşımdaki hissesinin tamamını geçemez. Bu bir eşik ayarı
    değil FİZİKSEL İMKÂNSIZLIKTIR ve kaynağı ölçülmüş vakalardır — kapak sayfasında "3 hisse" yazan
    CSX 2011-04, "100" yazan ETN 2012-11/BKR 2017-08, "8.000" yazan SPG 2013-02, "25.000" yazan
    LIN 2017-10 kayıtları devri 10⁴ katına çıkarıyordu. Kartın hiçbir eşiğine dokunmaz; yalnız
    uydurma bir değerin skora girmesini engeller.
    ÖLÇÜMDEN FARKI (beyan): ölçüm bekçiyi KAYIT düzeyinde işletir — bir as-of kaydının geçerlilik
    penceresindeki medyan devir 1'i aşarsa o kaydın TAMAMI geçersizdir. Burada bekçi NOKTASALdır:
    yalnız devri 1'i aşan barlar düşer. Aynı imkânsızlığı aynı yönde eler, penceredeki temiz günleri
    ayakta bırakır; yani canlı yol ölçümden daha AZ eler, daha çok değil."""
    if shares is None:
        return pd.Series(float("nan"), index=volume.index)
    med = med_volume21(volume)
    if isinstance(shares, pd.Series):
        sh = shares.astype(float).reindex(volume.index)
    else:
        try:
            sh = pd.Series(float(shares), index=volume.index)
        except (TypeError, ValueError):   # sessiz-yutma: sayıya çevrilemeyen hisse sayımı "ölçülemedi"dir; dönen NaN serisi bunu hücre hücre GÖSTERİR — yutulan istisna değil, dürüst-None çevirisidir (çağıran None'u 0 gibi kullanamaz; MARKER biçimi YASA-4 dedektörü için, "DEĞİL" eki işareti bozuyordu)
            return pd.Series(float("nan"), index=volume.index)
    to = med / sh.where(sh > 0)
    return to.where(to <= TURNOVER_FIZIKSEL_TAVAN)


def pivot_high(high: pd.Series, lookback: int = 40, exclude_recent: int = 1) -> pd.Series:
    """Highest high over the consolidation window, excluding the most recent bar(s).
    Used as the breakout pivot: an entry triggers when close clears this level."""
    shifted = high.shift(exclude_recent)
    return shifted.rolling(lookback, min_periods=lookback // 2).max()


# ISINMA (canlı `warmup_coverage_short` bulgusu): trend şablonu EN UZUN penceresi kadar
# bar ister; bu kadar bar yoksa şablon HESAPLANAMAZ.
# DÜZELTME: sabit 220 idi ve "en uzun pencere 200g ortalama +
# 20 barlık eğim" diye gerekçelendirilmişti. YANLIŞ: şablonun 5. ve 6. koşulu 52 HAFTALIK yüksek/düşük
# üzerinden kurulur — o pencere 252 bardır, 220'den UZUNDUR. 52w serilerinin min_periods'ı 100 olduğu
# için 220-251 bar arası şablon SAYI ÜRETİYOR ve o sayı "52 haftalık" diye raporlanıyordu, oysa 220-251
# barlık bir pencerede ölçülmüştü. Gerçek kanıt: KVUE (ilk bar 2023-05-04) 2024-03-19 → 2024-05-02
# arasındaki 32 seansta tam olarak bu şekilde puanlandı. Isınma artık GERÇEK en uzun penceredir.
TREND_TEMPLATE_WARMUP = 252


def trend_template(df: pd.DataFrame) -> pd.Series:
    """Minervini-style trend template score in [0,1]: fraction of conditions met.
    Close>50sma>150sma>200sma, 200sma rising, close within 25% of 52w high, >30% above 52w low.

    ISINMASI DOLMAYAN BAR = NaN, 0 DEĞİL (sessiz doğruluk hatası).
    Eski hâl `pd.concat(conds).astype(float).mean()` idi. Pandas'ta NaN ile karşılaştırma False üretir:
    200 günlük ortalaması HENÜZ YOKKEN `sma150 > sma200` "koşul sağlanmadı" sayılıyordu. Yani genç bir
    sembol (canlı kanıt: KVUE ilk barı 2023-05-04, istenen 2021-01-01) "veri yok" değil "trend zayıf"
    diye puanlanıyordu — uydurulmuş bir sayı, gerçek ölçüm kılığında. Sonuç iki yerde yanlıştı:
      (1) tt bir SERT kapıdır (pullback/momentum_burst `tt >= 0.6`) — sembol yanlış gerekçeyle elenir;
      (2) tt bileşik SKORA ağırlıkla girer (entry.w_tight) — ısınma boyunca skor sistematik olarak
          bastırılır ve OOS kapısı bu bozuk kesitle strateji kabul/ret kararı verir.
    Artık ısınma dolmadan NaN döner; dört kurulumun DA zaten var olan `pd.isna(tt) → None` koruması
    sembolü DÜRÜSTÇE dışlar. Ölçülemeyen şey ölçülmüş gibi raporlanmaz."""
    close = df["close"]
    sma50 = sma(close, 50)
    sma150 = sma(close, 150)
    sma200 = sma(close, 200)
    sma200_prev = sma200.shift(20)
    # 52 HAFTA = 252 BAR, EKSİĞİ DEĞİL. min_periods=100 iken 100-251 bar arasında
    # "52 haftalık yüksek/düşük" adı altında DAHA KISA bir pencerenin uç değeri dönüyordu. Kısa
    # pencere maksimumu ≤ gerçek maksimum → "52w zirvenin %25 yakınında" koşulu KOLAYLAŞIYOR;
    # kısa pencere minimumu ≥ gerçek minimum → "52w dipten %30 yukarıda" koşulu ZORLAŞIYOR. İki
    # koşul da ölçülmemiş bir şeyi ölçülmüş gibi raporluyordu. Artık pencere dolmadan NaN döner ve
    # aşağıdaki `unknown` maskesi barı DÜRÜSTÇE bilinmez yapar (maske serilerden türediği için
    # TREND_TEMPLATE_WARMUP ile otomatik tutarlı kalır).
    hi_52w = close.rolling(252, min_periods=252).max()
    lo_52w = close.rolling(252, min_periods=252).min()

    conds = [
        close > sma50,
        sma50 > sma150,
        sma150 > sma200,
        sma200 > sma200_prev,
        close >= hi_52w * 0.75,
        close >= lo_52w * 1.30,
    ]
    stacked = pd.concat(conds, axis=1).astype(float)
    score = stacked.mean(axis=1)
    # BİLİNMİYOR maskesi: girdilerinden HERHANGİ biri NaN olan bar için skor tanımsızdır. Maske
    # doğrudan serilerden türetilir (sabit bir bar sayısından değil) ki eksik/boşluklu seride de
    # doğru kalsın; ileri-dönük değildir — her bar yalnız KENDİ geçmişine bakar.
    unknown = (sma50.isna() | sma150.isna() | sma200.isna() | sma200_prev.isna()
               | hi_52w.isna() | lo_52w.isna())
    return score.where(~unknown)


def weekly_uptrend(df: pd.DataFrame, sma_weeks: int = 10) -> bool:
    """Higher-timeframe confirmation: is the weekly close above its N-week average? Resampled from the
    daily closed bars (no look-ahead — the current partial week's close is just the latest daily close).
    Returns True when there isn't enough weekly history, so it never blocks on thin data."""
    if "date" not in df.columns or len(df) < sma_weeks * 5 + 5:
        return True
    w = df.set_index("date")["close"].resample("W").last().dropna()
    if len(w) < sma_weeks + 1:
        return True
    sma = w.rolling(sma_weeks).mean().iloc[-1]
    return True if pd.isna(sma) else bool(w.iloc[-1] >= sma)


def rs_rating(returns_by_ticker: dict[str, float]) -> dict[str, int]:
    """Cross-sectional relative-strength rating in [1,99] from a map ticker->trailing_return.
    Percentile rank; the IBD-style RS proxy the strategy's rs_rating_min gate compares against."""
    if not returns_by_ticker:
        return {}
    items = [(t, r) for t, r in returns_by_ticker.items() if r is not None and not np.isnan(r)]
    if not items:
        return {t: 50 for t in returns_by_ticker}
    tickers = [t for t, _ in items]
    if len(items) == 1:
        # a cross-section of ONE measurable ticker has no peers to rank against — the old formula gave
        # it RS=1 (worst), hard-vetoing the only candidate below no-data names' default 50
        return {tickers[0]: 50}
    vals = np.array([r for _, r in items], dtype=float)
    # BERABERLİK = AYNI PUAN. Eski hâl argsort ile beraberlere KEYFÎ
    # ayrı sıralar veriyordu: getirisi birebir aynı iki isimden biri RS 50, diğeri RS 99 alabiliyordu
    # — ve rs_rating_min sert bir eşik olduğu için AYNI kanıt zıt kararlar üretiyordu (biri silahlanır,
    # diğeri elenir). Üstelik argsort kararlılığı garanti değil: evrenin sırası değişince sonuç kayar.
    # Ortalama-sıra (standart yüzdelik konvansiyonu) hem adil hem sıradan bağımsız.
    ranks = pd.Series(vals).rank(method="average").to_numpy() - 1.0
    pct = (ranks / max(1, len(vals) - 1)) * 98.0 + 1.0  # map to [1,99]
    out = {t: int(round(p)) for t, p in zip(tickers, pct)}
    for t in returns_by_ticker:
        out.setdefault(t, 50)
    return out


def returns_tail(close, lookback: int = 60):
    """Recent daily returns (numpy) for a close series — precompute once per held name per day."""
    v = close.tail(lookback + 1).astype(float)
    return v.pct_change().dropna().values


def corr_max(cand_close, others_rets, lookback: int = 60, min_pts: int = 20) -> float:
    """Max pairwise return-correlation between a candidate name and the names already held. This is REAL
    concentration — two tech names can sit in different sectors yet move as one; sector-count misses it.
    `others_rets` is the PRECOMPUTED list of held-name return arrays (returns_tail), so we only compute
    the candidate's returns here — at most (open positions ≤ 5) corrcoefs per candidate. 0.0 if none."""
    import numpy as np
    if not others_rets:
        return 0.0
    cr = returns_tail(cand_close, lookback)
    if len(cr) < min_pts:
        return 0.0
    best = 0.0
    for orr in others_rets:
        m = min(len(cr), len(orr))
        if m < min_pts:
            continue
        with np.errstate(invalid="ignore", divide="ignore"):
            c = np.corrcoef(cr[-m:], orr[-m:])[0, 1]
        if np.isfinite(c):
            best = max(best, float(c))
    return round(best, 3)
