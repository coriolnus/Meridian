# MODÜL ENVANTERİ — 2026-08-15

**Okuyucu (YASA 6):** oturum açan her Claude rolü + operatör. `CLAUDE.md` kural 1'in yol arkadaşı:
mühendislik günlüğü "şu an ne var"ı anlatır, bu belge "neresi nerede ve ne iş yapar"ı. 96 modül,
~67k satır. **Tek gerçek kaynak modüllerin kendi başlık docstring'leridir** — bu belge onların
dizinidir; Görev sütunu her modülün kendi başlık satırından (kırpılmış) alınmıştır.

**2026-08-15 sonrası kural:** başlık docstring'i 'ne yapar'ı anlatır (Türkçe, detaylı); WP/tur/
kart/tarih köken etiketleri kodda DURMAZ — arşivi `docs/MODUL-KOKENLERI-2026-08-15.md`'dedir.
İstisnalar: `run.py` ve `adapters/{macro,news}.py` mezar taşlarıdır, docstring'leri kaydın kendisidir.

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
| `meridian/api.py` | 5489 | state/ üzerinde FastAPI okuma-modeli ve dar bir operatör yazma yüzeyi (HALT/DEVAM, onaylar). |
| `meridian/scheduler.py` | 1400 | süreç-içi kâğıt-ilerletme döngüsü: kapanan her XNYS seansı için loop.daily_cycle'ı |
| `meridian/loop.py` | 3309 | canlı ileri-yönlü kâğıt döngüsü: kapanan her işlem günü için bir kez koşan günlük |
| `meridian/intraday_cycle.py` | 391 | kapanmış dakikalık barların tüketicisi: sıfır-yetkili gözlem/gölge ölçümü ve |
| `meridian/run.py` | 433 | entrypoint (TOHUMLAMA + TEK ATIŞ). 24/7 KADANS BURADA DEĞİL: `scheduler.advance_once`. |

### 2. Sinyal Çekirdeği (saf karar)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/strategy.py` | 1170 | saf sinyal mantığı: yedi giriş kurulumunun değerlendirmesi ve kapalı-bar pozisyon yönetimi. |
| `meridian/score.py` | 228 | kapanmış işlem defterinden [-1, +1] aralığında bileşik performans skoru. |
| `meridian/regime.py` | 335 | endeks (SPY) barlarından piyasa rejimi sınıflaması ve günlük rejim artefaktı. |
| `meridian/indicators.py` | 352 | kapalı OHLCV barları üzerinde saf, determinist teknik gösterge kütüphanesi. |
| `meridian/earnings.py` | 787 | kazanç takvimi: karartma kapısı, PEAD çapası ve takvim tazeleme/birikim katmanı. |

### 3. Kısıt & Yasa Katmanı

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/guard.py` | 680 | parametre önerileri ve işlem planları için saf, statik kısıt katmanı. |
| `meridian/health.py` | 312 | operatörün kontrol durumu: kill-switch, nabız, bayatlık ve silahlanma kilitleri. |
| `meridian/codelaw.py` | 1097 | iki statik yasanın (sessiz-yutma, okuyucusuz-yazım) kaynak-kod denetçisi. |
| `meridian/ledgers.py` | 538 | paylaşılan defterlerin yazılı sözleşmesi: zorunlu alanlar, izinli yazarlar, anahtarlar. |
| `meridian/ledgerstamp.py` | 459 | işlem defterine kaynak damgası: canlı kanıt ile tohum simülasyonunu ayırır. |
| `meridian/provenance.py` | 242 | anahtar köken takibi: üretici↔tüketici alan ayrışmasının çalışma-anı dedektörü. |
| `meridian/integrity_registry.py` | 418 | bileşen × değişmez-desen kapsam kaydı: "nereye bakmadık?" tablosu. |
| `meridian/sieve.py` | 254 | eleme muhasebesi: her sessiz `continue`yi sayılı ve gerekçeli bir kayda çevirir. |
| `meridian/validation.py` | 415 | doğrulama üçlüsü: aday getiri defteri + DSR/PSR + PBO/CSCV ve ship hükümleri. |
| `meridian/validation_report.py` | 143 | "hangi mekanizma/edge KANITLANIYOR?" sorusunun salt-okuma tek tablosu. |
| `meridian/recompute.py` | 674 | aynı büyüklüğü iki BAĞIMSIZ yoldan hesaplayıp kıyaslayan mutabakat dedektörü. |

### 4. Öğrenme Beyni (Hermes + Kapı)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/hermes.py` | 4617 | Meridian'ın öneri üreten beyni: durum okur, TEK değişkenlik bir hipotez kurar ve |
| `meridian/hermes_runtime.py` | 562 | Hermes yansıma beyninin süreç-içi süpervizörü: bekleme döngüsü, |
| `meridian/hermes_composite.py` | 381 | bileşik (çok-düğmeli) önerilerin ölçüm kuyruğu: tek-değişken yasasını |
| `meridian/reflect.py` | 1946 | yansıma boru hattının motoru ve TEK ship kapısı: hipotez nereden gelirse gelsin |
| `meridian/probgate.py` | 458 | eşleştirilmiş olasılıksal kapı: nokta-eşik yerine blok-bootstrap ile P(ΔS>0) |
| `meridian/backtest.py` | 935 | walk-forward simülasyon motoru: öğrenme kapısının tek ölçüm zemini. |
| `meridian/oos_pipeline.py` | 83 | OOS penceresinin 70/30 Search/Confirm bölümlemesi ve teyit yürüyüşü. |
| `meridian/oos_erosion.py` | 225 | OOS aşınma defteri: aynı sınav kâğıdına kaç kez soru soruldu? |
| `meridian/memory.py` | 233 | hipotez defteri ve damıtılmış dersler: sistemi gerçekten öğrenir kılan katman. |
| `meridian/versioning.py` | 146 | strategy.yaml sürüm zinciri: bump, değişmez tarih anlık görüntüleri ve karne. |
| `meridian/rollback.py` | 462 | otomatik ebeveyn-dönüşü: kötüleşen sürüm insansız geri alınır, sonuç deftere işlenir. |
| `meridian/prescreen.py` | 539 | hipotez ön-elemesi: adayları kapının KENDİ yasasıyla ölç, canlı state'e dokunma. |
| `meridian/sprint.py` | 977 | öğrenme sprintinin KONTROL YÜZEYİ: kum havuzu kurulumu, otomatik kadans ve koşum yolu. |
| `meridian/sprint_run.py` | 224 | öğrenme sprintinin ÇOCUK SÜRECİ: kum havuzunda üç fazlı ileri-yürüyüş ölçümü. |
| `meridian/baseline.py` | 330 | ebeveyn sürümün tabanını UYDURMADAN ölçmek: backfill + like-for-like would-have kıyası. |
| `meridian/threshold_curve.py` | 216 | entry.min_score eşik eğrisi: kapıyı yükseltmek/alçaltmak kâr getirir mi? |
| `meridian/component_ic.py` | 830 | bileşen IC tablosu: bileşik skorun ham parçalarından hangisi tahmin gücü taşıyor? |
| `meridian/counterfactual.py` | 301 | karşı-olgusal defter: alınmayan her tam-şekilli adayı simüle edip kanıta çevirir. |
| `meridian/cf_backfill.py` | 230 | karşı-olgusal defteri TÜM TARİHİ SEANSLARA koşturarak dolduran tek-seferlik motor. |
| `meridian/mutation.py` | 824 | MUTASYON KOŞUMU: bütünlük dedektörlerinin NEYİ GÖREMEDİĞİNİ ölçen körlük haritası. |
| `meridian/nous_eval.py` | 863 | NOUS SİSTEM-DEĞERLENDİRME KATMANI: telemetriden kanıt-atıflı iyileştirme önerileri. |
| `meridian/regime_trigger.py` | 51 | ertelenmiş rejim-bütçe tetikleyicisi: rejim başına örneklem sayacı + "kanıt hazır" sinyali. |
| `meridian/shadowlaw.py` | 612 | BÜYÜKLÜK YASASI **PARA-v3**: kapının karar değişkeninin tanımı + ESKİ YASANIN GÖLGESİ. |
| `meridian/arming.py` | 356 | silahlanma değerlendiricisi: uyuyan→ölç→silahla döngüsünün kapı-ölçümü halkası. |
| `meridian/selfreview.py` | 409 | haftalık öz-değerlendirme sentezi + katmanlar-arası çelişki dedektörü. |
| `meridian/agent_telemetry.py` | 459 | ajan/LLM çağrılarının telemetri ve ham-iz defterleri: süre ölçüm anında |
| `meridian/spend.py` | 113 | Hermes LLM çağrılarının maliyet defteri ve aylık bütçe kapısı. |
| `meridian/olcum_araclari.py` | 796 | ölçüm şablonlarının ORTAK YARDIMCILARI: temiz taban, blok bootstrap, küçültme, damga. |
| `meridian/faz5_cikis.py` | 470 | dakika-hassas icra ÇIKIŞ ÖLÇÜMÜ: gölge dolumlarının EOD zamanlamasına karşı CI'lı kazancı. |

### 5. Gölge Katman (sıfır yetki)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/shadow_model.py` | 488 | plan özelliklerinden P(kazanç) tahmin eden, yetkisiz gölge sonuç-modeli. |
| `meridian/shadow_variants.py` | 621 | aynı günün canlı aday akışına farklı parametre kümeleriyle KÂĞIT karar uygulayan gölge-varyant karar defteri. |
| `meridian/shadow_lifecycle.py` | 554 | varyant başına kalıcı kâğıt kitap yürüten gölge yaşam-döngüsü motoru (fill → yönetim → çıkış → mark). |
| `meridian/trend_shadow.py` | 571 | hükümlü uzun-ufuk trend kolunu canlı barlar üzerinde ileri yürüten sanal gölge-kitap. |
| `meridian/intraday_shadow.py` | 827 | seans içinde tetiği kesilen planın TAM icra kararını ("emir çıkar mıydı, kaç lot, hangi fiyattan") kendi defterine ölçen gölge katmanı. |

### 6. Beceri Katmanı (Axis-2)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/skills.py` | 1085 | skill kütüphanesinin kayıt, koşu ve öneri katmanı: deterministik boru hattı koşucusu + katalog + Eksen-2 önerileri. |
| `meridian/skill_evolve.py` | 278 | ölçülmüş-zayıf skill'ler için revize SKILL.md TASLAĞI üreten, operatör-onaylı içerik-evrim döngüsü. |
| `meridian/skill_gorus.py` | 623 | skill'lerin yapılandırılmış GÖRÜŞ yazıp gerçekleşen sonuçla puanlandığı, icraya dokunmayan görüş defteri. |

### 7. İcra (paper broker)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/broker.py` | 719 | kâğıt broker: gerçekçi sürtünmeli dolum/çıkış simülatörü ve giriş-icra yasası. |
| `meridian/sermaye.py` | 643 | antrenman tohumunun (replay_seed) K/Z'sini canlı-kâğıt sermayeden ayrıştıran, kuru-koşu-varsayılanlı reset aracı. |

### 8. Bar / Akış Altyapısı

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/barfeed.py` | 146 | `mrd:barfeed` akışını consumer-group ile okuyan DAYANIKLI bar-tetiği tüketicisi. |
| `meridian/barclock.py` | 134 | intraday'in TEK ortak zaman kaynağı: kapanmış-bar admissibility + NY seans kapıları. |
| `meridian/bararchive.py` | 118 | dakikalık WS bar çerçevelerinin gün-dosyalı kalıcı disk arşivi (kanıt katmanının ilk taşı). |
| `meridian/barsarchive.py` | 781 | `mrd:bars:{T}` akışlarının DAYANIKLI disk arşivcisi (kanıt katmanının ham maddesi). |
| `meridian/barrepair.py` | 379 | diskteki bar defterlerinden HAYALET SEANS satırlarını temizleyen onarım/envanter aracı. |
| `meridian/marketstream.py` | 223 | Alpaca dakikalık KAPANMIŞ bar WS dinleyicisi: piyasa verisi → mrd:bars + sıcak fiyat. |
| `meridian/mirror_stream.py` | 345 | Alpaca trade_updates akışından beslenen olay-güdümlü YÜRÜTME-DURUMU katmanı. |
| `meridian/streamhealth.py` | 300 | WS dinleyicilerinin ORTAK YASASI: bayatlık/nabız/backoff/down-reassert/reconnect. |
| `meridian/hotstate.py` | 521 | Redis SICAK-DURUM katmanı: intraday'in ~ms hızlı-okuma ve bar-akışı ara katmanı. |
| `meridian/dataset.py` | 338 | replay evreninin ORTAK yükleyicisi + backtest pencere sabitleri. |

### 9. Veri Kenarı (adapters/)

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/adapters/data.py` | 2755 | günlük OHLCV bar hattının tek boğazı: çok kaynaklı zincir, artımlı önbellek, |
| `meridian/adapters/alpaca.py` | 1556 | Alpaca broker adaptörü: varsayılan olarak PAPER; iç broker simülatörünün |
| `meridian/adapters/massive.py` | 928 | Massive (massive.com) EOD bar sağlayıcısı: tüm piyasayı TEK çağrıda veren |
| `meridian/adapters/fmp.py` | 379 | Financial Modeling Prep (STABLE API) istemcisi: kotalı, çift-anahtarlı, |
| `meridian/adapters/finviz.py` | 339 | Finviz momentum/kırılım ekranını OTONOM ADAY KAYNAĞI yapan keşif adaptörü. |
| `meridian/adapters/insider.py` | 648 | Form 4 (içeriden işlem) verisi: FMP insider-trading akışından artımlı |
| `meridian/adapters/shortinterest.py` | 353 | FINRA Equity Short Interest: kaçınma filtresinin veri ayağı — |
| `meridian/adapters/edgar_shares.py` | 397 | EDGAR as-of dolaşımdaki hisse sayımı: salt-okunur PIT veri köprüsü. |
| `meridian/adapters/constituents.py` | 248 | point-in-time S&P 500 üyeliği: FMP birincil, Wikipedia en iyi-çaba |
| `meridian/adapters/macro.py` | 24 | EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu). |
| `meridian/adapters/news.py` | 28 | EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu). |

### 10. Kalıcılık & Yapılandırma

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/store.py` | 642 | state/ defterlerinin tek okuma-yazma kapısı: atomik yazım + file_lock + db_backed yönlendirmesi. |
| `meridian/storage.py` | 700 | altı defter varlığının SQLite arka ucu: `state/meridian.db` varlık kaydı + WAL + tek transaction. |
| `meridian/dbmigrate.py` | 614 | dosya defterlerini SQLite'a parite kanıtıyla taşıyan ve geri alan operatör aracı. |
| `meridian/config.py` | 385 | merkezi yapılandırma ve yol çözümü: goal/bounds/strategy yükleme + varsayılan tohum. |

### 11. Gözlem, Pano & Operasyon

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/obs.py` | 328 | yapılandırılmış JSON olay kaydı + bildirim zincirinin anahtarlandığı ALARM_ jetonları. |
| `meridian/watchdog.py` | 3425 | mekanizma bekçisi: periyodik dişlilerin canlılık nabzı + bütünlük/makullük rapor ailesi. |
| `meridian/analytics.py` | 4321 | panonun okuma-modeli: state/ üzerinden türetilen analitik hesapların tek çatısı. |
| `meridian/marketview.py` | 311 | izlenen evrenin tek bakışta okunan görüntüsü; pano "Piyasa" sekmesinin tek kaynağı. |
| `meridian/notify.py` | 215 | operatöre kısa mesaj itme (Telegram / genel webhook) + yerel alarm gelen kutusu; yalnız stdlib. |
| `meridian/secrets.py` | 230 | sır erişiminin tek kapısı: env → yerel 0600 deposu → Secret Manager, ya da hiçbiri (Hard Rule 5). |
| `meridian/auth.py` | 348 | operatör kimliği: scrypt parola doğrulama + HMAC-imzalı, kayan-pencereli oturum çerezi. |
| `meridian/auth_cli.py` | 106 | operatör parolasını ve oturum imza anahtarını kabuktan yöneten CLI. |
| `meridian/mcp_server.py` | 173 | Meridian'ın SALT-OKUNUR durumunu yerel hermes-agent'a MCP aracı olarak açan stdio sunucusu. |

### 0. Paket Kökleri

| Modül | Satır | Görev |
|---|---:|---|
| `meridian/__init__.py` | 5 | Meridian — kapalı-bar swing paper-trading motoru + Hermes öğrenme döngüsü. |
| `meridian/adapters/__init__.py` | 5 | meridian.adapters — dış dünya kenar katmanı (veri sağlayıcılar + Alpaca broker). |

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
