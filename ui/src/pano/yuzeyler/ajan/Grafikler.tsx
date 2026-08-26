"use client";

/* ============================================================================
   AJANIN AĞZI — kim konuştu, kapı ne dedi, tahmin tuttu mu
   ----------------------------------------------------------------------------
   Üç grafik, üç ayrı soru; hiçbiri diğerinin paydası DEĞİL:
     · KAYNAK   — bu cümleleri kim kurdu (`source`). Ölçüldü 2026-08-25: 41 satırın
                  25'i `deterministic`, 11'i `hermes:*` (nous 6 · gemini 5), 5'i
                  arama kolları. Yani defterin çoğunluğunu LLM değil, deterministik
                  öneri üreteci yazmış — "ajan konuşuyor" cümlesi bu grafiği görmeden
                  kurulursa yanlış olur.
     · HÜKÜM    — her cümlenin sonu (`status`). Ölçüldü: 41/41 satır bir REDDE ya da
                  aşılmaya düşmüş; hiçbiri `live`/`promoted` değil.
     · KALİBRASYON — tahmin ↔ gerçekleşen. Ölçüldü: 41 satırın YALNIZ 1'inde
                  `realized_delta` var. Bu yüzden saçılım bir bulut değil, bir nokta;
                  grafik bunu gizlemek yerine payda beyanıyla SÖYLÜYOR.

   NEDEN GRİ TONLAR: tema.css'in beş grafik jetonu da akromatiktir (`--chart-1`
   oklch(0.87 0 0) … `--chart-5` oklch(0.269 0 0)). Anlamı renk değil ETİKET ve
   UZUNLUK taşıyor; yalnız "kapı reddetti" kovaları destructive tonuna boyanıyor
   çünkü orada renk bir hüküm değil, ölçülmüş bir sonucun sınıfı.
   ============================================================================ */
import { useMemo } from "react";

import { Bar, BarChart, Cell, ReferenceLine, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

import { DURUM_SOZLUGU, Olculemedi, bicimSayi, say, nesne, dizi, metin, type Hipotez } from "./ortak";

const YAPI = { n: { label: "hipotez" } } satisfies ChartConfig;

function sayimlar(deger: (h: Hipotez) => string | null, hipotezler: readonly Hipotez[]) {
  const m = new Map<string, number>();
  let yazilmamis = 0;
  for (const h of hipotezler) {
    const k = deger(h);
    if (k === null) {
      yazilmamis += 1;
      continue;
    }
    m.set(k, (m.get(k) ?? 0) + 1);
  }
  return {
    satirlar: [...m.entries()].map(([ad, n]) => ({ ad, n })).sort((a, b) => b.n - a.n),
    yazilmamis,
  };
}

/* ---- KAYNAK + HÜKÜM ------------------------------------------------------ */

export function KaynakDagilimi({ hipotezler }: { hipotezler: readonly Hipotez[] }) {
  const { satirlar, yazilmamis } = useMemo(() => sayimlar((h) => h.kaynak, hipotezler), [hipotezler]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="leading-none">Bu cümleleri kim kurdu?</CardTitle>
        <CardDescription>
          `source` alanı — LLM beyni (`hermes:*`) ile deterministik üreteç aynı deftere yazıyor.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {satirlar.length === 0 ? (
          <Olculemedi
            neden="Önerileri kimin yazdığı hiçbir kayıtta belirtilmemiş"
            teknik="defterdeki hiçbir satırda `source` alanı yok"
          />
        ) : (
          <div className="flex flex-col gap-3">
            <ChartContainer config={YAPI} className="aspect-auto h-44 w-full">
              <BarChart data={satirlar} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="ad"
                  tickLine={false}
                  axisLine={false}
                  width={124}
                  tickMargin={4}
                  className="text-xs"
                />
                <ChartTooltip cursor={false} content={<ChartTooltipContent hideIndicator />} />
                <Bar dataKey="n" radius={4} isAnimationActive={false}>
                  {satirlar.map((s) => (
                    // LLM kolları koyu, geri kalanı açık: ayrım anlam taşır (bir cümle
                    // ya bir modelden ya bir arama kolundan geldi) ve gri skalada
                    // yalnız TON farkıyla okunur.
                    <Cell key={s.ad} fill={s.ad.startsWith("hermes:") ? "var(--chart-5)" : "var(--chart-2)"} />
                  ))}
                </Bar>
              </BarChart>
            </ChartContainer>
            <p className="text-muted-foreground text-xs leading-5">
              {yazilmamis > 0
                ? `${bicimSayi(yazilmamis)} satırda \`source\` yazılmamış; bu grafiğin paydası DIŞINDA.`
                : "Defterdeki her satır kaynağını yazıyor — payda tam."}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function HukumDagilimi({ hipotezler }: { hipotezler: readonly Hipotez[] }) {
  const { satirlar, yazilmamis } = useMemo(() => sayimlar((h) => h.durum, hipotezler), [hipotezler]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="leading-none">Cümlenin sonu ne oldu?</CardTitle>
        <CardDescription>`status` alanı — öneri hangi kapıda kaldı, hangisinden geçti?</CardDescription>
      </CardHeader>
      <CardContent>
        {satirlar.length === 0 ? (
          <Olculemedi
            neden="Hiçbir öneri için verilen karar kaydedilmemiş"
            teknik="defterdeki hiçbir satırda `status` alanı yok"
          />
        ) : (
          <div className="flex flex-col gap-3">
            <ChartContainer config={YAPI} className="aspect-auto h-44 w-full">
              <BarChart data={satirlar} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="ad"
                  tickLine={false}
                  axisLine={false}
                  width={124}
                  tickMargin={4}
                  className="text-xs"
                  tickFormatter={(v: string) => DURUM_SOZLUGU[v]?.etiket ?? v}
                />
                <ChartTooltip cursor={false} content={<ChartTooltipContent hideIndicator />} />
                <Bar dataKey="n" radius={4} isAnimationActive={false}>
                  {satirlar.map((s) => (
                    <Cell
                      key={s.ad}
                      fill={
                        DURUM_SOZLUGU[s.ad]?.ton === "olumsuz"
                          ? "var(--destructive)"
                          : DURUM_SOZLUGU[s.ad]?.ton === "olumlu"
                            ? "var(--chart-5)"
                            : "var(--chart-2)"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ChartContainer>
            <p className="text-muted-foreground text-xs leading-5">
              {yazilmamis > 0
                ? `${bicimSayi(yazilmamis)} satırda \`status\` yazılmamış; bu grafiğin paydası DIŞINDA.`
                : "Defterdeki her satır bir hüküm taşıyor — payda tam."}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ---- KALİBRASYON --------------------------------------------------------- */

interface SacilimNoktasi {
  readonly tahmin: number;
  readonly gerceklesen: number;
  readonly degisken: string;
  readonly durum: string;
}

/** `/api/agent.calibration_scatter` — YALNIZ `realized_delta` YAZILMIŞ hipotezler
 *  (analytics.py::agent_view). Yani buradaki n, defterin n'i DEĞİLDİR. */
function sacilimOku(ham: unknown): { noktalar: readonly SacilimNoktasi[]; atlanan: number } {
  const noktalar: SacilimNoktasi[] = [];
  let atlanan = 0;
  for (const s of dizi(ham)) {
    const o = nesne(s);
    const p = say(o?.["predicted"]);
    const r = say(o?.["realized"]);
    if (o === null || p === null || r === null) {
      // Sessiz yutma DEĞİL: nokta çizilemeyeceği için sayılıyor ve ekranda yazılıyor.
      atlanan += 1;
      continue;
    }
    noktalar.push({
      tahmin: p,
      gerceklesen: r,
      degisken: metin(o["variable"]) ?? "(değişken yazılmamış)",
      durum: metin(o["status"]) ?? "(durum yazılmamış)",
    });
  }
  return { noktalar, atlanan };
}

const SACILIM_YAPI = {
  gerceklesen: { label: "gerçekleşen Δ" },
} satisfies ChartConfig;

export function KalibrasyonKarti({
  kalibrasyon,
  sacilim,
  defterN,
}: {
  kalibrasyon: Readonly<Record<string, unknown>> | null;
  sacilim: unknown;
  defterN: number;
}) {
  const { noktalar, atlanan } = useMemo(() => sacilimOku(sacilim), [sacilim]);
  const n = say(kalibrasyon?.["n"]);
  const brier = say(kalibrasyon?.["brier"]);
  const isabet = say(kalibrasyon?.["hit_rate"]);
  const not = metin(kalibrasyon?.["note"]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="leading-none">Tahmin tuttu mu?</CardTitle>
        <CardDescription>
          Ajan her öneriye bir Δskor tahmini yazar. Bu kart tahmini GERÇEKLEŞENLE karşılaştırır — ama
          yalnız sonucu yazılmış satırlarda.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-3 gap-3">
          <Olcut
            etiket="sonuçlanan"
            deger={n === null ? null : `${bicimSayi(n)} / ${bicimSayi(defterN)}`}
            neden="Kaç önerinin sonucu ölçüldüğü kaydedilmemiş"
            teknik="`/api/agent.calibration` gövdesinde `n` alanı yok"
          />
          <Olcut
            etiket="Brier"
            deger={brier === null ? null : bicimSayi(brier, 4)}
            neden={not ?? "sonucu yazılmış tahmin yok — Brier tanımsız (0 yazmak yalan olurdu)"}
          />
          <Olcut
            etiket="isabet"
            deger={isabet === null ? null : `%${bicimSayi(isabet * 100, 0)}`}
            neden={not ?? "sonucu yazılmış tahmin yok — isabet oranı tanımsız"}
          />
        </div>

        {noktalar.length === 0 ? (
          <Olculemedi
            neden={not ?? "Hiçbir önerinin sonucu henüz yazılmamış — çizilecek nokta yok"}
            teknik="`calibration_scatter` boş — hiçbir hipoteze `realized_delta` yazılmamış"
          />
        ) : (
          <div className="flex flex-col gap-2">
            <ChartContainer config={SACILIM_YAPI} className="aspect-auto h-52 w-full">
              <ScatterChart margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                <XAxis
                  type="number"
                  dataKey="tahmin"
                  name="tahmin Δ"
                  tickLine={false}
                  axisLine={false}
                  className="text-xs"
                  tickFormatter={(v: number) => bicimSayi(v, 3, true)}
                />
                <YAxis
                  type="number"
                  dataKey="gerceklesen"
                  name="gerçekleşen Δ"
                  tickLine={false}
                  axisLine={false}
                  width={56}
                  className="text-xs"
                  tickFormatter={(v: number) => bicimSayi(v, 3, true)}
                />
                <ZAxis range={[90, 90]} />
                {/* SIFIR ÇİZGİLERİ: bir nokta sağ-üst ya da sağ-alt çeyrekteyse
                    tahminin YÖNÜ tutmuş ya da tutmamış demektir. Çizgi olmadan
                    tek noktalı bir saçılım hiçbir şey söylemez. */}
                <ReferenceLine y={0} stroke="var(--border)" strokeDasharray="3 3" />
                <ReferenceLine x={0} stroke="var(--border)" strokeDasharray="3 3" />
                <ChartTooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  content={
                    <ChartTooltipContent
                      hideIndicator
                      labelKey="degisken"
                      formatter={(v) => (typeof v === "number" ? bicimSayi(v, 4, true) : String(v))}
                    />
                  }
                />
                <Scatter data={[...noktalar]} fill="var(--chart-5)" isAnimationActive={false} />
              </ScatterChart>
            </ChartContainer>
            <ul className="flex flex-col gap-1 border-t pt-2 text-xs">
              {noktalar.map((p) => (
                <li key={`${p.degisken}:${p.tahmin}:${p.gerceklesen}`} className="flex flex-wrap gap-x-2">
                  <code className="font-mono">{p.degisken}</code>
                  <span className="text-muted-foreground">
                    tahmin {bicimSayi(p.tahmin, 4, true)} → gerçekleşen {bicimSayi(p.gerceklesen, 4, true)}
                  </span>
                  <span
                    className={
                      Math.sign(p.tahmin) === Math.sign(p.gerceklesen)
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-red-600 dark:text-red-400"
                    }
                  >
                    {Math.sign(p.tahmin) === Math.sign(p.gerceklesen) ? "yön tuttu" : "yön ters"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-muted-foreground text-xs leading-5">
          PAYDA: saçılıma yalnız `realized_delta`sı YAZILMIŞ hipotezler girer (analytics.py::agent_view).
          Defterin geri kalanı "başarısız" değil, HENÜZ ÖLÇÜLMEMİŞTİR — ikisini aynı kovaya koymak
          öğrenme döngüsünü olduğundan kötü ya da iyi gösterirdi.
          {atlanan > 0
            ? ` ${bicimSayi(atlanan)} satır sayısal olmayan tahmin/gerçekleşen taşıdığı için çizilemedi.`
            : null}
        </p>
      </CardContent>
    </Card>
  );
}

function Olcut({
  etiket,
  deger,
  neden,
  teknik,
}: { etiket: string; deger: string | null; neden: string; teknik?: string }) {
  return (
    <div className="rounded-lg border bg-muted/20 px-3 py-2">
      <p className="text-muted-foreground text-xs">{etiket}</p>
      {deger === null ? (
        <div className="mt-0.5">
          <Olculemedi neden={neden} teknik={teknik} />
        </div>
      ) : (
        <p className="mt-0.5 font-medium text-lg tabular-nums leading-none">{deger}</p>
      )}
    </div>
  );
}

/* ---- ÜÇ KART BİR ARADA --------------------------------------------------- */

/** Ölçüm sekmesinin gövdesi. `govde` `/api/agent` yanıtının TAMAMI; buradan
 *  yalnız `calibration` ve `calibration_scatter` okunuyor — geri kalanı (karne,
 *  rollback, regresyon) Öğrenme yüzeyinin konusu ve orada çiziliyor. Aynı sayıyı
 *  iki yüzeyde ayrı hesaplamak, iki gerçek üretmenin en kolay yoludur. */
export function Grafikler({
  govde,
  hipotezler,
}: {
  govde: Readonly<Record<string, unknown>>;
  hipotezler: readonly Hipotez[];
}) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <KaynakDagilimi hipotezler={hipotezler} />
      <HukumDagilimi hipotezler={hipotezler} />
      <div className="lg:col-span-2">
        <KalibrasyonKarti
          kalibrasyon={nesne(govde["calibration"])}
          sacilim={govde["calibration_scatter"]}
          defterN={hipotezler.length}
        />
      </div>
    </div>
  );
}
