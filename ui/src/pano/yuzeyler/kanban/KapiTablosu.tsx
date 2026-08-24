"use client";

/* ============================================================================
   KAPI TABLOSU — hangi ölçüt kaç adayı eledi
   ----------------------------------------------------------------------------
   `gate_checks` alanı 2026-07-21'den beri her planda karar ağacını taşıyor ama
   "kapı neyi eliyor" sorusu panoda hiç ölçülmemişti (analytics.py:3675'in
   şerhi). Bu tablo o soruyu O SEANSIN planları üzerinde cevaplıyor.

   PAYDA DÜRÜSTÇE BEYAN EDİLİYOR: bir kapı satırı YALNIZ onu yazan planlarda
   değerlendirilir. `gate_checks` taşımayan planlar (eski satırlar, replay
   tohumu — `backtest.py:472`) paydanın DIŞINDADIR ve sayıları tablonun altında
   ayrıca yazılı. Onları payda saymak, hiç sorulmamış bir kapıyı "geçti" diye
   saymak olurdu.

   Tablo TanStack v9 (`useTable` + `dataTableFeatures`) — şablonun kendi kaydıyla
   aynı özellik sözleşmesi (`lib/data-table-features.ts` başlığı).
   ============================================================================ */
import { useMemo, useState } from "react";

import { type ColumnDef, type SortingState, useTable } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import type { Plan } from "./planlar";

export interface KapiSatiri {
  readonly ad: string;
  readonly siddet: string | null;
  /** Bu kapıyı YAZAN plan sayısı (payda). */
  readonly payda: number;
  readonly gecen: number;
  readonly dusen: number;
  /** Satır var ama `passed` mantık değeri değil — ne geçti ne düştü. */
  readonly olcumsuz: number;
  /** `dusen / (gecen + dusen)`. Paydası sıfırsa `null` — 0 yazmak yalan olurdu. */
  readonly dususOrani: number | null;
  /** Kapının kendi `coverage` beyanı ("no_calendar_data" gibi) kaç planda geçti. */
  readonly kapsamNotlari: ReadonlyMap<string, number>;
}

export interface KapiOzeti {
  readonly satirlar: readonly KapiSatiri[];
  readonly kontrolluPlan: number;
  readonly kontrolsuzPlan: number;
  readonly toplamPlan: number;
}

export function kapilariOzetle(planlar: readonly Plan[]): KapiOzeti {
  const birikim = new Map<
    string,
    { siddet: string | null; payda: number; gecen: number; dusen: number; olcumsuz: number; kapsam: Map<string, number> }
  >();
  let kontrolluPlan = 0;

  for (const p of planlar) {
    if (!p.kontroller || p.kontroller.length === 0) continue;
    kontrolluPlan += 1;
    for (const k of p.kontroller) {
      const ad = k.ad ?? "(kontrol adı yazılmamış)";
      const mevcut = birikim.get(ad) ?? {
        siddet: k.siddet,
        payda: 0,
        gecen: 0,
        dusen: 0,
        olcumsuz: 0,
        kapsam: new Map<string, number>(),
      };
      mevcut.payda += 1;
      if (k.gecti === true) mevcut.gecen += 1;
      else if (k.gecti === false) mevcut.dusen += 1;
      else mevcut.olcumsuz += 1;
      // ŞİDDET İLK GÖRÜLENDEN alınır; satırlar arasında değişirse ilkini tutuyoruz
      // çünkü `loop.py` bir kontrolün şiddetini plan başına değiştirmiyor (hard/soft
      // kontrolün KENDİ özelliği). Değişirse tablo yanıltmasın diye null'a düşmüyoruz:
      // ilk değeri göstermek, hiç göstermemekten daha çok bilgi taşıyor.
      if (mevcut.siddet === null && k.siddet !== null) mevcut.siddet = k.siddet;
      if (k.kapsam !== null) mevcut.kapsam.set(k.kapsam, (mevcut.kapsam.get(k.kapsam) ?? 0) + 1);
      birikim.set(ad, mevcut);
    }
  }

  const satirlar: KapiSatiri[] = [];
  for (const [ad, v] of birikim) {
    const hukmedilen = v.gecen + v.dusen;
    satirlar.push({
      ad,
      siddet: v.siddet,
      payda: v.payda,
      gecen: v.gecen,
      dusen: v.dusen,
      olcumsuz: v.olcumsuz,
      dususOrani: hukmedilen > 0 ? v.dusen / hukmedilen : null,
      kapsamNotlari: v.kapsam,
    });
  }

  return {
    satirlar,
    kontrolluPlan,
    kontrolsuzPlan: planlar.length - kontrolluPlan,
    toplamPlan: planlar.length,
  };
}

const kolonlar: ColumnDef<DataTableFeatures, KapiSatiri>[] = [
  {
    accessorKey: "ad",
    header: "Kapı",
    cell: ({ row }) => (
      <div className="flex flex-col gap-1">
        <code className="break-all font-mono text-xs">{row.original.ad}</code>
        {row.original.siddet ? (
          <span className="text-muted-foreground text-[11px]">{row.original.siddet}</span>
        ) : null}
      </div>
    ),
  },
  {
    accessorKey: "payda",
    header: "Değerlendirilen",
    cell: ({ row }) => <span className="tabular-nums text-xs">{row.original.payda}</span>,
  },
  {
    accessorKey: "gecen",
    header: "Geçen",
    cell: ({ row }) => <span className="tabular-nums text-xs">{row.original.gecen}</span>,
  },
  {
    accessorKey: "dusen",
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 h-8 px-2 text-xs"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Düşen
        <ArrowUpDown className="ml-1 size-3" aria-hidden />
      </Button>
    ),
    cell: ({ row }) => (
      <span
        className={cn("tabular-nums text-xs", row.original.dusen > 0 && "font-medium text-destructive")}
      >
        {row.original.dusen}
      </span>
    ),
  },
  {
    accessorKey: "dususOrani",
    header: "Düşüş oranı",
    cell: ({ row }) =>
      row.original.dususOrani === null ? (
        <span
          className="text-muted-foreground text-xs"
          title="bu kapının hiçbir satırında `passed` mantık değeri yok — oran ölçülemedi"
        >
          ölçülemedi
        </span>
      ) : (
        <span className="tabular-nums text-xs">{(row.original.dususOrani * 100).toFixed(0)}%</span>
      ),
  },
  {
    accessorKey: "olcumsuz",
    header: "Ölçümsüz satır",
    cell: ({ row }) =>
      row.original.olcumsuz === 0 ? (
        <span className="text-muted-foreground text-xs">0</span>
      ) : (
        <Badge variant="outline" className="tabular-nums" title="`passed` alanı mantık değeri olmayan satırlar">
          {row.original.olcumsuz}
        </Badge>
      ),
  },
  {
    accessorKey: "kapsamNotlari",
    header: "Kapsam beyanı",
    cell: ({ row }) => {
      const notlar = [...row.original.kapsamNotlari.entries()];
      if (notlar.length === 0) {
        return (
          <span className="text-muted-foreground text-xs" title="bu kapı `coverage` alanı yazmıyor">
            —
          </span>
        );
      }
      return (
        <div className="flex flex-wrap gap-1">
          {notlar.map(([k, n]) => (
            <Badge key={k} variant="ghost" className="text-[10px]">
              {k} · {n}
            </Badge>
          ))}
        </div>
      );
    },
  },
];

export function KapiTablosu({ ozet }: { ozet: KapiOzeti }) {
  const [siralama, setSiralama] = useState<SortingState>([{ id: "dusen", desc: true }]);
  const veri = useMemo(() => [...ozet.satirlar], [ozet.satirlar]);

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: kolonlar,
    getRowId: (satir) => satir.ad,
    state: { sorting: siralama },
    onSortingChange: setSiralama,
  });

  return (
    <div className="flex flex-col gap-3">
      <div className="min-w-0 overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/30">
            {tablo.getHeaderGroups().map((grup) => (
              <TableRow key={grup.id}>
                {grup.headers.map((baslik) => (
                  <TableHead key={baslik.id}>
                    {baslik.isPlaceholder ? null : <tablo.FlexRender header={baslik} />}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {tablo.getRowModel().rows.map((satir) => (
              <TableRow key={satir.id}>
                {satir.getVisibleCells().map((hucre) => (
                  <TableCell key={hucre.id}>
                    <tablo.FlexRender cell={hucre} />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <p className="text-muted-foreground text-xs leading-5">
        PAYDA: {ozet.kontrolluPlan}/{ozet.toplamPlan} plan `gate_checks` dizisi taşıyor.
        {ozet.kontrolsuzPlan > 0 ? (
          <>
            {" "}
            Kalan {ozet.kontrolsuzPlan} plan bu tablonun DIŞINDA — o planlarda kapının ne dediği
            yazılmamış; "geçti" saymak ölçmediğimiz bir şeyi ölçülmüş göstermek olurdu.
          </>
        ) : null}
      </p>
    </div>
  );
}
