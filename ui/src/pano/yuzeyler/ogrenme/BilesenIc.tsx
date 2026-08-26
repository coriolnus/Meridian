"use client";

/* ============================================================================
   BİLEŞEN İÇİ — "hangi bileşen skoru gerçekten taşıyor?"
   ----------------------------------------------------------------------------
   IC = bileşen değeri ile ileri getirinin SIRALAMA korelasyonu (Spearman). Sıfıra
   yakın bir IC "bu bileşen işe yaramıyor" demektir; ölçülemeyen bir hücre ise
   "bilmiyoruz" — ve bu ikisi grafikte AYNI YÜKSEKLİĞE düşerdi. Bu yüzden ölçülemeyen
   hücre çizilmez, tabloda `neden`iyle satır olarak durur.

   KATMAN SEÇİMİ BİR SÜS DEĞİL, PAYDA DEĞİŞİMİDİR. `gercek` katman alınmış işlemleri,
   `cf` katman ALINMAMIŞ hipotetik girişleri sayar — farklı popülasyonlar. cf'nin n'i
   yirmi kat büyük olduğu için "anlamlı hücre" sayısı da doğal olarak büyük çıkar;
   ikisini yan yana koyup "cf daha iyi" demek payda karşılaştırmasıdır, kanıt değil.
   Uç bunu kendi cümlesiyle söylüyor (`cf_katman_gerekce`) ve o cümle ekranda duruyor.

   GÜVEN ARALIĞI HER HÜCREDE VAR ve tabloda yazılı: IC 0,23 ile CI [0,03; 0,42] aynı
   satırda okunmazsa nokta tahmin bir kesinlik iddiası gibi okunur.
   ============================================================================ */
import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, LabelList, ReferenceLine, XAxis, YAxis } from "recharts";
import { Boxes } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";
import { Beyan, BolumKarti, Deger, Kapi, Kutu, Olculemedi, OlculemediHucre, Satir, sayi } from "./ortak";
import type { BilesenIcBelgesi, IcHucresi, KucultulmusIc, TeshisGovdesi } from "./tipler";

const KATMAN_ETIKETI: Readonly<Record<string, string>> = {
  gercek: "Gerçek (alınmış işlemler)",
  cf: "Alınmamış işlem (alınmamış girişler)",
  havuz: "Havuz (ikisinin birleşimi)",
};

/** Grafikte kullanılacak beş jeton; ufuk sayısı beşi aşarsa başa sarar (renk
 *  tükendiğinde çıplak hex yazmak yerine tekrar etmek — jeton sözleşmesi korunur). */
const UFUK_RENKLERI = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"] as const;

interface GrafikSatiri {
  readonly bilesen: string;
  readonly [anahtar: string]: string | number | null;
}

export function BilesenIc({ teshis }: { teshis: Durum<TeshisGovdesi> }) {
  return (
    <BolumKarti kimlik="bilesenic" baslik="Bileşen içi" soru="Hangi bileşen skoru taşıyor?" ikon={Boxes}>
      <Kapi durum={teshis} ad="/api/diagnostics" yukseklik="h-72">
        {(v) => <Govde doc={v.mlops?.component_ic ?? null} kucuk={v.mlops?.shrunk_component_ic} />}
      </Kapi>
    </BolumKarti>
  );
}

function Govde({ doc, kucuk }: { doc: BilesenIcBelgesi | null; kucuk: KucultulmusIc | undefined }) {
  const katmanlar = doc?.layers ?? [];
  const ilkKatman = katmanlar[0] ?? "gercek";
  const [katman, setKatman] = useState<string>("gercek");
  const secili = katmanlar.includes(katman) ? katman : ilkKatman;

  const ufuklar = useMemo(() => (doc?.horizons ?? []).filter((h) => typeof h === "number"), [doc]);
  const bilesenler = useMemo(() => doc?.components ?? [], [doc]);
  const tablo = doc?.tablo?.[secili];

  const config: ChartConfig = useMemo(() => {
    const c: ChartConfig = {};
    ufuklar.forEach((h, i) => {
      c[`h${h}`] = { label: `${h} bar`, color: UFUK_RENKLERI[i % UFUK_RENKLERI.length] ?? "var(--chart-1)" };
    });
    return c;
  }, [ufuklar]);

  const satirlar: GrafikSatiri[] = useMemo(() => {
    if (!tablo) return [];
    return bilesenler.map((b) => {
      const satir: Record<string, string | number | null> = { bilesen: b };
      ufuklar.forEach((h) => {
        const hucre: IcHucresi | undefined = tablo[b]?.[String(h)];
        satir[`h${h}`] = typeof hucre?.ic === "number" && Number.isFinite(hucre.ic) ? hucre.ic : null;
      });
      return satir as GrafikSatiri;
    });
  }, [tablo, bilesenler, ufuklar]);

  if (!doc) {
    return (
      <Olculemedi
        neden="Bileşenlerin skora katkısı bu turda hiç ölçülmedi — 'hepsi sıfır' demek değil"
        teknik="/api/diagnostics yükünde `mlops.component_ic` YOK (dosya hiç üretilmemiş)"
      />
    );
  }
  if (ufuklar.length === 0 || bilesenler.length === 0) {
    return (
      <Olculemedi
        neden="Çizilecek bileşen ya da vade bulunamadı"
        teknik="`component_ic` belgesi var ama `horizons`/`components` eksenlerinden biri boş"
      />
    );
  }

  const olculenHucre = satirlar.reduce(
    (t, s) => t + ufuklar.filter((h) => typeof s[`h${h}`] === "number").length,
    0,
  );
  const toplamHucre = satirlar.length * ufuklar.length;

  return (
    <div className="flex flex-col gap-6">
      {/* ---- HÜKÜM ---- */}
      <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
        <p className="text-muted-foreground text-xs">Uçtan gelen karar</p>
        <p className="mt-1 text-sm leading-relaxed">
          {doc.verdict ?? (
            <span className="text-muted-foreground italic">
              ölçülemedi — `component_ic.verdict` yükte yok; en güçlü bileşen hükmü bu turda yazılmadı.
            </span>
          )}
        </p>
        {doc.en_guclu ? (
          <p className="mt-2 text-muted-foreground text-xs">
            En güçlü hücre: <span className="font-medium text-foreground">{doc.en_guclu.bilesen ?? "?"}</span> ·{" "}
            {doc.en_guclu.horizon ?? "?"} bar · IC {sayi(doc.en_guclu.ic, 4) ?? "ölçülemedi"} (n{" "}
            {sayi(doc.en_guclu.n, 0) ?? "?"}) · {doc.en_guclu.anlamli ? "ANLAMLI" : "anlamlı değil"}
          </p>
        ) : null}
      </div>

      {/* ---- KATMAN SEÇİMİ ---- */}
      {katmanlar.length > 1 ? (
        <div className="flex flex-wrap items-center gap-3">
          <Tabs value={secili} onValueChange={setKatman}>
            <TabsList>
              {katmanlar.map((k) => (
                <TabsTrigger key={k} value={k}>
                  {KATMAN_ETIKETI[k] ?? k}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <span className="text-muted-foreground text-xs tabular-nums">
            gözlem: {sayi(doc.n_gozlem?.[secili], 0) ?? "ölçülemedi"} · anlamlı hücre:{" "}
            {sayi(doc.anlamli_sayim?.[secili], 0) ?? "ölçülemedi"}
          </span>
        </div>
      ) : null}

      {/* ---- GRAFİK ---- */}
      {olculenHucre === 0 ? (
        <Olculemedi
          neden={`"${KATMAN_ETIKETI[secili] ?? secili}" katmanında ${toplamHucre} hücrenin hiçbiri ölçülememiş — bu katman hiç hesaplanmamış (sıfır katkı değil)`}
          teknik="hiçbir hücrede `ic` sayısı yok"
        />
      ) : (
        <ChartContainer config={config} className="aspect-auto h-72 w-full">
          <BarChart data={satirlar} margin={{ bottom: 0, left: 0, right: 8, top: 16 }}>
            <CartesianGrid vertical={false} />
            <XAxis axisLine={false} dataKey="bilesen" tickLine={false} tickMargin={10} />
            <YAxis axisLine={false} tickLine={false} tickMargin={8} width={52} tickFormatter={(v) => sayi(v, 2) ?? ""} />
            {/* SIFIR ÇİZGİSİ ZORUNLU: IC işaretli bir büyüklük ve eksi bir IC "ters yönde
                bilgi" demek. Çizgisiz bir grafikte eksi çubuklar yalnız "kısa" görünürdü. */}
            <ReferenceLine y={0} stroke="var(--border)" />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent className="w-52" formatter={(deger, ad) => (
                <span className="text-muted-foreground">
                  {String(ad)} <span className="ml-1 font-medium text-foreground tabular-nums">{sayi(deger, 4) ?? "—"}</span>
                </span>
              )} />}
            />
            <ChartLegend content={<ChartLegendContent />} />
            {ufuklar.map((h) => (
              <Bar isAnimationActive={false} key={h} dataKey={`h${h}`} fill={`var(--color-h${h})`} radius={2} fillOpacity={0.9}>
                <LabelList
                  dataKey={`h${h}`}
                  position="top"
                  className="fill-muted-foreground"
                  fontSize={9}
                  formatter={(v: unknown) => sayi(v, 2) ?? ""}
                />
              </Bar>
            ))}
          </BarChart>
        </ChartContainer>
      )}
      <Beyan>
        Çizilen hücre: {olculenHucre} / {toplamHucre}. Çizilmeyenler SIFIR değil ÖLÇÜLEMEDİ'dir ve
        nedenleri aşağıdaki tabloda satır satır duruyor.
      </Beyan>

      {/* ---- TABLO ---- */}
      <div className="overflow-x-auto">
        <Table className="min-w-[42rem]">
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-9">Bileşen</TableHead>
              {ufuklar.map((h) => (
                <TableHead key={h} className="h-9 text-right">
                  {h} bar
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {bilesenler.map((b) => (
              <TableRow key={b} className="border-border/50">
                <TableCell className="py-2.5 font-medium">{b}</TableCell>
                {ufuklar.map((h) => {
                  const hucre: IcHucresi | undefined = tablo?.[b]?.[String(h)];
                  if (!hucre) {
                    return (
                      <TableCell key={h} className="py-2.5 text-right">
                        <OlculemediHucre
                          neden={`Bu bileşen ${h} barlık vadede hiç hesaplanmamış`}
                          teknik={`tabloda ${b}×${h} hücresi yok`}
                        />
                      </TableCell>
                    );
                  }
                  if (typeof hucre.ic !== "number") {
                    return (
                      <TableCell key={h} className="py-2.5 text-right">
                        <OlculemediHucre
                          neden={hucre.neden ?? `Bu bileşenin ${h} barlık vadedeki katkısı ölçülemedi`}
                          teknik={`${b}×${h}: \`ic\` sayı değil (n=${hucre.n ?? "?"})`}
                        />
                      </TableCell>
                    );
                  }
                  return (
                    <TableCell key={h} className="py-2.5 text-right">
                      <div className="flex flex-col items-end gap-0.5">
                        <span className={cn("tabular-nums", hucre.anlamli ? "font-medium" : "text-muted-foreground")}>
                          {sayi(hucre.ic, 4)}
                          {hucre.anlamli ? (
                            <Badge variant="outline" className="ml-1.5 border-emerald-500/40 text-emerald-700 dark:text-emerald-300">
                              anlamlı
                            </Badge>
                          ) : null}
                        </span>
                        <span className="text-muted-foreground text-xs tabular-nums">
                          n {sayi(hucre.n, 0) ?? "?"} · CI [{sayi(hucre.ci?.lo, 3) ?? "?"}; {sayi(hucre.ci?.hi, 3) ?? "?"}]
                        </span>
                      </div>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* ---- KÜÇÜLTME ---- */}
      <Kutu
        baslik="Küçültülmüş IC (empirical Bayes)"
        aciklama="Küçük örneklemli hücreler ortalamaya çekilir. GÖSTERGEDİR — hiçbir kapı tabanına girmez."
      >
        {!kucuk ? (
          <Olculemedi
            neden="Küçük örneklem düzeltmesi bu turda hiç hesaplanmadı"
            teknik="`mlops.shrunk_component_ic` yükte yok"
          />
        ) : (
          <div className="flex flex-col">
            <Satir etiket="Küçültüldü mü?">
              <span>{kucuk.kucultuldu === undefined ? "ölçülemedi" : kucuk.kucultuldu ? "evet" : "hayır"}</span>
            </Satir>
            <Satir etiket="Hücre sayısı">
              <Deger
                metin={sayi(kucuk.n_hucre, 0)}
                neden="Kaç hücrenin düzeltildiği bildirilmedi"
                teknik="`n_hucre` yükte yok"
              />
            </Satir>
            {kucuk.neden ? (
              <Satir etiket="Neden">
                <span className="text-xs">{kucuk.neden}</span>
              </Satir>
            ) : null}
            {kucuk.tablo_ici_eb?.var === false ? (
              <Satir etiket="Tablo içi EB bloğu">
                <span className="text-xs text-muted-foreground">{kucuk.tablo_ici_eb.neden ?? "yok (neden yazılmamış)"}</span>
              </Satir>
            ) : null}
            {kucuk.kaynak ? <Beyan>{kucuk.kaynak}</Beyan> : null}
            {kucuk.rol ? <Beyan>{kucuk.rol}</Beyan> : null}
          </div>
        )}
      </Kutu>

      {doc.getiri_tanimi ? <Beyan>Getiri tanımı: {doc.getiri_tanimi}</Beyan> : null}
      {doc.ci_yontem ? <Beyan>CI yöntemi: {doc.ci_yontem}</Beyan> : null}
      {doc.ci_varsayim ? <Beyan>CI varsayımı: {doc.ci_varsayim}</Beyan> : null}
      {doc.cf_katman_gerekce ? <Beyan>{doc.cf_katman_gerekce}</Beyan> : null}
    </div>
  );
}
