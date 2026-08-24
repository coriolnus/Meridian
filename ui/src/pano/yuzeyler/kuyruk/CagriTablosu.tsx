"use client";

/* ============================================================================
   AJAN ÇAĞRILARI — gecenin üçüncü ekseni (`agent_call` / `agent_call_empty`)
   ----------------------------------------------------------------------------
   ÜÇ EKSEN, ÜÇ AYRI SORU: adım damgaları "dişli döndü mü", koşu defteri "hat ne
   kadar sürdü", çağrı defteri "beyin gerçekten cevap verdi mi". Üçüncüsü olmadan
   koşan ama BOŞ dönen bir gece "başarılı" görünür — `empty` sütunu tam olarak bunu
   ölçüyor (`agent_call_empty` olayı ayrı bir olay adıdır, api.py:4041).

   PENCERE SINIRLI VE BU SÖYLENİYOR: uç son 30 çağrıyı, o da `obs.recent(3000)`
   olay penceresinden süzerek veriyor. Boş liste "çağrı yapılmadı" DEĞİLDİR, "bu
   pencerede görülmedi"dir — ayrımı kart altındaki cümle taşıyor.
   ============================================================================ */
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { Deger, HukumRozet, Olculemedi, zamanMetni } from "./parcalar";
import type { CizelgeCagrisi } from "./tipler";

export function CagriTablosu({
  cagrilar,
  olayPenceresi,
}: {
  readonly cagrilar: readonly CizelgeCagrisi[] | undefined;
  readonly olayPenceresi: number | undefined;
}) {
  const satirlar = useMemo(() => [...(cagrilar ?? [])], [cagrilar]);
  const bosSayisi = useMemo(() => satirlar.filter((c) => c.empty === true).length, [satirlar]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{satirlar.length} çağrı (pencerede)</Badge>
        <Badge variant={bosSayisi > 0 ? "destructive" : "outline"}>{bosSayisi} boş dönen</Badge>
        <Badge variant="outline">
          taranan olay: <Deger deger={olayPenceresi} neden="`olay_penceresi` yazılmamış" />
        </Badge>
      </div>

      <div className="min-w-0 overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow>
              <TableHead className="whitespace-nowrap">Zaman</TableHead>
              <TableHead className="whitespace-nowrap">Tür</TableHead>
              <TableHead className="whitespace-nowrap">Model</TableHead>
              <TableHead className="whitespace-nowrap">Deneme</TableHead>
              <TableHead className="whitespace-nowrap">Araç çağrısı</TableHead>
              <TableHead className="whitespace-nowrap">Sonuç</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {satirlar.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center">
                  <span className="text-muted-foreground text-sm">
                    Bu olay penceresinde ajan çağrısı görülmedi — &quot;çağrı yapılmadı&quot; DEĞİL.
                  </span>
                </TableCell>
              </TableRow>
            ) : (
              satirlar.map((c, i) => (
                <TableRow key={`${c.ts ?? "?"}#${i}`} className={c.empty === true ? "bg-destructive/5" : undefined}>
                  <TableCell className="whitespace-nowrap text-xs tabular-nums">
                    {zamanMetni(c.ts) ?? <Olculemedi neden="olay `ts` taşımıyor" kisa />}
                  </TableCell>
                  <TableCell className="text-xs">
                    {c.kind ?? <Olculemedi neden="olay `kind` taşımıyor" kisa />}
                  </TableCell>
                  <TableCell className="text-xs">
                    {c.model ? (
                      <code className="break-all font-mono text-[11px]">{c.model}</code>
                    ) : (
                      <Olculemedi neden="olay `model` taşımıyor" kisa />
                    )}
                  </TableCell>
                  <TableCell>
                    <Deger deger={c.attempt} neden="`attempt` yazılmamış" />
                  </TableCell>
                  <TableCell>
                    <Deger deger={c.tool_calls} neden="`tool_calls` yazılmamış" />
                  </TableCell>
                  <TableCell>
                    <HukumRozet
                      ton={c.empty === undefined ? "olculemedi" : c.empty ? "kotu" : "iyi"}
                      metin={c.empty === undefined ? "bilinmiyor" : c.empty ? "BOŞ döndü" : "dolu cevap"}
                      baslik="`empty` — çağrı koştu ama içerik üretmedi mi"
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <p className="text-muted-foreground text-xs leading-5">
        Uç son <strong>30</strong> çağrıyı döndürüyor ve onları da sınırlı bir olay penceresinden
        süzüyor (<code className="font-mono text-[11px]">obs.recent(3000)</code>). Bu tablo bir
        harcama defteri DEĞİLDİR — maliyet ve token kırılımı kanonik olarak{" "}
        <code className="font-mono text-[11px]">/api/hermes</code> <code className="font-mono text-[11px]">spend</code>{" "}
        yüzeyindedir ve bu sayfa oraya ikinci bir tüketici bağlamıyor.
      </p>
    </div>
  );
}
