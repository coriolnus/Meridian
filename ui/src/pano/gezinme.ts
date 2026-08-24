/* ============================================================================
   KENAR ÇUBUĞU MADDELERİ — `YUZEYLER`den TÜRETİLİR, elle yazılmaz
   ----------------------------------------------------------------------------
   Şablonun `sidebar-items.ts`i elle yazılmış sabit bir listeydi ve on beş yüzeyin
   adı orada, yolu başka yerde, içeriği üçüncü bir yerde duruyordu. Burada liste
   bir TÜREVDİR: bir bölüm eklemek `alanlar.ts`e bir satır yazmaktır; gezinme,
   yönlendirme, arama ve sayfa gövdesi dördü birden takip eder.

   GRUPLAMA ŞABLONUNKİDİR (Panolar / Sayfalar) — operatörün seçtiği ağaç bu.
   ============================================================================ */
import { YUZEYLER, YUZEY_ANAHTARLARI, yuzeyYolu, type YuzeyAnahtari } from "./alanlar";
import type { NavGroup, NavMainItem } from "@/navigation/sidebar/sidebar-items";

function madde(anahtar: YuzeyAnahtari): NavMainItem {
  const y = YUZEYLER[anahtar];
  const temel = { id: anahtar, title: y.baslik, icon: y.ikon };

  // BÖLÜMSÜZ YÜZEY DÜZ BAĞ OLUR: açıldığında hiçbir şey göstermeyen bir ok koymak,
  // tıklandığında boşluk açan bir vaat olurdu.
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
