# DENETİM — ROADMAP TUTARLILIĞI (2026-08-13 ölçüm/dağıtım dalgası sonrası)

> **Operatör talebi (2026-08-13):** "WP'lerden ve öneri havuzundan son durumda etkilenen veya
> değiştirilmesi gereken noktalar var mı, onları çıkart."
>
> **Bu belgenin yetkisi:** SALT RAPOR. `ROADMAP.md`ye tek bayt yazılmadı, hiçbir kart hükmü
> değiştirilmedi, git komutu koşulmadı, canlıya yalnız repo üzerinden salt-okuma bakıldı.
> Uygulamayı Rol-1 yapar. Her "yanlış" iddiasının altında bugünün ölçüm dosyasından `dosya:satır`
> alıntısı vardır (UYDURMA YASAĞI).
>
> **Kapsam:** `ROADMAP.md` §1 (12 WP satırı + detaylar) ve §2 (29 öneri) TEK TEK; ayrıca §3/§4/§5'in
> bugünkü bulgularla değişen kalemleri. Girdi: EDG-2026-023…039 kartları, `docs/*2026-08-13*.md`
> altı belge, canlı `state/goal.yaml` · `state/bounds.yaml` · `state/strategy.yaml`, `meridian/` kaynak.

---

## §0 · TEK CÜMLELİK HÜKÜM

ROADMAP'in **iddia gövdesi büyük oranda sağlam** ama **20 kalemi bugünün ölçümleriyle çelişiyor ya da
bayatladı**; en ağır üçü: (1) benimsenen paketin **seçim gerekçesi** (EDG-026/032'nin mutlak P&L'i)
friksiyon varsayımına asılı ve o varsayım ilk kez ölçüldü, (2) `§1` **"4 pozisyon KORUMALI"** diyor,
bugünkü ölçüm **dördü de çıplak** diyor, (3) **WP-L "kodla açılabilir kilit YOK"** diyor, §2-28
kapının ÖNÜNDE kodla açılabilir üç tıkanıklık ölçtü ve biri **bugün 17:26'da hâlâ ateşliyordu**.

---

## §A · ARTIK YANLIŞ OLAN İDDİALAR (17 kalem)

| # | Kalem | ROADMAP satırı | Şu anki hâli | Sorun — bugünkü kanıt | Önerilen yeni hâl |
|---|---|---|---|---|---|
| A1 | **WP-L: "kodla açılabilir kilit YOK"** | `:108` (özet tablo) + `:698` ("Merdivende kodla açılabilecek kilit KALMADI") | Merdiven tamamen kanıt-şartlı sayılıyor | `TESHIS-OGRENME-TIKANIKLIGI:79-81` süzgeci **tek `if`**: "arka plan turu `chop` için sertifikalıysa, GLOBAL (`@`siz) her öneri atılır"; `:72-74` "**47**, ilk ateşleme 2026-08-02T14:00, son ateşleme **2026-08-13T17:26 (bugün, hâlâ akıyor)**". `:163-164` "**`already_failed` kontrolü YALNIZCA `explore` dalının içindedir**". `:109-111` "`chop` diliminde 27 işlem, eşik 30 … Kapı burada bir yargı vermiyor; **ölçemiyor**" | "Faz-6 BEŞ KİLİT kanıt-şartlı KALIR; ama merdivenin ALT basamağı (öğrenme döngüsünün kendisi) **kodla açılabilir ÜÇ tıkanıklıkla** bloklu — §2-28a/28c/28d. WP-L artık tetik-şartlı DEĞİL, §2-28-şartlı." |
| A2 | **WP-L: "DSR 1e-06"** | `:697` | Üç kapalı kilidin sayısal gerekçesi | `EDG-2026-036…yaml:166` (aşama-2 KAPILAR): "**DSR 0,0391** (kuru koşum 0,0391 ile birebir)" — tohum yenilemesi sonrası | Sayı **0,0391**'e güncellenir + "kilit açıldı mı" ayrıca doğrulanır (bu denetim onu ÖLÇMEDİ) |
| A3 | **§1 GÜNCEL DURUM: "4 motor pozisyonu KORUMALI"** | `:79-91` (blok 2026-08-09 tarihli) | Broker'da 4 açık `P-KORUMA-…-0835` OCO var deniyor | `DENETIM-OLU-BILESEN-ENVANTERI:397-398`: "AMGN/BKNG/EMR/NUE **dördü de açık ve broker'da canlı koruyucu stop YOK** (son 7 günde her biri 6 kez, `korumasiz_motor_disi_pozisyon` **26 kez**)" | GÜNCEL DURUM bloğu 2026-08-13'e taşınır; "4 pozisyon KORUMASIZ" + §2-27 bağı; eski blok §6 snapshot'a |
| A4 | **WP-S: koruma×süpürücü "✅ KAPANDI … CANLIDA DOĞRULANDI"** | `:205-217` | Kapanmış kalem | Kapanış **süpürücünün korumayı süpürmemesi** hakkındaydı; bugün koruma **hiç kurulmuyor**. `EDG-2026-038…yaml:142-149`: "Koruma OTOMATİK yeniden kurulMUYOR"; korumasız duvar **56,4 saat**, seans-içi 2,895 sa. Ayrıca `:213-217`'nin "davranışsal EOD kanıtı Pazartesi 13:30 UTC" sözü — o Pazartesi (08-10) geçti, kayıt YOK | ✅ tarihçe olarak KALIR; WP-S'e **iki yeni açık kalem**: (i) koruma yeniden-kurulum otomatiği (§2-27 → §3), (ii) davranışsal EOD kanıtı hâlâ kayıtsız |
| A5 | **WP-E: "E3 kötümser maliyet bandı (açılış-spread ~20bps)"** | `:139-140` | Ölçülecek kalem, sayı literatürden | `EDG-2026-037…yaml:70`: "aksine **E3 kötümser bandı (+5 bps/bacak) DA iyimser çıktı (~4,5×)**"; `:79-80`: "`pessimistic_band_v2`ın `ampirik_bps: null, ampirik_n: 0` — **bugüne dek hiç ölçülmemiş, literatürden alınmış bir sayıymış**" | E3 "ölçülecek band" değil **çürütülmüş varsayım**; WP-E'nin E2/E3 satırı §2-23 hattına bağlanır (bkz. C2) |
| A6 | **WP-E / EXE-2026-001-R2: "limit-bacağı MONOTON ZARARLI · kaçanlar sistematik kazanan"** | `:122-134` + §4 `:1233-1235` | Yerleşmiş işletim-noktası hükmü (REF·limitsiz) | `ARASTIRMA-SLIPAJ-AZALTMA:349-350`: "**K1 kapanmadan yapılan her limit-tavanı ölçümü kaçan işlem maliyetini SİSTEMATİK OLARAK ABARTIR, ve 2026-08-03 E1 grid hükmü tam olarak o abartılmış maliyetle verilmiştir.**" Fırsat kanıtı `:335-345`: 100 bps tavanla EMR/BKNG/AMGN limit fiyatı aynı seansta işlem gördü | EXE-2026-001-R2 hükmüne **ŞERH**: "K1 (replayde dinlenen limit modellenmiyor) kapanana dek işletim-noktası gerekçesi ASILI". Canlı davranış DEĞİŞMEZ; değişen tek şey gerekçenin gücü |
| A7 | **RUNBOOK borcu: "32 / 31 girdi henüz yazılmadı"** | WP-P `:675` (32) · WP-S2 `:292` (31) | İki WP'nin tek canlı borcu | `grep -c "henüz yazılmadı" docs/RUNBOOK.md` = **1**, o da kuralın kendi tarifi (`RUNBOOK.md:29`). Alarm bölümleri gerçek prosedürlü: `:67` HEARTBEAT_STALE · `:168` MIRROR_DRIFT · `:304` NAKED_POSITION "KALICI RİSKLER / DERSLER" bloklu | WP-P **P-A borcu ✅ kapandı** (Rol-1 tek-doğrulamasıyla); WP-S2 ① kalemi düşer. WP-P'nin "tek canlı borç" cümlesi yeniden yazılır |
| A8 | **§2-20a: "`DD_VETO_MARGIN` 0,04'te kaldı → iki test kırmızı"** | `:924-927` | ACİL/KIRMIZI kalem | `meridian/shadowlaw.py:102` `DD_VETO_MARGIN: float = 0.08`; `state/goal.yaml:20` `max_drawdown: 0.16`; çivi `tests/test_dalga_w1_v216.py:526-528` goal/2 eşitliğini arıyor → **0,08 == 0,16/2** | §2-20a **✅ KAPANDI** (`62727d6` v238 "max_drawdown 0.16 zinciri") — arşive |
| A9 | **§2-16: "korunum dedektörü 14 AÇIKLANAMAYAN sayıyor"** | `:947-949` | 14 rakamı üzerine kurulu kalem | `EDG-2026-036…yaml:172`: "Kapının AMACI 'yenileme korunumu BOZMASIN'dı; bozmadı, **14→3 İYİLEŞTİRDİ**" | Sayı **3**'e güncellenir; kalan üçün ikisi adıyla kayıtlı (PKG-momentum_burst, ROK-exhaustion_hammer, `card:169-170`) — dedektör-tarafı `uyuyan_kurulum` kovası hâlâ gerekli |
| A10 | **§2-9: "TUZAK: … bugün nokta ekleyen yazar sınırı kaydırıp köken defterini bozar"** | `:765-771` | Gelecek-riski olarak yazılmış | Risk **gerçekleşti ve tersine döndü**. `EDG-2026-036…yaml:175-178`: "`equity_curve` YAZILMADI … Canlı eğri 2026-07-20'de duruyor (882 nokta). `ledgerstamp.seed_boundary()` bu dosyanın son nokta+mtime çiftini okuyor → **SINIR ŞU AN TOHUM-SONRASI DEĞİL**" | §2-9 metni: "adım (1) artık bir ÖNLEM değil **ONARIM** — tohum 08-13 18:54Z yazıldı, sınır 2026-07-20'yi gösteriyor". Öncelik yükselir (bkz. D1) |
| A11 | **§2-28a satır atfı `hermes.py:3889`** | `:1070-1072` | Kanıt çapası | Repo'da aynı koşul `meridian/hermes.py:4002`, olay `:4008`. Kayma **v242'nin kendi dağıtımından** (`32822c6`). `TESHIS-OGRENME-TIKANIKLIGI:148` `reflect.py:771`'i "canlı" diye etiketliyor, ROADMAP etiketsiz taşıdı | Tüm `dosya:satır` çapalarına **"canlı A1" / "repo"** etiketi zorunlu olsun; §2-28a → `hermes.py:4002` (repo) |
| A12 | **§2-11: "OPERATÖR ÖN-KARARI (2026-08-12: 'ISI 10R kalsın')"** | `:793-794` | Yürürlükteki ön-karar gibi duruyor | Ölçüm bunu aştı: `EDG-2026-028…yaml:61-65` "ÖNERİLMEZ … OPERATÖR ÖN-KARARI ('ISI 10R kalsın') **ölçümle ÇELİŞİYOR** … Rol-1 önerisi **5R'DE KAL**". Canlı: `state/goal.yaml:140` `heat_hard_r: 5.0`, `:126` "ZARF DEĞİŞMEDİ: heat_hard_r 5,0R KALDI (EDG-2026-028 zarf-10'u ölçtü ve ELEDİ)" | Satır düzeltilir: "ön-karar **ölçümle aşıldı**, yürürlükte 5R" |
| A13 | **§2-28j "explore_rate ÖLÜ" — yeni bulgu gibi** | `:1102-1103` | Bugünün keşfi olarak yazılmış | Zaten beyanlı: `state/goal.yaml:48-53` "explore_rate: BİLGİLENDİRİCİ — HİÇBİR KOD OKUMAZ (**K1 denetimi, 2026-07-30**)". Aynısı `backtest_gate` (`goal.yaml:40-46`) ve `kill_switch_file` (`:172-175`) için; WP-S2 B-1 `:311-314` bunu **✅ KAPANDI (426b998)** diye kaydetmiş | §2-28j, §2-25a'ya **birleştirilir**; açık soru "yeni ölü bulundu" değil, **"KALDIR mı, BEYANLI kalsın mı"** politika sorusu |
| A14 | **§2-20b: "KARAR GEREKİR (eşiği ölç-ve-güncelle mi, paketi mi elemek)"** | `:928-932` | Operatöre gidecek açık karar | Karar **ölçümle verildi**: `EDG-2026-037…yaml:65` "**EŞİK TARTIŞMASI KAPANDI — `RESULT_PF_MIN=1.3` GEVŞETİLMEZ**, çünkü tartışmanın yönü TERSİNE döndü"; `:66-67` "PF ek friksiyonda monoton azalandır: **1,1119 hiçbir friksiyon varsayımıyla YÜKSELEMEZ**"; `EDG-…-038:155-159` "EDG-037 hükmü **güçlenerek** durur" | §2-20b **karar kalemi olmaktan çıkar**, KAYIT olur: "Faz-6 `sonuc_hukmu` bu paketle yapısal kapalı ve bu **ARIZA DEĞİL, KORUMA** (`EDG-037:83-85`)" |
| A15 | **§5 KARAR GÜNLÜĞÜ — 2026-08-10…13 arası SIFIR giriş** | `:1271` sonrası; en yeni giriş **2026-08-09** | §0 `:20` "Neden-kaydı (kronolojik, tarihli) → §5 KARAR GÜNLÜĞÜ" diyor | Sayım (tarih histogramı): 08-09'dan sonra hiç giriş yok. Oysa arada: karar penceresinin **uygulanması**, `max_drawdown` 0,08→0,16 **operatör kararı**, tohum yenilemesi, TCA hükümleri, v237-v242 altı dağıtım. Hepsi yalnız §2 maddelerinin İÇİNDE yaşıyor | §5'e dört günlük kronolojik giriş (madde başına tek satır). Aksi hâlde §2 temizlendiğinde neden-kaydı da silinir |
| A16 | **§2-15c: "EVREN GENİŞLETME (kalan TEK kalite-nötr **debi** kolu)"** | `:846-849` | Debi (throughput) kolu varsayımı | Bağlayıcı kısıt artık ısı: `EDG-…-035:57-59` "Bağlayıcı kaynak **ısı zarfı** (gerçekleşen tepe tam 5,000R)"; `EDG-…-039:63-64` "Bağlayan kısıt **SLOT DEĞİL ISI**: 39 meşgul seansın hiçbirinde slot dolmadı (0/39)". Isı bağlıyorken isim eklemek işlem SAYISINI artırmaz; zarfı açmak ise ölçülü zararlı (`EDG-028`) | §2-15c "debi kolu" olmaktan çıkar, **seçilim-kalitesi kolu** olarak yeniden yazılır. **UYARI:** `EDG-…-026:47-49` aynı paket için "bağlayıcı kısıt **EVREN** (%99.55)" diyor — iki kart iki ayrı tasnifle **zıt manşet** üretiyor; §2-15c'nin önceliği bu çelişki çözülmeden belirlenemez (bkz. C6) |
| A17 | **Küçük çapa sürüklenmeleri** | §2-15g `:867` `guard.py:359` **doğru**; ama `state/goal.yaml:130` aynı kuralı `guard.py:352` diye anıyor · `meridian/api.py:1890` "goal.yaml:**27** slippage_bps: 5" diyor, gerçek `state/goal.yaml:58` | — | Kaynak-içi yorum çapaları bayat | Tek turda düzeltilir (kod yorumu, davranış yok) |

---

## §B · KAPANMIŞ AMA AÇIK DURAN KALEMLER (arşive/✅'ye taşınmalı)

| # | Kalem | ROADMAP satırı | Kapanma kanıtı | Önerilen yeni hâl |
|---|---|---|---|---|
| B1 | **§2-11 KARAR PENCERESİ PAKETİ** | `:786-803` | Pencere kuruldu (`docs/KARAR-PAKETI-2026-08-12.md`), beş kart da hükümlendi (023/024/025/026/027), final-paket doğrulandı (`EDG-032` 3/3 kapı), dağıtıldı: `state/strategy.yaml:1` `version: 5`, `:12` `position_size_r: 0.5`, `state/goal.yaml:131` `max_open_positions: 20`, `:140` `heat_hard_r: 5.0` | **✅ TAMAMLANDI → §6 arşiv.** Yalnız iki satırı §2'de yaşar: (i) A12 düzeltmesi, (ii) "SIRA: … hemen OPT Faz-1" → §2-10'a taşınır |
| B2 | **§2-12 ISI'nın piyasa-koşullu otomatik ayarı** | `:805-813` (öncelik: yüksek) | `EDG-2026-028…yaml:70-71`: "**DOSYA HÜKMÜ: sabit-5R + mevcut rejim kapısı kalır; kart kapanır (ölçülmüş-red)**"; Y1 rejim-harita `+3.074$` CI 0-içi → otomatik YOK, Y2 vol-hedef `−3.924$` → otomatik YOK | **✅ ÖLÇÜLDÜ-KAPANDI → arşiv.** Not: §2-10 OPT bu kalemi "boru hattının ilk müşterisi" sayıyordu — o rol boşaldı (bkz. C7) |
| B3 | **§2-15a / 15b / 15f** | `:837-845`, `:856-864` | Metinlerinde zaten "ÖLÇÜLDÜ-KAPANDI" yazıyor ama §2'nin AÇIK havuzunda duruyorlar | Kapalı alt-kalemler §6'ya; §2-15 yalnız **15c · 15d · 15e · 15g** ile kalır |
| B4 | **§2-19 TOHUM YENİLEME** | `:913-921` (öncelik: yüksek) | `EDG-2026-036…yaml:157-166` "CANLIDA UYGULANDI … 885 tohum + 2 live_paper = 887 … 7/8 GEÇTİ"; düşen kapı gerekçeli (`:167-173`) | **✅ UYGULANDI → arşiv.** Tek artık: `equity_curve` yazılmadı (`card:174-178`) → §2-9'a devredilir |
| B5 | **§2-20a** | `:924-927` | A8 | **✅ KAPANDI → arşiv** |
| B6 | **§2-23a ÖLÇÜT** | `:990` | Zaten "✅ KAPANDI" işaretli, madde içinde | Biçimsel: kapanan alt-kalem madde başına taşınmasın, §2-23'ün açık alt-kalemleri 23b-23g olarak kalsın |
| B7 | **§2-24a ÇAĞRI İZİ GERİLEMESİ** | `:1005-1007` | Metinde "(v242 turu kapatıyor)"; v242 dağıtıldı (`32822c6`) | **✅ KAPANDI** (canlı doğrulama Rol-1'de); 24b/24c/24d/24e/24f/24g açık kalır |
| B8 | **WP-S2 ① RUNBOOK 31 girdi** · **WP-P P-A 32 girdi** | `:292` · `:675` | A7 | Her ikisi ✅; WP-P'nin "WP-UX'ten AYRI TEK canlı borç" cümlesi düşer → WP-P **borçsuz** |
| B9 | **§3 OB-2 systemd exit-143** | `:1115-1118` | Zaten "✅ YAPILDI" ama §3'ün başındaki sıra cümlesi (`:1110-1112`) hâlâ "OB-2 → OB-1 → OB-4" diyor | Sıra cümlesi güncellenir: **OB-1 (bildirim kanalı) artık BLOKSUZ ve sıranın başı** |

**Not (kapanmayan, doğru duran):** §2-17'nin kalan borcu ("sürüm terfisi dagit kapsamı DIŞIDIR" prosedürü RUNBOOK'a) **hâlâ açık** — `grep "sürüm terfisi" docs/RUNBOOK.md` = 0, RUNBOOK bugün 21:58'de yeniden üretilmiş olmasına rağmen.

---

## §C · ÇAKIŞAN KALEMLER

| # | Çakışma | ROADMAP satırları | Neden çakışıyor | Önerilen çözüm |
|---|---|---|---|---|
| C1 | **§2-9 ↔ §2-18** (equity_curve) | `:765-771` ↔ `:978-984` | Aynı nesne, iki madde. §2-18 kendi metninde "§2-9'un … önceliği yükseltildi" diyor — yani zaten birbirine bağımlı | **BİRLEŞTİR** → tek madde "equity_curve zinciri", üç bacaklı: (1) `seed_boundary` onarımı [ARTIK ONARIM — A10], (2) kadanslı yazar, (3) pano reset-penceresi beyanı |
| C2 | **§2-23 ↔ WP-E (E2/E3/E5)** | `:988-1002` ↔ `:139-141` + `:97` özet | Aynı cephe: icra friksiyonu. §2-23 ölçümü yaptı, WP-E hâlâ "yüzey hazır, E1'e bağlı" diyor | §2-23 **WP-E'nin alt-cephesi** olur (ya da yeni **WP-TCA**); WP-E `:139-141` satırı §2-23'e işaret eder. §0'ın "Okuma düzeltmeleri" bloğuna (`:62-67`) **friksiyon satırı** eklenir: "replay tüm bacaklara 5 bps uygular; bar-içi stop slipajı SIFIR (`broker.py:596`) — adı konmuş iyimserlik" |
| C3 | **§2-27 ↔ WP-S ↔ §1 GÜNCEL DURUM** | `:1048-1055` ↔ `:198-266` ↔ `:79-91` | §2-27 (öneri havuzu) bir SERMAYE RİSKİ kalemi ve WP-S'in doğuş sebebiyle **birebir aynı sınıf**; GÜNCEL DURUM ise tersini iddia ediyor (A3) | §2-27 → **WP-S açık kalemi** + §3'e operatör kararı (F2). Öneri havuzunda kalmaz — canlı risk kalemi backlog'da yaşamaz |
| C4 | **§2-25a ↔ §2-28j ↔ WP-S2 B-1** | `:1022-1024` ↔ `:1102-1103` ↔ `:311-314` | Üç yerde aynı ölü anahtar ailesi; biri "✅ KAPANDI" diyor, ikisi "yeni bulundu" diyor (A13) | Tek madde: **§2-25a**. İçine not: "beyan 426b998'de indi; açık olan tek şey KALDIR-mı-BEYANLI-KALSIN-mı politikası; emsal `spy_sma_gate` mezar taşı" |
| C5 | **§2-25c ↔ kaynak belgesi** | `:1026-1033` ↔ `DENETIM-OLU-BILESEN…:346` | ROADMAP (Rol-1 düzeltmesi) **DAMGALA** diyor; kaynak belge hâlâ **DİRİLT** diyor ("Ya `loop.py`ye kablo, ya `backtest.py`den kaldır … Aradaki hâl en kötüsü") | ROADMAP §2-25c'ye açık üstün-hüküm cümlesi: "kaynak belge D-3/1 maddesi **bu satırla aşılmıştır**" — yoksa gelecek bir tur belgeden yeniden açar |
| C6 | **BAĞLAYICI KISIT: EDG-026 ↔ EDG-035/039** | `:846-849` (§2-15c dayanağı) | `EDG-…-026:47-49` "bağlayıcı kısıt **EVREN** (%99.55)" ↔ `EDG-…-035:57-59` "Bağlayıcı kaynak **ısı zarfı**" ↔ `EDG-…-039:63-64` "Bağlayan kısıt SLOT DEĞİL **ISI**". İki farklı tasnif (022 kısıt-sınıfı vs `heat_hard` NO_GO) aynı pakete zıt manşet veriyor | **UZLAŞTIRMA KALEMİ** (§2'ye yeni madde, ölçüm gerekmez — tasnif eşleme turu). §2-15c ve §3-8 FINVIZ'in önceliği buna bağlı |
| C7 | **§2-10 OPT ↔ §2-12 (kapandı) ↔ §2-28d (ölçemeyen kapı)** | `:773-784` ↔ `:805-813` ↔ `:1080-1084` | OPT'un "ilk müşterisi" §2-12'ydi ve kapandı; OPT **Faz-2** "kâğıt-OOS kapılı arama" demek, ama `TESHIS…:98` "Ağustos'ta ölçülen sonda sayısı **SIFIR**", `:109-111` "Kapı … **ölçemiyor**" | §2-10 yeniden sıralanır: **Faz-1 (kablolama) serbest**, **Faz-2 §2-28d'ye BAĞIMLI**. Yeni ilk müşteri seçilir (aday: §2-15d PIT-temiz faktör seti). OPT'un freni "PBO 0.6286" cümlesine ek: "fren ancak kapı ÖLÇEBİLİYORSA fren" |
| C8 | **§2-26 ↔ §2-20 ↔ §2-25b** | `:1042-1046` ↔ `:923-945` ↔ `:1025-1026` | Üçü de "aynı gerçek iki yerde" ailesi. §2-26'nın kapısı §2-20a sınıfını **mekanik yakalar** — nitekim yakaladı: `meridian/watchdog.py:2064-2066` "Ölçüm sırasında bir kez AYRIK yakalandı (0,04 iken goal 0,16)" | §2-26 **§2-20'nin yapısal panzehiri** olarak etiketlenir ve önceliği yükselir (D3). Doğrulandı: `EQUIVALENT_TRUTHS` bugün **4 çift** (`watchdog.py:2058/2072/2083/2096`) |
| C9 | **§2-15e ↔ §2-29** | `:854-855` ↔ `:1059-1065` | İkisi de tek yüzeye (`ARMED_SETUPS`, `strategy.py:1029`) zıt yönde dokunuyor: 15e "yeni aile ekle (kanıt-önce)", 29 "bir aile çıkar" | Tek **"ARSENAL POLİTİKASI"** başlığı altında birleştirilir; giriş ve çıkış aynı kanıt çıtasına bağlanır (29'un önerdiği "cf'de n≥30 ∧ ort-R CI-alt>0" eşiği **her iki yön** için standart olsun) |
| C10 | **§2-24f ↔ §2-25b (skill rozeti)** | `:1015-1016` ↔ `:1025-1026` | Aynı kusur: 93 skill bayrağı motor registry'sine bağlı değil, pano "gölge" diyor. `DENETIM-OLU-BILESEN…:340` bunu "**En acil damga**" sayıyor | §2-25b'nin skill satırı §2-24'e taşınır (skill katmanı tek yerde toplansın); §2-25b'de yalnız çapraz-referans kalır |

---

## §D · ÖNCELİĞİ DEĞİŞMESİ GEREKENLER

### D-a · YÜKSELENLER

| # | Kalem | Şu anki öncelik | Yeni | Gerekçe (bugünkü kanıt) |
|---|---|---|---|---|
| D1 | **§2-9/§2-18 equity_curve** `:771`, `:984` | orta-yüksek / yüksek | **ACİL** | Risk artık gelecekte değil **bugün**: `EDG-…-036:175-178` "`equity_curve` YAZILMADI … `seed_boundary()` … → **SINIR ŞU AN TOHUM-SONRASI DEĞİL**". Yani tohum yenilendi ama sistemin köken-sınırı hâlâ 2026-07-20'yi gösteriyor; kart bunun geçici çaresini de yazıyor ("o güne dek tohum sınırı `trades.kaynak` damgasından okunur") |
| D2 | **§2-28a / 28c / 28d** `:1070-1084` | ACİL / YÜKSEK / yüksek | **EN ÜST — 28a > 28d > 28c** | 28a **bugün 17:26'da hâlâ ateşledi** (`TESHIS…:72-74`); 28d tüm öğrenme ölçümünü durduruyor (`:96` tablo: Ağustos 500 sonda, **0** ölçülen, 450 `candidate_oos = NULL`); 28c tek satır ve 21 tekrarın kökü (`:163-164`). **UYARI:** 28a'nın kodu kendi gerekçesini taşıyor (`hermes.py:4003-4007`) — "tek satır aç" diye sunulamaz, kart-önce |
| D3 | **§2-26 değer-eşitliği kapısı** `:1042-1046` | yüksek | **ACİL** | §2-20a tam bu kapının sınıfıydı ve kapı onu bir kez YAKALADI (`watchdog.py:2064-2066`). Bugün 4 çift var, split denetimi **26 kapısız çift** buldu; her ekleme tek satır |
| D4 | **§2-27 koruma** `:1048-1055` | (operatör kalemi, sırasız) | **OPERATÖR-ACİL** | 4 pozisyon çıplak, `korumasiz_motor_disi_pozisyon` 26 kez (`DENETIM-OLU-BILESEN…:397-398`). Ölçülen seans-içi çıplaklık eşiği aşmadı (`EDG-038:142-149`) ama **eşik kanıt değil, tolerans** |
| D5 | **§2-23c (K1 dinlenen limit)** `:992-994` | 23c>23d>23e sırası zaten var | **§2-23'ün tamamının önceliği yükselir** | K1 yalnız gelecek kararları değil **geçmiş bir hükmü** de asıyor (A6). `ARASTIRMA-SLIPAJ…:594-596`: "**hiçbir tek seçenek tek başına yetmiyor**; 1+2+3 (ölçüm altyapısı) olmadan 4/5'in hükmü kurulamaz" |
| D6 | **§2-4 DSR girdi-serisi aracı** `:724-729` | orta | **orta-yüksek** | DSR artık anlamlı bir sayı (3e-06 → **0,0391**, `EDG-036:166`); M2'nin DSR yarısı "ölçülemez" olmaktan çıktı, araç borcu bağlayıcı hâle geldi |
| D7 | **§2-14 M8 / K-defteri** `:826-831` | yüksek-ama-odaklı | **yüksek, sıraya alınmalı** | İki günde K hızla harcandı (035 K+=6, ayrıca 036/037/038/039). U5 (beyan-K/harcanan-K) ve U6 (kart-K ↔ DSR `n_trials`) artık DSR'ı doğrudan etkiler |
| D8 | **§3-2 bildirim kanalı (OB-1)** `:1140` | operatör bloğu | **sıranın başı** | Ön-şartı OB-2 kapandı (`:1115-1118`); `docs/GECE-RAPORU-2026-08-13.md:86` "N1 bildirim kanalı (alarmlar yalnız panoda birikiyor; **12 teslim edilmemiş**)". D4'ün çıplaklık alarmı da bu kanaldan geçecek |

### D-b · DÜŞENLER / NÖTRLEŞENLER

| # | Kalem | Şu anki | Yeni | Gerekçe |
|---|---|---|---|---|
| D9 | **§2-15c evren genişletme** `:846-849` | orta | **askıya (C6 çözülene dek)** | A16 + C6 |
| D10 | **§2-10 OPT Faz-2** `:773-784` | yüksek (pencere sonrası ilk büyük iş) | **Faz-1 yüksek KALIR, Faz-2 §2-28d'ye bağımlı** | C7 |
| D11 | **§2-12** | yüksek | **kapandı** | B2 |
| D12 | **§2-20b PF eşiği** `:928-932` | yüksek (karar) | **karar değil, kayıt** | A14 |
| D13 | **§2-13 scale-out kusuru** `:815-824` | düşük (latent) | **düşük KALIR — ve TCA bunu pekiştirdi** | Scale-out ek dolum bacağı üretir; gerçek friksiyonda daha da zararlı (bkz. §E, EDG-027/029 satırları) |

---

## §E · YENİDEN OKUNMASI GEREKEN HÜKÜMLER (TCA ŞERHİ) — KART KART

### E.0 · Ayrım kuralı

> **KURAL (analitik çıkarım — ÖLÇÜM DEĞİL; `EDG-037:81-85`'in genelleştirilmesi, Rol-1 onayına açık):**
> Friksiyon varsayımı değişince
> **(i) DEĞİŞMEZ:** aynı işlem kümesinde **eşli (paired)** R farkları · oran/sayım ölçütleri ·
> bit-özdeş/inert sonuçlar.
> **(ii) DUYARLI:** kollar arasında **işlem SAYISI farklıysa** ΔP&L — her ek işlem iki bacak
> friksiyon taşır.
> **(iii) DOĞRUDAN ASILI:** mutlak seviye iddiaları (net P&L, PF, sharpe **seviyesi**).

Kartın kendi cümlesi (`EDG-2026-037…yaml:81-85`):
> "C+mb'nin **GÖRECELİ** üstünlüğü (EDG-035: yerel optimum) etkilenmez — tüm kollar aynı friksiyon
> varsayımıyla ölçüldü. Ama **MUTLAK** kârlılık iddiası (**"+20.685$"**) friksiyon varsayımına asılı
> … Faz-6 kilidinin kapalı olması **ARIZA DEĞİL, KORUMA**."

Ve zorunlu ölçüt şerhi (`EDG-037:98-100`): sağlam kalan **üç** şey — (i) slipaj 5 bps'in **belirgin**
üstünde, (ii) PF ek friksiyonda **monoton azalan** → 1,1119 yükselemez, (iii) **çıkış bacağı n=0**.
"~9 kat" ölçüt artefaktıydı; kanonikte **~7×** ve **3/4** aleyhte (`EDG-038:132-135`).

### E.1 · Kart kart ayrım

| Kart | Hükmün DAYANDIĞI ölçüt | Mutlak iddia var mı | TCA sonrası durum | Eylem |
|---|---|---|---|---|
| **023** rampa 15/36 | kill#1 işlem **sayısı** (+275, CI [+210,+342]) · kill#3 dd **oranı** ×2,287 → *invaryant* | **EVET** — `verdict.sayilar_ozet`: "A … net **−7.760$** … B … net **+775$**"; karar gerekçesi "**eksiden artıya P&L**" | n **135 vs 410** (3×) → ΔP&L kural (ii)+(iii). "Eksiden artıya" **işaret iddiası** friksiyona asılı; B'nin marjı paketinkinden ince | **ŞERH ZORUNLU** |
| **024** eşik retro | eklenen-işlem **ort-R CI**'ları (n=106/28/126) | **HAYIR** — kart mutlak "+8.826$"yı kendi eliyle reddediyor: `:50-53` "**SERAP** … Karar bu sayıya dayandırılamaz" | Eklenen işlemler ekstra friksiyon taşır → gerçek friksiyonda **daha negatif** → "eşikler doğrulandı" **GÜÇLENİR** | Şerh gerekmez. **Örnek kart** — biçim standardı olsun |
| **025** mb karnesi | ölçüt-i replay **avg-R** (+0,2695, CI 0-içi) → kıl payı düştü | **KISMEN** — ölçüt-ii "bileşik **ΔP&L +11.917$**" | ölçüt-i friksiyonla aşağı → "otomatik silahlanma yok" **GÜÇLENİR**; ölçüt-ii n-asimetrik → duyarlı | **Kısmi şerh** (ölçüt-ii'ye). Ayrıca ROADMAP'te görünmeyen bir gerçek: kart "dormant kalır" derken canlı `strategy.py:1029` `ARMED_SETUPS`'ta **momentum_burst VAR** (operatör takdiri, kartta yazılı) — §2'de açık yazılmalı |
| **026** slot20+0,5R | "C, B'ye **her eksende** baskın" | **EVET, MERKEZÎ** — "işlem 410→772 … net P&L **+775→+9.869$** (12,7×) … max-dd 0,1775→0,1235 … sharpe 0,018→**0,285**" | C ~**1,9× işlem** → ~1,9× friksiyon emer → üstünlük **daralır**; dd/sharpe **seviye** iddiaları | **EN KRİTİK ŞERH.** Benimsenen paketin **seçim gerekçesi** budur. Öneri: kart-önce tek koşumluk **friksiyon-duyarlılık taraması** (B vs C, +10/+20/+30 bps senaryolu) |
| **027** çıkış paketi | **eşli** ort-R farkları, **aynı** işlemlerde (n=371/404) | HAYIR (tam-defter sayıları yan-tablo, hüküm eşli CI'da) | Scale-out **ek dolum bacağı** üretir → gerçek friksiyonda **daha zararlı** → "alet kapalı" **GÜÇLENİR** | Şerh gerekmez |
| **028** ısı zarfı 5→10 | T10 vs C@5: +110 işlem, net 9.869→**1.266$** | EVET ama **yön lehte** | Daha çok işlem = daha çok friksiyon → "zarf-10 ÖNERİLMEZ" **GÜÇLENİR** | Şerh gerekmez (yön not düşülür) |
| **029** scale-out düzeltilmiş | eşli R farkları (−0,0530 / −0,0451, CI-negatif) | HAYIR | Ek bacak → **GÜÇLENİR** | Şerh gerekmez |
| **030** rejim eşiği | e20: +299 işlem ort-R CI 0-içi; e30 **bit-özdeş** | KISMEN (tam-defter −16,1k$) | e30 invaryant; e20 daha çok işlem → **GÜÇLENİR** | Şerh gerekmez |
| **031** turnover ağırlığı | ΔP&L CI'ları **0-içi** → null sonuç ("w=0 doğrulandı") | Nokta değerler (−3.520$ / −4.279$) var ama hüküm CI'da | Null hüküm; friksiyon işareti çevirmez | Şerh gerekmez |
| **032** final paket | Kapı: (i) ΔP&L CI-üst ≥0 · (ii) dd ≤0,16055 · (iii) **sharpe 0,521 ≥ 0,20** ← SEVİYE | **EVET, EN AÇIK** — "PAKET DAMGASI (C+mb): 885 işlem · net **+20.684,7$** · max-dd %12,7 · sharpe **0,521**" | `EDG-037:81-85` doğrudan bu sayıyı adlandırıyor; PF 1,1119 → §2-20b | **ŞERH ZORUNLU — damganın ÜSTÜNE.** Emsal hazır: `EDG-036:147-148` tohum damgasına friksiyon şerhini **zaten** ekledi; aynı metin 032'ye de |
| **033** rejim-koşullu boyut | ΔP&L CI'ları 0-içi → "düz-0,5R **kanıtla doğrulandı**" | EVET (−7.624$ / −8.897$) | **TEK YÖN-ALEYHTE KART:** h1/h2 kolları **daha AZ işlem** üretiyor (0,75R zarfı 2× hızlı doldurup C'nin ~170 işlemini yeriyor). Gerçek friksiyonda **taban** daha çok friksiyon yer → fark **daralır** → "kanıtla doğrulandı" **ZAYIFLAR** (tersine dönmez, **belirsizleşir**) | **ŞERH ZORUNLU** — dili "kanıtla doğrulandı"dan "**bu friksiyon varsayımı altında doğrulandı**"ya |
| **034** skor-sıralı kabul | FAZ-0, replay **koşulmadı**, bit-özdeşlik **yapısal** | HAYIR | **İnvaryant** | Şerh gerekmez |
| **035** yerel duyarlılık | 6/6 hücrede **CI-üstünlük düştü**; slot25 **bayt-özdeş** | EVET — `kill1_kanit` mutlak damgayı tekrarlıyor: "n=885, **+20.684,69$**, dd 0,1268, sharpe 0,521" | Zarf hücreleri işlem sayısını artırıyor (885→1052→1144) → friksiyonla **daha kötü** → "yerel optimum" **GÜÇLENİR**; ama damga 032'yle aynı maruziyette | **Kısmi şerh** (yalnız damga satırına) |
| **039** pullback silahsızlanması | ΔP&L CI 0-içi + pullback'in kendi zararı (replay −0,787R · canlı −1,00R · cf −0,97R) | Nokta ΔP&L +3.121$ var ama **n DEĞİŞMEDİ (885→885)** | **EN SAĞLAM KART:** eşit-n → ΔP&L ve sharpe farkı kural (i)'de; pullback'in zararı friksiyonla **derinleşir** → hüküm **GÜÇLENİR** | Şerh gerekmez |
| **036** tohum yenileme | — | — | Friksiyon şerhi **zaten damgalı** (`:147-148`) | ✅ örnek uygulama |

**Özet:** şerh gerektiren **6** kart — **023 · 025(ölçüt-ii) · 026 · 032 · 033 · 035(damga)**.
Şerhsiz geçerli **8** kart — **024 · 027 · 028 · 029 · 030 · 031 · 034 · 039**; bunların **beşi**
(027/028/029/030/039) gerçek friksiyonla **güçleniyor**. Yani TCA, replay hüküm gövdesinin
çoğunu **çürütmüyor** — yalnız **paketin seçim ve kabul gerekçesini** (026/032) ve **bir null
hükmü** (033) asıyor.

### E.2 · §4 ve §0'a yansıması

- §4 kart indeksi (`:1208-1246`) EDG-023…039'u **hiç taşımıyor** — dokuz güncel kart §4'te yok, yalnız §2 maddeleri içinde yaşıyor. §0 `:19` "Ölçüm ön-kaydı / hüküm → §4 KANIT/KARTLAR" diyor. **§4 indeksi tazelenmeli.**
- §4 kill-list `:1268-1269`: "knob-bileşik çıkış paketleri … **dolar merceğiyle yeniden değerlendirilecek**" — dolar merceği artık var ama friksiyon-kirli; kill-list **DOKUNULMAZ**, yalnız bu şart cümlesinin TCA'ya bağlı olduğu §4'e not düşülür.
- §0 "Okuma düzeltmeleri" (`:62-67`) replay iyimserliğini ve cf sadakat sınırını sayıyor; **friksiyon iyimserliği listede yok** → eklenmeli (C2).

---

## §F · §3 OPERATÖR BLOKLARI — DEĞİŞENLER VE EKLENENLER

| # | Kalem | ROADMAP satırı | Değişiklik |
|---|---|---|---|
| F1 | **§3-12 `goal.max_drawdown` 0.08 ↔ dd %12,4 gerilimi** | `:1167-1173` | **✅ ÇÖZÜLDÜ.** `state/goal.yaml:20` `max_drawdown: 0.16` "(OPERATÖR KARARI 2026-08-13 penceresi)". Maddedeki "0.08'e bakmaya devam ediyor" cümlesi artık tarihsel olarak yanlış. Zincir kapandı: `shadowlaw.DD_VETO_MARGIN` 0,08 (A8) → arşive, §5'e karar satırı |
| F2 | **YENİ: koruma yeniden-kurulumu otomatikleşsin mi** | (§2-27 `:1048-1055` → §3) | Operatör kararı. Kanıt: `DENETIM-OLU-BILESEN…:397-398` (4 pozisyon çıplak, 26 olay) + `EDG-038:142-149` (56,4 sa duvar; seans-içi 2,895 sa, **eşik aşılmadı**). Yön **risk-AZALTAN**; `api.py`nin kendi şerhi bu sınıfı onaya bağlamamayı savunuyor. Üç seçenek: (a) tam otomatik, (b) onay-jetonlu ama ölçüm-kapısız, (c) mevcut üç kapı kalsın + alarmı bildirim kanalına bağla |
| F3 | **YENİ: pullback silahsızlanması** | §2-29 `:1059-1065` | Şu an yalnız §2'de. **Strateji kimliği değişikliği = §3 kalemi.** §3'e taşınmalı (operatör "önce diğer işler" dedi — sırada beklediği §3'te görünsün, §2'de değil) |
| F4 | **PF eşiği tartışması** | §2-20b `:928-932` | **Operatöre GİTMEZ artık.** Ölçüm kararı verdi (A14). Operatöre gidecek olan tek cümle: "Faz-6 `sonuc_hukmu` bu paketle **yapısal olarak açılamaz** ve bu bir koruma; açılmasının yolu eşiği gevşetmek değil **icra friksiyonunu ölçüp düşürmek** (§2-23)" |
| F5 | **§3-1 NOUS_MODEL** | `:1134-1139` | Gerekçe bayat. §2-22 (v239) ölü model adını kapattı ve beyin zinciri ayrıldı; ama §2-24c: "son 7 günde **788** `agent_call`, 385 boş, **1** başarılı görüş". Karar aynı (Claude anahtarı ya da Google-dışı `NOUS_MODEL`), **gerekçe** "model adı ölü"den "**danışma yolu ölü**"ye güncellenir |
| F6 | **§3-2 bildirim kanalı (OB-1)** | `:1140` + sıra `:1110-1112` | Ön-şart kalktı → **sıranın başı** (D8). F2'nin alarmı da bu kanaldan geçecek |
| F7 | **§3-8 FINVIZ** | `:1148-1152` | De-risk hükmü (EDG-022) **geçerli kalır**; üstüne ısı-bağlayıcılık notu (A16) — ama C6 çelişkisi çözülmeden "kesinlikle gereksiz" denemez |
| F8 | **YENİ: bakım penceresi kapsamı** | `:1110-1112` | Aynı pencereye eklenmesi gereken iki iş: (i) `equity_curve` / `seed_boundary` onarımı (state'e yazar → worker durur, D1), (ii) OB-4 restart→PBO damgalama. Sıra: **OB-1 kanal → equity_curve → OB-4** |
| F9 | **YENİ: dagit kapsamı dışı canlı artefaktlar (v241/v242 dalgası)** | — (yeni) | `deploy/oracle-a1/meridian-sprint@.service`, `deploy/oracle-a1/50-meridian-sprint.rules` (polkit), SOUL.md ve tick-watchdog **`deploy/oracle-a1/deploy.sh:111-119`** ile ELLE kuruluyor. `dagit.sh`ta bu dosyalara **sıfır atıf** (`grep "deploy/oracle-a1\|SOUL\|tick_watchdog\|polkit" dagit.sh` = 0); `dagit.sh:224/267` yalnız `meridian meridian-barsarchive` durdurup başlatıyor. Bu tam olarak OB-2'yi doğuran **"kurulu ≠ çalışır"** sınıfı — dört artefakt için sürüklenme bekçisi YOK | WP-H'ye açık kalem + `dagit.sh`a repo↔canlı içerik-sha kapısı önerisi (ya da en azından RUNBOOK'a "bu dört dosya dagit kapsamı dışıdır" satırı — §2-17'nin RUNBOOK borcuyla **aynı turda**) |

---

## §G · BUGÜNKÜ TURUN ROADMAP'TE YERİ OLMAYAN ÜRÜNLERİ

| Ürün | Bugünkü kaynak | Nereye gitmeli |
|---|---|---|
| **EDG-023…039 kart hükümleri** | 17 kart | §4 kart indeksi (E.2) |
| **`incumbent` holdout −0,5366** | `TESHIS…:472-474` "`oos_score = +0,2354` · `holdout_score = −0,5366`; sapma 0,772, `reflect.HOLDOUT_DIVERGENCE = 0,10` … **savunulan tabanın kendisi holdout'ta sert negatif**" | §2-28i olarak var ama "Ayrı kalem" deyip bırakılmış → **kendi maddesi** olmalı (fold geometrisi ölçülmedi, `:475-479`) |
| **Kapının örneklem tabanı 6× büyüdü** | `TESHIS…:427-434` (~32 → ~90 → **560**); "Bu, 30 backtest-değerlendirmesinin tamamını farklı bir tabana taşır" (`:432`) | Yeni madde: **geçmiş retlerin yeniden-değerlendirilmesi** (hangi ret bugünkü örneklemle ayakta kalır?) |
| **`params_by_regime` dört harita da BOŞ** | `DENETIM-OLU-BILESEN…:184` "rejim çözümü kimlik fonksiyonu" | §2-25c'nin DİRİLT listesinde var ama §2-12'nin kapanmasıyla **yakıtsız kaldığı** görünmüyor; §2-28d ile aynı kök (chop 27<30) → **birleştirilmeli** |
| **Ölçüt-taşıma dersi** ("payda modelin paydasıyla aynı büyüklükte değilse fark model hatası değil KAYNAK farkıdır", `EDG-038:72-78`) | EDG-038 ön-kayıt | **WP-M metodoloji dersi** (`:358-366` "YENİ (…)'dan ders" serisine yeni madde) — bu ders EDG-037'nin manşetini çürüttü, kalıcı olmalı |
| **Kart biçim kusurları** | `EDG-2026-038…yaml:120` ve `:122` **iki `verdict:` anahtarı** (katı YAML ayrıştırıcı hata verir); `:118` `status: measured` satırının yorumu "ölçüm bu satır yazıldıktan SONRA koşuldu" | Kart şablonu/lint kalemi (§2 küçük madde) |

---

## §H · ÖNCELİK SIRALI EYLEM LİSTESİ

**Rol-1 kalemleri (kod/ölçüm gerekmeyen, ROADMAP hijyeni) — tek turda:**

1. **§1 GÜNCEL DURUM bloğunu tazele** (A3) — "4 pozisyon KORUMALI" cümlesi bugünkü kanıtla çelişiyor ve panonun okuduğu ilk paragraf bu.
2. **§5'e dört günlük karar kaydı** (A15) — 08-10…08-13 boşluğu; bu belge bir sonraki temizlikte silinirse neden-kaydı kaybolur.
3. **Kapananları arşive taşı** (B1-B9): §2-11 · §2-12 · §2-15a/b/f · §2-19 · §2-20a · §2-24a + WP-P/WP-S2 RUNBOOK borçları.
4. **Yanlış iddiaları düzelt** (A1 · A2 · A5 · A7 · A9 · A12 · A13 · A14 · A16) — hepsi metin.
5. **§4 kart indeksini tazele** (E.2) — dokuz kart §4'te yok.

**Şerh turu (hüküm metni, ölçüm gerekmez):**

6. **Altı karta friksiyon şerhi** (§E.1): **026 · 032** önce (paketin kendi gerekçesi), sonra **033 · 023 · 025 · 035**. Şablon hazır: `EDG-036:147-148`.
7. **EXE-2026-001-R2'ye K1 şerhi** (A6) — canlı davranış değişmez, gerekçe askıya alınır.
8. **§0'a friksiyon okuma-düzeltmesi** (C2) + **WP-M'e ölçüt-taşıma dersi** (§G).

**Kod/ölçüm turu — sıralı:**

9. **§2-28a** (görünmez süzgeç) — kart-önce; kod kendi karşı-gerekçesini taşıyor (`hermes.py:4003-4007`), "tek satır" diye sunulamaz. **Bugün hâlâ akıyor.**
10. **§2-9/§2-18 birleşik equity_curve zinciri** — (1) `seed_boundary` **onarımı** (artık önlem değil), sonra (2) kadanslı yazar. Bakım penceresi (F8).
11. **§2-28d** (chop 27 < `state/goal.yaml:33` `min_sample: 30`) — §2-10 Faz-2 ve `params_by_regime` bunun arkasında bekliyor.
12. **§2-28c** (`reflect.propose_deterministic` exploit dalında hafıza yok) — tek satır, 21 tekrarın kökü; 9/11'den sonra ölçülebilir hâle gelir.
13. **§2-26 değer-eşitliği kapısı** — her ekleme tek satır, §2-20 sınıfını mekanikleştirir.
14. **§2-23c (K1)** — kapanmadan hiçbir limit-tavanı kararı verilemez ve A6'daki şerh kalkmaz.
15. **§2-16 `uyuyan_kurulum` kovası** — kalan 3 korunum kalemini sınıflar (A9).
16. **F9 dagit kapsamı** — dört canlı artefakt için sürüklenme kapısı ya da RUNBOOK satırı.

**Operatör kuyruğu (sırayla):**

17. **F6** bildirim kanalı (OB-1) — artık bloksuz, en ucuz, F2'nin alarmını taşıyacak kanal.
18. **F2** koruma yeniden-kurulumu otomatikleşsin mi — 4 pozisyon çıplak.
19. **F3** pullback silahsızlanması (operatör sıraya aldı).
20. **F4** Faz-6 `sonuc_hukmu`nun yapısal kapalılığı — karar değil, **bilgi**.
21. **F5** NOUS_MODEL (gerekçe güncellendi) · **F7** FINVIZ (C6'ya bağlı).

---

## §I · SINIR BEYANI — BU DENETİMİN ÖLÇMEDİKLERİ

- **Canlı sisteme bağlanılmadı.** Tüm canlı iddialar bugünün ölçüm belgelerinden ve repo'daki
  `state/*.yaml` kopyalarından okundu. Canlı A1 ile repo arasındaki satır kayması **ölçüldü ve
  beyan edildi** (A11) ama tam sürüklenme envanteri çıkarılmadı.
- **Test suite koşulmadı.** A8'in "iki test artık yeşil" sonucu **assert'in okunmasından** çıkarıldı
  (`tests/test_dalga_w1_v216.py:526-528` + iki sabitin değeri), koşumdan değil. Otoriter suite Rol-1'de.
- **RUNBOOK borcunun kapandığı** (A7) tek bir `grep` sayımına dayanıyor; üretecin (`ops/runbook_uret.py:55`)
  başka bir boşluk dilini kullanıp kullanmadığı denetlenmedi.
- **§E.0 kuralı bir ÖLÇÜM DEĞİL, çıkarımdır.** Kartların friksiyon-duyarlılığı yeniden koşulmadı;
  E.1'deki "güçlenir/zayıflar" yönleri işaret tahminidir, sayı değildir. Tek gerçek yol
  §H-6'nın önerdiği friksiyon-duyarlılık koşumudur.
- **C6 çelişkisi (evren mi ısı mı bağlıyor) çözülmedi** — iki kartın iki tasnifi karşılaştırıldı,
  hangisinin doğru payda olduğu **ölçülmedi**.
- **`§2` maddelerinin numara düzeni bozuk** (1-15, sonra **21, 22, 19, 20, 16, 17, 18**, sonra
  23-27, **29, 28**) ve **§2-16'nın gövdesi §2-15'in kuyruğunu taşıyor** (`:957-959` — "NOT:
  çıkış-mühendisliği hattı BİLİNÇLİ dışarıda … *gerekçe: sharpe 0.285 …*" satırları KORUNUM-14
  maddesine değil SEÇİLİM-KALİTESİ hattına ait). Bunlar içerik hatası değil, **birleştirme
  artefaktı** — ama bir sonraki okuyucuyu yanıltır.
