# QC ENTEGRASYON DEĞERLENDİRMESİ — 2026-08-03 (Rol-1 hükümlü)

> Kaynak: 7-ajanlık doküman-tarama Workflow'u (6 kol + sentez; yalnız resmî kaynaklar,
> her bulgu URL'li, sayılar aynen). /strategies bileşen-dersleri ve /learning süzgeci ayrı
> turlarda — indiklerinde bu dosyaya Ek-B/C olarak eklenecek.

## 0. ROL-1 HÜKMÜ (özet)

**ToS gerçeği delist-bar kararının yapısını değiştirdi:** QC verisi platformda serbest,
platformdan çıkarken kilitli (üç ayrı resmî yasak — log-export, scrape, 'internal LEAN use
only'). Yerel arşiv QC'yle DOLDURULAMAZ; QC/AlgoSeek verisi Meridian motoruna BESLENEMEZ
(para ödense bile). Dolayısıyla iki yol artık rakip değil TAMAMLAYICI:
- **(a) QC platform-içi ölçüm hattı — BUGÜN, BEDAVA:** EDG-021 deseni kalıcı yöntem olur;
  sinyaller delist-dahil evrende QC research'te kartla ölçülür, dışarı yalnız hüküm-sayısı
  taşınır. Hemen-yapılabilir kuyruk aşağıda (§2) — hepsi FREE.
- **(b) Massive plan yükseltmesi — YEREL ARŞİV YOLU (operatörde):** kendi motorumuzla ölçüm +
  gerçek arşiv ancak bu yolla dolar. QC bunu ikame etmez.
İkinci büyük kazanım: **LEAN motoru Apache-2.0** — CLI paid-tier ama motorun kendisi serbest;
KENDİ verimizle yerel diferansiyel ikinci-motor pilotu meşru ve bedava (WP-H adayı).

## 1. Uyum matrisi

### [1] delist-bar (iki yaşayan sinyalin delist edilmiş isimlerdeki gerçek büyüklüğü; yerel arşivde %96,6 boşluk)
- **Bileşen:** AlgoSeek US Equities (survivorship-bias-free, ~27.500 sembol, Ocak 1998+, delist dahil; https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/algoseek/us-equities) + US Equity Security Master (delist/sembol-değişim otoritesi, bulut algoritmalarında otomatik dahil; https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quantconnect/us-equity-security-master) + FREE R1-4 research node
- **Ücret:** Bulut içi ölçüm: FREE ('The QuantConnect data provider serves US Equities data for free'; FREE katman dakika–günlük çözünürlük). Yerel indirme alternatifi: paid tier + Security Master $600/yıl (QR) + Daily 100 QCC = $1/ticker (tüm tarihçe tek dosya) — kaynak: https://www.quantconnect.com/docs/v2/lean-cli/datasets/quantconnect/us-equity
- **Yol:** 1) FREE hesapta research notebook aç; 2) delist sembolü SecurityIdentifier.generate_equity(ticker, Market.USA, mapping_resolve_date=...) + Symbol(security_id, ticker) ile çöz (https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/security-identifiers); 3) qb.history ile günlük barları çek, Delisting/SymbolChangedEvent tarihçesini self.history(Delisting, ...) ile doğrula; 4) ölçümü research/cards ön-kayıt kartıyla PLATFORM İÇİNDE koş; 5) dışarı yalnız özet hüküm istatistiği elle taşı (bar verisi asla). Önce fizibilite: delist isimlerin Data Explorer kapsamı tek tek doğrulanmadı — ilk adım kapsam testi.
- **Riskler:** SERT ToS sınırı: barlar dışarı ÇIKARILAMAZ — 'you may not use the logs to export dataset information' (resources docs), Terms 3.3(b)(xvi) scrape yasağı, Security Master 'cannot be consumed another way'. Yani yerel arşiv boşluğu QC ile DOLDURULAMAZ, yalnız ölçülebilir. FREE log kotası 10KB/backtest zaten fiziksel engel. R1-4 4GB RAM + 15 dk hücre zaman aşımı. İndirme yolu seçilirse 'internal LEAN use only ... cannot be ... converted in any format' — Meridian motoruna besleme ihlal riski (operatör yorumu gerekir).

### [1] ikinci-motor (çapraz-doğrulama: aynı sinyaller, bağımsız motor, çıktı diff'i)
- **Bileşen:** İki yol: (a) LEAN motoru yerelde CLI'sız — Apache-2.0, hesapsız, dotnet/docker ile (https://github.com/QuantConnect/Lean) + custom data (PythonData + SubscriptionTransportMedium.LOCAL_FILE) veya native equity formatı (deci-cent OHLCV, ticker.zip; https://github.com/QuantConnect/Lean/blob/master/Data/equity/readme.md) ya da Lean.Brokerages.Alpaca ile canlının AYNI Alpaca verisi (https://github.com/QuantConnect/Lean.Brokerages.Alpaca); (b) FREE bulut backtest — B-MICRO, 200 backtest/gün, AlgoSeek verisi üstünde
- **Ücret:** (a) Ücretsiz (Apache-2.0; kendi verimiz). DİKKAT: lean-cli KULLANILMAZ — 'To use the CLI, you must be a member in an organization on a paid tier'. (b) FREE (B-MICRO: 2 çekirdek/8GB, 20 sn başlatma gecikmesi, 200 backtest/gün, 10K emir/backtest, 12 saat/koşum)
- **Yol:** (a) 1) LEAN'i yerel makineye klonla (Oracle A1'e DEĞİL — canlı sisteme dokunma); 2) dotnet build QuantConnect.Lean.sln; 3) Massive/Alpaca barlarımızı ~50 satırlık dönüştürücüyle custom-data CSV'ye yaz; 4) sinyal kurallarını LEAN algoritmasına port et; 5) emir-düzeyi diff (fill/komisyon/sıralama) kendi motor çıktımızla karşılaştır. (b) Aynı algoritmayı web IDE'de FREE bulutta koş — özet istatistik karşılaştır. Kolların çelişki notu: canlı-katman kolu 'LEAN'in CLI'sız koşturma şartları doğrulanmadı' derken LEAN kolu Apache-2.0'ı repo düzeyinde doğruladı; motor serbest, katman şartı yalnız CLI dokümanına ait.
- **Riskler:** Custom data yolunda LEAN'in delist/split otomasyonu kaybolur (map/factor işlenmez) — diferansiyel test yine fill/komisyon/sıralama farklarını yakalar. Native format seçilirse map/factor şeması resmî dokümante değil, repo örneklerine kalıplanmalı; factor dosyası yokken davranış belirsiz (küçük deneyle doğrula). QC verisini LEAN-dışı Meridian motoruna beslemek yasak — bu yolda veri hep BİZİM verimiz olmalı. Bulut yolunda otomasyon yok (elle koşum).

### [2] earnings-tarihçe (kazanç takvimi derinliği)
- **Bileşen:** EODHD Upcoming Earnings (Ocak 1998+, günlük, Nasdaq kıyasında %96,79 yakalama / %97,25 kesin-tarih; https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/eod-historical-data/upcoming-earnings) + çapraz doğrulama: US SEC Filings 10-Q/10-K/8-K filing tarihleri (15.000 hisse, 1998+; https://www.quantconnect.com/data/us-security-exchange-commission-filings) + Morningstar US Fundamentals file-date disiplini (https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/morningstar/us-fundamental-data)
- **Ücret:** Üçü de FREE (cloud). Kol notu: Licensing 'You need an organization above the Free tier to purchase cloud access' derken Tier Features 'Free tier provides cloud access to datasets for all asset classes' diyor — ücretsiz lisanslı setlerin FREE'de açık olduğu yorumu mantıklı ama set-bazında teyit edilmedi (çelişki aynen aktarıldı).
- **Yol:** 1) Research'te History çağrısıyla EODHD setinin 1998'e dönük TAM earnings-tarih dizisi verip vermediğini test et (set 7-gün ileri-pencere evreni olarak tasarlanmış — kritik açık soru); 2) veriyorsa kartlı ölçüm platform içinde; 3) SEC filing tarihleriyle örneklem çapraz kontrolü; 4) dışarı yalnız özet hüküm.
- **Riskler:** 7-günlük ileri pencere biçimi tarihsel dizi çıkarımını engelleyebilir — fizibilite testi geçmeden karta yazılmamalı. Tarih verisi de dışa aktarılamaz (aynı log/scrape yasakları). Morningstar'da eski semboller için file date '45 gün sonrası yaklaşıklaması' — karta yazılmalı.

### [2] insider (FMP ücretsiz katman kısıtına karşı derinlik)
- **Bileşen:** Quiver Quantitative Insider Trading — Form 4, 4.994 hisse, 25 Nisan 2014+, günlük 04:00 güncelleme (https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quiver-quantitative/insider-trading). İkincil aday: Smart Insider Corporate Buybacks (https://www.quantconnect.com/data/smart-insider-corporate-buybacks)
- **Ücret:** Quiver: FREE (cloud) / on-premise 10 QCC/dosya. Smart Insider: ÜCRETLİ, alt set başına $10/ay cloud — FREE'de erişilemez
- **Yol:** 1) Research'te Quiver setini 2014'e dönük sorgula; 2) 'Before May 14 2021, this dataset included legacy data without all the information' — 2014–2021 aralığını kartta AYRI işaretle (yalnız 3 çekirdek alan: price_per_share, shares, shares_owned_following kısıtlı); 3) insider-derinlik ölçümünü platform içinde kartla koş.
- **Riskler:** 2021-05-14 öncesi alan fakirliği ölçüm tasarımını bölmeli (iki dönem ayrı hükme bağlanmalı). 2014 öncesi tarihçe QC'de de yok. Dışa aktarım yasakları aynen geçerli.

### [3] NLP (haber/metin bileti)
- **Bileşen:** Tiingo News Feed — 10.000 hisse, 120+ sağlayıcı, Ocak 2014+ (https://www.quantconnect.com/data/tiingo-news-feed) + US SEC Filings ham metni 1998+ (FREE). Ücretli alternatifler: Brain Sentiment Indicator $25/ay (2016+), ExtractAlpha Estimize $75/ay (2011+), Benzinga $120/ay
- **Ücret:** Tiingo + SEC Filings: FREE (cloud). Brain $25/ay, Estimize/True Beats $75/ay, Benzinga $120/ay — hepsi FREE hesapta satın alınamaz ('You need an organization above the Free tier to purchase cloud access to datasets')
- **Yol:** 1) Kendi NLP özelliğimizin fizibilitesini Tiingo başlıklarıyla FREE research'te kartla sına; 2) SEC 10-K/8-K metni aynı ortamda ek özellik kaynağı; 3) sonuç olumluysa hazır-skor (Brain) vs kendi-özellik kararı operatöre taşınır.
- **Riskler:** R1-4 (1 çekirdek/4GB) metin işleme için dar — örneklem küçük tutulmalı. Türetilmiş NLP özelliklerini toplu dışa aktarmak da 'strip, scrape, or mine' + log-export yasaklarına takılır; yalnız özet hüküm çıkar. Train() kotası FREE'de sembolik (20 dk kapasite, 1 dk/gün dolum) — model eğitimi QC'de değil A1'de.

### [3] ölçüm-otomasyonu (kart → koşum → hüküm zincirinin programatikleştirilmesi)
- **Bileşen:** REST API zinciri: files/update → compile/create → compile/read (poll) → backtests/create → backtests/read + /backtests/orders/read (100'lük sayfalama) (https://www.quantconnect.com/docs/v2/cloud-platform/api-reference). Notebook-execute ucu YOK — otomasyon yalnız algoritma+backtest biçiminde. Lean Version ucu motor sürümünü karta kaydetmek için.
- **Ücret:** FREE'de YOK: pricing tablosunda API Access Free='–'; 'Organizations on the Quant Researcher tier have access to the QuantConnect API and can use the CLI to run Lean locally.' En ucuz aday: Researcher Seat $10/ay ($96/yıl, pricing JSON'dan aynen) — ancak koltuğun tek başına (düğümsüz) API'yi açıp açmadığı dokümanda net değil; düğümlü Researcher Pack $84/ay ($888/yıl).
- **Yol:** ANCAK katman yükseltme kararından SONRA: 1) Account>Security'den API token; 2) SHA-256 zaman damgalı auth sarmalayıcı; 3) kart başına izole proje (kart-ID → proje adı eşlemesi); 4) compile+backtest zinciri; 5) statistics + emir-düzeyi çıktıyı Rol-1 hükmüne taşı. FREE'de kalınırsa: web IDE'den elle koşum (günde 200 backtest, 1 eşzamanlı oturum) — çalışır ama otomasyon değil.
- **Riskler:** FREE hesapla API/CLI'yi dolaylı yolla kullanmak sözleşme ihlali. Optimizasyon uçları koşum başına QCC faturalı (estimatedCost zorunlu) — bütçe kapısız otomasyona bağlanmamalı; azami 3 parametre + 4 sabit hedef metrik K-grid disiplinimize dar, hedef fonksiyon QC'ye devredilemez. REST hız limiti dokümante değil (429 davranışı bilinmiyor). lean cloud push YIKICI (bulutta yerel karşılığı olmayan dosyayı siler) — tek yönlü akış kuralı şart.

### [2] yedeklilik (Alpaca aynasına karşı ikinci veri görüşü)
- **Bileşen:** QC cloud US Equities — SIP CTA/UTP kaynaklı '100% market coverage', resmî müzayede açılış/kapanış fiyatları, tam split/temettü geri-düzeltmesi (https://www.quantconnect.com/docs/v2/cloud-platform/datasets/quantconnect/us-equities) + Cash Indices (SPX/VIX 1998+/1990+, FREE) + SPY üzerinden US ETF Constituents (2009+, FREE) evren-üyeliği çapraz kontrolü
- **Ücret:** FREE (bulut kullanımında). Bulk yerel kopya: paid tier + Daily bulk $2.136/yıl + Security Master $600/yıl — ama yalnız LEAN-içi kullanım şartıyla
- **Yol:** 1) Bu bir YEDEK ARŞİV değil DOĞRULAMA GÖRÜŞÜ olarak kurgulanmalı (veri dışarı alınamaz); 2) kendi barlarımızın özet istatistiklerini (dönem getirileri, uç değerler) algoritma parametresi olarak gömüp QC barlarıyla platform içinde diff et — FREE dosya limiti 32KB, büyük listeler bölünmeli; 3) uyuşmazlıkta Alpaca-IEX vs SIP farkı ve Raw-vs-Adjusted normalizasyon modu (Misconceptions uyarısı) ayrıştırılmalı; 4) RETIRED_SYMBOLS'ı Security Master delist olaylarıyla doğrula.
- **Riskler:** Gerçek yedeklilik (arşiv kopyası) ToS gereği imkansız — QC düşerse veri görüşü de düşer; tek-nokta bağımlılığı çözmez, yalnız kalite doğrular. Yeni canlı verinin backtest'e düşmesi 24-48 saat gecikmeli. SPY constituents 1 haftaya kadar gecikmeli, 2015 öncesi aylık, resmî SPX üyeliği değil.

## 2. Hemen yapılabilir (FREE, karar gerektirmez — WP-QC kuyruğu)

- Delist-bar fizibilite testi: FREE research notebook'ta SecurityIdentifier.generate_equity + qb.history ile iki yaşayan sinyalin delist sembollerinin QC kapsamında olup olmadığını tek tek doğrula (ölçüm kartından ÖNCE kapsam testi; sıfır ücret).
- EODHD Upcoming Earnings testi: History ile 1998'e dönük tam earnings-tarih dizisi çıkıyor mu yoksa yalnız 7-günlük evren-günlüğü mü — FREE research'te sına; sonuç karta 'sembol çözümleme + veri biçimi' notu olarak yazılır.
- Quiver Insider derinlik kontrolü: 2014+ tarihçeyi FREE research'te sorgula; 2021-05-14 öncesi legacy alan eksikliğini örneklemle doğrula, iki dönemi kartta ayır.
- İkinci-motor pilotu (yerel): LEAN'i Apache-2.0 kapsamında CLI'SIZ (dotnet/docker) yerel makineye kur — QC hesabı/katmanı gerekmez; kendi Massive/Alpaca barlarımızı custom data (LOCAL_FILE) ile okutup tek sinyalde emir-düzeyi diferansiyel çalıştır. Oracle A1'e kurulmaz.
- İkinci-motor pilotu (bulut): aynı sinyali FREE web IDE'de B-MICRO ile koş (200 backtest/gün, günlük çözünürlük FREE) — LEAN+AlgoSeek verisiyle bağımsız ikinci görüş, elle.
- RETIRED_SYMBOLS çapraz doğrulaması: US Equity Security Master delist olayları + SPY ETF Constituents (2009+) ile evren-emekliliği kararlarını platform içinde doğrula.
- Morningstar US Fundamentals notu: 'As Original Reported' + file-date disiplinli PIT iddialı set FREE — 'PIT'siz fundamentals proxy YASAK' yasasına uyan aday; delist isimler için shares_outstanding tarihçesi research'te sınanmalı (45-gün yaklaşıklama kuralı karta yazılır).
- Tiingo News + SEC Filings ile NLP ön-fizibilite: küçük örneklemde kendi özellik çıkarımımızı FREE research'te kartla sına (R1-4 sınırları içinde).
- VIX/SPX rejim bağlamı: Cash Indices (1998+) ve CBOE VIX (1990+) FREE — çapraz-doğrulama koşularına pazar-rejimi filtresi olarak eklenebilir.

## 3. Operatör kararı gereken

- Katman yükseltme (ölçüm-otomasyonu kilidi): Researcher Seat $10/ay ($96/yıl) mı, düğümlü Researcher Pack $84/ay ($888/yıl) mı — ve koltuğun TEK BAŞINA API/CLI/ObjectStore/saniye-tick kilidini açıp açmadığı dokümanda belirsiz; karar öncesi hesapla pricing sayfasından teyit şart. (Üç kol da QR fiyatını statik dokümanda doğrulayamadı; $10/ay pricing JSON'dan.)
- ToS yorumu — yerel indirme yolu: 'internal LEAN use only ... cannot be redistributed or converted in any format' ve 'cannot be consumed another way' hükümleri karşısında QC/AlgoSeek verisini (Security Master $600/yıl + Daily $1/ticker) Meridian'ın KENDİ motoruna beslemek ihlal görünüyor; meşru tek biçim yerelde LEAN koşturmak. Bu yorum ve para kararı operatörün. Tam veri sözleşmesi (quantconnect.com/terms/data) oturum duvarı arkasında — girişle okunmalı.
- Ücretli veri setleri: Brain Sentiment $25/ay (hazır NLP skoru vs kendi özelliğimiz), ExtractAlpha Estimize/True Beats $75/ay (analist/beat tahmini), Smart Insider Buybacks $10/ay — her biri ancak FREE fizibilite testleri değer gösterirse.
- ObjectStore aboneliği (yalnız katman yükseltilirse): fiyat çelişkisi var — docs 2GB/$10-ay derken pricing JSON S-10 2GB/$12-ay diyor; ayrıca ObjectStore'dan DOSYA İNDİRME 'Permissioned Institutional' iznine bağlı — dışa aktarım kanalı olarak plana yazılmadan önce netleştirilmeli.
- Optimizasyon uçlarının kullanımı (yükseltme sonrası): koşum başına QCC faturalı, saatlik düğüm ücreti dokümante değil — bütçe kapısı tasarımı operatör onayı ister.
- QC hesabında fiilî doğrulama turu: FREE org'da R1-4 research node'un gerçekten açık olduğu, workspace kotası çelişkisi (pricing 500MB vs resources 1GB) ve Morningstar alan sayısı çelişkisi (900 vs 1100) hesap içinden kontrol edilmeli.

**Rol-1 önerisi (ToS-yorumu kalemi):** yerel-indirme yolu İZLENMESİN — 'internal LEAN use
only' şartı Meridian motoruna beslemeyi kapatıyor; para bu kapıyı açmıyor. Arşiv ihtiyacının
meşru yolu Massive'dir.

## 4. Reddedilenler (gerekçeli)

- QC canlı/kağıt ticaret katmanı: sıfır yeni yetenek — Alpaca entegrasyonu, broker.py'nin zaten doğrudan konuştuğu aynı Alpaca API'sine QC bulutunu aracı sokar; QC Paper Trading kayma modellemez + $0.005/pay sabit komisyon uygular (Alpaca'nın kendi kağıt eşleştirmesinden GERİYE gidiş); FREE'de canlı node 0, asgari giriş fiilen $84+/ay; Meridian canlısı A1'de $0'a koşuyor ve ikinci canlı dağıtım tek-yazar state disiplinine ikinci emir kaynağı riski ekler. (Kaynak: canlı-katman kolunun iki-paragraf hükmü; https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading)
- Delist-bar verisini log/ObjectStore/scrape yoluyla dışa aktarma: 'you may not use the logs to export dataset information' + Terms 3.3(b)(xvi) — açık ToS ihlali; ayrıca FREE'de 10KB/backtest log ve ObjectStore yazma izni yokluğuyla teknik olarak da ölü yol. Meşru desen: ölçüm platform içinde, dışarı yalnız özet hüküm.
- K-grid taramasını QC optimizasyon uçlarına devretme: azami 3 parametre, hedef metrik 4 sabit seçenek, koşum başına belirsiz QCC faturası — kart disiplinimiz (eşik sonradan değişmez, hedef fonksiyon devredilmez, kill-list dokunulmaz) ile yapısal uyumsuz; backtest zinciri yeterli.
- Öğrenme döngüsünü / ML eğitimini QC'ye taşıma: Train() kotası FREE B-MICRO'da 20 dk kapasite + 1 dk/gün dolum — sembolik; öğrenme döngüsü A1'de kalır.
- Benzinga News Feed ($120/ay): Tiingo (FREE, 2014+, 120+ kaynak) dururken en pahalı NLP seçeneği; fizibilite bile FREE alternatifle yapılabilirken gerekçesiz maliyet.
- FREE hesapla lean-cli kullanımı: 'To use the CLI, you must be a member in an organization on a paid tier' — teknik olarak denenebilir olsa da sözleşmesel ihlal; CLI konforu isteniyorsa yol katman yükseltmedir, gri kullanım değil.
- US Equities Short Availability'yi short-interest ihtiyacına saymak: set ödünç-verilebilirlik/borç maliyetidir (2018+, IB+Axos), FINRA bi-haftalık short interest değil; fiyat/tier bilgisi de bulunamadı — bu ihtiyaç QC'den karşılanmıyor sayılmalı.

## 5. ToS özeti (tam metin)

QC'nin veri rejimi tek cümleyle: veri platformda serbest, platformdan çıkarken kilitli. Bulutta FREE katman dakika-günlük tüm fiyat verisine (delist dahil, survivorship-bias-free, 1998+) backtest+research erişimi verir; ama üç ayrı resmi metin dışa aktarımı kapatır: (1) log-export yasağı — 'you may not use the logs to export dataset information' (resources docs, tüm katmanlar; FREE'de zaten 10KB/backtest); (2) Terms 3.3(b)(xvi) — otomatik araçla 'strip, scrape, or mine data from the Site' yasak; (3) indirme lisansı — 'internal LEAN use only and cannot be redistributed or converted in any format' + Security Master için 'cannot be consumed another way'. Sonuç: QC verisi Meridian'ın yerel arşivini DOLDURAMAZ ve Meridian'ın kendi (LEAN-olmayan) motoruna BESLENEMEZ; para ödense bile meşru kullanım LEAN-içi kalır. ObjectStore'dan türev veri indirme yalnız 'Permissioned Institutional' izinli; FREE'de ObjectStore'a yazma bile yok. Tek açık istisna: orijinal veri yeniden kurulamıyorsa grafik GÖRSELİ paylaşımı. CLI ve REST API kullanımı ücretli katman şartına bağlı ('To use the CLI, you must be a member in an organization on a paid tier'); FREE hesapla dolaylı otomasyon sözleşme ihlalidir. Ters yön (kendi verimizi ve açık kaynak LEAN motorunu, Apache-2.0, hesapsız yerel kullanmak) tamamen serbesttir — ikinci-motor stratejimizin ToS-temiz omurgası budur. Açık kalan: tam veri sözleşmesi (quantconnect.com/terms/data) oturum duvarı arkasında, 'Subscription and Sublicense Agreement' metni okunmadan indirme kararı verilmemeli; özet-istatistik ihracının kesin boyut eşiği resmî dokümanda tanımsız — ihtiyatlı yorum: yalnız küçük, türetilmiş, fiyat-olmayan hüküm çıktıları dışarı taşınır.
