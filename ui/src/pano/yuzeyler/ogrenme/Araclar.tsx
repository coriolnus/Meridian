"use client";

/* ============================================================================
   ARAÇLAR — "ajanın elinde hangi araçlar var, hangisi gerçekten kullanılıyor?"
   ----------------------------------------------------------------------------
   ÜÇ AYRI "KULLANILDI" VAR VE ÜÇÜ DE AYRI SÜTUN:
     · `n` / `avg_r`            — skill'in DETERMİNİSTİK boru hattındaki canlı atfı
     · `n_cf` / `cf_avg_r`      — karşı-olgusal katman (geniş örneklem, AYRI popülasyon)
     · `ajan_yukleme_n` / `ajan_acilma_n` — LLM katmanı: birincisi "biz isteme bastık",
                                  ikincisi "model kendi açtı". Toplamaları YASAK.
   Bunları tek bir "kullanım" sayısına indirgemek, üç farklı olguyu tek rakama katlamak
   olurdu; katalog zaten (skills.py:505) bu ayrımı yazıyor ve pano onu koruyor.

   AJAN SAYAÇLARININ YOKLUĞU SIFIR DEĞİLDİR. Uç bunu açıkça söylüyor: sayaç dosyasında
   bir ad hiç geçmiyorsa "hiç kullanılmadı" ile "CLI o adı hiç kaydetmedi" bu dosyadan
   AYIRT EDİLEMEZ — o yüzden alan `null` gelir ve `ajan_kullanim_neden` dolar. Hücre 0
   yazsaydı, ölçülmemiş bir şeyi ölçülmüş gösterirdik.

   PAYDA GÖRÜNÜR: "kaç skill var?" sorusunun üç ayrı paydası vardı (dizin / SKILL.md /
   kayıt) ve üçü de farklı sayıyordu. `envanter.hukum` o üç paydayı ölçen cümledir ve
   tablonun altında AYNEN duruyor.
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
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Hammer, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { dataTableFeatures, type DataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";
import { anMetni, Beyan, BolumKarti, Deger, Kapi, Olculemedi, OlculemediHucre, rKati, sayi, yuzde } from "./ortak";
import type { KatalogSatiri, SkillGovdesi } from "./tipler";

/* ---- SATIR --------------------------------------------------------------- */

interface AracSatir {
  readonly ad: string;
  readonly aciklama: string;
  readonly kategori: string;
  readonly yasam: string;
  readonly acik: boolean;
  readonly mod: string;
  readonly golge: boolean;
  readonly boru: string | null;
  readonly korumali: boolean;
  readonly gerekli: readonly string[];
  readonly n: number;
  readonly kazanma: number | null;
  readonly avg_r: number | null;
  readonly n_cf: number;
  readonly cf_avg_r: number | null;
  readonly yukleme: number | null;
  readonly acilma: number | null;
  readonly son_yukleme: string | null;
  readonly ajan_neden: string | null;
}

function sayiYaNull(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function satirlariCoz(ham: readonly KatalogSatiri[]): { satirlar: AracSatir[]; adsiz: number } {
  const satirlar: AracSatir[] = [];
  let adsiz = 0;
  ham.forEach((s) => {
    if (typeof s.name !== "string" || s.name.length === 0) {
      adsiz += 1; // ADSIZ SATIR SESSİZCE DÜŞMEZ: kaç tanesinin düştüğü tablonun altında yazar
      return;
    }
    satirlar.push({
      ad: s.name,
      aciklama: typeof s.description === "string" ? s.description : "",
      kategori: typeof s.category === "string" && s.category.length > 0 ? s.category : "kategorisiz",
      yasam: typeof s.yasam_dongusu === "string" ? s.yasam_dongusu : s.retired === true ? "arşiv" : "—",
      acik: s.enabled === true,
      mod: typeof s.mode === "string" ? s.mode : "—",
      golge: s.shadow === true,
      boru: typeof s.pipeline === "string" ? s.pipeline : null,
      korumali: s.protected === true,
      gerekli: s.requires ?? [],
      n: typeof s.n === "number" ? s.n : 0,
      kazanma: sayiYaNull(s.win_rate),
      avg_r: sayiYaNull(s.avg_r),
      n_cf: typeof s.n_cf === "number" ? s.n_cf : 0,
      cf_avg_r: sayiYaNull(s.cf_avg_r),
      yukleme: sayiYaNull(s.ajan_yukleme_n),
      acilma: sayiYaNull(s.ajan_acilma_n),
      son_yukleme: typeof s.son_yukleme === "string" ? s.son_yukleme : null,
      ajan_neden: typeof s.ajan_kullanim_neden === "string" ? s.ajan_kullanim_neden : null,
    });
  });
  return { satirlar, adsiz };
}

/** Sıralamada `null` en dibe: "ölçülemedi" ile "en kötü" aynı yere düşmesin. */
function siraAnahtari(v: number | null): number {
  return v === null ? Number.NEGATIVE_INFINITY : v;
}

/* ---- SÜTUNLAR ------------------------------------------------------------ */

const SAG_SUTUNLAR = new Set(["n", "avg_r", "n_cf", "cf_avg_r", "ajan"]);

function SiraliBaslik({
  column,
  etiket,
  saga,
}: {
  column: Column<DataTableFeatures, AracSatir, unknown>;
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

const SUTUNLAR: ColumnDef<DataTableFeatures, AracSatir>[] = [
  {
    id: "ad",
    accessorFn: (s) => s.ad,
    filterFn: "includesString",
    header: ({ column }) => <SiraliBaslik column={column} etiket="Araç" />,
    cell: ({ row }) => {
      const s = row.original;
      return (
        <div className="flex min-w-0 flex-col gap-0.5">
          <span className="font-medium" title={s.aciklama || undefined}>
            {s.ad}
          </span>
          {s.aciklama ? (
            <span className="line-clamp-1 max-w-[22rem] text-muted-foreground text-xs">{s.aciklama}</span>
          ) : (
            <span className="text-muted-foreground text-xs italic">SKILL.md özeti okunamadı</span>
          )}
        </div>
      );
    },
  },
  {
    id: "kategori",
    accessorFn: (s) => s.kategori,
    filterFn: "equalsString",
    header: ({ column }) => <SiraliBaslik column={column} etiket="Kategori" />,
    cell: ({ row }) => <span className="text-muted-foreground text-xs">{row.original.kategori}</span>,
  },
  {
    id: "durum",
    accessorFn: (s) => `${s.acik ? "1" : "0"}${s.yasam}`,
    header: ({ column }) => <SiraliBaslik column={column} etiket="Durum" />,
    cell: ({ row }) => {
      const s = row.original;
      return (
        <div className="flex flex-wrap items-center gap-1">
          <Badge
            variant="outline"
            className={
              s.acik
                ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
                : "text-muted-foreground"
            }
          >
            {s.acik ? "açık" : "kapalı"}
          </Badge>
          {s.yasam !== "—" ? <Badge variant="outline">{s.yasam}</Badge> : null}
          {s.golge ? (
            <Badge
              variant="outline"
              className="cursor-help border-amber-500/40 text-amber-700 dark:text-amber-300"
              title="Deneme: skill koşar ama kararı icraya BAĞLANMAZ (beyan tablonun altında)."
            >
              deneme
            </Badge>
          ) : null}
          {s.korumali ? <Badge variant="outline">korumalı</Badge> : null}
          {s.boru ? <Badge variant="outline">{s.boru}</Badge> : null}
          {s.gerekli.map((g) => (
            <Badge key={g} variant="outline" className="text-muted-foreground">
              {g} gerek
            </Badge>
          ))}
        </div>
      );
    },
  },
  {
    id: "n",
    accessorFn: (s) => s.n,
    header: ({ column }) => <SiraliBaslik column={column} etiket="Gerçek n" saga />,
    cell: ({ row }) => (
      <div className="flex flex-col items-end">
        <span className="tabular-nums">{sayi(row.original.n, 0)}</span>
        <span className="text-muted-foreground text-xs tabular-nums">
          {row.original.kazanma === null ? "kazanma ölçülemedi" : (yuzde(row.original.kazanma, 0) ?? "")}
        </span>
      </div>
    ),
  },
  {
    id: "avg_r",
    accessorFn: (s) => siraAnahtari(s.avg_r),
    header: ({ column }) => <SiraliBaslik column={column} etiket="Gerçek R" saga />,
    cell: ({ row }) => (
      <Deger
        metin={rKati(row.original.avg_r, 2)}
        neden="Bu aracın ortalama getirisi hesaplanamadı"
        teknik={`gerçek katmanda ${row.original.n} işlem var ama \`avg_r\` yok — 0,0 DEĞİL`}
        className="tabular-nums"
      />
    ),
  },
  {
    id: "n_cf",
    accessorFn: (s) => s.n_cf,
    header: ({ column }) => <SiraliBaslik column={column} etiket="cf n" saga />,
    cell: ({ row }) => <span className="text-muted-foreground tabular-nums">{sayi(row.original.n_cf, 0)}</span>,
  },
  {
    id: "cf_avg_r",
    accessorFn: (s) => siraAnahtari(s.cf_avg_r),
    header: ({ column }) => <SiraliBaslik column={column} etiket="cf R" saga />,
    cell: ({ row }) => (
      <Deger
        metin={rKati(row.original.cf_avg_r, 2)}
        neden="Denenmeyen girişlerin ortalama getirisi hesaplanamadı"
        teknik={`karşı-olgusal katmanda ${row.original.n_cf} satır var ama \`cf_avg_r\` yok`}
        className="text-muted-foreground tabular-nums"
      />
    ),
  },
  {
    id: "ajan",
    accessorFn: (s) => siraAnahtari(s.acilma),
    header: ({ column }) => <SiraliBaslik column={column} etiket="Ajan katmanı" saga />,
    cell: ({ row }) => {
      const s = row.original;
      if (s.yukleme === null && s.acilma === null) {
        return (
          <OlculemediHucre
            neden={s.ajan_neden ?? "Bu aracı yapay zekânın kaç kez kullandığı kaydedilmemiş"}
            teknik="`ajan_yukleme_n` / `ajan_acilma_n` yok — sayaç dosyasında bu ad hiç geçmiyor; 0 yazmak ölçülmemiş bir şeyi ölçülmüş göstermek olurdu"
          />
        );
      }
      return (
        <div className="flex flex-col items-end">
          <span className="tabular-nums" title="Biz isteme bastık (-s ile yükleme)">
            ↑ {s.yukleme === null ? "—" : sayi(s.yukleme, 0)}
          </span>
          <span className="text-muted-foreground text-xs tabular-nums" title="Model kendi açtı (skill_view)">
            ↗ {s.acilma === null ? "—" : sayi(s.acilma, 0)}
            {s.son_yukleme ? ` · ${anMetni(s.son_yukleme) ?? ""}` : ""}
          </span>
        </div>
      );
    },
  },
];

/* ---- BÖLÜM --------------------------------------------------------------- */

export function Araclar({ skills }: { skills: Durum<SkillGovdesi> }) {
  return (
    <BolumKarti kimlik="skiller" baslik="Araçlar" soru="Ajanın elinde hangi araçlar var?" ikon={Hammer}>
      <Kapi durum={skills} ad="/api/skills" yukseklik="h-72">
        {(v) => <Govde veri={v} />}
      </Kapi>
    </BolumKarti>
  );
}

function Govde({ veri }: { veri: SkillGovdesi }) {
  const { satirlar, adsiz } = useMemo(() => satirlariCoz(veri.catalog ?? []), [veri.catalog]);
  const kategoriler = useMemo(
    () => [...new Set(satirlar.map((s) => s.kategori))].sort((a, b) => a.localeCompare(b, "tr")),
    [satirlar],
  );

  const [sorting, setSorting] = useState<SortingState>([{ id: "n", desc: true }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 12 });

  const table = useTable({
    features: dataTableFeatures,
    data: satirlar,
    columns: SUTUNLAR,
    state: { sorting, columnFilters, pagination },
    getRowId: (s) => s.ad,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
  });

  const arama = (table.getColumn("ad")?.getFilterValue() as string | undefined) ?? "";
  const kategoriSuzgeci = (table.getColumn("kategori")?.getFilterValue() as string | undefined) ?? "__hepsi";
  const suzulen = table.getFilteredRowModel().rows.length;
  const sayfaSayisi = Math.max(table.getPageCount(), 1);
  const sayfa = Math.min(table.state.pagination.pageIndex + 1, sayfaSayisi);

  const c = veri.counts;
  const env = veri.envanter;

  return (
    <div className="flex flex-col gap-5">
      {/* ---- SAYAÇLAR ---- */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { baslik: "Kayıtlı araç", deger: c?.total, alt: "reconcile SONRASI canlı sayım" },
          { baslik: "Açık", deger: c?.enabled, alt: "anahtar durumuna göre uzlaştırıldı" },
          { baslik: "Kapalı", deger: c?.disabled, alt: "stile uymayan / birleştirilen / anahtarsız" },
          { baslik: "Boru hattında etkin", deger: c?.active_in_pipelines, alt: "hem açık hem bir hatta bağlı" },
        ].map((k) => (
          <div key={k.baslik} className="rounded-lg border border-border/60 bg-card p-4">
            <p className="text-muted-foreground text-xs">{k.baslik}</p>
            <p className="mt-1.5 text-2xl leading-none tabular-nums">
              <Deger
                metin={sayi(k.deger, 0)}
                neden="Araç sayımı bildirilmedi"
                teknik="/api/skills `counts` bloğu bu alanı basmadı"
              />
            </p>
            <p className="mt-2 text-muted-foreground text-xs leading-snug">{k.alt}</p>
          </div>
        ))}
      </div>

      {/* ---- SÜZGEÇLER ---- */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={kategoriSuzgeci}
          onValueChange={(d) => {
            table.getColumn("kategori")?.setFilterValue(d === "__hepsi" ? undefined : d);
            table.setPageIndex(0);
          }}
        >
          <SelectTrigger className="w-60" aria-label="Kategori süz">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__hepsi">Tüm kategoriler</SelectItem>
            {kategoriler.map((k) => (
              <SelectItem key={k} value={k}>
                {k}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute top-2.5 left-2.5 size-3.5 text-muted-foreground" aria-hidden />
          <Input
            className="h-9 pl-8"
            placeholder="Araç adında ara…"
            aria-label="Araç adında ara"
            value={arama}
            onChange={(e) => {
              table.getColumn("ad")?.setFilterValue(e.target.value || undefined);
              table.setPageIndex(0);
            }}
          />
        </div>

        <span className="text-muted-foreground text-xs tabular-nums">
          {suzulen} / {satirlar.length} araç
        </span>
      </div>

      {/* ---- TABLO ---- */}
      {satirlar.length === 0 ? (
        <Olculemedi
          neden={`Hiç araç listelenmedi${adsiz > 0 ? ` (${adsiz} satır adsız olduğu için ayrıca atlandı)` : ""} — araç kaydı okunamamış olabilir`}
          teknik={`/api/skills \`catalog\` boş liste döndürdü${adsiz > 0 ? `; ${adsiz} satır \`name\` taşımıyordu` : ""}`}
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <Table className="min-w-[62rem]">
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
                        Süzgeç hiçbir araçla eşleşmedi — kayıt defterinde araç VAR, süzgeç boş döndü.
                      </span>
                    </TableCell>
                  </TableRow>
                ) : (
                  table.getRowModel().rows.map((satir) => (
                    <TableRow key={satir.id} className="border-border/50">
                      {satir.getVisibleCells().map((hucre) => (
                        <TableCell
                          key={hucre.id}
                          className={cn("py-2.5 align-top", SAG_SUTUNLAR.has(hucre.column.id) && "text-right")}
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

      {/* ---- PAYDA BEYANI ---- */}
      <div className="flex flex-col gap-2">
        {adsiz > 0 ? (
          <Beyan>
            {adsiz} katalog satırı `name` taşımadığı için tabloya girmedi — sessizce düşmediler, burada
            sayılıyorlar.
          </Beyan>
        ) : null}
        {env?.hukum ? <Beyan>{env.hukum}</Beyan> : <Beyan>Envanter kararı yükte yok — "kaç araç var?" sorusunun paydası bu turda ölçülemedi.</Beyan>}
        {env?.kayit ? (
          <Beyan>
            Kayıt: toplam {sayi(env.kayit.toplam, 0) ?? "?"} · aktif {sayi(env.kayit.aktif, 0) ?? "?"} · arşiv{" "}
            {sayi(env.kayit.arsiv, 0) ?? "?"}
          </Beyan>
        ) : null}
        {veri.golge_beyani ? <Beyan>{veri.golge_beyani}</Beyan> : null}
      </div>
    </div>
  );
}
