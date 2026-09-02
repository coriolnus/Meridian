"use client";

/* ============================================================================
   ONAY DEFTERİ — `approvals.jsonl` (verilmiş kararların sicili)
   ----------------------------------------------------------------------------
   BU KART BOŞ GÖRÜNDÜĞÜNDE "KARAR VERİLMEDİ" DEMEK DEĞİLDİR ve bu, ölçülmüş bir
   uç davranışıdır: `api_approvals` defteri YALNIZ `autonomy_level >= 1` iken
   döndürüyor (api.py::api_approvals — `pending: ... if lvl >= 1 else []`). L0'da liste HER
   ZAMAN boş gelir, oysa defterde satır OLABİLİR: `POST /api/approvals/{id}` L0'da
   da yazıyor (kapı-bağlamayan `kayit:` ve `arming:` önekleri için, api.py::_onay_bekleyen_damgala).
   Yani L0'da bu kart bir ÖLÇÜM DEĞİL, bir KAPIDIR — ve öyle yazıyor.

   `davranissal: false` SATIRIN KENDİ KÜNYESİDİR: defteri okuyan, o kararın hiçbir
   icrayı açmadığını satırdan görmeli. Sütun bu yüzden var; alan yoksa "ölçülemedi"
   yazılır, "davranışsal" varsayılmaz.
   ============================================================================ */
import { BookLock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { BolumKart, Olculemedi, zamanMetni } from "./parcalar";

/** Ham defter satırının okunabilen kesiti. Alanların hiçbiri garanti DEĞİL (JSONL). */
function alan(satir: Record<string, unknown>, ad: string): string | null {
  const v = satir[ad];
  if (v === undefined || v === null) return null;
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  return JSON.stringify(v);
}

export function OnayDefteri({
  satirlar,
  seviye,
  neden,
  teknik,
}: {
  readonly satirlar: readonly Record<string, unknown>[] | undefined;
  readonly seviye: number | undefined;
  /** Uç okunamadıysa NEDEN — boş tablo çizmeden önce bunu yazmak zorundayız. */
  readonly neden: string | null;
  readonly teknik?: string;
}) {
  // EN YENİ ÜSTTE: defter append-only yazılıyor (`append_jsonl`), yani dosya sırası
  // KRONOLOJİK. Ters çevirmek bir yorum değil, okuma yönünün düzeltilmesi.
  const ters = satirlar ? [...satirlar].reverse().slice(0, 40) : [];

  return (
    <BolumKart
      kimlik="defter"
      baslik="Onay defteri"
      soru="Hangi karar ne zaman, hangi gerekçeyle yazıldı?"
      ikon={BookLock}
      aksiyon={
        seviye === undefined ? (
          <Badge variant="outline">otonomi seviyesi ölçülemedi</Badge>
        ) : (
          <Badge variant={seviye >= 1 ? "secondary" : "outline"}>L{seviye}</Badge>
        )
      }
    >
      {seviye !== undefined && seviye < 1 ? (
        <p className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-sm leading-6">
          Sistem <strong>L{seviye}</strong>. Uç bu seviyede defteri HİÇ döndürmüyor
          (<code className="font-mono text-xs">pending: [] if level &lt; 1</code>) — aşağıdaki liste
          bir ölçüm değil, kapalı bir kapıdır. Defterde satır olabilir: kapı-bağlamayan kararlar
          (<code className="font-mono text-xs">kayit:</code> · <code className="font-mono text-xs">arming:</code>)
          L0&apos;da da yazılıyor, yalnız buradan okunmuyor.
        </p>
      ) : null}

      {neden !== null ? (
        <Olculemedi neden={neden} teknik={teknik} />
      ) : ters.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          {seviye !== undefined && seviye < 1
            ? "Uç bu seviyede satır döndürmüyor (yukarıdaki kapı notu)."
            : "Defterde satır yok. Bu, hiç karar verilmediği anlamına gelir — uç L1+&apos;ta defterin TAMAMINI döndürür, kırpma yapmaz."}
        </p>
      ) : (
        <>
          <div className="min-w-0 overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader className="bg-muted/30">
                <TableRow>
                  <TableHead className="whitespace-nowrap">Damga</TableHead>
                  <TableHead className="whitespace-nowrap">Kimlik</TableHead>
                  <TableHead className="whitespace-nowrap">Karar</TableHead>
                  <TableHead className="whitespace-nowrap">Davranışsal mı</TableHead>
                  <TableHead>Gerekçe</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ters.map((s, i) => {
                  const kimlik = alan(s, "id");
                  const karar = alan(s, "decision");
                  const davranissal = s["davranissal"];
                  return (
                    <TableRow key={`${kimlik ?? "?"}#${i}`}>
                      <TableCell className="whitespace-nowrap align-top text-xs tabular-nums">
                        {zamanMetni(alan(s, "ts")) ?? <Olculemedi neden="Kararın zamanı kaydedilmemiş" teknik="satır `ts` taşımıyor" kisa />}
                      </TableCell>
                      <TableCell className="align-top">
                        {kimlik === null ? (
                          <Olculemedi neden="Kimlik yok — bu karar hiçbir işle eşleşemez" teknik="satır `id` taşımıyor — kapı bu satırı eşleştiremez" kisa />
                        ) : (
                          <code className="break-all font-mono text-xs">{kimlik}</code>
                        )}
                      </TableCell>
                      <TableCell className="align-top">
                        {karar === null ? (
                          <Olculemedi neden="Karar kaydedilmemiş — kontrolde onaysız sayılır" teknik="`decision` yok — kapıda 'onay YOK' sayılır (fail-closed)" kisa />
                        ) : (
                          <Badge variant={karar === "approve" ? "secondary" : "outline"}>{karar}</Badge>
                        )}
                      </TableCell>
                      <TableCell className="align-top">
                        {davranissal === undefined ? (
                          // ALANIN YOKLUĞU "DAVRANIŞSAL" DEMEK: sunucu `davranissal:false`ı yalnız
                          // kapı-bağlamayan satırlara yazıyor. Yine de VARSAYMIYORUZ — yokluğu
                          // olduğu gibi söylüyoruz, çünkü yarın yazım kuralı değişebilir.
                          <span
                            className="text-muted-foreground text-xs"
                            title="satır `davranissal` alanı taşımıyor — sunucu bunu yalnız kapı-bağlamayan kararlara yazıyor"
                          >
                            alan yok
                          </span>
                        ) : davranissal === false ? (
                          <Badge variant="outline">kayıt — icra açmaz</Badge>
                        ) : (
                          <Badge variant="secondary">kapı-bağlayıcı</Badge>
                        )}
                      </TableCell>
                      <TableCell className="align-top text-xs leading-5">
                        {alan(s, "reason") || (
                          <span className="text-muted-foreground">gerekçe yazılmamış</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          {satirlar && satirlar.length > 40 ? (
            <p className="text-muted-foreground text-xs">
              Defterde {satirlar.length} satır var; en yeni 40 tanesi gösteriliyor. Kırpma BU
              PANONUNDUR (uç kırpmıyor) — sayı yanda dursun ki eksik okunmasın.
            </p>
          ) : null}
        </>
      )}
    </BolumKart>
  );
}
