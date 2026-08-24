"use client";

/* ============================================================================
   ANALİZ YÜZEYİ — "Biriken hükümler ne söylüyor?"
   ----------------------------------------------------------------------------
   İKİ BÖLÜM, ÜÇ UÇ. Kayıttaki bölümler (`alanlar.ts`) korunuyor:
     · `topviews`   — dokuz facetin kırılımı + kurulum × rejim verim matrisi
     · `performans` — sermaye eğrisi, tepe-altı düşüş, R dağılımı, risk sayıları

   UÇLAR BURADA BİR KEZ AÇILIYOR ve alt bileşenlere `Durum<T>` olarak geçiyor.
   `/api/performance` iki bileşenin (KPI şeridi + para eğrisi), `/api/topviews`
   yine ikisinin (facet tablosu + dağılım) kaynağı. Her biri kendi `useApi`sini
   açsaydı aynı ekranda AYNI ucun İKİ AYRI ANI olurdu — üst şerit bir okumadan,
   alttaki grafik başka bir okumadan. `durum.tsx`teki `useBugun` gerekçesi aynen
   geçerli, yalnız kapsam bu yüzeyle sınırlı olduğu için bağlam kurulmadı.

   NABIZ NEDEN 60 SANİYE (panonun 15 sn'lik nabzı DEĞİL): bu üç ucun beslediği
   sayılar seans kadanslıdır — `equity_curve.json` günde TEK nokta ekliyor
   (loop._persist_equity_point), `trades.jsonl` bir işlem kapandığında büyüyor.
   15 saniyede bir sormak aynı sayıyı dört kez getirirdi ve bedeli boş değil:
   `/api/performance` her istekte `tail_risk`i koşuyor, o da 20.000 yollu bir
   blok-bootstrap (score.py TAIL_SIMS). Elle tazeleme düğmesi üstte duruyor.
   ============================================================================ */
import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { useApi } from "../veri";
import { GetiriDagilimi } from "./analiz/GetiriDagilimi";
import { KpiSeridi } from "./analiz/KpiSeridi";
import { KurulumRejim } from "./analiz/KurulumRejim";
import { ParaEgrisi } from "./analiz/ParaEgrisi";
import { TopviewsTablosu } from "./analiz/TopviewsTablosu";
import { Kapi, sayi } from "./analiz/ortak";
import type { PerformansGovdesi, PlotlarGovdesi, TopviewsGovdesi } from "./analiz/tipler";

/** Bkz. dosya başı: seans kadanslı uçlar + istek başına 20.000 yollu bootstrap. */
const ANALIZ_NABIZ_MS = 60_000;

const YUZEY = YUZEYLER.analytics;

function BolumBasligi({ kimlik }: { kimlik: string }) {
  const b = YUZEY.bolumler.find((x) => x.kimlik === kimlik);
  if (!b) return null;
  const Ikon = b.ikon;
  return (
    <div className="flex items-start gap-2">
      <Ikon className="mt-1 size-4 shrink-0 text-muted-foreground" aria-hidden />
      <div className="min-w-0">
        <h2 className="font-semibold text-lg tracking-tight">{b.baslik}</h2>
        <p className="text-muted-foreground text-sm">{b.soru}</p>
      </div>
    </div>
  );
}

export function AnalizYuzey() {
  const { bolum } = useRota();

  const perf = useApi<PerformansGovdesi>("/api/performance", ANALIZ_NABIZ_MS);
  const top = useApi<TopviewsGovdesi>("/api/topviews", ANALIZ_NABIZ_MS);
  const plots = useApi<PlotlarGovdesi>("/api/plots", ANALIZ_NABIZ_MS);

  // ÇAPAYA KAYDIR — `GenelYuzey`teki desen. Eski panonun `#topviews` / `#performans`
  // yer imleri `ROTA_TAKMA_ADLARI` üstünden buraya düşüyor ve çalışmaya devam etsin.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const sonOkuma = [perf.zaman, top.zaman, plots.zaman].filter((z): z is Date => z !== null);
  // ÜÇ UÇ AYRI ANLARDA DÖNER: şerit EN ESKİ okumayı yazar, en yenisini değil.
  // En yeniyi yazmak, düşmüş bir ucun bayatlığını taze bir kardeşinin arkasına saklardı.
  const enEski = sonOkuma.length === 0 ? null : new Date(Math.min(...sonOkuma.map((z) => z.getTime())));

  function hepsiniTazele() {
    perf.tazele();
    top.tazele();
    plots.tazele();
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">{YUZEY.baslik}</h1>
          <p className="mt-1 text-muted-foreground text-sm">{YUZEY.soru}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-xs tabular-nums">
            {enEski === null
              ? "henüz okunmadı"
              : `en eski okuma ${enEski.toLocaleTimeString("tr-TR")} · ${ANALIZ_NABIZ_MS / 1000} sn nabız`}
          </span>
          <Button variant="outline" size="sm" onClick={hepsiniTazele}>
            <RefreshCw data-icon="inline-start" />
            Tazele
          </Button>
        </div>
      </div>

      <KpiSeridi perf={perf} />

      <section id="bolum-topviews" className="flex scroll-mt-20 flex-col gap-4">
        <BolumBasligi kimlik="topviews" />
        <KapsamKarti top={top} />
        <TopviewsTablosu top={top} />
        <KurulumRejim plots={plots} />
      </section>

      <section id="bolum-performans" className="flex scroll-mt-20 flex-col gap-4">
        <BolumBasligi kimlik="performans" />
        <ParaEgrisi perf={perf} />
        <GetiriDagilimi top={top} />
        <HoldoutNotu perf={perf} />
      </section>
    </div>
  );
}

/** Facet ailesinin TOPLAM paydası — tablonun üstünde, tek cümlede. */
function KapsamKarti({ top }: { top: ReturnType<typeof useApi<TopviewsGovdesi>> }) {
  return (
    <Kapi durum={top} ad="/api/topviews" yukseklik="h-16">
      {(v) => (
        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="font-normal text-muted-foreground text-sm">Bu yüzey neyi sayıyor?</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
              <span>
                <span className="text-muted-foreground">Kapanmış işlem: </span>
                <span className="font-medium tabular-nums">{sayi(v.toplam_islem, 0) ?? "ölçülemedi"}</span>
              </span>
              <span>
                <span className="text-muted-foreground">Plan: </span>
                <span className="font-medium tabular-nums">{sayi(v.toplam_plan, 0) ?? "ölçülemedi"}</span>
              </span>
              <span>
                <span className="text-muted-foreground">Defter: </span>
                <span className="font-medium">{v.kaynak_defter ?? "beyan edilmedi"}</span>
              </span>
              <span>
                <span className="text-muted-foreground">Ölçüm anı: </span>
                <span className="font-medium tabular-nums">{v.as_of ?? "beyan edilmedi"}</span>
              </span>
            </div>
            {typeof v.kapsam === "string" ? (
              <p className="text-muted-foreground text-xs leading-relaxed">{v.kapsam}</p>
            ) : (
              <p className="text-muted-foreground text-xs leading-relaxed">
                Uç kapsam cümlesini basmadı — bu yüzeyin hangi paydayı saydığı ölçülemedi.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </Kapi>
  );
}

/** Dondurulmuş holdout notu uçtan gelir; SABİT metni panoya kopyalamak, uç değişince
 *  sessizce yanlış söylerdi (aynı hata `/api/secrets` model varsayılanında yaşandı). */
function HoldoutNotu({ perf }: { perf: ReturnType<typeof useApi<PerformansGovdesi>> }) {
  const not = perf.veri?.holdout_note;
  if (typeof not !== "string" || not.length === 0) return null;
  return <p className="text-muted-foreground text-xs leading-relaxed">{not}</p>;
}
