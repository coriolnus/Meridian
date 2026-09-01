/* ============================================================================
   HUNİ ÇEKİRDEĞİ — REACT'SİZ VE GERÇEKTEN ÇAĞRILABİLİR
   ----------------------------------------------------------------------------
   NEDEN AYRI DOSYA: huninin GRAMERİ (basamak tipi, taban kuralı, payda neden
   yok sorusu) bir çizim ayrıntısı değil bir DOĞRULUK sözleşmesidir. `Huni.tsx`
   JSX taşıdığı ve `@/components/ui/*` takma adına bağlandığı için node'da
   çağrılamaz — yani o sözleşme bugüne dek yalnız kaynak METNİNE bakan çivilerle
   ölçülebilirdi. Metin çivisi, ifadeyi bozan ama adı koruyan mutasyonda ISIRMAZ
   (v347 incelemesinin B4 dersi). Çekirdek burada saf duruyor: çiviler onu
   ÇAĞIRIYOR, okumuyor.

   TABAN KURALI NEDEN BURADA: `Huni` şeridin genişliğini ilk basamağa göre
   çiziyor, kartlar ise DÜŞÜŞ oranlarını aynı tabana bölüyordu — aynı kuralın iki
   kopyası. Bugün aynılardı; yarın biri "0 da tabandır" derse şerit ile yüzdeler
   SESSİZCE ayrışır (tek-kaynak yasası). Tek tanım, iki okuyucu.

   TİPLER DE BURADA, `Huni.tsx` onları YENİDEN DIŞA VERİYOR: mevcut çağrı yerleri
   (`KararZinciri`, `HukumDagilimi`) ithal yolunu değiştirmeden çalışsın diye.
   ============================================================================ */

/* ---- TİPLER ---------------------------------------------------------------
   Basamak ayrık birleşim (`src/meridian/olcum.ts::Olcum` ile aynı desen):
   `{ n: null }` NEDEN'siz YAZILAMAZ. Konvansiyon değil, derleyici tutuyor. */

export type HuniBasamagi =
  | { readonly ad: string; readonly n: number; readonly neden?: never }
  | { readonly ad: string; readonly n: null; readonly neden: string };

/** İki basamak ARASINDA eriyen küme — "Nerede, neden elendi" satırı.
 *  `app.js`teki `dususler` kaydıyla aynı alanlar: ok · metin · oran (+ neden). */
export interface HuniDususu {
  /** "Kurulan plan → Kapıyı geçen" */
  readonly ok: string;
  /** Eriyen kümenin ADIYLA anlatımı: "3 plan kapıda takıldı · kapı: 3 NO_GO" */
  readonly metin: string;
  /** Tabana göre eriyen oran. null → payda ya da sayı ölçülemedi. */
  readonly oran: number | null;
  /** `oran === null` iken NEDEN. Nedensiz boşluk okuyucuya "sıfır" diye okunur. */
  readonly neden?: string;
}

/** Bu huninin SEANSI — hangi güne ait ve sayıları hangi defter verdi. */
export interface HuniSeansi {
  /** Kayıttan OKUNAN damga (`2026-08-21`). null → damga ölçülemedi. */
  readonly damga: string | null;
  /** `damga === null` iken NEDEN. Tahmini tarih UYDURULMAZ. */
  readonly neden?: string;
  /** Tek satırlık kaynak beyanı — hangi defterden sayıldı. */
  readonly kaynak: string;
}

/** Aynı soruyu BAŞKA bir defterden cevaplayan kardeş kart. İki damga yan yana
 *  görünmezse okuyucu iki farklı sayının hangi güne ait olduğunu ANLAYAMAZ. */
export interface HuniKarsiKart {
  /** Ekrandaki adı — "Bugün · Hüküm dağılımı" */
  readonly ad: string;
  readonly damga: string | null;
  readonly neden?: string;
  readonly kaynak: string;
}

/* ---- TABAN ---------------------------------------------------------------- */

/** TABAN = İLK BASAMAK. Yüzdeler ve şerit genişliği buna göredir.
 *  "0" ile "ölçülemedi" AYRI olgulardır; ikisi de payda OLAMAZ ama sebepleri
 *  farklıdır ve o fark `tabanNedeni` ile söylenir — burada sessizce eşitlenmez. */
export function huniTabani(basamaklar: readonly HuniBasamagi[]): number | null {
  const ilk = basamaklar[0];
  return ilk !== undefined && ilk.n !== null && ilk.n > 0 ? ilk.n : null;
}

/** PAYDA NEDEN YOK — ÜÇ AYRI OLGU, ÜÇ AYRI CÜMLE (ölçülmüş vaka 2026-08-31).
 *  Eskiden tek metin vardı ("ilk basamak yazılı değil") ve 0 aday çıkan bir gece
 *  operatöre "hiç tarama olmadı" diye okundu — oysa döngü koşmuş, sayı ÖLÇÜLMÜŞ
 *  ve sıfır çıkmıştı. Taban varsa `null` döner (söylenecek bir kusur yok). */
export function tabanNedeni(basamaklar: readonly HuniBasamagi[]): string | null {
  const ilk = basamaklar[0];
  if (ilk === undefined) return "huninin ilk basamağı hiç yok — payda kurulamadı";
  if (ilk.n === null) return `ilk basamak ölçülemedi (${ilk.neden}) — oranların paydası yok`;
  if (ilk.n === 0) return `${ilk.ad} 0 — oran hesaplanamaz (payda 0); ölçüm YAPILDI, sonuç sıfır çıktı`;
  return null;
}
