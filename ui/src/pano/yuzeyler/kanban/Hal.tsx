"use client";

/* ============================================================================
   ÜÇ HÂL + "ölçülemedi" rozeti — bu yüzeyin dürüstlük iskeleti
   ----------------------------------------------------------------------------
   `veri.ts` bir isteğin sonucunu DÖRT ayrı hâl olarak taşıyor (yükleniyor / hata /
   oturum düştü / veri) ve dördünün ÇARESİ farklı: yükleniyor → bekle; hata →
   sunucuya bak; oturum düştü → yeniden giriş; veri → oku. Hepsini tek bir boş
   karta indirgemek operatörü yanlış yere bakmaya gönderir — VLO dersinin arayüz
   hâli (bkz. hafıza: "oturum-başı canlı triyaj").

   ESKİ VERİ SİLİNMEZ: `veri.ts` bir hıçkırıkta ekrandaki sayıyı boşaltmıyor,
   `hata`yı dolduruyor. Bu bileşen de aynısını yapıyor — veri varken hata gelirse
   veriyi ÇİZER ama üstüne bayat şeridini basar.
   ============================================================================ */
import type { ReactNode } from "react";

import { AlertTriangle, Info, LockKeyhole } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";

export function Hal<T>({
  d,
  ad,
  iskelet,
  ciz,
}: {
  d: Durum<T>;
  /** Uç adı — hata metninde geçiyor ki operatör hangi isteğin düştüğünü bilsin. */
  ad: string;
  iskelet?: ReactNode;
  ciz: (v: T) => ReactNode;
}) {
  if (d.oturumDustu) {
    return (
      <Alert>
        <LockKeyhole />
        <AlertTitle>Oturum düştü</AlertTitle>
        <AlertDescription>
          {ad} 401 döndü. Bu bir veri arızası değil — panoyu yenileyip parolayla yeniden gir.
        </AlertDescription>
      </Alert>
    );
  }

  if (d.veri === null) {
    if (d.hata) {
      return (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertTitle>{ad} okunamadı</AlertTitle>
          <AlertDescription>{d.hata}</AlertDescription>
        </Alert>
      );
    }
    if (d.yukleniyor) return <>{iskelet ?? <Skeleton className="h-32 w-full" />}</>;
    return (
      <Alert>
        <Info />
        <AlertTitle>{ad} henüz okunmadı</AlertTitle>
        <AlertDescription>İstek ne tamamlandı ne düştü — bu boş bir sonuç DEĞİL.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {d.hata ? (
        // BAYAT AMA ÇİZİLİYOR: aşağıdaki sayılar son BAŞARILI okumadan geliyor.
        // Silmek bir ağ hıçkırığında panoyu boşaltırdı; sessizce çizmek bayatı
        // canlı diye okutmak olurdu. Üçüncü yol: çiz + damgala.
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertTitle>Tazeleme düştü — aşağısı son başarılı okuma</AlertTitle>
          <AlertDescription>{d.hata}</AlertDescription>
        </Alert>
      ) : null}
      {ciz(d.veri)}
    </div>
  );
}

/** Ölçülemeyen bir DEĞERİN yerine geçer. "—" yazmıyoruz: tire, okuyucuya "ölçtük,
 *  sonuç yok" der ve bu bu depoda bir yalandır (CLAUDE.md §4). */
export function Olculemedi({ neden, kisa = false }: { neden: string; kisa?: boolean }) {
  return (
    <span
      className={cn("inline-flex items-center gap-1 text-muted-foreground", kisa ? "text-xs" : "text-sm")}
      title={neden}
    >
      <Info className="size-3 shrink-0" aria-hidden />
      ölçülemedi
    </span>
  );
}

/** Ölçülemeyen bir BLOĞUN yerine geçer — nedeni gizlemeden yazar. */
export function OlculemedBlok({ baslik, neden }: { baslik: string; neden: string }) {
  return (
    <Alert>
      <Info />
      <AlertTitle>{baslik} ölçülemedi</AlertTitle>
      <AlertDescription>{neden}</AlertDescription>
    </Alert>
  );
}

export function SaltOkunurRozet({ not }: { not: string }) {
  return (
    <Badge variant="outline" className="shrink-0 gap-1" title={not}>
      <LockKeyhole className="size-3" aria-hidden />
      salt okunur
    </Badge>
  );
}
