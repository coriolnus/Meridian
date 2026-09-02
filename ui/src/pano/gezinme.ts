/* ============================================================================
   KENAR ÇUBUĞU MADDELERİ — `YUZEYLER`den TÜRETİLİR, elle yazılmaz
   ----------------------------------------------------------------------------
   Şablonun `sidebar-items.ts`i elle yazılmış sabit bir listeydi ve her yüzeyin
   adı orada, yolu başka yerde, içeriği üçüncü bir yerde duruyordu. Burada liste
   bir TÜREVDİR: bir bölüm eklemek `alanlar.ts`e bir satır yazmaktır; gezinme,
   yönlendirme, arama ve sayfa gövdesi dördü birden takip eder.

   `sidebar-items.ts`teki `sidebarItems` sabiti BU YÜZDEN ÖLÜDÜR: oradan yalnız TİPLER
   (`NavGroup`/`NavMainItem`) alınıyor, liste hiçbir yerde tüketilmiyor (ölçüldü
   2026-09-01: tek tüketici `search-dialog.tsx` ve o da `gezinmeGruplari`yi alıyor).
   Yeni bir yüzeyi oraya da yazmak, ekranda hiçbir şey değiştirmeyen ama sessizce
   ayrışacak İKİNCİ bir kopya üretirdi — tek-kaynak yasasının kapattığı sınıf.

   GRUPLAMA ŞABLONUNKİDİR (Panolar / Sayfalar) — operatörün seçtiği ağaç bu.
   ============================================================================ */
import { YUZEYLER, YUZEY_ANAHTARLARI, yuzeyYolu, type Yuzey, type YuzeyAnahtari } from "./alanlar";
import type { NavGroup, NavMainItem } from "@/navigation/sidebar/sidebar-items";

function madde(anahtar: YuzeyAnahtari, altBolumleriAc: boolean): NavMainItem {
  /* TİP ANOTASYONU ŞART, SÜS DEĞİL: `YUZEYLER` `as const` ile donuk ve her
     yüzeyin literal tipi yalnız KENDİ yazdığı alanları taşır — isteğe bağlı
     `altBolumNav` alanı, onu yazmayan on beş yüzeyin tipinde HİÇ yoktur ve
     birleşim üstünde okunamaz. `Yuzey` sözleşmesine daraltmak, kaydın kendi
     arayüzünü okumaktır. */
  const y: Yuzey = YUZEYLER[anahtar];
  const temel = { id: anahtar, title: y.baslik, icon: y.ikon };

  // BÖLÜMSÜZ YÜZEY DÜZ BAĞ OLUR: açıldığında hiçbir şey göstermeyen bir ok koymak,
  // tıklandığında boşluk açan bir vaat olurdu.
  //
  // KENDİ GEZİNMESİ OLAN YÜZEY DE DÜZ BAĞ OLUR (`altBolumNav: "yuzey-ici"`,
  // 2026-09-02 operatör görsel turu): Hafıza'nın sekiz durağı yüzeyin KENDİ kenar
  // çubuğunda zaten çiziliyordu ve küresel çubuk aynı listeyi ikinci kez asıyordu
  // — çift gezinme. Kararı burada VERMİYORUZ, kayıttan OKUYORUZ: hangi yüzeyin
  // kendi gezinmesi olduğunu bilen tek yer yüzey kaydıdır ve o bilgiyi ikinci kez
  // (bu dosyada bir yüzey adı listesi olarak) yazmak, sessizce ayrışacak bir kopya
  // üretirdi. Bölümler kayıtta DURUR: palet, kırıntı ve derin bağlar okumaya devam
  // eder — susturulan yalnız bu ağaçtır.
  if (y.bolumler.length === 0 || (!altBolumleriAc && y.altBolumNav === "yuzey-ici")) {
    return { ...temel, url: yuzeyYolu(anahtar) };
  }

  return {
    ...temel,
    subItems: y.bolumler.map((b) => ({
      id: `${anahtar}-${b.kimlik}`,
      title: b.baslik,
      url: yuzeyYolu(anahtar, b.kimlik),
      icon: b.ikon,
    })),
  };
}

const grupla = (ad: "Panolar" | "Sayfalar", altBolumleriAc: boolean) =>
  YUZEY_ANAHTARLARI.filter((a) => YUZEYLER[a].grup === ad).map((a) => madde(a, altBolumleriAc));

/** KENAR ÇUBUĞUNUN AĞACI — `altBolumNav` beyanına UYAR. */
export const gezinmeGruplari: NavGroup[] = [
  { id: 1, label: "Panolar", items: grupla("Panolar", false) },
  { id: 2, label: "Sayfalar", items: grupla("Sayfalar", false) },
];

/* KOMUT PALETİNİN AĞACI — BEYANI UMURSAMAZ, VE BU BİR KOPYA DEĞİL AYNI ÜRETİCİDİR.
   İki tüketicinin iki ayrı sorusu var: kenar çubuğu "operatör buraya nereden
   TIKLAR" diye sorar, palet "operatör bu adı YAZARSA nereye gitmeli" diye. Bir
   yüzeyin alt gezinmesi kendi gövdesindeyse çubuk onu ikinci kez ASMAMALI ama
   palet onu unutmamalı: `#/dashboard/memory/hafiza-recall` gerçek bir adrestir ve
   ⌘K onu bulamazsa operatör sekiz görünüme yalnız fareyle ulaşabilirdi.

   ÖLÇÜLEN RİSK, VARSAYIM DEĞİL: palet maddelerini `search-dialog.tsx`
   `gezinmeGruplari`den türetiyor ve alt maddesi olmayan bir yüzey için YALNIZ
   yüzeyin kendisini listeliyor. Beyan tek ağaca uygulansaydı sekiz görünüm
   paletten SESSİZCE düşerdi — hata vermeden, yalnız aramada bulunmayarak. */
export const paletGruplari: NavGroup[] = [
  { id: 1, label: "Panolar", items: grupla("Panolar", true) },
  { id: 2, label: "Sayfalar", items: grupla("Sayfalar", true) },
];
