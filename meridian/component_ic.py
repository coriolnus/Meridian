"""component_ic.py — bileşen IC tablosu: bileşik skorun ham parçalarından hangisi tahmin gücü taşıyor?

Ne yapar: Bileşik 0-100 skor ağırlıklı bir toplamdır ve toplam, içindeki bir sinyali diğerlerinin
gürültüsüyle söndürebilir — "skorun IC'si sıfır" ile "skorun hiçbir parçası bilgi taşımıyor" AYNI
cümle değildir ve ikisi ayrılmadan ağırlıkların (entry.w_*) hangi yöne çevrileceği bilinemez. Bu
modül sekiz bileşeni (COMPONENTS: rs, tight, vol, prox, rvol20, mom12_1, rmom, turnover21 — eski
çekirdek silinmedi, kıyas sürsün diye yenilerle yan yana ölçülür) üç ufukta (HORIZONS: 5/10/20 bar)
ve katman etiketiyle (gercek / cf / havuz) ayrı ayrı ölçer; her hücre Fisher-z güven aralığı ve
`anlamli` alanı taşır, `eb` alanı ham IC'ye DOKUNMAYAN paralel empirik-Bayes küçültme sütunudur.
SIFIR YETKİ: hiçbir kapıya, karara, silahlanmaya girmez — yalnız rapor yazar; bir bileşenin IC'si
yüksek çıksa bile ağırlığı ancak olasılıksal kapıdan geçen bir hipotezle değişebilir.

Kilit girişler: `component_ic(write=True)` tabloyu kurar ve state/component_ic.json'a yazar
(write=False kuru koşu: artefakta dokunmaz, telemetriye sessizlik vaat etmez); `forward_returns(df)`
ileri getirinin TEK tanımı (close[t+h]/close[t]-1 — eşik eğrisi de aynı tanımı tüketir);
`compact_lines()` beyin için kompakt özet; `eslesme_nedeni(ticker, tarih)` çerçeve dışı tarihin
eleme sınıfı (bütünlük defterinin beyanlı piyasa dışlaması ≠ şema hatası).

Ölçüm kararları (değişmezler): bileşenler defterden değil BARLARDAN, canlı skorun kullandığı AYNI
indicators fonksiyonlarıyla yeniden hesaplanır (tek yasa, tek uygulama; göstergeler nedensel —
tam seride hesap, canlı kuyruk hesabıyla aynı barda birebir aynıdır). İleri getiri SABİT ufukta ve
YÜZDE olarak ölçülür, R DEĞİL: değişken çıkış ufku sinyal gücünü çıkış kuralının davranışıyla
karıştırır ve satır-başına-farklı bir bölen monoton dönüşüm olmadığından Spearman'ı da bozar.
Havuz katmanı (ticker, tarih) anahtarında tekilleştirilir, gerçek katman önceliklidir — aynı
gözlemi iki kez saymak paydayı şişirmektir. cf katmanı bu tabloda sadakat sorusundan BAĞIMSIZDIR;
bu, "cf sayıları hüküm taşıyamaz" kuralının GEREKÇELİ ve DAR bir istisnasıdır (yazılmazsa sessizce
genelleşir): cf defterinin bilinen sadakat kusuru ÇIKIŞ simülasyonundadır ve r_multiple'ı kirletir,
oysa bu tablonun y ekseni barlardan gelir — cf satırından alınan tek şey GİRİŞ ANIdır (ticker +
tarih) ve bir çıkış kuralının simüle edilip edilmemesi, giriş barından h bar sonraki fiyatı
DEĞİŞTİRMEZ. Yine de cf satırları ALINMAMIŞ hipotetik girişlerdir: tabloda ayrı satırda, "sim"
etiketiyle durur — kanıt değil bağlamdır; hüküm cümlesi yalnız gerçek katmandan kurulur.
Ölçülemeyen hücre None kalır (sıfır değil). Okur: trades.jsonl, cf defteri, bar önbelleği, EDGAR
pay sayımı; yazar: state/component_ic.json + gecelik olay satırı."""
from __future__ import annotations

import json
import math

import pandas as pd

from . import config, store, obs, sieve, indicators as ind
from . import strategy as strat
from .analytics import spearman_ic, IC_MIN_SAMPLE

COMPONENT_IC_FILE = "component_ic.json"

# UFUKLAR: 5 = bir işlem haftası, 20 = bir işlem ayı, 10 = ikisinin arası. `exit.time_stop_days`
# canlıda 15 — yani 20 barlık ufuk, stratejinin kendi tutma süresini KAPSAYAN ilk ufuktur; 5 ise
# kârın büyük kısmının geldiği time_stop çıkışlarının altındaki kısa vadeyi görür.
HORIZONS = (5, 10, 20)

# Dört ham bileşen — `strategy.evaluate_entry`de `entry.w_*` ağırlıklarının ÇARPTIĞI değerler.
# İsimler ağırlık adlarını takip eder (w_rs → rs) ki pano tablosunda hangi ağırlığın hangi ölçüme
# karşılık geldiği tahmin edilmek zorunda kalmasın.
#
# ÜÇ YENİ BİLEŞEN: rvol20 / mom12_1 / rmom. Eski dördü
# KALDIRILMADI — kıyas sürsün diye yan yana ölçülürler; yeni bir çekirdeğin eskisinden iyi olduğu
# ancak ikisi AYNI tabloda, aynı popülasyonda, aynı CI disiplininde durursa söylenebilir.
#
# BU HÜCRELER HAM DEĞERİ ÖLÇER, SKORA GİREN DÖNÜŞÜMÜ DEĞİL — VE BU FARK YAZILI OLMALI. Eski dört
# bileşen skor uzayındadır (tight = tt·100, vol = kırpılmış oran, prox = kırpılmış puan). Yenilerde
# ise ağırlığın çarptığı büyüklük bir DÖNÜŞÜMDÜR: entry.w_rvolband ham rvol'ü değil onun ÜÇGEN bant
# puanını (strategy.rvol_band_score), entry.w_mom ise ham 12-1 getiriyi değil onun 63-barlık
# yüzdelik rütbesini çarpar. Buradaki satırlar HAM seriyi ölçer; sebebi, kanıt tabanının
# (g2_olcum) tam olarak ham seriyi ölçmüş olması ve gece tablosunun o kanıtla DOĞRUDAN kıyaslanabilir
# kalması. Sonuç: bu satırlar "bant puanının IC'si" DEĞİLDİR — üçgen dönüşüm monoton olmadığı için
# Spearman IC'si de aynı sayı olmak zorunda değildir. Bandın kanıtı ayrı bir tablodur (bant ortalama
# getirileri, g2_olcum çıktısı) ve bileşiğin uçtan uca ölçümü kalem E'nin aday profillerine aittir.
#
# (7) SEKİZİNCİ SATIR: turnover21. Kartın hükmü SUCCESS ve entegrasyon
#     kararı "elle ağırlık yok — kablola, düğmeyi bounds'a 0 ile indir, ölçüsünü öğrenme döngüsü
#     versin". Bu tablo o döngünün GÖZÜDÜR: düğme 0'da dururken bile hücreler her gece dolar, yani
#     "önce aç sonra ölç" kısır döngüsüne girilmez. Satırın ölçtüğü büyüklük HAM orandır
#     (medyan21(hacim)/as_of_shares); skora giren büyüklük onun yüzdelik PUANIdır
#     (`strategy.turnover_score`) — dönüşüm monotondur, yani Spearman IC'si aynı sayıdır, ama ölçek
#     beyanı yine de yazılıdır (`yeni_bilesen_notu`). Payda EDGAR'dan gelir ve ölçülemeyen hücre
#     None kalır; kaynağın sayacı çıktının `turnover_kaynak` alanındadır.
COMPONENTS = ("rs", "tight", "vol", "prox", "rvol20", "mom12_1", "rmom", "turnover21")
COMPONENT_WEIGHT_KEY = {"rs": "entry.w_rs", "tight": "entry.w_tight",
                        "vol": "entry.w_vol", "prox": "entry.w_prox",
                        "rvol20": "entry.w_rvolband", "mom12_1": "entry.w_mom",
                        # rmom'un ağırlık DÜĞMESİ YOK: g2_olcum'da hiçbir ufukta anlamlı değil
                        # (cf @20 IC 0.036, CI [-0.007, 0.079]) → yedek aday. Ölçülür, skora girmez.
                        "rmom": None, "turnover21": "entry.w_turnover"}
COMPONENT_WEIGHT_DEFAULT = {"rs": 0.35, "tight": 0.30, "vol": 0.20, "prox": 0.15,
                            "rvol20": 0.0, "mom12_1": 0.0, "rmom": None, "turnover21": 0.0}
LAYERS = ("gercek", "cf", "havuz")


CI_Z = 1.96          # %95 iki yanlı normal kuantil


def _fisher_ci(ic: float, n: int) -> tuple[float | None, float | None]:
    """Spearman IC'si için Fisher-z GÜVEN ARALIĞI. Neden gerekli ve neden BU yaklaşım:

    Bir hücrede "IC 0.15" yazması tek başına bir bulgu DEĞİLDİR — n=40'ta 0.15, sıfırdan ayırt
    edilemez; n=2000'de aynı sayı sağlam bir sinyaldir. Aralık olmadan tablo, örneklem büyüklüğünü
    okurun kafasında taşımasını bekler ve 07-28'in ilk okumasında ("vol tek tutarlı pozitif")
    tam da bu risk vardı.

    YÖNTEM: z = artanh(ic) dönüşümü korelasyonu yaklaşık normal ve VARYANSI ÖRNEKLEMDEN BAĞIMSIZ
    bir ölçeğe taşır; Spearman için standart hata ≈ 1/sqrt(n-3) (Fisher yaklaşımı — Pearson için
    tam, Spearman için yaygın kabul gören yaklaşıklık; katsayı düzeltmeleri (ör. 1.06) literatürde
    tartışmalı olduğu için EKLENMEDİ, yani aralık bir miktar DAR olabilir ve bu yönde muhafazakâr
    değildir: aralığın sıfırı kapsaması "kesin anlamsız" değil "anlamlılık gösterilemedi"dir).
    Aralık z ölçeğinde kurulup tanh ile geri alınır — bu yüzden [-1,1] dışına ASLA taşmaz.

    SINIR (yazılı olmalı, çünkü sayı bu sınırdan büyük görünüyor): formül gözlemlerin BAĞIMSIZ
    olduğunu varsayar. cf katmanında gözlemler güne ve sembole KÜMELENMİŞTİR (tek günde onlarca
    satır), yani etkin örneklem ham n'den küçüktür ve GERÇEK aralık buradakinden GENİŞTİR. Bu
    tabloda cf aralıkları bu nedenle bir ALT SINIR olarak okunmalıdır; `score_calibration` aynı
    gerekçeyle cf diliminde anlamlılığı hiç hesaplamıyordu (orada None bırakılmıştı). Burada
    hesaplanıyor ama etiketiyle: `ci_varsayim` alanı çıktının içinde bu cümleyi taşır."""
    if n is None or n <= 3:
        return None, None
    try:
        z = math.atanh(max(-0.999999, min(0.999999, float(ic))))
    except ValueError:  # sessiz-yutma: atanh yalnız |ic|>=1 ya da sayı-olmayan girdide patlar; ikisi de "aralık ÖLÇÜLEMEDİ" demektir ve None çifti hücrede zaten görünür (ci: None, anlamli: None) — ikinci bir uyarı aynı olguyu tekrar söylerdi
        return None, None
    se = 1.0 / math.sqrt(n - 3)
    return round(math.tanh(z - CI_Z * se), 4), round(math.tanh(z + CI_Z * se), 4)


# ==================================================================================================
# EMPİRİK BAYES SÜTUNU
# ==================================================================================================
# NE. Her hücrenin HAM `ic`'sinin YANINA, o katmanın ortak ortalamasına James-Stein tarzı
# küçültülmüş bir ikizi (`eb_ic`) + küçültme katsayısı (`shrink_katsayisi`) yazılır.
#
# NEDEN. Bu tablonun hücreleri n=31 ile n=2100 arasında değişiyor ve panoda AYNI yazı tipiyle yan
# yana duruyorlar. Küçük hücrenin ekstrem IC'si büyük ölçüde gürültüdür; "en güçlü bileşen" seçimi
# tam o gürültüyü seçer (kazananın-laneti). Küçültme, her hücreyi kendi belirsizliği ölçüsünde
# ortak ortalamaya çeker.
#
# HAM `ic` DEĞİŞMEZ — GERİYE UYUM ÇİVİLİ. `eb` bir PARALEL SÜTUNdur: `tablo` sözlüğüne tek bayt
# dokunmaz, ayrı bir üst-seviye alanda durur. Bugünün okuyucuları (`compact_lines` → beyin,
# `analytics.shrunk_component_ic` → pano, `yeniden_uret` farkı) HAM ic okumaya devam eder. `eb`
# bugün YALNIZ GÖRÜNÜRDÜR; bir hükme bağlanması ayrı bir karardır.
#
# NEDEN KATMAN BAŞINA VE NEDEN TEK HAVUZDA DEĞİL: `gercek` ile `cf` FARKLI POPÜLASYONLARDIR (biri
# alınmış işlemler, öteki alınmamış hipotetik girişler) — modül başlığının 4. kararı bunu zaten
# yazıyor. İkisini tek ortalamaya çekmek, iki farklı gerçeği tek sayıya eritirdi.
#
# BEYAN EDİLEN SINIR: aynı bileşenin 5/10/20 barlık hücreleri AYNI gözlemlerden türer, yani
# bağımsız değildirler. Momentler yöntemi τ²'yi hücreler-arası varyanstan tahmin ederken bağımsızlık
# varsayar → τ² bir miktar KÜÇÜK, küçültme bir miktar GÜÇLÜ olabilir. Bu, sayıyı yanlış yapmaz ama
# "ne kadar" sorusunu belirsizleştirir; `beyan` alanı bunu çıktının içinde taşır.
def _eb_blok(tablo: dict) -> dict:
    """Katman başına empirik-Bayes küçültme sütunu. HAM `ic` alanlarına DOKUNMAZ.

    Hesap `analytics._empirical_bayes` ile yapılır ve hücreler `analytics._ic_hucreleri` ile
    kurulur — TEK UYGULAMA, İKİ TÜKETİCİ (pano okuyucusu aynı fonksiyonları çağırır). İkinci bir
    küçültme yazmak, aynı adı taşıyan iki farklı sayı üretirdi."""
    from .analytics import _empirical_bayes, _ic_hucreleri
    katmanlar = {}
    for lay in LAYERS:
        ham = _empirical_bayes(_ic_hucreleri((tablo or {}).get(lay) or {}))
        katmanlar[lay] = {
            "n_hucre": ham.get("n_hucre"), "kucultuldu": ham.get("kucultuldu"),
            "genel_ortalama": ham.get("genel_ortalama"), "tau2": ham.get("tau2"),
            "sigma2_vekil": ham.get("sigma2_vekil"), "neden": ham.get("neden"),
            "hucreler": {ad: {"ham_ic": h["ham"], "eb_ic": h["kucultulmus"],
                              "shrink_katsayisi": h["agirlik"], "cekim": h["cekim"], "n": h["n"]}
                         for ad, h in (ham.get("hucreler") or {}).items()},
        }
    return {
        "katmanlar": katmanlar,
        "hucre_anahtari": "bileşen@ufuk",
        "yontem": ("empirik Bayes / James-Stein (momentler yöntemi): eb_ic = w·ic + (1−w)·ortak; "
                   "w = τ²/(τ²+σ²ᵢ); τ² = hücreler-arası varyans − ortalama hücre-içi varyans, "
                   "0'a kıstırılmış; ortak ortalama n-ağırlıklıdır"),
        "shrink_katsayisi_tanimi": ("w = hücrenin KENDİ tahminine verilen ağırlık. w=1 → hiç "
                                    "küçültme (ham=eb), w=0 → TAM küçültme (eb=ortak ortalama). "
                                    "`cekim` = ham_ic − eb_ic, yani küçültmenin BÜYÜKLÜĞÜ"),
        "sigma_yasasi": ("σᵢ = 1/√(n−1) — küçültme HAM IC (r) ölçeğinde yapılır. Hücrenin `ci` "
                         "alanı ise Fisher-z ölçeğindedir ve orada SE = 1/√(n−3): iki farklı "
                         "sabit, iki farklı ÖLÇEK (çelişki değil)"),
        "beyan": ("PARALEL SÜTUN — ham `ic` alanları DEĞİŞMEZ ve bugünün okuyucuları (beyin, pano, "
                  "yeniden-üretim farkı) HAM ic okumaya devam eder. Küçültülmüş değer hiçbir "
                  "hükme, kapıya ya da eşiğe girmez; küçültme n'i BÜYÜTMEZ, yalnız ortalamayı "
                  "çeker. Katmanlar AYRI küçültülür (gerçek/cf farklı popülasyonlardır). SINIR: "
                  "aynı bileşenin 5/10/20 bar hücreleri aynı gözlemlerden türer, bağımsız "
                  "değildir → τ² bir miktar küçük, küçültme bir miktar güçlü olabilir"),
    }


def _component_frame(df: pd.DataFrame, prox_max: float,
                     index_close: pd.Series | None = None,
                     ticker: str | None = None) -> pd.DataFrame:
    """Bir sembolün TÜM barları için SEKİZ bileşen + üç ileri getiri.

    Formüller `strategy.evaluate_entry`den BİREBİR alınmıştır (satır 114-124); `rs` orada
    kesitsel olarak dışarıdan geldiği için burada da ayrı hesaplanır ve sonradan eklenir.
    `index_close` yalnız `rmom` içindir; yoksa o sütun tamamen NaN kalır (uydurma yok).
    `ticker` yalnız `turnover21` içindir (as-of hisse sayımı sembole çapalıdır); verilmezse o sütun
    tamamen NaN kalır — sıfır DEĞİL, "ölçülemedi"."""
    close, high = df["close"], df["high"]
    tt = ind.trend_template(df)                                   # [0,1] · ısınma dolmadan NaN
    vr = ind.volume_ratio(df["volume"], 50)
    pivot = ind.pivot_high(high, strat.PIVOT_LOOKBACK, exclude_recent=1)
    prox_pct = (close - pivot) / pivot * 100.0
    out = pd.DataFrame(index=df.index)
    out["tight"] = tt * 100.0
    out["vol"] = 100.0 * (vr / 3.0).clip(upper=1.0)
    # KIRPMA TİE ÜRETİR VE BU BİLİNÇLİ: canlı formül `min(prox/prox_max, 1)` ile eşiğin ötesindeki
    # her barı 0'a bastırır. Ölçümü "düzeltip" kırpmasız hesaplamak, canlı skorda OLMAYAN bir
    # bileşenin IC'sini raporlamak olurdu. Spearman beraberlikleri ortalama rütbeyle kırar.
    out["prox"] = (100.0 * (1.0 - (prox_pct / prox_max).clip(upper=1.0))
                   if prox_max > 0 else pd.Series(0.0, index=df.index))
    out.loc[pivot <= 0, "prox"] = float("nan")                    # geçersiz pivot → ölçülemedi
    # HAM seriler, canlı yolun kullandığı AYNI indicators fonksiyonlarıyla
    # (tek yasa, tek uygulama — modül başlığı, karar 1).
    out["rvol20"] = ind.rvol20(df["volume"])
    out["mom12_1"] = ind.mom_12_1(close)
    out["rmom"] = ind.residual_momentum(close, index_close)
    # turnover21 = medyan21(hacim)/as_of_shares(t). Payda BAR BAŞINA as-of
    # okunur (tek çağrı, vektörel) — sembolün bugünkü hisse sayısını tüm geçmişe yaymak PIT
    # sızıntısı olurdu ve tam olarak EDGAR README'nin GOOGL örneğindeki hatadır. Ölçülemeyen
    # payda → o barda NaN + neden (sayaç `edgar_shares.okuma_raporu()`nda).
    out["turnover21"] = _turnover_serisi(df, ticker)
    for h, seri in forward_returns(df).items():
        out[f"fwd{h}"] = seri
    return out


def _turnover_serisi(df: pd.DataFrame, ticker: str | None) -> pd.Series:
    """Sembolün TÜM barları için devir hızı. Payda = as-of EDGAR hisse sayımı (bar başına).

    ÜRETİM YOLU BUNU KENDİLİĞİNDEN KAPSAR: `component_ic()` bu çerçeveyi her gece (P5) yeniden
    kurar, yani düğme 0'da dururken bile `turnover21` hücreleri dolar ve kartın "ölçüsünü öğrenme
    döngüsü versin" kararı ölçülebilir bir zemine oturur. Ticker verilmezse ya da bar çerçevesi
    tarihsizse seri tamamen NaN'dır (uydurma yasağı — tarihsiz bir as-of okuma yapılamaz)."""
    bos = pd.Series(float("nan"), index=df.index)
    if not ticker:
        return bos
    try:
        from .adapters import edgar_shares as _es
        idx = df.index
        tarihler = (idx if isinstance(idx, pd.DatetimeIndex)
                    else pd.to_datetime(df["date"]) if "date" in df.columns else None)
        if tarihler is None:
            return bos
        sh, _neden = _es.as_of_shares_series(
            ticker, [d.strftime("%Y-%m-%d") for d in pd.DatetimeIndex(tarihler)])
        return ind.turnover21(df["volume"], pd.Series(sh, index=df.index))
    except Exception as e:
        # YASA 4: sessizce NaN dönmek, turnover satırının neden hep "n=0" olduğunu cevapsız
        # bırakırdı — bileşen ölçülemez ama SEBEBİ adıyla deftere düşer.
        obs.warn("component_ic_turnover_failed", ticker=ticker, error=f"{type(e).__name__}: {e}")
        return bos


def forward_returns(df: pd.DataFrame) -> dict:
    """{ufuk: ileri getiri serisi}. TEK TANIM, İKİ TÜKETİCİ (bileşen IC'si + eşik eğrisi).

    İkinci bir yerde `close.shift(-h)/close-1` yazmak, ölçüm tanımını iki dosyaya kopyalamak olurdu;
    biri değişince (ör. açılıştan ölçmeye geçilse) diğeri sessizce eski tanımda kalır ve iki tablo
    aynı adı taşıyan iki farklı büyüklüğü gösterir. `getiri_tanimi` alanı da bu tek tanımı anlatır.

    İLERİ BAKAN TEK YER VE YALNIZ ÖLÇÜM İÇİN: bu seri hiçbir sinyale, kapıya ya da karara girmez.
    Serinin sonundaki h bar NaN kalır (ufuk dolmadı) — uydurulmaz."""
    close = df["close"]
    return {h: close.shift(-h) / close - 1.0 for h in HORIZONS}


# ---- ÇERÇEVEDE OLMAYAN TARİHİN SINIFI: BUG MU, BEYAN EDİLMİŞ DIŞLAMA MI? -----------
# ÖLÇÜLDÜ, VARSAYILMADI. MAKULLÜK paneli iki ihlal bağırıyordu — `eleme:component_ic.eslesme:
# sema_elemesi` ve `eleme:threshold_curve.eslesme:sema_elemesi` — ikisi de aynı cümleyle: "7 satır
# VERİ SÖZLEŞMESİ yüzünden elendi, bu bir piyasa filtresi DEĞİL yazılım hatasıdır". Yedi satırın
# kimliği çıkarıldı (research/olcumler/makulluk_2026-08-07/): YEDİSİ DE `DD`, yedisi de cf katmanı,
# tarihler 2022-11-10 … 2024-07-31. `DD`nin `bars_integrity` kaydı `guvenli_baslangic: 2025-11-04`
# diyor; yani barlar ham önbellekte VAR ama `adapters.data.measurement_bars` o tarihten öncesini
# ÖLÇÜM ÇERÇEVESİNDEN BİLEREK ÇIKARIYOR (çözülmemiş ölçek/kimlik kırılması — `measurement_bars`
# gerekçesinde adı geçen HON/DD çifti).
#
# HÜKÜM: bu bir veri sözleşmesi hatası DEĞİLDİR. Satır beklenen alanı TAŞIYOR (ticker + tarih
# yerinde); çerçeve o barı taşımıyor ve TAŞIMAMASI KARARDIR. `sema:` demek, bekçinin her turda
# olmayan bir hata için kırmızı yakması demekti — sieve'in kendi yazılı gerekçesiyle birebir çelişir
# ("dedektör kurt masalı anlatmamalı: operatör kırmızıyı yok saymayı öğrenir, sonra GERÇEK bir
# `sema:` ihlali de görünmez olur").
#
# BEKÇİ ZAYIFLATILMADI — İKİYE AYRILDI. Ledger'ın dışladığı tarih `piyasa:` (meşru, beyanlı,
# SAYILAN filtre; panonun eleme tablosunda "piyasa filtresi N" olarak görünür ve künyedeki aşama
# listesinden okunur). Ledger'ın SÖYLEMEDİĞİ bir eksik tarih — takvim boşluğu, hayalet seans, bozuk
# defter satırı — HÂLÂ `sema:bar_yok:tarih`tir ve ihlal üretir. Yani gerçek arıza sınıfı için
# dedektörün dişi yerinde durur; susan yalnız yanlış alarm.
DISLAMA_NEDENI = "piyasa:butunluk_dislamasi:guvenli_baslangic_oncesi"


def butunluk_disladi(ticker: str, dstr: str) -> bool:
    """Bu (sembol, tarih) çifti ölçüm çerçevesinden BÜTÜNLÜK DEFTERİ tarafından mı düşürüldü?

    Kural DEFTERDEN okunur, burada yeniden yazılmaz: `measurement_bars` da aynı `safe_start`
    eşiğiyle kırpıyor (`date >= guvenli_baslangic`). İkinci bir yerde ikinci bir eşik tanımlamak,
    bu depoda adı konmuş hata sınıfı olurdu (aynı yasanın iki kopyası zamanla ayrışır).
    Defterde kayıt yoksa None döner → kısıt yok → dışlama iddiası KURULAMAZ (False)."""
    from .adapters import data as data_adapter
    ss = data_adapter.safe_start(ticker)
    return bool(ss and str(dstr)[:10] < str(ss))


def eslesme_nedeni(ticker: str, dstr: str) -> str:
    """Çerçevede olmayan bir tarihin ELEME NEDENİ — tek tanım, iki tüketici (`forward_returns` ile
    aynı gerekçe: eşleştirme yasası iki dosyaya kopyalanırsa biri sessizce eski sınıfta kalır)."""
    return DISLAMA_NEDENI if butunluk_disladi(ticker, dstr) else "sema:bar_yok:tarih"


def _bars_taban() -> dict:
    """Bu tablonun üretildiği bar tabanının damgası (`bars_integrity` defterinin bu turdaki etkisi).

    Yerel ithalat, modülün mevcut deseni (`_load_universe`/`_load_index_close` ile aynı): `adapters`
    zinciri bu modülün ithalat yüzeyine girmesin."""
    from .adapters import data as data_adapter
    return data_adapter.integrity_report()


def _turnover_kaynak() -> dict:
    """EDGAR payda okumasının bu koşumdaki sayacı + en sık ölçülememe sebebi.

    Yerel ithalat, modülün mevcut deseni (`_bars_taban`/`_load_universe` ile aynı). Sayaç okunamazsa
    sebebiyle birlikte döner — sessiz boş sözlük, "hiç okuma olmadı" ile "sayaç kırık" arasındaki
    farkı silerdi."""
    try:
        from .adapters import edgar_shares as _es
        r = _es.okuma_raporu()
        neden = r.get("neden") or {}
        r["en_sik_neden"] = (max(neden.items(), key=lambda kv: kv[1])[0] if neden else None)
        return r
    except Exception as e:
        return {"hata": f"{type(e).__name__}: {e}",
                "not": "payda sayacı OKUNAMADI — turnover hücreleri yine de tabloda (None ise ölçülemedi)"}


def _load_universe() -> dict:
    """Önbellek CSV'lerinden bar evreni (cf_backfill ile AYNI yol: ağ yok, sanitize onarımı var)."""
    from .adapters import data as data_adapter
    per = {}
    for t in data_adapter.REPLAY_UNIVERSE:
        cp = data_adapter._cache_path(t)
        if not cp.exists():
            continue
        try:
            df, _ = data_adapter.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
            # BÜTÜNLÜK DEFTERİ (hayalet-round-2): çözülmemiş ölçek/kimlik kırılmasından
            # ÖNCEKİ dönem ölçümden düşer. Kural burada YENİDEN YAZILMAZ — `bars_integrity` defteri
            # okunur (tek yasa, iki tüketici: cf_backfill aynı satırı çağırır). Defter yoksa hiçbir
            # şey düşmez; tablonun eski hâline döner ve bunu `integrity_report()` söyler.
            df = data_adapter.measurement_bars(df, t)
            if df is not None and len(df) > strat.PIVOT_LOOKBACK + 3:
                per[t] = df.set_index("date").sort_index()
        except Exception as e:
            # YASA 4: `continue` sembolü ölçüm evreninden SESSİZCE düşürürdü — bileşen IC'sinin
            # paydası küçülür, hiçbir hata görünmez ve "neden bu kadar az satır?" cevapsız kalır.
            obs.warn("component_ic_bars_unreadable", ticker=t, error=f"{type(e).__name__}: {e}")
    return per


def _load_index_close() -> pd.Series | None:
    """Endeks (SPY) kapanışları — `rmom`un beta regresyonu için. `_load_universe` ile AYNI yol:
    ağ yok, bar önbelleğinden, `sanitize_bars` onarımıyla.

    Okunamazsa None döner ve rmom sütunu tamamen NaN kalır → o hücreler "ölçülemedi" olarak görünür,
    sıfır olarak DEĞİL. YASA 4: sessizce None dönmez, sebebini adıyla uyarır — yoksa rmom satırı
    tabloda aylarca "n=0" durur ve kimse endeks barının hiç okunmadığını fark etmez."""
    from .adapters import data as data_adapter
    sym = getattr(data_adapter, "INDEX_SYMBOL", "SPY")
    try:
        cp = data_adapter._cache_path(sym)
        if not cp.exists():
            obs.warn("component_ic_index_bars_missing", symbol=sym, path=str(cp))
            return None
        df, _ = data_adapter.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), sym)
        df = data_adapter.measurement_bars(df, sym)      # evrenle AYNI kapı (bkz. _load_universe)
        if df is None or df.empty:
            obs.warn("component_ic_index_bars_empty", symbol=sym)
            return None
        return df.set_index("date").sort_index()["close"]
    except Exception as e:
        obs.warn("component_ic_index_bars_unreadable", symbol=sym, error=f"{type(e).__name__}: {e}")
        return None


def _rs_by_date(per: dict, dates: set) -> dict:
    """Kesitsel RS derecesi — YALNIZ gereken tarihler için, canlı yolun kendi fonksiyonuyla.

    RS bir sembolün kendi geçmişinden değil, o gün EVRENİN geri kalanına göre durduğu yerden gelir.
    Bu yüzden tek tek satır üzerinden hesaplanamaz: her tarih için evrenin tamamının getirisi lazım.
    `indicators.rs_rating` doğrudan çağrılır (beraberlik kuralı dahil canlıyla aynı)."""
    rets = pd.DataFrame({t: df["close"] / df["close"].shift(strat.RS_LOOKBACK) - 1.0
                         for t, df in per.items()})
    out = {}
    for d in sorted(dates):
        if d not in rets.index:
            continue
        row = rets.loc[d].dropna()
        if row.empty:
            continue
        out[d] = ind.rs_rating({t: float(v) for t, v in row.items()})
    return out


def _rows() -> tuple[list, dict]:
    """Ölçülecek gözlemler: (katman, ticker, tarih). Eleme muhasebesiyle.

    cf tarafı `resolved_rows(entered_only=True)` — `score_calibration`ın kullandığı POPÜLASYONUN
    AYNISI (near-miss hariç). İki tablo aynı satırlardan hesaplanmazsa "bileşik skorun IC'si şu,
    bileşenlerinki bu" karşılaştırması iki farklı deftere bakan bir kıyas olurdu."""
    from . import counterfactual as cf
    rows, sayim = [], {"gercek": 0, "cf": 0}
    with sieve.Sieve("component_ic.gercek") as sv:
        for t in store.read_jsonl("trades.jsonl"):
            pid = str(t.get("plan_id") or "")
            if not pid.startswith("P-"):
                sv.drop("sema:plan_id_biçimi:eski_şema"); continue
            parts = pid.split("-")                       # P-YYYY-MM-DD-TICKER
            if len(parts) < 5:
                sv.drop("sema:plan_id_biçimi:eksik_parça"); continue
            sv.keep()
            rows.append(("gercek", parts[4], "-".join(parts[1:4])))
            sayim["gercek"] += 1
    with sieve.Sieve("component_ic.cf") as sv:
        for r in cf.resolved_rows(entered_only=True):
            if not r.get("ticker") or not r.get("date"):
                sv.drop("sema:eksik_alan:ticker_veya_date"); continue
            sv.keep()
            rows.append(("cf", str(r["ticker"]), str(r["date"])[:10]))
            sayim["cf"] += 1
    return rows, sayim


def component_ic(write: bool = True) -> dict | None:
    """Bileşen × ufuk × katman IC tablosu. Ölçülemeyen her hücre None kalır (UYDURMA YASAĞI).

    Dönüş None: hiç gözlem yoksa ya da bar evreni okunamadıysa — boş bir tablo yazıp "ölçtük"
    izlenimi vermek, ölçmemekten daha kötüdür.

    `write=False` (yeniden-üretim aracı için): tabloyu hesaplar ama `component_ic.json`a
    ve başarı olayına YAZMAZ. Varsayılan True olduğu için gecelik P5 çağrısı (loop.py) birebir
    eskisi gibi davranır. Kuru koşunun yazmaması bir incelik değil şart: bu tablo canlı state'te
    durur ve worker koşarken ikinci bir sürecin yazması bu depoda yasak.
    DÜRÜST SINIR: bar okuma yolunun UYARILARI (hayalet satır, karantina, dışlanan dönem —
    `obs.warn`) kuru koşuda da deftere düşer. Onlar ölçümün kendi kaydıdır ve susturulmaları YASA
    4 ihlali olurdu; yani "kuru koşu" = artefakta dokunmaz, telemetriye sessizlik vaat etmez."""
    rows, sayim = _rows()
    if not rows:
        return None
    per = _load_universe()
    if not per:
        obs.warn("component_ic_no_bars", detail="önbellekte bar yok — bileşen IC'si ölçülemedi")
        return None

    params = config.load_strategy()["params"]
    prox_max = float(params.get("entry.pivot_proximity_pct", 2.0) or 2.0)
    # rmom'un ağırlığı YOKTUR (düğmesi yok) → None kalır; 0.0 yazmak "ağırlığı sıfıra ayarlanmış bir
    # düğme var" demek olurdu ve pano o satırı öbür sıfırlarla aynı okurdu.
    agirliklar = {c: (None if COMPONENT_WEIGHT_KEY[c] is None
                      else float(params.get(COMPONENT_WEIGHT_KEY[c], COMPONENT_WEIGHT_DEFAULT[c])))
                  for c in COMPONENTS}
    index_close = _load_index_close()

    # Bileşen serileri sembol başına BİR KEZ (satır başına değil): 7000+ satırın çoğu aynı sembolün
    # farklı günleri; satır başına yeniden hesap aynı yuvarlanan pencereyi yüzlerce kez kurardı.
    gerekli = {t for _, t, _ in rows}
    comp = {}
    for t in sorted(gerekli & set(per)):
        try:
            comp[t] = _component_frame(per[t], prox_max, index_close, ticker=t)
        except Exception as e:
            obs.warn("component_ic_frame_failed", ticker=t, error=f"{type(e).__name__}: {e}")

    tarihler = {pd.Timestamp(d) for _, t, d in rows if t in comp}
    rs_map = _rs_by_date(per, tarihler)

    # (katman, bileşen, ufuk) → [(bileşen_değeri, ileri_getiri), ...]
    buk: dict = {(lay, c, h): [] for lay in LAYERS for c in COMPONENTS for h in HORIZONS}
    gorulen: set = set()          # havuz tekilleştirmesi (bkz. modül başlığı, karar 3)
    with sieve.Sieve("component_ic.eslesme") as sv:
        # GERÇEK ÖNCE: havuz tekilleştirmesinde çakışan (ticker, tarih) gerçek katmandan sayılsın.
        for katman, ticker, dstr in sorted(rows, key=lambda r: (r[0] != "gercek", r[1], r[2])):
            frame = comp.get(ticker)
            if frame is None:
                sv.drop("sema:bar_yok:sembol"); continue
            d = pd.Timestamp(dstr)
            if d not in frame.index:
                sv.drop(eslesme_nedeni(ticker, dstr)); continue   # bkz. `eslesme_nedeni` bloğu
            satir = frame.loc[d]
            rsv = (rs_map.get(d) or {}).get(ticker)
            if rsv is None:
                sv.drop("sema:rs_kesiti_yok")
                continue
            sv.keep()
            degerler = {"rs": float(rsv), "tight": satir["tight"], "vol": satir["vol"],
                        "prox": satir["prox"], "rvol20": satir["rvol20"],
                        "mom12_1": satir["mom12_1"], "rmom": satir["rmom"],
                        "turnover21": satir["turnover21"]}
            yeni = (ticker, dstr) not in gorulen
            gorulen.add((ticker, dstr))
            for c in COMPONENTS:
                x = degerler[c]
                if pd.isna(x):
                    continue          # ısınma dolmamış bileşen — o HÜCRE için gözlem yok, satır değil
                for h in HORIZONS:
                    y = satir[f"fwd{h}"]
                    if pd.isna(y):
                        continue      # ufuk dolmadı (serinin sonu) — uydurulmaz
                    buk[(katman, c, h)].append((x, float(y)))
                    if yeni:
                        buk[("havuz", c, h)].append((x, float(y)))

    def _hucre(pairs: list) -> dict:
        """Tek IC hücresinin özeti: örneklem eşiği altındaysa `ic=None` + neden; rütbe değişimi yoksa yine
        None ("0.0 ilişki" DEĞİL, tanımsız). Aksi hâlde Spearman IC + Fisher %95 aralığı ve aralığın
        sıfırı dışlayıp dışlamadığı (anlamlılık)."""
        if len(pairs) < IC_MIN_SAMPLE:
            return {"ic": None, "n": len(pairs), "neden": f"n<{IC_MIN_SAMPLE}",
                    "ci": None, "anlamli": None}
        ic = spearman_ic(pairs)
        # ic None: bir tarafta hiç rütbe değişimi yok → korelasyon TANIMSIZ, "0.0 ilişki" değil.
        if ic is None:
            return {"ic": None, "n": len(pairs), "neden": "rütbe değişimi yok",
                    "ci": None, "anlamli": None}
        lo, hi = _fisher_ci(ic, len(pairs))
        return {"ic": round(ic, 4), "n": len(pairs), "neden": None,
                "ci": None if lo is None else {"lo": lo, "hi": hi, "seviye": 0.95},
                # ANLAMLILIK = ARALIK SIFIRI DIŞARIDA BIRAKIYOR MU. Tek bir IC sayısına bakıp
                # "vol pozitif, ağırlığını artıralım" demek, n=95'te ±0.20 genişliğindeki bir
                # aralığın içindeki bir kıpırtıyı bulgu sanmaktır — 07-28'in ilk bileşen tablosu
                # tam olarak böyle okunma riski taşıyordu.
                "anlamli": None if lo is None else bool(lo > 0 or hi < 0)}

    tablo = {lay: {c: {str(h): _hucre(buk[(lay, c, h)]) for h in HORIZONS} for c in COMPONENTS}
             for lay in LAYERS}

    # HÜKÜM: en güçlü |IC| hangi bileşende ve ölçülebilen hücre var mı? Yalnız GERÇEK katman
    # hüküm taşır (kuzey yıldızının 1. ölçütüyle aynı yasa) — cf katmanı bağlamdır, kanıt değil.
    olculen = [(c, h, tablo["gercek"][c][str(h)]["ic"], tablo["gercek"][c][str(h)]["n"])
               for c in COMPONENTS for h in HORIZONS if tablo["gercek"][c][str(h)]["ic"] is not None]
    # ANLAMLI HÜCRE SAYIMI HER KATMAN İÇİN AYRI: 1.4 karar kapısının sorusu ("hiçbir bileşen anlamlı
    # IC taşımıyor mu?") gerçek katmanda örneklem kuraklığından, cf katmanında ise gerçekten sıfır
    # bilgiden ötürü "hayır" cevabı alabilir — ikisi AYNI cevap değildir ve tek sayıya indirilemez.
    anlamli_sayim = {lay: sum(1 for c in COMPONENTS for h in HORIZONS
                              if tablo[lay][c][str(h)].get("anlamli") is True) for lay in LAYERS}
    if not olculen:
        verdict = ("gerçek katmanda ÖLÇÜLEBİLEN bileşen hücresi yok — dört bileşenin hiçbiri "
                   f"hakkında bir şey söylenemez (her hücre n<{IC_MIN_SAMPLE} ya da rütbe değişimi yok)")
        en_guclu = None
    else:
        c, h, ic, n = max(olculen, key=lambda x: abs(x[2]))
        hucre = tablo["gercek"][c][str(h)]
        en_guclu = {"bilesen": c, "horizon": h, "ic": ic, "n": n,
                    "ci": hucre.get("ci"), "anlamli": hucre.get("anlamli")}
        # HÜKÜM CÜMLESİ ANLAMLILIĞI SÖYLER: "en güçlü bileşen X" cümlesi tek başına, aralığı sıfırı
        # kapsayan bir sayıyı da bir bulgu gibi okutur. 07-28'in ilk tablosunda dört hücrenin dördü
        # de böyleydi ve cümle bunu söylemiyordu.
        nitelik = ("ANLAMLI" if hucre.get("anlamli") is True
                   else "anlamlı DEĞİL (aralık sıfırı kapsıyor)")
        verdict = (f"gerçek katmanın en güçlü bileşeni: {c} · {h} bar · IC {ic} (n={n}) — {nitelik}; "
                   f"{len(olculen)}/{len(COMPONENTS) * len(HORIZONS)} hücre ölçülebildi, "
                   f"{anlamli_sayim['gercek']} anlamlı. "
                   f"cf (sim) katmanında {anlamli_sayim['cf']} anlamlı hücre var — bağlam, kanıt değil")

    out = {
        "horizons": list(HORIZONS), "components": list(COMPONENTS), "layers": list(LAYERS),
        "agirliklar": agirliklar,
        # GETİRİ TANIMI ÇIKTININ İÇİNDE: panoyu ya da beyni okuyan biri "hangi getiri?" sorusunu
        # koda inmeden cevaplayabilmeli. Tanım değişirse bu satır da değişir; ikisi ayrı düşemez.
        "getiri_tanimi": "close[t+h]/close[t]-1 (sinyal barı kapanışından, yüzde; R'ye bölünmez)",
        "prox_max": prox_max, "tablo": tablo, "en_guclu": en_guclu, "verdict": verdict,
        "anlamli_sayim": anlamli_sayim,
        # EMPİRİK-BAYES PARALEL SÜTUN — `tablo`ya DOKUNMAZ, yanında durur.
        # Gerekçe ve sınırlar `_eb_blok`un üstündeki blokta; okuyucusu
        # `analytics.shrunk_component_ic().tablo_ici_eb` (YASA 6).
        "eb": _eb_blok(tablo),
        # YENİ BİLEŞENLERİN ÖLÇEK BEYANI ÇIKTININ İÇİNDE (getiri tanımı/CI varsayımıyla aynı
        # gerekçe): panoyu ya da beyni okuyan biri "bu satır skora giren büyüklüğün mü, ham
        # göstergenin mi IC'si?" sorusunu koda inmeden cevaplayabilmeli — aksi hâlde bant puanının
        # IC'si sanılır ve monoton olmayan bir dönüşümün ardındaki fark görünmez.
        "yeni_bilesen_notu": ("rvol20/mom12_1/rmom HAM seri olarak ölçülür (G2 kanıt tabanıyla "
                              "doğrudan kıyaslanabilsin diye). Skora giren büyüklükler DÖNÜŞÜMDÜR: "
                              "entry.w_rvolband üçgen bant puanını, entry.w_mom 63-barlık yüzdelik "
                              "rütbeyi çarpar; üçgen MONOTON DEĞİLdir → bu IC bant puanının IC'si "
                              "değildir. rmom'un ağırlık düğmesi yoktur (yedek aday, ölçülür). "
                              "turnover21 (EDG-016) HAM oran olarak ölçülür; skora giren büyüklük "
                              "onun yüzdelik puanıdır (strategy.turnover_score) ve o dönüşüm "
                              "MONOTONdur → Spearman IC'si aynı sayıdır."),
        # TURNOVER PAYDASININ KAYNAK SAYACI — ÜRETİLEN KANIT TÜKETİLİR (YASA 6). Bu alan aynı
        # zamanda fail-open beyanının GÖRÜNÜR yüzüdür: kaç hücrenin hangi sebeple ölçülemediği
        # (dosya yok / sembol EDGAR kapsamında değil / seri bayat / ölçek hatası) burada durur ve
        # gecelik `component_ic` olayına özet olarak düşer. Sayaç SÜREÇ-İÇİdir: bu koşumun
        # okumalarını sayar, tarihsel bir toplam değildir.
        "turnover_kaynak": _turnover_kaynak(),
        # ARALIĞIN YÖNTEMİ VE VARSAYIMI ÇIKTININ İÇİNDE (getiri tanımıyla aynı gerekçe): panoyu ya
        # da beyni okuyan biri "bu aralık neye göre?" sorusunu koda inmeden cevaplayabilmeli.
        "ci_yontem": "Fisher-z, SE=1/sqrt(n-3), %95 iki yanlı",
        "ci_varsayim": ("gözlemler bağımsız varsayılır; cf katmanında satırlar güne/sembole "
                        "kümelenmiştir → gerçek aralık daha GENİŞtir, buradaki bir ALT SINIRdır"),
        "cf_katman_gerekce": ("ileri getiri BARLARDAN hesaplanır (close[t+h]/close[t]-1); cf'ten "
                              "yalnız GİRİŞ ANI alınır. cf'in çıkış-simülasyonu sadakat kusuru "
                              "r_multiple'ı kirletir, bu tablonun y eksenini KİRLETMEZ"),
        "n_gozlem": {"gercek": sayim["gercek"], "cf": sayim["cf"], "havuz_tekil": len(gorulen)},
        # BAR TABANI ÇIKTININ İÇİNDE (getiri tanımı/CI varsayımıyla AYNI gerekçe): `bars_integrity`
        # defteri evrenden DÖNEM düşürür — çözülmemiş ölçek/kimlik kırılmasından önceki geçmiş.
        # Hangi tabandan üretildiği yazılmazsa iki `component_ic.json` aynı adı taşıyıp farklı bar
        # kümesine ait olur ve fark GÖRÜNMEZ; "bu tabloyu yeniden üretmek gerekir mi?" sorusu da
        # tahminle cevaplanır. Bu satır aynı zamanda `integrity_report()` sayacının TÜKETİCİSİdir:
        # üretilip tüketilmeyen kanıt bu depoda yasaktır (YASA 6).
        "bars_integrity": _bars_taban(),
        sieve.PROV_KEY: sieve.provenance(sayim["gercek"] + sayim["cf"], sayim["gercek"], sayim["cf"],
                                         stages_=("component_ic.gercek", "component_ic.cf",
                                                  "component_ic.eslesme")),
    }
    if write:
        store.write_json(COMPONENT_IC_FILE, out)
        # GÜNLÜK DÖNGÜ OLAYINDA TURNOVER SAYACI (fail-open beyanının okuyucusu): payda kaç
        # kez okunabildi, kaç kez okunamadı ve EN SIK sebep neydi. Olay satırı kısa tutulur; tam
        # döküm `component_ic.json` → `turnover_kaynak` alanındadır.
        tk = out.get("turnover_kaynak") or {}
        obs.log("component_ic", n_gercek=sayim["gercek"], n_cf=sayim["cf"],
                olculen_hucre=len(olculen) if olculen else 0,
                turnover_payda_olculdu=tk.get("olculdu"),
                turnover_payda_olculemedi=tk.get("olculemedi"),
                turnover_payda_en_sik_neden=tk.get("en_sik_neden"))
    return out


def compact_lines(doc: dict | None = None, max_satir: int = 6) -> list[str]:
    """evidence_pack için KOMPAKT özet: yalnız gerçek katmanın ölçülebilen hücreleri, |IC| sırasıyla.

    Beyne tam tablo (3 katman × 4 bileşen × 3 ufuk = 36 hücre) verilirse prompt şişer ve içindeki
    tek anlamlı satır kaybolur. Ölçülemeyen hücreler HİÇ gitmez — ama kaç tanesinin ölçülemediği
    bir satırda söylenir; "gördüğün her şey bu" ile "ölçebildiğimiz her şey bu" farkı beyne de
    açıkça gitmeli, yoksa eksik kanıttan tam-kanıt gibi öneri üretir."""
    doc = doc if doc is not None else store.read_json(COMPONENT_IC_FILE, None)
    if not doc or not doc.get("tablo"):
        return []
    g = doc["tablo"].get("gercek") or {}
    hucreler = [(c, h, g[c][str(h)]["ic"], g[c][str(h)]["n"])
                for c in doc.get("components", COMPONENTS) for h in doc.get("horizons", HORIZONS)
                if (g.get(c) or {}).get(str(h), {}).get("ic") is not None]
    toplam = len(doc.get("components", COMPONENTS)) * len(doc.get("horizons", HORIZONS))
    if not hucreler:
        return [f"bileşen IC (gerçek katman): 0/{toplam} hücre ölçülebildi — hiçbir bileşen hakkında "
                f"kanıt yok"]
    hucreler.sort(key=lambda x: -abs(x[2]))

    def _ci_metni(lay: str, c: str, h) -> str:
        """Aralık BEYNE DE gider. Aralıksız bir IC listesi, hipotez üreten tarafa "vol pozitif"
        gibi okunur ve ağırlık değiştirme önerisi ölçülmemiş bir kesinliğe dayanır."""
        cell = ((doc["tablo"].get(lay) or {}).get(c) or {}).get(str(h), {})
        ci = cell.get("ci")
        if not ci:
            return ""
        return f" CI[{ci['lo']},{ci['hi']}]{'' if cell.get('anlamli') else ' (sıfırı kapsıyor)'}"

    satirlar = [f"{c} @{h}bar IC {ic} (n={n}, ağırlık {doc.get('agirliklar', {}).get(c)})"
                f"{_ci_metni('gercek', c, h)}"
                for c, h, ic, n in hucreler[:max_satir]]
    # CF SATIRI AYRI VE ETİKETLİ: 1.4 karar kapısının cevaplanabilir olması için gereken
    # örneklem yalnız cf'te var (n≈2100 vs 95), ama o satırlar ALINMAMIŞ girişlerdir — beyne
    # etiketsiz giderse ikisini aynı kefeye koyar ve seçim yanlılığını görmez.
    cf = doc["tablo"].get("cf") or {}
    cf_hucre = [(c, h, cf[c][str(h)]["ic"], cf[c][str(h)]["n"])
                for c in doc.get("components", COMPONENTS) for h in doc.get("horizons", HORIZONS)
                if (cf.get(c) or {}).get(str(h), {}).get("anlamli") is True]
    cf_hucre.sort(key=lambda x: -abs(x[2]))
    for c, h, ic, n in cf_hucre[:max_satir]:
        satirlar.append(f"[sim/cf] {c} @{h}bar IC {ic} (n={n}){_ci_metni('cf', c, h)} — alınmamış "
                        f"hipotetik girişler, kanıt değil bağlam")
    satirlar.append(f"[{len(hucreler)}/{toplam} hücre ölçülebildi; gerisi örneklem altı — "
                    f"getiri: {doc.get('getiri_tanimi')}]")
    return satirlar


# ==================================================================================================
# YENİDEN ÜRETİM ARACI — "defterdeki tablo hangi bar tabanından çıktı?"
# ==================================================================================================
# NEDEN VAR. `_load_universe`/`_load_index_close` `measurement_bars()` kapısına
# bağlandı: çözülmemiş ölçek/kimlik kırılmasından ÖNCEKİ dönem ölçümden düşer (hayalet-round-2).
# Ama `state/component_ic.json` o günden ÖNCE üretilmişti ve dosya bunu KENDİ SÖYLÜYOR: `bars_integrity`
# alanı yok (o alan da aynı turda eklendi). Yani defterdeki tablo ile bugünkü boru hattının ürettiği
# tablo AYNI ADI taşıyan İKİ FARKLI ölçümdür — ve fark ölçüldü (cf rvol20 @20
# defterde 0,0604, dışlamalı boru hattında 0,0637).
#
# NEDEN AYRI BİR ARAÇ (gecelik P5 zaten `component_ic()` çağırıyor). İki sebep:
#   (1) Gecelik koşum tabloyu SESSİZCE değiştirir; hangi hücrenin ne kadar kaydığı hiçbir yerde
#       görünmez. Bu tablo 1.4 karar kapısının ve ağırlık tartışmasının girdisi — "anlamlı" bayrağı
#       düşen bir hücrenin fark edilmeden değişmesi, kararın altını sessizce oyar.
#   (2) P5 veri kapsamasına REHİN (öğrenme-rehineliği dersi): daily_cycle noop olduğu gecelerde
#       öğrenme adımları da durur. Yeniden üretimin ne zaman gerçekleştiği tahmine kalmamalı.
#
# YETKİSİ SIFIR VE KURU KOŞU VARSAYILAN: araç yalnız ESKİ↔YENİ farkını basar. `--uygula` verilmedikçe
# tek bayt yazmaz; verildiğinde de canlı worker koşuyorsa REDDEDER (state'e iki süreçten yazım yasağı).
# İDEMPOTENT: aynı bar tabanı + aynı defterlerle ikinci koşum "0 hücre değişti" der ve aynı içeriği
# yazar (çıktıda zaman damgası yoktur — fark yalnız GERÇEK bir girdi değişikliğinden gelir).
_FARK_ALANLARI = ("ic", "n", "anlamli")


def _hucre_farklari(eski: dict | None, yeni: dict) -> list[dict]:
    """Hücre hücre ESKİ↔YENİ. Kayıp/yeni hücre de bir FARKtır: ölçülebilirlik sınırının kayması
    (n eşiğin altına düşmesi) sayının kaymasından daha büyük bir haberdir."""
    e_tab = (eski or {}).get("tablo") or {}
    y_tab = yeni.get("tablo") or {}
    out = []
    for lay in LAYERS:
        for c in COMPONENTS:
            for h in HORIZONS:
                e = ((e_tab.get(lay) or {}).get(c) or {}).get(str(h))
                y = ((y_tab.get(lay) or {}).get(c) or {}).get(str(h))
                if y is None:
                    continue                      # yeni tabloda hiç yok (bileşen listesi değişmiş)
                e = e or {}
                if all(e.get(k) == y.get(k) for k in _FARK_ALANLARI) and e:
                    continue
                d_ic = (None if (e.get("ic") is None or y.get("ic") is None)
                        else round(float(y["ic"]) - float(e["ic"]), 4))
                out.append({"katman": lay, "bilesen": c, "ufuk": h,
                            "eski_ic": e.get("ic"), "yeni_ic": y.get("ic"), "d_ic": d_ic,
                            "eski_n": e.get("n"), "yeni_n": y.get("n"),
                            "eski_anlamli": e.get("anlamli"), "yeni_anlamli": y.get("anlamli"),
                            "anlamlilik_dondu": (e.get("anlamli") is not y.get("anlamli")),
                            "defterde_yoktu": not e})
    # SIRALAMA HÜKME GÖRE: önce anlamlılığı dönen hücreler (karar girdisi), sonra |Δic|.
    out.sort(key=lambda r: (not r["anlamlilik_dondu"], -abs(r["d_ic"] or 0)))
    return out


def yeniden_uret(uygula: bool = False) -> dict:
    """component_ic.json'ı GÜVENSİZ-DÖNEM-DIŞLAMALI boru hattından yeniden üretir.

    Kuru koşu (varsayılan): hesaplar, defterdekiyle karşılaştırır, HİÇBİR ŞEY yazmaz.
    `uygula=True`: aynı hesabı yazar. Yeni tablo ölçülemezse (None) HİÇBİR KOŞULDA yazılmaz —
    ölçülemeyen bir turda defteri boşaltmak, elde olan kanıtı da silmek olurdu."""
    eski = store.read_json(COMPONENT_IC_FILE, None)
    yeni = component_ic(write=False)
    if yeni is None:
        return {"uygulandi": False, "olculdu": False,
                "neden": ("yeni tablo ÖLÇÜLEMEDİ (gözlem yok ya da bar evreni okunamadı) — "
                          "defter OLDUĞU GİBİ bırakıldı"),
                "eski_var": bool(eski), "farklar": [], "sayim": {}}
    farklar = _hucre_farklari(eski, yeni)
    toplam = len(LAYERS) * len(COMPONENTS) * len(HORIZONS)
    rapor = {
        "olculdu": True, "eski_var": bool(eski),
        "sayim": {
            "hucre_toplam": toplam, "degisen": len(farklar),
            "anlamlilik_donen": sum(1 for f in farklar if f["anlamlilik_dondu"]),
            "defterde_olmayan": sum(1 for f in farklar if f["defterde_yoktu"]),
        },
        # BAR TABANI FARKI ASIL SORU: tablonun hangi evrenden çıktığı. Eski dosyada alan YOKSA
        # bu "bilinmiyor" değil, "dışlama kapısı henüz yoktu" demektir ve öyle yazılır.
        "bar_tabani": {
            "eski": (eski or {}).get("bars_integrity", "ALAN YOK — dışlama kapısından ÖNCE üretilmiş"),
            "yeni": yeni.get("bars_integrity"),
        },
        "n_gozlem": {"eski": (eski or {}).get("n_gozlem"), "yeni": yeni.get("n_gozlem")},
        "anlamli_sayim": {"eski": (eski or {}).get("anlamli_sayim"), "yeni": yeni.get("anlamli_sayim")},
        "verdict": {"eski": (eski or {}).get("verdict"), "yeni": yeni.get("verdict")},
        "farklar": farklar,
        "uygulandi": False,
    }
    if uygula:
        store.write_json(COMPONENT_IC_FILE, yeni)
        obs.log("component_ic_yeniden_uretildi", degisen_hucre=len(farklar),
                anlamlilik_donen=rapor["sayim"]["anlamlilik_donen"],
                n_gercek=(yeni.get("n_gozlem") or {}).get("gercek"),
                n_cf=(yeni.get("n_gozlem") or {}).get("cf"))
        rapor["uygulandi"] = True
    return rapor


def _fark_yazdir(rapor: dict, max_satir: int = 40) -> None:
    """Yeniden-üretim raporunu insan okunur biçimde basar: kuru koşu mu uygulandı mı, değişen hücre
    sayımları, gözlem/anlamlılık kırılımları, bar tabanları ve (tavana kırpılmış) fark tablosu."""
    mod = "UYGULANDI" if rapor.get("uygulandi") else "KURU KOŞU (hiçbir bayt yazılmadı)"
    print(f"[component_ic] {mod}")
    if not rapor.get("olculdu"):
        print(f"  {rapor.get('neden')}")
        return
    s = rapor["sayim"]
    print(f"  hücre: {s['degisen']}/{s['hucre_toplam']} DEĞİŞTİ · anlamlılığı dönen: "
          f"{s['anlamlilik_donen']} · defterde hiç olmayan: {s['defterde_olmayan']}")
    print(f"  gözlem  eski={rapor['n_gozlem']['eski']}")
    print(f"          yeni={rapor['n_gozlem']['yeni']}")
    print(f"  anlamlı eski={rapor['anlamli_sayim']['eski']}  yeni={rapor['anlamli_sayim']['yeni']}")
    bt_e, bt_y = rapor["bar_tabani"]["eski"], rapor["bar_tabani"]["yeni"]
    print(f"  bar tabanı ESKİ: {bt_e if isinstance(bt_e, str) else json.dumps(bt_e, ensure_ascii=False)[:200]}")
    print(f"  bar tabanı YENİ: {json.dumps(bt_y, ensure_ascii=False)[:200] if bt_y else 'YOK'}")
    if rapor["farklar"]:
        print(f"  {'katman':7} {'bileşen':9} {'ufuk':>4} {'eski_ic':>9} {'yeni_ic':>9} {'Δ':>8} "
              f"{'eski_n':>7} {'yeni_n':>7}  anlamlı")
        for f in rapor["farklar"][:max_satir]:
            anl = f"{f['eski_anlamli']}→{f['yeni_anlamli']}" + (" **" if f["anlamlilik_dondu"] else "")
            print(f"  {f['katman']:7} {f['bilesen']:9} {f['ufuk']:>4} "
                  f"{str(f['eski_ic']):>9} {str(f['yeni_ic']):>9} {str(f['d_ic']):>8} "
                  f"{str(f['eski_n']):>7} {str(f['yeni_n']):>7}  {anl}")
        if len(rapor["farklar"]) > max_satir:
            print(f"  ... +{len(rapor['farklar']) - max_satir} satır (tamamı için --json)")
    else:
        print("  fark YOK — defterdeki tablo bugünkü boru hattının ürettiğiyle birebir aynı")
    print(f"  ESKİ hüküm: {rapor['verdict']['eski']}")
    print(f"  YENİ hüküm: {rapor['verdict']['yeni']}")
    if not rapor.get("uygulandi"):
        print("  → yazmak için: python -m meridian.component_ic --uygula  (canlı worker DURMUŞ olmalı)")


def main(argv: list[str] | None = None) -> int:
    """CLI girişi: `component_ic.json`ı boru hattından yeniden üretir. Varsayılan KURU KOŞU — `--uygula`
    olmadan tek bayt yazılmaz, `--uygula` da canlı worker görünürken `--zorla` olmadan REDDEDİLİR
    (iki süreç aynı defteri iki farklı bar tabanıyla yazamasın). Dönüş: çıkış kodu."""
    import argparse
    import sys

    ap = argparse.ArgumentParser(
        prog="python -m meridian.component_ic",
        description="component_ic.json'ı güvensiz-dönem-dışlamalı boru hattından yeniden üretir")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşu)")
    ap.add_argument("--json", action="store_true", dest="as_json", help="raporu JSON olarak bas")
    ap.add_argument("--zorla", action="store_true",
                    help="canlı süreç görülse de yaz (riski sen alırsın)")
    a = ap.parse_args(argv)
    if a.uygula and not a.zorla:
        from .barrepair import _worker_running          # tek desen, çok tüketici (dbmigrate/ledgerstamp)
        if _worker_running():
            print("[component_ic] REDDEDİLDİ: canlı Meridian süreci görülüyor. Gecelik P5 zaten bu "
                  "tabloyu yazıyor — iki süreç aynı defteri iki farklı bar tabanıyla yeniden "
                  "yazabilir. Önce `./ops/stop-worker.sh`, sonra tekrar dene (ya da --zorla).",
                  file=sys.stderr)
            return 2
    rapor = yeniden_uret(uygula=a.uygula)
    if a.as_json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _fark_yazdir(rapor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
