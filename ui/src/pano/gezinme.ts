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
import { YUZEYLER, YUZEY_ANAHTARLARI, yuzeyYolu, type YuzeyAnahtari } from "./alanlar";
import type { NavGroup, NavMainItem } from "@/navigation/sidebar/sidebar-items";

function madde(anahtar: YuzeyAnahtari): NavMainItem {
  const y = YUZEYLER[anahtar];
  const temel = { id: anahtar, title: y.baslik, icon: y.ikon };

  // BÖLÜMSÜZ YÜZEY DÜZ BAĞ OLUR: açıldığında hiçbir şey göstermeyen bir ok koymak,
  // tıklandığında boşluk açan bir vaat olurdu.
  //
  // BÖLÜMÜ OLAN HER YÜZEY AÇILIR MADDEDİR — İSTİSNASI YOK (operatör kararı
  // 2026-09-02). Bir tur boyunca `altBolumNav: "yuzey-ici"` diye bir istisna
  // vardı: kendi kenar çubuğunu taşıyan yüzey (Hafıza) küresel çubukta düz bağ
  // oluyordu. Operatör dağıtımda gördü ve TERSİNİ seçti — alt başlıklar sol
  // nav'da, Hafıza'nın altında; yüzey içindeki ikinci sütun kalktı. İstisna
  // ortadan kalkınca mekanizma da kalktı (tek kullanıcısı oydu; ölü kod yok) ve
  // bu dosya tek ağaç üretmeye döndü — palet de o ağacı okuyor.
  if (y.bolumler.length === 0) return { ...temel, url: yuzeyYolu(anahtar) };

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

const grupla = (ad: "Panolar" | "Sayfalar") =>
  YUZEY_ANAHTARLARI.filter((a) => YUZEYLER[a].grup === ad).map(madde);

export const gezinmeGruplari: NavGroup[] = [
  { id: 1, label: "Panolar", items: grupla("Panolar") },
  { id: 2, label: "Sayfalar", items: grupla("Sayfalar") },
];
