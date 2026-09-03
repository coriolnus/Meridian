/* ============================================================================
   HAFIZA GÖRÜNÜMLERİ — CP'nin kenar çubuğu sırası, TEK YERDE
   ----------------------------------------------------------------------------
   SIRA UYDURULMADI, OKUNDU. Hindsight Control Plane v0.9.2'nin `sidebar.tsx`
   dosyasındaki `navItems` dizisi sekiz maddedir ve SIRASI ŞUDUR:

       home · data · knowledge · recall · reflect · documents · entities · profile

   Aşağıdaki dizi o sıranın birebir karşılığıdır. Alfabetik sıraya çekmek ya da
   "bize göre daha mantıklı" bir sıraya dizmek, birebirleştirmenin tam olarak
   ölçülebilir olan yarısını kaybetmek olurdu: CP'yi bilen bir okuyucu aynı
   yerde aynı maddeyi bulamazdı.

   ETİKETLER VE İKONLAR BURADA YAZILMAZ — `alanlar.ts`teki YÜZEY KAYDINDAN gelir
   (tek-kaynak yasası). Kayıt zaten gezinmenin, ⌘K paletinin, kırıntının ve v288
   parite çivisinin ortak kaynağı; ikinci bir başlık listesi tutmak, kenar
   çubuğunun içindeki adla dışındaki adın sessizce ayrışması demekti.

   BU DOSYA KAYITTAN NE İSTER: sekiz kimliğin her birinin `alanlar.ts`te KAYITLI
   olmasını. İstemediği tek şey SESSİZLİK — bir kimlik kayıttan düşerse sayfa onu
   gizlemez, "yüzey kaydında bulunamadı" diye ÇİZER (`HafizaYuzey.tsx`).
   Gizleseydi bir görünüm gezinmeden düşer ve kimse fark etmezdi; bu deponun
   defalarca ölçtüğü sessiz kayıp sınıfı tam olarak budur.

   SIRANIN TÜKETİCİSİ DEĞİŞTİ (2026-09-02, operatör kararı): yüzey içi kenar
   çubuğu kalktı ve sekiz durak küresel sol gezinmeye taşındı. Sıra oradan da
   KAYITTAN okunuyor (`alanlar.ts::YUZEYLER.memory.bolumler` → `gezinme.ts`),
   yani bu dizinin sözleşmesi değişmedi: adres çözümü ve varsayılan görünüm.
   ============================================================================ */
import { YUZEYLER, type Bolum } from "../../alanlar";
import type { Durum } from "../../veri";
import type { HafizaGovdesi } from "./uctipleri";

/** CP `sidebar.tsx::navItems` sırası — kimlikler `hafiza-` önekli (v288 tekillik). */
export const HAFIZA_GORUNUMLERI = [
  "hafiza-anasayfa",
  "hafiza-bellekler",
  "hafiza-bilgi",
  "hafiza-recall",
  "hafiza-reflect",
  "hafiza-belgeler",
  "hafiza-varliklar",
  "hafiza-yapilandirma",
] as const;

export type HafizaGorunumu = (typeof HAFIZA_GORUNUMLERI)[number];

/** Açılışta hangi görünüm — CP'de de ilk madde `home`dur. */
export const VARSAYILAN_GORUNUM: HafizaGorunumu = "hafiza-anasayfa";

/* ---------------------------------------------------------------------------
   ESKİ ÇAPALAR — YER İMİ KIRMADAN EMEKLİ EDİLİR
   Bu yüzeyin ilk sürümü DÖRT bölümdü (`hafiza-bankalar` · `hafiza-bellekler` ·
   `hafiza-operasyon` · `hafiza-kota`) ve o adresler ⌘K paletinde, kenar
   çubuğunda ve operatörün yer imlerinde GERÇEKTEN dolaştı. Yeni bilgi mimarisi
   üçünü kaldırıyor; kaldırılan bir adresin sessizce varsayılana düşmesi bu
   deponun A-sınıfı arızasıdır ("bağ çalıştı sanırsın, yanlış yerdesindir").

   Üçü de anlamlı bir yeni eve yönlendiriliyor:
     · bankalar   → banka seçici artık kabuğun üstünde, sayaçlar Ana Sayfa'da
     · operasyon  → CP bu sayaçları banka yapılandırma tarafında topluyor
     · kota       → aynı ev

   YÖNLENDİRMENİN KARŞILIĞI ARTIK DOLU (TSK-108 Görev 3): `operasyon` ve `kota`
   içerikleri Yapılandırma görünümünde çiziliyor — işler tablosu, denetim kaydı,
   model çağrıları ve iki sayaç kutusu. Yani bu tablo bir telafi değil, gerçek
   bir evin adresidir.
   --------------------------------------------------------------------------- */
export const ESKI_GORUNUM_ADRESLERI: Readonly<Record<string, HafizaGorunumu>> = {
  "hafiza-bankalar": "hafiza-anasayfa",
  "hafiza-operasyon": "hafiza-yapilandirma",
  "hafiza-kota": "hafiza-yapilandirma",
};

/**
 * Bir bölüm adresini görünüme çevirir. Tanınmayan adreste `null` döner.
 *
 * ŞERH DÜZELTİLDİ (T2 yeniden-incelemesi): burada önce "çağıran yerel seçimini
 * korur" yazıyordu ve o cümle I-4 düzeltmesinden sonra YANLIŞ. Görünüm artık
 * yerel bir durumda değil ADRESTE yaşıyor (`HafizaYuzey.tsx` başlığı), yani
 * korunacak bir yerel seçim yok: `null` gören çağıran varsayılana — yüzeyin
 * adressiz ilk açılışıyla AYNI hâle — düşer. Bayat bir şerh, olmayan bir
 * şerhten kötüdür: okuyucu davranışı kaynaktan değil yorumdan öğrenir.
 */
export function gorunumCoz(bolum: string | null | undefined): HafizaGorunumu | null {
  if (!bolum) return null;
  if ((HAFIZA_GORUNUMLERI as readonly string[]).includes(bolum)) return bolum as HafizaGorunumu;
  return ESKI_GORUNUM_ADRESLERI[bolum] ?? null;
}

/**
 * Görünümün BAŞLIĞI, SORUSU VE İKONU — yüzey kaydından, elle yazılmadan.
 *
 * `null` dönüşü "bu görünüm kayıtta YOK" demektir ve çağıran onu GİZLEMEZ,
 * yazar. Sessiz bir `??` yedeği koysaydık kayıttan düşen bir görünüm ekranda
 * uydurma bir başlıkla yaşamaya devam eder, kenar çubuğundan ise düşerdi —
 * ve ikisi arasındaki fark yalnız kaynağı okuyanın gözünden anlaşılırdı.
 */
export function bolumKaydi(kimlik: HafizaGorunumu): Bolum | null {
  return YUZEYLER.memory.bolumler.find((b) => b.kimlik === kimlik) ?? null;
}

/**
 * Her görünüm gövdesinin ALDIĞI ŞEY — sekizinde de aynı, bilerek.
 *
 * `bank` kabuktan iner ve HİÇBİR görünüm kendi banka seçicisini açmaz: iki
 * görünüm aynı anda iki farklı bankayı gösterirse operatör hangisine baktığını
 * ekrandan okuyamaz. `kayit` da kabuktan iner, çünkü başlığın tek kaynağı yüzey
 * kaydıdır — görünüm kendi başlığını yazsaydı kenar çubuğundaki adla gövdedeki
 * ad sessizce ayrışırdı.
 */
export interface GorunumOzellikleri {
  readonly bank: string | null;
  readonly kayit: Bolum;
  /**
   * KABUĞUN ZATEN YAPTIĞI TOPLU OKUMA — yeni bir çağrı DEĞİL, mevcut olanın
   * paylaşılması.
   *
   * NEDEN VAR (bedel yasası, Görev 2 incelemesi M-2): `/api/hindsight` banka
   * başına kota ve operasyon sayaçlarını da getiriyor ve Görev 2'den sonra o iki
   * bacağı HİÇBİR ekran okumuyordu — otuz saniyede bir okuyucusuz iki upstream
   * çağrısı. Sayaçların evi Yapılandırma görünümüdür; onları oradan ikinci kez
   * ÇEKMEK aynı gerçeğin iki kopyasını üretirdi (üstelik iki farklı pencereyle:
   * toplu uç pencere göndermiyor, ayrık uçlar 7 günü açıkça soruyor). Bu yüzden
   * gövde çekilmiyor, PAYLAŞILIYOR.
   *
   * `Durum` olarak iniyor, çıplak gövde olarak değil: "yoklama henüz dönmedi"
   * ile "alan gelmedi" ekranda ayrı cümlelerdir ve çıplak gövde ikisini tek
   * `undefined`e indirirdi.
   *
   * Sekiz görünümün sekizi de alır, yalnız biri okur — ve bu bilinçli: özelliği
   * tek görünüme özel yapmak, gövde tablosunu (`HafizaYuzey.tsx::GOVDELER`) tek
   * tipte tutulamaz hâle getirir ve sessiz yedeklere kapı açardı.
   */
  readonly toplu: Durum<HafizaGovdesi>;
}

/* ---------------------------------------------------------------------------
   SEKME KADEMESİ — GÖRÜNÜMÜN ALTI DA ADRESTEN TÜRER
   Bilgi Tabanı görünümü üç sekme taşıyor ve hangisinin açık olduğu İLK YAZIMDA
   yerel bir durumdaydı. Ölçülen sonuç (nihai inceleme Ö-1): "Hafıza → Bilgi
   Tabanı → Meridian dersleri" diyen bağ da, `#hafiza` yer imi de hep VARSAYILAN
   sekmeyi açıyordu — yani üçü de çalışıyor ama üçü de yanlış yere gidiyordu.
   Bu dosyanın kendi kuralı ("görünüm adreste yaşar") sekme için de geçerli.

   ÖLÇÜM ÖNCE YAPILDI (brief kalemi): `rota.tsx::hashiCoz` bölüm olarak yalnız
   yolun ÜÇÜNCÜ parçasını okuyordu ve dördüncüsünü DÜŞÜRÜYORDU; `gorunumCoz` da
   tek bir bölüm dizgesi alıyor. Yani mevcut mekanizma ikinci kademeyi TAŞIMIYOR.
   Bu yüzden kademe SORGUDA taşınır (`?sekme=`), yol parçasında değil: dördüncü
   bir yol parçası, yüzey kaydının saymadığı bir bölüm kimliği doğururdu
   (`alanlar.ts` bölüm sayacı · kırıntı · ⌘K anahtarları hepsi o uzaydan okur).
   --------------------------------------------------------------------------- */

/** Sekme kademesinin sorgu adı — adres yazan da okuyan da BURADAN alır. */
export const SEKME_SORGU_ADI = "sekme";

/** Bilgi Tabanı sekmeleri; İLKİ VARSAYILANDIR (üst yüzeyin sırası: sayfalar → modeller). */
export const HAFIZA_BILGI_SEKMELERI = ["sayfalar", "modeller", "dersler"] as const;

export type HafizaBilgiSekmesi = (typeof HAFIZA_BILGI_SEKMELERI)[number];

export const VARSAYILAN_BILGI_SEKMESI: HafizaBilgiSekmesi = "sayfalar";

/**
 * Adresteki sorgudan sekmeyi çözer. TANINMAYAN DEĞER VARSAYILANA DÜŞER — ve bu,
 * `gorunumCoz`un `null` sözleşmesinden BİLEREK farklı: bir görünüm kaybı ekranda
 * yazılması gereken bir şeydir (yüzey kaydında yok), bir sekme kaybı ise yalnız
 * bayat bir yer imidir ve sekme listesi zaten ekranda görünür duruyor.
 */
export function bilgiSekmesiCoz(sorgu: Readonly<Record<string, string>>): HafizaBilgiSekmesi {
  const ham = sorgu[SEKME_SORGU_ADI];
  return (HAFIZA_BILGI_SEKMELERI as readonly string[]).includes(ham ?? "")
    ? (ham as HafizaBilgiSekmesi)
    : VARSAYILAN_BILGI_SEKMESI;
}

/**
 * `/dashboard/memory/hafiza-bilgi` + `?sekme=…` — adres kurma TEK yerde.
 *
 * YALNIZ `sekme` TAŞINIR — VE BU BUGÜNKÜ ÖLÇÜMÜN SINIRIDIR (düzeltme turu 2, Y-11).
 * `rota.sorgu` genel bir sözlük ama bu kurucu tek anahtar biliyor: hash'te ikinci bir sorgu
 * anahtarı doğduğu gün sekme değiştirmek onu SESSİZCE düşürürdü. Bugün zararsız, çünkü panonun
 * ürettiği TEK sorgu anahtarı budur (ölçüldü 2026-09-03: `?` yazan başka bir adres kurucusu yok).
 * İkinci anahtar doğduğu gün burası büyür — mevcut sorguyu koruyup yalnız `sekme`yi değiştirir.
 * Bugün genelleştirmek, ölçülmemiş bir ihtiyaca kod yazmak olurdu.
 */
export function sekmeliYol(yol: string, sekme: HafizaBilgiSekmesi): string {
  return sekme === VARSAYILAN_BILGI_SEKMESI ? yol : `${yol}?${SEKME_SORGU_ADI}=${sekme}`;
}
