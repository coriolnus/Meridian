/* ============================================================================
   MERIDIAN — EPİSTEMİK TİPLER (shadcn pilotu, G3 kapısı)
   ----------------------------------------------------------------------------
   Bu dosya pilotun ASIL sorusunu cevaplıyor: Meridian'ın çivileri görsel değil,
   EPİSTEMİK. shadcn bunlar hakkında hiçbir şey bilmez. Bileşen sınırına
   taşınabiliyorlar mı?

   Bugün bu kurallar `app.js`te YORUM + ÇİVİ ile korunuyor:
     · UYDURMA YASAĞI  — ölçülemeyen değer None döner ve NEDENİNİ taşır
     · PAYDA BEYANI    — paydasız çubuk yasak; okuru kendi uydurduğu tavana okutur
     · SIFIR ≠ YOK     — "ölçtük, sıfır çıktı" ile "ölçemedik" AYRI kutulardır

   Çivi bir ihlali TESPİT eder. Aşağıdaki tipler onu YAZILAMAZ kılar — fark bu,
   ve operatörün argümanının doğru olduğu yer tam burası.
   ============================================================================ */

/** Bir ölçüm ya bir SAYIDIR ya da ÖLÇÜLEMEMİŞTİR — ve ölçülememişse NEDENİ vardır.
 *
 *  Ayrık birleşim (discriminated union) bunu tipte zorunlu kılar:
 *  `{ deger: null }` YAZILAMAZ, çünkü `neden` eksiktir. `app.js`teki karşılığı
 *  `deger == null ? veriYok(neden) : ...` idi ve `neden`i unutmak SESSİZCE mümkündü
 *  ("veri yok" basılır, okur onu "sıfır" sanır). Burada derleyici durduruyor.
 */
export type Olcum =
  | { readonly deger: number; readonly neden?: never }
  | { readonly deger: null; readonly neden: string };

/** Bir oran ÇUBUĞA dönüşür — ama yalnız paydası beyan edilmişse.
 *
 *  `oran: 0`  → çubuk DOĞAR ve boş görünür  ("ölçtük, sıfır çıktı")
 *  `oran: null` → çubuk HİÇ DOĞMAZ          ("ölçemedik")
 *  Bu ikisi aynı şey değildir ve tip onları ayırır.
 *
 *  `payda` OPSİYONEL DEĞİLDİR. `payda?: string` yazılsaydı kural bir konvansiyona
 *  geri düşerdi ve ilk acelede atlanırdı — bugün panoda tam bunun izini bulduk
 *  ("huni `paydaBeyani` birinci adımın defterini yanlış adlandırıyor").
 */
export interface Kanit {
  readonly oran: number | null;
  readonly payda: string;
}

/** Rozet metni SÖZLÜKTEN gelir, serbest dizgeden değil.
 *
 *  Ölçüldü (2026-08-24): 103 çağrı yerinde 42 ayrı dizge vardı ve TEK eşik
 *  (`azOrnek`, n<10) ekranda BEŞ biçimde çıkıyordu — "AZ ÖRNEK" ×12, "az örnek" ×1,
 *  "AZ VERİ" ×3, ayrı sınıfla bir kez daha, düz cümleyle bir kez daha. Operatör
 *  bunu ekran görüntüsüyle bildirmek zorunda kaldı. Sözlük o çatalı YAZILAMAZ kılar.
 */
export const ROZET = {
  az_ornek: "AZ ÖRNEK",
  olculemedi: "ÖLÇÜLEMEDİ",
  bekliyor: "BEKLİYOR",
  sermaye_reset: "SERMAYE-RESET",
  pay_tanimsiz: "PAY TANIMSIZ",
} as const;

export type RozetAnahtari = keyof typeof ROZET;

/** "AZ ÖRNEK" eşiği TEK yerde ve bir KAPI DEĞİL — hiçbir karar bu sayıda değişmez,
 *  yalnız rozet doğar (görünürlük kuralı). `app.js`teki `AZ_ORNEK_N` ile aynı. */
export const AZ_ORNEK_N = 10;
export const azOrnek = (n: number): boolean => n < AZ_ORNEK_N;

/** İŞARET BİR HÜKÜM DEĞİLDİR — gürültü bandı.
 *
 *  `app.js:292-296`teki `signClass`ın birebir karşılığı ve gerekçesi de aynı:
 *  33 işlemde −0.035R KIRMIZI, 55 işlemde +0.031R YEŞİL boyanıyordu; ikisi de
 *  gürültü, ikisi de sıfırdan ayırt edilemez. Ortalama örneklem gürültüsünün
 *  (1/√n) İÇİNDE kalıyorsa hücre ne yeşil ne kırmızı — nötr mürekkep.
 *
 *  Operatör bunu "aynı anlam iki renkte" diye bildirdi; ölçüldü ve okuma YANLIŞTI
 *  (ikisi aynı anlam değil). AMA şikâyet geçerli bir okunabilirlik kusuruna işaret
 *  ediyordu: kural ekranda açıklanmıyordu. Pilot onu LEJANTLA açıklıyor — kuralı
 *  değil, görünürlüğünü düzelterek.
 */
export type YonSinifi = "arti" | "eksi" | "notr";

export function yonSinifi(ortalama: number | null, n: number): YonSinifi {
  if (ortalama == null || !n) return "notr";
  return Math.abs(ortalama) > 1 / Math.sqrt(n)
    ? (ortalama > 0 ? "arti" : "eksi")
    : "notr";
}

/** Gürültü bandının ekrandaki AÇIKLAMASI. Kural görünmezse okur onu tutarsızlık sanar. */
export function gurultuBandiAciklamasi(ortalama: number | null, n: number): string | null {
  if (ortalama == null || !n) return null;
  const bant = 1 / Math.sqrt(n);
  if (Math.abs(ortalama) > bant) return null;
  return `ortalama gürültü bandının içinde (|${ortalama.toFixed(2)}| ≤ 1/√${n} = ${bant.toFixed(3)}) — sıfırdan ayırt edilemez, renk taşımaz`;
}

/** Örneklem gücünün log ölçeği — TEK tanım (`app.js::kanitOrani` ile aynı).
 *  İki kopya, aynı n'in iki yüzeyde farklı doluluk çizmesi demekti. */
export const KANIT_TAVAN_N = 55;
export function kanitOrani(n: number): number | null {
  if (!Number.isFinite(n) || n <= 0) return null;
  return Math.min(1, Math.log10(1 + n) / Math.log10(1 + KANIT_TAVAN_N));
}
