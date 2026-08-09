# DEVİR TATBİKATI — 2026-08-09

**Yazan:** bağlamsız devralan ajan (oturum hafızası yok; girdi = deponun kendi devir sözleşmesi
`CLAUDE.md` → `MERIDIAN_ENGINEERING_LOG.md`, artı salt-okunur canlı erişim).
**Okuyucu (YASA 6):** Rol-1 (fark hükmü için) + bir sonraki devralan mühendis.
**Ölçüm penceresi:** 2026-08-09 01:20–02:10 UTC, A1 canlı (`ubuntu@130.61.126.87`), salt-okunur.
**Sınır beyanı:** git komutu koşulmadı, dağıtım yapılmadı, `serve.sh` koşulmadı, broker'a emir
gönderilmedi/iptal edilmedi, `meridian/` ve `tests/` altında hiçbir dosyaya dokunulmadı, tam suite
koşulmadı. Canlıya dosya yazılmadı; ölçüm betikleri yerelde yazılıp `ssh … python -` ile stdin'den
beslendi. Bu belge deponun içinde yazılan TEK dosyadır.

---

## 1. SİSTEM HARİTASI

### 1.1 Ne koşuyor (canlı ölçüm)

Tek makine, tek uygulama süreci. `systemctl list-units` (2026-08-09 01:21 UTC):

| Birim | Durum | Ne yapar |
|---|---|---|
| `meridian.service` | **active** (start 01:19:32 UTC) | uvicorn `meridian.api:app` @127.0.0.1:8080 — worker AYRI SÜREÇ DEĞİL, kadans bu sürecin içinde thread |
| `meridian-barsarchive.service` | **active** | Redis `mrd:bars:*` → `state/bars_intraday` arşivcisi |
| `meridian-litestream.service` | **active** | `state/meridian.db` sürekli çoğaltma → `/home/ubuntu/replica` (8,4 MB) |
| `meridian-tick-watchdog.timer` | **active/waiting** (15 dk) | `scheduler_status.updated` >45 dk bayatsa `systemctl restart meridian` |
| `meridian-backup.timer` | **active/waiting** (23:30 UTC) | `backup_to` + `tar --exclude=state/sprint` → `/home/ubuntu/backups` |
| `meridian-fail-notify.service` | oneshot, `OnFailure` zincirinde | kanal yoksa NO-OP (bkz. Risk #4) |

**Giriş noktası:** `meridian/api.py:109` (`app = FastAPI(..., lifespan=_lifespan)`) → `api.py:105`
`_autostart()` → `api.py:349-399` altı kolu başlatır: scheduler thread (`scheduler.py:1300`),
hermes standby thread (`hermes_runtime.py:476`), Alpaca `trade_updates` WS (`mirror_stream`),
piyasa-verisi WS (`marketstream`), barfeed + intraday tüketicisi.
`run.worker()` **EMEKLİ** — çağrılırsa reddeder (`meridian/run.py:344-369`).

**Birim ortamı** (`/etc/systemd/system/meridian.service`, canlıdan okundu):
`MERIDIAN_BROKER=alpaca_paper` · `MERIDIAN_AUTOSTART_CYCLE=1` · `CYCLE_POLL_SECONDS=300` ·
`MERIDIAN_AUTOSTART_HERMES=1` · `MERIDIAN_BIND_HOST=127.0.0.1` · sır kanalı
`EnvironmentFile=-/opt/meridian/.dash.env`. Sertleştirme birimin İÇİNDE (drop-in değil).

**Kadanslar** — poll 300 sn, zaman tabanı UTC (`scheduler.py:29-30`):

- **Her poll:** `watchdog.beat("scheduler_poll")` (`scheduler.py:815`), `_intraday_gap_check`
  (`scheduler.py:818`), bar tazeleme denemesi (`scheduler.py:877-954`; merdiven
  `DENSE_ATTEMPTS=8` → `SPARSE_BASE_S=1800` → `SPARSE_MAX_S=3600`, `scheduler.py:181-183`).
- **Seans başına bir kez:** onarım geçidi (`scheduler.py:886`), **öğrenme kadansı** 4 adımlı
  (`scheduler.py:1112-1119`, `LEARN_STEPS` `scheduler.py:418`), Y4 toplama (`scheduler.py:1128`),
  SPY çapraz-doğrulama (`scheduler.py:1165`).
- **Haftalık:** kazanç takvimi, `arming.evaluate`, `selfreview.weekly`, yetim-hipotez süpürmesi,
  `nous_eval`, doğrulama üçlüsü (`scheduler.py:1142-1154`), `skill_evolve.weekly_draft`.
- **Gece (22:00–06:00 YEREL saat):** `sprint.maybe_start` (`scheduler.py:1246`,
  `sprint.SPRINT_HOURS=(22,6)` `sprint.py:320`).
- **Fazlar:** P1_REGIME (`loop.py:1199`) → P2_SCREEN (`loop.py:1258`) → P3_PLAN (`loop.py:1333`)
  → P4_EXECUTE (`loop.py:1072`) → P5_LEARN (`loop.py:1659`). **P6 diye bir faz repoda yok.**

### 1.2 Para nereden akıyor

**İki motor, ikisi de kâğıt — ama biri gerçek hesaba yazıyor.**

| | Nerede | Ağ | Rolü |
|---|---|---|---|
| İç simülatör `PaperBroker` | `meridian/broker.py:337` | yok (`broker.py:8-9`) | **Defterin TEK gerçeği**: PnL, öğrenme, karne |
| Alpaca paper aynası | `meridian/adapters/alpaca.py` | gerçek HTTPS | Kararların `paper-api.alpaca.markets` hesabına yansıması |

**Giriş zinciri:**
`scheduler._run` (`scheduler.py:1281`) → `advance_once` (`scheduler.py:804`, HALT kapısı `:827-829`)
→ `loop.daily_cycle` → iç motor `b.fill_entry` (`loop.py:1096` → `broker.py:375`) **ve** ayna
`loop.mirror_submit_armed` (`loop.py:1584`) → `alpaca.submit_plan` (`loop.py:555` → `alpaca.py:516`)
→ `alpaca.submit_bracket` (`alpaca.py:289`) → `httpx.post {paper}/v2/orders` (`alpaca.py:326`).

**Broker'a yazan altı uç** (hepsi `_paper_base()` hostname kilidi arkasında, `alpaca.py:189-233`):
`submit_bracket` (`:289`) · `submit_protective_oco` (`:639`) · `cancel_order` (`:345`) ·
`replace_order_stop` (`:572`, yalnız yukarı) · `close_engine_position` (`:398`) ·
`close_all` (`:703`, jeton `CLOSE_ALL_CONFIRM="FLATTEN-PAPER"` `:56`).

**Gerçek para yolu kodda YOK.** `alpaca.live_client()` (`alpaca.py:176-179`) tanımlı ama tüm
depoda **çağıranı yok**; emir yazan altı fonksiyonun hepsi `_paper_base()` kullanır. Canlıya geçiş
üç bağımsız elle kilit ister: `MERIDIAN_MODE=live` + `MERIDIAN_I_ACCEPT_RISK=true`
(`config.py:17-28`), `goal.yaml limits.autonomy_level ≥ 1` (`guard.py:273-274`), ve pano bu iki
env'i asla yazamaz (`secrets.py:25-27`).

**Kill-switch'ler:**

| Mekanizma | Tanım | Tetik | Durdurduğu | Canlı durum |
|---|---|---|---|---|
| `state/HALT` | `health.py:13-19` | **yalnız MANUEL** (`api.py:4828`) — otomatik yol YOK | scheduler turu, iç dolum, ayna gönderimi, dolmamış girişlerin iptali | dosya YOK, `halted:false` |
| `state/LEARN_HALT` | `health.py:25-30` | manuel | yeni strateji sürümü ship'i (işlem sürer) | dosya YOK |
| Günlük kayıp kesici | `health.py:293-295`, eşik `max_daily_loss_pct:3.0` | **otomatik** | tüm silahlı planlar + ayna girişleri (`loop.py:1080`, `:312-313`) | `breaker_tripped:false` |
| Veri kalitesi kapısı | `loop.py:1000-1022` | otomatik (bozuk ticker >%25) | dolum + plan üretimi | `data_ok:true` |
| De-risk rampası | `broker.derisk_mult` `:213-224`, `max_positions_at` `:227-236` | otomatik (tepe-DD %3→kıs, %8→sıfır) | boyut ve eşzamanlı pozisyon sayısı | DD %0,7 → çarpan 1,0 |
| Gap vetosu (E1) | `broker.GAP_VETO` `:90` | `goal.yaml gap_behavior` | — | **KAPALI** (`marketable_limit`) |
| Kazanç karartması | `earnings.py:13,587` → `loop.py:1393` | otomatik | plan NO_GO | **fail-open** (takvimsiz sembolde geçirgen, `loop.py:1394-1401`) |
| Panic/flatten | `alpaca.close_all` `:703` | manuel + jeton | her şey (operatörün kendi pozisyonları dahil) | — |

**Sert risk kapıları** (`guard.py`, kaynak `state/goal.yaml limits`): `max_open_positions:5` ·
`max_position_r:1.0` · `max_sector_exposure_pct:40` · `heat_hard_r:5.0` (NO_GO) ·
`heat_review_r:3.5` (REVIEW) · `corr_review:0.85` · R:R tabanı 2.0 (`guard.py:281`).
Boyutlama: `RISK_PCT_PER_R=0.01` (`broker.py:16`), notional tavanı %25 (`broker.py:20`),
ADV tavanı %2 + doğrusal etki (`broker.py:18-19`) — **ADV kapısı yalnız iç motorda; aynada yok**
(`alpaca.py:534-536`).

### 1.3 Hangi defterler neyi tutuyor

**İki arka uç, tek yüzey.** Uygulama HER ZAMAN `meridian/store.py` üzerinden gider; `store`
adı görüp arka ucu seçer (`storage.active()` `storage.py:354-373`). **DB'ye giden yalnız altı ad**
(`storage.py:70-75`): `trades.jsonl` · `trade_plans.jsonl` · `scoreboard.json` · `portfolio.json` ·
`equity_curve.json` · `shadow_books.json`. Diğer ~90 defter dosyadır.

Canlıda ölçüldü: `storage.active() = True`; `state/meridian.db` tabloları
`trades`(96) · `trade_plans`(409) · `scoreboard`(1) · `portfolio`(1) · `equity_curve`(882) ·
`shadow_books`(1) + litestream tabloları.

Kritik defterler ve sahipleri:

| Defter | Ne tutar | Yazan | Okuyan |
|---|---|---|---|
| `trades.jsonl` (96) | kapanmış işlemler, r_multiple, exit_reason | `loop.py:1821`, `run.py:198` | analytics, score, rollback, shadow_model |
| `trade_plans.jsonl` (409) | günlük planlar, gate_verdict, broker_status | `loop.py:618/1556`, `hermes.py:2955` | analytics, api, counterfactual |
| `portfolio.json` (DB) | **canlı kitap**: cash, positions, armed, peak_equity, entry_law, sermaye_resetleri | `run.py:108`, `loop.py:454/728/747` | watchdog, faz5_cikis, api |
| `events.jsonl` (13,4 MB) | tüm `obs.log/warn` | `obs.py:71` — TEK yazar | watchdog, selfreview, notify, api |
| `entry_execution.jsonl` (9 satır) | E2 icra defteri: yasa, limit, `fill_vs_*_bps`, motor | `loop.py:43` | `analytics.py:3839` → pano |
| `counterfactuals.jsonl` (4,0 MB) | karşı-olgu plan sonuçları | `counterfactual.py:243` | arming, shadow_model, selfreview |
| `hypotheses.jsonl` (51) | hipotez defteri | `memory.py:68` — TEK yazar | reflect, rollback, probgate |
| `scheduler_status.json` | last_tick/last_processed | `scheduler.py:34` | api + **VM'de** `tick_watchdog.sh:68` |
| `sprint_runs.jsonl` | sprint arama koşusu | `sprint_run.py:160` — **kum havuzuna** yazar | `sprint._sandbox_runs` `sprint.py:133-158` |

**Git-izli iki konfig** (`.gitignore` istisnası): `state/goal.yaml` (operatörün değişmez zarfı) +
`state/bounds.yaml` (Hermes'in kum havuzu). **Canlı ile depo BİREBİR** (sha256 doğrulandı,
bkz. §1.4).

**Yedekleme dört halka:** `storage.backup_to` (yalnız 6 DB defteri) · litestream (yalnız DB,
**aynı fiziksel disk**) · gecelik tar 23:30 UTC (`--exclude=state/sprint`) · Mac pull 21:40.
Son tar: `state-2026-08-08.tar.gz` 59.846.989 B, `Result=success`, `ExecMainStatus=0`.
**DB dışı ~90 defterin RPO'su hâlâ 24 saat**; litestream o boşluğu kapatmaz.

### 1.4 Canlı ↔ depo ayrıklığı: YOK (ölçüldü)

- `meridian/**/*.py`: yerel 96 dosya / canlı 96 dosya, **içerik-farklı = 0**, sadece-bir-tarafta = 0
  (sha256 kıyası).
- `state/goal.yaml` `099590de…7043` ve `state/bounds.yaml` `3e810b54…3515` — canlı = yerel BİREBİR.

Yani "canlı eski kodda mı" sorusunun bugünkü cevabı **hayır**. Bu, geçmişte tekrarlayan bir arıza
sınıfıydı (ENGINEERING_LOG'da üç ayrı vaka) ve şu an temiz.

**İkinci ölçüm (~30 dk sonra), yan bulguyla:** tatbikat sürerken paralel bir oturum aktifti ve
`meridian/` altında 10 dosyanın **mtime'ı** değişti (`watchdog.py`, `api.py`, `scheduler.py`, …)
— ama sha256 kıyası yine **0 fark** verdi. Yani mtime git trafiğini ölçtü, sızıntıyı değil.
Bu, CLAUDE.md §8'in "izli dosyada mtime sızıntıyı değil git trafiğini ölçer" dersinin
(2026-08-02 bekçi yanlış-alarmı) canlı bir tekrarı: **teşhiste mtime'a değil içerik-hash'ine
bak.** Devralan için pratik sonuç: bu belgedeki tüm canlı sayılar 2026-08-09 01:20–02:10 UTC
penceresine aittir ve depo o sırada hareketliydi.

### 1.5 Paranın anlık fotoğrafı (2026-08-09 ~01:35 UTC, salt-okunur)

| | İç defter (gerçek kabul edilen) | Alpaca paper aynası |
|---|---|---|
| Özsermaye | 99.303,11 | 99.744,88 |
| Açık pozisyon | 4 | **5** (+NVDA 1, motor-dışı) |
| Açık emir | — | **0** |
| Gerçekleşmiş PnL | −450,38 | — |
| Açık risk | 3,97R ≈ 3.170 $ | stop yok → sınırsız |

| sym | iç qty | ayna qty | iç giriş | ayna ort. | iç stop | ayna stop |
|---|---|---|---|---|---|---|
| NUE | 54 | 25 | 273,65 | 273,95 | 257,4033 | **YOK** |
| EMR | 64 | 37 | 163,95 | 164,76 | 152,4839 | **YOK** |
| BKNG | 43 | 22 | 207,55 | 210,24 | 191,5372 | **YOK** |
| AMGN | 33 | 22 | 414,59 | 415,01 | 389,4209 | **YOK** |
| NVDA | — | 1 | — | 208,12 | — | **YOK** (operatörün) |

**Sermaye tabanı 2026-08-01'de resetlendi** (`portfolio.sermaye_resetleri`): cash 94.457,91 →
100.000, realized_pnl −5.542,09 → 0, `tohum_islem_n:95`, `canli_islem_n:0`. Yani bugünkü
96 kapalı işlemin **95'i replay tohumu, 1'i gerçek canlı** (T00096 / ALL, −450,38 $, stop).

---

## 2. İLK 10 RİSK (şiddet sıralı)

### RİSK 1 — 🔴 **Beş açık pozisyonun broker'da HİÇ koruması yok; "kapandı" denen kusuru sistemin KENDİ düzeltmesi yeniden üretti**

**Ne.** Şu an Alpaca paper hesabında 5 açık pozisyon ve **0 açık emir** var. Dört motor pozisyonu
(AMGN/BKNG/EMR/NUE, ~26.429 $ notional) + operatörün NVDA'sı (224 $) çıplak. İç defter ise
kendini korunmuş sanıyor: `trail_stop` değerleri yerinde ve iç motor barlardan stop çıkışı
simüle edecek.

**Neden tehlikeli.** ROADMAP §WP-S bu kalemi **"✅ KAPANDI — koruma ölmüyor (E1-v2, v209-v211,
canlıda doğrulandı)"** diye kaydediyor (ROADMAP:174-180). Ölçüm bunun aksini söylüyor. Zincir:

1. `broker.py:45-57` — 08-06 vakası: bracket `tif=day` yüzünden koruma bacakları her akşam ölüyordu.
   Düzeltme: `ENTRY_TIF="gtc"` (`broker.py:82`), `ENTRY_TIF_ALLOWED=("gtc",)` (`broker.py:88`),
   ve bayat-tetik temizliği **broker'dan alınıp motorun günlük `cancel_open_entries()` kadansına
   taşındı** (ROADMAP:177).
2. Operatör 2026-08-07 16:23'te panodan korumaları yeniden kurdu — 4/4 OCO, `tif=gtc`
   (olay `koruma_oco_gonderildi`, coid `P-KORUMA-20260807-1623-{AMGN,BKNG,EMR,NUE}`).
3. **Aynı gün 20:32:39-40'ta dördü de İPTAL EDİLDİ.** Fail: `mirror_stale_entries_cancelled`,
   `gate:"gunluk_kadans"`, `cancelled:4, kept:0, foreign:0` — ve olayın kendi metni
   *"Koruma bacakları YAŞAR (dolmuş parent `kept` altında)"* diyor. `kept:0` bunun yanlış
   olduğunu kanıtlıyor.

**Kök neden (kod).** `alpaca.cancel_open_entries()` (`adapters/alpaca.py:354-381`) sahipliği
`ENGINE_COID_PREFIX="P-"` ile, terminalliği ise **emrin KENDİ `filled_qty`si** ile ölçüyor:

```python
if filled <= 0 and st in ("new", "accepted", "pending_new", "held"):
    res = cancel_order(o.get("id"))
```

`koruma_kur`un ürettiği bağımsız koruma OCO'su `koruma_coid()` (`alpaca.py:625-636`) gereği
**`P-` önekini taşır** (A2/A3 sahiplik kanıtı — bilinçli) ve doğası gereği **dolmamıştır**. Yani
iki koşulu da sağlar → iptal edilir; OCO kardeşi de onunla birlikte düşer. Fonksiyonun docstring'i
"koruma bacaklarına ASLA dokunmaz" diyor; uyguladığı test ise "bu emir dolmuş mu", "bu emir bir
pozisyonu koruyor mu" değil. `loop.py:276-278`'in *"DAY'in körlemesine yaptığı işin yalnız DOĞRU
YARISINI yapar"* beyanı ölçümle yanlışlandı — aynı işi yapıyor, sadece motorun eliyle.

**Kanıt.** `alpaca.orders(status="all")` çıktısı: `P-KORUMA-20260807-1623-NUE` submit
2026-08-07T16:23:42, `canceled_at` 2026-08-07T20:32:39 (dördü de aynı saniye kümesinde);
`alpaca.orders(status="open")` = 0; `alpaca.positions()` = 5; olay defterinde
`mirror_stale_entries_cancelled` (2026-08-07T20:32:40, cancelled=4/kept=0).

**İlk adım.** `cancel_open_entries`in terminallik ölçütünü emirden POZİSYONA taşı: iptal
adayı yalnız "aynı sembolde açık pozisyon YOKKEN duran, `P-` önekli, dolmamış GİRİŞ emri" olsun;
`P-KORUMA-` öneki ayrı bir sınıf olarak muaf tutulsun (ya da koruma OCO'su ayrı bir önek taşısın —
`is_engine_order` yine geçsin diye önek `P-` altında bir alt-ad, örn. `P-K-`). Aynı turda
`kept:0` gibi bir sonuç "koruma bacakları yaşadı" iddiasıyla ÇELİŞTİĞİNDE alarm üreten bir çivi
gerekir. Kısa vadede (Pazartesi 13:30 UTC açılışından önce) korumaların elle yeniden kurulması
operatör kararıdır — **ama düzeltme inmeden kurulan koruma bir sonraki EOD'de yine silinir.**

---

### RİSK 2 — 🔴 **Korumasız-pozisyon alarmı 2 gündür sev-1 bağırıyor ve hiçbir yere ulaşmıyor**

**Ne.** `watchdog.check_koruma_and_alarm` doğru çalışıyor: olay defterinde
`MIRROR_DRIFT KORUMASIZ POZİSYON … (4/4 motor pozisyonu korumasız)` sev-1 alarmları
**2026-08-07: 12 · 2026-08-08: 12 · 2026-08-09 (kısmi gün): 4** kez basıldı. Ama teslim kanalı yok:
`TELEGRAM_BOT_TOKEN`+`CHAT_ID` ve `MERIDIAN_WEBHOOK_URL` boş (fail-notify journal'ı her koşuda
`kanal yapilandirildi mi: False` yazıyor). Pano yalnız SSH tünelinden görülüyor.

**Neden tehlikeli.** Sistemin en pahalı riski, kendi kendine doğru teşhis edilmiş, doğru
şiddetle etiketlenmiş ve **hiçbir insana ulaşmamış**. ROADMAP N1 bunu zaten sayıyor
("33 teslim edilmemiş alarm birikmiş") ve `NAKED_POSITION` jetonunu ayırmış — ama jeton ayrımı
kanal boşken teslimat üretmez. Yani Risk 1, kurumsal olarak "kimsenin görmediği şey" sınıfında.

**Kanıt.** `events.jsonl` gün bazında sev-1 sayımı (yukarıda) · `journalctl -u meridian-fail-notify`
(Aug 7 14:16 / 16:20 / 17:33, Aug 8 22:15, Aug 9 01:19 — hepsi NO-OP).

**İlk adım.** Kanal operatör kalemi ve tek parça; ondan bağımsız olarak yapılabilecek şey:
korumasız-pozisyon hâli `/healthz` yanıtına (ya da ayrı bir `/api/riskz` ucuna) **makine-okunur**
düşsün ki dışarıdan bir uptime-probe'u bile yakalayabilsin. Bugün `/healthz` yalnız
`{"status":"ok","halted":false,…}` dönüyor ve dört çıplak pozisyonla da "ok" diyor.

---

### RİSK 3 — 🔴 **`systemctl restart` her seferinde "FAILED" sayılıyor — arıza sinyali duyarsızlaştı**

**Ne.** `meridian.service` SIGTERM'de 143 ile çıkıyor; birimde `SuccessExitStatus` yok →
systemd her temiz restart'ı `Failed with result 'exit-code'` olarak işaretliyor ve
`OnFailure=meridian-fail-notify.service` ateşliyor.

**Neden tehlikeli.** Birim dosyasının kendi yorumu (`meridian.service:16-18`) *"Temiz
`systemctl stop` bunu TETİKLEMEZ — operatörün durdurması bir arıza değildir"* diyor; ölçüm
tersini gösteriyor. Kanal kurulduğu gün her dağıtım operatöre "MERIDIAN A1: FAILED" bildirimi
gönderecek. Gerçek çöküşle rutin restart aynı sinyali üretirse sinyalin bilgi değeri sıfırdır —
ve bu, Risk 2'nin kanalı kurulunca doğrudan onun üstüne binen bir kusur.

**Kanıt.** `journalctl -u meridian`: `Aug 08 22:15:44 … Main process exited, code=exited,
status=143/n/a` + `Failed with result 'exit-code'`; aynı saniyede fail-notify
`Starting … Finished`. `NRestarts=0` (yani bunlar Restart=always döngüsü değil, elle restart).

**İlk adım.** Birime `SuccessExitStatus=143` ekle **ya da** uygulama SIGTERM'i yakalayıp 0 ile
çıksın; sonra bir kez elle test-ateşleme ile doğrula (deponun kendi doktrini: "kurulu ≠ çalışır").

---

### RİSK 4 — 🟠 **Öğrenme sprinti 2 gündür ölü ve panoda "koşuyor" görünüyor; hiçbir dedektör bakmıyor**

**Ne.** `state/sprint_status.json`: `pid 96924`, `sid 20260807-111642`, `phase "baseline"`,
`progress 281/527`, `updated 2026-08-07T14:15:30`. **pid 96924 diye bir süreç yok**
(`/proc/96924` yok; `ps` boş). Ölüm anı 14:15:30, `meridian.service` restart'ı 14:16:02 —
çocuğu cgroup kesti (ENGINEERING_LOG'un 2026-08-03'te "sıradaki tur adayı: sprint-çocuğu
yetim/ölüm dedektörü" diye yazdığı vaka, aynen tekrarladı).

**Neden tehlikeli.** (a) 281 seanslık iş çöpe gitti ve kimse bilmiyor; (b) durum dosyası donuk
kaldığı için pano %53 ilerleme çizer; (c) `sprint_cadence` bekçi eşiği **9 gün**
(`watchdog.py:58`), yani watchdog ~2026-08-11'e kadar susacak; (d) yeniden tetik kapısı
`should_run` (`sprint.py:391-424`) `gecen_gun`u **ölü sprintin başlama anından** sayıyor →
`tetik_yok(gun=1<7, taze=0<5)`; ikinci tetik olan "taze hipotez ≥5" ise imkânsız (aşağıda).

**Kanıt.** Canlı ölçüm: `sprint.status()` → `{'active': False, 'pid': 96924, 'phase': 'baseline',
'progress': 281, 'total': 527}`; `sprint.should_run()` → `sebep: 'tetik_yok(gun=1<7, taze=0<5)'`.
Skip sebep dağılımı (son ~9.800 olay): `saat_dilimi_disinda` 997 · `mesgul:canli_arama` 704 ·
`zaten_kosuyor` 257 · `tetik_yok(*)` 309. `sprint_runs.jsonl` canlı `state/`te YOK.

**İlk adım.** `status()` zaten `alive`ı ölçüyor — eksik olan, **ölü pid + terminal-olmayan faz**
kombinasyonunu bir OLAY olarak yazmak (`sprint_child_orphaned`, `sid`+`progress` ile) ve o hâlde
`started_at`ı tetik hesabından düşürmek (ölü koşu "1 gün önce koştu" saymamalı).

---

### RİSK 5 — 🟠 **Hipotez üretimi 7 gündür sıfır: öğrenme döngüsü LLM kotasına rehin**

**Ne.** `state/hypotheses.jsonl` **2026-08-02T10:36'dan beri 51 satırda donuk**. `taze = 0`
olduğu için sprintin ikinci tetiği de hiç ateşlenemiyor (Risk 4'ün ikinci ayağı).
`hermes_status.reflections: 0`. `brain_cooldown.json`: `agent` → `fallback_empty:review`,
**streak 17**; `gemini` → `rate_limit`. Kanıt dolgusu tavanı `gece_tavani: 0`, gerekçe
*"ajan havuzu soğumada (451.9 sn) → tavan 0"*; kuyrukta 405 görüşsüz plan var.
Gölge modeli `n_live: 1` vs `promote_min_n: 30` → hiç terfi edemez.
`agent_call_cooldown` son 6 günde 1.105 olay.

**Neden tehlikeli.** Hedef sözleşmesinin 2. maddesi "öğrenme katmanı operatörsüz döner" diyor;
ölçülen hâl, katmanın dış kotaya rehin olduğu ve **rehin olduğunu hiçbir üst-düzey göstergenin
söylemediği**. `hypotheses_shipped: 0/51` — sistem kurulduğundan beri tek bir hipotez ship
etmemiş. WP-N'in "darboğaz kanıt üretim hızı" teşhisi doğru ama darboğazın bir bacağı da bu.

**Kanıt.** `/api/public/summary` → `hypotheses_total:51, hypotheses_shipped:0`;
`hypotheses.jsonl` mtime 2026-08-02 10:36:19; `/api/diagnostics.ogrenme.dolgu_kuyrugu`.

**İlk adım.** "Öğrenme akıyor mu" için tek bir türev gösterge: son 7 günde yeni hipotez sayısı +
dolgulanan görüş sayısı; ikisi de 0 ise `learning_stalled` (sev-2). Bugün bu bilgi üç ayrı kartta
dağınık ve hiçbiri "durdu" demiyor.

---

### RİSK 6 — 🟠 **E2 icra defteri kendi varsayımını ölçüyor (iç motor bacağı totolojik)**

**Ne.** `entry_execution.jsonl`'in iç-motor satırlarında `fill_vs_resmi_acilis_bps` = 5,007 /
5,012 / 5,022 / 5,037 / 5,104 (ort **5,037**). Bu tesadüf değil: `broker.py:443`
`base_fill = next_open * (1.0 + self.slip)` ve `goal.yaml slippage_bps: 5`. Yani ölçülen sayı
girdi sabitinin kendisidir.

**Neden tehlikeli.** `/api/diagnostics.icra.slipaj` bu iki bacağı yan yana raporluyor ve ayna
bacağının `fill_vs_limit_bps` ortalaması −271 bps için otomatik yorum basıyor:
*"belirgin NEGATİF → yasa para bıraktı, tavan gevşetilebilir (kart grid'inin ölçüm girdisi)"*.
Bu yorumun dayandığı örneklem **n=4**; ve E1 tavanı 2026-08-03'te zaten `limit_atr_mult:100.0`
ile fiilen bağlamaz hâle getirilmiş durumda. `goal.yaml pessimistic_band_v2.ampirik_bps` hâlâ
`null`/`n=0` — yani gerçek maliyet bandı henüz hiç ölçülmedi ama karar yüzeyi "gevşet" diyor.
İlk gerçek canlı işlem (ALL, 2026-08-07) tam da gevşek zarftan girip aynı gün −1,03R stop oldu.

**Kanıt.** `entry_execution.jsonl` 9 satırın tamamı (yukarıdaki bps değerleri);
`/api/diagnostics.icra.slipaj.ic_motor` ve `.ayna`; `broker.py:443`; `state/goal.yaml:53-55,63-89`.

**İlk adım.** İç-motor bacağının `fill_vs_resmi_acilis_bps` alanını ya `None` + beyan yaz
("model sabiti, ölçüm değil"), ya da özet katmanında ayrı isimle sun. Karar yüzeyine yalnız
AYNA (gerçek dolum) satırları girsin ve n<20 iken yorum cümlesi basılmasın.

---

### RİSK 7 — 🟠 **İç defter ile ayna aynı pozisyonda %49 farklı boyut taşıyor**

**Ne.** İç 54/64/43/33'e karşı ayna 25/37/22/22 (§1.5). ROADMAP bunu ölçmüş ve
**operatör kalemi** olarak açık bırakmış (*"ayna hedef riskin ~%49'unu taşıyor; taban yerinde
olsaydı 51/76/45/45 giderdi"*, ROADMAP:207-209).

**Neden tehlikeli.** Öğrenme, karne ve tüm edge hükümleri İÇ defterden besleniyor; gerçek hesapta
olan başka bir şey. İkisi ayrıştığı sürece "sistem şunu kazandırdı" cümlesi hangi kitaptan
söylendiğine bağlı olur. Ayrıca aynada ADV/likidite kapısı hiç yok (`alpaca.py:534-536` vs
`broker.py:448-456`) — bugün ayna daha KÜÇÜK olduğu için zarar görünmüyor, ama işaret ters
döndüğünde koruyan bir sınır da yok.

**Kanıt.** §1.5 tablosu (canlı `portfolio.positions` vs `alpaca.positions()`).

**İlk adım.** Karar değil ama ucuz: ayrışmayı tek sayı olarak sürekli ölç
(`Σ ayna_qty·r_per_share ÷ Σ iç_risk`) ve panoya payda-beyanlı bas. ROADMAP'teki SB-1 "boyut
makbuzu" kalemi zaten bunun doğru biçimi.

---

### RİSK 8 — 🟠 **Karne 96 işlem gösteriyor; gerçek canlı işlem sayısı 1**

**Ne.** `/api/public/summary` → `closed_trades: 96, score: -0.0089` ve setup×rejim matrisi
(`breakout_vcp` n=33/55/3 …). Oysa `portfolio.sermaye_resetleri` kaydı: 2026-08-01 resetinde
`tohum_islem_n: 95, canli_islem_n: 0`. O tarihten sonra tek bir işlem kapandı (T00096/ALL,
−450,38 $). Yani gerçek canlı gerçekleşmiş PnL = **−450,38 $, n=1**.

**Neden tehlikeli.** Bu uç halka açık (`/api/public/summary`, landing sayfası bu uca bağlı).
Tohum/canlı ayrımı `portfolio.json` içinde dürüstçe duruyor ama **özet uca taşınmıyor** —
"belgenin/arayüzün yanlış anlattığı şey" sınıfının en pahalı örneği, çünkü dışarıya bakan yüzey.
Aynı sınıftan ikinci örnek: matris hücrelerindeki `mean_r` değerleri de tohum-ağırlıklı.

**Kanıt.** `curl /api/public/summary` çıktısı; `portfolio.sermaye_resetleri` (yukarıda);
`portfolio.realized_pnl = -450.38`; `trades` tablosunda son satır T00096.

**İlk adım.** Özet uca iki alan ekle: `closed_trades_live` ve `closed_trades_seed` (payda beyanı),
ve `score`un hangi kümeden hesaplandığını alan olarak yaz.

---

### RİSK 9 — 🟡 **Sessiz bozulan üretim kontrolleri: `lxml` yok, FMP 402, Finviz kapalı**

**Ne.** Üç bağımsız kalem, üçü de "arıza" değil "bilinmiyor"a düşüyor:
- `/api/diagnostics.universe_drift` → `status: "unknown", reason: "ImportError: Import lxml
  failed"`. Evren bayatlığı denetimi canlıda **hiç koşmuyor** (payda yine 251 basıyor).
- `integrity.production.starved` → `fmp_source`: *"anahtar var ama üretmiyor — 402 Payment
  Required"*. FMP bilgi katmanının tamamı (temel/float, kazanç, insider, haber) ölü. Sonucu
  rejim kartında görünüyor: `risk.regime.source = "index-derived (SPY); FMP breadth/sector feeds
  inactive until key present"` — maruziyet bütçesi %60 tek kaynaktan türetiliyor.
- `finviz_unavailable` son 6 günde **1.490 olay**: *"evren yalnız REPLAY_UNIVERSE ile kuruldu —
  Finviz keşfi bu tur devre dışı"*. Yani evren keşfi statik.

**Neden tehlikeli.** Üçü de dürüstçe beyan ediliyor (uydurma yok — bu iyi), ama üçü birlikte
"sistem tam kapasite çalışıyor" izlenimini bozmadan kapasiteyi düşürüyor. Özellikle `lxml`
eksikliği bir **kurulum kusuru**: kod var, bağımlılık yok, kontrol sessizce `unknown`.

**Kanıt.** `/api/diagnostics` → `universe_drift`, `integrity.production.starved`, `risk.regime`;
`events.jsonl` sayımı.

**İlk adım.** `lxml`i canlı ortama ekle (tek bağımlılık, tek dağıtım kalemi) — sonra
`universe_drift`in `unknown` dönmesi **kendi başına** bir alarm olsun; "ölçemedim" ile
"sapma yok" bugün aynı renkte görünüyor.

---

### RİSK 10 — 🟡 **Kayıp-güncelleme penceresi: E2 defteri kilitsiz oku-değiştir-yaz**

**Ne.** `store.append_jsonl`in dosya dalı **kilit almıyor** (`store.py:365-376`: düz
`open(path,"a")`); 29 çağıran bu yoldan geçiyor (`obs.py:71` events, `loop.py:43` E2,
`counterfactual.py:243`, `memory.py:68` …). Daha keskini: `_entry_exec_trim`
(`loop.py:77-84`) ve E2 dolum yaması (`loop.py:1863-1892`) `read_jsonl` → `write_jsonl` arasında
dış `file_lock` tutmuyor; 1892'deki yorum *"atomik (mkstemp + os.replace)"* diyor —
**atomiklik kayıp-güncellemeyi önlemez**, iddia yanıltıcı.

**Neden tehlikeli.** Aynı anda çalışan bir CLI (`sprint`, `recompute`, `barrepair`, elle bir
ölçüm betiği) ile worker'ın çakışması sessiz satır kaybı üretir; ve bu tam da CLAUDE.md §5'in
"canlı worker koşarken state'e yazma" kuralının kâğıt üzerinde kaldığı yer — kural insana
söyleniyor, koda değil. Bugün E2 defteri 9 satır olduğu için kayıp görünmez; defter büyüdükçe
ve N2/N4 turları cf'yi yeniden koştukça pencere gerçek olur.

**Kanıt.** `store.py:365-376`, `loop.py:77-84`, `loop.py:1863-1892`; `store.write_text`
(`store.py:306-333`) üretimde **0 çağıranlı** — docstring'inin taşınacak dediği yollar
(`memory.py:212` lessons.md, `run.py:172`, `config.py:307`, `auth.py:88` sabit tmp adı) hâlâ
elle yazıyor.

**İlk adım.** En dar ve en değerli tek yama: E2'nin iki oku-değiştir-yaz bloğunu
`file_lock(ENTRY_LEDGER)` içine al. `append_jsonl`in tamamını kilitlemek ayrı bir tur
(performans etkisi ölçülmeli), ama `loop.py:1892`'deki yanıltıcı yorum aynı turda düzeltilmeli.

---

**Onuncunun altında kalan, kayda değer kalemler** (sıralamaya girmedi, kaybolmasın diye):
`conservation.ok = false / unexplained = 14` (kökü ölçülmüş: `dormant_setup` yolu 31 plan/0 işlem,
`docs/KORUNUM-KOK-2026-08-07.md`; operatör kararı bekliyor) · `INTRADAY_ARM` dosyası canlıda VAR
ama Faz-4b silahlama bacağı yazılmamış — son 6 günde 855 `intraday_arm_flag_on_but_4b_not_built`
uyarısı · `goal.yaml limits.no_trade_before_bars: 3` canlı yolda **okuyucusuz** (yalnız
`backtest.py:151`; `guard.py:25` sadece anahtar listesinde) — kapı sözü veren ama davranışı
olmayan ikinci konfig (`backtest_gate` zaten dosyanın kendi beyanında böyle) · cf sadakati:
skor havuzunun %96'sı, 6 çıkış mekanizması ve 5 friksiyon kalemi modellenmeden
(`pipeline.cf_fidelity`, WP-N N4) · `state/` 498 MB'ın 217 MB'ı `state/sprint` (disk %10, acil
değil) · `equity_curve.json` 149 saat bayat (`integrity.coherence.stale`).

---

## 3. DEVİR NOTLARI

### 3.1 Nereden başlamalı

1. **Önce canlıyı ölç, sonra belgeyi oku.** Deponun devir sözleşmesi seni
   `MERIDIAN_ENGINEERING_LOG.md`'ye gönderiyor; o dosya **2026-08-03'te donmuş** (6 gün).
   Gerçek "şu an ne var" fotoğrafı üç yerde: `/api/diagnostics` (29 kart, hepsi payda-beyanlı),
   `state/heartbeat.json`, ve broker'ın kendisi. İlk 20 dakikanı şu üç komuta ayır:
   `systemctl list-units | grep meridian` · `curl -H "x-meridian-token: …" …/api/diagnostics` ·
   `alpaca.positions()` + `alpaca.orders(status="open")`.
2. **Kitap ile broker'ı yan yana koy.** Bu sistemin merkezî ayrımı "iç defter (gerçek kabul
   edilen) vs Alpaca aynası (gerçekten olan)". Bu iki tarafı karşılaştırmayan hiçbir ölçüm
   güvenilir değil — Risk 1 ve Risk 7 tam bu boşlukta yaşıyor ve ikisi de yalnız
   yan-yana-koyunca görünüyor.
3. **Sonra ROADMAP §3'ün WP tablosuna geç** (§1 "ŞİMDİ" bloğu 2026-07-31'de donmuş, atla).
   Aktif program WP-N (kanıt-hızı) ve WP-S (sermaye/koruma); bu belgedeki Risk 1 doğrudan
   WP-S'in "kapandı" işaretli kaleminin üstüne düşüyor.

### 3.2 Hangi belge güncel, hangisi bayat

| Belge | mtime | Hüküm |
|---|---|---|
| `docs/RUNBOOK.md` | 2026-08-09 03:09 | **GÜNCEL** — üretilmiş yüzey (`ops/runbook_uret.py`), mesaj şablonları satır numarasıyla; en iyi arama alanı |
| `ROADMAP.md` §3 (WP tablosu) + §7 (karar günlüğü) | 2026-08-09 02:20 | **GÜNCEL** — ama §7'nin en yeni girdisi 2026-08-03; 08-05…08-09 işleri §3'ün WP bloklarına yazılmış, günlüğe değil (iki yerde arama gerekiyor) |
| `ROADMAP.md` §1 "ŞİMDİ" | — | **BAYAT** (2026-07-31 başlıklı, 9 gün) |
| `MERIDIAN_ENGINEERING_LOG.md` | 2026-08-03 19:29 | **BAYAT** — ve giriş noktası olduğu için en tehlikeli bayatlık; "AÇIK KALANLAR" listesi 6 günlük |
| `docs/KORUNUM-KOK-…`, `BAYAT-SERMAYE-KOK-…` (08-07) | 08-07 | **GÜNCEL ve iyi** — kök-neden belgelerinin çürütülen hipotezleri de yazma alışkanlığı, devralan için en faydalı desen |
| `docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md`, `ARTEFAKT-TARAMASI-2026-08-07.md` | 08-09 / 08-08 | **GÜNCEL** — en yeni denetim turları |
| `README.md`, `CLAUDE.md` | 08-02 | sözleşme metni, hâlâ geçerli |
| `research/cards/*.yaml` (26 kart) | — | ölçüm hükümlerinin tek kaynağı; `research/cards/README` ile birlikte okunur |

**Belgenin yanlış anlattığı üç yer (ölçümle):** (a) ROADMAP WP-S "koruma ölmüyor ✅ KAPANDI" —
ölmüş durumda (Risk 1); (b) `meridian.service:16-18` "temiz stop OnFailure tetiklemez" — tetikliyor
(Risk 3); (c) `loop.py:1892` "atomik" yorumu kayıp-güncelleme koruması ima ediyor — etmiyor
(Risk 10). Üçü de aynı sınıf: **bir mekanizmanın niyeti yorumda, davranışı kodda, ve ikisi
ayrışmış.**

### 3.3 Tuzaklar — beni en çok yavaşlatan üç şey

1. **Yerel `state/` kopyası bir zaman fotoğrafı, gerçek değil.** `/Users/erdemozturk/AI-Trading/state/`
   içindeki `heartbeat.json` `equity: 94457.91` / `open_positions: 0` / ts `2026-07-30` diyor;
   canlı 99.303,11 / 4 pozisyon / 2026-08-09. Yerelde `meridian.db` hiç yok, yani `storage.active()`
   yerelde `False` ve altı defter tamamen farklı bir yoldan okunuyor. Depodaki state'e bakıp
   "sistem şunu yapıyor" demek doğrudan yanlış cevap üretir — bu tatbikatta paralel çalışan bir
   ölçüm kolu tam bu tuzağa düştü. **Kural: state hakkında her cümle A1'den ölçülür.**
2. **"Kapandı" işaretli kalemler kapalı olmayabilir.** Depo çok disiplinli bir kayıt tutuyor ve
   bu güven yaratıyor; ama Risk 1'de gördüğüm gibi bir düzeltmenin *kendi ikame mekanizması*
   aynı arızayı yeniden üretebiliyor ve kayıt "✅" kalıyor. Kapanış iddialarını **son durumdan**
   doğrula, kapanış commit'inden değil. En hızlı yol: iddianın ürettiği ARTEFAKTI ölç
   (burada: broker'da açık emir var mı), olay defterindeki "düzeltme indi" satırını değil.
3. **Aynı olgu üç ayrı isimle üç ayrı yerde yaşıyor.** Korumasız pozisyon: `events.jsonl`de
   `MIRROR_DRIFT KORUMASIZ POZİSYON` (sev-1) + `korumasiz_motor_disi_pozisyon` (warn) +
   `/api/diagnostics.reconcile.hwm_pairs` (`desync: false` diyor!) + `sessiz_hat` ("bekçiler
   17/17 · kilitler 3/3 · sağlıklı"). Dört yüzeyin ikisi alarm veriyor, ikisi "iyi" diyor.
   Hangi yüzeyin neyi ölçtüğünü öğrenmek, olguyu bulmaktan uzun sürdü. Devralan için kısayol:
   `docs/RUNBOOK.md`'de olay adını ara — mesaj şablonu + üreten `dosya:satır` orada yazılı.

### 3.4 Erişim ve ölçüm deseni (çalıştığı doğrulanmış)

```
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87
# kurulum: /opt/meridian ; venv: ./.venv/bin/python ; sır: .env (broker) + .dash.env (pano token)
# ölçüm: betiği YERELDE yaz, stdin'den besle — canlıya dosya YAZMA
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && ./.venv/bin/python -' < betik.py
# pano/API (yalnız 127.0.0.1): set -a; . /opt/meridian/.dash.env; set +a
#   curl -H "x-meridian-token: $MERIDIAN_DASH_TOKEN" http://127.0.0.1:8080/api/diagnostics
```

`~/Documents/OCI/…` altındaki anahtar macOS gizlilik korumasına takılır — `~/.ssh/oci-a1.key`
kullanılır (`dagit.sh:16` kanonu).

---

## 4. ÖLÇÜLEMEDİ (dürüst boşluklar)

- **`P-KORUMA-*` emirlerini iptal eden kod yolunun İZLEME KAYDI.** `_cancel_mirror_entries`
  (`loop.py:258-262`) olaya yalnız **sayıyı** yazıyor
  (`cancelled=len(res.get("cancelled") or [])`), listeyi değil. Yani "iptal edilen 4 emir tam
  olarak o dört koruma bacağıydı" cümlesi bir **çıkarım**; dayanakları: (a) `cancelled=4`,
  `kept=0`, `foreign=0` @20:32:40 ile dört `P-KORUMA-20260807-1623-*` emrinin `canceled_at`
  damgası (20:32:39-40) saniye düzeyinde örtüşüyor; (b) o anda broker'da açık BAŞKA motor emri
  yoktu — Aug-6 giriş emirleri `filled`, `portfolio.alpaca_submitted` yalnız dört
  `P-2026-08-05-*` planını taşıyor ve emir geçmişinde 08-07'de gönderilmiş yeni bir alım emri
  yok; (c) `cancel_open_entries` süzgeci (`alpaca.py:373`) bu emirleri **kapsıyor**
  (P- önekli + `filled_qty=0` + `new`/`held`). Üç bacak birlikte iddiayı taşıyor ama tek satırlık
  bir izleme kaydı yerine geçmez — kesinleştirmek için `cancelled[]` içeriği olaya yazılmalı.
  (Doğrulandı: `systemctl show meridian -p SuccessExitStatus` → **boş**, yani Risk 3'ün
  "temiz restart FAILED sayılıyor" iddiası ölçülmüş hâldedir, çıkarım değil.)
- **İç defter ↔ ayna boyut farkının (%49) kök nedeni.** ROADMAP "taban yerinde olsaydı
  51/76/45/45" diyor; ben yalnız farkı doğruladım, üreten hesabı ayrıştırmadım.
- **Neden Alpaca aynası 2026-08-05'te, iç motor 2026-08-06'da doldu** (aynı planlar, farklı gün
  ve fiyat). İki icra modelinin yapısal farkı olabilir; ölçmedim.
- **Tam test suite durumu.** Tek-otoriter kural gereği koşmadım; son bilinen referans
  ENGINEERING_LOG'da 4133/0 @ `4dbe688` (2026-08-03) — 6 gün ve çok sayıda commit öncesi.
- **`sprint_runs.jsonl`in kum havuzlarındaki son durumu** — canlı `state/`te yok olduğunu
  ölçtüm, sandbox içlerini taramadım.
- **Pano UI'ının bu hâlleri nasıl çizdiği.** Yalnız API katmanını ölçtüm; `app.js`in bu JSON'ları
  nasıl render ettiğini (özellikle donuk `sprint_status` ve `reconcile.desync:false`) görmedim.
