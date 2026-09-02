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
   olmasını. İstemediği tek şey SESSİZLİK — bir kimlik kayıttan düşerse kenar
   çubuğu onu gizlemez, "kayıtta yok" diye ÇİZER (`HafizaYuzey.tsx::Kenar`).
   Gizleseydi bir görünüm gezinmeden düşer ve kimse fark etmezdi; bu deponun
   defalarca ölçtüğü sessiz kayıp sınıfı tam olarak budur.
   ============================================================================ */
import { YUZEYLER, type Bolum } from "../../alanlar";

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

   AMA YÖNLENDİRME BİR TELAFİ DEĞİL: `operasyon` ve `kota`nın İÇERİĞİ bu turda
   çizilmiyor (Görev 3). Gideceği ekran bunu kendi ağzıyla söylüyor — sessizce
   boş bir sayfaya düşmüyor.
   --------------------------------------------------------------------------- */
export const ESKI_GORUNUM_ADRESLERI: Readonly<Record<string, HafizaGorunumu>> = {
  "hafiza-bankalar": "hafiza-anasayfa",
  "hafiza-operasyon": "hafiza-yapilandirma",
  "hafiza-kota": "hafiza-yapilandirma",
};

/**
 * Bir bölüm adresini görünüme çevirir. Tanınmayan adres `null` döner —
 * VARSAYILANA DÜŞMEZ: çağıran o zaman yerel seçimini korur, yani yanlış bir
 * adres kullanıcının açık olan görünümünü altından çekmez.
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
}
