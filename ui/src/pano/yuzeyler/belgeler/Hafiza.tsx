"use client";

/* ============================================================================
   HAFIZA — `state/lessons.md`in okunur belge yüzeyi
   ----------------------------------------------------------------------------
   BU DOSYA AJANIN HAFIZASIDIR, bir günlük değil: uç şerhi "Injected into every
   reflection" diyor (api.py::api_memory) — yani buradaki her madde, bir sonraki
   öneri turunda modele geri veriliyor. Panoda okunur durmasının nedeni bu:
   ajanın neyi bir daha denemeyeceğini operatör de görebilsin.

   ÜÇ AYRI "BOŞ" VAR ve üçü ayrı cümle kurar:
     · uç okunamadı            → hata metni (Kapi çiziyor)
     · uç `_No lessons yet._`  → DOSYA YOK (api.py'nin açık boşluk beyanı)
     · dosya var, bölüm yok    → belge var ama `##` başlığı taşımıyor
   Üçünü tek "hafıza boş" kartına indirmek, dosyanın olmadığı durumla dosyanın
   boş olduğu durumu aynı şey saymak olurdu; birincisinde bakılacak yer diskte,
   ikincisinde ajanda.

   ARAMA MADDE DÜZEYİNDE: metnin tamamında `Ctrl+F` zaten var; buradaki süzgecin
   işi bölümleri KORUYARAK maddeleri elemek, böylece "hangi bölümde kaç eşleşme"
   sorusu da cevaplanır. Süzgeç boş sonuç verdiğinde "kayıt yok" DEMİYOR —
   "süzgeç geçirmedi" diyor ve toplamı yanına yazıyor.
   ============================================================================ */
import { useMemo, useState } from "react";

import { Bar, BarChart, XAxis, YAxis } from "recharts";
import { FileText, Search } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { bicimSayi } from "./ortak";
import { hafizaAyristir, vurguSok, type Hafiza as HafizaBelgesi } from "./damitim";

const YAPI = { n: { label: "madde" } } satisfies ChartConfig;

export function Hafiza({ ham }: { ham: string }) {
  const belge = useMemo(() => hafizaAyristir(ham), [ham]);
  const [arama, setArama] = useState("");

  if (belge.bosBeyani) {
    return (
      <Alert>
        <FileText />
        <AlertTitle>Hafıza dosyası YOK</AlertTitle>
        <AlertDescription>
          `/api/memory` gövdesi `_No lessons yet._` döndü. Bu, api.py'nin açık boşluk beyanıdır:
          `state/lessons.md` diskte bulunmuyor. "Ajan hiçbir şey öğrenmedi" ile AYNI ŞEY DEĞİL —
          damıtım dosyası hiç yazılmamış.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Kunye belge={belge} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <Belge belge={belge} arama={arama} setArama={setArama} />
        <div className="flex flex-col gap-4">
          <BolumTablosu belge={belge} />
          <BolumGrafigi belge={belge} />
        </div>
      </div>
    </div>
  );
}

/* ---- KÜNYE --------------------------------------------------------------- */

function Kunye({ belge }: { belge: HafizaBelgesi }) {
  const maddeN = belge.bolumler.reduce((a, b) => a + b.maddeler.length, 0);
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="outline" className="gap-1">
        <FileText className="size-3" aria-hidden />
        state/lessons.md
      </Badge>
      <Badge variant="ghost">{bicimSayi(belge.bolumler.length)} bölüm</Badge>
      <Badge variant="ghost">{bicimSayi(maddeN)} madde</Badge>
      <Badge variant="ghost">{bicimSayi(belge.karakterN)} karakter</Badge>
      <span className="text-muted-foreground text-xs">
        salt okunur — bu dosyayı yazan yansıma turudur, pano değil
      </span>
    </div>
  );
}

/* ---- BELGE GÖVDESİ ------------------------------------------------------- */

function Belge({
  belge,
  arama,
  setArama,
}: {
  belge: HafizaBelgesi;
  arama: string;
  setArama: (s: string) => void;
}) {
  const q = arama.trim().toLocaleLowerCase("tr-TR");
  const suzulmus = belge.bolumler.map((b) => ({
    ...b,
    maddeler: q === "" ? b.maddeler : b.maddeler.filter((m) => m.toLocaleLowerCase("tr-TR").includes(q)),
  }));
  const eslesenN = suzulmus.reduce((a, b) => a + b.maddeler.length, 0);
  const toplamN = belge.bolumler.reduce((a, b) => a + b.maddeler.length, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">{belge.baslik ?? "(belgede `#` başlığı yok)"}</CardTitle>
        <CardDescription>
          {belge.kunye.length === 0
            ? "Belge künye satırı taşımıyor."
            : belge.kunye.map((k) => vurguSok(k)).join(" · ")}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="relative">
          <Search className="-translate-y-1/2 absolute top-1/2 left-2.5 size-3.5 text-muted-foreground" aria-hidden />
          <Input
            value={arama}
            onChange={(e) => setArama(e.target.value)}
            placeholder="Maddelerde ara…"
            className="h-9 pl-8 text-sm"
            aria-label="Hafızada ara"
          />
        </div>
        {q === "" ? null : (
          <p className="text-muted-foreground text-xs tabular-nums">
            {bicimSayi(eslesenN)} / {bicimSayi(toplamN)} madde eşleşti
            {eslesenN === 0 ? " — süzgeç geçirmedi, hafıza boş DEĞİL" : null}
          </p>
        )}

        <ScrollArea className="h-[30rem] rounded-md border">
          <div className="flex flex-col gap-6 p-4">
            {belge.bolumler.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Belgede `##` bölümü yok. Dosya VAR ama bölümlenmemiş — düz yazısı aşağıda künyede
                duruyor.
              </p>
            ) : (
              suzulmus.map((b) => (
                <section key={b.baslik} className="flex flex-col gap-2">
                  <h3 className="border-b pb-1 font-medium text-sm">
                    {b.baslik}
                    <span className="ml-2 font-normal text-muted-foreground text-xs tabular-nums">
                      {bicimSayi(b.maddeler.length)} madde
                    </span>
                  </h3>
                  {b.duzYazi.length > 0 ? (
                    <div className="flex flex-col gap-1">
                      {b.duzYazi.map((d, i) => (
                        <p key={`${b.baslik}-p-${i}`} className="text-muted-foreground text-xs leading-relaxed">
                          {vurguSok(d)}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {b.maddeler.length === 0 ? (
                    <p className="text-muted-foreground text-xs italic">
                      {q === "" ? "bu bölümde madde yok" : "bu bölümde eşleşme yok"}
                    </p>
                  ) : (
                    <ul className="flex list-disc flex-col gap-1.5 pl-5">
                      {b.maddeler.map((m, i) => (
                        <li key={`${b.baslik}-${i}`} className="text-sm leading-relaxed">
                          {vurguSok(m)}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

/* ---- BÖLÜM TABLOSU + GRAFİĞİ --------------------------------------------- */

function BolumTablosu({ belge }: { belge: HafizaBelgesi }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">Bölüm dökümü</CardTitle>
        <CardDescription>Hafıza neyi biriktirmiş, hangi kovada?</CardDescription>
      </CardHeader>
      <CardContent>
        {belge.bolumler.length === 0 ? (
          <p className="text-muted-foreground text-sm">Belgede `##` bölümü yok — dökülecek kova yok.</p>
        ) : (
          <div className="min-w-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-0">Bölüm</TableHead>
                  <TableHead className="text-right">Madde</TableHead>
                  <TableHead className="text-right">Düz yazı</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {belge.bolumler.map((b) => (
                  <TableRow key={b.baslik}>
                    <TableCell className="pl-0 text-xs leading-snug">{b.baslik}</TableCell>
                    <TableCell className="text-right text-xs tabular-nums">{bicimSayi(b.maddeler.length)}</TableCell>
                    <TableCell className="text-right text-xs tabular-nums">{bicimSayi(b.duzYazi.length)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BolumGrafigi({ belge }: { belge: HafizaBelgesi }) {
  const veri = belge.bolumler.map((b) => ({
    // Uzun başlıklar eksende okunmaz; kırpma GÖRÜNÜR olsun diye üç nokta konuyor.
    ad: b.baslik.length > 26 ? `${b.baslik.slice(0, 25)}…` : b.baslik,
    tam: b.baslik,
    n: b.maddeler.length,
  }));

  if (veri.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">Ağırlık nerede?</CardTitle>
        <CardDescription>Bölüm başına madde sayısı — hafızanın çoğu hangi dersten?</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={YAPI} className="aspect-auto h-40 w-full">
          <BarChart data={veri} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="ad"
              tickLine={false}
              axisLine={false}
              width={150}
              tickMargin={4}
              className="text-xs"
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent hideIndicator labelKey="tam" />} />
            <Bar dataKey="n" radius={4} fill="var(--chart-2)" isAnimationActive={false} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
