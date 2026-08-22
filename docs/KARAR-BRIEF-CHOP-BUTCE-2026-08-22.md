# KARAR BRIEF — CHOP BÜTÇE-KAPALILIĞI: KASITLI POLİTİKA MI, YAN ETKİ Mİ? (2026-08-22)

**Karar mercii: OPERATÖR. Bu brief hüküm vermez** — iki okumanın kanıtını yan yana koyar,
her seçeneğin sonucunu somutlaştırır. Kaynak ölçüm: `research/olcumler/wp3_28d_kanit_2026-08-22/sonuc.json`
(28d teşhisi, K'sız betimleyici sayım); bu brief'in ek sayıları aynı dizinin türev verisinden ve
exe003 canlı-DB kopyasından üretildi (bkz. §6 veri kaynakları). ROADMAP kalemi: satır 195
("chop BÜTÇE-KAPALILIĞI — politika sorusu", 28d'den dönüştü).

---

## 0. Karar sorusu ve ölçülmüş mekanizma (özet)

Zincir (ölçülmüş, `sonuc.json` → `soru2_ayristirma`):

```
chop taban 45 (meridian/regime.py:127)
  − dd≥5 cezası 20 (meridian/regime.py:151-152)
  = 25 < min_exposure_score 40 (state/strategy.yaml:13)
  → exposure_budget_pct = 0
  → regime_ok False (meridian/backtest.py:382 · meridian/loop.py:1597)
  → chop planı kurulamaz → chop işlemi DOĞAMAZ → 28d kapısının @chop dilimi boş kalır
```

- 2022-01-03→2026-08-21: 1163 gün; 324 chop günü; **62'si girişe açık, 262'si kapalı** (kapalıların hepsi skor tam 25).
- Son açık chop günü **2025-06-12**; kapının son chop işlemi ts_open 2025-06-13 (birebir ertesi gün).
- Claim penceresi (2025-07-01+): 52 chop gününün **52'si kapalı**.

**SORU:** Bu kapalılık (A) kasıtlı politika mı ("chop'ta işlem istemiyoruz") — o zaman 28d kapısı
@chop dilimini beklemekten çıkarılır; yoksa (B) dd-cezasının yan etkisi mi — o zaman eşik kartı gerekir.

---

## 1. Okuma A — "kasıtlı politika": chop'ta işlem istememenin lehine kanıt var mı?

### 1.1 Chop-dilimi işlemlerin R dağılımı (defter, canlı DB kopyası; kaynak §6)

Defterdeki tüm işlemler `replay_seed` (885) + `live_paper` (8). **Canlı-kağıt hesabında chop
işlemi hiç yok (8/8 trend_up)** — bu, kapalılığın kendisinin sonucu. "5 canlı chop işlemi" =
canlı inc_cache'in global girdisindeki 5 chop-etiketli işlem (replay-tohumlu; 5/5 çapraz-doğrulanmış,
`sonuc_kapi_capraz.json`).

| Dilim | n | ort R | medyan R | toplam R | kazanma | p10/p90 | min/maks |
|---|---|---|---|---|---|---|---|
| Defter chop (tümü) | 95 | **+0.012** | **−0.221** | +1.17 | %36.8 | −1.03 / +1.82 | −1.72 / +5.75 |
| Kapının R1 arama @chop dilimi (ts_open 2024-01-11→2025-08-18) | 27 | **+0.094** | −0.101 | +2.54 | %37.0 | −1.03 / +2.22 | −1.06 / +3.46 |
| inc_cache 5 işlem (T, CHTR, LHX, WMB, DIS) | 5 | −0.089 | −0.101 | −0.45 | %20 | — | −1.01 / +1.66 |
| Kıyas: defter trend_up (replay) | 790 | +0.084 | −0.171 | +66.37 | %36.2 | −1.02 / +1.91 | −4.29 / +19.35 |

- pnl_pct ortalaması: chop **−0.47%/işlem** vs trend_up **+0.31%/işlem** (R ile işaret farkı
  pozisyon/stop ağırlıklamasından; ikisi de ham sayı, seçilmedi).
- Çıkış nedenleri (95 chop): regime_flip **40 (%42)** · stop 37 · target(+gap) 10 · time_stop 6 ·
  stop_gap 2 — işlemlerin beşte ikisi rejim dönünce yarıda kesiliyor (chop pencereleri kısa).
- Küme bazında toplam R: 2022-08 **−3.53** · 2022-11 −1.76 · 2022-12 −2.10 · 2023-01 −3.09 ·
  2023-02 **+9.11** · 2024-09 −0.53 · 2025-05 +1.30 · 2025-06 +1.77. (2022-08→2023-01 birikimli ≈ −10.5R;
  sonrası karışık-pozitif.)

### 1.2 Okuma A'nın kanıt durumu

**Lehine:** defter genelinde zayıflık işaretleri — medyan R negatif (−0.221), işlem başına pnl −0.47%,
%42 regime_flip kesintisi, 2022 kümeleri belirgin negatif.

**Aleyhine:** (i) Kapının kendi @chop örneklemi (27 işlem) ort R +0.094 — trend_up ortalamasıyla
(+0.084) aynı düzeyde; son üç küme (2023-02, 2025-05, 2025-06) toplam +12.2R. "Chop sistematik
kaybettirir" iddiası defterde desteklenmiyor; sinyal karışık ve örneklem küçük (95/27/5).
(ii) Repo'da beyan edilmiş bir "chop'ta işlem yok" politikası **bulunamadı** (None — arandı,
bulunamadı; niyet belgesi yok). Tersine iki tasarım işareti chop girişinin İSTENDİĞİNİ imler:
giriş whitelist'ine chop açıkça yazılmış (`backtest.py:382` ve `loop.py:1597`:
`regime in ("trend_up", "chop")`), ve chop tabanı 45 bilinçli olarak min_exposure_score 40'ın
ÜSTÜNE konmuş. Kapanma, iki bağımsız parçanın (taban − ceza) aritmetik kesişimi.
(iii) dd-cezasının kod yorumu genel risk azaltımı ("heavy distribution throttles exposure",
regime.py:152) — chop'a özgü bir hedef beyanı değil.

---

## 2. Okuma B — "yan etki": dd-cezası ile chop'un sistematik çakışması

Gün-serisi kaynağı: `research/olcumler/wp3_28d_kanit_2026-08-22/gunluk_rejim_canli.csv`
(1163 gün, canlı barlardan otoriter seri; kolonlar date/regime/budget/dd/score).

### 2.1 Ceza chop'a özgü mü? — HAYIR (seçici değil)

| Rejim | gün | dd≥5 gün | oran | ort dd |
|---|---|---|---|---|
| trend_up | 618 | 420 | %68.0 | 5.03 |
| chop | 324 | 262 | %80.9 | 6.60 |
| high_vol | 187 | 174 | %93.0 | 7.93 |
| trend_down | 34 | 34 | %100 | 7.03 |
| **toplam** | **1163** | **890** | **%76.5** | — |

- dd≥5 bu pencerede **varsayılan hâl** (%76.5). Chop-dd≥5 birlikteliğinin taban oranların ötesindeki
  ilişkisi **φ = 0.064** (2×2: 262/62/628/211) — pratikte sıfır. Ceza chop günlerini seçmiyor;
  hemen her yerde ateşliyor.
- "dd yükselince rejim chop'a mı düşüyor?" — nedensel sıra yönünde işaret YOK: 39 chop'a-geçişin
  **37'sinde dd hem geçiş günü hem önceki gün zaten ≥5**. dd ve chop aynı stres dönemlerinin
  eşzamanlı iki okuması; biri diğerini tetiklemiyor (bu seriden ayrıştırılamaz, öncelik ölçülemedi → None).

### 2.2 Ama cezanın KAPATMA gücü %100 chop'ta (asimetri — mekanizmanın kendisi)

Skor dağılımları (gün): chop {25: 262, 45: 62} · trend_up {60: 420, 80: 198} ·
high_vol {5: 174, 25: 13} · trend_down {0: 34}.

- **trend_up:** ceza 420 günde uygulanıyor → bütçe 80→60, **hiçbirini kapatmıyor** (60 ≥ 40).
- **high_vol / trend_down:** taban (25/15) zaten 40 altı; ayrıca giriş whitelist'i bu iki rejimi
  ADEN dışlıyor — ceza sonucu değiştirmiyor.
- **chop:** 45−20=25 < 40 — cezanın bütçeyi 0'a indirdiği TEK rejim. Kapanan 262 günün 262'si chop.

Yani: ceza genel-amaçlı ve seçicisiz; fakat eşik aritmetiği yalnız chop'ta 40 çizgisinin altına
düşürüyor. "Sistematik çakışma", korelasyondan değil **sabit aritmetikten** geliyor.

---

## 3. Seçenek A seçilirse → 28d kapısı @chop dilimini beklemekten çıkar (envanter)

Kapının fail-closed davranışı DOĞRU ve **kod değişikliği zorunlu değil**; değişen şey beklenti
(ROADMAP) + hipotez-üretim kapsamı. Etkilenen bileşenler:

| Bileşen | Yol | Bugünkü davranış | A'da ne olur |
|---|---|---|---|
| `@chop` hipotez sınıfı üretimi | `meridian/hermes.py:180` (şema `variable@regime` teşviki) · `hermes.py:4590-4610` (bg-sertifika çivilemesi `@chop`'a yazar) | `@chop` adayları üretilebiliyor; hepsi yapısal olarak ölçülemez ölüyor | Sınıf üretimden çıkarılmalı/duraklatılmalı — aksi hâlde her `@chop` turu israf + 28c-tipi tekrar gürültüsü |
| Notlandırma nüfusu | `meridian/reflect.py:170` `_eval_regime_of` | `var@chop` → yalnız chop işlemleriyle notlanır | Kod kalır; sınıf üretilmeyince ölü yol |
| Arama tabanı + None-ship + ölçülemedi | `reflect.py:580` (floor 21) · `:613` (OOS None → ship yok) · `:621-631` (law='olculemedi', fail-closed) | @chop burada ölüyor (canlı inc_cache: @chop graded 27 < min_sample 30 → score None) | Davranış AYNEN kalır (kapı gevşetilmez); beklenti kalkar |
| Teyit tabanı | `meridian/oos_pipeline.py:79-86` (floor 21; boş dilim → fail-closed red) | @chop confirm dilimi yapısal 0 işlem | Aynen kalır |
| Rejim-parametre haritası | `meridian/config.py:368` `params_by_regime={"chop": {}, ...}` | Boş (ROADMAP:1476 — kökü 28d ile aynı) | Kalıcı-boş kabul edilir; ROADMAP:1476 kalemi buna bağlanıp kapanış diline çevrilir |
| Rejim-ship geri-alma | `meridian/rollback.py:31` `_ship_eval_regime` | chop ship'i hiç olmadı | Dokunulmaz |
| ROADMAP kalemleri | ROADMAP.md:195 (politika sorusu) · :205 (28d teşhis) · :209 ve :650 (OPT Faz-2 → 28d bağımlılığı) | Faz-2, 28d'ye bağımlı bekliyor | Faz-2 bağımlılığı yeniden ifade edilmeli: kapı trend_up diliminde ÖLÇEBİLİYOR (canlı confirm 205 işlem, tamamı trend_up — `sonuc.json` soru3) |

Açık soru (operatöre): `@high_vol` ve `@trend_down` dilimleri de yapısal boş (bu rejimler
whitelist dışı, işlem hiç doğmaz). A kararı yalnız chop'a mı, "girişi yapısal-kapalı tüm rejim
dilimlerine" mi uygulanacak?

---

## 4. Seçenek B seçilirse → eşik kartı (aday envanteri, karar-odaklı tablo)

Ön-kayıt kartını Rol-1 yazar; eşik kartta donar. Aşağıdaki etkiler gün-serisinden birebir sayımdır
(324 = 2022+ tüm chop günleri; 52 = claim penceresi 2025-07-01+). **Cliff uyarısı:** chop skorları
yalnız {25, 45} olduğundan min_exp / ceza / taban adayları ya-hep-ya-hiç davranır; **tek kademeli
kaldıraç dd tetiğidir.**

| Aday | Bugün | Çapa | bounds? | Değer → açılan chop günü (324'te / 52'de) | Açılan günün bütçesi | Yan etki (chop dışı) |
|---|---|---|---|---|---|---|
| `regime.min_exposure_score` | 40 | `state/strategy.yaml:13` | **VAR** (`state/bounds.yaml:16`: 0-80, step 5) | 35: 62/0 · 30: 62/0 · **25: 324/52** (30-40 arası ölü bölge) | 25 (dd'li günlerde) | ≤25'te 13 high_vol gününde bütçe 0→25 olur; giriş whitelist'i high_vol'u yine dışlar — bütçenin giriş-dışı tüketicilerine etkisi bu brief'te ölçülmedi (None) |
| dd cezası TETİĞİ | dd≥5 | `meridian/regime.py:151` | **YOK** (kod sabiti) | 6: 95/3 · 7: 154/25 · 8: 213/43 · 9: 255/48 · 10: 298/52 · 13: 324/52 | 45 | **BÜYÜK:** tetik T'de dd∈[5,T) trend_up günleri cezasız kalır (bütçe 60→80): T=7'de 339 gün, T=10'da 420 gün — fren trend_up'ta da gevşer |
| dd cezası BÜYÜKLÜĞÜ | 20 | `meridian/regime.py:152` | **YOK** | 6-20 arası: 62/0 (değişmez) · **≤5: 324/52** | 40-45 | trend_up dd≥5 (420 gün) bütçesi 60→(80−P): P=5'te 75 |
| chop TABANI | 45 | `meridian/regime.py:127` | **YOK** | 50: 62/0 · 55: 62/0 · **≥60: 324/52** | B−20 (dd'li; B=60'ta 40) · dd'siz 62 günde B | **YOK — tek izole kaldıraç** (yalnız chop'u etkiler); dd'siz 62 açık günün bütçesi de 45→B yükselir |
| `goal.min_sample` (28d'nin kendi eşiği) | 30 | `state/goal.yaml:33` | — | **KALDIRAÇ DEĞİL:** 30→10 inse bile @chop confirm 0 açılmaz (ROADMAP-45 + `sonuc.json` soru3 sayımı) | — | — |

Not: dd cezası/tetiği/taban bounds'ta olmadığından B yolu muhtemelen kod+bounds işi de doğurur
(Opus brief'i, kart-sonrası); `min_exposure_score` ise bugün bile OPT/hermes'in oynatabileceği tek
kalemdir ama 30-40 arası ölü bölge nedeniyle kademesiz.

---

## 5. Kanıt ağırlığı yan yana (hüküm yok — karar operatörün)

| | Okuma A: kasıtlı politika | Okuma B: yan etki |
|---|---|---|
| İşlem kanıtı | Defter geneli zayıf: medyan R −0.221, pnl −0.47%/işlem, %42 regime_flip, 2022 kümeleri ≈ −10.5R | Kapının kendi @chop örneklemi ort R +0.094 ≈ trend_up (+0.084); son üç küme +12.2R; örneklem küçük |
| Tasarım niyeti | Yazılı politika beyanı YOK (bulunamadı) | Whitelist'te chop AÇIKÇA var (backtest.py:382, loop.py:1597); taban 45 > min_exp 40 bilinçli; ceza yorumu genel risk dili |
| Mekanizma | — | Ceza seçicisiz (%76.5 taban oranı, φ=0.064) ama kapatma gücü %100 chop'ta — sabit aritmetik kesişim |
| Karar sonrası iş | ROADMAP yeniden ifade + hermes @chop üretim kapsamı (kod değişikliği zorunlu değil) | Ön-kayıt kartı (Rol-1) + muhtemel kod/bounds işi; cliff yapısı nedeniyle gerçek kademe yalnız dd tetiğinde |

İki okuma birbirini tamamen dışlamaz: operatör "chop'ta işlem istemiyorum AMA bunun mekanizması
bilinçli bir kapı olsun, cezanın tesadüfi aritmetiği olmasın" da diyebilir (A'nın ROADMAP sonucu +
B'nin kod temizliği). Bu üçüncü yol da karta ihtiyaç duyar.

---

## 6. Veri kaynakları ve sınırlar (UYDURMA YASAĞI beyanları)

- **Ana ölçüm (yeniden ölçülmedi):** `research/olcumler/wp3_28d_kanit_2026-08-22/sonuc.json` +
  `sonuc_kapi_capraz.json` + `gunluk_rejim_canli.csv` (canlı barlardan otoriter gün-serisi).
- **R dağılımları:** exe003 canlı-DB kopyası `research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db`
  `trades` tablosu (kopya tarihi 2026-08-22; ssh sınıflandırıcı vekil emsali). Defter işlemleri
  `replay_seed` kaynaklı — **gerçek-zamanlı canlı chop işlemi hiç yok** (live_paper 8/8 trend_up);
  chop performans kanıtı bütünüyle replay-tohumlu geçmişten gelir, canlı icra kalitesini içermez.
- **Örneklem sınırı:** 95/27/5 işlem küçük; eşik taraması betimleyicidir, çoklu-kıyas düzeltmesi
  ve K sayımı YOKTUR — bu brief bir ölçüm kartı DEĞİLDİR, karar hazırlığıdır.
- **Ölçülemeyenler (None + neden):** (i) dd→chop nedensel önceliği — geçişlerin 37/39'unda dd
  zaten yüksek, eşzamanlılık ayrıştırılamıyor; (ii) exposure_budget_pct'nin giriş-dışı tüketicilerinde
  min_exp≤25'in high_vol yan etkisi — izlenmedi; (iii) yazılı politika niyeti — belge bulunamadı;
  (iv) chop işlemlerinin canlı-icra maliyeti — canlı chop işlemi hiç doğmadığından ölçülemez.
- Analiz betiği (tek seferlik, repo dışı): scratchpad `wp3_brief_analiz.py`; girdi olarak yalnız
  yukarıdaki iki dosyayı okur, hiçbir state'e yazmaz.
