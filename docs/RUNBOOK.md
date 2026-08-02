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

- **12 alarm jetonu** (`meridian/obs.py`) — hepsi bildirim beyaz-listesinde
  (`NOTIFY_TOKENS` ALARM_ sabitlerinden TÜRETİLİR, elle liste değil)
- **17 bekçi mekanizması** (`meridian/watchdog.py::EXPECTED`)
- **5 sessiz-hat sapma adı** (`meridian/api.py::_sessiz_hat`; bekçi segmentinin
  adları değişkendir ve yukarıdaki mekanizma listesinden gelir)
- **11 ops betiği** başlığıyla okundu
- **39 günlük maddesi** üç bölümden toplandı

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

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `HEARTBEAT_STALE` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## ROLLBACK {#rollback}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **2 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/rollback.py:152` → mesaj şablonu: `f"GERİ ALMA BAŞARISIZ: v{version} kötü ama v{parent} anlık görüntüsü yok — " f"kötü sürüm CANLI kalıyor, elle müdahale gerekli"`
  - `meridian/rollback.py:183` → mesaj şablonu: `f"v{version} → v{parent} underperformed by {round(karar['par'] - karar['cur'], 4)} " f"({karar['yontem']})"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `ROLLBACK` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## CIRCUIT_BREAKER {#circuit_breaker}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:786` → mesaj şablonu: `f"günlük kayıp devre kesici: {day_pnl_pct:.2%}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `CIRCUIT_BREAKER` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## DATA_QUALITY {#data_quality}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **11 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/adapters/data.py:936` → mesaj şablonu: `f"BAR KAYNAK UYUŞMAZLIĞI: {ticker.upper()} {d} — {src} {round(pc, 4)} vs " f"massive {round(mc, 4)} (%{round(dev * 100, 3)} > tol %{round(MASSIVE_TOL * 100, 3)})"`
  - `meridian/adapters/data.py:2084` → mesaj şablonu: `f"{ticker}: {streak} ardışık turda hiçbir kaynak satır vermedi (istek hatası YOK) " f"— evren bakımı gerekiyor olabilir"`
  - `meridian/api.py:40` → mesaj şablonu: `"MERIDIAN_DASH_TOKEN ASCII-DIŞI: HTTP başlığında gönderilemez, yani pano " "kimlik doğrulaması FİİLEN İMKÂNSIZ. ASCII bir token ile değiştir."`
  - `meridian/hotstate.py:167` → mesaj şablonu: `f"hotstate ÇIRPINMA: {DOWN_REASSERT_S}s içinde {bastirilan} kopma"`
  - `meridian/loop.py:435` → mesaj şablonu: `f"evren sapması: {rep['n_stale']} sembol S&P 500'de yok — {', '.join(rep['stale'][:8])}"`
  - `meridian/loop.py:739` → mesaj şablonu: `f"endeks çapraz-doğrulama sapması: {_xc.get('divergence')}"`
  - `meridian/loop.py:746` → mesaj şablonu: `f"veri kalitesi kapısı: index_ok={idx_ok}, {len(tick_bad)} hisse başarısız"`
  - `meridian/scheduler.py:234` → mesaj şablonu: `f"SEANS ATLANDI: {session} — bir sonraki seans kapandı, bu seansın barı hâlâ " f"gelmedi (kapsama %{100 * float(cov or 0):.0f} < %{100 * need:.0f})"`
  - `meridian/watchdog.py:1210` → mesaj şablonu: `f"BAR DETERMİNİZMİ ÖLÇÜLEMEDİ: {rep['determinism'].get('detail')}" if _olcum_yok else f"SESSİZ BAR MUTASYONU: {rep['determinism'].get('detail')}"`
  - `meridian/watchdog.py:1270` → mesaj şablonu: `f"GERİLEME: {rg['field']} {rg['was']} → {rg['now']} (ileri-only olmalıydı)"`
  - `meridian/watchdog.py:1277` → mesaj şablonu: `f"ALAN EZİLDİ: {lo['file']}.{lo['field']} bir kez doluydu, şimdi kayıp"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `DATA_QUALITY` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## HALT_ACTIVE {#halt_active}

### Belirti

- `obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/api.py:2628` → mesaj şablonu: `"HALT via dashboard"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `HALT_ACTIVE` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## MIRROR_DRIFT {#mirror_drift}

### Belirti

- internal sim fill vs actual Alpaca fill diverged beyond tolerance *(kaynak: `meridian/obs.py` — `ALARM_MIRROR_DRIFT`)*

### Teşhis adımları

- Bu jetonu **6 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:164` → mesaj şablonu: `f"ayna çıkışı kapatılamadı: {t} ({info.get('reason')}) — iç defter KAPALI, aynada " f"AÇIK; {info['tries']}. deneme" + (" — KORUMA BACAĞI İPTAL EDİLDİ, pozisyon ÇIPLAK" if info["naked"] else "")`
  - `meridian/loop.py:1627` → mesaj şablonu: `f"ayna pozisyonu kayıp: {sym} içeride açık, Alpaca'da ne pozisyon ne emir var"`
  - `meridian/loop.py:1642` → mesaj şablonu: `f"ayna adet sapması: {sym} — içeride {qty:g}, Alpaca'da {aq:g}"`
  - `meridian/loop.py:1664` → mesaj şablonu: `f"motor yetimi: {sym} Alpaca'da açık (motorun emri dolmuş) ama iç defterde yok"`
  - `meridian/loop.py:1668` → mesaj şablonu: `f"çıkış yetimi: {sym} iç motor çıktı ama ayna kapatılamadı — kuyrukta, " f"bir sonraki döngüde yeniden denenecek"`
  - `meridian/loop.py:1733` → mesaj şablonu: `f"ayna sapması: {tr.get('ticker')} — sim {sim} vs Alpaca {af} (%{div*100:.2f})"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `MIRROR_DRIFT` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## BROKER_REJECT {#broker_reject}

### Belirti

- Alpaca rejected an order the internal book would have executed *(kaynak: `meridian/obs.py` — `ALARM_BROKER_REJECT`)*

### Teşhis adımları

- Bu jetonu **3 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:330` → mesaj şablonu: `f"Alpaca ulaşılamıyor — ayna atlandı, {len(meta['armed'])} plan silahlı kaldı"`
  - `meridian/loop.py:396` → mesaj şablonu: `f"Alpaca reddi: {pl['ticker']} — {res.get('detail','')}"`
  - `meridian/mirror_stream.py:158` → mesaj şablonu: `f"akıştan anlık RET: {order.get('symbol')}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `BROKER_REJECT` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## TRAIL_DESYNC {#trail_desync}

### Belirti

- trailing-stop PATCH reddedildi — iç HWM ile broker stopu ayrıştı *(kaynak: `meridian/obs.py` — `ALARM_TRAIL_DESYNC`)*

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/loop.py:1458` → mesaj şablonu: `f"trail PATCH reddedildi: {sym} {frm}→{to}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `TRAIL_DESYNC` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## MECHANISM_STALE {#mechanism_stale}

### Belirti

- bir mekanizma üretmiyor/bayatladı (bütünlük dedektörleri) *(kaynak: `meridian/obs.py` — `ALARM_MECHANISM_STALE`)*

### Teşhis adımları

- Bu jetonu **8 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/selfreview.py:103` → mesaj şablonu: `f"mekanizma ÜRETEMİYOR: {name} — {detail} (üst üste {box['streak']} koşum)"`
  - `meridian/watchdog.py:125` → mesaj şablonu: `f"mekanizma gecikti: {x['name']} — {x['gap_h']} sa (pencere {x['expected_h']} sa)"`
  - `meridian/watchdog.py:1184` → mesaj şablonu: `f"BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ: {_ad} hüküm veremedi — {_dr.get('error')}"`
  - `meridian/watchdog.py:1193` → mesaj şablonu: `f"mekanizma ÜRETMİYOR: {s['name']} — {s['note']} (0 çıktı)"`
  - `meridian/watchdog.py:1199` → mesaj şablonu: `f"KORUNUM İHLALİ: {rep['conservation']['unexplained']} plan kayıtsız kayboldu"`
  - `meridian/watchdog.py:1250` → mesaj şablonu: `f"OKUNMAYAN ARTEFAKT: {_a} yazılıyor ama hiçbir modül okumuyor"`
  - `meridian/watchdog.py:1257` → mesaj şablonu: `f"MAKULLÜK: {pr['check']} — {pr['detail']}"`
  - `meridian/watchdog.py:1263` → mesaj şablonu: `f"BAYAT TÜREV: {st['artifact']} kaynağından {st['behind_h']} sa geride"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `MECHANISM_STALE` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## ARMING_READY {#arming_ready}

### Belirti

- silahlanma eşiği karşılandı — operatör kararı bekleniyor *(kaynak: `meridian/obs.py` — `ALARM_ARMING_READY`)*

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/arming.py:73` → mesaj şablonu: `f"uyuyan kurulum kapıyı GEÇTİ: {setup} — silahlanma operatör onayı bekliyor"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `ARMING_READY` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## AUTHORITY_CHANGE {#authority_change}

### Belirti

- bir mekanizmanın yetkisi açıldı/geri alındı *(kaynak: `meridian/obs.py` — `ALARM_AUTHORITY`)*
- Neden ayrı bir sınıf: KALİBRASYON YETKİ DEĞİŞİMİ 'BENİ UYANDIR' SINIFIDIR (operatör kararı 2026-07-27): bir danışmanın yetkisi EŞİK DOLUNCA KENDİLİĞİNDEN açılır ve pano bunu yalnız DUYURUR — yani operatör onay vermez, haberdar edilir. Haberin kendisi obs.log seviyesinde kalsaydı yetki devri olay defterinin içinde sıradan bir satır olurdu ve kimse bakmadan geçerdi. Kayıp da kazanım kadar yüksek sesli olmalı: yetkinin GERİ ALINMASI, sessizce alınırsa "danışman hâlâ konuşuyor" sanılır. *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Bu jetonu **2 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/analytics.py:1172` → mesaj şablonu: `f"LLM danışman yetkisi {'AÇILDI' if promoted else 'GERİ ALINDI'} — " f"R farkı {gap if gap is not None else 'ölçülmedi'}, n={len(pairs)} çift " f"(yetki: yalnız REVIEW+karşı dolum vetosu)"`
  - `meridian/nous_eval.py:303` → mesaj şablonu: `f"ÇEKİRDEK-ŞEKİLLİ ÖNERİ KUYRUĞA SOKULMAYA ÇALIŞILDI (sekil={sekil})"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `AUTHORITY_CHANGE` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## GOAL_FAILURE {#goal_failure}

### Belirti

- realized_30d < goal.failure_below — sözleşme hükmü *(kaynak: `meridian/obs.py` — `ALARM_GOAL_FAILURE`)*
- Neden ayrı bir sınıf: SÖZLEŞMENİN BAŞARISIZLIK HÜKMÜ (K1, 2026-07-30). goal.yaml `failure_below` hükmünü ("30g getiri bu eşiğin altına düşerse deney BAŞARISIZ") tanımlandığı 2026-07-14'ten beri hiçbir kod ölçmüyordu: score.py hedef tarafını (target_return_30d/max_drawdown/min_sharpe) composite'e katıyor, failure tarafını asla okumuyordu. Deney başarısız olsa bunu söyleyecek tek satır kod yoktu. Bu kendi sınıfıdır: DATA_QUALITY "veri bozuk" der, MECHANISM_STALE "mekanizma üretmiyor" der — ikisi de "mekanizma çalıştı ve sonuç sözleşmenin başarısızlık eşiğinin altında" demez. *(kaynak: `meridian/obs.py`)*

### Teşhis adımları

- Bu jetonu **1 kod yolu** ateşliyor — hangisinin konuştuğu olay kaydındaki `detail` alanından okunur:
  - `meridian/watchdog.py:1167` → mesaj şablonu: `f"SÖZLEŞME BAŞARISIZLIK EŞİĞİ: {_gf['detail']}"`
- Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `GOAL_FAILURE` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

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

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:619`
- Son damga: `state/mechanism_beats.json` → `scheduler_poll`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `scheduler_poll` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## hermes_poll {#hermes_poll}

### Belirti

- Beklenen azami sessizlik **30 dk**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: bekleme döngüsü + ısınma sprinti (sonda başına nabız) *(kaynak: `meridian/watchdog.py`)*
- `hermes_poll` PENCERESİ 30 DK KALIR AMA ANLAMI 2026-07-31'DE (WP-H/H11) DEĞİŞTİ: nabzı artık yalnız `_run` döngüsünün turu atmıyor, ISINMA SPRİNTİ de her sondada atıyor. Eskiden ısınma koşarken (nominal 1-5 sa) döngü tura dönemiyor, nabız susuyor ve bekçi SAHTE bir MECHANISM_STALE üretiyordu — mekanizma ölü değil MEŞGULdü. Nabzın sorduğu soru "döngü turladı mı" değil, "hermes ipliği canlı ve ilerliyor mu"dur; ısınma içinden atılan nabız o soruya DOĞRU cevap verir. Pencereyi ısınmaya göre genişletmek yanlış olurdu: o zaman gerçekten ölmüş bir poll ipliği de saatlerce görünmezdi. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/hermes_runtime.py:146` · `meridian/hermes_runtime.py:133` · `meridian/hermes_runtime.py:368`
- Son damga: `state/mechanism_beats.json` → `hermes_poll`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `hermes_poll` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## warmup_sprint {#warmup_sprint}

### Belirti

- Beklenen azami sessizlik **8 sa**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- `warmup_sprint` EŞİĞİ 8 SA'DA KALIR — VE ARTIK GERÇEK BİR ANOMALİ ÖLÇER. Nominal ~1-5 sa; H11'den beri aramanın KENDİ süre tavanı var (HERMES_WARMUP_MAX_MIN, varsayılan 300 dk = 5 sa) ve tavana takılan koşum kibarca kesilir. Yani 8 sa'lık bir sessizlik artık "ısınma uzun sürdü" olamaz: tavan onu 5 saatte keserdi. Kalan tek açıklama tavanın ÇALIŞMAMASIDIR (iplik asıldı, sonda içinde kilitlendi, süreç öldü) — eşiği eskiden gürültü üreten bir sayı, şimdi teşhis. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/hermes_runtime.py:145` · `meridian/hermes_runtime.py:132`
- Son damga: `state/mechanism_beats.json` → `warmup_sprint`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `warmup_sprint` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## cf_advance {#cf_advance}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı: uzun hafta sonu + tatil toleransı *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/loop.py:907`
- Son damga: `state/mechanism_beats.json` → `cf_advance`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `cf_advance` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## p5_calibrations {#p5_calibrations}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (P5 her döngüde) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/loop.py:1368`
- Son damga: `state/mechanism_beats.json` → `p5_calibrations`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `p5_calibrations` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## mirror_reconcile {#mirror_reconcile}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (alpaca modunda her döngüde) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/loop.py:1776`
- Son damga: `state/mechanism_beats.json` → `mirror_reconcile`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `mirror_reconcile` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## crosscheck {#crosscheck}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seansta bir *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:954`
- Son damga: `state/mechanism_beats.json` → `crosscheck`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `crosscheck` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## earnings_refresh {#earnings_refresh}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık (+2 gün pay) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:779`
- Son damga: `state/mechanism_beats.json` → `earnings_refresh`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `earnings_refresh` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## arming_eval {#arming_eval}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık (+2 gün pay) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:825`
- Son damga: `state/mechanism_beats.json` → `arming_eval`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `arming_eval` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## shadow_fit {#shadow_fit}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (öğrenme kadansı seans başına 1×) *(kaynak: `meridian/watchdog.py`)*
- ---- ÖĞRENME KADANSLARI (öğrenme-otomasyonu turu 2026-07-30; listeye temizlik turunda girdi) -- NEDEN GECİKMELİ GİRDİ: dört mekanizma `beat()` damgasını ZATEN atıyordu (scheduler._learning_ cadence → shadow_fit/axis2_cycle, hermes.backfill → opinion_backfill, sprint.maybe_start → sprint_cadence) ama EXPECTED'de olmadıkları için `report()` onları hiç ARAMIYORDU. Nabız atılıp kimsenin beklemediği bir mekanizma, durduğunda MECHANISM_STALE üretmez — yani bekçinin kör noktası. Dördü de artık izleniyor. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:326`
- Son damga: `state/mechanism_beats.json` → `shadow_fit`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `shadow_fit` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## axis2_cycle {#axis2_cycle}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-bağımlı (aynı kadansın 2. adımı) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:336`
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

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/hermes.py:2634`
- Son damga: `state/mechanism_beats.json` → `opinion_backfill`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `opinion_backfill` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## sprint_cadence {#sprint_cadence}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- SPRINT AYNI SINIF: `sprint.should_run` gece dilimi/aktif sprint/meşguliyet kapılarından dönebilir; her seans koşması BEKLENMEZ. Haftalık pencere "antrenman tamamen durdu"yu yakalar. *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/sprint.py:394`
- Son damga: `state/mechanism_beats.json` → `sprint_cadence`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `sprint_cadence` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## y4_collect {#y4_collect}

### Belirti

- Beklenen azami sessizlik **4 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: seans-sonrası Y4 toplama (insider delta + short interest) *(kaynak: `meridian/watchdog.py`)*
- ---- TEMİZLİK TURUNDA EKLENEN KADANSLAR (2026-07-30) --------------------------------------- *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:453`
- Son damga: `state/mechanism_beats.json` → `y4_collect`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `y4_collect` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## validation_report {#validation_report}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık kanıt raporu (+2 gün pay) *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:489`
- Son damga: `state/mechanism_beats.json` → `validation_report`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `validation_report` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## massive_verify {#massive_verify}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık grouped-vs-zincir tutarlılık ölçümü *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:505`
- Son damga: `state/mechanism_beats.json` → `massive_verify`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `massive_verify` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## shadowlaw_drift {#shadowlaw_drift}

### Belirti

- Beklenen azami sessizlik **9 gün**; aşılırsa `MECHANISM_STALE` ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*.
- Pencere gerekçesi: haftalık MEASURED_V3 kayma bekçisi *(kaynak: `meridian/watchdog.py`)*

### Teşhis adımları

- Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: `meridian/scheduler.py:517`
- Son damga: `state/mechanism_beats.json` → `shadowlaw_drift`; rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).
- mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor *(kaynak: `meridian/api.py::_sessiz_hat`)*
- nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama) *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `shadowlaw_drift` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

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

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `soft_halt` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## halt_learning {#halt_learning}

### Belirti

- kol ÇEKİLİ *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- ship DURDU (işlem sürer) — Kademe 4 kolu; rollback güvenlik olarak açık kalır *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `halt_learning` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## devre_kesici {#devre_kesici}

### Belirti

- günlük zarar kesicisi ATEŞLEDİ *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- kesici bir sonraki seansta kendiliğinden sıfırlanır — sıfırlanmıyorsa risk defterine bak *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `devre_kesici` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## nabız {#nabız}

### Belirti

- nabız damgası OKUNAMADI *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- heartbeat.json yok ya da bozuk — worker hiç tur atmadı mı *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `nabız` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

## veri_kalitesi {#veri_kalitesi}

### Belirti

- data_ok=False *(kaynak: `meridian/api.py::_sessiz_hat`)*

### Teşhis adımları

- veri kalitesi kapısı düştü — karantina ve kaynak sağlığı kartı *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*

### Çözüm / betik

- **runbook girdisi henüz yazılmadı** — onaylı kaynaklarda (betik başlıkları · mühendislik günlüğü) `veri_kalitesi` adı literal olarak geçmiyor.
- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı [Betik dizini](#betikler) bölümünde; hüküm operatöründür.

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
bilmiyoruz demektir; test yeşilliği bunu telafi etmez.
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

---

# Bilinen sınıflar ve açık kalanlar {#siniflar}

`MERIDIAN_ENGINEERING_LOG.md`'den olduğu gibi taşınır. Bir alarmın açıklaması burada
olabilir: bu depoda tekrar eden şey tek tek hatalar değil, HATA SINIFLARIDIR.

## AÇIK KALANLAR (bilinçli, sahipli) {#acik-kalanlar}

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

## KALICI RİSKLER / DERSLER {#kalici-riskler}

- Waiter/ajan-içi bekletici YASAK (iki arıza). Tam suite turda BİR kez, ön planda, senkron.
- file_lock süreç-içi; canlı worker koşarken state'e ikinci süreçten yazma.
- rsync dağıtımı tüm repoyu taşır — yarım iş canlıya gidebilir; önce dry-run + mtime.
- Sınıflandırıcı curl|sh'ı engeller → kurulumlar PyPI/pipx veya sabitlenmiş git klonuyla.
- classifier/API kesintilerinde: salt-okuma araçlarla devam + zamanlayıcılı yeniden deneme.
- pytest `-qq` tuzağı (2026-08-02): pyproject `addopts = "-q"` zaten veriyor; komuta fazladan `-q` eklemek `-qq` yapar ve "N passed" özet satırını TAMAMEN bastırır — yeşil koşu hiçbir şey basmaz, triyaj `grep -E "FAILED|ERROR"` + özet satırı ikisine birden bakar. pytest'i `-q`suz çağır.
- venv ana repo kökünde (`/Users/erdemozturk/AI-Trading/.venv`, py3.12 + pytest); worktree'lerde YOK ve sistem `python3` (3.14 homebrew) pytest içermez → testler `.venv/bin/python -m pytest` ile.

## BU OTURUMDA BULUNAN + ÇÖZÜLEN (kök nedenleriyle) {#bu-oturumda-bulunan}

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
