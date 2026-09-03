"use client";

/* ============================================================================
   EN ÇOK BAKILANLAR — dokuz facet, tek tabloda, kendi paydasıyla
   ----------------------------------------------------------------------------
   HER FACETİN PAYDASI AYRIDIR ve bu tabloda yazılı. Yedi facet kapanmış işlem
   defterini sayıyor, iki KAPI faceti PLAN defterini — çünkü bir kapı reddi
   kapanmış işlemde YAŞAMAZ (reddedilen plan hiç işleme dönüşmez). İki paydayı
   aynı tabloda ayrımsız göstermek, "217 ret / 84 işlem" gibi bir oranı okura
   hesaplatırdı ve o oranın anlamı yok. Facet değişince kaynak/pencere/payda
   şeridi de değişiyor ve uçtan ne geliyorsa aynen yazıyor.

   `n` İLE `r_n` AYRI SÜTUN: bir satırın kaç kez GÖRÜLDÜĞÜ ile o satırın kaç
   tanesinin R taşıdığı farklı iki sayı. Tek sütuna indirseydik, R'siz satırların
   ortalamaya girmediği görünmezdi.

   PF `null` İKEN "0" DEĞİL "ölçülemedi" YAZAR ve NEDENİ uçtan gelir: zarar eden
   işlem yoksa PF tanımsızdır (bölme yok) — sonsuz DEĞİL, sıfır DEĞİL. Bu üç
   ayrı cümle ve üçü de aynı hücreye düşebilirdi.
   ============================================================================ */
import { useMemo, useState } from "react";

import {
  type Column,
  type ColumnDef,
  type ColumnFiltersState,
  type PaginationState,
  type SortingState,
  useTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { dataTableFeatures, type DataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";
import { Deger, Kapi, Olculemedi, OlculemediHucre, rKati, sayi, yuzde } from "./ortak";
import type { FacetBloku, FacetKaynagi, FacetSatiri, TopviewsGovdesi } from "./tipler";

/* ---- FACET KAYDI --------------------------------------------------------- */

const AILE_ETIKETI: Record<string, string> = {
  KAYNAK: "Kaynak — işlem nereden geldi",
  SONUC: "Sonuç — işlem nasıl bitti",
  KAPI: "Kapı — plan nerede takıldı",
};

const FACETLER = [
  { aile: "KAYNAK", ad: "kurulum", etiket: "Kurulum" },
  { aile: "KAYNAK", ad: "rejim", etiket: "Rejim" },
  { aile: "KAYNAK", ad: "sektor", etiket: "Sektör" },
  { aile: "SONUC", ad: "cikis_nedeni", etiket: "Çıkış nedeni" },
  { aile: "SONUC", ad: "tutma_kovasi", etiket: "Tutma süresi" },
  { aile: "SONUC", ad: "r_kovasi", etiket: "R aralığı" },
  { aile: "KAPI", ad: "kapi_reddi", etiket: "Kapı reddi" },
  { aile: "KAPI", ad: "kapi_hukmu", etiket: "Kontrolün kararı" },
  { aile: "KAPI", ad: "kaynak", etiket: "Kaynak damgası" },
] as const;

type FacetAdi = (typeof FACETLER)[number]["ad"];

const VARSAYILAN_FACET: FacetAdi = "kurulum";

/* ---- SATIR --------------------------------------------------------------- */

interface TopSatir {
  readonly deger: string;
  readonly n: number;
  readonly r_n: number;
  readonly sum_r: number | null;
  readonly gross_win: number | null;
  readonly gross_loss: number | null;
  readonly pf: number | null;
  readonly kazanma: number | null;
  readonly pf_yok_nedeni: string | null;
}

function sayiYaNull(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

/** Sıralama anahtarı: `null` en dibe. Ölçülemeyen satırı ölçülenlerin arasına
 *  karıştırmak, sıralı listeyi okurken "en kötü" ile "bilinmiyor"u aynı yere koyardı. */
function siraAnahtari(v: number | null): number {
  return v === null ? Number.NEGATIVE_INFINITY : v;
}

/** Ham facet satırlarını tabloya çevirir; `deger`/`n` taşımayanları SAYARAK atar. */
function satirlariCoz(ham: readonly FacetSatiri[]): { satirlar: TopSatir[]; atlanan: number } {
  const satirlar: TopSatir[] = [];
  let atlanan = 0;
  ham.forEach((s) => {
    if (typeof s.deger !== "string" || typeof s.n !== "number") {
      atlanan += 1;
      return;
    }
    satirlar.push({
      deger: s.deger,
      n: s.n,
      r_n: typeof s.r_n === "number" ? s.r_n : 0,
      sum_r: sayiYaNull(s.sum_r),
      gross_win: sayiYaNull(s.gross_win),
      gross_loss: sayiYaNull(s.gross_loss),
      pf: sayiYaNull(s.pf),
      kazanma: sayiYaNull(s.kazanma),
      pf_yok_nedeni: typeof s.pf_yok_nedeni === "string" ? s.pf_yok_nedeni : null,
    });
  });
  return { satirlar, atlanan };
}

/* ---- SÜTUNLAR ------------------------------------------------------------ */

const SAG_SUTUNLAR = new Set(["n", "r_n", "sum_r", "gross_win", "gross_loss", "pf", "kazanma"]);

function SiraliBaslik({
  column,
  etiket,
  saga,
}: {
  column: Column<DataTableFeatures, TopSatir, unknown>;
  etiket: string;
  saga?: boolean;
}) {
  const yon = column.getIsSorted();
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("-mx-2 h-7 font-normal text-muted-foreground", saga && "ml-auto")}
      onClick={() => column.toggleSorting(yon === "asc")}
    >
      {etiket}
      {yon === "asc" ? (
        <ArrowUp data-icon="inline-end" />
      ) : yon === "desc" ? (
        <ArrowDown data-icon="inline-end" />
      ) : (
        <ArrowUpDown data-icon="inline-end" />
      )}
    </Button>
  );
}

/** R taşımayan bir hücrenin neden boş olduğunu satırın KENDİ sayısıyla anlat. */
function rYokNedeni(s: TopSatir, alan: string): string {
  return `bu satırın ${s.n} kaydından ${s.r_n} tanesi r_multiple taşıyor — ${alan} ölçülemedi (0,0 DEĞİL: ölçülmedi).`;
}

const SUTUNLAR: ColumnDef<DataTableFeatures, TopSatir>[] = [
  {
    id: "deger",
    accessorFn: (s) => s.deger,
    filterFn: "includesString",
    header: ({ column }) => <SiraliBaslik column={column} etiket="Değer" />,
    cell: ({ row }) => <span className="font-medium">{row.original.deger}</span>,
  },
  {
    id: "n",
    accessorFn: (s) => s.n,
    header: ({ column }) => <SiraliBaslik column={column} etiket="n" saga />,
    cell: ({ row }) => <span className="tabular-nums">{sayi(row.original.n, 0)}</span>,
  },
  {
    id: "r_n",
    accessorFn: (s) => s.r_n,
    header: ({ column }) => <SiraliBaslik column={column} etiket="R'li n" saga />,
    cell: ({ row }) => <span className="text-muted-foreground tabular-nums">{sayi(row.original.r_n, 0)}</span>,
  },
  {
    id: "sum_r",
    accessorFn: (s) => siraAnahtari(s.sum_r),
    header: ({ column }) => <SiraliBaslik column={column} etiket="Toplam R" saga />,
    cell: ({ row }) => (
      <Deger
        metin={rKati(row.original.sum_r)}
        neden={rYokNedeni(row.original, "toplam R")}
        className="tabular-nums"
      />
    ),
  },
  {
    id: "gross_win",
    accessorFn: (s) => siraAnahtari(s.gross_win),
    header: ({ column }) => <SiraliBaslik column={column} etiket="Brüt kâr" saga />,
    cell: ({ row }) => (
      <Deger
        metin={rKati(row.original.gross_win)}
        neden={rYokNedeni(row.original, "brüt kâr")}
        className="text-[var(--yon-arti)] tabular-nums"
      />
    ),
  },
  {
    id: "gross_loss",
    accessorFn: (s) => siraAnahtari(s.gross_loss),
    header: ({ column }) => <SiraliBaslik column={column} etiket="Brüt zarar" saga />,
    cell: ({ row }) => (
      <Deger
        metin={rKati(row.original.gross_loss)}
        neden={rYokNedeni(row.original, "brüt zarar")}
        className="text-[var(--yon-eksi)] tabular-nums"
      />
    ),
  },
  {
    id: "pf",
    accessorFn: (s) => siraAnahtari(s.pf),
    header: ({ column }) => <SiraliBaslik column={column} etiket="PF" saga />,
    cell: ({ row }) => {
      const s = row.original;
      if (s.pf === null) {
        return (
          <OlculemediHucre
            neden={s.pf_yok_nedeni ?? "uç PF'yi null bastı ama nedenini yazmadı — sıfır ya da sonsuz olarak okuma."}
          />
        );
      }
      return <span className="tabular-nums">{sayi(s.pf, 2)}</span>;
    },
  },
  {
    id: "kazanma",
    accessorFn: (s) => siraAnahtari(s.kazanma),
    header: ({ column }) => <SiraliBaslik column={column} etiket="Kazanma" saga />,
    cell: ({ row }) => (
      <Deger
        metin={yuzde(row.original.kazanma, 1)}
        neden={rYokNedeni(row.original, "kazanma oranı")}
        className="tabular-nums"
      />
    ),
  },
];

/* ---- YÜZEY --------------------------------------------------------------- */

export function TopviewsTablosu({ top }: { top: Durum<TopviewsGovdesi> }) {
  const [facet, setFacet] = useState<FacetAdi>(VARSAYILAN_FACET);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Facet kırılımı</CardTitle>
        <CardDescription>
          Dokuz eksenden biri · her satırda n, toplam R, brüt kâr/zarar, PF ve kazanma. Facetin kendi kaynağı ve
          paydası tablonun altında.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Kapi durum={top} ad="/api/topviews" yukseklik="h-64">
          {(v) => <FacetGovdesi veri={v} facet={facet} setFacet={setFacet} />}
        </Kapi>
      </CardContent>
    </Card>
  );
}

function FacetGovdesi({
  veri,
  facet,
  setFacet,
}: {
  veri: TopviewsGovdesi;
  facet: FacetAdi;
  setFacet: (f: FacetAdi) => void;
}) {
  const secili = FACETLER.find((f) => f.ad === facet) ?? FACETLER[0];
  const blok: FacetBloku | undefined = veri.aileler?.[secili.aile]?.[secili.ad];
  const kaynak = veri.facet_kaynaklari?.[secili.ad];

  const { satirlar, atlanan } = useMemo(() => satirlariCoz(blok?.satirlar ?? []), [blok]);

  const [sorting, setSorting] = useState<SortingState>([{ id: "n", desc: true }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 15 });

  const table = useTable({
    features: dataTableFeatures,
    data: satirlar,
    columns: SUTUNLAR,
    state: { sorting, columnFilters, pagination },
    getRowId: (s) => s.deger,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
  });

  const arama = (table.getColumn("deger")?.getFilterValue() as string | undefined) ?? "";
  const suzulen = table.getFilteredRowModel().rows.length;
  const sayfaSayisi = Math.max(table.getPageCount(), 1);
  const sayfa = Math.min(table.state.pagination.pageIndex + 1, sayfaSayisi);

  // PF'si ölçülemeyen satırların nedenleri: hücrede `title` ile taşınıyor ama tablonun
  // altında da listeleniyor — fareye bağlı bir bilgi, klavyeyle gezen okur için yok demektir.
  const pfNedenleri = useMemo(() => {
    const kume = new Set<string>();
    satirlar.forEach((s) => {
      if (s.pf === null && s.pf_yok_nedeni) kume.add(s.pf_yok_nedeni);
    });
    return [...kume];
  }, [satirlar]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={facet}
          onValueChange={(d) => {
            setFacet(d as FacetAdi);
            setPagination({ pageIndex: 0, pageSize: 15 });
            setColumnFilters([]);
          }}
        >
          <SelectTrigger className="w-56" aria-label="Facet seç">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.keys(AILE_ETIKETI).map((aile) => (
              <SelectGroup key={aile}>
                <SelectLabel>{AILE_ETIKETI[aile]}</SelectLabel>
                {FACETLER.filter((f) => f.aile === aile).map((f) => (
                  <SelectItem key={f.ad} value={f.ad}>
                    {f.etiket}
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>

        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute top-2.5 left-2.5 size-3.5 text-muted-foreground" aria-hidden />
          <Input
            className="h-9 pl-8"
            placeholder={`${secili.etiket} içinde ara…`}
            aria-label={`${secili.etiket} içinde ara`}
            value={arama}
            onChange={(e) => {
              table.getColumn("deger")?.setFilterValue(e.target.value || undefined);
              table.setPageIndex(0);
            }}
          />
        </div>

        <span className="text-muted-foreground text-xs tabular-nums">
          {suzulen} / {satirlar.length} satır
        </span>
      </div>

      {!blok ? (
        <Olculemedi
          neden={`/api/topviews yükünde \`aileler.${secili.aile}.${secili.ad}\` bloğu yok — bu facet hiç üretilmedi.`}
        />
      ) : !blok.satirlar ? (
        <Olculemedi
          neden={
            blok.olculemedi_neden ??
            `${secili.etiket} faceti \`satirlar: null\` döndürdü ama nedenini yazmadı — boş liste DEĞİL, ölçülemedi.`
          }
        />
      ) : satirlar.length === 0 ? (
        <Olculemedi
          neden={`${secili.etiket} faceti boş liste döndürdü: taranan defterde bu eksende tek bir etiketli satır bile yok${atlanan > 0 ? ` (${atlanan} satır \`deger\`/\`n\` taşımadığı için ayrıca atlandı)` : ""}.`}
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <Table className="min-w-[52rem]">
              <TableHeader>
                {table.getHeaderGroups().map((grup) => (
                  <TableRow key={grup.id} className="hover:bg-transparent">
                    {grup.headers.map((baslik) => (
                      <TableHead
                        key={baslik.id}
                        className={cn("h-9", SAG_SUTUNLAR.has(baslik.column.id) && "text-right")}
                      >
                        {baslik.isPlaceholder ? null : <table.FlexRender header={baslik} />}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={table.getVisibleLeafColumns().length} className="h-20 text-center">
                      <span className="text-muted-foreground text-sm">
                        Arama "{arama}" hiçbir satırla eşleşmedi — defterde veri VAR, süzgeç boş döndü.
                      </span>
                    </TableCell>
                  </TableRow>
                ) : (
                  table.getRowModel().rows.map((satir) => (
                    <TableRow key={satir.id} className="border-border/50">
                      {satir.getVisibleCells().map((hucre) => (
                        <TableCell
                          key={hucre.id}
                          className={cn("py-2.5", SAG_SUTUNLAR.has(hucre.column.id) && "text-right")}
                        >
                          <table.FlexRender cell={hucre} />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {sayfaSayisi > 1 ? (
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground text-xs tabular-nums">
                Sayfa {sayfa} / {sayfaSayisi}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!table.getCanPreviousPage()}
                  onClick={() => table.previousPage()}
                >
                  <ChevronLeft data-icon="inline-start" />
                  Önceki
                </Button>
                <Button variant="outline" size="sm" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>
                  Sonraki
                  <ChevronRight data-icon="inline-end" />
                </Button>
              </div>
            </div>
          ) : null}
        </>
      )}

      <FacetBeyani blok={blok} kaynak={kaynak} etiket={secili.etiket} atlanan={atlanan} pfNedenleri={pfNedenleri} />
    </div>
  );
}

function FacetBeyani({
  blok,
  kaynak,
  etiket,
  atlanan,
  pfNedenleri,
}: {
  blok: FacetBloku | undefined;
  kaynak: FacetKaynagi | undefined;
  etiket: string;
  atlanan: number;
  pfNedenleri: readonly string[];
}) {
  const ek = blok?.ek ?? {};
  const ekAnahtarlari = Object.keys(ek);

  return (
    <div className="flex flex-col gap-2 border-border/60 border-t pt-4 text-muted-foreground text-xs leading-relaxed">
      {blok?.cok_etiketli === true ? (
        <p className="text-uyari">
          ÇOK ETİKETLİ FACET: bir kayıt birden çok satıra girebilir, `n` toplamı paydayı AŞAR. Satırları birbirine
          ekleyip yüzde çıkarma.
        </p>
      ) : null}

      {typeof blok?.etiketsiz_n === "number" && blok.etiketsiz_n > 0 ? (
        <p>
          <span className="font-medium text-foreground">Etiketsiz {blok.etiketsiz_n} kayıt:</span>{" "}
          {blok.etiketsiz_neden ?? "uç nedeni yazmadı."} Bu kayıtlar hiçbir satıra girmedi — bir "diğer" kovasına
          itilmediler.
        </p>
      ) : null}

      {atlanan > 0 ? (
        <p>
          Pano ayrıca {atlanan} satırı çizmedi: `deger` ya da `n` alanı gelmemişti; sayı uydurmak yerine atlandılar.
        </p>
      ) : null}

      {ekAnahtarlari.map((k) => (
        <p key={k}>
          {k}: <span className="text-foreground tabular-nums">{sayi(ek[k], 0) ?? "ölçülemedi"}</span>
        </p>
      ))}

      {kaynak && typeof kaynak.kaynak === "string" ? (
        <p>
          Kaynak: {kaynak.kaynak}
          {typeof kaynak.pencere === "string" ? ` · pencere ${kaynak.pencere}` : ""}
          {typeof kaynak.n === "number" ? ` · taranan ${kaynak.n} satır` : ""}
        </p>
      ) : (
        <p>{etiket} faceti için kaynak/pencere beyanı gelmedi — bu tablonun neyi saydığı ölçülemedi.</p>
      )}
      {kaynak && typeof kaynak.payda === "string" ? <p>{kaynak.payda}</p> : null}

      {pfNedenleri.length > 0 ? (
        <div>
          <p className="font-medium text-foreground">PF'nin ölçülemediği satırların nedeni:</p>
          <ul className="mt-1 list-disc pl-5">
            {pfNedenleri.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
