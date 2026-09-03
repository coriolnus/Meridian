"use client";

/* ============================================================================
   AJAN YÜZEYİNİN ORTAK PARÇALARI — ham JSONL'i tipli okumak + üç hâl kapısı
   ----------------------------------------------------------------------------
   NEDEN HER ALAN OPSİYONEL: `/api/agent.hypotheses` ve `/api/memory.hypotheses`
   aynı kaynağı servis ediyor — `state/hypotheses.jsonl` satırlarını OLDUĞU GİBİ
   (`memory.all_hypotheses()` → `store.read_jsonl`, dönüşüm YOK). Yani gövde bir
   şema değil, bir DEFTER: satırlar zaman içinde alan kazanmış.

   ÖLÇÜM (2026-08-25, `state/hypotheses.jsonl`, 41 satır, ts 2026-07-14 → 2026-07-29):
     · her satırda var  : variable, old, new, rationale, predicted_direction,
                          predicted_delta, confidence, regime, source, version_from,
                          version_to, status, id, ts, market_regime   (41/41)
     · çoğunda var      : reject_reasons 39/41 · backtest 19/41
     · NADİR            : status_ts 2 · note 2 · overfit_suspect 2
     · BİR TANE         : realized_delta / realized_detail / calibration_hit /
                          outcome_ts / vs_benchmark_at_ship  (1/41 — H00026)
   Bu son satır bu yüzeyin en önemli ölçümüdür: defterin NEREDEYSE TAMAMI sonucu
   yazılmamış tahminlerden oluşuyor. Eksik alanı 0 basan bir tablo, 41 tahminin
   41'ini "gerçekleşen fark: 0" diye okuturdu — 40'ı için bu düpedüz uydurma.

   Bu yüzden okuyucular DEĞER YOK ile DEĞER null'ı ayırıyor: `deger()` alan hiç
   yoksa `null`, varsa ve null ise `"null"` dizgesini döndürür.
   ============================================================================ */

import { Info, LockKeyhole, TriangleAlert } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { Bildiri } from "../../parcalar/bildiri";
import { type AdEki, kapiKur } from "../../parcalar/kapi";
import { olculemediKur } from "../../parcalar/olculemedi";

/* ---- HAM OKUYUCULAR ------------------------------------------------------ */

export function nesne(v: unknown): Readonly<Record<string, unknown>> | null {
  return typeof v === "object" && v !== null && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : null;
}

export function dizi(v: unknown): readonly unknown[] {
  return Array.isArray(v) ? (v as unknown[]) : [];
}

export function metin(v: unknown): string | null {
  return typeof v === "string" && v.trim() !== "" ? v : null;
}

export function say(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

/** ALAN YOK ile ALAN null AYRI: birincisi "hiç yazılmamış", ikincisi "yazılmış, boş".
 *  İkisini tek "—"ye indirgemek defterin en bilgi taşıyan farkını silerdi. */
export function deger(v: unknown): string | null {
  if (v === undefined) return null;
  if (v === null) return "null";
  if (typeof v === "number") return Number.isFinite(v) ? bicimSayi(v, 4) : String(v);
  if (typeof v === "string") return v;
  if (typeof v === "boolean") return v ? "true" : "false";
  return JSON.stringify(v);
}

const BICIMLER = new Map<string, Intl.NumberFormat>();

function bicimci(basamak: number, isaretli: boolean): Intl.NumberFormat {
  const k = `${basamak}|${isaretli}`;
  let b = BICIMLER.get(k);
  if (!b) {
    b = new Intl.NumberFormat("tr-TR", {
      maximumFractionDigits: basamak,
      signDisplay: isaretli ? "exceptZero" : "auto",
    });
    BICIMLER.set(k, b);
  }
  return b;
}

export function bicimSayi(v: number, basamak = 2, isaretli = false): string {
  return bicimci(basamak, isaretli).format(v);
}

/** Sayıysa biçimli dizge, DEĞİLSE null — çağıranı "ölçülemedi" yazmaya zorlar. */
export function sayiMetni(v: unknown, basamak = 2, isaretli = false): string | null {
  const n = say(v);
  return n === null ? null : bicimSayi(n, basamak, isaretli);
}

/** ISO damgası → yerel okunur biçim. Ayrıştırılamayan damga GİZLENMEZ, ham döner. */
export function zamanMetni(iso: string | null): string | null {
  if (iso === null) return null;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  return new Date(t).toLocaleString("tr-TR", { dateStyle: "medium", timeStyle: "short" });
}

export function gunMetni(iso: string | null): string | null {
  if (iso === null) return null;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  return new Date(t).toLocaleDateString("tr-TR", { dateStyle: "long" });
}

/** YALNIZ saat — mesajlaşma gramerinde satır sonundaki damga. Gün bilgisini
 *  ayraç taşıyor; her balonda tam tarih tekrar etmek gürültüdür. Ayrıştırılamayan
 *  damga GİZLENMEZ, ham döner (çağıran onu ham olarak işaretler). */
export function saatMetni(iso: string | null): string | null {
  if (iso === null) return null;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  return new Date(t).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}

/* ---- HİPOTEZ SATIRI ------------------------------------------------------ */

export interface Hipotez {
  readonly ham: Readonly<Record<string, unknown>>;
  readonly id: string | null;
  readonly ts: string | null;
  readonly degisken: string | null;
  /** `old` alanı; hiç yoksa null, yazılıp boşsa `"null"`. */
  readonly eski: string | null;
  readonly yeni: string | null;
  /** Ajanın kendi cümlesi — sohbetin gövdesi budur. */
  readonly gerekce: string | null;
  readonly durum: string | null;
  /** `deterministic` · `hermes:gemini` · `hermes:nous` · `coordinate_search` … */
  readonly kaynak: string | null;
  readonly rejim: string | null;
  readonly piyasaRejimi: string | null;
  readonly guven: number | null;
  readonly tahminDelta: number | null;
  readonly tahminYon: string | null;
  readonly gerceklesenDelta: number | null;
  readonly kalibrasyonIsabet: boolean | null;
  readonly redNedenleri: readonly string[];
  readonly not: string | null;
  readonly surumDen: string | null;
  readonly surumE: string | null;
  readonly backtestVar: boolean;
  readonly asiriUyumSupheli: boolean | null;
}

export function hipotezOku(v: unknown): Hipotez | null {
  const h = nesne(v);
  if (h === null) return null;
  const kal = h["calibration_hit"];
  const asiri = h["overfit_suspect"];
  return {
    ham: h,
    id: metin(h["id"]),
    ts: metin(h["ts"]),
    degisken: metin(h["variable"]),
    eski: deger(h["old"]),
    yeni: deger(h["new"]),
    gerekce: metin(h["rationale"]),
    durum: metin(h["status"]),
    kaynak: metin(h["source"]),
    rejim: metin(h["regime"]),
    piyasaRejimi: metin(h["market_regime"]),
    guven: say(h["confidence"]),
    tahminDelta: say(h["predicted_delta"]),
    tahminYon: metin(h["predicted_direction"]),
    gerceklesenDelta: say(h["realized_delta"]),
    kalibrasyonIsabet: typeof kal === "boolean" ? kal : null,
    // Neden dizgeye zorluyoruz: `reject_reasons` ölçülen 39 satırda dizge listesi,
    // ama defterin şeması yok — sayı/nesne gelirse yutmak yerine yazıya çeviriyoruz.
    redNedenleri: dizi(h["reject_reasons"]).map((r) => (typeof r === "string" ? r : JSON.stringify(r))),
    not: metin(h["note"]),
    surumDen: deger(h["version_from"]),
    surumE: deger(h["version_to"]),
    backtestVar: nesne(h["backtest"]) !== null,
    asiriUyumSupheli: typeof asiri === "boolean" ? asiri : null,
  };
}

/** Defterin görsel sözlüğü. Bilinmeyen durum SESSİZCE YUTULMAZ: `null` dönüşü
 *  çağırana "bu durumu tanımıyorum" dedirtir, nötr rozetle çizilir. */
export const DURUM_SOZLUGU: Readonly<
  Record<string, { readonly etiket: string; readonly ton: "olumlu" | "olumsuz" | "notr" }>
> = {
  proposed: { etiket: "önerildi", ton: "notr" },
  live: { etiket: "canlıya alındı", ton: "olumlu" },
  promoted: { etiket: "terfi etti", ton: "olumlu" },
  shipped: { etiket: "sevk edildi", ton: "olumlu" },
  superseded: { etiket: "aşıldı", ton: "notr" },
  rolled_back: { etiket: "geri alındı", ton: "olumsuz" },
  rejected_by_backtest: { etiket: "backtest reddetti", ton: "olumsuz" },
  rejected_by_guard: { etiket: "bekçi reddetti", ton: "olumsuz" },
  rejected_by_confirmation: { etiket: "teyit reddetti", ton: "olumsuz" },
};

/* ---- ÖLÇÜLEMEDİ ----------------------------------------------------------
   TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`. Bu yüzeyin
   gövdesi "span" ailesinin "altcizgi" stili — her zaman altçizgili, `className` alır. */
export const Olculemedi = olculemediKur("span", { stil: "altcizgi" });

/** Değer varsa yazar, yoksa nedeni taşıyan "ölçülemedi" basar. */
export function Deger({
  metin: m,
  neden,
  teknik,
  className,
}: {
  metin: string | null;
  neden: string;
  teknik?: string;
  className?: string;
}) {
  if (m === null) return <Olculemedi neden={neden} teknik={teknik} />;
  return <span className={className}>{m}</span>;
}

export function OlculemediBlok({ baslik, neden, teknik }: { baslik: string; neden: string; teknik?: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border border-dashed bg-muted/30 p-4">
      <Info className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
      <div className="min-w-0">
        <p className="font-medium text-sm">{baslik}</p>
        <p className="mt-0.5 break-words text-muted-foreground text-xs leading-relaxed" title={teknik}>
          {neden}
        </p>
      </div>
    </div>
  );
}

/* ---- DÖRT HÂL KAPISI -----------------------------------------------------
   `Bildiri` TANIMI BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/bildiri.tsx`.
   Eski `{govde, uyari: boolean}` çifti ortak `{metin, tonu: "uyari"|"notr"}` sözleşmesine
   ÇAĞRI YERİNDE eşlenir (`metin=govde`, `tonu=uyari?"uyari":"notr"`) — markup zaten birebirdi,
   fark yalnız prop adlarındaydı. */

/** Yükleniyor / okunamadı / oturum düştü / bayat-ama-var — dördü AYRI çare ister.
 *  TANIM BURADA DEĞİL (TSK-113, 2026-09-03): yedi yüzey aynı `Kapi<T>` gövdesini kopyalıyordu.
 *  KARAR tek kaynakta (`parcalar/kapi.tsx`), ÇİZİM burada — bu yüzeyin metinleri kendisinindir,
 *  sıra ortaktır. `bayat` verildiği için hata veriyi EZMEZ: veri varken şerit olur (A ailesinin
 *  `Alert` kapıları bunun tersini yapar ve bu ayrım kabuktan türetilir). */
export const Kapi = kapiKur<AdEki>({
  oturum: ({ ad }) => (
    <Bildiri
      ikon={LockKeyhole}
      tonu="notr"
      baslik="Oturum düştü"
      metin={`${ad} 401 döndü. Bu bir veri arızası DEĞİL — pano parola kapısının arkasında, yeniden giriş gerekiyor.`}
    />
  ),
  bos: (hata, { ad }) => (
    <Bildiri
      ikon={TriangleAlert}
      tonu="uyari"
      baslik={`${ad} okunamadı`}
      metin={hata ?? `${ad} ne tamamlandı ne düştü — bu boş bir sonuç DEĞİL.`}
    />
  ),
  iskelet: ({ yukseklik = "h-40" }) => (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className={cn("w-full", yukseklik)} />
    </div>
  ),
  // BAYAT AMA ÇİZİLİYOR: bir ağ hıçkırığında ekranı boşaltmak da, bayatı taze
  // diye okutmak da yanlış. Üçüncü yol: çiz + damgala (veri.ts'in sözleşmesi).
  bayat: (hata, zaman) => (
    <div className="mb-3 flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2">
      <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
      <p className="min-w-0 break-words text-amber-700 text-xs leading-relaxed dark:text-amber-300">
        Tazeleme düştü — aşağısı{" "}
        {zaman ? `${zaman.toLocaleTimeString("tr-TR")} okumasından` : "önceki bir okumadan"} kalma,
        ŞU ANI göstermiyor. {hata}
      </p>
    </div>
  ),
});
