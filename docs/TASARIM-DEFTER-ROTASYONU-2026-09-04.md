# TASARIM — Append-only state defterlerinin okuma bedeli ve rotasyonu (TSK-137) — 2026-09-04

Durum: H1 TASLAK (Rol-1; keşif Explore ajanı 2026-09-04 15:0xZ, bütün sayılar ölçülmüş). Operatör onayı BEKLİYOR — sorular §5.

## 1. Ölçülen gerçek

| Defter (A1, 2026-09-04) | Boyut | Yazar | Günlük hacim |
|---|---|---|---|
| `state/events.jsonl` | 26,5 MB (~31 k satır) | `obs._emit` (worker 12 sn'de bir) | ~536 satır/gün ort., pik 7.256 (tek `hotstate_down` seli) — yerel ölçüm |
| `state/intraday_decisions.jsonl` | 19 MB | `intraday_cycle.IntradayConsumer._handle_symbol` (kapanan 1-dk bar × sembol) | ölçülmedi (bu belgede açık kalem) |
| `state/validation_ledger.jsonl` | 1,08 MB / 398 satır | `validation.record_candidate` (learn kapalı — son yazım 2026-08-21) | 1–5 satır/gün → TSK-128, aciliyet düşük |

`store.read_jsonl(name, limit=N)` dosya-yolu dalında dosyanın TAMAMINI okuyup ayrıştırır, `limit`i sonda `rows[-limit:]` ile uygular
(seek-from-end YOK). SQLite yolu (`storage.read_rows`, 6 varlık: trades/trade_plans/scoreboard/portfolio/equity_curve/shadow_books)
gerçek kuyruk okur (`ORDER BY seq DESC LIMIT`) — events/intraday_decisions o yolda DEĞİL.

## 2. Okuyucu envanteri (events.jsonl) — bedel = tam dosya × sıklık

| Okuyucu | limit | Kadans | Sunucu önbelleği |
|---|---|---|---|
| `notify.inbox` (EVENT_WINDOW 4000) → `/api/alerts` | var | pano 15 sn | YOK |
| `analytics._hayalet_suzulen_n` (15.000) → `learning_scorecard` → `/api/hermes` | var | pano 30 sn | YOK |
| `watchdog.integrity_report` (7 dedektör, tek okuma) → `/api/diagnostics` | yok | 20 sn TTL + uç 45 sn | var |
| `hermes.bg_on_eleme_karnesi` (4000) → `/api/diagnostics` | var | aynı | var (aynı cache-miss'te 2. tam okuma) |
| `watchdog.check_integrity_and_alarm` | yok | günde 1 | — |
| `selfreview.build` | yok | haftalık | — |
| `api._son_dongu_olaydan` → `/api/today` | — | 15 sn | ZATEN seek-from-end (512 KB/4 MB kademeli + mtime önbelleği) — EMSAL |

`intraday_decisions.jsonl`: `health.faz6_kilitleri` + `api.py` `_idec` — aynı `/api/diagnostics` gövdesinde aynı dosya İKİ kez tam okunuyor
(45 sn önbellek arkasında). `intraday_shadow_orders.jsonl` aynı yapıda.

Mevcut emsal/altyapı: `ops/olay_sikistir.py` (TSK-020 adım-2, 2026-09-03) geçmiş ayları `state/olaylar/AAAA-AA.parquet`e sıkıştırır, DEFTERİ
KIRPMAZ (adım-3 açık); `ops/olay_sorgu.py` jsonl+parquet'i "parquet kazanır" kuralıyla birleştirir; litestream yalnız SQLite; gece yedeği
`state/`in tamamını tar'lar (26,5 + 19 MB her gece). Testler: 142 dosya events.jsonl adını geçiriyor, hepsi sandbox — canlı içeriğe çivili yok.

## 3. Seçenekler (risk sırasıyla)

(c) **`store.read_jsonl(limit=)` kuyruk okuma (seek-from-end)** — imza sabit, `_son_dongu_olaydan` emsali; kazanç `limit` veren üç sık okuyucuda
(inbox 15 sn, hayalet sayacı 30 sn, bg_on_eleme). `limit=None` okuyucular değişmez (tam tarih isteyenler). EN DÜŞÜK RİSK, kısmi kazanç.
(b) **Boyut/ay eşikli kırpma + arşiv** — `olay_sikistir` adım-3: parquet'e alınmış aylar jsonl'den düşürülür; `limit=None` okuyucular
"tüm tarih" için `olay_sorgu`nun birleşik görünümüne taşınmalı (integrity_report, selfreview.build, check_integrity_and_alarm, alarm_backlog_digest).
Orta risk: okuyucu sözleşmesi değişir; kazanç tam (dosya küçülür, yedek küçülür).
(a) **Günlük dosya dönüşü** — bütün okuyucular çok-dosyalı olmalı; en çok dokunuş. ÖNERİLMEZ.

## 4. Öneri (Rol-1)

Adım-1 (S, TSK-137a): (c) — `read_jsonl` kuyruk okuma + `/api/alerts`e kısa (15 sn) sunucu önbelleği; bedel ölçümü önce/sonra (ms/çağrı, A1).
Adım-2 (M, TSK-137b = TSK-020 adım-3): events.jsonl kırpma parquet'e bağlı (cari ay + son N gün jsonl'de kalır; `limit=None` okuyucular
`olay_sorgu` görünümüne); intraday_decisions için önce hacim/gün ölçümü, sonra aynı mekanizmanın defter-parametrik hâli.
Yasa 6: parquet arşivinin okuyucusu `olay_sorgu.py` + selfreview/integrity (adım-2'de bağlanır) — beyanlı.

## 5. Operatör soruları

1. Kapsam: TSK-137 = TSK-020 adım-3'ü de kapsasın mı (tek kalem), yoksa adım-3 TSK-020 altında ayrı mı kalsın?
2. Adım-1 (kuyruk okuma + alerts önbelleği) hemen açılsın mı — düşük risk, ölçülebilir kazanç?
3. `limit=None` okuyucular (bütünlük/öz-inceleme) kırpma sonrası DuckDB birleşik görünümüne mi taşınsın, yoksa "cari + son N gün" penceresi yeter mi?
4. intraday_decisions.jsonl: önce hacim/gün ölçümü (bu belgeye eklenir), sonra karar — uygun mu?
