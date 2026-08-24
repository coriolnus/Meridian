"use client";

/* ============================================================================
   HÜKÜM DAĞILIMI — kapının o seans ne dediği
   ----------------------------------------------------------------------------
   Kaynak `/api/today.verdict_counts`: `analytics.today()` (analytics.py:262) günün
   planlarını `gate_verdict` alanına göre sayar ve alanı olmayan planı `"?"` kovasına
   koyar. Yani `"?"` bir hata değil, ÖLÇÜLMÜŞ bir kova — ekranda da öyle duruyor.

   NEDEN ÇUBUK, NEDEN DONUT DEĞİL: varsayılan paletin beş grafik jetonu da GRİ
   (tema.css: `--chart-1: oklch(0.87 0 0)` … `--chart-5: oklch(0.269 0 0)`, ölçüldü
   2026-08-25). Gri tonlu bir halkada üç dilimi ayırt etmek renge bağlıdır; yan yana
   etiketli çubuklarda ise ayrım UZUNLUKTAN okunur ve sayı zaten yanında yazar.
   Hüküm kovalarını yeşil/kırmızıya boyamak ayrıca yanlış olurdu: NO_GO bir ARIZA
   değil, kapının normal ve en sık çıktısıdır — kırmızı bir çubuk her sakin günü
   olay gibi gösterirdi.

   BOŞ GÖVDE "HER ŞEY YOLUNDA" DEĞİLDİR: `verdict_counts` YOKSA ölçülemedi denir;
   `{}` ise "bu seansta hüküm verilmiş plan yok" denir. İkisi ayrı cümle.
   ============================================================================ */
import { Bar, BarChart, Cell, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

import { Olculemedi, bicimSayi } from "./ortak";
import type { BugunTam } from "./tipler";

/** Okuma sırası: kapıdan GEÇEN önce, düşen sonra. Listede olmayan bir hüküm
 *  (uç yeni bir kova açarsa) sona eklenir — bilinmeyen bir kovayı yutmak, ölçülmüş
 *  bir planı ekrandan silmek olurdu. */
const SIRA = ["GO", "REVIEW", "NO_GO", "?"];

/** Jeton seçimi KOYUDAN AÇIĞA: en sık kova (NO_GO) en açık tonu alır, göze en az
 *  yüklenen o olsun. Anlam taşıyan renk YOK — anlamı etiket taşıyor. */
const TON: Readonly<Record<string, string>> = {
  GO: "var(--chart-5)",
  REVIEW: "var(--chart-3)",
  NO_GO: "var(--chart-1)",
  "?": "var(--chart-2)",
};

const yapilandirma = {
  n: { label: "plan" },
} satisfies ChartConfig;

export function HukumDagilimi({ b }: { b: BugunTam }) {
  const sayimlar = b.verdict_counts;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="leading-none">Hüküm dağılımı</CardTitle>
        <CardDescription>
          {b.todays_plan_date === undefined || b.todays_plan_date === null
            ? "seans tarihi ölçülemedi"
            : `${b.todays_plan_date} seansı · kapı ne dedi?`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {sayimlar === undefined ? (
          <Olculemedi neden="`/api/today` gövdesinde `verdict_counts` alanı yok" />
        ) : (
          <Icerik sayimlar={sayimlar} planN={b.todays_plans?.length} />
        )}
      </CardContent>
    </Card>
  );
}

function Icerik({ sayimlar, planN }: { sayimlar: Readonly<Record<string, number>>; planN: number | undefined }) {
  const anahtarlar = Object.keys(sayimlar);
  const sirali = [
    ...SIRA.filter((k) => anahtarlar.includes(k)),
    ...anahtarlar.filter((k) => !SIRA.includes(k)),
  ];
  const veri = sirali.map((k) => ({ hukum: k, n: sayimlar[k] ?? 0 }));
  const toplam = veri.reduce((a, x) => a + x.n, 0);

  if (veri.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Bu seansta hüküm verilmiş plan yok — sayaç boş döndü (ölçüldü, bilgi eksikliği değil).
        {planN !== undefined && planN > 0
          ? ` DİKKAT: aynı gövdede ${bicimSayi(planN)} plan var; sayaç ile liste ayrışıyor.`
          : null}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <ChartContainer config={yapilandirma} className="aspect-auto h-40 w-full">
        <BarChart data={veri} layout="vertical" margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="hukum"
            tickLine={false}
            axisLine={false}
            width={78}
            tickMargin={4}
            className="text-xs"
          />
          <ChartTooltip cursor={false} content={<ChartTooltipContent hideIndicator />} />
          <Bar dataKey="n" radius={4} isAnimationActive={false}>
            {veri.map((d) => (
              <Cell key={d.hukum} fill={TON[d.hukum] ?? "var(--chart-4)"} />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>

      {/* SAYILAR GRAFİĞİN DIŞINDA DA YAZAR: fareyle üstüne gelmeden okunabilmeli ve
          tek bir çubuk 10, diğerleri 0 iken uzunluk farkı bilgi taşımaz. */}
      <ul className="flex flex-col gap-1 border-t pt-3 text-sm">
        {veri.map((d) => (
          <li key={d.hukum} className="flex items-baseline justify-between gap-3">
            <span className="text-muted-foreground">{d.hukum === "?" ? "hükümsüz (?)" : d.hukum}</span>
            <span className="tabular-nums">
              {bicimSayi(d.n)}
              {toplam > 0 ? <span className="ml-1 text-muted-foreground">%{bicimSayi((100 * d.n) / toplam)}</span> : null}
            </span>
          </li>
        ))}
      </ul>

      {planN !== undefined && planN !== toplam ? (
        <p className="text-destructive text-xs">
          Sayaç {bicimSayi(toplam)} plan sayıyor, liste {bicimSayi(planN)} plan taşıyor — aynı gövdede iki farklı
          cevap. Bu bir ekran hatası değil, gövdenin kendisinde ayrışma.
        </p>
      ) : null}
    </div>
  );
}
