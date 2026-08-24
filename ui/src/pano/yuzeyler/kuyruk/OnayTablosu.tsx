"use client";

/* ============================================================================
   ONAY TABLOSU — görev listesi grameri: ne · hangi konu · ne zaman geldi · ne bekliyor
   ----------------------------------------------------------------------------
   ŞABLONUN `tasks` TABLOSUNDAN ALINDI (TanStack v9 `useTable` + `dataTableFeatures`,
   `KapiTablosu.tsx` ile aynı sözleşme). ÜÇ FARK ve üçünün de gerekçesi burada:

   1) SATIR SEÇİM KUTUSU YOK, AMA "İNCELE" EYLEMİ VAR. Şablonun onay kutusu bir
      TOPLU EYLEM içindir; bu kuyrukta toplu eylem YOK ve olmayacak — bir kalem
      geri alınamaz bir icra tetikleyebiliyorken "hepsini onayla" diye bir yol
      açmak, tek tıkla çok emir göndermek olurdu. Satır sonundaki tek eylem
      İNCELE'dir: kalemin TAM kanıtını açar, karar orada verilir (çift adımlı,
      `KararPaneli.tsx`). Satırın kendisi de tıklanabilir kalır — düğme, tıklama
      alanını daraltmak için değil, EYLEMİ GÖRÜNÜR kılmak için var (operatör
      şikâyeti 2026-08-25: "review butonuna basınca bir ekran açılması gerekli").
   2) "GELDİ" SÜTUNU İKİ KATLI: mutlak damga + göreli yaş. Yalnız göreli yazmak
      ("3 gün önce") kuyruğun ne zaman dolduğunu belgelemez; yalnız mutlak yazmak
      bayatlığı gizler. Damga ölçülemeyen satırda sütun BOŞ değil, NEDEN taşır.
   3) DURUM SÜTUNU İKİ DEĞERLİ DEĞİL: "iş istiyor" ile "karar verilmiş, kayıt
      olarak duruyor" AYRI. Sunucunun `inbox_count`u (api.py:5899) ikincisini
      saymıyor; tablo saysaydı, hiç azalmayan bir liste çıkardı.

   SIRALAMA VARSAYILANI "EN ESKİ ÖNCE": bir görev listesinde en yaşlı kalem en
   tehlikelisidir (okunmamış onay = alınmamış karar). Damgası ölçülemeyen satırlar
   listenin SONUNA düşer — "bilinmiyor"u "en taze" saymak yanlış bir güven verirdi.
   ============================================================================ */
import { useMemo, useState } from "react";

import { type ColumnDef, type SortingState, useTable } from "@tanstack/react-table";
import { ArrowUpDown, Eye } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type DataTableFeatures, dataTableFeatures } from "@/lib/data-table-features";
import { cn } from "@/lib/utils";

import { goreliMetin, HukumRozet, Olculemedi, tarihMetni, zamanMetni, zamanMs } from "./parcalar";
import { TUR_ETIKET, type KuyrukOgesi, type KuyrukTuru } from "./onaylar";

/**
 * Damgasız satırın sıralama değeri `-Infinity`: anahtar YAŞ olduğu için azalan sıralamada
 * (en eski üstte) bu satırlar EN SONA düşer. "Bilinmiyor"u en yaşlı sayıp kuyruğun başına
 * koymak, ölçülemeyen bir damgayı bir aciliyet iddiasına çevirmek olurdu.
 */
const DAMGASIZ = Number.NEGATIVE_INFINITY;

const TUR_TONU: Record<KuyrukTuru, "iyi" | "uyari" | "kotu" | "notr" | "olculemedi"> = {
  plan: "uyari",
  silahlanma: "uyari",
  revizyon: "notr",
  oneri: "notr",
  bilinmeyen: "kotu",
};

function kolonlariKur(
  simdi: number,
  sec: (o: KuyrukOgesi) => void,
): ColumnDef<DataTableFeatures, KuyrukOgesi>[] {
  return [
    {
      id: "tur",
      accessorFn: (o) => TUR_ETIKET[o.tur],
      header: "Ne",
      cell: ({ row }) => (
        <HukumRozet
          ton={TUR_TONU[row.original.tur]}
          metin={TUR_ETIKET[row.original.tur]}
          baslik={`gelen kutusu türü: ${row.original.ayrinti.cesit}`}
        />
      ),
    },
    {
      id: "konu",
      accessorFn: (o) => o.konu ?? "",
      header: "Konu",
      cell: ({ row }) => (
        <div className="flex min-w-0 flex-col gap-0.5">
          {row.original.konu === null ? (
            <Olculemedi neden={row.original.konuNeden} kisa />
          ) : (
            <code className="break-all font-mono text-xs">{row.original.konu}</code>
          )}
          <span className="max-w-[26rem] truncate text-muted-foreground text-[11px]" title={row.original.baslik}>
            {row.original.baslik}
          </span>
        </div>
      ),
    },
    {
      id: "geldi",
      // SIRALAMA ANAHTARI YAŞ (ms): damgasız satır `Infinity` alır ve artan sıralamada
      // en sona düşer — "ölçülemedi"yi "en yeni" saymak, kuyruğun başını yalanla doldururdu.
      accessorFn: (o) => {
        const ms = zamanMs(o.gelisIso);
        return ms === null ? DAMGASIZ : simdi - ms;
      },
      header: ({ column }) => (
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 h-8 px-2 text-xs"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Geldi
          <ArrowUpDown className="ml-1 size-3" aria-hidden />
        </Button>
      ),
      cell: ({ row }) => {
        // SAATİ OLMAYAN KAYNAĞA SAAT BASILMAZ: plan satırı yalnız seans TARİHİ taşıyor
        // (`gelisSaatli: false`); "03:00" yazmak, kaynağın hiç ölçmediği bir değeri
        // ekrana koymak olurdu.
        const mutlak = row.original.gelisSaatli
          ? zamanMetni(row.original.gelisIso)
          : tarihMetni(row.original.gelisIso);
        if (mutlak === null) return <Olculemedi neden={row.original.gelisNeden} kisa />;
        const gorece = goreliMetin(zamanMs(row.original.gelisIso), simdi);
        return (
          <div className="flex flex-col gap-0.5">
            <span className="tabular-nums text-xs">{mutlak}</span>
            <span className="text-muted-foreground text-[11px]">
              {row.original.gelisSaatli ? (gorece ?? "yaş hesaplanamadı") : "saat yok — seans tarihi"}
            </span>
          </div>
        );
      },
    },
    {
      id: "durum",
      accessorFn: (o) => (o.isIstiyor ? 0 : 1),
      header: "Durum",
      cell: ({ row }) =>
        row.original.isIstiyor ? (
          <HukumRozet
            ton="uyari"
            metin="iş istiyor"
            baslik="sunucunun `inbox_count` ölçütüne göre hâlâ bekliyor (api.py:5899)"
          />
        ) : (
          <HukumRozet
            ton="notr"
            metin="karar verilmiş"
            baslik={row.original.durgunNeden ?? "kayıt olarak duruyor, iş istemiyor"}
          />
        ),
    },
    {
      id: "bekleyen",
      accessorFn: (o) => o.bekleyen,
      header: "Ne bekliyor",
      cell: ({ row }) => (
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-xs leading-5">{row.original.bekleyen}</span>
          {row.original.eylemler.length > 0 ? (
            <span className="flex flex-wrap gap-1">
              {row.original.eylemler.map((e) => (
                <Badge key={e} variant="secondary" className="font-mono text-[10px]">
                  {e}
                </Badge>
              ))}
            </span>
          ) : (
            <span className="text-muted-foreground text-[11px]">uçta uygulanabilir eylem yok</span>
          )}
        </div>
      ),
    },
    {
      id: "islem",
      header: "",
      enableSorting: false,
      cell: ({ row }) => (
        <Button
          type="button"
          variant="outline"
          size="sm"
          // TIKLAMA YUKARI SIZMASIN: satırın kendisi de `sec` çağırıyor. Durdurmazsak
          // aynı tık iki kez işlenir; bugün zararsız (aynı kalem seçilir) ama yarın
          // satır tıklaması başka bir şey yaparsa sessiz bir çift-eylem olurdu.
          onClick={(e) => {
            e.stopPropagation();
            sec(row.original);
          }}
          aria-label={`${row.original.baslik} — kararı incele`}
        >
          <Eye aria-hidden />
          İncele
        </Button>
      ),
    },
  ];
}

export function OnayTablosu({
  ogeler,
  sec,
  bosMetin,
}: {
  readonly ogeler: readonly KuyrukOgesi[];
  readonly sec: (o: KuyrukOgesi) => void;
  /** Liste boşken yazılacak DÜRÜST cümle — "sıfır bekleyen" ile "ölçülemedi" ayrı. */
  readonly bosMetin: string;
}) {
  const [siralama, setSiralama] = useState<SortingState>([{ id: "geldi", desc: true }]);
  // ŞİMDİ BİR KEZ SABİTLENİR: her hücrede `Date.now()` çağırsaydık aynı tablonun iki
  // satırı iki farklı ANA göre yaş yazardı (ve sıralama anahtarı render sırasında kayardı).
  const simdi = useMemo(() => Date.now(), [ogeler]);
  const kolonlar = useMemo(() => kolonlariKur(simdi, sec), [simdi, sec]);
  const veri = useMemo(() => [...ogeler], [ogeler]);

  const tablo = useTable({
    features: dataTableFeatures,
    data: veri,
    columns: kolonlar,
    getRowId: (o) => o.kimlik,
    state: { sorting: siralama },
    onSortingChange: setSiralama,
  });

  return (
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
                <span className="text-muted-foreground text-sm">{bosMetin}</span>
              </TableCell>
            </TableRow>
          ) : (
            tablo.getRowModel().rows.map((satir) => (
              <TableRow
                key={satir.id}
                /* SATIR FARE İÇİN TIKLANABİLİR, ERİŞİLEBİLİR EYLEM "İNCELE" DÜĞMESİDİR.
                   ÖNCEDEN satırın kendisi `role="button"` + `tabIndex={0}` idi ve o zaman
                   DOĞRUYDU (satırda başka düğme yoktu). Artık satırın içinde GERÇEK bir
                   düğme var; `role="button"` bir kabın içine ikinci bir düğme koymak,
                   erişilebilirlik ağacında iç içe iki etkileşimli düğüm demektir ve ekran
                   okuyucu satırın tamamını tek bir düğme diye okur — düğmenin kendi
                   etiketi kaybolur. Klavye yolu KAYBOLMADI, İYİLEŞTİ: sekme artık satır
                   başına ADLANDIRILMIŞ bir düğmeye ("… — kararı incele") uğruyor. */
                className={cn(
                  "cursor-pointer hover:bg-muted/40",
                  !satir.original.isIstiyor && "opacity-70",
                  satir.original.tur === "bilinmeyen" && "bg-destructive/5",
                )}
                onClick={() => sec(satir.original)}
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
  );
}
