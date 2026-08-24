"use client";

/* ============================================================================
   KARAR ZİNCİRİNİN HÜKÜM GEÇMİŞİ GRAFİĞİ
   ----------------------------------------------------------------------------
   HUNİ BURADAN TAŞINDI (2026-08-25): `HuniGrafigi` bu dosyada düz bir Recharts
   çubuğuydu — ne yüzde etiketi, ne payda beyanı, ne karekök ölçek beyanı, ne de
   "nerede, neden elendi" listesi taşıyordu. Bugün yüzeyindeki hüküm dağılımı da
   huniye çevrilince İKİ HUNİ doğacaktı ve iki kopya bu depoda "zamanla ayrışan
   iki gramer" demek. Gövde bu yüzden `./Huni.tsx`e çıkarıldı ve iki yüzey de
   ondan doğuyor; buradaki kopya SİLİNDİ (okuyucusuz kod bırakmak YASA 6 ihlali
   olurdu, üstelik bir sonraki düzenlemede hangisinin canlı olduğu karışırdı).

   GERİYE KALAN: seans başına NO_GO/REVIEW/GO dağılımı, `/api/signals.plans`
   üstünde sayılır. Bu uç kırpılıdır (son 120 plan) ve grafiğin altında bunu
   AÇIKÇA yazıyoruz: kırpma beyanı `ledger` bloğundan geliyor, tahminden değil.

   RENK: bu temanın `--chart-*` skalası GRİ TONLAMALI (tema.css) — hükümleri
   yalnız onunla ayırmak NO_GO ile GO'yu birbirine karıştırırdı. Bu yüzden anlam
   taşıyan iki uç ROL jetonuna bağlandı (`--destructive` = reddedildi, `--primary`
   = geçti); aradaki REVIEW ve "hüküm yok" gri skalada kaldı.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import { kisaTarih } from "./oku";

/* --------------------------- HÜKÜM GEÇMİŞİ -------------------------------- */

export interface SeansHukmu {
  readonly gun: string;
  readonly no_go: number;
  readonly review: number;
  readonly go: number;
  readonly belirsiz: number;
}

const hukumAyari = {
  no_go: { label: "NO_GO", color: "var(--destructive)" },
  review: { label: "REVIEW", color: "var(--chart-3)" },
  go: { label: "GO", color: "var(--primary)" },
  belirsiz: { label: "hüküm yok", color: "var(--chart-1)" },
} satisfies ChartConfig;

export function HukumGrafigi({ seanslar }: { seanslar: readonly SeansHukmu[] }) {
  return (
    <ChartContainer config={hukumAyari} className="h-64 w-full">
      <BarChart accessibilityLayer data={[...seanslar]} margin={{ left: 0, right: 8, top: 8 }}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="gun"
          axisLine={false}
          tickLine={false}
          tickMargin={8}
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => kisaTarih(String(v))}
        />
        <YAxis axisLine={false} tickLine={false} tickMargin={6} width={32} allowDecimals={false} />
        <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "var(--muted)" }} />
        <ChartLegend align="right" verticalAlign="top" content={<ChartLegendContent className="justify-end" />} />
        <Bar isAnimationActive={false} dataKey="no_go" stackId="h" fill="var(--color-no_go)" />
        <Bar isAnimationActive={false} dataKey="review" stackId="h" fill="var(--color-review)" />
        <Bar isAnimationActive={false} dataKey="go" stackId="h" fill="var(--color-go)" />
        <Bar isAnimationActive={false} dataKey="belirsiz" stackId="h" fill="var(--color-belirsiz)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
}
