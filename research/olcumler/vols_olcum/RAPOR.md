# EDG-2026-008 — vol-scaling overlay ÖLÇÜM RAPORU

* Kart: `research/cards/EDG-2026-008-vol-scaling-overlay.yaml` · aile `momentum_vol_scaling_overlay`
* Ölçüm zamanı: 2026-07-31T11:31:53.538473+00:00
* Motor damgası: git HEAD `6ec281c3aefc05b40d67d1630bea05d5746a79e3` · 89 dosya · kopya=repo: EVET

> SALT-ÖLÇÜM: depoya ve canlı state'e hiçbir yazım yapılmadı; motor sandbox'a kopyalandı, barlar canlı önbellekten salt-okunur okundu. Kart dosyasına DOKUNULMADI — aşağıdaki hüküm bir ÖNERİDİR, kartı Rol-1 işler.

## 0. Tasarım (kartın harfiyen uygulanması)

* **Çarpan**: m = clip(sigma_hedef / sigma_gercek(P), 0.5, 1.5) — YALNIZ yeni-giriş boyutuna
* **Uygulama noktası**: dolum anında `size_mult` üzerinden (motorun derisk rampasıyla AYNI yol); `plan['size_r']` DEĞİŞMEZ → guard'ın gördüğü open_risk_r değişmez → kapı hükmü kaymaz
* **As-of**: m, D KAPANIŞININ SPY verisinden hesaplanır ve D+1 AÇILIŞINDA dolan emre uygulanır — ileri bakma YOK
* **sigma_hedef kaynağı**: IS [2022-01-01, 2024-01-01) gerçekleşen vol serisinin MEDYANI; on_adim_sigma.py'de TEK SEFER hesaplandı, koşuma BEYAN edilerek geçirildi (aranmadı, K'yı artırmaz)
* **Koşulmayan kollar**: isonly / tam kollar KOŞULMADI — WP-M oosonly standardı; tanı gerekirse Rol-1 ister

| kol | tanım |
|---|---|
| `ref_snapshot` | yamasız ikiz (pozitif kontrol referansı) |
| `kapali` | yamalı motor, knob KAPALI (pozitif kontrol ikizi) |
| `p21_oosonly` | P=21, çarpan YALNIZ 2024-01-01'den itibaren |
| `p63_oosonly` | P=63, çarpan YALNIZ 2024-01-01'den itibaren |

## 1. sigma_hedef BEYANI (ön adım — aranmadı, tek sefer hesaplandı)

* Endeks: `SPY` · 1398 bar (2021-01-04 → 2026-07-29)
* **sigma_gercek**: SPY günlük getirilerinin P-gün örneklem std'si (ddof=1) × sqrt(252); t ve ÖNCESİ — motorun `backtest.vols_gerceklesen` fonksiyonunun ta kendisi
* **sigma_hedef**: [2022-01-01, 2024-01-01) seanslarında hesaplanan sigma_gercek serisinin MEDYANI
* **isinma**: IS'in ilk seanslarında pencere, IS penceresinden ÖNCEKİ (2021) SPY barlarıyla dolar — bu ileri bakma DEĞİL, geriye bakmadır ve replay de aynısını yapar
* **m**: clip(sigma_hedef/sigma_gercek, 0.5, 1.5) — KART SABİTİ

| P (gün) | sigma_hedef (IS medyanı) | IS gün | IS sigma ort | IS sigma p05–p95 | OOS sigma medyan | OOS m medyan | OOS m p05–p95 | OOS bağlı oran |
|---|---|---|---|---|---|---|---|---|
| 21 | **0.176545** | 501 | 0.1852 | [0.0953, 0.3052] | 0.1227 | 1.4393 | [0.8106, 1.5] | %47.00 |
| 63 | **0.182742** | 501 | 0.1893 | [0.1069, 0.2793] | 0.1212 | 1.5 | [0.5534, 1.5] | %51.63 |

## 2. KOL İMZA TABLOSU

| kol | oos_score | PARA (search) | is_score | holdout | oos_n | search_n | confirm_n | avg_r | win_rate | Sharpe(işlem) | maxDD(işlem) | süre sn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ref_snapshot` | 0.0579 | 0.1605 | 0.0651 | _ölçülemedi_ | 130 | 103 | 22 | 0.012 | 0.354 | 0.226 | 0.0717 | 724.4 |
| `kapali` | 0.0579 | 0.1605 | 0.0651 | _ölçülemedi_ | 130 | 103 | 22 | 0.012 | 0.354 | 0.226 | 0.0717 | 722.2 |
| `p21_oosonly` | 0.0807 | 0.2103 | 0.0651 | _ölçülemedi_ | 109 | 86 | 20 | 0.046 | 0.367 | 0.508 | 0.0746 | 766.2 |
| `p63_oosonly` | 0.0528 | 0.1037 | 0.0651 | _ölçülemedi_ | 75 | 61 | 13 | 0.002 | 0.333 | 0.359 | 0.0767 | 771.2 |

### Defter ve BOYUT imzaları (ilk 16 hane)

| kol | trade_digest search | trade_digest confirm | qty_digest search | qty_digest confirm |
|---|---|---|---|---|
| `ref_snapshot` | `9f6527cc0151f166` | `715385ddfbcf9c88` | `15c83b0254cc8bd7` | `1b39119c88a3d540` |
| `kapali` | `9f6527cc0151f166` | `715385ddfbcf9c88` | `15c83b0254cc8bd7` | `1b39119c88a3d540` |
| `p21_oosonly` | `b3eb14ca13fb38e1` | `8d79158307a96263` | `ad6f0afde6d94100` | `95172565c80b6e5b` |
| `p63_oosonly` | `d49ea1227dee3476` | `807b2a044f60c3a4` | `ae255b31d43e4ac5` | `fa959fa6899fca9c` |

> `qty_digest` NEDEN AYRI: overlay `size_r`ı değil `qty`yi değiştirir (çarpan dolum anında uygulanır). `trade_digest` bu farkı GÖRMEZ — tek imzaya bakılsaydı overlay'in hiç ateşlemediği sanılırdı.

### MTM özkaynak istatistikleri

| kol | pencere | gün | günlük vol | yıllık vol | Sharpe (günlük→yıllık) | MTM maxDD | toplam getiri |
|---|---|---|---|---|---|---|---|
| `ref_snapshot` | equity_search | _ölçülemedi_ | | | | |  |
| `ref_snapshot` | equity_oos | _ölçülemedi_ | | | | |  |
| `kapali` | equity_search | 400 | 0.004912 | 0.078 | 0.6868 | 0.0582 | 0.0833 |
| `kapali` | equity_oos | 576 | 0.004266 | 0.0677 | 0.2941 | 0.0717 | 0.041 |
| `p21_oosonly` | equity_search | 400 | 0.005697 | 0.0904 | 0.8493 | 0.0663 | 0.122 |
| `p21_oosonly` | equity_oos | 576 | 0.004923 | 0.0781 | 0.5145 | 0.0746 | 0.0885 |
| `p63_oosonly` | equity_search | 400 | 0.004522 | 0.0718 | 0.5479 | 0.0752 | 0.0599 |
| `p63_oosonly` | equity_oos | 576 | 0.00377 | 0.0598 | 0.4371 | 0.0767 | 0.0572 |

## 3. POZİTİF KONTROL

**SONUÇ: GEÇTİ**

* Yöntem: yamasız ikiz (ref_snapshot) ile yamalı-knob-kapalı (kapali) kollarının SEARCH + CONFIRM defter imzaları, BOYUT (qty) imzaları ve skorları
* `trade_digest_tum` KIYASA GİRMEZ: yamalı motorda `_trades_all` (IS dahil TÜM defter), yamasızda its+itc (yalnız OOS) demektir — EDG-005'te belgelenen artefaktın aynısı.

| kontrol | eşit mi |
|---|---|
| `search_digest` | EVET |
| `confirm_digest` | EVET |
| `qty_digest_search` | EVET |
| `qty_digest_confirm` | EVET |
| `oos_score` | EVET |
| `para_search` | EVET |
| `is_score` | EVET |
| `holdout_score` | EVET |
| `n_trades_total` | EVET |

| kol | oos_score | PARA | is_score | n_trades_total |
|---|---|---|---|---|
| `ref_snapshot` | 0.0579 | 0.1605 | 0.0651 | 201 |
| `kapali` | 0.0579 | 0.1605 | 0.0651 | 201 |

### Yol tutarlılığı (PK4/PK5)

| kol | search digest yeniden üretildi | confirm digest yeniden üretildi | pnl_dollars var | qty var | geometri aynı | n_sembol |
|---|---|---|---|---|---|---|
| `ref_snapshot` | EVET | EVET | EVET | EVET | EVET | 250 |
| `kapali` | EVET | EVET | EVET | EVET | EVET | 250 |
| `p21_oosonly` | EVET | EVET | EVET | EVET | EVET | 250 |
| `p63_oosonly` | EVET | EVET | EVET | EVET | EVET | 250 |

## 4. TEDAVİ KIYASLARI — `kapali` (taban) vs oosonly kolları

### 4.1 `p21_oosonly`

| ölçüt | kapali (taban) | p21_oosonly | Δ |
|---|---|---|---|
| oos_score | 0.0579 | 0.0807 | 0.0228 |
| PARA (search) | 0.1605 | 0.2103 | 0.0498 |
| Sharpe (işlem) | 0.226 | 0.508 | 0.282 |
| avg_r | 0.012 | 0.046 | 0.034 |
| win_rate | 0.354 | 0.367 | 0.013 |
| oos_n | 130 | 109 | -21 |
| search_n | 103 | 86 | -17 |
| confirm_n | 22 | 20 | -2 |
| maxDD (işlem) | 0.0717 | 0.0746 | 0.0029 |
| total_return | 0.0319 | 0.0737 | 0.0418 |
| is_score | 0.0651 | 0.0651 | 0 |
| holdout_score | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ |
| fold_avg_r_mean | 0.0608 | 0.0807 | 0.0199 |
| trade_digest eşit | | | hayır |
| qty_digest eşit | | | hayır |

**PARA-v3 (blok/gün-kümeli bootstrap, `pnl_dollars`lı defterden)**

* P(ΔPARA < 0) = **0.4417** · ort Δ = 0.0505 · %95 CI = [-0.5567, 0.741] · CI 0-dışı: hayır · geçerli tekrar 600, ölçülemeyen 0

**CI paketi — pencere `search`**

* n = 399 gün (eşleştirilmiş)

| ölçüt | taban | tedavi | fark CI %95 | P(düşüş) |
|---|---|---|---|---|
| günlük ort getiri farkı | | 0.92 bps | [-2.00 bps, 2.58 bps] | 0.3588 |
| günlük vol | 0.004912 | 0.005697 | [-0.000266, 0.001807] | **0.0635** |
| yıllık vol | 0.078 | 0.0904 | | |
| MTM maxDD | 0.0582 | 0.0663 | [-0.0204, 0.0568] | **0.1948** |
| Sharpe (yıllık) | 0.6868 | 0.8493 | [-0.75, 0.5693] | 0.472 |
| vol oranı (tedavi/taban) | | 1.1598 | | |

**CI paketi — pencere `oos_tam`**

* n = 575 gün (eşleştirilmiş)

| ölçüt | taban | tedavi | fark CI %95 | P(düşüş) |
|---|---|---|---|---|
| günlük ort getiri farkı | | 0.81 bps | [-1.15 bps, 2.60 bps] | 0.232 |
| günlük vol | 0.004266 | 0.004923 | [-0.000356, 0.001393] | **0.0938** |
| yıllık vol | 0.0677 | 0.0781 | | |
| MTM maxDD | 0.0717 | 0.0746 | [-0.0505, 0.0589] | **0.4108** |
| Sharpe (yıllık) | 0.2941 | 0.5145 | [-0.4453, 0.8272] | 0.264 |
| vol oranı (tedavi/taban) | | 1.1538 | | |

### 4.2 `p63_oosonly`

| ölçüt | kapali (taban) | p63_oosonly | Δ |
|---|---|---|---|
| oos_score | 0.0579 | 0.0528 | -0.0051 |
| PARA (search) | 0.1605 | 0.1037 | -0.0568 |
| Sharpe (işlem) | 0.226 | 0.359 | 0.133 |
| avg_r | 0.012 | 0.002 | -0.01 |
| win_rate | 0.354 | 0.333 | -0.021 |
| oos_n | 130 | 75 | -55 |
| search_n | 103 | 61 | -42 |
| confirm_n | 22 | 13 | -9 |
| maxDD (işlem) | 0.0717 | 0.0767 | 0.005 |
| total_return | 0.0319 | 0.0429 | 0.011 |
| is_score | 0.0651 | 0.0651 | 0 |
| holdout_score | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ |
| fold_avg_r_mean | 0.0608 | 0.0038 | -0.057 |
| trade_digest eşit | | | hayır |
| qty_digest eşit | | | hayır |

**PARA-v3 (blok/gün-kümeli bootstrap, `pnl_dollars`lı defterden)**

* P(ΔPARA < 0) = **0.5333** · ort Δ = -0.0307 · %95 CI = [-0.6727, 0.5669] · CI 0-dışı: hayır · geçerli tekrar 600, ölçülemeyen 0

**CI paketi — pencere `search`**

* n = 399 gün (eşleştirilmiş)

| ölçüt | taban | tedavi | fark CI %95 | P(düşüş) |
|---|---|---|---|---|
| günlük ort getiri farkı | | -0.56 bps | [-4.26 bps, 1.86 bps] | 0.7438 |
| günlük vol | 0.004912 | 0.004522 | [-0.002104, 0.000729] | **0.6995** |
| yıllık vol | 0.078 | 0.0718 | | |
| MTM maxDD | 0.0582 | 0.0752 | [-0.0342, 0.053] | **0.333** |
| Sharpe (yıllık) | 0.6868 | 0.5479 | [-1.7938, 0.5718] | 0.748 |
| vol oranı (tedavi/taban) | | 0.9206 | | |

**CI paketi — pencere `oos_tam`**

* n = 575 gün (eşleştirilmiş)

| ölçüt | taban | tedavi | fark CI %95 | P(düşüş) |
|---|---|---|---|---|
| günlük ort getiri farkı | | 0.25 bps | [-2.38 bps, 2.29 bps] | 0.4358 |
| günlük vol | 0.004266 | 0.00377 | [-0.002081, 0.000409] | **0.8618** |
| yıllık vol | 0.0677 | 0.0598 | | |
| MTM maxDD | 0.0717 | 0.0767 | [-0.0828, 0.0381] | **0.6943** |
| Sharpe (yıllık) | 0.2941 | 0.4371 | [-1.1226, 0.8952] | 0.447 |
| vol oranı (tedavi/taban) | | 0.8837 | | |

## 5. ÇARPAN DAĞILIMI, BAĞLANMA ve ÇİFTE-KISMA

### `p21_oosonly`

| pencere | gün | m medyan | m p05–p95 | m min–max | ham m medyan | bağlı oran | üst-bağlı | alt-bağlı | m>1 oran | uygulanan medyan | uygulanan≠1 gün |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IS_2022_2024 | 501 | 1 | [0.5784, 1.5] | [0.5142, 1.5] | 1 | %18.56 | %18.56 | %0.00 | %50.10 | 1 | 0 |
| OOS_search | 400 | 1.4351 | [0.5, 1.5] | [0.5, 1.5] | 1.4351 | %49.00 | %43.75 | %5.25 | %83.00 | 1.4351 | 400 |
| OOS_tam | 583 | 1.4393 | [0.8106, 1.5] | [0.5, 1.5] | 1.4393 | %47.00 | %43.40 | %3.60 | %85.25 | 1.4398 | 583 |

**Çifte kısma (ısı-tavanı × vol-overlay)**

| pencere | gün | derisk<1 gün | derisk medyan | derisk p05–p95 | m<1 gün | ÇİFTE<1 gün | çifte oran | dolum denenen gün | çifte+dolumlu gün | en sert çarpım | çarpım medyanı | toplam armed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cifte_kisma_IS | 501 | 189 | 1 | [0.4557, 1] | 0 | **0** | %0.00 | 54 | 0 | 0.4226 | 1 | 114 |
| cifte_kisma_OOS | 583 | 469 | 0.561 | [0.0708, 1] | 86 | **86** | %14.75 | 104 | 5 | 0.0621 | 0.6274 | 341 |

* OOS dolum: 130 deneme → 113 dolum · ret nedenleri: `{'entry_missed_limit': 13, 'open_below_stop': 1, 'max_chase': 3}`

### `p63_oosonly`

| pencere | gün | m medyan | m p05–p95 | m min–max | ham m medyan | bağlı oran | üst-bağlı | alt-bağlı | m>1 oran | uygulanan medyan | uygulanan≠1 gün |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IS_2022_2024 | 501 | 1 | [0.6544, 1.5] | [0.6285, 1.5] | 1 | %17.76 | %17.76 | %0.00 | %50.10 | 1 | 0 |
| OOS_search | 400 | 1.4518 | [0.5509, 1.5] | [0.5365, 1.5] | 1.4518 | %42.00 | %42.00 | %0.00 | %83.25 | 1.4518 | 400 |
| OOS_tam | 583 | 1.5 | [0.5534, 1.5] | [0.5365, 1.5] | 1.5078 | %51.63 | %51.63 | %0.00 | %88.51 | 1.5 | 583 |

**Çifte kısma (ısı-tavanı × vol-overlay)**

| pencere | gün | derisk<1 gün | derisk medyan | derisk p05–p95 | m<1 gün | ÇİFTE<1 gün | çifte oran | dolum denenen gün | çifte+dolumlu gün | en sert çarpım | çarpım medyanı | toplam armed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cifte_kisma_IS | 501 | 189 | 1 | [0.4557, 1] | 0 | **0** | %0.00 | 54 | 0 | 0.4226 | 1 | 114 |
| cifte_kisma_OOS | 583 | 487 | 0.1183 | [0.0526, 1] | 67 | **67** | %11.49 | 74 | 4 | 0.0554 | 0.1637 | 379 |

* OOS dolum: 88 deneme → 79 dolum · ret nedenleri: `{'entry_missed_limit': 6, 'open_below_stop': 1, 'qty_zero': 1, 'max_chase': 1}`

### `kapali`

| pencere | gün | m medyan | m p05–p95 | m min–max | ham m medyan | bağlı oran | üst-bağlı | alt-bağlı | m>1 oran | uygulanan medyan | uygulanan≠1 gün |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IS_2022_2024 | 501 | 1 | [0.5784, 1.5] | [0.5142, 1.5] | 1 | %18.56 | %18.56 | %0.00 | %50.10 | 1 | 0 |
| OOS_search | 400 | 1.4351 | [0.5, 1.5] | [0.5, 1.5] | 1.4351 | %49.00 | %43.75 | %5.25 | %83.00 | 1 | 0 |
| OOS_tam | 583 | 1.4393 | [0.8106, 1.5] | [0.5, 1.5] | 1.4393 | %47.00 | %43.40 | %3.60 | %85.25 | 1 | 0 |

**Çifte kısma (ısı-tavanı × vol-overlay)**

| pencere | gün | derisk<1 gün | derisk medyan | derisk p05–p95 | m<1 gün | ÇİFTE<1 gün | çifte oran | dolum denenen gün | çifte+dolumlu gün | en sert çarpım | çarpım medyanı | toplam armed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cifte_kisma_IS | 501 | 189 | 1 | [0.4557, 1] | 0 | **0** | %0.00 | 54 | 0 | 0.4226 | 1 | 114 |
| cifte_kisma_OOS | 583 | 312 | 0.8691 | [0.0987, 1] | 0 | **0** | %0.00 | 121 | 0 | 0.0987 | 0.8691 | 304 |

* **m serisi koldan bağımsız mı?** EVET (1146 gün; ilk fark: yok) — kapali kolu P=21 ile aynı sigma_hedef'i taşır ve knob KAPALI olduğu hâlde m'yi kaydeder; iki serinin birebir aynı olması m'nin SPY'den türediğini, portföy durumundan ETKİLENMEDİĞİNİ gösterir

* OOS dolum: 155 deneme → 134 dolum · ret nedenleri: `{'entry_missed_limit': 14, 'open_below_stop': 1, 'max_chase': 5, 'qty_zero': 1}`

## 5b. MEKANİZMA — işlem sayısı neden değişti? (kartın maliyet-modeli beyanının sınanması)

* **Kart beyanı**: cost_model: 'overlay işlem sayısını değiştirmez (boyut değiştirir)' — ÖLÇÜM BU BEYANI YALANLIYOR
* **Ölçülen yol**: m > 1 → pozisyon boyu büyür → özkaynak salınımı artar → `broker.derisk_mult` rampası daha derin, `broker.max_positions_at` eşzamanlı slotu kısar → silahlı planların daha azı dolum kapısından geçer
* `plan['size_r']` DEĞİŞMEDİĞİ için guard'ın kapı hükmü kaymadı (silahlanan plan sayısı tedavi kollarında DAHA YÜKSEK); düşüş guard'dan değil DOLUM KAPISINDAN geliyor — bu ayrım tasarımın doğrudan sonucu ve ölçülebilir olması için sayaçlar oraya kondu.

| kol | OOS silahlanan plan (toplam) | dolum kapısından geçen | dolan | OOS işlem (n) | derisk medyan | derisk<1 gün | derisk p05–p95 | ret nedenleri |
|---|---|---|---|---|---|---|---|---|
| `kapali` | 304 | 155 | 134 | 130 | 0.8691 | 312 | [0.0987, 1] | `{'entry_missed_limit': 14, 'open_below_stop': 1, 'max_chase': 5, 'qty_zero': 1}` |
| `p21_oosonly` | 341 | 130 | 113 | 109 | 0.561 | 469 | [0.0708, 1] | `{'entry_missed_limit': 13, 'open_below_stop': 1, 'max_chase': 3}` |
| `p63_oosonly` | 379 | 88 | 79 | 75 | 0.1183 | 487 | [0.0526, 1] | `{'entry_missed_limit': 6, 'open_below_stop': 1, 'qty_zero': 1, 'max_chase': 1}` |

## 5c. POZİTİF-EV ÖNKOŞULU (kart guard'ı)

* Kart beyanı: taban V3 OOS para_search 0.0856 > 0 (wpg_olcum ref_snapshot, 2026-07-31 sabahı)
* **Bu turda ölçülen taban** (`ref_snapshot`): PARA(search)=0.1605 · oos_score=0.0579 · oos_n=130 · is_score=0.0651
* Önkoşul sağlandı mı (taban PARA > 0): **EVET**
* Sapma nedeni: MOTOR AYNI GÜN DEĞİŞTİ: bu tur BUGÜNKÜ depo motoruyla koşuldu (WP-E E1 giriş-icra yasası: limit fiyat tavanı + gap vetosu; goal.yaml'a `execution_v2`/`pessimistic_band_v2` blokları eklendi; H9 SQLite turu). wpg_olcum'un 0.0856'sı E1 ÖNCESİ motorun sayısıdır — iki sayı farklı motorlardan gelir, kıyaslanamaz. Bu turun İÇ tutarlılığı bozulmaz: dört kolun DÖRDÜ de aynı motorla koştu.

## 6. KART ÖLÇÜTÜNE GÖRE HÜKÜM ÖNERİSİ

* Eşikler (karttan, değiştirilmedi): `{'P(ΔS<0) < ': 0.5, 'P(düşüş) >= ': 0.95, 'kill2_m_bandi': [0.9, 1.1], 'kill2_medyan_tolerans': 0.05}`
* Okuma penceresi: başarı/kill okuması SEARCH dilimindendir (PARA-v3 ile AYNI popülasyon); tam-OOS karşılığı bilgi olarak yanında durur

| kol | ÖNERİ | P(ΔPARA<0) | PARA anlamlı arttı | vol düştü P≥0.95 | maxDD düştü P≥0.95 | Sharpe anlamlı düştü | kill#2 etkisiz | m medyan | m p05–p95 | bağlı |
|---|---|---|---|---|---|---|---|---|---|---|
| `p21_oosonly` | **bilgisiz/yonsuz** | 0.4417 | hayır | hayır | hayır | hayır | hayır | 1.4393 | [0.8106, 1.5] | %47.00 |
| `p63_oosonly` | **bilgisiz/yonsuz** | 0.5333 | hayır | hayır | hayır | hayır | hayır | 1.5 | [0.5534, 1.5] | %51.63 |

* **`p21_oosonly`** → `bilgisiz/yonsuz` — P(ΔPARA<0)=0.4417 · vol düştü P=0.0635 · maxDD düştü P=0.1948 · m medyan=1.439344 p05-p95=[0.810581, 1.5] bağlı=0.47
* **`p63_oosonly`** → `bilgisiz/yonsuz` — P(ΔPARA<0)=0.5333 · vol düştü P=0.6995 · maxDD düştü P=0.333 · m medyan=1.5 p05-p95=[0.553444, 1.5] bağlı=0.5163

* kill#3 (iki pencerede de yönsüz): EVET
* **AİLE ÖNERİSİ: `arşiv`**

---

Bu rapor `rapor.py` tarafından YALNIZ `sonuc.json`dan üretildi; hiçbir sayı elle taşınmadı. Kart dosyasına dokunulmadı.
