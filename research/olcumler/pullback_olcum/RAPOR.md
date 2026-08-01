# EDG-2026-010 — trend-pullback kurulumu · ÖLÇÜM RAPORU

- Kart: `research/cards/EDG-2026-010-pullback-setup.yaml` · aile `trend_pullback_setup`
- Durum: **OLCULDU** · ölçüm zamanı `2026-08-01T09:00:25.194474+00:00`
- Sandbox: `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/pullback_olcum` — repo/state'e **hiçbir yazım yok**

> Bu rapordaki her sayı `sonuc.json`dan okunur. Ölçüm ajanı **karta dokunmadı**; aşağıdaki
> hüküm bir **öneridir**, hükmü Rol-1 işler.

## 1 · Kart metninin uygulaması (ne ölçüldü)

**Ön-şart — trend şablonu:** `meridian.indicators.trend_template (Minervini 6 koşul, [0,1] kesir)`, sert kapı **tt ≥ 0.6**.
Kapının kaynağı (icat DEĞİL): depo — strategy.py:424 (evaluate_pullback), :485 (evaluate_momentum_burst), :840 (evaluate_canslim) hepsi `tt >= 0.6`; indicators.trend_template belgesi bunu 'SERT kapı' diye adlandırıyor. Tanım İCAT EDİLMEDİ.
NaN davranışı: ısınma (252 bar) dolmamış bar GEÇMEZ — depo davranışı (pd.isna(tt) → None)

**Geri-çekilme tanımları (kart grid'i, K=2):**

- `sma20_dokunus` — |kapanış/SMA20 - 1| <= 0.02 VE son 5 barın (t dâhil) en yüksek HIGH'ından kapanışa geri-çekilme >= 0.04
- `dip10` — (kapanış - son 10 barın (t dâhil) en düşük LOW'u) / o dip <= 0.01

**Devam tetiği:** kurulum gününden SONRAKİ ilk bar ile kapanış > önceki günün yükseği; bekleme penceresi kartta YOK → üst sınır uygulanmadı, bekleme dağılımı raporlanır

**İleri getiri:** close[t+h]/close[t]-1, TAM (takvim-kapılı + integrity-dışlamalı) bar serisinden

**Maliyet:** 10.0bps tek-yön; brüt ortalamadan düşülmüş değer AYRICA verilir (hüküm brüt üzerinden — kart success_metric maliyet yazmıyor)

**CI:** 21-günlük HAREKETLİ BLOK bootstrap (%95 persentil, 2000 tekrar)

### 1.1 Beyan edilen operasyonel seçimler (kart metni ayrık olduğu yerler)

- Kart 'son 5g >=%4 geri-çekilme' ve '10 günün en düşüğü' derken bar alanını yazmıyor. BİRİNCİL okuma: geri-çekilme tepesi HIGH, 10g dibi LOW (bar serisinde 'en yüksek/en düşük'ün karşılığı). KAPANIŞ tabanlı okuma duyarlılık olarak AYRICA sayılır ama HÜKME GİRMEZ (K harcanmaz).
- Kart horizon alanı 'cf-katmanlı retrospektif (MAX/resmom şablonu)' diyor; universe alanı full_251. Sinyaller cf defterinde YOK (bu tanımlar depoda hiç koşmadı), o yüzden 'cf-katmanlı' BORU HATTI şablonu olarak okundu: popülasyon full_251 bar paneli. cf defterinin tarih penceresine kısıtlı ölçüm AYRICA verilir (alternatif okuma).

## 2 · Veri zemini

| kalem | değer |
|---|---|
| istenen sembol (full_251) | 251 |
| yüklenen sembol | 248 |
| kısa (ısınma+ufuk dolmuyor) | 2 |
| dosya yok / okunamadı | 1 / 0 |
| hayalet seans düşen satır | 428 |
| karantina (düzeltilmemiş fiyat) satır | 13 |
| takvim uyuşmazlığı olan sembol | 0 |
| **bars_integrity — KANONİK defter yolu** | 46256 satır (57 sembol) |
| bars_integrity — HESAPLANAN yolun EK dışladığı | 0 satır |
| iki yolun ayrıştığı sembol | 0 |
| taranan bar | 1,252,244 |
| trend şablonu TANIMLI bar | 1,189,996 |
| trend şablonunu GEÇEN bar (tt ≥ 0.6) | 731,597 |
| devam tetiği (kapanış > önceki yüksek) günü | 342,365 |
| kurulum günü — `sma20_dokunus` | 34,407 |
| kurulum günü — `dip10` | 87,047 |

resmom_olcum'da bars_integrity defteri sandbox'ta yoktu ve kanonik yol fail-open'dı; bu turda
defter sandbox'a salt-okuma kopyalandı, yani **kanonik yol gerçekten uygulandı** ve hesaplanan
yol üstüne bir şey eklemedi (yukarıdaki iki satır).

## 3 · Kart kill#3 kapısı — sinyal sayısı

| tanım | sinyal (sembol-gün) | eşik | yeterli |
|---|---:|---:|---|
| `sma20_dokunus` | 19,915 | 200 | EVET |
| `dip10` | 35,475 | 200 | EVET |

## 4 · (i) Sinyal dilimi — ileri getiri + 21g blok-bootstrap CI

`ham` = sinyal gününün ham ileri getirisi (**kart success_metric'inin okuduğu istatistik**).
`evren fazlası` / `trend evreni fazlası` = aynı takvim gününde evrenin (ve trend şablonunu geçen
alt evrenin) ortalamasına göre **fazla** — TANI amaçlı, ek hipotez testi değil.

### `sma20_dokunus`

- sinyal 19,915 · sembol 248 · gün 3,969 · aralık 2005-01-06 … 2026-07-28
- kurulum→sinyal bekleme (gün): medyan 2 · ort 3.37 · p90 7 · maks 40
- sinyal gününde trend şablonu HÂLÂ geçiyor: 95.3%

| ufuk | ölçüm | n | ort | medyan | %95 CI (21g blok) | CI 0-dışı | poz.&anlamlı | maliyet sonrası ort |
|---|---|---:|---:|---:|---|---|---|---:|
| 5g | ham | 19,871 | +0.17% | +0.24% | [-0.05%, +0.38%] | hayır | hayır | +0.07% |
| 5g | evren fazlası | 19,871 | -0.07% | -0.12% | [-0.17%, +0.04%] | hayır | hayır | -0.17% |
| 5g | trend evreni fazlası | 19,871 | -0.06% | -0.13% | [-0.14%, +0.03%] | hayır | hayır | -0.16% |
| 10g | ham | 19,838 | +0.49% | +0.51% | [+0.10%, +0.90%] | EVET | EVET | +0.39% |
| 10g | evren fazlası | 19,838 | +0.04% | -0.14% | [-0.10%, +0.19%] | hayır | hayır | -0.06% |
| 10g | trend evreni fazlası | 19,838 | +0.04% | -0.19% | [-0.07%, +0.16%] | hayır | hayır | -0.06% |
| 20g | ham | 19,770 | +1.13% | +1.03% | [+0.51%, +1.75%] | EVET | EVET | +1.03% |
| 20g | evren fazlası | 19,770 | +0.04% | -0.26% | [-0.19%, +0.28%] | hayır | hayır | -0.06% |
| 20g | trend evreni fazlası | 19,770 | +0.10% | -0.28% | [-0.08%, +0.28%] | hayır | hayır | -0.00% |

### `dip10`

- sinyal 35,475 · sembol 248 · gün 4,311 · aralık 2005-01-05 … 2026-07-28
- kurulum→sinyal bekleme (gün): medyan 2 · ort 2.36 · p90 5 · maks 30
- sinyal gününde trend şablonu HÂLÂ geçiyor: 94.5%

| ufuk | ölçüm | n | ort | medyan | %95 CI (21g blok) | CI 0-dışı | poz.&anlamlı | maliyet sonrası ort |
|---|---|---:|---:|---:|---|---|---|---:|
| 5g | ham | 35,441 | +0.17% | +0.26% | [-0.02%, +0.35%] | hayır | hayır | +0.07% |
| 5g | evren fazlası | 35,441 | -0.07% | -0.10% | [-0.13%, +0.00%] | hayır | hayır | -0.17% |
| 5g | trend evreni fazlası | 35,441 | -0.09% | -0.12% | [-0.14%, -0.04%] | EVET | hayır | -0.19% |
| 10g | ham | 35,415 | +0.41% | +0.45% | [+0.04%, +0.72%] | EVET | EVET | +0.31% |
| 10g | evren fazlası | 35,415 | -0.08% | -0.21% | [-0.19%, +0.00%] | hayır | hayır | -0.18% |
| 10g | trend evreni fazlası | 35,415 | -0.11% | -0.22% | [-0.17%, -0.05%] | EVET | hayır | -0.21% |
| 20g | ham | 35,354 | +1.00% | +1.01% | [+0.57%, +1.41%] | EVET | EVET | +0.90% |
| 20g | evren fazlası | 35,354 | -0.13% | -0.31% | [-0.26%, +0.01%] | hayır | hayır | -0.23% |
| 20g | trend evreni fazlası | 35,354 | -0.13% | -0.33% | [-0.23%, -0.04%] | EVET | hayır | -0.23% |

> Taban tanımları — evren: aynı takvim gününde ileri getirisi TANIMLI olan TÜM evren sembollerinin ortalaması; trend evreni: aynı günde trend şablonunu geçen (tt>=0.6) sembollerin ortalaması — pullback kurulumunun trend FİLTRESİNDEN ayrı katkısını izole eder
> kart success_metric'i 'sinyal dilimi anlamlı POZİTİF' diyor; birincil okuma HAM ortalamadır. İki taban ölçümü TANI amaçlıdır (piyasa sürüklenmesi / trend filtresi payını ayırır), ek hipotez testi değildir.

### 4.1 Alternatif okuma — cf defterinin tarih penceresine kısıtlı

| tanım | pencere | sinyal | 5g ort (CI) | 10g ort (CI) | 20g ort (CI) |
|---|---|---:|---|---|---|
| `sma20_dokunus` | 2022-01-03 … 2026-07-23 | 4,922 | +0.02% [-0.33%, +0.49%] | +0.32% [-0.20%, +1.14%] | +0.94% [-0.03%, +2.06%] |
| `dip10` | 2022-01-03 … 2026-07-23 | 6,842 | +0.11% [-0.19%, +0.49%] | +0.32% [-0.13%, +0.88%] | +0.82% [+0.00%, +1.66%] |

## 5 · (ii) Bağımsızlık — kırılma ailesiyle örtüşme (Jaccard)

**Kırılma ailesi sinyal günlerinin kaynağı:** state/counterfactuals.jsonl — MEVCUT STRATEJİNİN GERÇEK ADAY ÜRETİMİ. Her satır (ticker, date, setup); kırılma ailesi = {breakout_vcp, momentum_burst}. Bu, kurulumları yeniden uygulamak yerine motorun KENDİ ürettiği sinyal günleridir (yeniden-uygulama sapması yok).

**Kısıt:** defter yalnız 2022-01-03..2026-07-23 penceresini kapsar; Jaccard bu pencerede hesaplanır (pullback sinyalleri de aynı pencereye kısıtlanır).

| defter kalemi | değer |
|---|---|
| defter satırı | 7,161 |
| setup dağılımı | `momentum_burst`=1,120, `breakout_vcp`=6,011, `pullback`=29, `episodic_pivot`=1 |
| kırılma ailesi dışı satır | 30 |
| near_miss satır (aile içi) | 4,981 |
| defter tarih aralığı | 2022-01-03 … 2026-07-23 (1,011 gün) |

| tanım | kırılma kümesi | A (pullback) | B (kırılma) | kesişim | birleşim | **Jaccard** | A'nın örtüşen oranı | <0.3 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `sma20_dokunus` | defter · near_miss HARİÇ (gerçek sinyal) | 4,922 | 1,988 | 131 | 6,779 | **0.0193** | 0.0266 | EVET |
| `sma20_dokunus` | defter · near_miss DÂHİL | 4,922 | 6,814 | 153 | 11,583 | **0.0132** | 0.0311 | EVET |
| `dip10` | defter · near_miss HARİÇ (gerçek sinyal) | 6,842 | 1,988 | 118 | 8,712 | **0.0135** | 0.0172 | EVET |
| `dip10` | defter · near_miss DÂHİL | 6,842 | 6,814 | 139 | 13,517 | **0.0103** | 0.0203 | EVET |

A = pullback sinyal günleri, **cf defterinin tarih penceresine kısıtlı** (elma-elma).

### 5.1 İkinci kaynak — kırılma tetiklerinin panel üzerinde YENİDEN TÜRETİLMESİ

Defter kümesi dardır (skor/RS/R:R kapılarından geçmiş hâli, near_miss hariç 1,988 sembol-gün) ve defter yalnız 2022+'yı kapsar; böyle bir B ile küçük Jaccard kısmen mekanik olurdu. Bu yüzden kırılma ailesi kurulumların **plan-tetik çekirdeğinden** panel üzerinde yeniden türetildi.

Türetme (SALT-OHLCV kısmı, `strategy.py`den): `breakout_vcp` = taze pivot kırılımı (`ind.pivot_high(high, 40, exclude_recent=1)`, c_prev < pivot ≤ c) + `volume_ratio(vol,50) ≥ 1.5` + `yakınlık ≤ 2.3%`; `momentum_burst` = `gün ≥ 4%` + `hacim ≥ 1.5×` + `c > 50-SMA` + `tt ≥ 0.6` + `c > c_prev`. Parametreler CANLI `state/strategy.yaml (CANLI)`dan.

**ALINMADI:** kesitsel RS kapısı, bileşik skor kapısı, `weekly_uptrend`, R:R/stop kapıları — hepsi B'yi DARALTIRDI. Alınmaması B'yi genişletir; `|A∩B|/|A|` oranı B'de monoton arttığı için bu, bağımsızlık iddiası için **muhafazakâr** sınavdır.

| kapsam | tanım | kırılma kümesi | A | B | kesişim | **Jaccard** | A'nın örtüşen oranı | <0.3 |
|---|---|---|---:|---:|---:|---:|---:|---|
| tam panel | `sma20_dokunus` | `breakout_vcp_cekirdek` | 19,915 | 10,567 | 156 | **0.0051** | 0.0078 | EVET |
| tam panel | `sma20_dokunus` | `momentum_burst_cekirdek` | 19,915 | 6,515 | 805 | **0.0314** | 0.0404 | EVET |
| tam panel | `sma20_dokunus` | `kirilma_ailesi_BIRLESIM` | 19,915 | 15,982 | 831 | **0.0237** | 0.0417 | EVET |
| tam panel | `dip10` | `breakout_vcp_cekirdek` | 35,475 | 10,567 | 253 | **0.0055** | 0.0071 | EVET |
| tam panel | `dip10` | `momentum_burst_cekirdek` | 35,475 | 6,515 | 733 | **0.0178** | 0.0207 | EVET |
| tam panel | `dip10` | `kirilma_ailesi_BIRLESIM` | 35,475 | 15,982 | 868 | **0.0172** | 0.0245 | EVET |
| cf penceresi | `sma20_dokunus` | `breakout_vcp_cekirdek` | 4,922 | 1,905 | 40 | **0.0059** | 0.0081 | EVET |
| cf penceresi | `sma20_dokunus` | `momentum_burst_cekirdek` | 4,922 | 1,550 | 168 | **0.0267** | 0.0341 | EVET |
| cf penceresi | `sma20_dokunus` | `kirilma_ailesi_BIRLESIM` | 4,922 | 3,206 | 175 | **0.0220** | 0.0356 | EVET |
| cf penceresi | `dip10` | `breakout_vcp_cekirdek` | 6,842 | 1,905 | 49 | **0.0056** | 0.0072 | EVET |
| cf penceresi | `dip10` | `momentum_burst_cekirdek` | 6,842 | 1,550 | 161 | **0.0196** | 0.0235 | EVET |
| cf penceresi | `dip10` | `kirilma_ailesi_BIRLESIM` | 6,842 | 3,206 | 179 | **0.0181** | 0.0262 | EVET |

→ Kırılma kümesi defterdekinin ~8 katına çıkarıldığında bile Jaccard aynı büyüklük mertebesinde kalıyor. Bağımsızlık bacağı **kaynaktan bağımsız olarak** geçiyor.

## 6 · (iii) Pozitif kontrol + PK4/PK5

AYNI boru hattı, kart çivisi: ham rvol20 @20 cf-katman IC ≈ 0.0645 (max_olcum/EDG-2026-004 turu). resmom_olcum aynı çiviyi bars_integrity dışlamalı yolda 0.0637 ölçtü — bu tur da DIŞLAMALI yoldadır.

Katman: counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı)

| ufuk | IC | n | %95 CI | CI 0-dışı |
|---|---:|---:|---|---|
| 5g | 0.0374 | 2,095 | [-0.0188, +0.0783] | hayır |
| 10g | 0.0516 | 2,093 | [-0.0084, +0.0950] | hayır |
| 20g | 0.0642 | 2,087 | [+0.0092, +0.1125] | EVET |

**Çivi:** hedef 0.0645 · ölçülen **0.0642** · sapma 0.0003 · tolerans 0.005 → **GEÇTİ = EVET**

Canlı defterdeki (`state/component_ic.json`) cf·rvol20 IC değerleri: 5g=0.0320, 10g=0.0456, 20g=0.0604

### PK4 — yol tutarlılığı

YOL TUTARLILIĞI: close[t+h]/close[t]-1, aradaki GÜNLÜK getirilerin bileşiğine eşit olmalı. Takvim kapısı/integrity kırpması ufkun İÇİNDE bar düşürdüyse ya da kaydırma bir gün kaysaydı bu özdeşlik bozulurdu.

| ufuk | n | maks mutlak fark | geçti |
|---|---:|---:|---|
| 5g | 62,337 | 0.0 | EVET |
| 10g | 62,255 | 0.0 | EVET |
| 20g | 62,088 | 0.0 | EVET |

### PK5 — özdeşlikler

İKİ ÖZDEŞLİK: (A) GERİYE-BAKIŞSIZLIK — trend_template TAM seride hesaplanınca ile df.iloc[:i+1] KESİLMİŞ seride hesaplanınca AYNI değeri vermeli (kart: 'YALNIZ t ve öncesi'); kurulum maskeleri de kesilmiş seriden yeniden türetilince aynı çıkmalı. (B) DURUM MAKİNESİ — sinyal günleri, bağımsız yazılmış kaba bir ileri-tarama uygulamasıyla birebir aynı olmalı.

| parça | ölçüm | geçti |
|---|---|---|
| A · geriye-bakışsızlık | 40 örnek · maks tt farkı 0.0 · kurulum maskesi uyuşmazlığı 0 | EVET |
| B · durum makinesi | 20 seri · ayrışan 0 | EVET |
| C · hızlı ortalama | 50 örnek · maks fark 0.0 | EVET |

## 7 · Duyarlılık (HÜKME GİRMEZ — K harcanmaz)

Operasyonel okuma duyarlılığı: 'geri-çekilme'/'en düşük' KAPANIŞ üzerinden okunsaydı. Hüküm bacağı DEĞİL, K HARCANMAZ — yalnız birincil okumanın taşıyıcı olup olmadığını gösterir. CI/anlamlılık BİLEREK hesaplanmadı.

| okuma | sinyal | 5g ort | 10g ort | 20g ort |
|---|---:|---:|---:|---:|
| `sma20_dokunus` (BİRİNCİL: high/low) | 19,915 | +0.17% | +0.49% | +1.13% |
| `sma20_dokunus` (kapanış okuması) | 9,819 | +0.15% | +0.56% | +1.35% |
| `dip10` (BİRİNCİL: high/low) | 35,475 | +0.17% | +0.41% | +1.00% |
| `dip10` (kapanış okuması) | 58,042 | +0.14% | +0.38% | +0.95% |

## 8 · Hüküm ÖNERİSİ (kart ölçütü — kartı Rol-1 işler)

**Kart success_metric:** sinyal dilimi @10 VEYA @20 anlamlı POZİTİF (21g blok-bootstrap CI 0-dışı) VE kırılma-ailesi ile Jaccard < 0.3

| tanım | bacak1: @10 veya @20 poz.&anlamlı | bacak2: Jaccard | bacak2 < 0.3 | success_metric | kill#1 | kill#2 |
|---|---|---:|---|---|---|---|
| `sma20_dokunus` | EVET | 0.0193 | EVET | **EVET** | hayır | hayır |
| `dip10` | EVET | 0.0135 | EVET | **EVET** | hayır | hayır |

- Pozitif kontrol GEÇTİ: **EVET** — geçmediyse hüküm YAZILMAZ.
- kill#1 (iki tanımda da CI 0-içi): hayır

### Kart ölçütünün OTOMATİK sonucu: **SUCCESS — bağımsız kurulum ailesi adayı (gölge-önce entegrasyon turu)**

### 8.1 Ölçüm ajanının notu — bu SUCCESS neyi ölçüyor?

Kart `success_metric` birinci bacağı **HAM** ileri getirinin pozitifliğini istiyor; bu ölçüt
piyasa sürüklenmesinden (drift) ayrışmıyor. Aynı boru hattında ölçülen iki taban bunu gösteriyor:

| tanım | ufuk | ham ort | evren fazlası ort (CI) | trend evreni fazlası ort (CI) |
|---|---|---:|---|---|
| `sma20_dokunus` | 10g | +0.49% | +0.04% [-0.10%, +0.19%] | +0.04% [-0.07%, +0.16%] |
| `sma20_dokunus` | 20g | +1.13% | +0.04% [-0.19%, +0.28%] | +0.10% [-0.08%, +0.28%] |
| `dip10` | 10g | +0.41% | -0.08% [-0.19%, +0.00%] | -0.11% [-0.17%, -0.05%] |
| `dip10` | 20g | +1.00% | -0.13% [-0.26%, +0.01%] | -0.13% [-0.23%, -0.04%] |

Yani: **sinyal gününden sonraki getiri, aynı gün evrenin/trend evreninin ortalamasının
ÜSTÜNDE değil.** `dip10`'da trend evreni fazlası her üç ufukta da CI'sı tamamen 0'ın ALTINDA
(negatif ve anlamlı) — geri-çekilmede girmek, trend şablonunu geçen ortalama bir isme göre
KÖTÜ. `sma20_dokunus`'ta fazla CI'ları 0'ı içeriyor (bilgisiz).

Ayrıca **popülasyon okumasına duyarlı**: kart `horizon` alanı 'cf-katmanlı' dediği için cf
defterinin tarih penceresine kısıtlı okuma da ölçüldü. O pencerede:

| tanım | pencere | sinyal | @10 CI | @20 CI | poz.&anlamlı |
|---|---|---:|---|---|---|
| `sma20_dokunus` | 2022-01-03 … 2026-07-23 | 4,922 | [-0.20%, +1.14%] | [-0.03%, +2.06%] | hayır |
| `dip10` | 2022-01-03 … 2026-07-23 | 6,842 | [-0.13%, +0.88%] | [+0.00%, +1.66%] | EVET |

→ cf penceresi okumasında **bacak1 İKİ tanımda da düşer** (kart kill#1). Tam panel
okumasında geçer. Fark, 2005-2021 döneminden geliyor.

**Öneri (hükmü Rol-1 işler):** bağımsızlık bacağı GÜÇLÜ ve tartışmasız geçti; ileri-getiri
bacağı kartın yazdığı biçimde geçiyor ama ölçüm, geçişin sürüklenmeden geldiğini gösteriyor.
Eşiği geriye dönük DEĞİŞTİRMEK yasak olduğuna göre bu bir *kart ölçütü kusuru* bulgusudur:
kart metnine göre SUCCESS, kanıta göre kenar YOK. Rol-1'in üç seçeneği ayrık: (a) kart metnine
uyup SUCCESS yazmak ve gölge-önce entegrasyonu ölçüsüz bir kenar üstüne kurmak; (b) ARŞİV +
not (bağımsız aile ama kenarsız); (c) ölçütü taban-fazlası olarak sabitleyen YENİ bir kart
açmak (bu kartın K'sı harcanmış sayılır, tanım gevşetilmez). Ölçüm ajanı (b)+(c)'yi işaret
ediyor; hüküm Rol-1'indir.

## 9 · Zemin ve yeniden üretilebilirlik

- **Repoya yazım:** YOK. Tek iz: Python import'unun ürettiği meridian/__pycache__/*.pyc (versiyonlanmayan bytecode). config.STATE sandbox'a çevrildi; canlı state SALT-OKUNDU (state/ altında değişen dosya yok).
- **Eşzamanlı oturum:** Ölçüm koşarken bu Mac'te BAŞKA bir oturum repo çalışma ağacını değiştirdi (git status: 10 değişik dosya + 2 izlenmeyen). Ölçümün İTHAL ETTİĞİ dört modülden üçü (indicators.py, strategy.py, adapters/data.py) HİÇ dokunulmadı; analytics.py dokunuldu.
- **Canlı state'e ikinci yazar:** Ölçüm penceresinde canlı state/ altında ÜÇ dosya değişti: sieve.json, events.jsonl, .locks/sieve.json.lock (12:08 yerel). BU YAZIMLAR BU ÖLÇÜMDEN DEĞİL. Bu sürecin obs.warn olayları SANDBOX _state/events.jsonl dosyasına düştü (son yazım 12:05:41 = bagimsizlik_ek.py bitişi). Canlı events.jsonl 12:08:04te yazıldı; o anda yalnız rapor.py ve damga.py koşuyordu ve ikisi de meridian ithal ETMİYOR. Mac üzerinde EŞZAMANLI başka bir oturum canlı state'e YAZIYOR (sieve.json). Bu ölçümü etkilemedi (okuduğu defterlerin hiçbiri değişmedi) ama Rol-1'e bildirilir: canlı state'e yazan ikinci bir yazar var.
- **`analytics.py` incelemesi:** kullanılan fonksiyon `spearman_ic (analytics.py:811)`; değişen hunk aralıkları 2366-2421 (yalnız prediction_accuracy_band); etkilendi mi: **hayır**. değişiklik ölçüm BİTTİKTEN sonra diske indi ve zaten farklı bir fonksiyondaydı — ölçüm zemini etkilenmedi

- Repo HEAD: `2d4cbf4f050bebbbae74b5b7da67c97767313439` (koşum boyunca commit araya girmedi: 0 commit) · Python 3.12.7
- Bar önbelleği: 259 dosya · birleşik sha256 `91a3f76063e2eb64…`
- Sandbox `_state` içeriği (canlıya DEĞİL): bars_integrity.json, events.jsonl

Dosyalar: `sonuc.json` (tek yetkili artefakt) · `RAPOR.md` · `kod_damgasi.json` · `bagimsizlik_ek.json` · `sinyaller.csv` (sinyal satırları) · `olcum.py` / `bagimsizlik_ek.py` / `rapor.py` / `damga.py` / `duman.py`

