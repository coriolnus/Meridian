"use client";

/* ============================================================================
   ERİŞİM TABLOSU — bugün GERÇEKTEN var olan TEK kayıt
   ----------------------------------------------------------------------------
   BU TABLONUN EN ÖNEMLİ ÖZELLİĞİ KAÇ SATIR ÇİZDİĞİ DEĞİL, KAÇ SATIR ÇİZMEDİĞİ.
   Şablonun users tablosu on kullanıcıyla dolu geliyor (users/_components/data.tsx);
   o veriyi taşımak, olmayan bir yeteneği — çok kullanıcılı erişim yönetimini —
   var göstermek olurdu. Meridian'da kullanıcı kaydı YOK: `state/auth.json` tek bir
   `{salt, hash}` çifti tutuyor (meridian/auth.py:150-152) ve `api_login` bir
   PAROLA doğruluyor, bir KİMLİK değil (api.py:1323-1340).

   Bu yüzden tablo TEK satırlıdır ve o satır bir "kullanıcı" değil, OTURUMDUR.
   Satırın adı bile ölçülmüş değil — sistemin ad alanı yok; "oturum sahibi" bu
   arayüzün verdiği etikettir ve hücrenin altında bunu açıkça yazıyor.

   ŞABLONUN GRAMERİ KORUNUYOR (kolonlar · arama · süzgeç · sayfalama · rozetler):
   2. aşamada satır sayısı arttığında değişecek olan yalnız VERİ KAYNAĞIDIR, bu
   dosyanın iskeleti değil. TanStack v9 + ortak `dataTableFeatures` kaydı —
   panonun öbür tablolarıyla aynı özellik sözleşmesi.

   ALAN OLMAYAN KOLONLAR SİLİNMEDİ, "alan yok" olarak duruyor (Katılma tarihi ·
   Son etkinlik). Silmek, eksiği görünmez yapardı; `0` ya da bir tarih uydurmak
   ise bu deponun birinci yasasını çiğnerdi. Boş kolon burada bir SAYAÇTIR.
   ============================================================================ */
import { useMemo, useState } from "react";

import {
  type ColumnDef,
  type ColumnFiltersState,
  type ColumnVisibilityState,
  type PaginationState,
  useTable,
} from "@tanstack/react-table";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import { AlanYok, Olculemedi } from "./parcalar";

/** Tablonun tek satırı. Her alan ya ÖLÇÜLMÜŞ bir uç değeridir ya da `null` + nedeni. */
export interface ErisimSatiri {
  readonly kimlik: string;
  /** Arayüzün verdiği etiket — sistemde ad alanı YOK, bu hücrenin altında yazılı. */
  readonly etiket: string;
  /** `/api/today.autonomy_level` → "L0" | "L1" | "L2" | ham dizge; ölçülemezse null. */
  readonly seviye: string | null;
  readonly seviyeNeden: string;
  /** `mode` + `broker` — seviyeden AYRI eksen, alt satırda. */
  readonly modBroker: string | null;
  readonly modNeden: string;
  /** `/api/session.password_set` */
  readonly parolaKurulu: boolean | null;
  /** `/api/session.authenticated` */
  readonly oturumAcik: boolean | null;
  /** `/api/session.tls` — çerez `Secure` işaretlenecek mi. */
  readonly tls: boolean | null;
}

/** Süzgeç kutusunun okuduğu metin — `oturum` kolonu bu değerlerle eşleşir. */
export function oturumEtiketi(acik: boolean | null): string {
  if (acik === null) return "ölçülemedi";
  return acik ? "açık" : "kapalı";
}

const NOKTA = "size-1.5 rounded-full";

const SUTUNLAR: ColumnDef<DataTableFeatures, ErisimSatiri>[] = [
  {
    id: "arama",
    accessorFn: (s) => `${s.etiket} ${s.seviye ?? ""} ${s.modBroker ?? ""}`,
    filterFn: "includesString",
    enableHiding: true,
  },
  {
    id: "etiket",
    accessorKey: "etiket",
    header: "Erişim kaydı",
    cell: ({ row }) => (
      <div className="grid min-w-0 gap-0.5">
        <span className="font-medium text-foreground text-sm">{row.original.etiket}</span>
        <span
          className="text-muted-foreground text-xs"
          title="meridian/auth.py — kimlik defteri yalnız {salt, hash} tutuyor; ad/e-posta/kullanıcı kimliği alanı yok"
        >
          ad alanı yok — bu etiket panonun kendi etiketi
        </span>
      </div>
    ),
  },
  {
    id: "seviye",
    accessorFn: (s) => s.seviye ?? "ölçülemedi",
    header: "Rol (otonomi seviyesi)",
    filterFn: "equalsString",
    cell: ({ row }) => {
      const s = row.original;
      return (
        <div className="grid min-w-0 gap-1">
          {s.seviye === null ? (
            <Olculemedi neden={s.seviyeNeden} kisa />
          ) : (
            <Badge variant="outline" className="w-fit font-mono">
              {s.seviye}
            </Badge>
          )}
          {s.modBroker === null ? (
            <Olculemedi neden={s.modNeden} kisa />
          ) : (
            <span className="text-muted-foreground text-xs">{s.modBroker}</span>
          )}
        </div>
      );
    },
  },
  {
    id: "dogrulama",
    accessorFn: (s) => (s.parolaKurulu === null ? "ölçülemedi" : s.parolaKurulu ? "kurulu" : "kurulu değil"),
    header: "Kimlik doğrulama",
    cell: ({ row }) => {
      const v = row.original.parolaKurulu;
      if (v === null) {
        return <Olculemedi neden="Parolanın kurulu olup olmadığı bildirilmedi" teknik="`/api/session` gövdesinde `password_set` alanı yok" kisa />;
      }
      return (
        <div className="grid gap-0.5">
          <Badge variant={v ? "outline" : "destructive"} className="w-fit">
            {v ? "parola kurulu" : "parola KURULU DEĞİL"}
          </Badge>
          <span className="text-muted-foreground text-xs">
            {v ? "scrypt (auth.py:138-141) · tek parola, kullanıcı ayrımı yok" : "pano kurulum ekranı gösterir"}
          </span>
        </div>
      );
    },
  },
  {
    id: "oturum",
    accessorFn: (s) => oturumEtiketi(s.oturumAcik),
    header: "Oturum",
    filterFn: "equalsString",
    cell: ({ row }) => {
      const v = row.original.oturumAcik;
      if (v === null) {
        return <Olculemedi neden="Oturumun açık olup olmadığı bildirilmedi" teknik="`/api/session` gövdesinde `authenticated` alanı yok" kisa />;
      }
      return (
        <Badge variant="outline" className="w-fit gap-1.5">
          <span className={cn(NOKTA, v ? "bg-emerald-500" : "bg-red-500")} />
          {v ? "açık" : "kapalı"}
        </Badge>
      );
    },
  },
  {
    id: "tasima",
    accessorFn: (s) => (s.tls === null ? "ölçülemedi" : s.tls ? "TLS" : "TLS yok"),
    header: "Taşıma",
    cell: ({ row }) => {
      const v = row.original.tls;
      if (v === null) {
        return <Olculemedi neden="Bağlantının şifreli olup olmadığı bildirilmedi" teknik="`/api/session` gövdesinde `tls` alanı yok" kisa />;
      }
      return (
        <Badge variant="outline" className="w-fit gap-1.5">
          <span className={cn(NOKTA, v ? "bg-emerald-500" : "bg-amber-500")} />
          {v ? "TLS · çerez Secure" : "TLS yok · çerez Secure değil"}
        </Badge>
      );
    },
  },
  {
    id: "katilma",
    header: "Katılma tarihi",
    enableSorting: false,
    cell: () => (
      <AlanYok
        neden="Kayıt tarihi hiç tutulmuyor"
        teknik="kimlik kaydında tarih alanı yok (auth.py: yalnız salt+hash yazılıyor)"
      />
    ),
  },
  {
    id: "sonEtkinlik",
    header: "Son etkinlik",
    enableSorting: false,
    cell: () => (
      <AlanYok
        neden="Son etkinlik bir kişiye bağlanamıyor"
        teknik="`login_ok` olayı IP ve TTL yazıyor, kimlik yazmıyor (api.py:1348)"
      />
    ),
  },
];

export function OperatorTablosu({ satirlar }: { readonly satirlar: readonly ErisimSatiri[] }) {
  const veri = useMemo(() => [...satirlar], [satirlar]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility] = useState<ColumnVisibilityState>({ arama: false });
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: SUTUNLAR,
    getRowId: (s) => s.kimlik,
    state: { columnFilters, columnVisibility, pagination },
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
  });

  const arama = (tablo.getColumn("arama")?.getFilterValue() as string | undefined) ?? "";
  const oturumSuzgeci = (tablo.getColumn("oturum")?.getFilterValue() as string | undefined) ?? "hepsi";
  const suzulen = tablo.getFilteredRowModel().rows.length;
  const sayfaSayisi = Math.max(tablo.getPageCount(), 1);
  const sayfa = Math.min(tablo.state.pagination.pageIndex + 1, sayfaSayisi);

  // SÜZGEÇ SEÇENEKLERİ VERİDEN TÜRETİLİR, sabit bir listeden değil: "kapalı" diye bir
  // seçenek göstermek, gerçekte hiç kapalı oturum satırı yokken bir küme varmış izlenimi
  // verirdi. Bugün tek satır var, yani liste tek elemanlı — ve bu dürüst olanı.
  const oturumSecenekleri = useMemo(() => {
    const kume = new Set<string>();
    veri.forEach((s) => kume.add(oturumEtiketi(s.oturumAcik)));
    return [...kume];
  }, [veri]);

  return (
    <div className="flex flex-col gap-4">
      {/* FİLTRE ÇUBUĞU — şablonun users tablosundaki gramer (arama + kolon süzgeci). */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-0 flex-1 sm:max-w-64">
          <Search className="-translate-y-1/2 pointer-events-none absolute top-1/2 left-2.5 size-3.5 text-muted-foreground" />
          <Input
            className="h-8 ps-8"
            placeholder="Kayıtlarda ara…"
            aria-label="Erişim kayıtlarında ara"
            value={arama}
            onChange={(e) => {
              tablo.getColumn("arama")?.setFilterValue(e.target.value || undefined);
              tablo.setPageIndex(0);
            }}
          />
        </div>

        <Select
          value={oturumSuzgeci}
          onValueChange={(d) => {
            tablo.getColumn("oturum")?.setFilterValue(d === "hepsi" ? undefined : d);
            tablo.setPageIndex(0);
          }}
        >
          <SelectTrigger size="sm" className="w-44" aria-label="Oturum durumuna göre süz">
            <span className="text-muted-foreground">Oturum:</span>
            <SelectValue />
          </SelectTrigger>
          <SelectContent align="start">
            <SelectItem value="hepsi">hepsi</SelectItem>
            {oturumSecenekleri.map((d) => (
              <SelectItem key={d} value={d}>
                {d}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <span className="ms-auto text-muted-foreground text-xs tabular-nums">
          {suzulen} / {veri.length} kayıt
        </span>
      </div>

      <div className="min-w-0 overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/30">
            {tablo.getHeaderGroups().map((grup) => (
              <TableRow key={grup.id}>
                {grup.headers.map((baslik) => (
                  <TableHead key={baslik.id} className="whitespace-nowrap font-normal">
                    {baslik.isPlaceholder ? null : <tablo.FlexRender header={baslik} />}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {tablo.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={tablo.getVisibleLeafColumns().length} className="h-20 text-center">
                  {/* İKİ AYRI BOŞLUK, İKİ AYRI CÜMLE: süzgeç mi eledi, kayıt mı yok? */}
                  <span className="text-muted-foreground text-sm">
                    {veri.length === 0
                      ? "Hiç erişim kaydı okunamadı — `/api/session` gövdesi bu satırı kuracak alanları taşımıyor."
                      : "Süzgeç var olan tek kaydı da eledi; süzgeci temizleyince geri gelir."}
                  </span>
                </TableCell>
              </TableRow>
            ) : (
              tablo.getRowModel().rows.map((satir) => (
                <TableRow key={satir.id} className="border-border/50">
                  {satir.getVisibleCells().map((hucre) => (
                    <TableCell key={hucre.id} className="py-3 align-top">
                      <tablo.FlexRender cell={hucre} />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* SAYFALAMA — tek satırla da çizilir ve "1 / 1" der. Gizlemek, tablonun
          ARKASINDA sayfalanacak kayıtlar varmış gibi bir belirsizlik bırakırdı. */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-muted-foreground text-xs">
          <span>Sayfa başına</span>
          <Select
            value={`${tablo.state.pagination.pageSize}`}
            onValueChange={(d) => tablo.setPageSize(Number(d))}
          >
            <SelectTrigger size="sm" className="w-20" aria-label="Sayfa başına satır">
              <SelectValue />
            </SelectTrigger>
            <SelectContent side="top">
              {[10, 20, 50].map((n) => (
                <SelectItem key={n} value={`${n}`}>
                  {n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="tabular-nums">
            Sayfa {sayfa} / {sayfaSayisi}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!tablo.getCanPreviousPage()}
            onClick={() => tablo.previousPage()}
          >
            <ChevronLeft data-icon="inline-start" />
            Önceki
          </Button>
          <Button variant="outline" size="sm" disabled={!tablo.getCanNextPage()} onClick={() => tablo.nextPage()}>
            Sonraki
            <ChevronRight data-icon="inline-end" />
          </Button>
        </div>
      </div>
    </div>
  );
}
