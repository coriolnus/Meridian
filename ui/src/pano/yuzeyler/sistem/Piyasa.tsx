"use client";

/* ============================================================================
   PİYASA — evrenin büyüklüğü ve bar tazeliği (`/api/market`)
   ----------------------------------------------------------------------------
   `?seri=1` BİLEREK İSTENMİYOR: seri her satıra ~40 kapanış ekler (260 sembol
   ≈ 91 KB, marketview.build şerhinde ÖLÇÜLMÜŞ) ve bu bölüm kıvılcım çizmiyor.
   İstemek, çizmediğimiz bir yükü her tazelemede taşımak olurdu.

   BAYATLIK EMEKLİYE SORULMAZ (marketview.py:341): delist gününde donmuş bir
   sembolün barı as_of'un gerisinde olmak ZORUNDADIR. Bu yüzden `stale_n` ucun
   kendi hesabıdır ve biz yeniden hesaplamıyoruz — aynı yasanın iki kaynağı, bu
   depodaki baskın hata desenidir. Tabloda gösterdiğimiz "bayat satırlar" listesi
   ucun sayacıyla AYNI kuralı uygular (emekli hariç) ve iki sayı yan yana yazılır;
   ayrışırlarsa ekranda görünür, sessizce örtülmez.

   SEANS İÇİ KOLON BOŞSA NEDENİ VARDIR: uç üç ayrı boşluğu ayırıyor (izlenecek
   sembol yok / akış yok / akış bayat) ve `intraday.reason` o cümleyi taşıyor.
   Boş kolonu sessiz bırakmak üçünü tek sessizliğe indirirdi.
   ============================================================================ */
import { CandlestickChart } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, Satir, zamanMetni } from "./parcalar";
import type { PiyasaGovdesi, PiyasaSatiri } from "./uctipleri";

const GRAFIK: ChartConfig = { n: { label: "sembol", color: "var(--chart-1)" } };

export function Piyasa({ durum }: { readonly durum: Durum<PiyasaGovdesi> }) {
  return (
    <BolumKart
      kimlik="market"
      baslik="Piyasa"
      soru="Kaç bar bayat, evren taze mi?"
      ikon={CandlestickChart}
      aksiyon={
        durum.veri?.as_of ? (
          <Badge variant="outline" title="Evrendeki EN TAZE seans. Bu uç canlı fiyat servis etmez — EOD kapanıştır.">
            as_of {durum.veri.as_of}
          </Badge>
        ) : null
      }
    >
      <Kapi durum={durum} yol="/api/market">
        {(m) => {
          const rows: readonly PiyasaSatiri[] = m.rows ?? [];
          // TAZELİK DAĞILIMI: satırları son bar seansına göre sayar. Emekliler AYRI
          // kovada — ucun `stale_n` kuralı da onları dışarıda bırakıyor (marketview.py:341).
          const sayac = new Map<string, number>();
          let emekli = 0;
          let tarihsiz = 0;
          for (const r of rows) {
            if (r.retired) {
              emekli += 1;
              continue;
            }
            if (!r.last_date) {
              tarihsiz += 1;
              continue;
            }
            sayac.set(r.last_date, (sayac.get(r.last_date) ?? 0) + 1);
          }
          const dagilim = [...sayac.entries()]
            .sort((a, b) => (a[0] < b[0] ? 1 : -1))
            .slice(0, 12)
            .reverse()
            .map(([seans, n]) => ({ seans, n }));

          const bayatlar = rows
            .filter((r) => !r.retired && r.last_date && m.as_of && r.last_date < m.as_of)
            .sort((a, b) => (a.last_date ?? "").localeCompare(b.last_date ?? ""))
            .slice(0, 25);

          return (
            <>
              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="Evren büyüklüğü (satır)">
                    <Deger deger={m.n} birim=" sembol" neden="/api/market `n` döndürmedi" />
                  </Satir>
                  <Satir etiket="Bayat bar (ucun sayacı)">
                    {m.stale_n === undefined ? (
                      <Olculemedi neden="/api/market `stale_n` döndürmedi" kisa />
                    ) : (
                      <span
                        className={
                          m.stale_n > 0
                            ? "font-medium text-amber-600 tabular-nums dark:text-amber-400"
                            : "tabular-nums text-emerald-600 dark:text-emerald-400"
                        }
                      >
                        {m.stale_n}
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="Bayat satır (bu ekranda sayılan)">
                    {m.rows === undefined || !m.as_of ? (
                      <Olculemedi neden="rows ya da as_of gelmedi — sayım yapılamaz" kisa />
                    ) : (
                      <span className="tabular-nums">
                        {rows.filter((r) => !r.retired && r.last_date && m.as_of && r.last_date < m.as_of).length}
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="Emekli sembol">
                    <Deger deger={m.retired_n} neden="/api/market `retired_n` döndürmedi" />
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Kaynak">
                    {m.source === undefined ? (
                      <Olculemedi neden="/api/market `source` bloğu gelmedi" kisa />
                    ) : (
                      <span className="tabular-nums">
                        bars {m.source.bars ?? "?"} · finviz ekstra {m.source.finviz_extra ?? "?"}
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="Seans içi ölçüm">
                    {m.intraday === undefined ? (
                      <Olculemedi neden="/api/market `intraday` bloğu gelmedi" kisa />
                    ) : m.intraday.reason ? (
                      <span className="text-muted-foreground text-xs">
                        {m.intraday.measured_n ?? 0}/{m.intraday.tracked_n ?? 0} — {m.intraday.reason}
                      </span>
                    ) : (
                      <span className="tabular-nums">
                        {m.intraday.measured_n ?? 0}/{m.intraday.tracked_n ?? 0} sembol ölçüldü (tolerans{" "}
                        {m.intraday.stale_tol_s ?? "?"} sn)
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="Grafikten ayrılan">
                    <span className="text-muted-foreground text-xs tabular-nums">
                      emekli {emekli} · son bar tarihi olmayan {tarihsiz}
                    </span>
                  </Satir>
                  <Satir etiket="Rejim (regime.json'da GERÇEKTEN olan)">
                    {m.regime === undefined || Object.keys(m.regime).length === 0 ? (
                      <Olculemedi neden="regime.json boş — uç olmayan anahtarı None ile doldurmuyor" kisa />
                    ) : (
                      <span className="text-xs">
                        {Object.entries(m.regime)
                          .map(([k, v]) => `${k}=${String(v)}`)
                          .join(" · ")}
                      </span>
                    )}
                  </Satir>
                </div>
              </div>

              {dagilim.length === 0 ? (
                <Olculemedi neden="son bar tarihi taşıyan yaşayan sembol yok — dağılım çizilemedi" />
              ) : (
                <ChartContainer config={GRAFIK} className="aspect-auto h-56 w-full">
                  <BarChart data={dagilim} margin={{ left: 4, right: 8 }}>
                    <CartesianGrid vertical={false} />
                    <XAxis dataKey="seans" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis tickLine={false} axisLine={false} allowDecimals={false} width={44} />
                    <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel />} />
                    <Bar isAnimationActive={false} dataKey="n" fill="var(--color-n)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ChartContainer>
              )}
              <p className="text-muted-foreground text-xs">
                Son bar seansına göre sembol dağılımı (en yeni 12 seans, emekliler hariç). Sağdaki çubuk
                `as_of` seansıdır; solundaki her çubuk o kadar sembolün geride kaldığını söyler.
              </p>

              {bayatlar.length > 0 ? (
                <div className="overflow-x-auto">
                  <Table className="min-w-[44rem]">
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead>Sembol</TableHead>
                        <TableHead>Son bar</TableHead>
                        <TableHead className="text-right">Kapanış</TableHead>
                        <TableHead className="text-right">20g ADV</TableHead>
                        <TableHead>Kaynak</TableHead>
                        <TableHead>Bayrak</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bayatlar.map((r, i) => (
                        <TableRow key={r.ticker ?? `bayat-${i}`}>
                          <TableCell className="font-medium font-mono">{r.ticker ?? "?"}</TableCell>
                          <TableCell className="text-muted-foreground text-xs">
                            {r.last_date ?? <Olculemedi neden="satır last_date taşımıyor" kisa />}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            <Deger deger={r.close} basamak={2} neden="bar okunamadı" />
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            <Deger deger={r.adv20_usd} basamak={0} neden="ADV ölçülemedi" />
                          </TableCell>
                          <TableCell className="text-muted-foreground text-xs">{r.source ?? "?"}</TableCell>
                          <TableCell className="flex flex-wrap gap-1">
                            {r.position ? <Badge variant="secondary">pozisyon</Badge> : null}
                            {r.armed ? <Badge variant="secondary">silahlı</Badge> : null}
                            {(r.plans_n ?? 0) > 0 ? <Badge variant="outline">{r.plans_n} plan</Badge> : null}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <p className="mt-2 text-muted-foreground text-xs">
                    En eski barlı 25 satır gösterildi (emekliler hariç). Tam liste bu bölümde YOK — evren
                    bakımının yeri Veri borusu bölümündeki `no_data_report` sayaçlarıdır.
                  </p>
                </div>
              ) : m.rows === undefined ? (
                <Olculemedi neden="/api/market `rows` döndürmedi — bayat satırlar listelenemedi" />
              ) : (
                <p className="text-muted-foreground text-sm">
                  Yaşayan hiçbir sembolün barı `as_of`un gerisinde değil.
                </p>
              )}

              <p className="text-muted-foreground text-xs">
                Okuma zamanı: {zamanMetni(durum.zaman?.toISOString()) ?? "henüz okunmadı"} · bu uç EOD
                kapanış servis eder, canlı fiyat DEĞİL.
              </p>
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
