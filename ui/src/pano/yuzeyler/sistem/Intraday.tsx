"use client";

/* ============================================================================
   SEANS İÇİ AKIŞ — üç katman, üçü de AYRI ölçülür (`/api/diagnostics`)
   ----------------------------------------------------------------------------
   marketstream (WS dinleyicisi) → hotstate (Redis sıcak katman) → barfeed
   (dayanıklı bar tetiği) → intraday_cycle (karar hattı). Dördü AYRI sağlıktır ve
   dördü de `ok: true|false|null` üçlüsünü taşır (`null` = "hiç kurulmadı", bozuk
   DEĞİL). Tek bir "akış sağlıklı" hapı basmak, hangi halkanın koptuğunu gizlerdi —
   ve bu depoda ölçülmüş bir vaka var: `stream_ok: true` diskte DONMUŞ, son olay
   3 gün eskiydi (api.py::api_diagnostics şerhi). Bu yüzden bayrağın yanına nabız yaşı yazılır.

   "BUGÜN" SAYACI TOPLAMDAN AYRI (api.py::api_audit_trail): ömür boyu biriken toplam, "bugün
   akış çalıştı mı?" sorusunu ASLA cevaplayamaz — dünkü 400 satır bugünkü sessizliği
   gizler.

   AKIŞ BOŞLUĞU ÜÇÜNCÜ HÂLİ: `akis_boslugu === null` "boşluk yok" DEĞİL, "kanca bu
   süreçte hiç koşmadı" demektir. İkisini aynı boşlukla göstermek, bakılmamış bir
   seansı temiz sanmaktır.
   ============================================================================ */
import { Activity } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, OkRozet, Satir, sureMetni, zamanMetni } from "./parcalar";
import type { IntradayKarari, TeshisGovdesi } from "./uctipleri";

const GRAFIK: ChartConfig = { n: { label: "atlanan", color: "var(--chart-3)" } };

/** Kararın serbest alanlarından okunabilir bir hücre üretir; bulunamazsa `null` (uydurma yok). */
function alan(k: IntradayKarari, adlar: readonly string[]): string | null {
  for (const a of adlar) {
    const v = k[a];
    if (typeof v === "string" && v) return v;
    if (typeof v === "number") return String(v);
    if (typeof v === "boolean") return v ? "evet" : "hayır";
  }
  return null;
}

export function Intraday({ teshis }: { readonly teshis: Durum<TeshisGovdesi> }) {
  return (
    <BolumKart kimlik="intraday" baslik="Seans içi akış" soru="Gün içi akış canlı mı?" ikon={Activity}>
      <Kapi durum={teshis} yol="/api/diagnostics">
        {(d) => {
          const i = d.intraday;
          const hud = d.hud ?? {};
          const kararlar: readonly IntradayKarari[] = i?.decisions?.recent ?? [];
          const atlanan = Object.entries(i?.skipped ?? {})
            .map(([neden, n]) => ({ neden: neden.length > 20 ? `${neden.slice(0, 19)}…` : neden, n }))
            .sort((a, b) => b.n - a.n)
            .slice(0, 10);
          const bosluk = i?.akis_boslugu;

          const halkalar = [
            { ad: "marketstream (WS)", ok: d.marketstream?.ok, not: "Alpaca canlı besleme dinleyicisi" },
            { ad: "hotstate (Redis)", ok: d.hotstate?.ok, not: "sıcak katman — fiyat/bar tamponu" },
            { ad: "barfeed (consumer-group)", ok: d.barfeed?.ok, not: "dayanıklı bar tetiği" },
            { ad: "intraday_cycle", ok: i?.ok, not: "karar hattı (gözlem / işleme hazır)" },
          ];

          return (
            <>
              <div className="overflow-x-auto">
                <Table className="min-w-[40rem]">
                  <TableHeader className="bg-muted/50">
                    <TableRow>
                      <TableHead>Halka</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Ne yapar</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {halkalar.map((h) => (
                      <TableRow key={h.ad}>
                        <TableCell className="font-medium font-mono text-xs">{h.ad}</TableCell>
                        <TableCell>
                          <OkRozet
                            ok={h.ok}
                            iyi="koşuyor"
                            kotu="kopuk"
                            neden="Bu halkanın durumu bildirilmedi — hiç kurulmamış olabilir"
                            teknik="health() `ok` alanı gelmedi"
                          />
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{h.not}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="WS bayrağı (nabızla çarpılmış)">
                    <OkRozet
                      ok={hud.stream_ok}
                      iyi="canlı"
                      kotu="kopuk"
                      neden="Canlı besleme bu süreçte hiç koşmamış"
                      teknik="broker tarafı aynası hiç koşmamış — stream_ok null "
                    />
                  </Satir>
                  <Satir etiket="Son akış olayı">
                    {zamanMetni(hud.stream_last_event_ts) ?? (
                      <Olculemedi neden="Akıştan hiç olay görülmemiş" teknik="stream_last_event_ts yok" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Ne zamandır kopuk">
                    {hud.stream_down_since ? (
                      <span className="text-uyari">
                        {zamanMetni(hud.stream_down_since) ?? hud.stream_down_since}
                      </span>
                    ) : hud.stream_down_since === null ? (
                      <span className="text-basari">kopuş kaydı yok</span>
                    ) : (
                      <Olculemedi neden="Kopukluğun ne zaman başladığı bildirilmedi" teknik="stream_down_since alanı gelmedi" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Nabız yaşı">
                    {sureMetni(hud.heartbeat_age_s) ?? (
                      <Olculemedi neden="Nabzın yaşı ölçülemedi" teknik="heartbeat_age_s ölçülemedi" kisa />
                    )}
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Mod">
                    {i?.mode ? (
                      <Badge variant={i.mode === "arm" ? "secondary" : "outline"}>
                        {i.mode === "arm" ? "SİLAHLI" : "gözlem"}
                      </Badge>
                    ) : (
                      <Olculemedi neden="Karar hattının hangi modda olduğu bildirilmedi" teknik="intraday `mode` alanı gelmedi" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Kararlar (bugün / toplam)">
                    {i?.decisions === undefined ? (
                      <Olculemedi neden="Karar sayaçları bildirilmedi" teknik="intraday.decisions bloğu gelmedi" kisa />
                    ) : (
                      <span className="tabular-nums">
                        {i.decisions.today ?? "?"} / {i.decisions.total ?? "?"} · tetiklenen{" "}
                        {i.decisions.fired ?? "?"}
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="İzlenen sembol / işleme hazır plan">
                    <span className="tabular-nums">
                      <Deger deger={i?.watched} neden="İzlenen sembol sayısı bildirilmedi" teknik="intraday.watched gelmedi" /> /{" "}
                      <Deger deger={i?.armed_plans} neden="İşleme hazır plan sayısı okunamadı" teknik="portfolio.armed okunamadı" />
                    </span>
                  </Satir>
                  <Satir etiket="Son karar / son hata">
                    <span className="text-xs">
                      {zamanMetni(i?.last_decision_at) ?? "karar damgası yok"}
                      {i?.last_error ? <span className="ml-1 text-destructive">· {i.last_error}</span> : null}
                    </span>
                  </Satir>
                </div>
              </div>

              {atlanan.length > 0 ? (
                <>
                  <ChartContainer config={GRAFIK} className="aspect-auto h-56 w-full">
                    <BarChart data={atlanan} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <CartesianGrid horizontal={false} />
                      <XAxis type="number" dataKey="n" tickLine={false} axisLine={false} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="neden"
                        tickLine={false}
                        axisLine={false}
                        width={150}
                        tick={{ fontSize: 11 }}
                      />
                      <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel />} />
                      <Bar isAnimationActive={false} dataKey="n" fill="var(--color-n)" radius={4} />
                    </BarChart>
                  </ChartContainer>
                  <p className="text-muted-foreground text-xs">
                    Karar hattının sembolü NEDEN atladığı (`skipped` sayacı). Bu sayaçlar diske yazılmaz —
                    süreç yeniden başlarsa sıfırlanır.
                  </p>
                </>
              ) : i?.skipped === undefined ? (
                <Olculemedi neden="Atlama sayacı bildirilmedi" teknik="intraday `skipped` sayacı gelmedi" />
              ) : (
                <p className="text-muted-foreground text-sm">Atlama sayacı boş — bu süreçte hiç sembol atlanmadı.</p>
              )}

              {/* --- AKIŞ BOŞLUĞU: ÜÇÜNCÜ HÂL AYRI --- */}
              {bosluk === null || bosluk === undefined ? (
                <Olculemedi neden="Boşluk taraması bu süreçte hiç koşmadı — boşluk yok değil, bakılmadı" teknik="`akis_boslugu` null (api.py::api_diagnostics)" />
              ) : bosluk.durum && bosluk.durum !== "ok" ? (
                <p className="text-muted-foreground text-sm">
                  Boşluk taraması karar VERMEDİ — durum: <span className="font-mono">{bosluk.durum}</span> (
                  {bosluk.gun ?? "gün yok"}). Boş boşluk listesi bu hâlde "boşluk yok" anlamına gelmez.
                </p>
              ) : (
                <div>
                  <Satir etiket="Boşluk taraması">
                    <span className="tabular-nums">
                      {bosluk.bosluk_sayisi ?? 0} boşluk · yeni uyarı {bosluk.yeni_uyari ?? 0} · gelen bar{" "}
                      {bosluk.gelen_bar ?? "?"} · ölçüldü {zamanMetni(bosluk.olculdu) ?? "?"}
                    </span>
                  </Satir>
                  {(bosluk.bosluklar?.length ?? 0) > 0 ? (
                    <div className="mt-2 overflow-x-auto">
                      <Table className="min-w-[38rem]">
                        <TableHeader className="bg-muted/50">
                          <TableRow>
                            <TableHead>Tür</TableHead>
                            <TableHead>Sembol</TableHead>
                            <TableHead>Aralık</TableHead>
                            <TableHead className="text-right">Eksik dk</TableHead>
                            <TableHead className="text-right">Beklenen / gelen</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(bosluk.bosluklar ?? []).map((b, k) => (
                            <TableRow key={`${b.tur ?? "?"}-${b.sembol ?? "*"}-${b.baslangic ?? k}`}>
                              <TableCell>
                                <Badge variant={b.tur === "akis" ? "destructive" : "outline"}>{b.tur ?? "?"}</Badge>
                              </TableCell>
                              <TableCell className="font-mono text-xs">{b.sembol ?? "tüm akış"}</TableCell>
                              <TableCell className="text-muted-foreground text-xs">
                                {b.baslangic?.slice(11, 16) ?? "?"}–{b.bitis?.slice(11, 16) ?? "?"}Z
                              </TableCell>
                              <TableCell className="text-right tabular-nums">
                                <Deger deger={b.eksik_dk} neden="Kaç dakikanın eksik olduğu kaydedilmemiş" teknik="eksik_dk yok" />
                              </TableCell>
                              <TableCell className="text-right tabular-nums">
                                {b.beklenen ?? "?"} / {b.gelen ?? "?"}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <p className="mt-2 text-muted-foreground text-xs">
                        `sembol` türü boşluk çoğu vakada arıza DEĞİL: IEX tek borsadır ve o dakikada o
                        borsada işlem geçmemiş olabilir (ölçüldü: 15 rastgele alarmın 15'i konsolide
                        beslemede doluydu). `akis` türü ise gerçek kesintidir.
                      </p>
                    </div>
                  ) : null}
                </div>
              )}

              {kararlar.length > 0 ? (
                <div className="overflow-x-auto">
                  <Table className="min-w-[40rem]">
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead>Zaman</TableHead>
                        <TableHead>Sembol</TableHead>
                        <TableHead>Karar</TableHead>
                        <TableHead>Neden</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {kararlar.map((k, idx) => (
                        <TableRow key={`${String(k.ts ?? "")}-${idx}`}>
                          <TableCell className="whitespace-nowrap text-muted-foreground text-xs">
                            {zamanMetni(typeof k.ts === "string" ? k.ts : null) ?? (
                              <Olculemedi neden="Kararın zamanı kaydedilmemiş" teknik="karar `ts` taşımıyor" kisa />
                            )}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {alan(k, ["ticker", "symbol"]) ?? <Olculemedi neden="Kararın hangi sembole ait olduğu kaydedilmemiş" teknik="karar satırı ticker/symbol taşımıyor" kisa />}
                          </TableCell>
                          <TableCell className="text-xs">
                            {alan(k, ["action", "decision", "karar"]) ?? (
                              <Olculemedi neden="Ne karar verildiği kaydedilmemiş" teknik="karar satırı action/decision/karar taşımıyor" kisa />
                            )}
                          </TableCell>
                          <TableCell className="max-w-[22rem] truncate text-xs">
                            {alan(k, ["reason", "neden", "detail"]) ?? (
                              <Olculemedi neden="Kararın gerekçesi kaydedilmemiş" teknik="karar satırı reason/neden/detail taşımıyor" kisa />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <p className="mt-2 text-muted-foreground text-xs">
                    Son 8 karar (uç kırpıyor). Karar satırlarının şeması SABİT DEĞİLDİR — alan bulunamadığında
                    hücre bunu söyler, boş bırakmaz.
                  </p>
                </div>
              ) : null}
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
