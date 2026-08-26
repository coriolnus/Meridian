"use client";

/* ============================================================================
   HATTIN ADIMLARI — hangi adım ne zaman koştu, hangisi gecikti
   ----------------------------------------------------------------------------
   GECİKEN ADIM GÖRSEL OLARAK AYRIŞIR (brief maddesi) ve ayrım ÜÇ KATLIDIR:
   satır zemini · hüküm rozeti · yaş çubuğunun rengi. Tek kat yeterli olmazdı —
   rozet renk körü bir okuyucuda kaybolur, zemin taramada gözden kaçar, çubuk tek
   başına "ne kadar geç" der ama "neye göre geç" demez.

   ÇUBUK GRAFİĞİ YAŞI GÖSTERİR, GECİKMEYİ DEĞİL ve bu bilinçli: gecikme
   (`gap_h − expected_h`) yalnız geciken satırlarda hesaplanabilirdi, yani grafiğin
   çoğu boş kalırdı. Yaş HER damgalı adımda ölçülü; pencereyi aşanlar renkle
   ayrışıyor. Damgası olmayan adım grafikte HİÇ ÇİZİLMEZ (sıfır uzunluk çubuk
   "az önce koştu" diye okunurdu) — tabloda satırı ve nedeni duruyor.
   ============================================================================ */
import { useMemo, useState } from "react";

import { type ColumnDef, type SortingState, useTable } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts";

import { Button } from "@/components/ui/button";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import { goreliMetin, HukumRozet, Olculemedi, zamanMetni, type HukumTonu } from "./parcalar";
import { HUKUM_ETIKET, type Adim, type AdimHukmu } from "./cizelge";

const HUKUM_TONU: Record<AdimHukmu, HukumTonu> = {
  penceresinde: "iyi",
  gecikti: "kotu",
  hic_kosmadi: "kotu",
  askida: "uyari",
  olculemedi: "olculemedi",
};

/** Çubuk rengi hükümle AYNI kaynaktan: iki yerde iki renk, yarın ayrışırdı. */
const HUKUM_RENGI: Record<AdimHukmu, string> = {
  penceresinde: "var(--color-penceresinde)",
  gecikti: "var(--color-gecikti)",
  hic_kosmadi: "var(--color-gecikti)",
  askida: "var(--color-askida)",
  olculemedi: "var(--color-olculemedi)",
};

const GRAFIK: ChartConfig = {
  yasSaat: { label: "sessizlik (saat)" },
  penceresinde: { label: "penceresinde", color: "var(--chart-2)" },
  gecikti: { label: "gecikti / hiç koşmadı", color: "var(--destructive)" },
  askida: { label: "askıda", color: "var(--chart-4)" },
  olculemedi: { label: "ölçülemedi", color: "var(--muted-foreground)" },
};

/**
 * Damgasız (hiç koşmamış) adımın sıralama değeri `+Infinity`: azalan sıralamada EN ÜSTE çıkar.
 * Bu bir estetik tercih değil, bekçinin kendi hüküm sıralaması — "geciken bir mekanizma
 * yavaşlamıştır, hiç koşmamış bir mekanizma KABLOLANMAMIŞTIR" (watchdog.py, `_sessiz_hat` şerhi).
 * Sıfır ya da `-Infinity` vermek, en yüksek sesli hâli listenin dibine gömerdi.
 */
const DAMGASIZ = Number.POSITIVE_INFINITY;

function kolonlariKur(simdi: number): ColumnDef<DataTableFeatures, Adim>[] {
  return [
    {
      id: "ad",
      accessorFn: (a) => a.ad,
      header: "Adım",
      cell: ({ row }) => (
        <div className="flex min-w-0 flex-col gap-0.5">
          <code className="break-all font-mono text-xs">{row.original.ad}</code>
          {row.original.askidaNeden ? (
            <span className="text-amber-700 text-[11px] dark:text-amber-400">
              askıya alma nedeni: {row.original.askidaNeden}
            </span>
          ) : null}
        </div>
      ),
    },
    {
      id: "hukum",
      accessorFn: (a) => a.hukum,
      header: "Karar",
      cell: ({ row }) => (
        <HukumRozet
          ton={HUKUM_TONU[row.original.hukum]}
          metin={HUKUM_ETIKET[row.original.hukum]}
          baslik={row.original.hukumNeden}
        />
      ),
    },
    {
      id: "sonKosu",
      // SIRALAMA ANAHTARI SESSİZLİK SÜRESİ: azalan sıralamada en uzun susan adım üstte.
      accessorFn: (a) => a.yasSaniye ?? DAMGASIZ,
      header: ({ column }) => (
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 h-8 px-2 text-xs"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Son koşu
          <ArrowUpDown className="ml-1 size-3" aria-hidden />
        </Button>
      ),
      cell: ({ row }) => {
        const mutlak = zamanMetni(row.original.sonKosuIso);
        if (mutlak === null) return <Olculemedi neden={row.original.sonKosuNeden} kisa />;
        const ms = row.original.yasSaniye === null ? null : simdi - row.original.yasSaniye * 1000;
        return (
          <div className="flex flex-col gap-0.5">
            <span className="tabular-nums text-xs">{mutlak}</span>
            <span className="text-muted-foreground text-[11px]">{goreliMetin(ms, simdi) ?? "yaş hesaplanamadı"}</span>
          </div>
        );
      },
    },
    {
      id: "pencere",
      accessorFn: (a) => a.pencereSaat ?? -1,
      header: "Beklenen pencere",
      cell: ({ row }) =>
        row.original.pencereSaat === null ? (
          <Olculemedi neden={row.original.pencereNeden} kisa />
        ) : (
          <div className="flex flex-col gap-0.5">
            <span className="tabular-nums text-xs">{row.original.pencereSaat} sa</span>
            {row.original.gapSaat !== null ? (
              <span className="text-destructive text-[11px] tabular-nums">
                bekçi ölçümü: {row.original.gapSaat} sa sessiz
              </span>
            ) : null}
          </div>
        ),
    },
    {
      id: "siradaki",
      accessorFn: (a) => a.siradakiIso ?? "",
      header: "Sırada",
      cell: ({ row }) => {
        const mutlak = zamanMetni(row.original.siradakiIso);
        if (mutlak === null) return <Olculemedi neden={row.original.siradakiNeden} kisa />;
        const ms = Date.parse(row.original.siradakiIso ?? "");
        const gecti = Number.isFinite(ms) && ms < simdi;
        return (
          <div className="flex flex-col gap-0.5">
            <span className={cn("tabular-nums text-xs", gecti && "font-medium text-destructive")}>{mutlak}</span>
            <span className="text-muted-foreground text-[11px]">
              {gecti ? "beklenen an GEÇTİ" : (goreliMetin(Number.isFinite(ms) ? ms : null, simdi) ?? "")}
            </span>
          </div>
        );
      },
    },
  ];
}

export function AdimTablosu({ adimlar, simdi }: { readonly adimlar: readonly Adim[]; readonly simdi: number }) {
  const [siralama, setSiralama] = useState<SortingState>([{ id: "sonKosu", desc: true }]);
  const kolonlar = useMemo(() => kolonlariKur(simdi), [simdi]);
  const veri = useMemo(() => [...adimlar], [adimlar]);

  // GRAFİK YALNIZ DAMGALI ADIMLARI ALIR (dosya başlığındaki gerekçe) ve en sessizden
  // en tazeye sıralanır: gözün ilk gittiği yer en tehlikeli satır olsun.
  const grafikVerisi = useMemo(
    () =>
      adimlar
        .filter((a): a is Adim & { yasSaniye: number } => a.yasSaniye !== null)
        .map((a) => ({ ad: a.ad, yasSaat: a.yasSaniye / 3600, hukum: a.hukum }))
        .sort((x, y) => y.yasSaat - x.yasSaat),
    [adimlar],
  );

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: kolonlar,
    getRowId: (a) => a.ad,
    state: { sorting: siralama },
    onSortingChange: setSiralama,
  });

  return (
    <div className="flex flex-col gap-4">
      {grafikVerisi.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Damgalı adım yok — grafik çizilmedi. Sıfır uzunluklu çubuk &quot;az önce koştu&quot; diye
          okunurdu.
        </p>
      ) : (
        <ChartContainer config={GRAFIK} className="aspect-auto h-72 w-full">
          <BarChart data={grafikVerisi} layout="vertical" margin={{ left: 8, right: 24 }}>
            <CartesianGrid horizontal={false} />
            <XAxis
              type="number"
              dataKey="yasSaat"
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `${v.toFixed(0)} sa`}
            />
            <YAxis type="category" dataKey="ad" tickLine={false} axisLine={false} width={148} className="text-[11px]" />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  nameKey="yasSaat"
                  formatter={(v) => `${Number(v).toFixed(1)} saattir sessiz`}
                />
              }
            />
            <Bar isAnimationActive={false} dataKey="yasSaat" radius={[0, 4, 4, 0]}>
              {grafikVerisi.map((s) => (
                <Cell key={s.ad} fill={HUKUM_RENGI[s.hukum]} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      )}

      <div className="min-w-0 overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/30">
            {tablo.getHeaderGroups().map((grup) => (
              <TableRow key={grup.id}>
                {grup.headers.map((baslik) => (
                  <TableHead key={baslik.id} className="whitespace-nowrap">
                    {baslik.isPlaceholder ? null : <tablo.FlexRender header={baslik} />}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {tablo.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={tablo.getVisibleLeafColumns().length} className="py-8 text-center">
                  <span className="text-muted-foreground text-sm">
                    Ne damga ne bekçi kovası satır döndürdü — bu, &quot;hat boş&quot; demek değil,
                    ölçülemedi demektir.
                  </span>
                </TableCell>
              </TableRow>
            ) : (
              tablo.getRowModel().rows.map((satir) => (
                <TableRow
                  key={satir.id}
                  className={cn(
                    (satir.original.hukum === "gecikti" || satir.original.hukum === "hic_kosmadi") &&
                      "bg-destructive/5",
                    satir.original.hukum === "askida" && "bg-amber-500/5",
                  )}
                >
                  {satir.getVisibleCells().map((hucre) => (
                    <TableCell key={hucre.id} className="align-top">
                      <tablo.FlexRender cell={hucre} />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <p className="text-muted-foreground text-xs leading-5">
        &quot;Sırada&quot; sütunu = son damga + beklenen pencere. Pencere uçtan YALNIZ geciken ve
        askıda satırlarda geliyor (<code className="font-mono text-[11px]">expected_h</code>);
        penceresinde koşan adımların penceresi <code className="font-mono text-[11px]">watchdog.EXPECTED</code>{" "}
        içinde ve panoya açılmamış. O satırlarda sıradaki koşu <strong>uydurulmadı</strong> —
        &quot;ölçülemedi&quot; yazıyor.
      </p>
    </div>
  );
}
