# Meridian hedef-sapma (S2) · id=meridian-hedef-sapma · v? · tazeleme=2026-10-01T13:06:54.606575+00:00
# Meridian Hedef Sözleşmesi Sapma Raporu (S2)

Bu belge, `MERIDIAN_ENGINEERING_LOG.md` "HEDEF SÖZLEŞMESİ" bölümündeki (goal/bounds kararları, limit anahtarları, hedef eşikler) ile 2026-08-17 – 2026-09-20 arası fiili durum arasındaki açık sapmaları belgeler. Üç kategori: (1) Hedef/Eşik/Kısıt karşılanm

---

## 1. Hedef/Bound Sapmaları — Yapılandırma Dağınıklığı

| # | Sözleşme | Fiili Durum | Sapma Sınıfı | Kaynak (tarih / dosya / kimlik) |
|---|---|---|---|---|
| 1 | `MERIDIAN_BIND_HOST` "bağlama adresi" — konfig kapısı | `api.py:66`+`auth_cli.py:57` okuyor; hiçbir başlatıcı yazmıyor → "hayalet bayrak". Önceki `MERIDIAN_TRUST_PROXY` emsal; aynı kalıp ≥6 kez tekrar. tests/ geçmiyor; ops/.plist + systemd drop-in kapsamı yok | Hayalet yapılandırma (LAW 6 ihlali, bekçi yok) | 2026-09; C1; S2R çakışması; gözlem `6ae03cfd`, `meridian-ajan-surec-hatalari` §S8 |
| 1a | `goal_locks` / `kill_switch_file` | `goal.yaml:131` "HİÇBİR KOD OKUMAZ" diyor; değiştirilirse sessiz no-op. `GOAL_KEYS` üyelik seti var ama değer okunmaz (`guard.py:15-17`) | Hayalet yapılandırma — beyanlı kopya tasarımı | 2026-09; `guard.py:15-17`, `goal.yaml:131`, `health.py:14`, `analytics.py:2121` |
| 1b | `goal.yaml` ölü düğmeler | `backtest_gate`, `session_tz`, `style`, `schema_version`, `one_variable_only`, `universe`, `fill`, `explore_rate`(0.15) — değer var, okuyucu yok (%30 ölü) | Beyanlı kopya tasarımı — yanlış güvenlik hissi | 2026-09-05; `state/goal.yaml`, `guard.py:15-17`, gözlem `28960754` |
| 1c | `HEAT_HARD_R=4.5R` | Modül sabiti config'den geçersiz kılınamıyor; `goal.limits.heat_hard_r` anahtarı yok; override mekanizması yok | Bekçi yok — modül sabiti yapılandırdan geçersiz | 2026-09; `guard.py:252,313-315` |
| 1d | `refetch_max: 8` | scheduler.py + api.py + app.js üç yerde literal; kadans/durum hattında config tekilliği disiplini yok | Tek-kaynak ilkesi ihlali | 2026-09; `meridian-uretici-okuyucu-haritasi` §2 |
| 1e | Sektör/ısı tavanı | goal 40.0, bounds.yaml 30.0, guard.py 25.0/6.0, runtime 0 — dört kaynak, üçü ölü | LAW 6 ihlali; P3 reçetesi: tek kaynağa indirme + senkron testi | 2026-09; `meridian-uretici-okuyucu-haritasi` §2 |
| 1f | `min_sample` yedeği 20 vs gerçek 30 | `goal.yaml:33` `min_sample:30` ama `score.py:108` ve `shadow_variants.py:532` anahtar düşerse sessizce 20 tabanıyla çalışır. Köken belirsiz. | Sessiz çöküş — bekçi yok | 2026-09; gözlem `d102c6cd`, `meridian-ariza-kok-neden` S3 §1 n.34 |
| 1g | `MERIDIAN_AGENT_RPD=600` | Birimler kurulmadığı için (dagit [1c] kapısı 2026-08-14) etkisiz | Bekçi yok — yapılandırma okuyucusu yok | 2026-08-14; `meridian-karar-gerekceleri`, `meridian-dagitim-tarihcesi` |
| 1h | `LIVE_EXPECTANCY_CAP_MULT`(0.5)+`LIVE_SUSPEND_RATIO`(0.4) | `config.py` varsayılan + `state/goal.yaml` (varsa kazanır); kaynak adı raporlanmıyor | İki-kaynak anayasası | 2026-09-06; `meridian/config.py → live_expectancy_rule()` |
| 1i | `START_EQUITY=100k` sessiz fallback | Sağlayıcı şema değişikliğinde sessizce 100k üzeri boyutlandırma; uyarı yok | "ULAŞILAMADI ≠ 100k" ihlali | 2026-09; `meridian-uretici-okuyucu-haritasi` §2 |
| 1j | `goal.limits.kill_switch_file` "HİÇBİR KOD OKUMAZ" | `goal.yaml:131` kendi içinde "HİÇBİR KOD OKUMAZ" diyor; değiştirilirse sessiz no-op | Beyanlı kopya tasarımı | 2026-09-05; `goal.yaml:131,172-174`, `guard.py:15-17` |
| 1k | `exit.early_kill_pivot {min:0,max:1}` | `bounds.yaml:53`; Hermes önerebilir, prescreen/replay ölçer, kapı kabul eder, `strategy.yaml`'a iner ama canlı motor uygulayamaz | Terfi kapıları geçersiz | 2026-09-05; `bounds.yaml:53` |
| 1l | `max_position_r:1.0` ghost kuralı | `guard.py:366` kontrolü 0.5R'de bağlamıyor (K-12 gerilimi) | Hayalet kural — beyan-kod ayrışması | 2026-09-05; `guard.py:366` |
| 1m | `refetch_max:8` config tekilliği | `scheduler.py` + `api.py` + `app.js` üç yerde literal `8` | Tek-kaynak ilkesi ihlali | 2026-09; `scheduler.py`, `api.py`, `app.js` |
| 1n | `analytics.py` circuit breaker — sessiz fail-open | `breaker_trips=0` → `met=True` → `auto_met` sayacı artıyor ama `guard.py` okumuyor | Sessiz fail-open | 2026-09-06; `analytics.py`, `guard.py`, `meridian-acik-sorular` §4 |
| 1o | `score._span_days` sessiz fallback | `len(ts)<2` durumunda sessizce 30 güne düşüyor; istisna dalı uyutar ama veri-yok dalı uymaz | Sessiz fallback | 2026-09-05; `score.py`, `meridian-hedef-sapma` §5 n.30b |
| 1p | `?? 0` / `|| 0` null handling yok | 9 dosyada 215 eşleşme; 162 DOM'a yazılıyor; biçimleyici (`tr`, `money`) upstream'dan atlatılıyor | Null handling kuralı yok | 2026-09; 9 dosya, `meridian-acik-sorular` §4 n.10 |
| 1q | `warmup_scale` `1<1` mantık hatası | 154 koşumda hep False; docstring "yukarı-aşağı merdiven" ama davranış "yalnız aşağı"; 7 gün sessizlik kanalı kapalı → **KAPANDI (2026-09-21 otomatik)** | Mantık hatası + sessizlik | 2026-09; `meridian-hedef-sapma` §5 n.25 |
| 1r | `HERMES_WRITE_SAFE_ROOT` iki yüzeyde | Kendi dizinine kısıtlı (§9.4/3), tam envanter tablosu 107 satır; 617 çağrı yeri | Yetki sınırlaması çelişkisi | Gözlem `07b062e6`, `e32d7e3d` (2026-09-07) |
| 1s | `test_MANIFEST_HERMES_SURUMU_SARTA_BAGLAR` | `hermes_requires` ≥ sürüm kısıtını beyan etmezse sessizce yarım kurulur; canlıda v0.19.0 ölçülen | Sessiz yarım kurulum | 2026-09-07; gözlem `fa8d8410` |
| 1t | `offset_kaynak`, `ref_kaynak`, `limit_bps`, `olay` | Tek tüketici = testler; canlıda üretim tükencisi yok | Test-tek-tüketici damgası, ÖLÜ | 2026-09; `meridian-acik-sorular` §1 |
| 1u | `--blue`, `--violet`, `--violet2` jetonları | Tanımlı, sıfır okuyucu (YASA 6 ihlali); diriltildi, jeton sayısı artmadı | Token sözleşmesi kırılması | 2026-09; `meridian-acik-sorular` §1 n.17 |
| 1v | `max_open_positions` = 20 aktif kapasite | EDG-035'te "fiilden ölü knob" (tepe 13); ısı zarfı tarafından bilinçli bağlanıyor | İlan edilen zarfın altında bağlama | 2026-09-05; EDG-035 (refs: EDG-043) |
| 1w | K-03 yönetişim asimetrisi | `max_open=20` LIMIT_KEYS'te (Hermes öneremez) + `position_size_r=0.5–1.0` kum havuzu; üç yol önerisi (a) bounds tavanı 0.5, (b) LIMIT_KEYS'e taşı, (c) bilinçli bırak; operatör kararı bekliyor → **KAPAT-TASARIMDA** | Politika/uygulama uyumsuzluğu | 2026-09; gözlem `0b45db49`, karar S6 #28, `guard.py:174` |
| 1x | CHOP bütçesi 28d kapısı | §2-28d chop 27 < `goal.yaml:33 min_sample:30` → fren kapı ÖLÇEMİYORSA fren yok; dd-cezasının yan etkisi mi politika mı ayrımı yapılmamış | Fren ancak kapı ölçebiliyorsa fren | 2026-09; `goal.yaml:33`, gözlem `16071c8f`, `2220f271` |
| 1y | K-02 PF Eşiği — Karşılanmıyor (KAPATILDI 2026-09-05) | Ölçülen PF 1.1119 < eşik 1.3; Faz-6 `sonuc_hukmu` yapısal olarak kilidi açılamaz | Karşılanmıyor — KAPATILDI | 2026-09-05; gözlem `0ed3cc7e`; karar S6 #27 |

## 2. Limit Anahtarları Sapmaları (guard.LIMIT_KEYS vs goal/bounds)

| # | Sözleşme | Fiili Durum | Sapma | Kaynak |
|---|---|---|---|---|
| 9 | `max_open_positions`, `heat_hard_r`, `derisk_*` bounds.yaml'da ya da goal.yaml:limits'te olmalı | Bunlar bounds.yaml'da YOK (olmamalı); guard.LIMIT_KEYS üyeleridir (bounds.yaml:105-131 iki-sahip yasağı + hükümsüz-eksen yasağı ile gerekçelendirilmiş) | Sözleşme ikamet yeri ayrımı | 2026-09-05; guard.LIMIT_KEYS, bounds.yaml:105-131 |
| 10 | `guard.LIMIT_KEYS` 12 anahtarı "Hermes değiştiremez limitleri" koruyor | Hermes `max_open_positions`'ı değiştiremez (guard.py:174 reddeder) AMA `position_size_r`'yi 0.1-1.0 arası değiştirebilir → K-03 yönetişim asimetrisi | Politika/uygulama uyumsuzluğu | 2026-09-05; guard.py:174, K-03 |
| 11 | `max_open_positions = 20` aktif kapasite | EDG-035'te "fiilen ölü knob" (tepe 13); ısı zarfı tarafından bilinçli olarak bağlanıyor. 13'e indirmek ölçülmemiş bir daraltma olur | İlan edilen zarfın altında bağlama | 2026-09-05; EDG-035 (refs: EDG-043) |
| 12 | `position_size_r` + `max_open_positions` "ayrılmaz ikili" (20 slotla) | config.py yedek yol `position_size_r=1.0` vs strategy.yaml=0.5 → yedekler ayrık, ORTA risk | Varsayılan-yol ayrışması | 2026-09-05; config.py, strategy.yaml |
| 13 | `max_position_r: 1.0` (goal.yaml:117) tek-tek pozisyon risk tavanı | guard.py:366 kontrolü 0.5R'de hiç bağlamaz (GERİLİM K-12) | Hayalet kural | 2026-09-05; guard.py:366, K-12 |
| 14 | `live_expectancy_cap_mult` / `live_suspend_ratio` (canlı beklenti katsayıları) config'de ya da goal'da olmalı | Kodda varsayılan: `LIVE_EXPECTANCY_CAP_MULT=0.5`, `LIVE_SUSPEND_RATIO=0.4`. state/goal.yaml dosyasında anahtar varsa kazanır, her okumada kaynak adıyla raporlanır | İki-kaynak anayasası | 2026-09-06; meridian/config.py → `live_expectancy_rule()` |

---

## 5. Sessiz Başarısızlık / Yanlış Yeşil

| # | Sözleşme | Fiili Durum | Sapma | Kaynak |
|---|---|---|---|---|
| 23 | Alarm "yazıldı = ulaştı" (notify_channel koşullu yeşil) | notify_undelivered.json sayaç artmıyor; parity_report _tot=0 ise alarm_delivery satırı hiç görünmüyor; kanal yanıt verse de vermese de yeşil | "Alarm yazıldı ≠ alarm ULAŞTI" kırılması | 2026-09; şiddet 3 |
| 24 | `START_EQUITY=100k` "yoksa uyarı ver" | Sağlayıcı şema değişikliğinde sessizce 100k üzerinden boyutlandırıyor, uyarı yok | "ULAŞILAMADI ≠ 100k" ihlali | 2026-09 |
| 25 | warmup_scale "yukarı ve aşağı merdiven" (docstring) | `1 < 1` mantık hatası, 154 koşumda hep False; sessizlik kanalı 7 gündür log basmıyor | Mantık hatası + sessizlik | 2026-09; onarım kartı gerekli |
| 26 | `?? 0` / `|| 0` semantiği (null mu, ölçülmüş sıfır mı?) | 9 dosyada 215 eşleşme; 162 DOM'a yazılıyor; ayrım yazara bırakılmış, biçimleyici katmanı (`trn`, `money`) upstream'de atlatılıyor | Null handling kuralı yok | 2026-09; B2 bulgusu |
| 27 | F8 sayım tutarlılığı (15 bekçi) | ROADMAP 15 der, RUNBOOK.md:41 + app.js:3040 "on yedi mekanizma" der, watchdog.EXPECTED=17 | Sayaç/ölçüm çelişkisi | 2026-09-06; WP8-B |
| 28 | `goal.yaml` 28 çapa + 9 bayat (S1-S9) kart kanıtları | ROADMAP 2026-08-1x "GÜNCEL DURUM/bekliyor" kart/commit kanıtlarıyla çelişiyor | Bayat beyan | 2026-09; EDG-2026-067 |
| 29 | WP5-B "SuccessExitStatus canlıda yok" | N1 kanalı artık CANLI (Telegram); gereksiz bakım penceresi + canlı systemd müdahalesi riski | Bayat iş kalemi | 2026-09; OB-2 2026-08-09'da yapılmış |
| 30 | **N1 bildirim kanalı — EN ACİL** | `notify_undelivered.json` sayaç artmıyor; parity_report `_tot=0` ise `alarm_delivery` satırı görünmez; `notify_channel` koşulsuz yeşil; 7 gündür log basmıyor. **fail-notify no-op; sev-1 alarmlar teslim edilmiyor (korumasız 40, MIRROR_DRIFT 34, NAKED_POSITION 8)** | "Alarm yazıldı ≠ alarm ULAŞTI" kırılması — EN ACİL | 2026-09-03; meridian-acik-sorular §4.8; gözlem 0703c366 |

---

| 31 | Alet-gürültüsü p95 çivisi | Tek pencerede hesaplanıyor, paralel worktree CPU contention'ı görmüyor. KILL#1 çivisi (EXE-2026-003); izole koşumda negatif-kontrol sapması %37,1 | Sessiz başarısızlık — "kalıcı köklük yok" | 2026-09; `meridian-ajan-surec-hatalari`; evidence: `90f6cd` turu, §S5 |

| 32 | `SuccessExitStatus=143` tanımsız — `meridian.service` exit-143 → systemd `OnFailure=` ateşir → `meridian-fail-notify.service` NO-OP; `notify.configured()` False → kanal yoksa birim 0 ile çıkuyor. FIX HAZIR ama canlıda uygulanmadı; bakım penceresi bekleniyor | "Alarm yazıldı ≠ alarm ULAŞTI" — bakım penceresi + sudo cp + daemon-reload + restart + elle test-ateşleme gerekli | 2026-09-17; D-8, `meridian-dagitim-tarihcesi`, `meridian-karar-gerekceleri` S6 #39; gözlem `2ec03a26` |

| 33 | Manifest sürüm denetimi — sessiz yarım kurulum | `hermes_requires` ≥ sürüm kısıtını beyan etmezse sessizce yarım kurulur; canlıda v0.19.0 ölçülen (`manifest v53:184`) | Sessiz yarım kurulum — bekçi yok | 2026-09-07; `meridian-karar-gerekceleri`, `meridian-dagitim-tarihcesi` |

## 6. Ertelenmiş / Geri Alınmış Kararlar

| # | Karar | Erteleme/Geri Alma Durumu | Kaynak |
|---|---|---|---|
| 34 | `run.py:worker()` kadansı | **Geri alındı:** İkinci kadans uygulaması üretimde koşmuyordu; üç düzeltilmiş kusur taşıyor (sessions[-1], dataset.load vs load_live, last_processed race). Karar: emeklilik — kadans `scheduler.advance_once`'a geçildi, **ancak daha sonra düzeltilip reverse edildi**. Dockerfile:31, docker-compose.yml:16, README.md:79 hâlâ `python -m meridian.run` öneriyor (WP-P kapsamında güncellenmeli). | 2026-09; gözlem f316f3e7, 8aaf05e |
| 35 | `DD_VETO_MARGIN` sürüklenmesi — **KAPANDI** | §2-20a'da 0,04'te kaldı; test 0,08 == 0,16/2 bekliyor → 62727d6 v238 zinciriyle kapatıldı, arşive alındı | 2026-09-05; meridian/shadowlaw.py:102, goal.yaml:20, 62727d6 v238 |
| 36 | LLM hafıza katmanı — **HİÇBİRİ KAPANDI** | Hindsight/mem0/Supermemory/Honcho üç adayın hiçbirinin veremediği üç şeyi sağlamıyor. Karar: mevcut harness damga dosyaları yeterli | 2026-09; gözlem 8f62926d, 5bfdc4d7 |
| 37 | QC verisi dışa aktarımı — **KAPANDI** | Log-export, Terms 3.3(b)(xvi), "internal LEAN use only", FREE 10KB sınırlamaları nedeniyle QC hiçbir kalemde arşiv kaynağı değil | 2026-09; meridian-acik-sorular §6, meridian-ariza-kok-neden §4 |
| 38 | `run.py:worker()` emekliliğe dönük — **Gerekçe çizilmeden bırakıldı** | Meridian geleneği emekri kararını `~~üstü çizili~~` bırakır; çizilmeyen gerekçe yürürlükte sayılır ve bir sonraki tur düzeltmeyi geri alır → **regresyon riski**. | 2026-08-24; meridian-karar-gerekceleri, 7a9b778a |
| 39 | §2-25c → DAMGALA üst-hüküm aşması | Kaynak belge D-3/1 "DİRİLT" diyordu; ROADMAP §2-25c "DAMGALA" (Rol-1 düzeltmesi). Üstün-hüküm cümlesi eklendi: "kaynak belge D-3/1 maddesi bu satırla aşılmıştır". | 2026-09-05; gözlem b4a2bb64 |

---

| 40 | IEX/SIP → SIP kararı — **ERTELENDİ** (karar S6 #12) | K3: FEED'e göre koşullu kalibrasyon; `5925a2f7`; IEX tabanlı ölçüt −36,8…+16,2 bps sistematik hata üretiyor; FEED kimliği eşiye bağlanmamış; K3 ve SIP kararı ertelendi | 2026-09-05; meridian-karar-gerekceleri §1.1 #12; gözlem `5925a2f7` |
| 41 | `Integrity.production.starved` (FMP 402) — **Operatör Kararı Bekliyor** | FMP ücretsiz plan kota ~250 çağrı/gün; 251 sembol tek tam tazeleme kotayı yakıyor; `fetch_delta` page≥1→402. Önlem B3 vs B4 arası operatör kararı bekliyor | 2026-09-03; meridian-ariza-kok-neden |
| 42 | `seed_boundary` yetkisi 8 günlük açık kalış — **Operatör Kararı Bekliyor** | Kapanış izi yok; meşru açık | 2026-09; meridian-ariza-kok-neden |
| 43 | C3 QC-Giriş — **Operatör Tarafından Engellendi** | Yaşlanıyor ama bayat değil; meşru açık | 2026-09; meridian-ariza-kok-neden |

| 44 | Hindsight Arama/Rerank → KAPANDI | pgroonga 4.0.8 + vector 0.8.6, bge-m3 ONNX, p95 ~10,6s; rrf fail-open mekanizmasıyla çalışır | Karar kapatıldı | 2026-09; `68d6d328`, `d9af2759`, `meridian-karar-gerekceleri` #18 |
| 45 | Scale-out Mekanik Kusuru (EDG-029) → CONCEPT REJECTED | `scale_out_frac>0` promotion → motor-correction kart condition; §2-13 LATENT-DEFECT olarak değerlendirildi | Kavra reddedildi | 2026-09; `6b469584`, `meridian-karar-gerekceleri` #48 |
| 46 | Claude API Bacak Kapatma Kararı — KALICI | Operatör istedi; iki bacaklı kusur ikizleri (commit `f40a032d`) | Karar kalıcı | 2026-09; `f40a032d`, `meridian-karar-gerekceleri` #6 |
| 47 | `@nobet` Profili Elendi — Faz 3'e Bırakıldı | Hermes gateway + ikinci token çakışma riski; token bir sırdır, ajan yaratmaz | Ertelemeye kaldırıldı | 2026-09; `273c952c`, `Spec §7`, `meridian-karar-gerekceleri` #33 |
| 48 | P-3 K1 AYRIK — Operatör Reddetti | `ts` anahtarı, ara işaret yok; bedel bilerek ~14 hafta | **Reddedildi** (karar `7249e6d0`) | 2026-09; `7249e6d0`, `meridian-karar-gerekceleri` S6 #14 |
| 49 | K1 → EDG-2026-042 — Gerçek Friksiyon Bandı Beklemede | K1 n≥30 ∧ ≥10 seans → B4 yeniden açılması için gerçek friksiyon bandı 4-6 hafta bekleme | Operatör reddetti (~14 hafta) | 2026-09; `4239782c`, `2e76e977`, `meridian-karar-gerekceleri` S6 #13 |
| 50 | Karar Değiştirme Kuralı — Uygulandı, Regresyon Riski Açık | Bir kararı değiştirmek = çiviyi BEYANLI gerekçeyle güncellemek. Emekri gerekçe `~~üstü çizili~~` bırakılır; çizilmeyen gerekçe yürürlükte sayılır → **regresyon riski**. Uygulamalar: v198, v266, v197, v154 | Uygulandı (4 kez) | 2026-09-05; `6f47a014`, `meridian-karar-gerekceleri` §2.1 |

| 51 | `meridian-fail-notify.service` — FIX HAZIR ama UYGULANMADI | `SuccessExitStatus=143` tanımsız; `meridian.service` exit-143 → yanlış 'MERIDIAN A1: FAILED' bildirimi devam ediyor. Bakım penceresi + sudo cp + daemon-reload + restart + elle test-ateşleme bekleniyor. | 2026-09-02/04; D-8; `meridian.service:82` |
| 52 | İkinci motor çapraz-doğrulama — KARAR VERİLDİ ama henüz yürütülmedi | LEAN yerelde CLI'sız + FREE bulut backtest; yerel LEAN kurulumu + Massive/Alpaca CSV dönüştürücü. Karar verilmiş, yürütülmemiş. | 2026-09-02; gözlem `ec143ff8` |
| 53 | `PIT yasa motoru` — veri hazır ama motor okumuyor | `research/edgar_facts/` altında `fundamentals.csv.gz`, `earnings_8k_tarihleri.csv` hazır; karmazanç akış FMP anlık takvimine bağlı. | 2026-09-14; `f78cb79`; `research/edgar_facts/` |
| 54 | 2026-09-20 dağıtım durumu — N1 hâlâ boşta | Harness SHA d1ebf14 (2026-09-17T20:10:22Z); MECHANISM_STALE 3, NAKED_POSITION 2, DISK_ESIK 1, MIRROR_DRIFT 1; N1 bildirim kanalı hâlâ boş; sev-1 alarmlar teslim edilmiyor. | `d1ebf14`; 2026-09-20 günlük durum |

| 55 | §2-24b → "Sınanmadı" | `entry_missed_limit` dalına uygulanmamış test boşluğu; AYNA TUTARLILIK YASASI sadece LLM veto dalına uygulanmış | Uygulamadı (test boşluğu) | 2026-08-13; `test_icra_gercekligi_v141.py`; karar `27218552` |

| 56 | B-PENCERE-KAYDIR (WP1) → DEVRİLMEDİ | Karar Pencere 13:45'e kaydırıldı (K2 EVET, 042-HAKEMLİ SÜRESİZ); `barclock.py`, `loop.py`, `intraday_cycle.py` uygulama kodu yaşıyor; kayıt tutarsızlığı | Devredilmedi (regresyon riski) | 2026-08-23; gözlem `8f8809e1`, `9b8b5efa`; karar `7249e6d0` |

| 57 | §2-17 sürüm terfisi prosedürü → RUNBOOK'a Eklenmemiş (AÇIK) | grep=0; codelaw test fikstürleri `line_anchor_unresolved`'dan ayıklanmamış (28→20) | Açıklık (yapılmamış) | 2026-09; commit `8321bd2e`; EDG-2026-067 |

## 7. Ölçüm Hiç Yapılmamış / Bayat Kararlar (YASA 6 bekleme listesi)

| # | Kalem | Bekleyen Hüküm | Kaynak |
|---|---|---|---|
| 37 | U1 | EXE-001 yorum aritmetiği (Rol-1) | 2026-09; Gözlem 39061e58 |
| 38 | U2 | 8 kartta `trial_ids` hâlâ `pending-*`; backfill yapılmamış | 2026-09; Gözlem 730c711c |
| 39 | U3 | `research/cards/README.md` indeksi bayat; EDG-001/002 Active/registered altında | 2026-09; Gözlem 730c711c |
| 40 | U4 | Retro kartsızlar kararı (EAP/Insider/Short-interest/PEAD) | 2026-09; Gözlem 730c711c |
| 41 | U5 | `k_registry` şema kararı; kartlarda statement-K/spent-K alanı yok | 2026-09; Gözlem 730c711c |
| 42 | U6 | `validation_trio` n_trials kart-K'ya bağlı değil (`analytics.py:2608-2615`) → mimari istisna hükmü | 2026-09; Gözlem 730c711c |
| 43 | U7 | Docstring ↔ davranış ayrışması (ömür-boyu sorgu vs R1-rotasyon penceresi) | 2026-09; Gözlem 730c711c |
| 44 | H0 25a-25d damgalama | 25b 5/6 damgalandı (987b552); 25a/25c/25d bekliyor. Beyan kısmen bayat | 2026-09 |
| 45 | WP5 stok kalemleri (M7, M9, 2B, 2C, A4, kill#4 → KAPAT-BAYAT; M8, 2D, 20c, 20d → KAPAT-TASARIMDA) | 15 kalem hüküm bekliyor | 2026-09 |
| 46 | K-02 PF eşiği (ölçülen 1.1119, eşik 1.3) | "Eşik mi taşınmalı, paket mi iyileşmeli?" OPERATÖR kararı | 2026-09; §2-20b |
| 47 | §2-17 sürüm terfisi prosedürü | RUNBOOK'a eklenmedi (grep = 0); RUNBOOK 21:58'de yeniden üretilmiş | 2026-09 |
| 48 | `analytics.RESULT_NET_OVER_FRICTION` — ÖLÇÜLEMEDİ | Net/ödenen friksiyon oranı hesaplanmadı. `islemler_cmb.json` işlem satırlarında `costs` alanı taşımıyor. İşlem sayısı 2,16× arttı; slippage_bps sabit, payda pakete duyarlı. `recompute.py` ile işlem satırına `costs` alanı eklemesi gerekli | 2026-09-05; `meridian-acik-sorular` §5.1; gözlem `aeb81159` |
| 49 | `goal_failure` olayı defterde sıfır kez — ÖLÇÜLEMEDİ | `goal.yaml` dört soru soruyor (target_return_30d, min_sharpe, max_drawdown, failure_below) ama `watchdog.goal_failure_report` yalnız arıza anında konuşuyor. "Hiç başarısız olmadı" ile "rapor hiç konuşmadı" ayrıştırılamıyor | 2026-08-30; `meridian-acik-sorular` §5 |
| 50 | Kaçan gün sayısı — ÖLÇÜLEMEDİ | Hiçbir yerde sayılmadığı için ölçüm yapılamaz. `EXE-2026-005` günlük-bar sınırı: aynı gün hem stop hem limit dokunmuşsa hangisi önce olduğu ölçülemez | 2026-09; `meridian-acik-sorular` §5.7; gözlem db |
| 51 | `candidate_review.json` — Sistem otomatik hesaplıyor, kimse tüketmiyor | ~23 kb/gün; karar hattında hiçbir okuyucusu yok | 2026-09-17; gözlem `f0ae690e` |
| 52 | `counterfactuals.jsonl` — 4 yazıcı, 7 okuyucu ama sıfır yetkili | Append-only + monoton; erişim kontrolü yok; yalnız gölge katmanları besliyor | 2026-09-14; mental model §5 |
| 53 | `state/intraday_bars/<gün>.jsonl` — ÖLÜ YAZIM, okuyucu yok | `bararchive.archive_frame` (`bararchive.py:111`) yazıyor; 171,9 MB birikmiş, 20 dosya; yalnız `_retention` siler; canlı üretim okuyucusu yok | 2026-09-17; gözlem `aeb81159` |
| 54 | `meridian-guard.sh` — 24 korumasız state dosyası | `trades.jsonl`, `equity_curve.json`, `scoreboard.json`, `notify_undelivered.json`…; guard kanca `pre_tool_call` kontrol eder; `.env` KULLANICI-SAHİPLİDİR; profillere OTOMATİK GEÇMEZ; `HERMES_WRITE_SAFE_ROOT` zorunluyu uygulanmamış | 2026-09; `meridian-guard.sh`, gözlem `f5d31c5c`, `a7dbad51` |
|
| 55 | `store.append_jsonl` — Dosya Kilidi Eksikliği (flock YOK) | `store.py:365-376`; 29 çağıran concurrent write; `db_backed` dalında flock YOK → çift-kilit riski; `loop.py:1892` "atomik" yorumu yanıltıcı | Ölçülemez — çift-kilit riski | 2026-09-02; `store.py:365-376`; gözlem `76141f4b` |
| 56 | `meridian-learn` Yenidenbaşlatma / Tick-Watchdog Boşluğu | `warmup_sprint` boşa döndü; ~4 saatte 6s40dk CPU (load ~3.2); `tick-watchdog` learn'ü izlemiyor; 10:37Z SIGTERM→SIGKILL; kalıcı yeniden-başlatıcı yok | Ölçülemez — kalıcı yok | 2026-09-01; `dagitim D-4`; `S8`; gözlem `204cfdd6`, `253e571d` |
| 57 | `meridian.service` Heartbeat Stale (~15 dk) | Daemon thread bağımlılığı; laptopta systemd worker yoksa `loop.daily_cycle` çağılmazsa heartbeat stale tekrarlar | Ölçülemez — stale tekrarı | 2026-09; mental model §3 |
| 58 | Dört Kayıt Mekanizması — HENÜZ YAZILMADI | `production_report` (ne ÜRETİR), `DERIVED_SOURCES` (neyi TÜKETİR), `monotonicity_report` (ne MONOTON kalmalı), `OWNED_FIELDS` (hangi alanların SAHİBİ) — hiçbirü yazılmadı; gerçek üretici→okuyucu eşleşmesi ölçülemez | Ölçülemez — bekçi yok | 2026-09-20; `meridian-bagimlilik-haritasi` S1 |
| 59 | `state/equity_curve.json` veri ayrışması | Yerel donmuş 2026-07-20/94.457,91$ vs canlı DB 2/95 | Veri ayrışması | 2026-09; `d2

## Meridian Üretici→Okuyucu Haritası (S4)

**Kapsam:** A1.canlı sistemi (130.61.126.87) — 2026-08-17 → 2026-09-29 arası taranan gözlemlerden derlenen üretici/okuyucu eşleşmeleri. Yalnız kod veya artefaktla kanıtlanan kalemler dahil edildi; kanıtı olmayan \"bilinmiyor\" olarak işaretlendi. Çelişkili iddialar için en yeni `mentioned_at` tarihi geçerlidir; eşit tarihte çözülmemiş çelişki açıklanmıştır. Kaynak belgeleri: meridian-acik-sorular, meridian-ajan-surec-hatalari, meridian-bagimlilik-haritasi, meridian-hedef-sapma, meridian-dagitim-tarihcesi, mm-0fb27056.

**Güncelleme (2026-09-29):** Bu belge harness üretimidir; her sayı yanındaki dosyadan okunmuştur (EDG-2026-089, TSK-168). Meridian harness dağıtım SHA `50a0af5` ile 2026-09-29T11:05:13Z tarihinde gerçekleşti. 2026-09-29 itibarıyla portföyde 4 açık pozisyon mevcut (gözlem `5f77cd99`); kapanan işlem 1, toplam R -1.01 (0 kazanan, 1 kaybeden). Gölge Pilot EDG-088: n=0, n_acik=6 (2026-09-26→2026-09-29 sabit). EXE-011 dönüşümü: 2026-09-29 karar satırı 0, dolum 0, ayna-satırı 0. Alarm durumu: 6 toplam (MECHANISM_STALE 5, DISK_ESIK 1).

**Dört registration mekanizması** (`production_report`, `DERIVED_SOURCES`, `monotonicity_report`, `OWNED_FIELDS`) bugüne kadar yazılmamış (2026-09-20); bu mekanizmadan gerçek üretici→okuyucu eşleşmesi ölçülmez, mevcut tablo yukarıdaki gözlemlere dayanır.

| Dosya / Artefakt | Üretici | Okuyucu | Sınıf | Kaynak |

|---|---|---|---|---|

| `state/portfolio.json` | 6 yazar | 36 okuyucu | CANLI-BAĞLI | manifest v53:184; `05d910ee` |

| `state/bars_intraday/*.jsonl` | BarsArchiver (Redis) | barsarchive --ozet; tests | CANLI-BAĞLI | barfeed.py; EDG-2026-067 |

| `state/intraday_bars/<gün>.jsonl` | bararchive.archive_frame:111 | YOK | ÖLÜ YAZIM | bararchive.py:111; `8aee449b` |

| `state/insider_signals.json` etc. | İlgili CLI | Yalnız CLI | CANLI (yazar tekliği) | store.write_json; `10389928` |

| `state/meridian.db` (6 defter) | storage.py:700 | analytics.py, pano | CANLI-BAĞLI | storage.py:700; store.py:642 |

| `state/equity_curve.json` | Canlı DB | watchdog.py:1884 | CANLI ama ayrışma | `d20521d8` (yerel 10/108 vs canlı 2/95) |

| `state/goal.yaml` | Operatör | Hiçbir kod OKUMAZ | HAYALET BAYRAK | `28960754`, `97dbdc90` |

| `state/bounds.yaml` | Operatör | Hermes (position_size_r) | CANLI-BAĞLI (kısmen) | dagit.sh:253; `d0b847be` |

| `state/strategy.yaml` | Operatör | config.py:364 | CANLI-BAĞLI | `5c03e05c` |

| `state/notify_undelivered.json` | Bilinmiyor | parity_report | YANLIŞ YEŞİL | mental model §4 |

| `state/fmp_usage.json` | adapters/fmp.py | dashboard | CANLI | `9c1b92c2` |

| `state/.locks/<ad>.lock` | store.file_lock | store.file_lock | MEKANİZMA | store.py:138/167 |

| `mrd:barfeed` (Redis) | marketstream/hotstate | barfeed.py XREADGROUP | CANLI-BAĞLI | 2026-07-23 |

| `mrd:bars:{T}` (Redis) | marketstream (Alpaca) | barsarchive.py | CANLI-BAĞLI | 2026-07-29 |

| `mrd:price`, `mrd:pos` | DEVRE DIŞI | Üretimde YOK | YALNIZ-YAZILIR | 2026-07-30 `11f61720` |

| `state/entry_execution.jsonl` | Loop (WP-S/WP-E) | E2 defteri | CANLI (file_lock) | `76141f4b` |

| `meridian/analytics.py` | — (okuma) | Pano | SAF-OKUMA | `b471af7e` |

| `scheduler.advance_once` ← `run.py:worker()` (ikinci kadans, **emekli** — commit `8aaf05e`, `git show 8aaf05e:meridian/run.py` ile erişilebilir) | `sessions[-1]` (bugünü gece yarısından itibaren \"kapanmış\" sayıyor), `last_processed`, `dataset.load(use_cache=False)` | `scheduler.advance_once` (kadans göçü) — worker() ikili katmanı emekli | 2026-09-02; `f316f3e7`; §C3 |

**Üç düzeltilemeyen kusur:** (a) `sessions[-1]` bugünkü seansı gece yarısından itibaren \"kapanmış\" sayıyorum; (b) `dataset.load(use_cache=False)` `load_live()` değil → Finviz keşfi + aynı-akşam Alpaca bacağı yoktu; (c) `daily_cycle` dönüşü sorgulanmadan `last_processed` yazılıyordu.

**İki kadans yasa:** worker() ve scheduler.advance_once tek depoda yaşayamaz (hiçbir seans-sonrası kadans — öğrenme, Y4, haftalık üçlü, arming, selfreview, orphan sweep, nous, sprint, earnings, intraday gap — worker() içinde yoktu).

**Emekrilme şekli:** Silme değil; `git show 8aaf05e:meridian/run.py` ile tam metin erişilebilir.

| Dört registration mekanizması | HENÜZ YAZILMADI | — | Ölçülemez | 2026-09-20; meridian-bagimlilik-haritasi S1 |

| `state/cf_open.json`, `state/trade_plans.jsonl` | Hermes (`hermes._stamp_llm_opinions` — store.file_lock + update_json/update_jsonl ile) | Hermes + pano | **CANLI-BAĞLI** (düzeltme sonrası) | 2026-09-02 düzeltme, gözlem `29f62ea9` |

| `events.jsonl`, `agent_calls.jsonl`, `agent_traces.jsonl`, `skills_registry.json`, `candidates.jsonl`, `pipeline_runs.jsonl`, `llm_calibration.json`, `component_ic.json`, `skill_recommendations.jsonl`, `nous_eval_runs.json`, `nous_fisler.json` | Çeşitli modüller (analiz kaynağı) | Salt-okuma ölçüm kampanyaları (EDG-2026-067) | **CANLI (salt-okuma tüketicisi)** | dünya `e2fabc8b`; `/opt/meridian/state/` + `~/.hermes/` |

| `SOUL.md`, `skills/.usage.json`, `skills/*.` | İnsan + otomatik yazar | Salt-okuma ölçüm | **CANLI (salt-okuma)** | dünya `e2fabc8b` |

# 8. Tekrarlanan Ders Sınıfları (meridian-tekrarlanan-dersler)

**Özet (tekrarlayan sınıflar)**

Sınıf tek-kök nedeni: Tek-kaynak ilkesi ihlali; bekçi yok. Önlem reçetesi ("tek-kaynağa indirme + senkron-testi") verilmiş ama uygulanma bilinmiyor.

| # | Arıza Kalemi | Kök Neden | Tekrar | Kaynak |
|---|---|---|---|---|
| 1 | `MERIDIAN_BIND_HOST` — api.py:66+auth_cli.py:57 okuyor; hiçbir başlatıcı yazmıyor | Tek-kaynak ilkesi ihlali; bekçi yok | ≥6 kez | 2026-09; 6ae03cfd; meridian-ajan-surec-hatalari §S8 |
| 2 | `refetch_max:8` — scheduler.py+api.py+app.js üç yerde literal | Config tekilliği disiplini yok | 3 kaynak | 2026-09; meridian-uretici-okuyucu-haritasi §2 |
| 3 | Sektör/ısı tavanı — goal 40.0, bounds.yaml 30.0, guard.py 25.0/6.0, runtime 0 | Çok kaynakta temsil; senkron testi yok | 4 kaynak (üçü ölü) | 2026-09; meridian-hedef-sapma §1 |
| 4 | `HEAT_HARD_R=4.5R` — modül sabiti; config'den geçersiz kılınamıyor | Modül sabiti öncelik; override mekanizması yok | Tekrarlayan | 2026-09; guard.py:252 |
| 5 | `goal_locks`/`kill_switch_file` — goal.yaml:131 "HİÇBİR KOD OKUMAZ" | Okuyucu yok | Kalıp tekrar | 2026-09; guard.py:15-17 |
| 6 | `goal.yaml` ölü anahtarları — backtest_gate, session_tz, style, schema_version, one_variable_only, universe, fill, explore_rate (%30 ölü) | GOAL_KEYS seti var ama değer okunmaz | 5+ anahtar | 2026-09-05; state/goal.yaml |
| 7 | `offset_kaynak`, `ref_kaynak`, `limit_bps`, `olay` — tek tüketici = testler | Canlı üretim tükencisi yok | Kalıp | 2026-09 |
| 8 | `--blue`, `--violet`, `--violet2` jetonları — sıfır okuyucu (YASA 6 ihlali) | Tanımlı ama hiçbir kod okumuyor | Tekrarlayan | 2026-09; meridian-hedef-sapma §1 n.17 |
| 9 | `max_position_r:1.0` ghost kuralı — guard.py:366 kontrolü 0.5R'de bağlamıyor (K-12 gerilimi) | Beyan-kod ayrışması | Tekrarlayan | 2026-09-05; guard.py:366 |
| 10 | `LIVE_EXPECTANCY_CAP_MULT`(0.5)+`LIVE_SUSPEND_RATIO`(0.4) — config.py vs goal.yaml; kaynak adı raporlanmıyor | İki-kaynak anayasası; kaynak adı bildirimi yok | 2 kaynak | 2026-09-06 |
| 11 | `exit.early_kill_pivot {min:0,max:1}` — bounds.yaml:53; terfi kapıları geçersiz | Config tanımı var, canlı uygulama yok | Tekrarlayan | 2026-09-05; bounds.yaml:53 |

---

**Ders:** Aynı kavram birden çok dosyaya dağılınca kodda olan ile beyan arasında sürüklenme kaçınılmaz. **Ölçüm zorunlu, bekçi yoksa tekrarlıyor** ("Bu sınıf üçüncü kez doğabilir çünkü kök neden hâlâ var").

| Olay | Bulgu | Doğan Kural / Çivi | Durum |
|---|---|---|---|
| `MERIDIAN_BIND_HOST` | api.py + auth_cli.py okuyor; hiçbir başlatıcı yazmıyor. "Hayalet bayrak" — kapı ateşlenemez ya da yanlış ateşlenir. | Önceki MERIDIAN_TRUST_PROXY emsal. **Aynı kalıp ≥6 kez** (karar tekrarı); tests/ geçmiyor; ops/.plist + systemd kapsamı yok. | **Açık** (C1, S2R çakışması) |
| `refetch_max: 8` | scheduler.py + api.py + app.js üç yerde literal. | "Aynı yasanın iki uygulaması" hata deseni; tek kaynak. | **Açık** |
| Sektör / ısı tavanı | goal 40.0, bounds.yaml 30.0, guard.py 25.0/6.0, runtime 0 — dört kaynak, üçü ölü. | LAW 6 ihlali. Kapama reçetesi: `tek-kaynağa indirme`. | **Açık** (P3) |
| `HEAT_HARD_R=4.5R` | Modül sabiti config'den geçersiz; goal.limits anahtarı yok. | Bekçi yok. | **Önlemsiz** |
| `goal_locks` / `kill_switch_file` | goal.yaml:131 kendi içinde "HİÇBİR KOD OKUMAZ" diyor; değiştirilirse sessiz no-op. GOAL_KEYS üyelik seti var ama değer okunmaz (guard.py:15-17). | Beyanlı kopya tasarımı — yanlış güvenlik hissi. | **Açık (bilinen)** |
| `goal.yaml` ölü düğmeler | backtest_gate, session_tz, style, schema_version, one_variable_only — değer var, okuyucu yok. | Kural kodda sabit; anahtar yapışık düğme. | **Açık** |
| `offset_kaynak`, `ref_kaynak`, `limit_bps`, `olay` | Tek tüketici = testler. | "Test-tek-tükenci" damgası. | **Açık** |

---

**Sınıf tek-kök nedeni:** okuyucu/üretici eşleşmesini ölçen bekçi eksik.

**Ders:** Aynı kavram birden çok dosyaya dağılınca kod ile beyan arasında sürüklenme kaçınılmaz; **ölçüm zorunlu, bekçi yoksa tekrarlıyor**.

| Olay | Bulgu | Doğan Kural / Çivi | Durum |
|---|---|---|---|
| AYNA TUTARLILIK YASASI | LLM veto dalına uygulanmış, entry_missed_limit dalına uygulanmamış. İki defter ayrışıyor. | "Yasa tek-yerde-yaşamalı" çivisi (test_icra_gercekligi_v141.py). | **Açık** (C10, test boşluğu) |
| K-03 yönetişim asimetrisi | max_open=20 LIMIT_KEYS'te (Hermes öneremez); position_size_r=0.5–1.0 bounds kum havuzunda. Çiftin yarısı tek başına çekilebilir. | ROADMAP §2-10(3) politika (b) | **KAPAT-TASARIMDA** |

