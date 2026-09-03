"use client";

/* ============================================================================
   ÖLÇÜM İLKELERİ — bir sayı ya ÖLÇÜLDÜ ya da NEDENİYLE ölçülemedi
   ----------------------------------------------------------------------------
   Bu dosya portföy yüzeyinin UYDURMA YASAĞI (CLAUDE.md §4) uygulamasıdır. İki
   şeyi tek yerde tutar:

     1. `sayi()` — ayrıştırmanın TEK kapısı. `/api/alpaca` Alpaca REST yanıtını
        HAM geçiriyor (adapters/alpaca.py::positions `r.json()`) ve Alpaca sayısal
        alanları DİZGE döndürür: `"qty":"10"`, `"unrealized_pl":"-12.3"`. Bunları
        doğrudan çarpmak `NaN` üretir ve `NaN` ekranda "—" olur — yani bir ölçüm
        hatası sessizce "veri yok"a dönüşür. Kapı dizgeyi de sayıyı da kabul
        eder, çevrilemeyeni `null` yapar.

     2. `<Olculemedi>` — "—" YAZMANIN YASAL BİÇİMİ. Çıplak bir tire okuyucuya
        "ölçtük, bir şey yok" der; bu bir yalandır. Bu bileşen tireyi yazarken
        NEDENİ de taşır (tooltip + `title` niteliği): fare tutmayan bir okuyucu
        için `title`, tutan için radix tooltip'i. İkisi de aynı cümleyi söyler.

   RENK KANALI AYRIDIR (operatör kararı): tutar BÜYÜKLÜK kanalında, kâr/zarar
   RENK kanalında taşınır. `kzSinifi()` yalnız İŞARETE bakar; büyüklüğe değil.
   Ölçülemeyen bir K/Z ne yeşil ne kırmızıdır — nötrdür, çünkü "bilmiyoruz"un
   rengi yoktur.
   ============================================================================ */
import type { ReactNode } from "react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { olculemediKur } from "../../parcalar/olculemedi";

/** Sayıya çevrilebiliyorsa sayı, aksi hâlde `null`. Dizge Alpaca yüzünden şart. */
export function sayi(v: unknown): number | null {
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v === "string") {
    const t = v.trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/** Dizgeye çevrilebiliyorsa dizge, aksi hâlde `null`. Boş dizge de `null` sayılır. */
export function metin(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const t = v.trim();
  return t === "" ? null : t;
}

const PARA = new Intl.NumberFormat("tr-TR", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
const PARA_KISA = new Intl.NumberFormat("tr-TR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const ORAN = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const ADET = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 4 });

export function para(v: number): string {
  return PARA.format(v);
}

export function paraKisa(v: number): string {
  return PARA_KISA.format(v);
}

export function yuzde(v: number): string {
  return `${v > 0 ? "+" : ""}${ORAN.format(v)}%`;
}

export function adet(v: number): string {
  return ADET.format(v);
}

/** İŞARET → renk sınıfı. Ölçülemeyenin (null) rengi YOKTUR: nötr döner.
 *  Tema jetonları gri (tema.css:75-79) olduğu için K/Z rengi sözleşmede AÇIKÇA
 *  izin verilen emerald/red çiftinden gelir (brief: "Kâr/zarar için … kabul"). */
export function kzSinifi(v: number | null): string {
  if (v === null) return "text-muted-foreground";
  if (v > 0) return "text-[var(--yon-arti)]";
  if (v < 0) return "text-red-600 dark:text-red-400";
  return "text-muted-foreground";
}

/** Aynı ayrımın SVG karşılığı — grafik çubuğunun dolgusu VE konturu.
 *
 *  NEDEN SOLİD DEĞİL, AÇIK DOLGU + KOYU KONTUR (ölçülmüş bir okunabilirlik
 *  kısıtı): çubuğun İÇİNDE sembol kodu yazıyor. Solid emerald-600 üzerine
 *  `fill-background` beyaz metin okunur, ama ÜÇÜNCÜ hâl olan nötr gri üzerine
 *  beyaz metin okunmaz — üç durumun üçünde birden çalışan tek metin rengi yok.
 *  Açık dolgu (%25) her üç durumda da `fill-foreground` metni taşır; renk kanalı
 *  ise 1,5 px'lik TAM DOYGUN kontura taşınır, yani hiç zayıflamaz. Şablonun kendi
 *  çubuk grafiği de aynı yolu tutuyor (`fillOpacity={0.5}` + `fill-foreground`
 *  etiket, analytics/top-traffic-sources.tsx). */
export function kzDolgusu(v: number | null): string {
  /* DOLGU OPAKLIĞI %25'TEN %85'E ÇIKTI (2026-08-25, tarayıcıda ölçüldü).
     Önceki hâl yön-artı rengini %25 alfayla dolduruyordu ve niyeti "içi soluk, kenarı keskin çubuk"tu;
     ama ölçüm başka söyledi: 1440px'te çubuklar 64×28 px ve %25 dolgu + 1px kontur
     beyaz zeminde OKUNMUYORDU — yüzeyin merkezindeki grafik boş görünüyordu, veri
     tastamam yerindeyken. Kontur DURUYOR (çubuğun sınırını verir, bitişik çubukları
     ayırır); değişen yalnız dolgunun ağırlığı.
     ÖLÇÜLEMEYEN HÂL BİLEREK SOLUK KALDI (%20): "K/Z ölçülemedi" bir değer değil bir
     boşluktur ve kârla aynı görsel ağırlığı taşımamalı. */
  if (v === null) return "fill-muted-foreground/20 stroke-muted-foreground/60";
  if (v > 0) return "fill-[var(--yon-arti)]/85 stroke-[var(--yon-arti)]";
  if (v < 0) return "fill-red-500/85 stroke-red-600 dark:stroke-red-400";
  return "fill-muted-foreground/20 stroke-muted-foreground/60";
}

/** Grafik göstergesinin (legend) örnek kutusu — `kzDolgusu`nun HTML karşılığı.
 *  İkisi ayrı yazılırsa ilk düzenlemede sessizce ayrışır ve gösterge, grafiğin
 *  söylemediği bir şey söyler. */
export function kzOrnegi(v: number | null): string {
  if (v === null) return "bg-muted-foreground/20 ring-1 ring-muted-foreground/60";
  if (v > 0) return "bg-[var(--yon-arti)]/85 ring-1 ring-[var(--yon-arti)]";
  if (v < 0) return "bg-red-500/85 ring-1 ring-red-600 dark:ring-red-400";
  return "bg-muted-foreground/20 ring-1 ring-muted-foreground/60";
}

/** "—" YAZMANIN TEK YASAL BİÇİMİ: tire NEDENİYLE birlikte gelir.
 *  TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`, "tooltip"
 *  ailesi (Radix Tooltip, tek üye bu yüzey). BEYANLI BEDEL: eski `kisa: string` (kısa ETİKET
 *  metni, varsayılan "ölçülemedi") ortak sözleşmede `kisaMetin`e taşındı — `kisa` artık HER
 *  AİLEDE boolean bir kısaltma bayrağı. Çağrı yerleri `kisaMetin=` kullanır; TAM SAYI ve dosya
 *  listesi TEK KAYNAKTA — `parcalar/olculemedi.tsx`nin "BEYANLI BEDEL" şerhi (düzeltme turu 1,
 *  2026-09-03: burada kopyalanmıyor, aynı sayı iki yerde ayrışmasın diye). */
export const Olculemedi = olculemediKur("tooltip");

/** Ölçüldüyse `bicim(v)`, ölçülemediyse nedenli tire. Sayı hücrelerinin ortak kapısı. */
export function Deger({
  v,
  bicim,
  neden,
  teknik,
  className,
}: {
  v: number | null | undefined;
  bicim: (n: number) => string;
  neden: string;
  teknik?: string;
  className?: string;
}) {
  if (v === null || v === undefined) return <Olculemedi neden={neden} teknik={teknik} />;
  return <span className={cn("tabular-nums", className)}>{bicim(v)}</span>;
}

/** Bölüm başlığı — kart yığınından ÖNCE gelen ince şerit. GenelYuzey'deki kart
 *  başlığının aynı gramerini taşır (ikon + başlık + soru), ama bölüm birden çok
 *  kart içerdiği için başlık kartın DIŞINDA durur. */
export function BolumBasligi({
  ikon: Ikon,
  baslik,
  soru,
  ek,
}: {
  ikon: React.ComponentType<{ className?: string }>;
  baslik: string;
  soru: string;
  ek?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
      <div className="min-w-0">
        <h2 className="flex items-center gap-2 font-semibold text-lg tracking-tight">
          <Ikon className="size-4 shrink-0 text-muted-foreground" />
          {baslik}
        </h2>
        <p className="mt-0.5 text-muted-foreground text-sm">{soru}</p>
      </div>
      {ek}
    </div>
  );
}

/** ÜÇ HÂLİN ORTAK KARŞILAYICISI (`veri.ts` sözleşmesi: yükleniyor / hata /
 *  oturum düştü / veri). Bileşenler bunu sarar; hiçbiri üç hâlden birini
 *  atlayamaz çünkü atlanan hâl derleyicide değil EKRANDA görünür. */
export function UcHal({
  yukleniyor,
  hata,
  oturumDustu,
  veriVar,
  yol,
  children,
}: {
  yukleniyor: boolean;
  hata: string | null;
  oturumDustu: boolean;
  veriVar: boolean;
  yol: string;
  children: ReactNode;
}) {
  if (oturumDustu) {
    return (
      <p className="text-muted-foreground text-sm">
        Oturum düştü — <code className="text-xs">{yol}</code> 401 döndü. Yeniden giriş gerekiyor; tazeleme çare değil.
      </p>
    );
  }
  if (!veriVar && yukleniyor) {
    return <p className="text-muted-foreground text-sm">okunuyor…</p>;
  }
  if (!veriVar) {
    return (
      <p className="text-sm text-destructive">
        <code className="text-xs">{yol}</code> okunamadı — {hata ?? "neden bilinmiyor (uç boş gövde döndürdü)"}
      </p>
    );
  }
  return <>{children}</>;
}

/** Bir ucun tazelik damgası. `hata` DOLUYKEN veri ekranda kalır ama TAZE SAYILMAZ
 *  (veri.ts:90 şerhi) — bu rozet o ayrımı görünür kılar. */
export function TazelikRozeti({ zaman, hata, yol }: { zaman: Date | null; hata: string | null; yol: string }) {
  if (hata) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-help text-destructive text-xs">
            {yol} · bayat{zaman ? ` (${zaman.toLocaleTimeString("tr-TR")})` : ""}
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-sm">{hata}</TooltipContent>
      </Tooltip>
    );
  }
  return (
    <span className="text-muted-foreground text-xs">
      {yol} · {zaman ? zaman.toLocaleTimeString("tr-TR") : "henüz okunmadı"}
    </span>
  );
}
