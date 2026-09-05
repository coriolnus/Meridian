# MERIDIAN YOL HARİTASI — tek kaynak

Koda gömülü faz planlarını, oturum kararlarını ve operatör tercihlerini TEK dosyada toplar; yeni
faz/iş kalemi buraya işlenir, "konuşmada kaldı" diye kaybolmaz. **Düzen (2026-08-09 yeniden
örgütleme — §0-6 mimarisi, operatör onaylı):** işler birbirine girmez, her bilginin TEK doğru yeri
vardır. §0 sözleşme + yasalar + kuzey yıldızı · §3 aktif WP'ler (açık cepheler) · §4 öneri havuzu
(backlog) · §5 operatör blokları · §6 kanıt/kartlar · §7 karar günlüğü (kronolojik, yeni giriş EN
ÜSTE) · §8 arşiv (tamamlanan WP'ler + oturum snapshot'ları). _(Bu tur öncesi düzen §3-7 idi; taşıma
haritası §7'in tepesindeki 2026-08-09 kaydında.)_

---

## §∞ EŞLEME TABLOSU — eski § numaraları (2026-08-17 yeniden numaralandırma)

_**[2026-08-31 DURUM DENETİMİ — BU BÖLÜM KALEM TAŞIMAZ.]** Burası eski→yeni § numaralarının eşleme tablosudur: bir ADRES defteri, iş listesi değil. Bu yüzden maddeleri durum işareti taşımaz ve `/api/roadmap` onları `belirsiz` sayar — **bu doğrudur**: "işaretsiz" burada "denetlenmemiş" değil, "durumu olan bir kalem değil" demektir. Denetim 9 tablo satırını kalemi bu gerekçeyle rozetsiz bıraktı; kaynak: `docs/DENETIM-ROADMAP-2026-08-30.md`._

> **NEDEN TAŞINDI:** belge artık **geliştirme yaşam döngüsünü** (superpowers H0→H6) izliyor; okuma
> sırası `yasa → hat → tahta → cepheler → fikir → blok → kanıt → karar → arşiv`. Operatör kararı
> 2026-08-17: *"bundan sonra superpowers roadmapten bağımsız olarak bütün geliştirme cycle'inin
> belkemiği olacak."* Emsal: 2026-08-13'te `WP-E → WP1` yeniden adlandırması da her başlıkta
> "(eski: …)" eşlemesini taşıyarak yapılmıştı.

| eski | yeni | bölüm |
|---|---|---|
| §0 | **§0** | SÖZLEŞME — anayasa (numarası bilerek SABİT) |
| — | **§1** | HAT — yaşam döngüsü ve kapıları (H0…H6) |
| — | **§2** | TAHTA — aktif kalemler, tek satır tek aşama |
| §1 | **§3** | AKTİF WP'ler (cepheler) |
| §2 | **§4** | ÖNERİ HAVUZU |
| §3 | **§5** | OPERATÖR BLOKLARI |
| §4 | **§6** | KANIT/KARTLAR |
| §5 | **§7** | KARAR GÜNLÜĞÜ |
| §6 | **§8** | ARŞİV |

**KALEM KİMLİĞİ KONUMDAN AYRILDI.** Havuz kalemleri artık `Ö-N` (eski `§2-N`) — 151 atıf çevrildi.
Gerekçe deponun kendi yasasıyla aynı: `§2-48` bir **konum adıdır** (satır çapası sınıfı) ve bölüm
kımıldayınca sessizce çürür; `Ö-48` bir **kimliktir** ve kımıldamaz. Kartlar bunu zaten doğru
yapıyordu (`EDG-2026-041` hiç taşınmadı). Operatör blokları (`§5` içindeki A1/A2/B1…) henüz
kimliklendirilmedi — **açık kalem**.

**DIŞ ATIFLAR — BİLİNÇLİ OLARAK DÜZELTİLMEDİ, YAZILI BIRAKILDI:**
`docs/` altındaki **553** ve `research/cards/` altındaki **29** atıf ESKİ numaralarıyla duruyor.
`docs/` tarihli kayıttır ve düzeltmek tarihi tahrif etmek olurdu; kartlar **dondurulmuş
ön-kayıtlardır** ve kart disiplini dokunmayı yasaklar. Bu tablo onları karşılar. `meridian/` (72)
ve `tests/` (140) canlı artefakt oldukları için ayrı bir adımda çevrilir — _açık kalem_.

**KAYIPSIZLIK KANITI (2026-08-17):** dönüşüm betikle yapıldı; §-atıfları maskelenince eski ve yeni
metin **birebir aynı** (`sha256[:16] = e842246dcb29e7ad`, 3658 → 3658 satır). Kanıtın kendisi de
kasıtlı-kırmızıyla sınandı: tek satır düşürünce de tek kelime değiştirince de DÜŞÜYOR.

### İKİNCİ DALGA (2026-09-01 — TSK/PRG madde standardizasyonu, `docs/TASARIM-ROADMAP-STANDART-2026-09-01.md`)

_Operatör kararı 2026-09-01 gece: tüm kalemler `TSK-###`/`PRG-##` şemasına göçer (§7/§8 muaf).
Kaynak: FAZ A raporu (`scratchpad/tsk001-fazA-rapor.md`) + bu dosyanın kendisi (FAZ A/B'nin
yazdığı `[TSK-NNN]` başlıkları ve tablo satırları) — hiçbir "eski" değer uydurulmadı; iz
bulunamayan yerde bunu açıkça yazdım (uydurma yasağı)._

**A. Cepheler (WP1-11 → PRG-01-11) — FAZ B, §3 başlıkları:**

| eski | yeni | not |
|---|---|---|
| WP1 (WP-E İcra Gerçekliği + Ö-23 + Ö-13) | **PRG-01** İcra ve Friksiyon | |
| WP2 (WP-S + Ö-27 + Ö-7 + Ö-9/Ö-18) | **PRG-02** Sermaye ve Koruma | cephe KAPALI (2026-08-22) |
| WP3 (WP-L + Ö-28 + Ö-10 + Ö-19) | **PRG-03** Öğrenme Döngüsü | |
| WP4 (WP-U Evren/PIT + WP-D Veri Bütünlüğü + Ö-8) | **PRG-04** Veri ve Evren | |
| WP5 (WP-M + WP-S2 + Ö-4 + Ö-14 + Ö-20 + Ö-16) | **PRG-05** Ölçüm Altyapısı | |
| WP6 (WP-H + Ö-25 + Ö-26 + Ö-2) | **PRG-06** Sistem Bütünlüğü | |
| WP7 (Ö-24 — 2026-08-13 yeni cephe) | **PRG-07** Skill Katmanı | |
| WP8 (WP-UX + WP-P + Ö-3) | **PRG-08** Pano ve Operatör | |
| WP9 (WP-QC) | **PRG-09** QuantConnect | |
| WP10 (eski-numaralandırmada WP2 — EDGAR) | **PRG-10** Referans Verisi | cephe KAPALI (açık borç yok) |
| WP11 (Ö-15 + Ö-29 + Ö-12) | **PRG-11** Strateji ve Seçilim | |

_WP12 (Bot Roster) BİLEREK PRG'YE ÇEVRİLMEDİ: 2026-08-31'de doğan bu cephenin `### WP12 —`
biçiminde bir §3 detay-başlığı hiç yok (yalnız özet tablosunda ve §2 TAHTA'da satırı var) — spec'in
literal kapsamı "eski WP1..WP11" zaten WP12'yi dışarıda bırakıyor; bu bir atlama değil, doğrulanmış
sınır (FAZ B, GERÇEKLİK KONTROLÜ)._

**B. FAZ A doğumlu maddeler (TSK-002…051, §4 HAVUZ + §5 OPERATÖR BLOKLARI) — kaynak: FAZ A raporu +
ROADMAP.md'nin kendi `eski:` satırları:**

| eski | yeni | not |
|---|---|---|
| — (göçten önce zaten TSK-002 idi, FAZ A dokunmadı) | **TSK-002** rejim-ship backtest_full | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-003** yansıma mükerrerlik kapısı | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-004** "gece ne buldu" hunisi üç kusur | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-005** `/api/infra` keşfi tek yönlü | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-006** `session_refresh` tekelleşmesi | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-007** `watchdog_incidents` mekanizma adı | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-008** dagit bakım penceresi `meridian-learn` | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-009** elle-kurulum penceresi (5 dosya + bucket-kopya) | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-010** filo-yönetim MCP sunucusu | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-011** cf tarama kuyruğu `reset_index` | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-012** pano 'Ajan' bölümü | dalga-A DONE, dalga-B GATED — TSK-012 gövdesi ikisini tek durumda anıyor (bkz. FAZ B bulgusu, rapor) |
| adsız havuz satırı (eski: kayıtsız) | **TSK-013** tick programı ücretsiz kaynak | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-014** teslim-öncesi ikinci-görüş geçişi | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-015** ajan kalıcı hafızası | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-016** hermes skill öz-iyileştirme | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-017** 6 skill reposu değerlendirmesi | DONE |
| adsız havuz satırı (eski: kayıtsız) | **TSK-018** bot filosu zamanlı→olay-tetikli | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-019** seyrelme mekanizması ölçülemiyor | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-020** backend mimari kararları (9 kalem) | |
| adsız havuz satırı (eski: kayıtsız) | **TSK-021** `earnings_8k_tarihleri.csv` okunmuyor | |
| — (born 2026-08-16, iz kayıtsız) | **TSK-022** öğrenme döngüsü API GIL | DONE |
| eski: Ö-49 | **TSK-023** çapa/beyan çürümesi | DONE → WP6-E'ye taşındı |
| — (born tahmini 2026-08-14) | **TSK-024** keşif üreticisi ölü düğmeler | DONE |
| — (born tahmini, iz kayıtsız) | **TSK-025** 28d teşhisi | DONE |
| — (born tahmini 2026-08-14) | **TSK-026** 28f teyit deliği | DONE |
| — (born tahmini 2026-08-14) | **TSK-027** 28i sapma | DONE |
| eski: Ö-44 | **TSK-028** renk rol-sızıntısı ikinci evi | DONE → WP8-D'ye taşındı |
| eski: Ö-41 · §4-41 | **TSK-029** mutasyon kapsamı 39/79 | |
| eski: Ö-42 · §4-42 | **TSK-030** çapa deseni ölçümü | |
| eski: Ö-43 · §4-43 | **TSK-031** yanlışlanan iddia (sermaye.py) | DONE |
| eski: §4-39 | **TSK-032** kalibrasyon "hangi beyin isabetli" | DONE |
| eski: Ö-40 | **TSK-033** `nous_eval` künye alanları | DONE → WP7'ye taşındı |
| eski: §4-36 · Ö-36 | **TSK-034** Faz-6 kilidi → §5'e taşındı | DONE |
| eski: Ö-37 · §4-37 | **TSK-035** `seed_boundary` iki yolu | |
| eski: Ö-38 | **TSK-036** iki modül yorumu | DONE → WP6-E'ye taşındı |
| eski: Ö-35 | **TSK-037** 15g turu iki kalem | DONE → WP5-G + WP11-G'ye bölündü |
| eski: Ö-34 | **TSK-038** kayan oturum sürüklenmesi | DONE → WP6-E'ye taşındı |
| eski: Ö-31 | **TSK-039** `active_model()` künye kusuru | DONE → WP7'ye taşındı |
| eski: Ö-32 | **TSK-040** suite içi ağ çağrısı | DONE → WP5-G'ye taşındı |
| eski: Ö-33 · §4-33 | **TSK-041** kardeş ajan pytest çakışması | DONE |
| eski: Ö-30 · §4-30 | **TSK-042** ayrılmaz çift yedek davranışı | DONE |
| eski: §4-36 · Ö-36 (TSK-034 ile aynı kök) | **TSK-043** Faz-6 kilidi — kadanslı yazar yan etkisi | GATED |
| adsız operatör bloğu (eski: kayıtsız) | **TSK-044** FINVIZ Elite token (C1) | OPERATOR |
| adsız operatör bloğu (eski: kayıtsız) | **TSK-045** FMP plan/kota (C2) | OPERATOR |
| adsız operatör bloğu (eski: kayıtsız) | **TSK-046** QC login+notebook (C3) | OPERATOR |
| adsız operatör bloğu (eski: kayıtsız) | **TSK-047** NOUS_MODEL/beyin çeşitliliği (C4) | OPERATOR |
| — (born 2026-08-09) | **TSK-048** systemd `SuccessExitStatus=143` | DONE |
| kimlik tablosu B-DASH-CRED | **TSK-049** DASH-TOKEN LoadCredential faz-1 | DONE (2026-09-01 canlı ölçüm — Rol-1 düzeltmesi, FAZ A GATED bırakmıştı) |
| CLAUDE.md §2 git satırı vakası (2026-08-26) | **TSK-050** ajan-git mekanik kapısı | |
| kimlik tablosu B-QC-LOGIN | **TSK-051** QC LEAN CLI `lean login` (C2-4) | OPERATOR |

**C. FAZ B doğumlu maddeler (TSK-052…085, §0 İCRA SIRASI + §2 TAHTA) — kaynak: bu dalganın kendi
İCRA SIRASI listesi + TAHTA H1/H0/DİK DURUM tabloları:**

| eski | yeni | not (göç anı durumu — TARİHÎ 2026-08-31, GÜNCELLENMEZ; güncel durum maddenin kendi `status:` satırındadır) |
|---|---|---|
| İCRA SIRASI adsız ①-madde | **TSK-052** A·PIT/veri (EDG-062) | ACTIVE |
| İCRA SIRASI adsız madde | **TSK-053** Akıbet Defteri | DONE |
| İCRA SIRASI adsız madde | **TSK-054** Ajan Yüzeyi Mesajlaşma Göçü | DONE |
| İCRA SIRASI adsız madde | **TSK-055** Akıbet Kararları — ilk karar turu | DONE |
| İCRA SIRASI adsız madde | **TSK-056** Tick Hüküm + Geri-Dolum (EDG-066) | DONE |
| İCRA SIRASI adsız madde | **TSK-057** Akıbet-Dalgası | DONE |
| İCRA SIRASI adsız madde | **TSK-058** Skill-görüş dalgası (EDG-019+063) | QUEUED |
| İCRA SIRASI adsız madde | **TSK-059** B·P-2/`ts` kart uygulaması | GATED |
| İCRA SIRASI adsız madde | **TSK-060** Hindsight bot-hafızası kurulumu | QUEUED |
| TAHTA H1 satırı (WP: WP12) | **TSK-061** Hermes bot roster — Faz 5+ rol seçimi | GATED |
| İCRA SIRASI adsız madde | **TSK-062**/TAHTA H1 satırı (WP: WP3) öğrenme kilidi çifti | GATED — aynı kalem iki yerde (İCRA SIRASI + TAHTA), tek numara |
| İCRA SIRASI adsız madde | **TSK-063** Faz-6 kilit-zinciri KANIT + BEŞ KİLİT | GATED |
| İCRA SIRASI adsız madde | **TSK-064** Sır-yönetimi kademeli YOL-1 | QUEUED |
| İCRA SIRASI ⑤-madde | **TSK-065**/TAHTA DİK DURUM satırı (WP: WP4) PIT mid-cap üst-sınır | GATED |
| İCRA SIRASI ⑥a-madde | **TSK-066** AN yeniden-kurulumu | QUEUED |
| İCRA SIRASI ⑥b-madde | **TSK-067** İLK yeni-sinyal kartı | QUEUED |
| İCRA SIRASI ⑥c-madde | **TSK-068** spread dinamiği + icra zamanlaması | QUEUED |
| TAHTA H1 satırı (WP: WP1) | **TSK-069** EDG-2026-042 K1/K3 bandı — Ö-55 | GATED |
| TAHTA H0 satırı (WP: WP3) | **TSK-074** `propose_virgin_knob` süzgeci | QUEUED |
| TAHTA H0 satırı (WP: WP1) | **TSK-075** `13` scale-out latent kusuru | QUEUED |
| TAHTA H0 satırı (WP: WP3) | **TSK-076** OPT Faz-1/Faz-2 | GATED |
| TAHTA H0 satırı (WP: WP5) | **TSK-077** WP5 metodoloji/eşik kalıntıları (M2+M11) | QUEUED |
| TAHTA H0 satırı (WP: WP6) | **TSK-078** `26` değer-eşitliği kalan 9 çift | QUEUED |
| TAHTA H0 satırı (WP: WP6) | **TSK-079** `25a`/`25c`/`25d` | OPERATOR |
| TAHTA H0 satırı (WP: WP6) | **TSK-080** `Ö-49` çapa/beyan çürümesi kalanı | QUEUED |
| TAHTA H0 satırı (WP: WP11) | **TSK-081** ARSENAL + `15d` + `15c` | QUEUED |
| TAHTA H0 satırı (WP: WP5) | **TSK-082** §6 kart indeksi elle tutuluyor | QUEUED |
| TAHTA H0 satırı (WP: WP6) | **TSK-083** ROADMAP satır çapaları | QUEUED |
| TAHTA DİK DURUM satırı (WP: WP4) | **TSK-084** delist-bar kaynağı + FINVIZ bloğu | OPERATOR |
| TAHTA DİK DURUM satırı (WP: WP1) | **TSK-085** `23b` çıkış slipajı | QUEUED |

_Not: TSK-061, 062, 063, 065, 069'a İCRA SIRASI içinde `(bkz. TSK-0NN — ...)` biçiminde geri-bağlantı
verildi — bu beş kalemin tam gövdesi TAHTA'da yaşar, İCRA SIRASI onu TEKRARLAMAZ (tek-kaynak
yasası). TSK-070…073 TAHTA H0'da tanımlıdır ama İCRA SIRASI'nda hiç anılmadı (İCRA SIRASI'nın
zaten kapsamadığı ayrı kalemler) — eşleme "eski" sütununda yalnız TAHTA H0 gösterilir, satırları
yukarıdaki B/C tablolarına tam giren TSK-070/071/072/073 unutulmadı, ayrı satırda listelenmedi
çünkü İCRA SIRASI'nda karşılıkları yok; TAHTA bölümünde zaten mevcutlar (bkz. ROADMAP.md §2 TAHTA
H0)._

**Kapsam dışı bırakılanlar (FAZ B, gerekçeli):** `WP\d` atıf süpürmesi yalnız §∞/§0/§2 içinde
uygulanabildi (2 atıf: "WP1 SIRASI"→"PRG-01 SIRASI", TSK-001 gövdesindeki "WP1'in A bacağı");
§6 KANIT/KARTLAR içindeki `WPn`/`WPn-X` atıfları (ör. `→ WP5-E/20b`, `WP2-D`, `WP11-C`, `WP5-C`,
`WP3-A/28a`) **BİLEREK dokunulmadı** — bunlar dondurulmuş kart-hüküm ("damga") paragraflarının
içinde geçiyor, §6'nın kendisi bu FAZ'ın dört bölgesinden biri değil (spec §3 "§6 kart ENDEKS
satırları" diyor, kart gövdesi değil) ve dondurulmuş hükme dokunmak tarihçe-koru ilkesini çiğnerdi;
FAZ C/Rol-1'e devredildi. §3 cephe gövdeleri içindeki ince-taneli alt-kalemler (23a-23f, 24a-h,
25a-e, 28a-i, M1-M11, 2B-2D…) TSK şemasına ÇEVRİLMEDİ — 2026-08-31 DURUM DENETİMİ
(`docs/DENETIM-ROADMAP-2026-08-30.md`) bu 70 kalemi zaten KAPALI/AÇIK/ASKIDA/DOĞRULANMADI/KAYIT
rozetleriyle tek tek sınıflandırmış durumda ve §3'ün kendi yazılı kuralı (2026-08-17 şerhi) durum
yetkisinin TAHTA'da olduğunu, bu gövdenin yalnız GEREKÇE taşıdığını söylüyor — bunlara ikinci bir
paralel TSK-durumu eklemek tek-kaynak yasasını ihlal eden yeni bir ayrışma kaynağı açardı (aynı
riski ROADMAP kendi 464-468. satırlarında zaten bir kez yaşamış ve yazılı uyarmış). Bu, FAZ B'nin
uydurma-yasağı gerekçeli bir kapsam kararıdır — Rol-1 incelemesi bekler (bkz. rapor).

## §0 SÖZLEŞME — nasıl okunur, yasalar, kuzey yıldızı

_**[2026-08-31 DURUM DENETİMİ — BU BÖLÜM KALEM TAŞIMAZ.]** Burası anayasadır — yasalar, kuzey yıldızı ve okuma kuralları. Bu yüzden maddeleri durum işareti taşımaz ve `/api/roadmap` onları `belirsiz` sayar — **bu doğrudur**: "işaretsiz" burada "denetlenmemiş" değil, "durumu olan bir kalem değil" demektir. Denetim 13 maddeyi kalemi bu gerekçeyle rozetsiz bıraktı; kaynak: `docs/DENETIM-ROADMAP-2026-08-30.md`._

**NASIL OKUNUR — her iş türü nereye yazılır (TEK doğru yer):**
- Yeni fikir / iyileştirme önerisi → **§4 ÖNERİ HAVUZU** (biçim: gerekçe · tahmini boyut · bağımlılık · öncelik).
- Olgunlaşan / başlanan açık cephe → **§3 AKTİF WP** (biçim: durum · kapsam · açık kalemler · dosya-sınırı · kanıt-kartı bağı) + Task açılır.
- Operatör kararı / kimliği / parası / bakım penceresi bekleyen → **§5 OPERATÖR BLOKLARI**.
- Ölçüm ön-kaydı / hüküm → **§6 KANIT/KARTLAR** (`research/cards/` indeksi; kartsız ölçüm kodu yok).
- Neden-kaydı (kronolojik, tarihli) → **§7 KARAR GÜNLÜĞÜ** (yeni giriş EN ÜSTE).
- Tamamlanan WP / bayat status snapshot → **§8 ARŞİV** (tarihçe-koru; silme yok).
- Bir bilginin nereye gideceği belirsizse **§7'e not düşülür, SİLİNMEZ**.

**YAŞAM DÖNGÜSÜ:** öneri (§4) → olgunlaşınca §3'e taşınır + Task açılır → bitince §8'ya arşivlenir;
kartı §6'te, kararı §7'te, operatör kalemi §5'te kalır. §3'deki her WP'nin NET SINIRı vardır
(dosya-ayrıklık sözleşmesi); açık kalanı §3'de, tarihçesi §8'da.

**DURUM İŞARETLERİ (§3/§6/§8 boyunca):** ✅ kapalı · 🔄 koşuyor · 🕐 kuyruk · 🔒 bağımlı/bilet ·
📋 sırada · 🔴 aktif/öncelik · 🔶 aktif araştırma · 🆕 yeni · 🔓 kilit açık.


### KUZEY YILDIZI (EDGE VERDICT + SONUÇ HÜKMÜ + yönetici ilke + operatör tercihleri)

**Kuzey yıldızı:** EDGE VERDICT — BEŞ ölçüt (gerçek-katman IC + SPY-üstü + tahmin isabeti + rejim
edge + **KUYRUK**, 5. ölçüt 2026-07-30'da indi). Canlı hüküm: **"1/5 sağlandı (1 zayıf, 2
sağlanmadı, 1 ölçülemedi) — edge kanıtlanmadı."** İKİZİ: **SONUÇ HÜKMÜ** (dolar merceği,
`analytics.result_verdict`) — canlı: **"0/4 sağlandı — para kanıtlanmadı."**
Yönetici ilke: **edge kanıtlanmadan rafineriye (emir bacağı, otonomi, sermaye) yatırım yok** —
rafineri kararları EDGE'e, **sermaye/silahlanma İKİ hükme birden** bakar (R birimi geniş stopa
yapısal önyargılı; dolar merceği olmadan sermaye kararı verilemez).
Operatör tercihleri (2026-07-27 röportajı): eksenler sıralı değil ÖRGÜLÜ; pano ana yüzey; kanıt
gövdesi replay+cf yoğunluğu, gerçek/sim etiketi her yerde açık; kalibrasyon yetkileri eşik dolunca
otomatik açılır; tempo çağrı-üzerine + kritik anlar.

### YASALAR VE KESİŞEN KURALLAR (anayasal — tüm işleri bağlar)

- **NOUS SİSTEM-DEĞERLENDİRME KATMANI (kalıcı anayasal kayıt — WP-konsolidasyonunda düşmüştü,
  F4 sürüklenme testi yakaladı, geri kondu):** Katman A-D haftalık öz-değerlendirme; **Katman D
  anayasal çekirdek KAPALIDIR** — hakim kendi yasasına dokunamaz (CORE_FILES/CORE_CONCEPTS,
  CekirdekIhlali + AUTHORITY_CHANGE alarmı, AST çivisi; nous_eval docstring'i ile aynı söz).

- **Ölçüm-önce:** hiçbir değişiklik ölçümsüz canlıya girmez; kapı (reflect._gate_eval) TEK hakem;
  knob hipotezleri tek-değişken (guard), mimari reform beyanlı bileşik ölçümle (k_probes = denenen).
- **YASA 4** sessiz yutma yasak (kaçış: `# sessiz-yutma: <neden>`) · **YASA 6** üretilen her alanın
  dış tüketicisi olmalı (okuma api.py üzerinden pano) · **UYDURMA YASAĞI** ölçülemeyen None kalır;
  alan adları canlı dosyadan doğrulanır; retro damga yok.
- **Canlı güvenlik:** state/'i yalnız worker yazar; ölçümler sandbox kopyada (config.STATE
  yönlendirme + mtime parmak izi kanıtı); restart'ı operatör koşar (`./ops/stop-worker.sh && ./serve.sh`).
- **Süreç:** turda tek konsolide-brief'li tek Opus implementasyon ajanı; tam suite turda BİR kez,
  ÖN PLANDA senkron (ajan-içi waiter/arka plan bekleyici YASAK — iki kez arıza çıkardı); uzun
  deterministik işler ana oturumdan harness-izlemeli arka planda; hermes SYSTEM statik (AST çivili).
- **Okuma düzeltmeleri:** replay iyimserliği ölçüldü ~+0.018 (motor sapması) — backtest skorları bu
  düzeltmeyle okunur · R-birimi geniş stopa yapısal önyargılı (boyut R-nötr küçülür, kazanan R'leri
  daralır) — çıkış reformu kararları Hafta 3'ün dolar merceğini bekler · McLean-Pontiff: yayınlanmış
  etkinin en fazla YARISI beklenir · cf sadakat sınırı: cf.advance yalnız stop/target/time_stop
  simüle eder (trail/BE/chandelier/giveback/regime_flip/scale_out ve komisyon/ADV/impact YOK —
  makine-okunur sabitlerle beyanlı, v108 canlı-kaynak testi çivili).
  **· FRİKSİYON İYİMSERLİĞİ (eklendi 2026-08-13 — denetim C2/§H-8):** replay **tüm bacaklara sabit 5 bps** uygular ve **bar-içi stop slipajı SIFIR**'dır (`broker.py:596`, repo: stop dokunuşu `eff_stop`ta dolmuş sayılır) — giriş LİMİT (tavanlı) ↔ çıkış stop→MARKET (tavansız) asimetrisiyle birleşince **adı konmuş bir iyimserlik**. Ölçüldü (EDG-2026-037/038): gerçek giriş slipajı bu varsayımın **~7 katı** (kanonik payda). Mutlak P&L / PF / sharpe **seviyesi** iddiaları bu varsayıma ASILIDIR; eşli R farkları ve oran/sayım ölçütleri değildir (§E.0 ayrımı).

_Aşağıdaki sıra 2026-07-31 gecesinden; güncel öncelikler §3 GÜNCEL DURUM'dadır (bayat referans, tarihçe)._
### SIRALAMA (güncel — rev. 2026-09-02 akşam, operatör onayı): §2 İCRA SIRASI dört kova —
**A kapanış dalgası** (TSK-108 → TSK-060 → TSK-089 → TSK-058 → günlük/ROADMAP kapanışı) →
**B hazır küçükler** (TSK-107 · 087+008 · 101/102/006/030 [tek dilim] · 020 `2-adım2→3→1→9` · 064 · 071 · 115 · 116 · 118 · 117 · 092/113/114 [tek dilim] · 014 · 103 · 083/078/073/082 [bakım dilimi] · 075 · 079 [25a/25c/25d] · 080 · 081-doğrulama · EXE-004-Aşama-2 [hafta sonu] · 119 · 120 · 121) →
**C kart isteyenler** (⑥a→⑥b→⑥c · 062 · 065 · 012-B · 104 · 029/035 · 074 · 077 · EDG-021-2.koşum [QC girişi]) → **D operatör masası** (§5.0).
Sprint çıkışı = DoD + testler yeşil + K-defteri güncel; kapanmadan sonraki sprinte geçilmez.
(Eski WP-dönemi sıralaması §∞ eşleme tablosunda ve §2 SIRA TARİHÇESİ'nde aynen durur.)



**PRG-01 SIRASI (2026-08-22, operatör istedi — bağımlılık sırası; eski: WP1 SIRASI):** ① ~~`Ö-51d` hükmü~~ ✅ aynı gün kapandı → ② `Ö-52` `EXE-2026-007` ölçüm koşumu + karar kuralı gereği `ledgerstamp`e broker-teyit boyutu (ön-ölçüm Ö1=%25 > 0) → ③ friksiyon dayanıklılığı `EDG-2026-040` ölçümü (kart hazır) → ④ `23d` kart yazımı (H0→H1; 23c'nin kapattığı asimetrinin öbür yarısı) → ⑤ `B4`+`D5` OPERATÖR kararları (bloklamaz — kanıt hazır ve karar verilebilir) → ⑥ `23b` (ASKIDA: örneklem bekliyor) → ⑦ `23e`/`23f`/`13` + WP-E boşluk sınıfları (tasarım ister, en sona). GEREKÇE: ①-② defter bütünlüğü zinciri (karşılıksız işlem hâlâ damgasız), ③-④ hazır kartların tüketilmesi, ⑤ operatörde, ⑥-⑦ girdisi/tasarımı olmayanlar.
## §1 HAT — geliştirme yaşam döngüsü ve kapıları

_**[2026-08-31 DURUM DENETİMİ — BU BÖLÜM KALEM TAŞIMAZ.]** Burası geliştirme yaşam döngüsünün KAPILARIDIR (H0…H6): her işin geçtiği süreç, işin kendisi değil. Bu yüzden maddeleri durum işareti taşımaz ve `/api/roadmap` onları `belirsiz` sayar — **bu doğrudur**: "işaretsiz" burada "denetlenmemiş" değil, "durumu olan bir kalem değil" demektir. Denetim 7 tablo satırını kalemi bu gerekçeyle rozetsiz bıraktı; kaynak: `docs/DENETIM-ROADMAP-2026-08-30.md`._

> **Operatör kararı 2026-08-17:** *"bundan sonra superpowers roadmapten bağımsız olarak bütün
> geliştirme cycle'inin belkemiği olacak."* Bu bölüm o hattın **tek kaynağıdır**. Hat ROADMAP'e
> bağlı değildir: burada kalemi olmayan bir iş de aynı kapılardan geçer.

Bu döngü depoda **zaten vardı ama dağınık ve isimsizdi** — kart burada, brief şurada, hüküm
başka yerde. Superpowers'ın katkısı yeni bir süreç icat etmek değil, **aşamalara ad ve kapı
vermek**. Aşağıdaki tablo hattın kendisidir.

| # | aşama | ürettiği artefakt | ÇIKIŞ KAPISI (bu olmadan sonraki aşamaya geçilmez) |
|---|---|---|---|
| **H0** | FİKİR | §4 havuz satırı (`Ö-N`) | bir kart ya da tasarım belgesi doğdu |
| **H1** | TASARIM | ölçüm işi → `research/cards/*.yaml` · mimari iş → `docs/TASARIM-*.md` | Rol-1 onayı; **eşikler DONDU** ve bir daha değişmez |
| **H2** | PLAN | `docs/superpowers/plans/*.md` | dosya-ayrıklık sözleşmesi YAZILI (sohbette değil) |
| **H3** | İCRA | kod + çivi | **çivi ÖNCE yazılır** — düşen testi görmeden kod yazılmaz |
| **H4** | DOĞRULAMA | suite çıktısı + `dagit` günlüğü | otoriter suite YEŞİL (tam `grep -E "FAILED\|ERROR"`, tail-kesme YOK) + `dagit [5]` healthz |
| **H5** | İNCELEME | hüküm metni | Rol-1 denetimi ya da cloud PR turu bir HÜKÜM yazdı |
| **H6** | KAPANIŞ | §7 karar günlüğü satırı | commit + `git push origin main` |

**AŞAMA DEĞİL, DİK DURUM (blocker).** Bir kalem aynı anda hem bir aşamada hem bloke olabilir; bu
ikisini karıştırmak §5'in kalemlerini tahtadan görünmez kılıyordu:
`BLOKE: operatör` (§5) · `BLOKE: erişim/anahtar` · `ASKIDA: kanıt bekliyor`

### Hattın deponun yasalarıyla ilişkisi — ÇATIŞMA HÂLİNDE DEPO KAZANIR

Superpowers 14 skill taşıyor; **11'inin deposal karşılığı zaten vardı** (kök-neden avı, doğrulama,
inceleme, dal kapanışı, worktree, paralel ajan, alt-ajan, plan icrası…). Gerçekten eksik olan
**üçtü** ve hat onları kapatıyor: **H1 mimari tasarım artefaktı · H2 kalıcı plan · H3 test-önce.**

Ters yönde de fark var ve o fark KORUNUR — deponun superpowers'ta **olmayan** disiplinleri:
ön-kayıt kartı (eşiği ölçümden ÖNCE dondurur; spec'ten KATIdır), UYDURMA YASAĞI, YASA 4, YASA 6,
kill-list, K-defteri, `dagit` kapı hattı. Bu yüzden iki bilinçli sapma yazılıdır:
skill "spec'i `docs/superpowers/specs/` altına yaz" der → **depo düzeni kazanır** (`docs/TASARIM-*.md`);
ölçüm işinde spec'in yerini **kart** alır.

### Hattın kendi kanıtı (H3'ün bedeli ölçüldü)

2026-08-17'de `Ö-50` H3'ü **atlayarak** yazıldı (önce kod, sonra çivi). Suite üç yasa borcu ve
**16 kırmızı** çıkardı; kırmızıların üçü tasarımın varsayımlarını çürüttü ve biri gerçek bir üretim
arızasıydı (sprint temiz kurulumda kalıcı MEŞGUL'e kilitleniyordu). Test-önce aynı yere daha ucuz
varırdı. Bu satır burada bir **hatıra değil kapı gerekçesidir**.

## §2 TAHTA — aktif kalemler: tek satır, tek aşama

_**İCRA SIRASI** — sıra icra sırasıdır, kopya değil; her kalem şema kimliğini taşır. **Rev. 2026-09-02 akşam (operatör onayı: "onayla, İCRA SIRASI'nı yeniden yaz"):** konsolide plan DÖRT KOVA — A kapanış dalgası (uçuştakini bitir) → B hazır küçükler (toplu ajan sevki) → C kart isteyenler (ölçüm dalgası) → D operatör masası (karar/para). Kova içi sıra icra sırasıdır. Kova B/C/D'de yalnız kimlikle anılan kalemler §4 havuzunda / §5.0 masada / H-tablolarında tam gövdesiyle yaşar (tek-kaynak: gövde taşınmaz, işaret edilir). DONE kalemler tahtada durmaz: bu dalganın kapananları en alttaki KAPANANLAR alt bloğunda bir dalga tutulur, sonraki tahta boşaltmasında §7'ye iner. Türetim: §2 tahtası + §4 havuzu + §5.0 masası + 2026-09-02 ledger'ı; gerekçe günlük 2026-09-02 (akşam) kaydında._

**KOVA A — KAPANIŞ DALGASI (bugün–yarın; uçuştakini bitir):**

- **[TSK-108] Hafıza sayfası CP-UI birebirleştirmesi** — status: DONE(2026-09-03 görsel tur onayı 12:40Z) · born: 2026-09-02 · owner: rol1 · size: M-L · trigger: —
  What: (status notu 2026-09-02 akşam: T1 9d6b81a · T2 d968e4c · T3 1ecbbe4 · T4 e8f899f [recall sorgu-sınıfı muafiyeti adıyla beyanlı]; tam suite 9430 yeşil + etkilenen küme yeşil; SDD üç görev × inceleme+düzeltme+yeniden-inceleme; ilk dağıtım 436d982 → operatör görsel turu 5 bulgu → T5 ebc8da0 · T6-A 5fd4ff1+c1dac25 · T6-B 3fdd746 (tam suite #2 9480 yeşil + etkilenen küme); ikinci dağıtım d0c7927 (2026-09-03 gece; T5 R20' + T9 CP home + T6 constellation); kalan: operatör görsel turu → DONE. Park [nihai inceleme]: fixture terfisi, `_HAFIZA_UC_TAVANI` doğrudan indeks, `_hafiza_toplam` bool dalı çivisi, M-10 3. örnek, bayat JSDoc.) operatör 2026-09-02: TSK-091 v1 sayfası "hindsight UI'ı ile alakası yok" — karar: CP UI incelenip BİREBİR taşınır. CP v0.9.2 kaynağından ölçüldü: bank-kapsamlı 8-görünümlü kenar çubuğu (home/data/knowledge/recall/reflect/documents/entities/profile) + stats/operasyon/denetim/LLM/mental-models/memory-defense görünümleri + graf. Faz-1 salt-okunur görünümler + recall (beyanlı sorgu-sınıfı POST istisnası); YAZAN her şey görünür-devre-dışı rozetle Faz-2'ye (yazma-vekili kararı ayrı kalem). Plan: docs/superpowers/plans/2026-09-02-hafiza-cpui-birebir.md.
  Why: orijinal talimat "birebir aktarılmalı"ydı (2026-09-01); v1 bunu Kapı-deseni dar yorumuyla uyguladı — spec gerilimi operatör aleyhine çözülmüştü, düzeltiliyor.
  Ref: TSK-091 (v1) · vectorize-io/hindsight v0.9.2 hindsight-control-plane/src · plan dosyası.

- **[TSK-060] Hindsight bot-hafızası kurulumu** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: L · trigger: —
  What: (status notu: Faz-0/Faz-1 kurulum TAMAM; sıradaki: soru kümesi dondurma → arşiv ingest → taban kıyası. born aslen '2026-08-31 akşam' — şema tarihi.) kart `EDG-2026-065` — beş sağlık kanıtı yeşil: servis 0.9.2 canlı (127.0.0.1:8888, MemoryMax=8G, User=ubuntu sapması beyanlı), Memory Defense gün-1 açık (redaksiyon kanıtlı), Türkçe smoke + 2 mutasyon + mükerrer çivisi + gecelik yedek timer'ı kartın kurulum_kayitlarında; model `nvidia/nemotron-3-ultra-550b:free` (ücretsiz şartı, operatör). SIRADA: soru kümesi dondurma (N≥30, blob-sha) → arşiv ingest → taban kıyası. Ardından Türkçe recall kartı → BOT RECALL kartı (DURUŞ REVİZYONU tasarım §3, hedef: "notlar sayfası + iste-getir" — push'u harness derler [reçeteli+kaynaklı+bütçeli], pull tek araç `hindsight_recall`; botlar SINIRLI ajan döngüsüne geçer; kart üç kol: derlenmiş-sayfa/provider-autoRecall/hafızasız taban; autoRetain: aşağıdaki 2026-09-01 revizyonuna bakın; kart geçmeden canlı botlara hiçbir şey değişmez). Ön-hazırlık TAMAM: A1 24GB + Adım-0 ✓, reçete sabit: `slim[local-onnx]==0.9.2` + native PG17+pgvector + Memory Defense gün-1 + BM25 `turkish` (koşullu). DERİN TARAMA + BRAINSTORM KARARLARI (operatör, 2026-09-01 — üç bölgeli doküman taraması sonrası, soru-cevap turuyla): ① autoRetain AÇIK — 2026-08-31 "her durumda kapalı" kararı DEVRİLDİ (operatör seçimi); sonuçları reçeteye girdi: botlarda `retain_async` zorunlu (retain senkron + CPU'da yavaş), Memory Defense redact açık kalır, retain LLM hacmi telemetriden günlük izlenir; araç takımı DEĞİŞMEDİ (tek araç `hindsight_recall` — retain aracı verilmedi, yazım autoRetain'le otomatik). ② Embedding/BM25 YÜKSELTME-ÖNCE: bge-m3 + `bge-reranker-v2-m3` + pgroonga (yalnız hindsight DB'sine; arm64 paket ön-kontrollü) arşiv-ingest'ten ÖNCE kurulur — EDG-2026-065 ölçülmeden EMEKLİYE ayrılır (Senaryo-A/B kıyası düştü; İŞLENDİ 2026-09-01: status=retired, hüküm YOK), yükseltilmiş reçeteyle YENİ kart AÇILDI: `EDG-2026-067` (donuk soru kümesi hedefi korunur; halef kart hipotez/eşik/kill-list'i devralır, tr çivisi bge-m3'le koşulsuz); gerekçe: embedding boyutu sonradan değiştirilemez (veri kaybı), ingest öncesi en ucuz an. ③ CP UI (9999) kurulur ama YALNIZ 127.0.0.1 + ssh tüneli (anahtar koruması upstream'de henüz yazılmadı — açık issue #1148); kalıcı yüzey TSK-091 Hafıza sayfası. ④ Arka plan LLM (auto-consolidation + mental model) AÇIK ve ANA MODELLE (operatör; kota telemetrisi ilk haftanın zorunlu ölçümü; baskıda işlem-bazlı override geriye açık vana). ⑤ `prefetch_method: recall` çiviyle sabit (sessiz reflect-LLM tuzağı) + reflect'in tool-calling şartı ücretsiz modelde canary + API-key extension 401 testi (auth varsayılan YOK — "kurulu ≠ korunuyor"). Tek-kapı kesişimi: `HINDSIGHT_API_LLM_BASE_URL` ileride APISIX'e tek env ile döner — kapı pilotunu BEKLEMEZ.
  Why: Faz-0 tetiği ölçümle değil operatör İLANIYLA ateşlendi (dört amaç: mükerrerlik · öneri akıbeti · trend/örüntü · süreklilikli diyalog — trend+diyalog grep/pano ile yapısal karşılanamaz); kurulum Ajan-A kapanınca (TSK-012 dalga-A) A1 tarafında repo dalgalarıyla paralel, KART-ÖNCE.
  Ref: kart `EDG-2026-065` (retired 2026-09-01, hüküm yok) → halef `EDG-2026-067`; tasarım `docs/TASARIM-HINDSIGHT-ENTEGRASYON-2026-08-31.md` §0/§3/§5-6/§10-11; derin inceleme `docs/INCELEME-HINDSIGHT-DERIN-2026-08-31.md`. GERÇEKLİK KONTROLÜ: commit "EDG-2026-065 ön-kayıt: Hindsight Faz-1 kurulum + recall taban-kıyası" repoda doğrulandı (FAZ B ajanı).

- **[TSK-089] APISIX tek-kapı pilotu — LLM + veri API'leri tek kapıdan** — status: DONE(2026-09-02 gece · dört faz canlı [LLM egress · FMP kota · pano ingress 9443 · bot kimlikleri+filo kotası] + tavan-açma geri alındı (hepsi :free, 67b5f47); "BİLİNEN AÇIK /models sondası" BAYATTI — kapıda `llm-models` rotası var, motor_meridian tüketicisi 200 alıyor (prometheus sayacı, Rol-1 ölçümü 21:20 UTC); kalan: TSK-090 kapı sayfası ayrı DONE) · born: 2026-09-01 · owner: rol1 · size: L · trigger: —
  (FAZ DURUMU 2026-09-01 gece — operatör "Faz 2-3-4'ü öne çek" talimatıyla: Faz 1 CANLI [2 LLM rotası] · Faz 2 KAPI-TARAFI CANLI [fmp-veri rotası + 250/gün redis kotası; canary: geçirgenlik 401/200 birebir, gerçek anahtarla 200; FMP env flip'i sabah restart penceresinde] · Faz 3 CANLI [9443 TLS + basic-auth pano ingress — dışarıdan doğrulandı; sertifika self-signed geçici, alan-adı/OCI-sertifika kararı operatörde; key-auth DEĞİL basic-auth: tarayıcı apikey başlığı koyamaz, beyanlı sapma] · Faz 4 KİMLİKLER CANLI [5 tüketici + filo 1000/gün; LLM rota KİLİDİ bilinçli bekliyor: motor+bot istemcileri anahtar taşıyınca flip]. Sır vakası ölçülüp kapandı: access-log sorgusuz + error warn. OCI listesi zaten "all 0.0.0.0/0" açıktı — etkin duvar host iptables [22+9443]; daraltma kararı operatör masasında.)
  (KAPI AÇILDI 2026-09-01 akşam — operatör: "9-10 için kur iznin var". Faz 1 KURULDU: pinli imajlar + loopback-yalnız + GitOps rota hattı + $env sırları; ölçülen dersler §7 kaydında. İÇERİK-SMOKE KAPANDI 2026-09-01 ~15:25Z: birincil rota `/llm/v1` HTTP 200 + gerçek üretim [nemotron-a55b, 45,2 sn — yavaş ama gerçek; fallback zinciri o anda tetiklenmedi çünkü birincil cevap verdi; gemma `/llm/hizli` aynı dakika hâlâ 429 upstream-havuz]. NOUS ÇEVİRİSİ YAPILDI 2026-09-01 akşam: /opt/meridian/.env'e NOUS_ENDPOINT=127.0.0.1:9080/llm/v1 + NOUS_MODEL=birincil-instance-adı + yer-tutucu API_KEY [kapı Authorization'ı söküp kendi anahtarını takar]; reflect'in nous bacağı learn kapalıyken uyuyan yol — canlanınca kapıdan geçer; bilinen sınır: fallback [gemma] anında künye birincil adı gösterir. FAZ 1 TAMAM. KALAN: Faz 2 FMP egress → Faz 3 pano ingress → Faz 4 bot filosu.)
  (F4-B İSTEMCİ TARAFI İNDİ 2026-09-02 gece — motor Nous istemcisi kapı-anahtarı taşıyabilir: `KAPI_APIKEY` ALLOWED'da, tek `_nous_headers()` iki yüzeye de (chat/completions POST + /models sondası) koşullu `apikey` başlığı ekler, sır yokken bit-eş (v370 9 çivi + 3 mutasyon; SDD incelemesi 7/7 ✅). BİLİNEN AÇIK: sonda URL'si `{base}/models` — kapıda `/llm/v1/models` rotası YOK, flip ÖNCESİ karar: models geçiş rotası YA DA sonda uyarlaması. F4-B KİLİDİ (routes key-auth+consumer-restriction) sabah penceresinde, TÜM istemciler anahtarlıyken EN SON.)
  What: Apache APISIX (traditional mod + tek-düğüm etcd, Docker arm64, sürüm-pin 3.18.x — OpenRouter desteği 3.15.0'da geldi, taban 3.15+) TEK genel kapı; DÖRT FAZ: ① LLM rotası (`ai-proxy-multi` öncelik zinciri danışma→yedek; fallback tetiği 429/5xx/kota-tükenmesi; hermes tarafında tek env: NOUS_ENDPOINT) ② FMP egress (`limit-count` redis 250/gün + `$ENV://` anahtar + `response-rewrite(vars)` ile 402/429 AYRI etiket — maskeleme DEĞİL) ③ pano ingress (key-auth/consumer, limit-req, uri-blocker, request-validation, client-control; TLS: certbot + Admin API push otomasyonu — yerleşik ACME yok) ④ bot filosu (Consumer+Credential rotasyonu, consumer-group filo kotası `limit-count` — günlük 1000 çağrı MEKANİKLEŞİR; not: ai-rate-limiting TOKEN sayar, çağrı saymaz). Konfig GitOps: `routes.yaml` repo'da → idempotent apply → etcd (Admin API `?ttl=` YASAK — kaynağı sessizce siler); gömülü dashboard AÇIK ama yalnız loopback + ssh tüneli (operatör revizyonu 2026-09-01 "aynı şekilde": Hindsight CP UI kararıyla aynı desen — 9180 zaten admin-anahtarlı; Kapı sayfası [TSK-090] olgunlaşana kadar geçici yönetim aracı; tünel-CRUD sapma riskine karşı apply betiğine DRİFT DENETİMİ: etcd↔routes.yaml karşılaştırması, ayrışma alarmı); `plugins:` listesi varsayılanı EZER, birleştirmez — kullanılan her plugin açık yazılır. KAPALI KALIR: batch-requests (CVE-2022-24112 aracı) · server-info · inspect · HTTP/3 · echo/mocking prod rotasında (sessiz-sahte-veri sınıfı — tur kapanışında rota temizliği denetlenir). BİLİNÇLİ DIŞARIDA: Alpaca emir yolu (kapı arızası emir yoluna bulaşmaz) · EDGAR bulk indirme.
  Why: operatör onayı 2026-09-01 ("production'a giderken genel kapı mecburi; dev'de seans kaybı bedelsiz" + tam doküman taraması talebi). Zincir: Kong OSS tedarik-zinciri ölümü (3.10'dan beri hazır OSS imajı yok, hat 3.9.x bakım-modunda, "Is KONG community dead?" issue'su cevapsız; öz-derleme teknik-mümkün/stratejik-ret) → APISIX (ASF, tüm plugin'ler ücretsiz, 3.18 Ağustos 2026) → LLM+veri TEK kapıda → LiteLLM pilotu SUPERSEDED (iki taslak commit'lenmeden geri çekildi; Postgres bağımlılığı + ~400MB/sızıntı sınıfı + minor-kırılma bedelleri düştü). CANARY LİSTESİ (kurulum sırasına çivili): ① ai-proxy-multi zinciri 429'da gerçekten düşüyor mu (gemma 429 doğal test vakası) ② `$ENV://` çözümü + BİLİNÇLİ-BOZUK referansın error-log'a düştüğü (çözüm hatası SESSİZ — literal string kalır) ③ ai-proxy header temizliği (varsayılan TÜM istemci header'larını LLM'ye iletir — proxy-rewrite şart) ④ FMP query-param anahtar enjeksiyonu ($ENV URI alanında; olmazsa serverless-pre-function Lua) ⑤ upstream TLS doğrulaması (tls.verify yalnız Kafka'da belgeli — MITM durumu ölçülür; gerekirse nginx_config proxy_ssl_verify) ⑥ proxy-mirror sır sızıntısı (öncelik 1010 > proxy-rewrite 1008: ayna isteği MASKESİZ gider) ⑦ real-ip trusted_addresses (EN BAŞTA koşar; yanlışsa tüm IP-bazlı kararlar zehirlenir) ⑧ bedel ölçümü (eklenen gecikme + 402≠429 ayrımının adapter'a BOZULMADAN geçişi) ⑨ worker_processes auto container doğrulaması + error_log_level info. Sağlık notu: pasif health-check varsayılanı (429/500/503) 402'yi SAYMAZ — FMP 402 sınıflaması ADAPTER'da kalır, kapı yalnız etiketler. LLM token metrikleri prometheus'a kendiliğinden düşmez — http-logger→api.py hattı (TSK-090 olay şeridi). Config yazımından önce şema teyidi: `GET /apisix/admin/schema/plugins/ai-proxy-multi`.
  Ref: TSK-088 (hüküm) · TSK-090 (pano bacağı) · doküman tam taraması 2026-09-01 (4 bölge + 114 plugin kataloğu; ~70 plugin gerekçeli elendi: SaaS logger'lar, kurumsal IdP'ler, gRPC/Dubbo/MQTT, bulut-fonksiyon sınıfı).

- **[TSK-058] Skill-görüş dalgası — EDG-019 uygulaması + EDG-063 LLM-üretici sınıfı** — status: ACTIVE · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: (status notu: implementasyon İNDİ 2026-09-01 — kuyruk+LLM üreticisi, SDD tam döngü 2 fix turuyla, 16/16 mutasyon kanıtı, commit 697655a. FAZ C UYGULANDI 2026-09-01 akşam [operatör "sabah paketini şimdi yap"]: bayrak kartın `acilis_kaydi_2026_09_01` resmî kaydıyla açıldı [d5d738e, suite 8720+6 yeşil — tek kırmızı repo-dışı ayna kopyasıydı, türetilip kapandı]; birim+timer kuruldu, timer armed 07:30Z; kurulum-günü elle ateşleme Result=success/exit-0 — boş kuyruk, tasarım gereği arıza değil. KALAN: işçi üçlüsünün yeni kodla restart'ı [sınıflandırıcı canlı-motor restart'ını reddetti — komut operatöre verildi] → kadans kuyruk-append başlar → ilk DOLU üretim koşumu yarın 07:30Z, sonucu karta.) kart `EDG-2026-019` (registered — defter+iki çözücülü yüzey) + kart `EDG-2026-063` (ön-kayıt: beyan-only SKILL.md'ler LLM'le AYNI deftere gölge görüş yazar). Tek dalga iki kart: altyapıyı 019 kurar, 063 LLM-üretici sınıfını AYRI kartla açar. Aynı satır §2 TAHTA H1'de tam gövdesiyle yaşar.
  Why: operatör 2026-08-31 — "beyan-only skill'lerin LLM ikinci görüşünü de yapalım"; icra Ajan-A dalgasından SONRA sıraya alındı (o dalga artık kapandı).
  Ref: kart `EDG-2026-019`, `EDG-2026-063`; §2 TAHTA H1 satırı (aynı kalem).

- (A-5 günlük + ROADMAP kapanışı: 2026-09-02 ikinci yarı — ücretli→ücretsiz kararı [kapı 67b5f47 + Hindsight .env], hindsight-api OOM düşüşü, sağlayıcı-yönlendirme dersi, sır-süzgeci vakası — TEK commit, TSK-108 T4 ile birlikte.)

**KOVA B — HAZIR KÜÇÜKLER (bu hafta; ajan işi, toplu sevk — gövdeler §4 havuzunda):**

- (B-1 **TSK-107** geri-dolum `indir()` boyut doğrulaması — S, bağımsız, hemen sevk edilebilir.)
- (B-2 **TSK-087** geri-dolum işçi-çökmesi dayanıklılığı + **TSK-008** dagit bakım penceresi `meridian-learn` restart'ı — geri-dolum haftası ailesi, birlikte.)
- (B-3/4 **TSK-101** · **TSK-102** · **TSK-006** · **TSK-030** — TEK DİLİM [operatör 2026-09-03 sabah: "o dört kalemi de tek dilimde sıraya al"]: defter/alan tutarlılığı üçlüsü + çapa göçü adım-3; tek ajan, tek paket, tek inceleme. Gece kuyruğunda kova-B'nin YAPILMAYAN yarısı.)
- (B-5 **TSK-020** backend: sıra `2-adım2 [aylık Parquet] → 3 → 1 → 9` — operatör 2026-09-01; revize notu aşağıda aynen.)

- (D REVİZE sırası, operatör onayı 2026-09-01 gece — bkz. **TSK-020**: sıra `8→4→2→1→3→9`'dan `4→2-adım2→3→1→9`'a revize edildi çünkü [UYGULA-8] artık DONE'dur [yukarıda not edildi]; `2-adım1` [events.jsonl doğrudan DuckDB sorgusu] İLK SIRAYA alındı (operatör 2026-09-01, sıra başındaki araya-kalem bloğu). UYGULA-1 notu: PG artık canlıda ama SQLite→WAL kararı DEĞİŞMEZ [motor izolasyonu gerekçesi ayakta]. UYGULA-9 = Prometheus+Grafana açık adla. Bu revizyon notu TSK-020'nin dondurulu §4 gövdesine Rol-1 tarafından işlenmelidir — FAZ B §4'e dokunmaz.)

- **[TSK-064] Sır-yönetimi kademeli YOL-1** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: (operatör K3 2026-09-03 sabah: Faz-0 [chmod 600 + envanter çivisi] Faz-1A/1B ile TEK DALGA — ayrı sabah adımı YOK.) (status notu 2026-09-03 gece: REPO-TARAFI HAZIRLIK YAZILDI — `docs/TASARIM-SIR-YOL1-2026-09-03.md`: envanter [5 dosya, yalnız adlar; 16 sır / 32 ayar], sınıf A/B/C/D, Faz-0..1C; Bulgu: `.env-apisix` mod 640 → 600 [sabah], DASH_TOKEN iki dosyada, vekil TENANT anahtarını dosyadan okuyor. Canlıya dokunulmadı.) kalan sırların LoadCredential/sops'a taşınma hazırlığı (B-DASH-CRED faz-1 emsali, TSK-049); OpenBao/unseal adımı BEKLEMEDE-7'de operatörde.
  Why: sır-yönetiminin kademeli göçünün ilk basamağı — mimari madde 7, `§4` bloğunun BEKLEMEDE-7 kaydı.
  Ref: TSK-049 emsali; `BEKLEMEDE-7`.

- (B-7 **TSK-071** friksiyon haftalık koşum — takvim: 5 Eylül; H1 tablosunda yaşar.)
- (B-8 **TSK-115** ingest067 parça küçültme + Hindsight LLM retry ölçümü + boş-saat tetiği — operatör K1 2026-09-03 sabah.)
- (B-9 **TSK-116** evren emekliliği: S&P 500 dışı 13 sembol → RETIRED_SYMBOLS — operatör K5 2026-09-03 sabah. **KAPANDI 2026-09-03 gece: b81b19b, dağıtım #8 canlı payda 238.**)
- (B-10 **TSK-118** ⌘K "Meridian dersleri" → dokuzuncu Hafıza nav durağı — operatör K8 2026-09-03 sabah.)
- (B-11 **TSK-117** palet turu: rezerve hue bantları + anlam jetonları — H1 tasarım belgesi ÖNCE; operatör K7 2026-09-03 sabah.)
- (B-12 **TSK-092** · **TSK-113** · **TSK-114** — TEK DİLİM [operatör 2026-09-03 sabah: "092+113+114 tek dilim"]: dağıtım reçetesi istenen-durum koruması + çivi · `Kapi` 7 kopya → tek kaynak · v323 `teknik` çağrı-yeri kapsaması; tek ajan, tek inceleme. — **KAPANDI 2026-09-03 10:28Z: fb07a16, dağıtım #6; 2 inceleme + 1 düzeltme turu; suite #6 9920/0.**)
- (B-13 **TSK-014** teslim-öncesi ikinci-görüş geçişi (SOUL kural denetimi) — AYRI dilim [operatör 2026-09-03 sabah]; **SEVK 2026-09-03 10:31Z (tek opus ajan; brief: ortak `ops/soul_denetimi.py`, mekanik terim korunumu önce, SOUL.md tek kaynak, fail-open BEYANLI, koşum başına çağrı tavanı 4, v385).** Not: "günlük kota kullanımı ~%0,2" kodda doğrulanamadı — filo-çapında sayaç YOK (keşif 2026-09-03), yalnız skill_gorus_llm kendi 100/gün alt-kotasını sayıyor; üç bot kapsar.)
- (B-14 **TSK-103** `full_detail_graded` span_days = dilim takvimi — operatör K6 2026-09-03 sabah; sayılar değişir, ayrışma beyanı + çivi.)
- (B-15 **TSK-083** · **TSK-078** · **TSK-073** · **TSK-082** — BAKIM DİLİMİ, tek ajan [operatör 2026-09-03 sabah]: ROADMAP satır çapaları → sembol · `26` değer-eşitliği 9 çift envanteri · 24b skill-görüş defteri kalanı · §6 kart indeksi üreticiye [Rol-1 yol kararı bu dilimde]. Gövdeler TAHTA H0'da.)
- (B-16 **TSK-075** `13` scale-out latent kusuru — AYRI dilim [operatör 2026-09-03 sabah]; motor kodu, tam suite. Gövde TAHTA H0'da. **KAPANDI 2026-09-03 gece: d0ed07d, dağıtım #8.**)
- (B-17 **TSK-079** `25a` kaldır + `25c` dirilt + `25d` ezilme zinciri — TEK DİLİM [operatör 2026-09-03 sabah: "üçünü de sıraya al"]; 25c dirilt canlı davranışı etkilerse KART-ÖNCE (KOVA C'ye taşınır). Gövde TAHTA H0'da. **25c-1 KOVA C HÜKMÜ 2026-09-04: EDG-072 KALDI (şasi bayatlığı) → EDG-073 R2 KALDI — rejim-koşullu çıkış H1/H2 ΔP&L CI sıfırı kapsıyor (orta +6.530/+3.638, dd 0,90); sevk kapısı KAPALI, 'kanıtla kapalı' (commit ec701b3).**)
- (B-18 **TSK-080** `Ö-49` çapa/beyan çürümesi kalanı — İKİNCİ BAKIM DİLİMİ, B-15'ten sonra [operatör 2026-09-03 sabah]; ölçüm önce: kalan sayısı. Gövde TAHTA H0'da. **KAPANDI 2026-09-03 gece: 3a493a4, dağıtım #8.**)
- (B-19 **TSK-081** ARSENAL doğrulama ölçümü — **KAPANDI 2026-09-03 sabah (Rol-1 ölçümü):** 2026-08-24 hükmü DOĞRU — ARSENAL politikası `docs/POLITIKA-ARSENAL.md` olarak VAR (K7 2026-08-23), 15e giriş yarısı DONE; `15d` PIT-temiz faktör seti için tasarım belgesi `docs/TASARIM-15D-PIT-FAKTOR-SETI-2026-08-23.md` VAR → KOVA C kart adayı (kart-önce); `15c` evren genişletme 044/084 kararına bağlı, BEKLEMEDE [operatör C-084 2026-09-03: beklemede]. Gövde TAHTA H0'da.)
- (B-20 **EXE-2026-004** cf çıkış-sadakati Aşama-2 koşumu — HAFTA SONU bakım penceresi [operatör 2026-09-03 sabah]: Cumartesi seans dışı, worker durdurulur, saatler sürer, state'e yazar; hüküm karta + K-defterine. Gövde §6'da.)
- (B-21 **TSK-119** TSK-030 adım-4: `tests/`+`ops/` satır çapaları (59 satır / 28 dosya) — B-15 bakım dilimiyle birlikte ya da hemen ardından; dilim incelemesi Ö3, 2026-09-03. KOD TAMAM 2026-09-03 gece (76/30 ölçüldü), inceleme KABUL, suite #11 uçuşta.)
- (B-22 **TSK-120** api.py 7 çürük sembol çapası + capa_uyusmasi üçüncü besleme — B-21 ile aynı dilimde; dilim tur-2 devri, 2026-09-03. **KAPANDI 2026-09-03 gece: a57e2c8, dağıtım #8; aşama-2 → TSK-129.**)
- (B-23 **TSK-121** pano komşu kopyaları (Bildiri/BayatSerit/YukleniyorIskeleti/Olculemedi) + TSK-114 pano-geneli — B-12 devri, 2026-09-03.)

**KOVA C — KART İSTEYENLER (ölçüm dalgası; kart-önce, §5 yasası):**

- (C-9 **TSK-074** `propose_virgin_knob` hayalet-düğme süzgeci — KART-ÖNCE [operatör 2026-09-03 sabah]; **KART YAZILDI 2026-09-03 sabah: `EDG-2026-071` (§6, `registered`, K=2 + ADIM-0 donmuş `hypotheses.jsonl` kopyası, kill: yanlış-pozitif>0) — OPERATÖR ONAYLADI 2026-09-03 ~10:45Z; ölçüm kodu KOVA C sırasında.** Tasarım belgesi `docs/TASARIM-VIRGIN-KNOB-SUZGECI-2026-08-22.md`; learn kapalıyken kurulup ölçülür. Gövde TAHTA H0'da.)
- (C-10 **TSK-077** WP5 kalıntıları: `M2` DSR-yarısı (K=1) + `M11` kova-6 taraması — **ŞEMA KARARI VERİLDİ 2026-09-03 sabah (Rol-1, ölçümle): DAMGA** — kapının DSR girdisi `_ret` adayın `_trades_search` listesinden gelir ve hiçbir deftere yazılmıyor (geçmiş için donmuş-çekim İMKÂNSIZ); `validation.record_candidate` satırına `ret_seri`+`ret_n` damgası, retro-damga YASAK. KYS-2026-002 kartına R2 planı yazıldı (trial `r2_dsr_damgali`, ADIM-0 ≥8 damgalı aday). (SEVK 2026-09-03 15:54Z: tek sonnet ajan, brief .superpowers/sdd/2026-09-03-tsk077; ret_seri+ret_n, retro-damga yasak, CONTRACTS required değişmez, bedel: satır ~70–110 float, defter LEDGER_CAP ile sınırsız — kırpma ayrı kalem; learn kapalıyken damga birikmez.) Damga kodu + çivi: **OPERATÖR ONAYLADI 2026-09-03 ~10:45Z** — C-10 altında KOVA B sırasına girer (küçük motor değişikliği, `meridian/reflect.py::record_candidate` çağrı yeri; tam suite). `M11` kova-6 taraması ayrı kart, sırada. Gövde TAHTA H0'da. **KAPANDI 2026-09-03 gece: 2578061 damga canlı, dağıtım #8; M11 kova-6 taraması AYRI kart, sırada.**)
- (~~C-11 **EDG-2026-021** ikinci koşum~~ KAPANDI 2026-09-03 08:1xZ: Rol-1 CLI push + Chrome'da koşturdu; hüküm ŞÜPHEDE-bilgisiz → arşiv, EDG-016 canlıda; KAPANANLAR bloğuna iner.)

**Pilot sonrası SİNYAL ZİNCİRİ** (operatör 2026-08-31 akşam: "bu şekilde plana dahil et"):

- (PARALEL not: ⑥a kartı [bkz. **TSK-066**] geri-dolumun 2.-3. günü erken yazılır — İCRA SIRASI'nın kendi zamanlama notu, ⑥a'nın gövdesinde tekrar edilmez.)

- **[TSK-066] ⑥a — mevcut sinyallerin AN yeniden-kurulumu** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: (status notu 2026-09-03 gece: KART YAZILDI — EDG-2026-069, §6; ONAY 2026-09-03 sabah [K2], ölçüm kodu KOVA C sırasında.) sinyal hangi saniyede doğdu, icraya kadar fiyat ne yaptı (EDG-040 friksiyon sorusunun tick bacağı). Kartı geri-dolumun 2.-3. günü erken yazılır (PARALEL not, yukarıda).
  Why: pilot sonrası sinyal zincirinin ilk halkası — mevcut sinyallerin tick-doğruluğunu ölçer.
  Ref: EDG-2026-040.

- **[TSK-067] ⑥b — İLK yeni-sinyal kartı: işlem yönü + akış dengesizliği** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: işlem-anı anlık görüntü bunu bedavaya getirir; kartın 1. kill-list maddesi IEX temsiliyeti — ~%2 hacim payının evrenimizde piyasa-geneli akışı temsil ettiği ölçülmeden hiçbir akış sinyali yayılmaz.
  Why: TICK-ARŞİV pilotunun (TSK-056) getirdiği yeni veri yüzeyinin ilk somut sinyal adayı.
  Ref: —.

- **[TSK-068] ⑥c — spread dinamiği + icra zamanlaması** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: S-M · trigger: —
  What: saat-dilimi/emir-tipi kuralları — alfa değil friksiyon düşürücü.
  Why: her aday KENDİ kartından + OOS kapılarından geçer; yeni sinyal yüzeyi doğduğu gün `pitlaw` kaydına girer; 1/sn seyreltme saniye-altı sinyalleri KAPATIR (beyanlı bedel, TSK-056'nın kabul ettiği bedelle aynı).

- (bkz. **TSK-062** — öğrenme-kilidi çifti [EDG-064+EDG-058]: ana sıraya BİRLEŞTİRİLDİ [paralel-şerit birleştirmesi, operatör 2026-09-01]; slot GERİ-DOLUM BİTİŞİ — learn program boyunca KAPALI [ölçüm koşulları bozuk, kapalı learn üstünde kilit ölçümü sahte sayı üretir; 2026-09-01 gece onayı]. Aynı kalem §2 TAHTA H1'de tam gövdesiyle yaşar.)

- (bkz. **TSK-065** — PIT mid-cap SAĞ-KALAN üst-sınır ölçümü: KART-ÖNCE, yanlılık beyanlı [EDG-018 askıda kalır, yeni kart]; TSK-062'nin hemen ardında koşar [paralel-şerit birleştirmesi 2026-09-01 — eski "seans-dışı şerit" kavramı kapandı]. Aynı kalem §2 TAHTA DİK DURUM'da tam gövdesiyle yaşar.)_
> Bugüne dek "açık kalemler" §3'ün WP tablosunda **düzyazı yığınıydı** ve hangi kalemin nerede
> olduğu okunamıyordu. Tahta onu satırlaştırır. **Tek kural: her aktif kalem tam bir satır ve tam
> bir aşama.** İki aşamadaysa kalem İKİYE bölünür.

- (Ajan dalga-B — sohbet, duruş çivili: bkz. **TSK-012** — aynı kalemin ikinci bacağı, İCRA SIRASI'nda burada tekrar anılır, ayrı numara almaz.)

- (C-8 **TSK-104** seyrelme gözlem paketi — GATED: EXE-011 canlı ilk hafta birikimi; §4.)
- (C-9 **TSK-029** mutasyon kapsamı · **TSK-035** seed_boundary — taslak hazır, sıra sonu; §4.)

**KOVA D — OPERATÖR MASASI (karar/para; asıl kayıt §5.0 — burada yalnız işaret):**

- **[TSK-063] Faz-6 kilit-zinciri KANIT bacağı + BEŞ KİLİT** — status: GATED(beş kilidin kanıtla dolması + `INTRADAY_ARM` operatör onayı) · born: 2026-08-31 · owner: rol1 · size: M · trigger: kanıt-şartlı (dalga kapanışlarında 5-kilit durumu raporlanır)
  What: dalga kapanışlarında 5-kilit durumu raporlanır + Faz-5 örneklem (11/20) dolunca ölçüm + dağıtım-sonrası `edge_verdict` okuması (v245-D bilgilendirmesi); `INTRADAY_ARM` ONAYI OPERATÖRDE KALIR. İlişkili: TSK-043 (kadanslı yazarın Faz-6 kilidini düşürebileceği yan-etki bulgusu).
  Why: kanıt-şartlı kilitler — açılış kararları operatörde; §2 TAHTA'nın DİK DURUM satırı (Faz-6 BEŞ KİLİT, ASKIDA: kanıt-şartlı) bu kalemle aynıdır.
  Ref: `health.faz6_kilitleri`; kimlik `B-FAZ6-KILIT` (§5 KİMLİK TABLOSU); bağlı: TSK-043.

- (bkz. **TSK-061** — C·WP12 Faz-5 rol seçimi: KİLİT AÇILDI, üç bot canlıda, ilk karne indi — seçim ölçümü bot değer-kanıtı biriktikçe. Aynı kalem §2 TAHTA H1'de tam gövdesiyle yaşar.)
(Not: F·operatör masası `§5.0` — DARALDI; masa tablosunun kendisi kalem taşımaz, bkz. §5.0 masası.)

- (D-3 §5.0 açık kimlikler: `B-TAVAN-502` [YENİ 2026-09-02: hepsi-ücretsiz kararının bedeli — tavan dolunca botlar 502; kabul mü, sessiz-atla mı] · `B-PG-ROTASYON` [YENİ 2026-09-02: Postgres parolası Rol-1 terminaline düştü; rotasyon evet/hayır] · `B-FMP-PLAN` · `B-FINVIZ-TOKEN` · `B-DELIST-KAYNAK` · `B-QC-LOGIN` · `B-NOUS-BEYIN` [Rol-1 ölçer-kapatır: kapı zinciri 2026-09-02'de ölçüldü] · `B-FAZ6-KILIT` [TSK-063] · `B-AJAN-TAVAN`.)
- (D-4 operatör sorusuyla açılanlar: **TSK-095** openrouter/auto [OPERATOR] · **TSK-097** çok-kullanıcı · **TSK-096** metrik trendi — §4.)

**KAPANANLAR — bu dalganın DONE kalemleri (tarihçe; sonraki tahta boşaltmasında §7'ye iner, gövdeler AYNEN):**

- **[TSK-052] A·PIT/veri (EDG-062)** — status: DONE(2026-08-31 · kart `EDG-2026-062` measured, hüküm `verdict_2026_08_31` dört kriterle · push 054f822; tahta hizalaması 2026-09-01 — kart hükmü işlenmişken satır ACTIVE kalmıştı, tek-kaynak ayrışması kapatıldı) · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: PIT ihlal düzeltmesinin (b) yolu (EDG-2026-062) İNDİ; inişi TSK-011 (cf tarama kuyruğu) ve TSK-059 (B·P-2/`ts` kart uygulaması) kapılarını AÇAR.
  Why: PRG-01'in (eski: WP1) "A" bacağı — sıra bu kart bitmeden sonraki icra kararlarını (P-2/ts, gerçek friksiyon tahmini) bekletiyor.
  Ref: EDG-2026-062; bağımlı: TSK-011, TSK-059.

- **[TSK-053] Akıbet Defteri** — status: DONE(2026-08-31/09-01 · `ops/akibet.py`, commit "Akıbet defteri doğdu: akibet.py aracı + şef brifingi üç-blok süzgeci", v349, 28 çivi) · born: 2026-08-31 · owner: rol1 · size: S · trigger: —
  What: öneri→karar→sonuç zinciri (Meridian defteri) — her hafıza yolunun ön şartı.
  Why: 2026-08-31 akşam brainstorm kararı: bu zincir o güne dek hiçbir yerde kaydedilmiyordu; küçük iş, sonraki adımların (AKIBET KARARLARI, AKIBET-DALGASI) önkoşuluydu.
  Ref: `ops/akibet.py`; GERÇEKLİK KONTROLÜ: dosya + commit repoda doğrulandı (FAZ B ajanı).

- **[TSK-054] Ajan Yüzeyi Mesajlaşma Göçü** — status: DONE(2026-08-31 akşam · commit `5fa9d39`, 59 çivi + tarayıcı doğrulaması) · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: operatör "Hermes-Bot-Mode gibi olsun, arayüz karışık" dedi — maket 3 turda onaylandı; dört sekme (Sohbet/Defter/Ölçüm/Filo) tek mesajlaşma gramerinde: botlar kişi + #öneri-hattı kanal + kilitli yazma şeridi.
  Why: okunmamış-rozet ve verisiz kadans etiketi uydurma yasağıyla DÜŞTÜ; v323 + tam suite kapılı.
  Ref: commit `5fa9d39`.

- **[TSK-055] Akıbet Kararları — ilk gerçek karar turu** — status: DONE(2026-09-01 gece) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: 22 öneri → 13 ret (mükerrer/ölçümsüz-parametre/eylemsiz/zaten-planda) + 5 ertele (learn-tetikli ×3, TSK-020 UYGULA-9-kapsar ×2) + 4 kabul-açık; kararlar deftere `--veren` etiketli işlendi — 16 operator, 2 rol1 sınıf-genişletmesi beyanlı.
  Why: akıbet defterinin (TSK-053) ilk gerçek karar turu; TSK-003'ün (%45 bellek-yokluğu) gerekçesi bu turdan.
  Ref: `ops/akibet.py` karar kayıtları, 2026-09-01 gece.

- **[TSK-056] Tick Hüküm + Geri-Dolum (TICK-ARŞİV pilotu, EDG-2026-066)** — status: DONE(2026-09-01 gece · `18c3e7f`) · born: 2026-08-31 akşam (born tahmini: pilot kararı bu tarihte; hüküm 2026-09-01'de indi) · owner: rol1 · size: L · trigger: —
  What: EDG-066 hükmü GEÇTİ — PK 30/30 işlem-sayısı Alpaca'yla BİREBİR · yoğunluk 250/250 %100 · seyreltme bedeli sayıyla: işlem-anı anlık görüntü modern günde işlemlerin %23,9'unda ızgaranın bilmediğini kurtarıyor. Kapsam 662 = PIT-S&P∪NDX-anlık∪evren (`kapsam_uret.py`); 662-kapsamla gerçek boyut 21/80/98 MiB/gün → ~73 GB projeksiyon, pencere 2020-01'e RAHAT. Pilot: S&P500+NDX · pencere 2020→bugün GERİYE doğru · kotasyon 1/sn seyreltilmiş + işlem-anı anlık görüntü + işlemler tam · tavan 120 GB `/opt/veri` (150G birim bağlandı) · motor DuckDB+Parquet (satır-DB yok). Çalıştırıcı `geridolum.py` + `meridian-geridolum.{service,timer}` F9'a kayıtlı, süzgeç kanıtı BİREBİR.
  Why: 1/sn seyreltme saniye-altı sinyalleri KAPATIR (beyanlı bedel) — geri-dolum programı bu bedeli kabul ederek kuruldu.
  Ref: kart `EDG-2026-066`; commit `18c3e7f`. GERÇEKLİK KONTROLÜ: `deploy/oracle-a1/geridolum.py` + `meridian-geridolum.timer`/`.service` repoda doğrulandı (FAZ B ajanı) — **systemd kurulum bloğu OPERATÖRDE** (canlıya kurulum henüz operatör penceresi bekliyor, artefaktın kendisi hazır).

- (D·altyapı-8 xdist: bkz. **TSK-020** `[UYGULA-8]` — GERÇEKLİK KONTROLÜ: `pyproject.toml`daki 2026-09-01 tarihli yorum artık "-n 4 ile ~9 dk, 2 temiz koşum, 8.344 test, 0 paralellik kırmızısı — xdist_group gerekmedi" diyor; koşum-2 doğrulaması TAMAMLANDI ve `-n 4` pyproject'e pinlendi. TSK-020'nin gövdesi §4'te dondurulu olduğundan (FAZ B kapsamı §4/§5'e dokunmaz) bu GERÇEKLİK KONTROLÜ farkı burada not düşülür; TSK-020'nin kendi UYGULA-8 alt-maddesinin durumu Rol-1 tarafından güncellenmelidir.)

- **[TSK-057] Akıbet-Dalgası** — status: DONE(2026-09-01 gece · commit "Akıbet-dalgası: ship yolu backtest_full taşıyor, coverage fişi hotstate sensörüne bağlı") · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: operatör kabulü 4 kalemdi; keşif 2026-09-01 gece İKİYE indirdi — ikisi BAYAT çıktı ve deftere gerçek akıbetiyle kapandı: N00010 `uygulandi` (v245/`3c9fd0f` öneriden 4 gün sonra çözmüş; canlı eğri 894 nokta, son 2026-08-31 — doğrulandı) · N00011 `reddedildi` (temelsiz: 3 nabız EXPECTED'da ilk commit'ten beri, 17/17). KALAN 2 GERÇEK KALEM İNDİ (Opus ajanı TDD + Rol-1 inceleme ONAY; tam suite 8.351 yeşil — tek kırmızı v280 ölü-alan dedektörünün ad-çakışması yanlış-pozitifiydi, dar zincir-istisnasıyla mutasyon-kanıtlı kapatıldı): N00017 ship yolu karneye `backtest_full` (v293 test gövdesi docstring izniyle güncellenir; bkz. TSK-002) · N00016 coverage fişindeki sabit `surec_ici_sayac: None` → `watchdog.hotstate_health_report` bağlantısı.
  Why: DERS (Hindsight gerekçesine kanıt) — yansıma motoru kodu DOĞRULAMADAN öneriyor: 22 önerinin 2'si var-olanı istiyordu, 1'i çözülmüşü. Bu ders TSK-003'ün (yansıma mükerrerlik kapısı) gerekçesine girdi.
  Ref: commit "Akıbet-dalgası…"; bağlı: TSK-002.

- **[TSK-001] ROADMAP-STANDART dalgası** — status: DONE(2026-09-01·suite 8421 yeşil, 6baf92a zinciri) · born: 2026-09-01 · owner: rol1 · size: L · trigger: —
  What: (status notu: kapı 2026-09-01 gece çözüldü — akıbet-dalgası [TSK-057] kapandı; ek talimat: her kalem gerçeklik kontrolünden geçer + açık/kapalı sınıflanır, spec tarihli ek.) yaşayan bölümlerin (§0/2/3/4/5/6) tamamı standart madde şemasına göçer; ROADMAP-doğumlu kimlikler TSK-###/PRG-## olur (dış kimlikler EDG/N/vNNN/Yasa Ref'e iner, DEĞİŞMEZ); zorlama çivisi + CLAUDE.md kapısı + `/api/roadmap` alan-ayrıştırması + YolHaritası dinamik tahtası aynı dalgada; §7/§8 geriye dönük muaf.
  Why: operatör 2026-09-01 gece ("hiçbir madde birbirine benzemiyor… pano dinamik olmalı"; kimlik/İngilizce-terim/muafiyet/zorlama/slot onayları aynı gece).
  Ref: `docs/TASARIM-ROADMAP-STANDART-2026-09-01.md`.

- (ARAYA-KALEM BLOĞU — İLK SIRA, operatör 2026-09-01 "bunları da ilk sıraya al"; üçü de küçük, TSK-052 uçuşuyla çakışmaz:)

- (bkz. **TSK-003** — YANSIMA MÜKERRERLİK KAPISI [a bacağı]: GERÇEKLİK 2026-09-01 — (a) bacağı ZATEN İNDİ [131ffa8, `mukerrerlik.py` + v352 28 çivi, status DONE]; bu bloktaki kalan iş yalnız İSRAF ÖLÇÜMÜ: sonraki akıbet karar turunda %45→≤%10 hedefi ölçülür. (b) bacağı ingest-sonrası recall'a GATED.)

- (bkz. **TSK-086** — İNFRA-SİMETRİ ikinci bacak: **DONE 2026-09-01** — Altyapı kartı üç durumu ayırıyor (boş=sessiz · null=görünür-ölçülemedi+gerekçe · dolu=amber rozet+liste+`komut` dipnotu); v354 19 çivi, SDD tam döngü [inceleme 1 blocker + 8 bulgu → fix turu → re-review 9/9 TAMAM]; park edilen 3 K-notu re-review raporunda. Yasa 6 borcu kapandı.)

- (bkz. **TSK-020** `2-adım1` — **DONE 2026-09-01**: `ops/olay_sorgu.py` + v355 36 çivi; SELECT-kapısı bypass avı temiz, bağlantı sertleştirmesi [temp_directory/autoinstall kapalı], RUNBOOK kümesine kayıtlı. Adım-2 [aylık Parquet] TSK-020 gövdesinde sırasını bekliyor.)

- **[TSK-059] B·P-2/`ts` kart uygulaması** — status: DONE(2026-09-01 · kart hükmü `p2_kapanis_2026_09_01` + hakem dizini `edg042_hakem_2026-09-01/` [26 çivi v359, 7/7 mutasyon] + işaretçi sha'lı çevrildi + ilk ateşleme gerçek A1 çekimiyle: giris_once n=15 tabanla birebir, ayrışan 0, tetik orneklem_birikimde) · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  (kapı AÇILDI 2026-09-01: EDG-062(b) inişi gerçekleşmişti — TSK-052 hizalaması. Aynı gün kart hükmü + kod + ateşleme; kalan iş yok — hakem bundan sonra haftalık 042 görevinin EK adımında yaşar, tetik hükmü tedavi kolu n≥10 dolunca.)
  What: akıbet kararlarına göre kart uygulaması; aynı kalem §2 TAHTA H1'de `EXE-2026-009` P-2 (hakem anahtarı `ts` geçişi) olarak tam gövdesiyle yaşar.
  Why: KOVA-2 kararı 2026-08-31'de Rol-1'e DEVREDİLDİ (85-aktarımı) — (a)/(b)/(c) seçenekleri P-3 ölçümüyle AŞILDI, yol `ts` anahtarı.
  Ref: kart `EXE-2026-009`; §2 TAHTA H1 satırı (aynı kalem).

- **[TSK-106] `session_refresh` defteri günlük yol-başına özete iner** — status: DONE(2026-09-02 · 90acfaa: v374 15 çivi + 8 mutasyon; SDD incelemesi spec 7/7 ✅; tam suite 8939 yeşil. İki yan kazanç: v274 middleware çivisi kaza-yeşiliydi — düzeltildi; v311'de üç bayat çapa mezar-taşıyla işaretlendi. ŞERH-1: defterde `session_refresh` artık İKİ satır sınıfı — anlık [ozet=false] + günlük özet [ozet=true, toplam_n N olayın raporu]; gelecekteki sayaç/dedektör ozet alanına bakmalı. ŞERH-2 ruling: `_session_refresh_ornekle` adı yanıltıcı ama KALDI — bu Ref çapası + v274 çapası taşıma maliyeti ad kazancını aşıyor, gerekçe docstring'de) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: api.py `_session_refresh_ornekle` bugün (ip, yol) başına ~5 dk'da bir olay yazar (SEL KESİMİ, 2026-08-23) — kalan gürültü yine günde onlarca satır. Yeni sözleşme: (ip, yol) başına GÜNDE TEK özet satırı (UTC gün anahtarı; alanlar: gün toplamı + ilk/son görülme; gün dönüşünde önceki günün özeti yazılır, çiftin İLK olayı görünürlük için anında yazılır). BEDEL BEYANLI (ölçüldü 2026-09-02): bireysel damgaların api.py dışında HİÇ tüketicisi yok; kayıp = gün-içi kadans çözünürlüğü + süreç yeniden başlarsa o günün sayacı (bugün ≤5 dk'lık sayaçtı). Motor değişikliği: push tam suite hükmü bekler; v245/v274 çivileri yeni sözleşmeye hizalanır.
  Why: operatör kararı 2026-09-02 sabah paketi ("Günlük özet"): sel kesimi sonrası kalan kadans da defter okuyucusuna gürültü.
  Ref: api.py::_session_refresh_ornekle (SEL KESİMİ bloğu) · sabah paketi karar turu 2026-09-02.

- **[TSK-091] Hafıza sayfası — pano'da Hindsight'ın tam yüzeyi** — status: DONE(2026-09-02 · kod 5c1ed2c+bea75b0, dağıtım ab0ed5b penceresi; canlı doğrulama: /api/hindsight canlı+kimlik-kapılı [çerezsiz 401], bundle DuLBfJd2 yayında, upstream 8888 sağlıklı — gerçek-veri görseli operatör tarayıcısında) · born: 2026-09-01 · owner: rol1 · size: M · trigger: —
  (KOD İNDİ 2026-09-02: SDD 2 görev + 3 düzeltme turu — 5c1ed2c `/api/hindsight` vekili [v375 60 çivi; canlı gövde ölçümü bir varsayımı düşürdü: /version alanı api_version] + bea75b0 Hafıza sayfası [4 bölüm, üç-durum ayrık; inceleme B-1'i yakaladı: skaler→tarih uydurması ISO süzgeciyle kapandı]. Tam suite 8999 yeşil. KALAN: dağıtım + A1 canlı doğrulama [operatör penceresi] — DONE o zaman. Vekil öneki ruling'i: plan `/api/memory/*` diyordu, o yol api.py'da doluydu [lessons ucu] → `/api/hindsight/*`.)
  (GATED→ACTIVE 2026-09-02, operatör kararı "yalnız ilkini başlat": bloktaki "operatör isteğiyle HEMEN sıraya girer" isteği karşılandı; EDG-067 kıyas/hüküm ölçümü ingest bitişini beklemeye DEVAM eder — sayfa inşası ondan bağımsız.)
  (İNGEST ÖNE ÇEKİLDİ 2026-09-01 16:25Z, operatör kararı ["şimdi yapabiliriz"]: 20:05Z transient timer söküldü, koşum elle başlatıldı [214 dosya, kaldığı-yerden ilerleme]; sahiplik düzeltmesi root→ubuntu gerekti [ilk deneme PermissionError]. Kıyas+hüküm ingest bitince ilk uygun pencerede — ardından bu kalem operatör isteğiyle HEMEN sıraya girer.)
  What: Kapı sayfası (TSK-090) deseninin Hindsight eşi — pano'da AYRI sayfa, bizim tasarım dilimizle: bank'ler (bot-başına) · bellek listesi/curation (fact/observation, kaynak-alıntılı — "hatırlıyorum sanma" ilkesinin görünür hali) · operasyon durumu (retain/consolidation kuyruğu, başarısızlar) · kota/LLM telemetrisi (retain+consolidation çağrı hacmi — ana-model kararının günlük ölçümü) · Memory Defense olayları. Veri yolu: tarayıcı 8888/9999'a ASLA gitmez — api.py salt-okunur vekil (`/api/hindsight/*`: loopback 8888; ad ruling'i 2026-09-02 — `/api/memory` lessons ucuyla doluydu), pano token'ıyla. CP UI (9999) tünelli geçici araç; sayfa olgunlaşınca kapatma kararı operatöre sunulur. Konsolidasyon kuralı Kapı sayfasıyla aynı: hafıza göstergeleri YALNIZ bu sayfada.
  Why: operatör talimatı 2026-09-01: "hindsight-dashboard bizim kendi UI'ımıza birebir ayrı bir sayfa olarak aktarılmalı". Yasa 6: retain/consolidation telemetrisi doğduğu gün okuyucusuyla doğar (autoRetain açık + ana-model kararı sonrası kota görünürlüğü şart).
  Ref: TSK-060 · TSK-090 (desen) · Hindsight derin taraması 2026-09-01 (üç bölge).

- **[TSK-090] Kapı sayfası — pano'da APISIX'in tam yüzeyi** — status: DONE(2026-09-01·4b7f92d: v1 canlıda, 4 bölüm dolu veriyle; ayrıntı gövdedeki DONE notunda) · born: 2026-09-01 · owner: rol1 · size: M · trigger: —
  (KAPI AÇILDI 2026-09-01 akşam: TSK-089 Faz 1 indi [kurulum + içerik-smoke + NOUS çevirisi]; operatör "bunları da sıraya almamız lazım" — serbest sıraya alındı.)
  (DONE 2026-09-01 gece: v1 canlıda — `/api/gateway` vekili [v361, 27 çivi + sızıntı duvarı] + pano "Kapı" sayfası [4 bölüm, üç-durum ayrık; fazlar plugin-imzasından türetilir, sabit metin değil]. SDD zinciri: 2 görev + dal-sonu incelemesi [B1 faz-çipi düzeltmesi] + tam suite [8746 yeşil; v323 tek-satır düzeltme delta-yeşil] + dağıtım 4b7f92d. What'taki olay şeridi / consumer-kota / SSL bölümleri v1-DIŞI: besleyen APISIX fazları [2-4] kurulunca kendi tetikleriyle gelir — sayfa o fazları bugün 'bekliyor' rozetiyle gösteriyor. Açık kalem: A1'de `.env-apisix` okuma izni [setfacl] operatörde; verilene dek sayfanın admin bacağı dürüstçe 'okunamadı' der.)
  What: pano'da AYRI sayfa, bizim tasarım dilimizle: rotalar (LLM zincir görünümü: öncelik/aktif model) · upstream'ler+sağlık · consumer'lar+kota kullanımı · plugin konfigleri (sırlar $ENV referansı olarak, değer asla) · SSL (Faz 3'te) · METRİKLER (gömülü dashboard'da OLMAYAN katman: sağlayıcı-başına çağrı/hata/gecikme, kota kalanları, zincir-düşüş sayısı, 402≠429 ayrık sayım, devre-kesici durumu) · olay şeridi (file/http-logger beslemesi). Veri yolu: tarayıcı 9180'e ASLA gitmez — api.py salt-okunur vekil `/api/gateway/*` (Admin API loopback + prometheus 127.0.0.1:9091 + Control API /v1/healthcheck), pano token'ıyla; admin anahtarı tarayıcıya inmez. KONSOLİDASYON KURALI (operatör 2026-09-01): kapı arkasındaki her servisin sağlık/kota/trafik göstergesi YALNIZ bu sayfada yaşar (FMP kota göstergeleri, LLM çağrı istatistikleri buraya taşınır); TSK-086 systemd/host katmanında kalır. v1 SALT-OKUNUR + "kaynağı repo'da aç" bağı; yazma yolu GitOps'ta (UI-üzerinden yazma ayrı operatör kararı). Gömülü `/ui/` tünelli geçici araç olarak yaşar (TSK-089 revizyonu 2026-09-01); kalıcı hakikat yüzeyi BU sayfa — sayfa olgunlaşınca gömülü UI kapatma kararı operatöre sunulur.
  Why: operatör talimatı 2026-09-01: "full APISIX dashboard'unun kapsadığı kısımlar UI'da ayrı sayfa olarak, bizim arayüze uygun aktarılsın; denk gelen kısımlar yalnız bu sayfada gösterilsin". Gömülü dashboard (3.13+) yalnız konfig-CRUD taşır, metrik hiç taşımaz — bu sayfa onun üst kümesi. Yasa 6: kapının her metriği doğduğu gün okuyucusuyla doğar.
  Ref: TSK-089 · TSK-086 (kesişim: infra sayfası host katmanında kalır) · tasarım kararı "taşıma değil benimseme".
(Araya not: E·tahta borçlarından haftada 1-2 — süregelen bakım pratiği, ayrı kalem değil.)

**F'DEN PLANA ALINANLAR** (operatör 2026-08-31 akşam: "FINVIZ/FMP/QC üçlüsü hariç diğerlerini konsolide plana al" — üçlü + delist-kaynak para-kararları MASADA KALDI):

- (① B-AJAN-GIT PATH-shim/wrapper aracı: bkz. **TSK-050** — beyaz listeyi araçla zorlar; küçük araç dalgası, araya-kalem sınıfı.)

- (② ana-beyin SOUL.md+config.yaml paketi: bkz. **TSK-009** — hazırlık+koşum bloğu Rol-1'den, koşum operatörden [bot-kurulum emsali 2026-08-31]; Ajan-A dağıtımından sonraki ilk pencere.)

- (④ olarak numaralanan bu kalem yukarıda TSK-064'tür.)

- (⑤ → **TSK-065**: sıranın sonuna taşındı — paralel-şerit birleştirmesi 2026-09-01; TSK-062'nin ardında koşar.)

- (⑥ TICK-ARŞİV pilotu: bkz. **TSK-056** — yukarıda tam gövdesiyle yaşar; bu madde F'DEN PLANA ALINANLAR listesindeki ikinci anılışıdır.)

**SIRA TARİHÇESİ (önceki başlık paragrafı ve revizyon notu — aynen):**

_**İCRA SIRASI** — sıra icra sırasıdır, kopya değil; her kalem şema kimliğini taşır (rev. 2026-08-31 akşamdan devralındı, göç 2026-09-01 gece standart şemaya çevirdi — GERÇEKLİK KONTROLÜ ile:_

- (SIRA REVİZYONU 2026-09-01, operatör: "konsolide planın sıralaması son değişikliklerle güncellenmeli" — kapı+hafıza hattı [TSK-091/089/090] Hindsight hattının [TSK-060] hemen ardına alındı; iki hat birbirinden bağımsız, TSK-089'un tetiği ayrıca operatör "kur" izni.)

**TRİYAJ KURALI (2026-08-17, §3'ün düzyazı kalemleri bu kurala göre taşındı — ezberden değil):**
`H1` = ön-kayıtlı **kart** ya da **tasarım belgesi** VAR · `H0` = ikisi de YOK (fikir/teşhis
aşamasında) · `H6 ✅` = kapandı ve kanıtı §7'de yazılı · `BLOKE`/`ASKIDA` = aşama değil **dik
durum**. Aciliyet aşama DEĞİLDİR: acil ama tasarımsız bir kalem yine H0'dır.

> ## ⚑ 2026-08-30 BAKIM TURU — TAHTA BANNER'LA DEĞİL TAŞIMAYLA TEMİZLENDİ
>
> Bu bölümün üstünde bugüne dek **üst üste binmiş dört düzeltme bloğu** duruyordu (2026-08-13 ·
> 08-22 · 08-23 · 08-24) ve hiçbiri satırlara İŞLENMEMİŞTİ: her tur "aşağıdaki N satır bayat"
> diye yeni bir banner ekledi, kapalı satır tahtada kaldı, bir sonraki tur banner'ı da okumak
> zorunda kaldı. 2026-08-24 denetimi bunun adını koydu — *"tahtanın toplam bakım borcu 27
> satır"* — ve bedeli ölçtü: **o gece iki ajan turu zaten kapalı kalemlere gitti.** Altı gün
> boyunca borç ödenmedi. Bu tur banner EKLEMEDİ: satırları TAŞIDI.
>
> **YAPILAN (hepsi taşıma, SİLME YOK — gövdeler `§8.T`/`§8.O`/`§8.H`'de tam metniyle):**
> §2'den **49 tablo satırı** (H1 6 · H2 2 · H0 16 · DİK DURUM 5 · H6'nın 20'si) ve **iki bayat
> banner bloğu** (2026-08-24 doğrulama turu + aynı günün gece karşıt-doğrulama notu) çıktı ·
> §5'ten **iki kova gövdesi** (KOVA 1 ve KOVA 2 — altı kalemin altısı da kapalıydı) ·
> §4'ten **üç kapanmış öneri**. Yerinde kalan her açık satır artık **rozet taşıyor**
> (`AÇIK`/`BLOKE`/`ASKIDA`) — "işaretsiz" ile "açık" bu tura kadar aynı görünüyordu.
>
> **ÖLÇÜM — ARAÇ DEPONUN KENDİ AYRIŞTIRICISI** (`meridian/api.py::_roadmap_ayristir`, yani
> `/api/roadmap`'in tükettiği kod; ayrı bir sayaç YAZILMADI — tek-kaynak yasası):
>
> | ölçüm | satır | kapalı | açık | bloke | askıda | işaretsiz | çok-işaretli |
> |---|---|---|---|---|---|---|---|
> | **§2 açık bölümler** (H0/H1/H2/DİK) — ÖNCE | 48 | 25 | 0 | 1 | 3 | 18 | 1 |
> | **§2 açık bölümler** — SONRA | 25 | 0 | 15 | 5 | 4 | 0 | 1 |
> | §2'nin tamamı (H6 dahil) — ÖNCE | 68 | 30 | 0 | 1 | 3 | 33 | 1 |
> | §2'nin tamamı — SONRA | 25 | 0 | 15 | 5 | 4 | 0 | 1 |
>
> Belgenin tamamı — **tablo satırı** 166 → 188 (işaretsiz 113 → 101; açık 0 → 23) · **düzyazı maddesi** 421 → 425 · satır 4626 → 4793 (§7 girişi dahil).
>
> **BEDEL ÖLÇÜMÜ (bedel yasası — kazanç ölçüldüyse kayıp da ölçülür):** bu tur belgeyi KISALTMADI, 167 satır UZATTI: taşınan metin tam olarak korundu (kayıp 0 satır — betiğin kapısı bunu doğruluyor), üstüne rozetler ve kanıt blokları eklendi. Kazanılan şey uzunluk değil **okunabilirlik**: tahtaya bakan bir tur artık 25 satır okuyor, 68 değil — ve okuduğu 25 satırın hiçbiri kapalı değil. Kaybedilen: kapanmış kalemin gerekçesi artık tahtada DEĞİL, `§8.T`'de — yani "neden kapandı" sorusu bir sıçrama uzakta.
>
> **BİLİNEN KALINTI (gizlenmiyor):** §2'de **bir** satır hâlâ çok-işaretli — `M2` (açık) ile `M7` (kapalı) aynı satırda yaşıyor ve tahtanın kendi kuralı *"iki aşamadaysa kalem İKİYE bölünür"* der. Bölmek satır metnini DEĞİŞTİRMEK demekti; bu tur kendini **taşımayla** sınırladı (metne dokunmadan). Bölme işi açık kalem olarak `§8.T` girişinde adıyla duruyor.
>
> **ÖLÇÜLEMEYEN — ve neden (uydurma yasağı):** bu tur **cloud klonunda** koştu; `state/` yereldir
> ve canlı A1 defteri okunamaz. Dolayısıyla "canlıda etkin mi" sorusu taşıyan kalemler
> (`B-DASH-CRED` faz-2 · `B-OCI-BUCKET` replica · `B-NOUS-BEYIN` danışma yolu) **depo tarafından**
> doğrulandı, canlı tarafı DOĞRULANMADI ve öyle işaretlendi. Tam suite de koşmadı (Rol-1 kapısı).
>
> **KURAL (bu turdan itibaren çivili — `tests/test_tahta_hijyeni_v337.py`):** §2'nin
> H0/H1/H2/DİK DURUM tablolarında `durum=kapali` ayrıştırılan satır BULUNAMAZ. Kapanan satır
> AYNI turda `§8.T`'ye taşınır. Banner ekleyerek kapatma artık kırmızı verir.

#### H1 — TASARIM VAR, ölçüm/uygulama bekliyor — **10 açık** (2026-08-31 gece: +2 — skill-görüş dalgası · öğrenme-kilidi çifti; kapananlar `§8.T`/C-D-J'de)

| id | name | status | owner | size | trigger |
|---|---|---|---|---|---|
| TSK-069 | EDG-2026-042 K1/K3 bandı — Ö-55 friksiyon-koşullu limit sınaması (WP: WP1) | GATED(EDG-042 gerçek-friksiyon bandının dolması, ~4 hafta) | rol1 | S | EDG-042 bandının gerçek-friksiyon eşiğe dolması (B4 kararı buna bağlı) |
| TSK-061 | Hermes bot roster programı — Faz 5+ rol seçimi (WP: WP12) | GATED(canlı-döngü ölçümünden bot değer-kanıtı birikmesi) | rol1 | M | canlı-döngü ölçümü (Faz 3 usulüyle) |
| TSK-012 | pano 'Ajan' bölümü — ajan iletişim yüzeyi (dalga-B: sohbet) (WP: WP12) | GATED(EDG-062 inişinden sonra — o gün tahtaya satır açılır) | rol1 | M | EDG-062 inişi |
| TSK-058 | Skill-görüş dalgası — EDG-019 uygulaması + EDG-063 LLM-üretici sınıfı (WP: WP7) | QUEUED (trigger karşılandı: Ajan-A dalgası TSK-012 kapandı) | rol1 | M | — |
| TSK-062 | Öğrenme kilidi çifti — EDG-064 duvar yeniden-sınama + EDG-058 K-enflasyonu ölçümü (WP: WP3) | GATED(geri-dolum programının tamamlanması — learn program boyunca KAPALI) | rol1 | M | geri-dolum programının kapanışı (2026-09-01 gece operatör onayı: learn açılana dek ertelendi) |
| TSK-070 | F8 pano durum-sözlüğü (WP: WP8) | QUEUED | rol1 | M | — |
| TSK-071 | Ö-54 gerçek friksiyon tahmini (n=4'ten çıkış) (WP: WP1) | GATED(K1 örneklem eşiğinin dolması — haftalık otomatik koşum `edg042-friksiyon-haftalik`) | rol1 | M | K1 n≥30 eşiği (takvimli otomatik koşum) |
| TSK-072 | EXE-2026-003 — gölge kapsam / planlı kol (WP: WP3) | GATED(örneklem penceresinin 2/20'den dolması) | rol1 | S | pencere dolması |
| TSK-059 | EXE-2026-009 P-2 — hakem anahtarı `ts` geçişi (WP: WP1) | GATED(EDG-062(b) inişinden sonra) | rol1 | M | EDG-062(b) inişi |

  Not (TSK-069): **BLOKE:** `EDG-2026-042` K1/K3 bandı (türev kalem — bağımsız iş içermez) · **`Ö-55` friksiyon-koşullu limit sınaması** — artefakt: `EDG-2026-043-friksiyon-kosullu-limit` — kapı durumu: 🆕 **KART ÖN-KAYITLI 2026-08-22** (B4 kararının C bacağı; EDG-040 ACİL kaleminin (b) bacağına ilk somut adım). Altı hücre (K=6): slip {15,25,35} × dolum {A,B}, cap=0,01 silahlı; kapalı-kapı hücreleri edg040'ın DONMUŞ kanıtından (yeniden koşmak kill). OKUMA KURALI DONUK: hüküm yalnız EDG-042'nin gerçek-friksiyon bandına düşen hücreden okunur — bant gelmeden (~4 hafta) B4 yeniden açılamaz. Ölçüm ~75 dk, hemen ya da bantla birlikte koşulabilir (operatör tercihi) → **ÖLÇÜLDÜ (aynı gün, K=6 harcandı): altı CI de 0-içi.** A kolu hep negatif (−7,3k/−5,8k/−1,3k) · B kolu hep pozitif NOKTA (+4,0k/+3,8k/+2,3k; slip15_B altı hücrenin tek kârlısı +895) — işaret-dönüşü deseni görünüyor ama HİÇBİRİ ayrışmıyor. HÜKÜM ASKIDA (okuma kuralı): EDG-042 bandı ~4 haftada; muhtemel okuma "ayrışmadı → B4 kapalı kalır"
  Not (TSK-061): **AÇIK** (PROGRAM: Faz 1-4 repo tarafında TAMAM — skill+karar görevi · `@sef` · `@bekci` · `@karne`; canlıda HİÇBİRİ etkin değil) · **hermes bot roster programı** **[2026-08-31 EKLENDİ: dört fazı inmiş koşan programın tahtada satırı YOKTU — kayıtları yalnız §7'de]** — artefakt: spec `docs/superpowers/specs/2026-08-27-bot-roster-design.md` · fazlar `docs/superpowers/plans/` (faz1-bot-roster · faz2-sef · faz3-bekci · faz4-karne) · profiller `deploy/hermes/profiles/{sef,bekci,karne}` — kapı durumu: İKİ BACAK: (1) ✅ **CANLI ETKİNLEŞTİRME TAMAM 2026-08-31** — operatör kurulum bloğunu koştu, Rol-1 kanıtı topladı: üç birim kurulu, üç timer active (bekci 10:01 · brifing 22:02 · karne Cmt 16:04 UTC), üç test-ateşleme Result=success/status=0, üçünde de sıralama/sunum=llm ve teslim damgalı (journal 09:29-09:31). İLK KARNE İNDİ: goal.yaml dört hükmü — min_sharpe KALDI (0,646<1,2) · max_drawdown GEÇTİ (%11,68≤%16) · failure_below GEÇTİ. @bekci ilk taramada 2 YENİ DURAN buldu (reconcile_atlandi 157 sa · mirror_cancel_sinif_dokumu 109 sa — triyaj notu §7'de). (2) **Faz 5+ rol seçimi ÖLÇÜM-ÖNCE** — kalan roster `@kod` · `@ayna`; `@nobet` ELENDİ (ikinci bot token'ı sır ister, §7 2026-08-29), `@hipotez` BLOKE (merdiven duvarı yeniden sınanana dek — kart + operatör kararı ister, EDG-2026-058 bağı). Seçim Faz 3 usulüyle canlı-döngü ölçümünden gelir, defterden değil
  Not (TSK-012): **AÇIK** (dalga-A kapanışı `§8.T`de TAM metniyle — taşındı 2026-08-31, v337 tahta kuralı; AYNI GÜN MESAJLAŞMA GÖÇÜ de indi: dört sekme tek gramerde, commit 5fa9d39, 59 çivi + tarayıcı doğrulaması — dalga-B kalanı: iki yönlü sohbet + ⌘K kanonik adres devri) · **Ajan iletişim yüzeyi — pano 'Ajan' bölümü** — artefakt: §4 havuz girdisi (tasarım eskizi + kapsam kararı) · veri kaynağı ölçüldü: profil `state.db` sessions/messages/session_model_usage — kapı durumu: İKİ DALGA: **(A)** salt-okunur zaman-çizelgesi — profil state.db + `*_teslim` olayları + son_brifing arşivi tek akışta, `/api/ajanlar` + pano yüzeyi; **(B)** iki yönlü sohbet — pano→API→hermes tek-atışlık, AYNI duruşla (guard kancası + kapalı araç takımları + safe-root + pano token'ı; §9.4 üçlüsü sohbet yolunda da çivilenir). Muhataplar: sef · bekci · karne · ana hermes beyni (her biri kendi duruşuyla). **AYNI DALGADA `ops/filo.py`** (2026-08-31 MCP değerlendirmesinin hükmü): komut-satırı sözleşmeli filo aracı — `durum · journal · test-atesle · profil-guncelle · oturumlar` alt komutları; bugünkü elle-ssh kalıplarını tek yerde toplar, ölçülmüş tuzakları (profile-update etkileşimli onayının sahte-başarısı) çözülmüş taşır. Dalga-A ile aynı veri yüzeyi (state.db + journal) — birlikte iner
  Not (TSK-058): **AÇIK** (KARARLI: operatör 2026-08-31 — 'beyan-only skill'lerin LLM ikinci görüşünü de yapalım'; icra Ajan-A dalgasından SONRA) · **skill-görüş dalgası: EDG-019 uygulaması + EDG-063 LLM-üretici sınıfı** — artefakt: kart `EDG-2026-019` (registered — defter+iki çözücülü yüzey: aday-siralayici→rank-IC, cikis→exit_efficiency) · kart `EDG-2026-063` (ön-kayıt: beyan-only SKILL.md'ler LLM'le AYNI deftere gölge görüş yazar, aynı çözücüyle puanlanır) — kapı durumu: TEK DALGA İKİ KART: altyapıyı 019 kurar, 063 LLM-üretici sınıfını AYRI kartla açar (019 evreni 'deterministik/LLM-çağırmayan' — evren yerinde genişletilemez). Donuk sınırlar 063 kartında: yalnız GÖLGE · şema-uyumsuz LLM çıktısı olculemedi · LLM düşerse üretici SUSAR · t-öncesi veri fence. İlk kez ölçülebilir olan soru: LLM görüşü deterministikten iyi mi (aynı çözücü, aynı defter)
  Not (TSK-062): **AÇIK** (KARARLI: operatör 2026-08-31 — 'merdiven duvarını yeniden sınayacak kartı sıraya al, burayı optimize etmemiz lazım') · **öğrenme kilidi çifti: EDG-064 duvar yeniden-sınama + EDG-058 K-enflasyonu ölçümü** — artefakt: kart `EDG-2026-064` (ön-kayıt: kademe grid ×1/×2/×4, %80-tavan eşiği, yenileme-politikası çıktısı, yalnız A1 seans-dışı, record_session=False) · kart `EDG-2026-058` (kayıtlı, HİÇ ölçülmemiş — aynı pencerede koşulur) — kapı durumu: Kuraklığın ölçülmüş iki kilidi birlikte: duvar süresiz ölçüm (93+ tur kilitli) + K'ya bedava-önbellek sondalarının sayılması (eşik 0,980→0,995). DÜRÜST VAAT: cleared değil KAPSAMA + kilidin süresizliğinin bitmesi; parametre kararı kanıtla operatöre. İCRA: PARALEL ŞERİT — ilk uygun seans-dışı A1 penceresi (diğer dalgaları bloklamaz; koşum çoğunlukla bekleme)
  Not (TSK-070): **AÇIK** (KISMEN: tasarım belgesi + `durum_sozlugu.py` indi; A1-A8 soruları ve pano bacağı açık) · **F8 durum sözlüğü** — artefakt: `docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md` — kapı durumu: 🆕 **H0→H1: TASARIM BELGESİ YAZILDI (2026-08-22, ajan ölçtü Rol-1 inceledi).** "15 bekçi" iddiası BAYATTI — ölçüm: EXPECTED kadans 17 · bütünlük 8 · alarm-geçişli 8 · rapor ailesi 19. 16 tutarsızlık 4 sınıfta (öğrenme mandalı 4 yazım · acil durdurma 5+ ad · hüküm alanı 5 ad · açıklama 7 ad/2 dil). **4 YASA-6 adayı:** goal_failure/kitap_damga/mutabakat_tazelik/onayli_gonderim raporları hiçbir uçtan servis edilmiyor + codelaw bu sınıfa YAPISAL KÖR (fonksiyon-düzeyi). **[2026-08-23 GÜNCEL — "hiçbir uçtan servis edilmiyor" BAYATLADI: 4 rapor v261'de bağlandı (`meridian/api.py:3390-3393`, 987b552; pano tabanı 18→20, e73241f); kalan yalnız kanonik sözlük]** Sıradaki: kanonik sözlük uygulaması (kod işi, ayrı tur)
  Not (TSK-071): **AÇIK** (TAKVİM: haftalık `edg042-friksiyon-haftalik`; koşum #2 2026-08-29 eşiği DOLDURMADI, sıradaki 5 Eylül) · **`Ö-54` gerçek friksiyon tahmini (n=4'ten çıkış)** — artefakt: `EDG-2026-042-gercek-friksiyon-tahmini` — kapı durumu: 🆕 **KART ÖN-KAYITLI 2026-08-22** (EDG-040 ACİL kaleminin (a) bacağı). Kanonik ölçüt EDG-038'den AYNEN (D1 konsolide açılış; E2'de KAYITLI alan — PIT, koşum günü tarihçe çekilmez). Üç kova (K=3): giriş · çıkış-hedef · çıkış-stop — karıştırılamaz. Örneklem eşikleri DONUK: K1 n≥30 & ≥10 seans, K2/K3 n≥15 & ≥6 seans; ALTINDA çıktı BETİMLEYİCİ (EDG-037 damga biçimi aynen). Karar kuralı EDG-040 başabaşına [5-15] karşı: CI-alt>15 → paket negatif işliyor sinyali · CI bandı kesiyor → hüküm yok, ölçüm sürer · CI-üst<5 → model muhafazakâr şerhi. SAYIM (değer bakılmadan): bugün K1=13 · K2+K3=5 → kart BUGÜN hüküm üretemez ve bunu beyan eder; K1 eşiği kabaca +4-6 hafta. Ö-52 bağı kill'de: teyitsiz satırın dolumu kıyasa giremez→ **BETİMLEYİCİ ARA-KOŞUM YAPILDI (aynı gün, operatör istedi — hüküm YOK):** K1 n=13/4 seans: **medyan +15,0 bps** (model 5'in üç katı, başabaş bandının [5-15] ÜST SINIRINDA) · p25/p75 −43/+41 · min/maks −131/+327 (dağılım vahşi, EDG-038'in 15↔134'üyle tutarlı) · en büyük seans %38,5 (<%40 şerh eşiği). K2/K3: beş aday satırın BEŞİ de `broker_teyit` damgasız → kill kriteri hepsini olculemedi'ye düşürdü (bps hiç hesaplanmadı) — damga ilk reconcile turunda basılınca ölçülebilirler. Damgalar aynen: "ÖLÇÜLEMEDİ (n<eşik) — betimleyici". ⏰ **OTOMATİK TAKVİM (2026-08-22):** her Cumartesi ~10:29 zamanlanmış görev `edg042-friksiyon-haftalik` — betimleyici tekrar + eşik dolan kovada hükümlü koşum OTOMATİK (CI-alt>15 çıkarsa ACİL kaleme 'rakamla doğrulandı' düşer, operatör penceresi raporlanır). YAN KAZANÇ: ajan K2/K3 işaret çelişkisini hücreler hiç ölçülmeden yakaladı, kart ölçüm-öncesi düzeltmeyle netleşti → **İLK OTOMATİK FIRE KOŞTU 2026-08-22 15:05Z** (`edg042_kosum_2026-08-22/`, snapshot sha 155a0da2…): üç kovada da EŞİK DOLMADI → hükümlü koşum tetiklenmedi, CI hesaplanmadı, karar kuralı uygulanmadı, `status: measuring` kalır. K1 n=13/4 seans (medyan +15,017 · p25/p75 −43,0/+40,8 · seans payı %38,5), K2/K3 ölçülebilen n=0 (beş adayın beşi damgasız). **ÖNCEKİ KOŞUMA GÖRE DEĞİŞİM SIFIR** — snapshot ara-koşumunkiyle bayt-özdeş (Cumartesi, arada seans/reconcile yok); bu takvimin çalıştığının kanıtı, yeni kanıt DEĞİL. İlk anlamlı tekrar **2026-08-29**. ⚠️ REÇETE DÜZELTİLDİ (Rol-1, ölçümden önce, eşik DEĞİŞMEDİ): donmuş `olcum.py` K2/K3 işareti kartın DÜZELTME formülüyle çelişiyordu (`bps_delta` → `−bps_delta`); MADDİ hataydı — LLY T00103'te LEHTE dolumu '+120 bps aleyhte' yazıp hükmü ters çevirirdi. Teyitli satır 0 iken düzeltildi, sentetik satırla sınandı, gerçek çıktı değişmedi. Donuk reçete artık `edg042_kosum_2026-08-22/`. YENİ AÇIK KALEM: kartın işaret cümlesi yalnız LONG için yazılı (bugün 8/8 long) — short satır çıkarsa reçete kartsız genişletilemez → **AÇIK KALEM KAPANDI 2026-08-24** (kart bloğu `r2_short_isaret_sozlesmesi_2026_08_24`; reçete R2 = `edg042_recete_short_2026-08-24/`, GÜNCEL DONUK REÇETE İŞARETÇİSİ) → 🔁 **HAFTALIK KOŞUM #2 · İLK ANLAMLI TEKRAR 2026-08-29 15:51Z** (`edg042_kosum_2026-08-29/`, snapshot sha 3a1f06bf…, R2 reçetesiyle — kart görev metnini yendi): üç kovada da EŞİK YİNE DOLMADI → hükümlü koşum tetiklenmedi, CI yok, karar kuralı uygulanmadı, `status: measuring`. **K1 n=13→17 / seans 4→7** (medyan **+15,0 → +29,8 bps** · p25/p75 −9,8/+87,1 · min/maks −130,7/+327,5 · en büyük seans %38,5→%29,4): yeni dört satırın DÖRDÜ DE pozitif ve büyük (DE +80,7 · PANW +87,1 · ECL +175,1 · CRM +245,0). **ÇIKIŞ KOVALARI İLK KEZ ÖLÇÜLEBİLİR** — `broker_teyit` damgası basıldı, afp-dolu 10 satırın 10'u teyitli (olculemedi n=0), Ö-52 dağıtımı öngörüldüğü gibi çalıştı: **K2 hedef n=6/2 seans medyan −4,2** · **K3 stop n=4/3 seans medyan +0,9** — ikisinde de kill #7 tek-seans ŞERHİ ZORUNLU (%66,7 / %50,0). BETİMLEYİCİ GÖZLEM (hüküm DEĞİL): giriş ile çıkış ZIT yönde — K1 medyanı başabaş bandının [5-15] ÜSTÜNDE, K2/K3 medyanları modelin (5) ALTINDA; friksiyon ağırlığı GİRİŞ bacağında toplanıyor *gibi görünüyor*, ama n=6 ve n=4 ile bu cümle KURULAMAZ. EŞİĞE KABA MESAFE (izdüşüm, ölçüm değil): K1 ~3-4 hafta (bağlayıcı: n, 13 eksik) [DÜZELTME 2026-08-31: BAYAT — P-3/AYRIK sonrası hüküm kolu yalnız giris_1345, ayrık eşik ~14 hf (bant 4,9-14); kart p3_karar_ayrik_ts_2026_08_31] · K2 ~2-3 hafta (bağlayıcı: seans) · K3 ~3 hafta — çıkış izdüşümleri ZAYIF dayanaklı, bu haftanın 10 satırı birikmiş arşivin damgayla açılmasından geldi, haftalık akıştan değil ⛔ **AÇIK KALEM P-3 (2026-08-29, kart bloğu `acik_kalem_p3_k1_karisik_ornekem_2026_08_29`):** medyan yükselişi kovalanınca K1'in İKİ İCRA MEKANİZMASINI tek medyanda topladığı çıktı — 13 satır EOD-GTC (eski), 2 satır gerçek 13:45 penceresi, 2 satır eski yoldan gelip yanlış damgalanmış (EXE-009 P-1). Kartın kill#5'i kovalar ARASI karışımı yasaklar, kova İÇİ karışımın kuralı YOK; üstelik payda 09:30 resmî açılışta DONUK olduğu için 1345 satırlarının bps'i "friksiyon + 15 dk sürüklenme"dir. **Karar eşik dolmadan verilmeli** (K1 n=17/30, ~3-4 hafta [izdüşüm 2026-08-31'de çürütüldü — bkz. p3 bloğu]): eşik dolduktan sonra kural koymak sayıya bakarak kural seçmektir. Üç yol kartta sunuldu (K1'i ayır / pooled+zorunlu şerh / kaydırma-öncesini dondur); seçilmezse bugünkü hâl sürer. Ara tedbir: haftalık rapor 1330/1345/damgasız kırılımını ve kontaminasyon sayısını beyan eder → ✅ **P-3 KARAR VERİLDİ 2026-08-31 (operatör): AYRIK, `ts` anahtarı, ara işaret YOK** — kart bloğu `p3_karar_ayrik_ts_2026_08_31` · reçete `edg042_recete_ayrik_2026-08-31/` (GÜNCEL DONUK REÇETE İŞARETÇİSİ) · KARAR belgesi docs/KARAR-P3-K1-AYRIK-TS-2026-08-31.md · haftalık görev metni revize (bitiş: ulaşabilen-üç-kova; giris_once kalıcı taban) → 🔁 **KOŞUM #3 · R3/AYRIK İLK RESMÎ KOŞUM 2026-08-31** (operatör: beklemeye gerek yok; Rol-1 koştu): dört kova eşik altında, betimleyici, DEĞİŞİM SIFIR (08-28'den beri seans yok — takvim kanıtı); giris_once n=15/+16,1 donuk taban · giris_1345 n=2/+210,1 · K2 n=6/−4,2 · K3 n=4/+0,9 · hakem orneklem_birikimde (`edg042_kosum_2026-08-31/`)
  Not (TSK-072): **AÇIK** (TAKVİM: `EXE-2026-003` `measuring` — pencere doluyor) · gölge kapsam / planlı kol — artefakt: `EXE-2026-003-golge-planli-kol` — kapı durumu: **measuring (2026-08-22):** ilk koşum yapıldı — pencere 2/20 dolmadı ama gözlenen her şey olumlu (5/5 dolum yazıldı · silahlı kol bayt-düzeyi etkilenmemiş · 002 hattına sızıntı 0 · kill tetiklenmedi). Yan teşhis: gölge×cf eşleşmezliğinin 12/13'ü cf_open'da AÇIK bekliyor — boru-hattı gecikmesi, kapsam deliği değil. Pencere dolunca aynı betik yeniden koşulur
  Not (TSK-073): **KAPANDI 2026-09-03 13:34Z (4fdde26): EDG-2026-019 resmî koşum #1 measured_partial — terfi adayları exhaustion-hammer (sıralayıcı) + vcp (çıkış), emeklilik işareti exhaustion-hammer (çıkış, 1/3); operatör kararı Masa'da.** · **AÇIK** (yalnız `24b`: SOUL kilidi canlıda doğrulandı, ETKİ ölçümü YOK — kart `registered`) · `24b-24d` skill görüş defteri **[2026-08-24: fiilen yalnız `24b` — `24c` ve `24d` KAPANDI-BAYAT, aşağıda]** — artefakt: `EDG-2026-019-skill-gorus-defteri` — kapı durumu: kart ön-kayıtlı · 24b SOUL kilidi açıldı ama **HİÇ SINANMADI** **[2026-08-23 GÜNCEL — kısmi bayat: kilit CANLIDA DOĞRULANDI 08-22 (sha birebir, kilit cümlesi yerinde; `research/olcumler/edg019_24b_sinama_2026-08-22/`); ETKİ ölçümü hâlâ yok — kart `registered`]** · ~~24c~~ **[2026-08-24 KAPANDI-BAYAT: "788/385/1" penceresi 08-06..08-13 bir RETRY FIRTINASIYDI; yol 08-14'te dirildi (142/142 dolu), son 7g 9 çağrı sağlıklı düşük tempo, görüş aynı-gün damgalanıyor ve danışman bu yol üzerinden 2026-08-14'te TERFİ ETTİ (`docs/ELEME-WP7-2026-08-23.md` §1)]** · ~~24d~~ **[2026-08-24 KAPANDI-BAYAT: tasarımın üç öncülü de yanlış — terfi tabanı PİLOTSUZ aşıldı (`n_pairs=100`, `promoted=true` 08-14), DOLGU artık tek yol değil ve `llm_veto_strip` 9 günde 0 kez ateşlendi, iki pilot skill'i canlı ön-yükleme listesinde bile yok; kalan meşru soru 24b ETKİ ölçümüne devredildi (`docs/ELEME-WP7-2026-08-23.md` §2)]**
  Not (TSK-059): **AÇIK** · `EXE-2026-009` **P-2** — hakem anahtarı `ts` geçişi (pencere damgası ailesinin kalan bacağı) **[2026-08-30 EKLENDİ; 2026-08-31 satır P-2'ye daraltıldı — P-3 bacağının kapanış kaydı Ö-54 satırında + `p3_karar_ayrik_ts_2026_08_31`]** — artefakt: kart `EXE-2026-009` bloğu `acik_kalemler_2026_08_29` + `docs/HAZIRLIK-P3-K1-KARISIK-ORNEKLEM-2026-08-30.md` — kapı durumu: **DEVRALINDI 2026-08-31** (operatör, 85-aktarımı; birebir: "bunların hepsini main'e devret main yapsın"): BLOKE kalktı, yol ÖLÇÜLMÜŞ — hakem `pencere_altbant.py` anahtarı `ts`ye geçerse kontrol kolu n=2→15 (eşik 10 GEÇER), tedavi kolu ~4 hafta (0,40 dolum/seans); bugünkü `pencere` anahtarıyla valf İNŞAEN kapalı. Kill#3 ÇERÇEVESİNE dokunur → KARTSIZ YAPILAMAZ: kart revizyonu + bölücü `gonderim_kolu()` `edg042_recete_ayrik_2026-08-31/olcum.py`den İTHAL (ikinci kopya yazılmaz — tek-kaynak) + görev EK'inin sabit-dizin işaretçisi aynı turda tek-kaynaklaştırılır ([2] emekliliğinin sınıfı; 2026-08-29 koşumunda fiilen aşıldı). SIRA: EDG-062 (b) inişinden sonra. Üçüncü bacak `P-1` 2026-08-30'da kapanmıştır: `90f6cdc` kod + `dcef1c6` dağıtım + `83bc47b` kill#3 istisnası

#### H2 — PLAN VAR, icra bekliyor — **BOŞ** (2026-08-30: iki satırın ikisi de kapalıydı, `§8.T`/E)

_(Bölüm bilerek silinmedi: aşama sırası `H0→H1→H2→H3…` bir sözleşmedir ve boş bir aşama
"kalem yok" demektir, "aşama yok" demek değil.)_

#### H0 — TASARIM ARTEFAKTI YOK (kart-önce açılacaklar) — **9 açık** (2026-09-03 gece: TSK-075/077/080 KAPANDI → `§8.T` "dağıtım #8 kapanış kaydı"; önceki: 12 açık) (2026-08-31: `§7` boşluğu kapandı, satır `§8.T`/I'ya taşındı; kapananlar `§8.T`/F'de) _(2026-08-30 ölçümü)_

| id | name | status | owner | size | trigger |
|---|---|---|---|---|---|
| TSK-074 | `propose_virgin_knob` hayalet-düğme süzgeci (WP: WP3) — operatör 2026-09-03 sabah: KOVA C, kart-önce (C-9); kart EDG-2026-071 yazıldı ve ONAYLANDI 2026-09-03 — 2026-09-04 EDG-071 ÖLÇÜLDÜ (KISMİ): süzgeç zararsız (K2 0/32 yanlış-pozitif, fail-open sessizleşmiyor, PK geçti), tarihsel fayda ölçülemedi (A1 defteri 60 satır, 42'si repo git tarihi öncesi; flagship vaka defterde yok) → OPERATÖR KARARI: Seçenek A kablolaması + canlı hayalet-öneri sayacı, ya da kanıtsız kapalı (commit ec701b3) **OPERATÖR 2026-09-04 13:0xZ: KABLOYA AL — Seçenek A (hayalet_suzgeci hermes.virgin_knobs tek boğazında) + canlı 'süzülen hayalet öneri' sayacı; 2 hafta sonra sayaç okunur, sıfırsa geri alınır. KOVA B dilimi, küçük motor değişikliği, tam suite.** **KABLOLANDI 2026-09-04 7ed0f54 (dağıtım #13): virgin_knobs tek boğazında reflect.hayalet_suzgeci (fail-open), sayaç analytics.learning_scorecard.hayalet_suzulen_n (kablolamadan beri birikimli, kuyruk 15.000 satır beyanlı) → /api/diagnostics → pano Karne satırı; v408; SAYAÇ OKUMA ~2026-09-18 (sıfırsa geri al).** | ACTIVE | rol1 | M | — |
| TSK-069 | (bkz. TSK-069 — EDG-2026-042 K1/K3 bandı; bu satır ACİL C+mb keşfinin kaydı, aynı bant eşiğine bağlı) (WP: WP1) | (bkz. TSK-069) | rol1 | — | — |
| TSK-076 | OPT — parametre-evrim boru hattı (Faz-1 serbest, Faz-2 28d'ye bağımlı) (WP: WP3) — operatör 2026-09-03 sabah: kapalı kalsın, OPT beklesin | GATED(28d/chop-bütçe kapalılığı operatör kararı) | rol1 | L | 28d tıkanıklığının/chop-bütçe kararının çözülmesi |
| TSK-081 | ARSENAL POLİTİKASI (15e giriş) · `15d` PIT-temiz faktör seti · `15c` evren genişletme (askı C6 uzlaştırmasıyla kalktı) (WP: WP11) — B-19 ölçümü 2026-09-03: ARSENAL politikası VAR (15e yarısı DONE), 15d tasarım belgesi var → kart adayı, 15c 044/084'e bağlı beklemede | QUEUED | rol1 | M | — |

  Not (TSK-074): **KABLOLU 2026-09-04 7ed0f54 · CANLI dağıtım #13 20:06Z: `/api/hermes` learning.hayalet_suzulen_n = 0 (kablolama günü, beklenen; okuma ~2026-09-18, sıfırsa geri alınır)** · eski not (2026-08-22, tarihçe): **AÇIK** (HAZIR İŞ · kart-önce: tasarım belgesi var, kart YOK kod YOK) · **`propose_virgin_knob` canlı-params süzgeci** — not/kapı durumu: **H0→H1: TASARIM BELGESİ YAZILDI** (`docs/TASARIM-VIRGIN-KNOB-SUZGECI-2026-08-22.md`). Ölçüldü: süzülmemiş liste ÜÇ yüzeyden tüketiliyor (deterministik havuz · LLM istem bölümü · evidence_pack) — tamirat tek fonksiyon işi DEĞİL; hermes→reflect kenarı zaten var, Ö-48 süzgeci yeniden kullanılabilir (döngüsel bağımlılık yok, ölçüldü). Uygulama kart-önce
  Not (TSK-069): **BLOKE:** `EDG-2026-042` K1/K3 bandı (türev — bağımsız yeni ölçüm GEREKMİYOR, reçete kartta yazılı) · 🔴 **ACİL: C+mb paketi +10 bps ek friksiyonda NEGATİF** (`EDG-2026-040` hükmü) — not/kapı durumu: **KARTIN DONUK KURALI BU KALEMİ AÇTI** ("aksi hâlde hüküm … ROADMAP'e ACİL kalem olarak girer"). Taban slip=5 → **+20.685** · slip=15 → **−3.067** · slip=25 → −13.722 · slip=35 → −25.681; ΔP&L CI'ları ÜÇÜNDE DE sıfırın dışında (CI-üst<0). Başabaş bandı **5-15 bps/bacak** (interpolasyon yok). Hasar FİYAT kaynaklı (n 885→862, seçilim değişmedi). BAĞLAM: gerçek friksiyon hâlâ n=4 TAHMİN (EDG-037 kill#1 ayakta) ama EDG-038 kanonik ölçütü giriş bacağında medyan +29 bps demişti — o doğruysa sistem slip25-35 bandındadır. Dokuz replay hükmündeki §E şerhi artık RAKAMLI. SIRADAKİ İŞ: (b) ✅ **KARTI ÖN-KAYITLI: `EDG-2026-046`** (iki-dünya × iki-seçilim, K=4; yaltaklanan-dünya tuzağı kill'de;
  Not (TSK-076): **AÇIK** · OPT Faz-1 (serbest) · Faz-2 (28d'ye bağımlı) — not/kapı durumu: 
  Not (TSK-078): **KAPANDI 2026-09-03 13:34Z (B-15, 8da5fb5): envanter tamam — #2 ve #4 kapalı, #3 max_drawdown ortamlar-arası AÇIK (canlı bacağı ölçülmedi; küçük takip, yeni kalem yazılmadı).** · **AÇIK** (kalan: 9 çiftin gerekçe envanteri; P0-b · P2 · #11 indi) · `26` değer-eşitliği — **kalan 9 çiftin GEREKÇE ENVANTERİ** — not/kapı durumu: ⚡ **2026-08-21 YENİDEN ÖLÇÜLDÜ, "26 kapısız çift" BAYAT.** Envanter v245'te yapılmış: **13'ü kaynağında zaten kapanmış · 5'i bağlanmış · 9'u bağlanmamış (her biri NEDENİYLE)**. `watchdog.EQUIVALENT_TRUTHS` bugün tam **9 olgu** taşıyor ve `_divergence_hesapla()` ÖLÇÜLDÜ: **ayrık 0 · eşit 7 · beyanlı-ayrı 2 · ölçülemeyen 0** — yani KAPILI taraf SAĞLAM. GERÇEKTEN AÇIK OLAN: bağlanmayan 9 çiftin gerekçeleri tek bir belgede TOPLANMAMIŞ; "her biri nedeniyle" deniyor ama neden nerede yazılı BİLİNMİYOR. Kalem artık "26 kapı kur" değil **"9 gerekçeyi bul, yazılı hâle getir, hâlâ geçerli mi ölç"**→ **YAPILDI (2026-08-22):** `docs/ENVANTER-DEGER-ESITLIGI-2026-08-22.md` — 26 = 12 kaynağında kapanmış + 5 bağlı + 9 bağlanmamış (gerekçeler yeniden türetildi, yazılı). **5 🔴 ayrık-değer bulgusu AYNI GÜN kapatıldı** (952dd2c) ve bekçiler genişletildi (C10e/C10f · v199 iki yönlü · v239 8a/8b). KALAN AÇIK: ortamlar-arası 3 çift (P0-b/P2 reçetesi belgede) + #11 guard.py okuyucusuz alanı **[2026-08-23 GÜNCEL: #11 v268'de MEZAR TAŞIYLA KAPANDI (`guard.py:554` — SECTOR_CAP_DEFAULT_PCT/HEAT_CAP_DEFAULT_PCT kaldırıldı; 375abd5); kalan yalnız ortamlar-arası 3 çift (`EQUIVALENT_TRUTHS` bugün de 9 olgu)]** (güncelleme 2026-09-03 13:13Z, B-15 ölçümü: #2 repo↔canlı-kod KAPANDI — dagit [B] beyanı + v266; #4 yerel-defter↔canlı-DB 2026-08-23'te ZATEN kapanmıştı (storage.py yerel_donmus_defter, v268) — "uygulanmamış" öncülü bayattı; kalan yalnız #3 max_drawdown ortamlar-arası, canlı bacağı ölçülmedi.)
  Not (TSK-079): **KAPANDI 2026-09-03 15:03Z (B-17, keşif + Rol-1 ölçümü, implementer gerekmedi):** 25a 14/14 — son kalem A1 `/opt/meridian/.env`'deki bayat `MERIDIAN_DASH_TOKEN` kopyası SİLİNDİ (yedek .env.bak-2026-09-03-tsk079 0600; ölçüm: meridian.service EnvironmentFile 51-dash-env-kaldir.conf ile boş, token LoadCredential kanalından, koşan süreç ortamında token yok, .dash.env değeri farklıydı; barsarchive .env'i okur ama token kullanmaz) · 25c: ROADMAP '3 aday' BAYATTI — ikisi 25b DAMGALA ile kapanmıştı (REPLAY_WARMUP_KEYS, GOLGE_BEYANI); kalan 25c-1 rejim-koşullu çıkış sevk kapısı → operatör 'kart-önce aç' → **EDG-2026-072** (§6, onaya); 25c-2 pessimistic_band ampirik alanları debi bekliyor (iş yok) · 25d 10 zincir damgası 8324177 ile ZATEN tamam, davranış değişmedi. Kalan tek açık: 25c-2 debi (takip notu, kalem değil). · **AÇIK** (KISMEN: `25b` 5/6 damgalandı; `25a` operatör 'beklet' — 14 kalemin 13'ü inmiş) · `25a` KALDIR(14) / `25b` DAMGALA(6) / `25c` DİRİLT(3) / `25d` ezilme zinciri — not/kapı durumu: operatör 2026-08-16'da **beklet** dedi **[2026-08-23 GÜNCEL — kısmi: 25b fiilen 5/6 DAMGALANDI (987b552, 08-22; `tests/test_ezilen_damga_v262.py`); beklet yalnız 25a/25c/25d için sürüyor]**
  Not (TSK-081): **AÇIK** (operatörde: `15c` + `15d`; `ARSENAL` 2026-08-24 denetiminde BAYAT-KAPANMIŞ çıktı — Rol-1 doğrulaması bekliyor) · ARSENAL POLİTİKASI (15e giriş + 29 çıkış) · `15d` PIT-temiz faktör seti · `15c` evren genişletme — not/kapı durumu: 15c'nin askısı C6 uzlaştırmasıyla KALKTI
  Not (TSK-082): **KAPANDI 2026-09-03 13:34Z (B-15, 8da5fb5): §6 elle tutulan kart tablosu → README'ye atıflı 5 satır; sayı tek kaynak README (v279 +6 çivi).** · §6 kart indeksi ELLE tutuluyor — üretici BAŞKA dosyaya yazıyor **[2026-08-30 EKLENDİ]** — not/kapı durumu: **AÇIK** · ölçüldü 2026-08-30: `ops/kart_endeksi_uret.py` hedefi `research/cards/README.md`; ROADMAP §6 aynı gerçeğin İKİNCİ kopyasıdır ve türetilmiyor (**tek-kaynak yasası**). Ayrışma ÖLÇÜLDÜ: diskte **73** kart var, §6'nın kendi toplamı **50** diyor — 23 kart indekste yok. Yol ya üreticiye ikinci hedef, ya §6'yı indekse atıf yapan tek bloğa indirmek — karar Rol-1'de
  Not (TSK-083): **KAPANDI 2026-09-03 13:34Z (B-15, 8da5fb5): dört ROADMAP satır çapası kalem kimliğine çevrildi — watchdog.py + v265 → §8 ARŞİV "SB-2 drift_sinifi · davranışsal EOD süpürme kanıtı" satırı (docs/DENETIM-ROADMAP-2026-08-30.md "§7 düzyazısı" demişti; hedef olarak §8 satırı SEÇİLDİ — ayrışma beyanlı), config.py → §5 B-CHOP-BUTCE, v283 → §3 WP5-F; ROADMAP-çapası bekçisi YOK (v373/v324 izlemiyor, beyanlı). v265 düzeltmesi chip oturumundan (ai-trading-08) geldi, aynı commit'te.** · ROADMAP satır çapaları — **üçü de ZATEN çürümüş** **[2026-08-30 EKLENDİ]** — not/kapı durumu: **AÇIK** · ölçüldü 2026-08-30 **bu turdan ÖNCE** (yani bu bakım turu kırmadı): `meridian/watchdog.py` "ROADMAP :503" → §7 düzyazısına düşüyor · `meridian/config.py` "ROADMAP:1476" → runbook-sıralama kalemine · `tests/test_korunum_uyuyan_kurulum_v283.py` "ROADMAP :1164-1188" → PF tartışmasına. Üçü de SATIR çapası; **SEMBOL** çapasına çevrilmeli (CLAUDE.md kuralı). `meridian/` dokunuşu tam-suite kapısı ister → Rol-1

#### DİK DURUM — aşamada ilerleyemez (bloke/askıda) — **6 açık** (5 mevcut + 1 yeni kayıt; kapananlar `§8.T`/G'de) _(2026-08-30 ölçümü)_

| id | name | status | owner | size | trigger |
|---|---|---|---|---|---|
| TSK-065 | PIT mid-cap üst-sınır (sağ-kalan üst-sınır ölçümü) (WP: WP4) | GATED(veri kapısı — delist-bar kaynağı kararı, EDG-018 askıda) | rol1 | M | delist-bar kaynağı kararı (TSK-084) + kart-önce ölçüm |
| TSK-084 | delist-bar kaynağı + FINVIZ erişim bloğu — `dataset.load↔bars_integrity` bağlama (WP: WP4) — operatör 2026-09-03 sabah: beklemede (fiyat/kapsam tablosu istenmedi) | OPERATOR | operator | M | — |
| TSK-051 | (bkz. TSK-051 — QC LEAN CLI `lean login`, kimlik-bloklu; bu satır makine-kurulumu bloğunun DİK DURUM kaydı) (WP: WP9) | (bkz. TSK-051) | operator | — | — |
| TSK-085 | `23b` çıkış slipajı (örneklem bekliyor — ayrı iş üretmez) (WP: WP1) | QUEUED(TSK-069 [EDG-042 K2/K3] + EDG-045 üzerinden kapanacak) | rol1 | — | — |
| TSK-063 | (bkz. TSK-063 — Faz-6 BEŞ KİLİT, kanıt-şartlı) (WP: WP3) | (bkz. TSK-063) | rol1 | — | — |

  Not (TSK-065): PIT mid-cap üst-sınır — durum: **ASKIDA: veri kapısı** · `EDG-2026-018` status=`askiya_veri_kapisi` · **2026-09-03 gece: KART YAZILDI EDG-2026-070 (§6, operatör onayı bekler)** · 2026-08-31 akşam: sağ-kalan üst-sınır ölçümü PLANA alındı (İCRA SIRASI ⑤; kart-önce, yanlılık beyanlı — EDG-018 askıda kalır, yeni kart)**
  Not (TSK-084): delist-bar kaynağı + FINVIZ · `dataset.load↔bars_integrity` `[B-DELIST-KAYNAK · B-FINVIZ-TOKEN]` — durum: **BLOKE: erişim**
  Not (TSK-051): **BLOKE:** makine kurulumu (dotnet YOK, docker YOK) + operatörün `lean login`i · `C2-4` LEAN fizibilite · notebook koşumu `[B-QC-LOGIN]` — durum: ~~**BLOKE: erişim** (QC login)~~ **[2026-08-23 GÜNCEL — blok gerekçesi yanlıştı: QC FREE hesap-açma bloğu 2026-08-03'te KALKMIŞTI (WP9 keşfi); gerçek blok MAKİNE KURULUMU (dotnet YOK, docker YOK; boyut L). Notebook-koşumu operatör-bloğu ayrı ve geçerli]**
  Not (TSK-085): `23b` çıkış slipajı — durum: ASKIDA: örneklem bekliyor → **MUTABIK KILINDI (2026-08-22):** sorusu iki kartta yaşıyor — gerçek-dolum bandı `EDG-2026-042` K2/K3 (birikiyor), replay-varsayım tarafı `EDG-2026-045`; ayrı iş üretmez, o ikisiyle kapanır
  Not (TSK-063): Faz-6 BEŞ KİLİT `[B-FAZ6-KILIT]` — durum: **ASKIDA: kanıt-şartlı**

#### H6 ✅ — KAPANANLAR TAHTADA DURMAZ (2026-08-30'da boşaltıldı)

Bu alt bölüm bir arşivdi ve **tahtanın içinde** yaşıyordu: 20 kapalı satır, her tur okunuyor,
hiçbir tur onlara ihtiyaç duymuyordu. Kapanmış kalemin tahtada satırı olmaz — bu deponun kendi
`Ö-49 bayat-beyan` sınıfıdır. Yirmi satırın tamamı **tam metniyle** `§8.T`/H'dedir; kronolojik
neden-kaydı zaten `§7 KARAR GÜNLÜĞÜ`ndedir (tek-kaynak: tahta AŞAMA söyler, §7 TARİHÇE).

**BEYAN — TAHTANIN SINIRI.** Aşamalar **kart varlığından** türetildi, iş hacminden değil: bir kalem
acil olabilir ve yine H0'da durabilir (`26` değer-eşitliği, `A1` koruma gibi). `H0` bir küçümseme
değil, *"tasarım artefaktı henüz yok"* demektir ve bu kalemlerin hepsi **kart-önce** açılır. §3'ün
WP metinlerinde bu satırların TAM gerekçesi durmaya devam eder; tahta onların yerine geçmez,
**hangi aşamada olduklarını** söyler.

## §3 AKTİF WP'ler — açık cepheler _(eski: §1)_

_Aşağıdaki GÜNCEL DURUM anlık yönelim; ardından uniform ÖZET TABLOSU (her WP tek biçim); sonra WP
detayları (tam metin). Kapanan alt-kalemler ✅ WP içinde tarihçe olarak kalır; tamamlanan WP'ler §8'da._

> ⚠ **BU BLOK 2026-08-13 ANLIK GÖRÜNTÜSÜDÜR (Ö-49 şerhi, 2026-08-22):** içindeki en az üç kalem SONRADAN KAPANDI — /api/diagnostics arızası (v243, 08-14) · N1 bildirim kanalı (08-22 CANLI) · beyin zinciri (08-14'te değişti). Güncel durum §2 TAHTA + §7 günlüktedir; bu blok tarihçe.
> **GÜNCEL DURUM — 2026-08-13 ~20:30Z (YEDİ DAĞITIM + TOHUM YENİLEME; ROADMAP tutarlılık denetimi
> `docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md`):**
> Sistem canlı — birimler active, healthz 200, otoriter suite yeşil. **CANLIDA: C+mb @5R paketi**
> (mb silahlı, slot 20, 0,5R, rampa 15/36 kablolu, `max_drawdown` 0,16) · sprint AYRI systemd
> biriminde (v241 — worker restart'ı artık onu öldürmüyor, kanıtlı) · beyin zinciri AYRIK
> (nous=tencent, gemini=flash-latest) · 8. bütünlük deseni `divergence` · eksen-2 karar kaydı ·
> tohum defteri YENİLENDİ (97→887 işlem, sv=90 ayrı sürüm-uzayı + friksiyon şerhi).
> **⚠ DÜZELTME (denetim A3): "4 motor pozisyonu KORUMALI" İDDİASI ARTIK YANLIŞ** — bugünkü ölçüm
> (`DENETIM-OLU-BILESEN-ENVANTERI:397-398`): NUE/EMR/BKNG/AMGN **dördü de açık ve broker'da canlı
> koruyucu stop YOK** (`korumasiz_motor_disi_pozisyon` 26 kez). Koruma yeniden-kurulumu ELLE ve üç
> kapı ardında (EDG-038 yan bulgusu) → **EN ACİL OPERATÖR KALEMİ** (bkz. §5).
> **AÇIK ÜRETİM ARIZASI (2026-08-13 20:2xZ):** pano açılışı `/api/diagnostics` üzerinden tıkanıyor —
> `parity_report` soğuk çağrıda 16,7s (tohum sonrası defter 9× büyüdü); v243 turu bunu kapatıyor.
> **İKİNCİ ACİL OPERATÖR KALEMİ: BİLDİRİM KANALI (N1)** — kanal yok, 29 alarm teslim edilemedi;
> artık ön-şartsız (systemd exit-143 kapandı).
>
> _(2026-08-09 kaydı tarihçe olarak aşağıda korunmuştur.)_
>
> **GÜNCEL DURUM — 2026-08-09 ~09:00 UTC (GECE+SABAH DÖRT DAĞITIM İNDİ, son commit `964696b`):**
> Sistem canlı ve sağlıklı — broker `alpaca_paper`, birimler active, otoriter suite YEŞİL (v196
> son iki kırmızıyı kapadı). **4 motor pozisyonu KORUMALI:** broker'da 4 açık `P-KORUMA-…-0835`
> OCO (gtc, sınıf=koruma — NUE/EMR/BKNG/AMGN, submit 08:35:44Z). Gecenin+sabahın dört dağıtımı:
> WP-N kanıt-hızı dalgası (v216-v219) · koruma×süpürücü kök düzeltmesi (v220+v221) · dalga-2
> sahte-yeşil avı (v222-v226) · null-sıfır kapısı (v196). Koruma kalemi (WP-S) canlıda
> ARTEFAKTTAN doğrulandı (alpaca.py yerel↔canlı md5 birebir + 4 OCO broker'da); davranışsal
> EOD-süpürme kanıtı Pazartesi 13:30 UTC sonrası ilk gerçek süpürmede. **EN ACİL OPERATÖR KALEMİ:
> BİLDİRİM KANALI (N1)** — token boş, fail-notify her koşuda NO-OP; teslim edilmemiş sev-1
> birikmiş (korumasız 40 · MIRROR_DRIFT 34 · NAKED_POSITION 8). BAĞ: kanal açılmadan ÖNCE systemd
> exit-143 (WP-S2) düzeltilmeli, yoksa her restart "FAILED" bildirir. Ayrıntı:
> `docs/SABAH-TRIYAJI-2026-08-09.md` + `docs/DEVIR-TATBIKATI-2026-08-09.md`.
> _(Aşağıdaki 2026-07-31 gece-vardiyası kaydı tarihçe olarak korunmuştur.)_

### AKTİF WP ÖZET TABLOSU (2026-08-13 YENİDEN NUMARALAMA — uniform biçim: durum · kapsam · açık kalemler · dosya-sınırı · kanıt-kartı)

> **YENİDEN NUMARALAMA (2026-08-13, operatör talebi: "WP isimleri karmaşıklaştı, bunları numara ve
> kısa açıklama şeklinde yeniden düzenle"):** 12 harfli WP adı **WP1-WP11** numaralı ada çevrildi ve
> örtüşen cepheler BİRLEŞTİRİLDİ. **Eski adlar kaybolmadı** — her satır ve her başlık "(eski: WP-E)"
> biçiminde eşlemeyi taşır (arama ve tarihçe için). Aynı turda **§4 öneri havuzu boşaltıldı**: 29
> kalemin 20'si sahibi olan WP'ye taşındı (gövde metni AYNEN), 9'u §8 arşive alındı; 5 kapanmış
> alt-kalem (15a/15b/15f · 20a · 24a) de arşive ayrıldı. Kaynak: `docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md`
> §A-§I. Taşıma haritası §7'in 2026-08-13 kaydında; her taşınan kalem hedefinde
> "_(taşındı: §4-N, eski satır :A-B)_" izini taşır.
>
> **⚠ ÇAKIŞMA UYARISI:** §8 arşivinde **WP0/WP1/WP3** adlı ESKİ (2026-07 iş-emri) WP'ler var —
> buradaki WP1/WP3 ile İLGİSİZDİR. Arşiv başlıkları tarihçe-koru gereği değiştirilmedi, ayrım §8'nın
> tepesindeki notla yapılır.

> **AŞAMA BU TABLODA DEĞİL, §2 TAHTA'DADIR (2026-08-17).** Aşağıdaki "açık kalemler" sütunu bir kalemin
> **GEREKÇESİNİ** taşır, **DURUMUNU** değil — hangi aşamada olduğu, bloke mi, kapandı mı: hepsi tahtada.
> İkisi çeliştiğinde **TAHTA YETKİLİDİR**; bu sütun düzyazı olduğu için bayatlamaya açıktır ve bugün
> bayat bir örneği yakalandı (M1 'en yüksek kaldıraç' derken kart 15 gündür kill#1'le arşivdeydi).
> Metin SİLİNMEDİ (tarihçe-koru) — yetkisi daraltıldı.

**SON TAZELEME: 2026-08-13 — hücreler fotoğraftır, yetkili kaynak §2 TAHTA + WP gövdeleridir (2026-08-23 süpürme: en az 6 hücre bayat; barizleri aşağıda köşeli-ayraçla damgalandı).**

| WP | durum | kapsam | açık kalemler | dosya-sınırı | kanıt-kartı |
|---|---|---|---|---|---|
| **PRG-01 İcra ve Friksiyon** _(eski: WP1 · WP-E + Ö-23 + Ö-13)_ | **AÇIK** · 🔴 aktif | emrin doğduğu andan dolduğu ana kadar: iki-motor icra sadakati · E1-E5 hattı · gerçek TCA/friksiyon defteri | **23c K1 dinlenen limit (D5 — kapanmadan hiçbir limit-tavanı kararı verilemez)** · 23d bar-içi stop varsayımı **[2026-08-23: KAPANDI — `EDG-2026-045` measured, 9d2cfb9]** · 23e gün-içi pencere (altyapı) · 23f `gap_behavior:cancel` elenmeli **[2026-08-23: KAPANDI — 746cbe8, hüküm EXE-001 gap-eksenine işlendi]** · 23b çıkış slipajı (örneklem bekler) · WP-E 6 boşluk sınıfı (#1/#2/#5/#6/#7/#8) **[2026-08-23: sınıf v234'le 08-12'de kapanmıştı — §7 2026-08-22 kaydı]** + E2 canlı-geçiş · 13 scale-out latent (düşük) · ~~A6 şerh önerisi~~ **[2026-08-23 KAPANDI-BAYAT: şerh 08-13'te İŞLENMİŞTİ (ROADMAP:389 ✅) ve konusu EXE-005/006/008 zinciriyle tümüyle tüketildi — hücre kalıntıydı]** | `loop.py` · `adapters/alpaca.py` · `broker.py` · `analytics`(cf) | EXE-2026-001(+R1/R2) · EXE-2026-002 · EDG-2026-037/038 |
| **PRG-02 Sermaye ve Koruma** _(eski: WP2 · WP-S + Ö-27 + Ö-7 + Ö-9/Ö-18)_ | **KAPALI** (cephe 2026-08-22) · 🔴 ~~aktif — **ACİL**~~ **[2026-08-23: cephe 08-22'de TAM KAPANDI — §7]** | sermaye defterinin, pozisyon korumasının ve P&L görünürlüğünün aynı gerçeği söylemesi | **koruma yeniden-kurulumu — 4 pozisyon ÇIPLAK (§5 KOVA-1)** **[2026-08-23: BAYAT — 08-22 ölçümü korumasız 0/7]** · **equity_curve zinciri (D1 ACİL: `seed_boundary` ONARIMI → kadanslı yazar → pano reset-penceresi)** **[2026-08-23: KAPANDI v264]** · davranışsal EOD süpürme kanıtı hâlâ KAYITSIZ (A4) · SB-2 `drift_sinifi` · 4 pozisyon adet-sapması (operatör yön kararı) · melez pozisyonlar + dormant icra (§5) | `adapters/alpaca.py` · `store.py` · `obs.py` · `ledgerstamp.py` · `loop.py` | EXE-2026-001-R1/R2 · EXE-2026-002(+R1) · EDG-2026-036/038 |
| **PRG-03 Öğrenme Döngüsü** _(eski: WP3 · WP-L + Ö-28 + Ö-10 + Ö-19)_ | **AÇIK** · 🔴 aktif _(eski "📋 tetik-şartlı" — A1 ile ÇÜRÜDÜ)_ | hipotez üretiminden ship'e giden döngünün kendisi + OPT parametre-evrim boru hattı + Faz-6 merdiveni | **28a görünmez süzgeç (EN ÜST — 2026-08-13 17:26'da hâlâ ateşliyordu)** · **28d kapı ÖLÇEMİYOR (chop 27 < 30)** **[2026-08-23: BAYAT — teşhis 08-22'de TAMAM, öncül çürüdü (gerçek mekanizma bütçe bağlaşımı); dönüşen kalem chop bütçe-kapalılığı OPERATÖR KARARI — §2 TAHTA]** · 28c tek satır / 21 tekrar · 28e/28f/28g/28h · 28i incumbent holdout −0,5366 · OPT Faz-1 serbest / Faz-2 28d'ye bağımlı · Faz-6 BEŞ KİLİT kanıt-şartlı | `hermes.py` · `reflect.py` · `probgate.py` · `bounds.yaml` | EDG-2026-036 · KYS-2026-002 |
| **PRG-04 Veri ve Evren** _(eski: WP4 · WP-U + WP-D + Ö-8)_ | **AÇIK** · 🔶 aktif (stratejik ana cephe) | girdi verisinin bütünlüğü + ölçülen evrenin kendisi (PIT üyelik, delist-bar, karantina, split) | PIT mid-cap üst-sınır (EDG-018 veri-kapısı) · delist-bar kaynağı + FINVIZ (§5) · `dataset.load↔bars_integrity` bağlama (§5) · ~~türetilmiş artefakt yeniden üretimi~~ **[2026-08-24 KAPANDI-BAYAT: yeniden üretim yapısal (P5 gecelik `component_ic()` + `threshold_curve.build()`) ve dışlama kapısına kablolu; canlı artefaktlar 2026-08-21 taze, `component_ic.json` bar-taban damgalı — `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A1]** · ~~seans-içi boşluk~~ **[2026-08-24 KAPANDI-BAYAT: `scheduler._intraday_gap_check` → `barsarchive.gap_scan` 08-01/02'de sevk, canlıda 3.321 olay / 15 seans; sınıf kırılımı 3.321 `sembol` / 0 `akis`, sembol tarafı ölçülmüş yapısal gürültü — genişletme sinyal değil alarm hacmi büyütür (`docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A2)]** · earnings kapsama+fail-open **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1): kapsam bugün 216/251 (%86,1 — eski "194" bayat), 35 sembol fail-open ve bedeli hiç sayılmadı; retro sayım her CANLI giriş anında sembol kapsam-dışı mıydı × gerçek rapor tarihi girişten ≤5 gün sonra mıydı (PIT anlık görüntüsüyle); donuk eşik N≥1 → daraltma tasarımı, N=0 → ÖLÇÜLMÜŞ-RETLE kapanır → KART ÖN-KAYITLI: `EDG-2026-055` (3ddafb1)]** · MNST split düzeltmesi (kart-önce) **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1): teşhis tam ama kart ve kod YOK, canlı semptom sustu (`data_quality.json` 08-21 temiz) — yapısal körlük duruyor; A1 oran-imza kartı, donuk eşik: MNST 2026-08-11'de yanlış-alarm 1→0 VE split-dışı günlerde yanlış-pozitif 0 → KART ÖN-KAYITLI: `EDG-2026-056` (3ddafb1)]** | `research/pit_universe/` · `adapters/data.py` | EDG-2026-018/021/022 |
| **PRG-05 Ölçüm Altyapısı** _(eski: WP5 · WP-M + WP-S2 + Ö-4 + Ö-14 + Ö-20 + Ö-16)_ | **AÇIK** · 📋 aktif | ölçümün kendisinin doğru olması: metodoloji/yasa borçları · görünürlük borçları · K-defteri · paket-bağımlı eşikler · korunum kovaları | ~~M1 kıyas-kirlenmesi~~ **KAPANDI: kill#1, KYS-2026-001, 2026-08-02 — yanlılık pratik-önemsiz** · M2 DSR-yarısı → Ö-4 aracı (D6) **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1): reflect şema kararı → KYS-002 R2 revizyonu; taban RAPORLANIR (hüküm eşiği yok), kill: ölçek-eşdeğerlik doğrulanamazsa DSR tabanı yazılMAZ]** · ~~M7~~ **[2026-08-24 KAPANDI-BAYAT: damga dört prescreen noktasında yazılı + çivili, iniş 4b84871 2026-08-02 — 08-09 keşfi bunu inişten BİR HAFTA SONRA açık listelemişti (Ö-49 bayat-beyan sınıfı); `docs/ELEME-WP5-2026-08-23.md` #2]** · M8 **[2026-08-24 TASARIM-KAPANIŞI: U1/U2/U3 mekanik işlenir, U5 ve U7 REDDEDİLİR, tek mimari karar U6 (kart-K ↔ DSR `n_trials`); kalan mini-iş hafta-1 partisinde]** · ~~M9~~ **[2026-08-24 KAPANDI-BAYAT: Chen-2022 dengeleme notu kodda + `docs/olcum_standartlari.md:348`'de, iniş c9aee5e 2026-08-10; F13 yüzey bacağı WP8'in — WP5'te iş kalmadı; `docs/ELEME-WP5-2026-08-23.md` #4]** · M11 **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=0 tarama): alan-merceği ARACI repo'da hiç yok (mercek 08-07'nin oturum-içi metodolojisiydi) ama sınıfın değeri uyuyan-yol + broker_status ölü-dalıyla KANITLANDI → kova-6 salt-ölçüm taraması, kalibrasyon kapısı şart]** · ~~2B~~ **[2026-08-24 KAPANDI-BAYAT: `olcum_araclari.blok_bootstrap_ci` genel standart + iki BEYANLI istisna (analytics circular ikizi, `benchmark_relative` IID'si) = kalemin istediği son durum; iniş 4b84871; `docs/ELEME-WP5-2026-08-23.md` #6]** · ~~2C~~ **[2026-08-24 KAPANDI-BAYAT: `_empirical_bayes` + `shrunk_regime_cells` → `/api/diagnostics` → pano zinciri tam, ikiz beyanlı, τ²=0 bulgusu v125 arşivinde; `docs/ELEME-WP5-2026-08-23.md` #7]** · 2D **[2026-08-24 TASARIM-KAPANIŞI: kalemin sahibi `holdout_rotation_advice` (ölçer-önerir-uygulamaz, panoda); sorgu basıncı limit 20'nin ÇOK altında — takvimle değil tetikle yaşayan kalemi stokta tutmak çift-defterdir; kalan mini-iş hafta-1 partisinde]** · ~~A4~~ **[2026-08-24 KAPANDI-BAYAT: `prediction_accuracy_band` ilk commit'ten beri var (d9c3f24), `A4_BAND_MIN_N` n<3'te uydurmuyor, okuyucuları gerçek (hermes + pano); `docs/ELEME-WP5-2026-08-23.md` #9]** · ~~kill#4 uygulama~~ **[2026-08-24 KAPANDI-BAYAT: `KAPSAM_DISI_SINIFLARI=("eod_yok",)` fail-closed daraltması `faz5_cikis.py:42-49`'da, kart R1 revizyonu işlenmiş ve status measured — "ayrı tur borcu" denen iş o turda YAPILMIŞTI; `docs/ELEME-WP5-2026-08-23.md` #10]** · Faz-5 örneklem (iş ister, kod değil) · 20c yönetişim asimetrisi **[2026-08-24 TASARIM-KAPANIŞI: `position_size_r` LIMIT_KEYS'e alınMAZ + bounds dokunulmaz, ama goal'a ÇİFT-BAĞ çivisi — slot≠20 VEYA size≠0,5 tek başına gelirse kapı `REVIEW`; kalan mini-iş hafta-1 partisinde]** · 20d ince marjlar **[2026-08-24 TASARIM-KAPANIŞI: 20b emsaliyle KAYIT sınıfına indirildi (hiçbir alt kalem iş üretmiyor; `EXPLORE_MAX_POS=5` artık beyanlı operatör debisi, max_open kalıntısı DEĞİL), canlanma koşulu beyanlı; kalan mini-iş hafta-1 partisinde]** · korunum kovası (kalan **3**) **[2026-08-24 BİRLEŞTİR: EDG-2026-049 hükmü sonrası (hüküm 2026-08-24'te indi: NO-GO — kova artık inebilir)]** · kart biçim/lint **[2026-08-24 TASARIM-KAPANIŞI: dup-anahtar dedektörü 65 kartın tamamında koşuldu, sınıfın nüfusu **1** (EDG-038) ve zarar bugün yalnız TESADÜFEN yok (PyYAML last-wins dolu bloğu seçiyor) → Rol-1 placeholder'ı siler + dedektör çivi olur, ayrı şablon turu AÇILMAZ; kalan mini-iş hafta-1 partisinde]** | `analytics` · `reflect` · `dataset` · `api.py` · `web/app.js` · `guard.py` | KYS-2026-001(ARŞİV) · KYS-2026-002 · EXE-2026-002-R1 |
| **PRG-06 Sistem Bütünlüğü** _(eski: WP6 · WP-H + Ö-25 + Ö-26 + Ö-2)_ | **AÇIK** · 🟡 aktif | kodun ve dağıtımın kendine sadakati: sürüm kontrolü · atomik yazım · sertleştirme · ölü/ezilen bileşen · "aynı gerçek iki yerde" kapıları | **26 değer-eşitliği kapısı (D3 ACİL — 26 kapısız çift)** **[2026-08-23: "26 kapısız çift" BAYAT — envanter: 12 kaynağında kapanmış + 5 bağlı + 9 gerekçeli-bağlanmamış; `EQUIVALENT_TRUTHS` 9 olgu; kalan ortamlar-arası 3 çift]** · 25a KALDIR(14) / 25b DAMGALA(6) / 25c DİRİLT(3) / 25d ezilme zinciri / 25e öğrenme 0 ship → WP3 · **F9 dagit kapsamı dışı dört canlı artefakt** · H3 tur-2 seccomp · LoadCredential+OCI (§5) · gözlemlenebilirlik adayları a-e · A17 kaynak-içi çapa bayatlığı | `store.py` · `auth.py` · `watchdog.py` · `hermes.py` · `deploy/` · `dagit.sh` | — |
| **PRG-07 Skill Katmanı** _(eski: WP7 — YENİ CEPHE 2026-08-13; eski: Ö-24 — bugüne dek WP'si yoktu)_ | **AÇIK** · 🆕 aktif | skill'in çağrılıp çağrılmadığı, izinin tutulduğu ve karar yüzeyine bağlandığı hat | 24b SOUL kilidi açıldı ama **HİÇ SINANMADI** · ~~24c ana danışma yolu ÖLÜ (§5 KOVA-3)~~ **[2026-08-24 KAPANDI-BAYAT: iddianın penceresi (08-06..08-13) bir retry fırtınasıydı — yol 08-14'te dirildi ve danışman TAM BU YOL ÜZERİNDEN terfi etti (2026-08-14T21:03 AUTHORITY_CHANGE, R farkı 0.638, n=100); `docs/ELEME-WP7-2026-08-23.md` §1]** · ~~24d pilot-S1 A/B~~ **[2026-08-24 KAPANDI-BAYAT: terfi tabanı PİLOTSUZ aşıldı (`n_pairs=100`), ölçülecek veto yüzeyi 9 günde 0 kez ateşlendi, iki pilot skill'i canlı ön-yüklemede yok — tasarımın üç öncülü de bugün yanlış; `docs/ELEME-WP7-2026-08-23.md` §2]** · ~~**24e çekimser teşviki (terfinin ASIL duvarı)**~~ **[2026-08-24 KAPANDI-BAYAT: duvar iddiadan BİR GÜN sonra yıkıldı — `r_gap` null→0.857, `promoted=true` 08-14'ten beri, son-30g çekimser %40'a düştü; bağlayıcı kısıt teşvik değil HACİMdi; `docs/ELEME-WP7-2026-08-23.md` §3]** · ~~24f SKILL.md↔kod bağı yok~~ **[2026-08-24 BİRLEŞTİR: 24h rozet-damgası ailesine devredildi]** · ~~24g sprint sızıntısı~~ **[2026-08-24 KAPANDI-BAYAT: v242 kapısı canlı kodda ve üç gerçek kum-havuzu koşumunda sökümü BLOKE etti (`n_sokulecek=4`, 08-14/08-15/08-22); bayrak testi değil gerçek-koşul kanıtı; `docs/ELEME-WP7-2026-08-23.md` §5]** · skill rozeti damgası (C10, eski Ö-25b) **[2026-08-24: 24f gövdesi buraya katlandı — aile tek kalem]** | `skills.py` · `hermes.py` · `SOUL.md` · `skills/` | EDG-2026-019 |
| **PRG-08 Pano ve Operatör** _(eski: WP8 · WP-UX + WP-P + Ö-3)_ | **AÇIK** · 🟡 frontend esasen bitti | operatörün gördüğü yüzey (icra) + kontrol-odası doktrini (kabul çıtası) | ~~AÇIK ÜRETİM ARIZASI: `/api/diagnostics` 16,7s~~ ✅ v243 kapattı (08-14; dördüncü kopya, 08-22 Ö-49 süpürmesi) · D3-b F3-F13/F15 · D3-c C2-4/C2-5/6. çalışma · F8 durum sözlüğü (kanonik okuyucu ön-şartlı) **[2026-08-23: tasarım belgesi yazıldı — H0→H1]** · 15 bekçi mekanizması **[2026-08-23: "15" bayat — F8 ölçümü 17]** + halt_learning | `web/app.js` · `api.py` · `docs/RUNBOOK.md` | harita: WP8 detayı |
| **PRG-09 QuantConnect** _(eski: WP9 · WP-QC)_ | **BLOKE:** makine kurulumu + `lean login` · 🆕 aktif | platform-içi ölçüm + LEAN yerel motor (asla arşiv-kaynağı değil) | C2-4 `lean init` QC-login-bloklu (§5) VEYA dotnet-CLI'sız L-boyut · FREE fizibilite ②③④⑥⑦ · notebook koşumu (§5) | `research/qc_dogrulama/` | EDG-2026-021/022 |
| **PRG-10 Referans Verisi** _(eski: WP10 · WP2 — EDGAR)_ | **KAPALI** (açık borç yok) · 🟢 borç yok | EDGAR PIT fundamentals adayları | açık borç YOK; yeni PIT-aday özniteliği ancak KART-önce açılır | skor bileşeni + `bounds.yaml` | EDG-2026-016(SUCCESS) · 012/013/014 |
| **PRG-11 Strateji ve Seçilim** _(eski: WP11 · Ö-15 + Ö-29 + Ö-12)_ | **AÇIK** · 🔶 aktif | ne alıp sattığımızın kendisi: kurulum arsenali · seçilim kalitesi · boyutlama · rejim | ARSENAL POLİTİKASI (15e giriş + 29 çıkış, ortak kanıt çıtası; **pullback kararı §5 KOVA-2**) · 15d PIT-temiz faktör seti (OPT Faz-2'nin yeni ilk müşteri adayı) · 15g slot↔sektör tavanı yapışıklığı · **15c evren genişletme ASKIDA (C6 çözülene dek)** · C6 uzlaştırma: evren mi ısı mı bağlıyor | `strategy.py` · `guard.py` · `bounds.yaml` | EDG-2026-026/033/034/035/039 |
| **WP12 Bot Roster** _(YENİ CEPHE 2026-08-31; program 2026-08-27 spec'iyle başladı, bugüne dek WP'si yoktu — dört fazı §7'de yaşıyordu)_ | **AÇIK** · 🆕 aktif | hermes bot filosu: gözetimsiz dar-görevli profiller — dikkat bütçesi (`@sef`) · sessiz arıza (`@bekci`) · amaç sorusu (`@karne`) · kalan roster | **Faz 1-4 TAMAM + CANLI** (üç bot 2026-08-31'de kuruldu/test-ateşlendi; İLK KARNE indi; model Super→Ultra A/B ölçümüyle geçti — `docs/OLCUM-MODEL-AB-2026-08-31.md`; SOUL'lara üslup + sade-özet kuralları) · **Ajan iletişim yüzeyi** (A→B, dört muhatap — §2 H1 satırı) · **Faz 5+ rol seçimi ÖLÇÜM-ÖNCE** (`@kod` · `@ayna` aday; `@nobet` ELENDİ — ikinci token=sır; `@hipotez` BLOKE — merdiven duvarı kartı, EDG-2026-058 bağı) · öneri: canlıda ≥1 bot değer kanıtlamadan Faz 5 açılmaz | `deploy/hermes/profiles/` · `deploy/oracle-a1/meridian-{brifing,bekci,karne}.*` · `ops/{sef,bekci,karne}_*.py` | spec `2026-08-27-bot-roster-design.md` |

### AKTİF WP DETAYLARI (tam metin — kapanan alt-kalemler ✅ tarihçe olarak korunur; taşınan §4 kalemleri kaynak-satır referanslı)

_**[2026-08-31 DURUM DENETİMİ — §3'ün 70 işaretsiz kalemi tek tek geçildi.]** Sonuç üç kümedir:
**35'i rozet aldı** (25'i depo kanıtıyla `KAPALI`/`AÇIK`/`ASKIDA`, 10'u **`🟡 DOĞRULANMADI`** —
gerekçesi her satırın kendi rozetinde yazılı, çoğu canlı defter isteyen sorular ve bu tur cloud
klonunda koştu). Kalan **30'u KAYIT'tır, kalem değil**: `BULGU` · `KEŞİF` · `ÖLÇÜM` · `ZATEN VAR` ·
`RED` · `EMİLDİ` · ders satırları — bunlar WP'nin GEREKÇESİni taşır, açılıp kapanmazlar ve
`belirsiz` okunmaları DOĞRUdur. **§3'ün kendi kuralı zaten bunu söylüyordu** (yukarıdaki 2026-08-17
şerhi: *"aşama bu tabloda değil §2 TAHTA'dadır"*); bu denetim onu satır düzeyinde ölçtü.
Yöntem ve tam liste: `docs/DENETIM-ROADMAP-2026-08-30.md`._

### PRG-01 — İcra ve Friksiyon 🔴
_(eski: WP1 · WP-E İcra Gerçekliği + Ö-23 icra/friksiyon hattı + Ö-13 scale-out)_

**KAPSAM (tek cümle):** Emrin doğduğu andan dolduğu ana kadar geçen her şey — iki-motor icra
sadakati, giriş/çıkış limit rejimi, gerçek slipaj/TCA defteri ve replay'in friksiyon iyimserliği.

#### WP1-A · İcra gerçekliği çekirdeği _(eski WP-E gövdesi; 2026-08-03 karne-tazeleme bulgusu; kart: EXE-2026-001)_
- **BULGU (research/olcumler/karne_tazeleme_2026-08-03/):** güncel motorla geriye-dönük defter
  TERSİNE DÖNDÜ — replay net +2.493$→−1.182$, PARA-v3 0,1605→−0,0037, oos 0,0579→0,0196, n 201→147.
  TEK-DEĞİŞKEN ATIF: farkın TAMAMI E1 giriş-limitinin ATR bacağı (dolum 237→176; limit daralınca
  kaçan dolumlar kârlı girişler). Diğer adaylar ölçülüp elendi: replay-PIT 1 plan/0 skor · ısı-5R
  0 · fail-closed/turnover/kardeş-PIT yapısal 0. OKUMA: eski artı büyük ölçüde replay-dolum
  iyimserliğiydi; canlı-ödeme-0,97-vs-Search-1,53 payda-uyumsuzluğunun ana açıklaması bu (E4
  sorusunun yarısı kapandı). E1 varsayılan noktası (0,5·ATR, %1 tavan) ÖLÇÜLMEMİŞ bir seçimdi ve
  defteri çeviriyor → E1 grid ölçümü (0,25/0,005 · 0,5/0,01 · 1,0/0,015 + limitsiz-MOO kolu)
  programın EN ÖNCELİKLİ ölçümü; BT-1 beklemesi bu kalem için KALKTI — ve AYNI GÜN KOŞULDU:
  **E1 GRİD ✅ ÖLÇÜLDÜ (e1_grid_2026-08-03/): limit-bacağı MONOTON ZARARLI** (net$ A −7,2k · B −1,2k ·
  C −2,9k · LİMİTSİZ +2.957$/+1.959$-E3; kaçanlar sistematik kazanan; kill#1 yok; gap-bacağı
  replay'de yapısal-ölçülemez — canlı/gölge noktaları kayıtlı; skor-para ayrışması B/C kayıtlı).
  ~~KARAR OPERATÖRDE~~ **✅ KARAR VERİLDİ (2026-08-07, kart `EXE-2026-001-R2`, K += 1):** işletim
  noktası REF·limitsiz rejimi — `execution_v2` canlıda `limit_atr_mult: 100,0` / `limit_pct_cap:
  0,04`, yani limit tavanı hiçbir gerçek barda bağlamıyor ve bağlayan tek şey `MAX_ENTRY_GAP_PCT
  = %4`. Bu ÖLÇÜLMEMİŞ dördüncü bir nokta DEĞİL: grid'in `ref_limitsiz` kolu da (`1000·ATR/%10`
  → limit tetik×1,10 > max_chase tetik×1,04) tam bu rejimdi — sayılar farklı, DAVRANIŞ AYNI.
  Rol-1 bunu önce "kanıtsız sapma" diye okudu ve YANILDI; kanıt kartın kendi grid'indeydi.
  Canlı doğrulama (08-06, dört pozisyon): AMGN +1,78% · EMR +1,60% · BKNG +1,55% kovalandı,
  ödül/risk 2,50→1,50/1,76/1,90 indi; NUE tetiğin ALTINDA doldu (2,63). **Eski B noktasında bu
  dördün ÜÇÜ hiç açılmayacaktı** — ölçüm, atlanan işlemlerin maliyetinin kovalama aşınmasından
  BÜYÜK olduğunu söylüyor (`entry_missed_limit`: A 38 · B 23 · C 12 · REF 0).
  `counterfactual.advance` AYNI sabiti okuduğu için canlı ile cf hâlâ aynı stratejiyi ölçüyor.
  E2 defteri gerçek dolumla dolmaya devam eder; canlı-geçiş kapısında E2 kanıtıyla yeniden hüküm. Ayna-dolum akışının boşluğu (E2'nin öbür yarısı) ayrı teşhis kalemi. Şerhler raporda (bars_integrity dışlaması
  yok · survivorship · +0,018 replay-iyimserliği · cf-sadakat +0,039R).
- E1 iki-motor mutabakatı (iç MOO-tarzı vs ayna buy-stop GTC + gap-red kökü) + marketable stop-limit
  grid + gap-risk vetosu · E2 slipaj defteri (yüzey hazır, E1'e bağlı) · ~~E3 kötümser maliyet bandı
  (açılış-spread ~20bps) → PARA-v3 net-kötümser sütun~~ **→ DÜZELTME (2026-08-13, denetim A5): E3
  bir "ölçülecek band" DEĞİL, ÇÜRÜTÜLMÜŞ VARSAYIM.** Kanıt: `EDG-2026-037…yaml:70` "aksine **E3
  kötümser bandı (+5 bps/bacak) DA iyimser çıktı (~4,5×)**"; `:79-80` `pessimistic_band_v2`ın
  `ampirik_bps: null, ampirik_n: 0` — "bugüne dek hiç ölçülmemiş, literatürden alınmış bir sayıymış".
  Kalem WP1-B (eski Ö-23) hattına bağlandı (denetim C2) · E4 gece/gündüz PnL ayrıştırması (join;
  BT-1 damgası sonrası) · E5 gecikmeli-giriş A/B (E2 verisi sonrası, opsiyonel).
- EMİLDİ: eski Y2 TCA/shortfall defteri (=E2/E3) · canlı-TCA rezervasyonu (canlıya geçişte,
  denetim YÜ-1) · payda-uyumsuzluğu sorusu (canlı ödeme 0,97 vs Search-OOS 1,53 — E4+E1 açıklayacak).
- **✅ K1 ŞERHİ İŞLENDİ (denetim A6 / §H-7 — 2026-08-13, kart: `EXE-2026-001-entry-execution.yaml`
  → `revizyonlar[R2].k1_serhi`, commit 025ef1d):** `EXE-2026-001-R2`nin "limit-bacağı MONOTON
  ZARARLI · kaçanlar sistematik kazanan" hükmü SİLİNMEDİ, üstüne şerh yazıldı —
  `ARASTIRMA-SLIPAJ-AZALTMA:349-350` harfiyen alıntılı: "K1 kapanmadan yapılan her limit-tavanı
  ölçümü kaçan işlem maliyetini SİSTEMATİK OLARAK ABARTIR, ve 2026-08-03 E1 grid hükmü tam olarak o
  abartılmış maliyetle verilmiştir." Fırsat kanıtı `:335-345`: 100 bps tavanla EMR/BKNG/AMGN limit
  fiyatı aynı seansta işlem gördü. **Canlı davranış DEĞİŞMEDİ** — işletim noktası REF·limitsiz
  rejiminde kaldı (operatör hükmü 2026-08-07), K defterine etki YOK; askıya alınan tek şey
  gerekçenin gücü. Şerh, WP1-B/23c (K1 kapanışı) tamamlandığında kalkar. **[2026-08-23: şerh KALKTI — kalkış kaydı kartta (`EXE-2026-001` `k1_serhi` bloğu); yerine EXE-006 hükmü geçer: E1 yeniden açık, karar §5 `[B-E1-LIMIT]`]**

#### WP1-B · İCRA/FRİKSİYON HATTI _(taşındı: Ö-23, eski satır :1006-1020 — 2026-08-13; §4 boşaltıldı)_
_(denetim C2: Ö-23 WP-E'nin alt-cephesidir, ayrı backlog kalemi değil. D5: **Ö-23'ün TAMAMININ
önceliği yükselir** — K1 yalnız gelecek kararları değil geçmiş bir hükmü de asıyor.)_
23. **İCRA/FRİKSİYON HATTI (EDG-037/038 + `docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md`)** — PF'i
    yükseltmenin en büyük kaldıracı artık strateji değil İCRA (EDG-035 komşuluğu kapattı; icra farkı
    ölçüldü). Sıralı kalemler: · **23a ÖLÇÜT ✅ KAPANDI** (EDG-038: kanonik payda konsolide açılış) ·
    **23b ÇIKIŞ SLİPAJI** — n=0, sebebi TIF değil TUTUŞ SÜRESİ (5 seansta hiçbir stop/hedef değmedi);
    örneklem beklenecek, eşik oynatarak hızlandırmak YASAK · **23c REPLAY'DE DİNLENEN LİMİT DALI** —
    replay limit emrinin dinlenmesini modellemiyor, kaçan-işlem maliyetini ABARTIYOR; iki ölçüm zıt
    işaretli (E1 grid vs 885-kesim) ve bu düzeltilmeden hiçbir limit-tavanı kararı verilemez · **[2026-08-23 GÜNCEL — SATIR BAYATTI, yedinci vaka: modelleme ZATEN KAPANDI (EXE-2026-005 H3 bar_low düzeltmesi, çivili) ve EXE-2026-006 K=8 grid'i onunla yeniden koştu → E1 hükmü YENİDEN AÇIK ama H2 ölçülemedi + Ö3 ΔP&L CI'ları 4/4 sıfır-içi: 'bacağı aç' bu ölçümden ÇIKARILAMAZ. Kalan iş ölçüm değil OPERATÖR KARARI (canlı execution_v2 yapılandırması; düşük-güç şerhiyle) — EXE-001 K1 şerhi kalkmış sayılır, karar kalemi §5'e adaydır.]** ·
    **23d BAR-İÇİ STOP VARSAYIMI** — `broker.py:596` stop dokunuşunu `eff_stop`ta dolmuş sayıyor,
    stop-tetik slipajı SIFIR; giriş LİMİT (tavanlı) ↔ çıkış stop→MARKET (tavansız) asimetrisiyle
    birleşince adı konmuş bir iyimserlik **[2026-08-23 KAPANDI: `EDG-2026-045` measured (9d2cfb9)]** · **23e GÜN-İÇİ PENCERE** — 13:30-13:45 menzili 146,7 bps,
    13:45-14:00'te 84,9 (−%42), bedeli +3,4 bps sürüklenme; AMA bugünkü replayde MODELLENEMEZ
    (dakika barı yolu yok, `timeframe=1Day` tek yol) → altyapı kalemi **[2026-08-23 GÜNCEL — ÖLÇÜLDÜ: replay engeli VERİ tarafında eridi (canlı bars_intraday dakika arşivi); `EDG-2026-047` K=1 ölçtü, Ö1 ATEŞLEDİ: Δ%menzil −%42,3 CI [−%44,3, −%40,1] — dış n=401 ölçümünün birebir replikasyonu. Fiyat etiketi: sürüklenme medyan +4,65 bps (|m2| 55,4 geniş). Pencere-kaydırma artık §5 kalemi [B-PENCERE-KAYDIR]; karar+kart operatörde.]** · **23f `gap_behavior: cancel`
    ELENMELİ** — koşulu TOTOLOJİ (`entry_trigger`=sinyal barı kapanışı, referans aynı → hep true);
    filtre değil KAPATMA DÜĞMESİ (%51 ya da %100 işlem keser) **[2026-08-23 KAPANDI: 746cbe8 (08-22) — hüküm `EXE-2026-001` gap-eksenine işlendi, canlanma koşulu beyanlı]** · **23g ADV/likidite sıkılaştırma ATIL**
    (etki ≤0,8 bps — kapatılan kalem). *öncelik: ~~23c>23d>23e; 23f/23g karar-gerektirmez~~ **[2026-08-23: sıralama bayatladı — 23c/23d/23f kapandı, 23e karar+kart operatörde (§5 `[B-PENCERE-KAYDIR]`); hatta açık ölçüm kalemi yalnız 23b (örneklem bekler)]**.*

#### WP1-C · Scale-out latent kusuru _(taşındı: Ö-13, eski satır :833-842 — 2026-08-13)_
_(denetim D13: **düşük KALIR** — ve TCA bunu pekiştirdi: scale-out ek dolum bacağı üretir, gerçek
friksiyonda daha da zararlı; EDG-027/029 hükümleri güçlenir.)_
13. ~~**Scale-out trail kusuru**~~ → **LATENT-KUSUR notuna indi (EDG-029 ölçtü, 2026-08-12):** düzeltilmiş
    haliyle bile kavram CI-negatif (B −0.053/C −0.045) → alet kapalı kalıyor, düzeltme ACİL DEĞİL.
    ZORUNLULUK ŞARTI: scale_out_frac bir gün açılacaksa ÖNCE bu kusur düzeltilir (bankalama-barı
    trail=entry_fill → aynı-bar stop_gap). *öncelik: düşük (latent) · orijinal bulgu:* — bankalama
    barında trail=entry_fill kurulumu (entry_fill>open) koşucuyu AYNI BARDA ~0.7R stop_gap'e kesiyor;
    ölçüm bu yüzden CI-negatif (−0.14R) çıktı — kavram değil implementasyon kusuru. DÜZELTME ADAYI:
    bankalama-barında trail'i entry_fill'e ÇEKMEME (ör. bir sonraki bardan itibaren) ya da aynı-bar
    stop-kontrol sırası; motor-değişikliği = kart + yeniden-ölçüm (027/H1 hükmü o zamana dek geçerli:
    alet kapalı). *gerekçe: büyük gap-kazananlar budanıyor (ENPH +12.3R→0.72R) · boyut: S-M ·
    bağımlılık: kart · öncelik: yüksek (çıkış-kanaması ailesi).*

### PRG-02 — Sermaye ve Koruma 🔴 **[2026-08-23: KAPANMIŞ CEPHE — "WP2 CEPHESİ TAM KAPANDI" 2026-08-22 (§7; 2af0e65, 6b29087); aşağıdaki gövde tarihçedir]**
_(eski: WP2 · WP-S + Ö-27 koruma-elle + Ö-7 adet-sapması + Ö-9/Ö-18 equity_curve)_

**KAPSAM (tek cümle):** Sermayenin defteri, pozisyonun koruması ve P&L'in görünürlüğü — kitap ↔
broker ↔ pano üçlüsünün aynı gerçeği söylemesi.

> **⚠ EN ACİL (denetim A3/D4, 2026-08-13):** `DENETIM-OLU-BILESEN-ENVANTERI:397-398` — AMGN/BKNG/
> EMR/NUE **dördü de açık ve broker'da canlı koruyucu stop YOK** (`korumasiz_motor_disi_pozisyon`
> son 7 günde **26 kez**). §3 GÜNCEL DURUM'un "4 pozisyon KORUMALI" iddiası (2026-08-09) bugün
> YANLIŞ ve düzeltildi. Operatör kalemi §5 KOVA-1'de.
> **[2026-08-23 TARİHÇE DAMGASI: bu blok 08-07→13 penceresinin fotoğrafıdır — 08-22 A1 ölçümü korumasız 0/7 (yedi motor pozisyonu TAM korumalı; §2 TAHTA H6 satırı). ACİL DEĞİL; bunu okuyup acil koruma-kurulum turu AÇMAYIN (çift-emir riski, CLAUDE.md §5)]**

#### WP2-A · Sermaye/defter bütünlüğü + koruma çekirdeği _(eski WP-S gövdesi; 2026-08-07 gecesi, kaynak: canlı risk turu)_
**BU WP'NİN DOĞUŞ SEBEBİ:** 2026-08-06 gecesi dört motor pozisyonu KORUMASIZ kaldı ve sistem
bunu fark etmedi. Kök turları üç ayrı kusur ailesi çıkardı; üçü de aynı sınıfın örneği —
**sistem doğru çalışıyor ama kendini yanlış anlatıyor.** Ayrıntı: `docs/KORUNUM-KOK-2026-08-07.md`,
`docs/BAYAT-SERMAYE-KOK-2026-08-07.md`, kartlar `EXE-2026-001-R1/R2`, `EXE-2026-002` (+R1).

- **✅ KAPANDI — koruma×süpürücü çarpışması KÖK DÜZELTME (v220+v221, 2026-08-09, CANLIDA ARTEFAKTTAN DOĞRULANDI):**
  süpürücü (`cancel_open_entries`, alpaca.py:481-487) korumayı artık YAPISAL tanıyor — **iki kemer,
  tek hüküm noktası:** limit bacağı P-KORUMA AİLE kemeri (`KORUMA_COID_ONEK` öneki, v220) + stop
  bacağı OCO GRUP kemeri (grup üyeliğinden türer, yön değil — v221); ayrıca long-only YÖN kemeri
  (satış-yönlü emir giriş olamaz). Koruma sınıfı emir `kept`e `sinif:koruma` gerekçesiyle düşer —
  süpürülmez. KANIT: `alpaca.py` yerel↔canlı md5 BİREBİR (`549b78e…`); broker'da **4 açık koruma
  OCO'su** (`P-KORUMA-20260809-0835-{NUE,EMR,BKNG,AMGN}`, gtc, sınıf=koruma, accepted/held);
  dağıtım #4 korumayı BOZMADI. Operatör 08:35'te panodan onayladı (İLK deneme tarayıcı önbelleğinden
  ulaşmadı — sıfır POST izi; İKİNCİ geçti). **AÇIK-DAVRANIŞSAL:** fixli süpürücü GERÇEK bir EOD
  süpürmesinde HENÜZ koşmadı (piyasa Cuma'dan kapalı) — mantık+md5+broker doğrulandı, ilk davranışsal
  kanıt Pazartesi 13:30 UTC sonrası (`docs/SABAH-TRIYAJI-2026-08-09.md` §0/§iv). "Bir kalem ancak
  artefaktı canlıda doğrulanınca ✅" dersi TUTTU — bağlamsız N6 devir tatbikatı önceki "✅ KAPANDI"
  beyanının yalanını ARTEFAKTTAN yakalayıp bu çarpışmayı yeniden açmıştı.
- **~~⟳ YENİDEN AÇILDI (2026-08-09, N6 tatbikatı buldu — kapanış ARTEFAKTTAN doğrulanmamıştı)~~ → yukarıda ✅ (tarihçe):**
  operatörün v211'le kurduğu 4 bağımsız koruma OCO'su (coid `P-KORUMA-…`) 2026-08-07T20:32:39Z'de
  `cancel_open_entries()` tarafından SÜPÜRÜLDÜ — koruma emri süpürücünün gözünde "dolmamış motor
  girişi" (P- öneki + açık + filled_qty=0); "koruma bacağına dokunmaz" güvencesi yalnız BRACKET'A
  BAĞLI bacağı tanıyordu, v211'in bağımsız OCO'su o fonksiyon yazılırken yoktu. Broker'da 0 açık
  emir / 5 korumasız pozisyon; 16 sev-1 alarmı kanalsızlıktan teslim edilemedi. KÖK DÜZELTME
  ~~UÇUŞTA~~ İNDİ (v220: yön kemeri + P-KORUMA aile dışlaması + olay coid-sınıfı + idempotans
  çivisi; v221: OCO grup kemeri). DERS ROADMAP DİSİPLİNİNE: bir kalem ancak ürettiği artefakt
  canlıda doğrulanınca ✅ olur.
  (Önceki metin aşağıda, tarihçe olarak duruyor:)
- **✅ KAPALI (WP2 cephesi 2026-08-22'de kapandı; kapanış iddiası bir kez geri alınmıştı, ikincisi ölçümle)** · **~~✅ KAPANDI~~ — koruma ölmüyor (E1-v2, v209-v211, canlıda doğrulandı):** bracket TIF'i emrin
  TAMAMINA uygulanıyordu; `day` seçimi dolmuş pozisyonun stop'unu her kapanışta öldürüyordu
  (ölçüm: 08-06 20:00-20:02Z, dört pozisyon çıplak). TIF `gtc`, `day` beyaz-listeden ÇIKARILDI
  (`ENTRY_TIF_ALLOWED`), bayat tetik günlük `cancel_open_entries()` kadansına taşındı. v209
  koruma bekçisi (300 sn, sev-1, payda-beyanlı) + v211 operatör-onaylı OCO yeniden-kurma yolu.
  Operatör 08-07'de panodan onayladı; dört pozisyonda OCO/gtc doğrulandı.
- **✅ SB-4 — DAMGASIZ YAZIM BEKÇİSİ (KAPANDI v216, dağıtım #2 — içerik-sha≠damga parmak izi, 08-04 fikstürlü; Rol-1 önerisiydi, EN ÖNCELİKLİydi):** ölçüldü ki `portfolio.json`
  `store` kapısı DIŞINDAN değişebiliyor — 08-04'teki kitap yazımında `entity_meta.rev` hiç
  ilerlemedi (o gün yalnız iki `_save_broker`, ikisi de kanıtlı). Yani denetim zincirinin bir
  deliği var ve bugün onu gören hiçbir şey yok. Tasarım: tur başı/sonu `entity_stamp` kıyası →
  "kitap bu tur DIŞARIDAN değişti" alarmı. **Bu kalem bir sermaye kalemi değil, bir DENETİM
  kalemidir** — kitap izsiz değişebiliyorsa hiçbir sermaye ölçümü kendi tabanına güvenemez.
- **✅ SB-3 — `taban_kaymasi` satırı (KAPANDI v216 — ters-onarım gerilemesi çivili; en ucuzdu, SB-4'ten hemen sonra):** `recompute`e dördüncü satır
  `realized_pnl − (Σ trades + ofset)`; + `monotonicity_report` tabanına beyan ölçüsü. 08-04
  vakasında bu satır olsaydı ters onarım ANINDA görünürdü.
- **✅ SB-1 — plan başına BOYUT MAKBUZU (KAPANDI v222 `_save_broker` 14. anahtar `size_law` + v226 pano-bacağı `_yama` kalıcılık, dağıtım #4):** `eq_kaynak` (eq_now|nabiz) · `eq_now` · `peak` ·
  `size_mult` · `kitap_rev` · `beyan_n/ofset`. `entry_law` deseniyle, `_save_broker`ın 14. anahtarı;
  reddedilen planda da yazılır. v226 `api.py._yama` bacağı makbuzun restart'ı atlatmasını sağladı
  (loop bacağı zaten kalıcıydı, eksik olan pano/nabız bacağıydı — 08-06 AMGN vakası).
  Gerekçe: 08-05 sapmasını çözmek üç ayrı deftere bakmayı gerektirdi; makbuz tek satırda söylerdi.
- **📋 SB-2 — `MIRROR_DRIFT`e `drift_sinifi` alanı:** **[2026-08-23: ✅ v257 damgası — `ayna_taban` sınıfıyla İNDİ]** `boyutlama_tabani` / `derisk_carpani` /
  `sermaye_kaynagi` / `kitap_kaydi` / `beyan_kaydi` / `icra` / `olculemedi`. Ölçülen gerekçe:
  08-05 gecesi DÖRT MIRROR_DRIFT alarmı bastı ve HİÇBİRİ sebebi adlandırmadı — belirti görüldü,
  sınıf söylenmedi. Aynı jeton koruma alarmıyla da paylaşılıyor (6 saatlik susturma penceresi
  ortak) → ayrı `NAKED_POSITION` jetonu operatör kalemi (obs.py NOTIFY_TOKENS, bir satır).
- **ÖLÇÜLEMEDİ (kapanmadı, beyanlı):** 08-04 kitap yazımını KİM yaptı. Kanıtın yokluğu ölçüldü
  (damgasız). Dışlananlar: replay_seed · iade betiği · ikinci `sermaye --uygula` · migrated
  kopyası · dağıtım/restart/litestream · hermes/api/arm yamaları. SB-4 bu soruyu GELECEKTE
  cevaplanabilir kılar; geçmiş vaka için kanıt yok ve uydurulmayacak.
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — WP2 cephesi kapalı ilan edildi ama bu operatör kaleminin o kapanışa dahil olduğu ölçülemedi)** · **🔒 OPERATÖR — melez pozisyonlar:** iç defter 54/64/43/33, ayna 25/37/22/22 (ayna hedef riskin
  ~%49'unu taşıyor; taban yerinde olsaydı 51/76/45/45 giderdi). Korumalar DOĞRU tarafa (broker
  adedine) kuruldu. Farkın kapatılıp kapatılmayacağı operatör kararı. **[2026-08-23 KAPANDI: Ö-53 kararı (08-22, B+D) — taban birleştirme + `_adet_benimse` sınıfı (v258) çözdü; 54/64/43/33 ↔ 25/37/22/22 sayıları 08-07 penceresinindi — tarihçe]**
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — aynı sınıf: `dormant_setup` yolunun bugünkü hâli canlı defter ister, cloud klonundan okunamaz)** · **🔒 OPERATÖR — uyuyan kurulum yolu:** `dormant_setup` 31 plan üretti, **0 işlem** çıktı, biri
  GO hükmü aldı ve yine işleme dönmedi (kapı geçirdi, arkasında tüketen yok). `conservation.
  unexplained = 14` = 31 uyuyan − 17 NO_GO; hesap tam kapanıyor. İcraya bağlamak SİSTEMİN NE
  ALIP SATTIĞINI değiştirir → ön-kayıt kartı + kill-list gerekir. Seçenekler: (a) icraya bağla,
  (b) tavsiye kalsın ama kapı GO vermesin, (c) geri al. Gözlemlenebilirlik tarafı (terminal
  olay · `dormant_unconsumed` ayrı kovası · panoda payda-beyanlı `0/31`) otonom yapılabilir.
- **🆕 AÇIK (denetim A4, 2026-08-13) — DAVRANIŞSAL EOD KANITI HÂLÂ KAYITSIZ:** yukarıdaki "✅ KAPANDI
  koruma×süpürücü" maddesi `:213-217`'de "davranışsal EOD kanıtı Pazartesi 13:30 UTC sonrası ilk
  gerçek süpürmede" diye söz vermişti — **o Pazartesi (2026-08-10) geçti, kayıt YOK.** Kapanış
  hükmü süpürücünün korumayı süpürmemesi hakkındaydı ve o hâliyle tarihçe olarak GEÇERLİ; ama bugün
  koruma **hiç kurulmuyor** (yukarıdaki acil blok) — iki ayrı kusur, ikisi de açık. **[2026-08-23 KAPANDI: v265 — davranış 10/10 seansta ölçüldü + `eod_supurme_report` bekçisi (`wp2_eod_supurme_2026-08-22/`); "koruma hiç kurulmuyor" tarafı da 08-22'de kapandı (korumasız 0/7)]**

#### WP2-B · KORUMA KURULUMU ELLE — OPERATÖR KALEMİ _(taşındı: Ö-27, eski satır :1066-1073 — 2026-08-13)_
_(denetim C3: Ö-27 bir SERMAYE RİSKİ kalemidir ve WP-S'in doğuş sebebiyle birebir aynı sınıf —
canlı risk kalemi backlog'da yaşamaz. Karar bacağı §5 KOVA-2'de, acil eylem bacağı §5 KOVA-1'de.)_
27. **KORUMA KURULUMU ELLE (EDG-038 yan bulgusu + envanter triyajı) — OPERATÖR KALEMİ** — canlıda
    4 pozisyonun (NUE/EMR/BKNG/AMGN) broker'da canlı koruyucu stop'u YOK (`korumasiz_motor_disi_pozisyon`
    26 kez, `MIRROR_DRIFT KORUMASIZ POZİSYON` her biri 6 kez). Kök: `submit_protective_oco`nun tek
    çağıranı `api.koruma_kur` ve o ÜÇ KAPI ardında (ölçüm + operatör onay jetonu + öneri kimliği);
    bekçi çıplaklığı GÖRÜP alarm üretiyor ama KURMUYOR. Ölçülen: `day` TIF bracket'ları gece öldürüyor,
    yeniden kurulum elle. Seans-içi çıplaklık 2,895 saat ölçüldü (0,445 seans — eşiği aşmadı).
    *karar: koruma yeniden-kurulumu otomatikleşmeli mi (risk AZALTAN yön, api.py'nin kendi şerhi bu
    sınıfı onaya bağlamamayı savunuyor) — OPERATÖR.* **[2026-08-23 KAPANDI: karar VERİLDİ — B2=(c) (operatör 08-17, §7); A1 ölçümüyle 08-22'de kapandı (korumasız 0/7, "4 pozisyonun stop'u YOK" beyanı bayat) — tarihçe]**

#### WP2-C · 4 pozisyon adet-sapması muhasebeli true-up _(taşındı: Ö-7, eski satır :765-773 — 2026-08-13)_
7. **4 pozisyon adet-sapması muhasebeli true-up (NUE 54/25 · EMR 64/37 · BKNG 43/22 · AMGN 33/22)** —
   **KÖK ÖLÇÜLDÜ (2026-08-12, Alpaca emir-geçmişi salt-okunur): kısmi-dolum DEĞİL — dört giriş emri de
   TAM dolmuş (25/25 · 37/37 · 22/22 · 22/22, 08-06). Sapma GÖNDERİM-ANI BOYUTLAMA AYRIŞMASI** (SB-1
   makbuz-öncesi dönem; oranlar 0.46–0.67 değişken = tek çarpan değil; AMGN coid'i momentum_burst —
   dormant bir kez aynalanmış, tarihsel). İleri akış SB-1 makbuzuyla korunuyor; geriye dönük yön kararı
   operatörde: (a) kitabı broker-gerçeğine indir (25/37/22/22; iç R-muhasebesi düzeltme-satırlı) ya da
   (b) iki-motor kabulü + drift_sinifi 'makbuzsuz_boyut' (olculemedi yerine açıklanmış sınıf, alarm
   anlamlı kalır). Uygulama her iki yönde de muhasebe-satırlı, SESSİZ DEĞİL. *gerekçe: kitap↔broker
   bütünlüğü · boyut: S-M (kök artık belli) · bağımlılık: operatör yön kararı (§5) · öncelik: yüksek.* **[2026-08-23 KAPANDI: yön kararı VERİLDİ — Ö-53 (08-22, B+D; v258); NUE artık ayrışma listesinde bile değil (08-22: AMGN/BDX/BKNG/CRM/EMR/MRK/MRNA); kalan olsa olsa geriye dönük makbuzsuz-dönem beyanı]**

#### WP2-D · equity_curve ZİNCİRİ — üç bacaklı TEK kalem _(BİRLEŞTİRİLDİ: Ö-9 [:783-789] + Ö-18 [:996-1002], denetim C1 — "aynı nesne, iki madde")_ **[2026-08-23: ✅ v264 damgası — üç bacak 08-22'de KAPANDI (`loop.py:2291+` kadanslı yazar · `ledgerstamp.seed_boundary:269` donmuş-kanıt okuması · pano beyanı); §2 TAHTA H6 satırı — gövde tarihçedir]**

**ÖNCELİK: ACİL (denetim D1 — eski "orta-yüksek"/"yüksek").** Gerekçe: risk artık gelecekte değil
**bugün**. `EDG-2026-036…yaml:175-178`: "`equity_curve` YAZILMADI … Canlı eğri 2026-07-20'de
duruyor (882 nokta). `ledgerstamp.seed_boundary()` bu dosyanın son nokta+mtime çiftini okuyor →
**SINIR ŞU AN TOHUM-SONRASI DEĞİL**." Yani tohum 2026-08-13 18:54Z'de yenilendi ama sistemin
köken-sınırı hâlâ 2026-07-20'yi gösteriyor. Kartın geçici çaresi de yazılı: "o güne dek tohum sınırı
`trades.kaynak` damgasından okunur". Bakım penceresi gerekir (state'e yazar → worker durur, §5-F8).

**ÜÇ BACAK (sıra ZORUNLU):**
1. **`seed_boundary` ONARIMI** — ⚠ **denetim A10: bu adım artık bir ÖNLEM DEĞİL, ONARIM.** Eski
   metin "bugün nokta ekleyen yazar sınırı kaydırıp köken defterini bozar" diye gelecek-riski
   yazıyordu; risk **gerçekleşti ve tersine döndü** (yukarıdaki kanıt). Sınır SON reset-işaretinin
   `egri_son_nokta`sından okunmalı (sınır donar).
2. **Kadanslı yazar** — `loop.daily_cycle` seans sonunda `(date, eq_now)` noktasını `file_lock`
   altında eklesin.
3. **Pano reset-penceresi beyanı** — pano hangi pencereyi gösterdiğini AÇIKÇA yazmalı.

_(Ayrıca Ö-19 TOHUM YENİLEME'nin tek artığı buraya devredildi: `EDG-036 card:174-178` "equity_curve
yazılmadı" — kartın kendisi ✅ UYGULANDI ve §8 arşivde.)_

**Özgün gövdeler (AYNEN korunur):**

_(taşındı: Ö-9, eski satır :783-789)_
9. **equity_curve KADANSLI YAZAR planı (öğrenme-durması turu ölçtü, 2026-08-12)** — canlıda eğriye nokta
   ekleyen HİÇBİR kadanslı yazar yok (yalnız replay_seed tohumu + reset işareti); 149sa bayatlık alarmı
   BİLİNÇLİ görünürlük yaması (Ç1). TUZAK: ledgerstamp.seed_boundary sınırı eğrinin SON NOKTASINDAN okur —
   bugün nokta ekleyen yazar sınırı kaydırıp köken defterini bozar. SIRA ZORUNLU: (1) seed_boundary önce
   SON reset-işaretinin egri_son_nokta'sından okusun (sınır donar); (2) ANCAK SONRA loop.daily_cycle seans
   sonunda (date, eq_now) noktasını file_lock altında eklesin. *gerekçe: pano eğrisi + Ç1 ölçümleri canlı
   akmıyor · boyut: S-M (sıralı 2 adım) · bağımlılık: ledgerstamp→loop sırası · öncelik: orta-yüksek.*

_(taşındı: Ö-18, eski satır :996-1002)_
18. **P&L GÖRÜNÜRLÜĞÜ — equity_curve 24 gün donuk (2026-08-13 ölçümü)** — son nokta 2026-07-20
    (882 kayıt); pano P&L eğrisi bu yüzden hareketsiz ve operatör "P&L yansıtmıyor" diye okuyor.
    Ö-9'un (kadanslı yazar) artık GÖRÜNÜR etkisi var → Ö-9 önceliği yükseltildi. Ek: canlı defter
    toplamı −5.264$ (97 kapanan) iken portfolio `realized_pnl` +278$ — fark 2026-08-01 kâğıt-hesap
    RESET işaretinden geliyor (equity_curve meta `paper_equity_reset` SR-20260801T151429); pano hangi
    pencereyi gösterdiğini AÇIKÇA yazmalı (reset-öncesi/sonrası ayrımı görünür değil). *boyut: S-M ·
    öncelik: yüksek.*


### PRG-03 — Öğrenme Döngüsü 🔴
_(eski: WP3 · WP-L + Ö-28 tıkanıklık + Ö-10 OPT + Ö-19 tohum)_

**KAPSAM (tek cümle):** Hipotezin doğduğu andan ship'e kadar giden döngünün kendisi — önerinin
deftere girebilmesi, kapının ölçebilmesi, tohumun doğru zeminde olması ve merdivenin basamakları.

> **⚠ DURUM DÜZELTMESİ (denetim A1, 2026-08-13):** WP-L'in "📋 tetik-şartlı · kodla açılabilir kilit
> YOK" durumu ÇÜRÜDÜ. Faz-6 BEŞ KİLİT kanıt-şartlı KALIR; ama merdivenin ALT basamağı (öğrenme
> döngüsünün kendisi) **kodla açılabilir ÜÇ tıkanıklıkla** bloklu — 28a/28c/28d. **WP3 artık
> tetik-şartlı DEĞİL, Ö-28-şartlı** ve durumu 🔴.

#### WP3-A · ÖĞRENME TIKANIKLIĞI — KÖK BULUNDU _(taşındı: Ö-28, eski satır :1085-1121 — 2026-08-13)_
_(denetim D2: **EN ÜST öncelik — 28a > 28d > 28c.** 28a bugün 17:26'da hâlâ ateşledi; 28d tüm
öğrenme ölçümünü durduruyor; 28c tek satır ve 21 tekrarın kökü. **UYARI:** 28a'nın kodu kendi
karşı-gerekçesini taşıyor (`hermes.py:4003-4007`) — "tek satır aç" diye sunulamaz, KART-ÖNCE.)_
28. **ÖĞRENME TIKANIKLIĞI — KÖK BULUNDU (`docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md`)** — Rol-1
    hükmü: **KARIŞIM, ama zaman dilimlerine göre** — Temmuz'da kapı HAKLIYDI (H1), 2026-08-02'den
    bugüne döngü TIKALI (H2). Ve tıkanıklık kapının SIKILIĞINDA değil **kapının ÖNÜNDE**.
    · **28a GÖRÜNMEZ SÜZGEÇ (EN ACİL, HÂLÂ AKIYOR):** `hermes_bg_proposal_rejected` — **47 öneri
      deftere HİÇ girmedi**; ~~`hermes.py:3889`~~ **`hermes.py:4002` (repo; olay `:4008`)** arka plan turu `chop` sertifikalıysa GLOBAL (`@`siz)
      her öneriyi atıyor. Aynı pencerede deftere giren: **1**. İlk 2026-08-02T14:00, **son bugün
      17:26**. Yani "52 hipotez" üretimin değil, ÖN-ELEMENİN hayatta kalanları. *öncelik: ACİL.*
      **DURUM (2026-08-14): düzeltme v247'de yazıldı ama DAĞITILMADI — canlıda hâlâ akıyor;
      kuru-koşum akıbet ölçümü Ö-48'de.** **[2026-08-23 GÜNCEL: v247 CANLIDA — 08-22'de en az iki tam dağıtım indi (cbcdeed tur-kapanışı + 5d75dcf Ö-53; rsync tüm repoyu taşır); kart `EDG-2026-041` measured (D1+D2), 28a tahtada H6]**
    · **28b "52 RET" ASLINDA 23:** 22'si TEKRAR (guard hafızası kesti, hepsi tek gün 07-14), 4'ü
      NO-OP (aday bit-bit aynı), 1 ölçülemeyen, 2 ship. Sayı olduğundan büyük görünüyordu.
    · **28c TEKRAR DESENİNİN KÖKÜ TEK SATIR:** `reflect.propose_deterministic`de `already_failed`
      kontrolü YALNIZ `explore` dalının içinde; varsayılan **exploit** yolunda hafıza YOK.
      `stop_loss_atr_mult=2,1` **21 kez** önerildi; arama uzayında 33 adım-üstü değer varken 32'sine
      hiç bakılmadı, ters yön bile denenmedi. *boyut: S · öncelik: YÜKSEK (tek satır, 21 tekrar).*
    · **28d AĞUSTOS'TA ÖLÇÜM DURDU:** 500 sondanın **500'ü** `candidate_oos=NULL` (Temmuz'da 477'nin
      382'si ölçülüyordu). Sebep `inc_cache.json`da yazılı: `chop` dilimi **27 işlem, eşik 30**;
      üçüncü fold'da 0, teyitte 0. Kapı yargı VERMİYOR — **ÖLÇEMİYOR**. Tohum yenilemesi bunu
      ÇÖZMEDİ ve ÇÖZEMEZ (kapı `meridian.db::trades` okumaz, `dataset.load()`+`walk_forward` ile
      kendi örneklemini simüle eder). *öncelik: yüksek — ölçemeyen kapı öğrenmeyi durdurur.*
    · **28e `P=0,000` İKİ GERÇEĞİ AYNI SAYIYLA SÖYLÜYOR:** `p = np.mean(arr > 0)` kesin eşitsizlik →
      bit-bit AYNI aday da 0,000 alıyor. Defterdeki beş 0,000'ın **dördü no-op**, biri gerçek felaket.
      No-op kaynakları: yapısal-atıl düğmeler (`scale_out_r` frac=0 iken, `early_kill_bars` pivot=0
      iken) ve `entry.w_tight None→0.3` = **kodun varsayılanının aynısı**. `bounds.yaml`ın kendi
      `spy_sma_gate` mezar taşının uyardığı zarar üç satırda tekrarlıyor; `regime.vix_backwardation_gate`
      ("veri_yok → atıl") bugün hâlâ 8 kez örneklendi. *boyut: S-M.*
    · **28f SHIP KAPISINDA DELİK:** H00029 (v0003) `confirm_p=null`, `confirm_n_valid=0`, OOS'lar
      `None` — **ölçülemeyen bir no-op ship edildi**. Kapı "ölçülemedi"yi "geçti" sayıyor.
    · **28g EŞİK DUYARLILIĞI (ölçüm, öneri DEĞİL):** P_BASE 0,80→**0 ship** · 0,70→**1**
      (`entry.rs_rating_min@trend_up`) · 0,60→**2**. Yalnız P'ye bakmak yanıltıcı: H00033 P'yi geçer
      ama fold-çoğunluğunda (1/3) düşer. **EŞİK DEĞİŞTİRİLMEZ** — 28a/28c/28d çözülmeden eşiğe
      dokunmak, ölçemeyen bir kapıyı gevşetmek olur.
    · **28h BAŞARI ÖRNEĞİ VAR:** **H00039** — ort.Δ +0,0837, OOS +%58, fold **3/3**, tail ✔; tek
      eksiği P=0,709. KARŞI-KANIT: **H00032** kapının haklılığını kanıtlıyor (arama +0,128 → teyit
      −0,080; kazananın-laneti tam yakalandı). İkisi birlikte "kapı çöp değil ama fazla tek-ayaklı".
    · **28i YAN BULGU (ciddi):** mevcut incumbent `oos_score +0,2354` ↔ `holdout_score −0,5366`
      (sapma 0,772, eşik 0,10) — **savunulan tabanın kendisi holdout'ta sert negatif**. Ayrı kalem.
    · **28j `explore_rate` ÖLÜ:** `goal.yaml`da yazılı ama HİÇBİR KOD OKUMUYOR (tek eşleşme
      `guard.GOAL_KEYS` üyeliği) → Ö-25a kaldırma listesine eklenir. **⚠ DÜZELTME (denetim A13,
      2026-08-13): bu YENİ BİR BULGU DEĞİL, zaten BEYANLI** — `state/goal.yaml:48-53` "explore_rate:
      BİLGİLENDİRİCİ — HİÇBİR KOD OKUMAZ (**K1 denetimi, 2026-07-30**)"; aynısı `backtest_gate`
      (`goal.yaml:40-46`) ve `kill_switch_file` (`:172-175`) için; WP-S2 B-1 bunu **✅ KAPANDI
      (`426b998`)** diye kaydetmişti. Kalem **WP6-B/25a'ya BİRLEŞTİRİLDİ** (denetim C4); açık soru
      "yeni ölü bulundu" değil, **"KALDIR mı, BEYANLI kalsın mı" POLİTİKA sorusu** (emsal:
      `spy_sma_gate` mezar taşı).
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — çapa etiketi kuralının uygulandığı bu turda taranmadı)** · **🆕 ÇAPA ETİKETİ KURALI (denetim A11, 2026-08-13):** yukarıdaki 3889→4002 kayması **v242'nin kendi
  dağıtımından** (`32822c6`) geldi. Bundan böyle ROADMAP'teki her `dosya:satır` çapası **"canlı A1"**
  ya da **"repo"** etiketi taşır; etiketsiz çapa bir sonraki turda bayat sayılır.
- **✅ KAPALI (`28g`/`28h`/`28i` teşhisi 2026-08-22 — gerçek bozulma, ölçüm artefaktı değil; gövde `§8.T`/F)** · **🆕 28i KENDİ KALEMİ (denetim §G, 2026-08-13 — "Ayrı kalem" deyip bırakılmıştı):** `TESHIS…:472-474`
  "`oos_score = +0,2354` · `holdout_score = −0,5366`; sapma 0,772, `reflect.HOLDOUT_DIVERGENCE = 0,10`
  … **savunulan tabanın kendisi holdout'ta sert negatif**". Fold geometrisi ÖLÇÜLMEDİ (`:475-479`).
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — geçmiş retlerin yeniden değerlendirilip değerlendirilmediği ölçülemedi)** · **🆕 GEÇMİŞ RETLERİN YENİDEN-DEĞERLENDİRİLMESİ (denetim §G, 2026-08-13):** kapının örneklem tabanı
  6× büyüdü (`TESHIS…:427-434`: ~32 → ~90 → **560**); "Bu, 30 backtest-değerlendirmesinin tamamını
  farklı bir tabana taşır" (`:432`). Soru: hangi ret bugünkü örneklemle ayakta kalır?
- **✅ KAPALI (`config.py` `URETIMI_DURAKLATILAN_REJIMLER=("chop",)` + `config.py`'nin kendi ÖLÇÜLMÜŞ-POLİTİKA damgası: harita bilerek boş)** · **🆕 `params_by_regime` DÖRT HARİTA DA BOŞ (denetim §G, 2026-08-13):** `DENETIM-OLU-BILESEN…:184`
  "rejim çözümü kimlik fonksiyonu". Ö-25c'nin DİRİLT listesinde duruyor ama Ö-12'nin kapanmasıyla
  **yakıtsız kaldığı** görünmüyor; kökü 28d ile AYNI (chop 27 < 30) → 28d ile birlikte çözülür.

#### WP3-B · OPT — parametre-evrim boru hattı _(taşındı: Ö-10, eski satır :791-802 — 2026-08-13)_
_(denetim C7/D10 YENİDEN SIRALAMA: **Faz-1 (kablolama) SERBEST ve yüksek KALIR · Faz-2 Ö-28d'ye
BAĞIMLI.** Gerekçe: OPT'un "ilk müşterisi" Ö-12'ydi ve kapandı (EDG-028 ölçümlü-red) — o rol
BOŞALDI; yeni ilk müşteri adayı **WP11/15d PIT-temiz faktör seti**. Faz-2 "kâğıt-OOS kapılı arama"
demek, ama `TESHIS…:98` "Ağustos'ta ölçülen sonda sayısı **SIFIR**", `:109-111` "Kapı … **ölçemiyor**".
OPT'un freni "PBO 0.6286" cümlesine ek: **fren ancak kapı ÖLÇEBİLİYORSA frendir.**)_
10. **OPT — parametre-evrim boru hattı (elle-değerlerin otomasyonu; operatör sorusu 2026-08-12)** —
    iskelet VAR (bounds arama-uzayı + hermes önerici + DSR/PBO/OOS/K kapıları + gölge varyantları; dün
    onarıldı), ÜÇ EKSİK: (1) KABLOLAMA — aranamaz sabitler parametrize (derisk bandı fonksiyon-gövdesinde
    sabitti, monkeypatch gerekti; max_open/size_r/scale_out/chandelier bounds'a — sınırlar operatör onaylı);
    (2) REPLAY-SWEEP otomasyonu — kart→koşum→CI→hüküm şablonu (bu hafta 5× elle) gece A1-nice penceresinde
    (operatör tercihi) makineleşir, K-deflate'e çarpılı sayılır; (3) UYGULAMA POLİTİKASI sınıf-başına — Rol-1 ÖNERİSİ (2026-08-12,
    operatör onayı bekler): HEP-PENCEREYE = risk-artıranlar (rampa/slot/boyut/ısı) + eşik-gevşetme
    (strateji kimliği); DONUK-EŞİK-OTOMATİĞE = çıkış-parametre iyileştirmeleri, skor-ağırlıkları
    (gölge-doğrulamalı), kurulum-silahlanma (025 emsali, operatör seçti), ölçüm/görünürlük. Tek cümle:
    'vanaları pencere açar, kenar-iyileştirmeleri kapılar içinde makine evriltir.' FREN: PBO 0.6286 — otomasyon kapıların İÇİNDEN akar. *gerekçe: elle-optimizasyon
    ölçeklenmez · boyut: M-L (3 aşama) · bağımlılık: 023-027 karar penceresi + örneklem birikimi ·
    öncelik: yüksek (karar penceresinden sonra ilk büyük iş).*
- **SIRA ARTIĞI (Ö-11 karar penceresinden devralındı, denetim B1):** "pencere → FİNAL-PAKET
  doğrulama koşumu → TEK goal/bounds dağıtımı → **hemen OPT Faz-1 kablolama**" — pencerenin ilk üç
  adımı 2026-08-12'de TAMAMLANDI (§8 arşiv), kalan tek adım OPT Faz-1'dir.

- **🟡 DOĞRULANMADI (2026-08-31 denetimi — M11 kova-6 bulgusunun akıbeti bu turda izlenmedi)** · **🆕 M11 TARAMASI BULGUSU (2026-08-24, kova-6; `docs/TARAMA-KOVA6-ALAN-MERCEGI-2026-08-24.md`):
  GÖLGE-MODEL TERFİ KAPISI YAPISAL OLARAK ERİŞİLEMEZ.** Canlı ölçüm: 893 işlemin **535'i** hiçbir
  plan satırına birleşmiyor (plan defteri tam 500'e kırpılmış); `p_win_shadow` damgalı 25 planın
  yalnız **6'sı** birleşiyor, `PROMOTE_MIN_N=30` → kapı hiçbir zaman dolamaz. ZİNCİR: EDG-052'nin
  bulduğu retention kusuru → v274 kırpma KURALI indi (02c91ca, ileriye dönük) ama GEÇMİŞ kırpılmış
  kaldı → `ops/plan_geri_doldur.py` kaynak-engelli (kırpma-öncesi yedek yok; şasi yeniden-koşumu
  kaynak olabilir). SONUÇ: gölge-model terfi hattı geri-doldurma yapılana dek ÖLÇÜLEMEZ; bu bir
  kapı arızası değil VERİ arızasıdır. *öncelik: yüksek (öğrenme hattının sessiz tıkacı) · sahibi
  WP3 + WP4 (geri-doldurma kaynağı).*
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — `exploration`/`carried` üretiminin bugünkü hâli canlı defter ister)** · **🆕 M11 BULGUSU — `exploration` + `carried` ÜRETİMİ SIFIR:** ikisi de gerçek davranış dalı
  (`loop.py:1636` çıkış gevşetmesi · `loop.py:1239` plan düşürme) ama 41 günde `exploration_armed`
  **1**, `armed_no_bar_carried` **0**; 0/500 plan, 0/893 işlem, 0/7 pozisyon. Pano keşif çipini
  gösterdiği için sistem "keşif yapıyor gibi" görünüyor — 25d ezilme zincirinin (c-4 keşif kuraklığı)
  canlı ölçümlü teyidi. *karar: damgala mı, debiyi aç mı — kart-önce; ROADMAP-25d ile aynı aile.*

#### WP3-C · Merdiven ve Faz-6 kilitleri _(eski WP-L gövdesi; tetik-şartlı basamaklar)_
- Y5 meta-labeling (tetik: işlem birikimi — WP-R rampayı serbestleştirirse hızlanır) · Y7 ML
  sıralama (tetik: evren genişlemesi WP-U) · intraday 4a saha kanıtı (tetik: ilk silahlı plan) →
  4b gölge → Faz 5 kanıt → Faz 6 BEŞ KİLİT (değişmedi) · 6.1 guard-ret oranı izleme.
- **MERDİVEN DURUMU ÖLÇÜLDÜ (2026-08-07, canlı):** 4a defteri 7.541 satır — ama bu DAKİKA BARI
  değerlendirmesidir, "emre dönebilecek karar" DEĞİL (Rol-1 bu paydayı bir kez yanlış okuyup
  "tıkanıklık" sandı; kart `EXE-2026-002` yanlış paydayı adıyla yasaklıyor). 4b gölge defteri
  4 dolum. Faz-6 zinciri **1/5** — açık olan tek kilit operatör onayı (`INTRADAY_ARM`).
- **✅ Faz-5 kilidi artık ÖLÇÜYOR (v212, kart `EXE-2026-002` + R1):** `durum` `olculemedi` →
  `olculdu`. Gerekçe "üreten kod yok"tan "ÖRNEKLEM YETERSİZ (4/20)"ya döndü — birincisi hiç
  dolmaz, ikincisi işlem biriktikçe KENDİLİĞİNDEN dolar. Ölçüm: n_eşleşen 4/4 (kill#4 %0),
  ortalama −9,69 bps / −0,015R; CI **hesaplanmadı** çünkü `n_kume=1` (dört dolum tek gün) —
  tek kümeden aralık üretmek genişliği sıfır bir CI verip kilidi HAK ETMEDEN açardı.
  Tarih-kümeli bootstrap ayrıştırıcı testle kanıtlandı (aynı gün ikizlenen gözlemde kümeli
  aralık %0 değişiyor, düz bootstrap %30 daralıyor). **Bu kalem KOD İSTEMEZ, İŞLEM İSTER.**
- **ASKIDA:** kanıt-şartlı (Faz-6 beş kilit — tahtada DİK DURUM satırı) · ~~Kalan üç kapalı kilit (edge 1/5 · sonuç 0/4 · DSR 1e-06) KANIT eksikliğinden kapalı; kodla
  açılamaz, kârlı işlem geçmişi ister. Merdivende kodla açılabilecek kilit KALMADI.~~
  **→ İKİ DÜZELTME (2026-08-13):**
  **(A1)** "Merdivende kodla açılabilecek kilit KALMADI" cümlesi **YANLIŞ**: kilitlerin kendisi
  kanıt-şartlı kalır, ama merdivenin ALT basamağında **kodla açılabilir ÜÇ tıkanıklık** ölçüldü
  (WP3-A / 28a·28c·28d) ve biri **2026-08-13 17:26'da hâlâ ateşliyordu**.
  **(A2)** **DSR 1e-06 sayısı BAYAT: yeni değer 0,0391** — `EDG-2026-036…yaml:166` (aşama-2 KAPILAR):
  "DSR 0,0391 (kuru koşum 0,0391 ile birebir)", tohum yenilemesi sonrası. ⚠ "Kilit AÇILDI mı" ayrıca
  doğrulanmalı — denetim bunu ÖLÇMEDİ, yalnız girdi sayısının değiştiğini ölçtü.

### PRG-04 — Veri ve Evren 🔶
_(eski: WP4 · WP-U Evren/PIT + WP-D Veri Bütünlüğü + Ö-8 MNST split)_

**KAPSAM (tek cümle):** Ölçümün girdisi — barın/karantinanın bütünlüğü ile evrenin kendisi
(survivorship-serbest üyelik, delist-bar, split/corp-action sadakati).

#### WP4-A · Evren/PIT cephesi _(eski WP-U gövdesi; araştırma indi 2026-07-31; stratejik ana cephe)_
- **ÜYELİK ÇÖZÜLDÜ (ücretsiz):** S&P500 tarihî üyelik 1996→bugün repo'da
  (`research/pit_universe/sp500_uyelik_tarihi.csv`, 2.719 satır, MIT — fja05680). S&P400/600 için
  hazır ücretsiz set BULUNAMADI (yfiua desteklemiyor — araştırma iddiası düzeltildi); alternatif:
  SEC 13(f) resmî listesi (2004Q1→, likidite-evreni; CUSIP→ticker emeği).
- **SERT KISIT (2026-08-02 SAYILANDI — EDG-018 kapı ölçümü):** delist-bar boşluğu ölçüldü:
  endeksten çıkmış 703 ismin yalnız 12'si arşivde barlı (%1,71); EDG-016 panel-penceresindeki
  çıkışların **%96,57'si SIFIR bar** (338/350) ve 12 barlının hepsi 2024+ (ikinci-seçilim).
  Survivorship şerhi artık kapsama-yüzünde sayı; iki yaşayan sinyalin büyüklüğü delist-bar
  kaynağı gelmeden ölçülemez — operatör kararının fiyat-etiketi bu. Kanıt:
  research/olcumler/wp_u_midcap/. EDG-018 askıda:veri-kapısı. Yollar (2026-08-03 QC-araştırmasıyla YENİDEN ÇERÇEVELENDİ —
  docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md): iki yol RAKİP DEĞİL TAMAMLAYICI. (a) QC platform-içi
  ölçüm hattı — BEDAVA, BUGÜN (EDG-021 deseni kalıcılaşır; ToS verinin dışarı çıkışını kilitler,
  içeride ölçüm serbest); (b) Massive yükseltme — YEREL ARŞİVİN tek meşru yolu (operatör kararı;
  QC bunu ikame edemez — 'internal LEAN use only').
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — Massive planının bugünkü kapsamı canlı sondaj ister)** · **⚠ OPERASYONEL BULGU (canlı sondaj):** mevcut Massive planı artık yalnız ~SON 2 AYI veriyor —
  2004'e giden yerel bar arşivi yeniden üretilemez KALINTI; arşiv kaybı = kalıcı kayıp → yedek
  zinciri kritikliği ↑ (VM-içi tar + Mac-pull mevcut; üçüncü kopya değerlendirilebilir).
- Sonrası: PIT-evrenli G1 mid-cap ölçümü (üyelik verisi hazır; bar kısıtı yalnız delist-isimleri
  etkiler — sağ-kalan mid-cap'lerle ÜST-SINIR ölçümü yine mümkün, yanlılık beyanlı) → B-9 (tetik:
  trend kolu ship) · 13F önceliklendirme katmanı.
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-U-2026-08-09.md`, salt-ölçüm + plan):** canlı evren **251 =
  REPLAY_UNIVERSE** (aynı küme, fark YOK — "251" zaten `REPLAY_UNIVERSE`'ün kendisi). FINVIZ evren-
  genişletme kolu **%100 ÖLÜ** — `finviz_unavailable` **3.746** / `finviz_universe` (başarılı keşif)
  **0** (2026-07-14→08-09), `FINVIZ_API_KEY` YOK → evren kalıcı 251. **RAKİP KÖK:** de-risk rampası
  günlerin **%92**'sinde pozisyonu 1'e kısıyor (ROADMAP:425) → **"evren +X → işlem +Y" ÖLÇÜLEMEDİ**
  (bilerek uydurulmuyor: aday-havuzu mu, tavan mı bağlıyor belirsiz). ÖNERİ **EDG-2026-022** ("Evren
  bağlayıcı kısıt mı?" — OTONOM/bloksuz; altyapı hazır: `backtest.py` candidate_log + eff_max_open +
  plan_log; yeni bar GEREKMEZ): FINVIZ harcamasını **DE-RISK eder** (evren bağlamıyorsa para boşa). **[2026-08-23: kart 08-09'da ÖLÇÜLDÜ — status: measured; öneri metni tarihçedir]**
  PIT fundamentals **EDGAR'la ÇÖZÜLÜ** (evrene bağlı otonom kol, blok değil). Delist-bar: 703 çıkıştan
  yalnız 12'si arşivde barlı (%1,71); EDG-016 penceresi %96,57 sıfır-bar (kaynak kararı §8-9'da).

#### WP4-B · Veri bütünlüğü _(eski WP-D gövdesi)_
- **BULGU-1 ✅ TEYİT-TAM (2026-08-03 bağımsız yeniden-üretim — kanıt research/olcumler/
  wpd_bulgu1_teyit/):** 4/4 vaka bugünkü kapıda KARANTİNA; evren geneli birebir (259 defter /
  1.343.892 satır / yeni-kural 13 yakalar, eski 3); yeni kaçak %0 → karantina-genişletme kalemi
  KAPANDI (uygulanacak kaçak yok). DÜZELTME: eski kaçak payı %29 değil **%77 (10/13)** — sayı
  doğru, pay yanlıştı.
- **bars_integrity ✅ ZATEN-SEVK (2026-07-31 adapters/data.py; teyit 2026-08-03 —
  wpd_bars_integrity_teyit/):** defter 98 kırılma/61 sembol (eski "97" düzeltildi); kanonik
  tüketiciler (component_ic/cf_backfill/trend_shadow) kablolu, 46.256 satır/57 sembol dışlanıyor,
  ayrışma 0; 26 test yeşil. AÇIK BİLET (operatör kararı): `dataset.load` bilerek bağlanmadı —
  walk-forward/prescreen/reflect kirli dönemi hâlâ görüyor.
- **✅ KAPALI (2026-08-24: üretici üçlüsü dışlama kapısına kablolu, yeniden üretim gecelik-otomatik; gövde `§8.T`/F)** · ~~türetilmiş
  artefaktların (component_ic/cf/eşik eğrileri) güvensiz-dönem-dışlamalı yeniden üretimi~~ ·
  BMO/AMC alanının ileri-birikimi (data.py `time` alanı — EAP öldü, kalan değer blackout
  hassasiyeti; DÜŞÜK öncelik) · earnings kapsaması 194/251 + fail-open daraltma · ~~5.3 seans-içi
  kesinti/boşluk tespiti~~ · ~~earnings 2-gün marj~~ (2026-08-02 KEŞİFLE KAPALI: aaa7a40+653c121 türetimli çözmüş, marj=9g, çivi v147'de).
  **[2026-08-24 KAPANDI-BAYAT — türetilmiş artefakt yeniden üretimi:** kalem "bir kez yeniden üret"
  diye doğmuştu; bugün yeniden üretim YAPISAL ve DAMGALI — üretici üçlüsü dışlama kapısına kablolu
  (`component_ic.py:348,373` · `cf_backfill.py:178,191` · `threshold_curve.py:110-140` aynı
  popülasyonu `cic._load_universe()` üzerinden tüketir), P5 döngüsü her gün koşuyor
  (`loop.py:2156-2167`) ve canlı artefaktlar 2026-08-21 20:33 taze; `component_ic.json` içinde
  `bars_integrity` bar-taban damgası VAR (dışlama-sonrası üretim kanıtı). cf defteri tarihçe
  satırları yerinde yeniden yazılmaz ama her kanonik tüketici OKUMA ANINDA aynı kapıdan filtreler
  ve cf satırı depo yasası gereği hüküm taşımaz. Kalemi açık tutmayan iki tek-satırlık kuyruk NOT
  olarak düşülür: (a) `threshold_curve.json` KENDİ bar-taban damgasını taşımıyor (YASA-6 tamlığı
  için `component_ic`'teki `_bars_taban()` deseninin tek satırlık kopyası); (b) cf tarihçe
  satırlarının filtre-anında dışlandığı beyanı. Belge: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A1.**]**
  **[2026-08-24 KAPANDI-BAYAT — 5.3 seans-içi kesinti/boşluk tespiti:** satır SEVKTEN ÖNCE yazılmış
  ve bayat. Dedektör canlıda çalışıyor: `scheduler._intraday_gap_check` (`scheduler.py:826`, her
  5-dk poll) → `barsarchive.gap_scan` (60-dk kuyruk penceresi, gerçek-seans takvimi, `takvim_yok`
  fail-declared zinciri); sevk aaa7a40 (2026-08-01) + 58e4a82/8dc7c8b (2026-08-02, çivi v175).
  Canlı olay defteri 2026-07-14→bugün **3.321 `intraday_gap_detected`** / 15 seans günü, son
  ateşleme 2026-08-21; kırılım **3.321 `sembol` · 0 `akis`** — gerçek besleme-kesintisi sınıfı hiç
  doğmadı. Sembol sınıfı ÖLÇÜLMÜŞ YAPISAL GÜRÜLTÜ (IEX tek borsa; 15 rastgele alarmın 15'i
  konsolide beslemede DOLU, `scheduler.py:803`), seviyesi bilerek info'ya indirilmiş. "Genişletme"nin
  bugün ölçülmüş tüketicisi yok ve sinyal değil alarm hacmi büyütür; yeni bir kesinti sınıfı kanıtı
  doğarsa YENİ kalem olarak açılır. Belge: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A2.**]**
  **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1) — earnings kapsaması + fail-open daraltma:**
  satırdaki **194/251 sayısı BAYAT** — bugün ölçülen kapsam **216/251 (%86,1)** (canlı `earnings.csv`,
  son tazeleme 2026-08-17 × `REPLAY_UNIVERSE`=251); kapsam dışı 35 sembol ve kapsam MEVSİMSELDİR
  (tazeleme penceresi [bugün−7, bugün+21 → KART ÖN-KAYITLI: `EDG-2026-055` (3ddafb1)]). Tazeleme hattı sağlıklı (son arıza uyarısı 2026-07-19).
  Fail-open BEYANLI tasarım ama GERÇEKLEŞMİŞ bedeli hiç sayılmadı — daraltma tasarımına girmeden
  önce bedel sayılır. Kart taslağı: retro sayım — her CANLI giriş anında sembol kapsam-dışı mıydı ×
  sonradan öğrenilen gerçek rapor tarihi girişten ≤5 gün sonra mıydı (PIT anlık görüntüsüyle,
  BUGÜNKÜ takvimle DEĞİL; `state/history/earnings_snapshots.jsonl` 2026-08-01'den beri birikiyor →
  retro ve sızıntısız). K-tahmini: hükümlü hücre **1** (grid yok; kalan çıktı betimleyici). Donuk
  eşik taslağı: vaka **N≥1** → "daraltma tasarımı" WP4 iş kalemine döner (aday yollar: kapsam-dışı
  sembole FMP nokta-sorgu · kapsam-dışılık ≥X gün sürerse sembol-bazlı fail-closed); **N=0** →
  fail-open beyanlı kalır ve kalem ÖLÇÜLMÜŞ-RETLE kapanır.
  Belge: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A3.**]**

#### WP4-C · MNST split sınıfı _(taşındı: Ö-8, eski satır :775-781 — 2026-08-13)_
8. **MNST split sınıfı — TEŞHİS ✅ (docs/TESHIS-MNST-SPLIT-2026-08-12.md); düzeltme KART-önce açık** —
   MNST 1→2 (08-11, Massive splits dış-doğrulama). Kök: kaynak-kıyas kör-yüzde (oran-imza tanımaz); defter
   DOĞRU retro-değişmez. Yön: A1 oran-imza + A2 kümülatif-katsayı defteri (kart ön-kayıtlı ölçüm-değişikliği).
   YAN: corp-action FLAP (GE 34 reset/26g) aynı körlük ailesi; MNST turnover ~2× şişme izlemede. *(eski madde:)* — DATA_QUALITY: nasdaq 91.43 vs massive 45.72
   (%50) + ledger_matches_bars 2 sapma (T00020/T00095 MNST defter-entry bar'ın 2 katı). Bar zinciri split'e
   ayarlanmış, trades satırları ham kalmış görünüyor. Teşhis + tutarlılık kuralı (defter mi bar mı düzeltilir,
   retro-değişmezlik gözetilerek). *gerekçe: ölçüm tabanı tutarlılığı · boyut: S-M · bağımlılık: yok · öncelik: orta.*
   **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1):** teşhis TAM ama kart YOK ve kod YOK
   (`research/cards/` içinde split kartı bulunamadı; `oran-imza`/`ratio_signature` için repo
   genelinde 0 eşleşme). Canlı semptom BUGÜN SESSİZ — `data_quality.json` (2026-08-21)
   `index_ok: true`, `tickers_failed: [ → KART ÖN-KAYITLI: `EDG-2026-056` (3ddafb1)]`, `data_halt: false`, `crosscheck: source_lagging`
   (MNST vakası değil): nasdaq tabanı yetişmiş, %50 yanlış-alarmı geçmiş. AMA yapısal körlük
   DURUYOR — evrende bir sonraki split'te aynı yanlış-alarm + defter-bar kırmızı sınıfı yeniden
   doğar. Kart taslağı (A1 oran-imza tanıma): `_massive_crosscheck` sapması `dev > MASSIVE_TOL`
   iken oran kümesi {1/4, 1/3, 1/2, 2, 3, 4} × TEK tolerans ile "taban-farkı" sınıfına ayrılır;
   retro doğrulama penceresi 2026-07-14→bugün + Massive `/stocks/v1/splits` dış-takvimi (PIT).
   K-tahmini: hükümlü hücre **1** (tek kural + tek tolerans; oran kümesi SABİT, taranmaz). Donuk
   eşik taslağı: retro pencerede bilinen split günlerinde (MNST 2026-08-11) yanlış-alarm **1→0**'a
   iner VE split-dışı günlerde sapma sayımı değişmez (**yanlış-pozitif 0**) → A1 sevk edilebilir;
   A2 kümülatif-katsayı defteri AYRI adım (tohum kırmızılarını "bilinen katsayı 2×" beyanlı-yeşile
   çevirir, retro-değişmezlik korunur). ÖLÇÜLEMEYEN (uydurma yasağı): `ledger_matches_bars`
   gece-deep güncel çıktısı = **None** (kalıcı artefakt dosyası yok; pano yolu yalnız canlı dilime
   bakar, `recompute.py:187-189`) — T00020/T00095 tohum kırmızılarının bugünkü hâli okunamadı.
   Belge: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A4.**]**


### PRG-05 — Ölçüm Altyapısı 📋
_(eski: WP5 · WP-M + WP-S2 + Ö-4 DSR aracı + Ö-14 M8 + Ö-20 eşik envanteri + Ö-16 korunum)_

**KAPSAM (tek cümle):** Ölçümün kendisinin doğru olması — metodoloji/yasa borçları, beyanlı
görünürlük borçları, K-defteri muhasebesi, paket-bağımlı eşik envanteri ve korunum kovaları.

#### WP5-A · Metodoloji/yasa borçları _(eski WP-M gövdesi; ölçüm altyapısının kendisi)_
- **YENİ (EDG-010'dan, ders #3): ölçütler HAM getiri okuyamaz** — success/kill her zaman
  taban-fazlası (aynı-gün evren / ilgili alt-evren) üzerinden yazılır; ham pozitiflik piyasa
  sürüklenmesidir (EDG-010 vakası: lafzen-success, kanıten-kenarsız).
- **YENİ (EDG-009'dan): kart eşik-DİLBİLGİSİ standardı** — success/kill metinlerinde her dal
  KENDİ niteleyicisini açıkça taşır ("artar (CI 0-dışı)" gibi); belirsiz niteleyici = muhafazakâr
  okuma + karta ders notu (EDG-009 vakası: "(P>=0.95)" hangi dala ait belirsizdi, hüküm değiştirici).
- **YENİ (WP-G tanısından, SINIF bulgusu): "oosonly" kolu STANDART** — walk_forward tek-parça
  replay koştuğu için IS'e dokunan HER overlay/knob OOS skorunu portföy-durumu kanalıyla
  (peak_equity/derisk/açık pozisyonlar) kirletir; bundan böyle knob ölçümlerinde knob'u
  oos_start'ta devreye alan kol zorunlu (kanıt: EDG-005 tanısı — oosonly≡kapali bit-bit).
- ~~PARA-v3 ①②~~ ✅ (①: 2026-08-01 + zincir-çivisi v178; ②: 2026-08-02 kapı-bacağı — ölçülür,
  veto-bağlamaz [MERIDIAN_DD_MTM_VETO kapalı; bağlama = M2M-σ ölçüm kartı]). ÜÇ KAYIT DA KAPANDI (2026-08-03 uygulama dalgası):
  (i) ✅ probgate birim-karışımı — teşhis: mekanizma muhafazakâr değil ÖLÜYDÜ (para-v3 altında
  yeni çift sayılamaz, extra_p yapısal 0). Rol-1 kararı SEÇENEK-1: rollback para-ikizi
  (realized_detail.delta_para, tek payda span; hüküm BİLEŞİK kaldı — eşik satırı çivili) +
  damga BEYAZ-LİSTESİ (bilinmeyen damga sayılmaz — para_v4-dirilme sınıfı ölü, negatif testli)
  + durum alanı {olculdu/kurak/askida_olcek_borcu} (extra_p askıda/kurakta 0,0 kalır); watchdog
  askıda≠starved ayrımı. 17 yeni test + 169 regresyon. AÇIK KUYRUK: hermes.py:644 ship_calibration
  askıda-durumu beyne taşımıyor (ayrı tur). (ii) ✅ canlı gate_calibration izlemesi — yeni koşumda
  durum alanıyla kendini beyan eder. (iii) ✅ DD_VETO_MARGIN okuma netliği — ledgers sözleşme notu
  (dd_mtm_* ailesi dahil) + analytics._dd_veto_okumasi ölçülü-oran (marj/tavan her çağrıda; mutlak
  çıpa goal.max_drawdown) → pano YASA-6 zinciri api.py:2279. · ~~2B blok-bootstrap CI standardı~~ · ~~2C empirical-Bayes küçültme~~ ·
  2D R2 holdout rotasyonu (zamanı gelince) · ~~A4 tahmin-isabeti bandı~~ · KIYAS-KİRLENMESİ düzeltmesi
  (olay-penceresi-dışı kıyas — EAP yan bulgusu; tüm evren-medyanı ölçümleri etkileniyor) ·
  ~~prescreen raporlarına kod-sürümü damgası~~ · PK4/PK5 yol-tutarlılık kontrolleri ölçüm-şablonu
  standardı · K-defteri↔kart senkronu (retro kartlar) · ~~canlı-beklenti tavanı config'e bağlama~~ (2026-08-03 TEYİT: 5fe0c1e'de ZATEN kablolu —
  config.live_expectancy_rule + analytics.live_expectancy_ceiling → pano; kayıt bayattı) · ~~Chen-2022 t-hurdle dengeleme notu (K-cezası
  kalibrasyonu — gevşetme değil referans)~~.
  **[2026-08-24 — STOK KAMPANYASI ELEME HÜKÜMLERİ, yukarıdaki listenin ALTI kalemi — beşi KAPANDI-BAYAT, biri (2D) TASARIM-KAPANIŞI (belge: `docs/ELEME-WP5-2026-08-23.md`):**
  · **M7 prescreen kod-sürümü damgası — KAPANDI-BAYAT:** YAPILMIŞ —
  `olcum_araclari.kod_surumu_damgasi` (`:761`) + prescreen DÖRT noktada damga yazıyor
  (`prescreen.py:186,243,277,390,429`), çivisi `tests/test_wpm_sasi_v173.py`; iniş **4b84871,
  2026-08-02** (blame `:186` doğrulandı). Not: 2026-08-09 KESIF-WP-MKP bunu inişten BİR HAFTA SONRA
  hâlâ açık listelemişti — Ö-49 bayat-beyan sınıfının bir örneği daha. *(#2)*
  · **2B blok-bootstrap CI standardı — KAPANDI-BAYAT:** YAPILMIŞ — genel standart
  `olcum_araclari.blok_bootstrap_ci` (sözleşme "1.0", `:41,:482`; moving-blok, n^(1/3)), iniş
  4b84871 (2026-08-02, WP-M şasi). İki beyanlı ikiz BİLİNÇLİ ayrı: `analytics._blok_bootstrap_ci`
  (circular, işlem-ekseni, yayımlanmış hüküm tabanı — `analytics.py:1819-1828` yazılı gerekçe) ve
  `benchmark_relative`in IID'si (bilinçli değişmedi, 2. ölçüt hükmü kaymasın). "Standart + beyanlı
  istisna" tam olarak kalemin istediği son durumdur. *(#6)*
  · **2C empirical-Bayes küçültme — KAPANDI-BAYAT:** YAPILMIŞ — `analytics._empirical_bayes`
  (`:3304`) + `shrunk_regime_cells` (`:3355`) → `/api/diagnostics` (`api.py:4570`) → panoda
  çiziliyor (`app.js:5828`); ikiz `olcum_araclari.eb_kucult` beyanlı (`analytics.py:3311`); iniş
  4b84871; τ²=0 bulgusu v125 arşivinde işlenmiş (ROADMAP §8). *(#7)*
  · **2D R2 holdout rotasyonu — TASARIM-KAPANIŞI:** R1 uygulandı (2026-07-30, `dataset.py:58-118`
  tam tarihçe) ve R2 için CANLI TETİK ZATEN KURULU — `holdout_rotation_advice` ölçer-önerir-
  uygulamaz (`dataset.py:158` YASA-6 şerhi) ve panoda görünür (`app.js:5828` `holdout_rotation`);
  sorgu basıncı limit **20**'nin çok altında (canlı 08-10 ölçümü 4 pencere). Kapanış paragrafı:
  *"R2'nin sahibi ROADMAP değil `holdout_rotation_advice`tir — advisor ROTASYON ÖNERİLİR dediği gün
  operatör kararıyla R1 usulü tekrarlanır (maliyet beyanı: fingerprint değişir, geçmiş p/ΔS
  kıyaslanamaz)."* Takvimle değil TETİKLE yaşayan bir kalemi stokta tutmak çift-defterdir → stok
  satırı düşürülür; kalan mini-iş hafta-1 partisinde. *(#8)*
  · **A4 tahmin-isabeti bandı — KAPANDI-BAYAT:** YAPILMIŞ ve ESKİ — `prediction_accuracy_band` ilk
  git commit'te bile var (d9c3f24, 2026-07-31; v125 dönemi); n<3'te bant UYDURMUYOR
  (`A4_BAND_MIN_N`, `analytics.py:2699`); para-ölçeği sütunu v178'de eklendi; okuyucuları gerçek —
  hermes kendi karnesini OKUYOR (`hermes.py:1059-1070`) + pano (`api.py:4541 hermes_scorecard`). *(#9)*
  · **M9 Chen-2022 t-hurdle dengeleme notu — KAPANDI-BAYAT:** YAPILMIŞ — dengeleme referansı hem
  koda yazılı (`analytics.py:2590-2607` — "BU NOT BİR GEVŞETME DEĞİLDİR" + UYDURMA-YASAĞI künye
  şerhi) hem standartlar belgesinde (`docs/olcum_standartlari.md:348`); iniş c9aee5e, 2026-08-10.
  F13 yüzey bacağı WP8'in — WP5'te iş kalmadı. *(#4)***]**
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-MKP-2026-08-09.md` §WP-M — salt-ölçüm; gece kapananlar v196/v214/
  kart-tekillik düşülmüş):** **11 kalem gerçekten açık** (9 metodoloji/yasa + **PBO/DSR tabanı** [M2,
  M2: damgalama ARTIK ÇALIŞIYOR — kanonik canlı `validation_ledger` **383 satır = 204 damgasız (R1-öncesi,
  retro-damga yasağı gereği sonsuza dek None) + 179 R1-damgalı (R1-sonrası TÜM yeni satırlar)**; oos_erosion
  4 pencere R1 (2026-08-10 Rol-1 salt-okunur canlı ölçüm; önceki gece "831/833" SAYIM HATASIYDI — sprint-sandbox
  kopyalarını da sayıyordu, düzeltildi). Eski "0/204 → NO-OP" dönem bitti: yeni akış %100 damgalı → **M2
  restart-bloğu KALKTI**; kalan otonom = R1 popülasyonunda PBO/DSR taban HESABI (ölçüm kodu → KART gerekir)] +
  **araç-kör-nokta artığı** [M11: KATMAN-4 alan merceği plan defterinin ~20 kontrol alanına genişlemedi]
  **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=0 tarama):** M11 YAPILMAMIŞ ve bugün yeniden ölçüldü —
  repo'da alan-merceği ARACI hiç yok (`meridian/ research/ ops/` grep boş); mercek 08-07
  taramasının OTURUM-İÇİ metodolojisiydi ve `ARTEFAKT-TARAMASI-2026-08-07.md:492-493`'ün "yalnız
  `dormant_setup`a uygulandı, ~20 kontrol alanı sonraki kova" beyanı bugün de doğru. Ara dönemde
  sınıfın DEĞERİ KANITLANDI: uyuyan-yol ve `broker_status` ölü-dalı tam bu körlükten çıktı
  (`watchdog.py:552-560` düzeltme şerhi). Sınıf ÖLÇÜLÜR ama **kart DEĞİL** — 4./5. kova emsaliyle
  **kova-6 salt-ölçüm taraması**: belge-çıktılı, `meridian/` dokunulmaz, **K=0** (grid yok,
  hipotez yok). Maliyet bir gece-ajanı; **kalibrasyon kapısı şart** (kova-4'ün 1/3 dersi).
  Belge: `docs/ELEME-WP5-2026-08-23.md` #5.**]**).
  EN YÜKSEK KALDIRAÇ = **M1 KIYAS-KİRLENMESİ** (olay-penceresi-dışı kıyas — TÜM evren-medyanı ölçümlerini
  etkiliyor; yeni WP-K aile ölçümlerinin tabanını temizler). Öneri sıra: bakım penceresinde OB-2 systemd
  → OB-1 kanal → OB-4 restart→PBO damgalama (M2) çapraz-kaldıraç; sonra M7/M8/M9 ucuz, sonra M1 çekirdek.
- **🆕 YENİ (EDG-038'den, ölçüt-taşıma dersi — denetim §G, 2026-08-13):** **"payda modelin
  paydasıyla aynı büyüklükte değilse fark model hatası değil KAYNAK farkıdır"** (`EDG-038:72-78`).
  Bu ders EDG-037'nin manşetini ("~9 kat") çürüttü — kanonikte **~7×** ve **3/4 aleyhte**
  (`EDG-038:132-135`). Kalıcı metodoloji dersi olarak yukarıdaki "YENİ (…)'dan ders" serisine girer.
- **🟡 DOĞRULANMADI (2026-08-31 denetimi — kart biçim/lint kalemi 2026-08-24 denetiminde BAYAT-KAPALI sayıldı ama depoda doğrulanamadı)** · **🆕 KART BİÇİM/LINT KALEMİ (denetim §G, 2026-08-13):** `EDG-2026-038…yaml:120` ve `:122` **iki
  `verdict:` anahtarı** taşıyor (katı YAML ayrıştırıcı hata verir); `:118` `status: measured`
  satırının yorumu "ölçüm bu satır yazıldıktan SONRA koşuldu" diyor. Kart şablonu + lint kalemi.
  *boyut: S · öncelik: düşük-orta (ama ölçüm ajanı karta dokunmaz — Rol-1 kalemi).*
  **[2026-08-24 TASARIM-KAPANIŞI:** vaka ÖLÇÜLDÜ — dup-anahtar dedektörü 65 kartın TAMAMINDA
  koşuldu ve sınıfın bugünkü nüfusu **1**: yalnız `EDG-2026-038` iki `verdict:` taşıyor (`:120` boş
  placeholder + `:122` gerçek hüküm); başka vaka ve parse hatası YOK. ZARAR BUGÜN YOK ama
  TESADÜFEN: PyYAML last-wins olduğu için İKİNCİ (dolu) blok kazanıyor — sıra ters olsaydı gerçek
  hüküm SESSİZCE yutulurdu. Lint aracı repo'da yok (`ops/` tarandı). Kapanış iki satırdır:
  ① Rol-1 `EDG-2026-038`'deki boş placeholder satırını siler (ölçüm ajanı karta dokunamaz —
  Rol-1 kalemi); ② eleme belgesinde koşulan 15 satırlık dup-anahtar dedektörü AYNEN çivi olur ve
  teste girer (S-boyut). Ayrı "kart şablonu" turu AÇILMAZ — sınıfın bugünkü tüm nüfusu 1. Kalan
  mini-iş hafta-1 partisinde. Belge: `docs/ELEME-WP5-2026-08-23.md` #14.**]**

#### WP5-B · Ölçüm/görünürlük borçları _(eski WP-S2 gövdesi; 2026-08-07, hepsi BEYANLI, hiçbiri sessiz değil)_
- ~~**kill#4 uygulama borcu (kart `EXE-2026-002-R1` ön şartı):** kod eşleşmeyenleri ZATEN
  `sinif_dagilimi` ile ayırıyor (`eod_yok`/`golge_bozuk`/`bps_yok`); kill kapısının yalnız
  BOZULMA sınıflarına daraltılması ayrı tur. Bugün fark yaratmıyor (oran %0), o yüzden acil değil
  — ama `eod_yok` biriktiği gün ölçüm haksız yere susar.~~
  **[2026-08-24 KAPANDI-BAYAT:** YAPILMIŞ — daraltma KODDA:
  `KAPSAM_DISI_SINIFLARI=("eod_yok",)` + "BURADA OLMAYAN her eşleşmeme BOZULMA sayılır —
  fail-closed" (`faz5_cikis.py:42-49`); payda `eod_yok`'u dışlıyor ve oran yalnız
  `golge_bozuk`+`bps_yok`'tan kuruluyor (`:355-372`). Kart R1 revizyonu işlenmiş
  (`EXE-2026-002…yaml:92-96`), `status: measured`. "Ayrı tur borcu" diye taşınan iş O TURDA
  YAPILMIŞ, satır güncellenmemişti (Ö-49 bayat-beyan sınıfı).
  Belge: `docs/ELEME-WP5-2026-08-23.md` #10.**]**
- **✅ `k.olcum` panoda ÇİZİLİYOR (KAPANDI v219 — "beş kilidin `olcum`'u nihayet çiziliyor").** Borç neydi: `app.js`
  yalnız `k.esik` + `k.neden` okuyordu; tam yük `/api/diagnostics` JSON'ında SERVİS EDİLİYORDU ama çizilmiyordu.
  Faz-5 turunda karar sayıları `neden` metnine yazıldı (operatör "4/20"yi görüyor) ama bu bir
  yamaydı; kilit ölçümlerinin kendi kartı yoktu. v219 beş kilit için `k.olcum`'u çizdi (eski
  "beyan bayatlamasın" testi — `"k.olcum" not in appjs` — pano okumaya başlayınca güncellendi).
- **✅ app.js 409-yutması (KAPANDI v219 — boş `catch` 6→0):** borç neydi: `apiFetch` 4xx'te throw etmiyordu,
  `applySkillRec` boş `catch` ile yutuyordu → L1'de onay-kapısı reddi PANODA GÖRÜNMEZ oluyordu
  (operatör basar, hiçbir şey olmaz). Mekanizma düzeyinde YASA 4 zaten tamamdı (olay+gerekçe defterde),
  operatör yüzeyinde değildi. v219 boş catch'leri 6→0 indirdi; N5 app.js turunun parçası.
- **✅ `EV_TR`de `koruma_*` + süpürücü çevirileri (KAPANDI v219 dokuz olay çevirisi + v225 opCancelOpen `siniflar` dökümü):** borç neydi: v209/v211 olayları panoda HAM olay adıyla görünüyordu
  (tam alanlar tıklanan çekmecede). v219 dokuz olayı ÖLÇÜLMÜŞ adlarla cümleye çevirdi; v225 pano
  `opCancelOpen` sonucunda süpürücü sınıf dökümünü (giriş/koruma/yabancı) + 4 süpürücü olay
  çevirisini gösteriyor. N5 app.js turu.
- **AÇIK** (TAKVİM: Faz-5 örneklemi kendiliğinden dolar — 11/20) · **Faz-5 örneklem (kendiliğinden dolar):** kilit artık `durum: olculdu` · "ÖRNEKLEM YETERSİZ
  (4/20)". Nokta tahmini −9,69 bps ama `n_kume=1` (dört dolum tek gün) olduğu için CI
  HESAPLANMADI ve `sifiri_disliyor: null`. Kill#2 ancak n≥20 VE CI tamamen negatifken işler.
  Bu kalem KOD İSTEMEZ, İŞLEM İSTER.
- **"BEYAN VAR, ÜRETİCİ/TÜKETİCİ YOK" sınıf taraması (2026-08-07 operatör sorusu üzerine;
  grep-turu yapıldı, sistematik tur AÇIK):** Faz-5 kilidi bu sınıfın bir örneğiydi ("üreten kod
  yok") ve kapandı. Grep'in bulduğu KALAN örnekler: ~~① `docs/RUNBOOK.md` 31 girdi "henüz
  yazılmadı" (görünür-bilinçli ama borç gerçek)~~ **① ✅ KAPANDI (denetim A7, 2026-08-13):**
  `grep -c "henüz yazılmadı" docs/RUNBOOK.md` = **1**, o da kuralın kendi tarifi (`RUNBOOK.md:29`);
  alarm bölümleri gerçek prosedürlü (`:67` HEARTBEAT_STALE · `:168` MIRROR_DRIFT · `:304`
  NAKED_POSITION "KALICI RİSKLER / DERSLER" bloklu). _SINIR BEYANI (denetim §I): bu kapanış tek bir
  `grep` sayımına dayanıyor; üretecin (`ops/runbook_uret.py:55`) başka bir boşluk dilini kullanıp
  kullanmadığı denetlenmedi._ · ② hermes çağrı telemetrisi — veri `/api/hermes`te
  AKIYOR, pano kartı YOK (`hermes.py:2503`, D3-UI kalemi; `k.olcum` borcuyla aynı aile) ·
  ③ cf çıkış-yasası sapması (`analytics.py:1380`): 6 çıkış tipi cf'te modellenmiyor, ölçülmüş
  iyimserlik +0,039R, cf satırları skor havuzunun %96'sı — "ayrı turun işi" denmiş, tur hiç
  açılmamış. DÜRÜST (iş gerektirmeyen) dallar ayrıldı: E3 ampirik bandı ve `_olcut(olculemedi)`
  dalları örneklem bekliyor, sabit taş değil. SINIR BEYANI: grep yalnız İTİRAF EDİLMİŞ borcu
  bulur — bugünün en tehlikeli vakaları (uyuyan-yol tüketicisizliği, koruma yeniden-kurma
  yolunun hiç olmaması) BEYANSIZDI ve `codelaw.artifact_graph`tan da kaçtı (defter yazılıyordu,
  okuyucusu vardı; eksik DAVRANIŞSAL tüketiciydi). Sistematik tur = artefakt/bayrak envanterini
  yürüyüp her birine "üreticin kim, seni kim OKUYOR, okuyan DAVRANIYOR mu?" sormak.
- **✅ SİSTEMATİK TUR KOŞULDU (2026-08-07 gece, dördüncü kova — `docs/ARTEFAKT-TARAMASI-2026-08-07.md`,
  551 satır):** 107 artefakt + 5 bayrak + 53 config anahtarı + 13 kapı-dışı kalem. KALİBRASYON
  KAPISI 3/3 — ama İKİ YÖNTEM ONARIMINDAN SONRA (ilk koşu 1/3; alan-düzeyi merceği + taint
  yayılımı eklendi; raporda beyanlı). Sayım: `davranissal` 92 · `yalniz-gorunurluk` 14 (13 meşru,
  1 şüpheli) · `tuketicisiz` 1 · `ureticisisiz` 0. Sistem BÜYÜK ORANDA KABLOLU — bulgular kenarda:
  (NUMARALAMA NOTU: buradaki B-1..B-7 TARAMA bulgularıdır; WP-S'teki B1-B4 bayat-sermaye turunun
  BEKÇİ önerileridir — iki ayrı dizi, çakışma tesadüfi. Bekçi dizisi bundan sonra SB-1..SB-4
  diye anılır.)
  · **✅ B-1 (KAPANDI 426b998):** `goal.yaml`'da 4 beyansız ölü düğme (`backtest_gate`/`session_tz`/`style`/
    `schema_version`) — tek eşleşme `guard.py:15-17 GOAL_KEYS` üyeliği, değeri kimse okumuyor.
    K1'in (2026-07-30) bulduğu `explore_rate`/`kill_switch_file` sınıfının kaçmış dördü.
    `backtest_gate: true` en ağırı: kapı sözü veriyor, davranış yok. Rol-1 doğruladı.
  · **B-2 (YÜKSEK → İKİ ALT İDDİA ÇÜRÜDÜ, ÇEKİRDEK DOĞRU ÇIKTI VE KAPANDI, v214):** "9 çağrı
    grafikte yok" YANLIŞTI (dokuzunun biçimi zaten çözülüyordu — filtre tabanı sorgulamıyordu);
    "massive_verify haritada yok" YANLIŞTI (hep oradaydı). DOĞRU çekirdek: tarayıcı ÇÖZEMEDİĞİNİ
    SAYMIYORDU — gerçek kör sınıf `store.py` içi 6 çıplak-ad çağrısıydı. Kapama: her erişim ya
    çözülür ya adlandırılmış `UNRESOLVED_REASONS` kovasına düşer + `access_patterns` census;
    unresolved 15→21 (körlük görünür oldu). Rapora DÜZELTME bloğu eklendi; ders: kalibrasyon
    yalnız bilinen-pozitifleri sınıyordu, bilinen-NEGATİF kapısı da gerekir.
  · **✅ B-3 (KAPANDI 426b998, K1 deyimiyle beyanlandı):** `one_variable_only` YAPIŞIK düğme — kural koşulsuz (`guard.py:134`), anahtar
    yalnız hata METNİNDE geçiyor; kapatılamaz bir şeyi düğme gibi beyan ediyor. Rol-1 doğruladı.
  · **✅ B-4 (KAPANDI d1c40e9, v214 `stale_claims()`):** `sieve.json` muafiyet beyanı BAYAT'tı — "tek okuyucusu kendi testi" diyor, oysa
    `api.py:3202→2232` üzerinden TERFİ HÜKMÜNE giriyor; `stale_sinks` bunu yapısal göremiyor.
  · **✅ B-5 (KAPANDI 4d09028, Rol-1 hükmü: yazım SÖKÜLMEDİ):** `state/intraday_bars/<gün>.jsonl` ölü yazımdı (canlı sıcak yolda her
    dakika) — tarihli f-string ad DECLARED_SINKS'e giremiyor; mimari karar Rol-1/operatörde.
  · **✅ B-6 (KAPANDI f253929, v215) / ✅ B-7 (KAPANDI 4d09028):** `approvals.jsonl` onay defterini hiçbir kapı okumuyordu (uyuyan-yol ailesi, L1'de
    patlar) · `shadow_trades.jsonl` tek tüketici bir CLI bayrağı.
  · Taze canlı sayım: uyuyan plan 31→**32** (0 işlem, 1 GO — oran değişmedi). ÖLÇÜLEMEYENLER
    raporda adıyla (7 kalem; en önemlisi: KATMAN-4 alan merceği yalnız `dormant_setup`a
    uygulandı, plan defterinin ~20 kontrol alanı BİR SONRAKİ KOVANIN konusu).
- **✅ ÖLÜ-MEKANİZMA AVININ BEŞİNCİ KOVASI KOŞULDU (2026-08-09 gece — `docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md`):**
  dördüncü kova TÜKETİCİSİZ YAZIM (ölü kopya) avlamıştı; beşincisi ÇOK-YAZARLI GERÇEK (ayrık kopya)
  avlar — "aynı gerçeği başka kim bildiğini iddia ediyor, o kopya bugün ne diyor?". 22 gerçek-ailesi
  yüründü, kalibrasyon İLK KOŞUDA 3/3 ve iki-yönlü kapı iki yanlış-pozitifi fiilen durdurdu
  (commit `f456b56`). Salt ölçüm+belge; `meridian/` altında dosya değişmedi.

- **🆕 YENİ AÇIK KALEMLER (2026-08-09, devir tatbikatı + sabah triyajı hasadı — `docs/SABAH-TRIYAJI-2026-08-09.md`):**
  · **systemd `daemon-reload` (P2, kanal-açılışında P1):** `SuccessExitStatus=143` birim dosyasına
    YAZILDI (v225) ama CANLI systemd hâlâ boş `SuccessExitStatus=` ile koşuyor — birim dosyası
    değişikliği reload+restart bekliyor ("kurulu ≠ çalışır" doktrini). N1 bildirim kanalı açılmadan
    ÖNCE inmeli, yoksa her restart "FAILED" sayılıp OnFailure bildirir. Bakım penceresi + elle
    test-ateşleme. *Kalem 1 (SABAH TRİYAJI en ucuz + kanal-kapılayan).* **[2026-08-23: ✅ 08-09 KAPANDI — OB-2 operatörce yapıldı, canlı `SuccessExitStatus=143` doğrulandı (Result=success; §5 `[B-SYSTEMD-143]`); bu gövde kopyası güncellenmeden kalmıştı]**
  · **skill görüş canlı-kanıt (P3, ölçüm-borcu):** N2b/EDG-2026-019 kod indi (v218) ama R-figürleri
    kuru-koşu (`eksen2.uretilen=0`, `gorusleri.jsonl` beslenmedi); birkaç EOD penceresi +
    EDG-2026-019 ölçüm kodu bekliyor.
  · **ajan-git MEKANİK kapısı (P2, süreç/araç kararı — operatör):** gece 2 ajan `git stash` koşup
    hasar verdi (hayalet dizin süpürüldü). Yasak yalnız CLAUDE.md sözleşmesi; `dagit.sh` yalnız
    DAĞITIMI kapıyor. `git stash`ın pre-stash kancası YOK → kapı ancak PATH-shim/wrapper'la
    mekanikleşir. Karar operatörde.
  · ~~**kill#4 uygulama (AÇIK — yukarıdaki borç):** kill kapısının yalnız BOZULMA sınıflarına
    daraltılması (kart `EXE-2026-002-R1`); bugün etki %0, `eod_yok` biriktiği gün ölçüm haksız susar.~~
    **[2026-08-24 KAPANDI-BAYAT: aynı kalemin ikinci kopyası — daraltma `faz5_cikis.py:42-49`'da
    fail-closed olarak kodda, kart R1 revizyonu işlenmiş ve `status: measured`
    (`docs/ELEME-WP5-2026-08-23.md` #10; hüküm yukarıdaki WP5-B borç satırında tam metinle).]**
  · **SB-2 `drift_sinifi` (AÇIK — WP-S):** MIRROR_DRIFT alarmına sebep-adlandırma alanı; 08-05'te
    dört alarm bastı, hiçbiri sebebi söylemedi.

- **🆕 AÇIK KALAN RUNBOOK BORCU (denetim §B notu, 2026-08-13):** Ö-17'nin (karne sürüm split'i,
  ✅ kapandı → §8) kalan borcu **HÂLÂ AÇIK**: "strateji **sürüm terfisi dagit kapsamı DIŞIDIR**:
  `strategy.yaml` scp + scoreboard DB yazımı AYRI adımdır; scp'lenen `scoreboard.json`'u bayat-defter
  migrasyonu `.migrated`'a taşır ve DB'ye YAZMAZ" prosedürü RUNBOOK'a yazılmadı —
  `grep "sürüm terfisi" docs/RUNBOOK.md` = **0**, RUNBOOK 2026-08-13 21:58'de yeniden üretilmiş
  olmasına rağmen. **Aynı turda WP6/F9'un RUNBOOK satırıyla birlikte kapatılır.** **[2026-08-23 KAPANDI — SON HAL 0e1c11a: sözleşme kaynağına taşındı (dagit.sh BAŞLIĞI — RUNBOOK 'yazılmaz, üretilir' olduğundan elle bölüm üreticide silinirdi); RUNBOOK'a girişi üretici-kapsam kararına bağlı → §5 [B-RUNBOOK-KAPSAM]]**

#### WP5-C · DSR girdi-serisi donmuş-çekim aracı _(taşındı: Ö-4, eski satır :742-747 — 2026-08-13)_
_(denetim D6: öncelik **orta → orta-yüksek.** DSR artık anlamlı bir sayı (1e-06 → **0,0391**,
`EDG-036:166`); M2'nin DSR yarısı "ölçülemez" olmaktan çıktı, araç borcu bağlayıcı hâle geldi.)_
4. **DSR girdi-serisi donmuş-çekim aracı (KYS-002 kill#2'nin araç borcu, 2026-08-10)** — kapının taze
   küme-DSR'ı `_ret` (pnl/START_EQUITY, reflect.py:559) serisini ister; validation_ledger `seri`si
   (kapanış-günü, r_multiple) ölçek-eşdeğer DEĞİL (ölçüldü: Sharpe sapması medyan 0.0131). İki yol:
   defter şemasına pnl-serisi damgası (yazar reflect, okuyucu ölçüm-çekimleri) YA DA işlem-düzeyi pnl'li
   yeni donmuş-çekim betiği. Araç inince KYS-002 DSR-yarısı yeniden ölçülür. *gerekçe: M2'nin DSR yarısı
   ölçülemiyor · boyut: S-M · bağımlılık: reflect şema kararı (Rol-1) · öncelik: orta.*
   **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1):** bugün yeniden ölçüldü — araç HÂLÂ YOK:
   `validation_ledger` `seri`si hâlâ `[[tarih, r_multiple]]` (`reflect.py:837`, `ledgers.py:220-226`
   sözleşme değişmemiş), pnl-serisi damgası da ayrı donmuş-çekim betiği de repo'da yok (grep boş);
   `KYS-2026-002` `status: measured_partial` — DSR yarısı kill#2 (kart `:50,:60-61`). D6 gerekçesi
   geçerliliğini KORUYOR: DSR artık anlamlı bir sayı — **0,0391** (`EDG-036:124,:166`), yani araç
   borcu bağlayıcı. Sıra: ÖNCE reflect şema kararı (Rol-1: pnl-serisi damgası MI, ayrı donmuş-çekim
   betiği Mİ), SONRA KYS-002'ye **R2 revizyonu** ile DSR-yarısı yeniden ölçülür. K-maliyeti:
   **K += 1** (grid yok, tek taban hesabı; araç boyutu S-M). Eşik taslağı: PBO yarısıyla
   simetrik — **taban RAPORLANIR, hüküm eşiği YOK** (taban ölçümü); **kill:** seri
   ölçek-eşdeğerliği doğrulanamazsa (Sharpe sapması medyan >0,01 kalırsa) DSR tabanı yine
   yazılMAZ. Belge: `docs/ELEME-WP5-2026-08-23.md` #1.**]**

#### WP5-D · M8 kararları Rol-1 turu _(taşındı: Ö-14, eski satır :844-849 — 2026-08-13)_
_(denetim D7: **yüksek, SIRAYA ALINMALI.** İki günde K hızla harcandı (EDG-035 K+=6, ayrıca
036/037/038/039); U5 (beyan-K/harcanan-K) ve U6 (kart-K ↔ DSR `n_trials`) artık DSR'ı DOĞRUDAN
etkiliyor.)_
14. **M8 kararları Rol-1 turu (docs/M8-K-SENKRON-RAPOR-2026-08-10.md'nin işlenmesi)** — rapor 7 başlık verdi,
   kararlar ölçüm-anlamı değiştirir, aceleye gelmez: U1 EXE-001 K-düzeltme notu (aritmetik dürüstlük;
   tarihçe-koru) · U2 8 kartın pending-* trial_ids temizliği · U3 README endeks tazeleme · U5 beyan-K/
   harcanan-K şeması · U6 kart-K↔DSR n_trials bağlanmalı mı (MİMARİ: yeni tüketici + DSR çıktısı değişir) ·
   U7 rotasyon-yerel vs ömür-boyu sayaç hükmü. *gerekçe: K-defteri deneysel bütçenin kalbi · boyut: M ·
   bağımlılık: rapor(✅) · öncelik: yüksek-ama-odaklı-tur.*
   **[2026-08-24 TASARIM-KAPANIŞI:** kalem YAPILMAMIŞ ve bugün dört bağımsız izle doğrulandı —
   ① U2 temizliği yok: **41/65 kart** hâlâ `pending-*` trial_ids taşıyor (ör. `EDG-001:18`,
   `EDG-038:116`); ② U3 yok: `research/cards/README.md` endeksi bayat (EDG-001/002 hâlâ
   "Aktif/registered" başlığında); ③ U5 yok: hiçbir kartta beyan-K/harcanan-K alanı yok;
   ④ U6 yok: `analytics.validation_trio` `n_trials`'ı aşınma-defteri + `k_probes`'tan topluyor,
   kart-K'ya bağlı DEĞİL (`analytics.py:2608-2615`). Rapor hazır:
   `docs/M8-K-SENKRON-RAPOR-2026-08-10.md`. **Tek konsolide Rol-1 oturumu bu kalemi ÖLÇÜMSÜZ
   kapatır.** Kapanış taslağı: U1 K-düzeltme notu tarihçe-koru işlenir · U2 41 kartın `pending-*`
   alanları gerçek trial_id'lerle (yoksa `none-<neden>` damgasıyla) MEKANİK değiştirilir ·
   U3 README endeksi kart durumlarından YENİDEN ÜRETİLİR (elle bakım bırakılır) · U5 şema alanı
   eklenMEZ (mevcut `k_registry` yeterli — yeni alan yeni bakım borcu) · U7 rotasyon-yerel sayaç
   REDDEDİLİR (ömür-boyu kalır; seçilim baskısı oturum tanımaz). **TEK MİMARİ İSTİSNA: U6**
   (kart-K ↔ DSR `n_trials` bağı) — DSR ÇIKTISINI değiştirir, ayrı Rol-1 hükmü ister ve oturumun
   tek "karar" maddesi budur. Kalan mini-iş hafta-1 partisinde.
   Belge: `docs/ELEME-WP5-2026-08-23.md` #3.**]**

#### WP5-E · PAKET-BAĞIMLI EŞİK ENVANTERİ SONUÇLARI _(taşındı: Ö-20, eski satır :941-963 — 2026-08-13; **20a ✅ KAPANDI → §8 arşiv**)_
20. **PAKET-BAĞIMLI EŞİK ENVANTERİ SONUÇLARI (denetim 2026-08-13, `docs/DENETIM-PAKET-BAGIMLI-ESIKLER-2026-08-13.md`)**
    · **20a ACİL/KIRMIZI — ✅ KAPANDI (2026-08-13, denetim A8/B5):** `shadowlaw.DD_VETO_MARGIN`
      artık **0.08** (`meridian/shadowlaw.py:102`, repo) ve `state/goal.yaml:20` `max_drawdown: 0.16`
      → çivi `tests/test_dalga_w1_v216.py:526-528` goal/2 eşitliğini arıyor, **0,08 == 0,16/2**
      tutuyor. Uygulama: `62727d6` v238 "max_drawdown 0.16 zinciri". **Tam metin §8 arşivde.**
      _(SINIR BEYANI, denetim §I: "iki test artık yeşil" sonucu assert'in OKUNMASINDAN çıkarıldı,
      koşumdan değil — otoriter suite Rol-1'de.)_
    · **20b YAPISAL:** `analytics.RESULT_PF_MIN=1.3` (`analytics.py:2089`) ↔ benimsenen paketin PF'i
      **1,1119** → SONUÇ hükmü 4/4 istediği için (`health.py:148`) **Faz-6 `sonuc_hukmu` kilidi bu
      paketle yapısal olarak AÇILAMAZ**. Eşiğin gerekçesi 95-işlemlik deftere dayanıyordu; 885 işlemde
      aynı biçimde geçerli değil. ~~KARAR GEREKİR (eşiği ölç-ve-güncelle mi, paketi mi elemek — ikincisi
      ölçüme aykırı olur). *öncelik: yüksek.*~~ **→ DÜZELTME (denetim A14/D12, 2026-08-13): BU BİR
      KARAR KALEMİ DEĞİL, KAYIT.** Karar **ölçümle verildi**: `EDG-2026-037…yaml:65` "**EŞİK
      TARTIŞMASI KAPANDI — `RESULT_PF_MIN=1.3` GEVŞETİLMEZ**, çünkü tartışmanın yönü TERSİNE döndü";
      `:66-67` "PF ek friksiyonda monoton azalandır: **1,1119 hiçbir friksiyon varsayımıyla
      YÜKSELEMEZ**"; `EDG-2026-038:155-159` "EDG-037 hükmü **güçlenerek** durur". Kayıt cümlesi:
      **"Faz-6 `sonuc_hukmu` bu paketle yapısal kapalıdır ve bu ARIZA DEĞİL, KORUMA"**
      (`EDG-037:83-85`). Açılmasının yolu eşiği gevşetmek değil **icra friksiyonunu ölçüp düşürmek**
      (WP1-B). Operatöre giden hâli §5 KOVA-2'de **BİLGİ** olarak duruyor. *öncelik: kayıt.*
    · **20c YÖNETİŞİM ASİMETRİSİ:** goal "slot 20 ve 0,5R AYRILMAZ" diyor ama slot `LIMIT_KEYS`te
      (hermes öneremez), `position_size_r` `bounds.yaml:15`'te 1,0'a kadar AÇIK → öğrenme ikilinin
      yarısını tek başına geri çekebilir; o yönün ölçülmüş hâli EDG-026'nın B kolu (+775$, sharpe 0,018).
      ÖNERİ: ya ikisi de kilitli ya da bounds üst sınırı 0,5'e çekilir (kart-önce). *öncelik: yüksek.*
      **[2026-08-24 TASARIM-KAPANIŞI:** asimetri BUGÜN DE GERÇEK (`max_open_positions` LIMIT_KEYS'te
      — `guard.py:51`, hermes öneremez — ve goal'da "ikisi AYRILMAZ" (`goal.yaml:134`); ama
      `position_size_r` bounds'ta **max: 1.0** duruyor (`bounds.yaml:19`) ve LIMIT_KEYS'te YOK →
      öğrenme çiftin yarısını tek başına 1,0'a çekebilir). Karşı-argüman da yazılı: bounds şerhi
      "arama uzayı kumhavuzudur, canlı değer `strategy.yaml`da" (`bounds.yaml:16-18`). Ama
      kumhavuzu-şerhi TEK BAŞINA YETMEZ, çünkü kapıdan geçen bir `position_size_r` önerisi canlıyı
      değiştirir — çift SÖZLEŞMEYSE iki yakası da aynı rejimde olmalı. Karar masa-başı verilir
      (operatör/Rol-1), ölçüm gerekmez; yön ölçümü zaten hazır (EDG-026 B kolu +775$, sharpe 0,018
      vs C kolu). **Kapanış:** `position_size_r` LIMIT_KEYS'e alınMAZ (arama ölçmeye devam etsin) ve
      bounds satırı DOKUNULMAZ kalır, ama **goal'a ÇİFT-BAĞ ÇİVİSİ** eklenir: slot≠20 VEYA
      size≠0,5 önerisi TEK BAŞINA gelirse kapı `REVIEW`a düşürür (öneri ancak ÇİFT olarak ve
      kart-önce gelir). Kalan mini-iş hafta-1 partisinde.
      Belge: `docs/ELEME-WP5-2026-08-23.md` #11.**]**
    · **20d İNCE MARJLAR / İZLEME:** `EDGE_CVAR5_MIN_R=−1.5` ↔ ölçülen −1,4736 (marj %1,8; hammer tek
      başına −1,5916 eşik-altı) · hedef üçlüsü ölçülen dünyada çok gevşek (realized_30d +0,341% vs %7;
      sharpe 0,521 vs 1,2 → bileşik skor ≈0,130 iken `rollback_if_worse_by=0.10` skorun neredeyse
      tamamı) · `loop.EXPLORE_MAX_POS=5` hâlâ eski max_open · trend_down/high_vol rejimlerinde 4,54
      yılda SIFIR işlem (rejim kapısı orada tümden kapalı — bilgi, kusur değil).
      **[2026-08-24 TASARIM-KAPANIŞI:** yapı DEĞİŞMEMİŞ ve HİÇBİR alt kalem iş üretmiyor —
      `EDGE_CVAR5_MIN_R=-1.5` aynen (`analytics.py:1686`); `EXPLORE_MAX_POS=5` artık `max_open`
      KALINTISI DEĞİL, **beyanlı operatör debisi** (`loop.py:45` "öğrenme debisi (operatör,
      2026-07-20)"); hedef üçlüsü goal'da aynen (`target_return_30d: 0.07`, `min_sharpe: 1.2`,
      `rollback_if_worse_by: 0.10`). Marjın BUGÜNKÜ CVaR değeri canlı defter ister — yerel anlık
      görüntü 2026-07-28 tarihli, **ölçülmedi ve uydurulmadı (None)**. Kalem **20b emsaliyle KAYIT
      sınıfına indirilir** (karar değil, BİLGİ): "hedef üçlüsü gevşek + CVaR marjı ince" cümlesi bu
      WP5-E satırında izleme notu olarak KALIR, stok kalemi düşer. **Canlanma koşulu beyanlı:**
      EDGE VERDICT bir ölçütü CVaR yüzünden çevirirse YA DA hedef üçlüsü bir hükme girerse kalem
      YENİDEN AÇILIR. Kalan mini-iş hafta-1 partisinde.
      Belge: `docs/ELEME-WP5-2026-08-23.md` #12.**]**
    · **20e İYİ HABER (kapandı):** R-birimli 11 eşik (skills −0,15/+0,30, AUTO_AVG_R, TAIL_MARGIN_R,
      CVAR) boyut değişiminden ETKİLENMİYOR — R, `position_size_r`'den yapısal olarak bağımsız
      (`broker.py:439-445,526,535,684` + `counterfactual.py:220` kanıtlı). Bu eşiklere DOKUNULMAZ.
      Denetimin §7'sinde 11 maddelik "dokunulmayacaklar" listesi var (başında heat_hard_r=5.0).

#### WP5-F · KORUNUM SINIFI — uyuyan-kurulum planlarına terminal sınıf _(taşındı: Ö-16, eski satır :965-974 — 2026-08-13)_
16. **KORUNUM-14 SINIFI — uyuyan-kurulum planlarına terminal sınıf (pano ihlal-triyajı 2026-08-12)** —
    korunum dedektörü 14 AÇIKLANAMAYAN sayıyor; canlı API dökümü: HEPSİ dönemin uyuyan kurulumlarının
    REVIEW planları (mb×5+ / hammer×2 ilk-8'de; P-2026-07-23-{CSX,UNP,NSC,RTX}-momentum_burst kümesi).
    Kök [[uyuyan-kurulum-yolu]] arka-bağsızlığı: silahlanamayan plan hiçbir terminal olaya ulaşamıyor.
    DÜZELTME (dedektör-tarafı, dürüst kova): watchdog.conservation_report'a `uyuyan_kurulum` terminal
    sınıfı — planın kurulumu plan-tarihinde ARMED_SETUPS dışıysa (silahlanma-tarihçesi kayıtla, koda
    gömme) replay_era gibi ayrı sayılır; + test. NOT: bu geceki dağıtım mb'yi silahlıyor → sınıf İLERİYE
    kapanıyor (hammer 08-12'de kapandı), kalan uyuyanlar üretmeye devam ederse sayı büyür — icra-bağı
    kararı operatörde (§5/uyuyan). *boyut: S · öncelik: yüksek (sıradaki kod turu; bu gecekine EKLENMEZ —
    dağıtım kapsamı donuk).*
    **⚠ SAYI DÜZELTMESİ (denetim A9, 2026-08-13): ~~14~~ → 3.** `EDG-2026-036…yaml:172`: "Kapının
    AMACI 'yenileme korunumu BOZMASIN'dı; bozmadı, **14→3 İYİLEŞTİRDİ**". Kalan üçün ikisi adıyla
    kayıtlı (PKG-momentum_burst, ROK-exhaustion_hammer — `card:169-170`); **dedektör-tarafı
    `uyuyan_kurulum` kovası hâlâ gerekli** (denetim §H-15: kalan 3 korunum kalemini sınıflar).
    _(Madde başlığındaki "KORUNUM-14" adı ÇAPA olarak korunur — arama/tarihçe için; sayı 3'tür.)_
    **[2026-08-24 BİRLEŞTİR — EDG-2026-049 hükmü sonrası (hüküm 2026-08-24'te indi: NO-GO — kova
    artık inebilir):** dedektör-tarafı `uyuyan_kurulum` terminal sınıfı bugün de HÂLÂ YOK
    (`watchdog.conservation_report:514-616` sınıfları: traded/dropped/NO_GO/taze/no_fill/replay_era/
    unexplained; grep `uyuyan_kurulum` boş). Yerel 2026-07-28 anlık görüntüde `unexplained=6`
    (CSX/UNP/NSC/RTX 07-23 mb + PKG 07-24 + ROK 07-27 hammer — HEPSİ uyuyan-kurulum REVIEW planı,
    yani kovanın sınıflayacağı sınıfın ta kendisi); **kanonik canlı sayı 08-13'te 3'tü**
    (`EDG-036:169-172`; mb 08-12'de silahlanınca düştü) — yerel sayı bayat-ayna değeridir, kanonik
    olan canlıdır. Kova ŞİMDİ inseydi `EDG-2026-049`'un (registered 2026-08-23, K6, dormant
    karşı-olgu) ölçtüğü popülasyonun sınıflaması ÖLÇÜM SIRASINDA değişirdi (ölçüm-bağlamı tuzağı) —
    bu yüzden kalem 049'un hükmüne bağlanmıştı. **Hüküm 2026-08-24'te indi (NO-GO), engel kalktı:**
    kova (S-boyut, kart İSTEMEZ — dedektör hijyeni) §5 icra-bağı operatör kararıyla aynı pencerede,
    tek kod turunda iner. Belge: `docs/ELEME-WP5-2026-08-23.md` #13.**]**
    **BİÇİM DÜZELTMESİ (denetim §I, 2026-08-13):** bu maddenin kuyruğundaki üç satır ("NOT:
    çıkış-mühendisliği hattı BİLİNÇLİ dışarıda …" + "gerekçe: sharpe 0.285 …") KORUNUM maddesine
    değil **SEÇİLİM-KALİTESİ hattına** aitti (birleştirme artefaktı) → **WP11'e taşındı.**

#### WP5-G · 🆕 §4 BOŞALTMASI 2026-08-23 — havuzdan taşınan iki kalem _(usul 2026-08-13 emsaliyle aynı; gövdeler AYNEN, izler §4'te)_
_(taşındı: §4-32, eski satır :1958-1965 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-32`; §4'te iz satırı)** · **🆕 32. SUITE'İN İÇİNDEN GERÇEK AĞ ÇAĞRISI — ÖLÇÜLDÜ** _(2026-08-14, v245-A yan bulgusu; sahibi WP5)_
  `test_ogrenme_otomasyonu_v136`in iki testi `scheduler.advance_once → earnings.refresh →
  adapters/data.py:2673 → :855 _get_json` üzerinden **gerçek `api.nasdaq.com`** çağrısı yapıyor.
  ÖLÇÜM: ağ bacağı saplandığında iki test **0,47 sn**, saplanmadığında **263,71 sn** (SIGABRT yığın
  dökümüyle çerçeve çerçeve doğrulandı). MERIDIAN_ENGINEERING_LOG bunu zaten açık kalem olarak
  taşıyor; bu ölçüm **büyüklüğünü** veriyor. Otoriter suite süresinin görünür bir kısmı budur ve
  ağ nondeterminizmi kırmızı üretebilir.
  *öncelik: orta · boyut: S (ağ bacağını testte sapla) · yan fayda: tam suite belirgin hızlanır.*
_(taşındı: §4-35a, eski satır :1916-1923 — 2026-08-23; §4-35'in (a) yarısı — (b) yarısı WP11-G'de; ortak başlık satırı iki hedefe de kopyalandı)_
- **✅ TAŞINDI (havuz `Ö-35`; §4'te iz satırı)** · **🆕 35. 15g TURUNUN DEVRETTİĞİ İKİ KALEM** _(2026-08-14, v245-E; sahipleri WP5 ve WP11)_
  **(a) MUTASYON SEÇİMİ EKSİK — `pyproject.toml`** _(WP5)_: `[tool.mutmut] only_mutate`
  `meridian/guard.py`yi içeriyor ama `pytest_add_cli_args_test_selection` listesinde yeni
  `tests/test_sektor_tavani_ayristirma_v245.py` YOK. pyproject'in KENDİ türetme kuralı ("bu üç
  modülü DOĞRUDAN import eden test dosyaları") gereği girmesi gerekir — v237 de-risk turunda tam
  bu gerekçeyle eklenmişti. Girmezse haftalık ritüelde `sector_cap_basis` mutantları (ör. "açık
  paydayı yok say") **ölmeden hayatta kalır**; yanlış-yeşil değil yanlış-kırmızı üretir ama gerçek
  boşlukları gizler. *tek satır.*

### PRG-06 — Sistem Bütünlüğü 🟡
_(eski: WP6 · WP-H + Ö-25 ölü/ezilen bileşen + Ö-26 değer-eşitliği + Ö-2 gözlemlenebilirlik)_

**KAPSAM (tek cümle):** Kodun ve dağıtımın kendine sadakati — sürüm kontrolü, atomik yazım,
sertleştirme, ölü/ezilen bileşenlerin budanması ve "aynı gerçek iki yerde" kapıları.

#### WP6-A · Mühendislik dayanıklılığı _(eski WP-H gövdesi; 2026-07-31 el kitabı turu; kaynak: operatörün 2024-26 araştırma anketi — bizim gerçekle çarpıştırılmış hâli. İlke: "AI mevcut disiplini AMPLİFİYE eder; kapılar+geri-alınabilirlik önce" — bizde kart/yasa/çivi disiplini VAR, eksik olan sürüm kontrolü.)_
- **ZATEN VAR (el kitabı istiyor, bizde karşılığı):** wide-event/run = `daily_cycle` olayı ·
  canary/shadow = gölge-v2 + paper-lock · DST-lite yarısı = replay_seed + deterministik backtest ·
  snapshot testleri = çivi dizisi · yedek zinciri = VM-tar + Mac-pull · takvim/UTC = takvim kapısı ·
  iç dead-man = 17 bekçi + tick-watchdog + fail-notify.
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-HD-2026-08-09.md`, salt-ölçüm — WP-H + WP-D):** WP-H çekirdeği
  büyük oranda KAPALI; kalan tek adlı OTONOM iş = **H9 Kademe-B ~11 kapı-dışı yazımın** `store.write_text`/
  kilitli-append'e taşınması (kapı HAZIR `store.py:306`). En tehlikeli tekil: **`auth._write` SABİT-TMP-
  ADI** (`auth.py:87-96` — iki süreç aynı `.json.tmp`'ye yazar, atomiklik iddiası biter); sonra kırpma-
  sınıfı düz yazımlar `memory.py:212` lessons.md + `run.py:172` scoreboard. systemd `SuccessExitStatus=143`
  birim dosyasında YAZILI (`meridian.service:82`) ama **CANLIDA DEĞİL** — A1 /etc birimi 08-02 tarihli,
  her restart exit-143 ile "FAILED" (son 3 günde 6 kez, fail-notify NO-OP kurtarıyor); **N1 bildirim
  kanalının ÖN-ŞARTI** (daemon-reload + bakım penceresi + elle test-ateşleme — §8) **[2026-08-23: ✅ 08-09 KAPANDI — OB-2; canlıda doğrulandı, §5 `[B-SYSTEMD-143]`]**. H10 aşama-2 = saf
  OCI-bucket operatör-bloğu (§8-10). **WP-D'de otonom kod deliği KALMADI gibi** (bars_integrity sevk+
  kablolu, seans-içi boşluk dedektörü kurulu); açık kalan iki kalem OPERATÖR-bloklu (`dataset.load↔
  bars_integrity` bağlama = kapsam kararı + FMP planı). POZİTİF: E2 defteri kilit-8 kod düzeyinde kapanmış görünüyor.
- **H1 Hypothesis invariant paketi ✅ (2026-07-31 tur-2):** 20 property / 5 yasa bölümü (sanitize,
  depo-roundtrip diferansiyeli, kayıpsızlık durum-makinesi, takvim kapısı, defter damgası).
  İLK GÜN GERÇEK KUSUR: SQLite REAL −0.0 işaret kaybı (latent, canlıda 0 örnek; _isaretli_sifir
  kapısıyla kapandı, @example kilitli) — property-testin varlık gerekçesi kendini ödedi.
- **H2 tedarik-zinciri kapısı** ✅ 2026-07-31: `uv audit` temiz (69 paket, 0 zafiyet); dağıtım
  betiğine zorunlu ön-adım olarak kablolu (`dagit.sh` [0/6]) — ajan-önerili her yeni bağımlılık
  kurulum ÖNCESİ lockfile+audit'ten geçer (slopsquatting %19,7).
- **H3 systemd sertleştirme** tur-1 ✅ (2026-07-31): 9.2 UNSAFE → 6.3 MEDIUM (iki servis;
  dosya-sistemi/ad-alanı seti + pano token'ı unit'ten 0600 .dash.env'e taşındı+rotasyon).
  ~~Tur-2 📋~~ **Tur-2 ✅ CANLIDA (2026-08-23 bakım penceresi, operatör+Rol-1 birlikte):**
  tick-watchdog + fail-notify faz-1+faz-2 kurulu (durum: 4/4 repo-özdeş). İKİ ALET/TASARIM VAKASI
  YAKALANDI VE DÜZELTİLDİ: (a) boş CapabilityBoundingSet root-bekçinin ubuntu-0600 state okumasını
  kırdı — tetik-testi tam bu sınıf için vardı ve yakaladı; CAP_DAC_READ_SEARCH geri kondu, v266
  çivisi birim-bazlı kilitledi; (b) h3 betiğinin ön-şart ölçümünde pipefail+grep-q SIGPIPE kusuru
  (kanıt varken 'ölçülemedi' diyordu) — grep akış-tüketir hale getirildi. TETİK-TESTİ KANITLI:
  sertleştirilmiş bekçi 'durum 105s bayat → yeniden başlatılıyor' bastı, meridian 10:47:42'de
  bekçi eliyle yeniden doğdu. N1 zinciri de uçtan uca ölçüldü (fail-notify → Telegram, üç gerçek
  gönderim). Eski hedef metni: seccomp @system-service + CapabilityBoundingSet; hedef <4
  (NoNewPrivileges/ProtectSystem=strict/PrivateTmp/ProtectHome önce; seccomp EN SON ve dikkatli).
  + `MERIDIAN_DASH_TOKEN` unit dosyasında DÜZ METİN (herkes-okur) → rotasyon + LoadCredential'a
  taşıma AYNI bakım penceresinde.
- **H4 import-linter ✅ (tur-2):** 5 sözleşme 5/5 (506 bağımlılık); tek bilinçli istisna
  adapters.alpaca→broker (WP-E iki-motor yasası); backtest→loop DOLAYLI zinciri ölçüldü (sözleşme
  bölündü); MİMARİ BORÇ KAYDI: en büyük güçlü-bağlı bileşen 20 modül. ops/kapilar.sh zinciri +
  dagit.sh [0c] kapısı canlı.
- **H5 ✅ İLK GERÇEK KARNE (2026-08-01, 14. koşumda — 13 kırıklık saga 4 ortam-sınıfı + 2 araç-yalanı
  dersiyle altyapıya döndü):** 2.698 mutant → öldürülen 1.267 · hayatta 1.305 · testsiz 118 · skor
  **~%49** (hedef %80; NOT: pozitif-seçim alt-kümesinde ölçüldü — tam suite'in dışlanan davranış
  testleri bir kısmını öldürebilir, skor alt-sınır okunur). **AKŞAM GÜNCELLEMESİ — BORÇ
  KAPANDI: 16. koşum resmi skor 2312/2663 = %86,8 (hedef %80 AŞILDI).** 28-ajanlık Workflow turu
  (14 küme, enjeksiyon-kanıtlı) skoru bir öğleden sonrada +38 puan taşıdı; kalan 351'in çekirdeği
  doğrulanmış-eşdeğerler + hedeflenmemiş kuyruk — haftalık ritüel izler.
- **H5-eski kayıt:** yapılandırma + ops/haftalik_mutasyon.sh hazır
  (mutmut 3.7 doğru anahtarlar; sahte-%100 tuzağı belgeli); ilk gerçek koşum bakım ritüelinde.
- **H6 CLAUDE.md** ✅ 2026-07-31 — kısa çalışma sözleşmesi repo köküne yazıldı (log-önce kuralı,
  roller, yasalar, canlı-güvenlik).
- **H7 restore tatbikatı** ✅ İLKİ YAPILDI (2026-07-31): A1 arşivinden çekme 3,1sn + açma 0,3sn,
  64/64 JSON sağlam, sayılar canlıyla birebir. BULGU→ÇÖZÜM: tar "file changed" exit-1'i unit'i
  FAILURE'a boyuyordu + SQLite sonrası ham tar yarışlı olurdu → yedek unit revize (exit<=1
  toleransı + storage.backup_to tutarlı kopya, canlıda doğrulandı). Çeyreklik ritim sürer.
- **H11 ✅ KOD-HAZIR (tur-2; canlıya sonraki pencerede):** coordinate_descent_search süre-tavanı +
  kibar-iptal (YASA-4 olaylı) + warmup'ta sonda-başına çift nabız (warmup_sprint + hermes_poll —
  açlık-alarmı sınıfı ölür); HERMES_WARMUP_MAX_MIN=300 varsayılan; 17 test. Bekçi eşikleri değişmedi.
- **DEV-GRUBU DARALTMA ✅ (2026-08-03):** ops/import_tarama.py (AST, geçişli dev-kümesi, kurulu-
  metadata'dan eşleme) → HÜKÜM DARALT-GÜVENLİ (17 dev dağıtımının 0'ı çalışma yolunda, 95 dosya);
  dagit.sh [0d] KAPISI oldu (dev-paketi-çalışma-yolunda ya da ölçülemedi → ENGEL) + [3] bayrağı
  koşum-anında ölçer (--no-default-groups destekliyse o, değilse --no-dev'e düşer). YAN BULGU:
  `certifi` beyan-dışı (streamhealth.py:84 opsiyonel import) — beyan kalemi mini-tura verildi.
- **H9 KADEME-B ✅ ÇEKİRDEK (2026-08-03):** flock kapıya indi (write_json/write_jsonl kilidi
  kendisi alır; write_text eklendi; db_backed dalında bilerek yok — çift-kilit kilitlenmesi;
  events.jsonl append-only mezar-taşı testli). 14/14 + süreçler-arası flock kanıtı.
  ~~AÇIK KUYRUK (çağrı-noktası taşıma)~~ **✅ KAPANDI — VE SATIR BAYATTI (2026-08-23 ölçüldü,
  altıncı bayat-beyan vakası):** göçün tamamı Kademe C'de (`e08a436`, 2026-08-09) ZATEN yapılmış —
  bugünkü AST envanteri: 12 yazım/10 modül kapıdan (memory:241 · run:176 · skill_evolve:194 ·
  auth:133 [sabit-tmp gitmiş, 0600 korunmuş] · config:392 · earnings:419,500 · sprint_run ·
  adapters/data:171 · hermes:2889,3042), çıplak yazım SIFIR; bilinçli kapı-dışılar nedenli
  (secrets fsync'li-elle · reflect kilit-dosyası · api BytesIO · mutation/prescreen sandbox).
  Bugün eklenen: `tests/test_h9_cagri_noktasi_gocu_v267.py` (envanter-AST çivisi — yarın eklenen
  kapı-dışı yazımı yakalar + auth._write 2-iplik×20 eşzamanlılık kanıtı + pozitif kontrol 4/4;
  77 passed). YENİ AÇIK UÇ (XS): `sprint.py:525` ortam dosyası düz write_text + SONRADAN chmod —
  kısa 0644 sır penceresi; secrets.py'nin fd-önce-0600 desenine çevrilmeli (motor-dosya penceresi:
  046 inince). **[2026-08-23: ✅ v270 damgası (3d95f8f, aynı gece) — `sprint.py:527` `os.open(O_CREAT, 0o600)` ile doğuyor]**
- **✅ KAPALI (depo tarafı doğrulandı: faz-1 drop-in + `dash_token_credential.sh`; canlı faz-2 ölçülemedi)** · ~~DASH-TOKEN LoadCredential HAZIR-BEKLEMEDE~~ **FAZ-1 CANLIDA (2026-08-23 penceresi, operatör koştu):** rotasyon + credential kanalı kuruldu (50-dash-credential.conf), yanlış-token→401 canlıdan kanıtlı; faz-2 (ortam-kanalı-sıfır) opsiyonel sonraki adım. _(eski metin: 2026-08-03; etkinleştirme OPERATÖR bakım-penceresi):_
  drop-in'ler deploy/oracle-a1/meridian.service.d/ (faz-1 LoadCredential, faz-2 ortam-kanalı-sıfır)
  + dash_token_credential.sh (rotasyon/kurulum/doğrulama/geri-alma; faz-2 farksal ölçümlü).
  LoadCredential ana birime BİLEREK yazılmadı (kaynak-dosya-yokken ilk dağıtım panoyu düşürürdü).
  ÖLÇÜLEN YÜZEY: token bugün her LLM alt-sürecinin ortamında (serve.sh env-devri) — faz-2 kapatır;
  api.py CREDENTIALS_DIRECTORY okuyucusu mini-turda.

- **REDDEDİLDİ (bizim gerçekte):** Litestream/SQLite-PRAGMA/DuckLake (Meridian'da SQLite YOK —
  state dosya+Redis; el kitabının varsayımı yanlış) · Pandera (karantina-v2 + bars_integrity zaten
  ölçülmüş özel koruma) · GE/Temporal/K8s/SBOM/fail2ban/staging (el kitabı da reddediyor) ·
  SDD çerçeveleri (kart+brief disiplini zaten SDD-lite).
- **H8 GİT** ✅ 2026-07-31 (operatör onayıyla): yerel git init, 863 dosya ilk commit `d9c3f24`;
  .gitignore güncel (state/ [goal/bounds hariç] + backups/ + .env dışarıda — sır taşınmaz);
  `dagit.sh`'a kirli-ağaç kapısı eklendi (yarım-iş canlıya gidemez; bilinçli istisna --kirli-gec).
  YENİ SÖZLEŞME: tur başına commit; dosya-ayrıklık artık git-diff ile DENETLENEBİLİR.
- **H9 SQLite defter çekirdeği ✅ CANLIDA (2026-07-31 ~10:56 UTC penceresi; operatör koştu):**
  6/6 varlık parite-digest'le taşındı (shadow_books dahil); app-gözü birebir (95/94457.91/v3);
  WAL aktif; .migrated geri-dönüş arşivleri yerinde; MERIDIAN_DB=off acil anahtarı hazır.
  Kademe A: meridian/storage.py (WAL + synchronous=NORMAL + busy_timeout + foreign_keys) +
  trades/trade_plans/scoreboard/portfolio/equity_curve/shadow_books → state/meridian.db;
  parite-digest'li idempotent migrasyon (dbmigrate --uygula); store.py API'si korunur.
  Kademe B: kalan TÜM JSON yazımlarına merkezî atomik-rename + flock (store.py'de tek kapı —
  "süreç-içi kilit" tehlike sınıfı yapısal kapanır). events.jsonl JSONL KALIR (append-only doğru
  biçim). Öğrenme-katmanı dosyaları (hypotheses/validation_ledger) Kademe C'ye ertelendi.
- **✅ KAPALI (hüküm yazılı — Litestream/PRAGMA/DuckLake yeniden değerlendirildi ve karara bağlandı)** · **H10 Litestream/PRAGMA/DuckLake hükmü (SQLite onayı sonrası yeniden değerlendirildi):**
  PRAGMA seti → H9 storage.py'ye gömülü (UYGULA) · Litestream v0.5 → UYGULA-AŞAMALI: önce
  file-replica (ikinci disk yolu + mevcut Mac-pull kapsar; RPO günler→dakikalar), OCI Object
  Storage S3-uyumlu bucket + anahtar OPERATÖRDE (→§8; Always-Free 20GB yeter) gelince gerçek
  off-box PITR · DuckDB → ölçüm tarafında OPSİYONEL okuma aracı (sıfır-risk ATTACH) ·
  DuckLake → RED-ŞİMDİLİK (251-sembol EOD'de katalog katmanının çözdüğü sorun bizde yok;
  tetik: bar arşivinin Parquet'e taşınması gündeme gelirse).
- **✅ KAPALI (`dagit.sh` `F9_LISTE` içerik kapısı kablolu, 2026-08-23)** · **🆕 F9 — DAGİT KAPSAMI DIŞI CANLI ARTEFAKTLAR (denetim §F9, 2026-08-13; v241/v242 dalgası):**
  `deploy/oracle-a1/meridian-sprint@.service`, `deploy/oracle-a1/50-meridian-sprint.rules` (polkit),
  `SOUL.md` ve tick-watchdog **`deploy/oracle-a1/deploy.sh` → “5) hermes-agent” + “6) systemd birimleri”** ile ELLE kuruluyor. `dagit.sh`ta
  bu dosyalara **sıfır atıf** (`grep "deploy/oracle-a1\|SOUL\|tick_watchdog\|polkit" dagit.sh` = 0);
  `dagit.sh` → `[4/5] bakım penceresi` yalnız `meridian meridian-barsarchive` durdurup başlatıyor. **[2026-08-23 KAPANDI: [F9] içerik kapısı dagit.sh'ta, v266; 82b84a0]** Bu **tam olarak
  OB-2'yi doğuran "kurulu ≠ çalışır" sınıfı** — dört artefakt için sürüklenme bekçisi YOK.
  ÖNERİ: `dagit.sh`a repo↔canlı içerik-sha kapısı; en azından RUNBOOK'a "bu dört dosya dagit kapsamı
  dışıdır" satırı (WP5-B'nin "sürüm terfisi" RUNBOOK borcuyla **AYNI TURDA**). *öncelik: yüksek.*
- **AÇIK** (`Ö-49` çapa/beyan çürümesi sınıfı TAM kapanmadı — tahtada `§2 H0` satırı) · **🆕 A17 — KAYNAK-İÇİ ÇAPA BAYATLIĞI (denetim A17, 2026-08-13; davranış YOK, yalnız yorum):**
  `state/goal.yaml:130` sektör-tavanı kuralını `guard.py:352` diye anıyor, gerçeği `guard.py:359`
  (WP11/15g doğru çapayı taşıyor) · `meridian/api.py:1890` "goal.yaml:**27** slippage_bps: 5" diyor,
  gerçek `state/goal.yaml:58`. Tek turda düzeltilir (kod yorumu). *boyut: XS · öncelik: düşük.* **[2026-08-23: ✅ v268 damgası (375abd5) — `state/goal.yaml:130` ve `api.py:2170` çapaları düzeltildi]**

#### WP6-B · ÖLÜ/EZİLEN BİLEŞEN BUDAMASI _(taşındı: Ö-25, eski satır :1037-1058 — 2026-08-13)_
25. **ÖLÜ/EZİLEN BİLEŞEN BUDAMASI (`docs/DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13.md`)** — operatör
    sezgisi ÖLÇÜLDÜ ve doğrulandı: **473 bileşenin %41,4'ü ölü (140) ya da eziliyor (56)**. Ölülerin
    105'i İKİ yapısal olgudan (93 skill bayrağı + 12 registry alanı); tek tek adlandırılmış ölü 35.
    · **25a KALDIR (14):** 8 goal.yaml alanı (en tehlikelileri `backtest_gate` — kapı SÖZÜ verir,
    davranışı yok; `kill_switch_file` — yolu değiştirmek kill-switch'i TAŞIMAZ, `health.py` sabit
    kodluyor) + `execution_v2.tif` + 2 guard sabiti + 12 registry alanı. Emsal: `spy_sma_gate` mezar
    taşı · **25b DAMGALA (6 sınıf):** en acili SKILL ROZETİ — pano "gölge" diyor ama bayrak trading
    davranışını DEĞİŞTİRMİYOR · **25c DİRİLT (4)** — DİKKAT, envanterin "en yüksek öncelik `no_trade_before_bars`
    = MOTOR-EŞİTLİĞİ İHLALİ" hükmü **Rol-1 ÖLÇÜMÜYLE DÜZELTİLDİ (2026-08-13)**: `bar_i`,
    `enumerate(calendar)` üzerinden gelen SEANS SIRASIDIR (`backtest.py:215`) → kural "koşumun ilk 3
    seansında tarama yapma" = REPLAY ISINMA kuralı. Canlının "koşum başlangıcı" kavramı YOK, yani
    `loop.py`nin okumaması eksiklik değil doğal sonuç; etki 1147 seansın 3'ü. Doğru muamele DİRİLT
    DEĞİL **DAMGALA**: `goal.yaml`daki yorum ("skip the first N bars after the open") intraday
    çağrışımı yapıyor ve YANILTICI; ayrıca `guard.LIMIT_KEYS`te durması onu "canlı zarf parametresi"
    gibi gösteriyor — ikisi de düzeltilmeli. Kalan 3 diriltme adayı geçerli · **25d ON EZİLME ZİNCİRİ** adıyla kayıtlı (slot←ısı zarfı ·
    limit_atr←limit_pct · tüm arama uzayı←`probgate.P_BASE=0,80` (16 ret) · keşif bütçesi←üretici
    kuraklığı (llm_pick 102 ↔ armed **1**) · R:R tabanı←bounds alt sınırı (0/409 düşen) · …).
    · **25e ÖĞRENME DÖNGÜSÜ 0 SHIP** — canlı defter: **52 hipotez, 52 ret, 0 ship**; `strategy.yaml`ın
    18 parametresinden 16'sı kodun tohum varsayılanıyla BİREBİR; döngünün tek hayatta kalan ürünü
    `pivot_proximity_pct=2,3`. Bir sürüm (v0003) kodun varsayılanının aynısını ship etmiş ("OOS
    None→None" = ölçülemeyen no-op). *öncelik: 25c ACİL (motor eşitliği), 25e YÜKSEK (öğrenme fiilen
    üretmiyor), 25a/25b orta.*
    · **🆕 25a'ya BİRLEŞTİRİLDİ (denetim C4/A13, 2026-08-13):** eski Ö-28j (`explore_rate` ÖLÜ) ve
      WP-S2 B-1 aynı ölü anahtar ailesidir; **beyan `426b998`'de indi**, açık olan tek şey
      **KALDIR-mı-BEYANLI-KALSIN-mı POLİTİKASI** (emsal: `spy_sma_gate` mezar taşı). Üç yerde üç ayrı
      kalem gibi durmaları birleştirme artefaktıydı.
    · **🆕 25b SKİLL ROZETİ SATIRI WP7'YE TAŞINDI (denetim C10, 2026-08-13):** 93 skill bayrağı motor
      registry'sine bağlı değil, pano "gölge" diyor ama bayrak trading davranışını DEĞİŞTİRMİYOR —
      `DENETIM-OLU-BILESEN…:340` bunu "**En acil damga**" sayıyor. Skill katmanı TEK yerde toplansın
      diye kalem **WP7**'de yaşar; burada yalnız bu çapraz-referans kalır.
    · **🆕 25c ÜSTÜN-HÜKÜM CÜMLESİ (denetim C5, 2026-08-13):** yukarıdaki `no_trade_before_bars`
      **DAMGALA** hükmü Rol-1 ölçümünün hükmüdür ve kaynak belgenin (`DENETIM-OLU-BILESEN…:346`)
      **DİRİLT** diyen D-3/1 maddesi **bu satırla AŞILMIŞTIR**. (Yazılmazsa gelecek bir tur belgeden
      kalemi yeniden açar.)
    · **🆕 25e → WP3'e bağlandı (2026-08-13):** "öğrenme döngüsü 0 ship" kalemi WP3-A'nın (Ö-28)
      kökleriyle aynı olguyu sayıyor — burada kayıt olarak kalır, iş WP3'te yürür.

#### WP6-C · DEĞER-EŞİTLİĞİ KAPISININ GENİŞLETİLMESİ _(taşındı: Ö-26, eski satır :1060-1064 — 2026-08-13)_
_(denetim C8/D3: öncelik **yüksek → ACİL.** Ö-20a tam bu kapının sınıfıydı ve kapı onu bir kez
YAKALADI — `meridian/watchdog.py:2064-2066` (repo) "Ölçüm sırasında bir kez AYRIK yakalandı (0,04
iken goal 0,16)". Doğrulandı: `EQUIVALENT_TRUTHS` bugün **4 çift** (`watchdog.py:2058/2072/2083/2096`).
Kapı **Ö-20'nin yapısal panzehiridir**; her ekleme tek satır.)_
26. **DEĞER-EŞİTLİĞİ KAPISININ GENİŞLETİLMESİ (Ö-20/split hattının devamı)** — 8. desen canlıda
    (3 eşit / 0 ayrık / 1 beyanlı) ama `EQUIVALENT_TRUTHS` yalnız 4 çift taşıyor; split denetiminin
    **26 KAPISIZ çifti** onun genişleme listesi (sektör tavanı dörtlüsü, `DISCIPLINE_MIN_RR`,
    `min_sample` yedeği, alarm jetonları, registry-bayrağı↔ARMED_SETUPS…). Her ekleme tek satır.
    *öncelik: yüksek — bugün bulunan split'lerin çoğu bu kapıyla kendiliğinden yakalanırdı.* **[2026-08-23 GÜNCEL — GÖVDE BAYATTI, yetkili hâl §2 TAHTA/26 satırı: `EQUIVALENT_TRUTHS` bugün 9 olgu (`watchdog.py:2221`; ayrık 0); "26 KAPISIZ çift" çürüdü — envanter 08-22: 12 kaynağında kapanmış + 5 bağlı + 9 gerekçeli-bağlanmamış (`docs/ENVANTER-DEGER-ESITLIGI-2026-08-22.md`); kalan açık yalnız ortamlar-arası 3 çift]**

#### WP6-D · Gözlemlenebilirlik/dağıtım iyileştirme adayları ✅ ARŞİV _(taşındı: Ö-2; 2026-08-23 KAPANDI — YEDİ KALEMİN YEDİSİ DE ZATEN KAPALIYMIŞ, beşinci bayat-beyan vakası)_
_(2026-08-23 ölçümü: a-e + hermes:1965 göçü + CREDENTIALS_DIRECTORY okuyucusu — hepsi 08-02→08-09
dalgalarında kapanmış [`f713815` açılış senkron-doğrulama `hermes_runtime.py:367` · senkron_ts her
dönüşte `hermes.py:2849` · kota≠yapılandırmasız ayrı imza sınıfları `hermes.py:1903-1937` ·
`_agent_budget_refund` üç ağa-çıkmayan yolda iade `hermes.py:1556` · `3142e70`
candidate_review_empty_parse `hermes.py:3510` · `e08a436` hermes yazımları kapıdan ·
`3e3a331` `_read_dash_token` CREDENTIALS_DIRECTORY-önce `api.py:191-236`]; adanmış çiviler
v168/v169/kademe-c/v184 = 69 passed. Tek kalan kuyruk [dagit versiyonlu-state adımı] F9 ajanına
devredildi. RPD cache-hit bacağı: yüzey YOK — `_agent_call` hattında önbellek kısa-devresi mevcut
değil, kalem konusuz.)_
2. ~~**Gözlemlenebilirlik/dağıtım iyileştirme adayları (2026-08-02 canlı vaka; tam metin §8 snapshot'ta korunur)**~~ —
   hermes-CLI kalemleri a-e (servis açılışında senkron-doğrulama · pano senkron-sonuç zaman-damgası ·
   bekçi "kota"≠"yapılandırmasız" ayrımı · RPD bütçesi ağa çıkmayan çağrıyı saymasın ·
   `candidate_review_empty_parse` uyarısı) + dagit versiyonlu-state adımı (diff-göster + onaylı-kopya;
   goal/bounds git-izli ama diğer versiyonlu state için). *gerekçe: canlı vaka kökenli sessiz-ölüm/
   görünürlük boşlukları · boyut: S-M · bağımlılık: bakım penceresi · öncelik: düşük-orta.*


#### WP6-E · 🆕 §4 BOŞALTMASI 2026-08-23 — havuzdan taşınan üç kalem _(usul 2026-08-13 emsaliyle aynı; gövdeler AYNEN, izler §4'te)_
_(taşındı: §4-49, eski satır :1553-1718 — 2026-08-23; kalemin beyan ettiği sahip adı WP-H = bugünkü WP6)_
- **🟡 49. ÇAPA/BEYAN ÇÜRÜMESİ: YASA KURULDU, SINIF TAM KAPANMADI — AÇIK KALEMLER** _(2026-08-15, ölçüldü; sahibi WP-H)_
  Docstring turu iki dersi ölçümle kanıtladı ve ikisi de bu turda TAM kapanmadı:
  · **ELLE SÜPÜRME SINIF KAPATMAZ.** ~117 satır çapası elle sembole çevrildi ve "sınıf kapandı"
    ilan edildi; aynı turda docstring eklemek YENİ bir çürük üretti ve bir test onu DONDURDU
    (literalin literale eşitliği — asla kırılamaz). Çözüm `codelaw.stale_line_anchors` YASASI oldu
    (report() `ok` kapısında, pozitif kontrol + `çapa-mezar-taşı` muafiyetiyle). Yasa kurulur
    kurulmaz kendi kodunu iki kez yakaladı (işaretsiz `except`; `_note_unscanned` yanlış arite).
  · **YASA KAPSAMI DAR.** Ölçüldü, KAPATILMADI: (a) yasa yalnız `meridian/**.py` tarar — `docs/`
    ve `tests/` içindeki çapalar denetimsiz (RUNBOOK'ta 73 çapa var ve üretici yeniden ürettikçe
    elle bayatlıyor); (b) DÜZ METİN çapaları (`satır NNN`) ve ÇAPRAZ BİÇİM çapaları
    (`goal.yaml:27`) desenin DIŞINDA — ölçülmüş bayat örnekleri var; (c) docstring'e gömülü
    SABİT SAYI aynı çürüme sınıfı ve hiçbir dedektör görmüyor (bu turda `0,08`→`0,16` ve `0,04`
    vakaları elle düzeltildi, yerine `0,16` YENİDEN gömüldü).
  **⚡ 2026-08-21 YENİDEN ÖLÇÜLDÜ — LİSTELENEN KUSURLARIN ÇOĞU ZATEN KAPANMIŞ.** Bu kalem
  bayatlık HAKKINDAYDI ve kendisi bayatlamıştı; aşağıdaki liste ölçümle güncellendi:
  · ~~`_site_key` `isdigit()` guard'ı~~ ✅ **KAPALI** — `codelaw.py:786` artık `isascii() and isdigit()`
  · ~~`_gate_why` tail dalı savunmasız~~ ✅ **KAPALI** — `margin` artık PARAMETRE (dışarıdan gelir)
  · ~~`report()` altı kez tarıyor (7,75 sn / 576 parse)~~ ✅ **KAPALI** — ölçüldü: **1,75 sn / 97 parse**
    (kalemin kendi tahmini "96 parse'a iner"di; 97 çıktı)
  · ~~`ops/runbook_uret.py` sıralama KOPYASI~~ ✅ **KAPALI** — artık `codelaw._site_key`i İMPORT ediyor
  · ~~`_GRAPH_CACHE` tek slot~~ ✅ **KAPALI** — anahtar `(root, damga)` çiftine çevrildi (cloud turu)
  · ~~yasa yalnız `meridian/**` tarar~~ 🟡 **KISMEN** — `tests/` ve `ops/` eklendi
    (`_EK_CAPA_KOKLERI`); **`docs/` HÂLÂ DIŞARIDA** ve RUNBOOK'ta 73 çapa var.
  **GERÇEKTEN AÇIK KALANLAR (2026-08-21 ölçümü):**
  · **`docs/` çapa yasasının dışında** — RUNBOOK üretilirken satır numaraları kayar, denetimsiz.
  · **28 çözülemeyen çapa** (`line_anchor_unresolved`, hepsi `hedef_yok`): `broker.py` yorumları
    `olcum.py:178`e bakıyor ama o ad ölçüm dizinlerinde ÇOK KEZ geçiyor, tarayıcı hangisi
    olduğunu seçemiyor. Kapıyı DÜŞÜRMÜYOR (körlük RAPORLANIYOR, sessizce yutulmuyor) ama
    çapraz-dizin çapası hâlâ çözülemez bir sınıf.
  · Düz metin (`satır NNN`) ve docstring'e gömülü SABİT SAYI çürümesi — dedektör yok.
  **BU TURDA YAKALANAN TAZE VAKA (yasa çalışıyor):** `alpaca.py`ye `equity_on` eklenince
  `test_acil_dogruluk_v196.py:463`teki `alpaca.py:487-491` çapası BAYATLADI ve yasa onu
  ANINDA yakaladı (`report()["ok"]=False`). Düzeltme satır güncellemek DEĞİL, **sembole
  çevirmek** oldu (`alpaca.coid_sinifi docstring GRUP KEMERİ maddesi`) — doktrin gereği:
  satır çapası sessizce çürür, sembol çapası yüksek sesle.

  **ESKİ AÇIK KUSUR LİSTESİ (tarihçe — 2026-08-15, çoğu yukarıda kapandı):**
  · `reflect._gate_why` tail dalı savunmasız: çağıran `effective_margin` (aşınma dahil) ile
    reddediyor ama `_gate_why` çıplak `GATE_MARGIN` ile sınıyor; aşınma devredeyken akış son
    return'e düşüp `cand_tail['var_r']` okuyor — legacy sözlükte tail YOK → `TypeError`.
  · `codelaw.report()` aynı ağacı ALTI kez tarıyor: 7,75 sn, 576 `ast.parse`, 30,3 MB (ölçüldü).
    Tek paylaşılan parse memosu 96 parse'a indirir.
  · `_GRAPH_CACHE`/`_CLAIMS_CACHE` `clear()` ile TEK SLOT: farklı `root` ile bir çağrı üretim
    girdisini atıyor; testlerde ~16 zorunlu yeniden kurulum ≈ 23 sn (ölçüldü).
  · `declared_claims` site listeleri hâlâ SÖZLÜKSEL sıralı (`_site_key` yalnız `artifact_graph`
    çıktılarına takıldı) — tek raporda iki farklı sıra.
  · `_site_key` guard'ı `isdigit()`: Unicode üst-simge rakam `int()`i patlatır (`isascii()` gerek).
  · `ops/runbook_uret.py` aynı sıralama mantığının KOPYASINI taşıyor ve ikisi zaten farklı
    davranıyor (biri ValueError atar, diğeri (site, 0)'a düşer).
  **EK AÇIK KUSURLAR (2026-08-15 ikinci inceleme dalgası, ölçüldü):**
  · **ÖNBELLEK KÖRLÜĞÜ YUTUYOR (en değerlisi):** `artifact_graph` `_GRAPH_CACHE` isabetinde
    HİÇBİR dosya okumadan döner, dolayısıyla `_note_unscanned` çalışmaz ve `UNSCANNED` BOŞ kalır.
    Reprodüksiyon: bozuk dosyalı ağaçta ilk çağrı 2 körlük kaydeder, `UNSCANNED.clear()` sonrası
    ikinci çağrı (aynı mtime → isabet) 0 kaydeder. Bu, bu turda yazılan "bekçi kendi körlüğünü
    RAPOR eder" sözleşmesini ikinci çağrıdan itibaren çürütür; `report()` yalnız DİĞER (önbeleksiz)
    fazlar yeniden kaydettiği için tesadüfen doğru kalıyor. Düzeltme: körlük kayıtlarını da
    önbelleğe koy ve isabette idempotent biçimde geri yaz.
  · `_gate_why` "tek çağıranı `_gate_eval`" iddiası YANLIŞ: `tests/test_audit_fixes.py` ikinci
    çağıran ve `margin` GEÇMİYOR (yani çıplak `GATE_MARGIN` yolunu sınıyor).
  · `_gate_why`ın `tail_ok` parametresi gövdede HİÇ okunmuyor (kuyruk dalı koşulsuz düşüş).
  · `_site_key` docstring'i `isascii() and isdigit()`i "int()'in kabul ettiği küme" sayıyor;
    gerçekte int() ASCII-dışı ondalıkları da kabul eder (`isdecimal()` doğru yüklemdir).
  · `tests/test_wpm_okuma_netligi_v182.py` hâlâ "0,04 / 0,08" eski sayılarını yorumda taşıyor;
    oran testi ikisi de ikiye katlandığı için YEŞİL kalıyor (görünmez bayatlık).
  · `declared_claims` `host_modules` iki ŞEKİL döndürüyor: sink/human'da modül adı, pattern'de
    çağrı-yeri dizgesi — tüketici sessizce atlar.
  **TABANDAN DEVRALINAN CANLI YASA İHLALİ (bu turun eseri DEĞİL, ölçüldü):**
  · `validation.deflated_sharpe` SIFIR VARYANSLI seride `None` yerine SÖZLÜK döndürüyor
    (`sharpe_gozlem=1.9e15`) — yani ölçülemeyen yerde SAYI ÜRETİYOR. Bu doğrudan UYDURMA
    YASAĞI ihlalidir ve DSR yolu ship hükmüne bağlı olduğu için değeri yüksektir.
    Çivisi zaten var ve KIRMIZI: `test_hafta3a_v119::test_D_dsr_taban_altinda_None_doner_SIFIR_DEGIL`.
  **ÜÇÜNCÜ DALGA — KAPANANLAR (2026-08-16, ölçüldü, testli):**
  · **ÖNBELLEK KÖRLÜĞÜ SINIFI KAPANDI (üç örneğin ÜÇÜ de).** İkinci dalgada yalnız
    `_GRAPH_CACHE` düzeltilmişti ve o düzeltme de BOZUKTU: saklama filtresi `u.get("_kok") == root`
    idi, oysa `_note_unscanned` `_kok` anahtarını HİÇ yazmıyor → filtre daima boş → `or
    list(UNSCANNED)` yedeği tüm defteri (BAŞKA taramaların körlüğü dâhil) önbelleğe koyup isabette
    geri yazıyordu. Artık seçim EVRE ADIYLA yapılıyor ve saklama/geri-yazma TEK gövdede
    (`_onbellek_oku` / `_onbellege_yaz`); `_CLAIMS_CACHE` (grafiğin evrelerini de saklar, çünkü
    isabet dalında `artifact_graph` hiç çağrılmaz) ve `ledgers._WRITERS_CACHE` (`UNPARSED`,
    `setdefault` ile) aynı gövdeye bağlandı. Dört yeni test, üçü negatif-kontrollü.
  · **ÇAPA YASASININ KENDİ KÖRLÜĞÜ SAYILIR OLDU.** `stale_line_anchors` hükmü kurulamayan çapayı
    (`hedef_yok` / `ikircikli`) sessiz `continue` ile atıyordu — körlük-raporlama yasasının kendi
    körlüğünü gizlemesi. `cozulemeyen_out` + `report()['line_anchor_unresolved']`(_by_reason)
    eklendi; canlı ağaçta **16 çapa** (hepsi `hedef_yok`: olcum.py, skill_usage.py,
    hermes_constants.py, engine.py — ağaçta olmayan dosyalar). `ok`u ETKİLEMEZ (ölçülemeyen ihlal
    değildir), ama artık ADIYLA sayılır.
  · **KAPI TUTARSIZLIĞI KAPANDI.** `uv audit` yoklaması yalnız `ci_duman.sh`e eklenmişti;
    `ops/kapilar.sh` bu yüzden KALICI KIRMIZI'ydı (uv 0.8.17'de alt-komut yok). Aynı ÖLÇÜLEMEDİ
    hükmü oraya da taşındı. Ayrıca duman kapısına bekçinin KENDİ testi eklendi
    (`test_codelaw_kor_nokta_v214`, +40 test / ~4 sn) — sözleşmeyi kıran değişiklik artık PR'da
    görünür, yalnız Rol-1'in tam suite'inde değil.
  · **ÜÇ CANLI UYDURMA DÜZELTİLDİ.** (a) `api._spend_detay` `olculemeyen` sayacı `nonlocal` olarak
    ÇAKIŞAN kümeler üzerinde ~5 kez artıyordu ve panoda `olculemeyen_satir/satir_n` kesirine
    düşüyordu — yani "5/2" gibi imkânsız bir dürüstlük sayacı; pay artık paydayla aynı kümeden tek
    geçişte. (b) `analytics.learning_automation` `bekci_notu` panoda "mechanism_beats.json beyanlı
    bir lağımdır ve dışarıdan okunmaz" yazıyordu; dosya DECLARED_SINKS'ten çıkarılmış ve
    `api._hat_cizelgesi` onu panoya taşımıştı — metin gerçeğe çekildi, KARAR (kadans damgasından
    ölçme) gerekçesiyle birlikte korundu. (c) `recompute._source_corpus` YASA 4 gerekçesi TERS
    kutupluydu ("eksik korpus yalnız DAHA AZ bulgu üretir"); okuyucu testi `nm not in _src_text`
    olduğu için kısalan korpus DAHA ÇOK yetim üretir — yön düzeltildi ve `__pycache__` elenerek
    düşen dosya sayısı 2→0 yapıldı. Docstring'i de `tests/`i korpusta sayıyordu (modülün KENDİ
    ölçütünün tersi) — düzeltildi.
  · **İKİ DAYANIKLILIK DELİĞİ KAPANDI.** (a) `secrets._write_file` atomik ama fsync'SİZDİ —
    `os.replace` yer değiştirmeyi garanti eder, verinin diske indiğini ETMEZ; güç kesintisi
    SIRLARI siler ve ajan sessizce deterministik moda düşerdi (modülün kendi
    `secrets_file_unreadable` notunun anlattığı sınıf). `store._atomic_write` sözleşmesine
    hizalandı: fsync + dizin fsync (en iyi çaba). (b) `health.write_heartbeat` "çok yazarlı nabız"
    docstring'iyle birlikte KİLİTSİZ oku-değiştir-yaz yapıyordu — yani onardığı kayıp-güncelleme
    hatasının daha dar bir penceresi. `store.file_lock` kapsamı oku+değiştir+yaz'ın tamamına
    çekildi.
  · **MİMARİ SAYILARI YENİDEN ÖLÇÜLDÜ.** `pyproject.toml` "20 modüllük güçlü-bağlı bileşen"
    diyordu: gerçek **33** (84 modülün %39'u; grimp + Tarjan, ad listesi yorumda). Çekirdek-altyapı
    döngüsü "config→obs→store→config" (3) yazılıydı: gerçek **6 modüllük SCC** (+notify, secrets,
    storage). "Her ikisi de SIFIR istisnayla geçiyor" iddiası da yanlıştı — iki sözleşmenin
    dördü `ignore_imports` kaydı taşıyor. README: uç sayısı 77→**73** (58'i `/api`), "onay 5 dk'da
    düşer" → gerçek ömür **tek seans** (`_enrich_stale_plans`, `expired`), "L0→L1 terfisini
    guard.py zorlar" → ölçen `analytics.py` (karne, 3 kalem `manual=True`), reddeden `guard.py`
    (TEK kural: `autonomy_level < 1` + canlı mod).
  **DÖRDÜNCÜ DALGA — AÇIK KALEMLER KAPATILDI (2026-08-16, ölçüldü):**
  · **DSR SIFIR-VARYANS İHLALİ KAPANDI** (listenin canlı hükümdeki tek kalemiydi).
    `validation._moments`teki `var <= 0` kapısının eşiği MUTLAK SIFIRDI ve kayan noktada sabit bir
    seri oraya HİÇ inmez: `[0.01]*40` için ortalama 1 ulp sapar, std ~5e-18 çıkar, Sharpe
    **1,9e15** olarak "ölçülmüş" görünürdü. Kapı artık GÖRELİ (serinin kendi ölçeğinin `1e-12`
    katı — araştırma eşiği değil, float64 bağıl hassasiyet tabanının dört mertebe üstü). Gerçek
    seriler DEĞİŞMEDİ (dsr 0,791686 aynı); `test_hafta3a_v119` 61/61.
  · **`report()` ALTI TARAMADAN BİRE İNDİ.** Ölçüm (aynı makine, öncesi/sonrası): soğuk
    **20,09 → 10,50 sn**, `ast.parse` **576 → 96** (modül başına tam bir kez = teorik alt sınır),
    sıcak **1,54 → 0,82 sn** ve sıcak yolda `ast.parse` **192 → 0**. Yol: dosya-başına
    mtime+boyut damgalı `_kaynak_oku`/`_ast_oku` memosu; `scan_source`un gövdesi `_scan_agac`a
    ayrıldı ki dosyadan gelen çağıran ağacı memodan alsın. Bedel: tepe bellek 110,5 → 122,7 MB.
    Memo SONUÇ değil GİRDİ önbelleğidir: ayrıştırma düşerse memoya hiçbir şey girmez ve
    `_note_unscanned` her fazda eskisi gibi çalışır — körlük sözleşmesi etkilenmez.
  · **TEK-SLOT ÖNBELLEK KALKTI.** `clear()` gerekçesi "damga değişince eski girdi geçersiz" idi,
    ama anahtar `(root, damga)` ÇİFTİ: farklı bir `root` ile tek bir çağrı üretim girdisini damgası
    HÂLÂ GEÇERLİYKEN atıyordu. Artık ekleme sıralı, sekiz slotlu, en eski düşer.
  · **YASA KAPSAMI `tests/` ve `ops/`a AÇILDI** ve açılır açılmaz **14 çürük çapa** buldu (hata
    ayıklayan kişiyi yanlış satıra gönderen CANLI iddialar; `ops/` zaten temizdi). On dördü de
    sembole çevrildi (`loop.py:1942` → `loop.mirror_submit_armed` gibi); biri yapılandırma
    dosyasını da kapsıyordu (`litestream.yml` → `storage.PRAGMAS`).
  · **`_gate_why` İKİ KUSURU.** (a) `tail_ok` parametresi imzada VARDI ama gövdede HİÇ okunmuyordu
    — son dal, kuyruk geçmiş olsa bile koşulsuz "kuyruk düşürdü" yazıyordu; artık `tail_ok=True`
    ile buraya düşmek "gerekçe BU ZİNCİRDE değil" der (sebep uydurmaz). (b) "tek çağıranı
    `_gate_eval`" beyanı yanlıştı — `test_audit_fixes.py` ikinci çağıran ve `margin` geçmiyor.
  · **`_site_key` DOCSTRING'İ.** "`isascii() and isdigit()` tam olarak `int()`in aldığı kümedir"
    YANLIŞTI: `int()` ASCII-dışı ondalıkları da alır (`isdecimal()`). Guard bilinçli bir ALT
    KÜMEDİR (satır numaraları ASCII'dir) — davranış korundu, iddia düzeltildi.
  · **`runbook_uret.py` KOPYASI KALKTI.** İki uygulama zaten ayrışmıştı (kopya sayı olmayan
    parçada `ValueError` ile çöküyor, `_site_key` `(site, 0)`a düşüyordu); betik artık
    `codelaw._site_key`i içe aktarıyor. Üretilen RUNBOOK **birebir aynı** (diff boş).
  · **`declared_claims.host_modules` TEK ŞEKLE İNDİ.** sink/human'da modül adı, pattern'de çağrı
    yeri taşıyordu — tek ad, iki şekil. Pattern'de modül adları yerlerden TÜRETİLİYOR, yerler
    `desen_yerleri` alanında ADIYLA duruyor (alan üç kayıtta da VAR).
  · **`test_wpm_okuma_netligi_v182` BAYAT LİTERALİ.** Yorum "bugünkü sözleşme: 0,04 / 0,08"
    diyordu; ikisi de ikiye katlandığı için (bugün 0,08 / 0,16) oran testi yeşil kalmış ve
    bayatlık GÖRÜNMEMİŞTİ. Çivilenen şey artık oran; sayılar hata mesajından okunuyor.
  **HÂLÂ AÇIK — ve ikisi de ÖLÇÜLDÜ, sonra BİLİNÇLİ bırakıldı:**
  · **`docs/` yasa kapsamına ALINMADI.** Ölçüm: 2324 çapa, **704 çürük**. Ama 668'i TARİHLİ teşhis
    belgelerinde (`SISTEM-DENETIMI-2026-08-02.md` 190, `ARTEFAKT-TARAMASI-2026-08-07.md` 158, …) —
    onlar tarihli birer KAYITTIR, yazıldıkları gün doğruydular ve geriye dönük "düzeltmek" tarihi
    tahrif etmek olurdu. Kalan **36'sı üretilen `RUNBOOK.md`de** ve kaynağın kendi yorum
    bloklarının kopyasıdır: gerçek kalem budur ve üreticinin işidir (mezar-taşı işareti kopyaya
    taşınmıyor). Düz metin (`satır NNN`) ve çapraz biçim (`goal.yaml:27`) çapaları hâlâ desen dışı.
  · **Çapa BAŞKA bir kod satırına kaymışsa yakalanmıyor** (yalnız boş/yorum/menzil-dışı ölçülür).
    Bunu kapatmak için çapanın gösterdiği İFADEyi de saklamak gerekir — biçim değişikliği, ayrı tur.
  · **33'lük SCC'nin BÖLÜNMESİ** — operatör kararı, mekanik düzeltme değil.
  *öncelik: düşük — canlı hükümde açık kalem KALMADI (DSR bu turda kapandı).*
_(taşındı: §4-38, eski satır :1909-1914 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-38`; §4'te iz satırı)** · **🆕 38. İKİ MODÜL YORUMU ARTIK YANLIŞ** _(2026-08-14, v245-D devri; sahibi WP6/A17)_
  `run.py:194-204` ("sınır tam olarak o çiftten ölçülür") ve `sermaye.py:30-35` ("eğriye nokta
  eklenmiyor **çünkü** sınır son noktadan okunuyor") — ikisi de v245-D ile **YANLIŞLANDI**: sınır
  artık son noktadan okunmuyor ve eğriye nokta ekleniyor. `test_sermaye_ayristirma_v150::test_B3`
  gerekçesi güncellendi (tests/ ajanın sınırındaydı); iki modül yorumu açık kaldı.
  A17/Ö-34(a) ile aynı sınıf: **kaynak-içi beyanın koddan geri kalması.** *boyut: XS.*
_(taşındı: §4-34, eski satır :1932-1943 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-34`; §4'te iz satırı)** · **🆕 34. KAYAN OTURUMUN İKİ SESSİZ SÜRÜKLENMESİ** _(2026-08-14, v245-B turunun ADIYLA devrettiği kalemler; sahibi WP6)_
  Kayan oturum (v2 jeton) uygulandıktan sonra **iki beyan eskidi** ve ikisi de test kırmızısı
  ÜRETMİYOR — yani sessiz:
  **(a)** `meridian/codelaw.py` `DECLARED_SINKS["auth.json"]` çapası `api.py:420` diyor, satır
  artık **426**; ayrıca yazan listesi `set_password`/`rotate_key`/`issue_session` sayıyor ama
  **`refresh_session`** (→`_sign`→`_key()`) aynı sınıftan ve **adı geçmiyor**. Test yalnız terim
  VARLIĞINA baktığı için kırmızı yok. Bu, denetim A17'nin (kaynak-içi çapa bayatlığı) yeni bir
  örneği — ve tam da `codelaw`ın kendi kovaladığı sınıf.
  **(b)** `meridian/auth_cli.py status` "oturum ömrü : 12 saat" basıyor; artık EKSİK — doğrusu
  "12 saatlik **KAYAN** pencere + **7 gün mutlak tavan**". Operatörün elindeki tek CLI beyanı bu.
  *öncelik: düşük-orta · boyut: XS (iki metin) · not: (a) çapa-bayatlığı sınıfı olduğu için
  A17 ile birlikte ele alınmalı — tek tek düzeltmek deseni kapatmaz.*

### PRG-07 — Skill Katmanı 🆕
_(YENİ CEPHE 2026-08-13; eski: WP7 · Ö-24 — bugüne dek kendi WP'si yoktu)_

**KAPSAM (tek cümle):** Skill'lerin gerçekten çağrılıp çağrılmadığı, çağrı izinin tutulduğu ve
skill katmanının karar yüzeyine (motor registry'si + terfi kapısı) bağlanıp bağlanmadığı hattı.

_(taşındı: Ö-24, eski satır :1022-1035 — 2026-08-13; **24a ✅ KAPANDI → §8 arşiv**. Gövde metni
AYNEN korunur, yalnız tek paragraftan madde-madde biçime alındı — kelime değişmedi.)_

**SKILL KATMANI — üç ayrı kusur (denetimler: `DENETIM-SKILL-CAGRI-IZI`, `ARASTIRMA-SKILL-ETKIN-KULLANIM`)**
- **24a ÇAĞRI İZİ GERİLEMESİ — ✅ KAPANDI** (v242 turu; 2026-08-13, denetim B7). Tam metin §8 arşivde.
- **24b SOUL.md KİLİDİ ✅ AÇILDI** (2026-08-13; yasak çıktı biçimine daraltıldı) ama **HİÇ SINANMADI**
  — çağrı oranı %1,1'den ne olacak, ölçülecek.
- ~~**24c ANA DANIŞMA YOLU ÖLÜ** — son 7 günde 788 `agent_call`, 385 boş, **1** başarılı görüş;
  skill'i oraya bağlamak bugün anlamsız. _(Bu kalem §5 KOVA-3/NOUS_MODEL'in GEREKÇESİDİR — denetim F5.)_~~
  **[2026-08-24 KAPANDI-BAYAT:** "788/385/1" iddiası **2026-08-13 tarihli ve penceresi 08-06..08-13**
  — o pencere bir **RETRY FIRTINASIYDI**, sağlıklı hacim değil (günlük kırım: 08-09 156/155 boş ·
  08-10 151/150 · 08-11 150/150 · 08-12 29/20 dönüş başlıyor · 08-13 153/73 · **08-14 142/0 boş =
  yol dirildi** · 08-16..21 toplam 9 çağrı, 8 dolu / 1 zaman-aşımı = sağlıklı düşük tempo). Görüş
  üretimi AYNI-GÜN damgalanıyor (`llm_opinions_stamped` 08-19 n=9 · 08-20 n=2 · 08-21 n=5;
  `llm_calibration.json` `n_plans_with_opinion=374`). En güçlü çürütme: bu "ölü" yol üzerinden
  danışman **2026-08-14T21:03:34'te TERFİ ETTİ** (`AUTHORITY_CHANGE`: "LLM danışman yetkisi AÇILDI
  — R farkı 0.638, n=100 çift"). Son çağrı 08-21 Cuma 21:44; 08-22/23 hafta sonu → sessizlik
  seans-dışı kadansla uyumlu, arıza kanıtı DEĞİL. **ÇAPRAZ ETKİ (Rol-1'e, hüküm DEĞİL):** 24c, §5
  KOVA-3/C4 `NOUS_MODEL` kaleminin güncel GEREKÇESİYDİ ve o satır zaten "kalem KAPANMIŞ olabilir"
  notu taşıyor — 24c kapandığına göre C4 kapanış adayıdır, doğrulama Rol-1'de.
  Belge: `docs/ELEME-WP7-2026-08-23.md` §1.**]**
- ~~**24d PİLOT-S1** — 2 skill (`edge-strategy-reviewer`, `weekly-performance-digest`) × DOLGU yolu
  (çalışan tek nokta), 91 günlük kuyrukta A/B; `n_pairs` 4→~51→~95, kol başına ~46 (terfi tabanı 30
  aşılır); başarı eşiği ve 5 başarısızlık ölçütü önceden yazılı.~~
  **[2026-08-24 KAPANDI-BAYAT:** tasarımın ÜÇ ÖNCÜLÜ de bugün yanlış — ① "terfi tabanı 30 pilotla
  aşılır" → taban **PİLOTSUZ** aşıldı (`n_pairs=100`, `promoted=true` 08-14'ten beri): pilotun var
  oluş amacı (örneklem kuraklığını DOLGU yolundan kırmak) kendiliğinden gerçekleşti; ② "DOLGU yolu
  çalışan tek nokta" → yol artık tek değil (review yolu dirildi, deterministik görüş defteri canlı
  yazıyor) ve DOLGU vetosunun kendisi (`loop.py:1103-1122` `llm_veto_strip`) terfiden bu yana
  **0 kez ateşlendi** — pilotun ölçeceği yüzey 9 günde tek örnek üretmedi; ③ iki pilot skill'i
  bugün canlı review ön-yüklemesinde YOK ve EDG-019 evreninde `llm_baglamli_motor_kosturmuyor`
  dışlamasında — A kolu tasarlandığı hâliyle bugünkü canlı yapılandırmaya oturmuyor. Kalan meşru
  soru ("ön-yükleme görüş KALİTESİNİ değiştiriyor mu") **24b'nin zaten açık ETKİ ölçümü penceresine
  devredilir**; yeniden açılacaksa BUGÜNKÜ tabandan yeni ön-kayıt kartı ister, eski sayılarla
  koşulamaz. Belge: `docs/ELEME-WP7-2026-08-23.md` §2.**]**
- ~~**24e ÇEKİMSER TEŞVİKİ (yapısal)** — `destekle` kovası BOŞ, `r_gap=null`; `_opinion_history`
  çekimseri "nötr" sayıyor → hep çekimser diyen model hiç yanılmaz ve hiç terfi etmez. Terfinin
  ASIL duvarı bu.~~
  **[2026-08-24 KAPANDI-BAYAT:** "terfinin ASIL duvarı" iddiası canlıda çürüdü — iddia yazıldıktan
  **BİR GÜN SONRA**: `n_pairs` 4→**100** · destekle/karşı/çekimser 0/1/3 → **10/14/76** · `r_gap`
  null→**0.857** (destekle +0.396 · karşı −0.461) · `promoted` false→**true** (2026-08-14T21:03'ten
  beri). Bugünkü çekimser oranı taze-100 çiftte %76, tüm görüşlü planlarda %73, ama **son-30g plan
  görüşlerinde %40** (25 görüşün 10'u) — yeni modelle çekimserlik belirgin düşüyor. **Bağlayıcı
  kısıt teşvik değil HACİMdi:** yol dirilince kovalar doldu ve kapı açıldı. Mekanizmanın kök
  parametreleri kayda geçer (config/state'te ayar YOK, dördü de kod): `analytics.py:1125-1128`
  (`LLM_PROMOTE_MIN_PAIRS=30` · `LLM_PROMOTE_MIN_BUCKET=8` · `LLM_PROMOTE_R_GAP=0.3`) ·
  `analytics.py:1169-1173` (`r_gap` yalnız destekle/karşı'dan; çekimser sayılır ama karara girmez) ·
  `hermes.py:3797-3798` (`_opinion_history` çekimseri "nötr" sayar — **teşvikin tek davranışsal kod
  noktası**) · `hermes.py:3687,3910` (istem üç seçeneği eşit sunar). Rol-1 ileride teşvik ölçümü
  İSTERSE ölçülebilir tek kaldıraç (3)'tür ve koşullu kart-taslağı eleme belgesi §3'te hazır
  (`family: llm_cekimser_tesviki`, K += 1); (1)/(2)'yi oynamak EŞİK İCADIDIR (kart + Rol-1 ister).
  Varsayılan hüküm: KAPAT. Belge: `docs/ELEME-WP7-2026-08-23.md` §3.**]**
- **✅ KAPALI (`24f` 2026-08-24'te `24h` rozet-damgası ailesine devredildi — BİRLEŞTİR)** · ~~**24f SKILL.md ↔ KOD BAĞI YOK** (31 dosyada 3 atıf; `strategy.py`de `skills` geçen 0 satır).~~
  **[2026-08-24 BİRLEŞTİR: 24h rozet-damgası ailesine devredildi.** Sayısal kanıt bayatladı: bugün
  `skills` modülünü **10** meridian modülü import ediyor (api · backtest · counterfactual · hermes ·
  scheduler · reflect · skill_gorus · loop · skill_evolve · skills); SKILL.md'ye 4 modül + `web/app.js`
  + 5 test atıf yapıyor; `strategy.py`de "skill" geçen **3** satır var (712, 1022, 1059);
  `skills.py:120 ENGINE_IMPLEMENTED` "motor FİİLEN neyi koşturuyor" dürüstlük kümesini tutuyor ve
  skill_gorus evreni SKILL.md-klasörü (`llm_baglamli_motor_kosturmuyor`) ile motor-koşturulanı zaten
  ayırıyor. **Kalan çekirdek** — SKILL.md İÇERİĞİNİN motor davranışına sözleşme/test bağı yok ve 93
  bayrak motor registry'sine bağlı değil — **24h ile AYNI yapısal boşluktur** (C10: "En acil damga");
  iki kalemi ayrı tutmak aynı işi iki satırda saymaktır. Gövde 24h'ye katlandı, WP7 listesi bir kalem
  kısaldı. Belge: `docs/ELEME-WP7-2026-08-23.md` §4.**]**
- ~~**24g SPRINT SIZINTISI** — sandbox canlının PAYLAŞIMLI skill dizinini buduyor (bugün 17:15'te 4
  symlink), "izole" vaadi ajan katmanında tutmuyor (v242).~~
  **[2026-08-24 KAPANDI-BAYAT:** düzeltme İNDİ ve canlıda ÜÇ koşumda tuttu. v242 kapısı
  (`sprint.kum_havuzunda` yapısal ölçütü + `hermes.sync_agent_skills` B-yolu atlaması) canlı kodda
  dağıtık (`/opt/meridian/meridian/hermes.py` doğrulandı). Canlı kanıt — üç kum-havuzu koşumunda
  (20260813-202316 → 08-14 02:34/02:35 · 20260814-220214 → 08-15 04:35 ×2 · 20260821-220656 →
  08-22 04:42/04:43) `agent_skills_sync_atlandi_kum_havuzu` uyarısı bastı ve söküm BLOKE oldu
  (`n_sokulecek=4`, dört `fmp=req` skill — 08-13 vakasının birebir senaryosu). Canlı ana
  `events.jsonl`'da 08-13'ten beri TÜM `agent_skills_synced` olayları `pruned=[]`; `~/.hermes/skills`
  bugün 46 girdi / **30 symlink** = 08-13 onarımı sonrası kapsamla aynı. Sızıntının yeniden
  üretileceği koşul (kum havuzunda FMP anahtarı yok → küçük enabled set) üç koşumda da OLUŞTU ve
  kapı üçünde de tuttu — bu **bayrak testi değil GERÇEK-KOŞUL kanıtıdır**.
  Belge: `docs/ELEME-WP7-2026-08-23.md` §5.**]**
- **✅ KAPALI (`24h` 2026-08-24 doğrulama turunda BAYAT-KAPALI çıktı)** · **🆕 24h SKİLL ROZETİ DAMGASI (taşındı: Ö-25b, denetim C10 — "skill katmanı tek yerde toplansın"):**
  93 skill bayrağı motor registry'sine bağlı değil; pano "gölge" diyor ama bayrak trading davranışını
  DEĞİŞTİRMİYOR. `DENETIM-OLU-BILESEN…:340` bunu **"En acil damga"** sayıyor. *boyut: S · öncelik: orta.*
  **[2026-08-24: 24f gövdesi buraya KATLANDI (BİRLEŞTİR) — SKILL.md içeriğinin motor davranışına
  sözleşme/test bağı olmaması ile 93 bayrağın registry'ye bağlı olmaması AYNI yapısal boşluktur;
  kanıt satırları yukarıdaki 24f kaydında güncellendi.]**

**[2026-08-24 ÇAPRAZ ATIF — `EDG-2026-019` kill#1 hükmü KARTTA İŞLENDİ:** eleme turunun kapsam-dışı
canlı bulgusuydu (`docs/ELEME-WP7-2026-08-23.md` §7-1) — katman ÇALIŞIYOR (`meridian/skill_gorus.py`
v218'de yazılmıştı, canlıda 5.500 görüş satırı) ama `skill_gorus_durum.json` `kill_p95` **"KILL"**
diyordu (p95_pay 6.57 > tavan 0.10) ve kod hükmü KAYDEDİP UYGULAMIYORDU. Rol-1 hükmü aynı gece indi
ve karta işlendi: **katman KAPATILIR** (E-partisi v278), yönetişim ihlali (katmanın KARTSIZ sevk
edilmiş olması) kartta kayıtlı, yeniden-açılış YALNIZ resmî ölçümle. Bu kalemin WP7'deki izi budur;
ayrıntı §7 2026-08-24 kaydında.]**

**🆕 §4 BOŞALTMASI 2026-08-23 — havuzdan taşınan iki kalem (usul 2026-08-13 emsaliyle aynı; gövdeler AYNEN, izler §4'te):**
_(taşındı: §4-31, eski satır :1945-1956 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-31`; §4'te iz satırı)** · **🆕 31. `active_model()` KÜNYE KUSURUNUN İKİNCİ EVİ + UYDURMA KORUMASI EKSİĞİ** _(2026-08-14, v245-A turunun ADIYLA devrettiği iki kalem; sahibi WP7)_
  **(a) İKİNCİ EV:** `hermes.py:3987` `chain_text` → `out.update({... "model": active_model()})` —
  `candidate_review`de bu tur kapatılan kusurun **birebir aynısı** (Katman-B nous değerlendirme
  kayıtları "istenen"i taşıyıp "cevap veren" sanılıyor). v245 sözleşmesi dar tutulduğu için
  DOKUNULMADI; kapatılması `cevap_veren_model()` hazır olduğu için tek satırlık iştir.
  **(b) UYDURMA KORUMASI TAŞINMAMIŞ:** `active_model()` (`hermes.py:727`), `_model_id("nous")`in
  (`:655`) sahip olduğu "yerel ajan + `NOUS_MODEL` yok → **None** (uydurma yasağı)" korumasını
  TAŞIMIYOR. ÖLÇÜLDÜ: aynı durumda `_model_id('nous')=None` iken `active_model()='Hermes-4-405B'`
  döndü — yani **defterde hiç çağrılmamış bir model adı** durabilir. Yeni `model_istenen` alanı
  eski anlamı birebir korumak için bilerek `active_model()` taşıyor, dolayısıyla o alan bu
  yapılandırmada uydurma ad taşıyabilir; `model` alanı taşımaz (o ölçülmüş).
  *öncelik: (a) düşük-orta, tek satır · (b) orta — uydurma yasağının kendi yüzeyinde ihlali.*
_(taşındı: §4-40, eski satır :1876-1880 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-40`; §4'te iz satırı)** · **🆕 40. `nous_eval` yeni künye alanlarını defterine taşımıyor** _(2026-08-14, v246-B devri; sahibi WP7)_
  `chain_text` artık `model_kaynagi`/`model_olculemedi`/`model_istenen` üretiyor ama
  `nous_eval.haftalik_degerlendirme` (`nous_eval.py:695-699`) yalnız `.get("model")` okuyor; iki
  kalıcı defter (`nous_eval_runs.json`, `improvement_proposals.jsonl`) beyanları taşımıyor.
  Tek satırlık iş; v246-B'nin dosya sınırı dışındaydı. *boyut: XS.*

### PRG-08 — Pano ve Operatör 🟡
_(eski: WP8 · WP-UX yeniden-tasarım + WP-P kontrol-odası doktrini + Ö-3 F8)_

**KAPSAM (tek cümle):** Operatörün gördüğü yüzeyin kendisi (WP-UX = icra) ve o yüzeyin kabul çıtası
(WP-P = kontrol-odası doktrini) — ikisi ayrı rol, tek cephe.

#### WP8-A · Yeniden-tasarım programı _(eski WP-UX gövdesi; yön: docs/TASARIM-YONU-2026-08-07.md, operatör onaylı, BAĞLAYICI)_
- **Girdi ölçümleri (bitti):** BASELINE-2026-08-06 (25 bulgu, 4×cid-4; araç kör noktası: detect
  app.js'in 7.511 satırında 0 bulgu) · PATTERN-ETUDU-2026-08-06 (11 platform, 81 iş; 22 FIRSAT,
  6 modül adayı, 10 yasaya-aykırı desen elendi) · UX-SADELESTIRME-DENETIMI (23 Nielsen bulgusu).
  HÜKÜM: pano eksik değil BAĞLANTISIZ — dürüstlükte kategoride önde, birleştirmede geride.
- **GİT OTORİTESİ DÜZELTMESİ (2026-08-09 — AŞAĞIDAKİ D0-D6 İŞARETLERİ BAYATTI):** D0-D6 dalgalarının
  HEPSİ git'te İNDİ; hash'ler tek tek doğrulandı (D2-D6 2026-08-07, D3-b `6bb2bb9` 2026-08-09 16:45).
  Kalan AÇIK: **D3-c altı modül** (delist-arşivi/C2-5 Massive kararına bağlı + kart ZORUNLU) +
  **D3-b F3-F13/F15** yüzeyleri. NOT: `docs/KESIF-WP-MKP-2026-08-09.md` §0 "WP-UX D0-D6 İNMEDİ" dedi —
  o BAYAT bu ROADMAP'e güvendi (git yasağı) ve ~16:30'da ölçtü; **git ÇÜRÜTTÜ** ve bu düzeltme onu kapatır.
- ~~**D0 acil doğruluk** 🔄~~ → **✅ İNDİ (v196 `c59dfcc`, 2026-08-07):** mod dört durumda da ölçümden
  basılır · ffill hücre-düzeyinde etiketli · `?? 0` triyajı 30/167 düzeltildi (137 listeli kuyrukta —
  D-serisi dışı kalıntı kuyruk, `?? 0` çıcır tavanı 181). Özgün: mod halted/stale'de kayboluyordu.
- ~~**D1 jetonlar + beş renk rolü** 📋~~ → **✅ İNDİ (v197 `6025d82` + çivi `0220e6b` + D2-a `07deab7`):**
  iki katmanlı jeton mimarisi (hue adı bileşende YOK); mod KENDİ yapısal kanalını aldı; koşulsuz emisyon
  15→0; D1 çivi 7 kırmızı kapandı (iddialar zayıflatılmadan); D1 şablon-içi ters-tırnak P0'ı D2-a kapadı.
- ~~**D2 kart sözleşmesi + yeni IA** 📋~~ → **✅ İNDİ (D2-a v198 `07deab7` + D2-b v199 `c0d8238`):**
  tek kapak anatomisi (özet=hucreGovde), açık kart 77→52; 7 sayfa→5 yüzey (işe göre), 6 olay yüzeyi
  (obs 12 jetonun 12'si), 8 yinelenen çift tekilleşti, 1220 test yeşil. Özgün IA: ①Bugün ②Karar ③Sağlık
  ④Öğrenme ⑤Kilitler; runbook.html EMİLİR, workflow.html EMEKLİ, landing.html KALIR+onarılır (1,53:1).
- **D3 fırsat yüzeyleri + modüller** 🔄 KISMİ İNDİ: D3-UI **✅ (v200 `ac86de9`)** — C1'in on işi 10/10
  defter→uç→pano zinciri TAM, "üretiliyor ama görünmüyor" kovası kapandı · D3-arka üç modül **✅ (v197
  `7b9158a`)** — ajan telemetrisi + ham-iz defteri + vaka sabitleme · D3-b F1/F2/F14 **✅ (v229 `6bb2bb9`,
  2026-08-09)** — kâğıt-canlı ayrışması + sapma kökü + iki-kademeli eşik+NO_DATA. **AÇIK:** D3-b F3-F13/F15
  yüzeyleri + **D3-c ALTI MODÜL** (operatör: hepsi yazılır; delist-arşivi/C2-5 Massive kararına bağlı +
  kart ZORUNLU). Özgün C1 on işi: reddedilen-karar karnesi 4.988 satır · emir yaşam-döngüsü · /api/spend
  SIFIR web çağıranı · canlı zaman çizelgesi · rollback sicili · regresyon kırılımı · denetim izi ·
  "bugün neden hiçbir şey olmadı" · çıkış-nedeni kırılımı [stop_gap 1.973R] · skor olgunlaşması.
- **D3-b F5 ✅ İNDİ (v230, 2026-08-09) + KAPSAM YENİDEN-SINIFLANDIRMASI (WP-UX ajanı KANITLADI):** F5
  alarm-taksonomisi (`watchdog.alarm_gunluk` YASA-6 boşluğu, F1/F2/F14 sınıfı — v192'den üretiliyor,
  hiç okunmuyordu) indi. Nominal "12 F-kart + 6 D3-c modül" frontend dosya-sınırından (app.js, api.py YOK)
  ÇOK büyük; kanıtlı gerçek harita:
  - **(a) frontend-inebilir + temiz yetim veri: YALNIZ F5 ✅** (indi).
  - **🟡 DOĞRULANMADI (2026-08-31 denetimi — F3/F4 backend kalemlerinin akıbeti bu turda ölçülmedi)** · **(b) BACKEND gerekli (ayrı WP, api.py — WP-UX değil):** F3 pre-flight/what-if · F4 decision-rewind ·
    F11 outage↔return time-series-join · F12 pre-tuning (config.py yazar).
  - **(c) ZATEN yüzeyde → çift-kaynak riski (v191'in savaştığı şey; KAPANDI say):** F9 gate/lock
    (`gatekeeper.plans[].gate_reasons` planRowFull'da) · F10 capacity (`portfolio_heat` app.js:5289) ·
    F13 K-penalty (`deflate` app.js:4719).
  - **🟡 DOĞRULANMADI (2026-08-31 denetimi — F6/F7 viz kalemlerinin akıbeti bu turda ölçülmedi)** · **(d) viz/etkileşim (ayrı özellik):** F6 saved-queries · F7 agent-path graph (C2-2 v197 zaten indi).
  - **AÇIK** (`F8` durum sözlüğü — tahtada `§2 H1` satırı, KISMEN) · **(e) kanonik okuyucu gerekli (uydurmadan inemez):** F8 status-dictionary (→ §4 öneri, en iyi aday) ·
    F15 allocation-history (per-period defter okuyucusu YOK).
  - **D3-c modüller:** C2-1/C2-2/C2-3 ✅ DONE (v197 "D3-arka"); AÇIK: **C2-4 LEAN** (Task-4, LEAN yok) ·
    **C2-5 delist-arşiv** (operatör Massive-kararına bağlı + kart ZORUNLU, veri yok) · 6. çalışma adayı.
  → **WP-UX FRONTEND kısmı ESASEN BİTTİ**; kalanlar backend WP'leri / operatör-blok / viz-özelliği.
- ~~**D4 yazı tipi** 📋~~ → **✅ İNDİ (ölçüm `f8097d0` + uygulama v201 `9cd27de`):** kazanan Recursive
  (Sans+Mono Linear, OFL, binary-ölçümle); üç yüzeyde KENDİ-BARINDIRMALI, CSP SERTLEŞTİ (Google origin
  düştü). Geist EMEKLİ (operatör kararı) uygulandı.
- ~~**D5 sertleştirme** 📋~~ → **✅ İNDİ (git otoritesinde "D5 jeton birliği", v208 `11bdc02` + merge
  `4560362`):** dört yüzey tek sözlük — landing/workflow rol katmanının 40 jetonu + runbook kendi paleti
  tekilleşti; CPL hükmü 92→78 düzeltildi.
- ~~**D6 doğrulama** 📋 (audit/critique önce-sonra, on ilke kanıtlı, devir)~~ → **✅ İNDİ (git otoritesinde
  "D6 tip rampası", `b71f65b` + `64009ca`):** runbook tip rampası gövde-sapması ÖLÇÜLDÜ ve ÇÜRÜTÜLDÜ
  (15/26/18→14/28/20px, telafi panonun KENDİ .md'sinden); D6 kanıt zinciri kapatıldı (korpusu ÜRETEN kod
  da depoda — EDG-016 sınıfı). D6 hükmü t3 korpus-tazeleme kadansında TUTUYOR (`d993bd1`/`e278466`/`8ce3123`:
  satır kaymaları hükmü değiştirmedi, 7 aile yeşil).
- Kapı: her dalgada kapsam testleri → tek otoriter suite → tek dagit → canlı doğrulama.
- ~~🆕 AÇIK ÜRETİM ARIZASI (2026-08-13)~~ ✅ **v243 KAPATTI (08-14; üç kopyanın üçü de 08-22 Ö-49 taramasında kapatıldı):** pano açılışı `/api/diagnostics`
  üzerinden tıkanıyor — `parity_report` soğuk çağrıda **16,7s** (tohum sonrası defter 9× büyüdü);
  v243 turu bunu kapatıyor. *öncelik: yüksek (operatörün ilk gördüğü yüzey).*

- **🟡 DOĞRULANMADI (2026-08-31 denetimi — `broker_status` pano yanlış-güveni bulgusunun akıbeti canlı pano ister)** · **🆕 M11 TARAMASI BULGUSU (2026-08-24): `broker_status` PANO YANLIŞ-GÜVENİ — yazan bacak indi,
  okuyan bacak inmedi.** `gap_veto` ve `armed_dropped_*` değerlerinin ÜRETİMDE hiçbir tüketicisi
  yok; `app.js:1218`'in `else` dalı bu planları **"gönderilecek"** rozetiyle çiziyor ve
  `app.js:2499` `bekleyen` sayacına yazıyor — yani VETO EDİLMİŞ/DÜŞÜRÜLMÜŞ plan, operatöre
  "sırada bekliyor" diye görünür. Bugün soğuk (41 günde 0 olay) = UYUYAN yanlış-güven; bir sonraki
  gap-veto gününde yanıltır. Düzeltme S-boyut (else dalına değer-farkındalı rozet + sayaç
  dışlaması) — dürüstlük-UI sınıfı, kart istemez. *öncelik: yüksek (operatör yanılgısı üretir).*
- **✅ KAPALI (`broker.py` ÖLÜ-ALAN DAMGASI[M11] bloğu indi, çivisi `tests/test_pano_durustluk_v280.py`)** · **🆕 M11 BULGUSU — `entry_law` yan tablosunda 4 ÖLÜ alt-alan + İKİ ÇÜRÜK BEYAN:** `offset_kaynak`,
  `ref_kaynak`, `limit_bps`, `olay` diske yazılıyor ama üretimde hiç okunmuyor (tek tüketicileri
  testler); ikisi kodda *"okuyucusu E2 defteri"* diyor — canlı `entry_execution.jsonl`'ın 30
  satırında o alanlar YOK (çürük beyan, Ö-49 sınıfı). *işlem: damgala ya da kaldır — 25a emsali.*

#### WP8-B · Kontrol-odası doktrini / kabul çıtası _(eski WP-P gövdesi; 2026-08-01 UI el kitabı — gerçekle çarpıştırılmış; kontrol-odası + finans-izleme kanıt tabanı: HP-HMI/ISA-101, Airbus dark-cockpit, EEMUA 191, Few/Tufte)_
- **ZATEN VAR:** tabular-nums (19 kullanım) · dürüstlük-UI (None≠0 = YASA, provenance rozetleri,
  sermaye-köken, nabız-bayat beyanı) · koyu tema · CSP script-src-self · yoğun-uzman düzeni.
- **P1 Sessiz-Hat ✅ CANLI (2026-08-01):** 17 bekçi + kilitler + tazelik TEK toplanmış şeritte — sağlıklı
  = "17/17" sönük tek özet, SAPMADA segment açılır; renk yalnız anomalide (ASM 5× tespit kanıtı;
  klinik alarm-yorgunluğuna karşı toplama KRİTİK).
- **P2 Alarm bütçesi ✅ CANLI:** EEMUA 80/15/5 + <10/10dk tepe + <10 duran-alarm canlı gösterge;
  taşkın-toplama.
- **P3 Gauge yasağı ✅:** mevcut 2 gauge → bullet-graph + gömülü-trend + beklenen-aralık bandı
  (Few spesifikasyonu; tek-hue yoğunluk aralıkları).
- **P4 Tipografi ✅ (slashed-zero ölçülüp-gereksiz):** slashed-zero + sağa-hizalı sabit ondalık taraması.
  **DÜZELTME 2026-08-06 (operatör): "Geist KORUNUR" bir YASA DEĞİL.** 2026-08-01'de reddedilen şey
  el kitabının *Inter* önerisiydi; bu, Geist'i dokunulmaz yapmaz — Geist bugünkü YÜRÜRLÜKTEKİdir,
  bağlayıcı taahhüt değildir. Yazı-tipi değişimi AÇIK kalem (ayrı `typeset` turu). Değişmeyen:
  jeton sözlüğü tekliği, iki-zemin, geometri/ölçek/gölgesizlik ve işlevsel çıta (kendi-barındırma
  [CSP dış font-host'a izin vermez] · açık lisans · tam Türkçe aksan · gerçek tabular rakam ·
  eşlenik mono · iki zeminde küçük-punto okunabilirlik/halation).
- **P5 Belirsizlik ✅ (renksiz kanal):** onarım-dolgu/imputation hücrelerinde belirsizlik-görseli +
  bayatlık-solması standardı (Sarma/Kay).
- **P6 ✅ TAM (gündüz turu 2026-08-02 indi — 9 yüzey tek-katsayı, sıfır saf beyaz; 148-çift yeniden-ölçüm, 0 hüküm değişimi):** #000/#FFF → koyu-gri zemin + kırık-beyaz metin (halation);
  WCAG 2.2 AA UYUMLULUK STANDARDI KALIR (APCA yalnız tasarım-yardımcısı — el kitabının kendi
  düzeltmesi: WCAG-3 onaylı değil).
- **P7 ⌘K paleti ✅ CANLI (933 satır, 25+7 komut, iki-adım onay):** tek eylem yüzeyi; kilit/nav/filtre; kısayol-ipuçları;
  CSP-self uyumlu.
- **P9 ✅ (2026-08-02):** kapsama ısı-matrisi (7×6, None-haritası) + tek-hue sequential + CVD-güvenli diverging; jetonlu, AA-ölçülü.
- **P10 Hareket ✅ (koşulsuz-puls söküldü):** prefers-reduced-motion + ≤300ms puls YALNIZ-anomali; skeleton
  sınırlaması kural olarak (zaten kullanılmıyor).
- **RED/UYARLANDI:** APCA-birincil (red) · Inter (red — Geist kalır) · skeleton yaygınlaştırma
  (red — Viget karşı-kanıtı) · ARIA-live genişletme (dar: yalnız kritik alarm/kilit — tek görüşür
  operatör) · Doherty 400ms (Nielsen 0.1/1/10 esas) · P8 confirmed-state zaten mimaride (E1/mutabakat).
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-MKP-2026-08-09.md` §WP-P):** yüzey programı **P1-P10 KAPALI**.
  ~~WP-UX'ten AYRI TEK canlı borç = `docs/RUNBOOK.md` **32 "runbook girdisi henüz yazılmadı"** (P-A —
  HEARTBEAT_STALE/ROLLBACK/CIRCUIT_BREAKER/MIRROR_DRIFT/NAKED_POSITION… alarmlarının Çözüm/betik
  prosedürü boş; kaynak-sözleşmeli/oto-üretilmiş `ops/runbook_uret.py`, kapatmak GERÇEK prosedür yazmayı
  ister — yüzey değil içerik).~~ **→ P-A BORCU ✅ KAPANDI (denetim A7/B8, 2026-08-13):**
  `grep -c "henüz yazılmadı" docs/RUNBOOK.md` = **1** ve o da kuralın kendi tarifi (`RUNBOOK.md:29`);
  alarm bölümleri gerçek prosedürlü (`:67` HEARTBEAT_STALE · `:168` MIRROR_DRIFT · `:304`
  NAKED_POSITION "KALICI RİSKLER / DERSLER" bloklu). **WP8-B artık BORÇSUZ** — "AYRI TEK canlı borç"
  cümlesi düştü. _(Sınır beyanı: kapanış tek `grep` sayımına dayanıyor; üretecin başka bir boşluk
  dilini kullanıp kullanmadığı denetlenmedi — denetim §I.)_ İkinci rol: **WP-P ≠ WP-UX** — WP-P =
  gereksinim/doktrin (HP-HMI/ISA-101/EEMUA-191/Few-Tufte kontrol-odası) = **WP-UX D6 kabul çıtası**;
  WP-UX = yüzey/icra. WP-P yüzey işi YENİDEN AÇILMAZ (WP-UX aynı yüzeyleri düzenler).
- **AÇIK** (`F8` ailesinin WP-P kolu — 15 bekçi + `halt_learning`; tahtada `F8` satırıyla aynı kalem) · **KALAN (WP-P kolu):** 15 bekçi mekanizması + `halt_learning` (aynı desen, ayrı tur). **[2026-08-23: "15" sayısı bayat — F8 tasarım ölçümü 17 bekçi (kalem açık, sayı düzeltildi)]**

#### WP8-C · F8 pano durum-sözlüğü _(taşındı: Ö-3, eski satır :736-740 — 2026-08-13)_
3. **F8 pano durum-sözlüğü (WP-UX kalan F-kartlarının en iyi frontend adayı)** — dağınık `durum`
   alanlarını tek kanonik sözlükte toplar. WP-UX ajanı (2026-08-09) F3-F15 içinden frontend-inebilir
   TEK temiz aday olarak işaretledi (F5 indi; F3/F4/F11/F12 backend, F9/F10/F13 zaten yüzeyde, F6/F7
   viz, F15 defter yok). ÖN ŞART: kanonik bir durum-okuyucu — yoksa dağınık alan sentezi UYDURMA riski
   (önce okuyucu tanımı). *gerekçe: YASA-6 (durum dağınık) · boyut: M · bağımlılık: kanonik durum-okuyucu · öncelik: orta.*


#### WP8-D · 🆕 §4 BOŞALTMASI 2026-08-23 — havuzdan taşınan kalem _(usul 2026-08-13 emsaliyle aynı; gövde AYNEN, iz §4'te)_
_(taşındı: §4-44, eski satır :1804-1814 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-44`; §4'te iz satırı)** · **🆕 44. RENK ROL-SIZINTISININ ÖLÇÜLMEMİŞ İKİNCİ EVİ** _(2026-08-14, v246-D kapsam dışı bulgusu; sahibi WP8)_
  `meridian/web/app.js`in **çalışma-zamanı SVG/inline** stillerinde **33 adet ham değer-katmanı
  jetonu** var (`var(--amber|--green|--red)`; ör. `:9227`/`:9229` delik işareti kehribar, ayrıca
  `:533`, `:3662`, `:3956`…). §4'nin `test_bilesen_kurallari_ham_hue_okumaz` çivisi **yalnız
  `index.html` CSS kurallarını** tarıyor — bu yüzey onun **menzilinde değil**.
  **Tutarsızlık AYNI FONKSİYONUN İÇİNDE:** delik işareti ham kehribar kullanırken üç satır
  ötedeki reset işareti `var(--tx2)` (rol jetonu) kullanıyor.
  Bu, gecenin tekrar eden deseninin bir başka yüzü: **kural konuyor ama bekçisi kuralın yaşadığı
  her yeri taramıyor** — `codelaw` çapası (Ö-34a), `tool_calls` (WP7), `nogo_neden_dagilim` (C6
  yan bulgusu) ve bu, aynı sınıf. *öncelik: düşük-orta · gerekli iş: çivinin menzilini
  `app.js` çalışma-zamanı stillerine genişletmek, sonra 33 jetonu sınıflamak (rol mü değer mi).*

### PRG-09 — QuantConnect 🆕
_(eski: WP9 · WP-QC)_

**KAPSAM (tek cümle):** Platform-içi ölçüm hattı + LEAN yerel motor — veri asla arşiv-kaynağı
değil, tüm ölçümler kart-disiplinli.

- **İlke:** veri platformda serbest/çıkışta kilitli → QC = platform-içi ölçüm + LEAN-yerel motor;
  asla arşiv-kaynağı değil. Tüm ölçümler kart-disiplinli.
- **FREE kuyruk (kart-önce, sırayla):** ① delist-kapsam ✅ ÖLÇÜLDÜ (2026-08-03 EDG-021 v3 koşumu — DUR=None, PK geçti;
  @20 fazla CI-0-içi → kill#1 dalı "ŞÜPHEDE-değerlendirme"; birincil şüpheli evren-kompozisyon
  farkı [günlük üst-250 dilim-medyanı 0,0233 vs full_251 p75 0,0089]; survivorship-yönü ilk
  sayı: hayatta +0,54 vs delist −1,46 @20 betimleyici; ikinci-koşum hakkı tanım-eşitleme —
  operatör kararı; kart hükmü EDG-2026-021'de) · ② EODHD earnings 1998+ tarihsel-dizi fizibilitesi (7-gün-pencere biçim riski) ·
  ③ Quiver insider 2014+ derinlik (2021-öncesi legacy-alan ayrımı) · ④ Morningstar PIT-shares
  (delist isimlerde tarihçe; 45-gün yaklaşıklama şerhi) · ⑤ RETIRED_SYMBOLS çapraz-doğrulama
  (Security Master delist olayları + SPY constituents 2009+) · ⑥ Tiingo+SEC NLP ön-fizibilite
  (R1-4 sınırında küçük örneklem) · ⑦ VIX/SPX rejim-bağlamı (Cash Indices 1998+, CBOE VIX 1990+
  FREE — VIX veri-kilidi kısmen çözülebilir).
- **İkinci-motor pilotu (WP-H kolu):** LEAN Apache-2.0 YEREL (CLI'sız — dotnet/docker; hesap
  gerekmez) + KENDİ Massive/Alpaca barlarımız custom-data ile → tek sinyalde emir-düzeyi
  diferansiyel. + bulut-ikizi FREE B-MICRO (200 bt/gün) elle.
- **AÇIK** — operatör kararı (QC katman yükseltmesi; kimlik `[B-QC-LOGIN]`) · **Operatör kararları (§8'ya):** katman yükseltmesi (Researcher Seat $10/ay — API/otomasyon
  kilidi; koltuk-tek-başına-yeter-mi belirsizliği hesap-içi doğrulanmalı) · ücretli setler
  (Brain $25 / Estimize $75 / SmartInsider $10 — ancak FREE fizibilite sonrası) · ToS-yorumu:
  yerel-indirme yolu Rol-1 önerisiyle İZLENMEZ.
- **EXPLORER DERİN-OKUMA HÜKMÜ (Ek-D — docs/QC-EXPLORER-DERSLERI-EK-D.md; 473 strateji, API-tam-envanter):**
  Explorer da kazanan-deposu DEĞİL — ÖLÇÜLDÜ: medyan OOS-1Y Sharpe −0,035, %50,8 negatif, SPY'yi
  geçen %5,8 (9 gerçek-kazanan, 4'ü Meridian-yakın: 343 B/M+F-Score · 341 TERS-likidite-value ·
  32 · 342); "score"=3-AYLIK Sharpe (aşırı-uydurma makinesi — 478 istisna değil beklenen çıktı);
  %30 ID silinmiş (sağkalan yanlılığı sayıyla). KART-KUYRUĞU REVİZE (Explorer-teyitleriyle yeni
  öncelik): ① PORTFÖY-düzeyi %4-8 tepe-dip kapısı vs isim-bazlı chandelier (ratchet DD'yi
  YÜKSELTMİŞ 31-26; take-profit en zararlı özellik: medyan −0,70/SPY-geçen %0) · ② rejim-KADRANI
  (kapı popülasyon-düzeyi teyit: medyan↑ ama sağ-kuyruk kesik — SPY-geçen %2,6-vs-%8,0; EDG-005
  bağımsız üretildi) · ③ HRP/korelasyon-küme bütçesi (YENİ — 452 DD %17,9; CF(ρ̄) kartının çalışan
  hâli) · ④ EDG-016 evren-koşulluluk ÜÇ-KOL (341 karşı-örneği: düşük-likidite-value OOS-1Y 1,58 —
  EDG-021 motoruyla) · ⑤ ufuk-uzatma 63g→252g (yıllık-rebalans SPY-geçme 4×) · ⑥ tamsayı bayrak-
  skoru (en iyi strateji 343 tam G-Score kalıbı). META-DERSLER: 3-aylık pencere hiçbir karnede
  birincil-sıralayıcı olamaz (kendi karnemizde kontrol → yoksa kill-list'e) · yorum-sayısı negatif
  sinyal (ρ=−0,591) · trend-t-stat çarpanı Explorer'da da YOK (Ek-B kartı teyitsiz ama açık).
  Açık kapı: kod-düzeyi okuma (klon ister — operatör hesabıyla, istenirse).
- **LEARNING-SÜZGECİ HÜKMÜ (Ek-C — docs/QC-LEARNING-SUZGECI-EK-C.md):** metodolojide ÜSTÜNLÜK
  BİZDE teyit (ön-kayıt/walk-forward/purged-CV katalogda yok; ISL makaleleri p-hacking ders-kitabı
  örneği — "nasıl kodlanır" kaynağı, "kanıt" kaynağı DEĞİL). Taşınan somut değer: R1 evren-yaşam-
  döngüsü + R2 SymbolData kalıbı + BC101 L5/L7 evren/ısıtma dersleri (API-bayatlık şerhiyle —
  docs'la çapraz-doğrulamadan kopyalanmaz). ASIL defter-v3 kaynağı: docs research-environment
  üçlüsü (applying-research + META-ANALYSIS [karne-akışımıza en yakın] + object-store).
  Operatöre: sertifika yok, kurs-kaydı yapılmadı, CV değeri sıfır.
- **BİLEŞEN-DERS KARTLARI (2026-08-03 /strategies taraması — docs/QC-STRATEJI-DERSLERI-EK-B.md;
  Rol-1 öncelik sırası, YAŞAYAN kolun üstünde çalıştıkları için (b)-adaylarından ÖNCE):**
  ① REJİM-KADRANI: SPY 12-ay t-stat [−1,+1] SÜREKLİ maruziyet çarpanı (kapı değil) — EDG-005
  hükmünü "kapı yanlış, modülasyon doğru" diye daraltır ya da rejim ailesini kapatır ·
  ② KORELASYON-ÇARPANI: CF(ρ̄)=√(N/(1+(N−1)ρ̄)) brüt-kısıntı — işlem sayısı korunup maxDD
  düşerse %92-aktif de-risk RAMPASI EMEKLİ EDİLİR (tabu-yok mandası kapsamında) · ③ ÇIKIŞ-
  MİMARİSİ: ratchet-olmayan vol-GENİŞLEYEN eşik (DBII) — chandelier "durak maliyeti"
  bulgusunun mekanizma-açıklaması; gölge-v2 varyant kolu olarak · ④ DİNAMİK-EVREN vs statik-251
  (EDG-016 seçici-mi-sıralayıcı-mı — EDG-021 QC motoruyla AYNI turda koşabilir) · ⑤ ikili-bayrak
  skoru + vol-önce koşullu sıralama (tutarlılık sınavları). (b)-KOVASI (8 aday, tam liste Ek-B):
  ilk-3 = 354 idio-skew (EDG-004'ü AÇIKLAMA potansiyeli) · 16 overnight-ayrışımı (sıfır ek veri,
  ÖZELLİK olarak yaşayan kola) · 269+125 kesitsel-mevsimsellik (tek kart, 125 grid-hücresi).
  AYRI TUR: Strategy Explorer taraması (hesap-kapılı — Rol-1 tarayıcı oturumuyla; OOS-cezalı
  skorla filtrelenmiş GERÇEK kazanan kümesi).
- **RED:** canlı katman (sıfır yeni yetenek) · log/scrape dışa-aktarım (ToS) · K-grid'i QC
  optimizasyonuna devir (kart disipliniyle uyumsuz) · ML-eğitim taşıma (Train kotası sembolik) ·
  Benzinga ($120 — Tiingo FREE dururken) · FREE'de lean-cli (sözleşme ihlali).
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-QC-2026-08-09.md`, salt-ölçüm + plan):** FREE QC hesabı **ZATEN
  AÇIK** (2026-08-03 — proje `Fat Apricot Koala`; hesap-açma bloğu KALKMIŞ, kalan tek blok operatörün
  defteri KOŞMASI, EDG-021 boru hattı hazır — §8-11). En düşük-bloklu kalem **⑤ RETIRED çapraz-doğrulama**:
  yerel yarısı BU TURDA koşuldu, **8/8** emekli sembol (ANSS/DFS/FI/HES/IPG/K/PARA/WBA) SP500-üyeliğiyle
  tutarlı; tek QC-adımı 1-hücrelik Security Master delist-olayı sondası (EDG-021'in ölçmediği erişim yolu,
  ②-④'ün delist-vekilini gerçeğe taşır). **C2-4 LEAN "hesapsız"** (Apache-2.0, dotnet/docker CLI'sız) AMA
  "sıfır-kurulum DEĞİL" — bu makinede **dotnet YOK, docker YOK** (makine-kurulum bloğu, operatör-hesap
  değil; boyut L, ayrı tur). **⑦ VIX/SPX** FREE ama ToS **platform-İÇİ** — canlı `regime.py` VIX kapısını
  AÇMAZ ("kısmen çözülebilir" = ölçüm-içi bağlam, canlı-kapı değil); ekleme K-grid'i ÇARPAR, ön-kayıtta beyan.


### PRG-10 — Referans Verisi 🟢
_(eski: WP10 · eski-numaralandırmada WP2 — Basit Referans-Verisi Adayları, EDGAR)_

**KAPSAM (tek cümle):** SEC EDGAR filed-tarihli PIT fundamentals adayları — kapanmış cephe, açık
borç yok; yeni öznitelik ancak KART-önce açılır.

- 2.4 EAP ✅ KAPALI (güç-yeterli). **2.1 ✅ ÇÖZÜLDÜ: SEC EDGAR companyfacts PIT verisi repo'da**
  (research/edgar_facts/; filed-tarihli — dei ilk-ifşa medyan 7 gün; 250/251 kapsam; FMP/operatör
  bileti DÜŞTÜ). **2.2 EDG-013 ✅ YAŞAYAN-ADAY
  (lafzen success: koşullu @20 +0,32% anlamlı + artımlılık; AMA tanı turnover ANA etkisini işaret
  ediyor → kaderi EDG-016'ya şartlı, entegrasyon bekliyor)** · **2.3 EDG-012 ✅ ARŞİV** (yön ters+
  anlamlı, U-eğrisi; REIT/büyüme yapısal) · **2.5 EDG-014 ✅ ARŞİV** (bilgisiz; finans-dışı da) —
  "PIT'siz ASLA" yasası filed-tabanlı as-of ile İLK KEZ meşru sağlandı · **2.6 EDG-016 ✅ SUCCESS —
  YENİ YAŞAYAN SİNYAL: turnover ana-etkisi** (@20 net +0,55% CI-0-dışı; artık üç yöntemle sağ;
  q5 monoton; survivorship-şerhi kalıcı). 2.2/EDG-013 arşive DEVREDİLDİ (etkileşim-tezi düştü).
  ~~SIRADAKİ ADIM 📋: turnover kablolama~~ → **✅ ZATEN İNMİŞ (`5dfca07`, log:414 2026-08-03 dalgası) —
  2026-08-10 doğrulama turu sözleşmeyi kaynak-doğruladı (58/0):** indicators.py:156 `turnover21` (kart
  formülü birebir) · strategy.py:452 bileşik-skor terimi (w_to>0 ∧ not-None; ölçülemeyende FAIL-OPEN) ·
  `entry.w_turnover` bounds.yaml:46 {0–0.40}, strategy.yaml TAŞIMIYOR → canlı etki 0 (default-0 bit-bit
  regresyonlu, test_turnover_kablolama_v149) · gölge-okuyucu üç kanal (component_ic + hermes arama-uzayı
  [canlı ret kanıtı: `hermes_bg_proposal_rejected variable=entry.w_turnover`] + shadow_variants). Bu tur
  ROADMAP bayattı, kod gerçeği önde — kalem KAPANDI; **WP2'de kablolama borcu kalmadı** (öğrenme ölçer).


### PRG-11 — Strateji ve Seçilim 🔶
_(eski: WP11 · Ö-15 seçilim-kalitesi + Ö-29 pullback + Ö-12 ISI otomatiği)_

**KAPSAM (tek cümle):** Ne alıp sattığımızın kendisi — kurulum arsenali (giriş/çıkış), seçilim
kalitesi, boyutlama ve rejim koşulluluğu.

#### WP11-A · SEÇİLİM-KALİTESİ HATTI _(taşındı: Ö-15, eski satır :851-891 — 2026-08-13; **15a/15b/15f ✅ KAPANDI → §8 arşiv**)_
15. **SEÇİLİM-KALİTESİ HATTI — C-sonrası iyileştirme yönü (operatör sorusu 2026-08-12: "bu rakamları
    iyileştirmek için hangi yöne gitmeliyiz")** — 9-kart dalgasının meta-bulgusu: DEBİ KOLU BİTTİ (C'ye
    eklenen her debi/eşik-gevşetme kalemi kaliteyi düşürdü); kalan kaldıraçlar seçilim kalitesi + sermaye
    tahsisi. Sıralı adaylar (her biri kart-önce, C-şasi üzerinde):
    · ~~15a REJİM-KOŞULLU BOYUTLAMA~~ · ~~15b SLOT-YARIŞMASI KABUL POLİTİKASI~~ · ~~15f YEREL
      DUYARLILIK TARAMASI~~ → **ÜÇÜ DE ÖLÇÜLDÜ-KAPANDI (EDG-033 / EDG-034 / EDG-035); tam metinleri
      §8 arşivde** (denetim B3: kapalı alt-kalemler açık havuzda durmamalı). Kalanlar: 15c · 15d ·
      15e · 15g.
    · **15c EVREN GENİŞLETME (kalan TEK kalite-nötr debi kolu):** 251→~400-500 likit isim; eşik
      GEVŞEMEZ, sadece havuz büyür (024 dersi: marjinal bant değersiz — daha çok isim ≠ daha gevşek
      kapı). Bağımlılık: §5-8 FINVIZ Elite / §5-9 delist-bar kaynağı (survivorship). *boyut: M ·
      öncelik: orta (operatör-blok bağımlı).*
      **⚠ DÜZELTME (denetim A16/D9, 2026-08-13): 15c artık bir "DEBİ (throughput) KOLU" DEĞİL.**
      Bağlayıcı kısıt ölçüldü ve ISI çıktı: `EDG-2026-035:57-59` "Bağlayıcı kaynak **ısı zarfı**
      (gerçekleşen tepe tam 5,000R)"; `EDG-2026-039:63-64` "Bağlayan kısıt **SLOT DEĞİL ISI**: 39
      meşgul seansın hiçbirinde slot dolmadı (0/39)". Isı bağlıyorken isim eklemek işlem SAYISINI
      artırmaz; zarfı açmak ise ölçülü zararlıdır (EDG-028). Kalem **seçilim-kalitesi kolu** olarak
      okunur. **ÖNCELİK: orta → ASKIYA** (denetim D9) — çünkü `EDG-2026-026:47-49` AYNI paket için
      "bağlayıcı kısıt **EVREN** (%99.55)" diyor: iki kart iki ayrı tasnifle **zıt manşet** üretiyor
      (bkz. WP11-D uzlaştırma kalemi). 15c'nin ve §5/FINVIZ'in önceliği bu çelişki çözülmeden
      belirlenemez. **[2026-08-23: ASKI KALKTI — C6 uzlaştırma KAPANDI (çelişki DEĞİLMİŞ: iki tasnif aynı huninin İKİ KATIYMIŞ; §2 TAHTA H6 satırı)]**
    · **15d PIT-TEMİZ FAKTÖR SETİ + hermes arama yakıtı (OPT Faz-2'nin girdisi):** 031 dersi — elle
      bileşik-ağırlık YOK; yeni faktörler (EDGAR filed-tarihli earnings-drift, sektör-görece momentum)
      indicators'a kablolanır w=0 ile, hermes arama uzayına bırakılır; benimseme OOS-kapılı. *boyut: M ·
      öncelik: orta.*
      _(denetim C7: OPT Faz-2'nin **yeni ilk müşteri adayı** — eski ilk müşteri Ö-12 kapandı.)_

#### WP11-B · ARSENAL POLİTİKASI — giriş ve çıkış AYNI kanıt çıtasında _(BİRLEŞTİRİLDİ: Ö-15e [:872-873] + Ö-29 [:1077-1083], denetim C9)_
_(Gerekçe: ikisi de TEK yüzeye dokunuyor — `ARMED_SETUPS`, `strategy.py:1029` (repo) — ama zıt
yönde: 15e "yeni aile EKLE (kanıt-önce)", 29 "bir aile ÇIKAR". Tek başlık altında toplandı ve
**29'un önerdiği eşik — cf'de `n≥30` ∧ ort-R CI-alt > 0 — HER İKİ YÖN için standart** kabul edildi.)_
    · **15e SETUP ARSENALİ:** hammer canlı-izlemede, mb EDG-032'de; yeni aile ancak kanıt-önce
      (aday: gap-sonrası-taban). *öncelik: düşük (önce eldekilerin canlı karnesi).*
    · **PULLBACK SİLAHSIZLANMASI — ÖLÇÜLDÜ, KARAR SIRAYA ALINDI** _(taşındı: Ö-29, eski satır
      :1077-1083; denetim F3: **strateji kimliği değişikliği = §5 kalemi** → operatör bacağı §5
      KOVA-2'de görünür, teknik gövdesi burada.)_
29. **PULLBACK SİLAHSIZLANMASI — ÖLÇÜLDÜ, KARAR SIRAYA ALINDI (EDG-2026-039, operatör 2026-08-13:
    "önce diğer işler, bu beklesin")** — hüküm: silahsızlanma ÖNERİLİR ama gerekçe "çıkarmak
    kazandırıyor" DEĞİL, KANIT ASİMETRİSİ. Ölçüm: ΔP&L +3.121$ (CI 0-içi), dd −0,0005, sharpe +0,073,
    işlem n sabit (kapasite doldu). ZAYIFLIK: sonuç tek işleme bağlı (IRM/hammer +2.247$). Pullback'in
    ZARARI ise üç kaynakta tutarlı (replay n=6 **kazanma %0,0** · canlı n=4 −1,00R · cf n=21 −0,97R).
    Uygulanırsa: `ARMED_SETUPS`ten çıkar + yeniden-silahlanma eşiği yaz (cf'de n≥30 ∧ ort-R CI-alt>0).
    Beklerken bedel: her seans slot+ısı+sermaye. *durum: KARAR BEKLİYOR (operatör sıraya aldı).* **[2026-08-23 GÜNCEL: karar VERİLDİ ve UYGULANDI — B1=A (operatör 08-22; c150902): `strategy.py:1059` `ARMED_SETUPS` üçlü (pullback yok), çiviler v260/v92; kalan yalnız canlı dağıtım (043 sonrası suite — kuyrukta)]**
    · **🆕 KAYIT (denetim §E.1/025, 2026-08-13):** EDG-025 "dormant kalır" derken canlı
      `strategy.py:1029` (repo) `ARMED_SETUPS`'ta **momentum_burst VAR** — operatör takdiri, kartta
      yazılı. ROADMAP'te bugüne dek görünmüyordu; arsenal politikasının kaydı olarak burada durur.

#### WP11-C · SLOT↔SEKTÖR TAVANI YAPIŞIKLIĞI _(taşındı: Ö-15g, eski satır :883-891 — 2026-08-13)_
    · **15g SLOT↔SEKTÖR TAVANI YAPIŞIKLIĞI (EDG-035'in yapısal bulgusu, 2026-08-13):** slot tavanı
      fiilen ÖLÜ knob (eşzamanlı tepe 13 < 20; slot25 defteri bayt-özdeş) — ama slot sayısını
      değiştirmek sektör tavanını DOLAYLI değiştiriyor (`guard.py:359`: (sektör+1)/max_open > %40 →
      isim tavanı 20'de 8, 15'te 6). İki ayrı risk-tercihi tek knoba yapışık: "kaç pozisyon" ile
      "ne kadar çeşitlendirme" birbirinden bağımsız sorulardır. ÖNERİ: sektör tavanı paydası
      max_open'dan ayrılıp kendi parametresine bağlansın (kart-önce ölçüm: mevcut davranış korunacak
      şekilde payda sabitlenip slot serbest bırakılırsa ne değişir). *boyut: S-M · öncelik: orta
      (ölü knobu diriltmez ama iki tercihi ayırır) · not: 035 slot15 nokta-farkı (+354$, dd 0.1179)
      tam bu kanaldan geldi — CI 0-içi olduğu için hüküm değil, işaret.* **[2026-08-23: ✅ YAPILDI — `sector_cap_basis` ayrıldı (`guard.py:359`); 620-hücre kalıcı matris; §2 TAHTA H6 satırı]**

#### WP11-D · 🆕 UZLAŞTIRMA KALEMİ — bağlayıcı kısıt EVREN mi ISI mı? ✅ **[2026-08-23 KAPANDI]** _(denetim C6, 2026-08-13; ÖLÇÜM GEREKMEZ — tasnif eşleme turu)_
`EDG-2026-026:47-49` "bağlayıcı kısıt **EVREN** (%99.55)" ↔ `EDG-2026-035:57-59` "Bağlayıcı kaynak
**ısı zarfı**" ↔ `EDG-2026-039:63-64` "Bağlayan kısıt SLOT DEĞİL **ISI**". İki farklı tasnif
(EDG-022'nin kısıt-sınıfı vs `heat_hard` NO_GO sayımı) **aynı pakete zıt manşet** veriyor. Bu bir
ölçüm işi değil, iki tasnifin paydasını eşleme işidir. **BAĞLI KALEMLER:** WP11-A/15c önceliği ·
§5 KOVA-3 FINVIZ kararı. _(Denetim §I sınır beyanı: hangisinin doğru payda olduğu ÖLÇÜLMEDİ.)_ **[2026-08-23: ✅ KAPANDI — C6 uzlaştırma H6 (§2 TAHTA): çelişki DEĞİLMİŞ, iki tasnif aynı huninin İKİ KATIYMIŞ; 15c askısı kalktı]**

#### WP11-E · Kapanmış kalemin izi _(Ö-12 ISI'nın piyasa-koşullu otomatik ayarı)_
**✅ ÖLÇÜLDÜ-KAPANDI (EDG-2026-028, 2026-08-12; denetim B2/D11):** "DOSYA HÜKMÜ: sabit-5R + mevcut
rejim kapısı kalır; kart kapanır (ölçülmüş-red)" — Y1 rejim-harita `+3.074$` CI 0-içi → otomatik YOK,
Y2 vol-hedef `−3.924$` → otomatik YOK. **Tam metin §8 arşivde.** İki artık burada yaşar:
(i) OPT boru hattının "ilk müşterisi" rolü **BOŞALDI** (yeni aday: WP11-A/15d — denetim C7);
(ii) `params_by_regime` haritaları hâlâ BOŞ ve kökü 28d ile aynı → **WP3-A**'da izlenir.

#### WP11-F · Hat notu _(denetim §I biçim düzeltmesi: bu üç satır Ö-16 KORUNUM maddesinin kuyruğuna yanlışlıkla yapışmıştı, :975-977 — asıl sahibi SEÇİLİM-KALİTESİ hattı)_
    NOT: çıkış-mühendisliği hattı BİLİNÇLİ dışarıda — 027/029 iki kartla ölçüp eledi (ATR-trail yeterli).
    *gerekçe: sharpe 0.285 pozitif-ama-ince; sıradaki çarpan işlem sayısı değil işlem SEÇİMİ · bağımlılık:
    dağıtım-sonrası ilk ölçüm dalgası · öncelik: yüksek (OPT Faz-1 kablolamasıyla eş-zamanlı gidebilir).*

#### WP11-G · 🆕 §4 BOŞALTMASI 2026-08-23 — havuzdan taşınan kalem _(usul 2026-08-13 emsaliyle aynı; gövde AYNEN, iz §4'te; §4-35'in (b) yarısı — (a) yarısı WP5-G'de; ortak başlık satırı iki hedefe de kopyalandı)_
_(taşındı: §4-35b, eski satır :1924-1930 — 2026-08-23)_
- **✅ TAŞINDI (havuz `Ö-35`(b); §4'te iz satırı)** · **🆕 35. 15g TURUNUN DEVRETTİĞİ İKİ KALEM** _(2026-08-14, v245-E; sahipleri WP5 ve WP11)_
  **(b) `backtest.py:149` ÖLÜ YEREL — İKİNCİ SEKTÖR KURALININ TOHUMU** _(WP11)_:
  `max_sector_pct = float(limits["max_sector_exposure_pct"])` atanıyor, **hiç okunmuyor** (replay
  sektör tavanını `guard.classify_gate`e devrediyor, `backtest.py:377` — yani ayrıştırma replay'i
  otomatik kapsıyor, ikinci uygulama YOK ve bu İYİ). Ama az önce ayrıştırılan politikanın adını
  taşıyan ölü bir yerel, kullanılan `max_open`/`max_pos_r` satırlarının üç satır altında duruyor:
  birileri "bağlarsa" **ikinci ve ayrışmış bir sektör kuralı** doğar — `guard.check_trade`
  docstring'indeki tur-12 ayrışma sınıfı. *KALDIR ya da DAMGALA (25a/25b deseni).*

## §4 ÖNERİ HAVUZU (backlog) — sınıflandırılmamış yeni öneriler _(eski: §2)_

- **[TSK-112] Hafıza ▸ Varlıklar: düğüm tıklaması → varlık künyesi paneli (CP entities-view birebirliği; vekil `/entities/{id}` + `entity_id` süzgeci)** — status: DONE(2026-09-03 görsel tur onayı 12:40Z) · born: 2026-09-02 · owner: rol1 · size: S-M · trigger: —
  What: (status notu 2026-09-03 gece: KOD İNDİ — 12-A vekil f4fcbb3 [/varlik + entity_id süzgeci doğrulandı; açık: kimlik yol-parçası duvarı tutarlılığı] + 12-B UI 345a5cd [künye çekmecesi + zaman çizelgesi, veri.ts hataEki tek kapı, v380]; dağıtım sonraki pencere [tam suite]; DONE = operatör görsel turu.) CP `entities-view.tsx` (v0.9.2 = ebad4782 :232-237, :287, :432-517) düğüme tıklayınca varlık künyesi (ad · anılma sayısı · ilk/son görülme · kimlik) + o varlığa bağlı kayıtların zaman çizelgesini (`memories/list?entity_id=`) açar; bizde takımyıldız düğümleri tıklanamaz (ekranda gerekçesiyle yazılı). Kalem: vekile `GET /api/hindsight/varlik?bank=&id=` (→ `/entities/{id}`) + `/liste`ye `entity_id` süzgeci (upstream `list_memories` parametresi, T1 R1 ölçümü) + panel.
  Why: T6-B incelemesi Q1 — birebirlik defterinde açık kalem; bağ LİSTESİ ise CP'de yok (Meridian icadıydı, kaldırılması kabul edilmiş bedel).
  Ref: TSK-108 T6-B inceleme (task-6b-review.md Q1); `hindsight-clients/go/api/openapi.yaml` @ ebad4782 `get_entity` / `list_memories.entity_id`.
- **[TSK-121] Pano komşu kopyaları tek kaynağa: `Bildiri` ×3 · `BayatSerit`/`YukleniyorIskeleti` ×2 · `Olculemedi` ×13** — status: DONE(2026-09-05 operatör görsel onayı; kod 2211977) · born: 2026-09-03 · owner: rol1 · size: S-M · trigger: —
  What: (KOD TAMAM 17:52Z: commit 2211977 — Olculemedi ×13→1 (olculemediKur, altı aile HEAD gövdeleriyle birebir, incelemede bağımsız doğrulandı), Bildiri ×3→1, BayatSerit/YukleniyorIskeleti ×2→1; kisa→kisaMetin 30 çağrı yeri; v323 pano-geneli 565 çağrı (sınıf-A boşluğu Huni.tsx'te düzeltildi — tek beyanlı metin değişimi); v403; 510 passed; bundle pano-J6CDxFmr.js. Push suite #10 sonrası; DONE damgası görsel turdan sonra.) (status notu 17:03Z: BRIEF HAZIR — keşif: Bildiri ×3 / BayatSerit-YukleniyorIskeleti ×2 markup birebir (düz paylaşılan bileşen, ajan imzası çağrı yerinde eşlenir); Olculemedi ×13 dört-altı gövde ailesi (satir/hucre/kpi/span/ikonlu/tooltip; portfoy `kisa: string`) → kabuk-enjeksiyonlu tek bileşen, her varyant HEAD gövdesiyle birebir kıyas; v323 pano-geneli (567 çağrı yeri, taban yeniden kalibre); v403. SIRA: TSK-121 → TSK-117 (göç tek yerde). Sevk TSK-118 commit'i sonrası.) TSK-113 (`Kapi` 7→1, 2026-09-03) aynı sınıfın komşularını ölçtü ve kapsam dışı bıraktı: `Bildiri` üç tanım (markup özdeş, prop adları farklı), `BayatSerit`/`YukleniyorIskeleti` ikişer, `Olculemedi` ON ÜÇ tanım. İş: TSK-113 deseni (`ui/src/pano/parcalar/` ortak modülü, kabuktan türetim, re-export, ekran değişmez, v384 dinamik `==1` taraması her ad için) — Olculemedi'nin 13 kopyası v323 `teknik`/`neden` çivisinin de tek hedefi olur. Ek: TSK-114'ün çağrı-yeri çivisi pano geneline (566/566 ölçüldü, sınıf-A ihlali 0) genişletilir — bu kalemde.
  Why: tek-kaynak yasası; TSK-099/113 emsali; implementer raporu endişe-4/5 (2026-09-03).
  Ref: .superpowers sdd kovab-b12 report.md (git-dışı) · TSK-113 · `ui/src/pano/parcalar/kapi.tsx`.
- **[TSK-122] SOUL denetimi terim-korunumu yarısı: motive eden 'çevrilen kaynak jetonu' vakası kapanmıyor** — status: DONE(2026-09-04 6e35ba1; canlıya dağıtım #14 ile) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (CANLI dağıtım #14 2026-09-04 22:08Z f8d7d6d: A1 SEMA_ALANLARI üç alan; ilk canlı denetim 2026-09-05 22:0xZ brifingi.) (HÜKÜM 2026-09-04 seçenek (a), 6e35ba1: şema {sade_ozet, uydurma, cevrilen}; `cevrilen` dolu → yeniden-üretim (uydurma yolu); bedel beyanı yalnız obs.log kwarg'ı, damgaya girmez (Yasa 6 çivisi); v385 genişletildi, mutasyon 19 öttü; bot dosyaları değişmedi. Seçenek (b) mekanik jeton koruması elendi (TAKILI/DURAN/BAYAT yanlış-pozitif). Dağıtım #14.) TSK-014 incelemesi Ö-2 (2026-09-03): `veri_terimleri` yalnız `olculemeyen` adlarıyla besleniyor (sağlıklı günde boş, @karne'de hep boş) ve denetçi şeması yalnız sade_ozet + uydurma soruyor — "0 ship Türkçeye çevrildi" vakası ne mekanik ne LLM tarafından yakalanıyor (bu turda yalnız BEYAN). İş: (a) şemaya `cevrilen` alanı + isteme SOUL'un "Terimi ÇEVİRME" şartı (kural metni yine SOUL'dan) YA DA (b) ilk istemin VERİ bloklarından türetilmiş dar jeton kümesi (büyük harfli tanımlayıcı + sayı). Bedel: (a) çağrı yok, şema büyür; (b) yanlış-pozitif riski ölçülür.
  Why: bedel yasası — TSK-014 maliyet öderken motive eden arıza sınıfını kapatmıyor; beyanla bırakıldı.
  Ref: .superpowers TSK-014 review Ö-2 (2026-09-03); ops/soul_denetimi.py; TSK-014.
- **[TSK-123] Brifing birimlerine açık `TimeoutStartSec` (oneshot; ikinci-görüş sonrası en kötü yol 4 çağrı)** — status: DONE(2026-09-04 e1beb13 A1 kuruldu) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (CANLI DOĞAL ATEŞLEME 2026-09-04 22:02:22–22:04:55Z: Result=success, 2 dk 33 s < 660 s; birim canlıda çalışır.) (HÜKÜM 2026-09-04 14:4xZ: brifing/bekci/karne 660 s = KOSUM_CAGRI_TAVANI 4 × PROFIL_TIMEOUT_S 150 + 60 s pay; skill-gorus 300 s (deterministik yol, dış çağrı yok — seçildi, beyanlı); NOUS_TIMEOUT_S 900 bu yolda kullanılmıyor; v409; A1'e elle kuruldu (F9), TimeoutStartUSec 11min/5min doğrulandı; test-ateşleme 22:00Z şef brifingi doğal tetiği — sonuç sabah/akşam okunur.) `deploy/oracle-a1/meridian-{brifing,bekci,karne}.service` `Type=oneshot`, hiçbiri `TimeoutStartSec=` beyan etmiyor (ölçüldü 2026-09-03); TSK-014 ile koşum duvar saati üst sınırı 1→4 çağrı × PROFIL_TIMEOUT_S. İş: birim başına açık tavan (ölçülen en kötü yol + pay), [1c] birim ayrıklığı kapısıyla dağıtım, kurulduğu gün elle test-ateşleme (§9).
  Why: zaman-aşımı sınıfı beyansız — teslimat düşerse sessiz (K-1'in kardeşi, inceleme Ö-5).
  Ref: TSK-014 review Ö-5; deploy/oracle-a1/meridian-brifing.service; CLAUDE.md §9.
- **[TSK-124] Hafıza "Genel bakış": kopya kartların tekilleştirilmesi + takımyıldızı düğüm stili + ad** — status: DONE(2026-09-03 görsel tur onayı 12:40Z) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (status notu 2026-09-03 12:28Z: CANLIDA 0bda163/dağıtım #7; operatör görsel turu bekler → 108…112 + 124 DONE) (status notu 2026-09-03 ~11:30Z: SEVK, tek opus ajan.) Operatör görsel turu (TSK-108…112 DONE kapısı) üç kopya buldu: takımyıldızı kartı (Bellekler'de de var), son belgeler (Belgeler görünümü), bilgi sayfaları (Bilgi Tabanı); düğümler mor tek renk ve büyük (orijinal CP: küçük, türe göre renkli); "Ana Sayfa" adı uygulama ana sayfasını andırıyor. İş: görünüm kimliği sabit, görünen ad "Genel bakış"; kopya kartlar → tek satır özet + bağlantı (içerik tekilleştirme, veri kaynağı ölçülerek); `takimyildizi.tsx` düğüm stili referanstan ölçülür (`DUGUM_STILI`, rol bantları dışı renkler); v388 çivileri. DONE damgası (108…112) bu dilimin görsel turundan sonra.
  Why: operatör 2026-09-03 ~11:15Z (görsel tur): "duplike, mor noktalar büyük, Ana Sayfa mantıksız"; hafıza kaydı konsolide-icerik-tekillestirme.
  Ref: .superpowers/sdd/2026-09-03-tsk124/brief.md; docs/superpowers/plans/2026-09-02-hafiza-cpui-birebir.md; ui/src/pano/yuzeyler/hafiza/AnaSayfa.tsx.
- **[TSK-125] Hindsight zihin modeli / bilgi sayfası üretimi: bankada 0 — üretici var mı, tetik ne** — status: DONE(2026-09-05 beyanla kapatıldı: üretici yok — model/sayfa yalnız kullanıcı tanımıyla doğar; pilot → [TSK-142] operatörde) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-05 02:4xZ, keşif A1: Hindsight konsolidasyonu zihin modeli ÜRETMEZ, yalnız TANIMLI modelleri tazeler (consolidator: refresh_after_consolidation / refresh_cron); tanımlı model 0 → 0 sayfa BEKLENEN, arıza değil. 2026-09-03 '404' ölçümü yol hatasıydı: gerçek yollar /knowledge-base/{tree,pages,…} ve /mental-models/{id}/{refresh,history} 200 (tree roots []). Konsolidasyon çalışıyor: 71 op tamam, 1026 olgu bekliyor, 24 sa'de 15×429, bir op 1564 s '[STUCK?]' (kota beklemesi mi takılma mı — ölçülmedi). hindsight-api docker DEĞİL systemd+venv (docker yalnız CP 9999). .env'de mental/consolidation anahtarı yok (varsayılanlar). Panodaki 'Sayfa oluştur' bayrak değil sabit devre-dışı Faz2Dugme. Kodsuz pilot (1 model, delta, gece cron, 7 gün kota sayımı) kart ister → [TSK-142] operatör kararı.) A1 ölçümü 2026-09-03 ~11:25Z: `mental-models` ucu total 0; `pages`/`knowledge` uçları bu API sürümünde 404. Yazan yok: ingest yalnız bellek (retain) yazar; panodaki 'Klasör/Sayfa oluştur' Faz-2 (kapalı). İş: Hindsight konsolidasyonunun zihin modeli üretip üretmediğini, tetik/ayarını (env anahtarları, CP'deki karşılığı) ölç; üretiyorsa boş-saat tetiğine bağla (TSK-115 penceresi), üretmiyorsa Faz-2 sayfa oluşturmayı KOVA B'ye al ya da kalemi kapat (beyanla).
  Why: operatör görsel turu 2026-09-03: "neden hiç bilgi sayfası yok" — cevap 'yazan yok' ölçüldü, üretici sorusu açık.
  Ref: TSK-124; TSK-115; deploy/hindsight/env.iskelet; meridian/api.py hafıza vekili.
- **[TSK-126] Skill görüş TERFİSİ tasarım belgesi: görüş gerçek kararı nasıl etkiler (EDG-019 koşum #1 sonrası)** — status: QUEUED · born: 2026-09-03 · owner: rol1 · size: M · trigger: —
  What: EDG-2026-019 resmî koşum #1 (2026-09-03) iki terfi adayı verdi (exhaustion-hammer aday-siralayici IC +0,169 CI[+0,038;+0,299]; vcp-screener cikis katkı +0,144 CI[+0,104;+0,183]) ve bir emeklilik işareti (exhaustion-hammer cikis −0,428; 1/3 pencere). "Terfi" bugün yalnız LİSTE (skill_gorus terfi_adaylari), eylem yok. İş: H1 tasarım belgesi — görüşün aday sıralamasına/çıkış kararına nasıl gireceği (ağırlık mı, veto mu, gölge kol mu), motor-içi bayrak yasağı, gölge denemesi + yeni kart şartı, ikinci pencere ölçümüyle bağ (kill#3 3 pencere); kod YOK, önce belge ve onay (uyuyan-yol dersi: önden bağlı arkadan bağsız yüzey inşa edilmez).
  Why: operatör 2026-09-03 14:18Z: "tasarım kalemi aç".
  Ref: research/cards/EDG-2026-019-skill-gorus-defteri.yaml hukum_2026_09_03; research/olcumler/edg019_skill_gorus_etki/sonuc_2026-09-03.json; TSK-073.
- **[TSK-127] RUNBOOK'taki 64 çürük satır çapasının kaynağı günlük: MERIDIAN_ENGINEERING_LOG.md 'KALICI RİSKLER/DERSLER' excerpt'i** — status: DONE(2026-09-04 1ffc521 dağıtım #11) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-04 gece: günlük DOKUNULMADI; üretici `_capa_notrle` excerpt'teki satır çapalarını nötrler (tek çağrı noktası), RUNBOOK 66 → 2 ham eşleşme (kalan 2 deploy/oracle-a1/tick_watchdog.sh başlık bloğu — geçerli satırlar, codelaw çürük sayacı 0), `_DOCS_URETILMIS` BOŞ (tek dışlama sıfırlandı), v391 çivileri hükmü izler; mutasyon (nötrleme kapalı → docs dünyası öttü); v209 korpus tazelendi (Rol-1).) TSK-080 A ölçümü (2026-09-03): docs/ 2.997 çapa / 1.020 çürük — 951'i tarihli teşhis belgesi (meşru, dışlandı), 5'i yaşayan (düzeltildi), 64'ü docs/RUNBOOK.md; RUNBOOK üretilmiş, 64'ün TAMAMI (29 eşsiz metin) günlüğün ops/runbook_uret.py madde-2 excerpt'inden geliyor — kaynak depo kökünde, docs/ dışı, vaka-künyeli tarihsel kayıt. İş: excerpt'e giren günlük bölümündeki `dosya.py:NNN` çapaları sembole çevrilir (günlük kaydı tarihsel; yalnız excerpt'e giren bölüm, ölçülerek) YA DA üretici excerpt'te satır çapalarını `dosya.py::?` biçiminde nötrler (beyanla); sonra RUNBOOK yeniden üretilir, codelaw docs dünyasından RUNBOOK dışlaması KALKAR (tek istisna sıfırlanır).
  Why: TSK-080 sonrası docs/ sıfır-tolerans yasasının tek dışlanan üretilmiş dosyası RUNBOOK; kaynağı düzeltilmeden dışlama kalıcı körlük.
  Ref: .superpowers TSK-080 report A tablosu; ops/runbook_uret.py ONAYLI KAYNAK SÖZLEŞMESİ madde-2; meridian/codelaw.py `_DOCS_URETILMIS`.
- **[TSK-128] validation_ledger.jsonl sınırsız büyüyor: LEDGER_CAP yalnız okuma penceresi, dosya kırpması yok (ret_seri ile satır ~2×)** — status: QUEUED · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (ÖLÇÜM 2026-09-04 14:5xZ A1: validation_ledger.jsonl 1,08 MB / 398 satır, son yazım 2026-08-21 (learn kapalı), ret_seri damgalı 0 satır, ort 2,7 KB/satır, günde 1–5 satır iken → yıllık ~1–2 MB; ACİLİYET DÜŞÜK, kırpma tasarımı learn açılınca. Asıl büyüyenler başka defterler: events.jsonl 26,5 MB, intraday_decisions.jsonl 19 MB → [TSK-137].) TSK-077 keşfi (2026-09-03): `store.append_jsonl` kırpma/compact yapmıyor, `validation.LEDGER_CAP=200` yalnız `ledger()`/`pbo_cscv`/analytics okuma limitidir; damga (`ret_seri`, ~70–110 float/satır) satırı ~2× büyütür. İş: ölçüm (bugünkü dosya boyutu/satır sayısı A1'de), kırpma tasarımı (son N satır + arşiv dosyası; retro-damga yasağıyla uyumlu; PBO/DSR pencereleri etkilenmez), çivi. Learn kapalıyken yazım yok — aciliyet düşük.
  Why: bedel yasası — TSK-077 bedeli beyan edildi, sınırı yok; sınırsız defter disk/okuma riski.
  Ref: .superpowers TSK-077 kesif §2–3; meridian/validation.py LEDGER_CAP; meridian/store.py append_jsonl.
- **[TSK-129] Yorum/docstring sembol çapaları: 102 çürük (71 dosya) → 0, sonra üçüncü besleme ok'a bağlanır** — status: DONE(2026-09-04 11aa356 dağıtım #10) · born: 2026-09-03 · owner: rol1 · size: M · trigger: —
  What: (HÜKÜM 2026-09-04 gece: 102 çürük / 71 dosya → 0 (48 gerçek sembol, 27 JSON-alan düzyazı, 20 yerel/URL/illüstratif, 7 dizge; 5 mezar taşı; bir gerçek düzeltme shadow_variants.in_blackout → earnings.py::in_blackout); AŞAMA-2 canlı: report()["ok"] yorum_sembol_curume'ye bağlı, körlük 500/1.500; TSK-119'un 37 çapası artık korunuyor (mutasyon öttü); 28 motor dosyası AST birebir; suite #13; inceleme KABUL — yapısal borç → [TSK-135].) (TSK-119 girdisi 2026-09-03 gece: 37 yeni `dosya.py::sembol` çapası tests/ yorum metninde — v373 yalnız DECLARED_SINKS + ui/src okur, üçüncü besleme gözlemsel; uydurma sembol mutasyonu ötmedi. Aşama-2 ok'a bağlanana kadar bu çapalar korumasız.) TSK-120 üçüncü beslemesi (18:17Z) meridian/**+tests/** yorum+docstring metninde 102 çürük `mod.sembol` çapası ölçtü (heuristik: 11 dizge-sözleşmesi — `shadow_model.terfi` gibi sieve aşama dizgeleri backtick'li çapa biçiminde; 23 JSON-alan/attribute sahte-pozitifi — `broker.equity`, `alpaca.httpx`; 68 olası gerçek — `loop._arm_yama`, `reflect._ship`, `watchdog.alarm_gunluk`). İş: (1) `report()["yorum_sembol_capalari"]["curuyen"]` listesini dosya×sınıf tablosuna dök; (2) gerçek çürükler `dosya.py::sembol`e (def/class ölçülerek; v373 sıfır tolerans), dizge sözleşmeleri düzyazıya, sahte-pozitifler metin düzeltmesiyle çapa biçiminden çıkar (dışlama listesi YOK); (3) canlı taban 0 → aşama-2: alan `ok`a bağlanır (sıfır tolerans, v373 deseni) + körlük alarmı. Dilimlere bölünebilir (tests/ ayrı, meridian/ ayrı). TSK-119 (satır çapaları) ile aynı dosyalara dokunabilir — sıra: 119 sonra 129 ya da tek ajan birlikte (Rol-1 karar).
  Why: TSK-030 'çürüme SESLİ olsun' — üçüncü besleme gözlemselken körlük sürüyor; 102 çürük bugünkü sessiz stok.
  Ref: .superpowers TSK-120 report §4; meridian/codelaw.py `_yorum_sembol_capalari`; TSK-119; TSK-120.
- **[TSK-130] LLM ücretsiz kota muhasebesi: ingest067 · Hindsight konsolidasyon · brifing denetçisi/hermes aynı openrouter gün kotasını paylaşıyor — tüketim ölçülmüyor, tavanlar POST sayıyor** — status: DROPPED(2026-09-04 operatör: 'ingest bitince rahatlayacak, burası böyle kalsın') · born: 2026-09-03 · owner: rol1 · size: S-M · trigger: —
  What: (OPERATÖR 2026-09-04 13:0xZ: kota muhasebesi AÇILMAZ — ingest kalan 61 belgeyi bitirince baskı kalkar; ingest r2 A1 transient timer 2026-09-04 22:30Z (brifing 22:00Z SONRASI, tavan 300) kuruldu; TSK-014 yeniden ölçümü 22:00Z brifinginde.) 2026-09-03 akşam ölçümü: 429 'free-models-per-day-high-balance' 01–20Z: 0, 21Z: 2.064, 22Z: 1.032 (scope retain_extract_facts 1.108 = ingest çıkarımı, consolidation 1.424); 22:04Z şef denetçisi bu yüzden `llm_dustu`. ingest067'nin `--cagri-tavani` POST sayar, Hindsight'ın belge başına yaptığı LLM çağrısını (chunk × çıkarım + konsolidasyon partisi) SAYMAZ. İş: (1) günlük kota tüketimini kaynağa göre ölç (Hindsight journal scope sayımı + hermes agent_calls) ve panoya/brifinge tek sayı; (2) ingest'e Hindsight-çağrı bütçesi (belge başına ölçülmüş katsayı × tavan) ve saat penceresi (brifinglerden SONRA, 22:30Z–06:00Z); (3) Hindsight konsolidasyon retry fırtınası (3/3 × 4 deneme, 2.5k satır/sa) için geri-çekilme ya da model ayrımı — operatör kararı (ücretli model / ayrı anahtar). Hafıza: `llm-cagri-kotasi` (1000/gün, bağlayıcı kısıt operatör dikkati).
  Why: bir ölçüm koşumu (ingest) operatörün dikkat hattını (brifing denetçisi) sessizce kördü; kota tüketicisi belli değilken TSK-014 canlı doğrulaması yapılamaz.
  Ref: TSK-115 hükmü; TSK-014 status notu 22:20Z; A1 journal 2026-09-03 21–22Z; .superpowers palet ledger "SABAH NOTU 2".
- **[TSK-131] EDG-066 tick geri dolumu disk projeksiyonu: kalan ~1.500 gün × ~95 MiB ≈ 140 G, boş 105 G — 2021 ortasında dolar** — status: GATED(/opt/veri kullanımı ≥ 120 G — operatör 2026-09-04: 'kendimize koyduğumuz 120G dolarsa ele alırız, geri dolum devam etsin') · born: 2026-09-03 · owner: rol1 · size: S · trigger: A1 /opt/veri kullanımı ≥ 120 G (df -h /opt/veri; 2026-09-04: 38 G)
  What: (OPERATÖR 2026-09-04 13:0xZ: geri dolum DEVAM, müdahale eşiği /opt/veri ≥ 120 G (bugün 38 G / 147 G); eşiğe gelince bu kalem açılır. İzleme: bekçi/watchdog disk eşiği ayrı küçük iş — ölçülmedi.) OPERATÖR KARARI: disk büyüt / 2020–21 ertele / eski yıl boyutunu ölçüp projeksiyonu düzelt. 2026-09-03 22:00Z ölçümü (A1 `meridian-geridolum`): 2 Eylül 12:16Z'den beri 98 gün (2026-04-02 → 2025-11-10), ~69 gün/gün, arşiv 2026-09-01 → 2025-11-10 bitişik (~205 gün) + 2020-09-15 pilot; /opt/veri 35 G / 147 G; parquet günlük ort. 41–53 MiB × 2 (kotasyon+işlem). 1 EOFError (kesik indirme; 2026-04-23 sınıfı, TSK-107) süreç durmadan. İş: karar + gerekiyorsa `kapsam`/pencere kısıtı ya da disk genişletme; eski yılların (2020–2022) gün boyutunu ilk 5 günden ölçüp projeksiyonu düzelt.
  Why: geri dolum kendi haline bırakılırsa diski doldurur; dolu disk canlı motorun `state/` yazımını da düşürür (aynı makine, ayrı bölüm — /opt/veri ayrı disk sdb, ana bölüm etkilenmez: RİSK yalnız arşiv).
  Ref: hafıza `edg066-tick-geri-dolumu`; EDG-2026-066 kartı; deploy/oracle-a1/geridolum.py.
- **[TSK-132] Palet turu artıkları: takımyıldızı `JETONLAR` adları (turuncu=lime, mor=fuchsia) hue ile uyumsuz · `--huni-1/2/3` rol jetonu okuyucusuz (pano seri-6/8/9 okur) · eski sayfalar (index/runbook/landing.html) elle-kopya palet blokları tokens.json'dan türemiyor** — status: QUEUED · born: 2026-09-04 · owner: rol1 · size: S-M · trigger: —
  What: (DİLİM-1 DONE 2026-09-04 bab158f: takımyıldızı JETONLAR rol adları (görünüm aynı, v388 rol adlarıyla), huni jetonu okuyucusu beyanı (app.js segRenk — okuyucusuz DEĞİL; kod yok), yön utility köprüsü (26 bracket → utility, v406). KALAN dilim-2: eski sayfalar (index/landing/runbook/workflow.html) elle-kopya palet blokları — keşif: üretici kısmi-blok üretimi emsalsiz; en ucuz yol `<link jetonlar.css>` + `/jetonlar.css` route + `--cikti` ikinci hedef; bugün sıfır ayrışma (v208 üçünü index.html'e, v153 index'i tokens.json'a bağlıyor) → düşük öncelik.) (dal-sonu inceleme 2026-09-04: + (4) `--color-yon-arti`/`--color-yon-eksi` `@theme inline` köprüsü YOK — 9 dosyada 26 kullanım `text-[var(--yon-arti)]` bracket gramerinde, anlam jetonları ise utility gramerinde (iki gramer); köprü + bracket→utility dönüşümü bu kalemin parçası.) TSK-117 G7 incelemesinin devri. (1) `takimyildizi.tsx` JETONLAR anahtarları renk adı taşıyor ama A′ rampasıyla anlamı kaydı (turuncu→seri-7 lime, mor→seri-8 fuchsia): ya ada göre değil ROLE göre adlandır (`bag-entity`, `bag-causal`) ya da gerçek hue adına çevir; çağıranlar grep'le. (2) `huni-1/2/3` tokens.json'da seri-6/8/9 kopyası, pano OKUMUYOR (kanban/Huni.tsx `--color-seri-*` okur, şerhli) — ya sil (v208/v197 etkisini ölç) ya Huni.tsx okusun. (3) `meridian/web/{index,runbook,landing}.html` kendi `--huni-*`/rol hex bloklarını taşıyor (#2563eb/#7c3aed/#16a34a, eski palet) — tokens.json'dan üretilmiyor; üretici (jeton_css_uret) bu sayfalar için de blok üretsin ya da sayfalar jetonlar.css'i yüklesin; ölçüm önce: kaç kopya, kaç değer ayrışmış.
  Why: tek-kaynak yasası (kopya sessizce ayrışır — bu gece huni-2/3 tokens.json'da "lime/fuchsia" derken ekran "fuchsia/pink" idi, incelemeci yakaladı); Yasa 6 (okuyucusuz jeton).
  Ref: .superpowers/sdd/2026-09-03-palet-turu-plan task-7-report.md (§Düzeltme turu 1) + G7 inceleme; TSK-117; docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md §6.
- **[TSK-133] Rol jetonları renk körlüğünde ışıklılıkla ayrışmıyor: 12 kontrastın 9'u ön-kayıtlı 1,4 eşiğinin altında (min 1,01) — ışıklılık düzeltmesi görsel karar** — status: DONE(2026-09-04 17b723b preset; görsel onay operatörde) · born: 2026-09-04 · owner: rol1 · size: S-M · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: Meridian Palet preset GÖRSEL ONAY alındı.) (HÜKÜM 2026-09-04: yalnız Meridian Palet preset'inde sev-1/2/3, yon-arti/eksi ışıklılığı — HSL hue ±3° kısıtıyla (r1: ilk tur sev-3'ü 10–12° kaydırmıştı, incelemeci yakaladı), 12/12 kontrast ≥1,4 (min 1,4046); v400 xfail kalktı + preset hue bant/sapma çivisi; gerçek mutasyon koşuldu; varsayılan tema birebir. Ekranda: başarı yeşili daha açık (#3bc774/#5ae593), gece kritik daha koyu (#c84d4f). Operatör preset'i seçip görsel onay verir; dağıtım #13.) (OPERATÖR 2026-09-04 13:0xZ: PRESET'TE DÜZELT — yalnız 'Meridian Palet' preset'inin altı çekirdek jetonunun ışıklılığı (hue sabit, G2 emsali) deutan/protan ≥1,4 kontrast verecek biçimde; varsayılan temaya dokunulmaz; sonra ekran görüntüsüyle onay; v400 xfail kalkar.) OPERATÖR KARARI: sev-1/sev-2/sev-3 ve yon-arti/yon-eksi çiftlerinin gündüz+gece ışıklılığı (hue sabit, G2 emsali) deuteranopi/protanopi simülasyonunda ≥1,4 kontrast verecek biçimde ayrılsın mı (altı çekirdek jetonun ekrandaki hâli değişir; ekran görüntüsü karşılaştırmalı) — ya da eşik yeni kart/spec revizyonuyla gevşetilsin (eşik sonradan değişmez kuralı: bu yol yeni ön-kayıt ister). Ölçüm tablosu spec §6'da; çivi `tests/test_renk_korlugu_v400.py` xfail(strict=True) — jetonlar düzelince kırmızıya döner, xfail kalkar.
  Why: S4 kararı (2026-09-03) ölçümü bu tura koydu; ölçüm kırmızı çıktı, düzeltme görünür tasarım değişikliği — operatör görmeden uygulanmaz.
  Ref: docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md §6 (S4 tablosu); .superpowers palet ledger task-8-report.md; TSK-117.
- **[TSK-134] `ui/src/jetonlar.css` genel-amaçlı adları (`--card`, `--card-2`, `--accent`, `--accent-2`, `--accent-tint`, `--bg`, `--tx*`, `--line*`) pano shadcn temasıyla AYNI adı tanımlıyor — cascade'de shadcn kazanıyor, çakışma belgesiz** — status: DONE(2026-09-04 fa29e6d suite #19; canlıya dağıtım #14 ile) · born: 2026-09-04 · owner: rol1 · size: S · trigger: —
  What: (CANLI dağıtım #14 2026-09-04 22:08Z f8d7d6d: bundle Csnm_HYs, medya seçicisi `:root:not([data-theme])` canlı css'te.) (HÜKÜM 2026-09-04 fa29e6d: medya bloğu `:root:not([data-theme])` — OS tercihi yalnız damgasız köke; v412 seçici-anlam yardımcısı + `.dark` import sırası testi, mutasyon 2 öttü, seri 170; jetonlar.css tek satır; bundle Csnm_HYs/ZBbyIQ5P; stub OS-koyu+gece --card oklch(20.5%) ✓ (tema.css kazandı), gündüz oklch(100%), damgasız #262626 (tasarım gereği). --card/--accent düşürme (kapsam alanı) GEREKMEDİ — çakışma cascade'de çözüldü; v407 beyanı aynen. Suite #19 10361/0.) (KÖK NEDEN 2026-09-04 21:0xZ: gece + OS-koyu'da `--card` #262626'nın kaynağı `.dark` bloğu DEĞİL, jetonlar.css OS-medya bloğu — seçici `:root:not([data-theme='light']):not([data-theme='gunduz'])` (0,3,0) pano `data-theme=gece` kökünde uygulanıp tema.css `.dark` (0,1,0) bloğunu eziyor; v412 yalnız gunduz'u dışlamıştı. HÜKÜM: medya bloğu `:root:not([data-theme])` — OS tercihi yalnız DAMGASIZ köke; damgalı kök temayı kendi yönetir. Brief .superpowers/sdd/2026-09-04-tsk134; sevk TSK-122 sonrası; dağıtım #14.) (EK ÖLÇÜM 2026-09-04 18:0xZ, stub OS-koyu: (1) v412 vakası — jetonlar.css medya gece bloğu `:root:not([data-theme='light'])` pano gündüzünü (data-theme=gunduz) EZİYORDU → üretici seçiciye `:not([data-theme='gunduz'])`, commit cea354d; (2) GECE modunda `--card` = #262626 (jetonlar `.dark` bloğu) — shadcn'in oklch(20,5%) değeri DEĞİL: 'tema.css kazanır' hükmü yalnız gündüz `:root` için doğru, `.dark`ta jetonlar kazanıyor (katman/sıra); görsel fark küçük (kart bir ton açık) ama çakışma gerçek → DÜŞÜRME (kapsam alanı: --card/--accent pano çıktısından çıkar) artık gerekçeli, QUEUED yeniden açıldı.) (HÜKÜM 2026-09-04: ölçüm — gerçek çakışma 8 değil 2 (--card, --accent); tema.css kazanır, pano bracket'le okumuyor; üretici BASLIK beyanı + v407 (kesişim == beyanlı küme, import sırası, bracket okuma yok). Düşürme (kapsam alanı) AÇILMADI — gerek görülmedi; yeni çakışma doğarsa v407 öter.) TSK-117 G1 `@import "./jetonlar.css"` ile jetonlar.css pano cascade'ine girdi; `:root`/`.dark` içinde tema.css'in shadcn bloğuyla aynı adlar (gece `--card` shadcn #171717 vs jetonlar #262626). Bugün görsel fark yok (tema.css bloğu importtan sonra, kazanıyor) ama iki çelişen tanım sessiz duruyor: import sırası değişirse ya da biri `var(--card)` bracket'iyle doğrudan okursa kırılır. İş: ölçüm (çakışan ad listesi + hangi değerler ayrışık), sonra ya jetonlar.css'ten pano tarafında ölü olan genel adları üreticiyle DÜŞÜR (tokens.json'da `tema: eski-sayfa` etiketi gibi bir kapsam alanı) ya da dosya başına beyan + v208 ailesine "çakışan ad yok" çivisi.
  Why: tek-kaynak yasası — aynı adın iki tanımı sessizce ayrışır; bu turda kimse fark etmedi, dal-sonu inceleme yakaladı.
  Ref: .superpowers/sdd/2026-09-03-palet-turu-plan dal-sonu inceleme (ÖNEMLİ #1); ui/src/tema.css; ops/jeton_css_uret.py; TSK-117; TSK-132.
- **[TSK-135] `codelaw._yorum_sembol_capalari` metin kökleri `report()`'tan parametrize edilmiyor — sentetik kökle çağıran testler üçüncü beslemede gerçek ağacı tarar** — status: DONE(2026-09-04 1ffc521 dağıtım #11) · born: 2026-09-04 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-04 gece: report() metin köklerini root'tan türetiyor (gerçek kök birebir; sentetik kök kendi ağacı), v373 yalıtımı kalktı, v402 +4 çivi, v314 dokunulmadı; bedel değişmedi (sıcak ~1,78 s); mutasyon öttü.) `report(root=tmp, tsx_kok=tmp)` çağrıları py_kokler'i sentetik alır ama `_yorum_sembol_capalari(metin_kokler=("meridian","tests"))` sabit → metin GERÇEK ağaçtan, sembol çözümü SENTETİK: v373 `test_CURUME_report_OKUNU_DUSURUR` bu yüzden monkeypatch ile yalıtıldı (TSK-129), v314 `test_TSX_NUKSU_report_OKUNU_DUSURUR` yalıtılmadan aynı tuzakta (bugün zararsız: `sentetik_hedef.py` adı gerçek yorumlarda `::` biçiminde geçmiyor). İş: `metin_kokler`i `report()`'tan geçir (root türevi), v314 yalıtımını kaldır, `_yorum_sembol_capalari` docstring'ine bedel (sıcak 1.790 ms, TSK-129 ölçümü) işlensin; çivi: sentetik kökte report() gerçek ağacı TARAMAZ (sentetik kökte 0 çapa).
  Why: kardeş beslemeler (tsx/docs/text/sembol) "sentetik kökle çağıran test kendi ağacını ölçer" disiplinine uyar, yalnız bu besleme kırıyor — gelecekte sessiz yanlış kırmızı/yeşil.
  Ref: TSK-129 inceleme (ÖNEMLİ); meridian/codelaw.py `_yorum_sembol_capalari`, `report`; tests/test_capa_uyusmasi_v373.py; tests/test_codelaw_tsx_capa_v314.py.
- **[TSK-136] Palet turu varsayılan DEĞİL, tema: varsayılan tema orijinal (kopyalanan UI) renklerine döndü, rezerve-bant paleti "Meridian Palet" preset'i (5. seçenek)** — status: DONE(2026-09-04 0c3f873 dağıtım #12) · born: 2026-09-04 · owner: rol1 · size: M · trigger: —
  What: Operatör kararı 10:10Z ("UI'da 4 renk seçeneği zaten var; ana renkleri geri al, bu yaptığını tema olarak yap; huni vs. değiştirdiğin kalemleri de bu temaya eski haliyle taşı"). Uygulama: tokens.json/tema.css/eş-kayıt HTML'ler 4bfa113 değerlerine (seri 6–10 blue/orange/violet/cyan/pink, huni, gece yön-eksi #f98080); anlam jetonlarının varsayılanı TSK-117 öncesi literal Tailwind hue'ları (amber-600/400 vb., ölçülerek); `ui/src/styles/presets/meridian-palet.css` (anlam → sev alias, seri A′, gece yön-eksi 17°, huni → seri) + `THEME_PRESET_OPTIONS`; tsx göçü kaldı; SeansTakvimi → basari; v395/v396/v399/v400 preset'i okur, v153 dar istisna (-h/-t iki temada aynı); spec §7 S6.
  Why: tema mekanizması varken renk kararının varsayılanı değiştirmesi operatör onayı olmadan görünümü değiştirdi (gece dağıtım #9); geri dönüş + tercih.
  Ref: .superpowers/sdd/2026-09-04-tsk136 (brief, inceleme); TSK-117; docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md §7 S6.
- **[TSK-137] Append-only state defterlerinin rotasyonu: events.jsonl 26,5 MB · intraday_decisions.jsonl 19 MB (A1, 2026-09-04) — store.append_jsonl kırpmıyor, okuyucular tam dosyayı ayrıştırıyor** — status: QUEUED · born: 2026-09-04 · owner: rol1 · size: M · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: (1) TEK KALEM — TSK-020 UYGULA-2 adım-3 (parquet arşivi + birleşik okuma) TSK-137 adım-2'ye devredildi; (2) `limit=None` okuyucular (bütünlük/öz-inceleme) BİRLEŞİK GÖRÜNÜME (DuckDB cari + arşiv) taşınır — tam tarih korunur; (3) intraday_decisions.jsonl için ÖNCE hacim/gün + okuyucu envanteri ölçümü (belgeye eklenir), sonra aynı kalemde karar. Adım-2 sevke hazır (Rol-1 brief).) (ADIM-1 DONE 2026-09-04 9c71bea, CANLI dağıtım #13 20:03Z — A1 /api/alerts 90 ms → 1,8 ms önbellekli: `store._read_jsonl_kuyruk` — `limit` verilince SONDAN büyüyen blok (taban 256 KB, ×4, ilk yoklamadan ort. satır tahmini; blok dosyanın yarısını aşarsa tam okuma; None → eski yol, sonuç hiçbir koşulda sapmaz — v410 37 test, rastgele sentetik eşitlik, yarım-satır mutasyon); inceleme R1: negatif limit kuyruk yoluna giriyordu → `limit > 0` + savunma + 700 KB testi; `/api/alerts` events.jsonl mtime + 10 sn TTL önbelleği (`onbellekten`, AlarmGovdesi tipi). A1 ÖLÇÜMÜ: tam okuma+parse 431 ms (26,6 MB / 87.839 satır) → kuyruk 1,5 MB 24 ms; yerel 9 MB'da kazanç ms altı — bedel A1'de ölçüldü. Bozuk-satır sayacı kuyruk yolunda yalnız taranan bloğu yansıtır (beyanlı bedel). v339 karne_hesap obs-yazım beyanı taşınmayı aynı gün yakaladı (531f717). Tasarım: docs/TASARIM-DEFTER-ROTASYONU-2026-09-04.md — 4 operatör sorusu açık; KALAN 137b: rotasyon/arşiv (append_jsonl kırpma) — operatör soruları cevaplanınca.) (H0→H1 2026-09-04 15:1xZ: TASARIM BELGESİ `docs/TASARIM-DEFTER-ROTASYONU-2026-09-04.md` — okuyucu envanteri (inbox 15 sn, hayalet sayacı 30 sn önbelleksiz; diagnostics 45 sn önbellek ama cache-miss'te iki tam okuma; intraday_decisions aynı istekte iki kez), emsaller (olay_sikistir adım-2, olay_sorgu, api._son_dongu_olaydan seek-from-end), üç seçenek risk sırasıyla; ÖNERİ: adım-1 read_jsonl kuyruk okuma + alerts önbelleği (S), adım-2 kırpma = TSK-020 adım-3 (M). 4 operatör sorusu belgede.) TSK-128 ölçümünün yan bulgusu. `store.read_jsonl(limit=)` dosyanın TAMAMINI okuyup `rows[-limit:]` kırpar (TSK-074 r1 ölçtü) → her `learning_scorecard` (~30 sn) ve her obs-okuyucu 26 MB'ı yeniden ayrıştırır; obs event hacmi ~536 satır/gün (uç gün 7.256). İş (tasarım önce, H0→H1): (1) okuyucu envanteri — hangi kod events.jsonl/intraday_decisions.jsonl'ı okuyor, kaç satır geriye bakıyor (tail mi tüm dosya mı); (2) rotasyon politikası — günlük/boyut eşikli dönüş + arşiv (`state/arsiv/events-YYYY-MM.jsonl`), okuyucuların pencere sözleşmesi (son N gün) ile uyumlu; retro yazım yok; (3) `read_jsonl` kuyruk okuma (seek-from-end) ya da satır indeksi; (4) çivi: dosya boyutu eşik + okuyucu bedeli ölçümü. Yasa 6: arşiv dosyasının okuyucusu (denetim/ölçüm) beyanlı.
  Why: bedel yasası — her karne çağrısı 26 MB ayrıştırıyor ve dosya sınırsız büyüyor; TSK-074 sayacı bu yüzden 15.000 satır kuyruk sınırıyla beyanlı sınır taşıyor.
  Ref: A1 `ls -la state/` 2026-09-04; meridian/store.py read_jsonl/append_jsonl; TSK-074 r1 raporu; TSK-128.
- **[TSK-138] Brifing SOUL denetçisi alan adlarını 'uydurma' sayıyor (bekçi · stop_gap'i · iyileştirme önerisi) → 2/2 ihlal, HAM teslim** — status: QUEUED · born: 2026-09-04 · owner: rol1 · size: S · trigger: —
  What: (KOD TAMAM 2026-09-05 c23a6a7: D1 VERİ üçüncü blok, D2 süzgeç (sözlük = VERİ + Üslup; aday metin sözlüğe girmez), D3 ilk_ihlal/suzulen olaya; v385 +6 (82/82), mutasyon 2; istem +%25. Canlı: dağıtım #16 → 22:04Z brifingi; DONE damgası canlı ölçümle.) (KÖK NEDEN + HÜKÜM 2026-09-05 02:4xZ, keşif: denetçi istemi VERİ'yi hiç görmüyor — `istem()` yalnız SOUL Üslup bloğu + brifing metni; SOUL kuralı 'ya VERİDEN ya bu dosyadan' der, çıktı sözleşmesi 'kural metninde ve brifingde OLMAYAN' diye yanlış tanım taşır. Canlı: brifing_kural_denetimi olayı TÜM tarihte 3 (14 değil — o sayı beklentiydi); 6 ihlal kaydının 4 uydurması VERİ'de literal geçiyor (yanlış-pozitif), gerçek 0, denetçinin kaçırdığı 1 gerçek bozuk çekim ('kritikisi'). (2) maddesi TERS: `veri_terimleri` 'susturulamaz' listesidir (eksikse ihlal) — bot adı eklemek sef'in bekçi'yi anmadığı her brifingi mekanik ihlale çevirir; UYGULANMAZ. HÜKÜM seçenek D: denetçiye VERİ bölgeleri üçüncü çitli blok + mekanik izinli-sözlük süzgeci (VERİ/SOUL/brifing'de geçen jeton uydurma sayılmaz, `suzulen` beyanı) + ilk-tur ihlali olaya (damgaya değil). `cevrilen` canlıda henüz hiç koşmadı (22:04Z koşumu eski şema, dağıtım #14 22:08Z) — ilk ölçüm 09-05 10:07Z bekci. Brief .superpowers/sdd/2026-09-05-tsk138; dağıtım #16 20:00–22:00Z, 22:04Z brifingi canlı doğrulama.) 2026-09-04 22:04:55Z şef brifingi (ilk llm-kaynaklı denetim, TSK-014): 4 ihlalin 3'ü bot adı (`bekçi`), kaynak adı (`iyileştirme önerisi`) ve olay alanı (`stop_gap`) — hepsi meşru; `ilk satır sade tek cümle DEĞİL` gerçek olabilir. Yeniden-üretim tavanı dolunca teslim HAM'a düşüyor (sıralama katmanı devre dışı) — yanlış-pozitif operatörün gördüğü sıralamayı bozuyor. İş: (1) son 14 denetimin ihlal listesini sınıfla (gerçek/yanlış-pozitif); (2) `veri_terimleri`ne bot adları + kaynak adları + olay alan adları (kaynaktan türetilir, elle liste değil — tek-kaynak); (3) çivi: bu üç sınıf 'uydurma' sayılmaz. TSK-122 `cevrilen` alanı aynı yanlış-pozitif riskini taşır — 2026-09-05 brifinginden sonra ölç.
  Why: denetim kazancı (uydurma yakalama) ölçüldü, bedeli (HAM teslim = sıralama kaybı) ölçülmedi — bedel yasası; ilk llm denetiminde 3/4 yanlış-pozitif.
  Ref: A1 events.jsonl brifing_kural_denetimi 2026-09-04T22:04:55Z; ops/soul_denetimi.py veri_terimleri; TSK-014; TSK-122.
- **[TSK-139] Tohum sınırı (2026-07-24, damga yolu) eğri serisinde yok → panoda listelenir ama grafiğe konumlanamıyor (i None)** — status: DONE(2026-09-04 c90b630 suite #20; canlı dağıtım #15 22:36Z, i=881 → 2026-07-20 doğrulandı) · born: 2026-09-04 · owner: rol1 · size: S · trigger: —
  What: (ÖLÇÜM 2026-09-04 22:1xZ: eğri 898 nokta, 2026-07-20'den sonraki ilk nokta Ağustos (07-21…07-31 yok) — tohum işlemleri 07-21…07-24'te kapanmış, eğri 07-20'de durmuş; 'en yakın önceki nokta' = 07-20 = eski reset-işareti konumu → (a) çizgiyi eski yerine koyar, listelenen tarih 07-24 kalır, `konum_neden` yaklaşıklığı söyler. HÜKÜM (Rol-1 22:2xZ): (a) uygulanır, aynı gece — brief .superpowers/sdd/2026-09-04-tsk139.) TSK-035 dağıtım #14 sonrası canlı: `api._egri_beyani` sınırı yalnız TAM tarih eşleşmesiyle konumlandırıyor; damga yolunun tarihi eğri noktasına denk gelmeyebilir (kod şerhi bunu 'normal' ve 'yer uydurulmaz' diye beyan ediyor). Eski reset-işareti yolu (07-20) grafikte duruyordu; şimdi sınır çizgisi yok. Seçenekler: (a) en yakın ÖNCEKİ eğri noktasına konumla + `konum_neden` yaklaşıklık beyanı; (b) listeleme yeterli, grafik boş kalsın. Beyanlı yaklaşıklık uydurma değildir. Test: v264 `test_C` konum sözleşmesi güncellenir.
  Why: görünür pano kaybı (sınır çizgisi) mekanik sıra değişikliğinin yan etkisi; TSK-035 R1 hükmü 'iki yol aynı tarih' varsayımıyla verildi, canlı ayrışık çıktı (reset 07-20 ≠ damga 07-24).
  Ref: meridian/api.py _egri_beyani; meridian/ledgerstamp.py seed_boundary; TSK-035; A1 /api/performance 2026-09-04 22:09Z.
- **[TSK-140] dagit [5b] kod-tazelik değişmezi kum-havuzu sprint örneğini ihlal sayıyor — haftalık 8 saatlik antrenman dağıtımı 'yarı-etkili' bırakıyor, beyan yazılmıyor** — status: DONE(2026-09-04 c37ad06; canlı test dağıtım #15 22:43Z — sprint koşarken beyan yazıldı) · born: 2026-09-04 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-04 c37ad06: [5b] Description 'kum havuzunda' → BEKLENEN (⚠, kapı düşmez), IHLAL/exit 1 aynen; beyan JSON'una `sandbox_eski_kod: [...]`; v266 beş yuva + türetme çivisi 54/54; CANLI TEST 22:43:01Z: sprint koşarken `--uygula` TAMAM, beyan c37ad06 + sandbox_eski_kod [sprint@20260904-220829] bayt-özdeş. Rol-1 yazdı (ops betiği).) 2026-09-04 22:36Z dağıtım #15: `meridian-sprint@20260904-220829` (Cuma 22Z haftalık antrenman, ~8 s, kum havuzunda canlı defterden izole) 22:08Z'de eski kodla başlamıştı; [5b] 'süreç ≥ kaynak' değişmezi IHLAL dedi, `state/dagitim.json` f8d7d6d'de kaldı (koşan servis c90b630 — doğrulandı). Onarım reçetesi 'birimi döndür' antrenmanı öldürür (sonraki koşum 09-11); bu gece seçilen yol: sprint bitince (~06:07Z) `--uygula` tekrar. İş: [5b] kapsamı ExecStart'tan türer (elle liste yok — ilke korunur); kum-havuzu birimleri KAYNAKTAN türeyen bir işaretle ayrılsın (ör. birim dosyasında `Environment=MERIDIAN_SANDBOX=1` ya da `Description` 'kum havuzunda' dizgesi — hangisi ölçülebilirse) ve ihlal yerine `⚠ beklenen: kum-havuzu süreci başlangıç kodunu taşır (bitiş ~HH:MMZ)` beyanıyla geçsin; beyan dosyasına `sandbox_eski_kod: [birim]` alanı (Yasa 6: okuyucu — sonraki dağıtımın [5b] çıktısı + günlük). Çivi: dagit.sh'ın shell'ini test eden mevcut desen varsa ona (ölç), yoksa A1'de kuru koşum.
  Why: değişmez doğru ('active' ≠ 'yeni kod') ama kum-havuzu süreci için bedeli yanlış ölçüyor — haftalık antrenmanı öldürmek ya da beyanı 8 saat yalan bırakmak; ikisi de bedel yasasına aykırı.
  Ref: dagit.sh [5b] (2026-08-24 vakası); deploy/oracle-a1/meridian-sprint@.service; .superpowers/sdd/2026-09-04-tsk139/dagit15-uygula.log; TSK-092.
- **[TSK-141] events.jsonl'ün yeni kalabalık sınıfı: `sprint_cadence_skip` ~284/gün (%40) + `intraday_gap_detected` ~230/gün (%32) — 5 dk kadanslı 'aynı sebep' satırları** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S-M · trigger: —
  What: (KOD TAMAM 2026-09-05 36e5c87, suite #21 10373/0: okuyucu bekci_tarama gün-bazlı (mandal-gün yolu + `_gun_bazli_durus`), yazan `sprint._skip_ozetle` (sebep değişince anında, aynı sebep susar, gün dönüşünde ozet=True toplam_n); v413 5 + v239/v333/v332/v175 yeşil; bedel beyanı docstring'de. Canlı: dağıtım #16 → ertesi gün events.jsonl'de sprint_cadence_skip ≤ (sebep×2)/gün ölçümüyle DONE.) (HÜKÜM 2026-09-05 03:1xZ, keşif: `intraday_gap_detected` DOKUNULMAZ — imza-mandalı zaten var (`_state["intraday_gap_seen"]`), ardışık %0 tekrar; `sprint_cadence_skip` ardışık %98,2 aynı içerik (18 sebep; saat_dilimi_disinda %57,6) ama TEK okuyucu `ops/bekci_tarama.py` kertik/duran hükümlerini HAM tekrar kadansından türetiyor → SIRA: önce okuyucu gün-bazlı (ham/ilk/özet hepsi 'görüldü'), sonra yazan: günlük özet + değişince-yaz (`_SKIP_SON` sebep anahtarlı; session_refresh alan adları). Brief .superpowers/sdd/2026-09-05-tsk141; sevk 03:2xZ.) TSK-006 keşfi (2026-09-05, A1): session_refresh kesildikten sonra günlük ~700 olayın %70'i iki olay: sprint_cadence_skip (her döngüde, seyreltmesiz; dosyada 9.871 satır) ve intraday_gap_detected (5.648). İş: (1) ikisinin okuyucularını ölç (grep meridian/ ops/ ui/src) — kim okuyor, hangi pencereyle; (2) desen seç: hotstate_down `DOWN_REASSERT_S` throttle+sayaç mı, alarm-mandal 'bilinen-aktif → satır yok, değişince yaz' mı, session_refresh günlük-özet mi (üç emsal aynı defterde, ayrı defter yok — tek-kaynak); (3) bedel yasası: skip satırının taşıdığı bilgi (sebep, kadans) özet satırda korunur mu, hangi okuyucu ne kaybeder; (4) çivi + mutasyon. TSK-137b rotasyonuyla çakışmaz (o tarihsel kütle, bu yeni yazım).
  Why: bedel yasası — TSK-137a kuyruk okuma bedeli düşürdü ama defter günde ~700 satır büyümeye devam ediyor; iki olay 'aynı sebep' tekrarı.
  Ref: TSK-006 hükmü; meridian/api.py KayanOturumMiddleware (günlük özet emsali); meridian/watchdog.py DOWN_REASSERT_S; TSK-137.
- **[TSK-142] Hindsight zihin modeli kodsuz pilotu: 1 model (delta, gece refresh_cron, 7 gün kota sayımı) — fayda ölçülürse Faz-2 yazma yolu KOVA B'ye** — status: OPERATOR · born: 2026-09-05 · owner: operator · size: S · trigger: —
  What: TSK-125 keşfi: Hindsight'ta model/sayfa yalnız kullanıcı tanımıyla doğar; tanımlanan model `refresh_cron` ile kendi 5 dk'lık maintenance tick'inde tazelenir — Meridian tarafında kod/timer gerekmez. Pilot: A1'de bir kerelik POST /mental-models (name, source_query, mode=delta, refresh_cron ingest tavanından SONRA ör. '0 5 * * *', min_refresh_interval_seconds 82800), 7 gün llm-requests operation=refresh_mental_model sayımı + history; kart ister (§5). Ön şart: reflect tool-calling canary'sinin (2026-09-01 karar ⑤) ücretsiz nemotron'da geçtiği kaydı YOK — önce o ölçülür. Tasarım belgesi 'reflect KAPALI doğar → ayrı kart + operatör kararı, önce gölge' der.
  Why: bilgi sayfası yeteneği kullanılmadan duruyor; açmanın bedeli reflect-sınıfı LLM (paylaşımlı ücretsiz kota, TSK-130 DROPPED — muhasebe yok) — operatör kararı.
  Ref: TSK-125 hükmü; docs/TASARIM-HINDSIGHT-ENTEGRASYON-2026-08-31.md (Faz 2+/reflect); A1 hindsight-api /openapi.json (mental-models, knowledge-base yolları); TSK-115.
- **[TSK-143] DATA_QUALITY 'evren sapması: 13 sembol S&P 500'de yok' (AVB, BURL, CAG, EA, ENPH, EQR, LNG, MTCH, …) — 4 gündür 20:32Z'de tekrar eden alarm, ROADMAP'te kalemi yoktu** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: 2026-09-05 alarm triyajı (41 bekleyen ACK'lendi, operatör talimatı): DATA_QUALITY grubu ×4 (09-01…09-04, mandal 96 sa) — evren 251 sembolün 13'ü S&P 500 üye listesinde yok. İş: (1) ölç — 13 sembolün durumu (endeksten çıkış tarihi, delist mi devam mı; TSK evren-emekliliği emsali `RETIRED_SYMBOLS`), evren kaynağının (constituents CSV/FMP) bayatlığı, alarmın karşılaştırdığı S&P listesinin kaynağı/tarihi; (2) karar — evreni güncelle (yeni üyeler girer, çıkanlar emekli) ya da "evren = S&P snapshot 2026-0x" beyanıyla alarmı bilerek sustur; (3) çivi + alarm iletisi sembol listesinin tamamını taşısın (bugün 8'de kesiliyor).
  Why: alarm dört gündür ötüyor, ACK sessizleştirdi ama nedeni çözülmedi; evren sapması sinyal/ölçüm tabanını sessizce kaydırır (survivorship).
  Ref: A1 /api/alerts DATA_QUALITY 2026-09-01…04; meridian/constituents; hafıza `evren-emekliligi`; TSK-044 (evren kaynağı kararı).
- **[TSK-144] ingest067 r2 kapanış ölçümü: ilerleme defterinde yol biçimi r1/r2 arasında farklı (`ROADMAP.md%237` vs `…#1/2`) → 'kalan belge' sayısı ölçülemiyor; 19/89 dilim sağlayıcı 500'ü (gecici_hata)** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: 2026-09-05 sabah ölçümü (A1 /opt/hindsight/ingest067/ilerleme.jsonl): r2 89 dilim = 70 ok / 19 başarısız (hepsi HTTP 500 "Fact extraction failed", sınıf gecici_hata; 429 yalnız 3); manifest 214 belge ile eşleme yol kodlaması yüzünden güvenilmez (r1 `%23`, r2 `#`). İş: (1) eşlemeyi tek biçime çevirip kalan/bitmiş sayısını ölç; (2) gecici_hata dilimlerini yeniden deneyen r3 gerekli mi (retry politikası v387) — sayı + tavan; (3) ingest bitiş beyanı (TSK-115 kapanışı) bu sayıyla yazılır.
  Why: ingest'in 'bitti' hükmü ölçülemeyen kalanla verilemez (uydurma yasağı); TSK-125/060 kapanışları buna bağlı.
  Ref: /opt/hindsight/ingest067/{ilerleme.jsonl,manifest.json,log.txt}; tests/test_ingest067_retry_v387.py; TSK-115.
- **[TSK-145] Hindsight konsolidasyon kuyruğu: 1.026 bekleyen olgu, bir işlem 1.564 s '[STUCK?]', 24 saatte 15×429 — kota beklemesi mi takılma mı** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: TSK-125 keşfi (2026-09-05 02:2xZ, hindsight-api stats/journal): pending_consolidation 1026, operations {completed 71, pending 1, processing 1}, aynı 5 op 24 saatte 80–96 kez STUCK etiketi. İş: ingest r2 bittikten sonra kuyruğun boşalıp boşalmadığını ölç (pending eğrisi 3 gün), STUCK op'un yaşam döngüsü (yeniden deneme var mı), 429 payı; boşalmıyorsa konsolidasyon partisi/eşzamanlılık ayarı (env anahtarları adlarıyla) ya da model kararı (TSK-095 free router adayı).
  Why: hafıza bankası konsolide olmadan recall/bot-hafızası (TSK-060) taban kıyası yanıltır; kota paylaşımlı (TSK-130 DROPPED — muhasebe yok).
  Ref: A1 hindsight-api journal 2026-09-04/05; TSK-060; TSK-095.
- **[TSK-146] events.jsonl'de 2026-08-27 ve 28 günleri boş (08-26 → 08-29 boşluk) — süreç mi durdu, defter mi taşındı?** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: TSK-006 keşfi (2026-09-05, A1 defteri günlük sayımı) iki günlük boşluk ölçtü. İş: journal (meridian.service o günler), dagitim.json/günlük (dağıtım #x, migrasyon, .migrated dosyaları) ve yedek timer'ı ile çapraz kontrol; boşluk gerçekse (canlı iki gün sessiz mi, kayıt mı kayıp) bekçinin 'defter sessizliği' sensörü var mı ölç.
  Why: iki günlük kayıt kaybı sessizse aynı sınıf yeniden olur; parite/öz-inceleme pencereleri o günleri 'olaysız' sanır.
  Ref: TSK-006 hükmü notu; A1 journalctl 2026-08-26..29; TSK-137b.
- **[TSK-147] trades defteri tohum satırı 887 (2026-08-14) → 885 (2026-09-04 DB sayımı): iki satır nereye gitti?** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: TSK-035 D2 canlı ölçümü (A1 meridian.db `trades`: 885 replay_seed + 16 live_paper, damgasız 0) ile 2026-08-14 ledgerstamp ölçümü (887/887) arasında 2 satır fark. İş: SQLite göç kayıtları (entity_meta, .migrated dosyaları), emeklilik/yeniden-yazım olayları (ledger rewrite, `--uygula`), litestream yedeklerinden 08-14 sonrası fark; sonuç 'silindi/birleşti/yeniden sınıflandı' beyanıyla kapanır.
  Why: tohum defteri donmuş olmalı (TSK-035 geri-açılış şartı 'damgasız > 0' idi; satır KAYBI ayrı bir sınıf) — iki satırın akıbeti bilinmeden 'donmuş' beyanı eksik.
  Ref: TSK-035 hükmü; meridian/ledgerstamp.py; A1 state/trades.jsonl.migrated; litestream yedekleri.
- **[TSK-148] dagit [5] doğrulaması yalnız healthz okuyor — yetkisiz uç JSON'u 'boş' diye okundu (dağıtım #13 vakası); token'lı anahtar kontrolü eklensin** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: 2026-09-04 20:04Z: dağıtım #13 doğrulaması token'sız `/api/alerts` çağırdı, `{"detail": …}` cevabı `pending None` diye okundu ve hayalet sayacı yanlış uçta arandı (/api/diagnostics yerine /api/hermes). İş: dagit.sh [5]'e token'lı (x-meridian-token, .dash.env'den ssh içinde, değer basılmaz) iki-üç anahtar kontrolü: `/api/alerts.pending` sayı, `/api/hermes.learning` sözlük, `/api/performance.equity_curve_beyani.tohum_siniri` var; anahtar yoksa ✗. Çivi v266 ailesinde (dagit metni AST/regex).
  Why: 'healthz 200' yeni kodun doğru cevap verdiğini söylemez (aynı sınıf: [5b] 'active ≠ yeni kod'); dağıtım sonrası ilk yanlış okuma insan zamanı yedi.
  Ref: dagit.sh [5]; günlük 2026-09-04 akşam (dağıtım #13); tests/test_dagit_f9_beyan_v266.py.
- **[TSK-149] A1 `apt-daily-upgrade.timer` aktif (06:12Z) — unattended-upgrades canlı birimleri yeniden başlatabilir mi, politika ölçülmedi** — status: QUEUED · born: 2026-09-05 · owner: rol1 · size: S · trigger: —
  What: 2026-09-05 ölçümü: apt-daily 15:36Z, apt-daily-upgrade 06:12Z timer'ları aktif; Oracle unified-monitoring-agent (fluentd, ruby) de koşuyor (CPU %0, sorun değil). İş: /etc/apt/apt.conf.d/ 20auto-upgrades + 50unattended-upgrades (Automatic-Reboot? paket kapsamı), son 30 günde upgrade journal'ı (hangi paketler, python/systemd yeniden başlatma), meridian birimlerine etkisi; karar: güvenlik yamaları kalsın + reboot kapalı + bakım penceresi (pre-market) beyanı.
  Why: piyasa saatinde habersiz paket yükseltmesi canlı motoru kesebilir; bugün ölçülmemiş bir varsayım.
  Ref: A1 systemctl list-timers; deploy/oracle-a1 (bakım penceresi kuralı); TSK-064 (sistem sertleştirme).
- **[TSK-120] `meridian/api.py`de 7 çürük `modül.sembol` şerh çapası + `capa_uyusmasi`ya depo-geneli üçüncü besleme** — status: DONE(2026-09-03 a57e2c8 dağıtım #8) · born: 2026-09-03 · owner: rol1 · size: S-M · trigger: —
  What: (KOD TAMAM 18:17Z, inceleme uçuşta: `_modul_adlari` tuple-assign kusuru düzeltildi (skills.ARSIV gerçek sembolmüş), yedi çapa dönüştürüldü (api.py 0 çürük), üçüncü besleme `report()["yorum_sembol_capalari"]` GÖZLEMSEL (ok'u etkilemez) — canlı ölçüm: 568 dosya / 2.231 çapa / **102 çürük, 71 dosya** (heuristik: 11 dizge-sözleşmesi, 23 JSON-alan sahte-pozitifi, 68 olası gerçek) → aşama-2 BAĞLANMADI, devir → [TSK-129]; bedel: önbelleksiz +1.696 ms/report() → mtime-imzalı önbellekle +2,3 ms; codelaw kendi docstring örneklerini çürük saydı (yansımalı) → düzeltildi; v402 14 çivi, 180 passed.) (status notu 16:55Z: BRIEF HAZIR — keşif: yedi çapanın üçü gerçek çürük değil (`skills.ARSIV` tarayıcı kusuru: `_modul_adlari` tuple-assign hedefini atlıyor; `shadow_model.terfi` sieve aşama dizgesi; `auth.header.Authorization` düzyazı) — dönüşümler ölçülerek; üçüncü besleme `.py` yorum+docstring metni (kod dizgesi değil), önce GÖZLEMSEL, canlı taban 0 ölçülürse aynı turda ok'a bağlanır; v402. SIRA: TSK-120 ÖNCE, TSK-119 sonra (codelaw.py ortak). Sevk TSK-116 r1 (api.py) bitince.) KOVA B dilimi (2026-09-03) `capa_uyusmasi(modul_bicimi=True)` çekirdeğini kendi dosyalarıyla besleyince api.py'de tur ÖNCESİNDEN kalma 7 çürük sembol çapası ölçüldü (`shadow_model.terfi` ×2, `shadow_model.refit_and_save`, `skills.ARSIV`, `ledgers.cf_resolved`, `durum_sozlugu.satirlar`, `auth.header.Authorization`) — hiçbir kapı görmüyor. İş: (1) yedi çapayı hedef okuyarak düzelt/muafiyetle; (2) `codelaw.report()` `capa_uyusmasi` beslemesine `meridian/**` + `tests/**` yorum metinlerindeki `x.py::sembol` ve `modül.sembol` çapalarını ekle (üçüncü besleme) — doğarken çürük sembol çapası sınıfı bu dilimde DÖRT kez tekrarlandı (`skill_gorus.olc`, `notify._imza`, `watchdog._sessiz_hat`, iki uydurma `check_*` adı); v382 bölüm E yalnız dilim dosyalarını kapsıyor, depo geneli kör.
  Why: TSK-030'un amacı 'çürüme SESLİ olsun'du; sembol çapası da sessiz çürüyorsa amaç yarım. Dilim tur-2 endişe-1/3.
  Ref: TSK-030 · TSK-119 (satır çapaları kardeşi) · `meridian/codelaw.py::capa_uyusmasi` · `tests/test_kovab_dilim_v382.py` bölüm E (emsal).
- **[TSK-119] TSK-030 adım-4: `tests/` + `ops/` satır çapaları → sembol ya da beyanlı muafiyet** — status: DONE(2026-09-04 4bfa113 dağıtım #9) · born: 2026-09-03 · owner: rol1 · size: M · trigger: —
  What: (status notu 2026-09-03 gece: KOD TAMAM — worktree'de tek sonnet ajan, ÖLÇÜM 76 çapa/30 dosya (B-21'deki "59/28" eskimiş): 31 canlı şerh + 6 tarihsel → `dosya.py::sembol` (22 hedef AST ile doğrulandı), 1 mezar taşı, 4 illüstratif cümle, 34 `çapa-sentetik` (codelaw'da ikinci sabit); v401 çivisi v382'den ithal; inceleme 1 BLOKER (v206 yanlış sembol) → r1 Rol-1, 58/0; mutasyon-2 ÖTMEDİ: tests/ sembol çapaları hiçbir sıfır-tolerans çivi tarafından korunmuyor → TSK-129 kapsamı; D4 takimyildizi.tsx 3 `.tsx:NNN` çapası TSK-117 G1'e katlandı (tsx şerhi build ister). Yama ana ağaçta, suite #11 uçuşta.) (status notu 16:49Z: BRIEF HAZIR — keşif: bugün ham sayım 76/30 (59'a güvenilmez, ölçüm önce), beş sınıf (tarihsel/canlı-şerh/_satir_no ölçülmüş/sentetik fikstür/illüstratif); dönüşüm sembol ya da tarihli künye + çapa-mezar-taşı; yeni `çapa-sentetik` işareti codelaw'da; v401 tests+ops kaynak çivisi (v382 ithal); takimtyıldızı dış .tsx çapaları metne — `.tsx` hedef tarayıcı genişletmesi ayrı kalem. Sevk TSK-118 bitince (tests/ çakışması).) (ek 2026-09-03 12:28Z: `ui/src/pano/yuzeyler/hafiza/takimyildizi.tsx` içinde depoda OLMAYAN CP dosyalarına 3 dış satır çapası — constellation.tsx:372/1056, entities-view.tsx:200-219, üst yüzey 1035-1042 — aynı sınıf, hiçbir tarayıcı doğrulayamaz; kurala/sembole çevrilir.) `meridian/*.py`deki 16 satır çapası adım-3'te kapandı (KOVA B dilimi, 2026-09-03); `tests/`+`ops/`de codelaw deseniyle 63 eşleşme / 59 satır / 28 dosya kaldı (sentetik fikstürler hariç; inceleme 57 saydı — sayım yöntemi tek biçime bağlanır). `meridian/`ye satır eklemek bu çapaları sessizce kaydırıyor: aynı turda 4 örnek ölçüldü (`analytics.py:730` yorum satırına, `broker.py:136` boş satıra, `watchdog.py:3736` ve `broker.py:569` KOD satırına — son ikisi codelaw'a görünmez). İş: her çapa hedef okunarak `dosya.py::sembol`e çevrilir ya da `çapa-mezar-taşı` ile beyanlanır; v382 tarayıcısı `tests/`+`ops/`yi de kapsar. Aday ek: `capa_uyusmasi`ya üçüncü besleme (`meridian/**`+`tests/**` yorum metinlerindeki sembol çapaları) — doğarken çürük sembol çapası (`skill_gorus.olc` vakası) çivisiz kalmasın.
  Why: CLAUDE.md §2 "çapa taşıyan dosyada satır eklemek/silmek BAŞKA çapaları kırar" — kural yazılı ama sınıf kapanmadı; dilim incelemesi Ö3 + implementer endişe-2/3.
  Ref: .superpowers sdd kovab-dilim review.md (git-dışı) · TSK-030 · `meridian/codelaw.py::capa_uyusmasi`.
- **[TSK-115] Hindsight ingest067: parça küçültme + LLM yeniden-deneme ölçümü + boş-saat tetiği** — status: DONE(2026-09-03 gece koşumu ölçüldü; darboğaz kota → TSK-130) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-03 22:17Z, gece koşumu 20:20Z→22:17Z: 18 POST / 7 dilim OK / 18 başarısız deneme (hepsi Hindsight HTTP 500 ← openrouter 429 'free-models-per-day'), 146 eski-şema kayıt atlandı, dilim süreleri 62–667 s; önceki koşum 476 çağrı / 0 belge idi → dilimleme + hata sınıflaması + tavan ÇALIŞTI, darboğaz artık bizim tarafta değil, PAYLAŞILAN ÜCRETSİZ KOTA. Rol-1 koşumu 22:17Z'de DURDURDU (kota 00:00Z'de yenilenince gündüz tüketicilerini — 10:00Z bekçi, 22:00Z şef denetçisi, Hindsight konsolidasyon — aç bırakmasın). Kalan 61 belge + kota muhasebesi → [TSK-130].) (status notu 2026-09-03 12:28Z: KOD CANLIDA: ingest067.py+dilim_sup.py A1 kopyası (sha eşit), --kuru 124 dilim/146 eski kayıt atlandı, transient timer ingest067-tsk115 20:20 UTC; hüküm koşum özetinden) gece koşumu (00:10–01:53Z) 476 çağrı / 108 sağlayıcı hatası (%23) / 0 belge — ücretsiz Nvidia havuzu "temporarily overloaded"; Hindsight belgeyi tüm-ya-da-hiç işliyor (`1/1 chunks failed`), sağlayıcı hatasında 1 deneme → N çağrılık parça P≈0,8^N. İş: (a) `/opt/hindsight/ingest067/ingest067.py` parça boyutunu çağrı-başına ölçüp küçült (repo kopyası research/olcumler/edg067 altında tutulmalı — ölçülecek), (b) hindsight-api LLM retry ayarı var mı (`HINDSIGHT_API_LLM_*`) ölç, varsa yükselt, (c) yeniden tetik hafta içi boş saat penceresi (transient timer), günlük ücretsiz tavan (1000/gün) gözetilir; sonuç OK/HATA sayımıyla raporlanır.
  Why: operatör K1 2026-09-03 sabah: "parça küçült + retry, sonra boş saatte tetikle". "Hindsight ne zaman tamamlanır" cevabı bugünkü kanalla "tamamlanmaz".
  Ref: günlük 2026-09-03 gece kaydı (ingest durdurma); EDG-2026-067; B-TAVAN-502.
- **[TSK-116] Evren emekliliği: S&P 500 dışına çıkan 13 sembol RETIRED_SYMBOLS'a** — status: DONE(2026-09-03 b81b19b dağıtım #8; canlı payda 238) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (REVİZE 16:28Z, operatör: "yalnız canlıdan çıkar" — keşif: REPLAY_UNIVERSE tek liste, tam emeklilik geçmiş replay'de sağkalan yanlılığını artırırdı; A1: açık pozisyonda yok, trades'te 11'i geçmişte var. Uygulama: yeni `INDEX_EXITED` işareti + türetilmiş `LIVE_UNIVERSE` (238) canlı tüketicilere; REPLAY_UNIVERSE 251 ve RETIRED_SYMBOLS 8 DEĞİŞMEZ; payda restart sonrası; KOD TAMAM 17:34Z: commit b81b19b (3 düzeltme turu; yeniden-inceleme temiz — imzalı süreç-içi önbellek soğuk 716 ms/sıcak 0,045 ms sandbox, kurtarma dalı kırpılmış, marketstream positions∪armed; 329 passed) — push suite #10 sonrası, canlı payda restart sonrası (dağıtım #8); r1 16:45Z: implementer açık kalem buldu — Finviz süzgeci pratikte no-op, `dataset.load()` tabanı canlı yolda 251 kaldığı için aday taraması 13'ü hâlâ görüyordu → ruling: `load(universe=)` geriye uyumlu parametre, canlı yol LIVE_UNIVERSE ∪ açık-pozisyon ticker'ları (manage_position çıkışı yönetir), replay varsayılanı 251 birebir; ağ çağrısı tasarrufu varsayımı ölçümle yanlış çıktı (üç yüzey evren boyutundan bağımsız) — kazanç kapsam doğruluğu; sevk tek sonnet ajan 16:28Z.) `state/universe_drift.json` ölçümü (2026-09-03 gece; kaynak wikipedia, evren 251, üye 503, emekli 8): AVB, BURL, CAG, EA, ENPH, EQR, LNG, MTCH, PINS, ROKU, SNAP, SPOT, VFC endeks dışı; hiçbirinde açık pozisyon yok. İş: RETIRED_SYMBOLS listesine ekle (evren 251→238), çivi, canlıda evren sayısı doğrulanır (evren emekliliği emsali: 8 delist sembol). Yeni üyelerin evrene alınması AYRI karar.
  Why: operatör K5 2026-09-03 sabah: "13'ünü emekli et, listeye işle".
  Ref: hafıza kaydı evren-emekliligi; ledger [G18]; `meridian/universe` RETIRED_SYMBOLS.
- **[TSK-117] Palet turu: rezerve hue bantları + anlam jetonları (`--success` vb.)** — status: DONE(2026-09-05 operatör görsel onayı; kod G1–G8 a797155…109c02f + r1 0c3f873, dağıtım #9–#12) · born: 2026-09-03 · owner: rol1 · size: M · trigger: —
  What: (OPERATÖR 2026-09-04 10:10Z: 'renk seçimleri ayrı bir tema olmalıydı; ana renkleri geri al, yaptığını tema olarak yap' → [TSK-136] 0c3f873: varsayılan tema orijinal (kopyalanan UI) renklerine döndü, palet 'Meridian Palet' preset'i oldu; göç (anlam utility'leri) kaldı. Palet turunun 'DONE damgası operatörde' kalemi bu kararla kapandı: ekran görsel turu artık preset seçilince.) (status notu 2026-09-04 gece: G1–G8 TAMAM, main'de — G1 a797155 · G2 2fbcc8d · G3 c09c727 · G4 01032e8 · G5+G6 c1b0254 · G7 8ba91dc · G8 109c02f; literal Tailwind renk sınıfı 416 → 0 (v397), anlam jetonları basari/uyari/kritik/bilgi alias, seri rampası A′ bant dışı (v399), gece yön-eksi 17° (v396), renk körlüğü çivisi (v400); her görev sonnet incelemesi + Rol-1 hükmü; GÖRSEL TUR canlı panoda operatörle (stub verisiz), DONE damgası operatörde; açık: takımyıldızı JETONLAR turuncu/mor adları hue ile uyumsuz, huni jetonu okuyucusuz, eski sayfaların elle-kopya paletleri → [TSK-132].) (status notu 2026-09-03 22:20Z: SDD icra başladı — G1 köprü commit a797155 (jetonlar.css panoya bağlandı, anlam jetonları alias, .dark seçicisi, brief'in iki varsayımı ölçümle düzeltildi: sky yolu + import yolu build'i kırıyordu; v395 6 çivi) · G2 K-0 kod+r1 (gece yon-eksi 0°→17°, zemin dahil, v396 4 çivi) inceleme uçuşta; görsel tur G3'ten itibaren ekran görüntüsüyle, DONE damgaları operatörde; dağıtım #9 gece sonu.) (status notu 2026-09-03 16:43Z: **H2 UYGULAMA PLANI YAZILDI** — `docs/superpowers/plans/2026-09-03-palet-turu-plan.md`, writing-plans ile, 8 görev: G1 köprü (jetonlar.css panoya bağlı DEĞİLDİ — ölçüldü; .dark seçicisi + anlam alias'ları basari/uyari/kritik/bilgi + @theme utility) · G2 K-0 gece yön-eksi 17° · G3–G6 dört göç dilimi (uyarı 238 → başarı 135 → kritik 31 → bilgi 12; tavan çivisi monoton) · G7 K-4 seri A′ (teal/lime/fuchsia/pink/yellow) + huni seriye + DUGUM_STILI istisnası kapanır · G8 S4 renk körlüğü çivisi (Viénot simülasyonu, kontrast ≥1,4 ön-kayıt). İcra: SDD, görev başına taze ajan + inceleme + görsel tur; TSK-116/118 VE TSK-121 (komşu kopyalar — göç tek yerde, keşif 17:03Z) kapanınca başlar (UI build sırası). Yeni testler v395–v400.) (status notu 2026-09-03 sabah: H1 TASARIM BELGESİ YAZILDI — `docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md`: 9 rol hue'su + seri 6–10'un BEŞİ de rol bantlarında (seri-6=nav hex, seri-8=mod-canlı hex) + 416 literal Tailwind renk sınıfı/56 dosya + gece yön-eksi↔red çakışması (K-0); operatör 2026-09-03 ~10:45Z: S1 = A′ (seriler serbest tonlara, huni seriye bağlanır; S2 böylece kapandı) · S3 = 195° ailesi BİLGİ rolü (`--bilgi`, gezinmeden ayrı bant) · S4 = renk körlüğü ölçümü BU TURDA (tasarım belgesine simülasyon + parlaklık farkı eşiği) · S5 = literal göç DÖRT dilim, aile başına (uyarı 238 → başarı 135 → kritik 31 → bilgi 12). Tasarım belgesi bu kararlarla güncellenir, sonra H2 planı.) TSK-108 nihai düzeltmesinde "başarı" rengi yeşilden mevcut seri rampasının bir durağına (camgöbeği, `--color-seri-9`) indi ve aynı jeton takımyıldızında bir kümeyi boyuyor (bedel şerhte). İş: H1 tasarım belgesi ÖNCE — başarı/uyarı/kritik + mod + nav için rezerve hue bantları (hafıza kaydı: palet turunun ilk adımı rezerve bantlar, güvenlik kaydı), anlam jetonları açık/koyu, seri rampası yalnız veri serilerine; sonra uygulama + v286 ailesi çivileri.
  Why: operatör K7 2026-09-03 sabah: "rezerve hue bantlarıyla palet turu aç".
  Ref: nihai UI incelemesi K-5 + yeniden-inceleme Y-8 (2026-09-03); `ui/src/tema.css` (seri rampası `--seri-*`/`--color-seri-*`) + `ui/src/jetonlar.css` (rol jetonları, üretilmiş); hafıza tasarim-dili-tasima-degil-benimseme.
- **[TSK-118] ⌘K "Meridian dersleri" → dokuzuncu Hafıza nav durağı** — status: DONE(2026-09-05 operatör görsel onayı; kod ec4616d) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (KOD TAMAM 17:52Z: commit ec4616d push; DONE damgası dağıtım + görsel turdan sonra.) (status notu 16:32Z: SEVK, tek sonnet ajan — Seçenek A: `MeridianDersleri` Bilgi Tabanı'ndan görünüme TAŞINIR (çoğaltılmaz, TSK-124 dersi), `hafiza-bilgi?sekme=dersler` köprüyle `hafiza-dersler`e çözülür, palet anahtarları taşınır, PARK-1 şerhi/v378 beyanı güncellenir (palet yine görünüme iner; dersler artık görünüm), alanlar.ts 42→43 ölçülerek, v394; build EN SON.) Bilgi Tabanı sekmesi adresten (`?sekme=`) türüyor ama komut paleti maddeleri kenar çubuğu ağacından üretildiği için "lessons.md/ders/damitim" aramaları sayfalar sekmesine iniyor (PARK-1, gerekçe `komutlar.ts`te çivili). İş: Hafıza altına 9. alt başlık "Meridian dersleri" (bölüm kimliği + `alanlar.ts` sayaçları 16/42→16/43 + ilgili çiviler), palet doğrudan oraya iner; `?sekme=dersler` adresi yeni durağa çözülür (ESKI_GORUNUM_ADRESLERI deseni).
  Why: operatör K8 2026-09-03 sabah: "dokuzuncu nav durağı aç".
  Ref: final-fix-report PARK-1 (2026-09-03); `ui/src/pano/komutlar.ts`, `alanlar.ts`, `yuzeyler/hafiza/gorunumler.ts`.
- **[TSK-113] Pano `Kapi` üç-hâl kapısının yedi kopyası tek kaynağa iner** — status: DONE(2026-09-03 fb07a16 dağıtım #6) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (status notu 2026-09-03 08:57Z: B-12 dilimi tek ajana SEVK EDİLDİ — brief .superpowers sdd kovab-b12, git-dışı.) `yuzeyler/{sistem,kuyruk,kimlik,yetki}/parcalar.tsx` + `yuzeyler/{ogrenme,ajan,analiz}/ortak.tsx` aynı `Kapi<T>` bileşenini taşıyor (ölçüm 2026-09-03 gece: 7 kopya [ilk sayım 5'ti — desen `export function Kapi<` kimlik/yetki'yi kaçırdı, nihai UI incelemesi 7 saydı, `grep -rn 'function Kapi'` ile doğrulandı]; beş yüzey-altı kopyada 4 ayrı gövde [md5], ogrenme≡analiz). Hepsi `durum.veri === null` üzerinden karar veriyor; TSK-110 bayatlığı `veri.ts`te çözdüğü için kopyalar dokunulmadan düzeliyor, ama kopyalar sessizce ayrışmaya devam eder. Hedef: tek `sistem/parcalar.tsx::Kapi` + dört yüzey ondan import + v-çivisi "ikinci `Kapi` tanımı doğmadı" (hafıza yüzeyi zaten sistem kopyasını `UcKapisi` adıyla kullanıyor — emsal).
  Why: tek-kaynak yasası (§4) — TSK-099'un `apiPost` vakasıyla aynı sınıf; TSK-110 brief'i kopyalara dokunmayı bilerek yasakladı (diff okunabilirliği, tek kalem tek sınıf).
  Ref: TSK-110 · TSK-099 (emsal) · `ui/src/pano/yuzeyler/*/{parcalar,ortak}.tsx`.
- **[TSK-114] v323 `teknik` çivisi çağrı yerlerini görmüyor — `Olculemedi` kullanım-yeri kapsaması** — status: DONE(2026-09-03 fb07a16 dağıtım #6) · born: 2026-09-03 · owner: rol1 · size: S · trigger: —
  What: (status notu 2026-09-03 08:57Z: B-12 dilimi tek ajana SEVK EDİLDİ — brief .superpowers sdd kovab-b12, git-dışı.) `tests/test_*_v323.py`nin `teknik` çivisi yalnız `Olculemedi` BİLEŞENİNİ ölçüyor; bir çağrı yerinden `teknik=` düşürmek (TSK-109 mutasyon denemesi, 2026-09-03 gece) sessizce geçiyor. Çivi genişletmesi: hafıza yüzeyindeki `Olculemedi` çağrılarında `neden` zorunlu + `teknik`in beklendiği sınıf (ölçülen alan adı taşıyanlar) çağrı-yeri düzeyinde taranır; tarayıcı boşta "temiz" demez (v380 kalıbı).
  Why: mutasyon ısırmadı = çivi o dalı korumuyor; "çivi yeşili kanıt değildir" (CLAUDE.md §6). Kapsam TSK-109'un dışıydı, ajan raporu endişe-4.
  Ref: task-109-report.md §4/§7 (.superpowers sdd, git-dışı) · v323 · v380 `soy()` kalıbı.
- **[TSK-111] Hafıza sayfası Faz-2 yazma yolu — Bank Configuration düzenleme (PATCH vekili + onay adımı + denetim izi)** — status: DONE(2026-09-03 görsel tur onayı 12:40Z) · born: 2026-09-02 · owner: rol1 · size: M · trigger: —
  What: (status notu 2026-09-03 gece: DİLİM 1 CANLIDA — 11-A vekil d31d8d0 [güvenlik 9/9] + 11-B UI db6a559 [iki adımlı onay, kısmi başarı pencerede, v378], dağıtım d0c7927 22:52Z; operatör görsel turu + ilk gerçek 'yeniden dene' denemesi bekliyor; dilim 2 = bank config PATCH.) (KAPSAM GENİŞLEDİ 2026-09-02 ~20:40 UTC, operatör: Operasyonlar görünümündeki "İptal et / Yeniden dene / Kaydı sil" düğmeleri "çalışması lazım" → Faz-2'nin İLK DİLİMİ operasyon eylemleri: upstream `DELETE /operations/{id}` (cancel_operation) · `POST /operations/{id}/retry` (retry_operation) · `DELETE /operations/{id}/delete` (delete_operation) — openapi @ ebad4782 ölçüldü; vekilde üç yazma ucu + iki-adımlı onay + `obs` izi + v54/v181 mutasyon-rota çivileri; ardından bank config PATCH.) TSK-108 Faz-1 salt-okunur sözleşmesi Yapılandırma formunu devre-dışı çizer (T5, R24). Faz-2: `PATCH /api/hindsight/yapilandirma` vekili (beyaz-listeli alanlar), panoda iki adımlı onay (fark özeti → uygula), `obs` denetim izi (kim/ne/önce-sonra), v375 çivileri kırmızı-önce; ardılları: bellek düzenle/geçersiz kıl, reflect tetikleme, consolidate/recover, webhook CRUD (her biri ayrı karar).
  Why: operatör 2026-09-02 akşam görsel turu ("konfigürasyon yapacak yer bile yok") + karar 2-A: "şimdilik devre-dışı, ayrı kalem". Yazma vekili motor koduna girer (tam suite + iz çivileri), panodan yanlış ayar canlı hafızayı bozabilir — bu yüzden onay adımı ve iz şart.
  Ref: TSK-108 plan eki R24; CP `bank-config-view.tsx` (v0.9.2 = ebad4782); upstream openapi `PATCH /banks/{id}/config` şeması.
- **[TSK-109] Hafıza sayfası webhook okuması — Faz-1 vekilinde yok, sekme dürüst boş** — status: DONE(2026-09-03 görsel tur onayı 12:40Z) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: (status notu 2026-09-03 gece · canlıda: afada26 vekil `/webhooklar` + Yapılandırma webhook sekmesi [dağıtım #4 0ddd4fb]; imza sırrı vekilde süzülür [Rol-1 hükmü]; DONE koşulu: operatör görsel turu) TSK-108 Faz-1 salt-okunur kapsamı webhook listesini (CP bank-config 'webhooks') vekile almadı; Yapılandırma sekmesi "bu pano webhook'ları okumuyor" diyor (≠ "webhook yok"). Kalem: `GET` webhook listesi vekile (salt-okunur), CRUD düğmeleri Faz-2 rozetiyle kalır.
  Why: T3 incelemesi endişe-3 — okunmayan sekme UI'da dürüst ama eksik; T1 uç haritası CP api ağacının bu dalını atlamıştı.
  Ref: TSK-108 (T3 raporu §endişeler); upstream `hindsight-clients/go/api/openapi.yaml` (v0.9.2 = ebad4782) webhooks yolları.
- **[TSK-110] Pano bayat-gövde sınıfı: `sistem/parcalar.tsx::Kapi` + `veri.ts` — çekmece/kapı yeniden açılınca eski veri** — status: DONE(2026-09-03 görsel tur onayı 12:40Z) · born: 2026-09-02 · owner: rol1 · size: M · trigger: —
  What: (status notu 2026-09-03 gece · canlıda: 116f3c3 `veri.ts::useApi` yol-bağlı okuma kaydı + türetim, v381 [dağıtım #4 0ddd4fb]; 7 `Kapi` kopyası → TSK-113; DONE koşulu: operatör görsel turu) `useApi` gövdesi ebeveynde yaşadığı için alt bileşene `key` vermek bayatlığı çözmüyor (T3 incelemesi M-7, ölçüldü); gerçek çare `Kapi` + `veri.ts` seviyesinde (panonun TÜM yüzeyleri) — tek kaynaklı yeniden-çekme sözleşmesi + çivi.
  Why: hafıza sayfasında iki yerde (Belgeler/ZihinModelleri çekmeceleri) görünür; pano-geneli olduğu için TSK-108 turunda bilerek yapılmadı (>10 satır, diff okunabilirliği).
  Ref: TSK-108 T3 inceleme M-7; `ui/src/pano/sistem/parcalar.tsx`, `ui/src/pano/veri.ts`.
- **[TSK-107] Geri-dolum `indir()` indirme-sonrası boyut doğrulaması (erken kesik-dosya kırmızısı)** — status: DONE(2026-09-03 gece · pilot.py::indir indirme-sonrası boyut kıyası + KesikIndirme tek satır KIRMIZI [main'de yakalanır]; v377; canlıya kuruldu /opt/veri, koşan tur eski kodla — sonraki turda etkin) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: `pilot.py::indir` indirme BİTTİKTEN sonra `hedef.stat().st_size == beklenen_bayt` kıyası yapmıyor; kesik inen gz ancak ~8 dk'lık ayrıştırma CPU'sundan sonra gzip `EOFError`'ıyla patlıyor ve birim failed'a düşüyor. İndirme sonrası boyut kıyası + net "KIRMIZI: kesik indirme (X/Y bayt)" mesajı arızayı dakikalar erken ve doğru adla yakalar; önbellek kapısı (var-olan boyut kıyası) zaten sonraki koşumda yeniden indirtiyor — sınıf kendi kendine iyileşiyor, bu kalem yalnız teşhis süresini/adını düzeltir.
  Why: vaka 2026-09-02 07:08Z — 2026-04-23 kesik gz, EOFError, servis failed; 2026-08-05 aynı sınıftan düşüp yeniden denemede geçmişti. Triyaj hükmü: eylem-gerektirmez ama teşhis pahalı ve yanlış adlı (gzip iç hatası gibi görünüyor).
  Ref: /opt/veri/pilot.py::indir (repo kaynağı research/olcumler/edg066_tick_arsiv/pilot.py) · journal meridian-geridolum 2026-09-02 07:08Z.
- **[TSK-104] Seyrelme gözlem paketi (EXE-011 ardılı): not_armed iç kırılımı · pano kovası kararı · E2 tavan izleme** — status: GATED(EXE-011 canlı ilk hafta birikimi) · born: 2026-09-02 · owner: rol1 · size: S-M · trigger: EXE-011 canlı ilk hafta birikimi
  What: üç bağlı gözlem — (a) ayna-satırı kütlesinin neredeyse tamamı not_armed'a düşecek (tek temiz armed_not_submitted üreticisi _llm_veto_filter); EDG-042 hakemi "nerede düştü"yü sorarken not_armed'ın İÇİ (kapı hükmü dağılımı) sayılmalı — bugün red_nedeni serbest metninde, sayılmıyor (kart adayı); (b) analytics.entry_execution_summary ayna-satırlarını bilinçli SAYMAZ (payda korunumu) — panoya "seyrelme" kovası eklenip eklenmeyeceği operatör/Rol-1 kararı; (c) ENTRY_LEDGER_CAP=4000 değişmedi, E2 geriye-görüş penceresi kısalır — ilk hafta pencere_kesildi/n_defter izlenir, tavan kararı ayrı.
  Why: TSK-019 raporu endişe-2/3/4 (2026-09-02) — üçü de ölçülmüş gözlem, üçü de EXE-011'in canlı birikimini bekler. İnceleme iki gözlem ekledi (K-4/K-5): (d) payda-kıyas dedektörü — okuyucunun plan_n paydası E2-izli planlardan, gerçek payda trade_plans.jsonl'de; ayna yazımı bir seans düşerse dolum_orani YUKARI yanlı olur (EXE-006 sınıfı), kıyas dedektörü yok; (e) taşınan plan silahlı kümeden sessizce düşerse (reconcile DEAD) kalıcı izsiz kalır — kohort bir daha ona dönmez.
  Ref: task-019-report.md · task-019 inceleme K-3/K-4/K-5 · EXE-2026-011 kartı · EDG-2026-042.
- **[TSK-105] Bot profillerinin kapıya göçü: Authorization↔apikey başlık uyumsuzluğu** — status: DONE(2026-09-02 · repo 925f241+a751c07, uygulama penceresi: rotalar PUT 200 + drift boş + üç profil canlıda birebir + üç anahtar profil .env'lerinde; UÇTAN UCA KANIT: bekçi tek-atımlık koşumu kapıdan kimlikli geçti [sayaç code=502 consumer=bot_bekci ×3 — 502 upstream günlük ücretsiz-model tavanı, göç arızası DEĞİL]; köprü/kilit/motor canary'leri 200/200/401/401. Filo kotası artık botları SAYIYOR — LLM kota mekanikleşmesi tamam. Pencere vakası: serverless-pre-function config allowlist'te yoktu → PUT 400; a751c07 + v376 kıyas çivisi) · born: 2026-09-02 · owner: rol1 · size: S-M · trigger: —
  (SIRAYA GİRDİ 2026-09-02: operatör "paralelde başka task" penceresi, Rol-1 seçimi. Ölçülen mimari: hermes extra_headers env genişletmez [sır repoya giremez] → köprü KAPIDA serverless-pre-function [Bearer→apikey], botlar custom provider key_env'le; yol boyu açık: key-auth hide_credentials'sız — apikey upstream'e sızıyor olabilir, aynı değişiklikte kapanır. Tasarım/defter: .superpowers sdd tsk105 [git-dışı çalışma kaydı]. REPO YARISI İNDİ 2026-09-02: 925f241 — köprü+hide_credentials+üç profil+reçeteler, v376 30 çivi/10 mutasyon; SDD incelemesi spec 11/11, iki ölçülmüş kurtarma [zaman-aşımı evi providers.custom + anahtar evi profil-başına HERMES_HOME/.env]. KALAN: A1 uygulaması [apisix PUT + 3 anahtar + canary] operatör penceresinde — DONE o zaman.)
  What: hermes OpenRouter istemcisi `Authorization: Bearer <OPENROUTER_API_KEY>` gönderir (ölçüldü 2026-09-02: `hermes_cli/runtime_provider.py:1185` `OPENROUTER_BASE_URL` env'ini okur ama kimlik Bearer'dadır); kapının key-auth'u `apikey` başlığı bekler — botlar bugün kapıya bağlanamaz, filo kotası (limit-count/filo) onları saymaz. Çözüm adayları ölçülerek seçilir: key-auth `header: Authorization` + Bearer-öneki sorunu · proxy-rewrite ile başlık eşleme · hermes custom-provider yolu. Göç sonrası F4-B whitelist'i zaten hazır (bot_bekci/karne/sef tüketicileri).
  Why: sabah penceresi 2026-09-02 — F4-B kilidi motor-yalnız uygulandı; botlar doğrudan OpenRouter'da kaldı (kırılma yok ama kota muhasebesi kör). LLM kota memory'sinin mekanikleşmesi bu göçü bekliyor.
  Ref: deploy/apisix/routes.yaml tuketiciler bloğu · meridian/hermes.py::_nous_headers (motor emsali: apikey başlığı) · günlük gece-5.
- **[TSK-103] `full_detail_graded` span-türevi alanların dürüstleştirilmesi (span_days kararı)** — status: DONE(2026-09-03 2f204c2 dağıtım #7) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: (operatör K6 2026-09-03 sabah: `span_days` = DİLİM TAKVİMİ GEÇİRİLİR — sayılar değişir; düz kardeşle ayrışma BEYANLI + çivi; KOVA B B-14.) rejim-dilimli tam-pencere defteri bugün `span_days`/`mtm_equity` VERMEDEN hesaplanır (bilinçli — düz kardeşiyle tek yasa; bedel beyanı madde-3 backtest.py'de): span-türevi alanlar (score/sharpe/realized_30d/trades_per_year) dilim kümelenmesinden yıllıklanır, max_drawdown yaşanmamış portföy yolunundur. Karar: ya `span_days=segment takvimi` geçir (sayılar değişir — düz kardeşle ayrışma beyan ister) ya beyanla kal. Bugünkü tek tüketici yalnız avg_r+n okur, aciliyet yok.
  Why: TSK-002 incelemesi bulgu-1 (orta): kalıcı deftere "kardeş" adıyla yazılan alanın bazı alanları kıyaslanabilir değil; beyan yazıldı, kararın kendisi ruling kalemi.
  Ref: task-002 inceleme raporu 2026-09-02 · backtest.py bedel beyanı madde-3 · score.py span docstring'i.
- **[TSK-099] Pano `apiPost` iki birebir kopyası tek kaynağa iner** — status: DONE(2026-09-02 · 062e989: `ui/src/pano/gonder.ts` yazma kapısı doğdu [apiPost + GonderSonucu + detaydanMetin], üç tüketici tek kaynaktan; kimlik/gonder.ts sözleşme dokümanı + re-export; `npm run kontrol` + build + 10 pano test dosyası yeşil) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: `ui/src/pano/yuzeyler/kimlik/gonder.ts` ve `kuyruk/onayEylem.ts` aynı `apiPost`u birebir taşıyor; ortak modüle inip iki tüketici de oradan import etmeli. TSK-098 üçüncü kopyayı YAZMADI (gonder.ts'ten import etti) — borç ikiye sabitlendi, büyümedi.
  Why: tek-kaynak yasası — iki kopya sessizce ayrışır (hata gövdesi/başlık davranışı çatallanınca yüzeyler farklı davranır).
  Ref: TSK-098 raporu endişe-3, 2026-09-02.
- **[TSK-100] `BIRIM_ANAHTAR_BEYAZ` ↔ polkit kural dosyası ayrışma çivisi** — status: DONE(2026-09-02 · çivi TSK-098'le birlikte doğmuştu: 8010cd4 `tests/test_birim_anahtari_v368.py::test_polkit_kurali_BEYAZ_LISTEYLE_AYRISMAZ`; sabah penceresinin üç kural revizyonu [ad2eb73→5872d2f] çiviyi yaşattı — yalnız tam-ad `unit ==` kümesini sayar, 71 passed ×2) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: `api.py::BIRIM_ANAHTAR_BEYAZ` ile `deploy/oracle-a1/51-meridian-birim-anahtari.rules` içindeki tam-ad listesi el ile eşit tutuluyor (iki dil/iki makine — türetme kurulamaz); repo-içi çivi iki dosyayı okuyup küme eşitliğini ölçmeli, ayrışma commit anında kırmızı olmalı.
  Why: tek-kaynak yasası — kopya kaçınılmazsa türetme + ayrışma çivisi; bugünkü tek koruma ilk canlı denemedeki 502 polkit hatası (geç ve canlıda).
  Ref: 51-meridian-birim-anahtari.rules başlık beyanı · TSK-098 kapanışı 2026-09-02.
- **[TSK-101] `loop.py` broker_reconcile alarmı `mekanizma=` (Türkçe) yazıyor — tüketiciler `mechanism` bekliyor** — status: DONE(2026-09-04 bayat-kapanış: üretici yok) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-04: `grep -rn "mekanizma=" meridian/*.py` → 0 üretici (yalnız selfreview.py şerhi tarihçe olarak anıyor); imza TSK-007 dalgasında düzelmiş, kalem bayat.) MECHANISM_STALE üreticilerinden loop.py:1436 (sembol: broker_reconcile alarmı) alanı `mekanizma=` adıyla basıyor; 18 üretici içinde tek aykırı imza. Üretici alanı `mechanism`e döner (olay-defteri geçmişi için tüketici toleransı gerekmiyor — TSK-007 düşüşü mesaj-önekiyle zaten okunur kılıyor).
  Why: imza-kayması sınıfı — gerçek ad alanda duruyor ve hiç okunmuyor; TSK-007 ölçümü sırasında yakalandı.
  Ref: task-007-report.md endişe-2, 2026-09-02.
- **[TSK-102] `watchdog_incidents.gap_h` için de düşüş sırası (age_h/yas_h/behind_h eşdeğerleri)** — status: DONE(2026-09-03 v382 selfreview süre düşüşü) · born: 2026-09-02 · owner: rol1 · size: S · trigger: —
  What: (HÜKÜM 2026-09-04 ölçüm: `meridian/selfreview.py` 'MECHANISM_STALE OLAYLARINDA SÜRE DÜŞÜŞÜ (v382, 2026-09-03 — TSK-102)' — `sure_h`/`sure_kaynak` dört alanlı düşüş (gap_h/age_h/yas_h/behind_h) kurulmuş; watchdog.py behind_h alan olarak basılıyor (TSK-102 künyeli). Kalem 2026-09-03 dilimiyle kapanmış, ROADMAP'e işlenmemişti.) rapor satırındaki `gap_h` yalnız sınıf-1 (bayat-geçiş) olaylarında dolu; sınıf 3/4 olaylarının bazıları eşdeğer süre alanları taşıyor (watchdog.py:3742 `age_h`, :3484 `yas_h`, :2225 `behind_h` sınıfı) — TSK-007'nin ad-düşüşü deseniyle süre için de kurulabilir. Alan adları satır kaydığı için sembolle doğrulanmalı.
  Why: operatörün gördüğü "gecikme" sütunu çoğunlukla boş; ölçüm varken boş sütun Yasa 6'nın ters yüzü.
  Ref: task-007-report.md endişe-3, 2026-09-02.
- **[TSK-098] Pano birim-anahtarı — servisleri UI'dan istenen-duruma çekme** — status: DONE(2026-09-02 gece · POST /api/infra/birim/{ad}/istek + BirimAnahtari.tsx; v368 71 çivi, SDD incelemesi 6 bulgu→düzeltme turu→ONAY; 14 mutasyonun 13'ü ısırdı, 1'i çivi düzelttirdi; polkit kuralı 51-…rules + TSK-100 ayrışma çivisi; CANLI KURULUM+İLK DENEME SABAH — polkit yetkisi yalnız A1'de ölçülebilir, ilk hedef meridian-barsarchive) · born: 2026-09-02 · owner: rol1 · size: M · trigger: —
  What: Sistem-sağlığı birim satırına anahtar: kapat=`disable --now`, aç=`enable --now` (istenen durumun tek kaynağı systemd `is-enabled` — TSK-092 dagit türetimiyle aynı sözlük). Uç `_auth`'lu + beyaz-listeli (v1: meridian-learn, meridian-barsarchive; çekirdek `meridian` HARİÇ — pano kendi dalını kesemez, HALT ailesi var) + obs olayı; yetki sudo değil polkit/DBus (meridian-sprint@ emsali genişler). UI onay diyaloglu, sonuç sunucu geri-okumasından. Taslak brief hazır: .superpowers/sdd/2026-09-01-kapi-faz234/task-birim-anahtari-brief.md.
  Why: vaka ×2 (learn dağıtımla dirildi) + operatör isteği 2026-09-02 gecesi ("servislerin üzerine tıklayıp elle durdurabilmeliyim — her seferinde uğraşmayalım"). SÜREÇ NOTU: ilk seferinde plansız implementasyona gidildi ve operatör durdurdu — kalem sıraya buradan girer, icrası triyaj onayından sonra.
  Ref: TSK-092 (dagit istenen-durum) · 50-meridian-sprint.rules (polkit emsali) · operatör talimatı 2026-09-02.
- **[TSK-097] Çok-kullanıcı kimlik paketi (kullanıcı adı/e-posta + kayıt akışı + roller, TEK pakette)** — status: GATED(operatör çok-kullanıcıya geçme kararını verdiğinde) · born: 2026-09-02 · owner: rol1 · size: L · trigger: soldaki kapı
  What: bugünkü tek-operatör kimliği (auth.py: tek parola + oturum çerezi) çok-kullanıcıya bir bütün olarak taşınır — kullanıcı tablosu, kullanıcı adı/e-posta alanı, gerçek kayıt akışı (port edilen register v2 formu bugün bilinçli bağsız, "2. aşama" etiketli), kullanıcı-başına oturum, roller/yetkiler yüzeyleriyle bağ. Giriş formuna alan eklemek bu paketin EN KÜÇÜK parçasıdır ve paketten önce yapılmaz.
  Why: operatör sorusu 2026-09-02 gece ("kullanıcı adı da ekleyelim mi") — karar: şimdilik hayır. Bugün eklemek ya sahte alan (tek sabit ada doğrulama, güvenlik katmaz) ya erken migrasyon artığı olurdu; gerçek korumalar TLS + kapı hız sınırı + başarısız-giriş kilidi + güçlü parola. Tek-kaynak: kimlik şeması bir kez, paket içinde tasarlanır.
  Ref: operatör kararı 2026-09-02 · Giris/KapiEkrani (register v2 bağsız) · deploy/apisix routes pano-ingress yorumu (kimlik uygulamada).
- **[TSK-096] Metrik trendi ihtiyacı doğarsa hafif toplayıcı (Prometheus yaygınlaştırma DEĞİL)** — status: GATED(operatör bir soruyu "zamanla nasıl değişti" biçiminde sorduğunda ve mevcut yüzeyler cevaplayamadığında) · born: 2026-09-01 · owner: rol1 · size: M · trigger: soldaki kapı
  What: kapı rotaları dışında sisteme Prometheus YAYILMAZ (operatör sorusu 2026-09-01, cevap: hayır); trend ihtiyacı gerçekten doğarsa aday çözüm tam Prometheus+Grafana yığını değil, mevcut `/metrics` ucunu periyodik örnekleyip `state/` dışı bir zaman-serisi dosyasına yazan hafif A1-içi toplayıcı + pano grafiği.
  Why: Yasa 6 (okuyucusuz yazım) — bugün hiçbir soru trend istemiyor; A1 4-çekirdek/24GB'da ikincil yük beyanlı tavan; tasarım dili tek-pano. Kazanç ölçülmeden altyapı kurmak bedel yasasının ters yönü.
  Ref: operatör sorusu 2026-09-01 gece ("Prometheus'u bütün sistemde yaygınlaştırmamız gerekiyor mu").

- **[TSK-002] Rejim-ship satırına rejim-dilimli backtest_full** — status: DONE(2026-09-02 gece · üç yüzey: walk_forward.full_detail_graded → backtest_full@<rejim> → analytics ek-adlı 1b bacağı; v371 17 çivi + 2 hedefli mutasyon; SDD incelemesi ONAY + 6 kapanış kalemi aynı turda işlendi; span_days kararı TSK-103'e; commit gece kapanışında, push tam-suite hükmüyle) · born: 2026-09-01 · owner: rol1 · size: M · trigger: —
  What: `backtest.walk_forward` rejim-dilimli `graded` popülasyonundan ikinci bir `score_detail` döndürsün; rejim ship satırları da kendi `backtest_full`ünü taşısın. Why: akıbet-dalgası N00017'yi yalnız GLOBAL ship için kapattı — `full_detail` rejim-dilimsiz popülasyondan üretiliyor, rejim satırına yazmak analytics'in öncelikli bacağına yanlış popülasyon koyardı (implementer endişe-1, bilinçli dışarıda bırakıldı). Ref: akibet-dalgasi-rapor · N00017.
- **[TSK-003] Reflect belleğe danışmadan öneri basıyor (yansıma mükerrerlik kapısı)** — status: DONE(2026-09-01·131ffa8 — mukerrerlik.py + v352 28 çivi, iki-kaynaklı kapı; israf hedefi %45→≤%10 sonraki karar turunda ölçülür) · born: 2026-09-01 · owner: rol1 · size: S-M · trigger: —
  What: hermes_reflect öneri üretirken hiçbir belleğe (akıbet defteri/kod/Hindsight) danışmıyor; öneri (a) reflect anında akıbet defterindeki açık+kararlı önerilere ucuz benzerlik kontrolü, (b) ingest-sonrası Hindsight recall'a terfi.
  Why: ilk karar turu ölçtü — 22 önerinin ~10'u (%45) bellek-yokluğu sınıfı (7 kopya + 3 zaten-var/çözülmüş/planda); hedef sonraki turda ≤%10. (a) bacağı aynı gece İCRA SIRASI D-revize araya-kalemine alındı (operatör, 2026-09-01); (b) arşiv ingest + recall kartını bekliyor.
  Ref: operatör sorusu 2026-09-01 gece · BOT RECALL kartı.
- **[TSK-004] "Gece ne buldu" hunisi üç kusur taşıyor** — status: DONE(2026-09-01·c32d13d — taranan alanı + etiket + üç-dallı dipnot; v353+17 UI çivisi; operatörün gece-otonomi emri kapsamında) · born: 2026-09-01 · owner: operator · size: S · trigger: —
  What: (a) ilk basamak etiketi "Taranan aday" yazıyor ama eleme-SONRASI `candidates`e bağlı (KararZinciri.tsx `GeceGovdesi`); (b) aday=0 gününde düşüş dipnotu yanlış nedeni gösteriyor ("ilk basamak yazılı değil" yerine "payda 0"); (c) `daily_cycle` olayına eleme-öncesi evren büyüklüğü (`taranan`) alanı eklenmeli.
  Why: operatör 2026-08-31 hunisini "hiç tarama olmadı" diye okudu; gerçek döngü 20:55Z'de koştu (0 aday + 1 near-miss, olağan). Boyut küçük ama okunabilirlik hatası tekrar eden yanlış-alarm üretiyor.
  Ref: operatör sorusu 2026-09-01 gece — akıbet-dalgası sınıfı bir sonraki küçük dalgaya mı yoksa havuzda mı kalacağı operatörde.
- **[TSK-005] `/api/infra` birim keşfi tek yönlü — makinede koşan-ama-repoda-yok birimler görünmüyor** — status: DONE(2026-09-01·c9b8c64 — beklenmedik_birimler bacağı 11 çivi; pano okuyucu bacağı TSK-086'da) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: bugünkü keşif yalnız `deploy/**`'ten repo→makine yönünü tarıyor; ikinci bacak `systemctl list-unit-files 'meridian-*' 'hindsight-*'` çıktısından repo listesinde olmayanları "repoda-yok/beklenmedik" bayrağıyla eklemeli.
  Why: kör yön aynı gece yaşandı — meridian-geridolum birimi makinede koşuyor ama canlı ağaçta dosyası henüz yok, panoda hiç görünmüyor; tek yönlü dedektör sürüklenmenin yarısını kaçırır.
  Ref: operatör sorusu 2026-09-01 gece ("birimler dinamik olmalı değil mi") — aynı gece İCRA SIRASI D-revize araya-kalemine alındı.
- **[TSK-006] `session_refresh` olayı defteri tekelleştiriyor** — status: DONE(2026-09-05 keşif: kod 63b64ab (KOVA B 2026-09-03), canlı c37ad06 — kayıt bayattı) · born: 2026-08-31 · owner: rol1 · size: S-M · trigger: —
  What: (HÜKÜM 2026-09-05 02:4xZ, keşif ölçümü A1: kesim 2026-09-02/03'te verilmişti (TSK-106 günlük özet + KOVA B IP anahtarı, v274/v374/v382) ve canlıda: 09-04 704 olayın 6'sı, son 24 sa 697'nin 4'ü session_refresh; gerçek tazeleme 1341/gün sürerken kayıt 1 satır/gün. Okuyan kod yok (Yasa 6: /api/events insan gözü). Tarihsel 22.100 satır / 3,24 MB (%25 satır) dosyada duruyor → TSK-137b rotasyonu. Bugünün kalabalık sınıfı sprint_cadence_skip ~284/gün + intraday_gap_detected ~230/gün → [TSK-141]. Why'daki '8.797/10.138 (%87)' A1/yerel defterde yeniden üretilemedi (günlük tavan 1.518) — kaynak muhtemelen journal. 08-27/28 defterde satır yok (açık soru, TSK-137b'de bak).) bu olay sınıfının defterde nasıl yaşaması gerektiği kararı gerekiyor — örneklem seyreltme / ayrı defter / özet satır seçeneklerinden biri.
  Why: 2 günlük olay kaydının %87'si tek olay (8.797/10.138) — pencereli tüketiciler (parite/inbox/selfreview/otonomi) daralmış tarih görüyor; canlı journal'da pano yolları başına 5 dk örneklemli satırlar yağıyor. Bedel yasası: gürültü kısılırken ne kaybedildiği de ölçülmeli.
  Ref: 2026-08-31 haftalık öz-değerlendirme triyajı.
- **[TSK-007] öz-değerlendirme `watchdog_incidents` mekanizma adını yalnız `mechanism` alanından okuyor** — status: DONE(2026-09-02 gece · `_olay_mekanizma()` düşüşü `mechanism→kind[:detector|:artifact]→artifact→mesaj-öneki→None`, v369 12 çivi + 2 mutasyon kanıtı; SDD incelemesi SPEC 12/12; commit gece kapanışında; yan keşifler TSK-101/102'ye) · born: 2026-08-31 · owner: rol1 · size: S · trigger: —
  What: `selfreview.py` çıkarımı `kind`→`artifact`→mesaj önekine düşecek şekilde genişletilmeli; çivi olay-sınıfı başına birer örnekle.
  Why: 21 olayın 19'unda `mechanism` alanı yok (`kind`/`artifact` taşıyor) — Telegram özeti "8 satırın 7'si isimsiz" çıktı.
  Ref: 2026-08-31 ölçümü.
- **[TSK-008] dagit bakım penceresi `meridian-learn`'ü yeniden başlatıyor — geri-dolum haftasında olmamalı** — status: DONE(2026-09-03 gece · ÖLÇÜLDÜ, kod gerekmedi: dagit [4] bakım penceresi TSK-092 istenen-durum korumasıyla `meridian-learn: disabled — istenen duruma saygı, pencere sonunda başlatılmadı` diyor — 2026-09-02'de iki dağıtımda (17:04 ve 20:19 UTC) doğrulandı, learn geri-dolum haftası boyunca kapalı kaldı [systemctl is-active inactive]) · born: 2026-08-31 · owner: rol1 · size: S · trigger: —
  What: kalıcı çözüm adayı — dagit'in restart listesini birim enabled-durumuna saygılı yapmak (disabled birim restart edilmemeli).
  Why: operatör kararıyla learn, geri-dolum bitene dek KAPALI (disabled+stopped); dagit onu yine de yeniden başlatıyor — bu akşam bir kez yakalanıp elle durduruldu. Her dağıtım sonrası "learn hâlâ kapalı mı" kontrolü şart; geri-dolum bitince learn'ü GERİ AÇMAK kapanış kaleminin parçası.
  Ref: 2026-08-31 geri-dolum haftası reçete notu.
- **[TSK-009] elle-kurulum penceresi: 5 ayrık dosya + `meridian-aylik-bucket-kopya` hiç kurulmamış** — status: DONE(2026-09-01 akşam · operatör pencere açtı, Rol-1 kurdu: 5 dosya yedekli [.bak-damgalı] + aylık-bucket service+timer kuruldu, timer armed 3 Eyl 04:03Z; AÇIK KALEM KAPANDI 2026-09-01 ~15:52Z [operatör "sabah paketini şimdi yap" penceresi]: elle test-ateşleme BAŞARILI — Result=success, exit 0, 1dk33sn/235MB tepe; arsiv/intraday/2026-08 tar'ı 69MB bucket'a yüklendi [sha256 75cf5342…, yuklendi:true, yerel-silme birim tasarımı gereği YOK]. Artık "çalışır") · born: 2026-08-31 · owner: operator · size: S-M · trigger: —
  What: hermes profil manifestleri (sef/bekci/karne `distribution.yaml`) + kök `SOUL.md`/`config.yaml` repoda zenginleşti ama canlıya elle taşınmadı; `meridian-aylik-bucket-kopya` service+timer hiç kurulmamış.
  Why: kurulu≠çalışır sınıfı — kurulum reçetesi `deploy/oracle-a1/deploy.sh`ta hazır, bakım penceresi + daemon-reload gerektiriyor.
  Ref: 2026-08-31 dağıtım F9 özeti (5 ayrık + 2 ölçülemedi).

- **[TSK-010] filo-yönetim MCP sunucusu — şimdi gerekmiyor** — status: GATED(yeni istemci filoya programatik erişim istediğinde: cloud oturumları · botların birbirini yönetmesi · operatörün Claude Desktop'tan filo sürmesi) · born: 2026-08-31 · owner: rol1 · size: M · trigger: yukarıdaki üç sınıftan biri doğduğunda
  What: bugün `meridian/mcp_server.py` (ajan→sistem, salt-okunur) ve `ops/filo.py` + Ajan-B köprüsü orkestratör→filo boşluğunu zaten kapatıyor; tetik geldiğinde Ajan-B'nin API yüzeyi MCP sarmalayıcıyla yayınlanır (yeni filo üyesi disipliniyle: birim+çivi+F9+güvenlik duruşu, salt-okunurla başlar). KOD YOK.
  Why: değerlendirme 2026-08-31, operatör sorusu üzerine — ihtiyaç henüz ölçülmedi.
  Ref: operatör sorusu 2026-08-31.

- **[TSK-011] cf tarama kuyruğu `reset_index(drop=True)` — kazanç-çapalı üreticiler çapaya ulaşamıyor** — status: DONE(2026-09-02 · b5f9c8d: cf tarama kuyruğu `date` sütununu taşır, kart EDG-2026-068 kart-önce; çivi v345 `test_cf_taramasi_KAZANC_CAPASINA_ULASIR` — ROADMAP durumu 2026-09-03 sabah ölçümle DÜZELTİLDİ, flip atlanmıştı) · born: 2026-08-31 · owner: rol1 · size: S · trigger: —
  What: `cf_backfill._plans_for_session` kuyruğuna `date` sütunu eklenmeli; düzeltme kartsız yapılamaz (kart-önce) çünkü `drop=True`ı kaldırmak cf defterine iki uyuyan kurulum sokar ve karşı-olgusal bileşimi değiştirir.
  Why: kazanç-çapalı iki üretici (pead/episodic) cf'de çapaya HİÇ ulaşamıyor; beyanlı-sıfır + çürüme çivisi v345'te zaten bu gerçeği anıyor (korumalı-zincir kaydı).
  Ref: EDG-062 Görev-3 bulgusu, 2026-08-31.

- **[TSK-012] pano 'Ajan' bölümü — ajan iletişim yüzeyi (A: zaman-çizelgesi, B: sohbet)** — status: GATED(yalnız dalga-B kaldı: sohbet, duruş çivili; dalga-A DONE 2026-08-31) · born: 2026-08-31 · owner: rol1 · size: M · trigger: dalga-B penceresi (İCRA SIRASI)
  What: Rol-1 düzeltmesi 2026-09-01 (FAZ B bulgusu): dalga-A KAPANDI — git kanıtı "Ajan-A kapanış partisi: canlı doğrulama işlendi" (ops/filo.py tarihçesi) + TSK-058'in kendi trigger beyanı; eski tek-durum satırı iki bacağı birleştirip yanıltıyordu. (A) salt-okunur zaman-çizelgesi — `state.db` (sessions/messages/session_model_usage, veri kaynağı zaten hazır) + teslim olayları + son_brifing arşivi, `/api/ajanlar` ucu; (B) A + sohbet — pano→API→hermes tek-atışlık çağrı, AYNI güvenlik duruşuyla (guard kancası + kapalı araç takımları + safe-root + pano token'ı, §9.4 üçlüsü). Sıra: A önce, B hemen ardından; sohbet muhatapları üç bot + ana Hermes beyni.
  Why: iki gereksinim operatörden geldi — Telegram mesajlarının anlaşılırlığı (SOUL 'ilk satır sade özet' kuralı ayrı küçük kalem) ve panoda TÜM ajan iletişiminin görünür + iki yönlü olması. Veri kaynağı 2026-08-31'de doğrulandı.
  Ref: OPERATÖR TALEBİ 2026-08-31, kapsam kararı aynı gün.

_**[2026-08-31 KONSOLİDASYON — HAVUZ GİRDİSİ ROZET TAŞIMAZ.]** Burası backlog'dur: girdi tahtaya terfi ettiği gün rozet alır; havuzda rozet taşımak çift-defter olurdu. `/api/roadmap` bu maddeleri `belirsiz` sayar ve **bu doğrudur**._

- **[TSK-013] tick programı — ücretsiz kaynak değerlendirmesi** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: M · trigger: —
  What: (operatör 2026-09-03 sabah: BEKLEMEDE — Senaryo-A kart-önce önerisi ertelendi, reddedilmedi.) tam bant (SIP) ücretsiz YOK; iki ücretsiz sınıf ölçüldü — (1) Alpaca IEX canlı akışı (30 kanal tavanı, ~%2-3 hacim), (2) IEX Exchange HIST (T+1 ücretsiz pcap, replay/araştırma sınıfı). SENARYO-A (icra-anı quote kaydı, yalnız o günkü plan+pozisyon sembolleri) 30-kanal tavanına TAM oturuyor — pilot tamamen ücretsiz kurulabilir. Kart-önce: pilot EDG-kartı (kayıp oranı · IEX-quote/dolum tutarlılığı · disk-CPU · worker etkisi kill'i) açılmadan kod yok.
  Why: operatör "tick için ücretsiz kaynakları değerlendirelim" dedi; SENARYO-B (tam akış) ücretsizle olmuyor — ücretli bant kararı operatörde.
  Ref: operatör 2026-08-31 gece; ikincil aday Finnhub free websocket (bant kaynağı/yeniden-dağıtım şartı doğrulanmadı).
- **[TSK-014] teslim-öncesi ikinci-görüş geçişi (SOUL kural denetimi)** — status: ACTIVE · born: 2026-08-31 · owner: rol1 · size: S-M · trigger: —
  What: (YENİDEN ÖLÇÜM 2026-09-04 22:04:55Z brifingi: brifing_kural_denetimi kaynak=LLM (dün llm_dustu), cagri_n 4, yeniden_uretim true, 429 sıfır — kök neden kota doğrulandı; ama 4 ihlalin 3'ü alan-adı yanlış-pozitifi ('bekçi', "stop_gap'i", 'iyileştirme önerisi') → 2/2 ihlal, HAM teslim → [TSK-138].) (status notu 2026-09-03 22:20Z: CANLI GÖZLEM 22:04Z — denetim KOŞTU (event var), hüküm `denetlenemedi`, kaynak `llm_dustu`, cagri_n 2, gerekçe 'denetçi cevabı JSON değil'. KÖK NEDEN kod değil KOTA: openrouter ücretsiz gün kotası 21:xxZ'de tükendi ('free-models-per-day-high-balance' 429 ×3.096, ingest067 çıkarımı + Hindsight konsolidasyonu aynı kota) → denetçi cevabı boş/hata metni. Karar: DONE damgası 2026-09-04 22:00Z gözlemine (ingest akşam koşmayacak); küçük iyileştirme: `ops/soul_denetimi.py` `_dustu` gerekçesine ham cevabın ilk 80 karakteri (sanitize) — Yasa 6 okuyucusu bu event. Kota muhasebesi → [TSK-130].) (status notu 2026-09-03 12:28Z: CANLIDA 0bda163/dağıtım #7 12:27:57Z; DONE damgası 22:00 UTC brifingde `brifing_kural_denetimi.kaynak` gözleminden sonra — llm ise DONE, llm_dustu ise K-2 biçim cümlesi yetmedi → düzeltme) brifing üretilince ikinci bir LLM çağrısı çıktıyı SOUL kurallarına (sade-özet · terim korunumu · uydurma-kelime) karşı denetler; ihlalde en çok bir yeniden-üretim; kural-uyumsuz çıktı Telegram'a düşmez. LLM-düşerse-ham-teslim sözleşmesi aynen kalır (denetçi düşerse ilk çıktı beyanla gider).
  Why: operatör onayladı; zemin uygun — günlük 1000 çağrı kotasının bugünkü kullanımı ~%0,2. Üç bot + ileride Ajan-B cevapları kapsar.
  Ref: operatör onayı 2026-08-31.
- **[TSK-015] ajan kalıcı hafızası — 4 aday değerlendirildi, sıralama HİÇBİRİ→Hindsight→mem0→Supermemory→Honcho** — status: GATED(Ajan-B inince semantik-arama ihtiyacı ölçülürse) · born: 2026-08-31 · owner: operator · size: M · trigger: Ajan-B canlıya girip semantik-arama ihtiyacı ölçülmesi
  What: kıyas ekseni — self-host şartı (ticaret verisi dışarı çıkamaz) · filo-disiplini bedeli · enjeksiyon-kalıcılaşma yüzeyi · çok-ajan kimlik ayrımı · LLM-sağlayıcı bağı · olgunluk. Dört aday da 'LLM-çıkarımlı serbest metni sonraki prompt'a geri koyma' sınıfı — botlarda memory'nin kapalı olma gerekçesinin ta kendisi. Gerçek kazanç alanı: yapılandırılmamış metinde semantik geri getirme (pano sohbeti · günlük/kart arşivi araması), o ihtiyaç Ajan-B ile doğar.
  Why: 'geçen sefere göre ne değişti' yeteneği depoda zaten ölçülü-halde var (damga + üçlü kimlik + OLCULEMEDI-geçişleri) — dış katman onu tekrarlamaz. Tetiklenirse Hindsight kartla denenir (provenans/kanıt-izi + PII taraması depo kültürüyle aynı dil; MIT; tek servis+pgvector). Deneme kartsız başlayamaz. Operatör vetosu açık.
  Ref: docs/DEGERLENDIRME-HAFIZA-ADAYLARI-2026-08-31.md; operatör yönü "memory olmalı, hatta persistent memory olmalı".
- **[TSK-016] hermes skill öz-iyileştirme — ölçülü kanalda açılabilir** — status: GATED(EDG-019/063 taban ölçümü tamamlanınca) · born: 2026-08-31 · owner: rol1 · size: M · trigger: mevcut skill'lerin değeri ölçülmesi (ilk kanıtlar: vcp avg_r 0,0 · pullback cf −0,968)
  What: Hermes Agent'ın meta-learning yeteneği (ajan kendi SKILL.md'sini yazar/rafine eder) kapı felsefesiyle açılır — taslak GÖLGE-ADAY alanına yazılır (aktif kümeye/profil evine DEĞİL), her taslak görüş defterine (EDG-019/063) üretici olarak girer, çözücü puanlar, terfi kanıt+operatörle. "Yazar ama kendi yazdığını kendisi yürürlüğe koyamaz."
  Why: kendini-değiştiren kalıcı prompt yüzeyi injection-kalıcılaşma sınıfı — botlarda memory'nin kapalı olma gerekçesiyle aynı; mevcut skill'lerin değeri ölçülmeden evrim hedefsizdir.
  Ref: operatör onayı 2026-08-31 (hermes skill self-improvement).
- **[TSK-017] 6 skill reposu değerlendirildi — 4'ü ALINMADI, 2'si derin-okuma adayı** — status: DONE(2026-08-31·operatör sorusu yanıtlandı) · born: 2026-08-31 · owner: rol1 · size: S · trigger: —
  What: planning-with-files (bizde daha sıkısı yerleşik) · delegate-skills · Agent-Reach (botların kapalı-web duruşunu deler — VERI-çiti saldırı yüzeyi) · rtk (hüküm-taşıyan komut çıktısını değiştiren proxy — üçlü-hüküm riski) ALINMADI. google/mantis + skill-retrieval, EDG-019/063 ölçümünden SONRA derin-okuma adayı (GATED).
  Why: ilke kaydı — Claude süreç-skill'leri (superpowers) Meridian çalışma zamanına yüklenmez, taşınan şey damıtılmış kuraldır (CLAUDE.md/SOUL çivili formu); dış skill içeriği yalnız hermes-SKILL.md + görüş-defteri ölçümü yolundan girer.
  Ref: operatör 6 skill reposu sordu, 2026-08-31.
- **[TSK-018] bot filosu zamanlı→olay-tetikli geçiş kaydı** — status: GATED(alarm katmanının ifade edemediği, saatlerin önemli olduğu ölçülmüş bulgu sınıfı doğarsa) · born: 2026-08-31 · owner: rol1 · size: S · trigger: yukarıdaki bulgu sınıfının ölçülmesi
  What: tetiklenirse çözüm sürekli-daemon değil olay-tetikli ONESHOT (path-unit/OnFailure sınıfı) olur. KOD YOK.
  Why: bugün öyle bir sınıf ölçülmedi — kayıt yalnız gelecekteki tetik için tutuluyor.
  Ref: 2026-08-31 tetik kaydı.
- **[TSK-019] seyrelme mekanizması ölçülemiyor — E2'de ret/veto ayna-satırı yok** — status: DONE(2026-09-02 gece · SDD tam döngü: kart-önce EXE-2026-011 + implementer + inceleme + 2 düzeltme turu; `loop._ayna_seyrelme_yaz` EOD dikişi [kohort=önceki seans — çift-iz kill#1 yapısal kapalı, karta beyanlı] + donuk 3-sınıf sözlük [K-1: kapı damgalı anomali olculemedi'ye] + `selfreview.week.donusum` + `/api/diagnostics` yüzeyi; v372 16 çivi + v280 onarımı; kart `measured_partial` — canlı ilk-hafta kolu açık, TSK-104 tetiği o birikim) · born: 2026-08-31 · owner: rol1 · size: S-M · trigger: —
  What: E2'ye ret/veto ayna-satırı eklenmeli (kartlı, PIT-uyumlu) — "kaç plan doluma dönüşmedi" sorusu bugün okunamıyor.
  Why: kaydırma sonrası plan-günü sıklığı değişmedi (0,38→0,40/seans) ama plan-günü başına dolum 3,0→1,0 düştü; sebep E2 ile ölçülemez çünkü defterde 36/36 submitted+dolu, ayna satırı yok. Bu sayı 1345 kolunun eşik takvimini belirliyor; ölçülemedikçe EDG-042 takvimi izdüşümde kalır.
  Ref: 85-aktarımı, EDG-042 P-3 bloğu "AYRI KALEM ADAYI" kaydı, 2026-08-31.
- **[TSK-020] backend mimari kararları — 9 kalem; sıra REVİZE (operatör 2026-09-01 gece): `4→2-adım2→3→1→9` (eski `8→4→2→1→3→9`; UYGULA-8 DONE, `2-adım1` İLK SIRA araya-kalem bloğuna alındı)** — status: QUEUED · born: 2026-08-31 · owner: rol1 · size: L · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: UYGULA-2 adım-3 TSK-137 adım-2'ye devredildi (tek kalem); kalan sıra 4→(2 devredildi)→3→1→9.) operatör brainstorm kapanışı (2026-08-31), zemin iki ölçümle düzeltildi — Redis KURULU ve ENTEGRE (hotstate.py, `mrd:` şeması, Streams+consumer-group üretimde); "daemon yasağı" diye bir yasa YOK (A1'de 5 kendi daemon'ımız koşuyor, gerçek yasa filo disiplini: birim+çivi+F9+yedek hikâyesi). Kalemler:
  · [UYGULA-1] SQLite göçünü bitir — kalıcı sıcak durum `store`→SQLite WAL; boyut büyük (motor); Postgres tetiği eşzamanlı yazıcı sınıfı (bugün yok).
  · [UYGULA-2] DuckDB analitik — adım 1 **DONE (2026-09-01):** `ops/olay_sorgu.py` (ozet/son/tip + yalnız-SELECT `--sql`, bozuk-satır sayımı stderr'e, meridian-import'suz, sertleştirilmiş bağlantı) + v355 36 çivi; adım 2 **KOD İNDİ 2026-09-03 gece** (`ops/olay_sikistir.py` + olay_sorgu birleşik okuma [parquet kazanır]; v379 37 çivi; canlı ilk koşum sabah bakım penceresinde — state/ kapısı); boyut orta.
  · [UYGULA-3] bars→Parquet (ay/sembol bölümlü) + DuckDB; TimescaleDB DEĞİL (debi ~98k satır/gün, küçük-veri rejimi, PIT'e ters).
  · [UYGULA-4] kalıcı-önbellek envanteri — `*_cache.json` sınıfından hangisi restart-sonrası gerçekten gerekli ÖLÇ; boyut küçük.
  · [TETİKLİ-5] olay/mesajlaşma — Redis Streams zaten üretimde; Kafka tetiği tüketici çeşitliliği + uzun replay (uzak). KOD YOK.
  · [TETİKLİ-6] kuyruk — systemd kalır; "tetikleyen işi koşamaz" deseni ölçülürse arq (Redis-tabanlı, async). KOD YOK.
  · [BEKLEMEDE-7] sır yönetimi — operatör "şu an kalsın"; kademeli yolun ilk basamağı (LoadCredential/sops hazırlığı) İCRA SIRASI ④'e alındı, OpenBao/unseal adımı beklemede.
  · [UYGULA-8] pytest-xdist spike — **DONE (2026-09-01):** `-n 4` pyproject'e pinlendi (~9 dk, 2 temiz koşum, 8.344 test, 0 paralellik kırmızısı — `xdist_group` gerekmedi); tarihçe: tetik ~26 dk × günde 6+ koşumla ateşlenmişti, ilk sıra olarak koştu.
  · [UYGULA-9] gecikme telemetrisi — Prometheus+Grafana (pano-SQLite alternatifi elendi); kill-kriteri yeniden çapalama AYRI KART ister.
  Why: PIT-(b) uygulaması (EDG-2026-062) bu kuyruğun ÖNÜNDE — operatör kararı daha eski.
  Ref: operatör 2026-08-31 brainstorm kapanışı; sıra 8→4→2→1→3→9 (5/6 tetik kaydı, 7 beklemede).
- **[TSK-095] openrouter/auto değerlendirmesi — künyesiz LLM yüzeyleri için** — status: ACTIVE · born: 2026-09-01 · owner: operator · size: S · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: `openrouter/auto` DEĞİL — https://openrouter.ai/openrouter/free (ücretsiz modeller arasında yönlendiren 'free' router) TEST EDİLSİN. Plan (Rol-1): (1) keşif — free router'ın model kümesi, cevapta gerçek model künyesi dönüyor mu (`model` alanı; dönüyorsa kart künyesi post-hoc yazılabilir), hız sınırı, boş-cevap oranı; (2) yalnız künyesiz yüzeyde (ikinci-görüş/sohbet sınıfı) 2 hafta, harcama + boş-cevap + kalite karşılaştırmalı; ölçüm/kart yollarına ve Hindsight ingest künyesine GİRMEZ (EDG-067 model şartı). Ücretsiz havuz boğulması (nemotron timeout + gemma 429) bu router'ın çözdüğü sınıf — kanıtlanırsa ingest için ayrı karar.) (operatör 2026-09-03 sabah: BEKLEMEDE — karar ertelendi, bedel aynen sürer.) OpenRouter duyurusu (operatör iletti, 2026-09-01 maili): `openrouter/auto` istek başına model seçiyor (task sınıflandırma + topluluk 7-gün harcama sıralaması; router ücreti yok, SEÇİLEN modelin fiyatı ödenir; `cost_tier` bandı; hesap-düzeyi model kısıtları auto'ya da uygulanır). DEĞERLENDİRME (Rol-1): canlı ÖLÇÜM yüzeylerinde KULLANILMAZ — model künyesi önceden bilinemez ve 7-günlük pencereyle KAYAR (ölçüm tekrarlanabilirliği + kart model-kaydı disiplipiyle çelişir; EDG-063/hindsight künye şartı). ADAY yüzey: künye gerektirmeyen sohbet/ikinci-görüş sınıfı — ANCAK önce hesapta "yalnız :free modeller" kısıtının auto'yu gerçekten bağladığı ÖLÇÜLMELİ (bağlamazsa her istek bilinmeyen tutarlı harcama = para kararı). Bugünkü kapı zinciri (ai-proxy-multi, pinli modeller) deterministik ve beyanlı — auto onun yerine değil, olsa olsa yanına.
  Why: bugün ölçülen free-havuz boğulması (nemotron timeout + gemma 429) auto'nun çözdüğü sınıfa yakın; ama bedeli opak yönlendirme. Öneri-akışı kuralı: kaybolmasın diye işlendi.
  Ref: operatör maili 2026-09-01 · TSK-089 Faz 1 §7 kaydı (ölçülen dersler).
- **[TSK-094] TSX satır-çapalarının sembol-çapaya göçü** — status: DONE(2026-09-02 gece · SDD tam döngü: implementer + inceleme + düzeltme turu + re-review onayı; 141/141 TSX çapası `dosya.py::sembol`e göçtü, ui/src'te kalan satır çapası 0, `TSX_CAPA_TABANI` 32→0; süpürmede 9 yanlış eşleme yorum-doğrulamasıyla bulunup düzeltildi — tarayıcı 9'unda da yeşildi, VARLIK≠YERİNDELİK sınırı rapor §2.1'de; v373 20 + v314 16 çivi) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: pano TSX kaynaklarındaki `api.py:NNNN` biçimli 73 satır-çapasından 36'sı `api.py`'nin tek bir bölgesinin (≈3555 altı) altını gösteriyor; `api.py`'ye eklenen her satır bloku hepsini birden kaydırıyor. Çapalar sembol-çapaya (fonksiyon adı) taşınır; v214 çivisi taban-aşımı yerine tekil çürümeyi ölçebilir hâle gelir.
  Why: vaka 2026-09-01 (TSK-058 fix turu 2): +38 satırlık api.py eklemesi 36 çapayı kaydırdı, v214 iki kırmızı verdi; satır-nötr sıkıştırmayla geçildi ama sayaç 32→23 "düşüşü" iyileşme değil yanlış hizalanma — v214 yalnız taban aşımını ölçtüğü için kayan-ama-yorum-olmayan çapalar sessizce yanlış. CLAUDE.md §2 çapa kuralının ölçülmüş yeni örneği.
  Ref: TSK-058 fix raporu 2026-09-01 · tests/test_… v214 (`tsx_line_anchor_nuks`).
- **[TSK-093] Skill-görüş karışık-üretici ileri kalemleri** — status: GATED(iki-üreticili skill doğuşu) · born: 2026-09-01 · owner: rol1 · size: S · trigger: bir skill'in hem det hem llm satır taşımaya başlaması (uretici_kirilimi'nde aynı skill iki kovada)
  What: iki kalem — (1) `_anahtar` üretici taşımıyor: iki-üreticili skill'de deterministik yol, llm gölge satırlarını "zaten_var" sayıp atlar (skill'in det ölçümü kendi gölgeleriyle susturulur); tekilleştirme anahtarı DONUK olduğundan değişiklik göç planı ister. (2) `api._gorus_kuyrugu` sayaç için tam kesit yükünü ayrıştırıyor (mertebe farkı yok bugün; okuyucu sayısı artarsa hafif okuyucu).
  Why: TSK-058 fix-turu-2 re-review bulguları (2026-09-01); bugün evrenler ayrık — karışık üretici YOK, rapor() bu hâli `uretici=None + neden:karisik_uretici` ile beyan ediyor (fail-closed). Tetik gerçekleşmeden dokunmak spekülatif.
  Ref: TSK-058 · re-review raporu 2026-09-01 · EDG-2026-019 (donuk tekilleştirme hükümleri).
- **[TSK-092] Dağıtım reçetesi birim istenen-durum koruması — start satırı sabit üçlü paket olamaz** — status: DONE(2026-09-03 fb07a16 dağıtım #6) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (status notu 2026-09-03 08:57Z: B-12 dilimi tek ajana SEVK EDİLDİ — brief .superpowers sdd kovab-b12, git-dışı.) dağıtım akışındaki `systemctl stop/start` satırları sabit birim listesi yerine her birimin dağıtım-öncesi İSTENEN durumunu okuyup korur (bilinçli-durdurulmuş birim start satırına girmez); reçeteye "durdurulmuş birimi başlatma" kalemi + çivi.
  Why: vaka 2026-09-01 — dün gece bilinçli durdurulan meridian-learn, sabah dağıtımının üçlü stop/start paketiyle geri başladı ve ~4 saatte 6h40m CPU yedi; operatör işaretiyle yakalandı (§7 triyaj kaydı). Aynı sınıf hata her dağıtımda tekrarlanabilir.
  Ref: §7 günlük 2026-09-01 canlı-triyaj kaydı · journalctl kanıtı 06:36:11Z (stop) / 06:36:13Z (start).
- **[TSK-021] `earnings_8k_tarihleri.csv` motorda hiç okunmuyor** — status: DONE(2026-09-02 · EDG-2026-062 d9bad5f: earnings_pit.py csv'yi OKUR — tarihsel kazanç çapası EDGAR 8-K arşivine bağlandı, yol b; ROADMAP durumu 2026-09-03 sabah ölçümle düzeltildi, üçüncü bayat flip) · born: 2026-08-31 · owner: rol1 · size: — (boyut seçilecek yola bağlı — ölçülemez, beyanlı) · trigger: —
  What: PIT-damgalı 8-K arşivi var ama hiçbir yol tüketmiyor; PIT ihlal düzeltmesinin (b) yolu onu okuyucuya kavuşturur.
  Why: PIT çivisi ölçümü, Yasa 6 adayı (üretilen alanın okuyucusu yok).
  Ref: docs/DEVIR-PIT-CIVISI-2026-08-30.md §1.4.

**BU BÖLÜM 2026-08-13'te BOŞALTILDI; 2026-08-14'ten beri 30-48 dalgası yine burada birikiyor —
sahipli kalemler ilk fırsatta WP'lerine taşınmalı.** Burası artık yalnız **sahibi henüz belirlenmemiş** yeni
önerilerin bekleme odasıdır: bir öneri buraya yazılır, sahibi (cephe) belirlenince ilgili
**WP1-WP11**'e taşınır ve burada yalnız tek satırlık taşıma izi kalır. Biçim:
`gerekçe · tahmini boyut · bağımlılık · öncelik`. Ölçüm önerileri karta (§6) dönüşür; operatör
kararı gerektirenler §5'e geçer.

> **BOŞALTMA KAYDI (2026-08-13 — operatör talebi "bütün önerilerini WP'lerde ilgili yerlere dağıt";
> denetim `docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md`):** havuzdaki **29 kalemin tamamı**
> boşaltıldı — **20'si** sahibi olan WP'ye taşındı (gövde metni AYNEN, kısaltma YOK), **9'u** (Ö-1 ·
> Ö-5 · Ö-6 · Ö-11 · Ö-12 · Ö-17 · Ö-19 · Ö-21 · Ö-22) tümüyle §8 arşive alındı; ayrıca **5
> kapanmış ALT-kalem** (15a · 15b · 15f · 20a · 24a) arşive ayrıldı. Her taşınan kalem hedefinde
> "_(taşındı: §4-N, eski satır :A-B)_" izini taşır; hiçbir madde SİLİNMEDİ.
>
> **TAŞIMA HARİTASI:** Ö-23 + Ö-13 → **WP1** · Ö-27 + Ö-7 + Ö-9/Ö-18(birleşik) → **WP2** ·
> Ö-28 + Ö-10 + Ö-19(artık) → **WP3** · Ö-8 → **WP4** · Ö-4 + Ö-14 + Ö-20 + Ö-16 → **WP5** ·
> Ö-25 + Ö-26 + Ö-2 → **WP6** · Ö-24 → **WP7 (yeni cephe)** · Ö-3 → **WP8** · Ö-15(c/d/e/g) +
> Ö-29 + Ö-12(iz) → **WP11**.
>
> **YAPISAL ARTEFAKT KAPANDI (denetim §I):** §4'nin numara düzeni bozuktu (1-15, sonra 21, 22, 19,
> 20, 16, 17, 18, sonra 23-27, 29, 28) ve Ö-16'nın gövdesi Ö-15'in kuyruğunu taşıyordu — ikisi de
> birleştirme artefaktıydı ve bu boşaltmayla yapısal olarak kapandı (kuyruk WP11-F'ye taşındı).

> **BOŞALTMA KAYDI (2026-08-23 — 30-50 dalgası; §4 başlığının kendi beyanı "sahipli kalemler ilk
> fırsatta WP'lerine taşınmalı" gereği; usul 2026-08-13 kaydıyla AYNI):** havuzdaki 21 kalemden
> **8 gövde** sahibi olan WP'ye taşındı (gövde metni AYNEN, kısaltma YOK; Ö-35 iki yarıya bölündü,
> ortak başlık satırı iki hedefe de kopyalandı). Her taşınan kalemin yerinde üstü-çizili tek satır
> iz, hedefinde "_(taşındı: §4-N, eski satır :A-B — 2026-08-23)_" izi var; hiçbir madde SİLİNMEDİ.
>
> **TAŞIMA HARİTASI:** Ö-32 + Ö-35(a) → **WP5-G** · Ö-49 + Ö-38 + Ö-34 → **WP6-E** (Ö-49'un beyan
> ettiği sahip adı WP-H = bugünkü WP6) · Ö-31 + Ö-40 → **WP7** · Ö-44 → **WP8-D** · Ö-35(b) →
> **WP11-G**.
>
> **HAVUZDA KALANLAR (taşınMADI — yalnız etiket eklendi, metin değişmedi):** Ö-50 · Ö-48 · Ö-45 ·
> Ö-47 · Ö-37 → **KART ADAYI** (beşinin de sıradaki işi kendi metninde "kart-önce"/ölçüm; kartı
> Rol-1 yazar) · Ö-36 → **§5 ADAYI (operatör)** (operatör bilgilendirmesi — B3 emsali; taşımayı
> Rol-1/operatör yapar). **DOKUNULMAYANLAR:** Ö-39 ve Ö-41 (Rol-1 kararı bekliyor) · Ö-30 (sahibi
> belirsiz: "WP2 ya da WP6 — sınıflandırma Rol-1'de") · Ö-42 (sahibi beyan edilmemiş) · Ö-43 ·
> Ö-33 · Ö-46 (ders/kayıt kalemleri — taşınacak açık iş gövdesi yok).
>
> **[2026-08-24 STOK KAMPANYASI ELEME — yukarıdaki paragrafın BEŞ etiketi artık bayat (gövdeler
> yerinde, hükümler kendi maddelerinde):** ~~Ö-45 KART ADAYI~~ → **KAPANDI-BAYAT** (EDG-048 NO-GO
> tüketiciyi kapattı) · ~~Ö-47 KART ADAYI~~ → **KAPANDI-BAYAT** (+ holdout kuyruğu BİRLEŞTİR →
> WP5-A 2D) · ~~Ö-37 KART ADAYI~~ → **TASARIM-KAPANIŞI** (sıra YOL-2 > YOL-1'e çevrilir) ·
> ~~Ö-39 DOKUNULMAYAN~~ → **TASARIM-KAPANIŞI** (yol (b): ayrı atıf defteri `state/plan_atif.jsonl`) ·
> ~~Ö-41 DOKUNULMAYAN~~ → **TASARIM-KAPANIŞI** (davranışsal ~27 girer, metin-tarayan ~19 beyanlı
> dışarıda; boşluk 41→46 BÜYÜDÜ). Belgeler: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` ·
> `docs/ELEME-WP7-2026-08-23.md` · `docs/ELEME-WP5-2026-08-23.md`.**]**

- **[TSK-022] öğrenme döngüsü API süreciyle aynı süreçte koşuyordu — GIL panoyu boğuyordu** — status: DONE(2026-08-17·v249: pano 14,0→0,027 sn, API CPU %93→%2) · born: 2026-08-16 · owner: rol1 · size: M · trigger: —
  What: kök neden öğrenme döngüsünün API sunucusuyla AYNI SÜREÇTE bir Python ipliği olmasıydı — GIL pano isteğini backtest hesabının arkasına diziyordu; işçi tavanı (`_havuz_tavani = max(1, min(4, cpu−2))`) bu paylaşım kusurunun YAMASIYDI, tasarım tercihi değil (2026-08-03 canlı olayı: iki işçi pano API'sini boğdu). Çözüm: öğrenme döngüsü kendi systemd birimine taşındı (emsal: `meridian-sprint`).
  Why: py-spy ölçümü 25 sn profilde patoloji göstermedi (dağınık normal backtest yükü); kök tanı restart'ın uykudaki aramayı uyandırması + GIL paylaşımıydı, regresyon DEĞİLDİ. Kazanç zinciri: pano GIL'de beklemez, tavan cpu−2'den cpu−1'e çıkabilir, faz-1 fold'lar bölünebilir hâle geldi.
  Ref: kaynak §8.T/H; sahibi WP3+WP6; kart açıldı 2026-08-23, sonuç v249'da kapandı.
- **[TSK-023] çapa/beyan çürümesi — yasa kuruldu, açık kalemler WP6-E'ye taşındı** — status: DONE(2026-08-23·WP6-E'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP6-E'de yaşıyor; burada yalnız taşıma izi kalıyor (§4'ün kendi kuralı: sahipli kalem WP'sine taşınır).
  Why: havuz yalnız sahibi belirsiz önerilerin bekleme odasıdır.
  Ref: taşındı: §4-49 → WP6-E, 2026-08-23. eski: Ö-49.

- **[TSK-024] keşif üreticisi canlıda taşınmayan düğmelere öneri üretiyordu — 30/47 önerinin 29'u ölü hedefe gidiyordu** — status: DONE(2026-08-22·süzgeç+öncül düzeltmesi, bugünkü bounds 32/32 motor-okuyuculu) · born: 2026-08-14 · owner: rol1 · size: M · trigger: —
  What: `propose_virgin_knob` adaylarını `bounds.yaml`dan seçiyordu ve "hiç denenmiş mi"ye bakıyordu, "canlı params'ta var mı"ya BAKMIYORDU — 21×`entry.w_turnover` + 8×`regime.vix_backwardation_gate` canlıda YOK düğmelerine üretim yapıyordu. Düzeltme: (a) üretici canlı params'a süzgeç uygular, (b) bounds↔motor okuma yüzeyleri eşleştirilir, (c) gerçekten ölü olanlar ayrı kaleme gider.
  Why: kök canlıda ölçüldü — `bounds.yaml` 32 düğme taşıyor, canlı `strategy.yaml` params 18 (14 düğme bounds'ta var canlıda yok). 28a uygulanana kadar bu kusur arka plan süzgeci tarafından guard'dan ÖNCE gizleniyordu — keşif bütçesinin %62'si (29/47) canlıda taşınmayan düğmeye gidiyordu.
  Ref: kaynak §8.T/F; sahibi WP3; kart açıldı 2026-08-23, akıbet kuru koşumda ölçüldü (v247 dağıtılmadı).

- **[TSK-025] 28d teşhisi — eşik düşürmek tıkanıklığı açmaz** — status: DONE(2026-08-23·EDG-2026-048 NO-GO tüketiciyi kapattı) · born: 2026-08-23 (born tahmini: bu iz satırında orijinal tarih yok, kapanış tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle §8.H/A'da taşınmış durumda; burada yalnız kapanış izi kalıyor.
  Why: EDG-2026-048'in NO-GO hükmü bu tıkanıklığın tüketicisini kapattı.
  Ref: §8.H/A (taşındı 2026-08-30).

- **[TSK-026] 28f — teyit deliği iki nüshalıydı, ikincisi ROADMAP'te hiç yoktu** — status: DONE(2026-08-23·ARŞİV, reflect.py fail-closed ayrımı kodda) · born: 2026-08-14 · owner: rol1 · size: — · trigger: —
  What: (a) TEYİT ayağı — `if conf.law == "probabilistic"` olasılıksız hükümde blok tamamen atlanıyordu, teyitsiz ship ediliyordu; (b) ARAMA ayağı (ölçümle bulundu, ROADMAP'te hiç yoktu) — `evaluate_search` "dilim yok" ile "dilim var ama ölçemedim"i aynı dala sokup gevşek bileşik nokta-marj yasasına sessizce düşürüyordu (`p=None` ile "geçti"). Düzeltme üç değerli (geçti/geçmedi/ölçülemedi) yapıldı, fail-closed, eşiklere dokunulmadı.
  Why: ayrım bilinçli — dilim YOKSA teyit mekanizması yürürlükte değildir ("olmayan sınavdan kalınmaz"); fail-closed yalnız "yasa yürürlükte, ölçüm yok" hâline biner. Geçmiş vaka H00029→v0003 (entry.w_prox None→0,15, 2026-07-20) retro-düzeltilmedi (tarihçe-koru).
  Ref: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md; v247-B ölçümü.

- **[TSK-027] 28i — sapma tek fold'dan gelmiyor, gelemez** — status: DONE(2026-08-24·holdout kuyruğu WP5-A 2D ile birleştirildi) · born: 2026-08-14 (28-serisinin diğer kalemleriyle aynı ölçüm turu) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle §8.H/B'de taşınmış durumda; burada yalnız kapanış izi kalıyor.
  Why: holdout kuyruğu birleştirmesiyle çözüldü.
  Ref: §8.H/B (taşındı 2026-08-30).

- **[TSK-028] renk rol-sızıntısının ölçülmemiş ikinci evi — WP8-D'ye taşındı** — status: DONE(2026-08-23·WP8-D'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP8-D'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-44 → WP8-D, 2026-08-23. eski: Ö-44.

- **[TSK-029] mutasyon kapsamı 39/79 — boşluk WP5'e sınıflandı, taslak hazır** — status: DONE(2026-09-03 gece · pyproject mutasyon seçimi 39→86 [47 davranışsal eklendi, 7 metin-tarayan gerekçeli dışarıda]; türetim inceleme tarafından bağımsız yeniden üretildi; İLK MUTASYON KOŞUMU ayrı pencere [saatler] — sonucu K defterine) · born: 2026-08-14 · owner: rol1 · size: S-M · trigger: —
  What: `pyproject.toml`ın kendi türetme kuralı 84 test modülü buluyor, `pytest_add_cli_args_test_selection` listesinde 39 var → boşluk 46 dosya (2026-08-14'te 41'di, İYİMSER çıkmıştı). Alt sınıf ölçüldü: ~19'u metin-tarayan (kaba grep, körce eklenemez — mutasyon skorunu şişirir), 1 fazlalık (`test_trend_shadow_v144`, beyanlı-zararsız). Taslak: davranışsal ~27 dosya listeye GİRER, ~19 metin-tarayan ADIYLA dışarıda bırakılır (pyproject şerhine liste eklenir), süre maliyeti ilk haftalık ritüelde ölçülür.
  Why: körlemesine eklenemez — kaynak-metni tarayan testler mutantı METİNLE öldürüp mutasyon skorunu şişirir; bu 2026-08-24 tasarım-kapanışıyla masa-başı karara bağlandı, ölçüm gerekmiyor.
  Ref: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md · docs/ELEME-WP5-2026-08-23.md #15. Kalan mini-iş hafta-1 partisinde. eski: Ö-41 · §4-41.

- **[TSK-030] çapa deseni ölçüldü — `dosya.py:SATIR` çapalarının %67'si `modül.sembol`e çevrilebilir** — status: DONE(2026-09-04 ölçüldü: kalan 0) · born: 2026-08-14 · owner: rol1 · size: M · trigger: —
  What: (HÜKÜM 2026-09-04 17:5xZ: ADIM-3 tamamlandı — meridian/tests/ops .py dosyalarında sentetik/mezar-taşı dışı `dosya.py:NNN` çapası 0 (grep, Rol-1); göç dilimleri TSK-119 (tests/ops 76), TSK-120 (api.py 7 + üçüncü besleme), TSK-129 (yorum sembol çapaları 102 → 0, aşama-2 ok'a bağlı), TSK-127 (RUNBOOK), TSK-080 (docs dünyası); çiviler v382/v401/v402/v373/v391 sıfır tolerans.) üç adım — (1) yeni çapalar `modül.sembol` olsun, (2) `codelaw`a genel `capa_uyusmasi()` tarayıcısı (DECLARED_* metinlerinden `mod.sembol` çıkarıp AST ile doğrular), (3) eski satır çapaları büyük-patlama göçü yerine çevresi düzenlendikçe dönüştürülür. Bu turda iki çapa (codelaw auth, sermaye→broker) tek tek sembolleştirildi. ADIM-2 İNDİ (2026-09-02 gece, TSK-094 ile): `codelaw.capa_uyusmasi()` iki beslemeli (DECLARED_* + ui/src), `report()`e `sembol_capalari`/`sembol_capa_curume` alanları, v373 20 çivi. SINIR (ölçüldü): tarayıcı sembolün VARLIĞINI doğrular, YERİNDELİĞİNİ doğrulayamaz — TSK-094 süpürmesinde 9 yanlış-ama-var eşleme tarayıcı yeşilken bulundu; adım-3 (kademeli göç + yorum-doğrulaması) açık kalır, tur-öncesi 116 eski sembol çapası yorum düzeyinde incelenmedi.
  Why: satır çapasının bayat olup olmadığı otomatik denetlenemiyor — sezgisel tarayıcı yanlış-pozitif üretti (`insider.py:281`); sembol çapası da çürür ama çürümesi SESLİ olur.
  Ref: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md — WP6'ya sınıflandı; `capa_uyusmasi` hâlâ yok (2026-08-23 ölçümü). eski: Ö-42 · §4-42.

- **[TSK-031] yanlışlanan iddianın üçüncü örneği veriye yazılmıştı — sermaye.py düzeltildi** — status: DONE(2026-08-23·ARŞİV, sermaye.py düzeltmesi + A17 çapası yerinde) · born: 2026-08-14 · owner: rol1 · size: — · trigger: —
  What: `sermaye.py:413-425` reset işaretinin `not` alanı artık-yanlış bir iddiayı ("eğrinin son noktası tohum sınırıdır") `state/`e YAZIYORDU; düzeltildi.
  Why: ders — beyanın koddan geri kalması taraması yalnız yorumlara değil, koda gömülü metin üreten yazımlara da uygulanmalı. Ayrıca `state/goal.yaml:130` çapası (`guard.py:352`, gerçek yer 440-443) bayat kaldı — `state/` yazımı yasak olduğu için rapor edildi, düzeltilmedi.
  Ref: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md; v246-A buldu. eski: Ö-43 · §4-43.

- **[TSK-032] kalibrasyon "hangi beyin ne kadar isabetli" — kapandı** — status: DONE(2026-08-24·`af8ca11`, `state/plan_atif.jsonl`) · born: 2026-08-24 (born tahmini: metinde yalnız kapanış tarihi var) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle §8.H/C'de taşınmış durumda; burada yalnız kapanış izi kalıyor.
  Why: kalibrasyon ölçümü commit `af8ca11` ile canlıya bağlandı.
  Ref: §8.H/C (taşındı 2026-08-30). eski: §4-39.

- **[TSK-033] `nous_eval` yeni künye alanlarını defterine taşımıyor — WP7'ye taşındı** — status: DONE(2026-08-23·WP7'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP7'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-40 → WP7, 2026-08-23. eski: Ö-40.

- **[TSK-034] Faz-6 kilidi meşru biçimde düşebilir — §5 [B-FAZ6-KILIT] altına taşındı** — status: DONE(2026-08-23·§5'e taşındı, operatör E-turu kararı 2/12) · born: 2026-08-14 · owner: rol1 · size: — · trigger: —
  What: gövde AYNEN §5 [B-FAZ6-KILIT] altında yaşıyor (bkz. TSK-043); burada yalnız taşıma izi kalıyor.
  Why: kalem operatör bilgilendirmesi sınıfına ait — B-FAZ6-KILIT ailesiyle birlikte tek yerden okunmalı (tek-kaynak yasası).
  Ref: taşındı: §5 [B-FAZ6-KILIT], 2026-08-23. eski: §4-36 · Ö-36.

- **[TSK-035] `seed_boundary` iki yolu farklı şey ölçüyor — sıra YOL-2>YOL-1'e çevrilmeli** — status: DONE(2026-09-04 c6b60b6 suite #18; canlıya dağıtım #14 ile) · born: 2026-08-14 · owner: rol1 · size: S · trigger: —
  What: (CANLI dağıtım #14 2026-09-04 22:08Z f8d7d6d: /api/performance tohum_siniri replay_end 2026-07-24 kaynak trades.kaynak guven ORTA yollar_ayrisik TRUE (reset 07-20 ≠ damga 07-24) — 887/887 varsayımı 'iki yol aynı tarih' DEĞİLDİ; ayrışma artık panoda beyanlı; sınır tarihi eğri serisinde yok → i None, grafikte konumlanamıyor (beyanlı 'normal', kod şerhi) → [TSK-139].) (HÜKÜM 2026-09-04 c6b60b6: sıra YOL-2 (damga, doğrudan ölçüm) > YOL-1 (reset işareti, çapraz-sağlama); `yollar_ayrisik` aynen; R1 hükmü: KAYNAK_DAMGA kazanınca guven 'yuksek' ancak reset işareti aynı tarihi doğrularsa, aksi 'orta' — canlı etiket düşmesin; v411 9 test, mutasyon 3+2 öttü; sıra sonucu 6 mevcut test değeri (v140/v264/v245) güncellendi; suite #18 10349/0. D2 CANLI ÖLÇÜM 2026-09-04 21:3xZ (A1 meridian.db `trades`, salt-okunur SQL): 901 satır = 885 replay_seed + 16 live_paper, damgasız/belirsiz 0; replay_seed en geç ts_close 2026-07-24, live_paper 2026-08-07…2026-09-04 → YOL-2 sınırı 2026-07-24; geri-açılış şartı (damgasız > 0) SAĞLANMIYOR, kalem kapalı. Not: 2026-08-14 ölçümü 887/887 idi, bugün 885 tohum — iki satır fark ölçülmedi (ledger yeniden yazımı/emeklilik olabilir; ayrı soru).) sınırın sözleşmedeki anlamı "tohum defteri nerede biter"dir ve bunun doğrudan ölçümü YOL-2'dir (`replay_seed` damgalı satırların en geç `ts_close`u) — donmuşluk şartını da sağlar. Öneri: sıra YOL-2 > YOL-1'e çevrilir, YOL-1 çapraz-sağlama olarak kalır, `yollar_ayrisik` bayrağı aynen korunur; değişiklik davranış-nötrlüğü (damgasız satır sayısı 0) tek satırlık ölçümle kayda geçirilir. Geri-açılış şartı: damgasız satır >0 çıkarsa kapanış geri açılır.
  Why: onarım sonrası sınır iki kaynaktan okunabiliyor ve ayrışıyordu (YOL-1: 2026-07-20, YOL-2: 2026-07-24) — bugün etkisiz (887/887 damgalı) ama ayrışma `yollar_ayrisik: true` ile GÖRÜNÜR. Ölçülemeyen: canlı `trades` damga sayımı = None (SQLite arka ucu, canlıda sqlite3 CLI yok; son ölçüm 2026-08-14 = 887/887).
  Ref: v264 tekilleştirmesi (`ledgerstamp.seed_boundary`, `api.py:2487`, `ledgerstamp.py:306-345`); docs/ELEME-WP4-HAVUZ-2026-08-23.md §B3; 2026-08-24 tasarım-kapanışı. eski: Ö-37 · §4-37.

- **[TSK-036] iki modül yorumu artık yanlış — WP6-E'ye taşındı** — status: DONE(2026-08-23·WP6-E'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP6-E'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-38 → WP6-E, 2026-08-23. eski: Ö-38.

- **[TSK-037] 15g turunun devrettiği iki kalem — ikiye bölünüp WP5-G ve WP11-G'ye taşındı** — status: DONE(2026-08-23·WP5-G + WP11-G'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde iki yarıya bölünmüş biçimde WP5-G (a) ve WP11-G (b)'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-35a → WP5-G + §4-35b → WP11-G, 2026-08-23. eski: Ö-35.

- **[TSK-038] kayan oturumun iki sessiz sürüklenmesi — WP6-E'ye taşındı** — status: DONE(2026-08-23·WP6-E'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP6-E'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-34 → WP6-E, 2026-08-23. eski: Ö-34.

- **[TSK-039] `active_model()` künye kusurunun ikinci evi + uydurma koruması eksiği — WP7'ye taşındı** — status: DONE(2026-08-23·WP7'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP7'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-31 → WP7, 2026-08-23. eski: Ö-31.

- **[TSK-040] suite'in içinden gerçek ağ çağrısı — ölçüldü, WP5-G'ye taşındı** — status: DONE(2026-08-23·WP5-G'ye taşındı) · born: 2026-08-23 (born tahmini: orijinal tarih bu iz satırında yok, taşıma tarihi kullanıldı) · owner: rol1 · size: — · trigger: —
  What: gövde tam metniyle WP5-G'de yaşıyor; burada yalnız taşıma izi kalıyor.
  Why: havuzun kendi kuralı — sahipli kalem ilk fırsatta WP'sine taşınır.
  Ref: taşındı: §4-32 → WP5-G, 2026-08-23. eski: Ö-32.

- **[TSK-041] kardeş ajan pytest çakışması — orkestrasyon dersi kurumsallaştı** — status: DONE(2026-08-23·CLAUDE.md §6 + hafıza + hermes.py) · born: 2026-08-14 · owner: rol1 · size: — · trigger: —
  What: aynı checkout'ta iki ajan eşzamanlı `pytest` koşarken `_no_live_state_writes` bekçisi ERROR verdi; izole yeniden koşum 10 passed/0 error — kırmızı koddan değil PARALEL koşumdan doğdu.
  Why: kural kurumsallaştı — otoriter tam suite koşarken hiçbir ajan test koşmamalı; dosya-ayrıklığı YETMEZ, `state/` paylaşımlı.
  Ref: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md; `hermes.py:410-419`. eski: Ö-33 · §4-33.

- **[TSK-042] ayrılmaz çiftin iki yarısı farklı yedek davranışında — WP2 kapanışında çözüldü** — status: DONE(2026-08-23·BAYAT, config.py yedek 0,5 + BEKLENEN_BOYUT çivisi, WP2 kapanışında çözülmüş) · born: 2026-08-14 · owner: rol1 · size: S · trigger: —
  What: `goal.yaml`ın beyan ettiği "AYRILMAZ" çift (`max_open_positions: 20` + `position_size_r: 0.5`) iki ayrı dosyada ve iki ayrı yedek davranışındaydı — `strategy.yaml` bozulursa `config.strategy()` sessizce `default_strategy()`e düşüyordu (orada `position_size_r: 1.0`). Seviye düzeltmesi: bu bir toplam-risk patlaması değil, portföy ŞEKLİ değişimiydi (`heat_hard_r` yine bağlıyordu).
  Why: sessiz olan yedeğin DEĞERİYDİ (`strategy_file_unusable` uyarısı zaten basılıyordu); WP2 kapanışında `config.py:364` yedek 0,5'e çekilip BEKLENEN_BOYUT çivisiyle kapatıldı.
  Ref: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md; WP6-26 turunun devrettiği kalem. eski: Ö-30 · §4-30.
- **[TSK-086] İnfra-simetri pano okuyucusu** — status: DONE(2026-09-01 — 88688ba + fix turu; v354 19 çivi, üç durum ayrık [boş/null/dolu], `beklenmedik_olcum.komut` dahil; SDD tam döngü, re-review 9/9) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: `/api/infra.beklenmedik_birimler` alanına pano yüzeyinde okuyucu (Altyapı kartına "beklenmedik birim" rozeti + listesi) — Yasa 6 borcunu kapatır: alan 2026-09-01 gecesinden beri yayında, tests-dışı okuyucusu yok (bacağı indiren ajanın kendi açık-kalem beyanı).
  Why: ayna körlüğü bacağı gece indi (gerçek vaka: A1'de repo-dışı inactive `meridian-dash.service` artık ölçülüyor); okuyucu olmadan işaret operatöre ulaşmaz. Not: /api/infra zaman tavanı 6,5 sn'e büyüdü (8 sn TTL) — UI bağlanırken gecikme gözlenirse ölçülür.
  Ref: tests/test_pano_altyapi_v287.py çivileri · gece kapanış raporu 2026-09-01.
- **[TSK-087] Geri-dolum işçi-çökmesi dayanıklılığı** — status: DONE(2026-09-03 gece · geridolum.py çöken gün aynı koşumda bir kez yeniden denenir, öteki işçi kesilmez, ikinci çöküşte KIRMIZI + bedel özeti [geçti/geçildi ayrı sayaç]; v377 13 çivi, 5+2 mutasyon; canlıya kuruldu) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: `deploy/oracle-a1/geridolum.py` — tek işçinin çökmesi tüm koşumu KIRMIZI'ya düşürmesin: çöken gün koşum-içi BİR kez yeniden denensin; ikinci çöküşte koşum yine KIRMIZI (pano-görünürlük korunur, sessizleşme yok — bedel yasası: kaybedilen görünürlük ölçülüp beyan edilir).
  Why: 2026-09-01 gecesi iki vaka — 08-31 sözlük boşlukları (kalıcı sınıf, ayrıca düzeltildi) ve 08-05 EOFError (kesik gzip, GEÇİCİ sınıf): geçici arızada tüm koşumun düşmesi diğer işçinin bitmiş işini yarıda bıraktı ve saatlik timer'a kadar bekletti. Operatör onayı 2026-09-01 sabah ("havuza yaz").
  Ref: gece kapanış raporu 2026-09-01 · 136ceb4 · 7b35888.
- **[TSK-088] Model kayıt bileşeni — LLM seçimi/rota/sağlık tek kaynakta** — status: DONE(2026-09-01·hüküm: tek-kapı APISIX — ardıl TSK-089/TSK-090) · born: 2026-09-01 · owner: rol1 · size: M · trigger: —
  What: motor-içi `model_kayit` modülü: rol→model-zinciri tablosu (danışma · review · bot profilleri · Hindsight) + model kartı (kimlik, sağlayıcı-rotası, ücretsiz-mi, bilinen-ölü/alias) TEK kaynakta; sağlık görüşü YENİ ölçüm değil mevcut telemetrinin okuyucusu (`agent_calls.jsonl` dolu-oranı); pano `/api/models` yüzeyi (rol→zincir + son-N-gün dolu-oranı + ölü-ad göç sayacı); sırlarda yalnız API ANAHTARLARI kalır, model SEÇİMİ sır deposundan çıkar (geçiş dönemi: mevcut sır-override'ları öncelik-beyanlı okunmaya devam eder + ayrışma çivisi).
  Why: ölçüm 2026-09-01 — model kararı ≥9 dosyada / 4 mekanizma sınıfında yaşıyor (hermes.py 34 atıf: zincir+ölü-ad+rota+cooldown · secrets 3 MODEL anahtarı · 4 hermes config.yaml · watchdog/spend/api okuyucuları) ve üç vaka aynı köke iniyor: 2026-08-13 iki-katman (config göçtü, sır katmanı açık kaldı) · tencent/hy3 419 sessiz-boş · 2026-09-01 canary (Gemma rota-model uyumsuzluğu elle keşfedildi). Harici gateway DEĞERLENDİRMESİ (operatör talebi 2026-09-01; web taraması + yerleşik keşif): yerleşikler LLM-gateway DEĞİL (`hermes gateway`=mesajlaşma köprüsü, `hermes proxy`=tek-sağlayıcı OAuth iletici, zincir/kota yok); yönetilen sınıf (Portkey-cloud/Cloudflare-AI-GW/Inworld) SIR İLKESİYLE ELENDİ (istem+anahtar üçüncü tarafa çıkar); öz-barındırılan iki gerçek aday: LiteLLM (Python, en zengin: retry/cooldown/fallback/budget/virtual-key; fallback STATİK config) ve Bifrost (Go tek-ikili, hafif, ARM-uyumlu). Meridian'a bugünkü fayda/bedel: hacim ~43 çağrı/gün (1071/25g) ve TEK tüketici (hermes sarmalayıcı); zincir+cooldown+kota-imzası KODDA ÇALIŞIYOR ve çivili; telemetri defterimiz karar yüzeyi — gateway ikinci bir metrik gerçek-kaynağı + yeni canlı birim ('kurulu≠çalışır' sınıfı) + config-sürüklenme yüzeyi (F9 sınıfı) getirir, kazancı (tek uç, merkezi kota) bugün büyük ölçüde bizde var. HÜKÜM ÖNERİSİ: red değil TETİKLİ ERTELEME — gateway şu tetiklerden biri doğunca kurulur: (a) hermes-dışı 2. LLM tüketicisi doğarsa · (b) çağrı hacmi/kota yönetimi elle taşınamazsa · (c) TSK-088 kayıt bileşeni rota ihtiyacına yetmezse; o gün aday BİFROST (hafif, tek ikili) — pilot yalnız OpenRouter önünde, ölçümle. KONG özel değerlendirmesi (operatör sezgisi 2026-09-01, web doğrulaması): ihtiyacın KALBİ olan model-zinciri fallback + yük dengeleme `AI Proxy Advanced` eklentisinde ve o ENTERPRISE (ücretli) — OSS `ai-proxy` çok-sağlayıcı iletim verir ama zincir-fallback vermez; ücretsiz kısıtıyla çelişir. Kong, zaten çok-servisli bir API kapısı işletiliyorsa parlar; bizde tek tüketici + localhost var. Kong ancak Enterprise bedeli bilinçli kabul edilirse ya da genel API-kapısı ihtiyacı doğarsa masaya döner. LiteLLM DERİN İNCELEME (operatör talebi 2026-09-01): OSS seti ihtiyacımızı KAPSIYOR (temel fallback/yük-dengeleme/tek-uç; Enterprise=SSO/RBAC/audit — gereksiz). Saha bedelleri: ~350-400MB RSS + eşzamanlılıkta bilinen bellek sızıntısı (MemoryMax şart) · minor sürümde kırılma alışkanlığı (sıkı pin şart) · tedarik-zinciri saldırı geçmişi (Cycode vakası; uv audit kapımız anlamlı) · DB'li+config'li karışık modda bilinen hata — istikrarlı yol DB'siz config-dosyası modu (bizim dagit disiplinimizle uyumlu). ZAMANLAMA: LiteLLM sıcak-yolu Rust'a taşıyor (beyan: 11x az bellek) — benimseme Rust hattı oturduktan SONRA bedelsizleşir. ENTEGRASYON TASARIMI HAZIR ve geri-alınabilir: NOUS_ENDPOINT (ALLOWED sırda) → http://127.0.0.1:<port>/v1 + NOUS_MODEL=alias → Meridian kodu SIFIR değişiklik. YAN KEŞİF: hermes CLI'nin YERLEŞİK sağlayıcı-fallback zinciri var (`hermes fallback` — rate-limit/overload/bağlantı hatasında sırayla dener); bugünkü ihtiyacın bir kısmı CLI'de bile mevcut, ama config-katmanı 2026-08-13 iki-katman dersine tabidir (kullanılacaksa tek-kaynak kayıttan beslenmeli). PİLOT PLANI (operatör isterse): DB'siz config modu, ayrı venv + pin, systemd MemoryMax=512M, yalnız danışma rotası, 1 hafta ölçüm (RSS/sızıntı · eklenen gecikme · fallback davranışı) → karar. DOKÜMAN İNCELEMESİ 2026-09-01 (docker_quick_start + reliability): (1) FALLBACK TAM DB'SİZ — router_settings.fallbacks + litellm_settings{num_retries·allowed_fails·cooldown_time·request_timeout} config-dosyası tabanlı; fallback tetiği '429 + 5xx + timeout dahil kalan tüm hatalar' (ihtiyacın kalbi ücretsiz VE DB'siz kanıtlandı). (2) DB (Postgres) YALNIZ virtual-key/bütçe/harcama-takibi için — mekanik kota zorlaması istenirse DB'li moda geçilir (A1'de PG17 hazır; karışık DB+config modu bilinen-hatalı, ayrım net tutulur). (3) A1 uyarlamaları: Docker DEĞİL pip-native (`litellm[proxy]`, uv venv + pin — quickstart'ın curl|docker-compose deseni tedarik-zinciri disiplinine aykırı, imaj/paket pin'lenir); 127.0.0.1 bind; güçlü LITELLM_MASTER_KEY + LITELLM_SALT_KEY (systemd credential yolu, quickstart'ın sk-1234'ü asla); admin UI kapalı/erişimsiz. (4) ÇİFT-RETRY UYARISI: hermes CLI 3 deneme × litellm num_retries çarpışır — pilotta litellm num_retries=1 tutulur, zincir/cooldown tek katmanda (litellm) toplanır ki telemetri okunabilir kalsın. (5) KAPSAM HÜKMÜ (operatör sorusu 2026-09-01: 'bütün API bağlantılarını buraya alabilir miyiz — FMP, Massive?'): HAYIR — LiteLLM yalnız LLM protokolü (OpenAI-uyumlu chat/embedding) konuşur; FMP/Alpaca/NASDAQ/EDGAR/IEX veri REST API'leri oradan GEÇEMEZ (sınıf farkı — genel API-kapısı Kong-OSS/Envoy sınıfıdır). Massive ayrıca motorun bağlantısı değil, Claude oturum aracıdır. Veri API'lerini genel bir egress-kapısına almak BUGÜN önerilmez: adapter katmanı vakalarla olgun (FMP 402≠429 rotasyonu vb.) ve tek proxy = tüm veri kaynakları için TEK ARIZA NOKTASI (canlı ticaret kalbi; LLM danışmasının aksine düşmesi seans kaybettirir). ORTA YOL — bu maddenin kapsam genişlemesi olarak: model_kayit bileşeni 'dış-servis kayıt defteri'ne genellenebilir (LLM + veri sağlayıcıları: kimlik · anahtar-adı · kota · sağlık TEK kayıtta, TRAFİK PROXYLENMEZ) — yönetişim merkezileşir, arıza yarıçapı büyümez. Operatör sorusu 2026-09-01: "backendde halleden bir bileşen olabilir mi?" NİHAİ HÜKÜM (operatör onayı 2026-09-01, tam doküman taraması sonrası): TEK KAPI = Apache APISIX — LLM rotası (ai-proxy-multi zinciri) + veri API egress + pano ingress + bot consumer'ları tek bileşende; dört faz ve 9 canary TSK-089'da, pano yüzeyi TSK-090'da. LiteLLM pilotu SUPERSEDED (iki taslak dosya commit'lenmeden geri çekildi); Kong tedarik-zinciri gerekçesiyle kapandı (OSS imaj hattı 3.10'da kesildi, sürüm hattı 3.9.x bakım-modunda; öz-derleme değerlendirildi — teknik olarak mümkün, stratejik olarak reddedildi: yazılı OSS yama taahhüdü yok). Motor-içi model_kayit ihtiyacı kapı konfigürasyonuna devrildi (routes.yaml SSoT) — madde bu hükümle kapandı.
  Ref: TSK-020 (backend mimari kararları — bu madde o dizinin 10. kalemi olarak da sıralanabilir) · TSK-047 canary kaydı · ardıl: TSK-089, TSK-090.

## §5 OPERATÖR BLOKLARI (karar/aksiyon/kimlik/para/bakım-penceresi operatörde) _(eski: §3)_

### §5.0 OPERATÖR MASASI — konsolide işaret defteri (2026-08-31)

_**BU TABLO KALEM TAŞIMAZ** — beş kovaya dağılmış operatör işlerinin TEK bakışta dizini. Satırlar durum rozeti taşımaz (rozetli asıl satırlar işaret ettikleri yerde; kopya rozet sessizce ayrışırdı — tek-kaynak). `/api/roadmap` bu satırları `belirsiz` sayar ve **bu doğrudur**._

| Kalem | Ne istiyor | Asıl kayıt |
|---|---|---|
| ~~Bot kurulumları (sef · bekci · karne)~~ | ✓ TAMAMLANDI 2026-08-31 (operatör koştu, Rol-1 kanıtladı — üç birim + timer active, üç test-ateşleme status=0) | kanıt: `§2` H1 roster satırı + §7 |
| hermes `SOUL.md` + `config.yaml` | elle kurulum + bakım penceresi (dagit taşımaz; F9 AYRIK ölçüyor) | F9 raporu + `deploy/hermes/` |
| `B-FINVIZ-TOKEN` | Finviz Elite anahtarı ya da delist-bar kaynak kararı | `§5` kimlik tablosu satırı |
| `B-FMP-PLAN` | FMP plan kararı (250 çağrı/gün ↔ 251 sembol yapısal uyumsuzluğu) | `§5` kimlik tablosu satırı |
| `B-QC-LOGIN` | `lean login` + makine kurulumu (dotnet/docker) | `§2` C2-4 LEAN satırı |
| `B-AJAN-GIT` | ajan git yetkisi kararı | `§5` kimlik tablosu satırı |
| Faz-6 beş kilit | kanıt-şartlı kilitler — açılış kararları; KANIT bacağı plana alındı 2026-08-31 akşam, ONAY masada | `§2` askıda satırı + WP3 |
| Sırlar (mimari madde 7) | kademeli YOL-1 plana alındı 2026-08-31 akşam; OpenBao/unseal adımı operatörde | `§4` mimari bloğu BEKLEMEDE-7 |
| PIT mid-cap üst-sınır | sağ-kalan üst-sınır ölçümü plana alındı 2026-08-31 akşam (kart-önce); veri-kapısı kararı masada | `§2` askıda satırı |

_2026-08-31 akşam: operatör kararıyla FINVIZ/FMP/QC üçlüsü (+delist-kaynak para ailesi) DIŞINDAKİ
masa kalemleri İCRA SIRASI'na alındı — dizin satırları yerinde, icra işaretleri İCRA SIRASI'nda._

**KİMLİK TABLOSU (2026-08-23 — tahta gerekçesi: "kimlik konumdan ayrılmalı"; her blok başlığının
önüne `**[B-…]**` kondu; aynı konu §5'te birden çok konumda yaşıyorsa — kova bloğu + numaralı
envanter — hepsi AYNI kimliği taşır. Kimlikler kalıcıdır; blok kapansa da kimlik yeniden kullanılmaz.):**

| kimlik | tek-cümle konu | beklediği şey (karar/anahtar/pencere) |
|---|---|---|
| ✅ KAPALI · `B-RUNBOOK-KAPSAM` | RUNBOOK üreticisinin onaylı betik kümesine `dagit.sh` eklensin mi (sürüm-terfisi sözleşmesi belgeye girsin diye; emsal: seçenek-C genişlemesi operatör onaylıydı) | operatör kararı (evet/hayır — tek satır BETIK_KUMESI değişikliği) |
| ✅ KAPALI · `B-PENCERE-KAYDIR` | canlı tarama/emir penceresinin ~13:45 UTC'ye kaydırılması (23e; `EDG-2026-047` Ö1 ateşledi: risk −%42, bedel medyan +4,65 bps) | operatör kararı — strateji-kimliği değişikliği; EVET derse kart-önce uygulanır |
| ✅ KAPALI · `B-CHOP-BUTCE` | chop bütçe-kapalılığı: kasıtlı politika mı (A) yan etki mi (B) — brief `docs/KARAR-BRIEF-CHOP-BUTCE-2026-08-22.md`; Rol-1 tavsiyesi: üçüncü yol (@chop üretimini kes + 'chop tabanı kartıyla açılır' notu) | operatör kararı (A / B / üçüncü yol) |
| ✅ KAPALI · `B-KORUMA-KUR` | çıplak motor pozisyonlarının korumasının panodan `koruma_kur` ile yeniden kurulması (KOVA-1/A1) | operatör icrası (tek oturum) — tahta 2026-08-22: ölçümle kapandı (korumasız 0/7), blok tarihçe |
| ✅ KAPALI · `B-BILDIRIM-N1` | Telegram/webhook bildirim kanalı kimliği (KOVA-1/A2 · envanter-2 · OB-1) | kanal anahtarı — ✅ kapandı 2026-08-22, Telegram canlı |
| ✅ KAPALI · `B-PULLBACK-SILAH` | pullback ailesi `ARMED_SETUPS`ten çıksın mı (KOVA-2/B1) | karar — ✅ verildi 2026-08-22 (A: silahsızlandırıldı); dağıtım 043 sonrası suite'le |
| ✅ KAPALI · `B-KORUMA-POLITIKA` | koruma yeniden-kurulumunun kalıcı politikası (KOVA-2/B2) | karar — ✅ verildi 2026-08-17 (c); teslim bacağı `B-BILDIRIM-N1` |
| ✅ KAPALI · `B-E1-LIMIT` | E1 limit bacağı canlıda açılsın mı (KOVA-2/B4) | karar — ✅ verildi 2026-08-22 (A+C: kapalı kalır); açık argüman `EDG-2026-043`te |
| ✅ KAPALI · `B-FAZ6-HUKUM` | Faz-6 `sonuc_hukmu` yapısal kapalılığı (KOVA-2/B3) | hiçbir şey — karar değil, bilgi |
| 🔴 AÇIK · `B-FINVIZ-TOKEN` | FINVIZ Elite token satın alınsın mı (KOVA-3/C1 · envanter-8) | para kararı (WP11-D uzlaştırması çözülmeden "kesinlikle gereksiz" denemez) |
| 🔴 AÇIK · `B-FMP-PLAN` | FMP plan/kota yükseltmesi — Y4 penceresi (KOVA-3/C2 · envanter-3 + envanter-7) | para kararı |
| 🔴 AÇIK · `B-QC-LOGIN` | QC kimliği (`lean login` ya da dotnet-engine kararı) + FREE defterin koşulması (KOVA-3/C3 · yeni-blok C2-4 · envanter-11) | anahtar/kimlik + operatör koşumu |
| ✅ KAPALI · `B-NOUS-BEYIN` | NOUS_MODEL / beyin çeşitliliği — danışma yolu ölü mü (KOVA-3/C4 · envanter-1) | ✅ kapandı 2026-09-03 00:17 UTC (Rol-1 ölçümü, A1-içi): motor zinciri NOUS_ENDPOINT=kapı `/llm/v1` + NOUS_MODEL nemotron:free + KAPI_APIKEY; `/llm/v1/models` 200 (sayaç, motor_meridian) ve gerçek chat canary kapıdan **200** (provider Nvidia, 28 token) — yol DİRİ; "ölü" teşhisi ücretsiz tavan dolu pencerelerinde 502 görmekten kaynaklanıyordu (B-TAVAN-502 politikası) |
| ✅ KAPALI · `B-SYSTEMD-143` | systemd `SuccessExitStatus=143` (OB-2) | ✅ yapıldı 2026-08-09 — tarihçe |
| ✅ KAPALI · `B-DASH-CRED` | DASH-TOKEN LoadCredential faz-1 etkinleştirme | bakım penceresi |
| 🔴 AÇIK · `B-AJAN-GIT` | ajan-git mekanik kapısı (PATH-shim/wrapper) | ~~süreç/araç kararı~~ KARAR VERİLDİ 2026-08-31 akşam (masa→plan taşıması): icra İCRA SIRASI ①'de, Rol-1 — kimlik araç inince kapanır |
| ✅ KAPALI · `B-ORACLE-TASIMA` | Oracle sunucu taşıma (envanter-4; Faz-6 ön şartı) | operatör aksiyonu/pencere |
| 🔴 AÇIK · `B-FAZ6-KILIT` | Faz-6 kapısı: beş kilit dolunca INTRADAY_ARM + emir bacağı onayı (envanter-5) | onay (kanıt-şartlı) |
- **[TSK-043] Faz-6 kilidi meşru biçimde düşebilir — kadanslı yazarın yan etkisi** — status: GATED(dağıtımdan sonra `edge_verdict` çıktısının okunması) · born: 2026-08-14 · owner: rol1 · size: S · trigger: dağıtım sonrası ölçüm (bu turda cloud klonundan ÖLÇÜLEMEDİ)
  What: `equity_curve` kadanslı yazarı devreye girince `analytics._realized_drawdown`ın m2m bacağı körlükten çıkıyor — `m2m_durum` "donem_disi"→"olculdu", `max_dd_alt_sinir` False oluyor; ajanın ölçtüğü %8,04, `EDGE_MAXDD_MAX=0,08`i kıl payı aşıyor → dağıtımdan sonra bir Faz-6 kilidi düşebilir.
  Why: BU BİR ARIZA DEĞİL, KAPININ ÇALIŞMASIDIR — hiçbir eşiğe dokunulmadı, sistem ilk kez ölçebildiği bir şeyi ölçüyor (EDG-037 `RESULT_PF_MIN` emsali: "kilidin kapalı kalması ARIZA DEĞİL KORUMA"). Operatör bilgilendirmesi sınıfı — B-FAZ6-KILIT ailesi.
  Ref: v245-D ölçümü; sahibi WP5/WP2; §4-36'dan taşındı 2026-08-23 (operatör E-turu kararı 2/12). eski: §4-36 · Ö-36.

| 🔴 AÇIK · `B-AJAN-TAVAN` | ajan tavanı 15 (envanter-6) | karar (mevcut değer: 15) |
| 🔴 AÇIK · `B-DELIST-KAYNAK` | Massive/QC delist-bar kaynağı kararı (envanter-9) | karar + para (QC platform-içi VEYA Massive plan) |
| ✅ KAPALI · `B-OCI-BUCKET` | OCI Object Storage bucket + S3-uyumlu anahtar — Litestream aşama-2 (envanter-10) | hesap/anahtar |
| ✅ KAPALI · `B-DD-ESIK` | `goal.max_drawdown` ↔ ölçülen dd gerilimi (envanter-12) | ✅ çözüldü 2026-08-13 (0,16) — tarihçe |
| ✅ KAPALI · `B-TAVAN-502` | hepsi-ücretsiz kararının bedeli: OpenRouter günlük ücretsiz-model tavanı dolunca kapı zinciri 502 döner, botlar o koşumu boş geçer | ✅ karar 2026-09-02 akşam (A): olduğu gibi kalır — 502 bilinçli ve sayaçta görünür, sabah bütçesiyle düzelir; "sessiz atla" varyantı bedel ölçümü istediği için AÇILMADI |
| ✅ KAPALI · `B-PG-ROTASYON` | Hindsight Postgres parolası 2026-09-02'de Rol-1 terminaline düştü (DATABASE_URL süzgeç kaçağı; DB yalnız 127.0.0.1) | ✅ karar (A) + icra 2026-09-02 18:08 UTC (operatör tek-satırı): ALTER USER + .env + restart; kanıt (Rol-1, A1): eski parola reddedildi, yeni `select 1` = 1, yedek birimi `User=postgres` (peer, etkilenmez), health 200 |
**[2026-08-30 KİMLİK DENETİMİ — 22 kimliğin 14'ü KAPALI, 7'si AÇIK, 1'i DOĞRULANAMADI.]**
Rozetler yukarıdaki tabloya işlendi (satır metinleri korundu, başına durum kondu). Kapalı
sayılanların kanıtı — hepsi **bu depoda** doğrulandı, canlı gerektiren üçü ayrıca işaretlidir:

| kimlik | kapanış kanıtı (2026-08-30'da yeniden okundu) |
|---|---|
| ✅ `B-RUNBOOK-KAPSAM` | `ops/runbook_uret.py` `BETIK_KUMESI` üçlüsünde `dagit.sh` VAR (K4 "Evet" uygulanmış) |
| ✅ `B-PENCERE-KAYDIR` | `meridian/barclock.py` `ENTRY_WINDOW_ET_MIN = 9*60+45` — yorumu "EXE-2026-009 + K2" diyor |
| ✅ `B-CHOP-BUTCE` | `meridian/config.py` `URETIMI_DURAKLATILAN_REJIMLER = ("chop",)` + `hermes.py` fail-closed bacağı (K1 · `EDG-2026-048` NO-GO) |
| ✅ `B-KORUMA-KUR` | 2026-08-22 ölçümüyle kapandı (gövde `§8.O`/A; "4 pozisyon çıplak" 08-07/09 penceresinin durumuydu) |
| ✅ `B-BILDIRIM-N1` | 2026-08-22 — Telegram kanalı canlı (§7 kaydı) |
| ✅ `B-PULLBACK-SILAH` | karar 2026-08-22 (A: silahsızlandırıldı); **dağıtım kuyruğu AÇIK** — tahtada DİK DURUM satırı olarak duruyor |
| ✅ `B-KORUMA-POLITIKA` | operatör kararı 2026-08-17 (c) |
| ✅ `B-E1-LIMIT` | operatör kararı 2026-08-22 (A+C: kapalı kalır) |
| ✅ `B-FAZ6-HUKUM` | karar değil BİLGİ — operatörden hiçbir şey beklenmiyor (kartın kendi beyanı) |
| ✅ `B-SYSTEMD-143` | 2026-08-09 yapıldı (tarihçe) |
| ✅ `B-DASH-CRED` | depo tarafı: `deploy/oracle-a1/dash_token_credential.sh` + `…/10-sertlestirme-faz1.conf` VAR. **Faz-2'nin canlıda etkin olduğu bu turda ÖLÇÜLEMEDİ** (cloud klonu) — 2026-08-24 denetiminin "iki faz da canlı" hükmüne dayanıyor |
| ✅ `B-ORACLE-TASIMA` | taşıma 2026-07-30'da yapıldı; sistem A1'de koşuyor (CLAUDE.md + mühendislik günlüğü sistem haritası) |
| ✅ `B-OCI-BUCKET` | depo tarafı: `deploy/oracle-a1/litestream_kur.sh` + `meridian-aylik-bucket-kopya.service` VAR. **Replica'nın canlıda aktığı ÖLÇÜLEMEDİ** (cloud klonu) |
| ✅ `B-DD-ESIK` | 2026-08-13'te çözüldü (0,16) — tarihçe |

**`B-NOUS-BEYIN` bilerek KAPALI SAYILMADI:** 2026-08-24 denetimi onu BAYAT-KAPALI listesine
koydu, ama kapanışı "danışma yolu canlıda diri mi" sorusuna bağlı ve bu **cloud klonundan
ölçülemez**. Kimlik tablosunun kendi şerhi zaten "kapanmış olabilir — Rol-1 doğrulasın" diyordu;
o şerh 2026-08-30'da hâlâ geçerlidir. Ölçmeden kapatmak, bu deponun tam da düzeltmeye çalıştığı
`bayat-beyan` sınıfını TERS yönde üretirdi.

### 🔴 BENDEN BEKLENENLER — ÜÇ KOVA (2026-08-13; operatör talebi: "benden beklediklerini ayrıca belirt")

Her kalemde dört satır: **ne bekleniyor · neden · beklerken oluşan bedel · bağımlı kalemler.**
Kaynak: `docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md` §F + §H-17..21. Aşağıdaki **numaralı envanter
(1-12) AYNEN duruyor** — bu üç kova o listeyi silmez, ÖNCELİKLENDİRİR ve "ne bekleniyor"u açık yazar.

#### KOVA 1 — ACİL (bugün bir bedel ödeniyor)

**[2026-08-30 ÖLÇÜMÜ — KOVA 1 BOŞ.]** İki kalemin ikisi de kapandı: `A1` `[B-KORUMA-KUR]`
koruma yeniden-kurulumu (2026-08-22, ölçümle) · `A2` `[B-BILDIRIM-N1]` bildirim kanalı
(2026-08-22, Telegram canlı). Gövdeleri tam metniyle `§8.O`/A'da. **Bugün operatörden ACİL
bir şey beklenmiyor.**

#### KOVA 2 — KARAR BEKLEYEN

**[2026-08-30 ÖLÇÜMÜ — 2026-08-13'te açılan DÖRT kalem de KAPANDI.]** `B1` pullback
silahsızlanması (karar 2026-08-22: A) · `B2` koruma politikası (karar 2026-08-17: c) · `B4` E1
limit bacağı (karar 2026-08-22: A+C) · `B3` Faz-6 `sonuc_hukmu` (karar değil bilgiydi).
Gövdeleri tam metniyle `§8.O`/B'de.

**AMA KOVA BOŞ DEĞİL — 2026-08-29/30'da İKİ YENİ KARAR DOĞDU ve hiçbir bölüme işlenmemişti
(bu turda eklendi; kalıcı `B-…` kimliğini Rol-1 atar):**

| kalem | kaynak | operatörden beklenen |
|---|---|---|
| ✅ **KARAR VERİLDİ 2026-08-31 · `EXE-2026-009` P-2 — kontrol kolu yapısal olarak BOŞ, öneri tetiği inşaen erişilemez** _(kimlik ATANMADI)_ | kart `EXE-2026-009` bloğu `acik_kalemler_2026_08_29`; ölçüm `research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/` | tetiğin kıyas tabanı: **(a)** damgasız kaydırma-öncesi küme AYRI+BEYANLI taban mı (kart revizyonu, kill#2'ye dikkat) · **(b)** A/B için pencere dönüşümlü mü koşsun · **(c)** tetik tek-kollu eşiğe mi bağlansın. Üçü de KART İŞİDİR; ölçüm başladıktan sonra eşiği kodda değiştirmek kill#2'yi tetikler → ✅ **KARAR 2026-08-31 (operatör, 85-aktarımı): kalem Rol-1'e DEVREDİLDİ** — (a)/(b)/(c) seçenekleri P-3 ölçümüyle AŞILDI: yol `ts` anahtarı (P-3 emsali; kontrol n=15 eşiği geçer, tedavi ~4 hf). Kill#3 çerçevesi kart revizyonu ister; icra kaydı §2 TAHTA satırında |
| ✅ **KARAR VERİLDİ 2026-08-31 · `EDG-2026-042` P-3 — K1 karışık örneklem** _(operatör: AYRIK/`ts`, ara işaret yok; kayıt Ö-54 satırı + kart bloğu `p3_karar_ayrik_ts_2026_08_31` + `docs/KARAR-P3-K1-AYRIK-TS-2026-08-31.md`)_ | `docs/HAZIRLIK-P3-K1-KARISIK-ORNEKLEM-2026-08-30.md`; commit `dcef1c6` | karışık-örneklem kararı; ileriye dönük hız yalnız 1345 yolu (pooled ~6,5 hafta / ayrık ~14 hafta) |

_(`P-1` KAPANDI 2026-08-30: damga gönderim anına bağlandı — `90f6cdc`, dağıtım `dcef1c6`;
kill#3 istisnası kartta ADIYLA kayıtlı — `83bc47b`.)_

#### KOVA 3 — ERİŞİM / KİMLİK (para ya da hesap gerektiren)

- **[TSK-044] FINVIZ Elite token satın alınsın mı (C1)** — status: OPERATOR · born: 2026-08-31 · owner: operator · size: S · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: BEKLEMEDE — bedel aynen sürer.) (operatör 2026-09-03 sabah: BEKLEMEDE — karar ertelendi, bedel aynen sürer.) satın alma kararı bekleniyor — Elite token evreni 251'in üstüne çıkarır.
  Why: EDG-2026-022 ölçtü — evren bağlayıcı DEĞİL (%34,17; de-risk+tavan %65,84 baskın) → harcama DE-RISK edildi; beklerken bedel evren kalıcı 251 kalıyor (`finviz_unavailable` 3.746 / `finviz_universe` 0).
  Ref: kimlik `B-FINVIZ-TOKEN` (§5 KİMLİK TABLOSU, WP4/WP11-A) · bağımlı: WP11-D uzlaştırma çözülmeden "kesinlikle gereksiz" DENEMEZ (EDG-026: "bağlayıcı kısıt EVREN %99.55").

- **[TSK-045] FMP plan/kota yükseltmesi kararı (C2)** — status: OPERATOR · born: 2026-08-31 · owner: operator · size: S · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: BEKLEMEDE — bedel aynen sürer.) (operatör 2026-09-03 sabah: BEKLEMEDE — karar ertelendi, bedel aynen sürer.) plan yükseltme kararı bekleniyor — ücretsiz planda `page>=1`/`limit>100`/`search?symbol` 402 dönüyor, `date=` sessizce yok sayılıyor.
  Why: beklerken bedel — Y4 içeriden-işlem penceresi günde tek sayfa (~100 dosyalama, evren isabeti ~6/100) ile ancak 3 yıl BEKLEYEREK dolar.
  Ref: kimlik `B-FMP-PLAN` (§5 KİMLİK TABLOSU) · bağımlı: EDG-2026-011 (askı).

- **[TSK-046] QC login + notebook koşumu kararı (C3)** — status: DONE(2026-09-03 · operatör QC girişi [Google hesabı, Reset My Token] + lean CLI onayı; EDG-021 v4 ikinci koşum ve ⑤ Security Master delist sondası Rol-1 tarafından QC'de koşuldu — ⑤ 8/8 çelişmedi [AYNI 3 / AYRIK ≤3 gün 3 / QC süreklilik 2]; kanıt research/olcumler/qc_dogrulama/sonda_delist_8*.json + wp-qc-5 belgesi; dotnet-engine yolu gerekmedi) · born: 2026-08-31 · owner: operator · size: S · trigger: —
  What: (2026-09-03 08:1xZ: QC ADIMLARI KOŞTU — EDG-021 v4 ikinci koşum tamam [C-11 kapandı]; ⑤ Security Master sondası düzeltilmiş haliyle koşuluyor; yol = `lean cloud push` + Chrome'da mevcut kernel oturumuna bağlı küçük çıktı defteri [research.ipynb 64.000 kr sınırı ölçüldü]. TSK-046 kapanışı sonda sonucuyla.) (2026-09-03 07:15Z: OPERATÖR GİRİŞ YAPTI — `lean whoami` ✓, kimlik dosyası 600; QC ücretsiz hesapta API jetonu 'Reset My Token' ile alındı ["Request Token Information" ücretli-org uyarısı verdi]; operatör CLI ile bulut kullanımına ONAY verdi [KEŞİF 2026-08-09 RED notunun üstüne operatör kararı]; ölçüm: `lean cloud pull` ücretsiz hesapta ÇALIŞTI [Fat Apricot Koala: research.ipynb + main.py + defter_021.py]; Research defteri CLI'dan koşulamaz → yol: Rol-1 `lean cloud push` ile yükler, operatör tek hücreyi web'de koşar. Sıradaki: EDG-021 v4 [C-11] + Security Master sondası.) (operatör 2026-09-03 sabah: OPERATÖR QC GİRİŞİNİ YAPACAK; sonra Rol-1 Security Master sondası + EDG-021 ikinci koşumu.) `lean login` (QC "Fat Apricot Koala") YA DA dotnet-engine yolu kararı; ayrıca FREE defterin operatör tarafından KOŞULMASI bekleniyor. Konsolide detay (eski TSK-051'den, kök fizibilite 2026-08-09): toolchain hazır (colima+docker+lean 1.0.227 çalışıyor), `lean init` QC User id+API token istiyor (`~/.lean/credentials`); kimliksiz alternatif dotnet-engine (LEAN Apache-2.0 local, QC'siz) ama monorepo clone+build = L-boyut ayrı tur.
  Why: toolchain hazır (colima+docker+lean 1.0.227) ama `lean init` QC User id+API token istiyor — kimlik-bloklu. Beklerken bedel: ⑤ RETIRED çapraz-doğrulamasının tek kalan QC-adımı (1 hücrelik Security Master sondası) ve EDG-021 2. koşumu bekliyor.
  Ref: kimlik `B-QC-LOGIN` (§5 KİMLİK TABLOSU) · bağımlı: WP9 · WP4 delist-bar hattı · TSK-051 buraya konsolide (operatör kararı 2026-09-01).

- **[TSK-047] NOUS_MODEL / beyin çeşitliliği — danışma yolu ölü olabilir mi (C4)** — status: OPERATOR · born: 2026-08-31 · owner: operator · size: S · trigger: —
  What: (OPERATÖR 2026-09-05 09:1xZ: BEKLEMEDE — öğrenme açılıp örneklem büyüyünce yeniden bakılır.) (operatör 2026-09-03 sabah: BEKLEMEDE — karar ertelendi, bedel aynen sürer.) Claude API anahtarı EKLE ya da `NOUS_MODEL`i Google-DIŞI modele çevir kararı bekleniyor (sır yolu, koda yazılamaz).
  Why: eski gerekçe ("model adı ölü") BAYAT — v239 model-adı bacağını kapattı, beyin zinciri artık AYRIK (`brain_chain_distinct` açık). "Danışma yolu ölü" şüphesi de KAPANDI — Rol-1 canlı ölçümü 2026-09-01 (A1 `agent_calls.jsonl`, 1.071 satır, 07 Ağu→31 Ağu): tarihsel boş-oranlar ölü ADLARDAN geliyordu (`tencent/hy3` 419/419 boş · `gemini-3.5-flash` 379/391 boş) ve o adlara son 14 günde SIFIR çağrı var (2026-08-13 iki-katmanlı ad-göçü onarımı işlemiş); bugünkü zincir `gemini-flash-latest`e gidiyor ve son 14 günün danışma çağrıları (nous_eval + reflect) %0 boş — beyanlı sınır: n=2, küçük örneklem (learn kapalı olduğundan hacim düşük), ama sınıf kesin (dolu) ve tüm-zaman `gemini-flash-latest` 81/81 dolu. Operatör yönü 2026-09-01: ÜCRETSİZ olmalı, Gemma tercih. Canary turu (2026-08-13 dersi: kimlik+yönlendirme+dolu-cevap sınanmadan ad değişmez): çıplak Google rotası Gemma taşımıyor (`gemma-3-27b-it`/`-12b-it` → 404); OpenRouter `:free` rotasında kimlikler VAR ve yönlendirme doğru (`google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free` → 429 = havuz kapasitesi, ad hatası değil); ayrıştırıcı karşı-test aynı dakikada `nemotron-super:free` DOLU cevap verdi → sorun hesap kotası DEĞİL, Gemma ücretsiz havuzuna özgü. ÖNERİLEN KURULUM (pano sır yüzeyi, iki alan): `NOUS_MODEL=google/gemma-4-31b-it:free` + `NOUS_FALLBACK_MODEL=nvidia/nemotron-3-super-120b-a12b:free` — zincir 429/boşta sıradakine düşer (hermes zincir döngüsü), yani Gemma havuzu tıkalıyken bile yol kanıtlı-canlı nemotron'da kalır ve telemetri (`agent_calls.jsonl`) Gemma'nın gerçek dolu-oranını önümüzdeki günlerde ölçer; dolu-cevap kanıtı Gemma'dan HENÜZ alınmadı (beyanlı — fallback bu riski taşınabilir kılıyor). UYGULAMA OPERATÖRDE: pano sır formu.
  Ref: kimlik `B-NOUS-BEYIN` (§5 KİMLİK TABLOSU) · bağımlı: WP7 (pilot-S1 ve terfi hattı) · canlı ölçüm + canary 2026-09-01 (Rol-1).

_(Yukarıdaki üç kovada olmayan operatör kalemleri — LoadCredential faz-1, ajan-git mekanik kapısı,
OCI bucket, Massive/QC delist-bar kaynağı, melez pozisyonlar, uyuyan-kurulum icra bağı — aşağıdaki
numaralı envanterde AYNEN duruyor; kova ayrımı yalnız "bugün bir bedel ödeniyor mu" sorusuna göredir.)_

---

Claude'un otonom kapatamayacağı kalemler: operatör kararı, ücretli kimlik/kota, gerçek-para kapısı,
ya da canlı-worker durdurup state'e yazan bakım penceresi. "Çağıranı yok" ile "çağıranı İNSAN" ayrı
şeydir (envanter tablosu §5-sonu bu ayrımı korur). ~~**Bakım-penceresi onaylı sırası (2026-08-09):**
OB-2 systemd exit-143 → OB-1 N1 kanal → OB-4 restart→PBO (M2) damgalama çapraz-kaldıraç~~ →
**GÜNCEL SIRA (2026-08-13, denetim B9/F8): OB-2 ✅ YAPILDI (2026-08-09) → sıranın başı artık **OB-1
bildirim kanalı** (bloksuz) → **`equity_curve`/`seed_boundary` ONARIMI** (state'e yazar, worker
durur — WP2-D, ACİL) → **OB-4 restart→PBO (M2) damgalama**;** N4 cf
çıkış-sadakati (EXE-2026-004 Aşama-2, saatler, state'e yazar) aynı pencerede.

**YENİ OPERATÖR BLOKLARI (WP turlarından toplandı — eski §8 numaralı listesi + envanter tablosu altta):**
- **[TSK-048] systemd `SuccessExitStatus=143` — temiz-durdurmayı FAILED saymasın** — status: DONE(2026-08-09·operatör doğruladı) · born: 2026-08-09 · owner: rol1 · size: S · trigger: —
  What: canlı `SuccessExitStatus=143` doğrulandı (`Result=success`, active/running, NRestarts=0) — restart exit-143'ü artık "FAILED" SAYMIYOR.
  Why: N1 bildirim kanalının (OB-1) ön-şartıydı — açıldığında temiz-durdurma yanlış-alarm boğmayacak (gerçek çöküş SIGKILL=137/SIGSEGV=139 hâlâ OnFailure'a gider).
  Ref: kimlik `B-SYSTEMD-143` (§5 KİMLİK TABLOSU, OB-2).
- **[TSK-049] DASH-TOKEN LoadCredential faz-1 etkinleştirme** — status: DONE(2026-09-01·canlı ölçüm) · born: 2026-08-03 (born tahmini: madde metninde tarih yok; repo dosya kanıtı `dash_token_credential.sh` mtime) · owner: operator · size: S · trigger: —
  What: drop-in'ler (`deploy/oracle-a1/meridian.service.d/` — faz-1 LoadCredential + faz-2 ortam-kanalı-sıfır) + `dash_token_credential.sh` (rotasyon/kurulum/doğrulama/geri-alma). Göç ajanı dosya varlığını doğruladı ama canlı aktivasyonu ölçemedi (GATED önerdi).
  Why: Rol-1 canlı ölçümü 2026-09-01 gece (ssh, salt-okunur): `meridian.service` (worker+dashboard) ACTIVE ve `LoadCredential` SET — faz-1 canlıda fiilen etkin; kimlik tablosunun "✅ KAPALI" hükmü kanıtla teyit edildi. Not: makinede ayrıca INACTIVE bir `meridian-dash.service` birimi duruyor — infra-simetri kalemine ilk somut vaka olarak devredildi.
  Ref: kimlik `B-DASH-CRED` (§5 KİMLİK TABLOSU) · canlı ölçüm 2026-09-01.
- **[TSK-050] ajan-git mekanik kapısı — PATH-shim/wrapper gerekiyor** — status: DONE(2026-09-01 · `ops/ajan_git_shim.sh` → `~/.local/bin/git` kurulu+canlı doğrulandı [stash RED rc=86, günlük komutlar saydam]; 13 çivi v360 + 4/4 mutasyon + kurulu-kopya ayrışma çivisi. KAPSAM BEYANI: yalnız evrensel-yasaklar mekanik — `stash` her biçimi + `add -A/--all/.`; oturum-kimlikli ayrım [ajan-commit engeli] ortamdan ÖLÇÜLEMEZ çıktı — spike 2026-09-01: Rol-1 ile ajan Bash'i aynı env işaretlerini taşıyor [CHILD_SESSION=1, AI_AGENT=…_agent] — o genişleme bilgi-tabanlı onay ister, ayrı karar. CLAUDECODE!=1 ortamı saydam geçer: operatör terminali etkilenmez; kaçış MERIDIAN_GIT_BYPASS=1) · born: 2026-08-26 (born tahmini: bu maddenin metninde tarih yok; CLAUDE.md §2 git satırındaki 2026-08-26 vakasıyla eşleşiyor) · owner: rol1 · size: S · trigger: —
  What: yasak bugün yalnız CLAUDE.md sözleşmesiyle duruyor — `dagit.sh` yalnız DAĞITIMI kapıyor, `git stash`ın pre-stash kancası yok; kapı ancak PATH-shim/wrapper'la mekanikleşir.
  Why: gece 2 ajan `git stash` koşup hasar verdi (hayalet dizin süpürüldü). Karar 2026-08-31 akşam verildi (masa→plan taşıması): İCRA SIRASI ①'de, Rol-1 — kimlik araç inince kapanır. CLAUDE.md §2'de ayrıca 2 zararsız-itirafla salt-okunur beyaz liste ajanlara AÇILDI (2026-08-31 gevşetmesi) — bu madde MEKANİK kapıyı (mutasyon engeli) kapsar, o gevşeme yalnız salt-okunur erişimi kapsıyordu.
  Ref: kimlik `B-AJAN-GIT` (§5 KİMLİK TABLOSU) · İCRA SIRASI ①.
- **[TSK-051] QC LEAN CLI `lean login` — kimlik-bloklu (C2-4)** — status: DROPPED(2026-09-01·operatör kararıyla TSK-046'ya konsolide — aynı B-QC-LOGIN kimliği, örtüşen içerik) · born: 2026-08-09 · owner: operator · size: S · trigger: —
  What: toolchain hazır (colima+docker+lean 1.0.227 kurulu/çalışıyor) AMA `lean init` QC User id+API token istiyor (`~/.lean/credentials`) — LEAN CLI yolu kimlik-bloklu. Operatör `lean login` (QC Fat Apricot Koala) yaparsa CLI tam-impl açılır. Alternatif (kimliksiz): CLI'sız dotnet-engine (LEAN Apache-2.0 local, QC'siz) — ama LEAN monorepo git-clone + dotnet-build = L-boyut ayrı tur.
  Why: karar — `lean login` (kolay) mı, dotnet-engine (bağımsız, daha büyük iş) mı.
  Ref: aynı kimlik `B-QC-LOGIN` — bkz. TSK-046 (QC login + notebook koşumu, KOVA-3/C3); içerik örtüşüyor, konsolidasyon Rol-1'e önerilir. Fizibilite 2026-08-09.

**EKSİK OPERATÖR ENVANTERİ (eski §8 — kanonik liste 1-11 + §8.1 tablosu; numaralar korunur):**

1. **[B-NOUS-BEYIN]** **NOUS_MODEL / beyin çeşitliliği — GEREKÇE GÜNCELLENDİ (2026-08-13, denetim F5).**
   ~~CANLI KANIT EKLENDİ (2026-08-12): Gemini HTTP 404.~~ Review
   doğrulamasında yakalandı: birinci model "Gemini returned HTTP 404" (endpoint/model-adı ölü), yedek
   tencent/hy3:free boş dönüyor → beyin zinciri fiilen CEVAPSIZ. v233 artık bunu dürüst olaylıyor ve
   bütçe yangınını kesti (150 boş çağrı/gün bitti) ama GERÇEK review üretimi beyin gelene kadar olmaz
   (12 denemede tarih 'gecersiz' işaretlenir — kalibrasyon boşluğu dürüst). **→ MODEL-ADI BACAĞI
   v239'da KAPANDI** (`canonical_model('gemini-3.5-flash')` → `gemini-flash-latest`; nous=tencent/hy3)
   → **beyin zinciri ARTIK AYRIK** (`brain_chain_distinct` açık).
   **Kalemin yeni gerekçesi "model adı ölü" DEĞİL, "DANIŞMA YOLU ÖLÜ"**:
   son 7 günde **788 `agent_call`, 385 boş, 1 başarılı görüş** (WP7/24c). Karar AYNI: Claude API
   anahtarı EKLE veya NOUS_MODEL'i Google-dışı modele çevir (panodan GEMINI_API_KEY girmek
   çeşitliliği GERİ siler). ⚠ Kalem **KAPANMIŞ OLABİLİR** — Rol-1 doğrulaması ister (§5 KOVA-3/C4).
2. **[B-BILDIRIM-N1]** **Bildirim kanalı:** Telegram/webhook — teslim zinciri hazır, kanal boş.
3. **[B-FMP-PLAN]** **FMP kota kararı** (plan/limit).
4. **[B-ORACLE-TASIMA]** **Oracle sunucu taşıma** (5.1) — Faz 6 ön şartı.
5. **[B-FAZ6-KILIT]** **Faz 6 kapısı:** BEŞ kilit (`health.faz6_kilitleri`) dolunca INTRADAY_ARM + emir bacağı onayı.
6. **[B-AJAN-TAVAN]** Ajan tavanı: 15 (2026-07-29; implementasyon yine turda tek ajan).
7. **[B-FMP-PLAN]** **FMP plan yükseltmesi (Y4):** ücretsiz planda Form-4 ucunun sayfalaması ve `search` ucu KAPALI
   (ölçüldü 2026-07-30 — aşağıdaki tabloda `insider` satırı). Yükseltme, 3 yıllık sınıflama
   penceresini beklemeden açar; yükseltilmezse pencere ancak zamanla dolar.
8. **[B-FINVIZ-TOKEN]** **FINVIZ_API_KEY (evren genişletme) — ÖNCE EDG-2026-022 (2026-08-09 keşfi):** Elite token evreni
   251'in üstüne çıkarır AMA satın almadan ÖNCE **EDG-2026-022** ("Evren bağlayıcı kısıt mı?" — otonom
   kart, `docs/KESIF-WP-U`) ölçmeli: işlem üretimini bağlayan aday-havuzu mu, yoksa de-risk tavanı
   (`eff_max_open`, günlerin %92'sinde 1 pozisyon) mu? Evren bağlamıyorsa FINVIZ parası boşa gider.
   Kanıt: `finviz_unavailable` 3.746 / `finviz_universe` 0. (§8.1 `FINVIZ_API_KEY` satırıyla aynı token.)
   **GÜNCELLEME (2026-08-13, denetim F7):** EDG-022'nin de-risk hükmü **geçerli kalır**; üstüne
   ısı-bağlayıcılık notu (EDG-035/039: bağlayan kısıt ISI) eklenir — **ama WP11-D çelişkisi
   (EDG-026: "bağlayıcı kısıt EVREN %99.55") çözülmeden "kesinlikle gereksiz" DENEMEZ.**
9. **[B-DELIST-KAYNAK]** **Massive/QC delist-bar kaynağı kararı (2026-08-09 keşfi):** survivorship-serbest evrenin TEK meşru
   yolu — RAKİP DEĞİL TAMAMLAYICI: **(a) QC platform-içi ölçüm** (BEDAVA; ToS barı dışarı ÇIKARAMAZ →
   yerel arşiv boşluğu ÖLÇÜLÜR, DOLMAZ) VEYA **(b) Massive plan yükseltmesi** (yerel arşivin tek meşru
   derin-tarih yolu; grouped bugün 403 + plan ~2 ay derinlik → 2004+ arşiv yeniden-üretilemez KALINTI).
   %96,57 delist boşluğu + EDG-018 açılışı buna bağlı. `docs/KESIF-WP-U` §6-B2 / `docs/KESIF-WP-QC`.
10. **[B-OCI-BUCKET]** **OCI Object Storage bucket + S3-uyumlu anahtar:** H10 Litestream **aşama-2** (off-box PITR).
    Always-Free 20GB yeter; gelene dek RPO = aynı-disk (medya/bölge arızası kapsanmaz). `docs/KESIF-WP-HD` §H10.
11. **[B-QC-LOGIN]** **QC FREE defter koşumu (EDG-021 boru hattı, 2026-08-09 keşfi):** FREE hesap AÇIK (2026-08-03);
    kalan tek blok operatörün notebook'u KOŞMASIDIR (ajan defteri yazar → operatör koşar → Rol-1 hüküm).
    Kuyruk başı = **⑤ RETIRED çapraz-doğrulama** (yerel yarısı 8/8 tutarlı; tek QC-adımı 1-hücrelik
    Security Master delist-olayı sondası). Ayrıca **EDG-021 2. koşum** tanım-eşitleme hakkı operatörde
    (@20 fazla CI-0-içi; WP-K K3). Katman yükseltmesi (Researcher Seat $10/ay) yalnız ölçüm-OTOMASYONU
    için — elle koşumda GEREKMEZ. `docs/KESIF-WP-QC` §6-5.

12. **[B-DD-ESIK]** ~~**goal.max_drawdown 0.08 ↔ benimsenen-dünya dd %12.4-12.7 GERİLİMİ (kod-turu bulgusu 2026-08-12)**~~
    → **✅ ÇÖZÜLDÜ (2026-08-13, OPERATÖR KARARI — karar penceresi; denetim F1).** `state/goal.yaml:20`
    `max_drawdown: 0.16` ("OPERATÖR KARARI 2026-08-13 penceresi"). Maddenin "0.08'e bakmaya devam
    ediyor" cümlesi artık tarihsel olarak yanlıştır. Zincir aynı turda kapandı: aşağı akış
    `shadowlaw.DD_VETO_MARGIN` 0,04 → **0,08** (goal'ün TAM YARISI, `62727d6` v238) → eski Ö-20a
    ✅ kapandı ve §8 arşive alındı. Karar satırı §7'te. *(Özgün metin, tarihçe olarak:)*
    C+mb paketinin ÖLÇÜLEN max-dd'si hedef-sözleşmesi eşiğinin üstünde — `goal_failure_report` + iki
    analytics kapısı 0.08'e bakmaya devam ediyor; paket normal davranırken "deney başarısız" işareti
    üretecekler (alarm/rapor düzeyi; icrayı durdurmaz). Rampa artık bu değere bağlı DEĞİL (v237 kablo).
    Rol-1 önerisi: eşik %16-18 bandına (ölçülen dd × ~1.3 tampon) — ama bu HEDEF SÖZLEŞMESİ maddesi,
    karar operatörün. Karar gelene dek 0.08 bilinçli-eski kalır (dürüst işaret: eşik aşımı = "paket
    beklenen bölgesinde, sözleşme güncellenmedi" diye okunmalı). (temizlik turu 2026-07-30 — ölü-mekanizma avının üçüncü kovası)

Bu tablonun VARLIK SEBEBİ: hedef sözleşmesi md.1 üç hâl tanır — kablolu, emekli, ya da **operatör
kalemi**. Üçüncüsü yazılı olmazsa bir sonraki ölü-mekanizma avı bunları "çağıranı yok" diye yeniden
öldürmeye çalışır (bu turda İKİSİ tam olarak öyle işaretlenmişti ve çürütüldü). "Çağıranı yok" ile
"çağıranı İNSAN" ayrı şeylerdir.

_**[2026-08-31 DURUM DENETİMİ — BU TABLO BİR ENVANTERDİR, İŞ LİSTESİ DEĞİL.]** Satırları kalıcı
kaldıraçlar ve kimliklerdir (sırlar, kurtarma kolları, elle tetikler); "açık" ya da "kapalı"
olmazlar — VAR olurlar. 13 satır bu gerekçeyle rozetsiz bırakıldı ve `belirsiz` okunmaları
doğrudur. Bir satır bir KARAR beklemeye başladığında yeri burası değil, `§5`in kimlik tablosudur._

_**[2026-08-31 KONSOLİDASYON — BU TABLO REFERANSTIR, kalem değil.]** Kimlik/erişim/elle-tetik envanteri; rozet taşımaz. Karar bekleyen satır buradan `§5` karar tablosuna terfi eder._

| Kalem | Ne | Neden operatörde | Nasıl kullanılır |
|---|---|---|---|
| `alpaca.live_client` / `live_guard` | Gerçek-para ticaret istemcisi ve onun sert kapısı (UYUYAN — hiçbir üretim yolu çağırmıyor) | Gerçek para. Kod bir insan iki bayrağı elle çevirmeden ve §8 terfi kapıları geçilmeden bu yola GİREMEZ | `MERIDIAN_MODE=live` **ve** `MERIDIAN_I_ACCEPT_RISK=true` + `goal.limits.autonomy_level >= 1`; üçü eksikse `live_guard` RuntimeError atar |
| `TELEGRAM_*` / `MERIDIAN_WEBHOOK_URL` | Bildirim kanalı kimliği (HALT, breaker, rollback, süreç ölümü) | Kimlik/kanal operatörün; girilene dek `notify.configured()` False ve `fail-notify` beyanlı no-op'tur | Ayarlar ekranından ya da ortam değişkeni; girildiği an teslim zinciri (obs.alarm → notify.send) uçtan uca çalışır |
| `FINVIZ_API_KEY` | Finviz **Elite** token'ı (evren keşfi) | Ücretli abonelik. Yokken public HTML scraping ToS-riskli olduğu için otonom döngüde KAPALIDIR — Finviz dürüstçe devre dışı kalır | Ayarlar → "Test et" (`finviz.ping`). Token yoksa evren `REPLAY_UNIVERSE`e iner ve `finviz_unavailable` olayı bunu söyler |
| `HERMES_API_KEY` / `ANTHROPIC_API_KEY` | Yansıma beynine erişim | Ücretli API kimliği; anahtar yoksa beyin zinciri kotasız yola düşer ve gece yansıması sessizce durmaz, `brain_availability` alanında görünür | Ayarlar/ortam; durum `/api/hermes` → `integrations` ve `brain_cooldown` satırlarında okunur |
| `NOUS_MODEL` | Haftalık öz-değerlendirme beyninin model kimliği | **Beyin ÇEŞİTLİLİĞİ kararı**: Google'dan Google'a çevirmek çeşitliliği GERİ siler (bkz. §8 md.1) | Ortam değişkeni; boşsa varsayılan zincir kullanılır |
| `MERIDIAN_FORCE_RESEED` / `MERIDIAN_FORCE_BASELINE` | Kurtarma kolları — durum yeniden tohumlama / taban zorlama | Yıkıcı: birikmiş defteri geçersiz kılabilir. Otomatik bir yolun bunlara dokunması, bir arızayı sessizce "temiz başlangıç" gibi göstermek olurdu | Yalnız elle, tek koşu için; kullanıldığı tur ROADMAP §7'ye yazılır |
| `MERIDIAN_CORS_ORIGINS` | API'yi BAŞKA bir origin'e açar | Güvenlik yüzeyi. Token'sız açılırsa API hem cross-origin hem kimliksiz olur — `api.py` bunu `cors_without_token` ile uyarır ama ENGELLEMEZ | Virgüllü origin listesi; **daima** `MERIDIAN_DASH_TOKEN` ile birlikte |
| `MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES` | L1+ bayrağı: WS koptuğunda açık girişleri iptal et | Otonomi seviyesine bağlı bir risk tercihi; kâğıtta gereksiz, gerçek parada operatörün kararı | RUNBOOK'ta yazılı; `deploy/oracle-a1/RUNBOOK.md` prosedürüyle açılır |
| `MERIDIAN_SUPERVISED` | "Süpervizör altında (yeniden) başladım" bildirimi | Süreç ölümünün operatöre ulaşan iki yolundan biri. `ops/com.meridian.agent.plist` kuruyor — yani **ölü değil**, av adayıyken çürütüldü | LaunchAgent yüklüyse otomatik; elle koşuda `MERIDIAN_SUPERVISED=1` |
| `watchdog.grant_amnesty` | Meşru defter küçülmesine (re-seed) af damgası | Monotonluk dedektörünü SUSTURUR. Bir mekanizmanın kendi alarmını kapatabilmesi, dedektörü dedektör olmaktan çıkarırdı | Elle çağrılır; af `monotonic_amnesty.json`a yazılır ve raporda `amnestied` alanıyla GÖRÜNÜR kalır |
| Sprint elle tetiği | Öğrenme antrenmanını sıradan önce başlatma (override) | Kadans zaten otomatik (`sprint.maybe_start`); elle tetik yalnız HIZLANDIRMADIR ve `should_run` kapılarını atlar | Pano düğmesi / `/api/sprint`; meşguliyet penceresinde kullanmak bar kovalamasını yavaşlatır |
| `reflect --auto` | Deterministik tek-hamle yansıması (LLM'siz) | Beyinsiz/kotasız gecede tek hamle üretmenin elle yolu. `skills.axis2_cycle` Eksen-2 kolunu devraldıktan sonra ÜRETİM çağıranı kalmadı — kalan tek yol bu komut | `uv run python -m meridian.reflect --auto` (README'de yazılı). Otomatik bir çağıran EKLENMEZ: iki yansıma aynı gecede yarışır |
| FMP plan yükseltmesi | Y4 içeriden-işlem derinliği | Para kararı. Ücretsiz planda ölçüldü (2026-07-30): `page>=1` → 402, `limit>100` → 402, `search?symbol` → 402, `date=` sessizce yok sayılıyor | Yükseltilince `insider.PLAN_SAYFA_TAVANI` ve `--gecmis` yolu yeniden açılabilir; kadans bugün günde 1× `page=0` çekiyor |

**🔒 BİLET SAHİPLERİ (eski WP-O — §5'teki biletlerin envanteri):**
bildirim kanalı · NOUS_MODEL · FMP planı · VIX kaynağı [öncelik düşük — aile hükmü zayıf] ·
analist/NLP verisi · FISV/PSKY; ~~shares-outstanding~~ ve ~~PIT-fundamentals~~ 2026-08-01'de
EDGAR'la operatörsüz çözüldü)

## §6 KANIT/KARTLAR (`research/cards/` indeksi + hükümler) _(eski: §4)_

Kural (README + iş emri): **kartsız ölçüm kodu yok**; her parametre grid'i K'ya ÇARPILARAK sayılır;
eşik ölçümden SONRA değişmez; kill-list dokunulmaz; ölçüm ajanı karta DOKUNMAZ (hükmü Rol-1 işler).
Durumlar: registered → measuring → promoted | archived. Kuzey yıldızı canlı hüküm (§0): **EDGE 1/5 ·
SONUÇ 0/4** — edge/para kanıtlanmadı. Aşağısı ÖZET-indeks; tam hüküm ilgili §8 WP / §7 kararında.

**Kart durumları `research/cards/README.md`'de** — `ops/kart_endeksi_uret.py` üretir; sayı burada
TEKRAR EDİLMEZ (tek-kaynak yasası; TSK-082, 2026-09-03: elle tutulan indeks/mutabakat sayım
tabloları kaldırıldı — README aynı kartları `status` + hüküm cümlesiyle zaten taşıyor, kart-kart
kıyası rapora yazıldı, kayıp bulunmadı). Bayat mı diye sor: `python ops/kart_endeksi_uret.py
--kontrol` (çıkış 1 = bayat).

> **✅ FRİKSİYON ŞERHİ TURU — KAPANDI (2026-08-13, commit 025ef1d; hüküm metni işi, ölçüm gerekmedi):**
> altı kartın altısı da işlendi — **026 · 032** (paketin kendi seçim ve kabul gerekçesi) + **033 ·
> 023 · 025(ölçüt-ii) · 035(damga)** — ve **EXE-2026-001-R2**'ye K1 şerhi (denetim A6). Hiçbir hüküm
> SİLİNMEDİ, hepsi ÜSTÜNE yazıldı; hiçbir hücre yeniden koşulmadı (şerhler ÇIKARIM, §E.0 ayrım
> kuralıyla). Şablon: `EDG-2026-036`nın `friksiyon_serhi` bloğu. Şerhsiz geçerli sekiz kart —
> **024 · 027 · 028 · 029 · 030 · 031 · 034 · 039** — kasten dokunulmadı; bunların **beşi**
> (027/028/029/030/039) gerçek friksiyonla **GÜÇLENİYOR**. Yani TCA, replay hüküm gövdesinin çoğunu
> **çürütmüyor**; yalnız **paketin seçim/kabul gerekçesini** (026/032) ve **bir null hükmü** (033)
> asıyor. Aynı turda 46 kartın **4 YAML ayrıştırma hatası** onarıldı (002 akış-dizisinde `#2` yorum
> başlatıyordu · 016/017 tırnaksız `universe` içinde `": "` · **037'nin kendisi okunamıyordu**) —
> içerik değişmedi, yalnız sözdizimi; **46/46 temiz**. Denetim §G'nin bildirdiği çift-`verdict`
> kalemiyle aynı sınıf, ama §G yalnız 038'i sayıyordu: bu dördü **ek bulgudur**.
>
> **AÇIK KALAN — ölçüm gerektiren tek kalem:** 026 şerhinin kendi işaret ettiği B-vs-C
> friksiyon-duyarlılık taraması → **EDG-2026-040** ön-kayda geçti (yukarıdaki satır).
> _(Ayrım kuralı — denetim §E.0, ANALİTİK ÇIKARIM, ÖLÇÜM DEĞİL: friksiyon varsayımı değişince
> **DEĞİŞMEZ** = aynı işlem kümesinde eşli R farkları · oran/sayım ölçütleri · bit-özdeş sonuçlar;
> **DUYARLI** = kollar arasında işlem SAYISI farklıysa ΔP&L; **DOĞRUDAN ASILI** = mutlak seviye
> iddiaları (net P&L, PF, sharpe seviyesi).)_

**AKTİF / YENİ KARTLAR (hüküm işlenmiş ya da ölçümde):**
- **[EXE-2026-006] limit-bacagi-hukum-sinamasi** — status: DONE(2026-08-17·NO-GO) · owner: rol1 · size: — · trigger: —
  What: EXE-2026-001-R2'nin "limit bacağı MONOTON ZARARLI · kaçanlar sistematik KAZANAN" hükmünü TAM pencerede (2022-01-01→2026-07-30, evren 251, K=8: `limit_pct_cap`{0,005·0,01·0,02·0,03}×`dolum_kurali`{yalniz_acilis·dinlenen_limit}) yeniden sınadı; şasi kapısı EXE-005'ten devralındı ama yeniden koşuldu.
  Why: kart 2026-08-17'de ölçülüp hüküm yazıldığında `status:` alanı `registered` kalmıştı (verdict bloğu yazılmamıştı, `research/olcumler/exe006_limit_bacagi_2026-08-17/HUKUM.md`, commit `a033256`) — bu ayrışma 2026-09-01 GERÇEKLİK KONTROLÜNDE artık ÇÖZÜLMÜŞ görünüyor (disk `status: measured`). **✅ HÜKÜM (altı kill kriterinin ALTISI geçti) — E1 HÜKMÜ YENİDEN AÇILIR:** H1 (monotonluk) DÜŞTÜ (net P&L 9.773→19.452→17.948→17.858, tepe 0,01'de) · H2 (ay-kümeli bootstrap, B=5000) dört tavanda da CI sıfırı içeriyor → ÖLÇÜLEMEDİ · Ö1 (birim uyuşmazlığı: RED OLAYI vs DİSTİNKT İŞLEM) ÖLÇÜLEMEDİ (UYDURMA YASAĞI: None+neden) · Ö3 ÖLÇÜLDÜ (ΔP&L dört tavanda POZİTİF +146/+7.163/+5.759/+7.355$; cap=0,005'te 154 işlem yerinden oldu, hepsi kaybedendi). **SONUÇ:** canlı yapılandırmanın (`limit_pct_cap=0,04` ile bacağın etkisizleştirilmesi) gerekçesi ARTIK KANITLI DEĞİL, ama kart bacağın AÇILMASINI da ÖNERMEZ (kendi sınırı; açma kararı strateji kimliğidir → §5 operatör bloğu). CANLI DOKUNULMAZ: `state/goal.yaml` DEĞİŞMEZ. Beyanlı sınırlar: E1'in yerine geçmez, günlük-bar sıra belirsizliği kötümser tarafa yazılır, `max_chase` kırpması ölçümden önce beyan edildi → hüküm bir ALT SINIRdır. BU TURDA YAPILMAYANLAR: ΔP&L bootstrap CI'ı, Ö1'in kimlikli yeniden tanımı; duman penceresinin (n=1..3) işareti YANILTTIĞI kayda geçti (885 işlemlik dünyada işaret döndü). Ref: research/cards/EXE-2026-006-limit-bacagi-hukum-sinamasi.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EXE-2026-005] dinlenen-limit (23c)** — status: DONE(2026-08-17·GEÇTİ) · owner: rol1 · size: — · trigger: —
  What: Replay'in limit girişini yalnız bir sonraki barın açılışına karşı sınamasının (gerçek limit emri gün boyu DİNLENİR) yarattığı tek-yönlü hata A/B kollarıyla ölçüldü; veri yeterli (günlük bar `low`, dakika barı gerekmez, o 23e'dir).
  Why: **A KOLU ÖZDEŞLİK HÜKMÜ GEÇTİ** (Rol-1, operatör onaylı) — işlemler+seanslar bayt-özdeş, 12 sonuç bloğunun 11'i eşit; tek ayrışan alan (`n_endeks_satir`, girdi envanteri sayacı) adıyla sınırlı tek istisna olarak muaf tutuldu, şasi özelliği değil. Reddedilen alternatif: "tabanı yeniden üret" (EDG-032'nin dondurulmuş kanıtını bozardı — tarihi tahrif olurdu). **B KOLU KOŞULDU ve örneklem BOŞ çıktı** — sebep yapısal: kartın ürünü (Ö1/Ö2/Ö3) `EXE-2026-006` çözülmeden üretilemezdi (o kart artık DONE). Beyanlı sınır: ölçüm bir ALT SINIRdır, 23d'yi (bar-içi stop slipajı) çözmez, yalnız asimetrinin yarısını kapatır. Ref: research/cards/EXE-2026-005-dinlenen-limit.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-022] evren-bağlayıcı-kısıt** — status: DONE(2026-08-09·GEÇTİ) · owner: rol1 · size: — · trigger: —
  What: De-risk rampası ile tavan kısıtının BİRLİKTE evrenin bağlayıcılığındaki payı ölçüldü.
  Why: de-risk+tavan BİRLİKTE %65,84 (CI 58,73–72,14, tamamı >%50) BASKIN → FINVIZ token harcaması **GEREKÇESİZ**; evren bağlayıcı DEĞİL (%34,17). Bağlayan: `tavan_sifir` %57,54 + `derisk_bagladi` %8,28. KILL#3 tetiklendi (rejim-koşullu): trend_up'ta de-risk baskın, chop'ta (nadir %6,7) evren baskın → chop-özel evren ayrı+küçük konu, OTONOM/bloksuz → §5-8 FINVIZ. Ref: research/cards/EDG-2026-022-evren-baglayici-kisit.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EXE-2026-004] cf-çıkış-sadakati (N4)** — status: OPERATOR · owner: rol1 · size: — · trigger: —
  What: (operatör 2026-09-03 sabah: Aşama-2 HAFTA SONU bakım penceresinde koşulur — Cumartesi seans dışı, worker durdurulur, sonuç karta + K-defterine; KOVA B B-20.) Aşama-1 (üç tüketici ölçütü) ölçüldü; Aşama-2 (dört/altı çıkış tipi + tüm cf tarihi yeniden koşum) bakım penceresi bekliyor.
  Why: Aşama-1'de üç ölçüt de ölçülebilir zarar göstermedi → cf çıkış-tipleri EKLENMEDİ (+0,039R iyimserlik sapma olarak KAYITLI, düzeltilmedi). Aşama-2 eşiğe ULAŞILMADI → DONDU; eşikler ölçümden ÖNCE donmuştu, DEĞİŞMEDİ. Bakım penceresi şartlı (saatler, state'e yazar) → operatör kararı §5. Ref: research/cards/EXE-2026-004-cf-cikis-sadakati.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-021] qc-delist-doğrulama** — status: DONE(2026-09-03·KALDI) · owner: rol1 · size: — · trigger: —
  What: (KALDI 2026-09-03: ikinci koşum v4 PIT evren — @20 fazla +0,48% CI[−0,10; +1,19] CI-0-içi; operatör+Rol-1 kararı ŞÜPHEDE-bilgisiz → ARŞİV, EDG-016 canlıda kalır; kanıt research/olcumler/qc_dogrulama/sonuc_021_v4.json.) (operatör 2026-09-03 sabah: QC girişinden [TSK-046] sonra İKİNCİ KOŞUM, evren PIT üyelik listesiyle eşitlenerek — tanım-eşitleme ONAYLANDI, eşikler donuk; KOVA C C-11.) QC FREE defter v3 ile delist doğrulaması ölçüldü (DUR=None, PK GEÇTİ, IC=0,0265 n=335k).
  Why: @20 fazla CI-0-içi → kill#1 "ŞÜPHEDE-değerlendirme" (birincil şüphe: evren-kompozisyon farkı); ikinci koşum için tanım-eşitleme hakkı OPERATÖRDE (§5-11; WP-K K3). Ref: research/cards/EDG-2026-021-qc-delist-dogrulama.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-019] skill-görüş-defteri (N2b)** — status: OPERATOR · owner: rol1 · size: — · trigger: —
  What: Skill görüş katmanı canlıya kartsız sevk edilmiş (v218); terfi/emeklilik R-figürleri (vcp +0,116R / momentum-burst −0,114R) canlı state'te yeniden-üretilemedi (`eksen2.uretilen=0`, `gorusleri.jsonl` beslenmedi).
  Why: 2026-08-23 Rol-1 kaydı (WP7 eleme turu, GERÇEKLİK KONTROLÜ ile bu göçte yüzeye çıktı) — kart↔kod ayrışması (kod kartsız sevk edilmiş, katmanın ürettiği hiçbir sayı resmî hüküm değil) + donuk kill#1 tetiklenmiş ama uygulanmamıştı (p95_pay 6,57 > tavan 0,10) → **katman KAPATILDI** (yazım varsayılan-kapalı bayrağa alındı, E-partisi v278). Yeniden açılış yalnız kartın RESMÎ ölçümüyle. _(README numara-notu: 019 önce "emekli" damgalıydı; bu defter için yeniden kullanıldı.)_ Ref: research/cards/EDG-2026-019-skill-gorus-defteri.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EXE-2026-003] gölge-planlı-kol (N2)** — status: ACTIVE · owner: rol1 · size: — · trigger: —
  What: Silahlanmamış planlı kol AYRI defterde (`kol: planli|silahli`) ölçülüyor; kod indi (v217), ilk koşum yapıldı, pencere doluyor.
  Why: karışım kill#4'ü ateşlerdi, bu yüzden ayrı defter zorunlu; Faz-5 kilidini AÇMAZ (kilit gerçek-iç-dolum ister), ölçeği ikincil hat verir: gölge(dakika-sim) × cf(EOD-sim). Anahtar/kol tanım revizyonu ölçüm SONRASI yapıldı ama eşik/kill DEĞİŞMEDİ (kart dosyasının kendi dürüstlük beyanı). Ref: research/cards/EXE-2026-003-golge-planli-kol.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-017] rvol-form-revizyonu** — status: DONE(2026-08-02·KALDI) · owner: rol1 · size: — · trigger: —
  What: rvol≥2,5 bölgesinde form-şartsız + sürekli-rvol artığı ölçüldü (1.4'ün torun-kartı).
  Why: ÜÇ kill de tetiklendi → ARŞİV (kartın kendi disk `status:` alanı; bu satır önceden "registered (K+=2)" yazıyordu — GERÇEKLİK KONTROLÜ ile düzeltildi, ölçüm-sonrası-seçim yasağına uyuldu). Ref: research/cards/EDG-2026-017-rvol-form-revizyonu.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-018] pit-midcap-üst-sınır** — status: OPERATOR · owner: rol1 · size: — · trigger: —
  What: PIT midcap-survivor kohortu için feasibility-gate (ADIM-0) sınandı; kayıt K+=1.
  Why: ADIM-0 DÜŞTÜ — kohort kurulamadı (PIT evren kaynağı yok) + isim eşiği 12<40 → askıda:veri-kapısı (delist-bar kaynağı ya da S&P400/600 PIT üyelik gelirse yeniden açılır; §5-9). Yan kazanım: EDG-016 penceresinde çıkan 350 isimden 338'i (%96,57) arşivde sıfır bar — survivorship şerhi sayı kazandı. Ref: research/cards/EDG-2026-018-pit-midcap-ust-sinir.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-020] postevent-inplay** — status: DONE(2026-08-03·KALDI) · owner: rol1 · size: — · trigger: —
  What: Post-event in-play havuz-fazlası ölçüldü.
  Why: kill#1+#3 tetiklendi (havuz-fazlası CI-0-içi/negatif; ham +%1,1 taban-sürüklenmesi = ders#3 vakası) → ARŞİV; EDG-2026-011'e aleyhte-önsel not düşüldü. Ref: research/cards/EDG-2026-020-postevent-inplay.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[KYS-2026-001] kıyas-kirlenmesi** — status: DONE(2026-08-02·KALDI) · owner: rol1 · size: — · trigger: —
  What: ALTYAPI kartı (retro-hüküm taşımaz) — kıyas kirlenmesi yanlılığı ölçüldü.
  Why: kill#1 tetiklendi → ARŞİV; yanlılık iki yüzeyde de CI-0-içi ve |fark|<10bps → pratik-önemsiz, temiz-kıyas aracı OPSİYONEL kaldı, yeniden-okuma envanteri BOŞ. _(2026-08-17 düzeltme tarihçesi: satır önce 'registered' + ölçüm-öncesi 'M1' iddiası taşıyordu, kart 15 gündür zaten arşivdeydi.)_ Ref: research/cards/KYS-2026-001-kiyas-kirlenmesi.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EXE-2026-001] entry-execution** — status: DONE(2026-08-07·NO-GO) · owner: rol1 · size: — · trigger: —
  What: E1-R2 grid koşuldu; işletim noktası REF·limitsiz rejim (`limit_atr_mult:100`/`limit_pct_cap:0,04`).
  Why: limit-bacağı MONOTON ZARARLI, kaçanlar sistematik kazanan → bacak canlıda kapalı kalır (NO-GO). E2 defteri gerçek dolumla accrues → canlı-geçiş kapısında E2 kanıtıyla yeniden hüküm (WP-E §3). _(Bu hüküm sonradan EXE-2026-006 tarafından YENİDEN AÇILDI — H1 monotonluk düştü, bkz. o kart.)_ Ref: research/cards/EXE-2026-001-entry-execution.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EXE-2026-002] faz5-çıkış-ölçümü (+R1)** — status: OPERATOR · owner: rol1 · size: — · trigger: —
  What: Faz-5 çıkış ölçüm kodu yazıldı ve koştu (v212, `meridian/faz5_cikis.py`); n_eşleşen 4/4 (kill#4 %0), ort −9,69 bps.
  Why: CI HESAPLANMADI (`n_kume=1`, dört dolum tek gün) → istatistiksel hüküm eksik, iş (uygulama) borcu bekliyor, kod değil. kill#4 uygulama borcu → WP-S2 §3'e devredildi. Ref: research/cards/EXE-2026-002-faz5-cikis-olcumu.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).

**ARŞİV / KAPALI KARTLAR (hüküm — tam gerekçe §8 ilgili WP + §7):**
_**[2026-08-31 KONSOLİDASYON — BU LİSTE ENDEKSTİR.]** Satırlar kart durumlarının dizinidir, açılıp kapanan kalem değil; karışık-durumlu satırlar rozetlenmez (durumlar kartlarda). `/api/roadmap` bunları `belirsiz` sayar ve bu doğrudur._
- **[EDG-2026-016] turnover-ana-etkisi** — status: DONE(2026-08-01·GEÇTİ) · owner: rol1 · size: — · trigger: —
  What: Turnover ana-etkisi ölçüldü (üç kill de tetiklenmedi).
  Why: SUCCESS / YAŞAYAN SİNYAL — @20 net +0,55% CI-0-dışı, q5 monoton, survivorship-şerhli. Kablolama (canlıya entegrasyon) açık kalem → WP2 §3. Ref: research/cards/EDG-2026-016-turnover-ana-etkisi.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-009] trend-kolu-rafine** — status: DONE(2026-07-31·GEÇTİ) · owner: rol1 · size: — · trigger: —
  What: Ham trend kolunun rafine edilmesi ölçüldü.
  Why: measured→ALIVE/refine — ham kol incumbent kalır, PIT şerhi ~6-7p/yıl, gölge-kitap kod-hazır. _(önceden EDG-2026-003/EDG-2026-011 ile aynı KARIŞIK satırda taşınıyordu, bu göçte ayrıldı.)_ Ref: research/cards/EDG-2026-009-trend-kolu-rafine.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-003] rampa-p3** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: P3 rampa paketi (K=4) ölçüldü.
  Why: measured→daraldı — P3 paketi ÖLDÜ (kill#1), rampa korumasının kendisi gerçek kaldı. _(önceden EDG-2026-009/EDG-2026-011 ile aynı KARIŞIK satırda taşınıyordu, bu göçte ayrıldı.)_ Ref: research/cards/EDG-2026-003-rampa-p3.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-011] inplay-önceliklendirme** — status: OPERATOR · owner: rol1 · size: — · trigger: —
  What: In-play aday-gün önceliklendirmesi kill#3'te ASKI (K harcanmadı).
  Why: kök neden VERİ — state/earnings.csv tarihsel takvim değil (tek ileriye-dönük anlık görüntü); PIT-takvim biriktikçe ya da EDGAR filed-tarih vekili gelirse yeniden açılır (FMP-402 erişim notu ayrıca kayıtlı). _(önceden EDG-2026-009/EDG-2026-003 ile aynı KARIŞIK satırda taşınıyordu, bu göçte ayrıldı.)_ Ref: research/cards/EDG-2026-011-inplay-onceliklendirme.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-013] mom-turnover** — status: DONE(2026-08-01·KALDI) · owner: rol1 · size: — · trigger: —
  What: Momentum×turnover etkileşim tezi ölçüldü (EDG-016 ana-etkisiyle birlikte).
  Why: devir-arşiv — etkileşim-tezi düştü, EDG-016'nın kaderini belirledi (ana etki yaşıyor, etkileşim yaşamıyor). Ref: research/cards/EDG-2026-013-mom-turnover.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-012] net-issuance** — status: DONE(2026-08-01·KALDI) · owner: rol1 · size: — · trigger: —
  What: Net-issuance sinyali ölçüldü.
  Why: kill#2 — yön literatürün TERSİ ve anlamlı (MAX deseni, U-eğrisi) → ARŞİV. Ref: research/cards/EDG-2026-012-net-issuance.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-014] gross-profitability** — status: DONE(2026-08-01·KALDI) · owner: rol1 · size: — · trigger: —
  What: Gross-profitability sinyali ölçüldü.
  Why: kill#1 — BİLGİSİZ (üst/alt dilim ve yayılım @20+@60 anlamsız) → ARŞİV; yan not: PIT filed-tabanlı as-of yaklaşımı İLK KEZ burada meşrulaştı. Ref: research/cards/EDG-2026-014-gross-profitability.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-010] pullback** — status: DONE(2026-08-01·KALDI) · owner: rol1 · size: — · trigger: —
  What: Pullback setup'ı ölçüldü (ölçüt-kusuru itiraflı).
  Why: bağımsızlık gerçek ama kenar (edge) yok → ARŞİV; ders#3 vakasına referans. Ref: research/cards/EDG-2026-010-pullback-setup.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-015] vcp-decompose** — status: DONE(2026-08-01·KALDI) · owner: rol1 · size: — · trigger: —
  What: VCP geometrisinin bileşenlerine ayrıştırılması ölçüldü.
  Why: kill#1 — çatı da BİLGİSİZ (form = bileşen-toplamı, ρ=0,95) → ARŞİV, WP-K açık-hipotez listesi kapandı. Ref: research/cards/EDG-2026-015-vcp-decompose.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-001] 52wh** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: 52 haftalık yüksek yakınlığı (52wh proximity) ölçüldü.
  Why: 9/9 hücre anlamsız (tarih-kümeli bootstrap; en iyi cf@20 IC=0,037 CI[-0,030,+0,100]) → ARŞİV. Ref: research/cards/EDG-2026-001-52wh-proximity.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-002] volume-shock** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: Hacim şoku (volume-shock) sinyali ölçüldü.
  Why: bant yapısı hayalet-artefaktı DEĞİL ama 18 hücrenin hiçbiri ham anlamlı çıkmadı → ARŞİV; torun-kartı EDG-2026-017'ye devretti (o da ayrıca ARŞİV). Ref: research/cards/EDG-2026-002-volume-shock.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-004] max-filter** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: MAX-filtre sinyali ölçüldü.
  Why: iki kill de tetiklendi — yön TERS (yüksek-MAX @20 DAHA İYİ) → ARŞİV. Ref: research/cards/EDG-2026-004-max-filter.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-005] sma-gate** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: SMA-kapı (gate) mekanizması ölçüldü.
  Why: ilk "KAPI_AÇILABİLİR" hükmü mekanizma kanıtıyla düştü → KAPI AÇILMAZ, GÖSTERGE sınıfına emekli edildi. Ref: research/cards/EDG-2026-005-sma-gate.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-006] turn-of-month** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: Ay-dönümü (turn-of-month) etkisi ölçüldü.
  Why: kill#2 ön-adımda tetiklendi (ikiz koşum hiç açılmadı, K tasarrufu) — yön ters → ARŞİV. Ref: research/cards/EDG-2026-006-turn-of-month.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-007] residual-momentum** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: Residual momentum sinyali ölçüldü.
  Why: iki kill de tetiklendi — kill#1: 6/6 dilim hücresi CI-0-içi (ρ=0,625) → ARŞİV. Ref: research/cards/EDG-2026-007-residual-momentum.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-008] vol-scaling-overlay** — status: DONE(2026-07-31·KALDI) · owner: rol1 · size: — · trigger: —
  What: Volatilite-ölçekleme overlay'i ölçüldü.
  Why: kill#3 — iki pencerede de yönsüz/CI-0-içi → ARŞİV. Ref: research/cards/EDG-2026-008-vol-scaling-overlay.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[BASE-2026-001] sistem-karnesi** — status: DONE(2026-08-01·GEÇTİ) · owner: rol1 · size: — · trigger: —
  What: Sistemin uçtan-uca karnesi (huni + getiri) ölçüldü.
  Why: KARNE HÜKMÜ verildi — +%2,5/4,5 yıl, sonuç 2024-bağımlı (getiri bir yıla yoğunlaşmış, kayıtlı caveat); huni üç-darboğaz gösterdi. Ref: research/cards/BASE-2026-001-sistem-karnesi.yaml (size ölçülemedi: kart S/M/L beyanı taşımıyor).
- **[EDG-2026-069] sinyal-tetik-dolum-tick-bacagi** — status: ACTIVE · owner: rol1 · size: — · trigger: —
  What: (ONAY 2026-09-03 sabah, operatör K2 → ACTIVE: ölçüm kodu KOVA C sırasında; eşikler donuk.) ⑥a (TSK-066) ön-kayıt 2026-09-03 gece: tetik kırılma saniyesi → dolum gecikmesi (≤60 sn) ve kayması (≤15 bps), K=2 (+3×2 tanı), ADIM-0 fizibilite (n≥30, dolum_ts ≤%30 eksik), yol-tutarlı üç PK; kod YOK — operatör onayı bekler.
  Why: EDG-040 friksiyon sorusunun tick yarısı; tick arşivi 129 gün + trades.extra_json.dolum_ts ölçüldü.
  Ref: research/cards/EDG-2026-069-sinyal-tetik-dolum-tick-bacagi.yaml; EDG-2026-038/040/066.
- **[EDG-2026-070] pit-midcap-sagkalan-ust-sinir** — status: ACTIVE · owner: rol1 · size: — · trigger: —
  What: (ONAY 2026-09-03 sabah, operatör K2 → ACTIVE: ölçüm kodu KOVA C sırasında; eşikler donuk.) EDG-018 halefi (askıda kalır), ön-kayıt 2026-09-03 gece: aynı ADIM-0 kapısı (≥40 isim, ≥3 yıl; yeni bar kaynağı Alpaca IEX tarihsel), EDG-016 tasarımı PIT mid-cap sağkalan kohortuna, ÜST-SINIR damgalı, K=2 (+1×2 tanı); kod YOK — operatör onayı bekler.
  Why: TSK-065 (İCRA SIRASI ⑤) — delist-bar kilidi (B-DELIST-KAYNAK) para kararına sayısal girdi.
  Ref: research/cards/EDG-2026-070-pit-midcap-sagkalan-ust-sinir.yaml; EDG-2026-018/016.
- **[EDG-2026-071] hayalet-dugme-oneri-suzgeci** — status: ACTIVE · owner: rol1 · size: — · trigger: —
  What: (ONAY 2026-09-03 ~10:45Z, operatör → ACTIVE: ölçüm kodu KOVA C sırasında; eşikler donuk.) TSK-074 (C-9) ön-kayıt 2026-09-03 sabah: öneri katmanının bounds'ta olup motorda okuyucusu olmayan (hayalet) düğmelere bütçe harcadığı hipotezi; K=2 (tarihsel hayalet payı üretici kırılımıyla + sandbox yanlış-pozitif sayımı), ADIM-0 donmuş `hypotheses.jsonl` kopyası git blob'una, kill: kablolu 32 düğmeden biri süzülürse; yol-tutarlı PK (sentetik hayalet + gerçek okunan anahtar, gerçek öneri yolu). Kod YOK — operatör onayı bekler.
  Why: Ö-48'in asıl tamiratı; tasarım belgesi 2026-08-22 §4 Q1/Q6/Q7'yi ölçümle cevaplar.
  Ref: research/cards/EDG-2026-071-hayalet-dugme-oneri-suzgeci.yaml; docs/TASARIM-VIRGIN-KNOB-SUZGECI-2026-08-22.md; tests/test_hayalet_dugme_v263.py.
- **[EDG-2026-072] rejim-kosullu-cikis-onerisi** — status: ACTIVE · owner: rol1 · size: — · trigger: —
  What: (ONAY 2026-09-03 15:11Z, operatör → ACTIVE: ölçüm kodu KOVA C sırasında EDG-069/070/071'den sonra; eşikler donuk.) TSK-079 25c-1 ön-kayıt 2026-09-03 15:03Z (operatör: "kart-önce aç"): rejim-koşullu ÇIKIŞ override'ı (config.resolve_params + REGIME_EXIT_KEYS altyapısı kurulu, canlı boş; guard.classify_proposal Hermes önerisini reddediyor) düz sete karşı OOS kazanç verir mi — C-şasi (EDG-026) üzerinde H1/H2 hücreleri, K=2, eşik ΔP&L CI-alt>0 VE dd≤C×1,3 (EDG-033 emsali), kontrol bit-özdeşlik, yol-tutarlı PK (sentetik override bars_held'i düşürmeli). Kod YOK — onay bekler; benimseme adayı çıkarsa sevk kapısını açma dilimi.
  Why: EDG-030 rejim asimetrisi (trend_up 0,736 vs 0,057) vs EDG-033 boyut-çürümesi — çıkış için iki yönlü ölçüm.
  Ref: research/cards/EDG-2026-072-rejim-kosullu-cikis-onerisi.yaml; EDG-2026-030/033/026; meridian/config.py REGIME_EXIT_KEYS.
- **Retro kuyruk (README):** EAP large-cap **archived** (+9,0bps<30 eşik; PK geçti) · Insider CMP **archived** (pozitif-kontrollü 0) · Short-interest FINRA **archived** (12 hücre 0) · çıkış paketi P1/P2/P3 (K=3) **measured→shadow-accrual** · PEAD/rekonstitüsyon/sektör-takvim **archived** (kaynaklı; kill-list altta).

**⑤ RETIRED çapraz-doğrulama (`research/qc_dogrulama/`, 2026-08-09; üç kaynak):** 8 emekli sembol
(ANSS/DFS/FI/HES/IPG/K/PARA/WBA) — **yerel SP500-üyeliği 8/8 tutarlı** (her sembol delist gününden
önce üyelikten düşmüş, beklenen); **Massive delist-otoritesi 7/8'i gün-güne BİREBİR doğruladı** (vekil→
gerçek taşındı); hiçbir emeklilik kararı ÇELİŞMEDİ. Tek kalan QC-adımı: 1-hücrelik Security Master
delist-olayı fizibilite sondası (artık TEYİT, bilinmeyen değil) — §5-11.

### YAPMA LİSTESİ (kill-list — ölçülmüş/belgeli çürükler; tur harcanmaz; DOKUNULMAZ)

Araştırma-kaynaklı: PEAD (likit büyük-cap'te ölü) · overnight drift (2021 sonrası çöktü) ·
ay-dönümü (ABD'de kayboldu) · sektör-ETF trend (net edge marjinal) · VCP geometrisi (bağımsız
kanıt yok — ölçülebilir bileşenleri zaten skorda) · opsiyon verisi satın alma (öngörü kısa-bacak/
borç-ücreti kanalında) · equity-eğrisi otomatik risk kısma (momentum sistemini dipte kapatır;
yerine DD>1.5×beklenti insan-incelemeli alarm) · fractional Kelly (sabit-R zaten ~çeyrek Kelly;
üç aylık overbetting kontrolü yeter) · derin NN/geniş özellik uzayı (bu veri rejiminde overfit
tiyatrosu) · breadth birincil kapı (yalnız <%20 washout istisnası) · **yerel LLM kurulmaz**
(operatör kararı 2026-07-30: karar yolu deterministik → gecikme argümanı yok; gece yansıması
1-3 çağrı/gün → maliyet/fallback değeri ≈0; VM 2OCPU/12GB'da toplu iş zaten ölür; ileride yalnız
"Y6 toplu API maliyeti ısırırsa + anlaşma-ölçümü geçerse" koşuluyla yeniden açılabilir).
Kendi ölçümlerimizle çürüyenler: breakeven'ı erkene çekme (H1a) · min_score 80 (H2 — dilim
istatistiği tam replay'de tutmadı) · stm21 kısa-vade momentum (devir-koşullusu anlamlı NEGATİF —
Medhat-Schmeling bizde replike olmadı) · knob-bileşik çıkış paketleri mevcut R-yasası altında
(G3a: 3/3 ret — kuyruk kazanır ortalama kaybeder; dolar merceğiyle yeniden değerlendirilecek).

> **NOT (denetim E.2, 2026-08-13 — kill-list DOKUNULMADI):** yukarıdaki son satırın şart cümlesi
> ("knob-bileşik çıkış paketleri … **dolar merceğiyle yeniden değerlendirilecek**") artık TCA'ya
> bağlıdır: dolar merceği VAR ama **friksiyon-kirli** (EDG-037/038). Kill-list maddeleri
> **DEĞİŞMEDİ**; yalnız o şartın ne zaman sayılacağı netleşti — friksiyon defteri (WP1-B) kapanmadan
> "yeniden değerlendirme" yapılamaz.

## §7 KARAR GÜNLÜĞÜ (kronolojik; yeni giriş EN ÜSTE — tek satır + tarih; ayrıntı oturum kayıtlarında) _(eski: §5)_

- **2026-09-01 akşam — İKİ KAPI OPERATÖRCE AÇILDI + İKİ KURULUM İNDİ:** operatör (birebir): "9-10 için kur iznin var, kurulum penceresi de açık 13# için". ① TSK-009: 5 ayrık F9 dosyası (üç profil manifesti + kök SOUL/config) yedekli kuruldu; `meridian-aylik-bucket-kopya` service+timer İLK KEZ kuruldu, timer armed (3 Eyl 04:03Z) — elle test-ateşleme borcu SEANS-DIŞI (343MB okuma I/O). ② TSK-089 Faz 1: APISIX 3.18.0 (pinli) + etcd v3.5.21 docker'la kuruldu — 9080/9180/2379 YALNIZ loopback, admin 401/200 canary yeşil, sır A1-içi üretim (.env-apisix 0600, F9-dışı); rota SSoT `deploy/apisix/routes.yaml` + `ops/apisix_uygula.py` (idempotent + --denetle drift, ?ttl= yasak-assert'li; drift 0). ÖLÇÜLEN DERSLER: $env çözümü YALNIZ saf-referans alanda çalışır ("Bearer $env://X" karışık dizgesi ÇÖZÜLMEZ — Bearer env değerine taşındı); OpenRouter upstream hatasını 200 zarfında gövdeye koyabiliyor → HTTP-kod tabanlı fallback o sınıfı YAKALAMAZ (canary ① notu); gpt-oss-20b free katmandan kalkmış → yedek/hızlı = gemma-4-26b-a4b:free (farklı sağlayıcı = gerçek çeşitlilik). İçerik-smoke'u BORÇ: iki free ucu da akşam boğuk (nemotron timeout, gemma 429 — doğal 429 vakası ölçüldü); ilk sakin pencerede 200+içerik kanıtı alınıp Faz-1 kapanır. NOUS_ENDPOINT çevirisi (hermes'i kapıya bağlama) SEANS-DIŞI ayrı adım.
- **2026-09-01 — TSK-059 KAPANDI (aynı gün: hüküm→kod→ateşleme):** ts-revizyonlu hakem `edg042_hakem_2026-09-01/` indi (bölücü P-3'ten şasi-yükleyiciyle İTHAL — kopya çivisi `__code__.co_filename` ile; 26 çivi v359, 7/7 mutasyon); kart işaretçisi sha'lı çevrildi (içerik-adresli, görev koşucusu ayrışmada KOŞMAZ); İLK ATEŞLEME gerçek A1 çekimiyle: giris_once n=15 (tarihli tabanla birebir) · giris_1345 n=3 (taban+1, tedavi kolu birikiyor) · damga↔ts ayrışan 0 · tetik "orneklem_birikimde". İnşaen-boş kontrol kolu valfi böylece gerçekten açıldı; tetik hükmü tedavi kolu n≥10 dolunca (~4 hafta). Uygulamada doğan `damga_bilinmeyen` kova beyanı kartta.
- **2026-09-01 — EXE-009 P-2 KAPANIŞ HÜKMÜ (TSK-059 açıldı; yetki: operatör 85-aktarımı + P-3 ölçümü):** hakemin alt-bant bölmesi `pencere` damgasından gönderim `ts`sine geçer — bölücü `gonderim_kolu` P-3 reçetesinden İTHAL, sınır d8030c0 inişi; eşik/kill/success_metric TEK KARAKTER değişmedi (kova tanımı daraldı — P-3'ün aynı sınıfı, kill#2/#3'e girmediği kartta beyanlı). Kontrol kolu böylece n=2→15 (inşaen-boş valf açılır), tetik tedavi kolunu bekler (~4 hafta). Görev EK'i sabit-dizin işaretçisi karta devredildi ([2]'nin deseni). Öncülü: TSK-052 tahta hizalaması (EDG-062 hükmü işlenmişken satır ACTIVE kalmıştı — tek-kaynak ayrışması kapatıldı). Kod uygulaması ajan kaleminde.
- **2026-09-01 — TSK-058 İMPLEMENTASYONU İNDİ (SDD tam döngü: implementer → inceleme → 2 fix turu → re-review ONAY):** EDG-019 kill#1 kök çözümü — kadans içinde yalnız ucuz kuyruk-append (5,4-5,7 ms vs tam koşu 88-220 ms = 15-41×; gözetim maliyeti ayrı `gozetim_ms` alanında), üretim seans-dışı `ops/skill_gorus_uret.py`'de; EDG-063 LLM gölge üreticisi (`--llm`, çitli, kota 100/gün, şema-uyumsuz→ölçülemedi) aynı deftere. İnceleme hükümleri: `cikis` LLM'de kapalı (B1 — `karar` okuyan çözücü yok, `--yuzey` opt-in) · FDR ailesi üretici-başına (Ö2) · karışık üretici `det`e ÇEVRİLMEZ (`uretici=None + uretici_neden`, fail-closed) · çit normalizasyonu 10 ölçülü kaçışı kapatır (Ö5: ZWSP/Kiril homoglif/boşluk sınıfı) · birikim >14 seans obs.alarm (Ö1). 16/16 mutasyon kanıtı; birim çifti `meridian-skill-gorus.service/.timer` (07:30Z) F9'a kayıtlı. FAZ C (bayrak+dağıtım+ilk canlı koşum) seans-dışı pencereye kaldı. Yan ürün: TSK-093 (karışık-üretici ileri kalemleri) + TSK-094 (TSX çapa göçü — 36 çapa tek api.py bölgesine bakıyor, vaka bu turda ölçüldü).
- **2026-09-01 — EDG-067 ARŞİV INGEST'İ ZAMANLANDI (Rol-1, seans-dışı hazırlık):** korpus manifesti HEAD ac824e1c9'dan — 214 dosya / 3,6 MB (LOG + ROADMAP §7 kesiti + 80 kart + 132 docs; RUNBOOK üretilmiş→dışı beyanlı), her girdi blob-sha'lı, document_id=repo yolu (idempotent upsert). Betikler `research/olcumler/edg067_hindsight_faz1/` (taban kıyasının "AYNI korpus" kill maddesi manifest_uret ile tekrarlanabilir). Koşum A1'de tek-atım systemd-run `edg067-ingest` 20:05Z (seans-dışı şart kendiliğinden). Elle test-ateşleme yapıldı ("kurulu ≠ çalışır"): boyut-1024/defense/manifest kapıları geçti; ölçülen ders → API timeout 900→3600 sn (138KB belge 180 sn'de bitmiyor). Ayrıntı kartta (`ingest_plani_2026_09_01`).
- **2026-09-01 — HİNDSİGHT YÜKSELTMESİ CANLIDA (EDG-2026-067 kurulum bacağı TAMAM):** bge-m3 ONNX 1024/cls/prefix'siz + pgroonga 4.0.8 (yalnız hindsight DB) + reranker zinciri local(bge-reranker-v2-m3)→flashrank→rrf (ONNX/TEI yolları fiilen kapalı çıktı — ölçülü sapma kartta) + ApiKeyTenantExtension gün-1 (401/200 canary) + bank yeniden kurulumu + smoke 6/6 sağlık + pozitif/negatif/mükerrer kontroller yeşil. AYNI GÜN EK (operatör "docker kurabilirsin"): docker.io 29.1.3 + CP UI 0.9.2 pinli, yalnız 127.0.0.1+ACCESS_KEY+tenant-anahtarlı dataplane bağı; birim `hindsight-cp.service` F9'a kayıtlı. Bedel satırı: sıcak recall ~10,6 sn (8 aday cross-encoder 8,1 sn) — hüküm kartın maliyet sütununda. SIRADA: soru kümesi dondurma → arşiv ingest → taban kıyası.
- **2026-09-01 — CANLI TRİYAJ: meridian-learn kaçak yeniden-başlatma (operatör işareti "gene yüksek CPU"):** dün 20:43Z'de bilinçli durdurulan learn, 06:36Z'deki dağıtım adımının ÜÇLÜ stop/start paketiyle (`meridian meridian-barsarchive meridian-learn`) geri başladı ve ~4 saatte 6h40m CPU yedi (load ~3.2 — warmup_sprint kuraklığı boşa döndü). 10:37Z durduruldu (SIGTERM zaman aşımı→SIGKILL; `reset-failed` temizlendi); worker/barsarchive/hindsight etkilenmedi, load düştü. Kalıcı yeniden-başlatıcı YOK (birim disabled; tick-watchdog learn'ü izlemiyor) — tek seferlik reçete hatası. DERS (→ §4 TSK-092): dağıtım reçetesinin start satırı sabit üçlü paket olamaz; her birimin İSTENEN durumu (bilinçli-durdurulmuş dahil) korunmalı.
- **2026-09-01 — PARALEL ŞERİT BİRLEŞTİRİLDİ (operatör):** ayrı-şerit kavramı kapandı, tek konsolide sıra — TSK-062 (öğrenme-kilidi çifti) + TSK-065 (PIT mid-cap) ana İCRA SIRASI sonuna taşındı; slot geri-dolum bitişi, sıra 062→065; TSK-012/050/009/061 zaten sıra içindeydi, dokunulmadı. EK (aynı gün): üç araya-kalem (TSK-003 a-bacağı · TSK-005 ikinci bacak · TSK-020 `2-adım1`) İLK SIRAYA alındı — operatör: "bunları da ilk sıraya al".
- **2026-09-01 — HİNDSİGHT DERİN TARAMA + BRAINSTORM (operatör, 6 karar, soru-cevap turu):** ① autoRetain AÇIK — 2026-08-31 "her durumda kapalı" kararı DEVRİLDİ (araç takımı değişmedi: tek araç `hindsight_recall`; retain_async zorunlu, Memory Defense açık kalır, retain hacmi telemetriden izlenir) ② embedding/BM25 YÜKSELTME-ÖNCE: bge-m3 çifti + pgroonga arşiv-ingest'ten önce; EDG-2026-065 ölçülmeden EMEKLİ → yükseltilmiş reçeteyle yeni kart `EDG-2026-067` (işlendi 2026-09-01) ③ CP UI (9999) kurulur ama yalnız 127.0.0.1+ssh tüneli ④ arka plan LLM (auto-consolidation + mental model) AÇIK ve ANA MODELLE — kota telemetrisi ilk haftanın zorunlu ölçümü ⑤ `prefetch_method: recall` çivili + reflect tool-calling canary + API-key 401 testi ⑥ Hafıza sayfası TSK-091 (Hindsight dashboard'u bizim UI'da ayrı sayfa). AYNI GÜN EK (operatör "aynı şekilde"): APISIX gömülü dashboard kararı revize — kapalı değil TÜNELLİ + apply betiğine drift denetimi (TSK-089/090 güncellendi). SIRA REVİZYONU: kapı+hafıza hattı (TSK-091/089/090) TSK-060 ardına taşındı. Tarama: 3 bölge (kavram+API · kurulum/işletme · retrieval/olgunluk); ayrıntı TSK-060 gövdesinde.
- **2026-09-01 — TEK-KAPI MİMARİSİ (operatör onayı, tam doküman taraması sonrası):** genel API kapısı + LLM kapısı TEK bileşende birleşti — Apache APISIX (traditional+etcd, 3.18.x pin); Kong tedarik-zinciri gerekçesiyle kapandı (OSS imajları 3.10'da kesildi, hat 3.9.x bakım-modunda; öz-derleme teknik-mümkün/stratejik-ret), LiteLLM pilotu superseded (taslaklar commit'siz geri çekildi). Dört faz + 9 canary TSK-089'da; pano "Kapı sayfası" TSK-090'da (gömülü dashboard kapalı, konsolidasyon bizim UI'da). Kurulum operatör iznine kilitli ("kuruluma hemen geçme" yürürlükte). Tarama: 4 bölge + 114 plugin kataloğu, ~70 plugin gerekçeli elendi.
- **2026-08-31 — Backend mimarisi (operatör): 9 kalem karara bağlandı** — 6 uygula (sıra 8→4→2→1→3→9; telemetri Prometheus+Grafana), 2 tetikli kayıt, sır yönetimi beklemede. Zemin: Redis entegre ölçümü + daemon-yasağının yasa olmadığı ölçümü. Ayrıntı §4 havuz girdisi.
- **2026-08-31 — ÖĞRENME KİLİDİ ÇİFTİ SIRAYA ALINDI (operatör: 'duvarı yeniden sınayacak kartı sıraya al, burayı optimize etmemiz lazım'):** EDG-2026-064 ön-kayıtla açıldı — duvar (carpan=1, 93+ tur kilitli) süresiz ölçümden tarihli ölçüme döner; kademe grid + %80-tavan eşiği + yenileme politikası önden donuk; dürüst vaat cleared değil KAPSAMA (hermes'in kendi 2026-08-06 ölçümü korunur: bağlayıcı kısıt kapı, bütçe K-cezasını büyütür). Kayıtlı-ölçülmemiş EDG-058 (K-enflasyonu) AYNI pencereye sıralandı — kuraklığın iki kilidi tek koşum ailesinde ölçülür.
- **2026-08-31 — LLM KOTA BEYANI + İKİ KARAR (operatör):** filo için günlük 1000 LLM çağrısı hakkı beyan edildi (bugünkü kullanım ~%0,2; bağlayıcı kısıt maliyet değil operatör dikkati — kadans DEĞİŞMEZ). Kararlar: (1) teslim-öncesi ikinci-görüş geçişi kart adayı (§4); (2) beyan-only skill'lerin LLM ikinci görüşü — tek dalga iki kart (EDG-019 uygulaması + EDG-063 ön-kayıt), icra Ajan-A'dan sonra (§2 H1 + icra sırası). Ayrıca EDG-2026-062 dalgası İNDİ: suite 8105 yeşil + tek kırmızı (010 trial_ids) hedefli düzeltmeyle kapandı, push 054f822.
- **2026-08-31 — GİT KURALI GEVŞETİLDİ (operatör onayı, yalnız AJAN):** salt-okunur beyaz liste (`log·show·blame·diff·rev-parse·status`) SDD alt-ajanlarına açıldı; mutasyon komutları (stash dahil) ve YAN oturum tam yasağı aynen. Gerekçe ölçülü: aynı gün 2 zararsız salt-okuma itirafı + git'siz tarihçe-doğrulamanın inceleme kalitesine maliyeti; korunan zarar sınıfı (yan oturumun kendini Rol-1 sanması, 2026-08-26) yan-oturum yasağında yaşamaya devam ediyor. Künye CLAUDE.md §2/§3'te.
- **2026-08-31 akşam — AKIBET DEFTERİ TASARIM KARARLARI (brainstorm, operatör):** KAPSAM GENİŞ — dört kaynak tek defterde (N-serisi hermes önerileri · Rol-1 önerileri · bot teslim kalemleri · operatör fikirleri; kaynak alanıyla); KART HÜKÜMLERİ GİRMEZ (tek-kaynak — kart-açma önerisi girer, hüküm kartta). YETKİ KARMA: küçük/teknik kararlar Rol-1 (kayıtlı, itiraza açık), para/strateji/politika operatörde. SEF: değişenler detaylı (yeni doğan + karara bağlanan birer cümle), AÇIKLAR HER BRİFİNGDE yaş listesiyle tek kompakt satır (operatör "her brifingde"yi seçti — 14-gün eşiği önerisi yerine). YER: A1 state/ (olay-defteri sınıfı, günlük yedekli, git'siz; iki-kopya yasağı). HINDSIGHT: defter SSoT, `akibet` bank'i Faz-2'de buradan ingest (notlar-sayfasının akıbet bölümü + "neyi reddetmiştik" recall'u + mükerrer-önleme). N-serisi doğum kaydı improvement_proposals'ta KALIR (akıbet defteri yalnız karar/sonuç satırı taşır — kopya yok); kaynağı olmayan öneriler (Rol-1/operatör/bot-kalemi) doğum satırını akıbet defterinde alır.
- **2026-08-31 akşam — BOT-HAFIZA KARARI (brainstorm, operatör onaylı — üç turlu müzakere):** (1) Operatör dört amacı beyan etti (mükerrerlik · öneri akıbeti · trend/örüntü · süreklilikli diyalog) → Hindsight Faz-0 tetiği İLANLA ateşlendi, kurulum ÖNE çekildi (Ajan-A sonrası, A1-paralel). (2) DURUŞ REVİZYONU: "botlar Hindsight'a erişmez" mutlak yasağı kalktı — gerekçe-zinciri: Türkçe riski blokaj değil (multilingual resmî reçete + 24GB ile bge-m3 çifti gün-1 mümkün) · recall LLM-kotasız (lokal retrieval) · tools-modu "hatırlıyorum sanma" ilkesini ihlal etmeden kaynak-etiketli erişim verir. Sıra: Türkçe kartı → bot-recall kartı (tools canlı + context gölge), HEDEF `hybrid` (operatör: "context-modu da olması lazım") — context bacağı zarar ölçülmezse açılır. autoRetain HER DURUMDA kapalı; SOUL revizyonu kartla iner; bugün canlıda değişiklik YOK. (3) AKIBET DEFTERİ ön şart ve İCRA SIRASI'nda (Ajan-A sonrası ilk iş). (4) C-kapısı (öz-güncelleme: ders→öneri→ölçüm+onay→versiyonlu SOUL) yavaş halka olarak Faz-3'te. Tasarım §0/§3/§6 aynı gün revize. **EK (aynı akşam, 2. brainstorm turu):** hedef mimari NETLEŞTİ — "notlar sayfası + iste-getir": push'u provider değil HARNESS derler (bot başına reçete + token bütçesi + satır başına kaynak etiketi + kullanım-beyanı alanı), pull tek araç; botlar SINIRLI ajan döngüsüne geçer (operatör: "ajan döngüsü de işlesin" — araç takımı yalnız `hindsight_recall`, tavanlar önden donuk, maliyet farkı kartın zorunlu sütunu). Kart üç kollu: derlenmiş-sayfa / provider-autoRecall / hafızasız taban. **EK-2 (aynı akşam):** araç takımı GENİŞLETİLMEZ — operatör: "şimdilik araç konusunu genişletmeyelim, ileride elimizde daha çok veri olunca konuşuruz"; tek araç `hindsight_recall` kalır, yeni araç talebi veri-kanıtıyla yeniden açılır.
- **2026-08-31 akşam — MASA→PLAN TAŞIMASI (operatör, birebir: "FINVIZ/FMP/QC üçlüsü hariç diğerlerini de konsolide plana al"):** §5.0 masasının beş kalemi İCRA SIRASI'na alındı (①B-AJAN-GIT shim ②ana-beyin SOUL/config paketi ③Faz-6 kanıt bacağı ④sır yol-1 ⑤PIT mid-cap sağ-kalan) — her birinde OPERATÖRDE KALAN çekirdek beyanlı (onay/koşum/para); FINVIZ/FMP/QC + delist-kaynak para ailesi masada. B-AJAN-GIT'in beklediği karar bu taşımayla VERİLMİŞ sayıldı (kimlik araç inince kapanır).
- **2026-08-31 — FİLO YÖNETİMİ HÜKMÜ (operatör 'internal MCP gerekir mi' sorusu, plana işlendi):** yeni MCP sunucusu ŞİMDİ değil — mevcut `meridian/mcp_server.py` ajan→sistem yönünü zaten taşıyor; orkestratör→filo boşluğu `ops/filo.py` (Ajan dalga-A ile birlikte iner — İCRA SIRASI güncellendi) + Ajan-B köprüsüyle kapanır; MCP yayını ikinci-istemci TETİĞİNE bağlandı (§4). YAGNI: daemon'suz araç önce.
- **2026-08-31 — İKİ OPERATÖR KARARI: bot sunum modeli ULTRA + pano AJAN YÜZEYİ (A→B, dört muhatap).** (1) 'İkisini de ölç' talimatıyla A1'de canlı-anahtar A/B koşuldu (2 model × 3 senaryo, gerçek gün verisi): Ultra dört eksende üstün/eşit, Super gizli akıl-yürütmeye token yakıyor — üç profil Ultra'ya geçti ve CANLIYA YAYILDI (profile update ×3 + kuru-koşum test-ateşleme ×3 RC=0; harness-içi kanıt bekci state.db: ultra-550b). 08-27 bütçe belgesinin 'Ultra sığmaz' hükmü tam-üretim varsayımına bağlıydı, güncellendi. (2) Telegram anlaşılırlığı: SOUL'lara 'ilk satır sade özet' kuralı; pano 'Ajan' bölümü kararı — dalga-A salt-okunur akış önce, dalga-B sohbet duruş çivileriyle ardından; muhataplar üç bot + ana hermes beyni. İcra sırası satırı revize edildi.
- **2026-08-31 — @bekci'nin İKİ DURAN'ı TRİYAJLANDI: ikisi de İYİ HUYLU, hipotez doğrulandı** (A1 ölçümü): `broker_reconcile.json` 08-28 Cuma 20:31'de yazılmış — mutabakat KADANSINDA (hafta sonu seans yok, bugünün EOD turu henüz gelmedi); 08-24'te bir `reconcile_failed`+atlama kümesi var, sonra düzelmiş — `reconcile_atlandi` olayının kesilmesi atlamanın BİTMESİ. `mirror_cancel_sinif_dokumu` ise KOŞULLU olay (yalnız süpürme koruma-sınıfına dokununca yazılır, `alpaca.py` kaynağından ölçüldü) — son iki seans koruma emrine dokunulmamış. DERS (bekçi iyileştirme adayı, §4): 'atlandı/skip' sınıfı olayların YOKLUĞU çoğu kez İYİLEŞMEdir — duran dedektörü bu sınıfı ayırt etmiyor; kural yazmak kod işi, kartsız küçük kalem. Aynı turda ÜÇ BOT SOUL'una ölçülen-arıza üslup bloğu eklendi (terim çevirme yasağı — '0 ship'→'gemi' vakası · kısa-cümle disiplini · kelime uydurma yasağı).
- **2026-08-31 — BOT ROSTER CANLIDA: üç profil kuruldu, test-ateşlendi, İLK KARNE indi** (operatör kurulum bloğunu koştu — uzak-sudo Rol-1 izin sınıfında engelliydi; kanıt journal'da: üçü status=0, LLM katmanı çalışıyor, teslimler damgalı). goal.yaml'ın dört sorusu İLK KEZ cevaplandı (sharpe KALDI, kalanlar GEÇTİ/ölçülebilir). TRİYAJ NOTU: @bekci ilk taramada reconcile_atlandi olayının 157 sa'tir GELMEDİĞİNİ raporladı — hipotez: 'atlandı' olayının kesilmesi reconcile'ın artık atlanmayıp KOŞMASI olabilir (08-29'da 10/10 broker_teyit damgası basıldı — akış canlı görünüyor); doğrulaması sonraki triyaj kalemi. mirror_cancel_sinif_dokumu duranı da aynı sınıf. WP12 bacak-1 kapandı; kalan bacak Faz-5 rol seçimi (kilidi açıldı: canlıda bot değer kanıtlıyor).
- **2026-08-31 — AÇIK KALEMLER Rol-1'e DEVREDİLDİ** (operatör, 85-aktarımı; birebir: "bunların hepsini main'e devret main yapsın, bu worktree sadece haftalık görevinde kalsın"). Kapsam: P-2/`ts` (tahta + §5 KOVA-2) · görev-EK sabit-dizin işaretçisi · seyrelme kart adayı (§4). 85 oturumu yalnız haftalık EDG-042 görevinde; not: o oturum worktree değil ANA CHECKOUT'ta koşuyor (yan oturum disipliniyle).
- **2026-08-31 — P-3: K1 AYRIK, anahtar `ts`, ara işaret YOK** (operatör). Bedel bilerek: hüküm ~14 hf'ye kayar, saflık > hız. Kart `p3_karar_ayrik_ts_2026_08_31`; P-2'nin çerçevesi değişti (iki kart, iki anahtar — beyanlı ayrışma).

_**[2026-08-31 DURUM DENETİMİ — BU BÖLÜM KALEM TAŞIMAZ.]** Burası kronolojik neden-kaydıdır: her giriş OLMUŞ bir şeyin kaydıdır, açılıp kapanan bir kalem değil. Bu yüzden maddeleri durum işareti taşımaz ve `/api/roadmap` onları `belirsiz` sayar — **bu doğrudur**: "işaretsiz" burada "denetlenmemiş" değil, "durumu olan bir kalem değil" demektir. Denetim 165 girişi kalemi bu gerekçeyle rozetsiz bıraktı; kaynak: `docs/DENETIM-ROADMAP-2026-08-30.md`._

- **2026-08-31 §7'NİN 2026-08-29/30 BOŞLUĞU DOLDURULDU — 24 GİRİŞ, HEPSİ COMMIT GÖVDESİNDEN TÜRETİLDİ (operatör istedi):** tahta bakım turu boşluğu ölçmüştü — §7'nin en yeni girişi 2026-08-29'du, oysa `2701cf4`…`6dd38b5` arasında 24 tur inmişti (hermes bot roster programı Faz 1-4 · `:free` fiyatlama ailesi #14/#16/#17/#18 · bayat bytecode kapısı #20 · pencere damgası P-1 · yasa katmanlaması · CLAUDE.md yeniden yazımı) ve neden-kaydı yalnız commit gövdelerinde yaşıyordu. **Hiçbir yeni hüküm verilmedi:** her giriş kaynak sha'sını taşır ve her cümlesi o gövdede ya da gösterdiği ölçüm dosyasında yazılıdır; zaten kayıtlı iki tur (`177a92b`, `6b9c6ad`) TEKRARLANMADI. Blok başında **köken notu** var — girişlerin turların kendi anında değil sonradan yazıldığı gizlenmiyor, çünkü kronolojik bir defterin geriye dönük doldurulduğunu söylememek defterin kendi sözleşmesini bozardı. Kapanan tahta satırı `§8.T`/I'ya taşındı (kendi kuralımız: kapanan satır tahtada durmaz).

- **2026-08-30 TAHTA BAKIM TURU — 27 SATIRLIK BORÇ ÖDENDİ, BANNER'LA DEĞİL TAŞIMAYLA (`§8.T`/`§8.O`/`§8.H` açıldı):** §2'nin açık bölümleri 48 satır taşıyordu ve **25'i kapalı, 18'i işaretsizdi**; dört tur üst üste satırları taşımak yerine üstlerine "bu satır bayat" notu düşmüştü (2026-08-13 · 08-22 · 08-23 · 08-24) — 2026-08-24 denetimi borcu 27 satır diye ölçmüş ve bedelini de yazmıştı (*o gece iki ajan turu zaten kapalı kalemlere gitti*), altı gün ödenmedi. Bu tur 49 tablo satırı + iki banner bloğu §2'den, iki kova gövdesi §5'ten, üç kapanmış öneri §4'ten arşive TAŞINDI (metin bayt-özdeş; dönüşüm betikle yapıldı ve betiğin kendi kapısı üç iddiayı doğrulamadan dosyayı yazmıyor: taşınan her satır çıktıda bayt-özdeş bulunur · yerinde kalan satırlarda yalnız ilk hücreye rozet eklenir, gövde değişmez · beyansız yeni satır çıkamaz). SONUÇ (aynı ayrıştırıcıyla ölçüldü — `/api/roadmap`): §2 açık bölümleri **48 → 25 satır**, kapalı **25 → 0**, işaretsiz **18 → 0**. Yeni çivi `v337` kuralı kalıcı kılar ve üç mutasyonla ısırdığı gösterildi. Aynı turda tahtada satırı OLMAYAN dört açık kalem de kayda geçti: `EXE-2026-009` P-2 + `EDG-2026-042` P-3 operatör kararları (§5 KOVA 2) · §7'nin 2026-08-30 boşluğu · ayrıştırıcının kelime-içi `KAPALI` eşlemesi · §6 kart indeksinin diskle ayrışması (73 kart ↔ §6'nın beyan ettiği 50). Denetim kaydı: `docs/DENETIM-ROADMAP-2026-08-30.md`.

_(**KAYIT KÖKENİ — DÜRÜSTÇE İŞARETLİ:** aşağıdaki 24 giriş turların KENDİ ANINDA değil,
**2026-08-31'de commit gövdelerinden türetilerek** yazıldı. §2 TAHTA'nın 2026-08-30 bakım turu
boşluğu ölçmüştü: §7'nin en yeni girişi 2026-08-29'du, oysa `2701cf4`…`6dd38b5` arasında 24 tur
inmişti ve neden-kaydı yalnız commit gövdelerinde yaşıyordu. Her girişin sonunda kaynak sha var;
her cümle o gövdede ya da onun gösterdiği ölçüm dosyasında yazılıdır — **bu blokta hiçbir yeni
hüküm YOKTUR.** İki tur zaten kayıtlıydı (`177a92b` pencere damgası teşhisi, `6b9c6ad` EDG-042
koşum #2) ve TEKRAR YAZILMADI.)_

- **2026-08-30 FAZ 4 PLANI — `@karne`: `goal.yaml`'IN SORDUĞU DÖRT SORUYU BUGÜN HİÇBİR TESLİMAT
  CEVAPLAMIYOR:** canlı ölçüm — `goal.yaml` dört soru soruyor (`target_return_30d` · `min_sharpe` ·
  `max_drawdown` · `failure_below`), `watchdog.goal_failure_report` yalnız ARIZA anında konuşuyor ve
  `goal_failure` olayı defterde **sıfır** kez var: "hiç başarısız olmadı" ile "rapor hiç konuşmadı"
  ayırt edilemiyor. `@karne` sessizliği bilgiye çevirir ("ölçtüm, başarısız değil" ≠ "ölçemedim").
  Substratın üçüncü kullanımı (@bekci kalıbı birebir); bilinçli tek sapma **SUSMA-YOK** — rapor botu
  alarm botu değildir, dikkat bütçesi haftalık kadansla korunur. Tek-kaynak bağlar: `failure_below`
  hesabı `watchdog`dan ÇAĞRILIR, kopyalanmaz. (`6dd38b5`)

- **2026-08-30 `EXE-2026-009` **P-1 KAPANDI** + `EDG-2026-042` K1 İZDÜŞÜMÜ BAYAT ÇIKTI:** kod
  dağıtıldı ve canlı defterde DE/PANW satırları 1345→1330 düzeltildi — bakım penceresinde, worker
  durmuşken (kuru koşu `duzeltilen=2` → YAZDI → idempotens `0/2`). **Kill#3 istisnası ADIYLA yazıldı:**
  düzeltme uydurma değil, iki ÖLÇÜLMÜŞ olgunun (gönderim `ts` + canlı `barclock` mtime) deterministik
  karşılaştırması ve operatör istisnasıyla — yazılmasaydı kill kriteri sessizce çiğnenmiş olurdu (yan
  oturumun uyarısıydı, haklıydı). Hakem bandı beklendiği gibi kaydı: 1345 n=2 · 1330 n=2, ikisi de
  n<10. Aynı commit'te `Ö-54`ün "K1 ~3-4 hafta" izdüşümü BAYAT ilan edildi: +4'ün 2'si artık var
  olmayan kaydırma-öncesi yoldan geliyordu; ileri hız yalnız 1345 yolu (0,40 dolum/seans) → pooled
  ~6,5 hafta / ayrık ~14 hafta. Eski satır SİLİNMEDİ, tarihli düzeltme eklendi. (`83bc47b`)

- **2026-08-30 `EDG-2026-042` **P-3 KARAR HAZIRLIĞI** — K1 KARIŞIK ÖRNEKLEM, OPERATÖRDE:** yan
  oturum hazırladı, Rol-1 devraldı. `HAZIRLIK-` öneki bilinçli — karar VERİLMEDİ, dolayısıyla belge
  `KARAR-*.md` raf desenine girmesin (yan oturumun kendi yakaladığı Yasa-6 kuzeni). Karar inince
  gerçek KARAR belgesi + kart işlemesi Rol-1'dedir. Aynı commit P-1 kodunun dağıtımını taşıdı
  (`state/dagitim.json`, 18:29Z). Belge: `docs/HAZIRLIK-P3-K1-KARISIK-ORNEKLEM-2026-08-30.md`. (`dcef1c6`)

- **2026-08-30 YASALAR KATMANLANDI — İKİ TERFİ, BİR HAYALET SERİ, BİR İŞARETLİ ZORLAMASIZLIK
  (operatör kararları):** **Tek-kaynak** ve **Bedel** yasaları sözleşme katına TERFİ etti; PIT
  yasağının mekanik zorlamasızlığı İŞARETLENDİ ve çivi işi açıldı (operatör onaylı). Ölçümler: Yasa
  1-3 ve 5 hiçbir yerde tanımlı DEĞİL (**hayalet seri** — yeni yasa numara almaz), Yasa 4/6 tarihî
  kimliktir (680 atıf, yeniden adlandırılmaz), PIT yasağının `guard`/`codelaw`/testlerde SIFIR
  karşılığı var. Aynı turda §10'a eksik superpowers eklendi (subagent-driven-development ana kalıptı
  ve yazılı değildi) ve §3'e ek-iş yönlendirmesi girdi (varsayılan alt ajan; worktree üç tetikle).
  Günlüğe suite ruling'i kayıtlı: `90f6cdc` turu **1 failed / 7714 passed** — kırmızı bilinen
  alet-gürültüsü sınıfı (negatif kontrol %37,1, aradığı etkinin üç katı; aynı ağaçta 5/5 izole koşum
  yeşil). Eşiğe ve kill-list'e dokunulmadı. (`0c83fe6`)

- **2026-08-30 PENCERE DAMGASI GÖNDERİM ANINA BAĞLANDI — DAMGASIZ SATIR DAMGASIZ KALIR:** yan
  oturumun devir paketi, Rol-1 doğrulayıp commit'ledi; operatör hükmü 2026-08-29 ("damgayı gönderim
  anına bağla, iki satırı da düzelt") — bu commit birinci yarı (kod). Arıza ölçülmüştü: `pencere`
  damgası dolum yamasında, yani satır DEFTERE YAZILIRKEN basılıyordu; gönderim ile yazım arasına bir
  dağıtım girince ikisi ayrıştı ve hakemin 1345 bandı %50 kontamine oldu (gerçek n=2). Damga artık
  gönderim satırında (`mirror_submit_armed`) basılır; dolum yaması damgaya DOKUNMAZ — ne yeniden
  yazar ne eksiği tamamlar. Düzeltme öncesi gönderilmiş satırın rejimi defterden okunamaz ve
  UYDURULMAZ (E2 ikame yasağı sınıfı). Eski sözleşmeyi çivileyen test silinmedi, HÜKME çevrildi.
  (`90f6cdc`; devir `docs/DEVIR-PENCERE-DAMGASI-2026-08-30.md`)

- **2026-08-30 PR #20 BİRLEŞTİ — BAYAT BYTECODE KAPISI (36 ÇAĞRI YERİ KAYNAKTAN DERLEMEYE GEÇTİ):**
  yan oturumun işi. `spec.loader.exec_module` `__pycache__`e bakar ve pyc'yi yalnız (tam-saniye mtime,
  bayt boyutu) çiftiyle doğrular — **boyutu değiştirmeyen** bir düzenleme aynı saniyede kalırsa BAYAT
  bytecode kaynağın yerine koşar; testler kaynağı değil ÖNBELLEĞİ ölçer. Üç kollu pozitif kontrolle
  ölçüldü: 16 çiftin kontrol kolunda 16/16 kırmızı, bayat kolda 15'i yeşil = kusur gerçek, 1
  ÖLÇÜLEMEDİ ("kusur yok" YAZILMADI); üretim tarafında 19 çağrı yerinin 17'si kusurlu. Önkoşul da
  gerçek: depo tarihindeki 1116 `.py` değişikliğinin 18'i (%1,6) boyut-koruyan. **Kapının değeri aynı
  gün ölçüldü:** dal `main`e rebase edilince 18. örnek (`test_spend_defter_duzeltmesi_v331.py`, o tur
  main'de doğmuştu) anında kırmızı verdi. `meridian/` altına dokunmadı (diff boş). (`d9b7a74`;
  dal `fcf2112` + `a0a81e9`, devir `docs/DEVIR-BAYAT-BYTECODE-2026-08-30.md`)

- **2026-08-30 `CLAUDE.md` YENİDEN YAZILDI — KURALLAR ARTIK EYLEM ANINDA TETİKLENİYOR:** operatörün
  şablonu temel alındı (eylem-anı kapı tablosu · muafiyet kuralı · açık öncelik zinciri korundu),
  üstüne üç kaynak işlendi: mevcut yasanın ölçülmüş vakaları, mühendislik günlüğünün **14 yazılmamış
  kuralı + 6 çelişkisi**, ve o oturumun dersleri. Şablonun iki olgusal hatası ÖLÇÜMLE düzeltildi —
  "`.claude/` versiyonlanır" YANLIŞTI (`.gitignore` dışlıyor, izli dosya 0; **cloud klonunun kural
  almamasının kökü buydu**) ve "suite 18-50 dk" bayattı (6 koşum: 25:57-26:07, 7.696 test). (`e17867a`)

- **2026-08-30 FAZ 3 — İKİNCİ BOT `@bekci`, VE ROL SEÇİMİNİ ÖLÇÜM DEĞİŞTİRDİ:** spec `@hipotez`i
  "en büyük ölçülmüş boşluk (5 günde 0 hipotez)" diye işaretlemişti; o ölçüm DEFTERE bakıyordu. Canlı
  döngü başka şey söyledi: saatte **40 aday değerlendiriliyor, 0 geçiyor** — 36'sı "AYIRT EDİLEMEZ",
  çünkü sonda bütçesi 10 ve `k_max` 2, ikisi de **duvar=1**'e çakılı ve o duvar **93 turdur**
  sorgulanmamış. Sistem hipotez KITLIĞI değil **istatistiksel GÜÇ** çekiyor; eşiğin kendi metni
  "K=40 aday cezası dahil" dediği için daha fazla hipotez eşiği SIKILAŞTIRIRDI — `@hipotez` bugün
  ölçülebilir biçimde ZARARLI olurdu ve ertelendi (duvarın yeniden sınanması ön-kayıt kartı + operatör
  kararı ister). `@bekci` süregelen ve DURAN durumları fark eder; tespit DETERMİNİSTİK (Python), model
  yalnız SIRALAR — listeyi üretmediği için arıza UYDURAMAZ ve ölçülemeyeni SUSTURAMAZ. Bu turda
  **bedel yasası** doğdu: gürültüyü azaltan değişiklik ne KAYBETTİĞİNİ de ölçmeli. Canlıda hiçbir şey
  yaratılmadı/etkinleştirilmedi. (`5449a83` plan + `7d0e307` uygulama)

- **2026-08-30 TUR KAPANIŞ NOTU — DÖRT PR'IN KÖK NEDENLERİ + İKİ "YEŞİL AMA YANLIŞ" VAKASI:** tek bir
  ölçüm kusurunun (`price_for` alt-dizge tablosu; canlıda 13 çağrı / 7.89 USD uydurma maliyet)
  arkasından üç mekanizma daha geldi — #14 `:free` soneği · #16 seçicinin ölü kapıları · #17 kartın
  sağlanamaz donmuş girdisi · #18 defter onarım betiği. İki sahte-yeşil ancak GERÇEK koşumla görüldü:
  **harness'in "exit code 0"ı sarmalayıcının son `echo`udur, pytest'in kodu DEĞİLDİR** (iki kez
  yanılttı: biri gerçekte `PYTEST_RC=1`, biri SIGTERM'lü 143) ve **16 çivi yeşilken onarım betiği
  komut satırından hiçbir şey yapmıyordu** (`parse_args([] if argv is None else argv)` → `sys.argv`
  atılıyordu; çiviler `main([...])` çağırdığı için görmedi). İkisi de bugün `CLAUDE.md` kuralıdır.
  (`ac26f6b`, #19)

- **2026-08-30 `spend` DEFTERİ ONARIM BETİĞİ — VARSAYILAN KURU KOŞU, YAZIM AÇIK BAYRAKLA:**
  `price_for` düzeltmesi (#14) yalnız GELECEK satırları düzeltir çünkü `dagit.sh` rsync'i `state/`i
  DIŞLAR — canlı defterdeki 13 satır (7.89 USD uydurma maliyet) dağıtımdan sonra da yanlış kalırdı ve
  `spend.over_budget()` üç ücretli yolu o sayıyla besliyor. Sözleşme emsalden (`ops/sermaye_beyani_iade.py`):
  kuru koşu VARSAYILAN · `--uygula` yazar · `--zorla` canlı-worker kapısını aşar. Dar ve denetlenebilir:
  yalnız `_is_free_variant` VE `cost_usd>0` satırlar, `cost_usd` yeniden HESAPLANIR (sabit 0 yazılmaz),
  satıra `duzeltme` alanı düşer — sessiz düzeltme yok. **Canlıda KOŞULMADI.** (`edc4729`, #18)

- **2026-08-30 KORUMA KANCASI ARTIK BAŞLIĞININ SÖZÜNÜ TUTUYOR — `state/` YAZIMI GERÇEKTEN KAPALI:**
  kanca başlığı "`state/` altına YAZMA" diye bir yüzey ÜSTLENİYORDU, hedef deseni ise yalnız adı
  sayılan yedi aileyi blokluyordu. Ölçüm: `state/` altında 87 dosya, 24'ü üretim kodunca yazılıyor ve
  korumasız kalanlar arasında **`trades.jsonl` (işlem defteri)**, `equity_curve.json`,
  `scoreboard.json`, `trade_plans.jsonl`, `notify_undelivered.json` vardı — `portfolio.json` KORUMALI
  ama `trades.jsonl` DEĞİLDİ, oysa ikisi aynı sınıf kanıttır. Hüküm: **kapsamı genişlet, başlığı
  indirme** — başlığı gerçeğe indirmek işlem defterindeki bir deliği BELGELEMEK olurdu. Fazla
  bloklamak ajana GÖRÜNÜR ret verir, az bloklamak kanıtı SESSİZCE tahrif eder. (`de5de29`)

- **2026-08-30 FAZ 2 — İLK BOT PROFİLİ `@sef`: ÜÇ TESLİMAT TEK BRİFİNGE, VE MODEL TESLİMATIN ÖNKOŞULU
  DEĞİL:** roster'ın ilk Hermes profili repo tarafında eksiksiz; **canlıda hiçbir şey yaratılmadı ve
  etkinleştirilmedi**, operatöre üç ayrı eylem kalıyor ve `deploy.sh` üçünü de adıyla basıyor. Taşıyıcı
  kısıt: **LLM SIRALAMA katmanıdır, TESLİMAT katmanı değil** — model zaman aşarsa, çöp dönerse ya da
  profil hiç kurulmamışsa HAM birleşik brifing yine gider; bir alarmı modele bağlamak, model
  yavaşladığı gün alarmı da susturur. Model alarmı SÜRESİZ erteleyemez: ardışık sessizlik tavanı
  aşılınca mesaj zorunlu gider. Denetimin açtığı üç sessiz delik kapandı; ilki: profil kimlik kapısı
  yalnız `config.yaml`ın VARLIĞINA bakıyordu, artık DURUŞ ölçülüyor. Rol seçimi de ölçümle yapıldı —
  `@nobet` elendi (ayırt edici yarısı ikinci bir bot token'ı ister ve token bir sırdır).
  (`0f8535d` plan + `8dba332` uygulama)

- **2026-08-29 FAZ 1 DENETİMİ KAPANDI — KURULUM İLE TESLİMAT AYRILDI, VE YASA GÖREMEDİĞİ HEDEFE HÜKÜM
  VERMEYİ BIRAKTI:** dal-sonu denetimi "landing'e hazır, ETKİNLEŞTİRMEYE değil" dedi. **Beyanı kod
  tutmuyordu:** `deploy.sh` brifing timer'ını KOŞULSUZ enable ediyordu ve `cutover.sh` onu çağırıyordu
  — ilgisiz bir sebeple koşan tek bir dağıtım, kimsenin karar vermediği günlük Telegram kadansını
  açardı. Kurulum (zararsız) ile etkinleştirme (teslimat) ayrıldı; kapı `is-enabled` üstünde. İkinci
  ders: **`codelaw` göremediği hedef hakkında hüküm veriyordu** — çapa deseni yalnız taban adı
  yakalıyordu ve `research/olcumler/.../olcum.py:178` diyen dört çapa `ops/olcum.py`ye çözülüp
  yargılanıyor, o satır tesadüfen kod olduğu için SESSİZCE yeşil veriyordu. (`cd2f6ba`)

- **2026-08-29 FAZ 1 · GÖREV 3 — ÖLÇÜM ARACI OLAY ADINI ARTIK TAHMİN ETMİYOR, VE TAMLIK İDDİA ETMİYOR:**
  vaka: canlı teşhiste olay adı iki kez tahmin edildi, iki kez **sahte sıfır** alındı
  (`pozisyon_adet_benimsendi` → gerçek ad `adet_benimsendi`; `position_drift` → o bir ALAN) ve sahte
  sıfır "arıza yok" diye okunur. Araç artık adı KODDAN çıkarır. Asıl ders bu değil: dört review turu,
  aracın kendi varlık sebebini DÖRT KEZ ihlal ettiğini buldu ve dördü de canlıda ateşleyen GERÇEK
  alarmlarla kanıtlandı — regex yalnız LİTERAL argümanı görüyordu (`obs.ALARM_MIRROR_DRIFT` görünmez;
  canlıda 51 teslim edilmemiş `MIRROR_DRIFT` varken "OLAY YOK" diyordu) · alıcı `obs` diye
  sabitlenmişti (`from . import obs as _obs` idiyomu, 44 çağrı yeri, hem görünmez hem SAYILMIYORDU).
  (`460cde1`)

- **2026-08-29 FAZ 1 · GÖREV 2 — HESAPLANAN TESLİM EDİLİR OLDU (ALARM YIĞINI + ÖNERİ BRİFİNGİ KADANSA
  ASILDI):** ölçüm — sistem hesaplıyor, kimse okumuyordu: `notify_undelivered.json` **310 alarm**
  (`MECHANISM_STALE` 208 · `MIRROR_DRIFT` 51 · `NAKED` 9) · `ops/alarm_backlog_digest.py` yazılmış,
  çalışıyor, **hiçbir kadansa asılı değil** · `improvement_proposals.jsonl` 16 yapısal öneri, teslimat
  yolu YOK. `ops/oneri_brifingi.py` + günlük timer (21:00 UTC) ikisini de koşar; şekil bilerek
  kopyalandı — kuru koşum varsayılan · BOŞKEN SESSİZ · teslimden SONRA damga · teslim düşerse damga
  BASILMAZ ("karar döndürmeyen zamanlanmış iş bildirim spam'idir"). Review iki sessiz-düşürme deliği
  buldu; `ts`siz satır `"" > ""` yüzünden HİÇ bildirilmiyor ama `toplam`a SAYILIYORDU. (`26df0cc`)

- **2026-08-29 BÜTÇE VE POLİTİKA ARIZALARI "BİÇİM BOZUK" DİYE YAZILIYORDU — SINIF ÜÇ BEYİN AYAĞINDA DA
  KAPANDI:** tavana çarpan ya da reddedilen cevap defterde `unparseable` oluyordu; yanlış ad yanlış
  düzeltmeye çağırır. **Kök neden tavan değil YAPISALDI:** üç ayakta da `finish_reason`/`stop_reason`
  incelemesi `if not text:` bloğunun İÇİNDEYDİ ve kesilen/reddedilen cevap BOŞ DEĞİLDİR — o ayrıma hiç
  uğramıyordu. Canlı kanıt: nemotron ailesine 13 çağrının 7'si tam `out_tokens=4000`de bitmiş (%54).
  Kesilme + red kontrolü artık metin kontrolünden ÖNCE; red SEZGİ değil BEYAN (`stop_reason`), sezgi
  silinmedi çünkü reddi beyan etmeyen sağlayıcılar için hâlâ tek yol. Sağlayıcı farkları bilerek
  korundu (Anthropic düşünce tokenını ayrı alanda BİLDİRMEZ → claude detayında `reasoning=` yazılmaz,
  bir çivi bunu kilitler). **PR kendi kusurunu dört kez düzeltti ve dördü de kayıtta.** 28 çivi
  (v325-v329), her biri düzeltmeden ÖNCE kırmızı görüldü; 17 mutasyonun 17'si yakalandı. (`76519a1`)

- **2026-08-29 ÜCRETSİZ KATMAN OPUS FİYATINA YAZILIYORDU — KURAL SATICI ADINDAN DEĞİL `:free`
  SONEĞİNDEN TÜREDİ:** canlı `state/spend.jsonl` ölçümü — 13 çağrı, **7.89 USD harcanmamış para**
  deftere ve panoya yazılmış (uydurma yasağı ihlali). Kök neden: `price_for` model adını `PRICES`
  anahtarlarıyla ALT-DİZGE eşleştiriyor, canlı slug hiçbirini tutmuyor ve muhafazakâr varsayılana —
  tam olarak Opus listesine — düşüyor. Tabloya `nemotron`/`nvidia` **EKLENMEDİ**: arızayı TERSİNE
  çevirirdi (aynı satıcının ÜCRETLİ varyantları 0'a fiyatlanır, bu kez HARCANMIŞ para deftere hiç
  girmezdi). `:free` OpenRouter'ın kendi sözleşmesinde "ücreti sıfırdır" demektir → yarın eklenen
  ücretsiz model adı hiç bilinmeden doğru fiyatlanır. Eşleşme alt-dizge değil **segment**tir. Bedel
  pano rakamından büyüktü: `spend.over_budget()` üç ücretli yolu kapatır ve tamponun ~%39'u yenmişti.
  Çivi ÖNCE yazıldı (11 kırmızı / 8 yeşil çürütme bacağı); mutasyon 4/4 öldürüldü. (`8fe683c`, #14)

- **2026-08-29 `EDG-2026-059`'UN DONMUŞ GİRDİSİ ÇALIŞMA AĞACINDAN GIT BLOB'UNA TAŞINDI — YAPISAL
  ÇELİŞKİ, TEK SEFERLİK KAZA DEĞİL:** kartın kill kriteri girdinin ÇALIŞMA AĞACINDA donmuş kalmasını
  şart koşuyordu, ama bir çivi `docs/RUNBOOK.md` her değiştiğinde AYNI dosyanın yeniden üretilmesini
  ZORUNLU kılıyor — ikisi aynı anda sağlanamaz. Girdi kart hiç koşulmadan **üç kez** kaybolmuştu
  (08-24 → 08-25 → 08-26 ×2); kart yazıldığı gün fiilen koşulamaz hâle gelmişti. Girdi artık
  **içerik-adresli bir git blob'u**: çalışma ağacı istediği kadar yeniden üretilsin, blob değişmez ve
  COMMIT'ten de bağımsızdır. Değişen girdinin ADRESLENMESİ, değişmeyen girdinin KENDİSİ (blob'un
  içerik sha'sı kartın 2026-08-24'te kaydettiğinin ta kendisi). Kartın kendi öngörüsü ("çapa sınıfı
  kapandı, tekrar BEKLENMİYOR") TUTMADI ve SİLİNMEDİ — üstüne tarihli düzeltme yazıldı. (`d030511`, #17)

- **2026-08-29 SEÇİCİNİN ÜÇ KAPISI DA ÖLÜYDÜ — `${#DIZI[@]-0}` GEÇERSİZ, HATA DA ÖLÜMCÜL DEĞİLDİ:**
  `ops/etkilenen_testler.sh`ta üç yerde bash'in kabul etmediği sözdizimi (`${#parametre}` varsayılan-değer
  soneki almaz) → `bad substitution`; betik `set -e` KULLANMADIĞI için hata ölümcül değildi, `[[ ]]`
  başarısız sayılıyor ve kapı **sessizce "false"** oluyordu. Üç `if` hiç değerlendirilmedi. En
  tehlikelisi küresel dosya kapısıydı: `tests/conftest.py` (7 autouse fikstür → 7183 testin hepsi) ya
  da `pyproject.toml` değişince "TAM SUITE GEREKLİ" DEMİYOR, 111 dosyalık dar küme öneriyordu.
  (`c7a13b5`, #16)

- **2026-08-29 FAZ 1 · GÖREV 1 — AJAN YAPILANDIRMASI DEPOYA ALINDI, GÜVENLİK DURUŞU ARTIK BEYANLI VE
  ÇİVİLİ:** `~/.hermes/config.yaml` bugüne dek YALNIZ CANLIDA duruyordu ve `dagit` F9 onu izlemiyordu
  — verilen izin kararlarının depoda evi yoktu, sürüklenme sessiz olurdu. Duruş: `approvals.mode: smart`
  · `cron_mode: deny` (başsız cron tehlikeli komutu ONAYLAMAZ) · deny listesi `*dagit.sh*` · `git push*`
  · `git commit*` · `*systemctl*` · `*serve.sh*` (`--yolo`da bile geçersiz). Terminal arka ucu BİLEREK
  `local` bırakıldı, gerekçesi dosyada: konteyner arka uçlarında Hermes'in KENDİ tehlikeli-komut
  denetimi atlanır. (`1922638`)

- **2026-08-29 ÖN-UÇUŞ TARAMASI — SDD ÇALIŞMA ALANI NE İZLENİYOR NE DIŞLANIYORDU:** Faz 1'e
  başlamadan yapılan çakışma taraması dispatch'ten ÖNCE bir tuzak buldu: `.superpowers/` ne
  `.gitignore`daydı ne `dagit`in `RSYNC_EXC` listesinde. İki ayrı zarar, ikisi de bu depoda ölçülmüş
  sınıflar — kirli ağaç `dagit.sh [0a]` kapısını düşürürdü · **rsync `.gitignore` OKUMAZ**, yalnız
  kendi listesini okur, yani SDD artefaktları CANLI İŞLEM KUTUSUNA giderdi (`scratch-panov2` vakasının
  birebir tekrarı). (`ccb5d98`)

- **2026-08-29 FAZ 1 UYGULAMA PLANI — VE PLAN YAZARKEN SPEC'İN BİR HEDEFİ ÖLÇÜMLE ÇÜRÜDÜ:**
  `writing-plans` ile üç görev, her biri TDD adımları ve gerçek kodla (placeholder yok). Spec §3 "310
  alarm + `self_review` + `improvement_proposals` → TEK brifing" diyordu; plan yazarken ölçüldü:
  `notify.configured()` **True** (kanal AÇIK) · `notify_suppressed` 10 / pencere 21600 sn (hız sınırı,
  arıza DEĞİL) · `selfreview.weekly()` `scheduler.py`de asılı ve ZATEN `notify.send()` çağırıyor ·
  yalnız `alarm_backlog_digest.py` hiçbir kadansa asılı değil. Hedef ölçümle daraltıldı.
  (`64ac6be`; plan `docs/superpowers/plans/2026-08-27-faz1-bot-roster.md`)

- **2026-08-29 AJAN GÜVENLİK DURUŞU ÖLÇÜLDÜ — ÜÇ AÇIK KALEM KARARA BAĞLANDI, VE ÖLÇÜM BİR BOŞLUK DAHA
  ÇIKARDI:** canlı A1'de `approvals` HİÇ TANIMLI DEĞİL (varsayılana düşüyor) · `terminal` tanımsız
  (local, konteyner izolasyonu yok) · `security` tanımsız · `pre_tool_call` → `ops/meridian-guard.sh`.
  Kanca iyi bir mekanizma (`state/` yazımını, `secrets.json`u, `autonomy_level`i ve Alpaca emir
  gönderimini sert blokluyor) **ama kendi şerhinde beyanlı**: parse edilemezse FAIL-OPEN, asıl savunma
  desen eşleşmesidir — kalkan değil desen filtresi. (`dc91b7e`)

- **2026-08-29 ROSTER SIRALAMASI DÜZELTİLDİ — DIŞ KANIT KENDİ PLANIMIZI ÇÜRÜTTÜ:** bağımsız bir
  kaynağın (Hermes Agent eğitimi, 303 segmentin tamamı okundu) altıncı hatası bizim planımızın ta
  kendisiydi — *"building profiles before workflows: do not create five specialist agents before you
  know what those specialist agents are actually here to do."* Kaynağın yedi günlük planı da aynı
  sırayı veriyor (gün 3 BİR skill · gün 5 KARAR döndüren BİR zamanlanmış iş · gün 6 BİR subagent akışı
  · gün 7 İLK uzman profili); bizimki "ilk dalgada 7 profil" idi. Sıra tersine çevrildi: **iş akışı
  ÖNCE, profil SONRA.** (`2701cf4`)

- **2026-08-29 `pencere` DAMGASI YALAN SÖYLÜYOR + HAKEM VALFİ AÇILAMIYOR — ÜÇ AÇIK KALEM (`EXE-2026-009` P-1/P-2, `EDG-2026-042` P-3):** "K1 medyanı neden yükseldi" sorusu kovalanınca yükselişin kaydırmadan ÖNCE gönderilmiş satırlarda da olduğu görüldü; teşhis (`research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/`, salt-okuma) damganın gönderim değil DEFTERE YAZIM rejimini bastığını ölçtü (DE/PANW `ts=08-21T20:32Z` eski yol, damga "1345" — 1345 bandı %50 kontamine, gerçek n=2) ve `oneri_tetigi`nin iki bant şartı yüzünden 1330 kolu asla dolmayacağından geri-al önerisinin İNŞAEN erişilemez olduğunu gösterdi. Üçüncü kalem: K1 iki icra mekanizmasını tek medyanda topluyor ve kural boşluğu eşik dolmadan (n=17/30) kapatılmalı. HÜKÜM YOK, eşik/karar kuralı hiçbir kartta değiştirilmedi (kill#2); üç kalem de operatörde.

- **2026-08-29 `EDG-2026-042` HAFTALIK KOŞUM #2 — İLK ANLAMLI TEKRAR (`Ö-54`):** üç kovada da eşik yine dolmadı → hükümlü koşum TETİKLENMEDİ, CI yok, `status: measuring` sürüyor; K1 n=13→17/seans 4→7 (medyan +15,0→+29,8 bps — yeni dört satırın dördü de büyük pozitif), ÇIKIŞ KOVALARI İLK KEZ ÖLÇÜLEBİLİR (`broker_teyit` damgası basıldı, 10/10 teyitli): K2 n=6 medyan −4,2 · K3 n=4 medyan +0,9, ikisinde de tek-seans şerhi zorunlu. Betimleyici gözlem (HÜKÜM DEĞİL): giriş bacağı başabaşın [5-15] ÜSTÜNDE, çıkış bacakları modelin ALTINDA. Reçete olarak R2 (`edg042_recete_short_2026-08-24/`) kullanıldı — zamanlanmış görev metni 2026-08-22'yi işaret ediyordu, KART kazandı (10/10 long olduğu için sayı farkı yok, ama seçim karta göre yapıldı). Pencere hakemi (EXE-2026-009): 1330 n=0 · 1345 n=4 → `orneklem_birikimde`, geri-al önerisi YOK.

_(2026-08-10…13 BOŞLUĞU KAPATILDI 2026-08-13 — denetim A15: en yeni giriş 2026-08-09'du, oysa arada
karar penceresinin UYGULANMASI, `max_drawdown` operatör kararı, tohum yenilemesi, TCA hükümleri ve
v237-v243 dağıtımları vardı; hepsi yalnız §4 maddelerinin İÇİNDE yaşıyordu ve §4 temizlenince
neden-kaydı da silinecekti. Aşağıdaki girişler madde başına TEK SATIRDIR; ayrıntı kartlarda/§3'de.)_


- **2026-08-24 İKİNCİ DAĞITIM — PANO YENİDEN YAPILANDIRILDI (`fc67d30`, 11:48Z):** otoriter tam suite **6751 passed / 0 failed**; kapıların tamamı yeşil, `goal.yaml` bayt-özdeş kopyalandı, canlı uçtan uca doğrulandı (yedi yüzey · `page-analiz` kabı · yeni seri jetonları · huni varsayılan görünüm · IC üçlüsü üç ayrı renkte · iki birim active · healthz ok). **BEŞ YÜZEY YEDİ OLDU** (operatör, onaylanan maketin kenar çubuğu gruplaması): eski tek "Karar" SEKİZ bölümle şişmişti ve içinde ÜÇ AYRI soru vardı → ② Portföy (kitap·mutabakat·seans-içi emir) · ③ Karar zinciri (aday·kapı·onay) · ④ **Analiz** (toplulaştırma·birikim defteri — operatörün adıyla istediği sekme). Kart bütçesi BÖLÜNDÜ, artmadı: 11+10+4 = 25. Ayrıntı: `docs/KARAR-2026-08-24-C-YUZEY-TAKASI.md`.
- **2026-08-24 PALET: "GRİ GÖRÜNÜYOR"UN KÖK NEDENİ HUE DEĞİL AÇIKLIKMIŞ — ve maketin paleti İKİ GÜVENLİK ÇAKIŞMASIYLA reddedildi.** İlk teşhisim ("merdiven yanlış hue'da") yanlıştı; maketin paletini dört yüzeye taşıdım, iki ölçüm çürüttü: `--lavender` #7c3aed **`--mod-canli` ile BİREBİR AYNI HEX** (canlı-para çipiyle grafik serisi aynı renk olamaz) ve Dub'ın `--blue`/`--sapphire` değerlerini **`--nav`/`--nav-2` ZATEN kullanıyor** (ROL 6). `index.html`in kendi yorumu bunu yazmıştı; okuyup üstünden geçtim. Gerçek kusur merdivenin ilk basamağının L\* 19,3'te olmasıydı — tek-seri grafikler tam onu kullanıyordu. Merdiven serbest bantta KALDI, yukarı kaydı (L\* → 28,1), altı kısıtın altısı yeniden ölçüldü. **DERS: rezerve hue bandı (mod/nav/şiddet) bir estetik tercih değil bir güvenlik kaydıdır; palet turu ona ÖNCE bakmalı.**
- **2026-08-24 Ö-39 KAPANDI (`plan_atif.jsonl`):** LLM görüşünün hangi künyeyle damgalandığı artık append-only defterde; yazar `hermes`, tüketici `analytics.llm_opinion_calibration["model_kirilim"]`. `backfill_opinions` künyeyi eskiden HİÇ okumuyordu — Ö-39'un canlı kanıtı oradan çıkmıştı. Künye ailesinin (31a·31b·40·39) son bacağı.
- **2026-08-24 BULGU · D6 KORPUSU BİRİKİMLİ KAYMA (Ö-sınıfı, kart AÇILMADI):** `olcum_sonucu.json` D6 korpusunu 151 blok / 56.249 karakter beyan ediyor; bugünkü korpus **197 / 99.740** — karakterde **+%77**. Her tazeleme KENDİ deltasını denetlemiş, birikimli kayma hiç sorulmamış. DESIGN.md'deki D6 sayıları (cpl_medyan 78,0 · x-yüksekliği 7,448px) damgalı ve damga dürüst; ama girdi artık damganın anlattığı girdi değil. CPL satır-başına bir özelliktir ve korpus BÜYÜKLÜĞÜNE bağlı olmak zorunda değil — ama bu bir SAVUNMA ve 2026-08-07'den beri ölçülmemiş. Borç: `research/olcumler/tipografi_rampa_2026-08-07/TAZELEME-2026-08-14.md` §üçüncü tazeleme.
- **2026-08-24 TEŞHİS · ISINMA MERDİVENİ TEK YÖNLÜ KİLİTLENDİ (davranış DEĞİŞTİRİLMEDİ):** canlı `warmup_scale` yedi gündür `carpan=1, duvar=1`; 154 koşumun HEPSİ aynı bütçede. Kök neden: `duvar` yalnız daraltma dalında atanıyor (`carpan//2`) ve `carpan ≤ duvar` olduğundan **monoton azalır — onu yükselten hiçbir yol yok**; 1'de yutucu (`1 < min(1,8)` daima False). Duvarın BAYAT olduğunun kanıtı elde: 154 koşumun hepsi `kesildi: false`. İkinci kusur SESSİZLİK — `warmup_budget_scaled` yalnız değişimde log basıyor, yedi gündür tek satır yok. **Onarım kart ister ve bu belge kartı AÇMAZ:** merdiveni açmak sonda sayısını artırır → K büyür → ön eleme eşiği SIKILAŞIR (EDG-058); etkinin YÖNÜ belirsiz. `docs/TESHIS-2026-08-24-ISINMA-MERDIVENI.md`.

- **2026-08-24 DAĞITIM YAPILDI VE CANLIDA DOĞRULANDI (`a7928601`, 02:44Z):** otoriter tam suite **6701 passed / 0 failed** (25dk 55sn) — ilk turdaki tek kırmızı (RUNBOOK satır-çapası çürümesi) emsal protokolüyle kapatıldı. Kapılar: temiz ağaç · uv audit · lint-imports · import taraması · `bounds.yaml`/`goal.yaml` canlı↔repo BİREBİR · sekiz systemd birimi birebir · F9 altı artefakt birebir · **SIFIR silme**. Canlı doğrulama uçtan uca: `meridian`+`meridian-learn` active · `/api/topviews` 200 (13,1 KB) · `/api/market?seri=1` 200 (292 KB) · `/api/bars/AAPL` 200 · `inter-vf.woff2` 200 (39,4 KB) · canlı HTML'de `--sans:'Inter'` + `--bg:#fafafa` + **183 `.pv-` bileşen kuralı** · healthz ok. **KURU KOŞUM DENETİMİNDE BULUNAN SIZINTI:** `scratch-panov2/` beş girdiyle canlıya gidiyordu — yerelde `.gitignore`'lu ama **rsync gitignore OKUMAZ**, yalnız `RSYNC_EXC` listesini okur; iki mekanizma ayrı. `scratch-*` globu eklendi (betiğin kendi `head -40`'ı listeyi kestiği için ancak 628 satırın tamamı üretilip denetlenince görüldü). **AÇIK:** `meridian-aylik-bucket-kopya.service/.timer` hiç kurulmamış (sudo — operatör işi) · `research/olcumler/*/state_*/bars` sembolik bağları mutlak yerel yola işaret ediyor, Linux'ta sarkık.
- **2026-08-24 GECE KARŞIT-DOĞRULAMA TURU (2 icra çifti · 1 kapandı · 1 düştü):** her icra iddiası bağımsız doğrulayıcıyla karşılandı — `EDG-2026-056` **doğrulanarak KAPANDI** (izole ağaçta yeniden üretim BYTE-AYNI, sha `c1092218…`; hüküm kırılmaya çalışıldı, kırılmadı), `EDG-2026-053` **"kapandı" iddiası DÜŞTÜ → kısmen** (aşağıda). Ayrıca tahtanın **8 satırı bayat** çıktı (M8-U2/U3 · M11 kova-6 · F8 · EXE-009 · WP7-31a/b · M11 Ö-3/Ö-4 · 26-değer-eşitliği P0-b/P2 · [8.'si girdi kesik]) — hiçbiri iş değil, tahta bakımı. **K3/K6 dosya çakışmasından koşulmadı; K4/K5'in kaydı hiç ulaşmadı.** Ayrıntı: `docs/GECE-TURU-2026-08-24-ROADMAP.md`.
- **2026-08-24 `EDG-2026-053` (GELİR MOMENTUMU) KOŞULDU — HÜKÜM YOK, KART AÇIK KALIR (blok birimi Rol-1'e düşer):** ölçüm zanaatı sağlam (dört nokta tahmini panelden bağımsız birebir yeniden üretildi; şasi sha'ları 050 ile aynı; PK geçti; karta dokunulmadı; gerçek PIT ihlali de bulunamadı) **AMA karar kuralı mekanik olarak çözülmedi**: kart "21g blok-bootstrap" derken şablon birimi **işlem günü**ydü (EDG-050), bu ölçümde **ay-sonu** okundu → blok ≈ 21 ay, `n_blok=10`. **Birim tersine dönünce hüküm de dönüyor:** blok=21'de "hiçbir dal eşleşmedi", blok=1'de `ivme_ust_30pct @60g` CI `[+0,000086; +0,008653]` 0-DIŞI ve net10bps=+0,003473>0 → **DAL-1 ATEŞLEME şartı TAM eşleşiyor**. Kırılganlık şerhi yalnız **zayıflatan** yönü yazmış (YASA 4 sınıfı tek-yönlü sunum). Tek 0-dışı hücre (`yoy@20g lo=+0,000330`) ay-düzeyi çıkarımda 0-İÇİ (t=1,58; NW t=1,34…1,55), blok genişliği ters yönde daralıyor (0,005552→0,003124) ve permütasyon sınamasında `lo>0` oranı 0,27 → **sıralama gürültüsünden ayırt edilemiyor**. PIT "yıkıcı sınaması" **totolojik** (`f(x)` vs `f(idempotent_filtre(x))` → ihlal 0 çıkmak zorunda, kanıt değeri sıfır). Kart sonrası eklenen `BAYAT_CEYREK_GUN=200` guard'ı 2.388 gözlem düşürdü, **duyarlılık koşusu yok** (ikinci serbest parametre). Depoda `edg053`'e değen **hiçbir test yok** — kapanışı hiçbir kapı korumuyor. **AÇILIŞ ŞARTI: (1) blok biriminin adlandırılması, (2) her iki okumanın karar tablosuna yazılması, (3) 200g guard duyarlılığı, (4) gerçek yıkıcı PIT sınaması.**
- **2026-08-24 `EDG-2026-056` (SPLIT ORAN-İMZASI) ÖLÇÜLDÜ — HÜKÜM: YETERSİZ, dedektör KABLOLANMAZ:** aday 55 · eşleşen 32 · yakalanmayan 60/92 → **YP %41,8 · yakalama %34,8**, çıta (YP≤%20 VE yakalama≥%80) **DÜŞTÜ** → *"imza tek başına yetersiz — körlük BEYANLI kalır"*; `grep ratio_signature|oran_imza meridian/` = **0** (motor temiz). Eşik donukluğu `stat birth==mtime` ile kanıtlı (tolerans 02:58:55, yer gerçeği 02:59:30, test 02:59:51 — hepsi ölçümden ÖNCE), karta ve `state/`e dokunulmadı, ELEME-WP4 belgesi **append-only** güncellendi. Hüküm üç yoldan zorlandı, kırılmadı: merdivenin üç basamağı da düşüyor (F=1,25/1,5/2,0) ve yapısal YP'ler (3:2 bandı, 8 aday) tamamen silinse bile YP=%31,9>%20. **İKİ SAYI KUSURU DÜZELTİLECEK:** `RAPOR.md:45` "92 olay / **61** sembol" → doğrusu **60** (61, `bars_integrity`'nin tüm-sınıf `sembol_sayisi`'dır); `RAPOR.md:128` *"hepsi 3:2 bandına düşüyor"* → **yanlış**, hayalet(5)+sıçra-dön(8)+3:2(7) düşünce **3 aday sınıflandırılmadan kalıyor** (CMCSA 2006-10-24 · CMCSA 2013-12-19 · DLTR 2012-06-26) ve hiçbiri o bantta değil. **İKİ TESCİL BEKLİYOR:** ters-split yönünün dahil edilmesi (karta AYKIRI ama ölçümden önce beyanlı + karşı-olgulu) ve hacim toleransı **F=1,5**'in icadı (kartta yoktu, "kart boşluğu" diye donduruldu) — ikisi de hükmü taşımıyor, Rol-1 tescili gerekir.
- **2026-08-24 PANO DUB DÖNÜŞÜMÜ İNDİ (operatör onaylı maket → üretim):** `KARAR-2026-08-24-B`. Sekiz GARANTİ (ölçüm dürüstlüğü · kontrast AA · CSP · iki tam tema · rol ayrılığı) Dub'a RAĞMEN sabit tutuldu; geri kalan her şey KARAR ilan edildi. İki çatışma Dub'ın KENDİ jetonuyla çözüldü, uydurmadan: saf beyaz zemin → `#fafafa` (Dub uygulama zemini, P9 parlama kısıtı korundu) · `#000000` eylem dolgusu → `midnight-ink #0a0a0a` (Dub DESIGN.md'nin kendi yazılı değeri). Gece paleti Dub'da YOK → türetildi ve damgalandı. Rol katmanı kırılmadı, **ALTINCI rol açıldı** (gezinme/seçim = `electric-blue`). İnen bileşenler: metrik sekmeleri · çok serili alan grafiği · birleşik akış kartı (zincir ↔ Sankey huni) · satır-içi kıvılcımlar (Y1) · aday karar çekmecesi (Y2) · **Top Views** üç sekmeli aile kartı (Y3) · huni % + karekök beyanı (Y4). Sadeleştirme: aynı sayıyı iki yüzeyde gösteren altı yüzey teke indi, hiçbir sayının TEK okuyucusu kaldırılmadı. Veri katmanı: `/api/market?seri=1` · `/api/bars/{ticker}` · `/api/topviews` (dokuz facet TEK paydadan, PF ilk kez ölçülü). Suite: bkz. aynı gün dağıtım kaydı.
- **2026-08-24 `ÖE1` ŞİDDET MERDİVENİ ÇÖKMESİ — KARARIN KENDİ KUSURU, ÖLÇÜLEREK DÜZELTİLDİ:** palet ataması Dub `tangerine` (41,1°) ile türetilmiş kırmızıyı (38,4°) **2,7°** arayla bırakıyordu; AA türetmesi ikisini aynı renge çökertiyordu (ΔE2000 **5,39**) ve sev-2↔sev-3 luminans oranı **1,004**'tü — ayrım tamamen protan/deutan'ın sildiği eksende. **Hiçbir mevcut test bunu göremezdi** (v197 rol AYRILIĞINI, v153 KONTRASTI ölçer; "iki seviye ayırt edilebiliyor mu" diye soran yoktu). Eşik ölçümden ÖNCE donduruldu (§9.3: komşu luminans oranı ≥1,20 — renk körlüğünün silemediği tek kanal — VE ΔE2000 ≥15, iki temada). Üç aday sırayla ölçüldü: Dub hue'ları 5,39 TUTMADI · ara çözüm 13,53 TUTMADI · §9.4 Omega ailesi **22,75-32,43 TUTTU**. Kök neden YAPISAL: lavanta MOD'a, maviler ROL 6'ya ayrılınca Dub'da şiddet için iki hue kalıyor. İkinci bulgu: Omega üçlüsü AYNEN alındığında da eşiği tutmuyor → **hue ailesi ne olursa olsun luminans merdiveni zorunlu**. Rol-1 bağımsız doğruladı (1,255/1,247 gündüz · 1,247/1,255 gece). **§9.5 çivisi eklendi** (v197 §10, 7 test) — bu kör nokta bir daha sessiz kalamaz.
- **2026-08-24 YAZI TİPİ: KARMA DEVRALMA (Inter ALINIR, Geist Mono ALINMAZ):** `HUKUM-2026-08-24-YAZITIPI.md`. Operatör indirmeye yetki verdi; Inter v4.1 ve Geist Mono v1.7.2 resmî kaynaktan indirildi, OFL 1.1 lisansları METİNDEN doğrulandı (üst-kaynakla bayt-aynı). **Geçerlilik kapısı geçti**: donmuş 2026-08-07 tabanı birebir yeniden üretildi (Geist 0,92/0,57 · Recursive Mono 1,00/0,817). Bulgu İKİ YÖNLÜ: sans'ta Inter kazandı (`1`/`l` @28px 0,968 vs 0,931 · `0`/`O` 0,774 vs 0,663), mono'da Recursive kazandı (0,817 vs **0,570**, cihazın gerçek dpr'ında 0,708 vs 0,576). Geist Mono kesitinde ayrıca `₺` ve `✓` YOK. **Kaybedilecek taraf panonun PARA TAŞIYAN yüzeyi** ve Geist'te telafi edecek OpenType özelliği yok → alınmadı; 2026-08-07 hükmü çürütülmedi, DOĞRULANDI. `ss02`/`cv01` kesitte KORUNDU: `l`/`I` 0,500 → **0,930**. Bütçe 77,6/120 KB. **Satoshi ALINMADI** (§8): ITF FFL v2.0 kesit almayı ADIYLA yasaklıyor, depoya commit BELİRSİZ, ve panonun en büyük başlığı 28px iken Dub'ın kendi kuralı Satoshi'yi 36px altında yasaklıyor — ekranda sıfır karakter çizerdi. İkilisi `.gitignore`'da, lisans+ölçüm depoda.
- **2026-08-24 `edg032c` KÜNYESİ TAZELENDİ — bit-nötrlük KANITLANDI (iddia değil ölçüm):** `EDG-057` künye kapısında durmuştu. Kaynak ölçüldü: `broker.py`/`guard.py` yorum-only, `strategy.py` `06a6cff`'te 36 KOD satırı ve commit "bit-nötr" İDDİA ediyordu. Protokol koşuldu: **üç yönlü bayt-özdeşlik** (taban ↔ kosum1 ↔ kosum2) dört kanonik defterde; beşincisi (`sonuc`) yapısal olarak özdeş olamaz (şasi koşum kimliği yazar) → farkı alan alan ölçüldü (tam beş alan) ve on ölçüm bloğu iki yönlü derin-eşit. Üç karıştırıcı koşumdan ÖNCE elendi (bars donuk · EDG-022 config birebir · şasi birebir), yani ayrışma olsaydı geriye tek değişken kalırdı. Künyeye YALNIZ `motor_sha256` + `kunye_tarihcesi` yazıldı; 15 alan dokunulmadı (bağımsız doğrulandı). Kapı emsalin ötesinde sıkılaştırıldı.
- **2026-08-24 `EDG-2026-057` (LEADING_SECTOR KAPISI) ÖLÇÜLDÜ — GÖZLEM ÇÜRÜTÜLDÜ, kapının POZİTİF değeri KURULMADI:** kartı doğuran gözlem "kapı kârlı planları reddediyor" diye okunabilirdi (REVIEW'a rağmen işleme dönen 52 plan +3,09R/PF 1,16). Kart kimsenin seçmediği dilimi ölçtü: n=156 karşı-olgusal işlem, ortalama R **−0,146**, CI95 ay-kümeli **[−0,266, −0,026]** — TAMAMI sıfırın altında. **`peek_beyani`'nın (b) şıkkı — SEÇİM YANLILIĞI — ayakta kalan hipotezdir.** Altı kill temiz, üç PIT sınaması geçti, iki koşumda `sonuc.json` bayt-özdeş. **AMA kartın "CI-üst<0 → KAPI HAKLI" kuralı ateşlemesine rağmen hüküm KURULMADI:** ölçüm sırasında bulunan REJİM BÜTÇESİ AYRIŞMASI (donmuş kasada 52 plan gününde `exposure_budget_pct`=0 → 75 `regime_flip` çıkışının **49'u İLK BARDA**, kohortun ~%31'i kasa artefaktıyla zorla kapanıyor; tabanın kendi replay'i bu planları hiç silahlandırmazdı) −0,146'nın ne kadarının edge olduğunu ölçülemez kılıyor. Ayrıca `counterfactual.py`'nin sınıf yasası geçerli sayıldı. **Kapı gevşetilmez — ama bu karar kanıtlanmış değere değil, KANITIN YOKLUĞUNA dayanıyor.**
- **2026-08-24 "SİSTEM ÖĞRENMİYOR" TEŞHİSİ ÇÜRÜDÜ — karşıt doğrulama bir hatadan kurtardı:** `HUKUM-2026-08-24-OGRENME-KURAKLIGI.md`. `warmup_sprint` saat başı birebir aynı `cleared:0` basıyordu; teşhis "kapı yapısal olarak erişilemez" dedi. İki bağımsız şüpheci manşeti yıktı: **İKİ AYRI KAPI KARIŞTIRILMIŞ** — resmî ship kapısı (`reflect.py:1325`, `record_erosion=True`, tek yol) `probes_tested` kullanıyor (pratikte 1) ve eşiği **0,80**; 0,995 yalnız döngü-içi ÖN ELEMEye ait. Kapı 2026-08-14'te GEÇİLDİ (H00057, p=0,9295), düştüğü terim K değildi. "Maks ölçülen P=0,799" yanlış defterden (`arming_measured` = canlı silahlandırma organı); doğrusu **0,941**. Döngü kapanmış: strategy v5, incumbent OOS 0,0853→0,2687. **Ve bugünkü sıkılık ölçülmüş bir kusurun ONARIMI** — eski formül K=16'da tavana çarpıyordu, kodun kendi beyanı "40 null adayda aile-bazlı yanlış geçiş %87" diyor. **Teşhis üzerine hareket edip eşiği indirmek sistemi ölçülebilir biçimde bozacaktı.** Ayakta kalan üç kalem (telemetri sınıfı): ön elemede K enflasyonu → `EDG-2026-058` kartına bağlandı · `warmup_scale` ölü kilidi (`1 < 1`) · `sprint_run.py` iz süzgeci **DÜZELTİLDİ** (reddin gerekçesi artık silinmiyor). **`meridian-learn` 7 gündür 16 Ağustos bytecode'u koşuyordu — restart edildi** (00:34:40Z; emir yolunda değil, saf hesap süreci).
- **2026-08-24 S2R "GENEL BAKIŞ ÖZETTİR" ADR'si AŞILDI — çivi silinmedi, DARALTILDI:** yeni yerleşim Bugün'e bir kanıt tablosu koydu. Karar öncesi ölçüldü: gövdede jenerik detay satırı **0**, eski kart grameri **0**, tablo **1** (açık pozisyonlar, paydası maruziyet bütçesiyle sınırlı). ADR'nin korktuğu "sınırsız detay dökümü" gerçekleşmemiş. `test_genel_bakis_SINIRSIZ_detay_dokumu_tasimaz` üç sınırı ayrı ölçer. `KART_TABANI` ratchet'inin İLK aşağı hareketi (karar 27→26) beyanla yapıldı — sebep SİLME değil TAŞIMA.
- **2026-08-24 IMPECCABLE DENETİMİ 18/20 — iki kalem düzeltildi, ÜÇ YANLIŞ POZİTİF elendi:** `DENETIM-IMPECCABLE-2026-08-24-PANO.md`. Düzeltilen: hedef boyu 23px → 24px (WCAG 2.2 AA 2.5.8) · 375px'te alarm ölçülerinin kırpılması. **Elenen yanlış pozitifler kayda geçti** (ikisi a11y, biri güvenlikle ilgili görünen "HALT mobilde erişilemez" — gerçek düğme 53×44 ve erişilebilir; seçici gizli bir `<option>` yakalamıştı). Dedektörün `overused-font:Inter` bulgusu BEYANLI yanlış pozitif (brief pinliyor + Inter ölçümle kazandı). `flat-type-hierarchy` KISMEN GERÇEK ve açık kalem: 33 kural 10/12px'i MONO ile kullanıyor (meşru imza idiomu) ama **26 kural SANS ile** ve sans rampasının başlığı 11px.
- **2026-08-24 `v214` ÇÜRÜK SATIR ÇAPALARI KAPANDI:** beşi de `broker.py:263`ü gösteriyordu; kök neden aynı günün M11 damgalarının `broker.py`yi ~270 satır büyütmesi (`PaperBroker.equity` 263→533, çapanın ÜÇÜNCÜ çürümesi). İki sınıf ayrı işlendi: canlı çapa → SEMBOL, anlatı → görünür `çapa-mezar-taşı` işareti (bir test `broker.py:263` dizgisinin KALMASINI şart koşuyor). İlk denemem yeni çürüme üretti ve geri alındı; ikinci deneme satır sayısını KORUYARAK yapıldı.
- **2026-08-22 `EDG-2026-042` HAFTALIK TAKVİM İLK FIRE (`Ö-54`):** üç kovada da eşik dolmadı (K1 n=13/4 seans, K2/K3 ölçülebilen n=0 — beş çıkış adayının beşi `broker_teyit` damgasız) → hükümlü koşum TETİKLENMEDİ, CI yok, `status: measuring` sürüyor; snapshot aynı günkü ara-koşumla bayt-özdeş olduğu için ÖNCEKİNE GÖRE DEĞİŞİM SIFIR (Cumartesi — takvimin çalıştığının kanıtı, yeni kanıt değil; ilk anlamlı tekrar 2026-08-29). ÖLÇÜM-ÖNCESİ REÇETE DÜZELTMESİ: donmuş `olcum.py`nin K2/K3 işareti kartın DÜZELTME formülüyle çelişiyordu ve MADDİ hataydı (LEHTE dolumu aleyhte yazardı) — teyitli satır 0 iken kart lehine düzeltildi, eşik/karar kuralı değişmedi, donuk reçete `edg042_kosum_2026-08-22/`ya taşındı.
- **2026-08-24 PANO ENVANTERİ (786 satır, 39 tablo) + ROL-1'İN ÜÇÜNCÜ DÜZELTMESİ:** yüzey haritası çıkarıldı (259 CSS sınıfı, 2.322 emisyon, 4 ayrı kart dili, 11 rozet ailesi, 13 grafik üreticisi; 52 test dosyası app.js'i STRING olarak tarıyor). KRİTİK: 'koyu tuval bağlayıcı' iddiam YANLIŞTI — bağlayıcı karar (2026-07-31) İKİ ZEMİN + GÜNDÜZ VARSAYILAN; kontrol-odası doktrini benimsendi ama koyu tuval BENİMSENMEDİ (DESIGN.md beyanlı sapma #3; 'koyu daha iyi okunur' HANDBOOK'ta çürütülmüş). Dub'dan alınabilecekler DAR: yalnız 12px yarıçap + 4px taban + 500 ağırlık; elektrik-mavi aksan v197 tavanı(=0) yüzünden YAPISAL OLARAK imkânsız (Money Rule), gölge/pill/soğuk-nötr/16px gövde de yasalarca dışarıda. İKİ BORÇ redesign'dan ÖNCE: DESIGN.md gündüz jetonları BAYAT (9 jeton ayrık, --bg #ffffff↔gerçek #fbf9f8) · app.js'te 53 satır-içi değer-jetonu / 0 rol-jetonu (WP8-D 33 diyor — sayım farkı açık).
- **2026-08-24 ~01:05 GECE DAĞITIMI (`7f38d23`) — EDG-019 KILL KAPAMASI CANLIDA:** suite 0 kırmızı; kill#1 kapısı canlıda doğrulandı (`SKILL_GORUS_URETIM_ACIK=False`, görüş yazımı durdu → canlı döngü p95 ihlali BİTTİ). Taşınanlar: E-partisi v278 (9 kalem + üç hata düzeltmesi) · v275 küçük paket · v276 OPT Faz-1 kabloları · v279 kart hijyeni (38 kart + README üreticisi) · aylık bucket-kopya birimi (kurulum ELLE — F9 'ölçülemedi' uyarısı beklenen) · RUNBOOK/korpus tazelemeleri. Bilinçli `--kirli-gec`: tek kirli kalem uçuştaki ajanın yarım yazdığı DOKÜMAN (kod/state değil); beyan `kirli_gec_kullanildi: true` ile kayıtlı. Canlı: 4 servis aktif, healthz 200, 401 ayrımı sağlam.
- **2026-08-24 BAĞLAYICI OPERATÖR KARARI — PANO İKİLİ TEMA (Dub referansı):** görsel dil Dub tasarım sistemiyle yenilenir; uygulama **ikili token katmanı** (her token açık+koyu), pano tema anahtarı kazanır. Varsayılan KOYU (davranış-nötr geçiş). TASARIM-YONU-2026-08-07 doktrini İPTAL DEĞİL GENİŞLETİLDİ — dark-cockpit gerekçesi korunur; ŞART: açık temada alarm görünürlüğü yeniden tasarlanmadan açık tema varsayılan YAPILAMAZ. Değişmezler listesi kararda (dürüstlük-UI, v196/v197/v198/v194/v205 çivileri, CSP script-src-self → harici font CDN'i YASAK). Yol: envanter → Claude Design projesi (`Meridian Pano — Design System`) → onay → bileşen-bileşen uygulama. Kayıt: `docs/KARAR-2026-08-24-PANO-IKILI-TEMA.md`.
- **2026-08-24 M8-U2/U3 KART HİJYENİ:** 68 kartın 46'sı pending taşıyordu → **38'i temizlendi** (ölçülmüş kartlar gerçek trial_id'ye; ölçülmemiş 8'i DOKUNULMADI — doğru hâl). 3 kart `none-` damgası aldı ve ajan brief'imi DÜZELTTİ: ölçülmüş-ama-arşivsiz kartlara 'olculmedi' demek uydurma olurdu → `none-arsivsiz-…` (Rol-1 onayladı). README endeksi elle-bakımdan çıktı: `ops/kart_endeksi_uret.py` (deterministik, `--kontrol` bayatlığı ölçer); eski elle bölümün 8/8 satırı bayatmış, gerçekten registered olan 6 kart listede HİÇ YOKMUŞ. v279: dup-anahtar çivisi (yaml.compose — safe_load'ın son-kazanır yutmasını atlar) + pending çivisi çift yönlü; mutasyon kanıtlı. Ayrıca iki dal merge edildi (v275 küçük paket + v276 OPT kablolama; 86 kapsam testi yeşil).
- **2026-08-24 M11 KOVA-6 ALAN MERCEĞİ TARAMASI (K=0):** 26 plan alanı + 14 `entry_law` alt-alanı sınıflandı (CANLI-BAĞLI 25 · GÖRÜNÜRLÜK 10 · ÖLÜ 5 · değer-düzeyi HAYALET 2). KALİBRASYON 1/3 DÜŞTÜ, iki onarımla 3/3'e çıktı (yüzey ayrımı + değer-düzeyi çapraz kontrol) — kova-4 dersi işledi. ÜÇ TEHLİKELİ BULGU tahtaya işlendi: gölge-terfi kapısı yapısal erişilemez (535/893 plan-birleşmesi yok) · broker_status pano yanlış-güveni (veto edilen plan 'gönderilecek' görünüyor) · exploration/carried üretimi sıfır ama pano keşif çipi yanıyor. Bonus: entry_law'da 4 ölü alan + 2 çürük 'okuyucusu var' beyanı.
- **2026-08-24 ELEME KAPANIŞLARI TAHTAYA İŞLENDİ (28/28, 69 damga):** 14 KAPAT-BAYAT · 8 KAPAT-TASARIMDA · 4 KART-ADAYI (ikisi aynı gece ön-kayıtlandı: 055 earnings fail-open, 056 split oran-imzası; 054 kirli-dönem E-1 kararından) · 2 BİRLEŞTİR. Ajan iki BAYAT NOKTA daha yakaladı (H1 '24b-24d' sayımı artık yalnız 24b; §4 havuz 'DOKUNULMAYANLAR' paragrafı) — kanıt-atıflı not düşüldü. Stok kampanyasının ilk gecesi: ~35 kalem → 22 kapanış + 4 ölçüm-kuyruğu + 2 birleştirme.
- **2026-08-24 `EDG-2026-050` (PEAD) ÖLÇÜLDÜ — KURAL ATEŞLEDİ, AMA KIL PAYI:** üst dilim @60g +52,4 bps CI [+1,6; +106,4], 10bps sonrası +42,4 → 'ARSENAL ADAYI' — ÜÇ ŞERHLE: (1) tohum-kırılgan (6 tohumun 2'sinde alt sınır ≤0; P=0,0239 ↔ çıta 0,025) → skor bağlaması İÇİN YETMEZ, ön-kayıtlı sağlamlık tekrarı şart; (2) survivorship ÜST-SINIR; (3) olay popülasyonu bir bütün olarak evrene karşı NEGATİF (−26,4 @60g) — bulgu olaylar İÇİNDEKİ göreli üstünlük. 15.838 olay, PIT yıkıcı sınaması ihlal 0, pozitif kontroller geçti. 15d'nin ilk faktörü ölçüldü.
- **2026-08-24 `EDG-2026-049` ÖLÇÜLDÜ — NO-GO (iki kat): uyuyan yol = ARKA KAPIDAN PULLBACK.** Δ −3.121,44 [CI 0-içi] + dilim n=6<30 (6/6 kayıp, −4,725R). ASIL BULGU: dormant dilimin 6/6'sı `pullback` — yani yolu bağlamak B1'in ölçümle silahsızlandırdığı kolu geri açmakmış; Δ, edg032b→c geçişindeki +3.121,44'ün kuruşu kuruşuna tersi (EDG-039'un rakamı, aynı 6 işlem). Üç bağımsız ölçüm aynı yeri işaretledi. Yol TEŞHİS-KATMANI damgasıyla kapandı; canlanma yalnız pullback'in ARSENAL çıtasını geçmesi + ayrı kartla. Künye tazeleme üç-yönlü özdeş (K2/K5 replay'e sızmadı).
- **2026-08-24 ~01:30 ELEME TURLARI TAMAM + EDG-019 KILL HÜKMÜ:** 28 stok kalemi elendi — 14 KAPAT-BAYAT · 8 KAPAT-TASARIMDA · 4 ÖLÇ (K=3) · 2 BİRLEŞTİR (belgeler: ELEME-WP5/WP7/WP4-HAVUZ). Çarpıcılar: 24e 'terfi duvarı' ilanından 1 gün sonra yıkılmış (danışman 08-14 terfi); M7/2B/2C aynı commit'le 08-02'de inmiş. KRİTİK: EDG-019'un donuk kill#1'i 08-21'den beri tetikliymiş (p95 ×6.6) ve katman KARTSIZ sevk edilmişti — Rol-1 hükmü: katman KAPATILIR (E-partisi v278), yönetişim ihlali kartta kayıtlı, yeniden-açılış yalnız resmî ölçümle. Konsolide tahta-uygulaması sırada.
- **2026-08-23 gece E-LİSTESİ 12/12 KAPANDI (çift-mercek brainstorm turu):** 1-kartla-ölç · 2-taşı · 3-kanonik-ad · 4-damgala · 5-mini-ölçüm · 6-tek-kaynak · 7-kopyala-ama-silme · 8/10-uykuda · 9-insider ÖNE (fizibilite indi) · 11-registry budandı (133; idempotens kanıtlı) · 12-LoadCredential FAZ-2 CANLI (token /proc-environ'dan silindi=0 ölçüldü; farksal kanıt; 200/401 ayrımı sağlam). Token artık yalnız systemd credential kanalında — H3 hattı TAM kapandı.
- **2026-08-23 gece INSIDER FİZİBİLİTESİ İNDİ (operatör öne çekti):** Form-4 gerçek sayımlarla ölçüldü (17,8k/yıl; gecikme medyan 2g; P-kodu nadir → faktör OLAY-bazlı tasarlanacak; geri-doldurma TSV kestirmesi ~81 zip). Öneri: EDGAR yolu, FMP'siz. 5 onay sorusu masada (F bölümü). Ayrıca OPT Faz-1 kablolama dalda (3/5 aday zaten kabloluymuş — WP3-B metni bayattı; 5 yeni düğme bit-nötr).
- **2026-08-23 gece `EDG-2026-052` İLK KOŞUM (betimleyici):** E2'de dolum-dakikası alanı YOKMUŞ (eşleme kurulamadı, 18/18 adlı) — ama yan-kanıt defter sadakatini bağımsız teyit etti (fiyat=parça-ağırlıklı ort, 0,002 bps) ve arşivin açılış-dakikası bant-içi oranını %30 ölçtü (IEX şerhi rakamlandı). Doğan işler: E2 dolum-zamanı alanı (13-A2/A3 ön-şartı) + HUM/NUE adlı tutarsızlık incelemesi.
- **2026-08-23 gece `EDG-2026-051` ÖLÇÜLDÜ — BREADTH AYIRMIYOR (hipotez arşiv):** Δ CI 0-içi; iki dilim de ağır negatif — 28g kaybı genişlik-bağımsız. Sınır: holdout gerçek dar-breadth rejimi hiç içermiyor (47,6–62,8 bandı) — genel breadth hipotezi ancak öyle bir pencerede yeni kartla sınanabilir. Bağlam-değişkeni avı sürüyor; breadth elendi.
- **2026-08-23 gece DEVAM DALGASI-2:** EDG-050 (PEAD) + EDG-051 (breadth) ölçümleri PARALEL kalktı (şasi gerektirmezler — 049'la çakışmaz). Küçük-paket dalda (v275: n_ok tip ayrımı + gölge-rozet beyanı + havuz raporu). Havuz sahipsizleri Rol-1 hükmüyle işlendi: 4 arşiv (Ö-30 bayat dahil) + 3 taşıma (Ö-39→WP7 · Ö-41→WP5 · Ö-42→WP6).
- **2026-08-23 gece `13` TASARIMI İNDİ (WP1 son tasarım stoku):** intraday dolum sözleşmesi belgesi (`docs/TASARIM-13-INTRADAY-DOLUM-SOZLESMESI-2026-08-23.md`) — 7 ilke + A1→A3 aşamalı yol (kart adayları Rol-1'de). YAN-BULGULAR: `bars_intraday` RETENTION'SIZ (~2,3GB/yıl tavansız — operatör kalemi, acil değil, disk 39G boş) · pencere-1345'in yeni canlı↔replay boşluğunun hakemi zaten kurulu (EXE-009 alt-bant). EDG-050 (PEAD) + EDG-051 (breadth) ön-kayıtlı, ölçümleri kuyrukta.
- **2026-08-23 ~17:05 AKŞAM DALGASI KAPANDI (dağıtım + bucket + goal):** 7-kararın uygulama kuyruğu canlıda (`02c91ca`): pencere-13:45 + E2 damgası + hakem katmanı · 25a kaldırmaları (goal kopyası operatör eliyle, anahtar-düzeyi [1b] kuralı işledi) · @chop duraklatma · triyaj 7 düzeltme (dedektör kaynak-farkındalı — 26k ihlali TEMİZLENDİ, canlıdan doğrulandı; session_refresh örnekleme; dagitim bloğu; sel/orphan kapanışları) · F8/K4 belgeler. **OCI bucket AŞAMA-2 CANLI:** litestream S3 replica çalışıyor (sır zinciri pano→secrets→env, değer kimsenin elinden geçmedi); GERİ-YÜKLEME TATBİKATI GEÇTİ (bucket→restore: integrity ok, 893/27.034,92 canlıyla birebir). Alarm backlog tek DIGEST'le teslim. Birleşik-ağaç 8 kırmızısı kök-nedenli kapandı; suite 0. Kalan op: plan_geri_doldur (kaynak-engelli, beyanlı) + registry budaması (dry-run hazır, sonraki pencere).
- **2026-08-23 `EXE-2026-008` ÖLÇÜLDÜ — İKİ DÜNYADA DA BELİRSİZ, bacak kapalı/042'ye park:** H1 yeni dünyada da kırık (tepe 0.01), H2 8/8 CI 0-içi, Ö3 4/4 CI 0-içi (noktalar 4/4 pozitif). B-E1-LIMIT kararı kanıt yönsüz kaldı; üçüncü tekrar yalnız 042 bandı gelince (043 askısıyla tek turda). Betimleyici: dinlenen-dolum %61-74 çalışıyor, yerinden-olanlar negatif ort-R'li.
- **2026-08-23 `EDG-2026-048` ÖLÇÜLDÜ — NO-GO, CHOP KAPALILIĞI ARTIK ÖLÇÜLMÜŞ POLİTİKA:** taban 45→60 açılımı Δ −18.266$ [CI 0-içi, nokta ağır negatif]; chop dilimi −26,3R VE +22,6R'lik 99 iyi işlemi yerinden etti (çift kanal zarar). K1 kararının kanıt kapısı kapandı; @chop üretim duraklatması gerekçeli, 28d @chop dilimi kapanır. Künye sagası: v268 guard farkı üç-yönlü bayt-özdeşlikle nötr KANITLANDI, TABAN_KUNYESI tarihçe-koruyarak tazelendi.
- **2026-08-23 ~10:50 BAKIM PENCERESİ KAPANDI (operatör 'hafta sonundayız' dedi, birlikte yürüdü):** H3 tur-2 CANLIDA (4/4 drop-in; tetik-testi bekçi-eliyle-restart KANITLI; iki alet vakası yakalandı-düzeltildi: CAP_DAC boş-küme okuma kırması + h3 pipefail/SIGPIPE) · LoadCredential faz-1 canlıda (401-kanıt) · N1 zinciri uçtan uca ölçüldü (üç Telegram gönderimi) · SuccessExitStatus zaten 08-09'da yapılmıştı (süpürme) · 044 aşama-2 düştü. Canlı bface8e.
- **2026-08-23 ~05:00 TUR KAPANIŞI (dağıtım + canlı doğrulama):** otoriter suite 0 kırmızı (beş kırmızı kök-nedenli kapandı: sermaye --json kanal ayrımı · yerel_donmus_defter FOTOĞRAF ŞARTI · conftest canlı-yol muafiyeti + 12 artık satır temizliği · korpus tazeleme · F8 emisyon kapısı + kart tabanı 20→22 beyanlı). `cbf6197` dagit ile canlıda: [F9] ilk koşum 5/5 BİREBİR · [B] beyanı bayt-doğrulamalı · goal.yaml A17 yorumu yedekli kopyalandı. Canlı doğrulama: 4 servis aktif, 0 restart, journal sessiz, healthz 200, diagnostics 32 anahtar (durum_sozlugu VAR, 4 YASA-6 raporu servis'te), damga canlıda 0. Sabah masası: docs/KARAR-MASASI-2026-08-23.md · friksiyon haritası: docs/FRIKSIYON-PROGRAMI-HARITA-2026-08-23.md.
- **2026-08-23 `EDG-2026-044` AŞAMA-1 ÖLÇÜLDÜ — KART KAPANDI:** havuz tavanı cpu−1 yerel kazancı %17,49 < %20 donuk eşiği; tavan kalır, canlı aşaması hiç açılmadı (sabah masasının koşullu bakım kalemi düştü). Yan-bulgu: ikiz formül tabanları bugün zaten farklı — tek-kaynak XS adayı.
- **2026-08-23 GECE FİLOSU (operatör: "benden karar beklemeyen bütün paketleri bitir"):** `EDG-2026-047` yakın-pencere AYNI GECE kart→ölçüm→hüküm (Ö1 ateşledi, −%42 replikasyon; pencere-kaydırma §5 [B-PENCERE-KAYDIR]) · §4 havuz boşaltıldı (8 gövde WP'lere; 5 KART-ADAYI + 1 §5-adayı etiketi) · §5'e 19 kalıcı kimlik + tablo (kimliklendirme H6) · 15d PIT-faktör tasarım belgesi indi · sprint ortam dosyası yaratma-anı 0600 (v270) · 23c YEDİNCİ bayat vaka olarak düzeltildi (modelleme EXE-005/006'da zaten kapalıymış). Uçuşta: F8 sözlüğü · Ö-49 tam süpürme · WP6-① (F9+P0-b+H3) · sırada 044 aşama-1 + suite + dağıtım + canlı doğrulama + sabah KARAR MASASI.
- **2026-08-23 `EDG-2026-046` ÖLÇÜLDÜ — MEKANİZMA KANITSIZ, KART KAPANDI (donuk iki-dünya kuralı):** ATR%-cezalı seçilim iki dünyada da +10,7k/+11,5k nokta kazancı gösterdi ama ATR-dünyası CI'sı 0-içi (−868 alt-uç) → kural gereği aday DEĞİL; kazancın dünya-bağımsızlığı mekanizmanın friksiyon-kanallı olmadığının kanıtı sayıldı (yaltaklanan-mekanizma tuzağı — kural tam bunun için donmuştu). Şasi kapısı edg032c ile bayt-özdeş, öz-sınama 4/4, kill 0. Yan-bulgu: sabit-5bps ↔ ATR-orantılı dünya farkı −2.115 CI-üst<0 (045'le aynı yönde). ACİL şemsiyesinin (b) bacağı kapandı.
- **2026-08-23 `23d`/EDG-2026-045 ÖLÇÜLDÜ — Ö1 ateşledi:** sıfır-stop-slip varsayımı defteri anlamlı şişiriyor (10 bps → −5.697$, üç CI de sıfır-dışı; paket yine pozitif). EDG-040 bandına ve replay hükümlerine şerh düşüldü. Yolda iki DOĞRU durma: B1-taban (edg032c donduruldu) + aletin bağ-yuvarlama tamamlaması (motorun KARMA yuvarlama yolu ölçüldü: np vs Python round, yola göre; 885/885 iki defterde). 046 sırada.
- **2026-08-22 edg032c TABAN DONDURULDU (determinizm çift-kapılı, bayt-özdeş):** B1-sonrası dünyanın kanonik tabanı hazır (n=885, pullback 0, dört motor-sha künyeli). ÇAPRAZ-DOĞRULAMA: eski↔yeni fark Δ+3.121,44$ — EDG-2026-039'un silahsızlanma ölçümüyle KURUŞU KURUŞUNA aynı (bağımsız yollardan aynı sayı; şasi bütünlüğü kanıtı). 045 yeni tabana karşı yeniden koşuluyor, 046 sırada.
- **2026-08-22 PARADİGMA OLAYI + KENDİ EKSİĞİM (kayıtlı): strateji-kimliği değişikliği donmuş tabanı geçersiz kılar.** B1 (pullback silahsız) edg032b'yi yeniden-üretilemez yaptı; 045 kill#1'de DOĞRU durdu (taban 6 pullback taşıyor). B1'i uygularken bunu ÖNGÖRMELİYDİM — kural artık yazılı: strateji kimliği değişen her karar, taban yeniden-dondurma kalemini YANINDA getirir. Rol-1 kararı: eski-dünya worktree'si değil YENİ taban (edg032c, determinizm çift-kapılı) — ölçümler yaşadığımız dünyayı bilgilendirmeli. 045/046 ölçümden-önce yeniden çapalandı (sıfır hücre ölçülmüşken; eşik/K aynı).
- **2026-08-22 `23f` KAPANDI (kayıt-düşme — yeniden ölçüm İSRAF olurdu):** cancel'ın anlamlı-tanım ölçümü zaten kanonikti (452/885, +11.233$ bırakır → ELENİR); yürürlük tanımı yapısal-totolojik. Hüküm EXE-2026-001 gap-eksenine işlendi, canlanma koşulu beyanlı. Friksiyon-dayanıklılığı satırı H6 hijyeni.
- **2026-08-22 SON TUR İNDİ (3 ajan):** chop KARAR BRIEF'İ hazır (kanıt iki yüzlü: defter-chop zayıf ama güncel arama-chop trend_up'a eşit — karar operatörde) · yoğunluk anomalisi ÇÖZÜLDÜ (gerçek değil: Rol-1'in etiket hatası [fold3≠holdout] + konfig-çağı bayat-önbelleği; kontrollü A/B 23↔90'ı yalnız konfigle üretti; hijyen: yerel inc_cache'ten hüküm okunmaz) · virgin-knob tasarımı H1 (üç tüketici yüzeyi ölçüldü).
- **2026-08-22 ÜÇ KART ÖN-KAYITLI + WP2 CEPHESİ RESMEN KAPANDI:** `EDG-2026-044` havuz cpu−1 (K=1, iki aşamalı, canlı yalnız operatör onaylı) · `EDG-2026-045` stop-slip (K=3, 23d'nin kartı; 23b iki karta mutabık kılındı) · `EDG-2026-046` friksiyon-bilinçli seçilim (K=4, ACİL(b), iki-dünya şartı). WP2'nin son iki satırı çizildi (v264/v265).
- **2026-08-22 WP1-H0 TURU İNDİ (4 kanıt/tasarım):** WP-E 6 boşluk sınıfı BAYAT çıktı — iş 2026-08-12'de v234'le kapanmış, on gün açık görünmüş (Ö-49 sınıfının en büyüğü) · 23e öncülü güncellendi (gün-içi veri birikiyormuş: 186 MB dakikalık, 249/251 ticker; derinlik 20 seans) · 23d kanıtı hazır (kart kuyruğa) · friksiyon-seçilim keşfi: |bps| tahmin edilebilir (ATR% ρ=+0,82 — plan alanı), işaret değil; ACİL(b) kartının hammaddesi. WP2 CEPHESİ TAM KAPANDI (equity zinciri + EOD kanıtı).
- **2026-08-22 WP3 TURU İNDİ (4 ajan):** `Ö-48` KAPANDI (süzgeç + öncül düzeltmesi: bugün hayalet 0, %62 vakası öneri-katmanı sınıfıydı → yeni H0) · `28d` TEŞHİS: "chop yok" yanlıştı, gerçek mekanizma BÜTÇE BAĞLAŞIMI (chop 2025-06-12'den beri girişe kapalı) → politika sorusu H0'a · `28g-i` TEŞHİS: gerçek bozulma (skorun %64'ü getiri bacağı; kayıp tekdüze; endeks-rejim görmez) + yoğunluk anomalisi yan bulgusu → H0 · havuz tavanı kanıtı hazır (ikiz formül bulgusuyla). Üç H0 kapandı, üç yeni kalem ADLI doğdu — stok küçülmedi ama artık ölçülmüş.
- **2026-08-22 KENDİ HATAM (kayıtlı): ölçüm uçuştayken motor dosyasına commit attım** — B1 commit'i (c150902) 043 koşumu sürerken strategy.py'yi değiştirdi; kill'in dosya-kanıtı slip25_B'de tetiklendi. Hücreler SÜREÇ-kanıtıyla geçerli (yüklü modül + assert + defterde pullback izi) ama dosya-kanıt zinciri o pencerede kırık — kartta kalıcı şerh. KURAL: uçuşta motor commit'i YOK; commit kuyruğu ölçüm bitişine bağlanır.
- **2026-08-22 `Ö-55`/EDG-2026-043 ÖLÇÜLDÜ (hüküm askıda):** kapılar 7/7 temiz; altı CI de 0-içi. Yön gözlemi: B kolu nokta tahminleri üç slip'te pozitif (slip15_B tek kârlı hücre) — işaret-dönüşü tezi nefes alıyor ama kanıtlanmadı. Okuma EDG-042 bandıyla; muhtemel sonuç "ayrışmadı". K=6 harcandı.
- **2026-08-22 PARALEL TUR-2 (workflow 3 ajan):** 24b SOUL kilidi CANLIDA DOĞRULANDI (sha birebir, kilit cümlesi yerinde; kartın tam ölçümü kod ister — registered kalır) · F8 tasarım belgesi yazıldı (H0→H1; "15 bekçi" bayat → 17 ölçüldü; 16 tutarsızlık; 4 YASA-6 adayı + codelaw yapısal körlüğü) · Ö-49 kalan envanteri: İHLAL SIFIR, 28 çözümsüz çapanın sınıflaması (gerçek risk 9 — hepsi trend_shadow→engine.py 'hedef repoda yok' ailesi; yanlış-satır çapası 0) + 9 bayat ROADMAP satırı → S1-S7 bu commit'te kapatıldı (ikisi BUGÜNÜN ıskası: kart güncellenmiş, §6 indeksi unutulmuştu — EXE-006 vakasının aynısı).
- **2026-08-22 EDG-019 numara çelişkisi KAPANDI:** README'nin 08-03 "emekli" notu ile diskteki 08-13 kartı çelişiyordu. Tarihçe ölçüldü (v219 docstring): numara bilinçli ve boşluk-doğrulamalı yeniden kullanılmış; bayat olan README beyanıydı → düzeltildi, kart kimliği yerinde. Ö-49 sınıfı.
- **2026-08-22 `B1` KARAR (operatör): A — pullback SİLAHSIZLANDI.** Kanıt asimetrisi hükmü uygulandı (zarar üç kaynakta tutarlı; fayda kanıtsız ama zararsız; ısı bedeli karşılıksızdı — 13-22 Ağu canlı işlem 0, cf 21→29 hep negatif). Yeniden-silahlanma kapısı DONUK: cf n≥30 ∧ CI-alt>0 → kart-önce; doğrudan geri ekleme yasak. Çiviler v260 + v92 (niyet korunarak). Strateji kimliği değişikliği — dağıtım 043 sonrası otoriter suite ile.
- **2026-08-22 `A2` KAPANDI — bildirim kanalı CANLI, `B2`(c) fiilen yürürlükte.** Telegram: token operatörden, chat_id sunucu tarafında token'a dokunmadan, yazım panonun kendi ucuyla; `configured=True`, test TESLİM edildi, teslim-hatası 0. 310'luk birikim sayaçtır (geriye akmaz); bundan sonra NAKED_POSITION/MIRROR_DRIFT/devre-kesici dahil her alarm telefona düşer. İlk deneme teşhisi ölçümle: bota mesaj hiç ulaşmamıştı (pending=0).
- **2026-08-22 `B4` KARAR (operatör): A+C — E1 limit bacağı KAPALI KALIR, gerekçe yeniden temellendirildi.** Eski dayanak (E1 'monoton zararlı') çürümüştü; yenisi ölçüm: açmak dört tavanda da taban altında (−1,2k…−11,1k), kurtarılanlar ~0R, hiçbir delta anlamlı değil, üstüne −8,4k'lık iç-motor↔canlı model boşluğu doğardı. Tek açık argüman (yüksek friksiyonda işaret dönüşü) `EDG-2026-043` kartına ön-kayıtlandı (`Ö-55`, K=6): hüküm EDG-042'nin gerçek bandıyla İKİ KAYNAKLI okunur — bant gelmeden B4 yeniden açılamaz (kill kriteri). `D5` tavan kararı park.
- **2026-08-22 `edg042-friksiyon-haftalik` İLK FIRE (insansız uçtan uca):** çekim → ölçüm → kart işleme → açık-yol commit zinciri çalıştı; sayılar öğleki ara-koşumla bayt-özdeş (Cumartesi, yeni veri yok — takvim kanıtı, yeni kanıt değil). Görev oturumu reçete↔kart işaret çelişkisini KENDİSİ yakalayıp kart-kazanır kuralıyla düzeltti (öncül sha'lı donuk kopya yanında; teyitli satır 0 iken — veri bakılmadan). İlk anlamlı tekrar 2026-08-29.
- **2026-08-22 `EDG-2026-042` OTOMATİK TAKVİME BAĞLANDI (operatör talimatı):** haftalık betimleyici tekrar (Cmt ~10:29, zamanlanmış görev) + eşik dolan kovada hükümlü koşum otomatik; üç kova hükümlüyse görev kendini kapatır. Görev tam Rol-1 disipliniyle yazıldı: kart kazanır, salt-okunur çekim, açık-yol commit, tam suite/dağıtım YASAK.
- **2026-08-22 `EDG-2026-042` BETİMLEYİCİ ARA-KOŞUM (hüküm yok):** K1 n=13 medyan **+15,0 bps** — model varsayımının üç katı, EDG-040 başabaş bandının üst sınırında; dağılım vahşi (−131..+327). K2/K3 tamamen olculemedi (teyit damgası henüz basılmadı — kill kriteri dürüstçe işledi). Kart measuring; K2/K3 işaret çelişkisi ölçüm-öncesi yakalanıp düzeltildi. n=4 → n=13: iki tahmin de "modelden yukarı" yönünde, ikisi de hüküm değil.
- **2026-08-22 `EDG-2026-042` ÖN-KAYITLI (`Ö-54`):** gerçek friksiyon tahmini kartı — EDG-040 ACİL kaleminin (a) bacağı. Eşikler veriye BAKILMADAN donduruldu (kanıt taraması yalnız sayım/tanım topladı; workflow 3 okuyucu). Kümeleme birimi SEANS (ay-kümeli emsal tek aya çökerdi — beyanlı sapma). YAN BULGU: `research/cards/README.md` 'EDG-2026-019 emekli, retro doldurma YAPILMAZ' derken diskte `EDG-2026-019-skill-gorus-defteri.yaml` var — numara 08-13'te yeniden kullanılmış; kimlik çakışması Ö-49 sınıfı, ayrı kalem (README mi kart mı düzelecek: Rol-1 sonraki tur).
- **2026-08-22 TUR KAPANIŞI (dağıtım cbcdeed):** `Ö-52` H6 ✅ (teyit boyutu canlıda; suite 6308/0). Turda üç kırmızı çıktı ve İKİ YASA ihlalim yakalandı: dört `|| 0` bulaştırması (null=ölçülemedi≠0 — çırçır 196>192) + süssüz-if emisyon kapısı; ikisi de kod-yasaya-uydurularak kapatıldı.
- **2026-08-22 🔴 `EDG-2026-040` HÜKMÜ: C+mb paketi +10 bps ek friksiyonda NEGATİF** — taban +20.685 → slip15 −3.067 (PF 0,98), CI'lar sıfırın dışında; başabaş 5-15 bps/bacak; hasar fiyat kaynaklı. Kartın donuk kuralı ACİL kalemi açtı (H0 tepesi). Kill#2 ilk koşumu DOĞRU şekilde durdurdu; öz-sınama likidite terimi ayrıştırılarak TAMAMLANDI (gevşetilmedi, 1e-9 korundu).
- **2026-08-22 PARALEL TUR (5 ajan):** `EXE-2026-007` ölçüldü→measured (Ö1=%25; ledgerstamp boyutu kodlandı, dağıtım bekliyor) · `EDG-2026-040` koşumda (kill#2 bir kez DOĞRU şekilde durdurdu; yeniden koşum sürüyor) · `EXE-2026-003` ara hüküm (pencere 2/20, altyapı sağlam, measuring) · WP6 değer-eşitliği envanteri çıkarıldı + 5 🔴 bulgu kapandı · Ö-53/B+D canlıya dağıtıldı (5d75dcf).
- **2026-08-22 `Ö-53` KAPANDI (operatör kararı B+D):** ayna kitabın tabanıyla boyutlanır (guard'lı) + kitap dolumdan sonra aynanın adedini benimser. İkinci mekanizma UYGULAMADAN ÖNCE ölçüldü ve baskın çıktı (per_share, dördünde de); "19 Ağu %8 equity farkı" beyanım YANLIŞTI (hizalama hatası — gönderim ertesi gün olmuş), düzeltildi. v258 çivileri, suite 6281/0.
- **2026-08-22 `A1` SATIRI BAYATTI — ölçümle kapandı:** bekçi hükmü korumasız 0/7; "4 pozisyon çıplak" 08-07/09 penceresinindi. NVDA motor-dışı ve stopsuz (bekçi ayrı sayıyor). Ölçüm dersi: stoplar OCO bacağı, düz emir sorgusu görmez (`nested=True`).
- **2026-08-22 `Ö-51d` HÜKMÜ YAZILDI:** `EXE-2026-005` → `measured`; soru canlı yasada cevaplanamaz (yapısal boş küme), dar-tavan K=8 `EXE-2026-006`da sayıldı, ek K yok. D5 operatörde.
- **2026-08-22 `Ö-51b` KAPANDI: Ö1 ölçüldü (%61–74), `K1` şerhi AÇILIR** — A kolu bayt-özdeşlik kapısı dört tavanda da geçti. 08-17'nin "aynı plan günlerce reddedilebilir" teşhisi ÇÜRÜDÜ (olay/plan çarpanı tam ×1,0); imkânsız %132'nin tek sebebi payın kirliliğiymiş. Kurtarılan işlemlerin ort-R'si ~sıfır → `B4`ün iki ön-koşulu da kapalı, karar operatörde ve kanıt açmayı DESTEKLEMİYOR.
- **2026-08-22 "açıklanamayan 2.623,34" SENTE KAPANDI** — 2.615,96 defter ayrışması + 7,38 taban farkı (kitap 100.000,00 yuvarlak, broker reset günü 99.992,62). Ezici çoğunluk `Ö-53` ADET AYRIŞMASI (yeni), −277,99'u `Ö-52` karşılıksız işlem. Yöntem varsayımsız (broker'ın kendi cost_basis'i; FIFO/ortalama-maliyet VARSAYILMADI). Kitap tarafı bağımsız doğrulandı (6.350,23 ↔ realized_pnl 6.350,22314). Canlıya dokunulmadı.
- **2026-08-22 DÜZELTME: `Ö-51c` (Ö3 ΔP&L CI) aslında 2026-08-21'de KAPANMIŞTI** — ROADMAP onu beş gün H1'de açık gösterdi ve `B4` operatör kararını gereksiz bekletti. CI dört tavanda da sıfırı içeriyor, yani limit bacağını açma gerekçesi ZAYIFLADI. Bayat-beyan sınıfı (A17/Ö-49); kanıt diskten okundu, ezberden değil.
- **2026-08-22 BULGU: `live_paper` damgası broker teyidi DEĞİL, kod yolu beyanı** — reset sonrası 8 canlı işlemin 2'si (`ALL`/`VLO`) Alpaca'da hiç var olmamış (62 emir · 55 aktivite · 61.511 olay, üçünde de sıfır iz). Kök neden kapalı: `submit_plan` ONAY ANINDA, iç motor onaydan BAĞIMSIZ koşuyor. Kart `EXE-2026-007` ön-kayıtlı, tahta kalemi `Ö-52`. Öğrenme etkisi ölçüldü ve DAR (satırlar yansıma tabanının altında). Davranış DEĞİŞTİRİLMEDİ — bu bir ölçüm/damga kalemidir.
- **2026-08-17 OPERATÖR İKİ KARAR VERDİ: `A1` "korumayı şimdi kur" + `B2` = seçenek (c):**
  **`B2`(c)** — `koruma_kur`un ÜÇ KAPISI (ölçüm + onay jetonu + öneri kimliği) KALIR, çıplaklık
  alarmı bildirim kanalına bağlanır; (a) tam otomatik ve (b) ölçüm-kapısız REDDEDİLDİ. **Kod işi
  gerekmedi ve bu ölçülerek söylendi:** (c)'nin ikinci yarısı zaten yürürlükteydi — alarm kendi
  jetonunu taşıyor (`obs.ALARM_NAKED_POSITION`, `watchdog.py:2836/2849`), `NOTIFY_TOKENS` bir
  TÜRETME (`obs.py:138`) olduğu için jeton kendiliğinden teslim kapsamında, zincir
  `obs.alarm → _maybe_notify → notify.send`. Üç çivi zaten vardı: `v216:85`, **`v216:130-141`**
  ((c)'nin asıl güvencesi — MIRROR_DRIFT susturma penceresinden SONRA bile NAKED_POSITION teslim
  edilir; muhasebe gürültüsü sermaye riskini susturamaz), `v209:248`. **SONUÇ — POLİTİKA KAPANDI,
  TESLİM KAPANMADI:** (c) kanal kimliğini ŞART koşuyor, o yüzden `A2` "en ucuz kalem" olmaktan çıkıp
  **seçilmiş politikanın teslim bacağı** oldu ve tahtada yükseltildi; kimlik girilene dek
  `notify.configured()` False, alarm yazılır ama TESLİM EDİLMEZ (`notify_undelivered.json` sayar).
  **`A1`** — emir verildi, **icra EDİLMEDİ ve emri alan oturum icra EDEMEZ**: cloud kabında `.env`
  ve Alpaca kimliği yok, üstelik kimlik olsa bile canlı worker koşarken ikinci süreçten emir
  göndermek CLAUDE.md §5'in yasakladığı **çift-emir** riskidir (kapasite eksiği değil, emniyet
  sınırı). Kalem DİK DURUM'da AÇIK bırakıldı ve "karar bekliyor"dan "**icra bekliyor**"a geçti;
  koddan doğrulanmış adım listesi §5 KOVA-1'e yazıldı (ölç → `oneri_id` al → jetonu GÖVDEDE gönder;
  jetonsuz çağrı kuru koşu; `oneri_id` eşleşmezse emir gitmez; `ok` yalnız TÜMÜ gittiğinde True).
- **2026-08-17 `EXE-2026-006` HÜKMÜ İŞLENDİ → E1 YENİDEN AÇILDI + kart↔hüküm çürümesi ÇİVİLENDİ (`v251`):**
  ölçüm hükmü (`a033256`) diske YAZILMIŞ ama **hiçbir karara/karta işlenmemişti** — o commit 24 dosya
  taşıdı ve hepsi ölçüm artefaktıydı; kart `status: registered` ("ölçüm bekliyor") derken hükmü
  `HUKUM.md`de duruyordu, `§2 TAHTA` kalemi H1'de bekliyordu, `§6` indeksinde kartın SATIRI HİÇ YOKTU.
  Bu bir iş bölümü kusuru DEĞİL: `CLAUDE.md §3` "ölçüm ajanı karta DOKUNMAZ, hükmü Rol-1 işler" der ve
  ölçüm ajanı doğru davrandı — eksik olan, **Rol-1 devir adımının hiçbir yerde ÇİVİLİ olmamasıydı**
  (sözleşme kendi devir noktasında sessizdi). **HÜKÜM:** kartın ölçümden ÖNCE yazdığı kural "H1 ∧ H2
  ayakta ⇒ E1 doğrulanır" idi; **H1 monotonluk DÜŞTÜ** (9.773 → **19.452** → 17.948 → 17.858, tepe
  0,01'de) ve **H2 ÖLÇÜLEMEDİ** (ay-kümeli bootstrap B=5000, dört tavanda da CI sıfırı İÇERİYOR) →
  **E1 HÜKMÜ YENİDEN AÇILIR**, bacağın canlıda etkisiz olmasının gerekçesi ARTIK KANITLI DEĞİL.
  Ö1 ÖLÇÜLEMEDİ (birim uyuşmazlığı — payda RED OLAYI sayacı, pay DİSTİNKT İŞLEM; ham bölme %132/%141
  ve bir oran %100'ü aşamaz → None+neden), Ö3 ÖLÇÜLDÜ ve **SENTE KAPANDI** (yan kanal büyük: cap=0,005'te
  251 yeni işleme karşı **154 yerinden**, yerinden olanlar dört tavanda da KAYBEDEN). Kart açmayı
  **ÖNERMEZ** (kendi sınırı) → **yeni operatör kalemi `B4`** (§5 KOVA-2), ön-koşulu `Ö-51b`+`Ö-51c`.
  İŞLENEN YÜZEYLER: kart (`status` + 9 alanlı `verdict` bloğu + `k_registry` K=8 harcandı; ön-kayıt
  metninin TEK SATIRI silinmedi) · `§2 TAHTA` (Ö-51→H6 ✅, türeyen `Ö-51b/c/d` + `B4`) · `§6` (005 ve
  006 satırları EKLENDİ) · `§5 KOVA-2` (`B4` dört satırlı paket) · bu kayıt. **ÇİVİ (`v251`, TDD —
  kırmızı doğdu):** yazılı `HUKUM*.md` ile o hükmün adlandırdığı kartın `status`u çelişemez; 5 pozitif
  kontrol + düzenek çivisi (boş taramanın sessiz-yeşili kapatıldı), tek yönlü olması BEYANLI (ters yön
  26 `measured` kartı yanlış-kırmızıya düşürürdü). Sınıf `Ö-49 çapa/beyan çürümesi`nin kart↔hüküm
  yüzeyi. **KALICI DERS (ölçüm-şablonu):** duman penceresi (n=1..3) Ö2'yi dört tavanda da NEGATİF
  gösteriyordu; 885 işlemde işaret DÖNDÜ ve CI'ya girince ölçülemez oldu — küçük örneklem yalnız
  gürültülü değil **YÖN OLARAK YANILTICIDIR**, duman bir hükmün İŞARETİ için delil sayılmaz.
- **2026-08-17 SUPERPOWERS PROTOKOLÜ KURULDU (CLAUDE.md §9, commit 1d10a75 + 44d8a06):** bu
  depoda çalışan her Claude oturumu `superpowers` plugin bileşenlerini (brainstorming,
  systematic-debugging, TDD, writing/executing-plans, code-review, verification-before-completion,
  git-worktrees vb.) kullanmak ZORUNDA — §4'deki Fable/Opus rol ayrımının ÜSTÜNE eklenir, iptal
  etmez; çelişki halinde CLAUDE.md madde 1-8 Meridian disiplini (ölçüm kartı, waiter yasağı,
  tam-suite tek-otoriter, git/dağıtım kuralları) önceliklidir. Aynı karar `MERIDIAN_ENGINEERING_LOG.md`
  başına da işlendi.
- **2026-08-17 Ö-50 UYGULANDI → v249 DAĞITILDI: ÖĞRENME KENDİ SÜRECİNE TAŞINDI, PANO 14,0 sn → 0,027 sn:** kök neden `py-spy` ile bulundu — öğrenme döngüsü API sunucusuyla AYNI süreçte bir Python ipliğiydi (`hermes-standby`) ve GIL, pano isteğini backtest hesabının arkasına diziyordu; üç çekirdek boşken pano 14 saniyeye çıkıyordu. **REGRESYON DEĞİLDİ** (geçmiş altı arama 1s55dk–3s14dk aynı bantta; yığındaki 8 modülün 7'si v248 merge'inde AST-aynı) — dağıtımın restart'ı uykudaki aramayı UYANDIRDI. Yol boyunca dört hipotez çürüdü (`barsarchive` çekişmesi · `barfeed` yoklaması · `codelaw` kapsamı · `warnings` filtre şişmesi — sonuncusu tek dökümde inandırıcıydı, 1392 örneklik profil %0,6 dedi). **ASIL BULGU:** `_havuz_tavani`nin `cpu−2` kısıtı bir tasarım tercihi değil BU KUSURUN YAMASIYDI (gerekçe kendi docstring'inde: 2026-08-03 canlı vakası, operatör elle `renice` attı). Uygulama beş kalem: `meridian-learn.service` (emsal `meridian-sprint@`; `CPUWeight=50` — `CPUQuota` DEĞİL, tavan boş çekirdekleri de yasaklardı) · `learn_run.py` · `meridian.service`te `AUTOSTART_HERMES 1→0` · **`SEARCH_PROGRESS` süreçler-arası olgu oldu (EMNİYET: ayrımdan sonra sprint kapısı boş sözlüğü "meşgul değil" okur ve koşan aramanın üstüne antrenman başlatırdı)** · pano düğmeleri `systemctl`e. **16 suite kırmızısı tasarımın üç varsayımını çürüttü** (bellek≻disk önceliği · bilgi eksikliği ≠ bilgi yokluğu · dosya yokluğu = arama yok — sonuncusu sprint'i temiz kurulumda kalıcı MEŞGUL'e kilitliyordu). `dagit [1c]` kapısı dağıtımı DURDURDU ve haklıydı: birimler kurulmadan repo değişikliği ETKİSİZ kalacaktı. **ÖLÇÜLEN SONUÇ (arama koşarken):** API süreci %93→**%2** · pano **0,027 sn** · API'de `hermes-standby` ipliği **0**. **KABUL ÖLÇÜTÜ 2 (toplam CPU >%40) SAĞLANMADI ve bu BEKLENENDİR:** faz-1 (incumbent walk) tasarım gereği seri; havuz tavanının `cpu−1`e çıkarılması kart-önce şartıyla KAPSAM DIŞI bırakılmıştı. Tasarım: `docs/TASARIM-OGRENME-SURECI-AYRIMI-2026-08-17.md`.
- **2026-08-21 GECE TURU — OPERATÖRÜN ÜÇ BİLDİRİMİ ÖLÇÜLDÜ, İKİSİ HAKLI BİRİ YANLIŞ ANLAŞILMIŞTI:** (1) *"öğrenme ve antrenman çalışmıyor"* → **İKİSİ DE BOZUK DEĞİL**: sprint `saat_dilimi_disinda` (ölçüm 21:53, pencere 22-06, yedi dakika kalmıştı), öğrenme 30 günlük aşırı-uydurma ufkunda (`span_days 2/30`, işlem şartı 6/5 SAĞLANMIŞ). Hiçbir kod değişmedi. **ÖLÇÜM TUZAĞI kayda geçti:** `_bg_ready_regime`ı TAZE süreçte çağırınca "chop" döndü ve bir an anomali sandım — fonksiyon rejim-başı TABAN kullanıyor, taze süreçte `_state` boştu; canlı durum yüklenince `None` oldu. Durum taşıyan fonksiyonu durumsuz çağırmak ölçtüğünü uydurur. (2) *"Alpaca'daki para panodakinden farklı"* → **HAKLI**, ve fark ÜÇ TERİMLİ köprü + **2.623,34 AÇIKLANAMAYAN** kalıntı; reset günü iki taraf mutabıktı (100.000 ↔ 99.992,62), ayrışma SONRA doğdu — tarihî artefakt değil YAŞAYAN kayıt eksiği. `sermaye.broker_mutabakati()` köprüyü kurar ve terim ölçülemezse kalıntıyı UYDURMAZ. (3) *"hangi işlemin ne kadar kazandırdığını göremiyorum"* → **HAKLI**: satır R basıyordu, dolar çekmecedeydi; kuzey yıldızının kendi cümlesi bunu zaten yasaklıyordu. **AYRICA İKİ BAYAT KALEM ÖLÇÜMLE DÜZELTİLDİ:** `Ö-49` (bayatlık HAKKINDAKİ kalem bayatlamıştı — beş kusuru zaten kapanmış; `report()` 7,75 sn/576 parse → **1,75 sn/97 parse**) ve `Ö-26` ("26 kapısız çift" → envanter v245'te yapılmış: 13 kapalı, 5 bağlı, 9 gerekçeli; `_divergence_hesapla` bugün **ayrık 0**). **YASA BENİ YAKALADI:** `alpaca.equity_on` eklemem bir satır çapasını bayatlattı, `codelaw.report()["ok"]` anında False oldu; düzeltme satır güncellemek değil SEMBOLE çevirmek oldu.
- **2026-08-16 CLOUD↔YEREL AYRIŞMASI KAPANDI → v248 DAĞITILDI:** GitHub'da biriken **8 cloud commit** (PR #1-#8, `4ad7684`→`22806b5`) yerele ileri-sarma ile alındı — yerel ağaç canlıya dağıtılan hâldi ve ayrışma her turda büyüyordu. Commit'lerin "docstring turu" iddiası İDDİAYA DEĞİL ÖLÇÜME bağlandı (AST karşılaştırması, docstring'ler sökülerek): **112 değişen `.py`'nin 95'i belge-yalnız (AST birebir), 17'si davranış.** Üç kırmızı-bayrak kontrolü de temiz: iki turda da hiçbir ölçüm eşiği oynamadı (`reflect`/`validation`/`probgate`), `ledgers.CONTRACTS` anahtarları aynı, yeni `pytest_collection_modifyitems` kancası bu makinede **0 test atladı** (şartı ölçüyor, bayat beyanı `UsageError` ile kırıyor). Otoriter suite **6213 geçti / 0 kırmızı / 0 atlama** (merge öncesi 3752 → cloud test tabanını büyüttü); boş grep'e güvenmeden **kasıtlı-kırmızı** ile boru hattının kırmızıyı raporladığı doğrulandı. CANLI KAZANÇ SOMUT: `/openapi.json` kimlik-doğrulamasız **200 · 39.905 B** sunuyordu → **404**. Cloud ayrıca kendi kodumuzdaki dört uydurmayı ölçümle düzeltti (import döngüsü 3 değil **6** modül · güçlü-bağlı bileşen 20 değil **33** · "sıfır istisnayla geçiyor" YANLIŞTI · çapa yasası `tests/`e açıldı, 77 çapanın 14'ü çürükmüş).
- **2026-08-14 C6 UZLAŞTIRILDI → 15c ASKISI KALKTI:** "evren mi ısı mı bağlıyor" çelişki DEĞİLmiş — huninin iki katı (seans düzeyi %99,55 evren · plan düzeyi 607/607 heat_hard). 15c'nin başarı ölçütü "daha çok işlem" DEĞİL, işlem-başı R + sharpe. `docs/UZLASTIRMA-C6-EVREN-MI-ISI-MI-2026-08-14.md`.
- **2026-08-14 WP7-24b ÖLÇÜLDÜ, TEŞHİS DEĞİŞTİ:** kilitli olan araç değil SKILL YOLU — model 202 kez araç çağırmış ama %85'i ham dosya araması, `skill_view` yalnız 5 (%2,5). SOUL düzeltmesi bir KESİNTİNİN içine indi (o gün 550× 404), o yüzden hâlâ sınanmadı. Ayrıca `tool_calls` yapısal −1 (`-Q` özeti bastırıyor) → Meridian kendi defterinden bunu ölçemiyor. `docs/OLCUM-WP7-24B-SKILL-CAGRI-IZI-2026-08-14.md`.
- **2026-08-14 EDG-2026-041 (28a görünmez süzgeç) ÖLÇÜLDÜ + hüküm D1+D2:** korkuluk körlükten değil AYRIMSIZLIKTAN kesiyormuş — `bg_regime` 47/47'de biliniyordu (hepsi `chop`), 46/47 yeniden yazılabilir. Ret yerine `x@<certified>`e çivileme; korkuluk bozulmuyor, güçleniyor.
- **2026-08-14 BEYİN ZİNCİRİ OPENROUTER'A TAŞINDI:** `tencent/hy3:free` OpenRouter kataloğunda HİÇ YOKMUŞ (411 model) — 24 saatte 33/33 boş, çağrıların %46'sı. Zincir artık `nemotron-3-ultra:free` → `gpt-oss-20b:free` (ikisi de ücretsiz), `same_model_ids` İLK KEZ boş. `--provider` yönlendirmesi v244'te; `model.provider auto` alternatifi CANLIDA ÇÜRÜTÜLDÜ (çalışan gemini ayağını da düşürdü).
- **2026-08-14 ALARM GÜRÜLTÜSÜ KÖKÜ (v244):** `intraday_gap_detected` günde 408 = uyarıların %68'i ve 15/15 örneklemle **IEX seyrekliği**, arıza değil (LMT 13:34-37: iex boş, sip dolu). `tur="sembol"` bilgi seviyesine indi, `tur="akis"` warn kaldı. Aynı kök TCA ölçütünü de bozmuştu — besleme kimliği bir ÖLÇÜT KÜNYESİDİR.
- **2026-08-14 PANO TIKANIKLIĞI KÖKÜ (v243):** tohum yenilemesi `recompute.report()` içindeki bar okumasını 95→400 çağrıya çıkarmış; `parity_report` canlıda 17,4→7,8 sn (soğuk) / 11,9→2,1 sn (sıcak), sayfa artık teşhis ucunu BEKLEMİYOR.
- **2026-08-14 dagit [1c] EKLENDİ:** birim dosyası repoda değişip `/etc/systemd/system`e kurulmayınca ayar SESSİZCE ETKİSİZ kalıyordu (aynı gece yaşandı: `MERIDIAN_AGENT_RPD=600`). Kapı yönerge-düzeyinde fark söyler, kurmaz — kurulum bakım penceresinin işi.

- **2026-08-13 ROADMAP YENİDEN YAPILANDIRMA (operatör talebi; denetim `docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md`):**
  12 harfli WP → **WP1-WP11 numaralı ad** (eski adlar "(eski: …)" ile korunur) · **§4 öneri havuzu
  BOŞALTILDI** (29 kalem: 20'si WP'ye taşındı gövde-AYNEN, 9'u + 5 alt-kalem §8 arşive) · dokuz bayat
  iddia üstü-çizili düzeltildi (A1/A2/A5/A7/A9/A12/A13/A14/A16 + A4/A10/A11) · §5'e **"benden
  beklenenler" ÜÇ KOVA** eklendi · §6 kart indeksi 18 kartla tazelendi · iki yapısal artefakt (§4
  numara düzeni + yanlış maddeye yapışmış kuyruk) kapatıldı. **Silme YOK, tarihçe korundu.**
- **2026-08-13 PULLBACK SİLAHSIZLANMASI ÖLÇÜLDÜ, KARAR SIRAYA ALINDI (EDG-2026-039; operatör: "önce diğer işler, bu beklesin"):**
  hüküm "silahsızlanma ÖNERİLİR ama gerekçe **kanıt asimetrisi**"; ΔP&L +3.121$ CI 0-içi, işlem n
  SABİT (kapasite doldu — bağlayan kısıt SLOT değil **ISI**) → operatör kalemi §5 KOVA-2.
- **2026-08-13 TCA — GERÇEK FRİKSİYON İLK KEZ ÖLÇÜLDÜ (EDG-2026-037 + EDG-2026-038):** gerçekleşen
  giriş slipajı replay'in 5 bps varsayımının **~7 katı** (kanonik payda; 3/4 aleyhte) ve E3 kötümser
  bandı DA iyimser; **`RESULT_PF_MIN=1,3` GEVŞETİLMEZ — eşik tartışması KAPANDI** (PF 1,1119 ek
  friksiyonda yükselemez) → Faz-6 `sonuc_hukmu` yapısal kapalılığı **ARIZA DEĞİL, KORUMA**; kalıcı
  metodoloji dersi: *payda farkı = kaynak farkı*.
- **2026-08-13 TOHUM DEFTERİ YENİLENDİ — ÖĞRENME ARTIK DOĞRU ZEMİNDE (EDG-2026-036, operatör onaylı
  pencerede):** 97 → **887** işlem (885 tohum + 2 live_paper), sv=90 ayrı sürüm-uzayı + friksiyon
  şerhi damgalı; 7/8 kapı geçti, **DSR 1e-06 → 0,0391**, korunum açıklanamayan **14 → 3**. ARTIK:
  `equity_curve` yazılmadı → köken sınırı hâlâ 2026-07-20 (WP2-D **ACİL**).
- **2026-08-13 C+mb @5R YEREL OPTİMUM KANITLA (EDG-2026-035, K+=6):** komşuluk 6/6 hücrede
  CI-üstünlük ayağında düştü (slot 15/25 · boyut 0,40/0,65 · zarf 6,5/8,0); slot25 defteri
  **bayt-özdeş** → slot tavanı fiilen ölü knob, ama sektör tavanına YAPIŞIK (WP11-C).
- **2026-08-13 SPRINT KENDİ SYSTEMD BİRİMİNE ALINDI (v241):** sprint ÇÖKMÜYORDU, **ÖLDÜRÜLÜYORDU** —
  çocuk worker'ın cgroup'unda doğuyordu ve `KillMode=control-group` her `restart meridian`da onu
  biçiyordu; çözüm `meridian-sprint@<sid>` şablon birimi + polkit kuralı (`NoNewPrivileges` taviz
  VERMEDEN korundu). Kanıt testi geçti: restart'ın öbür tarafında aynı pid CANLI.
- **2026-08-13 BEYİN ZİNCİRİ AYRILDI (v239):** çağrı-anı ölü model adı tek kapıdan kapatıldı
  (`canonical_model('gemini-3.5-flash')` → `gemini-flash-latest`); nous=tencent/hy3,
  gemini=flash-latest → `brain_chain_distinct` AÇIK. Operatör kaleminin **gerekçesi değişti**:
  "model adı ölü" → **"danışma yolu ölü"** (788 `agent_call`, 385 boş, 1 başarılı görüş).
- **2026-08-13 SOUL.md KİLİDİ AÇILDI (yasak çıktı BİÇİMİNE daraltıldı) — AMA HİÇ SINANMADI:** skill
  çağrı oranının %1,1'den ne olacağı ölçülecek (WP7/24b); skill katmanı aynı gün **WP7 olarak kendi
  cephesine** kavuştu.
- **2026-08-13 KARNE SÜRÜM SPLIT'İ KAPANDI (~22:15Z, canlı doğrulandı):** v5 kaydı uygulamanın KENDİ
  yazım kapısından DB'ye eklendi (`current_version: 5`), v3/v4 tarihçesi korundu (elle SQL YOK).
  KALAN BORÇ: "strateji sürüm terfisi **dagit kapsamı DIŞIDIR**" prosedürü RUNBOOK'a — hâlâ açık (WP5-B).
- **2026-08-13 `goal.max_drawdown` 0,08 → 0,16 (OPERATÖR KARARI, karar penceresi):** hedef sözleşmesi
  maddesi güncellendi; aşağı akış **`shadowlaw.DD_VETO_MARGIN` 0,04 → 0,08** (goal'ün TAM YARISI,
  `62727d6` v238) AYNI turda kapatıldı → §5-12 gerilimi **ÇÖZÜLDÜ**, eski Ö-20a arşive gitti.
- **2026-08-12 KARAR PENCERESİ UYGULANDI — CANLIDA C+mb @5R PAKETİ:** rampa **15/36** (operatör
  talimatı: gerçek-para DA aynı, mod ayrımı YOK) · slot **20** · `position_size_r` **0,5** ·
  **momentum_burst SİLAHLI** (operatör takdiri) · ısı **5R KALDI** (zarf-10 ölçümle elendi).
  Final-paket doğrulaması EDG-2026-032'de **3/3 kapı** geçti (885 işlem · net +20.684,7$ · max-dd
  %12,7 · sharpe 0,521 — **friksiyon şerhli okunur**, bkz. §6).
- **2026-08-12 ON İKİ KART HÜKMÜ (EDG-023…034):** 023 rampa BENİMSENDİ · 024 eşikler DOĞRULANDI
  (kill#1) · 025 mb otomatik-silahlanma YOK · 026 slot20+0,5R baskın · 027 çıkış paketi eşli-CI'da
  düştü · 028 zarf-10 ÖNERİLMEZ + ısı otomatiği YOK · 029 scale-out KAVRAMEN elendi · 030 rejim-eşiği
  40 KALIR · 031 turnover w=0 DOĞRULANDI · 032 final paket 3/3 · 033 düz-0,5R doğrulandı · 034
  skor-sıralı kabul İNERT. _(Tek cümle hükümler §6 indeksinde.)_
- **2026-08-12 ÖĞRENME/GÖRÜNÜRLÜK ONARIMLARI (v234-v239):** `.locks/` budaması + bayat-defter
  göç-süzgeci (v234) · sprint yetim-restart'ı `mesgul` YÜK/YETKİ ayrımıyla açıldı, ardından ölüm
  kökü bulundu (v239→v241) · 4 pozisyon adet-sapmasının kökü ölçüldü (kısmi-dolum DEĞİL,
  **gönderim-anı boyutlama ayrışması**) · MNST split sınıfı teşhis edildi.

- **2026-08-09 ROADMAP §0-6 MİMARİ YENİDEN-ÖRGÜTLEME (operatör onaylı; İÇERİK KORUNDU — silme/özet
  DEĞİL, yeniden-ORGANİZE).** Eski §3-7 düzeni §0-6'ya taşındı. **Eski başlık → yeni bölüm haritası:**
  eski §3 "ŞİMDİ" GÜNCEL-DURUM bloğu → §3 tepesi; eski §3 gece-vardiyası/denetim-kuyruğu tarihçesi →
  §8 oturum snapshot'ları · eski §4 DURUM PANOSU → §8 snapshot · eski §5 PLAN WP'leri → §3 (aktif: WP-E/
  WP2/WP-U/WP-S/WP-S2/WP-M/WP-D/WP-H/WP-QC/WP-UX/WP-P/WP-L) ve §8 (tamamlanan: WP0/WP1/WP3/WP-G/WP-R/
  WP-K/WP-N) · eski §5 SIRALAMA → §0 · eski §6 YASALAR → §0 · eski §7 YAPMA LİSTESİ → §6 (kill-list) ·
  eski §8 OPERATÖR + §8.1 envanter → §5 · eski §7 KARAR GÜNLÜĞÜ → §7 (aynen). Bitmiş dalgalar (KOVA-B,
  WP-N, dalga-3) §8'da; WP-U/QC keşfi §6 kanıt + §5 operatöre dağıtıldı; kartlar §6 indeksinde. Hiçbir
  bilgi kaybı yok: taşınan bloklar byte-özdeş; her açık kalem §3/§5/§6'te temsil edildi.
- **2026-08-09 EDG-2026-022 ÖLÇÜLDÜ — FINVIZ HARCAMASI GEREKÇESİZ:** de-risk+tavan birlikte %65,84
  (CI >%50) BASKIN; evren bağlayıcı DEĞİL (%34,17). Asıl kaldıraç de-risk rampası/`eff_max_open`.
  Rejim-koşullu KILL#3: chop'ta (nadir %6,7) evren baskın ama genel+trend_up de-risk baskın. Sonuç:
  `FINVIZ_API_KEY` operatör-bloğu (§5-8) DE-RISK edildi — evren bağlamadığı için token parası şimdilik
  gerekçesiz. Otonom kart, blok değil; `docs/KESIF-WP-U-2026-08-09.md`.
- **2026-08-09 EXE-2026-004 (N4) AŞAMA-1 ÖLÇÜLDÜ, AŞAMA-2 DONDURULDU:** üç tüketici ölçütü ölçülebilir
  zarar göstermedi → cf çıkış-tipleri EKLENMEDİ (+0,039R iyimserlik sapma olarak KAYITLI, düzeltilmedi).
  Aşama-2 (çıkış tipleri modeli + TÜM cf tarihi yeniden koşum) eşiğe ulaşılmadı; bakım penceresi şartlı
  (saatler, state'e yazar → canlı worker koşarken YAPILMAZ). Eşikler ölçümden ÖNCE donmuş, DEĞİŞMEDİ.

- **2026-08-09 DÖRT-CEPHE KEŞİF TURU + BAKIM PENCERESİ ONAYI (commit `068a580`):** operatör onayıyla
  dört büyük cephede SALT-ÖLÇÜM keşfi koşuldu (git yasaklı, canlı salt-okunur, `meridian/` dokunulmadı) —
  `docs/KESIF-WP-{U,QC,HD,MKP}-2026-08-09.md`. Her cephede küçük otonom çekirdek + büyük operatör-bloğu;
  en değerli bulgu: **FINVIZ'e para harcamadan ÖNCE "evren bağlayıcı mı" ölçülmeli (EDG-2026-022)**.
  ÖZET: WP-U evren=251=REPLAY_UNIVERSE, FINVIZ %100 ölü · WP-QC FREE hesap açık, ⑤ en düşük blok, LEAN
  dotnet/docker yok · WP-H H9 kapı-dışı yazım (auth._write) + systemd-143 CANLI DEĞİL (N1 ön-şartı) ·
  WP-MKP WP-M 11 açık / WP-K hipotez yok / WP-P P1-P10 kapalı (tek borç RUNBOOK 32 prosedür). **BAKIM
  PENCERESİ ONAYLANDI:** OB-2 systemd exit-143 daemon-reload → OB-1 N1 kanal → OB-4 restart→PBO (M2)
  damgalama çapraz-kaldıraç; N4 cf çıkış-sadakati (saatler, state'e yazar) aynı pencerede. Bloklar §8-8..11.
- **2026-08-09 WP-UX D0-D6 BAYAT-KAYIT DÜZELTİLDİ (git otoritesiyle):** ROADMAP D0🔄/D1-D6📋 gösteriyordu
  ama git D0-D6'nın HEPSİNİN indiğini kanıtladı — v196 `c59dfcc` (D0) · v197 `6025d82` (D1) · v198 `07deab7`
  + v199 `c0d8238` (D2) · v200 `ac86de9` + v197 `7b9158a` (D3-UI/arka) · v201 `9cd27de` (D4) · v208 `11bdc02`/
  `4560362` (D5) · `b71f65b`/`64009ca` (D6) · v229 `6bb2bb9` 16:45 (D3-b F1/F2/F14). Hash'ler doğrulandı.
  `KESIF-WP-MKP` §0 "D0-D6 inmedi" bayat-ROADMAP'e güvenmişti (git yasağı, ~16:30 ölçüm), git ÇÜRÜTTÜ.
  Kalan açık: D3-c altı modül + D3-b F3-F13/F15.
- **2026-08-09 ~09:00 GECE+SABAH DÖRT DAĞITIM İNDİ (v216→v196, son `964696b`):** WP-N kanıt-hızı
  dalgası (v216-v219) + koruma×süpürücü kök düzeltmesi (v220+v221) + dalga-2 sahte-yeşil avı
  (v222-v226) + null-sıfır kapısı (v196). Sistem paper/sağlıklı, otoriter suite yeşil, 4 pozisyon
  korumalı. Kapsam hasadı `docs/SABAH-TRIYAJI-2026-08-09.md` (13/13 gerçek kalem, 0 çürük).
- **2026-08-09 KORUMA ARKI KAPANDI — E1-v2 → N6 çarpışma → v220+v221 kök düzeltme:** E1-v2 (v209-v211,
  TIF gtc + `cancel_open_entries` kadansı) korumayı ölmez kılmıştı; N6 devir tatbikatı v211'in
  bağımsız OCO'sunun 08-07'de süpürüldüğünü ARTEFAKTTAN yakaladı → çarpışma yeniden açıldı; v220
  (P-KORUMA aile kemeri + yön kemeri) + v221 (OCO grup kemeri) süpürücüye korumayı YAPISAL tanıttı.
  CANLIDA md5+broker doğrulandı (4 OCO); davranışsal EOD kanıtı Pazartesi.
- **2026-08-09 N6 DEVİR TATBİKATI KOŞTU — "✅ KAPANDI" yalanı ARTEFAKTTAN yakalandı:** bağlamsız
  ajan (oturum hafızası yok, salt-okunur canlı) devralmayı denedi, koruma kapanış beyanının
  doğrulanmadığını buldu. Ders: bir kalem ancak artefaktı canlıda doğrulanınca ✅.
  `docs/DEVIR-TATBIKATI-2026-08-09.md`.
- **2026-08-09 DALGA-2 SAHTE-YEŞİL AVI (v222-v226) + v196:** "doğru çalışıyor ama kendini yanlış
  anlatıyor" sınıfının son kalıntıları — liveness ölçümü (sprint orphan + öğrenme durması),
  tohum/canlı karne ayrımı, E2 totoloji+kilit, SB-1 boyut makbuzu, universe-unknown alarmı;
  v196 null-sıfır kapısı dalga-2'nin 15 yeni guard'ını SINIFLADI (15/15 meşru, tavan 181→192).
- **2026-08-09 WP-N W1 (v216) SERMAYE BEKÇİLERİ + KARTLAR:** SB-4 damgasız-yazım + SB-3
  `taban_kaymasi` indi (WP-S N3); NAKED_POSITION jetonu ayrıldı (N1 kod); gölge planlı-kol
  (v217, EXE-2026-003) + skill görüş defteri (v218, EDG-2026-019 — figürler kuru-koşu) kartları
  indi. Ölü-mekanizma avının beşinci kovası: `docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md`.
- **2026-08-03 OPERATÖR MANDASI — STRATEJİDE TABU YOK:** "katı hiçbir kural yok; değişmesi
  gereken değişir, kalkması gereken kalkar." Hiçbir strateji bileşeni (çıkış/boyutlama/skor/
  evren/ufuk/yaşayan sinyaller dahil) dokunulmaz değildir; QC-ders hükümleri ve sonraki tüm
  turlar tam yapısal serbestlikle verilir. DEĞİŞMEYEN tek şey karar TERAZİSİ: ölçüm-önce +
  kart + kill-disiplini ("değişmesi gereken"i keyfîden ayıran mekanizmanın kendisi).
- **2026-08-02 ~21:20 EDG-016 KANIT ZİNCİRİ KAPANDI + A1'E DAĞITIM.** Kartın hükmü depodaki yolu
  gösteriyordu ama kod damgası + damgalı betikler scratchpad'deydi; sınıf avı 012–014 kodunu da
  yakaladı → 11 dosya damga-SHA doğrulamalı `wp2_olcum/` arşivine (039c5b8, merge 06e8f60);
  `dagit.sh --uygula` yeşil (bounds/goal canlı=repo BİREBİR · healthz 200 · A1'de 13 dosya
  bayt-özdeş). 70c61f4 token-bekçisi onarımları aynı dağıtımla canlıya indi. Ders günlükte:
  "measured" = kanıt+damga+kod depoda — damga kodsuz yaşayamaz.
- **2026-08-02 ~17:40 GECE KAPANIŞI: KOVA-B CANLIDA — dağıtım kapısı kırmızıyı yakaladı, kök çözüldü,
  A1 yeni kodla.** Kapı açılınca dağıtım-öncesi tam suite İLK KEZ otoriter koşuldu ve 16F/2E yakaladı
  → `--uygula` durdu (kapı çalıştı). Bisect kökü: 0a4453f iki-motor ATR bacağı DOĞRU sıkılaştırması
  v76 fikstür kanıt tabanını 17<30'a düşürdü → onarım FİKSTÜRDE (da6bec3; geometri+16 sembol,
  17→68 işlem, eşik/assert değişmedi). Girişim avı ÇÜRÜTMELİ kapandı: sızıntı ipucu yanlış alarm
  (bounds/goal = c783442 git-çıkışı), 9'lu aile = YÜRÜYEN-AĞAÇ artefaktı (a75a207 statik koşu 0/9);
  DERS: otoriter suite yalnız DONMUŞ ağaçta. Yapısal kilitler: close_engine_position/replace_order_stop/
  cancel_order üç ateş-duvarı listesine (b6273af). Freeze 571a094 → otoriter suite 3752/0 → pencere
  14:00 UTC → birim migrasyonu token-korumalı TEMİZ (journal 0/48) → adım-7 doğrulaması yeşil
  (healthz 200 · 3 birim aktif · scheduler 0,7 dk · evren 251 · fail-notify bayt-özdeş) — BLOKE
  ÇÖZÜLDÜ (25e8824). Kadans dersi kalıcı: log-edit + runbook_uret TEK commit (t3 aynası).
- **2026-08-02 ~04:30 GECE KAPANIŞI: S2R ÜÇLEMESİ TAMAM + KOVA A 9/9 — DAĞITIM OPERATÖR KAPISINDA.**
  S2R-1 kabuk (f7f66fa) → S2R-2 göç 20 bölüm + YASA-6 emekli listesi (9ca0998) → S2R-3 cila +
  bekçi ÖLÇÜLEMEDİ yüzeyi + palet-20 (006cc67). Denetim KOVA A: d50b03b/395920e/8a38248 +
  close_connections yeniden-adı (8ac8e1a, C5 yasa-çivisi isim çakışması). Final tam suite ~3.600
  test SIFIR kırmızı; dagit kapıları [0a-0c]+kuru-koşu YEŞİL. `--uygula` izin-sınıflandırıcısına
  takıldı (2 ret — otonom pencerede canlı-sunucu yazımı; karar operatöre bırakıldı, tek komut:
  `./dagit.sh --uygula`). A1'de C15 canlı hasarı ölçüldü: sprint HER 5-DK poll'de yeniden
  tetikleniyor (99 start, tamamlanma olayı YOK, w_turnover örneklemesi 0) — düzeltme dağıtımla
  iner, kadans kendini bir koşuda onarır; sprint erken-ölümü AYRI şüphe (dağıtım-sonrası izleme).
- **2026-08-02 ~03:30 TAM-SİSTEM DENETİMİ İNDİ (operatör talebi: "bütün bileşenler").** 8 salt-okuma
  denetçi + şiddet≥3'e adversarial doğrulayıcı (34 ajan): **25 doğrulanmış ciddi bulgu** (19 şiddet-3)
  + 22 hafif + 1 çürütülen. Rapor+triyaj: `docs/SISTEM-DENETIMI-2026-08-02.md`. KOVA A (9 sessiz-güvenli
  hata-yolu düzeltmesi) gece kapatılıyor; KOVA B (16 karar-değiştiren: en kritiği C9 çıkış-ayna kopukluğu)
  operatör sabah onayında. Yan kazanım: her-gece-sprint gizemi çözüldü (C15 damga-ezilmesi).
- **2026-08-01 ~17:50 UIUX S1 CANLIDA (otonom gece, pencere-5).** WP0 onaylandı → S1 iki ajanla:
  DTCG tokens.json (eş-doğrulamalı; ham-renk istisnası SIFIR çıktı) + 136-çift kontrast raporu
  (8 beyansız bulgu — B1 merdiven-çöküşü, B6 aynı-renk-iki-seri: refinement-turu adayı) + RUNBOOK
  yüzeyi (50 bölüm kaynak-türetimli, 34 dürüst-boşluk; /runbook auth'lu, alarm→çapa bağlı) +
  g-kısayolları + soru-cümleleri. YAN AV: CSP listesinde eksik virgül — palette.js hiç
  denetlenmemişti. Suite-10 yeşil. Gece nöbetçisi A1'de (trend_book/turnover/yedek).

- **2026-08-01 ~16:15 GÜN KAPANIŞI (tam-güç günü).** Mutasyon %49→%86,8 (28-ajan Workflow) ·
  EDG-016 turnover SUCCESS→KABLOLANDI (bounds'ta bakir düğme) · BASE-001 karne: '+%2,5/4,5yıl,
  2024-bağımlı' + huni üç-darboğaz · sermaye tohum-ayrıştırması CANLI (100k gerçek-canlı taban;
  rampanın hayalet-tepe kusuru dahil) · WP-P pano dönüşümü CANLI (sessiz-hat 16/17'yi dürüstçe
  gösterdi + alarm-KPI ilk gün tepe-aşımını yakaladı + ⌘K palet) · dagit sır-silme sınıfı kapandı ·
  8-K vekili + P9 dışında WP-P tamam. DÖRT pencere, DOKUZ tam-suite, ~50 commit. İzlemede: akşam
  trend_book doğumu + turnover ilk örneklemesi + restart-patlamasının alarm-tepesini şişirmesi
  (yarın: dağıtım-penceresi muafiyeti değerlendirilebilir — bilinçli, ölçülmüş karar ister).

- **2026-08-01 ~16:00 BÜYÜK HÜKÜM GÜNÜ KAPANIŞI.** EDG-016 turnover SUCCESS (yeni yaşayan sinyal;
  net +0,55% @20; survivorship-şerhli) · EDG-013 devir-arşiv · EDG-015 VCP-çatı arşiv (a-fortiori:
  canlı skor kesit-sıralaması @10 TERS — stratejik izleme) · EDG-012/014 arşiv · EDG-011 askı
  (PIT-takvim birikimi başladı) · EDG-010 arşiv+ders#3. WP2 KOMPLE ÇÖZÜLDÜ (EDGAR, operatörsüz);
  WP-K hipotez listesi SIFIR. Karne: 19 kart → 16 hükümlü (14 arşiv + trend-kolu + turnover),
  1 askı, 1 ölçüm-altyapı (EXE), mutasyon-karnesi koşumda. İki pencere daha (sabah H11+gölge-kitap,
  öğlen WP-M/WP-D/pano) — üçü de temiz. Sıradaki: turnover-kablolama turu + H5 ilk skor + akşam
  trend_book doğumu.

- **2026-08-01 ~09:45 PARALEL DALGA İNDİ.** H3 tur-2 seccomp 6.3→2.1 OK · WP-D teyit (kapı 3/4
  aktif dışlıyor; DLTR kaynak-onarımlı) · EDG-010 pullback ARŞİV (lafzen-success/kanıten-kenarsız;
  WP-M ders #3: ham-getiri ölçütü yasak) · PARA-v3 ①② indi (realized_usd + mtm_dd_veto, geriye-uyum
  çivili; ölçek borcu rakamla görünür: n_ölçülen=0) · EDG-005 kapı emekliliği + component_ic aracı
  (kuru: 61/63 hücre; rs cf/havuz ANLAMLI NEGATİF — w_rs=0.35 İZLEME) + mutmut fikstürü (--kisa
  kanıtlı) · .gitignore ölü-negasyon: goal/bounds ilk kez gerçekten versiyonda. Karne 15 ölçülen →
  14 arşiv + 1 yaşayan. AKŞAM PENCERESİ PAKETİ: kod dağıtımı + component_ic --uygula + bounds knob
  düşümü.

- **2026-07-31 ~21:45 GÖLGE-KİTAP TURU KAPANDI.** Trend kolu canlı paralel-defter olarak hazır
  (d3425e2); dağıtım paketi = H11 + SQLite −0.0 düzeltmesi + gölge-kitap (migrasyonsuz düz kod);
  tam suite koşuyor, yeşilse pencere operatöre tek komutla hazır. 23:32 yedek + ~02:00 ilk
  SQLite-gecesi döngüsü izlemede.

- **2026-07-31 ~15:30 EDG-009 TREND-RAFİNE HÜKMÜ.** Rafine üstünlük kanıtlanamadı → ham kol
  incumbent; KALICI PIT ŞERHİ: fazlanın ~yarısı evren-seçim yanlılığı (~6-7p/yıl, D t=2.08
  hayatta); 2021+ = oynaklık, decay değil; eşik-dilbilgisi dersi WP-M'ye. Pozitif kontrol
  0.000000. Kanıt research/olcumler/trend_rafine/. Sıradaki: aylık gölge-kitap Opus turu.

- **2026-07-31 ~sabah WP-G + WP1 HÜKÜM GÜNÜ.** EDG-005 SMA-kapısı ARŞİV (tanı turu: OOS etkisi
  sıfır — fark IS-yankısıymış; temiz pencerede kill#1; "oosonly standardı" WP-M'ye sınıf dersi
  olarak girdi; ci_para kökü: _slim'in pnl_dollars düşürmesi) · EDG-006 ToM ARŞİV (ön-adım, yön
  ters) · EDG-007 residual momentum ARŞİV (6/6 CI-0-içi; residmom≈rawmom ρ=0,63 yapısal; FF3
  verisi yan-kazanım olarak repo'da). Skor: 12 ölçülen aile/filtre → 11 arşiv + 1 yaşayan
  (uzun-ufuk trend). Aynı gün: git kuruldu (H8), SQLite defter-çekirdeği turu sahada (H9).

- **2026-07-31 ~07:00 MÜHENDİSLİK EL KİTABI TURU (operatör dokümanı).** 2024-26 araştırma anketi
  gerçekle çarpıştırıldı → WP-H açıldı. Üç düzeltme: Meridian SQLite-backed DEĞİL (Litestream
  ailesi reddedildi) · git YOK = en büyük boşluk (operatör kararına sunuldu) · systemd 9.2 UNSAFE
  ölçüldü + pano token'ı unit'te düz metin (H3). uv audit temiz + dağıtım kapısına kablolu;
  CLAUDE.md yazıldı. Aynı sabah: EDG-006 ToM ön-adımda arşiv (yön ters −11,8bps) · EDG-005
  "AÇILABİLİR" hükmü mekanizma-kanıtına kadar ASKIDA (pozitif kontrol aslında geçiyor —
  tum-digest artefaktı; tanı ajanı sahada) · EDG-007 residual momentum kartı açıldı, ölçüm ajanı
  sahada (FF3 ingestion dahil).

- **2026-07-31 ~03:00 GECE DALGASI DAĞITIMI (operatör uykuda, tam-yetki).** 6 kod kolu tek bakım
  penceresinde: WP-E + SIP-yasası + pano + BT-1 migrasyonu (95/95 seed damgası) + round-2
  (karantina-v2 8 onarım + bütünlük 61 sembol) + regime üretici düzeltmesi + tick-bekçisi.
  Suite ~2.900/0. İlk canlı kanıtlar: `alpaca_sip_skipped_current_session` + damga sayaçları.
  Gece ölçüm hükümleri: 52wh/volshock/MAX/EAP arşiv (kartlarda gerekçeli), ToM yeni kart,
  WP3.1 4/4 birinci-el, PIT üyelik verisi repo'da. Koşan: WP-R + SMA/ToM.

- **2026-07-31 ~04:00 PLAN WP-KONSOLİDASYONU (operatör talimatı).** Eski §5.0-3.5'in tamamı iş
  emrinin WP yapısına döküldü: örtüşenler emildi (Y2→WP-E · G2-adayları→1.4 kartı · Y3-SMA/VIX→WP-G
  · Y6-transkript→3.3 bileti · Y6-13F→WP-U · G7→1.5 · G3b→WP-R), örtüşmeyenler yeni WP oldu
  (WP-R rampa/çıkış [EN YÜKSEK] · WP-U evren/PIT · WP-K kurulum/aile · WP-M metodoloji borçları ·
  WP-D veri bütünlüğü · WP-L ölçek merdiveni). Kapalılar işaretli: WP0 ✅ · 2.4-EAP ✅ edge-yok ·
  3.2-insider ✅ kalıcı-arşiv. Ön-kayıt metinleri research/cards/'a taşındı; §3/§4 sabah
  konsolidasyonunda tazelenecek (bayat oldukları burada beyan).

- **2026-07-30 TEMİZLİK + KABLOLAMA TURU KODLANDI — DAĞITILMADI (Rol 2).** Ölü-mekanizma avının
  kapanışı; hedef sözleşmesi md.1: "kablola / emekli et / belgele — üçü dışında hiçbir şey kalmaz".
  Dokunulan: `meridian/{watchdog,notify,broker,regime,shadowlaw,api,scheduler,skills,reflect*}.py`
  (*yalnız yorum/belge), `meridian/adapters/{alpaca,fmp,macro,news,insider,finviz*}.py`
  + yeni `tests/test_temizlik_kablolama_v137.py` (57 test) + 5 mevcut test dosyası güncellendi + §8.1
  tablosu + bu not. `hermes.py`/`shadow_model.py`/`sprint.py`/`loop.py`/`analytics.py`/`health.py`/
  `codelaw.py`/`adapters/data.py`/`web/app.js` DOKUNULMADI (HALT delegasyonu `health.set_halt`i
  ÇAĞIRIR, dosyayı DEĞİŞTİRMEZ); **`state/`e YAZILMADI** (doğrulandı: tur boyunca `state/` altında
  hiçbir dosyanın mtime'ı değişmedi); **DAĞITILMADI**.

  **① EMEKLİ EDİLENLER (13 fonksiyon + 2 sabit = 15 ad; her biri çağıran taramasıyla, her biri
  geri-al notu bırakarak).**
  Tarama `meridian/ + tests/ + ops/ + deploy/ + skills/` üzerinde yapıldı ve HER birinde tek eşleşme
  tanımın kendisiydi: `alpaca.paper_client` (SDK sarmalayıcısı — kağıt yürütme REST/httpx yolundan
  gidiyor; `_client` KORUNDU, `live_client`ın tek dayanağı) · `fmp.income_statement` /
  `fmp.search_name` / `fmp.stock_list` (üçü de kota yakabilen, hiçbir karara bağlı olmayan ağ yolu) ·
  `macro.snapshot` / `macro.status` (modül MEZAR TAŞINA çevrildi — `regime.classify`ı sarmalıyordu,
  canlı yol onu zaten doğrudan çağırıyor) · `news.stock_news` / `news.status` / `news.available` /
  `MAX_SYMBOLS` (aynı — mezar taşı; N1/N3 dersleri metinde KORUNDU) · `broker.PaperBroker.
  open_risk_dollars` (ikinci bir "açık risk" gerçeği; canlı tavan R biriminde ve `guard.py`de) ·
  `regime._slice` (tek satırlık dilimleyici) · `shadowlaw.score_eski_yasa` (eski yasanın hükmü ZATEN
  `money_score_detail`in `score_eski_yasa` ALANINDA kayda geçiyor) · `notify.data_quality` (kendi
  docstring'i K1'de zaten "emekli, çağıran eklenmez" diyordu — beyan fiiliyata geçirildi; tek kapı
  `obs.alarm(ALARM_DATA_QUALITY)` ve o zaten susturma penceresi uyguluyor).
  **İKİ AV ADAYI ÇÜRÜTÜLDÜ ve operatör kalemi olarak belgelendi (§8.1):** `MERIDIAN_SUPERVISED`
  (`ops/com.meridian.agent.plist:31` onu KURUYOR → süreç ölümünün operatöre ulaşan iki yolundan
  biri) ve `reflect.propose_deterministic` (Eksen-2 kolu gerçekten koptu — `skills.axis2_cycle`
  devraldı — ama `reflect --auto` CLI'ı README:81'de operatör komutu olarak yazılı).

  **② KABLOLANANLAR (tetikleriyle).** ① Sağlayıcı sağlık kartı → `/api/diagnostics.saglayicilar`
  (finviz/massive/insider/shortinterest/alpaca-veri/alpaca-ticaret; beşinin de sağlık sayacı
  ölçülüyor ve dördünün okuyucusu YOKTU). Ortak biçim + üç dürüstlük kuralı: ölçülemeyen **None**
  (0,0 değil), `son_basari_ts` yalnız `ok is True` iken dolar, kapsam `surec-ici` diye BEYAN edilir.
  ② Y4 toplama → scheduler seans-sonrası kancası, seans başına 1× (`y4_session`, KALICI).
  ③ `validation_report.build/render_text` → haftalık kadans, `state/validation_report.json`,
  `/api/diagnostics.mlops.validation_report`. ④ `massive.verify` → aynı haftalık blok (yazım
  kapısının dayanağı bayatlamasın). ⑤ `massive.reset_cache` → EMEKLİ EDİLMEDİ, **bakım yoluna
  bağlandı**: docstring'in "gün dönümü" gerekçesi GEÇERSİZDİ (iki sözlük de tarihe anahtarlı, bayat
  veri servis edilemez) ama SIZINTI gerçekti (memo `{tarih: {~12.400 sembol}}`, 7/24 worker'da hiç
  boşalmıyordu) → yeni seans kovalaması başlarken temizlenir; memo diskten geri dolar, ağa çıkmaz.
  ⑥ `shadowlaw.variance_drift` (YENİ) → haftalık MEASURED_V3 kayma bekçisi. **Toleranslar
  uydurulmadı**, üçü de kodda yazılı gerekçeden türedi: marj çevriminin YUVARLAMASI
  (`0,02 × margin_scale` hâlâ `MONEY_GATE_MARGIN`e yuvarlanıyor mu), veto marjının kendi gürültüsünün
  DIŞINDA kalması, PARA payının TEK TERİM özdeşliği. Bekçi UYARIR, **sabiti değiştirmez** (operatör +
  Rol 1 kararı). ⑦ HALT tek kapı: `api_halt`/`api_resume` artık `health.set_halt`e delege ediyor
  (kardeş kapı `api_intraday_arm` zaten `set_intraday_arm`e delege ediyordu; `set_halt`in üretim
  çağıranı yoktu — yani kapının "resmî" hâli ölü, kopyası canlıydı). ⑧ `watchdog.EXPECTED` 9 → 17:
  öğrenme turunun dört kadansı (`shadow_fit`/`axis2_cycle`/`opinion_backfill`/`sprint_cadence`)
  nabız ATIYOR ama listede olmadıkları için `report()` onları ARAMIYORDU — nabzı atılıp beklenmeyen
  bir mekanizma, durduğunda MECHANISM_STALE üretmez. Yeni dördü de eklendi. Kısılabilen kadanslar
  (dolgu/sprint) 9 günlük pencerede: kısılmayı arıza sanan bir dedektör gürültüyle susturulur.
  ⑨ **Eksen-2 cf kolu (Rol 1 tasarım kararı, uygulandı):** örneklem kapısı iki kollu oldu —
  `n >= min_n` **VEYA** (`n >= min_n/2` **VE** `n_cf >= 5·min_n`). cf tek başına öneri TETİKLEMEZ
  (gerçek katman ölçülmemişse `avg_r is None` → kol açılmaz); yön hükmü **yalnız** gerçek katmandan;
  cf-destekli satır `kanit: "gercek+cf"` künyesi taşır ve rationale'inde cf payını AÇIKÇA yazar.
  `axis2_diagnosis` beyanı güncellendi ("cf OKUNMUYOR" artık yanlış olurdu) ve yetersiz-örneklem
  kovası ikiye ayrıldı.

  **③ Y4 KABLOLAMASI — Rol 1'in canlı sondası kadansı DEĞİŞTİRDİ (brief eki, aynı gün).** FMP
  ÜCRETSİZ planında ölçüldü: `search?symbol` → **402**, `limit>100` → **402**, `page>=1` → **402**
  (yalnız `page=0` çalışıyor), `date=` parametresi **sessizce yok sayılıyor** (200 + günün verisi).
  Yani `fetch_delta`ın sayfalama yolu bu planda ÖLÜ. Kadans `VARSAYILAN_SAYFA_TAVANI` (40) yerine
  yeni `insider.PLAN_SAYFA_TAVANI` (=1) kullanıyor — 40'lık tavan her gece 39 boşa 402 yakardı.
  402 `obs.log` ile TEK SATIR bilgi olarak geçiyor (alarm DEĞİL: her gece tekrarlayan ve ancak plan
  yükseltilerek çözülebilen bir uyarı, gerçek uyarıları okunmaz yapar). Sağlık kartında
  `plan_siniri: page0-only`. **DÜRÜSTLÜK DÜZELTMESİ:** dosyanın başlığındaki ve
  `codelaw.DECLARED_SINKS`teki "günlük biriktirmeyle 3 yıllık pencere dolar" cümlesinin ÖLÇÜLMEMİŞ
  BİR UMUT olduğu yazıldı — günde tek sayfa = ~100 dosyalama, evren isabeti ~6/100 ve `latest` akışı
  GERİYE derinleşmez, İLERİ akar; o pencere bu yoldan ancak 3 yıl BEKLEYEREK dolar. (`codelaw.py`
  bu turun dosyası değil — oradaki aynı cümle Rol 1'e bırakıldı.)

  **④ SINIF AVI — "kodda örtük zaman/yayın varsayımı" (T+1 kusurunun sınıfı).** Üç aday okundu:
  * **finviz keşif zamanlaması → BULUNDU, BELGELENDİ (davranış değişmedi).** Önbellek anahtarı
    `date.today()`, yani SUNUCUNUN YEREL takvim günü. Zincir günde İKİ çekim yapıyor: biri kapanış
    sonrası kovalamada (`use_cache=False`, doğru), biri yerel gece yarısından sonraki ilk poll'de
    (önbellek tarihi tutmayınca `use_cache=True` bile `discover()`a DÜŞÜYOR). Örtük varsayım:
    "yerel gün sınırı NY seansının (13:30-20:00 UTC) dışına düşer". UTC/Amerika/Avrupa'da doğru;
    UTC+10:30…+14'te yerel gece yarısı seansın İÇİNE düşer ve gün-içi filtre değerleri önbelleğe
    yazılırdı. Koşum yerleri o bantta değil (geliştirme makinesi UTC+3; A1'in TZ'si bu depodan
    doğrulanamadı — systemd birimi TZ ayarlamıyor). Varsayım artık `discover_universe` docstring'inde
    YAZILI. Ucuz çözüm (UYGULANMADI, Rol 1): anahtarı son kapanmış seansa bağlamak — varsayımı
    kaldırır ve günde iki olan çekimi bire indirir.
  * **earnings takvim tazeleme → NET AMA KAPSAM DIŞI (AÇIK).** Ölçüm: tazeleme penceresi
    `[bugün-7, bugün+14]`, kadans haftalık, `BLACKOUT_DAYS = 5`. Normal işleyişte bir sonraki
    tazelemeden hemen önceki asgari ileri kapsama `14-7 = 7` gün > 5 → **2 gün marj**. AMA
    `earnings_calendar_gave_up` (5 deneme) hafta damgasını YAKAR: bir hafta kaçarsa sonraki deneme
    7 gün daha ileridedir → ileri kapsama **0**'a iner ve `in_blackout` herkes için False döner
    (guard FAIL-OPEN, bilanço gününde işlem açılır). Yani örtük varsayım "haftalık kadans hiç
    kaçmaz" ve TEK kaçan hafta marjın %100'ünü yiyor. Sessiz DEĞİL (`earnings_calendar_gave_up` +
    `earnings_refresh_empty` + `coverage().future_dates`). Düzeltilmedi: `earnings.py` bu turun
    dosyası değil ve iki çözüm de (ileri pencereyi genişletmek / pes ederken hafta damgasını
    yakmamak) davranış kararıdır. Not: Nasdaq ucu ANAHTARSIZ ve ~15 istek — pencereyi genişletmenin
    kota maliyeti ≈ 0.
  * **bararchive Redis TTL → AÇIK (mimari karar Rol 1'de).** Ölçüm: `BARS_MAXLEN = 900` (~2 seans),
    `BARS_TTL_S = 172800` (2 gün). TTL'nin KENDİSİ belgeli. Belgeli OLMAYAN: **arıza hâlindeki kayıp
    penceresi**. `archive_frame` `hotstate.ingest_bars` içinden satır-içi çağrılıyor, her istisnayı
    yutup False dönüyor ve `_WARNED` global'i yüzünden SÜREÇ BAŞINA TEK uyarı basıyor; watchdog'a
    bilerek bağlanmamış (gerekçe yazılı: seans-dışı sahte bayat alarmı). Sonuç: sürekli bir arşiv
    arızası tek olay satırı üretir ve Redis çerçeveleri ≤2 günde döndürür → sessiz kayıp penceresi
    ~2 seans. Dokunulmadı: `barsarchive.py`nin kendi notu iki arşivin birleştirilmesini/emekliliğini
    zaten Rol 1'e devretmiş ve `bararchive.py`/`hotstate.py` bu turun yüzeyi değil.

  **⑤ TESTLER.** Yeni `tests/test_temizlik_kablolama_v137.py` — **57 test, hepsi yeşil**: emeklilik
  ("gerçekten yok" + geri-al notu + `_client` korundu), operatör kalemleri (plist ve README kanıtı
  KODLA doğrulanıyor — kaynak kaybolursa test kırılıp kararı yeniden aldırır), sağlayıcı kartı
  (None≠0, `son_basari_ts` yalnız ok iken), Y4 (tetik / kota kısılması / plan sınırı / bir ayak
  düşünce öteki yaşar / damga kalıcılığı), haftalık üçlü (tetik / nabız / hafta kısılması / anahtarsız
  atlama / bekçi sabiti DEĞİŞTİRMİYOR), memo temizliği (tetik + yalnız seans değişiminde + ağa
  çıkmıyor), HALT tek kapı (delege +
  davranış aynı + statik `touch/unlink` yok), watchdog (AST taramasıyla "nabzı atılan her ad
  EXPECTED'de mi"), Eksen-2 cf kolu (cf tek başına tetiklemiyor / birleşik koşul / rationale şeffaf /
  eski yol değişmedi / PROTECTED delinmiyor). Güncellenen 5 dosya: `test_macro_news_audit_v20.py`
  (denetim → emeklilik çivisi, 6 test — dersler mezar taşında korunuyor), `test_gaps_final_v52.py`
  (determinizm çivisi `regime.classify`a devredildi), `test_review_backlog_v98.py` (#7'nin dersi
  emeklilikte de korunuyor), `test_na_revision2_v54.py` (saflık çivisi `fmp.status`a devredildi),
  `test_ogrenme_otomasyonu_v136.py` (cf beyanı çivisi YÖN DEĞİŞTİRDİ: artık kolun SINIRINI kilitliyor).
  TAM SUITE KOŞULMADI (Rol 1'de).

  **⑤b ROL 1 TAM-SUITE TRİYAJI — BAYAT ÇİVİ TAŞINDI (aynı gün, ek görev).**
  `tests/test_agent_efficiency_v9.py::test_axis2_recommendations_ignore_cf_columns` FAILED verdi.
  Çivi KAYNAK-METNİ yasaklıyordu: `recommend_from_attribution` içinde `"cf_avg_r"`/`"n_cf"` dizeleri
  geçemez. **ÖNCE GERÇEK KUSUR MU DİYE SINANDI** (Rol 1'in şartı: cf tek başına tetikleyebiliyorsa
  düzeltme, RAPOR ET). Dört bağımsız sonda, dördü de `[]` döndü:
  ① gerçek katman ölçülmemiş (`avg_r=None`) + cf n=100.000, cf_avg_r=−5,0 → öneri YOK
  ② gerçek n=3 (eşiğin yarısı 4'ün altında) + cf n=100.000 → YOK
  ③ gerçek n=4 ama cf n=39 (eşiğin 5×'i 40'ın altında) → YOK (birleşik koşul gerçekten VE)
  ④ **en sert hâl:** gerçek katman NÖTR ölçülmüş (0,0R), cf katmanı −5,0R → YOK. Yani yön
  karşılaştırması `cf_avg_r`yi OKUMUYOR; cf yalnız örneklem kolunda. → **Tasarım kusuru YOK, çivi
  BAYAT.** Kaynak-metin çivisi bu ayrımı yapısal olarak yapamaz (iki kullanım da aynı dizeyi içerir),
  bu yüzden çivi DAVRANIŞA taşındı ve ÜÇE bölündü: (a) cf TEK BAŞINA öneri üretemez — yukarıdaki
  dört vaka parametrize (eski korumanın YAŞAYAN yarısı), (b) birleşik koşulda öneri üretilir,
  `kanit="gercek+cf"` künyesi taşır ve rationale cf payını + "HÜKÜM gerçek katmandan"ı BEYAN eder,
  (c) cf'siz yol AYNEN durur (`n >= min_n` iken cf'ye bakılmaz, künye `gercek`, rationale'e cf
  cümlesi sızmaz, PROTECTED yeni koldan da delinmez). Eşikler testte SABİTLERDEN okunuyor
  (`sk.CF_REAL_FRACTION`/`sk.CF_SAMPLE_MULT`) — sayı ikinci kez yazılmadı. Dosya: **13 test yeşil**
  (1 kaynak-çivisi → 6 davranış vakası). Modül docstring'inin #3 satırı da güncellendi.

  **⑥ ROL 1'E UYARI — TAM SUITE'TE ÇIKACAK, BU TURUN ÜRÜNÜ DEĞİL.**
  `tests/test_api_contract.py::test_benchmark_relative_beat_flag_is_a_plain_bool` sırayla bazen
  ERROR veriyor: `conftest._no_live_state_writes` "CANLI state'e YAZILDI" diyor. KÖK NEDEN ÖLÇÜLDÜ
  ve bu turun diff'iyle ilgisi YOK: o test `sandbox_state` fikstürü ALMIYOR, yani `analytics.
  benchmark_relative()`i CANLI state üzerinde koşuyor; çağrı canlı SPY bar önbelleğini yüklüyor ve
  `adapters/data.py`nin hayalet-seans onarımı devreye giriyor (`bar_ghost_session_dropped` →
  `bar_cache_repaired`), yani test bir CANLI YAZIM deniyor ve bekçi haklı olarak düşürüyor.
  Doğrulandı: `state/bars/SPY.csv` satır 3752 = **2018-11-22** (Şükran Günü) ve satır 5386 =
  **2025-05-26** (Anma Günü) — ikisi de XNYS'te KAPALI gün, yani gerçek hayalet satır. Kesintili
  görünmesinin sebebi `pytest-randomly`: sıra rastgele ve SPY'ı ilk okuyan testin sandbox'lı olup
  olmaması değişiyor. Bu turda DOKUNULMADI çünkü `analytics.py` ve `adapters/data.py` bu turun
  DOKUNMA listesinde ve iki çözüm de (teste `sandbox_state` vermek / canlı önbellekteki iki hayalet
  satırı temizlemek) ya başka bir iş kolunun dosyası ya da `state/`e yazmak — bu tur `state/`e
  yazmadı. Rol 1'e bırakıldı.

- **2026-07-30 ÖĞRENME OTOMASYONU TURU KODLANDI — DAĞITILMADI (Rol 1).** Operatör mandası: "elle
  tetik beklemeden tam fonksiyonlu". Dokunulan dosyalar: `meridian/{scheduler,shadow_model,hermes,
  skills,analytics,api,sprint}.py` + yeni `tests/test_ogrenme_otomasyonu_v136.py` (27 test) + bu not.
  `loop.py`/`reflect.py`/`watchdog.py`/`web/app.js` DOKUNULMADI; `state/`e YAZILMADI.
  ① TEŞHİS — kusurun adı "eksik çağrı" DEĞİL, **REHİNELİK**. `shadow_model.refit_and_save` (loop.py:796)
  ve `skills.auto_shadow_from_evidence` (loop.py:848) ZATEN çağrılıyordu — ama ikisi de P5_LEARN ⊂
  `daily_cycle` ⊂ "yeni seansın barı geldi" zincirindeydi. Canlı ölçüm: scheduler `last_summary=noop`,
  kapsama 0,172, `portfolio.last_date=2026-07-28` → veri hattı takıldığı gece öğrenme de duruyor ve
  durduğu hiçbir yerde yazmıyor. (Kanıt ki model eğitimSİZ değildi: `shadow_model.json` n_fit=2201,
  brier_train=0,2431, 2026-07-29T21:10Z.)
  ② ANTRENMAN: `shadow_model.maybe_refit()` + `dataset_fingerprint()` + `training_status()`. Tetik =
  model yok VEYA kaynak defterlerin (trades/trade_plans/counterfactuals) boyut+mtime parmak izi değişti
  VEYA `force`. Bütçe = parmak izinin kendisi (fit saf-numpy, LLM kotası harcamaz). Yetki DEĞİŞMEDİ:
  terfi hükmü `evaluate_promotion`ın yazılı kuralı, tek sonucu `shadow_veto`. `n_live=0` DÜRÜST —
  `p_win_shadow` damgası 2026-07-21'de başladı, damgalı 23 planın hiçbiri henüz kapanmadı (95 kapanmış
  işlemin 0'ı damgalı); terfi kod değil VERİ bekliyor.
  ③ DOLGU: `backfill_opinions(max_days=None)` → tavan `hermes.backfill_budget()`ten türer, seans-sonrası
  kadansa bağlandı, `backfill_progress` olayı kuyruğu (kalan gün/satır) yayınlıyor, `watchdog.beat`
  atıyor. Pano düğmesi ELLE HIZLANDIRMA olarak kaldı (artık kendi `max_days`ini vermiyor — tek formül).
  KUYRUK ÖLÇÜLDÜ ve brief'teki 390 sayısı YANLIŞ: dolgu yalnız SONUCU BİLİNEN plana dokunabilir
  (kalibrasyon çifti sonuç ister) → **93 gün / 95 satır** dolgulanabilir; 386 plan görüşsüz ama 291'inin
  sonucu yok. Türetilmiş tavan (kalan 140) = 46/gece → kuyruk ~3 gecede erir.
  ④ EKSEN-2 ÜRETECİ — KİM ÇIKTI, NEDEN SESSİZDİ. İki üreteç var: (a) `skills.recommend_from_attribution`,
  TEK çağıranı `reflect._proposal` (reflect.py:643) ve deftere ancak o öneri `_submit_locked`e
  (reflect.py:706) ulaşırsa yazılıyor — yani üreteç bir HİPOTEZ ÖNERİSİNİN YAN ÜRÜNÜ; hermes'in canlı
  yollarının ikisi de o alanı boş bırakıyor (beyin zinciri hiç doldurmuyor, `propose_virgin_knob`
  BİLEREK `None` yazıyor). (b) `auto_shadow_from_evidence` (H5, bugün eklendi), loop.py:848 → aynı
  rehinelik. ÇÖZÜM `skills.axis2_cycle()`: ikisini de kadansa bağlar, `record_recommendation`ı doğrudan
  çağırır. `reflect.py`ye DOKUNULMADI (Rol 1'in kararına bırakıldı). EŞİK DEĞİŞTİRİLMEDİ — ölçüldü:
  `recommend_from_attribution()` = [] DÜRÜST bir sıfır (korumasız skillerden yalnız vcp n=91 avg_r=0,000
  eşik aralığında; pullback n=4 < min_n=8 ve zaten gölgede). Ama eşiğin YAPISAL körlüğü var ve
  `axis2_diagnosis()` onu sayıyla yazıyor: eşik YALNIZ gerçek katmana bakıyor, `catalog()`ün bugün
  taşımaya başladığı cf katmanını (`n_cf`,`cf_avg_r`) hiç okumuyor → en büyük örneklemli iki skill
  (momentum-burst n_cf=1080, vcp n_cf=1004) gerçek katmanda n=0/n=91 olduğu için üretecin gözünde YOK.
  ÖNERİ (uygulanmadı): eşiğe cf kolu eklenmeli, H5'in üçlü koşulu (cf eşiği + gerçek katman aynı yönde)
  desenini izleyerek.
  ⑤ BÜTÇE ÖZ-AYARI — `hermes.quota_state()` tek türetim yeri. `kalan = AGENT_RPD − agent_budget.json[day]`
  (gün damgası bugüne ait değilse 0); soğuma = `brain_cooldown("agent")`. `backfill_budget = 0` eğer
  soğumada, aksi `max(1, floor(kalan × 1/3))`. Pay 1/3 çünkü canlı yollar (öneri/inceleme/sıralama/
  nous_eval) aynı kovadan içiyor ve ölçülmüş tüketimleri kotanın ~%7'si (day=10/RPD=150) — 1/3 pay o
  tüketimin ~5 katını rezerve bırakır. Env override (`MERIDIAN_BACKFILL_MAX_DAYS`) türetimi DEVRE DIŞI
  bırakır; bozuk değer uyarıyla türetime döner. **BEYAN EDİLMİŞ SAPMA — `search_budget()`:** yönerge
  "soğumada sıfıra" diyordu, uygulanmadı ve nedeni ölçülebilir: `SEARCH_BUDGET` bir LLM değil CPU
  bütçesidir (walk-forward sayısı) ve beyin zinciri sustuğu gece hipotez üreten TEK mekanizma o aramadır
  — sıfırlamak son kolu tam da diğerleri düştüğünde kesmek olurdu. İlişki TERS ve SINIRLI kuruldu:
  taban `SEARCH_BUDGET` (=10), beyin kapalıyken `min(SEARCH_BUDGET_MAX=20, 2×taban)`; asla 0 olmaz.
  ⑥ ÖĞRENME ANTRENMANI (sprint) — Rol 1 ek mandası. `sprint.maybe_start()` + `should_run()` +
  `auto_config()`; docstring'in "Operator-triggered" ibaresi güncellendi. Ölçüm: son sprint 2026-07-22
  (8 gün önce), `learning_scorecard.outcomes_measured=1` ve o TEK satır H00026 (`source: sprint_search`,
  realized_delta −0,0364) — yani karnedeki tek ölçülmüş sonuç gerçekten sprint kökenli. Kadans
  zamanlayıcının **"current" (boşta) dalına** bağlandı, `fresh` bloğuna DEĞİL: `fresh` bloğu aynı
  `advance_once` çağrısında birkaç satır sonra EOD döngüsünü başlatıyor ve ikisi 8 çekirdeği paylaşırdı.
  Kapılar: aktif sprint / çağıranın meşguliyet sinyali (`refetch_chase`) / canlı arama
  (`hermes.SEARCH_PROGRESS`) / gece dilimi [22:00,06:00) / tetik (haftalık 7 gün VEYA 5 taze hipotez);
  her ret ADIYLA raporlanır. Bütçe türetimi ÇEKİRDEKTEN (kotadan değil — sprint LLM ÇAĞIRMAZ):
  `isci = max(2, min(4, çekirdek−2))` (reflect'in kendi formülü), `budget = clamp(3×isci, 6, 24)`,
  `k_max = clamp(1+isci//2, 2, 4)`. Bu makinede (8 çekirdek) formül **bugünkü elle yazılmış varsayılanları
  birebir yeniden üretiyor** (12/3) — ölçülmüş değeri yeniden üretmeyen bir formül türetim değil yeni
  bir sabit olurdu. Override: `MERIDIAN_SPRINT_BUDGET` / `MERIDIAN_SPRINT_KMAX` + pano/CLI düğmesi.
  ⑦ `sprint_runs.jsonl` TERS ORPHANININ KÖK NEDENİ BULUNDU. Kayıtlı teşhis "defter ya hiç doğmadı ya
  07-23 taşımasında kayboldu" diyordu — İKİSİ DE DEĞİL: `sprint_run` çocuk süreçtir ve `MERIDIAN_ROOT=
  <sbroot>` ile koşar, yani defteri KUM HAVUZUNA yazıyor. Üç sandbox'ın üçünde de dosya yerinde
  (921/921/443 B). `sprint.status()` okuyucusu yanlış rafa bakıyordu; kum havuzlarını gezecek şekilde
  düzeltildi (yazarı canlıya yazdırmak izolasyonu delerdi).
  ⑧ KARNE KABLOLAMASI (YASA 6): `hermes_scorecard()` → `kesif_payi` (bugünkü `exploration_share`, tek
  tüketicisi hermes'in KENDİ istemiydi — operatör göremiyordu), `butce` (arama+dolgu türetimleri),
  `ogrenme_otomasyonu`. `learning_scorecard()` → `besleme` bloğu (antrenman durumu / dolgu kuyruğu /
  antrenman sprinti); eski anahtarların HEPSİ yerinde (testle çivili). `/api/diagnostics` → `ogrenme`
  bloğu + `scheduler.learn_session`. **app.js'e DOKUNULMADI** — alanlar API'de hazır, pano turu Rol 1'de.
  Uydurma YOK: 0 ship / 0 terfi / outcomes_measured=1 rakamları AYNEN duruyor; eklenen tek şey "0'ın
  NEDENİ"nin ölçülebilir hâli.
  ⑨ AÇIK BIRAKILANLAR (Rol 1). (a) `watchdog.EXPECTED`e üç satır: `shadow_fit`/`axis2_cycle`/
  `opinion_backfill` (+`sprint_cadence`) — `beat()` atılıyor, veri var, ama MECHANISM_STALE onları
  izlemiyor; watchdog.py bu turun dosya sınırının dışındaydı. Tazelik geçici olarak
  `analytics.learning_automation().nabiz`ta kadansların KENDİ damgalarından ölçülüyor
  (`mechanism_beats.json` beyanlı bir lağım — dışarıdan okumak `codelaw` `stale_sinks` ihlali olurdu).
  (b) **KIRMIZI TEST, BENİM DEĞİL:** `tests/test_sprint.py::test_reflect_once_searches_when_no_claude`
  düşüyor — sebebi BUGÜNKÜ keşif-dengesi turunun `VIRGIN_FALLBACK` yolu: test `dataset.load`u
  ("BARS","IDX") ile ve `search_and_submit`i mock'luyor ama `reflect.submit`i mock'lamıyor; yeni yol
  gerçek `submit`e giriyor ve `backtest.py:147`de `'str' object has no attribute 'set_index'` atıyor.
  `HERMES_VIRGIN_FALLBACK=0` ile test GEÇİYOR → üretim değil FİKSTÜR boşluğu. Testi düzeltmek mevcut bir
  test dosyasına dokunmak demekti (sınır dışı), o yüzden raporlandı. (c) Eksen-2 eşiğine cf kolu (④).
  ⑩ TAM SUITE TRİYAJI — İKİ EK BULGU (Rol 1 sevkiyle, 2026-07-30 gece).
  (a) `test_na_revision_v53.py::test_scheduler_owns_only_its_own_state` BAYAT ÇİVİYDİ, sahiplik ihlali
  DEĞİL. Çivi elle yazılmış bir literal kümesi sayıyordu ve o gün İKİ meşru artefakt eklenmişti:
  `learning_cadence.json` (bu tur) ve `validation_report.json` (eşzamanlı Y4/doğrulama turu). AST
  taraması ikisinin de TEK yazarının `scheduler.py` olduğunu doğruladı (depo geneli sahiplik taraması
  `test_no_module_writes_another_modules_file` yeşil). Çivi, kardeşlerinin desenine (`probgate.META_FILE`,
  `shadow_model.STATE_FILE`) çekilerek adları artık MODÜLDEN okuyor — elle kopyalanmış bir ad, dosya adı
  değiştiği gün çiviyi sessizce yanlış yapardı. 30/30 yeşil.
  (b) **KENDİ SOKTUĞUM GERÇEK KUSUR — SAAT BAĞIMLI SUITE.** Sprint kadansını zamanlayıcının boşta dalına
  bağlarken `advance_once`ın İKİ çağıranı olduğunu gözetmemiştim: daemon `_run` döngüsü VE panonun ELLE
  TİK düğmesi (`api.py:1823`). Saat 22:00'yi geçip gece kapısı açılınca testlerin doğrudan çağırdığı
  `advance_once()` GERÇEKTEN bir `meridian.sprint_run` alt süreci başlattı. Paket 18:00-21:00 arası
  yeşil, 23:52'de kırmızıydı — sıra bağımlılığının daha sinsi kuzeni: gece yarısına kadar görünmez.
  DÖRDÜNCÜ KAPI eklendi (`_thread.is_alive()` → `mesgul:elle_tik`), ve gerekçesi test değil DOĞRULUKTUR:
  operatör "bir tur ilerlet" düğmesine bastığında 4 çekirdek yiyen dakikalarca sürecek bir antrenman
  başlatmayı istememiştir; sprint'in elle tetiği ayrı bir düğmedir (`/api/sprint/start`) ve o hiçbir
  kapıya uğramaz. VM worker (`run.py`) `loop.daily_cycle`ı doğrudan çağırır, etkilenmez. Regresyon çivisi
  `test_elle_tik_ASLA_sprint_alt_sureci_baslatmaz` SAATTEN BAĞIMSIZ (gece kapısı zorla açılır, hüküm
  yalnız daemon ayrımına bakar) ve mutasyon testiyle doğrulandı: kapı kaldırılınca DÜŞÜYOR.
  KAZA CANLIYA DOKUNMADI — kopyalanan state pytest'in tmp `sandbox_state`iydi: `state/sprint/` hâlâ eski
  üç kum havuzu, `sprint_status.json` 2026-07-22'de, koşan `sprint_run` süreci yok, canlı defterde 0
  test artefaktı. Test sayısı 27 → **28**.

- **2026-07-30 ÜRETEÇ KEŞİF DENGESİ TURU KODLANDI — DAĞITILMADI (yarın sabah Rol 1).** Nous N00002'nin
  implementasyonu; dokunulan dosyalar YALNIZ `meridian/hermes.py` + yeni `tests/test_uretec_kesif_dengesi_v135.py`
  + bu not. SORUN (ölçüldü): 41 hipotezin %51,2'si `stop_loss_atr_mult`ta (21 deneme, 0 ship),
  32 düğmenin 18'i hiç hipotez taşımamış; H2 (`analytics.dead_families`) bunu ZATEN ölçüyordu ama
  isteme yalnız kanıt paketinin İÇİNDE, tavana çarpınca düşebilir ham veri olarak giriyordu.
  ① İSTEM: `_user_prompt`ın her iki dalına (şemalı/şemasız) `_exploration_sections()` eklendi —
  (A) ÖLÜ AİLELER (deneme/ship/ölüm sebebi kırılımı/denenmiş değerler + "bu aileden yeni deneme
  için FARKLI bir ret sebebi gerekçelendir" + K/p_required maliyeti), (B) BAKİR DÜĞMELER (H2'nin
  listesi + bounds aralıkları + canlı değer/"unset"). YÖNLENDİRME, kota DEĞİL: kapı tek hakem, beyin
  serbest. Bölümler kanıt paketinin İÇİNDE değil ARDINDA — `_render_pack` tavan taşmasında alanları
  tümden düşürüyor ve bu turun tek çözdüğü şey bu iki bölümün beyne ULAŞMASI. Ölçü: bölüm 2,6k
  karakter; SYSTEM'e HİÇBİR ŞEY eklenmedi (statik sabit + cache_control sözleşmesi duruyor).
  ② DETERMİNİSTİK YOL — ESKİ DAVRANIŞ (okunduğu hâliyle): beyin zinciri boş dönünce `reflect_once`
  TEK akıllı hamle üretmeden DOĞRUDAN koordinat-inişi aramasına düşüyordu; `reflect.propose_deterministic`
  hermes'in yolunda HİÇ çağrılmıyor (yalnız `reflect --auto` CLI'sinde) — yani yuva BOŞTU. Arama sırası
  denenmemiş düğmeleri zaten öne alıyor (`_ucb_rank` → +inf) ama arama sondaları DEFTERE YAZILMIYOR,
  dolayısıyla bakir düğme aramada denense de "hiç önerilmemiş" kalıyor ve kör nokta kapanmıyordu.
  YENİ: `propose_virgin_knob()` yuvayı H2'nin bakir listesinden dolduruyor (değer = bounds ORTA NOKTASI,
  adıma oturtulmuş; no-op ise denenmemiş yarıya bir adım; o da no-op ise sonraki düğme). Guard ÖN-DENETİMİ
  zorunlu (gerçek aylık kota ile): guard'a takılan bir öneri deftere `rejected_by_guard` yazar ve düğme
  HİÇ ÖLÇÜLMEDEN bakir listesinden düşerdi. Bakir kalmayınca/hiçbiri geçmeyince ZARİF düşüş → davranış
  birebir eski hâl. Kaynak etiketi `deterministic:virgin`. Dağıtım anahtarı `HERMES_VIRGIN_FALLBACK=0`.
  ③ ÖLÇÜM (YASA 6): `exploration_share()` — son 12 önerinin aile dağılımı, bakir isabet (öneri kendi
  ailesine defterdeki İLK dokunuş mu), ölü-aile tekrar oranı (H2'nin BUGÜNKÜ hükmüne göre; sapma beyanlı).
  Ölçülemeyen None. TÜKETİCİ: istem bölümünün son satırı + yeni `python -m meridian.hermes --kesif`
  (karneyi basan `analytics.system_telemetry`/`/api/diagnostics` yolları BAŞKA dosyaların malı — bu tur
  onlara DOKUNMADI; panoya bağlama Rol 1'e kalan iş). Canlı ölçüm bugün: son 12 öneride bakir isabet
  10/12, ölü-aile tekrarı 2/12 — yoğunlaşma TARİHSEL (21 stop denemesi eski), kör nokta ise güncel (18/32).
  ④ UYDURMA YASAĞI/TEK KAYNAK: bakir liste, ölü aile hükmü, aile tanımı (`_knob_family`) ve eşik
  (`DEAD_FAMILY_MIN_N`) H2'den ALINIR — ikinci sayım YAZILMADI. ⑤ DEĞİŞMEZLER korundu: HYP_SCHEMA
  geriye-uyumlu (yeni zorunlu alan yok), K/`k_probes` muhasebesi aynı (bakir öneri `probes_tested`
  YAZMAZ → K=1), H4 bütçesi ve guard'lar el değmedi, ship yetkisi yalnız `reflect.submit`
  (h1b yasa-çivisi yüzünden `reflect._proposal` ÇAĞRILMADI, öneri sözlüğü hermes'te kuruldu).
  TESTLER: yeni dosyada 27 test (hepsi geçti); mevcut hermes'e dokunan 20+ dosya koşuldu;
  `codelaw.report()` ok=True / silent_handlers=0 / artifact_violations=0. TAM suite Rol 1'de.
  İKİ FİKSTÜR BOŞLUĞU — ÜRETİM HATASI DEĞİL (Rol 1 tam-suite triyajında buldu, ikisi de düzeltildi):
  `test_sprint.py::test_reflect_once_searches_when_no_claude` ve
  `test_regime_patch.py::test_reflect_once_targets_live_nondefault_regime`. İkisi de `reflect.submit`i
  mock'lamıyordu; yeni bakir hamle GERÇEK backtest'e girip stub/None bar'larda patlıyordu. AYNI onarım
  (a): fikstüre eksik `submit` basamağı eklendi ve İDDİAYA dahil edildi — sprint'te "bakir yol tek
  öneri verir → ship etmez → arama PRODUCTION pencereleriyle devralır", regime_patch'te ayrıca "bakir
  hamle her zaman KÜRESELdir (`@rejim` yok), rejim hedefleme kararı bütünüyle aramaya ait kalır".
  `HERMES_VIRGIN_FALLBACK=0` yamalama seçeneği İKİSİNDE DE REDDEDİLDİ: testi varsayılan-olmayan bir
  yapılandırmada koşturmak, bakir yol bir gün yansımayı yutarsa testleri yeşil bırakırdı.
  SINIF AVI (üçüncü kardeş yok): `reflect_once`a değen 5 test dosyası tarandı — kalan ikisi YAPISAL
  olarak bağışık, şansla değil. `test_hermes_audit_v28` iki testinde de `propose_with_llm` GERÇEK bir
  öneri döndürüyor, yani bakir dal hiç girilmiyor (h1d'de öneri sertifikasız-rejim kapısında düşüyor —
  o düşüş bakir daldan SONRA olduğu için yuvayı yeniden doldurmuyor; kasıtlı: guardrail'in düşürdüğü
  bir yuvayı doldurmak guardrail'i delerdi). `test_hermes_runtime` doğrudan `hermes.reflect_once`ın
  kendisini mock'luyor. Koşum: test_regime_patch 28 + v135 27 = 55 geçti; test_sprint 17 + v135 27 +
  hermes audit/prompt = 79 geçti.
  BENİM OLMAYAN 3 HATA (aynı triyaj çıktısında, dokunulmadı): `test_api_contract` +
  `test_hafta3b_v125` benchmark/bootstrap testleri teardown'da canlı-yazım bekçisine takılıyor —
  yazılan satırlar `bar_ghost_session_dropped`/`bar_cache_repaired` (SPY), yani benchmark yolu
  SANDBOX İÇİNDE koşarken CANLI SPY bar önbelleğini okuyup ONARIYOR. Kanıt bana ait olmadığına dair:
  her iki dosya TEK BAŞINA koşturulduğunda da, `HERMES_VIRGIN_FALLBACK=0` ile de birebir aynı üç hata
  çıkıyor. Ayrı bir tur ister (canlı defteri kirletiyor ve canlı bar önbelleğini değiştiriyor).
  BEYAN (YASA 4): geliştirme sırasında `propose_virgin_knob` bir kez SANDBOX DIŞINDA denendi ve
  canlı `state/events.jsonl`e TEK bir info satırı düştü (`hermes_virgin_proposal`, 17:49Z, satır
  26831) — defter geri düzeltilmedi (ikinci bir yazım daha kötüydü); başka hiçbir canlı state yazımı
  YOK, kalan tüm koşular sandbox'ta.
- **2026-07-30 ~20:35 İST: İKİ TUR A1'E DAĞITILDI (kapanıştan önce).** Kod rsync + uv sync +
  restart; healthz 200, heartbeat taze; `OnFailure=meridian-fail-notify` kurulu dosyaya cerrahi
  eklendi (üretilmiş token korundu, CHANGEME=0); codelaw ihlalleri dağıtım sonrası 0 (panodaki
  kalabalık eski kod/state uyumsuzluğuydu). 07-29 deliği (44/259) bilinçli olarak bu akşamki yoğun
  fazda kapanacak (onarım tetiği fresh-penceresine bağlı; 07-29'un penceresi dağıtım öncesi yanmış).
  Bu gece İLK aynı-akşam denemesi: kapanış+16 dk'da SIP bacağı → beklenti `alpaca_sip` damgalı
  07-30 barları + repair(07-29) + hacim kalibrasyonu bootstrap. VM-dışı yedek çekici Mac'te kurulu
  (LaunchAgent 21:40; TCC: anahtar ~/.ssh/oci-a1.key'e kopyalandı — ~/Documents'ı launchd okuyamıyor,
  duman testiyle kanıtlandı). Operatör kalemi: bildirim kanalı kimliği (fail-notify şimdilik beyanlı no-op).
- **2026-07-30 VERİ KAPSAMA / AYNI-AKŞAM BACAĞI TURU İNDİ (Rol 1 kabulü; tam not:
  oturum scratchpad `veri_turu_notu.md`).** KÖK NEDEN (Rol 1, kanıtlı): bar zincirinin birincisi
  Massive ücretsiz katmanı seansı T+1 yayınlıyor (kanıt `massive_grouped_last.json`: date 07-28,
  fetched_at 07-29 21:15); zamanlayıcının 8×300 sn (~40 dk) bütçesi bu yüzden HEP boş dönüyor,
  seans "atlandı" ilan edilip bir daha onarılmıyordu — 07-29 barı hâlâ 44/259 sembolde, 164
  tarihsel atlama aynı imza. FMP bilgi katmanına tahsis edilince akşam-yayın varsayımı sessizce
  çökmüştü: sistem fiilen T+1 ritmindeydi ve her seans için sahte SEANS ATLANDI alarmı üretiyordu.
  ÇÖZÜM (4 parça): ① `alpaca.same_evening_bars` — birincil `feed=sip` (Rol 1 CANLI KANITI:
  ücretsiz paper anahtarla dünün barı HTTP 200 + konsolide hacim; `delayed_sip` bu uçta "invalid
  feed" → merdivenden çıkarıldı), yedek IEX snapshot + sembol-başına hacim kalibrasyonu (canlı
  ölçüm: IEX hacmi konsolidenin medyan %2,2-2,5'i — ölçeksiz yazım rvol'ü ~40× küçültürdü);
  damgalar `alpaca_sip`/`alpaca_iex`, abonelik reddi 6 sa soğur, ham hata olaya yazılır.
  ② T+1 Massive düzeltmesi otoriter üstüne-yazım — watchdog'a DOKUNMADAN mevcut
  `_changed_rows → _bump_wf_rev` sanctioned yolundan (`bar_source_upgrade` olayı: seans, n, maks
  |Δclose|/c, hacim oranı); dikiş istisnası adlı ve üreticisi kilitli (yalnız bacağın kendi geçici
  barları). ③ Onarım geçidi `data.repair_coverage`: son 5 seansın deliği grouped'la kapanır
  (07-29 deliği ilk turda kapanmalı). ④ Merdiven: sık faz aynen (8×poll), sonra 30→45→60 dk
  seyrek kovalama; TERMİNAL atlama+alarm yalnız SONRAKİ seans kapanışında (imza korundu); geç bar
  `session_bar_arrived_late`. Ölçüm defteri `state/bar_same_evening.json` (beyan edilmiş sapma:
  `data_quality.json`'ı loop her seansta sıfırdan yazıyor — birikim orada yapısal imkânsız);
  tüketici `scheduler.status()["bar_upgrade"]` → /api. Replay yolu bacağı GÖRMEZ. 3 bayat
  yasa-çivisi + v64 dikiş çivisi yeni yasaya taşındı ("pes sınırı" denemeden ZAMANA); v133
  sıra-bağımlılığı fixture ile kapatıldı (kirleten: alpaca `_TRANSPORT` mutlak sayacı). Yeni test
  dosyası `test_ayni_aksam_bacagi_v133.py` (32); NİHAİ OTORİTER SUITE: %100 tamam, 0 fail/0 error
  (~2.500 test). YAN BULGU (ayrı çip oturumunda): ANSS/DFS/FI/HES/IPG bayat sembol şüphesi.
- **2026-07-30 GÖLGE-v2 YAŞAM-DÖNGÜSÜ MOTORU İNDİ + DAYANIKLILIK ÇİFTİ.** Yeni
  `meridian/shadow_lifecycle.py`: varyant başına KALICI kâğıt defteri (`state/shadow_books.json` +
  `state/shadow_trades.jsonl`) — fill → yönetim → çıkış → mark, her gün, canlı akışın taze
  barlarıyla. Kanca v1 ile AYNI (`loop.daily_cycle` → `shadow_variants.record_cycle`; loop'a eklenen
  tek şey `bars=per, index_bars=idx, regime_ok=regime_ok` — ikinci bir bar yükleyici YOK).
  **YASA KOPYALANMADI:** kitap bir `broker.PaperBroker` ÖRNEĞİDİR (fill/gap koruması/likidite
  tavanı/notional tavanı/kısmi satış/bar-içi muhafazakârlık/komisyon-kayma muhasebesi hep
  üretimden), yönetim `strategy.manage_position`, ADV `backtest._adv`, kısma `broker.derisk_mult`/
  `max_positions_at`, tarama+kapı `shadow_variants._signals`/`._judge` (→ `strategy.scan_all` /
  `guard.classify_gate`). **Kopyalanan TEK şey sürücüdür** (`step()`in OPEN→INTRADAY→CLOSE faz
  sırası, kaynağı `backtest.replay` 182-351 olarak yazılı) — replay kendi takvimini ve kendi
  brokerını kurduğu için çağrılamıyordu.
  **TASARIM SAPMASI (bilinçli, Rol 1 briefinden):** V3/V6 `shadow_variants.VARIANTS`e EKLENMEDİ;
  ayrı bir `LIFECYCLE_ONLY` setinde duruyorlar ve payda İKİYE ayrıldı — `k_variants`=4 (KARAR
  sorusu, v1 defteri) ve `k_lifecycle`=6 (PARA sorusu, kitap defteri). Gerekçe: çıkış düğmeleri
  `scan_all`/`classify_gate` yolunda hâlâ HİÇ okunmuyor (v123 çivisi bunu ölçüyor), yani karar
  defterinde V3/V6 hâlâ kontrol koluyla ÖZDEŞ; onları oraya geri koymak 07-30'da tam bu gerekçeyle
  yapılan temizliği geri almak ve V1/V2/V4'ün çoklu-karşılaştırma cezasını SIFIR ölçüm kazancı
  karşılığında artırmak olurdu. Kitapta ise gerçekten ayrışıyorlar. Yan fayda: mevcut v1 çivilerinin
  HİÇBİRİ gevşetilmedi (test dosyasına dokunulmadı).
  **YENİ KOLLAR:** V3 `exit.early_kill_pivot=1` (`early_kill_bars` VARSAYILANDA 1 — iki düğmeyi
  birden oynatmak "hangisi etkiledi"yi ölçülemez yapardı; pivot artık `_judge` yan haritası →
  `fill_entry(pivot=)` → `Position.pivot` yolundan taşınıyor, yani kitapta GERÇEKTEN ateşliyor) ·
  V6 `exit.scale_out_frac=0.5` (YALNIZ frac: `scale_out_r` zaten 2.0 — E4 no-op tuzağı).
  **NO-OP GUARD ÖLÇÜMDÜR, KONVANSİYON DEĞİL:** `noop_arms()` her kolun ETKİN parametre sözlüğünü
  kontrol kolununkiyle OKUNAN anahtar düzeyinde karşılaştırır; ayrışmayan kol turdan düşer
  (obs.warn + `dropped_arms`). Varsayılan tablosu (`LIFECYCLE_READ_DEFAULTS`) bir KOPYA olduğu için
  AST testiyle kaynaktaki literallere çakılı — strategy/broker varsayılanı değişirse test patlar.
  **TOHUMLAMA (Nous N00005):** ilk koşuda son 5 seans aynı `step()` sürücüsüyle geriye doldurulur,
  yalnız defter BOŞKEN; satırlar `seeded: true` taşır ve `ts` GERÇEK yazım anıdır (retro-damga
  yasağı), seans tarihi ayrı alandır. **KARNE:** `--karne` CLI — varyant × {n_islem, ort_R, PF,
  para, maxDD, açık_poz} + V5 kontrolüne göre fark; para sütunu `shadowlaw.ret_c_v3` (probgate'in
  PARA-v3 tek-terim yasasıyla AYNI ölçek), ölçülemeyen değerler None. Kitapların DIŞ okuyucusu
  `shadow_variants` (codelaw YASA 6 zinciri: sl YAZAR → sv OKUR).
  **KİMLİK:** kapanan gölge işlemi `SV-<kol>-<tarih>-<ticker>`; `ledgers.PLAN_ID_RE`/`CF_ID_RE` ile
  eşleşmediği testle çakılı. **ARIZA:** bir kolun patlaması turu düşürmez, kitabı da SİLİNMEZ
  (açık pozisyonları düşürmek gerçekleşmemiş K/Z'yi yok etmek olurdu) — kitap ilerlemez ve arıza
  `last_error`/`failed_days` ile damgalanır.
  **DAYANIKLILIK ÇİFTİ:** yeni `ops/pull-a1-backups.sh` (A1'deki `state-*.tar.gz` arşivlerini bu
  Mac'e rsync'ler — yalnız eksikler, `--delete` ASLA, yerelde 30 gün budama; kurulum komutları
  betiğin başında) + `ops/com.meridian.backup-pull.plist` (LaunchAgent, StartCalendarInterval 21:40
  → Mac uykudaysa uyanınca telafi; hedef ~/AI-Trading, yani ESKİ ~/Documents TCC engelinin DIŞINDA
  — tek kalan temas SSH anahtarının yolu ve okunamazsa betik çıkış kodu 2 ile bağırır). Yeni
  `deploy/oracle-a1/meridian-fail-notify.service` (oneshot; `meridian.service`'e `OnFailure=` ile
  bağlı, `deploy.sh` kuruyor) — süreç ÖLÜYKEN haber verebilen tek katman; kanal yoksa
  `notify.configured()` False → beyan edilmiş NO-OP, birim 0 ile çıkar ve nedenini journal'a yazar.
  **KOŞULMADI/ELLE:** yedek çekici ve LaunchAgent bu turda KURULMADI ve KOŞTURULMADI (ağ+A1 erişimi
  bu ajanın yetkisi dışında) — kurulum operatörde. **OPERATÖR KALEMLERİ:** ① bildirim kanal kimliği
  (`TELEGRAM_BOT_TOKEN`+`TELEGRAM_CHAT_ID` ya da `MERIDIAN_WEBHOOK_URL`) kurulmadıkça fail-notify
  no-op'tur; ② `launchctl bootstrap` ile yedek çekicinin kurulması; ③ A1'e dağıtım (Rol 1);
  ④ gölge-v2 kartının panoya bağlanması SONRAKİ tur (bugünkü tüketici CLI + testler).
  **TESTLER:** yeni `tests/test_golge_v2_yasam_dongusu_v132.py` (27 test: fill+gap koruması, erken
  itlaf, kısmi satış, breakeven, dokunuş çıkışı, uçtan-uca arm→fill, no-op reddi, varsayılan-tablo
  AST çivisi, kimlik ayrıklığı, tohumlama tek-seferliği, karne/PARA-v3, iki payda, sıfır yetki,
  artefakt grafiği, dayanıklılık çifti). Mevcut v123/v125/v57/v59/v60/v122 çivileri KIRILMADI.

- **2026-07-30 5.1 ORACLE TAŞIMA KİTİ HAZIR (yazıldı, KOŞULMADI — kesme kararı operatörde).**
  `deploy/oracle-a1/` altında: yeni `cutover.sh` (yerelden tek komut; sıra **durdur → rsync →
  deploy → token → doğrula**, çünkü koşan worker'dan alınan state kopyası yarım defter taşır),
  yeni `meridian-barsarchive.service` (worker'dan AYRI birim — yereldeki serve.sh/`stop_worker`
  ayrıklığının systemd karşılığı: pano restart'ı bar akışını kesmesin) ve yeni
  `meridian-backup.{service,timer}` (23:30 UTC, 7 gün, yalnız yerel disk). **ÜÇ GERÇEK HATA
  BULUNDU VE DÜZELTİLDİ:** ① `deploy.sh`'ın tohum adımı `serve.sh:16`'daki
  `[ ! -s state/trades.jsonl ]` korumasını TAŞIMIYORDU → rsync'lenmiş CANLI state üstüne
  2022→bugün replay koşabilirdi; kapı birebir eklendi ve iki dalın hangisine girildiği basılıyor.
  ② RUNBOOK B.3'ün `sed` deseni (`DEĞİŞTİR-uzun-rastgele-token`) `meridian.service`'teki gerçek
  placeholder'la (`CHANGEME-long-random-ascii-token`) EŞLEŞMİYORDU → `sed` sessizce 0 dönüyor,
  servis **bilinen bir placeholder token'la** canlıya çıkıyordu; desen dosyadan doğrulandı ve
  değişimin gerçekten olduğu artık denetleniyor. ③ `deploy.sh` **redis kurmuyordu**, oysa
  `hotstate.py`/`barsarchive.py` ona bağlı — `redis-server` apt'ye eklendi (localhost-only
  default'a DOKUNULMADI). **ÖLÇÜLMÜŞ İKİ DÜZELTME:** sunucu 2 değil **4 OCPU** (`nproc=4`, ssh ile
  teyit) → havuz KAPATILMIYOR, `MERIDIAN_PARALLEL_PROBES=1` birime eklendi; ve Redis yokken
  arşivci **ölmüyor, sessizce boşa dönüyor** (`barsarchive.py:343/413` okundu) → `is-active`
  yeşilliği bar yazdığını KANITLAMAZ, birim yorumuna ve doğrulama listesine böyle yazıldı.
  Taşıma-sonrası ölçü listesi eklendi (tabanlar bugün ölçüldü): `pencere_id:"R1"` damgası
  **0/204** satır, PBO `olculemedi`, `hotstate_down` yerel taban **15.860/hafta**.

- **2026-07-30 NOUS SİSTEM-DEĞERLENDİRME KATMANI İNDİ (§5.2'nin ilk kalemi; 33 yeni çivi, canlı
  state'e SIFIR yazım, RESTART YOK).** Operatör yönü uygulandı: "bütün mekanizmaları değerlendirip
  güncellenmesi gerekenleri nous bulmalı." Dört katman: **A** `analytics.system_telemetry` — 12
  bölümlük haftalık paket, HEPSİ mevcut üreticilerden (yeni ölçüm icat edilmedi); **B**
  `nous_eval.haftalik_degerlendirme` — paket + statik görev şablonu, `hermes.chain_text` ile
  YERLEŞİK beyin zincirinden (SYSTEM'e dokunulmadı, AST çivili); **C** `sekil="parametre"` öneriler
  `composite_queue`ya `nous_eval` damgasıyla — **AYRI BÜTÇE AÇILMADI**, H4'ün 3/hafta tavanına tabi
  ve taşan öneri GÖRÜNÜR biçimde devrediyor; **D** çekirdek hakkındaki öneri YALNIZ rapor —
  kuyruğa giden TEK fonksiyon `_kuyruga_yaz`, ilk işi şekil denetimi, ihlal denemesi
  `CekirdekIhlali` + `AUTHORITY_CHANGE` alarmı (AST testi ikinci bir `enqueue` çağrısı türerse
  düşer). **ÜÇ ÖLÇÜLMÜŞ TASARIM KARARI:** ① **şekil beynin etiketine GÜVENMEZ** — kodda yeniden
  türetilir ve etiket EZİLİR; ilk canlı koşuda bu FİİLEN oldu (model bir veto-geri-besleme önerisini
  "tasarim" diye etiketledi, kod `cekirdek_hakkinda`ya çevirdi). İlk test koşusu ayrıca `koprule`nin
  DIŞ süzgecinin aynı alana güvendiğini yakaladı: iç çivi ihlali durdurup alarm basmıştı ama
  `n_parametre` sayacı yalan söylüyordu — süzgeç de yeniden türetiyor artık. ② **kalite kapısı**
  kanıt-atıfsız öneriyi düşürür ve atıf DENETLENEBİLİR (eşleşen telemetri jetonu satıra yazılır);
  ilk test koşusunda kapının kendini geçersiz kıldığı bulundu — `genel` (gerçek bir alan adı)
  "sistem GENEL olarak iyi" cümlesini kanıtlı sayıyordu, tek-kelimelik ad eşiği 9 karaktere çıkarıldı.
  ③ **iki ayrı boşluk sayacı**: "üretici hiç çıktı vermedi" (0) ile "üretici kendi içinde ölçemedim
  DEDİ" (3) — yalnız birincisi raporlansa paket "12/12 doldu, her şey ölçülüyor" yanılgısını verirdi,
  oysa ilk koşuda 6 önerinin 5'i o üç boşluktan çıktı. **İLK KOŞU KUM HAVUZUNDA YAPILDI** (telemetri
  CANLI verilerden salt-okuma derlendi, değerlendirme sandbox'a yazdı): beyin `nous`/gemini-3.5-flash,
  6 öneri üretildi, 6'sı da kanıt atıflıydı (0 düştü), 4 tasarım + 2 çekirdek-hakkında, **0 parametre
  → kuyruğa hiçbir satır girmedi** (bütçe 3/3 kullanılmadı). Sıfır parametre bir arıza DEĞİL,
  muhafazakâr sınıflandırmanın beklenen sonucu: mekanizma dilinde "veto"/"guard" geçen bir öneri
  anayasal sayılır ve rapora gider. Tüketiciler (YASA 6): pano "Sistem önerileri" kartı +
  `/api/diagnostics.improvement_proposals` + `python -m meridian.nous_eval --ozet` + önceki
  önerilerin akıbetinin SONRAKİ prompt'a geri beslenmesi (H1'in mekanizma-düzeyi ikizi; akıbet
  kuyruktan CANLI okunur, deftere retro damga YAZILMAZ). Kadans `scheduler.advance_once`ın haftalık
  bloğunda (`sweep_orphan` deseni) — **CANLIYA RESTART'la iner, bu turda restart YAPILMADI.**

- **2026-07-30 DSR/PBO SERT KAPI İNDİ — "MOD-FARKINDALIKLI" TASARIM (karar #3, operatör onaylı;
  38 yeni çivi, canlı state'e SIFIR yazım, RESTART YOK).** Y1'in advisory hâli kapandı. Tasarım
  MÜHÜRLÜ hâliyle uygulandı ve buraya AYNEN kaydedilir — çünkü asıl karar eşikler değil, **eşiğin
  hangi bağlamda kestiği**:
  ⟨**KURAL MATRİSİ — mod × ölçüm × hüküm**⟩
  | | DSR ölçülü, ≤0,95 | DSR ölçülü, >0,95 | DSR ÖLÇÜLEMEDİ | PBO ölçülü ≥%20 | PBO ölçülü <%20 | PBO ÖLÇÜLEMEDİ |
  |---|---|---|---|---|---|---|
  | **kâğıt** (bugün) | ship GEÇER + `dsr_dusuk:true` damgası | GEÇER | GEÇER + `dsr_durum:olculemedi` | **RET** | GEÇER | GEÇER (veto YOK) |
  | **gerçek-para** (MODE=live + I_ACCEPT_RISK) | **RET** | GEÇER | **RET** (fail-closed) | **RET** | GEÇER | **RET** (fail-closed) |
  **GEREKÇELER KODDA YAZILI, ikisi ayrı:** (a) DSR kâğıtta bloklamaz çünkü **kâğıt evrimi ölçüm
  aracıdır** — ana defterin öğrenme hızını istatistiksel bir uyarıyla kısmak, kanıt üretimini kanıt
  olmadan yavaşlatmaktı; bloklamamak SUSMAK değildir, uyarı damga olarak KAYDEDİLİR. (b) PBO kâğıtta
  DA keser çünkü **aday testi değil SÜREÇ testidir**: aşırı-uydurulmuş bir SEÇİM SÜRECİNDEN çıkan
  aday kâğıda bile inmemeli — kâğıt defter o adayın kanıtı olarak birikir ve süreç bozuksa biriken
  şey kanıt değil gürültüdür. (c) Gerçek-parada ikisi de FAIL-CLOSED: **"kanıt yoksa gerçek para
  kapısı kapalı"** — ölçülemeyen bir kontrolü "geçti" saymak, yapılmamış bir testin sonucunu
  uydurmaktır (UYDURMA YASAĞI'nın kapı hâli).
  ⟨**BUGÜNKÜ DEĞERLER — kural CANLI SAYILARLA okundu**⟩ Canlı defter DSR (95 işlem, N=32 deneme):
  **0,000024** → kâğıtta `dsr_dusuk: true` damgası, **gerçek-para bağlamında RET**. Doğrulama
  defterindeki **122 ölçülü DSR'nin 122'si de ≤0,95** (medyan 0,047, maks 0,193) — yani DSR kâğıtta
  SERT olsaydı bu tur **hiçbir aday** ship edemezdi; (a) gerekçesi bir tercih değil, ölçülmüş bir
  zorunluluk. PBO yürürlükteki pencerede **ÖLÇÜLEMEDİ (0/8 aday)** → kâğıtta veto YOK, gerçek-parada
  RET olurdu. **YAN BULGU (ölçüldü, düzeltilmedi):** defterdeki 124 satırın **124'ü de `pencere_id`
  damgasız** — yani canlı yazar süreç R1 rotasyonundan ÖNCEKİ kodu koşuyor. Sonuç: **PBO tabanı
  restart'a kadar boş kalır ve sert PBO kapısı canlıda NO-OP'tur** (bu turun canlı davranışı
  değiştirmediğinin ikinci kanıtı; restart operatörde).
  ⟨**FAZ-6 KİLİT ZİNCİRİ: DÖRT → BEŞ, ve İLK KEZ MAKİNE OKUNUR**⟩ `health.faz6_kilitleri` —
  ① EDGE kanıtı (5/5) ② SONUÇ hükmü (4/4) ③ Faz-5 çıkışı ④ operatör onayı (INTRADAY_ARM; 5.1
  runtime ön şartı burada, operatörde) ⑤ **DSR>0,95 yürürlükteki pencerede ölçülü ve geçer**.
  ROADMAP'in "dört kilit" cümlesi bugüne kadar hiçbir yüzeyde yazılı DEĞİLDİ — yani bir kilidin
  sessizce düşmesi kimseye görünmüyordu. Bugün **3/5 açık** ve kapalı olan ikisi ③ (Faz-5 çıkış
  ölçümünü üreten kod YOK → fail-closed) ile ⑤ (DSR 0,000024). Zincir SAF OKUMA: hiçbir şey
  silahlamaz, diske yazmaz; Faz 4b/6 emir bacağı yazıldığında ön-koşul kontrolü oraya bağlanır.
  ⟨**KAPI SEMANTİĞİ KORUNDU**⟩ `_gate_eval.passes` DEĞİŞMEDİ ve DSR orada hâlâ `passes` satırının
  ALTINDA üretiliyor (çivi: `dsr_kapi` adı `_gate_eval` kaynağında GEÇMEZ) — sertlik yalnız SHIP
  yolunda. Arama döngüsünü sertleştirmek, ölçüm aracını ölçüm yapmadan kısmak olurdu. İki yeni statü:
  `rejected_by_dsr` / `rejected_by_pbo`; `rejected_by_backtest` kovasına KARIŞMAZ ve `_ledger_stats`
  onları bandit DENEMESİ saymaz (süreç hükmü, o değişken hakkında kanıt değildir — guard reddiyle
  aynı yapısal sebep).
  ⟨**SAPMALAR — üçü de yazılı**⟩ ① `dsr_dusuk` mühürde "true/false" yazıyordu, **ÜÇ DEĞERLİ**
  uygulandı: `None` ⟺ `dsr_durum: olculemedi`. Ölçülmemiş bir DSR'ye `False` yazmak "düşük değil"
  demek, yani yapılmamış bir ölçümün sonucunu uydurmak olurdu (UYDURMA YASAĞI). ② Kilit zinciri
  `health.py`ye kondu (mühür "arming/health yolu" diyordu, mevcut adlandırılmış bir kilit kontrolü
  YOKTU): Faz-6'nın fiziksel anahtarı `state/INTRADAY_ARM` o dosyada yaşıyor ve anahtarla kilit
  listesini iki dosyaya dağıtmak, birinin diğerinden habersiz gevşemesine izin verirdi. ③ Panoda
  hazır bir "Faz-6 hazırlık satırı" YOKTU; 5 kilit doğrulama kartına eklendi (mühür "varsa" dediği
  için yeni bir kart açılmadı).
  ⟨**SUİT**⟩ 2354 → **2392 / 0 / 0** (+38: kural matrisi 16 parametrik hücre + ship yolu 11 + Faz-6
  zinciri 6 + damga/sözleşme/tüketici 5). Canlı worker koşarken tek bayt canlı state'e yazılmadı;
  restart YAPILMADI (yasa canlıya operatörün restart'ıyla iner — PARA-v3'ün ③ borcuyla aynı sıra).

- **2026-07-30 HOLDOUT ROTASYONU "R1" İNDİ (operatör onayı: "holdout rotasyonunu da yap"; 35 yeni
  çivi, canlı state'e SIFIR yazım).** Sınav kâğıdı döndü: **OOS 2023-07-01→2025-12-31 ⇒
  2024-01-01→2026-04-30**, IS başlangıcı AYNEN 2022-01-01, yeni **dondurulmuş holdout
  2026-04-30→2026-07-30** (sıfır sorgu). GEREKÇE ÖLÇÜLDÜ VE TASARIM SIRASINDA BÜYÜDÜ: aynı
  parmak izine §7 yazıldığında 290, Rol 1 tasarımında 367, **rotasyon uygulandığında 434 sorgu**
  (limit 20 → **21,7×**) — yani "biraz daha bekleyelim" maliyetsiz değildi. Çifte kazanç: en çok
  kazılmış [2023-07→2023-12] dilimi Search'ten çıktı (**silinmedi — IS'e geçti**, öğrenmeye açık,
  yargılamaya kapalı: `is_score` 0,0083→**0,0616**) + eski holdout'un ~4 ayı [2026-01→04] taze OOS
  oldu. **DÜRÜSTLÜK NOTU KODA GİRDİ:** eski holdout kabule HİÇ girmedi ama insana RAPORLANDI →
  **YARI-TEMİZ** sayılır, "hiç görülmemiş veri" diye SUNULMAZ (`dataset.ARSIV_GEOMETRILER`).
  ⟨**R1 TABANI, SANDBOX, KARNEYE YAZILMADI**⟩ v3 incumbent iki geometride yeniden ölçüldü (250
  sembol, `load_cached` — canlı barlara tek bayt yazılmadı): **R0 0,0853 / n111 / PARA 0,1311**
  ⇒ **R1 0,0749 / n90 / PARA 0,1005**. R0 sayısı PARA-v3 kabul sınavının 0,0853'ünü **BİREBİR**
  yeniden üretti → motor sürekliliği kanıtlı; düşüş bir kırılma değil, **%12 skor / %23 PARA**
  farkı (maks düşüş İKİSİNDE DE 0,0689 — aynı motor, aynı barlar). **AMA BEDEL ÖRNEKLEMDE VE §7'nin
  TEŞHİSİNE TERS: Search n 90→71, dilim 630→585 gün.** §7 "çıta artık ölçek sorunu değil ÖRNEKLEM
  sorunu (n≈81-96'da P tavanı ~0,66)" diyordu; R1 örneklemi **küçültüyor**, yani P tavanı DÜŞER —
  rotasyon temizliği kanıt hızıyla ÖDÜYOR ve bu takas ölçülmüş bir maliyet olarak yazılıdır
  (kanıt-hızı akışları + gölge-varyant birikimi bu boşluğun karşılığı). Fold'lar n-dengeli kesimle
  kendiliğinden yeniden oluştu: 27/27/28 ⇒ **20/19/22**, avg_r deseni de döndü
  (+0,04/−0,15/+0,29 ⇒ +0,36/+0,21/−0,07). Holdout skoru İKİ pencerede de `None` (min_sample altı —
  dürüstçe tanımsız, uydurulmadı). **SÜREKLİLİK DAMGALARI:** yeni parmak izi
  `da8bdc35…`⇒`a5f205ec…`, aşınma sayacı R1'de **sıfırdan** başlar ("aşınma yok" DEĞİL "henüz
  ölçülmedi" — ek marj 0,01⇒**0,0**, yani PARA-v3 sınavında S2'yi vetolayan kol şimdilik boşta);
  R0 kayıtları **SİLİNMEDİ**, `arsiv_R0` işareti aldı (içerik değişmez — retro damga yasağı),
  arşiv 435 sorguyla ayrı satırda durur ve yürürlükteki sayaca **EKLENMEZ**. Tüm yeni kapı/ön-eleme/
  doğrulama kayıtlarına `pencere_id: "R1"` damgası; habersiz kıyas yasağı ledgers sözleşmesine +
  pano doğrulama satırına yazıldı. **BULUNAN VE KAPATILAN İKİ SESSİZ HATA (rotasyonun kendisi
  doğurdu):** ① `oos_erosion.report()` defterin TAMAMINDA maksimum arıyordu → arşivlenmiş 434'ü "en
  çok sorulan pencere" gösterip ek marjı YÜRÜRLÜKTE sanardı, yani pano kapının uyguladığı marjın
  TERSİNİ söylerdi ② `analytics.validation_trio` PBO'yu defterin TAMAMINDAN hesaplıyordu → iki
  ayrı takvim ızgarasını havuzlayıp gürültüyü "aşırı-uydurma yok" diye okurdu; PBO artık YALNIZ
  yürürlükteki pencereden (canlıda 84 satırın 84'ü R0 → PBO dürüstçe "taban dolmadı" diyor,
  eskiden 84 satırdan sayı ÜRETİYORDU). **BEYAN EDİLMİŞ SAPMA:** holdout sonu "yuvarlanır"
  tasarlandı, **DONDURULDU** — `fingerprint` girdilerinde `holdout_end` VAR, yuvarlanan bir son
  parmak izini her gün değiştirir ve aşınma sayacı hiç birikemezdi (④ ile çelişki); yuvarlanma
  isteği `dataset.holdout_report_end()`te yaşar, YALNIZ insana-rapor yolunda, pencerelemeye ve
  parmak izine ASLA girmez. 2D değerlendiricisi artık "R1 UYGULANDI (2026-07-30)" durumunu bilir ve
  arşivlenmiş 434 yeni bir öneri TETİKLEMEZ (yoksa ölü sayaç her tur "döndür" derdi). **RESTART
  YAPILMADI:** canlı uvicorn (2s+ ayakta) R0 sabitlerini bellekte tutuyor → R1 sonraki süreç
  başlangıcında yürürlüğe girer; karne güncellemesi de gece döngüsünün resmî yolundan/operatör
  onayından geçer (rapordaki hazır blok ÖNERİ).

- **2026-07-30 ROL 1 PLAN DÜZELTMESİ (V6/V7 ajanının bulgusuyla):** gölge-v1 yalnız GİRİŞ kararını
  ölçer → çıkış-düğmeli kollar (V3 scale_out, V6 early_kill, V7 e.k.+s.o.) kontrolle karar-özdeş —
  k paydasını kazançsız şişiriyorlardı; ÜÇÜ DE SETTEN ÇIKARILDI (set: V1/V2/V4/V5, k=4; V2
  kalıyor — stop mesafesi RR-filtresi/boyut yoluyla girişe DOKUNUYOR, sandbox'ta ayrışması
  ölçülmüştü). E1/E4 kanıt birikiminin gerçek kanalı: ① haftalık prescreen yeniden-ölçümü
  (Rol 1 rutini; her hafta ~5-10 yeni işlem defterde) ② gölge-v2 YAŞAM-DÖNGÜSÜ motoru — önceliği
  YÜKSELDİ (çıkış hipotezlerinin tek gölge-ölçüm yolu; §5.2'ye kalem eklendi). Ders: kanıt
  akışının ŞEKLİ hipotezin şekliyle eşleşmeli — giriş defteri çıkış sorusunu cevaplayamaz.

- **2026-07-30 PARA-v3 KABUL SINAVI (k_probes=4, sandbox, 123 dk):** hiçbiri geçmedi (gereken
  P=0.95) AMA yasa görevini yaptı — üç anlatı düzeltmesi: ① E1 erken-itlaf yeni yasada GÜÇLENDİ
  (P 0.561→**0.659**, para_delta **+0.0688** = incumbent paranın yarısı; dd vetosu geçti) ②
  **S2'nin maskesi düştü**: eski-yasa cazibesi (fold 3/3, kuyruk) PARA getirmiyormuş — para_delta
  **−0.0692**, P 0.327; rvol bandı işlem kalitesini değil pencere getirisini yönetiyormuş ③
  G3a-P2'nin eski yüksek P'si (0.742) çift-sayım avantajıymış — yeni yasada dürüst 0.632 (para
  +0.053 + kuyruk −2.28R gerçek ama orta). E4 fold 3/3 sürüyor (P 0.612). SONUÇ: çıta artık
  ölçek sorunu değil ÖRNEKLEM sorunu (n≈81-96'da P tavanı ~0.66) — kanıt-hızı akışları tam bu
  boşluk için; E1+E4 gölge-varyant setine ekleniyor (V6/V7) → canlı kâğıt-kanıt birikimi.
  S2 neden-vetosu notu: aşınma marjı artık PARA ölçeğinde işliyor (sahada ilk görüldü).

- **2026-07-30 BÜYÜKLÜK YASASI YENİDEN TASARLANDI — "PARA-v3" İNDİ (operatör onayı: "1 numaradan
  başla"; 20 yeni çivi + 9 bilinçli güncelleme, yasa GEÇİŞİ YAPILDI).** Kapının karar değişkeni
  değişti: `ΔS` artık YALNIZ paradan türer. `ret_c_v3 = kıs(pencere_bileşik_getirisi /
  ((1+%25)^(span/365) − 1))` — **30-güne indirgeme çarpıtması YOK** (pay ham getiri, ölçek yalnız
  paydada; terim getiride DOĞRUSAL). `dd_c` ve `sharpe_c` SKORDAN ÇIKTI. ÖLÇÜLDÜ: PARA'nın varyans
  payı **%0,3 → %100** (yapısal özdeşlik, çivili), σ(ret_c) 0,0151 → **0,0356 (2,36×)**.
  **KÖK NEDEN ÇİFT-SAYIMDI, ölçek değil** (3b'nin bulgusu): düşüş ve Sharpe HEM skorun varyansında
  HEM ayrı sert vetolarda sayılıyordu; v2 rötuşu (ölçek düzeltmesi) PARA payını yalnız %3,2'ye
  taşımıştı ve 3 ağırlık denemesi de tutmamıştı — o ölçüm kaydı SİLİNMEDİ, v3'ün gerekçesi olarak
  `MEASURED_V2`de duruyor. **KORUMA BİTMEDİ, GÜÇLENDİ:** skordan çıkan düşüş bacağı **DÜŞÜŞ
  VETOSU**na taşındı (`DD_VETO_MARGIN = 0,04`, TEK YÖNLÜ — kötüleşme RET eder, iyileşme HİÇBİR puan
  kazandırmaz, yoksa çift-sayım arka kapıdan dönerdi). Marj iki bağımsız türetimle aynı sayıya çıktı:
  ölçülen σ(düşüş) = 0,0343'ün DIŞINDA **ve** %8 düşüş bütçesinin tam yarısı. Sharpe hiçbir yerde
  AYRICA sayılmaz (fold çoğunluğu + kuyruk vetosu + DSR üç ayrı açıdan kapsıyor) — davranışla
  çivili: toplamı koruyup dağılımı daralttığımızda (Sharpe 2× artıyor) karar skoru DEĞİŞMİYOR.
  **MARJ ÇEVRİMİ σ-EŞDEĞERLİĞİYLE:** `GATE_MARGIN` 0,02 bileşik-ölçekliydi ve karar değişkeninin
  kendi gürültüsünde yalnız **0,107 σ**'ydı; para ölçeğinde aynı σ konumu → 0,02 × (σ_v3/σ_eski =
  **0,1908**) = 0,00382 → adlandırılmış sabit **`MONEY_GATE_MARGIN = 0,004`**. İKİNCİ ÇEVRİM BİLİNÇLİ
  REDDEDİLDİ ve gerekçesi kodda yazılı: "0,02'yi salt parayla kazan" okuması 0,0945 verirdi (25×
  daha sert) çünkü eski yasada o para HİÇ TAHSİL EDİLMİYORDU — aday 0,02'yi tek başına düşüşle de
  aşabiliyordu. Aşınma marjı da AYNI çarpanla para ölçeğine çevrildi (yoksa aşınmış bir pencerede
  aday kârı DEĞİL düşüşünü iyileştirerek cezayı geçebilirdi — çıkardığımız bacağın arka kapıdan
  dönüşü). **TERS GÖLGELEME:** `shadowlaw.py` "v2 gölgesi"nden "ESKİ YASA gölgesi"ne dönüştürüldü —
  eski bileşik hüküm her değerlendirmede AYNI replikasyonlarda ölçülüp `*_eski_yasa` alanına yazılır
  (tek `score_detail` çağrısı; gölge artık BEDAVA), kapı kaydına `yasa_surumu: para_v3` + geçiş
  tarihi damgası basılır, pano satırı "GEÇİŞ YAPILDI · eski hüküm: X" gösterir. Geçiş ÖNCESİ 15 kayıt
  `gecis_oncesi` olarak SAYILIR ama v3 hükmü **ters çevrilmez**: v2 doğrusal bir pertürbasyondu
  (tersinir), v3 üç terimden İKİSİNİ atıyor — tek bileşik sayıdan çıkarılamaz, denemek uydurma olurdu
  (`divergence_row`un ters-çevrim makinesi bu yüzden kaldırıldı). **YAKALANAN SESSİZ MİKTAR HATASI:**
  `predicted_delta` artık PARA, `realized_delta` ise hâlâ BİLEŞİK (rollback yolu) — meta-kalibrasyon
  bu ikisini bölüyordu ve σ oranı 0,19 olduğundan oran sistematik ~5× ŞİŞECEK, sahte bir "öngörüler
  fazlasıyla gerçekleşiyor" sinyaliyle kapıyı YANLIŞ yerde gevşetecekti (hiçbir test kırılmadan).
  Ölçek karışımı artık YASAK ve atlanan çift sayısı beyan ediliyor; realized tarafının para
  ölçeğinde ölçülmesi AÇIK ÖLÇÜM BORCU olarak kayıtta (`olcek_borcu`). SÜREKLİLİK: `score_detail`
  bileşiği RAPOR metriği olarak AYNEN yerinde (karne/tarih/`oos_score` serisi kırılmadı) ve kapı
  kaydında para skorlarıyla AYRI satır olarak durur. LEGACY yol (dilimsiz fikstür) para ölçeği
  hesaplayamadığı için eski 0,02 marjıyla kalır ve damgası bunu `eski_bilesik_marj` diye söyler.
  **YASA CANLIYA RESTART'LA İNER** — bu turda restart YAPILMADI (canlı worker koşuyor); kod
  yürürlükte, canlı süreç bir sonraki yeniden başlatmada yeni yasayı alır.

- **2026-07-30 G3b ÇIKIŞ REFORMU İNDİ (29 test; 4 mekanizma default-off, sıfır-etki çivili +
  anti-tautoloji):** ölçüm (k_probes=5, sandbox): **E1 erken-itlaf ham ΔS +0.0406 ve E4
  (E1+bankalama) +0.0275 fold 3/3 — PROGRAMIN İLK POZİTİF ÇIKIŞ ADAYLARI**; ret sebebi büyüklük
  değil olasılıksal çıta (P 0.56 vs gereken 0.96 — yasa-revizyon dosyasına girdi). E2 yapı-stopu
  ÇÜRÜDÜ (−0.178, CVaR +5.3R) AMA iki ölçülmüş karıştırıcıyla: notional tavanı stopu de-riske
  çeviriyor (1R→0.25R) + R:R filtresi gevşeyip n %60 artıyor — "pivot stopu mevcut tavanlarla
  kötü" (saf hüküm değil). **TIME-STOP EĞRİSİ (en net bulgu): kesiş KISALTILMAZ — gün-15 kovası
  popülasyonun %34'ü ve en kârlı kova (+13.2R; uzatma adayı); sızıntı gün 2-5'te (−18.3R, stop/gap).**
  Rejim-çıkış boşluğu kapatıldı (flat-params'ta olmayan knob'un rejim override'ı sessizce
  düşüyordu → REGIME_EXIT_KEYS izin listesi; sevk yetkisi bilinçli kapalı). Pivot defter alanı
  değil icra girdisi olarak taşındı (differential yasası korundu).

- **2026-07-30 HAFTA 3b + HERMES ETKİNLEŞTİRME İNDİ (43 yeni test; yasa geçişi YOK):**
  **① GÖLGE-YASA v2 ÖLÇÜM MODUNDA** (`shadowlaw.py`): mevcut yasa `passes`i AYNEN üretiyor, v2 her
  kapı değerlendirmesinde ÇİFT hesapla kayda geçiyor (`*_shadow_v2`, tek `score_detail` çağrısıyla).
  Harness E raporunu BİREBİR replike etti (v1 PARA %0,3 / düşüş %82,0 / Sharpe %17,7) → taban
  doğrulandı. v2 (yıllıklandırılmış getiri / **%25 yıllık hedef**, adlandırılmış sabit) PARA payını
  %0,3→**%3,2**'ye çıkardı; **hedef ≥%40 TUTMADI, 3 deneme beyanlı** (0.5/0.3/0.2 → %3,2 ·
  0.5/0.2/0.3 → %4,1 · 0.5/0.25/0.25 → %3,8; en az değişiklik seçildi). **KÖK NEDEN ÖLÇÜLDÜ ve ölçek
  DEĞİL:** getiri/hedef ailesinden hangi ölçek seçilse σ(ret_c)≈0,045-0,050'de kalıyor (yıllıklandırma
  kaldırılsa 0,0481; dolar-beklentisi bacağı konsa 0,0455) ama σ(dd_c)=0,4182 ve σ(sharpe_c)=0,2917 —
  fark PAYDALARDAN (maks düşüş %8 ve 2·min_sharpe=2,4 DAR, target_return GENİŞ). %40 için dd/sharpe
  paydaları 4,5× genişlemeliydi (maks düşüş %8→%36, anlamsız). **YAPISAL BULGU:** düşüş ve Sharpe
  bacakları HEM skorun varyansında HEM ayrı sert vetolarda sayılıyor (3A kuyruk + max_drawdown +
  TAIL_MARGIN_R) — ÇİFT uygulanıyorlar; PARA tek uygulanan bacak. **IRAKSAMA TABLOSU** (14 gerçek
  kapı kaydı + S1/S2 σ-beyanlı, ters çevrimle): PARA-nötr senaryoda v2 kapıyı **SERTLEŞTİRİYOR**
  (σ %9,3 şişer) — tek hüküm değişimi H00032 GEÇER→RET. Her satırda **δ\*** = hükmü döndürecek aylık
  getiri iyileşmesi: H00033 (P=0,799, kıl payı) **%0,038/ay**, S2 %1,22/ay, S1 %2,60/ay.
  **② HERMES PAKETİ H1-H5:** H1 tahmin-isabet bandı (canlı: n=1, bant ÖLÇÜLEMEDİ — tek çift v4
  rollback'i ve **YÖNÜ TERS**, oran −0,614) · H2 ölü aile hafızası (`stop_loss_atr_mult` 21 deneme /
  0 ship = hipotezlerin **%51,2**'si; **defterde HİÇ önerilmemiş 14/28 düğme** satırı; §7 YAPMA
  listesi makine-okunur) · H3 bileşik yol (`composite_queue.jsonl`, guard REDDETMİYOR→kuyruğa yazıyor,
  tek-değişken yasası KALKMADI) · H4 gece kancası (haftalık bütçe **3**, ayrı süreçte nohup deseni,
  döngüyü bloklamaz) · H5 skill öz-yönetimi (PROTECTED beşlisi ASLA; **motor-içi skiller yalnız
  RAPORLANIR** çünkü onlara `shadow` yazmak davranışı DEĞİŞTİRMEZ — kozmetik kayıt reddedildi).
  Kanıt paketi ORTADAN kesilmeyi bıraktı: **alan-düzeyi öncelik** (H1/H2 en üstte) + tavan 1400→6200.
  **③ Y3 DÖRTLÜSÜ** default-off indi (bounds 28→32): SPY 200-SMA yeni-giriş kapısı (zorla tasfiye YOK)
  · sektör notional tavanı · ısı tavanı (3a'nın "YALNIZ GÖSTERGE" ısısının kapıya bağlanma YOLU, kapalı)
  · **VIX/VIX3M: KAYNAK DOĞRULANDI ve YOK** — Massive endeks uçları HTTP 403 NOT_AUTHORIZED, FMP quote
  ^VIX/VIX/^VIX3M/VIX3M dördü de BOŞ → knob indi ama `veri_yok` ile DEVRE DIŞI, oran UYDURULMADI.
  **④ K1 DEVİRLERİ:** MAE karnesi (kazananlar p90 **0,713R** vs eşik 0,70 — kıl payı; kaybedenler
  medyan 1,058R = stop çalışıyor, ama maks 2,437R kuyruk gap'i var) · otonomi sayımı ts-tabanlı
  (400 satır → 30 gün = **26.357 olay**, 66×) · hotstate DOWN_REASSERT throttle (**500 kopma → 1 olay**,
  bastırılan sayılıyor + çırpınma alarmı; K1'in 6.834/24s seli kesildi) · notify.new_plan loop'a
  BAĞLANDI (ham metin kaldırıldı) · shadow_variants CONTRACT'a girdi ve **süreli codelaw beyanı
  KALDIRILDI** (pano/api devri tamamlandı). **⑤ 2B/2C/2D:** benchmark_relative blok-bootstrap'a geçti —
  aralık [−0,1694,−0,0517]→[−0,1868,−0,0378] GENİŞLEDİ ama **2. ölçütün hükmü DEĞİŞMEDİ** (ikisi de
  sıfırı dışlıyor; kayma alanı ve IID kıyası kayıtta) · 2C empirik Bayes: **rejim hücrelerinde τ²=0**
  — yayılımın TAMAMI hücre-içi gürültü, üç rejim de genel ortalamaya (−0,0421R) TAM küçültüldü
  ("chop zararlı / trend_up iyi" GERÇEK katmanda desteklenmiyor); bileşen IC'de 21 hücre, **rvol20@5
  0,2336→0,0667** (w≈0,15) yani G2'nin manşet IC'si aile-çapı küçültmede %71 tıraşlanıyor · 2D holdout
  rotasyonu: en çok sorulan pencere **290/20 sorgu = 14,5× limit → ROTASYON ÖNERİLİR** (uygulanmadı,
  operatör kararı; maliyet: fingerprint değişir, geçmiş p/ΔS karşılaştırılamaz).
  **İKİ ÖZ-ARIZA YAKALANDI:** (a) `catalog()` cf katmanını düşürüyordu → H5 sessizce HİÇ çalışmazdı;
  (b) `st = st or {}` boş sözlükte YENİ nesne yaratıyordu → H4 bütçesi diske hiç yazılmıyor, yoklama
  SINIRSIZ oluyordu (10/10 izin aldı). İkisi de v125'te çivilendi.

- **2026-07-30 K1 KOPUKLUK TURU İNDİ (25 BAĞLA + 10 EMEKLİ; suite 2224/0/0):** panoya: kelly
  (full −0.041 → yarım-kelly 0: overbetting yok ama kenar da yok — SONUÇ hükmüyle tutarlı),
  VaR/CVaR, tazelik rozetleri, rejim-tetik doluluğu (trend_up 57/30 READY, chop 35/30 READY —
  kalibrasyon yetki eşikleri DOLU), sprint son-5, işlem detay çekmecesi. Bağlanan: goal.failure_below
  İLK KEZ ölçüldü (16 gün sonra: −0.13% vs −4% eşik, failed=False) · crosscheck diagnostics'te
  (251/1775/0 uyumsuz) · selfreview haftası 7→66 vaka · verify_hermes SUNUCUYU ölçüyor (autostart
  gerçekten AÇIK) · monitoring filtresi 3/12→türetilmiş · sweep_orphan haftalık takvimde. İki
  öz-bulgu: yorum-satırı okuyucu değildir (AST'li korpus) + test üretim tüketicisi değildir.
  **YENİ GÖRÜNÜR 3 GERÇEK ARIZA:** universe_coverage 164 atlanmış seans (son: 07-28 %18 kapsam —
  FMP kota günü) · event_ledger %91 hotstate_down seli · hotstate 6.834 kopma/24s (reboot sonrası
  çırpınma şüphesi — restart sonrası yeniden ölçülecek). Devirler 3b'ye: mae_r→exit_efficiency,
  otonomi ts-sayımı, notify.new_plan loop kancası, hotstate throttle.

- **2026-07-30 SADELEŞTİRME+KANIT-HIZI TURU İNDİ (38 test; kendi kırmızısı 0):** ① 4a gözlemi
  TÜM planlara — izlenen ticker 0→10 (aç yığın beslenmeye başladı; eod_armed anlamı aynen, 4b
  gölgesi bilinçli yalnız-silahlı). ② `shadow_variants.py` — 5 varyantlı kâğıt-karar defteri
  (kanun çağrılır kopyalanmaz; near_miss üst-kümesiyle nüfus tamlığı; k_variants beyanı; ship yolu
  YOK); sandbox gerçek-döngü doğrulaması İLK AYRIŞMAYI gösterdi (V2 geniş-stop PM adayını
  geometrik kaybediyor). v1 sınırı beyanlı: karar ölçülür, portföy ömrü değil. ③ `prescreen
  --composite` resmî bileşik yolu. ④ barsarchive NOGROUP onarımı + `ops/barsarchive-run.sh`;
  RUNNER BAŞLATILDI (Rol 1, 2026-07-30 ~02:45) — ring 3 günü tutuyormuş: İLK TURDA 15.622 satır /
  33 sembol / 27-29 Tem KURTARILDI, Faz-5 birikimi resmen başladı. ⑤ mrd:price/pos yalnız-yazılır
  EOD kopyaları kapatıldı (geri açma tek satır), mrd:ord ölü beyanı temizlendi. Suite'teki 2 kırmızı
  K1'in /api/hermes emekliliğinden (K1 kapatacak — denetimde doğrulanacak).

- **2026-07-30 ROL 1 DÜZELTMESİ (Hafta 3a E-raporu sonrası — önceki günlük anlatımına):**
  (1) "Bileşik skor kuyruk-kazananları reddediyor" anlatımı YANLIŞ popülasyondaki gösterge
  sayıya (Δoos_score) dayanıyordu — kapının gerçek karar değişkeni P(ΔS>0)/SEARCH-blok
  yeniden-örneklemesi ve S2 o değişkende ortalama **+0,062 DAHA İYİYDİ**; ret sebebi terim değil
  ULAŞILAMAZ ÇITA (K=2'de gereken ΔS≈0,24 = incumbent skorunun 1,85 katı; σ'nın %82'si düşüş
  gürültüsü). S1 istisna: liyakatle reddedildi (ΔS −0,169 + kuyruk kötü). (2) Önceki G3a/S2
  "CVaR −2,2…−3,5R" rakamları DELTA'dır (iyileşme), absolut değil. (3) DSR canlı defterde
  **1e−06** (N=321 deneme, Sharpe negatif) — "beceri kanıtı yok" artık deflasyonlu sayıyla
  resmî. BÜYÜKLÜK YASASI REVİZYONU 3b'de GÖLGE-YASA olarak ölçülecek (çift hesap + ıraksama
  tablosu; canlı geçiş sabah operatör görünürlüğüyle).

- **2026-07-30 SKILL TEMİZLİĞİ İNDİ (suite 2122/0/0):** 37/68 klasör `skills/_emekli/`ye
  (22 emekli + 15 birleştirilen; silme yok, README'li geri-getirme yolu); registry 36 kayıtta
  retired damgası + 17 bayat last_run temizliği + 8 aktivasyon koşulu; skills.py zincirlerinde
  declared-only 26→14 (P1 12→7, P3 3→1, P5 9→4); PROTECTED beşlisi + hermes preload'ları dokunulmadı.
  Canlı-worker yarışı yakalandı ve kalıcı çözüldü (anahtar-kapısı arşivli kaydı yeniden
  enable ediyordu — 8 kayıtta kapı adaylığı kaldırıldı, özgün değer retired_requires'ta).
  breakout-planner sezgileri docs/G3B-CIKIS-REFORMU-NOTLARI.md'ye (G3b turunun girdisi).
  Yüzey-dışı bayat metinler (landing "66 skill" vb.) için görev fişi açık.

- **2026-07-30 G1 PİLOTU v2 SONUÇLANDI (Massive zinciri, FMP'ye sıfır dokunuş; 394 mid-cap vs
  250 büyük-cap, AYNI 2-yıl pencere, haftalık örnekleme; n=38.8k vs 24.7k):** McLean-Pontiff
  beklentisi ("mid-cap'te IC daha yüksek") BU PENCEREDE DOĞRULANMADI — rvol20 büyük-cap'te ~2×
  GÜÇLÜ (0.053✓ vs 0.024✓ @5bar); mom12_1 iki evrende benzer (0.045-0.049✓ @20); rvol bant deseni
  mid-cap'te de replike (1.5-2.0 tatlı nokta +2.03%). HÜKÜM: evren genişlemesi sinyal-kalitesi
  vaat etmiyor — kalan değeri yalnız FREKANS/çeşitlendirme; önceliği near-miss bulgusundaki
  hacim-eşiği takasına (mevcut evren İÇİNDE ~3.4× havuz) devretti. G1 genişleme kararı: giriş
  kapıları yeniden ayarlanana dek BEKLET (kaydedilmiş efor). Kısıtlar: 2-yıllık tek rejim
  penceresi + koşulsuz örnekleme — kırılım-koşullu popülasyonda tablo farklı olabilir.

- **2026-07-30 HAFTA 3a İNDİ — dolar merceği + kuyruk + ısı + doğrulama üçlüsü; suite 2122/0/0 (bu turun 61 testi dahil).**
  **1B SONUÇ HÜKMÜ** (`analytics.result_verdict`, EDGE'in ikizi, panoda yanındaki kart): canlı
  hüküm **"SONUÇ: 0/4 sağlandı (4 sağlanmadı) — para kanıtlanmadı"** — işlem başına $−58,34
  (blok-bootstrap %95 CI **[−137,75, +14,53]**, sıfırı İÇERİYOR), PF 0,567, maks düşüş %8,04,
  net −$5.542 vs ödenen friksiyon $581. Friksiyon İKİ KEZ kesilmez (`pnl_dollars` zaten net;
  `costs` yalnız 4. ölçütün kıyas tabanı). **3A KUYRUK** kuzey yıldızının 5. ölçütü oldu → hüküm
  artık **"1/5 sağlandı (1 zayıf, 2 sağlanmadı, 1 ölçülemedi)"**; kuyruk SAGLANMADI çünkü CVaR%5
  −1,16R (taban −1,5R) GEÇİYOR ama düşüş %8,04 > %8. **İKİ GERÇEKLİK DÜZELTMESİ:** (a) maks düşüş
  kapanmış-işlem eğrisinde %5,70, GÜNLÜK M2M eğrisinde %8,04 — kapanmış eğri tek başına okunsaydı
  iki hüküm de eşiği "geçmiş" görünürdü (denetim #6); (b) IID bootstrap CI'ı [−116,86, −0,00] ile
  sıfırı kıl payı dışlıyor, blok bootstrap içeriyor — IID okuma "kaybettiğimiz kanıtlandı" derdi.
  **3B ISI** `portfolio_heat` (anlık 0,0% — açık pozisyon yok) YALNIZ GÖSTERGE, hiçbir kapıya bağlı
  değil (test bunu guard/broker/reflect/loop/arming taramasıyla çiviliyor). **Y1** DSR/PSR +
  PBO/CSCV + `validation_ledger.jsonl` (D1) — hepsi ADVISORY, passes semantiği DEĞİŞMEDİ; canlı
  defterde **DSR 1e−06** (N=321 = 289 aşınma sorgusu + 32 k_probes; PSR(0)=0,027), PBO 0/8 adayla
  OLCULEMEDI. **E RAPORU — ÖLÇÜNÜN ÖLÇÜMÜ, KAPININ GERÇEK KARAR DEĞİŞKENİ BULUNDU:** olasılıksal
  yasada `oos_score` karşılaştırması karar VERMEZ (o tam-OOS bir GÖSTERGE sayısıdır); karar
  `P(ΔS>0) ≥ 1 − 0,20/K`dır ve ΔS, bileşik skorun SEARCH dilimi blok-yeniden-örneklemesidir.
  Canlı defterde ölçüldü: ΔS varyansının **%82'si düşüş terimi, %17,7'si Sharpe, %0,3'ü PARA
  terimi** — yani büyüklük kapısı fiilen bir düşüş+düzgünlük kapısıdır. σ(ΔS)≈0,19 ⇒ P=0,90 için
  gereken ortalama ΔS ≈ **0,24**, incumbent'ın TÜM skoru 0,1309 iken. S2 (fold 3/3, kuyruk −2,26R
  daha iyi, n 98→106) P=0,629 ile reddedildi — K=1'de bile (0,80) geçmezdi. Ayrıştırma
  `segment_score` docstring'ine düz yazıyla girdi; her resmî kapı değerlendirmesi artık
  `oos_components`i deftere yazıyor (bu borç kapandı).

- **2026-07-30 NEAR-MISS ÖLÇÜMÜ (ilk kez; n=4.988 vs girilen 2.102):** kılpayı elenenlerin ileri
  getirisi girilenlere ÇOK yakın — @10bar fark YOK (+0.453% vs +0.430%), @20bar mütevazı fark
  (+0.90% vs +1.31%, CI'lar sınırda örtüşür) → giriş eşiklerinin marj değeri zayıf; filtreler
  masada büyük havuz bırakıyor. KIRILIM: engelleyicilerin %85'i **hacim eşiği** (4.243 aday;
  rs 1.217, skor 690, uzamış 675). Bileşik skor IC'si HER İKİ nüfusta da ≈0/negatif (near-miss
  @10 anlamlı -0.034) — skorun sıralama körlüğü üçüncü bağımsız popülasyonda teyit. ADAY DOĞDU
  (prescreen kuyruğuna, dolar merceği indikten sonra): "hacim-eşiği gevşet + rvol-bant filtresi
  koy" bileşiği — replike olmayan volume_ratio kapısını, doğrulanmış rvol bandıyla TAKAS eder;
  frekansı ~2-3× büyütme potansiyeli, kalite bekçisi bantta.

- **2026-07-30 MASSIVE ENTEGRASYONU İNDİ — YAZIM modunda, suite 1980/0/0 (TEMİZ SAYIM).**
  Zincir: massive(grouped) → massive_hist(≤2y) → FMP → cboe → nasdaq; derin tarih Massive'e hiç
  sorulmaz. Günlük bar yenilemesi **250 çağrı → 1** (eski maliyetin kanıtı: 07-27'de calls_today=251
  "Limit Reach"). Canlı doğrulama GERÇEK anahtarla: 320 örtüşen bar / maks sapma 1.3e-05; canlı
  çapraz-kontrol defteri 251 sembol / 450 kıyas / 0 uyumsuzluk. İKİ GERÇEKLİK DÜZELTMESİ: MCP
  ölçümümdeki "0.000%" küçük-örneklem yuvarlamasıydı (gerçek ölçek ~1e-5) ve kıyas tabanı FMP
  değilmiş — bars_source: cboe 192 / nasdaq 59 / **FMP 0** (önbelleği son dönemde yedek zincir
  besliyormuş). Tur 6 GERÇEK HATA da düzeltti: tarih-yok-eden corporate-action reset yolu (tek
  artımlı bar 250 barlık önbelleği 1 satıra indirebiliyordu), tasarrufu sıfırlayan aynı-gün tarih
  hatası, kesinti çoğaltıcısı (memoizasyonsuz 250×4 retry), 30-günlük sessiz bayatlık kapanı,
  gürültü tabanına oturan alarm eşiği (0.1%→0.5%), seam-defteri kirletme riski. Kalan tek iş:
  api.py Test-düğmesi kablolaması (3 satır — ajana verildi).

- **2026-07-30 Y4 veri katmanı indi** (63 test yeşil, kendi kırmızısı 0): `adapters/insider.py` —
  Form 4 akışı sembol-BAĞIMSIZ `latest` sayfalarından (~3-8 çağrı/gün; sembol-başına yol 250
  olurdu), yalnız P/S kodları nete girer (KO'daki icra-et-ve-sat vakası naif okumada "75k ALIM"
  görünürdü — engellendi), sınıflama 3-yıl penceresi dolana dek DÜRÜST `siniflanamadi` ("bu dosya
  sinyal değil kapsam ölçümü" notu dosyada); BULGU: `insider-trading/search` ücretsiz planda 402
  (plan sınırı) → geçmiş derinleştirme yalnız günlük birikimle. `adapters/shortinterest.py` —
  FINRA anahtarsız (FMP kotasına sıfır etki), 250/250 eşleşme, kendi DTC'si ile FINRA DTC'si AYRI
  raporlanır, float kaynağı yokken si_yuzde_float=None. Suite'te kalan 21 kırmızının tamamı
  kanıtla Massive turunun yarım dosyalarına ayrıştırıldı.

- **2026-07-30 SKILL DENETİMİ (68/68, 10-ajanlı workflow; tam tablo tasks/w4fkdamk2.output):**
  Dağılım: **22 olduğu-gibi** (koruma katmanı PROTECTED beşlisi + hermes preload çekirdeği fiilen
  çalışıyor: backtest-expert 114 proposal çağrısında bağlamda, data-quality-checker 14/14 koşuda
  gerçek-invoked) · **22 EMEKLİ** (programa hizmet etmeyen aileler: temettü/kanchi üçlüsü, COT,
  opsiyon, pair-trade, teknik-görsel, skill-oto-üretim — hiçbirinin §5 kalemi ve kullanım izi yok)
  · **16 BİRLEŞTİR** (işlevi motor soğurmuş ya da ikizi var: breakout-planner→strategy.py yolu,
  breadth ikilisi→Y3, edge-* zinciri→orchestrator) · **8 ÖLÇÜMLE-AKTİVE** (programa eşlendi:
  theme-detector→G5 · uptrend-analyzer+ibd-distribution-day→Y3 · parabolic-short→G6 ·
  edge-orchestrator→G4/Y1-sonrası · canslim→FMP anahtarı+helper şartlı · economic-calendar→Y3 ·
  strategy-pivot-designer→Aşama 6). Yapısal bulgular: registry'nin eski "invoked" kayıtları
  2026-07-15 dürüstlük düzeltmesi ÖNCESİ yalanın kalıntısı; kayıt-zincir çelişkileri (P5_LEARN
  beyanlı ama zincirde adı olmayan skill'ler) belgelendi. AKSİYON: "skill temizlik mini-turu"
  §5.2'ye eklendi (emekli 22 → disabled+arşiv klasörü, birleştirmeler, registry dürüstlüğü).

- **2026-07-29 gece — S1/S2 bileşik skor kapı sınavı: İKİSİ DE GEÇMEZ.** S1 "yeni çekirdek"
  (rvol-bant ağırlıklı): Δ**-0.081**, fold 2/3, kuyruk KÖTÜ, P=0.19 → bileşen-IC kanıtı sistem
  düzeyine TAŞINMADI (çıkış darboğazı + w_mom popülasyon kayması; rvol sinyal olarak gerçek ama
  skor ağırlığı olarak değil). S2 "eski + min_rvol 1.5": Δ-0.046 AMA **fold 3/3 kazanıyor + CVaR
  -2.26R + n 98→106** ve bileşik skor yine düşük → G3a'dan sonra ÜÇÜNCÜ vaka: fold/kuyruk kazanan
  adayı büyüklük yasası reddediyor. HÜKÜM: hiçbir şey ship edilmez (kapı hakem); Hafta 3'ün dolar
  merceği (SONUÇ HÜKMÜ) artık kritik yol — S2 + G3a paketleri o mercekle YENİDEN değerlendirilecek;
  ayrıca "bileşik oos_score neyi ödüllendiriyor" ayrıştırması (ölçünün ölçümü) Hafta 3'e eklendi.

- **2026-07-29 KOTA TAHSİS POLİTİKASI (operatör):** bar verisi → Massive (grouped-daily günde 1
  çağrı; sembol-başına yakın-dönem yedek: massive→fmp→cboe/nasdaq; derin tarih 2021+ FMP'de kalır);
  **FMP kotası BİLGİ KATMANINA ayrılır** (temel/float, insider, kazanç takvimi, haber, transkript,
  13F — skill'lerin motoru). Gerekçe: aynı gün FMP birincil anahtar kotası G1 çekimiyle doldu
  (yedek anahtara rotasyon çalıştı — ilk saha testi). Ayarlama-tutarlılığı MCP ile ÖLÇÜLDÜ:
  37 kıyas / 2 tarih (temettü ex-pencereli) → 0.000% fark → Massive YAZIM modunda bağlanır.

- **2026-07-29 C2 bar arşivi indi** (barsarchive.py, 33/33): kendi "archive" consumer-group'u,
  fsync-sonra-XACK crash-safety, (ticker,t) idempotens; barfeed'e dokunması AST testleriyle yapısal
  olarak imkânsız. **Rol 1 kararı — örtüşme:** mevcut `bararchive.py` (hotstate içinden tek-deneme
  yazan, hatayı yutan eski yol) EMEKLİYE ayrılacak; `barsarchive` kanonik Faz-5 arşivi (dayanıklı).
  Emeklilik + `intraday_bars/`→`bars_intraday/` tekilleştirme sonraki mini-tura. Tur sırasında bir
  test kazası canlıya 16MB sızdırdı — geri taşındı (scratchpad'de), teste bekçi eklendi; canlı
  Redis'te atıl `archive` grupları kaldı (zararsız; runner başlarken karar: kabul ya da destroy).
  Yan bulgu: conftest bekçisinde yapısal delik (ham open() + alt dizin körlüğü) — görev çipi açıldı.

- **2026-07-29 G2 implementasyon turu (Rol 2, SIFIR ETKİLİ):** rvol20/mom_12_1/residual_momentum +
  bant-üçgen (1.75±0.75) ve yüzdelik-rütbe skor şekilleri üretime indi; üç bileşen plan/aday
  satırında ALAN oldu (`notes` metnine gömülmedi); `entry.w_rvolband`/`entry.w_mom`/`entry.min_rvol`
  bounds'a **varsayılan 0** ile eklendi (strategy.yaml'a dokunulmadı — canlı skor 20-sembollük çivi
  testiyle G2 öncesiyle BİREBİR); component_ic 4→7 bileşen ve kum havuzu koşusunda **rvol20 gerçek
  katmanda @5 +0.234✓ @10 +0.219✓** — gerçek defterin İLK anlamlı bileşeni. S1/S2 ölçümü sırada.
- **2026-07-29 G3b ön-kanıt (kapanış-konumu/pivot/gap, cf n≈2100):** kapanış-KONUMU sürekli sinyal
  olarak SIFIR (IC ≈ 0 her iki katman — Zarattini kuralının aralık-konumu biçimi bize taşınmadı);
  **pivot-ALTI kapanış kısa ufukta gerçek negatif işaret** (@5bar -0.74% vs pivot-üstü +0.32%,
  n=302; @20'de kısmen toparlar) → erken-itlaf yalnız "pivot-altı kapanış" biçiminde savunulabilir,
  PnL etkisi G3b replay'inde ölçülecek; **BONUS: gap'li kırılım kalite işareti** (@20bar +2.30%
  vs gapsiz +0.73%, n=841) → G5 önceliklendirme + meta-labeling ortogonal özellik adayı.

- **2026-07-29 G3a bileşik çıkış ölçümü:** P1(stop3.0+bank1.5R+BE0) Δ-0.036 · P2(stop3.0+BE0)
  Δ-0.030 · P3(stop2.5+bank2R) Δ-0.043 — üçü de fold 1/3, P≈0.63-0.68 GEÇMEZ; kuyruk hepsinde
  büyük iyileşme (CVaR -2.2…-3.5R). Ders: R-birim önyargısı + dolar merceği ihtiyacı (§6).
- **2026-07-29 G2 ölçümü (1.4 sonrası ilk adım):** rvol20 projenin İLK çift-katman-anlamlı bileşeni
  (gerçek @5 IC .234✓ @10 .219✓; cf @10 .047✓ @20 .062✓); bant doğrulandı (cf @20: 0.8-1.5→-0.5%,
  1.5-2.0→+1.84% n=955, 2.0+→+1.44%); mom12_1@20 cf +0.055✓; rmom zayıf ns; stm21 çürüdü.
- **2026-07-29 1.4 KARAR KAPISI (operatör):** ağırlık ayarı değil G2 YENİDEN İNŞASI. Gerekçe:
  gerçek 0/12 anlamlı; cf'te rs@10 −0.047 ve prox 3 ufukta anlamlı NEGATİF (ağırlıklarıyla ters),
  eski vol replike olmadı; tek anlamlı pozitif tight@20 +0.049.
- **2026-07-29 kimlik mini turu:** suite 35 kırmızı + 1 error → **1805/0/0**. Kök: auth.AUTH_FILE
  import-anı config.STATE bağlaması (geç bağlamayla 21/26 kapandı) + _FAILS sıra sızıntısı.
  Kimlik uçları api.KIMLIK_UCLARI tek kaynağında; ?token= kaldırımı çivili; auth.py hijyen
  istisnası gerekçeli; hermes iplik önle+yakala muhafızı. İkiz checkout YOKMUŞ — symlink + 124
  bayat bytecode (temizlendi, çivili).
- **2026-07-29 Hafta 2 turu:** EDGE hükmüne ANLAMLILIK katı (ZAYIF durumu; canlı 2/4→**1/4**) ·
  bileşen IC cf katmanı + Fisher CI · eşik eğrisi (80'de +0.066R ama CI canlı eşikle örtüşür —
  fark gösterilemedi) · KÂR ŞELALESİ (MFE +0.96R → çıkış −0.99R → friksiyon −0.02R → net −0.04R;
  sızıntı ÇIKIŞTA; çıkış verimi: stop −%76, stop_gap −%209, time_stop +%50, target +%82) ·
  maruziyet-düzeltilmiş SPY (ham −0.908 → **−0.110** CI[−.164,−.054], maruziyet 0.064) ·
  **rollback like-for-like: v4→v3 kararı ÇÜRÜDÜ** (simetrik Δ−0.075 > eşik −0.10; eski elma-armut
  −0.133 abartmıştı; Rol 1 hükmü: v3 yerinde kalır — v3 would-have +0.066 > v4 canlı −0.009;
  motor sapması +0.018 kayıtlı) · prescreen.py kalıcılaştı.
- **2026-07-29 H1b yeniden ölçümü (n-dengeli fold):** Δ+0.006 aynı, fold 3/3→2/3, P=0.446 GEÇMEZ —
  Aşama 0 kesin kapandı (4/4 elendi).
- **2026-07-28/29 derin araştırma sentezleri:** Aşama 7 (frekans+edge; 4 kol) ve Aşama 8 (yeni
  bileşenler; 4 kol) plana işlendi; kaynak listeleri oturum kayıtları + tasks/wpiusyxrm,wrj7g2q0t.
- **2026-07-28 Kuzey Yıldızı turu (Hafta 1):** IC katmanlaması (gerçek/cf/havuz) · bileşen IC ilk
  tablo · n-dengeli fold (fold_uncontested koruması + "taban tutan en çok fold" seçimi) · OOS
  aşınma defteri (sayaç o günden; >20 sorguda +0.01 marj) · EDGE VERDICT bileşimi (A3 ✅; ölçüt-1
  yalnız GERÇEK katmandan — 07-27 havuz kararı geri alındı) · cf sadakat kusuru makine-okunur
  beyanla kayıt altına alındı. Canlı-state sızıntısı yakalandı ve temizlendi (test-doğumlu
  oos_erosion.json — kök neden record_erosion bayrağı).
- **2026-07-28 Aşama 0 ön-eleme (takvim fold):** taban v3 OOS 0.1309 n=98; H1a Δ−0.046 ÇÜRÜDÜ ·
  H1b Δ+0.006 3/3 marj-altı · H2 Δ−0.095 ÇÜRÜDÜ · H3 Δ−0.030 ama CVaR −2.9R (kuyruk bulgusu
  G3'ün gerekçesi oldu). Zarar otopsisi: kâr time_stop'tan (+$3.9k, %70), stoplar −$11.8k,
  MFE ort +0.71R — "çıkış mimarisi kanatıyor" teşhisi.
- **2026-07-28 auth/login katmanı** (ayrı oturum): scrypt parola + imzalı HttpOnly çerez oturumu +
  x-meridian-token CLI yolu (MERIDIAN_DASH_TOKEN, .env 0600, serve.sh source eder) + kaba kuvvet
  sınırı. CLI tam yetki token yoluyla doğrulandı.
- **2026-07-28 rollback v4→v3 gerçekleşti** (o günkü asimetrik yasayla; 07-29'da yasa simetrikleşti
  ve karar çürütüldü — üstteki Hafta 2 satırı) · learning_loop_open temizlendi.
- **2026-07-27:** Faz 4b gölge modu kodda · hermes prompt yeniden inşası (statik SYSTEM + kanıt-bağ
  zorunluluğu; −%63 boyut) · broker-ret ack mekanizması · Piyasa sekmesi + SEANS İÇİ kolonu ·
  ilk yansıma yeni prompt'la: hipotez guard'dan geçti, backtest'te elendi (n=1 olumlu sinyal).
- **2026-07-26:** ilmek-1 (EDGE kartı, IC serisi, öğrenme çarkı, canlı akış kartı) · v3 ebeveyn
  taban ölçümü (OOS 0.1245) · keepalive/grup-kill sağlamlaştırması · 31 maddelik review revizyonu ·
  numpy sanitizer (54/54 rota) · review-backlog 5 madde · beyin unparseable kök nedeni düzeltildi.
- **Numaralandırma notu (2026-07-26):** intraday "Faz" sayımı kanoniktir (§5.5); Faz 5/6 tanımları
  yeniden kurulmuştur (kayıp tarihin kurtarılması değil).

## §8 ARŞİV — tamamlanan WP'ler + oturum snapshot'ları (tarihçe-koru; silme yok) _(eski: §6)_

_**[2026-08-31 DURUM DENETİMİ — BU BÖLÜM KALEM TAŞIMAZ.]** Burası arşivdir: tanımı gereği kapanmış iş ve tarihçe. Rozetli olanlar zaten `kapalı`, rozetsizler ise kapanışın GEREKÇESİNİ taşıyan düzyazıdır. Bu yüzden maddeleri durum işareti taşımaz ve `/api/roadmap` onları `belirsiz` sayar — **bu doğrudur**: "işaretsiz" burada "denetlenmemiş" değil, "durumu olan bir kalem değil" demektir. Denetim 75 kalemi kalemi bu gerekçeyle rozetsiz bıraktı; kaynak: `docs/DENETIM-ROADMAP-2026-08-30.md`._

Buradaki WP'ler tam metin korunur (tarihçe). Bir WP'nin içinde geçen açık operatör/kart/ölçüm kalemi
KANONİK olarak §5/§6'te yaşar; buradaki metin o kalemin tarihçesi + gerekçesidir (çürütülen av
adayları, kill-eşikleri, PIT şerhleri kaybolmasın diye). Bitmiş dalgalar: KOVA-B (16/16, 2026-08-02),
WP-N kanıt-hızı programı (N1-N6; N1 kanal §5 · N4→EXE-2026-004 §6 · N2b→EDG-2026-019 §6), dalga-3.

### §4 ÖNERİ HAVUZUNDAN ARŞİVE — kapanmış kalemler (2026-08-13 yeniden yapılanma; tam metin korunur, SİLME YOK)

_(Denetim `docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md` §B: bu kalemler kapanmıştı ama §4'nin AÇIK
havuzunda duruyordu — okuyucuyu "hâlâ yapılacak iş" sanısına düşürüyorlardı. Her biri "✅ KAPANDI
(tarih, gerekçe)" satırıyla buraya alındı; gövde metinleri **AYNEN**, eski §4 numaraları ÇAPA olarak
korunur.)_

#### Ö-1 · dagit rsync exclude genişletme — ✅ KAPANDI (2026-08-10, `dagit.sh:18`; §4'den kapanan ilk madde)
1. ~~**dagit rsync exclude genişletme**~~ → **✅ YAPILDI (2026-08-10, dagit.sh:18):** üç kapsamlı desen
   eklendi (`research/olcumler/*/seanslar.json` · `*/run.stderr.log` · `*/state`), tarihli gerekçe yorumda;
   v204 testi ekleme-toleranslı (yalnız 'backups' varlığını sabitler). Özet `sonuc.json`+`olcum*.py` taşınmaya
   devam eder. *(Öneri-akış yaşam döngüsü: §4'den kapanan ilk madde.)*

#### Ö-5 · `.locks/` budaması — ✅ KAPANDI (v234, 2026-08-12; store.kilit_budamasi + conftest sessionfinish)
5. ~~**`.locks/` budaması**~~ → **✅ KAPANDI (v234, 2026-08-12):** store.kilit_budamasi + conftest
   sessionfinish (24sa+flock+inode-güvenli; ilk koşu 29 kilit temizledi). *(orijinal madde: 2026-08-10)* — test koşuları
   oturum-düzeyi tmp yolları hash'lenmiş kilit dosyaları bırakıyor (tur ölçtü: tek AST koşusu bile +2;
   25→27 birikiyor, budama yok). DİKKAT: flock semantiği — canlı tutulan kilidi silmek dışlamayı kırar;
   güvenli budama = non-blocking flock alınabilen + eski dosyalar (ops betiği ya da conftest teardown).
   *gerekçe: sınırsız birikinti · boyut: S (flock-dikkatli) · bağımlılık: yok · öncelik: düşük.*

#### Ö-6 · Bayat-defter-kalıntısı tuzağı — ✅ KAPANDI (v234, 2026-08-12; db_backed göç-süzgeci)
6. ~~**Bayat-defter-kalıntısı tuzağı**~~ → **✅ KAPANDI (v234, 2026-08-12):** db_backed göç-süzgeci
   (idempotent, adli-olaylı, damgasız-dosya-taşınmaz); canlı trades.jsonl kalıntısı bir sonraki restart'ta
   kendiliğinden .migrated olur. *(orijinal madde: 2026-08-11)* — trades defteri 07-31'de
   DB'ye göç etti ama `state/trades.jsonl` DOSYASI 95 satırda donuk kalıntı olarak duruyor (portfolio/
   shadow_books `.migrated`a çevrilmiş, trades ÇEVRİLMEMİŞ) → insan+araç yanlış okuyor (Rol-1'i "pozisyon
   izsiz kayboldu" yanılgısına düşürdü; gerçek: T00097 VLO target +728$ DB'de düzgün). Düzeltme: migrate
   edilen TÜM defter dosyalarına .migrated disiplini + store'a "bu ad DB'de, dosyayı okuma" koruması.
   *gerekçe: adli/ölçüm güvenilirliği · boyut: S · bağımlılık: yok · öncelik: yüksek.*

#### Ö-11 · KARAR PENCERESİ PAKETİ — ✅ TAMAMLANDI (2026-08-12; denetim B1)
**Kapanma gerekçesi:** pencere kuruldu (`docs/KARAR-PAKETI-2026-08-12.md`), beş kart da hükümlendi
(023/024/025/026/027), final-paket doğrulandı (EDG-2026-032, 3/3 kapı) ve DAĞITILDI:
`state/strategy.yaml:1` `version: 5` · `:12` `position_size_r: 0.5` · `state/goal.yaml:131`
`max_open_positions: 20` · `:140` `heat_hard_r: 5.0`. İki artığı §3'de yaşıyor: (i) aşağıdaki A12
düzeltmesi, (ii) "SIRA: … hemen OPT Faz-1" → **WP3-B**.
> **⚠ DÜZELTME (denetim A12, 2026-08-13):** aşağıdaki metinde geçen **"SLOT 20 + 0.5R: OPERATÖR
> ÖN-KARARI (2026-08-12: 'ISI 10R kalsın')"** satırı **ölçümle AŞILDI** ve yürürlükte DEĞİLDİR.
> `EDG-2026-028…yaml:61-65`: "ÖNERİLMEZ … OPERATÖR ÖN-KARARI ('ISI 10R kalsın') **ölçümle
> ÇELİŞİYOR** … Rol-1 önerisi **5R'DE KAL**". Canlı: `state/goal.yaml:140` `heat_hard_r: 5.0`;
> `:126` "ZARF DEĞİŞMEDİ: heat_hard_r 5,0R KALDI (EDG-2026-028 zarf-10'u ölçtü ve ELEDİ)".
> **Yürürlükteki değer 5R'dir.**
11. **KARAR PENCERESİ PAKETİ — 023/024/025/026/027 + Rol-1 önerileri (2026-08-12; ölçümler inince
    tek pencere kurulur)** — Rol-1'in pencereye getireceği öneriler ŞİMDİDEN kayıtlı (sayılar hükümden önce
    gelir; CI'lar öneriyi çürütürse öneri düşer):
    · RAMPA 15/36 (kâğıt): BENİMSE — kill#3 (dd ×2.29) otomatik-hükmü engelledi, karar operatörün; %17.8 dd
      kâğıtta öğrenme bedeli ↔ 3× işlem + eksiden artıya P&L + düzelen işlem-R (−0.078→+0.032). ~~Gerçek-para 3/8 SABİT~~
      → **GÜNCELLEME (2026-08-12 pencere-sonrası operatör talimatı): gerçek-para DA 15/36, mod ayrımı YOK**
      ("birebir aynı" — KARAR-PAKETİ §E.3; Rol-1'in 3/8-sabit önerisi operatör kararıyla aşıldı).
    · SLOT 20 + 0.5R: OPERATÖR ÖN-KARARI (2026-08-12: 'ISI 10R kalsın') — 0.25R geri-düşüş önerisi KALDIRILDI;
      ısı 10R sabit, 026 sayıları pencereye BİLGİ olarak gelir (karar değiştirmez, şasi-geçersizlik hariç).
    · EŞİKLER (024): sayı gelmeden söz YOK — CI>0 hücre varsa OOS-kapılı öneri; yoksa 'eşikler kanıtla doğrulandı' kapanışı.
    · momentum_burst (025): DONUK ÜÇLÜ EŞİK karar verir (operatör otomatik-akış seçimi): replay-CI>0 ∧
      portföy-etkisi≥0 ∧ çelişki-açıklandı → silahlanır; düşen ölçüt adıyla raporlanır.
    · ÇIKIŞ KOLLARI (027): CI>0 kazanan kol(lar) benimse; Rol-1 beklentisi scale-out (%38 erken-kesim panzehiri) — beklenti≠hüküm.
    · FİNAL-PAKET DOĞRULAMASI (2026-08-12 eklendi — operatör sorusu 'birleşince ne verecek'): pencerede
      SEÇİLEN tam kombinasyon dağıtımdan ÖNCE tek doğrulama replay'iyle ölçülür (kartlı, K+=1) — OAT
      etkileri toplamsal varsayılMAZ, etkileşim ölçülür; beklenen sayı pakete damgalanır.
    · SIRA: pencere → FİNAL-PAKET doğrulama koşumu → TEK goal/bounds dağıtımı → hemen OPT Faz-1 kablolama.
    *gerekçe: pencere kararları kanonik belgede ön-kayıtlı olsun (sohbette kaybolmaz) · bağımlılık: 024/025/026/027 ölçümleri · öncelik: en yüksek (bekleyen tek büyük karar).*

#### Ö-12 · ISI'nın piyasa-koşullu otomatik ayarı — ✅ ÖLÇÜLDÜ-KAPANDI (EDG-2026-028, 2026-08-12; ölçülmüş-red)
**Kapanma gerekçesi:** `EDG-2026-028…yaml:70-71` "**DOSYA HÜKMÜ: sabit-5R + mevcut rejim kapısı
kalır; kart kapanır (ölçülmüş-red)**" — Y1 rejim-harita `+3.074$` CI 0-içi → otomatik YOK; Y2
vol-hedef `−3.924$` → otomatik YOK. NOT (denetim C7): bu kalem OPT boru hattının "ilk müşterisi"
sayılıyordu — o rol **BOŞALDI**; iz ve yeni aday **WP11-E**'de.
12. **ISI'nın piyasa-koşullu otomatik ayarı (operatör sorusu 2026-08-12; aday kart EDG-028)** —
    kancalar HAZIR: exposure_score günlük hesaplanıyor (bugün yalnız açık/kapalı kapı), params_by_regime
    tabloları motorda BOŞ bekliyor; de-risk rampası (öz-performans) ile ÇARPIMSAL birleşir. Üç aday yöntem:
    rejim-haritalı ısı (trend_up 10R / chop 6 / high_vol 4 / trend_down 2 — değerler pencereden) ·
    vol-hedefleme (taban × hedef-vol/gerçekleşen-vol, bant [2R,10R]) · skor-lineer (10R × skor/100).
    OPERATÖR ÖN-KARARIYLA UYUM: 10R TAVAN sabit — otomatik ayar yalnız tavan ALTINDA kısar. Ölçüm:
    C-dünyasında sabit-10R tabanına karşı üç varyant (OPT boru hattının ilk müşterisi; kazanan
    params_by_regime kancasına). *gerekçe: ısı tek sabit yerine koşul-duyarlı · boyut: M · bağımlılık:
    026 şasisi + pencere girdileri · öncelik: yüksek (karar-paketi sonrası).*

#### Ö-15a · REJİM-KOŞULLU BOYUTLAMA — ✅ ÖLÇÜLDÜ-KAPANDI (EDG-2026-033, 2026-08-12)
    · ~~**15a REJİM-KOŞULLU BOYUTLAMA**~~ → **ÖLÇÜLDÜ-KAPANDI (EDG-033, 2026-08-12): İKİ HÜCRE DE DÜŞTÜ,
      düz-0.5R kanıtla doğrulandı** (h1 Δ−7.6k / h2 Δ−8.9k; sharpe 0.285→0.05/0.02). Öğretici mekanizma:
      saf-boyut etkisi eşleşenlerde POZİTİFTİ (+1.4k) ama 0.75R planlar 5R zarfını 2× hızla doldurup C'nin
      ~170 iyi işlemini yerinden etti — ZARF bağlayıcı kaynak; zarfa dokunmadan boyut büyütme kompozisyonu
      bozuyor (028/032 ile aynı yasa). Zarf×boyut birlikte-büyütme açılMAZ (028 zarf-10 çöküşü ölçülü).

#### Ö-15b · SLOT-YARIŞMASI KABUL POLİTİKASI — ✅ ÖLÇÜLDÜ-KAPANDI (EDG-2026-034 FAZ-0, 2026-08-12; İNERT)
    · ~~**15b SLOT-YARIŞMASI KABUL POLİTİKASI**~~ → **ÖLÇÜLDÜ-KAPANDI (EDG-034 FAZ-0, 2026-08-12):
      İNERT — motor kabulü ZATEN bileşik-skor azalan sıralıyor** (backtest.py:332; canlı loop.py:1641
      aynı yasa; 'aday>boş-slot' yarışması 1147 seansta 3). Öğretici: 030'un çalınması sıra değil SKOR
      sorunu (kötü-rejim adayı yarışı kazanabiliyor) → 15a hattını güçlendirir.

#### Ö-15f · YEREL DUYARLILIK TARAMASI — ✅ ÖLÇÜLDÜ-KAPANDI (EDG-2026-035, 2026-08-13; C+mb yerel optimum)
    · **15f YEREL DUYARLILIK TARAMASI (EDG-035; operatör yönergesi 2026-08-12: "iterasyonlarla en kârlı
      versiyonu bulalım"):** C+mb komşuluğu OFAT 6 hücre — slot {15,25} · boyut {0.40,0.65} · zarf
      {6.5,8.0} (K+=6). SERAP-KORUMASI: benimseme yalnız CI-üstünlükle (nokta-P&L sıralaması hüküm girdisi
      değil); hiçbiri üstün değilse C+mb yerel-optimum kanıtla kapanır. Zamanlama: dağıtım-SONRASI temiz
      ağaçta (033 dersi). SÜREKLİ motor: elle tarama tek atımlık — kalıcı iterasyon OPT Faz-2'dir (Ö-10:
      hermes bounds-uzayında kâğıt-OOS kapılı arama; Faz-1 kablolaması bu kod-turuyla açıldı).
      *öncelik: yüksek (dağıtım-sonrası ilk ölçüm).* → **ÖLÇÜLDÜ-KAPANDI (EDG-035, 2026-08-13):
      6/6 hücre CI-üstünlük ayağında düştü → C+mb @5R YEREL OPTİMUM KANITLA.** Yan kazanç: v237
      dağıtımının davranışı ZERRE değiştirmediği bayt-özdeşlikle kanıtlandı (regresyon yok).

#### Ö-17 · KARNE SÜRÜM SPLIT'İ — ✅ KAPANDI (2026-08-13 ~22:15Z, canlı doğrulandı)
**Kalan borç AÇIK ve WP5-B'de yaşıyor:** "sürüm terfisi dagit kapsamı DIŞIDIR" prosedürü RUNBOOK'a
yazılmadı (`grep "sürüm terfisi" docs/RUNBOOK.md` = 0, denetim §B notu).
17. ~~**KARNE SÜRÜM SPLIT'İ**~~ → **✅ KAPANDI (2026-08-13 ~22:15Z, canlı doğrulandı):** v5 kaydı
    uygulamanın KENDİ yazım kapısından (`store.write_json`→DB) eklendi, `current_version: 5`; v3/v4
    tarihçesi korundu (elle SQL YOK), `.migrated-*` artığı backups'a alındı, worker yedekli bakım
    penceresinde durdurulup başlatıldı (healthz 200). KALAN: prosedür RUNBOOK'a — "strategy sürüm
    terfisi dagit kapsamı DIŞIDIR: strategy.yaml scp + scoreboard DB yazımı AYRI adımdır; scp'lenen
    scoreboard.json'u bayat-defter migrasyonu `.migrated`'a taşır ve DB'ye YAZMAZ" (bu turun dersi).
    Özgün teşhis:
    `docs/TESHIS-CANLI-VS-REPLAY-2026-08-13.md` §4. Motor `strategy.yaml` v5'i (0.5R) okuyor ama DB
    `scoreboard.current_version: 3` — 08-12 mini-penceresinde scp'lenen scoreboard.json'u v234
    bayat-defter migrasyonu `.migrated-*`e taşıdı, DB'ye YAZILMADI. Etki: sürüm-bazlı değerlendirme
    yanlış sürüme atfediyor, yeni hipotezlerin ebeveyni yanlış, rollback yanlış hedefe döner
    (`analytics.py:683,2168` · `hermes.py:133` · `recompute.py:292` · `rollback.py:355`). DÜZELTME:
    v5 kaydı uygulamanın KENDİ yazım kapısından DB'ye (elle SQL DEĞİL) + `.migrated-*` artığı temizliği
    + prosedür RUNBOOK'a ("sürüm terfisi dagit kapsamı dışıdır; strategy.yaml scp + scoreboard DB
    yazımı AYRI adımdır" — bu tur öğrenildi). *boyut: S · öncelik: ACİL (öğrenme katmanı yanlış
    zeminde çalışıyor).*

#### Ö-19 · TOHUM YENİLEME — ✅ UYGULANDI (EDG-2026-036, 2026-08-13; canlıda doğrulandı)
**Kapanma gerekçesi:** `EDG-2026-036…yaml:157-166` "CANLIDA UYGULANDI … 885 tohum + 2 live_paper =
887 … **7/8 GEÇTİ**"; düşen kapı gerekçeli (`:167-173`). **Tek artık:** `equity_curve` yazılmadı
(`card:174-178`) → **WP2-D**'ye devredildi.
19. **TOHUM YENİLEME — defter ESKİ dünyadan (operatör bulgusu 2026-08-13; kart EDG-2026-036)** —
    canlı DB kırılımı: `replay_seed` n=95 (sv=4, ESKİ paket: slot5·1,0R·mb dormant) · `live_paper`
    n=2 (+277,99$). Yani öğrenme/kalibrasyon/DSR-PBO/karne'yi besleyen soğuk-başlangıç tohumu
    yürürlükteki C+mb @5R paketinin DEĞİL. Operatörün sorusu ("bunu C+mb için de yapmamız gerekmiyor
    mu") yapısal olarak haklı. Kart üç aşamalı: (0) tohumun gerçek tüketicileri kanıtla çıkarılır —
    tüketicisi yoksa yenileme YASA-6 ihlali olur, kart ucuz kapanır · (1) kuru koşum (eski tohum vs
    EDG-032'nin 885-işlemlik defteri ile tüketici çıktıları yan yana) · (2) uygulama YALNIZ operatör
    onayıyla, yedekli pencerede; eski tohum ARŞİVLENİR, kâğıt-icra satırlarına DOKUNULMAZ.
    *boyut: M · öncelik: yüksek (öğrenme yanlış zeminde) · bağımlılık: EDG-036 aşama-0.*

#### Ö-20a · `DD_VETO_MARGIN` — ✅ KAPANDI (2026-08-13, `62727d6` v238 "max_drawdown 0.16 zinciri")
**Kapanma gerekçesi (denetim A8/B5):** `meridian/shadowlaw.py:102` (repo) `DD_VETO_MARGIN: float =
0.08`; `state/goal.yaml:20` `max_drawdown: 0.16`; çivi `tests/test_dalga_w1_v216.py:526-528` goal/2
eşitliğini arıyor → **0,08 == 0,16/2** tutuyor. _(Sınır beyanı: sonuç assert'in okunmasından
çıkarıldı, suite koşumundan değil — otoriter suite Rol-1'de.)_
    · **20a ACİL/KIRMIZI:** `shadowlaw.DD_VETO_MARGIN` (`shadowlaw.py:97`) goal bütçesinin YARISI olmalı;
      max_drawdown 0,16'ya çıkınca 0,04'te kaldı → iki test kırmızı (`test_para_yasasi_v127`,
      `test_dalga_w1_v216::test_C5_dd_veto_margin_goalun_TAM_YARISIDIR`). Rol-1'in değişikliğinin
      aşağı akışı; AYNI TURDA kapatılır.

#### Ö-21 · SPRINT YETİM-RESTART'I KALICI BLOKLU — ✅ KAPANDI (v239 + v241, 2026-08-13, canlı doğrulandı)
21. ~~**SPRINT YETİM-RESTART'I KALICI BLOKLU**~~ → **✅ KAPANDI (v239, dağıtım 2026-08-13 01:26Z,
    CANLI DOĞRULANDI):** `mesgul` YÜK/YETKİ diye ayrıldı (yük kapıları yetimi bloklamaz; `elle_tik`
    yetki kapısı korunur — 2026-07-30'da ölçülmüş kazanın kapısı, Rol-1 onayı). KANIT: yeni sprint
    `sid=20260813-005434` doğdu ve skip sebebi `mesgul:canli_arama` → **`tetik_yok(gun=0<7, taze=0<5)`**
    oldu (doğru davranış). YENİ KALEM ÇIKTI: yeni sprint çocuğu da 0,5 saatte öldü (`sprint_yetim_tespit`
    yetim_saat=0.5). **ÖLÜM KÖKÜ DE BULUNDU VE KAPANDI (v241, 2026-08-13 17:16Z):** sprint ÇÖKMÜYORDU,
    ÖLDÜRÜLÜYORDU — çocuk worker'ın systemd cgroup'unda doğuyordu ve `KillMode=control-group` her
    `restart meridian`da onu biçiyordu (o gün üç ölüm: 41/113/1 adım, üçünün de tetiği bir restart —
    ikisi Rol-1 dağıtımı, biri paralel oturumunki; OOM yok, traceback yok, NRestarts=0). Çözüm: kendi
    şablon birimi `meridian-sprint@<sid>` (worker'a bağ YOK) + polkit kuralı (setuid'siz tetik —
    `NoNewPrivileges` koruması taviz VERMEDEN korundu). **KANIT TESTİ GEÇTİ:** sprint koşarken kasten
    `systemctl restart meridian` → aynı pid restart'ın öbür tarafında CANLI, `kosum_yolu:"systemd"`.
    Özgün teşhis: v235'in
    yetim-restart mekanizması ÖLÜ: son `sprint_cadence_skip` satırı `sebep="mesgul:canli_arama"`,
    `yetim=true`, `gecen_gun=5`, `arama_bayrak_yasi_sa=0.17`, `arama_bayat=false`. Yani canlı arama
    bayrağı sürekli tazeleniyor (hermes ~5 dk'da bir çağrı yapıyor) → "meşgul" kontrolü ASLA
    bayatlamıyor → yetim sprint gece penceresinde de yeniden başlamıyor. Kusur mantıksal: **yetim
    restart'ı "meşgul" kapısına tabi olmamalı** (yetim = zaten ÖLÜ süreç; onu diriltmek canlı aramayla
    çakışmaz — ayrı süreçler). Kadans-atlama doğru, yetim-restart yanlış yerde ona bağlanmış.
    DÜZELTME: yetim dalını meşgul-kontrolünden ayır + test (yetim ∧ meşgul → RESTART; sağlıklı ∧ meşgul
    → skip). *boyut: S · öncelik: yüksek (öğrenme sprintі 5 gündür durmuş).*

#### Ö-22 · GEMİNİ ÇAĞRI-ANI ESKİ MODEL ADI — ✅ KAPANDI (v239, 2026-08-13, canlı doğrulandı)
**Not:** kalıcı onarım hâlâ OPERATÖR kaleminde (§5 KOVA-3/C4) — sır yolu koda yazılamaz; ama
kalemin gerekçesi "model adı ölü"den "danışma yolu ölü"ye döndü (denetim F5).
22. ~~**GEMİNİ ÇAĞRI-ANI ESKİ MODEL ADI**~~ → **✅ KAPANDI (v239, canlı doğrulandı: `canonical_model
    ('gemini-3.5-flash')` → `gemini-flash-latest`).** Kök brief'imin ötesindeydi: göç SIR yolunu hiç
    kapsamıyordu (`NOUS_MODEL`) ve `GEMINI_MODEL` sırrı da ölüydü → doğrudan Gemini HTTP çağrısı da 404
    alıyordu. Tek kapı (`canonical_model`) rapor-edilen↔çağrılan split'ini de kapattı. **YAN BULGU
    ÇÜRÜTÜLDÜ:** nous'un birincili de aynı ölü ad (tencent/hy3 yalnız YEDEK) → `brain_chain_distinct`
    TAM AÇIK ve paylaşılan kimlik ölüydü. Kalıcı onarım OPERATÖR kaleminde (§5: Claude anahtarı ya da
    NOUS_MODEL'i Google dışına al) — koda yazılamaz, sır. Özgün teşhis:
    `hermes.GEMINI_DEFAULT_MODEL = "gemini-pro-latest"` (v235 alias düzeltmesi yerinde) AMA bugünkü
    20 `agent_call` olayında `model="gemini-3.5-flash"`. Yani varsayılan devreye girmiyor: model adı
    başka bir yerden (config/integrations kaydı ya da çağrı-yeri parametresi) geliyor ve ölü-model
    migrasyonu o yolu kapsamıyor. İYİ HABER: `nous` artık ayrı modele gidiyor (`tencent/hy3:free`,
    20 çağrı) → `brain_chain_distinct` ihlalinin YARISI kendiliğinden kapanmış olabilir (doğrula).
    DÜZELTME: model adının GERÇEK kaynağını izle (agent_call'ı yayan çağrı yeri), migrasyonu oraya
    da bağla + çağrı-anı ölü-model kontrolü. *boyut: S-M · öncelik: yüksek (ölü model = 404 riski,
    v235'in kapattığı sanılan sınıf).*

#### Ö-24a · SKİLL ÇAĞRI İZİ GERİLEMESİ — ✅ KAPANDI (v242 turu, 2026-08-13; canlı doğrulama Rol-1'de)
**Gövde (AYNEN, eski satır :1023-1025):** "**24a ÇAĞRI İZİ GERİLEMESİ** — `nous_call_skills` olayı
skill adlarını yazıyordu, 2026-07-20'de `preloaded:<sayı>`ya çöktü; Meridian defterlerinde skill ADI
yok, gerçek iz üçüncü-taraf `~/.hermes/skills/.usage.json`'da (v242 turu kapatıyor)". Kardeş
kalemler 24b-24h **WP7**'de açık kalır.

### Tamamlanan WP'ler (tam metin)

> **⚠ NUMARA ÇAKIŞMASI UYARISI (2026-08-13):** aşağıdaki **WP0 · WP1 · WP3** başlıkları **2026-07
> iş-emri numaralandırmasına** aittir (tamamlanmış, arşiv). §3'deki **WP1 (İcra ve Friksiyon)** ve
> **WP3 (Öğrenme Döngüsü)** bunlarla İLGİSİZDİR — 2026-08-13 yeniden numaralandırmasının ürünüdür.
> Başlıklar tarihçe-koru gereği DEĞİŞTİRİLMEDİ; ayrım bu notla yapılır.

### WP0 — Keşif ve Uyum Matrisi ✅ (2026-07-31; 14 mekanizma kanıtlı; en riskli 3 boşluk: iki-motor
icra ayrışması · hacim-onayı çelişkisi · BMO/AMC boşluğu)


### WP1 — Yalnız-OHLCV Adayları _(⚠ ESKİ 2026-07 numaralandırması — §3'deki yeni "WP1 İcra ve Friksiyon" DEĞİLDİR)_
- 1.2 52w-high ✅ ARŞİV (9/9 hücre anlamsız; VCP'den bağımsız ama bilgisiz ρ=-0.036; panel tanısı
  aralık-kısıtını dışladı) · 1.4 hacim-şoku ✅ ARŞİV (bant hayalet-artefaktı değil AMA 0/18 hücre
  ham rvol20'yi geçemedi — ham rvol20 @20 IC 0.065 ANLAMLI; canlı eşik kalır). TORUN-KART ADAYI:
  rvol≥2.5 bölgesi +1.61% anlamlı-pozitif, üçgen form onu sıfırlıyor — form-revizyonu YENİ ön-kayıtla
  (ölçüm-sonrası-seçim yasağına uyuldu). BT-2 hasar tespiti: 5/63 hücre anlamlılık DEĞİŞTİRDİ
  (sınırda hasar); 2018 hayaleti bu pencereye değmiyor — uzun-geçmiş artefaktları aklanmadı.
- 1.3 MAX-filtresi ✅ ARŞİV (2026-07-31: yön TERS — yüksek-MAX bizde @20 +1,46pp iyi; eleme
  hedef-çıkışların %28'ini keserdi; kill×2). **1.1 residual momentum ✅ ARŞİV (2026-07-31, kart
  EDG-007, K=2): 6/6 hücre CI-0-içi + artımlı katkı yok — yapısal örtüşme (residmom≈rawmom ρ=0,625,
  üst-terzil örtüşmesi %83); aile kapalı, torun yok. Yan kazanım: FF3 günlük faktörler repo'da
  (research/ff_factors/, damgalı+doğrulanmış) — 1.5 için altyapı hazır.** **1.5 vol-scaling overlay ✅ ARŞİV (2026-07-31, EDG-008, K=2, kill#3): iki pencere de yönsüz;
  tasarım dersi — IS-çapalı sigma_hedef düşük-vol OOS'ta kaldıraç-artırıcıya döner, ısı-rampasıyla
  çifte-kısma; torun (yalnız-kıs m<=1) tetik-şartlı: yüksek-vol penceresi birikince.**
- EMİLDİ: eski G2 skor-inşası S1/S2 adayları (rvolband/min_rvol çekirdeği) → 1.4'ün kart hükmüne
  bağlandı (iki ayrı ölçüm değil) · eski G7 vol-hedefleme → 1.5'in portföy-bacağı olarak, ısı
  tavanıyla birlikte POZİTİF-EV ÖNKOŞULLU (denetim RS-1).


### WP3 — Doğrulama ve Ek-Veri Aileleri _(⚠ ESKİ 2026-07 numaralandırması — §3'deki yeni "WP3 Öğrenme Döngüsü" DEĞİLDİR)_
- 3.2 insider yeniden-kaydı ✅ KAPALI: gerçek CMP ayrımıyla ölçüldü, pozitif-kontrollü sıfır →
  kalıcı arşiv (iş emrinin kendi kill-eşiği).
- 3.1 kaynak-doğrulama ✅ TAMAM (2026-07-31 gece — 4/4 birinci-el): CMP tanımı BİZİMKİYLE
  BİREBİR (insider arşivi GÜÇLENDİ; 2025 replikasyonu etki yarıya inmiş diyor — sıfırımız decay'le
  tutarlı) · Moskowitz-Grinblatt: en-büyük-quintile'da da var AMA Grundy-Martin itirazı (VW +
  1-ay gecikme sağlamlık protokolü ŞART — ileride kart açılırsa protokole gömülü) · Meursault
  PEAD.txt: etki büyük-cap'te sönmüyor ama transkript+NLP ister → veri bileti (FMP transkriptleri
  VAR, NLP altyapısı YOK) · McConnell-Xu ToM: DOĞRULANDI+replike → KART AÇILDI (EDG-2026-006,
  ölçümde).
- 3.3 text/analist PEAD 🔒 veri bileti (analist-tahmin/NLP; proxy yasak). EMİLDİ: eski Y6
  transkript-LLM skoru (aynı text-veri ailesi; look-ahead disiplini şartıyla aynı bilete bağlı).


### WP-G — Rejim Kapıları ✅ İKİ KART DA KAPANDI (2026-07-31; tanı turlu)
- **SMA-200 kapısı ✅ ARŞİV (kart EDG-005): KAPI AÇILMAZ.** İlk "açılabilir" hükmü tanı turunda
  DÜŞTÜ: karşı-olgu kolları kapının OOS doğrudan etkisinin SIFIR olduğunu (55 bloke gün, 0
  engellenen giriş), OOS "iyileşmesinin" tamamen IS-yankısı (portföy-durumu taşıması) olduğunu
  kanıtladı; tek atfedilebilir pencerede kill#1: Sharpe −0,25→−0,90, PARA −0,03→−0,09. Tez kısmen
  doğru (vol anlamlı ↓, oran 0,79) ama bedeli getiri — "pano göstergesi yeter". · **ToM tilt ✅
  ARŞİV (EDG-006):** ön-adımda yön ters (−11,8bps), ikizler hiç açılmadı.
- **KABLO BİLETİ ✅ KAPANDI (2026-08-01 temizlik turu):** spy_sma_gate GÖSTERGE'ye emekli edildi
  (blocks sabit False + knob_emekli beyanı + sessiz-diriliş çivisi; hükümsüz kapıya çekilmiş kablo
  söküldü). KALAN KÜÇÜK İŞ 📋: bounds.yaml'dan knob satırı düşülecek (makine etkisiz knob'u hâlâ
  örnekliyor — 6 değerlendirme boşa K harcadı; akşam penceresi).
- VIX koşullaması 🔒 veri-kilidi (operatörde) — SMA hükmünden sonra AİLE ÖNCELİĞİ DÜŞTÜ: rejim
  kapısı ailesi bu evrende "vol'ü düşürür ama parayı da düşürür" profili verdi; JM rejim modeli +
  koşullu vol kısma adayları açılmadan önce bu hüküm karşı-kanıt olarak okunmalı.
- EMİLDİ: eski Y3 dörtlüsünün SMA/VIX bacakları · turn-of-month index-tilt (EDG-006 ile öldü) ·
  breadth/distribution-day = PANO GÖSTERGESİ, kapı DEĞİL (kill-list).


### WP-R — Rampa/Çıkış Serbestleştirme ✅ ÖLÇÜLDÜ→DARALDI (2026-07-31 03:19; kart EDG-003 measured)
- **HÜKÜM:** P3 paketi ÖLDÜ (rampa serbest bile olsa P≤0,48 — suçlu rampa değil paketmiş);
  early_kill-tek sağ (P=0,606) → gölge-v2 V3 birikimi sürer; **rampanın koruması GERÇEK ölçüldü**
  (serbestlikte DD %4,6→%9,7) — gevşetme lehine kanıt yok. Kalan iş küçüldü: eşikleri bounds'a
  taşımak yalnız hipotez-görünürlüğü için (düşük öncelik); çıkış-mimarisi umudu artık gölge-v2
  canlı birikimi + E1/E4 zamanlama içgörülerinde (gece bacağı kaybı, 8-15g gündüz kazancı).
- Kanıt: de-risk rampası (%3-kıs/%8-sıfırla, KODDA SABİT) günlerin %92'sinde aktif, izin çoğu gün
  1 pozisyon — işlem üretiminin gizli boğucusu; P3 çıkış paketi imzası 4/4 (ödeme 2,84, beklenti
  0,287R) ama örneklem çöküşüyle "reddedildi-çürütülmedi".
- İş: rampa eşikleri bounds'a + `exit.profit_target_r`/`exit.time_stop_days` "kapalı" değerleri +
  sabit-rampa koşulunda P3 ve early_kill tek-başına yeniden-ölçüm + chandelier sıkıştırma
  tuhaflığının (max(close,hh) formu) düzeltilme kararı. Tek ön-kayıt kartı, K-muhasebeli.
- EMİLDİ: eski G3b çıkış reformu ölçümü (bu turun ta kendisi, genişlemiş haliyle).


### WP-K — Kurulum/Aile Genişletme
- **Trend-kolu RAFİNE ✅ ÖLÇÜLDÜ (2026-07-31, kart EDG-009, K=4; pozitif kontrol 0.000000 farkla):**
  rafine üstünlük KANITLANAMADI (B aylık-rebalans CI-0-içi, vol/DD kötü; muhafazakâr okuma) →
  HAM KOL incumbent. ASIL BULGU — KALICI PIT ŞERHİ: +13,1p/yıl fazlanın büyük kısmı evren-seçim
  yanlılığı; PIT-sağkalan evrende ~6-7p/yıl (D t=2.08 — hayatta, kill#2 tetiklenmedi). 2021+
  tanısı: decay değil oynaklık (eşlemeli çıtada erime yok, t=1.82). **GÖLGE-KİTAP ✅ KOD-HAZIR
  (2026-07-31 gece turu; canlıya sonraki pencerede):** trend_shadow.py sıfır-yetkili paralel defter
  — şasi-birebir sabitler, PIT şerhi kitap içinde, YASA-6 okuyucuları çivili, 645-seans smoke temiz
  (medyan tur 23ms), kapatma anahtarı var; ilk giriş 2026-09-01 ay-sonu kararıyla (tasarım). · **G4 pullback ✅ ARŞİV (2026-08-01, kart EDG-010, K=2): bağımsızlık GERÇEK (Jaccard ~0.02)
  ama kenar YOK — ham pozitiflik evren-tabanında kayboluyor (dip10 trend-evreninde anlamlı negatif);
  kart-ölçütü kusuru itiraflı, ders WP-M #3'e (ham-getiri ölçütü yasak)** · G5 in-play: EDG-011 ASKI SÜRER (tanım tarafı — 2026-08-02 keşfi: veri İKİ bağımsız eksenle
  olgunlaştı [Nasdaq-geçmişi %99,7 tamlık + EDGAR 8-K %98,4 çapraz-doğrulama, dakika-damgalı]
  ama kartın "t'de BİLİNEN takvim" lafzı ex-post kaynakla karşılanamaz; PIT defteri 0 satır —
  A1'de snapshot dosyası hiç doğmamış, AYRICA canlı earnings.csv 2-sütunlu/Jul-31 bayat =
  tazeleme turu dağıtımdan beri koşmamış, İZLENECEK). Tek-yönlü post-event tez ölçüldü ve
  **EDG-2026-020 ✅ ARŞİV (2026-08-03: kill#1+#3 — havuz-fazlası CI-0-içi/negatif-nokta; ham
  +%1,1 taban-sürüklenmesiydi [ders#3 vakası]; PEAD-kopyası değil ama bilgi de yok; 011'e
  aleyhte-önsel not düşüldü)** · **G6 koşullu-kısa → RAF (2026-08-02 fizibilite keşfi: 5 yüzeyin 4'ü YOK
  [broker/strategy/gölge/ayna], 12-kalem motor inşası; EDG-005 karşı-gözlemi: SPY<200MA
  günlerinde long hâlâ pozitif-beklentili görünüyor — kısa tezine doğrudan karşı; 55 OOS
  bloke-gününde 0 silahlanma. Yeniden açılış: operatör kararı + delist-bar sonrası kısa-tez
  kanıtı. Kanıt: research/olcumler/kesif_2026-08-02/)** · **VCP-DECOMPOSE ✅ ARŞİV (2026-08-01, EDG-015,
  K=2): çatı da bilgisiz — üst-%20 kompozit @10 aday-havuzunun ANLAMLI ALTINDA; form=bileşen-toplamı
  (ρ=0,95). WP-K'da ölçülmemiş hipotez KALMADI.** ⚠ İZLEME→ÖĞRENME: canlı skorun kesit-içi
  sıralaması kısa ufukta kanıtsız/ters (rs-negatif bulgusuyla tutarlı) — knob kararı öğrenme
  döngüsünün/operatörün; kanıt vcp_olcum'da.
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-MKP-2026-08-09.md` §WP-K):** kendi kuyruğunda **ölçülmemiş hipotez
  YOK** (VCP-DECOMPOSE ile tükendi). 3 artık kalem açık: **G5 in-play** (EDG-011 ASKI SÜRER — "t'de
  BİLİNEN takvim" lafzı ex-post kaynakla karşılanamaz + PIT defteri 0 satır + canlı `earnings.csv` bayat,
  FMP-402'ye bağlı) · **G6 koşullu-kısa** (RAF; EDG-005 karşı-gözlemi) · **EDG-021 2. koşum** (tanım-
  eşitleme, operatör — §8). Genişleme hattı (transkript-LLM/13F + WP-QC (b)-kovası [354 idio-skew /
  16 overnight / 269+125 mevsimsellik] + bileşen-ders Ek-B ①-⑤) kart-önce, WP-QC/HEDEF-5'te park.


### WP-N — Kanıt-Hızı Programı 🔴 AKTİF (2026-08-09; operatör onaylı sıra: N1→N2→N3→N4, N5 serpiştirilir)

**TEŞHİS (ölçülü):** darboğaz kod değil KANIT ÜRETİM HIZI. Faz-6'nın kapalı üç kilidi kârlı
işlem geçmişi istiyor (kodla açılabilecek kilit kalmadı — WP-L); Eksen-2 67 skill'in 2'sini
ölçebilmiş; Faz-5 4/20 çiftte; E3 ampirik bandı örneklem bekliyor; gölge modeli n_live=0
yüzünden hiç terfi edememiş. Sistem haftada ~4 pozisyon açıyor — kanıt musluğu bu.

- **N1 — Bildirim jetonu ayrımı ✅ KOD TARAFI (v216 — NAKED_POSITION jetonu obs.py NOTIFY_TOKENS'a ayrıldı; jeton pini `7f91178`'de beyanla büyüdü) / 🔒 KANAL OPERATÖRDE:** `NAKED_POSITION`
  jetonu (obs.py NOTIFY_TOKENS) + koruma alarmının `MIRROR_DRIFT`ten ayrılması — bugün ikisi
  aynı 6 saatlik susturma penceresini paylaşıyor; korumasız-pozisyon gecesi sev-1 alarmlar
  bastı ve operatöre HİÇBİRİ ulaşmadı (33 teslim edilmemiş alarm birikmiş). Jeton ayrımı kanal
  gelmeden de değerli (susturma ayrışır). KANAL (Telegram bot token / webhook URL) operatörün
  tek parçası — teslim zinciri hazır, kanal boş (WP-O §8.1).
- **N2 — Gölge kapsam genişletme ✅ KOD İNDİ (v217, kart EXE-2026-003 + R1 — gölge planlı-kol):** silahlı kol bayt-özdeş kaldı, planlı (silahlanmamış) kol AYRI defterde `kol: planli|silahli` etiketiyle (karışım kill#4'ü ateşlerdi, ölçülüp kanıtlandı). Tasarım metni: 4b bugün yalnız SİLAHLANMIŞ planların
  gölge dolumunu yazıyor (6 seansta 4). Genişletme: tetiği kesilen PLANLI (silahlanmamış)
  GO/REVIEW planları da gölge dolumu yazar, `kol: planli|silahli` etiketiyle AYRIK.
  **ROL-1 DÜZELTMESİ (ilk öneri metnindeki hesap yanlıştı):** bu genişletme Faz-5 kilidinin
  n_min'ini DOĞRUDAN doldurmaz — kilidin çifti gerçek-iç-dolum ister ve silahlanmamış planın
  iç dolumu YOKTUR (R1'in kapsam_disi kovasına düşerler). Ölçeği veren İKİNCİL eşleştirmedir:
  gölge(dakika-sim) × cf(EOD-sim) — İKİ SİMÜLASYON, aynı maliyet modeli, fark yalnız zamanlama
  (EXE-2026-002'nin kendi onayladığı metodoloji). cf tüm adayları kapsadığı için örneklem
  ~7 bin satırlık havuzdan beslenir. Bu ikincil hat KİLİDİ AÇMAZ (kilit gerçek-çift ister);
  birikip gerçek-çift hattıyla UYUŞURSA kilidin kanıt kaynağını genişletme önerisi ayrı bir
  kart revizyonu olarak OPERATÖRE gider. cf'nin çıkış-sadakati kusuru bu ölçümü KİRLETMEZ —
  bu bir GİRİŞ ölçümü, çıkış modeli işe karışmıyor.
  Skill gölge rotasyonu (57 ölçülmemiş skill, haftada N) AYRI kart — N2'den sonra açılır.
- **N2b — Skill görüş defteri + yaşam-döngüsü ⚠️ KOD İNDİ / CANLI KANIT BEKLİYOR (v218, kart EDG-2026-019):**
  skill yaşam-döngüsü dürüstlüğü + görüş defteri v1 katmanı indi (İLK koşusunda iki yönlü kesti).
  AMA terfi/emeklilik R-figürleri (vcp +0,116R / momentum-burst −0,114R) canlı state'te
  YENİDEN-ÜRETİLEMEDİ: `eksen2.uretilen=0`, `gorusleri.jsonl` beslenmedi, kadans bu adımı KOŞMADI —
  KURU-KOŞU. Doğrulama birkaç EOD penceresi + EDG-2026-019 ölçüm kodu bekliyor (uydurulmaz:
  ölçülemedi — bkz. `docs/SABAH-TRIYAJI-2026-08-09.md` §iii.7/§iv). 57 ölçülmemiş skill rotasyonu
  bu hatta bağlı.
- **N3 — Sermaye bekçileri ✅ İNDİ (WP-S SB-4 + SB-3, v216):** damgasız-yazım bekçisi (kitap
  `store` dışından değişebiliyor ve kimse görmüyor — denetim tabanı) + `taban_kaymasi` satırı;
  ikisi de v216'da indi (bkz. WP-S SB-4/SB-3 ✅).
- **N4 — cf çıkış-yasası sadakati 🔒 BAKIM PENCERESİ ŞARTLI (en pahalı, en değerli):** 6 çıkış
  tipi modellenecek + TÜM cf tarihi yeniden koşulacak (saatler, state'e yazar → canlı worker
  koşarken YAPILMAZ). %96'lık skor havuzundaki +0,039R iyimserlik kapanır; Eksen-2/terfi/edge
  hükümlerinin ortak zemini temizlenir. Kendi ön-kayıt kartıyla gider; pencereyi operatör açar.
- **N5 — Görünürlük turu ✅ İNDİ (v219 + v225 + v226):** 409-yutması (boş catch 6→0, v219) +
  `EV_TR` koruma_*/süpürücü çevirileri (v219 dokuz olay + v225 `siniflar` dökümü) +
  `k.olcum`un çizilmesi (beş kilit, v219) + hermes telemetri kartı (v219, İLK pano okuyucusu) +
  liveness kartı (v226). WP-S2 görünürlük borçlarının icra turu; hepsi app.js/api.py gösterim ailesinde.
- **N6 — DEVİR TATBİKATI ✅ KOŞTU (6. kova, 2026-08-09 01:20-02:10 UTC — `docs/DEVIR-TATBIKATI-2026-08-09.md`):**
  bağlamsız devralan ajan sistem haritası + ilk 10 risk çıkardı. **KRİTİK BULGU:** önceki koruma
  "✅ KAPANDI" beyanı artefakttan doğrulanmamıştı — koruma×süpürücü çarpışmasını yeniden açtı
  (`68ea173`), kök düzeltme v220+v221'le indi (bkz. WP-S ✅). Bağlam-sahibi SABAH TRİYAJI
  (`docs/SABAH-TRIYAJI-2026-08-09.md`) 13 kalemi dağıtımlardan SONRA yeniden ölçtü: **13/13 gerçek,
  0 çürük**; kapsamdaki P1=0 (tek gerçek sermaye-P1 çıplak pozisyon v220 ile kapandı). Fark hükmü:
  tatbikatın bulduğu bilinen-dışı kalemler (systemd exit-143, sprint orphan, dual-source) dalgaya/
  WP-S2'ye girdi. _(Aşağıdaki tasarım metni tarihçe olarak korunmuştur:)_
- **~~N6 — DEVİR TATBİKATI (tasarım; 6. kova; DAĞITIMLAR BİTİNCE koşar — operatör onayı 2026-08-09)~~:**
  BAĞLAMSIZ bir ajan (oturum hafızası YOK, yalnız depo + salt-okunur canlı) "sistem haritası +
  ilk 10 risk" çıkarır; girişi deponun kendi devir sözleşmesi (CLAUDE.md → MERIDIAN_ENGINEERING_LOG).
  Rol-1 çıktıyı BİLİNEN bulgu defteriyle (2026-08-07/09 turları = bilinen-pozitif seti) kıyaslar:
  (a) bilinenleri BULAMADIĞI yerler = depo onboarding'inin/tek-kaynak haritasının boşluğu —
  belge borcu olarak açılır; (b) bizim listemizde OLMAYIP bulduğu şeyler = bizim körlüğümüz —
  şiddetine göre dalgaya girer. Çıktı: docs/DEVIR-TATBIKATI belgesi + Rol-1 fark hükmü.
  SIRA GEREKÇESİ: dağıtım #2'den SONRA — tatbikat iyileştirilmiş durumu denetlesin ki bulduğu
  her boşluk GERÇEK kalan boşluk olsun, bu gece zaten kapatılmış bir şeyin gölgesi değil.


### Oturum snapshot'ları (tarihçe — açık kalemler ilgili §3/§5/§6'e taşındı; burada tam metin korunur)

**2026-07-31 gece-vardiyası + 2026-08-02 denetim-kuyruğu kaydı (eski §3 "ŞİMDİ" gövdesi):**

- **GECE DALGASI CANLIDA (03:00 dağıtımı):** WP-E icra turu (iki-motor tek yasası `broker.entry_law`,
  marketable stop-limit + gap-yolları, E2 slipaj defteri, E3 kötümser bant, E4 gece/gündüz) ·
  SIP-geçmiş-yasası (ilk canlı kanıt: `alpaca_sip_skipped_current_session`) · pano 8-kalemi ·
  BT-1 damga-migrasyonu UYGULANDI (95/95 `replay_seed`, gerçek-canlı sayaç 0'dan başladı) ·
  round-2 karantina (8 defter onarıldı) + `bars_integrity.json` (61 sembol) · regime `entry_gates`
  üretici düzeltmesi (SMA/VIX kapıları İLK KEZ ateşleyebilir durumda; knob'lar kapalı, tarih
  birikiyor) · tick-progress bekçisi (asılı-tick sınıfına) · Suite: **~2.900 test, 0 kırmızı.**
- **GECENİN ÖLÇÜM HÜKÜMLERİ:** 52wh ARŞİV · volshock ARŞİV (canlı eşik aklandı; ham rvol20 anlamlı)
  · MAX ARŞİV (yön ters — yüksek-MAX bizde İYİ) · EAP ARŞİV (güç-yeterli) · WP3.1 4/4 birinci-el
  (CMP birebir → insider arşivi kesinleşti; ToM YENİ KART ölçümde) · trend kolu YAŞIYOR (rafine
  bekliyor) · KOŞUYOR: WP-R rampa-P3 (K=4) + SMA/ToM ikizleri.
- **E4 İLK OKUMA (tohum-etiketli):** kaybın %84'ü GECE bacağında; tek pozitif dilim (8-15g)
  kazancını GÜNDÜZDEN yapıyor; giriş-gap p90 +100bps → %1 limit tavanı bağlayıcı olacak.
- **A1:** ilk tam-anayasa tick'i ilerliyor (IEX bacağı 252/253 teslim; onarım soğuma-içi-bekleme
  kokusu sabah listesinde); monitör-v2 + 3sa-gevşetilmiş bekçi nöbette.
- **Operatöre sabah kalemleri:** MNST 2005 ×0,48 bütünlük yorumu · delist-bar kararı (QuantConnect
  vs Massive planı) · bildirim kanalı · FMP planı · VIX kaynağı · shares-outstanding kaynağı.
- **DENETİM KUYRUĞU (2026-08-02 gecesi; kaynak `docs/SISTEM-DENETIMI-2026-08-02.md`):** KOVA A
  **9/9 İNDİ** (d50b03b defter+kadans · 395920e veri-hattı · 8a38248 gözetim; 44 yeni test, hepsi
  kırmızı-önce/canlı-kopya doğrulamalı). **KOVA B 16/16 İNDİ (2026-08-02 gündüz, operatör onayıyla — üç dalga):**
  90a6663 icra-güvenlik (C9/C23/C8) · 6020fa0 yapı (C3/C5) · 84fcf69 öğrenme-politika (C14/C16/C17) ·
  9b8327e küçükler (C1/C25) · 0a4453f iki-motor (C11/C18/C13/C19) · 6aba956 dalga-3 (C24/C12) ·
  0170cc0 borçlar + takip hükümleri (v76 fikstürü, Y3 ölçülemedi-notu). Dağıtıldı 14:00/14:30 UTC;
  birim migrasyonu yapıldı. 25 bulgunun 25'i kapalı ya da bilinçli-beyanlı.
- **Hermes-CLI yapılandırma dersi (2026-08-02, canlı vaka):** A1 taşınmasında ~/.hermes yapılandırması
  taşınmadı (hiçbir kanalın parçası değildi), senkron tek-atımlık olduğundan kendini onarmadı, hiçbir
  bekçi "yerel ajan yapılandırılmış mı" ölçmüyordu — LLM ikinci-görüşü 6 gün sessiz öldü. Kalemler:
  (a) servis açılışında senkron-doğrulama (GEMINI_API_KEY dolu + CLI modelsiz → yeniden senkron + olay);
  (b) pano senkron-sonucu zaman-damgalı (bayat OSError vakası); (c) bekçi: agent_call boş-serisi
  "kota" ile "yapılandırmasız"ı ayırt etsin; (d) RPD bütçesi ağa HİÇ çıkmamış çağrıyı saymasın —
  canlı vaka: ölü zincir 150/150'yi 06:19'da yaktı, gerçek Gemini kotası el değmemişken inceleme
  tüm gün bütçe-reddi yedi (sayaç korumaya çalıştığını ölçmüyor); (e) `review_candidates` dolu cevabın
  filtreden sıfır görüşle çıktığı hâlde OLAYSIZ None dönüyor (hermes.py ~2109) — ham cevabın ilk
  ~300 karakteriyle bir `candidate_review_empty_parse` uyarısı gerekir (2026-08-02 canlı vaka:
  Gemini dolu cevap verdi, kayıt yok, sebep görünmez).
- **VERSİYONLU-STATE DAĞITIM BOŞLUĞU (2026-08-02 akşam, canlı doğrulandı — KRİTİK SINIF):**
  bounds.yaml/goal.yaml versiyonda AMA rsync state/'i dışlar → hiçbir dağıtım bunları canlıya
  taşımıyor. Canlıda w_turnover YOK (sıfır turnover-örneklemesinin C15'ten bağımsız İKİNCİ kök
  nedeni — knob hiç doğmamış), heat_hard_r YOK (guard fail-safe aynı değerlerde; sahiplik canlıda
  gerçekleşmemiş). ÇÖZÜM toplu pencerede: canlı↔repo diff (canlıda repo-dışı satır varsa DUR) →
  worker durmuşken scp → doğrulama. KALICI KALEM: dagit'e versiyonlu-state adımı (diff-göster +
  onaylı-kopya) eklenmeli.
- **Denetim turunun bıraktığı küçük kuyruk (ajan-beyanlı):** `same_evening_bars` fırlatmayan arıza
  yolu hâlâ `empty` yazıyor (bacaktaki ikinci HATA≠BOŞ deliği; kapanış yolu: calls/fails deltasını
  `_fetch_alpaca_session` üzerinden taşı) · `conftest._clear_module_caches` `scheduler._state`i
  sıfırlamıyor (test_regime_patch sıraya-bağlı düşüş — kısmi `-k` seçimlerinde; tam suite düzeninde
  görünmez) · pano `_patOK/_patNote` `dedektor_dustu/olculemedi` bilmiyor (düşen dedektör yeşil
  görünür — S2R-3/app.js kalemi) · mutation.py `dedektor_dustu`yu okumuyor.

**DURUM PANOSU (2026-07-31 sabah — eski §4; bayat, GÜNCEL DURUM §3 tarafından güncellenir):**

| Eksen | Durum | % |
|---|---|---|
| Çalışma ortamı (A1 7/24 + bekçiler + yedek zinciri) | canlı; tick-bekçisi + fail-notify + VM-dışı yedek | 95 |
| Veri hattı (aynı-akşam IEX + sip-sabah + onarım + takvim/karantina/bütünlük kapıları) | canlıda; delist-bar kısıtı açık | 90 |
| İcra sadakati (iki-motor tek yasası + E2 defteri) | KOD canlıda; ilk gerçek emir sınavı bugünkü seans | 70 |
| Ölçüm yönetişimi (kartlar + K + DSR/PBO + donmuş holdout + kod-damgası) | işliyor; skor kartı 39/100 → yeniden puanlama bekliyor | 85 |
| Öğrenme otomasyonu (sprint/dolgu/Eksen-2/karne) | kadanslar canlı; ilk tam gece verisi birikiyor | 80 |
| Edge envanteri | 9 aile ölçülmüş-arşiv · 1 YAŞIYOR (trend) · 3 ölçümde (rampa-P3, SMA, ToM) | — |
| Pano dürüstlüğü | 8 kalem canlıda; operatör doğrulaması bekliyor | 85 |
| Gerçek-canlı kanıt | n=0 (damga sonrası dürüst sayaç) — birikim bugün başlıyor | 0 |


---

### §8.T — TAHTA ARŞİVİ (2026-08-30 bakım turu; `§2 TAHTA`'dan taşınan satırlar)

**Ajan dalga-A kapanış kaydı** (taşındı 2026-08-31 akşam, `§2` H1 satırından — v337 kuralı: kapanan kalem tahtada durmaz):
(**DALGA-A KAPANDI 2026-08-31 akşam** — SDD 3 görev incelemeli + dal-sonu geniş inceleme "With fixes"→kapandı; suite kırmızısı v323×4 düzeltme partisiyle yeşile, bileşim hükmü YEŞİL; **dağıtım 06317b7 canlıda** healthz 200; CANLI DOĞRULAMA: `/api/ajanlar` 4 kaynak durum=ok + 401 çivisi + Ultra rozeti bekçi/karnede canlı (sef 22:01 koşumunda döner — son oturumu Ultra-öncesi, sahte değil) + WAL/-shm temiz + `--kanit` gerçek koşum YEŞİL; filo.py RUNBOOK kümesine kayıtlı; `profil-guncelle --uygula` ilk gerçek koşumu ARIZA BULDU ve araç DÜRÜSTÇE KIRMIZI dedi (2026-08-31 ~15:51: etkileşimsiz ssh PATH'inde `hermes` yok → RC=127, güncelleme hiç koşmadı; yedek kapısı çalıştı; önceki "md5-özdeş=kanıt" değerlendirmem HATALIYDI — günlük dersi). DÜZELTİLDİ aynı saat (PATH öneki + 127 hüküm dalı, k1/k2 çivili, v348 67 yeşil) ve YENİDEN KOŞUM DOĞRULANDI 15:58 UTC — koşum-üretimi kanıtla: taze tar ×2 + hermes `installed_at: 15:58:39Z` damgası + model=ultra grep'i (önceden-doğru-durum dersi uygulanarak). DEVRET LİSTESİ BOŞ; dalga-B sırada — dalga-B kapsamına EK: son_brifing arşivi yüzeye inmedi, dal-sonu incelemesi yakaladı, Rol-1 hükmü kapsam-açığı→dalga-B kalemi 2026-08-31)

Buraya taşınan her satır **§2'de kapalı ayrıştırılıyordu** ve tahtada duruyordu. Metinler
**AYNEN** taşındı — tek karakter değişmedi, hiçbir satır silinmedi (`§0`: *tamamlanan /
bayat status snapshot → §8 ARŞİV, tarihçe-koru, silme yok*). Kronolojik neden-kaydı
`§7 KARAR GÜNLÜĞÜ`ndedir; burası **tahtanın** tarihçesidir, kararın değil.

#### A · §2 başlığındaki **2026-08-24 DOĞRULAMA TURU** bloğu — tam metin

> ## ⚑ 2026-08-24 DOĞRULAMA TURU — BU BÖLÜMÜN YETKİLİ DÜZELTMESİ
>
> 59 aday kalem koda/canlıya karşı doğrulandı, sonra "hâlâ açık" diyen her hüküm AYRI bir
> şüpheciye çürütülmeye verildi (19 cephe, 33 ajan). Tam liste ve kalem kalem kanıt:
> **`docs/ACIK-KALEMLER-DOGRULANMIS-2026-08-24.md`** (o belgenin EK bölümü tam sayımı taşır).
>
> **SAYIM: 25 gerçekten açık · 20 BAYAT-KAPALI · 14 KISMEN.**
> Aşağıdaki tablolar ve §3 WP hücreleri bu ölçümden ÖNCEye aittir. **Çeliştiklerinde bu blok
> yetkilidir.** Satırlar SİLİNMEDİ (tarihçe-koru) — üstlerine bu not düşüldü.
>
> ### BAYAT-KAPALI 20 — tahta açık gösteriyor, kalem KAPALI (tur harcama)
> `B-PENCERE-KAYDIR` · `24h` · `WP7-40 (K5)` · `B-NOUS-BEYIN` · `BT-2` · `M11-Ö1` ·
> `kart-lint` · `ARSENAL` · `B-CHOP-BUTCE` · `L3` · `L4` · `sprint-inactive` ·
> `GOAL_FAILURE` · `B-ORACLE-TASIMA` · `26-3cift` · `F9/H3` · `registry-budama` ·
> `B-OCI-BUCKET` · `B-DASH-CRED` · `B-RUNBOOK-KAPSAM`
>
> **Bunların DÖRDÜ §5'te "operatör bekliyor" diye duruyor ama kararları VERİLMİŞ ve
> UYGULANMIŞ:** `B-RUNBOOK-KAPSAM` (K4, "Evet") · `B-DASH-CRED` (iki faz da canlı) ·
> `B-OCI-BUCKET` (anahtar kurulu, S3 replica dakika başı sync) · `B-ORACLE-TASIMA`
> (taşıma 2026-07-30'da yapıldı). Operatöre boşuna karar bekletiyorlar.
>
> ### GERÇEKTEN AÇIK 25 — engele göre
> **HAZIR İŞ (4, bugün başlanabilir):** `korunum-kovası-3` (EDG-049 hükmü indi, engel kalktı) ·
> `20c` (tasarım kapalı, kod+çivi) · `Ö-54-ek` (short işaret sözleşmesi) · `K3/K6`
> (dün gece dosya çakışmasından koşulamadı, çakışma YOK) — **dördü de 2026-08-24'te başlatıldı.**
> **OPERATÖR (11):** `B-AJAN-TAVAN` · `B-AJAN-GIT` · `U6` · `B-FMP-PLAN` · `B-DELIST-KAYNAK` ·
> `bars_intraday` retention · `insider-A6` · `15c` · `15d` · `M11-Ö10` · `M2`
> **TAKVİM (5):** `Ö-54/EDG-042` (29 Ağustos KOŞTU — eşik dolmadı; sıradaki 5 Eylül; K1 eşik izdüşümü DÜZELTİLDİ 2026-08-30: ~3-4 hafta BAYATTI — ileriye dönük hız yalnız 1345 yolu, pooled ~6,5 hf / ayrık ~14 hf, karışık-örneklem KARARI VERİLDİ 2026-08-31: AYRIK/ts — docs/KARAR-P3-K1-AYRIK-TS-2026-08-31.md) · `Ö-55` · `Faz-5` örneklemi (11/20) ·
> `EXE-2026-003` (~8 hafta) · `eq_ayna` kanıtı (bugünkü seans turundan sonra)
> **BLOKE (5):** `EDG-040-a` · `EDG-2026-055` (PIT derinliği) · `propose_virgin_knob` ·
> `L2` · `M2`
>
> **`D5` bilinçli olarak OPERATÖR listesinde DEĞİL:** nominal olarak operatörde ama kararı
> verdirecek kanıt üretilmedi (EDG-042 bandı). "Operatör bekliyor" demek yanıltıcı olurdu —
> asıl engel ölçüm.
>
> ### KISMEN 14 — bir bacağı kapalı
> `F8-A1A8` · `EDG-2026-053` · `B-FINVIZ-TOKEN` · `13` · `24b` · `EDG-2026-056` · `2D` ·
> `20d` · `B-QC-LOGIN` · `B-FAZ6-KILIT` · `L1` · `25a/25c/25d` · `Ö-49-kalan` ·
> `zaman-varsayimi`
> İkisi (`2D`, `20d`) **yalnız tahta bakımı** — iş tamamen bitmiş, satır çizilmemiş.
> `B-QC-LOGIN`in "dotnet/docker yok" engeli BAYAT; gerçek engel operatörün `lean login`i.
> `25a`nın 14 kaleminden **13'ü inmiş**; kalan tek şey canlı `.env`de gereksiz token kopyası.

#### B · §2 H1 üstündeki **2026-08-24 gece karşıt-doğrulama** notu — tam metin

> **[2026-08-24 gece karşıt-doğrulama: aşağıdaki 7 satır BAYAT — kalemler kapalı, tahta açık gösteriyordu. Kanıt tek tek `docs/GECE-TURU-2026-08-24-ROADMAP.md` §4'te.]**
> · `M8 U2/U3 kart hijyeni` → 68 kartın yalnız 8'i `pending-` taşıyor ve 8'i de ölçülmemiş kart (`registered`/`measuring`) = DOĞRU hâl; `ops/kart_endeksi_uret.py --kontrol` → `GÜNCEL` (çıkış 0); çivi `tests/test_kart_hijyeni_v279.py`. Kalan tek gerçek karar **U6** (kart-K ↔ DSR `n_trials` bağı) ve o Rol-1'in.
> · `M11 kova-6 alan merceği taraması` → `docs/TARAMA-KOVA6-ALAN-MERCEGI-2026-08-24.md` mevcut (26 plan alanı + 14 `entry_law` alt-alanı, kalibrasyon 3/3); Ö-3/Ö-4 indi, Ö-5…Ö-8 K4'e ayrıldı.
> · `F8 kanonik durum sözlüğü uygulaması` → `meridian/durum_sozlugu.py` mevcut ve üç yüzeye kablolu (`watchdog.py:202/515/1347/1782/3053` · `api.py:3087-3089/3166` · `hermes_runtime.py:643-647`); "Sıradaki: kanonik sözlük uygulaması" satırı BAYAT. Kalan: A1-A8 soruları (Rol-1/operatör) + pano bacağı (`web/**` + `api.py`, yasak liste).
> · `EXE-2026-009 pencere kaydırma` → kod indi: `barclock.py:144/147/150`, damga `loop.py:700/1470/2571`, kapı `intraday_cycle.py:90/172`, okuyucu `edg042_kosum_2026-08-22/pencere_altbant.py`. **§5'teki "operatör-bekliyor" BAYAT** — karar 2026-08-23 K2'de verildi. ⛔ **İKİ AÇIK KALEM 2026-08-29 (kart bloğu `acik_kalemler_2026_08_29`; kanıt `research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/`):** **P-1 damga yalan söylüyor (kill#3 sınıfı, MADDİ)** — `pencere` damgası `loop.py:2761`'de DEFTERE YAZIM anındaki sabitten basılıyor, gönderim anındakinden değil; kod re-stamp'e karşı korunmuş ama bayat satıra bugünün rejimini basmaya karşı korunmamış. Ölçüldü: DE/PANW `ts=2026-08-21T20:32Z` ile ESKİ EOD-GTC yolundan gönderilmiş, canlı 1345'e 08-23T14:53Z'de dönmüş, satırlar 08-24'te yazılıp "1345" damgası ORADA almış → **1345 bandı %50 kontamine, gerçek n=2 (yalnız ECL/CRM, ikisi de `ts=13:45:0x`)**. Zehiri: `ts` iki donuk çekicinin de alan listesinde YOK, hakem kendi kontaminasyonunu ölçemez. **P-2 tetik inşaen erişilemez** — `oneri_tetigi` iki bandın da n≥10 olmasını şart koşuyor, 1330 n=0 ve kaydırma süresiz + retro-etiketleme kill#3'le yasak olduğundan bir daha HİÇ 1330 satırı üretilmeyecek: geri-al valfi hiçbir veriyle açılamaz. Üçü de operatör kararı; eşik/kural HİÇBİR kartta değiştirilmedi (kill#2).
> · `WP7-31a/31b hermes künye + active_model uydurma koruması` → `hermes.py:2185 cevap_veren_model()`, künye `:3748`/`:4269`, tüketen-okuma sözleşmesi `:4178`; `active_model()` `_model_id`'ye delege. Ailenin açık tek bacağı **WP7-40**.
> · `M11 Ö-3/Ö-4 entry_law ölü alanları` → `broker.py:255` ÖLÜ-ALAN DAMGASI[M11] bloğu indi (`olay`/`offset_kaynak`/`ref_kaynak`/`limit_bps`), çürük "okuyucusu E2" beyanı adıyla düzeltildi; çivi `tests/test_pano_durustluk_v280.py:303-347`.
> · `26 değer-eşitliği — ortamlar-arası 3 çift` → **P0-b indi** (`dagit.sh` → `[B] dağıtım-beyanı` bloğu → canlıya `state/dagitim.json`; çivi `tests/test_dagit_f9_beyan_v266.py`), **P2 indi** (`yerel_donmus_defter` damgası; çivi `tests/test_wp6_kucuk_kalemler_v268.py:111-162`), **#11** `guard.py` v268/`375abd5`'te mezar taşıyla kapandı. **KALAN TEK KIRMIZI:** `landing.html` + `workflow.html` sabit sayıları — `meridian/web/**` yasak listede, gece turunda AÇILAMADI.
>
> _(SİLME YOK: satırlar yerinde kalır, üstlerine bu not düşülür. "Kapalıyı açık göstermek"
> bu deponun `Ö-49 bayat-beyan` sınıfıdır ve tur harcatır — nitekim bu gece iki ajan turu
> zaten kapalı kalemlere gitti.)_

#### C · §2 **H1**'den taşınan KAPALI satırlar (5)

| kalem | WP | artefakt | kapı durumu |
|---|---|---|---|
| ~~**`Ö-51b` Ö1'in KİMLİKLİ yeniden tanımı**~~ **H6 ✅ KAPANDI 2026-08-22** | WP1 | `research/olcumler/exe006b_o1_kimlik_2026-08-22/HUKUM-O1.md` + `O1_kimlikli.json` | ✅ **Ö1 ÖLÇÜLDÜ: %60,8 · %66,9 · %73,8 · %73,6** (208/342 · 121/181 · 59/80 · 53/72) → dördü de %20 eşiğinin ÇOK üstünde, **`K1` şerhi AÇILIR**: replay'in kaçan-işlem maliyeti kabaca ÜÇTE İKİ abartıyormuş. **A kolu BAYT ÖZDEŞ** dört tavanda da (bu geceki `backtest.py` değişikliği A kolunu bozmadı → 08-17 ile doğrudan kıyaslanabilir). K harcanmadı (aynı hücreler). ⚠ **08-17'nin TEŞHİSİ KISMEN ÇÜRÜDÜ:** "aynı plan günlerce reddedilebilir" gerekçesi YANLIŞMIŞ — olay/plan çarpanı dört tavanda da tam **×1,0**, payda hiç şişmemiş. İmkânsız %132/%141'in TEK sebebi payın saf olmamasıydı (hücre başına 43-54 YERİNDEN-ETME işlemi kurtarılan sayılıyordu). 🔑 **B4 İÇİN KRİTİK:** kurtarılanların ort-R'si ~SIFIR (−0,079/+0,002/−0,005/+0,073) ve kirli payla ölçülen Ö2 dört tavanda da DAHA YÜKSEKTİ → pozitif işareti taşıyan şey kurtarılanlar değil **yerinden-etme** işlemleriymiş. `Ö-51c` ile aynı yöne bakıyor. _(eski kayıt: HÜKÜMDEN DOĞDU 2026-08-17, Ö1 ölçülemedi çünkü birim uyuşmazlığı — o teşhis yukarıda düzeltildi)_ |
| ~~eski `Ö-51b` satırı~~ | WP1 | tarihçe | 🆕 **HÜKÜMDEN DOĞDU (2026-08-17).** Ö1 ölçülemedi çünkü payda (`entry_missed_limit`) bir RED OLAYI sayacı, pay DİSTİNKT İŞLEM — ham bölme %132/%141 verdi. Abartının BÜYÜKLÜĞÜ, ret sayacı **plan kimliği** taşımadan hiç hesaplanamaz. Kartın "Ö1 > %20 → K1 şerhi" kuralı bu yüzden ne AÇILDI ne KAPANDI (askıda). `B4` kararının ÖN-KOŞULU |
| ~~**`Ö-51c` Ö3 ΔP&L bootstrap CI**~~ **H6 ✅ KAPANDI 2026-08-21** | WP1 | `EXE-2026-006` `HUKUM.md` + `O3_delta_pnl_ci.json` | ✅ **KOŞULDU — ve HÜKMÜ SERTLEŞTİRDİ.** Eşlenik ay-kümeli bootstrap (B=5000 · seed 20260812 · birim=AY · 42 ay · iki kol AYNI ayı görür): 0,005 → [−16.657 · +17.319] · 0,01 → [−10.148 · +24.400] · 0,02 → [−8.403 · +20.662] · 0,03 → [−4.820 · +21.381]. **DÖRDÜ DE SIFIRI İÇERİYOR** → "+7.163$" bir NOKTA TAHMİNİDİR, kanıtlanmış para DEĞİL. `HUKUM.md` bu satırla düzeltildi: "ΔP&L dört tavanda da POZİTİF" cümlesi artık anlamlılık İDDİA ETMİYOR. K harcanmadı (aynı hücreler). ⚠ **BU KALEM 2026-08-17'den 08-22'ye kadar ROADMAP'te AÇIK göründü, oysa 08-21'de kapanmıştı** — `B4`ün ön-koşulu olarak yanlış bekletti. Bayat-beyan sınıfı (A17/Ö-49); düzeltme 2026-08-22, kanıt diskten okundu |
| ~~**`Ö-52` `live_paper` damgası broker teyidi TAŞIMIYOR**~~ **H6 ✅ KAPANDI 2026-08-22 (DAĞITILDI)** | WP1 | `EXE-2026-007` + `docs/BULGU-KARSILIKSIZ-CANLI-ISLEM-2026-08-21.md` | 🆕 **ÖLÇÜLDÜ 2026-08-21, kart ön-kayıtlı 2026-08-22.** Damga bir BROKER TEYİDİ değil bir **KOD YOLU** beyanı: `loop._persist_trade`ten geçen her satır onu alır ve fonksiyon broker'a hiç sormaz. Reset sonrası 8 "canlı" işlemin **2'si** (`ALL` T00096 · `VLO` T00097) broker'da HİÇ VAR OLMAMIŞ — 62 emirde 0, 55 aktivitede 0 fill, 61.511 olayda 0 `alpaca_submit`. **Kök neden zinciri KAPALI:** `submit_plan` ONAY ANINDA çağrılıyor (`loop.py:743`), iç motor stratejiyi onaydan BAĞIMSIZ koşuyor → onaylanmayan plan iç defterde açılıp kapanıyor ve `live_paper` damgalanıyor (`plan_operator_approved` 7 olay, ALL/VLO yok). **Öğrenme etkisi ÖLÇÜLDÜ ve DAR:** karşılıksız satırlar indeks 885/886, yansıma tabanı 887 → **bugünkü ufuk penceresi TEMİZ** (besleyen 6 işlemin 0'ı karşılıksız); iki satır 2026-08-17'de koşan TEK yansımanın penceresindeydi. P&L etkisi **+277,99**. ⚠ Bu kalem **davranış DEĞİŞTİRMEZ** — onaysız planın iç motorda koşması bir tasarım tercihi olabilir; kusur sayılan tek şey iki sınıfın TEK DAMGA altında toplanmasıdır. Bir sonraki adım: `ledgerstamp`e broker-teyit boyutu → **ATILDI (2026-08-22):** kart `measured` (ölçüm ajanı ön-ölçümü BİREBİR üretti: Ö1=%25 · Ö2=+277,99 · 885/886<887, tohum 0, olculemedi 0) ve karar kuralı ateşledi → boyut EKLENDİ (55d72b3: dört değerli eksen · reconcile'da kendi kendini iyileştiren damgalayıcı · KIRPIK DEFTERDE KARŞILIKSIZ DENMEZ · pano satırı + alarm). Kalan tek adım DAĞITIM — ilk reconcile turu damgasız satırları kendisi damgalar → **DAĞITILDI (cbcdeed):** canlı doğrulandı — `defter_teyit = {teyitli 0 · karşılıksız 0 · olculemedi 8 · kapsam_disi 885}`; sekiz canlı satır dürüstçe 'henüz ölçülmedi', damga İLK reconcile turunda kendiliğinden basılır (beklenen: 6 teyitli + 2 karşılıksız → pano kırmızı satır) |
| ~~friksiyon dayanıklılığı~~ **H6 ✅ (040 measured 2026-08-22 — satır hijyeni; işi ACİL şemsiyesi + 042/043/045/046 kartları taşıyor)** | WP1 | `EDG-2026-040` hükmü tahtanın 🔴 ACİL kalemi olarak yaşıyor |

#### D · §2 **H1**'den taşınan — kartı `measured`, hükmü inmiş (1)

| kalem | WP | artefakt | kapı durumu |
|---|---|---|---|
| `23e` gün-içi pencere **[2026-08-23: H0'dan taşındı]** | WP1 | `EDG-2026-047` (1afdfd9) | kart ön-kayıtlı ve aynı gece ölçüldü — Ö1 ateşledi (bkz. WP1-B 23e eki); pencere-kaydırma kararı §5 `[B-PENCERE-KAYDIR]` |

#### E · §2 **H2**'den taşınan KAPALI satırlar (2) — bölüm bu turda BOŞALDI

| kalem | WP | artefakt | kapı durumu |
|---|---|---|---|
| ~~`23c` dinlenen limit sadakati~~ **KAPANIŞA ÇEKİLDİ 2026-08-23 (süpürme; H6-benzeri)** | WP1 | `EXE-2026-005` + `docs/superpowers/plans/2026-08-17-23c-dinlenen-limit-plan.md` | **H3 İCRADA — A KOLU KAPISI GEÇTİ 2026-08-17** (`research/olcumler/exe005_23c_a_kolu_2026-08-17/`: işlemler+seanslar bayt-özdeş, tek ayrışan alan `n_endeks_satir` ve o ADIYLA muaf). Çiviler **6/6** · `bar_low` uygulandı · bayrak kuruldu · **B KOLU DA KOŞULDU (a83c5e9)** ve örneklem BOŞ çıktı — sebebi yapısal, bkz. `Ö-51`. **H5 incelemesi yapıldı (2026-08-17): 2 kritik + 4 önemli bulgu, HEPSİ KAPATILDI** (kol kimliği damgası · AST sızıntı taraması · tolerans totolojisi · YASA 6 ret alanı). ⚠ **`Ö-51` KAPANDI 2026-08-17 (`EXE-2026-006` measured) — ama 23c'nin kendi Ö1/Ö2/Ö3'ü BUNUNLA ÜRETİLMİŞ SAYILMAZ:** 006 DAR tavanlı (0,005-0,03) bir ölçüm kolunda koştu, 23c'nin sorusu CANLI yasadaki (`limit_pct_cap=0,04` · `limit_atr_mult=100,0`) sadakattir ve orada kapı hâlâ YAPISAL OLARAK ÖLÜ (`BULGU-B-KOLU.md`: limit = `trigger·1.04` = `max_chase` tavanıyla birebir, `max_chase` ÖNCE sınanır → boş küme). Yani 006 hükmü 23c'yi ÇÖZMEDİ, sorusunun canlı yasada CEVAPLANAMAZ olduğunu TEYİT etti; 005'in kendi Rol-1 hükmü hâlâ AÇIK (aşağıda). Ön-koşullar ölçüldü (temiz ağaç · edg032b tabanı · `low` erişilebilir). Kill riski somutlaştı ve çözüldü: `fill_entry`nin **6 çağıranı** var, biri CANLI → kural tek yerde, davranışı `bar_low` parametresi seçer (bayrak DEĞİL — canlıda o veri yok, yani değişmezlik YAPISAL). H3 sırası bağlayıcı: **çivi önce**, sonra A kolu bit-özdeşlik kapısı. · **D5: kapanmadan limit-tavanı kararı YOK** **[2026-08-23 GÜNCEL — SATIR BAYATTI: EXE-2026-005 `measured`, Rol-1 hükmü Ö-51d 2026-08-22'de verildi (kartta; tahtanın H6 bölümünde kapanış satırı var). "H3 İCRADA / hüküm hâlâ AÇIK" okuması mükerrer tur açtırmasın: kalan TEK iş D5 OPERATÖR KARARI — §5 `[B-E1-LIMIT]`]** |
| ~~`tests/` §-atıf çevrimi (120 satır)~~ **H6 ✅ — BU SATIR BAYATTI (2026-08-22'de fark edildi)** | WP6 | `scratchpad/roadmap_donusum.py` | ✅ İş 2026-08-21'de ZATEN KAPANMIŞTI (bkz. aşağıdaki H6 satırı + commit a81a3dd): çıplak `§N`'lerin çoğu ROADMAP atfı DEĞİLMİŞ, yalnız `§2-N`/`ROADMAP §N` çevrildi (23 dosya), 88 çıplak atıf BİLEREK bırakıldı, tam suite doğruladı. Bu H2 satırı güncellenmeden kalmıştı — dördüncü bayat-beyan vakası (A17/Ö-49 sınıfı). _(eski metin: meridian/ ÇEVRİLDİ ✅ 10 dosya/18 satır; tests/ bekliyor: 86 satır assert içinde olabilir)_ |

#### F · §2 **H0**'dan taşınan KAPALI satırlar (16)

| kalem | WP | not |
|---|---|---|
| ✅ KAPALI (2026-08-23 K1 · `EDG-2026-048` NO-GO; kod `config.py` `URETIMI_DURAKLATILAN_REJIMLER`) · 🟠 **chop BÜTÇE-KAPALILIĞI — OPERATÖR KARARI BEKLİYOR** | WP3 | **KARAR BRIEF'İ HAZIR:** `docs/KARAR-BRIEF-CHOP-BUTCE-2026-08-22.md`. Kanıt İKİ YÜZLÜ: defter chop'u zayıf (95 işlem, medyan −0,221; 2022 kümeleri −10,5R) AMA kapının kendi R1-arama @chop dilimi trend_up'a EŞİT (+0,094; son üç küme +12,2R) — yani "chop kötü" beyanı ESKİ kümelerden. Yazılı politika YOK; dd-cezası seçicisiz (φ=0,064) ama kapatma gücü chop'ta %100. Karar operatörün |
| ~~**yerel↔canlı replay YOĞUNLUK anomalisi**~~ **H6 ✅ TEŞHİS TAMAM 2026-08-22 — GERÇEK ANOMALİ DEĞİL, İKİ KATMANLI YANILGI** | WP3 | (1) ETİKET HATASI (Rol-1'in — bu satırın ilk hâli): 21↔249 sayıları holdout değil fold3-FULL penceresinin; gerçek holdout çifti 5↔87. (2) KÖK = KONFİG-ÇAĞI (bayat-önbellek bağlam-tuzağı): yerel inc_cache 07-29'da v3-dünyasıyla (E1 bağlar · slot 5) donmuş, canlı 08-21'de v5-dünyasıyla (E1 serbest · slot 20). KONTROLLÜ A/B: aynı barlar+kod+pencere, yalnız konfig → 23↔90. HİJYEN KURALI: yerel inc_cache'ten hüküm OKUNMAZ (bayat çağ) |
| ~~**`Ö-53` kitap↔broker ADET AYRIŞMASI**~~ **H6 ✅ KAPANDI 2026-08-22 (OPERATÖR KARARI + B/D UYGULANDI)** | WP2 | 🆕 **ÖLÇÜLDÜ 2026-08-22** (`docs/BULGU-KALINTI-AYRISTIRMASI-2026-08-22.md`). Açık pozisyonların **YEDİSİNDE DE** kitap ile broker adet tutmuyor (AMGN 33/22 · BDX 43/40 · BKNG 43/22 · CRM 17/19 · EMR 64/37 · MRK 76/65 · MRNA 13/8), üstelik broker'da kitabın hiç bilmediği bir **NVDA** var. Kitap **15.661,22** fazla maliyet taşıyor. Yön TEK YÖNLÜ DEĞİL (CRM'de broker fazla) → basit "kısmî dolum" hikâyesi DEĞİL. Bu sembollerde broker SATIŞI YOK → fark satıştan değil **GİRİŞTEN**. Panonun "açıklanamayan 2.623,34"ünün ezici çoğunluğu bu. **KÖK NEDEN ÖLÇÜLMEDİ ve UYDURULMADI** — adaylar (hiçbiri sınanmadı): kısmî dolum · boyutlandırmanın broker equity'si yerine kitap equity'siyle hesaplanması · `scaled_out`un tek defterde işlenmesi · `Ö-52`nin kök nedeninin (iç motor onaydan bağımsız koşuyor) adet düzeyindeki karşılığı — sonuncusu EN OLASI, aynı zincir zaten iki tam işlemi karşılıksız üretti. ⚠ **`mirror_divergence` bu işi YAPMIYOR:** yedide yedi ayrışma varken alan `None` — ve panoda `None` "ayrışma yok" gibi okunuyor, oysa "ölçülmedi" demek. 🆕 **KÖK NEDEN AYNI GÜN BULUNDU (2026-08-22):** "kısmî dolum" hipotezi ÇÜRÜTÜLDÜ (her giriş emri TAM doldu: AMGN 22→22 · BDX 40→40 · CRM 19→19 · EMR 37→37 · BKNG 22→22). Gerçek sebep `loop.py`de: `eq_now=_hb["equity"]` KİTABI, `eq=acct["equity"]` AYNAYI boyutlandırıyor — aynı `1R=%1` kuralı İKİ FARKLI sermaye tabanına uygulanıyor, oran da bu yüzden sabit değil. Farkın kendisi kusur DEĞİL; **kayıtsız** olması kusurdu (makbuz aynanın kullandığı sayıyı hiç yazmıyordu → makbuzu OLAN dört planda bile sapma açıklanamıyordu). **KAPATILDI:** makbuza `eq_ayna` + sapma tablosuna `ayna_taban` sınıfı (v257, 10 çivi, kasıtlı-kırmızı doğrulandı, 74 mevcut sınıflandırıcı testi yerinden oynamadı). ⚠ İLERİYE DÖNÜK: bugünkü yedi makbuz alanı taşımıyor, geriye doldurmak uydurma olurdu. **KALAN AÇIK — POLİTİKA (operatörde):** iki taban ayrı mı kalsın, tek tabana mı geçilsin? Ayrı kalırsa adetler ayrışmaya ve köprüde kalıntı üretmeye devam eder; tek tabana geçmek "hangisi doğru" sorusunu açar (broker'ınki gerçek para, kitabınki stratejinin muhasebesi) | → **KAPANIŞ:** operatör iki tabanın BİRLEŞTİRİLMESİNE karar verdi; ikinci mekanizma önce ÖLÇÜLDÜ ve baskın çıktı (per_share: ayna tetik−stop, kitap dolum−stop; CRM'de sente doğrulandı 19 vs 17). **B** ayna kitabın tabanıyla boyutlanır (`min(eq_now, eq)` guard'lı; makbuz ÜÇ tabanı da yazar) · **D** kitap dolumdan sonra aynanın adedini benimser (`_adet_benimse`: eşikten bağımsız, kapsamı dar, her benimseme kayıtlı). v258 10 çivi + K5 7-alan sözleşmesi; suite 6281/0 |
| ~~`23d` bar-içi stop varsayımı~~ **H6 ✅ ÖLÇÜLDÜ+HÜKÜM 2026-08-23 (`EDG-2026-045` measured)** | WP1 | **Ö1 ateşledi: sıfır-stop-slip DEFTERİ ANLAMLI ŞİŞİRİYOR** — 10 bps'te −5.697$ [−7.604,−4.004]; üç CI de sıfır-dışı; paket 10 bps'te pozitif kalıyor (+18.109). ŞERH düşüldü: EDG-040 bandı iyimser tarafta + replay hükümlerine genel stop-slip şerhi. Ö2 askıda (042-K3 bandı). İki DURDU tarihçesi kartta (B1-taban + bağ-yuvarlama alet-tamamlaması — üçüncü alet vakası) |
| ~~WP-E 6 boşluk sınıfı + E2 canlı-geçiş~~ **H6 ✅ SATIR BAYATTI — İŞ 2026-08-12'DE KAPANMIŞ (v234/531ea2b)** | WP1 | Envanter ölçtü (`docs/ENVANTER-WPE-BOSLUK-2026-08-22.md`): commit gövdesi 6 sınıfı TEK TEK sayıp kapatmış ve mekanizmalar bugün CANLIDA koşuyor (exit_fill kuyruğu · kapsamlı emir penceresi · kısmi-dolum sınıflaması · anakronizm kapısı…). On gün boyunca açık göründü — Ö-49 bayat-beyan sınıfının en büyüğü. E2 canlı fotoğrafı ve kalan kart-adayları belgede |
| ~~`equity_curve` zinciri / `seed_boundary` kadanslı yazar~~ **H6 ✅ KAPANDI 2026-08-22 (v264)** | WP2 | gerçek borç ölçümle bulunup kapandı: tohum sınırı beyansızdı (882 nokta) · `defter.sinir` v245'ten beri okuyucusuzdu (YASA 6) · `yollar_ayrisik` panosuzdu — üçü bağlandı |
| ~~`SB-2` `drift_sinifi` · davranışsal EOD süpürme kanıtı~~ **H6 ✅ KAPANDI 2026-08-22 (v265)** | WP2 | drift_sinifi zaten v257'de (ayna_taban); EOD kanıtı: davranış 10/10 seansta ölçüldü (koruma dokunulmamış, v220 sonrası akşam iptali 0) ve `eod_supurme_report` bekçisiyle KAYITLI |
| ~~`28d` kapı ÖLÇEMİYOR~~ **H6 ✅ TEŞHİS TAMAM 2026-08-22 — ÖNCÜL ÇÜRÜDÜ, GERÇEK MEKANİZMA BULUNDU** | WP3 | "chop hiç oluşmadı" GÜN düzeyinde YANLIŞTI (birim karışıklığı: işlem sayımı gün diline çevrilmiş): 2022→bugün 324 chop günü, 2025-07 sonrası 52 (%18,1), sonuncusu 2026-07-30. GERÇEK MEKANİZMA **BÜTÇE BAĞLAŞIMI**: chop taban 45 − dd≥5 cezası 20 = 25 < min_exposure_score 40 → bütçe 0 → plan kurulamaz → chop işlemi DOĞAMAZ; son açık chop günü 2025-06-12 (52/52 kapalı, mekanik birebir; 5 chop işlemi 5/5 çapraz-doğrulandı). Eşik-adayı envanteri ölçüm dizininde (dd cezası 20/tetik 5 bounds'ta YOK — kapalı 262 günün tek nedeni). → DÖNÜŞEN KALEM aşağıda: chop bütçe-kapalılığı POLİTİKA sorusu |
| ~~`28g` · `28h` · `28i` incumbent holdout −0,5366~~ **H6 ✅ TEŞHİS TAMAM 2026-08-22 — GERÇEK BOZULMA, ölçüm artefaktı DEĞİL** | WP3 | Vekil tabanla −0,5365 yeniden üretildi (hedef −0,5366; canlı ssh sınıflandırıcıya takılınca exe003 DB kopyası kullanıldı). H1 rejim ÇÜRÜDÜ (holdout %87 trend_up — LEHTE) · H2 kuraklık ÇÜRÜDÜ (n=87≥30) · H3 ÖLÇÜLDÜ: skorun %64'ü ret_c(−0,688), %37'si sharpe_c(−1 kırpık). Kayıp TEKDÜZE (4 setup'ın 4'ü negatif, 3 ayın 3'ü kötüleşiyor), stop payı %48→%72, stop_gap 11 işlem hasarın yarısı, yarıiletken kümesi ağır ama kalan 47 işlem de negatif — SPY yükselirken genele yayılı kayıp; endeks-türevi rejim bunu GÖRMEZ. İncumbent'ın holdout'ta gerçekten kötü olduğu KESİNLEŞTİ |
| ~~`Ö-48` hayalet düğmeler~~ **H6 ✅ KAPANDI 2026-08-22 (SÜZGEÇ + ÖNCÜL DÜZELTMESİ)** | WP3 | YENİDEN ÖLÇÜLDÜ: bugünkü bounds 32/32 motor-okuyuculu — katı tanımla hayalet BUGÜN YOK; %62 vakası "bounds-var/params-yok" sınıfıydı (kaynak `propose_virgin_knob` — o tamirat AYRI sınıf, kart-önce, aşağıda H0). Süzgeç yine de KALICI BEKÇİ olarak kuruldu (sınıf iki kez tekrarlamıştı): AST-tabanlı motor-zinciri taraması · UCB/sonda uzayına hayalet girmez · üç hâl ayrık ([]=temiz · [..]=süzüldü · None=ölçülemedi, fail-open) · v263 10 çivi, mutasyon-kırmızısı 5 çivi yakaladı · 340 kapsam testi 0 kırmızı |
| havuz tavanı `cpu−2` → `cpu−1` | WP3 | **H0→H1: KART ÖN-KAYITLI `EDG-2026-044`** (K=1; aşama-1 yerel duvar-saati elemesi, aşama-2 CANLI yalnız operatör onaylı bakım penceresinde; ikiz-formül [sprint.py:672] tek-kaynak şartı kill'de) **[2026-08-23 ÖLÇÜLDÜ — KART KAPANDI: aşama-1 kazanç %17,49 < %20 (A-B-A-B, tekrarlar %1,5 içinde, işçiler doygun); tavan KALIR, aşama-2 hiç açılmadı. Ö3 yan-bulgu: ikiz formül tabanları zaten farklı (reflect max(1,·) ↔ sprint max(2,·)) — tek-kaynak XS hijyen adayı.]** |
| ~~türetilmiş artefakt yeniden üretimi~~ **[2026-08-24 KAPANDI-BAYAT: üretici üçlüsü dışlama kapısına kablolu ve yeniden üretim gecelik-otomatik; canlı `component_ic.json`/`threshold_curve.json` 2026-08-21 taze ve `bars_integrity` bar-taban damgalı (`docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A1)]** · ~~seans-içi boşluk~~ **[2026-08-24 KAPANDI-BAYAT: dedektör 08-01/02'de sevk edilmiş ve canlıda koşuyor — 3.321 `intraday_gap_detected` / 15 seans, 3.321'i `sembol` (ölçülmüş yapısal IEX gürültüsü) ve 0 `akis` (`docs/ELEME-WP4-HAVUZ-2026-08-23.md` §A2)]** · earnings kapsama **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1): fail-open'ın GERÇEKLEŞMİŞ bedeli PIT anlık görüntüsüyle retro sayılır; donuk eşik — vaka N≥1 → daraltma tasarımı WP4 iş kalemine döner, N=0 → fail-open beyanlı kalır ve kalem ÖLÇÜLMÜŞ-RETLE kapanır → KART ÖN-KAYITLI: `EDG-2026-055` (3ddafb1)]** · MNST split **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1): A1 oran-imza tanıma — `dev > MASSIVE_TOL` iken {1/4,1/3,1/2,2,3,4} × tek toleransla "taban-farkı" sınıfı; donuk eşik — bilinen split gününde (MNST 2026-08-11) yanlış-alarm 1→0 VE split-dışı günlerde yanlış-pozitif 0 → A1 sevk edilebilir → KART ÖN-KAYITLI: `EDG-2026-056` (3ddafb1)]** | WP4 | **[2026-08-24 eleme: 2 KAPANDI-BAYAT · 2 KART-ADAYI (K=2)]** |
| `F9` dagit kapsamı dışı 4 canlı artefakt · `H3` tur-2 seccomp · ~~gözlemlenebilirlik a-e~~ **a-e ✅ 2026-08-23: yedisi de ZATEN KAPALIYMIŞ (bayat-beyan #5; kanıt WP6-D arşiv bloğunda)** | WP6 | F9+H3-hazırlık ajanı uçuşta (2026-08-23); versiyonlu-state adımı da ona devredildi |
| ~~operatör bloklarının kimliklendirilmesi~~ **H6 ✅ 2026-08-23** | WP6 | 19 kalıcı `B-…` kimliği + §5 başında KİMLİK TABLOSU; tahtada 8 satıra atıf-kimliği eklendi; kimlik konumdan ayrıldı (blok kapansa da kimlik yeniden kullanılmaz) |
| ~~`24e` çekimser teşviki~~ **[2026-08-24 KAPANDI-BAYAT: "terfinin ASIL duvarı" iddiası yazıldıktan BİR GÜN sonra canlıda çürüdü — destekle/karşı/çekimser 10/14/76, `r_gap=0.857`, `promoted=true` (2026-08-14T21:03 AUTHORITY_CHANGE); bağlayıcı kısıt teşvik değil HACİMdi (`docs/ELEME-WP7-2026-08-23.md` §3)]** · ~~`24f` SKILL.md↔kod bağı~~ **[2026-08-24 BİRLEŞTİR: 24h rozet-damgası ailesine devredildi]** · ~~`24g` sprint sızıntısı~~ **[2026-08-24 KAPANDI-BAYAT: v242 kapısı (`sprint.kum_havuzunda` + `sync_agent_skills` atlaması) canlı kodda ve ÜÇ gerçek kum-havuzu koşumunda (08-14 · 08-15 · 08-22) sökümü BLOKE etti (`n_sokulecek=4`); canlı sync olayları 08-13'ten beri `pruned=[]` (`docs/ELEME-WP7-2026-08-23.md` §5)]** · skill rozeti | WP7 | ~~24e "terfinin ASIL duvarı"~~ **[2026-08-24 eleme: 2 KAPANDI-BAYAT · 1 BİRLEŞTİR → 24h; tahtada yalnız skill rozeti (24h) açık kalır]** |
| ~~`F8` durum sözlüğü · 15 bekçi mekanizması + `halt_learning`~~ **H1'e TAŞINDI (2026-08-22)** | WP8 | yukarıdaki H1 satırına bakın — tasarım belgesi yazıldı; "15" iddiası bayattı (ölçüm: 17). Çift-satır aynı gün yakalandı, kanonik okuyucu işi H1 satırında sürüyor |

#### G · §2 **DİK DURUM**'dan taşınan KAPALI satırlar (5)

| kalem | WP | durum |
|---|---|---|
| ~~**`A1` koruma yeniden-kurulumu — 4 pozisyon ÇIPLAK**~~ **H6 ✅ KAPANDI 2026-08-22 (ÖLÇÜMLE)** `[B-KORUMA-KUR]` | WP2 | `watchdog.koruma_report` canlı koşumu | ✅ **SATIR BAYATTI:** "4 pozisyon çıplak" 2026-08-07-09 penceresinin durumuydu (KORUMASIZ alarmı son kez 08-09'da öttü, olay defterinde 32 kayıt). 2026-08-22'de ölçüldü: bekçinin kendi hükmü **korumasız 0/7** — yedi motor pozisyonunun YEDİSİ DE tam korumalı (stoplar OCO bacağı olarak `held`, adetler pozisyonla birebir; `koruma_oco_gonderildi` 6 olay). Tek stopsuz pozisyon NVDA ve o MOTOR-DIŞI (operatörün malı) — bekçi onu zaten ayrı sayıyor. ⚠ ÖLÇÜM DERSİ: düz `orders(status=open)` sorgusu stop'ları GÖRMEZ (OCO bacakları `nested=True` ister) — ilk okuma "8/8 korumasız" diye YANLIŞTI |
| ~~**`B4` E1 limit bacağı — canlıda AÇILSIN MI**~~ **H6 ✅ OPERATÖR KARARI 2026-08-22: A+C — KAPALI KALIR** `[B-E1-LIMIT]` | WP1 | 🆕 **BLOKE: operatör (2026-08-17)** · 🟢 **HER İKİ ÖN-KOŞUL DA KAPANDI 2026-08-22 — KARAR ARTIK VERİLEBİLİR.** `Ö-51c`: ΔP&L CI dört tavanda da sıfırı İÇERİYOR. `Ö-51b`: Ö1 %61–74 (abartı BÜYÜK, K1 şerhi açılır) ama kurtarılan işlemlerin ort-R'si ~SIFIR. **İKİSİ AYNI YÖNE BAKIYOR:** E1'in GEREKÇESİ çöktü (H1 düştü · H2 ölçülemedi · maliyet modeli üçte iki abartıyor) ama SONUCUNU (bacak kapalı) ters çevirecek POZİTİF kanıt YOK. Yanlış gerekçeyle doğru yerde durmak doğru durmak değildir — ama yanlış gerekçeyi düzeltmek tek başına yer değiştirmeyi de gerektirmez · `EXE-2026-006` measured → **E1 hükmü YENİDEN AÇILDI** (H1 düştü, H2 ölçülemedi) → bacağın canlıda etkisiz olmasının gerekçesi ARTIK KANITLI DEĞİL. Kart açmayı **ÖNERMEZ** (kendi sınırı) · strateji kimliği kalemi → §5 KOVA-2 · ÖN-KOŞUL: `Ö-51b` + `Ö-51c` → **KARAR (A+C):** bacak KAPALI kalır — gerekçe YENİDEN TEMELLENDİ: E1'in çürüyen hükmü değil, ölçüm (açmak dört tavanda da taban altında: A kolu −8,4k…−11,1k, en iyi B hücresi −1,2k; kurtarılanlar ~0R; hiçbir delta anlamlı değil; üstüne açmak iç motor↔canlı arasına ölçülmüş −8,4k'lık model boşluğu sokardı — 23c yapısal engeli). TEK açık argüman (kapı pahalı-dolum kuyruğunu keser, friksiyon yüksekse işaret dönebilir) `EDG-2026-043` kartına döküldü (`Ö-55`): hüküm EDG-042'nin gerçek bandıyla İKİ KAYNAKLI okunur, bant gelmeden B4 yeniden açılamaz (kill kriteri). `D5` tavan kararı C'nin sonucuna kadar PARK |
| ~~**`Ö-51d` `EXE-2026-005` Rol-1 hükmü + K kaydı**~~ **H6 ✅ KAPANDI 2026-08-22** | WP1 | 🆕 **BEKLİYOR: Rol-1 (2026-08-17)** · B kolu koştu, örneklem BOŞ ve sebebi YAPISAL (`BULGU-B-KOLU.md` yazılı) ama kart hâlâ `status: registered`. Belge kendi son satırında **"Rol-1 hükmü ve K-defteri kaydı ister"** diyor — `parameter_grid`e (dar tavan) dokunulduğu için K kararı gerekiyor. Aynı sınıf `v251` çivisiyle ölçülür hâle geldi ama o çivi yalnız `HUKUM*.md` yazılmış kartları bağlar; bu kartın belgesi `BULGU-*.md` | → **HÜKÜM YAZILDI (karta):** soru geçerli ama canlı yasada CEVAPLANAMAZ (yapısal boş küme); dar-tavan bölgesi `EXE-2026-006`da ayrı ön-kayıtla ölçüldü, K=8 ORADA sayıldı, bu karta EK K YAZILMADI. `status: measured`. Açık kalan tek şey D5 (operatör) |
| ~~`A2` bildirim kanalı (N1)~~ **H6 ✅ KAPANDI 2026-08-22 — KANAL CANLI, `B2`(c) FİİLEN YÜRÜRLÜKTE** `[B-BILDIRIM-N1]` | — | ✅ · kanal kimliği yok, 29 alarm teslim edilemedi. 2026-08-17'ye kadar "en ucuz kalem"di; **`B2`(c) seçildiği an politikanın TESLİM BACAĞI oldu**: (c)'nin tek içeriği "çıplaklık alarmı kanala bağlansın"dır ve alarm ZATEN kanal kapsamında (`obs.ALARM_NAKED_POSITION` ∈ `NOTIFY_TOKENS`, çivi `v216`) — eksik olan yalnız KİMLİK. Kimlik girilene dek (c) yazılı ama **teslim etmeyen** bir politikadır (`notify.configured()` False → `notify_undelivered.json` sayar) → **KAPANIŞ (2026-08-22):** Telegram kanalı kuruldu — operatör token'ı panodan girdi (sır Claude'un elinden GEÇMEDİ; kural), chat_id sunucu tarafında getUpdates'ten bulunup panonun kendi ucuyla yazıldı (maskeli ••••9134), `configured=True`, TEST TESLİM EDİLDİ (send=True, teslim-hatası 0). Kuruluş teşhisi: ilk denemede bota mesaj ulaşmamıştı (bekleyen güncelleme 0 ölçüldü, varsayılmadı). Birikmiş 310 alarm SAYAÇTIR, geriye akmaz — bundan sonraki her alarm telefona düşer |
| ~~`B1` pullback silahsızlanması~~ **H6 ✅ KARAR+UYGULAMA 2026-08-22 (dağıtım kuyruğunda)** `[B-PULLBACK-SILAH]` | WP11 | **BLOKE: operatör** · `EDG-2026-039` ölçüldü; strateji kimliği değişikliği → **A UYGULANDI:** ARMED_SETUPS üçlüye indi; yeniden-silahlanma kapısı donuk (cf n≥30 ∧ CI-alt>0, kart-önce); dormant kanıt kanalı çivili (v260). Dağıtım 043 sonrası suite'le |

#### H · §2 **H6 ✅** alt bölümünün TAMAMI (başlık + 20 satır) — tahtada kapanmış kalem durmaz

#### H6 ✅ — bu tur/önceki turlarda kapandı (kanıt §7'de)

| kalem | WP | kanıt |
|---|---|---|
| **`B2` koruma politikası — OPERATÖR (c)'yi SEÇTİ** `[B-KORUMA-POLITIKA]` | WP2 | ⚡ **2026-08-17 operatör kararı: seçenek (c)** — "mevcut üç kapı KALSIN + çıplaklık alarmı bildirim kanalına bağlansın". Yani `koruma_kur` üç kapılı (ölçüm + onay jetonu + öneri kimliği) KALIR; otomatik yeniden-kurulum (a) ve jeton-yalnız (b) REDDEDİLDİ. **KOD İŞİ GEREKMEDİ — (c) ZATEN YÜRÜRLÜKTEYDİ ve bu ölçüldü, varsayılmadı:** çıplaklık alarmı kendi jetonunu taşıyor (`obs.ALARM_NAKED_POSITION`, `watchdog.py:2836/2849` — v209'un ÖDÜNÇ aldığı `MIRROR_DRIFT` bitti) · `NOTIFY_TOKENS` el listesi değil **türetme** (`obs.py:138`) olduğu için jeton eklendiği an teslim kapsamında · zincir `obs.alarm → _maybe_notify → notify.send`. ÜÇ ÇİVİ: `v216:85` (jeton ∈ NOTIFY_TOKENS) · **`v216:130-141`** — (c)'nin ASIL güvencesi: gürültülü bir MIRROR_DRIFT susturma penceresi kurulduktan SONRA bile NAKED_POSITION teslim edilir, yani **muhasebe gürültüsü sermaye riskini SUSTURAMAZ** · `v209:248` (teslim edilen jeton sınıfı). **KALAN TEK BACAK `A2`** (kanal kimliği) — (c) onu ŞART koşar; o yüzden A2 satırı yükseltildi. Politika kapandı, teslim kapanmadı |
| **`Ö-51` limit bacağı hüküm sınaması** | WP1 | 🆕 **`EXE-2026-006` measured (2026-08-17)** — TAM pencere, K=8 (4 tavan × 2 dolum kuralı), altı kill kriterinin HEPSİ geçti. **HÜKÜM: E1 YENİDEN AÇILIR** (H1 monotonluk DÜŞTÜ: 9.773→**19.452**→17.948→17.858, tepe 0,01'de · H2 ÖLÇÜLEMEDİ: dört tavanda da bootstrap CI'ı sıfır İÇERİYOR). Ö1 ÖLÇÜLEMEDİ (birim uyuşmazlığı — ham bölme %132/%141, bir oran %100'ü aşamaz → None+neden) · Ö3 ÖLÇÜLDÜ ve **SENTE KAPANDI** (yan kanal büyük: cap=0,005'te 251 yeni işleme karşı 154 YERİNDEN, ve yerinden olanlar dört tavanda da kaybeden). **KAPALI DÖNGÜ KIRILDI** — E1'in "monoton zararlı" hükmü artık canlı yapılandırmayı GEREKÇELENDİRMİYOR. Türeyen kalemler: `Ö-51b` · `Ö-51c` (H1) · `B4` (operatör) · `Ö-51d` (005 hükmü). **DERS (ölçüm-şablonu):** duman penceresi Ö2'yi dört tavanda da NEGATİF gösteriyordu, tam pencerede işaret DÖNDÜ ve CI'ya girince ölçülemez oldu — küçük örneklem yalnız gürültülü değil **YÖN OLARAK YANILTICI** |
| **kart↔hüküm beyan çürümesi (`Ö-49` yüzeyi)** | WP6 | 🆕 **`v251` çivisi (2026-08-17)** — `a033256` hükmü 24 ölçüm artefaktı taşıdı, kart/§2/§6/§7'ye DOKUNMADI: kart `registered` derken hükmü diskte yazılıydı. Ölçüm ajanı DOĞRU davrandı (CLAUDE.md §3), eksik olan **Rol-1 devir adımının çivisiz** olmasıydı. Çivi kırmızı doğdu, hüküm işlenince yeşile döndü; 5 pozitif kontrol + düzenek çivisi |
| **operatör: Alpaca↔pano para farkı** | WP2 | ⚡ **2026-08-21 KAPANDI.** Şikâyet HAKLIYDI ve fark ÜÇ TERİMLİ bir köprü: broker 109.701,49 − gerçekleşmemiş 735,31 − broker'ın RESET GÜNÜ equity'si 99.992,62 = **8.973,56** ↔ kitap **6.350,22** → **AÇIKLANAMAYAN 2.623,34**. Reset günü iki taraf MUTABIKTI, ayrışma SONRA doğdu. `sermaye.broker_mutabakati()` + `alpaca.equity_on()` + `/api/today` alanı |
| **operatör: işlem başına para görünmüyor** | WP2 | ⚡ **2026-08-21 KAPANDI.** İşlem satırı R gösteriyordu, DOLAR göstermiyordu (`pnl_dollars` yalnız çekmecede — 15 işlem tek tek açılacaktı). Kuzey yıldızı zaten yasaklıyordu: "R geniş stopa yapısal önyargılı; dolar merceği olmadan sermaye kararı verilemez." Para sütunu eklendi, R kaldırılmadı |
| **öğrenme/antrenman "çalışmıyor"** | WP3 | ⚡ **2026-08-21 TEŞHİS: İKİSİ DE BOZUK DEĞİL.** Sprint `saat_dilimi_disinda` (21:53, pencere 22-06 — 7 dk kalmıştı) · öğrenme 30 günlük aşırı-uydurma ufkunda (`span_days 2/30`). Kod DEĞİŞMEDİ. `docs/TESHIS-OGRENME-ANTRENMAN-BEKLEMEDE-2026-08-21.md` |
| **ısınma `cleared=0` gerekçesiz** | WP3 | ⚡ **2026-08-21 KAPANDI.** `_gate_eval` gerekçeyi ÜRETİP ATIYORDU (YASA 6 tersi); iz artık `why` taşıyor, ısınma log'u `neden_dagilim` basıyor — kuraklık teşhis EDİLEBİLİR oldu |
| `Ö-51c` ΔP&L bootstrap CI | WP1 | ⚡ **2026-08-21 KAPANDI.** Eşlenik ay-kümeli (42 ay, B=5000): dört tavanda da **CI sıfırı İÇERİYOR**. Hüküm değişmedi ama SERTLEŞTİ — "+7.163" bir nokta tahminidir, kanıtlanmış para değil |
| `Ö-51b` ret kimliği | WP1 | ⚡ **2026-08-21 UYGULANDI.** `BacktestResult.entry_reject_ids` (neden → [(ticker,tarih)]); Ö1 artık DİSTİNKT PLAN paydasıyla hesaplanabilir. Tam pencere koşumu ayrı tur |
| `tests/` §-atıf çevrimi | WP6 | ⚡ **2026-08-21 KAPANDI — ve KURAL DÜZELTİLDİ.** Çıplak `§N`'lerin çoğu ROADMAP atfı DEĞİLMİŞ (`CLAUDE.md §3`, `denetim §3.1`, `YASA 4`). Yalnız `§2-N` ve `ROADMAP §N` çevrildi (23 dosya); **88 çıplak atıf BİLEREK bırakıldı** |
| `Ö-50` öğrenme süreç ayrımı | WP3 | v249 · pano 14,0 → **0,027 sn**, API CPU %93 → %2 |
| `28a` görünmez süzgeç | WP3 | `EDG-2026-041` status=`measured` (D1+D2) · v247 |
| `28c` · `28e` · `28f` | WP3 | v247 |
| `/api/diagnostics` 16,7 sn üretim arızası | WP8 | v243 · kök: tohum yenilemesi `load_bars` 95→400 |
| `D3-b F3-F13/F15` · `D3-c` | WP8 | tur kapanışlarında |
| `15g` slot↔sektör tavanı yapışıklığı | WP11 | `sector_cap_basis` ayrıldı; 620-hücre kalıcı matris |
| `C6` uzlaştırma (evren mi ısı mı) | WP11 | çelişki DEĞİLMİŞ — huninin iki katı; 15c askısı kalktı |
| ROADMAP `§1 HAT` + `§2 TAHTA` | WP6 | bu bölüm |
| `M1` kıyas-kirlenmesi | WP5 | `KYS-2026-001` **kill#1 · 2026-08-02** — yanlılık iki yüzeyde de CI-0-içi ve \|fark\|<10bps → PRATİK-ÖNEMSİZ; temiz-kıyas aracı OPSİYONEL, yeniden-okuma envanteri BOŞ. **KILL-LIST: tur harcanmaz.** ⚠ §3'ün 'en yüksek kaldıraç' cümlesi ÖLÇÜMDEN ÖNCEye aitti ve bayattı — 2026-08-17'de düzeltildi |
| WP10 referans verisi | WP10 | 🟢 açık borç YOK — tahtada satırı yok |

#### I · §2 **H0**'dan taşınan — 2026-08-31'de KAPANDI (`§7` boşluğu dolduruldu)

| kalem | WP | not |
|---|---|---|
| ✅ KAPANDI 2026-08-31 · ROADMAP `§7 KARAR GÜNLÜĞÜ` — **2026-08-30 turları kayıtsız** **[2026-08-30 EKLENDİ]** | WP6 | ~~**AÇIK**~~ · ölçüldü 2026-08-30: §7'nin en yeni girişi **2026-08-29**; o tarihten sonra dokuz commit indi (`90f6cdc` pencere damgası · `d9b7a74` bayat bytecode · `e17867a` CLAUDE.md yeniden yazımı · `7d0e307`+`5449a83` @bekci · `8dba332`+`0f8535d` @sef · `0c83fe6` yasa katmanlaması · `dcef1c6` P-3 hazırlığı · `83bc47b` kart kapanışları · `6dd38b5` @karne planı). Neden-kaydını Rol-1 yazar; bu satır onun KAYBOLMASINI engeller |

_(Kapanış: `2701cf4`…`6dd38b5` arası 24 turun neden-kaydı §7'ye yazıldı — girişler commit
gövdelerinden TÜRETİLDİ ve blok başında köken notuyla işaretli. Zaten kayıtlı iki tur
(`177a92b`, `6b9c6ad`) tekrarlanmadı.)_

**B-15 bakım dilimi + EDG-019 kapanış kaydı** (taşındı 2026-09-03 13:32Z, `§2` TAHTA H0 satırlarından — v337 kuralı: kapanan kalem tahtada durmaz; hücre metinleri AYNEN, madde biçiminde — §8 şema tablosu taşımaz, v343; durum hücresi DONE):

- `TSK-073` · 24b-24d skill görüş defteri — kalan yalnız 24b (WP: WP7) · **DONE(2026-09-03 EDG-019 resmî koşum 1)** · rol1 · S · —
- `TSK-078` · `26` değer-eşitliği — kalan 9 çiftin gerekçe envanteri (ortamlar-arası 3 çift) (WP: WP6) · **DONE(2026-09-03 8da5fb5; #3 açık)** · rol1 · S · —
- `TSK-082` · §6 kart indeksi ELLE tutuluyor — üretici başka dosyaya yazıyor (WP: WP5) · **DONE(2026-09-03 8da5fb5)** · rol1 · S · Rol-1 kararı
- `TSK-083` · ROADMAP satır çapaları — üçü de çürümüş (SATIR→SEMBOL çevrimi gerekiyor) (WP: WP6) · **DONE(2026-09-03 8da5fb5)** · rol1 · S · —
- `TSK-079` · `25a` KALDIR(14) / `25c` DİRİLT(3) / `25d` ezilme zinciri (25b 5/6 damgalandı) (WP: WP6) — operatör 2026-09-03 sabah: "üçünü de sıraya al" (25c dirilt kart-önce şartlı) · **DONE(2026-09-03 25a/25d kapalı; 25c-1 → EDG-072 KOVA C; 25c-2 debi)** · rol1 · S-M · —

**Dağıtım #8 kapanış kaydı** (taşındı 2026-09-03 gece, `§2` TAHTA H0 satırlarından — v337 kuralı: kapanan kalem tahtada durmaz; hücre metinleri AYNEN, madde biçimi; kanıt: TSK-075 d0ed07d suite #8 · TSK-077 2578061 · TSK-080 3a493a4 suite #9 · dağıtım #8 cbdac82 21:21Z canlı, healthz 200, evren 238/251/13):

- `TSK-075` · `13` scale-out latent kusuru (23e/23f kapandı, kalan tasarım yalnız 13) (WP: WP1) · **DONE(2026-09-03 d0ed07d dağıtım #8 cbdac82)** (eski durum: QUEUED) · rol1 · S-M · —
  Not (TSK-075): (status notu 2026-09-03 14:18Z: KOD TAMAM commit d0ed07d, suite #8 10071/0, push; dağıtım #8 SEANS SONRASI 20:05Z'ye ertelendi — _save_broker günde tek kez, seans içi restart gün-içi durumu riske atar.) (status notu 2026-09-03 13:13Z: B-16 SEVK, tek opus ajan — düzeltme = EDG-029 F1x mekanizmasının motor karşılığı, yeni kart yok. **OPERATÖR KARARI 13:13Z: kısmi kâr alma aralığına (bounds `exit.scale_out_frac` 0–0,75) DOKUNULMAZ, yalnız gizli hata düzeltilir; ileride gözden geçirme notu → Masa: "arama frac>0 önerirse ship öncesi yeni kart" şartı henüz çivisiz.** Alpaca ayna bracket kısmi-satış bacağı (tasarım belgesi Soru 6) frac=0 olduğu sürece kapalı, ayrı kalem yazılmadı.) **AÇIK** (yalnız `13`: `23e` `EDG-2026-047` `measured`, `23f` 2026-08-22 kayıt-düşmeyle kapandı) · `23e` gün-içi pencere · `23f` `gap_behavior:cancel` · `13` scale-out — not/kapı durumu: **H0→H1: TASARIM BELGESİ YAZILDI** (`docs/TASARIM-23E-23F-13-2026-08-22.md`). ÖNCÜL GÜNCELLENDİ: "1Day tek yol" kod düzeyinde doğru AMA gün-içi veri BİRİKİYORMUŞ — `state/bars_intraday` 20 dosya/186 MB, dakikalık, 249/251 ticker, açılış penceresi tam kapsanıyor; derinlik 20 seans (replay 2022'den koşar → 23e ancak YAKIN pencere için modellenebilir, tam-tarih için değil). Kart-adayı envanterler belgede → **23f KAPANDI (2026-08-22, kayıt-düşme):** cancel anlamlı tanımla ZATEN kanonik ölçülmüştü (%51 işlem kaybı, +11.233$ bırakır — ELENİR); yürürlük tanımı yapısal-totolojik (E2 gap 15/15). Hüküm EXE-2026-001'in gap-ekseni kapanışına işlendi; canlanma koşulu beyanlı (pivot değişirse). Kalan: 23e (yakın-pencere kart adayı) + 13 (tasarım) **[2026-08-23: 23e H0→H1'e TAŞINDI — kart aynı gece ön-kayıtlandı (`EDG-2026-047`, 1afdfd9) ve ölçüm koştu (Ö1 ateşledi; §5 `[B-PENCERE-KAYDIR]`); bu satırda kalan tasarım işi yalnız 13]**
- `TSK-077` · WP5 metodoloji/eşik kalıntıları — M2 DSR-yarısı kart-adayı + M11 kova-6 taraması (diğer 12 alt-madde 2026-08-24 elemesinde KAPANDI) (WP: WP5) — operatör 2026-09-03 sabah: Rol-1 şema kararı + kart (C-10); şema kararı 2026-09-03: DAMGA (`ret_seri`), KYS-002 R2 planı yazıldı, damga kodu ONAYLANDI 2026-09-03 · **DONE(2026-09-03 2578061 dağıtım #8 cbdac82)** (eski durum: ACTIVE) · rol1 · M · —
  Not (TSK-077): **BLOKE:** Rol-1 şema kararı (pnl-serisi damgası mı, ayrı donmuş-çekim betiği mi) · `M2` DSR-yarısı (`Ö-4` aracı) **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=1): önce reflect şema kararı (pnl-serisi damgası mı, ayrı donmuş-çekim betiği mi), sonra KYS-002'ye R2 revizyonu; taslak eşik PBO yarısıyla simetrik — taban RAPORLANIR, hüküm eşiği yok; kill: seri ölçek-eşdeğerliği doğrulanamazsa (Sharpe sapması medyan >0,01) DSR tabanı yazılMAZ]** · ~~`M7`~~ **[2026-08-24 KAPANDI-BAYAT: `olcum_araclari.kod_surumu_damgasi` + prescreen dört noktada damga yazıyor, çivisi `test_wpm_sasi_v173.py`; iniş 4b84871 2026-08-02 (`docs/ELEME-WP5-2026-08-23.md` #2)]** · `M8` **[2026-08-24 TASARIM-KAPANIŞI: tek konsolide Rol-1 oturumu U1 tarihçe-koru + U2 mekanik pending-* temizliği + U3 README'nin kart durumlarından YENİDEN ÜRETİLMESİ ile ölçümsüz kapatır, U5 ve U7 REDDEDİLİR, tek gerçek karar U6 (kart-K ↔ DSR n_trials bağı); kalan mini-iş hafta-1 partisinde]** · ~~`M9`~~ **[2026-08-24 KAPANDI-BAYAT: Chen-2022 dengeleme referansı hem kodda (`analytics.py:2590-2607`, "BU NOT BİR GEVŞETME DEĞİLDİR") hem `docs/olcum_standartlari.md:348`'de yazılı; iniş c9aee5e 2026-08-10 (`docs/ELEME-WP5-2026-08-23.md` #4)]** · `M11` **[2026-08-24 KART-ADAYI (kampanya ÖLÇ, K=0 tarama): kart DEĞİL, kova-6 salt-ölçüm taraması (4./5. kova emsali — belge-çıktılı, `meridian/` dokunulmaz, grid yok, hipotez yok); kalibrasyon kapısı şart (kova-4'ün 1/3 dersi)]** · ~~`2B`~~ **[2026-08-24 KAPANDI-BAYAT: genel standart `olcum_araclari.blok_bootstrap_ci` (sözleşme "1.0", moving-blok n^(1/3)), iki ikiz BEYANLI ayrı; iniş 4b84871 2026-08-02 (`docs/ELEME-WP5-2026-08-23.md` #6)]** · ~~`2C`~~ **[2026-08-24 KAPANDI-BAYAT: `analytics._empirical_bayes` + `shrunk_regime_cells` → `/api/diagnostics` → panoda çiziliyor, ikiz beyanlı; iniş 4b84871, τ²=0 bulgusu v125 arşivinde (`docs/ELEME-WP5-2026-08-23.md` #7)]** · `2D` **[2026-08-24 TASARIM-KAPANIŞI: R2'nin sahibi ROADMAP değil `holdout_rotation_advice`tir — advisor ROTASYON ÖNERİLİR dediği gün operatör kararıyla R1 usulü tekrarlanır (maliyet beyanı: fingerprint değişir, geçmiş p/ΔS kıyaslanamaz); takvimle değil TETİKLE yaşayan kalemi stokta tutmak çift-defterdir; kalan mini-iş hafta-1 partisinde]** · ~~`A4`~~ **[2026-08-24 KAPANDI-BAYAT: `prediction_accuracy_band` ilk commit'ten beri var (d9c3f24, 2026-07-31), n<3'te bant UYDURMUYOR (`A4_BAND_MIN_N`), okuyucuları gerçek (hermes kendi karnesini okuyor + pano) (`docs/ELEME-WP5-2026-08-23.md` #9)]** · ~~kill#4~~ **[2026-08-24 KAPANDI-BAYAT: daraltma kodda — `KAPSAM_DISI_SINIFLARI=("eod_yok",)` + fail-closed şerhi (`faz5_cikis.py:42-49`), payda eod_yok'u dışlıyor; kart R1 revizyonu işlenmiş (`EXE-2026-002…yaml:92-96`, status measured) (`docs/ELEME-WP5-2026-08-23.md` #10)]** · `20c` **[2026-08-24 TASARIM-KAPANIŞI: `position_size_r` LIMIT_KEYS'e alınMAZ ve bounds satırı dokunulmaz kalır, ama goal'a ÇİFT-BAĞ çivisi eklenir — slot≠20 VEYA size≠0,5 önerisi tek başına gelirse kapı `REVIEW`a düşürür (öneri ancak ÇİFT ve kart-önce gelir); kalan mini-iş hafta-1 partisinde]** · `20d` **[2026-08-24 TASARIM-KAPANIŞI: 20b emsaliyle KAYIT sınıfına indirilir (karar değil bilgi) — "hedef üçlüsü gevşek + CVaR marjı ince" cümlesi WP5-E'de izleme notu olarak kalır; canlanma koşulu beyanlı: EDGE VERDICT bir ölçütü CVaR yüzünden çevirirse ya da hedef üçlüsü bir hükme girerse; kalan mini-iş hafta-1 partisinde]** · korunum kovası (3) **[2026-08-24 BİRLEŞTİR: EDG-2026-049 hükmü sonrası (hüküm 2026-08-24'te indi: NO-GO — kova artık inebilir)]** — not/kapı durumu: **[2026-08-24 eleme: 6 KAPANDI-BAYAT · 5 TASARIM-KAPANIŞI · 2 KART-ADAYI (K=1) · 1 BİRLEŞTİR; kart biçim/lint satırı bu tahtada değil §3 WP5 tablosunda + WP5-A gövdesinde işlendi — `docs/ELEME-WP5-2026-08-23.md`]**
- `TSK-080` · `Ö-49` çapa/beyan çürümesi kalanı (WP: WP6) — operatör 2026-09-03 sabah: ikinci bakım dilimi (B-18) · **DONE(2026-09-03 3a493a4 dağıtım #8 cbdac82)** (eski durum: QUEUED) · rol1 · M · —
  Not (TSK-080): (status notu 2026-09-03 15:39Z: B-18 uygulandı — ÖLÇÜM: docs/ 2.997 çapa/1.020 çürük (RUNBOOK 64 → kaynağı günlük excerpt'i → [TSK-127]; tarihli teşhis 951 dışlandı; yaşayan 5 düzeltildi); codelaw'a docs dünyası (ok'u etkiler) + düz-metin/çapraz-biçim dedektörü (ok'u düşürmez, körlük tabanı ≥20 .md); B3 docstring-sayı ve SCC operatör kararı; inceleme uçuşta.) **AÇIK** · `Ö-49` çapa/beyan çürümesi kalanı — not/kapı durumu: yasa kuruldu, sınıf TAM kapanmadı

### §8.O — OPERATÖR BLOKLARI ARŞİVİ (2026-08-30; `§5`'ten taşınan KAPALI kova gövdeleri)

`§5`'in "BENDEN BEKLENENLER" bölümü operatöre **altı kalem** gösteriyordu ve altısı da
kapanmıştı — dördünün kararı 2026-08-17/22'de bizzat operatör tarafından verilmişti.
Gövdeler **AYNEN** buraya alındı; `§5`'te yerlerine tarihli birer kapanış satırı kondu.


#### J · §2'den taşınan — 2026-08-31'de KAPANDI (konsolidasyon ön-temizliği; metin AYNEN + kapanış şerhi)

| Kalem | Cephe | Hüküm (taşınma anındaki metin AYNEN) |
|---|---|---|
| ROADMAP ayrıştırıcısı kapanış sözcüklerini **kelime içinde** de eşliyor **[2026-08-30 EKLENDİ]** | WP6 | **AÇIK** · ölçüldü 2026-08-30: `meridian/api.py::_roadmap_madde_durumu` dört kapanış imini (onay imi + üç büyük harfli sözcük) **sözcük sınırı olmadan** arıyor; "chop BÜTÇE-KAPALILIĞI" satırı bu yüzden kapalı ayrıştırılıyordu. **Hüküm tesadüfen doğruydu** (kalem gerçekten kapanmıştı), ayrıştırma değil — sayaç bugün yanlış nedenle doğru. `meridian/` dokunuşu tam-suite kapısı ister → Rol-1 → ✅ **KAPANDI 2026-08-31:** PR #23 (`325fdce`) eşlemeyi sözcük sınırına daralttı, v287'ye 11 çivi (5 yanlış-pozitif + 5 daralma bedeli); `451c7ac` dağıtımıyla canlıda |
| `B1` pullback silahsızlanması — **DAĞITIM KUYRUĞU** (karar + kod 2026-08-22'de kapandı) **[2026-08-30 EKLENDİ: kapanan gövde §8.T/G'ye taşındı, kuyruk kalemi tahtada kaldı]** | WP11 | **ASKIDA:** dağıtım penceresi — Rol-1 (`043` sonrası suite'le); kimlik `[B-PULLBACK-SILAH]` → ✅ **KAPANDI 2026-08-31:** kod `ARMED_SETUPS`ta pullback'siz (ölçüldü) ve 08-30 `dcef1c6` + 08-31 `451c7ac` dağıtımlarıyla canlıda; kuyruk boşaldı, `[B-PULLBACK-SILAH]` kimliği kapandı |

#### A · §5 **KOVA 1 — ACİL** gövdesi (A1 `[B-KORUMA-KUR]` · A2 `[B-BILDIRIM-N1]`) — ikisi de KAPALI

**[B-KORUMA-KUR]** **A1 · KORUMA YENİDEN-KURULUMU — 4 POZİSYON ÇIPLAK** _(WP2; kaynak: `DENETIM-OLU-BILESEN-ENVANTERI:397-398`, `EDG-2026-038…yaml:142-149`)_
- **⚡ EMİR VERİLDİ (2026-08-17, operatör): "A1 korumayı şimdi kur."** Karar aşaması KAPANDI.
  Kalem açık kalmaya devam ediyor çünkü **icra edilmedi** — ve icrayı emrin verildiği oturum
  YAPAMAZ: o oturum bir cloud kabıdır, `.env`/Alpaca kimliği YOK, ve kimlik olsa bile canlı worker
  koşarken ikinci bir süreçten emir göndermek **CLAUDE.md §5'in yasakladığı çift-emir riskidir**
  (bu bir kapasite eksiği değil, emniyet sınırı). İcra A1'de, operatörün elinde.
  **ADIM LİSTESİ (koddan doğrulandı, ezberden değil — `api.py:4846/4992/5115`, `alpaca.py:969-972`):**
  (1) panoya SSH tünelinden bağlan; (2) **önce ÖLÇ** — `GET /api/alpaca/koruma_onerileri` çıplak
  motor pozisyonlarını ve bir `oneri_id` döndürür; (3) o `oneri_id`yi AYNEN al ve
  `POST /api/alpaca/koruma_kur` gövdesine `{"onay": "KORUMA-KUR", "oneri_id": "<o kimlik>"}`
  yaz (**jeton GÖVDEDE, sorguda DEĞİL** — sorgu dizesi log/geçmiş/`Referer`'a düşer ve oradaki bir
  yetki işareti yeniden oynatılabilir onaydır). (4) Jetonsuz çağrı **KURU KOŞUdur**: ne göndereceğini
  raporlar, hiçbir şeye dokunmaz — önce onu koşmak güvenlidir. (5) `oneri_id` eşleşmezse emir
  GİTMEZ (`koruma_onay_bayat` uyarısı) ve bu doğru davranıştır: ekrandaki liste onaydan sonra
  değiştiyse eski onay yeni listeye uygulanmaz — listeyi tazeleyip yeniden onayla.
  **DÖNEN CEVABI OKU:** `ok` yalnız TÜM öneriler gittiğinde True'dur; kısmi başarı "2/4 gönderildi
  + 2 neden" der ve "tamam" DEMEZ. Düşen her satır `koruma_oco_dusuru` uyarısı bırakır ve o
  pozisyon **HÂLÂ çıplaktır**.
- **ne bekleniyor:** NUE/EMR/BKNG/AMGN'in korumasının **şimdi** yeniden kurulması — panodan
  `koruma_kur` (üç kapı: ölçüm + operatör onay jetonu + öneri kimliği). Bu bir kod işi değil,
  operatörün tek oturumluk eylemi.
- **neden:** `submit_protective_oco`nun tek çağıranı `api.koruma_kur` ve o üç kapı ardında; bekçi
  çıplaklığı **GÖRÜP alarm üretiyor ama KURMUYOR**. Ölçülen kök: `day` TIF bracket'ları gece
  öldürüyor, yeniden kurulum elle.
- **beklerken bedel:** dört pozisyon da broker'da canlı koruyucu stop'suz; `korumasiz_motor_disi_pozisyon`
  son 7 günde **26 kez**, her biri için `MIRROR_DRIFT KORUMASIZ POZİSYON` 6 kez. Ölçülen korumasız
  duvar **56,4 saat**, seans-içi 2,895 sa (0,445 seans — eşiği AŞMADI). ⚠ **eşik kanıt değil,
  TOLERANS**: aşılmaması riskin yokluğu anlamına gelmez.
- **bağımlı kalemler:** A2 (alarm bu kanaldan geçecek) · B2 (kalıcı politika kararı) · WP2 SB-2
  `drift_sinifi` · §3 GÜNCEL DURUM'un doğruluğu (2026-08-13'te düzeltildi).

**[B-BILDIRIM-N1]** **A2 · BİLDİRİM KANALI (N1) — ARTIK ÖN-ŞARTSIZ** _(§5-2; kaynak: OB-2 kapanışı + `docs/GECE-RAPORU-2026-08-13.md:86`)_

> ✅ **KAPANDI (2026-08-22): Telegram canlı, test teslim edildi.** Token operatörden (panodan), chat_id sunucu tarafından (token Claude'a hiç inmeden), yazım panonun kendi API'siyle. `B2`(c) bu an itibarıyla TESLİM EDEN politika. Aşağıdaki metin tarihçe.
- **ne bekleniyor:** Telegram/webhook kimliği (`TELEGRAM_*` ya da `MERIDIAN_WEBHOOK_URL`) —
  teslim zinciri hazır (`obs.alarm → notify.send`), kanal boş. Ayarlar ekranı ya da ortam değişkeni.
- **neden:** tek ön-şartı olan systemd `SuccessExitStatus=143` (OB-2) 2026-08-09'da kapandı — artık
  temiz-durdurma "FAILED" sayılmıyor, kanal açılınca yanlış-alarm boğmayacak. **Sıranın başı ve en
  ucuz kalem** (denetim D8/F6).
- **beklerken bedel:** alarmlar yalnız panoda birikiyor — **29 alarm teslim edilemedi** (§3 GÜNCEL
  DURUM, 2026-08-13; `GECE-RAPORU:86` aynı gün için 12 teslim edilmemiş sayıyor — iki sayım farklı
  pencereden, ikisi de teslimatsızlığı söylüyor). "Alarm öttü, kimse duymadı" sınıfı sürüyor.
- **bağımlı kalemler:** A1'in çıplaklık alarmı · bakım penceresi sırası (aşağıdaki F8 sırası:
  **OB-1 kanal → equity_curve/`seed_boundary` onarımı → OB-4 restart→PBO damgalama**).

#### B · §5 **KOVA 2 — KARAR BEKLEYEN** gövdesi (B1/B2/B4/B3) — dördü de KAPALI

**[B-PULLBACK-SILAH]** **B1 · PULLBACK SİLAHSIZLANMASI** _(WP11-B; kart EDG-2026-039 — ölçüldü, operatör 2026-08-13: "önce diğer işler, bu beklesin")_

> ✅ **KARAR VERİLDİ (operatör, 2026-08-22): A — SİLAHSIZLANDIRILDI.** Karar günü ölçümü: cf 21→29 (−0,885R), 13-22 Ağu canlı işlem 0. Yeniden-silahlanma kapısı DONUK (cf n≥30 ∧ CI-alt>0 → kart-önce). Dağıtım: 043 koşumu bitince otoriter suite ile birlikte. Aşağıdaki metin tarihçe.
- **ne bekleniyor:** pullback ailesinin `ARMED_SETUPS`ten çıkarılıp çıkarılmayacağı kararı
  (+ çıkarılırsa yeniden-silahlanma eşiğinin yazılması: cf'de `n≥30` ∧ ort-R CI-alt > 0).
- **neden:** **strateji kimliği değişikliğidir** (denetim F3) — sistemin ne alıp sattığını değiştirir,
  bu yüzden §4 backlog'da değil §5'te bekler. Hüküm: "silahsızlanma ÖNERİLİR ama gerekçe *çıkarmak
  kazandırıyor* DEĞİL, **KANIT ASİMETRİSİ**" — ΔP&L +3.121$ (CI 0-içi), işlem n SABİT (885→885);
  pullback'in kendi zararı üç kaynakta tutarlı (replay n=6 kazanma %0,0 · canlı n=4 −1,00R · cf n=21
  −0,97R). ZAYIFLIK: sonuç tek işleme bağlı (IRM/hammer +2.247$).
- **beklerken bedel:** her seans slot + ısı + sermaye — ve bağlayıcı kısıt ISI olduğu için
  (`EDG-039:63-64`) bu bedel doğrudan başka bir adayın yerini yiyor.
- **bağımlı kalemler:** WP11-B ARSENAL POLİTİKASI (giriş/çıkış ortak çıtası) · WP11-D uzlaştırma.

**[B-KORUMA-POLITIKA]** **B2 · KORUMA YENİDEN-KURULUMU OTOMATİKLEŞSİN Mİ (kalıcı politika) — ✅ KARAR VERİLDİ: (c)** _(WP2-B; denetim F2)_
- **⚡ OPERATÖR KARARI (2026-08-17): seçenek (c).** Yani `koruma_kur`un ÜÇ KAPISI (ölçüm + onay
  jetonu + öneri kimliği) **KALIR**; (a) tam otomatik ve (b) ölçüm-kapısız REDDEDİLDİ. Sermaye
  yüzeyine dokunan bir eylem, ölçülmüş bir listeye ve tura-özel bir onaya bağlı kalmaya devam eder.
- **KOD İŞİ GEREKMEDİ — (c)'nin ikinci yarısı ZATEN YÜRÜRLÜKTEYDİ, ve bu ölçüldü:** "çıplaklık
  alarmı bildirim kanalına bağlansın" şartı bugün sağlanıyor — alarm kendi jetonunu taşıyor
  (`obs.ALARM_NAKED_POSITION`; `watchdog.py:2836/2849`, v209'un `MIRROR_DRIFT` ödüncü bitti),
  `NOTIFY_TOKENS` bir **türetmedir** (`obs.py:138`) yani jeton eklendiği an teslim kapsamındadır,
  ve zincir `obs.alarm → _maybe_notify → notify.send` işliyor. Çiviler: `v216:85` · **`v216:130-141`
  ((c)'nin asıl güvencesi: MIRROR_DRIFT susturma penceresi kurulduktan sonra bile NAKED_POSITION
  TESLİM EDİLİR — muhasebe gürültüsü sermaye riskini susturamaz)** · `v209:248`.
- **BU YÜZDEN (c) BUGÜN YARIM BİR POLİTİKADIR ve yarısı `A2`dir:** kanal kimliği (`TELEGRAM_*` ya da
  `MERIDIAN_WEBHOOK_URL`) girilene dek `notify.configured()` False döner, alarm yazılır ama
  TESLİM EDİLMEZ ve yalnız `notify_undelivered.json` sayacı artar. (c) seçilerek A2 "en ucuz kalem"
  olmaktan çıkıp **seçilmiş politikanın teslim bacağı** oldu — sıra önceliği buna göre yükseltildi.
- **eski karar metni (tarihçe — SİLİNMEDİ):** üç seçenekten biri — **(a)** tam otomatik
  yeniden-kurulum · **(b)** onay-jetonlu ama ölçüm-kapısız · **(c)** mevcut üç kapı kalsın +
  çıplaklık alarmı bildirim kanalına bağlansın.
- **neden:** yön **risk-AZALTAN** ve `api.py`nin kendi şerhi bu sınıfı onaya bağlamamayı savunuyor;
  ama koruma kurmak sermaye yüzeyine dokunur → politika kararı operatörün.
- **beklerken bedel:** A1 her `day`-TIF gecesinden sonra ELLE tekrarlanır; iki gecede bir aynı
  operatör eylemi. (Ölçülen seans-içi çıplaklık eşiği aşmadı — ama tolerans, kanıt değil.)
- **bağımlı kalemler:** A1 (acil eylem) · A2 (c seçeneği kanalı ŞART koşar).

**[B-E1-LIMIT]** **B4 · E1 LİMİT BACAĞI — CANLIDA AÇILSIN MI** _(WP1; kart `EXE-2026-006` — ölçüldü 2026-08-17, hüküm: E1 YENİDEN AÇILIR)_

> ✅ **KARAR VERİLDİ (operatör, 2026-08-22): A+C — KAPALI KALIR.** Gerekçe yeniden temellendirildi (ölçüm: açmak taban altında, kurtarılanlar ~0R, deltalar anlamsız, model boşluğu −8,4k). Açık kalan tek argüman `EDG-2026-043`e (`Ö-55`) döküldü; hüküm EDG-042 bandıyla iki kaynaklı okunacak. `D5` park. Aşağıdaki metin TARİHÇE olarak korunur.
- **ne bekleniyor:** `state/goal.yaml` `execution_v2`de bacağı fiilen ÖLÜ bırakan iki değerin
  (`limit_pct_cap=0,04` · `limit_atr_mult=100,0`) değiştirilip değiştirilmeyeceği kararı — **ama
  ÖNCE iki ön-koşul** (`Ö-51b` Ö1'in kimlikli tanımı · `Ö-51c` ΔP&L bootstrap CI'ı). Kart bir değer
  ÖNERMEZ ve önermemesi bilinçlidir.
- **neden:** bacağın kapalı olmasının gerekçesi E1'in "limit bacağı MONOTON zararlı · kaçanlar
  sistematik KAZANAN" hükmüydü. `EXE-2026-006` o hükmü düzeltilmiş dolum kuralıyla sınadı:
  **monotonluk ayağı DÜŞTÜ** (tepe 0,01'de, sonra azalıyor) ve **işaret ayağı ÖLÇÜLEMEDİ** (dört
  tavanda da CI sıfırı içeriyor). Yani hüküm ÇÜRÜTÜLMEDİ ama **DOĞRULANMADI da** — canlı
  yapılandırma bugün KANITSIZ bir gerekçeye yaslanıyor. Kartın ölçümden ÖNCE yazdığı asimetri
  beyanı burada bağlıyor: *"hüküm düştü" sonucu canlıda para bırakıyor olabileceğimiz anlamına
  gelir* — iki sonucun bedeli EŞİT DEĞİL.
- **beklerken bedel:** ÖLÇÜLEN YÖN pozitif ama CI'sız — dar tavanlı ölçüm kolunda ΔP&L dört
  tavanda da POZİTİF (+146 / +7.163 / +5.759 / +7.355$). ⚠ **BU BİR KÂR VAADİ DEĞİL:** (a) CI
  koşulmadı, (b) `max_chase` kırpması yüzünden hüküm bir ALT SINIRDIR, (c) yan kanal büyük
  (154 işlem yerinden oldu) ve ölçüm dar tavanda koştu — canlı yasa geniş tavanda. Bedel
  "kaçırılan X dolar" diye YAZILAMAZ; yazılabilecek olan şudur: **karar verilene dek bacak,
  gerekçesi çürümüş bir yapılandırmayla ölü duruyor.**
- **bağımlı kalemler:** `Ö-51b` + `Ö-51c` (ÖN-KOŞUL, ikisi de H1) · `Ö-51d` (`EXE-2026-005` Rol-1
  hükmü + K kaydı) · WP1-B 23c limit-tavanı kararı (D5: "kapanmadan limit-tavanı kararı YOK") ·
  `EDG-2026-037/038` friksiyon hükmü (bacak açılırsa işlem sayısı artar → friksiyon emilimi de artar,
  ve mutlak P&L iddiaları friksiyona ASILI).

**[B-FAZ6-HUKUM]** **B3 · FAZ-6 `sonuc_hukmu` YAPISAL KAPALILIĞI — ⚠ KARAR DEĞİL, BİLGİ** _(WP5-E/20b; denetim A14/F4)_
- **ne bekleniyor:** **hiçbir şey — operatörden karar İSTENMİYOR.** Bu satır yalnız bilgilendirme
  olarak §5'te duruyor, çünkü daha önce "KARAR GEREKİR" diye kayıtlıydı ve o kayıt artık yanlış.
- **neden:** karar **ölçümle verildi**: `EDG-2026-037:65` "EŞİK TARTIŞMASI KAPANDI —
  `RESULT_PF_MIN=1.3` GEVŞETİLMEZ"; `:66-67` "PF ek friksiyonda monoton azalandır: **1,1119 hiçbir
  friksiyon varsayımıyla YÜKSELEMEZ**"; `EDG-2026-038:155-159` hükmü güçlendiriyor.
- **operatöre giden tek cümle:** *"Faz-6 `sonuc_hukmu` bu paketle **yapısal olarak açılamaz** ve bu
  bir **KORUMA, arıza değil**; açılmasının yolu eşiği gevşetmek değil **icra friksiyonunu ölçüp
  düşürmektir** (WP1-B)."*
- **bağımlı kalemler:** WP1-B (23c K1 → limit kararları) · §6 kart indeksindeki friksiyon şerhi turu.

### §8.H — HAVUZ ARŞİVİ (2026-08-30; `§4 ÖNERİ HAVUZU`ndan taşınan KAPALI öneriler)

`§4`'ün kendi kuralı: kapanan öneri havuzda kalmaz. Bu üçünün hükmü 2026-08-23/24'te
inmişti ama gövdeleri havuzda duruyordu. Metin **AYNEN**; havuzda tek satırlık iz kaldı.

#### A · §4 `Ö-45` — `EDG-2026-048` NO-GO tüketiciyi kapattı (2026-08-23)

- ~~**🔴 45. 28d TEŞHİSİ — EŞİK DÜŞÜRMEK BU TIKANIKLIĞI AÇMAZ**~~ _(2026-08-14, v247-B ölçtü; **planı DEĞİŞTİRİR**)_ ~~**[KART ADAYI — 2026-08-23]**~~ **[2026-08-24 KAPANDI-BAYAT: Ö-45'in istediği ölçümün ("sınıflayıcının chop tanımını ölçmek — kart-önce") KARAR-TÜKETİCİSİ kapandı — `EDG-2026-048-chop-tabani` (kart 2026-08-23 ön-kayıtlı, aynı gün ölçüldü, `status: measured`) hükmü **NO-GO / ölçülmüş ret**: Δ(taban60−taban45) = −18.266$, CI95 [−47.734, +10.589]; chop açılımı 417 chop işlemi ile −26,3R üretti VE +22,6R'lik 99 chop-dışı işlemi yerinden etti, yani "sınıflayıcı hiç chop üretmiyor" endişesi de pencere-bağımlıydı (chop VAR, para etmiyor). Hüküm metni: "@chop hipotez üretiminin duraklatılması (K1 paketi) daha da gerekçeli — 28d kapısının @chop dilimi kapanır; canlanma yalnız yeni dünya/yeni kartla." Sınıflayıcı tanımını ölçmek artık SAHİPSİZ bir ölçüm olurdu. Tek kalıntı NOT olarak düşülür (kalemi açık tutmaz): az-tespitin RİSK tarafı (gerçek chop'ta bütçe kısılamaması) AYRI ve bugün kanıtsız bir sorudur — istenirse YENİ ve kendi gerekçeli kalem, Ö-45'in metni onu içermiyor. Belge: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §B1]**
  ROADMAP 28d'yi "kapı ölçemiyor, `chop` dilimi 27 < eşik 30" diye taşıyordu ve örtük çözüm eşikti.
  **ÖLÇÜM ÜÇ ŞIKKI AYRIŞTIRDI:** pencere dar mı → **HAYIR** (OOS 850 gün) · fold geometrisi mi →
  **HAYIR** (eşik `score_detail`te dilimin TAMAMINA biner) · **sınıflayıcı seyrek mi → EVET,
  BELİRLEYİCİ**: `chop` OOS'un **%4,7'si** (27/572) ve **zamanda kümelenmiş**.
  Fold kırılımı: fold1 8/189 · fold2 19/128 · **fold3 0/255**. **27 chop'un 26'sı arama diliminde,
  TEYİTTE SIFIR.** 2025-07-01'den sonraki **394 günde hiç chop yok**.
  **KİLİT SONUÇ:** teyit tabanı `max(10, …)` yüzünden **10'un altına inmez** ve chop'un teyit dilimi
  **0 işlem**. Yani `min_sample` 30→10 olsa **bile** @chop teyitte ölçülemez → **eşik düşürmek bu
  tıkanıklığı AÇMAZ.** Eşik tartışması bu kalem için **konusuz**.
  **SIRA ÖLÇÜMLE DOĞRULANDI:** 28f'ten ÖNCE eşik düşürülseydi @chop adayları **teyitsiz** ship
  edilebilirdi (H00029 sınıfı). 28f sonrası dürüstçe engelleniyor — ROADMAP'in `28a > 28d` sırası
  doğruymuş, ama gerekçesi sanılandan farklı.
  **GERÇEK KALEM ARTIK BU:** `chop` rejimi bir yıldır oluşmuyor. Bu bir kapı arızası değil, **rejim
  sınıflayıcısının ya da piyasanın** gerçeği. Doğru soru: sınıflayıcı fazla mı dar (kalibrasyon) ·
  yoksa gerçekten chop yok mu (o zaman @chop öğrenmesi **yapısal olarak beklemede**). *öncelik:
  yüksek · gerekli iş: sınıflayıcının chop tanımını ölçmek — kart-önce.*

#### B · §4 `Ö-47` — holdout kuyruğu WP5-A `2D` ile BİRLEŞTİRİLDİ (2026-08-24)

- ~~**🆕 47. 28i — SAPMA TEK FOLD'DAN GELMİYOR, GELEMEZ**~~ _(2026-08-14, v247-B ölçtü)_ ~~**[KART ADAYI — 2026-08-23]**~~ **[2026-08-24 KAPANDI-BAYAT: kalemin iki yarısı da kapandı. ① ARTIK-FOLD OYLAMASI YAPISAL OLARAK KAPALI — kapı fold'ları artık N-DENGELİ kesiliyor (`reflect.py:411-430` sınırları incumbent Search-OOS işlem damgalarından türetir), `backtest.py` `FOLD_MIN_N = 15` SERT TABAN ("n<15 pencere oy kullanamaz"), `FOLD_K_TRY (3,2)`, taban tutmazsa takvime dönüş ADIYLA görünür, `fold_total == 1 → majority UNPROVABLE` yasası yerinde; CANLIDA ÖLÇÜLDÜ: kapı kayıtlarında `fold_law` = **23 × n_dengeli · 3 × n_dengeli_taban_tutmadi · 0 × takvim** → 38-günlük artık dilim kapı oylamasına ARTIK GİREMEZ (takvim fold'ları yalnız rapor katmanında, bilerek — önbellek anahtarı korunur). ② 91-GÜNLÜK HOLDOUT hüküm-dışıdır TASARIMLA ("holdout never drives acceptance", `reflect.py:1446`, `backtest.py:735-736,937`); sapma yalnız `overfit_suspect` bayrağı üretir (`HOLDOUT_DIVERGENCE = 0.10`) — hükümsüz bir rapor penceresinin "meşruiyeti" uzunluk sorusudur. HOLDOUT KUYRUĞU BİRLEŞTİRİLDİ → WP5-A "2D R2 holdout rotasyonu": pencerenin uzunluğu/rotasyonu zaten ORADA sahipli (`dataset.py` R1 bloğu + rotasyon disiplini yazılı); ikinci bir kart açmak ÇİFT-KAYIT olurdu. Belge: `docs/ELEME-WP4-HAVUZ-2026-08-23.md` §B2]**
  Arama fold'ları: fold1 **274 gün** · fold2 **263** · fold3 **38**. fold3 bir tasarım penceresi
  DEĞİL, takvim sınırı (2025-07-01) ile %70 kesimi (2025-08-18) arasında kalan **ARTIK** — tam
  fold3'ün %13'ü.
  Canlı: kapı `n=36, avg_r=−0,2223` oyluyor; **aynı dönem** tam uzunlukta `n=249, avg_r=+0,2140`.
  **Aynı dönem, iki zıt işaret, tek fark pencere uzunluğu.**
  **"Sapma tek fold'dan mı?" → HAYIR, GELEMEZ:** holdout bir fold DEĞİL, OOS'un tamamen dışında
  ayrı **91 günlük** pencere. Fold'lar OOS'un içindedir ve holdout skoruna hiç girmezler. 0,772'lik
  sapma, o 91 günlük kısa pencerenin **kendi getirisidir**. *gerekli iş: artık-fold ve 91 günlük
  holdout penceresinin meşruiyeti — kart-önce.*

#### C · §4 `Ö-39` — KAPANDI 2026-08-24 (`af8ca11`, `state/plan_atif.jsonl`)

- **🟢 39. KALİBRASYON "HANGİ BEYİN NE KADAR İSABETLİ" — KAPANDI (2026-08-24, `af8ca11`)**
  **ÇÖZÜM:** append-only `state/plan_atif.jsonl`. Yazar `hermes._plan_atif_yaz` (damgalanan HER
  plan bir satır, YASA 4 işaretli); künyeyi ÇAĞIRAN verir (`_stamp_llm_opinions(..., kunye=)`) —
  damga kendi okusaydı iki çağıran birbirinin künyesini boşaltırdı. `backfill_opinions` künyeyi
  eskiden HİÇ okumuyordu; Ö-39'un canlı kanıtı oradan çıkmıştı. Tüketici İLK GÜNDEN var
  (`analytics.llm_opinion_calibration()["model_kirilim"]`, YASA 6) ve `ledgers.CONTRACTS`
  kaydı düşüldü. Doğrulama: `artifact_graph` → writers `[hermes.py]` · external_readers
  `[analytics.py]` · unread False; `ledgers.report()` ok=True. Künye ailesinin (31a·31b·40·39)
  SON bacağıydı — aile kapandı. GÖVDE AŞAĞIDA SİLİNMEDİ (tarihçe-koru).
  _(eski başlık: 🔴 … YAPISAL — 2026-08-14, v246-B ölçtü)_ **[2026-08-23 Rol-1 SINIFLANDIRMA: WP7'ye SINIFLANDI — künye ailesi WP7'de; iş ölçüm değil YOL kararı (candidate_review analytics'te 0); kaynak: docs/RAPOR-HAVUZ-SINIFLANDIRMA-2026-08-23.md; gövde SİLİNMEDİ]**
  `analytics.llm_opinion_calibration` çiftleri `trade_plans.llm_opinion` + işlem defteri join'inden
  kuruyor ve **model künyesini hiç okumuyor** (`grep -c candidate_review analytics.py` = **0** —
  v245'te benim ters yöndeki iddiam da böyle çürümüştü). Sorun künyeyi okumaması değil,
  **kaydedilmiş bir künye OLMAMASI**:
  · `llm_opinion`ı yazan tek yer `hermes._stamp_llm_opinions`; satıra **TEK anahtar** yazabiliyor ve
    bu **YAZILI YASA** (`test_authority_boundaries_v77::test_c3`: `degisen == {"llm_opinion"}`)
  · plan satırlarında model/beyin adı **yok** (ölçüm: damgalı 4 satırın 0'ında)
  · olaylar da taşımıyor (`llm_opinions_stamped` alanları ts/event/level/date/n)
  · `candidate_review.json` v245'ten beri cevap vereni taşıyor ama **tek-belge** deposu (`doc.clear()`)
    — yalnız son gün
  · tek kalıcı model defteri `agent_calls.jsonl`, ama satırında **ticker ve plan günü yok** ve
    `backfill_opinions` bugünkü çağrıyla **aylar öncesine** damga vuruyor → zaman-yakınlığı join'i
    **yapısal olarak yanlış**
  **DOĞRUDAN SONUCU:** bu gecenin **ultra→super** değişiminin etkisi bu kanalda **ÖLÇÜLEMEZ**;
  öncesi/sonrası çiftler aynı taze pencerede ayrıştırılamadan karışır. Yani "model değişikliği
  işe yaradı mı" sorusunun bugün bir cevap yolu YOK.
  **NEDEN ROL-1'DE:** ucuz ve sözleşme-kırmayan yol yok. Plan satırına ikinci alan yazmak
  **yetki-sınırı yasasını değiştirmeyi** gerektirir; ayrı bir atıf defteri yasayı kırmaz ama
  `ledgers.CONTRACTS` kaydı + kalibrasyon tarafında tüketici ister.
  Ölçüm `tests/test_zincir_kunye_v246.py::test_n1` ile **donduruldu** (kapı kapatmıyor, ölçümün
  bayatlamasını engelliyor). *öncelik: yüksek — model seçimi bir kaldıraç ve bugün geri-besleme yok.*
  **[2026-08-24 TASARIM-KAPANIŞI: YOL (b) — AYRI ATIF DEFTERİ seçilir; yasa KORUNUR** (plan satırında
  `llm_opinion` TEK anahtar kalır, `test_authority_boundaries_v77::test_c3` kırılmaz). Kusur bugün de
  canlıda görünür ve soru artık akademik değil: 08-16'da `backfill_opinions` **2026-02-26 ve
  2026-04-14 tarihli planlara** damga vurdu (`llm_opinions_stamped` date=2026-02-26 n=1 ·
  date=2026-04-14 n=2) — "bugünkü çağrıyla aylar öncesine damga", §4-39'un tarif ettiği yapısal
  yanlışın ta kendisi; terfi 08-14'te açıldığı için YETKİLİ danışmanın hangi model olduğu kalıcı
  hiçbir defterde yok. Taslak: yeni append-only defter **`state/plan_atif.jsonl`**, satır
  `{ts, plan_id, ticker, plan_date, kind, model, model_istenen, model_kaynagi, iz_id, backfill:bool}`
  — `iz_id` `agent_calls.jsonl` join anahtarı, `backfill=true` damgası zaman-yakınlık join'ini
  YAPISAL olarak düzeltir (geriye-damga artık kendini beyan eder); yazan TEK yer
  `hermes._stamp_llm_opinions` + `backfill_opinions` (aynı çağrı içinde, kilitli); `ledgers.CONTRACTS`
  kaydı + tüketici İLK GÜNDEN (`analytics.llm_opinion_calibration` kovalarına model-kırılımı) —
  uyuyan-yol dersi: **okuyucusuz defter açılmaz**; ölçüm çapası hazır
  (`tests/test_zincir_kunye_v246.py::test_n1` donduruyor, yeni defterin kapsam testi aynı dosyaya
  eklenir). **AYNI TURA KATLANACAK KÜNYE AİLESİ:** WP7-31a (`hermes.py:3987` tek satır
  `cevap_veren_model()`) · WP7-31b (`active_model()` uydurma koruması) · WP7-40 (`nous_eval` künye
  alanları, XS) — dört kalem tek "künye turu" olarak kapanır. Kalan mini-iş hafta-1 partisinde.
  Belge: `docs/ELEME-WP7-2026-08-23.md` §6.**]**
