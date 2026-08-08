# ARTEFAKT TARAMASI — 2026-08-07

**Ölü-mekanizma avının DÖRDÜNCÜ kovası.** Okuyucusu: Rol-1 + operatör (YASA 6 tamam).
Bu tur **SALT ÖLÇÜM + BELGE**: `meridian/` altında hiçbir dosya değişmedi, git koşulmadı, canlıya
dağıtım yapılmadı, `serve.sh` koşulmadı, broker'a emir gönderilmedi. Yazılan tek dosya budur.

---

## 0. NİYE VAR — mevcut bekçinin ölçülmüş körlüğü

Bugün iki tehlikeli kusur hiçbir beyan taşımıyordu ve mevcut YASA-6 bekçisinden
(`meridian/codelaw.py:458 artifact_graph`) **kaçtı**. Kaçış nedeni yapısaldır ve kodun kendisinde
okunabilir — `codelaw.py:513-519`:

```
external = sorted(set(readers) - set(writers))
"unread": bool(writers) and not external
```

Bekçinin sorduğu tek soru şudur: *"bu artefaktı BAŞKA bir modül okuyor mu?"* Sormadığı soru:
*"okuyan DAVRANIYOR mu?"* Bir artefakt bir sözlüğe konup HTTP gövdesine basıldığında
`external_readers` dolar, `unread` False olur ve bekçi susar — mekanizma ölü olsa bile. Bu tur o
üçüncü soruyu envanterin TAMAMINA sorar.

Üç katman (her artefakt için ayrı ayrı ölçülür):

| Katman | Soru | Yanlış cevabın bedeli |
|---|---|---|
| ÜRETİCİ | Kim yazıyor? | Üreticisiz okuma = fail-open / bayat disk |
| OKUYUCU | Kim okuyor? | Okuyucusuz yazım = ölü yazım (YASA 6) |
| DAVRANIŞSAL TÜKETİCİ | Okunan değer bir **dallanmayı / emri / kapıyı / alarmı / kadans kararını** değiştiriyor mu? | Değiştirmiyorsa bu **GÖRÜNÜRLÜK**'tür, davranış değil — `dormant_setup` sınıfı |

---

## 1. YÖNTEM (ve yöntemin kendi arızaları)

**Kapsam.** `meridian/*.py` (86 dosya) + `meridian/adapters/*.py` (13 dosya). AST ile taranan
çağrılar: `write_json · write_jsonl · append_jsonl · write_text · merge_dated_jsonl · read_json ·
read_jsonl · read_text · update_json · update_jsonl · stamp · mtime · db_backed`. Buna ek olarak
elle: bayrak dosyaları (`config.STATE / "..."` yoklamaları), `goal.yaml`/`bounds.yaml` bölümleri ve
CANLI `state/` listesiyle çapraz kontrol.

**Davranış ölçümü nasıl yapıldı.** Salt "okuma var mı" yetmediği için üç aşamalı bir veri-akış izi
kuruldu:

1. **Fonksiyon-içi TAINT yayılımı.** Okunan değerin atandığı isim tohumdur; `Assign / AugAssign /
   For / comprehension / with / walrus` üzerinden sabit noktaya kadar yayılır. Sonra kirlenmiş her
   `Name` kullanımı bir **dal bağlamında** mı diye sorulur (`If.test`, `While.test`, `IfExp.test`,
   `Assert`, `comprehension.ifs`, `Raise`, ya da `obs.alarm/notify.send/submit_order/cancel_order/
   close_engine_position/replace_order_stop` gibi davranışsal çağrı argümanı).
2. **Fonksiyonlar-arası yayılım.** Değer bir fonksiyonun `return`'üne akıyorsa, o fonksiyonun
   ÇAĞIRANLARI sonucu üzerinde dallanıyor mu diye bakılır (erişimci-fonksiyon sınıfı).
3. **Şiddet katmanlaması.** Dallar iki sınıfa ayrıldı: **güçlü** (`if/while/raise/assert` ya da
   davranışsal çağrı) ve **zayıf** (`ternary`/`comp-if` — çoğu zaman biçimlendirme ya da rapor
   süzgeci). Zayıf-dallı ve dalsız çıkan HER artefakt **elle okundu**; mekanik hüküm tek başına
   kova belirlemedi.

### 1.1 YÖNTEMİN ÜÇ ARIZASI — ÖLÇÜLDÜ VE ONARILDI (beyan)

Bu bölüm bilerek yazılıdır: tarayıcının kendi körlüğünü gizlemesi bu yasanın ihlali olurdu.

| # | Arıza | Nasıl yakalandı | Onarım | Yanlış hüküm riski |
|---|---|---|---|---|
| Y-1 | Tek adımlık iz, çok-atamalı zinciri göremiyor | Kalibrasyon (b) düştü: `health.faz6_kilitleri` değeri `_golge → _h → k_faz5 → kilitler → sum(... if k["gecer"])` zincirinden geçiyor | Taint yayılımı (yukarıda 1) | `intraday_shadow_orders.jsonl` **yanlışlıkla** `yalniz-gorunurluk` çıkmıştı |
| Y-2 | Yalnız `store.` / `_store.` taban adı taranıyordu | `bars_integrity.json` "okuyucusu YOK" çıktı; elle bakıldığında `adapters/data.py:559` `_st.read_json(INTEGRITY_FILE)` bulundu | Taban ad kümesi `{store, _store, _st, st}`'ye genişletildi | `bars_integrity.json` **yanlışlıkla** `tuketicisiz` (ölü yazım) çıkmıştı |
| Y-3 | `_store().read_json(...)` deseni (taban bir **çağrı**, isim değil) hiç görülmüyor | `insider_trades.json` / `short_interest*.json` "okuyucusu YOK" çıktı | Elle grep ile 9 çağrı yeri bulundu ve envantere katıldı | Üç artefakt **yanlışlıkla** `tuketicisiz` çıkardı; ayrıca `massive_grouped_last.json` + `massive_verify.json` envanterde HİÇ görünmüyordu |

**Y-3'ün ikinci sonucu ÖNEMLİ:** `codelaw.artifact_graph` de aynı desene kördür (o da yalnız
`ast.Attribute` tabanına bakar). Yani bugünkü YASA-6 bekçisi `insider.py` / `shortinterest.py` /
`massive.py`'nin `_store()` üzerinden yaptığı **9 okuma/yazımın hiçbirini görmüyor**. Bu artefaktlar
bugün `DECLARED_SINKS`'te elle beyan edildiği için gürültü çıkmıyor — ama beyan kalkarsa bekçi
gerçek olmayan bir ihlal bağırır, ya da tersi: `_store()` ile yazılan YENİ bir ölü artefakt bekçiden
sessizce geçer. (Bulgu B-2.)

**Bilinen kalıntı kusur (onarılmadı, beyan ediliyor):** fonksiyonlar-arası yayılım fonksiyonları
**çıplak ada** göre eşliyor; `ozet()`, `build()`, `status()`, `today()`, `current()` gibi adlar
birden çok modülde var ve ÇAKIŞIYOR. Bu yüzden "yalnız dolaylı kanıtı olan" artefaktların HEPSİ elle
doğrulandı (4 tane: `sieve.json`, `bars_source.json`, `hermes_status.json`, `nous_eval_runs.json`) —
dolaylı kanıt tek başına kova belirlemedi.

---

## 2. KALİBRASYON KAPISI — SONUÇ: **3/3, AMA İKİ ONARIMDAN SONRA**

Brief üç bilinen vakayı yöntemin kendiliğinden yeniden bulmasını şart koşuyordu.

| Vaka | Beklenen | İlk koşu (v1/v2) | Onarım | Son hüküm |
|---|---|---|---|---|
| **(a)** `dormant_setup` / uyuyan planlar | `yalniz-gorunurluk` ya da davranışsal-tüketici-eksik | ❌ **DÜŞTÜ** — artefakt düzeyinde `trade_plans.jsonl` `davranissal` çıkıyor (haklı olarak: aynı defter onlarca kapıyı besliyor) | **KATMAN-4 (alan düzeyi)** eklendi | ✅ `yalniz-gorunurluk` (disk düzeyinde) — §2.1 |
| **(b)** `intraday_shadow_orders.jsonl` | `davranissal` (v212 health kilidi) | ❌ **DÜŞTÜ** — `yalniz-gorunurluk` çıktı | Taint yayılımı (Y-1) | ✅ `davranissal` — `health.py:162` → `faz5_cikis.cikis_olcumu()` → `k_faz5["gecer"]` → `health.py:199 sum(1 for k in kilitler.values() if k["gecer"])` |
| **(c)** hermes `agent_calls` | "veri akıyor / çizim yok" sınıfı | ✅ geçti | — | ✅ `yalniz-gorunurluk (MEŞRU-pano, ÇİZİM YOK)` — kaynağın kendi cümlesiyle doğrulandı, `hermes.py:2502`: «veri hazır, çizim henüz yok» |

Yani: **yöntem ilk hâliyle 1/3'tü.** İki onarımdan (taint yayılımı + alan-düzeyi katmanı) ve bir
kapsam genişletmesinden (store takma adları) sonra 3/3. Bu, brief'in "yöntemde kusur varsa beyan et
ve düzeltip YENİDEN koş" şartının yerine getirilmesidir; hükümler **onarılmış** yöntemin çıktısıdır.

### 2.1 KATMAN-4 — ALAN DÜZEYİ MERCEĞİ (kalibrasyon (a)'nın zorunlu kıldığı katman)

Vaka (a) yöntemin gerçek bir sınırını gösterdi: **ölü mekanizma bir dosyanın tamamı değil, canlı bir
defterin İÇİNDEKİ bir ALAN olabilir.** `trade_plans.jsonl` artefakt olarak fazlasıyla davranışsaldır;
ölü olan `dormant_setup` alanıdır. Artefakt granülaritesi bunu yapısal olarak göremez.

Eklenen mercek: *bir KONTROL alanı diske yazılıyorsa, o alanı DİSKTEN okuyan taraflardan biri
dallanıyor mu — yoksa hepsi yalnız etiketliyor/çiziyor mu?* `dormant_setup` alanına uygulandı:

| Katman | Ölçüm |
|---|---|
| YAZAN (disk) | `loop.py:1380` · `cf_backfill.py:109` · `mutation.py:176` · `shadow_variants.py:247` · şema `storage.py:103` |
| DALLANAN — ama **AYNI TURUN BELLEK İÇİ** değeri, diskten DEĞİL | `loop.py:1491 if plan["dormant_setup"]:` → `explore_pool` → `meta["armed"]`; `loop.py:1372` (kimlik); `cf_backfill.py:135` |
| DİSKTEN OKUYAN | `counterfactual.py:118` (`"dormant"` diye YENİDEN ETİKETLER) · `hermes.py:697` (kanıt paketi metni) · `api.py:2676` (olay etiketi listesi) · `web/app.js:8182` (`"Uyuyan kurulum: evet"` satırı) |
| DİSKTEN OKUYUP **DAVRANAN** | **YOK** |

**Hüküm:** disk düzeyinde `yalniz-gorunurluk`; tek dallanma aynı turun bellek içi değeridir ve o
dalın KUYRUĞU boştur. **Canlı ölçüm (2026-08-08, SSH, salt-okunur):** `trade_plans` **409** satır,
bunun **32'si** `dormant_setup=1`, **1'i** `gate_verdict='GO'`, karşılık gelen **0 işlem**
(`trades`=96). ROADMAP §WP-O'daki kayıt 31/0/1'di — sayı 32'ye çıktı, oran değişmedi.

**Kova: `operator-kalemi`.** ROADMAP:205 `🔒 OPERATÖR — uyuyan kurulum yolu` kalemiyle ÇAPRAZLANDI:
"kapı geçirdi, arkasında tüketen yok… İcraya bağlamak SİSTEMİN NE ALIP SATTIĞINI değiştirir →
ön-kayıt kartı + kill-list gerekir." Bu tur o kararı ALMAZ; yalnız ölçümü tazeler.

---

## 3. TAM ENVANTER TABLOSU

**Okuma notu.** Satır sayısı 107'dir; bu, `store` kapısından geçen **BENZERSİZ ARTEFAKT ADI**
sayısıdır (617 çağrı yeri). Beş satır değişkenden gelen adlardır ve elle çözüldü (çözümleri
hücrede). Bu tabloya girmeyen ama envantere ait olan kalemler §4'te (bayrak dosyaları,
`goal.yaml`/`bounds.yaml` bölümleri, `store` kapısı DIŞINDAKİ `state/` kalemleri).

Kanıt satırları `dosya:satır:fonksiyon` biçimindedir. `DAVRANIŞSAL TÜKETİCİ` sütunundaki `[if]`,
`[comp-if]`, `[ternary]`, `[davranis-cagri:…]` etiketleri dalın TÜRÜNÜ söyler.

| # | Artefakt | ÜRETİCİ (yazan) | OKUYUCU | DAVRANIŞSAL TÜKETİCİ (kanıt satırı) | KOVA | İşaret |
|---:|---|---|---|---|---|---|
| 1 | `<VAR:defter> *(çözüldü)*` | `agent_telemetry.py:215:_budan:write_jsonl` | `agent_telemetry.py:212:_budan:read_jsonl`<br>`faz5_cikis.py:318:cikis_olcumu:read_jsonl` | çözüm: agent_calls.jsonl / agent_traces.jsonl (agent_telemetry._budan) · intraday_shadow_orders.jsonl (faz5_cikis) | **davranissal** | değişken-ad (çözüldü) |
| 2 | `<VAR:f> *(çözüldü)*` | — | `watchdog.py:328:_cal:read_json`<br>`watchdog.py:1920:monotonicity_report:read_jsonl` | çözüm: counterfactuals/trades/hypotheses/events/candidates.jsonl (watchdog.monotonicity_report) · score_calibration/exit_efficiency/cf_fidelity/near_miss/llm_calibration/gate_calibration.json (watchdog._cal) | **davranissal** | değişken-ad (çözüldü) |
| 3 | `<VAR:fname> *(çözüldü)*` | — | `watchdog.py:1971:ownership_report:read_json` | çözüm: heartbeat.json (watchdog.OWNED_FIELDS) | **davranissal** | değişken-ad (çözüldü) |
| 4 | `<VAR:ledger> *(çözüldü)*` | — | `ledgers.py:351:validate_live:read_jsonl` | çözüm: ledgers.CONTRACTS 16 defteri (ledgers.validate_live) | **davranissal** | değişken-ad (çözüldü) |
| 5 | `<VAR:name> *(çözüldü)*` | — | `ledgerstamp.py:132:_mtime:mtime`<br>`shadow_model.py:385:dataset_fingerprint:stamp`<br>`watchdog.py:1555:intraday_stamp_report:read_jsonl`<br>*(+2)* | çözüm: watchdog._n_jsonl · watchdog._m (DERIVED_SOURCES 15 ad) · intraday_stamp_report (2 defter) · ledgerstamp._mtime · shadow_model.dataset_fingerprint | **davranissal** | değişken-ad (çözüldü) |
| 6 | `<X:f'{ARCHIVE_DIR}/{day}.jsonl'>` | `bararchive.py:111:archive_frame:append_jsonl` | — | — (`state/intraday_bars/<gün>.jsonl` — bararchive.archive_frame YAZAR, hotstate çağırır; DEPODA HİÇBİR OKUYUCU YOK (yalnız _retention SİLER)) | **tuketicisiz** | **ÖLÜ YAZIM** |
| 7 | `agent_budget.json` | `hermes.py:1204:_agent_budget_take:write_json`<br>`hermes.py:1191:_agent_budget_take:write_json`<br>`hermes.py:1239:_agent_budget_refund:update_json`<br>*(+1)* | `api.py:3459:api_diagnostics:read_json`<br>`hermes.py:1180:_agent_budget_take:read_json`<br>`hermes.py:1239:_agent_budget_refund:update_json`<br>*(+2)* | hermes.py:1180:_agent_budget_take[if] *(+1 dal)* | **davranissal** | - |
| 8 | `agent_calls.jsonl` | `agent_telemetry.py:253:kaydet:append_jsonl` | `agent_telemetry.py:355:ozet:read_jsonl`<br>`hermes.py:2504:integrations_status:read_jsonl` | — (hermes.integrations_status → /api/hermes gövdesi; hermes.py:2502 kendi söylüyor: «veri hazır, çizim henüz yok») | **yalniz-gorunurluk** | MEŞRU-pano (ÇİZİM YOK) |
| 9 | `agent_tooluse.json` | `hermes.py:1878:_agent_call:write_json` | `hermes.py:2509:integrations_status:read_json`<br>`hermes.py:1867:_agent_call:read_json` | hermes.py:2509:integrations_status[if] | **davranissal** | - |
| 10 | `agent_traces.jsonl` | `agent_telemetry.py:286:_iz_yaz:append_jsonl` | `agent_telemetry.py:311:iz_oku:read_jsonl`<br>`agent_telemetry.py:324:iz_durum:stamp` | — (ham iz; `iz_oku` comp-if bir ARAMA süzgeci, karar değil. codelaw DECLARED_SINKS'te beyanlı) | **yalniz-gorunurluk** | MEŞRU-teşhis |
| 11 | `alerts_ack.json` | `api.py:1897:api_alerts_ack:write_json` | `notify.py:77:inbox:read_json`<br>`watchdog.py:1135:parity_report:read_json` | notify.py:77:inbox[if] *(+1 dal)* | **davranissal** | - |
| 12 | `approvals.jsonl` | `api.py:4589:api_approve:append_jsonl` | `api.py:4410:api_approvals:read_jsonl` | — (ONAY defteri: api_approve YAZAR, tek okuyucu api_approvals `pending` alanı → pano. Hiçbir KAPI onayı okumuyor) | **yalniz-gorunurluk** | **ŞÜPHELİ — kontrol artefaktı** |
| 13 | `arming_report.json` | `arming.py:296:evaluate:write_json`<br>`arming.py:191:_rapora_isle:update_json` | `api.py:4388:api_approvals:read_json`<br>`api.py:4503:_inbox_count:read_json`<br>`api.py:3246:api_diagnostics:read_json`<br>*(+5)* | arming.py:277:evaluate[if] *(+4 dal)* | **davranissal** | - |
| 14 | `axis2_status.json` | `skills.py:643:axis2_cycle:write_json` | `analytics.py:2776:learning_automation:read_json`<br>`api.py:2321:_eksen2_motor_ici:read_json` | — (analytics.learning_automation karne satırı + api._eksen2_motor_ici; kadans kararı skills.axis2_cycle'ın kendi içinde) | **yalniz-gorunurluk** | MEŞRU-pano |
| 15 | `bar_same_evening.json` | `data.py:1181:flush_same_evening:write_json` | `scheduler.py:1302:status:read_json`<br>`data.py:1164:_se:read_json` | data.py:1164:_se[if] | **davranissal** | - |
| 16 | `bar_source_seams.json` | `data.py:2432:flush_seams:write_json` | `data.py:2424:_seams:read_json` | data.py:2424:_seams[if] | **davranissal** | - |
| 17 | `bars_fingerprint.json` | `watchdog.py:576:determinism_report:write_json` | `watchdog.py:574:determinism_report:read_json` | watchdog.py:574:determinism_report[if] | **davranissal** | - |
| 18 | `bars_integrity.json` | `barrepair.py:271:integrity_apply:write_json` | `data.py:559:bars_integrity:read_json` | data.py:559 `_st.read_json` → bars_integrity() → safe_start() → measurement_bars() ÖLÇÜM DÖNEMİ DIŞLAR (component_ic + cf_backfill) | **davranissal** | - |
| 19 | `bars_source.json` | `data.py:167:_pin_source:write_json` | `data.py:164:_pin_source:read_json`<br>`data.py:151:_bar_source:read_json` | data._bar_source() → data.py:2280 load_bars dalı (kaynak tutarlılığı) | **davranissal** | - |
| 20 | `brain_cooldown.json` | `hermes.py:401:brain_stand_down:update_json`<br>`hermes.py:409:brain_recovered:update_json`<br>`hermes.py:431:brain_pause:update_json` | `hermes.py:401:brain_stand_down:update_json`<br>`hermes.py:409:brain_recovered:update_json`<br>`hermes.py:431:brain_pause:update_json`<br>*(+3)* | hermes.py:2597:_pool_window_renewed[if] *(+1 dal)* | **davranissal** | - |
| 21 | `broker_reconcile.json` | `loop.py:2147:reconcile_broker_state:write_json`<br>`loop.py:1923:_skip:write_json`<br>`loop.py:1948:reconcile_broker_state:write_json`<br>*(+1)* | `api.py:3054:api_diagnostics:read_json`<br>`api.py:1920:api_broker_reject_ack:read_json`<br>`api.py:3724:api_alpaca:read_json`<br>*(+4)* | loop.py:1320:daily_cycle[if] *(+2 dal)* | **davranissal** | - |
| 22 | `broker_reject_ack.json` | `api.py:1942:api_broker_reject_ack:update_json` | `api.py:1942:api_broker_reject_ack:update_json`<br>`health.py:245:split_rejections:read_json` | health.py:245:split_rejections[if] | **davranissal** | - |
| 23 | `candidate_review.json` | `hermes.py:2904:review_candidates:write_json` | `api.py:1309:api_signals:read_json`<br>`hermes.py:3175:review_backlog:read_json` | hermes.py:3175:review_backlog[if] | **davranissal** | - |
| 24 | `candidates.jsonl` | `loop.py:1311:daily_cycle:merge_dated_jsonl`<br>`run.py:277:replay_seed:write_jsonl` | `api.py:1292:api_signals:read_jsonl` | watchdog.py:1920 monotonluk dedektörü defter uzunluğunu okur → gerileme alarmı (api okuması ayrıca görünürlük) | **davranissal** | - |
| 25 | `cf_fidelity.json` | `analytics.py:1461:cf_fidelity:write_json` | `api.py:3508:api_diagnostics:read_json`<br>`mcp_server.py:29:_calibrations:read_json`<br>`selfreview.py:136:build:read_json`<br>*(+1)* | watchdog.py:922:parity_report[if] | **davranissal** | - |
| 26 | `cf_open.json` | `counterfactual.py:150:collect:write_json`<br>`counterfactual.py:241:advance:write_json`<br>`hermes.py:2967:_stamp_llm_opinions:update_json` | `api.py:3546:api_diagnostics:read_json`<br>`cf_backfill.py:213:run:read_json`<br>`counterfactual.py:67:collect:read_json`<br>*(+4)* | counterfactual.py:67:collect[if] *(+1 dal)* | **davranissal** | - |
| 27 | `component_ic.json` | `component_ic.py:650:component_ic:write_json`<br>`component_ic.py:799:yeniden_uret:write_json` | `analytics.py:3213:shrunk_component_ic:read_json`<br>`api.py:3445:api_diagnostics:read_json`<br>`component_ic.py:770:yeniden_uret:read_json`<br>*(+1)* | analytics.py:3213:shrunk_component_ic[if] *(+2 dal)* | **davranissal** | - |
| 28 | `composite_budget.json` | `hermes_composite.py:186:_budget_take:update_json` | `hermes_composite.py:186:_budget_take:update_json`<br>`hermes_composite.py:159:_budget_used:read_json` | hermes_composite._budget_take → `return not (out or {}).get('_denied')` = HAFTALIK YOKLAMA BÜTÇE KAPISI | **davranissal** | - |
| 29 | `composite_queue.jsonl` | `hermes_composite.py:110:enqueue:append_jsonl`<br>`hermes_composite.py:199:mark:update_jsonl` | `analytics.py:2833:composite_queue_status:read_jsonl`<br>`hermes_composite.py:199:mark:update_jsonl`<br>`hermes_composite.py:307:spawn_pending:read_jsonl`<br>*(+5)* | hermes_composite.py:307:spawn_pending[if] *(+3 dal)* | **davranissal** | - |
| 30 | `counterfactuals.jsonl` | `counterfactual.py:243:advance:append_jsonl` | `api.py:3547:api_diagnostics:read_jsonl`<br>`cf_backfill.py:212:run:read_jsonl`<br>`counterfactual.py:251:resolved_rows:read_jsonl`<br>*(+4)* | recompute.py:328:report[if] *(+1 dal)* | **davranissal** | - |
| 31 | `data_quality.json` | `loop.py:1016:daily_cycle:write_json` | `api.py:1620:api_digest:read_json`<br>`api.py:3069:api_diagnostics:read_json`<br>`api.py:1067:metrics:read_json`<br>*(+1)* | intraday_shadow._gates (ternary) → gölge karar kapısı; ayrıca /api/* | **davranissal** | - |
| 32 | `entry_execution.jsonl` | `loop.py:43:_entry_exec_write:append_jsonl`<br>`loop.py:81:_entry_exec_trim:write_jsonl`<br>`loop.py:1892:_patch_entry_slippage:write_jsonl` | `analytics.py:3744:_entry_rows:read_jsonl`<br>`analytics.py:3769:entry_execution_summary:read_jsonl`<br>`faz5_cikis.py:258:gerceklik_capasi:read_jsonl`<br>*(+2)* | loop.py:79:_entry_exec_trim[if] *(+3 dal)* | **davranissal** | - |
| 33 | `equity_curve.json` | `run.py:200:replay_seed:write_json`<br>`sermaye.py:382:uygula:write_json` | `analytics.py:1648:_realized_drawdown:read_json`<br>`api.py:1574:api_performance:read_json`<br>`api.py:1616:api_digest:read_json`<br>*(+6)* | analytics.py:1648:_realized_drawdown[if] *(+6 dal)* | **davranissal** | - |
| 34 | `events.jsonl` | `obs.py:60:_emit:append_jsonl` | `notify.py:78:inbox:read_jsonl`<br>`obs.py:200:recent:read_jsonl`<br>`selfreview.py:164:build:read_jsonl`<br>*(+2)* | notify.inbox (alarm teslimi) + watchdog.integrity_report + _olay_satirlari | **davranissal** | - |
| 35 | `exit_efficiency.json` | `analytics.py:1232:exit_efficiency:write_json` | `api.py:3300:api_diagnostics:read_json`<br>`hermes.py:681:evidence_pack:read_json`<br>`mcp_server.py:28:_calibrations:read_json`<br>*(+4)* | hermes.py:681:evidence_pack[if] *(+3 dal)* | **davranissal** | - |
| 36 | `finviz_universe.json` | `finviz.py:260:discover_universe:write_json` | `marketview.py:232:build:read_json`<br>`finviz.py:300:status:read_json`<br>`finviz.py:252:discover_universe:read_json` | finviz.py:252:discover_universe[if] *(+1 dal)* | **davranissal** | - |
| 37 | `fmp_usage.json` | `fmp.py:125:_usage:write_json` | `fmp.py:133:usage:read_json`<br>`fmp.py:96:_usage:read_json` | fmp.py:96:_usage[if] | **davranissal** | - |
| 38 | `gate_calibration.json` | `probgate.py:176:refresh_meta_calibration:write_json` | `api.py:3306:api_diagnostics:read_json`<br>`hermes.py:686:evidence_pack:read_json`<br>`mcp_server.py:27:_calibrations:read_json`<br>*(+5)* | hermes.py:686:evidence_pack[if] *(+2 dal)* | **davranissal** | - |
| 39 | `heartbeat.json` | `health.py:272:write_heartbeat:write_json` | `analytics.py:203:today:read_json`<br>`analytics.py:2373:portfolio_heat:read_json`<br>`api.py:698:api_public_summary:read_json`<br>*(+13)* | health.py:277:heartbeat_age_seconds[if] *(+8 dal)* | **davranissal** | - |
| 40 | `hermes_status.json` | `hermes.py:3583:loop:write_json`<br>`hermes_runtime.py:286:_persist:write_json` | `api.py:3062:api_diagnostics:read_json`<br>`hermes.py:3581:loop:read_json`<br>`hermes_runtime.py:311:_restored_baseline:read_json` | hermes_runtime._restored_baseline() → hermes.py:3560 + hermes_runtime.py:377 dalı | **davranissal** | - |
| 41 | `history/earnings_snapshots.jsonl` | `earnings.py:550:_snapshot:append_jsonl` | `api.py:3289:api_diagnostics:read_jsonl`<br>`earnings.py:540:_snapshot:read_jsonl`<br>`earnings.py:574:snapshot_stats:read_jsonl` | earnings.py:540:_snapshot[if] *(+1 dal)* | **davranissal** | - |
| 42 | `hypotheses.jsonl` | `memory.py:68:record:append_jsonl`<br>`memory.py:156:writeback_outcome:write_jsonl`<br>`memory.py:116:update_status:write_jsonl` | `analytics.py:1008:prediction_hit_rate:read_jsonl`<br>`analytics.py:1034:deflate_stats:read_jsonl`<br>`analytics.py:1057:deflate_why:read_jsonl`<br>*(+13)* | recompute.py:312:report[if] *(+4 dal)* | **davranissal** | - |
| 43 | `hypothesis_id_hwm.json` | `memory.py:74:record:write_json` | `memory.py:60:next_id:read_json`<br>`memory.py:73:record:read_json` | memory.py:73:record[if] | **davranissal** | - |
| 44 | `improvement_proposals.jsonl` | `nous_eval.py:771:_oneri_kaydet:append_jsonl` | `analytics.py:3693:improvement_proposals_status:read_jsonl`<br>`nous_eval.py:537:onceki_akibet:read_jsonl`<br>`nous_eval.py:845:_cli:read_jsonl`<br>*(+1)* | analytics.py:3693:improvement_proposals_status[if] *(+2 dal)* | **davranissal** | - |
| 45 | `inc_cache.json` | `reflect.py:98:_inc_disk_save:write_json` | `reflect.py:82:_inc_disk_load:read_json` | reflect.py:82:_inc_disk_load[if] | **davranissal** | - |
| 46 | `index_crosscheck.json` | `scheduler.py:1150:advance_once:write_json` | `api.py:3522:api_diagnostics:read_json`<br>`loop.py:1010:daily_cycle:read_json` | loop.py:1010:daily_cycle[if] | **davranissal** | - |
| 47 | `insider_trades.json` | `insider.py:497:_defteri_birlestir:write_json` | — | — (insider.py:281 `_store().read_json(LEDGER_FILE)` → ozet()/durum(); codelaw DECLARED_SINKS'te gerekçeli erteleme) | **yalniz-gorunurluk** | MEŞRU-BEYANLI (Y4 ertelemesi) |
| 48 | `integrity_alarmed.json` | `watchdog.py:1766:check_integrity_and_alarm:write_json` | `watchdog.py:1642:check_integrity_and_alarm:read_json` | watchdog.py:1642:check_integrity_and_alarm[if] | **davranissal** | - |
| 49 | `integrity_audit_log.json` | `integrity_registry.py:408:record_audit:write_json` | `integrity_registry.py:393:next_audit_target:read_json`<br>`integrity_registry.py:406:record_audit:read_json` | integrity_registry.py:393:next_audit_target[if] | **davranissal** | - |
| 50 | `intraday_decisions.jsonl` | `intraday_cycle.py:197:_handle_symbol:append_jsonl` | `api.py:3167:api_diagnostics:read_jsonl`<br>`health.py:161:faz6_kilitleri:read_jsonl` | health.faz6_kilitleri (n_4a) + watchdog.intraday_stamp_report üç-damga ihlali → bütünlük raporu | **davranissal** | - |
| 51 | `intraday_shadow_orders.jsonl` | `intraday_shadow.py:342:record:append_jsonl` | `api.py:3180:api_diagnostics:read_jsonl`<br>`health.py:162:faz6_kilitleri:read_jsonl`<br>`intraday_shadow.py:366:vs_eod:read_jsonl`<br>*(+1)* | health.py:162 → faz5_cikis.cikis_olcumu() → `k_faz5.gecer` → FAZ-6 KİLİT ZİNCİRİ (fail-closed kapı) | **davranissal** | - |
| 52 | `learning_cadence.json` | `scheduler.py:535:_learning_cadence:write_json` | `analytics.py:2775:learning_automation:read_json` | — (tek okuyucu analytics.learning_automation → karne satırı (tazelik gösterimi)) | **yalniz-gorunurluk** | MEŞRU-pano |
| 53 | `learning_loop_open.json` | `rollback.py:293:_open_loop:update_json`<br>`rollback.py:329:_close_loop:write_json` | `api.py:2888:_rollback_sicili:read_json`<br>`rollback.py:293:_open_loop:update_json`<br>`rollback.py:328:_close_loop:read_json`<br>*(+2)* | rollback.py:328:_close_loop[if] *(+2 dal)* | **davranissal** | - |
| 54 | `llm_calibration.json` | `analytics.py:1162:llm_opinion_calibration:write_json` | `analytics.py:1138:llm_opinion_calibration:read_json`<br>`analytics.py:1181:llm_promoted:read_json`<br>`api.py:3299:api_diagnostics:read_json`<br>*(+5)* | analytics.py:1138:llm_opinion_calibration[if] *(+3 dal)* | **davranissal** | - |
| 55 | `mae_profile.json` | `analytics.py:3075:mae_profile:write_json` | `analytics.py:3581:system_telemetry:read_json`<br>`api.py:3394:api_diagnostics:read_json`<br>`hermes.py:675:evidence_pack:read_json` | hermes.py:675:evidence_pack[if] | **davranissal** | - |
| 56 | `massive_crosscheck.json` | `data.py:1004:flush_xcheck:write_json` | `data.py:996:_xcheck:read_json` | data.py:996:_xcheck[if] | **davranissal** | - |
| 57 | `mechanism_beats.json` | `watchdog.py:79:beat:write_json` | `api.py:2737:_hat_cizelgesi:read_json`<br>`watchdog.py:177:report:read_json`<br>`watchdog.py:76:beat:read_json` | watchdog.py:177:report[if] *(+1 dal)* | **davranissal** | - |
| 58 | `mirror_orders.json` | `mirror_stream.py:120:_persist:write_json`<br>`mirror_stream.py:212:decay_stale_stream_flag:write_json` | `api.py:2621:_emir_yasam:read_json`<br>`api.py:3056:api_diagnostics:read_json`<br>`loop.py:2126:reconcile_broker_state:read_json`<br>*(+4)* | mirror_stream.py:209:decay_stale_stream_flag[if] *(+4 dal)* | **davranissal** | - |
| 59 | `monotonic_amnesty.json` | `watchdog.py:1850:grant_amnesty:write_json` | `watchdog.py:1847:grant_amnesty:read_json`<br>`watchdog.py:1858:_amnesty_index:read_json` | watchdog._amnesty_index → monotonluk ALARMINI susturur (af) | **davranissal** | - |
| 60 | `monotonic_state.json` | `watchdog.py:1929:monotonicity_report:write_json` | `sermaye.py:429:_peak_affi:read_json`<br>`watchdog.py:1927:monotonicity_report:read_json` | sermaye.py:429:_peak_affi[if] *(+1 dal)* | **davranissal** | - |
| 61 | `near_miss.json` | `analytics.py:1515:near_miss_report:write_json` | `api.py:2582:_near_miss_karne:read_json`<br>`hermes.py:712:evidence_pack:read_json`<br>`mcp_server.py:36:_near_miss:read_json`<br>*(+2)* | hermes.py:712:evidence_pack[if] *(+3 dal)* | **davranissal** | - |
| 62 | `notify_sent.json` | `obs.py:156:_maybe_notify:write_json` | `obs.py:134:_maybe_notify:read_json` | obs._maybe_notify token başına 6 sa susturma penceresi (if dalı). CANLIDA DOSYA YOK — kanal boş (operatör kalemi §6.1) | **davranissal** | - |
| 63 | `notify_undelivered.json` | `obs.py:184:_maybe_notify:update_json`<br>`obs.py:130:_maybe_notify:update_json` | `api.py:1896:api_alerts_ack:read_json`<br>`obs.py:184:_maybe_notify:update_json`<br>`obs.py:130:_maybe_notify:update_json`<br>*(+1)* | watchdog.py:1133:parity_report[if] | **davranissal** | - |
| 64 | `nous_eval_runs.json` | `nous_eval.py:786:_kosu_kaydet:update_json` | `analytics.py:3708:improvement_proposals_status:read_json`<br>`nous_eval.py:786:_kosu_kaydet:update_json` | analytics.improvement_proposals_status() → nous_eval.ozet_metni dalı | **davranissal** | - |
| 65 | `nous_fisler.json` | `nous_eval.py:460:_fis_yaz:update_json` | `api.py:2417:_nous_fisler:read_json`<br>`nous_eval.py:460:_fis_yaz:update_json` | — (api._nous_fisler → pano fişleri) | **yalniz-gorunurluk** | MEŞRU-pano |
| 66 | `oos_erosion.json` | `oos_erosion.py:149:record:write_json` | `oos_erosion.py:196:report:read_json`<br>`oos_erosion.py:124:record:read_json`<br>`oos_erosion.py:164:status:read_json` | oos_erosion.py:124:record[if] *(+1 dal)* | **davranissal** | - |
| 67 | `ownership_state.json` | `watchdog.py:1981:ownership_report:write_json` | `watchdog.py:1968:ownership_report:read_json` | watchdog.py:1968:ownership_report[if] | **davranissal** | - |
| 68 | `pipeline_runs.jsonl` | `skills.py:386:pipeline_run:append_jsonl` | `api.py:2750:_hat_cizelgesi:read_jsonl`<br>`api.py:1375:api_skills:read_jsonl`<br>`api.py:4377:api_pipeline_runs:read_jsonl` | — (üç okuyucu da api.py (skills kartı, hat çizelgesi, /api/pipeline-runs)) | **yalniz-gorunurluk** | MEŞRU-pano |
| 69 | `pool_exhausted_seen.json` | `hermes.py:2571:_pool_seen_at:update_json`<br>`hermes.py:2587:_pool_seen_clear:update_json` | `hermes.py:2571:_pool_seen_at:update_json`<br>`hermes.py:2587:_pool_seen_clear:update_json`<br>`hermes.py:2585:_pool_seen_clear:read_json` | hermes.py:2585:_pool_seen_clear[if] | **davranissal** | - |
| 70 | `portfolio.json` | `api.py:3773:api_alpaca_submit_armed:update_json`<br>`hermes.py:2978:_stamp_llm_opinions:update_json`<br>`loop.py:454:operator_onay_ver:update_json`<br>*(+5)* | `analytics.py:205:today:read_json`<br>`analytics.py:2372:portfolio_heat:read_json`<br>`api.py:1615:api_digest:read_json`<br>*(+33)* | faz5_cikis.py:184:_eod_defteri[if] *(+23 dal)* | **davranissal** | - |
| 71 | `probe_cache.json` | `reflect.py:1163:_probe_disk_save:write_json` | `reflect.py:1148:_probe_disk_load:read_json` | reflect.py:1148:_probe_disk_load[if] | **davranissal** | - |
| 72 | `regime.json` | `loop.py:1204:daily_cycle:write_json` | `analytics.py:204:today:read_json`<br>`api.py:1298:api_signals:read_json`<br>`api.py:1614:api_digest:read_json`<br>*(+19)* | hermes.py:3495:reflect_once[if] *(+7 dal)* | **davranissal** | - |
| 73 | `regime_edge.json` | `analytics.py:1549:regime_edge:write_json` | `analytics.py:1894:edge_verdict:read_json`<br>`api.py:3317:api_diagnostics:read_json`<br>`hermes.py:708:evidence_pack:read_json`<br>*(+1)* | analytics.py:1894:edge_verdict[if] *(+2 dal)* | **davranissal** | - |
| 74 | `regime_trigger.json` | `regime_trigger.py:38:evaluate:write_json` | `regime_trigger.py:28:evaluate:read_json` | regime_trigger.py:28:evaluate[if] | **davranissal** | - |
| 75 | `scan_debt.json` | `loop.py:837:_scan_debt_add:write_json`<br>`loop.py:886:_scan_debt_collect:write_json` | `loop.py:831:_scan_debt_add:read_json`<br>`loop.py:855:_scan_debt_collect:read_json` | loop.py:831:_scan_debt_add[if] *(+1 dal)* | **davranissal** | - |
| 76 | `scheduler_status.json` | `scheduler.py:34:_persist:write_json`<br>`scheduler.py:1270:_run:write_json` | `api.py:3058:api_diagnostics:read_json`<br>`scheduler.py:195:_rehydrate:read_json` | scheduler.py:195:_rehydrate[if] | **davranissal** | - |
| 77 | `score_calibration.json` | `loop.py:1669:daily_cycle:write_json` | `analytics.py:1795:edge_verdict:read_json`<br>`api.py:3307:api_diagnostics:read_json`<br>`hermes.py:639:evidence_pack:read_json`<br>*(+5)* | analytics.py:1795:edge_verdict[if] *(+4 dal)* | **davranissal** | - |
| 78 | `score_calibration_history.jsonl` | `analytics.py:986:record_score_calibration_point:append_jsonl` | `analytics.py:981:record_score_calibration_point:read_jsonl`<br>`api.py:3316:api_diagnostics:read_jsonl` | analytics.py:981:record_score_calibration_point[if] | **davranissal** | - |
| 79 | `scoreboard.json` | `run.py:264:replay_seed:write_json`<br>`versioning.py:91:update_scoreboard:update_json`<br>`versioning.py:115:set_row_fields:update_json` | `analytics.py:649:learning_scorecard:read_json`<br>`analytics.py:771:agent_view:read_json`<br>`analytics.py:2085:live_expectancy_ceiling:read_json`<br>*(+8)* | analytics.py:2085:live_expectancy_ceiling[if] *(+4 dal)* | **davranissal** | - |
| 80 | `self_review.json` | `selfreview.py:75:mechanism_ok:update_json`<br>`selfreview.py:99:mechanism_failed:update_json`<br>`selfreview.py:213:build:write_json` | `api.py:3148:api_diagnostics:read_json`<br>`hermes.py:703:evidence_pack:read_json`<br>`mcp_server.py:53:_selfreview:read_json`<br>*(+4)* | hermes.py:703:evidence_pack[if] *(+2 dal)* | **davranissal** | - |
| 81 | `shadow_books.json` | `shadow_lifecycle.py:572:_run_cycle_govde:write_json` | `shadow_lifecycle.py:538:_run_cycle_govde:read_json`<br>`shadow_variants.py:606:_load_books:read_json` | shadow_lifecycle.py:538:_run_cycle_govde[if] | **davranissal** | - |
| 82 | `shadow_model.json` | `shadow_model.py:71:_damga_yaz:write_json`<br>`shadow_model.py:238:save:write_json`<br>`shadow_model.py:331:refit_and_save:write_json` | `hermes.py:699:evidence_pack:read_json`<br>`selfreview.py:137:build:read_json`<br>`shadow_model.py:66:_damga_yaz:read_json`<br>*(+7)* | hermes.py:699:evidence_pack[if] *(+4 dal)* | **davranissal** | - |
| 83 | `shadow_trades.jsonl` | `shadow_lifecycle.py:574:_run_cycle_govde:append_jsonl` | `shadow_variants.py:607:_load_books:read_jsonl` | — (tek dış okuyucu shadow_variants._load_books → `--karne` CLI çıktısı; üretim yolu yok) | **yalniz-gorunurluk** | MEŞRU-CLI |
| 84 | `shadow_variants.jsonl` | `shadow_variants.py:420:record_cycle:append_jsonl` | `analytics.py:2871:shadow_variant_summary:read_jsonl`<br>`shadow_variants.py:641:main:read_jsonl` | analytics.py:2871:shadow_variant_summary[if] | **davranissal** | - |
| 85 | `short_interest.json` | `shortinterest.py:348:ozet:write_json` | — | — (shortinterest.durum()/main() okur; kaçınma filtresi ölçülene dek kapıya BAĞLANMADI) | **yalniz-gorunurluk** | MEŞRU-BEYANLI (Y4 ertelemesi) |
| 86 | `short_interest_float.json` | `shortinterest.py:254:float_cek:write_json` | — | — (shortinterest.py:210 `_store().read_json(FLOAT_FILE)` → SI%float paydası) | **yalniz-gorunurluk** | MEŞRU-BEYANLI (kota önbelleği) |
| 87 | `sieve.json` | `sieve.py:127:flush:update_json` | `sieve.py:127:flush:update_json`<br>`sieve.py:148:stages:read_json` | api.py:3202 sieve.report() → api.py:2232 `_terfi_hukmu` TERFİ hükmü. DİKKAT: codelaw beyanı BAYAT (aşağıda B-4) | **davranissal** | - |
| 88 | `skill_auto_shadow.json` | `skills.py:523:auto_shadow_from_evidence:write_json` | `api.py:3428:api_diagnostics:read_json` | — (skills.py:420 kendi söylüyor: «panonun duyuru kartı bu dosyadan okunur») | **yalniz-gorunurluk** | MEŞRU-pano |
| 89 | `skill_recommendations.jsonl` | `skills.py:301:record_recommendation:append_jsonl`<br>`skills.py:348:apply_skill_action:append_jsonl`<br>`skills.py:504:auto_shadow_from_evidence:append_jsonl` | `skills.py:291:record_recommendation:read_jsonl`<br>`skills.py:314:pending_recommendations:read_jsonl` | skills.py:291-298 açık `pending` satırı varsa `return False` — TEKRAR ÖNERİYİ BASTIRIR | **davranissal** | - |
| 90 | `skill_revisions.json` | `skill_evolve.py:127:_write_revisions:write_json`<br>`skill_evolve.py:116:revisions:write_json` | `skill_evolve.py:109:revisions:read_json` | skill_evolve.py:109:revisions[if] | **davranissal** | - |
| 91 | `skills_registry.json` | `skills.py:163:reconcile_enablement:write_json`<br>`skills.py:347:apply_skill_action:write_json`<br>`skills.py:360:_touch_registry_run:write_json` | `api.py:1356:api_skills:read_json`<br>`api.py:702:api_public_summary:read_json`<br>`skills.py:102:registry:read_json` | skills.registry() → yetkinlik etkinleştirme; api okumaları ayrıca görünürlük | **davranissal** | - |
| 92 | `sp500_constituents.json` | `constituents.py:138:current:write_json`<br>`constituents.py:130:current:write_json` | `constituents.py:57:_cached:read_json` | constituents.py:57:_cached[if] | **davranissal** | - |
| 93 | `spend.jsonl` | `spend.py:70:record:append_jsonl` | `api.py:2802:_spend_detay:read_jsonl`<br>`api.py:1125:api_spend:read_jsonl`<br>`spend.py:76:month_spend:read_jsonl`<br>*(+1)* | spend.month_spend/summary + api._spend_detay dalları | **davranissal** | - |
| 94 | `sprint_runs.jsonl` | `sprint_run.py:160:_run:append_jsonl` | `sprint.py:122:status:read_jsonl` | sprint.py:122:status[if] | **davranissal** | - |
| 95 | `sprint_status.json` | `sprint.py:296:start:write_json`<br>`sprint.py:464:stop:write_json` | `sprint.py:84:status:read_json`<br>`sprint.py:451:stop:read_json` | sprint.py:84:status[if] *(+1 dal)* | **davranissal** | - |
| 96 | `symbol_no_data.json` | `data.py:2110:_record_no_data:write_json`<br>`data.py:2129:_clear_no_data:write_json` | `constituents.py:210:universe_drift:read_json`<br>`data.py:2094:_no_data_reg:read_json` | data.py:2094:_no_data_reg[if] *(+1 dal)* | **davranissal** | - |
| 97 | `threshold_curve.json` | `threshold_curve.py:186:build:write_json` | `analytics.py:2844:threshold_cross_note:read_json`<br>`api.py:3449:api_diagnostics:read_json` | analytics.py:2844:threshold_cross_note[if] | **davranissal** | - |
| 98 | `trade_plans.jsonl` | `hermes.py:2955:_stamp_llm_opinions:update_jsonl`<br>`loop.py:203:_stamp_plan_status:update_jsonl`<br>`loop.py:442:operator_onay_ver:update_jsonl`<br>*(+4)* | `analytics.py:206:today:read_jsonl`<br>`analytics.py:1080:llm_opinion_calibration:read_jsonl`<br>`analytics.py:3423:gate_veto_tally:read_jsonl`<br>*(+27)* | analytics.py:1080:llm_opinion_calibration[if] *(+14 dal)* | **davranissal** | - |
| 99 | `trades.jsonl` | `ledgerstamp.py:274:_migrate_locked:write_jsonl`<br>`loop.py:1821:_persist_trade:append_jsonl`<br>`loop.py:2119:reconcile_broker_state:update_jsonl`<br>*(+1)* | `analytics.py:11:_trades:read_jsonl`<br>`analytics.py:657:learning_scorecard:read_jsonl`<br>`analytics.py:4030:_nd_stamp:stamp`<br>*(+53)* | analytics.py:657:learning_scorecard[if] *(+26 dal)* | **davranissal** | - |
| 100 | `trend_book.json` | `trend_shadow.py:98:_kaydet:write_json` | `api.py:3496:api_diagnostics:read_json`<br>`trend_shadow.py:523:run_cycle:read_json` | trend_shadow.py:523:run_cycle[if] | **davranissal** | - |
| 101 | `universe_drift.json` | `loop.py:641:_universe_drift_check:write_json` | `api.py:3507:api_diagnostics:read_json` | — (DATA_QUALITY alarmı YAZIM ANINDA bellekteki `rep`ten atılır (loop.py:643); DOSYA yalnız çizilir) | **yalniz-gorunurluk** | MEŞRU-pano |
| 102 | `validation_ledger.jsonl` | `validation.py:341:record_candidate:append_jsonl` | `analytics.py:2453:validation_trio:read_jsonl`<br>`shadowlaw.py:547:divergence_table:read_jsonl`<br>`validation.py:351:ledger:read_jsonl` | analytics.validation_trio → DSR/PBO → faz6 kilidi + reflect kapısı | **davranissal** | - |
| 103 | `validation_report.json` | `scheduler.py:663:_weekly_validation:write_json` | `api.py:3198:api_diagnostics:read_json` | — (tek okuyucu api_diagnostics; scheduler haftalık yazar) | **yalniz-gorunurluk** | MEŞRU-pano |
| 104 | `warmup_scale.json` | `hermes.py:1462:warmup_budget_feedback:update_json` | `hermes.py:1462:warmup_budget_feedback:update_json`<br>`hermes.py:1407:warmup_budget:read_json` | hermes.warmup_budget() ısınma bütçe merdiveni (çarpan + ölçülen duvar) | **davranissal** | - |
| 105 | `watchdog_alarm_gunluk.json` | `watchdog.py:280:check_and_alarm:write_json` | `api.py:2391:_alarm_gunluk:read_json`<br>`watchdog.py:224:_gunluk_oku:read_json`<br>`watchdog.py:279:check_and_alarm:read_json` | watchdog.py:224:_gunluk_oku[if] *(+1 dal)* | **davranissal** | - |
| 106 | `watchdog_alarmed.json` | `watchdog.py:281:check_and_alarm:write_json` | `watchdog.py:1465:alarm_budget:read_json`<br>`watchdog.py:241:check_and_alarm:read_json` | watchdog.py:241:check_and_alarm[if] | **davranissal** | - |
| 107 | `wf_cache_rev.json` | `reflect.py:123:clear_wf_caches:write_json`<br>`data.py:119:_bump_wf_rev:write_json` | `reflect.py:122:clear_wf_caches:read_json`<br>`reflect.py:83:_inc_disk_load:read_json`<br>`reflect.py:96:_inc_disk_save:read_json`<br>*(+6)* | reflect.py:83:_inc_disk_load[if] *(+3 dal)* | **davranissal** | - |

---

## 4. TABLONUN DIŞINDAKİ ENVANTER

### 4.1 Bayrak dosyaları (`store` kapısından geçmez — `pathlib` yoklaması)

| Bayrak | ÜRETİCİ | OKUYUCU + DAVRANIŞ | Kova |
|---|---|---|---|
| `state/HALT` | **İNSAN** (pano `/api/halt` → `health.set_halt`) | `health.halted()` → `loop.py:412` tur iptali · `scheduler.py:809` · `api.py:3754` gönderim reddi · `hermes.py:3564` | `operator-kalemi` (sağlıklı: davranışsal tüketici TAM) |
| `state/LEARN_HALT` | **İNSAN** | `health.learn_halted()` → `reflect.py:898` yansıma durdurma · `hermes_runtime.py:411` | `operator-kalemi` (sağlıklı) |
| `state/INTRADAY_ARM` | **İNSAN** (elle `touch` / pano tuşu; `api.py:1785`) | `health.intraday_armed()` → `intraday_cycle.py:153,262` gözlem/arm modu · `health.py:181` FAZ-6 4. kilidi | `operator-kalemi` (sağlıklı) — **CANLIDA MEVCUT** |
| `state/STOP` | `sprint.py:455` (sprint kum havuzu içinde) | `sprint_run.py:119` → oturum başında iptal | `davranissal` |
| `state/.reflect.lock` | `reflect.py:878` | aynı dosya (süreç kilidi) | `davranissal` |

> **NOT (canlı çapraz):** canlı `state/`'te `INTRADAY_ARM` **VAR**, `HALT`/`LEARN_HALT` **YOK**.
> Bayrak dosyasının yokluğu "kapalı" demektir — bu beklenen durumdur, bulgu değildir.
> `INTRADAY_ARM`'ın varlığı FAZ-6'nın 4. kilidini açar; kalan dört kilit hükmü ayrı ölçülür.

### 4.2 `goal.yaml` bölümleri — **DÖRT ADET BEYANSIZ ÖLÜ DÜĞME BULUNDU**

Ölçüm: her anahtar `meridian/` içinde arandı; `guard.GOAL_KEYS`/`LIMIT_KEYS` üyelik kümeleri
**okuyucu SAYILMAZ** (o kümeler yalnız "Hermes bunu değiştiremez" der, değeri hiç OKUMAZ).

| Anahtar | Tek eşleşme | Kova | Durum |
|---|---|---|---|
| `explore_rate` | `guard.py:17` (GOAL_KEYS) | `tuketicisiz` | ✅ **BEYANLI** — `goal.yaml` içinde yazılı: "HİÇBİR KOD OKUMAZ (K1 denetimi 2026-07-30)" |
| `limits.kill_switch_file` | `guard.py:25` (LIMIT_KEYS) | `tuketicisiz` | ✅ **BEYANLI** — yazılı: "yolu değiştirmek kill-switch'i TAŞIMAZ" |
| **`backtest_gate`** | `guard.py:17` (GOAL_KEYS) | `tuketicisiz` | ❌ **BEYANSIZ** — bulgu B-1 |
| **`session_tz`** | `guard.py:15` (GOAL_KEYS) | `tuketicisiz` | ❌ **BEYANSIZ** — bulgu B-1 |
| **`style`** | `guard.py:15` (GOAL_KEYS) | `tuketicisiz` | ❌ **BEYANSIZ** — bulgu B-1 |
| **`schema_version`** | `guard.py:15` (GOAL_KEYS) | `tuketicisiz` | ❌ **BEYANSIZ** — bulgu B-1 |
| `one_variable_only` | `guard.py:16` (GOAL_KEYS) + `nous_eval.py:86` (metin listesi) | `yalniz-gorunurluk` **ŞÜPHELİ** | ❌ Kural `guard.py:134`'te **SABİT KODLU** (`len(changes) != 1`); dosyadaki değer OKUNMUYOR — bulgu B-3 |
| `universe`, `target_return_30d`, `min_sharpe`, `max_drawdown`, `failure_below`, `reflection_every`, `min_sample`, `rollback_if_worse_by`, `max_accepted_changes_per_month`, `commission_per_share`, `slippage_bps`, `fill`, `execution_v2.*`, `pessimistic_band_v2.*`, `limits.*` (10 anahtar) | çok sayıda gerçek okuyucu | `davranissal` | ✅ |

`bounds.yaml`: 33 arama-uzayı anahtarı. Hepsi `reflect`/`hermes` arama yolundan geçer
(`config.bounds()` tek kapı). İki anahtar dosyanın KENDİSİNDE "bugün atıl" diye beyanlıdır
(`stop_buffer_atr` — `stop_mode=0` iken; `exit.early_kill_bars` — `early_kill_pivot=0` iken;
`regime.vix_backwardation_gate` — "BUGÜN veri_yok → atıl"). Üçü de **BEYANLI**, bulgu değil.

### 4.3 CANLI `state/` çaprazlaması (SSH, salt-okunur, 2026-08-08)

`ssh ubuntu@130.61.126.87 'ls -1 /opt/meridian/state/'` — SSH **çalıştı**, sınıflandırıcıya
takılmadı; yerel bayat `state/` KULLANILMADI. Canlıda 113 giriş var.

**Canlıda var + tabloya girmeyen kalemler ve hükümleri (yetim adaylarının tamamı çözüldü):**

| Canlı kalem | Hüküm |
|---|---|
| `bars_source.json`, `insider_signals.json`, `massive_grouped_last.json`, `massive_verify.json` | **YETİM DEĞİL** — `_store()` deseniyle okunuyor/yazılıyor (Y-3 kör noktası). `massive_verify.json` fiilen bir **emniyet anahtarıdır** (`write_enabled()` kapısı) |
| `auth.json`, `secrets.json` | `store` dışından (`_auth_file().read_text()`, `secrets.py:65`); `auth.json` codelaw'da beyanlı, 51 uç ona bağlı → `davranissal` |
| `earnings.csv` | `earnings.py:101/391/474` doğrudan yol; karartma guard'ını besler → `davranissal` |
| `lessons.md` | `memory.py:212` yazar; `hermes.py:153` + `skill_evolve.py:143` + `api.py:1345` okur → `davranissal` |
| `strategy.yaml`, `goal.yaml`, `bounds.yaml` | `config.py` tek kapı → `davranissal` (goal alt-anahtarları için §4.2) |
| `bars/`, `history/`, `sprint/`, `quarantine/`, `bars_intraday/` | dizinler; `config.py:13-14`, `sprint.py:135`, `barsarchive.py:99` |
| **`intraday_bars/`** | `bararchive.ARCHIVE_DIR` — **BULGU B-5 (tek gerçek ölü yazım)** |
| `meridian.db`, `-shm`, `-wal`, `.yedek` | SQLite arka ucu (`storage.py`); altı defter oraya taşındı |
| `*.migrated` (6 dosya: trades, trade_plans, portfolio, scoreboard, equity_curve, shadow_books) | DB'ye göç etmiş defterlerin donmuş dosya kalıntısı — `store.stamp()`/`store.mtime()` bu sınıfı zaten soyutluyor |
| `barsarchive.log`, `dashboard.log` | süreç günlükleri, artefakt değil |

**Canlıda YOK ama repoda yazılan artefaktlar (yazım yolu hiç koşmamış):**
`approvals.jsonl` (L0'da `api_approve` 403 döner) · `notify_sent.json` (bildirim kanalı boş —
§6.1 operatör kalemi) · `pool_exhausted_seen.json` · `skill_revisions.json` ·
`sp500_constituents.json` · `symbol_no_data.json` · `sprint_runs.jsonl` ·
`short_interest_float.json` · `monotonic_amnesty.json` (af hiç verilmemiş — sağlıklı).
Bunların hiçbiri **ölü kod** değildir; yazım yolu henüz TETİKLENMEMİŞTİR. `ÖLÇÜLEMEDİ ≠ 0`
disiplini gereği "kullanılmıyor" denmez.

---

## 5. BULGULAR — ŞİDDET SIRALI

### B-1 · `goal.yaml`'da DÖRT BEYANSIZ ÖLÜ DÜĞME — `backtest_gate`, `session_tz`, `style`, `schema_version`

**Ne.** Dördünün de `meridian/` içindeki TEK eşleşmesi `guard.GOAL_KEYS` üyelik kümesidir
(`guard.py:15-17`). O küme değeri hiç okumaz; yalnız "Hermes bu adı değiştiremez" der. Yani bu dört
satırın değerini değiştirmek **hiçbir davranışı değiştirmez**.

**Neden tehlikeli.** `goal.yaml` bu sistemdeki **değişmez operatör sözleşmesidir** — dosyanın kendi
başlığı "IMMUTABLE. Hermes may NEVER edit this file" der. Orada duran bir satır, operatöre *"bu
kontrol bende"* hissi verir. `backtest_gate: true` özellikle ağırdır: adı "her değişiklik önce
backtest'ten geçsin" sözü verir; operatör bunu `false` yapsa da, `true` bıraksa da **hiçbir şey
değişmez**. Bu, yanlış kontrol hissinin tanımıdır.

**Hangi sınıf.** `explore_rate` ve `kill_switch_file` ile **BİREBİR aynı sınıf** — ikisi K1
denetiminde (2026-07-30) bulunmuş ve `goal.yaml` içine gerekçeleriyle YAZILMIŞTI. Yani sınıfın adı
zaten konmuş, envanteri TAMAMLANMAMIŞ: aynı taramada bu dördü kaçmış. Akrabalık: bugünkü
"koruma yeniden-kurma yolu HİÇ YOKTU" vakasıyla aynı aile — mekanizma "koşmadı" değil, hiç yok.

**Önerilen kapama (UYGULAMA — öneri, bu turda uygulanmadı).** İki seçenek, biri seçilmeli:
(a) `explore_rate`/`kill_switch_file` emsalindeki gibi dördünün de üstüne "BİLGİLENDİRİCİ — HİÇBİR
KOD OKUMAZ" gerekçesi yazılsın; (b) `backtest_gate` için gerçek bir okuyucu bağlansın (`reflect`
terfi yolu zaten backtest koşuyor — kapının anahtarı o satır olabilir). **Yapısal kapama:**
`goal.yaml` anahtarlarının okuyucusunu ölçen bir bekçi (`GOAL_KEYS` üyeliğini okuyucu SAYMAYAN) —
`codelaw`'un artefakt grafiğinin config karşılığı. Bugün böyle bir bekçi yok, bu yüzden aynı sınıf
üçüncü kez doğabilir.

---

### B-2 · YASA-6 BEKÇİSİNİN KÖR NOKTASI: `_store()` deseni — 9 çağrı yeri görünmüyor

**Ne.** `codelaw.artifact_graph` (`codelaw.py:486`) yalnız `ast.Attribute` tabanlı çağrıları görür.
`adapters/insider.py`, `adapters/shortinterest.py` ve `adapters/massive.py` erişimlerini
`_store().read_json(...)` ile yapar — taban bir **çağrıdır**, isim değil. Ölçülen 9 çağrı yeri:
`insider.py:281,637` · `shortinterest.py:210,353,392` · `massive.py:555,564,632,856`.

**Neden tehlikeli.** Bu, "yasa var ama yasanın gözü kapalı" sınıfıdır. Bugün zararsız görünüyor
çünkü ilgili dört artefakt `DECLARED_SINKS`'te elle beyanlı. Ama beyan bir MUAFİYETTİR, kör nokta
bir YAPIDIR: bu desenle yazılan YENİ bir artefakt bekçiden **sessizce** geçer ve tam olarak
2026-07-21'de olan şey (üretilip hiç okunmayan bütünlük raporu) tekrar eder. Üstelik bugün
`massive_verify.json` bir **emniyet anahtarıdır** — bekçi onun yazar/okuyucu grafiğini hiç görmüyor.

**Hangi sınıf.** Bugünkü iki vakanın ORTAK kökü: dedektörün kendi kapsamı ölçülmemiş.
`ROADMAP` dilinde "sıfır ihlal iddiasının şartı taramanın kapsamının bilinmesidir" — `codelaw`
`UNSCANNED` listesini bu yüzden tutuyor, ama bu kör nokta `UNSCANNED`'e DÜŞMÜYOR (dosya taranıyor,
çağrı görülmüyor) ve `unresolved`'a da düşmüyor (çağrı hiç `role` almıyor, `continue` ediliyor).
Yani körlük **hiçbir yerde sayılmıyor**.

**Önerilen kapama (öneri).** `codelaw.py:486`'daki filtre `n.func.value` bir `ast.Call` olduğunda da
adı çözecek biçimde genişletilsin (`_store()` → `store`); çözülemezse **`unresolved`'a yazılsın**
(bugün sessizce atlanıyor — asıl kusur bu). Çivi: `insider/shortinterest/massive` çağrı yerlerinin
`artifact_graph`'ta görünmesini bekleyen bir test.

---

### B-3 · `one_variable_only`: dosyada düğme, kodda sabit — YANLIŞ KONTROL

**Ne.** `goal.yaml`'da `one_variable_only: true` yazar. `guard.py:134` kuralı **koşulsuz** uygular:
`if len(proposal["changes"]) != 1: return Verdict(False, ...)`. Anahtarın değeri hiç okunmaz.

**Neden tehlikeli.** B-1'in daha sinsi hâli: burada düğme ÖLÜ değil, **YAPIŞIK**. Bugün doğru
konumda yapışık (kural açık) — yani zararsız görünüyor. Ama sözleşme dosyası bir DÜĞME vaat
ediyor: operatör `false` yazarsa kuralın kalkacağını sanır, kalkmaz. Tersi daha kötü olurdu.

**Hangi sınıf.** `kill_switch_file` ile aynı aile ("yolu değiştirmek kill-switch'i taşımaz").
Fark: `kill_switch_file` BEYANLI, bu değil.

**Önerilen kapama (öneri).** Ya `guard.validate_change` anahtarı gerçekten okusun
(`goal.get("one_variable_only", True)` — fail-safe varsayılan True), ya da `goal.yaml`'a
"BİLGİLENDİRİCİ — kural kodda sabittir, bu satır onu kapatmaz" gerekçesi yazılsın. Kural gevşemez;
gevşetilebilir olduğu İDDİASI kalkar.

---

### B-4 · `sieve.json` beyanı BAYAT — ve bekçi bunu göremiyor (yapısal `stale_sinks` deliği)

**Ne.** `codelaw.DECLARED_SINKS["sieve.json"]` (`codelaw.py:403-405`) diyor ki: *"ŞU AN tek okuyucusu
kendi testidir (tests/test_sieve_v58.py); panoya bağlanması o iş kolunun işi."* Bu cümle artık
DOĞRU DEĞİL: `api.py:3202` `sieve.report()` çağırıyor, sonuç `api.py:2232 _terfi_hukmu()`'ne gidiyor
ve **TERFİ HÜKMÜNÜ** belirliyor (`api.py:2342`). Yani artefakt bir karar girdisi hâline gelmiş.

**Neden tehlikeli.** `codelaw`'un `stale_sinks` dedektörü bu vakayı yapısal olarak yakalayamaz:
`stale_sinks = [k for k in DECLARED_SINKS if k in out and not out[k]["unread"]]`. `sieve.json`'ı
okuyan tek `store` çağrısı `sieve.py:148`'dir — yani yazar da okur da `sieve.py`, `external_readers`
BOŞ, `unread` hâlâ True, muafiyet hâlâ "geçerli" görünüyor. Muafiyet listesinin kendi kuralı
("muafiyet işi bittikten sonra da yerinde dursaydı liste kimsenin bakmadığı çöplüğe dönerdi")
burada **çalışmıyor**, çünkü tetikleyicisi yanlış sinyale bağlı.

**Hangi sınıf.** Beyanın gerçeği örtmesi — `learning_loop_open.json` vakasının (2026-07-26) tersi:
orada beyan olmayan bir okuyucuyu iddia ediyordu, burada beyan var olan bir okuyucuyu inkâr ediyor.

**Önerilen kapama (öneri).** `sieve.json` satırı `DECLARED_SINKS`'ten ÇIKARILSIN ve metni
`api.py:3199`'daki gerçek zincire bağlansın. Yapısal: `stale_sinks` yalnız `unread`'e değil,
beyanın METNİNDE adı geçen okuyucunun hâlâ var olup olmadığına da bakamaz — bu yüzden en azından
beyanların tarih damgalı ve süreli (`devir` cümleli) olması emsali (`shadow_variants.jsonl`,
2026-07-30) tüm satırlara yayılsın.

---

### B-5 · `state/intraday_bars/<gün>.jsonl` — ENVANTERDEKİ TEK GERÇEK ÖLÜ YAZIM, ve BEYAN EDİLEMEZ

**Ne.** `bararchive.archive_frame` (`bararchive.py:111`) her dakikalık çerçeveyi
`state/intraday_bars/<gün>.jsonl`'a yazar; çağıran `hotstate.py:409` (canlı yolda). **Depoda hiçbir
okuyucu yok.** Modülün tek diğer dosya işlemi `_retention` (`bararchive.py:61-75`) — o da yalnız
SİLER. Canlıda dizin mevcut.

**Neden tehlikeli.** İki katmanlı. (1) Canlı sıcak yolda her dakika disk G/Ç yapılıyor ve hiç
kimse okumuyor. (2) Daha ağırı: `bararchive.py`'nin KENDİ dosya başlığı (satır 13-18) sorunu
biliyor ve şunu yazıyor — `DECLARED_SINKS`'e bir satır **EKLENEMEZ**, çünkü anahtarlar `unread`
artefakt adlarıyla eşleşir ve tarihli f-string ad (`{ARCHIVE_DIR}/{day}.jsonl`) hiç çözülmez. Yani
bu artefakt YASA-6'nın **hem ihlal listesine hem muafiyet listesine giremeyen** bir boşlukta
yaşıyor: bekçi onu `unresolved`'a atar ve orada kimse bakmaz.

**Hangi sınıf.** Bugünkü "koruma yeniden-kurma yolu HİÇ YOKTU" vakasının aynası: mekanizma var,
karşılığı yok. Ayrıca `barsarchive.py:43-52` bu sapmayı ZATEN rapor etmiş ("iki arşivin
birleştirilmesi ya da `bararchive`ın emekliye ayrılması bir MİMARİ karardır ve Rol 1'e aittir") —
yani **karar bekleyen bilinen bir kalem**, ama YASA-6 yüzeyinde görünmüyor.

**Önerilen kapama (öneri).** Mimari karar Rol-1'in: ya `bararchive` emekliye ayrılsın (yazım dursun,
dizin arşive), ya `barsarchive` ile birleşsin, ya da bir okuyucu bağlansın. **Ölçüm tarafı bu
turda kapanabilir:** `codelaw.artifact_graph` `unresolved` kalemlerini `report()`'ta SAYIYOR ama
`ok` hükmüne KATMIYOR (`codelaw.py:555`: `ok = not sil and not violations and not UNSCANNED`).
`unresolved` de `ok`'u düşürmeli, ya da `DECLARED_SINKS`'e desen (glob) anahtarı kabul ettirilmeli.

---

### B-6 · `approvals.jsonl` — ONAY defteri yazılıyor, hiçbir KAPI okumuyor

**Ne.** `api.py:4589` operatörün onay/ret kararını deftere yazar. Tek okuyucu `api.py:4410`:
`"pending": store.read_jsonl("approvals.jsonl") if lvl >= 1 else []` → pano. Hiçbir kapı, hiçbir
silahlanma yolu bu defteri okumuyor. Canlıda dosya **YOK** (L0'da uç 403 döner, `api.py:4585`).

**Neden tehlikeli.** `dormant_setup` ile **tam olarak aynı sınıf**: defter yazılıyor, okuyucusu var,
okuyan davranmıyor. Bugün uykuda çünkü `autonomy_level = 0`; **L1'e geçildiği gün** (ROADMAP §8
terfi kapısı) sistem gerçek parayla çalışırken operatörün "onayla" kararı hiçbir icra yoluna
bağlanmamış olacak. Kusur o gün doğmayacak — o gün GÖRÜNÜR olacak.

**Ayırt edici not (yanlış hükümden kaçınma).** Bu, REVIEW planlarının onayıyla KARIŞTIRILMAMALI:
o yol ayrıdır, gerçektir ve davranışsaldır (`loop.operator_onay_ver` → `trade_plans.jsonl` onay
damgası → `loop.girise_uygun` → silahlı küme). Ölü olan `approvals.jsonl` L1 onay kuyruğudur.
`app.js:8468` bu ayrımı zaten not etmiş.

**Önerilen kapama (öneri).** L1 kapısıyla birlikte ele alınmalı, tek başına değil: ya defter
`operator-kalemi` olarak `DECLARED_SINKS`'e "L1 açılana kadar tüketicisiz, devri L1 biletine
bağlı" gerekçesiyle yazılsın (süreli beyan emsali: `shadow_variants.jsonl`), ya da L1 ön-şartı
listesine "onay defterini icraya bağla" maddesi eklensin.

---

### B-7 · `shadow_trades.jsonl` — gölge-v2 işlem defterinin tek tüketicisi bir CLI bayrağı

**Ne.** `shadow_lifecycle.py:574` yazar (canlı gölge yaşam döngüsü). Tek dış okuyucu
`shadow_variants._load_books` (`shadow_variants.py:607`) ve o da yalnız `main()`'in `--karne`
kolundan çağrılır. Canlıda defter **2 satır**.

**Neden tehlikeli / neden DÜŞÜK şiddet.** Kardeşi `shadow_variants.jsonl` 2026-07-30'da tam bu
gerekçeyle muafiyetten ÇIKARILMIŞTI (`analytics.shadow_variant_summary` → `/api/diagnostics` →
pano). `shadow_trades.jsonl` o devri ALMADI ve bugün hiçbir muafiyet listesinde de yok — yani
sessizce bir CLI'a bağlı. Şiddeti düşük tutan şey: defter 2 satırlık, mekanizma yeni ve
`ledgers.CONTRACTS`'te sözleşmesi var.

**Önerilen kapama (öneri).** Kardeşiyle aynı devir: `analytics`'e bir özet + `/api/diagnostics`
alanı; ya da `DECLARED_SINKS`'e süreli beyan.

---

## 6. ÖLÇÜLEMEYENLER (adıyla — `ÖLÇÜLEMEDİ ≠ 0`)

1. **Dolaylı-dal kanıtının çağrı çözümü ad-çakışmalıdır.** Fonksiyonlar-arası yayılım çıplak ada
   göre eşler; `ozet`, `build`, `status`, `today`, `current` adları birden çok modülde var. Bu
   yüzden *yalnız* dolaylı kanıtı olan 4 artefakt elle doğrulandı, ama A-katmanındaki 92 artefaktın
   dolaylı kanıtları **tek tek doğrulanmadı** — onların hükmü DOĞRUDAN dal kanıtına dayanıyor.
2. **`tests/`, `ops/`, `deploy/`, `research/` taranmadı.** Brief kapsamı `meridian/*.py` +
   `meridian/adapters/*.py` idi. Bir artefaktın tek tüketicisi bir ops betiği olabilir
   (`agent_traces.jsonl` beyanı `ops/vaka_sabitle.py`'yi bu gerekçeyle anıyor). "Tüketicisiz"
   hükümleri bu kapsam içindir.
3. **`meridian/web/*.js` yalnız hedefli olarak arandı** (`dashboard_mentions` emsali). Panonun bir
   alanı ÇİZİP çizmediği tek tek doğrulanmadı; `agent_calls` için kaynak kodun kendi beyanı
   kullanıldı.
4. **Alan (KATMAN-4) merceği YALNIZ `dormant_setup`'a uygulandı.** Kalibrasyonun zorunlu kıldığı
   vaka için kuruldu; plan/aday defterlerindeki diğer ~20 kontrol alanı (`exploration`,
   `gate_reasons`, `skill_chain`, `regime_at_plan`, `p_win_shadow` …) bu mercekten GEÇİRİLMEDİ.
   Sınıfın envanteri **AÇIK**tır — bu, bir sonraki kovanın konusudur.
5. **`heartbeat.json` alan düzeyinde ölçülmedi.** 15 okuyucusu var ve `watchdog.OWNED_FIELDS`
   yalnız 4 alanını sahipleniyor (`regime`, `exposure_budget_pct`, `equity`, `last_bar`); geri
   kalan alanların davranışsal tüketicisi tek tek çıkarılmadı.
6. **Yazım yolu hiç koşmamış 9 artefaktın canlı davranışı ölçülemez** (§4.3 sonu). Kod yolu var,
   canlı kanıt yok; "ölü" DEMEZ, "tetiklenmemiş" der.
7. **`.migrated` altı defterin dosya-arka-ucu kalıntısı** SQLite'a taşındığı için dosya
   `mtime`'ları donuktur; `store.stamp()`/`store.mtime()` bunu soyutluyor ama bu soyutlamanın her
   çağıran için doğru çalıştığı bu turda **yeniden sınanmadı**.

---

## 7. SAYIM ÖZETİ

**Tarama hacmi:** 99 kaynak dosya · **617** `store` çağrı yeri · **107** benzersiz artefakt adı
(+ 5 bayrak dosyası, + 20 `goal.yaml` anahtarı/bölümü, + 33 `bounds.yaml` anahtarı, + 13 `store`
kapısı dışındaki `state/` kalemi).

### Kova dağılımı — `store` artefaktları (107)

| Kova | Adet | Not |
|---|---:|---|
| `davranissal` | **92** | 75'i doğrudan motor dalı; 17'si elle doğrulandı |
| `yalniz-gorunurluk` | **14** | 13 MEŞRU (pano/CLI/teşhis, adıyla işaretli) · **1 ŞÜPHELİ** (`approvals.jsonl`) |
| `tuketicisiz` | **1** | `state/intraday_bars/<gün>.jsonl` (B-5) |
| `ureticisisiz` | **0** | Repoda yazarı olmayan `store` artefaktı bulunmadı |
| `operator-kalemi` | **0** | (bu kovaya düşenler tabloda değil — §4.1 ve §2.1'de) |
| `emekli` | **0** | Kill-list/arşiv kaydına bağlanacak emekli artefakt bulunmadı |

### Kova dağılımı — tablo dışı envanter

| Kalem sınıfı | `davranissal` | `yalniz-gorunurluk` | `tuketicisiz` | `operator-kalemi` |
|---|---:|---:|---:|---:|
| Bayrak dosyaları (5) | 2 | 0 | 0 | 3 (`HALT`, `LEARN_HALT`, `INTRADAY_ARM` — üçü de sağlıklı) |
| `goal.yaml` anahtarları (20) | 13 | 1 (`one_variable_only`, ŞÜPHELİ) | **6** (2 beyanlı + **4 beyansız**) | — |
| `bounds.yaml` anahtarları (33) | 30 | 0 | 3 (üçü de dosyada "atıl" diye BEYANLI) | — |
| `state/` kapı-dışı kalemler (13) | 11 | 0 | 0 | 2 (`secrets.json`, `auth.json` — kimlik) |
| Alan düzeyi (KATMAN-4, 1 alan) | 0 | **1** (`dormant_setup`) | 0 | 1 (ROADMAP:205 ile çaprazlandı) |

### Bulgu şiddet dağılımı

| Şiddet | Bulgu |
|---|---|
| YÜKSEK | **B-1** (4 beyansız ölü `goal.yaml` düğmesi) · **B-2** (YASA-6 bekçisinin `_store()` kör noktası) |
| ORTA | **B-3** (`one_variable_only` yanlış kontrol) · **B-4** (`sieve.json` bayat beyanı + yapısal `stale_sinks` deliği) · **B-5** (`intraday_bars` ölü yazımı — beyan edilemez boşluk) |
| DÜŞÜK / GECİKMELİ | **B-6** (`approvals.jsonl`, L1'de patlar) · **B-7** (`shadow_trades.jsonl` CLI bağı) |

---

## 8. BU TURUN HÜKMÜ — TEK CÜMLE

Envanterin **%86'sı sağlıklı** (92/107 davranışsal); ölü yazım **tek** (`intraday_bars`) ve zaten
mimari karar bekliyor. Asıl bulgu artefaktlarda değil **yönetişim yüzeylerinde**: `goal.yaml`'ın
değişmez sözleşmesinde dört beyansız ölü düğme var, ve YASA-6 bekçisinin kendisi `_store()`
desenine kördür — yani bugünkü "sıfır ihlal" hükmü ölçülmemiş bir kapsam üzerine kuruludur.
`dormant_setup` ve `approvals.jsonl` aynı aileyi paylaşır: **karar KAYDEDİLİYOR, kimse o kaydı
okuyup DAVRANMIYOR.**
