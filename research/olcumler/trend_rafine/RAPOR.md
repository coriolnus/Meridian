# WP-K — UZUN-UFUK TREND KOLU RAFİNE ÖLÇÜMÜ (EDG-2026-009)

Rol 2 · SALT-ÖLÇÜM · sim 2010-12-31 → 2026-07-28 (15.57 yıl) · repo HEAD `7293cc63f3a0` · repoya/state'e hiçbir bayt yazılmadı.

Bu rapor kartın ölçütlerini ÖLÇER; hükmü Rol-1 yazar. Karta dokunulmadı.

## 0. POZİTİF KONTROL (kart guard'ı) — ŞASİ GEÇERLİ

| kontrol | ölçülen | referans (2026-07-30) | sonuç |
|---|---|---|---|
| ham kol fazlası vs EW-evren (yıllık) | 13.145% | 13.145% | fark 0.000000 puan |
| t (NW lag3) | 3.6907 | 3.6907 | fark 0.000000 |
| rafine motor ≡ şasi motoru | maks mutlak özkaynak farkı 0.0 $ | 0 | EVET |
| PK4 yol tutarlılığı | 7.0e-14% | ~0 | ✅ |
| PK5 nakit-akışı özdeşliği | -1.9e-12% | ~0 | ✅ |

**GUARD GEÇTİ: EVET** — ham kol hükmü BİREBİR yeniden üretildi (fark sıfır,
son basamağa kadar). Canlı bar önbelleği 2026-07-30 anlık görüntüsünden yalnız iki hayalet-seans
satırında ayrılıyor (SPY 2018-11-22, 2025-05-26) ve deponun kendi kapısı o satırları zaten düşürüyor.
Şasi geçerlidir; rafine hücrelerin sayıları okunabilir.

## 1. GRID (K=4) — ANA TABLO

### 1a. Getiri / risk (tam pencere, 10bps net)
| hücre | çıkış | evren | CAGR | vol | Sharpe | maxDD | son özkaynak |
|---|---|---|---|---|---|---|---|
| **A_chandelier_full** | chandelier_mevcut | full_251 | 30.32% | 27.9% | 1.09 | -40.2% | 61,776,510 $ |
| **B_rotate_full** | aylik_rebalans_duraksiz | full_251 | 32.26% | 29.4% | 1.10 | -43.8% | 77,796,270 $ |
| **C_chandelier_pit** | chandelier_mevcut | pit_sagkalan | 18.38% | 25.1% | 0.80 | -32.4% | 13,832,419 $ |
| **D_rotate_pit** | aylik_rebalans_duraksiz | pit_sagkalan | 19.48% | 27.2% | 0.79 | -34.8% | 15,992,642 $ |
| _EW_full_BH_ | — | — | 17.11% | 19.4% | 0.91 | -34.0% | 11,702,599 $ |
| _EW_full_aylik_ | — | — | 14.61% | 17.4% | 0.87 | -37.6% | 8,362,564 $ |
| _EW_pit_aylik_ | — | — | 13.00% | 17.0% | 0.80 | -37.5% | 6,704,873 $ |
| _SPY_BH_ | — | — | 11.99% | 17.1% | 0.75 | -34.1% | 5,834,291 $ |

**ÇITA SEÇİMİ ÖNEMLİ — ve fark maliyet DEĞİL:** statik `EW_full_BH` (CAGR
17.11%) ile aylık denkleştirilmiş
`EW_full_aylik` (CAGR 14.61%) arasında
2.50 puan/yıl
fark var. Bu fark friksiyon değil: aylık EW çıtasının devri yalnız
%34/yıl ve friksiyon sürüklemesi %0.068/yıl.
Fark EKONOMİK: statik B&H 15 yılda kendiliğinden kazananlara ağırlık veren bir portföye dönüşür —
yani ham kolun 2026-07-30 çıtası zaten momentum yüklüdür. Bu yüzden her hücre İKİ çıtaya karşı da
raporlanır ve §3c tanısı bu ayrımdan çıkar.

### 1b. Fazla getiri, t, devir, maliyet (kartın istediği hücre tablosu)
| hücre | fazla vs EŞLEMELİ çıta | t | fazla vs TABAN çıta (EW_full_BH) | t | maxDD | vol | devir (tek-yön/yıl) | friksiyon sürükleme |
|---|---|---|---|---|---|---|---|---|
| **A_chandelier_full** (EW_full_aylik) | 15.80% | 4.09 | 13.14% | 3.69 | -40.2% | 27.9% | 329% | 0.66%/yıl |
| **B_rotate_full** (EW_full_aylik) | 17.96% | 4.45 | 15.26% | 4.01 | -43.8% | 29.4% | 372% | 0.74%/yıl |
| **C_chandelier_pit** (EW_pit_aylik) | 6.03% | 1.77 | 2.07% | 0.67 | -32.4% | 25.1% | 340% | 0.68%/yıl |
| **D_rotate_pit** (EW_pit_aylik) | 7.25% | 2.08 | 3.25% | 1.01 | -34.8% | 27.2% | 397% | 0.79%/yıl |

### 1c. Tutuş süresi ve çıkış kanalları
| hücre | kapanan işlem | medyan tutuş | ortalama tutuş | >1 yıl | chandelier çıkış | rotasyon çıkış | bütünlük çıkış | ay/işlem |
|---|---|---|---|---|---|---|---|---|
| A_chandelier_full | 482 | 63g | 80g | 2.5% | 479 | 0 | 3 | 5.2 |
| B_rotate_full | 539 | 41g | 71g | 4.3% | 0 | 535 | 4 | 5.8 |
| C_chandelier_pit | 504 | 63g | 76g | 1.8% | 504 | 0 | 0 | 5.4 |
| D_rotate_pit | 572 | 42g | 67g | 3.1% | 0 | 572 | 0 | 6.2 |

## 2. TABANA (HAM KOL) KARŞI FARK — blok-bootstrap (21 gün, 2000 tekrar)
| hücre | fazla farkı (eşlemeli çıta) | %95 CI | P(fark>0) | vol farkı | P(vol düşük) | maxDD farkı | P(maxDD sığ) |
|---|---|---|---|---|---|---|---|
| B_rotate_full | 1.92 puan/yıl | [-2.66, 6.72] | 0.804 | 1.50 puan | 0.000 | -1.61 puan | 0.340 |
| C_chandelier_pit | -8.91 puan/yıl | [-13.46, -4.37] | 0.000 | -2.79 puan | 1.000 | 1.10 puan | 0.613 |
| D_rotate_pit | -7.43 puan/yıl | [-12.73, -2.36] | 0.002 | -0.72 puan | 0.976 | -0.81 puan | 0.478 |

(maxDD farkı POZİTİF = hücrenin düşüşü ham koldan DAHA SIĞ.)

## 3. RAPOR DİLİMLERİ (K'ya sayılmaz)

### 3a. Alt-dönem fazlası (eşlemeli çıtaya karşı)
| hücre | 2011-2015 | t | 2016-2020 | t | 2021-2026 | t |
|---|---|---|---|---|---|---|
| A_chandelier_full | 17.66% | 3.28 | 15.10% | 2.57 | 15.03% | 1.82 |
| B_rotate_full | 21.02% | 4.41 | 19.77% | 2.91 | 13.99% | 1.70 |
| C_chandelier_pit | 3.87% | 1.03 | 3.15% | 0.57 | 10.78% | 1.45 |
| D_rotate_pit | 7.88% | 1.90 | 3.19% | 0.62 | 10.54% | 1.37 |

### 3b. Yıl-yıl fazla (eşlemeli çıtaya karşı, puan)
| yıl | A_chandelier_full | B_rotate_full | C_chandelier_pit | D_rotate_pit |
|---|---|---|---|---|
| 2010 | — | — | — | — |
| 2011 | 0.1 | 5.8 | -8.5 | -6.6 |
| 2012 | 26.2 | 30.0 | 6.5 | 8.1 |
| 2013 | 20.6 | 25.7 | 6.1 | 18.1 |
| 2014 | 30.7 | 34.2 | 12.1 | 19.4 |
| 2015 | 15.5 | 14.1 | 5.5 | 4.4 |
| 2016 | 5.9 | 2.0 | -4.8 | -7.8 |
| 2017 | 7.0 | -0.9 | -10.3 | -2.0 |
| 2018 | 12.2 | 16.9 | 11.3 | 3.6 |
| 2019 | 15.2 | 24.3 | -3.9 | 9.4 |
| 2020 | 40.6 | 61.2 | 22.7 | 10.8 |
| 2021 | -14.6 | 0.1 | -15.5 | -17.6 |
| 2022 | 17.4 | 15.9 | 15.4 | 21.0 |
| 2023 | 17.0 | 0.4 | 12.5 | 7.0 |
| 2024 | 48.9 | 33.3 | 28.9 | 25.3 |
| 2025 | 0.1 | 1.7 | -2.6 | 0.5 |
| 2026 | 8.9 | 14.9 | 11.6 | 9.8 |

### 3c. 2021+ sessizliği — rejim mi decay mi? (TANI, eşik değil)

Ham kolun (A) fazlası, İKİ ÇITAYA karşı, dönem dönem — ortalama ve DAĞILIM ayrı ayrı:

| dönem | vs TABAN çıta (EW_full_BH, statik) | t | vs EŞLEMELİ çıta (EW_full_aylik) | t | fazla std (yıllık) | pozitif ay |
|---|---|---|---|---|---|---|
| 2011-2015 | 16.26% | 3.16 | 17.66% | 3.28 | 13.4% | 67% |
| 2016-2020 | 13.10% | 2.84 | 15.10% | 2.57 | 13.9% | 63% |
| 2021-2026 | 10.66% | 1.36 | 15.03% | 1.82 | 23.9% | 60% |

**Üç ölçülen olgu:**
1. **Sessizlik büyük ölçüde ÇITA KAYMASI.** Statik B&H çıtasına karşı fazla
   13.10% → 10.66% eriyor; ama
   yapı-eşlemeli (aylık denkleştirilmiş) EW çıtasına karşı
   15.10% → 15.03% — **erime yok**.
   Statik B&H çıtası 15 yılda kendisi de bir kazanan-ağırlıklı portföye dönüşüyor; 2021+ "sessizliğinin"
   bir kısmı kolun zayıflaması değil, ÇITANIN güçlenmesidir.
2. **Ortalama değil DAĞILIM değişti.** Eşlemeli çıtaya karşı fazlanın yıllık std'si
   13.4% → 13.9% →
   23.9%. t'nin düşüşü paydadan geliyor.
3. **Tek kötü yıl.** Yıl-yıl (§3b) fazlanın negatif olduğu yıllar: 2021;
   en kötüsü 2021 (-14.6 puan). Monoton bir erime deseni YOK.

Bu üç olgu **decay'den çok rejim/oynaklık** okumasını destekler; ancak 2021-2026 penceresinde
t=1.82 (n=67 ay) hâlâ ön-kayıt eşiğinin altındadır —
"kanıtlanamadı" durumu sürüyor. Hüküm Rol-1'in.

## 4. PIT KOLU — ÜST SINIR BEYANI

> **PIT kolu bir ÜST SINIRDIR. Üyelik tarihi PIT'tir, FİYATLAR DEĞİLDİR: bar önbelleğinde yalnız BUGÜN yaşayan 250 sembol var. O tarihte S&P500 üyesi olup sonradan delist olan / iflas eden / satın alınan isimler fiyatlanamıyor, dolayısıyla ne kola ne çıtaya giriyor. GERÇEK PIT getirisi bu ölçümden DÜŞÜK olabilir; bu kol yalnızca EVREN-SEÇİM (üyelik) yanlılığını kaldırır, HAYATTA-KALMA (fiyat serisi) yanlılığını KALDIRMAZ.**

| kalem | değer |
|---|---|
| üyelik kaynağı | `/Users/erdemozturk/AI-Trading/research/pit_universe/sp500_uyelik_tarihi.csv` |
| anlık görüntü sayısı / kapsam | 2718 · 1996-01-02 → 2026-06-30 |
| CSV bitişinden sonra ileri taşınan gün | 19 |
| önbellekte olup HİÇ S&P500 üyesi olmayan | 6: BURL, LNG, PINS, ROKU, SNAP, SPOT |
| takma-ad haritası (1-e-1 ad değişimi) | 9 kayıt |
| PIT süzgecinin ELEDİĞİ aday-ay toplamı | 4038 |
| tutulan pozisyon o ay üye değil (ay sayısı) | C: 0 · D: 0 |

**Takma-ad haritası** (haritasız PIT kolu META'yı 2013-2022 arası SAHTE olarak dışlardı):

- `FB` → `META` — Facebook -> Meta ad değişimi; FB 2022-06-08 çıkış, META 2022-06-09 giriş
- `PX` → `LIN` — Praxair -> Linde plc; PX 2018-10-25 çıkış, LIN 2018-11-06 giriş
- `UTX` → `RTX` — United Technologies -> Raytheon Technologies; UTX 2020-03-03 çıkış, RTX 2020-04-03 giriş
- `BHGE` → `BKR` — Baker Hughes a GE co. -> Baker Hughes Co.; BHGE 2019-10-03 çıkış, BKR 2019-10-18 giriş
- `HRS` → `LHX` — Harris -> L3Harris; HRS 2019-04-02 çıkış, LHX 2019-06-01 giriş
- `KRFT` → `KHC` — Kraft Foods -> Kraft Heinz; KRFT 2015-07-02 çıkış, KHC 2015-07-06 giriş
- `DISCA` → `WBD` — Discovery A -> Warner Bros. Discovery; DISCA 2022-04-04 çıkış, WBD 2022-04-11 giriş
- `DISCK` → `WBD` — Discovery C sınıfı — aynı tüzel kişilik
- `ARNC` → `HWM` — Alcoa Inc -> Arconic Inc -> Howmet Aerospace (SÜREKLİ listeleme); ARNC 2020-04-03 çıkış, HWM 2020-04-06 giriş. BELİRSİZLİK: 2016 ayrışması yeni Alcoa'yı (AA) doğurdu; veri kümesi sürekli listelemeyi ARNC diye etiketlemiş.

**Takma-ad duyarlılığı (teşhis):** C haritalı son özkaynak 13,832,419 $ vs
haritasız 13,736,549 $;
D 15,992,642 $ vs
16,067,498 $.
Haritasız fazla (eşlemeli çıta): C 5.98%
(t=1.74),
D 7.25%
(t=2.10) — hüküm haritaya duyarlı DEĞİL.

**PIT süzgecinin en çok elediği adaylar (aday-ay):** MRVL:186, LNG:181, DECK:159, LULU:154, BX:153, STLD:144, KKR:139, BURL:139, PANW:117, APO:116, NXPI:113, TSLA:111, SNAP:98, ROKU:91, TRGP:90

**Üyelik verisinin kendi sınırı (dürüstlük kalemi):** yukarıdaki elenen adayların çoğu doğrulanabilir
endeks katılım tarihleriyle uyumlu (TSLA 2020-12, DECK 2024-03, LULU 2023-10, BX 2023-09, KKR 2024-06,
PANW 2023-06, APO 2024-12, NXPI 2021-03, STLD 2022-12, TRGP 2022-10). İki kalem ölçüm ajanı tarafından
**doğrulanamadı**: `MRVL` (veri kümesinde üyelik yalnız 2026-06-22'den itibaren) ve `LNG`
(veri kümesinde hiç üye değil). Bunlar veri kusuruysa etkinin YÖNÜ bellidir: **sahte dışlama PIT
kolunu AŞAĞI çeker**, yani PIT fazlası bu yönden muhafazakârdır (ölçülen 6.03%/
7.25% bir ALT sınır bileşeni taşır).
Bu, §4 başındaki ÜST SINIR beyanıyla çelişmez: iki yanlılık AYRI katmanlardır (fiyatlanamayan ölü
isimler ↑ yönlü, sahte üyelik dışlaması ↓ yönlü).

### PIT evreninin büyüklüğü (aylık uygun sembol sayısı)

| yıl | PIT evreni | full_251 evreni |
|---|---|---|
| 2010 | 178.0 | 202.0 |
| 2011 | 179.6 | 208.2 |
| 2012 | 183.4 | 211.0 |
| 2013 | 186.8 | 214.7 |
| 2014 | 191.2 | 224.3 |
| 2015 | 197.8 | 227.7 |
| 2016 | 205.1 | 231.8 |
| 2017 | 211.4 | 234.9 |
| 2018 | 214.8 | 236.6 |
| 2019 | 217.2 | 240.0 |
| 2020 | 220.2 | 243.2 |
| 2021 | 227.2 | 246.2 |
| 2022 | 232.7 | 249.0 |
| 2023 | 237.2 | 249.0 |
| 2024 | 240.2 | 249.5 |
| 2025 | 241.5 | 249.8 |
| 2026 | 239.2 | 248.8 |

## 5. MALİYET AYRIŞTIRMA — devir fazlayı yutuyor mu?
| hücre | net fazla (10bps) | brüt fazla (0bps) | maliyetin yediği | CAGR net | CAGR 0bps | friksiyon sürükleme |
|---|---|---|---|---|---|---|
| A_chandelier_full | 15.80% | 16.57% | 0.77 puan | 30.32% | 31.17% | 0.66%/yıl |
| B_rotate_full | 17.96% | 18.86% | 0.90 puan | 32.26% | 33.26% | 0.74%/yıl |
| C_chandelier_pit | 6.03% | 6.76% | 0.73 puan | 18.38% | 19.18% | 0.68%/yıl |
| D_rotate_pit | 7.25% | 8.10% | 0.85 puan | 19.48% | 20.43% | 0.79%/yıl |

## 6. KART ÖLÇÜTLERİNİN OKUNUŞU (hüküm ÖNERİSİ — hükmü Rol-1 işler)

> **ÖLÇÜT OKUMA BELİRSİZLİĞİ:** Kart metni: 'maliyet-sonrası net fazla artar VEYA maxDD/vol anlamlı düşer (P>=0.95)'. (P>=0.95) niteleyicisinin İKİ dala da mı yoksa YALNIZ ikinci dala mı ait olduğu metinden kesin değildir. Ölçüm ajanı eşiği DEĞİŞTİRMEZ ve SEÇMEZ: iki okuma da hesaplanıp raporlanmıştır. Ayrım tek hücrede sonuç değiştiriyor (B_rotate_full).

| rafine hücre | t≥2 (eşlemeli) | bozulma yok | net fazla ↑ | P(artış) | risk ↓ (P≥0.95) | SUCCESS (sıkı) | SUCCESS (lafzî) |
|---|---|---|---|---|---|---|---|
| B_rotate_full | EVET (t=4.45) | EVET (1.92 puan) | EVET | 0.804 | HAYIR (P_vol=0.00, P_dd=0.34) | **HAYIR** | **EVET** |
| C_chandelier_pit | HAYIR (t=1.77) | HAYIR (-8.91 puan) | HAYIR | 0.000 | EVET (P_vol=1.00, P_dd=0.61) | **HAYIR** | **HAYIR** |
| D_rotate_pit | EVET (t=2.08) | HAYIR (-7.43 puan) | HAYIR | 0.002 | EVET (P_vol=0.98, P_dd=0.48) | **HAYIR** | **HAYIR** |

- **success_metric sağlayan hücre(ler)** — sıkı okuma: YOK
  · lafzî okuma: B_rotate_full
- **kill-1** (hiçbir rafine hücre ham kolu geçemiyor → rafine ölür, HAM KOL YAŞAMAYA DEVAM EDER):
  sıkı okumada EVET, lafzî okumada HAYIR
- **kill-2** (PIT kolunda edge kayboldu, t<1 → survivorship-şüphe kaydı AÇILIR): **HAYIR**
  · PIT hücrelerinin KENDİ evreninin EW'sine karşı t: C=1.77,
    D=2.08 → ikisi de t≥1
  · UYARI — çıta seçimine duyarlılık: TABAN çıtasıyla (EW_full_BH) okunsaydı t
    C=0.67, D=1.01 olurdu;
    kill-2 çıta seçimine duyarlı mı: **EVET**. Kart "kendi evreninin
    EW'si" dediği için ölçüm EŞLEMELİ çıtayı esas alır; taban çıtası kolu KENDİ evreni dışındaki bir
    portföyle kıyaslar ve PIT kolu için tanım gereği yanlıdır.
  · kartın "PIT'te t≥2 başlı başına değerli bulgu" koşulu hücre bazında:
    C=HAYIR,
    D=EVET (en az bir hücre: EVET)
- **kill-3** (devir maliyeti fazlayı yutan hücre): YOK
  — aylık-rebalans kolunun devri ham koldan yüksek (372%
  vs 329%) ama maliyet farkı
  0.09 puan/yıl
  düzeyinde kalıyor; fazla farkını (1.92 puan) YUTMUYOR.

**ÖLÇÜM AJANININ HÜKÜM ÖNERİSİ (bağlayıcı değil — Rol-1 işler):**

1. **Şasi geçerli** (pozitif kontrol birebir üretildi) → hücre sayıları okunabilir.
2. **B (aylık-rebalans duraksız × full_251): fazlayı ARTIRIYOR ama RİSK-DÜZELTİLMİŞ İYİLEŞME YOK.**
   Fazla 15.80% → 17.96%
   (+1.92 puan) ama CI sıfırı içeriyor
   (-2.66,
   6.72), vol ARTIYOR
   (27.9% → 29.4%),
   maxDD DERİNLEŞİYOR (-40.2% → -43.8%),
   Sharpe fiilen aynı (1.09 → 1.10).
   Kartın (a) hipotezi — "çıkış mekaniği yalnız maliyet üretir" — **getiri düzeyinde zayıf desteklendi,
   risk-düzeltilmiş düzeyde DESTEKLENMEDİ**: chandelier fazlayı tırpanlıyor ama düşüşü de sığlaştırıyor.
3. **PIT kolu: edge YARIYA İNİYOR ama KAYBOLMUYOR.** Üyelik yanlılığı kaldırıldığında fazla
   C: 15.80% → 6.03%,
   D: 17.96% → 7.25%
   (kayıp: C 9.8 puan/yıl, D 10.7 puan/yıl).
   t: C=1.77, D=2.08.
   kill-2 TETİKLENMİYOR (t<1 değil); kartın "t≥2 değerli bulgu" koşulunu yalnız D karşılıyor.
   **ÖNERİ: survivorship-şüphe kaydı AÇILMASIN, ama ham kolun +13,1p/yıl rakamının yanına
   "evren-seçim yanlılığı düşüldüğünde ~6-7p/yıl" şerhi kalıcı olarak İLİŞTİRİLSİN.**
   · **Yanlılığın ZAMAN DESENİ tanıyı doğruluyor:** PIT ile full arasındaki fazla farkı erken
   dönemde en büyük, geç dönemde kayboluyor — A vs C: 2011-2015
   17.7% vs
   3.9%,
   2021-2026 15.0% vs
   10.8%.
   Beklenen desen tam olarak budur: PIT evreni full evrene yakınsadıkça
   (2011'de 180/208,
   2025'te 242/250 sembol)
   fark kapanır. Yani ham koldaki fazlanın önemli bir kısmı, "bugünün 251'ini 2011'de bilmek"
   avantajıdır — mekanizma değil, evren tanımıdır.
4. **Rafine turu için:** sıkı okumada kill-1 tetikleniyor (rafine ölür, ham kol yaşar); lafzî okumada
   B success sağlıyor. Ölçüm ajanının okuması: **B'yi "yaşayan ama üstünlüğü kanıtlanmamış varyant"
   olarak tutmak**, ham kolu değiştirmemek. Rafine turunun ASIL çıktısı çıkış mekaniği değil,
   PIT bulgusudur (madde 3).

## 7. KAPSAM VE SINIRLAR

- Bar kaynağı: canlı önbellek /Users/erdemozturk/AI-Trading/state/bars (SALT-OKUMA kopyası); kapsam 2004-01-02 → 2026-07-28;
  sim 2010-12-31 → 2026-07-28 (15.57 yıl).
- Evren beyan 251, barı olan 250.
- Deponun kendi kapısı 441 satır düşürdü; ölçüm-içi bütünlük katmanı
  L1 0 satır, L2 15 satır, 97 kırılma işaretledi
  (şablon şasiden AYNEN devralındı — bu turda değiştirilmedi).
- **YAN GÖZLEM (kart dışı, tek satır):** 2026-07-30 ölçümünün BULGU-1'i (deponun hayalet-satır kapısındaki
  hacim şartı gerçek hayalet sınıfının %29'unu kaçırıyor) bu koşumda **artık üretilmiyor**: ölçüm-içi
  L1 katmanı o turda 10 satır yakalarken bu turda 0 satır yakaladı ve depo kapısı
  GILD/CMCSA/DLTR/UNP satırlarını kendisi karantinaya aldı (kapı 441 satır düşürdü,
  o turda 433'tü). Depo kusuru giderilmiş görünüyor; doğrulaması Rol-1'in.
- **Bu ölçümün değmediği:** kapasite/piyasa etkisi (10bps sabit; devir yüksek), vergi, kısa bacak,
  sektör yoğunlaşması, delist/iflas eden isimlerin fiyat serileri (PIT üst sınırının kaynağı),
  ve N=10 dışındaki slot sayıları (kart N'i sabitlemiştir).