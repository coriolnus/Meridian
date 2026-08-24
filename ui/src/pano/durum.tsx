/* ============================================================================
   PANO DURUMU — `/api/today` TEK yerden çekilir, TEK nabızla
   ----------------------------------------------------------------------------
   Üst bar (HALT, durum hapı), kenar çubuğu (hesap kutusu, rozetler) ve Bugün
   yüzeyi AYNI gövdeye bakıyor. Her biri kendi `useApi("/api/today")`sini açsaydı
   üç ayrı istek, üç ayrı zamanlayıcı ve — asıl sorun — ÜÇ AYRI AN olurdu: üst bar
   "HALT çekili" derken kenar çubuğu bir önceki saniyenin "sakin"ini gösterebilirdi.
   Aynı ekranda iki farklı gerçek, operatörün hangisine inanacağını bilemediği bir
   arayüzdür.
   ============================================================================ */
import { createContext, use, type ReactNode } from "react";

import { NABIZ_MS, useApi, type Durum } from "./veri";
import type { BugunGovdesi } from "./tipler";

const BugunBaglami = createContext<Durum<BugunGovdesi> | null>(null);

export function BugunSaglayici({ children }: { children: ReactNode }) {
  const durum = useApi<BugunGovdesi>("/api/today", NABIZ_MS);
  return <BugunBaglami value={durum}>{children}</BugunBaglami>;
}

export function useBugun(): Durum<BugunGovdesi> {
  const d = use(BugunBaglami);
  if (!d) throw new Error("BugunSaglayici yok");
  return d;
}
