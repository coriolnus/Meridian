"use client";

/* ============================================================================
   BUGÜN — operatörün tek ekranı (şablonun "Default" panosu)
   ----------------------------------------------------------------------------
   ŞABLONUN GRAMERİ AYNEN: üstte KPI kartı ızgarası, altında büyük bir alan
   grafiği, en altta bir tablo (`dashboard/default/page.tsx`). Değişen tek şey,
   şablonun sabit sayılarının yerine `/api/today` ve `/api/performance`ın ölçülmüş
   alanlarının gelmesi — ve her parçanın ölçemediğinde bunu söyleyebilmesi.

   NABIZ PAYLAŞILIYOR: bu yüzey `/api/today`i KENDİSİ İSTEMEZ, `useBugun()`
   üzerinden üst barla ve kenar çubuğuyla AYNI gövdeye bakar (durum.tsx başlığı:
   aynı ekranda iki farklı gerçek, operatörün hangisine inanacağını bilemediği bir
   arayüzdür). Eğri ayrı uçtan ve ayrı periyottan gelir — gerekçesi o dosyada.

   TİP GENİŞLETMESİ: `useBugun()` paylaşılan `BugunGovdesi`i döndürür ve o tip bu
   turda bana kapalı. `bugun/tipler.ts` ondan TÜREYEREK bu yüzeyin okuduğu alanları
   ekliyor; buradaki tek dönüştürme o türemenin uygulanmasıdır — yeni bir alan
   uydurmaz, `api.py`de okunmuş alanları görünür kılar.

   ÜST BARLA ÇAKIŞMA YOK: durum hapı (HALT / kesici / sakin) HER yüzeyde üst barda
   duruyor ve sürekli açıktır. Buradaki şerit ONUN KOPYASI DEĞİL — yalnız bir şey
   TERS GİTTİĞİNDE açılır ve gerekçeyi cümleyle yazar. Sakin bir günde hiç çizilmez.
   ============================================================================ */
import { AlertTriangle, OctagonPause } from "lucide-react";
import { useEffect } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import { YUZEYLER } from "../alanlar";
import { useBugun } from "../durum";
import { useRota } from "../rota";
import { HukumDagilimi } from "./bugun/HukumDagilimi";
import { KpiIskeleti, KpiKartlari } from "./bugun/KpiKartlari";
import { PlanTablosu } from "./bugun/PlanTablosu";
import { SermayeEgrisi } from "./bugun/SermayeEgrisi";
import { UcHal } from "./bugun/ortak";
import type { BugunTam } from "./bugun/tipler";

/** Yalnız TERS GİDEN şeyi yazar. Sırası önem sırasıdır: durdurulmuş bir sistemde
 *  bayat nabız ikincil bir ayrıntıdır ve ikisini yan yana koymak, en pahalı olanı
 *  gürültüye gömerdi. */
function Serit({ b }: { b: BugunTam }) {
  if (b.halted === true) {
    return (
      <Alert variant="destructive">
        <OctagonPause aria-hidden />
        <AlertTitle>Sistem DURDURULDU</AlertTitle>
        <AlertDescription>
          Yeni giriş açılmıyor. Kolun çekildiği yer Müdahale kolları bölümü; bu ekran yalnız okur.
        </AlertDescription>
      </Alert>
    );
  }
  if (b.stale === true) {
    return (
      <Alert>
        <AlertTriangle aria-hidden />
        <AlertTitle>Nabız bayat</AlertTitle>
        <AlertDescription>
          Aşağıdaki sayılar son yazılan nabızdan geliyor; şu anki durum OLMAYABİLİR.
          {b.heartbeat_age_seconds !== undefined && b.heartbeat_age_seconds !== null
            ? ` Nabız ${Math.round(b.heartbeat_age_seconds)} saniye önce yazıldı.`
            : " Nabzın yaşı ölçülemedi."}
        </AlertDescription>
      </Alert>
    );
  }
  if (b.heartbeat?.data_ok === false) {
    return (
      <Alert variant="destructive">
        <AlertTriangle aria-hidden />
        <AlertTitle>Veri kapısı ŞÜPHELİ</AlertTitle>
        <AlertDescription>
          Nabız `data_ok=false` yazmış. Bu ekrandaki planlar ve fiyatlar şüpheli veriyle üretilmiş olabilir.
        </AlertDescription>
      </Alert>
    );
  }
  return null;
}

export function BugunYuzeyi() {
  const { bolum } = useRota();
  const y = YUZEYLER.default;
  const nabiz = useBugun();

  // ÇAPAYA KAYDIR — `GenelYuzey.tsx`teki desenin aynısı. Bu yüzeyin bölümleri
  // `alanlar.ts` kaydında YOK (Bugün tek ekran olarak tasarlandı) ama derin bağ
  // yine de çalışsın: `#/dashboard/default/planlar` tabloya iner.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  // TÜREMENİN UYGULANMASI: gövde aynı gövde, tip `api.py`de okunmuş alanları taşıyor.
  const durum = { ...nabiz, veri: nabiz.veri as BugunTam | null };

  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
      </div>

      <UcHal durum={durum} iskelet={<KpiIskeleti />}>
        {(b) => (
          <div className="flex flex-col gap-4 md:gap-6">
            <Serit b={b} />

            {/* BAYAT AMA SİLİNMEMİŞ VERİ: `veri.ts` bir ağ hıçkırığında eski gövdeyi
                SİLMİYOR, yalnız `hata`yı dolduruyor. O hâlde sayıları çizeriz ama
                taze saymayız — bu satır o farkı ekranda tutar. */}
            {durum.hata !== null ? (
              <Alert>
                <AlertTriangle aria-hidden />
                <AlertTitle>Son tazeleme başarısız</AlertTitle>
                <AlertDescription>
                  Aşağıdakiler son BAŞARILI okumadan
                  {durum.zaman ? ` (${durum.zaman.toLocaleTimeString("tr-TR")})` : ""}; şu anki durum değil. Neden:{" "}
                  {durum.hata}
                </AlertDescription>
              </Alert>
            ) : null}

            <section id="bolum-kpi" className="scroll-mt-20">
              <KpiKartlari b={b} />
            </section>

            <section id="bolum-egri" className="grid grid-cols-1 gap-4 scroll-mt-20 md:gap-6 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <SermayeEgrisi />
              </div>
              <div id="bolum-hukum" className="scroll-mt-20">
                <HukumDagilimi b={b} />
              </div>
            </section>

            <section id="bolum-planlar" className="scroll-mt-20">
              <PlanTablosu b={b} />
            </section>
          </div>
        )}
      </UcHal>
    </div>
  );
}
