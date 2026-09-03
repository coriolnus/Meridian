"use client";

/* ============================================================================
   SİSTEM SAĞLIĞI — ORTAK PARÇALAR
   ----------------------------------------------------------------------------
   Bu yüzeyin yedi bölümü AYNI üç soruyu tekrar tekrar soruyor: "istek düştü mü",
   "alan geldi mi", "gelen sayı ne anlama geliyor". Üçünü de her bölümde elle
   yazmak, birinde unutulduğunda ekranın SESSİZCE yalan söylemesi demekti — boş
   bir kart "ölçtük, hiçbir şey yok" diye okunur. Bu yüzden kapı da, "ölçülemedi"
   ibaresi de TEK yerde duruyor ve nedenini taşımadan çizilemiyor (tip zorluyor:
   `Olculemedi` `neden` olmadan derlenmez).

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

export interface BolumKartOzellikleri {
  /** `alanlar.ts`teki bölüm kimliği. Derin bağ çapası buna bağlı (`#/dashboard/infrastructure/market`). */
  readonly kimlik: string;
  readonly baslik: string;
  readonly soru: string;
  readonly ikon: ComponentType<{ className?: string }>;
  readonly aksiyon?: ReactNode;
  readonly children: ReactNode;
  readonly className?: string;
}

export function BolumKart({ kimlik, baslik, soru, ikon: Ikon, aksiyon, children, className }: BolumKartOzellikleri) {
  return (
    <Card id={`bolum-${kimlik}`} className={cn("scroll-mt-20", className)}>
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
 *  TANIM BURADA DEĞİL (TSK-113, 2026-09-03): yedi yüzey aynı gövdeyi kopyalıyordu — karar tek
 *  kaynakta (`parcalar/kapi.tsx`), çizim kabukta. Tüketicilerin import YOLU değişmesin diye
 *  ad buradan yeniden dışa aktarılır. */
export { Kapi } from "../../parcalar/kapi";

/* --- UYDURMA YASAĞININ EKRAN KARŞILIĞI ---------------------------------- */

/** Ölçülemeyen değerin yeri. `neden` ZORUNLU — "—" tek başına yalandır.
 *  TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`, "satir"
 *  ailesi (22rem, altçizgi YOK — `kuyruk/parcalar.tsx` ile birebir). */
export const Olculemedi = olculemediKur("satir", { maxGenislik: "22rem", altCizgiTeknikte: false });

/** Sayı ya da "ölçülemedi". `deger` undefined = alan HİÇ gelmedi, null = ölçüldü sonuç yok. */
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

/** Etiket + değer satırı — bölüm içi "künye" listelerinin tek biçimi. */
export function Satir({ etiket, children }: { readonly etiket: string; readonly children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b py-1.5 last:border-b-0">
      <span className="shrink-0 text-muted-foreground text-xs">{etiket}</span>
      <span className="min-w-0 text-right text-sm">{children}</span>
    </div>
  );
}

/* --- DURUM ROZETİ: ÜÇ DEĞERLİ (true / false / ölçülemedi) --------------- */

export type UcDeger = boolean | null | undefined;

/**
 * `ok` ÜÇ DEĞERLİDİR ve üçü de ekranda AYRI görünür. `undefined`/`null`ı "bozuk"
 * saymak sistemi olmadığı kadar kötü gösterirdi; "sağlam" saymak ise ölçülmemiş
 * bir bileşeni yeşile boyamak olurdu — ikisi de bu deponun birinci yasasını çiğner.
 */
export function OkRozet({
  ok,
  iyi = "sağlam",
  kotu = "bozuk",
  neden = "uç bu alanı döndürmüyor",
  teknik,
}: {
  readonly ok: UcDeger;
  readonly iyi?: string;
  readonly kotu?: string;
  readonly neden?: string;
  readonly teknik?: string;
}) {
  if (ok === undefined || ok === null) {
    return (
      <Badge variant="outline" className="gap-1.5" title={teknik ? `${neden} — ${teknik}` : neden}>
        <span className="size-1.5 rounded-full bg-muted-foreground/60" />
        {neden}
      </Badge>
    );
  }
  return (
    <Badge
      variant={ok ? "secondary" : "destructive"}
      className={cn("gap-1.5", ok && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400")}
    >
      <span className={cn("size-1.5 rounded-full", ok ? "bg-emerald-500" : "bg-destructive")} />
      {ok ? iyi : kotu}
    </Badge>
  );
}

/** Çekili/serbest kol rozeti — "çekili" BURADA kırmızı değil AMBER: durdurma bir arıza değil bir karardır. */
export function KolRozet({ cekili, cekiliMetin, serbestMetin }: { readonly cekili: UcDeger; readonly cekiliMetin: string; readonly serbestMetin: string }) {
  if (cekili === undefined || cekili === null) {
    return (
      <Badge variant="outline" className="gap-1.5">
        <span className="size-1.5 rounded-full bg-muted-foreground/60" />
        bilinmiyor
      </Badge>
    );
  }
  return (
    <Badge
      variant="secondary"
      className={cn(
        "gap-1.5",
        cekili
          ? "bg-amber-500/10 text-amber-700 dark:text-amber-400"
          : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
      )}
    >
      <span className={cn("size-1.5 rounded-full", cekili ? "bg-amber-500" : "bg-emerald-500")} />
      {cekili ? cekiliMetin : serbestMetin}
    </Badge>
  );
}

/* --- ÖLÇEK ÇUBUĞU (şablonun ResourceMeter'ı, eşikleri beyanlı) ---------- */

/**
 * Şablonun `ResourceMeter`ından alındı (infrastructure/_components/project-environments.tsx).
 * TEK FARK ve nedeni: eşikler (uyarı %70, kritik %85) BURADA yazılı ve tooltip'te
 * okunuyor — şablonda 55/70 gömülüydü ve hiçbir yerde beyan edilmiyordu. Renk bir
 * hükümdür; hükmün eşiği görünmeden verilmez.
 */
export function OlcekCubugu({
  etiket,
  yuzde,
  neden,
  teknik,
  uyari = 70,
  kritik = 85,
  altMetin,
}: {
  readonly etiket: string;
  readonly yuzde: number | null | undefined;
  readonly neden: string;
  readonly teknik?: string;
  readonly uyari?: number;
  readonly kritik?: number;
  readonly altMetin?: string;
}) {
  if (yuzde === undefined || yuzde === null || !Number.isFinite(yuzde)) {
    return (
      <div className="min-w-0 space-y-1">
        <div className="flex items-baseline justify-between gap-2 text-xs">
          <span className="font-medium text-muted-foreground">{etiket}</span>
        </div>
        <Olculemedi neden={neden} teknik={teknik} kisa />
      </div>
    );
  }
  const v = Math.max(0, Math.min(100, yuzde));
  const uyarida = v >= uyari;
  const kritikte = v >= kritik;
  return (
    <div className="min-w-0 space-y-1" title={`uyarı eşiği %${uyari} · kritik eşik %${kritik}`}>
      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="font-medium text-muted-foreground">{etiket}</span>
        <span
          className={cn(
            "font-medium text-emerald-600 tabular-nums dark:text-emerald-400",
            uyarida && "text-amber-600 dark:text-amber-400",
            kritikte && "text-destructive",
          )}
        >
          {v.toFixed(1)}%
        </span>
      </div>
      <span className="block h-1.5 overflow-hidden rounded-full bg-muted-foreground/20">
        <span
          className={cn(
            "block h-full rounded-full bg-emerald-500",
            uyarida && "bg-amber-500",
            kritikte && "bg-destructive",
          )}
          style={{ width: `${v}%` }}
        />
      </span>
      {altMetin ? <span className="block text-muted-foreground text-[11px] tabular-nums">{altMetin}</span> : null}
    </div>
  );
}

/* --- BİÇİMLEYİCİLER ------------------------------------------------------ */

/** Bayt → insan okuru. Ölçülemeyen değer için `null` döner; çağıran `Olculemedi` çizer. */
export function baytMetni(b: number | null | undefined): string | null {
  if (b === undefined || b === null || !Number.isFinite(b)) return null;
  const birimler = ["B", "KB", "MB", "GB", "TB", "PB"];
  let v = b;
  let i = 0;
  while (v >= 1024 && i < birimler.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(v >= 100 || i === 0 ? 0 : 1)} ${birimler[i] ?? "B"}`;
}

/** Saniye → "3g 4sa 12dk". Ölçülemeyen değer için `null`. */
export function sureMetni(s: number | null | undefined): string | null {
  if (s === undefined || s === null || !Number.isFinite(s) || s < 0) return null;
  const g = Math.floor(s / 86400);
  const sa = Math.floor((s % 86400) / 3600);
  const dk = Math.floor((s % 3600) / 60);
  const sn = Math.floor(s % 60);
  if (g > 0) return `${g}g ${sa}sa ${dk}dk`;
  if (sa > 0) return `${sa}sa ${dk}dk`;
  if (dk > 0) return `${dk}dk ${sn}sn`;
  return `${sn}sn`;
}

/** ISO damgası → yerel kısa metin. Ayrıştırılamayan damga `null` döner (uydurma yasağı). */
export function zamanMetni(iso: string | null | undefined): string | null {
  if (!iso || typeof iso !== "string") return null;
  const t = new Date(iso);
  if (Number.isNaN(t.getTime())) return null;
  return t.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "medium" });
}
