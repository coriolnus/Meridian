"use client";

/* ============================================================================
   ANALİZ YÜZEYİNİN ORTAK PARÇALARI — üç hâl kapısı + dürüst sayı basımı
   ----------------------------------------------------------------------------
   BU DOSYANIN VAR OLMA NEDENİ TEK: "ölçülemedi" ile "sıfır" bu yüzeyde ASLA aynı
   piksele düşmesin. Yüzey altı bileşene bölündü ve her biri kendi kartında sayı
   basıyor; kural her dosyada yeniden yazılsaydı biri unutur, o kart sessizce 0
   yazardı — ve 0, okuyucuya "ölçtük, sonuç bu" der.

   `Kapi` ÜÇ HÂLİ AYRI KARŞILAR (veri.ts'in sözleşmesi): yükleniyor / okunamadı /
   oturum düştü. Dördüncü bir hâl daha var ve o da burada: ELDE ESKİ VERİ VARKEN
   tazeleme düşmüş. O durumda kart boşaltılmaz (bir ağ hıçkırığında ekrandaki her
   sayı kaybolurdu) ama TAZE de sayılmaz — üstüne bayat şeridi çizilir.
   ============================================================================ */
import { LockKeyhole, TriangleAlert } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { type AdEki, kapiKur } from "../../parcalar/kapi";

/* ---- SAYI BASIMI --------------------------------------------------------- */

// Intl örneği pahalı; basamak başına bir kez kurulur. (Ölçüm değil, bilinen maliyet.)
const BICIMLER = new Map<string, Intl.NumberFormat>();

function bicim(basamak: number, isaretli: boolean): Intl.NumberFormat {
  const anahtar = `${basamak}|${isaretli}`;
  let b = BICIMLER.get(anahtar);
  if (!b) {
    b = new Intl.NumberFormat("tr-TR", {
      minimumFractionDigits: basamak,
      maximumFractionDigits: basamak,
      signDisplay: isaretli ? "exceptZero" : "auto",
    });
    BICIMLER.set(anahtar, b);
  }
  return b;
}

/** Sayıysa biçimlenmiş dizge, DEĞİLSE `null`. `null` dönüşü çağıranı "ölçülemedi"
 *  yazmaya ZORLAR — burada "—" ya da "0" döndürmek yasağın tam ihlali olurdu. */
export function sayi(v: unknown, basamak = 2, isaretli = false): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return bicim(basamak, isaretli).format(v);
}

/** Oran (0..1) → yüzde. Türkçe biçimde işaret ÖNDE: `%61,4`. */
export function yuzde(v: unknown, basamak = 1, isaretli = false): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  const s = bicim(basamak, isaretli).format(v * 100);
  return s.startsWith("-") ? `-%${s.slice(1)}` : `%${s}`;
}

/** R katı — defterin kendi birimi, bu yüzden ayrı bir basım. */
export function rKati(v: unknown, basamak = 2): string | null {
  const s = sayi(v, basamak, true);
  return s === null ? null : `${s}R`;
}

export function para(v: unknown): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return `$${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(v)}`;
}

/** Kâr/zarar rengi. `null`/0 için NÖTR: sıfırı yeşile boyamak "kazandık" der. */
export function pnlRengi(v: unknown): string {
  if (typeof v !== "number" || !Number.isFinite(v) || v === 0) return "text-foreground";
  return v > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400";
}

/* ---- ÖLÇÜLEMEDİ ---------------------------------------------------------- */

/** Blok biçimi: nedeni GÖRÜNÜR yazar. Kart gövdesinde kullanılır. */
export function Olculemedi({ neden, teknik, className }: { neden: string; teknik?: string; className?: string }) {
  return (
    <span className={cn("flex flex-col gap-0.5", className)}>
      <span className="text-muted-foreground text-sm italic" title={teknik}>
        {neden}
      </span>
    </span>
  );
}

/** Satır-içi biçim: dar hücrede nedeni `title` ile taşır (noktalı altı çizgi =
 *  "üstüne gel"). Nedeni tamamen düşürmek yasak; yalnız yerleşimi değişir. */
export function OlculemediHucre({ neden, teknik }: { neden: string; teknik?: string }) {
  return (
    <span
      className="cursor-help text-muted-foreground text-xs underline decoration-dotted underline-offset-2"
      title={teknik ? `${neden} — ${teknik}` : neden}
    >
      {neden}
    </span>
  );
}

/** Sayı varsa yazar, yoksa `neden`i taşıyan "ölçülemedi" basar. */
export function Deger({
  metin,
  neden,
  teknik,
  className,
}: {
  metin: string | null;
  neden: string;
  teknik?: string;
  className?: string;
}) {
  if (metin === null) return <OlculemediHucre neden={neden} teknik={teknik} />;
  return <span className={className}>{metin}</span>;
}

/* ---- ÜÇ (DÖRT) HÂL KAPISI ------------------------------------------------ */

function Bildiri({
  ikon: Ikon,
  baslik,
  metin,
  tonu,
}: {
  ikon: typeof TriangleAlert;
  baslik: string;
  metin: string;
  tonu: "uyari" | "notr";
}) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border border-dashed p-4",
        tonu === "uyari" ? "border-destructive/40 bg-destructive/5" : "border-border bg-muted/30",
      )}
    >
      <Ikon
        className={cn("mt-0.5 size-4 shrink-0", tonu === "uyari" ? "text-destructive" : "text-muted-foreground")}
        aria-hidden
      />
      <div className="min-w-0">
        <p className="font-medium text-sm">{baslik}</p>
        <p className="mt-0.5 break-words text-muted-foreground text-xs leading-relaxed">{metin}</p>
      </div>
    </div>
  );
}

export function YukleniyorIskeleti({ yukseklik = "h-40" }: { yukseklik?: string }) {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className={cn("w-full", yukseklik)} />
    </div>
  );
}

/** Tazeleme düştü ama elde ESKİ veri var — çizilir, "taze" DENMEZ. */
function BayatSerit({ hata, zaman }: { hata: string; zaman: Date | null }) {
  return (
    <div className="mb-3 flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2">
      <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
      <p className="min-w-0 break-words text-amber-700 text-xs leading-relaxed dark:text-amber-300">
        Tazeleme düştü — aşağıdaki sayılar{" "}
        {zaman ? `${zaman.toLocaleTimeString("tr-TR")} okumasından` : "önceki bir okumadan"} kalma, ŞU ANI göstermiyor.{" "}
        {hata}
      </p>
    </div>
  );
}

/** Yükleniyor / okunamadı / oturum düştü / bayat-ama-var — dördü AYRI çare ister.
 *  TANIM BURADA DEĞİL (TSK-113, 2026-09-03): yedi yüzey aynı `Kapi<T>` gövdesini kopyalıyordu.
 *  KARAR tek kaynakta (`parcalar/kapi.tsx`), ÇİZİM burada — bu yüzeyin metinleri ve `Bildiri`
 *  kabuğu kendisinindir, sıra ortaktır. `bayat` verildiği için hata veriyi EZMEZ: veri varken
 *  şerit olur (A ailesinin `Alert` kapıları bunun tersini yapar ve bu ayrım kabuktan türetilir). */
export const Kapi = kapiKur<AdEki>({
  oturum: ({ ad }) => (
    <Bildiri
      ikon={LockKeyhole}
      tonu="notr"
      baslik="Oturum düştü"
      metin={`${ad} okunamıyor: sunucu 401 döndü. Bu bir veri arızası DEĞİL — yeniden giriş gerekiyor.`}
    />
  ),
  bos: (hata, { ad }) => (
    <Bildiri
      ikon={TriangleAlert}
      tonu="uyari"
      baslik={`${ad} okunamadı`}
      metin={hata ?? `${ad} boş gövde döndürdü — çizilecek bir şey yok ve nedeni uçtan gelmedi.`}
    />
  ),
  iskelet: ({ yukseklik }) => <YukleniyorIskeleti yukseklik={yukseklik} />,
  bayat: (hata, zaman) => <BayatSerit hata={hata} zaman={zaman} />,
});
