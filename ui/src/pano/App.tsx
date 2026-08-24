"use client";

/* ============================================================================
   UYGULAMA KÖKÜ — tercih deposu, kabuk, yüzey seçimi
   ----------------------------------------------------------------------------
   `PreferencesStoreProvider` şablonda sunucudan gelen değerlerle doğuyordu.
   Burada değerler BELGE NİTELİKLERİNDEN okunuyor: önyükleyici (pano-onyuk.js)
   onları ilk boyamadan önce çerezden okuyup `<html>`e yazar, depo da aynı
   yerden başlar. Tek kaynak DOM; ikinci bir kopya tutmak, tercihin iki farklı
   yerde iki farklı değeri olması demekti.
   ============================================================================ */
import {
  PREFERENCE_DEFAULTS,
  PREFERENCE_KEYS,
  PREFERENCE_REGISTRY,
  parsePreference,
  type PreferenceKey,
  type PreferenceValueMap,
} from "@/lib/preferences/preferences-config";
import { TooltipProvider } from "@/components/ui/tooltip";
import { PreferencesStoreProvider } from "@/stores/preferences/preferences-provider";

import { Kabuk } from "./Kabuk";
import { Yuzey } from "./Yuzey";

function belgedenTercihler(): PreferenceValueMap {
  const d = { ...PREFERENCE_DEFAULTS };
  function ata<K extends PreferenceKey>(k: K) {
    d[k] = parsePreference(k, document.documentElement.getAttribute(PREFERENCE_REGISTRY[k].attribute));
  }
  for (const k of PREFERENCE_KEYS) ata(k);
  return d;
}

export function App() {
  return (
    /* TOOLTIP SAĞLAYICISI EN DIŞTA — şablonun kök düzeninde de orada.
       Atlandığında uygulama AÇILIŞTA ÇÖKÜYOR: kenar çubuğunun ikon rayı her maddeye
       bir `Tooltip` sarıyor ve sağlayıcısız bir `Tooltip` `throw` ediyor. Ölçüldü
       (2026-08-25, boş ekran + "must be used within TooltipProvider"). */
    <TooltipProvider>
      <PreferencesStoreProvider initialValues={belgedenTercihler()}>
        <Kabuk>
          <Yuzey />
        </Kabuk>
      </PreferencesStoreProvider>
    </TooltipProvider>
  );
}
