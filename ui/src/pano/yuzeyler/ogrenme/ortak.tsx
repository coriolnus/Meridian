"use client";

/* ============================================================================
   ÖĞRENME + ANTRENMAN YÜZEYLERİNİN ORTAK PARÇALARI
   ----------------------------------------------------------------------------
   İKİ YÜZEY TEK KAPIYI PAYLAŞIR ve bu bilinçli. Öğrenme (academy) ile Antrenman
   (productivity) AYNI defterin iki yüzü: biri "döngü kapandı mı?", öteki "döngüyü
   besleyen makine koşuyor mu?" diye sorar ve ikisi de aynı uçlardan (`/api/hermes`,
   `/api/diagnostics`) okur. Kapıyı iki kez yazsaydım, bir gün birinde "ölçülemedi"
   yazan bir alan ötekinde 0 basardı — aynı sayı iki yüzeyde iki farklı gerçek
   gösterirdi. Bu yüzden yasak TEK yerde duruyor.

   ÜÇ HÂL AYRI (veri.ts sözleşmesi): yükleniyor / okunamadı / oturum düştü.
   DÖRDÜNCÜ HÂL de burada: elde ESKİ veri varken tazeleme düşmüş — kart boşaltılmaz
   (bir ağ hıçkırığı ekrandaki her sayıyı silmemeli) ama TAZE de sayılmaz.

   BU YÜZEYLERİN KENDİNE ÖZGÜ TUZAĞI ÜÇ DEĞERLİ BAYRAKLARDIR. `active`,
   `veri_seti_taze`, `stream_ok`, `independent_upstreams` … hepsi `true|false|null`
   döner ve `null` "hayır" DEĞİL, "ölçülemedi"dir. `UcDegerli` bu ayrımı tek bir
   bileşene kapatır; `!x` yazan her satır sessizce üçüncü hâli ikinciye katlardı.
   ============================================================================ */
import type { ReactNode } from "react";
import { CircleHelp, LockKeyhole, TriangleAlert, type LucideIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";

/* ---- SAYI BASIMI --------------------------------------------------------- */

// Intl örneği pahalı; basamak+işaret bileşimi başına bir kez kurulur.
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
export function rKati(v: unknown, basamak = 3): string | null {
  const s = sayi(v, basamak, true);
  return s === null ? null : `${s}R`;
}

export function para(v: unknown, basamak = 2): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return `$${new Intl.NumberFormat("tr-TR", {
    minimumFractionDigits: basamak,
    maximumFractionDigits: basamak,
  }).format(v)}`;
}

/** Kâr/zarar (ve delta) rengi. `null`/0 için NÖTR: sıfırı yeşile boyamak "kazandık" der. */
export function pnlRengi(v: unknown): string {
  if (typeof v !== "number" || !Number.isFinite(v) || v === 0) return "text-foreground";
  return v > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400";
}

/** Metin alanı gerçekten dolu mu? Boş dizge de "yok" sayılır — `""` basmak boş
 *  bir hücre bırakır ve boş hücre okuyucuya "ölçtük, içi boş" der. */
export function metin(v: unknown): string | null {
  return typeof v === "string" && v.trim().length > 0 ? v : null;
}

/** ISO damganın YAŞI, insan diliyle. Damga yoksa/bozuksa `null` — "0 dk önce"
 *  yazmak, hiç koşmamış bir işi az önce koşmuş gibi gösterirdi (canlıda ölçülmüş
 *  tuzak: `learning_automation._yas` aynı ayrımı sunucu tarafında yapıyor). */
export function yas(ts: unknown): { metin: string; saniye: number } | null {
  const s = metin(ts);
  if (s === null) return null;
  const t = Date.parse(s);
  if (!Number.isFinite(t)) return null;
  const sn = Math.max(0, (Date.now() - t) / 1000);
  if (sn < 90) return { metin: `${Math.round(sn)} sn önce`, saniye: sn };
  if (sn < 5400) return { metin: `${Math.round(sn / 60)} dk önce`, saniye: sn };
  if (sn < 172800) return { metin: `${(sn / 3600).toFixed(1).replace(".", ",")} sa önce`, saniye: sn };
  return { metin: `${Math.round(sn / 86400)} gün önce`, saniye: sn };
}

/** ISO damgayı yerel okunur biçime çevirir; damgasızsa `null`. */
export function anMetni(ts: unknown): string | null {
  const s = metin(ts);
  if (s === null) return null;
  const t = new Date(s);
  if (!Number.isFinite(t.getTime())) return s; // ayrıştırılamayan damga AYNEN yazılır, yutulmaz
  return t.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

/* ---- ÖLÇÜLEMEDİ ---------------------------------------------------------- */

/** Blok biçimi: nedeni GÖRÜNÜR yazar. Kart gövdesinde kullanılır. */
export function Olculemedi({ neden, className }: { neden: string; className?: string }) {
  return (
    <span className={cn("flex flex-col gap-0.5", className)}>
      <span className="text-muted-foreground text-sm italic">ölçülemedi</span>
      <span className="text-muted-foreground text-xs leading-snug">{neden}</span>
    </span>
  );
}

/** Satır-içi biçim: dar hücrede nedeni `title` ile taşır (noktalı altı çizgi =
 *  "üstüne gel"). Nedeni tamamen düşürmek yasak; yalnız yerleşimi değişir. */
export function OlculemediHucre({ neden }: { neden: string }) {
  return (
    <span
      className="cursor-help text-muted-foreground text-xs underline decoration-dotted underline-offset-2"
      title={neden}
    >
      ölçülemedi
    </span>
  );
}

/** Sayı/metin varsa yazar, yoksa `neden`i taşıyan "ölçülemedi" basar. */
export function Deger({
  metin: m,
  neden,
  className,
}: {
  metin: string | null;
  neden: string;
  className?: string;
}) {
  if (m === null) return <OlculemediHucre neden={neden} />;
  return <span className={className}>{m}</span>;
}

/* ---- ÜÇ DEĞERLİ BAYRAK --------------------------------------------------- */

/** `true|false|null` bayrağın rozetli hâli. `null` ASLA "hayır" gibi çizilmez:
 *  bu yüzeylerdeki bayrakların çoğu (`active`, `veri_seti_taze`, `ready`,
 *  `independent_upstreams`) üçüncü hâli GERÇEKTEN kullanıyor ve o hâl operatör
 *  için bambaşka bir eylem demek — "hayır" bilgi, "ölçülemedi" kuraklıktır. */
export function UcDegerli({
  deger,
  evet,
  hayir,
  neden,
  evetIyi = true,
}: {
  deger: boolean | null | undefined;
  evet: string;
  hayir: string;
  /** `null` iken ekrana çıkacak gerekçe — uçtan geliyorsa aynen taşı. */
  neden: string;
  /** `true` iyi haber mi? (Örn. `brain_degraded` için FALSE iyi haberdir.) */
  evetIyi?: boolean;
}) {
  if (deger === null || deger === undefined) {
    return (
      <Badge variant="outline" className="cursor-help gap-1 text-muted-foreground" title={neden}>
        <CircleHelp className="size-3" aria-hidden />
        ölçülemedi
      </Badge>
    );
  }
  const iyi = deger === evetIyi;
  return (
    <Badge
      variant="outline"
      className={cn(
        iyi
          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
          : "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300",
      )}
    >
      {deger ? evet : hayir}
    </Badge>
  );
}

/* ---- KART İSKELETİ ------------------------------------------------------- */

/** Bölüm kartı — derin bağ çapası (`#/dashboard/academy/karne`) BU id'ye düşer. */
export function BolumKarti({
  kimlik,
  baslik,
  soru,
  ikon: Ikon,
  ek,
  children,
}: {
  kimlik: string;
  baslik: string;
  soru: string;
  ikon: LucideIcon;
  ek?: ReactNode;
  children: ReactNode;
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
          {ek ? <div className="shrink-0">{ek}</div> : null}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">{children}</CardContent>
    </Card>
  );
}

/** Etiket → değer satırı. Değer `ReactNode` çünkü çoğu satır ya rozet ya
 *  "ölçülemedi" taşıyor; düz dizgeye indirgemek üçüncü hâli kaybettirirdi. */
export function Satir({ etiket, children, ipucu }: { etiket: string; children: ReactNode; ipucu?: string }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-border/40 border-b py-1.5 last:border-0">
      <span className="text-muted-foreground text-xs" title={ipucu}>
        {etiket}
      </span>
      <span className="min-w-0 break-words text-right text-sm tabular-nums">{children}</span>
    </div>
  );
}

/** Alt-başlıklı kutu — bir kartın içindeki mantıksal blokları ayırır. */
export function Kutu({ baslik, aciklama, children }: { baslik: string; aciklama?: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-border/60 bg-muted/20 p-4">
      <h3 className="font-medium text-sm">{baslik}</h3>
      {aciklama ? <p className="mt-0.5 text-muted-foreground text-xs leading-relaxed">{aciklama}</p> : null}
      <div className="mt-3 flex flex-col gap-3">{children}</div>
    </section>
  );
}

/** Uçtan gelen beyan cümlesi — payda/kapsam/sınır metinleri. Uydurulmaz, aynen taşınır. */
export function Beyan({ children }: { children: ReactNode }) {
  return <p className="text-muted-foreground text-xs leading-relaxed">{children}</p>;
}

/* ---- (DÖRT) HÂL KAPISI --------------------------------------------------- */

function Bildiri({
  ikon: Ikon,
  baslik,
  metin: m,
  tonu,
}: {
  ikon: LucideIcon;
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
        <p className="mt-0.5 break-words text-muted-foreground text-xs leading-relaxed">{m}</p>
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
        {zaman ? `${zaman.toLocaleTimeString("tr-TR")} okumasından` : "önceki bir okumadan"} kalma, ŞU ANI
        göstermiyor. {hata}
      </p>
    </div>
  );
}

export function Kapi<T>({
  durum,
  ad,
  children,
  yukseklik,
}: {
  durum: Durum<T>;
  /** Hangi ucun okunamadığı ekranda ADIYLA yazsın diye. */
  ad: string;
  children: (veri: T) => ReactNode;
  yukseklik?: string;
}) {
  if (durum.oturumDustu) {
    return (
      <Bildiri
        ikon={LockKeyhole}
        tonu="notr"
        baslik="Oturum düştü"
        metin={`${ad} okunamıyor: sunucu 401 döndü. Bu bir veri arızası DEĞİL — yeniden giriş gerekiyor.`}
      />
    );
  }
  if (durum.veri === null && durum.yukleniyor) return <YukleniyorIskeleti yukseklik={yukseklik} />;
  if (durum.veri === null) {
    return (
      <Bildiri
        ikon={TriangleAlert}
        tonu="uyari"
        baslik={`${ad} okunamadı`}
        metin={durum.hata ?? `${ad} boş gövde döndürdü — çizilecek bir şey yok ve nedeni uçtan gelmedi.`}
      />
    );
  }
  return (
    <>
      {durum.hata === null ? null : <BayatSerit hata={durum.hata} zaman={durum.zaman} />}
      {children(durum.veri)}
    </>
  );
}
