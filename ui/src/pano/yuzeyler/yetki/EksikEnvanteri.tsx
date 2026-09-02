"use client";

/* ============================================================================
   EKSİK ENVANTERİ — "çok kullanıcılı" derken NE eksik, tek tek
   ----------------------------------------------------------------------------
   "2. aşamada gelecek" tek başına bir cümle değil bir ERTELEME. Eksik bir
   yeteneği erteleyebilmek için önce SAYABİLMEK gerekir; bu tablo o sayımdır ve
   her satır kendi KANITINI taşır (hangi dosya, hangi satır, hangi ölçüm).

   KAYNAK BİR UÇ DEĞİL, KAYNAK TARAMASIDIR — ve bu tablonun altında açıkça
   yazıyor. Uçtan gelseydi kendini tazelerdi; gelmiyor, dolayısıyla kod
   değiştiğinde bu liste ELLE güncellenir. Ölçümün tarihini ve yöntemini
   yazmadan bir sayıyı ekrana koymak, bu depoda yasak olan "kaynağı belirsiz
   rakam" hamlesinin ta kendisi olurdu.

   ÖLÇÜM (2026-08-25):
     · `meridian/auth.py` — dosyada "user/kullanıcı" geçen SIFIR satır; kimlik
       defterine yalnız `salt` + `hash` yazılıyor (auth.py::set_password).
     · `meridian/api.py` — 81 rota tanımlı; adında `user|invite|member|role|team`
       geçen rota SIFIR (rota listesi taraması).
   ============================================================================ */
import { useMemo, useState } from "react";

import { type ColumnDef, type ColumnFiltersState, useTable } from "@tanstack/react-table";
import { Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";

export interface EksikSatiri {
  readonly kimlik: string;
  /** 2. aşamada gelmesi gereken yetenek. */
  readonly eksik: string;
  /** Onun YERİNE bugün ne var — "hiçbir şey" de geçerli bir cevap, ama yazılmış olmalı. */
  readonly bugun: string;
  /** Bu satırı KİM ölçtü: dosya + satır ya da tarama biçimi. */
  readonly kanit: string;
}

/** Kaynak taramasıyla ölçülen eksikler. Sıra ÖNEM sırası değil, bağımlılık sırasıdır:
 *  kullanıcı tablosu olmadan davet ucu, davet ucu olmadan rol ataması yazılamaz. */
export const EKSIKLER: readonly EksikSatiri[] = [
  {
    kimlik: "kullanici-tablosu",
    eksik: "Kullanıcı tablosu",
    bugun: "Tek parola kaydı: `state/auth.json` → {salt, hash}. Ad, e-posta, kullanıcı kimliği alanı yok.",
    kanit: "auth.py::set_password · auth.py::password_set",
  },
  {
    kimlik: "davet-ucu",
    eksik: "Davet / kayıt ucu",
    bugun: "`POST /api/setup-password` yalnız İLK parolayı kurar; kurulduktan sonra 409 döner.",
    kanit: "api.py::api_setup_password · rota taraması: 81 rotanın hiçbirinde user/invite/member yok",
  },
  {
    kimlik: "rol-atamasi",
    eksik: "Rol ataması (kullanıcı → rol)",
    bugun: "Rol kavramı yok. Tek yetki ekseni `autonomy_level` ve o KİŞİYE değil SİSTEME ait.",
    kanit: "state/goal.yaml `limits.autonomy_level` · analytics.py::autonomy_ladder",
  },
  {
    kimlik: "kisi-denetim",
    eksik: "Kişi bazlı denetim izi",
    bugun: "`login_ok` olayı IP ve oturum ömrünü yazıyor; kimliği yazmıyor (yazacak kimlik yok).",
    kanit: "api.py::api_login — `obs.log(\"login_ok\", ip=…, ttl_s=…)`",
  },
  {
    kimlik: "oturum-defteri",
    eksik: "Açık oturum listesi / tek tek iptal",
    bugun: "Oturum DURUMSUZ: imzalı çerez. Sunucuda oturum defteri yok, tek oturum geri alınamaz.",
    kanit: "auth.py::_parse_session · auth.py::verify_session (yalnız imza + `exp`)",
  },
  {
    kimlik: "parola-sifirlama",
    eksik: "Panodan parola sıfırlama",
    bugun: "Yok ve bilinçli: sıfırlama kabuktan (`python -m meridian.auth_cli set`) — sunucuya erişim ister.",
    kanit: "api.py::api_setup_password şerhi (arka kapı DEĞİL)",
  },
];

const SUTUNLAR: ColumnDef<DataTableFeatures, EksikSatiri>[] = [
  {
    id: "arama",
    accessorFn: (s) => `${s.eksik} ${s.bugun} ${s.kanit}`,
    filterFn: "includesString",
    enableHiding: true,
  },
  {
    id: "eksik",
    accessorKey: "eksik",
    header: "2. aşamada gelecek",
    cell: ({ row }) => (
      <div className="flex items-start gap-2">
        <Badge variant="outline" className="mt-0.5 shrink-0 text-[10px]">
          eksik
        </Badge>
        <span className="font-medium text-sm leading-5">{row.original.eksik}</span>
      </div>
    ),
  },
  {
    id: "bugun",
    accessorKey: "bugun",
    header: "Bugün onun yerine ne var",
    cell: ({ row }) => <span className="text-sm leading-5">{row.original.bugun}</span>,
  },
  {
    id: "kanit",
    accessorKey: "kanit",
    header: "Ölçüm",
    cell: ({ row }) => (
      <code className="break-all font-mono text-[11px] text-muted-foreground leading-4">{row.original.kanit}</code>
    ),
  },
];

export function EksikEnvanteri() {
  const veri = useMemo(() => [...EKSIKLER], []);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: SUTUNLAR,
    getRowId: (s) => s.kimlik,
    state: { columnFilters, columnVisibility: { arama: false } },
    onColumnFiltersChange: setColumnFilters,
  });

  const arama = (tablo.getColumn("arama")?.getFilterValue() as string | undefined) ?? "";
  const suzulen = tablo.getFilteredRowModel().rows.length;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-0 flex-1 sm:max-w-64">
          <Search className="-translate-y-1/2 pointer-events-none absolute top-1/2 left-2.5 size-3.5 text-muted-foreground" />
          <Input
            className="h-8 ps-8"
            placeholder="Eksiklerde ara…"
            aria-label="Eksik envanterinde ara"
            value={arama}
            onChange={(e) => tablo.getColumn("arama")?.setFilterValue(e.target.value || undefined)}
          />
        </div>
        <span className="ms-auto text-muted-foreground text-xs tabular-nums">
          {suzulen} / {veri.length} eksik
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
                <TableCell colSpan={tablo.getVisibleLeafColumns().length} className="h-16 text-center">
                  <span className="text-muted-foreground text-sm">
                    Arama "{arama}" hiçbir satırla eşleşmedi — envanterde {veri.length} kalem VAR, süzgeç boş döndü.
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

      <p className="text-muted-foreground text-xs leading-5">
        KAYNAK: bu tablo bir UÇTAN GELMİYOR — 2026-08-25'te kaynak taramasıyla ölçüldü
        (`meridian/auth.py` + `meridian/api.py` rota listesi). Kendini tazelemez; kod değişirse elle
        güncellenmesi gerekir. Sayı ({veri.length} kalem) taramanın sonucudur, bir tahmin değil.
      </p>
    </div>
  );
}
