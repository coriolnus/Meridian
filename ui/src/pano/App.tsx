"use client";

/* ============================================================================
   UYGULAMA KÖKÜ — tercih deposu, KAPI, kabuk, yüzey seçimi
   ----------------------------------------------------------------------------
   `PreferencesStoreProvider` şablonda sunucudan gelen değerlerle doğuyordu.
   Burada değerler BELGE NİTELİKLERİNDEN okunuyor: önyükleyici (pano-onyuk.js)
   onları ilk boyamadan önce çerezden okuyup `<html>`e yazar, depo da aynı
   yerden başlar. Tek kaynak DOM; ikinci bir kopya tutmak, tercihin iki farklı
   yerde iki farklı değeri olması demekti.

   KAPI KABUĞUN ÜSTÜNE ÇIKTI (2026-09-01). Bugüne kadar burada koşulsuz `Kabuk`
   duruyordu, çünkü panonun önünde APISIX basic-auth vardı ve uygulamanın kendi
   oturumu İKİNCİ katmandı. O dış kapı operatör kararıyla kaldırıldı; artık tek
   kimlik katmanı `/api/login` + çerez. Kimliksiz ziyaretçiye kabuğu çizmek,
   ona yüzey haritasını ve her panelin 401'ini okutmak olurdu — dallanma bu
   yüzden BURADA, kabuğun mount edilip edilmeyeceği kararında.

   TERCİH DEPOSU KAPININ DA ÜSTÜNDE: tema ve yazı tipi ziyaretçinin çerezinden
   geliyor ve kapı da o temada çizilmeli. Kapı deponun DIŞINDA kalsaydı gece
   vardiyasındaki operatör önce beyaz bir giriş ekranı, sonra koyu bir pano
   görürdü.
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

import { GirisKapisi } from "./GirisKapisi";
import { Kabuk } from "./Kabuk";
import { OturumSaglayici, useOturum } from "./oturum";
import { Yuzey } from "./Yuzey";

function belgedenTercihler(): PreferenceValueMap {
  const d = { ...PREFERENCE_DEFAULTS };
  function ata<K extends PreferenceKey>(k: K) {
    d[k] = parsePreference(k, document.documentElement.getAttribute(PREFERENCE_REGISTRY[k].attribute));
  }
  for (const k of PREFERENCE_KEYS) ata(k);
  return d;
}

/**
 * TEK DALLANMA, İKİ YOL. Ara bir hâl (kilitli kabuk, yarı çizilmiş kenar çubuğu)
 * BİLEREK yok: yarım kabuk, olmayan bir yetkiyi varmış gibi gösterir. Oturumun
 * açık OLDUĞU ölçülmediği sürece kabuk doğmaz — "ölçülemedi" de "kapalı" gibi
 * kapıya düşer, ama kapının kendisi orada hangi ekranı çizemediğini yazar
 * (`GirisKapisi::Bekleme`). Kabuk tarafına düşmek için tek yeterli sebep,
 * `authenticated: true` alanını GERÇEKTEN okumaktır.
 *
 * OTURUM ORTADA DÜŞERSE: sağlayıcının 15 saniyelik nabzı `authenticated:false`
 * okur okumaz bu dallanma kabuğu söker ve tam-ekran giriş geri gelir. Kabuk
 * içindeki "oturum düştü" hapı (üst bar) o ana kadarki köprüdür — 401'i ilk
 * gören odur, nabız ise onu ekrandan kaldırandır.
 */
function Govde() {
  const { hal } = useOturum();
  if (hal === "acik") {
    return (
      <Kabuk>
        <Yuzey />
      </Kabuk>
    );
  }
  return <GirisKapisi />;
}

export function App() {
  return (
    /* TOOLTIP SAĞLAYICISI EN DIŞTA — şablonun kök düzeninde de orada.
       Atlandığında uygulama AÇILIŞTA ÇÖKÜYOR: kenar çubuğunun ikon rayı her maddeye
       bir `Tooltip` sarıyor ve sağlayıcısız bir `Tooltip` `throw` ediyor. Ölçüldü
       (2026-08-25, boş ekran + "must be used within TooltipProvider"). */
    <TooltipProvider>
      <PreferencesStoreProvider initialValues={belgedenTercihler()}>
        <OturumSaglayici>
          <Govde />
        </OturumSaglayici>
      </PreferencesStoreProvider>
    </TooltipProvider>
  );
}
