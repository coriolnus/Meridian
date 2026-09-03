"use client";

/* ============================================================================
   HAFIZA · MERİDİAN DERSLERİ — Bilgi Tabanı görünümünün üçüncü alt sekmesi
   ----------------------------------------------------------------------------
   BU SEKME ÜST YÜZEYDE YOKTUR VE ADINDA BUNU SÖYLER. Hindsight Control Plane'in
   Bilgi Tabanı görünümü iki alt sekme taşır (sayfa ağacı · zihin modelleri);
   üçüncüsü Meridian'ın kendi eklediğidir ve içeriği Hindsight korpusunun
   PARÇASI DEĞİLDİR: korpus depo belgelerinden beslenir (docs/, araştırma
   kartları, üst düzey .md), `state/` dizini dışarıdadır. Buradaki dersler
   Meridian'ın KENDİ öğrenme döngüsünün çıktısıdır ve o çıktı hafıza bankasına
   hiç girmemiştir. Etiketsiz bir sekme, iki ayrı korpusu tek korpus sanmaya
   davet ederdi.

   NEREDEN GELDİ: bu sunum eski "Belgeler" rafı yüzeyindeydi (`Hafiza.tsx`) ve o
   yüzey 2026-09-02'de tümüyle kalktı — rafın iki bölümü Hafıza yüzeyinin ilgili
   görünümlerine dağıldı, çift üretim olmadan. Ayrıştırıcı da (`damitim.ts`)
   kopyalanmadı, taşındı.

   BU DOSYA AJANIN HAFIZASIDIR, bir günlük değil: uç şerhi "Injected into every
   reflection" diyor (api.py::api_memory) — yani buradaki her madde, bir sonraki
   öneri turunda modele geri veriliyor. Panoda okunur durmasının nedeni bu:
   ajanın neyi bir daha denemeyeceğini operatör de görebilsin.

   ÜÇ AYRI "BOŞ" VAR ve üçü ayrı cümle kurar:
     · uç okunamadı            → hata metni (kapı çiziyor)
     · uç boşluk beyanı döndü  → DOSYA YOK (ucun açık boşluk beyanı)
     · dosya var, bölüm yok    → belge var ama bölüm başlığı taşımıyor
   Üçünü tek "hafıza boş" kartına indirmek, dosyanın olmadığı durumla dosyanın
   boş olduğu durumu aynı şey saymak olurdu; birincisinde bakılacak yer diskte,
   ikincisinde ajanda.

   ARAMA MADDE DÜZEYİNDE: metnin tamamında tarayıcının kendi araması zaten var;
   buradaki süzgecin işi bölümleri KORUYARAK maddeleri elemek, böylece "hangi
   bölümde kaç eşleşme" sorusu da cevaplanır. Süzgeç boş sonuç verdiğinde "kayıt
   yok" DEMİYOR — "süzgeç geçirmedi" diyor ve toplamı yanına yazıyor.

   NABIZ YOK: damıtım dosyası bir yansıma turunda bir kez yazılıyor; on beş
   saniyede bir çekmek okunan bir belgeyi altından kaydırmak olurdu.
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

import { useApi } from "../../veri";
import { Kapi as UcKapisi, Olculemedi } from "../sistem/parcalar";
import { hafizaAyristir, vurguSok, type Hafiza as HafizaBelgesi } from "./damitim";
/* SAYI BİÇİMİ İTHAL EDİLİR, KOPYALANMAZ (nihai inceleme K-3, 2026-09-03): burada
   tek satırlık bir `bicimSayi` kopyası duruyordu ve şerhi "eski raf yüzeyinin
   ortak yardımcısının yerine" diyordu — ölçüm bunu yalanladı: yardımcı raf
   yüzeyinde DEĞİL `ajan/ortak.tsx`te yaşıyor, hâlâ ihraç ediliyor ve `Ajan.tsx`
   onu kullanıyor. Kopya davranışsal bir gerekçe de taşımıyordu (`maximumFraction
   Digits` kullandığı için tam sayılarda çıktı AYNI). */
import { bicimSayi } from "../ajan/ortak";
import { metin } from "./parcalar";

const UC_DERSLER = "/api/memory";

const YAPI = { n: { label: "madde" } } satisfies ChartConfig;

export function MeridianDersleri() {
  /* YOKLANMAZ: bu dosya bir yansıma turunda bir kez yazılıyor (dosya başlığı). */
  const durum = useApi<Record<string, unknown>>(UC_DERSLER, 0);

  return (
    <div className="flex flex-col gap-3">
      <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs leading-relaxed">
        <span className="font-medium text-foreground">Bu sekme üst yüzeyde yok. </span>
        Buradaki dersler Meridian&apos;ın kendi öğrenme döngüsünün çıktısıdır (çalışma durumundaki
        damıtım dosyası) ve hafıza bankasının korpusunda DEĞİLDİR — korpus depo belgelerinden
        beslenir, çalışma durumu dizini dışarıdadır. İki listeyi aynı korpus sanmamak için not
        burada duruyor.
      </p>
      <UcKapisi durum={durum} yol={UC_DERSLER}>
        {(g) => {
          const ham = metin(g["lessons_md"]);
          if (ham === null) {
            // 200 GELDİ AMA ALAN YOK: bu bir ağ hatası değil, bir SÖZLEŞME ihlali;
            // ikisini aynı kutuya koymak operatörü ağa baktırırdı.
            return (
              <Olculemedi
                neden="Ders metni bildirilmedi"
                teknik="uç cevap verdi ama gövdesinde ders metni alanı yok — sözleşme bu alanı her zaman yazmalı (api.py::api_memory)"
              />
            );
          }
          return <Dersler ham={ham} />;
        }}
      </UcKapisi>
    </div>
  );
}

function Dersler({ ham }: { readonly ham: string }) {
  const belge = useMemo(() => hafizaAyristir(ham), [ham]);
  const [arama, setArama] = useState("");

  if (belge.bosBeyani) {
    return (
      <Alert>
        <FileText />
        <AlertTitle>Ders dosyası YOK</AlertTitle>
        <AlertDescription>
          Uç açık boşluk beyanı döndürdü: damıtım dosyası diskte bulunmuyor. &quot;Ajan hiçbir şey
          öğrenmedi&quot; ile AYNI ŞEY DEĞİL — dosya hiç yazılmamış.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <BelgeKunyesi belge={belge} />
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

/* ---- KÜNYE --------------------------------------------------------------- */

/* BELGE BAŞLIĞI VE KÜNYE SATIRLARI BURADA OKUNUR — ve bu bir taşıma değil,
   OKUYUCU DEVRİDİR: ikisini de eskiden madde listesi kartı çiziyordu. O kart
   konsolide listeye devredilirken başlık ve künye okunmadan kalsaydı,
   ayrıştırıcı onları üretmeye devam eder ama kimse görmezdi. */
/* AD DİZİNDE TEKİL (düzeltme turu 2, Y-12): `Kunye` bu dizinde ÜÇ ayrı sözleşmeyle
   yaşıyordu; ikisi K-2 turunda adlandırıldı (`VarlikKunyesiPaneli` · `DugumKunyesi`),
   üçüncüsü burada kalmıştı. İhraç edilmediği için bugün zararsızdı — ama `Yapilandirma
   .tsx::araSuresi` şerhinin yazdığı tehlike ("aynı yüzeyde aynı adın iki sözleşmesi …
   yanlış olanı içe aktarmayı SESSİZ kılar") aynen geçerliydi. */
function BelgeKunyesi({ belge }: { belge: HafizaBelgesi }) {
  const maddeN = belge.bolumler.reduce((a, b) => a + b.maddeler.length, 0);
  return (
    <div className="flex flex-col gap-1.5">
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="outline" className="gap-1">
        <FileText className="size-3" aria-hidden />
        state/lessons.md
      </Badge>
      <Badge variant="ghost">{bicimSayi(belge.bolumler.length)} bölüm</Badge>
      <Badge variant="ghost">{bicimSayi(maddeN)} madde</Badge>
      <Badge variant="ghost">{bicimSayi(belge.karakterN)} karakter</Badge>
      <span className="text-muted-foreground text-xs">
        salt okunur — bu dosyayı yazan değerlendirme turudur, pano değil
      </span>
    </div>
      <p className="text-muted-foreground text-xs leading-relaxed">
        {belge.baslik ?? "(belgede başlık satırı yok)"}
        {belge.kunye.length === 0 ? null : ` · ${belge.kunye.map((k) => vurguSok(k)).join(" · ")}`}
      </p>
    </div>
  );
}

/* ---- BÖLÜM TABLOSU + GRAFİĞİ --------------------------------------------- */

function BolumTablosu({ belge }: { belge: HafizaBelgesi }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">Bölüm dökümü</CardTitle>
        <CardDescription>Hafıza neyi biriktirmiş, hangi aralıkta?</CardDescription>
      </CardHeader>
      <CardContent>
        {belge.bolumler.length === 0 ? (
          <p className="text-muted-foreground text-sm">Belgede `##` bölümü yok — dökülecek aralık yok.</p>
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
