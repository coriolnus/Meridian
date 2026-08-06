# BÜTÜNLÜK PANELİ DÖKÜMÜ — 2026-08-06

**Operatör bulgusu:** "pano BÜTÜNLÜK DEDEKTÖRLERİ kartında çok ihlal gösteriyor; ama
`state/integrity_report.json` `{}`."

**Bu rapor bir HÜKÜM değil bir DÖKÜMdür:** her ihlali adıyla listeler, gerçek mi bu haftanın
restart/sermaye-reset fırtınasının artığı mı olduğunu ölçümle söyler ve düzeltme ÖNERİSİ yazar.
**Uygulama AYRI TUR** (Rol-1 hükmü) — bu turda hiçbir dedektör susturulmadı, hiçbir eşik
gevşetilmedi, hiçbir taban ilerletilmedi.

---

## 0. ÖNCE İKİ YANLIŞ VARSAYIM DÜZELTİLİYOR

**(a) `state/integrity_report.json` DİYE BİR DOSYA YOK — hiç olmadı.** Depoda o adı yazan tek bir
satır kod bulunmuyor (`grep -rn "integrity_report\.json" meridian/ tests/ docs/ ops/` → 0 eşleşme).
Panelin `{}` görmesi bir bozulma değil; **var olmayan bir dosyaya bakılmasıdır**.

Panelin GERÇEK kaynağı bir dosya değil, **her istekte yeniden hesaplanan bir ölçümdür**:

```
app.js:4719   const ig = d.integrity || {}      ← BÖLÜM 5 kartı
api.py:2231   watchdog.integrity_report_cached()   (20 sn süreç-içi önbellek)
watchdog.py:891  integrity_report(persist=False)   ← yedi dedektör, TAZE
```

`persist=False` bilinçlidir ve gerekçesi kaynakta yazılı (watchdog.py:1527-1532): pano salt-okunur
bir GET ucudur; her yenilemede tabanı yazsaydı **panoyu açık tutmak dedektörü körleştirirdi**.
Tabanı ilerleten TEK yol `check_integrity_and_alarm`'dır (zamanlayıcı kancası).

Kalıcı vekiller (panelin kaynağı DEĞİL, ama denetlenebilir iz):
`state/integrity_alarmed.json` (hangi ihlal ALARMLANMIŞ hâlde mandalda) ·
`state/events.jsonl` (ihlal GEÇİŞLERİ) · `monotonic_state.json` / `ownership_state.json` /
`bars_fingerprint.json` / `monotonic_amnesty.json` (dedektör tabanları).

**(b) "Çok ihlal" ile "çok alarm" AYNI ŞEY DEĞİL.** Panel her 20 saniyede o an DÜŞEN her satırı
yeniden türetir; olay defteri ise yalnız GEÇİŞLERİ yazar. Panelde 10 kırmızı satır, defterde o
ihlal başına 1 alarm demektir. Kartın kalabalık görünmesinin bir kısmı budur — ama hepsi değil
(§3'te gerçek olanlar sayılıyor).

---

## 1. ÖLÇÜM PENCERESİ VE YÖNTEM (dürüst sınırlar)

| | |
|---|---|
| Girdi | `backups/a1/state-2026-08-04.tar.gz` (sha256 `cc789063a…`), Mac çekimi 2026-08-05T02:33 |
| Defterin son satırı | **2026-08-04T23:28:53Z** (34.215 satır) |
| Yöntem | salt-okuma; yedek geçici dizine açıldı, `MERIDIAN_ROOT` oraya çevrildi, yedi dedektör `persist=False` ile koşuldu |
| Ölçüm kodu | `olc.py` (sha256 `b8417c4c9…`) |
| Ham çıktı | `olcum_20260804.json` (sha256 `fe25a929d…`) |
| Canlıya erişim | **YOK** (ssh yok, üretim state'ine tek bayt yazılmadı) |

**PENCERENİN DIŞINDA KALAN:** operatörün 24 saatlik alarm dağılımı (2026-08-05/06) ve
`shadow_model_fit` 2026-08-05T22:10 koşusu bu yedekte YOKTUR. Aşağıdaki hiçbir sayı o iki günü
kapsamaz ve kapsıyormuş gibi yazılmadı. İki bağımsız kaynak (operatörün canlı ölçümü ve bu yedek)
**aynı deseni** gösteriyor; bu bir teyittir, bir tekrar-sayım değil.

**İKİ DEDEKTÖRÜN YEREL KOŞUMU EKSİK ÖLÇER (beyan):** `sp500_membership` ve `fmp_source` üretkenlik
alt-kontrolleri **ağa çıkar** (`constituents.health()`, `fmp.health()`). Yerel/ağsız koşumda ikisi
de sessiz kalır ve bu koşumun `starved` listesinde görünmezler — ama **canlı mandalda ikisi de
VARDIR**. Rapor onları mandaldan sayar, bu koşumun eksikliğini "yok" diye okumaz.

---

## 2. ÖLÇÜLEN TABLO

Mandal (canlı, 2026-08-05T00:48 yazımı) **10 jeton** taşıyor; yeniden hesap (bu koşum) parity'de
**7 düşen satır** + 1 starved + 1 conservation + 1 coherence buluyor. İki liste birleşince:

```
production   : starved 1 (yerel) / 3 (canlı mandal)   · waiting 0 · askida 0 · ok 8
conservation : 400 plan · 95 işlem · 5 no_fill · 242 replay çağı → 7 AÇIKLANAMAYAN
determinism  : OK (bar mutasyonu yok)
coherence    : 1 bayat türev (scoreboard.json, 47,7 sa geride) · ok 13
monotonicity : 0 gerileme   (peak_equity vakası AFLA kapandı — §3.11)
ownership    : 0 ezilen alan
parity       : 37 satırın 7'si düşük
```

---

## 3. İHLAL-İHLAL DÖKÜM VE SINIFLANDIRMA

Sınıf sütunu üç değerlidir: **GERÇEK** (mekanizma gerçekten kusurlu/eksik) ·
**FIRTINA ARTIĞI** (bu haftanın restart/dağıtım/sermaye-reset olaylarının kalıntısı, kendiliğinden
ya da tek seferlik temizlikle kapanır) · **YANLIŞ SINIFLANDIRMA** (olgu gerçek ama dedektör onu
YANLIŞ KOVAYA koyuyor — en tehlikelisi budur, çünkü operatörü yanlış yerde arattırır).

### 3.1 `starved:llm_calibration` — **YANLIŞ SINIFLANDIRMA** (olgu gerçek, kova yanlış)

**Ölçüm:** `llm_calibration.json` → `n_pairs: 0`, `cf_pairs: 1`, `n_plans_with_opinion: 4`,
`last_opinion_plan_date: 2026-07-27`.

Dedektörün sözleşmesi (`production_report`): `n == 0 → starved` = *"HİÇ üretmemiş → **hata
şüphesi**"*. Ama burada üretim VAR: dört plan LLM görüşü taşıyor. Eksik olan **BİRLEŞTİRME
ÖRNEKLEMİ**dir — görüş damgalı planların hiçbiri henüz kapanmış bir işleme dönüşmedi (son görüşlü
plan 07-27, son kapanan işlem çok daha eski). Yani mekanizma **çalışıyor ama SAYAMIYOR**.

Bu ayrımın adı ve kovası kodda ZATEN VAR: WP-M ölçek-borcu turu `production_report`e üçüncü kovayı
(`askida`) açtı ve `gate_calibration`ı oraya bağladı (watchdog.py:252-259). **Aynı sınıftan iki
mekanizma daha var ve ikisi de hâlâ `starved` kovasında:** `llm_calibration` ve (aşağıda)
gölge-model terfi hattı.

> **ÖNERİ D1 (düşük risk, tek dosya):** `askida` kovasını genelleştir. `production_report` bir
> mekanizmayı yalnız "kaç çıktı var" diye değil, "üretti mi / eşleştirebildi mi" diye sorsun:
> üretim izi VARSA (`n_plans_with_opinion > 0`) ve birleşme 0 ise satır `askida`ya düşsün, gerekçesi
> eleme defterinden (`sieve`) yazılsın. Alarm sınıfı da değişir: askıda MECHANISM_STALE üretmez.
> **Ölçüsü:** mandaldaki `starved:llm_calibration` düşer, kartta gerekçeli bir "askıda" satırı doğar,
> ve GERÇEK bir üretim arızası olduğunda `starved` yeniden anlamlı olur.

### 3.2 Gölge-model terfi hattı — **AYNI SINIF, ayrı yüzey** (kart bunu ihlal olarak göstermiyor)

**Ölçüm:** `sieve.json` → `shadow_model.terfi: {in: 95, out: 0, drops: {piyasa:gölge_tahmini_damgalanmamış: 95}}`.

95 kapanmış işlemin **hepsi** planına birleşti; hiçbirinin planında `p_win_shadow` damgası yoktu
(damga 2026-07-21'de başladı, kapanan işlemler ondan eski). Elemenin sınıfı `piyasa:` — yani
`sieve` bunu bilinçli olarak **BİLGİ** sayıyor, hata değil (kurt-masalı yasağı, sieve.py:178-185),
ve bu DOĞRU hükümdür. Bütünlük kartında ihlal ÜRETMEZ. Rapora giriyor çünkü **operatörün gördüğü
"öğrenme durmuş" hissinin kaynağı burası** ve sınıfı §3.1 ile birebir aynı: kuraklık, arıza değil.

> **ÖNERİ D2:** ayrı bir uygulama gerekmiyor — bu turda `/api/diagnostics.ogrenme.son_fit.terfi`
> alanı bu gerekçeyi eleme defterinden okuyup panoya taşıdı (İŞ 2). Kalan iş: aynı cümlenin
> `starved:llm_calibration` satırında da görünmesi (= D1).

### 3.3 `conservation` — 7 açıklanamayan plan — **GERÇEK (küçük), sınıfı dar**

**Ölçüm:** 400 plan · 95 işlem · 5 `no_fill` · 242 replay çağı → **7 açıklanamayan**, hepsi
`verdict: REVIEW`:

```
P-2026-07-23-CSX/UNP/NSC/RTX-momentum_burst · P-2026-07-24-PKG-momentum_burst
P-2026-07-27-ROK-exhaustion_hammer · P-2026-07-31-PANW-exhaustion_hammer
```

Yedisi de **REVIEW** hükmüyle kapıda durmuş, ne işleme dönüşmüş ne de düşüşü bir OLAYLA
kaydedilmiş. Korunum dedektörünün tanımı gereği bu "sessiz kayıp"tır — ve tanım doğru: bir REVIEW
planının akıbeti (operatör baktı/bakmadı/süre doldu) hiçbir yerde yazmıyorsa o plan gerçekten
buharlaşmıştır.

**Fırtına artığı DEĞİL:** tarihler 07-23…07-31, yani bu haftanın restart penceresinden (08-03 gecesi)
ÖNCE. Restartlar bu satırları üretmedi.

> **ÖNERİ D3:** REVIEW planları için terminal-durum damgası. En ucuz hâli: gün sonu kapanışında
> silahlanmamış REVIEW planına `review_expired` olayı (plan_id + neden). Kod eklemeden önce ÖLÇÜM:
> yedi planın ortak imzası "REVIEW + hiç silahlanmadı" mı, yoksa bir kısmı silahlanıp emri mi
> düşürüldü — ikisi ayrı kök. **Bu turun kapsamı dışında** (loop/scheduler dokunuşu gerekir).

### 3.4 `stale:scoreboard.json` — 47,7 saat geride — **GERÇEK, ve kökü MİGRASYON**

**Ölçüm (arka-uçtan bağımsız `store.mtime`):**

| artefakt | son yazım |
|---|---|
| `scoreboard.json` | **2026-07-31T10:56:02Z** |
| `hypotheses.jsonl` (kaynağı) | 2026-08-02T10:36:19Z |

Fark tam 47,7 saat. **2026-07-31T10:56:02 damgası `dbmigrate --uygula` anıdır** (KOKNEDEN.md'nin
zaman çizelgesindeki ilk satır: "altı defter SQLite'a"). Yani karne, migrasyondan bu yana **bir kez
bile yeniden üretilmedi**; hipotez defteri ilerledi, karne yerinde kaldı.

Bu bulgu bağımsız bir kanıtla örtüşüyor: **nous'un 2026-W32 önerilerinin birincisi (N00001) tam
olarak karne üreticisini işaret ediyor** — *"`tavan_durumu` olculemedi, nedeni: v3 karne satırında
`backtest_full.avg_r` YOK"*. İki farklı dedektör (bütünlük tutarlılığı + nous telemetri boşluğu)
aynı mekanizmayı gösteriyor.

> **ÖNERİ D4:** karne üreticisinin kadans kancasını doğrula — "yazılıyor ama bayat" ile "hiç
> yazılmıyor" ayrı hâllerdir ve `coherence` ikisini aynı satırla anlatıyor. Ölçüm: `scoreboard`
> yazan yolun son çağrılma anını olay defterinden çıkar; yazan yol hiç koşmuyorsa bu bir
> **kablolama** kalemidir (ölü-mekanizma avı sınıfı), bayatlık değil.

### 3.5 `parity:universe_coverage` — **GERÇEK, ama KAYNAK arızası (kod değil)**

Detay: *"165 seans evren kapsaması yetersiz olduğu için ATLANDI (son: 2026-07-29 %17) — kaynak
yayınlamıyor"*. Bu, mühendislik günlüğünde adı konmuş T+1 ritim kusurunun kalıntı sayacı; kod
tarafı (same-evening bacağı + merdiven + onarım geçidi) zaten sevk edildi. Sayaç **kümülatiftir**:
geçmişte atlanan 165 seansı sonsuza dek taşır ve bugün akış düzelse bile kırmızı kalır.

> **ÖNERİ D5:** kümülatif sayacın yanına **pencere** ekle ("son 20 seansın kaçı atlandı"). Kalıcı
> kırmızı, kurt masalının ta kendisidir: operatör satırı yok saymayı öğrenir, sonra GERÇEK bir
> kapsama çöküşü de görünmez olur (`sieve`in kendi gerekçesiyle birebir aynı ilke).

### 3.6 `parity:yeniden_hesap:orphan_state_files` — 7 dosya — **FIRTINA ARTIĞI (6/7)**

Tam liste (bu koşumdan):

| dosya | sınıf |
|---|---|
| `bounds.yaml.bak-202608021652` | 2026-08-02 16:52 bakım penceresi artığı |
| `goal.yaml.bak-202608021652` | aynı pencere |
| `goal.yaml.bak-202608030421` | 2026-08-03 04:21 penceresi (sprint turu) |
| `goal.yaml.bak-202608031627` | 2026-08-03 16:27 penceresi (E1 kararı) |
| `earnings.csv.20260803T100416Z.bak` | 2026-08-03 10:04 dağıtımı |
| `earnings.csv.sedbak` | sed yedeği (tarihsiz) |
| `auth.json` | **GERÇEK DEĞİL — dedektörün kör noktası** |

**Altısı doğrudan bu haftanın dağıtım pencerelerinin damgasını taşıyor** (günlükteki 08-02 16:52,
08-03 04:21/10:03/16:27 dagit kayıtlarıyla birebir). Bunlar üretim artığıdır; bir sonraki temizlikte
düşerler ve o zamana dek kartı kalabalıklaştırırlar.

`auth.json` ayrı bir haldir: pano kimlik dosyasıdır, okuyucusu `auth.py`/`api.py`'dir ve
**statik graf onu göremiyor** (`finviz_universe.json` vakasıyla aynı sınıf: modül-içi/dolaylı okuma).

> **ÖNERİ D6 (iki bacaklı):** (1) yedek dosyaları dedektörün desen listesinden ÇIKARMA — bunun
> yerine bakım penceresi betiklerine "pencere kapanışında `*.bak-*`/`*.sedbak` temizliği" adımı
> ekle; artığın kaynağı temizlenirse dedektör kendiliğinden susar ve **bekçi zayıflatılmamış olur**.
> (2) `auth.json` için: ya `codelaw.DECLARED_SINKS`e gerekçeli beyan, ya da gerçek okuyucunun statik
> olarak görünür hâle getirilmesi. Beyan tercih edilirse gerekçe "hangi modül nasıl okuyor"u
> YAZMALI (boş beyan, `learning_loop_open.json` vakasında eksik tüketiciyi örtmüştü).

### 3.7 – 3.8 `parity:eleme:component_ic.eslesme` + `threshold_curve.eslesme` — **GERÇEK, TEK KÖK**

**Ölçüm:** ikisi de birebir aynı: `in: 2216 · out: 2209 · drops: {sema:bar_yok:tarih: 7}`.

`sema:` sınıfı **yazılım hatası** demektir (piyasa filtresi değil): yedi kanıt satırı, karşılık
gelen barın tarihi bulunamadığı için iki türetilmiş ölçümden birden sessizce düşüyor. İki ihlal
**tek kök**tür: aynı 7 satır, aynı eşleştirme adımı, iki tüketici.

Oran küçük (%0,32) ama sınıfı büyük: bu, günlükteki **HAYALET SEANS / takvim doğrulaması yok**
ailesinin imzasıyla aynı ("bar yok / tarih eşleşmiyor").

> **ÖNERİ D7:** yedi satırın tarihlerini çıkar ve hayalet-seans karantinasıyla (2025-05-26,
> 2018-11-22 sınıfı) kesiştir. Kesişiyorsa kalem o turun kuyruğuna girer; kesişmiyorsa yeni bir
> takvim boşluğu bulunmuş demektir. **Ölçüm ucuz** (eleme defteri satır kimliklerini taşımıyor →
> `sieve.Sieve` çağrısına örnek tarih listesi eklemek gerekir; küçük, ayrı kalem).

### 3.9 `parity:brain_chain_distinct` — **GERÇEK ve ZATEN BEYANLI**

*"`[gemini, nous]` AYNI model kimliğiyle çağrılıyor (gemini-3.5-flash) — zincirin yedekli olduğu
ÖLÇÜLMEMİŞTİR."* Bu, hafızadaki "beyin zinciri ölçümü" bulgusunun canlı sayacı: üç beyin bir sayım
değil bir varsayımdı. **Operatör kalemi** (Claude anahtarı ya da farklı `NOUS_MODEL`), kod kalemi
değil. Kartta kalması DOĞRU.

### 3.10 `parity:alarm_delivery` + `parity:notify_channel` — **GERÇEK, ve İŞ 1'İN TAM SEBEBİ**

**Ölçüm:** *"13 alarm TESLİM EDİLEMEDİ (BROKER_REJECT×4, DATA_QUALITY×3, **MECHANISM_STALE×136**,
ROLLBACK×1) — bildirim kanalı yapılandırılmamış"*.

Defterin tamamındaki alarm dağılımı (2026-07-14 → 08-04):

| jeton | n |
|---|---|
| MECHANISM_STALE | **161** |
| DATA_QUALITY | 4 |
| BROKER_REJECT | 4 |
| ROLLBACK | 1 |

MECHANISM_STALE'in mekanizmaya göre dağılımı: **`hermes_poll` 110** · parity 12 · server_process 10 ·
warmup_sprint 10 · coherence 9 · conservation 2 · diğer 8.

`hermes_poll` alarmlarının **gap dağılımı** (pencere 0,5 sa):

| gap (sa) | n |
|---|---|
| **0,5** | 68 |
| **0,6** | 27 |
| **0,7** | 4 |
| 1,1–9,3 | 11 |

**%90'ı pencere sınırının 0,0-0,2 saat ötesinde.** Bu bir mekanizma ölümü değil, ders kitabı
**çırpınmadır** (flapping): nabız pencerede salınıyor, mandal her toparlanışta düşüyor, her yeniden
aşımda yeni alarm yazılıyor. Günlük dağılım da bunu doğruluyor — 07-28'den 08-04'e kadar HER GÜN
5-10 `hermes_poll` alarmı, kesintisiz.

Üstelik salınımın **nedeni kayıtlı**: canlı `brain_cooldown.json` →
`{"agent": {"seconds": 21600, "streak": 13, "reason": "pool_exhausted:gemini",
"since": "2026-08-04T19:38:54Z"}}`. Yani hermes ipliği **kota soğumasında beklemeye alınmıştı** ve
bekçi bu meşru hâli "gecikti" diye alarmlıyordu.

> **BU KALEM BU TURDA KAPANDI (İŞ 1, v192):** (a) `hermes_poll` bayatlığı, hermes soğuma/havuz
> kaydı canlıyken `askida` kovasına düşer ve **alarm basılmaz**; (b) mekanizma başına **günlük
> alarm tavanı 1** (histerezis korunur; bastırma `watchdog_alarm_gunluk.json`da SAYILIR ve panoda
> görünür). Beklenen etki, bu tablonun kendi sayılarıyla: `hermes_poll` 5-10/gün → **≤1/gün** (soğuma
> sürerken 0), `warmup_sprint` 1/gün → ≤1/gün. Toplam MECHANISM_STALE günlük hacmi **~7-12 → ~1-3**,
> yani ROADMAP WP-P'nin EEMUA-191 ≤10/gün bütçesinin içine iner.
>
> **KALAN AÇIK KALEM (operatör):** `notify_channel`. Teslim edilemeyen 13 alarmın kökü hijyen değil
> **kanalın hiç kurulmamış olmasıdır**; hijyen o 13'ün büyümesini durdurur, kanalı kurmaz.

### 3.11 Sermaye-reset vakasının artıkları — **KAPANMIŞ (kanıtlı)**

KOKNEDEN.md'nin (8f68d0b) 2026-08-04T01:16'da ateşlenen üç MAKULLÜK ihlali bu koşumda **ÜÇÜ DE
YEŞİL**:

```
yeniden_hesap:realized_pnl        ✓ broker -5.542,09$ · defter -5.542,09$
yeniden_hesap:cash_identity       ✓ nakit 94.457,91$ · kimlik 94.457,91$
yeniden_hesap:equity_curve_tail   ✓ eğri sonu 94.457,91$ · kitap nakdi 94.457,91$
```

Üçü mandalda da YOK. `monotonicity` gerilemesi de kapalı: `peak_equity 102.520,45 → 100.000,00`
küçülmesi **yazılı afla** kapatılmış (`monotonic_amnesty.json`, gerekçe: `SR-20260801T151429`
sermaye tohum ayrıştırması). Yani **R1 iadesi işledi ve dedektörler bunu ölçtü.**

> Bu, kartın kalabalığının bir kısmının GEÇİCİ olduğunun kanıtıdır: fırtına geçince ilgili satırlar
> kendiliğinden düştü. Kalan 10 jeton fırtınadan ÖNCE de oradaydı.

---

## 4. ÖZET SINIFLANDIRMA

| # | jeton | dedektör | sınıf | öneri |
|---|---|---|---|---|
| 1 | `starved:llm_calibration` | üretkenlik | **YANLIŞ SINIFLANDIRMA** (kuraklık) | D1 |
| 2 | `starved:fmp_source` | üretkenlik | GERÇEK (kaynak) — canlı mandalda, yerel koşumda ölçülemedi | — |
| 3 | `starved:sp500_membership` | üretkenlik | GERÇEK (kaynak) — aynı beyan | — |
| 4 | `conservation` (7 plan) | korunum | **GERÇEK** (fırtına öncesi) | D3 |
| 5 | `stale:scoreboard.json` | tutarlılık | **GERÇEK** — kök: migrasyondan beri üretilmedi | D4 |
| 6 | `parity:universe_coverage` | makullük | GERÇEK (kaynak) + **kümülatif sayaç kusuru** | D5 |
| 7 | `parity:yeniden_hesap:orphan_state_files` | makullük | **FIRTINA ARTIĞI** 6/7 + 1 kör nokta | D6 |
| 8 | `parity:eleme:component_ic.eslesme` | makullük | **GERÇEK** (7 satır, `sema:bar_yok:tarih`) | D7 |
| 9 | `parity:eleme:threshold_curve.eslesme` | makullük | **GERÇEK** — 8 ile TEK KÖK | D7 |
| 10 | `parity:brain_chain_distinct` | makullük | GERÇEK, **operatör kalemi** | — |
| 11 | `parity:alarm_delivery` | makullük | **GERÇEK** — %85'i çırpınma | **İŞ 1'de kapandı** |
| 12 | `parity:notify_channel` | makullük | GERÇEK, **operatör kalemi** | — |
| — | 3× `yeniden_hesap` kimliği | makullük | **KAPANDI** (R1 iadesi) | — |
| — | `monotonicity:peak_equity` | monotonluk | **KAPANDI** (yazılı af) | — |

**Sayım:** 12 açık jetonun **1'i yanlış sınıflandırma**, **1'i fırtına artığı (6 dosyalık)**,
**3'ü operatör/kaynak kalemi**, **5'i gerçek mühendislik kalemi**, **1'i bu turda kapandı**,
**1'i kısmen kapandı** (`alarm_delivery`in hacmi düştü, kanalın yokluğu sürüyor).

---

## 5. NE YAPILMADI (ve neden)

- **Hiçbir dedektör susturulmadı.** Kalabalık kartın çözümü eşik gevşetmek değil, satırların
  SINIFINI doğru söylemektir (D1/D5'in ortak ilkesi).
- **`state/integrity_report.json` ÜRETİLMEDİ.** Panelin dosyaya değil taze ölçüme bakması bilinçli
  bir tasarımdır ve gerekçesi kaynakta yazılıdır; "dosya boş" şikâyetinin doğru cevabı dosyayı
  yaratmak değil, o dosyanın hiç var olmadığını söylemektir.
- **D1-D7 UYGULANMADI.** Bu turun mandası döküm + sınıflandırma + öneriydi; uygulama Rol-1'in ayrı
  turudur. D3 ve D7 zaten `loop.py`/ölçüm katmanı dokunuşu ister ve bu turun yazma sınırlarının
  dışındadır.

---

## 6. TEKRAR ÜRETİM

```bash
mkdir -p /tmp/bd && tar -xzf backups/a1/state-2026-08-04.tar.gz -C /tmp/bd
MERIDIAN_ROOT=/tmp/bd .venv/bin/python research/olcumler/butunluk_dokumu_2026-08-06/olc.py \
  > /tmp/bd/olcum.json
diff <(jq -S . /tmp/bd/olcum.json | grep -v olcum_ts | grep -v kaynak) \
     <(jq -S . research/olcumler/butunluk_dokumu_2026-08-06/olcum_20260804.json | grep -v olcum_ts | grep -v kaynak)
```

Kanıt damgaları (sha256):

```
olc.py                        b8417c4c9bee9ad70889dbe3da2c7e299a524ccdea2f3ee6b55c4e8e34887809
olcum_20260804.json           fe25a929defa9a87501e855ca813608a2eceb756dde3aa0685bbd0a4b5c98237
state-2026-08-04.tar.gz       cc789063ac7ebb1ea150edfd4ceaa9a727e4626ac1dd73a3fd22be42a7b31325
```
