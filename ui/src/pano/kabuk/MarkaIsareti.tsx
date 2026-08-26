/* ============================================================================
   MARKA İŞARETİ — "C · M Monogramı", varyant v0 (operatör tasarımı, 2026-08-26)
   ----------------------------------------------------------------------------
   M'nin iki kolu kutupta birleşen meridyen çizgileri gibi içe kapanır; enlem
   çizgisi ortadan geçer. GEOMETRİ DOKUNULMAZ: v0, üç düzeltme varyantı render
   edilip gösterildikten SONRA operatörün seçtiği hâldir.

   GEOMETRİ İKİ YERDE YAŞIYOR ve bu KAÇINILMAZ:
     meridian/web/favicon.svg  → sekme ikonu. AYRI bir belge olarak yüklenir,
                                 sayfanın `color`ını GÖREMEZ → sabit renk +
                                 `prefers-color-scheme`.
     bu dosya                  → uygulama içi. Kenar çubuğu metniyle AYNI renkte
                                 olmalı ve temayla birlikte kaymalı →
                                 `currentColor`. Sabit renk burada YANLIŞ olurdu.
   `<img src="/favicon.svg">` ile tek dosyaya inmek ÇÖZÜM DEĞİL: `<img>` de ayrı
   bir belgedir, `currentColor`u yine miras almaz ve işaret metinden kopuk bir
   tonda kalırdı. İki render zorunlu; AYRIŞMALARI çiviyle kapatılıyor —
   tests/test_marka_isareti_v321.py geometriyi iki dosya arasında karşılaştırır.
   ========================================================================== */

/** Meridian marka işareti. Rengi `currentColor`dan alır — kabın metin rengiyle
 *  aynı tonda kalır ve tema değişince onunla birlikte kayar. */
export function MarkaIsareti({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 100 100"
      className={className}
      role="img"
      aria-label="Meridian"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="6" y1="52" x2="94" y2="52" strokeWidth="3.5" />
      <path d="M16,82 L33,17 L50,52 L67,17 L84,82" strokeWidth="7" />
    </svg>
  );
}
