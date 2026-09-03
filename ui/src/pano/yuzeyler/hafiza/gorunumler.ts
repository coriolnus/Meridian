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

   BU DOSYA KAYITTAN NE İSTER: dokuz kimliğin her birinin `alanlar.ts`te KAYITLI
   olmasını. İstemediği tek şey SESSİZLİK — bir kimlik kayıttan düşerse sayfa onu
   gizlemez, "yüzey kaydında bulunamadı" diye ÇİZER (`HafizaYuzey.tsx`).
   Gizleseydi bir görünüm gezinmeden düşer ve kimse fark etmezdi; bu deponun
   defalarca ölçtüğü sessiz kayıp sınıfı tam olarak budur.

   SIRANIN TÜKETİCİSİ DEĞİŞTİ (2026-09-02, operatör kararı): yüzey içi kenar
   çubuğu kalktı ve sekiz durak küresel sol gezinmeye taşındı. Sıra oradan da
   KAYITTAN okunuyor (`alanlar.ts::YUZEYLER.memory.bolumler` → `gezinme.ts`),
   yani bu dizinin sözleşmesi değişmedi: adres çözümü ve varsayılan görünüm.

   DOKUZUNCU KİMLİK CP SIRASININ PARÇASI DEĞİL (TSK-118, 2026-09-03, operatör K8):
   `hafiza-dersler` yukarıdaki sekizin SONUNA eklendi, aralarına değil — CP'nin
   `sidebar.tsx`inde hiç karşılığı olmadığı için "birebir sıra" iddiası ilk sekiz
   için hâlâ geçerli, dokuzuncu ise Meridian'ın kendi eklediği (gerekçe `alanlar.ts`).
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
  // DOKUZUNCU DURAK CP PARİTESİNDEN DEĞİL (TSK-118, 2026-09-03, operatör K8):
  // Meridian'ın kendi eklediği, sırası CP `sidebar.tsx::navItems`ten OKUNMADI —
  // sekiz durağın SIRASI hâlâ birebir, bu yalnız SONA eklendi (gerekçe `alanlar.ts`).
  "hafiza-dersler",
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
 * Bir bölüm adresini (gerekirse sorgusuyla birlikte) görünüme çevirir. Tanınmayan
 * adreste `null` döner.
 *
 * ŞERH DÜZELTİLDİ (T2 yeniden-incelemesi): burada önce "çağıran yerel seçimini
 * korur" yazıyordu ve o cümle I-4 düzeltmesinden sonra YANLIŞ. Görünüm artık
 * yerel bir durumda değil ADRESTE yaşıyor (`HafizaYuzey.tsx` başlığı), yani
 * korunacak bir yerel seçim yok: `null` gören çağıran varsayılana — yüzeyin
 * adressiz ilk açılışıyla AYNI hâle — düşer. Bayat bir şerh, olmayan bir
 * şerhten kötüdür: okuyucu davranışı kaynaktan değil yorumdan öğrenir.
 *
 * `sorgu` PARAMETRESİ TSK-118'DE EKLENDİ (2026-09-03): tek başına bir bölüm
 * dizgesi artık yetmiyor, çünkü ESKİ sekme adresi (`hafiza-bilgi?sekme=dersler`)
 * bölüm+sorgu BİLEŞİMİDİR ve `ESKI_GORUNUM_ADRESLERI` yalnız çıplak bölüm
 * dizgelerini eşler. Köprü bu yüzden burada, tablodan AYRI bir kontrol.
 */
export function gorunumCoz(
  bolum: string | null | undefined,
  sorgu?: Readonly<Record<string, string>>,
): HafizaGorunumu | null {
  if (!bolum) return null;
  // ESKİ SEKME KÖPRÜSÜ (TSK-118, 2026-09-03, operatör K8): "Meridian dersleri"
  // TSK-118'e kadar Bilgi Tabanı'nın üçüncü sekmesiydi (`?sekme=dersler`); artık
  // kendi görünümü. Sekme adresi hâlâ dolaşıyor olabilir (sohbet hattının eski
  // bağı, operatörün kendi yer imleri) — sessizce "sayfalar"a düşürmek bir yer
  // imini KIRMAK olurdu (bu dosyanın kendi A-sınıfı arıza tanımı, yukarıda).
  // KÖPRÜ AŞAĞIDAKİ İKİ KONTROLDEN ÖNCE ÇALIŞIR: `hafiza-bilgi` kendisi hâlâ
  // geçerli bir görünüm kimliği, yani bu satır olmasaydı ikinci `if` onu zaten
  // "hafiza-bilgi" diye çözer ve sorgudaki `sekme=dersler` sessizce düşerdi.
  if (bolum === "hafiza-bilgi" && sorgu?.[SEKME_SORGU_ADI] === "dersler") return "hafiza-dersler";
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
 * Her görünüm gövdesinin ALDIĞI ŞEY — dokuzunda da aynı, bilerek.
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
   * Dokuz görünümün dokuzu da alır, yalnız biri okur — ve bu bilinçli: özelliği
   * tek görünüme özel yapmak, gövde tablosunu (`HafizaYuzey.tsx::GOVDELER`) tek
   * tipte tutulamaz hâle getirir ve sessiz yedeklere kapı açardı.
   */
  readonly toplu: Durum<HafizaGovdesi>;
}

/* ---------------------------------------------------------------------------
   SEKME KADEMESİ — GÖRÜNÜMÜN ALTI DA ADRESTEN TÜRER
   Bilgi Tabanı görünümü İKİ sekme taşır (sayfalar · modeller) ve hangisinin açık
   olduğu İLK YAZIMDA yerel bir durumdaydı. Ölçülen sonuç (nihai inceleme Ö-1):
   "Hafıza → Bilgi Tabanı → Meridian dersleri" diyen bağ da, `#hafiza` yer imi de
   hep VARSAYILAN sekmeyi açıyordu — yani üçü de çalışıyor ama üçü de yanlış yere
   gidiyordu (o turda ÜÇÜNCÜ sekme "dersler"di). Bu dosyanın kendi kuralı
   ("görünüm adreste yaşar") sekme için de geçerli.

   ÜÇÜNCÜ SEKME EMEKLİ OLDU (TSK-118, 2026-09-03, operatör K8): "dersler" artık
   bir sekme değil, kendi görünümü (`hafiza-dersler`, `alanlar.ts::YUZEYLER.
   memory.bolumler`). Aşağıdaki liste bu yüzden "dersler" değerini artık
   TANIMIYOR — `bilgiSekmesiCoz` tanınmayan bir sorgu değerini varsayılana
   düşürür (kendi sözleşmesi, aşağıda). Eski sekme adresi (`hafiza-bilgi?sekme=
   dersler`) hâlâ dolaşabilir; o adres bu düşüşten ÖNCE `gorunumCoz` köprüsüyle
   (yukarıda) doğru görünüme çözülür — bu liste BİLEREK "dersler"i geri almadı.

   ÖLÇÜM ÖNCE YAPILDI (brief kalemi): `rota.tsx::hashiCoz` bölüm olarak yalnız
   yolun ÜÇÜNCÜ parçasını okuyordu ve dördüncüsünü DÜŞÜRÜYORDU; `gorunumCoz` da
   tek bir bölüm dizgesi alıyordu (TSK-118: ikinci parametre olarak sorguyu da
   alıyor, yalnız köprü için). Bu yüzden kademe SORGUDA taşınır (`?sekme=`), yol
   parçasında değil: dördüncü bir yol parçası, yüzey kaydının saymadığı bir bölüm
   kimliği doğururdu (`alanlar.ts` bölüm sayacı · kırıntı · ⌘K anahtarları hepsi o
   uzaydan okur).
   --------------------------------------------------------------------------- */

/** Sekme kademesinin sorgu adı — adres yazan da okuyan da BURADAN alır. */
export const SEKME_SORGU_ADI = "sekme";

/** Bilgi Tabanı sekmeleri; İLKİ VARSAYILANDIR (üst yüzeyin sırası: sayfalar → modeller).
 *  ÜÇÜNCÜ DEĞER YOK (TSK-118, 2026-09-03): "dersler" kendi görünümüne taşındı — gerekçe
 *  yukarıdaki dosya-başlığı şerhinde. */
export const HAFIZA_BILGI_SEKMELERI = ["sayfalar", "modeller"] as const;

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
