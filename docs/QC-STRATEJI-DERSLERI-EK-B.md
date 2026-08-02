# EK-B — QC Strategy Library bileşen-dersleri (2026-08-03)

Katalog taraması tamam. Rapor:

---

# QuantConnect Strategy Library → Meridian eşlemesi

## 0. DÜRÜSTLÜK ŞERHİ (önce okunmalı — çerçeveyi değiştiriyor)

QC yazımlarının performans iddiaları bizim yasalarımızdan geçmedi; dersler **mekanizma düzeyinde** alındı, sayı taşınmadı. Ama tarama sırasında bundan daha sert bir şey çıktı:

**Kataloğun "kazanan" kümesi neredeyse boş.** QC'nin kendi yazımında benchmark kıyası bastığı 6 stratejinin 5'i, QC'nin KENDİ sayılarıyla SPY'nin altında:

| Strateji | QC'nin kendi bastığı sayı |
|---|---|
| 357 Commodities Trend Following | Sharpe **−0,131** |
| 271 Price & Earnings Momentum | Sharpe **−0,268** (SPY 0,758) |
| 269 Seasonality same-month | Sharpe **0,128** (SPY 0,773) |
| 211 Mean-Reversion StatArb | ~%6/yıl, maxDD **~%49** |
| 353 Fama-French 5 Factor | ~%6,8/yıl, maxDD %19,8 |
| 354 Expected Idio. Skewness | Sharpe 0,947 (SPY 0,87) — **tek net geçen** |

Sonuç: Strategy Library bir **kazanan deposu değil, literatür-uygulama deposu**. Dolayısıyla aşağıdaki bileşen dersleri "başarısı kanıtlanmış desen" olarak değil, **mühendislik konvansiyonu** olarak etiketlenmeli — "bu alanı uygulayanlar şunu yapıyor", "bu para kazanıyor" değil. Gerçek "kazanan" listesi **Strategy Explorer**'da (community canlı, skor = 1-yıl Sharpe + <1yıl OOS cezası, QC her gün yeniden backtest ediyor) ve orayı **enumerate EDEMEDİM** — JS-render + hesap kapısı. **Operatör QC hesabını 2026-08-03'te açtı (EDG-021 notu): Explorer envanteri artık erişilebilir ve asıl kazanan-madenciliği ORADA.** Bu, bu turun kapanmamış tek kapısı.

---

## A. BİLEŞEN-BAZLI DERS ÇIKARIMI (asıl teslimat)

### (1) ÇIKIŞ / TRAILING MİMARİSİ

**Katalog bulgusu — güçlü ve tek yönlü:** Kesitsel hisse kütüphanesinin TAMAMINDA çıkış **takvim-kaynaklı**, durak-kaynaklı değil. Stop-loss'un açıkça yok olduğu yazımlar: [Commodities Futures Trend Following](https://www.quantconnect.com/tutorials/strategy-library/commodities-futures-trend-following) ("no stops, no trailing stops, no time-based exits"), [Optimal Pairs Trading](https://www.quantconnect.com/tutorials/strategy-library/optimal-pairs-trading) ("no stop-loss or time-stop provisions"), [Improved Momentum on Commodities Futures](https://www.quantconnect.com/tutorials/strategy-library/improved-momentum-strategy-on-commodities-futures) (yalnız ±%100 clip). 83 yazımda ratchet'li trailing stop **bulunamadı**.

**En bilgilendirici istisna — [Dynamic Breakout II](https://www.quantconnect.com/tutorials/strategy-library/the-dynamic-breakout-ii-strategy):** çıkış eşiği = uyarlanan lookback penceresinin kapanış ORTALAMASI, ve pencere volatiliteyle birlikte 20–60 gün arasında **genişliyor** (`numdays = round(numdays * (1 + deltavol))`).

- **Bizim tasarımla FARK (tek cümle):** Bizim chandelier bir RATCHET — tek yönlü yukarı kilitleniyor; DBII'nin eşiği ratchet DEĞİL ve vol arttığında **gevşiyor**, yani tam da bizim "durak maliyeti" bulgumuzun (chandelier kapatınca CAGR artıyor) mekanizma açıklaması: ratchet, vol genişlemesinde tam ters yönde sıkışıp en kötü anda çıkartıyor.
- **Kart cümlesi:** "Ratchet olmayan, volatiliteyle GENİŞLEYEN çıkış eşiği (uyarlanan N-gün ortalaması, N∈[20,60], vol-oranıyla ölçekli), chandelier ratchet'ine kıyasla ~63g tutuşta taban-fazlasını kaybetmeden maxDD'yi kötüleştirmez — hüküm: taban-fazlası KORUNUP maxDD düşerse P3 çıkış-paketi hükmü mekanizma-düzeyinde revize edilir."

**İkinci ders — KISMİ ÇIKIŞ olarak örtüşük takvim dilimleri:** [Combining Momentum with Volume](https://www.quantconnect.com/tutorials/strategy-library/combining-momentum-effect-with-volume) 3-ay tutuşu **her ay 1/3 dilim** ekleyip 3-ay-eskiyi tasfiye ederek kuruyor; [Momentum+Reversal+Volatility](https://www.quantconnect.com/tutorials/strategy-library/momentum-and-reversal-combined-with-volatility-effect-in-stocks) 6-ay tutuşu **1/6 aylık dilimle**. Bu, portföy düzeyinde kısmi-çıkış.

- **FARK:** Bizde giriş/çıkış pozisyon-atomik (tek seferde tam 1R girip tam çıkıyoruz); dilim yapısı tutuş süresini rebalans frekansından **ayırıyor**.
- **Kart cümlesi:** "Aynı sinyalle ~63g tutuşu tek-seferde değil 1/3'lük aylık örtüşük dilimlerle kurmak, taban-fazlası ORTALAMASINI değiştirmeden CI'yı daraltır — hüküm ortalamada değil CI genişliğinde ve giriş-zamanlaması varyansında aranır."

### (2) BOYUTLAMA / RİSK

**Katalogdaki en olgun boyutlama makinesi:** [Baltas-Kosowski TSMOM-CF](https://www.quantconnect.com/tutorials/strategy-library/improved-momentum-strategy-on-commodities-futures) — ağırlık ÜÇ ÇARPANIN çarpımı:

1. **Sürekli trend-gücü** `X ∈ [−1,+1]`: 12-aylık günlük log-getirilerin **t-istatistiği**; |t|>1 → %100 maruziyet, |t|<1 → orantılı kısılma.
2. **Ters-vol**: `σ_hedef / σ_i`, portföy hedef vol %12, birim vol **Yang-Zhang** tahmincisiyle (gecelik boşluk + gün-içi aralık dahil).
3. **Korelasyon çarpanı**: `CF(ρ̄) = √(N / (1 + (N−1)ρ̄))`, ρ̄ = son 3 ayın ortalama ikili korelasyonu.

**Bizim EDG-008 hükmüyle ÇELİŞİYOR MU? — Hayır, ve bu ayrım önemli.** EDG-008 vol-scaling'i **zaman-serisi** kaldıracı olarak ölçtü (Moreira-Muir / Barroso-Santa-Clara: defterin tamamını kendi geçmiş volüne göre ölçekle) ve yönsüz buldu. Baltas-Kosowski'nin (2) maddesi **kesitsel risk-paritesi** (sepet İÇİNDE isimler arası), (3) maddesi ise vol değil **çeşitlenme** ölçüsü. Yani EDG-008 hükmü ayakta kalır; ama **iki ayrı ölçülmemiş kol** var.

- **FARK:** Bizde sabit 1R + zaman-serisi de-risk rampası (günlerin %92'sinde aktif, işlem-boğucu ölçüldü); burada isim-bazlı ters-vol + korelasyon-bazlı brüt kısıntı, ve rampa yerine **rejim değil çeşitlenme** kaldıracı çekiliyor.
- **Kart cümlesi A:** "Aday sepeti içinde eşit-1R yerine ters-vol ağırlık (Yang-Zhang, günlük OHLC'den — ek veri gerekmez), aynı 5R ısı tavanı altında @20/@63 taban-fazlasını artırır."
- **Kart cümlesi B (daha yüksek değerli):** "Ortalama ikili korelasyon ρ̄(63g) yükseldiğinde brüt maruziyeti CF(ρ̄)=√(N/(1+(N−1)ρ̄)) ile kısmak, günlerin %92'sinde aktif olan işlem-boğucu de-risk rampasının yerini alarak maxDD'yi işlem sayısını boğmadan düşürür — hüküm: işlem sayısı KORUNURKEN maxDD düşerse rampa emekli edilir."

### (3) TUTUŞ / REBALANS

**Desen:** Ufuk sinyalin veri-tazelenme hızına kilitli, keyfi değil — fiyat-sinyalleri aylık ([Momentum Effect in Stocks](https://www.quantconnect.com/tutorials/strategy-library/momentum-effect-in-stocks), [Short Term Reversal](https://www.quantconnect.com/tutorials/strategy-library/short-term-reversal)), kazanç-sinyalleri çeyreklik, bilanço-sinyalleri **yıllık ve Haziran sonunda** ([Earnings Quality](https://www.quantconnect.com/tutorials/strategy-library/earnings-quality-factor), [Asset Growth](https://www.quantconnect.com/tutorials/strategy-library/asset-growth-effect) — Fama-French konvansiyonu, PIT güvenliği için).

**Hijyen detayı:** 155 sinyal penceresinden **ay-sonu öncesi son haftayı dışlıyor** ("to avoid biases due to microstructures").

- **FARK:** Bizim aylık-rebalans rafinesi "farksız" çıktı — ama ölçülen REBALANS FREKANSIYDI, dilim YAPISI değil; ayrıca sinyal penceresinin kuyruğunu kesme hijyenimiz yok.
- **Kart cümlesi:** "Sinyal penceresinin son 5 gününü dışlamak (ay-sonu mikroyapı/likidite artefaktı) taban-fazlasını düşürmez; düşmüyorsa sinyal mikroyapıya değil bilgiye dayanıyor demektir — bu bir POZİTİF KONTROL kartı, edge kartı değil."

### (4) EVREN KURULUMU

**Desen — istisnasız:** iki aşamalı **dinamik** huni, her ay yeniden koşuyor. Coarse: fiyat > $4–5, fundamental var, ADR/ETF/kapalı-uçlu fon hariç → **dolar-hacim üst-N** (modal N = 100; 20/200 de var). Fine: piyasa değeri üst-K, sektör dışlaması (finans + kamu hizmetleri, kalite/muhasebe kartlarında standart). Nihai portföy 10–50 isim.

**En keskin gözlem:** QC evreni **dolar-hacimle KURUYOR**; bizim YAŞAYAN kenarımız (EDG-016 turnover üst-%20) aynı ailedeki değişkeni **SIRALAYICI** olarak kullanıyor. Bu, "seçici mi sıralayıcı mı" sorusunu doğuruyor — statik 251'de turnover sıralayıcı olarak para getiriyor; dinamik evrende aynı bilginin bir kısmı evren düzeyinde zaten tüketilmiş olabilir.

- **FARK:** Bizim 251 statik-yakın; QC'nin evreni her ay yeniden doğuyor ve likidite ekseni evrenin İÇİNE gömülü.
- **Kart cümlesi:** "Statik 251 yerine aylık dolar-hacim üst-N dinamik evren kurulduğunda EDG-016 turnover üst-dilim kenarı KÜÇÜLÜR (bilgi evrene taşınmıştır) ya da KORUNUR (bilgi sıralamada) — iki tasarım yan yana ölçülür; fark, kenarın nereden geldiğinin doğrudan ölçüsüdür." *(Not: bu kart EDG-021 QC delist doğrulamasıyla aynı motorda koşabilir — evren tanımı zaten orada tartışılıyor.)*
- **İkinci kart cümlesi:** "Finans + kamu-hizmeti sektörlerinin evrenden dışlanması (muhasebe/kalite ailesinde evrensel konvansiyon) taban-fazlasını değiştirmez."

### (5) SİNYAL BİRLEŞİMİ / SKOR

Katalogda **dört ayrı** birleşim deseni, karmaşıklık sırasıyla:

- **(a) İkili-bayrak toplamı** — [G-Score](https://www.quantconnect.com/tutorials/strategy-library/g-score-investing): 7 koşul, her biri 1 puan, 0–7 tamsayı, yalnız ≥5 alınır. Ağırlık yok, uydurulacak parametre yok.
- **(b) Sıra-toplamı (rank-sum)** — [Earnings Quality](https://www.quantconnect.com/tutorials/strategy-library/earnings-quality-factor) (4 faktörün ordinal sıraları toplanır), [Price & Earnings Momentum](https://www.quantconnect.com/tutorials/strategy-library/price-and-earnings-momentum) (2 sıra toplanır).
- **(c) Ağırlıklı sıra-ortalaması** — [Fama-French 5](https://www.quantconnect.com/tutorials/strategy-library/fama-french-five-factors): sıra × beta_i, ortalanır. **Tek uydurulan-ağırlıklı desen ve QC'nin kendi sayısıyla en zayıflarından biri (%6,8/yıl, %19,8 maxDD).**
- **(d) KOŞULLU ARDIŞIK SIRALAMA (double sort)** — 66: önce momentum decile, SONRA o decile İÇİNDE turnover; 155: önce vol quintile, SONRA üst-vol quintile İÇİNDE 6-ay getiri. Toplamsal değil, **koşullandırıcı** yapı.

- **FARK:** Bizim skor toplamsal-ekonomik (PARA-v3) + bileşen-IC. (d) deseni "ikinci sinyal yalnız birincinin tanımladığı alt-popülasyonda bilgilidir" der. **Bu bizde kısmen CEVAPLI:** EDG-013 (mom×turnover etkileşimi) arşivlendi, EDG-016 ana-etkiyi kurdu — yani mom×turnover çifti için toplamsal ana-etki koşullandırmayı yendi. Ama **vol-quintile-önce** koşullandırması (155) hiç ölçülmedi.
- **Kart cümlesi A:** "İkili-bayrak toplamı tarzı monoton tamsayı skor (0–K, eşik ≥m), sürekli-ağırlıklı skora kıyasla K-cezası ucuz ve aşırı-uydurmaya dayanıklı; mevcut PARA-v3 sıralamasıyla yan yana @20 taban-fazlası kıyaslanır."
- **Kart cümlesi B:** "Üst-vol quintile İÇİNDE momentum sıralaması, tüm-evren momentum sıralamasından fazla taban-fazlası üretir (155 koşullandırması) — EDG-004'ün ters-yön MAX bulgusuyla aynı yönde bir öngörü taşıdığı için ucuz bir tutarlılık sınavıdır."
- **NEGATİF BULGU (dürüstlük):** Katalogda **rejim-koşullu sinyal AĞIRLIĞI örneği YOK.** 91 "Style Rotation" adına rağmen düz bir momentum çift-işlemi çıktı. Yani (5)+(6) kesişimi için katalogdan alınacak ders yok.

### (6) REJİM

**Katalogdaki rejim kurgularının hepsi KAPI:** [Momentum & State of Market](https://www.quantconnect.com/tutorials/strategy-library/momentum-and-state-of-market-filters) (Wilshire 12-ay getiri işareti → momentum AÇIK, değilse %100 TLT), [Asset Class Trend Following](https://www.quantconnect.com/tutorials/strategy-library/asset-class-trend-following) (10-ay SMA → içerde ya da nakit), [Leveraged ETFs](https://www.quantconnect.com/tutorials/strategy-library/leveraged-etfs-with-systematic-risk-management) (200-gün SMA → SSO ya da SHY; yazım açıkça "complete on/off switch, not a position-size modulator" diyor), [VIX Predicts](https://www.quantconnect.com/tutorials/strategy-library/vix-predicts-stock-index-returns) (90./10. persentil → tam long/tam short).

**TEK istisna — ve tam da aradığınız desen:** Baltas-Kosowski **TREND kuralı**. 12-aylık günlük log-getirilerin t-istatistiği [−1,+1] aralığına kırpılarak **sürekli maruziyet çarpanı** olarak kullanılıyor. Kapı değil, **kadran**. Bu, bizim EDG-005 hükmümüzle ("SMA kapısı volü düşürür ama parayı da düşürür") **uyumlu** olan katalogdaki tek yapı.

**İkinci, daha zayıf ders:** 37 ve 1025'te "kapalı" durum nakit değil **tahvil** — kapatılan risk boşta durmuyor.

- **FARK:** Bizim SMA-200 kapımız ikili ve kapalı durumda düz; burada rejim sürekli bir ÇARPAN ve kapalı durum getiri üretiyor.
- **Kart cümlesi (bu turun en yüksek değerli rejim kartı):** "SPY 12-ay günlük log-getirisinin t-istatistiği, [−1,+1] kırpılmış SÜREKLİ maruziyet çarpanı olarak (kapı DEĞİL) uygulandığında, taban-fazlası KORUNURKEN maxDD düşer → EDG-005 hükmü 'kapı yanlış, modülasyon doğru' diye daraltılır; taban-fazlası da düşerse EDG-005 hükmü ('rejim müdahalesi parayı düşürür') mekanizmadan bağımsız olarak TEYİT edilir ve rejim ailesi kapanır."
- **Veri şerhi:** QC'nin kullandığı Wilshire 5000 FRED serisi **kapatılmış** — yazımın kendi veri bağımlılığı ölü. Ücretsiz vekil: SPY. Bu, QC yazımlarının bakımsız olabileceğinin de kanıtı.

---

## B. KATALOG YAPISI

- **Envanter:** GitHub'da 85 klasör; bunların 2'si dizin sayfası (`00 Strategy Library`, `26 Quantpedia`) → **83 yayımlı yazım, 82 gerçek strateji**. Numaralandırma bitişik değil: Quantpedia kaynaklı ID'ler (58, 61, 66 … 357) + QC-özgün seri (1023–1036).
- **Her girdinin yapısı:** düzyazı makale (tez + akademik atıf) + tam Python kaynak (eski girdilerde C# de) + gömülü QC backtest'i ve kendi metrikleri. Kategori/etiket taksonomisi **yok** — düz liste.
- **Lisans (net):** `QuantConnect/Tutorials` deposu **Apache License 2.0** — türev eser serbest; şartlar: lisans kopyası, değişiklik bildirimi, telif/atıf notlarının korunması; ticari marka izni verilmiyor; garanti yok. Site içeriği ayrıca "© QuantConnect, All Rights Reserved". **Community Strategy Explorer stratejileri için açık lisans belgelenmemiş** → oradan kopya alınmaz, yalnız fikir okunur.
- **İki AYRI şey karıştırılmamalı:** `/tutorials/strategy-library/*` = literatür uygulamaları (yukarıdaki 82). `/strategies` = Strategy Explorer, community canlı algoritmaları, skor = 1-yıl Sharpe + <1yıl OOS cezası, QC her gün yeniden backtest ediyor, lider tablosu ilk 10'u gösteriyor. **Enumerate edilemedi (JS + hesap kapısı).**

---

## C. KOVA SAYILARI

| Kova | Sayı |
|---|---|
| **(a) Bizde ölçüldü / arşiv-örtüşmesi** | **29** |
| **(b) Yeni kart-adayı** | **8** |
| **(c) Uygulanamaz** | **45** |
| *(dizin sayfası, strateji değil)* | *1* |
| **Toplam yazım** | **83** |

**(a) kovasındaki MEKANİZMA-VARYANTI işaretlileri (bizim ölçmediğimiz açı taşıyanlar):**
- **24 Liquidity Effect** → EDG-016 (YAŞAYAN) — **yön TERS**: QC/Quantpedia **düşük** turnover'a long, üstelik en küçük-cap çeyreğinde ve **yıllık** rebalansla; bizim yaşayan kenarımız large-cap'te **yüksek** turnover @20. İki bulgu çelişmiyor (evren+ufuk farklı) ama bu, EDG-016'nın "evren-koşullu mu evrensel mi" sorusunu doğuruyor. [URL](https://www.quantconnect.com/tutorials/strategy-library/liquidity-effect-in-stocks)
- **66 Momentum×Volume** → EDG-013/016 — varyant: 3-ay tutuş + 1/3 örtüşük dilim (bizde ölçülen @20 idi)
- **37 State of Market** → EDG-005 — varyant: SMA yerine 12-ay getiri işareti + kapalı durumda tahvil
- **162 Momentum in Small Portfolios** → EDG-009 (YAŞAYAN) — **N=10 bizimkiyle birebir aynı**, ama yıllık tutuş (bizde ~63g)
- **21 Momentum Effect in Stocks** → EDG-009 — varyant: 50 en büyük, 12-ay, aylık, eşit ağırlık
- **155 Momentum+Reversal+Volatility** → EDG-004/008 — varyant: **vol-quintile-önce koşullu sıralama**
- **229 Earnings Quality / 1030 G-Score** → EDG-014 ailesi — varyant: **kompozit skor inşası** (bkz. bileşen 5)
- **01 CAPM Alpha Ranking** → EDG-007 — varyant: 21-günlük CAPM alfası (bizde 12-ay artık momentum)
- **39 Asset Growth** → EDG-012 komşusu — varyant: hisse ihracı yerine **toplam varlık** büyümesi

---

## D. (b) KOVASI — TAM LİSTE (8 aday)

Hepsi: **tez taşır, sayı taşımaz.**

**1. 354 Expected Idiosyncratic Skewness** — [URL](https://www.quantconnect.com/tutorials/strategy-library/expected-idiosyncratic-skewness)
- *Tez:* FF3 artıklarından hesaplanan idiyosinkratik vol ve çarpıklığın kesitsel regresyonla ÖNGÖRDÜĞÜ gelecek-ay çarpıklığı, düşük olduğunda large-cap @20 taban-fazlası pozitiftir (Boyer-Mitton-Vorkink: yüksek idio-çarpıklık → düşük beklenen getiri).
- *Veri:* günlük fiyat + Ken French kütüphanesi FF faktörleri — **FREE ✓**, NLP/analist kilidi yok.
- *Kill-riski:* **orta**. EDG-004 (MAX) ters yön verdi; bu kart onu ya açıklar ya da vol-ailesinin tümüyle bilgisiz olduğunu teyit eder.

**2. 16 Overnight Anomaly — özellik olarak** — [URL](https://www.quantconnect.com/tutorials/strategy-library/overnight-anomaly)
- *Tez:* Günlük getiriyi gecelik (kapanış→açılış) ve gün-içi (açılış→kapanış) bileşenlere ayırdığımızda, gecelik bileşenin 21-günlük toplamı @10–20 taban-fazlası taşır (Lou-Polk-Skouras "gece ve gündüz" ayrışması).
- *Veri:* mevcut OHLC barları — **ek veri SIFIR ✓** (open alanı zaten var).
- *Kill-riski:* **orta**. Tamamen yeni bir eksen; strateji değil ÖZELLİK olduğu için YAŞAYAN kola doğrudan takılabilir.

**3. 211 PCA-Artığı Kısa-Ufuk Ortalamaya Dönüş** — [URL](https://www.quantconnect.com/tutorials/strategy-library/mean-reversion-statistical-arbitrage-strategy-in-stocks)
- *Tez:* Fiyatların 3 ana bileşene (PCA) regresyonundan kalan artığın z-skoru −1,5'in altındayken large-cap @10 taban-fazlası pozitiftir.
- *Veri:* yalnız fiyat — **FREE ✓**. Long-only uyarlaması doğal (yalnız negatif-z tarafı alınır; RAF'taki koşullu-kısa kısıtına takılmaz).
- *Kill-riski:* **orta-yüksek**. EDG-007 artık MOMENTUM'u öldürdü ama artık DÖNÜŞÜ (kısa ufuk) ölçülmedi; öte yandan EDG-010 pullback'in ölümü kısa-ufuk dönüş ailesine karşı ön-yargı yaratıyor. QC'nin kendi sayısı %49 maxDD.

**4. 269 Same-Calendar-Month Seasonality** — [URL](https://www.quantconnect.com/tutorials/strategy-library/seasonality-effect-based-on-same-calendar-month-returns)
- *Tez:* Bir hissenin geçen yılın AYNI takvim ayındaki getirisi, bu yılın aynı ayı için kesitsel sıralama bilgisi taşır (Keloharju-Linnainmaa-Nyberg, "Common Factors in Return Seasonalities").
- *Veri:* yalnız fiyat, 13 ay geçmiş — **FREE ✓**. @20 ≈ 1 ay, ufkumuzla **uyumlu ✓**.
- *Kill-riski:* **orta-yüksek**. Bizim takvim ailesi (ToM, EAP, pre-holiday) tümüyle öldü — AMA hepsi ZAMAN-SERİSİ takvimiydi; bu KESİTSEL mevsimsellik, farklı eksen. QC'nin kendi Sharpe'ı 0,128 (SPY 0,773).

**5. 125 12-Month Cycle in Cross-Section** — [URL](https://www.quantconnect.com/tutorials/strategy-library/12-month-cycle-in-cross-section-of-stocks-returns)
- *Tez:* 4'ün özel hali — geçen yılın Ocak ayı performansı bu yılın Ocak'ını öngörür (t−365 ile t−335 gün arası getiri).
- *Veri:* yalnız fiyat — **FREE ✓**.
- *Kill-riski:* **yüksek**. 4 numaranın dar bir alt-kümesi; 4 ölçülürse bu ayrıca ölçülmemeli (K israfı). **4 ile aynı kartta bir grid hücresi olarak koşulmalı.**

**6. 77 Beta Factors in Stocks** — [URL](https://www.quantconnect.com/tutorials/strategy-library/beta-factors-in-stocks)
- *Tez:* SPY'ye karşı düşük-beta hisseler large-cap @20 taban-fazlası taşır (düşük-beta anomalisi).
- *Veri:* fiyat + SPY — **FREE ✓**.
- *Kill-riski:* **yüksek**. Vol ailesi bizde neredeyse tümüyle arşiv; dahası EDG-004'ün ters-yön bulgusu (yüksek-MAX daha iyi) düşük-beta tezinin TERSİNİ ima ediyor. Değeri edge olarak değil, **tutarlılık sınavı** olarak.

**7. 102 Option Expiration Week Effect** — [URL](https://www.quantconnect.com/tutorials/strategy-library/option-expiration-week-effect)
- *Tez:* Opsiyon vade haftasında (ayın 3. Cuma'sını içeren hafta) large-cap taban-fazlası sistematik olarak farklıdır.
- *Veri:* takvim + fiyat — **FREE ✓** (opsiyon verisi GEREKMEZ, yalnız takvim).
- *Kill-riski:* **çok yüksek**. Takvim ailesi bizde öldü (ToM kill#2 ön-adımda tetiklendi). Yalnız tamlık için listede.

**8. 14 Sektör-Göreli Momentum (uyarlanmış)** — [URL](https://www.quantconnect.com/tutorials/strategy-library/sector-momentum)
- *Tez:* Hissenin ham momentumundan kendi sektörünün momentumu çıkarıldığında kalan sektör-göreli momentum, ham momentumun üstünde taban-fazlası taşır.
- *Veri:* fiyat + sektör sınıflaması — **PIT ŞERHİ**: sektör ataması as-of değilse YASAK (PIT'siz fundamentals proxy yasağı).
- *Kill-riski:* **çok yüksek**. EDG-007'nin kill gerekçesi tam olarak "rawmom-örtüşmesi" idi; sektör-demeaning büyük olasılıkla aynı kill'e çarpar.

---

## E. ÖNCELİK SIRALI İLK 5 — ve bir uyarı

> **Uyarı:** (b) kovasının tamamının beklenen değeri, **A bölümündeki bileşen derslerinin altında.** Sekiz adayın hiçbiri YAŞAYAN kola dokunmuyor; A(1) ratchet-olmayan çıkış, A(2) korelasyon-çarpanı ve A(6) sürekli-rejim kartları ise doğrudan **mevcut, canlı, para kazanan** kolun üzerinde çalışıyor. K bütçesi kısıtlıysa sıra A'dan başlamalı.

(b) içinde sıralama:

1. **354 Expected Idiosyncratic Skewness** — tek gerekçe: arşivdeki bir sonucu (EDG-004 ters-yön MAX) **açıklama** potansiyeli taşıyan tek aday; yeni edge bulmasa bile bilgi üretir. Veri ücretsiz, mekanizma net.
2. **16 Overnight decomposition** — en ucuz gerçek yenilik: sıfır ek veri, sıfır PIT riski, tamamen ölçülmemiş eksen, ve strateji değil ÖZELLİK olduğu için YAŞAYAN kola takılabilir (ayrı motor gerektirmez).
3. **269 (+125 tek kartta)** — kesitsel mevsimsellik, bizim ölü takvim ailesinden yapısal olarak farklı eksen; @20 ufkumuza birebir oturuyor; 125 ayrı kart değil grid hücresi olmalı.
4. **211 PCA-artığı dönüş** — mekanizma temiz ve veri bedava, ama EDG-010'un ölümü kısa-ufuk dönüş ailesine karşı ağır ön-yargı bırakıyor; ancak 1–3 sonuçsuz kalırsa sıraya girmeli.
5. **77 Beta** — edge beklentisiyle değil, EDG-004'ün ters-yön bulgusunun **bağımsız doğrulaması** olarak; tek başına açılmamalı, 354 ile aynı kartta ikinci hücre olarak koşulmalı.

**Listelenmeyen 102 ve 14:** ön-yargı o kadar ağır ki tek başına K harcamaya değmez.

---

## Kapanmamış kapı + bir yan gözlem

- **Asıl kazanan madeni taranmadı.** Strategy Library literatür deposu ve QC'nin kendi sayılarıyla çoğunlukla SPY-altı. Gerçek "kazanan/olgun" küme Strategy Explorer'da ve enumerate edilemedi. Operatörün hesabı 2026-08-03'te açıldığına göre (EDG-021), **Explorer envanteri ayrı bir tur olarak koşulabilir** — orada bileşen dersleri hem daha güncel hem de OOS-cezalı bir skorla filtrelenmiş olur.
- **Yan gözlem (görev dışı, K-defteri bütünlüğü):** `research/cards/` dizininde **EDG-2026-019 yok** — 018'den 020'ye atlıyor. Kasıtlıysa sorun değil; değilse ön-kayıt defterinde numara boşluğu var.
