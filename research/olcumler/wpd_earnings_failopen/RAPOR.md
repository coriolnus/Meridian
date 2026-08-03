# WP-D KALEM 3 — earnings fail-open: TEŞHİS + İKİ SEÇENEK (kod değişikliği YOK)

**Tarih:** 2026-08-03 · **Rol:** ölçüm ajanı (WP-D turu) · **Karar sahibi:** Rol-1
**Cevaplanan ROADMAP satırı:** §WP-D "earnings kapsaması 194/251 + fail-open daraltma".
**Kapsam:** yalnız teşhis ve seçenek sunumu. Bu turda `earnings.py`ye, `guard`a, `loop`a
**dokunulmadı**; ölçüm salt-okunur kum havuzunda koştu.

## BAŞLIK HÜKMÜ

> **"194/251 kapsama" bir KORUMA ölçüsü DEĞİL** — önümüzdeki ~4 haftada rapor veren sembol
> sayısıdır. Kapsam-dışı 59 sembolün büyük çoğunluğu, raporu ufkun ÖTESİNDE olduğu için
> bilinmiyor; raporu 4 hafta ötede olan bir sembol zaten 5 günlük karartmaya giremez.
> **Gerçek risk kapsam yüzdesinde değil, ufuk marjının tükenmesinde** — ve o arıza CANLIDA
> EN AZ BİR KEZ GERÇEKLEŞTİ (2026-07-25: karartma kapısı HERKES için kapalı).

---

## 0. Veri kaynağı ve tazelik beyanı (UYDURMA YASAĞI)

| kaynak | damga | not |
|---|---|---|
| `state/earnings.csv` | mtime **2026-07-30T01:10:30** | YEREL snapshot; canlı A1'deki takvim daha taze olabilir |
| `state/events.jsonl` | son satır 2026-08-01 | yalnız 2026-07-19 → 07-29 aralığında earnings olayı içeriyor |
| `state/trade_plans.jsonl` | mtime 2026-07-30 | 390 plan, 2023-01-20 → 2026-07-28 |
| `state/trades.jsonl` | mtime 2026-07-23 | 95 işlem; mühendislik günlüğü §546: **95/95 seed, gerçek-canlı sayaç 0'dan** |

Bu snapshot **2026-08-02'deki `refresh_from_fmp` üst-küme düzeltmesinden ÖNCEsine** ait. Aşağıdaki
kapsam sayıları o düzeltmenin etkisini İÇERMEZ; canlıda yeniden ölçülmeli.

---

## 1. S1 — Kapsam-dışı sembolde kapı ne yapıyor? (koddan + davranışsal)

**Kod (`earnings.py:573 in_blackout`):**
```python
dates = _load().get((ticker or "").upper())
if not dates:
    return False        # ← FAIL-OPEN: bilgi yoksa BLOKLAMAZ
```
**Davranışsal doğrulama** (`kalem3.py`, ham çıktı `sonuc.json`):

| çağrı | sonuç |
|---|---|
| `in_blackout("ABT", <bilinen bir rapor günü>)` | `False` (ABT kapsam dışı) |
| `known("ABT")` | `False` |
| `coverage_note("ABT")` | `"NOT: earnings_kapsami_yok — … karartma kapısı KONTROL EDEMEDİ (karar DEĞİŞMEDİ)"` |
| `in_blackout("AAPL", <AAPL'ın kendi rapor günü>)` | `True` (kapı kapsam içinde çalışıyor) |

**Karar yolu:** `loop.py:1068-1088` — `_bl=False` olduğu için verdict DEĞİŞMEZ. 2026-08-01'den
beri `gate_reasons`a `COVERAGE_NOTE` **eklenir** (görünürlük), ama **NO_GO yok, REVIEW'e düşürme
yok**. `gate_checks`te `coverage: "no_calendar_data"` alanı 2026-07-21'den beri var.
Aynı kural `backtest.py:377`, `cf_backfill.py:112`, `shadow_variants.py:252`'de de uygulanır.

**Yani fail-open BUGÜN BEYANLI ama DARALTILMAMIŞ.**

---

## 2. S2 — Kapsam bugün ne, ve o sayı NE ÖLÇÜYOR

| ölçüm | değer |
|---|---|
| evren | **251** |
| takvimde sembol | 193 (`TEST` dâhil → evrende karşılığı olan **192**) |
| **evren kapsam-dışı** | **59** |
| `covered_pct` | %76,5 |
| `BLACKOUT_DAYS` | 5 |
| `REFRESH_FWD_DAYS / CADENCE / BACK` | 21 / 7 / 7 |
| **`margin_days()` = 21−7−5** | **9 gün** (pozitif ⇒ kararlı hâlde koruma GARANTİLİ) |
| `ileri_gun` (takvim bugünden kaç gün ileri görüyor) | 10 |
| `future_dates` | 69 |

### Kapsama sayısının GERÇEK anlamı — ölçüldü

Takvimin **her sembol için TAM 1 tarihi var** (193 sembol × 193 tarih). Tarih dağılımı:

- 182/193 tarih **[2026-07-22, 2026-08-19]** aralığında (son tazeleme penceresi),
- 10 tarih 2026-07-20/21 (bir önceki pencerenin kuyruğu),
- 1 tarih `TEST,2025-06-24`.

Yani **CSV ≈ TEK bir tazeleme penceresinin hasadıdır.** `earnings_refreshed` olayı bunu
doğruluyor: `2026-07-29 · source=nasdaq · new_rows=168 · total=193`.

**Sonuç:** 59 "kapsam-dışı" sembol = "önümüzdeki ~4 haftada rapor VERMİYOR". Liste bu okumayı
birebir destekliyor — ağırlıklı olarak **standart-dışı mali çeyrek** takvimli isimler
(NVDA, AVGO, COST, WMT, TGT, HD, LOW, ORCL, ADBE, CRM, NKE, FDX, MU, INTU, ISRG, LULU, ROST,
TJX, DG, DLTR, KR, AZO, BURL, STZ, MKC, HRL, CAG, SNPS, ADSK, PANW, MRVL, DE) ve **sezonun İLK
haftasında** raporlayıp pencereden çıkmış finansallar (JPM, BAC, C, GS, MS, WFC, USB, PNC, BLK,
TRV, PGR) + JNJ, PEP, UNH, GE, ABT, MDT, PLD, DAL, UAL, CCL, BKR, FISV.

**Somut kanıt (geçmiş çapa KAYBI):** GS 2026-07-14 tarihli planında **karartma vetosu yemiş**
(`gate_reasons`ta "kazanç öncesi karartma") — yani o gün takvimde VARDI. Bugün GS "kapsam dışı".
Bu tam olarak `refresh_from_fmp`in baştan-yazma kusurudur ve 2026-08-02'de üst-küme kuralıyla
düzeltilmiştir; snapshot düzeltmeden öncesine ait.

---

## 3. S3 — RİSKİN NİCELENMESİ

### 3a. "Bu 57/59'da kazanç gününde işlem açılmış mı?" → **ÖLÇÜLEMEDİ (None + neden)**

Kapsam-dışı sembolün takvimde **HİÇ tarihi yok**; geçmiş bir işlemin o sembolün kazanç gününe
denk gelip gelmediğini söyleyecek **PIT kazanç takvimi bu depoda YOK** (`earnings.csv` ileri-
pencere snapshot'ı, sembol başına 1,0 tarih tutuyor). Cevap uydurulmadı. Ölçmek için dış PIT
kaynak (NASDAQ/FMP geçmiş takvim) çekilmesi gerekir — bu tur kapsam dışı, ayrı bilet.

### 3b. Ölçülebilen vekil: kapı kaç planda KONUŞAMADI

| ölçüm | değer |
|---|---|
| plan defteri | **390** |
| `gate_checks.coverage = "known"` | 320 |
| `gate_checks.coverage = "no_calendar_data"` | **70 (%17,9)** |
| verdict dağılımı | GO 101 · REVIEW 250 · NO_GO 39 |
| **kapsam-dışı sembolde GO alan plan** | **21 / 101 (%20,8)** |
| karartma vetosu düşen plan | 4 (GS 07-14 · MMM 07-21 ×2 · NCLH 07-27) |
| `gate_reasons` metninde kapsam beyanı | 0 (beyan 2026-08-01'de eklendi, defter 07-30'da donmuş) |

İşlem defteri: 95 işlemin **25'i** bugün kapsam-dışı olan 21 sembolde (ADI, C, COST, CRM, DAL,
DE, FDX, HD, KR, LOW, MDT, MRVL, NFLX, NVDA, ORCL, PANW, PGR, SNPS, TJX, UAL, WMT).
**Ama bu 95 işlemin tamamı seed/replay'dir** (mühendislik günlüğü §546) — yani
**fail-open'ın CANLIDA gerçekleşmiş zararı: payda 0.**

### 3c. YAN BULGU — replay/backtest'te karartma kapısı YAPISAL OLARAK ÖLÜ (PIT ihlali)

`backtest.py:377` `in_blackout(sig.ticker, <replay tarihi>)` çağırıyor ama takvim **PIT değil**,
bugünkü ileri-pencere snapshot'ı. Ölçüm: 390 planın **yalnız 10'unda** takvimde plan tarihinden
sonraki 0-5 gün içinde bir rapor tarihi VAR. Yani **380 planda (%97,4) `in_blackout` kapsam
alanından bağımsız olarak zaten `False` dönüyordu.**

İki sonucu var:
1. Replay/gölge sonuçları karartma kapısının etkisini **hiç içermiyor** — kapı canlıda diri,
   kapıda ölü (bu deponun bilinen "aynı yasanın iki motorda ayrışması" sınıfı).
2. Tarihsel planlardaki `coverage: "known"` etiketi **plan tarihindeki değil, BUGÜNKÜ** kapsamı
   yansıtıyor; geriye dönük okunduğunda yanıltıcı.

### 3d. YAN BULGU — fail-open CANLIDA GERÇEKLEŞTİ

`state/events.jsonl`:
- `2026-07-19T23:09:40 earnings_calendar_gave_up attempts=5`
- `2026-07-25T07:36:58 MECHANISM_STALE … earnings_calendar — gelecek tarih yok (son: 2025-06-24)`
  **— karartma guard'ı fiilen kapalı (0 çıktı)**

Yani 2026-07-19 tazelemesi tutana kadar takvimde tek satır (`TEST,2025-06-24`) vardı ve kapı
**251 sembolün 251'inde** geçirgendi. Bu, "59 sembolde geçirgen"den iki kat mertebe büyük bir
maruziyettir ve `covered_pct` metriği onu **görünmez kılar** (0/251 iken de "kapsama" bir sayı
üretir).

### 3e. Küçük hijyen bulgusu

`state/earnings.csv` içinde **`TEST,2025-06-24`** satırı var — test fikstürü üretim defterine
sızmış. Zararsız değil: `coverage().max_date`i geriye çekiyor ve MECHANISM_STALE mesajındaki
"son: 2025-06-24" tam olarak bu satırdır. (Düzeltme bu ajanın yazma kapsamı dışında.)

---

## 4. İKİ SEÇENEK (karar Rol-1'de)

### SEÇENEK A — DARALT: fail-closed'ı SEMBOLE değil TAKVİME bağla

**Ne:** "sembol bilinmiyor" ile "kapı konuşamıyor" ayrılır. Kapı yalnız **takvimin kendisi
güvenilmezken** kapanır:

- **A1 (asıl):** `coverage().inert` ya da `ileri_gun < BLACKOUT_DAYS` ya da son tazeleme penceresi
  kapsaması `EARNINGS_FMP_FALLBACK_COVERAGE` altındaysa → o turda **tüm** semboller karartma
  varsayılanına düşer (GO → REVIEW; NO_GO değil, çünkü kapının kör olması sembolün suçu değil).
- **A2 (ucuz, bağımsız):** `scheduler`ın pes-ederken **hafta damgasını YAKMAMASI** — bu zaten
  `scheduler.py`de "İKİNCİSİ HÂLÂ AÇIK" diye yazılı; ardışık iki pes ileri kapsamayı 0'a indiriyor.
- **A3 (opsiyonel):** kapsam-dışı sembolde varsayılan **REVIEW** (GO değil).

**Maliyet ölçüldü:** A3 uygulansaydı bu defterde 70/390 plan (%17,9) ve 21/101 GO planı (%20,8)
etkilenirdi. **A3'ün risk azaltımı ise düşük**, çünkü kapsam-dışılık ağırlıklı olarak "raporu
4 hafta ötede" demek. A1+A2 ise ölçülen GERÇEK arızayı (2026-07-25) kapatır ve normal işleyişte
**hiçbir planı etkilemez** (bugün `ileri_gun=10 > BLACKOUT_DAYS=5`).
→ **Bu ajanın teknik okuması: A1+A2 kazanç/maliyet oranı yüksek; A3 kötü pazarlık.**

### SEÇENEK B — MEVCUT KALSIN + İZLEME

**Ne:** karar yolu değişmez (fail-open + beyanlı not), yalnız **ölçü aleti** düzelir:

- `covered_pct` panodan/karneden **birincil metrik olmaktan çıkarılır**; yerine
  **`ileri_gun ≥ BLACKOUT_DAYS`** değişmezi ve son tazeleme penceresinin gün-kapsaması konur.
- `ileri_gun < BLACKOUT_DAYS` → **ALARM** (bugün yalnız `earnings_calendar_gave_up` ve
  `MECHANISM_STALE` var; ikisi de arıza ANINDA değil, sonucunda konuşuyor).
- `earnings_refresh_window_partial` olayı **kaç plan** etkilediğiyle birlikte sayılır.
- Kapsam-dışı GO planlarının oranı haftalık karneye eklenir (bugün %20,8 — taban ölçüldü).

**Maliyet:** kod değişikliği yok denecek kadar az, karar yolu risksiz. **Riski:** ölçülen arıza
(2026-07-25) tekrarlarsa yine **sonradan** öğreniriz — izleme, kapı değildir.

---

---

## 4b. ROL-1 KARARI VE UYGULAMA (2026-08-03, teşhisten SONRA eklendi)

**Karar: SEÇENEK A1 + A1b UYGULANDI · A3 UYGULANMADI · ayrıca REPLAY-PIT düzeltmesi.**
Bu bölüm raporun geri kalanını geçersiz kılmaz — §1-§3 teşhisin ÖLÇÜM hâlidir ve karar onun
üstüne bindi.

| # | ne | dosya |
|---|---|---|
| A1-yüklem | `calendar_untrustworthy()` — takvim karartma ufkunu taşıyamıyorsa sebep döner (`takvim_atil` · `ufuk_tukendi` · `kismi_pencere`); iki bilinçli istisna: takvim DOSYASI hiç yoksa ve pencere kapsaması ÖLÇÜLMEMİŞSE tetiklemez | `meridian/earnings.py` |
| A1-hüküm | tur başına BİR kez ölçülür; sebep varsa TÜM planlar karartma varsayılanına düşer **GO→REVIEW** (NO_GO'ya dokunulmaz), YASA-4 gerekçeli `earnings_calendar_untrustworthy` olayı + `daily_cycle` sayacı | `meridian/loop.py` |
| A1b | pes ederken **hafta damgası yakılmıyor**; fren GÜN damgası (`earnings_gaveup_day`) — ertesi gün yeniden dener, sabır sınırı (5 deneme) korunur | `meridian/scheduler.py` |
| 2 | **replay-PIT**: `backtest.replay` bugünün takvimini tarihsel plana uygulamayı BIRAKTI — `in_blackout` çağrısı yok, veto yok, etiket dürüst (`olculemedi_replay`), sayaç `BacktestResult.earnings_gate` | `meridian/backtest.py` |

**"0 plan etkilendi" çivisi:** `tests/test_wpd_takvim_kapisi_v184.py` — canlı-benzeri takvimde
yüklem `None` döner (davranış) **ve** düşürme bloğu yüklemin içinde yaşar (yapı). İkisi birlikte
kanıttır; normal işleyişte GO seti değişmez.

**A3 neden uygulanmadı (beyan çürümesin diye teste bağlandı):** kapsam-dışı sembolde fail-open
DEVAM EDİYOR. Ölçülen maliyet 70/390 plan, ölçülen kazanç ≈ 0 — çünkü kapsam-dışılık ağırlıklı
olarak "raporu 4 hafta ötede" demek.

### Bu turda KAPATILMAYAN, aynı sınıftan iki kalem (kapsam dışıydı → ayrı bilet)
`backtest.replay` ile **aynı PIT ihlali** iki kardeş modülde daha var ve bu tur onlara
dokunulmadı (dosya-ayrıklık sözleşmesi):
- `meridian/cf_backfill.py:112` — `earnings.in_blackout(c["ticker"], dstr)`, `dstr` tarihsel
- `meridian/shadow_variants.py:252` — `earnings.in_blackout(sig.ticker, date)`, `date` tarihsel

İkisi de bugünün ileri-pencere takvimini geçmiş bir karara uyguluyor; yani cf defteri ve gölge
varyant tabloları da karartma etkisini "uygulanmış gibi" taşıyor. Düzeltme replay'dekiyle
birebir aynı olmalı (çağrıyı kaldır, etiketi `olculemedi_replay` yap, sayacı rapora bağla).

## 5. Yeniden üretim
```
mkdir -p <sandbox>/state
cp research/olcumler/wpd_earnings_failopen/kalem3.py <sandbox>/
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python kalem3.py
```
Betik `MERIDIAN_ROOT`u kendi dizinine sabitler ve `state/earnings.csv`nin KOPYASI üzerinde
çalışır; üretim `state/`ine yazmaz.
