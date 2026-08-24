"use client";

/* ============================================================================
   KOŞU DEFTERİ — `pipeline_runs.jsonl` (son 40 satır, uç kırpıyor)
   ----------------------------------------------------------------------------
   BU DEFTER "SAAT" SORUSUNUN GERÇEK CEVABI: bekçi damgası bir adımın SON koşusunu
   söyler, koşu defteri her koşunun BAŞLANGICINI ve BİTİŞİNİ ayrı ayrı yazar —
   yani süre burada ÖLÇÜLÜR, tahmin edilmez (`cizelge.ts` → `kosulariOlc`).

   `skills_declared_not_run` SÜTUNU BİLEREK DURUYOR: "beyan edildi ama koşmadı",
   bir hattın sessizce boş dönmesinin tek kanıtıdır ve yalnız bu defterde ölçülüyor
   (api.py:1846 şerhi). Sıfırdan büyükse satır ayrışır — `status: ok` bir koşunun
   iş yaptığını KANITLAMAZ.

   SIFIR SANİYE BİR ÖLÇÜMDÜR, BİR EKSİKLİK DEĞİL: `started == finished` satırlar
   defterde gerçekten var (P3_PLAN, canlı örnek) ve "0 sn" yazmak doğrudur. Damgası
   okunamayan satır ise "ölçülemedi" der — ikisi aynı hücrede karışmaz.
   ============================================================================ */
import { useMemo, useState } from "react";

import { type ColumnDef, type SortingState, useTable } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import { Deger, HukumRozet, Olculemedi, sureMetni, zamanMetni, zamanMs } from "./parcalar";
import type { KosuSatiri } from "./cizelge";

const GRAFIK: ChartConfig = {
  saniye: { label: "süre (sn)" },
  ok: { label: "ok", color: "var(--chart-2)" },
  hata: { label: "hata", color: "var(--destructive)" },
};

/** Ölçülemeyen süre sıralamada EN SONA. */
const OLCULEMEDI = Number.NEGATIVE_INFINITY;

function durumTonu(durum: string | undefined): "iyi" | "kotu" | "olculemedi" {
  if (durum === undefined) return "olculemedi";
  return durum === "ok" ? "iyi" : "kotu";
}

const KOLONLAR: ColumnDef<DataTableFeatures, KosuSatiri>[] = [
  {
    id: "pipeline",
    accessorFn: (s) => s.kosu.pipeline ?? "",
    header: "Hat",
    cell: ({ row }) => (
      <div className="flex min-w-0 flex-col gap-0.5">
        {row.original.kosu.pipeline ? (
          <code className="font-mono text-xs">{row.original.kosu.pipeline}</code>
        ) : (
          <Olculemedi neden="satır `pipeline` taşımıyor" kisa />
        )}
        <span className="max-w-[22rem] truncate text-muted-foreground text-[11px]" title={row.original.kosu.run_id}>
          {row.original.kosu.run_id ?? "koşu kimliği yazılmamış"}
        </span>
      </div>
    ),
  },
  {
    id: "basladi",
    accessorFn: (s) => zamanMs(s.kosu.started) ?? OLCULEMEDI,
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 h-8 px-2 text-xs"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Başladı
        <ArrowUpDown className="ml-1 size-3" aria-hidden />
      </Button>
    ),
    cell: ({ row }) =>
      zamanMetni(row.original.kosu.started) ?? <Olculemedi neden="`started` damgası okunamadı" kisa />,
  },
  {
    id: "sure",
    accessorFn: (s) => s.sureSaniye ?? OLCULEMEDI,
    header: "Süre",
    cell: ({ row }) =>
      row.original.sureSaniye === null ? (
        <Olculemedi neden={row.original.sureNeden} kisa />
      ) : (
        <span className="tabular-nums text-xs">{sureMetni(row.original.sureSaniye) ?? "0sn"}</span>
      ),
  },
  {
    id: "durum",
    accessorFn: (s) => s.kosu.status ?? "",
    header: "Durum",
    cell: ({ row }) => (
      <div className="flex flex-col gap-1">
        <HukumRozet
          ton={durumTonu(row.original.kosu.status)}
          metin={row.original.kosu.status ?? "yazılmamış"}
          baslik="koşu defterinin kendi `status` alanı"
        />
        {row.original.kosu.error ? (
          <span className="max-w-[20rem] truncate text-destructive text-[11px]" title={row.original.kosu.error}>
            {row.original.kosu.error}
          </span>
        ) : null}
      </div>
    ),
  },
  {
    id: "skiller",
    accessorFn: (s) => s.kosu.skills_invoked ?? -1,
    header: "Skill (koşan / beyan edilip koşmayan / atlanan)",
    cell: ({ row }) => {
      const beyanKosmayan = row.original.kosu.skills_declared_not_run;
      return (
        <div className="flex items-center gap-1.5 text-xs tabular-nums">
          <Badge variant="secondary" title="`skills_invoked` — gerçekten koşan skill sayısı">
            <Deger deger={row.original.kosu.skills_invoked} neden="`skills_invoked` yazılmamış" />
          </Badge>
          <Badge
            variant={beyanKosmayan !== undefined && beyanKosmayan > 0 ? "destructive" : "outline"}
            title="`skills_declared_not_run` — beyan edildi ama KOŞMADI; hattın sessizce boş dönmesinin tek kanıtı"
          >
            <Deger deger={beyanKosmayan} neden="`skills_declared_not_run` yazılmamış" />
          </Badge>
          <Badge variant="outline" title="`skills_skipped` — kapı/koşul nedeniyle atlanan">
            <Deger deger={row.original.kosu.skills_skipped} neden="`skills_skipped` yazılmamış" />
          </Badge>
        </div>
      );
    },
  },
  {
    id: "artefakt",
    accessorFn: (s) => s.kosu.artifacts ?? -1,
    header: "Artefakt",
    cell: ({ row }) => <Deger deger={row.original.kosu.artifacts} neden="`artifacts` yazılmamış" />,
  },
];

export function KosuTablosu({ satirlar }: { readonly satirlar: readonly KosuSatiri[] }) {
  const [siralama, setSiralama] = useState<SortingState>([{ id: "basladi", desc: true }]);
  const veri = useMemo(() => [...satirlar], [satirlar]);

  // GRAFİK YALNIZ SÜRESİ ÖLÇÜLEN KOŞULARI ALIR: ölçülemeyen süreyi 0 çizmek, hiç bitmemiş
  // bir koşuyu "anında bitti" diye göstermek olurdu. En yeni 20 koşu (defter zaten 40'ta kırpık).
  const grafikVerisi = useMemo(
    () =>
      satirlar
        .filter((s): s is KosuSatiri & { sureSaniye: number } => s.sureSaniye !== null)
        .slice(0, 20)
        .map((s) => ({
          etiket: `${s.kosu.pipeline ?? "?"} · ${(s.kosu.started ?? "").slice(11, 16)}`,
          saniye: s.sureSaniye,
          hata: s.kosu.status !== "ok",
        }))
        .reverse(),
    [satirlar],
  );

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: KOLONLAR,
    getRowId: (s, i) => s.kosu.run_id ?? `kosu#${i}`,
    state: { sorting: siralama },
    onSortingChange: setSiralama,
  });

  return (
    <div className="flex flex-col gap-4">
      {grafikVerisi.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Süresi ölçülebilen koşu yok — grafik çizilmedi. (Süre iki damganın farkıdır; biri
          eksikse çizilmez, 0 sayılmaz.)
        </p>
      ) : (
        <ChartContainer config={GRAFIK} className="aspect-auto h-56 w-full">
          <BarChart data={grafikVerisi} margin={{ left: 8, right: 8, bottom: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="etiket" tickLine={false} axisLine={false} interval={0} angle={-35} textAnchor="end" height={72} className="text-[10px]" />
            <YAxis tickLine={false} axisLine={false} tickFormatter={(v: number) => `${v}s`} />
            <ChartTooltip
              content={<ChartTooltipContent nameKey="saniye" formatter={(v) => `${Number(v).toFixed(1)} sn`} />}
            />
            <Bar isAnimationActive={false} dataKey="saniye" radius={[4, 4, 0, 0]}>
              {grafikVerisi.map((s, i) => (
                <Cell key={`${s.etiket}#${i}`} fill={s.hata ? "var(--color-hata)" : "var(--color-ok)"} />
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
                    Koşu defteri boş döndü — &quot;hiç koşmadı&quot; DEĞİL, bu pencerede satır yok.
                  </span>
                </TableCell>
              </TableRow>
            ) : (
              tablo.getRowModel().rows.map((satir) => (
                <TableRow
                  key={satir.id}
                  className={cn(
                    satir.original.kosu.status !== undefined && satir.original.kosu.status !== "ok" && "bg-destructive/5",
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
        Defteri uç <strong>son 40 satırda kırpıyor</strong> (api.py:4029) — liste hattın tarihi
        değil, son iki-üç gecesidir. Kırmızı rozet: beyan edilip koşmayan skill; sayı sıfırdan
        büyükken <code className="font-mono text-[11px]">status: ok</code> tek başına
        &quot;iş yapıldı&quot; anlamına gelmez.
      </p>
    </div>
  );
}
