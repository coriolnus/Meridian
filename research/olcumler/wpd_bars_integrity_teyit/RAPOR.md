# WP-D KALEM 2 — bars_integrity güvensiz-dönem dışlaması: DURUM TESPİTİ + BAĞIMSIZ TEYİT

**Tarih:** 2026-08-03 · **Rol:** ölçüm ajanı (WP-D turu) · **Hüküm sahibi:** Rol-1
**Cevaplanan ROADMAP satırı:** §WP-D "bars_integrity defteri (97 kalıcı dikiş/kimlik kırılması —
silme değil güvensiz-dönem dışlama, tüketici kablolu)".

## HÜKÜM: KALEM ZATEN UYGULANMIŞ VE ÇALIŞIYOR — yeni modül YAZILMADI, kapanış öneriliyor

Brief "YENİ `meridian/bars_integrity.py`" öngörüyordu. **Yazılmadı, bilerek:** mekanizmanın
tamamı 2026-07-31'de `meridian/adapters/data.py` içinde sevk edilmiş, üç gerçek tüketiciye
kablolanmış ve 26 testle kilitlenmiş durumda. Yeni bir modül **aynı yasanın ikinci kopyası**
olurdu — bu deponun tekrar eden hata sınıfı (guard'ın iki-yüzey kusuru, hermes_runtime ufuk
kopyası). Yapılan iş: iddianın **bağımsız teyidi**.

### Salt-okunurluk beyanı
`MERIDIAN_ROOT` kum havuzuna alındı, defter oraya kopyalandı; bar arşivi salt-okundu. Üretim
`state/` dosyaları değişmedi. Canlıya (A1) dokunulmadı.

---

## 1. MEKANİZMA NEREDE (keşif sonucu)

| parça | yer | ne yapar |
|---|---|---|
| defter | `state/bars_integrity.json` | rev 1, üretildi 2026-07-31T00:01:10, **61 sembol / 98 kırılma / 48.735 satır** |
| üretici | `meridian/barrepair.py` → `integrity_apply()` | `store.write_json` ile SANCTIONED yazım + `_bump_wf_rev()` (önbelleklenmiş walk-forward'lar başka bar kümesine ait olduğu için) |
| sınıflandırıcı (SAF) | `meridian/adapters/data.py:422 integrity_breaks()` | K1 ölçek dikişi · K2 bozuk kesit · K3 hayalet geçmiş |
| güvenli başlangıç (SAF) | `data.py:498 integrity_safe_start()` | SON kırılmadan sonraki ilk bar |
| defter okuyucu | `data.py:517 bars_integrity()` | YALNIZ `store.read_json` üzerinden, **FAIL-OPEN**, önbelleksiz |
| tek-sembol sorgu | `data.py:544 safe_start(ticker)` | defterde yoksa `None` = kısıt yok |
| **DIŞLAMA KAPISI** | `data.py:550 measurement_bars(df, ticker)` | güvensiz dönemi düşürür, sayar, sembol başına bir kez olay yazar |
| sayaç/beyan | `data.py:596 integrity_report()` | `{ledger_symbols, ledger_rev, generated_at, applied{}, rows_excluded}` |

Brief'in istediği API'nin karşılığı birebir mevcut: `is_guvenli(sembol, tarih)` yerine
`safe_start(sembol)` + `measurement_bars(df, sembol)` (çerçeve düzeyinde uygulanır, satır
düzeyinde değil — 250 sembollük turda satır-başına sorgu maliyetinden kaçınmak için).

## 2. TÜKETİCİ KABLOLAMASI (YASA 6) — üç gerçek okuyucu

| tüketici | çağrı yeri | ne için |
|---|---|---|
| `component_ic` | `component_ic.py:346` (`_load_universe`) ve `:371` (`_load_index_close`) | evren + SPY endeksi AYNI kapıdan |
| `cf_backfill` | `cf_backfill.py:152` (evren) ve `:165` (SPY) | karşı-olgu defteri |
| `trend_shadow` | `trend_shadow.py:205` (`_uygunluk`) → `_uygun()` | defteri doğrudan okur, rebalance tarihinde uygunluk kapısı |
| **sayaç okuyucuları** | `cf_backfill.py:196` (rapora `bars_integrity` alanı), `component_ic.py:312` (`_bars_taban`) | üretilen kanıt TÜKETİLİYOR |

Ölçüm sandbox'ları da **kanonik yolu** kullanıyor, kendi kuralını yeniden yazmıyor:
`research/olcumler/wp2_olcum/ortak.py:92`, `wp1_rvol_form/ortak017.py:106`,
`inplay_postevent/ortak020.py:248` — hepsi `dat.measurement_bars` çağırıyor ve ikinci bir
doğrulama olarak `dat.integrity_safe_start`i yan yana koşturup ayrışmayı raporluyor.

**BİLEREK BAĞLANMAYAN yol:** `dataset.load()` / `dataset.load_cached()` — yani walk-forward,
prescreen, reflect ve CANLI tarama. Gerekçe `measurement_bars` docstring'inde ölçülmüş: HON'un
kırılması 22 seans önce; canlı yolda uygulanırsa HON göstergeleri ısınma barı bulamaz ve sembol
tarama evreninden SESSİZCE düşer. "Geçmişi ölçen için doğru olan, bugünü tarayan için yıkıcıdır."
Bu beyan `barrepair.integrity_apply` olayında da yazılı (2026-08-02'de kodla eşitlendi: olay
eskiden `dataset.load_cached`i de dışlayanlar arasında sayıyordu — düzeltilmiş).

## 3. BAĞIMSIZ TEYİT — kanonik tüketici yolu tüm evrende koşturuldu

**Komut**
```
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python kalem2.py
```
(betik: `kalem2.py`, ham çıktı: `sonuc.json`. `sanitize_bars` → `measurement_bars` sırası
`component_ic._load_universe` ile BİREBİR aynı.)

| ölçüm | değer |
|---|---|
| evren | 251 sembol (1 defter dosyası yok → 250 yüklendi) |
| takvim kapısının düşürdüğü hayalet-seans satırı | **428** |
| karantinanın düşürdüğü satır | **13** (KALEM 1'in 13'üyle birebir aynı — çapraz doğrulama) |
| **defterin ÖLÇÜMDEN dışladığı satır** | **46.256** |
| dışlamadan etkilenen sembol | **57** |
| `integrity_report().rows_excluded` | **46.256** (sayaç ile ölçüm aynı) |
| defterde kayıt YOK → TAM geçen sembol | **193** |
| **ayrışma / ihlal** | **0** |

En çok satır kaybeden semboller: HON 5.657 · DD 5.172 · EQT 3.744 · WBD 2.287 · ABT 2.266 ·
CTSH 955 · CI 834 · HLT 771 · ALB 709 · CMI 709.

**Defter 48.735 diyor, ölçüm 46.256 buluyor — fark 2.479 ve BEKLENEN:** defterdeki sayı HAM
CSV üzerinden üretildi; ölçüm yolunda `sanitize_bars` ÖNCE koşuyor (hayalet/karantina satırları
zaten düşmüş) ve defterin 61 sembolünün 4'ü mevcut 251'lik evrende yok. Sembol-başına ayrışma
kontrolü (>3 satır eşiği) **0 sembol** işaretledi.

### Brief'in istediği üç davranış — üçü de doğrulandı
1. **dikiş-dönemi DIŞLANIR** — 57 sembolde güvenli başlangıç öncesi satır kalmadı (0 ihlal).
2. **temiz dönem GEÇER** — güvenli başlangıç sonrası her satır korundu (0 ihlal).
3. **kayıt-yok sembol TAM geçer** — 193 sembolde 0 satır düştü (0 ihlal).

### Testler
```
./.venv/bin/python -m pytest tests/test_bars_integrity_v141.py -q
→ 26 passed
```
`tests/test_bars_integrity_v141.py` üç davranışı da adıyla kilitliyor:
`test_the_ledger_excludes_the_unsafe_period_and_says_so` ·
`test_a_missing_ledger_fails_open` · `test_component_ic_and_cf_backfill_read_the_ledger` ·
`test_safe_start_follows_the_LAST_break_not_the_first` ·
`test_the_ledger_is_not_a_sink_in_the_artifact_graph` (YASA 6 dedektörü kendi üzerinde).
**Bu tur yeni test yazılmadı** — mevcut kapsam brief'in istediği üç iddiayı zaten karşılıyor;
dördüncü bir kopya sadece bakım borcu olurdu.

---

## 4. SAYI DÜZELTMESİ + KAPANIŞ ÖNERİSİ (Rol-1'e)

1. **ROADMAP §WP-D "bars_integrity defteri (97 …)" kalemi → KAPANIR.** Mekanizma var, tüketici
   kablolu, sayaç tüketiliyor, testler yeşil, dışlama uçtan uca ölçüldü (46.256 satır / 57 sembol).
2. **Sayı tazelemesi:** ROADMAP "97 kalıcı dikiş" diyor; canlı defter **98 kırılma / 61 sembol**
   (92 ölçek dikişi + 5 hayalet geçmiş + 1 bozuk kesit). Mühendislik günlüğü satır 547 zaten
   "bütünlük defteri (61 sembol)" diyor — ROADMAP tazelenmeli.
3. **AÇIK KALAN (bu kalemin kapsamı DIŞI, ayrı biletler):**
   - `dataset.load` yolu bilerek bağlanmadı → **walk-forward / prescreen / reflect tabloları
     hâlâ kirli dönemi görüyor.** Kapatılması `dataset.load()`un replay-girişi ile canlı-girişine
     AYRILMASINI gerektirir ve HON/DD'nin canlı evrenden düşmesi **operatör kararıdır**.
   - Türetilmiş artefaktların (component_ic / cf / eşik eğrileri) güvensiz-dönem-dışlamalı
     YENİDEN ÜRETİMİ — WP-D'nin ayrı maddesi, bu teyitle kapanmaz.

## Yeniden üretim
```
mkdir -p <sandbox>/state && cp state/bars_integrity.json <sandbox>/state/
cp research/olcumler/wpd_bars_integrity_teyit/kalem2.py <sandbox>/
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python kalem2.py
```
