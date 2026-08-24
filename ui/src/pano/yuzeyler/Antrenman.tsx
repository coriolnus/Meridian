"use client";

/* ============================================================================
   ANTRENMAN YÜZEYİ (şablon: Productivity) — "makine çalışıyor mu, yoksa yalnız
   duruyor mu?"
   ----------------------------------------------------------------------------
   İKİ BÖLÜM, İKİ SORU VE İKİSİ BİRBİRİNİN YERİNE GEÇMEZ:
     · SPRINT — kum havuzunda koşan öğrenme antrenmanı. "Koşuyor mu" ile "koştu,
       aday geçmedi" AYRI satırlarda (bölümün kendi şerhine bak).
     · HERMES — canlı yansıma hattı: kalp atışı, geri sayım, geri dolum, harcama.

   YÜZEY ÖĞRENME (Academy) İLE AYNI KAPIYI PAYLAŞIR (`yuzeyler/ogrenme/ortak.tsx`) ve
   bu bilinçli: iki yüzey aynı `/api/hermes` gövdesine bakıyor ve bir alanın "ölçülemedi"
   basımı iki yerde ayrışırsa aynı sayı iki ekranda iki farklı gerçek gösterirdi.

   NABIZ: `/api/hermes` 30 sn (yansıma/sprint dakikalar içinde değişir),
   `/api/diagnostics` 60 sn (sunucuda ZATEN 45 sn önbellekli — daha sık sormak aynı
   gövdeyi tekrar indirmek olurdu).
   ============================================================================ */
import { useEffect } from "react";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";

import { Hermes } from "./antrenman/Hermes";
import { Sprint } from "./antrenman/Sprint";
import type { HermesGovdesi, TeshisGovdesi } from "./ogrenme/tipler";

export function Antrenman() {
  const { bolum } = useRota();
  const y = YUZEYLER["productivity"];

  const hermes = useApi<HermesGovdesi>("/api/hermes", NABIZ_MS * 2);
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", NABIZ_MS * 4);

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

      <Sprint hermes={hermes} />
      <Hermes hermes={hermes} teshis={teshis} />
    </div>
  );
}
