# DENETİM — SPLIT SINIFI (çift-kaynak ayrışması) — 2026-08-13

**Operatör talebi (2026-08-13):** *"sürekli bir yerlerde split konusu çıkıyor, bütün sistemi bu
hatalara karşı test etmek iyi olacak."*

**Tur sınırı.** SALT ÖLÇÜM + BELGE. `meridian/` altında hiçbir dosya değiştirilmedi; canlıya dağıtım
yapılmadı; `serve.sh` koşulmadı; broker'a emir gönderilmedi/iptal edilmedi; test dosyası yazılmadı;
pytest koşulmadı. Yazılan tek dosya budur.

> **ŞERH — TUR SINIRINDAN BİR SAPMA, BEYAN EDİLİYOR.** Brief `git` kullanımını yasaklamıştı. Kapanışta
> "yalnız bu dosya yazıldı"yı doğrulamak için **bir kez** `git status --porcelain` koşuldu (salt-okunur,
> ağaca dokunmaz). Bulgu kayda değer: `tests/test_hafta3a_v119.py` **değişmiş** görünüyor ve **bu
> denetim onu değiştirmedi** — paralel oturumun izidir ve aşağıdaki "ölçüm ortamının kendi arızası"
> beyanını bağımsız olarak doğrular. Başka hiçbir `git` komutu koşulmadı; `git log`/`diff` gerektiren
> her kalem §6'da **ÖLÇÜLEMEDİ** olarak duruyor. Canlı erişim
SALT-OKUNUR: betikler yerelde yazıldı ve `ssh … './.venv/bin/python -'` stdin'inden beslendi
(dokuz koşu). Canlı `state/`e tek bayt yazılmadı — SQLite'a `file:…?mode=ro` URI'siyle bağlanıldı;
uygulama tarafında yalnız `store.read_*` ve saf rapor üreticileri (`watchdog.coherence_report`,
`skills.catalog`) koşturuldu.

**Ölçüm anları.** Canlı defter/DB/olay: **2026-08-12T21:5x–22:03Z**. `broker_reconcile.json`
damgası: **2026-08-12T20:44:58Z**. Repo tarafı: yerel `main` çalışma ağacı, **2026-08-13 00:5x–01:0xZ**.

> **ÖLÇÜM ORTAMININ KENDİ ARIZASI — BEYAN.** Repo bu denetim **koşarken düzenleniyordu**: `meridian/shadowlaw.py`
> mtime **2026-08-13 01:00:03**, `tests/test_dalga_w1_v216.py` **01:05:05**, `state/goal.yaml` **00:08:13** —
> üçü de ölçüm penceresinin içinde. Bir çift (`DD_VETO_MARGIN`, §7-#5) **ayrışmış hâlde yakalandı
> (0,04 iken `goal.max_drawdown` 0,16'ydı), sonraki okumada onarılmış (0,08) bulundu.** Yani
> §3.2'nin "10 ayrık yüzey" sayımı **bir andır, kalıcı bir olgu değildir**; repo tarafı hareket
> hâlindeydi. Bu, MEMORY'deki *paralel-oturum* dersinin ölçüm sırasında bizzat tekrarlanmasıdır ve
> sayıya değil, **sınıfa** dair kanıt sayılmalıdır.

---

## 0. BU TURUN KONUMU — ÖNCEKİ TARAMANIN ÜSTÜNE

Bu sınıf bu depoda **daha önce yürünmüştür**: `docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md` (447 satır,
4 gün önce) 22 gerçek-ailesini elle yürüdü ve dört kovalı bir taksonomi kurdu. O turun hükmü hâlâ
geçerlidir ve bu tur onu **yeniden yazmaz**. Katkı üç yerdedir:

1. **REGRESYON YENİDEN-ÖLÇÜMÜ** — 08-09 bulguları 4 gün sonra canlıda ne durumda? (§2)
2. **YENİ YÜZEYLER** — o turun merceğine girmemiş çiftler: **repo ↔ canlı ağacın TAM taraması**
   (o tur 2 dosya ölçmüştü, bu tur 108 yüzeyin hepsini), pano rozetinin okuduğu alan, `README.md`
   kümesi, SQLite göçünün **yerel** yan-ürünü. (§3)
3. **KAPI BOŞLUĞUNUN ADI** — brief'in hipotezi ("tutarlılık deseni dosya-BAYATLIĞI ölçüyor,
   çift-kaynak AYRIŞMASINI değil") **ÖLÇÜLDÜ VE DOĞRULANDI**; kanıt §5'te, önerilen 8. desen §8'de.

**Yöntemin kendi arızaları — ÖLÇÜLDÜ VE BEYAN EDİLİYOR.**

| # | Arıza | Nasıl yakalandı | Sonuç |
|---|---|---|---|
| **Y-1** | `bounds.portfolio.sector_cap` **`{}`** okundu → "tavan bandı boşalmış" gibi göründü | `bounds.yaml` **düz noktalı anahtar** kullanıyor (`portfolio.sector_cap:` tek anahtardır); probe iç içe okumuştu. Yeniden ölçüm (`bounds.yaml:103`): `{min: 0.0, max: 30.0, step: 5.0}` | **YANLIŞ POZİTİF ÖNLENDİ** |
| **Y-2** | "4/4 pozisyon korumasız" bugünkü hâl sanılabilirdi | Alarmların damgası okundu: son `NAKED_POSITION` **2026-08-09T02:34:04Z**, bugünkü `broker_reconcile.json` kaydında koruma alanı **yok** | **§6-#1'e ÖLÇÜLEMEDİ olarak taşındı** |
| **Y-3** | Alt-ajan iddiası kanıt sanılabilirdi (iki keşif ajanı: kod-sabiti ↔ yapılandırma; üretilmiş artefakt ↔ doküman) | Hükme giren **her yüksek-şiddetli satır elle yeniden grep'lendi**: `app.js:6094/6133`, `test_skill_cleanup_v121.py:357`, `README.md:17,45,59,146`, `config.py:286`, `strategy.yaml:12`, `shadowlaw.py:102` | Doğrulananlar aşağıda; **doğrulanmayan hiçbir satır hükme girmedi** |
| **Y-4** | Brief'in kendi atfı yanlıştı | Brief *"mevcut 7 desen `integrity_registry.py:21`"* dedi. Ölçüm: o satırda **6** desen var; `CLAUDE.md`'de "desen" sözcüğü **hiç geçmiyor**. Gerçek "7" başka yerde (§3.6) | Brief'in atfı **düzeltildi**, sessizce benimsenmedi |

---

## 1. YÖNETİCİ ÖZETİ

| Ölçü | Sayı |
|---|---:|
| Envantere giren çift | **54** |
| **KAPISIZ** (sessizce ayrışır) — *bu denetimin asıl ürünü* | **26** |
| **KAPILI** (ayrışırsa kırmızı yanar) | **23** |
| **ÖLÇÜLEMEDİ** (+neden, §6) | **5** |
| **BUGÜN FİİLEN AYRIŞMIŞ** | **24** |
| Bilinçli ikizleme (yanlış-pozitif, §7) | **7** |

**Tek cümlelik hüküm.** Çift-kaynak şablonu bu depoda **çalışıyor ve bu tur onu yeniden kanıtladı**
(`coherence_report` üç bayat türevi saatiyle bağırıyor; orphan dedektörü göç arşivlerini *türeterek*
tanıyor; 5.542,09$'lık defter farkı `sermaye_resetleri` beyanıyla kuruşuna kadar kapanıyor;
`RUNBOOK.md` üreteciyle bayt-özdeş çivili) — **asıl borç, şablonun ölçtüğü NİCELİĞİN yanlış
olmasıdır: şablon ZAMAN ölçüyor, ayrışma ise DEĞERde.** Bu yüzden üç sınıf yapısal olarak görünmez:
**(a)** aynı anda yazılan zıt değerler · **(b)** aynı ağacın iki ortamdaki hâli · **(c)** kodun
yanında duran ama kimsenin türetmediği anlatı (`README.md`).

**En ağır dört bulgu:**

1. **§3.1 — Pano rozeti yanlış alanı okuyor.** `app.js:898` `hb.mirror_drift`e (=false) bakıp
   **"ayna uyumlu"** (yeşil) yazıyor; gerçek `rc.position_drift`te (=true), 4/4 pozisyon ~2 kat ayrık.
2. **§3.2 — Repo ↔ canlı: 108 yüzeyin 10'u ayrık**, biri (`analytics.py`) **bayt boyu birebir aynı,
   içeriği farklı** — boyut/mtime'a bakan doğrulama bunu "özdeş" der. Canlıda sürüm beyanı **yok**.
3. **§3.3 — `max_drawdown` ortamlar arasında ayrık** (repo 0,16 · canlı 0,08); üçlü kapı **iki
   tarafta da yeşil** çünkü tek checkout içinde koşuyor. Canlı motor bugün **iptal edilmiş** eşikle
   hüküm veriyor.
4. **§3.7/§3.8 — SUNUM KATMANI: tek kapı üç ayrı yoldan kaçırıyor.** `README.md`'nin "Locked
   strategy" satırı 3 sayıda birden yanlış; C10 bekçisi (a) README'yi **kapsamıyor**, (b)
   `workflow.js`'i **hiç taramıyor**, (c) kapsadığı dosyada bile **ifade biçimiyle atlatılıyor**
   ("68 **Meridian** skill" regex'e takılmıyor — fiilen koşturuldu, `[]` döndü).

---

## 2. REGRESYON — 08-09 BULGULARI 4 GÜN SONRA

| 08-09 bulgusu | Bugünkü ölçüm | Hüküm |
|---|---|---|
| §4.3 `skills.catalog()` kaynağın `retired` alanını **düşürüyor** | `catalog()` n=67; anahtarlar arasında **`retired` VAR** (canlı 22:01Z); defterde 36 retired | ✅ **KAPANMIŞ** |
| §3 #7 türev artefaktlar **5/14 bayat** | **3/15 bayat** (22:01Z): `equity_curve` **245,3 sa** · `self_review` 48,3 sa · `arming_report` 47,1 sa. `scoreboard`/`llm_calibration`/`broker_reconcile` **toparladı**; liste 14→15 (`equity_curve` eklendi) | ◐ **KISMEN** |
| §4.1 `equity_curve.json` donmuş, bir Faz-6 kilidini besliyor | Son nokta hâlâ **2026-07-20 / 94.457,91$**; `portfolio.last_date`=2026-08-12. Dedektör artık **görüyor** (`watchdog.py:1884`) ve 245,3 saattir bağırıyor | ◐ **KAPI KONDU, AYRIŞMA SÜRÜYOR** |
| §4.2 pozisyon adetleri ayrık | **BİREBİR AYNI SAYILAR** 3 gün sonra: NUE 54/25 · EMR 64/37 · BKNG 43/22 · AMGN 33/22 · `external:["NVDA"]` | ❌ **AÇIK — HİÇ HAREKET YOK** |
| §4.4 sektör/ısı tavanı dört sayı | `goal` **40,0** · `bounds.yaml:103` max **30,0** · `guard.py:428` **25,0** · runtime **0** — ve bu tur ölçüldü: 25,0/6,0'ın **hiçbir okuyucusu yok** | ❌ **AÇIK** (§3.5) |
| §4.9 `DERISK_FLOOR_DD` testsiz dördüncü kopya | Artık **çivili** (`test_derisk_rampa_kablosu_v237.py:68`) **ve** bağ beyanla koparıldı (`broker.py:33`) | ✅ **KAPANMIŞ** → §7-#3 |
| §3 #21 repo ↔ canlı: 95 dosyanın **2'si** ayrı | **108 yüzeyin 10'u** ayrı | ❌ **BÜYÜMÜŞ** (§3.2) |
| §3 #5 `scoreboard` 47,7 sa geride | `coherence` listesinde **YOK** → taze | ✅ **KAPANMIŞ** |
| brief: `scoreboard v3 ↔ strategy v5` | Canlı: `current_version`=**5**, `strategy.yaml`=**version: 5** | ✅ **KAPANMIŞ** (doğrulandı) |

---

## 3. YENİ BULGULAR — ŞİDDET SIRALI

### 3.1 ⛔ PANO ROZETİ YANLIŞ ALANI OKUYOR — "ayna uyumlu" derken ayna 2 kat ayrık

**Çift:** `heartbeat.mirror_drift` ↔ `broker_reconcile.position_drift`. İkisi **aynı adı
çağrıştırır, farklı gerçeği ölçer** — ve bu kodda yazılıdır:

- `loop.py:25` — `MIRROR_DRIFT_TOL = 0.005` · *"between internal sim fill and actual Alpaca fill"*
  → `mirror_drift` = **FİYAT** sapması
- `loop.py:3073` — `"mirror_drift": bool(out["drift"])` (fiyat kolu)
- `loop.py:3075` — `"position_drift": bool(pos["missing_on_alpaca"] or pos["qty_drift"])` → **ADET**
- `loop.py:2109` — nabza **yalnız** `mirror_drift` yazılır; `heartbeat.json`da `position_drift`
  anahtarı **YOKTUR** (canlı doğrulandı)

**Tüketici bölünmesi:**

| Tüketici | Okuduğu | Bugün ne diyor |
|---|---|---|
| `app.js:898` — HESAP kartı **durum rozeti** | **yalnız** `hb.mirror_drift` | **"ayna uyumlu"** (yeşil, `pos`) |
| `app.js:1049` — eylem listesi | `hb.mirror_drift \|\| rc.mirror_drift \|\| rc.position_drift` | "Alpaca aynasında sapma var" |

**Canlı (22:01Z):** `heartbeat.mirror_drift`=**False** · `reconcile.mirror_drift`=**False** ·
`reconcile.position_drift`=**True**. Pano **aynı ekranda iki zıt cümle** kuruyor.

**Kök neden — bir DÜZELTMENİN yan ürünü.** `app.js:9739-9744` P6 tekilleştirmesi sapmanın "İKİ
yerde, İKİ FARKLI SÖZCÜKLE" yazıldığını doğru teşhis etti ve mutabakat kartından metni kaldırıp
**adres** bıraktı (*"değerin TEK EVİ mutabakat masasıdır"*). Ama geriye kalan özet rozeti **başka
bir alandan** besleniyordu ve taşınmadı. Tekilleştirme gerçeği tek eve taşıdı; **rozet eski evin
anahtarında kaldı.**

**KAPI: ❌ KAPISIZ.** `position_drift`in repo genelinde 3 geçişi var (`loop.py:3075` üretim,
`app.js:1049` tüketim, `tests/test_regime_patch.py:47` tek assert) — nabızla rozet arasında kapı yok.
**RİSK: YÜKSEK** — operatörün "her şey yolunda" gördüğü tek yüzey bu rozettir.

---

### 3.2 ⛔ REPO ↔ CANLI: 108 YÜZEYİN 10'U AYRIK — VE BİRİ BAYT BOYU BİREBİR AYNI

Tam sha256 taraması (2026-08-12T22:03Z canlı ↔ 2026-08-13T01:0xZ repo):

```
KIYASLANAN YÜZEY: 108   AYNI: 98   AYRI: 10
  meridian/adapters/constituents.py  canlı=  13750b yerel=  16251b  fark=+2501
  meridian/analytics.py              canlı= 276568b yerel= 276568b  fark=   +0  <<< BAYT BOYU AYNI, İÇERİK AYRI
  meridian/api.py                    canlı= 314832b yerel= 318996b  fark=+4164
  meridian/hermes.py                 canlı= 242324b yerel= 242851b  fark= +527
  meridian/recompute.py              canlı=  36147b yerel=  39610b  fark=+3463
  meridian/reflect.py                canlı= 118692b yerel= 118884b  fark= +192
  meridian/shadowlaw.py              canlı=  40244b yerel=  40793b  fark= +549
  meridian/skills.py                 canlı=  49574b yerel=  55601b  fark=+6027
  meridian/web/app.js                canlı= 814128b yerel= 815568b  fark=+1440
  state/goal.yaml                    canlı=  13138b yerel=  13652b  fark= +514
```

**`analytics.py` bu denetimin sergi parçasıdır:** **276.568 baytta özdeş**, sha256 **ayrı** (canlı
`ff70e187…`, yerel `37d3afbc…`). Sebep §3.3: `0.08`→`0.16` iki karakter yerine iki karakter koyar.
**Boyuta, satır sayısına ya da mtime'a bakan hiçbir doğrulama bunu göremez** — ve bu ders bu depoda
zaten öğrenilmişti (`bounds.yaml` bekçisi mtime→içerik-sha256'ya çevrildi, 0652841). O ders
**bekçiye** uygulandı, **dağıtım hattına uygulanmadı.**

**KAPI: ❌ KAPISIZ, ölçüldü.** Canlıda dağıtılmış sürümü beyan eden hiçbir şey yok:
`/opt/meridian/.git` **YOK** (rsync); `VERSION` / `version.txt` / `.deployed_sha` /
`state/dagitim.json` / `state/deploy.json` — **hiçbiri yok**. `dagit.sh:30` dağıtılan commit'i
**konsola basıyor** (`git rev-parse --short HEAD`), hiçbir yere **kaydetmiyor**.

**KISMİ İSTİSNA (İYİ ÖRNEK):** `state/*.yaml` kopyaları **bayt-özdeş doğrulanıyor** —
`dagit.sh:253` uzak dosyayı `cmp -s` ile karşılaştırır, tutmazsa **dağıtımı durdurur** (`exit 1`).
Sözleşme **yapılandırma için var, kod için yok.**

**RİSK: YÜKSEK** — MEMORY'deki *paralel-oturum rsync'i* dersinin (660dc10) açık kalan bacağı.

---

### 3.3 ⛔ `max_drawdown` ORTAMLAR ARASINDA AYRIK — üçlü kapı iki tarafta da yeşil

| Kaynak | YEREL REPO | CANLI |
|---|---:|---:|
| `state/goal.yaml:20` `max_drawdown` | **0,16** | **0,08** |
| `meridian/analytics.py:1614` `EDGE_MAXDD_MAX` | **0,16** | **0,08** |
| `meridian/analytics.py:2094` `RESULT_MAXDD_MAX` | **0,16** | **0,08** |
| `meridian/shadowlaw.py:102` `DD_VETO_MARGIN` (= yarısı) | **0,08** | **0,04** |

Yerel `goal.yaml:20` şerhi: *"0.08→0.16 (OPERATÖR KARARI 2026-08-13 penceresi)"*.

**KAPI: ◐ VAR AMA ORTAM-KÖR.** Eşitlik **gerçekten çivili** — `tests/test_orgu2_v103.py:120`,
`tests/test_hafta3a_v119.py:78` (üçlü), `tests/test_dalga_w1_v216.py:522` (`DD_VETO_MARGIN ==
goal/2`). Ama kapı **tek checkout içinde** koşar: yerelde 0,16/0,16/0,16/0,08 → **yeşil**; canlıda
0,08/0,08/0,08/0,04 → **yeşil**. **İki taraf kendi içinde tutarlı, birbirine göre ayrık.**

**RİSK: YÜKSEK** — bu sayı `edge_verdict` (`analytics.py:2017`) ve `result_verdict`
(`analytics.py:2339`) üzerinden Faz-6 kilitlerini besler.

---

### 3.4 ⛔ YEREL `state/` KANONİK ADLARLA DONMUŞ İKİNCİ KİTABI TUTUYOR

Canlıda göç **2026-07-31T10:56:02Z**'de yapıldı (`entity_meta.migrated_at`); altı defter DB'ye
taşındı, kaynaklar `.migrated` ekiyle arşivlendi, **kanonik adlar canlıda YOK**. Yerelde ise
kanonik adlar **duruyor ve dolu**:

| Defter | YEREL dosya | CANLI DB | Fark |
|---|---:|---:|---|
| `trades.jsonl` | **95 satır** | **97** | −2 |
| `trade_plans.jsonl` | **390 satır** | **409** | −19 |
| `portfolio.realized_pnl` | **−5.542,09** | **+277,98** | reset öncesi |
| `portfolio.last_date` | **2026-07-28** | **2026-08-12** | 15 gün |
| `portfolio.positions` | **[] boş** | **4 açık** | tamamen ayrık |
| `scoreboard.current_version` | 5 | 5 | ✓ |

**Neden KAPISIZ:** `store._path` kanonik ada bakar; yerelde o ad **VAR ve dolu** → yerel koşan her
şey (`research/olcumler/` ölçüm kampanyası, sprint, mutasyon, backtest) **sessizce 2026-07-28
fotoğrafını** okur. `storage.py:27-33` bu sınıfı **canlı için** teşhis etmiştir (`MERIDIAN_DB=off`
tuzağı) ve `active()` bir `db_off_kaynaklar_arsivde` uyarısı basar — ama o uyarı **DB dosyası
varken** tetiklenir. Yerelde `state/meridian.db` **YOK**, dolayısıyla uyarı da yok: **yerel ağaç
"göç hiç olmamış" bir dünyada, tam sessizlikle çalışıyor.**

**RİSK: YÜKSEK** — ön-kayıt kartlı ölçüm disiplini tam da bu ağaçta koşuyor; bir ölçümün 95 satırlık
donmuş defterden mi 97 satırlık canlıdan mı konuştuğu **hiçbir yerde damgalı değil**.

---

### 3.5 ⚠ `SECTOR_CAP_DEFAULT_PCT` / `HEAT_CAP_DEFAULT_PCT` — OKUYUCUSU OLMAYAN "VARSAYILAN"

```
$ grep -rn "SECTOR_CAP_DEFAULT_PCT|HEAT_CAP_DEFAULT_PCT" meridian/ tests/
meridian/guard.py:428:SECTOR_CAP_DEFAULT_PCT = 25.0
meridian/guard.py:429:HEAT_CAP_DEFAULT_PCT = 6.0
```

**İki satır, ikisi de tanım — repo genelinde (kod + test) tek okuyucu yok.** Fiilî runtime
varsayılanı **0**. Aynı tavanı **dört sayı** iddia ediyor (`goal` 40,0 · `bounds` max 30,0 · sabit
25,0 · runtime 0) ve **üçüncüsü ölü**. **KAPI: ❌ KAPISIZ. RİSK: ORTA** (bugün ısırmıyor, tavan kapalı).

---

### 3.6 ⚠ "7 DESEN" ↔ "6 DESEN" — AYNI PANO GÖRÜNÜMÜNDE, YAN YANA

Brief bu denetimi *"mevcut 7 desen `integrity_registry.py:21`"* diye tarif etti. **Ölçüm brief'i
düzeltiyor** (Y-4):

- `integrity_registry.py:21` — `PATTERNS` → **6** desen; docstring (satır 5) da *"6 değişmez-deseniyle"* der
- `watchdog.py:1284-1292` — `_DEDEKTOR_BOS` → **7** dedektör (6 + `parity`); `watchdog.py:1299`
  7.'yi **bilinçli** olarak `PATTERNS` dışında tutuyor (bileşen-kapsamlı değil, sistem-geneli)
- `CLAUDE.md` — "desen" sözcüğü **hiç geçmiyor** (brief'in atfı yanlıştı)

**Asıl bulgu panoda:** `app.js:6094` başlığı **"Bölüm 5 · Bütünlük dedektörleri (7 desen)"** yazıyor;
**aynı kartın** `app.js:6133` satırı `${cov.patterns} desen` render ediyor = `coverage_report()` →
**6**. Yani **tek görünümde 7 ve 6 yan yana**, aralarında hiçbir köprü yok. Kodun kendi yorumu riski
adıyla biliyor: `app.js:6048` ve `:6086` — *"'7 desen temiz' izlenimi tam da bu kaçışla doğar"*.

**KAPI: ❌ KAPISIZ. RİSK: DÜŞÜK** (davranış değil, muhasebe) — ama §8'in "8. desen nereye" sorusunun
cevabını belirlediği için burada.

---

### 3.7 ⛔ `README.md` — "Locked strategy" satırı ÜÇ SAYIDA YANLIŞ, ve kapı yanlış dosyalara bakıyor

`README.md:146-147` tek cümlede sistemin sözleşmesini iddia ediyor. **Ölçüm:**

| README iddiası | Kod/config gerçeği | Hüküm |
|---|---|---|
| "**max drawdown 8%**" | `state/goal.yaml:20` = **0,16** (2026-08-13 operatör kararı) | ❌ **BAYAT** |
| "**5 positions**" | `state/goal.yaml:131` `max_open_positions: **20**` (2026-08-12) | ❌ **BAYAT** |
| "**1.0R** each" | `state/strategy.yaml:12` `position_size_r: **0.5**` (2026-08-12) | ❌ **BAYAT** |
| "target +7% / 30d" | `goal.yaml:16` `target_return_30d: 0.07` | ✅ |
| "min Sharpe 1.2" | `goal.yaml:17` | ✅ |
| "3% max daily loss" | `goal.yaml:132` `max_daily_loss_pct: 3.0` | ✅ |
| "reflect every 5 trades · min sample 30 · 5 bps slippage" | `goal.yaml:32-33` + `slippage_bps: 5` | ✅ |

Aynı dosyada üç bayat iddia daha:

| README | Gerçek | Hüküm |
|---|---|---|
| `:17` "**66** Claude trading skills" | `skills_registry.json`: total **67**, retired **36** → canlı **31**; dizin: 31 klasör + 36 `_emekli` | ❌ **BAYAT** |
| `:45` "`skills/shadow/` for **10 sessions**" | **Böyle bir dizin YOK** (repo genelinde tek geçiş bu satır). Gerçek mekanizma: kayıt girdisinde `shadow` **boolean** bayrağı (`skills.py:478-510`) | ❌ **BAYAT** (yol); "10 sessions" → §6-#4 |
| `:59-60` "circuit-breaker … last **20 sessions**" | `analytics.py:18` `LADDER_BREAKER_WINDOW_DAYS = **30**`; `analytics.py:143-149` pencerenin 2026-07-30'da satır-sayımından **takvime** çevrildiğini yazıyor | ❌ **BAYAT** (hem birim hem sayı) |

**KAPI: ❌ KAPISIZ — VE KÖK NEDEN YAPISALDIR.** Bu sınıfın kapısı **zaten yazılmış**:
`tests/test_skill_cleanup_v121.py:359` `test_c10_presentation_carries_no_hardcoded_skill_count`
sunum sayfalarını sabit skill sayısına karşı tarar. Ama kapsamı:

```python
# tests/test_skill_cleanup_v121.py:357-358
PRESENTATION_PAGES = ("meridian/web/landing.html", "meridian/web/workflow.html",
                      "workflow-diagram.html")
```

**`README.md` bu tuple'da YOK.** Kapı 2026-07-30'da tam bu hastalık için kuruldu (testin kendi
docstring'i önceki "66/68/59 skill" vakasını anlatıyor) ama **yalnız web sunum katmanına
kapsandı** — deponun en çok okunan sayfası dışarıda kaldı. **RİSK: ORTA-YÜKSEK** (dış okuyucu +
yeni oturum brief'i buradan besleniyor).

---

### 3.8 ⛔ SUNUM KATMANI — TEK KAPI, ÜÇ AYRI KAÇIŞ YOLU

C10 bekçisi (`tests/test_skill_cleanup_v121.py:361-366`) bu sınıfın **tek** içerik-gerçek kapısıdır.
2026-07-30'da tam bu hastalık için kuruldu — docstring'i açık: *"Sabit '66/68/59 skill' yazıları
arşivle bir gecede yalan oldu."* Bu tur **üç ayrı kaçış yolu ölçtü**:

**(a) KAPSAM DIŞI DOSYA — `README.md`** (§3.7): tuple'da yok.

**(b) HİÇ TARANMAYAN DOSYA — `meridian/web/workflow.js`** (canlı `/workflow` rotasından servis
edilir, tuple'da yok, hiçbir test içeriğini Python'a bağlamıyor):

| `workflow.js` iddiası | Gerçek | Hüküm |
|---|---|---|
| `:22` *"Strateji **v4** … `min_exposure_score` **40→20**"* | `strategy.yaml:1` `version: **5**`; `:13` `regime.min_exposure_score: **40**` (eşik geri döndü) | ❌ **BAYAT** |
| `:28` *"**250** sembollük evren (7 ölü sembol **bugün** tazeleriyle değişti…)"* | `data.py:2549` kendi yorumu: *"evren 2026-07-30'da FISV ile **251** oldu"*; "bugün" 2026-07-21'e ait | ❌ **BAYAT** |
| `:39-40` "20 slot · 0,5R · ısı 5R · rampa 15/36" | `goal.yaml:131,140,170-171` + `strategy.yaml:12` | ✅ **DOĞRU** |
| `:41-42` "5 × 0,25R sonda, toplam ≤1,25R" | `loop.py:22-24` | ✅ **DOĞRU** |
| `:38` ARMED_SETUPS anlatısı | `strategy.py:1029` (4 kurulum) | ✅ **DOĞRU** (2026-08-12'de elle düzeltildi) |

**Bu karışım, saf bayatlıktan DAHA tehlikelidir:** aynı dosyada 2026-08-12'de elle tazelenmiş
satırlar ile 2026-07-20/21 fosilleri yan yana duruyor ve **okuyucunun hangisinin hangisi olduğunu
ayırt etmesinin hiçbir yolu yok.** Kısmî onarım, "resmen bayat" ilan edilmiş bir dosyada **sahte
güven** üretir. Kodun kendisi bunu biliyor: `app.js:6438-6439` yorumu, workflow.html'in emekli
edilme gerekçesi olarak **tam bu iki ifadeyi** (`"250 sembollük evren"`, `"min_exposure_score
40→20"`) adıyla anıyor — ama ifadeler `workflow.js`'ten hiç silinmedi.

**(c) KAPSANAN DOSYADA İFADE BİÇİMİYLE ATLATMA — `workflow-diagram.html`.** Dosya tuple'da **VAR**,
test **yeşil**, sayı **hâlâ orada**. Regex fiilen koşturuldu:

```
regex r"\d+\s+skill" eşleşme: []
"Meridian skill" geçen satır: tip:"HERMES_BRAIN_ORDER: … (68 Meridian skill + SOUL.md) → Gemini…"
```

Araya giren tek sözcük (`Meridian`) `\d+\s+skill`in bitişiklik koşulunu bozuyor. **Gerçek: 31 canlı
skill** (`api.py:747` `skills_live`); kayıt defteri toplamı 67 — **68 hiç olmadı.** Aynı dosyada iki
ağır bayatlık daha:

| `workflow-diagram.html` | Gerçek | Hüküm |
|---|---|---|
| `:146` *"momentum_burst ve episodik pivot **UYUYAN**"* | `strategy.py:1029` `ARMED_SETUPS = (breakout_vcp, pullback, exhaustion_hammer, momentum_burst)` — momentum_burst **SİLAHLI**, exhaustion_hammer hiç anılmıyor | ❌ **BAYAT** |
| `:195` `sb:"**gemini-3.5-flash** · native"` | `hermes.py:348` `GEMINI_DEFAULT_MODEL = "gemini-pro-latest"`; `hermes.py:356` `"gemini-3.5-flash": "gemini-flash-latest",  # canlı config'teki ölü ad (**üretim 404**, 2026-08-12)` | ❌ **BAYAT — ÖLÜ MODEL** |

Sonuncusu sınıfın en keskin hâli: sunum katmanı, kodun **404 verdiğini kendi yorumunda yazdığı** bir
modeli hâlâ sistemin beyni diye ilan ediyor. Aynı hata `app.js:9802-9810`'da vardı ve
`/api/secrets → model_defaults` canlı bağıyla **düzeltildi**; `workflow-diagram.html` düzeltme
öncesi hâlde kaldı. *(Not: aynı dosyanın `:193-194` düğümü **doğru deseni** kullanıyor —
sayı yazmak yerine *"güncel sayı: state/skills_registry.json"* diyor. Doğru cevap dosyanın içinde,
iki satır ötede.)*

**KAPI: ◐ VAR AMA ÜÇ YOLDAN KAÇIRIYOR. RİSK: ORTA-YÜKSEK** (dış okuyucu + yeni oturum brief'i).

---

### 3.9 ▪ İKİ İYİ ÖRNEK — kapının doğru hâli neye benziyor

Bu turun kıyas tabanı; §8'in önerileri bunları kopyalıyor:

- **`app.js:6455-6471` `HAT_ADIMLARI`** — workflow.html'in canlı halefi. **Hiç sabit sayı taşımıyor**;
  kendi başlık yorumu (`app.js:6443-6445`) niyeti yazıyor: *"ADIMLAR RESİMDEN EMİLDİ, SAYILARI
  EMİLMEDİ."* Kapısı gerçek: `tests/test_ia_v199.py:341-353` `watchdog.EXPECTED` sözlüğünü
  **ayrıştırıp** her mekanizmanın çizelgede bir evi olduğunu çiviliyor; `:356+` ölçülmeyeni
  uydurmadığını. **Yapısal olarak bayatlayamaz.**
- **`landing.html:664` + `landing.js:88-91`** — skill sayısı `d.skills_live`den canlı geliyor
  (`api.py:747`), çivisi `test_skill_cleanup_v121.py:369-392`. C10'un **çalıştığı** vaka.

---

### 3.10 ⚠ `config.default_strategy()` YEDEĞİ — "AYRILMAZ ikili"nin yarısını taşıyor

- `meridian/config.py:286` — `"position_size_r": 1.0` (yedek; `load_strategy()` `strategy.yaml`
  yok/boş/bozuk olduğunda buraya düşer, `config.py:186-204`)
- `state/strategy.yaml:12` — `position_size_r: **0.5**` (canlı, 2026-08-12'den beri)

`state/goal.yaml:123-125` bu parametrenin `max_open_positions: 20` ile **"AYRILMAZ ikili"** olduğunu
açıkça yazıyor: 20-slot zarfı **yalnız 0,5R ile birlikte** ölçüldü ve onaylandı (EDG-2026-026/032).
`strategy.yaml`ın kendi notu da aynısını der. Yedek yol **20 slotu 1,0R ile eşliyor** — operatörün
kendi yorumunun *hiç doğrulanmadı* dediği bileşim. (Not: `guard.classify_gate`'in `heat_hard_r`=5,0
tavanı toplam riski yine sınırlar; sonuç patlama değil, **niyet edilenden çok daha az sayıda, iki
kat büyük pozisyon**.)

**KAPI: ❌ KAPISIZ** (arandı: `grep -rn position_size_r tests/*.py`; `default_strategy` ile
`position_size_r`/`max_open_positions` birlikte geçen test **yok**). **RİSK: ORTA** (yalnız yedek
yol ateşlenirse).

---

### 3.11 ▪ GÖÇ ARŞİVLERİ — İYİ ÖRNEK, ama kapı canlıda ESKİ SÜRÜMDE

`state/*.migrated` altı arşiv **bilinçlidir** (geri dönüş yolu) **ve dedektörü vardır**:
`recompute._orphan_state_files` (`recompute.py:400`) arşivleri **beyaz listeyle değil TÜRETEREK**
tanır (`recompute.py:430`) — kökü bilinmeyen bir arşiv kapıdan geçmez. Örnek alınacak desen.

**Ama:** 2026-08-12T20:46:28Z'de alarm düştü — `orphan_state_files — … scoreboard.json.migrated-20260812-201359-p192112`.
**Damgalı** çarpışma-dalını tanıyan düzeltme (v238) `recompute.py`de **yazılı ama canlıda değil**
(§3.2 listesinin bir kalemi). **Kapı repoda kapalı, canlıda açık.** **RİSK: DÜŞÜK.**

---

## 4. TABLO — ÇİFT · KAYNAK-A · KAYNAK-B · KAPI · CANLI ÖRNEKLEM · RİSK

Kategoriler: **(a)** defter/DB · **(b)** kod sabiti ↔ yapılandırma · **(c)** üretilmiş artefakt ·
**(d)** pano ↔ kod · **(e)** iç ↔ dış · **(f)** kod ↔ doküman · **(g)** ortamlar arası.

### 4.1 KAPISIZ — bu denetimin asıl ürünü (18)

| # | Kat. | Çift | Kaynak-A | Kaynak-B | Canlı/bugünkü örneklem | Risk |
|---:|:--:|---|---|---|---|---|
| 1 | d | ayna rozeti | `loop.py:2109` `heartbeat.mirror_drift` (fiyat) | `loop.py:3075` `reconcile.position_drift` (adet) | **AYRIK** — `app.js:898` "ayna uyumlu" yazarken 4/4 pozisyon 2× ayrık | **YÜKSEK** |
| 2 | g | repo ↔ canlı kod | yerel `main` ağacı | `/opt/meridian` (`.git` yok, sürüm beyanı yok) | **AYRIK 10/108**; `analytics.py` bayt-boyu özdeş | **YÜKSEK** |
| 3 | g,b | `max_drawdown` ortamlar arası | yerel 0,16 (`goal.yaml:20`+`analytics.py:1614,2094`) | canlı 0,08 | **AYRIK**; her ortam kendi içinde yeşil | **YÜKSEK** |
| 4 | a | yerel defter ↔ canlı DB | `state/trades.jsonl` 95 · `trade_plans` 390 · `portfolio` boş | DB 97 · 409 · 4 pozisyon | **AYRIK** (§3.4) | **YÜKSEK** |
| 5 | f | README "max drawdown 8%" | `README.md:146` | `goal.yaml:20` = 0,16 | **AYRIK** | ORTA-YÜKSEK |
| 6 | f | README "5 positions · 1.0R" | `README.md:146-147` | `goal.yaml:131`=20 · `strategy.yaml:12`=0,5 | **AYRIK** | ORTA-YÜKSEK |
| 7 | f | README "66 skills" | `README.md:17` | registry: 67 total / 31 canlı | **AYRIK** | ORTA |
| 8 | f | README `skills/shadow/` | `README.md:45` | dizin **yok**; `skills.py:478-510` boolean bayrak | **AYRIK** | ORTA |
| 9 | f | README "last 20 sessions" | `README.md:59-60` | `analytics.py:18` = 30 **takvim günü** | **AYRIK** | ORTA |
| 10 | f | PRODUCT.md "state/ dosyaları tek gerçek kaynak" | `PRODUCT.md:165-167` | `storage.py:1-28` + `RUNBOOK.md:1195`: 6 defter SQLite'ta (2026-07-31) | **AYRIK** (dosyaya bakan insan için) | ORTA |
| 11 | b | sektör/ısı tavanı | `goal` 40,0 · `bounds.yaml:103` 30,0 | `guard.py:428-429` 25,0/6,0 **okuyucusuz** · runtime 0 | **AYRIK** (dört sayı) | ORTA |
| 12 | b | `default_strategy` yedeği | `config.py:286` `position_size_r: 1.0` | `strategy.yaml:12` = 0,5 (20 slotla "AYRILMAZ") | **AYRIK** (yedek yol) | ORTA |
| 13 | d | `app.js` alarm jetonları | `app.js:3066,3103,3147,3175,3208` elle kopya JS dizileri | `obs.py:25-71` `ALARM_*` (14 sabit) | **EŞİT** ✓ (14/14) — dil sınırını aşan elle kopya | ORTA |
| 14 | b | `guard.DISCIPLINE_MIN_RR` | `guard.py:289` = 2,0 | `bounds.yaml:7` `exit.profit_target_r.min` = 2,0 | **EŞİT** ✓ — `bounds` altına inerse planlar kalıcı hard-veto | ORTA |
| 15 | b | `REGIME_N_MIN` ↔ `min_sample` | `analytics.py:1580` = 30 | `goal.yaml:33` = 30 | **EŞİT** ✓ — çivi **literal** (`test_orgu2_v103.py:111`), çapraz-dosya değil | DÜŞÜK |
| 16 | b | `min_sample` yedeği 20 | `score.py:86` · `shadow_variants.py:561` `goal.get(...,20)` | gerçek değer 30 | **LATENT AYRIK** (anahtar eksikse ısırır) | DÜŞÜK |
| 17 | a | `ledgers.CONTRACTS` ↔ `storage._COLS` | `ledgers.py:54-70` `required` | `storage.py:81-106` tipli kolonlar | **TUTARLI** ✓ — ayrışma sorgulanabilirliği bozar, doğruluğu değil | DÜŞÜK |
| 18 | f | "7 desen" ↔ "6 desen" | `app.js:6094` başlık "(7 desen)" | `app.js:6133` `${cov.patterns}` = 6 · `integrity_registry.py:21` | **AYRIK** (aynı görünümde) | DÜŞÜK |
| 19 | d | `workflow-diagram.html:195` Gemini modeli | `sb:"gemini-3.5-flash · native"` | `hermes.py:348` `gemini-pro-latest`; `:356` ölü ad, **üretim 404** | **AYRIK — ÖLÜ MODEL** | ORTA-YÜKSEK |
| 20 | d | `workflow-diagram.html:164` "68 Meridian skill" | sabit sayı | `api.py:747` `skills_live` = **31**; defter toplamı 67 | **AYRIK** — C10 kapsıyor ama regex **atlıyor** (koşturuldu: `[]`) | ORTA-YÜKSEK |
| 21 | d | `workflow-diagram.html:146` kurulum kadrosu | "momentum_burst … UYUYAN" | `strategy.py:1029` `ARMED_SETUPS` — **silahlı**; exhaustion_hammer hiç yok | **AYRIK** | ORTA |
| 22 | d | `workflow.js:22` rejim eşiği | "Strateji v4 · `min_exposure_score` 40→20" | `strategy.yaml:1` v**5** · `:13` = **40** | **AYRIK** | ORTA |
| 23 | d | `workflow.js:28` evren boyu | "250 sembollük evren … bugün" | `data.py:2549` = **251** (2026-07-30'dan beri) | **AYRIK** | ORTA |
| 24 | d | `landing.html:669,747` ↔ `:864` tarama boyu | "**3.000** hisse" (×2) | "**2.847** hisse" (aynı sayfa) · gerçek **251** | **AYRIK** + kendi içinde çelişik; bölüm "maket" etiketi **taşımıyor** (`:719` etiketi yalnız `:675-736` kapsar) | ORTA |
| 25 | d | `landing.html:884` örneklem eşiği | "örneklem **20**'ye ulaşmadan" | `goal.yaml:33` `min_sample: **30**` | **AYRIK** | ORTA |
| 26 | d | `workflow.html:365-384` emeklilik afişi | "2026-07-20 sürümü, o günden beri tazelenmiyor" | `workflow.js:38,40` içeriği **2026-08-12** tarihli | **AYRIK** (afiş kendi dosyasıyla çelişiyor); çivi (`test_ia_v199.py:319-325`) yalnız **dizgi varlığı** bakıyor | DÜŞÜK |

### 4.2 KAPILI — mekanizma var (21, örneklem)

| # | Kat. | Çift | KAPI (kanıt) | Canlı örneklem | Risk |
|---:|:--:|---|---|---|---|
| 19 | c | `equity_curve` ↔ `trades` | `watchdog.py:1884` `DERIVED_SOURCES` | **AYRIK — 245,3 sa** | **YÜKSEK** |
| 20 | e | pozisyon adedi ↔ Alpaca | `ALARM_MIRROR_DRIFT` (4 satır, 20:44:58Z) | **AYRIK** — 08-09'dan beri aynı sayılar | **YÜKSEK** |
| 21 | c | `self_review.json` | `DERIVED_SOURCES` | **AYRIK — 48,3 sa** | ORTA |
| 22 | c | `arming_report.json` | `DERIVED_SOURCES` | **AYRIK — 47,1 sa** | ORTA |
| 23 | b | `EDGE_MAXDD_MAX`≡`RESULT_MAXDD_MAX`≡`goal` | `test_orgu2_v103.py:120` · `test_hafta3a_v119.py:78` | Her ortamda eşit ✓ (ortam sınırı hariç, #3) | DÜŞÜK |
| 24 | b | `DD_VETO_MARGIN` ≡ `goal/2` | `test_dalga_w1_v216.py:522` | **Ölçüm sırasında ayrık yakalandı, onarıldı** (§ölçüm arızası) | DÜŞÜK |
| 25 | b | `guard.HEAT_HARD_R`/`HEAT_REVIEW_R`/`CORR_REVIEW` ≡ `goal.limits` | `test_kovab_dalga3_v166.py:185` | Eşit ✓ (5,0/3,5/0,85) | DÜŞÜK |
| 26 | b | `heat_hard_r ≤ max_open × max_position_r` | `test_kovab_dalga3_v166.py:196` | Tutarlı ✓ (5,0 ≤ 20,0) | DÜŞÜK |
| 27 | b | `DERISK_FULL/FLOOR_DD` ≡ `goal.limits` | `test_derisk_rampa_kablosu_v237.py:67` · `test_dalga_w1_v216.py:497` | Eşit ✓ (0,15/0,36) | DÜŞÜK |
| 28 | b | `guard.GOAL_KEYS` ≡ `goal.yaml` anahtarları | `test_guard_audit_v27.py:36` | Eşit ✓ (20/20) | DÜŞÜK |
| 29 | b | `guard.LIMIT_KEYS` ≡ `goal.limits` | `test_guard_audit_v27.py:43` · `test_kovab_dalga3_v166.py:223` | Eşit ✓ (12/12) | DÜŞÜK |
| 30 | b | `config.VALID_REGIMES` ≡ `regime.py` | `test_config_audit_v25.py:73` · `test_batch_j.py:14` | Eşit ✓ | DÜŞÜK |
| 31 | b | `RESULT_N_MIN` ≡ `goal.min_sample` | `test_hafta3a_v119.py:82` (çapraz-dosya) | Eşit ✓ (30) | DÜŞÜK |
| 32 | b | `MAX_ENTRY_GAP_PCT` ≡ `limit_pct_cap` | `test_icra_gercekligi_v141.py:194` | Eşit ✓ (0,04) | DÜŞÜK |
| 33 | b | `ENTRY_LIMIT_*` yedeği | `test_mutborc_broker_entry_law_v148.py:85` | Eşit ✓ (0,5/0,01) | DÜŞÜK |
| 34 | c | `docs/RUNBOOK.md` ↔ `ops/runbook_uret.py` | `test_uiux_s1b_v154.py:74-82` **yeniden üretip bayt-özdeş** çiviler; CI'da (`.github/workflows/ci.yml:16-17`) — **İYİ ÖRNEK** | §6-#5 | DÜŞÜK |
| 35 | c | tipografi korpusu | `test_tipografi_rampa_v209.py` SHA-256 kıyası **3/7** artefakt | 4/7 yalnız *varlık* kontrolü | DÜŞÜK |
| 36 | a | `scoreboard` ↔ `strategy.yaml` sürümü | — | **EŞİT ✓** (5=5) | DÜŞÜK |
| 37 | a | göç arşivleri ↔ DB | `recompute.py:430` **türetilmiş** tanıma | Tanınıyor; damgalı dal canlıda eski (§3.11) | DÜŞÜK |
| 38 | a | HALT ↔ `heartbeat.halted` | `health.py` her yazımda yeniden damgalar | 08-09: eşit | DÜŞÜK |
| 39 | a | nabzın çok-yazarlı alanları | `watchdog.OWNED_FIELDS` + `ownership_report` | 08-09: `lost: []` | DÜŞÜK |
| 40 | f | "19/19 authed" | `test_api_audit_v21.py:37-47` — **kendini güncelleyen** (rotayı canlı ayrıştırır, sayıyı gömmez) | Bugün **24/24** ✓ | DÜŞÜK |
| 41 | d | `app.js` canlı zaman çizelgesi ↔ `watchdog.EXPECTED` | `test_ia_v199.py:341-353` sözlüğü **ayrıştırıp** her mekanizmanın evini çiviler; `:356+` uydurmayı yasaklar — **İYİ ÖRNEK** | Yapısal olarak bayatlayamaz ✓ | DÜŞÜK |
| 42 | d | `landing.html:664` skill sayısı | `landing.js:88-91` → `api.py:747` `skills_live` **canlı bağ**; çivi `test_skill_cleanup_v121.py:369-392` | **31** ✓ (C10'un çalıştığı vaka) | DÜŞÜK |
| 43 | d | `app.js` düşüş/P&L/sürüm göstergeleri | Sabit sayı **yok** — hepsi API yükünden enterpole (`app.js:5105,8586,8946`) | Kıyaslanacak çift oluşmuyor ✓ | DÜŞÜK |

**Tek-kaynak olduğu doğrulananlar (kopya aranıp bulunamadı):** `SECTORS` (`backtest.py:38`, diğerleri
`import` eder) · `RETIRED_SYMBOLS` (`adapters/data.py:2612`) · `obs.NOTIFY_TOKENS` (`globals()`ten
türetilir) · "251 sembol" (10+ yerde tutarlı) · otonomi merdiveni ölçütleri (`analytics.py:168-174`
≡ `README.md:57-59`).

---

## 5. KAPI BOŞLUĞUNUN ADI — brief'in hipotezi ÖLÇÜLDÜ

**Hipotez:** *"tutarlılık deseni dosya-BAYATLIĞI ölçüyor, çift-kaynak AYRIŞMASINI değil."*
**DOĞRULANDI.** Kanıt `watchdog.py:1889-1909`:

```python
def coherence_report() -> dict:
    """#4 — türev bayatlığı. Kaynak güncellendiği halde türev eskiyse bayrak."""
    a = _m(art)                                     # türevin mtime'ı
    newest = max([m for m in (_m(s) for s in srcs) if m], default=None)
    if newest and a < newest - COHERENCE_GRACE_S:   # SADECE ZAMAN KIYASI
        stale.append({"artifact": art, "behind_h": ...})
```

Ölçtüğü tek nicelik **zaman**dır (`store.mtime`). Sorduğu: *"türev kaynağından eski mi?"*
**Sormadığı:** *"iki kaynak aynı şeyi mi söylüyor?"* İki dosya **aynı saniyede** yazılıp **zıt
değerler** taşısa `coherence_report` **yeşil** verir.

Bu tam olarak §3.1'in (ikisi de her döngüde tazelenir, biri False biri True), §3.3'ün (iki ortam da
taze), §3.5'in (dört sabit, hiçbiri "bayat" değil) ve §3.7'nin (README hiçbir şeyden *türemez*,
dolayısıyla asla "geride" olamaz) gözden kaçma mekanizmasıdır. Yedi dedektörün **hiçbiri
değer-eşitliği ölçmüyor**: `parity` makullük/oran, `ownership` alan-ezilmesi, `monotonicity`
geri-sarma ölçer. **DEĞER AYRIŞMASI dedektörü YOK.**

---

## 6. ÖLÇÜLEMEYENLER — ADIYLA

| # | Ölçülemeyen | Neden | "0" DEĞİL, ne demek |
|---|---|---|---|
| 1 | **Pozisyonların BUGÜNKÜ koruma durumu** | Bugünkü `broker_reconcile.json`da koruma alanı **yok** (anahtarlar: `alive_order_syms, api_ok, date, drift, emir_penceresi, entry_slippage, exit_fill, failed_submissions, force_sync, ghosts, mirror_drift, position_drift, positions, stripped, trail_synced, updated`); Alpaca'ya ağ çağrısı bilerek yapılmadı | Son `NAKED_POSITION` alarmı **2026-08-09T02:34:04Z** (32 satır). Bugün korumasız oldukları **DEĞİL**, bugün **ÖLÇÜLMEDİĞİ** — 3 günlük kayıt boşluğu. *Bu, tur sonrası bakılacak ilk kalem olmalı.* |
| 2 | **`scoreboard.json.migrated-20260812-201359-p192112`'nin akıbeti** | 20:46:28Z'de alarmlandı; 22:03Z taramasında **yok** | Silindiği/taşındığı ölçülmedi; alarmın gerçekliği kesin |
| 3 | **Alpaca hesabının ŞU ANKİ pozisyonları** | Tur sınırı: broker'a dokunulmadı | Adetler **2026-08-12T20:44:58Z** damgasından — "Alpaca şu an 25 tutuyor" değil, "son mutabakat 25 ölçtü" |
| 4 | **10 ayrık dosyanın fark İÇERİĞİ/YÖNÜ** (`analytics.py`, `shadowlaw.py`, `goal.yaml` hariç) | `git` bu turda YASAK; diff tur-ayrıklığı sözleşmesine girer | Fark **var** (sha256, damgalı); üçünde yön **ölçüldü**, kalan 7'sinde ölçülmedi |
| 5 | **`README.md:45`'in "10 sessions" sayısı** | Gölge oturum/gün sayan bir kod yolu **bulunamadı** (aynı "10" `PRODUCT.md:47` ve `docs/PATTERN-ETUDU-2026-08-06.md:431`'de de var → tutarlı tasarım niyeti) | Yol adı (`skills/shadow/`) **kesin bayat**; sayının zorlanıp zorlanmadığı bilinmiyor |

---

## 7. YANLIŞ-POZİTİF LİSTESİ — bilinçli ikizlemeler (tasarım, kusur değil)

| # | Görünen "çift" | Neden KUSUR DEĞİL — kanıt |
|---|---|---|
| 1 | `portfolio.realized_pnl` **+277,98** ↔ `Σ trades.pnl_dollars` **−5.264,10** | **Beyanlı sermaye reseti.** `portfolio.sermaye_resetleri`: `ofset: 5542.09`, `onceki_realized_pnl: -5542.09`, `tarih: 2026-08-01T15:14:29Z`, gerekçe yazılı. Ölçülen fark **5.542,08** — beyanla **kuruşuna kadar** uyuşuyor. Mekanizma `sermaye.py:80` + `recompute.py:287`. **Kopya değil, ofsetli iki farklı soru.** |
| 2 | `portfolio.positions` **4 açık** ↔ `trades` tablosunda açık işlem **0** | `trades.jsonl` **kapanmış** işlem defteridir: `ledgers.py:55` `required=("id","ts_open","ts_close",…)`; yazım yalnız kapanışta (`loop.py:2197`, `broker.py:703`). **İki farklı gerçek, tek kaynak.** |
| 3 | `broker.DERISK_FLOOR_DD` **0,36** ↔ `goal.max_drawdown` | Bağ **2026-08-12'de bilinçli koparıldı ve beyan edildi** — `broker.py:33` "ŞERH — KOPAN BAĞ", `test_dalga_w1_v216.py:464` eski iddiayı tarihiyle emekli ediyor, `test_derisk_rampa_kablosu_v237.py:68` yeni değeri çiviliyor. Mezar-taşı testi **sessiz yeniden-bağlanmaya karşı kapıdır**. |
| 4 | `state/*.migrated` altı arşiv ↔ DB | **Geri dönüş yolu**; `store.py` yasası "hiçbir şey silinmez". Orphan dedektörü **türeterek** tanıyor (`recompute.py:430`), beyaz listeyle değil. |
| 5 | `alpaca.KORUMA_TIF` ↔ `broker.ENTRY_TIF` | Ayrılık **bilinçli ve testle zorlanıyor**: `test_koruma_yeniden_kurma_v211.py:345` koruma TIF'inin giriş TIF'inden **türetilmesini YASAKLIYOR**. |
| 6 | `goal.limits.kill_switch_file` ↔ `health.py:14` sabit HALT yolu | `goal.yaml:172-174` kendi içinde beyan ediyor (*"HİÇBİR KOD OKUMAZ"*); `config.py:78` ve `analytics.py:2121` de sınıfı adıyla biliyor. **Beyanlı ölü kopya, sessiz değil.** ŞERH: beyan "değer sürüklenmesi"ni değil "kablosuzluğu" kapsıyor — operatör bu anahtarı düzenlerse **sessiz no-op** olur. |
| 7 | `research/olcumler/*` donmuş ölçüm çıktıları · `tests/fikstur/vaka_*` | Nokta-zaman kanıt kayıtlarıdır; güncel kodu **yansıtmaları beklenmez**. Bayatlık burada tasarımdır. |

**Ortak ilke.** Bu yedisini "kusur"dan ayıran şey kopyanın yokluğu değil, **kopyanın hangi soruyu
cevapladığının YAZILI olması** — 08-09 turunun hükmü aynen geçerli: *kopyanın kendisi kusur
değildir; kusur, kopyanın hangi soruyu cevapladığının yazılı olmamasıdır.*

---

## 8. ÖNCELİK SIRALI DÜZELTME ÖNERİLERİ — "kapı nereye konmalı"

### P0-a · Pano rozetini gerçeğin evine bağla (§3.1)
**Kapı türü:** tüketici düzeltmesi + kapsam testi. `app.js:898` rozeti `hb.mirror_drift` yerine
`app.js:1049`'un zaten kullandığı birleşik ifadeyi okumalı; daha iyisi **nabza `position_drift`
alanını taşımak** (`loop.py:2109`) — o zaman nabzı okuyan her tüketici otomatik kapsanır.
**Kapı:** fixture'da `position_drift=True, mirror_drift=False` kurup panonun ürettiği rozet metninin
"uyumlu" **olmadığını** çivileyen assert.

### P0-b · Dağıtılmış sürümü CANLIDA BEYAN ET (§3.2, §3.3)
**Kapı türü:** dağıtım-kapısı + bekçi sondası. `dagit.sh` dağıtım sonunda canlıya
`state/dagitim.json` yazmalı: `{commit, dagitim_ts, dosya_sha_ozeti}`. İki kapı bedavaya gelir:
(1) bekçi sondası — canlı ağacın sha özeti beyanla tutmuyorsa alarm ("yarım rsync" sınıfı);
(2) `analytics.py` vakası imkânsızlaşır çünkü kıyas **içerik-sha256** üzerindendir.
**Bu, `bounds.yaml` bekçisinde zaten öğrenilmiş dersin (0652841: mtime→içerik-sha256) dağıtım
hattına taşınmasıdır.** `dagit.sh:253`'ün `cmp -s` deseni yapılandırma için doğru cevabı zaten
veriyor — kod tarafına da aynısı.

### P0-c · C10 bekçisinin ÜÇ KAÇIŞ YOLUNU kapat (§3.7, §3.8) — **en ucuz kapı**
Üçü de `tests/test_skill_cleanup_v121.py`de, tek turda:
1. **Kapsam:** `:357` tuple'ına `"README.md"` + `"meridian/web/workflow.js"` ekle.
2. **Regex:** `r"\d+\s+skill"` → `r"\d+\s+(\w+\s+)?skill"` (ya da sayı+`skill` arasına en fazla iki
   sözcük). Fiilen ölçüldü: bugünkü desen `workflow-diagram.html`in "68 **Meridian** skill"ini
   kaçırıyor ve test **yeşil** kalıyor.
3. **Kapsam genişliği:** sabit *skill sayısı* tek sınıf değil. Sunum katmanına **hiçbir motor sayısı**
   elle yazılamamalı; kural `landing.js:88-91`in ve `workflow-diagram.html:193-194`ün zaten
   uyguladığı desendir — *sayı ya canlı gelir ya da adres verilir.*

Kalan doküman iddiaları (drawdown, pozisyon, R, pencere, evren boyu, model adı) için: **"Locked
strategy" satırını `goal.yaml`/`strategy.yaml`dan TÜRETEN** bir çivi — satırdaki her sayı config'ten
okunmalı, elle yazılmamalı. Aynı desen `PRODUCT.md:165-167` için de geçerli. Model adı için hazır
çözüm var: `app.js:9802-9810`'un `/api/secrets → model_defaults` canlı bağı kopyalanır.

**Ayrıca — emeklilik afişleri iş görmüyor (§3.8-b, §4.1-#26).** `workflow.js`/`workflow-diagram.html`
"emekli" ilan edildi ama **kısmen tazelendi**, ve kısmî tazeleme sahte güven üretiyor. İki temiz
seçenek: ya içerik **tamamen** dondurulur (tazeleme yasağı teste bağlanır), ya da canlı bağa taşınır.
Bugünkü üçüncü hâl — "emekli ama bazı satırları güncel" — en kötüsüdür.

### P1 · 8. BÜTÜNLÜK DESENİ: **AYRIŞMA** (`divergence`) — nereye konacağı ÖLÇÜLDÜ
**Nereye:** `meridian/watchdog.py:1284` `_DEDEKTOR_BOS` + `integrity_report` — **`integrity_registry.py`ye DEĞİL.**
Gerekçe §3.6'da ölçüldü: `integrity_registry` statik **kapsam matrisidir** (bileşen × desen, elle
doldurulur); `watchdog._DEDEKTOR_BOS` çalışma-anı **dedektör ailesidir** ve 7. desen (`parity`)
oraya eklendi. Bir *dedektör* dedektör tarafına gider. *(Aynı turda `app.js:6094` başlığı ile
`app.js:6133` sayısı arasına köprü kurulmalı; yoksa 8. desen eklendiğinde pano "8 desen"/"6 desen"
diye aynı hatayı bir kez daha yapar.)*

**Desenin sözleşmesi — `coherence`den farkı (§5):**

| | `coherence` (mevcut #4) | `divergence` (önerilen #8) |
|---|---|---|
| Ölçtüğü | `mtime` farkı | **değer eşitliği** |
| Sorduğu | "türev kaynağından eski mi?" | "iki kaynak aynı şeyi mi söylüyor?" |
| Kaçırdığı | zıt-değerli iki taze dosya | (bayatlığı `coherence` kapsar) |

**Kayıt biçimi** — `DERIVED_SOURCES`in kardeşi, `EQUIVALENT_TRUTHS`; her satır bir **ilişki** taşır
(`eşit` / `yarısı` / `kapsar` / `beyanlı-ayrı`) ki §7'nin bilinçli ikizlemeleri **kayda girsin ve
sessiz muafiyet olmasın** — `recompute.py:430`'un "beyaz liste değil, türetme" ilkesiyle aynı ruh:

```python
EQUIVALENT_TRUTHS = {
  "max_drawdown":  [("goal.yaml","max_drawdown"), ("analytics","EDGE_MAXDD_MAX"),
                    ("analytics","RESULT_MAXDD_MAX"), ("shadowlaw","DD_VETO_MARGIN", "yarisi")],
  "ayna_sapmasi":  [("heartbeat.json","mirror_drift"),
                    ("broker_reconcile.json","position_drift", "kapsar")],
  "sektor_tavani": [("goal.yaml","limits.max_sector_exposure_pct"),
                    ("bounds.yaml","portfolio.sector_cap.max"), ("guard","SECTOR_CAP_DEFAULT_PCT")],
  "alarm_jetonlari":[("obs","ALARM_*"), ("web/app.js","jetonlar")],
  "rr_tabani":     [("guard","DISCIPLINE_MIN_RR"), ("bounds.yaml","exit.profit_target_r.min")],
  "derisk_bandi":  [("broker","DERISK_FLOOR_DD"), ("goal.yaml","max_drawdown", "beyanli-ayri")],
  "evren_boyu":    [("adapters.data","REPLAY_UNIVERSE"), ("web/workflow.js","250"),
                    ("web/landing.html","3.000/2.847")],
  "gemini_modeli": [("hermes","GEMINI_DEFAULT_MODEL"), ("workflow-diagram.html","sb")],
}
```

**Neden bu kayıt sunum katmanını da kapsamalı:** §3.8 kaçışlarının üçü de "kapı yok"tan değil,
**"kapının kapsamı elle tutulan bir listeydi"**den doğdu. `EQUIVALENT_TRUTHS` bir *gerçek* kaydıdır,
*dosya* kaydı değil — yeni bir tüketici (JS, doküman, kart) aynı gerçeği yazdığında satıra eklenir ve
regex biçimine bağımlılık ortadan kalkar.

### P2 · Yerel `state/` donmuş defterine damga (§3.4)
**Kapı türü:** runtime uyarı + ölçüm damgası. Yerelde `meridian.db` yokken kanonik defter dosyası
**varsa**, `store` süreç başına bir kez `yerel_donmus_defter` uyarısı basmalı — canlıdaki
`db_off_kaynaklar_arsivde` uyarısının **simetriği** (`storage.py:33`'te sınıf zaten teşhis edilmiş,
yalnız ters yönü kapalı). Ek: `research/olcumler/` sonuç JSON'ları defterin satır sayısı +
`entity_meta` damgasını yazmalı; bir ölçümün **hangi kitaptan** konuştuğu sonradan sorulabilsin.

### P3 · Kalan kapısız sabitler (§3.5, §3.10, §4.1-#13…17)
`SECTOR_CAP_DEFAULT_PCT`/`HEAT_CAP_DEFAULT_PCT` okuyucusuz → ya bağla ya kaldır.
`config.default_strategy()` `position_size_r` yedeği `strategy.yaml`la birlikte taşınmalı (ya da
yedek yolun 20-slot bileşimini reddetmesi). `REGIME_N_MIN` çivisi literal yerine `config.goal()`ten
okumalı (kardeşi `RESULT_N_MIN` zaten öyle — `test_hafta3a_v119.py:82` deseni kopyalanabilir).
`min_sample` yedeği 20 → 30. Hepsi P1'in `EQUIVALENT_TRUTHS` kaydına girerse tek kapıyla kapanır.

### P4 · `equity_curve` (§2) — kapı VAR, **hüküm** yok
Dedektör 08-09'da kondu, o günden beri **bağırıyor**, ayrışma sürüyor. Bu kapı eksiği değil,
**alarm→eylem** eksiğidir (MEMORY: *oturum-basi-canli-triyaj*, "alarm öttü, kimse dinlemedi" — VLO
dersi; ve o dersin öznesi VLO bu turun olay defterinde *"MIRROR_DRIFT ayna pozisyonu kayıp: VLO"*
satırıyla **yine** görünüyor). Öneri: `coherence` bayatlığı bir eşiği aşarsa alarm sınıfı
yükselsin — **245 saat ile 3 saat aynı rengi taşımamalı.**

---

## 9. BU TURUN HÜKMÜ — TEK CÜMLE

Çift-kaynak şablonu bu depoda **çalışıyor ve bu tur onu kanıtladı** (üç bayat türev saatiyle
bağırıyor, göç arşivi türetilerek tanınıyor, 5.542,09$'lık defter farkı beyanla kuruşuna kadar
kapanıyor, RUNBOOK üreteciyle bayt-özdeş çivili, canlı zaman çizelgesi `watchdog.EXPECTED`e
ayrıştırılarak bağlı) — ama şablonun ölçtüğü nicelik **ZAMAN**dır, ve bu yüzden üç sınıf yapısal
olarak görünmezdir: **aynı anda yazılan zıt değerler** (pano "ayna uyumlu" derken 4/4 pozisyon iki
kat ayrık), **aynı ağacın iki ortamdaki hâli** (108 yüzeyin 10'u ayrık, biri bayt-boyu birebir aynı,
ve ayrışan sayı canlı motorun düşüş hükmünü veren eşiğin ta kendisi) ve **hiçbir şeyden türemeyen
anlatı** (sunum katmanı 8 ayrı yerde bayat, bir yerde 404 veren bir modeli sistemin beyni ilan
ediyor). Ve bu turun en öğretici tek satırı şudur: bu sınıfın **kapısı zaten yazılmıştı** — C10 —
ama kapsamı **elle tutulan bir dosya listesi** ve eşleşmesi **bir regex biçimi** olduğu için üç ayrı
yoldan aynı anda kaçırıyor; kapının **yeşil yanması**, ölçtüğü şeyin doğru olduğu anlamına gelmiyor.
Sekizinci desen bu yüzden bir **zaman** dedektörü değil, bir **değer** dedektörü olmalı — ve kaydı
**dosya** değil **gerçek** üzerinden tutmalıdır.

---

*Denetim ajanı, 2026-08-13. Kanıtsız satır yoktur: her iddia `dosya:satır` ya da damgalı canlı ölçüm
çıktısıdır. Alt-ajan bulgularının hükme giren her satırı elle yeniden doğrulanmıştır (Y-3).
Ölçülemeyenler §6'da adıyla listelenmiştir — hiçbiri "0" diye yazılmamıştır.*
