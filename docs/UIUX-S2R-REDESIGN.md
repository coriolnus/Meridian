# S2R — Pano YENİDEN TASARIMI (ADR + hedef IA) — 2026-08-02, operatör talebi

## Karar (ADR)
Operatör geri bildirimi: kademeli-giydirme birikimi panoyu DAHA karmaşık hissettirdi; beklenti
baştan tasarımdı. KARAR: iş emrinin (docs/UIUX-WORKORDER.md §3) hedef IA'sı ŞİMDİ kurulur —
"redesign replaces": eski yerleşim referans değil, kanıt; yeni dünya iş emrinin cam-kokpit tezi.
SINIRLAR: (a) motor korunur — vanilla JS + RENDER kaydı + CSP-self + kaynak-çivili test rejimi
(stack göçü DEĞİL, ADR'siz zaten yasak); (b) YASA-6 KORUNUMU — bugün panoda okunan her API/tablo
alanı yeni IA'da bir eve taşınır YA DA bilinçli-gerekçeli emekli edilir (öksüz tablo = kırmızı);
(c) veri semantiğine/eşiklere sıfır dokunuş.

## Hedef IA (12 görünüm → 1+6+detay)
- **GENEL BAKIŞ (Overview — J1'in evi, TEK EKRAN KAYDIRMASIZ):** Sessiz-Hat (zaten global) ·
  "dün gece ne oldu" tek paragraf-blok (son döngü: seans/aday/plan/silahlı) · sermaye-köken kartı ·
  bugün-ne-var (silahlı planlar / bekleyen onaylar sayacı) · alarm-bütçesi tek satır · 3 mini-trend
  (equity+DD, karne, kapsama) — HEPSİ özet; her kartın "→ alan sayfası" tek bağı. ~~BAŞKA HİÇBİR ŞEY.~~

  > **AŞILDI — 2026-08-24, `docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md` (operatör onaylı maket).**
  > İki hüküm düştü, biri KALDI.
  >
  > **DÜŞEN 1 — "BAŞKA HİÇBİR ŞEY".** Bugün yüzeyi artık metrik sekmeleri, çok serili alan
  > grafiği, birleşik akış kartı (zincir ↔ huni), alan satırları, **bir** kanıt tablosu (açık
  > pozisyonlar, seviye-işaretli kıvılcımlarla) ve Top Views taşıyor. Gerekçe: S2R'nin
  > "her şey özet, detay alan sayfasında" modeli tarama derinliğini üç tıklamaya gömüyordu;
  > devralınan Dub dili tam tersini yapar — tek yüzeyde zaman serisi + toplulaştırma +
  > (istenirse) olay akışı, filtreler görünümler arasında taşınarak.
  >
  > **DÜŞEN 2 — "TEK EKRAN KAYDIRMASIZ".** Yeni yüzey kaydırılır ve bu BİLİNÇLİDİR. Tek-ekran
  > kısıtı, ölçülmemiş bir ergonomi iddiasıydı ve bedeli ölçülebilirdi: her ek bilgi bir alan
  > sayfasına sürülüyordu. Operatör kaydırmayı seçti.
  >
  > **KALAN — sınırsız detay dökümü hâlâ YASAK.** Aşma sınırlıdır ve `test_s2r1_kabuk_v155`
  > tarafından ÖLÇÜLÜR: jenerik detay satırı (`trow`) sıfır · en fazla BİR `<table` ve o da
  > açık pozisyonlar kanıt tablosu (paydası maruziyet bütçesiyle sınırlı, bir sorgu sonucu
  > DEĞİL) · eski kart grameri (`class="card`) geri gelemez. Yani ADR'nin korktuğu şey
  > (sayfanın sınırsız bir tabloya dönüşmesi) hâlâ kırmızıya döner — yalnız eşik, "sıfır
  > tablo"dan "bir sınırlı tablo"ya taşındı.
- **VERİ SAĞLIĞI:** kapsama/tazelik/karantina/bütünlük + intraday akış durumu (eski market-sağlık +
  intraday-veri parçaları buraya).
- **KOŞU & DÖNGÜ:** günlük döngü karnesi, koşu şelalesi, onarım geçidi, seans işleme geçmişi.
- **PORTFÖY & EMİRLER:** pozisyonlar, silahlı planlar, dolum akışı/mutabakat, sermaye detayı,
  reddedilen emirler (eski bugün+intraday'ın emir yarısı).
- **ÖĞRENME:** karne, gölge kollar (küçük-katlar hedefi), bileşen-IC+EB, hipotez/sprint, K-defteri
  (eski ogrenme+ajan+hermes+skiller+hafiza+performans BİRLEŞİR — en büyük sadeleşme burada).
- **GÖZETİM & ALARMLAR:** alarm gelen kutusu (runbook bağlı), bekçi ayrıntıları, alarm-bütçesi
  detayı, olay günlüğü (eski operasyon'un gözetim yarısı).
- **KİLİTLER & YAPILANDIRMA:** kilit paneli (pozitif çerçeve), bayraklar, ayarlar, tema/yoğunluk
  (eski ayarlar + operasyon'un müdahale kolları — müdahale ⌘K'da da yaşar).
- **Detay katmanı (istek-üzerine):** bir koşu / bir işlem / bir hipotez — alan sayfalarından bağla.
- landing/workflow/runbook bağımsız sayfalar olarak kalır. `brifing`/`adaylar`/`kararlar`
  içerikleri: kararlar→Portföy&Emirler(onay kuyruğu)+Gözetim; adaylar→Koşu&Döngü; brifing→Overview
  "dün gece" bloğunun kaynağı.
- Navigasyon: kalıcı SOL RAY (7 madde, ikon+etiket), Sessiz-Hat her sayfada sabit üstte;
  g-kısayolları+palet yeni haritaya güncellenir.

## "Ekrana dök" yasağı uygulaması
Her alan sayfası başındaki soru-cümlesi ARTIK SÖZLEŞMEDİR: sayfadaki her kart o soruya hizmet
etmeli; etmeyen kart taşınır/emekli edilir. Emekli edilen her görsel bileşen için: okuyucu-kaydı
kontrolü (codelaw) + karar notu (bu dosyanın Ek'ine işlenir).

## Uygulama planı (gece, kademeli — her adım ayrı commit + testli)
- **S2R-1:** kabuk — sol ray + 7-sayfa iskeleti + yönlendirme (eski görünümler geçici olarak yeni
  evlerine ALIAS'lanır; hiçbir içerik kaybolmaz) + Overview v1 (yukarıdaki kompozisyon, mevcut
  bileşenlerin ÖZETLENMİŞ kartları).
- **S2R-2:** içerik göçü — eski 12 görünümün kartları yeni evlerine taşınır; Öğrenme birleşimi;
  kart-başına "soruya hizmet" denetimi; emekli listesi.
- **S2R-3:** cila — yoğunluk/boşluk ritmi, kart hiyerarşisi, palet/g-kısayol/CSP/test güncellemesi;
  kontrast yeniden-doğrulama; ekran görüntüsüyle operatör onayına sunum.
Testler: mevcut kaynak-çiviler taşınan seçicilerle güncellenir; YASA-6 okuyucu haritası
test_edge_dashboard/test_pano_* ailesinde yeni IA'ya çekilir; her aşamada tam grep.

## Geri-dönüş
Her aşama ayrı commit; eski görünüm fonksiyonları S2R-2 sonuna dek silinmez (alias) — tek
`git revert` ile dönüş mümkün. Operatör sabah beğenmezse: revert maliyeti dakikalar.

---

# Ek A — S2R-2 göç haritası (2026-08-02, uygulandı)

Yedi sayfa, **yirmi bölüm**. Sıra = sayfadaki okuma sırası ve "en kritik üstte" kuralının
ölçülebilir hâli (`app.js` → `ALAN_BOLUMLERI`, `index.html` kap dizilimi, `test_s2r2_goc_v156`
üçü birden çivili).

| Sayfa | Bölümler (sırayla) | Kaynağı |
|---|---|---|
| **Genel Bakış** | *(kendi render'ı — altı kart + alarm satırı)* | S2R-1 |
| **Veri Sağlığı** | market · intraday · **veriboru** | intraday BÖLÜNDÜ (akış yarısı); veriboru = eski Operasyon'un Bölüm 4+5+6 + sağlayıcı sağlığı + Faz-4a gözlem özeti |
| **Koşu & Döngü** | adaylar · **kapilar** | onaylar ÇIKTI (→Portföy); kapilar = eski Operasyon Bölüm 2 |
| **Portföy & Emirler** | brifing · **onaylar** · **mutabakat** · **intraemir** · performans | onaylar Koşu'dan geldi; mutabakat = eski Operasyon Bölüm 1; intraemir = intraday'in emir yarısı; brifing'den alarm kutusu + olay akışı ÇIKTI (→Gözetim); performans'ın karne yarısı ÇIKTI (→Öğrenme) |
| **Öğrenme** | **karne** · **golge** · **bilesenic** · hermes · ajan · skiller · hafiza | karne = öğrenme karnesi + performans kırılımları + kalibrasyon + **Hermes karnesi (MAE, gölge-varyant)** + **sistem önerileri**; golge = trend kolu canlı gölge-kitabı; bilesenic = edge beş ölçüt + bileşen IC/EB + dolar merceği + kâr şelalesi + doğrulama üçlüsü + Y3; hermes'e MLOps (Bölüm 3) + öğrenme çarkı eklendi |
| **Gözetim & Alarmlar** | operasyon | kapsam DARALDI: alarm bütçesi + gelen kutusu + kadans nabzı/bekçi notu + olay günlüğü |
| **Kilitler & Yapılandırma** | **mudahale** · ayarlar | mudahale = dört kademe (üst bar kapağı ve ⌘K KALIR); ayarlar'a dışa aktarım kutusu eklendi (Öğrenme'den) |

**Bölünen üç görünüm.** `onaylar` kabı `#page-adaylar`ın içinden çıkarıldı ve alias'ı Portföy'e
alındı. `intraday` ikiye ayrıldı: `intraParcalar()` beş kart üretir, akış yarısı (s3+s4) Veri'de,
emir/silahlama yarısı (s1+s2+s5) Portföy'de yazılır. `operasyon` on dokuz parçaya ayrıldı:
`opParcalar()` tek hesapla saf bir HTML sözlüğü döndürür, altı sayfa bölümü yalnız kendi
anahtarlarını yazar. Alt-render zincirleri (`brifing→performans`, `adaylar→onaylar`,
`ajan→hermes+skiller+hafiza`) söküldü — sırayı artık yalnız `ALAN_BOLUMLERI` söyler.

**Korunan iki bitişiklik.** Göç, anlam taşıyan iki komşuluğu BİRLİKTE taşıdı ve testleri
onlarla birlikte güncellendi: `sEdge`→`sSonuc` (EDGE hükmü ile dolar merceği ikizdir; okunma
yeri yan yanadır, v119) ve `sHermes`→`sNous` (karne "beyin PARAMETRE tahminlerinde ne kadar
isabetli?", sistem önerileri bir üst katman "beyin MEKANİZMALAR hakkında ne görüyor?" — v131).
İkincisi `karne` bölümüne birlikte indi. Bunun bedeli: gölge-**varyant** portföyleri Hermes
karnesi kartının bir alt başlığı olduğu için `golge` bölümüne alınamadı; `golge` bu turda tek
kart (trend kolu canlı gölge-kitabı) taşıyor ve altyazısı ötekinin nerede olduğunu SÖYLÜYOR.
Kart gövdesini ikiye bölmek S2R-3'ün (cila) işi.

**Alias sözleşmesi daraldı.** `ROUTE_ALIAS` bir *eski-hash* sözlüğüdür ve on iki eski görünüm
adıyla sınırlı kalır. S2R-2'nin sekiz yeni bölümü (mutabakat, kapilar, veriboru, intraemir,
karne, golge, bilesenic, mudahale) alias ALMAZ — hiçbiri bir eski yer imi değil; çapaları
`<sayfa>#<bölüm>` biçiminde çalışır (bölüm başlığı `id="<bölüm>"` taşır).

## Ek B — emekli / detay katmanına indirilenler (YASA-6 gerekçeleri)

Emeklilik kuralı: bölümün okuduğu API/tablo alanlarının **tek okuyucusu** o bölümse blok
SİLİNMEZ; varsayılan-kapalı `<details>`e (detay katmanı) iner ve gerekçesi hem ekranda hem
burada yazılır. **Hiçbir tablo öksüz bırakılmadı; hiçbir uç düşmedi** (ölçüm: göç öncesi HEAD ile
göç sonrası app.js karşılaştırıldı — kaybolan uç 0, kaybolan alan okuması 0;
`codelaw.artifact_graph` ihlal 0 / bayat-sink 0 / taranamayan dosya 0).

| Blok | Nereden | Hüküm | Gerekçe (soruya hizmet + okuyucu korunumu) |
|---|---|---|---|
| Geçmiş sinyaller · denetim izi | adaylar (Koşu) | `<details>` | Bölümün sorusu "bugün kapıdan ne geçti"; geçmiş planlar zaten silahlandı ya da süresi doldu. `ledger.plans_total/plans_shown` kırpma beyanının tek okuyucusu bu blok — denetim izi kanıttır, silinmez. |
| Ham tarama çıktısı | adaylar (Koşu) | `<details>` | Kapı görmemiş GİRDİ listesi; bölümün sorusu kapının ÇIKTISI. `candidates[]` satır alanlarının (rs_rating, sector, score) tek okuyucusu burası — yukarıdaki özet yalnız `source_skill` sayıyor. |
| Yedek anahtar havuzu | hermes (Öğrenme) | `<details>` (yerinde) | Anahtar yönetimi Kilitler'in sorusu; yerinde bırakıldı çünkü kota düşüşünün önlemi eylem şeridiyle aynı nefeste okunur. `/api/hermes/pool_key` ucunun tek yazma yüzeyi. |
| Hermes entegrasyonları (Tier 1+2) | hermes (Öğrenme) | `<details>` | Bağlantı tesisatı — "makine ne öğreniyor?" değil "beyin nasıl kurulmuş?" sorusuna cevap. `integrations.mcp / guard_hook / prompt_cache / tool_use` alanlarının tek okuyucusu. |
| Dışa aktar & operasyon | ajan (Öğrenme) → **ayarlar (Kilitler)** | TAŞINDI + `<details>` | Hiçbiri öğrenme sorusuna hizmet etmiyor. Altı ucun (`report.csv`, `digest`, `digest/weekly`, `state/snapshot`, `debug_export`, `notify/test`) ve `/halt` sayfasının TEK yüzeyi buydu — taşındı, indirildi, silinmedi. |
| Intraday · Faz 4a gözlem özeti | operasyon → veriboru (Veri) | `<details>` | Ayrıntısı `intraemir`de TAM hâliyle duruyor; "aynı soruya iki yerden cevap" operatörün şikâyetiydi. `barfeed.running`, `intraday.armed_plans`, `intraday.decisions.today` alanlarının tek okuyucusu bu özet (ayrıntı kartı bu üçünü okumuyor) — silmek üç alanı öksüz bırakırdı. |
| Kalibrasyon dağılımı | ajan (Öğrenme) → **karne** | TAŞINDI | "Tahmin mi tuttu?" karnenin sorusudur; hüküm ile kanıtı ayrı bölümlere koymak ikisini de zayıflatıyordu. |
| Alarm gelen kutusu · olay akışı | brifing (Portföy) → **operasyon (Gözetim)** | TAŞINDI | ADR Gözetim tanımı. Alarmın iki evi vardı (biri "kaç tane", diğeri "hangileri") ve ikisi de yarımdı. |
| Performans karne yarısı | performans (Portföy) → **karne (Öğrenme)** | TAŞINDI | Rejim/araç kırılımı Portföy'de dururken kimse onu öğrenme kanıtı okumuyordu. |

**Ölü-kod silme (S2R-sonrası av, 2026-08-02):** `app.js::bpAlpaca` — sıfır çağıran (göçten ÖNCE de
sıfırdı; S2R kırığı değil, miras ölü kod). YASA-6 kontrolü: okuduğu alan kümesi
(`account.connected/equity/buying_power/positions{symbol,qty,upl}/open_orders`) Ayarlar'daki
`_alpacaKartHTML`in okuduğu kümenin ALT kümesi — tekil okuyucusu olduğu alan yok, silme hiçbir
API alanını öksüz bırakmadı. (Emeklilik değil silme: görünür bir bileşen değildi, hiçbir sayfada
çizilmiyordu.)

**Eritilen başlık katmanları** (kart-içinde-kart yasağı): bölümler kendi `.slabel + <h1> +
.subline` üçlüsünü basmayı bıraktı; tek kalıp `bolumBasHTML()` (h2 + tek satır altyazı + soru
cümlesi + çapa). Eylem şeridinin `<h1>Öğrenme. Üç düğme, üç iş.</h1>` başlığı ve brifing'in
`<h1 class="greet quiet">Günaydın</h1>` selamlaması eritildi — sabah turunun evi Genel Bakış.

**İncelendi, KORUNDU** (soruya hizmet ediyor): Elenen planlardan örnekler (kapı kararıdır),
Bootstrap çan eğrisi (kapının kanıtı), Pipeline koşuları ("beyan edildi KOŞMADI" körlük kanıtı),
emekli araç rafı (zaten `<details>`), terimler sözlüğü (zaten `<details>`), Öz-değerlendirme ·
DİKKAT (öğrenme katmanlarının kendi denetimi — Öğrenme'de kaldı, Gözetim'e taşınması S2R-3'e
bırakıldı çünkü tek karttan ayrıştırılması gerekiyor).

---

# Ek C — S2R-3 cila kaydı (2026-08-02, uygulandı)

Cila turunun sözleşmesi: **mevcut dünya korunur.** Yeni görsel dil, yeni renk jetonu, yeni bileşen
varyantı YOK. Değişen üç şey: ritmin nerede tutulduğu, iki içerik borcunun ödenmesi, ve bir
dürüstlük yüzeyinin üçüncü duruma açılması.

## C.1 · Yoğunluk ve boşluk ritmi — iki yerde tutulan ölçü tek yere indi

**Ölçülen kusur:** ritim CSS'te yazılıydı (`.card + .card` = `--s4`) ama `app.js` **otuz bir**
blok kabına AYRICA satır içi `style="margin-top:Npx"` basıyordu ve N şuydu: 10, 14, 16, 18, 20, 22.
Satır içi stil kuralı her zaman yener — yani sözleşme fiilen yoktu. Aynı mertebedeki iki kart
arası sayfadan sayfaya 10px ile 22px arasında geziniyordu ve okuyucu bu farkı "burada bir
hiyerarşi var" diye okuyordu. Yoktu.

**Hüküm — ÜÇ ÖLÇÜ, hepsi jeton, hiçbiri satır içi:**

| ne | ölçü | nerede tanımlı |
|---|---|---|
| blok arası (kart · ızgara · metrik şeridi · detay katmanı · sözlük) | `--s4` (16px) | `index.html` → *S2R-3 · BLOK RİTMİ* |
| bölüm başlığı altı | `--s5` (20px) | `.bolum-bas{margin-bottom}` — TEK yerde |
| bölüm arası | `--s12` + `--s10` (48+40) | `.alan-bolum + .alan-bolum` — DEĞİŞMEDİ |

Uygulama: 31 satır içi marj silindi; `.mrow`'un kendi `--s8` (32px) marjı `--s4`e indi (beş
çağrının beşinde de zaten satır içi eziliyordu — yani 32 hiçbir zaman ÜSTTE geçerli olmadı,
yalnız ALTTA sessizce duruyor ve ritmi tek başına bozuyordu); `.detay-kat` `--s6`dan `--s4`e;
`.hero`nun 24px'lik ham marjı kalktı.

**Ölçü bloğun KENDİSİNDE, komşusunda değil.** İlk kurgu kardeş seçiciydi (`X + Y`) ve sessizce
yarım koşuyordu: bir kartın önünde her zaman başka bir blok olmuyor — Piyasa'da kart bir
`<p class="hint">`i izliyor — ve o hâllerde kural hiç ateşlenmiyordu, yani kart metne yapışıyordu
ve hiçbir test kırmızı vermiyordu. Taban kural artık `:is(.card,.g2,.mrow,.hero,.gloss,
.detay-kat){margin-top:var(--s4)}`; sıfırlandığı iki hâl var ve ikisi de gerekçeli: (1) ızgara
ÇOCUĞU — eski aile yalnız İKİNCİ kartı sıfırlıyordu, blok kendi marjını taşıyınca BİRİNCİ kartın
da sıfırlanması gerekti (yoksa ızgaranın ilk kutusu tek başına 16px kayar — 2026-07-28
arızasının aynası); (2) `.bolum-bas`tan sonraki ilk blok. Taban kuralın özgüllüğü bilerek
`(0,1,0)`: hem eski sıfırlayıcılar `(0,3,0)` hem yeni ızgara-çocuğu sıfırlaması `(0,2,0)` onu her
zaman yener. `.hero-grid` ve `.eylem-serit` aileye ALINMADI — ikisi de bir kartın İÇ yerleşim
sarmalayıcısı; aileye alsaydık `.hero`nun içine 16px'lik bir kaçık enjekte ederdik.

**Aynı bildirim iki yere yazılmaz.** `.mrow`/`.gloss`/`.detay-kat` marjları kendi kurallarında
duruyor, S2R-3 bloğunda tekrarlanmıyor: aynı özgüllükteki iki bildirimin kazananı KAYNAK SIRASINA
bağlıdır ve bu turda tam olarak o hata bir kez yapıldı (blok yukarıda olduğu için orada yazılan
`--s4`, aşağıdaki `--s8`e sessizce yeniliyordu — gözle görülmezdi). Test artık her sınıf için
"marj TEK kuralda bildirilmiş" diye ölçüyor.

**Öğrenme'nin ilk sınırı eklendi:** `#ogrenme-eylem + .alan-bolum` artık kural çizgisi taşıyor.
Yedi bölümlü bir sayfada ilk sınırın eksik olması (Karne, eylem şeridinin düğmelerine yapışık
başlıyordu) geri kalan altı sınırın ritmini de yalanlıyordu.

**Kart-içinde-kart:** tarandı, YOK. `rise`sız `class="card"` beş yerde geçiyor ve beşi de bir
ızgara ÇOCUĞU (yan yana kart, iç içe değil). Liste ve gerekçeleri
`test_s2r3_cila_v160::IZGARA_KARTLARI`de; listeye gerekçesiz satır giremez.

**Çift çerçeve: BİR tane vardı, eridi.** Altı detay katmanının beşi çerçevesiz gövde taşıyor;
biri (Veri Sağlığı → "Intraday · Faz 4a gözlem özeti") tam bir `.card` alıyordu, çünkü o parça
`opParcalar()`ta kart olarak üretiliyor ve tek tüketicisi orası. Sonuç: katlanmış bir bölmenin
İÇİNDE ikinci bir kutu. Kart JS'te bölünmedi (tek üretici/tek tüketici — bölmek iki yeri
ayrıştırma riskine açardı); kural CSS'te eritildi: `.detay-kat .dk-govde > .card` çerçevesini ve
dolgusunu bırakır, içeriğini bırakmaz. Yeni değer YOK.

## C.2 · İçerik borcu #1 — gölge-varyant portföyleri `golge` bölümüne indi

Ek A'nın açık bıraktığı borç. Blok, Hermes karnesi kartının bir ALT BAŞLIĞIYDI ve S2R-2 onu
taşıyamamıştı çünkü göç sözleşmesi "bölüm taşı, kart gövdesi yeniden yazma"ydı.

**Hüküm:** kart gövdesi bölündü. `sHermes` artık yalnız H1–H3 + MAE; yeni `sGolgeVaryant` kendi
kartı ve `golge` bölümünde yazılıyor. Bölüm iki kol taşıyor ve sırası hüküm mertebesine göre:
**canlı gölge-kitap** (hükmü verilmiş TEK kol, gerçek barlar) → **varyant portföyleri** (k adet
aday kol, çoklu-karşılaştırma paydasıyla). Altyazıdaki borç beyanı ("öteki gölge kol Karne
bölümünde") kaldırıldı — ödenmiş bir borcu anlatan altyazı okuru var olmayan bir yere gönderir.

**Okuyucu korunumu (YASA-6):** `shadow_variants`ın altı alanı da birebir taşındı — `n_satir` ·
`son_karar{label,date,signal_n,would_arm_n}` · `kumulatif_ayrisma` · `k_variants` · `rol` ·
`durum`. Panoda başka okuyucusu yok; biri düşseydi alan öksüz kalırdı. `k_variants` (çoklu-
karşılaştırma paydası) bilerek tabloyla AYNI kartta bırakıldı: "şerh rakamdan ayrılamaz" kuralının
bu karttaki karşılığı — payda ayrılırsa "en iyi varyant" seçiminin yanlılığı görünmez olur.
İki hâl ayrı cümle olarak korundu: uç servis etmiyorsa kart **hiç doğmaz**; defter boşsa kart
doğar ve arka ucun kendi `durum` cümlesini yazar.

## C.3 · İçerik borcu #2 — "Öz-değerlendirme · DİKKAT": karttan AYRILDI, Öğrenme'de KALDI

İki ayrı karar, ikisi de ölçüldü:

**(a) Karttan ayrıştırıldı.** Blok "Bölüm 3 · MLOps & Hermes" kartının dibinde, iki ızgara
sütununun altında bir `<h3>` olarak duruyordu. Kartın başlığı onu ARAMAYACAĞIN bir yere
koyuyordu: bir DİKKAT listesi, bir tesisat kartının dip başlığı olamaz. Artık kendi kartı
(`sOzDeg`).

**(b) Gözetim'e TAŞINMADI — ölçüm, varsayım değil.** `selfreview._attention()` sekiz kural
ailesi üretiyor. Dağılım:

| kural ailesi | hangi sorunun cevabı |
|---|---|
| skor kalibrasyonu IC'si (gerçek dilim, anlamlı, < −0.05) | ÖĞRENME |
| cf sadakati onaysız | ÖĞRENME |
| kapı kendini sıkılaştırdı (`gate_meta.extra_p`) | ÖĞRENME |
| çıkışta masada R kalıyor (`exit.nudge_active`) | ÖĞRENME |
| ilerleme eşiği doldu (`progress`, silahlanma kanıtı) | ÖĞRENME |
| bekleyen revizyon taslağı | ÖĞRENME |
| near-miss hipotez tohumu | ÖĞRENME |
| mekanizma kesintisi / bekçi olay sayısı | GÖZETİM |

Altıya bir. Ve **tek gözetim ailesinin Gözetim'de ZATEN evi var:** `selfreview.mechanism_failed()`
`MECHANISM_STALE` alarmı üretiyor (jeton `obs.NOTIFY_TOKENS` içinde, `monitoring.sh` grepliyor) ve
o alarm Gözetim'in gelen kutusunda okunuyor. Bloğu taşımak, yedi öğrenme hükmünü "sistem sağlıklı
mı?" sorusunun altına gömer ve iki sağlık satırını İKİNCİ kez göstererek operatörün asıl
şikâyetini ("aynı soruya iki yerden cevap") geri getirirdi. **Ev: Öğrenme · beyin bölümü.** Kart
sağlık yarısının nerede yaşadığını ekrandan söylüyor, böylece okur "burada mı, orada mı?" diye
sormuyor.

## C.4 · Bekçi dürüstlük yüzeyi — üçüncü durum (denetim C21/C22'nin pano ayağı)

**Ölçülen kusur.** watchdog düşen bir dedektörü `_DEDEKTOR_BOS` **iskeletiyle** döndürüyor
(`{**iskelet, ok: False, dedektor_dustu: True, olculemedi: True, error: …}`) — yani `starved: []`,
`stale: []`, `lost: []` BOŞ gelir. Panonun `_patOK`'u iki değerliydi ve o boşlukları "bulgu yok"
diye okuyup satırı **YEŞİL "temiz"** basıyordu: ölçülemeyen bir hüküm, ölçülmüş bir temizlik
kılığında (üretkenlik · korunum · tutarlılık desenleri). Ters yön de yanlıştı: `determinism`
fail-closed'ta `ok:False` döndüğü için **KIRMIZI "İHLAL"** basılıyordu — oysa watchdog'un kendi
cümlesi, "ölçülemeyen bir hükmü ihlal diye anlatmak da bir uydurmadır".

**Hüküm — üç durum:**

| durum | koşul | çip | metin |
|---|---|---|---|
| temiz | ölçüldü, bulgu yok | `t-go` | mevcut özet satırı |
| İHLAL | ölçüldü, bulgu var | `t-no` | mevcut bulgu satırı |
| **ÖLÇÜLEMEDİ** | `olculemedi === true` **veya** `dedektor_dustu === true` | `t-vi` (nötr) + `.mut` gövde | `ÖLÇÜLEMEDİ — bu turda hüküm verilmedi (detector_failed · olculemedi) · <hata>. Boş liste "bulgu yok" DEĞİL.` |

**Renk icat edilmedi.** `t-vi` bu panoda zaten "ölçüm yok / hüküm yok" kanalı: sağlayıcı kartında
`"çağrı yok"`, defter sözleşmesinde `"boş"`, trend kitabında `"DOĞMADI"`. İkinci bir nötr renk üç
ay sonra "hangi gri neydi?" sorusunu doğururdu. Çift kodlama (Ç7) **kelimeyle** sağlanıyor:
üç durumun üçü de farklı bir sözcük basıyor (bkz. kontrast eki §10.2 — nötr çipin DOLGUSU gündüz
temasında 1.02:1, yani hüküm mürekkepten ve kelimeden geliyor; bu dört çipin dördü için de böyle).

**Makine-okunur ad satırda duruyor.** Metin `olculemedi` (ve dedektör yalıtımı devredeyse
`detector_failed`) kelimelerini AYNEN yazıyor: operatörün panodan okuduğu ad ile obs günlüğünde
(`integrity_detector_failed`) ve alarm katmanında greplediği ad aynı olmalı. Yalnız `olculemedi`
taşıyan hâl `detector_failed` DEMEZ — olmayan bir yalıtım olayını raporlamak da uydurma olurdu.
Kaç dedektörün ölçemediği kart BAŞLIĞINDA da sayılıyor: yedi satırın içinde tek bir nötr çipi
kaçırmak kolaydır ve "7 desen temiz" izlenimi tam da bu kaçışla doğar.

**Aynı kusur sınıfı ikinci bir kartta kapandı:** sağlayıcı sağlık kartı `p.olculemedi` satırını
`t-no` (kırmızı) basıyordu. Sağlık OKUMASININ düşmesi, sağlayıcının ARIZALI olduğu anlamına
gelmez ve o hüküm zaten ayrı bir satırda (`SON ÇAĞRI BAŞARISIZ`) yaşıyor. Nötre indi.

## C.5 · Palet, `g`-kısayolu, `?` haritası, CSP

**Palet yirmi bölümün beşine gidebiliyordu.** `mutabakat`, `golge`, `bilesenic` ve on iki eski
görünüm adının hiçbiri palet aramasında geçmiyordu — operatör "mutabakat" yazıyor, hiçbir şey
çıkmıyordu. Palet bir bilgi mimarisi haritasıdır; on beş odası olmayan bir harita, haritanın
kendisine olan güveni bitirir (bir kez boş dönen arama bir daha denenmez).

Hüküm: `BOLUMLER` tablosu — **yirmi satır**, sırası `ALAN_BOLUMLERI` ile birebir (yani paletdeki
sıra sayfadaki OKUMA sırası). Tablo paletin SAF ÇEKİRDEĞİNE alındı ve dışa veriliyor: test onu
kaynak metninden regex'le sökmüyor, gerçek diziyi alıp gerçek `bulanikSkor` ile arıyor — "yirmi
bölüm de bulunuyor" iddiası ölçülüyor, beyan edilmiyor. Türkçe katlama (`katla`) sayesinde "gölge"
ve "golge" aynı satırı buluyor; her satır ayrıca kendi id'sini anahtar kelime olarak taşıyor.
Uydurma çapa yok: her `<bölüm>` hem `bolumBasHTML(id, …)`ın ürettiği bir `id`, hem `#page-<bölüm>`
kabı (`el()` kapısı çalışma anında da doğruluyor).

**`g`-kısayolu** yedi sayfanın yedisini kapsıyordu, değişmedi. **`?` haritasına** iki satır
eklendi: ⌘K'nın kapsamı ("yedi sayfa ve yirmi bölümün tamamı") ve bölüm çapası biçimi
(`portfoy#mutabakat`) — özellik keşif yüzeyinde yazmıyorsa fiilen yoktur (Nielsen İ6).

**CSP:** `YUZEYLER` listesi zaten tamdı (app.js · palette.js · theme.js · landing.js ·
workflow.js + dört html). Eksik olan, listenin TAM OLDUĞUNUN ölçülmesiydi — 2026-08-01'in
virgül-bitişme vakasında liste yeşil görünürken iki yüzey hiç sınanmıyordu. Yeni test listeyi
`meridian/web` dizininin gerçek `.js`/`.html` kümesiyle **iki yönlü** karşılaştırıyor: eksik giren
yüzey de, bitişip var olmayan ada dönüşen giriş de kırmızı verir.

## C.6 · Ölçüm ve kapsam

- Yeni test: `tests/test_s2r3_cila_v160.py` (29 test). Bekçi hüküm dilimi **Node ile
  koşturuluyor** ve yükler `meridian.watchdog._DEDEKTOR_BOS`tan **import ediliyor** — üretici/
  tüketici paritesi ancak üreticinin kendi iskeletiyle ölçülür, elle yazılmış bir taklidiyle değil.
  `test_TEST_KENDINI_KANITLAR_eski_iki_degerli_hukum_YESIL_derdi` testin kırabildiğini kanıtlıyor.
- Taşınan çivi: `test_s2r2_goc_v156::sahipler` — "Gölge-varyant portföyleri" `karne_ek`ten
  `golge`ye geçti (silinmedi, ev değiştirdi; silinseydi tablo bir daha izlenmezdi).
- Koşum: `-k "pano or s2r or uiux or tasarim or csp or edge_dashboard"` → **368 geçti, 0 hata**
  (exit 0) + `node --check` app.js/palette.js temiz. Ayrıca bölünen üç kart (`sHermes`,
  `sGolgeVaryant`, `sOzDeg`) Node'da FİİLEN çalıştırılıp HTML denge denetiminden geçirildi
  (dolu / boş-defter / uç-yok hâllerinin üçünde de etiket yığını dengeli). Tam suite Rol-1'de.

## C.7 · Yapılmadı, bilerek

- **Jeton yeniden-değerlemesi yok.** `tokens.json` ve `:root` blokları bit-bit aynı; jeton sayımı
  23 temel + 2×36 renk = 95. Kontrast §3 tablosu bu yüzden bayat değil.
- **Nötr çipe ikinci kanal (kesikli kenar) uygulanmadı** — öneri Ö-S3-1 olarak kontrast ekine
  yazıldı. Yeni bir çip varyantı bu turun "mevcut dünya korunur" sözleşmesini deler.
- **Bölüm arası ölçüsü (`--s12`+`--s10`) yeniden değerlenmedi.** Zaten tek kuralda ve tek ölçüde;
  daraltmak bir yoğunluk KARARIdır ve ekran görüntüsüyle operatör onayına aittir.
- **Kalan ham px boşluk değerleri app.js'te duruyor** (kart İÇİ `margin-top:8px/10px` gibi
  satırlar). Bu tur BLOK ritmini kapattı; kart-içi mikro ritim ayrı bir tur ve ayrı bir ölçüm
  ister — ikisini aynı commit'e koymak, kırılma hâlinde hangisinin kırdığını ölçülemez kılardı.

---

# Ek D — **S2R-4 REVİZYONU: yedi sayfa → beş yüzey** (D2-b, 2026-08-07, uygulandı)

**Statü:** bu ek, yukarıdaki "Hedef IA (12 görünüm → 1+6+detay)" bölümünü **yürürlükten
kaldırır**. Üstteki metin tarihsel kayıt olarak yerinde bırakılmıştır (S2R-1/2/3'ün gerekçeleri
oradan okunur); **bağlayıcı IA artık `docs/TASARIM-YONU-2026-08-07.md` §3'tür.**

## D.1 · Hangi sayfa neden birleşti

| Yeni yüzey | Birleşen | Ölçülen gerekçe |
|---|---|---|
| **① Bugün** | `genel` (yeniden adlandırıldı) | Ad, ekranın işini söylemiyordu: "Genel Bakış" bir kap adı, "Bugün" bir iştir. Kart kompozisyonu ve altı-kart bütçesi AYNEN korundu. |
| **② Karar** | `kosu` + `portfoy` | Durum ızgarası (`DURUM_SAYFALARI`) **tek tanımdı, iki sayfada çiziliyordu** — v191 çakışmayı bir bantla örtmüş, kökünü çözmemişti. Birleşme `durumIzgarasiCiz` çağrısını **ikiden bire** düşürdü ve "aynı sayı iki sayfada" sınıfını yapısal olarak kapattı. |
| **③ Sağlık** | `veri` + `gozetim` | TASK ③'ün (alarmdan nedene ve dispozisyona) ölçülen yolu **iki sayfaya** yayılıyordu (denetim B12). Birleşme alarm → ihlal → veri kaynağı zincirini tek yüzeyde tutar. |
| **④ Öğrenme** | (değişmedi) | 39 kart taşıyor ve hiçbiri diğer dört yüzeyin sorusuna hizmet etmiyor. Çözümü birleşme değil **katlama** (v198 kart sözleşmesi). |
| **⑤ Kilitler** | (değişmedi) | Adı kısaldı; kapsamı aynı. |

**Sıra sözleşmesi korundu ve genişledi:** ② içinde zincir *ne önerildi → neden geçti/geçmedi →
senden ne isteniyor → ne oldu → aynaya ulaştı mı → seans-içi → birikim*; ③ içinde *önce bozulan →
hattın çizelgesi → hattın iç sağlığı → evren → akış*. Sıra `ALAN_BOLUMLERI` + `index.html` DOM
dizilimi + `palette.js` tablosunda **üç yerde aynı** ve test onu üçünde birden karşılaştırıyor.

## D.2 · Ölçülen kart sayıları (D2-a yöntemi, aynı betik)

| Yüzey | Toplam kart | Kapaklı | Bütçe | Not |
|---|---|---|---|---|
| ② Karar | **21** (kosu 4 + portfoy 17) | 3 | 6 | kart TAŞINDI, doğmadı |
| ③ Sağlık | **14** (veri 9 + gozetim 3 + çizelge 2) | 4 | 6 | +2 doğan kart: canlı zaman çizelgesi |
| ④ Öğrenme | 39 | 18 | 6 | değişmedi |
| ⑤ Kilitler | 5 | 0 | 5 | değişmedi |

**Bütçeler toplanmadı, taşındı.** Bir okurun bir ekranda tutabildiği kart sayısı iki yüzey
birleşti diye ikiye katlanmaz; toplamak (4+6=10, 6+3=9) sözleşmeyi birleşmenin kendisiyle
gevşetmek olurdu. Aşım gizlenmez: `.kk-butce` satırında **sayıyla** ve **şiddet rengi taşımadan**
yazılır (renk yalnız anomalide).

## D.3 · "BAŞKA HİÇBİR ŞEY" kuralının triyaj şeridi lehine revizyonu

S2R-1'in ADR'si ① için *"altı kart ve BAŞKA HİÇBİR ŞEY"* diyordu; triyaj şeridi bu yüzden ①'e
alınmamıştı. **Yön belgesi §3 şeridi açıkça ①'e yerleştiriyor** ("sessiz-hat · triyaj şeridi ·
son döngü · kitap · alarm bütçesi"). Revizyonun gerekçesi ölçüldü, tercih değil:

- Şerit bir KART DEĞİLDİR — `<main>`in ilk çocuğudur ve **her yüzeyde aynı yerde** durur; kart
  bütçesini yemez (ölçüm: `.gb-kart` sayımı 6'da kalır, test onu sayıyor).
- Şeridin cevapladığı soru ("şu an senden bir şey bekleniyor mu?") ①'in soru cümlesinin
  **üçüncü yarısıdır** ("benden ne bekleniyor?"). Kural bu yüzden şöyle daraldı:
  **① yeni bir KART almaz; şerit ve sessiz hat kart değildir.**

## D.4 · Geri uyum — 17/17 alias, iki sınıf

`ROUTE_ALIAS` artık **iki sınıf** taşır ve ikisi de "eski adres"tir:

| Sınıf | Girdi | Neden |
|---|---|---|
| (a) **bölüm aliası** — 12 | eski on iki görünüm adı | bugün birer `.alan-bolum`; kabı gerçekten hedef yüzeyin içinde |
| (b) **sayfa aliası** — 5 | `genel · kosu · portfoy · veri · gozetim` | kabı YOK (yüzeyi birleşti); `kosu#adaylar` / `portfoy#mutabakat` / `gozetim#failsub` / `veri#veriboru` biçimindeki her eski derin adres bununla çözülür |

`go()` çapayı **önce** ayırır, alias'ı **sonra** uygular — sıra bozulursa `portfoy#mutabakat`
hiç çözülmez ve `test_ia_v199::test_eski_derin_adresler_capasiyla_birlikte_cozulur` bunu çiviler.
**Pano kendi içinde YENİ adres dilini konuşur:** alias bir geçiş katmanıdır, ikinci bir dil değil
(ayrı test).

## D.5 · Olay yüzeyleri (Tier-4) ve `runbook.html`in emilmesi

`runbook.html` **birincil teşhis yüzeyi olmaktan çıktı**. İçeriği panonun olay yüzeylerine
emildi: ③ Sağlık → alarm satırı → `teşhis ↗` → **tam çekmece**, dört bölümlü ve sırası sabit:
*1 · ne oldu · 2 · değerler ŞİMDİ ne · 3 · runbook adımları · 4 · mevcut eylemler.*

- **Yeni bileşen yok:** aynı `openDrawer` kapısı, aynı odak tuzağı, aynı Esc sözleşmesi.
- **Tek emir-yolu korundu:** "mevcut eylemler" yalnız kolun gerçekten yaşadığı bölüme *götürür*;
  çekmecede HALT/FLATTEN düğmesi YOKTUR (test bunu yasaklıyor).
- **Uydurma yasağı:** `docs/RUNBOOK.md` çoğu jeton için "runbook girdisi henüz yazılmadı" diyor
  ve yüzey o boşluğu **doldurmaz, adıyla yazar**. Ölçülemeyen değer `0` basmaz.
- **12/12 jeton kapsandı:** altı sınıf (`besleme · mutabakat · kill · butunluk · yetki · kota`)
  `obs.py`nin on iki jetonunun **hepsini** ve yalnız onları taşıyor; jeton→sınıf haritası
  **türetilir**, elle yazılmaz.
- **Dosya SİLİNMEDİ:** derin çapa bağları (`/runbook#mirror_drift`) dışarıda yer imi olabilir.
  Sayfa "içerik panoya taşındı" yönlendirmesi bıraktı ve `<!--RUNBOOK-TOC-->` /
  `<!--RUNBOOK-GOVDE-->` yer tutucuları korundu (`api.py::runbook()` onları arıyor). **Silme
  D5'te, bağ denetimiyle.**

## D.6 · `workflow.html` emekli — halefi ③'ün canlı zaman çizelgesi

Statik boru-hattı resmi panodan **sıfır iç bağ** alıyordu (baseline §3.3) ve gösterdiği her nicel
iddia elle yazılmıştı. Halefi `saglik#cizelge`: hattın **adımları** (`HAT_ADIMLARI`, liste-veri)
+ bekçinin **ölçtüğü** gecikme. Dürüstlük sınırı yazılı: bekçi raporu yalnız GECİKENLERİ
adlandırır, penceresinde olanlar bir SAYIdır — bu yüzden "bu adım 03:12'de koştu" **yazmıyor** ve
uydurulmuyor da; damgaların uca açılması D3-UI'ın kalemi. Bekçinin **her** mekanizmasının
çizelgede bir evi var (test `watchdog.EXPECTED`ten okuyup karşılaştırıyor).

## D.7 · Tekilleştirilen yinelenen çiftler (baseline §2)

| # | Soru | Ne yapıldı | Tek ev |
|---|---|---|---|
| P1 | Emir aynaya ulaştı mı? | İki biçim (rozet · oran çubuğu) artık **aynı yüzeyde** ve aralarında adres var | sayı: ③ EMİRLER kartı · satır kimliği: "Sıradaki seans" tablosu |
| P2 | Alarm bütçesi aşıldı mı? | **Bırakıldı** — özet(①, tek satır + adres) ile kırılım(③) farklı mertebedir, kopya değil | ③ `operasyon` |
| P3 | Bekçiler ne durumda? | **HUD çipi kaldırıldı** | sessiz hat `bekçiler` segmenti (adlarıyla) + ③ `cizelge` (17 mekanizma) |
| P4 | Nabız taze mi? | **Ray özetinden kaldırıldı** | `#statuspill` (yaşıyla) + sessiz hat `veri` segmenti |
| P5 | WS akıyor mu? | Durum kartı artık **yalnız anomalide** konuşur (rozetin gerekçesi), sağlıklı hâlde adres verir | ② `mutabakat` masası satırı |
| P6 | Ayna sapması var mı? | **Ray özetinden ve Ayarlar kartından kaldırıldı** (ikincisi adres verir) | ② `mutabakat` masası |
| P7 | Sistem durduruldu mu? | **Ray özetinden kaldırıldı** (dördüncü kopyaydı) | banner `#statuspill` · alarm: triyaj şeridi (koşullu) · kol: ⑤ `mudahale` |
| P8 | Hangi kesitte kaç işlem? | **Bırakıldı** — matris hücresi ile satır listesi aynı bölümde, farklı kesit | ④ `karne` |
| P9 | Bugün ne bekliyor? | Şeridin **ölü kolu silindi** (N1: `autonomy_level >= 1` L0'da hiç ateşlemedi ve `pending_count` yanlış adlandırılmıştı) | ① "Bugün ne var" kartı (`inbox_count` + REVIEW) |
| P10 | Otonomi seviyesi ne? | **`.acct` kutusundan kaldırıldı**, ⑤'in ray özetine taşındı (mod satırı kaldı — Dalga-0 hükmü) | `#statuspill` + ⑤ ray özeti |

## D.8 · Test çivileri — taşındı, sökülmedi

`docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md` §7.3 maliyeti **23 test fonksiyonu / 6 dosya**
diye ölçmüştü. Fiilî: **7 dosyada 34 fonksiyon** yeniden ifade edildi (üçü ölçüm dışıydı:
`test_pano_palet_v152`, `test_pano_turu_v139`, `test_v195a_quickwin`) + **yeni
`tests/test_ia_v199.py` (25 test)**. Hiçbir çivi zayıflatılmadı; her biri yeni gerçekle yeniden
yazıldı ve gerekçesi test gövdesinde duruyor (*"ÇİVİ TAŞINDI …"* deseni).

Ayrıca `research/olcumler/kart_sozlesmesi_2026-08-07/say_kart.py` artık `ALAN_BOLUMLERI`yi
**app.js'ten türetiyor**: ikinci bir elle liste, IA değiştiği gün ölçüm betiğini `KeyError`e
düşürdü — ölçümün yöntemi değil, girdisinin kaynağı düzeltildi.

## D.9 · Yapılmadı, bilerek

- **Kart silme yok.** D2-a'nın "kapak almayan bölümler" kuyruğu (Öğrenme'nin 21 kartı, ②'nin 14
  kartı) yerinde; silme bir İÇERİK kararıdır ve D3-UI'ın kalemi.
- **Çizelgenin adım-başına DAMGASI bağlanmadı** — uçta yok (yalnız gecikenler adlandırılıyor).
  D3-UI'a devredildi; bu turda yüzey ve yerleşim kuruldu, sayı uydurulmadı.
- **Yazı tipi ve tipografi değişmedi** (Geist, D4'ün kalemi). `runbook.html` ve `workflow.html`in
  kendi jeton blokları ve type-ramp sapmaları da bu yüzden yerinde — ikisi D5'te siliniyor.
