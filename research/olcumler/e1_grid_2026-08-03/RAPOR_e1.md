# E1 İCRA GRID'İ — kart EXE-2026-001, ön-kayıtlı `parameter_grid` ölçümü

**Tarih:** 2026-08-03 · **Rol:** ölçüm ajanı · **Hüküm sahibi:** Rol-1
**Kart:** `research/cards/EXE-2026-001-entry-execution.yaml` — OKUNDU, DEĞİŞTİRİLMEDİ.
Aşağıda yalnız sayı, kaynak ve kapsam beyanı vardır; **hüküm cümlesi kurulmadı**, eşik
sonradan değiştirilmedi, grid genişletilmedi (6 hücre = kartın kendi listesi).

**Salt-ölçüm beyanı:** her kol kendi kum havuzunda koştu (`MERIDIAN_ROOT` + `config.STATE`
yönlendirmesi), gerçek `state/`e YAZILMADI (kanıt §7), canlıya (ssh) dokunulmadı, git komutu
koşulmadı, üretim dosyası değiştirilmedi.

---

## 0. NE ÖLÇÜLDÜ, HANGİ MOTORLA (iddia değil damga)

| kalem | değer |
|---|---|
| motor | `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/e1_grid/meridian` |
| motor .py dosya sayısı | 93 |
| depo `meridian/` ile bayt eşitlik (`diff -rq`) | rc=0 → **fark yok** |
| aynı motor karne-tazeleme ölçümünün motoruyla eşit mi | rc=0 → **evet** (o ölçümle KIYASLANABİLİR) |
| kollar arası TEK fark kaynağı | `state_<kol>/goal.yaml` → `execution_v2` bloğunun 2-3 satırı |
| goal.yaml'da değişen satır sayısı | her kolda ≤3 (geri kalan dosya bayt-aynı; `goal_diff_<kol>.txt`) |
| koşum yolu | deponun kendi `backtest.walk_forward`'ı (harness `kosum.py` + `kosum_kanca.py`) |

**Üretim kodu DEĞİŞTİRİLMEDİ.** Grid parametreleri kum havuzu `goal.yaml` kopyalarından verildi —
`broker.entry_law()` yasayı zaten YALNIZ `goal.yaml → execution_v2`'den okur (broker.py:70-101),
yani parametreyi oradan vermek yasanın kendi yoludur. Kanıt: her kolun çıktısındaki `entry_law`
bloğu (ana tablonun 3. satırı) ve `goal_diff_<kol>.txt`.

**R1 geometrisi (yedi kolda BİREBİR, karne_olcum/karne_tazeleme ile de aynı):** IS `2022-01-01` →
OOS `2024-01-01` → `2026-04-30` → holdout `2026-07-30`; foldlar `[2024-01-01, 2024-10-01,
2025-07-01, 2026-04-30]`; embargo 10. `strategy_version = 3` (`state/strategy.yaml:version`den
okundu, sabit yazılmadı). Evren: `REPLAY_UNIVERSE` 251 → **yüklenen 250**
(`FISV` için `state/bars/fisv.csv` YOK); replay takvimi 2022-01-03 →
2026-07-29; barlar canlı önbellekten SEMBOLİK BAĞ ile salt-okunur.

**Kollar:** kartın `parameter_grid`i 3 `limit_offset` × 2 `gap_davranisi` = **6 hücre**. Ek olarak
kart-DIŞI **1 referans** kol: `ref_limitsiz` — limit tavanı hiç bağlamayacak şekilde
(`limit_atr_mult=1000`, `limit_pct_cap=0,10` → limit = tetik×1,10 > `max_chase` tavanı tetik×1,04)
kurulmuş "eski koşulsuz-açılış" defteri. İkinci referans **ayrı bir kol değildir**: `B·mkt`
hücresi zaten bugünkü yürürlükteki varsayılandır. Bunlara ek olarak, referans kolonunun
DOĞRULANMASI için sekizinci bir kol koşuldu: `e1oncesi_eski` — **eski motor** (505603b kopyası,
`karne_olcum` ölçümünün kendi motoru ve state'i) + aynı limitsiz bayrak (§5).

---

## 1. GRID TABLOSU (6 hücre + referans)

| alan | A·mkt | A·cancel | B·mkt (VARSAYILAN) | B·cancel | C·mkt | C·cancel | REF·limitsiz |
|---|---|---|---|---|---|---|---|
| limit_offset | min(0,25·ATR14; %0,5) | min(0,25·ATR14; %0,5) | min(0,5·ATR14; %1,0) | min(0,5·ATR14; %1,0) | min(1,0·ATR14; %1,5) | min(1,0·ATR14; %1,5) | limit tavanı ETKİSİZ |
| gap_davranışı | marketable_limit | cancel | marketable_limit | cancel | marketable_limit | cancel | marketable_limit |
| (yasa: atr_mult · pct_cap) | 0,25 · 0,0050 | 0,25 · 0,0050 | 0,50 · 0,0100 | 0,50 · 0,0100 | 1,00 · 0,0150 | 1,00 · 0,0150 | 1.000,00 · 0,1000 |
| **dolum çağrısı → dolan** | **124 → 81** | **124 → 81** | **176 → 147** | **176 → 147** | **199 → 180** | **199 → 180** | **168 → 164** |
| **dolmama oranı (plan-bazlı)** | **0,3468** (%34,68) | **0,3468** (%34,68) | **0,1648** (%16,48) | **0,1648** (%16,48) | **0,0955** (%9,55) | **0,0955** (%9,55) | **0,0238** (%2,38) |
| · bunun limit-kaynaklı payı | 0,3065 | 0,3065 | 0,1307 | 0,1307 | 0,0603 | 0,0603 | 0,0000 |
| · ret nedenleri | entry_missed_limit 38· max_chase 2· open_below_stop 3 | entry_missed_limit 38· max_chase 2· open_below_stop 3 | entry_missed_limit 23· max_chase 3· open_below_stop 3 | entry_missed_limit 23· max_chase 3· open_below_stop 3 | entry_missed_limit 12· max_chase 4· open_below_stop 3 | entry_missed_limit 12· max_chase 4· open_below_stop 3 | max_chase 2· open_below_stop 2 |
| **net $ (replay defteri, 10bps)** | **-7.202,46$** | **-7.202,46$** | **-1.182,15$** | **-1.182,15$** | **-2.878,30$** | **-2.878,30$** | **+2.957,02$** |
| net $ — E3 kötümser ikiz | -7.830,84$ | -7.830,84$ | -2.045,61$ | -2.045,61$ | -3.997,61$ | -3.997,61$ | +1.958,81$ |
| · kötümser ek maliyet | +628,38$ | +628,38$ | +863,46$ | +863,46$ | +1.119,31$ | +1.119,31$ | +998,21$ |
| profit factor | 0,7074 | 0,7074 | 0,9646 | 0,9646 | 0,9259 | 0,9259 | 1,0828 |
| ödenen friksiyon $ | 1.259,87 | 1.259,87 | 1.735,61 | 1.735,61 | 2.249,19 | 2.249,19 | 2.009,15 |
| **PARA-v3 (search)** | **None** | **None** | **-0,0037** | **-0,0037** | **0,0581** | **0,0581** | **0,0965** |
| · search realize $ | -3.770,33$ | -3.770,33$ | -161,89$ | -161,89$ | +2.497,86$ | +2.497,86$ | +4.146,31$ |
| · search realize $ — kötümser | -3.897,08$ | -3.897,08$ | -546,28$ | -546,28$ | +1.832,69$ | +1.832,69$ | +3.673,19$ |
| **oos_score** | **None** | **None** | **0,0196** | **0,0196** | **0,0398** | **0,0398** | **0,0639** |
| · oos_score None ise NEDEN | 18/30 closed trades — score undefined (None, not 0.0) | 18/30 closed trades — score undefined (None, not 0.0) | — | — | — | — | — |
| is_score | 0,0557 | 0,0557 | 0,0651 | 0,0651 | -0,0060 | -0,0060 | 0,0616 |
| holdout_score | None | None | None | None | None | None | None |
| **n işlem (replay toplam)** | **81** | **81** | **147** | **147** | **180** | **180** | **164** |
| n işlem (OOS / search) | 18 / 18 | 18 / 18 | 75 / 61 | 75 / 61 | 111 / 92 | 111 / 92 | 90 / 72 |
| avg_r (OOS) | None | None | -0,0150 | -0,0150 | 0,0080 | 0,0080 | 0,0490 |
| win_rate (OOS) | None | None | 0,3330 | 0,3330 | 0,3600 | 0,3600 | 0,3890 |
| sharpe (OOS) | None | None | -0,0430 | -0,0430 | 0,1620 | 0,1620 | 0,2940 |
| **M2M maks-DD (tam pencere)** | **0,0853** | **0,0853** | **0,0739** | **0,0739** | **0,0745** | **0,0745** | **0,0723** |
| M2M maks-DD (mtm_dd_veto) | 0,0853 | 0,0853 | 0,0739 | 0,0739 | 0,0745 | 0,0745 | 0,0723 |
| maks-DD (kapanmış işlem, OOS) | None | None | 0,0735 | 0,0735 | 0,0740 | 0,0740 | 0,0718 |
| tam pencere toplam getiri | -0,0720 | -0,0720 | -0,0118 | -0,0118 | -0,0288 | -0,0288 | 0,0296 |
| işlem digest (16) | `35ade95809c1f406` | `35ade95809c1f406` | `4676800e30f1d90e` | `4676800e30f1d90e` | `f106441328df484c` | `f106441328df484c` | `0d9976ddbf409db2` |
| plan digest (16) | `7407193b0859f87d` | `7407193b0859f87d` | `e907ac6864525bcf` | `e907ac6864525bcf` | `5d690d82dbfe31f8` | `5d690d82dbfe31f8` | `62e0c03414e8a939` |
| plan n · kazanç-karartma vetosu | 702 · 0 | 702 · 0 | 639 · 0 | 639 · 0 | 662 · 0 | 662 · 0 | 619 · 0 |
| süre (sn) | 1.816,4 | 1.796,5 | 1.741,8 | 1.758,8 | 1.746,8 | 1.760,8 | 1.697,2 |

---

## 2. KILL#1 EŞİĞİ — DOLMAMA ORANI vs %40 (sayı, hüküm cümlesi YOK)

Kart `kill_criteria[0]`: *"limit-offset hiçbir grid noktasında dolum oranını kabul edilebilir
tutamıyorsa (dolmama >%40) tasarım geri döner"*. Payda beyanı: **`fill_entry` çağrısına ulaşan
plan sayısı** — yani silahlanmış, o gün barı olan, slot/kesici/`size_mult` kapılarını geçmiş plan.
(Bu paydanın seçimi ölçümün kendisidir ve burada yazılıdır; başka bir payda — ör. tüm GO planları —
başka bir oran verirdi.)

| hücre | dolmayan / çağrı | dolmama oranı | eşik %40 | fark (oran − 0,40) |
|---|---|---|---|---|
| A·mkt | 43 / 124 | **0,3468** (%34,68) | 0,40 | -0,0532 |
| A·cancel | 43 / 124 | **0,3468** (%34,68) | 0,40 | -0,0532 |
| B·mkt (VARSAYILAN) | 29 / 176 | **0,1648** (%16,48) | 0,40 | -0,2352 |
| B·cancel | 29 / 176 | **0,1648** (%16,48) | 0,40 | -0,2352 |
| C·mkt | 19 / 199 | **0,0955** (%9,55) | 0,40 | -0,3045 |
| C·cancel | 19 / 199 | **0,0955** (%9,55) | 0,40 | -0,3045 |
| REF·limitsiz | 4 / 168 | **0,0238** (%2,38) | 0,40 | -0,3762 |

Eşiğin okunuşu Rol-1'e aittir; bu rapor yalnız oranı ve farkı yazar.

---

## 3. `gap_davranisi` BACAĞI — YAPISAL ÖLÇÜM (iddia değil)

Grid'in ikinci bacağı (`marketable_limit` ↔ `cancel`) walk-forward replay yolunda **ölçülebilir bir
fark üretmez** ve bu bir varsayım değil, üç ayrı yerden ölçülmüş bir olgudur:

1. **Argüman ölçümü.** `fill_entry`e geçen `gap_at_submit` değerlerinin dağılımı (B·mkt kolu,
   tüm kollarda aynı): çağrı 176 · `None` **176** · `True`
   0 · `False` 0.
2. **Kaynak.** `backtest.replay` `fill_entry`i `size_mult / adv / pivot / atr / reject_out` ile
   çağırır (backtest.py:232-236); `gap_at_submit` argüman listesinde YOKTUR → varsayılan `None`.
   `broker.fill_entry` gap vetosunu `if gap_at_submit and _law["gap_behavior"] == GAP_VETO` ile
   kurar; `None` bu dala giremez. Bu, broker.py'de BEYAN EDİLMİŞ bir kapsam farkıdır
   (*"None = 'bu motorda gönderim anı YOK' (replay) ve veto ateşlemez"*).
3. **Defter ölçümü.** Aynı `limit_offset`in iki gap noktası BİREBİR aynı defteri üretti:

| çift | işlem digest eşit | plan digest eşit | equity digest eşit | net $ (mkt / cancel) | entry_gap_veto reddi |
|---|---|---|---|---|---|
| a_mkt_vs_a_cnl | **EVET** | EVET | EVET | -7.202,46$ / -7.202,46$ | 0 / 0 |
| b_mkt_vs_b_cnl | **EVET** | EVET | EVET | -1.182,15$ / -1.182,15$ | 0 / 0 |
| c_mkt_vs_c_cnl | **EVET** | EVET | EVET | -2.878,30$ / -2.878,30$ | 0 / 0 |

**Kapsam beyanı (bu ölçümün SÖYLEYEMEDİĞİ):** `cancel` noktasının etkisi burada **ölçülemedi
(None)** — replay motorunda gönderim anı yoktur. Bacağın ölçülebileceği iki yer üretimde vardır ve
ikisi de bu ölçümün dışındadır: canlı `loop.py:824` (gerçek gönderim anı) ve `intraday_shadow.py:301`
(gölge defteri, plan yan tablosundaki `entry_law.gap_at_submit` alanından). Kartın bu bacağı için
"6 hücre koşuldu" cümlesi doğrudur; "6 farklı sonuç ölçüldü" cümlesi **yanlış olurdu**.

---

## 4. KAÇAN DOLUMLARIN SONRADAN-GETİRİSİ (betimleyici — "kaçan kâr" DEĞİL)

İki bağımsız betim, ikisi de hüküm vermez:

* **(a) hipotetik koşulsuz-açılış getirisi** — ham barlardan: giriş = o günün AÇILIŞI (limitsiz
  motorun ödeyeceği fiyat), çıkış = h seans sonraki KAPANIŞ; R-benzeri = (kapanış−açılış) /
  (açılış−stop). Çıkış mantığı (trail/breakeven/chandelier/giveback/regime_flip/scale_out),
  friksiyon ve portföy kısıtı **UYGULANMAZ**. İkinci bir icra/çıkış modeli KURULMADI.
* **(b) limitsiz koldaki gerçekleşen karşılık** — aynı (sembol, tarih) `ref_limitsiz` kolunun
  defterinde açıldıysa onun GERÇEKLEŞEN R/$ değeri. **Yol-bağımlıdır**: limitsiz kolun portföyü
  farklı bir yol izler; eşleşmeyen kaçan plan o kolda slot/ısı/eş-anlılık yüzünden hiç açılmamış
  olabilir. Temiz bir karşı-olgu değildir.

| hücre | kaçan (limit) n | hipotetik ret_10 ort | hipotetik R_10 ort | hipotetik R_10 toplam | R_10 poz. oran | limitsiz kolda eşleşen n (kapsama) | eşleşenlerin gerçekleşen ΣR | eşleşenlerin gerçekleşen Σ$ |
|---|---|---|---|---|---|---|---|---|
| A·mkt | 38 | 0,0172 | 0,2265 | 8,6074 | 0,6053 | 23 (0,6053) | 8,6680 | +5.016,25$ |
| A·cancel | 38 | 0,0172 | 0,2265 | 8,6074 | 0,6053 | 23 (0,6053) | 8,6680 | +5.016,25$ |
| B·mkt (VARSAYILAN) | 23 | 0,0132 | 0,2577 | 5,9281 | 0,5217 | 15 (0,6522) | 4,5610 | +4.014,58$ |
| B·cancel | 23 | 0,0132 | 0,2577 | 5,9281 | 0,5217 | 15 (0,6522) | 4,5610 | +4.014,58$ |
| C·mkt | 12 | -0,0214 | -0,0848 | -1,0174 | 0,4167 | 10 (0,8333) | 1,4610 | +1.336,24$ |
| C·cancel | 12 | -0,0214 | -0,0848 | -1,0174 | 0,4167 | 10 (0,8333) | 1,4610 | +1.336,24$ |

Ufuk h=10 seans gösterildi; h=5 ve h=20 özetleri `sonuc_e1.json → tablo[].kacan_*` ve kol
dosyalarındaki `kacan_dolum` bloğundadır (satır satır defterle birlikte).

---

## 5. DETERMİNİZM KAPISI

**Birincil (bağlayıcı).** `B·mkt` hücresi = bugünkü yürürlükteki yasa; girdileri
(motor, `strategy.yaml`, `bounds.yaml`, `goal.yaml`, `bars_integrity.json`, `earnings.csv`)
karne-tazeleme ölçümünün `guncel` koluyla **bayt-aynıdır**, dolayısıyla o kolu BİREBİR üretmesi
gerekir:

| imza | karne_tazeleme `guncel` (2026-08-03) | bu ölçüm `B·mkt` | eşit |
|---|---|---|---|
| işlem digest (tüm) | `4676800e30f1d90e` | `4676800e30f1d90e` | EVET |
| işlem digest (search) | `3e054b7e23f0e595` | `3e054b7e23f0e595` | EVET |
| plan digest | `e907ac6864525bcf` | `e907ac6864525bcf` | EVET |
| equity digest | `5772bc9251a19d21` | `5772bc9251a19d21` | EVET |
| oos_score | 0,0196 | 0,0196 | — |
| PARA-v3 (search) | -0,0037 | -0,0037 | — |
| n işlem | 147 | 147 | — |
| replay defteri net $ | -1.182,15$ | -1.182,15$ | — |

**KAPI: digest eşitliği = EVET · skor eşitliği = EVET.**

**İkincil (referans kolonunun yeniden üretimi).** "Eski koşulsuz-açılış defteri" bu depoda
`karne_olcum` ölçümünün `e1_oncesi_icra` kolu olarak zaten ölçülüydü. İki ayrı kol koşuldu:

* `REF·limitsiz` — **bugünkü** motorla, aynı bayrak yolu. Digest eşitliği BEKLENMEZ: o kol
  505603b motoruyla ve 2026-08-01 state'iyle koşmuştu. Ölçülen: digest eşit =
  HAYIR (`995f1d33a8b8a719` ↔
  `0d9976ddbf409db2`).
* `e1oncesi_eski` — **eski** motorla (505603b kopyası) + o ölçümün kendi state'i + aynı bayrak.
  Bu kolun görevi digest'i BİREBİR doğrulamak ve böylece `REF·limitsiz` ile arasındaki farkı
  TEK DEĞİŞKENE (motor 505603b → HEAD) indirmektir.

| imza | `karne_olcum` kaydı | `e1oncesi_eski` (yeniden üretim) | `REF·limitsiz` (bugünkü motor) |
|---|---|---|---|
| işlem digest (tüm) | `995f1d33a8b8a719` | `995f1d33a8b8a719` | `0d9976ddbf409db2` |
| plan digest | `b5390efe9f241786` | `b5390efe9f241786` | `62e0c03414e8a939` |
| equity digest | `ea6777ea1b70bf08` | `ea6777ea1b70bf08` | `62a30c58529f17f4` |
| oos_score | 0,0699 | 0,0699 | 0,0639 |
| is_score | 0,0616 | 0,0616 | 0,0616 |
| PARA-v3 (search) | 0,0856 | 0,0856 | 0,0965 |
| n işlem | 161 | 161 | 164 |
| n işlem (OOS) | 88 | 88 | 90 |
| replay defteri net $ | (kayıtta yok) | +2.804,21$ | +2.957,02$ |
| dolan / çağrı | (kayıtta yok) | 161 / 165 | 164 / 168 |
| kazanç-karartma vetosu (plan) | (kayıtta yok) | 1 | 0 |

**`e1oncesi_eski` ↔ `karne_olcum` digest eşitliği: EVET** — yani grid-dışı referans kolon bu turda yeniden ÜRETİLDİ, alıntılanmadı.

İki limitsiz kol arasındaki TEK değişken motordur (505603b → HEAD). Ölçülen fark: n işlem 161 → 164; işlem kümesi ortak 144, yalnız eskide 17, yalnız bugünde 20; kazanç-karartma vetosu 1 → 0 plan (replay-PIT düzeltmesi 89d4497'nin doğrudan izi). Fark burada BETİMLENİR; hangi kalemin ne kadarını açıkladığı yol-bağımlılık yüzünden tek tek AYRIŞTIRILAMAZ ve bu ölçümün kapsamı dışındadır.

**Kolun kendi iddiası ölçüldü:** `REF·limitsiz`te `entry_missed_limit` reddi =
**0** (limit tavanı hiç bağlamadı — karne_olcum'un aynı
iddiası da 0 ölçmüştü).

Ek çapraz kontrol (her kolda): kancanın saydığı ret nedenleri ile motorun KENDİ sayacı
(`BacktestResult.entry_rejects`) eşit mi → A·mkt: EVET, A·cancel: EVET, B·mkt (VARSAYILAN): EVET, B·cancel: EVET, C·mkt: EVET, C·cancel: EVET, REF·limitsiz: EVET.

---

## 6. ZORUNLU BEYANLAR (okuma bunlar olmadan yapılamaz)

1. **`bars_integrity` `dataset.load` yoluna BİLEREK bağlı DEĞİLDİR.** Kirli dönemler replay'de
   GÖRÜNÜR; operatör kararı bekliyor. Walk-forward kollarında `rows_excluded = 0`'dır — o yol
   `measurement_bars`ı hiç çağırmaz (kol çıktılarındaki `veri_kapilari.integrity_report`).
   Bu, yedi kolun HEPSİ için aynıdır, yani hücreler arası kıyası bozmaz.
2. **Survivorship (hayatta-kalan evren).** Replay evreni bugünün sağ-kalan 250
   sembolüdür; delist olmuş isimler defterde YOKTUR. Yönün ilk ölçülmüş sayısı EDG-2026-021
   kartından (betimleyici, vekil-delist %18,6 sembol-payı): @20 tüm +0,48 · hayatta +0,54 ·
   delist −1,46. Bu tablodaki getiriler o yanlılığı TAŞIR ve büyüklüğü bu veriyle ölçülemez.
3. **Replay iyimserliği ≈ +0,018 (motor sapması).** ROADMAP.md:473'te kayıtlı; backtest skorları
   bu payı içerir. Bu turda yeniden ölçülmedi.
4. **cf sadakat sınırı.** `cf.advance` yalnız `stop_gap/target_gap/stop/target/time_stop` simüle
   eder (`analytics.CF_SIM_EXITS`); canlı motorun 6 çıkış mekanizması ve 5 friksiyon kalemi
   UYGULANMAZ. Ölçülmüş sapma (canlı defter, 2026-07-28): n=89 çift, corr 0,935, ortalama fark
   **+0,039R** (pozitif = simülasyon iyimser). Bu turda cf defteri KOŞULMADI; sınır, §4'ün (a)
   betimine EVLEVİYETLE uygulanır — orada çıkış mantığı hiç yoktur.
5. **E2 gerçek-slipaj bu ölçümle ÖLÇÜLEMEZ — None.** Kartın (b) başarı ölçütü canlı dolum verisi
   ister (`fill − resmî açılış`). Ölçülen durum: `state/entry_execution.jsonl` **yok**,
   `state/trades.jsonl` 95 satırın **95'inde `alpaca_fill_price` yok**,
   `analytics.pessimistic_band_update` ampirik bandı hâlâ `None` döndürür (n eşiği dolmadı).
   Bu grid REPLAY defteridir; kaçan/dolan ayrımını ölçer, ÖDENEN FİYATI ölçmez.
6. **E3 kötümser bandı RAPOR YÜZEYİDİR, karar değil.** İkiz sütun üretim fonksiyonlarıyla
   hesaplandı (`analytics.pessimistic_band` + `analytics._kotumser_ek_dolar`), band
   `goal.pessimistic_band_v2` (açılış spread 20,0 bps, yürürlükteki
   model 10,0 bps → ek **5,0 bps** yalnız
   GİRİŞ bacağına; taban `literatur`). `ampirik_bps` **None**'dır
   (E2 defteri boş, n=0) — literatür tabanı kullanıldı ve bu
   satırda yazılıdır. Hiçbir kapıya girmez (`hukme_girmez: true`).
7. **Holdout skoru yedi kolda da `None`** (kapanmış işlem < 30) — sıfır değil, tanımsız.
8. **PARA-v3 yasası değişmedi:** `shadowlaw.py`/`score.py` tüm kollarda aynı motordan gelir.
   Skor farkı yasadan değil, yasaya giren işlem defterinden gelir.
9. **Yol-bağımlılık.** Kaçan tek dolum, o günün slot dolumunu ve ertesi günlerin aday sıralamasını
   değiştirir; hücreler arası n farkı ayrı kararların toplamı değil, **bir kararın zincirlemesidir**.

---

## 7. YENİDEN ÜRETİM ve SALT-ÖLÇÜM KANITI

```
# kum havuzu (motor kopyası + kol başına state kopyası + bars/research SEMBOLİK BAĞ)
python kur.py                      # -> meridian/ + state_<kol>/ + kod_damgasi.json + goal_diff_*.txt
python parmakizi.py once           # gerçek state/ parmak izi (ÖNCE)
python kosum.py <kol>              # kol ∈ {a_mkt,a_cnl,b_mkt,b_cnl,c_mkt,c_cnl,ref_limitsiz}
                                   # (7 kol PARALEL koşuldu; her biri kendi state_<kol>/'una yazar)
cd eski_motor && python kosum.py e1oncesi_eski   # referans doğrulama kolu (505603b motoru)
python karsilastir_e1.py           # -> sonuc_e1.json
python parmakizi.py sonra          # gerçek state/ parmak izi (SONRA)
python rapor_yaz.py                # -> RAPOR_e1.md (tablolar sonuc_e1.json'dan üretilir)
```

Gerçek `state/` ağacının tam parmak izi (yol → mtime+boyut) koşumlardan önce ve sonra alındı:

| | dosya | parmak izi sha256(16) |
|---|---|---|
| önce | 608 | `7fa53ebf8c11e567` |
| sonra | 608 | `7fa53ebf8c11e567` |

Değişen dosya **0**, yeni **0**, silinen
**0**. Yazılan her bayt `<sandbox>/state_<kol>/` altındadır. `serve.sh`
koşulmadı, ssh kullanılmadı, git komutu çalıştırılmadı, kart dosyasına dokunulmadı.

Bu dizindeki dosyalar: `sonuc_e1.json` (makine-okunur tam sonuç), `kod_damgasi.json`,
`state_parmakizi_sonra.json`, `goal_diff_<kol>.txt` (kolların tek-fark kanıtı) ve koşum betikleri
(`kur.py`, `kosum.py`, `kosum_kanca.py`, `karsilastir_e1.py`, `rapor_yaz.py`, `parmakizi.py`,
`duman.py`). Kol JSON'ları (`kol_<kol>.json`, ~1 MB × 8) kum havuzunda kalır; içlerinde ham
defterler (`_trades_tum`, `_plan_log`, `_fill_cagrilari`, `_equity`) ve kaçan-dolum satır
defteri (`kacan_dolum.satirlar`) vardır. Kum havuzu yolu:
`/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/e1_grid`.
