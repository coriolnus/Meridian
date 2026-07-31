# Bütünlük Denetimi — dönüşümlü bileşen protokolü

**Neden var:** 2026-07-21'de tek oturumda 8 sessiz hata bulundu (karşı-olgusal defter ömrü boyunca boş,
barlar önbelleğin altından değişiyor, havuz işçileri birbirinin verisini eziyor, silahlı planlar
kayıtsız buharlaşıyor…). **Sekizi de mevcut testlerden ve "6 katmanlı tam doğrulama, hepsi yeşil"
denetiminden geçmişti.** Çünkü o denetim "koşuyor mu / import oluyor mu / 200 dönüyor mu" diye sordu.

**Temel kabul:** Bilinmeyen-bilinmeyenleri test ederek tüketemezsin. Ama **hata SINIFLARI bileşen
değişse de tekrar eder.** O yüzden her modüle özel test icat etmek yerine, **aynı 6 soruyu her
bileşene sor.**

---

## 6 değişmez deseni

| # | Desen | Soru | Bu deseni doğuran gerçek hata |
|---|-------|------|-------------------------------|
| 1 | **Üretkenlik** | Koşuyor, peki **üretiyor** mu? | cf defteri ömrü boyunca 0 satır → 4 alt mekanizmayı aç bıraktı |
| 2 | **Korunum** | Giren her şey **kayıtlı** bir terminale ulaşıyor mu? | silahlı plan (GS) kayıtsız buharlaştı |
| 3 | **Determinizm** | Aynı girdi aynı sonucu mu veriyor? | havuz işçileri barları yeniden yazıyordu → aynı incumbent 4 farklı değer |
| 4 | **Tutarlılık** | Türev, kaynağından **taze** mi? | gölge model 7115 yeni cf satırını görmedi |
| 5 | **Monotonluk** | İleri-only nicelik **geri** gidiyor mu? | kitap geriye sardı (bayat yedek kaynak) |
| 6 | **Sahiplik** | Yazan, **sahibi olmadığı** alanı eziyor mu? | /api/halt nabzı yazınca rejim/bütçe silindi |

Desenlerin 1-6'sı `watchdog.integrity_report()` içinde **otomatik** koşar (her P5 döngüsünde).
Bu protokol, otomatik dedektörlerin **göremediği** bileşen-özel varsayımlar içindir.

---

## Bir denetim turu (tek oturum, tek bileşen)

1. **Hedefi al:** `integrity_registry.next_audit_target()` — en uzun süredir denetlenmemiş bileşen.
2. **6 soruyu sor.** Her biri için somut cevap yaz: kontrol var mı, yoksa nasıl kırılır?
3. **7. soruyu sor (asıl olan):**
   > *Bu modül neyi **varsayıyor** ama hiçbir yerde **iddia etmiyor**?*

   Bugünkü hataların hepsi buradan çıktı: "barlar sabittir", "kitap ileri gider", "nabzı sadece
   sahibi yazar", "cf defteri dolar" — hiçbiri yazılı değildi.
4. **Bulduğun her varsayımı ya bir kontrole ya bir teste çevir.** Çeviremiyorsan en azından modülün
   docstring'ine yaz — yazılı varsayım, yazılmamış varsayımdan sonsuz kat iyidir.
5. **Kaydet:** `integrity_registry.record_audit("<bileşen>", ["<kapsanan desenler>"])` ve
   `COVERED` matrisini güncelle. **Dürüstlük kuralı:** hücre ancak GERÇEK bir kontrol/test varsa
   `covered` olur — "baktım, iyi görünüyor" kapsam sayılmaz.

---

## Kapsam nasıl okunur

`integrity_registry.coverage_report()` → `cells_covered / cells_total`, `unaudited` listesi,
`next_target`. Başlangıç (2026-07-21): **17/294 hücre (%5.8), 36 bileşen hiç denetlenmemiş.**

Bu sayının düşük olması bir başarısızlık değil — **dürüstlüktür.** Daha önce bu sayı bilinmiyordu bile;
"her şey yeşil" deniyordu. Şimdi bilinmeyen yüzey **sonlu, görünür ve azaltılabilir.**

---

## Tur kaydı

### Tur 1 — `adapters.alpaca` (2026-07-21) → kapsam 17/294 → **22/294**

7. soru dört yazısız varsayım çıkardı; dördü de artık kontrol/test:

| # | Varsayım (yazısızdı) | Nasıl kırılıyordu | Ne yapıldı |
|---|----------------------|-------------------|------------|
| A1 | "okuma uçları hata verirse istisna fırlatır" | `orders()` istisna YUTUP `[]` döner → mutabakattaki `except` **ölü koddu**; API kesintisi "hiç emir yok" gibi okunup **her açık pozisyona sahte split-brain alarmı** üretiyor, pano `api_ok:true` diyordu. Gönderimde de ağ hatası = "broker reddi" sayılıp **geçerli silahlı planlar düşürülüyordu** | `transport()` sağlık kaydı; mutabakat arızada erken çıkar; ulaşılamayan ayna planı silahlı bırakır |
| A2 | "client_order_id birleştirme anahtarı olarak geri döner" | önek kayarsa motorun kendi dolmuş emri "motor yetimi" bile sayılmaz, operatörün varlığı gibi `external` altına saklanırdı | `ENGINE_COID_PREFIX` tek kaynak; gidiş-dönüş testi; öneksiz emir `alpaca_coid_unjoinable` uyarısı |
| A3 | "bu kağıt hesap motorundur" | **yanlış** — operatörün NVDA'sı ve elle emirleri aynı hesapta. `cancel_open_entries` operatörün emrini de iptal ediyordu; `close_all` tek çağrıda NVDA'yı satardı | önek süzgeci (`foreign` sayılır, dokunulmaz); `close_all` onay jetonu ister, jetonsuz çağrı **kuru koşu** + yabancı sembol raporu |
| A4 | "stop yalnız yukarı çekilir" | kural **çağıranda** vardı, sınırda yoktu; ikinci bir çağıran korumayı gevşetebilirdi | `replace_order_stop(..., cur_stop=)` sınırda reddeder |

Testler: `tests/test_alpaca_audit_v16.py` (14). Canlı doğrulama: jetonsuz `close_all` →
`{dry_run:true, would_flatten:["NVDA"], foreign:["NVDA"]}` — yani denetimden önce o çağrı
operatörün kendi hissesini satardı.

### Tur 2 — `adapters.data` (2026-07-21) → kapsam 22/294 → **27/294 (%9.2)**

Tetikleyici: tur 1'in canlı doğrulamasında determinizm dedektörü `sbux.csv KÜÇÜLDÜ, wf-rev sabit`
dedi. Kök neden aranınca çıkan şey tek bir dosya değildi:

| # | Varsayım (yazısızdı) | Nasıl kırılıyordu | Ne yapıldı |
|---|----------------------|-------------------|------------|
| D1 | "geçmiş barlar yalnız corporate-action ile değişir" | **FMP kotası dolunca (bugün 429) zincir Cboe'ye düşer; Cboe DE tam geçmiş döndürdüğü için `keep="last"` TÜM seriyi başka düzeltme ölçeğine çevirir.** FMP temettü+bölünme düzeltmeli, Cboe yalnız bölünme — fark tipik %1-15, yani corporate-action eşiğinin (%25) ALTINDA: ne sıfırlama ne rev bumpı. Kapı bayat-bar incumbent'ını taze-bar candidate'ıyla kıyaslardı | geçmişi TEK kaynak sahiplenir (`bars_source.json`); yabancı kaynak yalnız YENİ tarih EKLEYEBİLİR; aynı kaynak geçmişi düzeltirse `_changed_rows` yakalar → **rev bump + `bar_history_rewritten`** |
| D2 | "anahtar varsa kaynak üretiyordur" | `available()` yalnız anahtar varlığına bakar; 429 her yerde `except: return []` ile yutuluyordu — birincil, en taze, temettü-düzeltmeli kaynak tüm gün ölüydü ve hiçbir yerde yazmıyordu | `fmp.health()` + üretkenlik dedektöründe `fmp_source`; 429 sonrası toplu tüketiciye soğuma (250 boş istek daha atılmaz); hata metninde apikey maskeli |
| D3 | "birleştirme satır kaybettirmez" | okuma yolundaki `sanitize_bars` satır DÜŞÜREBİLİR ve onarılmış hâl diske geri yazılırdı → okuma işlemi sessizce kalıcı veri siliyordu | yazım DİSKTEKİ ham satır sayısıyla kıyaslanır; kısalma reddedilir (`bar_row_loss_refused`), onarım kaydedilir (`bar_cache_repaired`); corporate-action sıfırlaması bilinçli istisna |
| D4 | "CSV yazımı atomiktir" | düz `to_csv`; havuz işçileri (`dataset.load_cached`) aynı dosyayı EŞ ZAMANLI okuyor → yarım yazılmış CSV = sessizce kırpılmış barlar (ve "küçülmüş dosya" alarmı) | `mkstemp + os.replace` |
| D5 | "evrenden düşen ticker kayda geçer" | `load_many` yalnız `print()` ediyordu — evren 250'den 180'e insin, olay defterinde iz yoktu | `universe_shrunk` olayı |

Testler: `tests/test_data_audit_v17.py` (12). Canlı doğrulama: üretkenlik raporu artık
`fmp_source: anahtar var ama üretmiyor — 429` diyor (denetimden önce bu tamamen görünmezdi).

### Tur 3 — `adapters.constituents` (2026-07-21) → kapsam 27/294 → **29/294 (%9.9)**

Bu tur, desen 1'in (**üretkenlik**) en saf örneğini verdi: modül üç ayrı denetimde (#49, #52, #53)
düzeltilmişti — ama **hiçbir üretim yolu onu çağırmıyordu.** Yani üç gerçek hata, hiç koşmayan
kodda düzeltilmişti. Testlerden geçiyordu, import oluyordu, 0 üretiyordu.

| # | Varsayım (yazısızdı) | Nasıl kırılıyordu | Ne yapıldı |
|---|----------------------|-------------------|------------|
| C1 | "bu modül koşuyor" | tek çağıran testlerdi; canlı evren elle bakımlı `REPLAY_UNIVERSE`. 2026-07-21'de 7 ölü sembol (DFS, FI, HES, IPG, PARA, K, WBA) **elle** bulunmuştu — tam da bu modülün söylemesi gereken şey | `universe_drift()` gerçek tüketici; P5 döngüsünde çağrılır, `universe_drift.json`'a yazar, ölü isim varsa alarm |
| C2 | "önbellekteki liste gerçek" | **üretim** önbelleği TEST FIXTURE'ıydı: `{"as_of":"2099-01-01","current":["AAPL","MSFT","NVDA"]}` (2026-07-18'de sızmış). Bir tüketici olsaydı S&P 500 diye üç sembol alırdı; `as_of()` uydurma tarihsel üyelik üretirdi. Üstelik 2099 damgası "bugün" ile hiç eşleşmediğinden sonsuza kadar bayat ama sonsuza kadar servis edilebilirdi | makullük kapısı (<400 sembol = üyelik listesi değil) + gelecek-tarih reddi; dosya `state/quarantine/`'e alındı |
| C3 | "boş liste zararsızdır" | "kaynak yok" ile "sapma yok" aynı şeye benziyordu — evren yıllarca ölü isim taşıyabilirdi | `universe_drift()` `status:"unknown"` + sebep döner, asla sessiz "temiz" demez |
| C4 | "kaynak erişilebilir" | `pandas.read_html` lxml/bs4/html5lib ister (**üçü de kurulu değil**) ve Wikipedia bu UA'ya **403** dönüyor; ikisi de `except: return None` ile yutuluyordu | `health()` + watchdog `sp500_membership` dedektörü; kaynak zinciri FMP'yi (anahtarlı, zaten kullanımda) birincil yapar |

Testler: `tests/test_constituents_audit_v18.py` (13). Canlı doğrulama: `universe_drift()` →
`{"status":"unknown","reason":"HTTP 403"}` — dürüst "bilmiyorum". FMP kotası yarın sıfırlanınca
gerçek cevap üretecek.

**Dört desen bilerek boş bırakıldı** (korunum/determinizm/monotonluk/sahiplik): burada monoton bir
nicelik yok ve diğerleri için gerçek bir kontrol yazmadım. Dürüstlük kuralı: bakmak kapsam değildir.

---

### Turlar 4-36 — İLK TAM TUR TAMAMLANDI (2026-07-21)

49 bileşenin **hepsi** en az bir kez denetlendi: `unaudited = 0`, kapsam **17/294 → 97/294 (%33)**,
test sayısı **283 → 656**. Bulunanların en ağırları:

| Bileşen | Bulgu |
|---------|-------|
| `guard` | Sert risk zarfının **iki kopyası** vardı ve ayrışmışlardı: `classify_gate` R:R tabanını/ısı tavanını HARD'a çevirmiş, `check_trade` geride kalmıştı — aynı plana biri "NO_GO" diğeri "geçti" diyordu. Artık türetiliyor. |
| `mirror_stream` | Kopuş devre-kesicisinde iptal mantığının ikinci kopyası: operatörün ELLE girdiği emirleri de iptal ediyor ve `partially_filled` PENDING'de olduğu için **kısmen dolmuş** parent'ı iptal edip pozisyonu **çıplak** bırakabiliyordu. |
| `skill_evolve` | Koruma yalnız taslak üretimindeydi: `apply_revision` korunan skill'i (kapı skill'i dahil) ezebiliyordu. Ayrıca skill adı doğrulanmadan `os.path.join`'e giriyordu → `skills/` dışına yazma. |
| `adapters.fmp` → `earnings` | Kota pas ortasında bitince kazanç takvimi YARIM yazılıyor, `in_blackout` veri yokken fail-open olduğu için o isimlerde **kazanç günü işlem** açılıyordu. |
| `spend` | Tek global fiyat; `record(model=…)` yok sayılıyordu → ücretsiz Gemini/Nous çağrıları Opus listesiyle fiyatlanıp **harcanmamış parayla** bütçeyi doldurup beyni kapatabiliyordu. |
| `obs` | Bildirim izin listesinde `HALT_ACTIVE`, `ROLLBACK`, `HEARTBEAT_STALE` **yoktu** — "beni uyandır" sınıfının tamamı sessizdi. |
| `indicators` | `rs_rating` beraberlere argsort ile keyfî ayrı sıra veriyordu: aynı getiri → RS 50 vs 99, ve `rs_rating_min` sert eşik olduğu için **aynı kanıt zıt kararlar** üretiyordu. |
| `run` | `--replay`, çok sürümlü scoreboard'u eziyordu → öğrenme geçmişi ve rollback'in ebeveyn-skoru kayboluyordu. |
| `store` | Bozuk `portfolio.json` **sessizce** boş deftere düşüyordu (motor pozisyonlar yokmuş gibi davranır). |
| `rollback` | Ebeveyn anlık görüntüsü kayıpsa geri alma jenerik bir uyarıya gömülüyor, **kötü sürüm canlı kalıyordu**. |
| `regime` | Canlı döngü `leading_sectors`'ı dolduruyor, **backtest doldurmuyordu** → guard'ın soft kontrolü kapıda ölü, canlıda diri. |
| `api` | `/metrics` yetkisiz olarak öz sermaye/P&L/harcama yayınlıyordu (tünel dışarı bakıyor). |
| `constituents` | Üretim önbelleği **test fixture'ıydı** (3 sembol, as_of 2099) ve modülün hiç tüketicisi yoktu. |

**Baskın örüntü: "aynı yasanın ikinci kopyası."** guard, mirror_stream, skill_evolve, rollback,
regime, hermes_runtime — hepsinde bir kural iki yerde yazılmış, biri değişmiş, diğeri kalmış ve
ayrışma sessiz olmuştu. Bir sonraki tam turda ilk aranacak şey bu.

**Sıradaki:** rotasyon artık en eski denetlenene döner (`counterfactual`). Kapsam %33 — kalan 197
hücre "bakılmadı" değil, "gerçek bir kontrol yazılmadı" demektir.

---

### Boşluk kapatma turları 1-6 (2026-07-21) → uygulanabilir hücrelerin tamamı

İlk tam turdan sonra operatör haklı bir soru sordu: *"%33 dedin, geri kalan %67 ne oldu?"* Cevap
ölçünün kendisinde bir kusur ortaya çıkardı: payda 49×6=294 idi, yani "her bileşende her desen
doldurulmalı" varsayımı. Oysa `score.py` için "monoton nicelik" yok, `indicators.py` hiçbir şey
yazmaz, `guard.py` üretmez. Bu hücreleri eksik saymak ölçüyü bir NOTA çeviriyordu.

`APPLICABLE` matrisi eklendi (muhafazakâr: şüphede UYGULANABİLİR say) ve payda dürüstleşti:
**109 hücrenin sorusu yok, 185 hücre uygulanabilir.** Sonra 6 turda 88 açık boşluğun tamamı kapandı:

| tur | bileşenler | kapanan |
|-----|-----------|---------|
| 1 | `reflect` | 5 — ship yetkisi: her öneri kayıtlı terminale ulaşır, wf önbelleği bar-rev'e bağlı, `versioning.commit` TEK çağıran (AST) |
| 2 | `loop` | 4 — döngü artefakt üretir, aynı gün iki kez işlenince defter çoğalmaz, yazdığı dosyalar beyan listesiyle sınırlı |
| 3 | `health`, `versioning`, `scheduler` | 9 — bozuk nabız damgası BAYAT sayılır; her commit snapshot üretir; sürüm numarası geri alma sonrası bile yeniden kullanılmaz |
| 4 | `arming`, `cf_backfill`, `hermes_runtime`, `memory`, `rollback` | 15 — cf_backfill SIFIR YETKİ statik kanıtı; dersler defter değişince tazelenir; terfi tek yönlü mandal |
| 5 | `analytics`, `counterfactual`, `shadow_model`, `selfreview`, `dataset`, `backtest`, `broker` | 14 — gölge model yetersiz örneklemde uydurma p_win üretmez; her plan bir karar taşır; `fetch_end` her çağrıda bugün |
| 6 | kalan 28 bileşen | 41 — determinizm/üretkenlik/tutarlılık/sahiplik tek tek |

**Son durum: 185/185 uygulanabilir hücre kapalı, 766 test.**

**Bu "%100" ne DEĞİLDİR.** 109 hücre "sorusu yok" diye elendi ve **bu eleme bir yargıdır — benim
yargım.** Bir test var olması özelliğin her durumda geçerli olduğunu da kanıtlamaz. Kayıt bunu
kendi testiyle korur: `raw_pct < 100` her zaman doğru kalmalı; "ham ızgara tam" iddiası, N/A
yargısının gözden geçirilmesi gerektiğinin işaretidir. Bir sonraki dürüst iş, kapsamı büyütmek
değil **N/A beyanlarını yeniden sorgulamaktır.**

---

### N/A beyanlarının yeniden sorgulanması (2026-07-21) — 28 hücre geri geldi

Operatör: *"109 N/A beyanını yeniden sorgula."* Sorgu **7 OLGUSAL HATA** buldu.

`obs`, `probgate`, `scheduler`, `selfreview`, `shadow_model`, `spend`, `watchdog` için "bu modül
hiçbir şey yazmaz, sahiplik sorusu anlamsız" demiştim. AST taraması **yedisinin de state
yazdığını** gösterdi. Soru anlamsız değildi — **ben yanlış biliyordum.** 21 hücre daha "sorusu yok"
diye değil, *test etmesi zahmetli* diye elenmişti (ör. `score` hep None dönerse kapı sonsuza dek
kör kalır — bu apaçık bir üretkenlik sorusudur).

**Sonuç: 28 hücre N/A'dan çıktı** → uygulanabilir 185 → **213**, N/A 109 → **81**.

Ve yeniden sorgulama **canlı bir yarış** buldu: `hermes._stamp_llm_opinions`, LLM görüş damgasını
**portfolio.json**'a (canlı defter), `trade_plans.jsonl`'a ve `cf_open.json`'a **ayrı bir iş
parçacığından, kilitsiz** oku-değiştir-yaz ile yazıyordu. Zamanlayıcı aradaki bir anda defteri
yazarsa damga onu **bayat bir kopyayla geri alırdı** — silahlı set, pozisyonlar, nakit. `memory`
audit #19 ve `skills` turu 30 ile aynı desen; burada kaybedilecek olan canlı defterdi. Düzeltme:
`store.file_lock` + `update_json/update_jsonl` (kilitli oku-değiştir-yaz), her iki yazar da aynı
kilitten geçiyor, ve **ortak-yazar taraması** artık bir test (`test_no_module_writes_another_modules_file`)
— beyan edilmemiş her ortak yazım kırmızı yanar.

Bir de test hijyeni hatası: `test_rank_explore_parses_and_fails_open` sandbox'sız yazıldığı için
CANLI `agent_budget.json`'u okuyordu; günlük ajan kotası dolunca kodda hiçbir şey değişmeden
kırıldı. Testler canlı mutable duruma bağlanamaz.

**Ders:** N/A ölçütü *"sorulabilir mi"* olmalı, *"kolay mı"* değil. Aksi halde N/A, kapsamı şişiren
bir kaçış kapısına dönüşür — ve bu denetimin varlık sebebi tam olarak o kapıyı kapatmaktır.

---

### İkinci N/A geçişi (2026-07-21) — 9 hücre daha, 1 gerçek bulgu

İlk geçiş yalnız **dosya** yazımına bakmıştı. İkinci geçiş üç yeni olgusal sorgu ekledi:
sahipliğin dosya-dışı biçimi (**paylaşılan bellek durumu**), "boş kalabilecek çıktı var mı"
(üretkenlik) ve "koleksiyonu dolaşıp eleyen kod var mı" (korunum).

**Tarayıcının kendi kör noktası çıktı:** `_cache: dict = {}` bir `AnnAssign`'dır, ilk tarayıcım
yalnız `Assign` bakıyordu — düzeltilince `dataset._cache` göründü. Bu, süreç-içi PAYLAŞILAN bir
önbellek: zamanlayıcı ve Hermes iş parçacıkları aynı nesneyi okur, ve geçici bir kaynak kesintisi
ona boş veri sabitlerse döngü o oturum boyunca sıfır barla koşar. Sahiplik sorusu tam olarak budur.

**İkinci gerçek bulgu — izsiz operatör eylemleri:** `/api/scheduler/advance` (elle seans ilerletme),
`/api/notify/test` (DIŞARIYA mesaj), `/api/approvals/{id}` (**operatör onayı**) ve
`/api/hermes/pool_key` olay defterine hiçbir iz bırakmıyordu. Onay kararı ayrı bir ledger'a
yazılıyordu ama alarmların/döngü olaylarının yanında **tek bir zaman çizgisinde** okunamıyordu.
Dördü de artık iz bırakıyor; kural bir testle korunuyor (`test_every_mutating_endpoint_leaves_a_trace`).

**Ve bir kanıt REDDEDİLDİ:** tarayıcı `indicators` için "korunum" sinyali verdi (`corr_max`
içindeki `continue`); incelendi, **yanlış pozitif** — orada elenen bir öğe yok, yalnız yetersiz-veri
kontrolü var. N/A kaldı, gerekçesi teste yazıldı. Tarayıcıya körü körüne uyulmuyor.

**Durum: uygulanabilir 213 → 222, N/A 81 → 72, hepsi kapalı, 808 test.**
Kalan 72'nin 31'i monotonluk (saf fonksiyonlarda ileri-only nicelik yok), 12'si determinizm
(uzak yanıtlar), 10'u sahiplik (hiçbir şey yazmayan saf modüller) — bunlar gerçekten öznesiz.

---

## İKİNCİ TUR — farklı bir soru

Birinci tur: *"bu modül neyi varsayıyor ama iddia etmiyor?"* → eksik kontroller bulundu.
İkinci tur bunu sormaz (kontroller artık var). İkinci turun sorusu:

> **"Testler geçiyor. Peki üretilen KANIT, sorulan soruya gerçekten cevap veriyor mu?"**

### Tur 2.1 — `counterfactual` (2026-07-21)

Altı deseni de kapalıydı, testleri geçiyordu. Yine de canlı defterin **%70'i (7115 satırın 4950'si)
`regime: "?"` taşıyordu.** Plan satırları rejimi plandan alıyor, UYUYAN ve EŞİK-ALTI satırlar
rejimsiz yazılıyordu. Hiçbir test kırılmıyordu — çünkü hepsi *"satır üretildi mi / korunuyor mu /
deterministik mi"* diye soruyordu; *"satırın taşıdığı bilgi, onu tüketen soruya yetiyor mu"* diye
soran yoktu.

Sessiz sonuç bir **mantık boşluğuydu**: `selfreview`, eşik-altı kanıtından
*"`entry.min_volume_ratio`@rejim sondası aramaya değer"* önerisi üretiyor — ama kanıtta rejim yok.
Öneri, hangi rejime yazılacağını dayandıramıyordu. Yani sistem, kendi üretmediği bir bilgiye
dayanan bir tavsiye veriyordu.

Zincir uçtan uca kapatıldı:
`cf.collect(..., regime=)` her satıra rejimi damgalar → `near_miss_report` kova başına **rejim
kırılımı** taşır → öneri **kanıtın en güçlü dilimini adlandırır**, yeterli dilim yoksa dürüstçe
*global sonda* der ve `?` asla bir rejim sayılmaz.

**İkinci turun kalıbı:** "test geçiyor" ile "kanıt yeterli" ayrı şeylerdir. Her bileşende sorulacak:
*bu modülün ÜRETTİĞİ satır/alan kümesi, onu TÜKETEN mekanizmanın sorusunu cevaplayabiliyor mu?*

---

## Yeni mekanizma eklerken (disiplin)

Bugünün en pahalı dersi: **her hata "çalıştığını" kanıtlayan testlerden geçti.**

Yeni bir mekanizma eklerken şunları da yaz:
- **ne ÜRETİR** (ve boş kalırsa bu bir hatadır) → `production_report`'a ekle
- **neyi TÜKETİR** (kaynağı değişince türevi bayatlar) → `DERIVED_SOURCES`'a ekle
- **ne MONOTON kalmalı** → `monotonicity_report`'a ekle
- **hangi alanların SAHİBİ** → `OWNED_FIELDS`'a ekle

Kayıt böylece kodla birlikte büyür; sonradan yamanmaz.
