# TEŞHİS — WP-E "AYNA-DOLUM AKIŞI BOŞLUĞU" (2026-08-10, SALT-TEŞHİS)

**Kapsam:** ROADMAP §1 WP-E açık kalemi — "ayna-dolum akışı boşluğu (ayrı teşhis)" (ROADMAP.md:97,
136: *"E2 defteri gerçek dolumla dolmaya devam eder; … Ayna-dolum akışının boşluğu (E2'nin öbür
yarısı) ayrı teşhis kalemi"*). Bu tur KOD DEĞİŞTİRMEZ; her iddia dosya:satır kanıtlıdır, kanıtlanamayan
yere "DOĞRULANAMADI + neden" yazılıdır.

**Ölçüm tabanı beyanı:** yereldeki `state/` CANLI DEĞİL, 2026-07-28'de donmuş bir fotoğraftır
(`state/portfolio.json.last_date=2026-07-28`; canlı A1'de). Fotoğraftan alınan sayılar yalnız
DESTEKLEYİCİ kanıttır; asıl kanıt koddur. Fotoğraf ölçümü: `state/trades.jsonl` 95 satır, 95'inde de
`alpaca_fill_price` YOK; `exit_reason` dağılımı: stop 46 · time_stop 33 · stop_gap 8 · target 4 ·
regime_flip 3 · target_gap 1. Aynı 0/95 sayısı kodun kendi beyanlarında da duruyor
(`meridian/broker.py:34` — "Canlı sonuç: 95/95 satırda `alpaca_fill_price` YOK";
`meridian/api.py:1720` — "canlı sayım 2026-07-30: 0/95"). O günkü 0/95'in ana nedeni E1-öncesi
%100 gönderim reddiydi; E1 sonrası dolumlar başladı (ROADMAP.md:131 canlı doğrulama, 08-06 dört
pozisyon) — yani aşağıdaki boşluklar artık VERİ ÜRETEN bir akışın boşluklarıdır.

---

## 1. DOLUM-AKIŞ ZİNCİRİ — UÇTAN UCA HARİTA (dosya:satır)

### 1a. Giriş emri aynaya nasıl gider
1. Plan silahlanır → `loop.mirror_submit_armed` (`meridian/loop.py:513`) → boyut makbuzu SB-1
   (`loop.py:593-596`, `meta["size_law"]`) → `alpaca.submit_plan` (`meridian/adapters/alpaca.py:694`)
   → `alpaca.submit_bracket` (`alpaca.py:289`): bracket BUY, `client_order_id = plan.id`
   (`alpaca.py:320-321`) — mutabakatın TEK birleştirme anahtarı (`alpaca.py:293-295`). TIF=GTC
   (`meridian/broker.py:82`), `extended_hours` HİÇ set edilmez (repo genelinde 0 kullanım) → emirler
   yalnız RTH'de dolabilir.
2. Gönderim anında E2 defterine `motor="ayna"`, `fill=None` satırı düşer (`loop.py:601-617`).

### 1b. Broker'da DOLUM olduğunda onu kim yakalar — İKİ KANAL
**KANAL 1 — anlık (WebSocket, salt-görünürlük):** `mirror_stream.MirrorStreamListener.session`
(`meridian/mirror_stream.py:264-289`) `trade_updates` dinler → `MirrorOrderStateMachine.apply`
(`mirror_stream.py:123-162`) → `state/mirror_orders.json`a coid başına
`status/filled_qty/filled_avg_price` yazar (`mirror_stream.py:146-154`) + `mirror_stream_event`
olayı. **Bu kanal KİTABA HİÇBİR ŞEY YAZMAZ** — okuyucuları: karar kilidi `pending_symbols_snapshot`
(`loop.py:1376-1379`), pano C1-2 emir yaşam-döngüsü `api._emir_yasam` (`meridian/api.py:2933-2982`),
akış sağlığı `_stream_view` (`api.py:3379`).

**KANAL 2 — gecelik (REST, kitaba tek giriş kapısı):** `daily_cycle` sonunda
`reconcile_broker_state` (`loop.py:1698` → `loop.py:2041`) `alpaca.orders(status="all", limit=200,
nested=True)` çeker (`loop.py:2085`; `alpaca.py:267-286`) ve dolumları ÜÇ artefakta işler:
- **(1.1) Giriş dolumu → E2 defteri:** `_patch_entry_slippage` (`loop.py:1907-1959`;
  çağrı `loop.py:2104`): `motor="ayna"`+`fill=None` satırlar `by_coid[plan_id]` ile eşlenir,
  `_entry_fill_price` (`loop.py:1890-1904`) `filled_avg_price` okur → satıra
  `fill/fill_qty/fill_status/fill_vs_resmi_acilis_bps/fill_vs_limit_bps` yazılır. İDEMPOTENT:
  `fill` doluysa bir daha yazılmaz (`loop.py:1933`).
- **(1.3) Çıkış-bacağı dolumu → trades.jsonl:** yalnız BU TURDA kapanan işlemler
  (`closed_this_cycle=b.closed`, `loop.py:1698`) için `alpaca.exit_fill_price(parent)`
  (`loop.py:2249-2251`; `alpaca.py:732-747` — parent'ın `legs[]`inden dolan TP/SL bacağını okur) →
  kilitli yama ile satıra `alpaca_fill_price + mirror_divergence` (`loop.py:2256-2282`),
  eşik aşımında `MIRROR_DRIFT drift_sinifi="icra"` alarmı (`loop.py:2260-2268`).
- **(1.2b) Pozisyon/adet mutabakatı → broker_reconcile.json:** split_brain (`loop.py:2142-2149`),
  qty_drift + SB-2 sınıflandırması `_drift_sinifi_adet` (`loop.py:2160-2173`, `loop.py:1977-2038`),
  motor_yetimi/cikis_yetimi/external (`loop.py:2177-2206`), hayaletler (`loop.py:2284-2302`),
  anlık görüntü yazımı (`loop.py:2310-2319`).

### 1c. İç kitap dolumu (ayna dolumundan BAĞIMSIZ — iki-motor yasası)
İç motor aynı planı D seansının AÇILIŞINDA kendisi doldurur: `daily_cycle`
`b.fill_entry(plan, open, …)` (`loop.py:1143-1146`; `broker.py:375-490` — dolum = açılış ×
(1+slippage) + likidite etkisi, `broker.py:455-470`) → pozisyon `portfolio.json`a `_save_broker`
ile (`loop.py:1713`, `loop.py:724-794`). Aynanın GERÇEK dolum fiyatı iç kitabın
giriş/çıkış fiyatını HİÇBİR ZAMAN değiştirmez — bilinçli tasarım (iki-motor); ayna dolumu yalnız
TELEMETRİ olarak E2 + trades-yaması + reconcile anlık görüntüsüne akar.

### 1d. Çıkış tarafı — üç ayrı yol
- **Dokunuş çıkışı (TP/SL):** iç motor `b._touch_exit` (`loop.py:1238-1240`; `broker.py:492`) —
  aynada karşılığı bracket'ın KENDİ bacağıdır, kuyruk BİLEREK kullanılmaz (`loop.py:126-128`).
- **Karar çıkışı (time_stop/regime_flip/giveback/erken-itlaf):** `pending_exits` → `b.close_position`
  + `_persist_trade` + `_mirror_exit_enqueue` (`loop.py:1093-1101`) → `_mirror_exit_sync`
  (`loop.py:146-192`) → `alpaca.close_engine_position` (`alpaca.py:576-672`): plan_id'li parent'ların
  canlı bacaklarını iptal eder (`alpaca.py:627-634`), pozisyonu `DELETE /v2/positions/{sym}?qty=`
  ile kapatır (`alpaca.py:659-660`). Başarı olayı `mirror_exit_closed` (`loop.py:175-177`).
- **Koruma-OCO çıkışı (v211):** operatör `koruma_kur` (`api.py:4362-4442`) →
  `alpaca.submit_protective_oco` (`alpaca.py:821-882`), coid `P-KORUMA-YYYYMMDD-HHMM-SYM`
  (`alpaca.py:803-818`) — plan_id'den FARKLI bir anahtar.

### 1e. Pano nasıl görür
`broker_reconcile.json` → `/api/diagnostics` (`api.py:3376`) + `/api/alpaca` panosu
(`api.py:4052-4053`) + bekçi #10 tazelik (`meridian/watchdog.py:2495-2546`); E2 →
`analytics.entry_execution_summary` (`meridian/analytics.py:3846`) → `/api/diagnostics` `slipaj`
(`api.py:3592`); trades-yaması → `api._slippage_measured` (`api.py:1712-1735`, çağrı `api.py:1808`);
anlık emir durumu → `api._emir_yasam` (`api.py:2933`); nabız `mirror_drift` bayrağı
(`loop.py:1811`).

---

## 2. BOŞLUK SINIFLARI (8 sınıf — her biri: kanıt · tetik · etki · düzeltme yönü)

### B1 — `karar_cikisi_dolum_korlugu` (EN KRİTİK)
**Ne:** Karar-çıkışlarının (time_stop/regime_flip/giveback — fotoğrafta kapanışların %38'i, 36/95)
aynadaki GERÇEK dolum fiyatı HİÇBİR deftere akmaz — yapısal olarak akamaz.
**Kanıt:** (a) kapatma `DELETE /v2/positions` ile yapılır (`alpaca.py:659-660`) — bu, coid'i
Alpaca-üretimi olan YENİ bir market emri doğurur; `close_engine_position` dönüşünde yalnız
`closed_qty` var, dolum fiyatı OKUNMAZ (`alpaca.py:668`). (b) `mirror_exit_closed` olayı da fiyatsız
(`loop.py:174-177`). (c) trades-yaması (1.3) fiyatı YALNIZ `by_coid[plan_id]` parent'ının
`legs[]`inden okur (`loop.py:2250-2251`; `alpaca.py:739-747`) — karar-çıkışında o bacaklar az önce
İPTAL edilmiştir (`alpaca.py:631-634`), `filled_avg_price` taşımazlar → `af=None` → `continue`
(`loop.py:2252-2253`), sayaçsız-sessiz atlama.
**Tetik:** her karar-çıkışı (`MIRROR_EXIT_KEY` yolu).
**Etki:** `trades.jsonl` karar-çıkışı satırları KALICI olarak `alpaca_fill_price/mirror_divergence`siz
→ `api._slippage_measured` örneklemi sistematik olarak yalnız TP/SL-bacağı dolumlarına yanlıdır;
"ölçülen slipaj vs varsayılan 5bps" sorusu (K1) çıkışların bu dilimi için asla cevaplanamaz.
E2'nin "öbür yarısı"nın (çıkış-icra defteri) en büyük deliği budur.
**Düzeltme yönü (uygulanmadı):** `close_engine_position` DELETE cevabındaki emir gövdesini (order id)
döndürüp kuyruğa "bekleyen dolum yaması" kaydı bıraksın; reconcile o order id'yi `orders`tan bulup
trades satırına yamasın (E2 giriş-yamasının simetriği). Alternatif: kapatmayı coid'li bir market
emriyle yapmak (sahiplik + eşleşme tek hamlede).

### B2 — `tek_atis_yamasi` (yeniden-deneme yüzeyi yok)
**Ne:** Çıkış-dolum yaması (1.3) yalnız AYNI TURDA kapanan işlemlere bakar; kaçırdığı satırı bir
daha ASLA denemez. Giriş yarısı (E2) ise her tur defteri tarayıp `fill=None` satırları yeniden
dener (`loop.py:1932-1938`) — iki yarı ASİMETRİKTİR.
**Kanıt:** `closed_this_cycle = b.closed` (`loop.py:1698`); `b` her turun başında sıfırdan yüklenir
(`loop.py:1071` → `_load_broker` `loop.py:691-702` — `closed` alanı geri YÜKLENMEZ;
`broker.py:345` `self.closed=[]`). Ayrıca iki arıza dalı (1.3)'e hiç varmadan döner: emir listesi
arızası (`loop.py:2092-2098` `return out`) ve pozisyon listesi arızası (`loop.py:2125-2133`
`return out`) — o turda kapanan işlemlerin yaması SONSUZA DEK kaybolur.
**Tetik:** (a) kapanış turunda geçici Alpaca API arızası; (b) iç dokunuş-çıkışı ile ayna bacağının
FARKLI GÜNLERDE dolması (bar kaynağı ↔ gerçek piyasa ayrışması: iç bar stop'a değdi, gerçek piyasa
ertesi gün değdi).
**Etki:** `mirror_divergence` örneklemi sessizce incelir ve "temiz-API günleri"ne yanlı hâle gelir;
(b) hâlinde ek belirti — iç kapalı/ayna açık pozisyon `motor_yetimi` alarmı yer (aşağıda B8-not).
**Düzeltme yönü:** (1.3)'ü `closed_this_cycle`dan koparıp E2 deseni gibi "trades.jsonl'da
`alpaca_fill_price`sız son N satır" üzerinden yeniden-denemeli yapmak (sınırlı pencere + idempotent
yama zaten var: `loop.py:2257`, `2277`).

### B3 — `koruma_oco_dolumu_zincir_disi`
**Ne:** Koruma-OCO'nun (v211) dolumu — yani pozisyonun aynada GERÇEKTE nasıl kapandığı — dolum
zincirinin HİÇBİR halkasına bağlanmaz, üstelik mutabakatta YANLIŞ SINIF üretir.
**Kanıt:** koruma coid'i `P-KORUMA-…` (`alpaca.py:803-818`), plan_id'den farklı; (1.3) eşleşmesi
yalnız `by_coid.get(tr["plan_id"])` (`loop.py:2250`) → koruma dolumu orada görünmez. (1.2b): koruma
dolduğu an ayna pozisyonu kapanır, iç kitap hâlâ açıktır → sembol `a_by_sym`de yok + koruma emri
`filled` olduğu için `alive_order_syms` dışı (`loop.py:2135-2136`) → `missing_on_alpaca` →
`drift_sinifi="split_brain"` alarmı (`loop.py:2142-2149`) — gerçek sebep ("koruma bacağı doldu,
iç motor henüz çıkmadı") HİÇBİR sınıfta yok. E2/trades tarafında koruma dolumunun fiyatı hiçbir
satıra yazılmaz (tek izi Kanal-1 `mirror_orders.json` + `koruma_oco_gonderildi` olayı,
`api.py:4424-4427`).
**Tetik:** korumalı pozisyonda stop/hedef seviyesine dokunulması.
**Etki:** kitap/karne: iç kitap kendi bar-similasyonuyla (farklı gün/fiyat) kapanır, gerçek çıkış
fiyatı kaybolur; alarm: her turda yanlış-sınıflı `split_brain` gürültüsü, gerçek split-brain
vakalarının okunurluğunu düşürür.
**Düzeltme yönü:** reconcile'a koruma-farkındalığı: `is_koruma_order` (`alpaca.py:394`) dolmuş
koruma emirlerini sembolle eşleyip (a) `drift_sinifi="koruma_dolumu"` diye ADLANDIRSIN,
(b) `filled_avg_price`ını ilgili trade satırına/bekleyen-yama kuyruğuna bağlasın.

### B4 — `koruma_x_cikis_kuyrugu_carpismasi` (v220'nin kardeşi — dolumun İCRA bacağı)
**Ne:** Korumalı bir pozisyonda iç motor karar-çıkışı verirse, ayna kapatması YAPISAL olarak
başarısız olur: `close_engine_position` yalnız `plan_id` eşleşen parent'ların bacaklarını iptal
eder (`alpaca.py:616-618` — `(plan_id is None or coid == plan_id)` süzgeci koruma OCO'sunu DIŞARIDA
bırakır); koruma OCO'nun canlı satış bacakları hisseleri rehin tutar; ardından gelen
`DELETE /positions?qty=<tam adet>` (`alpaca.py:650-660`) reddedilir.
**DOĞRULANAMADI notu:** "açık satış emirli pozisyonda DELETE reddi" Alpaca API davranışıdır, bu
depodan kanıtlanamaz (repo kendi yorumunda aynı mekanizmayı 'hisseler açık satış emirlerince
tutulur ve kapatma insufficient qty ile reddedilir' diye beyan ediyor — `alpaca.py:599-600`);
canlıda tek GET/senaryo ile doğrulanmalı.
**Tetik:** `koruma_kur` kurulmuş pozisyon + `pending_exits` (aynı kombinasyon 08-07 süpürücü
vakasının ikizidir: koruma, kendisini tanımayan İKİNCİ bir mekanizmayla çarpışıyor).
**Etki:** `cikis_yetimi` her tur alarm + sonsuz yeniden deneme (`loop.py:150-151` tavan bilinçli
yok); pozisyon ancak koruma kendi (bayat) seviyesinden dolunca kapanır — o dolum da B3 gereği
hiçbir yere akmaz; kuyruk ancak "pozisyon kalmadı" dalıyla boşalır (`alpaca.py:651-656`).
**Düzeltme yönü:** `close_engine_position` parents süzgecine koruma ailesini dahil etmek
(`is_koruma_order(o) and o.symbol==sym` → bacakları iptal listesine) — sahiplik kanıtı zaten
`P-` önekinde; ya da kapatmadan önce sembolün canlı koruma emirlerini ayrı adımda toplamak.

### B5 — `kismi_dolum_sinifsiz`
**Ne:** Kısmi dolum senaryosu üç halkada da yanlış/eksik işlenir.
**Kanıt:** (a) E2 yaması `partially_filled`i dolum sayar (`loop.py:1896`, doğru) ama idempotens
`fill is not None` olduğundan (`loop.py:1933`) İLK fotoğraf donar — parent sonraki seans(lar)da
dolmaya devam ederse (`fill_qty`/ortalama fiyat değişir) satır ASLA güncellenmez. (b) günlük süpürücü
kısmi-dolmuş parent'ı BİLEREK yaşatır (`alpaca.py:548-555` — `filled<=0` koşulu; kept "dolmuş/kısmi
parent") → bayat tetikli GTC kalanı günler sonra dolabilir; bu geç dolum E2'ye (satır donmuş) ve iç
kitaba (tam adet zaten yazılmış) görünmezdir. (c) SB-2 adet-sapması sınıflandırıcısında
`kismi_dolum` diye bir sınıf YOK — kısmi dolum ancak `olculemedi`nin gerekçe METNİNDE geçiyor
(`loop.py:2036-2038`); eq/çarpan kıyası tesadüfen tutarsa sapma yanlışlıkla `boyutlama_tabani`/
`derisk_carpani`ya yazılır (B6 ile birleşik).
**Tetik:** açılışta limitin kısa süreli/kısmi teması; ince likidite.
**Etki:** E2 slipaj dağılımı kısmi dolumlarda yanlış (ilk-parça fiyatı "the fill" sanılır); kitap
adedi ile ayna adedi arasında sınıfsız sapma; >%25 ise yanlış-adlı alarm.
**Düzeltme yönü:** yamada `fill_status=partially_filled` satırları donmuş sayma (terminal olana dek
tazele); `_drift_sinifi_adet`e makbuz/emir `filled_qty vs qty` okuyan bir `kismi_dolum` dalı.

### B6 — `fill_eq_now_anakronizmi` (dolum-anı tabanının bugünle ikamesi)
**Ne:** SB-2 sınıflandırıcısına "DOLUM anının boyut tabanı" diye geçirilen `fill_eq_now`, gerçekte
"BU TURUN açılış öz sermayesi"dir; adet sapması ise BÜTÜN açık pozisyonlar için (dolumu günler/haftalar
önce olanlar dahil) her tur ölçülür — yaşlı pozisyonda sınıflandırıcı, dolum gününün tabanı diye
BUGÜNÜN tabanını kıyaslar ve sebep UYDURur.
**Kanıt:** `fill_eq_now=eq_now` (`loop.py:1709`) = D açılış markı (`loop.py:1115`); 1.2b döngüsü
TÜM `local` pozisyonları gezer (`loop.py:2139`), her qty_drift'te AYNI `fill_eq_now` ile sınıf türetir
(`loop.py:2164-2166`); `Position` dolum-günü sermayesini TAŞIMAZ (`broker.py:473-487` alan listesi),
SB-1 makbuzu yalnız GÖNDERİM anını taşır (`loop.py:593-596`). Sonuç: beş gün önce dolan pozisyonda
`"gönderim eq_now X ≠ dolum eq_now Y → boyut tabanı gönderim↔dolum arasında kaydı"` cümlesindeki Y
(`loop.py:2020-2023`) dolum gününün değil BUGÜNÜN sayısıdır — sermaye dolumdan SONRA oynadıysa sınıf
`boyutlama_tabani/derisk_carpani` diye yanlış adlandırılır.
**Tetik:** >%25 adet sapması taşıyan (kalıcı — adet değişmez, her tur yeniden alarmlanır) herhangi
bir yaşlı pozisyon + dolum sonrası ≥1$ sermaye hareketi.
**Etki:** SB-2'nin varlık sebebi "belirtiye SINIF söylemek"ti (`loop.py:1965-1970`); bu dal tam
tersini yapar — depo teamülündeki "çalışıyor ama kendini yanlış raporluyor" sınıfının ta kendisi.
**Düzeltme yönü:** iç dolum anında makbuza ikinci yarıyı damgalamak (`size_law[plan_id]["dolum_eq"]`
— `fill_entry` çağrısının olduğu yerde, `loop.py:1143`) ve sınıflandırıcıyı onu okutmak; damga yoksa
yaşlı pozisyon için dürüst `olculemedi`.

### B7 — `pencere_bosluklari` (limit=200 + işlenmeyen seans günleri)
**Ne:** Kanal-2'nin görüş alanı iki eksende sınırlı: (a) `orders(status="all", limit=200)` — en yeni
200 üst-düzey emir (`loop.py:2085`; `alpaca.py:275` — `after` parametresi YOK, sayfalama YOK): 200'ü
aşan bir boşlukta (uzun kesinti + yoğun emir trafiği) daha eski dolumlar `by_coid`e hiç girmez → E2
satırı sonsuza dek `fill=None` kalır ve `dolmama_orani` benzeri okumalarda "dolmadı" sanılır
(E2 yeniden-deneme yüzeyi bunu normalde kapatır ama pencereden taşanı kapatamaz); (b) `noop`
(`loop.py:1072-1084`), `waiting_for_universe` (`loop.py:1030-1035`), `refused_regressive`
(`loop.py:1042-1045`) dalları reconcile'a HİÇ varmadan döner — gün içi dolumlar o gün yalnız
Kanal-1'de (kitap-dışı) yaşar, `broker_reconcile.json` önceki seanstan konuşur (skip-yazıcı yalnız
broker/paper_available dallarını kapsar, `loop.py:2069-2080`).
**Tetik:** (a) çok-günlük kesinti/tatil + emir yoğunluğu; (b) her gün-içi poll (bilinçli EOD kadansı)
ve kapsama/monotonluk beklemeleri.
**Etki:** SINIRLI ve kısmen bekçili: #10 tazelik bekçisi seans-gerisi/96 saati alarmlar
(`watchdog.py:2495-2546`) ama SEANS-İÇİ gecikme tanım gereği bekçi-dışıdır; (a) hâli sessizdir.
**Düzeltme yönü:** (a) için `after=<son işlenen tur>` parametreli sayfalama ya da E2'de "pencere-dışı,
hüküm yok" beyanlı ayrı durum; (b) mevcut kadans bilinçli — yalnız belge/beyan.

### B8 — `motor_yetimi_kabul_yolu_yok` (giriş tarafında C9'un karşılığı eksik)
**Ne:** Ayna, iç motorun DOLDURMADIĞI bir girişi doldurduğunda (motor yetimi) akış ALARMDA BİTER:
pozisyonu ne iç kitaba alan ne aynada kapatan bir yol vardır; sembol süresiz `_mirror_busy`de kalır.
**Kanıt:** yetim tespiti + alarm (`loop.py:2189-2195`), karar kilidi (`loop.py:1373-1375`) — ama
`orphans` için hiçbir eylem yolu yok (çıkış tarafının kuyruğu C9 ile kuruldu, `loop.py:114-129`;
giriş tarafının simetriği kurulmadı). Yetim üretebilen gerçek yollar kodda mevcut: iç `missed_limit/
max_chase` düşürmesi sonrası aynanın gün içi dolumu (`broker.py:430-439` iç ret; ayna emri ancak
akşam süpürülür `loop.py:1205`, gün içinde dolmuşsa süpürücü ona dokunMAZ `alpaca.py:552-555`),
slot/kapı düşürmeleri (`loop.py:1181-1192`), taşınan plan (`loop.py:955-976`) — taşınan planın ayna
dolumu ertesi güne dek "yetim" görünür (armed küme yetim süzgecine BAKILMAZ, `loop.py:2189`).
**Ek yanlış-sınıf notu (B2 ile bağlı):** iç dokunuş-çıkışı dolmuş ama ayna bacağı henüz dolmamışsa
oluşan "iç kapalı / ayna açık" hâli de AYNI `motor_yetimi` adıyla alarmlanır — üç ayrı olgu
(giriş-yetimi · çıkış-gecikmesi · taşıma-gecikmesi) tek isim altında okunamaz hâle gelir (C9'un
kendi gerekçesinin — `loop.py:123-124` "iki teşhis aynı isimle sayılırsa ikisi de okunamaz" —
giriş tarafındaki ihlali).
**Etki:** aynada YÖNETİLMEYEN gerçek pozisyon (stop'u bracket'ta ama trail/karar katmanı yok);
kalıcı alarm gürültüsü; huninin sembol kilidi.
**Düzeltme yönü:** operatör kararı gerektirir (kabul-mü-kapat-mı politikası); asgari teşhis adımı
yetim sınıfını üçe ayırmak (`giris_yetimi/cikis_gecikmesi/tasima_gecikmesi`) ve armed kümesini
süzgece katmak.

---

## 3. YASA-6 DENETİMİ — dolum olayları hangi artefakta yazılıyor, okuyucusu kim?

| Artefakt / olay | Yazar | Okuyucu | Hüküm |
|---|---|---|---|
| `state/mirror_orders.json` (`filled_avg_price` dahil) | `mirror_stream.py:120,146-154` | `api._emir_yasam` (`api.py:2943,2961-2971`) · `_stream_view` (`api.py:3379`) · `pending_symbols*` (`loop.py:1378`) | OKUYUCULU — ama dolum fiyatı KİTAP zincirine bağlı değil; REST penceresi kaçırdığında yedek olarak KULLANILMIYOR (B2/B7 ile bağ) |
| `state/entry_execution.jsonl` (E2, `fill` yaması) | `loop.py:48-63,1907-1959` | `analytics.entry_execution_summary` (`analytics.py:3846`) → `/api/diagnostics` `slipaj` (`api.py:3592`) | OKUYUCULU (sağlam zincir) |
| `trades.jsonl` `alpaca_fill_price/mirror_divergence` | `loop.py:2256-2282` | `api._slippage_measured` (`api.py:1712-1735`, çağrı `api.py:1808`) | OKUYUCULU ama AÇ: yapısal besleme boşlukları B1/B2 yüzünden örneklem yanlı/boş (yerel fotoğraf 0/95) |
| `broker_reconcile.json` | `loop.py:2310-2319` | `api.py:3376,4052` · `watchdog.py:2515` · `loop.py:1373` | OKUYUCULU |
| **`out["entry_slippage"]` sayaçları (`eslesen/yazilan/acilis_yok`)** | `loop.py:2104` üretir | **YOK** — `broker_reconcile.json` yazımına girmiyor (`loop.py:2310-2319` anahtar listesinde yok), loglanmıyor, dönüş değeri `daily_cycle`da yalnız `mirror.get("drift")` okunuyor (`loop.py:1811`) | **OKUYUCUSUZ ÜRETİM** — özellikle `acilis_yok` (resmî açılışsız dolum) açlığı görünmez; YASA-6 ihlali sınıfında |
| `mirror_exit_closed` olayı | `loop.py:175-177` | olay defteri/gelen kutusu | OKUYUCULU ama EKSİK YÜK: `qty/tries` taşır, DOLUM FİYATI taşımaz — fiyat o anda `close_engine_position`da da yok (B1'in olay-katmanı yüzü) |
| `koruma_oco_gonderildi/dusuru` olayları | `api.py:4424-4432` | olay defteri/gelen kutusu (beyanlı, `api.py:4422`) | OKUYUCULU — ama koruma DOLUMUNUN karşı-olayı hiç üretilmiyor (B3) |

**YASA-6 net bulgu:** tek okuyucusuz yazım `entry_slippage` yama-sayaçlarıdır (loop.py:2104 →
hiçbir artefakt/olay); ikincil bulgu "okuyucusu var ama beslemesi yapısal aç" zinciridir
(`alpaca_fill_price` → `_slippage_measured`), ki bu da api.py:1716-1717'nin kendi tespitiyle
("ölçülen sapmayı geri besleyen tüketici YOKTU") birleşince E2'nin çıkış yarısını fiilen ölçüsüz
bırakır.

---

## 4. ÖNEM SIRASI + HÜKÜM

1. **B1** karar-çıkışı dolum körlüğü (çıkış-icra defterinin yapısal deliği; kapanışların ~%38'i)
2. **B2** tek-atış yaması (B1'i temiz vakalarda da büyütür; arıza günü kalıcı kayıp)
3. **B4** koruma×çıkış-kuyruğu çarpışması (canlı koruma kullanımı arttıkça tetiklenir; v220 dersi
   üçüncü mekanizmada tekrar ediyor)
4. **B6** fill_eq_now anakronizmi (SB-2'nin ürettiği sebep yaşlı pozisyonda uydurmadır)
5. **B3** koruma-OCO dolumu zincir dışı (yanlış `split_brain` sınıfı + kayıp gerçek çıkış fiyatı)
6. **B5** kısmi dolum sınıfsız · 7. **B8** motor-yetimi kabul yolu yok · 8. **B7** pencere boşlukları

**Tek cümle hüküm:** Ayna-dolum akışının giriş yarısı (E2 + yeniden-denemeli yama) sağlam kurulmuş;
çıkış yarısı ise yalnız "aynı-tur bracket-bacağı" dar vakasını görüyor — karar-çıkışı, koruma-OCO,
geç-dolan bacak ve kısmi dolum sınıflarının GERÇEK dolumları ya hiçbir deftere akmıyor ya da yanlış
sınıf adıyla akıyor; sistem bu dilimde "çalışıyor ama kendini yanlış raporluyor" sınıfındadır.

## 5. DOĞRULANAMADI LİSTESİ
- Alpaca'nın açık-satış-emirli `DELETE /positions` davranışı (B4'ün reddi) — dış API semantiği;
  repo yorumu (`alpaca.py:599-600`) destekliyor ama canlıda ölçülmedi.
- Seans-dışı dolum senaryosu: `extended_hours` hiçbir emirde set edilmediği (repo genelinde 0
  kullanım) ve emir tipleri stop/stop-limit/OCO olduğu için "RTH-dışı dolum" bu emir sınıflarında
  Alpaca tarafından üretilmez varsayımı — dış API semantiği, koddan tam kanıtlanamaz; mevcut
  yapıda ayrı bir boşluk sınıfı olarak SAYILMADI.
- Canlı A1 defterlerinin güncel dolum sayıları (E2 satır sayısı, 08-06 sonrası yama oranı) — bu tur
  ssh/canlı erişim kapsam dışı; yereldeki fotoğraf 2026-07-28'de donuk.
