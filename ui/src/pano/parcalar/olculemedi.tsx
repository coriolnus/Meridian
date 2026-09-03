/**
 * olculemedi.tsx — `Olculemedi` (+ `OlculemediHucre`) ON ÜÇ KOMŞU KOPYASININ TEK TANIMI
 * (TSK-121, 2026-09-03).
 *
 * ÖLÇÜM (`.superpowers/sdd/2026-09-03-tsk121/kesif.md`): on bir düz `Olculemedi` tanımı
 * (`kabuk/FlattenKapisi.tsx`, `ajan/analiz/bugun/ogrenme/ortak.tsx`, `kanban/Hal.tsx`,
 * `kimlik/kuyruk/sistem/yetki/parcalar.tsx`, `portfoy/olcum.tsx`) + iki `OlculemediHucre`
 * (`analiz`, `ogrenme` — birebir) = 13. TSK-113'ün aksine `Bildiri` gibi DÜZ paylaşım YETMEZ:
 * gövdeler GERÇEKTEN ayrışıyor (ikon/tooltip/prop-tipi farklı) — kabuk enjeksiyonu şart, tıpkı
 * `parcalar/kapi.tsx::kapiKur(kabuk)`nun iki durum makinesini tek sıraya indirdiği gibi.
 *
 * ÖLÇÜLEN ALTI AİLE (KABUK tablosunda ADIYLA — `test_pano_komsu_kopyalar_v403.py` bu tabloyu
 * METİN olarak okur, aile kümesi sessizce değişirse çivi öter):
 *   satir   — kuyruk ≡ sistem (22rem, altçizgi YOK) · kimlik (20rem, teknik'te altçizgi) ·
 *             yetki (20rem, altçizgi YOK). Üçü de AYNI gövde, `SatirEki` iki ekseni taşır.
 *   hucre   — analiz ≡ ogrenme'nin İKİ ürünü: blok-biçimli `Olculemedi` (flex-col+italik
 *             sarmalı; ogrenme'de teknik-koşullu altçizgi EK DALI) ve `OlculemediHucre`
 *             (satır-içi, ikisinde de birebir). `HucreEki.bicim` ayırır.
 *   kpi     — yalnız `bugun` (KPI başlığı stili: italik DEĞİL, `font-medium text-base`).
 *   span    — ajan (her zaman altçizgili, `className` alır) · FlattenKapisi (italik + hard-
 *             coded "ölçülemedi — " öneki, dışa aktarılmaz). İkisi de TEK <span> ama stili ayrı.
 *   ikonlu  — yalnız `kanban` (Info ikonlu).
 *   tooltip — yalnız `portfoy` (Radix `Tooltip`; eski `kisa: string` — kısa ETİKET metni —
 *             burada `kisaMetin`e taşındı, `kisa` artık HER AİLEDE boolean).
 *
 * TASARIM — KARAR TEK YERDE, ÇİZİM ÇAĞRI YERİNDE (`kapiKur` emsali): `olculemediKur(aile, ek)`
 * bağlı bir `Olculemedi` döndürür; literal `function Olculemedi(` bu dosyada TAM BİR kez geçer
 * (döndürülen kapanış) — aile-özel gövdeler (`satirCiz`, `hucreCiz`, …) BAŞKA adlar taşır ki
 * tarama onları KOPYA saymasın.
 *
 * BEYANLI BEDEL — SAYI TEK KAYNAKTA (düzeltme turu 1, 2026-09-03): `kisa` prop'unun anlamı
 * AİLEYE göre SABİTLENDİ (boolean, "kısalt" bayrağı); portföyün ÖLÇÜLEN 30 çağrı yeri (5 dosya:
 * `portfoy/olcum.tsx` + üç `portfoy/*.tsx` yüzeyi + `yuzeyler/PortfoyYuzey.tsx` — bu beşincisi
 * `yuzeyler/portfoy/` ALTINDA DEĞİL, ilk taramada kaçmıştı, `npm run kontrol` yakaladı; 28
 * dizge-değerli `kisaMetin="…"` + 2 ifade-değerli `kisaMetin={…}`) `kisa="…"` → `kisaMetin=`e
 * taşındı (tam liste: `.superpowers/sdd/2026-09-03-tsk121/report.md` §4). Diğer çağıranlar
 * (`portfoy/olcum.tsx` dahil) sayıyı KOPYALAMAZ, BU şerhe atıf yapar. `ek`
 * parametresi `unknown` — aile-özel şekli (`SatirEki`/`HucreEki`/`SpanEki`) her `Ciz`
 * fonksiyonunun İÇİNDE `as` ile daraltılır; çağrı yerinde tip denetimi kaybolur ama gövdeler
 * zaten HİÇ değişmiyor (ölçülen sabit ek nesneleri, kesif.md tablosu).
 */
import { Info } from "lucide-react";
import type { ReactNode } from "react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export interface OlculemediOzellikleri {
  readonly neden: string;
  readonly teknik?: string;
  /** Kısaltma BAYRAĞI — `satir`/`ikonlu` ailelerinde kullanılır. */
  readonly kisa?: boolean;
  /** Kısa ETİKET METNİ — yalnız `tooltip` ailesi (eski portföy `kisa: string`). */
  readonly kisaMetin?: string;
  readonly className?: string;
}

export type OlculemediAilesi = "satir" | "hucre" | "kpi" | "span" | "ikonlu" | "tooltip";

/* ---- satir: kuyruk ≡ sistem (22rem) · kimlik (20rem+altçizgi) · yetki (20rem) ------------ */

export interface SatirEki {
  readonly maxGenislik: "20rem" | "22rem";
  /** yalnız `kimlik` true — `teknik` varken satır altçizgili olur. */
  readonly altCizgiTeknikte: boolean;
}

function satirCiz(o: OlculemediOzellikleri, ek: SatirEki): ReactNode {
  return (
    <span
      className={cn(
        "text-muted-foreground text-xs italic",
        o.kisa &&
          (ek.maxGenislik === "22rem"
            ? "inline-block max-w-[22rem] truncate align-bottom"
            : "inline-block max-w-[20rem] truncate align-bottom"),
        ek.altCizgiTeknikte && o.teknik && "cursor-help underline decoration-dotted underline-offset-2",
      )}
      title={o.teknik ? `${o.neden} — ${o.teknik}` : o.neden}
    >
      {o.neden}
    </span>
  );
}

/* ---- hucre: analiz ≡ ogrenme — blok (Olculemedi) + satırici (OlculemediHucre) ------------ */

export interface HucreEki {
  readonly bicim: "blok" | "satirici";
  /** yalnız `blok` biçiminde anlamlı — ogrenme true, analiz false. */
  readonly altCizgiTeknikte: boolean;
}

function hucreCiz(o: OlculemediOzellikleri, ek: HucreEki): ReactNode {
  if (ek.bicim === "satirici") {
    return (
      <span
        className="cursor-help text-muted-foreground text-xs underline decoration-dotted underline-offset-2"
        title={o.teknik ? `${o.neden} — ${o.teknik}` : o.neden}
      >
        {o.neden}
      </span>
    );
  }
  return (
    <span className={cn("flex flex-col gap-0.5", o.className)}>
      <span
        className={cn(
          "text-muted-foreground text-sm italic",
          ek.altCizgiTeknikte && o.teknik && "cursor-help underline decoration-dotted underline-offset-2",
        )}
        title={o.teknik}
      >
        {o.neden}
      </span>
    </span>
  );
}

/* ---- kpi: yalnız bugun ------------------------------------------------------------------- */

function kpiCiz(o: OlculemediOzellikleri): ReactNode {
  return (
    <span className={cn("inline-flex flex-col gap-0.5", o.className)}>
      <span className="font-medium text-muted-foreground text-base leading-snug tracking-tight" title={o.teknik}>
        {o.neden}
      </span>
    </span>
  );
}

/* ---- span: ajan (altçizgili) · FlattenKapisi (italik + önekli) --------------------------- */

export interface SpanEki {
  readonly stil: "altcizgi" | "italik-onekli";
}

function spanCiz(o: OlculemediOzellikleri, ek: SpanEki): ReactNode {
  if (ek.stil === "italik-onekli") {
    return (
      <span className="text-muted-foreground text-xs italic" title={o.teknik ? `${o.neden} — ${o.teknik}` : o.neden}>
        ölçülemedi — <span className="not-italic">{o.neden}</span>
      </span>
    );
  }
  return (
    <span
      className={cn("cursor-help text-muted-foreground text-xs underline decoration-dotted underline-offset-2", o.className)}
      title={o.teknik ? `${o.neden} — ${o.teknik}` : o.neden}
    >
      {o.neden}
    </span>
  );
}

/* ---- ikonlu: yalnız kanban (Info ikonlu) -------------------------------------------------- */

function ikonluCiz(o: OlculemediOzellikleri): ReactNode {
  return (
    <span
      className={cn("inline-flex items-center gap-1 text-muted-foreground", o.kisa ? "text-xs" : "text-sm")}
      title={o.teknik ? `${o.neden} — ${o.teknik}` : o.neden}
    >
      <Info className="size-3 shrink-0" aria-hidden />
      {o.neden}
    </span>
  );
}

/* ---- tooltip: yalnız portfoy (Radix Tooltip) ---------------------------------------------- */

function tooltipCiz(o: OlculemediOzellikleri): ReactNode {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          title={o.teknik ? `${o.neden} — ${o.teknik}` : o.neden}
          className={cn(
            "cursor-help text-muted-foreground text-xs underline decoration-dotted underline-offset-4",
            o.className,
          )}
        >
          {o.kisaMetin ?? "ölçülemedi"}
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-sm">{o.neden}</TooltipContent>
    </Tooltip>
  );
}

/* ---- KABUK — aile adı → gövde. `ek`in şekli aileye göre `as` ile daraltılır. -------------- */

const KABUK: Record<OlculemediAilesi, (o: OlculemediOzellikleri, ek: unknown) => ReactNode> = {
  satir: (o, ek) => satirCiz(o, ek as SatirEki),
  hucre: (o, ek) => hucreCiz(o, ek as HucreEki),
  kpi: (o) => kpiCiz(o),
  span: (o, ek) => spanCiz(o, ek as SpanEki),
  ikonlu: (o) => ikonluCiz(o),
  tooltip: (o) => tooltipCiz(o),
};

/** TEK TANIM. Verilen aileye (+ aile-özel `ek`e) bağlı bir `Olculemedi` bileşeni üretir. */
export function olculemediKur(aile: OlculemediAilesi, ek?: unknown) {
  return function Olculemedi(o: OlculemediOzellikleri): ReactNode {
    return KABUK[aile](o, ek);
  };
}
