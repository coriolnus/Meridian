# EDG-2026-056 — SPLIT ORAN-İMZASI RETRO TARAMASI (K=1, hücre `oran_imza_retro`)

**Koşuldu:** 2026-08-24 · **Kapsam:** WP4 / kalem K2 · **Kart:**
`research/cards/EDG-2026-056-split-oran-imzasi.yaml` (karta DOKUNULMADI — hükmü Rol-1 işler,
CLAUDE.md madde 3).

**Ölçüm tabanı beyanı:** `state/bars/*.csv` **SALT-OKUMA** okundu (`csv` modülüyle doğrudan);
`meridian` motoru **import EDİLMEDİ**, `state/` altına **YAZILMADI**, git komutu koşulmadı.

---

## 0. HÜKÜM (karar kuralı doğrudan okundu)

| Ölçüt | Donuk eşik | ÖLÇÜLEN | Geçti mi |
|---|---|---|---|
| Yanlış-pozitif oranı | ≤ %20 | **%41,8** (23/55) | ✗ |
| Bilinen split yakalama | ≥ %80 | **%34,8** (32/92) | ✗ |

→ **“İMZA TEK BAŞINA YETERSİZ.”** Kalem KAPANIR; bölünme körlüğü **BEYANLI** kalır (veri
sağlayıcı düzeltmesine bağlı). Dedektör kablolaması **YAPILMAZ**.

İki eşik de tek yönde değil, **iki yönde birden** düştü: dedektör hem fazla ateş ediyor hem
yer gerçeğinin üçte ikisini kaçırıyor.

---

## 1. DONMUŞ TANIM VE LİSTE (kill kriterleri)

| Artefakt | sha256 |
|---|---|
| `donuk_tanim.json` (oran kümesi + toleranslar + karar kuralı) | `d456efd2a25ed5cd2403c6f817bfdabfecc636deb85b505bfd19cf493c98061b` |
| `bilinen_split_donuk.json` (yer gerçeği) | `60177962804f9b0b63c446b0d80ac0e013c3ae0f8c81c9f6a41c605d6d48fbb7` |
| kaynak `state/bars_integrity.json` | `ab6b2e5995ba3084782cbcedc2982a7d56d0d16a6245cadff14e74e5edfdedcc` |

- **Liste ölçümden ÖNCE donduruldu** (`dondur_liste.py` bir kez koştu) ve ölçüm sırasında
  **genişletilmedi**.
- **Tolerans %2 donuk** (karttan), ölçümden sonra değiştirilmedi.
- **Hacim teyidi atlanmadı** — aday tanımı fiyat VE hacim koşulunun VE'sidir.
- **Karantina kuralına dokunulmadı** (`meridian/adapters/data.py` okunmadı-dışı, değiştirilmedi).

### 1a. Yer gerçeği nereden geldi — ve `state/quarantine` neden kullanılamadı
`state/quarantine/` **ÖLÇÜLDÜ**: içinde tek dosya var (`sp500_constituents.FIXTURE-2026-07-18.json`,
`docs/INTEGRITY-AUDIT.md` C2 vakası) — **SIFIR bölünme kaydı**. Repodaki tek makine-okunur
ölçek-dikişi defteri `state/bars_integrity.json`dur; **BİRİNCİL** yer gerçeği onun
`sinif=="olcek_dikisi"` (K1) satırlarıdır: **92 olay / 61 sembol**, 92'sinin de tarihi arşivde var.

**İKİNCİL (hüküm dışı):** `docs/TESHIS-MNST-SPLIT-2026-08-12.md`'deki dış Massive takvimi
(MNST 2026-08-11 1→2, 2023-03-28 1→2, 2016-11-10 1→3). Bizim temizlik kaydımız olmadığı için
karar kuralına GİRMEDİ.

### 1b. Kartın kendi içindeki çelişki — ölçümden ÖNCE çözüldü
Kart tezi oran kümesinde “1:2 ters”i **anıyor**, `beyanli_sinirlar(2)` ise ters-split'i “imza
sınıfı dışında” **sayıyor**. Donuk tanımda tez cümlesi esas alındı: küme **iki yönlüdür**, yön
kırılımı ayrıca raporlanır (aday 55 → ileri 26 / ters 29). Bu seçim `donuk_tanim.json`da
ölçümden önce yazılıdır.

### 1c. Kartın BIRAKTIĞI boşluk — hacim toleransı
Kart hacim teyidi için **sayı vermiyor** (“v[t]/v[t-1] ≈ r”). Fiyat için verilen %2 günlük hacim
gürültüsü için fizikî olarak anlamsız olduğundan, ölçümden ÖNCE log-simetrik bir kat-toleransı
donduruldu: **F = 1,5 BİRİNCİL** (hüküm buradan okunur), merdiven {1,25 · 1,5 · 2,0} yalnız
dayanıklılık için. **Üç basamağın hiçbiri eşikleri geçmiyor** (§4) — hüküm F seçimine duyarlı değil.

---

## 2. TARAMA — ne koştu, ne çıktı

`tara.py`: 260 dosya, **1.349.764 ardışık bar çifti**, fiyat hesaplanamayan çift **0**.

| Sayım | Değer |
|---|---|
| Fiyat kapısını geçen (hacimden ÖNCE) | 107 |
| … hacmi **ÖLÇÜLEMEYEN** (v≤0/NaN → aday DEĞİL, ayrı sayıldı) | 16 |
| … hacim teyidi DÜŞEN | 36 |
| **ADAY (fiyat ∧ hacim)** | **55** |
| bilinen-split ile **EŞLEŞEN** | 32 |
| **EŞLEŞMEYEN aday** (yanlış-pozitif adayı) | 23 |
| **YAKALANMAYAN** bilinen split | 60 / 92 |

Adların tamamı `sonuc.json` içinde: `eslesen_adaylar_ADIYLA`, `eslesmeyen_adaylar_ADIYLA`,
`yakalanmayan_bilinen_ADIYLA`.

---

## 3. NEDEN DÜŞTÜ — iki kök, ikisi de ölçüldü

### 3a. Yakalama neden %35 — %2 toleransı gerçek dikişler için FAZLA DAR (42/60)
Kaçan 60 olayın **42'si fiyat kapısında** düşüyor: en yakın donuk orana bağıl sapmaları
%2'nin üstünde. Örnekler (r = c[t-1]/c[t]):

| Sembol | Tarih | r | en yakın oran | sapma |
|---|---|---|---|---|
| ABT | 2013-01-02 | 2,0437 | 2:1 | %2,19 |
| CB | 2006-01-03 | 1,9596 | 2:1 | %2,02 |
| CSX | 2006-01-03 | 2,0433 | 2:1 | %2,17 |
| GILD | 2006-01-03 | 3,7272 | 4:1 | %6,82 |
| AVGO | 2009-08-06 | 0,0062 | 1:20 | %87,7 |
| CHTR | 2010-09-15 | 0,0009 | 1:20 | %98,3 |

Sebep yapısal: K1 dikişlerinin çoğu **saf bölünme değil** — spinoff yeniden-tabanlaması
(ABT/ABBV 2013-01-02), temettü-düzeltmeli sağlayıcı taban değişimi, ya da hiç oran olmayan
hayalet-geçmiş ölçek atlaması (AVGO, CHTR). Saf bir bölünme oranı beklemek bunları göremez.
Kalan **18'i hacim kapısında** düşüyor: fiyat oranı çok temiz (ör. HES 2006-06-01 r=0,3332,
1:3'e sapma %0,04; EXPE 2006-01-03 r=1,9968, %0,16) ama hacim serisi teyit etmiyor — kaynağın
tabanı değişirken **hacim alanı yeniden ölçeklenmemiş**.

### 3b. Yanlış-pozitiflerin %22'si aslında GERÇEK BOZULMA — ama başka sınıfın
23 eşleşmeyen adayın **5'i tek bir güne yığılıyor: 2025-05-26** (DD · HON · KLAC · NFLX · NOW),
üçü de tam oran ve **vr/r = 1,000**:

| Sembol | 05-23 kapanış | 05-26 kapanış | oran | hacim oranı |
|---|---|---|---|---|
| KLAC | 75,717 | 757,17 | ×10 | ÷10 (9.419.480 → 941.948) |
| NFLX | 118,54 | 1185,39 | ×10 | ÷10 |
| NOW | 200,87 | 1004,37 | ×5 | ÷5 (6.938.940 → 1.387.788) |
| HON | 444,06 | 222,03 | ÷2 | ×2 (1.268.759 → 2.537.518) |
| DD | 202,95 | 67,65 | ÷3 | ×3 |

Bu tam olarak `docs/RUNBOOK.md:1310`da kayıtlı **HAYALET SEANS** vakasıdır (2025-05-26
Memorial Day, “5 sembolde bölünmemiş ham fiyat”) — sayı da birebir 5. Yani dedektör **gerçek
bir bozulmayı, mükemmel imzayla yakalıyor**; “yanlış-pozitif” sayılmasının tek sebebi bu
satırların BİRİNCİL yer gerçeğinde olmaması: K1 kuralı geri-dönen satırları **bilerek** dışarıda
bırakır (`data.py:531` — “geri dönüyor → karantinanın işi, dikiş değil”), o sınıf karantina
hattınındır. Kartın kendi ifadesiyle: *komşu sınıf, oran-imza ONDAN FARKLI.*

Aynı sınıftan sıçra-ve-geri-dön çiftleri: CHD 2013-12-18/19, EL 2012-01-20/23,
UNP 2014-06-06/09, HON 2025-05-26/27, ALB 2006-10-31.

Geriye kalan yanlış-pozitifler **gerçek piyasa günleridir** ve hepsi 3:2 (1,5) bandına düşüyor:
AIG 2008-09-24 · EOG/HES 2020-03-09 · TRGP 2020-03-18 · CCL 2020-04-01 · MDLZ 2012-10-02 ·
SNAP 2024-02-07. %50'lik bir kriz/kazanç hareketi ile 3:2 bölünme, bu imzayla **ayrılamıyor** —
kartın kill gerekçesindeki “yalnız fiyat oranı bölünmeyi ayıramaz” endişesi hacim teyidiyle de
kapanmıyor.

### 3c. Arşiv zaten split-düzeltilmiş — imzanın arayacağı şey çoğunlukla YOK
İkincil listedeki iki arşiv-içi MNST bölünmesinin ikisi de yakalanmadı, çünkü **imza yok**:

- MNST 2016-11-10 (1→3): 22,10 → 21,16 (r = 1,044)
- MNST 2023-03-28 (1→2): 52,34 → 51,60 (r = 1,014)

(MNST 2026-08-11 bölünmesi arşiv kapsamı dışı — yerel son bar 2026-07-28.) Kaynaklar
“YALNIZ split-adjusted” verdiği için (`docs/TESHIS-MNST-SPLIT-2026-08-12.md` §0 tablosu) gerçek
bölünmeler seride **iz bırakmaz**. Yani bu dedektörün BİRİNCİL yer gerçeği fiilen “gerçek
bölünmeler” değil, **sağlayıcı taban dikişleri**dir — kartın `beyanli_sinirlar(1)` uyarısının
ölçülmüş hâli.

---

## 4. DAYANIKLILIK (donuk merdiven — HÜKÜM DIŞI, eşik seçmez)

Hacmi ölçülebilen 91 fiyat adayı üzerinden:

| F | aday | eşleşen | YP | yakalama | eşikleri geçer |
|---|---|---|---|---|---|
| 1,25 | 34 | 18 | %47,1 | %19,6 | hayır |
| **1,5 (BİRİNCİL)** | **55** | **32** | **%41,8** | **%34,8** | **hayır** |
| 2,0 | 65 | 38 | %41,5 | %41,3 | hayır |

Hüküm hacim toleransı seçimine duyarlı değil.

---

## 5. BEYANLI SINIRLAR (bu ölçümün göremediği)

1. **Yer gerçeği = bizim kaydımız.** K1 eşikleri r ≥ 1,9 / r ≤ 0,55'tir; **3:2 gibi küçük oranlı
   dikişler bu yer gerçeğinde HİÇ YOK**. Yakalama oranı büyük-oranlı dikişlere yanlıdır.
2. **K1 kovası karışıktır**: gerçek bölünme + spinoff yeniden-tabanlaması + sağlayıcı taban
   değişimi aynı sınıfta. Bu yüzden “yakalanmayan bilinen split” sayısı, gerçek bölünme
   kaçırmasının ÜST sınırıdır, kendisi değil.
3. **2025-05-26 hayalet-seans kümesi** metodolojik olarak yanlış-pozitif sayıldı; olgu olarak
   gerçek bozulmadır (§3b). Farklı bir yer gerçeğiyle YP %41,8 yerine %32,7'ye (18/55) inerdi —
   **eşiği yine geçmezdi**, bu yüzden hüküm değişmez. (Bu sayı hükme GİRMEZ; kayda geçiyor.)
4. Ters-split yönü karta rağmen dahil edildi (§1b). **ÖLÇÜLDÜ** — yalnız ileri yön alınsaydı:
   aday 26 · eşleşen 13 · eşleşmeyen 13 → **YP %50,0**; yakalama, yer gerçeği de ileri yöne
   süzülürse (r>1 olan 50 olay) **%26,0**, süzülmezse (92 olay) **%14,1**. Hangi taban alınırsa
   alınsın hüküm yine “yetersiz”.
5. Yerel arşiv **donmuş fotoğraftır** (son barlar 2026-07-28 civarı); 2026-08 sonrası olaylar
   kapsam dışıdır.

---

## 6. DÜZELTME KAYDI (SİLME YOK)

- İlk koşumda `ikincil_merdiven_HUKUM_DISI` sayımı **yanlış tabandaydı**: merdiven, F=1,5
  kapısını ZATEN geçmiş havuz üzerinde sayılıyordu ve F=2,0 için totolojik “55” üretiyordu.
  Taban “hacmi ölçülebilen fiyat adayları (kapıdan ÖNCE)” olarak düzeltildi ve merdiven yeniden
  koşuldu. **Birincil hüküm satırı (F=1,5) değişmedi**: aday 55 · YP %41,8 · yakalama %34,8.
  Hiçbir eşiğe dokunulmadı.

---

## 7. ARTEFAKTLAR

| Dosya | Ne |
|---|---|
| `donuk_tanim.json` | ölçüm-öncesi donmuş kural (oran kümesi, %2, F=1,5, karar kuralı) |
| `dondur_liste.py` | yer gerçeğini donduran betik (BİR KEZ koştu) |
| `bilinen_split_donuk.json` | donmuş yer gerçeği (92 birincil + 3 ikincil) |
| `tara.py` | salt-okuma tarama (motor import etmez) |
| `test_tara.py` | dedektör davranış testleri (7 test — otoriter suite'e girmez, `testpaths=["tests"]`) |
| `sonuc.json` | tüm sayımlar + adıyla listeler + sha'lar |
