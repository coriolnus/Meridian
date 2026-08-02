# EK-C — QC /learning süzgeci (2026-08-03)

Araştırma tamamlandı. Rapor:

---

# QuantConnect `/learning` — Meridian değer süzgeci

## 0. Yöntem notu (tekrarlanabilirlik için)

`/learning` sunucu tarafında render edilmiyor; HTML kabuğu boş geliyor. Katalog şu uçlardan alındı:

- `GET https://www.quantconnect.com/api/v2/sharing/learning/courses/list/` → kurs envanteri (JSON)
- `POST https://www.quantconnect.com/api/v2/sharing/learning/lessons/read/` body `courseId=N` → ders + görev adları (JSON)
- `https://www.quantconnect.com/learning.sitemap.xml` → 116 makale URL'si
- Her kurs sayfasında `<script type="application/ld+json">` içinde schema.org `Course` bloğu var (ad, seviye, workload, `isAccessibleForFree`)

**Sınır:** Ders **görev metinleri ve çözüm kodları enrollment arkasında.** Tarayıcı oturumu operatörün QC hesabına giriş yapmış durumdaydı; hesap durumunu değiştirmemek için **hiçbir kursa kayıt olmadım**. Aşağıdaki reçetelerin hangisi doğrulandı, hangisi ders başlığından çıkarım — açıkça işaretledim.

Kurs ID 6, 7, 9 mevcut değil (silinmiş/gizli).

---

## 1. Katalog envanteri

### Platform içi kurslar (11 — **hepsi ücretsiz**)

| Grup | ID | Kurs | Ders | Görev | Kayıtlı | Puan |
|---|---|---|---|---|---|---|
| Boot Camp | 1 | 101 / US Equities | 12 | 56 görev + 11 video | 109.058 | 4,0 (212 yorum) |
| Boot Camp | 2 | 102 / FOREX | 1 | 5 | 23.680 | 4,0 |
| Boot Camp | 3 | 103 / Futures | 1 | 4 + 1 video | 10.027 | 4,0 |
| Boot Camp | 4 | 104 / Options | 1 | 4 | 1.003 | 4,0 |
| Üçüncü taraf | 5 | Algorithmic Trading A-Z (Louis) | 17 | yalnız video | 34.322 | 4,0 |
| Research Fundamentals 1/6 | 8 | Introduction to Data Analysis and Programming | 5 | — | 2.409 | 4,0 |
| Research Fundamentals 2/6 | 10 | Statistics and Basic Data Analysis | 6 | — | 514 | — |
| Research Fundamentals 3/6 | 11 | Regression Analysis | 8 | — | 299 | — |
| Research Fundamentals 4/6 | 12 | Statistical Inference | 4 | — | 153 | — |
| Research Fundamentals 5/6 | 13 | Financial and Risk Analysis | 12 | — | 272 | — |
| Research Fundamentals 6/6 | 14 | Advanced Data Analysis and Algorithmic Trading | 15 | — | 334 | — |

Research Fundamentals serisi = Quantopian Lecture Series uyarlaması, 6 kurs / **50 ders**.

**Metadata güvenilmez:** API `workload` alanı 104 ve tüm Research kursları için `"0 interactive lesson"` diyor, gerçekte ders var. Ders açıklamalarının çoğu `"Empty lesson description"`. Bakım zayıf.

### Ücretli dış bağlantılar (3, Udemy'ye yönlendirme)
Complete Algorithmic Trading Course (Cheng Li) · Python for Finance and Algorithmic Trading with QuantConnect (Jose Portilla) · Crypto Trading with QuantConnect C# (Eric Summers). Katalog API'sinde yok, yalnız kart olarak görünüyor.

### Makale serileri (116 makale, ücretsiz, kayıt gerekmez)
`https://www.quantconnect.com/learning/articles`

| Seri | Adet |
|---|---|
| Investment Strategy Library | 83 |
| Introduction to Financial Python | 14 |
| Introduction to Options (Options Theory) | 8 |
| Applied Options | 8 |
| Alternative Data | 3 |

**Bu, kataloğun en değerli katmanı:** makaleler tam Python kodu içeriyor ve enrollment gerektirmiyor.

---

## 2. Kova 1 — PLATFORM TEKNİĞİ

Ana kaynak: `https://www.quantconnect.com/learning/course/1/boot-camp-101-us-equities`

| Ders | Görev zinciri | Meridian iş akışına maddesi |
|---|---|---|
| L1 Buy and Hold / Equities | Set Starting Cash → Set Date Range → Manually Selecting Data → **Set Data Normalization Mode** → Checking Holdings → Placing Orders | `raw` vs `adjusted` normalizasyon ayrımı — PIT fiyat disiplinimizle doğrudan kesişir |
| L2 Trailing Stop | Stop Market Order → **Order Events** → Stop Loss Hit tespiti → Trailing Stop → seviyeleri plot | Emir yaşam döngüsü + "LEAN destekliyor ama brokeriniz desteklemeyebilir" uyarısı (canlı/backtest sapması) |
| L4 Opening Range Breakout | **Consolidator** oluştur → Bar Data ve Bar Time → consolidator çıktısı → **Scheduled Events** | Özel bar üretimi; intraday ölçüm kartları için |
| L5 Liquid Universe Selection | **Coarse Universe Filter** → CoarseFundamental nesneleri → **Tracking Security Changes** → portföy → `universe_settings` özelleştirme | Evren tanımı + evren değişiminde durum yönetimi (bizim RETIRED_SYMBOLS/evren bakımına en yakın ders) |
| L6 Fading The Gap | Scheduled Events → **RollingWindow** oluştur/eriş → **"Reducing a Parameter"** | RollingWindow reçetesi; ayrıca sabit eşiği stddev indikatörüyle değiştirip **parametre sayısını düşürme** — bu bir ölçüm-disiplini fikri, aşırı-uydurmaya karşı |
| L7 200-50 EMA Momentum Universe | Universe temeli → **sınıfla veri gruplama (SymbolData)** → sınıfı universe'e uygula → **`history()` ile indikatör ısıtma** | Evrene yeni giren sembolde indikatör soğuk-başlangıç problemi — EDG tarzı ölçümlerde klasik tuzak |
| L8 The Algorithm Framework | Framework Overview → UniverseSelection → Alpha → PortfolioConstruction → Risk → Execution | 5 modüllü ayrıklık sözleşmesi; sinyal ile sermaye tahsisini ayırma |
| L10 Liquid Value Stocks | **Fundamental Universe** talebi → likit seçim → **Fine Selection özellikleri** → fundamental veriyle insight | İki aşamalı coarse→fine fundamental filtre; aylık rebalance |
| L11 Tiingo Sentiment | Alternatif veri tanıtımı → **alt veri ekleme** → **algoritma verisini bakımda tutma** → insight emisyon yönetimi | Alt-dataset abonelik yaşam döngüsü (evren değişince abonelik ekle/kaldır) |
| L12 Sector Weighted PCM | Sektöre göre evren → Sector Weighting PCM → security changes → hedef ağırlık yüzdeleri | Morningstar sektör kodlarıyla gruplama + PortfolioTarget'ları Execution modeline devretme |

Diğer Boot Camp'lerden alınabilecek tek maddeler:
- **102/FOREX** (`/learning/course/2/boot-camp-102-forex`): `set_brokerage_model`, quote fiyatına erişim, **lot boyutuna yuvarlama**. Varlık sınıfımız değil ama brokerage-model kavramı taşınabilir.
- **103/Futures** (`/learning/course/3/boot-camp-103-futures`): contract chain'i **open interest**'e göre sıralama/filtreleme, contract multiplier, **margin call yönetimi**.
- **104/Options** (`/learning/course/4/boot-camp-104-options`): option chain gezinme, volatility model kurma.

### Makalelerden çıkan **doğrulanmış** kod reçeteleri

**R1 — İki aşamalı fundamental evren + aylık scheduled rebalance**
`https://www.quantconnect.com/learning/articles/investment-strategy-library/stock-selection-strategy-based-on-fundamental-factors`
Sayfadan birebir okunan çağrılar:
```
self.universe_settings.resolution = Resolution.DAILY
self.add_universe(self.coarse_selection_function, self.fine_selection_function)
self.schedule.on(self.date_rules.month_start("SPY"),
                 self.time_rules.after_market_open("SPY"), Action(self.rebalancing))
```
- Coarse aşaması: `x.has_fundamental_data` ile **ETF'leri ele** (fundamental verisi olmayanlar), `x.dollar_volume` ile sırala, top-N al, `i.symbol` döndür.
- Fine aşaması: sıfır faktör değerlilerini at, faktöre göre sırala. Erişilen alan örnekleri: `x.valuation_ratios.pe_ratio`, `x.financial_statements.total_risk_based_capital.twelve_months`.
- Rebalance frekansını flag değişkenleriyle kontrol edip **evren yenilemesini günlükten aylığa düşürme** kalıbı (universe varsayılan olarak her gün yenileniyor).
- Tarihsel veri: `self.history(20, Resolution.DAILY)`.

**R2 — Alpha modeli içinde sembol-başı durum yaşam döngüsü**
`https://www.quantconnect.com/learning/articles/investment-strategy-library/gradient-boosting-model`
```
symbols = [ Symbol.create("SPY", SecurityType.EQUITY, Market.USA) ]
self.set_universe_selection( ManualUniverseSelectionModel(symbols) )
self.universe_settings.resolution = Resolution.MINUTE
```
`AlphaModel.on_securities_changed(self, algorithm, changes)` içinde `changes.added_securities` → `SymbolData` yarat, `changes.removed_securities` → `pop`. Evren dalgalanırken sembol-başı tampon/indikatör sızıntısını önleyen kanonik kalıp.

> **Bayatlık uyarısı — önemli.** BC101'in L5, L7, L10, L12 derslerinin sayfalarında QC'nin kendi notu var: *videolar deprecated Legacy Universe'ü anlatıyor, bunun yerine ders içindeki modern birleşik sürümü kullanın.* ISL makaleleri hâlâ coarse+fine ikili imzasını kullanıyor. Yani **video katmanı ve makale kodu API açısından bayat**; reçeteler docs ile çapraz doğrulanmadan kopyalanmamalı.

---

## 3. Kova 2 — METODOLOJİ (örtüşme / çelişki)

### Örtüşenler (standartlarımızı destekliyor)

| Ders | URL | Not |
|---|---|---|
| **p-Hacking and Multiple Comparisons Bias** (C12 L3) | `/learning/course/12/statistical-inference` | **En yüksek değerli metodoloji dersi.** K grid'de çarparak sayma kuralımızın literatür gerekçesi burada |
| **The Dangers of Overfitting** (C11 L8) | `/learning/course/11/regression-analysis` | Regresyon bağlamında aşırı uydurma |
| Instability of Estimates (C10 L5) | `/learning/course/10/statistics-and-basic-data-analysis` | Tahminlerin zaman içinde kayması — eşik sabitleme disiplinimizin nedeni |
| Regression Model Instability (C11 L3) + Model Misspecification (L6) + Residual Analysis (L7) | `/learning/course/11/...` | Model kırılganlığı üçlüsü |
| Introduction to Volume, Slippage, and Liquidity (C13 L4), Market Impact Models (C13 L5) | `/learning/course/13/financial-and-risk-analysis` | Backtest→canlı sapmasının kaynakları |
| Factor Analysis with Alphalens (C14 L3) | `/learning/course/14/advanced-data-analysis-and-algorithmic-trading` | Faktör değerlendirme çerçevesi |
| Integration, Cointegration, and Stationarity (C14 L6) | aynı | Durağanlık testleri |
| Position Concentration Risk (C13 L2), Factor Risk Exposures (C13 L11), VaR/CVaR (C14 L5) | — | Risk ölçüm katmanı |

**Kültürel örtüşme (kayda değer):** `gradient-boosting-model` makalesi, referans aldığı Zhou et al. (2013) çalışmasının **Sharpe > 20** iddiasını reprodüksiyonda tutturamadığını ve modelin 5 yıllık backtest'te **SPY'ın altında kaldığını** açıkça yazıyor. Ayrıca yazarların özel kayıp fonksiyonlarının "kötü tahminlere yol açtığını" belirtiyor. Bu, bizim UYDURMA YASAĞI / kanıtla-iddia-etme ilkemizle birebir örtüşen, kataloğun en dürüst parçası.

### Çelişenler / boşluklar (kayda geçirilecek)

1. **Walk-forward analizi katalogda YOK.** Purged/embargoed cross-validation YOK. Deflated Sharpe / çoklu-test düzeltmeli performans metriği YOK. Kombinatoryal CV YOK. C12 L3 problemi *tanımlıyor* ama backtest bağlamında *çözüm reçetesi vermiyor*.
2. **Ön-kayıt (pre-registration) kavramı hiç yok.** Bizim `research/cards/` disiplininin, dokunulmaz kill-list'in, "eşik sonradan değişmez" kuralının karşılığı katalogda mevcut değil. Bu bir çelişki değil, **bizim üstünlüğümüz** — QC materyali bunu hiç kurmuyor.
3. **QC materyali kendi içinde çelişiyor.** `stock-selection-strategy-based-on-fundamental-factors` makalesi faktör "anlamlılığı" için post-hoc sabit eşikler koyuyor (sıralama-getiri korelasyonunun |ρ| > 0,8 olması gibi), tüm örneklem in-sample, çoklu-karşılaştırma düzeltmesi yok, out-of-sample doğrulama yok — yani C12 L3'ün uyardığı p-hacking'in ders kitabı örneği. **Hüküm: ISL makaleleri "nasıl kodlanır" için iyi kaynak, "kanıt" için kaynak değil.**
4. **Research Fundamentals serisi bakımsız.** Quantopian (2020'de kapandı) uyarlaması; API'de ders açıklamaları boş; puan/kayıt sayıları çok düşük (153–2.409). İçerik iyi ama güncellenmiyor.
5. Kullanıcı yorumlarında tekrar eden şikâyet: çözüm kodları bile derlenmiyor, IDE takılıyor, LEAN sözdizimi eskimiş (2024–2025 tarihli yorumlar).

---

## 4. Kova 3 — ALAKASIZ (tek satır)

- **BC102 / FOREX, BC103 / Futures, BC104 / Options** — varlık sınıfı dışı; yalnız yukarıda not edilen tek maddeleri taşınabilir.
- **Course 5, Algorithmic Trading A-Z (17 video)** — üçüncü taraf giriş videosu, etkileşimli görev yok, yeni bilgi yok.
- **C8 Introduction to Data Analysis and Programming** — Python/NumPy/pandas/matplotlib girişi.
- **C10 Statistics and Basic Data Analysis** — ortalama/varyans/çarpıklık/basıklık; L5 (Instability of Estimates) hariç temel.
- **Introduction to Options serisi (8 makale)** — Black-Scholes, Yunan harfleri, put-call paritesi; opsiyon dışı.
- **Applied Options serisi (8 makale)** — iron condor, straddle, butterfly vb.; opsiyon dışı.
- **Introduction to Financial Python serisi (14 makale)** — temel Python + istatistik.
- **ISL'nin 83 makalesinin büyük çoğunluğu** — strateji fikri kataloğu (momentum/mean-reversion/mevsimsellik varyantları). Meridian'ın kendi öğrenme döngüsü var; fikir kaynağı olarak düşük öncelik. Yalnızca *uygulama kalıbı* taşıyanları (yukarıdaki R1/R2) süzdüm.
- **3 ücretli Udemy kursu** — dış platform, ücretli, giriş seviyesi.

---

## 5. Katalogda YOK, docs'ta VAR — asıl aksiyon

Görevde adı geçen "ObjectStore" ve "research→backtest köprüsü" **`/learning` kataloğunda hiç geçmiyor.** Tarama sırasında incelenen hiçbir kurs/makale ObjectStore'a değinmiyor. Bunlar dokümantasyonda:

- **ObjectStore** — `https://www.quantconnect.com/docs/v2/writing-algorithms/object-store` (16 alt sayfa). Bizim için doğrudan ilgili olanlar: *Save/Read Data*, *Example for DataFrames*, *Storage Quotas*, **Preserve Insights Between Deployments** (yeniden dağıtım arası durum korunması — bizim state/ disiplinimizin QC karşılığı), *Live Trading Considerations*.
- **Research → backtest köprüsü** — `https://www.quantconnect.com/docs/v2/research-environment/applying-research/key-concepts` + 9 tutorial (Mean Reversion, Random Forest Regression, Uncorrelated Assets, Kalman Filters & Stat Arb, PCA & Pairs Trading, Hidden Markov Models, LSTM, Airline Buybacks, Sparse Optimization).
- **Meta Analysis** — `https://www.quantconnect.com/docs/v2/research-environment/meta-analysis/key-concepts` — backtest/optimizasyon/canlı sonuçlarını notebook'ta analiz etme. **Karne/ölçüm iş akışımıza kataloğun tamamından daha yakın olan tek yer bu.**
- **Custom data** — katalogda yalnız Course 5 L9'da (video, üçüncü taraf) var; gerçek referans `docs/v2/writing-algorithms/importing-data`.

**Öneri:** defter-v3 girdisi için asıl kaynak `/learning` değil, `research-environment/{applying-research, meta-analysis, object-store}` üçlüsü. `/learning`'den alınacaklar yukarıdaki R1/R2 + BC101 L5/L7/L11/L12'nin evren-yaşam-döngüsü kalıpları ile sınırlı.

---

## 6. Operatöre kişisel değer (kısa)

- **Sertifika yok.** Kurs sayfalarında sertifika/rozet mekanizması bulunmuyor; yalnız yüzde ilerleme, "In Progress / Completed / Wish List" sekmeleri ve yıldız puanı var. CV değeri sıfır.
- **Hepsi ücretsiz** (platform içi 11 kursun tamamı `price: 0`).
- Süre: BC101 ≈ 56 etkileşimli görev + ~90 dk video → 6–8 saat. Diğer 3 Boot Camp toplam ~1 saat.
- **Eğer QC'ye canlı dağıtım gündeme gelirse** BC101'in yalnız L1, L2, L5, L8'i (LEAN idiomları, order events, evren, framework) yeterli; kalan 8 ders trading öğretiyor, bizim için değersiz.
- **Kayıt gerekli:** görev metni ve çözüm kodları enroll olmadan okunamıyor. Bu turda hesabınıza hiçbir kayıt yapılmadı; ders içeriğine ihtiyaç olursa enroll etme kararı sizde.
