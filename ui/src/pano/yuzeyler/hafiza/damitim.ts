/* ============================================================================
   lessons.md AYRIŞTIRICISI — ham metni belge yapısına çevirir
   ----------------------------------------------------------------------------
   DOSYA `hafiza/` ALTINA TAŞINDI (2026-09-02, operatör kararı): dersler artık
   Hafıza yüzeyinin Bilgi Tabanı görünümünde yaşıyor ve eski belge rafı yüzeyi
   tümüyle kalktı. Ayrıştırıcı KOPYALANMADI, taşındı — iki uygulama olsaydı bölüm
   sayıları sessizce ayrışır ve hangisinin doğru olduğu hiçbir yerde yazmazdı.

   DOSYA ADI `damitim.ts`, `hafiza.ts` DEĞİL: ad çakışmasını yeniden adlandırarak
   çözmek, derleyiciyi harf durumuna güvendirmekten sağlamdır (macOS dosya sistemi
   büyük/küçük harfe duyarsız, aynı depo Linux'ta koşuyor — TS1149).
   ----------------------------------------------------------------------------
   KAYNAK: `GET /api/memory` → `lessons_md`. Uç `state/lessons.md` dosyasını HAM
   döndürüyor; dosya yoksa `"_No lessons yet._"` yazıyor (api.py::api_memory).
   Bu sabit dizge bir BELGE DEĞİL, bir BOŞLUK BEYANIDIR ve burada öyle ayrılıyor:
   onu bir başlıksız paragraf gibi çizmek, olmayan bir hafızayı bir satırlık
   hafıza gibi gösterirdi.

   ÖLÇÜM (2026-08-25, `state/lessons.md`): 2 392 bayt · bir `#` belge başlığı ·
   iki italik künye satırı · `##` bölümleri ("Dead ends — do not retry",
   "Calibration misses — belief updated") · madde satırları `- **değişken** (…): …`
   biçiminde. Ayrıştırıcı BU YAPIYI okur; tanımadığı satırı YUTMAZ, bulunduğu
   bölümün düz yazısına koyar — bir markdown ayrıştırıcısının sessizce sildiği her
   satır, okunmamış bir ders demektir.

   NEDEN AJAN YÜZEYİ DE BURAYI KULLANIYOR: aynı dosyanın iki ayrı ayrıştırıcısı
   olsaydı (biri sohbetteki "kalıcı hafıza" balonu, biri ders görünümü), bölüm
   sayıları sessizce ayrışabilir ve hangisinin doğru olduğu hiçbir yerde yazmazdı.
   Tek uygulama, tek gerçek.
   ============================================================================ */

/** Uç dosya yokken bunu döndürür (api.py::api_memory) — belge değil, boşluk beyanı. */
export const BOSLUK_BEYANI = "_No lessons yet._";

export interface HafizaBolumu {
  readonly baslik: string;
  /** `- ` ile başlayan satırlar, işaret sökülmüş hâlde. */
  readonly maddeler: readonly string[];
  /** Madde olmayan, boş olmayan satırlar — YUTULMAZ. */
  readonly duzYazi: readonly string[];
}

export interface Hafiza {
  /** `# ` başlığı; yoksa null. */
  readonly baslik: string | null;
  /** Belge başlığı ile ilk `##` arasındaki künye/açıklama satırları. */
  readonly kunye: readonly string[];
  readonly bolumler: readonly HafizaBolumu[];
  readonly satirN: number;
  readonly karakterN: number;
  /** Uç "henüz ders yok" dedi mi? (Boş belge ile AYNI ŞEY DEĞİL.) */
  readonly bosBeyani: boolean;
}

/** Markdown vurgusunu söker — `**x**` ve `_x_` ekranda ham işaretle durmasın diye.
 *  İçeriği DEĞİŞTİRMİYOR, yalnız işaret karakterlerini kaldırıyor. */
export function vurguSok(s: string): string {
  return s.replace(/\*\*(.+?)\*\*/g, "$1").replace(/(^|\s)_(.+?)_(?=$|\s|[.,;:])/g, "$1$2");
}

export function hafizaAyristir(ham: string): Hafiza {
  const bosBeyani = ham.trim() === BOSLUK_BEYANI;
  const satirlar = ham.split("\n");
  let baslik: string | null = null;
  const kunye: string[] = [];
  const bolumler: HafizaBolumu[] = [];
  let acik: { baslik: string; maddeler: string[]; duzYazi: string[] } | null = null;

  for (const ham_satir of satirlar) {
    const s = ham_satir.trim();
    if (s === "") continue;
    if (s.startsWith("# ") && baslik === null && acik === null) {
      baslik = s.slice(2).trim();
      continue;
    }
    if (s.startsWith("## ")) {
      if (acik !== null) bolumler.push(acik);
      acik = { baslik: s.slice(3).trim(), maddeler: [], duzYazi: [] };
      continue;
    }
    if (s.startsWith("- ") || s.startsWith("* ")) {
      const m = s.slice(2).trim();
      if (acik === null) kunye.push(m);
      else acik.maddeler.push(m);
      continue;
    }
    // TANIMADIĞIM SATIR YUTULMAZ: bulunduğu yerin düz yazısına düşer.
    if (acik === null) kunye.push(s);
    else acik.duzYazi.push(s);
  }
  if (acik !== null) bolumler.push(acik);

  return {
    baslik,
    kunye,
    bolumler,
    satirN: satirlar.length,
    karakterN: ham.length,
    bosBeyani,
  };
}

/** Sohbet yüzeyinin "kalıcı hafıza" balonu için: bölüm adı + madde sayısı. */
export function bolumOzeti(h: Hafiza): readonly { readonly baslik: string; readonly n: number }[] {
  return h.bolumler.map((b) => ({ baslik: b.baslik, n: b.maddeler.length }));
}
