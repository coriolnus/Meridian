/* ============================================================================
   HESAP KUTUSU — eski panonun `.acct` bloğunun karşılığı, kenar çubuğu ayağında
   ----------------------------------------------------------------------------
   Şablon buraya `NavUser` + `SupportCard` koyuyordu: biri sahte bir kullanıcı
   kartı, öteki bir şablon reklamı. İkisi de düştü. Meridian'da kenar çubuğunun
   ayağında duran şey HESABIN kendisidir — broker, sermaye, mod, nabız.

   MOD HER DURUMDA GÖRÜNÜR (Dalga-0 hükmü): kağıt mı gerçek mi sorusunun cevabı
   ekrandan hiçbir koşulda kaybolamaz. Ölçülemediyse bile satır durur ve
   "ölçülemedi" yazar — satırı gizlemek, okuyucuya moddan emin olma hissi verirdi.
   ============================================================================ */
import { SidebarGroup, useSidebar } from "@/components/ui/sidebar";
import type { BugunGovdesi } from "../tipler";

const MOD_OLCULEMEDI = "ölçülemedi";

function para(d: number | null | undefined): string {
  if (d == null || !Number.isFinite(d)) return MOD_OLCULEMEDI;
  return d.toLocaleString("tr-TR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function Satir({ ad, deger, vurgu }: { ad: string; deger: string; vurgu?: "iyi" | "uyari" }) {
  return (
    <div className="flex items-baseline justify-between gap-2 py-0.5 text-xs">
      <span className="text-muted-foreground">{ad}</span>
      <span
        className={
          "font-medium tabular-nums " +
          (vurgu === "uyari" ? "text-uyari" : vurgu === "iyi" ? "text-basari" : "")
        }
      >
        {deger}
      </span>
    </div>
  );
}

export function HesapKutusu({ bugun, hata }: { bugun: BugunGovdesi | null; hata: string | null }) {
  const { state, isMobile } = useSidebar();
  // İKON RAYINDA GİZLENİR: dört satırlık bir tablo 48px genişliğe sığmaz ve sıkıştırılırsa
  // rakamlar kırpılır — kırpılmış bir sermaye rakamı, yanlış bir sermaye rakamıdır.
  if (state === "collapsed" && !isMobile) return null;

  return (
    <SidebarGroup className="gap-1 rounded-md border bg-sidebar-accent/40 px-2 py-2">
      <div className="pb-1 font-medium text-[10px] text-muted-foreground uppercase tracking-wider">Hesap</div>
      {hata ? (
        // OKUNAMADI ≠ BOŞ. Kutuyu boş çizmek "hesap yok" derdi; neden yazılıyor.
        <p className="text-[11px] text-uyari leading-snug">Hesap okunamadı — {hata}</p>
      ) : (
        <>
          <Satir ad="Broker" deger={bugun?.broker ?? MOD_OLCULEMEDI} />
          <Satir ad="Sermaye" deger={para(bugun?.equity)} />
          <Satir ad="Mod" deger={bugun?.mode ?? MOD_OLCULEMEDI} />
          <Satir
            ad="Nabız"
            deger={bugun == null ? MOD_OLCULEMEDI : bugun.stale ? "gecikmiş" : "canlı"}
            vurgu={bugun == null ? undefined : bugun.stale ? "uyari" : "iyi"}
          />
        </>
      )}
    </SidebarGroup>
  );
}
