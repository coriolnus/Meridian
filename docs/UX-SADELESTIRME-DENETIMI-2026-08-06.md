# UX SADELEŞTİRME DENETİMİ — 2026-08-06

**Rol:** kıdemli UX denetçisi (salt-analiz turu). **Kod yazılmadı, git koşulmadı, canlıya dokunulmadı.**
**Yer-gerçeği:** `meridian/web/app.js` (7.355 satır), `meridian/web/index.html` (1.573 satır),
`meridian/web/palette.js` (1.043 satır), `meridian/api.py`, `meridian/analytics.py`,
`ROADMAP.md` §WP-P, `research/olcumler/butunluk_dokumu_2026-08-06/RAPOR.md`, `tests/test_s2r*`.

**Bu belge bir HÜKÜM değil bir TEŞHİStir.** Her bulgu koddaki somut bir öğeye (dosya:satır, sınıf
adı, fonksiyon adı) işaret eder. Ölçülemeyen hiçbir iddia yok; tahmin edilen her yerde "tahmin"
yazıyor. Uygulama ayrı tur.

---

## 0. ÖNCE ÜÇ YANLIŞ VARSAYIM ÇÜRÜTÜLÜYOR

Denetime "şunlar bozuktur" diye başlanan üç şey ölçüldü ve **bozuk değil**. Yazıya geçiyorlar ki
bir sonraki tur onları yeniden "sadeleştirmeye" kalkmasın.

**(a) Bölüm parçaları iki sayfada TEKRARLANMIYOR.** `opParcalar()` ve `intraParcalar()` iki AYRI
`s1…s6` ad uzayı taşıyor. `veriboru` (opParcalar `s4`) ile `intraday` (intraParcalar `s4`) aynı
sayfada duruyor ama **farklı kartlardır** (`Bölüm 4 · Veri hattı` vs `Dayanıklı tetik`). Aynısı
`portfoy` sayfasındaki `mutabakat` (op `s1`) ile `intraemir` (intra `s1`) için de geçerli.
Duplikasyon **yok**.

**(b) Alarm seli sunum katmanında zaten toplanmış.** `/api/alerts` satır değil **grup** döndürüyor
(`a.groups`, `g.n` çarpanıyla) ve `alertsInbox()` (app.js:1047) `×N` rozetiyle çiziyor. 129/24s'lik
şikâyetin bir kısmı **üretim hızıdır, liste uzunluğu değil.** v192'nin `askida` kovası da depoda
(`watchdog.py:158-206`, `api.py:1920-1930`) — sunucu tarafı hazır.

**(c) Yedi-sayfa ADR'ı bir duvar değil.** Test çivileri sayfa yapısını **yasaklamıyor**, iki listenin
sessizce ayrışmasını yasaklıyor. Ölçüldü: sayfa yapısına bağlı test fonksiyonu **23 adet / 6 dosya**
(§7.3). Değişim maliyeti gerçek ama sınırlı ve hepsi **gürültülü** düşer — sessiz kırılma yok.

---

## 1. TEŞHİS

### 1.1 Envanter (koddan sayıldı)

| Sayfa (`VIEWS`) | Bölüm (`ALAN_BOLUMLERI`) | Ölçülen kart | Not |
|---|---|---|---|
| Genel Bakış | — (bölümsüz) | 6 `.gb-kart` + 1 `.gb-alarm` şeridi | bütçe **çivili** (`GENEL_KARTLARI`, test sayıyor) |
| Veri Sağlığı | 3 (`market`,`intraday`,`veriboru`) | 8 kart + 1 detay katmanı + evren tablosu (canlıda 251 sembol) | — |
| Koşu & Döngü | 2 (`adaylar`,`kapilar`) | 4 `.durum-kart` + 4 kart + 2 `.pane` + 2 detay katmanı | — |
| Portföy & Emirler | 5 (`brifing`,`onaylar`,`mutabakat`,`intraemir`,`performans`) | 4 `.durum-kart` + 13 kart | — |
| **Öğrenme** | **7** (`karne`,`golge`,`bilesenic`,`hermes`,`ajan`,`skiller`,`hafiza`) | **39 kart** | bütçe **yok** |
| **Gözetim & Alarmlar** | **1** (`operasyon`) | **3 kart** | bütçe yok |
| Kilitler & Yapılandırma | 2 (`mudahale`,`ayarlar`) | 5 kart + 1 detay katmanı | — |

**Ölçülen asimetri: Öğrenme sayfası Gözetim sayfasının 13 KATI kart taşıyor.** Operatörün en sık
girdiği triyaj yüzeyi 3 kart, en seyrek girdiği öğrenme yüzeyi 39 kart. Genel Bakış'ın (6) ve durum
ızgarasının (4) yazılı kart bütçesi var; **beş alan sayfasının hiçbirinin yok** — yani "ekrana dök"
yasağının ölçülebilir bir kapısı yalnız iki yüzeyde mevcut.

### 1.2 Nielsen 10-sezgisel denetimi

Ciddiyet: **4 = felaket** (görevi bitiremez / sessizce yanlış yaptırır) · **3 = ciddi** ·
**2 = küçük** · **1 = kozmetik**.

| # | Sezgisel | Bulgu — SOMUT öğe | Cid. |
|---|---|---|---|
| B1 | #1 Sistem durumunun görünürlüğü · YASA 4 | **`#alp-msg` DİYE BİR ÖĞE YOK.** `alpacaSubmit` (app.js:6967) ve `alpacaClose` (app.js:6974) her geri-bildirim satırını `const m = $("alp-msg"); if (m) …` ile koruyor; `id="alp-msg"` ne app.js'te ne index.html'de üretiliyor (grep: 0 eşleşme; kardeşleri `#intraday-arm-msg`, `#fsub-msg`, `#alerts-ack-msg`, `#plan-onay-msg` VAR). Sonuç: "Silahlı planları Alpaca'ya gönder" düğmesi **"gönderiliyor…" de yazmıyor, "N emir gönderildi" de, hatayı da.** Yalnız `RENDER.ayarlar()` yeniden çiziyor (~1,4 sn, dış Alpaca çağrısı). **AMGN "onay→gönderim kopukluğu" vakasının mekanik açıklaması budur.** | **4** |
| B2 | #1 Görünürlük · uydurma yasağı | Genel Bakış → "Bugün ne var" kartı (app.js:1416-1421) `t.inbox_count` okuyor. `_inbox_count()` (api.py:3172) yalnız **arming + skill_revision + skill_rec** sayıyor — **REVIEW planları HİÇ girmiyor.** Onayını bekleyen 3 REVIEW planı varken kart aynen şunu yazıyor: **"0 bekleyen onay — senden bir şey beklenmiyor."** Ölçülmüş bir gerçeğin yanlış olumsuzlanması; None≠0 yasasının ihlal edilmediği ama 0≠"yok" yasasının ihlal edildiği yer. | **4** |
| B3 | #5 Hata önleme · #4 Tutarlılık | `alpacaClose` (Ayarlar → Alpaca kartı, app.js:6883) **Kademe 3 · FLATTEN ile AYNI ucu** çağırıyor (`/api/alpaca/close_all?confirm=FLATTEN-PAPER`) ama **tek `confirm()`** ile; `opFlatten` (app.js:2450) **çift onay** istiyor. Üstelik Müdahale paneli ekranda şunu yazıyor: *"üçü de aynı gövdeyi çağırır, ikinci bir yetki yolu yoktur"* (app.js:2478) — **dördüncü yüzey var ve kapısı zayıf.** | **4** |
| B4 | #2 Sistem–gerçek dünya eşleşmesi | `onaylar` bölümünün soru cümlesi: *"şu an benim onayımı bekleyen ne var?"* (`EKRAN_SORUSU.onaylar`). Ama `RENDER.onaylar` (app.js:6313) `/api/approvals` gelen kutusunu çiziyor ve **REVIEW planları o kutuda yok**; REVIEW onayı `planOnayBloguHTML` ile **Koşu & Döngü → `adaylar` → satır çekmecesinin İÇİNDE** yaşıyor. Bölüm kendi sorusunu cevaplamıyor. | 3 |
| B5 | #1 Görünürlük · #7 Verimlilik | Onay başarı mesajı (app.js:1999): *"aynaya göndermek için **Ayarlar'daki** 'Silahlı planları Alpaca'ya gönder'"*. Üç kusur birden: (a) "Ayarlar" **bir sayfa adı değil** — sayfanın adı "Kilitler & Yapılandırma", "ayarlar" onun 2. bölümü; (b) **bağ yok**, düz metin; (c) mesaj çekmece kapanınca **kayboluyor** (çekmece `recReset`/`closeDrawer` ile temizleniyor). | 3 |
| B6 | #1 Görünürlük · YASA 6 | `api._sessiz_hat` bekçi segmentine `askida` ve `n_askida` **yazıyor** (api.py:1928-1930) ama `sessizHat()` (app.js:2360) **yalnız `sapmalar`/`n_sapma` okuyor** — `askida` hiç çizilmiyor. Şerit "15/17" gösterir, eksik 2'nin nedeni **yalnız HUD çipinin `title` ipucundadır** (app.js:2267): hover-only, klavyeyle erişilemez. Üretilen alanın okuyucusu yok = YASA 6. | 3 |
| B7 | #8 Estetik ve minimalist tasarım | **Aynı sağlık gerçeği üç bileşende:** *bekçi* → HUD çipi (app.js:2268) **+** sessiz-hat "bekçiler" segmenti. *nabız/tazelik* → `#statuspill` **+** sessiz-hat "tazelik" segmenti **+** kenar şeridi `subs.genel`. *WS akışı* → HUD çipi **+** ③ EMİRLER durum kartı **+** `spineHTML`. P1'in Level-1 toplaması **kuruldu ama eski yüzeyler emekli edilmedi** — toplamanın alarm-yorgunluğuna karşı tek yapısal savunma olması gerekirken 3 kopya kaldı. | 3 |
| B8 | #6 Tanıma > hatırlama | **Triyaj şeridi (`spineHTML`, app.js:879) Genel Bakış'ta YOK.** Panonun tek "senden şunu bekliyor + doğrudan bölüm çapasına götüren çip" yüzeyi (12 farklı durum, hepsi `sayfa#bolum` adresli) yalnız Portföy sayfasının 1. bölümünde (`RENDER.brifing`, app.js:1891) çiziliyor. 10-saniyelik sabah bakışı onu **görmüyor**. Kod bunu bilinçli diye yazıyor (ADR "BAŞKA HİÇBİR ŞEY") — ama telafi olarak koyulan "Bugün ne var" kartı B2 yüzünden yanlış sayıyor. | 3 |
| B9 | #2 Eşleşme · ölü kol | `spineHTML` satır 900: `if ((t.pending_count \|\| 0) > 0 && t.autonomy_level >= 1) acts.push([`${t.pending_count} onay bekliyor`, …])`. İki kusur: (a) `pending_count` = **o seansta kurulan GO+REVIEW plan sayısı** (`analytics.py:216-221`) ve kodun kendi yorumu (app.js:673) *"kimseden bir şey istemez"* diyor — çip yine de "onay bekliyor" yazıyor; (b) sistem **L0**'da, yani `autonomy_level >= 1` kapısı **hiç ateşlemiyor** → satır ölü. | 3 |
| B10 | #8 Minimalizm · bilişsel yük | **Öğrenme sayfası: 39 kart, 7 bölüm, tek kaydırma sütunu.** (`karne` 12 · `hermes` 9 · `bilesenic` 7 · `golge` 4 · `skiller` 4 · `ajan` 2 · `hafiza` 1). Sayfanın hiçbir kart bütçesi yok; Genel Bakış'ın 6'lık ve durum ızgarasının 4'lük bütçeleri **teste çivili**, alan sayfalarınınki **yazılmamış**. | 3 |
| B11 | #8 Minimalizm · progressive disclosure | **`Bölüm 5 · Bütünlük dedektörleri` TEK kartta 5 alt-başlık taşıyor** (app.js:4878): 7 desen satırı + "Makullük ihlalleri" + "Defter sözleşmesi" + "Yazar ihlalleri" + "Eleme muhasebesi" + kapsama satırı. Hepsi aynı görsel ağırlıkta, kademe yok. Operatörün *"bütünlük dedektörleri kartında çok ihlal gösteriyor"* şikâyetinin **sunum kökü budur** — ölçüm raporu (`RAPOR.md` §2) 7 düşen satır + 1 starved + 1 conservation + 1 coherence buluyor, yani sayı doğru; **hiyerarşi yok.** | 3 |
| B12 | #7 Verimlilik | **Tek triyaj iki sayfaya yayılmış:** bütünlük ihlalleri **Veri Sağlığı → `veriboru`**'da, onların alarmları **Gözetim & Alarmlar → `operasyon`**'da. "Bir alarm çaldı → hangi ihlal → hangi veri" zinciri sayfa değiştirmeden yürünemiyor. | 3 |
| B13 | #3 Kullanıcı kontrolü | `go()` (app.js:489) her geçişte koşulsuz `scrollTo({top:0})`; **kaydırma konumu hiçbir yerde saklanmıyor.** 39 kartlık Öğrenme sayfasında bir karta bakıp başka sayfaya gidip dönmek = **baştan arama**. | 3 |
| B14 | #10 Yardım ve belgeler | Runbook bağı (`runbookHref`, app.js:2352) `/runbook#<ad>` — **ayrı, tam sayfa bir belge.** Alarmdan teşhise giden yol **panoyu terk ediyor**; tarayıcı geri tuşuyla dönüşte `go()` yine `scrollTo(0)` yapıyor. Zincirin son halkası bir bağlam anahtarı. | 3 |
| B15 | #3 Kullanıcı kontrolü · #6 Tanıma | **Tema dışında SIFIR UI durumu kalıcı.** `localStorage` yalnız `meridian_api`/`meridian_token` (app.js:137-140) ve `meridian-tema` (theme.js) için kullanılıyor. 7 `<details>` (detay katmanı + 4 yerli) her yeniden çizimde **kapalıya dönüyor**; `sessionStorage` hiç kullanılmıyor. | 2 |
| B16 | Hick–Hyman | ⌘K paletinde **29 gezinme komutu tek "Gezinme" grubunda** (7 ray + 20 `BOLUMLER` + `failsub` + yedek). Boş sorguda liste 45+ satır; grup sırası (`GRUP_SIRA`, palette.js:130) 6 grup ama ilk grup tek başına listenin üçte ikisi. | 2 |
| B17 | #7 Verimlilik | Alarm gelen kutusunda **tek toplu eylem** var: "Tümünü okundu işaretle" (`ackAlerts`). Satır bazında **ertele / sustur / sahiplen yok** → 129/24s'lik günde triyaj "ya hepsi ya hiçbiri". | 2 |
| B18 | #4 Tutarlılık | Aynı gerçek iki dilde: `nextSessionCard` ayna sütunu **rozetle** anlatıyor (`aynada` / `gönderilecek` / `RET`), ③ EMİRLER durum kartı aynı gerçeği **oran çubuğuyla** (`silahlı → gönderilmiş → dolan`, payda beyanlı). İkisi de Portföy sayfasında, aralarında 1 bölüm var. | 2 |
| B19 | #4 Tutarlılık | **Üç kart-benzeri yüzey, iki tıklama sözleşmesi:** `.gb-kart` tıklanamaz (bağ ayrı düğme), `.durum-kart` tıklanabilir (çekmece açar), `.trow.rowbtn` tıklanabilir (çekmece açar). Gerekçe kodda yazılı (index.html:651-654) ama **ekranda hiçbir işaret yok** — üçü de aynı `--card`/`--line-2`/`--r-card` reçetesinden. | 2 |
| B20 | #6 Tanıma > hatırlama | **Klavye yüzeyi 7 ayrı kip:** `1-7`, `g`+harf, `j/k`, `r`, `?`, `⌘K`, `Esc`. `?` haritası var (`kbdOverlay`) ama **keşfi yalnız `?` tuşuna bağlı**; ekranda hiçbir kalıcı ipucu yok (sidebar ray düğmelerinde rakam gösterilmiyor). | 2 |
| B21 | Taranabilirlik | **Hiçbir kart başlığında ikon yok.** `.gb-kart`, `.durum-kart` ve `.card` başlıkları düz metin (`<h2 class="t">`); tarama hızı tek kanala (tipografi) bağlı. 39 kartlık sayfada bu ölçülebilir bir maliyettir. | 2 |
| B22 | #4 Tutarlılık | **"Bölüm 1…6" numaralı başlıklar artık yalan bir sıra vaat ediyor.** `opParcalar` mirası olan numaralar S2R-2'de **dört ayrı sayfaya dağıldı**: "Bölüm 5 · Bütünlük dedektörleri" bugün Veri Sağlığı'nın 3. bölümünün 2. kartı; "Bölüm 2 · Risk & rejim kapıları" Koşu & Döngü'nün 2. bölümünün tek kartı. Numara bir konum iddiasıdır ve o konum yok. | 1 |
| B23 | #8 Minimalizm | `gbAlarmSatiri` (app.js:1492) ve `alarmButce` (app.js:2394) **aynı veriyi iki farklı bileşen dilinde** yazıyor (`.gb-alarm` şeridi vs `.alarmbutce` kutusu). İkisi ayrı sayfalarda ama aynı jetonları farklı reçetelerle kullanıyor. | 1 |

**Dağılım: 3 × ciddiyet-4 · 11 × ciddiyet-3 · 7 × ciddiyet-2 · 2 × ciddiyet-1.**

### 1.3 Bilişsel-yük envanteri

**(a) Gereksiz seçenek.** Yıkıcı eylemin **iki** yolu var (B3). Aynaya gönderimin **iki** yeri yok —
**bir** yeri var ve o yer görev akışının dışında (B5). ⌘K'da 29 gezinme komutu, kenar şeridinde 7,
`g`-öneki ile 7 → **aynı hedefe üç yol, üçü de tam liste** (B16).

**(b) Tekrar.** Bekçi ×2, nabız ×3, WS ×3 (B7). Ayna durumu ×2 (B18). Alarm bütçesi ×2 dil (B23).
Ölçülen tekrar: **10-saniyelik açılış ekranında 6 bağımsız sağlık okuma bölgesi** (HUD 6 çip ·
`#statuspill` · sessiz-hat 3 segment · `.gb-alarm` şeridi · kenar şeridi alt satırı · "Dün gece"
kartının veri-kapısı uyarısı) + 6 `.gb-kart` = **12 okuma bölgesi.**

**(c) Tutarsız desen.** Kart tıklama sözleşmesi (B19) · numaralı vs adlı başlık (B22) · çekmecede
onay adımı düğmenin kendisinde, ⌘K'da ayrı satırda, müdahalede `confirm()` diyaloğunda → **üç
farklı onay dili** (`_planOnayStil` satır-içi amber · `palette.onayIste` · tarayıcı `confirm()`).

**(d) Derin hiyerarşi.** En derin yol: **sayfa → bölüm → kart → alt-başlık → tablo satırı →
çekmece → çekmece alt-başlığı**. Somut örnek: Veri Sağlığı → `veriboru` → `Bölüm 5` →
"Eleme muhasebesi" → aşama satırı. **6 kademe**, hiçbiri katlanabilir değil.

### 1.4 ÜÇ TOP-TASK — MEVCUT ADIM SAYIMI (koddan yürüyerek)

Sayım kuralı: **tık** = fare/klavye ile bir kontrol tetikleme · **kaydırma** = bir ekran boyu
(~800px) hareket · **sayfa** = `.page` değişimi.

---

#### TASK ① — "sağlıklı mı / dün gece ne oldu" 10-sn kontrolü

| # | Adım | Maliyet |
|---|---|---|
| 1 | Pano açılır → `VARSAYILAN_ROTA = "genel"` | 0 tık |
| 2 | Sessiz hat (üstte, sabit) · HUD (6 çip) · statuspill okunur | — |
| 3 | "Dün gece" kartı: tarih · aday·plan·silahlı · yaş · rejim · veri kapısı | — |
| 4 | "Bugün ne var" kartı: silahlı emir + bekleyen onay | — |

**MEVCUT: 0 tık · 0 kaydırma · 1 sayfa — ama 12 okuma bölgesi ve REVIEW körlüğü (B2).**
Görev **mekanik olarak** hızlı, **bilişsel olarak** pahalı ve **bir soruya yanlış cevap veriyor.**

---

#### TASK ② — REVIEW planı incele → onayla → arm → GÖNDERİLDİĞİNİ gör

| # | Adım | Maliyet | Kanıt |
|---|---|---|---|
| 1 | Genel Bakış'ta sinyal yok → operatör alışkanlıkla Koşu'ya gider | **1 tık** | B2 |
| 2 | `kosu`: durum ızgarası (4 kart) → `adaylar` başlığı → soru cümlesi → LLM görüşü kartı → "Bir sonraki açılış için" → özet şeridi (4 hücre) → `gateLegend` → tablo | **~2 kaydırma** | `RENDER.adaylar` |
| 3 | REVIEW satırını bul (GO'lar önce sıralı: `_VORDER`) → tıkla | **1 tık** | `planRowFull` |
| 4 | Çekmece: `pd-stats` (3) → onay bloğu | **~1 kaydırma** | `RECORD_VIEW.plan` |
| 5 | "Onayla ve Arm Et" (niyet) | **1 tık** | `planOnayla` |
| 6 | Tekrar bas — 8 sn penceresi (karar) | **1 tık** | `_PLAN_ONAY_ZAMAN` |
| 7 | Başarı mesajını oku, Esc ile çekmeceyi kapat | **1 tuş** | mesaj burada **kaybolur** |
| 8 | Kilitler & Yapılandırma'ya git | **1 tık** | B5 |
| 9 | `mudahale` (4 kol) + `ayarlar` başlık + sır kartları geçilir, Alpaca kartına inilir | **~3 kaydırma** | `RENDER.ayarlar` |
| 10 | "Silahlı planları Alpaca'ya gönder" | **1 tık** | app.js:6883 |
| 11 | **HİÇBİR GERİ BİLDİRİM YOK** — doğrulamak için Portföy'e gidilir | **1 tık** | **B1** |
| 12 | ③ EMİRLER · ayna kartındaki huni okunur (`silahlı → gönderilmiş → dolan`) | **0-1 kaydırma** | `_durumEmirKarti` |

**MEVCUT: 8 tık + 1 tuş + ~7 kaydırma · 3 sayfa · 2 bölüm · 1 çekmece.**
Ve kritik son bacak (adım 8-10) **yalnız geçici bir çekmece mesajından** öğrenilebiliyor.

---

#### TASK ③ — alarm / ihlal triyajı

| # | Adım | Maliyet | Kanıt |
|---|---|---|---|
| 1 | Sessiz hat "sap" hâline geçer; ≤4 sapma satırı açılır. **Gözetim'e giden bağ YOK** — satırdaki tek bağ `runbook ↗` | 0 tık | `sessizHat` |
| 2 | Gözetim & Alarmlar'a git | **1 tık** | — |
| 3 | Sayfa: alarm bütçesi → "Alarm gelen kutusu" (async, "yükleniyor…") → `sOgr` → "Olay akışı · son 8" | **~1 kaydırma** | `RENDER.operasyon` |
| 4 | Alarm satırına tıkla → çekmece (ham kayıt) | **1 tık** | `alertsInbox` |
| 5 | `runbook ↗` → **pano terk edilir** | **1 tık** | B14 |
| 6 | Tarayıcı geri → `go()` `scrollTo(0)`, konum kaybı | **1 tık** | B13 |
| 7 | İhlal bir bütünlük deseni ise: Veri Sağlığı'na git | **1 tık** | B12 |
| 8 | `market` (251-satırlık evren tablosu) + `intraday` (2 kart) geçilir, `Bölüm 5`e inilir | **~4 kaydırma** | `RENDER.veriboru` |
| 9 | Tek kartta 5 alt-başlık, ~30+ satır, kademe yok | — | **B11** |

**MEVCUT: 6 tık + ~5 kaydırma · 3 sayfa + 1 harici belge · kaydırma konumu 2 kez sıfırlanır.**

---

## 2. STRATEJİ — dört kaldıraç

Her öneri **tek** kaldıraçla etiketli ve çözdüğü problem **tek cümle**.

| Kod | Kaldıraç | Öneri | Çözdüğü problem (tek cümle) |
|---|---|---|---|
| **Ö1** | **Yer-değiştir** | `#alp-msg` kabını Alpaca kartının düğme sırasının altına koy (mevcut `#intraday-arm-msg` deseninin birebir kopyası) | Aynaya gönderim düğmesi bugün **hiçbir** geri bildirim üretmiyor. |
| **Ö2** | **Yer-değiştir** | "Aynaya gönder" düğmesini onay çekmecesinin **içine**, onay başarısının hemen altına ikinci bir iki-adımlı düğme olarak taşı (uç aynı: `/api/alpaca/submit_armed`) | Onay ile gönderim arasında iki sayfa ve bir hafıza sıçraması var. |
| **Ö3** | **Kaldır** | `alpacaClose` düğmesini Ayarlar'dan kaldır; Kademe 3 · FLATTEN'a yönlendiren **bir bağ** bırak | Aynı yıkıcı ucun ikinci ve daha zayıf kapılı yolu var. |
| **Ö4** | **Grupla** | Genel Bakış'ın "Bugün ne var" kartına REVIEW sayacını ekle: `t.todays_plans.filter(p => p.gate_verdict==="REVIEW" && !p.operator_onayi && !p.expired).length` (uç zaten çekiliyor, yeni istek yok) | Açılış ekranı bekleyen REVIEW varken "senden bir şey beklenmiyor" yazıyor. |
| **Ö5** | **Yer-değiştir** | `spineHTML`'i Genel Bakış'a taşı (Portföy'den **kaldırılarak**, kopyalanarak değil); ADR'nin "BAŞKA HİÇBİR ŞEY" kuralı bu şerit lehine revize edilir | Panonun tek adresli triyaj yüzeyi 10-sn ekranında yok. |
| **Ö6** | **Kaldır** | HUD'dan `bekçi` çipini ve `#statuspill`in nabız metnini **kaldır**; ikisi de sessiz hattın segmentleri | Aynı sağlık gerçeği 2-3 bileşende tekrarlanıyor, toplama işlevini yitiriyor. |
| **Ö7** | **Grupla** | `sessizHat()`'e `askida` dalını ekle: sapma değil, `ok/total`ın altında sönük bir "N askıda · <neden>" satırı | Sunucu askıda nedenini üretiyor, pano hiç okumuyor (YASA 6). |
| **Ö8** | **Grupla** | Sessiz hat sapma satırına `runbook ↗` yanına **`→ gözetim#operasyon`** çapası ekle | Sapmadan gelen kutusuna giden hiçbir bağ yok. |
| **Ö9** | **Gizle** | `Bölüm 5`i **beş katlanabilir kartla** böl: `Dedektörler (7 desen)` · `Makullük ihlalleri` · `Defter sözleşmesi` · `Yazar ihlalleri` · `Eleme muhasebesi`; kapalıyken her biri kendi `.pm-cell` özetini gösterir | Tek kartta 5 alt-başlık ve 30+ satır aynı ağırlıkta duruyor. |
| **Ö10** | **Gizle** | Öğrenme sayfasının 7 bölümünden 5'ini (`golge`,`bilesenic`,`skiller`,`hafiza`,`ajan`) varsayılan-kapalı yap; `karne` ve `hermes` açık kalır | 39 kart tek kaydırma sütununda; sayfa bütçesi yok. |
| **Ö11** | **Yer-değiştir** | Bütünlük ihlallerini **alarm satırı** olarak gelen kutusuna düşür (kart Veri Sağlığı'nda kalır, satır Gözetim'de doğar) | Bir triyaj iki sayfaya yayılmış. |
| **Ö12** | **Yer-değiştir** | Runbook'u `/runbook` yerine **çekmecede** aç (mevcut `plotdrawer` mekanizması, `RECORD_VIEW.runbook`) | Teşhise gitmek panoyu terk ettiriyor ve kaydırma konumunu siliyor. |
| **Ö13** | **Grupla** | Alarm satırına satır-içi `ertele 24s` ve `sustur (gerekçe zorunlu, ≥20 karakter)` ekle; ikisi de `events.jsonl`e olay yazar | Gelen kutusunda ya hepsi ya hiçbiri var. |
| **Ö14** | **Kaldır** | "Bölüm 1…6" numaralarını başlıklardan kaldır (adlar zaten kendi başına anlamlı) | Numara artık var olmayan bir sırayı vaat ediyor. |
| **Ö15** | **Grupla** | ⌘K'daki 29 gezinme komutunu **"Sayfalar" (5-7)** ve **"Bölümler" (20)** diye ikiye ayır | Tek grupta 29 satır, Hick maliyeti boş sorguda ödeniyor. |
| **Ö16** | **Grupla** | Kaydırma konumunu `sessionStorage` ile sayfa başına sakla; `go()` yalnız **yeni** sayfada 0'a döner | Her dönüşte 39-kartlık sayfada baştan arama. |
| **Ö17** | **Yer-değiştir** | `nextSessionCard`'ın ayna sütununu kaldır; huninin tek evi ③ EMİRLER durum kartı | Ayna durumu iki dilde iki kez anlatılıyor. |
| **Ö18** | **Grupla** | Kart başlıklarına tek renkli, 14px, `aria-hidden` glif ekle (kenar şeridinin `RAIL_ICON` dilinden türet) | Tarama tek kanala (tipografi) bağlı. |

---

## 3. SOMUT ÇÖZÜM

### 3.1 TASK ② — yeni akış (Ö1+Ö2+Ö4+Ö5)

**Düşük-detay wireframe (metin):**

```
┌─ GENEL BAKIŞ ────────────────────────────────────────────────────────────┐
│ [sessiz hat: bekçiler 15/17 · 2 askıda (hermes kota) · kilit — · taze —] │  ← Ö6,Ö7
│                                                                          │
│ ⚠ SENDEN BİR ŞEY BEKLİYOR      (triyaj şeridi — Ö5)                      │
│   [3 plan onayını bekliyor →]  [2 emir reddedildi →]  [nabız 9sa →]      │
│   └── çipler `sayfa#bolum` çapalı; tıklayınca ÇEKMECE açar, sayfa değil  │
│                                                                          │
│ ┌ Dün gece ─────┐ ┌ Sermaye · köken ┐ ┌ Bugün ne var ─────────────────┐ │
│ │ 2026-08-05    │ │ $98.412         │ │ 4 silahlı emir                │ │
│ │ 61·5·3        │ │ tohum ayrışık   │ │ 3 REVIEW onayını bekliyor ⚠  │ │  ← Ö4
│ │ ▓▓▓▓▓░ tazelik│ │ ▓▓▓░░           │ │ 0 gelen kutusu kararı         │ │
│ │ → Koşu&Döngü  │ │ → Portföy       │ │ → Portföy & Emirler           │ │
│ └───────────────┘ └─────────────────┘ └───────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Adım adım yeni akış:**

1. Genel Bakış açılır. Triyaj şeridi **"3 plan onayını bekliyor"** çipini gösterir (Ö5 + Ö4).
2. Çipe tık → **çekmece açılır** (sayfa değişmez, kaydırma yerinde kalır). Çekmece "onay kuyruğu"
   kaydını taşır: 3 REVIEW planı, her biri `planRowFull` satırı. → **1 tık**
3. Plana tık → aynı çekmece plan kaydına derinleşir (`RECORD_VIEW.plan`). → **1 tık**
4. "Onayla ve Arm Et" (niyet) → **1 tık**
5. Tekrar bas (karar) → **1 tık**. Çekmece **kapanmaz**; onay bloğu şuna dönüşür:

```
┌─ çekmece ────────────────────────────────────────────────┐
│ ✓ onaylandı 6 Ağu 09:14 — plan silahlı kuyrukta (4 emir) │
│ Kapı hükmü REVIEW olarak KALDI (onay bir olaydır).       │
│                                                          │
│ SIRADAKİ ADIM — aynaya gönderim                          │
│ 4 silahlı plandan 1'i aynada. Gönderim ayrı bir kapıdır. │
│ [ Aynaya gönder (4 plan) ]     ← Ö2, iki adımlı           │
│ ⟨sonuç satırı burada belirir⟩  ← Ö1                       │
└──────────────────────────────────────────────────────────┘
```

6. "Aynaya gönder" (niyet) → **1 tık**; tekrar bas (karar) → **1 tık**.
7. **Sonuç ÇEKMECEDE yazılır:** `✓ 4 emir gönderildi` / `2 gönderildi · 2 broker reddi: <gerekçe>` /
   `✗ HTTP 502 — ayna erişilemiyor`. Ayrıca ③ EMİRLER durum kartının hunisi arkada tazelenir.

**ÖNCE → SONRA:**

| | tık | tuş | kaydırma | sayfa |
|---|---|---|---|---|
| **Önce** | 8 | 1 | ~7 | 3 |
| **Sonra** | **6** | 1 (Esc) | **0** | **0** |

**Kazanç: −2 tık, −7 kaydırma, −3 sayfa değişimi.** Asıl kazanç sayıda değil: **görev tek bir
yüzeyde başlayıp bitiyor** ve her adımın sonucu **kalıcı** olarak yazılıyor.

**Durum tasarımı (mutlu-yol yasak):**

| Durum | Ne yazar |
|---|---|
| **Yüklenme** | `[ gönderiliyor… ]` — düğme `disabled`, metin değişir (`planOnayla` deseni) |
| **Boş** | Şerit çipi hiç doğmaz. Kart: "0 REVIEW · kapı bu seansta N plan üretti, hepsi GO/NO_GO" — *"aday yok"* ile *"aday vardı, kapı eledi"* ayrımı `RENDER.adaylar`'da zaten var, buraya da taşınır |
| **Ölçülemedi** | `t.todays_plans` hiç gelmediyse: `REVIEW <b class="mut">ölçülemedi</b> — plan defteri uçtan gelmedi` (asla 0 değil) |
| **Kısmi başarı** | `2/4 gönderildi · 2 broker reddi` + ret gerekçeleri satır satır + `→ portfoy#mutabakat` çapası |
| **Hata** | `✗ HTTP <kod> — <sunucu gerekçesi>`; düğme **geri gelir** (`planOnayla`'nın mevcut deseni), karar operatörün |
| **Süresi dolmuş** | Düğme **çizilmez**; yerine `Süresi dolmuş bir plan onaylanamaz — seviyeleri bayat` (mevcut davranış korunur) |
| **HALT çekili** | Düğme çizilir ama üstünde `HALT çekili — onay kuyruğa girer, dolum HALT kalkınca` uyarısı; uç 409 verirse gerekçe basılır |

### 3.2 TASK ③ — yeni akış (Ö8+Ö9+Ö11+Ö12+Ö13)

```
┌─ herhangi bir sayfa ─────────────────────────────────────────────────────┐
│ [sessiz hat  bekçiler 2 GECİKEN                                          │
│    ▸ scheduler_poll  9sa  · pencere 1sa  [runbook ⌄] [→ gelen kutusu]]   │  ← Ö8, Ö12
└──────────────────────────────────────────────────────────────────────────┘
       │ "→ gelen kutusu" tıklanır
       ▼
┌─ GÖZETİM & ALARMLAR ─────────────────────────────────────────────────────┐
│ ALARM GELEN KUTUSU (9 okunmamış · uzak kanal YOK)     [tümünü okundu]    │
│ ▲ MECHANISM_STALE ×4  scheduler_poll 9sa geride    2sa [runbook⌄][ertele]│  ← Ö13
│ ▲ INTEGRITY_STARVED ×1  llm_calibration üretti, eşleşemedi  5sa [runbook⌄]│ ← Ö11
│ △ PARITY_LOW ×7  37 satırın 7'si düşük              1g  [runbook⌄][sustur]│
└──────────────────────────────────────────────────────────────────────────┘
       │ [runbook⌄] tıklanır → ÇEKMECE (sayfa değişmez)
```

**ÖNCE → SONRA:**

| | tık | kaydırma | sayfa | harici belge |
|---|---|---|---|---|
| **Önce** | 6 | ~5 | 3 | 1 |
| **Sonra** | **2** | **~1** | **1** | **0** |

**Durum tasarımı:**

| Durum | Ne yazar |
|---|---|
| **Yüklenme** | Mevcut `<div class="empty">yükleniyor…</div>` korunur |
| **Boş** | `Okunmamış alarm yok — dürüst boşluk.` (mevcut, aynen kalır) |
| **Pencere kesildi** | `a.window_truncated` dalı mevcut ve doğru — aynen kalır |
| **Runbook girdisi yok** | Çekmece: `Bu ad için runbook girdisi henüz yazılmadı — bağ bir VAAT değil bir ADRES` (mevcut sözleşme) |
| **Ertelenmiş alarm** | Satır **silinmez**, sönükleşir + `24sa ertelendi · <ts>` rozeti; süre dolunca tam tonda geri gelir |
| **Susturulmuş** | Gerekçe **zorunlu** (≥20 karakter, YASA 4 deseni); satır `sustur: <gerekçe>` ile listede kalır |

### 3.3 TASK ① — yeni akış (Ö5+Ö6+Ö7)

Adım sayısı zaten 0. Kazanç **okuma bölgesi** sayısındadır:

| | okuma bölgesi | sağlık yüzeyi |
|---|---|---|
| **Önce** | 12 | 6 |
| **Sonra** | **8** | **2** (sessiz hat + triyaj şeridi) |

HUD'da kalanlar: `mod·broker` · `rejim·bütçe` · `döngü geri sayımı` · `IO` — dördü de sessiz hatta
**bulunmayan** gerçekler. Çıkanlar: `bekçi` çipi (→ sessiz hat segmenti), `WS` çipi (→ sessiz hat
tazelik segmenti + ③ EMİRLER kartı), `#statuspill` nabız metni (→ sessiz hat).

---

## 4. ÖNCELİK — Etki × Efor

Efor birimi: **S** = tek fonksiyon/tek dosya, <50 satır · **M** = 1-3 fonksiyon + test · **L** = çok
dosya + ADR + test çivisi güncellemesi.

| Öneri | Etki | Efor | Çeyrek |
|---|---|---|---|
| **Ö1** `#alp-msg` kabı | **çok yüksek** (ciddiyet-4) | **S** (~3 satır) | ⚡ QUICK WIN |
| **Ö4** REVIEW sayacı | **çok yüksek** (ciddiyet-4) | **S** (~5 satır, yeni uç yok) | ⚡ QUICK WIN |
| **Ö3** `alpacaClose` kaldır | **çok yüksek** (ciddiyet-4, güvenlik) | **S** (1 düğme + 1 bağ) | ⚡ QUICK WIN |
| **Ö7** sessiz hat `askida` | yüksek (YASA 6) | **S** (~8 satır) | ⚡ QUICK WIN |
| **Ö8** sapma → gelen kutusu çapası | yüksek | **S** (~3 satır) | ⚡ QUICK WIN |
| **Ö14** "Bölüm N" numaralarını kaldır | orta | **S** (6 dizgi) | ⚡ QUICK WIN |
| **Ö9** `Bölüm 5`i beşe böl | **çok yüksek** (B11 kökü) | **M** | 🔧 YAPISAL |
| **Ö2** "Aynaya gönder" çekmecede | **çok yüksek** | **M** | 🔧 YAPISAL |
| **Ö5** triyaj şeridi Genel Bakış'a | **çok yüksek** | **M** (+ ADR notu) | 🔧 YAPISAL |
| **Ö6** HUD/statuspill tekrar temizliği | yüksek | **M** (test çivisi var) | 🔧 YAPISAL |
| **Ö16** kaydırma hafızası | yüksek | **M** | 🔧 YAPISAL |
| **Ö10** Öğrenme kart sözleşmesi | **çok yüksek** (39 kart) | **M-L** (§5 sözleşmesi) | 🔧 YAPISAL |
| **Ö13** alarm ertele/sustur | yüksek | **M-L** (sunucu tarafı gerekir) | 🔧 YAPISAL |
| **Ö15** palet grup ayrımı | orta | **S-M** (test çivisi var) | 🔧 YAPISAL |
| **Ö17** `nextSessionCard` ayna sütunu | orta | **S** (+ YASA-6 kontrolü) | 🔧 YAPISAL |
| **Ö11** bütünlük → alarm satırı | yüksek | **L** (sunucu + pano) | 🌱 UZUN VADE |
| **Ö12** runbook çekmecede | yüksek | **L** (yeni `RECORD_VIEW`) | 🌱 UZUN VADE |
| **Ö18** kart ikonları | orta | **L** (18 kart × jeton kararı) | 🌱 UZUN VADE |
| **§7 sayfa birleşmesi 7→5** | **çok yüksek** | **L** (23 test + ADR) | 🌱 UZUN VADE |

### 4.1 "ÖNCE BUNU YAP" listesi

**Dalga 0 — bugün, tek Opus turu, ~1 saat (ciddiyet-4'lerin üçü birden kapanır):**
`Ö1` + `Ö4` + `Ö3` + `Ö7` + `Ö8` + `Ö14`.
Altısı da **tek dosya** (`app.js`), birbirine dokunmuyor, hiçbiri ADR/test çivisi kırmıyor.
**Bu dalga bittiğinde AMGN sınıfı kapanmış olur.**

**Dalga 1 — yapısal, tek Opus turu:** `Ö2` + `Ö5` + `Ö6` + `Ö16` + `Ö17`.
Hepsi görev-akışı düzeltmesi; `Ö5` ve `Ö6` ADR'nin "BAŞKA HİÇBİR ŞEY" kuralına **beyanlı** bir
revizyon ister (ADR Ek'ine tek paragraf).

**Dalga 2 — kart sözleşmesi, tek Opus turu:** `Ö9` + `Ö10` + §5'in tamamı.
Tek bir yeni bileşen (`katKart`) ve onun `.pm-*` üstüne oturması; sonra 18 kartın ona geçirilmesi.

**Dalga 3 — uzun vade, ayrı turlar:** `Ö11`, `Ö12`, `Ö13`, `Ö15`, `Ö18`, §7.

---

## 5. KART SÖZLEŞMESİ

### 5.1 Tek kart anatomisi — v192 `.pm-*` dilinin ÜSTÜNE

**Yeni hücre dili İCAT EDİLMİYOR.** Sözleşme mevcut `hucreGovde(o)` (app.js:1553) çıktısını kartın
**kapalı özeti** olarak kullanır. `o` sözleşmesi aynen: `{deger, degerSinif, oran, payda, meta,
rozet}` → `.pm-yield` / `.pm-conf[data-payda]` / `.pm-n` / `.pm-thin` / `.pm-none`.

```
KAPALI:
┌────────────────────────────────────────────────────────────────────┐
│ ⬡ Bütünlük dedektörleri            [3 İHLAL]                    ▸ │  ← başlık satırı
│   7 → 4                                                            │  ← .pm-yield
│   ▓▓▓▓░░░░░░  desen · payda: uygulanabilir desen (7)               │  ← .pm-conf + payda
│   3 desen düşüyor · 1 dedektör ölçemedi · 47sa geride              │  ← .pm-n
└────────────────────────────────────────────────────────────────────┘

AÇIK:
┌────────────────────────────────────────────────────────────────────┐
│ ⬡ Bütünlük dedektörleri            [3 İHLAL]                    ▾ │
│   7 → 4    ▓▓▓▓░░░░░░  desen · payda: uygulanabilir desen (7)      │
│   3 desen düşüyor · 1 dedektör ölçemedi · 47sa geride              │
│ ──────────────────────────────────────────────────────────────────│
│   <detay: mevcut kart gövdesi, DEĞİŞMEDEN>                        │
└────────────────────────────────────────────────────────────────────┘
```

**Başlık satırının dört alanı, sırayla:**

| Alan | Kaynak | Kural |
|---|---|---|
| **ikon** | `RAIL_ICON` dilinden türetilir | `aria-hidden`, tek renk, süs değil sınıf işareti |
| **isim** | mevcut `<h2 class="t">` metni | değişmez |
| **durum rozeti** | `hucre.rozet` → `.pm-thin` | **YALNIZ** ölçülemeyen/sapan hâlde doğar; sağlıklıyken **hiç yazılmaz** |
| **collapse oku** | `.detay-kat > summary::before` deseni (`▸`/`▾`) | mevcut CSS'ten türer, yeni kural yok |

**KAPALI ÖZETİN SÖZLEŞMESİ (bu sözleşmenin can damarı):**

> Kapalı özet **"içeride önemli bir şey var mı?"** sorusunu cevaplamak ZORUNDADIR. Cevaplamayan bir
> özet katlamayı yükü azaltmaktan çıkarır, **tık artıran bir süse** çevirir.

Bunun ölçülebilir hâli **üç kapı**:
1. `deger` **var** (veya `.pm-none` "veri yok" + nedeni).
2. `oran` + `payda` **beyanlı** (payda kurulamıyorsa çubuk **çizilmez**, meta nedenini yazar —
   `_durumEmirKarti`'nin mevcut kuralı).
3. `meta` **en fazla 2 satır** ve içinde **en az bir sayı** taşır.
Üçünden biri kurulamıyorsa **kart katlanamaz** — o kart bir özet üretemiyor demektir ve bu bir
tasarım bulgusudur, gizlenecek bir şey değil.

**Anomali mürekkebi (v192'nin kuralı aynen genişler):** sapma varsa **hücrenin mürekkebi** renklenir
(`.uyari` amber · `.kopuk` kırmızı) ve sapmanın adı `aria-label`a girer. **Ayrı bir anomali noktası
YOK** (v191'de zaten söküldü — o karar burada da geçerli).

### 5.2 Collapse kuralları

| Kural | Karar | Gerekçe |
|---|---|---|
| **Varsayılan** | **KAPALI** | 39 kartlık sayfada varsayılan-açık, sözleşmeyi anlamsız kılar |
| **Dikkat gerektiren** | **AÇIK başlar** — `hucre.rozet` doluysa **veya** `anomali` sınıfı varsa | Sapma bir katmanın altında saklanamaz |
| **Sayfanın 1. bölümü** | **AÇIK başlar** | Sayfanın soru cümlesine doğrudan hizmet eden bölüm gizlenmez |
| **Global aç/kapat** | `.alan-bas` içinde tek kontrol: `hepsini aç ⌄ / hepsini kapat ⌃` + ⌘K'da `Görünüm` grubunda iki komut | Tek tek 39 kart açmak bir görev değil bir ceza |
| **Oturum hatırlama** | `sessionStorage`, anahtar `mrd-kart:<sayfa>:<kart>` | `localStorage` **DEĞİL**: geçen haftanın açık kartı bu sabahın bakışını yönetmemeli |
| **Hatırlamanın ÜSTÜNÜ ÇİZEN kural** | Hatırlanan hâl "kapalı" ama **şimdi** anomali varsa kart **AÇILIR** ve şunu yazar: `kapalı hatırlanmıştı — sapma geldiği için açıldı` | Oturum hafızası bir alarmı gizleyebilseydi bu sözleşme bir güvenlik açığı olurdu |
| **Accordion DEĞİL** | Kartlar **bağımsız**; birini açmak diğerini kapatmaz | Uzman kullanıcı iki kartı yan yana karşılaştırır; accordion bunu yasaklar |
| **Klavye** | `<details>/<summary>` yerli sözleşmesi (Enter/Space); `j/k` satır gezinmesi **bozulmaz** (`[data-rk]` kümesi değişmez) | Yeni tuş dinleyicisi yazmamak H23 deseninin kuralı |
| **Yoğun-uzman muafiyeti** | Bir kart `data-kat="hayir"` taşıyorsa katlanmaz (tablolar: `adaylar` plan tablosu, `market` evren tablosu) | Yoğun düzen cezalandırılmaz — bunlar zaten "içinde ne var" sorusunu **satırlarıyla** cevaplıyor |

### 5.3 Uygulama sırası (18 kart)

| Öncelik | Kart | Neden |
|---|---|---|
| 1 | `Bölüm 5 · Bütünlük dedektörleri` → **5 karta böl** | B11, operatörün doğrudan şikâyeti |
| 2 | Öğrenme'nin `golge`(4) · `bilesenic`(7) · `skiller`(4) · `hafiza`(1) · `ajan`(2) = **18 kart** | B10, tek dalgada en büyük yük düşüşü |
| 3 | `veriboru`'nun `s4`,`s6`,`sSag` (3 kart) | ikinci en kalabalık yüzey |
| 4 | `mutabakat`'ın `sIcra`,`sBand`,`sGeceG` (3 kart) | `s1` açık kalır (bölümün ana cevabı) |

---

## 6. GENEL BAKIŞ VE DURUM IZGARASI — DEĞİŞMEZ ALANLAR

Denetim şunları **doğru** buldu ve **korunmasını** öneriyor:

- `GENEL_KARTLARI` ve `DURUM_KARTLARI`'nın **liste-veri olarak** tutulup teste sayılabilir olması —
  kart sayısını bir tasarım bütçesi yapan tek mekanizma budur ve **beş alan sayfasına da
  yayılmalıdır** (Ö10'un ön koşulu).
- `hucreGovde` / `.pm-conf[data-payda]` **payda beyanı**: sıfır paydadan oran üretmeme kuralı
  (`_durumEmirKarti`, `ozetHucre`) panonun en olgun tasarım kararı.
- `satirKoru` (app.js:1256) **satır-düzeyi yalıtımı** — dört müdahale kolunun birden silinmesi
  vakasının (v194) doğru cevabı; genişletilmeli, daraltılmamalı.
- `detayKatmani`'nin **`neden` parametresi**: "bu neden burada değil" sorusunun ekrandan
  cevaplanabilmesi. Yeni katlanabilir kart sözleşmesi bu alanı **devralmalı**.
- Sessiz hattın **`SH_ACILIM_TAVAN = 4` + "+N daha"** kırpma beyanı — kırpmanın sessiz olmaması.

---

## 7. SAYFA AZALTMA ÖNERİSİ — 7 → 5

### 7.1 Görev-tabanlı yeniden gruplama

| Yeni sayfa | Birleşen | Bölümler | Görev |
|---|---|---|---|
| **① Genel Bakış** | (değişmez) | — | TASK ① |
| **② Karar & Emir** | `kosu` + `portfoy` | `adaylar` · `onaylar` · `brifing` · `mutabakat` · `intraemir` + [detay: `kapilar`, `performans`] | TASK ② |
| **③ Gözetim & Veri** | `gozetim` + `veri` | `operasyon` · `veriboru` · `market` · `intraday` | TASK ③ |
| **④ Öğrenme** | (değişmez, katlanır) | 7 bölüm, 5'i varsayılan-kapalı | haftalık |
| **⑤ Kilitler & Yapılandırma** | (değişmez) | `mudahale` · `ayarlar` | müdahale |

**Neden bu ikisi birleşiyor:**

- **② Karar & Emir:** durum ızgarası (`DURUM_SAYFALARI = {kosu, portfoy}`) **zaten tek tanım, iki
  sayfada çiziliyor** — v191 çakışmayı bir bantla örttü, kökünü çözmedi. Birleşme, `durumIzgarasiCiz`
  çağrısını **ikiden bire** düşürür ve "aynı sayı iki sayfada" sınıfını yapısal olarak kapatır.
  Kart sayısı: 4 durum + 4 (kosu) + 13 (portfoy) = 4 + 17 → §5 sözleşmesiyle **4 + 6 açık + 11
  katlı**.
- **③ Gözetim & Veri:** TASK ③'ün ölçülen yolu bugün **iki sayfaya** yayılıyor (B12). Birleşme
  alarm → ihlal → veri kaynağı zincirini tek yüzeyde tutar. Kart sayısı: 3 + 8 = 11 → **3 açık +
  8 katlı**.

**Neden Öğrenme birleşmiyor:** 39 kart taşıyor ve hiçbiri diğer dört sayfanın sorusuna hizmet
etmiyor. Çözümü **birleşme değil katlama** (Ö10).

### 7.2 Bare-key etkisi

`VIEWS` 7→5 olunca çıplak `1-7` tuşları **`1-5`** olur ve `PAGE_MAP`/`GIT_KISAYOL` **zaten VIEWS'ten
türüyor** (app.js:7250, `test_uiux_s1b_v154.py`) — yani kas hafızası bir kez kayar, sonra sabitlenir.
Eski hash'ler `ROUTE_ALIAS`'a düşer: 12/12 kuralı **14/14** olur (`kosu`→`karar`, `veri`→`gozetim`).

### 7.3 ÖLÇÜLEN MALİYET

Değişmesi gereken dosyalar (hepsi **birlikte**, hiçbiri sessiz kırılmaz):

| # | Dosya | Ne değişir |
|---|---|---|
| 1 | `meridian/web/app.js` | `VIEWS` · `ALAN_BOLUMLERI` · `EKRAN_SORUSU` (27→25 girdi: iki **sayfa** cümlesi düşer, 20 **bölüm** cümlesi aynen kalır) · `ROUTE_ALIAS` (12→14) · `DURUM_SAYFALARI` (2→1) · `RAIL_ICON` |
| 2 | `meridian/web/index.html` | `.page` kapları 7→5; `.alan-bolum` kapları yeniden yerleşir (sıra `ALAN_BOLUMLERI` ile birebir kalmak zorunda) |
| 3 | `meridian/web/palette.js` | `SAYFA_ADI` · `BOLUMLER`'in sayfa sütunu |
| 4 | `docs/UIUX-S2R-REDESIGN.md` | **ADR revizyonu (S2R-4)**: hangi sayfa neden birleşti, ölçülen kart sayıları, "BAŞKA HİÇBİR ŞEY" kuralının triyaj şeridi lehine revizyonu |

**Test çivisi maliyeti — ölçüldü:**

| Dosya | Sayfa yapısına bağlı test fonksiyonu |
|---|---|
| `tests/test_s2r2_goc_v156.py` | **8** (en sertler: `test_bolum_sayfa_haritasi_ADR_ile_birebir` — `ALAN_BOLUMLERI == ADR_HARITASI` tam eşitlik) |
| `tests/test_s2r1_kabuk_v155.py` | **5** (`VIEWS` sırası/sayısı, `EKRAN_SORUSU` kapsamı, `GENEL_KARTLARI`) |
| `tests/test_uiux_s1b_v154.py` | **5** (`g`-eşlemesi `VIEWS`'ten türer) |
| `tests/test_s2r3_cila_v160.py` | **2** (`test_palet_bolum_tablosu_ALAN_BOLUMLERI_ile_BIREBIR`) |
| `tests/test_market_v104.py` | **2** |
| `tests/test_pano_durum_kartlari_v191.py` | **1** (`DURUM_SAYFALARI`) |
| **TOPLAM** | **23 test fonksiyonu / 6 dosya** |

**Bu çivilerin niteliği önemlidir:** hiçbiri "yedi sayfa olsun" demiyor; **iki listenin ayrışmasını**
yasaklıyorlar. Yani maliyet *"çiviyi sök"* değil, *"çiviyi ADR ile birlikte yeni yere çak"*.
Toplam düzenleme: **4 kaynak dosya + 6 test dosyası + 1 ADR.**

**KARŞI-ARGÜMAN (yazıya geçiyor):** Sayfa birleşmesi **§5 kart sözleşmesi olmadan yapılırsa
DURUMU KÖTÜLEŞTİRİR** — ② Karar & Emir 21 kartlık bir kaydırma sütununa dönüşür. **Sıra
zorunludur: Dalga 2 (kart sözleşmesi) → Dalga 3 (sayfa birleşmesi).** Tersi yapılırsa operatör
"yedi sayfa daha iyiydi" diyecektir ve haklı olacaktır.

---

## 8. HÜKMÜ KESKİNLEŞTİRECEK EKRAN GÖRÜNTÜSÜ İSTEKLERİ

Aşağıdaki üçü, bu raporda **tahmin** olarak işaretlenmiş üç noktayı **ölçüme** çevirir:

1. **Öğrenme sayfası — tam sayfa, tepeden dibe (1440×900, tam kaydırma yüksekliği görünecek
   şekilde).** Ölçmek istediğim: 39 kartın gerçek piksel yüksekliği ve `#ogrenme-eylem` şeridiyle
   `karne` arasındaki ilk bölüm sınırının ritmi. §5'in "18 kart katlanır" önerisinin kazancını
   **piksel** cinsinden yazabilmek için gerekli.

2. **Veri Sağlığı → `Bölüm 5 · Bütünlük dedektörleri` kartı — CANLI hâliyle, ihlaller görünürken.**
   Ölçmek istediğim: 7 desen satırı + makullük + defter sözleşmesi + yazar ihlalleri + eleme
   muhasebesi bloklarının **gerçek satır sayısı** ve hangisinin göze ilk çarptığı. B11'in ciddiyetini
   3'ten 4'e çıkarıp çıkarmayacağına bu karar verir.

3. **Üst bar (nav) — sapma anında: HUD çipleri + `#statuspill` + sessiz hat "sap" hâli aynı karede.**
   Ölçmek istediğim: Ö6'nın (bekçi çipi + nabız metni kaldırılması) gerçekten bir bilgi kaybı
   üretmediği, yani sessiz hattın açılımının o iki çipin taşıdığı her şeyi **görünür** kıldığı.
   Kaldırma önerisi ancak bu kareyle güvenle uygulanabilir.

**Bonus (varsa):** onay çekmecesi açıkken bir REVIEW planının ekran görüntüsü — `planOnayBloguHTML`
bloğunun çekmece içindeki dikey konumunu ölçmek, TASK ② adım-4'ün "~1 kaydırma" tahminini
kesinleştirir.

---

## 9. ÖZET — SAYILAR

| Ölçüm | Mevcut | Dalga 0-2 sonrası (hedef) |
|---|---|---|
| Ciddiyet-4 bulgu | **3** | 0 |
| Ciddiyet-3 bulgu | **11** | 2 |
| TASK ① okuma bölgesi | 12 | **8** |
| TASK ① sağlık yüzeyi | 6 | **2** |
| TASK ② tık / kaydırma / sayfa | 8 / ~7 / 3 | **6 / 0 / 0** |
| TASK ③ tık / kaydırma / sayfa | 6 / ~5 / 3+belge | **2 / ~1 / 1** |
| Öğrenme sayfası açık kart | 39 | **~12** (27 katlı) |
| Sayfa sayısı | 7 | 7 (Dalga 3'te → **5**) |

---

*Denetim: 2026-08-06 · salt-analiz · kod yazılmadı, git koşulmadı, canlıya dokunulmadı.*
