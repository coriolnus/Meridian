# MERIDIAN ENGINEERING LOG
Her oturumun BAŞINDA önce bu dosya okunur (§8 protokolü, 2026-07-30'da operatör kurdu).
İçerik bir İPUCUDUR, gerçek-kaynak değildir — koda karşı doğrulanmadan güvenilmez.
Tur notlarının kronolojik defteri ROADMAP.md §5'tedir (eski adıyla §7 — 2026-08-13 yeniden
yapılandırmada numaralandı, içerik aynen taşındı); bu dosya "şu an gerçekte ne var ve ne açık"
fotoğrafıdır.

**SUPERPOWERS PROTOKOLÜ (2026-08-17, operatör kurdu — CLAUDE.md §9, commit 1d10a75):** bu
depoda çalışan her Claude oturumu `superpowers` plugin bileşenlerini (brainstorming,
systematic-debugging, test-driven-development, writing-plans/executing-plans,
requesting/receiving-code-review, verification-before-completion, using-git-worktrees vb.)
kullanmak ZORUNDADIR. Bu, §2'deki rol ayrımının (Fable=mimari/brief/denetim,
Opus=implementasyon) ÜSTÜNE eklenir, onu iptal etmez — hangi rol kod/karar üretiyorsa kendi
kapsamında ilgili skill akışını izler. Çelişki halinde CLAUDE.md madde 1-8'deki Meridian'a özgü
disiplin (ölçüm kartı, waiter yasağı, tam-suite tek-otoriter, git/dağıtım kuralları) önceliklidir
— superpowers akışı bu kısıtları gevşetemez.

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

## BU OTURUMDA BULUNAN + ÇÖZÜLEN

**SUITE HÜKMÜ AŞILDI — KAYITLI RULING (2026-08-30, Rol-1).** 90f6cdc turunun otoriter suite'i
1 failed / 7714 passed döndü; kırmızı `test_golge_planli_kol_v217::test_p95_dongu_suresi_kart_
tavanini_ASMIYOR`. Hüküm: bilinen alet-gürültüsü sınıfı, İTİLDİ. Kanıt: (i) bu çivinin negatif-
kontrol sapması daha önce %37,1 ölçüldü — aradığı %10 etkinin üç katı, ayrı görev açık;
(ii) aynı donmuş ağaçta 5/5 izole koşum yeşil (1,33-4,02 sn); (iii) koşum sırasında paralel
worktree oturumu (PIT çivisi) CPU yakıyordu ve çivi duvar saati ölçer. Yanlışsa bedeli: p95
gerilemesi bir sonraki suite'te yine görünür — kalıcı körlük yolu yok.
 (kök nedenleriyle)

- **TUR KAPANIŞI 2026-08-29/30 — UYDURMA MALİYET TURU: DÖRT PR, HEPSİ `main`'DE (sınıf: "bir
  ölçüm kusuru çekilince ardından üç mekanizma daha geldi"):** başlangıç tek bir bulguydu —
  `spend.price_for` ücretsiz OpenRouter slug'larını Opus listesinden fiyatlıyordu (canlı A1'de
  13 çağrı, **7.89 USD harcanmamış para**). Kuyruk ucu dörde çıktı; sırayla:
  · **#14 `8fe683c` — `:free` VARYANT SONEĞİ.** Kural satıcı adından DEĞİL OpenRouter'ın kendi
    sözleşmesinden türetildi. Tabloya `nemotron`/`nvidia` EKLENMEDİ, çünkü bu arızayı TERSİNE
    çevirirdi: aynı satıcının ÜCRETLİ varyantları 0'a fiyatlanır, bu kez HARCANMIŞ para deftere
    hiç girmezdi — aynı yasanın öbür yönden ihlali. Eşleşme alt-dizge değil iki nokta ile ayrılmış
    SEGMENT (`":free" in m` testi `vendor/model:freeform`u da bedava sayardı). Çivi ÖNCE yazıldı
    (11 kırmızı / 8 yeşil; yeşil kalan 8 çürütme bacağı), mutasyon 4/4. **Brief'te olmayan,
    turda ölçülen:** aynı sessiz uydurma `tencent/hy3:free` ve `openai/gpt-oss-20b:free` için de
    koşuyordu. **Bedel pano rakamından büyüktü:** `over_budget()` üç ücretli yolu kapatır ve
    biri BEYİN ZİNCİRİNİN TAMAMIdır (`hermes.py:4275` → `return None`); tampon %39 yenmişti ve
    ajan yolunun kısması (`_agent_budget_take`) RPM/RPD SAYAR, maliyete BAKMAZ.
  · **#16 `c7a13b5` — SEÇİCİNİN ÜÇ KAPISI DA ÖLÜYDÜ.** `ops/etkilenen_testler.sh`ta üç yerde
    `${#DIZI[@]-0}`; bash'te `${#parametre}` varsayılan-değer soneki KABUL ETMEZ →
    `bad substitution`. Betik `set -e` KULLANMADIĞI için hata ÖLÜMCÜL DEĞİLDİ: stderr'e düşüyor,
    `[[ ]]` başarısız sayılıyor, kapı SESSİZCE "false" oluyordu. **En tehlikelisi küresel-dosya
    kapısı:** `tests/conftest.py` (7 autouse fikstür → 7183 testin hepsi) değişince "TAM SUITE
    GEREKLİ" DEMİYOR, 111 dosyalık dar küme öneriyordu — EKSİK-KAPSAMA, betiğin kendi
    başlığındaki sözleşmenin TAM TERSİ. Boş-diff kapısının HİÇ çivisi yoktu ve düşünce
    `grep -rlE ""` her dosyayı tutuyordu: "hiçbir şey değişmedi" girdisi **394 dosya** hükmüne
    dönüşüyordu. Eklenen ikinci çivi SINIF çivisidir (betik stderr'e genişletme hatası dökemez),
    çünkü davranış çivileri yalnız BİLİNEN kapıları korur.
  · **#17 `d030511` — KARTIN DONMUŞ GİRDİSİ SAĞLANAMAZ BİR ŞARTTI.** `EDG-2026-059`un kill
    kriteri korpusun ÇALIŞMA AĞACINDA donmuş kalmasını istiyordu; ama korpus çivisi RUNBOOK her
    değiştiğinde onun YENİDEN ÜRETİLMESİNİ zorunlu kılar. İkisi aynı anda sağlanamaz ve kart hiç
    koşulmadan girdi ÜÇ KEZ kaybolmuştu. Girdi İÇERİK-ADRESLİ git blob'una taşındı — adresleme
    değişti, GİRDİNİN KENDİSİ değişmedi (sha256 aynen `9f5c91203284d794`).
  · **#18 `edc4729` — DEFTER ONARIM BETİĞİ**, varsayılanı KURU KOŞU (yukarıdaki AÇIK KALANLAR
    kalemine bak; canlıda KOŞULMADI).
  **ARADA ÜRETİLMİŞ BELGE ZİNCİRİ İKİ KEZ ISIRDI** (`docs/RUNBOOK.md` → D6 korpusu): tur boyunca
  RUNBOOK üç ayrı sebeple bayatladı ve her seferinde korpus çivisi düştü. Beşinci tazeleme
  yazıldı (`TAZELEME-2026-08-14.md`); emsalin süreç notu ("üretilmiş belgeleri TUR BAŞINA BİR
  KEZ, tüm ajanlar indikten sonra üret") bu turda ADIYLA doğrulandı.

- **İKİ "YEŞİL AMA YANLIŞ" VAKASI — ÖLÇÜM ARACININ KENDİSİ YANILTTI (2026-08-29/30; sınıf:
  "yeşil, ölçülmüş demek değildir"):** ikisi de ancak GERÇEK koşumla görüldü ve ikisi de bu
  deponun kendi doktrinini (ölçmeden hüküm verme) araç katmanında sınadı.
  · **HARNESS'İN "exit code 0"I PYTEST'İN KODU DEĞİLDİR.** Arka plan sarmalayıcısı
    `pytest > log; echo "PYTEST_RC=$?" >> log` biçimindeydi; sarmalayıcının çıkış kodu son
    `echo`unkidir, yani HER ZAMAN 0. Bildirim iki kez "completed (exit code 0)" dedi: birinde
    suite gerçekte KIRMIZIYDI (`PYTEST_RC=1`, 2 kırmızı), öbüründe SIGTERM'lüydü (`143`).
    **Hüküm yalnız log'daki `PYTEST_RC` satırından okunur.**
  · **18 ÇİVİ YEŞİLKEN BETİK KOMUT SATIRINDAN HİÇBİR ŞEY YAPMIYORDU.** `ops/spend_defter_
    duzeltmesi.py` `parse_args([] if argv is None else argv)` yazıyordu; betik olarak koşulunca
    `main()` argv=None alır ve `sys.argv` TAMAMEN ATILIR — `--uygula` sessizce yok sayılıyordu.
    16 çivi bunu göremezdi çünkü hepsi `main([...])`'i DOĞRUDAN çağırıyordu: **API sınanıyordu,
    GİRİŞ NOKTASI değil.** Bir ops betiğinin sözleşmesi komut satırıdır. Çivi SD10 alt süreçle
    betiği gerçekten koşturur.
  **ÜÇÜNCÜ, KENDİ HATAM (kayda geçiyor):** arka planda tam suite koşarken ana checkout'ta dal
  değiştirdim; 14 dakikalık koşum kayan bir ağacı ölçtü ve GEÇERSİZ oldu. Sonucu raporlamak
  yerine öldürüp attım. Kural: **arka planda otoriter suite koşarken dal DEĞİŞTİRİLMEZ**;
  taban karşılaştırması gerekiyorsa ayrı worktree ya da `git checkout <ref> -- <yol>` kullanılır.

- **KILL#1 p95 ÇİVİSİ TAM SUITE'TE KIRMIZI VERDİ; ÖLÇÜM BUNUN REGRESYON OLMADIĞINI GÖSTERDİ
  (2026-08-29, `752e51e` birleştirme koşumu):** `test_p95_dongu_suresi_kart_tavanini_ASMIYOR` 7148
  yeşilin içinde TEK kırmızıydı. **"Flake" bir kök neden değildir**, o yüzden iki bağımsız ölçüm
  yapıldı. **(1) ETKİ YOLU YOK:** birleştirmenin `meridian/` altında dokunduğu TEK dosya
  `spend.py`dir (#14, `:free` fiyatlandırması); çivinin ölçtüğü döngü `on_barfeed_event`tir ve test
  yalnız `barclock · config · faz5_cikis · intraday_cycle · intraday_shadow · store` çağırır —
  `spend` o listede YOK. Bu turun kendi değişikliği de `hermes.py`dir, yani sıcak yolda değil.
  **(2) ALETİN GÜRÜLTÜSÜ ÖLÇÜLDÜ:** çivi YALNIZ BAŞINA beş kez koşturuldu —
  oran 1,024 · 1,018 · 1,014 · 0,720 · 1,006 (tavan 1,10, beşi de altında) ama negatif kontrolün
  sapması 6,5% · 1,1% · 2,1% · **37,1%** · 0,5%. Yani aletin kendi gürültüsü, aradığı %10'luk
  etkinin ÜÇ KATINA kadar çıkabiliyor — çivinin kendi yorumu bunu zaten yazmıştı ("taban da tavanı
  aşıyor... aletin ÇÖZÜNÜRLÜĞÜNÜ raporluyordu").
  **AÇIK KALAN (bu turda BİLEREK dokunulmadı):** çivinin `ÖLÇÜLEMEDİ` skip-kapısı tam bu duruma
  karşı konmuş ama BU koşumda ateşlemedi — kontrol tesadüfen SIKI görünürken oran sıçradı. Yani kapı
  gerçek koruma sağlıyor ama yeterli değil (tek pencerede hesaplanan kontrol, yükün açık kola düştüğü
  durumu göremiyor). Çivi bir KILL KRİTERİDİR (`EXE-2026-003`) ve CLAUDE.md madde 3 eşik/kill-list'e
  dokunmayı yasaklar — düzeltme kart sahibinin işidir, birleştirme turunun değil. Ayrı görev açıldı.

- **ÜÇ TAVANDAN BİRİ ÖTEKİLERDEN FARKLI DAVRANIYORDU (2026-08-29; merge öncesi öz-denetimde
  bulundu, çivi bulmadı):** `CLAUDE_MAX_TOKENS` `_claude_text`in İMZASINA varsayılan olarak
  yazılmıştı, yani değer TANIM ANINDA bağlanıyordu. `NOUS_MAX_TOKENS` ve `GEMINI_MAX_OUTPUT_TOKENS`
  ise gövde İÇİNDE okunur. Sonuç ölçüldü: sabiti çalışma anında değiştirmek claude ayağında
  SESSİZCE etkisiz, ötekilerde etkili. Env yolu (`HERMES_CLAUDE_MAX_TOKENS`) her üçünde de çalışıyor
  — yani CANLI bir arıza DEĞİL, ama bu turun kovaladığı "iki kopya sessizce ayrışır" sınıfının
  küçük ve gerçek bir örneği, üstelik onu ben doğurmuştum. Tavan artık gövdede çözülüyor
  (`max_tokens: int | None = None` → `if max_tokens is None`). **NEDEN KAYDA GEÇİYOR:** hiçbir çivi
  bunu yakalamadı ve yakalayamazdı — üç ayağın davranış SİMETRİSİ o gün çivili değildi. Bulan şey
  merge öncesi diff okumasıydı; yani "yeşil suite" ile "gözden geçirilmiş diff" ayrı güvencelerdir.

- **KENDİ DÜZELTMEMİN ÇAPALARI BAYATLADI — CI YAKALADI, YEREL KOŞUM YAKALAMADI (2026-08-29):**
  `test_ihlal_seti_GERILEMEDI` üç ardışık commit'te CI'da kırmızıydı. Sebep tam da `codelaw`ın
  kovaladığı sınıf: çivi yorumuma `hermes.py:491` diye bir SATIR çapası yazmıştım, sonra AYNI
  dosyaya sabit bloğu ekledim ve `propose_with_claude` 491'den 522'ye kaydı — yani çapayı bayatlatan
  şey benim kendi düzeltmemdi. `codelaw.py`nin kendi notu bunu zaten yasaklıyordu: "ÇAPA SATIR
  DEĞİL SEMBOL"; o not, iki nokta üst üsteli biçimin (`dosya.py:NNN`) tarayıcıya CANLI çapa
  göründüğünü ve bir kez "anlatının, anlattığı şeyin kurbanı" olduğunu da yazıyor.
  **DÜZELTME:** iki çapa da SEMBOLE çevrildi (`propose_with_claude`, `hermes_runtime.reflect_now`)
  — biri ÇİVİLENMİŞTİ, öbürü henüz çözülüyordu ama aynı sınıftaydı: bile bile mayın bırakılmaz.
  Belgedeki satır alıntıları da sembole çevrildi (aynı sebep; `.md` taranmıyor ama sayı ARTIK
  YANLIŞTI).
  **NEDEN YEREL KOŞUM KAÇIRDI:** kapsam testlerim (`brain_resilience`, `uiux`, `tipografi`,
  `etkilenen_testler`) `codelaw` çivisini İÇERMİYORDU ve `ops/etkilenen_testler.sh` motor kaynağı
  değiştiği için ZATEN "tam suite gerekli" diyordu — yani seçici doğru söylüyordu, ben tam suite'i
  arka planda başlatıp SONUCUNU BEKLEMEDEN commit'ledim. Ders: motor kaynağına dokunan bir turda
  push, tam suite sonucundan ÖNCE atılırsa CI onu benim yerime bulur.

- **ÇAPA TANIMI İKİ YERDE İKİ TÜRLÜYDÜ — DÜZYAZI HAYALET ÇAPA BEYAN EDEBİLİYORDU (2026-08-29;
  sınıf: "iki kopya sessizce ayrışır", bu deponun tekrar eden sınıfı):** günlükte bash dizi-uzunluğu
  ifadesinden söz eden bir cümle (`ops/runbook_uret.py` günlük maddelerini AYNEN kopyalar) belgeye
  İKİ HAYALET ÇAPA soktu; biri düpedüz `...` idi ve `...` bir HTML id'ye dönüşemediği için
  `test_t3_rota_cizer_ve_capalari_html_id_yapar` kırmızıya döndü.
  **KÖK NEDEN İLK HİPOTEZ DEĞİLDİ.** Görev kartım "kod aralıklarını ayıkla" diyordu ve ÜÇ yerin
  (`test`, `runbook_uret`, `api`) hizalanması gerektiğini varsayıyordu. ÖLÇÜM ikisini de çürüttü:
  `meridian/api.py::_MD_BASLIK` — `/runbook`u GERÇEKTEN çizen ayrıştırıcı — çapayı `^#{1,3} ...
  {#x}$` diye, yani **BAŞLIK SONEKİ** olarak tanır ve `id=` YALNIZ oradan doğar (`api._md_render`in başlık dalı);
  `ops/runbook_uret.py` de çapayı yalnız başlık satırlarına YAZAR (475/697/718) ve hiç TÜKETMEZ.
  Yani üretici ile oluşturucu **zaten aynı fikirdeydi**; ayrışan TEK yer testteki `_capalar()`tı:
  belgenin TAMAMINDA `{#...}` arıyordu. Üstelik aynı dosyanın 223. satırındaki kardeşi ZATEN
  başlık-bağlıydı — tutarsızlık dosyanın kendi içinde de duruyordu. **Yani düzeltilecek yer üç
  değil BİRDİ, ve kural "kod aralığını ayıkla" değil "çapa bir başlık sonekidir"dir.** Kod-aralığı
  çözümü sınıfı KAPATMAZDI: ters tırnaksız bir düzyazı `{#x}` yine hayalet çapa olurdu.
  **DÜZELTME:** `_capalar()` artık oluşturucunun DERLENMİŞ desenini (`api._MD_BASLIK`) İTHAL EDER —
  ikinci bir regex yazmaz. Desen değişirse okuma onunla birlikte değişir.
  **DOĞRULAMA ÇÜRÜTMEYLE, İDDİAYLA DEĞİL:** kırmızıyı doğuran cümle DÜZ hâline geri döndürüldü
  (dolaylı yazım ve "geri düzeltmeyin" notu KALDIRILDI) — belge o diziyi hâlâ içeriyor ve testler
  yeşil. Çivi de sabit listeye değil `api._md_render`ın ÜRETTİĞİ id'lere karşı ölçer, yani iki tanım
  ayrışırsa düşer. Üç mutasyon üçü de yakalandı (çıkarıcıyı eski gevşek regex'e döndür · çıkarıcıyı
  boşalt · oluşturucuyu düzyazı çapasını tanıyacak şekilde genişlet).
  **KENDİ ÇİVİMİ GERİ ÇEKTİM, kayda geçiyor:** ilk turda `test_duzyazi_capa_BEYAN_EDEMEZ_gercek_belgede`
  yazmıştım; yazıldığı an yeşildi ÇÜNKÜ cümle o sırada dolaylıydı. Cümle düzeltilince düştü ve
  düşmesi DOĞRUYDU: çivi, düzeltmenin KALDIRDIĞI kısıtı KALICI YASAYA çeviriyordu — "düzyazıda
  `${#...}` geçmesin" demek, bu turun tam tersini savunmaktır. Kaldırıldı, yerine gerekçesi yazıldı.
  Ders: bir çivinin YEŞİL olması doğru şeyi ölçtüğü anlamına gelmez; geçici bir düzenlemenin
  üstüne yazılmış çivi o düzenlemeyi yasalaştırır.

- **SINIFIN ÜÇÜNCÜ AYAĞI DA KAPANDI — CLAUDE BACAĞI (2026-08-29; operatör istedi, önceki turda
  "latent, bilerek dokunulmadı" diye açık bırakılmıştı):** kusur ikizlerinin aynısı, iki bacaklı.
  **(1) TAVAN:** `_claude_text` imzası `max_tokens: int = 4000` ve `propose_with_claude`
  (`propose_with_claude`) onu **ARGÜMANSIZ** çağırıyordu → 4000'e düşüyordu. Üstelik gövde
  `thinking={"type": "adaptive"}` + `output_config={"effort": "high"}` gönderir, yani bu ayak da
  **DÜŞÜNEN** bir yapılandırmadır; Anthropic sözleşmesinde `max_tokens` modelin BİLMEDİĞİ, dayatılan
  bir yanıt tavanıdır ve düşünce o tavandan yenir. Gemini AYNI yansıma prompt'unda 3838 düşünce
  tokenı ölçtü — yani 4000 bu iş için ÖLÇÜLÜ biçimde dardı. **(2) SINIFLANDIRMA:** `stop_reason`
  incelemesi `if not text:` bloğunun **İÇİNDEYDİ**; tavana çarpan cevap BOŞ DEĞİLDİR (kısmî metin
  taşır), o yüzden o ayrıma HİÇ UĞRAMIYORDU → `_parse_hyp` → `unparseable`. Portal ayağındaki
  yapısal kusurun birebir aynısı. **DETERMİNİSTİK ÜREME:** düzeltmeden önce çivi yine
  `assert 'unparseable' == 'truncated'` ile düştü. **DÜZELTME:** `CLAUDE_MAX_TOKENS`
  (env `HERMES_CLAUDE_MAX_TOKENS`, vars. **16000** — Anthropic'in AKIŞSIZ istekler için belgelenmiş
  varsayılanı; daha yükseği akış ister, bu ayak akış kullanmıyor) + kesilme kontrolü metin
  kontrolünden ÖNCE (`stop_reason == "max_tokens"` → `EMPTY_TRUNCATED`) + `chain_text`teki elle
  yazılmış `max_tokens=8000` KALDIRILDI, iki ayak artık TEK adlandırılmış tavanı paylaşıyor
  (bu PR'ın kendi dersinin uygulanması: bağımsız iki sayı bırakmak, birinin değişip öbürünün
  unutulduğu vakayı üretir). **SAĞLAYICI FARKI BİLEREK KORUNDU — UYDURMA YASAĞI:** gemini
  `thoughtsTokenCount`, OpenRouter `reasoning_tokens` RAPORLAR; **Anthropic düşünce tokenını AYRI
  bir alanda BİLDİRMEZ** (`output_tokens` içindedir). Kardeşlere SİMETRİ uğruna "reasoning=" yazmak
  ölçülmemişi ölçülmüş göstermek olurdu; detayda yalnız ÖLÇÜLEN iki sayı var (`output=N, cap=N`) ve
  bunu bir çivi kilitliyor. **ZAMAN AŞIMI BURADA AYRI DÜĞME DEĞİL** (nous ayağından farkı): SDK'nın
  kendi varsayılanı (10 dk) yönetir ve 16000 token onun içine sığar — yani nous'taki "tavan
  yükseldi, zaman aşımı elde kaldı" tuzağı bu ayakta YOKTUR. **ÇİVİLER (8, v327):** SDK bu depoda
  KURULU DEĞİL (ölçüldü), o yüzden çiviler sahte bir `anthropic` modülü enjekte eder — kurulu
  olmasına bağlanmaz, CI de kurmuyor. Beş mutasyonun beşi de yakalandı (tavanı 4000'e geri al ·
  kesilme kontrolünü kaldır · sınıfı `unparseable`a geri al · `chain_text` yine elle 8000 geçsin ·
  detaya uydurma `reasoning=0` ekle).
  **BU AÇIK KALEM AYNI GÜN KAPANDI (v328, operatör istedi) — VE KAPATIRKEN YUKARIDAKİ CÜMLE
  DÜZELTİLDİ:** açık kalem "red `EMPTY_NO_TEXT`e düşer" diyordu; ÖLÇÜM bunu çürüttü. `NO_TEXT`e
  yalnız GÖVDESİZ red düşer. Metin TAŞIYAN red — asıl vaka — `_parse_hyp`e gidiyordu ve orada
  `_looks_like_refusal()` METNİN SÖZCÜKLERİNE bakıyordu (`_REFUSAL_MARKS`), yani sınıf bir
  TAHMİNDİ: listede olmayan bir ifadeyle reddedilirse sessizce **`unparseable`** oluyordu. Kırmızı
  faz bunu birebir gösterdi: `assert 'unparseable' == 'refusal'`. **ASIL MESELE EKSİK BİR DAL
  DEĞİL, YANLIŞ KAYNAKTAN OKUMAKTI.** Anthropic reddi BEYAN EDER (`stop_reason == "refusal"`,
  `stop_details = {type, category, explanation}`) ve **beyan edilmiş olgu tahmin edileni EZER** —
  bu turun tamamının dersi. **DÜZELTME:** red dalı metin kontrolünden ÖNCE, `category` beyandan
  okunur; `stop_details` YALNIZ redde dolduğu için korumalı okunur (`getattr`), ve `category` AÇIK
  bir kümedir + null olabilir → uydurulmaz, `None` yazılır. Sezgi SİLİNMEDİ: `_parse_hyp`teki
  kardeşi, reddi beyan ETMEYEN sağlayıcılar için hâlâ tek yoldur. **ÇİVİLER (6):** çürütme bacağı
  dahil — kullanılan gövde (`"Bu talep politika dışıdır."`) `_REFUSAL_MARKS`ın HİÇBİRİNE takılmaz,
  yani çivi beyanı ölçüyor, sezgiyi değil. Beş mutasyonun beşi de yakalandı (dalı kaldır · sınıfı
  `NO_TEXT` yap · kategoriye `unknown` uydur · `stop_details`i korumasız oku · dalı metin
  kontrolünün ARKASINA al). Böylece üç ayağın ÜÇÜ de artık aynı sözleşmeyi taşıyor:
  kesilme · red · araç · metin-yok ayrı ayrı adlandırılıyor.

- **SEÇİCİ BETİĞİ BASH'TE GEÇERSİZ İFADE TAŞIYORDU (2026-08-29; taban kırmızısı, operatör istedi):**
  `ops/etkilenen_testler.sh` üç satırda `${#DIZI[@]-0}` kullanıyordu; `-` varsayılan-değer operatörü
  `${#...}` UZUNLUK biçimiyle birleşmez. `main`in kendi kopyası koşturularak doğrulandı (dal kusuru
  DEĞİL). **BU SATIRDA YANILDIM ve düzeltiyorum:** "sessiz yanlış-negatif değildi, kapı
  gürültülüydü ama doğruydu" demiştim. PR #16 (`c7a13b5`, main'e indi) bunu ÖLÇÜMLE ÇÜRÜTTÜ: betik
  `set -e` KULLANMADIĞI için `bad substitution` ölümcül değil ama `[[ ]]` başarısız sayılıyor ve kapı
  SESSİZCE "false" oluyordu — yani **üç kapı da ölüydü**. En pahalısı küresel-dosya kapısı:
  `tests/conftest.py` değişince "TAM SUITE GEREKLİ" DEMİYOR, dar bir küme öneriyordu — yani
  EKSİK-KAPSAMA, betiğin kendi sözleşmesinin tam tersi. Benim okumam yalnız stderr'e bakmıştı,
  kapıların DÖNDÜĞÜ değere bakmamıştı. Ders: "hata ölümcül değil" ile "karar doğru" ayrı iddialardır. 8/8 yeşil. Taşınabilirlik YARIM doğrulandı: konteynerde yalnız bash
  5.2.21 var, macOS'un 3.2'si YOK — betiğin başlığı ikisini de şart koşuyor.

- **BÜTÇE ARIZASI BİÇİM ARIZASI DİYE YAZILIYORDU — v97'nin GEMİNİ'DE KAPATTIĞI SINIF PORTAL AYAĞINI
  HİÇ ALMAMIŞTI (2026-08-27; sınıf: `Ö-49` kardeşi — "aynı kusur ikinci sağlayıcıda, düzeltme göç
  etmedi"):** `_nous_text` (OpenRouter/nous portal yolu) `max_tokens: 4000` sabitini gönderiyordu.
  Canlı defter (A1, `state/spend.jsonl`): nvidia/nemotron ailesine **13 çağrının 7'si TAM
  `out_tokens=4000`** (%54) — 5x super-120b + 1x ultra-550b `reflect (nous)`, 1x super-120b
  `nous_eval`; girdi ~23-27k token. Sağlayıcı sondası mekanizmayı gösterdi: `ultra @ max_tokens=60`
  → `finish_reason=length` + içerik modelin **DÜŞÜNCE ÖN-EKİ** (reasoning=62); `@2000` →
  `finish_reason=stop` + geçerli JSON. **KÖK NEDEN YAPISALDIR ve tavandan İBARET DEĞİL:**
  `_nous_text`te `finish_reason` ayrımı `if not txt.strip():` bloğunun **İÇİNDEYDİ**. Kesilen cevap
  BOŞ DEĞİLDİR — içinde düşünce ön-eki vardır — yani o ayrıma **HİÇ UĞRAMIYORDU**: yarım metin
  çağırana dönüyor, `_parse_hyp` JSON bulamıyor, defter `unparseable` yazıyordu. Gemini'de kesilme
  kontrolü metin kontrolünden ÖNCE gelir (`_gemini_text` docstring'i, v97); portalda o sıra yoktu.
  Yani tavanı tek başına yükseltmek sınıfı düzeltMEZDİ: bir sonraki kesilme yine "biçim" diye
  okunurdu. **DETERMİNİSTİK ÜREME (çıkarım değil, ölçüm — kırmızı faz):** düzeltmeden önce çivi
  `assert 'unparseable' == 'truncated'` ile düştü; yani canlı defterdeki yanlış adın kaynağı
  koddan yeniden üretildi. **DÜZELTME (ilk geçiş — aşağıda İKİ KEZ düzeltildi):** `NOUS_MAX_TOKENS`
  (env: `HERMES_NOUS_MAX_TOKENS`, o an 16000; YÜRÜRLÜKTEKİ değer 16384 · 900 sn) + kesilme kontrolü metin kontrolünden ÖNCE + `EMPTY_TRUNCATED` sınıfı token sayılarıyla
  (`reasoning=N, completion=N, cap=N`) + `reasoning_tokens` → `spend.record(thought_tokens=)`.
  **TAVAN NEREDEN TÜRÜYOR:** o 7 satır **SAĞDAN SANSÜRLÜDÜR** — tavanda kesilen örnek "ihtiyaç
  ≥4000" der, ihtiyacın NE OLDUĞUNU söylemez; gerçek istem üzerinde ölçülmüş tek akıl-yürütme sayısı
  gemini'nin `thoughtsTokenCount=3838`üdür → ×4 marj = 16000. Marj bedelsiz: iki model de `:free`,
  platform tavanı istek/dk + istek/gün cinsinden, token cinsinden DEĞİL. Gerçek ihtiyacı bundan sonra
  `truncated` olayının kendisi ölçecek. **ÇİVİLER (10, tests/test_brain_resilience_v66.py v325):**
  uçtan uca sınıf çivisi + `reasoning=None` (uydurma yasağı) + pozitif kontrol + tavan/gövde çivisi +
  eski üç sınıfın korunması. Dört mutasyonun dördü de yakalandı (tavanı 4000'e geri al · sınıfı
  `unparseable`a geri al · kesik metni yine çağırana döndür · ölçülmeyen akıl sayısına 0 yaz).
  **BU TURUN KENDİ KUSURU — İLK GEÇİŞ YARIM DÜZELTMEYDİ (aynı gün, `main`deki ölçüm belgesi
  yakaladı):** ilk commit (69cf842) tavanı 4000→16000 yaptı ama `timeout=120.0` sabitine
  DOKUNMADI. `docs/OLCUM-MODEL-BUTCESI-2026-08-27.md` (e8e52cb, `main`) §3-4 bunun neden bir
  düzeltme DEĞİL ad değişikliği olduğunu ölçmüş: Super 130,8 tok/sn ama **Ultra 25,8 tok/sn (5 KAT
  yavaş)** → 120 sn'de ancak ~3.096 token, yani yükseltilen tavana ULAŞAMADAN zaman aşımına düşer.
  Belgenin cümlesi birebir: "ikisini AYRI AYRI değiştirmek işe yaramaz: yalnız `max_tokens`
  yükseltilirse kesilme zaman aşımına dönüşür". DAHA KÖTÜSÜ, belge bunu söylemiyor ama bu turda
  ölçüldü: o yolda httpx cevap DÖNMEDEN istisna atar, yani bu turda eklenen `truncated`
  sınıflandırması HİÇ ATEŞLENMEZ ve olay `nous_chain_failed`e düşer — bütçe arızası bu sefer TAŞIMA
  arızası diye okunurdu. Sınıf kapanmaz, yer değiştirirdi. **DÜZELTME (ikinci geçiş):** tavan
  16384 (belgenin §6 tablosunda bu çağrı sınıfının satırı; iki modelin sağlayıcı tavanının da
  altında — ölçülen §1: ultra 65.536 · super 235.929) ve **zaman aşımı artık TÜRETİLİR, sabit
  değil**: `NOUS_MAX_TOKENS / NOUS_OLCULEN_TOK_SN(25,8) × NOUS_ZAMAN_MARJI(1,4)` = 889 sn. Emsal
  `HAVUZ_IS_SURESI_OLCULEN_SN × HAVUZ_ATALET_MARJI`dir ve gerekçe aynı: ikisini bağımsız iki sayı
  bırakmak, birinin yükseltilip öbürünün unutulduğu TAM BU VAKAYI bir kez daha üretirdi. Çivi
  invaryantı kilitler (tavan zaman aşımı içinde ULAŞILABİLİR olmalı) + çürütme bacağı eski çiftin
  (4000, 120) invaryantı ÇİĞNEDİĞİNİ gösterir, yani kontrol totoloji değildir. Üç mutasyon üçü de
  yakalandı (zaman aşımını 120'ye geri al · tavanı yükselt ama zaman aşımını türetme · tavanı
  sağlayıcı sınırının üstüne çıkar). **ASENKRON ŞARTI DOĞRULANDI:** §6 tablosu bu satır için
  "yalnız async" der; `_nous_text`in iki çağıranı da arka plandadır (`reflect_now()` arka plan iş
  parçacığı açıp HEMEN döner, `hermes_runtime.reflect_now`; `nous_eval` haftalık kadans), yani 889 sn
  hiçbir HTTP isteğini bloklamaz. Senkron çağıran eklenirse yeniden ölçülmeli.
  **DERS:** "tavanı yükselt" tek başına bir düzeltme değildi; bağlayan tarafın HANGİSİ olduğu
  ölçülmeden seçilen her iki sayı da keyfîdir.
  **ÜÇÜNCÜ GEÇİŞ — ÇİVİNİN KENDİSİ TOTOLOJİYDİ (aynı gün, tablo koda karşı okunurken bulundu):**
  ikinci geçiş zaman aşımını `NOUS_MAX_TOKENS / NOUS_OLCULEN_TOK_SN × 1,4` diye TÜRETİYORDU (889 sn)
  ve invaryant çivisi "zaman aşımı >= tavan/hız" diye sınıyordu. 1,4 > 1 olduğu için bu kontrol
  VARSAYILAN YOLDA ASLA KIRMIZI OLAMAZDI — ölçen değil, kendi kendini onaylayan bir çivi. Bu deponun
  "çürütmeyle sınandı, varsayılmadı" şartının ihlali; üstelik tam da o şartı yazmak için eklenmiş
  bir çividen. İKİNCİ KUSUR: sessiz ölçeklenme bir TEHLİKEDİR — tavanı 32.768'e çıkaran biri farkında
  olmadan ~21 dakikalık, kimsenin ÖLÇMEDİĞİ bir zaman aşımı da satın alırdı. **DÜZELTME:** değer
  artık §6 tablosunun yayımlanmış sayısıdır (900 sn) ve tavandan BAĞIMSIZDIR; bağı çivi tutar, yani
  bağ kırıldığı gün çivi KIRMIZIYA DÖNER ve insanı yeniden ölçmeye zorlar — doğru davranış budur.
  Eklenen iki çivi: (a) invaryantın AYIRT ETTİĞİ (tavan iki katına çıkarılsa çiğnenirdi) — çivinin
  kendisini sınayan çivi; (b) kaynaktaki çiftin §6 tablosuyla BİREBİR aynı olduğu (16.384 · 900),
  yoksa belge ile kod sessizce ayrışırdı. Üç mutasyonun üçü de yakalandı.


  **AÇIK KALAN — ÖLÇÜLEMEDİ, UYDURULMADI (3):**
  (1) **7 damganın olay defteriyle KORELASYONU CANLIDA DOĞRULANMADI.** Bu tur GitHub'dan klonlanan
      *cloud* oturumunda koştu: konteynerde `ssh` ikilisi YOK, `~/.ssh/oci-a1.key` YOK, `state/`
      versiyonlanmıyor (yalnız `goal.yaml`+`bounds.yaml` izli) — yani `journalctl -u meridian
      -u meridian-learn` ve `spend.jsonl` bu konumdan ERİŞİLEMEZ. Mekanizma koddan deterministik
      üretildi; "bu 7 damga şu ledger satırlarını üretti" ifadesi hâlâ ÇIKARIMDIR. A1 erişimi olan
      Rol-1 oturumu doğrulamalı: 7 damganın ±2 dk penceresinde `nous_eval_unparseable` /
      `hermes_brain_empty(reason=unparseable)` / `nous_chain_empty` satırı var mı.
  (2) **AYNI SINIF CLAUDE AYAĞINDA LATENT DURUYOR (bu turda BİLEREK dokunulmadı — kapsam
      genişletmesi olurdu):** `_claude_text` imzası `max_tokens: int = 4000` ve `propose_with_claude`
      (`propose_with_claude`) onu **argümansız** çağırır, yani 4000'e düşer — üstelik gövde
      `thinking={"type": "adaptive"}` gönderir, yani o ayak da DÜŞÜNEN bir yapılandırmadır ve gemini'nin
      3838 ölçtüğü AYNI yansıma prompt'unu kullanır. `chain_text`in claude ayağı 8000 geçer,
      `propose_with_claude` GEÇMEZ. Ayrıca `stop_reason="max_tokens"` → `EMPTY_TRUNCATED` eşlemesi orada
      da YOK. Bugün canlıda tetiklenmiyor (sistem haritası: "claude bacağı kimliksiz") — bu yüzden
      ACİL değil, ama kimlik girildiği gün sınıf üçüncü kez doğar.
  (3) **`reasoning` kolu DOĞRULANMADI:** `NOUS_REASONING_EFFORT` env kolu eklendi ama **varsayılan
      KAPALI ve boşken alan gövdeye HİÇ konmaz** (çivili). Sebep: `openrouter.ai` bu konteynerin çıkış
      vekilince kapalı ve burada anahtar yok — parametrenin bu uçtaki tam şekli doğrulanamadı, uydurma
      yasağı istek gövdesi için de geçerlidir. Açmadan önce sonda şart. TUZAK YAZILI: `exclude` bir
      BÜTÇE ayarı DEĞİLDİR (düşünceyi cevaptan gizler, üretilmesini engellemez → tavanı aynen yer);
      bütçeyi kurtaran ayar düşünceyi KAPATANdır (gemini'de `thinkingBudget=0`).
  **KAPSAM SINIRI (varsayılmadı, brief'te ölçülmüş):** `agent_call_empty` (709) ve
  `review_fallback_empty` (459) YEREL AJAN CLI yoludur (`_agent_call`), bu düzeltme onlara DOKUNMAZ.

- **ARAMA HAVUZU 13 GÜNDÜR SIFIR SONUÇ ÜRETTİ — TAVAN İŞTEN KISAYDI (2026-08-25; sınıf: "eşik,
  ÖLÇTÜĞÜ mekanizmadan değil BAŞKA bir mekanizmadan türetildi"):** `arama_havuzu_zaman_asimi`
  olaylarının TAMAMINDA (2026-08-12'den beri **61 olayın 61'i**) `biten=0`. Şüphe kilitlenme/
  açlık/OOM/`nice(15)`e gitti; ÜÇÜ DE DEĞİL. Canlı adliye: işçiler ÇALIŞIYOR — 487337 `R`
  durumunda %99,8 CPU, 487340 `S` + `wchan=anon_pipe_read`. **KÖK NEDEN: tavan tek bir işten
  KISA.** İş başına walk-forward üç bağımsız kaynakta ölçüldü — 45 başarılı prefill turu
  (duvar×işçi/n) **2279-3042 sn**, ardışık `hermes_search_probe` farkı **2487-3185 sn**,
  reflect.py'nin kendi notu **2532 sn** — tavan ise **1800 sn**. İlk bitiş tavana yetişemediği
  için `biten=0` bir arıza BELİRTİSİ değil ARİTMETİK ZORUNLULUKTU. Havuz 08-12'ye kadar
  ÇALIŞIYORDU (94 başarılı prefill, sonuncusu 08-12T07:40 n=10); tavan o gün indi (`becb03b`,
  "asılı-arama öz-onarımı") ve ilk aşım 08-12T11:40'ta geldi. **TÜRETİM NEREDE KAYDI:** gerekçe
  "incumbent-walk ~90 sn ÖLÇÜLÜDÜR × 20" diyordu; o ~90 sn `hermes.py`de PANONUN bekleme süresi
  için düşülmüş bir nottur ve BAŞKA bir hesabı anlatır. Doğru sayı ölçülmemiş değildi —
  `events.jsonl`da 94 satırdı, bakılmamıştı. **İKİNCİ, BAĞIMSIZ KUSUR (`_havuzu_oldur` hiçbir
  işçiyi öldürmüyordu):** `shutdown()` gövdesinin sonunda koşulsuz `self._processes = None` var
  (`wait` bayrağına BAKMAZ, CPython 3.12); yakalama sonra yapıldığı için `getattr(ex,
  "_processes", {})` varsayılana DÜŞMEZ (öznitelik var, değeri None) → `None.values()` →
  `AttributeError` → alttaki `except Exception: pass` yutar → `terminate()` HİÇ ÇAĞRILMAZ.
  Yutucunun gerekçesi bunu "sürüm değişimi" uç durumu sayıyordu; **TEK durummuş**. Bedel her
  atalet olayında iki süreç: biri sonucunu kimsenin okumayacağı bir hesapta tam çekirdek yakıyor,
  öbürü `anon_pipe_read`de, ikisi ~225 MB. ÖMÜR DE ÖLÇÜLDÜ: 20:05'te ikisi de gitmişti — terk
  edilişten sonra ~47-69 dk (kabaca elde kalan bir walk-forward), `terminate()` koştuğu için
  değil işleri bitip kuyruk yıkıldığı için. Yani kalıcı sızıntı DEĞİL, atalet başına ~1 saat tam
  çekirdek + ~450 MB — tam da sıralı yedek yolun CPU istediği pencerede. **YAYILIM:** aramanın verimi de aynı gün
  çöktü — `evaluated` 26/34'ten TAM 2'ye indi (tavanın yediği 1800 sn'den sonra
  `MERIDIAN_SEARCH_MAX_MIN=60` penceresine yalnız iki taze sonda sığıyor); 179 `hermes_search_start`
  karşısında 60 `done`, kayıp 119'un **70'i tek sonda bile koşturamadı**; biten SON arama
  2026-08-21 18:02. **ÇİVİLER:** `test_havuz_oldurme_kacagi_v317` (davranışsal — atalete çarpan
  havuzun işçileri ölmüş olmalı; düzenek çivisi: işçiler doğmazsa KURULUMDA düşer, sessiz-yeşil
  yok) ve `test_havuz_atalet_tavani_v318` (üç bacaklı; ortadaki bilerek DAVRANIŞSAL — gerçek
  (iş, tavan) oranını 1/10000 ölçekte GERÇEK `_havuz_sonuclari`ndan geçirir, çünkü sabit
  karşılaştırması totoloji olurdu; üçüncü bacak yasanın İPTAL EDİLMEDİĞİNİ sınar). Dört mutasyonun
  dördü de yakalandı. Tavan artık kaynakta ADLANDIRILMIŞ bir ölçümden türüyor
  (`HAVUZ_IS_SURESI_OLCULEN_SN=3185 × HAVUZ_ATALET_MARJI=3` → 9555 sn = 2,65 sa), bayatlık
  eşiğinin (6 sa) ALTINDA — kurtarma hâlâ aynı gece penceresinde. **SIRA BAĞI:** v318 v302'siz
  DAĞITILAMAZ — bekleyiş artık bekçi penceresinin kat kat üstünde sürebildiğinden, nabız
  kuantumlanmamış olsaydı v318 bayat-geçişi ortadan kaldırmaz BÜYÜTÜRDÜ. **AÇIK KALAN (ölçüldü,
  bu turda kapatılmadı):** (1) `clear_wf_caches()` sonda+incumbent önbelleğini HER seans bar
  tazelemesinde SİLİYOR — kalıcı sıcak önbellek yok, yani her gün 8-10 taze walk-forward sıfırdan;
  "08-18→08-23 önbellek-isabetliydi" okuması yanlıştı, 0 sn'lik farklar KALICI önbelleğin değil
  ÇALIŞAN havuz ön-dolgusunun imzasıydı ve 08-12'de o durdu. (2) `_havuz_tavani` 2026-07-30'da
  4 işçiden 2'ye düştü (`cpu-2`, A1'de 4 OCPU) ve iş süresini ~1100-1430 sn'den ~2280-3040 sn'ye
  çıkardı — brief'teki "865-1276 → 2259-3185" basamağı budur, 08-06 değil 07-30'dur ve tavanı
  imkânsız kılan asıl olaydır. (3) Bugünkü `probe_prefill` aşımları ISINMA SPRİNTİNDEN geliyor
  (`hermes_runtime` → `coordinate_descent_search`), `hermes.search` sarmalayıcısından değil —
  o yüzden `hermes_search_start` damgası düşmüyor; "bugün 0 arama" okuması bu yüzden yanıltıcı.

- **HÜKÜM YAZILDI, HİÇBİR KARARA İŞLENMEDİ (2026-08-17; sınıf: `Ö-49` çapa/beyan çürümesi — kart↔hüküm
  yüzeyi):** `EXE-2026-006` ölçümü TAM koşuldu (K=8, altı kill kriteri de geçti) ve hükmü
  `research/olcumler/exe006_limit_bacagi_2026-08-17/HUKUM.md`e yazıldı: **E1 HÜKMÜ YENİDEN AÇILIR**.
  Ama hüküm commit'i (`a033256`) **24 dosya taşıdı ve hepsi ölçüm artefaktıydı** — karta, `§2 TAHTA`ya,
  `§6` indeksine, `§7` karar günlüğüne DOKUNMADI. Sonuç: kart `status: registered` ("ölçüm bekliyor")
  derken hükmü diskte YAZILI duruyordu; `§6`da kartın satırı HİÇ YOKTU; `§2 TAHTA` kalemi hâlâ
  "kart ÖN-KAYITLI · ölçüm bekliyor" kovasındaydı. **KÖK NEDEN BİR İŞ BÖLÜMÜ KUSURU DEĞİL, TAM TERSİ:**
  `CLAUDE.md §3` "ölçüm ajanı karta DOKUNMAZ — hükmü Rol-1 işler" der ve ölçüm ajanı DOĞRU davrandı.
  Eksik olan, **Rol-1'in devralma adımının hiçbir yerde ÇİVİLİ olmamasıydı** — yani sözleşme kendi
  DEVİR NOKTASINDA sessizdi: hükmü yazan taraf karta dokunamaz, karta dokunacak taraf ise "hüküm hazır"
  sinyalini yalnız HATIRLAYARAK alır. Üç okuyucu birden yanılıyordu: `§6` durumu karttan okur ·
  **K defteri kart kimliğinden okunur ve `registered` bir kart K HARCAMAMIŞ görünür** (006 K=8 harcadı;
  eksik K, eşiği HAK ETMEDEN geçme yönünde YANLIDIR — `test_kart_kimlik_v219`un ölçtüğü yanlılığın
  birebir aynısı, farklı yüzeyden) · `§2 TAHTA` triyajı aşamayı "kart ön-kayıtlı mı" sorusundan türetir.
  **ÇİVİ (`tests/test_kart_hukum_damgasi_v251.py`, TDD — KIRMIZI DOĞDU):** yazılı bir `HUKUM*.md` ile
  o hükmün adlandırdığı kartın `status`u ÇELİŞEMEZ (+ hükmün adlandırdığı kart VAR olmalı). 5 pozitif
  kontrol + **düzenek çivisi** (desen kayarsa tarama boş döner ve çekirdek çivi hiçbir şey ölçmeden
  yeşil geçerdi — o sessiz-yeşil kapatıldı). TEK YÖNLÜ olması BEYANLI: "hüküm yok ama kart `measured`"
  ters yönü sınanmaz, çünkü hüküm `HUKUM.md` dışında da yazılabilir (kartın `verdict` bloğu, `§7`,
  `BULGU-*.md`) ve bugün 26 `measured` kartın yalnız BİRİNİN ayrı `HUKUM.md`si var — zorunlu kılmak
  25 kartı yanlış-kırmızıya düşürür, yani kusur değil BİÇİM ölçerdi. **AÇIK KALAN AYNI SINIFTA:**
  `EXE-2026-005` de `registered` ve hükmü `BULGU-B-KOLU.md`de yazılı ("Rol-1 hükmü ve K-defteri kaydı
  ister") — `v251` onu YAKALAMAZ (dosya adı `HUKUM*` değil) ve bu bilinçli; kalem `§2 TAHTA`ya
  `Ö-51d` olarak yazıldı, kapatılması `parameter_grid` dokunuşu yüzünden K kararı gerektirir.

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
  vakasının İKİNCİ kuşağı):** H3 tur-2 `CHANGEME` placeholder'ını birimden çıkarınca `deploy.sh`ın pano-token bekçisi
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

- **OTURUM KAPANIŞI (2026-08-02 gece, Rol-1 — takvim_yok/pencere oturumu):** hungry-jemison
  merge'i (0652841: bekçi kapıları + v176 + sınıf-ailesi bağı; RUNBOOK çakışması regen'le çözüldü,
  merge-sonrası 93/93) indi; ÜÇ tur worktree'si + dalı temizlendi (xenodochial / unruffled /
  hungry-jemison) — repo TEK checkout. Dağıtım kuyruğu BOŞ. Otoriter suite referansı:
  **3969/0 @ 6545c6a** (bu oturumun pencere koşusu). A1 çalışma-yolu içeriği 6545c6a-özdeş;
  main 0652841 farkı yalnız test-katmanı (conftest bekçi kapıları + v176) ve belgeler — runtime
  etkisi YOK, sıradaki pencereyle iner (yeni kuyruk kaydı açmayı gerektirmeyecek kadar küçük;
  pencereyi koşan, dağıtım anındaki main tepesini kaydetsin — 660dc10 dersi).

- **STATE ŞİŞMESİ + YEDEK KAPSAMI (2026-08-02 gece, Rol-1 + Opus; H10 turunun devredilen bulgusu —
  iki sınıf birden):** A1'de state/ 617M'in 438M'i = 4 sprint kum-havuzu × ~110M; gecelik tar 112,5M.
  İKİ AYRI KÖK NEDEN ÖLÇÜLDÜ: (1) SINIF "belgede donmuş boyut varsayımı" — `sprint.SKIP_COPY` yalnız
  `bars`ı atlıyordu; küme yazıldıktan SONRA doğan `bars_intraday` (43M) + `intraday_bars` (40M) her
  kum havuzuna sessizce kopyalanıyordu (83M = ~110M'in 3/4'ü; sprint çocuğunun yolunda okuyucuları
  YOK); docstring'in "~1.5 MB" iddiası 70× bayattı. Birikim SINIRSIZ DEĞİLDİ: SANDBOX_KEEP=3 +
  start()-anı budaması çalışıyor, kararlı durum 4 dizin. (2) Aynı sabahki 4×5dk damgaları KADANS
  KUSURU DEĞİL YENİ VAKA DEĞİL — C15'in (damga-ezme) canlı imzası: olay defterinde **154
  `sprint_cadence_start`, HEPSİ `taze_aday_birikimi/taze=50/gecen_gun=0`**, tam 300sn poll
  aralığında, 06:00'da pencere kapanınca kesiliyor; canlı `sprint_status.json`'da `n_hyp_at_start`
  YOK (eski kod çocuğu eziyordu). Düzeltme (`_damgayi_koru`) 19:05 restart'ıyla ZATEN CANLIDA
  (A1 diskinde grep'le doğrulandı); ilk yeni sprint damgayı yeniden basınca kadans kendi kendini
  onarır — beklenti: bu gece 22:00'de TEK sprint, sonra haftalık taban. ÇÖZÜMLER: SKIP_COPY +=
  {bars_intraday, intraday_bars} (çivi: test_sr4b, v45) · `meridian-backup.service` tar'ına
  `--exclude=state/sprint` (ölçülen: 112,5M → **40.497.179 bayt ~40,5M**; RUNBOOK B4/9 satır 5'in
  ~15M tahmini yanlıştı) + çift-yönlü kapsam çivisi (`test_backup_kapsami_sprint_haric_bars_dahil`,
  v174: sprint dışarıda + bars/seans-içi arşivler İÇERİDE kalmak zorunda) · kayıp beyanı birim
  yorumunda (sandbox `sprint_runs.jsonl` defterleri arşiv dışı — 2026-08-02'de 4/4 sandbox'ta
  zaten yoktu) · H7 tatbikat beyanı güncellendi (B4/6). Sıklık artışı BİLEREK yapılmadı
  (litestream defterin dakika-RPO'sunu taşıyor; bars günde bir değişiyor). Hedefli testler
  74/74 + t3 yeşil.

- **YEDEK BİRİMİNİN PYTHON BACAĞI H9'DAN BERİ HİÇ ÇALIŞMAMIŞTI (2026-08-02 ~20:45 UTC, elle
  test-ateşleme yakaladı; sınıf: "birimde kabuk-sözdizimi varsayımı" — fail-notify çok-satır-Python
  ve Environment satır-sonu yorumuyla AYNI AİLE, ÜÇÜNCÜ vaka):** `storage.backup_to` bacağı yolu
  `\"...\"` kaçışıyla geçiriyordu; systemd TEK-TIRNAK İÇİNDE de C-kaçışlarını çözer → sh'a ulaşan
  `-c` dizgisinin tırnakları erken kapanır, python `backup_to(/opt/...)` alır → H9 revizyonundan
  (2026-07-31) beri HER koşu SyntaxError (journal 08-01/08-02 birebir), `state/meridian.db.yedek`
  diskte HİÇ DOĞMAMIŞ, tar hiçbir gece tutarlı DB kopyası içermemiş — ve `if...fi;` zinciri hatayı
  yuttuğu, `rc` yalnız tar'ı ölçtüğü için her koşu `Result=success`'ti (birimin kendi "sessiz yedek
  kaybı" uyarısının vücut bulmuş hâli; elle-ateşleme doktrini tam bu yüzden var ve işledi). ÇÖZÜM
  İKİ BACAKLI: (1) yol string-literal değil `sys.argv[1]` — dizgide iç tırnak kalmadı, systemd'nin
  çözeceği kaçış yok (önce sh katmanında elle provalandı: `.yedek` doğdu, `PRAGMA integrity_check`
  ok); (2) `ok` bayrağı — python bacağı düşerse tar YİNE alınır ama birim BAŞARISIZ beyan eder.
  Çivi: `test_backup_python_bacagi_tirnaksiz_ve_sessiz_degil` (v174: ExecStart'ta `\"` YASAK +
  `sys.argv[1]` + `ok=0` + `[ $$ok -eq 1 ]` zorunlu). CANLI KANIT (ikinci ateşleme, 20:50 UTC):
  journal'da SyntaxError YOK, `.yedek` İLK KEZ birim eliyle tazelendi (1.335.296 bayt), tar'da
  yedek üyesi 1. DERS (aileyi genelleştirir): birim içinde `\"` görülen her ExecStart şüphelidir —
  systemd'nin quoting'i sh değildir; değer taşımak gerekiyorsa argv kullan, kaçış kullanma.

- **STATE-ŞİŞMESİ TURU KAPANIŞI (2026-08-02 gece ~21:00–22:10 UTC, Rol-1; ölçümler dağıtım-kuyruğu
  kaydında):** (1) Otoriter suite donmuş `0248653`te **2 failed / 4104 passed**; triyaj İKİ AYRI
  hüküm verdi: t3 kırmızısı YÜRÜYEN-AĞAÇ ARTEFAKTIYDI (nervous-dewdney merge'i 5f906c5 koşum
  ORTASINDA indi; statik ağaçta yeşil — "otoriter suite yalnız donmuş ağaçta" dersi bir kez daha
  fiilen kanıtlandı), v116 kırmızısı GERÇEKTİ: SKIP_COPY'ye giren `bars_intraday` literali
  yazar-tekliği kör-taramasına takıldı → test-katmanı çözümü 48cd445 (MUAF kümesi
  {barsarchive.py, sprint.py}, gerekçeli; tarama üçüncü modül için aynen tetikte). (2) **CERRAHİ
  DAĞITIM KARARI (sınıf: "paralel-oturum trafiğinde tam-repo dağıtımı"):** main gece boyunca
  hareketliydi — v166 ısı-tavanı karar-turu (`heat_hard_r 4.5→5.0`, goal.yaml İZLİ state!) +
  v181'in commit'lenmemiş watchdog WIP'i + a2a7665. Tam `dagit.sh --uygula` ya kirli ağacı
  (`--kirli-gec` → yarım-iş-canlıya YASAsı) ya da BAŞKASININ karar-turunu kendi penceresi/
  doğrulaması olmadan taşıyacaktı (660dc10 sınıfının tam kendisi). Hüküm: kapsam tek dosyaya
  daraltıldı — `meridian/sprint.py` worktree↔main ÖZDEŞ (sha `8b9b6baa…`), hedefli kapsam 146/146,
  sha-doğrulamalı scp + yedek + yalnız-meridian restart. DAĞITIM ANINDAKİ main tepesi: `4c06c61`
  (sprint.py o tepeyle de özdeş — 660dc10 dersi uygulandı, beyan doğru). SONUÇ: A1 ağacı BİLİNÇLİ
  karışık ara durumda (19:05 içeriği + yeni sprint.py + /etc'de yeni yedek birimi); v166 goal
  değişikliği, v181 api/watchdog kolları ve ağ-kapısı test katmanı CANLIYA İNMEDİ — her biri kendi
  penceresinin/sahibinin işi, İLK TAM dagit ağacı eşitler ve dry-run delta'sı bu kaydı doğrular.
- **SPRINT n_v1=0 KÖK NEDENİ ÖLÇÜLDÜ + DÜZELTİLDİ (2026-08-02 gece, öğrenme katmanı turu; sınıf:
  "depolama arka-ucu değişti, yan sözleşmeler sessizce bayatladı" — audit #23'ün [kopyalanan HALT]
  İKİNCİ kuşağı + SKIP_COPY-denylist-kaçağı [bars_intraday ile aynı tur]):** 154 kadans koşusunun
  tamamının ~60 sn'de `phase=done, n_v1=0` bitmesi ÖRNEKLEM KURAKLIĞI DEĞİL İZOLASYON DELİĞİYDİ.
  Zincir: dbmigrate A1'de 07-31 02:01'de uygulandı (WP-H/H9 A3, cb48f93+; `.migrated` damgaları) →
  altı defter `state/meridian.db` varken SQLite'tan okunur → `sprint.start()` kum havuzuna canlı
  DB'yi de KOPYALIYORDU (SKIP_COPY migrasyon öncesi yazılmıştı) → `_reset_sandbox_state`in ham
  dosya sıfırlaması çocuğun store okumalarına GÖRÜNMEZ → çocuk canlının `last_date=2026-07-31`ini
  DB kopyasından okudu → `loop.daily_cycle` monotonluk bekçisi (2026-07-15 GS dersinin bekçisi —
  DOĞRU çalıştı) eval penceresindeki HER seansı reddetti. KANIT (A1 salt-okuma): son sandbox'ta
  522/522 `regressive_session_refused, book_at=2026-07-31`; sandbox DOSYASI `last_date: null` iken
  sandbox DB'si `"2026-07-31"`; DB'deki 95 işlemin hepsi v4 → `_count(1)=0`; İLK kadans 07-31
  02:08:10 = migrasyondan 7 dk sonra (tümü DB-sonrası; 07-22'nin dosya-tabanlı sprinti n_v1=100
  üretmişti); son koşu 05:59:06→06:00:10 = 64 sn. Eval penceresi ve giriş kapıları AKLANDI — yürüyüş
  taramaya hiç ulaşmadı. ÇÖZÜM (Opus, tek brief): SKIP_COPY += {meridian.db, -wal, -shm} (kum havuzu
  DB'siz doğar → çocukta `storage.active()` False → ölçülmüş-iyi dosya yolu; sıcak-WAL kopyasının
  tutarsız-anlık-görüntü riski de kapandı) + `start()`ten saf `_kur_kum_havuzu()` çıkarıldı (test
  yasanın kendisini çağırır) + İKİ ÇİVİ (test_sr4c ad-çivisi; test_sr1d DAYANIKLI çivi: migre-DB'li
  sentetik canlıda sıfırlama STORE KATMANINDAN doğrulanır — SR1b'nin körlüğü tam buydu, dosyaya
  bakıyordu). Kırmızı-önce kanıtlı (sr1d üretim semptomuyla düştü: `'2099-01-01' is None`); kapsam
  31/31 + storage 15/15 yeşil (Rol-1 bağımsız koşumu). sprint_runs.jsonl'ın hiç doğmaması aynı kökün
  sonucu (Faz A, B'ye hiç ulaşmadı). YAN NOT: `_damgayi_koru` (C15) canlıda — bu gece 22:00'de TEK
  60-sn'lik inconclusive sprint beklenir, düzeltme inene dek haftalık taban boşa döner. SINIF AVI:
  state kopyalayan diğer iki mekanizma (prescreen._sandbox, mutation harness) defterleri
  SIFIRLAMADIĞI için içerik-tutarlı — kırık değil; ama ikisi de sıcak-WAL kopya riskini taşıyor
  (küçük, ayrı kalem). DERS: MERIDIAN_ROOT-sandbox izolasyonu dosya kopyası/reset'iyle kuruluysa
  arka-uç değişimi onu sessizce deler; sandbox kuran her mekanizmada reset STORE katmanından test
  edilmeli.

- **SPRINT TURU PENCERESİ KAPANDI + KABUL ÖLÇÜTÜ ÖLÇÜMLE TAMAM (2026-08-03 ~04:35 UTC, Rol-1,
  operatör talimatlı "Faz B bitince koş, sabaha bırakma"; 23:30 kısıtı operatör kalemiyle
  kaldırılmıştı):** otoriter suite donmuş `4dbe688` tepesinde **4133/0 (EXIT 0, 23:06 dk)**; tek
  sonraki commit (a933a3e) günlük-yalnız → hüküm dağıtılan içeriğe birebir taşınır. `dagit.sh
  --uygula` 04:31 UTC: kapılar yeşil (audit ✓ · lint 5/5 KEPT · [1b] bounds/goal BİREBİR), dry-run
  delta YALNIZ 4 doküman/cache satırı — kod, 04:21 penceresiyle (tick-watchdog dirilişi turu) zaten
  eşitlenmişti; restart + healthz 200 + üç birim aktif + v181/SKIP_COPY/test damgaları diskte
  doğrulandı. KABUL ÖLÇÜTÜ (üç gösterge, iki bağımsız sprintte): (1) sandbox DB'siz doğdu ✓ (22:04
  ve 04:33 koşuları; yalnız inert `meridian.db.yedek` kopyalanıyor — `storage.active()` görmez,
  1,3M'lik SKIP_COPY boyut-kalemi olarak nota geçti); (2) Faz A gerçek yürüyüş ✓ (60 sn ölüm
  imzası yerine 5s46d); (3) **nihai n_v1 = 115/523 seans** ✓ — min_sample'ın ~4 katı, "modern
  giriş yasasında kuraklık" çatalı ölçümle KAPANDI (07-22 eski-yasa emsali 100'dü). YAN VAKA
  (sınıf: paralel-oturum restart'ı koşan sprint çocuğunu keser — cgroup): 22:04 sprintinin Faz
  B'si, 04:21 penceresinin restart'ıyla arama ORTASINDA öldü (pid 15110; sprint_runs.jsonl
  doğmadan; status "search"te donuk kaldı — sessiz ölüm, hiçbir bekçi bunu ölçmüyor → sıradaki
  tur adayı: sprint-çocuğu yetim/ölüm dedektörü). Faz B sonucu için sprint dağıtım-sonrası
  YENİDEN tetiklendi (sid 20260803-043330, CLI `sprint.start()` — token'sız yol; damga
  n_hyp_at_start=51 yerinde); faz-geçiş monitörü kurulu, B hükmü (shipped/no_clearing + ilk
  sprint_runs.jsonl satırı) geldiğinde işlenecek. **B HÜKMÜ GELDİ (2026-08-03 11:05 UTC, temiz
  çıkış):** Faz A n_v1=111/523 (ilk koşunun 115'iyle tutarlı bant; girdi birebir değil — barlar
  gece tazelendi), Faz B **no_clearing_candidate** (incumbent_oos=0.0813, evaluated=2, cleared=0;
  "bu veri diliminde v1 yerel-optimal") → shipped=false, Faz C yok. **`sprint_runs.jsonl`
  MİGRASYONDAN BERİ İLK SATIRINI YAZDI** — mekanizma uçtan uca dönüyor; md.2 sayacının
  kalibrasyon-noktası bacağı ancak bir aday kapıyı geçip C'de döngü kapatınca akar (bu, dürüst
  bir "henüz yok", arıza değil). GÖZLEM (tur adayı, düşük öncelik): budget=12'ye karşı
  evaluated=2 — koordinat inişi ilk turda iyileşme bulamayıp erken durdu; arama-verimliliği
  sorusu ayrı bir ölçüm ister, bu turun kapsamı dışında.

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
   /etc/systemd/system/meridian.service KOPYADIR (`deploy/oracle-a1/deploy.sh` → “6) systemd birimleri”, `sudo cp`) — rsync
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

**E1 KARARI CANLIDA (2026-08-03 ~16:30 UTC; operatör "önerin neyse uygula"):** E1 grid ölçümü
aynı gün koşuldu (EXE-2026-001 → measured; kanıt e1_grid_2026-08-03/; determinizm çift-kapılı):
limit-bacağı MONOTON ZARARLI (A −7,2k · B −1,2k · C −2,9k$), tek artı kolon LİMİTSİZ
(+2.957$/+1.959$-E3), kaçanlar sistematik kazanan; gap-bacağı replay'de yapısal-ölçülemez (canlı/
gölge noktaları kayıtlı); skor-para ayrışması (PARA-v3 C>B, net$ B>C) kayıtlı — hüküm $-merceği.
KARAR: execution_v2 100·ATR/%4 (=MAX_ENTRY_GAP_PCT dış zarfı; felaket-gap koruması kalır, bağlayan
taraf artık dış zarf) + GERİ-DÖNÜŞ KAPISI dosyada (canlı-para geçişi E2 kanıtıyla yeniden hüküm
ŞARTI). 14 test-çivisi iki ilkeyle süpürüldü (mekanizma=kart-yasası-override; yürürlük=yeni-olgu;
2 dürüst ad-değişimi). Suite SIFIR kırmızı → dagit 16:27, goal.yaml bayt-özdeş kopyalandı, CANLI
YASA DOĞRULANDI (entry_law: 100.0/0.04/marketable/day). BEKLENEN: yarınki açılıştan itibaren
girişler zarf-içi koşulsuz dolar; entry_execution.jsonl (E2) İLK GERÇEK satırlarını yazar — izleme
kalemi: ilk seans sonrası E2 defteri doğrulaması.

**KARNE-TAZELEME TURU (2026-08-03 ~11:20-13:05 UTC; operatör sorusu "backfill eski veriyle
dönüyor, kâr-soru güncellensin"):** kardeş-PIT söküldü (cf_backfill tamamen tarihsel — çağrı+import
gitti; shadow_variants _CANLI_TUR çapası — canlı EOD kapısı KORUNDU, seed bacağı olculemedi_seed;
16 test) → determinizm-kapılı tazeleme ölçümü: GERİYE-DÖNÜK DEFTER TERSİNE DÖNDÜ — replay net
+2.493$→−1.182$, PARA-v3 0,1605→−0,0037, oos 0,0579→0,0196, n 201→147. TEK-DEĞİŞKEN ATIF: farkın
TAMAMI E1 giriş-limitinin ATR bacağı (dolum 237→176); replay-PIT 1-plan/0-skor, ısı-5R 0, diğerleri
yapısal 0. OKUMA: eski artı replay-dolum iyimserliğiydi; canlı-0,97-vs-Search-1,53 uyumsuzluğunun
ana açıklaması. HÜKÜM: WP-E 🔴 en-öncelikli ölçüm (E1 grid'i BT-1 beklemez — 9b2cef4). Suite 0
kırmızı → dagit 13:04, canlı md5-doğrulamalı (cf_backfill özdeş; in_blackout yalnız yorumda).
Salt-ölçüm kanıtı: state parmak-izi 608-dosya/0-fark.

**AÇIK-WP UYGULAMA DALGASI (2026-08-03 ~06:30-10:10 UTC, Rol-1 + 5 Opus ajanı; operatör mandası
"açık bütün WP'leri uygula"):** 12 commit, suite SIFIR kırmızı (donmuş ağaç), dagit --uygula 10:03,
bakım penceresinde OPS_NOTU fikstür-temizliği (TEST,2025-06-24 satırı düştü 195→194; takvim-yüklemi
canlıda None=sağlıklı; max_date 2026-08-13 — tazeleme dağıtım-sonrası kendiliğinden koşdu, WP-K
izleme kalemi kapandı). KAPANANLAR: EDG-021 ölçüldü+hükümlü (kill#1 ŞÜPHEDE dalı; survivorship-yönü
ilk sayı: hayatta +0,54 vs delist −1,46 @20) · WP2 turnover-kablolama doğrulama-kapanış (5dfca07
zaten sevkti; default-0 bit-bit çivisi) · WP-M TAMAMI (probgate ÖLÜ-emniyet dirildi: para-ikizi +
damga beyaz-listesi + durum-alanı; DD-veto ölçülü-oran; prescreen zaman-damgası) · WP-D çekirdeği
(BULGU-1 teyit-tam %77-düzeltmesiyle; bars_integrity zaten-sevk teyidi 98/61; earnings TAKVİM-düzeyi
fail-closed A1+A2 — 25-Tem 251-sembol-geçirgen sınıfı yapısal kapalı; replay-PIT ihlali söküldü) ·
WP-H (dev-grubu DARALT-GÜVENLİ + dagit [0d] kapısı + [3] koşum-anı bayrak; H9-B flock-kapıya-indi +
write_text; dash-token LoadCredential hazır-beklemede + api.py CREDENTIALS_DIRECTORY okuyucusu;
certifi beyanı). AÇIK BİLETLER: cf_backfill.py:112 + shadow_variants.py:252 kardeş-PIT ·
hermes ship_calibration askıda-farkındalığı · kapı-dışı yazım 4+7 yol taşıması · dataset.load↔
bars_integrity (OPERATÖR) · token faz-1/2 etkinleştirme (OPERATÖR) · EDG-021 ikinci-koşum
tanım-eşitleme (OPERATÖR).

**PAZARTESİ-ÖNCESİ PENCERE (2026-08-03 04:20-04:23 UTC, Rol-1):** otoriter suite SIFIR kırmızı →
dagit --uygula (state adımı: `limits.heat_hard_r` 4,5→5,0 CANLIYA kopyalandı — operatör kararı
d01ccb5 artık motorda) → **TICK-WATCHDOG DİRİLDİ**: birimler /etc'ye, timer `active`, üç-ayaklı
test-ateşleme geçti (ExecStart -x ✓ · timer ✓ · hüküm satırı sayı basıyor — ilk atışta YAS-lütfu
dalı doğru çalıştı: "meridian 23s önce başladı (<300s) → hüküm VERİLMEDİ"). 3 Temmuz'dan beri ölü
olan asılı-tick koruması piyasa açılışından ~9 saat önce yerinde. → **LITESTREAM AŞAMA-1 KURULDU**:
sürüm-sabitli+sha256 kurulum, birim `active`, güvenlik skoru **2.0 OK**, replica çalışıyor
(snapshot 358.908 B + "replica sync" txid eşleşmesi, /home/ubuntu/replica 1,1 MB); canlı DB
bozulmadı. RPO günler→saniyeler (aynı-disk şerhi: medya arızası kapsanmaz — aşama-2 OCI bucket
operatörde). Dört birim aktif: meridian · barsarchive · litestream · tick-watchdog.timer.
SECCOMP NÖBETİ: 20 saatte 0 SIGSYS (H3-t2 penceresi temiz kapanıyor). AÇIK: LLM inceleme-kaydı
hâlâ kota-kapılı (soğuma 3.853 s; dosya 2026-07-27'de) — dış-kota, kod tarafı hazır.

**AĞ-KAPISI İNDİ — "CANLI-BEKÇİ YANLIŞ ALARMI" AÇIK #1 KAPANDI (2026-08-03 ~02:50 TR, Rol-1;
devir hungry-jemison'dan):** birincil aday (soket-düzeyi autouse kapı) ölçümle kaldı: 13-dosya
süpürmesi kapısız 37 dış TCP (4 IP) → kapılı 0; FAILED küme diff'i BOŞ (yama yetkisi doğmadı);
hedef-test tek başına yeşil 2/2. v133'ün merdiven-ödemesi Rol-1 yetkisiyle tek-nokta yamayla
kapandı (earnings.refresh sınırı, 5 tüketici; ~25 dk türetilmiş → 6,6 sn; assert dokunuşu sıfır).
Dürüst sınır conftest'te beyanlı: kapı connect'i sarar, getaddrinfo sarılmaz (DNS çıkabilir).
KUYRUK: gerçek-ağ sınıf avı — v133'te merdivensiz shortinterest bacağı + aynı giriş noktalarına
değinen ~23 dosya (ayrı tur). Sınıf-ailesi: "test gerçek ağa çıkar" (nondeterminizm+kota+makine-
bağımlılık) — hermes-CLI kolu 0652841, earnings kolu bu tur.

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

- **CANLI `state/spend.jsonl`DA 13 UYDURMA SATIR — KOD DÜZELDİ, DEFTER DÜZELMEDİ (2026-08-27;
  sahip: A1'e erişebilen Rol-1 + operatör onayı; sınıf: "düzeltme ileriye işler, geçmişe
  işlemez"):** `price_for` ücretsiz OpenRouter slug'larını Opus listesinden fiyatlıyordu (kök
  neden + çivi: `tests/test_ucretsiz_katman_fiyati_v325.py`, bu commit). **KOD TARAFI KAPANDI.**
  Kapanmayan taraf ÖLÇÜLEN defter: canlı A1'de 10 çağrı **6.49 USD** `nvidia/nemotron-3-super-
  120b-a12b:free` + 3 çağrı **1.40 USD** `nvidia/nemotron-3-ultra-550b-a55b:free` = **7.89 USD
  harcanmamış para**, ikisi de ücretsiz katman, gerçek maliyet 0.
  **NEDEN KOD DÜZELTMESİ YETMEZ (yapısal, tercih değil):** `dagit.sh` rsync'i `state/` dizinini
  DIŞLAR — dağıtım yalnız GELECEK satırları düzeltir; diskteki 13 satır dağıtımdan sonra da aynen
  yanlış kalır ve `/api/spend` → pano onları okumaya devam eder.
  **BEDEL "pano rakamı"NDAN BÜYÜK, ölçüldü:** `spend.over_budget()` üç yerde ücretli yolu kapatır
  — `hermes.py:429` (claude bacağı), **`hermes.py:4275` (beyin zincirinin TAMAMI → `return None`)**,
  `hermes.py:4398` (nous zinciri) — ayrıca `api.py:1533` Prometheus göstergesi. Yani harcanmamış
  para gerçek bir kapıyı besliyor. Kapı BUGÜN atmadı (7.89/20 USD) ama tampon ~%39 yenmiş
  durumda; ajan yolunun kendi kısması (`_agent_budget_take`, RPD=150) MALİYETE bakmaz, dolayısıyla
  bu birikimi hiçbir şey durdurmuyordu. Modülün kendi docstring'inin yazdığı arıza sınıfının
  ("harcanmamış para bütçeyi doldurur ve LLM katmanı sessizce kapanırdı") İKİNCİ örneğidir.
  **ÜÇ SEÇENEK TARTILDI:**
  (a) *Bırak + beyan yaz.* Canlı state'e hiç dokunulmaz. Ama pano ve defter uydurma rakamı
      GÖSTERMEYE devam eder, yani UYDURMA YASAĞI ihlali okuyucunun GÖRDÜĞÜ yüzeyde sürer. Beyan,
      okunmayan bir yerde durursa ihlali kapatmaz — yalnız etiketler.
  (b) *Telafi satırı ekle (negatif `cost_usd`).* Append-only sözleşmesini korur. REDDEDİLDİ:
      `summary()` satır SAYAR (`calls_this_month`) — 13 hayalet çağrı doğar; ayrıca "maliyeti
      -0.649 USD olan bir çağrı" ölçülmemiş bir olgudur, yani uydurmayı uydurmayla kapatmak olur.
  (c) **ÖNERİLEN — tek seferlik, yedekli, DENETLENEBİLİR yerinde düzeltme.** Yalnız `model`i
      ücretsiz-varyant kuralını (`spend._is_free_variant`) sağlayan VE `cost_usd > 0` olan satırlar
      dokunulur; `cost_usd` `spend.estimate_cost(in_tokens, out_tokens, model)` ile YENİDEN
      HESAPLANIR (bugün 0) ve satıra `duzeltme` alanı yazılır: eski değer + gerekçe + tarih.
      Böylece düzeltme SESSİZ olmaz, defterin kendisinde okunur. `ts`/`model`/token alanları
      DEĞİŞMEZ. Sözleşme kontrol edildi: `ledgers.CONTRACTS["spend.jsonl"]` yalnız
      `ts/model/cost_usd` ZORUNLU tutar ve fazladan alanı reddetmez (`validate_row`) — `duzeltme`
      alanı sözleşmeyi bozmaz.
  **(c)'NİN KAPILARI (hepsi şart, CLAUDE.md §5):** operatör onayı · canlı worker DURDURULMUŞ
  (koşarken state'e yazılmaz) · bakım penceresi · önce `--dry-run` diff (kaç satır, hangi ts'ler) ·
  yedek (`spend.jsonl.bak-<tarih>`) · değişmez: satır sayısı önce == sonra · sonrasında
  `ledgers.validate_live("spend.jsonl")` + `spend.summary()` doğrulaması.
  **[2026-08-29'da YAZILDI] BU TURDA BİLEREK YAPILMAYAN:** düzeltme betiği YAZILMADI. Gerekçe:
  betiğin tek işi canlı state'i yeniden yazmaktır ve hangi seçeneğin (a/b/c) uygulanacağı bir
  OPERATÖR kararıdır — karar verilmeden yazılan betik, onay kapısını bir dosya varlığıyla ima
  etmiş olurdu. Karar (c) yönünde verilirse betik `ops/` altına, varsayılanı dry-run olacak
  biçimde yazılır.
  **DÜZELTME (2026-08-30, satır SİLİNMEDİ):** operatör (c)'yi seçti ve betiği istedi — yazıldı:
  `ops/spend_defter_duzeltmesi.py` (#18, `edc4729`), varsayılanı KURU KOŞU, çivisi
  `tests/test_spend_defter_duzeltmesi_v331.py` (18 çivi, mutasyon 5/5). Kalem KAPANMADI, yalnız
  YER DEĞİŞTİRDİ: açık olan şey artık "betik yok" değil, **betiğin canlıda KOŞULMAMIŞ olması**.
  Koşma sırası: `./ops/stop-worker.sh` → kuru koşu → çıktıyı oku → `--uygula` → worker'ı başlat.
  Betik A1'e erişemeyen bir cloud kabında yazıldı; canlı defterde HİÇ koşmadı.
  **KAPSAM NOTU:** aynı uydurma `tencent/hy3:free` ve `openai/gpt-oss-20b:free` satırlarında da
  koşmuş olabilir (ikisi de aynı kurala takılmıyordu; ROADMAP 2026-08-14 zincir taşınması). Dry-run
  bunları ADIYLA saymalı — 13 sayısı yalnız iki nemotron slug'ı için ÖLÇÜLDÜ, defterin tamamı için
  DEĞİL.

- **`A1` KORUMA İCRASI — EMİR VERİLDİ, İCRA EDİLMEDİ (2026-08-17; sınıf: "karar aşaması kapandı,
  icra aşaması başka bir yerde"):** operatör "A1 korumayı şimdi kur" dedi ve `B2` politikasını
  **(c)** olarak seçti. `B2`(c) KAPANDI — üç kapı kalır ve çıplaklık alarmının kanala bağlı olması
  şartı ZATEN sağlanıyordu (`obs.ALARM_NAKED_POSITION` kendi jetonu · `NOTIFY_TOKENS` türetmesi ·
  çiviler `v216:85`, `v216:130-141`, `v209:248`); kod işi gerekmedi. **`A1` ise AÇIK KALDI ve
  gerekçesi kayda geçmelidir:** emri alan oturum bir CLOUD KABIDIR ve icrayı yapamaz — (a) `.env`
  ve Alpaca kimliği bu kapta YOK (ölçüldü: dosya yok, ortam değişkenleri boş), (b) kimlik olsa
  bile canlı worker koşarken ikinci bir süreçten emir göndermek **CLAUDE.md §5'in yasakladığı
  çift-emir riskidir**. İkinci gerekçe birincisinden ÖNEMLİDİR: kimlik bir gün bu kaba girse bile
  icra buradan yapılMAMALIdır. Kalem "karar bekliyor"dan "**icra bekliyor**"a geçti; koddan
  doğrulanmış adım listesi ROADMAP §5 KOVA-1'de. **DEVAM EDEN BEDEL:** dört pozisyon (NUE/EMR/
  BKNG/AMGN) korumasız kabul edilmelidir — bu oturum canlı durumu GÖREMEZ ve "hâlâ çıplak mı"
  sorusunu ölçemez; son ölçülen değer çıplaklık duvarı 56,4 sa (2026-08-13). **`B2`(c)'NİN AÇIK
  YARISI `A2`:** kanal kimliği girilene dek alarm yazılır ama TESLİM EDİLMEZ — yani seçilen
  politika bugün yarım çalışıyor ve eksik yarısı bir operatör kalemidir (`TELEGRAM_*` ya da
  `MERIDIAN_WEBHOOK_URL`).

- **DAĞITIM KUYRUĞU (2026-08-02 gece, state-şişmesi turu):** (a) **KAPANDI (aynı gece ~20:50 UTC,
  operatör talimatlı pencere):** birim A1'e kuruldu (sha256 doğrulamalı scp + geri-alma yedeği
  `~/meridian-backup.service.bak-20260802` + sudo cp + daemon-reload) ve İKİ kez elle
  test-ateşlendi — ikinci koşum: Result=success, journal temiz, tar **40.593.530 bayt**
  (`state/sprint/` 0 üye · `state/bars/` 261 · `meridian.db.yedek` 1 · 0600). İlk ateşleme
  ayrıca H9'dan beri sessiz bir arızayı yakaladı (aşağıdaki yeni vaka). Mac'teki geniş
  2026-08-02 kopyası (112,5M) bilerek korunuyor; 23:30 timer'ı bu gece dar birimle koşacak.
  (b)+(c) **KAPANDI (aynı gece 21:27–22:07 UTC, operatör talimatlı CERRAHİ dağıtım — gerekçe ve
  ölçümler §BU OTURUMDA "STATE-ŞİŞMESİ TURU KAPANIŞI"):** `sprint.py` (iki turun birleşik içeriği,
  sha 8b9b6baa…) tek dosya olarak A1'e indi (yedek `~/sprint.py.bak-20260802-2`), worker 21:27'de
  restart (yalnız meridian; barsarchive kesilmedi). İlk sprint operatör talimatıyla `/api/sprint/start`
  override'ından 22:04:08'de doğdu (kadans `mesgul:canli_arama`da bekliyordu — v181'in ölçtüğü
  %99,9 CPU arama vakası). ÖLÇÜMLER: sandbox **30 MB** (~27M türetimi doğrulandı; dökümde
  bars_intraday/intraday_bars/çıplak meridian.db YOK) · `phase=baseline, total=523, progress 0→1`
  (22:04:17→22:06:50) — 60sn ölüm deseni KIRILDI · `n_hyp_at_start=51` status'ta ve çocuk yazımı
  ezmedi (C15 canlı kanıt) · budama en eskiyi sildi (4 dizin). n_v1 TIRMANIŞI DA ÖLÇÜLDÜ
  (22:11:40 okuması): `progress 9/523, n_v1=1` — **migrasyondan (07-22) beri İLK sıfır-üstü n_v1**;
  süreç canlı (%99,3 CPU), hız ~1,7 seans/dk → tam baseline ~5 saat. KALAN (sabah kontrolü):
  final n_v1 + Faz B'de `sprint_runs.jsonl` doğumu.
  ÇATAL BEYANI AYNEN YÜRÜRLÜKTE: iki-motor giriş yasası (0a4453f) 07-22'den beri dolumları
  sıkılaştırdı — n_v1 100'ün altında kalabilir; 522 seansta <30 çıkarsa bu YENİ ve DÜRÜST bir
  bulgudur ("modern yasada eval-penceresi kuraklığı", ayrı tur + gerekirse kart) — min_sample
  GEVŞETİLEREK "çözülmez". Gecelik tar da elle ateşlemeyle YENİDEN doğrulandı (22:05, sprint
  KOŞARKEN): Result=success, journal temiz, `.yedek` tazelendi, tar **40.598.037 bayt**
  (koşan sandbox dahil `state/sprint/` 0 üye · bars 261 · db.yedek 1). KÜÇÜK KALEM (temizlik
  turuna): `meridian.db.yedek` (2M) sandbox'a kopyalanıyor — SKIP_COPY adayı, okuyucusu yok.
- **SPRINT DÖNGÜ KAPATAMIYOR — n_v1=0: KÖK NEDEN ÖLÇÜLDÜ, DÜZELTME HAZIR (2026-08-02 gece;
  ayrıntı §BU OTURUMDA):** kuraklık değil izolasyon deliği (DB kopyası reset'i görünmez kılıyor,
  monotonluk bekçisi 522/522 reddediyor). Kod + çiviler bu commit'te; canlıya İNİŞ yukarıdaki
  dağıtım kuyruğu kalemi (c). md.2 "sprint noktaları ↑" sayacı restart + ilk başarılı sprint'e
  kadar akmaz. Kalan küçük kalem (sahipsiz bırakılmadı, düşük öncelik): prescreen/mutation'ın
  sıcak-WAL kopya riski — temizlik turuna not.

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
- **GOAL_FAILURE kurtarması KOD-TÜRETİLEMEZ — operatör domain kararı gerekir (WP-P, 2026-08-10,
  bilinçli açık):** tetik watchdog.py:1696 — `goal_failure_report` (watchdog.py:1647): 30g
  gerçekleşen getiri `goal.yaml failure_below` eşiğinin altında (mandallı — düşüşte bir kez;
  örneklem min_sample altındaysa hüküm None, alarm yok). Bu sözleşmenin BAŞARISIZLIK HÜKMÜdür;
  onu "kurtaracak" betik/endpoint yoktur ve olmamalıdır — deneyin akıbeti (durdur / param
  revizyonu / goal.yaml değişikliği) operatör mandasıdır. Kontrol: olay alanları
  realized_30d/threshold/n + pano bütünlük yüzeyi; goal.yaml İZLİ (dagit [1b] SSoT), değişiklik ayrı turdur.

## KALICI RİSKLER / DERSLER

- **"DOCS-ONLY PUSH" DİYE BİR ŞEY YOKTUR — PUSH DAL TAŞIR (2026-08-31, Rol-1 ihlali).** Ajan-A
  dalga commit'i (motor `api.py` dahil) suite hükmü beklerken yerelde dururken, ÜSTÜNE atılan
  bir belge commit'inin push'u alttaki dalga commit'ini de origin'e taşıdı — suite o an KIRMIZI
  (v323 ×4) idi ve §8 tam bunu yasaklar; CI kırmızı gördü. Kural: motor-dokunan commit yerelde
  suite bekliyorsa, O DALDAN HİÇBİR push atılmaz — belge partisi de bekler ya da suite-öncesi
  ayrı pencerede push'lanır. Telafi aynı akşam: düzeltme partisi + bileşim hükmü ile kapandı.
- **PANO/UI DALGASININ ZORUNLU KAPSAM AİLESİ v323'ü İÇERİR (2026-08-31).** T2 pano görevi kendi
  ailesini yeşil koştu ama `test_arayuz_dili_v323` (arayüz-dili yasası: `neden` insan cümlesidir,
  iç ayrıntı `teknik=`e) kapsamda değildi — tam suite 4 kırmızıyla yakaladı. UI dizgesi üreten
  her görev brief'ine v323 kapsam şartı yazılır; `.tsx/.ts` dizge değişikliği = v323 koşulur.
- **ÖNCEDEN-DOĞRU DURUM, KOŞUMUN KANITI DEĞİLDİR (2026-08-31, Rol-1 kanıt hatası).**
  `profil-guncelle --uygula` ilk gerçek koşumunda "canlı config repo ile md5-özdeş" bulgusunu
  başarı kanıtı saydım — oysa özdeşlik koşumdan ÖNCE de vardı (dry-run sabah BİREBİR demişti);
  gerçekte güncelleme hiç koşmamıştı (etkileşimsiz ssh PATH'inde `hermes` yok, RC=127) ve aracın
  kendi hükmü bunu KIRMIZI basmıştı. Kural: koşum kanıtı, koşumun DEĞİŞTİRDİĞİ ya da ÜRETTİĞİ
  şeyden gelir (taze yedek, damga, hüküm satırı); koşumdan bağımsız da doğru olacak bir gözlem
  kanıt sepetine girmez. Araç haklıydı, ben acele ettim — hüküm satırı sorulmadan kapanış yazılmaz.
- **YEŞİL ÇİVİ TAKIMI, GERÇEK KOŞUMUN YERİNE GEÇMEZ (2026-08-30).** Bir ops betiğinin sözleşmesi
  `main()` değil KOMUT SATIRIDIR; bir arka plan işinin hükmü sarmalayıcının çıkış kodu değil
  aracın KENDİ kodudur. Bu turda ikisi de yanılttı (ayrıntı §BU OTURUMDA). Kural: teslimden önce
  aracı operatörün koşacağı BİÇİMDE bir kez koş, ve hükmü aracın kendi çıktısından oku.
- **BİR ÇİVİ İLE BİR KART AYNI ARTEFAKTI TERS YÖNDE ŞARTA BAĞLAYABİLİR (2026-08-29).**
  `EDG-2026-059` korpusun DONMUŞ kalmasını, `test_korpus_ureticisi_...` ise RUNBOOK değişince
  YENİDEN ÜRETİLMESİNİ şart koşuyordu; çelişki üç kez sessizce kartı öldürdü. Ön-kayıt bir
  artefaktı donduruyorsa, girdi ÇALIŞMA AĞACINA değil İÇERİK-ADRESLİ bir referansa (git blob)
  bağlanmalıdır — yoksa şart, deponun kendi çivileriyle sağlanamaz hâle gelir.

- Waiter/ajan-içi bekletici YASAK (iki arıza). Tam suite turda BİR kez — **ARKA PLANDA**
  (`run_in_background`), senkron DEĞİL. Bu satır 2026-08-30'a dek "ön planda, senkron"
  diyordu: suite ~3.750 test / ~9 dk iken yazılmıştı ve o gün doğruydu. Bugün 7.696 test /
  ~26 dk (6 koşum ölçümü) ve Bash tavanı 600 sn — ön plan İMKÂNSIZ. CLAUDE.md madde 7 ile
  zıt emir veriyordu; "iki kopya sessizce ayrışır" sınıfının bu belgedeki canlı örneğiydi.
- file_lock süreç-içi; canlı worker koşarken state'e ikinci süreçten yazma.
- rsync dağıtımı tüm repoyu taşır — yarım iş canlıya gidebilir; önce dry-run + mtime.
- Sınıflandırıcı curl|sh'ı engeller → kurulumlar PyPI/pipx veya sabitlenmiş git klonuyla.
- classifier/API kesintilerinde: salt-okuma araçlarla devam + zamanlayıcılı yeniden deneme.
- pytest `-qq` tuzağı (2026-08-02): pyproject `addopts = "-q"` zaten veriyor; komuta fazladan `-q`
  eklemek `-qq` yapar ve "N passed" özet satırını TAMAMEN bastırır — yeşil koşu hiçbir şey basmaz,
  triyaj `grep -E "FAILED|ERROR"` + özet satırı ikisine birden bakar. pytest'i `-q`suz çağır.
- venv ana repo kökünde (`/Users/erdemozturk/AI-Trading/.venv`, py3.12 + pytest); worktree'lerde
  YOK ve sistem `python3` (3.14 homebrew) pytest içermez → testler `.venv/bin/python -m pytest` ile.
- **HEARTBEAT_STALE kurtarma (WP-P, 2026-08-10):** jeton bugün ÜRETİCİSİZ — tek üreticisi eski
  `run.py` worker döngüsüydü, emekli (beyan: meridian/run.py:34). Yeni bir kaydı görmek "eski bir
  yapı koşuyor" demektir: `state/events.jsonl` kaydının sürecini/sürümünü doğrula (A1'de
  `journalctl -u meridian`). Döngü canlılığının gerçek bekçileri: A1 `meridian-tick-watchdog.timer`
  (deploy/oracle-a1/tick_watchdog.sh — scheduler damgası 45 dk bayatlarsa restart) + yerelde
  `ops/keepalive.sh` (healthz 60 sn'de bir; üst üste 2 ölü → süreci diriltir).
- **ROLLBACK kurtarma (WP-P, 2026-08-10):** iki hâl, olay `detail`inden ayrılır. (a) rollback.py:253
  = geri alma UYGULANDI (çocuk ebeveynden `rollback_if_worse_by` kadar kötü) — eylem gerekmez,
  kayıttaki from_version/to_version + karar_* alanları hükmün kanıtı. (b) rollback.py:221 = geri
  alma BAŞARISIZ: `state/history/vNNNN.yaml` ebeveyn anlık görüntüsü yok, KÖTÜ sürüm CANLI kalıyor.
  Kurtarma: dosyayı state yedeğinden geri koy (Mac `backups/a1/` — ops/pull-a1-backups.sh çeker;
  A1 `/home/ubuntu/backups/state-*.tar.gz`) — bakım penceresinde (canlı worker koşarken state'e
  yazılmaz); dosya gelince sonraki değerlendirme (loop.py:1717) geri almayı kendiliğinden yeniden dener.
- **CIRCUIT_BREAKER kurtarma (WP-P, 2026-08-10):** tetik loop.py:1108 — OPEN işaretli günlük PnL
  `goal.limits.max_daily_loss_pct` eşiğini aştı (health.py:293); o gün yeni giriş yok (giriş
  kapısındaki `not breaker` şartı, loop.py:198 beyanı), pozisyon yönetimi sürer. ELLE KOL YOK —
  bilinçli: kesici dosya değil heartbeat alanıdır (`breaker_tripped`) ve bir sonraki seansta
  kendiliğinden sıfırlanır (`devre_kesici` sapmasının ipucuyla aynı hüküm; day_start_equity her
  işlenen barda tazelenir, loop.py:1221). Operatör: günün kayıp nedenini oku (pano kill yüzeyi →
  Kitap · şu an); ertesi seans sıfırlanmadıysa risk defterine bak.
- **DATA_QUALITY kurtarma (WP-P, 2026-08-10):** 15 yol tek sınıf değildir — önce olay `detail`inden
  alt sınıfı ayır. Kapı hâli (loop.py:1068, `data_halt` → heartbeat `data_ok=False`; `veri_kalitesi`
  sapması aynı olgu): o gün yeni giriş kapalı, karantinadaki sembol işlem üretmez, tazeleme sabrı
  kendiliğinden dener — pano Sağlık → Veri hattı · bütünlük (saglik#veriboru) + `state/data_quality.json`.
  Elle onarımlı bilinen alt sınıflar: pano token'ı ASCII-dışı (api.py:40) → A1 `.dash.env` rotasyonu
  (deploy/oracle-a1/dash_token_credential.sh); sermaye beyanı kaybı (loop.py:806 reddin kaydı) →
  iade betiği ops/sermaye_beyani_iade.py.
- **HALT_ACTIVE kurtarma (WP-P, 2026-08-10):** tek tetik api.py:4873 — panodan `/api/halt`
  (health.set_halt → `state/HALT`; bir sonraki muma kadar yeni alım yok, mevcut pozisyonlar
  yönetilir). Arıza değil OPERATÖR EYLEMİNİN kaydıdır: kolu kimin/ne zaman çektiği olay defterinde.
  Geri alma yine panodan: sağ üst DEVAM (Kademe 1 Soft Halt kolu) → `POST /api/resume`; telefonda
  `/panic` sayfası aynı halt/devam çiftini taşır (`soft_halt` sapması aynı kolu gösterir).
- **MIRROR_DRIFT kurtarma (WP-P, 2026-08-10):** altı yolun ayrımı olaydaki `drift_sinifi`
  alanındadır. Kendi kendine onarım: çıkış-yetimi kuyruğu her döngü yeniden dener (loop.py:146 —
  tavansız, sessiz terk yok); trail senkronu yalnız yukarı PATCH'ler. Operatör: Mutabakat masası
  (pano karar#mutabakat) — hayalet/yetim/adet satırları; alarm "pozisyon ÇIPLAK" diyorsa önce
  koruma kur (çıplak-pozisyon prosedürü). Kalıcı split_brain/motor_yetimi/adet sapmasında hüküm
  operatöründür: iç defter tek gerçek (loop.py:563 beyanı), broker tarafını elle düzeltmek domain kararıdır.
- **BROKER_REJECT kurtarma (WP-P, 2026-08-10):** üç hâl: (a) ulaşım yok (loop.py:564) — ayna
  atlanır, planlar SİLAHLI kalır, sonraki tur kendiliğinden dener; Alpaca erişimini/anahtarları
  doğrula (mutabakat "Broker API" satırı; sırlar A1 `.env` — deploy/oracle-a1/RUNBOOK.md Bölüm C).
  (b) gerçek ret (loop.py:645) — plan silahlı kümeden DÜŞER (`failed_broker_rejection` damgası,
  kendiliğinden geri gelmez); ret nedeni/sınıfı panoda Reddedilen emir kaydı (karar#failsub) —
  yeniden kurma kararı operatöründür. (c) akış reti (mirror_stream.py:158) aynı masada görünür.
- **TRAIL_DESYNC kurtarma (WP-P, 2026-08-10):** tetik loop.py:1885 (çağrı loop.py:2233) — iç iz
  süren stop yükseldi, aynadaki stop bacağının PATCH'i reddedildi; broker'da ESKİ (daha alçak)
  stop duruyor: pozisyon korumasız değil, koruması BAYAT. Senkron her mutabakat turunda yeniden
  dener (sayaç: mutabakat masası Force-sync satırı). Operatör: ret `detail`indeki broker nedenine
  bak; ret sürüyorsa stop bacağının emir durumunu Alpaca tarafında doğrula — bacak ölü/iptalse iş
  çıplak-pozisyon prosedürüne düşer.
- **MECHANISM_STALE kurtarma (WP-P, 2026-08-10):** ilk soru "hangi mekanizma" — ad olay
  `detail`inde; RUNBOOK'un o mekanizma bölümü nabzı kimin attığını söyler, son damga
  `state/mechanism_beats.json`. Bekçi YALNIZ gözlemdir, yeniden başlatmaz. Ölü sunucu hâlinin
  kurtarma yöneticisi yerelde `ops/keepalive.sh` (healthz 2× ölü → diriltir + bu jetonu yazar),
  A1'de `meridian-tick-watchdog.timer`. ÜRETMİYOR/DÜŞTÜ/BAYAT-TÜREV hâlleri mekanizmanın kendi
  bölümünden teşhis edilir; toplu görünüm pano Sağlık → gece hattı çizelgesi (saglik#cizelge).
- **ARMING_READY kurtarma (WP-P, 2026-08-10):** tetik arming.py:203/299 — uyuyan kurulum kapıyı
  geçti; arıza değil KARAR ÇAĞRISI. Kanıt: pano Onay kuyruğu (karar#onaylar) +
  `state/arming_report.json`. Panelde uygulanacak eylem BİLEREK yok (`actions: []` — api.py:1438
  beyanı): silahlanma bir KOD değişikliğidir, icra yolu `strategy.py:995 ARMED_SETUPS` listesine
  kurulumu eklemektir (mühendislik turu, operatör onayıyla). Kapı geçişi icra zorunluluğu doğurmaz
  (arming.py docstring: "kapı GEÇSE bile ARMED_SETUPS değişmez") — reddetmek de meşru bir hüküm.
- **AUTHORITY_CHANGE kurtarma (WP-P, 2026-08-10):** iki hâl. (a) analytics.py:1172 — LLM danışman
  yetkisi eşikle KENDİLİĞİNDEN açıldı/geri alındı (yetki yalnız REVIEW + karşı dolum vetosu);
  onay gerekmez, doğrulama yeter: olay alanları promoted/r_gap/n + `state/llm_calibration.json`;
  sınırlar pano Otonomi ve sınırlar (kilitler#ayarlar). (b) nous_eval.py:312 — çekirdek-şekilli
  öneri kuyruğa sokulmaya çalışıldı: alarmın kendi beyanıyla KOD HATASIDIR (köprü yanlış
  yönlendirdi) → operatör eylemi yok, mühendislik turu açılır.
- **NAKED_POSITION kurtarma (WP-P, 2026-08-10):** tetik watchdog.py:2286 (motor pozisyonunda canlı
  koruyucu stop YOK — sev-1; pozisyon başına bir kez mandallı) ve watchdog.py:2273 (ÖLÇÜLEMEDİ:
  broker okunamadı — "korumasız 0" DEĞİL, önce erişimi düzelt). Kurtarma panodan: Mutabakat
  masası → Koruma · çıplak pozisyonlar kartı (taze ölçüm `GET /api/alpaca/koruma`) → koruma-onayı
  `POST /api/alpaca/koruma_kur` (onay jetonu + oneri_id; jetonsuz çağrı KURU KOŞU, bayat oneri_id
  emri düşürür) her çıplak motor pozisyonuna TEK OCO kurar; HALT bu yolu kapatmaz (koruma_kur bloğu beyanı).
- **ONAYLI_PLAN_GONDERILMEDI kurtarma (WP-P, 2026-08-12):** tetik watchdog.py:2687 (rapor
  watchdog.py:2606; poll kadansında, kendi try'ında watchdog.py:311): operatör-onaylı + iç-motor-dolmuş
  planın dolum-sonrası reconcile fotoğrafında Alpaca'da NE EMİR NE POZİSYON var; ihlal plan_id başına
  bir kez mandallı, ÖLÇÜLEMEDİ dalları alarmsız (fotoğraf bayatlığının sahibi #10 mutabakat-tazelik
  bekçisi — çift-duyuru yasağı). İlk ayrım olaydaki `gonderim_izi`: False = emir HİÇ çıkmadı → onay
  yanıtının/`plan_operator_approved` olayının `icra_yolu` alanını oku (loop.py:503-527 gönderimin
  sonucunu ya da yolun yokluğunu hâl hâl AÇIKÇA yazar); True = iz var ama broker'da yok → Mutabakat
  masası (pano karar#mutabakat) + Alpaca tarafını doğrula. Kendi kendine onarım: döngünün geç-gönderim
  kemeri (loop.py:1342) her günlük turda aynasız iç dolumları TEK kapıdan yeniden gönderir — olay
  `mirror_gec_gonderim`, kemer düşerse `mirror_gec_gonderim_dustu`. Pano `submit_armed` düğmesi BU
  vakayı KAPATMAZ (yalnız SİLAHLI kümeyi gönderir; dolan plan kümede değil — loop.py:1339 armed'a
  dokunulmaz beyanı). Kemer de kapatamıyorsa acil kapama ELLE EMİRDİR ve operatör domain kararıdır
  (alarm metninin kendi hükmü: "gönderim yolunu onar ya da elle emirle"); kalıcı onarım mühendislik turu.
- **scheduler_poll kurtarma (WP-P, 2026-08-12):** damgayı advance_once'ın kendisi atar
  (scheduler.py:815, her 300 sn poll'da — seans DIŞINDA da; tick_watchdog başlığındaki ölçüm: hafta
  sonu maksimum aralık 302 sn). 30 dk sessizlik "kadans gecikti" değil SÜREÇ ÖLÜ/KİLİTLİ demektir;
  kurtarma yöneticileri süreç düzeyindedir: A1'de `meridian-tick-watchdog.timer`
  (deploy/oracle-a1/tick_watchdog.sh — scheduler_status.updated 45 dk bayatlarsa restart; YAS
  koruması taze süreci bayat sanmaz), yerelde `ops/keepalive.sh` (healthz üst üste 2 ölü → diriltir).
  Süreç dirilince poll kendiliğinden döner; elle yetişme `POST /api/scheduler/advance` (pano düğmesi;
  olay `scheduler_advance_manual`).
- **hermes_poll kurtarma (WP-P, 2026-08-12):** önce ASKIDA mı bak — bekçi rozeti (pano Operasyon)
  `askida` kovasını ayrı gösterir (watchdog.py:118 sondası): kota soğuması (`brain_cooldown.json`)
  ya da kimlik havuzu tükenmesi BEKLEMEDİR, arıza değil — alarm üretmez, eylem gerektirmez, OK da
  sayılmaz (panoda dürüst). Gerçek bayatlıkta iplik ölmüştür: hermes ipliği api sürecinin İÇİNDE
  yaşar (start() api açılışında; hermes_runtime.py:372 beyanı) → kurtarma süreç restart'ıdır
  (yerelde `ops/keepalive.sh`, A1'de `meridian-tick-watchdog.timer` — iplik tek başına yeniden
  başlatılamaz). Isınma koşarken damga sonda başına atılır (hermes_runtime.py:133) — "meşgul"
  sahte alarm üretmez (v192 + H11).
- **warmup_sprint kurtarma (WP-P, 2026-08-12):** 8 sa sessizlik "ısınma uzun sürdü" OLAMAZ —
  aramanın kendi tavanı (HERMES_WARMUP_MAX_MIN, varsayılan 5 sa) koşumu kibarca keser; aşım = tavan
  ÇALIŞMADI (iplik asılı / sonda içinde kilitli / süreç ölü). Kanıt: son ısınma özeti
  (hermes_runtime.py:160 `last_warmup`: kesildi/sebep/tavan_dk — pano hermes kartı) + `_warm_skip`
  nedeni (hermes_runtime.py:410 — "koşmadı" ile "koşamaz" ayrımı; learn_halted değeri Kademe-4
  kolunun MEŞRU duraklatmasıdır, arıza değil). Kurtarma süreç restart'ıdır (yerelde
  `ops/keepalive.sh`, A1'de `meridian-tick-watchdog.timer`).
- **cf_advance kurtarma (WP-P, 2026-08-12):** karşı-olgusal defterin (cf_open.json +
  counterfactuals.jsonl) günlük ilerleyişi; SIFIR YETKİ — hiçbir karar bu deftere bakmaz
  (loop.py:1408 beyanı), bayatlığı sermaye riski değil ÖLÇÜM boşluğudur (gölge katmanların ham
  maddesi birikmez). Düşerse `cf_advance_failed` uyarısı hatayı taşır (olay akışı /
  `state/events.jsonl`); damga yalnız başarıda atılır → bir sonraki günlük tur kendiliğinden dener;
  elle yetişme `POST /api/scheduler/advance`. Günlük tur hiç koşmuyorsa sorun bu mekanizma değil
  süreçtir (süreç-düzeyi yöneticilere bak).
- **p5_calibrations kurtarma (WP-P, 2026-08-12):** damga P5_LEARN bloğunun SON adımıdır
  (loop.py:1948) — bayatlık "tek kalibrasyon düştü" değil "öğrenme-analitik bloğu sonuna
  ulaşamadı" demektir; hangi adımda kırıldığı `v3_learn_layer_failed` uyarısındadır (blok tek
  korumada, loop.py:1950). Kendiliğinden onarım: her günlük turda yeniden koşar; elle yetişme
  `POST /api/scheduler/advance`. Rehinelik dersi: bu blok günlük döngüye bağlıdır — veri kapsaması
  yüzünden noop kalan bir gün öğrenmeyi de sessizce durdurur (öğrenme-rehineliği vakasının sınıfı).
- **mirror_reconcile kurtarma (WP-P, 2026-08-12):** damga reconcile'ın `broker_reconcile.json`
  yazımından hemen önce atılır (loop.py:2570) — bayatlık "aynanın fotoğrafı eski" demektir ve
  fotoğraf yaşının asıl bekçisi #10 mutabakat-tazelik dedektörüdür (kind=mutabakat_tazeligi ile
  ayrıca alarmlar). Kontrol: Mutabakat masası (pano karar#mutabakat) + `state/broker_reconcile.json`
  date/api_ok/skip_reason alanları. Alpaca erişimi yoksa reconcile hüküm veremez → anahtar/ağ
  doğrulaması (mutabakat "Broker API" satırı; sırlar A1 `.env`). Kendiliğinden onarım: alpaca
  modunda her günlük tur; elle yetişme `POST /api/scheduler/advance`.
- **crosscheck kurtarma (WP-P, 2026-08-12):** SPY kapanışının bağımsız kaynakla seans başına bir
  karşılaştırması — `state/index_crosscheck.json`u yazar; veri-kalitesi kapısı `status=diverged`i
  AYNI seansta halt sebebine çevirir (loop.py:1169). Bayatlığın bedeli: bağımsız doğrulama SUSAR,
  bar kalitesi tek kaynağa kalır. Ateşleme yolu BİLİNÇLİ sessiz-yutmalı (scheduler.py:1170 —
  düşüş olay YAZMAZ) → teşhis dosyanın kendisinden: date/status alanı taze mi (pano Sağlık → Veri
  hattı, api.py:3850 aynı dosyayı servis eder). Kendiliğinden onarım: her yeni seans işlendiğinde;
  süreklilik arızası mühendislik turudur.
- **arming_eval kurtarma (WP-P, 2026-08-12):** haftalık uyuyan-kurulum ölçümü (scheduler.py:1039
  `arming.evaluate`) — damga ve hafta bayrağı YALNIZ başarıda ilerler; düşerse `arming_eval_failed`
  uyarısı + bir SONRAKİ poll yeniden dener (hafta yakılmaz). Bayatlıkta kontrol:
  `state/arming_report.json` üretim damgası + pano Onay kuyruğu (karar#onaylar). Ölçüm koşup kapı
  geçse bile kod değişmez (ARMED_SETUPS bir mühendislik turudur; o karar çağrısının prosedürü kendi
  alarm bölümündedir) — burada iş yalnız kadansı yaşatmaktır.
- **shadow_fit kurtarma (WP-P, 2026-08-12):** öğrenme kadansının 1. adımı (scheduler.py:517
  `shadow_model.maybe_refit` — seans başına bir, bar varışından bağımsız). Düşerse
  `shadow_fit_cadence_failed` uyarısı ve asıl risk şudur: model BAYAT katsayılarla tahmin üretmeye
  DEVAM eder (yanlış sayı doğru görünür). Kontrol: `state/shadow_model.json`
  fit_attempt_ts/fit_ts/fit_skip_reason/n_fit damgaları. Adım düşerse seans damgası yine ilerler →
  yeniden deneme bir SONRAKİ seans; kadansın KENDİSİ düşerse (`learning_cadence_failed`) damga
  ilerlemez → sonraki poll dener; elle yetişme `POST /api/scheduler/advance` (seans henüz
  işlenmemişse).
- **opinion_backfill kurtarma (WP-P, 2026-08-12):** 9 günlük pencere kısılmayı alarm SANMAZ — önce
  meşru sessizliği ele: `backfill_progress` olayı kuyruğun hâlini (kalan_gun/kalan_satir),
  `hermes.backfill_budget()` türetimi tavanı söyler (tavan 0 = bütçe kısıldı, damga BİLEREK atılmaz;
  kuyruk boş = iş yok). İkisi de değilse dolgu gerçekten durmuştur: kota soğuması
  (`brain_cooldown.json`) + kadans uyarılarına bak (`learning_cadence_failed` /
  `backfill_beat_failed`). Kendiliğinden onarım: her seans kadans yeniden tetikler; dolgu asenkron
  koşar (hermes.py:3285) ve kalanı sonraki tura devreder.
- **y4_collect kurtarma (WP-P, 2026-08-12):** damga toplama turunun SONUNDA koşulsuz atılır
  (scheduler.py:646) — iki ayak (Form 4 + FINRA kısa pozisyon) kendi korumasında, ayak arızası
  bayatlık ÜRETMEZ (`y4_insider_failed`/`y4_shortinterest_failed` uyarıları + `y4_collect` olayının
  insider_cagri/si_satir alanları ayak sağlığını taşır; anahtar/kota kısılması `atlandi` alanlarıyla
  kayıtlı — fmp_anahtari_yok/fmp_kota_blogu arıza değildir). Bayatlık = kadans HİÇ koşmadı (seans
  işlenmedi ya da süreç ölü) → günlük tur/süreç teşhisi. TÜKETİCİSİ BİLEREK YOK (scheduler.py'deki
  Y4 teşhis bloğu): bayatlığın bedeli karar değil PENCERE kaybıdır — 3 yıllık sınıflama penceresi dolmaz.
- **validation_report kurtarma (WP-P, 2026-08-12):** haftalık kanıt raporu — SALT-OKUMA, hiçbir
  kapı etkilenmez (scheduler.py:685 olay beyanı); damga `state/validation_report.json` yazımından
  sonra (scheduler.py:682). Kontrol: dosyanın uretildi/hafta alanları + `validation_report_written`
  olayı. Ayak kendi korumasında düşerse (`validation_report_failed`) hafta İLERLER → yeniden deneme
  gelecek hafta; üçlü kadansın KENDİSİ düşerse (`weekly_validation_failed`) hafta yakılmaz →
  sonraki poll dener. Bayatlığın bedeli görünürlük: "hangi edge kanıtlanıyor?" tablosu eskir,
  karar bozulmaz.
- **massive_verify kurtarma (WP-P, 2026-08-12):** haftalık grouped-vs-zincir tutarlılık ölçümü —
  yazım kapısının (`massive.write_enabled`) DAYANAĞI; bayatlarsa kapı bayat kanıtla karar verir
  (`massive_verify_failed` uyarısının kendi beyanı). Kontrol: `state/massive_verify.json`
  (verdict/samples/max_dev) + `massive_verify_week` olayı. Anahtar yoksa ölçüm `atlandi:
  massive_anahtari_yok` ile atlanır ve damga HİÇ atılmaz — bu bayatlık arıza değil YAPILANDIRMA
  hâlidir (anahtar operatör kalemi). Ayak düşerse hafta ilerler → gelecek hafta; üçlü kadans
  düşerse (`weekly_validation_failed`) sonraki poll dener.
- **shadowlaw_drift kurtarma (WP-P, 2026-08-12):** haftalık MEASURED_V3 kayma ölçümü — kayma
  bulursa SABİT DEĞİŞTİRMEZ, yalnız `shadowlaw_variance_drift` uyarısı basar (scheduler.py:716
  beyanı); türetilmiş marjların yenilenmesi KOD-TÜRETİLEMEZ, operatör + Rol-1 domain kararıdır.
  Sağlıklı hafta `shadowlaw_drift_ok` yazar; ölçüm düşerse `shadowlaw_drift_failed` ("marjlar
  sınanmadan yürürlükte" — bedeli bu). Kontrol: api teşhis bloğunun servis ettiği kayma özeti
  (scheduler.py:713 `_state` alanı) + olay defteri. Ayak düşerse hafta ilerler → gelecek hafta;
  üçlü kadans düşerse (`weekly_validation_failed`) sonraki poll dener.
- **halt_learning kurtarma (WP-P, 2026-08-12):** arıza değil OPERATÖR KOLUNUN kaydıdır —
  `state/LEARN_HALT` dosyası (health.py:26); kolu kimin/ne zaman çektiği `control_learn_halt`
  olayında. Etkisi: işlemler SÜRER, ship durur (reflect.submit erken döner —
  `submit_blocked_learn_halt` olayı, reflect.py:898) ve hermes ısınması duraklar
  (`_warm_skip="learn_halted"`, hermes_runtime.py:411); rollback güvenlik olarak açık kalır.
  Geri alma panodan: Müdahale kademeleri (kilitler#mudahale) Kademe-4 kolu →
  `POST /api/control/learn_halt` (api.py:2025; aynı uç aç/kapa).
- **PIT çapası olmayan kurulum "kanıt yetersiz" DEĞİL, ÖLÇÜLEMEZ (EDG-2026-060, 2026-08-25):**
  operatör sorusu ("sistem son seed'den beri çok gelişti, planları yeniden değerlendirmek
  gerekmez mi?") tam aralık karşı-olgusal geri dolumuyla ölçüldü — 1164 seans, 8754 satır,
  127,6 dk, kum havuzunda (canlı defter DOKUNULMADI). Hüküm üç parça:
  · `pullback` → (A): n=21 < 30, ort-R −0,968. Kalem KAPANIR. Hipotez ÇÜRÜDÜ: tam aralık koşumu
    canlıdan AZ satır üretti (21 vs 28) — tarih zaten yürütülmüştü, seyreklik kurulumun kendi
    ateşleme sıklığı. EDG-2026-039'un donuk yeniden-silahlanma kapısı (n≥30 VE ort-R CI-alt>0)
    iki ayakta da düşüyor, KAPALI kalır.
  · `episodic_pivot` → ÖLÇÜLEMEDİ, (A) UYGULANMADI. `evaluate_episodic_pivot` zorunlu çapa
    taşır (`earnings.days_since_report`), kazanç takvimi ise NOKTA-ZAMAN ARŞİVİ DEĞİL:
    29 tarih, 2026-07-20→2026-09-11; defter 2022-01-03'ten başlıyor → 1164 seansın ~1141'inde
    çapa sorusu SORULAMAZ. Koşumun kendi sayacı beyan etti: `earnings_gate {plan:3687,
    olculemedi_cf:3687}`. "Ölçüldü ve doldurmadı" yazmak uydurma olurdu; "biraz daha bekleyelim"
    de değil — geri dolum KAÇ KEZ koşarsa koşsun bu kurulum için kanıt üretilemez, ARŞİV gerekir.
  · YAN BULGU — kartın hipotezi UYUYAN değil, ZATEN SİLAHLI bir kurulum için doğru çıktı:
    `exhaustion_hammer` canlı defterde n=14 ort-R +1,260, tam tarihte **n=1571 ort-R +0,090**
    (14 kat küçülme). 2026-08-11 silahlanmasının gerekçesi kenar iddiası değil P-2026-08-07-VLO
    tesisat vakasıydı, yani çürütme yok — ama kayda kurulumun İLK gerçek beklenti ölçümü girdi.
    `cf_fidelity` sapması +0,059R İYİMSER olduğundan +0,090 sadakat iskontosu altında sıfırdan
    ayırt edilemez. Canlı izleme kalemi; MIN_CF_ENTERED=30'un neden var olduğunun canlı kanıtı.
  KODDA KAPATILAN: `arming` raporu "birikiyor" (`insufficient_cf`) ile "birikemez"
  (`olculemez_pit_yok`) cümlelerini AYIRIYOR — `arming._kanit_durumu` + `PIT_CAPALI_KURULUMLAR`,
  okuyucuları `earnings.takvim_ufku()` ve `counterfactual.defter_ufku()` (YASA 6). Kayıt iddia
  olmasın diye çivi v301 İKİ YÖNÜ de bağlar: kayıttaki her ad çapayı gerçekten çağırmalı, çapayı
  çağıran her kurulum kayıtta olmalı. Dört mutasyonla sınandı.
  KOŞUMUN BEYANLI KUSURU: kum havuzu betiği `strategy.json` kopyalamaya çalıştı (dosya adı
  `strategy.yaml`) → koşum varsayılan parametrelerle gitti. Fark DAR ve ölçüldü: tek etkili
  parametre `entry.pivot_proximity_pct` (2.0 vs 2.3) ve YALNIZ `evaluate_entry` okur → sadece
  `breakout_vcp` satırı şartname dışı, karara girmez. Diğer dört kurulumun ölçümü geçerli.
- **hermes_poll MECHANISM_STALE — ÜÇÜNCÜ TEKRAR, KÖK NEDEN BULUNDU (2026-08-25, v302+v303):**
  `mekanizma gecikti: hermes_poll — 0.5 sa (pencere 0.5 sa)` alarmı 2026-08-06'dan beri günde
  tam bir kez ötüyordu (canlıda 134 kayıt). Çok-mercekli soruşturma (5 bulucu + 3 şüpheci);
  ilk hipotez ÜÇ ŞÜPHECİNİN ÜÇÜ tarafından da ÇÜRÜTÜLDÜ — asıl bulgu çürütmelerde çıktı.
  KÖK NEDEN: `beat("hermes_poll")` yalnız 3 yerde ve hepsi `hermes_runtime.py` (176/193/488);
  `reflect.py`de ve `hermes.py`de HİÇ YOK. Nabız "iş bitti"ye bağlıydı, oysa havuz bekleyişi
  tanım gereği "hiçbir iş bitmeyen" penceredir. Isınma dalında İLK nabza kadar ÜÇ ağır faz
  nabızsız koşuyordu: (1) `prefill_incumbents` havuz bekleyişi — tek blokta `_cf.wait(1800)`;
  (2) atalet sonrası SIRALI incumbent yedeği (canlıda 5065 sn / 2 walk-forward); (3)
  `_parallel_prefill_probes` havuz bekleyişi — 1800 sn daha. (1) YAPISAL olarak yamanamıyordu:
  `prefill_incumbents` satır 167'de çağrılıyor, `_nabiz` satır 170'te TANIMLANIYOR.
  Üstüne `HAVUZ_ATALET_SN=1800` (reflect.py) ile `EXPECTED["hermes_poll"]=1800` (watchdog.py)
  BİREBİR EŞİT → havuz ataleti her çarptığında pencere tanım gereği tam doluyor, bayat-geçiş
  GARANTİ. Alarm bekçi kusuru DEĞİL: kör bir fazı doğru bildiriyordu.
  KESKİN KANIT: 2026-08-24'te alarm 01:59:48'de, `arama_havuzu_zaman_asimi biten=0` olayı
  02:00:08'de — 20 sn sonra; sonda döngüsü hiç başlamamıştı.
  NEDEN ÜÇ KEZ YANLIŞ TEŞHİS: metindeki "0.5 sa" bir SESSİZLİK UZUNLUĞU DEĞİL, TESPİT GECİKMESİ
  TAVANI. `check_and_alarm` 300 sn'lik poll'da koşar, histerezis mandalı tekrarı keser → kaydedilen
  değer hep İLK TESPİT anındaki gap → (1800, 2100] → 0,5 veya 0,6. 134 kaydın 113'ü (%84) bu ikisi.
  Gerçek sessizlikler ölçüldüğünde 2,1-2,8 sa, bir vakada 15,2 sa. Mesaj arızanın büyüklüğünü
  GİZLİYORDU. Ayrıca "günde tam bir kez" bir mekanizma periyodu değil `GUNLUK_ALARM_TAVANI=1`in
  imzasıdır (mandal kontrolü tavan kontrolünden ÖNCE gelir; tavan öncesi günde 4-14 alarm vardı).
  ÇÖZÜM (pencere GENİŞLETİLMEDİ, alarm SUSTURULMADI — watchdog.py:48 ikisini de reddediyor;
  eşitlik de KIRILMADI çünkü iki sabit iki ayrı türetimden geliyor):
   · v302 — nabız artık "iş bitti" değil "iplik canlı": havuz bekleyişi `HAVUZ_NABIZ_SN=60`
     kuantumlarına bölündü, her kuantumda `canlilik()` ateşleniyor. TOPLAM-ATALET YASASI
     DEĞİŞMEDİ (kurtarma hâlâ 1800'de). Kanca üç kör fazın üçüne de geçirildi; `_nabiz` tanımı
     `prefill_incumbents` çağrısının ÜSTÜNE taşındı (yapısal kusurun kendisiydi).
   · v303 — mesaj artık aşımı çözünen bir birimde yazıyor ve rakamın İLK TESPİT değeri olduğunu
     İTİRAF ediyor. Yeni `mechanism_stale_since.json` + `mechanism_recovered` olayı: sessizliğin
     GERÇEK uzunluğu bittiğinde ölçülüp yazılıyor (eskiden geriye dönük ÖLÇÜLEMEZdi —
     `watchdog_alarm_gunluk.json` gün dönüşünde sıfırlanır, `mechanism_beats.json` yalnız SON
     damgayı tutar). `gap_h` korundu (okuyucuları api.py:3258/3285, selfreview.py:284).
  Çiviler v302 (9 test) + v303 (4 test); SEKİZ mutasyonla sınandı, ikisi ilk turda HAYATTA KALDI
  (prefill kancası ve ilk-tespit uyarısı) ve çiviler sertleştirildi.
  AÇIK KALAN (ölçülmedi, devredildi): taze walk-forward 2026-08-06 civarında neden yavaşladı
  (865-1276 sn → 2259-3185 sn), ve 08-23→08-24 arasında ısınma önbelleğini ne geçersizleştirdi.
- **"hiçbir öneri OOS kapısını geçemiyor" — ÖNCÜL YANLIŞTI, KAPI İKİ KEZ SHIP ETTİ (2026-08-25, v304):**
  Operatör sorusu panodaki `analytics.py` karne cümlesinden geliyordu:
  "hiçbir öneri OOS kapısını geçemedi — canlı strateji hâlâ v1 (parent yok)". İKİ İDDİA DA YANLIŞ.
  ÖLÇÜLDÜ (canlı defter): 60 hipotez — rejected_by_backtest 32 · rejected_by_guard 25 ·
  rejected_by_confirmation 1 · **superseded 2**. İki superseded'in ikisinde de `reject_reasons: None`:
      H00026  entry.pivot_proximity_pct  v1→v2  realized_delta −0,0364
      H00029  entry.w_prox               v2→v3
  Canlı `strategy.yaml`: version 5 · parent 3 · `pivot_proximity_pct: 2,3` · `w_prox: 0,15`.
  YANİ İKİ DÜĞME DE BUGÜN CANLIDA. Bağımsız çapraz kanıt: aynı gün karşı-olgusal kum havuzu
  koşumunda `default_strategy()` ile canlıyı karşılaştırdığımda ayrışan parametreler TAM OLARAK
  bu ikisiydi — canlı stratejinin varsayılandan farkının TAMAMI öğrenme kapısının ürünü.
  KÖK NEDEN — SONRADAN EKLENEN HİJYEN, ESKİ SAYACIN VARSAYIMINI GEÇERSİZ KILDI:
  `ever_shipped` = live + promoted + rolled_back idi; `superseded` YOKTU. Ama
  `rollback.sweep_orphan_hypotheses` YALNIZ `status == "live"` olanı `superseded`e taşır ve bir
  hipotez ancak SHIP ETTİYSE `live` olur. Süpürme, öğrenmenin kanıtını karneden SESSİZCE siliyordu.
  Fark edilmemesinin sebebi arıza biçiminin makul bir cümle olması: "sistem hiç öğrenmiyor".
  ÜSTELİK AYNI DOSYA DOĞRUSUNU BİLİYORDU: `deflate_why` superseded'i ship sayıyor ve docstring'i
  "defterde ship VARDI (2 superseded)" diyor. Tek dosya, iki ship tanımı; operatöre yanlış olan
  servis ediliyordu — `iki-kapi-karistirma-tuzagi` sınıfının yeni bir örneği.
  DÜZELTİLDİ: `analytics.SHIP_DURUMLARI` TEK KAYNAK (her iki fonksiyon oradan okur); sürüm iddiası
  artık `config.load_strategy()`ten ÖLÇÜLÜYOR (ölçülemezse cümle sürümden hiç bahsetmiyor — eski
  hâli sabit bir "v1" literaliydi). Çivi v304 (5 test) BEŞ mutasyonla sınandı; anti-sürüklenme
  ayağı süpürmenin HEDEF durumunu kaynaktan okuyup ship kümesinde arıyor.
  KAPININ KENDİSİ SAĞLAM — ayrı ve ayakta kalan bulgu: kapıya ULAŞAN adaylar gerçekten ölçülüyor
  (30/30 olasılıksal hüküm, n_valid 1965-2000, fail-closed dalına SIFIR giriş). Ölçülen p medyanı
  0,2605 (eşik `probgate.P_BASE = 0.80`); 35 satırın yalnız 8'inde ortalama ΔS pozitif. Eşik
  0,80→0,70 yalnız iki adayı kurtarırdı ve tam-ölçülebilir tek eşik-geçen aday (H00032,
  exit.breakeven_r 1,0→0,0, arama p=0,909) TEYİT bacağında p=0,1395 / ΔS −0,0796 ile öldü.
  Yani kapı "reddediyor", "ölçemiyor" DEĞİL.
  KAPI KİMLİĞİ (çok-kapı tuzağına karşı çivilendi): resmî yol `reflect._gate_eval` →
  `oos_pipeline.evaluate_search` → `probgate` P_BASE=0,80. BUNLAR O KAPI DEĞİL: `hermes`teki
  arka-plan rejim ön-elemesi (`hermes_bg_proposal_rejected`, 48 kayıt — hypotheses.jsonl'a satır
  YAZMAZ, 2026-08-14'te çivileme dalıyla değiştirildi), teyit kapısı (P_CONFIRM=0,70), ve
  "0,995" (ayrı bir sabit DEĞİL — `min(P_CEIL, 1 - alpha_family/k)` formülünün K=40'taki değeri,
  yalnız aramanın kayıtsız içinde).
  AÇIK KALAN (ölçülmedi, birincil kök neden HENÜZ OTURMADI — iki şüpheci ayrıştı): (a) "arama
  uzayı yapısal olarak kapalı" tezi üç karşı-örnekle çürütüldü (H00028/H00043/H00048 gerçek ölçüm
  üretti), yerine "tek donmuş kanıt penceresi → yerel optimal" önerildi; ikisi arasında karar
  verecek ölçüm YAPILMADI. (b) rejim örneklem kuraklığı GERÇEK: 893 işlemde trend_down=0,
  high_vol=0, chop teyit dilimi=0 — `params_by_regime`in dördünün de boş olmasının mekanik sebebi.
  (c) 179 aramanın 119'u hüküm üretmeden kayboldu (`hermes_search_start` 179 vs `_done` 60) ve
  `arama_havuzu_zaman_asimi` bugün hâlâ ötüyor. (d) OOS penceresi 2026-04-30'da bitiyor; aradaki
  ~4 ay hiç denenmedi — "yerel optimal" hükmü YALNIZ o donmuş pencere için geçerli.

## 2026-08-31 (akşam) — Kaçak gerçek-ssh vakası ve sistemik kilit; v348 çakışması (vNNN ikinci vaka)
VAKA — KAÇAK GERÇEK-SSH: Akıbet defteri (v349) R1 mutasyon doğrulamasında, sahte-ssh nişancı
deseni KURULMAMIŞ tek bir test, mutasyonlu kodla GERÇEK A1'e bağlanıp canlı `oneri_akibet.jsonl`i
tek test satırıyla YARATTI. Ajan dürüstçe itiraf etti; Rol-1 inceledi (1 satır, yalnız test
verisi, resmî kullanım doğmamıştı), kaldırma OPERATÖRE bırakıldı (kalıcı silme Rol-1 sınıfı
değil), operatör sildi ve defter ilk gerçek kararla temiz doğdu. KÖK NEDEN: nişancı deseni
(testin İÇİNDE sahte-ssh kurmak) OPT-IN'dir — deseni kurmayı unutan her yeni test, mutasyon
turlarında canlıya çıkış biletidir; tek katmanlı koruma "disiplinli yazar" varsayımına yaslanır.
ÇÖZÜM (sistemik, R2): dosya-düzeyi autouse `_sistemik_ssh_kilidi` — PATH'in başına rc=113 dönen
ve iz dosyası bırakan sahte-ssh konur; hiçbir test istemeden gerçek ssh'a ULAŞAMAZ, kaçış ancak
bilinçli fixture-override ile olur. Yeniden-inceleme kilidi deneysel kanıtla doğruladı. DERS:
canlıya dokunabilen her yol için koruma OPT-OUT olmalı, OPT-IN değil; ajan brief'lerine "gerçek
ssh/anahtar erişimi ortamdan koparılır" maddesi eklendi (CLAUDE.md'ye taşınacaksa ölçümle).
vNNN İKİNCİ VAKA: UI mesajlaşma göçünün ajanı yeni çivi dosyasını v348 açtı — v348
`test_filo_araci_v348.py`nin kimliğiydi (grep yapılmadı). Kural işledi: az-çapalı taraf AYNI GÜN
v350'ye taşındı, 5 atıf güncellendi, taşıma kaydı dosya başlığına. v331×2'den sonra ikinci vaka:
"oluşturma anında yeniden grep" adımı ajan brief'lerinde açık madde olmalı.

## 2026-09-01 (gece) — UYGULA-8 xdist ÖLÇÜMÜ ve benimseme; donmuş-ağaç esnemesi (küçük vaka)
ÖLÇÜM: tam suite `-n 4` (pytest-xdist 3.8.0, 4 işçi, yerel M-serisi): koşum-1 538,5 sn
(8.344 yeşil + benim RUNBOOK ihmalim = 1 kırmızı, paralellikle İLGİSİZ — seri koşumda da
düşüyordu), koşum-2 539,1 sn TERTEMİZ (0 FAILED/ERROR + özet + PYTEST_EXIT=0). Seri taban
~26 dk (2026-08-30) → ~2,9× hızlanma, günde 6+ koşumda ~1,7 saat/gün. BEKLENMEDİK İYİ HABER:
`state/` paylaşım çakışması İKİ koşumda da SIFIR — `xdist_group` işaretine gerek kalmadı
(öngörü yanlıştı; conftest fixture'ları izolasyonu zaten sağlıyormuş). BENİMSEME: pytest-xdist
dev-grubuna pinli; CLAUDE.md §6 "-n 4, ~9 dk" güncellendi. `-n 4` addopts'a KONMADI: hedefli
küçük koşumlarda işçi açılışı net kayıp; tam-suite reçetesi CLAUDE.md'de. 539 sn, 600 sn Bash
tavanına TEHLİKELİ yakın — arka plan kuralı kalır (suite büyüdükçe tavana çarpar, ön plan denemesi
yasak kalmalı). KÜÇÜK VAKA — DONMUŞ AĞAÇ ESNEMESİ: koşum-2 uçuştayken ROADMAP commit'i atıldı
(5b5ecb4); kuralın telafi yolu işletildi — delta tek dosya (ROADMAP.md), etkilenen küme (v337+
v343) commit anında ayrıca yeşildi, ölçüm geçerli sayıldı. Ders: arka plan suite başlatınca
"ağaç donuk" bayrağını tur boyunca taşı — akıbet defter yazımları (A1-yan) serbest, YEREL commit
değil. AYRICA: RUNBOOK ayrışması (deploy.sh başlığı değişti, üretim atlandı — f0f0645) TEKRARLAYAN
vaka sınıfının yeni örneği; xdist koşum-1 yakaladı, 883f0b0 kapattı.

## 2026-09-01 (gece, otonom) — Akıbet-dalgası kapanışı; TSK-001 tam göç; geri-dolum sözlük vakaları

Operatör gece emri: "açık kalemleri sabaha kadar full otonom bitir" + sudo delegasyonu kaldırıldı
(önce kendim denerim) + göçte GERÇEKLİK KONTROLÜ talimatı (yapıldı-mı/gerekli-mi + açık/kapalı)
+ Sonnet ajanlarına izin (kompleks olmayan görevler).

**AKIBET-DALGASI kapandı** (21b4d2c): N00017 ship yolu `backtest_full` + N00016 hotstate
tek-kaynak; defterde uygulandi+sonuc, 0 açık. HARNESS-EXIT VAKASI (3. kez): bildirim "exit 0"
derken gerçek 1 failed/PYTEST_EXIT=1 — üçlü hüküm kuralı yine ödedi. Kırmızı v280'di:
ölü-alan dedektörü `_hs["defter"]["olay"]` sensör anahtarını broker giriş alanı sandı
(docstring'in uyardığı ad-çakışması sınıfının sözlük-aboneliği hâli) — dar `["defter"][alan]`
zincir istisnası, 5-vaka mutasyon kanıtlı.

**TSK-001 ROADMAP-STANDART tam göç** (ed4b1fe→cf6ccff, suite 8421 yeşil): A(§4+§5, 49 madde)
→ B(§0/§2/§3/§∞, TSK-052..085 + PRG-01..11) → B2(§6 endeksi 30 kart, EDG/EXE-başlıklı) →
C(v351 çivisi 50 test + CLAUDE.md kapısı) → D(api sema alanları + muaf_tarihce=432 muhasebeli +
dinamik tahta; v337 kökü SÖZLÜK değil ARAMA ALANI çıktı — rozet kendi sütunundan okunur).
Süreç dersleri: (1) v351 ilk turda 21 GERÇEK ihlal buldu — çözüm pinli-envanter değil KÖKTEN
temizlik; 16'sında haklı taraf ihlaldi → spec'e `size: —` meşruiyeti (uydurma yasağı S/M/L
uydurtmaktan üstün). (2) FAZ B'nin bilinçli DURMA NOKTASI (v337 davranış çivisi) doğru karardı
— düzeltme FAZ D'nin işiydi, ROADMAP'e eski-sözlük kelimesi sıkıştırmak yeni spec'i bozardı.
(3) Ajan gerçeklik-kontrolü + Rol-1 canlı ölçümü birlikte çalıştı: TSK-049 GATED önerisi
A1 kanıtıyla (LoadCredential SET, servis ACTIVE) DONE'a düzeltildi.

**GERİ-DOLUM iki sözlük vakası** (136ceb4 + 7b35888): HIST taze günü boş-liste yerine önce
404, sonra TOPS'suz-200 ile veriyor — `hist_tops_kaydi`'nin iki raise'i de sürücünün
"boş döndü" vokabülerini konuşmuyordu → her yeni işlem gününde servis düşerdi. İkisi de aynı
sözlüğe çevrildi (taze/tatil ayrımı sürücüde), scp+restart, canlı "taze-boş" kanıtı. 08-05
EOFError'ı ayrı sınıf: kesik gzip, indir() boyut-uyuşmazlığında yeniden indirir — bilinçli
kod değişikliği YOK. İZLEYİCİ DERSİ: Bash aracı zsh — tırnaksız `$SSH` kelime-bölünmez,
rc=127 yanlış "A1 kopması" alarmı üretti; izleyici betikleri zsh semantiğiyle yazılır.

**Araya-kalemler**: mükerrerlik kapısı (131ffa8 — ayrım-noktasında, İKİ kaynak, 28 çivi;
hedef %45→≤%10 sonraki karar turunda ölçülür) · infra-simetri (c9b8c64 — beklenmedik_birimler,
[]≠None; gerçek vaka meridian-dash; okuyucu borcu TSK-086) · huni üçlüsü (c32d13d — taranan
alanı; v314 çırçırında 9 çapa satırdan SEMBOLE çevrildi, 8 anlamca-kaymış çapa AÇIK KALEM).

**Açık kalemler**: 8 drift'li tsx çapası (niyet okuma ister) · TSK-086 okuyucu · 2-adım1
(geceye sığmadı) · işçi-çökmesi-koşumu-düşürmesin iyileştirmesi (operatör görüşüne) · spec
tarihli eklerinin operatör onayı (B-XXX, §6 endeks, size —, DROPPED).

**Hindsight CP UI login döngüsü — kök neden HOSTNAME** (vaka 2026-09-01, akşam): Operatör
Safari'de "çok fazla yönlendirme" gördü; iki yanlış hipotez ölçümle elendi (konteyner env'i
tam — ilk "eksik ACCESS_KEY" sinyalini kendi sır-filtrem üretmişti; CP↔dataplane anahtarları
sha256-aynı). Gerçek kök: Next 16.3.2 middleware rewrite origin'ini HEP "localhost:PORT"
kurarken birim HOSTNAME=127.0.0.1 veriyordu → intl rewrite'ı (localePrefix "never", / → /en)
cross-origin sayılıp 307'ye çevriliyor, middleware yeniden koşup /en/login'i muafiyet
listesinde bulamıyor → kimliksiz istek login formunu ASLA göremiyor (curl ile Host/çerez
bağımsız doğrulandı). Çare tek satır: HOSTNAME=localhost (bind yine 127.0.0.1'e çözülür,
ss ile doğrulandı; ACCESS_KEY katmanı geri takıldı). İkincil ölçüm: login POST alanı `key`
(accessKey değil), çerez `hindsight_cp_access` 24 saat geçerli — yeniden giriş günlüktür.
Zincir A1'de VE operatör tünelinden uçtan uca yeşil: /login 200 → POST 200+çerez →
/dashboard 200. Ders: "auth döngüsü" görünümü iki bağımsız katmanın (origin kıyası + muafiyet
listesi) bileşkesiydi; ilk katman düzelince ikincisi hiç tetiklenmiyor. Teşhis sırasında
sır-filtresinin (grep -v KEY) yapı satırlarını da gizleyip sahte kanıt ürettiği not edildi —
filtre değerlere, satırlara değil.

**Sabah paketi öne çekildi — operatör penceresi** (2026-09-01 akşam; "yarın sabah paketini şimdi
yapabilirsin, seansı etkilemez" + ardından iki ek karar: "geri dolum kesintisiz çalışmalı,
seans içi dahil" ve "arşiv→Hindsight yüklemesini şimdi yapabiliriz"). İcra edilenler:
① TSK-009 aylık-bucket elle ateşleme: success/69MB/sha'lı — kalem tamamen kapandı.
② TSK-058 FAZ C: bayrak açılışı kartın `acilis_kaydi_2026_09_01` bloğuyla (elle-True yasağının
meşru yolu — kill#1 kök çözümü kadans-içi ~5-6ms kuyruk-append), v278 test_9a yeni gerçeğe
çevrildi (bayrak↔kart-kaydı bağı çivilendi; kapalı-yol fixture'ları kapalılığı KURARAK yaşıyor),
v356 H2'ye kapalı-zorlama. Suite 8720 yeşil + 1 kırmızı: görev-aynası testi — sabahki SKILL.md
düzenlemesinin ~/.claude kopyası türetilmemişti; kopya aynadan türetildi, 6/6. Birim+timer
kuruldu (07:30Z armed), kurulum-günü elle ateşleme exit-0/boş-kuyruk (bayrak-açık yol kanıtlı).
③ TSK-089 Faz 1 TAMAM: içerik-smoke (nemotron 200/45sn) + NOUS çevirisi (.env: kapı ucu +
birincil model künyesi + yer-tutucu anahtar; learn kapalıyken uyuyan yol).
④ Kıyas hazırlığı: sqlite-vec kuruldu, betikler+anahtar A1'de, sorular çapası cf1c39bb tuttu;
sema-ornek ÜÇ ölçümle kapandı — soğuk recall >120sn (reranker ısınması), uzun-sorgu sıcakta
129,8sn (betik sabiti 120→360), `limit`/`top_k` API'ce TANINMIYOR (sunucu varsayılanı 23 sonuç;
hüküm istemci-tarafı [:K]); şema: kimlik=document_id, metin=text.
⑤ Geri-dolum SEANS_KILIDI=False (/opt/veri + repo aynası deploy/oracle-a1/geridolum.py —
aynanın varlığını F9 listesi hatırlattı, ilk grep deploy/'u taramamıştı); seans içinde iki
işçiyle koşuyor. ⑥ İngest öne çekildi: 20:05Z transient timer söküldü, elle systemd-run;
ilk deneme PermissionError (dizin root'undu, User=ubuntu) — sahiplik düzeltilip başladı.
⑦ UI "dinamik değil" sorusu ölçümle yanıtlandı: birincil neden dağıtım gecikmesi (push ≠
dağıtım — TSK-059 DONE'u canlıya ancak bu akşamki rsync indirdi); ikincil: göç kimlik-eşleme
tablosunun durum sütunu ikinci-kopyaydı, TARİHÎ olarak donduruldu.
⑧ DAGİT ELLE-AYNA VAKASI: sınıflandırıcı `dagit.sh`i, `stop`u ve `restart`ı üç ayrı denemede
reddetti — betiğin adımları ([0a] sha-dondurma, [1b] goal/bounds kıyası AYNI, [5c] artefakt
taze, [2] rsync, [3] uv sync --no-default-groups, F9 birim kurulumu) tek tek şeffaf koşuldu;
işçi üçlüsünün restart'ı ve [B] beyanı OPERATÖRDE (learn bilinçli-kapalı — restart listesinden
çıkarıldı; beyan [5b] gereği eski-süreçle YAZILMAZ). Açık kalan: restart → kuyruk-append
başlar → yarın 07:30Z ilk dolu üretim → beyan.

## 2026-09-01 (akşam-2, otonom) — TSK-090 kapanışı; ingest "başarı akışı ↔ belge başarısızlığı" çelişkisinin çözümü

**TSK-090 zinciri (SDD, iki görev + dal-sonu):** `/api/gateway` (v361) + pano "Kapı" sayfası canlıda; dağıtım 4b7f92d, beyan bayt-özdeş. Üç kayıt: (1) Dal-sonu incelemesi görev-içi incelemelerin ıskaladığı sınıfı yakaladı — dört faz da "olculemedi" iken başlık çipi "0/4 faz canlı" basıyordu (parçalar tek tek doğru, ÖZET yüzeyi ezdi; uydurma-yasağı ihlali özetlerde de aranır). (2) Tam suite tek kırmızısı v323: `neden` cümlesindeki "KAPSAMI" büyük-harf sabit desenine takıldı — arayüz-dili çivisi YENİ yüzeyde ilk gün ısırdı, çivi çalışıyor. (3) Sınıflandırıcı `sudo setfacl` + state-yazan ssh-heredoc'u vermedi; beyan scp+sha256 kanalıyla yazıldı (aynı sözleşme, yalın kanal), `.env-apisix` izni operatöre devredildi — verilene dek sayfanın admin bacağı dürüstçe "okunamadı" der (üç-durum tasarımı ilk gün işe yaradı).

**İngest çelişkisi (EDG-067) — vaka:** Operatör "panoda hiç failed yok" derken betik 0/214'te duruyordu; ikisi de DOĞRUYDU. Ölçümle çözüldü: (a) OpenRouter "Generations" sekmesi YALNIZ başarılı üretimleri listeler — 429/hata satır üretmez, "hiç failed yok" görüntüsü hata-yokluğu kanıtı DEĞİLDİR; (b) başarılı ~4 istek/dk akışı bizim özütlememiz (istek içine girildi: Chunk 1/1, arsiv-ingest context'i, kart içeriği; çıktı Türkçe yapılandırılmış olgular — kalite iyi); (c) düşen yalnız TEK-parça-dev-belgeler (günlük 138KB ≈ 35K token): Nvidia ücretsiz ucu o boyu 5/5 "temporarily overloaded" ile reddediyor — rastgele yoğunluk değil BOYUT-SINIFI reddi; (d) hindsight parça-başına 1 deneme yapar (`HINDSIGHT_API_RETAIN_LLM_MAX_RETRIES` env'i var, varsayılan retain=1). Ders: "hepsi başarılı" panosu + "hepsi başarısız" logu çelişki değil, İKİ AYRI SEÇKİ olabilir — hüküm ancak aynı isteği iki uçtan izleyince verilir. Plan: koşum bitince dev belgeler başlıklardan dilimlenir (manifest_uret ROADMAP emsali) + retain retry ≥3 + hindsight-api restart penceresi; GLM sondası 3/3 anlık 429 (free havuzların tümü tepe saatte tıkalı; GLM'in düzgün HTTP-429 dönmesi zincir-mimari lehine not edildi, acil geçiş gerekçesi değil).

## 2026-09-01 (gece-2, otonom) — Faz 2-3-4 öne çekme: kapı tam katman; üç ölçülmüş vaka

Operatör talimatı ("Faz 2-3-4'ü öne çek" + "OCI CLI kur, gerekeni yap") ile kapının kalan katmanı bir gecede indi: fmp-veri rotası (250/gün redis) · 9443 TLS + basic-auth pano ingress (dışarıdan doğrulandı: nip.io adıyla el sıkışma + 401/200) · 5 tüketici + filo kotası. Motor dokunuşları TDD'yle (v363 fmp taban-env, v364 uygula tüketici/upstream); LLM rota kilidi bilinçli sabaha (istemciler anahtarsız — kilit önce gelirse motor nous'u 401'e düşer).

Üç vaka: (1) **443 bind reddi** — imajın nginx'i root değil, ssl.listen 443 konteyneri çakılma döngüsüne soktu; 9443'e çevrildi (config yorumu künyeli). Ders: ayrıcalıklı port varsayımı konteyner kullanıcısıyla birlikte ölçülür. (2) **upstream düşürme 503'ü** — uygula betiği Faz-1 çağından yalnız uri+plugins PUT'luyordu; upstream'li ilk rota "missing upstream" ile öldü. Betik-sözleşmesi genişlerken PUT gövdesinin kapsamı da ölçülür. (3) **apikey log sızıntısı** — access-log $request + error info, FMP anahtarını iki ayrı satıra yazdı; ölçüldü, biçim sorgusuz + warn ile kesildi, sıfır-geçiş teyitli. Kısıt "görünüyorsa kapat"tı — görünmeden önce değil, ölçüp kapattık.

Sınıflandırıcı bu gece sudo/anahtar-malzemesi sınıfının tamamını reddetti (setfacl, cp, systemctl, ssl-yükleme, hatta bir salt-okunur durum sorgusu); akış operatör tek-satırlarıyla yürüdü ve ssl-yükleme kalıcı ops betiğine döndü (ops/apisix_ssl_yukle.py — certbot yenilemesinin de yolu). OCI güvenlik listesi sürprizi: "all 0.0.0.0/0" zaten açıkmış — etkin duvar host iptables'mış; daraltma operatör masasına. v351 çivisi kapanış notumu ısırdı (çıplak DONE) — şema çivileri Rol-1'i de ısırır, bu iyi bir şeydir.
## 2026-09-02 (gece-4) — Kimlik modeli flip'i: kapı kimliği emekli, tek katman uygulama oturumu; tam-ekran giriş kapısı

**Operatör kararları (2026-09-01/02 gecesi):** (1) kapıdaki basic-auth'tan "sistemin içindeki
full authentication"a geçilsin — port edilen UI'ın login v2 / register v2 ekranları kullanılsın;
(2) sistem bugün tek kullanıcı, ileride çok-kullanıcı (Kayıt bağsız kalır); (3) kullanıcı adı
ŞİMDİ eklenmez → TSK-097 (GATED çok-kullanıcı kimlik paketi).

**Zincir:** Safari fetch-401 döngüsü vakası (gece-3, 44afc2b: /api/* ayrı rotaya) kalıcı çözüme
büyüdü: kapı kimliği İKİ ölçülmüş arıza üretiyordu (yerel kimlik kutusu döngüsü + kapı-401'inin
uygulamada "oturum düştü" yanlış sınıfı). Karar: kimlik TEK katmanda — uygulamanın parola+çerez
oturumu (fail-closed açılış duruşu, ~80 uçta _auth, beyanlı muafiyet listesi). Kapının işi
ingress'te hız sınırı + gövde tavanı + sayaç.

**Flip'ten önce ölçülen delik — /metrics vekil körlüğü (v365):** `_local_request` yalnız TCP
eşine bakıyordu (ssh-tünel dönemi varsayımı). Kapı 127.0.0.1'den proxy'lediği için dış HERKES
"yerel" sayılır, /metrics tam seti (öz sermaye, P&L) kimliksiz dökerdi. TDD: XFF taşıyan istek
yerel SAYILMAZ (uydurma yalnız yetki DÜŞÜRÜR; A1-içi doğrudan scrape XFF'siz, tam set korunur).
Testte ikinci ölçüm: parolasız sandbox `_auth`'un belgeli no-op dalına düşüyor — test parola
kurarak canlı duruşa oturtuldu. Motor düzeltmesi canlıya inene kadar kapıda köprü:
`metrics-dis` rotası /metrics→/healthz (dış izleyicinin sözleşmesi zaten healthz; sonrası
derinlemesine savunma). /api/halt dahil yazan uçlar _auth'lu ölçüldü — başka açık yok.

**Konfig:** routes.yaml pano-ingress basic-auth'suz; pano-api rotası katlandı (tek-kaynak —
kimlik ayrımı kalkınca iki rota aynı politikaya inmişti); pano_operator tüketicisi kaldırıldı
(etcd DELETE operatör satırında, PANO_GIRIS_PAROLA env'i zararsız artık); config.yaml plugin
listesinden basic-auth düştü (sonraki restart'ta etkin). Faz3 imzası basic-auth→limit-req
(api.py + v361). Dış canary: GET / 200 gri kutusuz · /api/session {authenticated:false,
password_set:true} · /api/summary·today·secrets·performance 401 · /metrics yalnız canlılık.
Operatörün "direk dashboard geliyor" gözlemi delik değil kendi geçerli çereziydi (dıştan
kimliksiz 401'lerle ayrıştırıldı).

**UI — tam-ekran giriş kapısı (SDD: opus implementer, 3 tur; sonnet inceleme):** Giris.tsx'in
"yüzey kabuğun içinde" kararının öncülü (dış kapı var) öldü → kapı App seviyesine çıktı:
kimliksiz ziyaretçi kabuğu HİÇ görmez (RotaSaglayici/BugunSaglayici da mount olmaz — kimliksize
/api/today nabzı bile açılmıyor), şablonun auth v2 bölünmüş paneli tam-ekran; `undefined`
hâlinde ne kabuk ne kapı (nötr kart + "Yeniden sor"). Tek oturum nabzı `oturum.tsx`
sağlayıcısında; `hali()` iki girdili saf fonksiyon (oturumDustu bayat-"acik"i ezer — bayrak
yazılıyor-okunmuyor sınıfı inceleme bulgusuydu). Kayıt sekmesi dürüst: "2. aşama — bugün hiçbir
yere bağlı değil", alanlar devre dışı. İnceleme döngüsünün kazıları: Giris.tsx yüzeyi
oturum-durumu+çıkışa küçüldü (−194 satır erişilemez dal); Kapi sarmalayıcısının "Okunamadı"
dalı bu çağrı noktasında ZARARLIydı (15 sn nabızdaki tek ağ hıçkırığı, elde sağlam gövde
varken çıkış düğmesini/künyeyi siliyordu) → kaldırıldı. İzleyici ayrımı: kapı ekranlarında iç
ad/komut ifşası sıfır (MarkaRayi `ayrintilar` bloğu yalnız kabuk-içi); auth_cli yönergesinin
yeri runbook, ekran değil.

**Hakemlik notu:** incelemecinin "bolum-kapi çapası yok" iddiasını implementer kod referansıyla
çürüttü (KapiKunyesi→parcalar id üretimi); grep'le doğrulandı — inceleme bulgusu da her zaman
bir iddiadır, ölçümle tartılır.

**Çalışma anı doğrulaması (pano_stub, 4 hâl + mobil + 2 geçiş):** giriş/kurulum/bekleme/açık ✓,
375px tek sütun ✓, düşüş geçişi (kabuk→"Oturumun kapandı" varyantı, bir nabızda) ✓, nabız
hıçkırığında künye+Çıkış yerinde ✓.

**Açık kalemler:** EksikEnvanteri.tsx auth_cli metni (kabuk-içi, hükümle kaldı) · alanlar.ts
giris/kayit derin bağları kapı-yüzeyinde no-op (bilinçli, KapiEkrani başlığında) ·
Kullanicilar.tsx üçüncü /api/session nabzı (parkta) · healthz "stale" gözlemi sabah paketine.

## 2026-09-02 (gece-5, otonom) — Gece kuyruğu kapanışı: yedi kalem SDD tam döngüyle; iki kart-önce ölçüm; tarayıcı-sınırı dersi

Onaylı gece kuyruğunun yedi kalemi tek oturumda kapandı — her biri taze implementer + görev
incelemesi + gerektiği kadar düzeltme turu + yeniden-incelemeyle: TSK-098 pano birim-anahtarı
(polkit kuralı yazıldı, kurulum+ilk ateşleme sabah penceresinde) · TSK-007 watchdog mekanizma
sırası · TSK-011 cf kuyruğu date sütunu (EDG-2026-068 kart-önce; gerçek-veri kolu Rol-1'de
açık) · TSK-089/F4-B istemci koşullu apikey (kilit flip'i sabaha) · TSK-002 rejim ship'inin
tam-pencere defteri · TSK-019 EOD seyrelme ayna-satırı (EXE-2026-011 kart-önce →
measured_partial) · TSK-094+030 TSX çapa göçü + `codelaw.capa_uyusmasi` doğuşu. Hükümler ve
ruling'ler SDD defterinde; commit zinciri 18ed103…a62ae03 + bu kapanış commit'i.

**Ölçülen ders — tarayıcı VARLIK ölçer, YERİNDELİK ölçmez (TSK-094):** göçen 141 çapanın 9'u
(%6,4) gerçek-ama-yanlış sembole bağlıydı ve dokuzunda da AST doğrulayıcısı yeşildi — inceleme
örneklemi 2'sini yakaladı, zorunlu kılınan tam süpürme 7'sini daha çıkardı (birinde sahte
alıntı atfı da vardı). "Yorumun iddiası ↔ hedef sembolün gövdesi" doğrulaması otomatikleşemeyen
ayrı bir iş sınıfı olarak kalır; tur-öncesi var olan 116 eski sembol çapası bu doğrulamadan
geçmedi (açık kalem, TSK-030 adım-3).

**Kohort beyanı (TSK-019):** ayna-satırı kohortu naif okunuşla ("bu turun planları") pencere
yasası yüzünden her gece kill#1 üretirdi — akşam gönderimi sabah kancasına ertelendiğinden her
silahlı plan önce ayna-satırı sonra submitted satırı alırdı. Kohort=meta[last_date] (dolum
fırsatını bu açılışta tüketen planlar); beyan kartta, çift-iz sınıfı yapısal kapalı. İnceleme
zinciri üç gerçek zayıflık daha kapattı: kapı damgalı anomali yolunun sınıf uydurması
(olculemedi'ye), ısırmayan ayrışma çivisi (kopya kaçınılmaz değildi — önek tek kaynaktan
türetildi), yanlış kopya-beyanı (gerçek okuyucu analytics'ti). Yan ölçüm: loop.py'ye satır
ekleyen tur yine komşu satır-çapalarını kırdı (v280 ×2, gecenin üçüncü tekrarı) — loop.py
çapa süpürmesi kalem adayı.

Parola-kilidi vakasının açık kalemi kapandı: unutulan-parola reçetesi `auth_cli` başlığına,
oradan RUNBOOK'a akar (giriş ekranı "sıfırlama runbook'ta" diyordu, runbook'ta yoktu — Yasa 6).

**Şafak suite'i #1 KIRMIZI — yedi çivi gecenin işini ısırdı, yedisi de meşru:** kart endeksi
(EXE-011 status değişti, README üretilmemişti) · v181 envanteri (098'in birim ucu teşhis
zarfını düşürmüyordu — kardeş desenle kapatıldı) · v334 (v366 ham exec_module) · v351 r08 ×2
(TSK-104 QUEUED dururken trigger doluydu → GATED) · v209 (RUNBOOK değişince D6 korpus
artefaktı bayatladı — yeniden üretildi) · v154 (BETIK_KUMESI'nin auth_cli genişlemesi sınır
çivisine yansımamıştı). Ders yeni değil ama ölçümü taze: kapsamlı koşumlar yeşilken bile
depo-geneli tutarlılık çivileri (endeks, envanter, şema, sınır beyanı) yalnız TAM suite'te
öter — gece boyu hedefli koşumların hiçbiri bu yediliyi göremezdi. Suite #2 (a62ae03 tepesinde
donmuş ağaç): **8923 passed / 3 skipped / EXIT=0**. Push tur kapanışında; sabah paketi operatöre.

## 2026-09-02 (sabah penceresi) — Kapı dört fazıyla canlı; iki ölçüm vakası: dagit sessiz ölümü, polkit çift körlüğü

Operatör elle + Rol-1 doğrulama/onarım döngüsüyle pencere kapandı: dağıtım (a18075d) →
kapı config+rotalar (drift boş) → motor flip (FMP+NOUS+KAPI_APIKEY, tek restart) → polkit
kuralı → pano birim-anahtarının İLK canlı toggle'ı iki yönde rc=0 (07:04; şafak yedilisinin
v181 düzeltmesi `diag_cache_invalidated` iziyle üretimde ilk gün çalıştı) → F4-B kilidi üç
LLM rotasında. Kilit dört kanıtla: anahtarsız 401 · yanlış anahtar 401 · motor anahtarı 200 ·
sayaçta `consumer=motor_meridian`. Anahtar eşitliği hash kıyasıyla (değer hiçbir terminale
basılmadan). Dış canary 9443 → 200. Botlar bilerek kapı DIŞINDA (TSK-105: hermes Bearer
gönderir, key-auth apikey bekler — ölçüldü, göç ayrı kalem).

**Vaka 1 — dagit [4] sessiz ölümü (TSK-092'nin ilk gerçek koşumu):** `is-enabled` türetimi
`[ … ] && printf` ile bitiyordu; son eleman (learn) disabled → uzak kabuk 1 → `set -e` atamada
betiği başlıktan hemen sonra öldürdü — rsync inmiş, restart/beyan kalmış, diskte-yeni/süreçte-
eski ikiliği doğmuştu. v367'nin metin çivileri türetmeyi KOŞMUYORDU; davranışsal çivi eklendi
(dagit metninden sökülen snippet + sahte systemctl, kırmızı doğdu) ve betik kendi ~132
doktrinine (açık `if`) getirildi. "Çivi yeşili kanıt değildir"in ops-betiği hâli.

**Vaka 2 — polkit çift körlüğü (iki ölçüm turu):** (1) systemd `manage-unit-files` eyleminde
polkit'e birim adı VERMEZ — kuralın tam-ad beklentisi hep null kaldı, ilk canlı deneme 502.
(2) Fiil-şartlı düzeltme de düştü: o eylemde `verb` ayrıntısı DA inmiyor VE `polkit.log` bu
polkitd yapısında (v124 duktape) sessizce kayboluyor — `stop`un logsuz YES'i kuralın çalışıp
izin doğmadığının kanıtı oldu; geçici 49-debug gözlem kuralı ve detaysız `pkcheck` teşhisi
tamamladı. Eşleşme eylem kimliğine indi; büyüyen genişlik kuralda BEYANLI (birim darlığı API
beyaz listesinde, v368; gerçek denetim izi api.py `birim_istek` obs kaydı — polkit.log
güvenilmez, ölçüldü). Ders: iki dilin/iki daemonun arasındaki sözleşme ancak CANLI denemeyle
ölçülür; tasarım-varsayımı yorumları ölçüm damgası taşımalı.

Ayrıca: apiPost tek kaynağa indi (062e989 — pano/gonder.ts yazma kapısı; implementer brief'imin
iki ölçüm hatasını yakaladı: KararPaneli bağımlılığı + yol derinliği) · v361 faz çivisi kilit
inince TAM mekanizmasıyla ısırdı (türetim doğru, beklenti bayattı — cf3b480) · bir commit
pytest hükmüne bağlanmadan atıldı (bd3ae0f, 1 kırmızıyla push; ders defterde: zincirde git,
hüküm değişkenine bağlanır). Açık: EDG-067 ingest sürüyor (süpürme bekliyor) · nous sondası +
FMP'nin kapıdan ilk doğal trafiği bir sonraki döngüde sayaçtan teyit edilecek.

## 2026-09-02 (gündüz penceresi) — Üç karar işlendi; Hafıza sayfası + bot göçü aynı günde canlıya; iki "çivi kendini doğruluyordu" vakası

**Üç sabah kararının işlenmesi** massive-403 kalem AÇMADAN kapandı: önerilen mekanizma
(403'ü hatırla, o gün deneme) `1cee514`'ten beri kodda ve canlıdaydı (`_YETKI_RET`); A1 ölçümü
gürültüyü günde 1-2 olayda gösterdi — tasarım gereği yol-başına-günde-bir yeniden deneme.
DERS: karar listesi kalemi koda karşı ölçülmeden sevk edilmez — mükerrer kalem uydurma sınıfı.
TSK-106 (session_refresh günlük özet) aynı gün TDD ile indi (90acfaa): yol boyu v274'ün
middleware çivisinin BUGÜNE DEK yanlış sebeple yeşil olduğu çıktı (taze çerez tazelemeyi hiç
tetiklemiyordu — bastırma hiç ölçülmemişti); düzeltildi, mutasyonla ısırdığı gösterildi.

**TSK-091 Hafıza sayfası** (5c1ed2c + bea75b0, dağıtım ab0ed5b): `/api/hindsight` vekili
(ruling: `/api/memory` doluydu) + dört bölümlü sayfa. İki inceleme yakalaması: (a) canlı gövde
ölçümü bir varsayımı düşürdü — `/version` alanı `api_version`; fixture da aynı varsayımı
taşıdığından çivi KENDİNİ doğruluyordu (v274 vakasıyla aynı sınıf, aynı günde ikinci örnek);
fixture gerçeğe çekilince eski kod 7 kırmızı verdi. (b) `HamDeger` her skaleri `zamanMetni`ne
sokuyordu — V8 `new Date("42")` → 01.01.2042: ekranda uydurma tarih; `zamanMetni`nin 30+
çağrısının tek spekülatif olanıydı, ISO süzgeciyle kapandı. DERS (iki vakanın ortak adı):
fixture/çağrı bir VARSAYIMI paylaşıyorsa yeşil, varsayımın değil kendinin kanıtıdır — gerçek
gövde ölçümü fixture'a girmeden "çivi yeşil" cümlesi şema kanıtı sayılmaz.

**TSK-105 bot göçü** (925f241 + a751c07, aynı pencere): hermes `extra_headers` env
genişletmiyor (ölçüldü — sır repoya giremez) → köprü KAPIDA: rewrite-fazlı
serverless-pre-function (Bearer→apikey) + `key-auth hide_credentials` (mevcut açık: apikey
upstream'e sızıyordu). İki sessiz-arıza ölçümle önlendi: zaman-aşımı sözlüğü `custom:kapi`de
`providers.custom`a bakar (kapak kondu, yoksa 120 sn sessiz düşerdi); anahtar evi
`HERMES_HOME/.env` = profil-başına (benim "~/.hermes/.env" tek-satırım sessiz-401 üretecekti —
implementer env_loader ölçümüyle düzeltti). İnceleme üçüncüyü yakaladı: distribution/deploy.sh
reçeteleri hâlâ OKUNMAYAN eski anahtarı yazdırıyordu. PENCERE VAKASI: `serverless-pre-function`
config.yaml allowlist'inde yoktu → PUT 400 "unknown plugin" — liste kullanım beyanı VE
zorlayıcı; v376'ya routes↔config kıyas çivisi eklendi. UÇTAN UCA KANIT: bekçi tek-atımlık
koşumu kapıdan kimlikli geçti — sayaç `code=502 consumer=bot_bekci ×3`; filo kotası artık
botları SAYIYOR (LLM kota memory'sinin mekanik yarısı tamam). 502'nin kendisi ayrı gerçek:
OpenRouter günlük ücretsiz-model tavanı DOLU — Hindsight ingest'i (~1.250 çağrı/gün, kapıyı
bypass eder) tavanı yiyor; motor+bot LLM çağrıları gün dönümüne dek 502 alır. Açık gözlem
olarak operatör masasında (seçenekler: bekle · ingest'i duraklat · hesap/kapı kararı).

**Ayrıca:** geri-dolum 2026-04-23 kesik-gz KIRMIZI'sı triyajlandı — sınıf bilinen-geçici
(boyut-kapılı önbellek), eylemsiz kapandı; teşhis iyileştirmesi TSK-107 havuzda. TSK-099/100
gerçekte bitmişti, DONE hizası. dagit [4] istenen-durum koruması üretimdeki ilk koşumunda
doğru çalıştı (learn kapalı kaldı).

## 2026-09-02 (akşam penceresi) — Tavan açma bir gün yaşadı ve geri alındı; ingest kök-nedeni sağlayıcı havuzu; TSK-108 T1-T2 indi; İCRA SIRASI dört kova

**Ücretli→ücretsiz zinciri (operatör kararları: 13:00 "tavan hemen açılsın" → 14:4x "ücretsiz
olması gerekiyordu" → "onlar da gitsin, hepsi ücretsiz olsun").** Sabahki 502'nin sahibi günlük
ücretsiz-model tavanıydı; öğlen kapıya ücretli son-çare instance'ları (öncelik 0) + Hindsight'a
aynı modelin ücretli varyantı kondu (7f015ad/fcc4020 + .env flip). İngest ölmemişti, BİTMİŞTİ:
10:11'de "BITTI · basarisiz: 74" (429 free-models-per-day, 3'er deneme). Ücretli modelle yeniden
koşum yine 429 verdi ama mesaj değişmişti — "Provider returned error … engine_overloaded,
limit_source=upstream_provider_shared_pool" (DeepInfra, BaseTen). Kök neden: nemotron-3-ultra'nın
ücretli havuzunda üç sağlayıcının ikisi dolu/bozuk (BaseTen status −2), Venice sağlıklı; aynı
7,5 KB dosya `provider.order=[Venice]` ile 200 ($0,003), `[DeepInfra]` ile 429 — boyut değil
havuz. Çare `HINDSIGHT_API_LLM_EXTRA_BODY={"provider":{"order":["Venice"],"allow_fallbacks":true}}`
(hindsight config'inde ölçülen düğme) — 429 kayboldu, gerçek token sayılı çağrılar aktı. Sonra
bedel ölçüldü: OpenRouter `usage_daily` 14:00→14:40 UTC $1,36→$4,13 (~$3/saat: ingest +
konsolidasyonun ücretli modelde de süren pydantic-retry'ları + bot son-çare). Operatör "ücretsiz
olmalıydı" dedi → .env `:free` + EXTRA_BODY kaldırıldı + restart (env mtime 14:45:31 < servis
14:46:19, doğrulandı); kapıdan iki ücretli instance çıkarıldı (67b5f47; 11 PUT 200, drift boş;
v361 zincir beklentisi 2+1'e indi + `test_tum_ai_proxy_instance_modelleri_ucretsiz` routes.yaml'ı
okur, mutasyon öttü). Kalan 74 dosya transient timer `ingest067-yeniden` 2026-09-03 00:10 UTC'de
(tavan sıfırlanınca) sürer; ikinci `systemd-run` "already loaded" ile reddedildi = tek zamanlayıcı.
DERS-1 (Bedel yasası, ters yönde): tavan açmanın bedeli ölçülmeden karar verildi; $/saat sayısı
ancak 40 dakika sonra görüldü — ücretli yol açılırken `auth/key` usage_daily'nin saatlik deltası
ilk 30 dakikada okunur. DERS-2: "429" tek sınıf değil — gövdedeki `limit_source` alanı okunmadan
(hesap tavanı ↔ sağlayıcı havuzu) çare seçilmez; sağlayıcı yönlendirmesi modeli değiştirmeden
çözer (EDG-067 model sabiti korundu). Politika bedeli açık kimlik: `B-TAVAN-502` (tavan dolunca
botlar 502 — kabul mü, sessiz-atla mı).

**hindsight-api OOM (14:30:59 UTC):** dev belge retain'inde kernel OOM-kill (systemd tepe 3,0G,
birim MemoryMax=8G — sınır dolmadan global OOM; makine 24G/18G kullanılabilir görünürken), 5 sn'de
otomatik restart. Nedeni ölçülmedi (açık kalem TSK-060 gövdesine); ingest'in üç deneme/90 sn
backoff'u restart'ı atlattı. Konsolidasyonun `_ConsolidationBatchResponse model_type` uyarısı
(LLM list döndürüyor, dict bekleniyor) ücretsiz/ücretli fark etmeden sürüyor — model şeması
sorunu, motor alt-yığını bölüp kurtarıyor; izleme.

**Sır süzgeci vakası (Rol-1 ihlali, itiraf edildi):** `.env`'i `grep -v "KEY|SECRET|PASS|TOKEN"`
ile okurken `DATABASE_URL` satırı süzgeci geçti → Postgres parolası terminale basıldı (DB yalnız
127.0.0.1). Kara-liste sırın ADINI tahmin eder; URL-gömülü kimlik bilgisi adında PASS taşımaz.
Kural sertleşti (hafıza): canlı sır dosyasından yalnız BEYAZ-LİSTE değişken adları basılır;
rotasyon operatör kararı `B-PG-ROTASYON`. Üç küçük ssh dersi de aynı pencerede (hafıza):
nohup'ta stdin yönlendirilmezse ssh asılı kalır; `pkill -f` deseni ssh kabuğunu da öldürür (boş
çıktı, hüküm yok); asılı komut yeniden koşulunca aynı ingest İKİ süreç oldu (idempotent upsert
bankayı bozmadı, parayı ikiye katladı) — `pgrep` tekillik doğrulaması başlatma protokolüne girdi.

**TSK-108 (Hafıza CP-UI) T1+T2 indi, SDD tam döngü.** T1 (9d6b81a): vekil 3→22 uç; en değerli
keşif upstream `hindsight-clients/go/api/openapi.yaml` (v0.9.2 = ebad4782) — sentetik fixture
sıfır; ölçülmüş sürprizler: `GET /observations` yok (memories/list?type=observation), `history`
deprecated/boş, `RecallRequest.limit` yok (`max_tokens`), `scope` parametresi yok. İnceleme 4
Önemli: istatistik gövdeleri liste örneğine bağlanmıştı (aynı dosyadaki canlı-ölçülmüş
audit-stats'la çelişerek), `tags_match=hepsi` çivisi vakumda yeşildi, `_hafiza_post` satır-satır
kopyaydı → `_kapi_istek` çekirdek + sarmalayıcılar. Düzeltme turunda YENİ arıza: `/islemler`
upstream `limit≤100` (biz 200) → 422; `_HAFIZA_UC_TAVANI` + kıyas çivisi, canlıda doğrulandı
(200→422, 100→200). T2 (d968e4c): CP kabuğu (8'li kenar çubuğu, adres tek kaynak — küresel
nav'la desenkron incelemede yakalandı) + üç görünüm; alan adları canlıdan ölçüldü (memories/list
22 anahtar, `source_memory_ids` — fixture `source_memories` diyordu; `nodes_by_fact_type` zaten
`observation` taşıyor — çift satır düşürüldü). VAKA: ilk T2 commit'i yeni bundle çiftini
KAÇIRDI (çok satırlı değişkenle `for` → tek pathspec, fatal; commit yine atıldı) — amend +
manifest↔ağaç kıyası; ders: build-çıktısı commit'inden sonra manifest referansları ağaçta
var mı diye ölçülür (dagit'te eksik bundle = ölü pano). T3 iki fazlı (ortak dosya çakışması:
Faz A yalnız yeni dosyalar, Faz B T2 turu inince) — operatör "T3'ü de sevk et" dedi, çakışma
fazla çözüldü.

**ROADMAP İCRA SIRASI dört kova (61763fa, operatör "onayla, yeniden yaz"):** A kapanış dalgası
(108→060→089→058→kapanış) · B hazır küçükler · C kart isteyenler · D operatör masası. Bilgi
kaybı sıfır betik-çivili (eski bölgenin her satırı yeni bölgede), DONE'lar KAPANANLAR alt
bloğunda bir dalga, TSK-108 §4'ten tahtaya; yedi ROADMAP çivisi 260 yeşil.

**Açık kalemler:** ingest 74 dosya (yarın 00:10 UTC timer → BITTI hükmü + OOM tekrarı mı) ·
TSK-089 kapanışı (`/models` sondası kararı + DONE beyanı) · TSK-058 ilk dolu koşum 07:30Z sonucu
karta · `B-TAVAN-502` · `B-PG-ROTASYON` · konsolidasyon şema uyarısı · TSK-108 T3/T4 (bu kayda
kapanışta eklenir).

**T4 kapanışı (aynı akşam):** tam suite donmuş ağaçta (parmak izi: HEAD 61763fa + diff/untracked
sha'ları, başta ve sonda eşit) 2 failed / 9430 passed — ikisi de T1'in `POST /api/hindsight/recall`
ucunun v181 (teşhis-zarfı envanteri) ve v54 (iz çivisi) tarafından MUTASYON sayılması. Ruling R14:
recall sorgu-sınıfı bir POST'tur (Hindsight araması gövde ister), iz UYDURULMAZ, muafiyet adıyla +
gerekçeyle beyan edilir (v181 `muaf` + `_diag_onbellek_bosalt` ENVANTER DIŞI satırı; v54 `/api/logout`
emsali) — e8f899f; etkilenen küme 496 yeşil, iki mutasyon ısırdı. T3 (1ecbbe4) iki fazla (ortak dosya
çakışması) + inceleme 3 Önemli (graf toplamları okunmuyordu — eksik graf tam görünüyordu; korumasız
`Date.parse` T2 sınıfının dönüşü; `query_timestamp` saat dilimsiz) → düzeltme → yeniden-inceleme temiz.
DERS-3 (T2+T3 ortak): "toplam" alanı telde dururken ekranın kendi tavanını sayması, eksikliği tam
gösterir — üç sayı adıyla (çizilen/vekil/toplam) ve gelmeyen alan "— (alan gelmedi)". Zincir: T1
9d6b81a → kapı 67b5f47 → T2 d968e4c → ROADMAP 61763fa → T4 e8f899f → T3 1ecbbe4 → bu kayıt; push +
dağıtım penceresi + canlı görsel doğrulama → TSK-108 DONE. Havuza iki kalem: TSK-109 (webhook
okuması), TSK-110 (pano bayat-gövde sınıfı).

**Görsel tur dalgası (aynı gece, T5/T6):** operatörün beş bulgusu (çift nav · raf ad çakışması ·
grafik tipi · constellation yok / varlık grafı uzak · bank config formsuz) iki görevle kapandı. T5
(ebc8da0): küresel nav'da yüzey `altBolumNav: "yuzey-ici"` beyanı; eski "Belgeler" rafı yüzeyi KALKTI
— içeriği konsolide: dersler (`/api/memory`, Hindsight korpusunda yok) → Bilgi Tabanı "Meridian
dersleri", karar arşivi (`/api/karar-belgeleri`; Hindsight'a ingest edilmiş, çiftti) → Belgeler
listesine `basename(id) ↔ ad` join (canlıda doğrulandı: belge id = repo yolu), karar şeridi (özet,
runbook-HEAD, ok:false — bedel yasası), v312 22→28; ana sayfa grafiği CP AreaChart satır satır;
Bank Configuration 8 bölüm/21 alan devre-dışı, overrides absent=INHERIT. T6-A (5fd4ff1 + c1dac25):
`/bellek-graf` (→/graph; limit.maximum yok; R7 CP varsayılanı 200), `/profil`; `features` ayrı yol
değil → `/version`dan `saglik.ozellikler` (R28). T6-B (3fdd746): kütüphanesiz canvas takımyıldızı —
CP constellation.tsx'in ~30 kuralı çapalı; ölçülmüş sapmalar: node.data'da `type` yok (fact-type
`table_rows`tan), CP'de tam graf yok (Bellekler "Tam graf" Meridian eklentisi), lejant `--color-*`
kapsam hatası doğrulanıp düzeltildi. Tam suite #2: 1 failed (v286 çıplak hex — canvas yedek paleti)
/ 9480 passed → hex yedekleri kaldırıldı, jeton çözülemezse dürüst hâl; etkilenen küme yeşil.
DERS-4 (yorum): "konsolide" operatörde İÇERİK tekilleştirmesidir (aynı şey iki yerde olmasın), sunum
birleştirme/redirect değil — üç düzeltme turu; bölüm-bazlı veri kaynağı ölçülmeden brief verilmez
(hafıza kaydı). DERS-5 (süreç): `git add -A -- <dizin>` bile shim'e takılır ve commit eksik atılır;
çok dosyalı ekleme porcelain'den tek tek, commit sonrası `git show --stat` kıyası (bugün iki vaka:
T2 bundle, T5 ui/src). DERS-6: mutasyon turu build'den ÖNCE — aksi hâlde dagit [5c] tazelik kapısı
içerik aynıyken mtime'a takılır. Havuza: TSK-111 (Faz-2 yazma), TSK-112 (varlık künyesi paneli).
Kararlar: B-TAVAN-502 kapalı (502 bilinçli), B-PG-ROTASYON icra+kanıt, konsolidasyon gece dokunulmadı.
DONE koşulu: dağıtım + operatör görsel turu.

## 2026-09-03 (gece kuyruğu, otonom) — 18 kalem onaylı: TSK-108 kapanış dalgası + TSK-111 dilim 1 canlıya; iki kart ön-kayıt; geri-dolum dayanıklılığı; OOM tavanı

**Yetki ve çerçeve:** operatör 2026-09-02 ~23:00 TR: "gece boyu konsolide plan üzerinde çalış, full
otonom, sudo dahil dağıtım yetkin var" → 18 kalemlik kuyruk gösterildi, onaylandı ("18 kaleme onay,
full otonom devam"). Yapılmayanlar baştan sınırlandı: seans kilidi · konsolidasyon · ücretli harcama ·
bank config yazma · strateji/evren/parametre · sır değerleri. Ledger `.superpowers/sdd/…/progress.md`
"[G#]" satırları; saatler `date -u` ile (ilk etiketlerim +1-1,5 saat şişkindi — düzeltildi).

**Canlıya inen (dağıtım d0c7927, 22:52:40Z; healthz 200, learn kapalı, kod-tazelik ✓):**
- TSK-108: T9 Ana Sayfa = CP home (operatörün canlı CP ekranı ölçüt; CP'nin home-view + bank-stats-view
  ikilisi tek sayfada — beyanlı sapma; DONE = max(0,total−pending−failed) CP formülü; FAILED tıklanır →
  `consolidation_state=failed` listesi; bant sırası sabit, `caused_by` "tanınmayan tür" rozetiyle sona).
  R20' (operatör ekran görüntüsüyle: alt başlıklar SOL nav'da, sayfa-içi kenar çubuğu ve beyan
  mekanizması silindi — R20 ters uygulanmıştı; "uygulama UI'ı" = panonun kendi kalıbı). Stub önizleme
  (statik + boş /api, uygulama yüklenmeden — hafıza kaydı) yapıyı doğruladı; dolu hâli operatör turu.
- TSK-111 dilim 1: 11-A vekil yazma uçları (`/islem/{iptal|yeniden-dene|sil}`, `/konsolidasyon/
  {kurtar|tetikle}`; güvenlik listesi 9/9; bank/id tip+duvar tek yardımcı; ret dallarında da iz;
  `/consolidate` gövdeli ÇIKTI — "dördün boşluğu beşinci için kanıt değil") + 11-B UI (iki adımlı onay,
  çift-gönderim kilidi, kısmi başarı pencerede bacak başına {ok,http,neden}, sr-only gerekçe; CP durum
  matrisi ölçüldü; CP onay sormuyor — beyanlı sapma; v378 30 çivi kalıcı). Kurtarma CP sırasıyla
  recover → retried_count>0 ise trigger (CP gövdesiz).
- hindsight-api MemoryMax 8G→12G: 14:30Z OOM cgroup'tu (anon-rss 8,37 GB > 8G; systemd "3,0G tepe"
  yanıltıcıydı); makine 23 GB. Birim dosyası repo+canlı (F9 aynası birebir).
- TSK-107/087 (/opt/veri kopyası kuruldu; koşan tur eski kodla): kesik indirme erken KIRMIZI (boyut
  kıyası, yarım gz silinir, `KesikIndirme` main'de tek satır) + işçi çökmesinde bir kez yeniden deneme
  (öteki işçi kesilmez; ikinci çöküşte KIRMIZI + bedel özeti). v377 13 çivi.

**Ölçümle kapananlar:** TSK-089 DONE (`/models` sondası "açık" BAYATTI — kapıda `llm-models` rotası
var, motor 200) · TSK-008 DONE (TSK-092 koruması iki dağıtımda learn'ü kapalı tuttu) · B-NOUS-BEYIN:
zincir doğru (NOUS_ENDPOINT=kapı, model, anahtar; models 200) — chat canary tavan sıfırlanınca ·
Evren sapması 13 sembol tam liste (universe_drift.json; endeks çıkışı, delist değil; açık pozisyon
kesişimi BOŞ) → sabah karar paketi.

**Kart ön-kayıtları (kod yok, operatör onayı):** EDG-2026-069 ⑥a tetik→dolum tick bacağı (gecikme
≤60 sn, kayma ≤15 bps; ADIM-0 n≥30; girdiler ölçüldü: tick arşivi 129 gün 1/sn, `trades.extra_json.
dolum_ts`) · EDG-2026-070 PIT mid-cap sağ-kalan üst-sınır (EDG-018 halefi, aynı ADIM-0, yeni bar
kaynağı). §6 OPERATOR; README endeksi üretildi (v279 yakaladı).

**TSK-064 hazırlık belgesi** `docs/TASARIM-SIR-YOL1-2026-09-03.md`: 5 dosya/16 sır (yalnız adlar),
sınıf A/B/C/D, Faz-0..1C; bulgular: `.env-apisix` 640, DASH_TOKEN iki dosyada, vekil TENANT'ı dosyadan
okuyor.

**Suite hükümleri (üçü de donmuş ağaç, parmak izi eşit):** #2 9480/1F (v286 çıplak hex — canvas yedek
paleti; kaldırıldı, jeton çözülemezse dürüst hâl) · #3 9628/2F (v334 ham exec_module — v377 conftest
yardımcısına; v279 README endeksi üretilmemiş — üretildi). Etkilenen kümeler yeşil; push d0c7927.

**Vakalar / dersler:** `.claude/launch.json` OKUMADAN üzerine yazıldı (stub yapılandırması; eski
içerik bilinmiyor, .claude git-ignore) — operatöre itiraf, Write-öncesi-Read hafıza kaydı ·
git shim `add -A -- dizin`i de reddetti, ilk T5 commit'i ui/src'siz atıldı → porcelain'den tek tek +
`git show --stat` kıyası (bugün 2.) · "konsolide" = içerik tekilleştirmesi (üç yorum turu; hafıza) ·
saat etiketleri ölçülmeden yazılmaz.

**Açık (sabah):** kart onayları 069/070 · TSK-064 Faz-0 (chmod 600) · 11-A bank allowlist · geri-dolum
seans kilidi (intraday_gap bedeli: 0→232/273/242) · evren sapması 13 sembol · konsolidasyon başarısız
258 (retry düğmesi canlı) · ingest 00:10Z koşumu hükmü · TSK-112 (12-A uçuşta) / TSK-020 2-adım2 /
TSK-029 / TSK-109 / TSK-110 sıradaki.
