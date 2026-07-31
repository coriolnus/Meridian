# Y4 SİNYAL AİLESİ — İLK ÖLÇÜM (2026-07-30, Rol 2)

Hedef sözleşmesi md.5. **ÖNCE ÖLÇ, sonra kabloLA** — bu tur yalnız ölçümdür, kablolama yapılmadı.
Makine-okunur tam tablo: `y4_ic_sonuc.json`. Kod: `y4_olc.py` (+ `si_fetch.py` çekim, `probe*.py` sonda).

**Repo dosyalarına yazılmadı; canlı/yerel state'e SIFIR yazım.** `config.STATE`/`BARS` sandbox'a
yönlendirildi (doğrulandı); barlar `/Users/erdemozturk/AI-Trading/state/bars`'tan SALT-OKUMA okundu.

---

## HÜKÜM (özet)

| aile | hüküm | dayanak |
|---|---|---|
| **short-interest** | **EDGE YOK** | 12 aday hücrenin 0'ı sınırı geçti; tek sınırdaki hücre karıştırıcı ayrışımında **likidite vekili** çıktı |
| **insider (Form-4)** | **ÖLÇÜLEMEDİ** — "edge yok" DEĞİL | FMP ücretsiz planında tarihsel pencere YOK; üç sınır de canlı sondalandı |

**Ek (istenmeyen ama önemli) bulgu: bar önbelleğinde HAYALET SEANS.**
`2025-05-26` (Memorial Day — ABD piyasası KAPALI) 259 bar dosyasının **258'inde** bir seans olarak
duruyor. Çoğu sembolde 2025-05-23'ün birebir kopyası; **beş sembolde (ORLY/BKNG/KLAC/NFLX/NOW)
bölünme-düzeltilmemiş ham fiyat** (ORLY 91.62 → 1374.37 = tam ×15, kendi 15:1 bölünmesi).
`2018-11-22` (Thanksgiving) de aynı sınıf (15 sembolde sıçrama). Ayrıntı aşağıda §4.

---

## 1. INSIDER AİLESİ — ÖLÇÜLEMEDİ (kapsam yok)

Aile ölçülemedi çünkü **FMP ücretsiz planı tarihsel Form-4 penceresi vermiyor**. Üç sınırın üçü de
bu turda CANLI sondalandı (varsayım değil):

| yol | sonuç |
|---|---|
| `insider-trading/search?symbol=X` (sembol-başına geçmiş) | **HTTP 402** — adaptör docstring'indeki 2026-07-29 ölçümü bugün doğrulandı |
| `insider-trading/latest&limit>100` | **HTTP 402** (limit=250 ve limit=1000 denendi) |
| `insider-trading/latest&page>=1` | **HTTP 402** (page=1, 5, 10, 40 denendi; **yalnız page=0** 200 döndü) |
| `insider-trading/latest&date=YYYY-MM-DD` | **PARAMETRE SESSİZCE YOK SAYILIYOR** — `date=2026-03-02` isteği page=0 ile AYNI (bugünkü) satırları döndürdü. 402 değil, **200 + yanlış veri**. |

**Ulaşılabilen gerçek pencere: akışın EN YENİ 100 dosyalaması — tek sayfa, tek anlık görüntü.**
Daha derinini uydurmuyorum; 6-12 aylık pencere bu planla ERİŞİLEBİLİR DEĞİL.

**Neden bu ölçümü imkânsız kılıyor** (page-0 örneği, 100 satır, hepsi filingDate=2026-07-30):
- evren-içi satır: **6/100** (%6, tamamı tek sembol: KO)
- evren-içi yön dağılımı: `diger` 4, `satim` 2 — **evren-içi P-Purchase olayı: 0**
- IC için gereken: ≥30 evren-içi ALIM olayı, **hepsi ≥1 ay öncesinden** (20 seans ileri getiri şart).
  Erişilebilir pencere BUGÜNÜN tek sayfası olduğu için **uygun olay sayısı sıfır**.
- yerel defter (`state/insider_trades.json`): 6 işlem, 3 sembol — aynı sebeple sığ.

**Point-in-time alan adı (belgelendi):** kullanılabilirlik tarihi = **`filingDate`**, işlem tarihi =
`transactionDate` — canlı yanıtta **ikisi de ayrı alan olarak MEVCUT**. Aradaki fark küçük değil:
page-0 örneğinde `transactionDate` 2025-11-07..2026-07-30'a yayılırken `filingDate`'lerin TAMAMI
2026-07-30. Yani geç dosyalama gerçek ve büyük; işlem tarihini kullanılabilirlik tarihi saymak
**ileri-bakış** olurdu.

### Bunun ikinci sonucu: `adapters/insider.py`'deki bir mekanizma ULAŞILAMAZ
`fetch_delta` artımlı SAYFALAMA üzerine kurulu (`VARSAYILAN_SAYFA_TAVANI=40`, `--sayfa-tavani`,
`durma_sebebi=sayfa_tavani`, "soğuk ilk koşu ~150 sayfa isteyebilir"). **page>=1 402 döndüğü için bu
yolun tamamı ücretsiz planda ölü**: her koşu page 0'da biter. Modül docstring'i "3 yıllık pencere
`/latest` akışının GÜNLÜK BİRİKTİRİLMESİYLE dolar" diyor — bu **ölçülmemiş bir umut**: günde ~%6
evren isabetli tek sayfa ile 3 yıllık kapsam pratikte dolmaz. (Rol 1'e: temizlik turunun
"ölü mekanizma" kovasına aday.)

### Aile nasıl ölçülebilir hâle gelir (operatör kalemi)
1. **FMP planı yükseltme** — `search` + paging + limit birlikte açılır. Tek adımda çözer.
2. **SEC EDGAR "Insider Transactions Data Sets"** (çeyreklik Form 3/4/5 TSV paketleri, ücretsiz,
   anahtarsız; filingDate + transactionDate + işlem kodu + adet + fiyat hepsi içinde). 12 ay = 4 paket.
   **BU TURDA İNDİRİLMEDİ** — dosya indirme operatör onayı gerektirir ve bu ölçümün kapsamı dışı.
   Onay verilirse aile FMP kotasına hiç dokunmadan tam ölçülebilir.

---

## 2. SHORT-INTEREST AİLESİ — ÖLÇÜLDÜ, EDGE YOK

### Ulaşılan pencere ve kapsam (uydurma yok, hepsi çekimden)
- kaynak: FINRA `otcMarket/consolidatedShortInterest` — **anahtarsız, ücretsiz, FMP kotasına etkisi 0**
- **6 istek** (251 sembol / 50'lik dilim), 12.267 ham satır
- **49 settlement: 2024-07-15 → 2026-07-15 (24 ay, TAM — eksik yayın yok)**
- 251 sembolün **251'i** FINRA'da bulundu; (sembol,settlement) çift kaydı **0**
- ölçülen kayıt: 12.250 (17 satır düştü: **FISV**'nin bar dosyası yok — bilinen açık operatör kalemi;
  FISV FINRA'da 2025-11-14'ten itibaren 17 settlement ile mevcut)
- yayın günü sayısı: **49**; ileri getiri eksiği: son yayın h=5/10'da, son iki yayın h=20'de (pencere dolmadı)

**Yayın tarihi tanımı:** `settlementDate + 9 İŞ GÜNÜ` — sabit `adapters/shortinterest.YAYIN_GECIKME_ISGUNU`'ndan
alındı (kendi sabitim değil). Tatiller hariç değil (adaptörün `_isgunu_farki`'siyle aynı kabul);
sonra **sonraki seansa yuvarlanır, asla öncekine** (erken giriş üretmez).
**Getiri tanımı:** `close[t+h]/close[t]-1`, t = yayın günü seansı — `component_ic.forward_returns`
ile AYNI tanım. Ufuklar `component_ic.HORIZONS` = (5,10,20).

### İki tanım gerçekten iki mi?
| çift | Spearman | not |
|---|---|---|
| `dtc_finra` ↔ `dtc_meridian` | **0.90** (medyan oran 0.992) | AYRI ölçümler — adaptörün uyarısı doğrulandı |
| `si_delta_pct_finra` ↔ `si_delta_pct_local` | **1.00** (medyan mutlak fark 0.0025 puan) | **AYNI büyüklüğün iki adı** — FINRA'nın `changePercent`i bizim yerel hesabımızın birebir aynısı; ayrı bileşen saymak çoklu-sınamayı şişirir |

### IC tablosu (hüküm "seri" okumasına dayanır)
`seri` = her yayın gününde kesitsel Spearman IC, sonra IC serisinin ortalaması (**bir gün = bir gözlem**,
kümelenme yapısal olarak çözülür). `havuz` = ev deseni (component_ic.json ile kıyas için); **havuz
Fisher CI'si bir ALT SINIRdır** — gün başına ~250 satır kümelenmiştir, gerçek aralık daha geniştir.

| bileşen | h | seri IC | %95 CI | t | n_gün | ilk 12ay | son 12ay | işaret aynı | havuz IC |
|---|---:|---:|---|---:|---:|---:|---:|:---:|---:|
| dtc_finra | 5 | -0.0012 | [-0.026, 0.023] | -0.10 | 48 | +0.008 | -0.010 | hayır | 0.005 |
| dtc_finra | 10 | -0.0085 | [-0.033, 0.016] | -0.69 | 48 | -0.012 | -0.005 | evet | -0.005 |
| dtc_finra | 20 | -0.0225 | [-0.050, 0.005] | -1.60 | 47 | -0.029 | -0.017 | evet | 0.012 |
| **dtc_meridian** | 5 | -0.0049 | [-0.033, 0.023] | -0.34 | 48 | +0.013 | -0.023 | hayır | 0.011 |
| **dtc_meridian** | 10 | -0.0103 | [-0.035, 0.014] | -0.82 | 48 | -0.014 | -0.006 | evet | 0.004 |
| **dtc_meridian** | **20** | **-0.0291** | **[-0.0582, -0.0001]** | **-1.97** | 47 | -0.038 | -0.020 | evet | -0.011 |
| si_delta_pct_finra | 5 | +0.0068 | [-0.014, 0.027] | 0.65 | 48 | +0.007 | +0.007 | evet | 0.016 |
| si_delta_pct_finra | 10 | +0.0031 | [-0.019, 0.026] | 0.27 | 48 | +0.010 | -0.004 | hayır | -0.010 |
| si_delta_pct_finra | 20 | -0.0007 | [-0.022, 0.020] | -0.06 | 47 | +0.014 | -0.015 | hayır | -0.014 |
| si_delta_pct_local | 5 | +0.0076 | [-0.013, 0.028] | 0.72 | 47 | +0.008 | +0.007 | evet | 0.015 |
| si_delta_pct_local | 10 | +0.0044 | [-0.018, 0.027] | 0.38 | 47 | +0.013 | -0.004 | hayır | -0.011 |
| si_delta_pct_local | 20 | -0.0004 | [-0.022, 0.021] | -0.04 | 46 | +0.015 | -0.015 | hayır | -0.013 |

**Sınır: CI sıfırı dışlıyor VE |IC| ≥ 0.03 → prescreen adayı. Geçen hücre: 0.**
Tek sınırdaki hücre `dtc_meridian@20`: CI üst sınırı **-0.0001** (kılpayı), |IC|=0.029 **eşiğin altında**.

### Sınırdaki hücre neden bir bulgu DEĞİL — karıştırıcı ayrışımı
`dtc_meridian = kısa_pozisyon / ADV20`. Bir ORANın IC'si tek başına **payın mı paydanın mı**
konuştuğunu söylemez. Üçünü ayrı ölçtüm (h=20):

| ölçülen | seri IC | t | beşlik şekli |
|---|---:|---:|---|
| **pay tek başına** (`kisa_ham`) | +0.0109 | 0.85 | monoton ama **ters işaretli** (boyut vekili) |
| **payda tek başına** (`ln ADV20`) | **+0.0263** | **1.89** | **temiz monoton**: Q1 -0.005 → Q5 +0.008 |
| oran (`dtc_meridian`) | -0.0291 | -1.97 | **monoton DEĞİL**: Q1 +0.008, Q2 -0.004, Q3 +0.000, Q4 +0.001, Q5 -0.005 |
| **boyut-nötr tanım** (`kısa / DOLAR hacim`) | -0.0086 | -0.51 | düz |

Okuma: **kısa pozisyonun kendisi hiçbir şey söylemiyor** (t=0.85, üstelik ters işaret). `dtc_meridian`'ın
sinyali paydadan geliyor — `ln(ADV20)`'nin ayna görüntüsü (+0.0263 ↔ -0.0291), ve **payda tek başına
oranın kendisinden daha temiz bir monoton gradyan üretiyor**. Kısa pozisyonu boyuttan arındıran
tanım (dolar hacme bölme) ise **tamamen düz**. Yani ölçülen kırıntı bir *short-interest* etkisi değil,
bir **likidite/hacim vekili** — ve o bile tek başına anlamlı değil (CI [-0.0009, +0.0535] sıfırı kapsıyor).

### Çoklu sınama
12 hücre sınandı ama **bağımsız değiller** (delta çifti ρ=1.00 → aynı büyüklük; dtc çifti ρ=0.90).
Etkin bağımsız sınama ≈ **6**. α=0.05'te 6 sınamadan ~0.3'ünün şansa "anlamlı" çıkması beklenir;
**t=-1.97'lik tek sınır hücresi tam da şansın vereceği şeydir.**

---

## 3. DÜRÜSTLÜK ÇİVİLERİ

- **Örneklem kuraklığı:** `IC_MIN_SAMPLE`=30 altındaki gün-kesiti hücreleri hiç hesaplanmadı;
  `n_gun<5` olan seri hücreleri `ci=None, neden` ile ÖLÇÜLEMEDİ işaretlendi. Bu panelde kesit
  günlük ~250 isim olduğu için kuraklık **short tarafında sorun değildi** — kuraklık insider
  tarafındaydı ve orası zaten "ölçülemedi" hükmü aldı.
- **Kümelenme:** havuz Fisher CI'leri **alt sınırdır** (gün başına ~250 satır). Bu yüzden hüküm
  havuza değil seri okumasına dayandırıldı. İki okumanın işaretinin bile yer yer ayrışması
  (ör. dtc_finra@20: seri -0.022 / havuz +0.012) havuzun neden tek başına okunmaması gerektiğinin
  somut kanıtı.
- **Survivorship:** evren BUGÜNÜN 251 sembolü (`REPLAY_UNIVERSE`). 24 ay geriye bakışta
  **hayatta-kalma yanlılığı VARDIR** — 2024-07'de endekste olup bugün olmayan isimler panelde yok.
  Emekli 8 sembol (ANSS/DFS/FI/HES/IPG/K/PARA/WBA) zaten evren dışı. Kesitsel IC bundan mutlak
  getiriden daha az etkilenir ama **bağışık değildir**.
- **Bilinen boşluk:** `si_yuzde_float` ölçülmedi — bu depoda float/sharesOutstanding kaynağı yok ve
  FMP `profile` sembol-başına 1 istektir (251 sembol = günlük kotanın tamamı). Uydurulmadı.
- **Uydurma yok:** tüm alan adları canlı yanıttan (`symbolCode`, `currentShortPositionQuantity`,
  `daysToCoverQuantity`, `averageDailyVolumeQuantity`, `changePercent`, `settlementDate`;
  FMP tarafında `filingDate`, `transactionDate`, `transactionType`, `acquisitionOrDisposition`).
  Sabitler adaptörlerden (`YAYIN_GECIKME_ISGUNU=9`, `ADV_PENCERE=20`, `SPLIT_SUSPECT_RET=0.35`),
  ufuk/eşik `component_ic`/`analytics`'ten.

---

## 4. YAN BULGU — BAR ÖNBELLEĞİNDE HAYALET SEANS (Rol 1'e taşınmalı)

Ölçüm ilk koşuda `dtc_meridian@20` için D1 deciline **+%6.3** ortalama getiri verdi. Kovalayınca
sinyal değil **veri kusuru** çıktı:

- **`2025-05-26` Memorial Day'dir; ABD piyasası KAPALIDIR. Bar önbelleğinin 259 dosyasının 258'inde
  o gün bir seans olarak duruyor** (SPY dahil).
  - çoğu sembolde 2025-05-23'ün **birebir OHLCV kopyası** (AAPL: open/close/volume tıpatıp aynı)
  - **5 sembolde bölünme-düzeltilmemiş ham fiyat**: ORLY 91.62→1374.37 (**×15**, kendi 15:1 bölünmesi),
    BKNG ×25, KLAC ×10, NFLX ×10, NOW
  - sonuç: BKNG için 20-günlük "getiri" **+%2598**, ORLY +%1377, KLAC +%963, NFLX +%940 — hepsi
    aynı yayın gününde (2025-04-28), tek başlarına D1 anomalisinin tamamını üretiyorlardı
- **`2018-11-22` (Thanksgiving) aynı sınıf** — 15 sembolde sıçrama.

**Ev savunmaları bunu YAKALAMIYOR:**
- `adapters/data.sanitize_bars` yalnız **aynı tarihi** tekilleştirir; 2025-05-26 ayrı bir tarihtir → geçer.
- `validate_bars` `split_suspect` diye işaretler ama **severity=soft**, hiçbir yerde engellemez.
- `state/bar_source_seams.json` bu iki tarihi **bilmiyor** (arandı, yok).

**Etki alanı:** `sanitize_bars` okuyan HER ölçüm — `component_ic.py`, `cf_backfill.py`, `dataset.py`,
`loop.py` — yani `component_ic.json`, karşı-olgusal defter ve eşik eğrisi 2025-05-26'yı kesen
pencerelerde bu kusuru taşıyor. Rank-tabanlı IC'ler büyük ölçüde dayanıklı (bu ölçümde temizlik
öncesi/sonrası IC -0.0299 → -0.0291), ama **ortalama-getiri / R-katlı her tablo doğrudan etkilenir**.

Bu ölçümde ne yapıldı: iki hedefli onarım (`y4_olc._bar_temizle`) — (1) OHLC dörtlüsü bir öncekinin
birebir aynısı olan bar düşürülür, (2) `|değişim| > SPLIT_SUSPECT_RET` olup **bir sonraki barda geri
dönen** izole sivri uç düşürülür (kalıcı kopuş DÜŞMEZ). Ölçüm penceresinde (2024-07+) temizlenen:
`2025-05-26` 208 hayalet + 7 sıçrama, `2025-09-10` 2 sıçrama.

---

## 5. KOTA HARCAMASI

| kaynak | çağrı | not |
|---|---:|---|
| **FMP** | **10** | tavan 120 idi — **110 kullanılmadı**. Fazlası ANLAMSIZDI: page>=1 ve limit>100 402 döndüğü için ek çağrı ek VERİ getirmiyor. 1 başarılı (page-0 örneği), 9'u sınır sondası. |
| FINRA | 6 | anahtarsız/kotasız; FMP bütçesine etki 0 |
| bar çekimi | 0 | yerel önbellek, salt-okuma |

FMP çağrıları sandbox `fmp_usage.json`'a işlendi (canlı muhasebe defterine dokunulmadı) —
**canlı sayaç bu 10 çağrıyı görmeyecek**, kota planlamasında hesaba katılmalı.

---

## 6. HÜKÜM ÖNERİSİ (Rol 1'e)

1. **short-interest → prescreen'e BAĞLANMASIN.** 4 bileşen × 3 ufukta sınırı geçen hücre yok; tek
   sınır hücresi karıştırıcı ayrışımında likidite vekili çıktı. Hedef sözleşmesi md.5'in
   "**'edge yok' hükmü ölçümle kayda geçti**" şıkkı **bu aile için karşılandı** (24 ay tam kapsam,
   49 yayın, 12.250 kayıt).
2. **`si_delta_pct_local` bileşen olarak kaldırılsın** — FINRA'nın `changePercent`iyle ρ=1.00, ayrı
   bileşen değil ikinci bir ad. (Adaptörde ikisini ayrı tutmak yine de doğru: biri sağlayıcı
   alanının doğrulaması.)
3. **insider → "edge yok" YAZILMASIN, "ÖLÇÜLEMEDİ (kapsam yok)" yazılsın.** Adaptörün kendi
   `siniflanamadi` disiplininin ta kendisi. Aile ancak (a) FMP planı yükseltilirse ya da
   (b) operatör SEC EDGAR Form 3/4/5 veri setlerinin indirilmesini onaylarsa ölçülebilir.
4. **`adapters/insider.fetch_delta` sayfalama yolu ölü-mekanizma kovasına aday** — `sayfa_tavani`
   ücretsiz planda ULAŞILAMAZ (page>=1 → 402). Docstring'in "günlük biriktirmeyle 3 yıl dolar"
   beklentisi de ölçülmemiş; %6 evren isabetli tek sayfa ile pratikte dolmaz.
5. **BAR HAYALET SEANSI ayrı ve acil bir kalem** (§4). En az: `2025-05-26` ve `2018-11-22`'nin
   önbellekten düşürülmesi + `sanitize_bars`'a "önceki barın birebir kopyası" kuralı + `split_suspect`
   soft bulgusunun bir yerde GERÇEKTEN okunması. `component_ic.json` bu düzeltmeden sonra yeniden
   üretilmeli.
6. Sıradaki aday aileler (transkript-LLM, 13F) için ders: **aileyi seçmeden ÖNCE erişilebilir
   pencereyi sonda** — bu turda ölçümün önündeki tek engel modelleme değil, 4 çağrıda ölçülebilen
   bir plan sınırıydı.

---

## DOSYALAR
- `y4_ic_sonuc.json` — tam makine-okunur tablo (bileşen × ufuk × {havuz, seri, yarı-örnek, gün detayı},
  kova tabloları, kontrol bileşenleri, hüküm bloğu, insider kapsam ölçümü, bar temizlik tanısı)
- `y4_olc.py` — ölçüm scripti · `si_fetch.py` — FINRA çekimi · `finra_raw.json` — ham panel (12.267 satır)
- `probe.py`/`probe2..5.py` — FMP sınır sondaları · `fmp_page0_sample.json` — page-0 kanıt örneği
- `confound.py`, `diag.py`, `d1.py` — karıştırıcı/kararlılık/konsantrasyon teşhisleri
