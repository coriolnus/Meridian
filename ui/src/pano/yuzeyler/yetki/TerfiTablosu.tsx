"use client";

/* ============================================================================
   TERFİ TABLOSU — L0'dan L1'e geçmek için sağlanması gereken ölçütler
   ----------------------------------------------------------------------------
   BU EKRANDAKİ TEK CANLI ÖLÇÜM BURADA: `/api/summary.ladder` bu listeyi her
   çağrıda GERÇEK durumdan hesaplıyor (analytics.py::autonomy_ladder) — kapanmış
   işlem sayısı, kaç rejimde pozitif skor, gözlenen maksimum düşüş, kalibre olmuş
   hipotez sayısı, devre kesici sicili. Yani "ajan paraya ne kadar yakın" sorusunun
   cevabı bir belgeden değil, defterden okunuyor.

   ELLE ADIMLAR PAYDANIN DIŞINDA ve bu uçta zaten öyle işaretli (`manual`). Onları
   otomatik sayaca katmak, operatörün/altyapının yapacağı bir işi ajanın başarısı
   gibi göstermek olurdu; ayırmak ise "%80 hazır" cümlesinin neyi ölçtüğünü
   dürüstleştirir. Sayaç `auto_progress` — uçtan gelir, burada yeniden hesaplanmaz.

   KADRAN: iki sayı da (`met`, `total`) gelmezse kadran ÇİZİLMEZ. Boş bir kadran
   "%0 hazır" diye okunur ve bu, ölçülmemiş bir şeyi ölçülmüş göstermektir.
   ============================================================================ */
import { useMemo, useState } from "react";

import { CircleCheck, CircleSlash } from "lucide-react";
import { PolarAngleAxis, RadialBar, RadialBarChart } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer } from "@/components/ui/chart";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { Olculemedi } from "./parcalar";
import type { Merdiven, MerdivenOlcutu } from "./tipler";

const KADRAN_CONFIG: ChartConfig = { deger: { label: "sağlanan ölçüt" } };

/** Otomatik ölçüt ilerlemesinin kadranı. `analytics.py::autonomy_ladder` paydayı ELLE
 *  adımlar hariç kuruyor; burada da aynısı gösterilir, yeniden hesaplanmaz. */
function IlerlemeKadrani({ met, total }: { readonly met?: number; readonly total?: number }) {
  if (met === undefined || total === undefined || !Number.isFinite(met) || !Number.isFinite(total) || total <= 0) {
    return (
      <div className="flex min-h-40 flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-4 text-center">
        <span className="font-medium text-sm">Otomatik ölçüt ilerlemesi</span>
        <Olculemedi
          neden="İlerleme kadranı için gereken sayılar gelmedi"
          teknik="`/api/summary.ladder.auto_progress` içinde `met`/`total` gelmedi (ya da payda 0)"
        />
      </div>
    );
  }
  const oran = Math.max(0, Math.min(100, (met / total) * 100));
  // RENK ROL JETONUNDAN (çıplak hex yok): tamamlanmadan yeşile boyamak, terfiye
  // hazır olmayan bir sistemi hazır göstermek olurdu.
  const renk = met >= total ? "var(--chart-2)" : "var(--chart-1)";
  return (
    <div className="flex flex-col items-center rounded-lg border p-2">
      <span className="pt-1 font-medium text-muted-foreground text-xs">Otomatik ölçüt ilerlemesi</span>
      <ChartContainer config={KADRAN_CONFIG} className="aspect-square h-36 w-full">
        <RadialBarChart
          data={[{ ad: "otomatik", deger: oran, fill: renk }]}
          startAngle={220}
          endAngle={-40}
          innerRadius="72%"
          outerRadius="100%"
        >
          {/* Ölçek 0-100'e SABİT: recharts varsayılanı tek değere göre ölçekler ve
              5 ölçütün 1'i sağlanmışken kadran tam dolu görünürdü. */}
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar isAnimationActive={false} dataKey="deger" background cornerRadius={6} angleAxisId={0} />
        </RadialBarChart>
      </ChartContainer>
      <span className="-mt-8 font-semibold text-2xl tabular-nums">
        {met} / {total}
      </span>
      <span className="px-2 pt-1 pb-1 text-center text-[11px] text-muted-foreground">
        elle adımlar paydanın dışında
      </span>
    </div>
  );
}

type TurSuzgeci = "hepsi" | "otomatik" | "elle";

export function TerfiTablosu({ merdiven }: { readonly merdiven: Merdiven | undefined }) {
  const [tur, setTur] = useState<TurSuzgeci>("hepsi");

  const olcutler: readonly MerdivenOlcutu[] | undefined = merdiven?.l0_to_l1;

  const gosterilen = useMemo(() => {
    if (!olcutler) return [];
    if (tur === "hepsi") return [...olcutler];
    const elleMi = tur === "elle";
    return olcutler.filter((o) => (o.manual === true) === elleMi);
  }, [olcutler, tur]);

  if (olcutler === undefined) {
    return <Olculemedi
        neden="Terfi ölçütlerinin listesi bildirilmedi"
        teknik="`/api/summary.ladder` gövdesinde `l0_to_l1` dizisi yok"
      />;
  }

  const elleN = olcutler.filter((o) => o.manual === true).length;

  return (
    <div className="grid gap-4 lg:grid-cols-[15rem_1fr]">
      <IlerlemeKadrani met={merdiven?.auto_progress?.met} total={merdiven?.auto_progress?.total} />

      <div className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Select value={tur} onValueChange={(d) => setTur(d as TurSuzgeci)}>
            <SelectTrigger size="sm" className="w-52" aria-label="Ölçüt türüne göre süz">
              <span className="text-muted-foreground">Tür:</span>
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="start">
              <SelectItem value="hepsi">hepsi</SelectItem>
              <SelectItem value="otomatik">otomatik (defterden ölçülür)</SelectItem>
              <SelectItem value="elle">elle (operatör/altyapı)</SelectItem>
            </SelectContent>
          </Select>
          <span className="ms-auto text-muted-foreground text-xs tabular-nums">
            {gosterilen.length} / {olcutler.length} ölçüt · {elleN} tanesi elle
          </span>
        </div>

        <div className="min-w-0 overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow>
                <TableHead className="min-w-64 font-normal">Ölçüt</TableHead>
                <TableHead className="min-w-32 font-normal">Durum</TableHead>
                <TableHead className="min-w-64 font-normal">Ölçüm</TableHead>
                <TableHead className="min-w-28 font-normal">Tür</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {gosterilen.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-16 text-center">
                    <span className="text-muted-foreground text-sm">
                      Süzgeç "{tur}" hiçbir ölçütle eşleşmedi — merdivende {olcutler.length} ölçüt VAR.
                    </span>
                  </TableCell>
                </TableRow>
              ) : (
                gosterilen.map((o, i) => {
                  const saglandi = o.met;
                  return (
                    <TableRow key={o.label ?? `olcut-${i}`} className="border-border/50">
                      <TableCell className="py-3 align-top text-sm leading-5">
                        {o.label ?? <Olculemedi neden="Ölçütün adı bildirilmedi" teknik="ölçütün `label` alanı gelmedi" kisa />}
                      </TableCell>
                      <TableCell className="py-3 align-top">
                        {saglandi === undefined ? (
                          <Olculemedi
                            neden="Bu ölçütün sağlanıp sağlanmadığı bildirilmedi — sağlandı sayılmaz"
                            teknik="ölçütün `met` alanı gelmedi"
                            kisa
                          />
                        ) : (
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 text-xs",
                              saglandi
                                ? "text-emerald-600 dark:text-emerald-400"
                                : "text-muted-foreground",
                            )}
                          >
                            {saglandi ? (
                              <CircleCheck className="size-3.5 shrink-0" aria-hidden />
                            ) : (
                              <CircleSlash className="size-3.5 shrink-0" aria-hidden />
                            )}
                            {saglandi ? "sağlandı" : "sağlanmadı"}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="py-3 align-top">
                        {o.detail === undefined ? (
                          <Olculemedi neden="Ölçümün ayrıntısı bildirilmedi" teknik="ölçütün `detail` alanı gelmedi" kisa />
                        ) : (
                          <span className="text-muted-foreground text-xs leading-4">{o.detail}</span>
                        )}
                      </TableCell>
                      <TableCell className="py-3 align-top">
                        <Badge variant="outline" className="text-[10px]">
                          {o.manual === true ? "elle" : "otomatik"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        <p className="text-muted-foreground text-xs leading-5">
          Bu tablo CANLI: `/api/summary.ladder.l0_to_l1` her çağrıda defterden hesaplanıyor
          (analytics.py::autonomy_ladder). "Elle" işaretli {elleN} adım operatör/altyapı işidir ve
          otomatik sayacın DIŞINDADIR — onları saymak, ajanın yapmadığı bir işi başarı hanesine
          yazmak olurdu.
        </p>
      </div>
    </div>
  );
}
