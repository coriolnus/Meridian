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

## AÇIK KALANLAR (bilinçli, sahipli)

- **DAĞITIM BLOKE — tam suite birleşik main'de KIRMIZI (2026-08-02, dağıtım kapısında bulundu):**
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
  (b) 9'u yalnız tam-suite'te kırmızı, izole yeşil = suite-içi girişim (v72 sınıfı sızıntı ailesi) —
  AYRI hastalık, ayrı tur. SIRA: v76 fikstür onarımı → girişim avı → yeşil suite → dağıtım.
  Çıktılar: scratchpad/full_suite_predeploy.txt.
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
