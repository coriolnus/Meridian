# KEŞİF — FRİKSİYON-BİLİNÇLİ SEÇİLİM (2026-08-22)

**Statü: TASARIM-KANITI (keşif). HÜKÜM YOK — hangi ailenin kartlaşacağı Rol-1/operatör kararıdır.**
Bu belge EDG-2026-040 ACİL kaleminin **(b) bacağı** için ("friksiyon-bilinçli seçilim/eşik
tasarımı — YENİ KART İSTER", ROADMAP §2 satır ~195) aday mekanizma AİLELERİNİ toplar, her
ailenin ön-kanıtını mevcut artefaktlardan + bir salt-okuma canlı çekimden çıkarır ve
kart-adayı eşik/kill ENVANTERİNİ (öneri değil envanter) listeler. Kod yazılmadı, hiçbir
karta/state'e dokunulmadı.

## 0. Kanıt künyesi

- **Canlı çekim (salt-okuma, ssh-stdin deseni — emsal `research/olcumler/exe007_broker_teyit_2026-08-22/canli_cek.py`):**
  A1'den `entry_execution.jsonl` ayna satırları (n_ayna=15, n_toplam=30) + 11 sembolün
  `state/bars/*.csv` kuyrukları (son 60 bar) + `goal.slippage_bps=5` künyesi.
  Çekim: 2026-08-22T18:42:04Z · sha256 `85d5ace2c04fdea13aaad8d38d9c818d2d54b48726420b578a2d567a8fbf4424`.
  Ham dosya oturum scratchpad'indeydi (kalıcı değil); **bu belgedeki tablolar satır-düzeyinde
  tamdır** — çekim aynı desenle her an yeniden üretilebilir. Canlıya/state'e tek bayt yazılmadı.
- **Donmuş artefaktlar:** `research/olcumler/edg042_kosum_2026-08-22/sonuc.json` (K1 13 satır dökümü),
  `research/cards/EDG-2026-031/034/037/038/040/042/043`, `EXE-2026-006`,
  `research/olcumler/edg040_friksiyon_2026-08-22/`, `edg043_friksiyon_limit_2026-08-22/`.
- **Kod okumaları (dosya:satır):** `meridian/broker.py:33-34` (ADV_CAP_PCT=0.02, IMPACT_COEF=0.10),
  `:114-115` (ENTRY_LIMIT_ATR_MULT=0.5, ENTRY_LIMIT_PCT_CAP=0.01 kod varsayılanları),
  `:174-200` (`entry_limit_price` = tetik + min(mult·ATR, cap·tetik)), `:515` + `:615-624`
  (`fill_entry`: base_fill=next_open·(1+slip); adv varsa tavan int(0.02·ADV), dolum
  = base_fill·(1+0.10·katılım)); `meridian/backtest.py:185` (`_adv`: 20 bar, KESİN ÖNCE, pay
  cinsinden), `:332-337` (replay dolum çağrısı, adv+size_mult+atr geçirilir), `:438`
  (`candidates.sort(key=score, reverse=True)` — kabul skor-sıralı, EDG-034 Faz-0 teyidi);
  `meridian/strategy.py:396-503` (skor bileşenleri; uyuyan veto düğmeleri `entry.min_rvol`:413,
  `entry.max_ext_atr`:420 — varsayılan 0=kapalı; sıfır-ağırlık bileşen deseni `entry.w_rvolband`/
  `w_mom`/`w_turnover` varsayılan 0.0, çivi test_score_rebuild_v115 / test_turnover_kablolama_v149);
  `meridian/loop.py:1428` (canlı ayna da `_adv` geçirir — aynı yasa iki motor), `:2463+`
  (`_patch_entry_slippage`: E2 dolum yaması, payda reconcile anında donar);
  `meridian/guard.py:423,505-507` (ısı sert tavanı `heat_hard_r`).

## 1. Soru netleştirme — "friksiyon-bilinçli seçilim" ne olabilir

Tanım (bu keşfin çerçevesi): **karar anında bilinebilen (PIT) vekillerle bir emrin beklenen
friksiyonunu tahmin edip bu tahmini üç kanaldan birine bağlamak:**

1. **DOĞUM kanalı** — sinyal hiç doğmasın / geriye düşsün (skor terimi ya da sert veto).
2. **İCRA kanalı** — sinyal doğsun ama emir tipi pahalı-dolum kuyruğunu kessin (limit tavanı).
3. **MARUZİYET kanalı** — sinyal doğsun, emir de gitsin, ama boyut/ısı payı friksiyon
   beklentisiyle ölçeklensin.

Mevcut şasinin friksiyon-bilinci BUGÜN nerede (ölçüldü, varsayılmadı):

- Motorun TEK isim-değişken friksiyon terimi katılım etkisidir (`0.10·qty/ADV`). 13 gerçek
  ayna dolumunda katılım **0.02–0.38 bps** (ADV'nin) → etki terimi **0.002–0.038 bps**.
  Ölçülen |friksiyon| 10–327 bps. Yani mevcut terim gerçeğin **~4 mertebe altında**; bu
  kitapta friksiyon boyut-kaynaklı DEĞİL, açılış-mikroyapısı/oynaklık kaynaklı.
- `illiquid` NO_GO'su ancak int(0.02·ADV)<1 ↔ ADV<50 pay iken ateşler — 251'lik evrende
  fiilen ölü.
- E1 limit yasası motorda uyuyor (canlı fiilen cap=0.04 + mult=100 → bağlamaz kılınmış;
  `broker.py:187-198` EZILEN-DAMGA). Silahlı hâli (0.5·ATR, %1) EXE-006/EDG-043'ün ölçtüğü şey.
- ATR14 her planda donmuş alan (`sig.atr`, E2 satırlarında `atr`) — friksiyon öngörücüsü
  adayı VERİ OLARAK zaten kayıtlı.

## 2. Ön-kanıt — 13 gerçek giriş dolumu × likidite/oynaklık vekilleri

Kova = EDG-042 K1 ile AYNI filtre (motor=ayna · karar=submitted · fill dolu · bps dolu), n=13.
Vekiller karar-anı bilgi kümesinden: **ADV20** = plan tarihinden KESİN ÖNCE 20 barın hacim
ortalaması (`backtest._adv` yasasıyla aynı pencere); **ADV$** = ADV20 × önceki kapanış;
**menzil%** = aynı 20 barın medyan (H−L)/C; **ATR%** = plan alanındaki `atr` / `entry_trigger`;
**katılım** = fill_qty/ADV20. bps işareti E2 sözleşmesi (aleyhte = +).

| ticker | plan tarihi | bps | ATR% | menzil% | ADV$ (M) | katılım (bps of ADV) | fiyat |
|---|---|---:|---:|---:|---:|---:|---:|
| MRVL | 2026-08-19 | **+327.5** | 7.74 | 6.75 | 4 717.9 | 0.02 | 216.00 |
| BKNG | 2026-08-05 | **+134.5** | 3.74 | 3.24 | 1 144.9 | 0.04 | 194.27 |
| MRNA | 2026-08-14 | −130.7 | 5.97 | 4.67 | 293.2 | 0.38 | 63.63 |
| MRNA | 2026-08-19 | −122.1 | 6.56 | 4.65 | 278.7 | 0.02 | 62.98 |
| CRM | 2026-08-13 | −82.0 | 4.00 | 4.09 | 2 406.5 | 0.02 | 193.32 |
| EMR | 2026-08-05 | +54.6 | 2.98 | 3.01 | 448.5 | 0.13 | 158.84 |
| HUM | 2026-08-14 | −43.0 | 3.82 | 3.89 | 560.2 | 0.30 | 384.97 |
| MRK | 2026-08-13 | +40.8 | 2.47 | 2.48 | 1 163.0 | 0.07 | 132.92 |
| LLY | 2026-08-19 | +29.8 | 3.31 | 2.82 | 3 238.7 | 0.03 | 1 225.73 |
| NUE | 2026-08-05 | +16.1 | 3.13 | 2.82 | 371.3 | 0.18 | 274.04 |
| AMGN | 2026-08-05 | +15.0 | 0.00* | 2.11 | 960.0 | 0.09 | 390.02 |
| BDX | 2026-08-19 | +13.2 | 2.40 | 2.29 | 330.3 | 0.22 | 180.77 |
| MRK | 2026-08-19 | −9.8 | 2.83 | 2.29 | 1 135.0 | 0.08 | 135.17 |

\* AMGN satırında plan `atr` alanı 0.0 (ölçülememiş görünüyor) — açık soru #4.

**Spearman (BETİMLEYİCİ — n=13, tek ay, hüküm değil):**

| vekil | vs işaretli bps | vs \|bps\| |
|---|---:|---:|
| menzil% (20 bar medyan H−L/C) | −0.149 | **+0.898** |
| ATR% (plan alanı) | −0.198 | **+0.824** |
| 1/ADV$ (ters likidite) | −0.566 | −0.132 |
| katılım (qty/ADV) | −0.265 | −0.359 |
| fiyat seviyesi | +0.368 | −0.203 |

**Okuma (betimleyici):**

1. **Friksiyonun BÜYÜKLÜĞÜ karar anında tahmin edilebilir görünüyor; İŞARETİ görünmüyor.**
   Oynaklık vekilleri (menzil%, ATR%) |bps| ile çok güçlü sıralı ilişkide; işaretli bps ile
   ilişkileri ~0. Yüksek-oynaklık satırlarının (menzil%≥3.8: MRVL, MRNA×2, CRM, HUM) işaretli
   toplamı +327−131−122−82−43 = **−51 bps ≈ nötr** — vahşi dolumların yarısı LEHTE.
2. **Naif likidite hipotezi bu örneklemde TERS:** en pahalı iki dolum evrenin en likit
   uçlarında (MRVL ADV$ 4.7 milyar, BKNG 1.1 milyar); en lehte dolumlar en az likit isimde
   (MRNA ~0.28-0.29 milyar). 1/ADV$ |bps|'i öngörmüyor (−0.13).
3. **Katılım nano ölçekte** (≤0.38 bps of ADV) — boyut-kaynaklı friksiyon kanalı bu kitapta ölü;
   ölçülen friksiyon zamanlama/mikroyapı/oynaklık kanallı. (MRNA 08-19 satırı olay günü
   ertesi: 08-19 barı açılış +%84, hacim 182.7M ≈ 56×ADV20 — in-play rejimi, açık soru #2.)

### 2b. Silahlı limit yasasının 13 gerçek dolum üzerindeki kesim seti (aritmetik, replay değil)

E2 satırları `entry_trigger` + `atr` + `limit` + `fill` taşıdığı için silahlı yasa
(limit_a = tetik + min(0.5·ATR, 0.01·tetik) — EXE-006/EDG-043'ün sınadığı nokta) satır satır
UYGULANABİLİR (yalnız "dolum fiyatı tavanı aşar mıydı" aritmetiği; **dolmama/ıskalama bedeli
bu aritmetikte YOK** — o bedel EDG-043'ün Δ'sında ölçülür):

| kesim | satırlar |
|---|---|
| **KESERDİ (n=4)** — dördü de ALEYHTE | EMR +54.6 · BKNG +134.5 · AMGN +15.0 · MRVL +327.5 → kesilen toplam **+531.6 bps** |
| **KESMEZDİ (n=9)** | kalan tüm satırlar — medyan **−9.8 bps**; hiçbir LEHTE dolum kesilmez |

Yani 043'ün tezindeki desen ("kapının kestiği şey tam olarak pahalı-dolum kuyruğu") gerçek
canlı dolumlarda birebir görünüyor: tavan yalnız aleyhte kuyruğu tıraşlıyor, lehte kuyruğa
dokunmuyor. n=13, betimleyici; EDG-043'ün altı CI'sının 0-içi olduğu gerçeği değişmez.

### 2c. Yan gözlem — E2 payda künyesi (Rol-1'e veri-kalite notu, hüküm değil)

E2 `resmi_acilis` değerleri, bugünkü canlı bar arşivinin SONRAKİ-SEANS açılışlarıyla
kıyaslandı (dolum bir sonraki açılışta gerçekleşir; `fill_kaydedildi` alanı doğruluyor):

- 13 satırın 5'inde fark tam 0.0; **6/13 satırda |fark| > 15 bps** (uçlar: NUE −54.2,
  BDX +27.9, EMR −27.7, MRK −21.2, AMGN +16.3, MRVL −16.0 bps).
- 08-05'in dört satırının E2 bps'leri (15.0/16.1/54.6/134.5; medyan 35.4, 4/4 aleyhte)
  EDG-037'nin **D0(IEX) sütunuyla birebir**; EDG-038'in kanonik D1 sayıları (−20.7/+26.8/
  +31.2/+134.5; medyan 29.0, 3/4) DEĞİL. Bugünkü arşiv açılışları AMGN 413.71 / EMR 164.32
  ise D1 türevleriyle uyuşuyor — yani arşiv sonradan D1'e onarılmış, E2 satırları reconcile
  anındaki paydayla donuk görünüyor (PIT tasarımının bilinçli sonucu; EDG-042 kill#1 koşum
  günü yeniden türetmeyi zaten yasaklıyor).
- Sonuç değil sayı: K1'in bugünkü medyanı (+15.017) tam da bu karışık-payda satırlarından
  birinin (AMGN) değeri. Payda D1'e taşınsaydı AMGN satırı +31.4 olurdu (bugünkü arşivle
  hesap). **Payda gürültüsü (≤54 bps) ölçülen büyüklükle aynı mertebede satırlar var** —
  EDG-038'in "ölçüt hatası ölçülen büyüklük mertebesinde" bulgusu E2 defterinin içinde de
  yaşıyor olabilir. K1 eşiği dolduğunda ne yapılacağı Rol-1/kart işidir (açık soru #1).

## 3. Aile tablosu

| # | Aile | Beslendiği veri — bugün var mı? | Replay'de sınanabilirlik (şasi noktası) | Canlı davranışı ne değiştirir | Ön-kanıt durumu (betimleyici) |
|---|---|---|---|---|---|
| **A1** | Beklenen-\|friksiyon\| SKOR terimi (ATR%/menzil% tabanlı yumuşak ceza) | **VAR**: `sig.atr` plan alanı; menzil% bars'tan türetilir; ek çekim gerekmez | Sıfır-ağırlık bileşen deseni (`entry.w_*`, varsayılan 0; çivi testleri korunur) — **yeni bileşen KOD ister**, sonra grid'den ağırlık noktası; kabul zaten skor-sıralı (backtest.py:438) → terim sıralamayı doğrudan değiştirir | Hangi isimlerin doğduğu (seçilim) — dormant_setup dersi: ne alıp sattığımız değişir, operatör kalemi | **ZAYIF/KARIŞIK**: ATR% \|bps\|'i öngörüyor (+0.82) ama işareti öngörmüyor (−0.20); yüksek-ATR% kuyruğun işaretli toplamı ≈ nötr (−51 bps). EMSAL ALEYHTE: EDG-031 — likidite-cinsi skor terimi (turnover w005/w010) seçilimi bozdu (ΔP&L medyan negatif, +R işlemler kaybedildi), "CI-pozitif değilse w=0" kuralıyla kapandı |
| **A2** | Likidite/ADV taban VETOSU (sert eşik: ADV$ tabanı, katılım tavanı sıkılaştırma) | **VAR**: `_adv` iki motorda da hesaplı ve dolum yasasına geçiyor | Uyuyan-veto düğme deseni (`entry.min_rvol`/`max_ext_atr` emsali, varsayılan 0=kapalı) — **yeni düğme KOD ister**; ya da `ADV_CAP_PCT` sıkılaştırması (mevcut sabit) | Hangi isimlerin doğduğu / hangi boyutta | **ALEYHTE**: 1/ADV$ \|bps\|'i öngörmüyor (−0.13); en pahalı dolumlar EN LİKİT isimlerde; katılım nano (≤0.38 bps) → boyut kanalı ölü. 251'lik büyük-isim evreninde muhtemelen İNERT |
| **A3** | EMİR-TİPİ politikası: pahalı-dolum kuyruğunu kesen limit tavanı (EDG-043'ün B kolu deseni) | **TAM VAR**: yasa motorda uyuyor (`entry_law` override, exe006 deseni); E2 defteri kesim setini satır-düzeyinde doğruluyor | **ZATEN ÖLÇÜLDÜ** — EDG-043 K=6 harcandı; A/B kol ayrımı + kapalı hücreler edg040 donmuş kanıtından; ek koşum ancak yeni kartla | Emrin fiyat tavanı (B4 operatör-karar çerçevesi kurulu; okuma kuralı EDG-042 bandına kilitli) | **EN GÜÇLÜ**: (i) EDG-043 B kolu üç slip'te de nokta-pozitif (slip15_B +895$, altı hücrenin tek kârlısı; ama 6 CI de 0-içi), (ii) bu keşfin 2b aritmetiği: silahlı yasa 13 gerçek dolumun tam 4'ünü keserdi — dördü aleyhte (+531.6 bps), sıfır lehte kayıp. Eksik: dolmama bedeli + 23c model boşluğu + EDG-042 bandı |
| **A4** | Friksiyon-ağırlıklı ISI/BOYUT (beklenen friksiyonla size_mult / ısı payı ölçekleme) | **VAR** (A1 ile aynı öngörücü) | `size_mult` argümanı iki motorda mevcut (derisk emsali) — isim-bazlı çarpan **KOD ister**; ısı yasası guard.py'de (iki motor tek yasa şartı) | Pozisyon büyüklüğü / ısı dağılımı (seçilim değil maruziyet) | **ZAYIF + ÇİFT-SAYIM ŞÜPHESİ**: işaret öngörülemezken \|bps\| öngörüsü varyans-azaltıcı boyutlamayı düşündürür, AMA stop=k·ATR → qty≈risk/(k·ATR) zaten yüksek-ATR isimde notional'ı küçültüyor (13 dolumun notional bandı dar: ~4.6-11k$). ATR-tabanlı ikinci bir ölçek çift-sayım olabilir — önce mevcut içselleştirme ölçülmeli |
| **A5** | DOLUM-YASASI kalibrasyonu (sabit slippage_bps=5 → koşullu/isim-bazlı model; seçilim değil ÖLÇÜM modeli ailesi) | **KISMEN**: E2 defteri birikiyor (K1 n=13; eşik 30) — kalibrasyon verisi EDG-042 hattından gelecek | `broker.py:414` skaler enjeksiyon noktası var; koşullu bps **motor değişikliği ister**; EDG-040 beyanlı sınır #1'i ("sabit-bps hasarı eksik sayar") kapatır | HİÇBİR ŞEY (canlı davranış değişmez) — replay hükümlerinin gerçekçiliği değişir | Ön-kanıt = bu belgenin 2. bölümü: bps ATR%'ye koşullu geniş dağılımlı; ama EDG-037 kill#1 ayakta — **n dolmadan motor sabiti değişmez** (kartın kendi yasası) |

Aileler dışlayıcı değil: A3 icra kanalını, A1/A2 doğum kanalını, A4 maruziyet kanalını tutar;
A5 hepsinin ölçüm zeminini düzeltir. Bugünkü kanıt ağırlığı sıralaması İSTATİSTİK DEĞİL
betimleyicidir ve Rol-1'i bağlamaz.

## 4. Kart-adayı eşik/kill ENVANTERİ (öneri değil envanter — donuk emsallerden derlendi)

**Ortak (hangi aile kartlaşırsa kartlaşsın, emsali donuk):**

- Şasi kapısı: knob-kapalı slip=5 koşumu `edg032b` ile bayt-özdeş, değilse DURUR (EDG-040/043 kill emsali).
- Slip öz-sınaması likidite-ayrıştırmalı, tolerans 1e-9 (edg040 kill#2'nin tamamlanmış hâli).
- Bootstrap damgası: replay kıyasında eşlenik ay-kümeli B=5000 seed 20260812 (55 ay); canlı-defter
  ölçümünde seans-kümeli (EDG-042 sapma beyanı emsali).
- Karar kuralı biçimi: **CI-alt > 0 değilse benimseme YOK** (EDG-031 "CI-pozitif değilse w=0" +
  EDG-043 Ö1 emsali); asimetri beyanı ölçümden önce yazılır.
- Kill: koşum sırasında motor dosyası sha/mtime değişimi → hücre geçersiz (EDG-033 dersi +
  EDG-043 olay şerhi: uçuşta commit yasağı).
- Kill: yasak modül (loop/counterfactual/cf_backfill/hermes) `sys.modules` kanıtı.
- Kill: bütünlük (frame_miss=0, dup=0, scan==plan).
- Kompozisyon ayrıştırması ZORUNLU ÇIKTI: işlem sayısı neden değişti — hasar/fayda FİYAT mı
  SEÇİLİM mi (EDG-040 zorunlu-ek-çıktı emsali).
- UYDURMA YASAĞI: ölçülemeyen vekil → satır None + neden; K grid'de çarpılarak sayılır.

**A1'e özgü envanter:**
- Çivi: w=0 iken skor bayt-özdeş (test_score_rebuild_v115 / test_turnover_kablolama_v149 deseni).
- Ölçülemeyen bileşende davranış ÖNCEDEN seçilir ve yazılır: "kurulum yok" (rvb/mom deseni) mı
  "terimsiz geç" (turnover fail-open deseni) mi — ikisi de emsalli, seçim kartta donmalı.
- K = ağırlık grid noktası sayısı (EDG-031'de 2 nokta = K+=2 emsali).
- Kill adayı: takas-ayrışımı raporu (giren/çıkan işlemlerin R dağılımı — EDG-031 mekanizma
  bulgusunun zorunlu çıktısı hâline getirilmesi).

**A2'ye özgü envanter:**
- Veto eşiği ölçümden ÖNCE donuk (ADV$ tabanı / katılım tavanı değeri grid'de sayılır).
- NO_GO sayaç ayrıştırması (illiquid vs diğer redler) zorunlu çıktı.
- Ölü-knob testi: eşik evrende hiç ateşlemiyorsa hücre "İNERT" damgalanır, sonuç boş sayılmaz
  (EDG-035 slot25 bayt-özdeş / EDG-034 Faz-0 "zaten öyle → dur" emsali).

**A3'e özgü envanter (fiilen EDG-043'te DONUK — buraya sayım için):**
- Okuma kuralı: hüküm yalnız EDG-042 gerçek-friksiyon bandına düşen slip hücresinden okunur;
  bant gelmeden B4 açılamaz (kill). Tavan TEK (0.01) — tarama yeni kart + K ister.
- Kol kimliği damgası (`dolum_kurali`) sonuçtan doğrulanır (exe006 Kritik-1).
- 23c şerhi kalıcı: B kolu iyimser alt sınır — "kapı iyi" hükmü tek başına canlıyı değiştirmez.

**A4'e özgü envanter:**
- Çift-sayım ön-ölçümü (Faz-0 adayı): mevcut 1/ATR boyutlamanın friksiyon-maruziyetini ne kadar
  içselleştirdiği — notional×beklenen-bps dağılımı; "zaten içselleşmiş → İNERT, dur" çıkışı
  (EDG-034 Faz-0 deseni).
- İki-motor tek-yasa şartı: ısı/boyut değişikliği guard+broker'da aynı yasadan okunmalı
  (test_differential emsali); yalnız replay'e konan çarpan kill'dir.
- Kill adayı: dd/uç-risk raporu zorunlu (boyut ailesi P&L'den önce kuyruk riskini oynatır —
  EDG-023 dd×2.287 emsali: dd kill'i otomatik hüküm engelleyebilmeli).

**A5'e özgü envanter (EDG-042 hattının devamı):**
- Örneklem eşikleri AYNEN: K1 n≥30 & ≥10 seans; K2/K3 n≥15 & ≥6 seans; altında betimleyici damga.
- EDG-037 kill#1 ayakta: eşik dolmadan `slippage_bps` GÜNCELLENMEZ; kalibrasyon fonksiyon formu
  (örn. bps = f(ATR%)) ölçümden önce ön-kayıtlı olmalı — "eğriye baktıktan sonra form seçme"
  EDG-038'in yaltaklanan-ölçüt tuzağının regresyon hâlidir.
- Payda künyesi kill adayı: satır satır payda kaynağı (hangi arşiv sürümü/feed) künyelenmeden
  kalibrasyon CI'sı yayımlanmaz (bu belgenin 2c gözlemi; eşiği Rol-1 koyar).

## 5. AÇIK SORULAR (hüküm yok — Rol-1/operatör)

1. **E2 payda karışımı (2c):** K1 eşiği dolduğunda CI hesaplanmadan önce satır-düzeyi payda
   denetimi (E2 değeri ↔ o günkü arşiv açılışı) istenecek mi? 08-05'in 4 satırı IEX-dönem
   paydası taşıyor görünüyor; medyanın kendisi (+15.017) bu satırlardan birinden. EDG-042
   kill#1 koşum-günü yeniden türetmeyi yasaklıyor (doğru), ama "payda künyesi" ayrı bir alan
   olarak defterde yok — bu bir kart/E2-şema kalemi mi?
2. **In-play/olay rejimi ayrı kova mı?** MRNA 08-19 (olay ertesi, hacim 56×ADV) ve MRVL
   (menzil %6.75) gibi satırlar friksiyonun vahşi ucunu taşıyor; postevent_inplay hattı
   (EDG-020) ile kesişim var. K1 tek kovada bunları normal girişlerle karıştırıyor —
   eşik dolunca alt-kova ayrımı (kartsız yapılamaz) gündeme gelir mi?
3. **A1/A4'ün A3'e karşı marjinal değeri:** |bps| öngörüsünün değere dönüşen tek asimetrik
   mekanizması şimdilik limit tavanı (2b: yalnız aleyhte kuyruğu keser). Skor/boyut aileleri
   aynı öngörücüden SİMETRİK kesinti yapar (lehte dolumları da kaybeder). A3'ün hükmü
   (EDG-042 bandı + muhtemel okuma) netleşmeden A1/A4 kartı açmak K israfı mı?
4. **AMGN `atr=0.0` satırı:** plan alanında ATR ölçülememiş görünüyor (silahlı yasa o satırda
   yalnız %1 koluyla çalışır). E2'de atr-ölçülemeyen satır oranı izlenmeli mi (YASA 6 okuyucusu:
   silahlı-yasa ölçümleri)?
5. **Short işaret sözleşmesi:** EDG-042'nin açık kalemi aynen geçerli — bugünkü örneklem 8/8
   long; short satır çıkarsa hem K2/K3 hem bu keşfin vekil işaretleri kartsız genişletilemez.
6. **Menzil% mi ATR% mi:** iki vekil neredeyse aynı bilgiyi taşıyor (+0.898 vs +0.824, n=13);
   ATR% planda DONMUŞ alan olduğu için PIT-temiz aday odur — ama seçim ölçümden önce kartta
   donmalı (payda-seçme serbestisi bırakılmaz).

## 6. Sınır beyanları

- Tüm korelasyon/kesim sayıları **n=13, tek ay (2026-08), tek rejim penceresi, BETİMLEYİCİ** —
  hiçbiri istatistiksel hüküm değildir; EDG-042'nin örneklem eşikleri bu belge için de bağlayıcıdır.
- Seçilim yanlılığı yapısal (EDG-042 beyanlı sınır #1): yalnız DOLAN emrin friksiyonu ölçülü;
  2b'nin kesim aritmetiği dolmama/ıskalama bedelini İÇERMEZ.
- ADV/menzil pencereleri plan tarihinden kesin önce 20 bar — karar-anı bilgi kümesinin alt
  kümesi (plan günü barı dahil edilmedi; dahil edilmesi sonuçları değiştirebilir, ölçülmedi).
- Bu belge hiçbir eşik DEĞİŞTİRMEZ, hiçbir yapılandırma ÖNERMEZ, kod YAZMAZ; §4 bir envanterdir,
  ön-kayıt değildir. Kartlaşma sırası/seçimi Rol-1 + operatördedir.
