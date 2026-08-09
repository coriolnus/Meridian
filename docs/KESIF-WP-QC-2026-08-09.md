# KEŞİF — WP-QC (QuantConnect Entegrasyonu) · 2026-08-09

> **Bu tur SALT ÖLÇÜM + PLAN.** git çalıştırılmadı, canlıya dağıtılmadı, `serve.sh`
> koşulmadı, broker emri yok, `meridian/`+`tests/` değiştirilmedi. Yazılan tek dosya budur.
> Kaynaklar: ROADMAP.md §WP-QC (satır ~637) · `docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md` ·
> `research/cards/EDG-2026-021-qc-delist-dogrulama.yaml` · `research/qc_dogrulama/*` ·
> repo-içi çapraz-doğrulama verileri (aşağıda satır/sembol sayılarıyla ölçüldü).
> **UYDURMA YASAĞI:** ölçülemeyen her sayı açıkça **ÖLÇÜLEMEDİ** diye işaretlendi.

---

## 0. Zemin gerçeği — mekanizma bu turda DEĞİŞMEDİ, ÖLÇÜLDÜ

WP-QC'nin çalışan deseni EDG-021'de kanıtlandı; kuyruğun ②-⑦'si aynı boru hattını kullanır.
Planı okumadan önce dört ölçülmüş gerçek:

1. **FREE QC hesabı VAR.** Operatör 2026-08-03'te açtı (proje `Fat Apricot Koala`, id 34763939,
   çekirdek `Foundation-Py-Default`; kaynak: `research/qc_dogrulama/OPERATOR_TALIMATI.md §0`).
   Yani ②-⑦'nin **hesap-açma bloğu ZATEN KALKMIŞ**; kalan blok operatörün defteri KOŞMASIDIR.

2. **Boru hattı: ajan defter yazar → operatör koşar → Rol-1 hüküm verir.** Ajanlar hesaba
   giremez/kimlik taşıyamaz; ölçüm motoru DIŞARIDA (QC Research). Ajan yalnız kendine-yeterli,
   **eşik içermeyen** notebook üretir; operatör QC'ye yapıştırıp koşar, JSON çıktısını repoya
   bırakır. Bu, "ölçüm ajanı karta dokunmaz" disiplininin dış-motor uyarlamasıdır.

3. **QC API zemini ÖLÇÜLDÜ** (`research/qc_dogrulama/QC_API_ZEMIN_GERCEGI.md`):
   - `qb.history(Fundamental, …)` ve `qb.history(CoarseFundamental, …)` → FREE'de **boş DataFrame**.
   - Çalışan tek yol: `qb.add_universe(secici)` + `qb.universe_history(u, t0, t1)` → `Series`,
     her değer `list[Fundamental]`; evren seçimi + fiyat + hacim + **as-of hisse sayısı**
     (`company_profile.shares_outstanding`) aynı çağrıdan gelir, look-ahead yok.
   - Kural: **QuantBook örneği amaç başına ayrı, paylaşılmaz** (v2 canlı arızasının kök nedeni).

4. **ToS tek cümlede: veri platformda serbest, çıkışta kilitli** (log-export yasağı + Terms
   3.3(b)(xvi) scrape yasağı + "internal LEAN use only"). Sonuç, TÜM kuyruk kalemlerini bağlar:
   **dışarı yalnız küçük, türetilmiş, fiyat-olmayan hüküm-sayısı taşınır.** QC hiçbir kalemde
   arşiv-kaynağı değildir; bir kalem "veriyi yerele indirir" diye tarif edilemez.

**① delist-kapsam ✅ ÖLÇÜLDÜ (EDG-2026-021, 2026-08-03).** Defter DUR=null ile koştu, pozitif
kontrol geçti (IC=0,0265). Headline @20 üst-%20 evren-fazlası **+0,48% CI[−0,78%, +1,85%]** —
CI-0-içi → "yaşayan sinyal ŞÜPHEDE" dalı; ikinci-koşum hakkı (tanım-eşitleme) operatörde.
Kanıt: `research/olcumler/qc_dogrulama/sonuc_021.json` + `kosum_ciktisi_ham.txt`.
**Bu turun ⑤'i için kritik miras:** EDG-021 delist tespitini bir **VEKİLLE** yaptı; QC'nin
map-file / `Delisting` olayına gerçek erişim yolu **ÖLÇÜLMEDİ** (defter beyanı, `cikti_semasi.md §11.1`).

---

## 1. FREE kuyruk — kalem kalem (②-⑦)

Her kalemde: **ne ölçer · elimizdeki çapraz-doğrulama hedefi (ölçüldü) · açık fizibilite
sorusu · kart · QC hesap/ödeme · operatör-blok.**

### ② EODHD Upcoming Earnings 1998+ — tarihsel-dizi fizibilitesi

- **Ne ölçer:** EODHD kazanç-takvimi setinin (1998+, Nasdaq kıyasında %96,79 yakalama /
  %97,25 kesin-tarih — kaynak değerlendirme §1[2]) 1998'e dönük **tam earnings-tarih dizisi**
  verip vermediği; yoksa yalnız 7-günlük ileri-pencere evren-günlüğü mü olduğu. Bu, "kazanç
  takvimi derinliği" ihtiyacının FREE'de karşılanıp karşılanmadığını söyler.
- **Elimizdeki çapraz-doğrulama hedefi (ÖLÇÜLDÜ):** `research/edgar_facts/earnings_8k_tarihleri.csv`
  = **17.536 satır** (SEC 8-K, item 2.02 kazanç dosyalamaları; `filed`/`report_date`/`acceptance`
  alanlı, PIT-temiz). EODHD tarihleri örneklemde bu SEC tarihleriyle çakıştırılabilir.
- **Açık fizibilite sorusu (ÖLÇÜLEMEDİ, defter koşmadan bilinemez):** set 7-gün ileri-pencere
  evreni olarak tasarlandı; `History` çağrısı geriye dönük tarih dizisi mi yoksa yalnız pencere
  günlüğü mü döndürür? Kartın önündeki ilk adım budur.
- **Kart:** önce **fizibilite notu** (kart-hafif — "sembol çözümleme + veri biçimi" sonucu);
  tarihsel dizi çıkıyorsa ancak o zaman **ölçüm kartı** açılır.
- **QC hesap/ödeme:** FREE (hesap VAR). Ödeme YOK.
- **Operatör-blok:** yalnız defteri koşma (~EDG-021 mertebesi).

### ③ Quiver Insider Trading 2014+ — derinlik + 2021-öncesi legacy ayrımı

- **Ne ölçer:** Form 4 tarihçesini 2014-04-25+ (4.994 hisse, günlük 04:00 güncelleme) derinliğinde;
  **2021-05-14 öncesi legacy dönemde alan fakirliği** (yalnız 3 çekirdek: price_per_share, shares,
  shares_owned_following) iki ayrı hükme bölünmeli.
- **Elimizdeki gerçek (ÖLÇÜLDÜ):** yerel `insider.py` FMP kullanıyor ve FMP `insider-trading/search`
  (sembol-başına geçmiş) ücretsiz planda **HTTP 402** döner (ölçüldü 2026-07-29, `insider.py` satır 16).
  Yani 3 yıllık sınıflama penceresi bugün ancak `/latest` akışının GÜNLÜK BİRİKMESİYLE dolar.
  Quiver-FREE, FMP'nin parayla açılan derinliğini **QC platformunda bedava** sınamayı sağlar.
- **Açık fizibilite sorusu (ÖLÇÜLEMEDİ):** 2014-2021 legacy alan kısıtının örneklemde gerçek
  büyüklüğü; 2014 öncesi QC'de de yok.
- **Kart:** derinlik-kontrol kartı; iki dönem (≷2021-05-14) AYRI hükme bağlanır. Bir kenar iddiası
  (fırsatçı-insider tilt) üretirse ölçüm kartı zorunlu.
- **QC hesap/ödeme:** FREE cloud (hesap VAR). *On-premise/indirme 10 QCC/dosya — İZLENMEZ (ToS+Rol-1).*
- **Operatör-blok:** defteri koşma.

### ④ Morningstar PIT-shares — delist isimlerde hisse-tarihçesi

- **Ne ölçer:** "As Original Reported" + file-date disiplinli Morningstar US Fundamentals'ın
  delist isimler için `shares_outstanding` tarihçesi (WP-U/PIT girdisi; "PIT'siz fundamentals
  proxy YASAK" yasasına uyan aday). 45-gün yaklaşıklama şerhi karta yazılır.
- **Elimizdeki gerçek (ÖLÇÜLDÜ — kısmen ZATEN kanıtlı):** as-of hisse SEVİYESİ QC'de
  `company_profile.shares_outstanding` yolundan **erişilebilir olduğu EDG-021'de ölçüldü**
  (kaynak kod-1, nokta-zamanlı seviye). Yerel çapraz-doğrulama: `research/edgar_facts/` —
  `CommonStockSharesOutstanding` (193 sembol / 17.938 satır), `EntityCommonStockSharesOutstanding`
  (247 sembol / 15.060 satır, ilk-ifşa gecikme medyanı **7 gün**) + `shares_outstanding.csv.gz`.
- **Açık fizibilite sorusu (ÖLÇÜLEMEDİ):** as-of SEVİYE elde ama **file-date/ilk-ifşa PIT
  TARİHÇESİ** (revizyon/yeniden-beyan izi) Morningstar setinden FREE'de sorgulanabilir mi;
  delist isimler için "45-gün sonrası yaklaşıklama" gerçek büyüklüğü nedir. `earning_reports.
  basic_average_shares` (kod-2, ağırlıklı ortalama) SEVİYE olarak reddedilir — sapma karta yazılır.
- **Kart:** fizibilite + **ölçüm kartı** (WP-U girdisi; PIT iddiası hüküm doğurur).
- **QC hesap/ödeme:** FREE (hesap VAR). Ödeme YOK.
- **Operatör-blok:** defteri koşma.

### ⑤ RETIRED_SYMBOLS çapraz-doğrulama — EN DÜŞÜK BLOKLU KALEM

- **Ne ölçer:** 8 emekli sembolün (evren-emekliliği kararlarının) QC US Equity Security Master
  **delist olayları** + SPY ETF Constituents (2009+) ile doğrulanması. Delist tarihi/nedeni ve
  sembol-değişim (FI→FISV) otoritesi Security Master'da.
- **Elimizdeki gerçek (BU TURDA ÖLÇÜLDÜ — çoğu YERELDE zaten yapılabiliyor):** `RETIRED_SYMBOLS`
  8 kalem (ANSS, DFS, FI, HES, IPG, K, PARA, WBA; `meridian/adapters/data.py:2606`). Yerel SP500
  üyelik dosyası (`research/pit_universe/sp500_uyelik_tarihi.csv`, 2.718 satır, 1996→2026-06-30)
  ile çapraz kontrol **bu turda koşuldu** — 8'inin 8'i de tutarlı (üyelikten SON görülme, delist
  gününden birkaç gün-hafta ÖNCE, beklendiği gibi):

  | sembol | RETIRED delist | yerel üyelikte son görülme |
  |---|---|---|
  | ANSS | 2025-07-18 | 2025-07-09 |
  | DFS  | 2025-05-19 | 2025-03-24 |
  | FI   | 2025-11-11 | 2025-11-04 |
  | HES  | 2025-07-21 | 2025-07-18 |
  | IPG  | 2025-11-28 | 2025-11-11 |
  | K    | 2025-12-12 | 2025-11-28 |
  | PARA | 2025-08-08 | 2025-07-23 |
  | WBA  | 2025-08-29 | 2025-08-08 |

- **Açık fizibilite sorusu (ÖLÇÜLEMEDİ — ⑤'in tek gerçek QC-adımı):** QC'nin `Delisting` olayına /
  Security Master delist-otoritesine FREE erişim yolu EDG-021'de **ölçülmedi** (vekil kullanıldı).
  ⑤'in ilk adımı bu yüzden **1-hücrelik API-fizibilite sondası**dır: Security Master delist olayı
  FREE'de sorgulanıyor mu? Evetse ⑤ neredeyse trivialdir (8 sembol, deterministik evet/hayır).
- **Kart:** **muhtemelen GEREKMEZ** — bu bir kenar iddiası değil, mevcut kararların olgu-denetimi.
  *İstisna:* bir emeklilik kararını yeniden AÇARSA (ör. Security Master tarih/neden çelişkisi)
  bulgu ROADMAP'e yazılır.
- **QC hesap/ödeme:** FREE (hesap VAR). Ödeme YOK.
- **Operatör-blok:** kısa defter koşma; yerel kısmı zaten koşuldu (yukarıda).

### ⑥ Tiingo News + SEC Filings NLP — ön-fizibilite

- **Ne ölçer:** Tiingo News (10.000 hisse, 120+ sağlayıcı, 2014+) + SEC 10-K/8-K ham metni üstünde
  KENDİ NLP özellik-çıkarımımızın küçük örneklemde fizibilitesi; sonuç olumluysa hazır-skor
  (Brain $25/ay) vs kendi-özellik kararı operatöre taşınır.
- **Elimizdeki gerçek:** SEC ham metni yerel `edgar_facts` çekimiyle örtüşür (kapsam hazır);
  Tiingo QC-FREE'de.
- **Açık fizibilite sorusu / teknik blok (ÖLÇÜLEMEDİ):** R1-4 research düğümü **1 çekirdek/4GB** —
  metin işleme için dar; örneklem küçük tutulmalı. Train() kotası FREE'de sembolik.
- **Kart:** ön-fizibilite (kart-hafif); yalnız bir özellik mezun olursa ölçüm kartı.
- **QC hesap/ödeme:** FREE (hesap VAR). Brain/Estimize/Benzinga = **ÖDEME** (yalnız fizibilite
  değer gösterirse; Benzinga $120 zaten RED).
- **Operatör-blok:** defteri koşma. En düşük acil-değer / en dar kaynak → kuyruğun SONU.

### ⑦ VIX/SPX rejim-bağlamı — Cash Indices 1998+, CBOE VIX 1990+ (FREE)

- **Ne ölçer:** QC Cash Indices (SPX 1998+) + CBOE VIX (1990+) FREE — çapraz-doğrulama koşularına
  **platform-içi rejim filtresi** olarak eklenebilir.
- **Elimizdeki gerçek (ÖLÇÜLDÜ):** yerel VIX vade-yapısı **DOĞRULANDI ve YOK** (`meridian/regime.py`
  VIX_DATA_STATUS: Massive `I:VIX/I:VIX3M` → HTTP 403 NOT_AUTHORIZED; FMP `^VIX/VIX/^VIX3M/VIX3M`
  dördü de boş; doğrulama 2026-07-30). ROADMAP'in "VIX veri-kilidi kısmen çözülebilir" notu tam budur.
- **KRİTİK SINIR (ToS):** QC VIX verisi **platformdan çıkamaz** → canlı A1'deki `regime.py` VIX
  kapısını **AÇMAZ** (o `veri_yok` kalır). QC yalnız **platform-içi** QC ölçümlerine rejim bağlamı
  katar. "Kısmen çözülebilir"in dürüst okuması: ölçüm-içi bağlam, canlı-kapı değil.
- **Kart:** tek başına kart DEĞİL; başka bir kartın koşumuna eklenen **beyanlı bağlam/filtre
  katmanı**. **Disiplin uyarısı:** rejim filtresini mevcut bir koşuma eklemek K-grid'i ÇARPAR
  (yeni hücre) — sessizce eklenemez, ön-kayıtta beyan edilir.
- **QC hesap/ödeme:** FREE (hesap VAR). Ödeme YOK.
- **Operatör-blok:** defteri koşma (başka kalemle birlikte).

---

## 2. C2-4 · LEAN-yerel motor (ikinci-motor diferansiyeli) — HESAP GEREKTİRMEZ

- **Fizibilite (ÖLÇÜLDÜ):** LEAN motoru **Apache-2.0**; `lean-cli` ücretli katman ister ama motorun
  kendisi `dotnet`/`docker` ile CLI'sız koşar → **QC hesabı ya da ücretli katman GEREKMEZ**
  (ROADMAP satır 650; `PATTERN-ETUDU §C2-4`). Veri **BİZİM** (Massive/Alpaca barları, custom-data
  `LOCAL_FILE`). Oracle A1'e kurulmaz — yerel makine.
- **YEREL TOOLCHAIN BLOĞU (BU TURDA ÖLÇÜLDÜ):** bu makinede **`dotnet` YOK, `docker` YOK**
  (`command -v` boş). Disk boş alanı 78 GiB (yeterli). Yani C2-4 "hesapsız"dır ama "sıfır-kurulum"
  DEĞİL: önce dotnet SDK ya da docker kurulmalı. Bu bir **makine-kurulum** bloğudur, operatör-hesap
  bloğu değil.
- **Ne kıyaslar:** aynı sinyali bağımsız motorda koşup **emir düzeyinde diff** (fill / komisyon /
  sıralama) — "canlı-backtest sapması bizim motorun mu?" sorusunun en derin cevabı (reconciliation).
- **Kart:** motor-diff'in kendisi kenar iddiası üretmez → **kart GEREKMEZ**; yalnız bir sinyalin
  **hükmünü değiştirirse** kart gerekir.
- **Risk (ÖLÇÜLDÜ, değerlendirme §1):** custom-data yolunda LEAN'in delist/split otomasyonu kaybolur
  (map/factor işlenmez); diff yine fill/komisyon/sıralama farklarını yakalar. Native formatta
  map/factor şeması resmî dokümante değil → küçük deneyle kalıplanır. Boyut: **L**.

---

## 3. Kart gereksinimleri (özet)

| Kalem | Kart gereksinimi | Not |
|---|---|---|
| ② EODHD earnings | fizibilite notu → (dizi çıkarsa) ölçüm kartı | 7-gün-pencere biçim riski önce elenmeli |
| ③ Quiver insider | derinlik-kontrol kartı; ≷2021-05-14 iki AYRI hüküm | kenar iddiası doğarsa ölçüm kartı |
| ④ Morningstar shares | fizibilite + **ölçüm kartı** (WP-U/PIT girdisi) | as-of SEVİYE zaten erişilebilir; file-date PIT tarihçe açık |
| ⑤ RETIRED çapraz-doğrulama | **muhtemelen GEREKMEZ** (olgu-denetimi) | karar yeniden açılırsa ROADMAP kaydı |
| ⑥ Tiingo+SEC NLP | ön-fizibilite (hafif); özellik mezun olursa kart | R1-4 dar → örneklem küçük |
| ⑦ VIX/SPX rejim | tek başına kart YOK; beyanlı filtre katmanı | ekleme K-grid'i ÇARPAR → ön-kayıtta beyan |
| C2-4 LEAN | kart YOK (hüküm değişmedikçe) | regresyon/reconciliation |

---

## 4. Operatör-blokları — hangisi hangi kalemi açar

| Blok | Durum | Hangi kalemi açar |
|---|---|---|
| **FREE QC hesabı** | ✅ AÇIK (2026-08-03) | ②③④⑤⑥⑦ hesap-düzeyinde zaten açık |
| **Operatör defter-koşma zamanı** | 🔵 gereken tek asıl blok | ②③④⑤⑥⑦ — her biri operatörün notebook koşmasını ister (EDG-021 boru hattı hazır) |
| **Yerel dotnet/docker kurulumu** | 🟠 makine-kurulum (operatör-hesap değil) | C2-4 LEAN pilotu |
| Katman yükseltme (Researcher Seat $10/ay) | operatörde | YALNIZ ölçüm-**otomasyonu** (REST/CLI); ②-⑦ ELLE koşumda buna gerek YOK |
| Ücretli setler (Brain $25 / Estimize $75 / SmartInsider $10) | operatörde, koşullu | ⑥ (Brain) / ③ (SmartInsider) — YALNIZ FREE fizibilite değer gösterirse |
| ToS-yorumu (yerel-indirme yolu) | Rol-1: İZLENMEZ | hiçbir kalemi açmaz; arşiv ihtiyacının meşru yolu Massive |

**Özet:** ②-⑦ için para bloğu YOK; tek gerçek blok operatörün defteri koşmasıdır. C2-4 için
hesap/para bloğu YOK; tek blok yerel dotnet/docker kurulumudur.

---

## 5. Önceliklendirilmiş plan — otonom vs bloklu

### A. Otonom (hesap YOK, operatör YOK) — bu ekibin tek başına ilerletebileceği iş
- **A1 · ⑤'in yerel yarısı ZATEN koşuldu** (bu turda; §1-⑤ tablosu): 8/8 emekli sembol yerel SP500
  üyeliğiyle tutarlı. Kalan yalnız QC Security Master'ın **otoritesini** eklemek.
- **A2 · C2-4 LEAN pilotu (planlama + toolchain kurulumu).** "Hesap gerektirmeyen iş var mı?"
  sorusunun cevabı **EVET, C2-4'tür** — ama sıfır-kurulum değil: önce dotnet/docker kurulur
  (§2, ikisi de bu makinede YOK), sonra ~50-satırlık bar→custom-data dönüştürücü + tek sinyalde
  emir-düzeyi diff. Boyut **L**; ayrı bir implementasyon turu ister (bu tur SALT plan).
  Not: C2-4 "L" olduğundan ve bu turun mandası ölçüm+plan olduğundan, kurulum bu turda YAPILMADI.

### B. Düşük-bloklu QC kalemi (yalnız kısa operatör-koşumu) — EN DÜŞÜK BLOK
- **B1 · ⑤ RETIRED çapraz-doğrulama.** En küçük kapsam (8 sembol), mevcut kararı doğrular, yarısı
  yerelde bitti, kart muhtemelen gerekmez. Tek QC-adımı: **1-hücrelik Security Master delist-olayı
  API sondası** (EDG-021'de ölçülmeyen erişim yolu). Sonda tutarsa ⑤ trivial kapanır. **Kuyruğun
  başı bu olmalı** — hem en düşük blok hem de EDG-021'in tek ölçülmemiş API-boşluğunu (Delisting
  erişimi) kapatır, bu da ②-④'ün delist-tespitini vekilden gerçeğe taşıyabilir.

### C. Yüksek-değer, fizibilite-kapılı (her biri önce 1 fizibilite sondası, sonra ölçüm kartı)
- **C1 · ② EODHD earnings** (1998+ dizi çıkarsa yüksek değer; 7-gün-pencere riski önce elenir).
- **C2 · ④ Morningstar shares** (WP-U/PIT girdisi; as-of seviye kanıtlı, file-date tarihçe açık).
- **C3 · ③ Quiver insider** (FMP-402 derinlik boşluğunu bedava sınar).

### D. Bağlam katmanı ve keşif (tek başına koşulmaz / kuyruğun sonu)
- **D1 · ⑦ VIX/SPX** — B/C koşularına beyanlı rejim-filtresi olarak katılır (K-grid çarpımı
  ön-kayıtta beyan). Canlı VIX kapısını AÇMAZ (ToS).
- **D2 · ⑥ Tiingo+SEC NLP** — en dar kaynak, en keşifsel; en son.

**Tek cümlelik sıralama:** ⑤ (en düşük blok, EDG-021 API-boşluğunu da kapatır) → ② / ④ / ③
(fizibilite-kapılı, değere göre) → ⑦ (bağlam katmanı) → ⑥ (keşif). Paralel ve hesapsız: C2-4
LEAN pilotu (önce yerel dotnet/docker kurulumu; ayrı implementasyon turu).

---

## 6. DÖNÜŞ ÖZETİ

- **En düşük-bloklu QC kalemi: ⑤ RETIRED_SYMBOLS çapraz-doğrulama.** Kapsam 8 sembol; yerel yarısı
  bu turda koşuldu (8/8 SP500-üyeliğiyle tutarlı); kart muhtemelen gerekmez; tek QC-adımı 1-hücrelik
  Security Master delist-olayı API sondası. Ek getiri: EDG-021'in ölçmediği `Delisting` erişim
  yolunu kapatır (②-④'ün delist-vekilini gerçeğe taşıyabilir).
- **Hesap gerektirmeyen iş var mı (C2-4?): EVET — C2-4 LEAN-yerel motor.** QC hesabı/katmanı/parası
  gerekmez (Apache-2.0). AMA sıfır-kurulum değil: bu makinede **dotnet YOK, docker YOK** (ölçüldü);
  önce toolchain kurulmalı. Boyut **L** → ayrı implementasyon turu; bu tur yalnız planladı.
- **Belge yolu:** `docs/KESIF-WP-QC-2026-08-09.md` (bu dosya).
