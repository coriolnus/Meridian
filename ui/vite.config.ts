import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";
import path from "node:path";

/* ============================================================================
   PİLOT DERLEMESİ — meridian/web/ İÇİNE, ama ÜZERİNE DEĞİL.
   ----------------------------------------------------------------------------
   `emptyOutDir: false` HAYATİ: Vite varsayılanı çıktı klasörünü TEMİZLER ve
   burada çıktı klasörü `meridian/web/` — yani varsayılan davranış index.html,
   app.js, tokens.json ve fonts/ dahil PANONUN TAMAMINI SİLERDİ. Pilot yan yana
   durur, yerine geçmez; karar ölçümle verilecek.

   `modulePreload.polyfill: false` CSP İÇİN: polyfill SATIR İÇİ bir <script>
   olarak enjekte edilir ve dağıtım CSP'si `script-src 'self'` onu BLOKLAR —
   sayfa canlıda ölü açılır. Bu arıza bu depoda iki kez yaşandı (api.py:280-281).
   Çivi: tests/test_ui_pilot_kapilari_v286.py::test_G2d.
   ============================================================================ */
export default defineConfig({
  plugins: [react(), tailwind()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  base: "/",
  build: {
    outDir: path.resolve(__dirname, "../meridian/web"),
    emptyOutDir: false,
    modulePreload: { polyfill: false },
    assetsDir: "pilot-assets",
    rollupOptions: {
      input: path.resolve(__dirname, "pilot-workflow.html"),
      output: {
        entryFileNames: "pilot-assets/[name]-[hash].js",
        chunkFileNames: "pilot-assets/[name]-[hash].js",
        assetFileNames: "pilot-assets/[name]-[hash][extname]",
      },
    },
  },
});
