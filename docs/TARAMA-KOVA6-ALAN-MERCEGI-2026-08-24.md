# TARAMA — KOVA-6 · KATMAN-4 ALAN MERCEĞİ (plan defteri)

**Ölü-mekanizma avının ALTINCI kovası. M11 kalemi.** Okuyucusu: Rol-1 + operatör (YASA 6 tamam).
Bu tur **SALT ÖLÇÜM + BELGE**: `meridian/` altında hiçbir dosya değişmedi, git koşulmadı, canlıya
dağıtım yapılmadı, `serve.sh` koşulmadı, broker'a emir gönderilmedi, canlıya yalnız **salt-okuma
SSH** ile bakıldı. Yazılan tek dosya budur. **K=0** (grid yok, hipotez yok, ön-kayıt kartı yok —
kova-4/5 emsali).

**Neden var.** `docs/ARTEFAKT-TARAMASI-2026-08-07.md:492-493` kendi ölçülemeyenler listesinde şunu
beyan etmişti: *"Alan (KATMAN-4) merceği YALNIZ `dormant_setup`'a uygulandı… plan/aday
defterlerindeki diğer ~20 kontrol alanı bu mercekten GEÇİRİLMEDİ. Sınıfın envanteri AÇIKtır."*
Ara dönemde sınıfın DEĞERİ kanıtlandı (uyuyan-yol + `broker_status` ölü-dalı, `watchdog.py:552-560`
şerhi). Bu belge o envanteri kapatır — **hüküm vermez**, ölçer.

---

## 0. KAPSAM VE ÖLÇÜM YÜZEYİ

**Alan evreni.** "Plan defteri" tek bir dosya değil, **üç yüzeydir** ve bu ayrım hükmü değiştirir:

| Yüzey | Nerede yaşar | Ömür |
|---|---|---|
| **DEFTER** | `trade_plans.jsonl` → SQLite `trade_plans` (500 satır tavanı) | tarihsel |
| **SİLAHLI** | `portfolio.json` → `armed[]` (SQLite `portfolio.doc_json`) | seans(lar) arası ÇALIŞMA kümesi |
| **YASA** | `portfolio.json` → `entry_law[plan_id]` yan tablosu | silahlı planın icra girdileri |

Bir alan DEFTER yüzeyinde ölü, SİLAHLI yüzeyinde canlı olabilir (`strategy_version` tam böyle).
Tek yüzeye bakan bir mercek yanlış hüküm verir; tablo bu yüzden "yüzey" sütunu taşır.

**Taranan kod.** `meridian/*.py` (86) + `meridian/adapters/*.py` (13) AST ile; `meridian/web/*.js`
hedefli grep ile; `tests/` + `ops/` + `research/` yalnız **bilinen-negatif kapısı** için (bkz. §2.4).

**Canlı ölçüm (salt-okuma SSH, `mode=ro` SQLite URI, 2026-08-23):**
`/opt/meridian/state/meridian.db` → `trade_plans` **500** satır (2025-07-02 → 2026-08-21),
`trades` **893**, `portfolio.armed` **2**, `positions` **7**, `entry_law` **2**;
`entry_execution.jsonl` **30** satır; `events.jsonl` **76.492** satır (2026-07-14 → 2026-08-23).

---

## 1. YÖNTEM — KATMAN-4 MERCEĞİ (v1 → v3)

Emsalin üç katmanına (ÜRETİCİ / OKUYUCU / DAVRANIŞSAL TÜKETİCİ) alan granülaritesinde sorulan
üç soru:

1. **ÜRETİLİYOR mu** — kim yazıyor (dosya:satır) ve **canlı veride dolu mu** (kodla değil VERİYLE).
2. **OKUNUYOR mu** — davranışa giren okuyucu var mı (AST + grep). *Pano-görüntüsü OKUYUCU SAYILIR*
   ama "davranış" sütununda ayrılır.
3. **DAVRANIŞ DEĞİŞTİRİYOR mu** — okunan değer bir dala / eşiğe / emre / kapıya / alarma giriyor mu.

Dört sınıf: **CANLI-BAĞLI · YALNIZ-GÖRÜNÜRLÜK · ÖLÜ** (üretiliyor, okunmuyor) **· HAYALET**
(okunuyor ama üretilmiyor / hep None).

**Araç.** `ast` tabanlı; `Subscript(Constant(str))` + `.get("alan")/.pop/.setdefault` erişimleri
bulunur, her erişim için (a) YAZIM mı okuma mı, (b) bir **test bağlamında** mı
(`If.test/While.test/IfExp.test/Assert/comprehension.ifs`), (c) davranışsal çağrı argümanı mı
(`alarm/notify/submit_order/cancel_order/submit_plan/submit_bracket/set_halt/…`), (d) bir isme
atanıp o isim dalda mı kullanılıyor (tek adım taint) sorulur. Araç oturum-içidir ve repoya
YAZILMADI (scratchpad'te kaldı) — kalıcı bir bekçi haline getirmek Rol-1'in kararıdır (§7).

### 1.1 YÖNTEMİN İKİ ONARIMI (kalibrasyonun zorunlu kıldığı)

| # | Onarım | Neyi çözdü |
|---|---|---|
| **R1** | **Yüzey ayrımı: DİSKTEN okunan dal ↔ AYNI TURUN BELLEK İÇİ dalı.** Bir dal, değeri o fonksiyonda kurulmuş bir sözlükten okuyorsa "davranış" saymaz; değer `store.read_jsonl("trade_plans.jsonl")` / `read_json("portfolio.json")` yolundan geldiyse sayar. | Kalibrasyon (a) — `dormant_setup` (bkz. §2.1) |
| **R2** | **Değer-düzeyi çapraz kontrol.** Kapalı sözcük dağarcığı olan alanlarda ÜRETİLEN değerler ile TÜKETİLEN string literalleri **kanal kanal** karşılaştırılır (plan alanı ≠ olay adı ≠ pano etiketi). | Kalibrasyon (b) — `broker_status` ölü-dalı (bkz. §2.2) |

### 1.2 YÖNTEMİN BİLİNEN KALINTI KUSURLARI (beyan — gizlenmedi)

1. **Sabit-dolayımlı anahtar körlüğü.** `operator_onayi` erişimleri `ONAY_ALANI` SABİTİ üzerinden
   yapılır (`loop.py:452`); AST tarayıcısı literal anahtar aradığı için alanı **0 hit** ile
   raporladı. Elle grep ile 8 erişim bulundu ve envantere katıldı. *Aynı desendeki başka bir alan
   varsa bu tarama da onu kaçırır.* (Emsalin Y-2/Y-3 arızasının alan-düzeyi kardeşi.)
2. **Ad çakışması.** `id · date · ticker · side · score · setup · stop · sector · targets` adları
   işlem satırı / pozisyon / aday / Alpaca emri sözlüklerinde de var. Bu dokuz alanın her okuyucusu
   **elle** bağlamıyla doğrulandı; mekanik sayım tek başına kova belirlemedi.
3. **Pano çizim doğrulaması kaynak koddan.** `web/app.js` satırları OKUNDU ama tarayıcıda
   çalıştırılıp çizildiği GÖRÜLMEDİ (yerel görsel doğrulama bu turun kapsamı dışı).
4. **Tek adım taint.** Emsalin çok-atamalı zincir onarımı (Y-1) burada YALNIZ tek adım uygulandı;
   dalsız çıkan HER alan elle okundu, ama derin zincirli bir davranış bağını kaçırma riski sıfır
   değildir. Bu riskin yönü **yanlış-ÖLÜ** iddiadır — §2.4 kapısı tam bunun içindir.

---

## 2. KALİBRASYON KAPISI — SONUÇ: **1/3 → onarımdan sonra 3/3**

Brief üç bilinen vakayı şart koştu. **Kalibrasyon geçmeden gerçek tarama SAYILMAZ** — bu bölüm
yöntemin ilk hâlinin DÜŞTÜĞÜNÜ kayda geçirir.

| Vaka | Beklenen | v1 (ham AST) | Onarım | Son hüküm |
|---|---|---|---|---|
| **(a)** `dormant_setup` | YALNIZ-GÖRÜNÜRLÜK (disk) | ❌ **DÜŞTÜ** — 5 dal bulundu → CANLI-BAĞLI derdi | **R1** (yüzey ayrımı) | ✅ YALNIZ-GÖRÜNÜRLÜK |
| **(b)** `broker_status` ölü-dalı | ölü-dal sınıfını YENİDEN BULMALI | ❌ **DÜŞTÜ** — bugünkü sınıfı (görünürlük) doğru der ama ölü-dalı **göremez**: tüketici alanı değil, alanın DEĞERİNİ başka bir kanalda arıyordu | **R2** (değer-düzeyi çapraz kontrol) | ✅ sınıf yeniden bulundu **+ aynı sınıfta CANLI bir örnek** (§2.2) |
| **(c)** `gate_verdict` (seçilen CANLI-BAĞLI) | CANLI-BAĞLI | ✅ geçti | — | ✅ CANLI-BAĞLI |

**Yani yöntem ilk hâliyle 1/3'tü.** Aşağıdaki bütün hükümler **onarılmış (v3)** merceğin çıktısıdır.

### 2.1 Vaka (a) — `dormant_setup`

| Katman | Ölçüm |
|---|---|
| YAZAN (disk) | `loop.py:1822` · `cf_backfill.py:117` · `mutation.py:188` · `shadow_variants.py:218` · şema `storage.py:90` |
| DALLANAN — ama **AYNI TURUN BELLEK İÇİ** | `loop.py:1933 if plan["dormant_setup"]:` · `loop.py:1814` (kimlik) · `loop.py:1979` (gerekçe metni) · `cf_backfill.py:143` · `cf_backfill.py:109` |
| DİSKTEN OKUYAN | `counterfactual.py:149` (`"dormant"` diye YENİDEN ETİKETLER) · `web/app.js:9202` ("Uyuyan kurulum: evet") |
| DİSKTEN OKUYUP **DAVRANAN** | **YOK** |

**Canlı (2026-08-23):** 500 planın **25**'i alanı taşıyor (**8** tanesi `1`), **475**'i NULL (alan
eklenmeden önceki satırlar). `hermes.py:1032 dormant_setup_evidence` alanı DEĞİL, cf defterinin
türetilmiş `dormant` alanını okur — yeni bir davranışsal bağ **açılmamış**. Emsalin 08-08 hükmü
bugün de geçerli.

### 2.2 Vaka (b) — `broker_status` ve **değer-düzeyi** ölü dal

Ölü dal şuydu (`watchdog.py:552-560` şerhi): korunum raporu `failed_broker_rejection` adlı bir
**OLAY** arıyordu; o ad hiçbir zaman olay olarak yayınlanmadı — `loop.py` onu yalnız **plan ALANI**
olarak yazar. Alan-düzeyi mercek bunu göremez, çünkü kusur alanın *değerinin başka bir kanalda*
aranmasıydı. R2 bunu yakalar ve **bugün canlı olan aynı sınıftan bir örnek** buldu:

| Üretilen değer | Üretici | Tüketici (herhangi bir kanalda) |
|---|---|---|
| `failed_broker_rejection` | `loop.py:830`, `loop.py:852` | `web/app.js:1218/2499/9203` (rozet "RET") |
| `gap_veto` | `loop.py:813` | **HİÇBİRİ** (ne Python ne JS) |
| `armed_dropped_<kapı>` | `loop.py:331-332` | **HİÇBİRİ** |

**Sonuç (ölçüm, hüküm değil):** panonun tek eşleşmesi `failed_broker_rejection`'dır; `app.js:1218`
diğer HER değeri `else` dalında **"gönderilecek"** (nötr/olumlu rozet) diye çizer ve `app.js:2499`
onları `bekleyen` sayacına yazar. Yani gap-vetosuyla ya da HALT/breaker kapısıyla DÜŞÜRÜLMÜŞ bir
plan, panoda "gönderilecek" görünür. **Canlı:** 500 planın **1**'i `failed_broker_rejection`, 499'u
NULL; 41 günlük olay penceresinde `armed_dropped` **0**, `entry_gap_veto` **0**, `BROKER_REJECT`
**4** — yani yol bugün soğuk, kusur **uyuyan** (bkz. §6/T-2).

### 2.3 Vaka (c) — `gate_verdict` (CANLI-BAĞLI kontrolü)

Diskten okunup dallanan **beş** yol: `loop.py:471 girise_uygun` (silahlanma) · `loop.py:510
operator_onay_ver` (`read_jsonl` → 404/409/200) · `loop.py:1103 _llm_veto_filter` (armed → veto) ·
`intraday_cycle.py:377 _faz4b` (`== "GO"` → GERÇEK bracket emri) · `watchdog.py:597
conservation_report` (`NO_GO` → terminal). Mercek onu ilk koşuda doğru sınıfladı.

### 2.4 TERS YÖNLÜ KAPI (bilinen-negatif) — emsalin son dersinin uygulanması

Emsal kendi düzeltmesinde şunu yazmıştı: *"Kalibrasyon kapısı bilinen-pozitifleri sınıyordu;
bilinen-NEGATİF için kapı yoktu. Bir sonraki kovada kalibrasyon iki yönlü olmalı."* Uygulandı:
**ÖLÜ diyeceğim her alan, kapsam dışı ağaçlarda (`tests/ ops/ research/ deploy/`) ayrıca arandı** ve
`meridian/` içinde çıplak-ad/sabit-dolayım desenleriyle ikinci kez tarandı. Sonuç:

- `side` → üretim dışı okuyucu YOK; `broker.py:649` pozisyonu **`side="long"` sabitiyle** kurar,
  plan alanını okumaz. ÖLÜ hükmü ayakta.
- `offset_kaynak · ref_kaynak · limit_bps · olay` → tek okuyucuları **testler**
  (`tests/test_mutborc_broker_entry_order_decision_v148.py`, `tests/test_icra_gercekligi_v141.py`).
  Üretim tüketicisi yok. "Test-tek-tüketici" alt-sınıfı olarak damgalandı, ÖLÜ hükmü ayakta.
- `targets` → `counterfactual.py:127`'de **yedek** olarak okunuyor; ÖLÜ demedim,
  YALNIZ-GÖRÜNÜRLÜK dedim (§3).

---

## 3. ALAN-ALAN TABLO — DEFTER + SİLAHLI yüzey (26 alan)

Sütunlar: **alan | yüzey | üretici | okuyucu(lar) | davranış? | sınıf | canlı doluluk**.
"davranış?" sütunu **yalnız DİSKTEN okunan** dalları sayar (R1).

| # | Alan | Yüzey | Üretici (dosya:satır) | Okuyucu(lar) | Davranış? | Sınıf | Canlı |
|---|---|---|---|---|---|---|---|
| 1 | `id` | defter+silahlı | `loop.py:1814` · `cf_backfill.py:109` | `loop.py:508` (onay lookup) · `loop.py:570` (arm dedup) · `loop.py:829` (`alpaca_submitted` dedup) · `loop.py:1998` (`entry_law` anahtarı) · `shadow_model.py:110` · `hermes.py:3791` · `watchdog.py:3252` | **EVET** — çift-emir kapısı | CANLI-BAĞLI | 500/500 |
| 2 | `date` | defter+silahlı | `loop.py:1817` | `loop.py:527` (seans yasası → 409) · `intraday_cycle.py:385` (4G → gönderim yok) · `api.py:5688` (`expired`) · `watchdog.py:530` (korunum penceresi) · `store.py:643` (retention) | **EVET** | CANLI-BAĞLI | 500/500 |
| 3 | `ticker` | defter+silahlı | `loop.py:1817` | `adapters/alpaca.py:889` (emir sembolü) · `broker.py:649` · `loop.py:539` (açık pozisyon kapısı) · `marketview.py:217` | **EVET** — emir | CANLI-BAĞLI | 500/500 |
| 4 | **`side`** | defter+silahlı | `loop.py:1817` (`"long"` sabit) | **YOK** (py/js/ops'ta plan bağlamında sıfır okuyucu; `broker.py:649` `side="long"` yazar, okumaz) | HAYIR | **ÖLÜ** | 500/500, hepsi `long` |
| 5 | `entry_trigger` | defter+silahlı+yasa | `loop.py:1818` | `adapters/alpaca.py:871` (tetik) · `broker.py:562` · `api.py:5696` (bayat-tetik dalı) · `counterfactual.py:121` | **EVET** — emir | CANLI-BAĞLI | 500/500 |
| 6 | `stop` | defter+silahlı | `loop.py:1818` | `adapters/alpaca.py:871` · `broker.py:615` (boyut) · `counterfactual.py:121` | **EVET** — emir | CANLI-BAĞLI | 500/500 |
| 7 | `profit_target` | defter+silahlı | `loop.py:1823` | `adapters/alpaca.py:889` (`submit_bracket` hedefi) · `broker.py:650` | **EVET** — emir | CANLI-BAĞLI | 500/500 |
| 8 | **`targets`** | defter+silahlı | `loop.py:1818` (`[profit_target]`) | `counterfactual.py:127` (**yalnız yedek**: `profit_target or targets[0]`) · `web/app.js:2979`, `9197` (yine yedekli) | HAYIR | **YALNIZ-GÖRÜNÜRLÜK** (yedekli ikiz) | 500/500 · `profit_target`tan **sapma 0** |
| 9 | `size_r` | defter+silahlı | `loop.py:1818`, `1976` | `adapters/alpaca.py:876` (risk $) · `broker.py:615` (qty) · `guard.py:522/531/542` · `recompute.py:530-533` (bounds dalı) | **EVET** — emir + kapı | CANLI-BAĞLI | 500/500 |
| 10 | `r_multiple_expected` | defter+silahlı | `loop.py:1819` | `guard.py:456` (rr_floor/rr_marginal) · `shadow_model.py:124` · `broker.py:657` → `trades.r_multiple_expected` | **EVET** | CANLI-BAĞLI | 500/500 |
| 11 | `regime_at_plan` | defter+silahlı | `loop.py:1820` | `broker.py:652` → `Position.regime_at_plan` → `trades.regime` → `analytics.per_regime_scores` → `autonomy_ladder:169` (dal) · `hermes.py:3900` · `shadow_model.py:125` | **EVET** (silahlı yüzeyden, dolaylı) | CANLI-BAĞLI | 500/500 |
| 12 | `strategy_version` | defter+silahlı | `loop.py:1823` | `broker.py:653` → `trades.strategy_version` → `rollback.py:209/213/404/407` (geri-alma dalı) · `baseline.py:115/269` | **EVET** (silahlı yüzeyden) · defter yüzeyi yalnız pano | CANLI-BAĞLI | 500/500 |
| 13 | **`sector`** | defter+silahlı | `loop.py:1820` | ~~`guard.py:673 y3_portfolio_inputs` (armed → `sector_notional`) → `guard.py:723` **ama kapı `portfolio.sector_cap`=0 iken hiç kurulmaz** · `web/app.js:9201`~~ **ŞERH 2026-08-24: EKSİK — `guard.py:454` → `_chk("sector_cap")` SERT kapısı atlanmıştı; bkz. §10/D-1** | ~~HAYIR (bugün)~~ **EVET** (§10/D-1) | ~~**YALNIZ-GÖRÜNÜRLÜK** + uyuyan bağ~~ **CANLI-BAĞLI** + AYRICA uyuyan İKİNCİ tavan | 500/500 · `y3_sector_cap` kontrolü **0/500 planda** |
| 14 | `score` | defter+silahlı | `loop.py:1820` | `guard.py:565` (score_band) · `broker.py:656` → `trades.score` → `analytics.score_calibration:916` · `threshold_curve.py:97` · `shadow_model.py:123` | **EVET** | CANLI-BAĞLI | 500/500 |
| 15 | `setup` | defter+silahlı | `loop.py:1821` | `intraday_cycle.py:376` (`ARMED_SETUPS` → GERÇEK emir) · `arming.py:141` · `hermes.py:3689/3912` · `counterfactual.py:125` | **EVET** — emir kapısı | CANLI-BAĞLI | 500/500 (6 kurulum) |
| 16 | `gate_verdict` | defter+silahlı | `loop.py:1883/1900` | §2.3'teki 5 disk-dalı + `analytics.py:258` + `api.py:4152` | **EVET** | CANLI-BAĞLI | 500/500 (REVIEW 370 · NO_GO 112 · GO 18) |
| 17 | **`gate_reasons`** | defter+silahlı | `loop.py:1883/1900/1978` | `analytics.py:3645` (aile sayımı) · `api.py:4155/4270` · `web/app.js:2812/2912/2981/9205` | HAYIR | YALNIZ-GÖRÜNÜRLÜK (MEŞRU) | 499/500 |
| 18 | **`gate_checks`** | defter+silahlı | `loop.py:1884` | `analytics.py:3637` (hard/soft sayımı) · `api.py:4156/4271` · `web/app.js:9117` (karar-ağacı tablosu) | HAYIR | YALNIZ-GÖRÜNÜRLÜK (MEŞRU, beyanlı) | 500/500 · 16 farklı kontrol adı |
| 19 | **`broker_status`** | defter+silahlı | `loop.py:332` · `loop.py:813` · `loop.py:830` · `loop.py:852` · yama `loop.py:310` | **yalnız** `web/app.js:1218/2499/9203` | HAYIR | **YALNIZ-GÖRÜNÜRLÜK** + değer-düzeyi ÖLÜ alt-küme (§2.2) | 1/500 dolu |
| 20 | **`dormant_setup`** | defter+silahlı | `loop.py:1822` · `cf_backfill.py:117` | `counterfactual.py:149` · `web/app.js:9202` | HAYIR | **YALNIZ-GÖRÜNÜRLÜK** (08-07 hükmü tazelendi) | 25/500 taşıyor, 8'i `1` |
| 21 | **`exploration`** | defter+silahlı | `loop.py:1977` (yalnız keşif havuzu seçimi) | `broker.py:657` → `Position.exploration` → **`loop.py:1636`** (çıkış rejim dalı GEVŞER) · `api.py:4158/4271` · `web/app.js:4793/9112/9166` | **EVET** (kablo gerçek) | CANLI-BAĞLI **— ÜRETİM KURAK** | **0/500** plan · **0/893** işlem · **0/7** pozisyon · 41 günde `exploration_armed` **1** (TMO, 07-25) |
| 22 | **`p_win_shadow`** | defter+silahlı | `loop.py:1888` | `shadow_model.py:315 evaluate_promotion` (disk `_plan_index`) → `promoted` → `loop.py:1893` REVIEW vetosu · `selfreview.py:342-345` (çelişki raporu) · `web/app.js:2981/9204` | **EVET** — ama uçtaki kapı kilitli | CANLI-BAĞLI **— ÖLÇÜM KITLIĞIYLA KİLİTLİ** | 25/500 damgalı, **yalnız 6'sı bir işleme birleşiyor**; `PROMOTE_MIN_N=30` |
| 23 | `llm_opinion` | defter+silahlı | `hermes.py:3826` (`update_jsonl`) · `hermes.py:3854` (armed) | `loop.py:1103` → `cancel_order` + silahlı kümeden düşürme · `analytics.py:1150-1206` (kalibrasyon → `llm_promoted`) · `counterfactual.py:220` · `hermes.py:3794` · `watchdog.py:1032` (parity) | **EVET** — en güçlü bağ | CANLI-BAĞLI | 379/500 · 358'i bir işleme birleşiyor |
| 24 | **`llm_veto`** | defter | `loop.py:1135` | `analytics.py:3635` (sayaç) · `api.py:4159/4272` · `web/app.js:4784/9114` | HAYIR | YALNIZ-GÖRÜNÜRLÜK (henüz **hiç üretilmedi**) | **0/500** · `llm_veto_strip` olayı 41 günde **0** |
| 25 | `operator_onayi` | defter+silahlı | `loop.py:558` (`_onay_yaz`, disk) · `loop.py:572` (armed) | `loop.py:458 operator_onayli` → `girise_uygun` (silahlanma) · `intraday_cycle.py:378` (4b emir yetkisi) · `watchdog.py:3263` (#11 alarm) · `api.py:5726` (rozet) · `web/app.js:2685/2700` | **EVET** | CANLI-BAĞLI | 6/500 |
| 26 | **`carried`** | silahlı | `loop.py:1241` | `loop.py:1239` — **bir sonraki seansta** (`portfolio.json`'dan) → plan düşürülür | **EVET** | CANLI-BAĞLI **— ÜRETİM 0** | 0/500 · 41 günde `armed_no_bar_carried` **0**, `armed_expired_no_bar` **0** |

**Efemeral (diske yazılmaz, yanıt-içi):** `expired` · `age_days` (`api.py:5688-5690`) ·
`onay_bekliyor` (`api.py:5727`). Üçü de panoya gider; `expired` ayrıca `_onay_bekleyen_damgala`
dalına girer. Kalıcı alan olmadıkları için tabloya sayılmadılar (sınıf: canlı-bağlı görünüm).

---

## 4. ALAN-ALAN TABLO — `entry_law` YAN TABLOSU (14 alt-alan)

`portfolio.json["entry_law"][plan_id]` **silahlı plan yapısının parçasıdır** ve icra girdilerini
sinyal barı kapanışında dondurur (`loop.py:1926-1930`). Aynı mercek uygulandı.

| Alt-alan | Üretici | Okuyucu(lar) | Davranış? | Sınıf |
|---|---|---|---|---|
| `atr` | `broker.py:249+` | `loop.py:787` → `alpaca.submit_plan(atr=…)` · `loop.py:1451` `fill_entry(atr=…)` | **EVET** — limit tavanı | CANLI-BAĞLI |
| `ref_price` | `broker.py:250` | `loop.py:787` → `submit_plan(ref_price=…)` (gap kararı) | **EVET** | CANLI-BAĞLI |
| `pivot` | `loop.py:1929` | `loop.py:1452` → `Position.pivot` → `strategy.py:282 early_kill_pivot_exit` | **EVET** — çıkış | CANLI-BAĞLI |
| `limit` | `broker.py:249` | `loop.py:1455` (E2) · `loop.py:1473 fill_vs_limit_bps` · `intraday_cycle.py:433` | kısmen (ölçüm) | CANLI-BAĞLI (ölçüm) |
| `gap_at_submit` | `broker.py:255` | `broker.py:567` **dal** (`GAP_VETO` → dolum yok) · `loop.py:1453` | **EVET** | CANLI-BAĞLI |
| `gap_behavior` | `broker.py:164` | `broker.py:244`, `broker.py:567` **dal** | **EVET** | CANLI-BAĞLI |
| `tif` | `broker.py:170` | `adapters/alpaca.py:892` (`submit_bracket(tif=…)`) | **EVET** | CANLI-BAĞLI |
| `mode` | `broker.py:249` | `loop.py:794` (E2 `emir_tipi`) · `intraday_cycle.py:433` (log). **Emir tipini belirleyen `mode` `alpaca.py:884/891`'de YENİDEN türetilir** | HAYIR (kalıcı kopya) | YALNIZ-GÖRÜNÜRLÜK |
| `trigger` | `broker.py:249` | `loop.py`/E2 üzerinden görünürlük (emir tetiği plandan gelir) | HAYIR | YALNIZ-GÖRÜNÜRLÜK |
| `law` | `broker.py:256` | `loop.py:794/1456` (E2 damgası) | HAYIR | YALNIZ-GÖRÜNÜRLÜK (sürüm damgası) |
| **`olay`** | `broker.py:249` | **YOK** (yalnız `tests/test_icra_gercekligi_v141.py`, `tests/test_mutborc_…_v148.py`) | HAYIR | **ÖLÜ** (test-tek-tüketici) |
| **`offset_kaynak`** | `broker.py:251` | **YOK** — kodun kendi beyanı (`broker.py:200`) *"okuyucusu E2 defteri"* der; **canlı E2'nin 30 satırında bu alan YOK** | HAYIR | **ÖLÜ + ÇÜRÜK BEYAN** |
| **`ref_kaynak`** | `broker.py:254` | **YOK** — beyan `broker.py:215` *"`ref_kaynak` alanıyla…"*; canlı E2'de YOK | HAYIR | **ÖLÜ + ÇÜRÜK BEYAN** |
| **`limit_bps`** | `broker.py:257` | **YOK** (grep'teki eşleşmeler `fill_vs_limit_bps` — AYRI ve canlı alan) | HAYIR | **ÖLÜ** (test-tek-tüketici) |

**Canlı teyit:** `portfolio.entry_law` iki plan taşıyor ve her ikisi de `offset_kaynak`,
`ref_kaynak`, `limit_bps`, `olay` alanlarını **dolu** yazıyor — yani üretim gerçek, tüketim sıfır.
E2 defteri (`entry_execution.jsonl`, 30 satır) alan sayımı: `ts date plan_id ticker motor
entry_trigger limit atr law gap_at_submit karar qty fill fill_vs_resmi_acilis_bps fill_vs_limit_bps
resmi_acilis emir_tipi tif red_nedeni red_sinifi kaynak fill_qty fill_status fill_kaydedildi
fill_vs_resmi_acilis_beyan` — **`offset_kaynak`/`ref_kaynak`/`limit_bps` yok.**

---

## 5. SAYIM ÖZETİ

### Plan defteri alanları (26)

| Sınıf | Adet | Alanlar |
|---|---:|---|
| **CANLI-BAĞLI** | ~~**18**~~ **19** | `id · date · ticker · entry_trigger · stop · profit_target · size_r · r_multiple_expected · regime_at_plan · strategy_version · score · setup · gate_verdict · llm_opinion · operator_onayi` **+ 3 yıldızlı** `exploration* · p_win_shadow* · carried*` (kablo gerçek, **besleme kurak / uç kilitli** — §6) **+ `sector`** (§10/D-1 düzeltmesi, 2026-08-24) |
| **YALNIZ-GÖRÜNÜRLÜK** | ~~**7**~~ **6** | `targets · `~~`sector`~~` · gate_reasons · gate_checks · broker_status · dormant_setup · llm_veto` (§10/D-1) |
| **ÖLÜ** | **1** | `side` |
| **HAYALET** | **0** | (alan düzeyinde; değer düzeyinde 2 — §2.2) |

> Sayım notu: ~~18 + 7 + 1 = 26~~ → **19 + 6 + 1 = 26** (2026-08-24 şerhi, §10/D-1). `gate_reasons`/`gate_checks` MEŞRU görünürlüktür (pano karar-ağacı,
> beyanlı); `targets`/`sector`/`llm_veto`/`broker_status`/`dormant_setup` beyansızdır.
> Yıldızlı üç alan **sınıf olarak CANLI-BAĞLI** sayıldı (dal gerçek ve diskten besleniyor); ayrı bir
> kova AÇILMADI çünkü dört sınıflı sözleşme brief'te sabittir — ayrım "canlı doluluk" sütununda ve
> §6'da taşınır.

### `entry_law` alt-alanları (14)

| Sınıf | Adet | Alanlar |
|---|---:|---|
| CANLI-BAĞLI | 8 | `atr · ref_price · pivot · limit · gap_at_submit · gap_behavior · tif` (+`limit` ölçüm bacağı) |
| YALNIZ-GÖRÜNÜRLÜK | 3 | `mode · trigger · law` |
| **ÖLÜ** | **4** | `olay · offset_kaynak · ref_kaynak · limit_bps` (ikisi ÇÜRÜK BEYANLI) |

### Değer düzeyi (R2 çıktısı)

| Alan | Üretilen değer sayısı | Tüketilen | Ölü değer |
|---|---:|---:|---|
| `broker_status` | 3+ (`failed_broker_rejection`, `gap_veto`, `armed_dropped_<kapı>`) | 1 | **2 sınıf** |

### Canlı doluluk profili (500 plan)

`side/targets/gate_checks/gate_reasons` 500/500 · `llm_opinion` 379 · `dormant_setup` 25 (8'i `1`) ·
`p_win_shadow` 25 · `operator_onayi` 6 · `broker_status` 1 · **`exploration` 0 · `llm_veto` 0 ·
`carried` 0**.

---

## 6. EN TEHLİKELİ ÜÇ (yanlış işe / yanlış güvene yol açma riskine göre)

### T-1 · `p_win_shadow` — defter kırpması gölge-model terfi kapısını YAPISAL olarak kilitliyor

**Ölçüm.** `shadow_model.evaluate_promotion` planları `trade_plans` üzerinden `plan_id` ile
birleştirir (`shadow_model.py:110`) ve `PROMOTE_MIN_N=30` taze çift ister. Canlıda **893 işlemin
535'i hiçbir plan satırına birleşmiyor** (defter tam 500'e kırpılmış); `p_win_shadow` damgalı 25
planın **yalnız 6'sı** bir işleme birleşiyor. Yani terfi eşiği bugün **erişilemez** ve
`is_promoted()` her zaman `False` döner → `loop.py:1893` REVIEW vetosu hiç kurulamaz.

**Neden tehlikeli.** Bu bir "veri az" durumu değil, **ölçüm aracının kendi kendini kör etmesi**:
pano/hermes "gölge model kalibre olmadı" der, oysa model kalibre OLAMAZ — kanıt diskte silinmiştir.
`store.py:632-655`'teki retention kuralı 2026-08-23'te tam bu gerekçeyle değiştirilmiş görünüyor
("plan, işlemi yaşadıkça yaşar") **ama canlı defter hâlâ tam 500 satır** — kural bir sonraki
`merge_dated_jsonl` yazımında etki edecek; son plan tarihi 2026-08-21. Yani düzeltme **inmiş ama
henüz koşmamıştır**; bu belge onu kanıtla kayda geçirir, hüküm vermez.

### T-2 · `broker_status` — düşürülen plan panoda "gönderilecek" görünüyor

**Ölçüm.** §2.2. `gap_veto` ve `armed_dropped_<kapı>` değerlerinin **hiçbir tüketicisi yok**;
`app.js:1218`'in `else` dalı onları "gönderilecek" rozetiyle, `app.js:2499` ise `bekleyen`
sayacında gösterir. Üstelik bu iki değeri yazan kod yolları (`loop.py:813`, `loop.py:331`)
`SISTEM-DENETIMI-2026-08-02` #14/#16'nın **düzeltmesi** olarak eklenmişti: "silahlı bir planın
kaybolma sebebi defterden okunabilmeli". Sebep defterde YAZILI, ama **okuyan taraf o sözcükleri
tanımıyor**.

**Neden tehlikeli.** Bu, düzeltmenin kendisinin yarım kalmasıdır: yazan bacak indi, okuyan bacak
inmedi. Bugün soğuk (41 günde 0 olay), yani **uyuyan** bir yanlış-güven yüzeyi — ilk gap-veto ya da
HALT-düşürmesi gününde operatör panoda "gönderilecek" okuyacak.

### T-3 · `exploration` + `carried` — GERÇEK davranış dalları, SIFIR üretim

**Ölçüm.** `exploration`: `loop.py:1636`'da açık pozisyonun çıkış rejim kapısını GEVŞETEN gerçek bir
dal var ve girdisi diskten (`portfolio.positions[].exploration`) geliyor. Canlıda 41 günde
`exploration_armed` **1 kez** (TMO, 2026-07-25) ateşledi; bugün 500 planın, 893 işlemin ve 7 açık
pozisyonun **hiçbirinde** `True` yok. `carried`: `loop.py:1239-1241` bir planı ikinci bar-sız seansta
DÜŞÜREN gerçek bir sayaç; 41 günde `armed_no_bar_carried` **0**, `armed_expired_no_bar` **0**.

**Neden tehlikeli.** Bunlar "ölü kod" değil — **beslenmeyen canlı kod**. Panoda keşif çipi
(`app.js:4793`), keşif uyarı metni (`app.js:9112`) ve denetim izinde `exploration` bayrağı
(`api.py:4158`) var: sistem keşif yapıyor gibi GÖRÜNÜYOR. ROADMAP'in kendi notu (`loop.py:1949-1952`)
sebebi zaten adlandırmış: *"tavan bağlamıyor, kaynak kurumuş"*. Risk **yanlış iş**: kimse tavanı
ayarlamaya çalışmasın diye kalemin adı "bütçe" değil "üretici kuraklığı" olmalı.

---

## 7. ROL-1'E ÖNERİ SATIRLARI (KALDIR / DAMGALA / BAĞLA) — **HÜKÜM YOK**

Her satır bir ÖNERİdir; hükmü Rol-1 verir. Şema alanına dokunan her öneri iki motorlu şema
eşitliği testini (`tests/test_differential_v60.py`) tetikleyeceği için "kaldır" önerileri
düşük-öncelikli işaretlendi.

| # | Alan(lar) | Öneri | Gerekçe (ölçüm) |
|---|---|---|---|
| Ö-1 | `broker_status` **değerleri** | **BAĞLA** — `app.js:1218/2499`'a `gap_veto` ve `armed_dropped_*` için ayrı rozet/sayaç; ya da `_durumEmirKarti`'nda "düşürüldü" kovası | §2.2 · T-2 · yazan bacak indi, okuyan bacak inmedi |
| Ö-2 | `p_win_shadow` (dolaylı: retention) | **DOĞRULA** — `store.py:632-655` yeni retention kuralının canlıda KOŞTUĞUNU bir sonraki `daily_cycle` sonrası ölç (bugün defter hâlâ tam 500) | T-1 · 535/893 birleşmeyen işlem · terfi eşiği erişilemez |
| Ö-3 | `offset_kaynak · ref_kaynak` | **DAMGALA (öncelikli)** — `broker.py:200` ve `broker.py:215`'teki *"okuyucusu E2 defteri"* beyanları ÇÜRÜK; ya beyanı tazele ya alanları E2'ye gerçekten yaz | §4 · canlı E2'nin 30 satırında alan YOK · Ö-49 bayat-beyan sınıfı |
| Ö-4 | `olay · limit_bps` | **DAMGALA** — "test-tek-tüketici" olarak beyan et (`DECLARED_SINKS` alan-düzeyi karşılığı yoksa yorum satırı yeter) | §2.4 · üretim tüketicisi sıfır |
| Ö-5 | `side` | **KALDIR ya da DAMGALA (düşük öncelik)** — plan şeması iki motorda aynı kalmak zorunda; kaldırmak `test_differential_v60`'ı tetikler. Alternatif: "gelecekteki short desteği için ayrılmış, bugün sabit `long`" beyanı | 500/500 `long` · sıfır okuyucu · `broker.py:649` sabit yazıyor **→ UYGULANDI 2026-08-24 (§10)** |
| Ö-6 | `targets` | **DAMGALA** — `profit_target`ın yedekli ikizi; canlıda 500/500 sapma 0. Kaldırma önerilmez (cf yedek okuması var) | §3/8 **→ UYGULANDI 2026-08-24 (§10)** |
| Ö-7 | `sector` | **DAMGALA** — "uyuyan bağ: `portfolio.sector_cap`=0 iken hiçbir kapıya girmez" (kod `guard.py:721`'de zaten koşullu ama alanın kendisi beyansız) | 0/500 planda `y3_sector_cap` kontrolü **→ UYGULANDI 2026-08-24 (§10)** |
| Ö-8 | `exploration · carried` | **DAMGALA** — "kablo canlı, ÜRETİM KURAK" ayrımını panoya/kaleme yaz; kalem "keşif bütçesi" değil "keşif üretici kuraklığı" adıyla izlensin | T-3 · 41 günde 1 / 0 olay **→ UYGULANDI 2026-08-24 (§10)** |
| Ö-9 | `llm_veto` | **İZLE** — üretici (`loop.py:1135`) yalnız `llm_promoted()` sonrası koşar; 0/500 doluluk bugün MEŞRU. Terfi gerçekleşirse alanın pano bacağı zaten hazır | `llm_veto_strip` 0 |
| Ö-10 | **yöntem** | **BAĞLA (mimari karar)** — bu turun merceği oturum-içi bir betikti; kalıcı bir alan-düzeyi bekçisi (`codelaw.artifact_graph`'ın alan kardeşi) YASA-6'yı alan granülaritesine taşır. `ONAY_ALANI` vakası (§1.2/1) böyle bir bekçinin ilk gününde çözmesi gereken sorunu adlandırıyor: **sabit-dolayımlı anahtarlar** | M11 kaleminin kendi tespiti: "alan-merceği ARACI repo'da hiç yok" |

---

## 8. ÖLÇÜLEMEYENLER (adıyla — `ÖLÇÜLEMEDİ ≠ 0`)

1. **Defter penceresi 500 satır.** Canlı `trade_plans` tam 500'e kırpılmıştır; 2025-07-02 öncesi ve
   aradaki kırpılmış satırlar **görülmedi**. "Canlı doluluk" sütunundaki bütün oranlar bu pencere
   içindir. `exploration=1` olan TMO planı (2026-07-25) bu pencerede YOK — yani "0/500" ifadesi
   "hiç olmadı" DEĞİL, "pencerede yok" demektir; olay defteri onu ayrıca kanıtlıyor (1 kez).
2. **Olay penceresi 41 gün** (`events.jsonl` 2026-07-14 → 08-23, 76.492 satır). `armed_dropped`,
   `gap_veto`, `llm_veto_strip` sayımları bu pencere içindir; dosya döndürülmüşse daha eski
   ateşlemeler ölçülmedi.
3. **Pano çizimi çalıştırılarak doğrulanmadı** (§1.2/3). `app.js` satırları kaynak koddan okundu.
4. **Aday defteri (`candidates.jsonl`) taranmadı.** Brief "plan defteri" dedi; aday satırlarının
   alanları (`rs_rating`, `source_skill`, `rvol20`, `mom_12_1`, `turnover21`, `notes`) bu mercekten
   GEÇMEDİ. `strategy.py:334 as_row` beş bileşen alanı yazıyor ve en az `rmom` bugün hiçbir çağıranın
   vermediği için hep `None` — **HAYALET adayı**, ama ölçülmedi. Bir sonraki kovanın konusu.
5. **`trades.jsonl` alan düzeyinde ölçülmedi.** Plan alanlarının işlem satırına KOPYALANDIĞI yerde
   izi bıraktım (`broker.py:649-660`), ama işlem satırının kendi 27 alanı tek tek taranmadı.
6. **Gölge motorların plan şemaları** (`shadow_variants.py:204 _plan_of`, `mutation.py:184`,
   `backtest.py:457`) yalnız ÜRETİCİ olarak sayıldı; o defterlerin kendi tüketicileri ayrı bir
   yüzeydir ve taranmadı.
7. **Tek adım taint** (§1.2/4): derin zincirli bir davranış bağı kaçmış olabilir. Yönü
   yanlış-ÖLÜ'dür ve §2.4 kapısı bu riski ÖLÜ hükmü verdiğim 5 alan için (side + 4 `entry_law`
   alanı) kapatır; **YALNIZ-GÖRÜNÜRLÜK** hükümlerinde aynı kapı koşulmadı.
8. **`_stamp_plan_status` yolunun canlı etkisi ölçülemedi** (`loop.py:292-315`): `armed_dropped`
   olayı 41 günde hiç ateşlemediği için damganın diske gerçekten indiği CANLIDA gözlenmedi.

---

## 9. BU TURUN TEK CÜMLESİ

Plan defterinin 26 alanının **17'si** karara dokunuyor, **8'i** yalnız çiziyor, **1'i** (`side`)
tamamen ölü; asıl bulgu alanların kendisinde değil **besleme ve okuma bacaklarının ayrışmasında**:
`p_win_shadow`'un kanıtı defter kırpmasıyla siliniyor, `broker_status`'ün iki değeri panoda
"gönderilecek" diye okunuyor, `exploration`/`carried` gerçek dallara bağlı ama hiç beslenmiyor — ve
`entry_law`'ın dört alt-alanı diske yazılıp **yalnız testler tarafından** okunuyor, ikisi de
"okuyucusu E2 defteri" diye **çürük bir beyan** taşıyor.

---

## 10. UYGULAMA KAYDI — Ö-5…Ö-8 DAMGALANDI (2026-08-24, WP5/WP3 · KALEM K4)

**Ne yapıldı.** §7'nin dört DAMGALA önerisi, aynı gece Ö-3/Ö-4 için indirilen kalıbın BİREBİR
tekrarıyla uygulandı: her alan için kaynak koda bir **`ALAN DAMGASI[M11·Ö-n]`** bloğu ve
`tests/test_pano_durustluk_v280.py` **§F**'ye o damganın DAYANDIĞI OLGUYU tutan bir **bayatlama
kapısı**. Kalıbın çekirdeği: *damga metni tek başına çivilenmez — damganın iddiası ölçülür, ve
alan bir gün gerçekten üretime bağlanırsa (ya da bağı kesilirse) çivi kırmızıya döner.*

**Davranış DEĞİŞMEDİ, şema alanı KALDIRILMADI.** Dört öneri de yorum + test kalemidir; hiçbir
karar dalı, eşik, emir ya da alan eklenmedi/çıkarıldı. `tests/test_differential_v60.py` (iki motor
plan şeması eşitliği) yeşil kaldı — kalemin ön koşuluydu.

| # | Alan(lar) | Damga nerede | Bayatlama kapısı (§F) |
|---|---|---|---|
| Ö-5 | `side` | `loop.py` (üretici) + `broker.py` (`side="long"` sabiti) | `test_f1` (damga metni) · `test_f2` (plan-adlı sözlük `side` okursa ya da sabit kalkarsa KIRMIZI) |
| Ö-6 | `targets` | `loop.py` (üretici) | `test_f3` · `test_f4` (liste çok elemanlı olur ya da ifadesi `profit_target`tan ayrışırsa KIRMIZI) |
| Ö-7 | `sector` | `guard.py:classify_gate` | `test_f5` · `test_f6` (CANLI yarım kesilirse) · `test_f7` (UYUYAN yarım knob koşulundan çıkarsa) |
| Ö-8 | `exploration` · `carried` | `loop.py` (`_carry_armed_without_bar` üstü + keşif çıkış dalında işaretçi) | `test_f8` (ad dâhil: "keşif ÜRETİCİ KURAKLIĞI") · `test_f9` (keşif dalı) · `test_f10` (carried sayacı + iki olayı) · `test_f11` (üretici yüzeyi tek kalmalı) |

### D-1 · BU TURUN DÜZELTMESİ — Ö-7 önerisi OLDUĞU GİBİ UYGULANAMAZDI

§7/Ö-7 şu damgayı önermişti: *"uyuyan bağ: `portfolio.sector_cap`=0 iken hiçbir kapıya girmez"*.
Bağımsız ölçüm (kör uygulama yapılmadı) bunun **eksik** olduğunu gösterdi:

- `guard.py:classify_gate` içinde `sec = plan.get("sector", "?")` **KOŞULSUZ** okunur ve
  `_chk("sector_cap", (sc.get(sec, 0) + 1) / max(1, sector_basis) > max_sector_exposure_pct/100)`
  **SERT** kapısına girer. Bu kapı bugün canlıdır (`max_sector_exposure_pct: 40.0`, `state/goal.yaml`)
  ve üretim çağıranı `loop.py`'nin plan döngüsüdür.
- §3'ün 13. satırı bu okuyucuyu listelemiyordu; yalnız `y3_portfolio_inputs → y3_sector_cap`
  bacağını görmüştü. İki tavan **AYRI**dır ve birbirinin yerine geçmez: canlı olan İSİM SAYAR
  (`sector_cap`), uyuyan olan NOTIONAL PAYI ölçer (`portfolio.sector_cap` → `y3_sector_cap`).
  Kodun kendi belgesi bunu zaten söylüyordu (`guard._y3_portfolio_caps` docstring'i).

Önerilen ifade olduğu gibi yazılsaydı **Ö-49 bayat-beyan sınıfını yeniden üretirdi** — yani tam bu
turun kapattığı kusuru. Damga bu yüzden İKİ YARIMLI yazıldı ve iki yarım ayrı ayrı çivilendi
(`test_f6` / `test_f7`). §3 satırı ve §5 sayımı **silinmedi**, üstü çizilip şerh düşüldü.

### D-2 · KASITLI-KIRMIZI DOĞRULAMASI (çiviler gerçekten ölçüyor mu)

Altı sahte bağlanma/kopma kaynağa geçici olarak enjekte edildi, ilgili çivi koşuldu, dosya
**sha256 ile birebir** geri alındı. Altısı da kırmızı yandı:

| Enjeksiyon | Beklenen çivi | Sonuç |
|---|---|---|
| plan sözlüğüne sahte `plan.get("side")` okuyucusu | `test_f2` | KIRMIZI ✓ |
| `targets` gerçek hedef merdivenine çevrildi (2 eleman) | `test_f4` | KIRMIZI ✓ |
| `sec = plan.get("sector")` kesildi (canlı yarım koptu) | `test_f6` | KIRMIZI ✓ |
| `portfolio.sector_cap` varsayılanı 0→25 (uyuyan yarım uyandı) | `test_f7` | KIRMIZI ✓ |
| keşif çıkış-gevşetme dalı kesildi | `test_f9` | KIRMIZI ✓ |
| ikinci bir `exploration` üreticisi eklendi | `test_f11` | KIRMIZI ✓ |

### D-3 · BU TURDA ÖLÇÜLEMEYENLER (ÖLÇÜLEMEDİ ≠ 0)

1. **Canlı doluluk sayıları YENİDEN ÖLÇÜLMEDİ.** Damgalardaki 500/500 · 0/500 · 1/0 olay
   rakamları bu belgenin 2026-08-23 salt-okuma SSH ölçümünden ALINTIdır; bu tur canlıya
   bakmadı. Pencere sınırları §8'de duruyor ve damgalarda tekrarlandı.
2. **`state/goal.yaml`'da `portfolio.sector_cap` anahtarı YOK** (dosyada geçmiyor) — yani knob
   `guard.py`nin `0` varsayılanına düşüyor. Bu kod tarafından çivilendi (`test_f7`), canlı
   `goal.yaml`ın kendisi çivilenMEDİ: canlı yapılandırma meşru olarak değişebilir ve testi
   yapılandırmaya bağlamak yanlış-alarm üretirdi.
3. **`side`in "sıfır okuyucu" hükmü** ad çakışması yüzünden mekanik değil ELLE doğrulandı
   (`watchdog` Alpaca pozisyonu · `faz5_cikis` açık pozisyon · `alpaca` emri). `test_f2` yalnız
   plan bağlamını adlandıran isimleri tarar; beyanlı sınırı testin kendi docstring'indedir.
4. **Pano tarafı bu kalemde açılmadı.** Ö-8 "kalem adı" önerisi kodun içine yazıldı; panonun
   keşif çipi/uyarı metni başka ajanın dosyasıdır (`meridian/web/**`) ve DOKUNULMADI.
