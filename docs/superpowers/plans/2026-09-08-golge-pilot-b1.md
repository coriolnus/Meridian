# EDG-2026-088 — B1 uygulama planı (uyuyan kurulum planlarının GÖLGE İCRA pilotu; GERÇEK EMİR YOK)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** `meridian/golge_icra.py` (gölge defteri + motor: dormant plan → giriş (ilk uygun bar açılışı) → çıkış (CANLI çıkış
fonksiyonu) → R) + worker kadansı + `meridian/api.py` okuyucusu + `research/olcumler/edg088_golge_pilot/sayim.py`.
Sermaye riski YOK; canlı davranış DEĞİŞMEZ.
**Kart (SPEC, bağlayıcı):** `research/cards/EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml` — ölçüm planı, eşikler
(n≥30 · CI-alt>0 · kazanma≥0,40 · pencere ≤120 gün · |gölge−gerçek| ≤0,05R), kill-list, üç PK.
**Selef:** `research/cards/EDG-2026-049-uyuyan-kurulum-karsi-olgu.yaml` (NO-GO; n=6, 6/6 kayıp, −4,725R) ·
`research/olcumler/edg049_dormant_2026-08-23/olcum.py` (eşlenik ay-kümeli bootstrap, B=5000, seed=20260812, birim=AY).
**Plan emsali:** `docs/superpowers/plans/2026-09-07-pano-sohbet-b1.md` · `docs/superpowers/plans/2026-09-08-pano-sohbet-b3.md` (sayım task biçimi).
**Kod emsalleri (ÖLÇÜLDÜ):** `meridian/shadow_lifecycle.py::step` (gölge yaşam-döngüsü: OPEN(D) bekleyen çıkış+fill →
INTRADAY(D) scale_out+dokunuş → CLOSE(D) `strategy.manage_position`+arm; "YASALAR ÇAĞRILIR, KOPYALANMAZ") ·
`meridian/shadow_lifecycle.py::run_cycle` (loop kancası) · `tests/test_golge_v2_yasam_dongusu_v132.py` (çivi deseni) ·
`meridian/store.py::append_jsonl` · `meridian/codelaw.py::artifact_graph` / `HUMAN_INVOKED_SINKS` ·
`meridian/analytics.py::shadow_variant_summary` (pano devri emsali).

## Ölçülen mevcut durum (varsayım değil)
- **Uyuyan plan doğumu:** `meridian/loop.py::daily_cycle` P2 bloğu — `strategy.scan_all` sinyallerinden
  `setup ∉ strategy.ARMED_SETUPS` olanlar `dormant_setup: True` damgasıyla aday olur; plan kimliği
  `P-<tarih>-<ticker>-<setup>`. Uyuyan küme `meridian/arming.py::_dormant_setups` (motor demeti eksi `ARMED_SETUPS`).
  Kapı hükmü `meridian/guard.py::classify_gate` (`dormant_setup` OKUNMAZ). Uyuyan plan yalnız `loop.girise_uygun`
  üzerinden keşif havuzuna girer.
- **Plan defteri:** `state/trade_plans.jsonl`; sözleşme `meridian/ledgers.py::CONTRACTS["trade_plans.jsonl"]`
  (`required`: id·date·ticker·setup·score·entry_trigger·stop·gate_verdict·strategy_version; ayrıca
  `targets`/`profit_target`/`size_r`/`r_multiple_expected`/`regime_at_plan`/`sector`/`dormant_setup`). İcra girdileri
  (`atr`/`ref_price`/`pivot`) plan sözlüğünde DEĞİL, `meta["entry_law"]` yan tablosundadır ve yalnız
  silahlı+REVIEW planlar için tutulur. Defter `store.merge_dated_jsonl` ile `cap=500` kırpılır.
- **Canlı çıkış motoru:** `meridian/strategy.py::manage_position` — kendi docstring'i "replay'in ve canlı döngünün
  PAYLAŞTIĞI tek çıkış-karar yüzeyi" der; `ManageDecision(exit_now, exit_reason, trail_stop)`; dallar
  `early_kill_pivot` · `giveback` · `time_stop` (`exit.time_stop_days`, vars. 15) · `regime_flip`. Fiyat-dokunuşu
  çıkışları (sert stop / hedef) `meridian/broker.py::PaperBroker._touch_exit`, kısmi satış `PaperBroker.scale_out`.
- **Bar / PIT:** günlük barlar `state/bars/*.csv` (260 sembol), yükleyici `meridian/dataset.py::load` / `load_live`;
  canlı turda `per`/`idx` ZATEN bellekte. Parquet arşivin okuma yüzeyi `ops/bar_sorgu.py` (DuckDB), yazıcısı
  `ops/bar_arsivle.py`. **İçerik hash'i BUGÜN YOK:** `meridian/watchdog.py::determinism_report` +
  `state/bars_fingerprint.json` yalnız DOSYA BOYUTU tutar → `kaynak_bar_hash` yeni tanımlanacak (Rol-1 kalemi 2).
- **Yasa 6:** `meridian/codelaw.py::artifact_graph` "okuyucu"yu YALNIZ `meridian/` içindeki BAŞKA bir modülde arar
  (`external_readers`); `research/` altındaki sayım betiği okuyucu SAYILMAZ. Emsal:
  `codelaw.HUMAN_INVOKED_SINKS["shadow_trades.jsonl"]` (beyanlı + devir şartı yazılı).
- **Kadans:** `meridian/scheduler.py::advance_once` 300 sn poll, kapanan her XNYS seansı için `loop.daily_cycle`
  EN ÇOK BİR KEZ. Doğru kanca yeri: `loop.daily_cycle` içindeki "2.4 GÖLGE-VARYANT PORTFÖYLERİ" bloğu (P3
  `pipeline_run` açıklığının DIŞI, kendi try/except'i). Ek ağ/LLM çağrısı SIFIR — `per`/`idx` zaten elde.
- **Pano:** "Uyuyan kurulumlar" KARTI YOK (ölçüldü). Bugün var olanlar: plan çekmecesinde tek satır
  (`ui/src/pano/yuzeyler/kuyruk/OnayCekmecesi.tsx`, etiket "Uyuyan kurulum") ve
  `meridian/watchdog.py::conservation_report`'un `uyuyan_kurulum`/`uyuyan_olculemedi` sayaçları →
  `/api/diagnostics`. Gölge paneli emsali `ui/src/pano/yuzeyler/ogrenme/Golge.tsx`.
- **Test numaraları:** `ls tests | grep -o 'v[0-9]*' | sort -V | tail -1` → **v454**. Bu plan v455/v456/v457 alır.

## Global Constraints (kart kill-list'i BİREBİR + repo yasaları)
- **GERÇEK EMİR YOK — SIFIR TOLERANS.** Gölge defteri hiçbir gerçek emir / plan onayı / silahlanma üretemez.
  Yasak yüzeyler (ölçüldü): `meridian/adapters/alpaca.py` `submit_plan` · `submit_bracket` · `submit_protective_oco` ·
  `cancel_order` · `cancel_open_entries` · `close_engine_position` · `close_all` · `replace_order_stop`;
  `meridian/loop.py` `mirror_submit_armed` · `mirror_submit_ve_kalicilastir` · `operator_onay_ver` · `operator_ret_ver`;
  canlı `state/portfolio.json` / `trades.jsonl` / `trade_plans.jsonl` / `approvals.jsonl` yazımı. Çivi 1 bu kümeyi
  patlayıcı sahtelerle kapatır.
- **Dormant ÜRETİMİNE DOKUNULMAZ.** `arming._dormant_setups`, `strategy.scan_all`, `guard.classify_gate`,
  `loop.girise_uygun` ve `loop.daily_cycle`'ın plan doğum bloğu DEĞİŞMEZ; `loop.py`de tek değişiklik yeni bloğun
  ÇAĞRISIDIR (satır ekleme dahil hiçbir mantık düzenlemesi yok).
- **Çıkış kuralı AYNI FONKSİYONDAN.** `strategy.manage_position` İTHAL EDİLİR ve ÇAĞRILIR; ikinci bir uygulama,
  eşik kopyası ya da `exit.*` anahtarının yerel yorumu YAZILMAZ (kaynak taraması çivisi).
- **PIT bar — SIFIR TOLERANS** (`pitlaw`, tarihsel yeniden yürütme dünyası). Her satır `kaynak_bar_hash` taşır;
  hash tüketilen barların İÇERİĞİNDEN türer. Bar eksikse `kaynak_bar_hash: None` + `olculemedi` nedeni ve satır
  K'ye SAYILMAZ (uydurma yasağı: 0 ile "bilmiyorum" aynı şey değildir).
- **Motor KAPI YÜZEYİ DEĞİLDİR.** `golge_icra` GO/REVIEW/NO_GO DÖNDÜRMEZ — plandaki `gate_verdict`i tüketir.
  Böylece `pitlaw.KAPI_SOZLESMELERI` / `SINYAL_SOZLESMELERI` kaydına girmez; çivi bunu kaynak taramasıyla mühürler
  (kayıtsız kapı yüzeyi doğarsa `pitlaw` çivisi zaten öter).
- **Eşik/pencere/n DONUK.** n_alt=30 · ci_alt_R_ust=0,0 · kazanma_alt=0,40 · pencere_gun_ust=120 ·
  golge_gercek_fark_R_ust=0,05 kodda SABİT ve kart kimliğiyle etiketli (`KART = "EDG-2026-088"`); env/parametre ile
  gevşetilemez (emsal: `meridian/faz5_cikis.py` kart sabitleri bloğu). n<30 ile hüküm yazılmaz.
- **Okuyucu ŞART (Yasa 6).** Yeni her artefakt için `meridian/` içinde DIŞ okuyucu: `meridian/api.py` →
  `golge_icra.ozet()`. `research/.../sayim.py` Yasa 6'yı KARŞILAMAZ (`artifact_graph` root="meridian").
- **Hüküm sayacı bedeli raporlar** (bedel yasası): satır/gün, defter baytı, ek ağ/LLM çağrısı = 0 (çivili).
- Yasa 4 (işaretli+gerekçeli `except`), çapa yasağı (`mod.ad` SEMBOL çapası; satır çapası YOK), `-q` verilmez,
  ajan koşumları SERİ, git yok, `meridian/` dokunulduğu için TAM SUITE Rol-1'de, pytest dışı koşum yok
  (`sandbox_state`'li çivi).

---

### Task 1 — `meridian/golge_icra.py` (gölge defteri + motor) — implementer
**Files:** Create `meridian/golge_icra.py` · Test `tests/test_golge_icra_v455.py`
(numara `ls tests | grep -o 'v[0-9]*' | sort -V | tail -1` ile doğrulanır; **v454 alınmış**).

**Interfaces (Produces):**
- `KART = "EDG-2026-088"` · `DEFTER = "golge_icra.jsonl"` (kapanan gölge işlemler) ·
  `ACIK = "golge_icra_acik.json"` (açık gölge pozisyonlar + `son_seans`).
- `N_ALT = 30` · `CI_ALT_R = 0.0` · `KAZANMA_ALT = 0.40` · `PENCERE_GUN = 120` · `FARK_R_UST = 0.05` (kart sabitleri).
- `adim(dstr: str, *, planlar: list[dict], bars_of, regime_ok: bool, params: dict, simdi=None) -> dict`
  — BİR seans. Faz sırası `shadow_lifecycle.step`ten alınır ve kaynağı ADIYLA yazılır (ileri-dönüklük yok):
  OPEN(D) bekleyen çıkışlar + giriş (planın giriş kuralı = İLK UYGUN BAR AÇILIŞI) → INTRADAY(D) dokunuş çıkışı
  (`broker.PaperBroker._touch_exit` yasası) → CLOSE(D) `strategy.manage_position`. İDEMPOTENT: aynı `dstr` ikinci
  kez çağrılırsa hiçbir satır yazılmaz.
- `bar_hash(kesitler) -> str | None` — tüketilen (ticker, tarih, o/h/l/c/v) satırlarının sha256'sı; eksik bar → None.
- `kayit_al(n: int | None = None) -> list[dict]` · `acik_kayit() -> dict` (okuyucular).
- `ozet(gun: int = PENCERE_GUN) -> dict` — pano/api yüzeyi: `{n, n_acik, hukum_dagilimi, kurulum_kirilimi, toplam_r,
  kazanma_orani, pf, pencere: {baslangic, gun, doldu}, bedel: {satir_gun, bayt, ag_cagri: 0, llm_cagri: 0},
  olculemeyen: [...]}` — **hiçbir eşik hükmü DÖNDÜRMEZ** (hüküm sayım betiği + Rol-1).
- Defter satırı (kart ölçüm planının alan kümesi + beyanlı ekler):
  `{ts, plan_id, ticker, kurulum, hukum, kol, ts_plan, giris_ts, giris_fiyat, stop, hedef, cikis_ts, cikis_fiyat,
   cikis_neden, R, bar_n, kaynak_bar_hash, strategy_version, olculemedi?}`
  — `kol ∈ {"dormant","kontrol"}`; `hukum` = plandaki `gate_verdict` (GO/REVIEW/NO_GO — hepsi girer);
  `ts` GERÇEK yazım anı, `ts_plan` plan tarihi (retro-damga yasağı, `shadow_lifecycle._trade_rows` emsali).

- [ ] **Çivi 1 (kırmızı) — KILL#1 SIFIR EMİR:** Global Constraints'teki yasak yüzeylerin TAMAMI patlayan sahtelerle
      değiştirilir; 5 sentetik planla tam bir gölge pencere koşar → hiçbiri çağrılmaz. Ayrıca `sandbox_state` altında
      YAZILAN dosya adları kümesi TAM olarak `{golge_icra.jsonl, golge_icra_acik.json}` (+ obs defteri).
- [ ] **Çivi 2 — KILL#3 AYNI FONKSİYON:** `strategy.manage_position` casus ile sarılır → açık pozisyon başına seansta
      TAM BİR kez çağrılır ve casusun döndürdüğü `exit_reason` satırdaki `cikis_neden`e BİREBİR düşer. Kaynak
      taraması: `golge_icra.py` gövdesinde `exit.time_stop_days` / `exit.trail_atr_mult` / `exit.giveback_pct`
      dizgeleri YOK (ikinci uygulama yasağı).
- [ ] **Çivi 3 — KILL#2 ÜRETİME DOKUNMAMA:** `golge_icra` modülü `arming`i ithal ETMEZ; `trade_plans.jsonl` /
      `candidates.jsonl` / `approvals.jsonl` adlarına hiçbir yazma çağrısı yok (`codelaw.artifact_graph` yazar
      kümesi çivisi).
- [ ] **Çivi 4 — PK (1) SENTETİK (5 plan, el hesabı):** bilinen fiyat yolları — (a) sert stop, (b) hedef,
      (c) `time_stop`, (d) `regime_flip`, (e) tetik hiç gelmedi → `cikis_neden="giris_yok"`, `R=None`
      (0 DEĞİL) + neden. Beş R el hesabıyla BİREBİR; toplam R çeyrek kuruşuna kadar eşit.
- [ ] **Çivi 5 — İLERİ-DÖNÜKLÜK YOK:** plan D kapanışında doğar, giriş D+1 AÇILIŞINDA olur; çıkış barından SONRAKİ
      barları değiştirmek sonucu DEĞİŞTİRMEZ; D'nin kapanışı girişte kullanılmaz.
- [ ] **Çivi 6 — PIT / `kaynak_bar_hash`:** aynı barlar → aynı hash; tek bir OHLCV hanesi değişince hash değişir;
      tüketilmeyen bir sembolün barı hash'i DEĞİŞTİRMEZ; bar eksikse `kaynak_bar_hash=None` + `olculemedi` ve satır
      `ozet`in K paydasına GİRMEZ.
- [ ] **Çivi 7 — ALAN KÜMESİ:** yazılan satırın anahtar kümesi kartın `olcum_plani` alanlarını KAPSAR; eksik alan
      testi kırar (kart ↔ kod tek-kaynak çivisi).
- [ ] **Çivi 8 — İKİ KOL:** aynı seansta hem dormant hem normal plan verildiğinde satırlar `kol` alanıyla ayrışır;
      `ozet` iki kolu ayrı sayar (PK (2)'nin paydası).
- [ ] **Çivi 9 — İDEMPOTENS:** `adim` aynı `dstr` ile iki kez → ikinci koşuda 0 yeni satır, `son_seans` değişmez.
- [ ] Uygulama (minimal, TDD) · [ ] **mutasyon ≥4:** (a) `manage_position` yerine yerel kopya → Çivi 2 ısırır ·
      (b) motorun içinden `alpaca.submit_plan` çağır → Çivi 1 ısırır · (c) girişi D kapanışına al → Çivi 4/5 ısırır ·
      (d) `bar_hash`i sabite bağla → Çivi 6 ısırır · (e) bir alanı düşür → Çivi 7 ısırır · [ ] rapor

---

### Task 2 — worker kadansı + `/api` okuyucusu + codelaw — implementer (Task 1 sonrası, aynı ajan)
**Files:** Modify `meridian/loop.py` (TEK ekleme: "2.4 GÖLGE-VARYANT PORTFÖYLERİ" bloğunun yanına, P3 `pipeline_run`
açıklığının DIŞINDA, kendi `try/except` + `obs.warn("golge_icra_failed", ...)` ile `golge_icra.adim(...)` çağrısı;
girdiler `dstr`, o turun `plans`ı, `lambda t: per[t]`, `regime_ok`, `eff`) · Modify `meridian/api.py`
(`GET /api/golge-icra` → `golge_icra.ozet()`, `_auth` zorunlu; ayrıca özet `/api/diagnostics`in öğrenme/mlops
bloğuna eklenir ki pano kartının EVİ olsun) · Test `tests/test_golge_icra_kadans_v456.py`.

**Interfaces (Consumes):** `loop.daily_cycle`in bellekteki `per` / `idx` / `plans` / `rj["regime"]` / `regime_ok` /
`eff`; `meridian/api.py::_auth`; `meridian/codelaw.py::artifact_graph`.

- [ ] Çivi 1 (kırmızı): kadans — kapanan seans başına TAM BİR `adim`; ikinci poll aynı seansta yeni satır yazmaz.
- [ ] Çivi 2: **arıza gölgede kalır** — `golge_icra.adim` patlarsa `daily_cycle` AYNEN tamamlanır, planlar diske
      yazılır ve `golge_icra_failed` uyarısı düşer (canlı tur bloke olmaz).
- [ ] Çivi 3: **bedel SIFIR ağ/LLM** — `hermes` / `spend.record` / HTTP taşıyıcısı patlayan sahtelerle → gölge bloğu
      hiçbirine dokunmaz; `ozet()["bedel"]["ag_cagri"] == 0`.
- [ ] Çivi 4: **Yasa 6** — `codelaw.artifact_graph()`ta `golge_icra.jsonl` ve `golge_icra_acik.json` için
      `unread is False` (dış okuyucu `api.py`); `tests/test_codelaw_v59.py` YEŞİL kalır. `DECLARED_SINKS`e satır
      EKLENMEZ (beyan gerekmiyor — okuyucu gerçek).
- [ ] Çivi 5: uç — kimliksiz istek 401; boş defterde `ozet` "kanıt yok" alanlarıyla döner, sahte "her şey yolunda"
      göstermez; `pencere.doldu` False iken hiçbir eşik hükmü metni YOK.
- [ ] Çivi 6: `loop.py` diff'i TEK çağrı bloğudur — dormant üretim bloğunun yüklemleri (`setup not in
      strat.ARMED_SETUPS`, `plan["dormant_setup"]`, `girise_uygun`) baytı baytına aynı (kaynak çivisi).
- [ ] Uygulama · [ ] mutasyon ≥4 (kadans idempotensi · try/except kaldırma · auth · artifact_graph okuyucusu) · [ ] rapor

**Pano kartı:** `ui/` tarafı bu planın DIŞINDA tutulabilir (B2) ya da `ui/src/pano/yuzeyler/ogrenme/Golge.tsx`
komşusuna küçük bir "Uyuyan kurulumlar — gölge icra" kutusu olarak eklenebilir → **Rol-1 kararı gerekir (6)**.
Backend özeti her iki durumda da bu task'ta hazır olur.

---

### Task 3 — `research/olcumler/edg088_golge_pilot/sayim.py` — implementer
**Files:** Create `research/olcumler/edg088_golge_pilot/sayim.py` + `README.md` (komut satırı + alan sözlüğü) ·
Test `tests/test_edg088_sayim_v461.py` (v457 kadans çivisine gitti; v458 bayatladı — Task 3 raporu §2).
**Komut satırı:** `.venv/bin/python research/olcumler/edg088_golge_pilot/sayim.py --defter state/golge_icra.jsonl
--cikti <json> [--markdown <md>] [--baslangic <ISO>] [--pk3 <edg049 kesiti>]`
**Interfaces (Consumes):** `meridian.golge_icra` (alan sözlüğü + kart sabitleri İTHAL, kopyalanmaz) ·
`meridian.olcum_araclari.blok_bootstrap_ci` (ya da 049 reçetesi — Rol-1 kararı 1) · `state/trades.jsonl` (PK 2).
**Ölçüler (JSON):** `n`, `pencere: {ilk_ts, gun, doldu}` (n≥30 ∧ ≤120 gün), `toplam_r`, `ci: {lo, hi, yontem, blok,
B, tohum}`, `kazanma_orani`, `pf`, **tanı:** `kurulum_kirilimi`, `hukum_dagilimi` (GO/REVIEW/NO_GO),
`cikis_neden_dagilimi`, **kontrol PK (2):** `{n_cift, ort_fark_r, komisyon_kayma_payi, gecti}`,
**PK (3):** `{n: 6, kayip: 6, toplam_r, esles: bool}`, **bedel:** `{satir_gun, bayt}`, `olculemeyen: [...]`.
K=2 birincildir (`EDG-088-toplam-R-CI`, `EDG-088-kazanma-orani`); kurulum kırılımı TANIdır, K'ye çarpılmaz.

- [ ] Çivi 1 (kırmızı, **PK (1) kimlik kontrolü**): Task 1'in 5 sentetik satırı → sayaç toplam R'yi el hesabıyla
      BİREBİR verir; altıncı satır eklenince sayı değişir (mutasyon).
- [ ] Çivi 2 (**PK (2) kontrol**): sahte kontrol kolu — gölge R ile `trades.jsonl` gerçek R'si eşleştirilir;
      ort. fark ≤0,05R ∧ komisyon+kayma payı içinde → `gecti=True`; farkı 0,06R'ye itince `gecti=False` VE
      **hiçbir sayı yayılmaz** (kill#5: markdown "PK DÜŞTÜ — sayı yayılmaz" başlığıyla çıkar).
- [ ] Çivi 3 (**PK (3) selef**): EDG-049'un 6 dormant planı gölgeden geçirilir → 6/6 kayıp, toplam R ≈ −4,725
      işaretiyle uyuşur. Kaynak: `research/olcumler/edg049_dormant_2026-08-23/islemler_tam_dormant_acik.json`
      (`setup == "pullback"` süzgeci TAM 6 satır verir; plan_id/ts_open/ts_close/entry/exit/r_multiple/exit_reason/
      bars_held var, **stop/profit_target YOK** → Rol-1 kararı 3). Ayrışırsa "harness KÖR" damgası.
- [ ] Çivi 4: `pencere.doldu` False iken markdown başlığı "HÜKÜM YOK (betimleyici ara-rapor)"; n<30 ile hiçbir
      eşik cümlesi yazılmaz (049'un ikinci düşme sebebi).
- [ ] Çivi 5: `kaynak_bar_hash` None olan satır K paydasına girmez, `olculemeyen`e ADIYLA düşer.
- [ ] Çivi 6: bootstrap DONUK — tohum/B/blok kaynağı çıktıda ADIYLA yazılı; IID bootstrap REDDEDİLİR.
- [ ] Çivi 7: komut satırı `subprocess` ile bir kez `tmp_path`te koşulur (ops sözleşmesi: sözleşme KOMUT SATIRIdır);
      sayaç `state/`e YAZMAZ.
- [ ] Uygulama · [ ] **mutasyon ≥4** (PK2 eşiği · pencere kapısı · hash süzgeci · bootstrap tohumu) · [ ] rapor

---

### Task 4 — Rol-1
- [ ] merge → **tam suite** (arka planda, `-n 4`, donmuş ağaç; hüküm ÜÇLÜ: `FAILED|ERROR` boş + "N passed" + `PYTEST_EXIT=0`)
- [ ] `codelaw`/`pitlaw`/`ledgers` raporları yeşil (yeni artefaktın okuyucusu var; yeni kapı yüzeyi YOK)
- [ ] dağıtım (akşam penceresi; `git status --porcelain` boş, worker durmuş, tek kip bayrağı)
- [ ] karta `notlar`: "B1 dağıtıldı <tarih>; pencere BU TARİHTEN itibaren n≥30 ∧ ≤120 gün" + ROADMAP TSK-175 notu
- [ ] PK (2)'nin GERÇEK ayağı ilk 10 gerçek işlemde; pencere dolunca `sayim.py` koşumu → hüküm AYNI TURDA karta + K defterine
- [ ] KALIR hükmü çıkarsa: gölge defteri okuyucusuz kalmasın diye ÖZELLİK KAPATILIR (kart `basari_tanimi`, Yasa 6)

---

## Rol-1 kararı gerekir (uydurma yok — bunlar plan yazarken KAPATILAMADI)
1. **Bootstrap yöntemi.** Kart "EDG-049 ile aynı blok uzunluğu" diyor; 049'da BLOK YOK — `olcum.py` **eşlenik
   ay-kümeli** bootstrap kullanıyor (B=5000, seed=20260812, birim=AY) ve iki kollu bir Δ ölçüyor. 087 tek kollu
   toplam R ölçüyor. Seçim: (a) `meridian/olcum_araclari.blok_bootstrap_ci` (moving block, n^(1/3), tohum 11, B=2000)
   mu, (b) 049'un ay-kümelemesinin tek-kollu uyarlaması mı? **Pencere açılmadan pinlenmeli** (eşik donuk).
2. **`kaynak_bar_hash` tanımı ve PIT çapası.** İçerik hash'i bugün yok (`watchdog.determinism_report` yalnız dosya
   BOYUTU). Tüketilen OHLCV satırlarının sha256'sı mı, yoksa `ops/bar_arsivle.py` parquet arşivine
   (`ops/bar_sorgu.py` okuyucusu) bağlanma mı? PK (3) tarihsel yeniden yürütmedir → pitlaw SIFIR TOLERANS: 2023/2025/2026
   barlarının PIT çapası hangi kaynaktır?
3. **PK (3) plan yeniden kurulumu.** 049 artefaktlarında plan SATIRI yok (stop/profit_target yok), yalnız işlem
   satırı var. Seçenekler: (a) 049 şasisini yeniden koşup plan satırlarını üretmek, (b) `r_multiple`den stop'u
   TÜRETMEK (bu ölçüm değil türetmedir — beyan gerekir), (c) 6 (tarih, sembol, kurulum) üçlüsünden donmuş
   edg032c parametreleriyle `strategy.scan_all` ile planı yeniden doğurmak.
4. **n≥30 / 45 gün gerçekçi mi?** `docs/degerlendirme/UYUYAN-KURULUM-INCELEME-2026-09-07.md` §2 taze sayımı:
   **10 uyuyan plan, 2026-07-24 → 09-02 (~40 gün)** → ~1,7 plan/hafta → n=30 için ~18 hafta. Kartın
   `veri_penceresi` cümlesi ("~31 plan / ~5 hafta") 7 Ağustos'un KÜMÜLATİF sayısına dayanıyor. Eşik DONUK ve
   değiştirilemez; Rol-1 "45 günde n<30 → bilgisiz arşiv" sonucunu şimdiden kabul ediyor mu, yoksa bu bir
   ardıl kart mı?
5. **n neyi sayar?** Gölgeye GİREN plan mı, KAPANAN gölge işlem mi? Tetiği hiç gelmeyen plan (R=None) paydada mı?
   Ayrıca `trade_plans.jsonl` `cap=500` ile kırpılıyor — gölge, planı DOĞDUĞU gün yakalamalı (kırpılmış defteri
   geriye dönük okumak n'i sessizce küçültür).
6. **Pano kartı bu planda mı, B2'de mi?** "Uyuyan kurulumlar" kartı BUGÜN YOK; var olan yüzeyler plan çekmecesindeki
   tek satır ve `watchdog.conservation_report` sayaçları. Ayrıca `golge_icra_acik.json` kendi okuyucusunu mu alsın
   yoksa `ozet()` üzerinden mi okunsun?
7. **Kontrol kolunun (PK 2) kapsamı.** Normal planlar B1 dağıtımından itibaren SÜREKLİ mi gölgelenecek (defter
   hacmi ~50×), yoksa yalnız son 10 gerçek işlem BİR KEZ mi yeniden yürütülecek? Kart ikisini de okuyacak biçimde yazılmış.
8. **Kısmi satış (`scale_out`) gölgeye girsin mi?** Canlı çıkış yolu `manage_position` + `_touch_exit` + `scale_out`
   ÜÇÜDÜR. Kill#3 "aynı fonksiyon" diyor; üçünü de çağırmak sadakati artırır ama `broker.PaperBroker`a bağlanmayı
   gerektirir (gerçek-emir yüzeyine bir adım daha yakın). Kapsam kararı kill#1 ile kill#3 arasında bir denge.

---

## Rol-1 hükümleri (2026-09-08 16:5xZ) — plan taslağındaki 8 karar kalemi (kaynak: EDG-049 kartı/olcum.py, meridian/olcum_araclari, inceleme belgesi §2; hafıza: uyuyan-kurulum-yolu)
1. **Bootstrap:** `meridian/olcum_araclari.blok_bootstrap_ci` (moving block, n^(1/3), tohum 11, B=2000) — tek kollu toplam R; 049'un ay-kümesi iki-kollu Δ içindi. Kart 088 `esikler.ci_yontem` bu adı taşır (donuk).
2. **`kaynak_bar_hash`:** tüketilen OHLCV satırlarının (ticker,tarih,o,h,l,c,v) sha256'sı; canlı yolda `state/bars/*.csv` (motorun kullandığı barlar), PK (3) tarihsel yolda `ops/bar_sorgu.py` parquet arşivi; satır `bar_kaynak` alanını taşır ("state/bars" | "arsiv"). Eksik bar → None + neden, K dışı.
3. **PK (3):** seçenek (c) — 6 (tarih, sembol, kurulum) üçlüsü donmuş edg032c parametreleriyle `strategy.scan_all`dan yeniden doğurulur; doğmazsa PK (3) "ölçülemedi — harness kör" (r_multiple'dan stop TÜRETİLMEZ).
4. **Pencere:** ölçülen hız 10 plan/40 gün (~1,7/hafta) → n≥30 için ~18 hafta. EDG-087'nin 45 günü bayat hıza dayanıyordu → EDG-087 ÖLÇÜM BAŞLAMADAN arşiv (öncül yanlış), ARDIL **EDG-2026-088**: n≥30 ∧ ≤120 gün (eşik/ölçüm aynı). Bu plan 088'e bağlıdır.
5. **n:** KAPANAN gölge işlem sayısı (R ölçülmüş); tetiği gelmeyen planlar (`giris_yok`, R=None) tanı, paydada değil. Plan DOĞDUĞU seans yakalanır (loop kancası); `trade_plans.jsonl` geriye dönük okunmaz.
6. **Pano kartı:** backend özeti (`/api/golge-icra` + diagnostics bloğu) bu planda (Yasa 6 okuyucusu); UI kutusu B2 (ayrı, `Golge.tsx` komşusu). `golge_icra_acik.json` `ozet()` üzerinden okunur (ayrı okuyucu gerekmez — artifact_graph aynı okuyucuyu görür; ölçülecek, görmüyorsa api'ye açık okuma eklenir).
7. **Kontrol kolu:** yalnız GERÇEK işlemler: B1'de son 10 gerçek işlem bir kez yeniden yürütülür + her yeni gerçek işlem kapandığında gölge eşleniği bir kez (ucuz, n küçük). Tüm normal planların sürekli gölgelenmesi YOK (bedel ~50×).
8. **`scale_out`:** çıkış yolu üçlüsünden `manage_position` + `_touch_exit` çağrılır; `scale_out` yalnız `PaperBroker` durumundan bağımsız saf fonksiyonla çağrılabiliyorsa dahil (ölç); değilse BEYANLI SAPMA (kısmi satışsız R) ve PK (2) toleransı olduğu gibi kalır — düşerse dürüstçe düşer.

### Rol-1 düzeltme notu (2026-09-08 19:00Z)
Plan metnindeki `edg087` yolu, `45` gün ve `v457` sayım çivisi bayattı (Task 1/2/3 raporlarının üç kez işaretlediği kalem); kart EDG-2026-088 ile eşitlendi: yol `edg088_golge_pilot`, pencere 120 gün, sayım çivisi v461. PK (3) hükmü kartın `notlar` alanında (şasi koşumu TSK-179 alt kalemi).
