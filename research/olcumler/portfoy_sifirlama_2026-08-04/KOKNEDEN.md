# KÖK NEDEN — "portföy sıfırlaması" 2026-08-04 (KOD İNCELEMESİ + YEDEK ADLİYESİ)

**Yöntem:** salt-okuma. Canlıya ssh YOK, git komutu YOK, üretim dosyası değişikliği YOK.
Kanıtın tamamı (a) depodaki kod ve (b) Mac'teki A1 yedeklerinden (`backups/a1/*.tar.gz`,
`ops/pull-a1-backups.sh` ile çekilen) çıkarılan **canlı `state/meridian.db` kopyası**ndan geldi.
Yedek kopyası scratchpad'e açıldı; depo ve canlı state'e hiçbir bayt yazılmadı.

---

## 0. HÜKÜM (tek cümle)

**Sayıları sıfırlayan şey bir arıza DEĞİL, operatörün 2026-08-01T15:14:29Z'de koştuğu
`meridian.sermaye --uygula`dır ve o yazım TAM BEYANLIYDI.** Olay, o beyanın **sonradan
silinmesidir**: `loop._save_broker` kitabı **SABİT 13 ANAHTARLIK BİR BEYAZ LİSTEYLE** yeniden
serileştirir, yani listede olmayan her anahtarı — bu vakada beyanın kendisi olan
`sermaye_resetleri`ni — ilk noop-olmayan döngüde **sessizce yok eder**. Beyan gidince
`recompute._sermaye_ofseti` 0.0'a düşer ve üç kimlik (`realized_pnl`, `cash_identity`,
`equity_curve_tail`) birden kırılır → 2026-08-04T01:16 MAKULLÜK alarmları.

Yani: **beyanlı bir reset, onu taşıyan defterin yazarı tarafından beyansız hâle getirildi.**
Sınıf: *"defterin sahibi olmayan alanları, sahibiymiş gibi yeniden yazan tam-belge yazarı"*
(aynı aile: `health.py:239` çok-yazarlı nabız alanlarının birbirini silmesi).

---

## 1. ZAMAN ÇİZELGESİ (ölçülmüş damgalar; hiçbiri türetilmedi)

| UTC | Olay | Kanıt |
|---|---|---|
| 2026-07-31 10:56:02 | `dbmigrate --uygula` — altı defter SQLite'a; portfolio **rev=1** | `entity_meta` (yedek DB) |
| 2026-07-31 21:57:29 | Son noop-olmayan Cuma döngüsü; `_save_broker` → portfolio **rev=2**; kitap DOĞRU (94.457,91 / −5.542,09) | `entity_meta.trade_plans rev=2 @21:57:29`, operatör raporu |
| **2026-08-01 15:14:29** | **`meridian.sermaye --uygula`** — dört alan taşındı + BEYAN yazıldı; portfolio **rev=3**, equity_curve **rev=2** | yedek DB `portfolio.doc_json.sermaye_resetleri`, `entity_meta.env_json.reset_isaretleri`, `monotonic_amnesty.json`, `events.jsonl` |
| 2026-08-02 19:53 (pull) | Mac yedeği çekildi — **DB'nin son yazımı hâlâ 2026-08-01 15:14:29**; kitap zeroed **AMA BEYANLI** | `backups/a1/state-2026-08-02.tar.gz` |
| 2026-08-03 10:03 / 13:04 / 16:27 | 3 dagit dağıtımı (store.py Kademe-B dâhil) — **state'e dokunmaz** (`RSYNC_EXC` `--exclude state`) | `dagit.sh:19` |
| 2026-08-03 20:52 / 21:52 / 22:38 / 23:23 | tick-watchdog zorla restartları | `tick_watchdog.sh:131` (`systemctl restart`, state yazımı YOK) |
| 2026-08-03 23:35 | operatör restartı | operatör raporu |
| **(Pazartesi 2026-08-03 seansı işlendiğinde)** | İlk **noop-olmayan** `daily_cycle` → `_save_broker` → **beyan silindi** | loop.py:1358 + loop.py:475-496 (aşağıda) |
| 2026-08-04 01:16 | MAKULLÜK alarmları (üç kimlik birden) | operatör raporu + `watchdog.py:1397` |

Kitap `last_date`i yedekte **2026-07-31**'dir: 08-01 (Cmt) ve 08-02 (Paz) döngüleri seans
olmadığı için `noop` dalında (loop.py:761-773) dönmüş, `_save_broker`a HİÇ ulaşmamıştır — bu
yüzden beyan iki gün hayatta kaldı. Beyanı öldüren, hafta sonundan sonraki **ilk gerçek seans**tır.

---

## 2. YAZAR ENVANTERİ — `portfolio.json` (kanonik ad; H9'dan beri SQLite `portfolio.doc_json`)

| # | Yazar | Yol | Semantik | Yabancı anahtarı korur mu? |
|---|---|---|---|---|
| W1 | `loop._save_broker` | loop.py:475-500 (tek çağrı: loop.py:1358) | **TAM BELGE, SABİT 13 ANAHTAR** | **HAYIR — SİLER** |
| W2 | `run._reset_book_to` (re-seed) | run.py:90-112 | TAM BELGE (10 anahtar) | HAYIR (ama `broker_rejected: []` yazar — bu vakada ELENDİ) |
| W3 | `sermaye.uygula` | sermaye.py:387-393 | **KİLİTLİ OKU-DEĞİŞTİR-YAZ** (`pf.update(...)`) | EVET |
| W4 | `api.api_alpaca_submit_armed._yama` | api.py:2681-2689 | `update_json` yaması (3 alan) | EVET |
| W5 | `hermes._stamp_llm_opinions._patch_pf` | hermes.py:2489-2499 | `update_json` yaması (`armed` içi) | EVET |
| W6 | `sprint._reset_sandbox_state` | sprint.py:171-173 | HAM DOSYA — **yalnız kum havuzu** (`MERIDIAN_ROOT=sbroot`) | n/a |
| W7 | `sprint_run` / `mutation` | sprint_run.py:114, mutation.py:272 | kum havuzu / mutasyon fikstürü | n/a |

Okuyucular (karar veren): `loop._load_broker` (449), `intraday_shadow._copy_broker` (78-86,
**salt-okuma**), `recompute.report` (154), `sermaye.koken` (164), `analytics`, `api`, `watchdog`,
`marketstream`, `scheduler`. Depolama katmanı: `store.read_json/write_json` →
`storage.read_doc/do_write_doc` — **`do_write_doc` doc_json'u BÜTÜN OLARAK EZER**
(storage.py:542-545 `ON CONFLICT(id) DO UPDATE SET doc_json=excluded.doc_json`), yani DB
katmanında hiçbir birleştirme yoktur; "korunmuş alan" ne varsa YAZARIN elinden gelmiştir.

### W1'in tam anahtar listesi (loop.py:477-496)
`cash · realized_pnl · last_id · positions · armed · pending_exits · last_date ·
day_start_equity · alpaca_submitted · broker_rejected · entry_law · peak_equity ·
mirror_exit_pending`

Bu listede **`sermaye_resetleri` YOKTUR**. `last_id` ve `broker_rejected` listede OLDUĞU için
korunmuş; beyan listede OLMADIĞI için gitmiştir. Operatörün gördüğü "seçici sıfırlama" görüntüsü
tam olarak budur: seçicilik sıfırlamada değil, **serileştirmenin beyaz listesindedir**.

---

## 3. KANIT SATIRLARI (yedek DB'den; 2026-08-02 tarball'ı, DB son yazımı 2026-08-01T15:14:29Z)

```
portfolio.doc_json:
  cash=100000.0  realized_pnl=0.0  day_start_equity=100000.0  peak_equity=100000.0
  last_id=95     positions={}      broker_rejected=[4 kayıt]  last_date=2026-07-31
  sermaye_resetleri=[1 kayıt]      ← BEYAN O GÜN YERİNDEYDİ
entity_meta: portfolio.json rev=3 @2026-08-01T15:14:29.288204Z
             equity_curve.json rev=2 @2026-08-01T15:14:29.284918Z   (sermaye'nin (1)→(2) sırası)
```

`sermaye_resetleri[0]`:
```json
{"id":"SR-20260801T151429+0000","tarih":"2026-08-01T15:14:29+00:00",
 "onceki_cash":94457.91,"yeni_cash":100000.0,"ofset":5542.09,
 "onceki_realized_pnl":-5542.09,"yeni_realized_pnl":0.0,
 "onceki_peak_equity":102520.45,"yeni_peak_equity":100000.0,
 "tohum_etkisi_usd":-5542.09,"tohum_islem_n":95,"canli_islem_n":0,
 "gerekce":"operatör talimatı 2026-08-01: tohum-PnL gerçek-canlı sermayeden ayrıştırıldı",
 "arac":"meridian.sermaye"}
```

Aynı işlemin diğer üç ayağı da **hâlâ diskte** (üçü de `_save_broker`ın dokunmadığı defterlerde):
- `equity_curve` zarfı → `entity_meta.env_json.reset_isaretleri` = aynı `SR-...` işareti,
  `egri_son_nokta:["2026-07-20", 94457.91]`.
- `state/monotonic_amnesty.json` → `{"field":"peak_equity","was":102520.45,"now":100000.0,
  "by":"meridian.sermaye","ts":"2026-08-01T15:14:29+00:00"}` (bu yüzden monotonluk bekçisi
  haklı olarak SUSTU — af yazılıydı).
- `state/events.jsonl` → `{"ts":"2026-08-01T15:14:29+00:00","level":"warn",
  "event":"paper_equity_reset", ...}` (append-only defter; A1'de HÂLÂ DURUYOR).

**Yani olayın "kayıp" sanılan bütün izleri aslında yerinde; kaybolan TEK şey kitabın içindeki
beyandır — ve onu `_save_broker` silmiştir.**

---

## 4. ADAY ELEME

### (a) Kısmi okuma → `dict.get(k, default)` ile varsayılana birleşme — **ÇÜRÜTÜLDÜ**
`loop._load_broker` **varsayılan kullanmaz**: `b.cash = st["cash"]; b.realized_pnl =
st["realized_pnl"]` (loop.py:449) — anahtar eksikse `KeyError` ile döngü DÜŞER, sessizce 100.000'e
düşmez. `.get(k, default)` deseni yalnız `intraday_shadow._copy_broker`dadır (81-83) ve o modülün
**hiçbir yazım yolu yoktur** (test_intraday_shadow_v105.py:276 `store.write_json(` /
`_save_broker(` token'larını yasaklıyor). Ayrıca gözlenen değerlerin kaynağı ölçüldü: beyanlı
reset kaydı. Bu dal gereksiz.

### (b) H9-B store.py (flock write_json'ın İÇİNE indi) yan etkisi — **ÇÜRÜTÜLDÜ**
İki bağımsız nedenle: (1) **Zaman**: reset yazımı 2026-08-01 15:14, Kademe-B canlıya
2026-08-03 10:03'te indi — kusur değişiklikten **iki gün önce** vardı. (2) **Mekanizma**: silme
kilit/atomiklik değil **serileştirme kapsamı** kusurudur; `db_backed` dalında flock zaten
alınmaz (store.py:283-287) ve `do_write_doc` tek `BEGIN IMMEDIATE…COMMIT` içindedir. Kilit
sırası bu vakada hiçbir rol oynamaz.

### (c) Gün-başı/rollover dalı `cash`i resetliyor — **ÇÜRÜTÜLDÜ**
`day_start_equity`in 100.000 olması bağımsız bir sıfırlama değil, **türev**dir:
loop.py:892 `meta["day_start_equity"] = b.equity({...})` ve `broker.equity()` =
`start_equity + realized_pnl` (broker.py:263) → pozisyon yokken ve `realized_pnl=0` iken sonuç
zorunlu olarak 100.000'dir. Ayrıca `sermaye._yeni_kitap` (sermaye.py:299-300) o alanı zaten
BİLEREK yazar. Rollover'da `cash`e dokunan hiçbir dal yok (`b.cash` yalnız
`broker.py:474/500`'de, yani **kapanışta** değişir — ve `trades` tablosu bozulmadı).

### (d) "Varsayılan doküman + mevcut alanları taşı" birleşmesi — **ÇÜRÜTÜLDÜ**
Böyle bir birleştirici yok. DB katmanı belgeyi **bütün olarak ezer** (storage.py:542-545);
`last_id`/`broker_rejected`ın korunması bir birleştirmenin değil, W1'in beyaz listesinin sonucudur.

### (e) SIGKILL anı — yarım yazım / okuma hatası → init-fallback zinciri — **ÇÜRÜTÜLDÜ**
SQLite yazımı `BEGIN IMMEDIATE` + tek `COMMIT`tir (storage.py:551-558): yarım belge YOKTUR.
Okuma hatası dalı da bu vakayı üretemez: `read_doc` bozuk JSON'da `None` döner →
`store.read_json(PORTFOLIO, None)` → `st` falsy → **TAZE broker** → `_save_broker`
`last_id=0`, `broker_rejected=[]`, `last_date=None` yazardı. Gözlenen belge `last_id=95` ve 4
kayıtlı `broker_rejected` taşıyor → **taze-init zinciri kesin olarak elendi.** (YASA-4 açısından:
o dalın kendi işareti var — `store.py:354-359` `state_file_unreadable` uyarısı dosya başına bir
kez basılır; yani sessiz değildi, ama zaten olmadı.)

### (f) Dağıtım/restart/litestream — **ÇÜRÜTÜLDÜ**
`dagit.sh` state'i dışlar (satır 19); tick-watchdog yalnız `systemctl restart` eder
(tick_watchdog.sh:131); litestream **okur/çoğaltır**, geri yükleme yalnız `-o` ile AYRI dosyaya
yapılır (RUNBOOK §6). Hiçbiri `portfolio.doc_json` yazamaz.

### (g) **HÜKÜMLÜ: `loop._save_broker` beyaz-liste serileştirmesi**
Tek tutarlı yazar. Gözlenen belgenin HER alanını açıklar (sıfırlar korunur çünkü diskten gelirler;
`last_id`/`broker_rejected` korunur çünkü listede; beyan gider çünkü listede değil) ve alarm
zamanlamasını açıklar (ilk noop-olmayan seans). Rakip aday YOK.

---

## 5. KALAN BELİRSİZLİK (dürüst kayıt) + tek komutluk teyit

Yedek 2026-08-02'de bitiyor; **silme anını doğrudan gören bir anlık görüntü elimde yok.** Silmenin
gerçekleştiği, alarmların ateşlemesinden **çıkarım**la sabittir: beyan yerinde olsaydı ofset
+5.542,09 olurdu ve üç kimlik de YEŞİL kalırdı (recompute.py:222/233/245 — ofset geçmişten türeyen
tarafa eklenir). Kimlikler kırıldıysa `sermaye.ofset()` 0'dır, yani kayıt yoktur.

Doğrudan teyit için A1'de **tek salt-okuma sorgusu** yeter:

```bash
sqlite3 /opt/meridian/state/meridian.db \
 "SELECT json_extract(doc_json,'\$.last_date'),
         json_extract(doc_json,'\$.sermaye_resetleri'),
         (SELECT rev FROM entity_meta WHERE entity='portfolio.json') FROM portfolio;"
```
Beklenen (hüküm doğruysa): `last_date` **> 2026-07-31**, `sermaye_resetleri` **NULL**, `rev ≥ 4`.
- `last_date` ilerlemiş + kayıt NULL → **W1 silmesi kanıtlanır** (bu turun hükmü).
- `last_date` hâlâ 2026-07-31 + kayıt NULL → hüküm değişir; o zaman ikinci bir yazar aranır
  (o hâlde `entity_meta.rev` ve `updated_at` hangi anı gösteriyor, ona bakılır).

İkinci (ücretsiz) teyit: `grep -c paper_equity_reset /opt/meridian/state/events.jsonl` → **1**
olmalı. Yedekte 1'dir; artmışsa ikinci bir reset koşulmuş demektir.

---

## 6. ÖNERİLEN KALICI DÜZELTME (UYGULANMADI — Rol-1'in hükmüne)

### D1 (kök) — `_save_broker` yabancı anahtarı SİLEMEZ: tam-belge yazımı → sahiplenilmiş-alan yaması
`loop._save_broker` bugün `store.write_json(PORTFOLIO, st)` ile **belgeyi ezer**. Doğrusu, kilidi
zaten alan `store.update_json` ile **diskteki belgeyi okuyup üstüne yalnız SAHİP OLDUĞU 13 alanı
yazmak**tır:

```python
def _save_broker(b, meta):
    st = {...}                                    # bugünkü 13 alan, aynen
    def _yama(doc):
        if not isinstance(doc, dict):
            return False
        doc.update(st)                            # sahiplenilen alanlar; yabancılar YERİNDE kalır
        return True
    store.update_json(PORTFOLIO, _yama, {})       # kilit + oku-değiştir-yaz (aynı file_lock)
```
Neden dar bir yama (`st["sermaye_resetleri"] = meta.get(...)`) DEĞİL: o, bu sınıfı bir kez daha
elle kapatmak olurdu — **bir sonraki beyan anahtarını yazan kişi aynı tuzağa düşer.** Bu deponun
kendi diliyle: kusur "aynı yasanın iki uygulaması" değil, "yasanın sahibi olmadığı alanı ezmesi".
Yapısal kapı, sahipliği yazarın kendi listesiyle sınırlamaktır.

### D2 (koruma) — BEYAN GERİLEMESİ YASAK (kimlik-denklemi ön-koşulu)
Yazımdan ÖNCE, kilit altında, diskteki belgenin beyanı ile yazılacak belgenin beyanı kıyaslanır:

```python
eski = sermaye.ofset(doc_on_disk); yeni = sermaye.ofset(yeni_doc)
if abs(yeni) < abs(eski) or len(sermaye.resetler(yeni_doc)) < len(sermaye.resetler(doc_on_disk)):
    → YAZIM REDDEDİLİR + obs.alarm("sermaye_beyani_silinecekti", eski=…, yeni=…, yazar=…)
```
Ve/veya kimliğin kendisi ön-koşul yapılır (pozisyon yokken):
`cash == START_EQUITY + realized_pnl + ofset(doc)` — tutmayan yazım reddedilir/alarm üretir.
Bu, `watchdog.grant_amnesty` + `monotonicity_report` ailesinin aynısıdır: **beyan yalnız
EKLENEBİLİR, sessizce düşemez.** Bugün bu ratchet YOK; kayıp 3 gün sonra üç kırık kimlik olarak
görünüyor, ki teşhis maliyeti bu dosyadır.

### D3 (aynı sınıfın ikinci örneği — LATENT, henüz patlamadı) — eğri zarfı da eziliyor
`storage._touch(..., env=env)` `env_json=COALESCE(?, env_json)` yazar (storage.py:456-459) ve
`do_write_series` `env`i **her zaman bir dict olarak** verir (593-596) — yani `{}` bile `'{}'`
yazılır, COALESCE hiçbir zaman eski zarfı korumaz. Tek eğri yazarı `run.py:200`
(`{"version": …, "points": …}`) olduğu için **bir sonraki re-seed `reset_isaretleri` işaretini de
silecektir.** Öneri: ya `do_write_series` zarfı MEVCUT zarfın üstüne birleştirsin, ya `run.py`
yazımdan önce zarfı okuyup taşısın. (Aynı yasa, ikinci defter.)

### D4 (dedektör boşluğu) — beyan defteri monotonluk tabanına alınsın
`watchdog.monotonicity_report` bugün `peak_equity`/sayaçları izliyor (watchdog.py:1536-1573).
`len(portfolio.sermaye_resetleri)` (ve/veya `ofset`) tam olarak monoton-artan bir büyüklüktür;
tabana eklenirse bu olay **bir döngü içinde** "beyan kaydı 1→0" alarmıyla yakalanırdı — üç gün
sonra üç kırık kimlik yerine.

### D5 (belge) — `sermaye.py`'nin kendi tehlike notu EKSİK
`sermaye.main` (545-551) canlı worker'a karşı **ters** tehlikeyi uyarıyor: "reset bir sonraki
tikte sessizce geri alınır". Gerçekte olan bu DEĞİL: sayılar kaldı, **beyan gitti** — yani
görünürde sorunsuz, teşhisi çok daha zor bir hâl. Not düzeltilmeli (D1 uygulanınca ikisi de
kapanır).

### R1 (operasyonel onarım — koddan bağımsız, para KIMILDAMAZ)
Kitaptaki sayılar zaten DOĞRU ve beyan `events.jsonl` + `monotonic_amnesty.json` + yedek DB'de
tam metniyle duruyor. Worker DURMUŞKEN, `sermaye_resetleri` kaydı kitaba **geri yazılırsa** üç
MAKULLÜK satırı dürüstçe yeşile döner (susturma değil: ofset gerçekten beyanlıdır). D1 yapılmadan
geri yazılırsa **bir sonraki seansta yine silinir** — sıra: önce D1, sonra R1.

---

## 7. TEST TASLAĞI (yazılmadı; hükmü Rol-1 verir)

```python
# tests/test_kitap_beyan_kalicilik_vXXX.py

def test_save_broker_yabanci_anahtari_SILMEZ(seeded_sandbox):
    """BUGÜN KIRMIZI — regresyonun kanıtı. Kitapta loop'un sahibi OLMADIĞI iki anahtar var:
    biri gerçek (sermaye beyanı), biri sentetik (gelecekteki her beyan için vekil)."""
    pf = store.read_json("portfolio.json", {})
    pf["sermaye_resetleri"] = [{"id": "SR-TEST", "ofset": 5542.09}]
    pf["gelecekteki_beyan"] = {"x": 1}
    store.write_json("portfolio.json", pf)
    b, meta = loop._load_broker()
    loop._save_broker(b, meta)
    yeni = store.read_json("portfolio.json", {})
    assert yeni.get("sermaye_resetleri"), "beyan silindi — 2026-08-04 vakası"
    assert yeni.get("gelecekteki_beyan"), "sahiplenilmemiş alan silindi (sınıf testi)"

def test_sermaye_beyani_bir_dongu_sonrasi_kimligi_YESIL_tutar(seeded_sandbox):
    """UÇTAN UCA: reset → bir kaydetme turu → recompute'un üç kimliği hâlâ tutmalı."""
    sermaye.uygula("uçtan uca kalıcılık sınaması — beyan döngüyü atlatmalı")
    loop._save_broker(*loop._load_broker())
    rows = {r["check"]: r["ok"] for r in recompute.report()["rows"]}
    for k in ("realized_pnl", "cash_identity", "equity_curve_tail"):
        assert rows.get(k) is not False, f"{k} reset SONRASI kırıldı — ofset beyanı kayboldu"

def test_egri_zarfi_yeniden_yazimda_KORUNUR(seeded_sandbox_db):   # D3, DB arka ucu
    store.write_json("equity_curve.json", {"version": 4, "points": [["2026-07-20", 94457.91]],
                                           "reset_isaretleri": [{"id": "SR-TEST"}]})
    store.write_json("equity_curve.json", {"version": 4, "points": [["2026-07-20", 94457.91]]})
    assert store.read_json("equity_curve.json", {}).get("reset_isaretleri")

def test_beyan_gerilemesi_REDDEDILIR(seeded_sandbox):             # D2 yazıldıktan SONRA yeşile döner
    ...  # ofset taşıyan bir kitabın üstüne ofsetsiz tam-belge yazımı → alarm + red
```

---

## 8. SINIF AVI (bu vakanın ailesi — ayrı tur adayı)

Aynı desen: **"tek yazar, tam-belge, sabit alan listesi"** — listede olmayan her alan sessizce
ölür. Depoda aynı şekle sahip yazarlar taranmalı:
`health.write_heartbeat` (belgeli vaka: health.py:239), `versioning._patch` (scoreboard),
`watchdog` MONOTONIC/OWNERSHIP dosyaları, `storage._touch(env=…)` (D3).
Ölçüt basit ve makineye verilebilir: *bir belgeye TAM yazan her yol, o belgenin bütün
anahtarlarının sahibi mi?* Değilse ya yamaya (`update_json`) dönmeli, ya sahipliği beyan etmeli.
