# MODÜL ENVANTERİ — 2026-08-15

**Okuyucu (YASA 6):** oturum açan her Claude rolü + operatör. `CLAUDE.md` kural 1'in yol arkadaşı:
mühendislik günlüğü "şu an ne var"ı anlatır, bu belge "neresi nerede ve ne iş yapar"ı. 96 modül,
~66.8k satır. **Tek gerçek kaynak modüllerin kendi başlık docstring'leridir** — bu belge onların
dizinidir; Görev sütunu her modülün kendi başlık satırından (kırpılmış) alınmıştır.

**Güncelleme yöntemi:** docstring'ler değiştikçe tablo yeniden üretilir (basit `ast` taraması:
her `meridian/**/*.py` için `ast.get_docstring` ilk satırı + satır sayısı). Elle satır düzeltme
YAPMA — kaynağı (docstring) düzelt, tabloyu yeniden üret.

**Katman sınırları belgeyle değil sözleşmeyle korunur:** `pyproject.toml [tool.importlinter]`
5 sözleşme (adapters yukarı-yön import etmez · çekirdek-altyapı üst katman tanımaz · saf yapraklar
bağımsız · api > scheduler > loop döngüsüz · backtest > strategy > regime > guard > indicators
döngüsüz). Bilinçli istisnalar ve bilinen `config→obs→store→config` döngüsü orada belgelidir.

---

## 1) Katman katman modüller


### 1. Giriş & Kadans (canlı döngü)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/api.py` | 5472 | FastAPI read-model over state/ + a tiny write surface (HALT / resume / approvals). |
| `meridian/scheduler.py` | 1382 | the local paper-advance loop. On a laptop there is no systemd worker, so nothing |
| `meridian/loop.py` | 3290 | the live forward paper cycle. Runs once per trading day after the close: builds the |
| `meridian/intraday_cycle.py` | 419 | Faz 4 KAPANMIŞ-BAR TÜKETİCİSİ (GÖZLEM-MODU / Faz 4a). |
| `meridian/run.py` | 433 | entrypoint (TOHUMLAMA + TEK ATIŞ). 24/7 KADANS BURADA DEĞİL: `scheduler.advance_once`. |

### 2. Sinyal Çekirdeği (saf karar)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/strategy.py` | 1154 | PURE. No I/O, no clock reads, no network. Index -1 is ALWAYS a closed bar. |
| `meridian/score.py` | 212 | composite performance score in [-1, +1] from realized return vs target, drawdown |
| `meridian/regime.py` | 317 | tags every trade (trend_up \| trend_down \| chop \| high_vol) and builds the P1 |
| `meridian/indicators.py` | 333 | Pure technical indicators over closed OHLCV bars. No I/O, no clock. numpy/pandas only. |
| `meridian/earnings.py` | 768 | the earnings blackout. A swing-momentum entry taken right into an earnings print |

### 3. Kısıt & Yasa Katmanı

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/guard.py` | 667 | the real constraint layer. An instruction to an LLM is a suggestion; a validator is |
| `meridian/health.py` | 295 | heartbeat, stale-data detection, kill-switch, circuit-breaker state. A silent agent |
| `meridian/codelaw.py` | 1106 | İKİ STATİK YASA (2026-07-21). |
| `meridian/ledgers.py` | 538 | DEFTER SÖZLEŞMESİ (2026-07-21). |
| `meridian/ledgerstamp.py` | 490 | İŞLEM DEFTERİNİN KAYNAK DAMGASI (denetim bulgusu BT-1'in kapanışı). |
| `meridian/provenance.py` | 251 | ANAHTAR KÖKEN TAKİBİ: baskın kusur sınıfının GENEL biçimi (2026-07-22). |
| `meridian/integrity_registry.py` | 410 | BİLEŞEN × DESEN kapsam kaydı (2026-07-21). |
| `meridian/sieve.py` | 260 | ELEME MUHASEBESİ (2026-07-21'in doğrudan çıktısı). |
| `meridian/validation.py` | 454 | Y1 DOĞRULAMA ÜÇLÜSÜ: DSR/PSR + PBO/CSCV + aday getiri defteri |
| `meridian/validation_report.py` | 131 | "hangi mekanizma/edge KANITLANIYOR?" (2026-07-21). |
| `meridian/recompute.py` | 664 | AYNI SORUYU İKİ YOLDAN CEVAPLA (2026-07-22). |

### 4. Öğrenme Beyni (Hermes + Kapı)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/hermes.py` | 4597 | the brain. Reads state, forms ONE single-variable hypothesis with Claude, and |
| `meridian/hermes_runtime.py` | 547 | in-process supervisor for the Hermes reflection brain, for LOCAL running. On app |
| `meridian/hermes_composite.py` | 389 | BİLEŞİK ÖNERİ YOLU (Hermes paketi H3 + H4, 2026-07-30). |
| `meridian/reflect.py` | 1928 | the reflection entrypoint. Routes a hypothesis through the honest pipeline: |
| `meridian/probgate.py` | 453 | Eşleştirilmiş Olasılıksal Kapı (karar mekanizması v3, Component 1). |
| `meridian/backtest.py` | 921 | walk-forward out-of-sample engine. THE learning gate. Replays through the exact |
| `meridian/oos_pipeline.py` | 73 | 70/30 OOS bölümleme + teyit yürüyüşü (karar mekanizması v3, Component 2). |
| `meridian/oos_erosion.py` | 229 | OOS AŞINMA DEFTERİ: aynı sınav kâğıdı kaç kez soruldu? |
| `meridian/memory.py` | 217 | the thing that makes it actually learn. Records every hypothesis with its full |
| `meridian/versioning.py` | 127 | strategy.yaml version bumps, immutable history snapshots, and the scoreboard. |
| `meridian/rollback.py` | 442 | automatic, no human in the loop. Once min_sample trades have run under the |
| `meridian/prescreen.py` | 580 | HİPOTEZ ÖN-ELEMESİ: adayları KAPININ KENDİ YASASIYLA ölç, canlıya dokunma. |
| `meridian/sprint.py` | 975 | the 'öğrenme antrenmanı' (learning sprint) CONTROL SURFACE. |
| `meridian/sprint_run.py` | 217 | the CHILD process of a learning sprint (launched by sprint.start()). |
| `meridian/baseline.py` | 322 | EBEVEYN SÜRÜMÜN TABANINI GERÇEKTEN ÖLÇ (2026-07-26). |
| `meridian/threshold_curve.py` | 221 | MIN_SCORE EŞİK EĞRİSİ: kapıyı yükseltmek kâr getirir mi? |
| `meridian/component_ic.py` | 870 | BİLEŞEN IC'si: skorun DÖRT HAM PARÇASINDAN hangisi tahmin gücü taşıyor? |
| `meridian/counterfactual.py` | 292 | Karşı-olgusal defter (öneri #1). Motorun ANA darboğazı kanıt bant genişliği: |
| `meridian/cf_backfill.py` | 222 | karşı-olgusal defteri TÜM TARİHE koşturarak doldurur (2026-07-21). |
| `meridian/mutation.py` | 828 | MUTASYON KOŞUMU: dedektörlerin NEYİ GÖREMEDİĞİNİ ölçer (2026-07-22). |
| `meridian/nous_eval.py` | 875 | NOUS SİSTEM-DEĞERLENDİRME KATMANI (ROADMAP §3.2, 2026-07-30). |
| `meridian/regime_trigger.py` | 39 | Ertelenmiş Rejim Bütçe Tetikleyicisi (karar mekanizması v3, Component 4). |
| `meridian/shadowlaw.py` | 624 | BÜYÜKLÜK YASASI **PARA-v3**: yeni yasanın tanımı + ESKİ YASANIN GÖLGESİ. |
| `meridian/arming.py` | 349 | Silahlanma Değerlendiricisi (#3): uyuyan→ölç→silahla döngüsünün eksik son halkası. |
| `meridian/selfreview.py` | 400 | Haftalık Öz-Değerlendirme (#2) + Çelişki Dedektörü (#3). |
| `meridian/agent_telemetry.py` | 489 | AJAN ÇAĞRI TELEMETRİSİ + HAM İZ DEFTERİ (D3 modül 1 ve 2, 2026-08-07). |
| `meridian/spend.py` | 98 | the Hermes cost ledger + budget guard. A self-improving agent that calls an LLM every |
| `meridian/olcum_araclari.py` | 804 | ÖLÇÜM ŞABLONLARININ ORTAK YARDIMCILARI (WP-M, 2026-08-01/02). |
| `meridian/faz5_cikis.py` | 481 | FAZ-5 ÇIKIŞ ÖLÇÜMÜ: dakika-hassas icranın CI'lı kazancı (kart EXE-2026-002). |

### 5. Gölge Katman (sıfır yetki)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/shadow_model.py` | 471 | Gölge Sonuç-Modeli (karar mekanizması v3, Component 3). |
| `meridian/shadow_variants.py` | 650 | 2.4 GÖLGE-VARYANT PORTFÖYLERİ (2026-07-30). SIFIR YETKİ, KENDİ DEFTERİ. |
| `meridian/shadow_lifecycle.py` | 579 | GÖLGE-v2 YAŞAM-DÖNGÜSÜ MOTORU (2026-07-30). SIFIR YETKİ, KENDİ KÂĞIT DEFTERİ. |
| `meridian/trend_shadow.py` | 577 | UZUN-UFUK TREND KOLU · CANLI PARALEL GÖLGE-KİTAP (WP-K, 2026-07-31). |
| `meridian/intraday_shadow.py` | 844 | FAZ 4B GÖLGE MODU (2026-07-27). SIFIR YETKİ, TAM KARAR. |

### 6. Beceri Katmanı (Axis-2)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/skills.py` | 1068 | the pipeline runner. Skills are bound into five DETERMINISTIC pipelines (§3), each |
| `meridian/skill_evolve.py` | 263 | Skill Revizyon Döngüsü v1 (#5): içerik evriminin güvenli ilk adımı. |
| `meridian/skill_gorus.py` | 614 | GÖRÜŞ DEFTERİ v1 (ön-kayıt kartı EDG-2026-019, 2026-08-09). |

### 7. İcra (paper broker)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/broker.py` | 704 | the paper broker. Realistic frictions or the agent learns a fantasy (Hard Rule 7). |
| `meridian/sermaye.py` | 626 | ANTRENMAN TOHUMUNUN CANLI SERMAYEDEN AYRIŞTIRILMASI (BT-1'in nakit ayağı). |

### 8. Bar / Akış Altyapısı

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/barfeed.py` | 140 | DAYANIKLI bar-tetiği tüketicisi (Faz 3, 2026-07-23). |
| `meridian/barclock.py` | 125 | Intraday LOOK-AHEAD saati (Faz 4). TEK ortak zaman kaynağı + kapanmış-bar admissibility |
| `meridian/bararchive.py` | 119 | Faz 5 KANIT KATMANININ İLK TAŞI: dakikalık bar çerçevelerinin kalıcı arşivi. |
| `meridian/barsarchive.py` | 820 | `mrd:bars:{T}` akışlarının DAYANIKLI disk arşivi (Faz 5 ham maddesi, 2026-07-29). |
| `meridian/barrepair.py` | 397 | DİSKTEKİ bar defterlerinden HAYALET SEANS satırlarını temizleyen onarım aracı. |
| `meridian/marketstream.py` | 216 | PİYASA-VERİSİ dinleyicisi: Alpaca dakikalık KAPANMIŞ bar akışı → mrd:bars (Faz 2). |
| `meridian/mirror_stream.py` | 338 | Olay-güdümlü YÜRÜTME-DURUMU katmanı (operatör mimari isteği, 2026-07-19). |
| `meridian/streamhealth.py` | 288 | WS DİNLEYİCİLERİNİN ORTAK YASASI (2026-07-23, Faz 2). |
| `meridian/hotstate.py` | 525 | Redis SICAK-DURUM katmanı (intraday, 2026-07-23, operatör mimari isteği). |
| `meridian/dataset.py` | 310 | shared loader + backtest windows for the replay universe. One place so reflect.py |

### 9. Veri Kenarı (adapters/)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/adapters/data.py` | 2737 | real daily OHLCV, no API key. Primary: Cboe delayed_quotes historical |
| `meridian/adapters/alpaca.py` | 1552 | Alpaca broker adapter. PAPER by default. The LIVE path is refused unless |
| `meridian/adapters/massive.py` | 951 | Massive (massive.com) EOD bar sağlayıcısı. |
| `meridian/adapters/fmp.py` | 365 | Financial Modeling Prep (STABLE API). Enriches live candidates (fundamentals, |
| `meridian/adapters/finviz.py` | 333 | Finviz'i OTONOM ADAY KAYNAĞI yapar (2026-07-23). |
| `meridian/adapters/insider.py` | 705 | Form 4 (içeriden işlem) verisi: FMP insider-trading uçları (ROADMAP §3.4 Y4). |
| `meridian/adapters/shortinterest.py` | 403 | FINRA Equity Short Interest (ROADMAP §3.4 Y4, "kaçınma filtresi" ayağı). |
| `meridian/adapters/edgar_shares.py` | 430 | EDGAR AS-OF DOLAŞIMDAKİ HİSSE SAYIMI: SALT-OKUNUR VERİ KÖPRÜSÜ. |
| `meridian/adapters/constituents.py` | 259 | point-in-time S&P 500 üyeliği (#36). |
| `meridian/adapters/macro.py` | 24 | EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu). |
| `meridian/adapters/news.py` | 28 | EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu). |

### 10. Kalıcılık & Yapılandırma

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/store.py` | 638 | state persistence helpers. Atomic JSON writes, JSONL append, and numpy sanitization |
| `meridian/storage.py` | 716 | DEFTER ÇEKİRDEĞİNİN SQLite ARKA UCU (WP-H/H9, Kademe A). |
| `meridian/dbmigrate.py` | 634 | DOSYA DEFTERİ → SQLite, PARİTE KANITIYLA (WP-H/H9, Kademe A4). |
| `meridian/config.py` | 361 | Central config + path resolution. Loads the immutable goal.yaml/bounds.yaml and the |

### 11. Gözlem, Pano & Operasyon

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/obs.py` | 319 | structured JSON logging + the ALARM_ tokens the notification chain keys on. |
| `meridian/watchdog.py` | 3407 | Mekanizma Bekçisi (#1): 15+ periyodik dişlinin canlılık nabzı. |
| `meridian/analytics.py` | 4297 | read-model computations over state/ for the dashboard. Pure reads; no mutation. |
| `meridian/marketview.py` | 306 | İZLENEN EVRENİN TEK BAKIŞTA OKUNAN GÖRÜNTÜSÜ (2026-07-27). |
| `meridian/notify.py` | 198 | push a short message to the operator (Telegram or a generic webhook). stdlib only. |
| `meridian/secrets.py` | 221 | Secret Manager, a local 0600 store, or nothing (Hard Rule 5). |
| `meridian/auth.py` | 351 | operatör kimliği: parola doğrulama + imzalı oturum çerezi. |
| `meridian/auth_cli.py` | 96 | operatör parolasını kabuktan yönet. |
| `meridian/mcp_server.py` | 164 | Meridian'ın SALT-OKUNUR durumunu yerel hermes-agent'a MCP aracı olarak açar. |

### 0. Paket Kökleri

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/__init__.py` | 6 | Paket kökü — katman haritasına (bu belge) işaret eder. _(docstring bu turda eklendi)_ |
| `meridian/adapters/__init__.py` | 6 | Kenar katman kökü — importlinter sözleşme 1'e işaret eder. _(docstring bu turda eklendi)_ |

---

## 2) Çekirdek akışların kilit girişleri

**Öneri yaşam döngüsü (öğrenme):**
`hermes_runtime._run:366` (300 sn bekleme döngüsü) → `hermes.reflect_once:4355` →
üretici: `hermes.propose_with_llm:3922` (claude→nous→gemini, bütçe kapısı `:3927`) ya da
determinist yedek `hermes.propose_virgin_knob:4147` →
arka plan süzgeci: `hermes.py:4425-4470` (v246: imha · v247+: sertifikalı rejime yeniden yazım;
retler `_bg_on_eleme_kaydi:4243` → `events.jsonl`, bilinçli olarak hipotez defterine DEĞİL —
gerekçe `hermes.py:4247-4280`) →
tek kapı: `reflect.submit:1007` → `_submit_locked:1018` →
guard: `guard.validate_change:118` (bounds üyeliği `:198`) →
ölçüm: `backtest.walk_forward:837` + `reflect._gate_eval:315` ("TEK yasa"; `probgate.P_BASE=0.80`) →
teyit: `oos_pipeline` (%30 Confirm, `P_CONFIRM=0.70`; ölçülemeyen onay ship'i BLOKLAR — 28f,
`reflect.py:1109-1120`) →
ship: `versioning.bump:41` → geri alma: `rollback.py` + `memory.writeback_outcome:130`.

**İşlem döngüsü (canlı paper):**
`scheduler.advance_once:861` → `loop.daily_cycle:1185` → `strategy.scan_all:1047` →
`guard.classify_gate:370` (GO/REVIEW/NO_GO) → `broker` / `adapters.alpaca` →
`loop._persist_trade:2186` → defter (`state/meridian.db`, `storage.py:70-116`).

**Dağıtım:** yalnız kod — `./dagit.sh --uygula` (temiz-ağaç kapısı → audit → lint-imports →
rsync → [1b] versiyonlu-state anahtar-düzeyi diff → bakım penceresi → doğrulama).
Parametre değişikliği dağıtım İSTEMEZ (`versioning.py:1-3`).

---

## 3) Ad → Anlam sözlüğü (dosya adı kendini anlatmayanlar)

| Ad | Anlamı |
|---|---|
| `hermes` | Öğrenme beyni — LLM'li/LLM'siz hipotez üreticisi (haberci tanrı; öneriyi kapıya taşır) |
| `nous_eval` | "Akıl" katmanı — haftalık sistem öz-değerlendirmesi (A–D katmanları; D anayasal, kilitli) |
| `probgate` | Olasılıksal kapı — P(ΔS>0) eşleştirilmiş bootstrap eşiği |
| `prescreen` | Kapının yasasıyla ÖN eleme — canlıya dokunmadan aday ölçümü |
| `sieve` | Eleme muhasebesi — nelerin hangi aşamada elendiğinin defteri |
| `sermaye` | Antrenman tohumu ↔ canlı sermaye ayrımı (nakit muhasebesi) |
| `cf_backfill` | Counterfactual (karşı-olgusal) defterin tarihsel doldurulması |
| `faz5_cikis` | Faz-5 çıkış ölçümü — dakika-hassas icra kazancı (kart EXE-2026-002) |
| `hotstate` | Redis'teki sıcak (uçucu) intraday durum |
| `codelaw` | Statik kod yasaları (YASA 4 sessiz-yutma + YASA 6 okuyucusuz-yazım) |
| `shadowlaw` | Büyüklük yasası PARA-v3 + eski yasanın gölge karşılaştırması |
| `olcum_araclari` | Ön-kayıtlı ölçüm şablonlarının ortak yardımcıları |
| `arming` | Uyuyan kurulumların "silahlanma" değerlendiricisi (ölç → silahla) |
| `dagit.sh` | "Dağıt" — A1'e tek kanonik dağıtım betiği (dry-run + kapılar + bakım penceresi) |

**Adlandırma hükmü:** dosya YENİDEN ADLANDIRMA önerilmez. Adlar tarihçe taşıyor; ~5.4k test,
systemd birimleri (`meridian-*.service`), `dagit.sh` ve ROADMAP/log çapraz referansları bu adlara
bağlı. Boşluk docstring + bu envanterle kapatıldı. Operatör yine de isterse: ayrı bir göç turu
(import'lar + testler + systemd + docs birlikte) olarak planlanmalı, bu turda YAPILMADI.

---

## 4) Emekli / nöbetçi-taş envanteri (bilerek duran ölüler)

| Kalem | Durum |
|---|---|
| `meridian/run.py` | Nöbetçi taş — çalışmayı REDDEDER (`run.py:1-25`); `--replay` tohumlama yolu yaşıyor |
| `meridian/adapters/macro.py`, `news.py` | EMEKLİ (2026-07-30 temizlik turu) — güdük bırakıldı |
| `Dockerfile` + `docker-compose.yml` + `deploy.sh` + `deploy/gcp_*` | ESKİ GCP/Docker yığını — `dagit.sh` + `deploy/oracle-a1/` geçerli; README:113-140 üç ölçülü sapmayı listeler |
| `ops/supervise.sh` | Belgeli ZARARLI — kurma (`:6-20`) |
| `regime.spy_sma_gate` | Emekli düğme — mezar taşı `bounds.yaml:71-95`, pano göstergesi olarak yaşar |
| `state/goal.yaml` ölü anahtarlar | `schema_version/style/session_tz`, `one_variable_only`, `backtest_gate`, `explore_rate` — "kod okumuyor" öz-beyanlı |

---

## 5) Doğrulama — 2026-08-15 (bu ortamda: Python 3.11.15 · uv 0.8.17 · linux/cloud konteyner)

| Kapı | Sonuç |
|---|---|
| `lint-imports` (5 sözleşme) | **5 KEPT / 0 broken** (96 dosya, 573 bağımlılık) |
| `python -m compileall meridian/` | **TEMİZ** (3.11 bayt-derleme, 96 modül) |
| `python -m compileall tests/` | **1 HATA bulundu ve düzeltildi** — aşağıda |
| `uv run pytest -q` (tam paket; ~50 dk / 4 çekirdek) | **6222 test: 6093 geçti (%97,9) · 52 başarısız · 50 fikstür hatası · 27 atlandı** — sınıflandırma aşağıda |
| `uv audit` | **BU ORTAMDA KOŞULAMADI** — uv 0.8.17 `audit` alt-komutunu tanımıyor (dagit [0b] kapısı A1'deki uv'yi ister); tedarik-zinciri kapısı bir sonraki `dagit.sh` koşumuna kalır |

**Bulunan ve düzeltilen hata:** `tests/test_firsat_yuzeyleri_v200.py:342` — f-string ifadesi
içinde ters bölü (`\"`), Python 3.12+ (PEP 701) kabul eder ama `requires-python = ">=3.11"`
taahhüdündeki 3.11'de SyntaxError. Sonuç ağırdı: pytest toplamayı **kesiyordu**
("Interrupted: 1 error during collection") — 3.11'li bir ortamda TEK BİR test bile koşmuyordu.
CI yeşilse koşucusunun 3.12+ olmasındandır; beyan edilen taban kırıktı. Düzeltme: sayım
f-string dışına alındı (`n_kart` ara değişkeni) — iki sürümde de geçerli, çift `count` çağrısı da
tekilleşti. Tüm test ağacı 3.11 ile yeniden derlendi: başka vaka YOK.

**Test paketi sonucu ve sınıflandırma (tam koşum, bu ortam):** 6222 test denendi — **6093 geçti,
52 başarısız, 50 fikstür (setup) hatası, 27 atlandı**. Düşenlerin tamamı üç ortam-bağımlı kümede
toplanıyor; **kod kusuru kanıtı yok** (bu turun tek gerçek kod kusuru yukarıdaki f-string idi,
düzeltildi):

1. **Canlı-state bağımlı aileler** (büyük çoğunluk): taze klonda `state/` yalnız goal+bounds
   taşır — `skills_registry.json`, hipotez/işlem defterleri, koşum damgaları yok. Düşen aileler:
   `test_navigator_retirement_gate_v126` ("canlı kayıt defteri okunamadı: bundled ≠ registry"),
   `test_skill_cleanup_v121`, `test_llm_advisor_v6`, `test_hafta3b_v125` (boş defterde `assert
   0 > 0` sınıfı), `test_hafta3a_v119`, `test_score_rebuild_v115`, `test_para_yasasi_v127`,
   `test_golge_planli_kol_v217`, `test_execution_fidelity_v75`, `test_cf_backfill_v14`,
   `test_audit_fixes`, `test_bottleneck_v12`.
2. **Hermes ikilisi yok:** `test_mutation_v61` fikstürü temel durumu `parity:brain_availability`
   kırmızısıyla KİRLİ bulup dürüstçe durdu ("kirli temelde her mutasyon yakalandı görünür") —
   lokal hermes-agent bu konteynerde kurulu değil.
3. **Ağ semantiği:** `test_kadans_ag_kapisi_v177` dış adresin bağlantı DENENMEDEN adli istisnayla
   düşmesini bekler; bu ortamın zorunlu HTTPS proxy'si o varsayımı değiştiriyor.

Bu tablo CLAUDE.md kural 6'nın ("tam suite yalnız Rol-1'de tek-otoriter") mekanik gerekçesidir:
paket canlı-benzeri state + lokal hermes + doğrudan ağ varsayar; taze klon/CI bu üçünü de taşımaz.

**CI gerçeği (2026-08-15 ölçümü):** `.github/workflows/ci.yml` 15 dakikalık `timeout-minutes`
taşır; paket 4 çekirdekte ~50 dk. Sonuç: **bugüne dek hiçbir CI koşusu paketi bitirememiş** —
son koşuların tümü ~15. dakikada `cancelled` (koşu listesi ölçüldü), main'deki tek `failure`
(4ad7684, 2026-08-14) pytest'e hiç ulaşmamış bir altyapı arızası (`actions/checkout` indirme 429).
İyileştirme adayı (bu turda YAPILMADI, operatör kararı): CI'ı state-bağımsız hızlı duman
alt-kümesine indirmek ya da zaman sınırını gerçekçi yapmak.

---

## 6) Diyagram güncellemesi (workflow-diagram.html, 2026-08-15)

Öğrenme kulvarı iki sıraya çıkarıldı ve gerçek boru hattı işlendi: **Arka Plan Süzgeci (28a)** ve
**Guard — Tek Kapı** düğümleri eklendi (eskiden beyin zinciri doğrudan olasılıksal kapıya
atlıyordu); beyin zinciri iç akışına **virgin-knob determinist yedek** düğümü eklendi (§2-48
kusur notuyla). Sayfanın kendi iki "sabit-veri çürümesi" dersine uyuldu: silahlı kadro listesi
düğüm etiketinden de kaldırıldı (yürürlük: `strategy.ARMED_SETUPS`), süzgeç davranışı dağıtım
durumu sabitlenmeden **sürümle** etiketlendi (v246 imha · v247+ yeniden yazım; yürürlük için
ROADMAP WP3-A durum notu). Duman testi: başsız Chromium render — 19 düğüm, 4 sıra, 0 konum
hatası, JS sözdizimi temiz.
