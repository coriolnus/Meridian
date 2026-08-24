/* ============================================================================
   YAZI TİPİ KAYDI — studio-admin'in kaydı, KENDİ BAYTLARIMIZLA
   ----------------------------------------------------------------------------
   Şablonun özgün hâli 18 aileyi `next/font/google` ile çekiyordu. İKİ SEBEPLE
   olduğu gibi alınamaz ve ikisi de ÖLÇÜLDÜ, varsayılmadı:

     1. Next YOK. Bu uygulama Vite'ta derleniyor (karar: docs/KARAR-2026-08-25-
        D4-STUDIO-ADMIN-GOCU.md) — `next/font` bir Next derleyici eklentisidir.
     2. CSP dış font-host'a İZİN VERMEZ: canlı politika `font-src 'self'`
        (meridian/api.py::CSP_POLITIKASI). `fonts.gstatic.com` 2026-08-07'de
        BİLEREK düşürüldü; geri eklemek bir sertleştirmeyi geri almak olurdu.

   Bu yüzden kayıt, `meridian/web/fonts/` altındaki KENDİ kesitlerimize daralıyor.
   Yüz değiştirici (layout-controls) çalışmaya devam eder — yalnız listesi iki
   satır. Yeni bir yüz eklemenin yolu bu listeyi uzatmak DEĞİL, önce `.woff2`yi
   depoya koyup `api.py::_FONT_DOSYALARI`ya yazmaktır; aksi hâlde seçenek
   görünür ama seçildiğinde sistem yüzüne düşer.
   ============================================================================ */

export interface KayitliYuz {
  readonly label: string;
  /** `font-family` yığını — ilk ad `yazitipi.css`teki `@font-face` ile aynı olmalı. */
  readonly stack: string;
  /** `<html>` üzerine yazılan CSS değişkeni adı. */
  readonly variable: string;
}

export const fontRegistry = {
  inter: {
    label: "Inter",
    stack: "'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif",
    variable: "--font-inter",
  },
  recursiveMono: {
    label: "Recursive Mono",
    stack: "'Recursive Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
    variable: "--font-recursive-mono",
  },
} as const satisfies Record<string, KayitliYuz>;

export type FontKey = keyof typeof fontRegistry;

export const fontKeys = Object.keys(fontRegistry) as FontKey[];

export const fontOptions = fontKeys.map((key) => ({
  key,
  label: fontRegistry[key].label,
}));

/** `<body>` sınıfına eklenen değişken listesi — Next sürümünde üretilen sınıf
 *  adlarının yerini burada tek bir yardımcı alıyor; değişkenler `tema.css`te
 *  statik tanımlı olduğu için burada eklenecek sınıf YOK. */
export const fontVars = "";
