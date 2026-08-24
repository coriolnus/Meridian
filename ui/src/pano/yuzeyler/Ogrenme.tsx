"use client";

/* ============================================================================
   ÖĞRENME YÜZEYİ (şablon: Academy) — "öğreniyor mu, yoksa yalnız koşuyor mu?"
   ----------------------------------------------------------------------------
   BEŞ BÖLÜM, DÖRT UÇ. Her bölüm KENDİ kapısını taşır ve bu bilinçli: `/api/agent`
   düşerse sürüm çizelgesi "okunamadı" der ama karne ve araçlar çizilmeye devam eder.
   Tek bir kapıya bağlasaydım bir ucun arızası yüzeyin tamamını boşaltırdı ve operatör
   çalışan üç ölçümü de kaybederdi.

   NABIZ PERİYOTLARI OLGUNUN HIZINA GÖRE, hepsi 15 sn olsun diye değil:
     · `/api/hermes`       — yansıma/sprint durumu dakikalar içinde değişir → 30 sn
     · `/api/diagnostics`  — sunucuda ZATEN 45 sn önbellekli; daha sık sormak aynı
                             gövdeyi tekrar indirmek olurdu → 60 sn
     · `/api/agent`        — sürüm defteri günler ölçeğinde değişir → 120 sn
     · `/api/skills`       — kayıt defteri + reconcile; yan etkisi var (enablement
                             uzlaştırması) → en seyrek, 180 sn
   `/api/skills`in yan etkisi ölçüldü ve zararsız (yalnız anahtar durumuna göre
   `enabled` alanını günceller) ama yine de en seyrek sorulan uç odur.
   ============================================================================ */
import { useEffect } from "react";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";

import { Araclar } from "./ogrenme/Araclar";
import { BilesenIc } from "./ogrenme/BilesenIc";
import { Golge } from "./ogrenme/Golge";
import { Karne } from "./ogrenme/Karne";
import { Surumler } from "./ogrenme/Surumler";
import type { AjanGovdesi, HermesGovdesi, SkillGovdesi, TeshisGovdesi } from "./ogrenme/tipler";

export function Ogrenme() {
  const { bolum } = useRota();
  const y = YUZEYLER["academy"];

  const hermes = useApi<HermesGovdesi>("/api/hermes", NABIZ_MS * 2);
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", NABIZ_MS * 4);
  const ajan = useApi<AjanGovdesi>("/api/agent", NABIZ_MS * 8);
  const skills = useApi<SkillGovdesi>("/api/skills", NABIZ_MS * 12);

  // ÇAPAYA KAYDIR — `#/dashboard/academy/bilesenic` bağı bölümü de gösterir.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
      </div>

      <Karne hermes={hermes} />
      <Golge teshis={teshis} />
      <BilesenIc teshis={teshis} />
      <Surumler ajan={ajan} />
      <Araclar skills={skills} />
    </div>
  );
}
