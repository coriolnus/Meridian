"use client";

/* ============================================================================
   KABUK — şablonun `(main)/dashboard/layout.tsx`inin karşılığı
   ----------------------------------------------------------------------------
   Şablonun düzeni sunucuda kuruluyordu: `await cookies()` ile tercihler okunur,
   `SidebarProvider` doğru açıklıkla doğardı. Burada sunucu React render etmiyor —
   tercihleri ÖNYÜKLEYİCİ (meridian/web/pano-onyuk.js) belge niteliklerine yazar,
   React onları DOM'dan okur. Sonuç aynı, sıçrama da yok; fark, kararın nerede
   verildiği.

   `--sidebar-width` ve `data-content-layout` kancaları şablondan AYNEN alındı:
   yerleşim denetimlerinin (LayoutControls) çalışması bu iki satıra bağlı.
   ============================================================================ */
import type { ReactNode } from "react";

import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Toaster } from "@/components/ui/sonner";
import { cn } from "@/lib/utils";

import { BugunSaglayici } from "./durum";
import { AppSidebar } from "./kabuk/app-sidebar";
import { Ustbar } from "./kabuk/Ustbar";
import { RotaSaglayici } from "./rota";

export function Kabuk({ children }: { children: ReactNode }) {
  return (
    <RotaSaglayici>
      <BugunSaglayici>
        <SidebarProvider
          defaultOpen={document.cookie.split("; ").includes("sidebar_state=false") === false}
          style={{ "--sidebar-width": "calc(var(--spacing) * 68)" } as React.CSSProperties}
        >
          <AppSidebar />
          <SidebarInset
            className={cn(
              "[html[data-content-layout=centered]_&>*]:mx-auto",
              "[html[data-content-layout=centered]_&>*]:w-full",
              "[html[data-content-layout=centered]_&>*]:max-w-screen-2xl",
              "peer-data-[variant=inset]:border",
              "[--dashboard-header-height:--spacing(12)]",
              "min-w-0 overflow-x-clip",
            )}
          >
            <Ustbar />
            <div className="min-h-0 min-w-0 flex-1 overflow-x-hidden p-4 md:p-6">{children}</div>
          </SidebarInset>
        </SidebarProvider>
        <Toaster />
      </BugunSaglayici>
    </RotaSaglayici>
  );
}
