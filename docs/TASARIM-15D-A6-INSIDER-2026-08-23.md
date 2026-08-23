# TASARIM — 15d-A6 Form-4 insider veri yolu fizibilitesi (2026-08-23)

**Rol:** tasarım/fizibilite (kod yok, kart yok, git yok). **Bağlam:** `docs/TASARIM-15D-PIT-FAKTOR-SETI-2026-08-23.md`
§2/A6 ve §4/soru-2 ("FMP plan yükseltmesi mi, EDGAR doğrudan ingest mi, erteleme mi?" — operatör
bu kalemi öne çekti). Emsal disiplin: `research/edgar_facts/README.md` (PIT filed-as-of, ilk-ifşa,
arşiv-donuk) + `meridian/adapters/edgar_shares.py` (as-of okuma köprüsü) + `meridian/adapters/insider.py`
(FMP akışı + CMP sınıflaması, ölçülmüş plan sınırları).

**Ölçüm tabanı bu belgede iki kaynaktır; her sayının yanında hangisi olduğu yazılıdır:**
(a) **YEREL SNAPSHOT** — `scratchpad/edgar_8k/raw/` (258 CIK'in data.sec.gov/submissions dökümü,
indirme 2026-08-01; 8-K turundan diskte duruyordu, sıfır yeni istekle sayıldı);
(b) **CANLI SONDA 2026-08-23** — SEC uçlarına az sayıda kibar istek (User-Agent'lı, istek arası ≥1sn:
1 Form-4 XML + 1 daily-index + 6 HEAD + 1 bulk-zip [9,9MB] indirimi) + FMP'nin halka açık 2 sayfası
(hesap/oturum YOK).

---

## [1] Veri yüzeyi ölçümü

### 1.1 Form-4'ün EDGAR'daki üç yüzü (üçü de canlı doğrulandı)

| yüzey | ne verir | ölçülen |
|---|---|---|
| **Ham XML** `www.sec.gov/Archives/edgar/data/{cik}/{accn}/{doc}.xml` | işlem-düzeyi tam kayıt | JPM `0001225208-26-006750` çekildi (4.351 bayt); şema aşağıda |
| **Daily-index** `Archives/edgar/daily-index/YYYY/QTRn/form.YYYYMMDD.idx` | günün TÜM dosyalamaları, form-tipine göre; satırda CIK+accession | 2026-08-20 dosyası: 4.193 satır, 975'i Form-4; **evren-issuer kesişimi 31 accession** (tek gün — gün-içi varyans ölçülmedi) |
| **Toplu veri seti** `files/structureddata/data/insider-transactions-data-sets/{yyyy}q{n}_form345.zip` | çeyreklik TSV döküm: `SUBMISSION` / `REPORTINGOWNER` / `NONDERIV_TRANS` / `DERIV_TRANS` / `FOOTNOTES`… | HEAD ile doğrulandı: **2006q1 VAR … 2026q1 VAR, 2026q2 → 404**. 2025q2 indirildi (9,9MB zip): şema doğrulandı, `SUBMISSION.tsv`de `ISSUERCIK` + `ISSUERTRADINGSYMBOL` + `AFF10B5ONE` var |

Toplu setin yayın gecikmesi (HTTP `Last-Modified` ile ölçüldü): 2026q1→2026-04-07 (~1 hafta),
2025q4→2026-01-07 (~1 hafta), 2025q3→2025-11-18 (~7 hafta), 2025q2→2025-07-22 (~3 hafta).
**Düzensiz (1–7 hafta) → toplu set GERİ-DOLDURMA içindir, canlı kadans için değil.**

### 1.2 XML şeması (JPM örneği üzerinden; `schemaVersion X0609`)

`ownershipDocument`: `periodOfReport` · `issuer{issuerCik, issuerTradingSymbol}` ·
`reportingOwner{rptOwnerCik, rptOwnerName, reportingOwnerRelationship{isOfficer/isDirector/…, officerTitle}}` ·
**`aff10b5One`** (10b5-1 plan bayrağı — rutin-ayıklamada değerli; toplu sette `SUBMISSION.AFF10B5ONE`) ·
`nonDerivativeTable/nonDerivativeTransaction{securityTitle, transactionDate,
transactionCoding.transactionCode [P/S/A/M/F/G/D/C/J…], transactionAmounts{transactionShares,
transactionPricePerShare, transactionAcquiredDisposedCode [A/D]},
postTransactionAmounts.sharesOwnedFollowingTransaction, ownershipNature.directOrIndirectOwnership}` ·
`derivativeTable` · `footnotes`. Alanlar `adapters/insider.py`nin kanonik satırıyla (`ALAN_ADAYLARI`)
birebir eşlenebilir; FMP'nin verdiği her alanın birinci-el karşılığı var.

### 1.3 Hacim — GERÇEK sayım (YEREL SNAPSHOT, 258 CIK, kesim 2026-08-01)

- **Son 1 yıl (2025-08-01→): 17.781 Form-4 + 110 adet 4/A** (düzeltme oranı %0,6).
- **Son 3 yıl (2022-08-01→): 74.720 Form-4** (CMP penceresinin ihtiyacı).
- Sembol-başına yıllık: **medyan 62**, p10 33, p90 110, maks 305 (örnek: AAPL 42, NVDA 99,
  JPM 133, KO 72, PG 118, AMD 71).
- Son 1 yılda 0 dosyalama: **XOM** (eşleme artefaktı — 1.638 Form-4'ün TAMAMI öncül CIK 34088'de,
  halef 2115436'da SIFIR; `edgar_facts` README §5.5 vakasının Form-4 yüzü) · PARA/ANSS/DFS
  (2025 birleşme/delist ile uyumlu — bu açıklama şirket-olay bilgisinden çıkarımdır, dosyalama
  kaydından ayrıca doğrulanmadı).
- 2025Q2 toplu setinde evren kesişimi (CANLI SONDA): **4.633 Form-4(+A) dosyalama, 6.393 nonDeriv
  işlem satırı**. İşlem kodu dağılımı: S 2.123 · A 1.830 · M 1.094 · F 876 · G 181 · **P 104** ·
  D 77 · C 57 · J 44 · diğer 7. **KRİTİK BULGU: açık-piyasa alımı (P) bu büyük-cap evrende NADİR —
  çeyrekte ~104, yani sembol başına ~0,4 P-olayı/çeyrek** (tek çeyrek ölçümü; mevsimsellik
  ölçülmedi). Faktör tasarımını §[4]'te bu belirliyor.

### 1.4 Gecikme karakteri (PIT penceresi) — son 1 yıl, n=17.781 (YEREL SNAPSHOT)

`filingDate − reportDate` (reportDate = dosyalamadaki EN ERKEN işlem günü): **medyan 2 gün**,
p90 4, p99 6; ≤2 gün %64,7; >4 gün %7,7; >10 gün yalnız 125 satır (%0,7); maks 9.102 gün
(eski işlemlerin geç raporu — gerçek olay, hata değil); negatif 0. Yasal çerçeve (2 iş günü,
Section 16) ölçülen medyanla tutarlı. **PIT kuralı `edgar_facts` ile aynıdır: bilgi tarihi =
`filingDate`; `transactionDate` yalnız olayın etiketi.** Kuyruktaki geç dosyalamalar tam da
`filed`-disiplinin var olma sebebi — `transactionDate`e göre çalışan ölçüm o 125+ satırda geleceği
sızdırır. 4/A düzeltmesinin bilgi tarihi kendi `filingDate`idir.

---

## [2] İngest tasarımı — yol (a): EDGAR doğrudan

`edgar_facts` deseninin uzantısı: `research/edgar_insider/` altında **arşiv-donuk** csv.gz +
`kaynak.json` (sha256 manifest) + `betikler/` boru hattı; UA + istek-arası 0,15sn fair-use aynen
(README §6). İki bacak:

1. **Geri-doldurma (tek sefer):** toplu setler 2006q1→2026q1 ≈ **81 zip, ~81 istek** (2025q2
   9,9MB ölçüldü; toplam boyut ölçülmedi — kaba sınıf ≤1GB). `SUBMISSION.tsv`
   `ISSUERCIK ∪ ISSUERTRADINGSYMBOL` ile süzülür; `NONDERIV_TRANS` + `REPORTINGOWNER`
   `ACCESSION_NUMBER` ile bağlanır. Ham 74,7k XML'i tek tek çekme ihtiyacını (≈14 saat) ortadan
   kaldırır.
2. **Dikiş + canlı kadans:** 2026Q2→bugün boşluğu daily-index taramasıyla (≈55 idx dosyası +
   evren-issuer accession XML'leri; 1.3'teki oranla ~9k istek ≈ 2 saat, tek koşu). Sonra günlük:
   **1× dünün `form.idx`i + ~30-70 XML** (2026-08-20 ölçümü 31; yıllık ortalamadan beklenti ~70).
   Alternatif (258 issuer'ın submissions delta'sı) günde 258 istekle daha ağır — önerilmez.

**Tekilleştirme:** doğal anahtar `ACCESSION_NUMBER` (EDGAR birincil kimlik; FMP yolunda yoktu).
4/A politikası: orijinal accession'a şerh, iki satır da PIT damgalı tutulur. Mevcut FMP defteriyle
birleştirme RİSKLİ: `insider.py:_anahtar` `kisi` adını anahtara katar ve ad biçimi farklıdır
(EDGAR "Friedman Stacey" ⇄ FMP biçimi) → sessiz çift sayım. Öneri: **faktör verisinin SSoT'u EDGAR
arşivi olur; FMP kadansı bilgi katmanında kalır, defterler birleştirilmez** (çapraz-doğrulama
raporu ayrık yazılır).

**CIK-halefiyet (41-sembol kesiği bize nasıl vurur):** 8-K'deki 41'lik kesik Form-4'te ÖLÇÜLDÜ ve
küçük çıktı — bugünkü CIK haritasıyla ilk Form-4'ü 2022-08 sonrası olan yalnız **BLK (2024-10-02)**
ve **SPOT (2026-04-03)**; XOM ise harita düzeltmesi (öncül CIK'ten okumak yeter). Toplu setler
dönemin-issuer-CIK'iyle yazıldığından öncül dönem satırları sette VARDIR; sembol+öncül-CIK
eşlemesiyle köprülenir (bu köprünün BLK üzerinde çalıştığı kurulumda doğrulanmalı — şimdilik tasarım
beklentisi). `build_cikmap.py`nin öncül-CIK genişletmesi işin parçasıdır.

**İş boyutu: M (orta).** Gerekçe: iki ayrıştırıcı (toplu TSV + canlı XML; şema sürümlü/kararlı,
HTML kazıma yok) + idx hasatçısı + harita genişletmesi + QC/README — 8-K boru hattı sınıfında
(719 istek, ~1.000 satır betik, tek oturumda inmişti); artı canlı kadans kablosu. S değil (iki
format + dikiş var), L değil (keşfedilecek bilinmeyen kalmadı — bu belgenin sondaları yüzeyi kapattı).

---

## [3] FMP kıyası — yol (b)

**Ücretsiz planın ölçülmüş sınırları** (canlı sonda 2026-07-30; `adapters/insider.py:44-70`,
ROADMAP:2349): `insider-trading/search` → 402 · `page>=1` → 402 · `limit>100` → 402 · `date=`
sessizce yok sayılıyor. Fiilen günde 1×100 satırlık `latest` sayfası, evren isabeti ~6 satır/gün,
yalnız İLERİYE akar → **3 yıllık CMP penceresi bu yoldan ancak 3 yıl bekleyerek dolar** (dosyadaki
"dürüstlük düzeltmesi" bloğu).

**Ücretli plan (CANLI SONDA 2026-08-23, halka açık sayfalar):** fiyat sayfasının statik HTML'inde
kademeler ve özellik listeleri okunuyor (Basic ücretsiz 250 çağrı/gün; Starter "5 yıl tarihsel, US";
Premium "30 yıl tarihsel"; Ultimate "tam tarihsel erişim, transkript, 13F") — ama **sayısal fiyatlar
None (ölçülemedi: JS ile çiziliyor, statik HTML'de yok; hesap/oturum açmak kapsam dışı)** ve
**insider-`search`ü hangi kademenin açtığı None (ölçülemedi: uç-başına plan rozeti dinamik;
"available on the following plans" şablonu boş geliyor)**. Maliyet sınıfı: **sürekli abonelik**
(aylık, yıl bazında yüzlerce-USD sınıfı olması muhtemel — tahmindir, fiyat ölçülemedi) karşısında
EDGAR'ın tek-seferlik M-emeği + ~sıfır işletme maliyeti.

**Para dışındaki asıl fark:** FMP aynı EDGAR verisinin türev satıcısıdır; `filed` damgasının
sadakati, 4/A işleyişi ve tarihsel tamlık satıcı iddiasıdır, arşivden doğrulanamaz — `date=`
parametresinin sessizce yok sayılması bu sınıfın canlı örneğiydi. Depo yasası ("PIT'siz fundamentals
proxy YASAK", CLAUDE.md §4) birinci-el kaynağı işaret ediyor; `edgar_facts`/`edgar_shares` emsali
zaten bu yolun altyapı ve disiplinini kurmuş durumda.

---

## [4] Faktör ön-taslak (KART DEĞİL — parametre önerisi; ön-kayıt Rol-1'in)

Ölçümün şekillendirdiği gerçek: **P-olayları seyrek** (§1.3: ~0,4/sembol/çeyrek). Sürekli kesitsel
"net-alım skoru" çoğunlukla sıfır olur; doğal tasarım **olay-bazlıdır** (A1 PEAD kartının şablonu).

- **Olay tanımı (ana eksen):** *fırsatçı net-alım kümesi* — aynı sembolde 30g içinde ≥N farklı
  insider'dan kod-P alımı; CMP rutin-ayıklaması `insider.py.siniflandir` ile (defter 2006'ya kadar
  dolunca 3-yıl penceresi tarihsel olarak da kurulabilir — FMP yolunun kurulamayan tek şeyi).
  N∈{1,2} tek grid ekseni adayı.
- **Filtreler:** yön disiplini aynen (`yon_coz`: nete yalnız P/S; A/M/F/G `diger`) ·
  `aff10b5One=1` dosyalamaları rutin sayılır (10b5-1 planı) · C-suite varyantı:
  `RPTOWNER_RELATIONSHIP=Officer` bayrağı + unvan regex'i (ölçüldü: unvan serbest-metin ve kirli —
  "SEE REMARKS" 841 satır; bayrak birincil, regex ikincil, beyan şart).
- **Pencere/tepki:** sinyal birikimi 90g (`VARSAYILAN_OZET_GUN` ile tutarlı); tepki ufku 20/60g,
  taban aynı-gün evren ortalaması, blok-bootstrap CI (wp2/K1 şablonu). Tutar normalizasyonu
  `edgar_shares.as_of_shares` paydasıyla (PIT payda hazır).
- **Kill adayları:** (i) 20 yıllık arşivde geçerli küme-olayı < ~400 → askı, K harcanmaz
  (P-seyrekliği bunu gerçek bir riske çevirir — 104/çeyrek × ~80 çeyrek ≈ 8k P-işlemi, kümeleme
  sonrası olay sayısı ölçümde görülecek); (ii) @20 ve @60 CI-0-içi → bilgisiz, arşiv;
  (iii) yön ters-anlamlı → arşiv+not. Satış bacağı (S) ayrı hüküm hücresi AÇILMASIN — büyük-cap'te
  S baskın ve plan/vergi gürültülü; tanı sütunu olarak eşiksiz raporlanır.
- **Kapsam şerhi:** BLK/SPOT halefiyet kesiği + XOM haritası hükümde beyan; survivorship üst-sınır
  şerhi (15d ana belgesindeki fja05680 as-of süzgeci) aynen geçerli.

---

## [5] Öneri + açık sorular

**ÖNERİ: yol (a) — EDGAR doğrudan ingest.** Üç gerekçe: (1) CMP'nin 3-yıl penceresi FMP'nin
ücretsiz yolunda YAPISAL olarak dolmuyor, ücretli yolda satıcı-iddialı; EDGAR toplu setleriyle
2006'ya kadar ~81 istekte birinci-el doluyor. (2) Maliyet: M-boy tek-seferlik iş + günde ~70 kibar
istek ↔ süreklilik arz eden abonelik (fiyatı ölçülemedi). (3) Disiplin: PIT damgası (`filingDate`),
accession-kimliği ve 4/A izi yalnız birinci-el kaynakta denetlenebilir; `edgar_facts` emsali
ingest kalıbını zaten kurdu. FMP kadansı bilgi katmanında aynen kalır (ROADMAP [B-FMP-PLAN] kalemi
A6 gerekçesini kaybeder; başka kalemler için değerlendirilmesi ayrı karar).

**Operatör kararı gerektirenler:**
1. **Yol onayı:** (a) EDGAR-ingest'e M-boy iş bütçesi mi, (b) FMP planı mı (fiyat ancak hesapla
   görülebilir), yoksa erteleme mi? (Bu belgenin önerisi: a.)
2. **Hedef katman:** arşiv yalnız `research/` (ölçüm için donuk) mı, yoksa canlı CMP defterini de
   EDGAR-SSoT'a mı geçirelim? İkincisi `insider.py`de kaynak-değişimi demek — ayrı brief, YASA 6
   okuyucu-analizi ister.
3. **Dikiş koşusu izni:** ~9k isteklik tek-sefer daily-index hasadı (fair-use içinde, ~2 saat) ne
   zaman koşulsun?
4. **Türev tablo kapsamı:** bu taslak nonDerivative-only (P/S orada); M/C kodlarının kaynağı olan
   `derivativeTable` ilk turda alınsın mı? (Öneri: ham arşive AL, faktöre KATMA — beyanla.)
5. **K/kart sırası:** 15d ana belgesinin sıralaması (A1→A2→A3 önce) değişmiyor; A6 kartı veri
   indikten sonra mı ön-kaydedilsin, veri işiyle paralel mi?

*Ölçülemeyenler özeti: FMP sayısal fiyatı ve plan-uç eşlemesi (JS/hesap bariyeri) · toplu setlerin
toplam boyutu (yalnız 3 çeyrek HEAD'lendi) · günlük Form-4 debisinin gün-içi varyansı (tek gün
ölçüldü) · P-kodu mevsimselliği (tek çeyrek ölçüldü) · BLK öncül-CIK köprüsünün toplu-set üzerinde
fiilî doğrulaması (kurulum işine bırakıldı).*
