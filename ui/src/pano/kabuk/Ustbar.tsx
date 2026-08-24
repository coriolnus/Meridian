"use client";

/* ============================================================================
   ÜST BAR — şablonun başlığı + Meridian'ın durum bandı
   ----------------------------------------------------------------------------
   ŞABLONDAN GELEN: yapışkan başlık, `SidebarTrigger`, arama (⌘K), yerleşim
   denetimleri, tema anahtarı. Yeri ve davranışı aynen korunuyor.

   ŞABLONDAN DÜŞEN: `AccountSwitcher` ve `GitHubRepositoriesMenu`. Meridian tek
   operatörlü ve hesap değiştirme diye bir kavramı yok; ikisi de basıldığında
   hiçbir şey yapmayan süs olurdu.

   MERIDIAN'DAN GELEN: DURUM HAPI. Sistemin o anki hâli — durduruldu / kesici
   tetikli / sakin — üst barda ve HER yüzeyde aynı yerde durur. Eski panoda bu
   `#statuspill`di ve kas hafızası oraya bağlı.

   KRİZ KOLLARI (HALT · Cancel-Open · Flatten · Halt-Learning) BU TURDA BURADA
   DEĞİL ve bu bilinçli bir eksiklik, bir unutma değil: dördü de geri alınamaz
   icra emri veriyor (Flatten TÜM pozisyonları kapatır) ve yarım bağlanmış bir
   kol, basıldığında ne yaptığı belirsiz bir koldur. Canlı olan eski panoda
   çalışmaya devam ediyorlar; buraya kendi turlarında, çift onay ve çiviyle
   gelecekler. Durum hapı bu yüzden yalnız OKUR — ve HALT çekiliyken operatörü
   kolun gerçekten bulunduğu yere gönderir.
   ============================================================================ */
import { AlertTriangle, CircleDot, OctagonPause } from "lucide-react";

import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { cn } from "@/lib/utils";

import { YUZEYLER, yuzeyYolu } from "../alanlar";
import { useBugun } from "../durum";
import Link, { useRota } from "../rota";
import { LayoutControls } from "./layout-controls";
import { SearchDialog } from "./search-dialog";
import { ThemeSwitcher } from "./theme-switcher";

function DurumHapi() {
  const { veri, hata, oturumDustu, yukleniyor } = useBugun();

  // DÖRT AYRI HÂL, DÖRT AYRI CÜMLE. Eskiden "okunamadı" ile "sakin" aynı sönük
  // stille çıkabiliyordu; okunamayan bir sistemi sakin sanmak en pahalı yanlış.
  const hal = oturumDustu
    ? { metin: "oturum düştü", sinif: "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400", Ikon: AlertTriangle, yol: null }
    : hata
      ? { metin: "durum okunamadı", sinif: "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400", Ikon: AlertTriangle, yol: null }
      : veri == null || veri.halted === undefined
        // BOŞ GÖVDE "SAKİN" DEĞİLDİR. `{}` dönen bir uçta `veri.halted` undefined olur ve
        // yalancı bir mantık onu "durdurulmamış" diye okurdu — yani ÖLÇÜLMEMİŞ bir sistemi
        // sakin ilan ederdi. Alanın VARLIĞI aranıyor, doğruluğu değil.
        ? { metin: yukleniyor ? "okunuyor…" : "durum ölçülemedi", sinif: "border-border bg-muted text-muted-foreground", Ikon: CircleDot, yol: null }
        : veri.halted
          ? { metin: "DURDURULDU", sinif: "border-destructive/50 bg-destructive/10 text-destructive", Ikon: OctagonPause, yol: "/dashboard/roles/mudahale" }
          : veri.heartbeat?.breaker_tripped
            ? { metin: "kesici tetikli", sinif: "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400", Ikon: AlertTriangle, yol: "/dashboard/roles/mudahale" }
            : { metin: "sakin", sinif: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400", Ikon: CircleDot, yol: null };

  const govde = (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-medium text-xs", hal.sinif)}>
      <hal.Ikon className="size-3.5" aria-hidden />
      {hal.metin}
    </span>
  );

  // TIKLANABİLİRLİK BİR HÜKÜM TAŞIR: yalnız YAPILACAK BİR ŞEY varken bağ olur.
  // "sakin" hâli bir yere götürmez — götürseydi operatör her bakışta bir eylem
  // bekleniyormuş gibi okurdu.
  return (
    <div role="status" aria-live="polite">
      {hal.yol ? <Link href={hal.yol} title="Müdahale koluna git">{govde}</Link> : govde}
    </div>
  );
}

export function Ustbar() {
  const { yuzey, bolum } = useRota();
  const a = YUZEYLER[yuzey];
  const b = a.bolumler.find((x) => x.kimlik === bolum);

  return (
    <header
      className={cn(
        "flex h-12 shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12",
        "[html[data-navbar-style=sticky]_&]:sticky [html[data-navbar-style=sticky]_&]:top-0 [html[data-navbar-style=sticky]_&]:z-50 [html[data-navbar-style=sticky]_&]:overflow-hidden [html[data-navbar-style=sticky]_&]:rounded-t-[inherit] [html[data-navbar-style=sticky]_&]:bg-background/50 [html[data-navbar-style=sticky]_&]:backdrop-blur-md",
      )}
    >
      <div className="flex w-full items-center justify-between gap-2 px-4 lg:px-6">
        <div className="flex min-w-0 items-center gap-1 lg:gap-2">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4 data-[orientation=vertical]:self-center" />
          <Breadcrumb className="hidden min-w-0 md:block">
            <BreadcrumbList>
              <BreadcrumbItem>
                {b ? <BreadcrumbLink href={`#${yuzeyYolu(yuzey)}`}>{a.baslik}</BreadcrumbLink> : <BreadcrumbPage>{a.baslik}</BreadcrumbPage>}
              </BreadcrumbItem>
              {b && (
                <>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <BreadcrumbPage>{b.baslik}</BreadcrumbPage>
                  </BreadcrumbItem>
                </>
              )}
            </BreadcrumbList>
          </Breadcrumb>
          <SearchDialog />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <DurumHapi />
          <LayoutControls />
          <ThemeSwitcher />
        </div>
      </div>
    </header>
  );
}
