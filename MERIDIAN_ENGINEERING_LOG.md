# MERIDIAN ENGINEERING LOG
Her oturumun BAŞINDA önce bu dosya okunur (§8 protokolü, 2026-07-30'da operatör kurdu).
İçerik bir İPUCUDUR, gerçek-kaynak değildir — koda karşı doğrulanmadan güvenilmez.
Tur notlarının kronolojik defteri ROADMAP.md §7'dedir; bu dosya "şu an gerçekte ne var ve ne açık" fotoğrafıdır.

---

## HEDEF SÖZLEŞMESİ (yürürlükte — 2026-07-30, operatör mandası)

1. **Ölü mekanizma sıfır:** Repodaki her mekanizma ya bir üretim kadansına kablolu, ya
   geri-alınabilirlik notuyla emekli, ya da adı+gerekçesiyle "operatör kalemi" olarak belgeli.
   Doğrulama: ölü-mekanizma avı (workflow) yeniden koşulduğunda "wire" kovası boş çıkar.
2. **Öğrenme katmanı operatörsüz döner:** antrenman (sprint + shadow_model fit/terfi), kanıt
   dolgusu (390'lık görüş kuyruğu), Eksen-2 beceri önerileri ve bütçe/k-max ayarı otomatik
   kadansta; elle tetik yalnız hızlandırma. Doğrulama: bir hafta operatör dokunuşu olmadan
   learning_scorecard sayaçları (dolgu kalanı ↓, kalibrasyon n ↑, sprint noktaları ↑) akar.
3. **Kanıt debisi maksimum dürüst seviyede:** aynı-akşam SIP verisi + gölge-v2 kitapları (k=6) +
   keşif-dengeli üreteç birlikte canlıda; seans atlama yalnız gerçek kaynak-arızasında.
   Doğrulama: `alpaca_sip` damgalı barlar + shadow_trades satırları + bakir-düğme önerileri akıyor.
4. **7/24 dürüst gözlemlenebilirlik:** sistem A1'de kendi başına; pano gördüğünü doğru anlatıyor
   (boş kart "aç" olduğunu söyler, arıza gibi görünmez); süreç ölümü operatöre ulaşır (kanal
   kimliği girilince). Doğrulama: operatör pano bulgusu listesi (§3.0) kapanmış.
5. **Edge araştırması çok-aileye genişler — Y4 sinyal aileleri ilk vatandaş olur (2026-07-30
   operatör onayı):** insider Form-4 ve short-interest verisi yalnız toplanmakla kalmaz, ÖLÇÜLÜR
   (G2 deseni: bileşen IC + Fisher CI, tarihsel geri-doldurma ile) ve IC gerçekse ailenin sinyali
   hipotez makinesine default-off düğmelerle girer. Doğrulama: Y4 IC tablosu üretildi; en az bir
   Y4 bileşeni prescreen'e aday oldu YA DA "edge yok" hükmü ölçümle kayda geçti — makine tek
   aileye mahkûm değil. Sıra sonrası aday aileler: transkript-LLM skoru, 13F uzun-ufuk.

## SİSTEM HARİTASI (gerçek, 2026-07-30 23:5x itibarıyla)

- **Koşum yeri:** Oracle A1 (ubuntu@130.61.126.87, 4 OCPU/12GB aarch64, anahtar ~/.ssh/oci-a1.key).
  systemd: `meridian` (uvicorn 127.0.0.1:8080, worker in-process, OnFailure→fail-notify),
  `meridian-barsarchive`, `meridian-backup.timer` (23:30 UTC), redis-server (localhost).
  Pano erişimi SSH tünel. Mac tarafı: LaunchAgent `com.meridian.backup-pull` (21:40, VM-dışı yedek).
  YERELDE ./serve.sh KOŞULMAZ (çift emir). Dağıtım: scratchpad/push_code_a1.sh (kod rsync,
  state'e dokunmaz) — paralel oturum dersi: rsync tüm repoyu taşır, dağıtımdan önce dry-run.
- **Veri hattı:** Massive grouped-daily (T+1, otoriter) + Alpaca same-evening bacağı
  (sip birincil — canlı kanıtlı; iex+kalibrasyon yedek) + onarım geçidi (son 5 seans) +
  zaman-tabanlı merdiven (terminal atlama yalnız sonraki kapanışta). FMP yalnız bilgi katmanı.
  Kaynak damgaları bar_same_evening.json; T+1 düzeltme watchdog'un rev-bump yolundan (sanctioned).
- **Karar çekirdeği:** PARA-v3 yasası (skor=para, düşüş→veto), K-cezası, R1 penceresi (donmuş
  holdout 2026-04-30→07-30), DSR/PBO mod-farkındalıklı kilitler, Faz-6 beş kilit (kapalı).
- **Öğrenme:** hermes zinciri (nous/gemini; claude bacağı kimliksiz), keşif-dengeli üreteç
  (ölü aileler + bakir düğmeler istemde; propose_virgin_knob deterministik yuvada) [YEREL,
  DAĞITILMADI], gölge-v1 karar defteri (k=4) + gölge-v2 yaşam-döngüsü kitapları (k=6) [CANLI],
  Nous katman A-D (haftalık öz-değerlendirme), sprint.py (kum-havuzlu antrenman — otomasyonu
  uçuşta), shadow_model (n=2201 birikmiş, fit kadansı uçuşta).
- **Durum dosyaları:** state/ yalnız A1'de canlı; Mac'teki kopya taşıma anı fotoğrafı.

## BU OTURUMDA BULUNAN + ÇÖZÜLEN (kök nedenleriyle)

- **CANLI-BEKÇİ YANLIŞ ALARMI, bounds.yaml (2026-08-02; sınıf: "git-izli dosyada mtime sızıntıyı
  değil git trafiğini ölçer"):** KATMAN-2 bekçisi `test_scheduler_flag_survives_publish_lag`
  teardown'unda `['bounds.yaml']` ile düştü; şüphe test alt-süreçlerine (hermes CLI + mcp_server)
  gitti. KÖK NEDEN TESTLER DEĞİL: `state/bounds.yaml`+`state/goal.yaml` git-İZLİdir (dagit [1b]
  SSoT, c783442) ve ana checkout'taki paralel oturum git işlemleri onları repo-içeriğiyle birebir
  yeniden yazar. Kanıt üç bacaklı: (a) inode adliyesi — goal doğum 14:28:04, bounds doğum 18:01:21
  + yerinde yazım 18:06:34, içerik `.git/index` blob'uyla birebir; (b) zaman çizgisi — ilk yazım
  günün İLK hermes boot'undan (18:01:28) önce; (c) aklama — sitecustomize audit-hook tüm Python
  alt süreçlerinde + 0,2sn mtime poller ile iki tam tekrar koşumu (worktree + ana checkout),
  84 test ×2 yeşil, canlı bounds'a SIFIR yazım denemesi. İKİ KAPI (conftest, kapsam
  test_canli_bekci_v176): izli iki dosyada parmak izi mtime→içerik-sha256 (içerik farkı hâlâ
  düşürür; alt-dizin muaf değil) + autouse `_hermes_bin` saplaması (gerçek CLI keşfi testlere
  kapalı — gerçek Gemini kotası, ~/.hermes yazımı ve MERIDIAN_ROOT=ana-checkout sabitli MCP alt
  süreci; testin enjekte ettiği HERMES_LOCAL_BIN onurlandırılır, çözümleyici testi bilinçli
  istisna). CLAUDE.md §8'e istisna notu düşüldü. AVDA BULUNAN AÇIK KALANLAR: (1) aynı scheduler
  testi gerçek kadansla NASDAQ'a çıkıyor (`earnings.refresh` — ağ nondeterminizmi, ayrı tur);
  (2) hermes/nous süpürmesindeki 34 kırmızı worktree-state-boşluğu sınıfı, taban ölçümüyle bu
  turdan bağımsız kanıtlandı (onarımlı/onarımsız FAILED kümeleri birebir aynı). SINIF-AİLESİ
  BAĞI (operatör talimatı, 2026-08-02 pencere kapanışı): bu vaka ile "paralel-oturum rsync'i"
  dersi (660dc10 kaydı — EDG-016 oturumunun `--uygula`sı, pencere oturumunun az önce merge'lediği
  main'i HABERSİZ taşıdı: kayıt b857f48 derken fiilen 6545c6a içeriği canlıya gitti) AYNI
  ÇATININ altındadır: "ana checkout'taki paralel oturum trafiği, paylaşılan durumu — izli state
  dosyası ya da canlıya giden ağaç — habersiz yeniden yazar". Sınıf avı iki vakayı tek çatıda
  görmeli: tek-oturum varsayımı taşıyan her mekanizma (bekçi mtime'ı, dağıtım kaydının "hangi
  tepe taşındı" beyanı) bu ailenin adayıdır; pencereyi koşan oturum dağıtım ANINDAKİ main
  tepesini kaydetmeli.

- **T+1 ritim kusuru (sınıf: "kaynak yayın gecikmesi varsayımı kodda örtük"):** 8×300sn refetch
  bütçesi FMP'nin akşam-yayınına göre yazılmıştı; kota tahsisi Massive'e (T+1) geçince her seans
  40 dk'da terk edildi (164 birikmiş atlama, %17 kapsama). Çözüm: same-evening bacağı + merdiven
  + onarım geçidi. SINIF avı yapıldı mı: kısmen — "zaman varsayımı" sınıfının diğer örnekleri
  (bararchive TTL, sprint pencereleri) bilinçli tarama görmedi → AÇIK (aşağıda).
- **Gölge-v1'in çıkış körlüğü:** giriş-kararı defteri çıkış düğmelerini ölçemiyordu → gölge-v2
  yaşam-döngüsü motoru (fill→yönetim→çıkış→mark, PaperBroker'ın kendisiyle; iki payda k=4/k=6).
- **Eksen-2 ölü zinciri:** beceri önerisi üreticisi (reflect.propose_deterministic →
  skills.recommend_from_attribution) hiçbir üretim yolunda değil → 0 öneri. Kablolama uçuşta.
- **Elle-tetik öğrenme katmanı:** sprint, shadow_model fit, backfill (390/390 görüşsüz plan),
  bütçeler statik → otomasyon turu uçuşta.
- **Panodaki "10 bekleyen" yanılsaması:** app.js inbox_count yokken pending_count'a düşüp planı
  "karar" diye etiketliyor; canlı gerçek 0. Düzeltme pano turunda.
- **sed placeholder uyuşmazlığı (sınıf: "sessiz sıfır-etkili sed"):** runbook token sed'i yanlış
  desendi — bilinen placeholder'la canlıya çıkardı. cutover.sh desen-doğrulamalı yapıldı.
- **rsync --delete-excluded tuzağı:** uzak state'i silerdi; ajan kendi yakaladı, sade --delete.
- **launchd TCC:** ~/Documents'taki SSH anahtarını launchd okuyamıyor → ~/.ssh/oci-a1.key kopyası.
- 46 bulguluk ölü-mekanizma avı (5 mercek + çürütme): triyaj ROADMAP §7 + §3.0'da.
- **fail-notify birimi hiç çalışmamıştı (sınıf: "systemd'de çok-satır gömülü Python"):**
  test-ateşleme IndentationError yakaladı — systemd `\` devamı baş boşlukları -c dizgisine katıyor;
  worker ölse ve kanal kurulu olsa bile bildirim gitmezdi. Tek-satıra çevrildi, A1'de yeniden
  test-ateşlendi: exit 0 + beyanlı NO-OP satırı journal'da. Sınıf avı: repo'daki diğer birimler/
  betikler tek-satır -c kullanıyor, başka örnek yok. DERS: her OnFailure/oneshot birimi kurulduğu
  gün test-ateşlenir — "kurulu" ≠ "çalışır".

- **ÖĞRENME REHİNELİĞİ (öğrenme-otomasyonu turu, kök düzeltme):** "fit çağrılmıyor" teşhisi
  YANLIŞTI — P5_LEARN her döngüde koşuyordu ama daily_cycle veri kapsaması yüzünden noop olunca
  öğrenme de sessizce onunla duruyordu (rehinelik, ve durduğu hiçbir yerde yazmıyordu). Yani veri
  düzeltmesi = öğrenme düzeltmesi. Ek: dolgu kuyruğunun gerçek boyutu 95 (sonuçlu planlar; 386
  görüşsüzün 291'i sonuçsuz — kalibrasyon çifti sonuç ister), türetilmiş tavan ~46/gece → ~3 gece.
  Eksen-2 üreticileri hipotez-yan-ürünü rehineliğindeydi → bağımsız skills.axis2_cycle();
  yapısal körlük bulundu: eşik cf katmanını okumuyor (n_cf=1080/1004'lük iki skill görünmez) —
  cf-kolu tasarımı temizlik turunda. sprint_runs "orphan"ı okuyucu hatasıydı (defter sandbox'ta,
  status() yanlış rafa bakıyordu — düzeltildi).

- **Y4 İLK ÖLÇÜM (madde 5 açılışı):** short-interest 24 ay/49 settlement/12.250 kayıtla ölçüldü —
  **EDGE YOK** (12 hücrenin 0'ı sınırı geçti; kılpayı hücre likidite-vekili çıktı, FINRA/yerel
  delta ρ=1.00 → etkin sınama ~6). Prescreen'e BAĞLANMAYACAK; si_delta_pct_local bileşen
  listesinden düştü. Insider: **ÖLÇÜLEMEDİ** (FMP ücretsiz: page≥1→402, date sessizce yok
  sayılıyor; yalnız page=0/100-dosyalama anlık görüntüsü) — "edge yok" DEĞİL; yol: plan yükseltme
  veya SEC EDGAR çeyreklik setleri (dosya indirme operatör onayı). fetch_delta sayfalama yolu
  ücretsiz planda ölü — kadans page0-only olmalı (temizlik ajanına iletildi).
- **HAYALET SEANS (Y4'ün yan bulgusu, sınıf: "takvim doğrulaması yok"):** 2025-05-26 Memorial Day
  258/259 CSV'de seans olarak duruyor (çoğu önceki günün kopyası; 5 sembolde bölünmemiş ham fiyat
  — BKNG +%2598 hayalet getiri); 2018-11-22 aynı sınıf. sanitize aynı-tarihe, split_suspect
  soft'a takılıyor → component_ic.json + cf + R-tabloları KİRLİ. Sınıf düzeltme ajanı uçuşta
  (takvim kapısı + karantina + onarım CLI); onarım + türetilmiş artefakt yeniden-üretimi yarınki
  dağıtımın migrasyon adımı.

- **DE-RISK RAMPASI KEŞFİ (çıkış-paketi ölçümü, 2026-07-31 — kuraklığın gizli ortağı):**
  `broker.max_positions_at` (tepe-DD %3→kıs, %8→sıfırla) incumbent'ta günlerin %92,4'ünde AKTİF;
  P3 kolunda %92 gün izin=1. Döngü ölçüldü: yavaş çıkış→eğri tepe altı→izin 1→işlem çöküşü (71→28).
  Eşikler bounds'ta DEĞİL kodda sabit → hipotez uzayının körü. P3 imzası 4/4 (ödeme 1,53→2,84,
  beklenti 0,104→0,287R, DD %4,6→%0,5) — "reddedildi ama çürütülmedi"; sıradaki tur: rampa
  eşikleri bounds'a + sabit-rampa yeniden-ölçüm + profit_target_r/time_stop "kapalı" değerleri.
  AYRICA: canlı-defter (ödeme 0,97) vs Search-OOS (1,53) şiddet farkı açıklanamadı — WP0'ın
  iki-motor bulgusuyla birleşen icra/uyum sorusu. Prescreen raporlarına kod-sürümü damgası önerisi.
- **EAP ARŞİVLENDİ (4/4 aday aile elendi):** +9,0bps CI[−13,3·+31,9] (eşik 30); güç-yeterli
  12,6-yıl genişletmede +6,8bps; PK-1 kesin. YAN BULGU → kart-adayı: KIYAS KİRLENMESİ (olay
  penceresinde evrenin %64-74'ü kendi penceresinde — tüm "evren-medyanı" ölçümleri sıkışık).

- **systemd `Environment=` satır-sonu yorumu tuzağı (2026-08-02; sınıf: "birim dosyasında
  kabuk-sözdizimi varsayımı" — fail-notify'ın çok-satır-Python vakasıyla aynı aile):**
  meridian.service'te `MERIDIAN_DASH_TOKEN=...token   # ASCII zorunlu (bkz. api._auth)` — systemd
  satır-sonu yorumu desteklemez, `#` sonrasını boşluklarla ayrı `VAR=VAL` atamalarına böler;
  geçersizler journal'e "Invalid environment assignment, ignoring" düşürür. Fiilî arıza YOK (ilk
  atama geçerli, token doğru kuruluyordu) — kusur, doğru görünen ama okunmayan yorum + journal
  gürültüsü. Çözüm: yorum üstteki blok yoruma katlandı; C1'in BIND_HOST çivisi GENELLENDİ —
  yeni test dosyadaki HER `Environment=` satırında `#` yasaklıyor
  (tests/test_kovab_kucuk_v165.py). Sınıf avı: deploy/ + ops/ tarandı, başka ihlal yok.
  Commit 4d695ff; A1'e dağıtım bakım penceresini bekliyor (o güne dek canlıdaki eski satır
  zararsız gürültü üretmeye devam eder).

- **İki ölü token-bekçisi (2026-08-02; sınıf: "sessiz sıfır-etkili adım" — sed-placeholder
  vakasının İKİNCİ kuşağı):** H3 tur-2 `CHANGEME` placeholder'ını birimden çıkarınca deploy.sh:96
  `grep CHANGEME` uyarısı ve cutover.sh adım 5/6'nın desen-bağımlı sed'i SESSİZ NO-OP'a düştü —
  taze kurulum/cutover panoyu TOKEN'SIZ canlıya çıkarırdı. Çözüm: iki betik de artık desen değil
  DOSYANIN KENDİSİNİ ölçüyor — `/opt/meridian/.dash.env` yok/boşsa üretilir (openssl rand -hex 24;
  RUNBOOK B.3 / bakim_h9.sh:59 deseni), doluysa DOKUNULMAZ (habersiz rotasyon yasak), izinler her
  koşuda ubuntu:ubuntu+0600'e sabitlenir, sonuç dolu+0600 doğrulanır (değilse exit 1 — cutover'ın
  sed-vakası doğrulama disiplini korunuyor). `.dash.env` dagit.sh rsync'inden dışlanmış kalır
  (2026-08-01 --delete vakası) → dosya SUNUCUDA doğar, taşınmaz. RUNBOOK'un sed-vakası notu
  iki-kuşaklı anlatıma güncellendi. Doğrulama: 78 çivi-testi yeşil (h3_tur2 + uiux_s1b + v132) +
  cutover snippet'inin 4-senaryolu şim-koşumu (yok→üret·0600 / dolu→bayt-özdeş / 0644→izin-onarımı
  / boş→yeniden-üret). DERS (sınıfı genelleştirir): bir bekçinin aradığı DESEN başka bir turda
  kaynaktan kalkarsa bekçi test edilmeden ölür — bekçiler durumu (dosya/uç-nokta) ölçmeli,
  yokluğu sessizliğe eşitlenen izleri değil.

- **EDG-016 kanıt zinciri kopuktu (2026-08-02; sınıf: "hüküm kanıtı silinebilir dizinde" — kart
  depodaki yolu gösterir, baytlar scratchpad'de yaşar):** Kartın SUCCESS hükmü `sonuc_016.json +
  RAPOR_016.md`'yi gösteriyordu; 511f1c1 o ikisini kurtarmıştı AMA kod damgası
  (`kod_damgasi_016.json`) ve damgaladığı beş betik yalnız /private/tmp scratchpad'inde kalmıştı —
  scratchpad silindiği gün damga doğrulanamaz hash listesine, hüküm tekrar-üretilemez iddiaya
  dönerdi. Sınıf avı İKİNCİ vakayı buldu: 012–014 turunun kodu da (depodaki kod_damgasi.json'un
  hash'lediği k012/k013/k014/rapor/birlestir.py) aynı kaderdeydi. 11 dosya kaynakta VE hedefte
  damga SHA-256'larıyla birebir doğrulanıp `research/olcumler/wp2_olcum/` arşivine alındı
  (039c5b8 → merge 06e8f60); `dagit.sh --uygula` ile A1'e dağıtıldı (kapılar yeşil; bounds/goal
  canlı=repo BİREBİR; A1'de 13 dosyanın uzak SHA-256'sı birebir — sonuc_016/RAPOR_016 önceki
  dağıtımla zaten canlıdaydı). Kart taraması başka eksik kanıt yolu bulmadı; panel ara-dosyaları
  bilinçli dışarıda (damgasız, girdilerden yeniden üretilebilir). DERS (sınıfı genelleştirir):
  "measured" statüsü kanıt+damga+kod ÜÇLÜSÜ depoya girince tamamdır — damga kodsuz yaşayamaz;
  güncel ölçüm dizinleri (kys_olcum, wp1_rvol_form, wp_u_midcap) bunu zaten yapıyor, wp2_olcum
  geleneğin öncesinde kalmıştı, hizalandı.

- **`takvim_yok` zinciri KAPANDI (WP-D'nin bilerek ertelenen kalemi, 2026-08-02):** `gap_scan`in
  üçüncü hâli panoda WP-P'yle tanınmıştı (e3edaf0: `_GAP_DURUM` girdisi + bilinmeyen-durum
  "hüküm VERİLMEDİ" dalı, çivisi v171'de); scheduler kancası eksikti — rapor ölçülmüş-sonuç
  dalına düşüyor, arıza nedenini taşıyan `seans` bloğu state'e hiç girmiyor ve hâl olay
  defterinde SESSİZdi. Çözüm (`scheduler._intraday_gap_check`): erken-dönüş listesine
  `takvim_yok` + `seans` kopyası YALNIZ bu hâlde (pano teşhisi; diğer iki hâl bit-bit aynı) +
  süreç başına BİR `gap_scan_calendar_unavailable` uyarısı (emsal `_CALENDAR_WARNED`; 300 sn
  poll'de koşulsuz uyarı 288 satır/gün ederdi). Çivi: v175 (3 test; kırmızı-önce dört geri-alma
  senaryosunda fiilen doğrulandı). A1'e sıradaki bakım penceresiyle iner.

- **PAZAR-AKŞAMI PENCERESİ KAPANDI — takvim_yok kalemi CANLIDA; `--uygula` BİLEREK atlandı
  (2026-08-02 ~19:25 UTC, Rol-1, operatör talimatlı):** otoriter suite donmuş `6545c6a` tepesinde
  **3969/0** (18:40 dk, ana checkout) + dagit kapıları yeşil (audit ✓ · lint-imports 5/5 KEPT ·
  [1b] bounds/goal canlıyla BİREBİR). Dry-run delta'sı yalnız 2 lint-cache satırı çıkınca ölçüldü:
  EDG-016 oturumunun 19:05 UTC `--uygula`sı, 18:30/18:37 UTC'de merge'lenmiş main çalışma ağacımızı
  taşımıştı (rsync-tüm-repo sınıfı, bu kez İYİ huylu: taşınan ağaç TAM commit'liydi) —
  scheduler.py A1-yazımı 19:05:15, servis başlangıcı 19:05:18 → KOŞAN worker yeni kodla doğdu.
  O pencerenin kapı-suite'i bu ağacı kapsamıyordu; boşluğu bu oturumun post-hoc otoriter suite'i
  (aynı içerik, 3969/0) kapattı. İkinci restart'ın kanıt desteği yoktu → `--uygula` atlandı (boş
  işlem canlıda gereksiz kesinti). CANLI DOĞRULAMA: healthz 200 · scheduler_status ilerliyor
  (19:05:50) · `akis_boslugu={"durum":"seans_disi","gun":"2026-08-02"}` — yeni üç-anahtarlı
  minimal kopya sözleşmesi canlıda (v175 test-3'ün çivisi). `sitecustomize.py` kancası sahibi
  hungry-jemison tarafından ~18:44 UTC'de silindi + yeniden doğrulandı — pencere-öncesi bekçi
  maddesi görevini yaptı, kuyruk kaydıyla birlikte kapandı (KUYRUK BOŞ; kayıt bu commit'te
  silindi). DERS (sınıf: paralel-oturum rsync'i): bir oturumun `--uygula`sı, başka oturumun az
  önce merge'lediği main'i HABERSİZ taşıyabilir — pencereyi koşan oturum dağıtım ANINDAKİ main
  tepesini kaydetmeli (EDG-016 kaydı b857f48 derken fiilen 6545c6a içeriği taşındı).

## DAĞITIM PENCERESİ PLANI — TAMAMLANDI (2026-08-02; pencere 14:00 UTC, kapanış ~15:00 UTC)

**Kapsam:** main tepesi (şu an 892bf75) + inecek v76 fikstür onarımı. İçerik: KOVA-B dalgaları
(84fcf69..6aba956) + icra-bloğu merge'i (46ce02f: E2 `kapi` kovası, E2/E3/E4 pano okuyucuları) +
RUNBOOK (892bf75) + birim düzeltmesi (4d695ff — migrasyon adımı aşağıda). Restart yan-etkisi:
emekli-sembol modülü devreye girer (payda 259→251) — BEKLENEN, doğrulama maddesi var.

**Sıra ve kapılar:**
1. v76 fikstür onarımı iner (diğer oturum, Opus uçuşta). Kontrol: onarım FİKSTÜRDE — eşik/assert
   gevşetilmedi.
2. **FREEZE:** onarım inince main donar — iki oturum da yeni KOD commit'i atmaz (hüküm/log serbest,
   açık yol listesiyle). Freeze beyanı bu bölüme tek satır işlenir.
3. Dağıtım-öncesi TAM SUITE (Rol-1, tek-otoriter, ana checkout, arka plan görevi → dosyadan okuma).
   Hedef 0 kırmızı. YALNIZ girişim-ailesi (izole-yeşil, v72 sınıfı) düşerse: izolasyon kanıtı +
   karar OPERATÖRE (beyanlı kapı "yeşil suite"; Rol-1 tek başına gevşetmez). Başka kırmızı → dağıtım
   YOK, tur açılır. Referans: 2026-08-02 akşam koşusu (merge'li main) 7 kırmızıydı = 6×v76 + uiux-t3
   (t3 892bf75 ile kapandı; girişim ailesi o koşuda hiç ateşlenmedi).
4. `./dagit.sh` onaysız kısım: temiz-ağaç + uv audit + lint-imports + rsync DRY-RUN. Dry-run GÖZLE
   okunur: beklenen küme (meridian/ tests/ docs/ deploy/ ops/ + kök belgeler) dışı satır varsa DUR
   (paralel-oturum yarım-iş dersi).
5. Bakım penceresi: `./dagit.sh --uygula`. Zamanlama: Pazar akşamı veya Pazartesi seans açılışından
   (13:30 UTC) ≥3 saat önce; 23:30 UTC yedek zamanlayıcısına bindirme yok (pencere ~5 dk, piyasa
   kapalı). KOVA-B dağıtım yetkisini operatör açtı; pencere SAATİ yine de operatöre bildirilir
   (restart istisnası operatör kalemi).
6. **BİRİM MİGRASYONU (pencere içinde, rsync sonrası, start öncesi — EN RİSKLİ ADIM):**
   /etc/systemd/system/meridian.service KOPYADIR (deploy/oracle-a1/deploy.sh:89 `sudo cp`) — rsync
   + daemon-reload 4d695ff'i İNDİRMEZ. TOKEN KORUMA ZORUNLU (sed-placeholder vakası sınıfı: repo
   şablonunda CHANGEME var, canlı kopyada gerçek DASH_TOKEN): (a) eski birim yedeklenir
   (`meridian.service.bak-20260802`), (b) canlıdan mevcut token çekilir, (c) repo birimi cp'lenir,
   (d) CHANGEME → MEVCUT token, (e) İKİ YÖNLÜ desen doğrulama: CHANGEME kalmadı + token bayt-özdeş,
   (f) daemon-reload. Doğrulama: journal'de "Invalid environment assignment" YOK + tünelden token'lı
   tek GET çalışıyor (token DEĞİŞMEDİ).
7. dagit.sh [5] + genişletilmiş doğrulama: healthz 200 · meridian/barsarchive/tick-watchdog aktif ·
   scheduler_status.updated ilk 30 dk tazeleniyor (asılı-tick sınıfı) · /api/diagnostics'te
   `icra.slipaj.kapi` alanı VAR · evren paydası 251 · pano mutabakat sayfası dört kartı basıyor
   (boş-hâl metinleri "ölçüm yok" ≠ 0 doğru) · fail-notify beyanlı NO-OP aynen.
8. Log kapanışı: DAĞITIM BLOKE kaydı kapatılır; pencere sonucu + doğrulama çıktıları işlenir.

**DESTEKLEYİCİ KOŞU (2026-08-02 gece, diğer oturum — otoriter koşunun yerine geçmez):** izole
worktree (da6bec3 + state fotoğrafı kopyası) tam suite: **2 failed / 3750 passed** —
v76 6'lısı YEŞİL, girişim ailesi bu koşuda da ateşlenmedi (ikinci bağımsız kanıt). İki kırmızı
ortam artefaktı, ikisi de dağıtımı bloklamaz ama ikisi de bulgu: (1) c1[shadow] —
`skills/_emekli/shadow/` BOŞ ve git-izsiz dizin, yalnız Mac diskinde; "taşındı-silinmedi"
güvencesi git'ten yeniden üretilemiyor (skill-temizlik sahibine: tombstone'a README/`.keep` +
versiyonlama önerisi). (2) uiux-t3 SINIFI: runbook §AÇIK KALANLAR günlüğün AYNASIDIR —
günlüğe atılan HER commit aynı commit'te `ops/runbook_uret.py` koşulmazsa t3'ü yeniden kırar
(892bf75 bir kez kapattı, sonraki log commit'i yine açtı; bu commit'te yeniden kapatılıyor).
DERS adayı: t3'ü kıran şey belge değil KADANS — log-edit + regen tek atomik alışkanlık olmalı.

**TOPLU PENCERE KAPANDI (2026-08-02 ~19:55 TR / 16:55 UTC, Rol-1, tam-otonom):** WP programının
tüm mühendislik+ölçüm dalgası tek pencerede canlıya indi. Zincir: otoriter suite SIFIR kırmızı
(~3.821; ilk koşum 2 çivi-kırmızısı onarımla kapandı — getsource-taşınma + alias-beyanı) →
dagit [1b] versiyonlu-state hükmü İKİ DOSYADA KOPYALA (w_turnover + E1/E3/limits.heat_* canlıda
İLK KEZ doğdu; yedekli, bayt-özdeş) → rsync+restart healthz 200 → H3-t2 B3: üç birim migre,
tur-1 drop-in söküldü, systemd-analyze **2.0 OK ×3** (6.3'ten), HERMES-RW-OK + PROTECTHOME-OK
probları, yedek-birimi ✓, SIGSYS 0 (24-saat nöbeti başladı). CANLI ETKİLEŞİM KANITI: state
kopyasından saniyeler sonra `hermes_bg_proposal_rejected variable=entry.w_turnover bg_regime=chop`
— yeni knob + C16 rejim-sınırı birlikte doğru çalıştı. BEKLEYEN TEK KABUL: inceleme-kaydı
(2026-07-31) — -Q düzeltmesi canlıda ama Gemini GERÇEK günlük kotası öğleden sonraki
ayrıştırılamayan-döngüde tükendi (cooldown 7200s); kota dönüşünde (~07:00 UTC) ilk poll
kanıtlar, izleyici kurulu. Hükümler: EDG-017 ARŞİV (3 kill) · EDG-018 askıya:veri-kapısı
(%96,6 çıkış-ismi barsız — delist-bar kararının fiyat-etiketi) · KYS-001 ARŞİV (yanlılık
pratik-önemsiz; temiz-kıyas opsiyonel).

**FREEZE KALKTI (2026-08-02 ~17:40 TR / 14:40 UTC, Rol-1 pencere-oturumu):** korunan boru hattı
TAMAMLANDI — otoriter tam suite `571a094` tepesinde SIFIR kırmızı (exit 0) + `./dagit.sh --uygula`
14:00 UTC'de operatör talimatıyla ("bitince otomatik uygula ve doğrula") koştu: 5 kapı yeşil,
healthz 200, app.js md5 birebir; bakım penceresinde agent_budget sıfırlandı (yakılan 150 hak ağa
hiç çıkmamıştı — gerekçe dosyada). YENİ AÇIK TUR (operatör: "kök nedeni bulunca düzeltmeyi de
uygula"): LLM ikinci-görüş cevabı DOLU gelirken kayda geçmiyor — görünürlük düzeltmesi
`candidate_review_empty_parse` (hermes.py + test_review_gorunurluk_v168) bu commit'le iniyor;
worker'ın bir sonraki poll'ü üretim-özdeş tanı olacak, kök neden olayla görünecek. Paralel oturuma
not: dağıtım YAPILDI; adım 3-5 tekrarı gereksiz (aynı içeriği yeniden dağıtmak zararsız ama boş).

**ADIM 7 DOĞRULAMASI YEŞİL (2026-08-02 ~14:50 UTC, Rol-1 — A1 canlıda, tümü salt-okur):**
üç birim aktif (meridian · barsarchive · tick-watchdog.timer; restart 14:00:34 UTC) · healthz 200 ·
journal restart-sonrası 48 satırda 0 "Invalid environment assignment" (pozitif kontrollü — birim
düzeltmesi CANLIDA) · birimde CHANGEME yok; token `.dash.env` kanalında (48 kr; değer okunmadı,
yazdırılmadı) ve `x-meridian-token` ile API 200 → token KORUNMUŞ (plan adım-6 endişesi yapısal
olarak çözülmüş: birim artık token taşımıyor) · scheduler_status.updated=14:30:22Z, yaş 0,7 dk —
restart'tan beri İLERLİYOR (canlılık ve ilerleme ayrı ayrı var) · /api/diagnostics: `icra.slipaj.kapi`
VAR (n=0, dağılım {} — dürüst boş hâl) + kotumser_band + gece_gunduz VAR · evren:
universe_drift/universe=251, retired_in_universe=0 (payda 259→251 GERÇEKLEŞTİ) · servis edilen
app.js YENİ paket (kapi_dagilimi içeriyor) · fail-notify birimi repo ile bayt-özdeş. SON MÜHÜR
(operatör, ~15:00 UTC): pano tünelden açıldı, DÖRT KART DOĞRU BASIYOR — PENCERE KAPANDI. Adım 8
tam: BLOKE kaydı kapalı, freeze kalkık, iki oturumun işi tek pencerede canlıda.

**FREEZE İLAN EDİLDİ (2026-08-02 ~16:50, Rol-1):** donan KOD tepesi `571a094` (içerik: v76 onarımı
da6bec3 ✓ fikstür-yalnız/eşiksiz doğrulandı + 65/65 bağımsız teyit · guard turu 014bc78 ·
destekleyici koşu + runbook yenilemesi 5aaef3d · ROADMAP dersleri). Ağaç temiz, aktif test süreci
yok. Bu noktadan sonra yeni KOD commit'i YOK; hüküm/log commit'i serbest — ama t3 kadans dersi
gereği log-edit + `ops/runbook_uret.py` TEK commit'te. Adım 3 (otoriter suite) bu tepede başlatıldı.

**ADIM 3-4 TAMAM (2026-08-02 ~17:15, Rol-1) — OPERATÖR PENCERESİ BEKLENİYOR:** otoriter suite
donmuş tepede **3752 passed / 0 kırmızı** (9:26; girişim ailesi ateşlenmedi, ortam artefaktı yok).
dagit.sh onaysız kısım yeşil: audit ✓ · lint-imports 5/5 KEPT ✓ · dry-run delta YALNIZ 3 doküman
(log/ROADMAP/RUNBOOK) + 2 lint-cache — kod A1 diskine önceki gece itilmişti (push_code_a1.sh),
KOŞAN süreç hâlâ eski; restart birikimi tek seferde etkinleştirir ve yeşil suite tam bu ağacı
kapsıyor (kod tepesi 571a094-özdeş; freeze sonrası tek commit bc08cc8 ROADMAP-yalnız). t3 tepede
ayrıca teyitli (37/37). KALAN: operatör pencere saati + `./dagit.sh --uygula` + adım 6 birim
migrasyonu (token-koruma) + adım 7 doğrulama listesi.

**Geri alma:** kod: yerelde önceki tepeye checkout + `./dagit.sh --uygula` (≈5 dk; state'e
dokunulmaz). Birim: adım 6(a) yedeği geri kopyalanır + daemon-reload.

**Roller:** v76 onarımı + (gerekirse) girişim avı = diğer oturum · freeze beyanı, otoriter suite,
dagit.sh koşusu, log kapanışı = Rol-1 (bu oturum) · pencere saati onayı + --uygula anı = operatör.

## AÇIK KALANLAR (bilinçli, sahipli)

- **DAĞITIM BLOKE — ÇÖZÜLDÜ (2026-08-02: yeşil suite 3752/0 donmuş tepede → pencere 14:00 UTC →
  adım-7 doğrulaması yeşil; ayrıntı §DAĞITIM PENCERESİ PLANI). Tarihçe aynen korunuyor:**
  operatör KOVA-B dağıtımını açtı; dagit.sh kapıları (audit+lint-imports) yeşildi ama dağıtım-öncesi
  tam suite 16 failed / 2 error / 3688 passed verdi → --uygula KOŞULMADI, canlı eski kodda.
  Ayrıştırma: (a) 7'si İZOLE de kırmızı = GERÇEK; bunlardan RUNBOOK eşitliği (uiux t3) yeniden-üretimle
  kapandı; kalan 6'sı test_learning_roundtrip_v76 — fikstür kanıt tabanı 17 < min_sample 30 →
  par_score None → rollback zinciri kademeli çöküyor ("örneklem kuraklığı → no_parent_score" sınıfı).
  Tarihleme DÜZELTİLDİ (ilk iddia "≤90a6663" HATALIYDI — kıyas ağacı rebase sonrası olduğundan
  ayrıştırıcı değildi; bisect ile kesinleşti): kök 0a4453f (iki-motor C11/C18) — replay giriş limiti
  canlıyla aynı yasaya sıkılaştı (min(0,5·ATR14, %1); eskiden ATR'siz daima %1), v76 sentetik
  fikstürünün kanıt tabanı 17 < min_sample 30'a düştü, 6 arıza bundan kademeli (score→None zinciri).
  Üretim değişikliği DOĞRU; onarım fikstürde (tur açık, Opus uçuşta) — eşik/assert GEVŞETİLMEZ.
  (b) GİRİŞİM AVI KAPANDI (2026-08-02 gece, diğer oturum) — iki hüküm, ikisi de çürütmeli:
  (b1) SIZINTI İPUCU YANLIŞ ALARMDI: taze worktree'deki `bounds.yaml`+`goal.yaml` test artığı değil
  GIT ÇIKIŞI — c783442 .gitignore ölü-negasyonunu düzeltip ikisini BİLEREK versiyona almış (ve o
  commit ipucu ağacının atası); `--collect-only` provası doğruladı: dosyalar checkout anında var,
  hiçbir test koşmadan. v72 ailesinin "yaşayan kanıtı" iddiası GERİ ÇEKİLDİ.
  (b2) 9'LU AİLENİN GERÇEK KİMLİĞİ: suite-içi sızıntı DEĞİL, YÜRÜYEN-AĞAÇ ARTEFAKTI. İlk tam-suite
  koşusu (8,5 dk) sırasında paralel merge main'i a75a207→0170cc0 taşıdı; 9'un tamamı kaynak-tarayan
  yapısal test (inspect.getsource) ve import-edilmiş modül ile diskte yeniden yazılan kaynak ayrıştı.
  Kanıt zinciri: imza tipi tekdüze · sıra eklentisi yok (alfabetik koşu, v76-zehirlenmesi imkânsız —
  gate_statistics/kovab_yapi v76'dan ÖNCE koşar) · statik ağaçta 4/4 koşu temiz (46ce02f otoriter,
  da6bec3 izole, ve ÇÜRÜTME KOŞUSU: a75a207 STATİK yeniden-koşumda 9'dan SIFIRI ateşlendi; çıkan
  10 kırmızı = o ağacın bilinen gerçekleri [6×v76+t3] + 2 düzenek artefaktı [c1-tombstone; güncel
  goal.yaml'ı (C24 anahtarlı) eski koda bindirince gu1b/authority-c3 — ayrıca ders: tarihi ağaca
  güncel tracked-state kopyalama GU1-sınıfı sahte kırmızı üretir]). DERS (pencere planı adım 3'ü
  genelleştirir): OTORİTER SUITE YALNIZ DONMUŞ AĞAÇTA — sha'ya sabitlenmiş worktree veya freeze;
  merge alan bir checkout'ta koşan suite hüküm değil gürültü üretir. Çıktı: full_suite_a75_static.txt.
  SIRA: v76 fikstür onarımı ✓ → girişim avı ✓ → yeşil suite ✓ (3752/0, donmuş tepe) → dağıtım ✓ (pencere 14:00 UTC).
  Çıktılar: scratchpad/full_suite_predeploy.txt. GÜNCELLEME (2026-08-02 akşam, Rol-1): icra-bloğu
  merge'i (46ce02f) sonrası otoriter koşu 7 kırmızı = 6×v76 + uiux-t3 (t3 892bf75 ile kapandı);
  girişim ailesi o koşuda ateşlenmedi. Pencere planı: §DAĞITIM PENCERESİ PLANI.
- **BT-2 YENİDEN AÇILDI (trend-kolu ölçümünün yan bulguları, 2026-07-31 ~02:30):**
  BULGU-1: karantina hacim-şartı gerçek hayalet sınıfının %29'unu kaçırıyor (10 kaçak ×2-ölçek
  satırı: GILD/CMCSA 2013-12-18, DLTR, UNP). BULGU-2: kapıdan geçen 97 çözülmemiş ölçek/kimlik
  kırılması (59 sembol: CHTR ×1158!, AVGO ×162, PINS kuruş-geçmişi, ABT/DD/HON spinoff'ları,
  TDG bozuk kesiti). component_ic/cf/R-tabloları hâlâ şüpheli → hayalet-round-2 turu (SIP kolu
  data.py'yi bırakınca): karantina şartı genişlet + 97'lik envanter → barrepair-2 + türetilmiş
  artefaktlar yeniden. Trend ölçümünün hükmü bu kirlilikten BAĞIMSIZ doğrulandı (katman
  kapalıyken de aynı) ama sistem-geneli tablolar için acil.
- **TREND KOLU: İLK SAĞ KALAN AİLE** — ayrıntı research/cards/README; ders: ön-kayıtlı pozitif
  kontrol tek-enstrümanlıysa portföy-yolu hatalarına yapısal kör (PK4/PK5 yol-tutarlılık
  kontrolleri standart olmalı — ölçüm-şablonu iyileştirmesi).
- **ASILI-TİCK VAKASI (2026-07-30 21:14→22:27 UTC; sınıf: "canlılık ≠ ilerleme"):** worker çöküp
  yeniden doğdu ve yeni beden açılışta futex'te asıldı; uvicorn 503 CEVAPLIYORDU ama tick
  ilerlemiyordu — watchdog tick İÇİNDE olduğundan sustu, OnFailure süreç ölmediği için ateşlemedi.
  Restart çözdü (operatör gece yetkisiyle). KALICI KORUMA KURULDU+TEST-ATEŞLENDİ:
  `meridian-tick-watchdog.timer` (15 dk'da bir; scheduler_status.updated>45dk bayat → restart).
  İLK IEX-BACAK KANITI aynı dakikada: `alpaca_session_bars feed=iex asked=253 answered=252` —
  seans tek çağrıda geldi. sip bugün-için-403 beklenen (SIP-düzeltmesi sabah dağıtımında).
- **GECE VARDİYASI SONUCU (2026-07-31 ~03:15 — dağıtım TAMAM):** 6 kod kolu + 7 ölçüm hükmü indi;
  suite 0 kırmızı; A1'de canlı: iki-motor icra yasası, sip-geçmiş kuralı (ilk kanıt: skipped_current
  olayı), damga-migrasyonu (95/95 seed; gerçek-canlı sayaç 0'dan), karantina-v2 (8 defter onarımı),
  bütünlük defteri (61 sembol), regime entry_gates üreticisi, tick-bekçisi. BEKLEYEN ÖLÇÜMLER:
  WP-R rampa-P3 (K=4) + SMA/ToM — hükümleri geldiğinde kartlara işlenecek. SABAH KALEMLERİ:
  onarım soğuma-içi-bekleme düzeltmesi · bekçi eşiği 3sa→45dk normalizasyonu · türetilmiş
  artefaktların güvensiz-dönem-dışlamalı yeniden üretimi (gecelik P5 + bars_integrity artık canlı)
  · skor kartı yeniden-puanlama · operatör karar listesi (§1'de).
- (eski vardiya planı — arşiv):
  Koşan: BT-1(damga+atribüsyon; bitince→WP-E ajanı EXE-2026-001 kartıyla) · hayalet-round-2 ·
  WP-R rampa-P3 ölçümü (kart EDG-003) · MAX ölçümü (EDG-004) · WP3.1 doğrulama filosu ·
  PIT-kaynak araştırması · A1 monitör-v2 (PID yerel, çıktısı tasks/b226ui034.output).
  SIRA: kollar indikçe → TAM SUITE → A1 dağıtımı (SIP-düzeltmesi+pano+BT-1+round-2 birlikte;
  restart yetkili) → EDG-005 SMA ölçümü → WP-M konsolide ajanı (kapasite kalırsa) → SABAH
  KONSOLİDASYONU (ROADMAP §1/§2 tazele, K-defteri↔kartlar senkron, gece karnesi raporu).
- **EDGE ARAŞTIRMA PROGRAMI ROADMAP §3.0b'de (operatör onaylı, filo-sentezli):** çıkış paketi
  (ölçüm koşuyor) → alfa/beta kablolama → mid-cap momentum yeniden-ölçümü (G1 çelişkisi kayıtlı) →
  katalizör-koşullandırma → insider hükmü (EDGAR koşuyor) → karşı-taraf istem satırı. ERTELENDİ:
  ısı tavanı (vol-yönetimi edge yaratmaz, paketler — pozitif-EV önkoşulu). YAPMA: klasik PEAD
  large-cap'te (Martineau + Subrahmanyam: 2006'dan beri ölü, mikro-cap hariç t=1,43). Canlı TCA
  canlıya geçişte ($6,12 paper-modeli; retail bandı 7-46bps → 2-4× kötüleşebilir).
- **Sıradaki turlar:** temizlik turu (14 emekli + 19 kablola + 13 operatör-kalemi belgesi;
  öğrenme ajanı inince — dosya çakışması) · pano/UX turu (§3.0'daki 10 kalem) · yarın sabah TEK
  dağıtım (keşif-dengesi + öğrenme-otomasyonu + temizlik + emekli-sembol restart'ı birlikte).
- **"Zaman varsayımı" sınıf avı eksik:** T+1 kusurunun sınıfı (kodda örtük yayın-zamanı/TTL
  varsayımları) repo genelinde sistematik taranmadı. Aday: bararchive Redis TTL, earnings takvim
  tazeleme, finviz keşif zamanlaması. → temizlik turuna ek mercek.
- **Yama-değil-çözüm borçları:** IEX hacim kalibrasyon oranları İLK T+1 düzeltmesine kadar boş
  (yedek katman o gece kör — bilinçli, damgalı) · emekli-sembol modülü A1'de diskte ama koşan
  süreçte değil (yarınki restart'a kadar payda 259) · monitörün başarı koşulu last_processed
  bekliyor (bu gece 07-29+07-30 birlikte işlenebilir — yorumda dikkat).
- **Operatör kalemleri:** bildirim kanal kimliği (TELEGRAM_*/MERIDIAN_WEBHOOK_URL — girilene dek
  fail-notify beyanlı no-op) · NOUS_MODEL · FISV/PSKY halef kararı · Faz-6/silahlanma onayları ·
  1.4 karar kapısı.
- **Ölçüm borçları:** hotstate_down çırpınması temiz Redis'te yeniden ölçülecek · R1 damgaları +
  PBO tabanı birikiyor (taban 0/204) · Katman C saha kanıtı · gölge-v2 kitaplarının ilk satırları.

## KALICI RİSKLER / DERSLER

- Waiter/ajan-içi bekletici YASAK (iki arıza). Tam suite turda BİR kez, ön planda, senkron.
- file_lock süreç-içi; canlı worker koşarken state'e ikinci süreçten yazma.
- rsync dağıtımı tüm repoyu taşır — yarım iş canlıya gidebilir; önce dry-run + mtime.
- Sınıflandırıcı curl|sh'ı engeller → kurulumlar PyPI/pipx veya sabitlenmiş git klonuyla.
- classifier/API kesintilerinde: salt-okuma araçlarla devam + zamanlayıcılı yeniden deneme.
- pytest `-qq` tuzağı (2026-08-02): pyproject `addopts = "-q"` zaten veriyor; komuta fazladan `-q`
  eklemek `-qq` yapar ve "N passed" özet satırını TAMAMEN bastırır — yeşil koşu hiçbir şey basmaz,
  triyaj `grep -E "FAILED|ERROR"` + özet satırı ikisine birden bakar. pytest'i `-q`suz çağır.
- venv ana repo kökünde (`/Users/erdemozturk/AI-Trading/.venv`, py3.12 + pytest); worktree'lerde
  YOK ve sistem `python3` (3.14 homebrew) pytest içermez → testler `.venv/bin/python -m pytest` ile.
