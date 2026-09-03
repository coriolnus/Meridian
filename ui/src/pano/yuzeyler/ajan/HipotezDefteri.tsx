"use client";

/* ============================================================================
   HİPOTEZ DEFTERİ — aynı kayıtlar, sohbet değil TABLO okumasıyla
   ----------------------------------------------------------------------------
   NEDEN İKİ OKUMA: sohbet hattı bir cümleyi tam okumak için iyi, ama "hangi
   değişken kaç kez denendi", "en yüksek güvenli öneri hangisiydi" gibi soruları
   cevaplayamaz — onlar SIRALAMA sorularıdır. Aynı deftere iki pencere açmak
   veriyi çoğaltmaz; iki farklı soruya hizmet eder.

   ÖLÇÜLEMEYEN HÜCRE 0 BASMAZ: `realized_delta` defterin 41 satırının 1'inde var
   (ölçüldü 2026-08-25). Kalan 40 hücre "ölçülemedi" der ve nedenini `title`da
   taşır. Bu sütunu 0 ile doldurmak, öğrenme döngüsünü "hiç fark yaratmadı" diye
   okutan bir yalan üretirdi.

   Tablo TanStack v9 (`useTable` + `dataTableFeatures`) — `lib/data-table-features.ts`
   ile aynı özellik sözleşmesi; şablonun kendi kaydı.
   ============================================================================ */
import { useMemo, useState } from "react";

import { type ColumnDef, type SortingState, useTable } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import { DURUM_SOZLUGU, Olculemedi, bicimSayi, zamanMetni, type Hipotez } from "./ortak";

function SiralamaBasligi({
  etiket,
  column,
}: {
  etiket: string;
  column: { toggleSorting: (desc: boolean) => void; getIsSorted: () => false | "asc" | "desc" };
}) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-2 h-8 px-2 text-xs"
      onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
    >
      {etiket}
      <ArrowUpDown className="ml-1 size-3" aria-hidden />
    </Button>
  );
}

const kolonlar: ColumnDef<DataTableFeatures, Hipotez>[] = [
  {
    id: "ts",
    accessorFn: (h) => (h.ts === null ? "" : h.ts),
    header: ({ column }) => <SiralamaBasligi etiket="Zaman" column={column} />,
    cell: ({ row }) => {
      const z = zamanMetni(row.original.ts);
      return z === null ? (
        <Olculemedi neden="Önerinin ne zaman yapıldığı kaydedilmemiş" teknik="satırda `ts` alanı yok" />
      ) : (
        <span className="whitespace-nowrap text-xs tabular-nums">{z}</span>
      );
    },
  },
  {
    id: "id",
    accessorFn: (h) => h.id ?? "",
    header: "Kimlik",
    cell: ({ row }) =>
      row.original.id === null ? (
        <Olculemedi neden="Bu kaydın kimliği kaydedilmemiş" teknik="satırda `id` alanı yok" />
      ) : (
        <code className="font-mono text-xs">{row.original.id}</code>
      ),
  },
  {
    id: "kaynak",
    accessorFn: (h) => h.kaynak ?? "",
    header: ({ column }) => <SiralamaBasligi etiket="Kaynak" column={column} />,
    cell: ({ row }) =>
      row.original.kaynak === null ? (
        <Olculemedi neden="Öneriyi kimin yaptığı kaydedilmemiş" teknik="satırda `source` alanı yok" />
      ) : (
        <Badge variant={row.original.kaynak.startsWith("danışma:") ? "secondary" : "outline"} className="text-[10px]">
          {row.original.kaynak}
        </Badge>
      ),
  },
  {
    id: "degisken",
    accessorFn: (h) => h.degisken ?? "",
    header: ({ column }) => <SiralamaBasligi etiket="Değişken" column={column} />,
    cell: ({ row }) => (
      <div className="flex min-w-0 flex-col gap-0.5">
        <code className="break-all font-mono text-xs">{row.original.degisken ?? "(yazılmamış)"}</code>
        <span className="text-muted-foreground text-[11px]">
          {row.original.eski ?? "?"} → {row.original.yeni ?? "?"}
        </span>
      </div>
    ),
  },
  {
    id: "guven",
    accessorFn: (h) => h.guven ?? -1,
    header: ({ column }) => <SiralamaBasligi etiket="Güven" column={column} />,
    cell: ({ row }) =>
      row.original.guven === null ? (
        <Olculemedi neden="Öneriye duyulan güven kaydedilmemiş" teknik="satırda `confidence` alanı yok" />
      ) : (
        <span className="text-xs tabular-nums">%{bicimSayi(row.original.guven * 100, 0)}</span>
      ),
  },
  {
    id: "tahmin",
    accessorFn: (h) => h.tahminDelta ?? 0,
    header: ({ column }) => <SiralamaBasligi etiket="Tahmin Δ" column={column} />,
    cell: ({ row }) =>
      row.original.tahminDelta === null ? (
        <Olculemedi neden="Öneriden beklenen etki kaydedilmemiş" teknik="satırda `predicted_delta` alanı yok" />
      ) : (
        <span className="text-xs tabular-nums">{bicimSayi(row.original.tahminDelta, 4, true)}</span>
      ),
  },
  {
    id: "gerceklesen",
    accessorFn: (h) => h.gerceklesenDelta ?? Number.NEGATIVE_INFINITY,
    header: ({ column }) => <SiralamaBasligi etiket="Gerçekleşen Δ" column={column} />,
    cell: ({ row }) => {
      const g = row.original.gerceklesenDelta;
      if (g === null) {
        return (
          <Olculemedi neden="Öneri canlıya çıkmadı, sonucu hiç ölçülmedi (sıfır değil)" teknik="`realized_delta` yazılmamış" />
        );
      }
      return (
        <span
          className={cn(
            "text-xs tabular-nums",
            g > 0 ? "text-[var(--yon-arti)]" : g < 0 ? "text-[var(--yon-eksi)]" : undefined,
          )}
        >
          {bicimSayi(g, 4, true)}
        </span>
      );
    },
  },
  {
    id: "durum",
    accessorFn: (h) => h.durum ?? "",
    header: ({ column }) => <SiralamaBasligi etiket="Karar" column={column} />,
    cell: ({ row }) => {
      const d = row.original.durum;
      if (d === null) return <Olculemedi neden="Öneri hakkındaki karar kaydedilmemiş" teknik="satırda `status` alanı yok" />;
      const s = DURUM_SOZLUGU[d];
      return (
        <Badge
          variant={s?.ton === "olumsuz" ? "destructive" : s?.ton === "olumlu" ? "default" : "outline"}
          className="text-[10px]"
          title={s === undefined ? `sözlükte olmayan durum: ${d}` : d}
        >
          {s?.etiket ?? d}
        </Badge>
      );
    },
  },
  {
    id: "red",
    accessorFn: (h) => h.redNedenleri.length,
    header: "Ret gerekçesi",
    cell: ({ row }) => {
      const r = row.original.redNedenleri;
      if (r.length === 0) {
        return (
          <span className="text-muted-foreground text-xs" title="`reject_reasons` yazılmamış ya da boş">
            yok
          </span>
        );
      }
      return (
        <span className="line-clamp-2 max-w-72 text-xs leading-snug" title={r.join(" · ")}>
          {r[0]}
          {r.length > 1 ? ` (+${bicimSayi(r.length - 1)})` : null}
        </span>
      );
    },
  },
];

export function HipotezDefteri({ hipotezler }: { hipotezler: readonly Hipotez[] }) {
  const [siralama, setSiralama] = useState<SortingState>([{ id: "ts", desc: true }]);
  const veri = useMemo(() => [...hipotezler], [hipotezler]);

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: kolonlar,
    getRowId: (h, i) => h.id ?? `satir-${i}`,
    state: { sorting: siralama },
    onSortingChange: setSiralama,
  });

  const sonucluN = veri.filter((h) => h.gerceklesenDelta !== null).length;

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
                  <TableCell key={hucre.id} className="align-top">
                    <tablo.FlexRender cell={hucre} />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <p className="text-muted-foreground text-xs leading-5">
        Defterde {bicimSayi(veri.length)} kayıt var; {bicimSayi(sonucluN)} tanesine sonuç
        (`realized_delta`) yazılmış. Kalan {bicimSayi(veri.length - sonucluN)} kayıt BAŞARISIZ DEĞİL,
        SONUÇSUZ: öneri kapıdan geçmediği için canlıda hiç ölçülmedi.
      </p>
    </div>
  );
}
