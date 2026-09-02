"use client";

/* ============================================================================
   VERİ BORUSU — beş sağlayıcı + hattın tıkanma noktaları (`/api/diagnostics`)
   ----------------------------------------------------------------------------
   `ok` ÜÇ DEĞERLİDİR ve kartın tamamı buna göre kuruldu: `true` sağlam, `false`
   bozuk, `null` "BU SÜREÇTE HENÜZ ÇAĞRI YAPILMADI". Üçüncüsünü ikinciye katmak,
   yeni başlatılmış bir süreçte beş sağlayıcıyı da kırmızı göstermek olurdu; birinciye
   katmak ise ölçülmemişi sağlam saymak. Ucun kendi beyanı (`saglayicilar.beyan`)
   kartın altında AYNEN duruyor — sayaçlar diske yazılmıyor, yeniden başlatmada sıfırlanıyor.

   HATA ORANI GRAFİĞİ yalnız ÇAĞRI YAPILMIŞ sağlayıcıları çizer: `cagri` 0 iken oran
   `null` döner (api.py::_saglayici_satiri) ve sıfır çubuk çizmek "hiç bozulmadı" diye okunurdu.
   Elenen satır sayısı grafiğin altında yazılı — sessiz eleme yok (YASA 4).

   İKİ AYRI "ÇAPRAZ KONTROL" KARIŞTIRILMAZ: `crosscheck` endeks düzeyi, `massive_crosscheck`
   sembol düzeyi (api.py::api_diagnostics şerhi). Bu kart ikisini de göstermez — göstermediğini söyler.
   ============================================================================ */
import { Database } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, OkRozet, Satir, zamanMetni } from "./parcalar";
import type { SaglayiciSatiri, TeshisGovdesi } from "./uctipleri";

const GRAFIK: ChartConfig = {
  cagri: { label: "çağrı", color: "var(--chart-2)" },
  hata: { label: "hata", color: "var(--chart-4)" },
};

function ekMetni(ek: Readonly<Record<string, unknown>> | undefined): string {
  if (!ek) return "";
  return Object.entries(ek)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
    .join(" · ");
}

export function Veriboru({ teshis }: { readonly teshis: Durum<TeshisGovdesi> }) {
  return (
    <BolumKart kimlik="veriboru" baslik="Veri borusu" soru="Veri nereden geliyor, nerede tıkandı?" ikon={Database}>
      <Kapi durum={teshis} yol="/api/diagnostics">
        {(d) => {
          const blok = d.saglayicilar;
          const satirlar: readonly SaglayiciSatiri[] = blok?.saglayicilar ?? [];
          const cagrilanlar = satirlar.filter((s) => (s.cagri ?? 0) > 0);
          const elenen = satirlar.length - cagrilanlar.length;
          const grafik = cagrilanlar.map((s) => ({
            ad: s.ad ?? "?",
            cagri: s.cagri ?? 0,
            hata: s.hata ?? 0,
          }));
          const p = d.pipeline;
          const karantina = p?.quarantine ?? [];
          const nd = p?.symbol_no_data;
          const io = p?.io;

          return (
            <>
              {/* --- SAĞLAYICI SAĞLIK KARTI --- */}
              {blok === undefined ? (
                <Olculemedi neden="Sağlayıcıların sağlığı bildirilmedi" teknik="/api/diagnostics `saglayicilar` bloğunu döndürmedi" />
              ) : (
                <>
                  {grafik.length > 0 ? (
                    <ChartContainer config={GRAFIK} className="aspect-auto h-56 w-full">
                      <BarChart data={grafik} margin={{ left: 4, right: 8 }}>
                        <CartesianGrid vertical={false} />
                        <XAxis dataKey="ad" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                        <YAxis tickLine={false} axisLine={false} allowDecimals={false} width={44} />
                        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
                        <Bar isAnimationActive={false} dataKey="cagri" fill="var(--color-cagri)" radius={[4, 4, 0, 0]} />
                        <Bar isAnimationActive={false} dataKey="hata" fill="var(--color-hata)" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ChartContainer>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      Çağrı yapılmış sağlayıcı yok — grafik çizilmedi. Sıfır çubuk çizmek "hiç bozulmadı"
                      diye okunurdu; doğru cümle "bu süreçte henüz çağrı yapılmadı".
                    </p>
                  )}
                  {elenen > 0 ? (
                    <p className="text-muted-foreground text-xs">
                      Grafikten elenen satır: {elenen} — `cagri` 0 olduğu için hata oranı ölçülemez (api.py::_saglayici_satiri).
                      Satırların kendisi aşağıdaki tabloda duruyor.
                    </p>
                  ) : null}

                  <div className="overflow-x-auto">
                    <Table className="min-w-[58rem]">
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead>Sağlayıcı</TableHead>
                          <TableHead>Durum</TableHead>
                          <TableHead className="text-right">Çağrı</TableHead>
                          <TableHead className="text-right">Hata</TableHead>
                          <TableHead className="text-right">Hata oranı</TableHead>
                          <TableHead>Son çağrı</TableHead>
                          <TableHead>Son hata / ek</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {satirlar.map((s, i) => (
                          <TableRow key={s.ad ?? `saglayici-${i}`}>
                            <TableCell className="font-medium">{s.ad ?? "?"}</TableCell>
                            <TableCell>
                              {s.olculemedi ? (
                                <Olculemedi neden="Bu sağlayıcının sağlığı okunamadı" teknik={`sağlık okunamadı: ${s.olculemedi}`} kisa />
                              ) : (
                                <OkRozet ok={s.ok} neden="Sağlayıcının durumu bildirilmedi" teknik="sağlayıcı `ok` alanı gelmedi" />
                              )}
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              <Deger deger={s.cagri} neden="Çağrı sayacı tutulmamış" teknik="satır `cagri` taşımıyor" />
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              <Deger deger={s.hata} neden="Hata sayacı tutulmamış" teknik="satır `hata` taşımıyor" />
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              {s.hata_orani === null || s.hata_orani === undefined ? (
                                <Olculemedi neden="Hata oranı hesaplanamadı" teknik="çağrı 0 ya da sayaç biçimsiz — oran ölçülemez" kisa />
                              ) : (
                                `${(s.hata_orani * 100).toFixed(2)}%`
                              )}
                            </TableCell>
                            <TableCell className="whitespace-nowrap text-muted-foreground text-xs">
                              {zamanMetni(s.son_cagri_ts) ?? (
                                <Olculemedi neden="Son çağrının zamanı kaydedilmemiş" teknik="son çağrı damgası yok" kisa />
                              )}
                            </TableCell>
                            <TableCell className="max-w-[22rem] truncate text-xs" title={s.son_hata ?? ekMetni(s.ek)}>
                              {s.son_hata ? (
                                <span className="text-destructive">{s.son_hata}</span>
                              ) : (
                                <span className="text-muted-foreground">{ekMetni(s.ek) || "—"}</span>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  {blok.beyan ? <p className="text-muted-foreground text-xs">{blok.beyan}</p> : null}
                </>
              )}

              {/* --- HATTIN TIKANMA NOKTALARI --- */}
              {p === undefined ? (
                <Olculemedi neden="Hattın tıkanma noktaları bildirilmedi" teknik="/api/diagnostics `pipeline` bloğunu döndürmedi" />
              ) : (
                <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                  <div>
                    <Satir etiket="Yeniden çekme denemesi">
                      {p.refetch_attempts === undefined ? (
                        <Olculemedi neden="Yeniden çekme denemeleri sayılmamış" teknik="scheduler refetch_attempts döndürmedi" kisa />
                      ) : (
                        <span className="tabular-nums">
                          {p.refetch_attempts} / {p.refetch_max ?? "?"}
                        </span>
                      )}
                    </Satir>
                    <Satir etiket="Son yeniden çekme seansı">
                      {p.last_refetch_session ?? <Olculemedi neden="Son yeniden çekme damgası kaydedilmemiş — hiç yapılmamış olabilir" teknik="`last_refetch_session` damgası yok" kisa />}
                    </Satir>
                    <Satir etiket="Kazanç takvimi denemesi">
                      <Deger deger={p.earnings_attempts} neden="Kazanç takvimi denemeleri sayılmamış" teknik="scheduler earnings_attempts döndürmedi" />
                    </Satir>
                    <Satir etiket="FMP kotası (bugün)">
                      {p.fmp_usage === undefined || Object.keys(p.fmp_usage).length === 0 ? (
                        <Olculemedi neden="Günlük kota muhasebesi tutulmamış" teknik="fmp_usage.json yok" kisa />
                      ) : (
                        <span className="tabular-nums">
                          {p.fmp_usage.calls ?? "?"} çağrı · {p.fmp_usage.fails ?? "?"} hata
                          {p.fmp_usage.blocked_at ? " · KOTA BLOKLU" : ""}
                        </span>
                      )}
                    </Satir>
                    <Satir etiket="Finviz keşfi">
                      {p.finviz?.last === undefined ? (
                        <Olculemedi neden="Son aday keşfi kaydedilmemiş" teknik="finviz.status() `last` döndürmedi" kisa />
                      ) : (
                        <span>
                          {p.finviz.last.source ?? "?"} · {p.finviz.last.n ?? "?"} aday
                          {p.finviz.last.reason ? ` · ${p.finviz.last.reason}` : ""}
                        </span>
                      )}
                    </Satir>
                  </div>
                  <div>
                    <Satir etiket="Karantina (bu seans veri gelmeyen)">
                      {p.quarantine === undefined ? (
                        <Olculemedi neden="Karantina listesi bildirilmedi" teknik="data_quality.json tickers_failed yok" kisa />
                      ) : (
                        <span className="tabular-nums">{karantina.length} sembol</span>
                      )}
                    </Satir>
                    <Satir etiket="Israrla veri vermeyen (doğrulanmış)">
                      {nd === undefined ? (
                        <Olculemedi neden="Israrla veri vermeyen semboller raporlanmadı" teknik="no_data_report() bloğu gelmedi" kisa />
                      ) : (
                        <span className="tabular-nums">
                          {nd.confirmed_no_data?.length ?? 0} · şüpheli {nd.suspect?.length ?? 0} · yalnız kaynak
                          hatası {nd.source_error_only?.length ?? 0}
                        </span>
                      )}
                    </Satir>
                    <Satir etiket="Kaynak dikişi (geçmişi sabit kaynağa bağlı)">
                      <Deger deger={p.bar_source_seams?.tickers} birim=" sembol" neden="Kaynak değişimi raporlanmadı" teknik="seam_report() gelmedi" />
                    </Satir>
                    <Satir etiket="Atomik yazım gecikmesi">
                      {io === undefined ? (
                        <Olculemedi neden="Yazma gecikmesi ölçülmemiş" teknik="store.io_stats() gelmedi" kisa />
                      ) : (
                        <span className="tabular-nums">
                          p50 {io.p50_ms ?? "—"} ms ·{" "}
                          {io.p95_ms === null || io.p95_ms === undefined ? (
                            <span className="italic">p95 ölçülemedi (&lt;20 örnek)</span>
                          ) : (
                            `p95 ${io.p95_ms} ms`
                          )}{" "}
                          · {io.writes ?? "?"} yazım
                        </span>
                      )}
                    </Satir>
                    <Satir etiket="Defterler">
                      {d.ledgers === undefined ? (
                        <Olculemedi neden="Defter sayaçları bildirilmedi" teknik="/api/diagnostics `ledgers` döndürmedi" kisa />
                      ) : (
                        <span className="tabular-nums">
                          {d.ledgers.trades ?? "?"} işlem · cf açık {d.ledgers.cf_open ?? "?"}/
                          {d.ledgers.cf_cap ?? "?"} · cf çözülmüş {d.ledgers.cf_resolved ?? "?"}
                        </span>
                      )}
                    </Satir>
                  </div>
                </div>
              )}

              {karantina.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {karantina.slice(0, 40).map((t) => (
                    <Badge key={t} variant="outline" className="font-mono text-[11px]">
                      {t}
                    </Badge>
                  ))}
                  {karantina.length > 40 ? (
                    <Badge variant="secondary">+{karantina.length - 40} daha (ekranda kırpıldı)</Badge>
                  ) : null}
                </div>
              ) : null}
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
