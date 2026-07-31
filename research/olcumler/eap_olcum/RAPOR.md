# EAP (KAZANÇ-ÖNCESİ DUYURU PRİMİ) — ÖN-KAYITLI ÖLÇÜM RAPORU

**Tarih:** 2026-07-31 · **Rol:** Rol 2 (salt-ölçüm) · **Program:** ROADMAP §3.0b, 4 aday aileden
tek geçen aday · **Statü:** ölçüm tamamlandı, hüküm aşağıda.

---

## 1. HÜKÜM (ön-kayıtlı eşiğe göre — eşik SONRADAN ESNETİLMEDİ)

> **GEÇMEDİ.** Ön-kayıtlı BAŞARI kriteri iki şart istiyordu; **ikisi de karşılanmadı.**

| Ön-kayıtlı şart | Gerekli | Ölçülen | Sonuç |
|---|---|---|---|
| Olay-fazla-getiri CI'si 0'ı dışlar | CI ∌ 0 | **+9,0 bps**, CI95 **[−13,3 · +31,9]** | ❌ 0'ı kapsıyor |
| Net büyüklük ≥ 3×friksiyon | ≥ **30 bps**/olay | **+9,0 bps** (friksiyon sonrası **−1,0 bps**) | ❌ eşiğin çok altında |

### "Edge yok" mu, "ölçülemedi" mi? → **EDGE YOK** (ölçüldü, körlük değil)

Bu ayrım ciddiye alındı, çünkü birincil pencerede **kıl payı** güç sorunu vardı:

- Birincil ölçümün küme-bootstrap SE'si **11,6 bps**, MDE₈₀ = **32,4 bps** — yani tam 30 bps'lik
  bir etkiyi saptama gücü **%74**, konvansiyonel %80'in *hemen* altında. Tek başına bu sayıyla
  dürüst hüküm "ölçülemedi" olurdu.
- Bu yüzden **aynı boru hattı** daha uzun geçmişe uygulandı (§11): **2014-2026, n=12.123 olay,
  151 küme**. Orada **MDE₈₀ = 19,2 bps < 30 bps** → **ölçüm eşiği artık GÖREBİLİYOR.**
- Ve etki yine yok: **+6,8 bps**, CI95 **[−6,5 · +20,5]**. Bootstrap kütlesinin yalnız
  **%0,07'si** 30 bps'in üstünde.

> Yani: ön-kayıtlı büyüklükteki bir EAP primi, onu görebilecek keskinlikteki bir ölçümle
> **arandı ve bulunamadı**. Hüküm "ölçemedik" değil, **"ölçtük, yok"**.

**KILL kriteri (ABD-daralması) — DOĞRULANMADI.** Birincil pencerede yıl eğimi +19,2 bps/yıl
(CI [−1,3 · +39,7]); **13 yıllık** güç ekinde eğim **+2,63 bps/yıl**, CI95 **[−0,97 · +6,37]** —
**düz**. Narayanamoorthy daralma tezi bu evrende **doğrulanmadı**; ama bu şık bağımsız olarak boş
döndü, çünkü **daralacak bir etki zaten yok**. Arşiv kararı KILL'den değil, **BAŞARI şartının
karşılanmamasından** geliyor.

**Öneri:** **EAP ailesi ARŞİVE.** §3.0b'nin "4 aday aileden tek geçen aday"ı da ölçümle kapandı;
dört adayın dördü de elendi. Ayrı bir kalem olarak taşınması gereken tek şey §10'daki
**kıyas-kirlenmesi bulgusu** — o EAP'ye değil, evren-medyanı kullanan **tüm** ölçümlerimize ait bir
altyapı kusuru ve kendi ön-kaydını hak ediyor.

**Hedef sözleşmesi md.5 ile ilişki:** "edge yok hükmü ölçümle kayda geçti" şıkkı bu ölçümle
**üçüncü kez** karşılandı (SI · insider · EAP). Makine tek aileye mahkûm değil — ve üç ailenin
üçünü de *ölçerek* öldürdü.

---

## 2. ÖN-KAYIT (ROADMAP §3.0b'den, değiştirilmeden)

- **Giriş:** duyurudan ~10 **işlem günü** önceki kapanış.
- **Çıkış:** duyuru-**öncesi son** kapanış.
- **BAŞARI:** olay-fazla-getiri CI'si 0'ı dışlar **VE** net büyüklük ≥ 3×friksiyon
  (10 bps round-trip → eşik **≥30 bps/olay**).
- **KILL:** ABD-daralması (Narayanamoorthy) bizim evrende doğrulanırsa arşiv.
- Ölçüm zemini: kendi evren + kendi takvim verisi, hayalet-filtreli sandbox.

---

## 3. VERİ — ulaşılan GERÇEK pencere ve kota

**Kazanç tarihleri.** Önce yerel kaynaklara bakıldı (mandat gereği):

| Kaynak | Bulunan | Yeterli mi |
|---|---|---|
| `state/earnings.csv` | 194 satır, **yalnız ileri takvim** (2026-07/08) | ❌ |
| `state/sprint/20260722-093305/state/earnings.csv` | 2.176 satır ama derin geçmiş **yalnız 15 sembolde** (2022-2026 medyanı ticker başına **1** tarih) | ❌ |

Yetmediği için harici kaynağa gidildi — **ama FMP'ye DEĞİL.** Repoda zaten kablolu olan
**Nasdaq'ın anahtarsız takvimi** (`data.nasdaq_earnings_window`) geçmiş tarihleri de servis ediyor.

> **KOTA HARCAMASI: 0 (SIFIR) FMP çağrısı.** Tavan ≤120 idi; **hiç kullanılmadı.**
> `state/fmp_usage.json` dokunulmadı (mtime 07-30 03:53, değişmedi). FMP zaten
> "Limit Reach" durumundaydı (iki anahtar da 429) — bu yol seçilseydi ölçüm **yapılamazdı**.
> Nasdaq'a **3.283 anahtarsız gün-isteği** yapıldı, **0 hata**.

**Ulaşılan pencere (uydurma yok, ölçülen):**

| | Pencere | İş günü | Kapsama | Olay |
|---|---|---|---|---|
| **BİRİNCİL (ön-kayıtlı)** | 2022-01-01 → 2026-07-31 | 1.218/1.218 | **%100, boşluk yok** | **4.591** |
| Güç eki (ikincil) | 2014-01-01 → 2021-11-30 | 2.065/2.065 | **%100** | +7.532 |

Toplam **3.283 gün-dosyası, 0 eksik gün, 0 hata**; ham takvimde 78.118 satır (tüm semboller).

- **Olay sayısı 4.591**, 250 sembol (evren 251; **FISV**'in bar dosyası yok — emekli FI'nin halefi,
  seri 2025-11-11'de başlıyor, mühendislik günlüğünde beyanlı).
- Yıl başına **~1.000 olay** (2022: 989 · 2023: 994 · 2024: 995 · 2025: 996 · 2026 kısmi: 617).
  251 sembol × 4 çeyrek = 1.004/yıl → **iç tutarlılık sağlaması geçti**.
- Ham olay defteri 12.307 satır (2014-2026); birincil ölçüm bunu **2022+**'ye filtreliyor.
  Düşenler: 5.690 (panel öncesi, 2014-2019) · 1.949 (2020-2021) · 50 (bar yok) · 27 (pencere eksik)
  → **4.591 kullanıldı**. Düşenlerin tamamı §11'in güç ekinde ayrıca ölçülüyor.

**Tarih doğruluğu — bilinen gerçeğe karşı sağlama (uydurma yasağı):**

```
AAPL 2024: 02-01, 05-02, 08-01, 10-31   MSFT 2024: 01-30, 04-25, 07-30, 10-30
JPM  2024: 01-12, 04-12, 07-12, 10-11   NVDA 2024: 02-21, 05-22, 08-28, 11-20
COST 2024: 03-07, 05-30, 09-26, 12-12   (off-cycle mali yıl — doğru)
```

Hepsi gerçek duyuru tarihleriyle **birebir**.

### 3.1 DUYURU SAATİ (BMO/AMC) — ALAN YOK, BEYAN EDİLİYOR

**Nasdaq geçmiş takvimde `time` alanını BOŞ döndürüyor:** 78.118 satırın **%100'ü**
`time-not-supplied`. (Alan yalnız *gelecek* duyurularda dolu: 54 BMO + 21 AMC.)

Mandat gereği **muhafazakâr BMO** varsayıldı → çıkış = duyuru gününden **bir önceki** kapanış.
Bu yön bilinçli: AMC varsaymak, gerçekte BMO olan isimlerde **ileri-bakış** yaratırdı.

**Saat, beyandan değil VERİDEN okundu** — duyuru tarihine göre ofset başına ortalama |getiri|:

| ofset | −3 | −2 | −1 | **0** | **+1** | +2 | +3 |
|---|---|---|---|---|---|---|---|
| bps | 138,7 | 135,2 | 135,7 | **308,0** | **331,8** | 164,6 | 150,2 |

İki şeyi birden kanıtlıyor:
1. **Tarihler gerçek ve hizalı** — sıçrama tam 0/+1'de, başka yerde değil.
2. **Ölçüm penceresine sızıntı YOK** — −1, −2, −3 taban oynaklıkta (~136 bps). Yani çıkışımız
   (t₀−1) gerçekten duyuru öncesi; kazanç şoku pencereye karışmıyor.

Sıçramanın hem 0'da hem +1'de olması evrenin **BMO/AMC karışımı** olduğunu gösteriyor
(JPM tipi BMO ↔ AAPL/NVDA tipi AMC). Duyarlılık: AMC varsayımıyla ana sonuç **+3,7 bps**
(CI [−21,8 · +29,7]) — hüküm değişmiyor. *(BMO isimleri için ileri-bakış içerir; karar ölçütü değil.)*

---

## 4. YÖNTEM

- **Barlar:** `state/bars` **kopyası** üzerinde (copytree sandbox), repo'nun **kendi**
  `data.sanitize_bars` kapısından geçirildi — takvim kapısı yeniden yazılmadı, **çağrıldı**.
  Hayalet temizliği: **430 takvim-dışı satır düştü** (240 sembol; 2025-05-26 Memorial Day +
  2018-11-22 sınıfı), **3 düzeltilmemiş satır karantinaya** alındı (CHD, EL, PINS).
  Kitlesel takvim reddi: **0 seri**. Panel: 1.651 seans, 2020-01-02 → 2026-07-29.

  **Kapının çalıştığı somut olarak doğrulandı** (BT-2'nin kayıtlı vakası, BKNG):

  | | 05-23 | **05-26** | 05-27 | 2025-05 maks hareket |
  |---|---|---|---|---|
  | Ham CSV | 213,31 | **5332,80** | 218,07 | **%2.400** |
  | Panel (filtreli) | 213,31 | **— (düştü)** | 218,07 | **%2,4** |

  Yani ölçüm zemini gerçekten temiz; hayalet getiriler fazla-getiri hesabına girmedi.
- **Fazla getiri** = olay log-getirisi − **aynı seans penceresindeki** evren medyanı (**kendisi
  hariç**). Ek okumalar: sektör medyanı (kendisi hariç), SPY.
- **CI = KÜME bootstrap'i** (10.000 tekrar, küme = **çıkış ayı**, 55 küme). Gerekçe: kazanç
  sezonu olayları takvimde yığıyor; bağımsız-olay varsayımı CI'yi yapay olarak daraltırdı.
  Naif t-CI de raporlanıyor ki farkı görünsün.

---

## 5. ANA SONUÇLAR (birincil, ön-kayıtlı pencere)

| Ölçüm | n | Ortalama | CI95 (küme) | CI95 (naif) | Medyan | İsabet | 0-dışı |
|---|---|---|---|---|---|---|---|
| **[−10,−1] fazla getiri (ANA)** | 4.591 | **+9,0 bps** | **[−13,3 · +31,9]** | [−6,4 · +24,4] | +13,0 | %51,5 | ❌ |
| [−5,−1] alt pencere | 4.591 | +5,4 bps | [−7,9 · +19,1] | [−5,6 · +16,4] | +12,8 | %51,6 | ❌ |
| Sektör-nötr [−10,−1] | 4.589 | +12,6 bps | [−4,2 · +31,0] | [−1,3 · +26,4] | +20,7 | %52,5 | ❌ |
| SPY-nötr [−10,−1] | 4.591 | +5,9 bps | [−26,2 · +39,7] | [−9,7 · +21,4] | +8,1 | %50,7 | ❌ |
| *(ham getiri, kıyassız)* | 4.591 | +66,7 bps | [−1,7 · +133,2] | [+49,2 · +84,3] | +69,1 | %55,9 | ❌ |

**Hiçbiri** ön-kayıtlı eşiği geçmiyor. İsabet oranı her okumada ~%51-52 — yazı-tura.
Ham getirinin naif CI'sinin 0'ı dışlaması ama küme CI'sinin dışlamaması, kümelemenin neden
zorunlu olduğunun canlı kanıtı (o fark saf piyasa yönü).

### Yıl kırılımı ve decay (KILL testi)

| Yıl | n | Ortalama | CI95 | Bonferroni (α=0,01) |
|---|---|---|---|---|
| 2022 | 989 | **−52,6 bps** | [−105,3 · −3,1] | geçmedi |
| 2023 | 994 | +18,8 bps | [−13,9 · +60,5] | geçmedi |
| 2024 | 995 | +28,8 bps | [−3,1 · +78,6] | geçmedi |
| 2025 | 996 | **+25,5 bps** | [+1,1 · +59,3] | geçmedi |
| 2026 (kısmi) | 617 | +33,6 bps | [−63,2 · +140,8] | geçmedi |

Ham %95 ile 2 hücre "geçiyor" (2022 **negatif**, 2025 pozitif) — **Bonferroni sonrası 0**.
5 hücrede 1 marjinal geçiş tam olarak şansın ürettiği şey. **Eğim +19,2 bps/yıl**
(CI [−1,3 · +39,7]) → **daralma doğrulanmadı**.

### Sektör kırılımı (11 hücre)

Ham %95 ile 3 hücre 0'ı dışlıyor — **işaretleri karışık**: energy +102,9 · industrials +60,5 ·
health **−93,8**. **Bonferroni (α=0,0045) sonrası yalnız health kalıyor ve o NEGATİF.**
Eşiği de aşan hücre: **0**. Bu, SI ve insider ailelerini öldüren çoklu-sınama deseninin aynısı
(mühendislik günlüğü: *"18 hücrede çoklu-sınama sonrası 0"*).

---

## 6. PLACEBO — duyuru-DIŞI pencereler

Aynı hisseler, aynı dönem, her ticker'ın **kendi** kazanç çıkışlarından ≥25 seans uzak, olay
başına 3 pencere (dönem-eşleştirmeli).

| | n | Ortalama | CI95 |
|---|---|---|---|
| Olay pencereleri | 4.591 | +9,0 bps | [−13,3 · +31,9] |
| Placebo pencereleri | 13.731 | −3,8 bps | [−20,1 · +11,4] |
| **Fark (olay − placebo)** | — | **+12,8 bps** | **[−14,2 · +41,8]** ❌ |

**Kazanç öncesi pencereler, rastgele pencerelerden ayırt edilemiyor.**

---

## 7. POZİTİF KONTROLLER

| # | Kontrol | Sonuç | Hüküm |
|---|---|---|---|
| **PK-1** | **Tarih hizası / duyuru-günü oynaklık sıçraması** | tepki seansı **308,6 bps** vs taban **139,8 bps** → **oran 2,21** (n=4.566 vs 64.629) | ✅ **GEÇTİ** |
| PK-2 | 12-1 momentum IC (aylık Spearman, n=66 ay) | IC **+0,023**, CI [−0,032 · +0,078], t=0,82 | ⚠️ belirsiz |
| PK-3 | Kısa-vade reversal IC (n=77 ay) | IC **+0,006**, CI [−0,044 · +0,055], t=0,23 | ⚠️ belirsiz |

**Dürüst okuma:** *Bu* boru hattını sınayan kontrol **PK-1'dir** ve kesin geçti — olay hizası,
pencere kurulumu ve getiri hesabı çalışıyor. PK-2/PK-3 **farklı** bir makineyi (aylık kesitsel IC)
sınıyor ve **66-77 aylık gözlemle güçsüz**; sonuçları "boru hattı kör" demiyor, "bu evren-dönemde
aylık momentum/reversal saptanamıyor" diyor — ki bu, kayıtlı G1 çelişkisiyle ve large-cap
literatürüyle (Martineau, Subrahmanyam) tutarlı. **Yine de bir zayıflıktır ve öyle kaydedilir:**
EAP nullünün tek dayanağı PK-1'dir, üç kontrolün üçü değil.

---

## 8. SAĞLAMLIK — null yöntem seçiminin yan ürünü mü?

9 varyant; ortalama ve CI:

| Varyant | Ortalama | CI95 | 0-dışı |
|---|---|---|---|
| Küme = ay (birincil) | +9,0 | [−13,6 · +32,0] | ❌ |
| Küme = çeyrek | +9,0 | [−20,7 · +37,5] | ❌ |
| Küme = hafta | +9,0 | [−9,8 · +28,1] | ❌ |
| Küme = gün | +9,0 | [−7,6 · +26,1] | ❌ |
| Küme = **sembol** (250) | +9,0 | [−9,6 · +27,3] | ❌ |
| Winsorize %1 | +10,2 | [−9,8 · +30,5] | ❌ |
| Winsorize %5 | +13,8 | [−1,3 · +28,9] | ❌ |
| Medyan | +13,0 | [−1,3 · +27,8] | ❌ |
| **Ay-eşit-ağırlık** | **+39,7** | **[+1,1 · +78,3]** | ✅ |

**Tek geçen varyant: ay-eşit-ağırlık.** Bunu saklamıyorum, ama **ön-kayıtlı ölçüt DEĞİL**:
ön-kayıt "≥30 bps/**olay**" diyor, yani **olay-ağırlıklı** ortalama. Ay-eşit-ağırlık, 10 olaylı
seyrek bir ayı 173 olaylı sezon ayıyla eşitler — ve tam da gürültülü küçük-n ayları yukarı
ağırlıklandırdığı için yükseliyor. 9 varyantta 1 geçiş, çoklu-sınama beklentisinin içinde.

---

## 9. SURVIVORSHIP BEYANI (zorunlu)

**Evren BUGÜNÜN evrenidir** — 251 isim, 2026-07-20/30 kurulumu. 2022-2026 olayları yalnız
**2026'ya kadar ayakta kalan** isimler üzerinde ölçüldü. Ara dönemde delist olan/evrenden düşen
şirketler örnekleme **hiç girmedi**. Emekli 8 sembol (`data.RETIRED_SYMBOLS`: ANSS, DFS, FI, HES,
IPG, K, PARA, WBA) hariç tutuldu.

**Yön:** hayatta-kalma yanlılığı fazla getiriyi **YUKARI** iter (batan isimlerin kazanç-öncesi
çöküşleri örneklemde yok). Yani **+9,0 bps bir TAVANDIR**; PIT-temiz bir evrende daha düşük olması
beklenir. Bu, null hükmünü **güçlendirir** (yanlılık lehte olmasına rağmen eşik geçilemedi).

**PIT evren yok:** BT-3 açık; nokta-zamanlı üyelik verisi bu depoda mevcut değil.
Takvim verisi ise doğası gereği PIT-temiz (duyuru tarihi sonradan değişmez).

---

## 10. YAN BULGU — KIYAS ÖLÇÜTÜ KİRLENMESİ (metodolojik, kaydedilmeli)

Ön-kayıtlı kıyas "aynı-pencere evren medyanı". **Ölçüldü:** bir olayın penceresinde evrenin
ortalama **%64,1'i** (medyan %73,6, maks %85,6) **kendi kazanç-öncesi penceresindedir**.

Eğer EAP gerçek olsaydı, bu isimler medyanı da yukarı iterdi ve fazla getiri **tam da etkinin en
yaygın olduğu anda sıfıra bastırılırdı**. Yani ön-kayıtlı kıyas, kendi ölçtüğü etkiye karşı
sistematik olarak kör.

**Düzeltilmiş okuma** (kıyastan kendi penceresindekiler çıkarılarak; **eşik aynen 30 bps**):

| | Ortalama | CI95 | MDE₈₀ | Hüküm |
|---|---|---|---|---|
| Kirli kıyas (ön-kayıtlı, aynı örneklem) | +9,3 bps | [−13,3 · +33,1] | 32,4 | ❌ |
| **Temiz kıyas** | **+21,1 bps** | **[−3,9 · +47,6]** | 36,8 | ❌ |

Düzeltme etkiyi **+11,8 bps** yukarı taşıyor — **ama hâlâ CI 0'ı kapsıyor ve eşiğin altında**
(ve temiz kıyas daha az isim kullandığı için CI *genişliyor*). **Hüküm değişmiyor.**

Kirlilik çeyreğine göre kırılım **monoton DEĞİL** (Q1 +56,8 · Q2 −9,2 · Q3 +36,5 · Q4 −0,9) —
yani "seyrek aylarda / sezon dışında edge var" hikâyesi **gürültü gibi davranıyor**, tutarlı bir
gradyan değil. Bu yüzden §8'deki ay-eşit-ağırlık varyantının geçmesi de **açıklanmış** sayılır:
seyrek ayları yukarı ağırlıklandırıyor, ama o ayların yüksekliği kalıcı bir yapı değil.

**Neden EAP'yi kurtarmıyor:** düzeltme etkiyi yukarı taşıyor ama eşiğin **hâlâ** altında bırakıyor,
ve güç ekinin 12,6 yıllık örnekleminde ana okuma zaten yeterli güçle sıfır. Kirlenme **gerçek bir
metodoloji kusurudur** — ama EAP'nin nullünün sebebi değildir.

---

## 11. GÜÇ EKİ — genişletilmiş geçmiş (İKİNCİL, ayrı beyan)

**Neden var:** birincil pencere 30 bps eşiğini kıl payı göremiyordu (MDE₈₀ 32,4 > 30). Aynı
anahtarsız kaynak geçmişe de çalıştığı için örneklem **2014'e** kadar genişletildi.
**Eşik ESNETİLMEDİ** (30 bps aynen); **ön-kayıtlı birincil sonuç DEĞİŞMEDİ** (yeniden üretim
kontrolü: n=4.591, +9,0 bps, CI [−13,25 · +31,94] — bit-bit aynı).

**Örneklem:** 2014-01 → 2026-07, **12.123 olay**, **151 aylık küme**, 251 sembol. Yıl başına
906-1.000 olay (13 yılın hepsinde tutarlı). Panel 3.413 seans (2013-01-02'den), aynı hayalet filtresi.

| Ölçüm | n | Ortalama | CI95 (küme) | **MDE₈₀** | Eşiği görebilir mi | P(ort ≥ 30bps) |
|---|---|---|---|---|---|---|
| **[−10,−1] (ANA)** | 12.123 | **+6,8 bps** | **[−6,5 · +20,5]** | **19,2 bps** | ✅ **EVET** | **0,0007** |
| [−5,−1] | 12.123 | +3,8 bps | [−5,1 · +13,2] | 13,2 bps | ✅ EVET | 0,0000 |
| Sektör-nötr | 12.121 | +9,1 bps | [−1,2 · +20,1] | 15,3 bps | ✅ EVET | 0,0000 |

**Üç okumanın üçü de:** yeterli güçte, CI 0'ı kapsıyor, eşiğin çok altında.

**Ön-kayıt penceresinin DIŞI (2014-2021, n=7.532) — bağımsız okuma:**
**+5,5 bps**, CI95 [−10,2 · +22,4] → **aynı null**. Ön-kayıtlı pencerede gördüğümüz şey döneme
özgü değil.

**Yıl kırılımı (13 yıl):**

| 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| +15,7 | −23,8 | +2,9 | −3,7 | −10,3 | **−30,7** | **+63,0** | +27,7 | **−52,6** | +18,8 | +28,8 | **+25,5** | +33,5 |

13 hücrenin 4'ü ham %95 ile 0'ı dışlıyor — **işaretler karışık** (2019 −30,7 · 2020 +63,0 ·
2022 −52,6 · 2025 +25,5) ve **hiçbiri ardışık yıllara taşınmıyor.** Kalıcı bir etkinin değil,
yıllık gürültünün imzası. **Eğim +2,63 bps/yıl, CI [−0,97 · +6,37] — düz çizgi.**

> **Not (dürüstlük):** geriye gidildikçe hayatta-kalma yanlılığı **artar** — 2014'te de ayakta olan
> isimlerle ölçüyoruz. Yani bu ek pencere fazla getiriyi **yukarı** itmeli. Buna rağmen +6,8 bps
> çıkması null'ü **güçlendirir**, zayıflatmaz.

---

## 12. OPERATÖRE NOTLAR

1. **Kota:** ölçüm **0 FMP çağrısı** harcadı (tavan 120). Kazanç takvimi için repoda zaten kablolu
   **anahtarsız Nasdaq** yolu geçmişe de çalışıyor — `earnings.refresh`'in birincil kaynağı bu ve
   FMP'nin 250/gün duvarına karşı **evren-boyundan bağımsız**. Geçmiş dolgusu gerekirse bu yol
   kullanılabilir (**3.283 gün / 0 hata** ölçüldü; 12,6 yıllık takvim artık `cal_cache/` altında hazır).
2. **`state/earnings.csv` geçmişi yok** (194 satır, yalnız ileri takvim). PEAD çapası
   (`days_since_report`) ve karartma guard'ı bugünü koruyor ama **geçmiş ölçümleri besleyemiyor**.
   Sprint kum-havuzundaki 2.176 satırlık dosya da yalnız 15 sembolde derin.
3. **Salt-ölçüm mührü:** ölçüm başında repo `state/events.jsonl`'e **5 iyi-huylu obs satırı**
   yazıldı (sanitize kapısının kendi hayalet uyarıları) — fark edilir edilmez `store.append_jsonl`
   sandbox'a yönlendirildi ve repo state'ine yazma sert hataya bağlandı. Sonrasında **repo state'e
   tek bayt yazılmadı**; `fmp_usage.json`, `bars/`, `earnings.csv` dokunulmadı.
4. **EŞ ZAMANLI AJAN UYARISI (operasyonel):** ölçüm sırasında repo `state/events.jsonl`'e
   **başka bir oturum** yazıyordu (`bar_ghost_session_dropped SPY` + `bar_cache_repaired SPY`,
   21:38-21:39 UTC) — muhtemelen §3.0b'nin *çıkış paketi* ölçümü. Benim ölçümüm barların
   **kopyası** üzerinde koştuğu için etkilenmedi; **copytree sandbox deseni tam da bunun için
   zorunlu.** Kayıtlı ders ("file_lock süreç-içi") burada canlı doğrulandı.
5. **Yeni ön-kayıt adayı (bu ölçümün geçme hükmü DEĞİL):** §10'daki kıyas-kirlenmesi, evren-medyanı
   kullanan **diğer** ölçümleri de etkiler (component_ic, karşı-olgusal R tabloları). Kazanç
   sezonunda evrenin ~%74'ü kendi penceresindeyse, "evren medyanına göre fazla getiri" sistematik
   olarak sıkıştırılmış demektir. Bu, EAP'den bağımsız bir **altyapı bulgusudur**.

---

## 13. ÜRETİLEN ARTEFAKTLAR (hepsi sandbox içinde)

```
scratchpad/eap_olcum/
├── RAPOR.md                  ← bu dosya
├── eap_ic_sonuc.json         ← tüm sayılar (ana + sağlamlık + kirlenme + hüküm)
├── eap_guc_eki.json          ← genişletilmiş geçmiş (§11)
├── olaylar.csv               ← 4.591 olay, olay başına satır
├── events.json               ← ham olay defteri (tarih + saat bayrağı)
├── sanitize_rapor.json       ← hayalet/karantina muhasebesi
├── panel.pkl / panel_ext.pkl ← hayalet-filtreli kapanış panelleri
├── cal_cache/                ← 3.283 gün-JSON (Nasdaq, anahtarsız, 2014-2026)
├── sandbox.py                ← SALT-ÖLÇÜM MÜHRÜ
└── {build_panel,build_events,analyze,verdict,robustness,benchmark_fix,supplement}.py
```
