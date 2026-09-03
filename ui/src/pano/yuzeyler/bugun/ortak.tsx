"use client";

/* ============================================================================
   BUGÜN YÜZEYİ — ORTAK DÜRÜSTLÜK PARÇALARI
   ----------------------------------------------------------------------------
   Bu dosyada tek bir iş var: "ölçemediğimiz" ile "ölçtük, sonuç bu" arasındaki
   farkı EKRANDA ayrı tutmak. Kod tarafında bu fark tipte duruyor (`?` ile `| null`);
   ekranda duracak yer de burasıdır — yoksa her kart kendi çözümünü uydurur ve
   biri "—", biri "0", biri boş kalır.

   YASA (CLAUDE.md §4 · UYDURMA YASAĞI): ölçülemeyen alan "0" ya da "—" yazmaz;
   "ölçülemedi" yazar ve NEDENİNİ taşır. Bir neden metni olmadan `Olculemedi`
   çizilemez — tip bunu zorunlu kılıyor.
   ============================================================================ */
import type { ReactNode } from "react";

import { olculemediKur } from "../../parcalar/olculemedi";

/* ---- BİÇİMLENDİRME ---------------------------------------------------------
   `tr-TR` bilinçli: panonun bütün metni Türkçe ve binlik ayracı ile ondalık
   işareti dilden gelir. `Intl` her çağrıda yeniden kurulmaz — biçimlendirici
   nesnesi pahalıdır ve bu sayılar 15 saniyede bir yeniden çizilir. */
const PARA = new Intl.NumberFormat("tr-TR", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
const SAYI = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2 });
const ORAN = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2, signDisplay: "exceptZero" });

export function bicimPara(n: number): string {
  return PARA.format(n);
}

export function bicimSayi(n: number): string {
  return SAYI.format(n);
}

/** Yüzdeyi İŞARETİYLE yazar (`+0,42%`). İşaret, yönü rengin YANINDA ikinci kez
 *  söyler: renk körlüğü ve tek renkli tema (varsayılan palet gri) yönü rengin
 *  tek başına taşımasına izin vermiyor. */
export function bicimOran(n: number): string {
  return `${ORAN.format(n)}%`;
}

/** Kâr/zarar rengi. Sıfır NÖTRDÜR — 0'ı yeşile boyamak "kazandık" demek olurdu. */
export function pnlRengi(n: number | null | undefined): string {
  if (n === null || n === undefined || n === 0) return "text-foreground";
  return n > 0 ? "text-[var(--yon-arti)]" : "text-[var(--yon-eksi)]";
}

/* ---- ÖLÇÜLEMEDİ ------------------------------------------------------------ */

/** Ölçülemeyen bir değerin yerine geçen tek işaret. `neden` ZORUNLU: nedensiz bir
 *  "ölçülemedi", okuyucuyu "acaba bozuk mu?" diye sunucu günlüklerine gönderir —
 *  oysa cevabın kendisi burada yazılabilir.
 *  TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`, "kpi"
 *  ailesi (KPI başlığı stili — italik DEĞİL, tek üye bu yüzey). */
export const Olculemedi = olculemediKur("kpi");

/* ---- ÜÇ HÂL ---------------------------------------------------------------
   `veri.ts` üç hâli AYRI taşıyor (yükleniyor / hata / oturum düştü) ve dördüncüsü
   "veri var". Her bileşende aynı dört dalı elle yazmak, birinde birini unutmak
   demekti — unutulan dal sessizce boş kart çizerdi. Dallanma tek yerde.

   ESKİ VERİ SİLİNMEZ AMA TAZE SAYILMAZ (veri.ts:90): `hata` doluyken elimizde eski
   bir gövde varsa onu ÇİZERİZ ve üstüne bayat şeridi koyarız. Boşaltmak, bir ağ
   hıçkırığında ekrandaki her sayıyı silmek olurdu. */
export function UcHal<T>({
  durum,
  iskelet,
  children,
}: {
  durum: { veri: T | null; yukleniyor: boolean; hata: string | null; oturumDustu: boolean };
  iskelet: ReactNode;
  children: (veri: T) => ReactNode;
}) {
  if (durum.oturumDustu) {
    return (
      <p className="text-muted-foreground text-sm">
        Oturum düştü — bu bölüm okunamıyor. Çaresi tazeleme değil, yeniden giriş.
      </p>
    );
  }
  if (durum.veri !== null) return <>{children(durum.veri)}</>;
  if (durum.yukleniyor) return <>{iskelet}</>;
  if (durum.hata !== null) {
    return <p className="text-destructive text-sm">Okunamadı — {durum.hata}</p>;
  }
  // DÖRDÜNCÜ DAL GERÇEKTİR: `yol` null verilmiş ya da istek hiç başlamamış olabilir.
  // Sessizce boş dönmek, "istek yapılmadı"yı "sonuç yok" diye çizmek olurdu.
  return <p className="text-muted-foreground text-sm">İstek henüz yapılmadı.</p>;
}
