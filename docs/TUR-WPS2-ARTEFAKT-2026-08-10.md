# TUR WP-S2 — SİSTEMATİK ARTEFAKT TURU (envanter yürüme) — 2026-08-10

**SALT-DENETİM.** Bu turda kod değişmedi, git koşulmadı, canlıya/ssh'a çıkılmadı, `serve.sh`
koşulmadı. Yazılan tek dosya budur. Okuyucusu: Rol-1 + operatör (YASA 6 tamam).

**Kardeş belge:** `docs/ARTEFAKT-TARAMASI-2026-08-07.md` (ölü-mekanizma avının 4. kovası,
DAVRANIŞSAL tüketici merceği, CANLI envantere karşı). Bu tur farklı soruyu sorar: **yerel `state/`
envanterinin kendisi yürünür** — dosya dosya sahiplik, okuyucu, kadans ve şema dürüstlüğü.
08-07 turunun bulgularının bugünkü durumu §5'te teyit edildi.

---

## 0. YEREL ŞERH (tüm mtime hükümlerinin ön şartı)

`state/` yerelde **canlının kopyası DEĞİL, çalışma kopyasıdır** (LOG sistem haritası: "state/
yalnız A1'de canlı; Mac'teki kopya taşıma anı fotoğrafı"). Yerel çekirdek damga ~2026-07-30
00:10–17:54 (tutarlı tek fotoğraf). Bu yüzden:

- **mtime'dan "canlıda bayat" hükmü BU TURDA VERİLEMEZ** (ssh kapsam dışı). Verilebilen hüküm:
  yerel kopyanın **iç tutarlılığı** (dosya mtime'ı ↔ içerikteki damga) ve **kod-beklentisi ↔
  disk** mutabakatı.
- Fotoğraftan **yeni** görünen her dosya için yerel yazım kaynağı adıyla teşhis edildi (§3.3) —
  hiçbirinde açıklanamayan yazım kalmadı.

## 1. YÖNTEM

1. **Kod tarafı resmi kapı:** `codelaw.artifact_graph("meridian")` koşuldu (statik, salt-okunur).
   Sonuç: **violations=0, stale_sinks=0, orphan_patterns=0**; `unread` listesinin tamamı
   `DECLARED_SINKS` (codelaw.py:224) + `DECLARED_SINK_PATTERNS` (:472) + `HUMAN_INVOKED_SINKS`
   (:500) ile beyanlı. unresolved=24 (tarihli/f-string adlar; B-5 mekanizması kapsıyor).
2. **Fonksiyon düzeyi yazar/okuyucu:** v53 manifestinin `_writes` desenli AST taraması
   `meridian/**` üzerine genişletildi (WRITERS + read_json/read_jsonl/stamp/mtime; sabit-ad
   çözümlemeli). store-dışı erişimciler (auth/secrets/lessons/earnings.csv/bars CSV/loglar)
   grep ile tek tek kapatıldı.
3. **Sahiplik çakışması:** `tests/test_na_revision_v53.py::test_no_module_writes_another_modules_file`
   koşuldu — **YEŞİL** (tüm çok-yazarlı dosyalar `allowed` beyanında; portfolio 6 yazarın 6'sı da
   kilit altında, manifest satır 156-199).
4. **Şema dürüstlüğü:** 14 dosyanın örnek satır/gövdesi elle okundu (uydurma-yasağı kokusu:
   ölçülemeyen yerde 0, None yerine sahte varsayılan).
5. **Aile mutabakatları:** bars evreni (kod `REPLAY_UNIVERSE` ↔ disk), emekli semboller
   (`RETIRED_SYMBOLS`), sprint budaması, kart→kanıt atıf çözünürlüğü.

Kadans kısaltmaları: **S**=seans-sonrası (XNYS kapanışı başına 1) · **S\***=seans içi çok kez
(300sn poll / dakikalık) · **O**=olay-tetikli (işlem kapanışı, öneri, onay, CLI, re-seed) ·
**L**=hermes/LLM döngüsü · **H**=haftalık · **C**=önbellek/kilit iç-durumu · **OP**=operatör kalemi.

---

## 2. ENVANTER TABLOSU — `state/` kökü (85 dosya) + 7 aile

Durum sütunu: aksi yazılmadıkça **SAĞLAM** = yazarı tekil/beyanlı + okuyucusu gerçek (ya da
sink-beyanlı) + kadansı kodda tanımlı + örneklenen şema dürüst.

| Dosya | Yazar (modül.fonksiyon) | Okuyucu (başlıca) | Kadans | Durum |
|---|---|---|---|---|
| .reflect.lock | reflect (fcntl hedefi, reflect.py:878) | flock mekanizması (içeriksiz) | C | SAĞLAM |
| agent_budget.json | hermes._agent_budget_take:1191 / _refund:1239 | api.diagnostics, hermes.quota_state, selfreview | L | SAĞLAM |
| agent_tooluse.json | hermes._agent_call:1878 | hermes.integrations_status → pano (sink-beyan) | L | SAĞLAM |
| alerts_ack.json | api.api_alerts_ack:2103 (uç yazar) | notify.inbox:77 | O | SAĞLAM |
| arming_report.json | arming.evaluate:296 / _rapora_isle:191 | api×3, hermes.evidence_pack, selfreview×2 | S | SAĞLAM |
| auth.json | auth._write:107 (0600 atomik) | auth._read → 51 korumalı uç (beyan codelaw:327) | O | SAĞLAM |
| bar_source_seams.json | data.flush_seams:2438 | data._seams → /api/diagnostics (sink-beyan) | S | SAĞLAM |
| bars_fingerprint.json | watchdog.determinism_report:607 | aynı fonksiyon :605 (dedektör tabanı, sink-beyan) | S | SAĞLAM |
| bars_integrity.json | barrepair.integrity_apply:260 (CLI `--integrity-tara --uygula`) | data.bars_integrity:565 → component_ic/trend_shadow/cf_backfill | O(CLI) | SAĞLAM¹ |
| bars_source.json | data._pin_source:173 | data._bar_source:157 (sink-beyan) | O | SAĞLAM |
| barsarchive.log | ops/barsarchive-run.sh:24 (stdout yönlendirme) | operatör | S* | SAĞLAM (OP-log; yerel 0B) |
| bounds.yaml | operatör + dagit [1b] SSoT (git-İZLİ, c783442) | config.bounds:59 → limits | OP | SAĞLAM |
| brain_cooldown.json | hermes.brain_pause:431 / recovered:409 / stand_down:401 | hermes.brain_availability → /api/hermes (sink-beyan) | O | SAĞLAM |
| broker_reconcile.json | loop.reconcile_broker_state:2071+ | api×3, loop, watchdog.mutabakat_tazelik | S | SAĞLAM |
| broker_reject_ack.json | api ucu (beyan health.py:229; REJECT_ACK_FILE :230) | health.split_rejections:245 | O | SAĞLAM |
| candidate_review.json | hermes.review_candidates:2910 | api.api_signals:1336, hermes.review_backlog | L | SAĞLAM |
| candidates.jsonl | loop.daily_cycle:1364 (merge_dated) + run.replay_seed:281 (beyanlı) | api.api_signals:1319 | S | SAĞLAM |
| cf_fidelity.json | analytics.cf_fidelity:1461 | api, mcp, selfreview, watchdog.parity | S | SAĞLAM |
| cf_open.json | counterfactual.collect:150/advance:241 + hermes damga :2973 (kilitli, beyanlı) | api, mcp, recompute, counterfactual | S | SAĞLAM |
| component_ic.json | component_ic.component_ic:650 / yeniden_uret:799 | analytics.shrunk_component_ic, api:3767 | O(CLI/kadans) | SAĞLAM² |
| counterfactuals.jsonl | counterfactual.advance:243 (append-only; cf_backfill tek-seferlik beyanlı) | 7 okuyucu (api, recompute, intraday_shadow…) | S | SAĞLAM (4.1MB; monotonluk testli) |
| dashboard.log | serve.sh:51 (append) | operatör | S* | SAĞLAM³ (rotasyonsuz) |
| data_quality.json | loop.daily_cycle:1063 (scheduler ortak-beyanlı) | api×3, intraday_shadow._gates | S | SAĞLAM |
| earnings.csv | earnings.refresh:397 / refresh_from_fmp:478 | earnings.in_blackout/coverage (erişimci) | S | SAĞLAM (ağ kalemi bilinen-açık) |
| equity_curve.json | run.replay_seed:204 + sermaye.uygula:382 (beyanlı ikili) | api.api_performance, sermaye×3, ledgerstamp.seed_boundary, recompute | O | SAĞLAM⁴ |
| events.jsonl | obs._emit:71 (append-only) | notify.inbox, obs.recent, selfreview, watchdog×2 | sürekli | SAĞLAM⁵ (8.9MB) |
| exit_efficiency.json | analytics.exit_efficiency:1232 | api, hermes, mcp, reflect._ucb_rank, selfreview×2, skill_evolve, skill_gorus | S | SAĞLAM (\_kaynak damgalı) |
| finviz_universe.json | finviz.discover_universe:260 | finviz.status, marketview.build:232 | S | SAĞLAM |
| fmp_usage.json | fmp._usage:125 | fmp.usage → /api/diagnostics (sink-beyan) | O | SAĞLAM² |
| gate_calibration.json | probgate.refresh_meta_calibration:176 | api, hermes, mcp, probgate, selfreview, watchdog×2 | S | SAĞLAM⁶ |
| goal.yaml | operatör (git-İZLİ SSoT) | config.goal:43 (her karar yolu) | OP | SAĞLAM |
| heartbeat.json | health.write_heartbeat:272 | 15 okuyucu (healthz, pano, sermaye.koken, scheduler…) | S* | SAĞLAM |
| hermes_status.json | hermes_runtime._persist:286 | api:3384, hermes_runtime._restored_baseline | S*/L | SAĞLAM |
| hypotheses.jsonl | memory.record:68 / update_status:116 / writeback_outcome:156 (+sprint, beyanlı) | 17 okuyucu | O/L | SAĞLAM |
| hypothesis_id_hwm.json | memory.record:74 | memory.next_id:60 (sink-beyan; kimlik HWM) | O | SAĞLAM |
| inc_cache.json | reflect._inc_disk_save:98 | reflect._inc_disk_load:82 (önbellek, sink-beyan) | L | SAĞLAM |
| index_crosscheck.json | scheduler.advance_once:1168 | api:3850, loop.daily_cycle:1057 | S | SAĞLAM |
| insider_signals.json | insider.ozet:637 | tüketici BİLİNÇLİ ertelenmiş (beyan codelaw:361, `kapsam.siniflama_hazir_mi` kapısı) | S(y4) | SAĞLAM-beyanlı |
| insider_trades.json | insider._defteri_birlestir:497 | insider.defter_oku:281 → scheduler._y4_collect (dış çağıran ölçülmüş, 2026-08-08) | S(y4) | SAĞLAM |
| integrity_alarmed.json | watchdog.check_integrity_and_alarm:1809 | aynı :1685 (alarm tekilleştirme, sink-beyan) | S | SAĞLAM |
| integrity_audit_log.json | integrity_registry.record_audit:408 | next_audit_target:393 → api coverage (sink-beyan) | S | SAĞLAM |
| intraday_decisions.jsonl | intraday_cycle._handle_symbol:207 | api:3489, health.faz6_kilitleri:161 | S* | SAĞLAM |
| learning_loop_open.json | rollback._open_loop:293 / _close_loop:329 | api._rollback_sicili:3210, rollback | O | SAĞLAM |
| lessons.md | memory.distill_lessons:216 (write_text) | hermes.py:153 (prompt, LESSONS_CAP=4000) + api:1372 | O/L | SAĞLAM |
| llm_calibration.json | analytics.llm_opinion_calibration:1162 | 8 okuyucu (api, hermes, mcp, watchdog.parity…) | S | SAĞLAM⁷ |
| mae_profile.json | analytics.mae_profile:3170 | analytics.system_telemetry, api:3716, hermes.evidence_pack | S | SAĞLAM (rol beyanı gövdede) |
| massive_crosscheck.json | data.flush_xcheck:1010 | data._xcheck:1002 (sink-beyan) | S | SAĞLAM |
| massive_grouped_last.json | massive._write_snapshot_disk:564 | _read_snapshot_disk:555 (süreç-sınırı gerekçeli sink-beyan) | S | SAĞLAM² |
| massive_verify.json | massive.verify:856 (CLI `--dogrula`) | verify_state:632 → yazım-kapısı ("emniyet anahtarı" beyanı) | O(CLI) | SAĞLAM |
| mechanism_beats.json | watchdog.beat:79 | watchdog.report:177 + api._hat_cizelgesi:3059 → pano | S* | SAĞLAM |
| mirror_orders.json | mirror_stream._persist:120 / decay:212 | 7 okuyucu (api, loop.reconcile, mirror_stream) | O/S* | SAĞLAM |
| monotonic_amnesty.json | watchdog.grant_amnesty:1907 | _amnesty_index:1915 (sink-beyan; rapor `amnestied` dışa verir) | O | SAĞLAM |
| monotonic_state.json | watchdog.monotonicity_report:2004 | aynı :2002 + sermaye._peak_affi (dış, 2026-08-01) | S | SAĞLAM |
| near_miss.json | analytics.near_miss_report:1515 | api, hermes, mcp, selfreview×2 | S | SAĞLAM |
| notify_undelivered.json | obs._maybe_notify:141/195 | api.api_alerts_ack:2124, watchdog.parity:1164 | O | SAĞLAM |
| oos_erosion.json | oos_erosion.record:149 | status/report → reflect._gate_eval + api (sink-beyan) | O | SAĞLAM (retro-damga yasağı beyanı gövdede) |
| ownership_state.json | watchdog.ownership_report:2056 | aynı :2043 (dedektör tabanı, sink-beyan) | S | SAĞLAM |
| pipeline_runs.jsonl | skills.pipeline_run:475 | api×3 | S | SAĞLAM |
| portfolio.json | 6 yazar — HEPSİ beyanlı + kilitli (manifest v53:184; loop/run/hermes/sermaye/api/sprint_run) | 36 okuyucu | S*/O | SAĞLAM |
| probe_cache.json | reflect._probe_disk_save:1163 | load:1148 (önbellek, sink-beyan) | L | SAĞLAM (5.9MB) |
| regime.json | loop.daily_cycle:1257 | 22 okuyucu | S | SAĞLAM |
| regime_edge.json | analytics.regime_edge:1549 | api, hermes, watchdog.parity | S | SAĞLAM (\_kaynak damgalı) |
| regime_trigger.json | regime_trigger.evaluate:38 | aynı :28 (sınıf iç-durumu, sink-beyan) | S | SAĞLAM |
| scan_debt.json | loop._scan_debt_add:884 / _collect:933 | aynı (iş kuyruğu, sink-beyan; olaylar dışa) | O | SAĞLAM |
| scheduler_status.json | scheduler._persist:34 / _run:1288 | api:3380 + scheduler._rehydrate:195 | S* | SAĞLAM |
| score_calibration.json | loop.daily_cycle:1726 | 8 okuyucu | S | SAĞLAM |
| score_calibration_history.jsonl | analytics.record_score_calibration_point:986 | aynı :981 + api:3638 | S | SAĞLAM |
| scoreboard.json | versioning.update_scoreboard:91 / set_row_fields:115 + run.replay_seed:268 (beyanlı) | 9 okuyucu | O | SAĞLAM |
| secrets.json | secrets.py:65 erişimcisi (0600; store-dışı bilinçli) | secrets erişimcileri | OP/O | SAĞLAM (git'te YOK — `git ls-files state/` yalnız goal+bounds) |
| self_review.json | selfreview.build:213 / mechanism_ok:75 / failed:99 | api, hermes, mcp, watchdog.production | H/S | SAĞLAM |
| shadow_model.json | shadow_model.save:238 / refit_and_save:331 / _damga_yaz:71 | 10 okuyucu | O(fit kadansı) | SAĞLAM |
| short_interest.json | shortinterest.ozet:348 | durum:353 → scheduler._y4_collect (ölçülmüş dış çağıran) | S(y4) | SAĞLAM |
| sieve.json | sieve.flush:127 | sieve.stages:148 → api._terfi_hukmu + mutation.detector_red + watchdog.parity (B-4 tazelenmiş beyan) | S/O | SAĞLAM² |
| skill_recommendations.jsonl | skills.record_recommendation:390 / apply:437 / auto_shadow:594 | pending_recommendations → /api/hermes (sink-beyan) | O | SAĞLAM |
| skills_registry.json | skills.reconcile_enablement:163 / _touch:449 / apply:436 | skills.registry:102 + api×2 | O/S | SAĞLAM |
| spend.jsonl | spend.record:70 | month_spend/summary + api×2 | L | SAĞLAM |
| sprint_status.json | sprint.start:320 / stop:500 | sprint.status:92 → /api/sprint (sink-beyan) | O | SAĞLAM |
| strategy.yaml | versioning.commit (config.dump_yaml; sprint sandbox-yolu beyanlı) | config.load_strategy:179 | O | SAĞLAM |
| threshold_curve.json | threshold_curve.build:186 | analytics.threshold_cross_note, api:3771 | S | SAĞLAM |
| trade_plans.jsonl | loop (4 yol) + hermes damga :2961 (kilitli) + run — beyanlı üçlü | 26 okuyucu | S/L | SAĞLAM |
| trades.jsonl | loop._persist_trade:1878 (append) + reconcile:2282 + run + ledgerstamp (beyanlı) | 55 okuyucu | O | SAĞLAM⁴ |
| universe_drift.json | loop._universe_drift_check:682 | api:3835 + watchdog.universe_audit:2761 | S | SAĞLAM⁷ |
| validation_ledger.jsonl | validation.record_candidate:341 | analytics.validation_trio, shadowlaw.divergence_table, validation.ledger | O | SAĞLAM |
| watchdog_alarmed.json | watchdog.check_and_alarm:281 | alarm_budget:1496 + aynı :241 (sink-beyan) | S* | SAĞLAM |
| wf_cache_rev.json | data._bump_wf_rev:119 + reflect.clear_wf_caches:123 (beyanlı ikili) | 9 okuyucu (reflect önbellekleri, watchdog) | O | SAĞLAM² |

**Aileler:**

| Aile | Yazar | Okuyucu | Kadans | Durum |
|---|---|---|---|---|
| bars/ (260 CSV) | adapters.data.load_bars (birleştirme) + barrepair (onarım) | backtest/dataset/replay zinciri | S | SAĞLAM — mutabakat TAM: 251 `REPLAY_UNIVERSE` + 8 emekli (bilinçli tutulur, data.py:2145 "DÜŞÜLÜR ama SİLİNMEZ") + SPY endeks = 260 |
| bars_intraday/ (4 gün-dosyası) | YALNIZ barsarchive.py (yazar-tekliği başlıkta, :37-39) | barsarchive digest/CLI | dakikalık | SAĞLAM |
| intraday_bars/ (4 gün-dosyası) | YALNIZ bararchive.archive_frame:111 | gelecek-tüketici BEYAN KAYDI (codelaw.py:472 `DECLARED_SINK_PATTERNS`, Rol-1 hükmü 2026-08-08; 120 gün retention ile süreli korpus) | dakikalık | SAĞLAM-beyanlı |
| history/ (26) | versioning.snapshot (v000N.yaml) + run.replay_seed:176 (re-seed yedekleri) + earnings._snapshot:548 | rollback:333, api:3611, earnings.snapshot_stats | O | SAĞLAM (kanıt arşivi) |
| sprint/ (3 sandbox, 228 dosya) | sprint.start kum havuzu | sprint.status | O | SAĞLAM — birikim SINIRLI: SANDBOX_KEEP=3 + her start'ta budama (sprint.py:39, :211); diskte tam 3 |
| quarantine/ (1 fixture) | constituents karantina yolu (constituents.py:13) | kanıt (kod okumaz — bilinçli) | O | SAĞLAM (kanıt arşivi) |
| .locks/ (tur başında 25, sonunda 27 kilit) | store._FileLock (:158) + test sızıntısı (aşağıda) | flock mekanizması | C | **ŞÜPHELİ → temizlik-adayı** (§3.1) |

Dipnotlar: ¹ yerel mtime 07-31 = yerel barrepair tam-evren taraması (BT-1 turu izi).
² §3.3'teki yerel-koşu izleri. ³ §3.4 önerisi. ⁴ §3.5 "donuk değil olay-tetikli" hükmü.
⁵ büyüme yapısal-monotonik (küçülme watchdog alarmı olur); budama politikası operatör kalemi.
⁶ §4 sınır-vaka notu. ⁷ §4 dürüstlük örneği.

---

## 3. BULGULAR (kanıtlı)

### 3.1 ŞÜPHELİ→temizlik-adayı — `state/.locks/` pytest-yollu kilit birikintisi (25 dosya)

**Kanıt:** `state/.locks/` altında 25 adet sıfır-bayt kilit; adları
`_private_var_folders_..._pytest-of-erdemozturk_pytest-37xx_test_sandbox_reset_..._state_history_v0001.yaml.lock`
biçiminde, damgaları 2026-08-09 19:19–23:36 (dünkü sprint-testi koşuları).
**Kök mekanizma bilinen ve YAZILI:** `tests/conftest.py:137` muafiyet bloğu bunu 2026-08-09'da
beyan etmiş — sandbox testi sprint history'sini MUTLAK yolla kilitleyince kilit adı sandbox yolunu
taşıyor, kilit dizini ise gerçek `_state()/.locks`e düşüyor; bekçi (katman-1) `os.open`ı sarmadığı
için görmüyor ve `.locks/*.lock` bilinçli muaf.
**Yeni olan tek şey birikimdir:** kilitler geçici flock artefaktı ama hiçbir yol silmiyor.
**Birikme hızı bu turun İÇİNDE ölçüldü:** sahiplik merceği için koşulan TEK-testlik, sandbox'sız
AST koşusu (pytest-3728, `test_no_module_writes_another_modules_file`) bile gerçek `.locks/`e 2
yeni kilit bıraktı — yani sızıntı sprint testlerine özgü değil, oturum-düzeyi bir yoldan geliyor
ve HER pytest oturumu ≥2 dosya ekliyor (25 → tur sonunda 27).
**Öneri (uygulama YOK):** (a) periyodik temizlik — `state/.locks/`te adı `_private_var_folders`
ile başlayan sıfır-bayt dosyaları silme kalemi (operatör ya da suite-sonu kancası, Rol-1 kararı);
(b) istenirse kökten: sprint reset'inin history kilidini sandbox-göreli adla alması (ayrı tur işi).

### 3.2 ÖLÜ-ADAY — `docs/provenance_report.json`

**Kanıt:** mtime 2026-07-22 (19 gün); depo genelinde SIFIR referans (docs/, ROADMAP, LOG grep);
içeriği `ok:false` + `llm_opinion` drift satırları — o drift sonradan kapatıldı (hermes
`_stamp_llm_opinions` zinciri canlı). Emsal aynı sınıftan: `meridian/recompute.py:447` kökteki
kopyanın "8 gün bayat + sıfır referanslı" bulunduğunu kayda geçirmiş.
**Öneri:** sil-adayı; ya da bir tur raporuna kanıt olarak bağlanıp `docs/arsiv/` altına taşınmalı.
Karar Rol-1'de.

### 3.3 Bilgi — yerel çalışma-kopyası yazım izleri (bulgu DEĞİL, şerh kaydı)

Fotoğraf-sonrası (07-30+) mtime taşıyan her dosyanın yerel yazım kaynağı teşhis edildi;
açıklanamayan yazım YOK:

| Dosya (yerel mtime) | Kaynak |
|---|---|
| bars_integrity.json (07-31) | yerel `barrepair --integrity-tara` koşusu (BT-1 turu) |
| sieve.json (08-01 12:08) | yerel `component_ic` koşusu — İÇ DAMGA BİREBİR DOĞRULAR: `component_ic.gercek/cf/eslesme` aşamaları `2026-08-01T09:08Z` (=12:08 yerel) |
| bounds.yaml (08-02) / goal.yaml (08-08) | git-İZLİ içerik-aynı yeniden yazım (bilinen sınıf, 2026-08-02 vakası; kapılar main'de) |
| bars/fisv.csv (08-06) | FISV geri-doldurma (evren kararı 2026-07-30, RETIRED_SYMBOLS notu) |
| fmp_usage + massive_grouped_last + wf_cache_rev (08-07 04:40, aynı dakika) | yerel veri tazeleme koşusu (D6 korpus t3 turu, commit 8ce3123 aynı gün) |
| events.jsonl (08-09 15:01Z) | yerel süpürücü koşusu — son satırlar `bar_unadjusted_row_quarantined` (TDG/ALB/EL; v220 koruma×süpürücü turu izi) |
| .locks/* (08-09) | §3.1 |

Tek dikkat kalemi: sieve'in `component_ic.*` aşamaları 08-01'de tazelenirken
`component_ic.json`ın yerel gövdesi 07-30'da kalmış — yani yerel ölçüm koşuları eleme
muhasebesine iz bırakıp ana çıktıyı her zaman yeniden yazmıyor. Yerel kopyada zararsız; ileride
yerel triyajı yanıltmasın diye kayda geçirildi. **Öneri:** ölçüm koşularının sieve yazımını
sandbox'a mı yoksa gerçek state'e mi düşürdüğü tek cümleyle `research/olcumler/README.md`
sözleşmesine eklenebilir (Rol-1 kararı).

### 3.4 Kadans notu — `dashboard.log` rotasyonsuz

`serve.sh:51` uvicorn stdout'unu `state/dashboard.log`a **append** modda yönlendirir; hiçbir
budama yolu yok (yerel 5.06MB — yerel pano önizleme oturumlarından). A1'de systemd journal ana
kanal olduğundan risk düşük. **Öneri:** düşük öncelik; ya logrotate kalemi ya da "bilinçli
sınırsız" notu RUNBOOK'a.

### 3.5 Yanlış-pozitiften dönenler (hüküm: SAĞLAM)

- **trades.jsonl + equity_curve.json (yerel 07-23'te "donuk" görünümü):** bariz-bayat DEĞİL.
  trades olay-tetiklidir (işlem kapanışı başına append); fotoğraf döneminde rejim `chop` +
  `exposure_budget_pct: 0` (heartbeat gövdesi) → planlar `NO_GO` (trade_plans son satır kanıtı:
  "exposure_budget %0 — bugün yeni risk yok"). Kapanan işlem yok → defter büyümez; eğri de
  re-seed/replay tetiklidir (run.py:197-204 zaman-imzası beyanı).
- **Emekli sembol CSV'leri (8 adet):** silinmemeleri KARARDIR — data.py:2145+ "emekliler aday
  listelerinden DÜŞÜLÜR ama SİLİNMEZ"; `is_retired` tek kapı. bars/ mutabakatı §2'de TAM.
- **İki intraday dizini (bars_intraday/ vs intraday_bars/):** kopya/çakışma değil — iki AYRI
  arşivci, yazar-tekliği her iki modül başlığında beyanlı (barsarchive.py:37, bararchive.py;
  sprint.py:55 aynı beyana atıf).
- **quarantine/sp500_constituents.FIXTURE:** çöp değil, karantina kanıtı (constituents.py:13 —
  fixture'ın tarihsel üyelik uydurmasını engelleme vakası).

### 3.6 Anlık-görüntü gecikmesi — kodda-yazarlı, yerelde-henüz-yok 31 dosya

Kod HEAD'i (08-09'a kadar: entity_damga SB-4, watchdog_alarm_gunluk v192, warmup_scale v193,
agent_traces D3, learning_cadence v190, validation_report, nous_*, shadow_books/trades/variants,
skill_gorus*, trend_book, approvals, bar_same_evening, composite_*, entry_execution,
improvement_proposals, intraday_shadow_orders, notify_sent, pool_exhausted_seen, short_interest_float,
skill_auto_shadow, skill_revisions, sp500_constituents, sprint_runs, symbol_no_data…) bu artefaktları
yazar; yerel fotoğrafta yoklar. **Hüküm: bulgu değil** — yerel kopya 07-30 fotoğrafı, mekanizmaların
çoğu o tarihten SONRA doğdu. Canlı varlık doğrulaması bu turun kapsamı dışında (ssh yasak);
istenirse ayrı bir A1 kontrol kalemi.

---

## 4. ŞEMA DÜRÜSTLÜĞÜ (mercek 4) — örneklem hükümleri

Elle okunan 14 gövde/örnek satır: portfolio, heartbeat, scoreboard, shadow_model, trade_plans(son),
candidates(son), llm_calibration, gate_calibration, near_miss, exit_efficiency, oos_erosion,
mae_profile, regime_edge, universe_drift, index_crosscheck, sieve, monotonic_state.

**İhlal bulunmadı; tersine desen güçlü:**
- Ölçülemeyen yerde **null + neden**: `universe_drift {status:"unknown", reason:"HTTP 403"}`;
  `index_crosscheck {cboe_close:null, divergence:null}`; `llm_calibration {n_pairs:0, r_gap:null}`.
- **`_kaynak` soy damgası** yaygın: `source:"yalnız-simüle"`, `n_real/n_cf` ayrımı, aşama listesi
  (near_miss, exit_efficiency, regime_edge, llm_calibration).
- **Rol/beyan gövdede**: mae_profile ("RAPOR — hiçbir kapıya bağlı DEĞİL", `n_eksik_alan:0`
  sayımı), oos_erosion ("retro damga yasağı" beyanı), sieve (düşürme nedenleri adlı sayaçlar).
- Geçti-kontrollerde `note:null` (uydurma gerekçe basılmıyor — trade_plans gate_checks).

**Tek sınır-vaka (ihlal değil, kayıt):** `gate_calibration.json` — `extra_p: 0.0` iken
`n_measured: 1` (kural "son 8 ship" ister). 0.0 burada ölçüm değil politika-varsayılanı (yetersiz
örneklemde marj ekleme); kural metni dosyanın içinde olduğundan okunabilir. İstenirse
`extra_p_gerekcesi:"n<8"` gibi tek alan daha da netleştirir — öneri, zorunlu değil.

---

## 5. `research/olcumler/` + `docs/` aileleri (kısa dört mercek)

**research/olcumler/ (42 girdi + README):**
- *Sahiplik:* README sözleşmesi net — kanıt kopyasını kartla AYNI commit'te **Rol-1** atar; ölçüm
  sandbox'ları scratchpad'de kalır. Çakışan yazar yok (dizin-başına-tek-tur deseni).
- *Okuyucu:* kartlar → kanıt zinciri SINANDI: `research/cards/*.yaml` içindeki 24 benzersiz
  `research/olcumler/...` atıfının **24'ü de çözülüyor (kırık atıf 0)** (ilk taramadaki 4 "kırık"
  benim grep noktalama artefaktımdı; elle doğrulandı — e1_grid/RAPOR_e1.md, trend_rafine/4'lü,
  kesif_2026-08-02 hepsi yerinde).
- *Tazelik:* tarihli adlar kendi damgasını taşıyor; en yenisi `kys002_pbo_dsr_taban_2026-08-10/`
  (bugün — aktif ölçüm, `canli_kopya/`; DOKUNULMADI).
- *Şema:* yumuşak not — 43 dizinin 23'ünde `sonuc.json` yok. Çoğu kart-dışı tur artefaktı
  (renk_rolleri, tipografi_rampa, kesif, butunluk_dokumu…) ya da kanıtı başka adla taşıyor
  (RAPOR_e1.md). Kart-atıflı zincir sağlam olduğundan ihlal değil; **öneri:** README'deki
  "sonuc.json + RAPOR.md" cümlesine "kart-atıflı ölçümler için" kapsam şerhi.

**docs/ (31 girdi):**
- Tarihli tur raporları (ARTEFAKT-TARAMASI-08-07, SISTEM-DENETIMI-08-02, DEVIR-TATBIKATI-08-09…)
  bilinçli-donuk kanıt belgeleri — okuyucusu Rol-1/operatör; N6 tatbikatı (commit 68ea173) bu
  ailenin fiilen OKUNDUĞUNU kanıtladı. SAĞLAM.
- `RUNBOOK.md` canlı; `olcum_standartlari.md` kart disiplininin okunan sözleşmesi. SAĞLAM.
- `docs/mutasyon/2026-08-01.md` tekil tarihli rapor — aile deseninde. SAĞLAM.
- **`docs/provenance_report.json` — ÖLÜ-ADAY (§3.2, ailenin tek kırmızısı).**
- 08-07 taramasının açık uçlarının bugünkü durumu (bu turun teyidi): **B-4** sieve beyanı
  GERÇEKLE değiştirilmiş (codelaw.py:437); **B-5** intraday_bars `DECLARED_SINK_PATTERNS` kaydına
  bağlanmış (codelaw.py:472, devir şartıyla); **B-7** shadow_trades `HUMAN_INVOKED_SINKS` kaydında
  (codelaw.py:500). Üçü de `declared_claims` mekanizmasının sınadığı yapısal beyanlar — bekçi
  bugün 0 ihlal veriyor.

---

## 6. SAYIM + ÖNERİ ÖZETİ

| Kapsam | SAĞLAM | ŞÜPHELİ | ÖLÜ-ADAY | BAYAT |
|---|---|---|---|---|
| state/ kökü (85 dosya) | 85 | 0 | 0 | 0 |
| state/ aileleri (7) | 6 | 1 (.locks birikintisi) | 0 | 0 |
| research/olcumler (42) | 42 | 0 | 0 | 0 |
| docs (31) | 30 | 0 | 1 (provenance_report.json) | 0 |

BAYAT=0 hükmü **yerel şerhlidir** (§0): yerel kopyada iç-tutarsız ya da kod-beklentisiyle çelişen
tek defter yok; canlı tazelik ölçümü bu turun dışında.

**Öneriler (hiçbiri uygulanmadı):**
1. `state/.locks` pytest-yollu sıfır-bayt kilitlerin periyodik temizliği (+istenirse kök çözüm:
   sprint history kilidinin sandbox-göreli adı) — §3.1.
2. `docs/provenance_report.json` sil ya da arşivle — §3.2.
3. `research/olcumler/README.md`ye sonuc.json kapsam şerhi + ölçüm koşularının sieve yazım yönü
   cümlesi — §3.3/§5.
4. `dashboard.log` rotasyon kararı (düşük öncelik) — §3.4.
5. İsteğe bağlı: `gate_calibration`a yetersiz-örneklem gerekçe alanı — §4.
6. İsteğe bağlı ayrı kalem: §3.6'daki 31 dosyanın A1'de varlık/tazelik kontrolü (bu tur ssh'sız).
