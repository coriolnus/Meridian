# UZUN-UFUK MEGA-CAP TREND KOLU — ÖN-KAYITLI ÖLÇÜM RAPORU

Rol 2 · SALT-ÖLÇÜM · 2010-12-31 → 2026-07-28 (15.57 yıl) · repoya/state'e hiçbir bayt yazılmadı.

Operatör tezi: *"en büyük hisseler en güçlü — insanlar buradan kazanıyor"*; Rol 1 çerçevesi: bu güç aylar-ölçekli kalıcılıksa 10-günlük kesme onu doğruyor. Bu rapor o tezi ölçer, savunmaz.

## 0. HÜKÜM (önce)

**SPY'ı GEÇTİ — ama koşulsuz değil ve üst-sınır-iyimser.** Ön-kayıtlı iki varyantın ikisi de
friksiyon-sonrası SPY'ı toplam getiri ve Sharpe'ta anlamlı biçimde geçti (Bonferroni k=2 sonrası
dahil); **maxDD çıtasını İKİSİ DE geçemedi**. KILL koşulu (iki varyant da anlamlı geçemiyor)
tetiklenmedi.

| Ön-kayıtlı çıta | N=10 | N=20 |
|---|---|---|
| Toplam getiri > SPY | ✅ 6,078% vs 483% | ✅ 1,998% |
| Sharpe > SPY | ✅ 1.09 vs 0.75 | ✅ 0.95 |
| maxDD daha iyi (daha sığ) | ❌ -40.2% vs -34.1% | ❌ -34.2% (fiilen berabere) |
| Anlamlılık (t, NW lag3, vs SPY) | ✅ t=4.85 | ✅ t=3.47 |
| Ek çıta: eşit-ağırlık evren B&H | ✅ t=3.69 | ⚠️ t=1.73 (Bonferroni'yi geçmez) |

**Üç çekince hükmü kayıtsız kabul etmeyi engeller:**
1. **Survivorship üst sınırı** — evrenin kendisi bugünün hayatta kalanlarıdır (§5).
2. **Son alt-dönem sessiz** — 2021-2026'da hiçbir varyant hiçbir çıtaya karşı anlamlı değil (§3).
3. **Tez mekanizma olarak YANLIŞLANDI** — bu kol "uzun-ufuk" değil: medyan tutuş
   63 işlem günü (~3 ay), yıllık devir
   %329 (§4).

## 1. ÖN-KAYIT VE YORUM BEYANI

Değiştirilmeyen ön-kayıt: aynı evren (emekli 8 hariç), long-only, aylık değerlendirme, giriş
12-1 momentum üst-N (N=10/N=20, k=2), çıkış chandelier ~3,5×ATR aylık kontrol (zaman-stopu ve
hedef YOK), eşit-ağırlık, friksiyon 10bps/bacak.

Ön-kayıtta belirtilmediği için ÖLÇÜMDEN ÖNCE seçilip burada beyan edilen yorumlar:

| Kalem | Seçim | Gerekçe |
|---|---|---|
| 12-1 tanımı | ay t sonunda `P(t−1 sonu)/P(t−12 sonu)−1` (son ay atlanır) | standart Jegadeesh-Titman atlama-ayı |
| İcra | karar ay-sonu kapanışında, **icra ERTESİ seans AÇILIŞI** | bakma-ileri tamamen kapansın diye |
| ATR | ATR22 (basit ortalama), chandelier = *girişten beri en yüksek high* − 3,5×ATR | "iz-süren" cırcır okuması |
| Eşit-ağırlık | **birincil:** her ay 1/N'e denkleştirme · **duyarlılık:** drift (yalnız girişte eşit) | ifade iki okumaya açık; ikisi de raporlanır, hüküm birincilde |
| Nakit | %0 faiz | muhafazakâr |
| Sharpe | rf=0, günlük getiriden yıllıklandırılmış | tüm kollarda aynı |

**Çoklu-sınama:** ön-kayıtlı k=2. Bonferroni ile tek-yönlü eşik p<0,025 (t>1,96).
Duyarlılık/teşhis koşumları hükme GİRMEZ, ayrıca etiketlenmiştir.

## 2. VERİ ZEMİNİ — İKİ KRİTİK BULGU (bu ölçümün en pahalı çıktısı)

### BULGU-1 (KRİTİK, REPO KUSURU): hayalet-satır kapısının hacim şartı sınıfın %29'unu kaçırıyor
`data._unadjusted_mask` üç koşulu **VE**'ler: (a) |hareket|>%35, (b) ertesi bar geri dönüyor,
(c) hacim tutarsız (0 ya da fiyatın tersi oranda). Ham 259 defter üzerinde ölçüldü:

| | satır |
|---|---|
| (a) \|ret\|>%35 | 258 |
| (a&b) sıçra-ve-geri-dön = **gerçek hayalet sınıfı** | **35** |
| (a&b&c) karantinaya alınan | 25 |
| **(c) yüzünden KAÇAN** | **10 (%29)** |

(b) zaten dikişi (geri dönmeyen ölçek adımı) hayaletten ayırıyor; (c) yalnız gerçek-pozitif
siliyor. Kaçanlar arasında **GILD 2013-12-18 (+%110, ertesi gün −%50)**, CMCSA aynı gün (+%105),
DLTR 2012-06-26 (+%103), UNP 2014-06-06 (+%102) — hepsi apaçık ×2 ölçek satırı.
**Sonuç: `component_ic.json`, cf ve R-tabloları bu satırlarla üretilmiş olabilir.**

### BULGU-2 (KRİTİK): çözülmemiş ölçek/kimlik kırılmaları
Kapıdan geçen barlarda 97 adet geri DÖNMEYEN büyük adım var
(59 sembolde). Örnekler: **CHTR 2010-09-15 ×1158**
(iflas-öncesi hisse), **AVGO 2009-08-06 ×162**, **PINS 2019-04-18 ×152,5** (2013-2018 arası
"geçmişi" 200-1000 adetlik kuruş barları — Pinterest 2019'da halka açıldı), **GOOGL 2013-12-18
×2,6**, **RTX 2020-04-03 ×3,8** (UTX birleşmesi), **HLT 2017-01-04 ×2,1** (spinoff),
ve düzeltilmemiş spinoff düşüşleri (ABT 2013-01-02 −%51, DD 2025-11-03 −%58, HON 2026-06-29 −%51).
**TDG'nin 2011-11 → 2012-01 kesiti tamamen bozuk** (kapanış $2-4, gün-içi high/low oranı 10'a kadar;
TransDigm o tarihte ~$100'du).

### Bu ölçümde ne yapıldı (ölçüm-içi katman, REPOYA YAZILMADI)
`integrity.py` — yalnız satır/uygunluk DÜŞÜRÜR, hiçbir fiyat ÜRETMEZ:
**L1** fiyat-only sıçra-ve-geri-dön (10 satır) ·
**L2** high/low>3 (15 satır) ·
**L3** çözülmemiş kırılmadan sonra 15 ay uygunsuzluk ·
**L4** kırılma sonrası ≥300 temiz bar · **L5** son 63 seans medyan dolar hacmi ≥20M$.

**Duyarlılık — sonuç bu katmanın seçimlerinin eseri DEĞİL:** uygunluk katmanı (L3/L4/L5) tamamen
kapatıldığında N=10 CAGR %31.51 (açıkken
%30.32), N=20 %22.25
(açıkken %21.58) — hüküm değişmiyor.

**Beyan (dürüstlük kalemi):** L1/L2 bir satırı düşürürken ERTESİ barı görür; bu geriye-dönük veri
temizliğidir, canlıda aynı anda bilinemez. Deponun kendi kuralı da aynı özelliği taşır.

## 3. SONUÇLAR

### TAM PENCERE
| kol | toplam | CAGR | vol | Sharpe | maxDD |
|---|---|---|---|---|---|
| N10_rebalance | 6,077.7% | 30.32% | 27.9% | 1.09 | -40.2% |
| N10_drift | 6,472.8% | 30.84% | 28.5% | 1.09 | -42.2% |
| N20_rebalance | 1,997.6% | 21.58% | 23.5% | 0.95 | -34.2% |
| N20_drift | 2,399.6% | 22.96% | 24.3% | 0.97 | -35.4% |
| SPY_BH | 483.4% | 11.99% | 17.1% | 0.75 | -34.1% |
| EW_UNIVERSE_BH | 1,070.3% | 17.11% | 19.4% | 0.91 | -34.0% |

### 2011-2015
| kol | toplam | CAGR | vol | Sharpe | maxDD |
|---|---|---|---|---|---|
| N10_rebalance | 308.8% | 32.59% | 23.8% | 1.31 | -28.0% |
| N10_drift | 286.2% | 31.09% | 23.9% | 1.25 | -28.9% |
| N20_rebalance | 185.7% | 23.40% | 20.9% | 1.11 | -24.4% |
| N20_drift | 191.1% | 23.87% | 21.2% | 1.12 | -24.7% |
| SPY_BH | 60.5% | 9.94% | 15.4% | 0.69 | -19.4% |
| EW_UNIVERSE_BH | 109.4% | 15.96% | 16.1% | 1.00 | -19.4% |

### 2016-2020
| kol | toplam | CAGR | vol | Sharpe | maxDD |
|---|---|---|---|---|---|
| N10_rebalance | 325.4% | 33.65% | 29.5% | 1.13 | -40.2% |
| N10_drift | 373.8% | 36.57% | 30.3% | 1.18 | -42.2% |
| N20_rebalance | 203.1% | 24.88% | 24.2% | 1.04 | -34.2% |
| N20_drift | 232.1% | 27.19% | 25.1% | 1.09 | -35.4% |
| SPY_BH | 86.0% | 13.24% | 18.9% | 0.75 | -34.1% |
| EW_UNIVERSE_BH | 141.8% | 19.35% | 19.9% | 0.99 | -34.0% |

### 2021-2026
| kol | toplam | CAGR | vol | Sharpe | maxDD |
|---|---|---|---|---|---|
| N10_rebalance | 261.9% | 26.02% | 29.9% | 0.93 | -26.8% |
| N10_drift | 266.5% | 26.31% | 30.6% | 0.92 | -28.4% |
| N20_rebalance | 147.9% | 17.73% | 25.0% | 0.78 | -25.4% |
| N20_drift | 164.6% | 19.12% | 26.3% | 0.80 | -25.3% |
| SPY_BH | 100.7% | 13.35% | 16.8% | 0.83 | -25.4% |
| EW_UNIVERSE_BH | 136.9% | 16.78% | 21.6% | 0.83 | -29.1% |

### Çıtalara karşı fazla getiri (aylık getiri farkı, Newey-West lag=3)
| kol | dönem | vs SPY (yıllık) | t | vs EW-evren (yıllık) | t |
|---|---|---|---|---|---|
| N10_rebalance | tam | 18.56% | 4.85 | 13.14% | 3.69 |
| N10_rebalance | 2011-2015 | 22.58% | 3.90 | 16.26% | 3.16 |
| N10_rebalance | 2016-2020 | 19.30% | 3.66 | 13.10% | 2.84 |
| N10_rebalance | 2021-2026 | 14.70% | 1.81 | 10.66% | 1.36 |
| N10_drift | tam | 19.27% | 4.66 | 13.83% | 3.62 |
| N10_drift | 2011-2015 | 21.32% | 3.47 | 15.05% | 2.75 |
| N10_drift | 2016-2020 | 22.45% | 3.39 | 16.11% | 2.80 |
| N10_drift | 2021-2026 | 15.01% | 1.80 | 10.96% | 1.37 |
| N20_rebalance | tam | 9.41% | 3.47 | 4.39% | 1.73 |
| N20_rebalance | 2011-2015 | 13.00% | 3.38 | 7.13% | 2.28 |
| N20_rebalance | 2016-2020 | 10.66% | 2.86 | 4.88% | 1.55 |
| N20_rebalance | 2021-2026 | 5.35% | 0.93 | 1.62% | 0.28 |
| N20_drift | tam | 10.83% | 3.66 | 5.75% | 2.10 |
| N20_drift | 2011-2015 | 13.48% | 3.31 | 7.58% | 2.27 |
| N20_drift | 2016-2020 | 12.80% | 3.15 | 6.92% | 2.04 |
| N20_drift | 2021-2026 | 6.98% | 1.09 | 3.19% | 0.51 |

### CAPM (SPY'a karşı, aylık)
| kol | beta | yıllık alfa | t(alfa) | R² |
|---|---|---|---|---|
| N10_rebalance | 1.14 | 16.57% | 3.35 | 0.46 |
| N10_drift | 1.16 | 16.95% | 3.28 | 0.45 |
| N20_rebalance | 1.03 | 9.00% | 2.78 | 0.60 |
| N20_drift | 1.04 | 10.36% | 2.90 | 0.56 |

**Alt-dönem okuması (tek-rejim hükmü yasak):** kol 2011-2015 ve 2016-2020'de her iki çıtayı da
anlamlı geçiyor; **2021-2026'da hiçbir varyant hiçbir çıtaya karşı anlamlı değil**
(SPY'a karşı t=1.81…1.09;
EW-evrene karşı t=0.28…1.36).
Fazla getiri işareti pozitif kalıyor ama örneklem hüküm vermeye yetmiyor. Bu, "edge öldü"
demek DEĞİL; "son 5,5 yılda kanıtlanamadı" demek.

## 4. DEVİR, FRİKSİYON, TUTUŞ — ve tezin mekanizma olarak yanlışlanması
| kol | rebalans | işlem bacağı | ay/işlem | devir (tek-yön/yıl) | friksiyon $ | sürükleme/yıl | medyan tutuş | ort. tutuş | >1yıl pay | nakit |
|---|---|---|---|---|---|---|---|---|---|---|
| N10_rebalance | 187 | 2352 | 5.2 | 329% | 1,520,744 | 0.66% | 63g | 80g | 2.5% | 0.1% |
| N10_drift | 187 | 968 | 5.2 | 284% | 1,386,280 | 0.57% | 63g | 80g | 2.5% | 0.8% |
| N20_rebalance | 187 | 4713 | 10.5 | 332% | 680,747 | 0.66% | 63g | 79g | 2.6% | 0.0% |
| N20_drift | 187 | 1923 | 10.6 | 289% | 678,188 | 0.58% | 63g | 79g | 2.6% | 0.1% |

**Durak genişliği ÖLÇÜLDÜ, varsayılmadı:** 3,5×ATR22 evrende medyan **%7.6**
(p10 %4.8 — p90 %13.8), SPY'da
%3.6. Ön-kayıt bunu "geniş" diye niteliyordu; ölçüm bunu **desteklemiyor** —
bu, mega-cap için orta-dar bir iz-süren duraktır ve tutuş dağılımını o belirliyor.

**Tez mekanizma olarak yanlışlandı:** kapanan işlemlerin medyanı 63,
ortalaması 80 işlem günü; yalnızca
%2.5'i bir yılı aşıyor. Yani kazanan kol "aylarca-yıllarca
tut" kolu değil, **~3 ay medyan tutuşlu, ~%329 yıllık
devirli** bir aylık-seçim kolu. Operatörün yönü (10 günden UZUN) doğrulanıyor; ölçek iddiası
("aylar-yıllar") doğrulanmıyor.

**Çıkış kuralı katkı DEĞİL maliyet (teşhis, ön-kayıt dışı):** aynı boru hattında chandelier
kapatıldığında N=10 CAGR %30.32 → **%17.88**,
N=20 %21.58 → **%16.57**
(Sharpe 1.09→0.84 /
0.95→0.83).
Edge **kesitsel momentum seçiminden** geliyor, iz-süren duraktan değil — durak onu tırpanlıyor.
Aynı imza pozitif kontrolde de var: SPY'ın kendisine chandelier uygulandığında CAGR
%11.99 → %5.69.
Bu, denetimdeki **ED-1 (çıkış-dağılım tutarsızlığı)** bulgusunun uzun-ufuk kolundaki karşılığıdır.

## 5. SURVIVORSHIP ÇERÇEVESİ (bu ölçümde KRİTİK)

**Evren bugünün 251'idir (barı olan 250) — yani geçmişe bakınca KAZANANLARDIR.** Elimizde delist
edilmiş seri YOK; bu yüzden yanlılık ÖLÇÜLEMEZ, ancak sınırlandırılabilir. Yapılanlar:

- **Listelenme yanlılığı KAPATILDI:** evren her ay o güne kadar GERÇEKTEN barı olan sembollerle
  kuruldu (uygun sembol sayısı 202 → 250
  arasında büyüyor); sembolün listelenmeden önceki tarihleri NaN kalır, ffill kendi ömrü içindedir.
- **Hayatta-kalma yanlılığı KAPATILAMAZ:** 2011'de mega-cap olup sonra çöken/endeksten düşen
  isimler listede hiç yok.

**ASİMETRİ AÇIKÇA:** SPY survivorship-DÜZELTİLMİŞ gerçek bir seridir (endeks kendi
rekonstitüsyonunu taşır); kolumuz değildir. Yani **kol-vs-SPY kıyası yapısal olarak kolun
lehinedir.** Buna karşılık **eşit-ağırlık evren B&H çıtası AYNI yanlılığı taşır** — dolayısıyla
kol-vs-EW-evren kıyası survivorship'e büyük ölçüde NÖTRDÜR ve asıl okunması gereken satır odur.

| katman | ölçü | okuma |
|---|---|---|
| Evren düzeyi şişkinlik vekili | EW-evren − SPY = **5.12 puan/yıl** | evrenin kendisinin taşıdığı iyimserlik (survivorship + eşit-ağırlık + boyut tilt'i birlikte) |
| Üst sınır (ölçülen) | N10 vs SPY **18.56 puan/yıl** | survivorship-iyimser ÜST SINIR |
| Yanlılığa büyük ölçüde nötr | N10 vs EW-evren **13.14 puan/yıl** (t=3.69) | seçim etkisi — asıl aday sayı |
| Alt sınır | **ÖLÇÜLEMEZ** | üst-momentum kovasındaki delist/iflas tehlikesi verimizde temsil edilmiyor |

Bir ek nüans: emekli 8 sembolün **7'si birleşme/take-private** ile düştü (genelde primli;
8'incisi FI — borsa transferi, şirket FISV olarak sürüyor). Yani bu evrende GÖZLENEN delistler
yukarı-yanlı olaylardır ve onları dışlamak aşağı-yanlı bir etkidir — iflasla sıfırlanan tek bir
isim bile yok. Asıl kayıp gözlenmeyenlerdir: listeye hiç girmemiş çökenler.

## 6. POZİTİF KONTROLLER VE MUHASEBE DOĞRULAMASI

| kontrol | sonuç | hüküm |
|---|---|---|
| **PK1** evrene yalnız SPY, çıkış kapalı | CAGR %12.00 vs SPY B&H %11.99; son değer farkı **0.1001%** | ✅ sızıntı yok — fark tam olarak ödenmeyen tek satış bacağı (10bps) |
| **PK2** yalnız SPY, chandelier açık | CAGR %5.69, 31 çıkış | teşhis: durak tek başına bilinen seride %6.30 puan/yıl yiyor |
| **PK3** SPY evrenin İÇİNDE (N=10) | CAGR %30.3155 = kolun kendisi (%30.3155); SPY için işlem kaydı **0** / 974 | SPY üst-10 momentuma HİÇ girmiyor — sızıntı yok; boru hattı endeksi hisselerden ayırt ediyor |
| **PK4** yol tutarlılığı (ağırlık↔defter) | maks. bağıl fark **7.0e-14%** (3914 gün) | ✅ makine hassasiyeti |
| **PK5** nakit-akışı özdeşliği | fark **-1.9e-12%** | ✅ friksiyon/boyutlandırma defteri tutarlı |

**MUHASEBE HATASI BULUNDU VE DÜZELTİLDİ (kendi kusurumuz, kayda geçiyor):** ilk sürümde günlük
işaretleme döngüsü rebalans döngüsünün DIŞINDAYDI — tüm özkaynak eğrisi **nihai** portföyle
fiyatlanıyordu. Toplam getiri doğru çıkıyordu (son portföy doğruydu) ama **vol %150, Sharpe 0,37,
maxDD −%87** üretiyordu. **PK1 bunu GÖREMEDİ** çünkü tek-enstrümanlı al-tut'ta portföy hiç
değişmez. PK4/PK5 bu yüzden eklendi ve hatayı anında ayrıştırdı (%27 sapma).
**DERS: tek-enstrümanlı pozitif kontrol, portföy-yolu hatalarına karşı KÖR bir kontroldür.**

## 7. KAPSAM BEYANI

- Beyan edilen evren **251**, barı olan **250**
  (eksik: FISV — 2026-07-30'da evrene alındı, yerel diskte CSV yok).
- Emekli ve dışlanan 8: ANSS, DFS, FI, HES, IPG, K, PARA, WBA.
- Bar kapsamı 2004-01-02 → 2026-07-28; **sim 2010-12-31 → 2026-07-28**
  (15.57 yıl). Ön-kayıt 2011→2026 istiyordu; barlar elverdi.
- Deponun kendi kapısı bu koşumda **433 satır** düşürdü
  (2012-01-20:1, 2013-07-15:1, 2013-12-18:1, 2018-11-22:179, 2025-05-26:251); reddedilen seri yok.
- Son seans **kesildi**: 2026-07-29'da 251 sembolün yalnız 44'ünde bar var (kısmi gün);
  o günde işaretleme son günün özkaynağını uydurma biçimde çökertirdi.
- Sembolün kendi ömrü içinde ffill'lenen hücre: 12,252
  / 1,424,927.

## 8. BU ÖLÇÜMÜN DEĞMEDİĞİ SORULAR
Kapasite/piyasa etkisi (10bps sabit varsayıldı; devir %300/yıl olduğu için canlı TCA burada
paper-modelden daha çok önemlidir — YÜ-1), vergi, kısa bacak, sektör yoğunlaşması,
2021-2026'daki sessizliğin rejim mi decay mi olduğu.