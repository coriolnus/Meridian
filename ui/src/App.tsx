/* ============================================================================
   PİLOT YÜZEYİ — shadcn "application shell" bloğunun KENDİSİ, Meridian jetonlarıyla
   ----------------------------------------------------------------------------
   Kabuk artık elle çizilmiyor: `npx shadcn add sidebar breadcrumb` ile gelen RESMÎ
   bileşenler kullanılıyor (SidebarProvider/Sidebar/SidebarInset/SidebarTrigger +
   Breadcrumb). Operatör bloğu shadcnblocks.com'da göremedi (üçüncü taraf paywall);
   burada bloğun grameri BİZİM paletimizle ve BİZİM verimizle çiziliyor.

   ÖLÇÜLEN İHLAL VE DÜZELTMESİ (stil.css'te yazılı): CLI kendi paletini enjekte etti ve
   iki rengi rezerve NAV bandımızın (255-272°) içine düştü. Palet silindi, shadcn'in
   `--sidebar-*` jetonları rol katmanına bağlandı. Bu dosyada çıplak hex ve Tailwind
   hazır renk skalası GEÇMEZ — çivi test_ui_pilot_kapilari_v286::test_G1b.
   ============================================================================ */
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Activity,
  CalendarDays,
  FileText,
  GitBranch,
  HeartPulse,
  LineChart,
  Workflow,
} from "lucide-react";

import { OlcumHucresi } from "./meridian/OlcumHucresi";
import { azOrnek, gurultuBandiAciklamasi, kanitOrani, yonSinifi } from "./meridian/olcum";
import type { Olcum } from "./meridian/olcum";

const RAY = [
  {
    grup: "Karar",
    ogeler: [
      { ad: "Bugün", yol: "/#bugun", Ikon: CalendarDays },
      { ad: "Karar zinciri", yol: "/#karar", Ikon: GitBranch },
      { ad: "Analiz", yol: "/#analiz", Ikon: LineChart },
    ],
  },
  {
    grup: "İşletme",
    ogeler: [
      { ad: "Portföy", yol: "/#portfoy", Ikon: Activity },
      { ad: "Sağlık", yol: "/#saglik", Ikon: HeartPulse },
    ],
  },
  {
    grup: "Belge",
    ogeler: [
      { ad: "İş akışı", yol: "/pilot-workflow.html", Ikon: Workflow, secili: true },
      { ad: "Runbook", yol: "/runbook", Ikon: FileText },
    ],
  },
] as const;

/* SAYILAR SABİT VE BU BİLEREK: pilot bir VERİ yüzeyi değil, bir GRAMER denemesi.
   Canlı uca bağlanmadı — bağlansaydı yanlış bir sayıyı canlı sanma riski doğardı. */
const ORNEKLER: {
  etiket: string;
  olcum: Olcum;
  n: number;
  ortalama: number | null;
  meta: string;
  bicim?: (d: number) => string;
}[] = [
  {
    etiket: "exhaustion_hammer · yükseliş",
    olcum: { deger: 0.21 },
    n: 190,
    ortalama: 0.21,
    meta: "190 işlem · %27 tutan",
    bicim: (d) => `${d > 0 ? "+" : ""}${d.toFixed(2)}R`,
  },
  {
    etiket: "exhaustion_hammer · yatay",
    olcum: { deger: 0.12 },
    n: 38,
    ortalama: 0.12,
    meta: "38 işlem · %34 tutan",
    bicim: (d) => `${d > 0 ? "+" : ""}${d.toFixed(2)}R`,
  },
  {
    etiket: "pullback · yükseliş",
    olcum: { deger: -0.79 },
    n: 5,
    ortalama: -0.79,
    meta: "5 işlem · %0 tutan",
    bicim: (d) => `${d > 0 ? "+" : ""}${d.toFixed(2)}R`,
  },
  {
    etiket: "pullback · düşüş",
    olcum: { deger: null, neden: "bu kesitte hiç işlem kapanmadı — ortalama tanımsız" },
    n: 0,
    ortalama: null,
    meta: "ekilmemiş parsel",
  },
];

export function App() {
  return (
    <SidebarProvider>
      <Sidebar collapsible="icon">
        <SidebarHeader>
          <div className="flex items-center gap-2 px-2 py-1.5">
            <span className="inline-block size-2 shrink-0 rounded-cip bg-nav" aria-hidden />
            <span className="truncate text-[length:var(--t-body)] font-semibold text-murekkep group-data-[collapsible=icon]:hidden">
              Meridian
            </span>
          </div>
        </SidebarHeader>

        <SidebarContent>
          {RAY.map((g) => (
            <SidebarGroup key={g.grup}>
              {/* E1 — MİKRO BÖLÜM BAŞLIĞI: 11px · 600 · .04em · UPPERCASE · --tx3 */}
              <SidebarGroupLabel className="font-semibold uppercase tracking-[.04em] text-murekkep-3">
                {g.grup}
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {g.ogeler.map((o) => (
                    <SidebarMenuItem key={o.ad}>
                      <SidebarMenuButton
                        asChild
                        isActive={"secili" in o && o.secili}
                        tooltip={o.ad}
                      >
                        <a href={o.yol}>
                          <o.Ikon />
                          <span>{o.ad}</span>
                        </a>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          ))}
        </SidebarContent>
        <SidebarRail />
      </Sidebar>

      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b border-cizgi px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="/">Meridian</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href="/#analiz">Belge</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>İş akışı</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>

        <main className="flex flex-1 flex-col gap-4 p-4">
          <div>
            <h1 className="text-[length:var(--t-h)] font-semibold text-murekkep">
              Kurulum × rejim
            </h1>
            <p className="mt-1 max-w-[65ch] text-[length:var(--t-body)] text-murekkep-2">
              shadcn'in resmî <span className="font-mono">sidebar</span> +{" "}
              <span className="font-mono">breadcrumb</span> bloğu, Meridian jetonlarıyla.
              Kenar çubuğu ikon-rayına daralır; hücrelerin hepsi tek bileşenden doğuyor ve
              renk yalnız rol jetonundan geliyor.
            </p>
          </div>

          {/* DÖRTLÜ SAYISAL BAND — TEK GRAMER: kapalı kap + paylaşılan kenar + gap:0 */}
          <div className="overflow-hidden rounded-kart border border-cizgi bg-kart">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
              {ORNEKLER.map((o, i) => (
                <div
                  key={o.etiket}
                  className={
                    i < ORNEKLER.length - 1
                      ? "border-b border-cizgi lg:border-b-0 lg:border-r"
                      : ""
                  }
                >
                  <OlcumHucresi
                    etiket={o.etiket}
                    olcum={o.olcum}
                    bicim={o.bicim}
                    meta={o.meta}
                    yon={yonSinifi(o.ortalama, o.n)}
                    kanit={
                      o.n > 0
                        ? { oran: kanitOrani(o.n), payda: "işlem sayısı · log ölçek, n=55 dolu" }
                        : undefined
                    }
                    rozet={o.n > 0 && azOrnek(o.n) ? "az_ornek" : undefined}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* GÜRÜLTÜ BANDI LEJANTI — operatörün "aynı anlam iki renkte" okumasının cevabı.
              Kural doğruydu ama EKRANDA AÇIKLANMIYORDU; kuralı değil görünürlüğünü düzeltiyoruz. */}
          <section className="rounded-serit bg-zemin-2 p-4" aria-label="Renk kuralı">
            <div className="mb-2 text-[length:var(--t-cap)] font-semibold uppercase tracking-[.04em] text-murekkep-3">
              Renk neden bazı hücrelerde yok
            </div>
            <p className="max-w-[65ch] text-[length:var(--t-body)] leading-[1.6] text-murekkep-2">
              Ortalama, örneklem gürültüsünün <span className="font-mono">(1/√n)</span> içinde
              kalıyorsa hücre ne yeşil ne kırmızı olur — o sayı sıfırdan ayırt edilemez ve renk
              taşırsa bir hüküm gibi okunur. İşaret sayının kendisinde durur.
            </p>
            <ul className="mt-3 flex flex-col gap-1">
              {ORNEKLER.filter((o) => o.ortalama != null).map((o) => (
                <li
                  key={o.etiket}
                  className="flex flex-wrap items-baseline gap-2 text-[length:var(--t-cap)] text-murekkep-2"
                >
                  <span className="font-mono tabular-nums text-murekkep">{o.etiket}</span>
                  <span>
                    {gurultuBandiAciklamasi(o.ortalama, o.n) ??
                      "bandın dışında — renk bir okuma taşıyor"}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
