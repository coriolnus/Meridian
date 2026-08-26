"use client";

/* ============================================================================
   KENAR ÇUBUĞU — şablonun `AppSidebar`ı, Meridian'ın bilgi mimarisiyle
   ----------------------------------------------------------------------------
   Şablondan GELEN: `Sidebar` iskeleti, tercih deposundan okunan `variant` /
   `collapsible`, ikon rayına daralma. Bunlar aynen duruyor.

   DEĞİŞEN İKİ ŞEY:
     · Maddeler `sidebarItems` sabit listesinden değil, `ALANLAR` kaydından
       TÜRETİLİYOR (pano/gezinme.ts) — üç tabloyu elle senkron tutma sınıfı
       ortadan kalkıyor.
     · Ayakta `NavUser` + `SupportCard` yerine HESAP KUTUSU var. İlki sahte bir
       kullanıcı kartıydı, ikincisi şablonun kendi reklamı; ikisi de bu üründe
       okuyucusuz yazımdı.
   ============================================================================ */
import { useShallow } from "zustand/react/shallow";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { APP_CONFIG } from "@/config/app-config";
import { usePreferencesStore } from "@/stores/preferences/preferences-provider";

import { useBugun } from "../durum";
import { gezinmeGruplari } from "../gezinme";
import Link from "../rota";
import { HesapKutusu } from "./HesapKutusu";
import { NavMain } from "./nav-main";
import { MarkaIsareti } from "@/pano/kabuk/MarkaIsareti";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { sidebarVariant, sidebarCollapsible, isSynced } = usePreferencesStore(
    useShallow((s) => ({
      sidebarVariant: s.values.sidebar_variant,
      sidebarCollapsible: s.values.sidebar_collapsible,
      isSynced: s.isSynced,
    })),
  );
  const { veri: bugun, hata } = useBugun();

  const variant = isSynced ? sidebarVariant : props.variant;
  const collapsible = isSynced ? sidebarCollapsible : props.collapsible;

  return (
    <Sidebar {...props} variant={variant} collapsible={collapsible}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link href="/dashboard/default">
                {/* Marka işareti. 2026-08-26'ya kadar burada bir NOKTA vardı ve şerhi
                    sebebini yazıyordu: "Meridian'ın kendi işareti yok, lucide kataloğundan
                    rastgele bir glif seçmek hiçbir şey anlatmayan bir süs olurdu." Nokta
                    bilinçli bir YER TUTUCUYDU ve dayandığı önerme o tarihte yanlışlandı —
                    operatör kendi işaretini tasarladı (C · M Monogramı v0). Yer tutucu,
                    gerekçesi düştüğü için kalkıyor. Aynı geometri sekme ikonunda da yaşıyor
                    (meridian/web/favicon.svg); ayrışmayı test_marka_isareti_v321 kapatır. */}
                <MarkaIsareti className="size-4 shrink-0" />
                <span className="font-semibold text-base">{APP_CONFIG.name}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={gezinmeGruplari} />
      </SidebarContent>
      <SidebarFooter>
        <HesapKutusu bugun={bugun} hata={hata} />
      </SidebarFooter>
    </Sidebar>
  );
}
