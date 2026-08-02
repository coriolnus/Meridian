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
  (equity+DD, karne, kapsama) — HEPSİ özet; her kartın "→ alan sayfası" tek bağı. BAŞKA HİÇBİR ŞEY.
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

**Eritilen başlık katmanları** (kart-içinde-kart yasağı): bölümler kendi `.slabel + <h1> +
.subline` üçlüsünü basmayı bıraktı; tek kalıp `bolumBasHTML()` (h2 + tek satır altyazı + soru
cümlesi + çapa). Eylem şeridinin `<h1>Öğrenme. Üç düğme, üç iş.</h1>` başlığı ve brifing'in
`<h1 class="greet quiet">Günaydın</h1>` selamlaması eritildi — sabah turunun evi Genel Bakış.

**İncelendi, KORUNDU** (soruya hizmet ediyor): Elenen planlardan örnekler (kapı kararıdır),
Bootstrap çan eğrisi (kapının kanıtı), Pipeline koşuları ("beyan edildi KOŞMADI" körlük kanıtı),
emekli araç rafı (zaten `<details>`), terimler sözlüğü (zaten `<details>`), Öz-değerlendirme ·
DİKKAT (öğrenme katmanlarının kendi denetimi — Öğrenme'de kaldı, Gözetim'e taşınması S2R-3'e
bırakıldı çünkü tek karttan ayrıştırılması gerekiyor).
