"use client";

/* ============================================================================
   ONAY KUYRUĞU + ÇİZELGE — ORTAK PARÇALAR
   ----------------------------------------------------------------------------
   İKİ YÜZEY TEK KLASÖRDE, çünkü ikisi de AYNI grameri konuşuyor: "bir iş kalemi,
   bir damga, bir hüküm". Onay kuyruğunda kalem senden iş ister; çizelgede kalem
   kendi kendine koşar. Aynı üç soru ikisinde de tekrarlanıyor — "istek düştü mü",
   "alan geldi mi", "damga ne kadar eski" — ve üçünü her bileşende elle yazmak,
   birinde unutulduğunda ekranın SESSİZCE yalan söylemesi demekti.

   NEDEN `sistem/parcalar.tsx`TEN İMPORT EDİLMEDİ (bilinçli tekrar, gerekçeli):
   bu tur paralel ajanlarla koşuyor ve dosya-ayrıklık sözleşmesi YAZMA tarafını
   ayırıyor. Başka bir ajanın uçuş hâlindeki dosyasından import etmek, o dosyanın
   dışa aktarım kümesi değiştiği an bu iki yüzeyi derlenemez hâle getirirdi —
   üstelik hatanın kaynağı benim yazmadığım bir dosyada görünürdü. Birleştirme bir
   TUR-KAPANIŞI işidir (tek `ortak/` klasörü), uçuş sırasındaki bir bağ değil.

   ÜÇÜNCÜ HÂL AYRI TUTULUR (veri.ts sözleşmesi): yükleniyor / oturum düştü /
   okunamadı / veri. "Oturum düştü"yü "okunamadı" diye göstermek operatörü ağa,
   sunucuya bakmaya gönderirdi; çaresi ise yalnız yeniden giriştir.
   ============================================================================ */
import type { ComponentType, ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { olculemediKur } from "../../parcalar/olculemedi";

/* --- BÖLÜM KABI --------------------------------------------------------- */

export function BolumKart({
  kimlik,
  baslik,
  soru,
  ikon: Ikon,
  aksiyon,
  children,
}: {
  /** Derin bağ çapası: `#/dashboard/tasks/onaylar` bu kimliği arar (`GenelYuzey.tsx` deseni). */
  readonly kimlik: string;
  readonly baslik: string;
  readonly soru: string;
  readonly ikon: ComponentType<{ className?: string }>;
  readonly aksiyon?: ReactNode;
  readonly children: ReactNode;
}) {
  return (
    <Card id={`bolum-${kimlik}`} className="scroll-mt-20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Ikon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          {baslik}
        </CardTitle>
        <CardDescription>{soru}</CardDescription>
        {aksiyon ? <CardAction>{aksiyon}</CardAction> : null}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">{children}</CardContent>
    </Card>
  );
}

/* --- ÜÇ HÂLİN KAPISI ---------------------------------------------------- */

/** Uç okunana kadar / okunamazsa ne çizileceği. `children` YALNIZ veri varken çağrılır.
 *  TANIM BURADA DEĞİL (TSK-113): tek kaynak `parcalar/kapi.tsx`; buradan yalnız yeniden dışa
 *  aktarılır. BEYANLI BEDEL: ortak kapı `iskelet?` prop'unu da kabul eder (bu yüzeyin eski
 *  gövdesinde yoktu, hiçbir çağrı yeri geçmiyor — çizim aynı). */
export { Kapi } from "../../parcalar/kapi";

/* --- UYDURMA YASAĞININ EKRAN KARŞILIĞI ---------------------------------- */

/** Ölçülemeyen değerin yeri. `neden` ZORUNLU — "—" tek başına yalandır.
 *  TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`, "satir"
 *  ailesi (22rem, altçizgi YOK — `sistem/parcalar.tsx` ile birebir). */
export const Olculemedi = olculemediKur("satir", { maxGenislik: "22rem", altCizgiTeknikte: false });

/** Sayı ya da "ölçülemedi". `undefined` = alan HİÇ gelmedi, `null` = ölçüldü sonuç yok. */
export function Deger({
  deger,
  birim = "",
  basamak = 0,
  neden,
  teknik,
  className,
}: {
  readonly deger: number | null | undefined;
  readonly birim?: string;
  readonly basamak?: number;
  readonly neden: string;
  readonly teknik?: string;
  readonly className?: string;
}) {
  if (deger === undefined || deger === null || !Number.isFinite(deger)) return <Olculemedi neden={neden} teknik={teknik} kisa />;
  return (
    <span className={cn("tabular-nums", className)}>
      {deger.toLocaleString("tr-TR", { minimumFractionDigits: basamak, maximumFractionDigits: basamak })}
      {birim}
    </span>
  );
}

/** Etiket + değer satırı — bölüm içi künye listelerinin tek biçimi. */
export function Satir({ etiket, children }: { readonly etiket: string; readonly children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b py-1.5 last:border-b-0">
      <span className="shrink-0 text-muted-foreground text-xs">{etiket}</span>
      <span className="min-w-0 text-right text-sm">{children}</span>
    </div>
  );
}

/** Basit KPI kutusu — şablonun `section-cards` kalıbının dar hâli (tek sayı + alt cümle). */
export function KpiKutu({
  etiket,
  children,
  altMetin,
  vurgu = false,
}: {
  readonly etiket: string;
  readonly children: ReactNode;
  readonly altMetin?: string;
  readonly vurgu?: boolean;
}) {
  return (
    <div className={cn("min-w-0 rounded-lg border p-3", vurgu && "border-amber-500/40 bg-amber-500/5")}>
      <div className="text-muted-foreground text-xs">{etiket}</div>
      <div className="mt-1 font-semibold text-xl tabular-nums">{children}</div>
      {altMetin ? <div className="mt-1 text-muted-foreground text-[11px] leading-4">{altMetin}</div> : null}
    </div>
  );
}

/* --- ZAMAN BİÇİMLEYİCİLERİ ---------------------------------------------- */

/** ISO damgası → yerel okunur metin. Ayrıştırılamayan/eksik damga için `null` (çağıran beyan eder). */
export function zamanMetni(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  return new Date(t).toLocaleString("tr-TR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** ISO damgası → YALNIZ TARİH. Saat taşımayan kaynaklar için: uydurma saat basmamanın yolu. */
export function tarihMetni(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  return new Date(t).toLocaleDateString("tr-TR", { year: "numeric", month: "2-digit", day: "2-digit" });
}

/** ISO damgası → epoch ms, ayrıştırılamazsa `null`. Yaş hesabının TEK kapısı. */
export function zamanMs(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  return Number.isFinite(t) ? t : null;
}

/** Saniye → "3g 4sa 12dk". Ölçülemeyen değer için `null`. */
export function sureMetni(s: number | null | undefined): string | null {
  if (s === undefined || s === null || !Number.isFinite(s)) return null;
  const isaret = s < 0 ? "-" : "";
  const v = Math.abs(s);
  const g = Math.floor(v / 86400);
  const sa = Math.floor((v % 86400) / 3600);
  const dk = Math.floor((v % 3600) / 60);
  const sn = Math.floor(v % 60);
  if (g > 0) return `${isaret}${g}g ${sa}sa`;
  if (sa > 0) return `${isaret}${sa}sa ${dk}dk`;
  if (dk > 0) return `${isaret}${dk}dk ${sn}sn`;
  return `${isaret}${sn}sn`;
}

/** "3sa 12dk önce" / "12dk sonra". `null` = damga ölçülemedi, çağıran `Olculemedi` çizer. */
export function goreliMetin(ms: number | null, simdi: number): string | null {
  if (ms === null) return null;
  const fark = (simdi - ms) / 1000;
  const metin = sureMetni(Math.abs(fark));
  if (metin === null) return null;
  return fark >= 0 ? `${metin} önce` : `${metin} sonra`;
}

/** ISO damgasının GÜN parçası (`YYYY-MM-DD`) — takvim işaretleri bunu anahtar olarak kullanır. */
export function gunAnahtari(iso: string | null | undefined): string | null {
  const ms = zamanMs(iso);
  if (ms === null) return null;
  const d = new Date(ms);
  const ay = `${d.getMonth() + 1}`.padStart(2, "0");
  const gun = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${ay}-${gun}`;
}

/* --- HÜKÜM ROZETİ -------------------------------------------------------- */

export type HukumTonu = "iyi" | "uyari" | "kotu" | "notr" | "olculemedi";

const TON_SINIFI: Record<HukumTonu, string> = {
  iyi: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  uyari: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
  kotu: "bg-destructive/10 text-destructive",
  notr: "bg-muted text-muted-foreground",
  olculemedi: "bg-muted text-muted-foreground italic",
};

const TON_NOKTASI: Record<HukumTonu, string> = {
  iyi: "bg-emerald-500",
  uyari: "bg-amber-500",
  kotu: "bg-destructive",
  notr: "bg-muted-foreground/50",
  olculemedi: "bg-muted-foreground/40",
};

/** Ton bir HÜKÜMDÜR; hükmün gerekçesi `baslik` (tooltip) olmadan çizilmez. */
export function HukumRozet({
  ton,
  metin,
  baslik,
  className,
}: {
  readonly ton: HukumTonu;
  readonly metin: string;
  readonly baslik: string;
  readonly className?: string;
}) {
  return (
    <Badge variant="secondary" className={cn("gap-1.5", TON_SINIFI[ton], className)} title={baslik}>
      <span className={cn("size-1.5 shrink-0 rounded-full", TON_NOKTASI[ton])} />
      {metin}
    </Badge>
  );
}
