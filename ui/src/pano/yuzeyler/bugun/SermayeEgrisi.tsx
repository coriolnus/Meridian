"use client";

/* ============================================================================
   SERMAYE EĞRİSİ — şablonun "Performance Overview" alanının Meridian karşılığı
   ----------------------------------------------------------------------------
   KAYNAK ÖLÇÜLEREK SEÇİLDİ, VARSAYILARAK DEĞİL. Brief iki adaydan birini istiyordu:
     · `/api/plots`       → kurulum × rejim MATRİSİ (setups/regimes/grid). Okundu
       (`api_plots`): hiçbir zaman serisi taşımıyor, tek bir tarih alanı bile yok.
     · `/api/performance` → `equity_curve.points`. Okundu (`api_performance`) ve yerel
       artefakttan doğrulandı (state/equity_curve.json, 2026-08-25): 882 nokta,
       `[["2023-01-12", 100000.0], …]`, son nokta 2026-07-20.
   Eğriyi veren uç ikincisi; bu dosya oradan okuyor.

   AYRI NABIZ, AYRI PERİYOT: bu uç paylaşılan `/api/today` nabzında DEĞİL ve olmamalı —
   eğriye günde TEK nokta ekleniyor (`loop._persist_equity_point`, beyan metninde yazılı).
   15 saniyede bir 882 noktalık bir seriyi yeniden çekmek, hiç değişmeyen bir veriyi
   günde ~5.700 kez sormak olurdu. Beş dakika, "seans içinde bir nokta düşerse aynı
   oturumda görürüz" ile "boşuna trafik yok" arasındaki ölçülü orta.

   DELİKLER GÖRÜNMEZ, İŞARETLER GÖRÜNÜR: seri DİZİN ekseninde çiziliyor (uç beyanı,
   `_egri_beyani`) — yani 20 günlük bir boşluk grafikte normal bir adım gibi durur.
   Bu yüzden tohum sınırı ve reset kırılmaları dikey işaret olarak konuyor ve boşluk
   sayısı alttaki beyan şeridinde yazıyor. Boşluğu geriye doldurmak uydurma olurdu.
   ============================================================================ */
import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, XAxis, YAxis } from "recharts";

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

import { NABIZ_MS, useApi } from "../../veri";
import { Olculemedi, UcHal, bicimPara, bicimSayi } from "./ortak";
import type { EgriBeyani, PerformansGovdesi } from "./tipler";

/** Eğri günde tek nokta alıyor; nabzı panonunkinin yirmi katı yavaş tutmak ölçülü. */
const EGRI_PERIYOT_MS = NABIZ_MS * 20;

const PENCERELER = [
  { deger: "tum", etiket: "Tüm seri", n: 0 },
  { deger: "250", etiket: "Son 250 nokta", n: 250 },
  { deger: "90", etiket: "Son 90 nokta", n: 90 },
] as const;

const yapilandirma = {
  deger: { label: "Sermaye", color: "var(--chart-2)" },
} satisfies ChartConfig;

interface Nokta {
  /** HAM dizin — uç işaretleri (`tohum_siniri.i`, `reset_isaretleri[].i`) bu eksende
   *  veriyor (`_egri_beyani` `enumerate(points)` ile sayıyor). Okunamayan noktalar
   *  elenince kendi dizinim kayar; işaretleri kendi dizinimle eşlemek onları sessizce
   *  yanlış yere koyardı. */
  readonly ham: number;
  readonly tarih: string;
  readonly deger: number;
}

/** Ham nokta listesini çözer. Çözülemeyen nokta SERİYE GİRMEZ ve SAYILIR — 0 olarak
 *  girseydi eğri gerçekte olmayan bir çöküş çizerdi. */
function noktalariCoz(ham: readonly (readonly unknown[])[]): { noktalar: Nokta[]; okunamayan: number } {
  const noktalar: Nokta[] = [];
  let okunamayan = 0;
  ham.forEach((p, i) => {
    const t = p[0];
    const v = p[1];
    if (typeof t !== "string" || typeof v !== "number" || !Number.isFinite(v)) {
      okunamayan += 1;
      return;
    }
    noktalar.push({ ham: i, tarih: t.slice(0, 10), deger: v });
  });
  return { noktalar, okunamayan };
}

/** Beyanı tek cümleye indirger. Ölçülemeyen her parça CÜMLEDEN DÜŞER — "0 boşluk"
 *  yazmak ile "boşluk sayılmadı" aynı şey değil. */
function beyanSatiri(beyan: EgriBeyani | undefined, gorunen: number, okunamayan: number): string[] {
  if (beyan === undefined) return ["pencere beyanı ölçülemedi — gövdede `equity_curve_beyani` yok"];
  const s: string[] = [];
  s.push(
    beyan.n_nokta === undefined
      ? "seri uzunluğu ölçülemedi"
      : `${bicimSayi(beyan.n_nokta)} nokta (${bicimSayi(gorunen)} çizildi)`,
  );
  if (beyan.ilk && beyan.son) s.push(`${beyan.ilk[0]} → ${beyan.son[0]}`);
  if (beyan.son_seans !== undefined && beyan.son_seans !== null) {
    s.push(
      beyan.gecikme_gun === undefined || beyan.gecikme_gun === null
        ? `kitabın son seansı ${beyan.son_seans} · gecikme ölçülemedi`
        : `kitabın son seansı ${beyan.son_seans} · ${bicimSayi(beyan.gecikme_gun)} gün geride`,
    );
  }
  if (beyan.n_bosluk !== undefined) {
    s.push(
      beyan.bosluk_esigi_gun === undefined
        ? `${bicimSayi(beyan.n_bosluk)} boşluk`
        : `${bicimSayi(beyan.n_bosluk)} boşluk (eşik ${bicimSayi(beyan.bosluk_esigi_gun)} gün)`,
    );
  }
  const yutulan = (beyan.okunamayan_nokta ?? 0) + okunamayan;
  if (yutulan > 0) s.push(`${bicimSayi(yutulan)} nokta okunamadı — seriye GİRMEDİ`);
  return s;
}

export function SermayeEgrisi() {
  const durum = useApi<PerformansGovdesi>("/api/performance", EGRI_PERIYOT_MS);
  const [pencere, setPencere] = useState<string>("tum");

  return (
    <Card className="@container/card h-full">
      <CardHeader>
        <CardTitle className="leading-none">Sermaye eğrisi</CardTitle>
        <CardDescription>Kitabın beyanlı tek tabanında, seans sonunda günde tek nokta.</CardDescription>
        <CardAction>
          <Select value={pencere} onValueChange={setPencere}>
            <SelectTrigger size="sm" className="w-40">
              <SelectValue placeholder="Tüm seri" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {PENCERELER.map((p) => (
                  <SelectItem key={p.deger} value={p.deger}>
                    {p.etiket}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>

      <CardContent>
        <UcHal durum={durum} iskelet={<Skeleton className="h-80 w-full" />}>
          {(p) => <Govde govde={p} pencere={pencere} />}
        </UcHal>
      </CardContent>
    </Card>
  );
}

function Govde({ govde, pencere }: { govde: PerformansGovdesi; pencere: string }) {
  const ham = govde.equity_curve?.points;
  const beyan = govde.equity_curve_beyani;

  const { noktalar, okunamayan } = useMemo(() => noktalariCoz(ham ?? []), [ham]);

  const dilim = useMemo(() => {
    const n = PENCERELER.find((x) => x.deger === pencere)?.n ?? 0;
    return n > 0 ? noktalar.slice(-n) : noktalar;
  }, [noktalar, pencere]);

  // İŞARETLER YALNIZ ÇİZİLEN DİLİMDEYSE KONUR: dilim dışında kalan bir tohum sınırını
  // grafiğin kenarına yapıştırmak, olmadığı bir yerde varmış gibi göstermek olurdu.
  const hamlar = useMemo(() => new Map(dilim.map((n) => [n.ham, n.tarih])), [dilim]);
  const tohumSinir = beyan?.tohum_siniri ?? null;
  const tohumI = tohumSinir?.i;
  const tohumX = typeof tohumI === "number" ? hamlar.get(tohumI) : undefined;
  const resetX = (beyan?.reset_isaretleri ?? [])
    .map((m) => (typeof m.i === "number" ? hamlar.get(m.i) : undefined))
    .filter((x): x is string => x !== undefined);

  if (ham === undefined) {
    return (
      <Olculemedi
        neden="Sermaye eğrisi bildirilmedi"
        teknik="`/api/performance` gövdesinde `equity_curve.points` alanı yok"
      />
    );
  }
  if (noktalar.length === 0) {
    return (
      <Olculemedi
        neden={
          okunamayan > 0
            ? `${bicimSayi(okunamayan)} noktanın hiçbiri okunamadı — çizilecek seri kalmadı`
            : "Henüz hiç sermaye noktası kaydedilmemiş"
        }
        teknik={
          okunamayan > 0
            ? "`equity_curve.points` dolu ama hiçbir satır tarih+değer çiftine çözülemedi"
            : "`equity_curve.points` boş dizi"
        }
      />
    );
  }

  const son = dilim[dilim.length - 1];
  const ilk = dilim[0];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-medium text-2xl tabular-nums leading-none tracking-tight">
          {son ? bicimPara(son.deger) : "—"}
        </span>
        {ilk && son ? (
          <span className="text-muted-foreground text-sm">
            çizilen pencerede {ilk.tarih} → {son.tarih}
          </span>
        ) : null}
      </div>

      <ChartContainer config={yapilandirma} className="aspect-auto h-72 w-full">
        <AreaChart data={dilim} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="dolguSermaye" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-deger)" stopOpacity={0.36} />
              <stop offset="95%" stopColor="var(--color-deger)" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} strokeOpacity={0.5} />
          <XAxis dataKey="tarih" tickLine={false} axisLine={false} tickMargin={8} minTickGap={48} />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={64}
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => bicimSayi(Math.round(v))}
          />
          <ChartTooltip cursor={false} content={<ChartTooltipContent className="w-48" indicator="line" />} />
          {/* TOHUM SINIRI — serinin hangi kısmı ANTRENMAN tohumu, hangisi canlı nokta.
              882 tohum noktası ile canlı kuyruk tek çizgide duruyor; sınır beyansız kalırsa
              okuyucu training'i canlı kanıt sanar. */}
          {tohumX !== undefined ? (
            <ReferenceLine x={tohumX} stroke="var(--foreground)" strokeOpacity={0.55} strokeDasharray="6 4" />
          ) : null}
          {resetX.map((x) => (
            <ReferenceLine key={x} x={x} stroke="var(--destructive)" strokeOpacity={0.7} strokeDasharray="2 3" />
          ))}
          <Area
            dataKey="deger"
            type="monotone"
            fill="url(#dolguSermaye)"
            stroke="var(--color-deger)"
            strokeWidth={1.4}
            dot={false}
            fillOpacity={1}
            isAnimationActive={false}
          />
        </AreaChart>
      </ChartContainer>

      <div className="flex flex-col gap-1 border-t pt-3 text-muted-foreground text-xs">
        <p>{beyanSatiri(beyan, dilim.length, okunamayan).join(" · ")}</p>
        <p>
          {tohumX !== undefined ? "Kesik gri dikey çizgi: antrenman tohumunun bittiği nokta. " : null}
          {resetX.length > 0 ? `Kesik kırmızı çizgi(ler): ${bicimSayi(resetX.length)} sermaye reset kırılması. ` : null}
          {tohumSinir?.konum_neden ? `Tohum sınırı grafiğe konmadı — ${tohumSinir.konum_neden}` : null}
        </p>
      </div>
    </div>
  );
}
