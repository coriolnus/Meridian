# ENVANTER — DEĞER-EŞİTLİĞİ: 26 KAPISIZ ÇİFTİN GEREKÇE ENVANTERİ — 2026-08-22

**Görev.** `docs/DENETIM-SPLIT-SINIFI-2026-08-13.md` §4.1'in **26 KAPISIZ çiftini** bugünkü koddan
yeniden ölçüp üç sınıfa ayırmak — **(a) kaynağında kapanmış · (b) `watchdog.EQUIVALENT_TRUTHS`a
bağlı · (c) bağlanmamış** — ve bağlanmamışların GEREKÇESİNİ yeniden türetmek. v245 turu (3c9fd0f,
2026-08-14) bu envanteri çıkarmıştı ama gerekçeler yalnız kayıp bir ajan oturumundaydı; bu belge o
boşluğu **yeniden ölçerek** kapatır.

**Tur sınırı.** SALT ÖLÇÜM + BU BELGE. `git` komutu koşulmadı; `meridian/` altında hiçbir dosya
değiştirilmedi; test koşulmadı; `state/`e yazılmadı; **canlıya (A1) hiç bağlanılmadı** — bütün
kanıtlar yerel `main` çalışma ağacından `grep`/okuma iledir (2026-08-22). Bunun bedeli açık:
ortamlar-arası çiftlerin **canlı bacağı bu turda ÖLÇÜLEMEDİ** (aşağıda her yerde `None + neden`
olarak, "eşit" ya da "ayrık" diye DEĞİL).

---

## 1. YÖNETİCİ ÖZETİ

| Sınıf | Sayı | Çiftler (§4.1 numarasıyla) |
|---|---:|---|
| **(a) kaynağında kapanmış** | **12** | 1 · 5 · 6 · 7 · 8 · 9 · 12 · 18 · 19 · 20 · 22 · 23 |
| **(b) `EQUIVALENT_TRUTHS`a bağlı** | **5** | 13 · 14 · 15 · 17 · 21 |
| **(c) bağlanmamış (gerekçeli)** | **9** | 2 · 3¹ · 4 · 10 · 11 · 16 · 24 · 25 · 26 |
| **🔴 bugün fiilen AYRIK yüzey taşıyan** | **5** | 24 · 25 · 26 · 10 (kısmî) · 16 (latent) |

¹ #3 **kısmen bağlıdır**: süreç-içi dört-kaynak bacağı `max_drawdown` olgusuyla kapılı
(`watchdog.py:2216`), **ortamlar-arası** bacağı bağlanmamış — ayrıntı §4-c.

**Sayım mutabakatı (v245'e karşı).** Brief'e taşınan v245 sayımı "13 kapanmış · 5 bağlı · 9
bağlanmamış"tı — toplamı **27 eder, 26 değil**; kayıp oturumun bölme mantığı yeniden üretilemedi.
Bugünkü ölçüm **12 + 5 + 9 = 26** verir; "5 bağlı" ve "9 bağlanmamış" kalemleri v245'le birebir
örtüşüyor, fark yalnız (a) kovasının 13 mü 12 mi sayıldığında (muhtemel neden: #3'ün kısmî-bağlı
hâlinin hangi kovaya yazıldığı, ya da iki-sayılı bir çiftin — ör. #6 "5 positions · 1.0R" — ikiye
bölünmesi).

**Şerh — kaynak belgenin kendi sayım tutarsızlığı.** §4.1'in başlığı "(18)" der ama tablo **26
satır** taşır (1-26); §4.2'nin numaralandırması 19'dan başlar ve 19-26 numaraları **iki tabloda da**
geçer. Bu envanter DAİMA §4.1 satırlarını kasteder.

**Kapılı tarafın bugünkü durumu** (brief beyanı: ayrık 0 · eşit 7 · beyanlı-ayrı 2). Bu tur repo
tarafındaki değerleri nokta-kontrol etti ve beyanla tutarlı buldu: `max_drawdown` çevrimi
0,16/0,16/0,16/0,08×2 ✓ · `asgari_ornek` 30/30/30/30 ✓ · `rr_tabani` 2,0=2,0 ✓ ·
`alarm_jetonlari` **14/14, fark kümesi boş** (comm ile ölçüldü) · `silahli_kurulumlar` sunumda
uyuyan-ilanı yok ✓. `defter_sema_kapsami` ve `strateji_surumu` bu turda yeniden koşulmadı
(fonksiyon-çifti / state okuması gerektirir; brief'in "esit=7" sayımının içindedir).

---

## 2. BUGÜNKÜ `EQUIVALENT_TRUTHS` — 9 OLGU ve 26'YA EŞLEME

Kayıt: `meridian/watchdog.py:2212` (`divergence_report` `:2350`). Her olgunun satırı ve 26'daki
karşılığı:

| Olgu | Satır | Kaynaklar (özet) | 26'daki karşılığı |
|---|---|---|---|
| `max_drawdown` | `watchdog.py:2216` | goal ↔ EDGE_MAXDD_MAX ↔ RESULT_MAXDD_MAX ↔ DD_VETO_MARGIN (yarisi) | **#3'ün süreç-içi bacağı** |
| `strateji_surumu` | `:2230` | strategy.yaml:version ↔ scoreboard.current_version | 26 DIŞI — §4.2-#36 (kapısız-KAPILI satırı) |
| `acik_pozisyon_defteri` | `:2241` | portfolio.positions ↔ trades açık-satır (beyanlı-ayrı) | 26 DIŞI — §7-#2 yanlış-pozitifin KAYDI |
| `silahli_kurulumlar` | `:2254` | strategy.ARMED_SETUPS ↔ sunum uyuyan-iddiaları | **#21** |
| `asgari_ornek` | `:2277` | goal:min_sample ↔ REGIME_N_MIN ↔ RESULT_N_MIN ↔ IC_MIN_SAMPLE | **#15** (ve #16'nın ana değerleri — yedek literali HARİÇ, bkz. §4-c) |
| `rr_tabani` | `:2296` | guard.DISCIPLINE_MIN_RR ↔ bounds:exit.profit_target_r.min | **#14** |
| `alarm_jetonlari` | `:2309` | obs.NOTIFY_TOKENS ↔ app.js `jetonlar:` dizileri | **#13** |
| `defter_sema_kapsami` | `:2322` | ledgers.CONTRACTS zorunlu ↔ storage._COLS karşılığı | **#17** |
| `derisk_tabani` | `:2334` | goal:max_drawdown ↔ broker.DERISK_FLOOR_DD (beyanlı-ayrı) | 26 DIŞI — §7-#3 yanlış-pozitifin KAYDI |

Yani 9 olgunun **5'i** 26'nın bir çiftini tam kapatır (#13, #14, #15, #17, #21), **1'i** #3'ü
kısmen kapatır, **3'ü** 26 dışındaki gerçekleri kayda alır (denetimin "bilinçli ikizleme kayda
girsin, sessiz muafiyet olmasın" ilkesi — ikisi `beyanli-ayri` ilişkisiyle).

---

## 3. ÖZET TABLO — 26 ÇİFTİN BUGÜNKÜ HÂLİ

Sınıf: **a** = kaynağında kapanmış · **b** = bağlı · **c** = bağlanmamış. Kanıtlar bugünkü
(2026-08-22) yerel ağaçtan.

| # | Çift (§4.1) | Sınıf | Bugünkü kanıt (dosya:satır) | Gerekçe / bugünkü değerler |
|---:|---|:--:|---|---|
| 1 | ayna rozeti (`mirror_drift` ↔ `position_drift`) | **a** | `loop.py:3166-3167` nabza **her iki** alan yazılır; `app.js:872-881` `aynaRozeti` İKİ boyutu (fiyat+adet) ayrı okur, birini kaçırırsa "ölçülmedi" der | Denetimin P0-a önerisi uygulanmış: gerçek nabza taşındı, rozet tek evden okuyor |
| 2 | repo ↔ canlı kod (108 yüzey) | **c** 🔶 | `dagit.sh:30` commit'i hâlâ yalnız **konsola** basar; `dagitim.json`/`deployed_sha`/`VERSION` beyanı repo genelinde YOK (grep boş); `cmp -s` yalnız `state/*.yaml` (`dagit.sh:126,298`) | **ORTAMLAR-ARASI**: `EQUIVALENT_TRUTHS` süreç-içidir, iki makinenin ağacını tek süreç göremez — kapısı dedektör değil dağıtım-beyanıdır (P0-b) ve hâlâ yazılmamış. Canlı ağaç bu turda ölçülmedi (**None**: A1'e bağlanılmadı) |
| 3 | `max_drawdown` ortamlar arası | **c¹** | Süreç-içi bacak: `watchdog.py:2216` olgusu; repo bugün EŞİT — `goal.yaml:20`=0,16 · `analytics.py:1676`=0,16 · `analytics.py:2168`=0,16 · `shadowlaw.py:90`=0,08 (yarisi→0,16) | **ORTAMLAR-ARASI**: olgu canlı süreçte kendi ağacının 4 sayısını kıyaslar; **repo-ağacı ↔ canlı-ağacı kıyası hâlâ yok** (#2 ile aynı kök: dağıtım beyanı). Canlı değerler bu turda ölçülmedi (**None**) |
| 4 | yerel defter ↔ canlı DB | **c** 🔶 | Yerel bugün: `state/trades.jsonl` **95 satır** · `trade_plans.jsonl` **390** · `portfolio.last_date` **2026-07-28** · `state/meridian.db` **YOK** — 08-13 fotoğrafıyla BİREBİR donmuş. P2 önerisi (`yerel_donmus_defter` damgası) uygulanmamış: `grep -rn yerel_donmus meridian/ tests/` → boş; tek yönlü uyarı hâlâ yalnız `db_off_kaynaklar_arsivde` (`storage.py:335`) | **ORTAMLAR-ARASI**: yerelde DB yok → süreç "göç hiç olmamış" dünyada dosyaları kanonik okur; süreç-içi dedektör bunu ayrışma olarak GÖREMEZ (kendi gördüğü tek kitap zaten o). Canlı DB bu turda ölçülmedi (**None**); 08-13 canlı ölçümü 97/409/4-pozisyon idi → yapısal ayrıklığın sürdüğü nerdeyse kesin ama bugün damgalı değil |
| 5 | README "max drawdown 8%" | **a** | README tümden yeniden yazılmış (215 satır, TR); drawdown/eşik SAYISI hiç geçmiyor (grep boş) | Yüzey kaldırılmış; ayrıca README artık C10 kapsamında (`test_skill_cleanup_v121.py:378`) |
| 6 | README "5 positions · 1.0R" | **a** | Aynı: pozisyon-sayısı/R iddiası yok (grep boş) | Yüzey kaldırılmış |
| 7 | README "66 skills" | **a** | `README.md:78`: *"Beceri sayısı sayfaya yazılmaz: `GET /api/public/summary → skills_live`"* | Doğru desene (sayı yerine adres) çevrilmiş + C10 README'yi tarar ve kök-dosya zorunluluğu var (`test_skill_cleanup_v121.py:419-420`) |
| 8 | README `skills/shadow/` yolu | **a** | "shadow" geçişi yok (grep boş) | Yüzey kaldırılmış. (Akraba iddia `PRODUCT.md:47` "10 sessions" durur — o §6-#5'in ölçülemeyeniydi, 26'nın parçası değil) |
| 9 | README "last 20 sessions" | **a** | Pencere iddiası yok (grep boş); gerçek hâlâ `analytics.py:49` `LADDER_BREAKER_WINDOW_DAYS=30` | Yüzey kaldırılmış |
| 10 | PRODUCT.md "state/ tek gerçek kaynak" | **c** 🔴 | PRODUCT.md tümden yeniden yazılmış (194 satır, EN tasarım brief'i) AMA `:165-167`: *"Live state files under `state/` (… `equity_curve.json`, …) are the only source of real numbers"* — oysa `storage.py:1-4` `equity_curve.json`u altı **DB varlığından** biri sayar (canlıda kanonik dosya arşivde) | **KAYNAĞI HENÜZ ONARILMAMIŞ** (hiçbir şeyden türemeyen anlatı). KISMEN AYRIK: örnek listesindeki 5 dosyadan 4'ü gerçekten dosyadır; `equity_curve.json` canlıda dosya DEĞİL DB varlığıdır — belgeye güvenen biri canlıda boş yol arar |
| 11 | sektör/ısı tavanı (dört sayı) | **c** | `goal.yaml:133`=40,0 · `bounds.yaml:103` max=30,0 ("NOTIONAL payı; bant 25-30") · `guard.py:533-534`=25,0/6,0 ("bandın ALT ucu" beyanlı ama repo genelinde **tek geçiş tanım satırları** — okuyucu hâlâ yok, ölçüldü) · runtime `portfolio.sector_cap` strategy.yaml'da yok → kapalı | **FARKLI NİCELİK**: goal'ün 40,0'ı pozisyon-SAYISI paydalı sektör maruziyetidir (payda artık kendi anahtarını taşır: `guard.py:344-351` `sector_cap_basis`), bounds'un 30,0'ı NOTIONAL pay tavanı, guard'ın 25,0/6,0'ı beyanlı bant-alt-ucu varsayılanı. Bunları `EQUIVALENT_TRUTHS`ta eşitlemek yakın-ama-farklı-tanımlı sayıları eşitlemek olur → kurt-masalı sınıfı yanlış alarm. Gerekçe HÂLÂ GEÇERLİ; kalan borç ayrışma değil **okuyucusuz sabit** (YASA 6, P3 kalemi) |
| 12 | `default_strategy` yedeği | **a** | `config.py:352` `position_size_r: 0.5` = `strategy.yaml:12` 0,5; gerekçe `config.py:307-327`'de yazılı; çivi **var**: `test_wp2d_pano_beyani_v246.py:353,417` | Değer hizalandı + testle çivilendi (v246 turu) |
| 13 | `app.js` alarm jetonları | **b** | Olgu `watchdog.py:2309`; bugün ölçüldü: `obs.py` 14 `ALARM_` sabiti ↔ `app.js` `jetonlar:` dizileri birleşimi 14 — **fark kümesi boş** (`comm`) | `alarm_jetonlari` olgusu; regresyon kapısı olarak çalışıyor |
| 14 | `guard.DISCIPLINE_MIN_RR` | **b** | Olgu `watchdog.py:2296`; `guard.py:317`=2,0 ↔ `bounds.yaml:7` min=2,0 — EŞİT | `rr_tabani` olgusu; iki yönlü ayrışmanın da anlamı olgu yorumunda yazılı |
| 15 | `REGIME_N_MIN` ↔ `min_sample` | **b** | Olgu `watchdog.py:2277`; `goal.yaml:33`=30 · `analytics.py:1642`=30 · `:2159`=30 · `:841`=30 — EŞİT | `asgari_ornek` olgusu; denetimin "çivi literaldi" kusuru çalışma-anı kıyasa taşındı |
| 16 | `min_sample` yedeği 20 | **c** 🔴(latent) | `score.py:108` ve `shadow_variants.py:532` hâlâ `goal.get("min_sample", 20)` — literal **20**, gerçek **30** | **ÇAĞRI-İÇİ LİTERAL**: dedektör modül sabitini okuyabilir (`_sabit`), bir çağrı ifadesinin İÇİNDEKİ yedek literali okuyamaz — bağlanacak adreslenebilir yüzey yok. Yazımda AYRIK (20≠30); bugün fiilen ısırmıyor (goal.yaml'da anahtar mevcut) — anahtar düşerse iki modül sessizce 20 tabanıyla konuşur. P3'ün "20→30" önerisi uygulanmamış |
| 17 | `ledgers.CONTRACTS` ↔ `storage._COLS` | **b** | Olgu `watchdog.py:2322` (`_defter_sema_alanlari` çifti) | `defter_sema_kapsami` olgusu; ayrışma alan ADIYLA raporlanır |
| 18 | "7 desen" ↔ "6 desen" | **a** | `app.js:6277-6293`: başlık sayısı **rapordan türer** (`${_patKeys.length} dedektör`), alt satır "kapsam matrisi deseni" diye YENİDEN ADLANDI, tanınmayan dedektör "PANODA TANIMSIZ" çipiyle bağırır | İki sayının iki ayrı soru olduğu artık yüzeyde yazılı; elle senkron kalmadı |
| 19 | `workflow-diagram.html` Gemini modeli | **a** | `:204`: *"MODEL ADI BU SAYFADA YAZILMAZ … Yürürlükteki ad canlı gelir: /api/secrets → model_defaults"* — ölü ad silinmiş, vaka tarihçesiyle | Sayı/ad yerine adres deseni |
| 20 | `workflow-diagram.html` "68 Meridian skill" | **a** | `:166`: *"canlı Meridian skill seti … güncel sayı: /api/public/summary → skills_live"*; C10 regex'i onarıldı: `SKILL_COUNT_RE` araya ≤2 sözcük kabul eder (`test_skill_cleanup_v121.py:383-387`) ve dosya tuple'da | Hem yüzey onarıldı hem kaçış yolu (regex + kapsam) kapandı |
| 21 | `workflow-diagram.html` kurulum kadrosu | **b** | Olgu `watchdog.py:2254`; `strategy.py:1050` `ARMED_SETUPS` 4'lü; `workflow-diagram.html`de `momentum_burst` geçişi YOK (grep boş), `workflow.js:38` "TAM SİLAHLANDI" der; dedektör iki dosyayı da tarar (`watchdog.py:2112`) | `silahli_kurulumlar` olgusu + kaynak da onarılmış — çifte kapak |
| 22 | `workflow.js` rejim eşiği | **a** | `:22`: *"Rejim eşiği ve sürüm SAYIYLA YAZILMAZ … yürürlükteki değer state/strategy.yaml"* — kendi vaka tarihçesiyle | Sayı yerine adres; bayatlama tarihçesi satırın içinde |
| 23 | `workflow.js` evren boyu | **a** | `:28`: *"Evren boyu SAYIYLA YAZILMAZ … yürürlükteki evren adapters/data.py REPLAY_UNIVERSE ve /api/market"* | Aynı desen (gerçek: 251 — `data.py:2622`) |
| 24 | `landing.html` tarama boyu | **c** 🔴 | `:669` "**3.000** hisseyi tarar" · `:747` "**3.000** hisse" · `:864` "tarama **2.847** hisse" — üçü de DURUYOR; maket etiketi (`:719`) yalnız cihaz-ekranı blokunu kapsar (`:715` yorumu "BURADAN AŞAĞISI" der ve o blokta biter), üç satır etiket DIŞI; gerçek evren **251** (`data.py:2622`) | **KAYNAĞI HENÜZ ONARILMAMIŞ**. C10 yalnız SKILL sayısını tarar (`SKILL_COUNT_RE`) — evren/tarama sayısına kapı yok. Sayfa kendi içinde de çelişik (3.000 ↔ 2.847) |
| 25 | `landing.html` örneklem eşiği | **c** 🔴 | `:884` "örneklem **20**'ye ulaşmadan hiçbir öneri canlıya çıkmaz" ↔ `goal.yaml:33` `min_sample: **30**` | **KAYNAĞI HENÜZ ONARILMAMIŞ**. `asgari_ornek` olgusu kod tarafını kapatır ama sunum METNİNE bakmaz; C10 regex'i skill'e özgü |
| 26 | `workflow.html` emeklilik afişi | **c** 🔴 | `:381-382` "Aşağıdaki resim **2026-07-20 sürümüdür** ve **o günden beri tazelenmiyor**" ↔ `workflow.js:38,40` 2026-08-12 tarihli içerik + `:22,28` 08-13 SONRASI onarım dili ("SAYIYLA YAZILMAZ") | **KAYNAĞI HENÜZ ONARILMAMIŞ**: afiş kendi dosyasıyla bugün 08-13'tekinden bile ÇELİŞİK — dosya iki kez tazelendi, afiş hâlâ "tazelenmiyor" diyor. Denetimin uyarısı aynen geçerli: "emekli ama bazı satırları güncel" üçüncü hâl en kötüsü. Çivi (`test_ia_v199.py`) yalnız dizgi-varlığı bakar |

🔶 = ortamlar-arası; ayrıklık bu turda damgalanamadı (canlı ölçülmedi) ama kapısızlık ölçüldü.

---

## 4. BAĞLANMAMIŞLAR — GEREKÇE + "BUGÜN AYRIK MI?"

Dokuz kalemin v245 kategorilerine dağılımı: **ortamlar-arası 3** (#2, #3, #4) · **farklı nicelik
1** (#11) · **çağrı-içi literal 1** (#16) · **kaynağı henüz onarılmamış 4** (#10, #24, #25, #26).

### 4.1 🔴 BUGÜN FİİLEN AYRIK — üç sunum yüzeyi + bir doküman cümlesi

Denetimin P0-c turu README/workflow.js/workflow-diagram bacağını kapatmış; **`landing.html` ve
`workflow.html` bacağı kapanmamış.** Dördü de tek sınıf: hiçbir şeyden türemeyen anlatı, ve mevcut
tek içerik-kapısı (C10) yalnız *skill sayısı* regex'i taradığı için yapısal olarak göremiyor.

1. **#24 — `landing.html:669,747` "3.000 hisse" · `:864` "2.847 hisse" ↔ gerçek 251**
   (`data.py:2622`). Maket etiketi (`:719`) bu satırları kapsamıyor — 08-13'te ölçülen kapsam
   sınırı aynen duruyor. Sayfa kendi içinde de çelişik (aynı iddia iki farklı sayıyla).
2. **#25 — `landing.html:884` "örneklem 20" ↔ `goal.yaml:33` = 30.** Kodun dört yüzeyi 30'da
   çivili ve olguya bağlıyken en çok okunan pazarlama cümlesi 20 diyor.
3. **#26 — `workflow.html:381` "o günden beri tazelenmiyor" ↔ `workflow.js:22,28,38,40`.** Afişin
   iddiası bugün İKİ onarım turu kadar geride: dosya 2026-08-12'de içerikçe, 08-13 denetimi
   sonrasında da "SAYIYLA YAZILMAZ" düzeltmeleriyle tazelendi. (Şiddet düşük — afişin *niyeti*
   "sayılara güvenme" ve bu hâlâ yerinde; ama "tazelenmiyor" cümlesi düpedüz yanlış.)
4. **#10 (kısmî) — `PRODUCT.md:165-167`** yeniden yazılmış hâlinde bile `equity_curve.json`u
   "gerçek sayıların tek kaynağı state/ dosyaları" listesinde sayıyor; `storage.py:1-4` onu altı
   DB varlığından biri ilan ediyor. Beş örneğin dördü doğru — cümlenin çerçevesi yanlış.

Ve bir **latent** ayrıklık: **#16 — `score.py:108` · `shadow_variants.py:532`
`goal.get("min_sample", 20)`** — yazımda 20≠30; `goal.yaml`da anahtar mevcut olduğu sürece
ısırmaz, anahtar düşerse iki modül sessizce yanlış tabana döner. P3'ün tek-satırlık "20→30"
önerisi hâlâ bekliyor.

### 4.2 Ortamlar-arası üçlü (#2, #3, #4) — dedektörün YAPISAL sınırı

`EQUIVALENT_TRUTHS`/`divergence_report` **süreç-içi** çalışır: koşan sürecin kendi ağacını ve kendi
`state`'ini okur. Repo-ağacı ↔ canlı-ağacı (#2), aynı sabitin iki ortamdaki değeri (#3'ün asıl
iddiası) ve yerel-donmuş-defter ↔ canlı-DB (#4) tek sürecin görüş alanına GİRMEZ — bu üçünün kapısı
dedektör değil, denetimin P0-b/P2 önerileridir ve **ikisi de bugün uygulanmamış** (ölçüldü:
`dagit.sh`te beyan dosyası yok; `storage.py`de `yerel_donmus_defter` simetriği yok). #3'ün
süreç-içi bacağının bağlanmış olması (canlı süreç kendi dört sayısını her raporda kıyaslar) doğru
ama KISMÎ tesellidir: iki ortam kendi içinde tutarlıyken birbirinden ayrık olabilir — 08-13'te tam
böyleydi. Bu turda canlıya bağlanılmadığı için üçünün bugünkü ayrıklığı **None** (ölçülmedi);
yerel taraflar damgalandı (repo 0,16 çevrimi eşit; yerel defter 95/390/2026-07-28'de donmuş —
08-13 fotoğrafıyla birebir, yani yerel bacak 9 gündür kıpırdamamış).

### 4.3 #11 — "farklı nicelik": bağlamamak DOĞRU karar, borç başka yerde

Dört sayı (40,0 · 30,0 · 25,0/6,0 · kapalı) dört FARKLI soruyu cevaplar: pozisyon-sayısı paydalı
maruziyet tavanı (`goal`, paydası artık açık anahtar — `guard.py:344-351`), NOTIONAL pay tavanının
arama bandı (`bounds.yaml:103`), bandın beyanlı alt-ucu varsayılanı (`guard.py:533-534`) ve
runtime'ın "kapalı" hâli. Bunları bir olguda eşitlemek, `EQUIVALENT_TRUTHS`un kendi seçim
ölçütünün (a) maddesini ihlal eder: *"yakın ama farklı tanımlı iki sayıyı eşitlemek yanlış alarm
üretir ve kapıyı işe yaramaz kılar."* Kalan gerçek borç ayrışma değil: `SECTOR_CAP_DEFAULT_PCT` /
`HEAT_CAP_DEFAULT_PCT` **bugün de okuyucusuz** (repo+test genelinde tek geçiş tanım satırları —
ölçüldü) → YASA 6 ihlali sürüyor; ya bağlanmalı ya kaldırılmalı (P3).

---

## 5. BU TURUN HÜKMÜ — TEK PARAGRAF

26 kapısız çiftin **17'si bugün güvenli** (12'si kaynağında kapanmış — çoğu "sayı yerine adres"
desenine çevrilerek; 5'i `EQUIVALENT_TRUTHS`la çalışma-anında çivili ve bugün eşit ölçüldü),
**9'u bilinçli-bağlanmamış ve gerekçeleri bugünkü kodda yeniden türetilebildi** — üçü dedektörün
yapısal sınırı (ortamlar-arası; kapısı P0-b/P2, ikisi de hâlâ yazılmamış), biri doğru bir
bağlamama kararı (farklı nicelik), biri bağlanamaz yüzey (çağrı-içi literal), **dördü ise düpedüz
onarılmamış kaynak**. Kırmızılar tek sınıfta toplanıyor: P0-c turu README/workflow.js bacağını
kapatırken **`landing.html` (3.000/2.847↔251, örneklem 20↔30) ve `workflow.html` afişi dışarıda
kaldı** — ve C10'un regex'i skill-sayısına özgü olduğu için bu sayılara yapısal olarak kör. En
ucuz kapanış hâlâ denetimin kendi reçetesi: bu satırlar ya canlı bağa ya "sayı yerine adres"
desenine çevrilir; `min_sample` yedeği tek satırla 30 olur; dağıtım-beyanı (P0-b) yazılana dek
ortamlar-arası üçlü ancak elle denetlenebilir.

---

*Envanter ajanı, 2026-08-22. Salt-okunur tur; yazılan tek dosya budur. Kanıtsız satır yoktur —
her hüküm bugünkü `dosya:satır` ölçümüne dayanır; canlıya bağlanılmadığı için ortamlar-arası
çiftlerin canlı bacağı None + nedenle bırakılmıştır, "eşit" diye uydurulmamıştır (UYDURMA YASAĞI).*
