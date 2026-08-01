# research/edgar_facts — SEC EDGAR companyfacts PIT serileri

WP2'nin üç ailesinin (2.2 kısa-dönem momentum/turnover, 2.3 net-issuance, 2.5 gross
profitability) girdi verisi. Kaynak: SEC XBRL **companyfacts** API. Çekim: 2026-08-01.

**Bu dizin ÖLÇÜM DEĞİL, VERİ.** Eşik, hüküm, kart yok. Ölçüm kartları Rol-1'den gelir.

---

## 1. PIT semantiği — tek kural

Her satırda iki tarih vardır ve **karıştırılmaları sızıntıdır**:

| alan | anlamı |
|---|---|
| `end` | Değerin ait olduğu tarih (bilanço günü) veya dönem sonu. **Etikettir.** |
| `filed` | Değerin SEC'e verildiği gün. **Bu günden önce piyasa bu sayıyı BİLMEZ.** |
| `start` | Süreli ölçülerde (gelir, maliyet) dönem başı; anlık ölçülerde boş. |

> **Ölçüm `filed`'ı kullanır.** `t` gününde bilinen değer kümesi
> `df[df.filed <= t]`'dir; `end <= t` filtresi PIT DEĞİLDİR ve geleceği sızdırır.

Bunun canlı kanıtı veride var: Alphabet'in `end=2021-12-31` hisse adedi
2022-04-27'de dosyalanan 10-Q'da **662.121.000**, 2022-07-27'de dosyalanan 10-Q'da
(20:1 bölünme sonrası geriye dönük düzeltmeyle) **13.242.000.000**. Aynı `end`, iki
farklı değer, iki farklı `filed`. `end`'e göre çalışan bir ölçüm, 2022 Temmuz'daki
bilgiyi 2021 Aralık'ta biliyormuş gibi davranır.

**İlk ifşa** (bir dönemin ilk kez görüldüğü an):
`df.groupby(['symbol','tag','start','end']).filed.min()`.
Aynı `(tag,start,end)` için sonraki satırlar ya yeniden beyandır ya da düzeltmedir —
ikisi de gerçek olaylardır, silinmemiştir.

`filed - end` gecikmesinin **ilk ifşa** üzerinden medyanı: `ilk_ifsa_gecikme.csv`.
Özet: kapak sayfası hisse adedi **7 gün**, bilanço/gelir tablosu kalemleri **33–37 gün**.
(Ham satır üzerinden hesaplanan medyan ~390 gündür; bu, sonraki dosyalamalardaki
karşılaştırmalı tekrarların yarattığı bir yanılsamadır — PIT gecikmesi DEĞİLDİR.)

---

## 2. Dosyalar

| dosya | içerik |
|---|---|
| `shares_outstanding.csv.gz` | 161.856 satır · 258 sembol · 6 etiket |
| `fundamentals.csv.gz` | 142.499 satır · 258 sembol · 7 etiket |
| `kapsam.csv` | etiket × sembol sayısı × tarih aralığı × ham gecikme |
| `ilk_ifsa_gecikme.csv` | etiket × **ilk ifşa** gecikmesi (medyan/p10/p90/min/maks) |
| `sembol_kapsam.csv` | sembol başına seri sayıları ve tarih aralıkları |
| `tutarsizlik.json` | kaynaktaki tutarsızlıkların envanteri (düzeltilmedi) |
| `cik_haritasi.json` | sembol → CIK, kaynağı ve payı |
| `kaynak.json` | köken, indirme manifesti (sha256), fair-use notu |

`.csv.gz` düz CSV'dir; `pd.read_csv("shares_outstanding.csv.gz")` doğrudan okur.
Sıkıştırılmamış hâli 44 MB; depoda izlenen en büyük dosya 5,5 MB olduğu için gzip'lendi.

### Şema (iki seri de aynı)

`symbol, cik, taxonomy, tag, unit, start, end, filed, val, form, fy, fp, donem_gun, donem_turu, accn, frame`

- `form`: 10-Q / 10-K / 8-K / 10-K/A … — **çeyreklik mi yıllık mı sorusunun cevabı burası DEĞİL**;
  bir 10-K hem yıllık hem çeyreklik ölçü taşır.
- `donem_turu`: `anlik` (start yok, bilanço/kapak) · `ceyrek` (≤135 g) · `yarim` · `9ay` ·
  `yillik` (316–400 g) · `diger`. Dönem uzunluğu `donem_gun`'dan türetildi.
- `accn`: dosyalama numarası — satırı kaynağına kadar geri izlemeye yarar.
- `frame`: SEC'in takvim çerçevesi (varsa); mali yılı takvime oturtmak için.

### Etiketler

**shares_outstanding** — iki farklı semantik, karıştırma:

| etiket | semantik | not |
|---|---|---|
| `dei:EntityCommonStockSharesOutstanding` | **anlık sayım**, kapak sayfası | En taze PIT: medyan 7 gün gecikme |
| `us-gaap:CommonStockSharesOutstanding` | anlık sayım, bilanço | ~36 gün |
| `us-gaap:CommonStockSharesIssued` | anlık, **ihraç edilmiş** | Outstanding + hazine hissesi. Eşit DEĞİL |
| `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` | **dönem ortalaması** (EPS paydası) | Anlık sayım değil |
| `us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding` | dönem ortalaması, seyreltilmiş | |
| `us-gaap:WeightedAverageNumberOfShareOutstandingBasicAndDiluted` | dönem ortalaması | Eski/az kullanılan varyant |

Ağırlıklı ortalama etiketleri brief'te yoktu; **çok sınıflı ihraççılarda ilk üç etiketin
tamamen boş kalması** yüzünden eklendi (META, EL, MKC, HRL). Sebep yapısaldır:
çok sınıflı şirket kapak sayısını sınıf boyutuyla (dimensioned) etiketler ve
companyfacts API'si boyutlu ölçüleri taşımaz.

**fundamentals** — `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`,
`RevenueFromContractWithCustomerIncludingAssessedTax`, `CostOfRevenue`,
`CostOfGoodsAndServicesSold`, `GrossProfit`, `Assets`.

---

## 3. Kapsam (evren = `REPLAY_UNIVERSE` 251 + `RETIRED_SYMBOLS` 8)

| aile | tüm 259 | evren 251 |
|---|---|---|
| A) anlık hisse sayımı (3 etiket birleşimi) | 254 | **246** |
| — yalnız `dei` kapak sayısı | 247 | 239 |
| B) herhangi hisse serisi (ağ. ort. dahil) | 258 | **250** |
| C) gelir (3 etiket birleşimi) | 256 | **248** |
| D) maliyet (2 etiket birleşimi) | 182 | 178 |
| E) `GrossProfit` doğrudan | 125 | 122 |
| F) brüt kâr hesaplanabilir (E veya C∧D) | 188 | **184** |
| G) `Assets` | 258 | **250** |
| H) 2.5 gross profitability (F ∧ G) | 188 | **184** |

Tarih aralığı: `end` 2006-12-31 → 2026-07-30, `filed` 2009-04-15 → 2026-07-31.
XBRL zorunluluğu 2009'da başladığı için 2009 öncesi `end`'ler sonraki dosyalamaların
karşılaştırmalı sütunlarından gelir — **ilk ifşaları 2009 sonrasıdır** ve `filed` bunu
doğru söyler.

**2.5'in gerçek kısıtı budur:** brüt kâr, evrenin %73'ünde (184/251) hesaplanabilir.
Eksik 67 sembol tesadüfi değil — banka, sigorta, REIT, telekom ve enerji şirketleri
gelir tablolarında satış maliyeti satırı yayımlamaz. Ölçüm ya sektör kısıtlı bir
evrenle koşar ya da kapsamı hükümde açıkça beyan eder.

---

## 4. Spot doğrulama — bilinen bölünmeler

Ardışık iki dosyalama arasındaki hisse adedi sıçraması, bölünme oranını vermelidir:

| sembol | bölünme | beklenen | gözlenen | kullanılan etiket |
|---|---|---|---|---|
| AAPL | 2020-08-31, 4:1 | 4,00 | 3,98 | dei |
| NVDA | 2024-06-10, 10:1 | 10,00 | 9,97 | dei |
| AVGO | 2024-07-15, 10:1 | 10,00 | 10,03 | dei |
| GOOGL | 2022-07-18, 20:1 | 20,00 | 20,10 | us-gaap Outstanding |
| TSLA | 2022-08-25, 3:1 | 3,00 | 3,02 | dei |

Sapmalar (±%3) beklenen yöndedir: iki dosyalama arasında geri alım ve yeni ihraç olur.

---

## 5. Bilinen tutarsızlıklar (kaynakta; DÜZELTİLMEDİ)

Tam envanter `tutarsizlik.json`. Ölçüm tarafını doğrudan ilgilendirenler:

1. **İki gelir etiketi aynı şey değil.** 131 sembolde `Revenues` ve
   `RevenueFromContract...` aynı dönemde birlikte var; 25'inde fark %10'un üstünde.
   AVB 2026Q2: sözleşme geliri 1,78 M$, `Revenues` 778 M$ (REIT'te kira geliri sözleşme
   geliri değildir). COP 2026Q1: 13,50 Mr$ vs 15,76 Mr$. **Etiket önceliği ölçümde
   yazılmalı** (öneri: `Revenues` varsa o, yoksa sözleşme geliri).
2. **`Issued` ≠ `Outstanding`.** Fark hazine hissesidir (OXY 2023-09-30: 1,106 Mr vs
   0,878 Mr). Hata değil, semantik.
3. **Dosyalayan hataları.** MET 2010-06-30 `dei`=0; CCI 2008-12-31 us-gaap değeri
   1000× ölçek hatalı (2,88e11), `dei` doğru (2,89e8); MPWR FY2012 geliri `AFN`
   (Afgan afganisi) birimiyle etiketlenmiş (tek satır). 76 hisse satırında `val<=0`.
   Öneri: `unit` filtresi + `val>0`.
4. **11 satırda `filed < end`** (kapak tarihi dosyalamadan sonraya yazılmış; ADBE
   `end=2010-06-15`, `filed=2010-01-22`). PIT kuralı `filed`'ı kullandığı için bunlar
   erken bilgi sızdırmaz.
5. **XOM kimlik kayması.** `company_tickers.json` XOM'u CIK **2115436**'ya
   ("ExxonMobil Holdings Corp", halef S-8 POS'ları 2026-07-01) bağlıyor; o kayıtta tek
   bir finansal XBRL ölçüsü yok. Tüm geçmiş öncül CIK **34088**'de. Haritada ikisi de
   var, satırlar 34088'den geliyor. **Ticker→CIK eşlemesi her tazelemede yeniden
   sınanmalı.**
6. **companyfacts'in kendi gecikmesi.** Citigroup 2026-05-07'de 2026-03-31 dönemli,
   inline-XBRL'li 10-Q dosyalamış (submissions API'de görünüyor) ama 2026-08-01
   çekiminde companyfacts'te en son `filed` 2026-02-20. Canlı kullanımda
   "son `filed` çok eski" bekçisi şart; sessizce eski veriyle karar alınmamalı.
7. **Kapsam dışı kalanlar.** STZ'de hiçbir boyutsuz hisse serisi yok (tüm sayımlar
   sınıf boyutlu). SPOT yabancı özel ihraççı: `ifrs-full` taksonomisi, us-gaap
   etiketlerinin hiçbiri yok (Assets dahil). GS ve SYF'de gelir, finansal kurum
   etiketleriyle (`RevenuesNetOfInterestExpense` vb.) verilir — bu turda çekilmedi.

---

## 5b. Emekli semboller

8 emekli sembol (`RETIRED_SYMBOLS`) de çekildi: barları diskte durduğu için 2023–2025
replay'inde bunlar işlem görüyordu ve o dönemin PIT verisi ölçüme gerekli. Serileri
delist tarihlerinde doğal olarak biter (`tutarsizlik.json` → `bayat_seri_emekli`).
FI ve FISV **aynı ihraççıdır** (CIK 798354, NYSE→Nasdaq liste değişimi); satırları
birebir aynıdır. GOOG ve GOOGL de aynı CIK'i (1652044) paylaşır. Sembol sayan bir
analiz bu iki çifti iki kez sayar.

---

## 6. Tazeleme

Boru hattı `betikler/` altında, bu sırayla: `build_cikmap.py` → `download.py` →
`extract.py` → `validate.py` → `finalize.py` → `make_kaynak.py`. Betikler çalışma
dizinini kendi konumlarından türetir; bir çalışma dizinine kopyalanıp koşulurlar
(`raw/` alt dizini gerekir, ~1,03 GB ham JSON oraya iner). Ham companyfacts JSON'ları
**depoya konmadı**; `kaynak.json` her birinin sha256'sını taşır, yani indirilen dosya
bit düzeyinde doğrulanabilir.

Tazelemeden önce okunacak iki tuzak: (a) `download.py` diskte duran dosyayı yeniden
indirmez — gerçekten tazelemek için `raw/` boşaltılmalı; (b) ticker→CIK eşlemesi
kayabilir (XOM vakası), `build_cikmap.py` çıktısındaki eşleşmeyen liste ve
`tutarsizlik.json` → `bayat_seri_evren` her turda okunmalı.

SEC fair-use: kimlik bildiren `User-Agent` zorunlu, 10 istek/sn üst sınır. Bu çekim
sıralı, tek bağlantılı, istekler arası 0,15 sn (~1,5 istek/sn ölçüldü). **Tazelerken
bu gecikmeyi koru.**
