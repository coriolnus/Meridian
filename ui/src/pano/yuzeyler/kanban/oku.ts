/* ============================================================================
   OKUMA YARDIMCILARI — "alan YOK" ile "alan var, değeri boş" ayrı tutulur
   ----------------------------------------------------------------------------
   NEDEN BU DOSYA VAR: bu panonun uçları bir alanı ÖLÇEMEDİĞİNDE onu HİÇ YAZMIYOR
   (uydurma yasağının sunucu tarafı — CLAUDE.md §4). `p.score ?? 0` yazmak o
   sözleşmeyi istemcide bozar: ölçülmemiş bir skoru sıfır skor diye çizdirir.
   Aşağıdaki okuyucular alanın TÜRÜNÜ doğrular ve tutmuyorsa `null` döner; çağıran
   `null`u "ölçülemedi" diye YAZMAK zorunda, "0"a çevirmek değil.

   İkinci gerekçe: plan satırları (`trade_plans.jsonl`) ve yol haritası maddeleri
   HAM defter/belge satırlarıdır — alan kümesi zamanla büyümüş, eski satırlarda
   yeni alanlar yok. Şekli TAHMİN eden bir istemci, alan tutmadığında sessizce boş
   kart çizer ve bu ekranda "kayıt yok" yalanı olarak okunur. Okuyucular bunun
   yerine `null` döndürüp nedenin ekrana yazılmasını ZORUNLU kılıyor.
   ============================================================================ */

export function nesne(x: unknown): Record<string, unknown> | null {
  return typeof x === "object" && x !== null && !Array.isArray(x) ? (x as Record<string, unknown>) : null;
}

export function dizi(x: unknown): unknown[] | null {
  return Array.isArray(x) ? x : null;
}

export function metin(x: unknown): string | null {
  return typeof x === "string" && x.trim() !== "" ? x : null;
}

/** Sonlu sayı. `NaN`/`Infinity` ÖLÇÜM DEĞİLDİR — JSON'da bunlar `null` olarak gelir
 *  ama bir hesabın çıktısı olarak da doğabilir; ikisini de eleyip `null` diyoruz. */
export function sayi(x: unknown): number | null {
  return typeof x === "number" && Number.isFinite(x) ? x : null;
}

export function mantik(x: unknown): boolean | null {
  return typeof x === "boolean" ? x : null;
}

/** Dizideki METİN olan öğeler. Metin OLMAYAN öğeler düşürülür ve bu bilinçli:
 *  `gate_reasons` serbest metin listesidir (`loop.py:1894` onu düz cümlelerle
 *  dolduruyor); içine düşen bir nesneyi "[object Object]" diye ekrana basmak
 *  gerekçeyi okunmaz kılardı. Tek çağıran `planlar.ts` ve orada bu liste yalnız
 *  GÖSTERİM içindir — hiçbir sayaç ondan türemiyor, yani düşen öğe bir ölçümü
 *  bozmuyor. */
export function metinDizisi(x: unknown): string[] | null {
  const d = dizi(x);
  if (!d) return null;
  return d.filter((e): e is string => typeof e === "string" && e.trim() !== "");
}

/** `2026-08-25` → `25 Ağu`. Ayrıştırılamayan damga OLDUĞU GİBİ geri döner —
 *  "geçersiz tarih" yazmak yerine ham değeri göstermek operatöre daha çok şey söyler. */
const AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"] as const;
export function kisaTarih(g: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(g);
  if (!m) return g;
  const ay = AYLAR[Number(m[2]) - 1];
  if (!ay) return g;
  return `${Number(m[3])} ${ay}`;
}
