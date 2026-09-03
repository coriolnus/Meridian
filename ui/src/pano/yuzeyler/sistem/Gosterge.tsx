"use client";

/* ============================================================================
   RADYAL GÖSTERGE — tek bir yüzdenin kadranı
   ----------------------------------------------------------------------------
   ŞABLONDA HAZIR BİR GAUGE YOK (arandı: `RadialBar|PolarAngleAxis|PolarGrid`
   şablonun tamamında SIFIR eşleşme). Ama `components/ui/chart.tsx` radyal için
   ZATEN hazırlanmış — kapsayıcı `.recharts-radial-bar-background-sector`ü
   `fill-muted` ile boyuyor (chart.tsx:68). Yani bu bileşen şablonun grafik
   sözleşmesinin İÇİNDE kalıyor: renk `var(--chart-N)`, kap `ChartContainer`.

   ÖLÇÜLEMEYEN DEĞER KADRAN ÇİZDİRMEZ. Boş bir kadran "sıfır" diye okunur ve bu
   yalandır; değer yoksa kadranın yerine nedeni yazılır.
   ============================================================================ */
import { PolarAngleAxis, RadialBar, RadialBarChart } from "recharts";

import { type ChartConfig, ChartContainer } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

import { Olculemedi } from "./parcalar";

const YAPILANDIRMA: ChartConfig = { deger: { label: "kullanım" } };

export function Gosterge({
  baslik,
  yuzde,
  neden,
  teknik,
  altMetin,
  uyari = 70,
  kritik = 85,
}: {
  readonly baslik: string;
  readonly yuzde: number | null | undefined;
  readonly neden: string;
  readonly teknik?: string;
  readonly altMetin?: string | null;
  readonly uyari?: number;
  readonly kritik?: number;
}) {
  if (yuzde === undefined || yuzde === null || !Number.isFinite(yuzde)) {
    return (
      <div className="flex min-h-40 flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-4 text-center">
        <span className="font-medium text-sm">{baslik}</span>
        <Olculemedi neden={neden} teknik={teknik} />
      </div>
    );
  }
  const v = Math.max(0, Math.min(100, yuzde));
  const kritikte = v >= kritik;
  const uyarida = v >= uyari;
  // RENK ROL JETONUNDAN: çıplak hex yok. Eşik aşılmadıkça grafik paletinin ilk rengi,
  // aşıldığında uyarı/tehlike rolü. Eşikler tooltip'te yazılı — renk bir hüküm ve
  // hükmün eşiği görünmeden verilmez.
  const renk = kritikte ? "var(--destructive)" : uyarida ? "var(--chart-4)" : "var(--chart-1)";

  return (
    <div
      className="flex flex-col items-center rounded-lg border p-2"
      title={`uyarı eşiği %${uyari} · kritik eşik %${kritik}`}
    >
      <span className="pt-1 font-medium text-muted-foreground text-xs">{baslik}</span>
      <ChartContainer config={YAPILANDIRMA} className="aspect-square h-36 w-full">
        <RadialBarChart
          data={[{ ad: baslik, deger: v, fill: renk }]}
          startAngle={220}
          endAngle={-40}
          innerRadius="72%"
          outerRadius="100%"
        >
          {/* Ölçek 0-100'e SABİTLENİR: recharts varsayılanı veriye göre ölçekler ve
              tek değerli bir kadranda %3 kullanım tam dolu görünürdü. */}
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar isAnimationActive={false} dataKey="deger" background cornerRadius={6} angleAxisId={0} />
        </RadialBarChart>
      </ChartContainer>
      <span
        className={cn(
          "-mt-8 font-semibold text-2xl tabular-nums",
          uyarida && "text-uyari",
          kritikte && "text-destructive",
        )}
      >
        {v.toFixed(1)}%
      </span>
      <span className="min-h-8 px-2 pt-1 pb-1 text-center text-[11px] text-muted-foreground tabular-nums">
        {altMetin ?? ""}
      </span>
    </div>
  );
}
