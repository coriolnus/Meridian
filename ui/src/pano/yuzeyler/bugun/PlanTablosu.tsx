"use client";

/* ============================================================================
   GÜNÜN PLANLARI — TanStack v9 tablosu
   ----------------------------------------------------------------------------
   Şablonun `default/_components/recent-customers-table/` grameri: `useTable` +
   ortak `dataTableFeatures` kaydı + `table.FlexRender`. Özellik kaydı v9'da AÇIK
   yazılmak zorunda ve depoda TEK bir tane var (`@/lib/data-table-features`) —
   kendi kaydımı kurmak, iki tablonun aynı özelliklere farklı cevap vermesi
   demekti.

   SATIR KİMLİĞİ: plan defterindeki `id` (`P-2026-07-28-PANW-exhaustion_hammer`
   biçiminde, yerel defterde ölçüldü). `id` YOKSA satır atılmaz — dizinden türetilmiş
   bir kimlik alır ve hücrede kimliğinin ölçülemediği YAZAR. Kimliksiz bir planı
   listeden düşürmek, ölçülmüş bir kararı ekrandan silmek olurdu.

   SIRALAMA ARTEFAKTI BEYAN EDİLİR: ölçülemeyen bir alan sıralamada boş dizge/0 gibi
   davranır ve o satırlar bir uca toplanır. Bu bir İDDİA DEĞİL, sıralamanın yan
   etkisidir; hücre yine "ölçülemedi" yazar, sayfa altında da not düşülür.
   ============================================================================ */
import { useMemo, useState } from "react";

import type { Column, ColumnDef } from "@tanstack/react-table";
import {
  type ColumnFiltersState,
  type ColumnVisibilityState,
  type PaginationState,
  type SortingState,
  useTable,
} from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  CircleSlash,
  Search,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { DataTableFeatures } from "@/lib/data-table-features";
import { dataTableFeatures } from "@/lib/data-table-features";

import { bicimOran, bicimSayi } from "./ortak";
import type { BugunTam, Plan } from "./tipler";

interface PlanSatiri extends Plan {
  readonly satirId: string;
}

/** Ölçülemeyen hücrenin tek biçimi. `Olculemedi` kart içi (iki satırlı) olduğundan
 *  tablo hücresinde onun yerine bu tek satırlık biçim kullanılıyor — nedeni `title`
 *  taşır, çünkü bir tablo hücresi iki satırlık gerekçeyi kaldırmaz. */
function Yok({ neden }: { neden: string }) {
  return (
    <span className="text-muted-foreground text-xs italic" title={neden}>
      ölçülemedi
    </span>
  );
}

function SiraIkonu({ yon }: { yon: false | "asc" | "desc" }) {
  if (yon === "asc") return <ArrowUp className="size-3.5" aria-hidden />;
  if (yon === "desc") return <ArrowDown className="size-3.5" aria-hidden />;
  return <ArrowUpDown className="size-3.5" aria-hidden />;
}

function SiraliBaslik({ sutun, etiket }: { sutun: Column<DataTableFeatures, PlanSatiri, unknown>; etiket: string }) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-2 text-muted-foreground"
      onClick={() => sutun.toggleSorting(sutun.getIsSorted() === "asc")}
    >
      {etiket}
      <SiraIkonu yon={sutun.getIsSorted()} />
    </Button>
  );
}

/** Hüküm rozeti. RENK ANLAM TAŞIMIYOR, İKON VE METİN TAŞIYOR: NO_GO kapının normal
 *  ve en sık çıktısıdır (yerel defterde son seansın 10 planının 10'u NO_GO, ölçüldü
 *  2026-08-25) — kırmızıya boyamak sakin bir günü olay gibi gösterirdi. Dikkat çeken
 *  tek hüküm REVIEW'dur, çünkü SENDEN iş ister; o da `primary` ile öne çıkar. */
function HukumRozeti({ hukum }: { hukum: string | undefined }) {
  if (hukum === undefined) return <Yok neden="plan kaydında `gate_verdict` alanı yok" />;
  if (hukum === "GO") {
    return (
      <Badge variant="outline">
        <CircleCheck className="size-3" aria-hidden />
        GO
      </Badge>
    );
  }
  if (hukum === "REVIEW") {
    return (
      <Badge variant="outline" className="border-primary/40 text-primary">
        <CircleAlert className="size-3" aria-hidden />
        REVIEW
      </Badge>
    );
  }
  if (hukum === "NO_GO") {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        <CircleSlash className="size-3" aria-hidden />
        NO_GO
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-muted-foreground">
      <CircleHelp className="size-3" aria-hidden />
      {hukum}
    </Badge>
  );
}

const SUTUNLAR: ColumnDef<DataTableFeatures, PlanSatiri>[] = [
  {
    id: "ticker",
    accessorFn: (r) => r.ticker ?? "",
    header: ({ column }) => <SiraliBaslik sutun={column} etiket="Sembol" />,
    cell: ({ row }) =>
      row.original.ticker === undefined ? (
        <Yok neden="plan kaydında `ticker` alanı yok" />
      ) : (
        <div className="flex flex-col gap-0.5">
          <span className="font-medium text-sm leading-none">{row.original.ticker}</span>
          <span className="truncate text-muted-foreground text-xs leading-none">
            {row.original.id ?? "kimliksiz plan"}
          </span>
        </div>
      ),
    enableHiding: false,
  },
  {
    id: "setup",
    accessorFn: (r) => r.setup ?? "",
    header: ({ column }) => <SiraliBaslik sutun={column} etiket="Kurulum" />,
    cell: ({ row }) =>
      row.original.setup === undefined ? (
        <Yok neden="plan kaydında `setup` alanı yok" />
      ) : (
        <span className="text-sm">{row.original.setup}</span>
      ),
  },
  {
    id: "verdict",
    accessorFn: (r) => r.gate_verdict ?? "",
    header: ({ column }) => <SiraliBaslik sutun={column} etiket="Hüküm" />,
    cell: ({ row }) => <HukumRozeti hukum={row.original.gate_verdict} />,
  },
  {
    id: "score",
    // SIRALAMA İÇİN -1: ölçülemeyen skor sıralamada bir yere düşmek ZORUNDA ve en
    // düşük skorun altına düşmesi, onu "kötü skor" diye okutmaz — hücre "ölçülemedi"
    // yazmaya devam eder. Sayfa altındaki not bu artefaktı beyan ediyor.
    accessorFn: (r) => (typeof r.score === "number" ? r.score : -1),
    header: ({ column }) => <SiraliBaslik sutun={column} etiket="Skor" />,
    cell: ({ row }) =>
      row.original.score === undefined ? (
        <Yok neden="plan kaydında `score` alanı yok" />
      ) : row.original.score === null ? (
        <Yok neden="plan kaydında `score` ölçülmemiş (null)" />
      ) : (
        <span className="tabular-nums text-sm">{bicimSayi(row.original.score)}</span>
      ),
  },
  {
    id: "sector",
    accessorFn: (r) => r.sector ?? "",
    header: ({ column }) => <SiraliBaslik sutun={column} etiket="Sektör" />,
    cell: ({ row }) =>
      row.original.sector === undefined ? (
        <Yok neden="plan kaydında `sector` alanı yok" />
      ) : (
        <span className="text-muted-foreground text-sm">{row.original.sector}</span>
      ),
  },
  {
    id: "entry",
    accessorFn: (r) => (typeof r.entry_trigger === "number" ? r.entry_trigger : -1),
    header: ({ column }) => <SiraliBaslik sutun={column} etiket="Giriş tetiği" />,
    cell: ({ row }) => {
      const p = row.original;
      if (p.entry_trigger === undefined) return <Yok neden="plan kaydında `entry_trigger` alanı yok" />;
      if (p.entry_trigger === null) return <Yok neden="`entry_trigger` ölçülmemiş (null)" />;
      return (
        <div className="flex flex-col gap-0.5">
          <span className="tabular-nums text-sm leading-none">{bicimSayi(p.entry_trigger)}</span>
          {/* SÜRÜKLENME YALNIZ UÇ ÖLÇTÜYSE VAR: `drift_pct` `_enrich_stale_plans`te
              ve SADECE `entry_trigger > 0` iken yazılıyor (api.py:5841). Yoksa satır
              hiç çizilmiyor — "%0 sürüklenme" yazmak ölçülmemiş bir sıfır olurdu. */}
          {p.drift_pct !== undefined ? (
            <span className="text-muted-foreground text-xs leading-none">son kapanış {bicimOran(p.drift_pct)}</span>
          ) : null}
        </div>
      );
    },
  },
  {
    id: "durum",
    accessorFn: (r) => (r.onay_bekliyor ? 2 : r.traded ? 1 : 0),
    header: "Durum",
    cell: ({ row }) => {
      const p = row.original;
      // ÜÇ DAMGA DA UÇ KATMANINDAN GELİYOR ve hiçbiri varsayılmıyor: `undefined` ise
      // damgalama koşmamış demektir ve o da bir bilgidir — "damga yok" yazılır.
      if (p.expired === undefined && p.traded === undefined && p.onay_bekliyor === undefined) {
        return <Yok neden="bayatlık/onay damgaları bu satıra basılmamış (uç zenginleştirmesi koşmadı)" />;
      }
      return (
        <div className="flex flex-wrap gap-1">
          {p.onay_bekliyor === true ? <Badge variant="default">onayını bekliyor</Badge> : null}
          {p.traded === true ? (
            <Badge variant="outline" className="text-muted-foreground">
              işleme döndü
            </Badge>
          ) : null}
          {p.expired === true ? (
            <Badge variant="outline" className="text-muted-foreground">
              seansı geçmiş{p.age_days !== undefined ? ` (${bicimSayi(p.age_days)} gün)` : ""}
            </Badge>
          ) : null}
          {p.onay_bekliyor !== true && p.traded !== true && p.expired !== true ? (
            <span className="text-muted-foreground text-xs">—</span>
          ) : null}
        </div>
      );
    },
  },
  {
    id: "arama",
    accessorFn: (r) => `${r.ticker ?? ""} ${r.setup ?? ""} ${r.sector ?? ""} ${r.gate_verdict ?? ""}`,
    filterFn: "includesString",
    enableHiding: true,
  },
];

export function PlanTablosu({ b }: { b: BugunTam }) {
  const planlar = b.todays_plans;

  const satirlar = useMemo<PlanSatiri[]>(
    () => (planlar ?? []).map((p, i) => ({ ...p, satirId: p.id ?? `kimliksiz-${i}` })),
    [planlar],
  );

  const [sorting, setSorting] = useState<SortingState>([{ id: "score", desc: true }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility] = useState<ColumnVisibilityState>({ arama: false });
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });

  const table = useTable({
    features: dataTableFeatures,
    data: satirlar,
    columns: SUTUNLAR,
    state: { sorting, columnFilters, columnVisibility, pagination },
    getRowId: (row) => row.satirId,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
  });

  const arama = (table.getColumn("arama")?.getFilterValue() as string | undefined) ?? "";
  const suzulen = table.getFilteredRowModel().rows.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">Günün planları</CardTitle>
        <CardDescription>
          {planlar === undefined
            ? "ölçülemedi — `/api/today` gövdesinde `todays_plans` alanı yok"
            : b.todays_plan_date === undefined || b.todays_plan_date === null
              ? `${bicimSayi(satirlar.length)} plan · seans tarihi ölçülemedi`
              : `${b.todays_plan_date} seansı · ${bicimSayi(satirlar.length)} plan`}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        {planlar === undefined ? (
          <p className="text-muted-foreground text-sm">
            Plan listesi okunamadı: gövdede `todays_plans` alanı yok. Boş tablo çizmek "bu seans plan kurulmadı"
            demek olurdu — ölçmediğimiz bir şey.
          </p>
        ) : (
          <>
            <div className="relative w-full lg:w-80">
              <Search
                className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden
              />
              <Input
                className="h-8 pl-8"
                placeholder="Sembol, kurulum, sektör, hüküm…"
                value={arama}
                onChange={(e) => {
                  table.getColumn("arama")?.setFilterValue(e.target.value || undefined);
                  table.setPageIndex(0);
                }}
              />
            </div>

            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/15">
                  {table.getHeaderGroups().map((hg) => (
                    <TableRow key={hg.id}>
                      {hg.headers.map((h) => (
                        <TableHead key={h.id} colSpan={h.colSpan} className="h-11 p-3 font-medium">
                          {h.isPlaceholder ? null : <table.FlexRender header={h} />}
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {table.getRowModel().rows.length > 0 ? (
                    table.getRowModel().rows.map((row) => (
                      <TableRow key={row.id}>
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id} className="p-3 align-middle">
                            <table.FlexRender cell={cell} />
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={table.getVisibleLeafColumns().length} className="h-24 text-center text-sm">
                        {satirlar.length === 0
                          ? "Bu seansta plan kurulmadı — defter boş döndü (ölçüldü)."
                          : "Aramaya uyan plan yok."}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-muted-foreground text-xs">
                {bicimSayi(suzulen)} / {bicimSayi(satirlar.length)} satır gösteriliyor. Sıralama artefaktı: ölçülemeyen
                skor ve giriş tetiği sıralamada en alta düşer — bu bir değer İDDİASI değil, hücre yine "ölçülemedi" yazar.
              </p>
              {table.getPageCount() > 1 ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm tabular-nums">
                    Sayfa {table.state.pagination.pageIndex + 1} / {table.getPageCount()}
                  </span>
                  <Button
                    variant="outline"
                    size="icon"
                    className="size-8"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                  >
                    <span className="sr-only">Önceki sayfa</span>
                    <ChevronLeft className="size-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="size-8"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                  >
                    <span className="sr-only">Sonraki sayfa</span>
                    <ChevronRight className="size-4" />
                  </Button>
                </div>
              ) : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
