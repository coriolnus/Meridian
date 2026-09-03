/**
 * bildiri.tsx — `Bildiri` KOMŞU KOPYASININ TEK TANIMI (TSK-121, 2026-09-03).
 *
 * ÖLÇÜM: `ajan/ortak.tsx`, `analiz/ortak.tsx`, `ogrenme/ortak.tsx` üç ayrı `Bildiri` gövdesi
 * taşıyordu ve gövde (JSX return) ÜÇÜNDE de birebir aynıydı — `div.border-dashed` + `Ikon` +
 * `p.font-medium` + `p.text-xs`. Fark yalnız PROP İMZASINDAYDI: ajan `{ikon, baslik, govde,
 * uyari: boolean}`, analiz/ogrenme `{ikon, baslik, metin, tonu: "uyari"|"notr"}`. TSK-113 bu
 * kopyayı ölçmüş ve KAPSAM DIŞI bırakmıştı (`parcalar/kapi.tsx` şerhi: "o ayrı bir kalem").
 *
 * DÜZ PAYLAŞIM YETERLİ — `kapiKur` gibi bir kabuk-enjeksiyonu GEREKMEZ: markup zaten birebir,
 * tek iş prop imzasını normalize etmekti. Ajan'ın eski `{govde, uyari}` çiftini ortak
 * `{metin, tonu}` sözleşmesine ÇAĞRI YERİNDE eşlemek yeter (`metin=govde`, `tonu=uyari?"uyari":
 * "notr"`) — bileşenin gövdesine dokunmadan.
 *
 * TÜKETİCİ ÖLÇÜLDÜ: üç dosyanın hiçbiri `Bildiri`yi DIŞARI aktarmıyordu (yalnız kendi
 * `kapiKur(...)` çağrısı içinde kullanılıyordu, tüketici = 0 dış dosya). Bu yüzden üç yüzey de
 * artık yalnız İTHAL EDER, yeniden dışa AKTARMAZ.
 */
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export interface BildiriOzellikleri {
  readonly ikon: LucideIcon;
  readonly baslik: string;
  readonly metin: string;
  readonly tonu: "uyari" | "notr";
}

export function Bildiri({ ikon: Ikon, baslik, metin, tonu }: BildiriOzellikleri) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border border-dashed p-4",
        tonu === "uyari" ? "border-destructive/40 bg-destructive/5" : "border-border bg-muted/30",
      )}
    >
      <Ikon
        className={cn("mt-0.5 size-4 shrink-0", tonu === "uyari" ? "text-destructive" : "text-muted-foreground")}
        aria-hidden
      />
      <div className="min-w-0">
        <p className="font-medium text-sm">{baslik}</p>
        <p className="mt-0.5 break-words text-muted-foreground text-xs leading-relaxed">{metin}</p>
      </div>
    </div>
  );
}
