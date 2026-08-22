# TASARIM — F8 DURUM SÖZLÜĞÜ (2026-08-22)

**Tahta kalemi:** "F8 durum sözlüğü · 15 bekçi mekanizması + halt_learning" (ROADMAP :213, :332, :1287)
**Tur rolü:** H0→H1 hazırlığı — YALNIZ tasarım belgesi, kod değişikliği YOK. Rol-1 gözden geçirecek.
**Yöntem:** envanter ÖLÇÜLDÜ (grep + kaynak okuma): `meridian/watchdog.py` (3461 satır),
`meridian/obs.py`, `meridian/health.py`, `meridian/api.py` (/api/diagnostics gövdesi :4001-4523),
`meridian/web/app.js` (10 844 satır), `meridian/hermes_runtime.py`. Satır numaraları bu turun
çalışma ağacına aittir (commit a033256 üstü, ağaç temiz).
**Ölçüm sınırı (uydurma yasağı):** canlı A1 state'i OKUNMADI (dağıtım penceresi — ağaç ve canlı
sabit); "panoda okunuyor" hükmü app.js kaynak grep'iyle verildi, tarayıcıda piksel doğrulaması
YAPILMADI. `/api/alpaca/koruma` yanıtının alan-düzeyi kapsamı ölçülmedi (None + neden: bu tur
sunucu koşturmuyor).

---

## 0. SAYIM — "15 bekçi mekanizması" iddiasının ölçümü

İddia tek bir ölçülen sayıya DENK GELMİYOR. Ölçülen dört ayrı sayım tabanı var:

| Sayım tabanı | Ölçülen | Kaynak |
|---|---|---|
| Kadans nabzı bekçisi `EXPECTED` girdileri | **17** | `watchdog.py:107-` (scheduler_poll, hermes_poll, warmup_sprint, cf_advance, p5_calibrations, mirror_reconcile, crosscheck, earnings_refresh, arming_eval, shadow_fit, axis2_cycle, opinion_backfill, sprint_cadence, y4_collect, validation_report, massive_verify, shadowlaw_drift) |
| Bütünlük dedektör ailesi (`integrity_report` altındaki) | **8** | `watchdog.py:1339` (production, conservation, determinism, coherence, monotonicity, ownership, parity, divergence) |
| Alarm-geçişli bekçi hattı (`check_*_and_alarm` fonksiyonları) | **8** | check_and_alarm · check_integrity_and_alarm · check_koruma · check_kitap_damga · check_mutabakat · check_onayli_gonderim · check_liveness · check_universe |
| Rapor fonksiyonu ailesi (modül başlığındaki liste) | **19** | `watchdog.py:16-22` (report dahil; uyuyan_iddia_tara tarayıcı, rapor değil) |

Çapraz kanıt: `docs/RUNBOOK.md:41` **"17 bekçi mekanizması (`watchdog.py::EXPECTED`)"** diyor ve
bu, ölçülen EXPECTED sayısıyla (17) birebir tutuyor. app.js:3040 da "on yedi mekanizmanın hepsi"
diyor. ROADMAP'teki "15" hiçbir güncel sayıma uymuyor → **iddia BAYAT** (EXPECTED'e sonradan
"EK KADANSLAR" bloğu eklendi: y4_collect, validation_report, massive_verify, shadowlaw_drift).
Düzeltmeyi Rol-1 ROADMAP'e işler (bu tur ROADMAP'e yazmaz) — bkz. §5 Açık Soru A1.

---

## 1. ENVANTER A — Kadans nabzı bekçisi (mekanizma bayatlığı)

Tek mekanizma, 17 izlenen kadans. Nabız `beat(ad)` → `state/mechanism_beats.json`;
rapor `report()` → `/api/diagnostics.watchdog`; alarm geçişi `check_and_alarm()` (300 sn poll).

| Üretici | Durum alanları / değerleri | Panoda okunuyor mu (app.js ölçümü) |
|---|---|---|
| `report()` :191 | `stale[] {name,gap_h,expected_h}` · `never[]` · `askida[] {+neden,detay}` · `ok` (SAYI!) · `total` | EVET — :3235-3241 (Penceresinde/Geciken/Hiç koşmamış/Askıda satırları), :7624 sayaç, sessiz_hat bekçi segmenti :3167 (askıda dalı v195-a'da kapatılmış YASA-6 vakası) |
| `check_and_alarm()` :250 | jeton `MECHANISM_STALE` (histerezis: `watchdog_alarmed.json` DOSYA mandalı; günlük tavan `GUNLUK_ALARM_TAVANI=1`) | alarm satırı akış/gelen-kutusunda; taksonomi kartı :3228 |
| `_alarm_gunluk()` (api.py:3321) | `gun · mekanizmalar{alarm,bastirilan,askida,son_askida_neden} · n_alarm · n_bastirilan · n_askida · durum: defter_yok\|dolu · tavan · beyan` | EVET — :6629, :7671-7725 (alarm taksonomisi; "uç vermedi → ÖLÇÜLEMEDİ (0 alarm DEĞİL)") |
| `_hat_cizelgesi()` (api.py:3665) | `diagnostics.cizelge.damgalar` (adım → gerçek saat) | EVET — RENDER.cizelge :6703, C1-4 :7057 |

Durum kelimeleri (kanonik adaylar): **PENCEREDE · GECİKTİ (stale) · HİÇ KOŞMADI (never) ·
ASKIDA (beyanlı bekleme — ne OK ne alarm) · BASTIRILDI (tavan, sayılı)**.

## 2. ENVANTER B — Dedektör/bekçi rapor ailesi

Sütunlar: numara etiketi (docstring'de yazan), hüküm alanları, alarm jetonu+`kind`, mandal türü,
API yüzeyi, pano okuyucu (app.js grep hükmü).

| # etiketi | Fonksiyon | Hüküm/durum alanları | Alarm (jeton · kind) | Mandal | API yüzeyi | Panoda? |
|---|---|---|---|---|---|---|
| "#1 ÜRETKENLİK" | `production_report` :384 | `starved[] · waiting[] · askida[] · ok(SAYI) · total` | MECHANISM_STALE · `starved` | `integrity_alarmed.json` (dosya) | diagnostics.integrity.production | EVET (PAT_TR "üretkenlik" :6162) |
| "#3 KORUNUM" | `conservation_report` :498 | `ok · plans · traded · no_fill · unexplained(SAYI) · rows` | MECHANISM_STALE · `conservation` | dosya | integrity.conservation | EVET (:6172,6206; ayrıca :3349 `wd.conservation_report`) |
| "#3 DETERMİNİZM" (çakışık numara!) | `determinism_report` :605 | `ok · olculemedi · detail · …` (persist'li taban) | DATA_QUALITY · `determinism` (jeton `determinism_unmeasured` ayrı) | dosya | integrity.determinism | EVET (PAT_TR) |
| "#4 TUTARLILIK" | `coherence_report` :1957 | `stale[]{artifact,behind_h} · ok(SAYI) · absent[] · total` | MECHANISM_STALE (bayat türev) | dosya | integrity.coherence | EVET (PAT_TR) |
| "#5 MONOTONLUK" | `monotonicity_report` :2478 | `ok · regressions[] · amnestied · tracked` (+`grant_amnesty` defteri) | DATA_QUALITY | dosya | integrity.monotonicity | EVET (PAT_TR) |
| "#6 SAHİPLİK" | `ownership_report` :2596 | `ok · lost[]` | DATA_QUALITY | dosya | integrity.ownership | EVET (PAT_TR) |
| "7. desen MAKULLÜK" | `parity_report` :934 | `rows[]{check,ok,detail}` — ~20 check adı (universe_coverage, scan_yield, evidence_source, mirror_parity, cf_fidelity_join/quality, llm_pair_join/promotion_rule, ledger_contract:*, ledger_writers, event_ledger_domination, hotstate_sustained_down, intraday_damga:*, yeniden_hesap:*, eleme:*, artifact_unread, brain_availability, brain_chain_distinct, alarm_delivery, notify_channel, alarm_mandal, learning_loop, measured_edge) | MECHANISM_STALE (satır sınıfına göre; :1866-1883) | dosya | integrity.parity | EVET (:6250 "Makullük ihlalleri") |
| "8. desen / #8 DEĞER-EŞİTLİĞİ" (çakışık!) | `divergence_report` :2350 | `esit · total · ayrik[] · olculemeyen[] · beyanli[]` | MECHANISM_STALE (:1875) | dosya | integrity.divergence | EVET (:6178, 6223) |
| — (integrity toplayıcı) | `integrity_report` :1339 | dedektör başına `ok=False + dedektor_dustu + olculemedi + error` yalıtım iskeleti | MECHANISM_STALE · `detector_failed:<ad>` | dosya | diagnostics.integrity + integrity_age_s | EVET (:6157-6301) |
| — (sözleşme hükmü) | `goal_failure_report` :1734 | `failed ∈ {True,False,None}` (`ok` DEĞİL!) · `threshold · realized_30d · n · detail` | GOAL_FAILURE | dosya (`integrity_alarmed`) | **YOK** — hiçbir uç servis etmiyor | **HAYIR** (app.js 0 okuma; yalnız jeton taksonomi kartı :3337) |
| — (look-ahead damgası) | `intraday_stamp_report` :1672 | `rows[]{ledger,ok,rows,violations,detail} · ok` | (parity üzerinden) | — | parity satırı `intraday_damga:*` olarak | dolaylı EVET |
| "#8 KORUMA" (çakışık!) | `koruma_report` :2691 | `ok ∈ {T,F,None} · olculemedi · kapsam_disi · neden · korumasiz/toplam · payda_beyani · rows[]{korumali,kismi,…} · motor_disi* · emir_tavani_dolu · sev` | NAKED_POSITION · `korumasiz_pozisyon` / `koruma_olculemedi`; motor-dışı → warn `korumasiz_motor_disi_pozisyon` | **süreç-içi set** `_KORUMA_ALARMED` (beyanlı karar :2657) | `/api/alpaca/koruma` :4914 | EVET (app.js "koruma" 74 kullanım; mutabakat masası kartı) |
| "#9 DAMGASIZ YAZIM" | `kitap_damga_report` :2940 | `ok · olculemedi · damgasiz[] · izlenen · rows[].sinif ∈ {olculemedi, taban_yok, degisim_yok, damgali_degisim, damga_ilerledi_icerik_ayni, damgasiz_yazim}` (izlenen: yalnız portfolio.json) | DATA_QUALITY · `damgasiz_yazim` | süreç-içi `_DAMGA_ALARMED` | **YOK** | **HAYIR** (sinif taksonomisi panoya hiç çıkmıyor; yalnız alarm satırı akışta) |
| "#10 MUTABAKAT TAZELİĞİ" | `mutabakat_tazelik_report` :3059 | `ok · olculemedi · kapsam_disi · neden · kayit_seansi · kitap_seansi · yas_s/yas_h · checked · api_ok · skip_reason · seans_gerisinde · yas_asildi · max_yas_h` | MECHANISM_STALE · `mutabakat_tazeligi` (+`mutabakat_olculemedi`) | süreç-içi `_MUTABAKAT_ALARMED` | **YOK** | **HAYIR** (rapor alanları görünmez; reconcile.date dolaylı görünür) |
| "#11 ONAYLI GÖNDERİM" | `onayli_gonderim_report` :3162 | `ok · olculemedi · kapsam_disi · neden · ihlaller[]{ticker,plan_id,gonderim_izi,onay_ts} · kontrol_edilen · payda_beyani` | ONAYLI_PLAN_GONDERILMEDI · `onayli_plan_gonderilmedi` (ölçülemedi dalı BİLEREK alarmsız — sahibi #10) | süreç-içi `_ONAYLI_GONDERIM_ALARMED` | **YOK** | **HAYIR** (yalnız jeton taksonomi kartı :3265) |
| "KALEM 3 CANLILIK" | `liveness_report` :3361 | `sprint{ok,orphaned,active,phase,age_h,beyan}` · `learning{ok,stalled,n,age_h,beyan}` (ok ∈ {T,F,None}) | MECHANISM_STALE · kind `sprint_liveness`/`learning_stalled` (4 jeton: orphan/stalled/2×olculemedi) | süreç-içi `_LIVENESS_ALARMED` | diagnostics.liveness | EVET (:6602 canlilikBloku) |
| "KALEM 7 EVREN" | `universe_audit_report` :3430 | `status ∈ {yok, unknown, ok…} · olculemedi · reason · n_stale · beyan` | DATA_QUALITY · `universe_drift` (yalnız olculemedi) | süreç-içi `_UNIVERSE_ALARMED` | diagnostics.universe_drift (ham dosya) | EVET (:7629-7636 "ÖLÇÜLMEDİ" kapılı) |
| — (EEMUA bütçesi) | `alarm_budget` :1528 | `dagilim{low,high,emergency:None} · toplam · yuzde · tepe_10dk (+ham/muafiyet beyanları) · duran/duran_adlar · damgasiz · asim · emergency_neden · yuzde_beyan · duran_beyan` | (kendisi alarm üretmez — ölçer) | — | diagnostics.alarm_butcesi (+yas_s) | EVET (:1826, :3578, :6609) |
| — (Level-1 toplama) | `_sessiz_hat` (api.py:2935) | `saglikli (İKİ değerli — ölçülemeyen=sağlıksız, beyanlı) · segmentler[]{ad: bekçiler/kilitler/veri, saglikli, kritik, ozet, n_sapma, sapmalar[], askida[], beyan} · satir` | — | diagnostics.sessiz_hat | EVET (:538, :1824, :3432) |

## 3. ENVANTER C — halt_learning ve mandal/kilit ailesi

### 3a. Durdurma kolları (normal konum: KAPALI; açık olması sapmadır — sessiz_hat "kilitler" segmenti)

| Kol | Kaynak gerçeği | Yazar(lar) | Okur (API alanı) | Pano adı | Alarm |
|---|---|---|---|---|---|
| Acil durdurma (kill-switch) | dosya `state/HALT` (`health.halted()/set_halt` :30-62) | `/api/halt` · `/api/resume` (`/api/control/halt` EMEKLİ ikiz — delege, :2599) | `hud.halted` · `risk.halted` · `/healthz.halted` · `/api/summary.halted` · metrik `meridian_halted` | sessiz_hat kolu **`soft_halt`** ("Kademe 1") | `HALT_ACTIVE` (api.py:5600) + notify.halted |
| Öğrenme durdurma | dosya `state/LEARN_HALT` (`health.learn_halted()/set_learn_halt` :43-72) | `/api/control/learn_halt` :2638 | `hud.learn_halted` · `risk.learn_halted` | sessiz_hat kolu **`halt_learning`** ("Kademe 4" — ship durur, işlem sürer) | (jeton yok — obs.log `control_learn_halt`) |
| Günlük zarar devre kesicisi | HESAP, dosya değil: `health.circuit_breaker_tripped()` :337; heartbeat alanı `breaker_tripped` (yazar loop.py:2180) | loop | `heartbeat.breaker_tripped` · metrik `meridian_breaker_tripped` | sessiz_hat kolu **`devre_kesici`** ("süre ölçülemez ve uydurulmaz") | `CIRCUIT_BREAKER` (loop.py:1386) |
| Intraday silahlanma | dosya `state/INTRADAY_ARM` — **TERS mantık: dosya VARSA silahlı** (health.py:7) | `/api/intraday-arm` | `intraday.armed` | (kilit segmentinde DEĞİL — bilinçli: durdurma kolu değil) | — |

Not: hermes tarafında halt/learn_halt TÜKETİMİ ayrı kelimelerle yüzeye çıkıyor:
`_state.last_result="learning_halted"`, `_warm_skip ∈ {learn_halted, halted_or_stale, reflect,
bg_reflect, lock_busy, disabled}` (hermes_runtime.py:505-550); pano `warmup.skip`i kendi `S`
sözlüğüyle Türkçeleştiriyor (app.js:4974-4978), `last_result`ı HAM basıyor (app.js:9869).
intraday_cycle atlama sayaçları da kendi kelimelerini kullanıyor: `skipped{session,halt,stale,no_bars}`.

### 3b. Mandal (latch) rejimleri — üç ayrı katman, iki saklama rejimi

| Katman | Saklama | Kayıtlar | Davranış |
|---|---|---|---|
| obs alarm-imza mandalı | dosya `state/alarm_mandal.json` (obs.py:249) | `MANDAL_IMZALAR`: yalnız MIRROR_DRIFT (`drift_sinifi`; icra/koruma_dolumu HARİÇ) + DATA_QUALITY (`bar_kaynak_uyusmazligi`) | bilinen-aktif durum satırsız SAYILIR; `tekrar_mandali` işareti + `mandal_yeniden` (geri gelen durum); dış okuyucu `parity_report` `alarm_mandal` satırı :1286 (fail-open: mandal arızası alarmı yutamaz) |
| bekçi histerezis mandalları (dosya) | `watchdog_alarmed.json` (kadans) · `integrity_alarmed.json` (bütünlük+goal_failure) | jeton kümeleri (`starved:*`, `detector_failed:*`, `determinism_unmeasured`, `goal_failure`…) | süreç ölse de tutar; toparlanınca düşer → yeniden bozulunca yeniden alarm |
| bekçi histerezis mandalları (süreç-içi) | `_KORUMA_ALARMED · _DAMGA_ALARMED · _MUTABAKAT_ALARMED · _ONAYLI_GONDERIM_ALARMED · _LIVENESS_ALARMED · _UNIVERSE_ALARMED` | jetonlar (`korumasiz:<sym>`, `damgasiz:<ad>`, `mutabakat_bayat:<seans>`, `onayli_gonderilmedi:<plan>`, `sprint_orphaned`, `learning_stalled`, `*_olculemedi`…) | BEYANLI karar (:2657): diske yazmak `artifact_unread` yüzeyi doğururdu; restart'ta durum başına EN FAZLA bir fazla alarm — kabul edilmiş bedel |

### 3c. Alarm jeton sözlüğü (obs.py — 14 `ALARM_` sabiti; NOTIFY_TOKENS bunlardan TÜRETİLİR)

HEARTBEAT_STALE · ROLLBACK · CIRCUIT_BREAKER · DATA_QUALITY · HALT_ACTIVE · MIRROR_DRIFT ·
BROKER_REJECT · TRAIL_DESYNC · MECHANISM_STALE · ARMING_READY · AUTHORITY_CHANGE · GOAL_FAILURE ·
NAKED_POSITION · ONAYLI_PLAN_GONDERILMEDI.
Seviyeler: `info`(bütçe dışı) / `warn`→EEMUA low / `alarm`→EEMUA high / **emergency: ÜRETİCİSİ YOK**
(sayaç None + `emergency_neden` — v196 disiplininin örnek uygulaması).
Pano taksonomi kartları 14'ün 14'ünü `jetonlar` listelerinde taşıyor (app.js:3228, 3265, 3309,
3337, 3370) — jeton düzeyinde YASA-6 açığı ÖLÇÜLMEDİ→bulunamadı.
`MECHANISM_STALE` tek jeton altında ≥8 ayrı olgu sınıfı taşıyor; ayrım `kind` alanına devredilmiş:
`starved · conservation · detector_failed · determinism(→DATA_QUALITY) · mutabakat_tazeligi ·
sprint_liveness · learning_stalled` + kadans gecikmesi (kind'siz, `mechanism` alanı). Bu `kind`
listesi bugün HİÇBİR yerde tek liste hâlinde durmuyor — kanonik sözlüğün §4c tablosu o listedir.

---

## 4. TUTARSIZLIK ENVANTERİ (16 kalem, 4 sınıf)

### T1 — Aynı kavrama birden çok ad (9 kalem)

| # | Kavram | Ölçülen adlar | Kanıt |
|---|---|---|---|
| T1.1 | Öğrenme durdurma mandalı | `LEARN_HALT` (dosya) · `learn_halted` (health/API/hud/risk) · `halt_learning` (sessiz_hat kolu + tahta) · `learning_halted` (hermes last_result) · `learn_halted` (_warm_skip) | health.py:6, api.py:2978, hermes_runtime.py:507-508 |
| T1.2 | Acil durdurma | `HALT` (dosya) · `halted` (API ×4 yüzey) · `soft_halt` (sessiz_hat kolu) · `HALT_ACTIVE` (jeton) · `meridian_halted` (metrik) · `halt` (intraday skipped anahtarı) | §3a |
| T1.3 | Hüküm alanının adı | `ok` (dedektörler) · `failed` (goal_failure) · `saglikli` (sessiz_hat) · `status` (universe_drift) · `durum` (alarm_gunluk/nous_fisler) | §2 |
| T1.4 | Açıklama alanının adı (2 dil, 7 ad) | `neden` · `beyan` · `detail` (parity/integrity/obs) · `detay` (kitap rows, sessiz_hat sapmalar) · `note` (production) · `reason` (universe/skip_reason) · `error` (dedektör düşmesi) | §2 tabloları |
| T1.5 | "stale" çok anlamlı | kadans gecikmesi (`watchdog.stale`) · türev bayatlığı (`coherence.stale`) · nabız bayatlığı (`health.stale()`/`t.stale`) · `halted_or_stale` (hermes) | app.js:1180 vs :3236 |
| T1.6 | "ölçülemedi" ifade biçimi | `ok=None`+`olculemedi` (koruma/mutabakat/onayli/liveness/kitap) · `olculemedi` tek başına (universe, `status` yanında) · `failed=None` (goal) · `dedektor_dustu`+`olculemedi` (integrity yalıtımı) · `olculemeyen[]` (divergence, kaynak-başına) | §2 |
| T1.7 | Numara şeması çakışık: "#1" iki mekanizma (bayat-geçiş :251 + üretkenlik :385), "#3" iki (korunum :499 + determinizm :606), "#8" iki (divergence :1984 + koruma :2624); #2 hiç yok; parity yalnız "7. desen"; üstüne ikinci şema "KALEM 3/7"; üçüncü sayı ailesi `integrity_registry.PATTERNS=6` (panoda "7/6 desen" çelişkisi yaşanıp AYRI adlandırmayla kapatılmış — :1348-1351 emsal) | | watchdog.py docstring'leri |
| T1.8 | `MECHANISM_STALE` aşırı yüklü (≥8 olgu sınıfı tek jetonda; ayrım `kind`ta, kind sözlüğü yok) | | §3c |
| T1.9 | "askida" iki tip: report()'ta satır listesi (dict'ler), alarm_gunluk'ta sayaç (int) — ad tutarlı, TİP farklı | | :211 vs api.py:3337 |

### T2 — Panoda okunmayan durum: YASA-6 ADAYLARI (4 kalem)

Dördünün ortak deseni: **alarm satırı akışa düşüyor ama DURUM YÜZEYİ yok** — operatör "şu an ne
âlemde" sorusunu ancak son alarmı bularak cevaplayabilir. (Emsal: sessiz_hat `askida` alanı aynı
sınıftı ve v195-a'da kapatıldı — app.js:3166-3170.)

| # | Üretilen durum | Ölçüm |
|---|---|---|
| T2.1 | `goal_failure_report` (`failed/threshold/realized_30d/n/detail`) | api.py'de servis yolu YOK (grep: yalnız watchdog içi çağrı); app.js 0 okuma |
| T2.2 | `kitap_damga_report` — 6 değerli `sinif` taksonomisi + `izlenen` listesi | uç yok; app.js'te tek "damgasiz" eşleşmesi alarm_butcesi'nin BAŞKA alanı (:3578) |
| T2.3 | `mutabakat_tazelik_report` (`yas_h/seans_gerisinde/yas_asildi/checked/api_ok/skip_reason`) | uç yok; yalnız MECHANISM_STALE satırı |
| T2.4 | `onayli_gonderim_report` (`kontrol_edilen/ihlaller/payda_beyani`) | uç yok; jeton taksonomi kartı jetonu anlatıyor (:3262-3265) ama sayaç görünmez |

Sınır beyanı: bu dördü "artefakt" değil fonksiyon — `codelaw.artifact_graph` onları göremez,
dolayısıyla mevcut YASA-6 denetimi bu sınıfa YAPISAL olarak kör (parity `artifact_unread` yalnız
dosya-artefaktlarını tarar). F8'in kanonik okuyucusu bu körlüğü kapatmanın en ucuz yolu.

### T3 — null/0 ve tip karışması (v196 sınıfı — 2 kalem + 4 temiz emsal)

| # | Bulgu | Ölçüm |
|---|---|---|
| T3.1 | `report().ok` bir SAYI (penceresinde mekanizma adedi), diğer tüm ailelerde `ok` bir HÜKÜM (bool\|None). Aynı ada iki tip; pano :3238 sayı bekliyor (`${wd.ok}/${wd.total}`), sessiz_hat `ozet` aynı sayıyı basıyor. Yarın "ok" hükmü bekleyen bir tüketici sessizce yanlış okur. Aynısı `production.ok` ve `coherence.ok` için de geçerli (sayaçlar). | watchdog.py:224, 697, 1964 |
| T3.2 | `_alarm_gunluk` `defter_yok` dalında `n_alarm: 0, n_bastirilan: 0` dönüyor; ayrım yalnız `durum` alanında. `durum`u okumayan bir tüketici "0 alarm"ı "ölçüldü, sıfır" sanır. (Bugünkü tek okuyucu :7699 doğru davranıyor — risk, gelecek tüketicide.) | api.py:3332 |
| temiz | `alarm_budget.emergency=None + emergency_neden` · universe `n_stale null → "ÖLÇÜLMEDİ"` (app.js:7630) · mutabakat `checked/api_ok` üç değerli · koruma "ok=None ≠ korumasız 0" | örnek uygulamalar — sözlüğe emsal olarak girer |
| beyanlı | `sessiz_hat.saglikli` bilinçli İKİ değerli: "ölçülemeyen segment SAĞLIKSIZDIR" (fail-closed, sözleşmesi docstring'de) — kusur değil, sözlükte BEYAN edilmeli | api.py:2937-2940 |

### T4 — Sayım çelişkisi (1 kalem)

| # | Bulgu |
|---|---|
| T4.1 | ROADMAP (:213/:332/:1287) "15 bekçi mekanizması" ↔ RUNBOOK:41 "17 bekçi mekanizması" ↔ ölçülen EXPECTED=17. ROADMAP bayat (bkz. §0). |

---

## 5. ÖNERİLEN KANONİK SÖZLÜK

### 4a. Hüküm çekirdeği (her bekçi/dedektör satırının ortak şeması)

```
ok           : true | false | null        # null = HÜKÜM YOK (asla "temiz" sayılmaz)
olculemedi   : bool                       # ok=null'un nedeni ÖLÇÜM ARIZASI (alarm sahibi varsa alarmlanır)
kapsam_disi  : bool                       # ok=null'un nedeni YAPILANDIRMA (ör. broker != alpaca_paper) — alarm YOK
askida       : bool / liste               # meşru, sistemin kendi beyan ettiği bekleme — ne OK ne alarm
neden        : str                        # makine-yakın kısa neden (ihlalin YA DA ölçülemezliğin)
beyan        : str                        # insan-okur tam cümle — PANO BUNU BASAR, ikinci metin kurmaz
```
Eşleme kuralı: `detail`/`detay`/`note`/`reason` → `neden`; uzun anlatı → `beyan`; `error` yalnız
`dedektor_dustu` iskeletinde kalır. `failed` → `ok` (işaret ters çevrilerek; goal_failure).
`saglikli` (sessiz_hat) KALIR ama sözlükte "iki değerli, fail-closed" şerhiyle kayıtlıdır.
SAYAÇLAR hüküm adını kullanamaz: `report().ok` → `n_ok` (geçiş: çift alan servis, bkz. §6).

### 4b. Pano durum kelimeleri (operatörün göreceği KANONİK kelime kümesi)

| Aile | Kanonik kelimeler |
|---|---|
| Kadans | PENCEREDE · GECİKTİ · HİÇ KOŞMADI · ASKIDA · BASTIRILDI (sayılı) |
| Dedektör | TEMİZ · İHLAL · ÖLÇÜLEMEDİ · KAPSAM DIŞI · DEDEKTÖR DÜŞTÜ |
| Canlılık | KOŞUYOR · BOŞTA · DURDU (orphan/stall) · ÖLÇÜLEMEDİ |
| Kitap damgası | DEĞİŞİM YOK · DAMGALI DEĞİŞİM · İÇERİK-AYNI YENİDEN YAZIM · DAMGASIZ YAZIM · İLK GÖZLEM · ÖLÇÜLEMEDİ |
| Kilitler | KAPALI (normal) · ÇEKİLİ — kollar: `soft_halt` "Kademe 1 · Soft Halt" · `halt_learning` "Kademe 4 · Öğrenme durdurma" · `devre_kesici` · (`intraday_arm` kol DEĞİL: silah bayrağı, ters mantık) |
| Mandal | İLK ALARM · MANDALLI (tekrar sayaçta) · YENİDEN (mandal_yeniden) · DÜŞTÜ (toparlandı) |

Kural (v196): sayı alanı `null` ise pano ASLA 0 basmaz; "ÖLÇÜLEMEDİ (0 DEĞİL)" kalıbı zorunlu —
mevcut iyi örnekler: app.js:7630, :7699.

### 4c. MECHANISM_STALE `kind` alt-sınıf sözlüğü (bugün dağınık, burada tek liste)

`(kind yok — mechanism=<ad>)` kadans gecikmesi · `starved` · `conservation` ·
`detector_failed` · `mutabakat_tazeligi` · `sprint_liveness` · `learning_stalled`.
(DATA_QUALITY tarafı: `determinism` · `damgasiz_yazim` · `universe_drift` · `bar_kaynak_uyusmazligi`…
NAKED_POSITION tarafı: `korumasiz_pozisyon` · `koruma_olculemedi`.)

## 6. GEÇİŞ HARİTASI (hangi alan hangi kanonik ada — kod DEĞİŞİKLİĞİ bu turda YOK)

| Bugünkü alan (yer) | Kanonik hedef | Geçiş notu |
|---|---|---|
| `goal_failure.failed` | `ok` (ters işaret) + `neden` | tüketicisi yok (T2.1) → kırılma riski sıfır; ÖNCE yüzey aç, sonra adlandır |
| `report().ok` (sayı) | `n_ok` | okuyucular: app.js:3238, api._sessiz_hat:3252 — çift alan servis (ok+n_ok) → app.js geçince eski düşer |
| `production.ok`, `coherence.ok` (sayaçlar) | `n_ok` | okuyucu integrity paneli (:6162+) — aynı çift-alan deseni |
| parity `rows[].detail`, integrity `detail` | `neden` | çok okuyucu; çift alan + bir sürüm sonra eski ad düşer |
| kitap `rows[].detay`, sessiz_hat `sapmalar[].detay` | `neden` | kitap tüketicisiz (T2.2) → doğrudan; sessiz_hat okuyuculu → çift alan |
| production `note` · universe `reason` | `neden` | universe okuyucusu :7636 `ud.status` üzerinden, `reason` okunmuyor → doğrudan |
| sessiz_hat kol adı `soft_halt` ↔ API `halted` | kanonik KOL ADI: `soft_halt`; API alanları `halted` KALIR (4 yüzey + metrik kırılır) — sözlük ikisini AYNI satıra bağlar | ad değiştirme değil, eşleme kaydı |
| `halt_learning` ↔ `learn_halted` ↔ `learning_halted` | kanonik KOL ADI: `halt_learning`; API alanı `learn_halted` KALIR; hermes `last_result="learning_halted"` → `"halt_learning"` (okuyucu :9869 ham basıyor — tek satır) | Açık Soru A3 |
| `MANDAL_FILE`/bekçi mandalları | sözlük §3b tablosu kanonik envanterdir; ad değişikliği YOK | saklama rejimi (dosya/süreç-içi) beyanla kalır |
| Numara etiketleri (#1/#3/#8 çakışık, KALEM 3/7) | tek envanter kimliği: `B-01…B-08` (bütünlük desenleri), `R-08…R-11` (risk kalemleri), `K-` (kadans), `C-` (canlılık/evren) — YA DA numaralar docstring folkloru ilan edilir ve kanonik kimlik fonksiyon ADI olur | Açık Soru A6 |

Sıralama önerisi (bağımlılık): (1) T2 yüzeyleri aç (yeni `diagnostics.bekci_durumlari` bloğu:
goal_failure + kitap_damga + mutabakat + onayli — dört rapor zaten 300 sn poll'da hesaplanıyor,
sonucu dosyaya/yanıta taşımak ucuz) → (2) kanonik okuyucu (aşağıda) → (3) ad geçişleri çift-alanla.

**Kanonik okuyucu (F8 ön-şartı, ROADMAP :1290-1293):** tek fonksiyon
(`watchdog.durum_sozlugu()` ya da api tarafında `_durum_sozlugu()`) — §2/§3 envanterindeki her
aileden {kimlik, ok, olculemedi, kapsam_disi, askida, neden, beyan, kaynak_alan} normalize satır
üretir; pano F8 sözlük sayfası YALNIZ bunu okur. Sentez yok, uydurma yok: her satır kaynak alanın
adını taşır (geçiş haritası canlıda görünür olur).

## 7. AÇIK SORULAR (Rol-1 / operatör kararı)

- **A1 (Rol-1):** ROADMAP'teki "15 bekçi mekanizması" hangi sayıya düzeltilecek — EXPECTED=17 mi
  (RUNBOOK ile tutarlı), yoksa tahta kaleminin kastı alarm-geçişli bekçi HATTI (8) mı? Düzeltmeyi
  Rol-1 işler (bu tur ROADMAP'e yazmadı).
- **A2 (Rol-1/operatör):** T2.1-T2.4 için karar: dört rapor `/api/diagnostics`e çıkarılsın mı
  (YASA-6 kapanışı, öneri §6), yoksa "alarm satırı yeterli yüzeydir" beyanı mı kayda geçsin?
  Beyan seçilirse bu belge o beyanın eviolur ve parity'ye `beyanli-ayri` benzeri kayıt gerekir.
- **A3 (operatör):** Öğrenme kolunun kanonik adı: tahta `halt_learning` diyor, API `learn_halted`
  taşıyor. Öneri: kol adı `halt_learning`, API alanı dokunulmaz. hermes `learning_halted`
  değeri kanonik ada çekilsin mi (tek okuyucu, ucuz)?
- **A4 (Rol-1):** `report().ok` → `n_ok` tip düzeltmesi (T3.1) hangi turda? Çift-alan servisi
  dagit gerektirir (api.py + app.js) — bakım penceresi sırasına girer mi?
- **A5 (Rol-1):** MECHANISM_STALE aşırı yükü: NOTIFY_TOKENS artık `ALARM_*`dan türediği için yeni
  jeton açmak ucuz (obs.py:77 sözleşmesi). `MUTABAKAT_BAYAT` ve `LIVENESS_DOWN` ayrı jeton mu
  olsun, yoksa `kind` sözlüğü (§4c) yeterli mi? (EEMUA bütçesine etkisi: jeton-başına 6 sa susturma
  penceresi ayrışır — KORUMASIZ-ödünç dersinin lehine argüman.)
- **A6 (Rol-1):** Numara şeması (T1.7): tek envanter kimliği mi (geçiş haritasındaki B-/R-/K-/C-
  önerisi), yoksa numaralar folklor ilan edilip kanonik kimlik fonksiyon adı mı? İkincisi ucuz,
  ilki panoda okunabilir.
- **A7 (Rol-1):** `DAMGALI_VARLIKLAR` bugün yalnız `("portfolio.json",)` — #9 bekçisinin kapsamı
  genişletilecek mi (goal.yaml/bounds.yaml dagit [1b] SSoT olduğuna göre adaylar onlar)? F8'in işi
  değil ama envanter bunu görünür kıldı; ROADMAP öneri-havuzuna Rol-1 taşır.
- **A8 (operatör):** F8 sözlüğünün kapsam sınırı: yalnız bekçi+kilit aileleri mi (bu belge), yoksa
  hermes `last_result`/`_warm_skip` ve intraday `skipped` kelimeleri de sözlük sayfasına girer mi?
  (Envanter C notunda ölçüldüler; karar kapsamı belirler.)

---
*Ölçüm ajanı damgası: bu belge yalnız envanter + öneridir; hiçbir eşik, jeton, alan bu turda
değişmedi. Hüküm Rol-1'de.*
