# EDG-2026-007 — residual momentum ölçümü (WP1/1.1)

**Kart:** `research/cards/EDG-2026-007-residual-momentum.yaml` · aile `residual_momentum`
**Ölçüm:** 2026-07-31 · salt-ölçüm sandbox'ı — repo'ya ve `state/`e **hiçbir bayt
yazılmadı** (`config.STATE` sandbox'a çevrildi; bar kapısı uyarıları `_state/events.jsonl`e düştü).
**Kart revizyonu:** guard_revizyonu 2026-07-31 (Rol-1) — kapsam guard'ı GÖRELİ, popülasyon kırpması ZORUNLU-BEYANLI; success/kill eşikleri DEĞİŞMEDİ
**Çıktılar:** `sonuc.json` (her sayı buradan), `olculen_satirlar.csv` (6,783 satır),
`olcum.py` / `duyarlilik.py` / `rapor.py`, `ingest_ff3.py` (ADIM 1).

---

## HÜKÜM ÖNERİSİ: **ARŞİV**

`success_metric` iki koşullu bir VE'dir; **ikisi de karşılanmadı**, iki kill kriterinin **ikisi de**
tetiklendi. Pozitif kontrol ve PK4/PK5 geçti → boru hattı geçerli, hüküm yazılabilir.

| Kartın istediği | Ölçülen |
|---|---|
| yüksek-residmom dilimin **@20g ileri getirisi anlamlı YÜKSEK** | **Hiçbir hücrede değil.** p70@20 fark +0.53 pp, CI [-0.70, +1.46]; p90@20 fark +0.02 pp, CI [-1.75, +1.43] — altı hücrenin altısı da 0 içeriyor |
| **çift sıralamada** ham-mom dilimi İÇİNDE residmom yayılımı **pozitif anlamlı** | **Yok.** Kova-içi havuzlanmış fark p70@20 +0.40 pp, CI [-1.39, +2.22]; p90@20 **negatif**. Hiçbir kovada anlamlı pozitif yayılım yok |

**Kök neden — residmom bu popülasyonda ham momentumun kılığıdır.** FF3 artıklaştırması momentumu
ayrıştırmıyor: `spearman(residmom, rawmom) = 0.62457`, ve p70 eşiğinde yüksek-residmom adayların
**%83.0**'i zaten ham momentumun **en üst terzilinde**; en alt terzilde yalnız
27 aday var (p90'da **1**). Kartın kendi ifadesiyle:
"taşımıyorsa aile ölür (ham momentum zaten skorda temsil ediliyor)".

---

## 1. Kapılar

| Guard | Kart eşiği | Ölçülen | Sonuç |
|---|---|---|---|
| **Kapsam (GÖRELİ, revize)** | FF son tarihi >= popülasyon son tarihi - 65 işlem günü | FF son 2026-05-29 · popülasyon son 2026-07-28 → **40 işlem günü** | ✅ |
| **SPY korelasyonu** | > 0.95 | **0.987566** (n=5,636); 2022+ 0.994159 | ✅ |
| **Pozitif kontrol** | rvol20 @20 IC ≈ 0.0645 | **+0.0637** (sapma 0.0008) | ✅ |
| **PK4** yol tutarlılığı | fwd = günlük getirilerin bileşiği | maks. mutlak fark **0.0** (n=6,783) | ✅ |
| **PK5** artık cebiri | hızlı yol = kaba kuvvet OLS | maks. bağıl fark **0.0** (n=120) | ✅ |

**PK4/PK5 uyarlaması BEYAN EDİLİR:** trend_kolu'nun PK4/PK5'i portföy-yolu içindi; kesitsel retrospektifte karşılığı getiri-yolu ve artık-cebiri özdeşlikleridir (uyarlama BEYAN EDİLİR) PK4 fwd getirinin günlük getiri zinciriyle
özdeşliğini, PK5 hızlı kayan-toplam artık cebirinin kaba kuvvet OLS ile özdeşliğini sınar
(tam pencere artık toplamı da 0.0). İkisi de **makine
hassasiyetinde** geçti.

### Popülasyon kırpması (ZORUNLU-BEYAN)

yalnız t <= FF_son ölçülür (kart guards: popülasyon kırpması ZORUNLU-BEYANLI)

| | |
|---|---|
| Kırpma öncesi eşleşen | **7,067** |
| Kırpılan | **267** (**%3.78**) · 2026-06-01 → 2026-07-28 |
| Ölçüme giren | **6,800** → residmom hesaplanabilen **6,783** |

Rol-1'in beyanı 270/7.122 idi; ölçülen 267/7,067 —
oran aynı (%3,8). Fark bu turun bar evreninin **247** sembol olmasından geliyor
(max_olcum 250 idi): `bars_integrity` dışlaması 3 sembolü pencere eşiğinin altına düşürdü, FISV'nin
önbelleği yok → 55 satır sembol tarafında eleniyor.

---

## 2. Ölçümün tabanı

| | |
|---|---|
| Popülasyon | cf `entered=True` (**kılpayı DAHİL**) + `cf_open` — max_olcum ile birebir aynı tanım |
| Ölçüm tabanı | **6,783** gözlem · 977 gün · 247 sembol · 2022-01-03 → 2026-05-29 |
| `residmom` | t-öncesi 756g OLS (r-rf ~ 1+MKT+SMB+HML) artıkları; S=[t-251, t-21] (231g) artık toplamı / S'nin artık std'si (ddof=1) |
| `rawmom` (kontrol) | AYNI S penceresi, ham getiri: sum(r_S)/std(r_S) — kartın karşılaştırma kontrolü |
| İleri getiri | close[t+h]/close[t]-1, TAM bar serisinden (FF kısıtı ileri getiriyi kesmez; bar önbelleği 2026-07-29'a kadar dolu) |
| Eşik | EVREN KESİTİ gün bazlı p70/p90 (as-of, o günün kesitinin yüzdeliği) · kesit genişliği medyan **247**, min 242 |
| CI | 21-günlük HAREKETLİ BLOK bootstrap (%95 persentil, 2000 tekrar) |
| Barlar | takvim kapısı: **428** hayalet satır düştü, **13** karantina, 0 seri takvim-reddi |
| **bars_integrity** | **46,256 satır**, 57 sembolde güvensiz dönem dışlandı (kırılma: olcek_dikisi 86 · hayalet_gecmis 5 · bozuk_kesit 1) |
| Eleme | bar_yok_sembol 55 · bar_yok_tarih 0 · residmom_NaN 284 · kesit_eşiği_yok 0 → kabul **6,783** |

**FF hizalaması kusursuz:** FF aralığındaki **1,241,511** bar-gününün
**0**'i FF takviminde eksik → 756 günlük regresyon penceresi
hiçbir sembolde takvim boşluğu yüzünden esnemedi.

**`bars_integrity` bu turda neden kritikti:** max_olcum'un penceresi 21 gündü, buradaki **756 gün**.
86 ölçek dikişinden önceki dönem 3 yıllık regresyona girseydi beta'lar ve
artıklar bozulurdu. Defter `state/bars_integrity.json` **diskte yok** → kanonik `measurement_bars()`
fail-open davrandı (0 satır); güvenli başlangıç bu yüzden
`integrity_safe_start` ile **ayrıca hesaplanıp uygulandı**, muhasebesi yukarıda.

---

## 3. POZİTİF KONTROL — boru hattı doğrulandı ✅

| Popülasyon | ufuk | IC | n | blok-bootstrap CI | anlamlı |
|---|---|---|---|---|---|
| kırpılmamış (çiviyle kıyas) | 5 | +0.0374 | 2,093 | [-0.0180, +0.0780] | ✗ |
| kırpılmamış (çiviyle kıyas) | 10 | +0.0515 | 2,091 | [-0.0080, +0.0996] | ✗ |
| kırpılmamış (çiviyle kıyas) | 20 | +0.0637 | 2,085 | [+0.0031, +0.1077] | ✅ |
| kırpılmış (bu turun tabanı) | 5 | +0.0336 | 2,038 | [-0.0268, +0.0831] | ✗ |
| kırpılmış (bu turun tabanı) | 10 | +0.0460 | 2,038 | [-0.0107, +0.1025] | ✗ |
| kırpılmış (bu turun tabanı) | 20 | +0.0558 | 2,038 | [+0.0051, +0.1068] | ✅ |

Kart çivisi **rvol20 @20 IC ≈ 0.0645** → ölçülen **+0.0637**
(sapma 0.0008). Kalan fark ve n düşüşü (2,085 vs max_olcum'un 2.094'ü)
`bars_integrity` dışlamasından geliyor — max_olcum o kapıyı uygulamıyordu. **Boru hattı temiz.**
Defterdeki (`state/component_ic.json`) değer @20 0.0604
(n=2,094).

---

## 4. (a) Dilim kıyası — yüksek-residmom vs kalan

| eşik | ufuk | n_yüksek | n_kalan | ort. yüksek | ort. kalan | fark | CI (21g blok) | anlamlı |
|---|---|---|---|---|---|---|---|---|
| p70 | 5 | 2,320 | 4,463 | +0.22% | +0.13% | **+0.08 pp** | [-0.36, +0.46] | ✗ |
| p70 | 10 | 2,320 | 4,463 | +0.61% | +0.46% | **+0.16 pp** | [-0.59, +0.79] | ✗ |
| p70 | 20 | 2,320 | 4,463 | +1.50% | +0.96% | **+0.53 pp** | [-0.70, +1.46] | ✗ |
| p90 | 5 | 739 | 6,044 | +0.01% | +0.18% | **-0.17 pp** | [-0.86, +0.47] | ✗ |
| p90 | 10 | 739 | 6,044 | +0.34% | +0.53% | **-0.19 pp** | [-1.19, +0.77] | ✗ |
| p90 | 20 | 739 | 6,044 | +1.16% | +1.14% | **+0.02 pp** | [-1.75, +1.43] | ✗ |

**Altı hücrenin altısı da CI-0-içi** → kill #1 ("dilim farkı CI-0-içi → bilgisiz, arşiv") tetiklendi.
p90'da işaret kısa ufuklarda negatif bile.

### Sürekli IC

| büyüklük | ufuk | IC | n | CI | anlamlı |
|---|---|---|---|---|---|
| residmom | 5 | +0.0278 | 6,783 | [-0.0151, +0.0681] | ✗ |
| residmom | 10 | +0.0182 | 6,783 | [-0.0330, +0.0591] | ✗ |
| residmom | 20 | +0.0231 | 6,783 | [-0.0332, +0.0611] | ✗ |
| ham 12-1 momentum | 5 | +0.0190 | 6,783 | [-0.0298, +0.0641] | ✗ |
| ham 12-1 momentum | 10 | -0.0017 | 6,783 | [-0.0606, +0.0646] | ✗ |
| ham 12-1 momentum | 20 | +0.0259 | 6,783 | [-0.0498, +0.1023] | ✗ |

residmom'un hiçbir ufukta anlamlı IC'si yok; ham momentumun da yok — ikisi de bu popülasyonda ölü.

### residmom beşlikleri (fwd20)

| beşlik | aralık | n | ort. fwd20 | medyan fwd20 |
|---|---|---|---|---|
| 1 | -36.12 … -9.35 | 1,357 | +0.32% | +0.38% |
| 2 | -9.35 … -3.02 | 1,356 | +0.93% | +0.88% |
| 3 | -3.02 … +2.74 | 1,357 | +1.29% | +1.01% |
| 4 | +2.74 … +9.54 | 1,356 | +1.59% | +1.16% |
| 5 | +9.54 … +39.67 | 1,357 | +1.59% | +0.45% |

Ortalamada zayıf artan bir eğim var ama **en üst beşliğin medyanı 3. ve 4. beşliğin altına düşüyor**
— etki ortalamada, tipik sonuçta değil; ve hiçbir dilim farkı anlamlı değil.

---

## 5. (c) ÇİFT SIRALAMA — artımlı katkı testi (kartın ikinci bacağı)

Ham 12-1 momentumun **gün bazlı evren kesiti terzilleri** İÇİNDE residmom yüksek-dilim yayılımı.

| eşik | ufuk | kova-içi havuzlanmış fark | CI (21g blok) | anlamlı |
|---|---|---|---|---|
| p70 | 5 | -0.10 pp | [-0.73, +0.49] | ✗ |
| p70 | 10 | +0.02 pp | [-0.97, +0.82] | ✗ |
| p70 | 20 | +0.40 pp | [-1.39, +2.22] | ✗ |
| p90 | 5 | +0.02 pp | [-0.67, +0.72] | ✗ |
| p90 | 10 | -0.73 pp | [-1.99, +0.32] | ✗ |
| p90 | 20 | -0.78 pp | [-2.51, +0.87] | ✗ |

**Hiçbir hücre anlamlı değil; p90'da işaret negatif** → kill #2 ("artımlı katkı yok → skor bileşeni
olarak ölü, arşiv") tetiklendi.

### Neden — dilimler zaten aynı adayları seçiyor (@20, kova dağılımı)

| eşik | ham-mom kovası | n_yüksek | n_kalan | fark | CI | anlamlı |
|---|---|---|---|---|---|---|
| p70 | 1 | 27 | 1316 | — | — | — dilim < 30 |
| p70 | 2 | 368 | 1968 | +0.02 pp | [-1.73, +1.57] | ✗  |
| p70 | 3 | 1925 | 1179 | +0.08 pp | [-1.59, +1.51] | ✗  |
| p90 | 1 | 1 | 1342 | — | — | — dilim < 30 |
| p90 | 2 | 35 | 2301 | -1.35 pp | [-4.08, +1.58] | ✗  |
| p90 | 3 | 703 | 2401 | -0.34 pp | [-2.16, +1.20] | ✗  |

**Bu tablo hükmün kalbidir.** p70'te yüksek-residmom adayların 1,925'i
(**%83.0**) ham momentumun en üst terzilinde; en alt terzilde yalnız 27
aday kaldığı için o hücre `n < 30` kuralıyla **ölçülemedi (None)** — uydurulmadı. p90'da en alt
terzilde **1** aday var.

Yani "yüksek residual momentum" bu popülasyonda pratikte "yüksek ham momentum"un yeniden
etiketlenmesidir.

### Kova içi sürekli IC (fwd20)

| ham-mom kovası | IC | n | CI | anlamlı |
|---|---|---|---|---|
| 1 | +0.0147 | 1,343 | [-0.0673, +0.0881] | ✗ |
| 2 | -0.0110 | 2,336 | [-0.0952, +0.0500] | ✗ |
| 3 | -0.0326 | 3,104 | [-0.1092, +0.0341] | ✗ |

Üçünde de sıfır civarı, üst kovada negatif. Artık bilgi yok.

---

## 6. Duyarlılık — hüküm CI yöntemine yaslanıyor mu?

Kart "blok-bootstrap" diyor, brief 21 günlük blok belirledi; **hüküm o yöntemle verildi.** Yöntemin
etkisi yine de ölçüldü (hipotez testi değil, yöntem duyarlılığı — K harcamaz):

| eşik | ufuk | fark | 21g blok (KART) | gün-kümeli (blok=1) | iid satır |
|---|---|---|---|---|---|
| p70 | 5 | +0.08 pp | [-0.36, +0.46] ✗ | [-0.21, +0.36] ✗ | [-0.17, +0.32] ✗ |
| p70 | 10 | +0.16 pp | [-0.54, +0.78] ✗ | [-0.23, +0.53] ✗ | [-0.17, +0.47] ✗ |
| p70 | 20 | +0.53 pp | [-0.70, +1.53] ✗ | [-0.02, +1.08] ✗ | [+0.07, +1.05] ✅ |
| p90 | 5 | -0.17 pp | [-0.87, +0.41] ✗ | [-0.63, +0.25] ✗ | [-0.59, +0.24] ✗ |
| p90 | 10 | -0.19 pp | [-1.22, +0.83] ✗ | [-0.79, +0.39] ✗ | [-0.72, +0.35] ✗ |
| p90 | 20 | +0.02 pp | [-1.73, +1.45] ✗ | [-0.89, +0.87] ✗ | [-0.80, +0.84] ✗ |

**Tek oynak hücre p70@20.** Kart yöntemiyle anlamsız; max_olcum'un gün-kümeli yöntemiyle **yine
anlamsız** (alt sınır sıfırın hemen altında); yalnız **iid satır** bootstrap'ında anlamlı görünüyor.
iid, hem aynı günün satırlarının bağımlılığını hem de fwd20'nin ardışık günlerde 19 gün paylaşan
**örtüşmesini** yok sayar — savunulabilir bir yöntem değildir. **Hüküm makul yöntem seçimlerine
dayanıklı.** İkinci bacak (artımlı katkı) ise **her yöntemde** ölü: kova dağılımı yapısal bir
gerçektir, CI seçiminden bağımsızdır.

---

## 7. Caveatlar

- **Survivorship (en ağır).** `REPLAY_UNIVERSE` BUGÜNÜN üyeliğidir, 2022'ye geriye uygulanıyor. Hem
  eşik kesiti hem popülasyon aynı hayatta-kalanlardan geliyor; momentum çöküşünün en sert vurduğu
  isimler burada yok. Bu, "residmom bu evrende ve bu popülasyonda artımlı bilgi taşımıyor" hükmünü
  destekler; **"residual momentum yoktur" hükmüne izin vermez.**
- **Popülasyon koşullu.** Satırlar zaten "kırılma adayı olmak" üzerine koşullanmış, alınmamış
  hipotetik girişlerdir. BHM'nin etkisi tüm evren kesitinde, aylık dengelemeli long-short portföyde
  ölçülür — burada ölçülen o değil; kartın sorduğu şey (skor bileşeni adaylığı) budur.
- **Kırpma.** 267 satır (%3.78) FF kapsamı dışında
  (2026-06-01 → 2026-07-28); en taze iki ay ölçümde yok.
- **Literatür.** Blitz-Huij-Martens (2011) birinci-el PDF bu turda çekilmedi (kart caveat'i). Hüküm
  literatür-bağımsızdır, kendi verimizde ölçüldü.
- **Çoklu test.** Kart K=2 (persentil 70/90). Raporlanan ek hücreler (5/10g, IC tabloları, kova
  kırılımları) **hüküm bacağı değildir**; hüküm yalnız @20g dilim farkı ve çift-sıralama havuzlanmış
  farkı üzerinden verildi. Düzeltme uygulanmadı — hiçbir hücre anlamlı çıkmadığı için gerek kalmadı.
- **`component_ic.json` bayat.** Defterdeki cf rvol20 @20 (0.0604),
  takvim kapısı + bars_integrity uygulanınca +0.0637'e kayıyor. AUDIT-2026-07-31
  BT-2'nin "türetilmiş artefaktlar yeniden üretilecek" maddesi açık.

---

## 8. Öneri

1. **EDG-2026-007 → `status: archived`.** kill #1 ve #2 tetiklendi; success'in iki bacağı da
   karşılanmadı; pozitif kontrol + PK4/PK5 geçtiği için hüküm yazılabilir. K harcandı (2 deneme).
2. **Aileyi kapat, torun kart AÇMA.** Bulgu "ölçüm zayıftı" değil **yapısal**: FF3 artıklaştırması
   bu popülasyonda momentumu ayrıştırmıyor (spearman 0.62457, üst-terzil yoğunlaşması %83.0).
   Farklı bir residüalizasyonla (FF5, sektör-nötr) aynı veriye dönmek yeni bilgi getirmez; getirse
   bile örneklem bağımsız olmaz.
3. **`research/ff_factors/` kalıcı artefakt.** FF3 günlük dosyası doğrulanmış biçimde repo'da; başka
   kartlar yeniden indirmeden kullanabilir (tazeleme: aynı URL + `ingest_ff3.py`).
4. **`bars_integrity.json` defteri üretilmeli.** Bu turda 46,256 satırlık
   güvensiz dönem (57 sembol) ölçüm ajanı tarafından
   **hesaplanarak** dışlandı, çünkü defter yok ve kanonik `measurement_bars()` fail-open. Uzun
   pencereli her ölçüm bu hesabı yeniden yapmak zorunda; defter üretilirse kanonik yol tek
   kaynaktan çalışır.
