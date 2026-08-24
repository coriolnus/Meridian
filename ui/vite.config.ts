import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";
import path from "node:path";

/* ============================================================================
   PANO DERLEMESİ — meridian/web/ İÇİNE, ama ÜZERİNE DEĞİL
   ----------------------------------------------------------------------------
   `emptyOutDir: false` HAYATİ: Vite varsayılanı çıktı klasörünü TEMİZLER ve çıktı
   klasörü `meridian/web/` — yani varsayılan davranış index.html, app.js,
   tokens.json ve fonts/ dahil ESKİ PANONUN TAMAMINI SİLERDİ. Göç bitene kadar
   ikisi yan yana duruyor; eski pano hâlâ canlının kendisi.

   `modulePreload.polyfill: false` CSP İÇİN: polyfill SATIR İÇİ bir <script> olarak
   enjekte edilir ve dağıtım CSP'si `script-src 'self'` onu BLOKLAR — sayfa canlıda
   ölü açılır. Bu arıza bu depoda iki kez yaşandı (api.py:280-281).

   NEDEN VITE, NEDEN NEXT DEĞİL — ÖLÇÜLDÜ, TARTIŞILMADI (docs/KARAR-2026-08-25):
   şablon Next 16 App Router. `next build` çıktısındaki her HTML sayfasında ÜÇ
   SATIR İÇİ <script> var (tema önyükleyicisi + `self.__next_f` RSC yükü) ve üçü de
   `script-src 'self'` altında bloklanır: sayfa çizilir, HİÇBİR düğme iş görmez.
   Ayrıca şablonun tüm pano rotaları ƒ (dinamik) — `cookies()` yüzünden — yani
   `output: "export"` da doğrudan mümkün değil. Buna karşılık şablonun Next'e
   BAĞLILIĞI 297 dosyada yalnız 20 import satırıydı; tasarım sistemi (Tailwind v4 +
   Radix + shadcn) çerçeveden bağımsız. Taşınan şey o sistem; çerçeve değil.
   ============================================================================ */
export default defineConfig({
  plugins: [react(), tailwind()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  base: "/",
  build: {
    outDir: path.resolve(__dirname, "../meridian/web"),
    emptyOutDir: false,
    modulePreload: { polyfill: false },
    assetsDir: "pano-assets",
    /* MANİFEST SUNUM İÇİN, ARAÇ ZİNCİRİ İÇİN DEĞİL. `meridian/api.py` `StaticFiles`
       montajını BİLEREK reddediyor (satır 650: montaj, dizine düşen her taslağı
       yayına açar) — ama Vite'ın çıktı adları içerik-hash'li, yani kaynağa literal
       yazılamaz. Manifest bu ikilemi çözer: sunulan ad kümesi DERLEMENİN kendi
       beyanıdır, dizin listesi değil. Manifest yoksa hiçbir varlık sunulmaz ve 404
       "derleme koşmamış" der — sessizce yarım bir sayfa açılmaz. */
    manifest: "pano-assets/manifest.json",
    rollupOptions: {
      input: path.resolve(__dirname, "pano.html"),
      output: {
        entryFileNames: "pano-assets/[name]-[hash].js",
        chunkFileNames: "pano-assets/[name]-[hash].js",
        assetFileNames: "pano-assets/[name]-[hash][extname]",
      },
    },
  },
});
