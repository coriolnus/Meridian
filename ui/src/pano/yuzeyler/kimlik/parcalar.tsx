"use client";

/* ============================================================================
   KİMLİK / OPERATÖR — ORTAK PARÇALAR
   ----------------------------------------------------------------------------
   ÇAKIŞMA KAYDI (2026-08-25, silinmesin): bu dosya tur sırasında BİR KEZ başka bir
   ajan tarafından yazıldı — Kullanıcılar/Roller turunu koşan ajan `yuzeyler/kimlik/`
   klasörünü boş sanıp buraya kendi `parcalar.tsx`ini bıraktı ve özgün gövdeyi ezdi.
   Dosya git'te izlenmediği için geri alınamadı; aşağıdaki gövde kimlik/operatör
   turunun KENDİ sürümüdür ve o ajanın bıraktığı notta istediği gibi üzerine
   yazılmıştır (birleştirme değil, sahiplik). Kayıt burada duruyor çünkü dosya-ayrıklık
   sözleşmesinin nerede sızdığını tek gösteren şey bu satırlar.

   NE İŞE YARAR: iki yüzey (Giriş · Operatör) aynı üç soruyu tekrar tekrar soruyor —
   "istek düştü mü", "alan geldi mi", "gelen değer ne anlama geliyor". Üçünü her
   bölümde elle yazmak, birinde unutulduğunda ekranın SESSİZCE yalan söylemesi
   demekti: boş bir hücre "ölçtük, hiçbir şey yok" diye okunur. Bu yüzden kapı da
   "ölçülemedi" ibaresi de TEK yerde ve nedenini taşımadan çizilemiyor — tip
   zorluyor, `Olculemedi` `neden` olmadan derlenmez.

   BU KAYIT 2026-09-03'te DÜZELTİLDİ (TSK-113): eskiden burada "`sistem/parcalar.tsx` aynı
   deseni taşıyor ve oradan İTHAL EDİLMEDİ — sahiplik ayrık" yazıyordu. O gerekçe ölçümle
   çürüdü: yedi yüzey aynı `Kapi<T>` gövdesini kopyalamış ve dört ayrı gövdeye ayrışmıştı
   (tek-kaynak yasası, §4). Kapının KARARI artık `parcalar/kapi.tsx`te — hiçbir yüzeyin
   yazma alanında değil; ÇİZİM kabukla enjekte edildiği için sahiplik yine ayrık kaldı.
   Bu yüzeyin tek farkı (401 cümlesindeki "(Giriş yüzeyi)" eki) bir kabuk parametresidir.
   ============================================================================ */
import type { ComponentType, ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { kapiKur, yolKabugu } from "../../parcalar/kapi";
import { olculemediKur } from "../../parcalar/olculemedi";

/* --- BÖLÜM KABI --------------------------------------------------------- */

/** Bölüm kartı. `kimlik` İSTEĞE BAĞLI: derin bağ çapası olan bölümler onu verir
 *  (`#/dashboard/profile/tercihler`), tek parçalı kartlar vermez. */
export function BolumKart({
  kimlik,
  baslik,
  soru,
  ikon: Ikon,
  aksiyon,
  children,
  className,
}: {
  readonly kimlik?: string;
  readonly baslik: string;
  readonly soru: string;
  readonly ikon: ComponentType<{ className?: string }>;
  readonly aksiyon?: ReactNode;
  readonly children: ReactNode;
  readonly className?: string;
}) {
  return (
    <Card id={kimlik ? `bolum-${kimlik}` : undefined} className={cn("scroll-mt-20", className)}>
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

/* --- ÜÇ HÂLİN KAPISI (veri.ts sözleşmesi) ------------------------------- */

/**
 * `children` YALNIZ veri varken çağrılır. Dört hâl AYRI çizilir çünkü çareleri
 * ayrı: yeniden giriş / ağa bakmak / beklemek / okumak.
 *
 * TANIM BURADA DEĞİL (TSK-113): tek kaynak `parcalar/kapi.tsx`. Bu yüzeyin TEK farkı 401
 * cümlesinin "(Giriş yüzeyi)" ekiydi — kopya gerekçesi değil, kabuk parametresi.
 */
export const Kapi = kapiKur(yolKabugu(" (Giriş yüzeyi)"));

/* --- UYDURMA YASAĞININ EKRAN KARŞILIĞI ---------------------------------- */

/** Ölçülemeyen değerin yeri. `neden` ZORUNLU — tek başına "—" yalandır. */
/** Dürüst boşluk — İKİ KATMAN (2026-08-26 sözleşmesi, bkz. ogrenme/ortak.tsx):
 *  `neden` İNSAN CÜMLESİdir ve görünür; `teknik` iç ayrıntıdır ve üstüne gelince çıkar.
 *  "ölçülemedi — " öneki KALKTI: 178 yerde aynı kelime, hiçbirinde ne olduğunu
 *  söylemiyordu. Çivi: tests/test_arayuz_dili_v323.py.
 *  TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`, "satir"
 *  ailesi — bu yüzeyin farkı (`yetki`ye göre) `teknik` varken altçizgi EK DALI taşımasıdır. */
export const Olculemedi = olculemediKur("satir", { maxGenislik: "20rem", altCizgiTeknikte: true });

/** Sayı ya da "ölçülemedi". `undefined` = alan HİÇ gelmedi, `null` = ölçüldü sonuç yok. */
export function Deger({
  deger,
  onek = "",
  birim = "",
  basamak = 0,
  neden,
  teknik,
  className,
}: {
  readonly deger: number | null | undefined;
  readonly onek?: string;
  readonly birim?: string;
  readonly basamak?: number;
  readonly neden: string;
  readonly teknik?: string;
  readonly className?: string;
}) {
  if (deger === undefined || deger === null || !Number.isFinite(deger)) return <Olculemedi neden={neden} teknik={teknik} kisa />;
  return (
    <span className={cn("tabular-nums", className)}>
      {onek}
      {deger.toLocaleString("tr-TR", { minimumFractionDigits: basamak, maximumFractionDigits: basamak })}
      {birim}
    </span>
  );
}

/** Metin ya da "ölçülemedi". BOŞ/BOŞLUK dizge de ÖLÇÜLMEMİŞ sayılır: ekranda görünen
 *  hiçlik, "alan gelmedi"den ayırt edilemez ve ikisi de bir cevap değildir. */
export function Metin({
  deger,
  neden,
  teknik,
  className,
}: {
  readonly deger: string | null | undefined;
  readonly neden: string;
  readonly teknik?: string;
  readonly className?: string;
}) {
  if (typeof deger !== "string" || deger.trim() === "") return <Olculemedi neden={neden} teknik={teknik} kisa />;
  return <span className={cn("break-all", className)}>{deger}</span>;
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
 *
 * ÜÇÜNCÜ HÂL DE ROZETTİR, düz yazı değil: bu bileşen tablo hücrelerinde kullanılıyor
 * ve ölçülemeyen satırın rozet yerine italik bir cümleye dönüşmesi sütun hizasını
 * bozardı — göz o satırı "farklı bir şey" diye değil, "eksik bir şey" diye okumalı.
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

/* --- KPI KARTI (şablonun `section-cards` deseni) ------------------------- */

export function Kpi({
  etiket,
  children,
  alt,
}: {
  readonly etiket: string;
  readonly children: ReactNode;
  readonly alt?: ReactNode;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-1 rounded-lg border bg-card px-3 py-2.5">
      <span className="text-muted-foreground text-xs">{etiket}</span>
      <span className="truncate font-semibold text-lg">{children}</span>
      {alt ? <span className="text-muted-foreground text-[11px] leading-4">{alt}</span> : null}
    </div>
  );
}

/* --- BİÇİMLEYİCİLER ------------------------------------------------------ */

/**
 * HAM GÖVDE ALANINI SAYIYA ÇEVİRİR; çeviremezse `null`.
 * Alpaca REST'i sayıları DİZGE döndürüyor ("184.31") ve `dashboard_view` onları
 * ayrıştırmadan geçiriyor — `Number()`ı doğrudan çağırmak boş dizgeyi ve `null`ı
 * 0 yapardı, yani ölçülmemiş bir tutar "sıfır tutar" diye okunurdu. Bu fonksiyonun
 * yapabileceği en kötü şey `0` döndürmektir; onun yerine `null` döner.
 */
export function sayiya(deger: unknown): number | null {
  if (typeof deger === "number") return Number.isFinite(deger) ? deger : null;
  if (typeof deger === "string") {
    const t = deger.trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/** ISO damgası → yerel kısa metin. Ayrıştırılamayan damga `null` döner: ham dizgeyi
 *  basmak, geçersiz bir damgayı geçerli gibi göstermek olurdu. */
export function zamanMetni(ts: string | null | undefined): string | null {
  if (typeof ts !== "string" || ts.trim() === "") return null;
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "medium" });
}

/** Saniye → "42 sn" / "7 dk" / "3,2 sa" / "1,5 gün". Ölçülemeyen değer için `null`.
 *  Negatif süre de ölçülemez sayılır: geçmişe akan bir yaş bir sayı değil, bir arızadır. */
export function sureMetni(saniye: number | null | undefined): string | null {
  if (saniye === undefined || saniye === null || !Number.isFinite(saniye) || saniye < 0) return null;
  if (saniye < 90) return `${Math.round(saniye)} sn`;
  if (saniye < 5400) return `${Math.round(saniye / 60)} dk`;
  if (saniye < 172800) return `${(saniye / 3600).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sa`;
  return `${(saniye / 86400).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} gün`;
}
