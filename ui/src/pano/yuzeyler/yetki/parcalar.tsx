"use client";

/* ============================================================================
   KİMLİK EKSENİ — ORTAK PARÇALAR (Kullanıcılar + Roller)
   ----------------------------------------------------------------------------
   İki yüzey de aynı üç soruyu soruyor: "uç okundu mu", "alan geldi mi", "gelen
   şey ne demek". Üçünü her kartta elle yazmak, birinde unutulduğunda ekranın
   SESSİZCE yalan söylemesi demekti — boş bir yetki kartı "yetkin yok" diye de
   "her şey serbest" diye de okunabilir ve ikisi de tehlikeli.

   `Olculemedi` `neden` olmadan DERLENMEZ (tip zorluyor). Bu yüzeylerde ölçülemeyen
   şey bir yetkidir; "—" yazmak, olmayan bir yeteneği var ya da var olan bir yetkiyi
   yok göstermek olurdu.
   ============================================================================ */
import type { ComponentType, ReactNode } from "react";

import { Check, Minus, X } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/* --- BÖLÜM KABI ---------------------------------------------------------- */

/** Bölüm kartı. `kimlik` derin bağ ÇAPASIDIR (`#/dashboard/users/oturum`) —
 *  `GenelYuzey.tsx`teki `bolum-<kimlik>` deseninin aynısı. */
export function BolumKart({
  kimlik,
  baslik,
  soru,
  ikon: Ikon,
  aksiyon,
  children,
}: {
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
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <Ikon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
              {baslik}
            </CardTitle>
            <CardDescription className="mt-1">{soru}</CardDescription>
          </div>
          {aksiyon ? <div className="shrink-0">{aksiyon}</div> : null}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">{children}</CardContent>
    </Card>
  );
}

/* --- ÜÇ HÂLİN KAPISI ----------------------------------------------------- */

/** Uç okunana kadar / okunamazsa ne çizileceği. `children` YALNIZ veri varken çağrılır.
 *  Oturum düşmesi ayrı bir hâl (veri.ts sözleşmesi): çaresi yeniden giriştir, tazeleme değil.
 *  TANIM BURADA DEĞİL (TSK-113): tek kaynak `parcalar/kapi.tsx`. */
export { Kapi } from "../../parcalar/kapi";

/* --- UYDURMA YASAĞININ EKRAN KARŞILIĞI ----------------------------------- */

/** Ölçülemeyen değerin yeri. `neden` ZORUNLU. */
export function Olculemedi({ neden, teknik, kisa = false }: { readonly neden: string; readonly teknik?: string; readonly kisa?: boolean }) {
  return (
    <span
      className={cn("text-muted-foreground text-xs italic", kisa && "inline-block max-w-[20rem] truncate align-bottom")}
      title={teknik ? `${neden} — ${teknik}` : neden}
    >
      {neden}
    </span>
  );
}

/** Sistemde KARŞILIĞI OLMAYAN alan. "ölçülemedi"den AYRI: orada bir ölçüm denendi ve
 *  başarısız oldu; burada ölçülecek bir şey HİÇ YOK — veri modelinde alan bulunmuyor. */
/** Dürüst boşluk — İKİ KATMAN (2026-08-26 sözleşmesi, bkz. ogrenme/ortak.tsx):
 *  `neden` İNSAN CÜMLESİdir ve görünür; `teknik` iç ayrıntıdır ve üstüne gelince çıkar.
 *  "ölçülemedi — " öneki KALKTI: 178 yerde aynı kelime, hiçbirinde ne olduğunu
 *  söylemiyordu. Çivi: tests/test_arayuz_dili_v323.py. */
export function AlanYok({ neden, teknik }: { readonly neden: string; readonly teknik?: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 text-muted-foreground text-xs"
      title={teknik ? `${neden} — ${teknik}` : neden}
    >
      <Minus className="size-3 shrink-0" aria-hidden />
      {neden}
    </span>
  );
}

/* --- ÜÇ DEĞERLİ İZİN HÜCRESİ --------------------------------------------- */

export type IzinDegeri = "var" | "yok" | "kosullu" | "olculemedi";

/**
 * İzin hücresi DÖRT DEĞERLİDİR ve dördü de ekranda ayrı görünür. "koşullu"yu
 * "var" saymak, onay kapısı ardındaki bir yetkiyi serbest göstermek olurdu;
 * "ölçülemedi"yi "yok" saymak ise sistemi olduğundan kısıtlı gösterirdi.
 */
export function IzinHucresi({ deger, not }: { readonly deger: IzinDegeri; readonly not: string }) {
  if (deger === "olculemedi") {
    return <Olculemedi neden={not} kisa />;
  }
  const Ikon = deger === "var" ? Check : deger === "yok" ? X : Minus;
  const renk =
    deger === "var"
      ? "text-emerald-600 dark:text-emerald-400"
      : deger === "yok"
        ? "text-red-600 dark:text-red-400"
        : "text-amber-600 dark:text-amber-400";
  return (
    <span className={cn("inline-flex items-start gap-1.5 text-left text-xs", renk)} title={not}>
      <Ikon className="mt-px size-3.5 shrink-0" aria-hidden />
      <span className="text-foreground/80 leading-4">{not}</span>
    </span>
  );
}
