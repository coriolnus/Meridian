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
import { cn } from "@/lib/utils";

import { Bildiri } from "../../parcalar/bildiri";
import { BayatSerit, YukleniyorIskeleti } from "../../parcalar/bayat";
import { type AdEki, kapiKur } from "../../parcalar/kapi";
import { olculemediKur } from "../../parcalar/olculemedi";

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

/* ---- ÖLÇÜLEMEDİ ----------------------------------------------------------
   TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`. Bu yüzeyin
   iki gövdesi (blok + satır-içi) "hucre" ailesinin iki `bicim`i — `Olculemedi` blok-biçimli
   (`altCizgiTeknikte: true`, `analiz/ortak.tsx`in aksine `teknik` varken altçizgi EK DALI
   taşır), `OlculemediHucre` satır-içi (analiz ile birebir). */

/** Blok biçimi: nedeni GÖRÜNÜR yazar. Kart gövdesinde kullanılır. */
/** Veri yokken basılan dürüst boşluk. İKİ KATMAN, ve sıra 2026-08-26'da TERSİNE DÖNDÜ:
 *
 *    ESKİ:  "ölçülemedi" + `neden` (içinde alan adı, uç yolu, `null` …)
 *    YENİ:  `neden` = İNSAN CÜMLESİ (görünür) · `teknik` = iç ayrıntı (üstüne gelince)
 *
 *  OPERATÖR VAKASI: "dışardan bir göz sadece UI'ı görecek" — ölçüldü ki 401 `neden`
 *  geliştiricinin kendine yazdığı cümleydi (`day_pnl_pct` nabızda yok · /api/alpaca
 *  `account.cash` null döndü). `/api/session` gören biri "bu bitmemiş" der.
 *
 *  DÜRÜSTLÜK DİSİPLİNİ GEVŞEMEZ: veri yokken hâlâ sayı UYDURULMUYOR ve sebep hâlâ
 *  TAŞINIYOR. Değişen tek şey sebebin hangi KATMANDA ve hangi DİLLE söylendiği.
 *  `teknik` sessizce düşürülemez (çivi: test_arayuz_dili_v323) — düşerse teşhis kaybolur
 *  ve "ölçemedim" ile "arıza var" yine ayırt edilemez hâle gelir.
 *
 *  "ölçülemedi" SABİT ETİKETİ KALKTI: 178 yerde aynı kelime, hiçbirinde ne olduğunu
 *  söylemiyordu. Artık cümlenin kendisi konuşuyor ("Günlük değişim henüz hesaplanmadı"). */
export const Olculemedi = olculemediKur("hucre", { bicim: "blok", altCizgiTeknikte: true });

/** Satır-içi biçim: dar hücrede nedeni `title` ile taşır (noktalı altı çizgi =
 *  "üstüne gel"). Nedeni tamamen düşürmek yasak; yalnız yerleşimi değişir. */
export const OlculemediHucre = olculemediKur("hucre", { bicim: "satirici", altCizgiTeknikte: false });

/** Sayı/metin varsa yazar, yoksa `neden`i taşıyan "ölçülemedi" basar. */
export function Deger({
  metin: m,
  neden,
  teknik,
  className,
}: {
  metin: string | null;
  neden: string;
  teknik?: string;
  className?: string;
}) {
  if (m === null) return <OlculemediHucre neden={neden} teknik={teknik} />;
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
  teknik,
  evetIyi = true,
}: {
  deger: boolean | null | undefined;
  evet: string;
  hayir: string;
  /** `null` iken ekrana çıkacak gerekçe — uçtan geliyorsa aynen taşı. */
  neden: string;
  teknik?: string;
  /** `true` iyi haber mi? (Örn. `brain_degraded` için FALSE iyi haberdir.) */
  evetIyi?: boolean;
}) {
  if (deger === null || deger === undefined) {
    return (
      <Badge variant="outline" className="cursor-help gap-1 text-muted-foreground" title={teknik ? `${neden} — ${teknik}` : neden}>
        <CircleHelp className="size-3" aria-hidden />
        {neden}
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
          : "border-uyari-h bg-uyari-t text-uyari",
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

/* ---- (DÖRT) HÂL KAPISI ---------------------------------------------------
   `Bildiri`/`YukleniyorIskeleti`/`BayatSerit` TANIMLARI BURADA DEĞİL (TSK-121, 2026-09-03):
   tek kaynak `parcalar/bildiri.tsx` ve `parcalar/bayat.tsx` — üçü de yukarıda ithal edilir. */

/** Yükleniyor / okunamadı / oturum düştü / bayat-ama-var — dördü AYRI çare ister.
 *  TANIM BURADA DEĞİL (TSK-113, 2026-09-03): yedi yüzey aynı `Kapi<T>` gövdesini kopyalıyordu.
 *  KARAR tek kaynakta (`parcalar/kapi.tsx`), ÇİZİM burada — bu yüzeyin metinleri kendisinindir,
 *  sıra ortaktır. `bayat` verildiği için hata veriyi EZMEZ: veri varken şerit olur (A ailesinin
 *  `Alert` kapıları bunun tersini yapar ve bu ayrım kabuktan türetilir). */
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
