"use client";

/* ============================================================================
   PARA EĞRİSİ — sermaye serisi + tepe-altı düşüş, ve serinin KENDİ BEYANI
   ----------------------------------------------------------------------------
   EKSEN DİZİNDİR, TARİH DEĞİL. `state/equity_curve.json` seans sonunda günde tek
   nokta ekliyor; hafta sonları ve duran günler seride HİÇ YOK. Zaman eksenine
   çizersek boşluklar düz bir çizgi olarak görünür ve okuyucu "o günlerde sermaye
   sabitti" diye okur — oysa o günler ölçülmedi. Uç da boşlukları TAM BU YÜZDEN
   dizin (`i`) ile işaretliyor (api.py:2537: "seri dizin ekseninde çizilir, yani
   boşluk grafikte normal bir adım gibi görünür; işaret olmadan delik GÖRÜNMEZ").
   Dikey işaretler o deliği geri koyuyor.

   DÜŞÜŞ SERİSİ TARAYICIDA TÜRETİLİR ve bu ekranda AÇIKÇA yazıyor. `score_detail.
   max_drawdown` ile AYNI SAYI DEĞİLDİR: o, KAPANMIŞ İŞLEM eğrisinden hesaplanır
   (score.py:121) ve gerekirse günlük M2M eğrisinin daha kötüsüyle değiştirilir;
   buradaki seri ise `equity_curve.json` noktalarının kendi tepe-altı yüzdesidir.
   İki sayıyı tek etiketle göstermek, farklı iki ölçümü aynıymış gibi okutmak
   olurdu — ikisi de basılıyor ve farkın nereden geldiği yazıyor.
   ============================================================================ */
import { useMemo, type ReactNode } from "react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

import type { Durum } from "../../veri";
import { Deger, Kapi, Olculemedi, para, pnlRengi, rKati, sayi, yuzde } from "./ortak";
import type { EgriBeyani, PerformansGovdesi } from "./tipler";

interface EgriNoktasi {
  /** HAM `points` dizini — uçtan gelen boşluk/reset/tohum işaretleri de bu dizini kullanır. */
  readonly i: number;
  readonly tarih: string;
  readonly sermaye: number;
  /** Tepe-altı yüzde (negatif ya da 0). Tepe pozitif değilse `null` — hesap tanımsız. */
  readonly dusus: number | null;
}

const EGRI_CONFIG = {
  sermaye: { label: "Sermaye", color: "var(--chart-2)" },
} satisfies ChartConfig;

const DUSUS_CONFIG = {
  dusus: { label: "Tepe altı", color: "var(--destructive)" },
} satisfies ChartConfig;

function noktalariCoz(ham: readonly unknown[] | undefined): {
  noktalar: EgriNoktasi[];
  atlanan: number;
  enKotuDusus: number | null;
} {
  const noktalar: EgriNoktasi[] = [];
  let atlanan = 0;
  let tepe = Number.NEGATIVE_INFINITY;
  let enKotu: number | null = null;

  (ham ?? []).forEach((p, i) => {
    // NOKTA ŞEKLİ GARANTİ DEĞİL: dosya HAM okunuyor (api.py `store.read_json`), uç
    // biçim doğrulaması yapmıyor. Çözülemeyen nokta ATLANIR VE SAYILIR — 0 sermaye
    // olarak seriye sokmak eğriyi tabana çakardı ve bu görsel bir yalan olurdu.
    if (!Array.isArray(p) || p.length < 2) {
      atlanan += 1;
      return;
    }
    const tarih: unknown = p[0];
    const deger: unknown = p[1];
    if (typeof tarih !== "string" || typeof deger !== "number" || !Number.isFinite(deger)) {
      atlanan += 1;
      return;
    }
    if (deger > tepe) tepe = deger;
    const dusus = tepe > 0 ? (deger / tepe - 1) * 100 : null;
    if (dusus !== null && (enKotu === null || dusus < enKotu)) enKotu = dusus;
    noktalar.push({ i, tarih, sermaye: deger, dusus });
  });

  return { noktalar, atlanan, enKotuDusus: enKotu };
}

/** Eksende en çok altı etiket — daha fazlası dar ekranda üst üste biner. */
function eksenIsaretleri(noktalar: readonly EgriNoktasi[]): number[] {
  const n = noktalar.length;
  if (n === 0) return [];
  const adet = Math.min(6, n);
  const isaretler: number[] = [];
  for (let k = 0; k < adet; k += 1) {
    const idx = adet === 1 ? 0 : Math.round((k * (n - 1)) / (adet - 1));
    const nokta = noktalar[idx];
    if (nokta && !isaretler.includes(nokta.i)) isaretler.push(nokta.i);
  }
  return isaretler;
}

function BeyanSatiri({ etiket, children }: { etiket: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-muted-foreground text-xs">{etiket}</dt>
      <dd className="text-sm tabular-nums">{children}</dd>
    </div>
  );
}

function EgriBeyaniBlogu({ beyani, atlanan }: { beyani: EgriBeyani | undefined; atlanan: number }) {
  if (!beyani) {
    return (
      <Olculemedi neden="Serinin penceresi, delikleri ve başlangıç sınırı bu turda ölçülemedi" teknik="/api/performance yükünde equity_curve_beyani bloğu yok" />
    );
  }
  const ilk = beyani.ilk ?? null;
  const son = beyani.son ?? null;
  const enBuyuk = beyani.en_buyuk_bosluk ?? null;
  const tohum = beyani.tohum_siniri ?? null;

  return (
    <div className="flex flex-col gap-4">
      <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-6">
        <BeyanSatiri etiket="Nokta">
          <Deger metin={sayi(beyani.n_nokta, 0)} neden="Serinin kaç noktadan oluştuğu bildirilmedi" teknik="beyanda n_nokta yok" />
        </BeyanSatiri>
        <BeyanSatiri etiket="İlk nokta">
          <Deger
            metin={ilk ? `${ilk[0]} · ${para(ilk[1]) ?? "sermaye okunamadı"}` : null}
            neden="Seride okunabilen tek bir nokta bile yok" teknik="beyanda `ilk` null — çözülebilen [tarih, sermaye] çifti yok"
          />
        </BeyanSatiri>
        <BeyanSatiri etiket="Son nokta">
          <Deger
            metin={son ? `${son[0]} · ${para(son[1]) ?? "sermaye okunamadı"}` : null}
            neden="Seride okunabilen tek bir nokta bile yok" teknik="beyanda `son` null — çözülebilen [tarih, sermaye] çifti yok"
          />
        </BeyanSatiri>
        <BeyanSatiri etiket="Kitabın son seansı">
          <Deger
            metin={typeof beyani.son_seans === "string" ? beyani.son_seans : null}
            neden="Eğrinin geride kalıp kalmadığı kıyaslanamadı" teknik="portfolio.last_date okunamadı"
          />
        </BeyanSatiri>
        <BeyanSatiri etiket="Gecikme">
          <Deger
            metin={typeof beyani.gecikme_gun === "number" ? `${sayi(beyani.gecikme_gun, 0)} gün` : null}
            neden="Eğrinin son noktası kitabın son seansıyla kıyaslanamadı — sıfır gün değil" teknik="gecikme_gun null (biri yok ya da biçimsiz)"
          />
        </BeyanSatiri>
        <BeyanSatiri etiket="Boşluk">
          <Deger
            metin={
              typeof beyani.n_bosluk === "number"
                ? `${sayi(beyani.n_bosluk, 0)}${enBuyuk?.gun === undefined ? "" : ` · en büyük ${enBuyuk.gun} gün`}`
                : null
            }
            neden="Takvim delikleri bu turda taranmadı" teknik="beyanda n_bosluk yok"
          />
        </BeyanSatiri>
      </dl>

      {atlanan > 0 || (beyani.okunamayan_nokta ?? 0) > 0 ? (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-amber-700 text-xs leading-relaxed dark:text-amber-300">
          Çözülemeyen nokta: grafik {atlanan} noktayı atladı, uç kendi taramasında{" "}
          {sayi(beyani.okunamayan_nokta, 0) ?? "ölçülemedi"} tanesini sayamadı olarak işaretledi. Atlanan noktalar seriye SIFIR
          olarak girmedi — çizilmedi.
        </p>
      ) : null}

      {beyani.bosluk_kirpildi === true ? (
        <p className="text-muted-foreground text-xs leading-relaxed">
          Boşluk listesi kırpıldı: uç en çok {sayi(beyani.bosluk_tavani, 0) ?? "ölçülemedi"} boşluk döndürüyor ve EN YENİLERİ
          tutuyor. Grafikteki dikey işaretler bu kırpılmış listeden geliyor — daha eski boşluklar seride VAR ama
          işaretsiz.
        </p>
      ) : null}

      {tohum ? (
        <p className="text-muted-foreground text-xs leading-relaxed">
          <span className="font-medium text-foreground">Başlangıç verisi sınırı:</span>{" "}
          {typeof tohum.replay_end === "string" ? tohum.replay_end : "ölçülemedi"}
          {typeof tohum.kaynak === "string" ? ` · kaynak ${tohum.kaynak}` : ""}
          {typeof tohum.guven === "string" ? ` · güven ${tohum.guven}` : ""}
          {typeof tohum.konum_neden === "string" ? ` — ${tohum.konum_neden}` : ""}
        </p>
      ) : (
        <p className="text-muted-foreground text-xs leading-relaxed">
          Başlangıç verisi sınırı ölçülemedi — serinin neresinde replay başlangıç verisinin bittiği ve canlı kağıdın başladığı
          işaretlenemiyor.
        </p>
      )}

      {typeof beyani.beyan === "string" ? (
        <p className="text-muted-foreground text-xs leading-relaxed">{beyani.beyan}</p>
      ) : null}
    </div>
  );
}

export function ParaEgrisi({ perf }: { perf: Durum<PerformansGovdesi> }) {
  return (
    <Kapi durum={perf} ad="/api/performance" yukseklik="h-72">
      {(v) => <EgriGovdesi veri={v} />}
    </Kapi>
  );
}

function EgriGovdesi({ veri }: { veri: PerformansGovdesi }) {
  const ham = veri.equity_curve?.points;
  const { noktalar, atlanan, enKotuDusus } = useMemo(() => noktalariCoz(ham), [ham]);
  const isaretler = useMemo(() => eksenIsaretleri(noktalar), [noktalar]);
  const tarihEsleme = useMemo(() => {
    const m = new Map<number, string>();
    noktalar.forEach((p) => m.set(p.i, p.tarih));
    return m;
  }, [noktalar]);

  const beyani = veri.equity_curve_beyani;
  // KONUMLANDIRILAMAYAN İŞARET ÇİZİLMEZ AMA YOK SAYILMAZ: uç `i: null` + `konum_neden`
  // döndürebiliyor (damga yolu bir eğri noktasına denk gelmeyebilir). Böyle bir işareti
  // 0 dizinine koymak onu serinin başına yapıştırıp yalan bir konum uydurmak olurdu;
  // sayıları aşağıdaki işaret sözlüğünde "kaç tanesi konumlandırıldı" diye yazıyor.
  const boslukIndeksleri = (beyani?.bosluklar ?? [])
    .map((b) => b.i)
    .filter((i): i is number => typeof i === "number");
  const resetIndeksleri = (beyani?.reset_isaretleri ?? [])
    .map((r) => r.i)
    .filter((i): i is number => typeof i === "number");
  const tohumIndeks = typeof beyani?.tohum_siniri?.i === "number" ? beyani.tohum_siniri.i : null;

  const ilkI = noktalar[0]?.i ?? 0;
  const sonI = noktalar[noktalar.length - 1]?.i ?? 0;
  const sd = veri.score_detail;

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Sermaye eğrisi</CardTitle>
          <CardDescription>
            {noktalar.length > 0
              ? `${noktalar.length} seans noktası · yatay eksen SERİ DİZİNİDİR (takvim değil), boşluklar dikey işaretle konur.`
              : "Çizilecek nokta yok."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {noktalar.length === 0 ? (
            <Olculemedi
              neden={`Seride çizilebilecek tek bir nokta yok — ${atlanan} kayıt okunamadı`}
              teknik={'equity_curve.points içinde çözülebilen [tarih, sermaye] çifti yok; boş bir eksen çizmek "sermaye sıfır" derdi'}
            />
          ) : (
            <>
              <ChartContainer config={EGRI_CONFIG} className="aspect-auto h-72 w-full">
                <AreaChart data={noktalar} margin={{ bottom: 0, left: 0, right: 8, top: 8 }}>
                  <defs>
                    <linearGradient id="analiz-sermaye-dolgu" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-sermaye)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--color-sermaye)" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} />
                  <XAxis
                    axisLine={false}
                    dataKey="i"
                    domain={[ilkI, sonI]}
                    tickLine={false}
                    tickMargin={10}
                    ticks={isaretler}
                    tickFormatter={(deger: number) => tarihEsleme.get(deger) ?? ""}
                    type="number"
                  />
                  <YAxis
                    axisLine={false}
                    domain={["auto", "auto"]}
                    tickLine={false}
                    tickMargin={8}
                    width={64}
                    tickFormatter={(deger: number) => para(deger) ?? ""}
                  />
                  <ChartTooltip
                    cursor={{ stroke: "var(--border)", strokeDasharray: "4 4" }}
                    content={
                      <ChartTooltipContent
                        className="w-48"
                        labelFormatter={(_etiket, yuk) => {
                          const ilk = Array.isArray(yuk) ? yuk[0] : undefined;
                          const p = (ilk as { payload?: EgriNoktasi } | undefined)?.payload;
                          return p?.tarih ?? "tarih okunamadı";
                        }}
                      />
                    }
                  />
                  {boslukIndeksleri.map((i) => (
                    <ReferenceLine
                      key={`bosluk-${i}`}
                      x={i}
                      stroke="var(--muted-foreground)"
                      strokeDasharray="2 4"
                      strokeWidth={1}
                    />
                  ))}
                  {resetIndeksleri.map((i) => (
                    <ReferenceLine
                      key={`reset-${i}`}
                      x={i}
                      stroke="var(--destructive)"
                      strokeDasharray="6 3"
                      strokeWidth={1.5}
                    />
                  ))}
                  {tohumIndeks === null ? null : (
                    <ReferenceLine x={tohumIndeks} stroke="var(--primary)" strokeWidth={1.5} />
                  )}
                  <Area isAnimationActive={false}
                    dataKey="sermaye"
                    fill="url(#analiz-sermaye-dolgu)"
                    stroke="var(--color-sermaye)"
                    strokeWidth={2}
                    type="linear"
                    dot={false}
                    activeDot={{ r: 3 }}
                  />
                </AreaChart>
              </ChartContainer>

              {/* İŞARET SÖZLÜĞÜ — dikey çizgiler grafikte etiketsiz duruyor (aynı anda
                  onlarca boşluk olabiliyor ve etiketler üst üste binerdi); anlamları burada. */}
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-muted-foreground text-xs">
                <span className="flex items-center gap-2">
                  <span className="inline-block h-3 w-px border-muted-foreground border-l border-dashed" aria-hidden />
                  Takvim boşluğu ({boslukIndeksleri.length} işaretli
                  {typeof beyani?.bosluk_esigi_gun === "number" ? `, eşik ${beyani.bosluk_esigi_gun} gün` : ""})
                </span>
                <span className="flex items-center gap-2">
                  <span className="inline-block h-3 w-px border-destructive border-l border-dashed" aria-hidden />
                  Sermaye reseti ({resetIndeksleri.length} konumlandırıldı
                  {typeof beyani?.n_isaret === "number" ? ` / ${beyani.n_isaret} işaret` : ""})
                </span>
                <span className="flex items-center gap-2">
                  <span className="inline-block h-3 w-px border-primary border-l" aria-hidden />
                  Tohum sınırı {tohumIndeks === null ? "(konumlandırılamadı)" : "(solu replay tohumu)"}
                </span>
              </div>

              <Separator />

              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-medium text-sm">Tepe altı düşüş</h3>
                  <p className="text-muted-foreground text-xs">
                    Bu seriden türetildi (tarayıcıda): her noktanın o ana kadarki tepeye göre yüzdesi.
                  </p>
                </div>
                <ChartContainer config={DUSUS_CONFIG} className="aspect-auto h-32 w-full">
                  <AreaChart data={noktalar} margin={{ bottom: 0, left: 0, right: 8, top: 4 }}>
                    <defs>
                      <linearGradient id="analiz-dusus-dolgu" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-dusus)" stopOpacity={0.02} />
                        <stop offset="95%" stopColor="var(--color-dusus)" stopOpacity={0.28} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} />
                    <XAxis
                      axisLine={false}
                      dataKey="i"
                      domain={[ilkI, sonI]}
                      tickLine={false}
                      tickMargin={8}
                      ticks={isaretler}
                      tickFormatter={(deger: number) => tarihEsleme.get(deger) ?? ""}
                      type="number"
                    />
                    <YAxis
                      axisLine={false}
                      domain={["auto", 0]}
                      tickLine={false}
                      tickMargin={8}
                      width={64}
                      tickFormatter={(deger: number) => `${sayi(deger, 1) ?? ""}%`}
                    />
                    <ChartTooltip
                      cursor={{ stroke: "var(--border)", strokeDasharray: "4 4" }}
                      content={
                        <ChartTooltipContent
                          className="w-48"
                          labelFormatter={(_etiket, yuk) => {
                            const ilk = Array.isArray(yuk) ? yuk[0] : undefined;
                            const p = (ilk as { payload?: EgriNoktasi } | undefined)?.payload;
                            return p?.tarih ?? "tarih okunamadı";
                          }}
                        />
                      }
                    />
                    <Area isAnimationActive={false}
                      dataKey="dusus"
                      fill="url(#analiz-dusus-dolgu)"
                      stroke="var(--color-dusus)"
                      strokeWidth={1.5}
                      type="linear"
                      dot={false}
                      connectNulls={false}
                    />
                  </AreaChart>
                </ChartContainer>

                <div className="flex flex-wrap gap-x-8 gap-y-2 text-xs">
                  <span className="text-muted-foreground">
                    Bu seriden:{" "}
                    <span className="font-medium text-foreground tabular-nums">
                      <Deger
                        metin={enKotuDusus === null ? null : `${sayi(enKotuDusus, 2) ?? ""}%`}
                        neden="Serinin tepesi hiç pozitif olmadı — tepe-altı yüzde tanımsız" teknik="tepe ≤ 0 olduğu için (deger/tepe - 1) hesabı tanımsız"
                      />
                    </span>
                  </span>
                  <span className="text-muted-foreground">
                    score_detail.max_drawdown:{" "}
                    <span className="font-medium text-foreground tabular-nums">
                      <Deger
                        metin={sd?.max_drawdown === undefined ? null : yuzde(sd.max_drawdown, 2)}
                        neden="En büyük düşüş hesaplanmadı"
                        teknik={
                          typeof sd?.reason === "string"
                            ? `${sd.reason} — bu eşiğin altında düşüş hiç hesaplanmıyor.`
                            : "score_detail max_drawdown alanını basmadı."
                        }
                      />
                    </span>
                  </span>
                  <span className="text-muted-foreground">
                    İkisi AYNI SAYI DEĞİL: soldaki `equity_curve.json` noktalarından, sağdaki KAPANMIŞ İŞLEM
                    eğrisinden (gerekirse günlük M2M'in daha kötüsüyle) hesaplanır.
                  </span>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Eğrinin beyanı</CardTitle>
          <CardDescription>Seri hangi pencereyi kapsıyor, nerede delik var, başlangıç verisi nerede bitiyor?</CardDescription>
        </CardHeader>
        <CardContent>
          <EgriBeyaniBlogu beyani={beyani} atlanan={atlanan} />
        </CardContent>
      </Card>

      <RiskKartlari veri={veri} />
    </div>
  );
}

/** Skor / getiri / Kelly / kuyruk — dördü de ölçülemediğinde AYRI cümle taşır. */
function RiskKartlari({ veri }: { veri: PerformansGovdesi }) {
  const sd = veri.score_detail;
  const kelly = veri.kelly ?? null;
  const kuyruk = veri.tail_risk ?? null;
  const hedefDusus = sd?.targets?.max_drawdown;
  const hedefGetiri = sd?.targets?.target_return_30d;

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card className="gap-3">
        <CardHeader>
          <CardTitle className="font-normal text-muted-foreground text-sm">Bileşik skor</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="text-2xl leading-none tracking-tight tabular-nums">
            <Deger
              metin={typeof sd?.score === "number" ? sayi(sd.score, 3) : null}
              neden="Bileşik skor hesaplanmadı — sıfır değil"
              teknik={
                typeof sd?.reason === "string"
                  ? `${sd.reason} — kapı örneklem eşiğinin altında skoru TANIMSIZ bırakır (0 değil).`
                  : "score_detail.score gelmedi."
              }
            />
          </div>
          <p className="text-muted-foreground text-xs leading-snug">
            0..1 · %50 getiri, %30 düşüş, %20 Sharpe
            {typeof hedefGetiri === "number" && typeof hedefDusus === "number"
              ? ` · hedef ${yuzde(hedefGetiri, 1) ?? ""}/30g, düşüş tavanı ${yuzde(hedefDusus, 1) ?? ""}`
              : ""}
          </p>
        </CardContent>
      </Card>

      <Card className="gap-3">
        <CardHeader>
          <CardTitle className="font-normal text-muted-foreground text-sm">Toplam getiri</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className={`text-2xl leading-none tracking-tight tabular-nums ${pnlRengi(sd?.total_return)}`}>
            <Deger
              metin={sd?.total_return === undefined ? null : yuzde(sd.total_return, 2, true)}
              neden="Toplam getiri hesaplanmadı"
              teknik={
                typeof sd?.reason === "string"
                  ? `${sd.reason} — bu eşiğin altında getiri hiç hesaplanmıyor.`
                  : "score_detail.total_return gelmedi."
              }
            />
          </div>
          <p className="text-muted-foreground text-xs leading-snug">
            30 güne ölçeklenmiş:{" "}
            <Deger
              metin={sd?.realized_30d === undefined ? null : yuzde(sd.realized_30d, 2, true)}
              neden="30 güne ölçeklenmiş getiri hesaplanamadı" teknik="realized_30d gelmedi"
            />
          </p>
        </CardContent>
      </Card>

      <Card className="gap-3">
        <CardHeader>
          <CardTitle className="font-normal text-muted-foreground text-sm">Kelly (yarım)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="text-2xl leading-none tracking-tight tabular-nums">
            <Deger
              metin={kelly === null ? null : yuzde(kelly.half_kelly, 1)}
              neden="Defterde yeterli işlem yok — oran tanımsız, sıfır değil" teknik="tail/kelly eşiği: 12'den az işlem ya da tek yönlü defter (yalnız kazanç ya da yalnız kayıp)"
            />
          </div>
          <p className="text-muted-foreground text-xs leading-snug">
            {kelly === null
              ? "Tavsiye niteliğinde bir tavan; ölçülemeden gösterilmez."
              : `kazanma ${yuzde(kelly.win_rate, 1) ?? "ölçülemedi"} · kazanç/kayıp ${sayi(kelly.win_loss_ratio, 2) ?? "ölçülemedi"} · n=${sayi(kelly.n, 0) ?? "ölçülemedi"}`}
          </p>
        </CardContent>
      </Card>

      <Card className="gap-3">
        <CardHeader>
          <CardTitle className="font-normal text-muted-foreground text-sm">Kuyruk riski (CVaR)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="text-2xl leading-none tracking-tight text-red-600 tabular-nums dark:text-red-400">
            <Deger
              metin={kuyruk === null ? null : rKati(kuyruk.cvar_r === undefined ? undefined : -kuyruk.cvar_r)}
              neden="Defterde yeterli işlem yok — kuyruk kaybı hesaplanamadı" teknik="tail_risk null — 12'den (TAIL_MIN_SAMPLE) az r_multiple var; blok-bootstrap'ın dürüstçe söyleyeceği bir şey yok"
            />
          </div>
          <p className="text-muted-foreground text-xs leading-snug">
            {kuyruk === null
              ? "20 işlemlik pencerede beklenen kuyruk kaybı."
              : `${sayi(kuyruk.horizon, 0) ?? "ölçülemedi"} işlemlik pencere · VaR ${rKati(kuyruk.var_r === undefined ? undefined : -kuyruk.var_r) ?? "ölçülemedi"} · en kötü yol ${rKati(kuyruk.worst_r === undefined ? undefined : -kuyruk.worst_r) ?? "ölçülemedi"}`}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
