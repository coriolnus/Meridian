/**
 * bayat.tsx — `BayatSerit` / `YukleniyorIskeleti` KOMŞU KOPYALARININ TEK TANIMI
 * (TSK-121, 2026-09-03).
 *
 * ÖLÇÜM: yalnız `analiz/ortak.tsx` ve `ogrenme/ortak.tsx` bu ikiliyi taşıyordu — TSK-113'ün
 * "ogrenme ≡ analiz" bulgusuyla AYNI çift. Gövdeler BYTE-BİREBİR (tek boşluk-sarma farkı
 * hariç, biçim aracının kararı). `YukleniyorIskeleti` iki dosyada da dışa aktarılmıştı ama
 * DIŞ hiçbir dosyadan import edilmiyordu (yalnız kendi `kapiKur(...)` çağrısının `iskelet`
 * dalında kullanılıyordu) — tüketici = 0 dış, 2 iç. Bu yüzden burada dışa aktarılır ama iki
 * yüzey de yalnız İTHAL eder, YENİDEN dışa aktarmaz (ölçülen dış tüketici sıfır kaldığı sürece
 * gerek yok — çıkarsa re-export eklenir).
 */
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TriangleAlert } from "lucide-react";

export function YukleniyorIskeleti({ yukseklik = "h-40" }: { yukseklik?: string }) {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className={cn("w-full", yukseklik)} />
    </div>
  );
}

/** Tazeleme düştü ama elde ESKİ veri var — çizilir, "taze" DENMEZ. */
export function BayatSerit({ hata, zaman }: { hata: string; zaman: Date | null }) {
  return (
    <div className="mb-3 flex items-start gap-2 rounded-md border border-uyari-h bg-uyari-t px-3 py-2">
      <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-uyari" aria-hidden />
      <p className="min-w-0 break-words text-uyari text-xs leading-relaxed">
        Tazeleme düştü — aşağıdaki sayılar{" "}
        {zaman ? `${zaman.toLocaleTimeString("tr-TR")} okumasından` : "önceki bir okumadan"} kalma, ŞU ANI göstermiyor.{" "}
        {hata}
      </p>
    </div>
  );
}
