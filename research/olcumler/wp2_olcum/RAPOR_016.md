# EDG-2026-016 — TURNOVER ANA-ETKİSİ · ÖLÇÜM RAPORU

- Kart: `research/cards/EDG-2026-016-turnover-ana-etkisi.yaml` · aile `turnover_main_effect`
- Ölçüm: `2026-08-01T11:21:54.498340+00:00` · sandbox `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/wp2_olcum`
- Repo HEAD: `90b5a0492655788b8f49c58295b62e67304d7f8c` · Python 3.12.7
- Rol: ölçüm ajanı — HÜKÜM VERMEZ, hüküm ÖNERİSİ yazar; kart dosyasına DOKUNULMADI
- Kart sha256 ölçüm ÖNCESİ = SONRASI: **EVET** (`42c49b33c93efe105c597b99751ab993bce1d05305c4963f8bb9d720080076cb`)

> **HÜKÜM ÖNERİSİ: SUCCESS — kart ölçütü karşılandı**

## 0. Bekçiler (pozitif kontrol İLK KOŞAN İŞ)

**Pozitif kontrol (CANLI, bu turda yeniden ölçüldü)** — ham `rvol20` @20 cf-katman IC: **0.0642** (hedef 0.0645, tolerans 0.005, sapma 0.0003) → **GEÇTİ=EVET** · n=2087, CI {'lo': 0.0061, 'hi': 0.1071, 'seviye': 0.95}
- @5 IC 0.0374 (CI {'lo': -0.0193, 'hi': 0.0791, 'seviye': 0.95}) · @10 IC 0.0516 (CI {'lo': -0.0119, 'hi': 0.0996, 'seviye': 0.95})
- Kart guard'ı 0.0642 çivisini anıyor; önceki tur (pk.json) 0.0642 ölçmüştü — bu tur aynı sayı yeniden üretildi.
- Katman: counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı) · eşleşme: {'bar_yok_sembol': 45, 'bar_yok_tarih': 0, 'kabul': 7077}

**PK4 / PK5 devralması** — PK4 geçti=EVET, PK5 geçti=EVET ({'A_asof_geriye_bakissizlik': True, 'B_split_bazi': True, 'C_hizli_ortalama': True, 'D_fundamentals_asof': True}).
- Devralma meşru çünkü `ortak.py` sha aynı=EVET ve `pk.py` sha aynı=EVET — **bu turda ortak altyapıya DOKUNULMADI**; yeni kodun tamamı `k016.py` içindedir. PK4 (yol tutarlılığı) ve PK5 (as-of/split/hızlı-ortalama/fundamentals özdeşlikleri) ortak.py ve pk.py üzerinde tanımlıdır. Bu tur İKİ DOSYA DA DEĞİŞTİRİLMEDİ (sha eşitliği aşağıda) ve girdi damgaları aynı — bu yüzden pk.json'daki sonuçlar bu tur için de geçerlidir; yeniden koşmak aynı sayıyı üretirdi (RNG tohumlu).

**Bu turun KENDİ bekçileri:**

| bekçi | ölçülen | geçti |
|---|---|---|
| PIT sızıntısı (`filed > t` olamaz) | ihlal satırı = 0 | EVET |
| Artık ortogonalliği | maks &#124;kesit-korelasyon&#124; = 0.0, maks &#124;gün-içi ortalama&#124; = 0.0 (4271 gün, tekil 0) | EVET |
| Hızlı Spearman ≡ kanonik `analytics.spearman_ic` | maks &#124;fark&#124; = 0.0 (3 örnek) | EVET |
| Fiziksel devir bekçisi (implied devir > 1.0) | 7 as-of kaydı geçersiz, 6 sembolde | uygulandı |
| 200g bayatlık bekçisi | 40002 hücre `bayat_seri` → None+neden | uygulandı |

- Fiziksel bekçinin geçersizlediği kayıtlar (kabuk/ölçek hatası): {'BKR': 100.0, 'CSX': 3.0, 'ETN': 100.0, 'LIN': 25000.0, 'ROKU': 4818812.0, 'SPG': 8000.0}
- Bayatlıktan etkilenen sembol sayısı: 27 · en çok etkilenen ilk 10: {'V': 4007, 'CMCSA': 3991, 'UPS': 3990, 'MA': 3817, 'F': 3687, 'REGN': 3385, 'NKE': 2934, 'CHTR': 2367, 'WBD': 1942, 'HSY': 1514}
- **Kartın adıyla andığı SCHW vakası**: dei serisinde en büyük dosyalama boşluğu 1664 gün (`2020-08-07` → `2025-02-26`), eşik 200g → eşiği aşıyor=EVET. Boşluk penceresinde 1143 gözlem günü var, bunların 137'inde turnover tanımlı kaldı; bu turda SCHW'de 1006 hücre bayat işaretlendi. Bekçi olmasaydı boşluğun BAŞINDAKİ hisse sayımı boşluk boyunca taşınır ve bu pencerede uydurma turnover üretirdi; 'bosluk_penceresinde_turnover_tanimli' bekçinin kapattığı kadarını gösterir.

## 1. Kapsam, kesit ve tanımlar

- Evren beyanı: full_251 — KAPSAM BEYANLI: bar önbelleğinde dosyası olan ve şablon asgari uzunluğunu geçen semboller ölçüldü; düşenler bar_muhasebesi'nde sayılı.
- Bar: istenen 251, yüklendi 248 (dosya yok 1, kısa 2, okunamadı 0); takvim reddedilen 0, defter yolu düşen 46256 satır / 57 sembol
- Panel: 248 sembol, 1252244 gözlem hücresi; turnover tanımlı 886434, rvol tanımlı 1247532, mom tanımlı 1247036, **üçü de** 886420
- Ölçülemeyen hücrelerin neden dağılımı (UYDURMA YASAĞI — hepsi None + neden): {'dosyalama_yok': 573996, 'olcek_hatasi_gidis_donus': 1884, 'anlik_hisse_serisi_yok': 31447, 'bayat_seri': 40002, 'olcek_hatasi_fiziksel_imkansiz': 5237}
- Kesit: 5678 gözlem gününden 4271'i kullanıldı (kesit >= 50); kesit medyanı 210.0 (min 52, maks 232); tarih aralığı ['2009-08-04', '2026-07-28']; ölçüme giren 885803 satır / 242 sembol
- Kontrol kovası: 9 kova, gün başına medyan kova büyüklüğü 23.0
- `turnover21` kesit dağılımı: {'0.01': 0.001924, '0.25': 0.004442, '0.5': 0.006067, '0.75': 0.008949, '0.99': 0.050849}

**Tanımlar (kart metninin uygulaması):**

- `universe`: full_251 — KAPSAM BEYANLI: bar önbelleğinde dosyası olan ve şablon asgari uzunluğunu geçen semboller ölçüldü; düşenler bar_muhasebesi'nde sayılı.
- `as_of_shares`: EDG-012/013 ile BİREBİR aynı altyapı (ortak.build_hisse, DEĞİŞTİRİLMEDİ): dei→us-gaap Outstanding önceliği, Issued ve ağırlıklı-ortalama YOK, val>0, donem_turu=anlik, 200g bayatlık bekçisi, split güncel-baz dönüşümü, ölçek-hatası penceresi None+neden.
- `turnover21`: medyan21(hacim) / as_of_shares(t). Bar hacmi GÜNCEL bazda split-düzeltilmiş olduğu için hisse sayımı da GÜNCEL baza çevrildi — oran bölünmeden bağımsız.
- `kontrol_degiskenleri`: rvol20 = ind.rvol20(hacim); mom21 = close[t]/close[t-21]-1. TANIMLAR EDG-013 TURUNDAKİYLE BİREBİR (ortak.bar_paneli), yeniden tanımlanmadı.
- `kesit`: İKİ KATMAN DA AYNI KESİTTE: o gün turnover21 VE rvol20 VE mom21 tanımlı semboller, kesit>=50. Aksi hâlde artık-katkı farkı kapsam farkıyla karışırdı.
- `katman_1`: turnover_ust20 = o gün turnover21 kesit üst %20
- `katman_2`: turnover_artik_rvol_mom_kontrollu = AYNI dilim, kontrol kovası tabanıyla (rvol20 terzili × mom21 terzili, 3×3) + artık-IC
- `taban_katman_1`: aynı-gün EVREN ortalaması (o gün ileri getirisi tanımlı tüm yüklü semboller) — EDG-013 ile birebir
- `taban_katman_2`: aynı-gün AYNI KONTROL KOVASI ortalaması, DIŞARIDA-BIRAK (leave-one-out): gözlemin kendisi tabana girmez. Gerekçe: kova ~23 üyeli, kendini içeren taban etkiyi 1/n kadar kendine doğru büzerdi; evren tabanı (~210 üye) ile kova tabanı arasındaki bu asimetri iki katmanı kıyaslanamaz yapardı. Kendini-içeren varyant ayrıca rapor edilir (CI'sız aritmetik dayanıklılık).
- `cift_siralama`: EDG-007 şablonu: kontrol kovası İÇİNDE turnover üst %20 vs kalanı; 9 kova hücresi + havuzlanmış kova-içi yayılım.
- `artik_ic`: GÜN BAZLI kesit OLS: pctrank(turnover21) ~ 1 + pctrank(rvol20) + pctrank(mom21); artık e(t,i). IC = havuzlanmış Spearman(e, FAZLA getiri). FAZLA getiri kullanılır çünkü artık gün-içinde zaten merkezlidir; ham getiriyle havuzlanmış IC gün-düzeyi varyansla sulandırılırdı (ham okuma tanı olarak var).
- `ci`: 21 ardışık gözlem günü blok-bootstrap, %95, ortalama 2000 / IC 600 tekrar
- `maliyet`: kart cost_model: 10.0bps + not. Kill#3 NET fazla üzerinden işletilir: net = brüt − 10.0bps (kartın yazdığı model, birebir). Gidiş-dönüş (20.0bps) BEYANLI DUYARLILIK olarak ayrıca verilir; hüküm kartın modeliyle okunur.
- `K_beyani`: Kart grid'i 2 katman (K+=2). Ufuk 10/20 kartın horizon alanıdır, K çarpanı DEĞİLDİR (EDG-013 ile aynı okuma). 9 kova hücresi ve 5'li turnover tablosu TANI'dır — havuzlanmış/üst-dilim rakamları hükmü taşır.

**Akrabalık beyanı** — rvol20 ZATEN skorda; kontrol değişkenleriyle akrabalık beyan edilir. n=200000: spearman(turnover, rvol20) = -0.077113, spearman(turnover, mom21) = -0.00853; gün-içi ortalama: rvol -0.084163, mom 0.010817. Turnover kontrol değişkenleriyle **zayıf** akrabadır — artık katmanının ne kadarını kontrolün yiyeceği bu sayılardan okunur.

## 2. KATMAN 1 — `turnover_ust20` (kart bacağı 1)

Dilim: turnover_ust20 = o gün turnover21 kesit üst %20; taban: aynı-gün EVREN ortalaması (o gün ileri getirisi tanımlı tüm yüklü semboller) — EDG-013 ile birebir. n=178954 sembol-gün, 4271 gün, 204 sembol; dilimin turnover medyanı 0.013979 (ortalama 0.019523), mom21 ort 0.018928, rvol20 ort 0.989375.

| ufuk | ölçüm | n | ortalama | %95 blok CI | hüküm |
|---|---|---|---|---|---|
| @10 | ham getiri | 178494 | +0.963% | [+0.558%, +1.385%] | ANLAMLI |
| @10 | **EVREN FAZLASI** | 178494 | +0.310% | [+0.146%, +0.493%] | ANLAMLI |
| @20 | ham getiri | 178023 | +1.950% | [+1.282%, +2.668%] | ANLAMLI |
| @20 | **EVREN FAZLASI** | 178023 | +0.648% | [+0.340%, +1.012%] | ANLAMLI |

→ **Bacak 1 (@20 (kart success_metric'i @20 yazıyor; @10 raporda tam), kart success_metric'in yazdığı ufuk): üst dilim fazlası pozitif-anlamlı = EVET** · kill#1 (CI-0-içi) = hayır

## 3. KATMAN 2 — `turnover_artik_rvol_mom_kontrollu` (kart bacağı 2)

Kontrol: rvol20 terzili × mom21 terzili (gün bazlı kesit), 9 kova. Kart iki yöntemi birden istiyor: **çift-sıralama VE artık-IC**.

### 3a. Çift-sıralama — A1: kayıtlı dilim, kontrol-kovası tabanı

KAYITLI dilim (turnover üst %20) — taban EVREN yerine AYNI-GÜN AYNI-KOVA leave-one-out ortalaması. Katman 1 ile TEK farkı tabandır; aradaki düşüş doğrudan rvol/mom kontrolünün bedelidir.

| ufuk | n | kova fazlası (LOO) | %95 blok CI | hüküm | kendini-içeren varyant | kova<2 düşen |
|---|---|---|---|---|---|---|
| @10 | 178494 | +0.269% | [+0.112%, +0.422%] | ANLAMLI | +0.257% | 0 |
| @20 | 178023 | +0.564% | [+0.273%, +0.879%] | ANLAMLI | +0.540% | 1 |

**Kontrolün bedeli** — aynı dilim, yalnız taban değişti:

| ufuk | evren tabanı (katman 1) | kova tabanı (katman 2/A1) | kalan pay |
|---|---|---|---|
| @10 | +0.310% | +0.269% | 86.6% |
| @20 | +0.648% | +0.564% | 87.0% |

### 3b. Çift-sıralama — A2: EDG-007 şablonu (kova İÇİNDE üst %20 vs kalanı)

EDG-007 çift-sıralama şablonu: her kontrol kovasında O KOVANIN turnover üst %20'si vs kalanı; hücre farkları + kova-içi merkezlenmiş havuzlanmış yayılım.

**@10g** — 9 kontrol kovası (rvol20 terzili t1..t3 × mom21 terzili t1..t3):

| kova | n yüksek | n kalan | ort yüksek | ort kalan | fark | %95 CI | hüküm |
|---|---|---|---|---|---|---|---|
| rvol_t1_mom_t1 | 19967 | 71502 | +1.000% | +0.660% | +0.340% | [+0.100%, +0.602%] | ANLAMLI |
| rvol_t1_mom_t2 | 21010 | 75432 | +0.861% | +0.554% | +0.307% | [+0.103%, +0.530%] | ANLAMLI |
| rvol_t1_mom_t3 | 22500 | 81366 | +0.954% | +0.529% | +0.425% | [+0.182%, +0.669%] | ANLAMLI |
| rvol_t2_mom_t1 | 20683 | 74125 | +0.919% | +0.622% | +0.298% | [+0.068%, +0.534%] | ANLAMLI |
| rvol_t2_mom_t2 | 22465 | 81492 | +0.856% | +0.509% | +0.347% | [+0.166%, +0.550%] | ANLAMLI |
| rvol_t2_mom_t3 | 20799 | 74747 | +1.024% | +0.549% | +0.475% | [+0.238%, +0.725%] | ANLAMLI |
| rvol_t3_mom_t1 | 22823 | 82681 | +0.819% | +0.670% | +0.149% | [-0.125%, +0.437%] | CI 0 içi |
| rvol_t3_mom_t2 | 20479 | 73431 | +0.822% | +0.571% | +0.251% | [+0.043%, +0.447%] | ANLAMLI |
| rvol_t3_mom_t3 | 21312 | 76707 | +1.001% | +0.494% | +0.507% | [+0.262%, +0.787%] | ANLAMLI |
| **HAVUZLANMIŞ** | 192038 | 691483 | — | — | **+0.359%** | **[+0.180%, +0.570%]** | **ANLAMLI** |

_kova-içi (leave-one-out) MERKEZLENMİŞ getirilerde üst%20 − kalan: kova bileşimi farkından arınmış havuzlanmış yayılım_

**@20g** — 9 kontrol kovası (rvol20 terzili t1..t3 × mom21 terzili t1..t3):

| kova | n yüksek | n kalan | ort yüksek | ort kalan | fark | %95 CI | hüküm |
|---|---|---|---|---|---|---|---|
| rvol_t1_mom_t1 | 19914 | 71304 | +2.231% | +1.322% | +0.909% | [+0.445%, +1.397%] | ANLAMLI |
| rvol_t1_mom_t2 | 20954 | 75233 | +1.781% | +1.133% | +0.647% | [+0.303%, +1.005%] | ANLAMLI |
| rvol_t1_mom_t3 | 22442 | 81162 | +1.981% | +1.125% | +0.856% | [+0.443%, +1.353%] | ANLAMLI |
| rvol_t2_mom_t1 | 20630 | 73938 | +1.902% | +1.245% | +0.657% | [+0.239%, +1.112%] | ANLAMLI |
| rvol_t2_mom_t2 | 22407 | 81281 | +1.666% | +0.987% | +0.679% | [+0.404%, +1.008%] | ANLAMLI |
| rvol_t2_mom_t3 | 20744 | 74541 | +1.954% | +1.021% | +0.933% | [+0.517%, +1.407%] | ANLAMLI |
| rvol_t3_mom_t1 | 22761 | 82468 | +1.752% | +1.294% | +0.458% | [-0.024%, +0.972%] | CI 0 içi |
| rvol_t3_mom_t2 | 20425 | 73235 | +1.676% | +1.090% | +0.586% | [+0.252%, +0.919%] | ANLAMLI |
| rvol_t3_mom_t3 | 21256 | 76505 | +1.957% | +0.971% | +0.986% | [+0.579%, +1.454%] | ANLAMLI |
| **HAVUZLANMIŞ** | 191533 | 689667 | — | — | **+0.773%** | **[+0.446%, +1.137%]** | **ANLAMLI** |

_kova-içi (leave-one-out) MERKEZLENMİŞ getirilerde üst%20 − kalan: kova bileşimi farkından arınmış havuzlanmış yayılım_

### 3c. Artık-IC

havuzlanmış Spearman IC. HEADLINE: artık ↔ FAZLA getiri (evren tabanı düşülmüş). Ham getiriye karşı okuma TANI (CI'sız).

Artıklaştırma: GÜN BAZLI kesit OLS: pctrank(turnover21) ~ 1 + pctrank(rvol20) + pctrank(mom21); artık e(t,i). IC = havuzlanmış Spearman(e, FAZLA getiri). FAZLA getiri kullanılır çünkü artık gün-içinde zaten merkezlidir; ham getiriyle havuzlanmış IC gün-düzeyi varyansla sulandırılırdı (ham okuma tanı olarak var).

| ufuk | ölçüm | n | IC | %95 blok CI | hüküm |
|---|---|---|---|---|---|
| @10 | **ARTIK IC** (fazla getiri) | 883521 | 0.0192 | [+0.0044, +0.0365] | ANLAMLI |
| @10 | ham turnover IC (fazla getiri) | 883521 | 0.0231 | [+0.0060, +0.0405] | ANLAMLI |
| @10 | artık IC / HAM getiri (tanı) | 883521 | 0.0192 | — | ölçülemedi |
| @20 | **ARTIK IC** (fazla getiri) | 881201 | 0.0284 | [+0.0092, +0.0503] | ANLAMLI |
| @20 | ham turnover IC (fazla getiri) | 881201 | 0.0337 | [+0.0127, +0.0547] | ANLAMLI |
| @20 | artık IC / HAM getiri (tanı) | 881201 | 0.0269 | — | ölçülemedi |

→ **Bacak 2 bayrakları (@20 (kart success_metric'i @20 yazıyor; @10 raporda tam)):** çift-sıralama A1 pozitif-anlamlı = EVET, A2 havuzlanmış pozitif-anlamlı = EVET, çift-sıralama GEÇTİ (ikisi birden, muhafazakâr) = EVET, artık-IC pozitif-anlamlı = EVET → **artık katkı GEÇTİ = EVET** · kill#2 (artık yok) = hayır

## 4. Maliyet-sonrası net (kill#3)

Maliyet bir SABİT olduğundan CI aynı sabitle ötelenir (bootstrap yeniden koşulmaz — cebirsel özdeş). Kart modeli tek-yön; gidiş-dönüş BEYANLI duyarlılıktır, hüküm kart modeliyle okunur.
Kart modeli **10.0bps tek-yön**; beyanlı duyarlılık **20.0bps gidiş-dönüş**.

| ufuk | katman | model | brüt | maliyet | **net** | net %95 CI | net>0 anlamlı |
|---|---|---|---|---|---|---|---|
| @10 | katman 1 (evren fazlası) | kart (10bps) | +0.310% | +0.100% | **+0.210%** | [+0.046%, +0.393%] | EVET |
| @10 | katman 1 (evren fazlası) | duyarlılık (20bps) | +0.310% | +0.200% | **+0.110%** | [-0.054%, +0.293%] | hayır |
| @10 | katman 2 A1 (kova fazlası) | kart (10bps) | +0.269% | +0.100% | **+0.169%** | [+0.012%, +0.322%] | EVET |
| @10 | katman 2 A1 (kova fazlası) | duyarlılık (20bps) | +0.269% | +0.200% | **+0.069%** | [-0.088%, +0.222%] | hayır |
| @20 | katman 1 (evren fazlası) | kart (10bps) | +0.648% | +0.100% | **+0.548%** | [+0.239%, +0.912%] | EVET |
| @20 | katman 1 (evren fazlası) | duyarlılık (20bps) | +0.648% | +0.200% | **+0.448%** | [+0.139%, +0.812%] | EVET |
| @20 | katman 2 A1 (kova fazlası) | kart (10bps) | +0.564% | +0.100% | **+0.464%** | [+0.173%, +0.779%] | EVET |
| @20 | katman 2 A1 (kova fazlası) | duyarlılık (20bps) | +0.564% | +0.200% | **+0.364%** | [+0.073%, +0.679%] | EVET |

**Kartın 'ucuz işlem görür' beyanının kanıtı** — Kart cost_model notu: 'yüksek-turnover diliminin kendisi ucuz işlem görür'. Betimleyici kanıt (CI YOK, kart bacağı DEĞİL): dilimin medyan-21g DOLAR hacmi.

- Üst %20 diliminin medyan 21g dolar hacmi: 265391711.28 · evren medyanı: 253364945.08 · oran: **1.047468×**
- Medyan kapanış: dilim 43.48 vs evren 69.82

→ **kill#3 (maliyet-sonrası net <= 0) = hayır**

## 5. Tanı (K harcanmaz — CI YOK)

TANI — kart grid'inde OLMAYAN kesitler. CI BİLEREK hesaplanmadı; CI'lı sınansaydı K çarpılırdı. Üst %20 dilimi (=5'lik tablonun 4. kovası) kartın KAYITLI katmanıdır ve CI'sı yukarıda I. bölümdedir.

**Turnover 5'lik tablosu** (0 = en düşük turnover, 4 = en yüksek):

| kova | @10 n / turnover ort / fazla ort | @20 n / turnover ort / fazla ort |
|---|---|---|
| q0 | 178496 / 0.003449 / -0.197% | 178027 / 0.003447 / -0.407% |
| q1 | 175873 / 0.004913 / -0.164% | 175413 / 0.004911 / -0.319% |
| q2 | 175731 / 0.006187 / -0.034% | 175271 / 0.006184 / -0.104% |
| q3 | 175871 / 0.008188 / +0.059% | 175411 / 0.008182 / +0.144% |
| q4 | 177550 / 0.019565 / +0.312% | 177079 / 0.019551 / +0.651% |

**EDG-013 karşılaştırması** — 013'ün kayıtlı dilimi (mom üst %20 ∧ turnover > gün medyanı) BU turun kesitinde; 013 hükmünün bu ölçümle birlikte okunması için.

| ufuk | n | 013 diliminin evren fazlası (CI YOK) | bu turun üst %20 dilimi (CI'lı) |
|---|---|---|---|
| @10 | 112338 | +0.149% | +0.310% |
| @20 | 112087 | +0.315% | +0.648% |

## 5b. Yapısal çekinceler (ölçümle AYRIŞTIRILAMAZ — hüküm okunurken birlikte okunmalı)

**Ç1 — Evren HAYATTA KALANLARDAN oluşuyor.** Kartın `universe: full_251` metnine sadık kalındı; `RETIRED_SYMBOLS` (8 delist) evrenin DIŞINDA. Bu çekince POZİTİF bir bulguda NEGATİF bulgudakinden daha ağırdır: yüksek devir hızı sıkıntı/spekülasyon göstergesidir ve yüksek-devirli isimlerin batan/çıkarılan kuyruğu örneklemde YOKTUR — bu, üst dilimin fazlasını YUKARI çarpıtır. Etkinin işareti bilinir, büyüklüğü bu veriyle ölçülemez. (Önceki turun T6 notuyla aynı yapısal sınır.)

**Ç2 — Örneklem içi tek dönem.** Ölçüm tek bir tarihsel pencerede yapıldı; alt-dönem kararlılığı bu kartın grid'inde YOK, ölçülmedi. Kart bir alt-dönem bacağı kaydetmediği için sonradan eklenmesi K'yı harcar — istenirse KENDİ kartını ister.

**Ç3 — `rvol20` skorda, `turnover21` değil.** Kontrol değişkenlerinden biri canlı skorun bileşenidir; artık katmanı bu yüzden 'skora ne EKLER' sorusunun doğru biçimidir. Ama mom21 kontrolü canlı skorun momentum kolunun BİREBİR aynısı değildir (kart, kontrolü 013 turundaki tanımla sabitledi) — entegrasyon kararında canlı skor bileşenleriyle çakışma ayrıca sınanmalıdır.

**Ç4 — Devir hızı ile işlem maliyeti arasındaki ilişki tek yönlü okunmamalı.** Yüksek devir likidite demek (yukarıdaki dolar-hacim kanıtı), ama aynı zamanda o isimlerin oynaklığı da yüksektir; kartın sabit-bps maliyet modeli oynaklığa bağlı kayma (slippage) farkını TAŞIMAZ. Kill#3 kartın yazdığı modelle işletildi.

## 6. Hüküm önerisi (hükmü Rol-1 işler)

**Kart success_metric:** üst-dilim fazlası @20 anlamlı POZİTİF VE artık-katkı anlamlı (çift-sıralama VE artık-IC)
**Değerlendirme ufku:** @20 (kart success_metric'i @20 yazıyor; @10 raporda tam)

| ölçüt | sonuç |
|---|---|
| `pozitif_kontrol_GECTI` | **EVET** |
| `bacak1_ust20_pozitif_anlamli` | **EVET** |
| `cift_siralama_A1_pozitif_anlamli` | **EVET** |
| `cift_siralama_A2_pozitif_anlamli` | **EVET** |
| `cift_siralama_GECTI_ikisi_birden` | **EVET** |
| `artik_ic_pozitif_anlamli` | **EVET** |
| `bacak2_artik_katki_GECTI` | **EVET** |
| `success_metric_KARSILANDI` | **EVET** |
| `kill1_ust_dilim_CI_0_ici` | **hayır** |
| `kill2_artik_yok` | **hayır** |
| `kill3_maliyet_sonrasi_net_sifir_alti` | **hayır** |

### → SUCCESS — kart ölçütü karşılandı

**EDG-013'e yansıması.** Kart tezi: ana etki bağımsız-anlamlıysa sinyal turnover'dır (013'ün etkileşim-tezi düşer, sinyal yaşar); artık yoksa ikisi de rvol/mom akrabalığına düşer. Yukarıdaki bayraklar bu iki dalın hangisinin geçerli olduğunu verir; 013'ün statü kararı Rol-1'dedir.

---

### Kod damgası

- Ölçüm kodu sha256: {'ortak.py': '8b274c5645838eb5fe11bbdd065703639c0917dac5a27059656c2f5572e94442', 'pk.py': '25c1221ef0758fd2f99f517423ea6b2501e67c550a75abc92544be3737ba0af6', 'k016.py': 'fee321d9c66fcb35c992d43cb9a9476b3fd8b0895f0f1972eaaf5bf7e94c58b4', 'rapor_016.py': '70dae89c71e6f2d193ba754063c4c5a57723e1d6839f4b27e06209bdf818bb28', 'damga_016.py': '3c951b0c2fbddf4932db0c12ab1e93f5612e1a1c6aa8391195b964650feb2216'}
- Girdi sha256: {'research/edgar_facts/shares_outstanding.csv.gz': '446f7bf00a227c586697f0a9669e82dc85abbb9504d67df45e4b695a03d998a3', 'state/bars_integrity.json': 'ab6b2e5995ba3084782cbcedc2982a7d56d0d16a6245cadff14e74e5edfdedcc', 'state/counterfactuals.jsonl': 'df479477d73c9f7998bebc368e505cb0ed77677c676719782b907199eb771f09', 'state/cf_open.json': 'fea01ce5696cf8d593800d0e9cc9af25617b4a46338f701bbd0ade99f49a6189'}
- Çıktı sha256: {'sonuc_016.json': '4f45e5e946d115c29ae0de6592c859ee3d21ab364ec4bc6af972b09422025e05'}
- Önceki turun kol_/sonuc_ dosyaları EZİLMEDİ; bu turun çıktıları sonuc_016.json + RAPOR_016.md.
