"use client";

/* ============================================================================
   SEKME 2 — YOL HARİTASI: ROADMAP.md'nin tahtası (SALT OKUNUR)
   ----------------------------------------------------------------------------
   Operatörün isteği: "roadmap'i düzenli tutabileceğimiz şekilde". Bu turda tahta
   YALNIZ GÖSTERİR — yazma ucu yok, sürükleme yok, düğme yok. Rozet bunu ekranda
   söylüyor: taşınabilir sandığı bir kartı taşıyan operatör, hiçbir yere
   kaydedilmeyen bir düzenleme yapmış olurdu. Kaynak dosyayı bir İNSAN düzenliyor
   (`ROADMAP.md`, 562 KB) ve uç da bunu başlığında yazıyor.

   KOLONLAR BELGENİN KENDİ § BÖLÜMLERİDİR, sabit kodlama YOK. Gerekçe belgenin
   kendi tarihinde yazılı: §-numaraları 2026-08-17'de yeniden numaralandı
   (§1→§3, §2→§4 …) ve 151 atıf çevrildi. Kolon adlarını buraya gömmek, belgenin
   bir sonraki yeniden örgütlenmesinde panoyu SESSİZCE yanlış yapardı.

   "BELİRSİZ" KOVASI BİRLEŞTİRİLMEZ. Ucun ayrıştırıcısının en önemli satırı:
   işaretsiz kalem "açık" değil "belirsiz"dir (api.py:6605). Panoda o beş kovayı
   dörde indirmek — ya da "belirsiz"i "açık"a katmak — ölçülmemiş bir sayıyı
   yönetim kararına çevirirdi.
   ============================================================================ */
import { useMemo, useState } from "react";

import { FileQuestion, FileWarning, Info, Map as MapIkonu, Rows3, Strikethrough } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { useApi } from "../../veri";
import { Hal, SaltOkunurRozet } from "./Hal";
import {
  DURUM_ETIKETI,
  DURUM_SIRASI,
  bolumBasligi,
  roadmapOku,
  type RoadmapBolumu,
  type RoadmapMaddesi,
  type RoadmapOkumasi,
} from "./roadmap";

/* KART TAVANI: §7 karar günlüğü tek başına yüzlerce madde taşıyor (belge 4622
   satır). Hepsini basmak tarayıcıyı da okuyucuyu da boğardı. Tavan var AMA
   GİZLİ DEĞİL — her kolonun altında "gösterilen / toplam" yazıyor. */
const KART_TAVANI = 25;

const durumAyari = {
  bloke: { label: "bloke", color: "var(--destructive)" },
  acik: { label: "açık", color: "var(--primary)" },
  askida: { label: "askıda", color: "var(--chart-3)" },
  belirsiz: { label: "belirsiz", color: "var(--chart-1)" },
  kapali: { label: "kapalı", color: "var(--chart-4)" },
} satisfies ChartConfig;

function durumRozetiTonu(durum: string | null): "default" | "secondary" | "destructive" | "outline" | "ghost" {
  if (durum === "bloke") return "destructive";
  if (durum === "acik") return "default";
  if (durum === "askida") return "secondary";
  if (durum === "kapali") return "outline";
  return "ghost";
}

function MaddeKarti({ m }: { m: RoadmapMaddesi }) {
  // BAŞLIK ile HAM aynıysa gövdeyi ikinci kez basmıyoruz: `_roadmap_madde_basligi`
  // kısa maddelerde başlığı gövdenin kendisinden üretiyor, yani ikisi eş olabilir.
  const govde = m.ham !== null && m.ham !== m.baslik ? m.ham : null;

  return (
    <article className="flex flex-col gap-2 rounded-xl border bg-card p-3.5 text-card-foreground shadow-xs">
      <div className="flex items-start justify-between gap-2">
        {/* BAŞLIĞA ÜSTÜ-ÇİZİK UYGULANMIYOR: `ustu_cizili` maddenin GÖVDESİNDE bir
            üstü-çizik ARALIĞI olduğunu söyler, başlığın kendisinin çizildiğini DEĞİL
            (ayrıştırıcı başlığı üretirken `~~...~~` işaretlerini zaten söküyor,
            api.py:6648). Tüm başlığı çizmek, ölçülenden fazlasını iddia ederdi —
            bilgi aşağıdaki "geri alınmış" rozetinde duruyor. */}
        <h4 className="min-w-0 font-medium text-sm leading-5">
          {m.baslik ?? <span className="text-muted-foreground italic">başlık çıkarılamadı</span>}
        </h4>
        {m.durum ? (
          <Badge
            variant={durumRozetiTonu(m.durum)}
            className="shrink-0 text-[11px]"
            title={m.durumKanit ?? "ayrıştırıcı bu durumu hangi kelimeden okuduğunu yazmadı"}
          >
            {DURUM_ETIKETI[m.durum] ?? m.durum}
          </Badge>
        ) : (
          <Badge variant="ghost" className="shrink-0 text-[11px]" title="madde satırında `durum` alanı yok">
            durumsuz
          </Badge>
        )}
      </div>

      {govde ? <p className="line-clamp-3 text-muted-foreground text-xs leading-5">{govde}</p> : null}

      <div className="flex flex-wrap items-center gap-1.5">
        {m.altBolum ? (
          <Badge variant="secondary" className="max-w-full truncate text-[10px]" title={m.altBolum}>
            {m.altBolum}
          </Badge>
        ) : null}
        {m.ustuCizili ? (
          <Badge
            variant="outline"
            className="gap-1 text-[10px]"
            title="dosyada üstü çizili — bir kapanış iddiası GERİ ALINMIŞ olabilir; kapalı sayılmaz"
          >
            <Strikethrough className="size-3" aria-hidden />
            geri alınmış
          </Badge>
        ) : null}
        {m.hamKirpildi ? (
          <Badge
            variant="ghost"
            className="text-[10px]"
            title={`madde gövdesi uçta kırpıldı — tam uzunluk ${m.hamUzunluk ?? "?"} karakter`}
          >
            kırpıldı
          </Badge>
        ) : null}
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {m.satir === null ? "satırsız" : `satır ${m.satir}`}
        </span>
      </div>
    </article>
  );
}

function Kolon({ b, maddeler }: { b: RoadmapBolumu; maddeler: readonly RoadmapMaddesi[] }) {
  const gosterilen = maddeler.slice(0, KART_TAVANI);

  return (
    <section className="flex min-h-0 flex-col rounded-xl border bg-muted/50">
      <div className="px-4 pt-4 pb-3">
        <h3 className="break-words font-medium text-base leading-tight">{bolumBasligi(b)}</h3>
        <p className="mt-1 text-muted-foreground text-sm tabular-nums leading-none">
          {maddeler.length} madde
          {b.altBolumN > 0 ? ` · ${b.altBolumN} alt başlık` : ""}
        </p>
      </div>
      <div className="flex max-h-[34rem] min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto px-3 pb-3 [scrollbar-color:var(--border)_transparent] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1">
        {gosterilen.length === 0 ? (
          <p className="rounded-lg border border-dashed px-3 py-6 text-center text-muted-foreground text-xs">
            bu süzgeçte madde yok
          </p>
        ) : (
          gosterilen.map((m) => <MaddeKarti key={m.anahtar} m={m} />)
        )}
        {maddeler.length > gosterilen.length ? (
          <p className="rounded-lg border border-dashed px-3 py-2 text-center text-muted-foreground text-xs">
            {gosterilen.length} / {maddeler.length} gösteriliyor — kalan {maddeler.length - gosterilen.length}{" "}
            madde tahtada ÇİZİLMEDİ (kart tavanı {KART_TAVANI}).
          </p>
        ) : null}
      </div>
    </section>
  );
}

export function YolHaritasi() {
  // NABIZ YOK (0): yol haritası bir BELGEdir, canlı bir ölçüm değil — dosyayı bir
  // insan düzenliyor. Zamanlayıcıyla çekmek 562 KB'lık ayrıştırmayı boşuna
  // tekrarlatır (uç önbellekli ama istek yine gider). Tazeleme yüzeye girişte olur.
  const uc = useApi<unknown>("/api/roadmap", 0);

  return (
    <section id="bolum-roadmap" className="flex scroll-mt-20 flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="flex items-center gap-2 font-semibold text-lg tracking-tight">
            <MapIkonu className="size-4 text-muted-foreground" aria-hidden />
            Yol haritası
          </h2>
          <p className="text-muted-foreground text-sm">Hangi iş hangi bölümde, hangi durumda?</p>
        </div>
        <SaltOkunurRozet not="Bu turda yazma ucu YOK — tahta yalnız gösterir; kaynağı ROADMAP.md ve onu bir insan düzenliyor." />
      </div>

      <Hal d={uc} ad="/api/roadmap" iskelet={<Skeleton className="h-64 w-full" />} ciz={(v) => <Tahta ham={v} />} />
    </section>
  );
}

function Tahta({ ham }: { ham: unknown }) {
  const okuma: RoadmapOkumasi = useMemo(() => roadmapOku(ham), [ham]);
  const [suzgec, setSuzgec] = useState<string | null>(null);

  if (okuma.tur === "hata") {
    return (
      <Alert variant="destructive">
        <FileWarning />
        <AlertTitle>Yol haritası dosyası okunamadı</AlertTitle>
        <AlertDescription>
          <span className="block">{okuma.hata}</span>
          {okuma.yol ? (
            <span className="mt-1 block">
              Aranan yol: <code className="font-mono text-xs">{okuma.yol}</code>
            </span>
          ) : (
            <span className="mt-1 block">Uç hangi yolu denediğini yazmadı.</span>
          )}
          <span className="mt-1 block">Bu "yol haritası boş" DEĞİL — dosyaya erişilemedi.</span>
        </AlertDescription>
      </Alert>
    );
  }

  if (okuma.tur === "tanimadi") {
    return (
      <Alert variant="destructive">
        <FileQuestion />
        <AlertTitle>`/api/roadmap` gövde şekli tanınmadı</AlertTitle>
        <AlertDescription>
          <span className="block">
            Uç cevap verdi ama `bolumler` bir dizi değil. Tahtayı hangi alandan kuracağımızı
            ölçemedik — bu "yol haritası boş" DEĞİL.
          </span>
          <span className="mt-2 block">
            Üst düzey anahtarlar:{" "}
            {okuma.ustAnahtarlar.length === 0 ? (
              <em>hiç yok (gövde nesne değil)</em>
            ) : (
              <code className="font-mono text-xs">{okuma.ustAnahtarlar.join(", ")}</code>
            )}
          </span>
          <code className="mt-2 block max-h-32 overflow-auto rounded bg-muted p-2 font-mono text-[11px] text-muted-foreground">
            {okuma.ornek}
          </code>
        </AlertDescription>
      </Alert>
    );
  }

  const { bolumler, sayim, kunye } = okuma;
  const tumMaddeler = bolumler.flatMap((b) => b.maddeler);

  // KENDİ SAYIMIMIZ — kart başına bir madde. Ucun `sayim.madde_n` beyanıyla
  // karşılaştırılıyor: ayrışırsa düzleştirme bir dalı atlıyordur ve bunu ekranda
  // söylemek, sessizce eksik tahta çizmekten iyidir.
  const bizimN = tumMaddeler.length;
  const beyanAyrisiyor = sayim.maddeN !== null && sayim.maddeN !== bizimN;

  const kendiDurumSayimi = new Map<string, number>();
  let durumsuz = 0;
  for (const m of tumMaddeler) {
    if (m.durum === null) durumsuz += 1;
    else kendiDurumSayimi.set(m.durum, (kendiDurumSayimi.get(m.durum) ?? 0) + 1);
  }

  const suzulmus = (b: RoadmapBolumu) =>
    suzgec === null ? b.maddeler : b.maddeler.filter((m) => m.durum === suzgec);

  const grafikVerisi = bolumler.map((b) => {
    const satir: Record<string, string | number> = { bolum: b.no ?? (b.baslik ?? "?").slice(0, 18) };
    for (const d of DURUM_SIRASI) satir[d] = b.maddeler.filter((m) => m.durum === d).length;
    return satir;
  });

  interface DurumSatiri {
    readonly durum: string;
    readonly ucSayimi: number | null;
    readonly panoSayimi: number;
  }
  const durumSatirlari: DurumSatiri[] = [...DURUM_SIRASI]
    .map<DurumSatiri>((d) => ({
      durum: d,
      ucSayimi: sayim.durum.get(d) ?? null,
      panoSayimi: kendiDurumSayimi.get(d) ?? 0,
    }))
    .concat(
      // Ucun sözlüğünde OLMAYAN bir durum gelirse (ayrıştırıcı büyürse) sessizce
      // düşmesin: bilinmeyen kovalar da tabloya girer.
      [...kendiDurumSayimi.keys()]
        .filter((d) => !DURUM_SIRASI.includes(d as (typeof DURUM_SIRASI)[number]))
        .map((d) => ({ durum: d, ucSayimi: sayim.durum.get(d) ?? null, panoSayimi: kendiDurumSayimi.get(d) ?? 0 })),
    );

  return (
    <div className="flex flex-col gap-4">
      {/* ------------------------------ KÜNYE ---------------------------- */}
      <div className="flex flex-wrap items-center gap-1.5 rounded-lg border bg-muted/30 p-3">
        <span className="text-muted-foreground text-xs">KAYNAK</span>
        <code className="font-mono text-xs">{kunye.yol ?? "yol yazılmadı"}</code>
        {kunye.satirN !== null ? (
          <Badge variant="ghost" className="tabular-nums text-[11px]">
            {kunye.satirN} satır
          </Badge>
        ) : null}
        {kunye.bayt !== null ? (
          <Badge variant="ghost" className="tabular-nums text-[11px]">
            {Math.round(kunye.bayt / 1024)} KB
          </Badge>
        ) : null}
        {kunye.mtime !== null ? (
          <Badge variant="outline" className="text-[11px]" title="dosyanın son değişiklik damgası (UTC)">
            {kunye.mtime.replace("T", " ").replace("+00:00", "Z")}
          </Badge>
        ) : (
          <Badge variant="ghost" className="text-[11px]" title="uç `mtime` göndermedi">
            tarih ölçülemedi
          </Badge>
        )}
        {kunye.hamTavan !== null ? (
          <Badge
            variant="ghost"
            className="text-[11px]"
            title="madde gövdeleri bu karakterde kırpılıyor; kırpılan kart 'kırpıldı' damgası taşır"
          >
            gövde tavanı {kunye.hamTavan}
          </Badge>
        ) : null}
      </div>

      {okuma.okunamayan > 0 ? (
        <Alert variant="destructive">
          <Info />
          <AlertTitle>{okuma.okunamayan} satır okunamadı</AlertTitle>
          <AlertDescription>
            Bu bölüm/madde satırları nesne değildi ve tahtanın DIŞINDA kaldı — sayaçlar onları
            içermiyor.
          </AlertDescription>
        </Alert>
      ) : null}

      {beyanAyrisiyor ? (
        <Alert variant="destructive">
          <Info />
          <AlertTitle>Madde sayısı ayrışıyor</AlertTitle>
          <AlertDescription>
            Uç {sayim.maddeN} madde beyan etti, pano ağacı düzleştirince {bizimN} madde saydı. İkisi
            aynı ağaca bakmalıydı; fark, tahtanın belgenin bir dalını atladığına işaret eder.
          </AlertDescription>
        </Alert>
      ) : null}

      {/* --------------------------- İKİ ÖLÇÜM --------------------------- */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rows3 className="size-4 text-muted-foreground" aria-hidden />
              Bölüm başına madde
            </CardTitle>
            <CardDescription>
              Kolonlar bu dağılımdan doğuyor — bölüm adları belgeden okundu, panoya gömülü değil.
            </CardDescription>
            <CardAction>
              <Badge variant="outline" className="tabular-nums">
                {bolumler.length} bölüm
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="min-w-0 overflow-x-auto">
              <ChartContainer
                config={durumAyari}
                className="w-full"
                style={{ height: `${Math.max(200, bolumler.length * 34 + 40)}px` }}
              >
                <BarChart accessibilityLayer data={grafikVerisi} layout="vertical" margin={{ left: 4, right: 16 }}>
                  <CartesianGrid horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="bolum"
                    axisLine={false}
                    tickLine={false}
                    tickMargin={6}
                    width={64}
                    tick={{ fontSize: 11 }}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "var(--muted)" }} />
                  <ChartLegend
                    align="right"
                    verticalAlign="top"
                    content={<ChartLegendContent className="justify-end" />}
                  />
                  {DURUM_SIRASI.map((d) => (
                    <Bar isAnimationActive={false} key={d} dataKey={d} stackId="d" fill={`var(--color-${d})`} />
                  ))}
                </BarChart>
              </ChartContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Durum dağılımı</CardTitle>
            <CardDescription>
              Ucun ayrıştırıcısının beş kovası — pano bunları birleştirmiyor, yorumlamıyor.
            </CardDescription>
            <CardAction>
              <Badge variant="outline" className="tabular-nums">
                {bizimN} madde
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="min-w-0 overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow>
                    <TableHead>Durum</TableHead>
                    <TableHead>Uç beyanı</TableHead>
                    <TableHead>Pano sayımı</TableHead>
                    <TableHead>Pay</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {durumSatirlari.map((s) => (
                    <TableRow key={s.durum}>
                      <TableCell>
                        <Badge variant={durumRozetiTonu(s.durum)} className="text-[11px]">
                          {DURUM_ETIKETI[s.durum] ?? s.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="tabular-nums text-xs">
                        {s.ucSayimi === null ? (
                          <span className="text-muted-foreground" title="uç bu aralığı `sayim.durum` içinde göndermedi">
                            ölçülemedi
                          </span>
                        ) : (
                          s.ucSayimi
                        )}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "tabular-nums text-xs",
                          s.ucSayimi !== null && s.ucSayimi !== s.panoSayimi && "font-medium text-destructive",
                        )}
                      >
                        {s.panoSayimi}
                      </TableCell>
                      <TableCell className="tabular-nums text-xs">
                        {bizimN === 0 ? "—" : `${Math.round((100 * s.panoSayimi) / bizimN)}%`}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <p className="text-muted-foreground text-xs leading-5">
              "belirsiz" AÇIK DEMEK DEĞİLDİR: belgedeki maddelerin çoğu düzyazıdır ve durum işareti
              taşımaz. Onları "açık" saymak, tahtanın üstüne ölçülmemiş bir sayı yazmak olurdu.
              {durumsuz > 0 ? ` Ayrıca ${durumsuz} maddede \`durum\` alanı hiç yok.` : ""}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* --------------------------- SÜZGEÇ ------------------------------ */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-muted-foreground text-xs">SÜZGEÇ</span>
        <Button
          variant={suzgec === null ? "default" : "outline"}
          size="sm"
          className="h-7 px-2.5 text-xs"
          onClick={() => setSuzgec(null)}
        >
          hepsi · {bizimN}
        </Button>
        {durumSatirlari.map((s) => (
          <Button
            key={s.durum}
            variant={suzgec === s.durum ? "default" : "outline"}
            size="sm"
            className="h-7 px-2.5 text-xs"
            onClick={() => setSuzgec(suzgec === s.durum ? null : s.durum)}
          >
            {DURUM_ETIKETI[s.durum] ?? s.durum} · {s.panoSayimi}
          </Button>
        ))}
      </div>

      {/* ---------------------------- TAHTA ------------------------------ */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {bolumler.map((b) => (
          <Kolon key={b.anahtar} b={b} maddeler={suzulmus(b)} />
        ))}
      </div>
    </div>
  );
}
