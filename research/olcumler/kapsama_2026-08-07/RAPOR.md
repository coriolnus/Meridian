# `universe_coverage` — kümülatif sayaç kusuru (bütünlük dökümü D5) · 2026-08-07 · v206

Koşum: `.venv/bin/python research/olcumler/kapsama_2026-08-07/olc.py --sim` (SALT OKUR).
Girdi: `state/events.jsonl` — 27.593 satır, ts aralığı `2026-07-14T09:36:31Z → 2026-08-07T06:59:31Z`.
Bu dosya canlı defterin YEREL KOPYASIDIR; canlı olay akışı 2026-07-30'dan sonra bu kopyaya
işlemiyor (2026-07-31 → 08-06 arası 0 satır). Ölçümün canlıyla örtüştüğü, eski hükmün birebir
yeniden üretilmesiyle KANITLANDI (aşağıda).

## 1. ÖLÇÜM

| büyüklük | ölçülen |
|---|---|
| `session_bar_never_published` **olay** sayısı (30 gün) | **165** |
| aynı olayların **ayrık seans** sayısı | **7** |
| en yoğun seans | `2026-07-15` → **159 olay** (toplamın %96'sı) |
| diğer seanslar | 07-17, 07-22, 07-23, 07-27, 07-28, 07-29 → her biri 1 olay |
| son atlanan seans | **2026-07-29** (hüküm gününden 9 gün önce) |
| `universe_coverage_low` | **0** |
| `session_deferred_for_coverage` (yerel kopyada) | 720, hepsi `coverage = 1.0` |

159 olayın kaynağı kodda yazılı: `scheduler._rehydrate` (2026-07-22, `scheduler.py:185`) öncesi
tazeleme tavanı SÜREÇ BAŞINAydı ve tek seans için 159 kez "yayınlanmadı" uyarısı düştü. Yani
**bir sayaç kusurunun kalıntısı, ikinci bir sayaç kusuru tarafından "165 seans" diye okunuyordu.**

## 2. ESKİ HÜKÜM — birebir yeniden üretildi

```
ok = False
detail = "165 seans evren kapsaması yetersiz olduğu için ATLANDI (son: 2026-07-29 %17)
          — kaynak yayınlamıyor"
```

Rol-1'in canlı A1'de gördüğü satırın AYNISI. Dört kusur:

1. **Olay ≠ seans.** `len(skipped)` olay sayar, metin "seans" der (165 ↔ 7).
2. **Hüküm kümülatif.** `_cov_ok = not low and not skipped` — 30 günlük OKUMA penceresindeki her
   geçmiş ihlal `ok`u düşürüyordu; iyileşme yapısal olarak görünemezdi.
3. **Zaman kipi.** "ATLANDI … kaynak yayınlamıyor" şimdiki zamandır; ölçülen olgu 9 gün önceydi.
4. **Sağlıklı kanıt çöpe gidiyordu.** `defer` listesi (`session_deferred_for_coverage`)
   hesaplanıyor, `low` türetildikten sonra HİÇ kullanılmıyordu — "kaynak bugün yayınlıyor mu"
   sorusunun cevabı tam o listedeydi.

## 3. YENİ HÜKÜM (v206) — aynı girdide

Yerel kopya (kanıt akışı 07-29'da donmuş):
```
ok = False · guncel_ihlal_seans = 4 · tarihsel_ihlal_seans = 7 / 165 olay
"GÜNCEL (son 5 seans): 4 seans ATLANDI (…, 2026-07-27, 2026-07-28, 2026-07-29) — bu seanslarda
 kaynak barı yayınlamadı, son ölçülen kapsama %100 (2026-07-29) · DEFTER TOPLAMI (30 günlük okuma
 penceresi): 7 ayrık seans / 165 alarm satırı, sonuncusu 2026-07-29"
```
Bu kopyada `ok=False` **DOĞRUDUR**: defterde kapsamanın düzeldiğine dair tek satır yok.

SİMÜLASYON (yerel defter + Rol-1'in canlıda ölçtüğü 7 seansın imzası — **canlı ölçüm değildir**):
```
ok = True · guncel_ihlal_seans = 0 · tarihsel_ihlal_seans = 7 / 165 olay
"GÜNCEL (son 5 seans, son kanıt 2026-08-07): kapsama ihlali YOK — 5 seansta evren eşiği (%90)
 tuttu, son ölçülen kapsama %99.6 (2026-08-07); kaynak YAYINLIYOR · TARİHSEL (hüküm penceresinin
 DIŞINDA, İHLAL DEĞİL): 7 ayrık seans / 165 alarm satırı, sonuncusu 2026-07-29"
```

## 4. PENCERE ve EŞİK — nereden geliyor

Sihirli sayı yok: `watchdog._kapsama_penceresi()` ikisini de MOTORDAN okur.

* pencere = `loop.UNIVERSE_LAG_MAX_D` (=5) — motorun bir seansın barını kovaladığı ufuk; ötesi
  motorun zaten pes ettiği yerdir, yani TARİHTİR.
* eşik = `loop.UNIVERSE_MIN_COVERAGE` (=0,90) — `scheduler.py:890`'daki "tek yasa, tek ölçüm".
* Pencere DUVAR SAATİ değil SEANS sayar: kusurun yarısı tam olarak olay-sayısını-seans-sanmaktı;
  159 olaylık fırtına seans ekseninde bir (1) seanstır.
* Motor sabitleri okunamazsa bekçi SUSMAZ: `kapsama_penceresi_okunamadi` uyarısı + watchdog'daki
  beyanlı yedek (YASA 4).

## 5. "kaynak yayınlamıyor" iddiası — BUGÜN doğru mu

**Hayır.** Cümle eski kodda KOŞULSUZDU (atlama varsa her zaman ekleniyordu). Ölçüm: son yedi
seansın `session_deferred_for_coverage` kapsaması 1,0 ×6 + 0,996 (Rol-1, canlı) ve yerel kopyadaki
720 erteleme olayının hepsi `coverage=1.0`. Kaynak **yayınlıyor**; olan şey T+1 GECİKMEdir ve
motorun kapsama kapısı bunu tasarım gereği karşılıyor (`loop.py:908`, "gecikmeli ücretsiz veriyle
bir gün geride olmak dürüsttür"). Yeni metin iddiayı yalnız GÜNCEL penceredeki atlamadan türetir
ve temiz pencerede "kaynak YAYINLIYOR" der — ikisi de ölçüme bağlı.

## 6. AYNI SINIFTAN BAŞKA DEDEKTÖR (tarama, düzeltme YOK)

`watchdog.py`'deki tüm `ok` ifadeleri + `sieve`/`ledgers`/`recompute`/`production` tarandı.

| dedektör | kümülatif mi | hüküm |
|---|---|---|
| `parity:universe_coverage` | **EVET** | bu turda DÜZELTİLDİ |
| `parity:alarm_delivery` | evetti | **2026-07-26'da AYNI reçeteyle düzeltilmiş** (`_kalan = _tot − _absorbed`) — emsal |
| `conservation` (`unexplained`) | **EVET** | pencere BİLEREK en eski plana kadar açık (C6); 2026-07-14 öncesi bir kayıp satırı sonsuza dek kırmızı tutar. Kapsam dışı, ölçülmedi — **Rol-1'e kalem** |
| `parity:measured_edge` | kısmen | rejim istatistiği; eski kötü örneklem sonsuza dek ortalamada kalır. Bir OLAY sayacı değil, ÖLÇÜM — sınıf farklı |
| `ledger_contract:*` | hayır | `validate_live(sample=200)` — son 200 satır |
| `intraday_damga:*` | hayır | `sample=500` |
| `event_ledger_domination` / `hotstate_sustained_down` | hayır | 2 gün / 1 gün penceresi |
| `eleme:*` (sieve) | hayır | `Sieve.flush` aşama başına SON koşumu tutar (kümülatif değil) |
| `yeniden_hesap:*` (recompute) | hayır | `trades[-400:]` |
| `production:starved` | hayır | "hiç üretmiş mi" — iyileşme anında yeşile döner |
| `cf_fidelity_join`, `llm_pair_join` | hayır | aynı gerekçe (tek başarı bayrağı düşürür) |

## 7. AÇIK KALEM (bu ajanın yetkisi dışında)

`docs/RUNBOOK.md` üretilen belgeyle ayrıştı: `test_uiux_s1b_v154::test_t3_diskteki_belge_kaynakla_ayrismamis`
kırmızı. Fark **yalnız satır numarasıdır** (watchdog.py'deki alarm yerleri +180 satır kaydı;
1460→1640, 1477→1657, 1503→1683 — hepsi aynı delta, içerik farkı YOK). Testin kendi belgesinin
dediği gibi bu "hata değil haber"dir; çözümü tek komut: `python ops/runbook_uret.py`.
`ops/` ve `docs/` bu turun yazma listesinde olmadığı için KOŞULMADI.
