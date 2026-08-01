# WP2 ÖLÇÜM DALGASI — EDG-2026-012 / -013 / -014

- Ölçüm: `2026-08-01T10:49:43.240471+00:00` · sandbox `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/wp2_olcum`
- Repo HEAD: `db94dc70be76e1f220ce99107c556817eb66fc0f` · Python 3.12.7
- Rol: ölçüm ajanı — KART DOKUNULMADI, hüküm ÖNERİDİR (hükmü Rol-1 işler)
- Üç kart **AYRI AİLEDİR**: birinin hükmü diğerini etkilemez. Ortak olan tek şey aşağıdaki boru-hattı bekçisidir.

## 0. Boru hattı bekçisi (İLK KOŞAN İŞ)

**Pozitif kontrol** — ham `rvol20` @20 cf-katman IC: **0.0642** (hedef 0.0645, tolerans 0.005, sapma 0.0003) → **GEÇTİ=True**  ·  n=2087, CI {'lo': 0.0061, 'hi': 0.1071, 'seviye': 0.95}
- @5 IC 0.0374 (CI {'lo': -0.0193, 'hi': 0.0791, 'seviye': 0.95}), @10 IC 0.0516 (CI {'lo': -0.0119, 'hi': 0.0996, 'seviye': 0.95})
- defterdeki referans (`state/component_ic.json`, cf/rvol20): {'5': 0.032, '10': 0.0456, '20': 0.0604}
- katman: counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı); eşleşme: {'bar_yok_sembol': 45, 'bar_yok_tarih': 0, 'kabul': 7077}

**PK4 (yol tutarlılığı)** — GEÇTİ=True. fwd5: n=1258029, maks|fark|=0.0; fwd10: n=1256766, maks|fark|=0.0; fwd20: n=1254248, maks|fark|=0.0; fwd60: n=1237364, maks|fark|=0.0

**PK5 (özdeşlikler)** — GEÇTİ=True
- `A_asof_geriye_bakissizlik`: n_ornek=500, ayrisan=0, filed>t_sizinti=0, gecti=True
- `B_split_bazi`: n_ornek=3729, ayrisan=0, gecti=True
- `C_hizli_ortalama`: n_ornek=50, maks_mutlak_fark=0.0, gecti=True
- `D_fundamentals_asof`: n_ornek=1160, filed>t_sizinti=0, gecti=True

**Brief'in bar-tabanlı split yolu bu veride YOK.** Bilinen bölünme günlerinde bar serisinde sıçrama gözlenmedi (seri split-DÜZELTİLMİŞ):

| sembol | bölünme günü | o günün getirisi | hacim oranı |
|---|---|---|---|
| NVDA | 2024-06-10 | +0.745% | 0.761817 |
| AVGO | 2024-07-15 | +0.794% | 0.755236 |
| AAPL | 2020-08-31 | +3.389% | 0.604427 |
| TSLA | 2022-08-25 | -0.347% | 0.929624 |
| GOOGL | 2022-07-18 | -2.460% | 0.922929 |

Bilinen bölünme günlerinde bar serisinde ~%90 fiyat düşüşü YOK — state/bars SPLIT-DÜZELTİLMİŞ. Yani 'bar verisindeki split günleri' bu veri kümesinde OKUNAMAZ; split takvimi EDGAR'ın kendi geriye-dönük yeniden-beyanından türetildi (ortak.build_split_takvimi belgesi).

## 0b. Ortak as-of altyapısı (012 ve 013 aynı nesneyi kullanır)

- Anlık hisse serisi olan sembol: 252 (birincil dei 244, birincil us-gaap 8); evrende serisi OLMAYAN: ['EL', 'HRL', 'META', 'MKC', 'STZ', 'TSN'] (çok-sınıflı kapak sayısı boyutlu → companyfacts taşımıyor)
- `val<=0` / birim filtresiyle düşen ham satır: 76
- Yedek etiketten doldurulan boşluk kaydı: 22
- **Split takvimi**: 169 aday sıçrama tarandı → 74 bölünme kabul (58 sembolde); temiz orana oturmayan 68, yeniden-beyan kanıtı olmayan 27
- Açıklanamayan ≥5.0× sınır (kart kuralı): 51 · ölçek-hatası gidiş-dönüş penceresi: 24
- Kanıt yalnız anlık etiketlerden toplansaydı kabul sayısı 64 olurdu (tam kanıtla 74); iki takvim aynı mı: False — ağırlıklı-ortalama etiketleri YALNIZ bölünme KANITI olarak okundu, seviye olarak ASLA.
- **Fiziksel ölçek bekçisi** (veri kalitesi, sinyal eşiği DEĞİL): implied medyan-21g devir hızı > 1.0 olan 7 as-of kaydı geçersiz — {'BKR': 100.0, 'CSX': 3.0, 'ETN': 100.0, 'LIN': 25000.0, 'ROKU': 4818812.0, 'SPG': 8000.0} (dosyalayan kabuk/ölçek hatası: 3, 100, 8.000, 25.000 hisse)

**Split normalizasyonu doğrulaması** (brief'in istediği NVDA/AVGO sınavı) — güncel baza çevrilmiş as-of hisse sayımı bölünmenin ÜZERİNDEN pürüzsüz geçmelidir; ham EDGAR serisi ise sıçrar. PK5-B baz çarpanını ayrıca cebirsel olarak da doğruluyor.

| sembol | kabul edilen bölünme(ler) | B_son |
|---|---|---|
| NVDA | 2021-08-20 ×4 (ham 4.012841); 2024-08-28 ×10 (ham 9.971545) | 40.0 |
| AVGO | 2024-09-11 ×10 (ham 10.033712) | 10.0 |
| AAPL | 2014-07-23 ×7 (ham 6.951473); 2020-10-30 ×4 (ham 3.97644) | 28.0 |
| GOOGL | 2022-07-27 ×20 (ham 19.85236) | 20.0 |
| TSLA | 2020-10-26 ×5 (ham 5.086349); 2022-10-24 ×3 (ham 3.023248) | 15.0 |
| WMT | 2024-03-15 ×3 (ham 2.993072) | 3.0 |
| NFLX | 2015-07-17 ×7 (ham 7.02738); 2026-01-23 ×10 (ham 9.96422) | 70.0 |

| sembol | seri | 2013-06-03 | 2015-06-01 | 2019-06-03 | 2021-06-01 | 2023-06-01 | 2024-06-03 | 2024-09-03 | 2025-06-02 | 2026-06-01 |
|---|---|---|---|---|---|---|---|---|---|---|
| NVDA | güncel baz | 2.312e+10 | 2.15e+10 | 2.436e+10 | 2.492e+10 | 2.47e+10 | 2.46e+10 | 2.453e+10 | 2.44e+10 | 2.42e+10 |
| NVDA | ham EDGAR | 5.779e+08 | 5.376e+08 | 6.09e+08 | 6.23e+08 | 2.47e+09 | 2.46e+09 | 2.453e+10 | 2.44e+10 | 2.42e+10 |
| AVGO | güncel baz | — | — | 3.958e+09 | 4.083e+09 | 4.169e+09 | 4.634e+09 | 4.655e+09 | 4.702e+09 | 4.735e+09 |
| AVGO | ham EDGAR | — | — | 3.958e+08 | 4.083e+08 | 4.169e+08 | 4.634e+08 | 4.655e+08 | 4.702e+09 | 4.735e+09 |
| AAPL | güncel baz | 2.628e+10 | 2.304e+10 | 1.84e+10 | 1.669e+10 | 1.573e+10 | 1.533e+10 | 1.52e+10 | 1.494e+10 | 1.469e+10 |
| AAPL | ham EDGAR | 9.386e+08 | 5.761e+09 | 4.601e+09 | 1.669e+10 | 1.573e+10 | 1.533e+10 | 1.52e+10 | 1.494e+10 | 1.469e+10 |
| GOOGL | güncel baz | — | — | 1.39e+10 | 1.342e+10 | 1.272e+10 | 1.238e+10 | 1.232e+10 | 1.216e+10 | 1.212e+10 |
| GOOGL | ham EDGAR | — | — | 6.948e+08 | 6.711e+08 | 1.272e+10 | 1.238e+10 | 1.232e+10 | 1.216e+10 | 1.212e+10 |
| TSLA | güncel baz | 1.733e+09 | 1.896e+09 | 2.606e+09 | 2.88e+09 | 3.17e+09 | 3.189e+09 | 3.195e+09 | 3.217e+09 | 3.752e+09 |
| TSLA | ham EDGAR | 1.156e+08 | 1.264e+08 | 1.737e+08 | 9.599e+08 | 3.17e+09 | 3.189e+09 | 3.195e+09 | 3.217e+09 | 3.752e+09 |
| WMT | güncel baz | 9.877e+09 | 9.678e+09 | 8.609e+09 | 8.451e+09 | 8.087e+09 | 8.058e+09 | 8.038e+09 | 8.017e+09 | 7.958e+09 |
| WMT | ham EDGAR | 3.292e+09 | 3.226e+09 | 2.87e+09 | 2.817e+09 | 2.696e+09 | 8.058e+09 | 8.038e+09 | 8.017e+09 | 7.958e+09 |
| NFLX | güncel baz | 3.93e+09 | 4.243e+09 | 4.372e+09 | 4.434e+09 | 4.445e+09 | 4.31e+09 | 4.292e+09 | 4.257e+09 | 4.213e+09 |
| NFLX | ham EDGAR | 5.614e+07 | 6.062e+07 | 4.372e+08 | 4.434e+08 | 4.445e+08 | 4.31e+08 | 4.292e+08 | 4.257e+08 | 4.213e+09 |

## 1. EDG-2026-012 · net hisse ihracı (`net_share_issuance`)

### (i) Örneklem / kapsam

- Gözlem günü: 259 · kesiti yeterli (>= 50 sembol) gün: 191 · kesit medyanı 208.0 (min 3, maks 231)
- Tarih aralığı: 2010-04-30 → 2026-07-29
- **Örneklem kapısı**: geçerli sembol-ay 39084 (kart eşiği 3000) → yeterli=True
- Ölçülemeyen hücrelerin nedenleri: `{"t-252_asof_yok:dosyalama_yok": 2515, "t_asof_yok:dosyalama_yok": 11077, "aciklanamayan_5x_sinir": 128, "t-252_asof_yok:olcek_hatasi_gidis_donus": 58, "t_asof_yok:olcek_hatasi_gidis_donus": 92, "anlik_hisse_serisi_yok": 1425, "t-252_asof_yok:bayat_seri": 113, "t_asof_yok:bayat_seri": 1885, "t-252_asof_yok:olcek_hatasi_fiziksel_imkansiz": 30, "t_asof_yok:olcek_hatasi_fiziksel_imkansiz": 235}`
- **filed gecikmesi** (gözlem günü − kullanılan kaydın filed'ı): n=39212, medyan 43.0g, p10 6.0g, p90 87.0g, maks 200.0g, negatif 0 (negatif = PIT ihlali olurdu)

- net_ihrac dağılımı (kesit): `{"0.01": -0.115314, "0.05": -0.069845, "0.2": -0.032482, "0.5": -0.004289, "0.8": 0.010094, "0.95": 0.089429, "0.99": 0.419148}`

### (ii) Dilim tablosu — aynı-gün EVREN tabanına göre FAZLA

| dilim / ufuk | n | fazla ort. | %95 CI (21 ay blok) | hüküm |
|---|---|---|---|---|
| ihrac_ust_20pct @20g | 7839 | +0.348% | [+0.104%, +0.569%] | ANLAMLI |
| ihrac_ust_20pct @60g | 7784 | +1.039% | [+0.331%, +1.670%] | ANLAMLI |
| gerialim_alt_20pct @20g | 7686 | +0.139% | [-0.101%, +0.315%] | CI 0 içi |
| gerialim_alt_20pct @60g | 7630 | +0.295% | [-0.306%, +0.722%] | CI 0 içi |

Ham (tabansız) ortalamalar ve dar bloklu (3 ay) CI'lar `sonuc.json`'da; **3 aylık blok hiçbir bacağın işaretini değiştirmiyor**.

- `ihrac_ust_20pct`: 7878 sembol-ay, 176 sembol, 191 gün; dilim içi net_ihrac ort. +9.49%, medyan +3.29%
- `gerialim_alt_20pct`: 7722 sembol-ay, 176 sembol, 191 gün; dilim içi net_ihrac ort. -6.02%, medyan -5.10%

**Yayılım (geri-alım − ihraç, TANI):** @20g -0.206% CI [-0.602%, +0.178%] (CI 0 içi); @60g -0.739% CI [-1.844%, +0.309%] (CI 0 içi)

**Beşli dilim (TANI, CI YOK — K harcanmaz; 0 = en çok geri-alan, 4 = en çok ihraç eden):**

| ufuk | q0 | q1 | q2 | q3 | q4 |
|---|---|---|---|---|---|
| @20g | +0.147% | -0.112% | -0.263% | -0.177% | +0.345% |
| @60g | +0.291% | -0.251% | -0.793% | -0.423% | +1.056% |

**İhraç diliminde en sık görülen semboller (TANI):** O(176), WELL(173), EQIX(170), DLR(168), TSLA(167), MPWR(155), NOW(146), CRM(138), BX(133), KKR(130), AMZN(128), ENPH(126), PANW(125), TTWO(124), MCHP(123)

### (iii) Hüküm ÖNERİSİ

- Kart ölçütü: *ihraç-dilimi fazlası @60 anlamlı NEGATİF VEYA geri-alım-dilimi fazlası @60 anlamlı POZİTİF (CI 0-dışı) VE yön literatürle tutarlı*
- success karşılandı: **hayır** · kill#1 (iki uç da CI-0-içi): hayır · kill#2 (yön TERS ve anlamlı): **EVET** · kill#3 (örneklem): hayır
- **ÖNERİ: ARŞİV — kill#2 (yön literatürün TERSİ ve anlamlı; 'bu evrende ters' notu)**

## 2. EDG-2026-013 · kısa-dönem momentum × turnover

### (i) Örneklem / kapsam

- Gözlem günü: 5678 · kesiti yeterli (>= 50 sembol) gün: 4271 · kesit medyanı 210.0 (min 1, maks 232)
- Tarih aralığı: 2009-08-04 → 2026-07-28
- Ölçülemeyen hücrelerin nedenleri: `{"dosyalama_yok": 573996, "olcek_hatasi_gidis_donus": 1884, "anlik_hisse_serisi_yok": 31447, "bayat_seri": 40002, "olcek_hatasi_fiziksel_imkansiz": 5237}`

- turnover21 dağılımı: `{"0.01": 0.001924, "0.25": 0.004442, "0.5": 0.006067, "0.75": 0.008949, "0.99": 0.050849}` · mom21 dağılımı: `{"0.01": -0.215737, "0.25": -0.034033, "0.5": 0.01275, "0.75": 0.058594, "0.99": 0.268551}`
- **Akrabalık beyanı (kart guard)**: Spearman(turnover21, rvol20) = -0.077113 (gün-içi ortalama -0.084163); Spearman(turnover21, mom21) = -0.00853. Yani turnover, skorda ZATEN olan rvol20'nin kılık değiştirmiş hâli DEĞİL (ilişki zayıf ve NEGATİF).

### (ii) Katman tablosu — aynı-gün evren tabanına göre FAZLA

| katman / ufuk | n | fazla ort. | %95 CI (21 işlem günü blok) | hüküm |
|---|---|---|---|---|
| mom_ust20_kosulsuz @10g | 178493 | +0.010% | [-0.106%, +0.134%] | CI 0 içi |
| mom_ust20_kosulsuz @20g | 178024 | +0.011% | [-0.202%, +0.251%] | CI 0 içi |
| mom_ust20_turnover_ustu @10g | 112338 | +0.149% | [-0.003%, +0.325%] | CI 0 içi |
| mom_ust20_turnover_ustu @20g | 112087 | +0.315% | [+0.040%, +0.613%] | ANLAMLI |

**ARTIMLILIK (koşullu − koşulsuz, eşleştirilmiş gün blokları):**

| ufuk | fark | %95 CI | hüküm |
|---|---|---|---|
| @10g | +0.139% | [+0.062%, +0.215%] | ANLAMLI POZİTİF |
| @20g | +0.305% | [+0.173%, +0.449%] | ANLAMLI POZİTİF |

**TANI dilimleri (hüküm bacağı DEĞİL):**

| tanı | @10g | @20g |
|---|---|---|
| mom üst%20 ∧ turnover ALTI (kayıtlı dilimlerin tümleyeni, CI okunabilir) | -0.226% CI [-0.376%, -0.073%] | -0.507% CI [-0.807%, -0.226%] |
| mom üst%20, koşulsuz, TAM evren (kapsam kontrolü) | +0.010% | +0.036% |

**turnover ANA ETKİSİ — momentum koşulu YOK, tüm kesit (CI BİLEREK yok: kartın grid'inde olmayan dilim, CI'lı sınansa K çarpılırdı):**

| ufuk | q0 (en düşük TO) | q1 | q2 | q3 | q4 (en yüksek TO) |
|---|---|---|---|---|---|
| @10g | -0.197% | -0.164% | -0.034% | +0.059% | +0.312% |
| @20g | -0.407% | -0.319% | -0.104% | +0.144% | +0.651% |

### (iii) Hüküm ÖNERİSİ

- Kart ölçütü: *turnover-koşullu mom diliminin fazlası @10 VEYA @20 anlamlı POZİTİF VE koşulsuz mom fazlasını anlamlı AŞIYOR (artımlılık)*
- bacak1 (koşullu dilim @10 VEYA @20 anlamlı POZİTİF): **EVET** · bacak2 (artımlılık anlamlı POZİTİF): **EVET** · iki bacak AYNI ufukta: **EVET**
- kill#1 (koşullu CI-0-içi): hayır · kill#2 (artımlılık yok): hayır · kill#3 (reversal): hayır
- **ÖNERİ: SUCCESS — kart ölçütü karşılandı**

## 3. EDG-2026-014 · brüt kârlılık (GP/Assets)

### (i) Örneklem / kapsam

- Gözlem günü: 271 · kesiti yeterli (>= 50 sembol) gün: 191 · kesit medyanı 103.0 (min 1, maks 162)
- Tarih aralığı: 2010-08-31 → 2026-06-30
- **Örneklem kapısı**: geçerli sembol-ay 23272 (kart eşiği 2500) → yeterli=True
- Ölçülemeyen hücrelerin nedenleri: `{"FY_dosyalama_yok": 16360, "bayat_FY_serisi": 2109, "GP_hesaplanamayan_sembol": 17877}`
- **filed gecikmesi** (gözlem günü − kullanılan kaydın filed'ı): n=23272, medyan 169.0g, p10 32.0g, p90 325.0g, maks 550.0g, negatif 0 (negatif = PIT ihlali olurdu)

- GP alt-kümesi: 173 sembol (README §3 F∧G evrende 184; aradaki 11 sembol: ['DD', 'DE', 'HON', 'INTU', 'KR', 'MCD', 'NEM', 'RTX', 'SO', 'TMO', 'TMUS'] — README kapsamı 'etiket var mı' sorusunu sorar; bu ölçüm ek olarak FY (donem_turu=='yillik') VE aynı dosyalamada Assets VE val>0 ister. Aradaki semboller bu üç şarttan birini sağlamıyor.)
- Yıl başına kesit: `{"2009": 6, "2010": 60, "2011": 87, "2012": 90, "2013": 94, "2014": 94, "2015": 101, "2016": 101, "2017": 103, "2018": 109, "2019": 155, "2020": 162, "2021": 158, "2022": 152, "2023": 148, "2024": 150, "2025": 150, "2026": 150}`
- gp kaynağı (hücre): `{"GrossProfit": 15494, "Revenues-CostOfRevenue": 1953, "RevenueFromContractWithCustomerExcludingAssessedTax-CostOfRevenue": 720, "RevenueFromContractWithCustomerExcludingAssessedTax-CostOfGoodsAndServicesSold": 1847, "Revenues-CostOfGoodsAndServicesSold": 2977, "RevenueFromContractWithCustomerIncludingAssessedTax-CostOfGoodsAndServicesSold": 180, "RevenueFromContractWithCustomerIncludingAssessedTax-CostOfRevenue": 101}`
- Assets eşleşmesi: aynı dosyalama+aynı end 4968, aynı dosyalama+yakın end 1, eşleşmeyen (DÜŞÜRÜLDÜ) 1509
- `val<=0` nedeniyle düşen GrossProfit satırı: 64 · AFN birimli satır: 1 (MPWR)
- gpa dağılımı: `{"0.01": 0.025543, "0.1": 0.121211, "0.3": 0.214129, "0.5": 0.311183, "0.7": 0.414526, "0.9": 0.588723, "0.99": 0.974928}` · sektör dağılımı: `{"tech": 28, "health": 25, "staples": 25, "consumer": 23, "industrials": 17, "materials": 15, "energy": 14, "comms": 14, "reits": 7, "utilities": 4, "financials": 1}`

### (ii) Dilim tablosu — aynı-gün **GP-alt-kümesi** tabanına göre FAZLA

| dilim / ufuk | n | fazla ort. | %95 CI (21 ay blok) | hüküm |
|---|---|---|---|---|
| gpa_ust_30pct @20g | 6942 | -0.013% | [-0.223%, +0.293%] | CI 0 içi |
| gpa_ust_30pct @60g | 6883 | -0.128% | [-0.807%, +0.809%] | CI 0 içi |
| gpa_alt_30pct @20g | 6772 | +0.012% | [-0.380%, +0.292%] | CI 0 içi |
| gpa_alt_30pct @60g | 6721 | +0.198% | [-1.073%, +1.102%] | CI 0 içi |

**YAYILIM (üst − alt, monotonluk kanıtı — kartın İKİNCİ bacağı):**

| ufuk | yayılım | %95 CI | hüküm |
|---|---|---|---|
| @20g | -0.025% | [-0.522%, +0.625%] | CI 0 içi |
| @60g | -0.326% | [-1.820%, +1.693%] | CI 0 içi |

**Beşli dilim (TANI, CI YOK; 0 = en düşük gpa, 4 = en yüksek):**

| ufuk | q0 | q1 | q2 | q3 | q4 |
|---|---|---|---|---|---|
| @20g | -0.030% | +0.060% | -0.099% | +0.225% | -0.152% |
| @60g | +0.176% | +0.011% | -0.291% | +0.632% | -0.521% |

**Sektör duyarlılığı (kart guard — TANI, eşik DEĞİL):** finans-dışı alt-küme 165 sembol; GP alt-kümesinde kalan finans/REIT sembolleri: ['AMT', 'C', 'CBRE', 'CCI', 'EQIX', 'EQR', 'PSA', 'WELL']

| finans-dışı dilim / ufuk | n | fazla ort. | %95 CI | hüküm |
|---|---|---|---|---|
| gpa_ust_30pct_FINANSDISI @20g | 6765 | -0.029% | [-0.242%, +0.264%] | CI 0 içi |
| gpa_ust_30pct_FINANSDISI @60g | 6707 | -0.164% | [-0.799%, +0.787%] | CI 0 içi |
| gpa_alt_30pct_FINANSDISI @20g | 6574 | +0.064% | [-0.351%, +0.381%] | CI 0 içi |
| gpa_alt_30pct_FINANSDISI @60g | 6525 | +0.289% | [-0.920%, +1.204%] | CI 0 içi |

Finans-dışı yayılım: @20g -0.092% CI [-0.590%, +0.570%]; @60g -0.454% CI [-2.016%, +1.714%]

### (iii) Hüküm ÖNERİSİ

- Kart ölçütü: *üst-dilim fazlası @60 anlamlı POZİTİF (CI 0-dışı; @20 destekleyici) VE üst−alt yayılımı pozitif anlamlı*
- bacak1 (üst dilim @60 anlamlı POZİTİF): **hayır** · bacak2 (yayılım @60 anlamlı POZİTİF): **hayır**
- kill#1 (üst+yayılım @20 ve @60 CI-0-içi): **EVET** · kill#2 (yön ters-anlamlı): hayır · kill#3 (örneklem): hayır
- **ÖNERİ: ARŞİV — kill#1 (üst dilim ve yayılım @20+@60 CI-0-içi, bilgisiz)**

## 4. Veri tuzakları ve hükmü okurken bilinmesi gerekenler

Bunlar **gözlem**dir; hiçbiri hükmü değiştirmedi, hükmü Rol-1 işler.

**T1 — Bar serisi split-düzeltilmiş; bölünme takvimi bar verisinden ÇIKARILAMIYOR.** Brief'in önerdiği yol bu veri kümesinde yok (§0). Takvim EDGAR'ın kendi geriye-dönük yeniden-beyanından kuruldu: 74 bölünme kabul, 27 sıçrama 'temiz orana oturdu ama yeniden-beyan kanıtı yok' diye REDDEDİLDİ. Reddedilenlerin çoğu birleşme kaynaklı GERÇEK ihraçtır (MRK/Schering 2009, RTX/UTC 2020, PLD/AMB 2011, O/VEREIT 2022, NEM/Goldcorp 2019, OMC/IPG 2026) — bölünme sayılsalardı gerçek ihraç silinirdi.

**T2 — Dosyalayan ölçek/kabuk hataları kapak sayfasında yaşıyor.** İki ayrı desen: (a) 1000×/10⁶× GİDİŞ-DÖNÜŞ (24 pencere: ON, ORCL, PKG, PSA, QCOM, SWKS, AEP, CLX, EXC, MAR, CB, AMD, CRM); (b) yeni kayıtçının KABUK sayısı — serinin başında tek yönlü, dönüşü yok (7 kayıt: CSX=3, ETN=100, BKR=100, SPG=8.000, LIN=25.000 hisse). (b) kartın ≥5× kuralıyla YAKALANAMAZ (sıçramanın hangi tarafının bozuk olduğunu söylemez ve seri başında karşı sıçrama yoktur); fiziksel bekçi bunun için eklendi ve beyan edildi. Bekçi olmasaydı 013'ün devir hızı kuyruğunda 10⁴ mertebesinde uydurma değerler kalırdı.

**T3 — MLM 2015-02-24 10-K kapak sayfası bir önceki yılın hisse adedini KOPYALAMIŞ** (46.158.811 iki yıl üst üste); aynı dosyalamadaki us-gaap bilanço sayısı doğru (67.293.000). Oran 0,69 olduğu için kartın 5× kuralına takılmaz. **WFC 2023-08-01** 10-Q'da dei=1,82 Mr, üç gün sonra 10-Q/A ile 3,66 Mr'a düzeltilmiş. İkisi de tek çeyreklik, sembol düzeyinde sınırlı; düzeltilmedi, beyan edildi.

**T4 — SCHW'de dei serisinde 4,5 yıllık boşluk var** (2020-08-07 → 2025-02-26). Bayatlık bekçisi (200 gün) olmasaydı 2020 sayısı 2025'e kadar taşınırdı. Aynı bekçi Citigroup'un companyfacts gecikmesini de (tutarsizlik.json #6) kapatıyor.

**T5 — 012'nin işareti bir SEVİYE etkisi değil, bir U eğrisi.** Beşli dilim tablosunda hem en çok geri-alan hem en çok ihraç eden uç, ORTA dilimlerin üstünde. Yani 'ihraç edenler kazanıyor' okuması eksik; monoton bir ilişki YOK. Ayrıca ihraç dilimi bileşimi REIT (O, WELL, EQIX, DLR) ve yüksek-büyüme teknoloji (TSLA, NOW, CRM, PANW) ağırlıklı — ikisi de yapısal olarak hisse ihraç eder ve bu örneklemde iyi getirmiştir.

**T6 — Evren HAYATTA KALANLARDAN oluşuyor.** Kartların `universe: full_251` metnine sadık kalındı; RETIRED_SYMBOLS (8 delist) DIŞARIDA. Ağır ihraç edip batan/çıkarılan şirketler örneklemde yok, bu 012'nin ihraç-dilimini YUKARI çarpıtır. Bu, kill#2 işaretinin en olası yapısal açıklamasıdır ve ölçümle ayrıştırılamaz.

**T7 — 013 SUCCESS'i muhtemelen turnover'ın ANA etkisidir, momentum×turnover ETKİLEŞİMİ değil.** Kartın kayıtlı ölçütü harfiyen karşılandı; ama kartın grid'inde olmayan tanı tablosu şunu gösteriyor: momentum koşulu HİÇ kullanılmadan, yalnız turnover en üst beşte birinin @20 fazlası +0.651% — koşullu momentum diliminin fazlasından (+0.315%) BÜYÜK; ve turnover dilimleri boyunca ilişki MONOTON. Koşulsuz momentum diliminin fazlası ise sıfırdan ayrışmıyor. Yani turnover tek başına bir sıralayıcı gibi davranıyor; 'kısa momentum yüksek turnover'da güçlenir' tezi bu ölçümle DOĞRULANMIŞ SAYILMAZ. Ayrım için turnover'ın KENDİ kartı gerekir (bu turda CI'lı sınanmadı — K çarpılmasın diye).

**T8 — 013'ün kazancı maliyet ölçeğinde ince.** Koşullu dilim @20 brüt +0.315%, 10bps tek-yön düşülünce +0.215%; @10'da brüt +0.149%, maliyet sonrası +0.049%. Kart maliyeti success ölçütüne koymamış; hüküm brüt üzerinden verildi, bu satır uyarıdır.

**T9 — 014'ün evreni hem dar hem ZAMANLA BÜYÜYOR.** Kesit 2010'da 60, 2020'de 162 sembol; büyük sıçrama 2018→2019'da RevenueFromContractWithCustomer etiketlerinin yaygınlaşmasıyla oluyor. 'Bilgisiz' hükmü bu dar ve dönem-boyunca-değişen kesitte okunmalı.

**T10 — 014'te `val<=0` kuralı asimetrik davranıyor.** Kart 'val<=0 düşülür' diyor; bu, NEGATİF brüt kâr bildiren 64 `GrossProfit` satırını da düşürüyor, oysa gelir−maliyet YOLUYLA hesaplanan negatif brüt kâr düşmüyor. Kart metnine harfiyen uyuldu, sapma beyan edildi.

**T11 — 014'te Assets eşleşmesi 1509 FY akış gözlemini düşürdü.** Kart 'assets(t) aynı filed'dan' diyor; başka bir dosyalamaya düşmek kart metnine aykırı olurdu, o yüzden eşleşmeyen gözlem UYDURULMADI, DÜŞÜRÜLDÜ. README §3'ün 184 sembollük kapsamı ile bu ölçümün 173 sembolü arasındaki fark buradan geliyor.

**T12 — Aylık panellerde blok uzunluğu kartın yazdığından GENİŞ.** Kart '21g blok' diyor; aylık gözlemde 21 ardışık gözlem günü = 21 AY, yani 60g örtüşmesinin gerektirdiğinden çok daha muhafazakâr. Örtüşmeye denk 3 aylık blok da hesaplandı; işareti/anlamlılığı DEĞİŞEN bacak sayısı: **0** (yok) (`sonuc.json` → `*_blok3`). Yani 012'nin kill#2'si ve 014'ün kill#1'i blok seçimine dayanmıyor.

## 5. Kod damgası / üretilebilirlik

- repo HEAD `db94dc70be76e1f220ce99107c556817eb66fc0f`
- ölçüm kodu sha256:
  - `birlestir.py` `33db94ec21aeea6d1d503516413ffa86fb6e9d97de925237bdb8bd1eee575f4f`
  - `k012.py` `832b1b9bbf6b4de873f439d0495b340ef16807133086a7f9eb5eecce80fc5ed1`
  - `k013.py` `082822aa22a28c519e154d85aea18db51a4851bc8325365d9f3bf6be5a4ec99e`
  - `k014.py` `a02dda53ecf1dc27ff9d7584d74c4ad72b9184afae19405bc7ea0d714ac46696`
  - `ortak.py` `8b274c5645838eb5fe11bbdd065703639c0917dac5a27059656c2f5572e94442`
  - `pk.py` `25c1221ef0758fd2f99f517423ea6b2501e67c550a75abc92544be3737ba0af6`
  - `rapor.py` `4455f4c2794fe6c46fa7fc96b7a6fdc0d41f93ba14c87920ce3c1c80743cbae1`
- girdi sha256:
  - `research/edgar_facts/shares_outstanding.csv.gz` `446f7bf00a227c586697f0a9669e82dc85abbb9504d67df45e4b695a03d998a3`
  - `research/edgar_facts/fundamentals.csv.gz` `626bba1a61b527e2d64bb19bbf10682ce34ee0bd765ac7862450c5a1ad6778b2`
  - `research/edgar_facts/tutarsizlik.json` `1bd10c16127bede4bbf7c7b21fe80a4279cfa378f84ceea8a093b34c9cf6dda8`
  - `state/bars_integrity.json` `ab6b2e5995ba3084782cbcedc2982a7d56d0d16a6245cadff14e74e5edfdedcc`
  - `state/counterfactuals.jsonl` `df479477d73c9f7998bebc368e505cb0ed77677c676719782b907199eb771f09`
  - `state/cf_open.json` `fea01ce5696cf8d593800d0e9cc9af25617b4a46338f701bbd0ade99f49a6189`
- **kart dosyaları (ajan DOKUNMADI)**:
  - `EDG-2026-012-net-issuance.yaml` `3e716253b337db6296169ec360fc50294dca1496b323853383befc04bdcafbec`
  - `EDG-2026-013-mom-turnover.yaml` `0e223e6d3db9ede06c29d52f45e5c48d0acc6c2ad89310f7d47b78384dbf9f42`
  - `EDG-2026-014-gross-profitability.yaml` `ff864dc1e3cb6b89b7d452c466be854d1c1905cd944ba40b87d70500902a291e`

Dosyalar: `sonuc.json` (üç kart ayrı blok) · `sonuc_012.json` · `sonuc_013.json` · `sonuc_014.json` · `pk.json` · `kod_damgasi.json` · `panel_012.csv.gz` · `panel_014.csv.gz` · `RAPOR.md` · kod: `ortak.py`, `pk.py`, `k012.py`, `k013.py`, `k014.py`, `birlestir.py`, `rapor.py`.
