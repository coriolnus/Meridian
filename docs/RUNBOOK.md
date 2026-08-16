# Meridian · Operasyon Runbook

> **ÜRETİLMİŞ DOSYA — ELLE DÜZENLEME YAPMA.** Kaynağı koddur; elle yazılan her satır
> bir sonraki üretimde silinir. Yeniden üret: `python ops/runbook_uret.py`
> · bayat mı diye sor: `python ops/runbook_uret.py --kontrol`

Bu belgenin panodaki okuyucusu **`/runbook`** sayfasıdır (YASA 6). Pano alarm satırları
ve sessiz-hat sapmaları buradaki bölüm çapalarına (`/runbook#<ad>`) bağlanır.

## Kaynak sözleşmesi ve eşleştirme kuralı {#kaynak-sozlesmesi}

Onaylı kaynaklar (WP0 §6.3, operatör onayı) — bunların DIŞINDA hiçbir yerden içerik alınmaz:

- `ops/*.sh` ve `deploy/oracle-a1/*.sh` **başlık yorumları** (shebang'dan sonraki ilk `#` bloğu)
- `MERIDIAN_ENGINEERING_LOG.md` → “AÇIK KALANLAR…” · “KALICI RİSKLER…” · “BU OTURUMDA BULUNAN…”
- envanter kaynakları: `meridian/obs.py` (ALARM_ sabitleri) · `meridian/watchdog.py`
  (EXPECTED pencereleri + `beat()` nabız yerleri) · `meridian/api.py::_sessiz_hat`
  (sapma adları ve runbook ipuçları) · `obs.alarm(...)` ateşleme yerleri
- `ops/*.sh` ve `deploy/oracle-a1/*.sh` **gövdesindeki `obs.alarm(...)` ateşlemeleri**:
  bir betik gövdesinde bir jetonu ateşliyorsa o jetonun **kurtarma yöneticisidir** ve
  jetonun Çözüm alanına eşlenir — başlıkta adı geçmese bile koddan türer (ör.
  `ops/keepalive.sh` → `MECHANISM_STALE`)

**Kapsam dışı, bilerek:** `deploy/*.sh` (üst düzey, `monitoring.sh` dahil) onaylı kümede
değil. Sessiz bir kapsam genişlemesi yerine sınır burada yazılı duruyor.

**Eşleştirme kuralı — LİTERAL AD GEÇİŞİ.** Bir bölüme betik/günlük maddesi ancak o metinde
bölümün adı harfi harfine geçiyorsa iliştirilir. Anlamsal/bulanık eşleştirme YOK: bir
alarmı yanlış betiğe bağlamak, hiç bağlamamaktan kötüdür. Kaynağı olmayan alan “**runbook girdisi henüz yazılmadı**”
der ve nerede aradığını söyler — o cümle bir eksiğin ADIDIR, doldurulacak bir boşluk değil.

**Üretim damgası yoktur, bilerek:** belge zaman damgası taşısaydı her koşu diff üretir ve
“kodla ayrıştı mı” sorusu ölçülemez olurdu. Aynı kaynaktan aynı metin çıkar.

---

## Envanter özeti {#envanter}

- **14 alarm jetonu** (`meridian/obs.py`) — hepsi bildirim beyaz-listesinde
  (`NOTIFY_TOKENS` ALARM_ sabitlerinden TÜRETİLİR, elle liste değil)
- **17 bekçi mekanizması** (`meridian/watchdog.py::EXPECTED`)
- **5 sessiz-hat sapma adı** (`meridian/api.py::_sessiz_hat`; bekçi segmentinin
  adları değişkendir ve yukarıdaki mekanizma listesinden gelir)
- **16 ops betiği** başlığıyla okundu
- **77 günlük maddesi** üç bölümden toplandı

---

# Alarmlar {#alarmlar}

Bir alarm panoda üç yerde görünür: **Alarm gelen kutusu** (Bugün), **olay akışı** ve —
kanal kuruluysa — telefon bildirimi. Aşağıdaki her bölüm o jetonun kendi teşhis hattıdır.

## HEARTBEAT_STALE {#heartbeat_stale}

### Belirti

- Neden ayrı bir sınıf: Tokens matched by deploy/monitoring.sh log filters. Keep these strings stable. *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Kodda `obs.alarm` ateşleme yeri BULUNAMADI — jeton tanımlı ama hiçbir yol onu üretmiyor. Bu bir bulgudur: ya mekanizma kablolanmamış, ya jeton emekli.
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **HEARTBEAT_STALE kurtarma (WP-P, 2026-08-10):** jeton bugün ÜRETİCİSİZ — tek üreticisi eski `run.py` worker döngüsüydü, emekli (beyan: meridian/run.py:34). Yeni bir kaydı görmek "eski bir yapı koşuyor" demektir: `state/events.jsonl` kaydının sürecini/sürümünü doğrula (A1'de `journalctl -u meridian`). Döngü canlılığının gerçek bekçileri: A1 `meridian-tick-watchdog.timer` (deploy/oracle-a1/tick_watchdog.sh — scheduler damgası 45 dk bayatlarsa restart) + yerelde `ops/keepalive.sh` (healthz 60 sn'de bir; üst üste 2 ölü → süreci diriltir).

## ROLLBACK {#rollback}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **2 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/rollback.py:246` → mesaj şablonu: `f"GERİ ALMA BAŞARISIZ: v{version} kötü ama v{parent} anlık görüntüsü yok — " f"kötü sürüm CANLI kalıyor, elle müdahale gerekli"`
  - `meridian/rollback.py:278` → mesaj şablonu: `f"v{version} → v{parent} underperformed by {round(karar['par'] - karar['cur'], 4)} " f"({karar['yontem']})"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **ROLLBACK kurtarma (WP-P, 2026-08-10):** iki hâl, olay `detail`inden ayrılır. (a) rollback.py:253 = geri alma UYGULANDI (çocuk ebeveynden `rollback_if_worse_by` kadar kötü) — eylem gerekmez, kayıttaki from_version/to_version + karar_* alanları hükmün kanıtı. (b) rollback.py:221 = geri alma BAŞARISIZ: `state/history/vNNNN.yaml` ebeveyn anlık görüntüsü yok, KÖTÜ sürüm CANLI kalıyor. Kurtarma: dosyayı state yedeğinden geri koy (Mac `backups/a1/` — ops/pull-a1-backups.sh çeker; A1 `/home/ubuntu/backups/state-*.tar.gz`) — bakım penceresinde (canlı worker koşarken state'e yazılmaz); dosya gelince sonraki değerlendirme (loop.py:1717) geri almayı kendiliğinden yeniden dener.

## CIRCUIT_BREAKER {#circuit_breaker}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:1366` → mesaj şablonu: `f"günlük kayıp devre kesici: {day_pnl_pct:.2%}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **CIRCUIT_BREAKER kurtarma (WP-P, 2026-08-10):** tetik loop.py:1108 — OPEN işaretli günlük PnL `goal.limits.max_daily_loss_pct` eşiğini aştı (health.py:293); o gün yeni giriş yok (giriş kapısındaki `not breaker` şartı, loop.py:198 beyanı), pozisyon yönetimi sürer. ELLE KOL YOK — bilinçli: kesici dosya değil heartbeat alanıdır (`breaker_tripped`) ve bir sonraki seansta kendiliğinden sıfırlanır (`devre_kesici` sapmasının ipucuyla aynı hüküm; day_start_equity her işlenen barda tazelenir, loop.py:1221). Operatör: günün kayıp nedenini oku (pano kill yüzeyi → Kitap · şu an); ertesi seans sıfırlanmadıysa risk defterine bak.

## DATA_QUALITY {#data_quality}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **15 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/adapters/data.py:1004` → mesaj şablonu: `f"BAR KAYNAK UYUŞMAZLIĞI: {ticker.upper()} {d} — {src} {round(pc, 4)} vs " f"massive {round(mc, 4)} (%{round(dev * 100, 3)} > tol %{round(MASSIVE_TOL * 100, 3)})"`
  - `meridian/adapters/data.py:2189` → mesaj şablonu: `f"{ticker}: {streak} ardışık turda hiçbir kaynak satır vermedi (istek hatası YOK) " f"— evren bakımı gerekiyor olabilir"`
  - `meridian/api.py:57` → mesaj şablonu: `"MERIDIAN_DASH_TOKEN ASCII-DIŞI: HTTP başlığında gönderilemez, yani pano " "kimlik doğrulaması FİİLEN İMKÂNSIZ. ASCII bir token ile değiştir."`
  - `meridian/hotstate.py:168` → mesaj şablonu: `f"hotstate ÇIRPINMA: {DOWN_REASSERT_S}s içinde {bastirilan} kopma"`
  - `meridian/loop.py:892` → mesaj şablonu: `f"evren sapması: {rep['n_stale']} sembol S&P 500'de yok — {', '.join(rep['stale'][:8])}"`
  - `meridian/loop.py:1022` → mesaj şablonu: `"portfolio.json bir sözlük DEĞİL — kitap tam belge olarak yeniden yazıldı"`
  - `meridian/loop.py:1032` → mesaj şablonu: `"sermaye beyanı silinecekti — kitap yazımı REDDEDİLDİ"`
  - `meridian/loop.py:1318` → mesaj şablonu: `f"endeks çapraz-doğrulama sapması: {_xc.get('divergence')}"`
  - `meridian/loop.py:1325` → mesaj şablonu: `f"veri kalitesi kapısı: index_ok={idx_ok}, {len(tick_bad)} hisse başarısız"`
  - `meridian/scheduler.py:363` → mesaj şablonu: `f"SEANS ATLANDI: {session} — bir sonraki seans kapandı, bu seansın barı hâlâ " f"gelmedi (kapsama %{100 * float(cov or 0):.0f} < %{100 * need:.0f})"`
  - `meridian/watchdog.py:1826` → mesaj şablonu: `f"BAR DETERMİNİZMİ ÖLÇÜLEMEDİ: {rep['determinism'].get('detail')}" if _olcum_yok else f"SESSİZ BAR MUTASYONU: {rep['determinism'].get('detail')}"`
  - `meridian/watchdog.py:1898` → mesaj şablonu: `f"GERİLEME: {rg['field']} {rg['was']} → {rg['now']} (ileri-only olmalıydı)"`
  - `meridian/watchdog.py:1905` → mesaj şablonu: `f"ALAN EZİLDİ: {lo['file']}.{lo['field']} bir kez doluydu, şimdi kayıp"`
  - `meridian/watchdog.py:3019` → mesaj şablonu: `f"DAMGASIZ YAZIM: {ad} bu tur DIŞARIDAN değişti — içerik değişti ama " f"rev/updated_at damgası ilerlemedi, yani yazım `store` kapısından GEÇMEDİ " f"(doğrudan SQL ya da elle kurulmuş belge yazımı)"`
  - `meridian/watchdog.py:3457` → mesaj şablonu: `rep.get("beyan")`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **DATA_QUALITY kurtarma (WP-P, 2026-08-10):** 15 yol tek sınıf değildir — önce olay `detail`inden alt sınıfı ayır. Kapı hâli (loop.py:1068, `data_halt` → heartbeat `data_ok=False`; `veri_kalitesi` sapması aynı olgu): o gün yeni giriş kapalı, karantinadaki sembol işlem üretmez, tazeleme sabrı kendiliğinden dener — pano Sağlık → Veri hattı · bütünlük (saglik#veriboru) + `state/data_quality.json`. Elle onarımlı bilinen alt sınıflar: pano token'ı ASCII-dışı (api.py:40) → A1 `.dash.env` rotasyonu (deploy/oracle-a1/dash_token_credential.sh); sermaye beyanı kaybı (loop.py:806 reddin kaydı) → iade betiği ops/sermaye_beyani_iade.py.

## HALT_ACTIVE {#halt_active}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/api.py:5507` → mesaj şablonu: `"HALT via dashboard"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **HALT_ACTIVE kurtarma (WP-P, 2026-08-10):** tek tetik api.py:4873 — panodan `/api/halt` (health.set_halt → `state/HALT`; bir sonraki muma kadar yeni alım yok, mevcut pozisyonlar yönetilir). Arıza değil OPERATÖR EYLEMİNİN kaydıdır: kolu kimin/ne zaman çektiği olay defterinde. Geri alma yine panodan: sağ üst DEVAM (Kademe 1 Soft Halt kolu) → `POST /api/resume`; telefonda `/panic` sayfası aynı halt/devam çiftini taşır (`soft_halt` sapması aynı kolu gösterir).

## MIRROR_DRIFT {#mirror_drift}

### Belirti

- internal sim fill vs actual Alpaca fill diverged beyond tolerance *(kaynak: `meridian/obs.py` — `ALARM_MIRROR_DRIFT`)*

### Teşhis adımları

- Bu jetonu **7 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:266` → mesaj şablonu: `f"ayna çıkışı kapatılamadı: {t} ({info.get('reason')}) — iç defter KAPALI, aynada " f"AÇIK; {info['tries']}. deneme" + (" — KORUMA BACAĞI İPTAL EDİLDİ, pozisyon ÇIPLAK" if info["naked"] else "")`
  - `meridian/loop.py:2835` → mesaj şablonu: `f"ayna sapması: {info.get('ticker')} — sim {round(sim, 4)} vs Alpaca " f"{round(af, 4)} (%{div*100:.2f})"`
  - `meridian/loop.py:2950` → mesaj şablonu: `f"koruma dolumu: {sym} aynada koruma bacağıyla kapandı (bacak={bacak or '?'}, " f"fiyat={fiyat_s})" + (f" — iç kitaba `{reason}` kapanışı işlendi" if islendi else f" — kitaba İŞLENEMEDİ: {neden}")`
  - `meridian/loop.py:3155` → mesaj şablonu: `f"ayna pozisyonu kayıp: {sym} içeride açık, Alpaca'da ne pozisyon ne emir var"`
  - `meridian/loop.py:3187` → mesaj şablonu: `f"ayna adet sapması: {sym} — içeride {qty:g}, Alpaca'da {aq:g}" f" · sapma sınıfı: {_sinif} — {_neden}"`
  - `meridian/loop.py:3263` → mesaj şablonu: `f"motor yetimi ({_ys}): {sym} Alpaca'da açık (motorun emri dolmuş) ama iç " f"defterde yok — {_yn}"`
  - `meridian/loop.py:3268` → mesaj şablonu: `f"çıkış yetimi: {sym} iç motor çıktı ama ayna kapatılamadı — kuyrukta, " f"bir sonraki döngüde yeniden denenecek"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **MIRROR_DRIFT kurtarma (WP-P, 2026-08-10):** altı yolun ayrımı olaydaki `drift_sinifi` alanındadır. Kendi kendine onarım: çıkış-yetimi kuyruğu her döngü yeniden dener (loop.py:146 — tavansız, sessiz terk yok); trail senkronu yalnız yukarı PATCH'ler. Operatör: Mutabakat masası (pano karar#mutabakat) — hayalet/yetim/adet satırları; alarm "pozisyon ÇIPLAK" diyorsa önce koruma kur (çıplak-pozisyon prosedürü). Kalıcı split_brain/motor_yetimi/adet sapmasında hüküm operatöründür: iç defter tek gerçek (loop.py:563 beyanı), broker tarafını elle düzeltmek domain kararıdır.

## BROKER_REJECT {#broker_reject}

### Belirti

- Alpaca rejected an order the internal book would have executed *(kaynak: `meridian/obs.py` — `ALARM_BROKER_REJECT`)*

### Teşhis adımları

- Bu jetonu **3 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:710` → mesaj şablonu: `f"Alpaca ulaşılamıyor — ayna atlandı, {len(meta['armed'])} plan silahlı kaldı"`
  - `meridian/loop.py:791` → mesaj şablonu: `f"Alpaca reddi: {pl['ticker']} — {res.get('detail','')}"`
  - `meridian/mirror_stream.py:186` → mesaj şablonu: `f"akıştan anlık RET: {order.get('symbol')}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **BROKER_REJECT kurtarma (WP-P, 2026-08-10):** üç hâl: (a) ulaşım yok (loop.py:564) — ayna atlanır, planlar SİLAHLI kalır, sonraki tur kendiliğinden dener; Alpaca erişimini/anahtarları doğrula (mutabakat "Broker API" satırı; sırlar A1 `.env` — deploy/oracle-a1/RUNBOOK.md Bölüm C). (b) gerçek ret (loop.py:645) — plan silahlı kümeden DÜŞER (`failed_broker_rejection` damgası, kendiliğinden geri gelmez); ret nedeni/sınıfı panoda Reddedilen emir kaydı (karar#failsub) — yeniden kurma kararı operatöründür. (c) akış reti (mirror_stream.py:158) aynı masada görünür.

## TRAIL_DESYNC {#trail_desync}

### Belirti

- trailing-stop PATCH reddedildi — iç HWM ile broker stopu ayrıştı *(kaynak: `meridian/obs.py` — `ALARM_TRAIL_DESYNC`)*

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:2408` → mesaj şablonu: `f"trail PATCH reddedildi: {sym} {frm}→{to}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **TRAIL_DESYNC kurtarma (WP-P, 2026-08-10):** tetik loop.py:1885 (çağrı loop.py:2233) — iç iz süren stop yükseldi, aynadaki stop bacağının PATCH'i reddedildi; broker'da ESKİ (daha alçak) stop duruyor: pozisyon korumasız değil, koruması BAYAT. Senkron her mutabakat turunda yeniden dener (sayaç: mutabakat masası Force-sync satırı). Operatör: ret `detail`indeki broker nedenine bak; ret sürüyorsa stop bacağının emir durumunu Alpaca tarafında doğrula — bacak ölü/iptalse iş çıplak-pozisyon prosedürüne düşer.

## MECHANISM_STALE {#mechanism_stale}

### Belirti

- bir mekanizma üretmiyor/bayatladı (bütünlük dedektörleri) *(kaynak: `meridian/obs.py` — `ALARM_MECHANISM_STALE`)*

### Teşhis adımları

- Bu jetonu **15 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/selfreview.py:123` → mesaj şablonu: `f"mekanizma ÜRETEMİYOR: {name} — {detail} (üst üste {box['streak']} koşum)"`
  - `meridian/watchdog.py:296` → mesaj şablonu: `f"mekanizma gecikti: {ad} — {x['gap_h']} sa (pencere {x['expected_h']} sa)"`
  - `meridian/watchdog.py:1800` → mesaj şablonu: `f"BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ: {_ad} hüküm veremedi — {_dr.get('error')}"`
  - `meridian/watchdog.py:1809` → mesaj şablonu: `f"mekanizma ÜRETMİYOR: {s['name']} — {s['note']} (0 çıktı)"`
  - `meridian/watchdog.py:1815` → mesaj şablonu: `f"KORUNUM İHLALİ: {rep['conservation']['unexplained']} plan kayıtsız kayboldu"`
  - `meridian/watchdog.py:1866` → mesaj şablonu: `f"OKUNMAYAN ARTEFAKT: {_a} yazılıyor ama hiçbir modül okumuyor"`
  - `meridian/watchdog.py:1873` → mesaj şablonu: `f"MAKULLÜK: {pr['check']} — {pr['detail']}"`
  - `meridian/watchdog.py:1883` → mesaj şablonu: `f"DEĞER AYRIŞMASI: {dv['olgu']} — aynı olguyu iddia eden kaynaklar ZIT " f"değer taşıyor ({_k}) · {dv['neden']}"`
  - `meridian/watchdog.py:1891` → mesaj şablonu: `f"BAYAT TÜREV: {st['artifact']} kaynağından {st['behind_h']} sa geride"`
  - `meridian/watchdog.py:3129` → mesaj şablonu: `f"MUTABAKAT TAZELİĞİ ÖLÇÜLEMEDİ: {rep.get('neden')}"`
  - `meridian/watchdog.py:3136` → mesaj şablonu: `f"BAYAT MUTABAKAT: {rep['neden']}"`
  - `meridian/watchdog.py:3388` → mesaj şablonu: `f"SPRINT CANLILIĞI ÖLÇÜLEMEDİ: {sp.get('beyan')}"`
  - `meridian/watchdog.py:3394` → mesaj şablonu: `f"SPRINT ORPHAN: {sp.get('beyan')}"`
  - `meridian/watchdog.py:3400` → mesaj şablonu: `f"ÖĞRENME CANLILIĞI ÖLÇÜLEMEDİ: {lr.get('beyan')}"`
  - `meridian/watchdog.py:3406` → mesaj şablonu: `f"ÖĞRENME DURDU: {lr.get('beyan')}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- `ops/keepalive.sh` — gövdesinde `obs.alarm('MECHANISM_STALE')` ateşliyor (satır 46); bu betik jetonun KURTARMA YÖNETİCİSİDİR.
  - Betik özeti: Meridian keepalive — kullanıcı-oturumu süpervizörü (launchd, ~/Documents'a TCC engeli yüzünden …
- **KALICI RİSKLER / DERSLER** → **MECHANISM_STALE kurtarma (WP-P, 2026-08-10):** ilk soru "hangi mekanizma" — ad olay `detail`inde; RUNBOOK'un o mekanizma bölümü nabzı kimin attığını söyler, son damga `state/mechanism_beats.json`. Bekçi YALNIZ gözlemdir, yeniden başlatmaz. Ölü sunucu hâlinin kurtarma yöneticisi yerelde `ops/keepalive.sh` (healthz 2× ölü → diriltir + bu jetonu yazar), A1'de `meridian-tick-watchdog.timer`. ÜRETMİYOR/DÜŞTÜ/BAYAT-TÜREV hâlleri mekanizmanın kendi bölümünden teşhis edilir; toplu görünüm pano Sağlık → gece hattı çizelgesi (saglik#cizelge).

## ARMING_READY {#arming_ready}

### Belirti

- silahlanma eşiği karşılandı — operatör kararı bekleniyor *(kaynak: `meridian/obs.py` — `ALARM_ARMING_READY`)*

### Teşhis adımları

- Bu jetonu **2 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/arming.py:215` → mesaj şablonu: `f"uyuyan kurulum kapıyı GEÇTİ: {setup} — silahlanma operatör onayı bekliyor"`
  - `meridian/arming.py:311` → mesaj şablonu: `f"uyuyan kurulum kapıyı GEÇTİ: {setup} — silahlanma operatör onayı bekliyor"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **ARMING_READY kurtarma (WP-P, 2026-08-10):** tetik arming.py:203/299 — uyuyan kurulum kapıyı geçti; arıza değil KARAR ÇAĞRISI. Kanıt: pano Onay kuyruğu (karar#onaylar) + `state/arming_report.json`. Panelde uygulanacak eylem BİLEREK yok (`actions: []` — api.py:1438 beyanı): silahlanma bir KOD değişikliğidir, icra yolu `strategy.py:995 ARMED_SETUPS` listesine kurulumu eklemektir (mühendislik turu, operatör onayıyla). Kapı geçişi icra zorunluluğu doğurmaz (arming.py docstring: "kapı GEÇSE bile ARMED_SETUPS değişmez") — reddetmek de meşru bir hüküm.

## AUTHORITY_CHANGE {#authority_change}

### Belirti

- bir mekanizmanın yetkisi açıldı/geri alındı *(kaynak: `meridian/obs.py` — `ALARM_AUTHORITY`)*
- Neden ayrı bir sınıf: KALİBRASYON YETKİ DEĞİŞİMİ 'BENİ UYANDIR' SINIFIDIR (operatör kararı): bir danışmanın yetkisi EŞİK DOLUNCA KENDİLİĞİNDEN açılır ve pano bunu yalnız DUYURUR — yani operatör onay vermez, haberdar edilir. Haberin kendisi obs.log seviyesinde kalsaydı yetki devri olay defterinin içinde sıradan bir satır olurdu ve kimse bakmadan geçerdi. Kayıp da kazanım kadar yüksek sesli olmalı: yetkinin GERİ ALINMASI, sessizce alınırsa "danışman hâlâ konuşuyor" sanılır. *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Bu jetonu **2 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/analytics.py:1228` → mesaj şablonu: `f"LLM danışman yetkisi {'AÇILDI' if promoted else 'GERİ ALINDI'} — " f"R farkı {gap if gap is not None else 'ölçülmedi'}, n={len(pairs)} çift " f"(yetki: yalnız REVIEW+karşı dolum vetosu)"`
  - `meridian/nous_eval.py:306` → mesaj şablonu: `f"ÇEKİRDEK-ŞEKİLLİ ÖNERİ KUYRUĞA SOKULMAYA ÇALIŞILDI (sekil={sekil})"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **AUTHORITY_CHANGE kurtarma (WP-P, 2026-08-10):** iki hâl. (a) analytics.py:1172 — LLM danışman yetkisi eşikle KENDİLİĞİNDEN açıldı/geri alındı (yetki yalnız REVIEW + karşı dolum vetosu); onay gerekmez, doğrulama yeter: olay alanları promoted/r_gap/n + `state/llm_calibration.json`; sınırlar pano Otonomi ve sınırlar (kilitler#ayarlar). (b) nous_eval.py:312 — çekirdek-şekilli öneri kuyruğa sokulmaya çalışıldı: alarmın kendi beyanıyla KOD HATASIDIR (köprü yanlış yönlendirdi) → operatör eylemi yok, mühendislik turu açılır.

## GOAL_FAILURE {#goal_failure}

### Belirti

- realized_30d < goal.failure_below — sözleşme hükmü *(kaynak: `meridian/obs.py` — `ALARM_GOAL_FAILURE`)*
- Neden ayrı bir sınıf: SÖZLEŞMENİN BAŞARISIZLIK HÜKMÜ. goal.yaml `failure_below` hükmünü ("30g getiri bu eşiğin altına düşerse deney BAŞARISIZ") tanımlandığından beri hiçbir kod ölçmüyordu: score.py hedef tarafını (target_return_30d/max_drawdown/min_sharpe) composite'e katıyor, failure tarafını asla okumuyordu. Deney başarısız olsa bunu söyleyecek tek satır kod yoktu. Bu kendi sınıfıdır: DATA_QUALITY "veri bozuk" der, MECHANISM_STALE "mekanizma üretmiyor" der — ikisi de "mekanizma çalıştı ve sonuç sözleşmenin başarısızlık eşiğinin altında" demez. *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/watchdog.py:1783` → mesaj şablonu: `f"SÖZLEŞME BAŞARISIZLIK EŞİĞİ: {_gf['detail']}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **AÇIK KALANLAR (bilinçli, sahipli)** → **GOAL_FAILURE kurtarması KOD-TÜRETİLEMEZ — operatör domain kararı gerekir (WP-P, 2026-08-10, bilinçli açık):** tetik watchdog.py:1696 — `goal_failure_report` (watchdog.py:1647): 30g gerçekleşen getiri `goal.yaml failure_below` eşiğinin altında (mandallı — düşüşte bir kez; örneklem min_sample altındaysa hüküm None, alarm yok). Bu sözleşmenin BAŞARISIZLIK HÜKMÜdür; onu "kurtaracak" betik/endpoint yoktur ve olmamalıdır — deneyin akıbeti (durdur / param revizyonu / goal.yaml değişikliği) operatör mandasıdır. Kontrol: olay alanları realized_30d/threshold/n + pano bütünlük yüzeyi; goal.yaml İZLİ (dagit [1b] SSoT), değişiklik ayrı turdur.

## NAKED_POSITION {#naked_position}

### Belirti

- açık pozisyonun broker'da canlı koruyucu stop'u YOK *(kaynak: `meridian/obs.py` — `ALARM_NAKED_POSITION`)*
- Neden ayrı bir sınıf: KORUMASIZ POZİSYON KENDİ JETONUNU HAK EDER (N1 — operatör kararı; v209'da ölçülüp ertelenmişti). `watchdog.check_koruma_and_alarm` v209'da MIRROR_DRIFT jetonunu ÖDÜNÇ alıyordu çünkü o tur `obs.py` yazım kapsamı dışındaydı ve listede olmayan bir jeton yazılıp operatöre HİÇ ulaşmazdı (NOTIFY_TOKENS türetmesi, aşağıda). Ödüncün BEDELİ o gün ölçülmüş ve docstring'e yazılmıştı: `_maybe_notify` susturma penceresi JETON BAŞINADIR (6 sa), yani gürültülü bir mutabakat gecesinde ADET SAPMASI alarmları pencereyi doldurup KORUMASIZ POZİSYON alarmının TESLİMATINI bastırabiliyordu. İki olgu ayrı: "ayna kitabın söylediği adette değil" bir MUHASEBE sapmasıdır, "pozisyonun broker'da canlı stop'u yok" bir SERMAYE riskidir (sev-1) ve birincisi ikincisini susturamaz. Teslim zinciri DEĞİŞMEZ — jeton buraya eklendiği an NOTIFY_TOKENS onu kendiliğinden kapsar (el listesi yok); kanalın kendisi operatör yapılandırmasıdır. *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Bu jetonu **2 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/watchdog.py:2836` → mesaj şablonu: `f"KORUMA ÖLÇÜLEMEDİ: broker okunamadı — {rep.get('neden')} " f"(bu 'korumasız 0' DEĞİL: açık pozisyonların koruma durumu BİLİNMİYOR)"`
  - `meridian/watchdog.py:2849` → mesaj şablonu: `f"KORUMASIZ POZİSYON: {r['ticker']} {r['adet']:g} adet açık, broker'da " f"canlı koruyucu stop YOK — {r['neden']} " f"({rep['korumasiz']}/{rep['toplam']} motor pozisyonu korumasız)"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **NAKED_POSITION kurtarma (WP-P, 2026-08-10):** tetik watchdog.py:2286 (motor pozisyonunda canlı koruyucu stop YOK — sev-1; pozisyon başına bir kez mandallı) ve watchdog.py:2273 (ÖLÇÜLEMEDİ: broker okunamadı — "korumasız 0" DEĞİL, önce erişimi düzelt). Kurtarma panodan: Mutabakat masası → Koruma · çıplak pozisyonlar kartı (taze ölçüm `GET /api/alpaca/koruma`) → koruma-onayı `POST /api/alpaca/koruma_kur` (onay jetonu + oneri_id; jetonsuz çağrı KURU KOŞU, bayat oneri_id emri düşürür) her çıplak motor pozisyonuna TEK OCO kurar; HALT bu yolu kapatmaz (koruma_kur bloğu beyanı).

## ONAYLI_PLAN_GONDERILMEDI {#onayli_plan_gonderilmedi}

### Belirti

- Neden ayrı bir sınıf: ONAYLI PLAN GÖNDERİLMEDİ — KENDİ JETONU (P-2026-08-07-VLO vakası). Aday alternatif MIRROR_DRIFT'in yeni bir `drift_sinifi` değeriydi ve ÜÇ ölçülmüş gerekçeyle REDDEDİLDİ: (1) N1 emsali birebir — `_maybe_notify` susturma penceresi JETON BAŞINADIR (6 sa): gürültülü bir mutabakat gecesinde adet-sapması MIRROR_DRIFT'leri pencereyi doldurur ve "operatörün onayladığı emir broker'a HİÇ gitmedi" alarmının TESLİMATINI bastırırdı — bu sınıf tam da operatörün "büyük fiyasko" dediği sınıftır, muhasebe gürültüsünün arkasında bekleyemez. (2) C9 yasası ("iki teşhis aynı isimle sayılırsa ikisi de okunamaz"): split_brain BELİRTİ adıdır (sebep bilinmiyor), bu jeton SEBEBİ BİLİNEN ve EYLEMİ BELLİ bir alt sınıftır (onay verildi, iç motor doldu, gönderim hiç olmadı → gönderim yolunu onar / elle emirle). (3) Teslim zinciri değişmez: NOTIFY_TOKENS her ALARM_ sabitinden TÜRETİLİR (aşağıda) — jeton eklendiği an bildirim kapsamındadır, el listesi eskimez. Üretici: watchdog (İŞ-3b bekçisi); reconcile'ın MIRROR_DRIFT/split_brain alarmı AYNEN kalır (o genel belirtiyi anlatmaya devam eder). *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/watchdog.py:3243` → mesaj şablonu: `f"ONAYLI PLAN GÖNDERİLMEDİ: {v.get('ticker')} ({v.get('plan_id')}) — operatör " f"onayladı ({v.get('onay_ts') or 'ts?'}), iç motor doldurdu, Alpaca'da NE EMİR NE " f"POZİSYON var ({iz}). VLO-2026-08-10 sınıfı: gönderim yolunu onar ya da elle emirle"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **ONAYLI_PLAN_GONDERILMEDI kurtarma (WP-P, 2026-08-12):** tetik watchdog.py:2687 (rapor watchdog.py:2606; poll kadansında, kendi try'ında watchdog.py:311): operatör-onaylı + iç-motor-dolmuş planın dolum-sonrası reconcile fotoğrafında Alpaca'da NE EMİR NE POZİSYON var; ihlal plan_id başına bir kez mandallı, ÖLÇÜLEMEDİ dalları alarmsız (fotoğraf bayatlığının sahibi #10 mutabakat-tazelik bekçisi — çift-duyuru yasağı). İlk ayrım olaydaki `gonderim_izi`: False = emir HİÇ çıkmadı → onay yanıtının/`plan_operator_approved` olayının `icra_yolu` alanını oku (loop.py:503-527 gönderimin sonucunu ya da yolun yokluğunu hâl hâl AÇIKÇA yazar); True = iz var ama broker'da yok → Mutabakat masası (pano karar#mutabakat) + Alpaca tarafını doğrula. Kendi kendine onarım: döngünün geç-gönderim kemeri (loop.py:1342) her günlük turda aynasız iç dolumları TEK kapıdan yeniden gönderir — olay `mirror_gec_gonderim`, kemer düşerse `mirror_gec_gonderim_dustu`. Pano `submit_armed` düğmesi BU vakayı KAPATMAZ (yalnız SİLAHLI kümeyi gönderir; dolan plan kümede değil — loop.py:1339 armed'a dokunulmaz beyanı). Kemer de kapatamıyorsa acil kapama ELLE EMİRDİR ve operatör domain kararıdır (alarm metninin kendi hükmü: "gönderim yolunu onar ya da elle emirle"); kalıcı onarım mühendislik turu.

---

# Bekçi mekanizmaları {#mekanizmalar}

Bekçi (`meridian/watchdog.py`) YALNIZ GÖZLEMDİR: hiçbir mekanizmayı yeniden başlatmaz,
hiçbir kararı etkilemez. Bir mekanizma penceresini aştığında sessiz hattın **bekçiler**
segmenti açılır ve `MECHANISM_STALE` ateşlenir. Aşağıdaki her bölüm tek bir mekanizmanın
penceresini, nabzını KİMİN attığını ve nerede arayacağını söyler.

Nabız defteri: `state/mechanism_beats.json` (ad → son damga, epoch saniye).

## scheduler_poll {#scheduler_poll}

### Belirti

- Beklenen azami sessizlik **30 dk**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: 300 sn'lik poll — 30 dk sessizlik = süreç ölü/kilitli *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:906`
- Son damga: `state/mechanism_beats.json` → `scheduler_poll`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **scheduler_poll kurtarma (WP-P, 2026-08-12):** damgayı advance_once'ın kendisi atar (scheduler.py:815, her 300 sn poll'da — seans DIŞINDA da; tick_watchdog başlığındaki ölçüm: hafta sonu maksimum aralık 302 sn). 30 dk sessizlik "kadans gecikti" değil SÜREÇ ÖLÜ/KİLİTLİ demektir; kurtarma yöneticileri süreç düzeyindedir: A1'de `meridian-tick-watchdog.timer` (deploy/oracle-a1/tick_watchdog.sh — scheduler_status.updated 45 dk bayatlarsa restart; YAS koruması taze süreci bayat sanmaz), yerelde `ops/keepalive.sh` (healthz üst üste 2 ölü → diriltir). Süreç dirilince poll kendiliğinden döner; elle yetişme `POST /api/scheduler/advance` (pano düğmesi; olay `scheduler_advance_manual`).

## hermes_poll {#hermes_poll}

### Belirti

- Beklenen azami sessizlik **30 dk**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: bekleme döngüsü + ısınma sprinti (sonda başına nabız) *(kaynak: `meridian/watchdog.py`)*
- `hermes_poll` PENCERESİ 30 DK KALIR AMA ANLAMI DEĞİŞTİ: nabzı artık yalnız `_run` döngüsünün turu atmıyor, ISINMA SPRİNTİ de her sondada atıyor. Eskiden ısınma koşarken (nominal 1-5 sa) döngü tura dönemiyor, nabız susuyor ve bekçi SAHTE bir MECHANISM_STALE üretiyordu — mekanizma ölü değil MEŞGULdü. Nabzın sorduğu soru "döngü turladı mı" değil, "hermes ipliği canlı ve ilerliyor mu"dur; ısınma içinden atılan nabız o soruya DOĞRU cevap verir. Pencereyi ısınmaya göre genişletmek yanlış olurdu: o zaman gerçekten ölmüş bir poll ipliği de saatlerce görünmezdi. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/hermes_runtime.py:165` · `meridian/hermes_runtime.py:148` · `meridian/hermes_runtime.py:418`
- Son damga: `state/mechanism_beats.json` → `hermes_poll`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **hermes_poll kurtarma (WP-P, 2026-08-12):** önce ASKIDA mı bak — bekçi rozeti (pano Operasyon) `askida` kovasını ayrı gösterir (watchdog.py:118 sondası): kota soğuması (`brain_cooldown.json`) ya da kimlik havuzu tükenmesi BEKLEMEDİR, arıza değil — alarm üretmez, eylem gerektirmez, OK da sayılmaz (panoda dürüst). Gerçek bayatlıkta iplik ölmüştür: hermes ipliği api sürecinin İÇİNDE yaşar (start() api açılışında; hermes_runtime.py:372 beyanı) → kurtarma süreç restart'ıdır (yerelde `ops/keepalive.sh`, A1'de `meridian-tick-watchdog.timer` — iplik tek başına yeniden başlatılamaz). Isınma koşarken damga sonda başına atılır (hermes_runtime.py:133) — "meşgul" sahte alarm üretmez (v192 + H11).

## warmup_sprint {#warmup_sprint}

### Belirti

- Beklenen azami sessizlik **8 sa**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- `warmup_sprint` EŞİĞİ 8 SA'DA KALIR — VE ARTIK GERÇEK BİR ANOMALİ ÖLÇER. Nominal ~1-5 sa; Aramanın KENDİ süre tavanı var (HERMES_WARMUP_MAX_MIN, varsayılan 300 dk = 5 sa) ve tavana takılan koşum kibarca kesilir. Yani 8 sa'lık bir sessizlik artık "ısınma uzun sürdü" olamaz: tavan onu 5 saatte keserdi. Kalan tek açıklama tavanın ÇALIŞMAMASIDIR (iplik asıldı, sonda içinde kilitlendi, süreç öldü) — eşiği eskiden gürültü üreten bir sayı, şimdi teşhis. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/hermes_runtime.py:164` · `meridian/hermes_runtime.py:147`
- Son damga: `state/mechanism_beats.json` → `warmup_sprint`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **warmup_sprint kurtarma (WP-P, 2026-08-12):** 8 sa sessizlik "ısınma uzun sürdü" OLAMAZ — aramanın kendi tavanı (HERMES_WARMUP_MAX_MIN, varsayılan 5 sa) koşumu kibarca keser; aşım = tavan ÇALIŞMADI (iplik asılı / sonda içinde kilitli / süreç ölü). Kanıt: son ısınma özeti (hermes_runtime.py:160 `last_warmup`: kesildi/sebep/tavan_dk — pano hermes kartı) + `_warm_skip` nedeni (hermes_runtime.py:410 — "koşmadı" ile "koşamaz" ayrımı; learn_halted değeri Kademe-4 kolunun MEŞRU duraklatmasıdır, arıza değil). Kurtarma süreç restart'ıdır (yerelde `ops/keepalive.sh`, A1'de `meridian-tick-watchdog.timer`).

## cf_advance {#cf_advance}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı: uzun hafta sonu + tatil toleransı *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/loop.py:1566`
- Son damga: `state/mechanism_beats.json` → `cf_advance`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **cf_advance kurtarma (WP-P, 2026-08-12):** karşı-olgusal defterin (cf_open.json + counterfactuals.jsonl) günlük ilerleyişi; SIFIR YETKİ — hiçbir karar bu deftere bakmaz (loop.py:1408 beyanı), bayatlığı sermaye riski değil ÖLÇÜM boşluğudur (gölge katmanların ham maddesi birikmez). Düşerse `cf_advance_failed` uyarısı hatayı taşır (olay akışı / `state/events.jsonl`); damga yalnız başarıda atılır → bir sonraki günlük tur kendiliğinden dener; elle yetişme `POST /api/scheduler/advance`. Günlük tur hiç koşmuyorsa sorun bu mekanizma değil süreçtir (süreç-düzeyi yöneticilere bak).

## p5_calibrations {#p5_calibrations}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (P5 her döngüde) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/loop.py:2127`
- Son damga: `state/mechanism_beats.json` → `p5_calibrations`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **p5_calibrations kurtarma (WP-P, 2026-08-12):** damga P5_LEARN bloğunun SON adımıdır (loop.py:1948) — bayatlık "tek kalibrasyon düştü" değil "öğrenme-analitik bloğu sonuna ulaşamadı" demektir; hangi adımda kırıldığı `v3_learn_layer_failed` uyarısındadır (blok tek korumada, loop.py:1950). Kendiliğinden onarım: her günlük turda yeniden koşar; elle yetişme `POST /api/scheduler/advance`. Rehinelik dersi: bu blok günlük döngüye bağlıdır — veri kapsaması yüzünden noop kalan bir gün öğrenmeyi de sessizce durdurur (öğrenme-rehineliği vakasının sınıfı).

## mirror_reconcile {#mirror_reconcile}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (alpaca modunda her döngüde) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/loop.py:3342`
- Son damga: `state/mechanism_beats.json` → `mirror_reconcile`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **mirror_reconcile kurtarma (WP-P, 2026-08-12):** damga reconcile'ın `broker_reconcile.json` yazımından hemen önce atılır (loop.py:2570) — bayatlık "aynanın fotoğrafı eski" demektir ve fotoğraf yaşının asıl bekçisi #10 mutabakat-tazelik dedektörüdür (kind=mutabakat_tazeligi ile ayrıca alarmlar). Kontrol: Mutabakat masası (pano karar#mutabakat) + `state/broker_reconcile.json` date/api_ok/skip_reason alanları. Alpaca erişimi yoksa reconcile hüküm veremez → anahtar/ağ doğrulaması (mutabakat "Broker API" satırı; sırlar A1 `.env`). Kendiliğinden onarım: alpaca modunda her günlük tur; elle yetişme `POST /api/scheduler/advance`.

## crosscheck {#crosscheck}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seansta bir *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:1260`
- Son damga: `state/mechanism_beats.json` → `crosscheck`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **crosscheck kurtarma (WP-P, 2026-08-12):** SPY kapanışının bağımsız kaynakla seans başına bir karşılaştırması — `state/index_crosscheck.json`u yazar; veri-kalitesi kapısı `status=diverged`i AYNI seansta halt sebebine çevirir (loop.py:1169). Bayatlığın bedeli: bağımsız doğrulama SUSAR, bar kalitesi tek kaynağa kalır. Ateşleme yolu BİLİNÇLİ sessiz-yutmalı (scheduler.py:1170 — düşüş olay YAZMAZ) → teşhis dosyanın kendisinden: date/status alanı taze mi (pano Sağlık → Veri hattı, api.py:3850 aynı dosyayı servis eder). Kendiliğinden onarım: her yeni seans işlendiğinde; süreklilik arızası mühendislik turudur.

## earnings_refresh {#earnings_refresh}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık (+2 gün pay) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:1073`
- Son damga: `state/mechanism_beats.json` → `earnings_refresh`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- `deploy/oracle-a1/tick_watchdog.sh` — başlığında `earnings_refresh` geçiyor.

## arming_eval {#arming_eval}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık (+2 gün pay) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:1131`
- Son damga: `state/mechanism_beats.json` → `arming_eval`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **arming_eval kurtarma (WP-P, 2026-08-12):** haftalık uyuyan-kurulum ölçümü (scheduler.py:1039 `arming.evaluate`) — damga ve hafta bayrağı YALNIZ başarıda ilerler; düşerse `arming_eval_failed` uyarısı + bir SONRAKİ poll yeniden dener (hafta yakılmaz). Bayatlıkta kontrol: `state/arming_report.json` üretim damgası + pano Onay kuyruğu (karar#onaylar). Ölçüm koşup kapı geçse bile kod değişmez (ARMED_SETUPS bir mühendislik turudur; o karar çağrısının prosedürü kendi alarm bölümündedir) — burada iş yalnız kadansı yaşatmaktır.

## shadow_fit {#shadow_fit}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (öğrenme kadansı seans başına 1×) *(kaynak: `meridian/watchdog.py`)*
- ---- ÖĞRENME KADANSLARI -- NEDEN GECİKMELİ GİRDİ: dört mekanizma `beat()` damgasını ZATEN atıyordu (scheduler._learning_ cadence → shadow_fit/axis2_cycle, hermes.backfill → opinion_backfill, sprint.maybe_start → sprint_cadence) ama EXPECTED'de olmadıkları için `report()` onları hiç ARAMIYORDU. Nabız atılıp kimsenin beklemediği bir mekanizma, durduğunda MECHANISM_STALE üretmez — yani bekçinin kör noktası. Dördü de artık izleniyor. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:541`
- Son damga: `state/mechanism_beats.json` → `shadow_fit`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **shadow_fit kurtarma (WP-P, 2026-08-12):** öğrenme kadansının 1. adımı (scheduler.py:517 `shadow_model.maybe_refit` — seans başına bir, bar varışından bağımsız). Düşerse `shadow_fit_cadence_failed` uyarısı ve asıl risk şudur: model BAYAT katsayılarla tahmin üretmeye DEVAM eder (yanlış sayı doğru görünür). Kontrol: `state/shadow_model.json` fit_attempt_ts/fit_ts/fit_skip_reason/n_fit damgaları. Adım düşerse seans damgası yine ilerler → yeniden deneme bir SONRAKİ seans; kadansın KENDİSİ düşerse (`learning_cadence_failed`) damga ilerlemez → sonraki poll dener; elle yetişme `POST /api/scheduler/advance` (seans henüz işlenmemişse).

## axis2_cycle {#axis2_cycle}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (aynı kadansın 2. adımı) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:551`
- Son damga: `state/mechanism_beats.json` → `axis2_cycle`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **BU OTURUMDA BULUNAN + ÇÖZÜLEN (kök nedenleriyle)** → **ÖĞRENME REHİNELİĞİ (öğrenme-otomasyonu turu, kök düzeltme):** "fit çağrılmıyor" teşhisi YANLIŞTI — P5_LEARN her döngüde koşuyordu ama daily_cycle veri kapsaması yüzünden noop olunca öğrenme de sessizce onunla duruyordu (rehinelik, ve durduğu hiçbir yerde yazmıyordu). Yani veri düzeltmesi = öğrenme düzeltmesi. Ek: dolgu kuyruğunun gerçek boyutu 95 (sonuçlu planlar; 386 görüşsüzün 291'i sonuçsuz — kalibrasyon çifti sonuç ister), türetilmiş tavan ~46/gece → ~3 gece. Eksen-2 üreticileri hipotez-yan-ürünü rehineliğindeydi → bağımsız skills.axis2_cycle(); yapısal körlük bulundu: eşik cf katmanını okumuyor (n_cf=1080/1004'lük iki skill görünmez) — cf-kolu tasarımı temizlik turunda. sprint_runs "orphan"ı okuyucu hatasıydı (defter sandbox'ta, status() yanlış rafa bakıyordu — düzeltildi).

## opinion_backfill {#opinion_backfill}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- DOLGU AYRI PENCERE: kadans her seans TETİKLENİR ama `backfill_budget()["tavan"] == 0` iken damga ATILMAZ (bütçe kısılması bir arıza değil). Kuyruk boşaldığında da öyle. 9 gün = "iki hafta boyunca hiç dolgu koşmadıysa gerçekten bakılmalı" — kısılmayı alarm sanmaz. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/hermes.py:3881`
- Son damga: `state/mechanism_beats.json` → `opinion_backfill`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **opinion_backfill kurtarma (WP-P, 2026-08-12):** 9 günlük pencere kısılmayı alarm SANMAZ — önce meşru sessizliği ele: `backfill_progress` olayı kuyruğun hâlini (kalan_gun/kalan_satir), `hermes.backfill_budget()` türetimi tavanı söyler (tavan 0 = bütçe kısıldı, damga BİLEREK atılmaz; kuyruk boş = iş yok). İkisi de değilse dolgu gerçekten durmuştur: kota soğuması (`brain_cooldown.json`) + kadans uyarılarına bak (`learning_cadence_failed` / `backfill_beat_failed`). Kendiliğinden onarım: her seans kadans yeniden tetikler; dolgu asenkron koşar (hermes.py:3285) ve kalanı sonraki tura devreder.

## sprint_cadence {#sprint_cadence}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- SPRINT AYNI SINIF: `sprint.should_run` gece dilimi/aktif sprint/meşguliyet kapılarından dönebilir; her seans koşması BEKLENMEZ. Haftalık pencere "antrenman tamamen durdu"yu yakalar. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/sprint.py:944`
- Son damga: `state/mechanism_beats.json` → `sprint_cadence`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- `deploy/oracle-a1/tick_watchdog.sh` — başlığında `sprint_cadence` geçiyor.
- **BU OTURUMDA BULUNAN + ÇÖZÜLEN (kök nedenleriyle)** → **STATE ŞİŞMESİ + YEDEK KAPSAMI (2026-08-02 gece, Rol-1 + Opus; H10 turunun devredilen bulgusu — iki sınıf birden):** A1'de state/ 617M'in 438M'i = 4 sprint kum-havuzu × ~110M; gecelik tar 112,5M. İKİ AYRI KÖK NEDEN ÖLÇÜLDÜ: (1) SINIF "belgede donmuş boyut varsayımı" — `sprint.SKIP_COPY` yalnız `bars`ı atlıyordu; küme yazıldıktan SONRA doğan `bars_intraday` (43M) + `intraday_bars` (40M) her kum havuzuna sessizce kopyalanıyordu (83M = ~110M'in 3/4'ü; sprint çocuğunun yolunda okuyucuları YOK); docstring'in "~1.5 MB" iddiası 70× bayattı. Birikim SINIRSIZ DEĞİLDİ: SANDBOX_KEEP=3 + start()-anı budaması çalışıyor, kararlı durum 4 dizin. (2) Aynı sabahki 4×5dk damgaları KADANS KUSURU DEĞİL YENİ VAKA DEĞİL — C15'in (damga-ezme) canlı imzası: olay defterinde **154 `sprint_cadence_start`, HEPSİ `taze_aday_birikimi/taze=50/gecen_gun=0`**, tam 300sn poll aralığında, 06:00'da pencere kapanınca kesiliyor; canlı `sprint_status.json`'da `n_hyp_at_start` YOK (eski kod çocuğu eziyordu). Düzeltme (`_damgayi_koru`) 19:05 restart'ıyla ZATEN CANLIDA (A1 diskinde grep'le doğrulandı); ilk yeni sprint damgayı yeniden basınca kadans kendi kendini onarır — beklenti: bu gece 22:00'de TEK sprint, sonra haftalık taban. ÇÖZÜMLER: SKIP_COPY += {bars_intraday, intraday_bars} (çivi: test_sr4b, v45) · `meridian-backup.service` tar'ına `--exclude=state/sprint` (ölçülen: 112,5M → **40.497.179 bayt ~40,5M**; RUNBOOK B4/9 satır 5'in ~15M tahmini yanlıştı) + çift-yönlü kapsam çivisi (`test_backup_kapsami_sprint_haric_bars_dahil`, v174: sprint dışarıda + bars/seans-içi arşivler İÇERİDE kalmak zorunda) · kayıp beyanı birim yorumunda (sandbox `sprint_runs.jsonl` defterleri arşiv dışı — 2026-08-02'de 4/4 sandbox'ta zaten yoktu) · H7 tatbikat beyanı güncellendi (B4/6). Sıklık artışı BİLEREK yapılmadı (litestream defterin dakika-RPO'sunu taşıyor; bars günde bir değişiyor). Hedefli testler 74/74 + t3 yeşil.

## y4_collect {#y4_collect}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-sonrası toplama (insider delta + short interest) *(kaynak: `meridian/watchdog.py`)*
- ---- EK KADANSLAR --------------------------------------- *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:669`
- Son damga: `state/mechanism_beats.json` → `y4_collect`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **y4_collect kurtarma (WP-P, 2026-08-12):** damga toplama turunun SONUNDA koşulsuz atılır (scheduler.py:646) — iki ayak (Form 4 + FINRA kısa pozisyon) kendi korumasında, ayak arızası bayatlık ÜRETMEZ (`y4_insider_failed`/`y4_shortinterest_failed` uyarıları + `y4_collect` olayının insider_cagri/si_satir alanları ayak sağlığını taşır; anahtar/kota kısılması `atlandi` alanlarıyla kayıtlı — fmp_anahtari_yok/fmp_kota_blogu arıza değildir). Bayatlık = kadans HİÇ koşmadı (seans işlenmedi ya da süreç ölü) → günlük tur/süreç teşhisi. TÜKETİCİSİ BİLEREK YOK (scheduler.py'deki Y4 teşhis bloğu): bayatlığın bedeli karar değil PENCERE kaybıdır — 3 yıllık sınıflama penceresi dolmaz.

## validation_report {#validation_report}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık kanıt raporu (+2 gün pay) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:716`
- Son damga: `state/mechanism_beats.json` → `validation_report`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **validation_report kurtarma (WP-P, 2026-08-12):** haftalık kanıt raporu — SALT-OKUMA, hiçbir kapı etkilenmez (scheduler.py:685 olay beyanı); damga `state/validation_report.json` yazımından sonra (scheduler.py:682). Kontrol: dosyanın uretildi/hafta alanları + `validation_report_written` olayı. Ayak kendi korumasında düşerse (`validation_report_failed`) hafta İLERLER → yeniden deneme gelecek hafta; üçlü kadansın KENDİSİ düşerse (`weekly_validation_failed`) hafta yakılmaz → sonraki poll dener. Bayatlığın bedeli görünürlük: "hangi edge kanıtlanıyor?" tablosu eskir, karar bozulmaz.

## massive_verify {#massive_verify}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık grouped-vs-zincir tutarlılık ölçümü *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:732`
- Son damga: `state/mechanism_beats.json` → `massive_verify`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **massive_verify kurtarma (WP-P, 2026-08-12):** haftalık grouped-vs-zincir tutarlılık ölçümü — yazım kapısının (`massive.write_enabled`) DAYANAĞI; bayatlarsa kapı bayat kanıtla karar verir (`massive_verify_failed` uyarısının kendi beyanı). Kontrol: `state/massive_verify.json` (verdict/samples/max_dev) + `massive_verify_week` olayı. Anahtar yoksa ölçüm `atlandi: massive_anahtari_yok` ile atlanır ve damga HİÇ atılmaz — bu bayatlık arıza değil YAPILANDIRMA hâlidir (anahtar operatör kalemi). Ayak düşerse hafta ilerler → gelecek hafta; üçlü kadans düşerse (`weekly_validation_failed`) sonraki poll dener.

## shadowlaw_drift {#shadowlaw_drift}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık MEASURED_V3 kayma bekçisi *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:744`
- Son damga: `state/mechanism_beats.json` → `shadowlaw_drift`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **shadowlaw_drift kurtarma (WP-P, 2026-08-12):** haftalık MEASURED_V3 kayma ölçümü — kayma bulursa SABİT DEĞİŞTİRMEZ, yalnız `shadowlaw_variance_drift` uyarısı basar (scheduler.py:716 beyanı); türetilmiş marjların yenilenmesi KOD-TÜRETİLEMEZ, operatör + Rol-1 domain kararıdır. Sağlıklı hafta `shadowlaw_drift_ok` yazar; ölçüm düşerse `shadowlaw_drift_failed` ("marjlar sınanmadan yürürlükte" — bedeli bu). Kontrol: api teşhis bloğunun servis ettiği kayma özeti (scheduler.py:713 `_state` alanı) + olay defteri. Ayak düşerse hafta ilerler → gelecek hafta; üçlü kadans düşerse (`weekly_validation_failed`) sonraki poll dener.

---

# Sessiz hat sapmaları {#sessiz-hat}

Sessiz hat üç segmenti toplar: **bekçiler** (yukarıdaki mekanizmalar) · **kilitler** ·
**veri**. Kilitler burada Faz-6 kilit zinciri DEĞİLDİR: bunlar DURDURMA kollarıdır,
normal konumları kapalıdır ve açık olmaları bir sapmadır.

## soft_halt {#soft_halt}

### Belirti

- kol ÇEKİLİ *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- yeni giriş DURDU — kaldırmak için panoda Kademe 1 (Soft Halt) kolu *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **HALT_ACTIVE kurtarma (WP-P, 2026-08-10):** tek tetik api.py:4873 — panodan `/api/halt` (health.set_halt → `state/HALT`; bir sonraki muma kadar yeni alım yok, mevcut pozisyonlar yönetilir). Arıza değil OPERATÖR EYLEMİNİN kaydıdır: kolu kimin/ne zaman çektiği olay defterinde. Geri alma yine panodan: sağ üst DEVAM (Kademe 1 Soft Halt kolu) → `POST /api/resume`; telefonda `/panic` sayfası aynı halt/devam çiftini taşır (`soft_halt` sapması aynı kolu gösterir).

## halt_learning {#halt_learning}

### Belirti

- kol ÇEKİLİ *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- ship DURDU (işlem sürer) — Kademe 4 kolu; rollback güvenlik olarak açık kalır *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **halt_learning kurtarma (WP-P, 2026-08-12):** arıza değil OPERATÖR KOLUNUN kaydıdır — `state/LEARN_HALT` dosyası (health.py:26); kolu kimin/ne zaman çektiği `control_learn_halt` olayında. Etkisi: işlemler SÜRER, ship durur (reflect.submit erken döner — `submit_blocked_learn_halt` olayı, reflect.py:898) ve hermes ısınması duraklar (`_warm_skip="learn_halted"`, hermes_runtime.py:411); rollback güvenlik olarak açık kalır. Geri alma panodan: Müdahale kademeleri (kilitler#mudahale) Kademe-4 kolu → `POST /api/control/learn_halt` (api.py:2025; aynı uç aç/kapa).

## devre_kesici {#devre_kesici}

### Belirti

- günlük zarar kesicisi ATEŞLEDİ *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- kesici bir sonraki seansta kendiliğinden sıfırlanır — sıfırlanmıyorsa risk defterine bak *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **CIRCUIT_BREAKER kurtarma (WP-P, 2026-08-10):** tetik loop.py:1108 — OPEN işaretli günlük PnL `goal.limits.max_daily_loss_pct` eşiğini aştı (health.py:293); o gün yeni giriş yok (giriş kapısındaki `not breaker` şartı, loop.py:198 beyanı), pozisyon yönetimi sürer. ELLE KOL YOK — bilinçli: kesici dosya değil heartbeat alanıdır (`breaker_tripped`) ve bir sonraki seansta kendiliğinden sıfırlanır (`devre_kesici` sapmasının ipucuyla aynı hüküm; day_start_equity her işlenen barda tazelenir, loop.py:1221). Operatör: günün kayıp nedenini oku (pano kill yüzeyi → Kitap · şu an); ertesi seans sıfırlanmadıysa risk defterine bak.

## nabız {#nabız}

### Belirti

- nabız damgası OKUNAMADI *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- heartbeat.json yok ya da bozuk — worker hiç tur atmadı mı *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- `deploy/oracle-a1/tick_watchdog.sh` — başlığında `nabız` geçiyor.

## veri_kalitesi {#veri_kalitesi}

### Belirti

- data_ok=False *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- veri kalitesi kapısı düştü — karantina ve kaynak sağlığı kartı *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **KALICI RİSKLER / DERSLER** → **DATA_QUALITY kurtarma (WP-P, 2026-08-10):** 15 yol tek sınıf değildir — önce olay `detail`inden alt sınıfı ayır. Kapı hâli (loop.py:1068, `data_halt` → heartbeat `data_ok=False`; `veri_kalitesi` sapması aynı olgu): o gün yeni giriş kapalı, karantinadaki sembol işlem üretmez, tazeleme sabrı kendiliğinden dener — pano Sağlık → Veri hattı · bütünlük (saglik#veriboru) + `state/data_quality.json`. Elle onarımlı bilinen alt sınıflar: pano token'ı ASCII-dışı (api.py:40) → A1 `.dash.env` rotasyonu (deploy/oracle-a1/dash_token_credential.sh); sermaye beyanı kaybı (loop.py:806 reddin kaydı) → iade betiği ops/sermaye_beyani_iade.py.

---

# Betik dizini {#betikler}

Onaylı kümedeki her betiğin KENDİ başlık sözleşmesi, olduğu gibi. Kod bloğu içinde
veriliyor ki betiğin kendi biçimi (kullanım satırları, kurulum komutları) bozulmasın.

## `ops/barsarchive-run.sh` {#ops-barsarchive-run-sh}

```
ops/barsarchive-run.sh — mrd:bars:* → state/bars_intraday/ dayanıklı arşivcisinin OPS GİRİŞİ.

NEDEN BU DOSYA VAR (kopukluk avı, 2026-07-30): `meridian.barsarchive` yazılıp test edilmişti ama
hiçbir ops katmanından ÇAĞRILMIYORDU — yani Faz 5'in kanıt birikimi (dakikalık barların TTL'den
önce diske alınması) pratikte OPERATÖRÜN elle bir terminal açmasına bağlıydı. Redis ring'i ~2 seans
tutar: koşmayan bir arşivci "sonra toplarız" demez, o barlar TEMELLİ yoktur.

NEDEN serve.sh'ye EKLENMEDİ: arşivci panonun/worker'ın ömrüne bağlı DEĞİLDİR ve bağlı olmamalıdır.
serve.sh her çağrışında `stop_worker` ile süreç GRUBUNU indiriyor; arşivciyi oraya asmak, panoyu
her yeniden başlatışta bar akışını da kesmek olurdu. Ayrıca serve.sh'ye dokunmak bu turun sözüne
aykırıydı. launchd de YOK: ~/Documents TCC engeli (bkz. ops/com.meridian.agent.plist denemesi)
yüzünden bu depoda launchd zaten çalışmıyor — keepalive.sh'nin öğrettiği desen kullanıcı-oturumu
içinde nohup + pidfile'dır.

KULLANIM:  ./ops/barsarchive-run.sh start | stop | status | once
start  : arşivciyi ayrı bir süreçte başlatır (nohup, kabuk kapansa da yaşar)
stop   : pidfile sahibini durdurur (SIGTERM → barsarchive KeyboardInterrupt yolunda temiz kapanır)
status : koşuyor mu + arşiv özeti (YASA 6 tüketicisi: `--ozet`)
once   : tek tur koş ve çık (duman testi / cron); Redis yoksa çıkış kodu 2
```

## `ops/ci_duman.sh` {#ops-ci-duman-sh}

```
ci_duman.sh — CI DUMAN KAPISI (2026-08-15).

NEDEN VAR. Tam suite 4 çekirdekte ~50 dk sürer ve canlı-benzeri `state/` + lokal hermes-agent +
doğrudan ağ varsayar (ölçüm ve küme sınıflandırması: docs/MODUL-ENVANTERI-2026-08-15.md §5).
CI'ın 15 dk sınırı bu paketi HİÇ bitirememişti — her koşu zaman aşımıyla iptal oluyordu, yani
fiilen kapı yoktu. Bu betik CI'ın gerçekten BİTİREBİLECEĞİ, state-bağımsız duman kapısıdır.

BU TAM SUITE DEĞİLDİR VE ONUN YERİNE GEÇMEZ (CLAUDE.md kural 6: tam suite Rol-1'de tek-otoriter).
Yerel hızlı kapı ops/kapilar.sh'tır; bu betik onun CI ikizidir — farkları: bayt-derleme taban
kontrolü eklidir ve pytest kapsamı daha geniştir (CI'ın dakikaları vardır, operatörün saniyeleri).

SIRA ucuzdan pahalıya; AMA İLK KIRMIZI KOŞUMU DURDURMAZ. Dört kapının HEPSİ koşar, hepsinin
hükmü ekranda görünür ve kırmızılar sonda TEK bir `exit 1`e toplanır. Bu BİLİNÇLİ: bir turda
tüm kapıların durumu bir kerede görülsün — kısa devre yapan bir kapı, ikinci kırmızıyı bir
sonraki koşuma erteler ve turu gereksiz yere ikiye böler. Sıra yine de ucuzdan pahalıyadır,
çünkü ucuz kapının hükmü saniyeler içinde ekrana düşer (bekleme değil, okuma sırası).
[1] compileall   (~5 sn)   — beyan edilen Python tabanında (>=3.11) SÖZDİZİMİ. CI, venv'i
bilerek 3.11'e sabitler: 3.12+'da geçerli olup 3.11'de patlayan
sözdizimi (PEP 701 f-string vakası, 2026-08-15) burada yakalanır.
O vaka test TOPLAMASINI kesiyordu — tek satır, sıfır koşan test.
[2] lint-imports (~2 sn)   — 5 mimari sözleşme (pyproject [tool.importlinter]).
[3] uv audit     (~2 sn)   — tedarik zinciri. Gerçek bir açık bulunursa KIRMIZI: dağıtım da
PR de bekler. Alt-komut bu uv sürümünde YOKSA sonuç KIRMIZI değil
ÖLÇÜLEMEDİ'dir ve ekranda öyle görünür (aşağıdaki bloğa bak).
[4] pytest duman (~2-4 dk) — state-bağımsız çekirdek: anayasa property paketi (kapilar [3]
ile aynı 6 dosya) + modül-yasası audit ailesi + bounds/seed
çivileri + son regresyon sitesi. Ölçüldü (2026-08-15, 4 çekirdek):
390 test · ~1 dk 50 sn · 0 kırmızı.
BEKÇİNİN KENDİ TESTİ DE LİSTEDE (test_codelaw_kor_nokta_v214.py,
2026-08-16): `codelaw.report()["ok"]` bu turda üç önbelleğin körlük
sözleşmesine dayanıyor; sözleşmeyi kıran değişiklik kapıda değil
yalnız Rol-1'in tam suite'inde görünürse, aradaki her PR "kör
noktam yok" diyen bir bekçiyle birleşirdi. Dosya state'siz
(tmp_path + kaynak ağacı) ve +40 test / ~4 sn ekler.

LİSTE ELLE VE DAR TUTULUR — yavaşlayan kapı, atlanan kapıdır (kapilar.sh dersi). Dosya eklerken
iki şart: (a) taze klonda state'siz geçtiği kanıtlı, (b) toplam süre < 5 dk kalmalı.
```

## `ops/haftalik_mutasyon.sh` {#ops-haftalik-mutasyon-sh}

```
haftalik_mutasyon.sh — HAFTALIK MUTASYON TESTİ (WP-H/H5, 2026-07-31).

NE ÖLÇER. Kapsam ("bu satır koşuldu mu") ile SINAMA ("bu satır DEĞİŞSE test kırılır mı") aynı şey
değildir. Bu depoda 1300+ test var ve hepsi yeşil — ama yeşil bir suite, ölçmediği bir davranış
hakkında hiçbir şey KANITLAMAZ. Mutasyon testi tam olarak o farkı ölçer: kaynağa küçük bir kusur
enjekte eder ve suite'in onu yakalayıp yakalamadığına bakar. HAYATTA KALAN bir mutant, "burada
testlerin görmediği bir davranış var" demektir — yani bu depoda uydurma riskinin adresi.

NEDEN YALNIZ ÜÇ DOSYA (pyproject `[tool.mutmut] only_mutate`): para yolunun karar çekirdeği.
broker.py — pozisyon/risk/de-risk rampası    guard.py — parametre sınırları
score.py  — skor=para yasası
Tüm repoyu mutasyona uğratmak günler sürer ve sinyali seyreltirdi. Kapsam genişletme kararı
Rol-1'indir; genişletirken bu betiğe DOKUNULMAZ, yalnız pyproject'teki liste büyür.

NEDEN HAFTALIK VE ELLE: koşum SAATLER sürer (her mutant için suite'in ilgili kesiti yeniden
koşar). Bir kadansa bağlamak, gecelik pencereyi tek başına yerdi. Bakım ritüelinde koşulur.

KULLANIM:
./ops/haftalik_mutasyon.sh --kontrol   # HIZLI öz-test: mutmut yapılandırmayı GÖRÜYOR mu?
./ops/haftalik_mutasyon.sh --kisa      # KISA doğrulama: tek dosya + dar test seçimi, DAKİKALAR
./ops/haftalik_mutasyon.sh             # TAM koşum (SAATLER) → docs/mutasyon/<tarih>.md
```

## `ops/kapilar.sh` {#ops-kapilar-sh}

```
kapilar.sh — MERIDIAN KAPI ZİNCİRİ (WP-H/H4, 2026-07-31).

NEDEN TEK BETİK. Bu depoda üç ayrı kapı var ve üçü de ayrı ayrı çalıştırılabiliyordu — yani
pratikte hiçbiri düzenli çalışmıyordu. "Kapı var" ile "kapıdan geçildi" arasındaki fark, bu
deponun tekrar eden kusur sınıfıdır (fail-notify birimi kurulmuştu ama hiç ateşlenmemişti).
Tek çağrı, sabit sıra, ilk kırmızıda DUR.

SIRA GEREKÇELİ, keyfi değil — ucuzdan pahalıya VE dıştan içe:
[1] lint-imports  (~2 sn)  — mimari sözleşmeler. En ucuz ve en yapısal: bir yukarı-yön
bağımlılık doğduysa altındaki hiçbir ölçüm güvenilir değildir.
[2] uv audit      (~1 sn)  — tedarik zinciri. Kırmızıysa koşturduğumuz kodun kim olduğunu
bilmiyoruz demektir; test yeşilliği bunu telafi etmez. Alt-komut
bu uv sürümünde YOKSA hüküm KIRMIZI değil ÖLÇÜLEMEDİ'dir.
[3] pytest kapsamı(~30 sn) — anayasa yasalarının property paketi + doğrudan komşuları.

BU TAM SUITE DEĞİLDİR VE ONUN YERİNE GEÇMEZ. Tam suite turda BİR kez, Rol-1'de, tek-otoriter
koşar (CLAUDE.md §6). Bu betik "dağıtımdan önce hızlı sağlık" kapısıdır — geçmesi dağıtım için
GEREK şarttır, YETER şart değildir.

KULLANIM: ./ops/kapilar.sh          → üç kapı, ilk kırmızıda exit 1
./ops/kapilar.sh --hizli  → pytest kapsamını atla (yalnız [1]+[2]; ~3 sn)
```

## `ops/keepalive.sh` {#ops-keepalive-sh}

```
Meridian keepalive — kullanıcı-oturumu süpervizörü (launchd, ~/Documents'a TCC engeli yüzünden
kullanılamadı; bkz. ops/com.meridian.agent.plist denemesi). serve.sh bunu otomatik başlatır.
60 sn'de bir healthz yoklar; üst üste 2 kez ölü bulursa serve.sh ile diriltir + obs'a yazar.
Tekil örnek: pidfile + süreç kimliği doğrulaması. Eski muhafız salt `kill -0` idi: pidfile
reboot'u aşıyor ve keepalive düşük PID aldığı için bayat PID reboot sonrası BAŞKA bir sürece
denk gelebiliyordu (~%13, 2026-07-26 ölçümü) — muhafız sessizce çıkıyor, süpervizör alarmsız
yok oluyordu. Reboot'ta otomatik başlatma yine yok — operatör ./serve.sh çalıştırır (bilinen
sınır) — ama bayat pidfile artık o başlatmayı engellemez.
Elle durdurmak için pidfile'ı silmek yeter: sahiplik her turda denetlenir, örnek kendini kapatır.
```

## `ops/meridian-guard.sh` {#ops-meridian-guard-sh}

```
meridian-guard.sh — hermes-agent pre_tool_call KORUMA HOOK'u (Meridian, 2026-07-20).

Kapı yasasını HARNESS düzeyinde ZORLAR: ajanı yalnız-öneri diye prompt'la sınırlamak ricadır; bu hook
mekanizmadır. Ajanın terminal/dosya araçlarıyla Meridian'ın KORUNAN yüzeylerine dokunmasını SERT bloklar:
• state/ altına YAZMA (portfolio, strategy.yaml, goal.yaml, bounds.yaml — Hermes'e değişmez)
• secrets.json / API anahtarları
• MERIDIAN_MODE / MERIDIAN_I_ACCEPT_RISK / autonomy_level (gerçek-para kapıları — yalnız operatör)
• alpaca emir gönderimi / close_all / submit_bracket (canlı emir yetkisi)

Girdi: stdin'de JSON {tool_name, tool_input:{command|path|file_path|content}, ...}.
Çıktı: izin → {} ; blok → {"decision":"block","action":"block","reason":..,"message":..} (iki şema da).
Parse edilemezse fail-open (boş {}) — ajanı büsbütün kilitlemeyiz; asıl savunma desen eşleşmesidir.
```

## `ops/pull-a1-backups.sh` {#ops-pull-a1-backups-sh}

```
pull-a1-backups.sh — A1'deki state yedeklerini BU MAC'E çeker (VM-DIŞI kopya).

NEDEN VAR. `deploy/oracle-a1/meridian-backup.timer` her gün `/home/ubuntu/backups/state-*.tar.gz`
üretiyor — ama o dosyalar YEDEKLENEN MAKİNENİN KENDİSİNDE duruyor. Instance silinir/bozulur/
Oracle kotası kapanırsa yedek de gider. "Yedeğimiz var" cümlesi, yedek yalnız kaynakla aynı
kaderi paylaşan bir diskte duruyorken YANLIŞTIR. Bu betik o cümleyi doğru yapar: ikinci bir
fiziksel kopya, başka bir makinede, günde bir.

KURULUM (LaunchAgent, günde 1 kez — eşlik eden plist bu dizinde):
cp ops/com.meridian.backup-pull.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.meridian.backup-pull.plist
launchctl enable gui/$(id -u)/com.meridian.backup-pull
launchctl kickstart -p gui/$(id -u)/com.meridian.backup-pull      # elle bir kez dene
KALDIRMA:
launchctl bootout gui/$(id -u)/com.meridian.backup-pull
DURUM / LOG:
launchctl print gui/$(id -u)/com.meridian.backup-pull | head -30
tail -f ~/AI-Trading/backups/a1/pull.log

ELLE KOŞU:  bash ops/pull-a1-backups.sh          (ağ ister; ajan koşumlarında ÇALIŞTIRILMAZ)

AĞ DIŞI HİÇBİR ŞEYE DOKUNMAZ: yalnız okur (rsync pull) ve YEREL hedef dizine yazar. A1'de hiçbir
dosya değişmez, hiçbir servis durdurulmaz/başlatılmaz.
```

## `ops/state_yetim_temizle.sh` {#ops-state-yetim-temizle-sh}

```
state_yetim_temizle.sh — `state/` içindeki YEDEK ARTIKLARINI `backups/state/`e TAŞIR (silmez).

NEDEN VAR (MAKULLÜK bulgusu 1, 2026-08-07). `yeniden_hesap:orphan_state_files` canlıda 7 dosya
sayıyordu ve ALTISI bizim artığımızdı: `dagit.sh` versiyonlu state kopyasının yedeğini
`state/` İÇİNE yazıyordu (yani dedektörün taradığı dizine), bir de bakım penceresindeki bir
`sed` iki dosya bırakmıştı. Kaynak `dagit.sh`ta onarıldı (yedek artık `backups/state/`e gider);
bu betik ONARIMDAN ÖNCE DOĞMUŞ artıkları toplar.

TAŞIR, SİLMEZ. Bu dosyalar GERİ DÖNÜŞ KOPYALARIDIR: `goal.yaml.bak-202608021652`, canlı motorun
o dağıtımdan önceki yazılı yasasıdır. Silmek, geri dönüş yolunu kesmek olurdu. Taşımak dedektörü
susturmaya YETER (tarama `state/` dizinine bakar) ve kanıtı korur.

YALNIZ YEDEK SONEKLİ DOSYALAR — CANLI ARTEFAKT ASLA. Desen listesi ÖLÇÜLDÜ, uydurulmadı: canlıda
görülen artıkların tamamı bu üç sonektendir. Özellikle `auth.json` bu betikle TAŞINMAZ: dedektör
onu da orphan sayıyor ama o bir yedek değil, panonun CANLI kimlik dosyasıdır (kararı: kod
tarafında beyan — `codelaw.DECLARED_SINKS`). Taşınsaydı operatör panosuna giremezdi.

KURU KOŞU VARSAYILAN. Argümansız çağrı hiçbir şeye dokunmaz; yalnız ne yapılacağını yazar.

KULLANIM
bash ops/state_yetim_temizle.sh                 # A1'e SSH, kuru koşu (varsayılan)
bash ops/state_yetim_temizle.sh --uygula        # A1'de TAŞI (bakım penceresinde)
bash ops/state_yetim_temizle.sh --yerel <kök>   # SSH yok: verilen kökte çalış (test/host-içi)

CANLI WORKER: bu betik defterlere YAZMAZ, yalnız yedek dosyalarını YENİDEN ADLANDIRIR. Yine de
bakım penceresinde koşulması istenir — bir yedeği okurken taşımak (nadir de olsa) yarış üretir.
```

## `ops/stop-worker.sh` {#ops-stop-worker-sh}

```
stop-worker.sh — Meridian worker'ını (uvicorn + arkasındaki probe havuzu) SÜREÇ GRUBU bazlı durdurur.
Kullanım:  ./ops/stop-worker.sh           (elle durdurma)
source ops/stop-worker.sh      (serve.sh ve ops/supervise.sh böyle kullanır)

NEDEN grup-kill (2026-07-26 yetim sızıntısı vakası):
serve.sh uvicorn'u start_new_session=True ile açıyor → uvicorn kendi oturumunun ve süreç grubunun
LİDERİ oluyor, yani PGID == uvicorn PID. MERIDIAN_PARALLEL_PROBES=1 ile kurulan multiprocessing
havuzu (resource_tracker + 4 spawn işçisi) uvicorn'un çocuğu olarak AYNI gruba doğuyor.
Eskiden durdurma `pkill -f "uvicorn meridian.api"` idi: bu yalnız desene uyan lideri öldürüyor,
havuz üyeleri PPID 1'e düşüp günlerce yaşamaya devam ediyordu. 2026-07-26'da bu sızıntıdan
~75 yetim süreç ve 7.6 GB swap dolgusu birikti ve Redis'i boğdu. Doğru çözüm sinyali tek sürece
değil GRUBA göndermek: kill -- -PGID.
(Python tarafındaki atexit / ProcessPoolExecutor.shutdown savunması AYRI bir konu — burada kapsam dışı.)
```

## `ops/supervise.sh` {#ops-supervise-sh}

```
Meridian süpervizörü (launchd): çökmede otomatik yeniden başlatma + oturum açılışında başlama.
kur:    ./ops/supervise.sh install
kaldır: ./ops/supervise.sh uninstall   (sonra elle: ./serve.sh)

==============================================================================================
EMEKLİ YOL — VARSAYILAN OLARAK KURULMAZ (K1, 2026-07-30)
==============================================================================================
Bu yol BELGELİ OLARAK ÖLÜ ama kurulabilir durumdaydı ve kurulması AKTİF ZARARLIYDI. Üç sebep:

1) TCC ENGELİ: ops/keepalive.sh:2-3 kendi ağzıyla yazıyor — "launchd, ~/Documents'a TCC engeli
yüzünden kullanılamadı". Yol artık gerçek depoya symlink olsa da engel YOL ÜZERİNDEN aynen
geçerlidir. Fiilî süpervizör keepalive'dır (state/keepalive.pid canlı) ve ~/Library/
LaunchAgents'ta bu plist YÜKLÜ DEĞİL.
2) TOKEN KAYBI: `.env` yalnız MERIDIAN_DASH_TOKEN içeriyor ve onu YALNIZ serve.sh yüklüyor.
api.py token'ı yalnız environ'dan okur → launchd altında betik/CLI token yolu SESSİZCE ölür
ve her açılışta `dashboard_token_unset` uyarısı düşer. plist bir sır dosyası okuyamaz ve
token buraya GÖMÜLMEZ (sır repoya yazılmaz — güvenlik duruşu gevşetilmez).
3) KEEPALIVE'I DEVRE DIŞI BIRAKIR: serve.sh, launchd kuruluysa elle başlatmayı kilitler. Yani
install çalıştıran bir operatör, ÇALIŞAN süpervizörü çalışmayanla değiştirir.

İki süpervizör katmanı TEKLEŞTİ: kanonik olan keepalive.sh. Bu betik ve plist geri
alınabilirlik için duruyor (yollar da düzeltildi), ama install açık bir onay ister.
Bilerek denemek için: MERIDIAN_FORCE_LAUNCHD=1 ./ops/supervise.sh install
==============================================================================================
```

## `deploy/oracle-a1/bakim_h9.sh` {#deploy-oracle-a1-bakim-h9-sh}

```
bakim_h9.sh — H9 SQLite canlı geçişi + H3 sertleştirme + yedek-unit düzeltmesi + token rotasyonu
TEK BAKIM PENCERESİ. Ajan runbook'u (12 adım) + Rol-1 eklemeleri. Her adım doğrulamalı;
migrasyon paritesi tutmazsa TOPTAN geri alınır ve servisler DOSYA arka ucuyla yeniden başlar.
Kullanım: ./bakim_h9.sh          (uçtan uca; ~10-20 dk)
```

## `deploy/oracle-a1/cutover.sh` {#deploy-oracle-a1-cutover-sh}

```
cutover.sh — YEREL (Mac) tarafta koşar. Meridian'ı Mac'ten Oracle A1'e TEK KOMUTLA taşır.

bash deploy/oracle-a1/cutover.sh [-i <ssh-anahtarı>] <A1-IP>
örnek: bash deploy/oracle-a1/cutover.sh 130.61.126.87

SIRA KRİTİK ve bilinçlidir:
1) ön kontrol (IP + ssh erişimi + uzak rsync/curl)
2) YEREL süreçleri DURDUR (worker + arşivci + keepalive)      ← rsync'ten ÖNCE
3) rsync (repo, sonra state/)                                  ← durmuş süreçten TUTARLI görüntü
4) uzakta deploy.sh
5) pano token'ı (openssl rand)
6) doğrulama tablosu
2. adım 3.'den ÖNCE olmalı: koşan bir worker state/'e yazarken alınan kopya, yarım yazılmış bir
defterle A1'e gider (jsonl'ların ortasında kesik satır, portfolio.json ile trades.jsonl uyumsuz).

BU BETİK KESME KARARINI VERMEZ, UYGULAR. Koştuğu an yerel sistem DURUR.
```

## `deploy/oracle-a1/dash_token_credential.sh` {#deploy-oracle-a1-dash-token-credential-sh}

```
=================================================================================================
dash_token_credential.sh — pano token'ı: rotasyon + systemd LoadCredential geçişi (WP-H/H3 tur-3)
=================================================================================================
SUNUCUDA (A1) KOŞAR — `deploy.sh`/`cutover.sh` ile aynı sözleşme. Otomatik ÇAĞRILMAZ: bakım
penceresinde, operatör eliyle. Kayıttaki hüküm buydu: "rotasyon + LoadCredential'a taşıma AYNI
bakım penceresinde" — çünkü ikisini ayırmak, eski token'ın hâlâ geçerliyken yeni kanalın
doğrulanmasını imkânsız kılar (hangi kanalın çalıştığı ölçülemez, yalnız varsayılır).

NEDEN (kalan yüzey): sır artık 0600'lük `.dash.env`te (tur-1) ve birim dosyasında DEĞİL (tur-2).
Kalan yüzey SÜREÇ ORTAMIDIR: `serve.sh:51` uvicorn'u `env=os.environ` ile, `hermes_composite.py`
ajan alt süreçlerini devralınan ortamla doğurur — token her birinin `/proc/<pid>/environ`ında.
LoadCredential sırrı ortama HİÇ koymaz. Gerekçenin tamamı: meridian.service.d/50-*.conf.

KULLANIM:
./dash_token_credential.sh              → DURUM (hiçbir şey değiştirmez; önce bunu koş)
./dash_token_credential.sh --faz1       → rotasyon + credential kanalı EKLE (ortam kanalı KALIR)
./dash_token_credential.sh --faz2       → ortam kanalını KAPAT (faz-1 + uygulama tarafı şartlı)
./dash_token_credential.sh --geri-al    → her iki drop-in'i kaldır, ortam kanalına dön
```

## `deploy/oracle-a1/deploy.sh` {#deploy-oracle-a1-deploy-sh}

```
deploy.sh — Meridian'ı Oracle Cloud Always Free Ampere A1 (aarch64 Ubuntu) üzerine kurar.
A1 ÜZERİNDE, repo /opt/meridian'a kopyalandıktan SONRA çalıştır. Idempotent: tekrar koşulabilir.

ssh ubuntu@<A1-IP>
sudo mkdir -p /opt/meridian && sudo chown ubuntu:ubuntu /opt/meridian
# (yerelden) rsync -az --exclude .venv ./ ubuntu@<A1-IP>:/opt/meridian/
cd /opt/meridian && bash deploy/oracle-a1/deploy.sh

Not: normalde bu betiği ELLE koşman gerekmez — yereldeki cutover.sh (aynı dizinde) durdurma +
rsync + bu betik + token + doğrulama sırasını tek komutta yürütür.
```

## `deploy/oracle-a1/litestream_kur.sh` {#deploy-oracle-a1-litestream-kur-sh}

```
litestream_kur.sh — Litestream'i A1'e SÜRÜM-SABİTLİ + SHA256-KAPILI kurar (WP-H / H10 aşama-1).

NEREDE KOŞAR: **A1'de**, /opt/meridian içinden. Mac'ten değil (ikili aarch64-Linux'tur).
NE ZAMAN KOŞAR: bakım penceresinde, RUNBOOK "Bölüm B4" prosedürünün adımı olarak. Bu betiği bir
AJAN KOŞMAZ — canlı defterin şemasına dokunan ilk `start`ı operatör açar (aşağıda `--baslat`).

İDEMPOTENT: iki kez koşmak hiçbir şeyi bozmaz. Doğru sürüm zaten kuruluysa indirme ATLANIR;
yapılandırma/birim dosyaları AYNIYSA "değişmedi" der ve dokunmaz; `enable` zaten etkinse geçer.

==================================================================================================
TEDARİK-ZİNCİRİ KAPISI (H2 ruhu — `uv audit` neyse bu da o)
==================================================================================================
Bu betik depo dışından bir İKİLİ indiriyor: Python paketlerine uyguladığımız kapıyı ona
uygulaMAMAK, kapıyı en zayıf halkadan delmek olurdu. Üç kilit:
1. SÜRÜM SABİT (`LS_SURUM`) — "latest" YASAK. `latest`, dünkü denetimden geçmemiş bir ikiliyi
yarınki koşumda sessizce canlıya sokar.
2. SHA256 SABİT (`LS_SHA256`) — yayıncının `checksums.txt`inden 2026-08-02'de alındı. İndirme
ile eşleşmezse betik DURUR ve dosyayı SİLER; "belki ağ bozdu" diye tekrar denemez.
3. MİMARİ KAPISI — `uname -m` aarch64 değilse durur (yanlış ikili "çalışmıyor" diye değil,
"exec format error" diye ölürdü ve bunu birim journal'ında aramak saatler yerdi).
SHA256 YENİLEME (sürüm yükseltirken): yayıncının checksums dosyasından okunur —
curl -sSL https://github.com/benbjohnson/litestream/releases/download/v<SÜRÜM>/checksums.txt
Sabit ELLE güncellenir ve turun commit'ine girer; betik onu İNTERNETTEN TAZELEMEZ (tazeleseydi
kapı kapı olmaktan çıkar, "indirdiğimi indirdiğimle doğruladım" totolojisine dönerdi).
```

## `deploy/oracle-a1/tick_watchdog.sh` {#deploy-oracle-a1-tick-watchdog-sh}

```
tick_watchdog.sh — ASILI-TİCK bekçisinin GÖVDESİ (küçük-kuyruk turu, 2026-08-02).

================================ NEDEN AYRI DOSYA ============================================
Bu mantık 2026-07-31'de birim dosyasının `ExecStart=/bin/bash -c '...'` satırının İÇİNE
yazılmıştı ve ÖLÜYDÜ. Kanıt (A1, salt-okuma ölçüm 2026-08-02 19:46 UTC):
journalctl -u meridian-tick-watchdog.service
Aug 02 19:32:34 (bash)[10835]: meridian-tick-watchdog.service:
Referenced but unset environment variable evaluates to an empty string: YAS
Aug 02 19:32:34 bash[10835]: [tick-watchdog] ilerleme var (s)
`(s)` yazması `(${YAS}s)`nin boş genişlemesidir: systemd, ExecStart satırındaki `$YAS`/`${YAS}`
dizgelerini bash'e VERMEDEN ÖNCE kendi ortam sözlüğünden ikame eder; sözlükte yoktur, boş dizge
koyar. Bash'in gördüğü karşılaştırma `[ "" -gt 10800 ]` olur, "integer expression expected" ile
düşer ve akış HER ZAMAN else dalına gider. Yani bekçi kurulduğu günden beri HİÇBİR restart
yapamazdı — 45 dk mı 3 sa mı tartışması bu kusurun yanında ikincildir.
SINIF: "birim dosyasında kabuk-sözdizimi varsayımı" — fail-notify'ın çok-satır-Python vakası
(2026-07-30) ve `Environment=` satır-sonu yorumu vakasının (2026-08-02) ÜÇÜNCÜ kuşağı. Kalıcı
ders bu üçünden çıkar: systemd birimi bir kabuk betiği DEĞİLDİR; mantık ayrı bir dosyada yaşar,
birim yalnız o dosyayı çağırır. Bu dosya kabuk tarafından okunur, `$` ikamesi bash'indir.

============================== EŞİK: 45 DK (KALICI) ==========================================
ÖNCEKİ DEĞER 10800 sn idi ve birim açıklamasında "3sa-GECICI(ilk-tam-tick; sabah 45dk-normale
döner)" yazıyordu. "Sabah" 2026-07-31'di; etiket 2026-08-02'ye kadar durdu. Artık KALICI 2700.
ÖLÇÜM (A1 canlı olay defteri + systemd journal, 2026-08-02, salt-okuma):
* NORMAL İŞLEYİŞ: son 24 saatte poll işaretlerinin (finviz_unavailable · candidate_review_backlog
· sprint_cadence_*) 513 damgası — medyan aralık 300 sn, p95 301 sn, MAKSİMUM 302 sn (5,0 dk).
45 dk bunun 8,9 KATIDIR. Yanlış alarm payı geniş.
* KURUCU VAKA: 2026-07-30 21:14→22:27 UTC asılı-tick — ölçülen sessizlik 73,1 dk. 45 dk bunu
YAKALAR; eski 10800 sn (3 sa) YAKALAMAZDI. Yani "geçici" gevşetme, bekçiyi tam da onu var
eden vakaya karşı kör bırakmıştı.
* İKİ EK İLERLEMESİZ PENCERE (aynı ölçüm, systemd'de restart YOK — süreç ayaktaydı):
2026-07-31 00:16:16→01:56:32 = 100,3 dk ve 2026-07-31 20:12:58→21:37:32 = 84,6 dk.
İKİSİ DE AYNI kod bölgesinde: `earnings_refreshed` olayından `arming_measured` olayına.
Bunlar "yavaş ama çalışan kadans" DEĞİL, tekrar eden bir takılmadır (kök neden ayrı tur —
günlükteki `earnings.refresh` ağ-nondeterminizmi kalemiyle aynı bölge). 45 dk'lık kapı bu
pencerelerde ateşlenir ve bu DOĞRUDUR: kadans damgaları ilerlememiştir, restart sonrası
sonraki poll onları yeniden koşar.

============================ NABIZ SÖZLEŞMESİ (v186, 2026-08-04) =============================
Uzun süpürmeler (bar yükleme/onarım, sip düzeltmesi, hacim kalibrasyonu, kazanç takvimi, tarama)
artık YİNELEME BAŞINA bir İLERLEME NABZI atar ve nabız bu betiğin okuduğu damgayı tazeler
(`meridian/scheduler.py` → İLERLEME NABZI bloğu; nabız = `_persist()`, yeni bir biçim yok).
NEDENİ: 2026-08-03 20:00→23:30 UTC'de bu bekçi meşru-uzun bir EOD döngüsünü ÜÇ kez öldürdü —
döngü asılı değildi, damga yalnız döngü SONUNDA yazılıyordu. HÜKÜM: eşik YÜKSELTİLMEZ, NABIZ
EKLENİR. Gerçekten tek bir çağrıda asılan bir döngü hiçbir yinelemeyi bitiremez, nabız atmaz ve
aşağıdaki 2700 sn eşiği onu ESKİSİ GİBİ yakalar.

========================= SEANS FARKINDALIĞI: ÖLÇÜLDÜ, GEREKSİZ ==============================
Brief'in sorusu: hafta sonu tick yok — 45 dk sahte alarm üretir mi? ÖLÇÜM: HAYIR, ve bu yüzden
takvim/mcal bağı EKLENMEDİ (gereksiz bir bağımlılık uydurmak çözüm değildir).
* Ölçülen 24 saatin TAMAMI seans dışıdır (2026-08-02 Pazar) ve maksimum poll aralığı yine
302 sn çıktı.
* MEKANİZMA (koda karşı doğrulandı): `scheduler.advance_once()` seans dışında "güncel" dalına
düşer ve o dal `_persist()` çağırır (scheduler.py:976) — yani `scheduler_status.updated`
seanstan BAĞIMSIZ olarak her poll'de (300 sn) tazelenir. `_run()`un istisna dalı da
`updated` yazar (scheduler.py:1051). Seans dışı olmak damganın DURMASI demek değildir.
* CANLI KANIT: 2026-08-02 19:46:50Z ölçüm anı · scheduler_status.updated = 19:45:59Z → yaş 51 sn.

============================ YAS (YENİDEN-BAŞLATMA-SONRASI) ==================================
Yeniden başlatmadan hemen sonra `scheduler_status.json` HÂLÂ eski `updated`ı taşır (yeni süreç
onu saniyeler içinde tazeler, ama "saniyeler" > 0). Zamanlayıcı o aralığa denk gelirse taze
doğmuş bir süreci bayat sanıp yeniden başlatır — ve bu KENDİNİ BESLEYEN bir restart döngüsüdür.
Bu yüzden servisin systemd'den okunan AYAKTA KALMA SÜRESİ eşiğin altındaysa hüküm VERİLMEZ.
Sinyal uydurma değil ölçülmüştür: `ActiveEnterTimestamp` = 2026-08-02 19:05:18 UTC, aynı anın
journal satırı "Started meridian.service" = 19:05:18 — birebir.
```

---

# Bilinen sınıflar ve açık kalanlar {#siniflar}

`MERIDIAN_ENGINEERING_LOG.md`'den olduğu gibi taşınır. Bir alarmın açıklaması burada
olabilir: bu depoda tekrar eden şey tek tek hatalar değil, HATA SINIFLARIDIR.

## AÇIK KALANLAR (bilinçli, sahipli) {#acik-kalanlar}

- **DAĞITIM KUYRUĞU (2026-08-02 gece, state-şişmesi turu):** (a) **KAPANDI (aynı gece ~20:50 UTC, operatör talimatlı pencere):** birim A1'e kuruldu (sha256 doğrulamalı scp + geri-alma yedeği `~/meridian-backup.service.bak-20260802` + sudo cp + daemon-reload) ve İKİ kez elle test-ateşlendi — ikinci koşum: Result=success, journal temiz, tar **40.593.530 bayt** (`state/sprint/` 0 üye · `state/bars/` 261 · `meridian.db.yedek` 1 · 0600). İlk ateşleme ayrıca H9'dan beri sessiz bir arızayı yakaladı (aşağıdaki yeni vaka). Mac'teki geniş 2026-08-02 kopyası (112,5M) bilerek korunuyor; 23:30 timer'ı bu gece dar birimle koşacak. (b)+(c) **KAPANDI (aynı gece 21:27–22:07 UTC, operatör talimatlı CERRAHİ dağıtım — gerekçe ve ölçümler §BU OTURUMDA "STATE-ŞİŞMESİ TURU KAPANIŞI"):** `sprint.py` (iki turun birleşik içeriği, sha 8b9b6baa…) tek dosya olarak A1'e indi (yedek `~/sprint.py.bak-20260802-2`), worker 21:27'de restart (yalnız meridian; barsarchive kesilmedi). İlk sprint operatör talimatıyla `/api/sprint/start` override'ından 22:04:08'de doğdu (kadans `mesgul:canli_arama`da bekliyordu — v181'in ölçtüğü %99,9 CPU arama vakası). ÖLÇÜMLER: sandbox **30 MB** (~27M türetimi doğrulandı; dökümde bars_intraday/intraday_bars/çıplak meridian.db YOK) · `phase=baseline, total=523, progress 0→1` (22:04:17→22:06:50) — 60sn ölüm deseni KIRILDI · `n_hyp_at_start=51` status'ta ve çocuk yazımı ezmedi (C15 canlı kanıt) · budama en eskiyi sildi (4 dizin). n_v1 TIRMANIŞI DA ÖLÇÜLDÜ (22:11:40 okuması): `progress 9/523, n_v1=1` — **migrasyondan (07-22) beri İLK sıfır-üstü n_v1**; süreç canlı (%99,3 CPU), hız ~1,7 seans/dk → tam baseline ~5 saat. KALAN (sabah kontrolü): final n_v1 + Faz B'de `sprint_runs.jsonl` doğumu. ÇATAL BEYANI AYNEN YÜRÜRLÜKTE: iki-motor giriş yasası (0a4453f) 07-22'den beri dolumları sıkılaştırdı — n_v1 100'ün altında kalabilir; 522 seansta <30 çıkarsa bu YENİ ve DÜRÜST bir bulgudur ("modern yasada eval-penceresi kuraklığı", ayrı tur + gerekirse kart) — min_sample GEVŞETİLEREK "çözülmez". Gecelik tar da elle ateşlemeyle YENİDEN doğrulandı (22:05, sprint KOŞARKEN): Result=success, journal temiz, `.yedek` tazelendi, tar **40.598.037 bayt** (koşan sandbox dahil `state/sprint/` 0 üye · bars 261 · db.yedek 1). KÜÇÜK KALEM (temizlik turuna): `meridian.db.yedek` (2M) sandbox'a kopyalanıyor — SKIP_COPY adayı, okuyucusu yok.
- **SPRINT DÖNGÜ KAPATAMIYOR — n_v1=0: KÖK NEDEN ÖLÇÜLDÜ, DÜZELTME HAZIR (2026-08-02 gece; ayrıntı §BU OTURUMDA):** kuraklık değil izolasyon deliği (DB kopyası reset'i görünmez kılıyor, monotonluk bekçisi 522/522 reddediyor). Kod + çiviler bu commit'te; canlıya İNİŞ yukarıdaki dağıtım kuyruğu kalemi (c). md.2 "sprint noktaları ↑" sayacı restart + ilk başarılı sprint'e kadar akmaz. Kalan küçük kalem (sahipsiz bırakılmadı, düşük öncelik): prescreen/mutation'ın sıcak-WAL kopya riski — temizlik turuna not.
- **DAĞITIM BLOKE — ÇÖZÜLDÜ (2026-08-02: yeşil suite 3752/0 donmuş tepede → pencere 14:00 UTC → adım-7 doğrulaması yeşil; ayrıntı §DAĞITIM PENCERESİ PLANI). Tarihçe aynen korunuyor:** operatör KOVA-B dağıtımını açtı; dagit.sh kapıları (audit+lint-imports) yeşildi ama dağıtım-öncesi tam suite 16 failed / 2 error / 3688 passed verdi → --uygula KOŞULMADI, canlı eski kodda. Ayrıştırma: (a) 7'si İZOLE de kırmızı = GERÇEK; bunlardan RUNBOOK eşitliği (uiux t3) yeniden-üretimle kapandı; kalan 6'sı test_learning_roundtrip_v76 — fikstür kanıt tabanı 17 < min_sample 30 → par_score None → rollback zinciri kademeli çöküyor ("örneklem kuraklığı → no_parent_score" sınıfı). Tarihleme DÜZELTİLDİ (ilk iddia "≤90a6663" HATALIYDI — kıyas ağacı rebase sonrası olduğundan ayrıştırıcı değildi; bisect ile kesinleşti): kök 0a4453f (iki-motor C11/C18) — replay giriş limiti canlıyla aynı yasaya sıkılaştı (min(0,5·ATR14, %1); eskiden ATR'siz daima %1), v76 sentetik fikstürünün kanıt tabanı 17 < min_sample 30'a düştü, 6 arıza bundan kademeli (score→None zinciri). Üretim değişikliği DOĞRU; onarım fikstürde (tur açık, Opus uçuşta) — eşik/assert GEVŞETİLMEZ. (b) GİRİŞİM AVI KAPANDI (2026-08-02 gece, diğer oturum) — iki hüküm, ikisi de çürütmeli: (b1) SIZINTI İPUCU YANLIŞ ALARMDI: taze worktree'deki `bounds.yaml`+`goal.yaml` test artığı değil GIT ÇIKIŞI — c783442 .gitignore ölü-negasyonunu düzeltip ikisini BİLEREK versiyona almış (ve o commit ipucu ağacının atası); `--collect-only` provası doğruladı: dosyalar checkout anında var, hiçbir test koşmadan. v72 ailesinin "yaşayan kanıtı" iddiası GERİ ÇEKİLDİ. (b2) 9'LU AİLENİN GERÇEK KİMLİĞİ: suite-içi sızıntı DEĞİL, YÜRÜYEN-AĞAÇ ARTEFAKTI. İlk tam-suite koşusu (8,5 dk) sırasında paralel merge main'i a75a207→0170cc0 taşıdı; 9'un tamamı kaynak-tarayan yapısal test (inspect.getsource) ve import-edilmiş modül ile diskte yeniden yazılan kaynak ayrıştı. Kanıt zinciri: imza tipi tekdüze · sıra eklentisi yok (alfabetik koşu, v76-zehirlenmesi imkânsız — gate_statistics/kovab_yapi v76'dan ÖNCE koşar) · statik ağaçta 4/4 koşu temiz (46ce02f otoriter, da6bec3 izole, ve ÇÜRÜTME KOŞUSU: a75a207 STATİK yeniden-koşumda 9'dan SIFIRI ateşlendi; çıkan 10 kırmızı = o ağacın bilinen gerçekleri [6×v76+t3] + 2 düzenek artefaktı [c1-tombstone; güncel goal.yaml'ı (C24 anahtarlı) eski koda bindirince gu1b/authority-c3 — ayrıca ders: tarihi ağaca güncel tracked-state kopyalama GU1-sınıfı sahte kırmızı üretir]). DERS (pencere planı adım 3'ü genelleştirir): OTORİTER SUITE YALNIZ DONMUŞ AĞAÇTA — sha'ya sabitlenmiş worktree veya freeze; merge alan bir checkout'ta koşan suite hüküm değil gürültü üretir. Çıktı: full_suite_a75_static.txt. SIRA: v76 fikstür onarımı ✓ → girişim avı ✓ → yeşil suite ✓ (3752/0, donmuş tepe) → dağıtım ✓ (pencere 14:00 UTC). Çıktılar: scratchpad/full_suite_predeploy.txt. GÜNCELLEME (2026-08-02 akşam, Rol-1): icra-bloğu merge'i (46ce02f) sonrası otoriter koşu 7 kırmızı = 6×v76 + uiux-t3 (t3 892bf75 ile kapandı); girişim ailesi o koşuda ateşlenmedi. Pencere planı: §DAĞITIM PENCERESİ PLANI.
- **BT-2 YENİDEN AÇILDI (trend-kolu ölçümünün yan bulguları, 2026-07-31 ~02:30):** BULGU-1: karantina hacim-şartı gerçek hayalet sınıfının %29'unu kaçırıyor (10 kaçak ×2-ölçek satırı: GILD/CMCSA 2013-12-18, DLTR, UNP). BULGU-2: kapıdan geçen 97 çözülmemiş ölçek/kimlik kırılması (59 sembol: CHTR ×1158!, AVGO ×162, PINS kuruş-geçmişi, ABT/DD/HON spinoff'ları, TDG bozuk kesiti). component_ic/cf/R-tabloları hâlâ şüpheli → hayalet-round-2 turu (SIP kolu data.py'yi bırakınca): karantina şartı genişlet + 97'lik envanter → barrepair-2 + türetilmiş artefaktlar yeniden. Trend ölçümünün hükmü bu kirlilikten BAĞIMSIZ doğrulandı (katman kapalıyken de aynı) ama sistem-geneli tablolar için acil.
- **TREND KOLU: İLK SAĞ KALAN AİLE** — ayrıntı research/cards/README; ders: ön-kayıtlı pozitif kontrol tek-enstrümanlıysa portföy-yolu hatalarına yapısal kör (PK4/PK5 yol-tutarlılık kontrolleri standart olmalı — ölçüm-şablonu iyileştirmesi).
- **ASILI-TİCK VAKASI (2026-07-30 21:14→22:27 UTC; sınıf: "canlılık ≠ ilerleme"):** worker çöküp yeniden doğdu ve yeni beden açılışta futex'te asıldı; uvicorn 503 CEVAPLIYORDU ama tick ilerlemiyordu — watchdog tick İÇİNDE olduğundan sustu, OnFailure süreç ölmediği için ateşlemedi. Restart çözdü (operatör gece yetkisiyle). KALICI KORUMA KURULDU+TEST-ATEŞLENDİ: `meridian-tick-watchdog.timer` (15 dk'da bir; scheduler_status.updated>45dk bayat → restart). İLK IEX-BACAK KANITI aynı dakikada: `alpaca_session_bars feed=iex asked=253 answered=252` — seans tek çağrıda geldi. sip bugün-için-403 beklenen (SIP-düzeltmesi sabah dağıtımında).
- **GECE VARDİYASI SONUCU (2026-07-31 ~03:15 — dağıtım TAMAM):** 6 kod kolu + 7 ölçüm hükmü indi; suite 0 kırmızı; A1'de canlı: iki-motor icra yasası, sip-geçmiş kuralı (ilk kanıt: skipped_current olayı), damga-migrasyonu (95/95 seed; gerçek-canlı sayaç 0'dan), karantina-v2 (8 defter onarımı), bütünlük defteri (61 sembol), regime entry_gates üreticisi, tick-bekçisi. BEKLEYEN ÖLÇÜMLER: WP-R rampa-P3 (K=4) + SMA/ToM — hükümleri geldiğinde kartlara işlenecek. SABAH KALEMLERİ: onarım soğuma-içi-bekleme düzeltmesi · bekçi eşiği 3sa→45dk normalizasyonu · türetilmiş artefaktların güvensiz-dönem-dışlamalı yeniden üretimi (gecelik P5 + bars_integrity artık canlı) · skor kartı yeniden-puanlama · operatör karar listesi (§1'de).
- (eski vardiya planı — arşiv): Koşan: BT-1(damga+atribüsyon; bitince→WP-E ajanı EXE-2026-001 kartıyla) · hayalet-round-2 · WP-R rampa-P3 ölçümü (kart EDG-003) · MAX ölçümü (EDG-004) · WP3.1 doğrulama filosu · PIT-kaynak araştırması · A1 monitör-v2 (PID yerel, çıktısı tasks/b226ui034.output). SIRA: kollar indikçe → TAM SUITE → A1 dağıtımı (SIP-düzeltmesi+pano+BT-1+round-2 birlikte; restart yetkili) → EDG-005 SMA ölçümü → WP-M konsolide ajanı (kapasite kalırsa) → SABAH KONSOLİDASYONU (ROADMAP §1/§2 tazele, K-defteri↔kartlar senkron, gece karnesi raporu).
- **EDGE ARAŞTIRMA PROGRAMI ROADMAP §3.0b'de (operatör onaylı, filo-sentezli):** çıkış paketi (ölçüm koşuyor) → alfa/beta kablolama → mid-cap momentum yeniden-ölçümü (G1 çelişkisi kayıtlı) → katalizör-koşullandırma → insider hükmü (EDGAR koşuyor) → karşı-taraf istem satırı. ERTELENDİ: ısı tavanı (vol-yönetimi edge yaratmaz, paketler — pozitif-EV önkoşulu). YAPMA: klasik PEAD large-cap'te (Martineau + Subrahmanyam: 2006'dan beri ölü, mikro-cap hariç t=1,43). Canlı TCA canlıya geçişte ($6,12 paper-modeli; retail bandı 7-46bps → 2-4× kötüleşebilir).
- **Sıradaki turlar:** temizlik turu (14 emekli + 19 kablola + 13 operatör-kalemi belgesi; öğrenme ajanı inince — dosya çakışması) · pano/UX turu (§3.0'daki 10 kalem) · yarın sabah TEK dağıtım (keşif-dengesi + öğrenme-otomasyonu + temizlik + emekli-sembol restart'ı birlikte).
- **"Zaman varsayımı" sınıf avı eksik:** T+1 kusurunun sınıfı (kodda örtük yayın-zamanı/TTL varsayımları) repo genelinde sistematik taranmadı. Aday: bararchive Redis TTL, earnings takvim tazeleme, finviz keşif zamanlaması. → temizlik turuna ek mercek.
- **Yama-değil-çözüm borçları:** IEX hacim kalibrasyon oranları İLK T+1 düzeltmesine kadar boş (yedek katman o gece kör — bilinçli, damgalı) · emekli-sembol modülü A1'de diskte ama koşan süreçte değil (yarınki restart'a kadar payda 259) · monitörün başarı koşulu last_processed bekliyor (bu gece 07-29+07-30 birlikte işlenebilir — yorumda dikkat).
- **Operatör kalemleri:** bildirim kanal kimliği (TELEGRAM_*/MERIDIAN_WEBHOOK_URL — girilene dek fail-notify beyanlı no-op) · NOUS_MODEL · FISV/PSKY halef kararı · Faz-6/silahlanma onayları · 1.4 karar kapısı.
- **Ölçüm borçları:** hotstate_down çırpınması temiz Redis'te yeniden ölçülecek · R1 damgaları + PBO tabanı birikiyor (taban 0/204) · Katman C saha kanıtı · gölge-v2 kitaplarının ilk satırları.
- **GOAL_FAILURE kurtarması KOD-TÜRETİLEMEZ — operatör domain kararı gerekir (WP-P, 2026-08-10, bilinçli açık):** tetik watchdog.py:1696 — `goal_failure_report` (watchdog.py:1647): 30g gerçekleşen getiri `goal.yaml failure_below` eşiğinin altında (mandallı — düşüşte bir kez; örneklem min_sample altındaysa hüküm None, alarm yok). Bu sözleşmenin BAŞARISIZLIK HÜKMÜdür; onu "kurtaracak" betik/endpoint yoktur ve olmamalıdır — deneyin akıbeti (durdur / param revizyonu / goal.yaml değişikliği) operatör mandasıdır. Kontrol: olay alanları realized_30d/threshold/n + pano bütünlük yüzeyi; goal.yaml İZLİ (dagit [1b] SSoT), değişiklik ayrı turdur.

## KALICI RİSKLER / DERSLER {#kalici-riskler}

- Waiter/ajan-içi bekletici YASAK (iki arıza). Tam suite turda BİR kez, ön planda, senkron.
- file_lock süreç-içi; canlı worker koşarken state'e ikinci süreçten yazma.
- rsync dağıtımı tüm repoyu taşır — yarım iş canlıya gidebilir; önce dry-run + mtime.
- Sınıflandırıcı curl|sh'ı engeller → kurulumlar PyPI/pipx veya sabitlenmiş git klonuyla.
- classifier/API kesintilerinde: salt-okuma araçlarla devam + zamanlayıcılı yeniden deneme.
- pytest `-qq` tuzağı (2026-08-02): pyproject `addopts = "-q"` zaten veriyor; komuta fazladan `-q` eklemek `-qq` yapar ve "N passed" özet satırını TAMAMEN bastırır — yeşil koşu hiçbir şey basmaz, triyaj `grep -E "FAILED|ERROR"` + özet satırı ikisine birden bakar. pytest'i `-q`suz çağır.
- venv ana repo kökünde (`/Users/erdemozturk/AI-Trading/.venv`, py3.12 + pytest); worktree'lerde YOK ve sistem `python3` (3.14 homebrew) pytest içermez → testler `.venv/bin/python -m pytest` ile.
- **HEARTBEAT_STALE kurtarma (WP-P, 2026-08-10):** jeton bugün ÜRETİCİSİZ — tek üreticisi eski `run.py` worker döngüsüydü, emekli (beyan: meridian/run.py:34). Yeni bir kaydı görmek "eski bir yapı koşuyor" demektir: `state/events.jsonl` kaydının sürecini/sürümünü doğrula (A1'de `journalctl -u meridian`). Döngü canlılığının gerçek bekçileri: A1 `meridian-tick-watchdog.timer` (deploy/oracle-a1/tick_watchdog.sh — scheduler damgası 45 dk bayatlarsa restart) + yerelde `ops/keepalive.sh` (healthz 60 sn'de bir; üst üste 2 ölü → süreci diriltir).
- **ROLLBACK kurtarma (WP-P, 2026-08-10):** iki hâl, olay `detail`inden ayrılır. (a) rollback.py:253 = geri alma UYGULANDI (çocuk ebeveynden `rollback_if_worse_by` kadar kötü) — eylem gerekmez, kayıttaki from_version/to_version + karar_* alanları hükmün kanıtı. (b) rollback.py:221 = geri alma BAŞARISIZ: `state/history/vNNNN.yaml` ebeveyn anlık görüntüsü yok, KÖTÜ sürüm CANLI kalıyor. Kurtarma: dosyayı state yedeğinden geri koy (Mac `backups/a1/` — ops/pull-a1-backups.sh çeker; A1 `/home/ubuntu/backups/state-*.tar.gz`) — bakım penceresinde (canlı worker koşarken state'e yazılmaz); dosya gelince sonraki değerlendirme (loop.py:1717) geri almayı kendiliğinden yeniden dener.
- **CIRCUIT_BREAKER kurtarma (WP-P, 2026-08-10):** tetik loop.py:1108 — OPEN işaretli günlük PnL `goal.limits.max_daily_loss_pct` eşiğini aştı (health.py:293); o gün yeni giriş yok (giriş kapısındaki `not breaker` şartı, loop.py:198 beyanı), pozisyon yönetimi sürer. ELLE KOL YOK — bilinçli: kesici dosya değil heartbeat alanıdır (`breaker_tripped`) ve bir sonraki seansta kendiliğinden sıfırlanır (`devre_kesici` sapmasının ipucuyla aynı hüküm; day_start_equity her işlenen barda tazelenir, loop.py:1221). Operatör: günün kayıp nedenini oku (pano kill yüzeyi → Kitap · şu an); ertesi seans sıfırlanmadıysa risk defterine bak.
- **DATA_QUALITY kurtarma (WP-P, 2026-08-10):** 15 yol tek sınıf değildir — önce olay `detail`inden alt sınıfı ayır. Kapı hâli (loop.py:1068, `data_halt` → heartbeat `data_ok=False`; `veri_kalitesi` sapması aynı olgu): o gün yeni giriş kapalı, karantinadaki sembol işlem üretmez, tazeleme sabrı kendiliğinden dener — pano Sağlık → Veri hattı · bütünlük (saglik#veriboru) + `state/data_quality.json`. Elle onarımlı bilinen alt sınıflar: pano token'ı ASCII-dışı (api.py:40) → A1 `.dash.env` rotasyonu (deploy/oracle-a1/dash_token_credential.sh); sermaye beyanı kaybı (loop.py:806 reddin kaydı) → iade betiği ops/sermaye_beyani_iade.py.
- **HALT_ACTIVE kurtarma (WP-P, 2026-08-10):** tek tetik api.py:4873 — panodan `/api/halt` (health.set_halt → `state/HALT`; bir sonraki muma kadar yeni alım yok, mevcut pozisyonlar yönetilir). Arıza değil OPERATÖR EYLEMİNİN kaydıdır: kolu kimin/ne zaman çektiği olay defterinde. Geri alma yine panodan: sağ üst DEVAM (Kademe 1 Soft Halt kolu) → `POST /api/resume`; telefonda `/panic` sayfası aynı halt/devam çiftini taşır (`soft_halt` sapması aynı kolu gösterir).
- **MIRROR_DRIFT kurtarma (WP-P, 2026-08-10):** altı yolun ayrımı olaydaki `drift_sinifi` alanındadır. Kendi kendine onarım: çıkış-yetimi kuyruğu her döngü yeniden dener (loop.py:146 — tavansız, sessiz terk yok); trail senkronu yalnız yukarı PATCH'ler. Operatör: Mutabakat masası (pano karar#mutabakat) — hayalet/yetim/adet satırları; alarm "pozisyon ÇIPLAK" diyorsa önce koruma kur (çıplak-pozisyon prosedürü). Kalıcı split_brain/motor_yetimi/adet sapmasında hüküm operatöründür: iç defter tek gerçek (loop.py:563 beyanı), broker tarafını elle düzeltmek domain kararıdır.
- **BROKER_REJECT kurtarma (WP-P, 2026-08-10):** üç hâl: (a) ulaşım yok (loop.py:564) — ayna atlanır, planlar SİLAHLI kalır, sonraki tur kendiliğinden dener; Alpaca erişimini/anahtarları doğrula (mutabakat "Broker API" satırı; sırlar A1 `.env` — deploy/oracle-a1/RUNBOOK.md Bölüm C). (b) gerçek ret (loop.py:645) — plan silahlı kümeden DÜŞER (`failed_broker_rejection` damgası, kendiliğinden geri gelmez); ret nedeni/sınıfı panoda Reddedilen emir kaydı (karar#failsub) — yeniden kurma kararı operatöründür. (c) akış reti (mirror_stream.py:158) aynı masada görünür.
- **TRAIL_DESYNC kurtarma (WP-P, 2026-08-10):** tetik loop.py:1885 (çağrı loop.py:2233) — iç iz süren stop yükseldi, aynadaki stop bacağının PATCH'i reddedildi; broker'da ESKİ (daha alçak) stop duruyor: pozisyon korumasız değil, koruması BAYAT. Senkron her mutabakat turunda yeniden dener (sayaç: mutabakat masası Force-sync satırı). Operatör: ret `detail`indeki broker nedenine bak; ret sürüyorsa stop bacağının emir durumunu Alpaca tarafında doğrula — bacak ölü/iptalse iş çıplak-pozisyon prosedürüne düşer.
- **MECHANISM_STALE kurtarma (WP-P, 2026-08-10):** ilk soru "hangi mekanizma" — ad olay `detail`inde; RUNBOOK'un o mekanizma bölümü nabzı kimin attığını söyler, son damga `state/mechanism_beats.json`. Bekçi YALNIZ gözlemdir, yeniden başlatmaz. Ölü sunucu hâlinin kurtarma yöneticisi yerelde `ops/keepalive.sh` (healthz 2× ölü → diriltir + bu jetonu yazar), A1'de `meridian-tick-watchdog.timer`. ÜRETMİYOR/DÜŞTÜ/BAYAT-TÜREV hâlleri mekanizmanın kendi bölümünden teşhis edilir; toplu görünüm pano Sağlık → gece hattı çizelgesi (saglik#cizelge).
- **ARMING_READY kurtarma (WP-P, 2026-08-10):** tetik arming.py:203/299 — uyuyan kurulum kapıyı geçti; arıza değil KARAR ÇAĞRISI. Kanıt: pano Onay kuyruğu (karar#onaylar) + `state/arming_report.json`. Panelde uygulanacak eylem BİLEREK yok (`actions: []` — api.py:1438 beyanı): silahlanma bir KOD değişikliğidir, icra yolu `strategy.py:995 ARMED_SETUPS` listesine kurulumu eklemektir (mühendislik turu, operatör onayıyla). Kapı geçişi icra zorunluluğu doğurmaz (arming.py docstring: "kapı GEÇSE bile ARMED_SETUPS değişmez") — reddetmek de meşru bir hüküm.
- **AUTHORITY_CHANGE kurtarma (WP-P, 2026-08-10):** iki hâl. (a) analytics.py:1172 — LLM danışman yetkisi eşikle KENDİLİĞİNDEN açıldı/geri alındı (yetki yalnız REVIEW + karşı dolum vetosu); onay gerekmez, doğrulama yeter: olay alanları promoted/r_gap/n + `state/llm_calibration.json`; sınırlar pano Otonomi ve sınırlar (kilitler#ayarlar). (b) nous_eval.py:312 — çekirdek-şekilli öneri kuyruğa sokulmaya çalışıldı: alarmın kendi beyanıyla KOD HATASIDIR (köprü yanlış yönlendirdi) → operatör eylemi yok, mühendislik turu açılır.
- **NAKED_POSITION kurtarma (WP-P, 2026-08-10):** tetik watchdog.py:2286 (motor pozisyonunda canlı koruyucu stop YOK — sev-1; pozisyon başına bir kez mandallı) ve watchdog.py:2273 (ÖLÇÜLEMEDİ: broker okunamadı — "korumasız 0" DEĞİL, önce erişimi düzelt). Kurtarma panodan: Mutabakat masası → Koruma · çıplak pozisyonlar kartı (taze ölçüm `GET /api/alpaca/koruma`) → koruma-onayı `POST /api/alpaca/koruma_kur` (onay jetonu + oneri_id; jetonsuz çağrı KURU KOŞU, bayat oneri_id emri düşürür) her çıplak motor pozisyonuna TEK OCO kurar; HALT bu yolu kapatmaz (koruma_kur bloğu beyanı).
- **ONAYLI_PLAN_GONDERILMEDI kurtarma (WP-P, 2026-08-12):** tetik watchdog.py:2687 (rapor watchdog.py:2606; poll kadansında, kendi try'ında watchdog.py:311): operatör-onaylı + iç-motor-dolmuş planın dolum-sonrası reconcile fotoğrafında Alpaca'da NE EMİR NE POZİSYON var; ihlal plan_id başına bir kez mandallı, ÖLÇÜLEMEDİ dalları alarmsız (fotoğraf bayatlığının sahibi #10 mutabakat-tazelik bekçisi — çift-duyuru yasağı). İlk ayrım olaydaki `gonderim_izi`: False = emir HİÇ çıkmadı → onay yanıtının/`plan_operator_approved` olayının `icra_yolu` alanını oku (loop.py:503-527 gönderimin sonucunu ya da yolun yokluğunu hâl hâl AÇIKÇA yazar); True = iz var ama broker'da yok → Mutabakat masası (pano karar#mutabakat) + Alpaca tarafını doğrula. Kendi kendine onarım: döngünün geç-gönderim kemeri (loop.py:1342) her günlük turda aynasız iç dolumları TEK kapıdan yeniden gönderir — olay `mirror_gec_gonderim`, kemer düşerse `mirror_gec_gonderim_dustu`. Pano `submit_armed` düğmesi BU vakayı KAPATMAZ (yalnız SİLAHLI kümeyi gönderir; dolan plan kümede değil — loop.py:1339 armed'a dokunulmaz beyanı). Kemer de kapatamıyorsa acil kapama ELLE EMİRDİR ve operatör domain kararıdır (alarm metninin kendi hükmü: "gönderim yolunu onar ya da elle emirle"); kalıcı onarım mühendislik turu.
- **scheduler_poll kurtarma (WP-P, 2026-08-12):** damgayı advance_once'ın kendisi atar (scheduler.py:815, her 300 sn poll'da — seans DIŞINDA da; tick_watchdog başlığındaki ölçüm: hafta sonu maksimum aralık 302 sn). 30 dk sessizlik "kadans gecikti" değil SÜREÇ ÖLÜ/KİLİTLİ demektir; kurtarma yöneticileri süreç düzeyindedir: A1'de `meridian-tick-watchdog.timer` (deploy/oracle-a1/tick_watchdog.sh — scheduler_status.updated 45 dk bayatlarsa restart; YAS koruması taze süreci bayat sanmaz), yerelde `ops/keepalive.sh` (healthz üst üste 2 ölü → diriltir). Süreç dirilince poll kendiliğinden döner; elle yetişme `POST /api/scheduler/advance` (pano düğmesi; olay `scheduler_advance_manual`).
- **hermes_poll kurtarma (WP-P, 2026-08-12):** önce ASKIDA mı bak — bekçi rozeti (pano Operasyon) `askida` kovasını ayrı gösterir (watchdog.py:118 sondası): kota soğuması (`brain_cooldown.json`) ya da kimlik havuzu tükenmesi BEKLEMEDİR, arıza değil — alarm üretmez, eylem gerektirmez, OK da sayılmaz (panoda dürüst). Gerçek bayatlıkta iplik ölmüştür: hermes ipliği api sürecinin İÇİNDE yaşar (start() api açılışında; hermes_runtime.py:372 beyanı) → kurtarma süreç restart'ıdır (yerelde `ops/keepalive.sh`, A1'de `meridian-tick-watchdog.timer` — iplik tek başına yeniden başlatılamaz). Isınma koşarken damga sonda başına atılır (hermes_runtime.py:133) — "meşgul" sahte alarm üretmez (v192 + H11).
- **warmup_sprint kurtarma (WP-P, 2026-08-12):** 8 sa sessizlik "ısınma uzun sürdü" OLAMAZ — aramanın kendi tavanı (HERMES_WARMUP_MAX_MIN, varsayılan 5 sa) koşumu kibarca keser; aşım = tavan ÇALIŞMADI (iplik asılı / sonda içinde kilitli / süreç ölü). Kanıt: son ısınma özeti (hermes_runtime.py:160 `last_warmup`: kesildi/sebep/tavan_dk — pano hermes kartı) + `_warm_skip` nedeni (hermes_runtime.py:410 — "koşmadı" ile "koşamaz" ayrımı; learn_halted değeri Kademe-4 kolunun MEŞRU duraklatmasıdır, arıza değil). Kurtarma süreç restart'ıdır (yerelde `ops/keepalive.sh`, A1'de `meridian-tick-watchdog.timer`).
- **cf_advance kurtarma (WP-P, 2026-08-12):** karşı-olgusal defterin (cf_open.json + counterfactuals.jsonl) günlük ilerleyişi; SIFIR YETKİ — hiçbir karar bu deftere bakmaz (loop.py:1408 beyanı), bayatlığı sermaye riski değil ÖLÇÜM boşluğudur (gölge katmanların ham maddesi birikmez). Düşerse `cf_advance_failed` uyarısı hatayı taşır (olay akışı / `state/events.jsonl`); damga yalnız başarıda atılır → bir sonraki günlük tur kendiliğinden dener; elle yetişme `POST /api/scheduler/advance`. Günlük tur hiç koşmuyorsa sorun bu mekanizma değil süreçtir (süreç-düzeyi yöneticilere bak).
- **p5_calibrations kurtarma (WP-P, 2026-08-12):** damga P5_LEARN bloğunun SON adımıdır (loop.py:1948) — bayatlık "tek kalibrasyon düştü" değil "öğrenme-analitik bloğu sonuna ulaşamadı" demektir; hangi adımda kırıldığı `v3_learn_layer_failed` uyarısındadır (blok tek korumada, loop.py:1950). Kendiliğinden onarım: her günlük turda yeniden koşar; elle yetişme `POST /api/scheduler/advance`. Rehinelik dersi: bu blok günlük döngüye bağlıdır — veri kapsaması yüzünden noop kalan bir gün öğrenmeyi de sessizce durdurur (öğrenme-rehineliği vakasının sınıfı).
- **mirror_reconcile kurtarma (WP-P, 2026-08-12):** damga reconcile'ın `broker_reconcile.json` yazımından hemen önce atılır (loop.py:2570) — bayatlık "aynanın fotoğrafı eski" demektir ve fotoğraf yaşının asıl bekçisi #10 mutabakat-tazelik dedektörüdür (kind=mutabakat_tazeligi ile ayrıca alarmlar). Kontrol: Mutabakat masası (pano karar#mutabakat) + `state/broker_reconcile.json` date/api_ok/skip_reason alanları. Alpaca erişimi yoksa reconcile hüküm veremez → anahtar/ağ doğrulaması (mutabakat "Broker API" satırı; sırlar A1 `.env`). Kendiliğinden onarım: alpaca modunda her günlük tur; elle yetişme `POST /api/scheduler/advance`.
- **crosscheck kurtarma (WP-P, 2026-08-12):** SPY kapanışının bağımsız kaynakla seans başına bir karşılaştırması — `state/index_crosscheck.json`u yazar; veri-kalitesi kapısı `status=diverged`i AYNI seansta halt sebebine çevirir (loop.py:1169). Bayatlığın bedeli: bağımsız doğrulama SUSAR, bar kalitesi tek kaynağa kalır. Ateşleme yolu BİLİNÇLİ sessiz-yutmalı (scheduler.py:1170 — düşüş olay YAZMAZ) → teşhis dosyanın kendisinden: date/status alanı taze mi (pano Sağlık → Veri hattı, api.py:3850 aynı dosyayı servis eder). Kendiliğinden onarım: her yeni seans işlendiğinde; süreklilik arızası mühendislik turudur.
- **arming_eval kurtarma (WP-P, 2026-08-12):** haftalık uyuyan-kurulum ölçümü (scheduler.py:1039 `arming.evaluate`) — damga ve hafta bayrağı YALNIZ başarıda ilerler; düşerse `arming_eval_failed` uyarısı + bir SONRAKİ poll yeniden dener (hafta yakılmaz). Bayatlıkta kontrol: `state/arming_report.json` üretim damgası + pano Onay kuyruğu (karar#onaylar). Ölçüm koşup kapı geçse bile kod değişmez (ARMED_SETUPS bir mühendislik turudur; o karar çağrısının prosedürü kendi alarm bölümündedir) — burada iş yalnız kadansı yaşatmaktır.
- **shadow_fit kurtarma (WP-P, 2026-08-12):** öğrenme kadansının 1. adımı (scheduler.py:517 `shadow_model.maybe_refit` — seans başına bir, bar varışından bağımsız). Düşerse `shadow_fit_cadence_failed` uyarısı ve asıl risk şudur: model BAYAT katsayılarla tahmin üretmeye DEVAM eder (yanlış sayı doğru görünür). Kontrol: `state/shadow_model.json` fit_attempt_ts/fit_ts/fit_skip_reason/n_fit damgaları. Adım düşerse seans damgası yine ilerler → yeniden deneme bir SONRAKİ seans; kadansın KENDİSİ düşerse (`learning_cadence_failed`) damga ilerlemez → sonraki poll dener; elle yetişme `POST /api/scheduler/advance` (seans henüz işlenmemişse).
- **opinion_backfill kurtarma (WP-P, 2026-08-12):** 9 günlük pencere kısılmayı alarm SANMAZ — önce meşru sessizliği ele: `backfill_progress` olayı kuyruğun hâlini (kalan_gun/kalan_satir), `hermes.backfill_budget()` türetimi tavanı söyler (tavan 0 = bütçe kısıldı, damga BİLEREK atılmaz; kuyruk boş = iş yok). İkisi de değilse dolgu gerçekten durmuştur: kota soğuması (`brain_cooldown.json`) + kadans uyarılarına bak (`learning_cadence_failed` / `backfill_beat_failed`). Kendiliğinden onarım: her seans kadans yeniden tetikler; dolgu asenkron koşar (hermes.py:3285) ve kalanı sonraki tura devreder.
- **y4_collect kurtarma (WP-P, 2026-08-12):** damga toplama turunun SONUNDA koşulsuz atılır (scheduler.py:646) — iki ayak (Form 4 + FINRA kısa pozisyon) kendi korumasında, ayak arızası bayatlık ÜRETMEZ (`y4_insider_failed`/`y4_shortinterest_failed` uyarıları + `y4_collect` olayının insider_cagri/si_satir alanları ayak sağlığını taşır; anahtar/kota kısılması `atlandi` alanlarıyla kayıtlı — fmp_anahtari_yok/fmp_kota_blogu arıza değildir). Bayatlık = kadans HİÇ koşmadı (seans işlenmedi ya da süreç ölü) → günlük tur/süreç teşhisi. TÜKETİCİSİ BİLEREK YOK (scheduler.py'deki Y4 teşhis bloğu): bayatlığın bedeli karar değil PENCERE kaybıdır — 3 yıllık sınıflama penceresi dolmaz.
- **validation_report kurtarma (WP-P, 2026-08-12):** haftalık kanıt raporu — SALT-OKUMA, hiçbir kapı etkilenmez (scheduler.py:685 olay beyanı); damga `state/validation_report.json` yazımından sonra (scheduler.py:682). Kontrol: dosyanın uretildi/hafta alanları + `validation_report_written` olayı. Ayak kendi korumasında düşerse (`validation_report_failed`) hafta İLERLER → yeniden deneme gelecek hafta; üçlü kadansın KENDİSİ düşerse (`weekly_validation_failed`) hafta yakılmaz → sonraki poll dener. Bayatlığın bedeli görünürlük: "hangi edge kanıtlanıyor?" tablosu eskir, karar bozulmaz.
- **massive_verify kurtarma (WP-P, 2026-08-12):** haftalık grouped-vs-zincir tutarlılık ölçümü — yazım kapısının (`massive.write_enabled`) DAYANAĞI; bayatlarsa kapı bayat kanıtla karar verir (`massive_verify_failed` uyarısının kendi beyanı). Kontrol: `state/massive_verify.json` (verdict/samples/max_dev) + `massive_verify_week` olayı. Anahtar yoksa ölçüm `atlandi: massive_anahtari_yok` ile atlanır ve damga HİÇ atılmaz — bu bayatlık arıza değil YAPILANDIRMA hâlidir (anahtar operatör kalemi). Ayak düşerse hafta ilerler → gelecek hafta; üçlü kadans düşerse (`weekly_validation_failed`) sonraki poll dener.
- **shadowlaw_drift kurtarma (WP-P, 2026-08-12):** haftalık MEASURED_V3 kayma ölçümü — kayma bulursa SABİT DEĞİŞTİRMEZ, yalnız `shadowlaw_variance_drift` uyarısı basar (scheduler.py:716 beyanı); türetilmiş marjların yenilenmesi KOD-TÜRETİLEMEZ, operatör + Rol-1 domain kararıdır. Sağlıklı hafta `shadowlaw_drift_ok` yazar; ölçüm düşerse `shadowlaw_drift_failed` ("marjlar sınanmadan yürürlükte" — bedeli bu). Kontrol: api teşhis bloğunun servis ettiği kayma özeti (scheduler.py:713 `_state` alanı) + olay defteri. Ayak düşerse hafta ilerler → gelecek hafta; üçlü kadans düşerse (`weekly_validation_failed`) sonraki poll dener.
- **halt_learning kurtarma (WP-P, 2026-08-12):** arıza değil OPERATÖR KOLUNUN kaydıdır — `state/LEARN_HALT` dosyası (health.py:26); kolu kimin/ne zaman çektiği `control_learn_halt` olayında. Etkisi: işlemler SÜRER, ship durur (reflect.submit erken döner — `submit_blocked_learn_halt` olayı, reflect.py:898) ve hermes ısınması duraklar (`_warm_skip="learn_halted"`, hermes_runtime.py:411); rollback güvenlik olarak açık kalır. Geri alma panodan: Müdahale kademeleri (kilitler#mudahale) Kademe-4 kolu → `POST /api/control/learn_halt` (api.py:2025; aynı uç aç/kapa).

## BU OTURUMDA BULUNAN + ÇÖZÜLEN (kök nedenleriyle) {#bu-oturumda-bulunan}

- **CANLI-BEKÇİ YANLIŞ ALARMI, bounds.yaml (2026-08-02; sınıf: "git-izli dosyada mtime sızıntıyı değil git trafiğini ölçer"):** KATMAN-2 bekçisi `test_scheduler_flag_survives_publish_lag` teardown'unda `['bounds.yaml']` ile düştü; şüphe test alt-süreçlerine (hermes CLI + mcp_server) gitti. KÖK NEDEN TESTLER DEĞİL: `state/bounds.yaml`+`state/goal.yaml` git-İZLİdir (dagit [1b] SSoT, c783442) ve ana checkout'taki paralel oturum git işlemleri onları repo-içeriğiyle birebir yeniden yazar. Kanıt üç bacaklı: (a) inode adliyesi — goal doğum 14:28:04, bounds doğum 18:01:21 + yerinde yazım 18:06:34, içerik `.git/index` blob'uyla birebir; (b) zaman çizgisi — ilk yazım günün İLK hermes boot'undan (18:01:28) önce; (c) aklama — sitecustomize audit-hook tüm Python alt süreçlerinde + 0,2sn mtime poller ile iki tam tekrar koşumu (worktree + ana checkout), 84 test ×2 yeşil, canlı bounds'a SIFIR yazım denemesi. İKİ KAPI (conftest, kapsam test_canli_bekci_v176): izli iki dosyada parmak izi mtime→içerik-sha256 (içerik farkı hâlâ düşürür; alt-dizin muaf değil) + autouse `_hermes_bin` saplaması (gerçek CLI keşfi testlere kapalı — gerçek Gemini kotası, ~/.hermes yazımı ve MERIDIAN_ROOT=ana-checkout sabitli MCP alt süreci; testin enjekte ettiği HERMES_LOCAL_BIN onurlandırılır, çözümleyici testi bilinçli istisna). CLAUDE.md §8'e istisna notu düşüldü. AVDA BULUNAN AÇIK KALANLAR: (1) aynı scheduler testi gerçek kadansla NASDAQ'a çıkıyor (`earnings.refresh` — ağ nondeterminizmi, ayrı tur); (2) hermes/nous süpürmesindeki 34 kırmızı worktree-state-boşluğu sınıfı, taban ölçümüyle bu turdan bağımsız kanıtlandı (onarımlı/onarımsız FAILED kümeleri birebir aynı). SINIF-AİLESİ BAĞI (operatör talimatı, 2026-08-02 pencere kapanışı): bu vaka ile "paralel-oturum rsync'i" dersi (660dc10 kaydı — EDG-016 oturumunun `--uygula`sı, pencere oturumunun az önce merge'lediği main'i HABERSİZ taşıdı: kayıt b857f48 derken fiilen 6545c6a içeriği canlıya gitti) AYNI ÇATININ altındadır: "ana checkout'taki paralel oturum trafiği, paylaşılan durumu — izli state dosyası ya da canlıya giden ağaç — habersiz yeniden yazar". Sınıf avı iki vakayı tek çatıda görmeli: tek-oturum varsayımı taşıyan her mekanizma (bekçi mtime'ı, dağıtım kaydının "hangi tepe taşındı" beyanı) bu ailenin adayıdır; pencereyi koşan oturum dağıtım ANINDAKİ main tepesini kaydetmeli.
- **T+1 ritim kusuru (sınıf: "kaynak yayın gecikmesi varsayımı kodda örtük"):** 8×300sn refetch bütçesi FMP'nin akşam-yayınına göre yazılmıştı; kota tahsisi Massive'e (T+1) geçince her seans 40 dk'da terk edildi (164 birikmiş atlama, %17 kapsama). Çözüm: same-evening bacağı + merdiven + onarım geçidi. SINIF avı yapıldı mı: kısmen — "zaman varsayımı" sınıfının diğer örnekleri (bararchive TTL, sprint pencereleri) bilinçli tarama görmedi → AÇIK (aşağıda).
- **Gölge-v1'in çıkış körlüğü:** giriş-kararı defteri çıkış düğmelerini ölçemiyordu → gölge-v2 yaşam-döngüsü motoru (fill→yönetim→çıkış→mark, PaperBroker'ın kendisiyle; iki payda k=4/k=6).
- **Eksen-2 ölü zinciri:** beceri önerisi üreticisi (reflect.propose_deterministic → skills.recommend_from_attribution) hiçbir üretim yolunda değil → 0 öneri. Kablolama uçuşta.
- **Elle-tetik öğrenme katmanı:** sprint, shadow_model fit, backfill (390/390 görüşsüz plan), bütçeler statik → otomasyon turu uçuşta.
- **Panodaki "10 bekleyen" yanılsaması:** app.js inbox_count yokken pending_count'a düşüp planı "karar" diye etiketliyor; canlı gerçek 0. Düzeltme pano turunda.
- **sed placeholder uyuşmazlığı (sınıf: "sessiz sıfır-etkili sed"):** runbook token sed'i yanlış desendi — bilinen placeholder'la canlıya çıkardı. cutover.sh desen-doğrulamalı yapıldı.
- **rsync --delete-excluded tuzağı:** uzak state'i silerdi; ajan kendi yakaladı, sade --delete.
- **launchd TCC:** ~/Documents'taki SSH anahtarını launchd okuyamıyor → ~/.ssh/oci-a1.key kopyası.
- 46 bulguluk ölü-mekanizma avı (5 mercek + çürütme): triyaj ROADMAP §7 + §3.0'da.
- **fail-notify birimi hiç çalışmamıştı (sınıf: "systemd'de çok-satır gömülü Python"):** test-ateşleme IndentationError yakaladı — systemd `\` devamı baş boşlukları -c dizgisine katıyor; worker ölse ve kanal kurulu olsa bile bildirim gitmezdi. Tek-satıra çevrildi, A1'de yeniden test-ateşlendi: exit 0 + beyanlı NO-OP satırı journal'da. Sınıf avı: repo'daki diğer birimler/ betikler tek-satır -c kullanıyor, başka örnek yok. DERS: her OnFailure/oneshot birimi kurulduğu gün test-ateşlenir — "kurulu" ≠ "çalışır".
- **ÖĞRENME REHİNELİĞİ (öğrenme-otomasyonu turu, kök düzeltme):** "fit çağrılmıyor" teşhisi YANLIŞTI — P5_LEARN her döngüde koşuyordu ama daily_cycle veri kapsaması yüzünden noop olunca öğrenme de sessizce onunla duruyordu (rehinelik, ve durduğu hiçbir yerde yazmıyordu). Yani veri düzeltmesi = öğrenme düzeltmesi. Ek: dolgu kuyruğunun gerçek boyutu 95 (sonuçlu planlar; 386 görüşsüzün 291'i sonuçsuz — kalibrasyon çifti sonuç ister), türetilmiş tavan ~46/gece → ~3 gece. Eksen-2 üreticileri hipotez-yan-ürünü rehineliğindeydi → bağımsız skills.axis2_cycle(); yapısal körlük bulundu: eşik cf katmanını okumuyor (n_cf=1080/1004'lük iki skill görünmez) — cf-kolu tasarımı temizlik turunda. sprint_runs "orphan"ı okuyucu hatasıydı (defter sandbox'ta, status() yanlış rafa bakıyordu — düzeltildi).
- **Y4 İLK ÖLÇÜM (madde 5 açılışı):** short-interest 24 ay/49 settlement/12.250 kayıtla ölçüldü — **EDGE YOK** (12 hücrenin 0'ı sınırı geçti; kılpayı hücre likidite-vekili çıktı, FINRA/yerel delta ρ=1.00 → etkin sınama ~6). Prescreen'e BAĞLANMAYACAK; si_delta_pct_local bileşen listesinden düştü. Insider: **ÖLÇÜLEMEDİ** (FMP ücretsiz: page≥1→402, date sessizce yok sayılıyor; yalnız page=0/100-dosyalama anlık görüntüsü) — "edge yok" DEĞİL; yol: plan yükseltme veya SEC EDGAR çeyreklik setleri (dosya indirme operatör onayı). fetch_delta sayfalama yolu ücretsiz planda ölü — kadans page0-only olmalı (temizlik ajanına iletildi).
- **HAYALET SEANS (Y4'ün yan bulgusu, sınıf: "takvim doğrulaması yok"):** 2025-05-26 Memorial Day 258/259 CSV'de seans olarak duruyor (çoğu önceki günün kopyası; 5 sembolde bölünmemiş ham fiyat — BKNG +%2598 hayalet getiri); 2018-11-22 aynı sınıf. sanitize aynı-tarihe, split_suspect soft'a takılıyor → component_ic.json + cf + R-tabloları KİRLİ. Sınıf düzeltme ajanı uçuşta (takvim kapısı + karantina + onarım CLI); onarım + türetilmiş artefakt yeniden-üretimi yarınki dağıtımın migrasyon adımı.
- **DE-RISK RAMPASI KEŞFİ (çıkış-paketi ölçümü, 2026-07-31 — kuraklığın gizli ortağı):** `broker.max_positions_at` (tepe-DD %3→kıs, %8→sıfırla) incumbent'ta günlerin %92,4'ünde AKTİF; P3 kolunda %92 gün izin=1. Döngü ölçüldü: yavaş çıkış→eğri tepe altı→izin 1→işlem çöküşü (71→28). Eşikler bounds'ta DEĞİL kodda sabit → hipotez uzayının körü. P3 imzası 4/4 (ödeme 1,53→2,84, beklenti 0,104→0,287R, DD %4,6→%0,5) — "reddedildi ama çürütülmedi"; sıradaki tur: rampa eşikleri bounds'a + sabit-rampa yeniden-ölçüm + profit_target_r/time_stop "kapalı" değerleri. AYRICA: canlı-defter (ödeme 0,97) vs Search-OOS (1,53) şiddet farkı açıklanamadı — WP0'ın iki-motor bulgusuyla birleşen icra/uyum sorusu. Prescreen raporlarına kod-sürümü damgası önerisi.
- **EAP ARŞİVLENDİ (4/4 aday aile elendi):** +9,0bps CI[−13,3·+31,9] (eşik 30); güç-yeterli 12,6-yıl genişletmede +6,8bps; PK-1 kesin. YAN BULGU → kart-adayı: KIYAS KİRLENMESİ (olay penceresinde evrenin %64-74'ü kendi penceresinde — tüm "evren-medyanı" ölçümleri sıkışık).
- **systemd `Environment=` satır-sonu yorumu tuzağı (2026-08-02; sınıf: "birim dosyasında kabuk-sözdizimi varsayımı" — fail-notify'ın çok-satır-Python vakasıyla aynı aile):** meridian.service'te `MERIDIAN_DASH_TOKEN=...token   # ASCII zorunlu (bkz. api._auth)` — systemd satır-sonu yorumu desteklemez, `#` sonrasını boşluklarla ayrı `VAR=VAL` atamalarına böler; geçersizler journal'e "Invalid environment assignment, ignoring" düşürür. Fiilî arıza YOK (ilk atama geçerli, token doğru kuruluyordu) — kusur, doğru görünen ama okunmayan yorum + journal gürültüsü. Çözüm: yorum üstteki blok yoruma katlandı; C1'in BIND_HOST çivisi GENELLENDİ — yeni test dosyadaki HER `Environment=` satırında `#` yasaklıyor (tests/test_kovab_kucuk_v165.py). Sınıf avı: deploy/ + ops/ tarandı, başka ihlal yok. Commit 4d695ff; A1'e dağıtım bakım penceresini bekliyor (o güne dek canlıdaki eski satır zararsız gürültü üretmeye devam eder).
- **İki ölü token-bekçisi (2026-08-02; sınıf: "sessiz sıfır-etkili adım" — sed-placeholder vakasının İKİNCİ kuşağı):** H3 tur-2 `CHANGEME` placeholder'ını birimden çıkarınca deploy.sh:96 `grep CHANGEME` uyarısı ve cutover.sh adım 5/6'nın desen-bağımlı sed'i SESSİZ NO-OP'a düştü — taze kurulum/cutover panoyu TOKEN'SIZ canlıya çıkarırdı. Çözüm: iki betik de artık desen değil DOSYANIN KENDİSİNİ ölçüyor — `/opt/meridian/.dash.env` yok/boşsa üretilir (openssl rand -hex 24; RUNBOOK B.3 / bakim_h9.sh:59 deseni), doluysa DOKUNULMAZ (habersiz rotasyon yasak), izinler her koşuda ubuntu:ubuntu+0600'e sabitlenir, sonuç dolu+0600 doğrulanır (değilse exit 1 — cutover'ın sed-vakası doğrulama disiplini korunuyor). `.dash.env` dagit.sh rsync'inden dışlanmış kalır (2026-08-01 --delete vakası) → dosya SUNUCUDA doğar, taşınmaz. RUNBOOK'un sed-vakası notu iki-kuşaklı anlatıma güncellendi. Doğrulama: 78 çivi-testi yeşil (h3_tur2 + uiux_s1b + v132) + cutover snippet'inin 4-senaryolu şim-koşumu (yok→üret·0600 / dolu→bayt-özdeş / 0644→izin-onarımı / boş→yeniden-üret). DERS (sınıfı genelleştirir): bir bekçinin aradığı DESEN başka bir turda kaynaktan kalkarsa bekçi test edilmeden ölür — bekçiler durumu (dosya/uç-nokta) ölçmeli, yokluğu sessizliğe eşitlenen izleri değil.
- **EDG-016 kanıt zinciri kopuktu (2026-08-02; sınıf: "hüküm kanıtı silinebilir dizinde" — kart depodaki yolu gösterir, baytlar scratchpad'de yaşar):** Kartın SUCCESS hükmü `sonuc_016.json + RAPOR_016.md`'yi gösteriyordu; 511f1c1 o ikisini kurtarmıştı AMA kod damgası (`kod_damgasi_016.json`) ve damgaladığı beş betik yalnız /private/tmp scratchpad'inde kalmıştı — scratchpad silindiği gün damga doğrulanamaz hash listesine, hüküm tekrar-üretilemez iddiaya dönerdi. Sınıf avı İKİNCİ vakayı buldu: 012–014 turunun kodu da (depodaki kod_damgasi.json'un hash'lediği k012/k013/k014/rapor/birlestir.py) aynı kaderdeydi. 11 dosya kaynakta VE hedefte damga SHA-256'larıyla birebir doğrulanıp `research/olcumler/wp2_olcum/` arşivine alındı (039c5b8 → merge 06e8f60); `dagit.sh --uygula` ile A1'e dağıtıldı (kapılar yeşil; bounds/goal canlı=repo BİREBİR; A1'de 13 dosyanın uzak SHA-256'sı birebir — sonuc_016/RAPOR_016 önceki dağıtımla zaten canlıdaydı). Kart taraması başka eksik kanıt yolu bulmadı; panel ara-dosyaları bilinçli dışarıda (damgasız, girdilerden yeniden üretilebilir). DERS (sınıfı genelleştirir): "measured" statüsü kanıt+damga+kod ÜÇLÜSÜ depoya girince tamamdır — damga kodsuz yaşayamaz; güncel ölçüm dizinleri (kys_olcum, wp1_rvol_form, wp_u_midcap) bunu zaten yapıyor, wp2_olcum geleneğin öncesinde kalmıştı, hizalandı.
- **`takvim_yok` zinciri KAPANDI (WP-D'nin bilerek ertelenen kalemi, 2026-08-02):** `gap_scan`in üçüncü hâli panoda WP-P'yle tanınmıştı (e3edaf0: `_GAP_DURUM` girdisi + bilinmeyen-durum "hüküm VERİLMEDİ" dalı, çivisi v171'de); scheduler kancası eksikti — rapor ölçülmüş-sonuç dalına düşüyor, arıza nedenini taşıyan `seans` bloğu state'e hiç girmiyor ve hâl olay defterinde SESSİZdi. Çözüm (`scheduler._intraday_gap_check`): erken-dönüş listesine `takvim_yok` + `seans` kopyası YALNIZ bu hâlde (pano teşhisi; diğer iki hâl bit-bit aynı) + süreç başına BİR `gap_scan_calendar_unavailable` uyarısı (emsal `_CALENDAR_WARNED`; 300 sn poll'de koşulsuz uyarı 288 satır/gün ederdi). Çivi: v175 (3 test; kırmızı-önce dört geri-alma senaryosunda fiilen doğrulandı). A1'e sıradaki bakım penceresiyle iner.
- **PAZAR-AKŞAMI PENCERESİ KAPANDI — takvim_yok kalemi CANLIDA; `--uygula` BİLEREK atlandı (2026-08-02 ~19:25 UTC, Rol-1, operatör talimatlı):** otoriter suite donmuş `6545c6a` tepesinde **3969/0** (18:40 dk, ana checkout) + dagit kapıları yeşil (audit ✓ · lint-imports 5/5 KEPT · [1b] bounds/goal canlıyla BİREBİR). Dry-run delta'sı yalnız 2 lint-cache satırı çıkınca ölçüldü: EDG-016 oturumunun 19:05 UTC `--uygula`sı, 18:30/18:37 UTC'de merge'lenmiş main çalışma ağacımızı taşımıştı (rsync-tüm-repo sınıfı, bu kez İYİ huylu: taşınan ağaç TAM commit'liydi) — scheduler.py A1-yazımı 19:05:15, servis başlangıcı 19:05:18 → KOŞAN worker yeni kodla doğdu. O pencerenin kapı-suite'i bu ağacı kapsamıyordu; boşluğu bu oturumun post-hoc otoriter suite'i (aynı içerik, 3969/0) kapattı. İkinci restart'ın kanıt desteği yoktu → `--uygula` atlandı (boş işlem canlıda gereksiz kesinti). CANLI DOĞRULAMA: healthz 200 · scheduler_status ilerliyor (19:05:50) · `akis_boslugu={"durum":"seans_disi","gun":"2026-08-02"}` — yeni üç-anahtarlı minimal kopya sözleşmesi canlıda (v175 test-3'ün çivisi). `sitecustomize.py` kancası sahibi hungry-jemison tarafından ~18:44 UTC'de silindi + yeniden doğrulandı — pencere-öncesi bekçi maddesi görevini yaptı, kuyruk kaydıyla birlikte kapandı (KUYRUK BOŞ; kayıt bu commit'te silindi). DERS (sınıf: paralel-oturum rsync'i): bir oturumun `--uygula`sı, başka oturumun az önce merge'lediği main'i HABERSİZ taşıyabilir — pencereyi koşan oturum dağıtım ANINDAKİ main tepesini kaydetmeli (EDG-016 kaydı b857f48 derken fiilen 6545c6a içeriği taşındı).
- **OTURUM KAPANIŞI (2026-08-02 gece, Rol-1 — takvim_yok/pencere oturumu):** hungry-jemison merge'i (0652841: bekçi kapıları + v176 + sınıf-ailesi bağı; RUNBOOK çakışması regen'le çözüldü, merge-sonrası 93/93) indi; ÜÇ tur worktree'si + dalı temizlendi (xenodochial / unruffled / hungry-jemison) — repo TEK checkout. Dağıtım kuyruğu BOŞ. Otoriter suite referansı: **3969/0 @ 6545c6a** (bu oturumun pencere koşusu). A1 çalışma-yolu içeriği 6545c6a-özdeş; main 0652841 farkı yalnız test-katmanı (conftest bekçi kapıları + v176) ve belgeler — runtime etkisi YOK, sıradaki pencereyle iner (yeni kuyruk kaydı açmayı gerektirmeyecek kadar küçük; pencereyi koşan, dağıtım anındaki main tepesini kaydetsin — 660dc10 dersi).
- **STATE ŞİŞMESİ + YEDEK KAPSAMI (2026-08-02 gece, Rol-1 + Opus; H10 turunun devredilen bulgusu — iki sınıf birden):** A1'de state/ 617M'in 438M'i = 4 sprint kum-havuzu × ~110M; gecelik tar 112,5M. İKİ AYRI KÖK NEDEN ÖLÇÜLDÜ: (1) SINIF "belgede donmuş boyut varsayımı" — `sprint.SKIP_COPY` yalnız `bars`ı atlıyordu; küme yazıldıktan SONRA doğan `bars_intraday` (43M) + `intraday_bars` (40M) her kum havuzuna sessizce kopyalanıyordu (83M = ~110M'in 3/4'ü; sprint çocuğunun yolunda okuyucuları YOK); docstring'in "~1.5 MB" iddiası 70× bayattı. Birikim SINIRSIZ DEĞİLDİ: SANDBOX_KEEP=3 + start()-anı budaması çalışıyor, kararlı durum 4 dizin. (2) Aynı sabahki 4×5dk damgaları KADANS KUSURU DEĞİL YENİ VAKA DEĞİL — C15'in (damga-ezme) canlı imzası: olay defterinde **154 `sprint_cadence_start`, HEPSİ `taze_aday_birikimi/taze=50/gecen_gun=0`**, tam 300sn poll aralığında, 06:00'da pencere kapanınca kesiliyor; canlı `sprint_status.json`'da `n_hyp_at_start` YOK (eski kod çocuğu eziyordu). Düzeltme (`_damgayi_koru`) 19:05 restart'ıyla ZATEN CANLIDA (A1 diskinde grep'le doğrulandı); ilk yeni sprint damgayı yeniden basınca kadans kendi kendini onarır — beklenti: bu gece 22:00'de TEK sprint, sonra haftalık taban. ÇÖZÜMLER: SKIP_COPY += {bars_intraday, intraday_bars} (çivi: test_sr4b, v45) · `meridian-backup.service` tar'ına `--exclude=state/sprint` (ölçülen: 112,5M → **40.497.179 bayt ~40,5M**; RUNBOOK B4/9 satır 5'in ~15M tahmini yanlıştı) + çift-yönlü kapsam çivisi (`test_backup_kapsami_sprint_haric_bars_dahil`, v174: sprint dışarıda + bars/seans-içi arşivler İÇERİDE kalmak zorunda) · kayıp beyanı birim yorumunda (sandbox `sprint_runs.jsonl` defterleri arşiv dışı — 2026-08-02'de 4/4 sandbox'ta zaten yoktu) · H7 tatbikat beyanı güncellendi (B4/6). Sıklık artışı BİLEREK yapılmadı (litestream defterin dakika-RPO'sunu taşıyor; bars günde bir değişiyor). Hedefli testler 74/74 + t3 yeşil.
- **YEDEK BİRİMİNİN PYTHON BACAĞI H9'DAN BERİ HİÇ ÇALIŞMAMIŞTI (2026-08-02 ~20:45 UTC, elle test-ateşleme yakaladı; sınıf: "birimde kabuk-sözdizimi varsayımı" — fail-notify çok-satır-Python ve Environment satır-sonu yorumuyla AYNI AİLE, ÜÇÜNCÜ vaka):** `storage.backup_to` bacağı yolu `\"...\"` kaçışıyla geçiriyordu; systemd TEK-TIRNAK İÇİNDE de C-kaçışlarını çözer → sh'a ulaşan `-c` dizgisinin tırnakları erken kapanır, python `backup_to(/opt/...)` alır → H9 revizyonundan (2026-07-31) beri HER koşu SyntaxError (journal 08-01/08-02 birebir), `state/meridian.db.yedek` diskte HİÇ DOĞMAMIŞ, tar hiçbir gece tutarlı DB kopyası içermemiş — ve `if...fi;` zinciri hatayı yuttuğu, `rc` yalnız tar'ı ölçtüğü için her koşu `Result=success`'ti (birimin kendi "sessiz yedek kaybı" uyarısının vücut bulmuş hâli; elle-ateşleme doktrini tam bu yüzden var ve işledi). ÇÖZÜM İKİ BACAKLI: (1) yol string-literal değil `sys.argv[1]` — dizgide iç tırnak kalmadı, systemd'nin çözeceği kaçış yok (önce sh katmanında elle provalandı: `.yedek` doğdu, `PRAGMA integrity_check` ok); (2) `ok` bayrağı — python bacağı düşerse tar YİNE alınır ama birim BAŞARISIZ beyan eder. Çivi: `test_backup_python_bacagi_tirnaksiz_ve_sessiz_degil` (v174: ExecStart'ta `\"` YASAK + `sys.argv[1]` + `ok=0` + `[ $$ok -eq 1 ]` zorunlu). CANLI KANIT (ikinci ateşleme, 20:50 UTC): journal'da SyntaxError YOK, `.yedek` İLK KEZ birim eliyle tazelendi (1.335.296 bayt), tar'da yedek üyesi 1. DERS (aileyi genelleştirir): birim içinde `\"` görülen her ExecStart şüphelidir — systemd'nin quoting'i sh değildir; değer taşımak gerekiyorsa argv kullan, kaçış kullanma.
- **STATE-ŞİŞMESİ TURU KAPANIŞI (2026-08-02 gece ~21:00–22:10 UTC, Rol-1; ölçümler dağıtım-kuyruğu kaydında):** (1) Otoriter suite donmuş `0248653`te **2 failed / 4104 passed**; triyaj İKİ AYRI hüküm verdi: t3 kırmızısı YÜRÜYEN-AĞAÇ ARTEFAKTIYDI (nervous-dewdney merge'i 5f906c5 koşum ORTASINDA indi; statik ağaçta yeşil — "otoriter suite yalnız donmuş ağaçta" dersi bir kez daha fiilen kanıtlandı), v116 kırmızısı GERÇEKTİ: SKIP_COPY'ye giren `bars_intraday` literali yazar-tekliği kör-taramasına takıldı → test-katmanı çözümü 48cd445 (MUAF kümesi {barsarchive.py, sprint.py}, gerekçeli; tarama üçüncü modül için aynen tetikte). (2) **CERRAHİ DAĞITIM KARARI (sınıf: "paralel-oturum trafiğinde tam-repo dağıtımı"):** main gece boyunca hareketliydi — v166 ısı-tavanı karar-turu (`heat_hard_r 4.5→5.0`, goal.yaml İZLİ state!) + v181'in commit'lenmemiş watchdog WIP'i + a2a7665. Tam `dagit.sh --uygula` ya kirli ağacı (`--kirli-gec` → yarım-iş-canlıya YASAsı) ya da BAŞKASININ karar-turunu kendi penceresi/ doğrulaması olmadan taşıyacaktı (660dc10 sınıfının tam kendisi). Hüküm: kapsam tek dosyaya daraltıldı — `meridian/sprint.py` worktree↔main ÖZDEŞ (sha `8b9b6baa…`), hedefli kapsam 146/146, sha-doğrulamalı scp + yedek + yalnız-meridian restart. DAĞITIM ANINDAKİ main tepesi: `4c06c61` (sprint.py o tepeyle de özdeş — 660dc10 dersi uygulandı, beyan doğru). SONUÇ: A1 ağacı BİLİNÇLİ karışık ara durumda (19:05 içeriği + yeni sprint.py + /etc'de yeni yedek birimi); v166 goal değişikliği, v181 api/watchdog kolları ve ağ-kapısı test katmanı CANLIYA İNMEDİ — her biri kendi penceresinin/sahibinin işi, İLK TAM dagit ağacı eşitler ve dry-run delta'sı bu kaydı doğrular.
- **SPRINT n_v1=0 KÖK NEDENİ ÖLÇÜLDÜ + DÜZELTİLDİ (2026-08-02 gece, öğrenme katmanı turu; sınıf: "depolama arka-ucu değişti, yan sözleşmeler sessizce bayatladı" — audit #23'ün [kopyalanan HALT] İKİNCİ kuşağı + SKIP_COPY-denylist-kaçağı [bars_intraday ile aynı tur]):** 154 kadans koşusunun tamamının ~60 sn'de `phase=done, n_v1=0` bitmesi ÖRNEKLEM KURAKLIĞI DEĞİL İZOLASYON DELİĞİYDİ. Zincir: dbmigrate A1'de 07-31 02:01'de uygulandı (WP-H/H9 A3, cb48f93+; `.migrated` damgaları) → altı defter `state/meridian.db` varken SQLite'tan okunur → `sprint.start()` kum havuzuna canlı DB'yi de KOPYALIYORDU (SKIP_COPY migrasyon öncesi yazılmıştı) → `_reset_sandbox_state`in ham dosya sıfırlaması çocuğun store okumalarına GÖRÜNMEZ → çocuk canlının `last_date=2026-07-31`ini DB kopyasından okudu → `loop.daily_cycle` monotonluk bekçisi (2026-07-15 GS dersinin bekçisi — DOĞRU çalıştı) eval penceresindeki HER seansı reddetti. KANIT (A1 salt-okuma): son sandbox'ta 522/522 `regressive_session_refused, book_at=2026-07-31`; sandbox DOSYASI `last_date: null` iken sandbox DB'si `"2026-07-31"`; DB'deki 95 işlemin hepsi v4 → `_count(1)=0`; İLK kadans 07-31 02:08:10 = migrasyondan 7 dk sonra (tümü DB-sonrası; 07-22'nin dosya-tabanlı sprinti n_v1=100 üretmişti); son koşu 05:59:06→06:00:10 = 64 sn. Eval penceresi ve giriş kapıları AKLANDI — yürüyüş taramaya hiç ulaşmadı. ÇÖZÜM (Opus, tek brief): SKIP_COPY += {meridian.db, -wal, -shm} (kum havuzu DB'siz doğar → çocukta `storage.active()` False → ölçülmüş-iyi dosya yolu; sıcak-WAL kopyasının tutarsız-anlık-görüntü riski de kapandı) + `start()`ten saf `_kur_kum_havuzu()` çıkarıldı (test yasanın kendisini çağırır) + İKİ ÇİVİ (test_sr4c ad-çivisi; test_sr1d DAYANIKLI çivi: migre-DB'li sentetik canlıda sıfırlama STORE KATMANINDAN doğrulanır — SR1b'nin körlüğü tam buydu, dosyaya bakıyordu). Kırmızı-önce kanıtlı (sr1d üretim semptomuyla düştü: `'2099-01-01' is None`); kapsam 31/31 + storage 15/15 yeşil (Rol-1 bağımsız koşumu). sprint_runs.jsonl'ın hiç doğmaması aynı kökün sonucu (Faz A, B'ye hiç ulaşmadı). YAN NOT: `_damgayi_koru` (C15) canlıda — bu gece 22:00'de TEK 60-sn'lik inconclusive sprint beklenir, düzeltme inene dek haftalık taban boşa döner. SINIF AVI: state kopyalayan diğer iki mekanizma (prescreen._sandbox, mutation harness) defterleri SIFIRLAMADIĞI için içerik-tutarlı — kırık değil; ama ikisi de sıcak-WAL kopya riskini taşıyor (küçük, ayrı kalem). DERS: MERIDIAN_ROOT-sandbox izolasyonu dosya kopyası/reset'iyle kuruluysa arka-uç değişimi onu sessizce deler; sandbox kuran her mekanizmada reset STORE katmanından test edilmeli.
- **SPRINT TURU PENCERESİ KAPANDI + KABUL ÖLÇÜTÜ ÖLÇÜMLE TAMAM (2026-08-03 ~04:35 UTC, Rol-1, operatör talimatlı "Faz B bitince koş, sabaha bırakma"; 23:30 kısıtı operatör kalemiyle kaldırılmıştı):** otoriter suite donmuş `4dbe688` tepesinde **4133/0 (EXIT 0, 23:06 dk)**; tek sonraki commit (a933a3e) günlük-yalnız → hüküm dağıtılan içeriğe birebir taşınır. `dagit.sh --uygula` 04:31 UTC: kapılar yeşil (audit ✓ · lint 5/5 KEPT · [1b] bounds/goal BİREBİR), dry-run delta YALNIZ 4 doküman/cache satırı — kod, 04:21 penceresiyle (tick-watchdog dirilişi turu) zaten eşitlenmişti; restart + healthz 200 + üç birim aktif + v181/SKIP_COPY/test damgaları diskte doğrulandı. KABUL ÖLÇÜTÜ (üç gösterge, iki bağımsız sprintte): (1) sandbox DB'siz doğdu ✓ (22:04 ve 04:33 koşuları; yalnız inert `meridian.db.yedek` kopyalanıyor — `storage.active()` görmez, 1,3M'lik SKIP_COPY boyut-kalemi olarak nota geçti); (2) Faz A gerçek yürüyüş ✓ (60 sn ölüm imzası yerine 5s46d); (3) **nihai n_v1 = 115/523 seans** ✓ — min_sample'ın ~4 katı, "modern giriş yasasında kuraklık" çatalı ölçümle KAPANDI (07-22 eski-yasa emsali 100'dü). YAN VAKA (sınıf: paralel-oturum restart'ı koşan sprint çocuğunu keser — cgroup): 22:04 sprintinin Faz B'si, 04:21 penceresinin restart'ıyla arama ORTASINDA öldü (pid 15110; sprint_runs.jsonl doğmadan; status "search"te donuk kaldı — sessiz ölüm, hiçbir bekçi bunu ölçmüyor → sıradaki tur adayı: sprint-çocuğu yetim/ölüm dedektörü). Faz B sonucu için sprint dağıtım-sonrası YENİDEN tetiklendi (sid 20260803-043330, CLI `sprint.start()` — token'sız yol; damga n_hyp_at_start=51 yerinde); faz-geçiş monitörü kurulu, B hükmü (shipped/no_clearing + ilk sprint_runs.jsonl satırı) geldiğinde işlenecek. **B HÜKMÜ GELDİ (2026-08-03 11:05 UTC, temiz çıkış):** Faz A n_v1=111/523 (ilk koşunun 115'iyle tutarlı bant; girdi birebir değil — barlar gece tazelendi), Faz B **no_clearing_candidate** (incumbent_oos=0.0813, evaluated=2, cleared=0; "bu veri diliminde v1 yerel-optimal") → shipped=false, Faz C yok. **`sprint_runs.jsonl` MİGRASYONDAN BERİ İLK SATIRINI YAZDI** — mekanizma uçtan uca dönüyor; md.2 sayacının kalibrasyon-noktası bacağı ancak bir aday kapıyı geçip C'de döngü kapatınca akar (bu, dürüst bir "henüz yok", arıza değil). GÖZLEM (tur adayı, düşük öncelik): budget=12'ye karşı evaluated=2 — koordinat inişi ilk turda iyileşme bulamayıp erken durdu; arama-verimliliği sorusu ayrı bir ölçüm ister, bu turun kapsamı dışında.
