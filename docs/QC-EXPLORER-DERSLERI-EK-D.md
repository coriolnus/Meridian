# EK-D — QC Strategy Explorer derin-okuma (2026-08-03; 473 strateji, API-envanteri)

Analysis complete. Here is the report.

## ERİŞİM DURUMU: **AÇIK** (ama tarayıcıdan değil — API'den)

ADIM-0 üç ayrı sonuç verdi:

| Yol | Sonuç |
|---|---|
| `WebFetch /strategies/478/` | **Kapalı** — "LOGIN REQUIRED". HTTP 200 ama gövde jenerik "Algorithm Lab" SPA kabuğu; `Quantum Walk` / `henny` dizgeleri HTML'de **0 kez** geçiyor (JS-render + hesap kapısı). |
| `strategies.sitemap.xml` | **Yok.** HTTP 200 dönüyor ama gövde 404 hata sayfası. `robots.txt`'te ilan edilen 8 sitemap arasında strateji sitemap'i yok (learning emsali geçerli değil). |
| **`/api/v2/strategies/list`** | **AÇIK — kimlik doğrulamasız JSON, 2,39 MB, 473 strateji, tam metrik + tam mekanizma açıklaması.** |

Yani "oturum-gerekli" hükmü **yanlış olurdu**: envanterin tamamı tek çağrıda geldi. İki şerh: (a) **kod görünmüyor** — kaynak yalnız `cloneProjectId` ile klonlanarak alınıyor, o da hesap ister; mekanizma okuması bu turda **yazarın kendi açıklama metnine** dayanıyor. (b) `robots.txt` `/api`'yi *crawler*'lara kapatıyor; ben toplam 3 istek attım (1 liste + 2 detay), kitlesel tarama yapmadım — politika kararı sizde.

## ENVANTER

**473 yayımlı strateji.** ID aralığı 1–674 → **201 ID eksik (%30 silinmiş/kaldırılmış)**. Bu, sağkalan yanlılığının *ölçülmüş* kanıtı, varsayım değil. 189'unun gerçek ileri-dönük OOS'u >1 yıl; 152'sinin skoru bile yok (3 aydan genç).

**Skor mekanizmasını çözdüm — ve brief'teki varsayımı bozuyor.** `score` alanı 321 stratejinin **321'inde tam olarak `oos 3m sharpe`'a eşit**; `oos 1y sharpe`'a **sıfır** eşleşme. Yani "OOS-cezalı skor" pratikte **3 AYLIK Sharpe**. Ayrıca `oos 1y sharpe`, 189 vakanın 189'unda `1y sharpe` ile birebir aynı — "OOS" = yayından bu yana geçen süre, ayrı bir pencere değil. Lider tablosu sırası (`leaderboard`) ise `score`'dan **yeniden üretilemiyor** (lb1=2,43 · lb2=1,15 · lb3=4,55 · lb5=−0,65) — sıralama kuralı **denetlenemez**.

## TABAN GERÇEĞİ (raporun en önemli sayısı)

SPY, aynı OOS-1Y penceresinde (2025-07-25→2026-08-02): **+%17,28, Sharpe 1,291** (3 aylık: +%4,04, Sharpe 1,136).

Gerçek ileri-dönük 189 stratejinin karşısına koyunca:

| | değer |
|---|---|
| Medyan OOS-1Y Sharpe | **−0,035** |
| Sharpe < 0 olanlar | **%50,8** |
| SPY'nin Sharpe'ını (1,291) geçen | **11 tane — %5,8** |
| SPY'nin getirisini (%17,28) geçen | %25,9 |

**Explorer da bir kazanan deposu değil.** Ek-B'nin Library için verdiği hüküm burada da geçerli; tek fark, ceza *ölçülebilir* hale geldi. Brief'in "gerçek-kazanan" eşiği (OOS-1Y Sh>0,8 · 5Y-DD<%35 · yaş>6ay) **30 strateji** veriyor — ama bunların **yalnız 9'u SPY'yi Sharpe'ta geçiyor**. Ham eşik, taban-fazlası testini geçmiyor.

## GERÇEK-KAZANAN LİSTESİ (SPY-üstü 9)

| ID | Ad / Yazar | OOS-1Y Sh | OOS-1Y ret | 5Y CAGR | 5Y DD | Yaş | Mekanizma çekirdeği |
|---|---|---|---|---|---|---|---|
| [343](https://www.quantconnect.com/strategies/343/) | High B/M High F-Score Quality Value — Louis Szeto | **2,21** | +%59,2 | %22,2 | %24,4 | 36ay | Üst-%20 B/M **sonra** Piotroski F-Score≥8; aylık; eşit ağırlık; spread>%1 ise işlem yok |
| [18](https://www.quantconnect.com/strategies/18/) | Asset Class Momentum — Jing Wu | 1,83 | +%29,8 | %10,4 | %18,7 | 98ay | 5 ETF, 12-ay momentum, en iyi 3, aylık |
| [211](https://www.quantconnect.com/strategies/211/) | Puppies of the Dow — Filib Uster | 1,73 | +%35,8 | %13,6 | %22,9 | 88ay | Dow30 → en yüksek 10 temettü **sonra** en ucuz 5; **yıllık** |
| [32](https://www.quantconnect.com/strategies/32/) | Book-to-Market Value Anomaly — Jing Wu | 1,67 | +%23,8 | %13,0 | %15,7 | 104ay | Üst-%20 mcap **sonra** üst-%20 B/M; **yıllık**; 550 klon |
| [218](https://www.quantconnect.com/strategies/218/) | 210-Day SMA Trend Overlay — H. Andersen | 1,58 | +%21,7 | %4,8 | %30,6 | 88ay | ETF sepeti, 210g SMA üstündeyse long |
| [341](https://www.quantconnect.com/strategies/341/) | Low PE **Illiquid** Value 10-Stock — Alethea Lin | 1,58 | +%71,9 | %21,7 | %26,6 | 90ay | **En DÜŞÜK 200 dolar-hacim** → en düşük 10 F/K; yıllık; N=10 |
| [17](https://www.quantconnect.com/strategies/17/) | Asset Class Trend Following — Jing Wu | 1,57 | +%21,6 | %5,2 | %29,7 | 98ay | 10-ay SMA kapısı, yoksa nakit |
| [342](https://www.quantconnect.com/strategies/342/) | Large-Cap Value+Momentum L/S — D. Melchin | 1,46 | +%30,9 | %4,3 | %17,1 | 65ay | Top-500 $hacim→top-50 mcap; değer+12-1 mom demeaned toplamı |
| [270](https://www.quantconnect.com/strategies/270/) | Cross-Asset RS Min-Variance — M. Wang | 1,46 | +%33,1 | %10,2 | %25,9 | 55ay | 180g getiri top-4 → 20g kovaryansla min-var |

Meridian'a en yakın olanlar (kesitsel, long-only, large-cap): **343, 341, 32, 342** — ve eşiği kıl payı kaçıran **310** (Sh 1,14; en düşük 12-ay vol, **N=5**, DD yalnız %16,4) ile **312** (Sh 1,08; en yüksek ROE, ayda 2 isim, 12-ay yuvarlanan 24'lük sepet).

## ŞÜPHELİ-SINIF

`score>2` olan 9 stratejinin **5'i 12 aydan genç** — yani lider tablosunun üst yarısı gerçek OOS'u olmayanlardan kuruluyor.

| ID | Profil | Teşhis |
|---|---|---|
| [478](https://www.quantconnect.com/strategies/478/) Quantum Walk BQP — henny / "highest larp output" | oos3m Sh **7,78** · 5Y CAGR **−%2,77** · DD **%70,4** · 3,3 ay | Skor tamamen 3-aylık gürültü. 5Y backtest'i para kaybediyor. Org adı kendini ilan ediyor. **Ders değil, uyarı.** |
| [411](https://www.quantconnect.com/strategies/411/) Short Vol Overbought | oos3m Sh 4,55 ama **OOS-1Y Sh 0,66**, DD %55,1 | Lider tablosu 3'üncüsü; gerçek 1-yıl ölçüsü SPY'nin yarısı. Kısa-vol kuyruk profili. |
| [322](https://www.quantconnect.com/strategies/322/) Calendar Month Seasonality | oos3m 2,36 ama **OOS-1Y Sh 0,36**, DD %50,1 | Tohumdaki "1Y-Sh yalnız 0,36" teyit edildi. |
| [245](https://www.quantconnect.com/strategies/245/) Tech Momentum Winner Rotation | oos3m 2,43 · **DD %64** · 5,9 ay · OOS-1Y **yok** | Lider tablosu 1'incisi. Topluluk şüpheciliği ("overfit mi?") **haklı**: %64 DD + 1 yıllık ölçüm yok. |
| [504](https://www.quantconnect.com/strategies/504/) Multi-Model Tactical ETF | 5Y CAGR **%233,7**, 2,3 ay, 56 takipçi | Genç + görkemli backtest + kalabalık ilgisi — sınıfın prototipi. |

## ALTI-BİLEŞEN DERSLERİ

### (1) ÇIKIŞ / TRAILING — **EXPLORER TEYİDİ, ve Ek-B'den daha sert**

30 kazananın **0'ı** trailing/ratchet durak kullanıyor (popülasyonda oran %9). Daha önemlisi, durak *işe yaramıyor* diye ölçülebiliyor:

- **Trailing/ratchet kullananlar (n=6): medyan 5Y-DD %31,0 — kullanmayanlar (n=183): %26,0.** Ratchet drawdown'ı düşürmedi, **yükseltti**.
- **Take-profit kullananlar (n=17): medyan OOS-1Y Sharpe −0,70; SPY'yi geçen %0.** Katalogdaki en zararlı tek özellik.
- Kazananların %70'inde çıkış **rebalans-kaynaklı** (takvim), %23'ü "durak yok"u açıkça beyan ediyor.
- **Tek hayatta kalan durak mimarisi farklı bir hayvan:** [84 "SPY vs. SPY"](https://www.quantconnect.com/strategies/84/) — isim-bazlı chandelier değil, **portföy düzeyinde %4 tepe-dip tetikleyicisi** (Sh 0,89 · CAGR %14,0 · DD %18,3).
- *Bizim tasarımla fark:* Bizim chandelier isim-bazlı ratchet; hayatta kalan yapı ya hiç durak koymuyor ya durağı **portföy** katmanına taşıyor.
- **Kart cümlesi:** "Isim-bazlı chandelier ratchet'i kaldırıp yerine portföy düzeyinde %4–8 tepe-dip kapısı koymak, @63g taban-fazlasını düşürmeden maxDD'yi düşürür — düşürmezse P3 çıkış-paketi hükmü 'durak katmanı yanlış' diye değil 'durak ailesi tümüyle ölü' diye kapanır."

### (2) BOYUTLAMA / RİSK — **KISMİ TEYİT + YENİ**

Ek-B'nin Baltas-Kosowski üçlü çarpımının **iki kolu Explorer'da canlı ve OOS-pozitif**, üçüncüsü yok:
- **Ters-vol** (n=11): medyan Sharpe +0,35 vs −0,04 → [226](https://www.quantconnect.com/strategies/226/) (Sh 1,23), [276](https://www.quantconnect.com/strategies/276/) (Sh 1,23).
- **Korelasyon/kümeleme (YENİ, Ek-B'de yok):** [67 Topology-Based Cluster Risk](https://www.quantconnect.com/strategies/67/) (Louis Szeto, Sh 0,86 · DD %21,9) ve [452 US Large-Cap HRP](https://www.quantconnect.com/strategies/452/) (DD yalnız **%17,9**) — Ek-B'nin `CF(ρ̄)` kartını *çalışan uygulama* olarak somutlaştırıyor: kümeler arası eşit bütçe, gürültülü isimleri tamamen dışla.
- **Trend t-istatistiği sürekli çarpanı: Explorer'da HİÇ YOK.** Ek-B'nin en yüksek değerli boyutlama kartının bağımsız teyidi gelmedi.
- Kazananların %43'ü düz **eşit ağırlık** — ve eşit ağırlık medyan Sharpe'ta +0,26 fark üretiyor. Karmaşık optimizasyon (n=14) bir üstünlük göstermiyor.
- **Kart cümlesi:** "Aday sepetini korelasyon-kümesi başına eşit bütçeyle (HRP tarzı) dağıtmak ve kümeye girmeyen isimleri elemek, eşit-1R'ye kıyasla @63g maxDD'yi düşürür; taban-fazlası korunursa EDG-008'in 'vol-ölçekleme yönsüz' hükmü **çeşitlenme koluna genişletilmez**, ayrı hüküm yazılır."

### (3) TUTUŞ / REBALANS — **EXPLORER TEYİDİ + güçlü YENİ yön**

Ek-B "ufuk sinyalin tazelenme hızına kilitli" demişti. Explorer bunu teyit ediyor **ve bir yön veriyor: uzun taraf kazanıyor.**

| Rebalans | n | medyan OOS Sharpe | SPY'yi geçen |
|---|---|---|---|
| **Yıllık** | 23 | +0,35 | **%22** |
| Aylık | 67 | +0,17 | %6 |
| Günlük | 19 | +0,13 | %5 |

Yıllık rebalanslılar SPY'yi geçme oranında diğerlerinin **~4 katı**. SPY-üstü 9 kazananın 3'ü (211, 32, 341) yıllık.
- *Bizim tasarımla fark:* Bizim ufkumuz 10–20g / ~63g; buradaki kazanan kuyruğu 12 ay.
- **Kart cümlesi:** "Aynı PARA-v3 sıralamasıyla tutuşu ~63g'den ~252g'ye çıkarmak, işlem maliyeti düştüğü için @252 taban-fazlasını @63'ün üstüne taşır — taşımazsa 'uzun ufuk avantajı evren-koşullu' hükmü yazılır ve ufuk ailesi kapanır."

### (4) EVREN KURULUMU — **EXPLORER TEYİDİ + EDG-016 için doğrudan bir karşı-örnek**

Dolar-hacim evreni kuranlar: medyan Sharpe +0,49 vs −0,13, SPY'yi geçen %14 vs %4 — Ek-B'nin "iki aşamalı dinamik huni" deseni **en güçlü tek yapısal ayırt edici**. Fundamental/değer filtresi de +0,76 ile en yüksek fark.

**Ama [341](https://www.quantconnect.com/strategies/341/) huniyi TERS çeviriyor ve kazanıyor:** "en DÜŞÜK 200 dolar-hacim" seçip içinden en ucuz 10 F/K → OOS-1Y Sh 1,58, +%71,9, CAGR %21,7. Bu, Ek-B'nin 24 Liquidity Effect notunun (düşük turnover'a long) **canlı, OOS-pozitif** versiyonu ve bizim YAŞAYAN EDG-016 kenarımızın (large-cap'te **yüksek** turnover) tam tersi yön.
- **Kart cümlesi:** "EDG-016 turnover üst-%20 kenarı, evren dolar-hacim üst-N ile dinamik kurulduğunda korunur mu? Aynı motorda üç kol — statik-251/üst-turnover, dinamik-üstN/üst-turnover, dinamik-altN/düşük-turnover — yan yana koşulur; 341 kolunun taban-fazlası pozitif çıkarsa EDG-016 'evrensel' değil **'evren-koşullu'** diye daraltılır."

### (5) SİNYAL BİRLEŞİMİ — **EXPLORER TEYİDİ (Ek-B'nin (a) ve (d) desenleri kazanıyor)**

Ek-B'nin dört deseninden ikisi kazanan kümede baskın:
- **(a) İkili-bayrak tamsayı skoru:** kümenin **en iyi stratejisi** olan 343, tam da G-Score kalıbı — Piotroski 0–9, eşik ≥8, ağırlık yok, uydurulacak parametre yok. Sh 2,21.
- **(d) Koşullu ardışık sıralama (double sort):** 343 (B/M **sonra** F-Score), 341 (illikidite **sonra** F/K), 211 (temettü **sonra** fiyat), 32 (mcap **sonra** B/M) — SPY-üstü 9'un **4'ü** bu yapıda.
- **(c) sürekli-ağırlıklı skor** yine zayıf: 342 z-skor toplamı Sh 1,46 ama 5Y CAGR yalnız %4,3, PSR 0,11.
- **Rejim-koşullu sinyal AĞIRLIĞI Explorer'da da YOK** — Ek-B'nin negatif bulgusu bağımsız olarak teyit edildi.
- **Kart cümlesi:** "PARA-v3'ün sürekli skorunu, aynı bileşenlerden türetilmiş 0–K monoton tamsayı bayrak-toplamıyla (eşik ≥m) değiştirmek @63g taban-fazlasını düşürmez; düşürmezse K-cezası ucuz olan tamsayı biçim tercih edilir."

### (6) REJİM — **EXPLORER TEYİDİ, ve EDG-005 için beklediğinizden temiz bir kanıt**

Ek-B "hepsi kapı" demişti; Explorer'da da öyle (kapı %40, sürekli-çarpan örneği yok). Ama Explorer bunu **sayıya çeviriyor** ve EDG-005'i ("vol düşürür parayı da düşürür") neredeyse birebir üretiyor:

| | n | medyan Sharpe | p90 | **SPY'yi geçen** | medyan DD |
|---|---|---|---|---|---|
| Rejim kapısı VAR | 76 | **+0,24** | +0,93 | **%2,6** | %30,6 |
| Rejim kapısı YOK | 113 | −0,14 | **+1,17** | **%8,0** | **%23,1** |

Kapı **medyanı yükseltiyor ama sağ kuyruğu kesiyor** (p90 0,93 vs 1,17; SPY'yi geçme %2,6 vs %8,0) — ve drawdown'ı da **düşürmüyor**. Yani kapının tek ölçülebilir etkisi ortalamayı toparlayıp kazanma ihtimalini yok etmek.
- *Şerh:* kapılı grupta kaldıraçlı-ETF/vol stratejileri yoğun; DD farkı karışık-etkili olabilir, Sharpe kuyruğu farkı daha güvenilir.
- **Kart cümlesi:** "SMA-200 kapısını sürekli maruziyet çarpanına çevirmek (kapı yerine kadran), taban-fazlası KORUNURKEN sağ kuyruğu (@63g üst-decile getiri) geri getirir → EDG-005 'kapı yanlış, modülasyon doğru' diye daraltılır; kuyruk geri gelmezse rejim ailesi **kapanır**."

### YENİ — Ek-B'de karşılığı olmayan üç ders

1. **Skorun kendisi bir aşırı-uydurma makinesi.** Lider tablosunu süren `score` = 3-aylık Sharpe. 3 ayda Sharpe 7,78 ölçmek gürültü ölçmektir. *Meridian dersi:* karne sıralamamızda 3-aylık pencere **hiçbir yerde** birincil sıralayıcı olmamalı; olduğu yer varsa kill-list'e yazılmalı.
2. **Yorum sayısı negatif sinyal.** Spearman(yorum, OOS-1Y Sharpe) = **−0,591**; klon = −0,335; takipçi = +0,456. Topluluğun *tartıştığı* strateji sonradan daha kötü performe ediyor — tohumdaki 245 şüpheciliği bu desenin örneği.
3. **Silinme sağkalımı ölçüldü:** 674 ID'nin 201'i (%30) listede yok. Explorer'ın gösterdiği her dağılım, ölmüşleri atılmış bir dağılım.

## DÜRÜSTLÜK ŞERHİ

- **Kod okunmadı.** Mekanizma özetleri yazarların kendi açıklama metinlerinden; kaynak kod hesap-kapısının arkasında. "Kritik satırlar" bu turda üretilemedi.
- **OOS ≠ ayrı pencere.** `oos 1y sharpe` her vakada `1y sharpe` ile aynı; OOS yalnız "yayından bu yana ≥1 yıl geçti" demek. 3 aydan genç 152 strateji için 5Y CAGR/DD **tamamen in-sample backtest**.
- **Skor neyi ödüllendiriyor:** son 3 ayın Sharpe'ını. Dolayısıyla lider tablosu yapısal olarak **genç + şanslı**yı ödüllendirir; 478 bir istisna değil, mekanizmanın **beklenen çıktısı**.
- **Sağkalan yanlılığı iki katmanlı:** (a) %30 ID silinmiş; (b) kalanlar arasında bile medyan OOS Sharpe −0,04 ve %50,8'i negatif. Kazanan listem bu havuzun sağ kuyruğu; 30 kazananın 21'i SPY'nin altında.
- **"Backtest OOS'u öngörüyor" DEMİYORUM.** 5Y-CAGR çeyreklerinin OOS Sharpe'ı monoton artıyor (Q1 −0,71 → Q4 +0,65) ama bu büyük ölçüde **tautolojik**: 2018'de yayımlanmış bir strateji için 5Y penceresi (2021–2026) zaten OOS periyodunun kendisi. İki ölçü aynı dönemi paylaşıyor.
- **Tek pencere.** Tüm OOS-1Y karşılaştırması 2025-08→2026-08 boğa penceresinde; SPY Sharpe 1,291. Farklı bir yılda kazanan kümesi de sıralaması da değişir.
- **Tüm bileşen farkları gözlemsel ve karıştırıcı-dolu** (varlık sınıfı, kaldıraç, yaş birlikte hareket ediyor). Kart cümleleri **hipotez**; hiçbiri bizim ölçüm yasalarımızdan geçmedi, sayı taşımıyor.

**Kapanan kapı:** Ek-B'nin "Explorer enumerate edilemedi" şerhi artık geçersiz — envanter alındı, altı bileşenin altısında da bağımsız ikinci kaynak elde edildi. **Açık kalan:** kod düzeyi okuma (klon/hesap gerekir) ve 343/341/32'nin gerçek kaynak satırları.

*(Not: `docs/QC-STRATEJI-DERSLERI-EK-B.md` bir markdown dokümanı değil — 99 satırlık JSONL oturum transkripti; rapor son satırdaki assistant mesajının içinde. Bu turda salt-okuma yaptım, dosyaya dokunmadım.)*
