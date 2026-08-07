# BAYAT SERMAYE — AYNANIN YARIM BOYUTLU EMRİNİN KÖKÜ (ölçüm: 2026-08-07)

**Okuyucu:** Rol-1 (hüküm) + operatör (karar).
**Tur sınırı:** SALT ÖLÇÜM + BELGE. `meridian/` altında hiçbir dosya değiştirilmedi; git komutu
koşulmadı; canlıya dağıtım yapılmadı; broker'a emir gönderilmedi/iptal edilmedi.
**Kanıt tabanı:** canlı A1 (`ubuntu@130.61.126.87`), salt-okunur (`sqlite3 … mode=ro`, `tar -xzO`,
stdin'den beslenen betikler). Canlı `state/`e tek bayt yazılmadı. Yedekler `/home/ubuntu/backups/
state-2026-08-0{2..6}.tar.gz` (günlük, 23:30-23:33Z, içinde `state/meridian.db.yedek` =
`storage.backup_to` ile alınmış tutarlı kopya).

---

## 1. HÜKÜM (tek cümle)

Ayna 5 Ağustos'ta emri yarım boyutta gönderdi çünkü **o an kitabın boyut tabanı 94.457,91$'dı**:
1 Ağustos'ta 100.000$ tabanına taşınmış olan `portfolio.realized_pnl`, **4 Ağustos'ta defterin
eski tabanına (−5.542,09$) geri çekilmişti** ve o hâl 5 Ağustos 22:31:56Z'ye kadar sürdü. Ayna
22:10:01Z'de, yani **onarımdan 21 dakika 55 saniye ÖNCE** gönderdi. İç motor ertesi sabah,
onarımdan sonraki tabanla (çarpan 1,0) doldurdu. Sapma bir ayna kusuru değil, **aynı planın iki
bacağının kitabı 22 saat arayla, ARADA DEĞİŞMİŞ hâlde okumasıdır**.

`eq_now` bayat DEĞİLDİ — o anki kitabı doğru okudu. **Bayat olan KİTABIN KENDİSİYDİ.**

---

## 2. ÖLÇÜLEN ZAMAN ÇİZELGESİ (her satırın kaynağı yazılı)

| An (UTC) | Olay | `portfolio` cash / realized / peak | beyan | Kaynak |
|---|---|---|---|---|
| 08-01 15:14:29 | `meridian.sermaye --uygula` — taban taşındı | 100000 / **0,0** / 100000 | **VAR** | `events.jsonl` `paper_equity_reset`; yedek DB 08-02 & 08-03 (`entity_meta.rev=3`) |
| 08-04 01:15:37 | `loop._save_broker` (o günkü kod: TAM-belge, 13 anahtarlık beyaz liste) | 100000 / 0,0 / 100000 | **SİLİNDİ** | `hotstate_write_disabled where=_save_broker`; 01:16:13'teki üç MAKULLÜK alarmı diski okuyor (`nakit 100.000,00$`, `broker muhasebesi 0,00$`, ofset 0) |
| 08-04 01:16:13 | `daily_cycle` (date=08-03) | eq_now = **100000,0** | — | `events.jsonl` `daily_cycle.equity` |
| 08-04 07:09–07:54 | dağıtım: `uv.lock`, `storage.py`, `ops/sermaye_beyani_iade.py`, iki test, KOKNEDEN.md | — | — | A1 `find -newermt` (mtime) |
| **08-04 07:54 ↔ 21:47 arası** | **TERS ONARIM — kitap defterin eski tabanına çekildi** | **94457,91 / −5542,09** / (peak 100000 kaldı) | yok | çıkarım + dışlama, §7 |
| 08-04 21:47:54 | `loop._save_broker` bu hâli çimentoladı (`rev=5`) | 94457,91 / −5542,09 / 100000 | yok | yedek DB 08-04; `meridian.db-wal` içindeki belge çerçevesi birebir |
| 08-04 21:48:25 | `daily_cycle` (date=08-04) | eq_now = **94457,91** | — | `daily_cycle.equity` |
| **08-05 22:10:01** | **`mirror_submit_armed` … `kaynak="loop"` — 3 emir gönderildi** | çarpan **0,4916** | yok | `alpaca_orders_sent {n:3, equity:100012.07, kaynak:"loop"}` |
| 08-05 22:10:48 | `daily_cycle` (date=08-05) | eq_now = **94457,91**, armed 3 | — | `daily_cycle.equity` |
| **08-05 22:31:56** | **`ops/sermaye_beyani_iade.py --uygula`** — taban + beyan iade (`rev=7`) | 100000 / 0,0 / 100000 | **VAR** | yedek DB 08-05 (`doc.updated_at`), worker yeniden başlatma izleri 22:29:42/22:30:40/22:32:03 |
| 08-06 10:32:46 | `mirror_submit_armed` … `kaynak="pano"` — AMGN gönderildi | çarpan **0,4916** (nabızdan) | VAR | `alpaca_orders_sent {n:1, equity:100011.45, kaynak:"pano"}`; nabız §6 |
| 08-06 13:30–13:33 | Alpaca dolumları: 25 / 37 / 22 / 22 | — | — | `mirror_stream_event` |
| 08-06 20:33:29 | iç motor doldurdu: 54 / 64 / 43 / 33 → **4 × MIRROR_DRIFT** | eq_now tabanı 100000 → çarpan **1,0** | VAR | `MIRROR_DRIFT` alarmları + kitaptaki pozisyonlar |

`entity_meta.rev` ve `doc.updated_at` her yedekte mikro-saniye farkla eşleşiyor (3 → 5 → 7 → 11),
yani **`store` üzerinden geçen her yazım damgalı**; damgasız bir içerik değişimi `store` DIŞINDAN
gelmiş demektir (§7).

---

## 3. `eq_now`UN TAM YOLU (kaynaktan çıkarıldı)

```
loop.daily_cycle
  ├─ 1024  b, meta = _load_broker()
  │          └─ loop.py:654-659   b = PaperBroker(START_EQUITY=100_000)        # score.py:11
  │                               b.cash        = st["cash"]                   # portfolio.json
  │                               b.realized_pnl= st["realized_pnl"]           # portfolio.json
  │                               b.positions   = st["positions"]
  ├─ 1067  eq_now = b.equity(marks_open)
  │          └─ broker.py:357-364  eq = self.start_equity + self.realized_pnl
  │                                   + Σ qty·(mark − entry)                   # ← `cash` OKUNMAZ
  ├─ 1069  meta["peak_equity"] = max(meta.get("peak_equity", 100_000), eq_now)
  ├─ 1070  size_mult = derisk_mult(eq_now, meta["peak_equity"])                # İÇ MOTOR
  └─ 1584  mirror_submit_armed(meta, dstr, eq_now=eq_now, …, source="loop")    # AYNA
             └─ loop.py:556  alpaca.submit_plan(pl, eq,
                                size_mult=derisk_mult(eq_now, meta["peak_equity"]))
```

**Hangi dal koştu — ÖLÇÜLDÜ.** `loop.py:527-532`'deki nabız yedeği (`eq_now is None` →
`heartbeat.json["equity"]`; yoksa gönderim REDDEDİLİR) **5 Ağustos'ta KOŞMADI**: döngü `eq_now`u
parametre olarak geçiyor ve olay `kaynak="loop"` taşıyor. Nabız dalı yalnız pano düğmesinde
(`api.py:3762`, `mirror_submit_armed(meta, dstr, source="pano")` — `eq_now` GEÇİRİLMEZ) koşar ve
**6 Ağustos 10:32:46'daki AMGN gönderimi tam olarak o daldan çıktı** (§6).

**Kritik ince nokta (`sermaye.py` başlığında yazılı, canlıda doğrulandı):** `PaperBroker.equity()`
`cash`i HİÇ okumaz. Yalnız `cash`i düzelten bir onarım panoyu düzeltir, **boyutlandırmayı
düzeltmez**; yalnız `realized_pnl`i kıpırdatan bir yazım ise panoda görünmeden emir boyutunu yarar.
Canlıda olan İKİNCİSİDİR.

---

## 4. SERMAYE BEYANININ YAZICI / TÜKETİCİ HARİTASI

### Yazıcılar (`portfolio.sermaye_resetleri`)
| Yol | Ne yazar | Olay bırakır mı |
|---|---|---|
| `meridian/sermaye.py:393` (`uygula`) | kaydı + dört alanı (cash · realized_pnl · day_start_equity · peak_equity) | **evet** — `paper_equity_reset` + `monotonic_amnesty_granted` |
| `ops/sermaye_beyani_iade.py` (`--uygula`) | kaydı + üç alanı (peak BİLEREK dışarıda), `update_json` yaması | **hayır** (stdout raporu var, obs olayı yok) |
| `loop._save_broker` (`loop.py:747`) | 13 sahiplenilmiş alan; bugün YAMA + D2 ratchet | reddederse alarm; başarılıysa olay yok |
| `run._reset_book_to` (`run.py:109`) | TAM belge yazar → kaydı **siler** (aynı sınıf, ikinci yazar) | `replay_seed` yolu |
| `hermes.py:2978`, `api.py:3773`, `loop.py:454` | belgeyi yamalar (llm_opinion / alpaca_submitted / onay) — kayda dokunmaz | — |

### Tüketiciler
| Yol | Ne yapar |
|---|---|
| `sermaye.resetler()/ofset()/ayrisik()` | kaydı okuyan **TEK** yer |
| `recompute._sermaye_ofseti` → üç kimlik | `realized_pnl` · `cash_identity` · `equity_curve_tail`; ofseti GEÇMİŞTEN türeyen tarafa ekler |
| `broker.beyan_olcusu/beyan_gerilemesi` | iki tüketici: `loop._save_broker` D2 ratchet + `watchdog.monotonicity_report` tabanı |
| `web/app.js:2162` | pano "beyan-ofset" rozeti |

### EKSİK TÜKETİCİ — ADIYLA
> **BOYUTLANDIRMA YOLUNDA BEYANIN TÜKETİCİSİ YOKTUR.**
> `loop.daily_cycle:1067` (`eq_now`), `loop.py:556`/`1070` (`derisk_mult`) ve
> `health.write_heartbeat(equity=…)` `portfolio.realized_pnl`i **doğrudan** okur ve
> `sermaye.ofset()`e **hiç sormaz**. Beyan, kitabın tabanının nerede DURMASI GEREKTİĞİNİ söyleyen
> tek kayıttır; ama emir boyutunu üreten zincir onu okumaz. Bu yüzden taban kaydığında
> boyutlandırma sessizce kayar ve tek fark edici (§5'teki üç kimlik) beyan silinmişse **yeşil
> kalır**.

---

## 5. 3. MADDEDEKİ ÇELİŞKİNİN ÇÖZÜMÜ

`alpaca_orders_sent` olayının `equity` alanı **`eq_now` DEĞİLDİR**:

```python
# loop.py:552-556
eq = float(acct["equity"]) if acct and "equity" in acct else START_EQUITY   # ← ALPACA HESABI
out["equity"] = eq
alpaca.submit_plan(pl, eq, size_mult=derisk_mult(eq_now, meta.get("peak_equity", …)))
# loop.py:625
obs.log("alpaca_orders_sent", n=sent, equity=eq, kaynak=source)             # ← `eq` basılır
```

Yani **100.012,07$ / 100.011,45$ = Alpaca PAPER hesabının öz sermayesi** (aynanın boyut PAYDASI),
`eq_now` ise iç defterin öz sermayesi (yalnız ÇARPANI belirler) ve o gün olay defterinde **başka
bir satırda** duruyor: `daily_cycle.equity` = **94.457,91$** (08-04 21:48:25 ve 08-05 22:10:48).
Çelişki yok — **iki farklı büyüklük, iki farklı olay alanı.**

`derisk_mult`in **PAYDASI da dışlandı**: `peak_equity` her ölçümde **100.000,0** (yedek DB 08-04 /
08-05 / 08-06 + canlı). 1 Ağustos affıyla 102.520,45 → 100.000 taşınmıştı ve orada kaldı. Yani
kusur payda değil **PAY** tarafındaydı.

---

## 6. DÖRT BACAĞIN ARİTMETİĞİ — BİREBİR YENİDEN ÜRETİLDİ

Boyut yasası: `qty = ⌊ size_r · 0,01 · equity · size_mult / (referans − stop) ⌋`
(`broker.RISK_PCT_PER_R = 0.01`, `broker.size_position`).
Plan tetikleri canlı `trade_plans` tablosundan, dolumlar `portfolio.positions`tan okundu.

| Plan | size_r | tetik → stop | AYNA (eq=Alpaca, çarpan **0,4916**) | İÇ MOTOR (eq=100.000, çarpan **1,0**) | canlı sapma |
|---|---|---|---|---|---|
| NUE | 0,89 | 274,57 → 257,4033 | 437,60/17,1667 = **25** | dolum 273,6478: 890,00/16,2445 = **54** | 54 vs 25 ✓ |
| EMR | 0,74 | 162,16 → 152,4839 | 363,86/9,6761 = **37** | dolum 163,9473: 740,00/11,4634 = **64** | 64 vs 37 ✓ |
| BKNG | 0,70 | 207,03 → 191,5372 | 344,20/15,4928 = **22** | dolum 207,5539: 700,00/16,0167 = **43** | 43 vs 22 ✓ |
| AMGN | 0,84 | 407,73 → 389,4209 | 413,03/18,3091 = **22** | dolum 414,5927: 840,00/25,1718 = **33** | 33 vs 22 ✓ |

`derisk_mult(94457,91 ; 100000)`: dd = 5,54209% → `1 − (0,0554209−0,03)/(0,08−0,03)` = **0,4916**
(`DERISK_FLOOR_DD = 0.08`).

**KARŞI-OLGU (taban yerinde olsaydı):** ayna 51 / 76 / 45 / 45 gönderirdi. Yani ayna, dört
pozisyonda **hedeflenen riskin ~%49'unu** taşıdı; iç defter tam boyutu kaydetti. Kâğıt aynanın K/Z'si
bu yüzden kitaptan yapısal olarak ayrışacak.

### AMGN ayrı bir daldan geldi — ve aynı sayıyı BAŞKA bir kaynaktan aldı
AMGN 6 Ağustos 10:32:46'da `kaynak="pano"` ile gönderildi; o dal `eq_now` almaz, **nabızdan** okur.
`health.write_heartbeat` bir **BİNDİRME** yazıcısıdır (health.py:255-262: "mevcut nabız üzerine
BİNDİRİLİR"), yani verilmeyen alan eski değerini korur. Ölçüldü: **08-05 23:32:53Z nabzı — kitap
22:31:56'da iade edildikten bir saat SONRA — hâlâ `equity: 94457.91` diyordu** (yedek 08-05
`state/heartbeat.json`), ve `equity` alanı ancak bir sonraki tam döngüde (08-06 20:34) tazelendi
(canlı nabız bugün 99138,94 = 6 Ağustos turunun değeri).

> Yani **aynı yanlış sayı iki AYRI yoldan** boyutlandırmaya girdi: 5 Ağustos'ta kitaptan (loop
> dalı), 6 Ağustos'ta bayat nabızdan (pano dalı). `mirror_submit_armed`in docstring'i nabız dalını
> "yedek" diye anlatır; ölçüm onun **bağımsız bir bayatlık kanalı** olduğunu gösteriyor.

---

## 7. KÖK: 4 AĞUSTOS'TAKİ TERS ONARIM — VE NE ÖLÇÜLEMEDİ

**Zincir (hepsi ölçüldü):**
1. 08-01: `sermaye --uygula` tabanı taşıdı + beyanı yazdı.
2. 08-04 01:15:37: `_save_broker`'ın TAM-belge beyaz listesi beyanı sildi (bilinen 2026-08-04
   vakası, `research/olcumler/portfoy_sifirlama_2026-08-04/KOKNEDEN.md`). **Sayılar doğruydu**
   (100000/0,0), yalnız beyan gitti → `recompute`in üç kimliği KIRILDI (01:16:13 alarmları).
3. 08-04 07:54 ↔ 21:47: **kitap defterin eski tabanına geri çekildi** (cash 94457,91 /
   realized −5542,09). Bu, kimlikleri yeşile döndürmenin **YANLIŞ** yoludur ve
   `ops/sermaye_beyani_iade.py`'nin başlığı onu o sabah adıyla uyarmıştı: *"kitabı defterin eski
   tabanına geri çekmek … sayıları uzlaştırır ama OPERATÖRÜN KARARINI geri alır"*.
   Beyan silinmiş olduğu için bu hâl **üç kimliği de dürüstçe YEŞİL yaptı** (ofset 0 ⇒
   A ve B birbirini tutuyor) — yani onarım kendi izini de sildi.
4. 08-04 21:47:54: `_save_broker` bu tabanı diske çimentoladı; `peak_equity` 100000 kaldı
   (`max(100000, 94457.91)`), yani kitap **"yeni tepe + eski taban"** melez hâline oturdu — tam
   olarak %5,54 çekilme, tam olarak 0,4916 çarpan.
5. 08-05 22:10:01: ayna bu tabanla gönderdi. 22:31:56: iade koştu — **22 dakika geç**.
6. 08-06: iç motor doğru tabanla doldurdu → 4 × `MIRROR_DRIFT` (yalnız ADET; sebep adlandırılmadı).

**ÖLÇÜLEMEDİ — ve uydurulmuyor:** 3. adımdaki yazımı **kimin/hangi komutun** yaptığı.
Kanıtın yokluğu ölçüldü:
* `events.jsonl`de o pencerede kitap/sermayeyle ilgili **hiçbir olay yok** (1.236 satır tarandı;
  hepsi finviz/sprint/hermes gürültüsü).
* `entity_meta.rev` 4 Ağustos'ta yalnız **iki** kez ilerledi (3→4→5) ve ikisi de kanıtlı
  `_save_broker` yazımıdır (01:15:37 ve 21:47:54; `hotstate_write_disabled where=_save_broker`
  süreç başına bir kez basar). `store.write_json`/`update_json` **her** yazımda `_touch` ile rev'i
  artırır (storage.py:480) ve her yedekte `doc.updated_at` ile `entity_meta.updated_at` mikro-saniye
  farkla eşleşiyor. ⇒ **İçerik değişimi `store` kapısından GEÇMEDİ** (damgasız yazım: doğrudan SQL
  ya da elle kurulmuş bir belge yazımı).
* `"REDDEDİLDİ"` alarmı defterde **0** kez geçiyor → D2 ratchet devreye girmedi (zaten o gün
  `loop.py`'nin D1/D2 sürümü A1'de değildi: canlı `meridian/loop.py` mtime **2026-08-07 13:26**).

**Dışlanan adaylar (her biri ölçümle):**
| Aday | Neden dışlandı |
|---|---|
| `run.replay_seed` / `_reset_book_to` | `trades.jsonl` entity `rev=1, updated_at=2026-07-31`; `equity_curve.json` `rev=2, updated_at=2026-08-01T15:14:29` — re-seed ikisini de yeniden yazar. Ayrıca `_reset_book_to` `broker_rejected`ı `[]` yapar; 08-04 belgesinde 4 kayıt **duruyor**. |
| `ops/sermaye_beyani_iade.py` | BEYANLI tabana (100000/0,0) **ve** beyan kaydını yazar; 08-04 belgesinde ikisi de yok. (Bu betik 08-05 22:31:56 yazımıdır.) |
| `meridian.sermaye --uygula` (ikinci reset) | `grep -c paper_equity_reset` = **1** (yalnız 08-01). |
| `state/portfolio.json.migrated` geri kopyalanması | O dosyanın `peak_equity`si **102.520,45**; 08-04 belgesinde **100.000,0**. |
| dağıtım / restart / litestream | `dagit.sh` `state/`i dışlar; A1'de 08-04 01:16–21:47 arasında değişen dosyalar yalnız `uv.lock` + `storage.py` + 2 test + 2 doküman; litestream geri yükleme yalnız `-o` ile ayrı dosyaya (RUNBOOK §6). |
| `hermes._patch_pf`, `api` gönderim ucu, `loop._arm_yama` | üçü de `cash`/`realized_pnl`e dokunmaz. |

**Ayrıca ölçüldü (brief'teki bir gözlem düzeltilir):** `state/equity_curve.jsonl` yok — eğri
`state/meridian.db`'de `equity_curve` tablosunda **882 satır** olarak duruyor; `entity_meta` son
yazımı **2026-08-01T15:14:29** (yani eğri 1 Ağustos'tan beri hiç yazılmadı, "boş" değil DURGUN).
`state/portfolio.json` de dosya olarak yok — kitap DB'dedir.

---

## 8. BEKÇİ ÖNERİSİ (TASARIM — UYGULANMADI)

Bu sınıfın tanımı: **"iki bacak aynı kitabı farklı anlarda okuyor ve fark ADSIZ kalıyor."**
Bugün `broker_reconcile`ın `MIRROR_DRIFT`i yalnız ADET sapmasını görüyor (`local_qty`,
`alpaca_qty`) ve sebep sınıfını sormuyor; dördü de aynı cümleyi kurdu, üçü loop dalından biri pano
dalından gelmişti ve hiçbiri bunu söylemedi.

### B1 — BOYUT KARARININ MAKBUZU (yeni alan, yeni defter değil)
`alpaca.submit_plan` çağrısının yanına, `entry_law` yan tablosunun **aynı deseniyle**, plan başına
bir **boyut makbuzu** yazılsın (`meta["size_law"][plan_id]`, `_save_broker`ın 13 anahtarına 14.
olarak eklenir — restart'ı atlatmalı, `entry_law` ile aynı gerekçe):

```
{"ts", "kaynak": "loop|pano",
 "eq_kaynak": "eq_now|nabiz",           # HANGİ DAL koştu — bugün hiçbir yerde yazılı değil
 "eq_now", "peak_equity", "size_mult",  # çarpanın üç girdisi
 "kitap_rev", "kitap_updated_at",       # storage.entity_stamp("portfolio.json") — kitabın KİMLİĞİ
 "beyan_n", "beyan_ofset",              # sermaye.beyan_olcusu — taban beyanı o an neydi
 "eq_broker"}                           # Alpaca hesabı (bugün olaydaki `equity`)
```
Maliyet: plan başına ~10 alan, turda ≤6 plan. Yeni dosya yok, yeni gerçek kaynağı yok.

### B2 — `MIRROR_DRIFT`E SEBEP SINIFI ALANI (`drift_sinifi`)
`loop.reconcile_broker_state` adet sapmasını görünce B1 makbuzunu iç motorun dolum girdileriyle
kıyaslasın ve sapmayı **adlandırsın** (alarmın kendisi kalır, yalnız alan eklenir):

| `drift_sinifi` | Ayırt eden ölçüm |
|---|---|
| `boyutlama_tabani` | makbuz `eq_now` ≠ dolum anındaki `eq_now` (bu vaka: 94457,91 vs 100000) |
| `derisk_carpani` | `size_mult` iki bacakta farklı ama `eq_now` aynı (kart/eşik değişimi) |
| `sermaye_kaynagi` | makbuz `eq_kaynak="nabiz"` ve nabız yaşı > 1 seans (AMGN bacağı) |
| `kitap_kaydi` | makbuz `kitap_rev` ≠ dolum anındaki rev → kitap arada DEĞİŞTİ |
| `beyan_kaydi` | makbuz `beyan_n/ofset` ≠ dolum anındaki → taban beyanı arada kıpırdadı |
| `icra` | girdilerin hepsi aynı; fark limit/slipaj/kısmi dolumdan (bugünkü tek meşru sınıf) |
| `olculemedi` | makbuz yok (restart öncesi plan) — **0 değil, ADI OLAN üçüncü hâl** |

Mesaj şekli korunur; alarmın sonuna tek cümle eklenir: *"sapma sınıfı: boyutlama_tabani — gönderim
anında kitap 94.457,91$, dolum anında 100.000,0$ (kitap rev 5 → 7)"*.

### B3 — TABAN SIÇRAMASI DEDEKTÖRÜ (asıl erken uyarı; `MIRROR_DRIFT`ten bağımsız)
Yukarıdakiler sapmayı **sonradan** açıklar. Sapmayı **doğmadan** yakalayacak olan tek ölçü şudur:
`recompute`in üç kimliği kitabın İÇ TUTARLILIĞINI ölçer, **TABANINI ölçmez** — ve bu vakanın
sessizliği tam olarak oradan geldi. Eklenmesi gereken dördüncü satır:

```
taban_kaymasi:  A = portfolio.realized_pnl − (Σ trades.pnl_dollars + sermaye.ofset())
                B = 0
```
Beyan yerindeyken bu zaten `realized_pnl` kimliğine eşittir; **beyan YOKKEN de anlamlıdır** çünkü
`Σ trades` ile kitabın tabanı arasındaki farkı bir BEYAN olmadan açıklamak mümkün değildir. Ek
olarak `watchdog.monotonicity_report` tabanına — D4'ün zaten önerdiği gibi — `len(sermaye_resetleri)`
ve `Σ|ofset|` alınırsa, beyanın 1→0 düşüşü **aynı döngüde** görülür (bu vakada üç gün ve dört alarm
sonra görüldü).

### B4 — DAMGASIZ YAZIM KAPISI (bu turun asıl açığı)
§7'nin ölçtüğü şey ayrıca şudur: **canlı kitaba `store` kapısından geçmeden yazan bir yol var** ve
o yol ne kilit alıyor, ne rev artırıyor, ne olay bırakıyor. D2 ratchet yalnız `_save_broker`ın
içindedir, yani onu görmüyor. Öneri: `entity_stamp` (rev + updated_at) döngü başında okunup tur
sonunda yeniden okunsun; ikisi arasındaki fark döngünün KENDİ yazım sayısıyla uyuşmuyorsa
`DATA_QUALITY` alarmı — *"kitap bu tur dışarıdan değişti"*. Bu, dış yazımı yasaklamaz (operatör
onarımı meşrudur) ama **sessiz kalmasını** engeller.

**Sıra önerisi:** B3 (en ucuz, en erken) → B1 → B2 → B4.

---

## 9. BU TURDA YAZILAN TESTLER

`tests/test_bayat_sermaye_koku_v213.py` — 7 test, hepsi `sandbox_state`te, **davranış
değiştirilmedi**:

* `test_equity_nakdi_okumaz_boyut_tabani_realized_pnl_dir` — `cash` kozmetik, `realized_pnl`
  davranışsal (K1).
* `test_kitap_beyanli_tabanda_iken_carpan_1_0` — kontrol grubu.
* `test_derisk_carpani_canli_vakanin_sayisini_verir` — 0,4916 ve rampanın içinde olduğu.
* `test_nue_iki_bacagin_adedi_birebir_yeniden_uretilir` — 25 (ayna) ve 54 (iç motor).
* `test_ayna_bacagi_kitap_tabani_yerindeyken_sapmazdi` — karşı-olgu: 51, sapma 3'e inerdi.
* `test_ters_onarilmis_kitap_uc_kimligi_de_YESIL_birakir` — **dedektör boşluğu**: üç kimlik yeşil,
  taban 5.542,09$ aşağıda. (Bir dedektörün YOKLUĞUNU iddia etmez; kimliklerin NE ölçtüğünü çiviler.)
* `test_beyan_yerindeyken_ayni_kitap_kimligi_KIRAR` — beyanın tek dedektör kolu olduğu; ayrışma
  büyüklüğü canlı alarmın sayısıyla aynı (5.542,09$).

Kapsam koşumu (yerel, `./.venv/bin/python -m pytest`): `test_bayat_sermaye_koku_v213` +
`test_sermaye_beyani_v187` + `test_sermaye_ayristirma_v150` + `test_risk` + `test_broker_audit_v24`
+ `test_mutborc_broker_derisk_mult_v148` → **94 geçti, 0 FAILED/ERROR**.

---

## 10. OPERATÖRE AÇIK KALEMLER

1. **Bugün risk var mı?** Hayır — üç sermaye kaynağı da çarpanı 1,0 veriyor (kitap 100000/0,0 ·
   nabız 99138,94 · day_start 99975,97; tepe 100000). Arıza **tekrarlamıyor**.
2. **Ama açık pozisyonlar melez.** İç defter 54/64/43/33, Alpaca 25/37/22/22 — dört pozisyon
   yaklaşık yarım aynada. Bu sapmayı kapatmak (aynayı büyütmek / kitabı küçültmek / olduğu gibi
   bırakıp beyan etmek) bir **operatör kararıdır**; bu tur emir göndermedi/iptal etmedi.
3. **Damgasız yazım yolu (B4)** açık kalemdir: kitabın `store` dışından değişebildiği ölçüldü.
