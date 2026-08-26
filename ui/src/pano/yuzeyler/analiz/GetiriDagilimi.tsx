"use client";

/* ============================================================================
   GETİRİ DAĞILIMI — R kovalarının histogramı
   ----------------------------------------------------------------------------
   KOVALARI PANO SEÇMİYOR, UÇ SEÇİYOR — ve bu bilinçli. Kapanmış işlemleri burada
   kendi kestiğim aralıklara bölseydim, eşikleri VERİYİ GÖRDÜKTEN SONRA seçmiş
   olurdum; bu deponun ölçüm disiplininde eşik sonradan değişmez (CLAUDE.md §3).
   `meridian/topviews.py` sınırları ÖNCEDEN ve gerekçesiyle sabitliyor: −1R tasarım
   sınırı (tam stop), 0 başabaş, sonrası tam sayı R katları, üçten sonrası tek
   kuyruk kovası. Histogram o kovaları OLDUĞU GİBİ çiziyor.

   KOVANIN İŞARETİ DE UÇTAN OKUNUYOR, ETİKET AYRIŞTIRARAK DEĞİL. `"-1..0R"` gibi
   bir dizgeyi ayrıştırmak, etiket biçimi değiştiği gün rengi sessizce ters
   çevirirdi. Uç şunu söylüyor (topviews.py, `r_kovasi` paydası): kova R'nin
   İŞARETİNE göre bölündüğü için pozitif kovada brüt zarar, negatif kovada brüt
   kâr YAPISAL olarak sıfırdır. Renk bu yapısal gerçeğe bakıyor.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, Cell, LabelList, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

import type { Durum } from "../../veri";
import { Deger, Kapi, Olculemedi, rKati, sayi, yuzde } from "./ortak";
import type { FacetBloku, FacetSatiri, TopviewsGovdesi } from "./tipler";

const DAGILIM_CONFIG = {
  n: { label: "İşlem", color: "var(--chart-2)" },
  kaybeden: { label: "Kaybeden aralık", color: "var(--destructive)" },
  kazanan: { label: "Kazanan aralık", color: "var(--chart-2)" },
} satisfies ChartConfig;

interface KovaNoktasi {
  readonly kova: string;
  readonly n: number;
  readonly kayip: boolean | null;
  readonly satir: FacetSatiri;
}

/** Kovanın işareti: brüt kâr yapısal olarak sıfırsa KAYIP kovası (bkz. dosya başı). */
function kovaKayipMi(s: FacetSatiri): boolean | null {
  const kazanc = s.gross_win;
  const zarar = s.gross_loss;
  if (typeof kazanc !== "number" || typeof zarar !== "number") return null; // R yok → renk uydurulmaz
  if (kazanc === 0 && zarar !== 0) return true;
  if (zarar === 0 && kazanc !== 0) return false;
  return null; // ikisi de dolu (ya da ikisi de sıfır) → kova saf değil, nötr çizilir
}

export function GetiriDagilimi({ top }: { top: Durum<TopviewsGovdesi> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Getiri dağılımı</CardTitle>
        <CardDescription>Kapanmış işlemler R aralıklarına göre — aralık sınırları uçta ÖNCEDEN sabit.</CardDescription>
      </CardHeader>
      <CardContent>
        <Kapi durum={top} ad="/api/topviews" yukseklik="h-56">
          {(v) => <DagilimGovdesi veri={v} />}
        </Kapi>
      </CardContent>
    </Card>
  );
}

function DagilimGovdesi({ veri }: { veri: TopviewsGovdesi }) {
  const blok: FacetBloku | undefined = veri.aileler?.["SONUC"]?.["r_kovasi"];
  const kaynak = veri.facet_kaynaklari?.["r_kovasi"];

  if (!blok) {
    return (
      <Olculemedi
        neden="Getiri dağılımı bu turda hiç üretilmedi"
        teknik="/api/topviews yükünde `aileler.SONUC.r_kovasi` bloğu yok"
      />
    );
  }
  if (!blok.satirlar) {
    return (
      <Olculemedi
        neden={
          blok.olculemedi_neden ??
          "Getiri dağılımı ölçülemedi ve nedeni de yazılmadı — bu, kayıt yok demek değil."
        }
        teknik="r_kovasi facet'i `satirlar: null` döndürdü ama nedenini yazmadı"
      />
    );
  }

  const noktalar: KovaNoktasi[] = blok.satirlar
    .filter((s): s is FacetSatiri & { deger: string; n: number } => typeof s.deger === "string" && typeof s.n === "number")
    .map((s) => ({ kova: s.deger, n: s.n, kayip: kovaKayipMi(s), satir: s }));

  const toplam = noktalar.reduce((t, p) => t + p.n, 0);

  if (noktalar.length === 0) {
    return (
      <Olculemedi
        neden="Çizilecek getiri aralığı yok"
        teknik="r_kovasi satırlarının hiçbiri hem `deger` hem `n` taşımıyor"
      />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <ChartContainer config={DAGILIM_CONFIG} className="aspect-auto h-64 w-full">
        <BarChart data={noktalar} margin={{ bottom: 0, left: 0, right: 8, top: 16 }}>
          <CartesianGrid vertical={false} />
          <XAxis axisLine={false} dataKey="aralık" tickLine={false} tickMargin={10} />
          <YAxis axisLine={false} tickLine={false} tickMargin={8} width={40} allowDecimals={false} />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                className="w-56"
                labelFormatter={(_etiket, yuk) => {
                  const ilk = Array.isArray(yuk) ? yuk[0] : undefined;
                  const p = (ilk as { payload?: KovaNoktasi } | undefined)?.payload;
                  if (!p) return "aralık okunamadı";
                  const pay = toplam > 0 ? ` · ${yuzde(p.n / toplam, 1) ?? ""}` : "";
                  return `${p.kova}${pay}`;
                }}
                formatter={(deger) => (
                  <span className="text-muted-foreground">
                    işlem <span className="ml-1 font-medium text-foreground tabular-nums">{String(deger)}</span>
                  </span>
                )}
              />
            }
          />
          <Bar isAnimationActive={false} dataKey="n" radius={[4, 4, 0, 0]}>
            <LabelList dataKey="n" position="top" className="fill-muted-foreground" fontSize={11} />
            {noktalar.map((p) => (
              <Cell
                key={p.kova}
                fill={p.kayip === null ? "var(--muted-foreground)" : p.kayip ? "var(--color-kaybeden)" : "var(--color-kazanan)"}
                fillOpacity={p.kayip === null ? 0.45 : 0.9}
              />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] text-sm">
          <thead>
            <tr className="border-border/60 border-b text-muted-foreground text-xs">
              <th className="py-2 pr-3 text-left font-normal">Aralık</th>
              <th className="py-2 pr-3 text-right font-normal">İşlem</th>
              <th className="py-2 pr-3 text-right font-normal">Pay</th>
              <th className="py-2 pr-3 text-right font-normal">Toplam R</th>
              <th className="py-2 text-right font-normal">Kazanma</th>
            </tr>
          </thead>
          <tbody>
            {noktalar.map((p) => (
              <tr key={p.kova} className="border-border/40 border-b last:border-0">
                <td className="py-2 pr-3 font-medium">{p.kova}</td>
                <td className="py-2 pr-3 text-right tabular-nums">{sayi(p.n, 0)}</td>
                <td className="py-2 pr-3 text-right text-muted-foreground tabular-nums">
                  <Deger
                    metin={toplam > 0 ? yuzde(p.n / toplam, 1) : null}
                    neden="Kovaların işlem toplamı sıfır — pay hesaplanamadı"
                  />
                </td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  <Deger
                    metin={p.satir.sum_r === null || p.satir.sum_r === undefined ? null : rKati(p.satir.sum_r)}
                    neden="Bu kovanın toplam R'si ölçülemedi — sıfır değil, ölçülmedi"
                    teknik={`bu kovadaki ${p.satir.r_n ?? 0} satır r_multiple taşıyor`}
                  />
                </td>
                <td className="py-2 text-right tabular-nums">
                  <Deger
                    metin={p.satir.kazanma === null || p.satir.kazanma === undefined ? null : yuzde(p.satir.kazanma, 1)}
                    neden="Kovanın R taşıyan satırı yok — kazanma oranı paydasız"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-2 text-muted-foreground text-xs leading-relaxed">
        {typeof blok.etiketsiz_n === "number" && blok.etiketsiz_n > 0 ? (
          <p>
            <span className="font-medium text-foreground">Kovaya girmeyen {blok.etiketsiz_n} satır:</span>{" "}
            {blok.etiketsiz_neden ?? "uç nedeni yazmadı."} Bu satırlar histogramda YOK — sıfır kovasına
            itilmediler.
          </p>
        ) : null}
        {typeof kaynak?.kaynak === "string" ? (
          <p>
            Kaynak: {kaynak.kaynak}
            {typeof kaynak.pencere === "string" ? ` · pencere ${kaynak.pencere}` : ""}
            {typeof kaynak.n === "number" ? ` · taranan ${kaynak.n} satır` : ""}
          </p>
        ) : (
          <p>Facet kaynağı beyan edilmedi — bu histogramın hangi pencereyi saydığı ölçülemedi.</p>
        )}
        {typeof kaynak?.payda === "string" ? <p>{kaynak.payda}</p> : null}
      </div>
    </div>
  );
}
