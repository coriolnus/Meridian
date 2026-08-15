"""strategy.py — saf sinyal mantığı: yedi giriş kurulumunun değerlendirmesi ve kapalı-bar pozisyon yönetimi.

Ne yapar: OHLCV bar kuyruğundan giriş sinyali (EntrySignal) üretir ve açık pozisyonun bar-başına
yönetim kararını (ManageDecision) verir. Çekirdek kenar, doğrudan OHLCV'den hesaplanan
swing-momentum kırılımıdır — dış tarayıcı (FMP) olmadan da çalışır; tarayıcılar yalnız EK canlı
aday besler, giriş mantığını asla tanımlamaz. Yedi ekran her sembolde daima değerlendirilir;
yalnız ARMED_SETUPS üyeleri işlem adayı üretir, kalanlar uyuyan olarak karşı-olgusal ölçüme akar.
Dolum mekaniği burada değil broker.py'dedir.

Kilit girişler: evaluate_entry (breakout_vcp), evaluate_pullback, evaluate_momentum_burst,
evaluate_episodic_pivot, evaluate_exhaustion_hammer, evaluate_pead, evaluate_canslim; toplayıcılar
scan_all / scan_entry; yönetim manage_position (+ structural_stop, early_kill_pivot_exit); bileşen
puanları rvol_band_score / mom_rank_score / turnover_score; gölge eşikleri relax_for_near_miss.

Değişmezler: modül SAF'tır — I/O yok, saat okuma yok, ağ yok; index -1 DAİMA kapalı bardır. Canlı
ve backtest birebir AYNI fonksiyonları koşar; ayrışırlarsa her backtest sayısı yalan olur. Karar
kapalı bara, icra ertesi barın açılışına bağlıdır (ileri-dönük yok). Ölçülemeyen değer None kalır
(0 uydurulmaz); ölçülemeyen kapı girdisi elemedir; disiplin kapısının R:R tabanının
(DISCIPLINE_MIN_RR) altındaki plan hiç yüzeye çıkmaz.

Okur/yazar: çağıranın verdiği DataFrame dışında yalnız iki tarihe-çapalı determinist okuma yapar
(EDGAR hisse sayımı ve kazanç takvimi — depo-içi statik dosyalar, duvar saati yok; canlı ile
replay aynı dosyadan aynı sayıyı alır, saflık sözleşmesi bozulmaz). Hiçbir dosyaya yazmaz."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd

from . import indicators as ind
from .guard import DISCIPLINE_MIN_RR   # the strategy respects the discipline gate's R:R floor: never emit a plan it would always veto

PIVOT_LOOKBACK = 40
ATR_PERIOD = 14
RS_LOOKBACK = 63  # ~one quarter

# =================================================================================================
# SKOR ŞEKİLLERİ (2026-07-29) — ham bileşenden [0,100] puana dönüşüm.
# İKİSİ DE BU TURDA UYKUDA: karşılık gelen ağırlıklar (entry.w_rvolband / entry.w_mom) bounds.yaml'a
# VARSAYILAN 0.0 ile girdi (Batch L deseni). Ağırlık 0 iken bileşik skor BİREBİR eskisidir.
# =================================================================================================
# Üçgenin tepesi ve yarı-genişliği. Kanıt (g2_olcum 2026-07-29, cf katmanı, 20 bar ort. ileri getiri):
#   rvol 0-0.8   → -0.80%  (n=12, örneklem yok denecek kadar az)
#   rvol 0.8-1.5 → -0.52%  (n=269)   ← NEGATİF: "hacim biraz artmış" bir kırılım, kırılım değil
#   rvol 1.5-2.0 → +1.84%  (n=955)   ← TATLI NOKTA
#   rvol 2.0+    → +1.44%  (n=857)   ← hâlâ pozitif ama tepe değil → ilişki MONOTON DEĞİL
# Tepe 1.75 (kanıtlı bandın orta noktası), yarı-genişlik 0.75 → puan 1.0'da ve 2.5'te sıfırlanır.
# BİLİNEN MUHAFAZAKÂRLIK, YAZILI OLSUN: üçgenin SAĞ kolu kanıttan daha serttir — 2.0+ bandı hâlâ
# +1.44% getirmişken üçgen 2.5'ten sonra o barları 0 puanla cezalandırır. Bunun sebebi bandın
# üstünde tek bir ölçülmüş kova olması (2.0+ hepsini toplar) ve orada nerede bozulduğunun HENÜZ
# ÖLÇÜLMEMESİ; ölçülmemiş bir bölgede yumuşak azalış varsaymak, kanıtın söylemediğini söylemek olurdu.
RVOL_BAND_CENTER = 1.75
RVOL_BAND_HALFWIDTH = 0.75

# mom yüzdelik-rütbe penceresi. NEDEN 63 VE NEDEN KESİTSEL DEĞİL:
#   (a) KESİTSEL OLAMAZ. Bu fonksiyon saf ve TEK SEMBOLLÜDÜR; evrenin o günkü dağılımı burada yok —
#       kesitsel rütbe gerektiren `rs` bileşeni tam bu yüzden dışarıdan parametre olarak geliyor.
#       Bileşeni [0,100] ölçeğine oturtmak için sembolün KENDİ yakın geçmişindeki 12-1 okumalarına
#       göre yüzdelik rütbesi alınır: "bu isim kendi son çeyreğine göre ne kadar momentumlu?"
#   (b) 63 ÇÜNKÜ CANLI KUYRUK 340 BAR. mom_12_1 ilk değerini 253. barda verir; 340 barlık kuyrukta
#       en fazla 88 mom okuması vardır. Pencere 88'i aşsaydı canlı tarama (loop/cf_backfill/backtest,
#       hepsi tail(340)) ile TAM SERİYİ okuyan ölçüm yolları FARKLI sayı üretirdi — "canlı ve
#       backtest aynı fonksiyon" yasasının sessizce ihlali. 252+63=315 ≤ 340, 25 bar marjla.
#   (c) SINIR, YAZILI OLSUN: g2_olcum HAM mom_12_1'in IC'sini ölçtü. Yüzdelik-rütbe, pencere İÇİNDE
#       monoton bir dönüşümdür ama pencere bardan bara kaydığı için GLOBAL olarak monoton DEĞİLDİR;
#       yani bu puanın IC'si ölçülen IC ile aynı sayı olmak zorunda değildir. Bu bileşiğin ölçümü
#       kalem E'nin (aday profilleri) işidir ve ağırlığı 0 olduğu sürece hiçbir karara girmez.
MOM_RANK_WINDOW = 63

# =================================================================================================
# EDG-2026-016 TURNOVER — ÖLÇÜLMÜŞ YOLUN KABLOLANMASI. AĞIRLIK VARSAYILAN 0.0.
# =================================================================================================
# HÜKÜM (kart status bloğu, Rol-1 onaylı SUCCESS): turnover21 = medyan21(hacim)/as_of_shares(t)
# kesitte MONOTON bilgi taşıyor — üst %20 dilim evren-fazlası @10 +0,31% CI[+0,15,+0,49], @20
# +0,65% CI[+0,34,+1,01]; rvol20+mom21 kontrolünden sonra ARTIK üç yöntemle birden sağ (etkinin
# ~%85'i kontrolden sağ çıkıyor); q5 TEKDÜZE monoton; maliyet-sonrası @20 net +0,55%.
# ENTEGRASYON KARARI: ELLE AĞIRLIK YOK. Bileşen kablolanır, düğmesi bounds.yaml'a VARSAYILAN 0 ile
# iner, ölçüsünü ÖĞRENME DÖNGÜSÜ kendi verir (Batch L deseninin birebir aynısı).
#
# ÖLÇEK: ÖLÇÜLMÜŞ EVREN YÜZDELİKLERİ — UYDURMA EĞRİ DEĞİL. Kanıt kesitseldir ("o gün evrenin üst
# %20'si"), bu fonksiyon ise SAF ve TEK SEMBOLLÜDÜR: günün kesiti burada YOKTUR (kesitsel rütbe
# gerektiren `rs` tam bu yüzden dışarıdan parametre olarak gelir). Bu yüzden ham devir, ölçümün
# HAVUZLANMIŞ dağılımının yüzdeliklerine göre [1,99] puanına oturtulur; çapa noktaları ölçümün kendi
# çıktısıdır (sonuc_016.json → kesit_muhasebesi.turnover21_dagilimi, n=885.803 sembol-gün,
# 2009-08-04 → 2026-07-28, 242 sembol).
# ÜÇ SINIR, YAZILI OLSUN:
#   (1) BU BİR KESİT RÜTBESİ DEĞİL, SABİT KALİBRASYONDUR. Günün kesiti dar/geniş olduğunda gerçek
#       rütbe kayar; sabit çapa kaymaz. Dönüşüm MONOTON olduğu için kartın "q5 tekdüze monoton"
#       bulgusunun YÖNÜ korunur, ama bu puanın IC'si ölçülen IC ile aynı sayı olmak zorunda değildir.
#   (2) EKSTRAPOLASYON YOK: p01 altı 1, p99 üstü 99 puanla sınırlanır. Ölçülmemiş bölgede eğri
#       uydurmak, kanıtın söylemediğini söylemek olurdu.
#   (3) ÇAPALAR YAŞLANIR: evrenin likiditesi kaydıkça 2026-08-01 dağılımı eskir. Bu bir sabit değil
#       bir ÖLÇÜM ARTEFAKTIDIR ve tazelenmesi yeni bir ölçüm turunun işidir.
TURNOVER_PCTL_CAPA = ((0.001924, 1.0), (0.004442, 25.0), (0.006067, 50.0),
                      (0.008949, 75.0), (0.050849, 99.0))
_TO_LOGX = np.log(np.array([c[0] for c in TURNOVER_PCTL_CAPA], dtype=float))
_TO_PCT = np.array([c[1] for c in TURNOVER_PCTL_CAPA], dtype=float)


def turnover_score(turnover: Optional[float]) -> Optional[float]:
    """Ham devir → [1,99] puanı: ölçülmüş evren yüzdelikleri arasında log-doğrusal ara değer.

    Ölçülemeyen/0-altı girdi → None (uydurma yasağı). Log ölçek, dağılım sağa çarpık olduğu içindir
    (p50 0,0061 · p99 0,0508); dönüşüm monotondur, yani sıralamayı — kanıtın taşıdığı tek şeyi —
    korur."""
    if turnover is None or pd.isna(turnover):
        return None
    x = float(turnover)
    if x <= 0:
        return None
    return float(np.interp(np.log(x), _TO_LOGX, _TO_PCT))


def _turnover_now(df: pd.DataFrame, ticker: str) -> tuple[Optional[float], str]:
    """Son KAPALI barın devir hızı + ölçülemediyse NEDENİ. (değer, neden) — neden "" ise ölçüldü.

    SAFLIK DİKİŞİ, EMSALİYLE BİRLİKTE: bu modülün başlığı "PURE. No I/O" der ve o yasanın GEREKÇESİ
    aynı cümlede yazılıdır — canlı ile backtest AYNI fonksiyonu koşmalı, ayrışırlarsa her backtest
    sayısı yalan olur. Buradaki okuma o gerekçeyi İHLAL ETMEZ: `research/edgar_facts/` deponun içinde
    STATİK bir dosyadır, okuma (ticker, tarih) çiftinin DETERMİNİST bir fonksiyonudur ve duvar
    saatine bakmaz; canlı yol da replay yolu da aynı dosyadan aynı as-of kuralıyla aynı sayıyı alır.
    EMSAL AYNI DOSYADA: `evaluate_pead` tam olarak bu biçimde `earnings.days_since_report(ticker,
    last_date)` çağırır — tarihe çapalı, dosya-destekli, PIT bir okuma. İkinci bir desen icat
    edilmedi.

    TARİH SÜTUNU YOKSA OKUMA DA YOK: as-of bir okuma tarihsiz yapılamaz ve "bugünü" varsaymak
    (duvar saati) tam da saflık yasasının yasakladığı şey olurdu — sentetik/tarihsiz çerçevelerde bileşen
    dürüstçe ölçülemez kalır."""
    if "date" not in df.columns:
        return None, "tarih_yok"
    last_date = str(df["date"].iloc[-1])[:10]
    from .adapters import edgar_shares as _es           # yerel ithalat: emsal `earnings` (bkz. yukarı)
    sh, neden = _es.as_of_shares_detay(ticker, last_date)
    if sh is None:
        return None, (neden or "olculemedi")
    v = ind.turnover21(df["volume"], sh).iloc[-1]
    if pd.isna(v):
        # Pay tarafı: 21 barlık medyan penceresi dolmadıysa ya da FİZİKSEL BEKÇİ (devir>1) kapattıysa.
        return None, ("fiziksel_bekci_veya_isinma")
    return float(v), ""


def _align_index_close(df: pd.DataFrame, index_close: pd.Series) -> pd.Series:
    """Endeks serisini `bars`ın SATIR EKSENİNE oturtur (2026-07-29).

    Tarama yolundaki `bars` KONUM indekslidir ve tarihi bir SÜTUNDA taşır (loop/backtest hepsi
    `.reset_index()` ile üretir); endeks serisi ise doğal olarak TARİH indekslidir. İkisi doğrudan
    karşılaşırsa etiketler hiç örtüşmez — `indicators.residual_momentum` bu durumu artık ValueError
    ile bildirir, ama doğru çözüm hatayı yakalamak değil hizayı BURADA kurmaktır: tarih sütunu
    hangi konvansiyonda ise bilen taraf burasıdır.

    SINIR, YAZILI OLSUN: endeks getirisi hizalamadan SONRA hesaplanır, yani sembolün bar takvimi
    üzerinden. Sembolde eksik bir seans varsa o günün endeks getirisi komşu güne katlanır; tam
    seriyi okuyan `component_ic` yolunda (iki taraf da tarih indeksli) böyle bir katlanma yoktur.
    Bugün hiçbir çağıran endeks geçirmediği için bu fark canlıda hiçbir sayıyı etkilemez."""
    if "date" in df.columns and isinstance(index_close.index, pd.DatetimeIndex):
        out = index_close.reindex(pd.DatetimeIndex(pd.to_datetime(df["date"])))
        out.index = df.index
        return out
    return index_close


def rvol_band_score(rvol: Optional[float]) -> Optional[float]:
    """rvol → [0,100] BANT puanı: 100·max(0, 1-|rvol-1.75|/0.75). Ölçülemeyen girdi → None.

    Neden üçgen ve neden monoton bir eğri değil: yukarıdaki bant tablosu. `vol_score`un
    `min(vr/3, 1)` biçimi "ne kadar çok hacim o kadar iyi" der; ölçüm bunun 2.0 üstünde YANLIŞ
    olduğunu söylüyor. Yeni bileşen eskisini SİLMEZ — yanında, ayrı ağırlıkla durur ki hangisinin
    doğru olduğunu kapı ölçsün."""
    if rvol is None or pd.isna(rvol):
        return None
    return 100.0 * max(0.0, 1.0 - abs(float(rvol) - RVOL_BAND_CENTER) / RVOL_BAND_HALFWIDTH)


def mom_rank_score(mom_series: pd.Series) -> Optional[float]:
    """Son barın mom_12_1 değerinin KENDİ son 63 okuması içindeki yüzdelik rütbesi → [0,100].

    Pencere dolmamışsa (ya da içinde NaN varsa) None — yarım pencereyle hesaplanmış bir "yüzdelik"
    ölçülmüş gibi raporlanmaz (trend_template dersi). Yalnız SON barın penceresine
    bakar: geçmiş barların rütbesi bu kararı ilgilendirmez ve tam seri üzerinde yuvarlanan bir
    rütbe hesabı her sembolde 340 pencere kurardı."""
    if mom_series is None or len(mom_series) < MOM_RANK_WINDOW:
        return None
    win = mom_series.iloc[-MOM_RANK_WINDOW:]
    if int(win.notna().sum()) < MOM_RANK_WINDOW:
        return None
    return float(win.rank(pct=True).iloc[-1]) * 100.0


# =================================================================================================
# ÇIKIŞ REFORMU — YAPI-TABANLI STOP + ERKEN İTLAF.
# İKİSİ DE BU TURDA UYKUDA (bounds.yaml varsayılanları 0). Batch L deseni: satır bounds'ta olduğu için
# kum havuzunda aranabilir, strategy.yaml onları taşımadığı için canlı davranış BİREBİR eskisidir.
#
# NEDEN ÇIKIŞ TARAFI: şelale ölçümü sinyalin +0.965R ürettiğini, çıkışın -0.985R'sini geri
# İADE ETTİĞİNİ gösterdi — stop verimi -%76, stop_gap -%209; time_stop TEK güçlü bileşen (+%50).
# Yani kalan kâr çıkış tarafında kayboluyor ve reformun yeri burasıdır.
# =================================================================================================


def structural_stop(entry_ref: float, pivot: float, atr: float, params: dict) -> float:
    """Kurulumun sert stop seviyesi. TEK KAYNAK: `stop_mode` knob'unun okunduğu YER burasıdır.

    `stop_mode` = 0 (VARSAYILAN, bugünkü yasa): stop = referans kapanış − `stop_loss_atr_mult`·ATR.
    `stop_mode` = 1 (pivot_alti): stop = PİVOT − `stop_buffer_atr`·ATR — yani seviye artık VOLATİLİTEDEN
    değil YAPIDAN türer: "kırılan direnç geri alındıysa tez öldü". Tampon, pivotun tam üstündeki
    gürültü dokunuşlarının stopu tetiklemesini engeller ve ATR birimindedir ki eşik sembol-bağımsız
    kalsın (yüzde tampon, düşük volatiliteli bir isimde çok geniş / yüksek volatilitede çok sıkı olurdu).

    R-NÖTRLÜK KORUNUR — YAZILI OLSUN: boyutlandırma DEĞİŞMEZ. `broker.size_position` aynen
    `risk_dolar / (giriş_fill − stop)` hesaplar, yani stop nereye konursa konsun pozisyonun taşıdığı
    RİSK 1R'dir; değişen tek şey o 1R'nin FİYAT cinsinden genişliği (ve dolayısıyla hisse adedi).
    Bu yüzden `stop_mode=1` "daha az riskli" bir mod DEĞİL, riski BAŞKA BİR YERE demirleyen bir moddur.

    AMA BİR KARIŞTIRICI VAR VE ÖLÇÜLDÜ — YAZILI OLSUN: R-nötrlük FORMÜL düzeyinde
    korunur, İCRA düzeyinde korunmaz. `broker.fill_entry`ın `MAX_NOTIONAL_PCT` (=%25 sermaye) tavanı
    adet üzerinden bağladığı için, stop yakınlaştıkça tavan devreye girer ve `risk_dollars` AŞAĞI
    yeniden türetilir. Cebir: tavan, stop mesafesi fiyatın `RISK_PCT_PER_R/MAX_NOTIONAL_PCT` = %4'ünden
    YAKIN olduğunda bağlar. Ölçüldü (sermaye 100k, fiyat 100): stop 96 → 1.00R · stop 98 → 0.50R ·
    stop 99 → 0.25R. Tipik ATR fiyatın %1.5-2.5'i olduğundan `stop_mode=0`ın 2·ATR stopu (%3-5) SINIRDA
    gezinir, `stop_mode=1`in pivot−0.5·ATR stopu (%0.5-1.5) ise TAVANI HER ZAMAN bağlar.

    SONUÇ, KAPI OKURLARINA: `stop_mode=1`in ölçülen ΔS'i saf bir ÇIKIŞ-KALİTESİ etkisi DEĞİLDİR —
    içine sistematik bir POZİSYON KÜÇÜLTMESİ karışmıştır (yarım ya da çeyrek R'lik işlemler). Düşüşü
    ve kuyruğu iyileştirmesi bu yüzden BEKLENEN bir yan etkidir ve "yapı-tabanlı stop işe yarıyor"
    diye okunamaz. Ayrıştırma yolu: `MAX_NOTIONAL_PCT`i ölçüm süresince gevşetmek AYRI bir tur
    (broker'ın sermaye-koruma tavanı bir çıkış hipotezi için gevşetilemez), ya da dolar-bazlı mercek
    (büyüklük yasası revizyonu). Bu tur SAYIYI ölçer ve karıştırıcıyı ADIYLA raporlar.

    SINIR, YAZILI OLSUN: yalnız `evaluate_entry` (breakout_vcp) bu fonksiyonu çağırır. Diğer altı
    kurulumun stopu ZATEN yapısaldır ve her biri KENDİ yapı çizgisine demirlidir (burst = patlama
    barının dibi, EP/PEAD = boşluk günü ya da kırmızı mumun dibi, hammer = çekiç dibi); orada
    `pivot` alanı bir direnç seviyesi değil (sma20 / önceki kapanış / 52-hafta zirvesi) ve
    "pivot − tampon" o nesnelerde AYNI cümleyi kurmaz. Kanıt tabanı da (çıkış şelalesi) kırılım
    işlemlerinden geliyor. Kapsamı genişletmek ayrı bir ölçüm turudur."""
    if int(_f(params, "stop_mode", 0)) == 1 and pivot > 0:
        return pivot - _f(params, "stop_buffer_atr", 0.5) * atr
    return entry_ref - _f(params, "stop_loss_atr_mult", 2.0) * atr


def early_kill_pivot_exit(bars: pd.DataFrame, position: dict, params: dict, bars_held: int) -> bool:
    """ERKEN İTLAF, PİVOT-ALTI BİÇİMİ — TEK YASA, İKİ TÜKETİCİ.

    Hüküm: pozisyonun gördüğü ilk `exit.early_kill_bars` kapanıştan birinde kapanış PİVOTUN ALTINA
    düştüyse tez ölmüştür → çıkış. Bu fonksiyon yalnız BAYRAK döndürür; icra `manage_position`ın
    sözleşmesiyle ERTESİ BARIN AÇILIŞINDA olur (ileri-dönük yok: karar kapalı bara, icra sonraki
    açılışa). `exit.early_kill_pivot` = 0 → hiç çalışmaz (varsayılan).

    ÇİFT UYGULAMA YOKTUR: kural `manage_position` içinden çağrılır ve `manage_position`ı İKİ tüketici
    çağırır — `backtest.replay` (CLOSE(D) döngüsü) ve `loop.daily_cycle` (canlı CLOSE(D) döngüsü),
    ikisi de aynı imza + aynı rejim-çözümlü `eff` ile. Yani yasa tek yerde yazılıdır ve iki motorun
    ayrışması yapısal olarak imkânsızdır. Canlı yola AYRI bir çıkış kuralı EKLENMEDİ.

    NEDEN "PİVOT-ALTI" VE NEDEN "ARALIĞIN ALT YARISI" DEĞİL: iki biçim önerilmişti; ön-ölçüm
    (2026-07-29, cf n≈2100) bunlardan BİRİNİ ÇÜRÜTTÜ — kapanışın bar aralığı içindeki
    KONUMU sürekli sinyal olarak SIFIR bilgi taşıyor (IC ≈ 0, her iki katmanda). Ölçüm YALNIZ
    pivot-altı kapanışı destekliyor (@5 bar −0.74% vs pivot-üstü +0.32%, n=302; @20 barda kısmen
    toparlıyor). Bu yüzden burada TEK biçim var: çürütülmüş biçim kod olarak da yazılmadı.

    PENCERE NEDEN VAR: kanıt KISA ufuklu ve @20'de zayıflıyor. Penceresiz bir kural (her barda
    pivot-altı kapanış → çık) uzun süren bir kazananı, aylar sonra pivotu bir gün delip geri alan bir
    salınımda keserdi — trail'in işini ikinci kez, daha kaba yapmak olurdu. Varsayılan 1 = tasarımın
    düz okunuşu: pozisyonun GÖRDÜĞÜ ilk kapanış (giriş barının kapanışı; sinyal barının kapanışı
    tanım gereği pivotun ÜSTÜNDEDİR — `c_prev < pivot <= c_now` — yani orada sınanacak bir şey yok).

    PİVOT YOKSA ÇIKIŞ DA YOKTUR: `position["pivot"]` eksik/ölçülemez (None, NaN, ≤0) ise False.
    Motorun ELEME yasası ölçülemeyen GİRİŞ kapısı girdisini eler; bir ÇIKIŞTA aynı refleks tersine
    çalışırdı — ölçülemeyen bir seviyeden UYDURMA bir çıkış üretmek olurdu.

    KABLO ARTIK ÜÇ MOTORDA DA VAR. Buraya kadar "canlı planlar bu alanı
    taşımıyor, yani bayrak açılsa bile canlıda ateşlemez" yazıyordu: replay/gölge ölçerken canlının
    YAPISAL olarak ateşleyemediği bir düğme, terfi ettiğinde canlıda sessiz no-op olurdu (sahte
    terfi). Kopukluk İKİ yerdeydi ve ikisi de kapandı — `loop.py` pivotu `entry_law` yan tablosunda
    taşıyıp `fill_entry(pivot=...)`e geçiriyor (→ `Position.pivot`) ve `manage_position`a verdiği
    sözlüğe `"pivot"` koyuyor. Ölçülemeyen pivot yine 0.0/None kalır ve bu dal dürüstçe False
    döner — değişen tek şey, artık ölçülebildiğinde ateşleyebilmesi."""
    if int(_f(params, "exit.early_kill_pivot", 0)) != 1:
        return False
    window = int(_f(params, "exit.early_kill_bars", 1))
    if not (1 <= bars_held <= window):
        return False
    pivot = position.get("pivot")
    if pivot is None:
        return False
    try:
        pv = float(pivot)
    except (TypeError, ValueError):
        # sessiz-yutma: dönen False'un KENDİSİ cevaptır — sayıya çevrilemeyen bir pivot "ölçülemedi"
        # demektir ve ölçülemeyen bir seviyeden çıkış üretmek uydurma olurdu. Bu dal bir arızayı
        # yutmuyor, kuralın "pivot yoksa çıkış da yok" hükmünü uyguluyor (bkz. docstring son paragraf).
        return False
    if not (pv > 0) or pd.isna(pv):
        return False
    return float(bars["close"].iloc[-1]) < pv


@dataclass(frozen=True)
class EntrySignal:
    """Sinyal barında üretilen GİRİŞ SİNYALİ — donmuş (frozen) kayıt: pivot/stop/ATR/skor ve skor
    bileşenleri. Ölçülemeyen bileşen None kalır (0.0 DEĞİL — uydurma yasağı)."""
    ticker: str
    setup: str
    entry_trigger: float      # reference price at the signal bar's close
    pivot: float
    stop: float
    atr: float
    rs_rating: int
    score: int
    profit_target: float
    size_r: float
    r_per_share: float
    notes: str
    # --- SKOR BİLEŞENLERİ: DEFTERDE ALAN, METİNDE DEĞİL (2026-07-29) ------------------------------
    # `component_ic` modül başlığının 1. tasarım kararı şunu tespit etmişti: tt/vr/prox hiçbir deftere
    # ALAN olarak yazılmıyor, yalnız `notes` METNİNİN içinde ("prox=1.2% vr=2.1 tt=0.83") duruyor ve
    # orada da 313 satırın 13'ünde kayıp. Sonuç: bileşen ölçümü ya bir string'i regex'le ayrıştırmak
    # ya da barlardan yeniden hesaplamak zorunda kaldı. Yeni bileşenlerde o hata TEKRARLANMAZ —
    # sinyal barında hesaplanan değer, hesaplandığı yerde alan olarak yazılır ve gelecekteki ölçüm
    # onu regex'siz okur. Ölçülemeyen bileşen None kalır (0.0 DEĞİL — uydurma yasağı).
    rvol20: Optional[float] = None      # volume / SMA20(volume) — ham (bant dönüşümü skor tarafında)
    mom_12_1: Optional[float] = None    # close[t-21]/close[t-252]-1
    rmom: Optional[float] = None        # artık 12-1 momentum; endeks serisi verilmezse None
    # medyan21(hacim)/as_of_shares(t) — HAM oran (yüzdelik puanı skor
    # tarafında). Aynı gerekçe: sinyal barında hesaplanan değer, hesaplandığı yerde ALAN olarak
    # yazılır ki gelecekteki ölçüm onu regex'siz okusun. Ölçülemeyen hücre None (0.0 DEĞİL).
    turnover21: Optional[float] = None

    def as_row(self) -> dict:
        """Sinyali deftere yazılacak düz sözlüğe çevirir (fiyat alanları yuvarlı). Bileşen alanları HER
        satırda bulunur; ölçülemeyen None olarak yazılır — "eksik alan" ile "ölçülemedi" karışmasın."""
        return {
            "ticker": self.ticker, "setup": self.setup, "pivot": round(self.pivot, 4),
            "stop": round(self.stop, 4), "atr": round(self.atr, 4), "rs_rating": self.rs_rating,
            "score": self.score, "entry_trigger": round(self.entry_trigger, 4),
            "profit_target": round(self.profit_target, 4), "size_r": self.size_r,
            "r_per_share": round(self.r_per_share, 4), "notes": self.notes,
            # ÜÇ ALAN HER SATIRDA VAR, ölçülemediğinde None. Alanın koşullu var/yok olması, okuyan
            # tarafta "eksik alan" ile "ölçülemedi"yi ayırt edilemez yapardı.
            "rvol20": None if self.rvol20 is None else round(self.rvol20, 6),
            "mom_12_1": None if self.mom_12_1 is None else round(self.mom_12_1, 6),
            "rmom": None if self.rmom is None else round(self.rmom, 6),
            "turnover21": None if self.turnover21 is None else round(self.turnover21, 8),
        }


def _f(params: dict, key: str, default: float) -> float:
    """Parametre sözlüğünden bir düğmeyi float olarak okur; anahtar yoksa verilen varsayılana düşer."""
    return float(params.get(key, default))


def evaluate_entry(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                   ticker: str = "?", index_close: Optional[pd.Series] = None) -> Optional[EntrySignal]:
    """Decide whether the last CLOSED bar is a fresh breakout entry. Returns None if no setup.
    `bars` must be sorted ascending with columns open,high,low,close,volume; -1 is the last close.

    `index_close` (2026-07-29): artık momentum için endeks kapanış serisi. VERİLMEZSE `rmom`
    alanı None kalır — bugün hiçbir çağıran vermiyor (scan_all/scan_entry imzası değişmedi, çünkü
    orada YEDİ kurulum aynı imzayla çağrılıyor ve yalnız birine ek argüman geçirmek o döngüyü
    özel-durumlu hâle getirirdi). rmom bu turda skora GİRMEDİĞİ için bu bir eksiklik değil, bilinçli
    bir dikiş yeri: bileşen `component_ic`de tam seri üzerinden ölçülür; canlı yolda ölçmek için
    (340 barlık kuyruk zaten ısınmasını doldurmuyor, bkz. indicators.residual_momentum) önce kuyruk
    uzunluğu sorusu açılmalı ve o ayrı bir turdur."""
    if bars is None or len(bars) < PIVOT_LOOKBACK + 3:
        return None
    df = bars
    close = df["close"]

    pivot_series = ind.pivot_high(df["high"], PIVOT_LOOKBACK, exclude_recent=1)
    base_low_series = df["low"].shift(1).rolling(PIVOT_LOOKBACK, min_periods=PIVOT_LOOKBACK // 2).min()
    vr_series = ind.volume_ratio(df["volume"], 50)
    atr_series = ind.atr(df, ATR_PERIOD)
    tt_series = ind.trend_template(df)

    pivot = pivot_series.iloc[-1]
    base_low = base_low_series.iloc[-1]
    c_now = close.iloc[-1]
    c_prev = close.iloc[-2]
    vr = vr_series.iloc[-1]
    a = atr_series.iloc[-1]
    tt = tt_series.iloc[-1]

    if any(pd.isna(x) for x in (pivot, c_now, c_prev, vr, a, tt)) or a <= 0 or pivot <= 0:
        return None

    # --- fresh breakout: prior close below pivot, current close at/above it ---
    if not (c_prev < pivot <= c_now):
        return None

    # --- higher-timeframe confirmation: only take breakouts with the weekly trend up ---
    if not ind.weekly_uptrend(df):
        return None

    proximity_pct = (c_now - pivot) / pivot * 100.0  # how extended above the pivot

    # --- gates from params (all inside bounds.yaml) ---
    rs_min = _f(params, "entry.rs_rating_min", 70)
    prox_max = _f(params, "entry.pivot_proximity_pct", 2.0)
    vr_min = _f(params, "entry.min_volume_ratio", 1.5)
    score_min = _f(params, "entry.min_score", 60)

    if rs_rating_value < rs_min:
        return None
    if vr < vr_min:
        return None
    # --- Skor bileşenleri: BURADA hesaplanır, BURADA deftere yazılır (bkz. EntrySignal alanları) ---
    rvol_now = ind.rvol20(df["volume"]).iloc[-1]
    rvol_val = None if pd.isna(rvol_now) else float(rvol_now)
    # RVOL TABAN FİLTRESİ (kalem C) — 0.0 = KAPALI (varsayılan, bu turda canlı davranış değişmez).
    # Kanıtı 0.8-1.5 bandının NEGATİF ortalama getirisidir (-0.52%, n=269 @20 bar): "hacim biraz
    # artmış" bir kırılım masada para bırakmıyor, para KAYBETTİRİYOR. Açılması yine kapıdan geçecek.
    # ÖLÇÜLEMEYEN rvol FİLTREYİ GEÇEMEZ: eşik açıkken NaN'ı geçirmek, kapıyı "kanıt yoksa serbest"
    # diye okumak olurdu; motorun her yerinde ölçülemeyen kapı girdisi elemedir (vr/tt emsali).
    min_rvol = _f(params, "entry.min_rvol", 0.0)
    if min_rvol > 0 and (rvol_val is None or rvol_val < min_rvol):
        return None
    if proximity_pct > prox_max:   # too extended past the pivot — don't chase
        return None
    # extension-from-50SMA climax filter: reject entries that are already stretched far above the
    # 50-day mean (distance in ATR units) — buying a climax is the classic momentum trap. 0 = off (default).
    max_ext = _f(params, "entry.max_ext_atr", 0.0)
    if max_ext > 0:
        sma50 = close.rolling(50).mean().iloc[-1]
        if not pd.isna(sma50) and sma50 > 0 and (c_now - sma50) / a > max_ext:
            return None
    # dual-horizon RS / acceleration gate: only buy names CLIMBING the leaderboard — the short
    # (21d) momentum must at least match the long (63d) momentum's pro-rata pace. 0 = off (default).
    if int(_f(params, "entry.rs_dual_horizon", 0)) == 1 and len(close) > 64:
        mom_short = c_now / close.iloc[-22] - 1.0
        mom_long = c_now / close.iloc[-64] - 1.0
        if mom_short * 3.0 < mom_long:      # short-horizon pace decelerating vs long-horizon → skip
            return None

    # --- composite score in [0,100] ---
    # bileşen ağırlıkları artık tunable (bounds.yaml entry.w_*) — seçilim fonksiyonunun kendisi
    # öğrenme döngüsüne açıldı. Toplama normalize edildiği için ağırlık oynadıkça ölçek [0,100] kalır;
    # varsayılanlar eski sabitlerin birebir aynısı (0.35/0.30/0.20/0.15) → temel davranış değişmez.
    prox_score = 100.0 * (1.0 - min(proximity_pct / prox_max, 1.0)) if prox_max > 0 else 0.0
    vol_score = 100.0 * min(vr / 3.0, 1.0)
    w_rs = _f(params, "entry.w_rs", 0.35); w_tt = _f(params, "entry.w_tight", 0.30)
    w_vol = _f(params, "entry.w_vol", 0.20); w_px = _f(params, "entry.w_prox", 0.15)
    w_sum = max(w_rs + w_tt + w_vol + w_px, 1e-9)
    score_num = (w_rs * rs_rating_value + w_tt * (tt * 100.0)
                 + w_vol * vol_score + w_px * prox_score)
    score_den = w_sum
    # --- EK BİLEŞENLER (2026-07-29): SIFIR-ETKİLİ. Ağırlık 0 iken ne pay ne payda değişir, yani skor
    # yukarıdaki dört terimli ifadenin BİREBİR kendisidir (çivi testi: test_score_rebuild_v115).
    # Bileşen değerleri ağırlıktan BAĞIMSIZ olarak hesaplanır ve deftere yazılır — ölçüm ancak
    # kayıt varsa mümkündür ve kaydı ağırlığa bağlamak, "önce aç sonra ölç" kısır döngüsü olurdu.
    mom_series = ind.mom_12_1(close)
    mom_now = mom_series.iloc[-1]
    mom_val = None if pd.isna(mom_now) else float(mom_now)
    rmom_now = (ind.residual_momentum(close, _align_index_close(df, index_close)).iloc[-1]
                if index_close is not None else None)
    rmom_val = None if (rmom_now is None or pd.isna(rmom_now)) else float(rmom_now)
    rvb_score = rvol_band_score(rvol_val)
    mom_score = mom_rank_score(mom_series)
    # ÖLÇÜLEMEYEN AĞIRLIKLI BİLEŞEN = KURULUM YOK, "kalanlara göre normalize et" DEĞİL. İkincisi,
    # ısınması dolmamış bir sembolün skorunu üç bileşenden hesaplayıp dört bileşenlik bir sayı gibi
    # raporlamak olurdu — trend_template'in daha önce düzeltilen hatasının aynısı. Ağırlık 0
    # iken bu dal HİÇ çalışmaz, yani bugün tek bir sembolü bile elemez.
    w_rvb = _f(params, "entry.w_rvolband", 0.0)
    w_mom = _f(params, "entry.w_mom", 0.0)
    if w_rvb > 0:
        if rvb_score is None:
            return None
        score_num += w_rvb * rvb_score
        score_den += w_rvb
    if w_mom > 0:
        if mom_score is None:
            return None
        score_num += w_mom * mom_score
        score_den += w_mom
    # --- TURNOVER TERİMİ: SIFIR-ETKİLİ. `entry.w_turnover` varsayılanı 0.0
    # olduğu sürece ne pay ne payda değişir; skor yukarıdaki ifadenin BİREBİR kendisidir (çivi:
    # test_turnover_kablolama_v149). Değer ağırlıktan BAĞIMSIZ hesaplanır ve deftere yazılır.
    #
    # FAIL-OPEN VE NEDEN KOMŞUSUNDAN FARKLI — BEYAN. Üstteki iki dal ölçülemeyen bileşende
    # `return None` der ("kurulum yok"); bu dal DEMEZ, ölçülemeyen turnover'ı terimi HİÇ EKLEMEDEN
    # geçer (pay da payda da dokunulmaz, yani skor kalan bileşenlerin kendi ölçeğinde kalır). Fark
    # keyfi değil, girdinin CİNSİNDEN gelir: rvb/mom kurulumun ZATEN istediği barlardan hesaplanır —
    # ölçülemiyorsa ısınma dolmamıştır ve orada gerçekten kurulum yoktur. Turnover'ın paydası ise
    # DIŞ ve statik bir dosyadır (`research/edgar_facts/`, aylık tazelenir); o dosyanın yokluğu bir
    # PİYASA olgusu değil bir ALTYAPI olgusudur. Aynı refleksi burada da uygulamak, dosya
    # tazelenmediği ya da sembol EDGAR kapsamında olmadığı gün motoru TOPTAN sustururdu — kimsenin
    # seçmediği bir "veri kesintisi → işlem durdu" bağlantısı. Bedeli yazılı olsun: knob açıkken
    # kapsam dışındaki semboller turnover'sız skorlanır, yani o gün iki farklı ölçekte skor üretilir;
    # bu SESSİZ DEĞİLDİR — sebep sayacı `adapters.edgar_shares.okuma_raporu()`ndan gecelik
    # `component_ic` olayına ve `component_ic.json` → `turnover_kaynak` alanına düşer.
    # SAYACIN KAPSAMI TAM OLARAK YAZILI OLSUN: o sayaç PAYDA okumasının sebeplerini taşır (dosya
    # yok / sembol EDGAR kapsamında değil / dosyalama yok / bayat seri / ölçek hatası) ve kapsam
    # dışı sembollerin ADINI da (`kapsam_disi_sembol`) — sayı tek başına eyleme dönüşmez. Payda
    # okunup da ORAN düşerse (fiziksel bekçi: devir>1, ya da 21 barlık medyan penceresi dolmamışsa)
    # bu sayaçta görünmez; o vaka defter satırında `turnover21: null` olarak ve gecelik tablonun
    # turnover hücrelerindeki `n` düşüşünde görünür. İki kanal iki farklı olguyu sayar; birini
    # ötekinin adıyla raporlamak, kaynağı bozuk olanla oranı imkânsız olanı karıştırmak olurdu.
    to_val = _turnover_now(df, ticker)[0]      # NEDEN alanının okuyucusu: testler + sayaç raporu
    to_score = turnover_score(to_val)
    w_to = _f(params, "entry.w_turnover", 0.0)
    if w_to > 0 and to_score is not None:
        score_num += w_to * to_score
        score_den += w_to
    score = int(round(score_num / score_den))
    if score < score_min:
        return None

    stop_mult = _f(params, "stop_loss_atr_mult", 2.0)
    pt_cap = _f(params, "exit.profit_target_r", 2.5)   # now the MAX R:R cap, not a fixed multiple
    size_r = _f(params, "position_size_r", 1.0)

    stop = structural_stop(float(c_now), float(pivot), float(a), params)
    r_per_share = c_now - stop
    if r_per_share <= 0:
        return None
    # measured-move target: project the consolidation base height (pivot - base_low) up from entry.
    # R:R now VARIES per plan (deep bases -> larger targets), capped at pt_cap so it can't run away and
    # floored so a valid base still produces a target. The discipline gate flags/kills shallow-base low-R:R.
    base_height = (pivot - base_low) if (not pd.isna(base_low) and base_low > 0) else r_per_share
    measured_rr = base_height / r_per_share
    rr = min(measured_rr, pt_cap)
    if rr < DISCIPLINE_MIN_RR:              # a shallow-base low-reward breakout the gate would veto → don't surface it
        return None
    target = c_now + rr * r_per_share

    # conviction sizing: scale size by setup quality (score), from 0.6x to 1.0x of position_size_r.
    # Still capped at the immutable max_position_r downstream in guard/backtest — never exceeds it.
    conviction = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    size_final = round(size_r * conviction, 3)

    return EntrySignal(
        ticker=ticker, setup="breakout_vcp", entry_trigger=float(c_now), pivot=float(pivot),
        stop=float(stop), atr=float(a), rs_rating=int(rs_rating_value), score=score,
        profit_target=float(target), size_r=float(size_final), r_per_share=float(r_per_share),
        # `notes` DEĞİŞMEDİ: yeni bileşenler metne EKLENMEZ, alan olarak gider (bkz. EntrySignal).
        notes=f"prox={proximity_pct:.2f}% vr={vr:.2f} tt={tt:.2f} rr={rr:.2f} conv={conviction:.2f}",
        rvol20=rvol_val, mom_12_1=mom_val, rmom=rmom_val, turnover21=to_val,
    )


def evaluate_pullback(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                      ticker: str = "?") -> Optional[EntrySignal]:
    """Second setup: a leader in an established uptrend that pulled back to its RISING 20-day average
    and is turning back up. Complements the breakout — catches strong names between breakouts. Pure,
    closed bars only."""
    if bars is None or len(bars) < 60:
        return None
    df = bars
    close = df["close"]
    sma20 = ind.sma(close, 20)
    sma50 = ind.sma(close, 50)
    atr_s = ind.atr(df, ATR_PERIOD)
    tt = ind.trend_template(df).iloc[-1]
    c, cprev = close.iloc[-1], close.iloc[-2]
    s20, s20_prev, s50 = sma20.iloc[-1], sma20.shift(20).iloc[-1], sma50.iloc[-1]
    a = atr_s.iloc[-1]
    if any(pd.isna(x) for x in (s20, s20_prev, s50, a, tt)) or a <= 0 or s20 <= 0:
        return None
    if not (tt >= 0.6 and s20 > s20_prev and c > s50):   # established uptrend, rising 20-sma, above 50-sma
        return None
    dist20 = (c - s20) / s20 * 100.0
    if not (-4.0 <= dist20 <= 4.0) or c <= cprev:         # near the 20-sma AND turning up
        return None
    if not ind.weekly_uptrend(df):
        return None
    rs_min = _f(params, "entry.rs_rating_min", 70)
    score_min = _f(params, "entry.min_score", 60)
    if rs_rating_value < rs_min:
        return None
    prox = 100.0 * (1.0 - min(abs(dist20) / 4.0, 1.0))
    score = int(round(0.40 * rs_rating_value + 0.35 * (tt * 100.0) + 0.25 * prox))
    if score < score_min:
        return None
    stop_mult = _f(params, "stop_loss_atr_mult", 2.0)
    pt_cap = _f(params, "exit.profit_target_r", 2.5)
    size_r = _f(params, "position_size_r", 1.0)
    stop = min(s20, c) - stop_mult * a
    r_per_share = c - stop
    if r_per_share <= 0:
        return None
    swing_high = df["high"].rolling(20).max().iloc[-1]
    base_height = max(swing_high - s20, r_per_share)
    rr = min(base_height / r_per_share, pt_cap)
    # A pullback that enters AT the 20-sma with a full ATR-width stop rarely has 2R of room back to the
    # prior high, so its measured R:R lands ~1R. Tightening the stop to force 2R was measured to HALVE the
    # OOS edge (whipsaw stop-outs) — the setup has no honest 2:1 here. So rather than ship a worse strategy
    # OR flood the board with plans the discipline gate vetoes 100% of the time, we simply don't surface a
    # sub-floor plan. The setup stays honestly dormant until it genuinely qualifies. (See also evaluate_entry.)
    if rr < DISCIPLINE_MIN_RR:
        return None
    target = c + rr * r_per_share
    conviction = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    return EntrySignal(
        ticker=ticker, setup="pullback", entry_trigger=float(c), pivot=float(s20), stop=float(stop),
        atr=float(a), rs_rating=int(rs_rating_value), score=score, profit_target=float(target),
        size_r=float(round(size_r * conviction, 3)), r_per_share=float(r_per_share),
        notes=f"pullback dist20={dist20:.1f}% rr={rr:.2f}")


def evaluate_momentum_burst(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                            ticker: str = "?") -> Optional[EntrySignal]:
    """Third setup — Stockbee-style MOMENTUM BURST: a >=4% up-day (range expansion) on above-average volume,
    in an established uptrend, for a short 3-5 day swing. Pure OHLCV (no key needed). Complements breakout +
    pullback so the deterministic scan genuinely evaluates more than one screener. Closed bars only."""
    if bars is None or len(bars) < 60:
        return None
    df = bars
    close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
    sma50 = ind.sma(close, 50)
    atr_s = ind.atr(df, ATR_PERIOD)
    tt = ind.trend_template(df).iloc[-1]
    c, cprev = close.iloc[-1], close.iloc[-2]
    a, s50 = atr_s.iloc[-1], sma50.iloc[-1]
    if any(pd.isna(x) for x in (a, s50, tt)) or a <= 0 or cprev <= 0:
        return None
    day_pct = (c - cprev) / cprev
    vol20 = vol.iloc[-21:-1].mean()
    vol_surge = (vol.iloc[-1] / vol20) if vol20 > 0 else 0.0
    # the burst: >=4% up-day on >=1.5x average volume, closing above the 50-sma in an uptrend, turning up
    if not (day_pct >= 0.04 and vol_surge >= 1.5 and c > s50 and tt >= 0.6 and c > cprev):
        return None
    rs_min = _f(params, "entry.rs_rating_min", 70)
    score_min = _f(params, "entry.min_score", 60)
    if rs_rating_value < rs_min or not ind.weekly_uptrend(df):
        return None
    mom_score = min(day_pct / 0.10, 1.0) * 100.0          # a 10% day saturates the momentum component
    vol_score = min(vol_surge / 3.0, 1.0) * 100.0
    score = int(round(0.35 * rs_rating_value + 0.30 * (tt * 100.0) + 0.20 * mom_score + 0.15 * vol_score))
    if score < score_min:
        return None
    stop_mult = _f(params, "stop_loss_atr_mult", 2.0)
    pt_cap = _f(params, "exit.profit_target_r", 2.5)
    size_r = _f(params, "position_size_r", 1.0)
    # tight STRUCTURAL stop just below the burst bar's low: the thesis is continuation, so a close back below
    # today's low means the burst failed. A momentum burst ENTERS at the high and PROJECTS FORWARD, so the
    # target is a forward continuation at the profit_target_r cap — NOT a measured move back to a prior swing
    # high (which is ~0 room here and would falsely veto every burst on R:R, exactly like the pullback issue).
    stop = float(low.iloc[-1]) - 0.25 * a
    r_per_share = c - stop
    if r_per_share <= 0:
        return None
    rr = max(DISCIPLINE_MIN_RR, pt_cap)                    # pt_cap∈[2.0,6.0] ≥ the discipline floor → always tradeable
    target = c + rr * r_per_share
    conv = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    return EntrySignal(
        ticker=ticker, setup="momentum_burst", entry_trigger=float(c), pivot=float(cprev), stop=float(stop),
        atr=float(a), rs_rating=int(rs_rating_value), score=score, profit_target=float(target),
        size_r=float(round(size_r * conv, 3)), r_per_share=float(r_per_share),
        notes=f"burst {day_pct*100:.1f}% vol×{vol_surge:.1f} rr={rr:.2f}")


def evaluate_episodic_pivot(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                            ticker: str = "?") -> Optional[EntrySignal]:
    """Dördüncü kurulum — Stockbee EPISODIC PIVOT / PEAD: kazanç açıklamasına DEMİRLİ büyük boşluk/patlama
    günü (haber-güdümlü kurumsal alım), aşırı-uzamamış bir isimde, sürüklenme (drift) devamına oynar.
    ZORUNLU çapa: son 2 seans içinde kazanç raporu (earnings.days_since_report — veri yoksa kurulum
    DÜRÜSTÇE hiç ateşlemez, uydurma tetik yok). Kapalı barlar; keşif menüsünü genişletme turu
    ile eklendi — momentum_burst emsali gibi önce DORMANT, silahlanma kararını olasılıksal kapı verir."""
    if bars is None or len(bars) < 60:
        return None
    from . import earnings as earn
    df = bars
    close, low, vol, opn = df["close"], df["low"], df["volume"], df["open"]
    atr_s = ind.atr(df, ATR_PERIOD)
    c, cprev = close.iloc[-1], close.iloc[-2]
    a = atr_s.iloc[-1]
    if any(pd.isna(x) for x in (a, cprev)) or a <= 0 or cprev <= 0:
        return None
    last_date = str(df["date"].iloc[-1])[:10] if "date" in df.columns else None
    if not last_date or not earn.days_since_report(ticker, last_date, max_days=2):
        return None                                        # PEAD çapası yok → kurulum yok (veri dürüstlüğü)
    gap_pct = (opn.iloc[-1] - cprev) / cprev
    day_pct = (c - cprev) / cprev
    vol50 = vol.iloc[-51:-1].mean()
    vol_surge = (vol.iloc[-1] / vol50) if vol50 > 0 else 0.0
    if not ((gap_pct >= 0.04 or day_pct >= 0.06) and vol_surge >= 2.5 and c > opn.iloc[-1] * 0.99):
        return None                                        # boşluk/patlama + hacim + gün içi tutuş
    c20 = close.iloc[-21]
    if c20 > 0 and (cprev / c20 - 1.0) > 0.20:
        return None                                        # rapordan ÖNCE zaten %20+ uzamış → sürpriz değil
    rs_min = _f(params, "entry.rs_rating_min", 70)
    score_min = _f(params, "entry.min_score", 60)
    if rs_rating_value < max(50, rs_min - 20):             # EP, RS dönüşünün BAŞI olabilir — eşik gevşek ama var
        return None
    gap_score = min(max(gap_pct, day_pct) / 0.12, 1.0) * 100.0
    vol_score = min(vol_surge / 5.0, 1.0) * 100.0
    score = int(round(0.30 * rs_rating_value + 0.40 * gap_score + 0.30 * vol_score))
    if score < score_min:
        return None
    stop_mult = _f(params, "stop_loss_atr_mult", 2.0)
    pt_cap = _f(params, "exit.profit_target_r", 2.5)
    size_r = _f(params, "position_size_r", 1.0)
    stop = max(float(low.iloc[-1]) - 0.25 * a, float(c) - stop_mult * a)   # EP günü dibi = tez çizgisi
    r_per_share = c - stop
    if r_per_share <= 0:
        return None
    rr = max(DISCIPLINE_MIN_RR, pt_cap)                    # PEAD sürüklenmesi ileri projeksiyondur (burst gibi)
    target = c + rr * r_per_share
    conv = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    return EntrySignal(
        ticker=ticker, setup="episodic_pivot", entry_trigger=float(c), pivot=float(cprev), stop=float(stop),
        atr=float(a), rs_rating=int(rs_rating_value), score=score, profit_target=float(target),
        size_r=float(round(size_r * conv, 3)), r_per_share=float(r_per_share),
        notes=f"EP gap {gap_pct*100:.1f}%/gün {day_pct*100:.1f}% vol×{vol_surge:.1f} rr={rr:.2f}")


def evaluate_exhaustion_hammer(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                               ticker: str = "?") -> Optional[EntrySignal]:
    """Beşinci kurulum — Stockbee SATIŞ-TÜKENMESİ ÇEKİCİ: uptrend içindeki kontrollü geri çekilmede,
    gün içi dibi kısa vadeli düşüğü delip kapanışa alıcıların dönmesiyle uzun alt fitilli çekiç bar →
    LONG reversal. Yalnız OHLCV (anahtarsız).

    SİLAHLANMA TARİHÇESİ (tarihçe-koru): 2026-07-24'te motor-uygulandı ve BİLİNÇLİ DORMANT bırakıldı
    ("ARMED_SETUPS'a EKLENMEZ; per-skill avg_r karşı-olgusal defterde ölçülür" — o günkü karar).
    2026-08-11 OPERATÖR ONAYIYLA SİLAHLANDI ("A seçeneği — exhaustion_hammer'ı silahla"): P-2026-08-07-
    VLO vakası (REVIEW→operatör-onaylı plan iç motorda doldu, aynaya emir hiç gitmedi; fiyat 304→322)
    onayın gerekçesidir. Silahlanma yalnız BU kuruluma verildi — momentum_burst ve episodic_pivot
    DORMANT kalır. GÜNCELLEME 2026-08-12: momentum_burst da AYRI bir operatör onayıyla silahlandı
    (gerekçe + şerh ARMED_SETUPS blokunda); yukarıdaki cümle o günün kapsamını anlatır, bugünkü
    silahlı kümeyi DEĞİL. episodic_pivot dormant kalmayı sürdürür. Kapalı barlar, ileri-dönük yok."""
    if bars is None or len(bars) < 65:
        return None
    df = bars
    o, h, l, c_s = df["open"], df["high"], df["low"], df["close"]
    atr_s = ind.atr(df, ATR_PERIOD)
    c, cprev = c_s.iloc[-1], c_s.iloc[-2]
    op, hi, lo = o.iloc[-1], h.iloc[-1], l.iloc[-1]
    a = atr_s.iloc[-1]
    if any(pd.isna(x) for x in (a, cprev, hi, lo)) or a <= 0 or c <= 0 or cprev <= 0:
        return None
    day_range = hi - lo
    if day_range <= 0:
        return None
    body = abs(c - op)
    lower_wick = max(0.0, min(op, c) - lo)
    lower_pct = lower_wick / day_range * 100.0
    body_pct = body / day_range * 100.0
    close_loc = (c - lo) / day_range * 100.0
    wick_body = (lower_wick / body) if body > 0 else 999.0
    recovery = (c / lo - 1.0) * 100.0 if lo > 0 else 0.0
    min_lower = _f(params, "eh.min_lower_wick_pct", 40.0)
    max_body = _f(params, "eh.max_body_pct", 35.0)
    min_close_loc = _f(params, "eh.min_close_location_pct", 60.0)
    min_wick_body = _f(params, "eh.min_lower_wick_to_body", 1.5)
    min_recovery = _f(params, "eh.min_recovery_from_low_pct", 2.0)
    if not (lower_pct >= min_lower and body_pct <= max_body and close_loc >= min_close_loc
            and wick_body >= min_wick_body and recovery >= min_recovery):
        return None
    rh_lb = int(_f(params, "eh.recent_high_lookback", 40))
    min_days = int(_f(params, "eh.min_days_since_high", 3))
    max_days = int(_f(params, "eh.max_days_since_high", 30))
    prior_high = h.iloc[-(rh_lb + 1):-1]                    # BUGÜNÜ HARİÇ → look-ahead yok
    if len(prior_high) < min_days + 1:
        return None
    recent_high = float(prior_high.max())
    if recent_high <= 0:
        return None
    days_since_high = int(len(prior_high) - int(prior_high.values.argmax()))
    pullback_depth = abs((c / recent_high - 1.0) * 100.0)
    min_pb = _f(params, "eh.min_pullback_pct", 6.0)
    max_pb = _f(params, "eh.max_pullback_pct", 35.0)
    if not (min_pb <= pullback_depth <= max_pb):
        return None
    if not (min_days <= days_since_high <= max_days):
        return None
    uc_lb = int(_f(params, "eh.undercut_lookback", 5))
    prior_low_win = l.iloc[-(uc_lb + 1):-1]                 # BUGÜNÜ HARİÇ
    prior_low = float(prior_low_win.min()) if len(prior_low_win) else lo
    undercut_reclaim = bool(lo < prior_low and c > prior_low)
    body_down = int((c_s.iloc[-11:-1].values < o.iloc[-11:-1].values).sum())
    if not ind.weekly_uptrend(df):                          # düşen-bıçak filtresi (uptrend içi düzeltme)
        return None
    rs_min = _f(params, "entry.rs_rating_min", 70)
    score_min = _f(params, "entry.min_score", 60)
    if rs_rating_value < max(50, rs_min - 20):
        return None
    stop_buf = _f(params, "eh.stop_buffer_pct", 0.10) / 100.0
    stop = lo * (1.0 - stop_buf)
    r_per_share = c - stop
    if r_per_share <= 0:
        return None
    risk_pct = r_per_share / c * 100.0
    if risk_pct > _f(params, "eh.max_risk_pct_to_stop", 12.0):
        return None
    geom = (min(lower_pct / 60.0, 1.0) * 40.0
            + min((100.0 - body_pct) / 80.0, 1.0) * 20.0
            + min(close_loc / 80.0, 1.0) * 25.0
            + min(recovery / (min_recovery * 3.0), 1.0) * 15.0)
    exh = (min(pullback_depth / 20.0, 1.0) * 45.0
           + (100.0 if undercut_reclaim else 40.0) * 0.35
           + min(body_down / 6.0, 1.0) * 20.0)
    exh = min(exh, 100.0)
    w_rs = _f(params, "eh.w_rs", 0.30); w_geom = _f(params, "eh.w_geom", 0.40); w_exh = _f(params, "eh.w_exh", 0.30)
    w_sum = max(w_rs + w_geom + w_exh, 1e-9)
    score = int(round((w_rs * rs_rating_value + w_geom * geom + w_exh * exh) / w_sum))
    if score < score_min:
        return None
    pt_cap = _f(params, "exit.profit_target_r", 2.5)
    size_r = _f(params, "position_size_r", 1.0)
    measured_rr = (recent_high - c) / r_per_share           # ÖLÇÜLÜ hareket (zirvenin ALTINDAN girilir → gerçek oda)
    rr = min(measured_rr, pt_cap)
    if rr < DISCIPLINE_MIN_RR:                              # sub-floor plan yüzeye çıkmaz (pullback emsali)
        return None
    target = c + rr * r_per_share
    conv = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    return EntrySignal(
        ticker=ticker, setup="exhaustion_hammer", entry_trigger=float(c), pivot=float(lo), stop=float(stop),
        atr=float(a), rs_rating=int(rs_rating_value), score=score, profit_target=float(target),
        size_r=float(round(size_r * conv, 3)), r_per_share=float(r_per_share),
        notes=f"hammer wick {lower_pct:.0f}% clo {close_loc:.0f}% pb {pullback_depth:.1f}% uc={undercut_reclaim} rr={rr:.2f}")


def evaluate_pead(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                  ticker: str = "?") -> Optional[EntrySignal]:
    """Altıncı kurulum — PEAD haftalık KIRMIZI-MUM KIRILIMI: kazanç boşluk-yükselişi sonrası düzenli geri
    çekilme (kırmızı haftalık mum), fiyat o mumun zirvesini aşınca sürüklenme devamı → GİRİŞ. episodic_pivot
    boşluk GÜNÜNDE ateşler; pead onun geri-çekilme-sonrası yeniden-kırılımını yakalar (ayrı zamanlama, ayrı
    kurulum — DUPLİKASYON DEĞİL). FMP-kapılı kazanç çapası (earnings.csv anahtarsız Nasdaq'tan dolar); veri
    yoksa None. DORMANT, LONG-only, kapalı barlar, ileri-dönük yok (kırmızı mum daima TAM GEÇMİŞ hafta)."""
    if bars is None or len(bars) < 60 or "date" not in bars.columns:
        return None
    from . import earnings as earn
    df = bars
    close, opn, vol = df["close"], df["open"], df["volume"]
    a = ind.atr(df, ATR_PERIOD).iloc[-1]
    c, cprev = close.iloc[-1], close.iloc[-2]
    if any(pd.isna(x) for x in (a, c, cprev)) or a <= 0 or cprev <= 0:
        return None
    watch_days = int(_f(params, "pead.watch_days", 35))
    last_date = str(df["date"].iloc[-1])[:10]
    if not earn.days_since_report(ticker, last_date, max_days=watch_days):
        return None                                        # FMP-kapılı çapa yok → kurulum yok
    min_gap = _f(params, "pead.min_gap_pct", 3.0) / 100.0
    win = min(watch_days, len(df) - 2)
    g, g_gap = None, min_gap
    for j in range(len(df) - win, len(df)):
        if j <= 0:
            continue
        gap = opn.iloc[j] / close.iloc[j - 1] - 1.0
        if gap >= g_gap:
            g_gap, g = gap, j
    if g is None or g >= len(df) - 2:
        return None
    # açık datetime coercion — dtype sürprizinde sessiz kalıcı None YOK (bare try/except değil)
    sub = df.iloc[g:].copy()
    sub["date"] = pd.to_datetime(sub["date"])
    wk = (sub.set_index("date")[["open", "high", "low", "close"]]
          .resample("W").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna())
    prior = wk.iloc[:-1]                                    # cari (kısmi) haftayı DIŞLA → look-ahead yok
    red_high = red_low = None
    for i in range(len(prior) - 1, -1, -1):
        w = prior.iloc[i]
        if w["close"] < w["open"]:
            red_high, red_low = float(w["high"]), float(w["low"])
            break
    if red_high is None or red_high <= 0 or red_low is None:
        return None
    if not (cprev < red_high <= c):                        # TAZE çapraz — bayat kırılımı kovalamaz
        return None
    rs_min = _f(params, "entry.rs_rating_min", 70)
    score_min = _f(params, "entry.min_score", 60)
    if rs_rating_value < max(50, rs_min - 20):
        return None
    vr = ind.volume_ratio(vol, 50).iloc[-1]
    vr_min = _f(params, "pead.min_volume_ratio", 1.2)
    if not pd.isna(vr) and vr < vr_min:                    # NaN (ince veri) bloklamaz, düşük hacmi eler
        return None
    brk_pct = (c - red_high) / red_high
    gap_score = min(g_gap / 0.10, 1.0) * 100.0
    brk_score = min(brk_pct / 0.03, 1.0) * 100.0
    vol_score = 0.0 if pd.isna(vr) else min(vr / 3.0, 1.0) * 100.0
    score = int(round(0.30 * gap_score + 0.25 * brk_score + 0.25 * rs_rating_value + 0.20 * vol_score))
    if score < score_min:
        return None
    pt_cap = _f(params, "exit.profit_target_r", 2.5)
    size_r = _f(params, "position_size_r", 1.0)
    stop = float(red_low) - 0.10 * a                       # kırmızı mum dibi = tez çizgisi
    r_per_share = c - stop
    if r_per_share <= 0:
        return None
    rr = max(DISCIPLINE_MIN_RR, pt_cap)                    # ileri sürüklenme projeksiyonu (burst/EP gibi)
    target = c + rr * r_per_share
    conv = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    return EntrySignal(
        ticker=ticker, setup="pead", entry_trigger=float(c), pivot=float(red_high), stop=float(stop),
        atr=float(a), rs_rating=int(rs_rating_value), score=score, profit_target=float(target),
        size_r=float(round(size_r * conv, 3)), r_per_share=float(r_per_share),
        notes=f"PEAD kırmızı-mum kırılımı brk={brk_pct*100:.1f}% gap={g_gap*100:.1f}% "
              f"vr={0.0 if pd.isna(vr) else vr:.2f} rr={rr:.2f}")


def evaluate_canslim(bars: pd.DataFrame, params: dict, rs_rating_value: int,
                     ticker: str = "?") -> Optional[EntrySignal]:
    """Yedinci kurulum — O'Neil CANSLIM büyüme-lideri: 52-hafta zirvesine YAKIN, hacim BİRİKİMLİ
    (up/down vol), RS LİDERİ bir isimde; çeyreklik kazanç ivmesi (C) ve yıllık büyüme (A) DOĞRULANMIŞ
    olarak devam alımı. C/A/I bileşenleri TEMELE (FMP) dayanır — o veri yoksa kurulum DÜRÜSTÇE hiç
    ateşlemez (episodic_pivot emsali; uydurma C/A skoru YOK). N/S/L günlük OHLCV + kesitsel RS'ten
    deterministik hesaplanır; M pazar yönü motorun REJİM katmanının işi (per-name uptrend burada
    trend_template+haftalık trendle teyit edilir). LONG-only, kapalı barlar, ileri-dönük yok. DORMANT.

    Faz C KAPISI: `earnings.canslim_fundamentals` yardımcısı + FMP nokta-zamanlı temel önbelleği HENÜZ
    YOK → bugün DAİMA None (güvenli no-op). Bu yüzden 'canslim-screener' ENGINE_IMPLEMENTED'a EKLENMEZ
    (pipeline_run onu yanlış 'invoked' saymasın); helper landıktan SONRA eklenir — pead/episodic'ten farkı
    tam olarak budur: onların earnings.csv'si mevcut anahtarsız kodla dolar, canslim'inki yeni kod ister."""
    if bars is None or len(bars) < 252:                    # N (52-hafta) ve trend şablonu tam geçmiş ister
        return None
    df = bars
    close, high, vol = df["close"], df["high"], df["volume"]

    # --- TEMEL KAPISI (C/A/I) — FMP-bağımlı, veri yoksa None (uydurma yok, episodic_pivot emsali) ---
    from . import earnings as earn
    last_date = str(df["date"].iloc[-1])[:10] if "date" in df.columns else None
    fund_fn = getattr(earn, "canslim_fundamentals", None)  # nokta-zamanlı FMP temel önbelleği (Faz C)
    if last_date is None or fund_fn is None:
        return None                                        # önbellek/yardımcı yok → tam DORMANT (bugün no-op)
    fund = fund_fn(ticker, last_date)                      # {eps_qoq_growth, eps_cagr_3yr, inst_ownership} | None
    if not fund:
        return None                                        # temel veri yok → kurulum yok (veri dürüstlüğü)
    eps_qoq = fund.get("eps_qoq_growth")                   # C: çeyreklik EPS YoY %
    eps_cagr = fund.get("eps_cagr_3yr")                    # A: 3y EPS CAGR %
    inst_own = fund.get("inst_ownership")                  # I: kurumsal sahiplik % (opsiyonel)
    if eps_qoq is None or eps_cagr is None:
        return None                                        # C ve A CANSLIM çekirdeği — eksikse ateşleme yok
    if eps_qoq < 18.0 or eps_cagr < 25.0:                  # O'Neil asgari: çeyreklik EPS +%18, yıllık CAGR +%25
        return None

    # --- TEKNİK BİLEŞENLER (N/S/L) — deterministik, günlük OHLCV ---
    atr_s = ind.atr(df, ATR_PERIOD)
    sma50 = ind.sma(close, 50)
    tt = ind.trend_template(df).iloc[-1]
    c = close.iloc[-1]
    a, s50 = atr_s.iloc[-1], sma50.iloc[-1]
    if any(pd.isna(x) for x in (a, s50, tt)) or a <= 0 or c <= 0:
        return None

    # N (Newness): 52-hafta zirvesine uzaklık + hacim-teyitli kırılım
    hi_52w = high.rolling(252, min_periods=252).max().iloc[-1]
    if pd.isna(hi_52w) or hi_52w <= 0:
        return None
    dist_high = (c / hi_52w - 1.0) * 100.0                 # 0 = tam zirvede, negatif = altında
    vr = ind.volume_ratio(vol, 50).iloc[-1]
    breakout = (not pd.isna(vr)) and c >= hi_52w * 0.995 and vr >= 1.4
    if dist_high >= -5.0 and breakout:      n_score = 100.0
    elif dist_high >= -10.0 and breakout:   n_score = 80.0
    elif dist_high >= -15.0 or breakout:    n_score = 60.0
    elif dist_high >= -25.0:                n_score = 40.0
    else:                                   n_score = 20.0
    if dist_high < -15.0 and not breakout:                 # zirveye yeterince yakın değil → CANSLIM alım noktası değil
        return None

    # S (Supply/Demand): son 60 barda up-günü hacmi / down-günü hacmi
    win = df.iloc[-60:]
    dclose = win["close"].diff()
    up_vol, dn_vol = win["volume"][dclose > 0], win["volume"][dclose < 0]
    if len(up_vol) < 10 or len(dn_vol) < 10:               # <10 up/down günü → ölçülemez
        return None
    avg_up, avg_dn = up_vol.mean(), dn_vol.mean()
    ud_ratio = (avg_up / avg_dn) if avg_dn > 0 else 5.0
    if ud_ratio >= 2.0:    s_score = 100.0
    elif ud_ratio >= 1.5:  s_score = 80.0
    elif ud_ratio >= 1.0:  s_score = 60.0
    elif ud_ratio >= 0.7:  s_score = 40.0
    elif ud_ratio >= 0.5:  s_score = 20.0
    else:                  s_score = 0.0
    if ud_ratio < 1.0:                                     # dağıtım → kurumsal alım yok → CANSLIM S başarısız
        return None

    # L (Leadership): motorun kesitsel RS proxy'si DOĞRUDAN L bileşenidir (O'Neil: liderler 80+ RS)
    rs_min = _f(params, "entry.rs_rating_min", 70)
    if rs_rating_value < max(rs_min, 80.0):                # CANSLIM liderlik tabanı 80
        return None
    l_score = 100.0 if rs_rating_value >= 90 else (80.0 if rs_rating_value >= 80 else 60.0)

    # C/A/I bileşen skorları
    c_score = 100.0 if eps_qoq >= 50.0 else (80.0 if eps_qoq >= 30.0 else 60.0)
    a_score = 90.0 if eps_cagr >= 40.0 else (70.0 if eps_cagr >= 30.0 else 50.0)
    if inst_own is None:      i_score = 50.0               # veri yoksa NÖTR 50 (I sadece %10 ağırlık; uydurma yok)
    elif 30.0 <= inst_own <= 90.0: i_score = 100.0
    else:                     i_score = 60.0

    # M (Market): pazar yönü motorun REJİM katmanının sorumluluğu (per-ticker DEĞİL). Per-name uptrend
    # teyidi trend_template + haftalık trend ile (lider tezi: 50-sma üstünde tutunma) — M'yi UYDURMADAN.
    if not (tt >= 0.6 and c > s50 and ind.weekly_uptrend(df)):
        return None
    m_score = tt * 100.0

    # --- CANSLIM bileşik skoru: O'Neil ağırlıkları (tunable → öğrenme döngüsüne açık), toplam normalize ---
    wc = _f(params, "entry.canslim_w_c", 0.15); wa = _f(params, "entry.canslim_w_a", 0.20)
    wn = _f(params, "entry.canslim_w_n", 0.15); ws = _f(params, "entry.canslim_w_s", 0.15)
    wl = _f(params, "entry.canslim_w_l", 0.20); wi = _f(params, "entry.canslim_w_i", 0.10)
    wm = _f(params, "entry.canslim_w_m", 0.05)
    wsum = max(wc + wa + wn + ws + wl + wi + wm, 1e-9)
    score = int(round((wc * c_score + wa * a_score + wn * n_score + ws * s_score
                       + wl * l_score + wi * i_score + wm * m_score) / wsum))
    score_min = _f(params, "entry.min_score", 60)
    if score < score_min:
        return None

    # plan: yeni-zirve alımı → İLERİ projeksiyon hedefi (isim zaten yeni zirvede; ölçülü-hareket R:R'yi
    # yanlışça veto ederdi). ATR stop (motor-tutarlı, ~O'Neil sıkı zarar kesme).
    stop_mult = _f(params, "stop_loss_atr_mult", 2.0)
    pt_cap = _f(params, "exit.profit_target_r", 2.5)
    size_r = _f(params, "position_size_r", 1.0)
    stop = float(c) - stop_mult * a
    r_per_share = c - stop
    if r_per_share <= 0:
        return None
    rr = max(DISCIPLINE_MIN_RR, pt_cap)                    # ileri projeksiyon ≥ disiplin R:R tabanı → hep tradeable
    target = c + rr * r_per_share
    conv = 0.6 + 0.4 * max(0.0, min(1.0, (score - score_min) / max(1.0, 100.0 - score_min)))
    return EntrySignal(
        ticker=ticker, setup="canslim", entry_trigger=float(c), pivot=float(hi_52w), stop=float(stop),
        atr=float(a), rs_rating=int(rs_rating_value), score=score, profit_target=float(target),
        size_r=float(round(size_r * conv, 3)), r_per_share=float(r_per_share),
        notes=f"CANSLIM C{c_score:.0f} A{a_score:.0f} N{n_score:.0f} S{s_score:.0f} L{l_score:.0f} "
              f"I{i_score:.0f} epsQoQ={eps_qoq:.0f}% cagr={eps_cagr:.0f}% ud={ud_ratio:.2f} "
              f"dist={dist_high:.1f}% rr={rr:.2f}")


# Which setups are AUTO-TRADED. Every screener is still EVALUATED on every ticker (scan_entry calls all
# three) — but only setups in this tuple arm a trade. Chosen by MEASURED contribution on the real FMP
# universe (full-replay score): breakout+pullback = 0.281; adding momentum_burst = 0.100 (it HURTS −0.18 —
# entering at the high after a 4% burst has no tradeable edge here); breakout-only = 0.164 (pullback HELPS
# +0.12). So the two proven setups are armed; momentum_burst is evaluated-but-DORMANT (its per-skill avg_r
# is still measured, and the learning loop can revisit). Add "momentum_burst" to arm it (lowers the edge).
#
# exhaustion_hammer — SİLAHLI, OPERATÖR ONAYI 2026-08-11 ("A seçeneği — exhaustion_hammer'ı silahla").
# Tarihçe: 2026-07-24'te motor-uygulandı ve bilinçli DORMANT bırakılmıştı (yukarıdaki ölçüm disiplini);
# P-2026-08-07-VLO vakası (onaylı REVIEW planı iç motorda doldu, aynaya emir hiç gitmedi, fiyat 304→322)
# sonrasında operatör silahlanmayı açıkça onayladı. SIRA ÖNEMLİ ve bilinçli: tuple sırası scan_entry /
# cf_backfilldeki "ilk eşleşen silahlı kurulum" önceliğidir — kanıtlı iki kurulum (breakout_vcp,
# pullback) öncelikli kalır, exhaustion_hammer aynı ticker'da ancak onlar ateşlemediyse aday üretir.
# momentum_burst ve episodic_pivot DORMANT KALIR (onay yalnız exhaustion_hammer içindir).
#
# momentum_burst — SİLAHLI, OPERATÖR ONAYI 2026-08-12 (karar penceresi: "momentum_burst:
# MANUEL SİLAHLANMA ONAYI"). Emsal exhaustion_hammer; yol aynı: OTOMATİK silahlanma OLMADI,
# insan verdi. Yukarıdaki 2026-07 paragrafı ÇÜRÜTÜLMEDİ, AŞILDI — silinmiyor çünkü o gün ölçülen
# şey (full-replay skor katkısı 0,281 → 0,100) gerçekti; değişen, kararın dayandığı ölçüm tabanı:
#   * Karne ölçümü: donuk üçlü eşiğin (i) replay-CI>0 ayağı KIL PAYI DÜŞTÜ
#     (CI [−0,0046, +0,5606], n=106) → OTOMATİK silahlanma tetiklenMEDİ; (ii) portföy-etkisi
#     GEÇTİ (+11,9k$); (iii) "−0,114R çelişkisi" hiç ölçüm değilmiş (prompt figürü) — çözüldü.
#   * Final-paket doğrulaması (3/3 GEÇTİ): C dünyası + mb = 885 işlem, +20.685$,
#     dd %12,7, sharpe 0,521. O koşum mb'yi `entry.armed_extra` ÖLÇÜM kanalıyla silahladı
#     (ARMED_SETUPS'a dokunmadan) — bu satır, ölçülen davranışın kablosudur.
# ŞERH (hükme iliştirik, silinmez): mb'nin yıl-deseni 2022 ve 2026'da ZAYIF (cf H2 −1,03 n=7;
# replay 2026 +0,014 n=16) → canlı izleme kalemi, sessiz bir zafer değil.
# SIRA ÖNEMLİ ve TARİHÇE-KORUMALI: tuple sırası `scan_entry`/`cf_backfill`teki "ilk eşleşen silahlı
# kurulum" önceliğidir. Mevcut üçlü YENİDEN SIRALANMADI; mb SONA eklendi — yani aynı ticker'da
# ancak breakout_vcp, pullback ve exhaustion_hammer ateşlemediyse aday üretir. Bu, final-paket koşumunun ölçtüğü
# önceliğin birebir aynısıdır (`ARMED_SETUPS + extra` → extra her zaman sonda).
# episodic_pivot (ve pead/canslim) DORMANT KALIR — onay yalnız momentum_burst içindi.
ARMED_SETUPS = ("breakout_vcp", "pullback", "exhaustion_hammer", "momentum_burst")


def relax_for_near_miss(eff: dict) -> dict:
    """near-miss GÖLGE taramasının gevşetilmiş eşik tablosu — TEK KAYNAK (tarama bulgusu).
    loop.daily_cycle ve cf_backfill bu dört satırı AYRI AYRI elle yazıyordu ('birebir' yorumuyla); iki
    ayrı dosyada elle bakımlı ikiz, near_miss_report'un beslendiği iki üreticidir — birinde eşik
    değişirse near-miss ölçümü sessizce ayrışırdı. Kırılım-sonrası eşiklerin hemen altında ölenleri
    cf deftere yazmak için: hacim ≤1.0, RS ≤55, skor ≤50, proximity ×1.5. Sıfır yetki — karar/kapı bu
    gevşek satırları asla okumaz; yalnız 'hangi eşik masada para bırakıyor?' ölçülsün diye."""
    rx = dict(eff)
    rx["entry.min_volume_ratio"] = min(1.0, float(eff.get("entry.min_volume_ratio", 1.5)))
    rx["entry.rs_rating_min"] = min(55, float(eff.get("entry.rs_rating_min", 70)))
    rx["entry.min_score"] = min(50, float(eff.get("entry.min_score", 60)))
    rx["entry.pivot_proximity_pct"] = float(eff.get("entry.pivot_proximity_pct", 2.0)) * 1.5
    return rx


def scan_all(bars: pd.DataFrame, params: dict, rs_rating_value: int, ticker: str = "?") -> dict:
    """Her ekran BU ticker'da HER ZAMAN koşar (kısa devre yok) → {setup: EntrySignal}. Silahlı/uyuyan
    ayrımı yapmaz — karşı-olgusal defter uyuyan kurulumların ateşlemelerini de görebilsin
    diye ham sonuç döner; işlem seçimi scan_entry'de kalır (davranış birebir)."""
    by_setup = {}
    for fn in (evaluate_entry, evaluate_momentum_burst, evaluate_pullback, evaluate_episodic_pivot,
               evaluate_exhaustion_hammer, evaluate_pead,   # Faz A (keyless) + Faz B (earnings-çapalı)
               evaluate_canslim):                           # Faz C: helper yokken güvenli no-op (hep None)
        sig = fn(bars, params, rs_rating_value, ticker)
        if sig is not None:
            by_setup[sig.setup] = sig
    return by_setup


def scan_entry(bars: pd.DataFrame, params: dict, rs_rating_value: int, ticker: str = "?") -> Optional[EntrySignal]:
    """Evaluate EVERY implemented screener on this ticker — all ALWAYS run (no short-circuit); each is
    logged as invoked in the P2_SCREEN pipeline. Only setups in ARMED_SETUPS produce a tradeable candidate;
    the rest are evaluated-but-dormant (measured to lack edge)."""
    by_setup = scan_all(bars, params, rs_rating_value, ticker)
    # silahlanma ÖLÇÜM kanalı: entry.armed_extra paramı bu taramada ek kurulumları silahlı sayar.
    # Param üzerinden aktığı için canlı döngüyle yarışmaz; yalnız arming._measure'ın walk'ları geçirir.
    extra = tuple(params.get("entry.armed_extra") or ())
    for setup in ARMED_SETUPS + extra:                                        # only proven setups arm a trade
        if setup in by_setup:
            return by_setup[setup]
    return None


@dataclass
class ManageDecision:
    """Bir barlık pozisyon yönetimi kararı: şimdi çıkılacak mı, çıkış nedeni ve GEVŞEMEYEN takip stopu."""
    exit_now: bool
    exit_reason: Optional[str]
    trail_stop: float          # updated trailing stop level (never loosens)


def manage_position(bars: pd.DataFrame, position: dict, params: dict,
                    bars_held: int, regime_ok: bool) -> ManageDecision:
    """Per-bar management on the last CLOSED bar. Returns updated trail stop + whether a
    time-stop or regime-flip exit fires. Price-touch exits (hard stop / target) are applied
    by broker.py against the NEXT bar so there is no look-ahead.

    `early_kill_pivot` de BURADAN çıkar — bu fonksiyon replay'in ve canlı döngünün
    PAYLAŞTIĞI tek çıkış-karar yüzeyidir, yani yeni bir çıkış yasası eklemenin doğru yeri burasıdır
    (loop.py'a ikinci bir uygulama YAZILMADI). `position` sözlüğü artık `pivot` da taşıyabilir;
    taşımayan çağıranlarda erken itlaf sessizce ateşlemez (bkz. early_kill_pivot_exit)."""
    df = bars
    a = ind.atr(df, ATR_PERIOD).iloc[-1]
    close = df["close"].iloc[-1]
    entry = position["entry"]
    hard_stop = position["stop"]
    prev_trail = position.get("trail_stop", hard_stop)

    trail_mult = _f(params, "exit.trail_atr_mult", 2.5)
    new_trail = prev_trail
    if not pd.isna(a) and a > 0:
        candidate = close - trail_mult * a
        # only ratchet up, and only once the trade is in profit past 1R
        if close > entry + position["r_per_share"]:
            new_trail = max(prev_trail, candidate)
    # breakeven: once the bar's high reached entry + breakeven_r * risk, lock the stop at entry so a
    # winner that reverses can't turn into a loss (protects the drawdown score / the L0->L1 max_dd gate).
    be_r = _f(params, "exit.breakeven_r", 1.0)
    if be_r > 0 and bars["high"].iloc[-1] >= entry + be_r * position["r_per_share"]:
        new_trail = max(new_trail, entry)
    # chandelier trail: anchor the trail to the recent SWING HIGH minus ATR·mult, not just close −
    # ATR·mult. Rides trends further while still ratcheting. exit.chandelier_lookback=0 → off (default).
    # PENCERE GİRİŞTEN ÖNCESİNE UZANAMAZ. Chandelier tanımı gereği
    # GİRİŞTEN BU YANA en yüksek zirveye demirlenir; `iloc[-chand_lb:]` ise pozisyon 1 bar tutulmuşken
    # 19 bar GİRİŞ ÖNCESİNE uzanıyordu — yani pozisyonun hiç görmediği bir zirveden stop hesaplanıyordu.
    # giveback için ZATEN düzeltilmiş olan hatanın (bkz. aşağıdaki giveback notu) birebir aynısı, iki satır arayla.
    # Gerçek barlarda ölçüldü (chand_lb=20, trail 2.5·ATR, 1-5 bar tutuş, kârda olan yönetim barları):
    # %22,0'ında stop gerçek chandelier'den DAHA SIKI çıkıyor; %3,70'inde stop GÜNCEL KAPANIŞIN ÜSTÜNE
    # çıkıyor (ertesi bar kesin çıkış) — gerçek chandelier ise çıkarmıyor. Bugün uykuda (varsayılan 0)
    # ama bounds.yaml 0-30 aralığını arama döngüsüne AÇIK bırakıyor: açıldığında kapı bozuk bir çıkışı ölçerdi.
    chand_lb = int(_f(params, "exit.chandelier_lookback", 0))
    if chand_lb > 0 and not pd.isna(a) and a > 0 and close > entry + position["r_per_share"]:
        hh = bars["high"].iloc[-min(chand_lb, max(1, bars_held)):].max()
        new_trail = max(new_trail, hh - trail_mult * a)
    new_trail = max(new_trail, hard_stop)

    # ERKEN İTLAF — SIRA GEREKÇESİ: diğer tüm çıkış dallarından ÖNCE sınanır çünkü sorduğu soru
    # en temel olanıdır ("tez hâlâ ayakta mı?") ve yalnız ilk birkaç barda sorulabilir. Sonraya
    # konsaydı aynı barda ateşleyen bir giveback/time_stop onu maskeler ve çıkış SEBEBİ yanlış
    # etiketlenirdi — sebep dağılımı çıkış şelalesinin ham maddesi olduğu için bu bir ölçüm hatası
    # olurdu. Pratikte çakışma dar: giveback zirvede >1R kâr ister, erken itlaf pivot-altı kapanış.
    # `new_trail` YUKARIDA hesaplandı ve döndürülür: itlaf kararı trail'i geri almaz.
    if early_kill_pivot_exit(bars, position, params, bars_held):
        return ManageDecision(True, "early_kill_pivot", new_trail)

    # peak-profit give-back: once a trade has run past 1R favorable, exit if it hands back more than
    # exit.giveback_pct of its PEAK open profit — protects momentum give-back on parabolic rollovers.
    # =0 → off (default). Uses the bars held so far to estimate the peak. bars_held is incremented ON the
    # entry day (backtest.py/loop.py), so the peak window is exactly the last `bars_held` bars — NOT
    # bars_held+1, which reached one bar BEFORE entry (the breakout/signal high) and fabricated a peak
    # profit the position never held, firing spurious 'giveback' exits. Latent today (default 0).
    giveback = _f(params, "exit.giveback_pct", 0.0)
    if giveback > 0 and bars_held >= 1:
        window = bars["high"].iloc[-bars_held:]
        peak_profit = float(window.max()) - entry
        if peak_profit > position["r_per_share"] and (close - entry) < peak_profit * (1.0 - giveback):
            return ManageDecision(True, "giveback", new_trail)

    time_stop = int(_f(params, "exit.time_stop_days", 15))
    if bars_held >= time_stop:
        return ManageDecision(True, "time_stop", new_trail)
    if not regime_ok:
        return ManageDecision(True, "regime_flip", new_trail)
    return ManageDecision(False, None, new_trail)
