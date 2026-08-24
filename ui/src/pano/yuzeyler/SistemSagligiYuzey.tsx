"use client";

/* ============================================================================
   SİSTEM SAĞLIĞI YÜZEYİ — şablonun `Infrastructure` panosu, Meridian'ın içeriğiyle
   ----------------------------------------------------------------------------
   İKİ KATMAN AYRI, operatörün açık isteğiyle: "sistemin çalıştığı ALTYAPI
   bileşenlerini ayrı (sunucu vs), meridian uygulamasında çalışan ALT bileşenlerin
   ne kadar kaynak tükettiğini ayrı ayrı görmek istiyorum". Bu yüzden sayfanın
   başında iki bağımsız bölüm var (Makine · Meridian bileşenleri) ve kayıtlı beş
   bölüm (operasyon · müdahale · veri borusu · piyasa · seans içi) onların ardından
   geliyor. Sıra bir kaza değil: arıza triyajı YUKARIDAN AŞAĞI okunur — önce kutu,
   sonra süreçler, sonra çalan alarm, sonra kollar, sonra veri, sonra piyasa/akış.

   DÖRT UÇ TEK YERDE AÇILIR ve bölümlere PROP olarak iner (beşincisi paylaşılan
   `/api/today` nabzıdır — `durum.tsx::useBugun`, kendi isteğimizi AÇMIYORUZ):
     · /api/infra        15 sn — kutu + süreç + birimler; ucun kendi TTL'i 8 sn
       (api.py `INFRA_TTL_S`), yani her anket TAZE ölçüm alır
     · /api/alerts       15 sn — çalan alarm; gecikirse triyaj gecikir
     · /api/diagnostics  30 sn — ucun önbelleği 45 sn (api.py:4348), yani bazı
       anketler KOPYA döner; gövde bunu `onbellekten` ile kendisi beyan ediyor.
       Daha sık sormanın faydası yok, daha seyrek sormak kolları bayatlatırdı.
     · /api/market       60 sn — EOD kapanış; seans içinde saniyede bir değişmez
   HER BÖLÜM KENDİ İSTEĞİNİ AÇSAYDI (`durum.tsx`taki gerekçenin aynısı) müdahale
   kolları ile seans-içi akış AYNI ekranda İKİ FARKLI ANI gösterebilirdi: biri
   "HALT çekili" derken öteki bir önceki dakikanın "serbest"ini basardı. Aynı
   ekranda iki gerçek, operatörün hangisine inanacağını bilemediği bir arayüzdür.

   `/api/market` BİLEREK `?seri=1` OLMADAN çağrılıyor: seri her satıra ~40 kapanış
   ekler (260 sembolde ≈91 KB, marketview.build şerhinde ölçülmüş) ve bu yüzeyde
   kıvılcım çizilmiyor. Çizmediğimiz bir yükü her tazelemede taşımazdık.
   ============================================================================ */
import { useEffect } from "react";
import { Server } from "lucide-react";

import { Badge } from "@/components/ui/badge";

import { Bilesenler } from "./sistem/Bilesenler";
import { Intraday } from "./sistem/Intraday";
import { Makine } from "./sistem/Makine";
import { Mudahale } from "./sistem/Mudahale";
import { Operasyon } from "./sistem/Operasyon";
import { Piyasa } from "./sistem/Piyasa";
import { Veriboru } from "./sistem/Veriboru";
import { YUZEYLER } from "../alanlar";
import { useBugun } from "../durum";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";
import type { AlarmGovdesi, InfraGovdesi, PiyasaGovdesi, TeshisGovdesi } from "./sistem/uctipleri";

export function SistemSagligiYuzey() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR, ELLE YAZILMAZ: `alanlar.ts` bu yüzeyin başlığını ve
  // cevapladığı SORUYU tek yerde tutuyor. Burada ikinci kez yazsaydık, kayıt
  // değiştiğinde ekran sessizce eski soruyu sormaya devam ederdi.
  const y = YUZEYLER.infrastructure;
  const bugun = useBugun();
  const infra = useApi<InfraGovdesi>("/api/infra", NABIZ_MS);
  const alarm = useApi<AlarmGovdesi>("/api/alerts", NABIZ_MS);
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", NABIZ_MS * 2);
  const piyasa = useApi<PiyasaGovdesi>("/api/market", NABIZ_MS * 4);

  // ÇAPAYA KAYDIR — `GenelYuzey.tsx`teki desenin aynısı ve aynı gerekçeyle:
  // `#/dashboard/infrastructure/market` bağı sayfayı açmakla kalmaz, bölümü de gösterir.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <Server className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        {/* ROZET ŞERİDİ YALNIZ ÖLÇÜLENİ TAŞIR: dört rozetin her biri kendi alanı
            gövdede VARSA çizilir, yoksa HİÇ çizilmez (boş rozet "0" diye okunurdu).
            Şablonun sabit "99.93% Global Uptime" rozetinin karşılığı burada YOK,
            çünkü o sayı bu sistemde ölçülmüyor. */}
        <div className="flex flex-wrap items-center gap-2">
          {bugun.veri?.halted !== undefined ? (
            <Badge variant={bugun.veri.halted ? "destructive" : "outline"}>
              {bugun.veri.halted ? "HALT ÇEKİLİ" : "HALT serbest"}
            </Badge>
          ) : null}
          {alarm.veri?.pending !== undefined ? (
            <Badge variant={alarm.veri.pending > 0 ? "destructive" : "outline"}>
              {alarm.veri.pending} bekleyen alarm
            </Badge>
          ) : null}
          {piyasa.veri?.stale_n !== undefined ? (
            <Badge variant="outline">{piyasa.veri.stale_n} bayat bar</Badge>
          ) : null}
          {infra.veri?.bilesenler ? (
            <Badge variant="outline">
              {infra.veri.bilesenler.filter((b) => b.durum === "active").length}/
              {infra.veri.bilesenler.length} birim koşuyor
            </Badge>
          ) : null}
        </div>
      </div>

      <Makine durum={infra} />
      <Bilesenler durum={infra} />
      <Operasyon durum={alarm} />
      <Mudahale teshis={teshis} bugun={bugun} />
      <Veriboru teshis={teshis} />
      <Piyasa durum={piyasa} />
      <Intraday teshis={teshis} />
    </div>
  );
}
