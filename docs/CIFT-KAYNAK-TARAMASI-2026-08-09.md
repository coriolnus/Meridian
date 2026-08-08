# ÇİFT-KAYNAK TARAMASI — 2026-08-09

**Ölü-mekanizma avının BEŞİNCİ kovası.** Okuyucusu: Rol-1 (hüküm) + operatör (karar) — YASA 6 tamam.

**Tur sınırı:** SALT ÖLÇÜM + BELGE. `meridian/` altında **hiçbir dosya değiştirilmedi**; git komutu
koşulmadı; canlıya dağıtım yapılmadı; `serve.sh` koşulmadı; broker'a emir gönderilmedi/iptal
edilmedi; test dosyası yazılmadı. Yazılan tek dosya budur.

**Kanıt tabanı:** canlı A1 (`ubuntu@130.61.126.87`), salt-okunur — betikler yerelde yazıldı ve
`./.venv/bin/python -` stdin'inden beslendi (altı koşu: `canli_01…06`). Canlı `state/`e tek bayt
yazılmadı; koşan hiçbir fonksiyon `store.write_*` yoluna girmedi (yalnız `read_*` + saf rapor
üreticileri). Ölçüm anları satır satır yazılıdır (C10 ruhu: sabit sayı değil, **ölçüm anı + kaynak**).

---

## 0. SINIFIN TANIMI (operatör, 2026-08-09)

> Aynı GERÇEK birden fazla yerde tutuluyor/türetiliyor; kopyalardan biri yaşam-döngüsünü/güncel
> durumu biliyor, diğeri bilmiyor; **tüketiciler ikiye bölünmüş.**

Dördüncü kova (`docs/ARTEFAKT-TARAMASI-2026-08-07.md`) her artefakta *"seni kim okuyor, okuyan
DAVRANIYOR mu?"* diye sormuştu. Bu kova artefakta değil **GERÇEĞE** sorar: *"aynı gerçeği başka kim
bildiğini İDDİA EDİYOR, ve o kopya bugün ne diyor?"*

İki kova birbirinin tersidir ve birlikte bir çift oluşturur: dördüncüsü **tüketicisiz yazım**
(ölü kopya) avlar, beşincisi **çok-yazarlı gerçek** (ayrık kopya) avlar. Bir artefakt dördüncüde
`davranissal` çıkıp beşincide `ayrismis-simdi` olabilir — çünkü davranan bir okuyucunun okuduğu
şeyin **yanlış kopya** olması, dördüncü kovanın merceğinden yapısal olarak görünmez.

---

## 1. YÖNTEM

**Birim: ARTEFAKT DEĞİL, GERÇEK.** Tarama "hangi dosyalar var" diye başlamaz; sekiz gerçek-ailesi
elle yürünür ve her aile için üç soru sorulur:

| Adım | Soru | Kanıt biçimi |
|---|---|---|
| **1. KAYNAK SAYIMI** | Bu gerçeği kaç yer TUTUYOR ya da TÜRETİYOR? | `dosya:satır` — her kaynak adıyla |
| **2. ŞU ANKİ AYRIŞMA** | Kopyalar **bugün canlıda** ne diyor? | canlı ölçüm, damgalı |
| **3. TÜKETİCİ BÖLÜNMESİ** | Her kaynağı kim okuyor — ve okuyanlar **aynı kopyayı** mı okuyor? | `dosya:satır:fonksiyon` |

**Yürünen sekiz aile:** ① yaşam-döngüsü/durum işaretleri (skill · sembol · plan · hipotez · emir) ·
② sermaye/öz-sermaye · ③ pozisyon/adet · ④ evren üyeliği · ⑤ config-değeri ↔ kod-sabiti ·
⑥ mod/durum bayrakları · ⑦ zaman damgaları · ⑧ eşikler (kart ↔ kod) ve sayımlar/paydalar.

### 1.1 HÜKÜM KOVALARI — ve bir tanım netleştirmesi (BEYAN)

| Kova | Tanım |
|---|---|
| `tek-kaynak` | Gerçek tek yerde. Sorun yok. |
| `kopya-senkron-korumali` | Kopya VAR **ve** senkronu tutan bir mekanizma + onu çivileyen bir test/kapı var — **adıyla**. |
| `kopya-korumasiz` | Kopya var, ayrışma bugün YOK, ama yakalayacak mekanizma da yok → **RİSK**. |
| `ayrismis-simdi` | Bugün fiilen ayrık → **KUSUR**, şiddetiyle. |

**Netleştirme (yöntem beyanı):** brief'in kova tanımı literal okunduğunda "bugün ayrık" HER durumda
`ayrismis-simdi`ye düşer — bekçi ayrışmayı **adıyla bağırıyor** olsa bile. Bu okumayı **değiştirmedim**
(operatörün taksonomisini kendi kendime yeniden yazmam, ölçüm ajanının kartı düzeltmesiyle aynı
ihlal olurdu). Bunun yerine kova adının yanına `[bekçili]` işareti koydum ve şiddeti oradan
derecelendirdim: bekçili bir ayrışma **görünür** bir borçtur, bekçisiz olan **sessiz** bir borçtur.

### 1.2 YÖNTEMİN KENDİ ARIZALARI — ÖLÇÜLDÜ VE BEYAN EDİLİYOR

Dördüncü kovanın DÜZELTME dersi ("tarama, bekçinin körlüğünü İDDİA ederken kendi körlüğünü üretti")
bu turda üç yerde ısırdı:

| # | Arıza | Nasıl yakalandı | Sonuç |
|---|---|---|---|
| **Y-1** | **Ölçüm ortamı, canlı ortam sanıldı.** İlk koşuda `config.BROKER` **`"internal"`** okundu ve bu bir an "canlı ayna kapalı" gibi göründü. | `deploy/oracle-a1/meridian.service:25` `Environment=MERIDIAN_BROKER=alpaca_paper` — stdin'den beslenen ölçüm süreci systemd birim ortamını **miras almaz**. | **YANLIŞ POZİTİF ÖNLENDİ.** Worker'ın gerçek değeri dolaylı ÖLÇÜLDÜ (§6.5): `loop.reconcile_broker_state` `config.BROKER != "alpaca_paper"` iken **yalnız** `_skip()` yazar (`loop.py:1928`); canlı `broker_reconcile.json` tam-yazım dalını taşıyor (`api_ok: true`, `skip_reason` yok) ⇒ worker `alpaca_paper`. |
| **Y-2** | **Yorum farkı, sözleşme farkı sanılabilirdi.** `state/goal.yaml` canlı↔repo sha256 **AYRI** çıktı (repo `099590de…`, canlı `416a67ad…`; ölçüm 2026-08-09 00:44Z). | Diff alındı: fark **yalnızca** dördüncü kovanın 08-07'de eklediği yorum blokları. Anahtar/değer düzeyinde fark YOK. | Kalibrasyon (b) **düşmedi** — bkz. §2. Ham `diff`e bakan bir yöntem burada KUSUR bağırırdı. |
| **Y-3** | **Alt-ajan iddiası kanıt sanılabilirdi.** Aile ⑤ ve ⑧'in geniş grep'i iki keşif ajanına verildi. | Dönen tablonun **her yüksek-şiddetli satırı** elle yeniden grep'lendi (`DERISK_FLOOR_DD`, `SECTOR_CAP_DEFAULT_PCT`/`HEAT_CAP_DEFAULT_PCT` okuyucu yokluğu, `KORUMA_TIF`, `COMPOSITE_MAX_KNOBS`, `refetch_max`×5, `app.js:4851/5052/5432`, `PK_CIVI_HEDEF`). | Doğrulananlar aşağıda; doğrulanmayan hiçbir satır hükme girmedi. |

**Kalıntı kusur (onarılmadı, beyan ediliyor):** aile ⑤'in "kod sabiti ↔ yaml anahtarı" eşlemesi
**ad benzerliğine** dayanır (`tif` ↔ `ENTRY_TIF`). Adı benzemeyen bir kopya (ör. `goal.max_drawdown`
↔ `shadowlaw.DD_VETO_MARGIN = 0.04`, kaynağın kendi yorumunda "goal.max_drawdown'un YARISI" diye
yazılı) yalnızca **kaynak yorumu okunduğu için** bulundu. Yorumsuz bir yarı-türev bu taramadan
sessizce geçer.

---

## 2. İKİ YÖNLÜ KALİBRASYON KAPISI — SONUÇ: **3/3, ONARIM GEREKMEDİ**

Brief üç bilinen vakayı şart koşuyordu: bir bilinen-POZİTİF, bir bilinen-NEGATİF, bir bilinen-KAPANMIŞ.

| Vaka | Yön | Beklenen | Ölçülen | Hüküm |
|---|---|---|---|---|
| **(a) Skill yaşam döngüsü** | POZİTİF (kusur bulunmalı) | `ayrismis-simdi` | `skills.catalog()` (`skills.py:194`) 67 kayıt döndürüyor, döndürdüğü sözlükte **`retired` alanı YOK** (canlı alan listesi ölçüldü, 2026-08-08 21:42Z); teşhis kovalarındaki 60 "ölçülmemiş" adın **36'sı** kayıt defterinde `retired: true` | ✅ **ayrismis-simdi** — köre yeniden bulundu |
| **(b) goal/bounds SSoT** | NEGATİF (kusur bulunmamalı) | `kopya-senkron-korumali` | `bounds.yaml` canlı↔repo **BİREBİR** (sha256 `3e810b54…`, 2026-08-09 00:44Z); `goal.yaml` bayt olarak ayrı ama **anahtar/değer düzeyinde fark YOK** (yalnız yorum). Mekanizma **adıyla**: `dagit.sh:95-175` **[1b]** (git-türetilmiş dosya listesi + yaprak-yol düzleştirme + iki-dallı hüküm + fail-closed) · `tests/conftest.py:78-89` içerik-sha256 parmak izi · `tests/test_canli_bekci_v176.py` | ✅ **kopya-senkron-korumali** — KUSUR diye işaretlenmedi |
| **(c) RETIRED_SYMBOLS evren kablolaması** | KAPANMIŞ (korumalı görünmeli) | `kopya-senkron-korumali` | Canlı (2026-08-08 21:46Z): `RETIRED_SYMBOLS`∩`REPLAY_UNIVERSE` = **∅**; `state/bars/*.csv` − evren = **tam olarak** 8 emekli + `SPY` (endeks); evren − CSV = **∅**; finviz keşif listesi ∩ emekli = **∅**. Tek kapı `data.is_retired()` (`adapters/data.py:2620`, büyük/küçük harf normalize). Çivi: `tests/test_evren_emekliligi_v134.py` (kesişim · sayı · tam küme · gerekçe zorunluluğu · endeks muafiyeti · kapsama paydası · pano etiketi · finviz kapısı) | ✅ **kopya-senkron-korumali** |

**Kapı sonucu: 3/3, ilk koşuda.** Yöntem onarımı gerekmedi; ama §1.2'deki Y-1 ve Y-2 tam olarak
kalibrasyonun (b) ve (c) bacaklarının **yanlış-pozitif üretmesini engelleyen** iki durak oldu — yani
iki yönlü kapı boşuna kurulmadı, iki kez ateşlendi.

---

## 3. GERÇEK-AİLE TABLOSU

Kanıt satırları `dosya:satır` biçimindedir. "BUGÜN AYRIK?" sütunu **canlı** ölçümdür.

| # | GERÇEK | KAYNAKLAR (dosya:satır) | TÜKETİCİLER — bölünme | BUGÜN AYRIK? | KOVA |
|---:|---|---|---|---|---|
| 1 | **Skill yaşam döngüsü** ("bu skill emekli mi?") | ① `skills/<ad>/SKILL.md` klasörleri (31) · ② `skills/_emekli/<ad>/` (37 klasör) · ③ `state/skills_registry.json` `retired` alanı (67 kayıt / 36 retired) · ④ `skills.PIPELINES` (`skills.py:79-98`) · ⑤ **`skills.catalog()`** (`skills.py:194`) — 67 DÜZ kayıt, `retired` DÜŞÜRÜLÜR | **BİLEN:** `skills.reconcile_enablement` (`skills.py:129`) · `api.api_public_summary` (`api.py:720-721`) — kayıt defterini DOĞRUDAN okur.<br>**BİLMEYEN (katalogdan okur):** `axis2_diagnosis` (`skills.py:567`) · `recommend_from_attribution` (`skills.py:256`) · `auto_shadow_from_evidence` (`skills.py:434`) · `api._eksen2_ozeti` (`api.py:2471-2499`) · `web/app.js:6128` | **EVET** | **ayrismis-simdi** |
| 2 | **Sermaye tabanı / öz sermaye** | ① `portfolio.json` `cash`+`realized_pnl`+`peak_equity`+`day_start_equity` · ② `heartbeat.json` `equity` · ③ **`equity_curve.json`** 882 nokta · ④ `score.START_EQUITY` (kod sabiti) · ⑤ Alpaca hesabı (ayna paydası) · ⑥ `portfolio.sermaye_resetleri` beyanı (`sermaye.py:80`) | **BOYUTLAMA:** `loop.py:1067` `eq_now` → `derisk_mult` (`loop.py:1070`, `:556`) — ①'i okur, ⑥'ya SORMAZ.<br>**PANO/AYNA:** `health.write_heartbeat` (`health.py:255-272`) → `api.py:3762` pano dalı ②'yi okur (bağımsız bayatlık kanalı, 08-06'da ölçüldü).<br>**HÜKÜM:** `analytics._realized_drawdown` (`analytics.py:1632`) ③'ü okur → `edge_verdict` (`:1926`) + `result_verdict` (`:2242`) → `health.faz6_kilitleri` (`health.py:84-85`).<br>**SINIR:** `ledgerstamp.seed_boundary` (`ledgerstamp.py:149`) ③'ün son noktasını **tohum sınırı** sayar. | **EVET** (③) | **ayrismis-simdi** |
| 3 | **Açık pozisyon adedi** | ① `portfolio.positions` (iç defter) · ② Alpaca hesabı · ③ `broker_reconcile.json` `positions.qty_drift` (mutabakat kaydı) · ④ `heartbeat.open_positions` | ①: tüm boyutlama/çıkış/ısı yolu · ②: gerçek ayna, `api.py:4099` koruma paydası · ③: pano ayna görünümü | **EVET** — 54/64/43/33 (defter) vs 25/37/22/22 (Alpaca), + `external: ["NVDA"]` | **ayrismis-simdi** `[bekçili]` |
| 4 | **Sembol yaşam döngüsü / evren üyeliği** | ① `data.RETIRED_SYMBOLS` (`adapters/data.py:2606`) · ② `data.REPLAY_UNIVERSE` · ③ `state/bars/*.csv` · ④ `finviz_universe.json` | Tek kapı `data.is_retired()` (`:2620`); `marketview.py:256` etiketler, `constituents.py:225,231` sayar, `dataset.py:244` uyarır — hepsi AYNI kapıdan | HAYIR | **kopya-senkron-korumali** |
| 5 | **Hipotez durumu / karne** | ① `hypotheses.jsonl` `status` (`memory.py:92-112`, yasal geçiş kapısı) · ② `scoreboard.json` (TÜREV) | `versioning.py:66` karneyi okur; `watchdog.DERIVED_SOURCES["scoreboard.json"]=["hypotheses.jsonl"]` (`watchdog.py:1792`) türevliği BEYAN eder | **EVET** — karne kaynağının **47,7 saat** gerisinde (`coherence_report`, 2026-08-08 21:54Z) | **ayrismis-simdi** `[bekçili]` |
| 6 | **Emir yaşam döngüsü** | ① `portfolio.armed` + `alpaca_submitted` · ② `mirror_orders.json` (23 emir) · ③ Alpaca emir listesi · ④ `broker_reconcile.alive_order_syms`/`ghosts`/`engine_orphans`/`exit_orphans` | `watchdog.py:356-357` ①'i sayar; `api.py:2805` ②'yi panoya çizer; `loop.reconcile_broker_state` üçünü karşılaştırıp `ALARM_MIRROR_DRIFT` üretir | ③↔① için **EVET** (bkz. #3); ④ **24,3 saat** bayat | **ayrismis-simdi** `[bekçili]` |
| 7 | **Türetilmiş kalibrasyon artefaktları** (14 kalem) | `watchdog.DERIVED_SOURCES` (`watchdog.py:1773-1799`) her türevi kaynağına bağlar; `COHERENCE_GRACE_S=3600` | `coherence_report()` (`watchdog.py:1803`) — pano + tanılama | **EVET, 5/14 bayat** (2026-08-08 21:54Z): `scoreboard` 47,7sa · `self_review` 46,4sa · `arming_report` 46,4sa · `llm_calibration` 24,3sa · `broker_reconcile` 24,3sa | **ayrismis-simdi** `[bekçili]` |
| 8 | **`goal.max_drawdown` (%8)** | ① `state/goal.yaml` · ② `analytics.EDGE_MAXDD_MAX` (`:1614`) · ③ `analytics.RESULT_MAXDD_MAX` (`:2012`) · ④ **`broker.DERISK_FLOOR_DD`** (`broker.py:23`) · ⑤ `shadowlaw.DD_VETO_MARGIN=0.04` (kendi yorumunda "goal'un YARISI") | ②③ hüküm eşiği; ④ **canlı emir boyutu** (`derisk_mult`); ⑤ ship vetosu | HAYIR (dördü de 0,08) | ②③: **korumali** (`tests/test_hafta3a_v119.py:78`, `tests/test_orgu2_v103.py:120`)<br>④⑤: **kopya-korumasiz** |
| 9 | **`execution_v2.tif` (gtc)** | ① `goal.yaml` · ② `broker.ENTRY_TIF` + `ENTRY_TIF_ALLOWED` (`broker.py:82,88`) · ③ **`alpaca.KORUMA_TIF`** (`adapters/alpaca.py:619`) | ②: giriş emri · ③: koruma (OCO) bacağı (`alpaca.py:682`, `api.py:4284`) | HAYIR | ②: **korumali** (`tests/test_koruma_tif_v210.py:94,115`)<br>③: **kopya-korumasiz — BİLİNÇLİ** (`tests/test_koruma_yeniden_kurma_v211.py:345` türetmeyi YASAKLAR) |
| 10 | **Sektör / ısı tavanı** | ① `goal.limits.max_sector_exposure_pct` = 40,0 · ② `bounds.portfolio.sector_cap` max = 30,0 · ③ `guard.SECTOR_CAP_DEFAULT_PCT` = 25,0 (`guard.py:420`) · ④ çalışma-zamanı varsayılanı **0** (`guard.py:542`) — ısı için aynısı: `HEAT_CAP_DEFAULT_PCT`=6,0 (`:421`) vs runtime 0 (`:561`) | ④ tek fiilî tüketici; ③'ün **okuyucusu YOK** (repo genelinde yalnız tanım satırı) | **EVET** — dört farklı sayı aynı tavanı iddia ediyor | **ayrismis-simdi** |
| 11 | **bounds düğme varsayılanları** (32 düğme) | ① `config.default_strategy()` (`config.py:275-293`) · ② `strategy.py` içi `_f(params,…,lit)` · ③ `shadow_lifecycle.LIFECYCLE_READ_DEFAULTS` (`:118-128`) · ④ dağınık `.get` (`loop.py`, `guard.py`, `cf_backfill.py`, `component_ic.py`, `broker.py`, **`counterfactual.DEFAULT_TIME_STOP`** `:24`) | Her motor kendi tablosunu okur | HAYIR (değerler bugün eşit) | ③: **korumali** (`tests/test_golge_v2_yasam_dongusu_v132.py:208-210`, AST kıyası)<br>①②④: **kopya-korumasiz** |
| 12 | **Ayrışan yedek varsayılanlar** | `goal.min_sample`=30 iken `score.py:86` + `shadow_variants.py:561` **20**; `goal.limits.no_trade_before_bars`=3 iken `backtest.py:151` **0**; `goal.slippage_bps`=5 iken `api.py:1691` **0.0** | Yalnız anahtar EKSİKKEN ısırır | Bugün ısırmıyor (anahtarlar dolu) | **kopya-korumasiz** |
| 13 | **HALT** | ① dosya `state/HALT` (tek gerçek) · ② `heartbeat.halted` (fotoğraf) · ③ `goal.limits.kill_switch_file: "state/HALT"` | Tüm kod `health.halted()` çağırır (`health.py:17`); `intraday_shadow.py:121` **açıkça yeniden ölçer** ("kopyalanmaz"); `scheduler.py:1172` dört alanı taşımadan hariç tutar | HAYIR (dosya yok · `health.halted()`=False · `heartbeat.halted`=False) | ②: **kopya-senkron-korumali** (`health.py:266-270` her yazımda yeniden damgalar; çivi `tests/test_health_versioning_gaps_v49.py:69,72`)<br>③: **kopya-korumasiz — BEYANLI** (`goal.yaml:131` "HİÇBİR KOD OKUMAZ" der) |
| 14 | **INTRADAY_ARM / Faz-6 silahlanma** | ① dosya `state/INTRADAY_ARM` (`health.py:57`) · ② `health.faz6_kilitleri()` beş kilidi | ② ①'i `operator_onayi` kilidi olarak **okur** — ikinci kaynak değil, aynı kaynağın tüketicisi | HAYIR (dosya VAR · `operator_onayi` = açık · zincir 1/5, 2026-08-08 21:54Z) | **tek-kaynak** |
| 15 | **autonomy_level / MODE** | ① `goal.limits.autonomy_level` (0) · ② `heartbeat.autonomy_level` (0) · ③ `config.MODE` env (paper) · ④ `heartbeat.mode` (paper) | ②④ her nabız yazımında yeniden damgalanır (`health.py:266-270`) | HAYIR | **kopya-senkron-korumali** |
| 16 | **Zaman damgaları (seans sınırı)** | `portfolio.last_date` · `heartbeat.last_bar` · `data_quality.date` · `scheduler.status().latest_session` · `bars_source.json` (252 anahtar = 251 evren + SPY) | `loop.py:987` `waiting_for_universe` / `:998` `refused_regressive` kapıları; `watchdog.monotonicity_report` | HAYIR — **beşi de** `2026-08-07` (2026-08-08 21:46Z) | **kopya-senkron-korumali** |
| 17 | **Nabzın çok-yazarlı alanları** | `heartbeat.json` `regime`/`exposure_budget_pct`/`equity`/`last_bar` — günlük döngü, worker, replay tohumu ayrı ayrı yazar | `watchdog.OWNED_FIELDS` (`watchdog.py:1955`) + `ownership_report()` (`:1958`) sahiplik dedektörü | HAYIR (`ownership_report`: `ok: true`, `lost: []`) | **kopya-senkron-korumali** |
| 18 | **Kart eşikleri ↔ kod literalleri** | 24 ön-kayıt kartı (`research/cards/`) ↔ `meridian/` + `research/olcumler/` literalleri | Kart hükmü verir, kod ölçer | **38 nicelikte UYUMLU · 4'ünde AYRIK** (§4.6) | uyumlu 38: **kopya-korumasiz** (kartı koda bağlayan HİÇBİR kapı yok)<br>ayrık 4: **ayrismis-simdi** |
| 19 | **Pano paydaları** | `web/app.js` + `api.py` — sayı kaynağı ya defterden gelir ya JS literalidir | `hucreCubuk` paydasız çubuk çizmeyi REDDEDER (`app.js:1665-1669`); `ozetHucre` paydasız oranı düşürür (`:1849`) | ~24 payda defterden türer; **12 kalem literal** (§4.7) | çoğu **kopya-korumasiz**; `app.js:5432-5436` **ayrismis-simdi** |
| 20 | **Systemd birim dosyası** | ① `deploy/oracle-a1/meridian.service` (native uvicorn, 11 `Environment=` satırı) · ② `deploy/meridian.service` (docker compose oneshot) | **Tüm testler ①'i çiviler**: `tests/test_h3_tur2_v174.py:39` · `tests/test_kovab_kucuk_v165.py:38` · `tests/test_authority_boundaries_v77.py:1033`. **`README.md:118` ②'yi "the systemd unit" diye gösterir.** | **EVET** — belge yanlış kopyayı işaret ediyor | **ayrismis-simdi** |
| 21 | **Repo ağacı ↔ canlı ağaç (kod)** | `meridian/**/*.py` — 95 dosya | dagit `--kuru` farkı + [1b] + mtime kontrolü | **95 dosyanın 2'si ayrı**: `api.py`, `codelaw.py` (sha256, 2026-08-09 00:47Z) | **ayrismis-simdi** `[bekçili]` — beklenen dağıtım kuyruğu |
| 22 | **`plan.dormant_setup`** | `loop.py:1380` · `cf_backfill.py:109` · `mutation.py:176` · `shadow_variants.py:247` · şema `storage.py:103` — **ve** `counterfactual.py:118` aynı gerçeği `"dormant"` diye YENİDEN ETİKETLER | Dördüncü kova ölçtü: diskten okuyup **DAVRANAN yok** | (dördüncü kovanın hükmü değişmedi) | **operator-kalemi** (ROADMAP:205) — bu tur yalnız çapraz-referans |

---

## 4. BULGULAR — ŞİDDET SIRALI

### 4.1 ⛔ EN AĞIR — DONMUŞ SERMAYE EĞRİSİ BİR **KAPI** BESLİYOR (aile #2)

**Ayrışma (canlı, 2026-08-08 21:46Z ve 21:52Z):**

| Kaynak | Değer | Damga |
|---|---|---|
| `portfolio.json` (kitap) | cash 99.549,62 · realized_pnl −450,38 · peak 100.000,0 | `last_date` = 2026-08-07 |
| `heartbeat.json` | equity 99.303,11 | ts 2026-08-08 21:41:54Z |
| **`equity_curve.json`** | **son nokta `["2026-07-20", 94.457,91]`** (882 nokta, ilki 2023-01-12) | 1 Ağustos'tan beri yazılmadı |

Eğrinin son noktası **19 gün geride** ve **1 Ağustos reset'inden ÖNCEKİ tabanda** (94.457,91 —
`docs/BAYAT-SERMAYE-KOK-2026-08-07.md`'nin bayat sayısının ta kendisi). Bu **bir arıza değil, bir
TASARIM** — eğrinin kendi `reset_isaretleri` kaydı bunu yazıyor: *"eğrinin son noktası ledgerstamp'in
tohum sınırıdır"*. Nitekim `ledgerstamp.seed_boundary()` (`ledgerstamp.py:149`) onu **tam olarak öyle**
okuyor ve canlıda `replay_end = 2026-07-20` döndürüyor.

**KUSUR, İKİNCİ TÜKETİCİDE:** `analytics._realized_drawdown()` (`analytics.py:1632`) **aynı noktaları**
*"GÜNLÜK piyasaya-göre eğri"* diye okur ve düşüşünü kapanmış-işlem eğrisiyle **kötü olan** kuralında
birleştirir. Canlı ölçüm (2026-08-08 21:52Z):

```
kapali_islem_dd = 0,0599   (trades.jsonl'den, 96 işlem — CANLI)
gunluk_m2m_dd   = 0,0804   (equity_curve.json'dan, 882 nokta — 2026-07-20'de DONMUŞ)
max_dd          = 0,0804   ← kötü olan seçildi
```

`analytics.py:1944` `_dd_ok = dd["max_dd"] <= EDGE_MAXDD_MAX` (0,08) ⇒ **0,0804 > 0,08, ölçüt DÜŞÜYOR.**
Bu ölçüt `edge_verdict` → `health.faz6_kilitleri` zincirinde (`health.py:84-85`) bir **KİLİT**tir; canlı
zincir 1/5 açık ve kapalı olanlardan biri `edge_kaniti` (canlı: *"1/5 sağlandı"*).

Yani: **canlı kâğıt döneminin (2026-07-21 → 08-07) piyasaya-göre düşüşü hükümde HİÇ YOK**, buna karşılık
**tohum döneminin düşüşü güncelmiş gibi sayılıyor** — ve kilidi düşüren sayı odur. Ek olarak
`_realized_drawdown` `sermaye.ofset()`i **hiç sormaz**; eğri eski tabanda, kitap yeni tabanda.

**Neden kimse bağırmıyor:** `equity_curve.json` `watchdog.DERIVED_SOURCES` listesinde **YOK**
(`watchdog.py:1773-1799`, 14 kalem) — yani bu depodaki tek genel bayatlık dedektörü ona bakmıyor.
`recompute`in `equity_curve_tail` kimliği (`recompute.py:242-252`) eğrinin son noktasını **beyan
ofsetiyle** düzelterek nakde bağlar ve **YEŞİL** kalır (canlı `recompute.report()`: `realized_pnl`
kimliği yeşil, ofset +5.542,09 uygulanmış) — yani var olan kimlik, eğrinin **tazeliğini** değil
**iç tutarlılığını** ölçüyor. `BAYAT-SERMAYE-KOK`'un B3 önerisinin (taban sıçraması dedektörü)
kardeşi burada da eksik.

**Şiddet: YÜKSEK.** Bir ship/Faz-6 kilidi, 19 gün bayat ve yanlış tabanlı bir seriden hüküm alıyor.

**Önerilen kapama SINIFI: `tüketici-taşıma`.** `_realized_drawdown`in günlük bacağı, tohum eğrisinden
**canlı** bir m2m serisine taşınmalı (ya da tohum bacağı adıyla ayrılıp hükümden çıkarılmalı).
İkincil: `equity_curve.json` `DERIVED_SOURCES`e girerse "kaynak ilerledi, türev durdu" en azından
**görünür** olur — ama bu bir yama olur, kök tüketici ayrımıdır.

---

### 4.2 ⛔ POZİSYON ADETLERİ FİİLEN AYRIK — ARTI DEFTERİN BİLMEDİĞİ BİR POZİSYON (aile #3, #6)

Canlı `broker_reconcile.json` (yazım damgası 2026-08-07T20:33:02Z):

| Sembol | iç defter | Alpaca |
|---|---:|---:|
| NUE | 54 | 25 |
| EMR | 64 | 37 |
| BKNG | 43 | 22 |
| AMGN | 33 | 22 |

Kökü `docs/BAYAT-SERMAYE-KOK-2026-08-07.md`'de ölçüldü (çarpan 0,4916). **Bu tur iki YENİ şey ekliyor:**

1. **`positions.external = ["NVDA"]`** — Alpaca'da motorun hiç açmadığı bir pozisyon var.
   `loop.py:2045` bunu bilerek **alarmsız** listeler ("operatörün kendi varlığı olabilir"). Ama
   `api.py:4099`'un **koruma paydası** Alpaca pozisyonlarından türer — yani "kaç pozisyon korumasız"
   sorusunun paydası, iç defterin hiç bilmediği bir satırı içeriyor.
2. **Mutabakat kaydının kendisi bayat:** `coherence_report` (2026-08-08 21:54Z) `broker_reconcile.json`ı
   kaynağının **24,3 saat** gerisinde buluyor. Pano ayna görünümü dünden konuşuyor.

Ayrıca bir **isim çakışması**: aynı belgede `mirror_drift: false` iken `position_drift` doğru ve
`qty_drift` dört satır taşıyor (`loop.py:2148-2150`). İki alan iki farklı sapmayı adlandırıyor ama
pano dilinde ikisi de "ayna sapması" diye okunabilir.

**Şiddet: YÜKSEK** (operatör kararı bekliyor — melez portföy).
**Önerilen kapama SINIFI: `tek-kaynağa indirme`** (aynayı büyüt / kitabı küçült / olduğu gibi bırakıp
BEYAN et) — üçü de operatör kararıdır; ölçüm tarafında yapılacak tek şey `BAYAT-SERMAYE-KOK` §8'in
**B2 `drift_sinifi`** alanıdır: sapma bugün **adsız**.

---

### 4.3 ⛔ SKİLL YAŞAM DÖNGÜSÜ — TÜREV, KAYNAĞIN BİLDİĞİ ALANI DÜŞÜRÜYOR (aile #1, kalibrasyon (a))

**Sayılar (canlı, 2026-08-08 21:42Z):**

| Ölçüm | Değer |
|---|---:|
| `skills_registry.json` kayıt | 67 |
| `retired: true` | 36 |
| `skills/` aktif klasör (SKILL.md'li) | 31 |
| `skills/_emekli/` klasör | 37 |
| `skills.catalog()` kayıt | 67 |
| `catalog()` çıktısında `retired` alanı | **YOK** |
| `axis2_status.json` (ts 2026-08-07T20:12:26Z) `gercek_katman_olculmemis` | 57 |
| … `_cf_dolu` | 3 |
| **60 "ölçülmemiş" adın kayıt defterinde `retired: true` olanı** | **36** |

`catalog()` (`skills.py:194`) kayıt defterini **zaten okuyor** (`reg = registry().get("skills", {})`) ve
oradan `category`/`enabled`/`mode`/`shadow`/`pipeline` alanlarını taşıyor — **`retired` hariç**. Tek bir
alanın düşmesi, aşağıdaki her tüketiciyi kör ediyor:

* `axis2_diagnosis` (`skills.py:567`) — 36 arşiv kaydı "gerçek katmanda hiç ölçülmemiş" kovasına
  düşüyor; oysa **hiç ölçülmeyecekler**, çünkü zincirden çıkarıldılar.
* `api._eksen2_ozeti` (`api.py:2486-2496`) — payda `f"katalogda beyan edilen skill sayısı ({toplam})"`
  = **67**.
* `web/app.js:6128` — *"⟨N⟩ gerçek katmanda hiç ölçülmemiş"*.

Yani panonun **sayısı doğru, ETİKETİ yanlış**: 57'nin çoğu "ölçemedik" değil, "bilerek arşivledik".
Karşıt kanıt aynı dosyada: `api.api_public_summary` (`api.py:720-721`) **kayıt defterini doğrudan**
okuyup `skills_live` = 31 / `skills_enabled` = 30 veriyor (canlı doğrulandı). **Aynı uygulama, aynı
gerçek hakkında iki farklı sayı yayınlıyor: 67 ve 31.**

**Yan bulgu (arşivin kendi sayımı da üç ağızdan konuşuyor):** brief 38 diyor · `skills/_emekli/README.md`
+ `skills.py:10` docstring'i 37 (22 emekli + 15 birleştirilen) diyor · ölçüm 37 klasör / **36** SKILL.md /
**36** `retired` kaydı buluyor. Fark tek bir kalemde: `skills/_emekli/shadow` — SKILL.md'si YOK ve kayıt
defterinde HİÇ yok (README onu "boş bir klasör artığı" diye emekli etmiş, ama kayıt satırı hiç olmamış).

**Şiddet: ORTA-YÜKSEK** (para yolunda değil; ama Eksen-2 öğrenme paydasını ve operatöre giden karneyi
zehirliyor — "üreteç 67 skilde başarısız" ile "31 skilde 2'sinde hüküm var" aynı piksele düşüyor).

**Önerilen kapama SINIFI: `tüketici-taşıma`** — `catalog()` `retired`ı taşısın (kaynağı ZATEN okuyor);
`axis2_diagnosis` arşiv kayıtlarını ya dışlasın ya `arsivlenmis` diye AYRI kovaya koysun.
Nokta atışı çivi: `set(catalog'da retired) == set(registry'de retired)`.

---

### 4.4 ⚠ SEKTÖR/ISI TAVANI — AYNI TAVANI DÖRT SAYI İDDİA EDİYOR, İKİSİ ÖLÜ (aile #10)

| Kaynak | Değer |
|---|---:|
| `goal.limits.max_sector_exposure_pct` | 40,0 |
| `bounds.portfolio.sector_cap` üst sınırı | 30,0 |
| `guard.SECTOR_CAP_DEFAULT_PCT` (`guard.py:420`) | 25,0 |
| **fiilî çalışma-zamanı varsayılanı** (`guard.py:542` `p.get("portfolio.sector_cap", 0)`) | **0** (kapı KAPALI) |

Aynısı ısı için: `guard.HEAT_CAP_DEFAULT_PCT = 6,0` (`guard.py:421`) vs `guard.py:561` runtime `0`.
**Elle doğrulandı:** iki sabitin repo genelinde (kod + testler) **tanım satırından başka hiçbir
kullanımı yok** — okuyucusu sıfır. Yani yorumlarında "bandın alt ucu (muhafazakâr)" diye anlatılan iki
sayı hiçbir şeyi kapamıyor; kapı gerçekte `cap_pct > 0` koşuluyla **tamamen kapalı**.

Pano bunu ikinci kez yanlış anlatıyor: `app.js:5432` `_y3Etkin` en fazla **2** olabilir (yalnız
`sector_cap_pct` + `heat_cap_pct`), ama `app.js:5435` paydası **4** ("Y3 kolu (dörtlü)") ve hemen yanındaki
`app.js:5436` `2 - _y3Etkin` **2** üzerinden konuşuyor — **tek ifadede iki farklı toplam**.

**Şiddet: ORTA** (kapı bugün zaten kapalı; ihlal, kapının **açık sanılması** riskinde).
**Önerilen kapama SINIFI: `tek-kaynağa indirme`** — ya iki sabit silinir (ölü), ya `guard.py:542/561`
varsayılanı onlara bağlanır; ve `goal`/`bounds` çelişkisi (40 vs 30) tek bir tavana indirilir.

---

### 4.5 ⚠ BEŞ TÜREV ARTEFAKT KAYNAĞININ GERİSİNDE (aile #5, #7)

`coherence_report()` (canlı, 2026-08-08 21:54Z) — 14 kayıtlı türevin **5'i** bayat:

| Türev | Kaynağının gerisinde | Ne anlatır |
|---|---:|---|
| `scoreboard.json` | 47,7 sa | öğrenme karnesi hipotez defterinin gerisinde |
| `self_review.json` | 46,4 sa | öz-değerlendirme eski kalibrasyondan konuşuyor |
| `arming_report.json` | 46,4 sa | silahlanma ölçümü eski cf defterinden |
| `llm_calibration.json` | 24,3 sa | LLM görüş↔sonuç kalibrasyonu |
| `broker_reconcile.json` | 24,3 sa | pano ayna görünümü (bkz. §4.2) |

Bu **bekçili** bir ayrışmadır — mekanizma (`watchdog.DERIVED_SOURCES` + `coherence_report`) çalışıyor ve
sapmayı saatiyle söylüyor. Sınıf açısından önemli olan iki şey: (a) mekanizma **var ve doğru işliyor** —
bu depoda çift-kaynak sorununun **çözülmüş** hâlinin şablonu budur; (b) listeye **girmeyen** kopyalar
(en ağırı `equity_curve.json`, §4.1) bu şablonun dışında kalıyor.

**Şiddet: ORTA-DÜŞÜK** (görünür borç). **Kapama SINIFI: yok — mekanizma yerinde; kadans sorusu Rol-1'in.**

---

### 4.6 ⚠ KART ↔ KOD: 38 UYUMLU, 4 AYRIK — VE BİR ÇİVİ KENDİ TOLERANSIYLA ÖRTÜLMÜŞ (aile #18)

24 ön-kayıt kartında ilan edilen eşiklerin **38'i** kodda birebir karşılığını buldu (de-risk rampası
%3/%8 ↔ `broker.py:220,224` + `broker.py:23`; `n_min=20` ↔ `faz5_cikis.py:48`; kill#4 %20 ↔
`faz5_cikis.py:53`; `MAX_ENTRY_GAP_PCT` %4 ↔ `broker.py:17`; SPY SMA 200 ↔ `regime.py:181`; …).
**Kartı koda bağlayan hiçbir kapı yok** — 38'inin hepsi `kopya-korumasiz`.

Dört ayrık kalem:

| # | Nicelik | Kart | Kod | Not |
|---|---|---|---|---|
| **D1** | Pozitif-kontrol çivisi (rvol20 @20) | **0,0642** (EDG-2026-015/016/017/020) · **0,0645** (EDG-2026-002/007/010) · **≈0,064** (EDG-2026-011/012/021) | `PK_CIVI_HEDEF = 0.0645` (`research/olcumler/wp2_olcum/k016.py:31`) | Kod **kendi kaynağında itiraf ediyor**: *"kart guard'ı 0.0642'yi anıyor; pk.py'nin kayıtlı hedefi 0.0645"*. Fark `PK_CIVI_TOL = 0.005` (`:32`) tarafından **örtülüyor**. Tek bir çivi için **üç** kart değeri + bir kod değeri. |
| **D2** | `prox_max` | EDG-2026-015 canlı değeri **2,3** diye kaydeder | `strategy.py:376` varsayılanı **2,0** | Kart ↔ canlı yapılandırma uyumlu; **kod varsayılanı üçüncü sayı**. |
| **D3** | Bootstrap tekrarı | EXE-2026-002: **10.000** | `faz5_cikis.py:50` = 10.000 **ama** ölçüm şasisi (`wp2_olcum/ortak.py`, `wp1_rvol_form/ortak017.py`, `inplay_postevent/ortak020.py`) = **2.000** | Depoda iki bootstrap standardı. |
| **D4** | Bootstrap tohumu | kartlarda YOK | `olcum_araclari.py:470` + `faz5_cikis.py:51` = **11**; `kys_olcum/pk_kys.py:51` = **20260802** | `research/qc_dogrulama/qc_defter_021_c.py:395` sapmayı zaten beyan etmiş. |

**Şiddet: ORTA** (ölçüm zemininde, canlı emirde değil — ama pozitif kontrol, bütün WP2 hükümlerinin
"ölçüm doğru mu" kapısıdır ve o kapı bugün **kendi toleransıyla** geçiyor).
**Önerilen kapama SINIFI: `tek-kaynağa indirme`** — çivinin bir kanonik değeri olsun, kartlar onu
alıntılasın; ikincil olarak bir `senkron-testi`: kart YAML'ındaki sayısal eşikleri, ilgili
ölçüm modülünün sabitleriyle kıyaslayan bir kapı (bugün YOK).

---

### 4.7 ⚠ PANO PAYDALARI: 12 LİTERAL — BİRİ **PAYLOAD'I HİÇ TAKİP EDEMEZ** (aile #19)

Pano gerçekten bir **payda sözleşmesi** uyguluyor (`app.js:1665-1669` paydasız çubuk çizmeyi reddeder;
`:1849` paydasız oranı düşürür) ve ~24 payda kaynak defterden türüyor. Kalan 12 kalem literal; en ağır üçü:

1. **`refetch_max` — bir sayının BEŞ kopyası.** Otorite `scheduler.DENSE_ATTEMPTS = 8`
   (`scheduler.py:181`, tüketicisi `:917`). Ama `api.py:3702` sayıyı **yeniden yazıyor**
   (`"refetch_max": 8`), `app.js:3010/5696/5715` üç kez `?? 8` / `|| 8` yedekliyor, ve
   `app.js:5723` başlığı **`<b>8 adımlı sabır sayacı</b>`** diye **sabit** yazıyor — bu bir yedek değil,
   payload değişse bile **"8" demeye devam edecek** bir metin. C10 ihlali.
2. **`app.js:4851` `ev.passed / 5` ve `app.js:5052` `rv.passed / 4`.** `analytics.py:1970` paydayı
   `n = len(criteria)` diye **türetiyor** ve satırın kendi yorumu bunu "sabit yazılmadığı için" diye
   övüyor — ama dönüş sözlüğü `n`i **yayımlamıyor**, dolayısıyla pano sabit yazmak zorunda kalıyor.
   Aynı literal Python tarafında da var: `health.py:139` `or 5`, `:145` `or 4`.
3. **`app.js:5432-5436`** — §4.4'te anlatılan yapısal olarak %50'de tavanlanan çubuk. **Bugün yanlış.**

Diğerleri (`KANIT_TAVAN_N = 61` ~18 kanıt çubuğunun paydası, `DONGU_TAZELIK_SAAT = 24`,
`KITAP_KZ_BANT = 0.02`, `AZ_ORNEK_N = 10`, `sma.window ?? 200`, `earnings … /5`) **kopya-korumasiz** —
değerler bugün tutarlı, kapı yok. `app.js:1652` `KANIT_TAVAN_N`i dürüstçe *"bir EŞİK DEĞİL bir GÖRÜNTÜ
ÖLÇEĞİ"* diye beyan ediyor; beyanı olan kopya, olmayanından iyidir.

**Şiddet: DÜŞÜK-ORTA.** **Kapama SINIFI:** #1 ve #2 için `tüketici-taşıma` (uç, sayıyı **servis etsin**;
`edge_verdict`/`result_verdict` dönüşüne `n` eklensin — pano zaten okumaya hazır), #3 için düzeltme.

---

### 4.8 ⚠ İKİ SYSTEMD BİRİMİ, BELGE YANLIŞ OLANI GÖSTERİYOR (aile #20)

`deploy/oracle-a1/meridian.service` = fiilen canlı olan (native uvicorn, `MERIDIAN_BROKER=alpaca_paper`,
`EnvironmentFile=-/opt/meridian/.dash.env`, sertleştirme blokları) — **üç ayrı test dosyası onu çiviliyor**
(`test_h3_tur2_v174.py:39`, `test_kovab_kucuk_v165.py:38`, `test_authority_boundaries_v77.py:1033`).
`deploy/meridian.service` = docker-compose çağı kalıntısı (`Type=oneshot`, `ExecStart=docker compose up`),
**hiçbir test onu okumuyor**. `README.md:118` yeni operatöre **bunu** kurmasını söylüyor.

**Şiddet: DÜŞÜK** (bugün kimseyi yakmıyor) ama **sınıfın saf örneği**: iki dosya aynı gerçeği iddia ediyor,
kapı birini biliyor, belge diğerini.
**Önerilen kapama SINIFI: `tek-kaynağa indirme`** (docker birimi emekliye ya da adı `-docker` yapılıp
README düzeltilsin).

---

### 4.9 ⚠ AYNI SAYININ TESTSİZ DÖRDÜNCÜ KOPYASI: `broker.DERISK_FLOOR_DD` (aile #8)

`goal.max_drawdown = 0,08`ün kodda üç kopyası var; **ikisi** goal'a test-kaynaklı bağlı
(`tests/test_hafta3a_v119.py:78`, `tests/test_orgu2_v103.py:120` — ikisi de `== float(config.goal()["max_drawdown"])`).
Üçüncüsü `broker.DERISK_FLOOR_DD = 0.08` (`broker.py:23`) ve **goal'a hiçbir test onu bağlamıyor** —
tek çivisi kendi literaline (`tests/test_mutborc_broker_derisk_mult_v148.py:142`, `(100-92)/100`).

Bu, aile #8'in **en tehlikeli** ucudur çünkü diğer ikisi bir *hüküm eşiği*, bu bir *emir boyutu*:
`derisk_mult` (`broker.py:213-224`, ikizi `max_positions_at` `:227`) canlı pozisyon adedini bu sayıdan üretir. Operatör `goal.max_drawdown`ı
değiştirirse iki hüküm eşiği testle takip eder, **boyutlama rampası yerinde kalır**.

Kardeş vaka: `COMPOSITE_MAX_KNOBS = 3` **iki modülde** tanımlı (`guard.py:68` ve `hermes_composite.py:57`),
`guard.py:68`in yorumu diğerine işaret ediyor ama ikisini bağlayan test yok.

**Şiddet: ORTA.** **Kapama SINIFI: `senkron-testi`** (mevcut iki testin desenini `DERISK_FLOOR_DD` ve
`COMPOSITE_MAX_KNOBS` için tekrarlamak — en ucuz kapama).

---

### 4.10 ▪ AYRIŞAN YEDEK VARSAYILANLAR (aile #12) — bugün ısırmıyor

`goal.min_sample = 30` iken `score.py:86` ve `shadow_variants.py:561` **20**'ye düşüyor;
`goal.limits.no_trade_before_bars = 3` iken `backtest.py:151` **0**'a; `goal.slippage_bps = 5` iken
`api.py:1691` **0.0**'a. Üçü de yalnız anahtar EKSİKKEN devreye girer ve bugün anahtarlar dolu — ama
yedek değerin **kendisi** ikinci bir gerçek beyanıdır ve `goal.yaml`ı okumayan bir yolda sessizce yürürlüğe girer.
**Şiddet: DÜŞÜK.** **Kapama SINIFI: `tek-kaynağa indirme`** (yedek `config.goal()`ten türesin).

---

## 5. ÖLÇÜLEMEYENLER — ADIYLA

| # | Ölçülemeyen | Neden | "0" DEĞİL, ne demek |
|---|---|---|---|
| 1 | **Canlı `meridian.service` biriminin fiilî `Environment=` satırları** | `/etc/systemd/system/meridian.service` okuma denemesi ve koşan sürecin `/proc/<pid>/environ` okuması **yerel izin katmanı tarafından reddedildi** (iki ayrı deneme) | Birim dosyasının **repo kopyası** okundu (`deploy/oracle-a1/meridian.service`); worker'ın `BROKER` değeri **dolaylı** ölçüldü (§1.2 Y-1). `MODE`/`autonomy_level` için nabzın kendi damgası kullanıldı. Canlı birimin repo kopyasıyla **birebir** olduğu bu turda DOĞRULANMADI. |
| 2 | **Alpaca hesabının BUGÜNKÜ öz sermayesi ve pozisyonları** | Ağ çağrısı bilerek yapılmadı (tur sınırı: broker'a dokunma) | Pozisyon adetleri `broker_reconcile.json`ın **2026-08-07T20:33:02Z** damgalı kaydından okundu — yani "Alpaca bugün 25 tutuyor" DEĞİL, "son mutabakat 25 ölçtü" |
| 3 | **`api.py` / `codelaw.py` canlı↔repo farkının YÖNÜ ve İÇERİĞİ** | `git` bu turda YASAK (§tur sınırı); iki dosyanın diff'i tur-ayrıklığı sözleşmesine girer (`tests/test_onay_kapisi_v215.py` başka ajanda) | Fark **var** (sha256, 2026-08-09 00:47Z) ve **yalnız bu iki dosyada**; hangi tarafın ileri olduğu ölçülmedi |
| 4 | **§4.1'in karşı-olgusu: canlı m2m eğrisiyle `max_dd` kaç çıkardı** | Böyle bir seri diskte YOK (üretecek kod yok — `equity_curve.json`ın tek canlı yazarı `run.replay_seed`, `sermaye.uygula`, `mutation`) | Kilidin **bugün** düştüğü ölçüldü (0,0804 > 0,08); doğru seriyle düşer mi düşmez mi **bilinmiyor** ve uydurulmuyor |
| 5 | **`axis2_status.json`ın canlı tazeliği** | Damgası 2026-08-07T20:12:26Z; kadansın neden 2026-08-08'de yazmadığı bu turun konusu değil | Ölçülen sayım o damgaya aittir; bugünkü katalogla yeniden koşulmadı (koşmak yazım olurdu) |
| 6 | **`skills/_emekli` sayımındaki 38 ↔ 37 ↔ 36 üçlemesinin kökeni** | Brief'in 38'i, README/docstring'in 37'si ve ölçümün 36 kaydı arasındaki farkın **hangi turda** doğduğu izlenmedi | Bugünkü envanter kesin: 37 klasör · 36 SKILL.md · 36 `retired` kaydı · `_emekli/shadow` üçünde de tek başına ayrık |

---

## 6. SAYIM ÖZETİ

**Yürünen gerçek-ailesi: 22** (tablo §3).

| KOVA | Aile sayısı | Hangileri (§3 numaraları) |
|---|---:|---|
| `tek-kaynak` | **1** | 14 |
| `kopya-senkron-korumali` | **6** | 4, 13(②), 15, 16, 17, 11(③) |
| `kopya-korumasiz` | **7** | 8(④⑤), 9(③), 11(①②④), 12, 13(③), 18(38 uyumlu eşik), 19(çoğu payda) |
| `ayrismis-simdi` | **8** | 1, 2, 3, 5, 6, 7, 10, 20 (+ 18'in 4 eşiği, 19'un 1 paydası, 21) |
| `operator-kalemi` (çapraz-referans) | **1** | 22 |

> Bir aile birden çok kovada görünebilir: kaynaklardan biri korumalı, diğeri değilse (ör. #8: iki
> kopya testli, iki kopya testsiz) satır **her iki** kovada sayılır. Bu bilinçlidir — kova, ailenin
> değil **kopyanın** hükmüdür.

**Kalibrasyon:** 3/3, **onarım gerekmedi** (ilk koşuda geçti). İki yönlü kapı iki kez ateşlendi ve
iki yanlış-pozitifi durdurdu (§1.2 Y-1, Y-2).

**Şiddet dağılımı:** YÜKSEK 2 (§4.1 sermaye eğrisi kapısı · §4.2 pozisyon ayrışması) · ORTA-YÜKSEK 1
(§4.3 skill kataloğu) · ORTA 4 (§4.4, §4.6, §4.9, §4.5) · DÜŞÜK 3 (§4.7, §4.8, §4.10).

**Önerilen kapama sınıflarının dağılımı:** `tüketici-taşıma` 3 (§4.1, §4.3, §4.7) ·
`tek-kaynağa indirme` 5 (§4.2, §4.4, §4.6, §4.8, §4.10) · `senkron-testi` 1 (§4.9) ·
mekanizma zaten yerinde 1 (§4.5).

---

## 7. BU TURUN HÜKMÜ — TEK CÜMLE

Bu depoda çift-kaynak sorununun **çözülmüş şablonu vardır ve çalışır** (`watchdog.DERIVED_SOURCES` +
`coherence_report` bugün beş bayat türevi saatiyle bağırıyor; `dagit [1b]` yorum farkıyla değer farkını
ayırt ediyor; `OWNED_FIELDS` nabzın dört çok-yazarlı alanını koruyor) — **asıl borç, o şablonun DIŞINDA
kalan kopyalardadır**, ve bunların en ağırı bir defter değil bir **TÜKETİCİ AYRIMIDIR**: `equity_curve.json`
aynı anda hem "tohum sınırı" (doğru okuma) hem "günlük piyasaya-göre eğri" (yanlış okuma) diye okunuyor ve
19 gün bayat, reset-öncesi tabanlı bir seri bugün bir Faz-6 kilidini düşürüyor. Aynı desen küçük ölçekte
her yerde: `catalog()` kaynağın bildiği `retired` alanını düşürüyor, `analytics` paydayı türetip
yayımlamadığı için pano onu sabit yazıyor, kart çivisi kendi toleransıyla örtülüyor. **Kopyanın kendisi
kusur değildir; kusur, kopyanın hangi soruyu cevapladığının yazılı olmamasıdır.**
