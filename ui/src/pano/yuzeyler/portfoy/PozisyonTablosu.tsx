"use client";

/* ============================================================================
   AÇIK POZİSYON TABLOSU — sıralanabilir, kaynak damgalı, tabular-nums
   ----------------------------------------------------------------------------
   NEDEN `@tanstack/react-table` KULLANILMADI (bilinçli sapma, brief'in tablo
   önerisinden): bu depoda kurulu sürüm **9.1.2** ve v9 API'si v8'den ayrı —
   `useReactTable`/`getCoreRowModel` kök giriş noktasından KALKMIŞ
   (`node_modules/@tanstack/react-table/dist/index.d.ts` yalnız `useTable`,
   `flexRender`, `createTableHook` veriyor; v8 uyumu ayrı bir `/legacy` yolunda).
   Şablonun tablo örnekleri v8 yazımıyla ve olduğu gibi derlenmiyor. Sıralanacak
   satır sayısı bir portföyün açık pozisyon sayısıdır (bugün 7 mertebesinde);
   bunun için `useMemo` + tek durum yeterli ve `noUncheckedIndexedAccess` altında
   tipçe güvenli. Görsel taraf şablonun kendi `ui/table.tsx` ilkelleri.

   ÜÇÜNCÜ HÂL HÜCREDE DE YAŞAR: ölçülemeyen hücre boş bırakılmaz, `<Olculemedi>`
   ile NEDENİNİ taşır. Sıralamada `null` HER ZAMAN sona düşer (yönden bağımsız) —
   yoksa "en küçük tutar" sıralaması ölçülemeyenleri en küçük gibi gösterirdi.
   ============================================================================ */
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import type { PozisyonSatiri } from "./birlestir";
import { adet as adetBicim, kzSinifi, Olculemedi, para, yuzde } from "./olcum";

type SutunAnahtari = "ticker" | "adet" | "giris" | "sonFiyat" | "piyasaDegeri" | "acikKz" | "kzYuzde" | "riskUsd";

interface Sutun {
  readonly anahtar: SutunAnahtari;
  readonly baslik: string;
  readonly sagda: boolean;
  /** Sıralama anahtarı; `null` sıralamada HER ZAMAN sona gider. */
  readonly deger: (s: PozisyonSatiri) => number | string | null;
}

const SUTUNLAR: readonly Sutun[] = [
  { anahtar: "ticker", baslik: "Sembol", sagda: false, deger: (s) => s.ticker },
  { anahtar: "adet", baslik: "Adet", sagda: true, deger: (s) => s.adet },
  { anahtar: "giris", baslik: "Giriş", sagda: true, deger: (s) => s.giris },
  { anahtar: "sonFiyat", baslik: "Son fiyat", sagda: true, deger: (s) => s.sonFiyat },
  { anahtar: "piyasaDegeri", baslik: "Piyasa değeri", sagda: true, deger: (s) => s.piyasaDegeri },
  { anahtar: "acikKz", baslik: "Açık K/Z", sagda: true, deger: (s) => s.acikKz },
  { anahtar: "kzYuzde", baslik: "K/Z %", sagda: true, deger: (s) => s.kzYuzde },
  { anahtar: "riskUsd", baslik: "Risk ($)", sagda: true, deger: (s) => s.riskUsd },
];

const FIYAT_ETIKETI: Record<string, string> = {
  broker: "broker",
  "seans-ici": "seans içi",
  eod: "EOD",
};

const NEREDE_ETIKETI: Record<PozisyonSatiri["nerede"], string> = {
  iki: "iki defterde",
  "yalniz-kitap": "yalnız kitapta",
  "yalniz-broker": "yalnız brokerda",
};

function karsilastir(a: number | string | null, b: number | string | null, yon: 1 | -1): number {
  // NULL YÖNDEN BAĞIMSIZ SONA: ölçülemeyen bir tutar "en küçük tutar" değildir.
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  if (typeof a === "string" || typeof b === "string") return String(a).localeCompare(String(b), "tr") * yon;
  return (a - b) * yon;
}

export function PozisyonTablosu({ satirlar }: { satirlar: readonly PozisyonSatiri[] }) {
  const [sirala, setSirala] = useState<{ anahtar: SutunAnahtari; yon: 1 | -1 }>({ anahtar: "piyasaDegeri", yon: -1 });

  const sirali = useMemo(() => {
    const sutun = SUTUNLAR.find((c) => c.anahtar === sirala.anahtar);
    if (!sutun) return [...satirlar];
    return [...satirlar].sort((a, b) => karsilastir(sutun.deger(a), sutun.deger(b), sirala.yon));
  }, [satirlar, sirala]);

  if (satirlar.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Açık pozisyon yok. Kitap ve broker aynası ikisi de boş döndü — bu ölçülmüş bir olgu, eksik veri değil.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            {SUTUNLAR.map((c) => {
              const etkin = sirala.anahtar === c.anahtar;
              const Ok = !etkin ? ChevronsUpDown : sirala.yon === 1 ? ArrowUp : ArrowDown;
              return (
                <TableHead key={c.anahtar} className={c.sagda ? "text-right" : undefined}>
                  <button
                    type="button"
                    onClick={() =>
                      setSirala((o) => (o.anahtar === c.anahtar ? { anahtar: c.anahtar, yon: o.yon === 1 ? -1 : 1 } : { anahtar: c.anahtar, yon: -1 }))
                    }
                    className={cn(
                      "inline-flex items-center gap-1 rounded-sm hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring",
                      c.sagda && "flex-row-reverse",
                      etkin ? "text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {c.baslik}
                    <Ok className="size-3" />
                  </button>
                </TableHead>
              );
            })}
            <TableHead>Kaynak</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sirali.map((s) => (
            <TableRow key={s.ticker}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  {s.ticker}
                  {s.nerede !== "iki" && (
                    <Badge variant="outline" className="text-[10px]">
                      {NEREDE_ETIKETI[s.nerede]}
                    </Badge>
                  )}
                </div>
                {s.setup && <div className="text-muted-foreground text-xs">{s.setup}</div>}
              </TableCell>

              <TableCell className="text-right tabular-nums">
                {s.adet === null ? (
                  <Olculemedi neden={`${s.ticker}: ne kitap ne broker satırında adet sayıya çevrilebildi`} />
                ) : (
                  <>
                    {adetBicim(s.adet)}
                    {/* `adetFarki` ANCAK iki defter de sayı verdiyse dolar (birlestir.ts);
                        yine de her iki alan AYRI AYRI daraltılıyor — `?? 0` yazmak,
                        ölçülemeyen bir adedi sıfır diye göstermek olurdu. */}
                    {s.adetFarki !== null && s.adetFarki !== 0 && s.kitapAdet !== null && s.brokerAdet !== null && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="ml-1 cursor-help text-amber-600 text-xs dark:text-amber-400">≠</span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-sm">
                          Kitap {adetBicim(s.kitapAdet)} · broker {adetBicim(s.brokerAdet)} — fark{" "}
                          {adetBicim(s.adetFarki)}. Gösterilen adet {s.adetKaynak} defterinden.
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </>
                )}
              </TableCell>

              <TableCell className="text-right tabular-nums">
                {s.giris === null ? (
                  <Olculemedi neden={`${s.ticker}: ne brokerın avg_entry'si ne kitabın entry'si okunabildi — K/Z tabanı yok`} />
                ) : (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="cursor-help">{para(s.giris)}</span>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      {s.girisKaynak === "broker"
                        ? "Brokerın ortalama DOLUM fiyatı — açık K/Z ve K/Z % bu tabandan okunuyor."
                        : "Kitabın plan TETİĞİ. Broker satırı olmadığı için taban bu; açık K/Z ve K/Z % de buradan türetildi."}
                    </TooltipContent>
                  </Tooltip>
                )}
              </TableCell>

              <TableCell className="text-right tabular-nums">
                {s.sonFiyat === null ? (
                  <Olculemedi neden={s.degerNedeni ?? `${s.ticker}: son fiyat hiçbir kaynaktan ölçülemedi`} />
                ) : (
                  <div className="flex flex-col items-end">
                    <span>{para(s.sonFiyat)}</span>
                    <span className="text-[10px] text-muted-foreground">
                      {FIYAT_ETIKETI[s.fiyatKaynak ?? ""] ?? "kaynak yok"}
                      {s.fiyatAni ? ` · ${s.fiyatAni.slice(0, 16)}` : ""}
                    </span>
                  </div>
                )}
              </TableCell>

              <TableCell className="text-right font-medium tabular-nums">
                {s.piyasaDegeri === null ? (
                  <Olculemedi neden={s.degerNedeni ?? `${s.ticker}: piyasa değeri ölçülemedi`} />
                ) : (
                  para(s.piyasaDegeri)
                )}
              </TableCell>

              <TableCell className={cn("text-right tabular-nums", kzSinifi(s.acikKz))}>
                {s.acikKz === null ? (
                  <Olculemedi neden={s.kzNedeni ?? `${s.ticker}: açık K/Z ölçülemedi`} />
                ) : (
                  <div className="flex flex-col items-end">
                    <span>
                      {s.acikKz > 0 ? "+" : ""}
                      {para(s.acikKz)}
                    </span>
                    {s.acikKzKaynak === "turetildi" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="cursor-help text-[10px] text-muted-foreground">türetildi</span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-sm">
                          Broker `unrealized_pl` vermedi; (son fiyat − giriş) × adet ile hesaplandı. Brokerın maliyet
                          bazı kitabınkinden ayrışabilir — mutabakat masasına bak.
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                )}
              </TableCell>

              <TableCell className={cn("text-right tabular-nums", kzSinifi(s.kzYuzde))}>
                {s.kzYuzde === null ? (
                  <Olculemedi neden={`${s.ticker}: giriş ya da son fiyat yok (ya da giriş 0) — yüzde bölünemedi`} />
                ) : (
                  yuzde(s.kzYuzde)
                )}
              </TableCell>

              <TableCell className="text-right tabular-nums text-muted-foreground">
                {s.riskUsd === null ? (
                  <Olculemedi
                    kisa="kitapta yok"
                    neden={`${s.ticker}: risk_dollars yalnız KİTAP pozisyonunda yaşar; bu satır ${NEREDE_ETIKETI[s.nerede]}`}
                  />
                ) : (
                  para(s.riskUsd)
                )}
              </TableCell>

              <TableCell className="text-muted-foreground text-xs">
                {s.nerede === "iki" ? "kitap + broker" : NEREDE_ETIKETI[s.nerede]}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
