# EDG-2026-011 — in-play aday önceliklendirme · ÖLÇÜM RAPORU

- Kart: `research/cards/EDG-2026-011-inplay-onceliklendirme.yaml` · aile `inplay_candidate_priority`
- Durum: **OLCULMEDI_KILL3** · ölçüm zamanı `2026-08-01T10:09:48.374196+00:00`
- Sandbox: `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/inplay_olcum` — repo/state'e **hiçbir yazım yok**

> Bu rapordaki her sayı `sonuc.json`dan okunur. Ölçüm ajanı **karta dokunmadı**; aşağıdaki
> hüküm bir **öneridir**, hükmü Rol-1 işler.

**TEK CÜMLE:** ASKI (kill#3) — in-play aday-gün sayısı iki pencerede de 150 eşiğinin ALTINDA; üstelik bu sayı PIT-İHLALLİ ÜST SINIRdır. Kart ÖLÇÜLEMEDİ: K HARCANMAZ, tanım GEVŞETİLMEZ. Kök neden veri: kazanç takvimi nokta-zamanlı DEĞİL (tek ileriye-dönük anlık görüntü).

## 1 · Kart metninin uygulaması (ne ölçülecekti)

- **Popülasyon:** cf-katmanlı aday popülasyonu — counterfactuals.jsonl entered=True (near_miss DAHİL = 'girilen+kılpayı') + cf_open.json; TEKİL (ticker, date)
- **in_play tanımı:** |t - en yakın kazanç tarihi| <= P TAKVİM günü (P ∈ [3, 5]) VE rvol20(t) >= 1.5
- **Katmanlar:** yalniz_katalizor (yalnız kazanç yakınlığı) / yalniz_rvol (yalnız rvol20>=1.5) / in_play (ikisi) — artımlılık bu üçlüden okunur
- **Taban:** AYNI-GÜN ADAY HAVUZU: o takvim gününde ileri getirisi tanımlı TÜM aday-günlerin ortalaması (piyasa sürüklenmesi ayıklanır). Birincil okuma havuz ortalamasına SATIRIN KENDİSİ DAHİLdir (kartın harfi); birini-dışarıda-bırak (LOO) okuması duyarlılık olarak AYRICA verilir, hükme girmez.
- **İleri getiri:** close[t+h]/close[t]-1, TAM (takvim-kapılı + integrity-dışlamalı) bar serisinden; h ∈ 5/10/20
- **Artımlılık:** ort(in_play fazlası) - ort(yalniz_rvol fazlası); CI ORTAK gün bloklarından (aynı blokla iki ortalama birden hesaplanır)
- **CI:** 21-günlük HAREKETLİ BLOK bootstrap (%95 persentil, 2000 tekrar)
- **Maliyet:** 10.0bps tek-yön; kart cost_model 'sıralama overlay'i işlem üretmez' diyor → hüküm BRÜT üzerinden, net değer AYRICA verilir
- **rvol20:** meridian.indicators.rvol20 (depo fonksiyonu; 20g hacim ortalamasına oran)

## 2 · Veri zemini

| kalem | değer |
|---|---|
| bar sembolü yüklendi | 248 / 251 |
| hayalet seans düşen satır | 428 |
| düzeltilmemiş karantina | 13 |
| bars_integrity **defter yolu** düşen satır | 46256 (57 sembol) |
| bars_integrity **hesaplanan yol** ek dışlanan satır | 0 |
| iki yolun ayrıştığı sembol | 0 |
| cf defteri satırı | 7161 (girilmemiş 108) |
| cf_open satırı | 69 |
| **ham aday satırı (girilen+kılpayı)** | 7122 |
| tekilleştirmede düşen kopya satır | 315 |
| **tekil aday-gün** | 6807 |
| bar eşleşen aday-gün | 6764 (bar yok: sembol 43, tarih 0) |
| rvol20 ölçülemeyen aday-gün | 0 |
| aday havuzu gün sayısı | 998 |
| gün başına aday (ort / medyan / min / maks) | 6.673347 / 5.0 / 1 / 54 |
| tek adaylı gün | 137 |

> tek-adaylı günlerde birincil (kendisi-dahil) fazla TANIM GEREĞİ 0'dır; LOO okuması o günleri ölçemez (n<2) ve dışlar — iki okuma bu yüzden AYRI verilir

## 3 · Kazanç takvimi ve nokta-zamanlılık (ölçümün kırıldığı yer)

| kalem | değer |
|---|---|
| kaynak | `/Users/erdemozturk/AI-Trading/state/earnings.csv` |
| yükleyici | meridian.earnings._load() (DEPONUN kendi yükleyicisi; dosya sandbox'a kopyalandı, canlı dosyaya DOKUNULMADI) |
| dosya mtime (UTC) | `2026-07-29T22:10:30.875123+00:00` |
| takvimde bilinen sembol | 193 |
| toplam kazanç tarihi | 193 |
| sembol başına tarih (min / maks) | 1 / 1 |
| takvim tarih aralığı | 2025-06-24 … 2026-08-13 |
| evren kapsamı | 193 / 251 (kart beyanı: 194/251 (kart evidence_refs)) |
| **aday sembolleri** kapsamı | 190 / 248 — kapsam dışı 58 sembol |
| kapsam dışı aday-gün (dilime GİRMEZ, None) | 1669 / 6764 |

**Takvim tarihlerinin ay dağılımı** (tüm takvim):

| ay | tarih sayısı |
|---|---|
| 2025-06 | 1 |
| 2026-07 | 123 |
| 2026-08 | 69 |

### 3.1 PIT denetimi

- **Kartın şartı:** in_play(t) tanımı kartta 'yalnız t'de BİLİNEN takvim' diye yazılmıştır — yani t gününde elde olan kazanç takvimi.
- **Bulgu:** state/earnings.csv TEK BİR İLERİYE-DÖNÜK ANLIK GÖRÜNTÜdür: her sembol için yalnız BİR tarih (sonraki planlı rapor) tutulur ve dosya haftalık olarak ÜZERİNE yazılır. Depoda kazanç tarihlerinin TARİHSEL (nokta-zamanlı) kaydı YOK: state/history altında takvim anlık görüntüsü yok, counterfactuals.jsonl satırlarında kazanç alanı yok, başka hiçbir state dosyasında rapor tarihi yok.
- **Kod dayanağı:** meridian/earnings.py — refresh(): Nasdaq penceresi [bugün-7g, bugün+14g]; refresh_from_fmp(): fmp.earnings_dates; her ikisi de earnings.csv'yi os.replace ile YENİDEN YAZAR. Geçmişe dönük arşiv tutulmaz.
- **Aday-gün aralığı:** 2022-01-03 … 2026-07-28
- **Takvim tarih aralığı:** 2025-06-24 … 2026-08-13
- **Sonuç:** PIT-DOĞRU in_play, aday popülasyonunun EZİCİ çoğunluğu için ÖLÇÜLEMEZ: takvimde hiç tarih bulunmayan bir dönemde (2022-01..2026-06) t'de bilinen takvim depoda yok. Kartın tanımını korumak için ölçüm İKİ okumayla verilir: (a) PIT-DOĞRU okuma — ölçülemez, None+neden; (b) PIT-İHLALLİ ÜST SINIR — bugünkü anlık görüntü TÜM geçmişe uygulanır (geleceğe bakar, HÜKME GİRMEZ) ve yalnız 'tanım gevşetilse bile örneklem yeter mi?' sorusunu kapatmak için sayılır.

## 4 · (i) Dilim sayıları

> katalizör ve in_play sayıları PIT-İHLALLİ ÜST SINIRdır (bugünkü takvim anlık görüntüsü tüm geçmişe uygulanmıştır). PIT-DOĞRU sayı bunlardan KÜÇÜK ya da eşittir; üst sınır bile kill#3 eşiğini (150) geçmiyorsa PIT-doğru okuma da geçemez.

| P | katman | aday-gün | tarih aralığı | ufku tanımlı @5 | @10 | @20 |
|---|---|---|---|---|---|---|
| 3 | yalnız-katalizör | 23 | 2026-07-21 … 2026-07-28 | 1 | 0 | 0 |
| 3 | yalnız-rvol | 2401 | 2022-01-04 … 2026-07-28 | 2387 | 2383 | 2379 |
| 3 | in-play (ikisi) | 11 | 2026-07-21 … 2026-07-28 | 1 | 0 | 0 |
| 5 | yalnız-katalizör | 24 | 2026-07-21 … 2026-07-28 | 1 | 0 | 0 |
| 5 | yalnız-rvol | 2401 | 2022-01-04 … 2026-07-28 | 2387 | 2383 | 2379 |
| 5 | in-play (ikisi) | 12 | 2026-07-21 … 2026-07-28 | 1 | 0 | 0 |

> in-play dilimi TAMAMEN verinin SON HAFTASINDA oturuyor (takvim anlık görüntüsü ileriye dönük olduğu için katalizör yakınlığı yalnız bugünün çevresinde kurulabiliyor). Bu yüzden 10g ve 20g ileri getirisi HENÜZ OLUŞMAMIŞTIR: dilim yalnız küçük DEĞİL, kart success_metric'inin okuduğu iki ufukta TAMAMEN BOŞTUR.

### 4.1 kill#3 kapısı

| P | in-play aday-gün (ÜST SINIR) | eşik | yeterli mi | PIT-doğru sayı |
|---|---|---|---|---|
| 3 | 11 | 150 | hayır | — (t'de bilinen takvim depoda yok (tek ileriye-dönük anlık görüntü) — PIT-doğru dilim sayılamaz) |
| 5 | 12 | 150 | hayır | — (t'de bilinen takvim depoda yok (tek ileriye-dönük anlık görüntü) — PIT-doğru dilim sayılamaz) |

## 5 · (i) Fazla tablosu + CI (üç katman)

Fazla = aday getirisi − **aynı-gün aday-havuzu** ortalaması. CI = 21g hareketli blok bootstrap %95.

### P = 3

| katman | h | n | ham ort | ham CI | **havuz fazlası** | **fazla CI** | poz. anlamlı | LOO fazla | LOO CI |
|---|---|---|---|---|---|---|---|---|---|
| yalnız-katalizör | 5 | 1 | — | — | **—** | **—** | — | — | — |
| yalnız-katalizör | 10 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |
| yalnız-katalizör | 20 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |
| yalnız-rvol | 5 | 2387 | +0.170% | [-0.219%, +0.621%] | **+0.025%** | **[-0.102%, +0.191%]** | hayır | +0.036% | [-0.107%, +0.241%] |
| yalnız-rvol | 10 | 2383 | +0.546% | [-0.021%, +1.367%] | **+0.010%** | **[-0.178%, +0.275%]** | hayır | +0.020% | [-0.191%, +0.340%] |
| yalnız-rvol | 20 | 2379 | +1.281% | [+0.389%, +2.529%] | **+0.059%** | **[-0.175%, +0.385%]** | hayır | +0.086% | [-0.150%, +0.464%] |
| in-play (ikisi) | 5 | 1 | — | — | **—** | **—** | — | — | — |
| in-play (ikisi) | 10 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |
| in-play (ikisi) | 20 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |

### P = 5

| katman | h | n | ham ort | ham CI | **havuz fazlası** | **fazla CI** | poz. anlamlı | LOO fazla | LOO CI |
|---|---|---|---|---|---|---|---|---|---|
| yalnız-katalizör | 5 | 1 | — | — | **—** | **—** | — | — | — |
| yalnız-katalizör | 10 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |
| yalnız-katalizör | 20 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |
| yalnız-rvol | 5 | 2387 | +0.170% | [-0.207%, +0.623%] | **+0.025%** | **[-0.110%, +0.191%]** | hayır | +0.036% | [-0.112%, +0.251%] |
| yalnız-rvol | 10 | 2383 | +0.546% | [-0.032%, +1.324%] | **+0.010%** | **[-0.177%, +0.272%]** | hayır | +0.020% | [-0.180%, +0.345%] |
| yalnız-rvol | 20 | 2379 | +1.281% | [+0.373%, +2.603%] | **+0.059%** | **[-0.159%, +0.389%]** | hayır | +0.086% | [-0.175%, +0.460%] |
| in-play (ikisi) | 5 | 1 | — | — | **—** | **—** | — | — | — |
| in-play (ikisi) | 10 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |
| in-play (ikisi) | 20 | 0 _(gözlem yok)_ | — | — | — | — | — | — | — |

Boş hücreler ölçülemeyen dilimlerdir (`sonuc.json` içinde `neden` ile birlikte durur: `n<30` ya da `gözlem yok`). **Uydurma yasağı gereği hiçbir boş hücre doldurulmadı.**

## 6 · (ii) Artımlılık

> kart success_metric 2. bacağı: in-play fazlası, yalnız-rvol katmanının fazlasını ANLAMLI aşıyor mu (katalizörün rvol-ötesi katkısı)?

| P | h | n(in-play) | n(yalnız-rvol) | fark | CI | anlamlı | neden |
|---|---|---|---|---|---|---|---|
| 3 | 5 | 1 | 2387 | — | — | — | in_play dilimi n=1 < 30 — ölçülemez (kill#3 zaten askıda) |
| 3 | 10 | 0 | 2383 | — | — | — | in_play dilimi n=0 < 30 — ölçülemez (kill#3 zaten askıda) |
| 3 | 20 | 0 | 2379 | — | — | — | in_play dilimi n=0 < 30 — ölçülemez (kill#3 zaten askıda) |
| 5 | 5 | 1 | 2387 | — | — | — | in_play dilimi n=1 < 30 — ölçülemez (kill#3 zaten askıda) |
| 5 | 10 | 0 | 2383 | — | — | — | in_play dilimi n=0 < 30 — ölçülemez (kill#3 zaten askıda) |
| 5 | 20 | 0 | 2379 | — | — | — | in_play dilimi n=0 < 30 — ölçülemez (kill#3 zaten askıda) |

## 7 · (iii) Pozitif kontrol + PK4/PK5

AYNI boru hattı, kart guards çivisi: ham rvol20 @20 cf-katman IC ≈0.064 (max_olcum/EDG-2026-004 turu 0.0645; resmom 0.0637; pullback 0.0642 — hepsi bars_integrity dışlamalı yolda).

- Katman: counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı), ŞABLONLA AYNI SATIR DÜZEYİ (tekilleştirme YOK) · n = 2099

| h | IC | n | CI | anlamlı |
|---|---|---|---|---|
| 5 | 0.0374 | 2095 | [-0.0180, +0.0889] | hayır |
| 10 | 0.0516 | 2093 | [-0.0079, +0.0981] | hayır |
| 20 | 0.0642 | 2087 | [+0.0130, +0.1118] | EVET |

**Çivi:** ölçülen `0.0642` · hedef `0.0645` · sapma `0.0003` · tolerans `0.005` → **GEÇTİ: EVET**

Tanı (hükme girmez) — aynı çivi bu turun TEKİL panelinde: IC `0.0533` (n=1932), CI [-0.0015, +0.0940]. TEKİLLEŞTİRME etkisi: aynı gün birden çok setup satırı tek aday-güne indiği için katman üyeliği ve ağırlıklar değişir. HÜKME GİRMEZ.

Defterdeki referans (`state/component_ic.json`, cf/rvol20):

| h | IC | n | CI |
|---|---|---|---|
| 5 | 0.0320 | 2102 | [-0.0108, +0.0747] |
| 10 | 0.0456 | 2100 | [+0.0029, +0.0882] |
| 20 | 0.0604 | 2094 | [+0.0176, +0.1030] |

### 7.1 PK4 — yol tutarlılığı

> YOL TUTARLILIĞI: close[t+h]/close[t]-1, aradaki GÜNLÜK getirilerin bileşiğine eşit olmalı. Takvim kapısı/integrity kırpması ufkun İÇİNDE bar düşürdüyse ya da kaydırma bir gün kaysaydı bu özdeşlik bozulurdu. · kapsam: tekil aday-gün paneli + pozitif kontrolün satır düzeyi paneli

| ufuk | n | maks mutlak fark | geçti |
|---|---|---|---|
| 5 | 13743 | 0.0 | EVET |
| 10 | 13699 | 0.0 | EVET |
| 20 | 13624 | 0.0 | EVET |

### 7.2 PK5 — özdeşlikler

> DÖRT ÖZDEŞLİK: (A) rvol20 GERİYE-BAKIŞSIZ — tam seride ile df.iloc[:i+1] kesilmiş seride aynı değer; (B) katman maskeleri bağımsız (vektörsüz, saf python) türetimle birebir aynı; (C) hızlı ortalama-bootstrap ile satır-toplayan bootstrap aynı gün dizisinde birebir aynı; (D) kazanç takvimi KANONİK yükleyici (meridian.earnings._load) ile bağımsız ayrıştırma birebir aynı.

| sınama | ölçü | geçti |
|---|---|---|
| A · rvol20 geriye-bakışsız | n=32, maks fark 0.0 | EVET |
| B · katman maskesi bağımsız türetim | 6 sınama, ayrışan 0 | EVET |
| C · hızlı ortalama-bootstrap özdeşliği | n=50, maks fark 0.0 | EVET |
| D · takvim yükleyici özdeşliği | kanonik 193 / bağımsız 193 sembol, ayrışma 0+0 | EVET |
| **PK5 toplam** | — | **EVET** |

## 8 · Hüküm ÖNERİSİ (kart ölçütüne göre)

- **Kart success_metric:** in-play diliminin aday-havuzu-fazlası @10 VEYA @20 anlamlı POZİTİF (CI 0-dışı) VE artımlılık: fazla, yalnız-rvol katmanının fazlasını anlamlı aşıyor
- **Kart kill listesi:**
  - iki pencerede de fazla CI-0-içi → arşiv
  - artımlılık yok → 'rvol zaten skorda' hükmü, arşiv
  - in-play aday-gün < 150 → ölçülemedi-nedenli askı (K harcanmaz, tanım gevşetilmez)

| P | ölçüldü mü | bacak1 (fazla @10/@20) | bacak2 (artımlılık) | neden |
|---|---|---|---|---|
| 3 | hayır | — | — | kill#3: in-play aday-gün üst sınırı 11 < 150 |
| 5 | hayır | — | — | kill#3: in-play aday-gün üst sınırı 12 < 150 |

**Kapı durumları:** pozitif kontrol EVET · PK4 EVET · PK5 EVET

### 8.1 Yan bulgu — yalnız-rvol katmanı (PIT-TEMİZ, hükmü tek başına kapatmaz)

Bu katman kazanç takvimine hiç bakmaz, bu yüzden PIT sorunundan **etkilenmez** ve tüm defter
penceresinde ölçülebilir. Kartın hükmü in-play dilimini şart koştuğu için bu tablo kartı
kapatmaz; ama kartın 2. kill'inin ('rvol zaten skorda') zeminini doğrudan gösterir.

| h | ham ort | havuz fazlası | fazla CI | poz. anlamlı | LOO fazla | LOO CI |
|---|---|---|---|---|---|---|
| 5 | +0.170% | **+0.025%** | [-0.102%, +0.191%] | hayır | +0.036% | [-0.107%, +0.241%] |
| 10 | +0.546% | **+0.010%** | [-0.178%, +0.275%] | hayır | +0.020% | [-0.191%, +0.340%] |
| 20 | +1.281% | **+0.059%** | [-0.175%, +0.385%] | hayır | +0.086% | [-0.150%, +0.464%] |

### 8.2 ÖNERİ

**ASKI (kill#3) — in-play aday-gün sayısı iki pencerede de 150 eşiğinin ALTINDA; üstelik bu sayı PIT-İHLALLİ ÜST SINIRdır. Kart ÖLÇÜLEMEDİ: K HARCANMAZ, tanım GEVŞETİLMEZ. Kök neden veri: kazanç takvimi nokta-zamanlı DEĞİL (tek ileriye-dönük anlık görüntü).**

