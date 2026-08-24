"use client";

/* ============================================================================
   KARAR ZİNCİRİNİN İKİ GRAFİĞİ
   ----------------------------------------------------------------------------
   (1) HUNİ — aday → plan → silahlı. Kaynağı `/api/today.son_dongu` ve bu bilinçli:
       o blok GÜNLÜK DÖNGÜNÜN KENDİ KAYDIdır (`events.jsonl`teki `daily_cycle`
       satırı, api.py:1571), yani "o gece kaç aday tarandı" sorusunun tek dürüst
       cevabı. Aynı sayıyı `/api/signals.candidates`ten saymak YANLIŞ olurdu:
       o uç son 120 satırla KIRPILMIŞ (api_signals 1731) ve kırpılmış bir sayı
       huninin ağzını olduğundan dar gösterirdi.
   (2) HÜKÜM GEÇMİŞİ — seans başına NO_GO/REVIEW/GO dağılımı, `/api/signals.plans`
       üstünde sayılır. Bu uç kırpılıdır (son 120 plan) ve grafiğin altında bunu
       AÇIKÇA yazıyoruz: kırpma beyanı `ledger` bloğundan geliyor, tahminden değil.

   RENK: bu temanın `--chart-*` skalası GRİ TONLAMALI (tema.css:75-79) — hükümleri
   yalnız onunla ayırmak NO_GO ile GO'yu birbirine karıştırırdı. Bu yüzden anlam
   taşıyan iki uç ROL jetonuna bağlandı (`--destructive` = reddedildi, `--primary`
   = geçti); aradaki REVIEW ve "hüküm yok" gri skalada kaldı.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts";

import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import { kisaTarih } from "./oku";

/* ------------------------------- HUNİ ------------------------------------ */

export interface HuniAsamasi {
  readonly asama: string;
  readonly n: number;
}

const huniAyari = {
  n: { label: "Adet", color: "var(--chart-3)" },
} satisfies ChartConfig;

export function HuniGrafigi({ asamalar }: { asamalar: readonly HuniAsamasi[] }) {
  return (
    <ChartContainer config={huniAyari} className="h-40 w-full">
      <BarChart accessibilityLayer data={[...asamalar]} layout="vertical" margin={{ left: 4, right: 32 }}>
        <CartesianGrid horizontal={false} />
        <XAxis type="number" dataKey="n" hide />
        <YAxis
          type="category"
          dataKey="asama"
          axisLine={false}
          tickLine={false}
          tickMargin={6}
          width={92}
          tick={{ fontSize: 12 }}
        />
        <ChartTooltip content={<ChartTooltipContent hideLabel />} cursor={{ fill: "var(--muted)" }} />
        <Bar isAnimationActive={false} dataKey="n" fill="var(--color-n)" radius={4}>
          <LabelList dataKey="n" position="right" offset={8} className="fill-foreground" fontSize={12} />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

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
