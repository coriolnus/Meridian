"use client";

/* ============================================================================
   HAFIZA · ANA SAYFA KARTLARI — üst yüzeyin `home` bölümlerinin birebir karşılığı
   ----------------------------------------------------------------------------
   BÖLÜM SIRASI VE KART İÇERİKLERİ KAYNAKTAN ÖLÇÜLDÜ (2026-09-02, TSK-108 Görev 9;
   üst yüzey sürümü v0.9.2, çapa ebad4782). İki dosya okundu ve ikisi de bağlayıcı:

     · `home-view.tsx::HomeView`      — ÜST SATIR: takımyıldız (2/3) + sağ sütun
                                         (bilgi sayfaları kartı, son belgeler kartı);
                                         ALTINDA `MemoryStoreCard`, en altta
                                         `MemoriesActivityChart`.
     · `bank-stats-view.tsx::BankStatsView` — ÜÇ BAŞLIKLI BÖLÜM: hafıza deposu ·
                                         birleştirme (+ zihin modelleri) · etkinlik
                                         (+ arka plan işleri).

   ÖLÇÜLEN AYRIM YAZILI DURUYOR (uydurma yasağı): operatörün ekranında bu üç
   başlıklı bölüm ana sayfanın ALTINDA duruyor; üst yüzeyin KAYNAĞINDA aynı üç
   bölüm `BankStatsView` bileşenindedir ve `home-view` yalnız ikisinin kartlarını
   (depo kartı + etkinlik grafiği) doğrudan çiziyor. Birleşim burada BİLEREK
   yapıldı: operatörün gördüğü ekran ile kaynağın bölüm listesi aynı sayfada
   toplandı, kart içerikleri kaynaktan alındı. Sapma rapora yazıldı; ekranda
   gizlenen bir şey yok.

   ---------------------------------------------------------------------------
   RENK BİR KİMLİK KANALIDIR, BİR HÜKÜM DEĞİL
   ---------------------------------------------------------------------------
   Üst yüzeyin çıplak altılık renkleri TAŞINMAZ (pano jetonları tema anahtarına
   katılır, çıplak renk katılmaz). Taşınan şey HUE SIRASI:
     · kayıt türleri → grafiğin kendi seri tanımı (aşağıda, TEK kaynak: aynı üç
       renk hem alan grafiğinde hem bileşim çubuğunda kullanılır),
     · bağ türleri → takımyıldızın efsanesiyle AYNI jetonlar ve AYNI kelimeler
       (`takimyildizi.tsx::BAG_TURU_JETONU` / `::BAG_TURU_ETIKETI`). İkinci bir
       eşleme yazmak, aynı sayfada aynı bağ türünü iki renkte göstermek olurdu.

   ---------------------------------------------------------------------------
   YAZMA YOLU AÇILDI — VE YALNIZ BU DÜĞMEDE (2026-09-03)
   ---------------------------------------------------------------------------
   Düşen-birleştirme penceresindeki "Hepsini yeniden dene" artık gerçekten
   yazıyor: üst yüzeyin sırasıyla önce kurtarma, sonra birleştirme tetiği
   (gerekçe `yazma.tsx::kurtarVeTetikle`). Devre dışı rozeti bu eylemden
   KALKTI; sayfadaki başka bir yazma düğmesi yok, dolayısıyla burada kalan
   rozet de yok. Eylem İKİ ADIMLIDIR (onay penceresi + uygula) ve pencerede
   bütçe uyarısı durur: birleştirme model çağrısı üretir.
   ============================================================================ */
import { useMemo, useState } from "react";
import { AlertCircle, ArrowRight, Brain, CheckCircle2, Clock, FileText, RefreshCw, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ChartConfig } from "@/components/ui/chart";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { useApi } from "../../veri";
import { Deger, Kapi as UcKapisi, Olculemedi } from "../sistem/parcalar";
import { ZarfKapisi, damga, goreliDamga, listeye, metin, sayi, sozluk } from "./parcalar";
import { BAG_TURU_ETIKETI, BAG_TURU_JETONU, JETONLAR } from "./takimyildizi";
import { KURTARMA_KUNYESI, YazmaOnayi, kurtarVeTetikle } from "./yazma";
import type {
  BankaSayaclari,
  BilgiAgaci,
  BilgiDugumu,
  HafizaBelgesi,
  HafizaKaydi,
  HafizaListesi,
  HafizaZarfi,
  SayfaliGovde,
  ZihinModeli,
} from "./uctipleri";

const UC_LISTE = "/api/hindsight/liste";
const UC_ZIHIN = "/api/hindsight/zihin-modelleri";
const UC_BELGELER = "/api/hindsight/belgeler";
const UC_AGAC = "/api/hindsight/bilgi-tabani";

/* SERİLER — RENK BİR KİMLİK KANALI, BİR HÜKÜM DEĞİL. Panonun grafik rampası
   akromatiktir ve anlamı taşıyan şey ETİKETtir; üst yüzeyin mor/pembe/çivit
   paletini taşımak, panonun rezerve renk bantlarına (mod/gezinme/şiddet) girmeden
   de tasarım dilini bozardı. Taşınan şey düzen ve içerik, piksel değil.

   SEMANTİK ROL ÜST YÜZEYLE AYNI ve sıra da aynı: dünya bilgisi · deneyim · gözlem.
   Yığının sırası bir süs değil — aynı sırayı bilen bir okuyucu iki ekranda aynı
   bandı aynı yerde arar.

   BURADA YAŞIYOR ÇÜNKÜ İKİ OKURU VAR (Görev 9): akış grafiği ve bileşim çubuğu.
   İki kopya, aynı türü aynı sayfada iki renkte gösterirdi. */
export const SERI_YAPISI = {
  world: { label: "Dünya bilgisi", color: "var(--chart-2)" },
  experience: { label: "Deneyim", color: "var(--chart-3)" },
  observation: { label: "Gözlem", color: "var(--chart-5)" },
} satisfies ChartConfig;

export const SERI_ANAHTARLARI = ["world", "experience", "observation"] as const;
export type SeriAnahtari = (typeof SERI_ANAHTARLARI)[number];

/** Y EKSENİ KISALTMASI — üst yüzeyin `formatCompact`inin karşılığı, tr-TR ile.
 *  TEK OKURU eksen (inceleme M-5): sayaçlar `Deger` ile TAM basılır, çünkü bir sayacı
 *  kısaltmak ekrandaki tek yerde duran değeri yuvarlamak olurdu; eksende ise kısaltma
 *  okunabilirlik içindir ve değerin kendisi ipucunda tam durur. */
export function kisaSayi(n: number): string {
  return n.toLocaleString("tr-TR", { notation: "compact", maximumFractionDigits: 1 });
}

function tam(n: number): string {
  return n.toLocaleString("tr-TR");
}

/** Yüzde metni — payda SIFIRSA yüzde YAZILMAZ (paydasız oran uydurma olurdu). */
function yuzde(pay: number, payda: number): string | null {
  if (payda <= 0) return null;
  return `%${Math.round((pay / payda) * 100)}`;
}

/* ---------------------------------------------------------------------------
   SAYAÇ ŞERİDİ — üst yüzeyin `bank-stats-view.tsx::InlineStat` üçlüsü
   --------------------------------------------------------------------------- */

export function Sayac({
  etiket,
  deger,
  teknik,
  ikon: Ikon,
}: {
  readonly etiket: string;
  readonly deger: unknown;
  readonly teknik: string;
  readonly ikon: typeof Brain;
}) {
  return (
    <div className="flex min-w-0 items-center gap-3 rounded-lg border p-3">
      <span className="rounded-md bg-muted p-2">
        <Ikon className="size-4 text-muted-foreground" aria-hidden />
      </span>
      <span className="flex min-w-0 flex-col gap-0.5">
        <span className="text-muted-foreground text-xs">{etiket}</span>
        <span className="font-semibold text-2xl leading-tight">
          <Deger deger={sayi(deger)} neden="Bu sayaç gelmedi" teknik={teknik} />
        </span>
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   DAĞILIM — üst yüzeyin `bank-stats-view.tsx::Distribution` karşılığı
   ----------------------------------------------------------------------------
   ÇUBUK + SAYI + YÜZDE, üçü birlikte (operatörün ekranındaki hâl). Üst yüzey
   payı üç SABİT ada daraltıyor; burada anahtar listesi YOK — sözlük TELDEN gelir.
   Daraltan taraf, yeni bir tür doğduğu gün onu sessizce düşürür ve parçaların
   toplamı ile toplam tutmaz.

   SAYI OLMAYAN ANAHTAR SESSİZCE DÜŞMEZ: kaçının okunamadığı çubuğun altında
   yazar — "ölçtük, sıfır" ile "okuyamadık" ayrı kutulardır.
   --------------------------------------------------------------------------- */

export function Dagilim({
  govde,
  sira,
  renk,
  etiket,
  bosCumle,
}: {
  readonly govde: unknown;
  /** Üst yüzeyin SABİT bant sırası. Sözlükte olmayan ad atlanır, sırada olmayan
   *  anahtar SONA eklenir ve tanınmadığı ekranda yazar. */
  readonly sira: readonly string[];
  /** Anahtar → çizim rengi (jeton değişkeni). */
  readonly renk: (anahtar: string) => string;
  /** Anahtar → insan etiketi. Tanınmayan anahtar HAM basılır (çağıran karar verir). */
  readonly etiket: (anahtar: string) => string;
  /** Sözlük geldi ve içi boşsa yazılacak cümle — "okunamadı" DEĞİLDİR. */
  readonly bosCumle: string;
}) {
  const s = sozluk(govde);
  if (s === null) {
    return (
      <Olculemedi
        neden="Dağılım gelmedi"
        teknik="alan sözlük değil ya da hiç gelmedi — şema sürüklenmiş olabilir"
      />
    );
  }
  /* SIRA ÜST YÜZEYDEN, LİSTE TELDEN — VE İLK YAZIM ÖYLE DEĞİLDİ (inceleme Ö-1).
     `Object.entries` sırayı JSON anahtar sırasına bırakıyordu: renk aynı kalsa da
     bantlar üst yüzeydekinden BAŞKA yerde duruyordu ve upstream anahtar sırasını
     değiştirdiği gün ekran sessizce yeniden dizilirdi. Aynı bandı aynı yerde arayan
     okuyucu için birebirlik tam burada kırılır. Desen bu dosyada zaten vardı
     (`IslemlerKarti`): bilinen adlar üst yüzeyin sırasıyla, tanınmayanlar SONA —
     düşürülmeden, ve tanınmadıkları ekranda yazılı. */
  const girdiler = Object.entries(s);
  const bilinen = sira.filter((k) => k in s);
  const kuyruk = Object.keys(s).filter((k) => !sira.includes(k));
  const sayilar: (readonly [string, number, boolean])[] = [];
  let okunamayan = 0;
  for (const k of [...bilinen, ...kuyruk]) {
    const n = sayi(s[k]);
    if (n === null) okunamayan += 1;
    else sayilar.push([k, n, !sira.includes(k)] as const);
  }
  const toplam = sayilar.reduce((a, [, n]) => a + n, 0);

  if (girdiler.length === 0) {
    return <p className="text-muted-foreground text-sm">{bosCumle}</p>;
  }
  /* ANAHTAR GELDİ AMA HİÇBİRİ SAYI DEĞİL: bu "boş" değil OKUNAMADIdır. Aşağıdaki
     boş cümlesini yazsaydık, bir tip sürüklenmesini ölçülmüş bir sıfır gibi
     gösterirdik (uydurma yasağı). */
  if (sayilar.length === 0) {
    return (
      <Olculemedi
        neden="Dağılımın hiçbir türü sayı olarak gelmedi"
        teknik={`${okunamayan} anahtar geldi ve hiçbirinin değeri sayı değil — şema sürüklenmiş olabilir`}
      />
    );
  }

  /* PAYDA SIFIRSA TEK CÜMLE (inceleme M-2): ilk yazım hem boş cümlesini yazıyor hem
     de her anahtar için "payda sıfır" rozetli bir hücre çiziyordu — doğru ama
     gürültülü. Üst yüzey bu hâlde yalnız boş etiketini gösteriyor. Sayaçların
     hepsinin sıfır OLDUĞU bilgisi cümlenin içinde duruyor, kaybolmuyor. */
  if (toplam === 0) {
    return (
      <div className="flex flex-col gap-2">
        <span className="text-muted-foreground text-xs tabular-nums">toplam 0</span>
        <p className="text-muted-foreground text-sm">{bosCumle}</p>
        {okunamayan > 0 ? (
          <p className="text-muted-foreground text-[11px]">
            {okunamayan} tür sayı olarak gelmedi ve toplama katılmadı
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-muted-foreground text-xs tabular-nums">toplam {tam(toplam)}</span>
      </div>
      <span className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
        {sayilar
          .filter(([, n]) => n > 0)
          .map(([k, n]) => (
            <span
              key={k}
              className="h-full"
              style={{ width: `${(n / toplam) * 100}%`, backgroundColor: renk(k) }}
              title={`${etiket(k)}: ${tam(n)}`}
            />
          ))}
      </span>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {sayilar.map(([k, n, taninmayan]) => (
          <div key={k} className="flex min-w-0 flex-col gap-0.5">
            <span className="flex items-center gap-1.5">
              <span className="size-2 shrink-0 rounded-[2px]" style={{ backgroundColor: renk(k) }} aria-hidden />
              <span className="min-w-0 truncate text-[11px] text-muted-foreground uppercase tracking-wider">
                {etiket(k)}
              </span>
              {taninmayan ? (
                <Badge
                  variant="outline"
                  className="shrink-0 font-normal text-[10px] text-muted-foreground"
                  title="bu tür üst yüzeyin bant sırasında yok — sona eklendi ve adı ham basıldı"
                >
                  tanınmayan tür
                </Badge>
              ) : null}
            </span>
            <span className="flex items-baseline gap-1.5">
              <span className="font-semibold text-base tabular-nums">{tam(n)}</span>
              <span className="text-[10px] text-muted-foreground tabular-nums">{yuzde(n, toplam) ?? ""}</span>
            </span>
          </div>
        ))}
      </div>
      {okunamayan > 0 ? (
        <p className="text-muted-foreground text-[11px]">
          {okunamayan} tür sayı olarak gelmedi ve çubuğa katılmadı — toplam bu kadarını saymıyor
        </p>
      ) : null}
    </div>
  );
}

/* BANT SIRALARI ÜST YÜZEYİN `Distribution` ÇAĞRILARINDAN ÖLÇÜLDÜ (`bank-stats-view.tsx`
   @ ebad4782): kayıt bileşimi dünya → deneyim → gözlem, bağ türleri zamansal →
   anlamsal → varlık. Canlıda ölçülen dördüncü bağ anahtarı (nedensellik) üst yüzeyin
   bu listesinde YOK; uydurup araya sokmak yerine kuyruğa düşer ve ekranda tanınmadığı
   yazar — sırayı biz icat etmiyoruz, ölçüyoruz. */
export const KAYIT_TURU_SIRASI: readonly string[] = SERI_ANAHTARLARI;
export const BAG_TURU_SIRASI: readonly string[] = ["temporal", "semantic", "entity"];

/** Kayıt türü rengi/etiketi — grafiğin seri tanımından, TEK kaynak. */
export function kayitTuruRengi(anahtar: string): string {
  const k = anahtar as SeriAnahtari;
  return SERI_ANAHTARLARI.includes(k) ? SERI_YAPISI[k].color : "var(--muted-foreground)";
}

export function kayitTuruEtiketi(anahtar: string): string {
  const k = anahtar as SeriAnahtari;
  return SERI_ANAHTARLARI.includes(k) ? SERI_YAPISI[k].label : anahtar;
}

/** Bağ türü rengi/etiketi — takımyıldızın efsanesiyle AYNI kaynak. */
export function bagTuruRengi(anahtar: string): string {
  const jeton = BAG_TURU_JETONU[anahtar];
  return jeton === undefined ? "var(--muted-foreground)" : `var(${JETONLAR[jeton]})`;
}

export function bagTuruEtiketi(anahtar: string): string {
  return BAG_TURU_ETIKETI[anahtar] ?? anahtar;
}

/* ---------------------------------------------------------------------------
   İLERLEME SATIRI — üst yüzeyin `bank-stats-view.tsx::ProgressRow` karşılığı
   ----------------------------------------------------------------------------
   PAYDASIZ ÇUBUK YASAK (v286 G3a): payda ölçülemediyse çubuk HİÇ DOĞMAZ, yerinde
   gerekçe durur. Payda sıfırsa çubuk çizilir ve BOŞ görünür — "ölçtük, sıfır".
   --------------------------------------------------------------------------- */

function IlerlemeSatiri({
  biten,
  toplam,
  teknik,
}: {
  readonly biten: number | null;
  readonly toplam: number | null;
  /** Sayılar ölçülemediğinde üstüne gelince okunacak iç ayrıntı. */
  readonly teknik: string;
}) {
  if (biten === null || toplam === null) {
    return <Olculemedi neden="İlerleme hesaplanamadı" teknik={teknik} />;
  }
  const oran = toplam > 0 ? biten / toplam : 0;
  const p = Math.round(oran * 100);
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-muted-foreground text-xs">
          <span className="font-semibold text-foreground text-sm tabular-nums">{tam(biten)}</span>
          <span className="tabular-nums"> / {tam(toplam)}</span>
        </span>
        <span className="font-semibold text-foreground text-xs tabular-nums">
          {toplam > 0 ? `%${p}` : "payda sıfır"}
        </span>
      </div>
      <span className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <span className="h-full rounded-full bg-emerald-500" style={{ width: `${toplam > 0 ? p : 0}%` }} />
      </span>
    </div>
  );
}

/** Bir sayacın etiketli hücresi (üst yüzeyin dörtlü ızgarası). */
function Hucre({
  etiket,
  ikon: Ikon,
  ikonSinifi,
  children,
}: {
  readonly etiket: string;
  readonly ikon: typeof Brain;
  readonly ikonSinifi?: string;
  readonly children: React.ReactNode;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="flex items-center gap-1.5">
        <Ikon className={cn("size-3 shrink-0 text-muted-foreground", ikonSinifi)} aria-hidden />
        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{etiket}</span>
      </span>
      <span className="font-semibold text-base leading-tight tabular-nums">{children}</span>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   BİRLEŞTİRME KARTI — üst yüzeyin `bank-stats-view.tsx::ConsolidationCard`
   ----------------------------------------------------------------------------
   "TAMAMLANAN" BİR SAYAÇ DEĞİL, BİR TÜRETİMDİR ve türetimi üst yüzeyden ÖLÇÜLDÜ:
   toplam kayıt − bekleyen − düşen (negatife düşerse sıfıra kırpılır). Üst yüzeyin
   kendi şerhi nedenini söylüyor: bekleyen sayacı kalıcı düşenleri ZATEN dışarıda
   bırakıyor, o yüzden düşenler "tamamlandı" diye sayılamaz.

   ÜÇ SAYIDAN BİRİ GELMEZSE TÜRETİM YAPILMAZ. Üst yüzey düşen sayacını sıfır
   varsayıyor; burada varsayılmaz — gelmeyen bir sayacı sıfır saymak, ekranda
   "hepsi tamam" yazdırırdı ve bu ölçüm değil tahmin olurdu.
   --------------------------------------------------------------------------- */

export function KonsolidasyonKarti({
  stats,
  bank,
  simdi,
  tazele,
}: {
  readonly stats: BankaSayaclari;
  readonly bank: string;
  /** Göreli zamanın çözüldüğü an — okumanın kendi anı (çağıranın ölçümü). */
  readonly simdi: number;
  /**
   * SAYAÇLARI YENİDEN OKUR — kurtarma düğmesinin sonucu buradan görünür.
   * Kart sayaçları KENDİ okumadığı için (özet okuması çağıranda) tazeleme de
   * çağıranın işidir; kartın içinde ikinci bir okuma açmak, aynı sayının iki
   * kopyasını doğururdu.
   */
  readonly tazele: () => void;
}) {
  const [acik, setAcik] = useState(false);
  const toplam = sayi(stats.total_nodes);
  const bekleyen = sayi(stats.pending_consolidation);
  const dusen = sayi(stats.failed_consolidation);
  const biten =
    toplam === null || bekleyen === null || dusen === null ? null : Math.max(0, toplam - bekleyen - dusen);
  const dusenVar = dusen !== null && dusen > 0;
  const sonMetin = goreliDamga(stats.last_consolidated_at, simdi);

  return (
    <div className="flex flex-col gap-4">
      <IlerlemeSatiri
        biten={biten}
        toplam={toplam}
        teknik={
          "tamamlanan sayısı üç sayaçtan türetilir (toplam kayıt − bekleyen − düşen); " +
          "biri gelmediği için türetim yapılamadı"
        }
      />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Hucre etiket="Tamamlanan" ikon={CheckCircle2} ikonSinifi="text-emerald-500">
          <Deger
            deger={biten}
            neden="Tamamlanan sayısı türetilemedi"
            teknik="türetim üç sayaç ister: toplam kayıt, bekleyen ve düşen birleştirme"
          />
        </Hucre>
        <Hucre etiket="Bekleyen" ikon={AlertCircle} ikonSinifi="text-amber-500">
          <Deger deger={bekleyen} neden="Bekleyen sayacı gelmedi" teknik="bekleyen birleştirme sayacı yanıtta yok ya da sayı değil" />
        </Hucre>
        {/* ODAK GÖRÜNÜR (inceleme Ö-2, WCAG 2.4.7): çıplak `<button>` panonun ortak
            odak halkasını almıyordu — klavyeyle gezen biri hücreye geldiğini
            GÖRMÜYORDU. Halka shadcn düğmesinin jetonlarıyla aynı; üst yüzey de aynı
            yerde bir odak halkası çiziyor. Rol ve durum da bildirilir: bu hücre bir
            PENCERE açıyor ve pencerenin açık olup olmadığı okunabilir olmalı. */}
        <button
          type="button"
          disabled={!dusenVar}
          onClick={() => setAcik(true)}
          aria-haspopup="dialog"
          aria-expanded={acik}
          title={
            dusenVar
              ? "Düşen birleştirmelerin listesini aç"
              : dusen === null
                ? "düşen sayacı gelmedi — açılacak liste ölçülmedi"
                : "düşen birleştirme yok"
          }
          className={cn(
            "-mx-1 flex min-w-0 flex-col gap-0.5 rounded-md px-1 py-0.5 text-left transition-colors",
            "outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-destructive/40",
            dusenVar ? "cursor-pointer hover:bg-destructive/10" : "cursor-default",
          )}
        >
          <span className="flex items-center gap-1.5">
            <XCircle className={cn("size-3 shrink-0", dusenVar ? "text-destructive" : "text-muted-foreground/50")} aria-hidden />
            <span
              className={cn(
                "text-[10px] uppercase tracking-wider",
                dusenVar ? "text-destructive" : "text-muted-foreground",
              )}
            >
              Düşen
            </span>
          </span>
          <span className={cn("font-semibold text-base leading-tight tabular-nums", dusenVar && "text-destructive")}>
            <Deger deger={dusen} neden="Düşen sayacı gelmedi" teknik="düşen birleştirme sayacı yanıtta yok ya da sayı değil" />
            {dusenVar ? <ArrowRight className="ml-1 inline size-3 opacity-70" aria-hidden /> : null}
          </span>
        </button>
        <Hucre etiket="Son" ikon={Clock}>
          {sonMetin === null ? (
            <Olculemedi
              neden={
                stats.last_consolidated_at === null
                  ? "Hiç birleştirme yapılmamış"
                  : "Son birleştirme zamanı okunamadı"
              }
              teknik="birleştirme damgası gelmedi ya da çözülemeyen bir biçimde geldi"
              kisa
            />
          ) : (
            <span className="text-sm" title={damga(stats.last_consolidated_at) ?? undefined}>
              {sonMetin}
            </span>
          )}
        </Hucre>
      </div>
      <DusenlerPenceresi acik={acik} kapat={() => setAcik(false)} bank={bank} sayac={dusen} simdi={simdi} tazele={tazele} />
    </div>
  );
}

/* ---------------------------------------------------------------------------
   DÜŞEN BİRLEŞTİRMELER PENCERESİ — üst yüzeyin `FailedConsolidationsDialog`i
   ----------------------------------------------------------------------------
   SÜZGEÇ VEKİLDE VAR ve ölçüldü: kayıt listesi ucu birleştirme durumunu kapalı
   bir sözlükten geçiriyor ("failed" · "pending" · "done"), yani bu pencere gerçek
   bir liste okur — "vekilde yok" diye boş çizilmiyor.

   PENCERE KAPALIYKEN OKUMA YAPILMAZ: yol boşken okuma hiç başlamaz. Açılışta
   okumak, kapalı bir pencerenin bedelini her ana sayfa ziyaretine yaymak olurdu.
   --------------------------------------------------------------------------- */

/** Vekilin liste tavanı (`api.py::HAFIZA_LISTE_TAVANI`) — daha büyük bir sayı
 *  sessizce buraya inerdi ve ekran istediğinden azını aldığını bilmezdi. */
const DUSEN_TAVANI = 200;

function DusenlerPenceresi({
  acik,
  kapat,
  bank,
  sayac,
  simdi,
  tazele,
}: {
  readonly acik: boolean;
  readonly kapat: () => void;
  readonly bank: string;
  /** Sayaçtan gelen düşen sayısı — listeyle KIYASLANIR, biri ötekini doğrular. */
  readonly sayac: number | null;
  readonly simdi: number;
  /** Banka sayaçlarını yeniden okur (kart sahibinin okuması). */
  readonly tazele: () => void;
}) {
  const yol = acik
    ? `${UC_LISTE}?bank=${encodeURIComponent(bank)}&consolidation_state=failed&limit=${DUSEN_TAVANI}`
    : null;
  const liste = useApi<HafizaListesi>(yol);

  return (
    <Dialog open={acik} onOpenChange={(a) => (a ? undefined : kapat())}>
      <DialogContent className="flex max-h-[80vh] max-w-4xl flex-col gap-4">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <XCircle className="size-4 text-destructive" aria-hidden />
            Düşen birleştirmeler
          </DialogTitle>
          <DialogDescription>
            Birleştirme denendi ve düştü — bu kayıtlar bankada duruyor ama bağlanmadı
          </DialogDescription>
        </DialogHeader>

        {/* İKİ SAYIYI DA OKUR, HİÇBİRİNİ VARSAYMAZ: düğme yalnız düşen kayıt
            OLDUĞU ÖLÇÜLDÜĞÜNDE basılabilir. Sayaç gelmediğinde "belki vardır"
            diye açık bırakmak, ölçülmemiş bir sayıyı varsaymak olurdu; sıfır
            olduğunda da kurtarılacak bir şey yoktur (üst yüzey de aynı kapıyı
            koyuyor). Rozet bu eylemden KALKTI — yolu açıldı. */}
        <div className="flex flex-wrap items-center gap-2">
          <YazmaOnayi
            kunye={KURTARMA_KUNYESI}
            hedef={bank}
            hedefEtiketi="Uygulanacağı banka"
            ikon={RefreshCw}
            engel={
              sayac === null
                ? "Düşen sayacı gelmedi — kurtarılacak kayıt olup olmadığı ölçülemedi"
                : sayac === 0
                  ? "Düşen birleştirme yok — kurtarılacak kayıt yok"
                  : null
            }
            calistir={() => kurtarVeTetikle(bank)}
            basarili={() => {
              /* İKİ OKUMA DA TAZELENİR: pencere içindeki liste ve kartın
                 sayaçları AYRI uçlardan gelir; yalnız birini tazelemek, aynı
                 ekranda iki farklı gerçek bırakırdı. */
              liste.tazele();
              tazele();
            }}
          />
        </div>

        {/* OKUMANIN ÜÇ HÂLİ PAYLAŞILAN KAPIDAN (`sistem/parcalar.tsx::Kapi`): oturum
            düşmesi, ağ arızası ve "henüz dönmedi" ayrı ayrı çizilir ve cümleleri
            panonun geri kalanıyla aynı yerden gelir. */}
        <UcKapisi durum={liste} yol={UC_LISTE}>
          {(g) => <DusenlerTablosu govde={g} sayac={sayac} simdi={simdi} />}
        </UcKapisi>
      </DialogContent>
    </Dialog>
  );
}

function DusenlerTablosu({
  govde,
  sayac,
  simdi,
}: {
  readonly govde: HafizaListesi;
  readonly sayac: number | null;
  readonly simdi: number;
}) {
  if (govde.neden) {
    return <Olculemedi neden="Düşen kayıtlar okunamadı" teknik={govde.neden} />;
  }
  const ogeler: readonly HafizaKaydi[] = Array.isArray(govde.ogeler) ? govde.ogeler : [];
  const toplam = typeof govde.toplam === "number" && Number.isFinite(govde.toplam) ? govde.toplam : null;

  return (
    <div className="flex min-h-0 flex-col gap-2">
      <p className="text-muted-foreground text-xs tabular-nums">
        {tam(ogeler.length)} kayıt okundu
        {toplam === null ? " · toplam sayı gelmedi" : ` · süzgeçte toplam ${tam(toplam)}`}
        {ogeler.length === DUSEN_TAVANI ? ` · okuma tavanı ${tam(DUSEN_TAVANI)}` : ""}
        {sayac !== null && toplam !== null && sayac !== toplam
          ? ` · banka sayacı ${tam(sayac)} diyor — iki sayı ayrışıyor`
          : ""}
      </p>
      {ogeler.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Süzgeç okundu ve düşen kayıt gelmedi — bu ölçülmüş bir boşluktur
        </p>
      ) : (
        <div className="min-h-0 overflow-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-40">Düşme zamanı</TableHead>
                <TableHead className="w-28">Tür</TableHead>
                <TableHead>Kayıt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ogeler.map((k, i) => {
                const kimlik = metin(k.id);
                const gorece = goreliDamga(k.consolidation_failed_at, simdi);
                const tur = metin(k.fact_type);
                const govdeMetni = metin(k.text);
                const baglam = metin(k.context);
                const etiketler = listeye(k.tags);
                return (
                  <TableRow key={kimlik ?? `dusen-${i}`}>
                    <TableCell className="whitespace-nowrap text-muted-foreground text-xs">
                      {gorece ?? (
                        <Olculemedi
                          neden="Düşme zamanı gelmedi"
                          teknik="düşme damgası yanıtta yok ya da çözülemeyen bir biçimde geldi"
                          kisa
                        />
                      )}
                    </TableCell>
                    <TableCell className="text-xs">
                      {tur ?? (
                        <Olculemedi neden="Tür gelmedi" teknik="kayıt türü alanı yok ya da dizge değil" kisa />
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {govdeMetni === null ? (
                        <Olculemedi neden="Kayıt metni gelmedi" teknik="metin alanı yok ya da dizge değil" kisa />
                      ) : (
                        <span className="line-clamp-2 block">{govdeMetni}</span>
                      )}
                      {baglam !== null ? (
                        <span className="mt-0.5 line-clamp-1 block text-muted-foreground text-xs">{baglam}</span>
                      ) : null}
                      {etiketler !== null && etiketler.length > 0 ? (
                        <span className="mt-1 flex flex-wrap gap-1">
                          {etiketler.slice(0, 4).map((e) => (
                            <Badge key={e} variant="outline" className="font-normal text-[10px]">
                              {e}
                            </Badge>
                          ))}
                        </span>
                      ) : null}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ZİHİN MODELLERİ KARTI — üst yüzeyin `bank-stats-view.tsx::MentalModelsCard`
   ----------------------------------------------------------------------------
   ÜST YÜZEY İKİ KOVA SAYIYOR (bayat / uyumlu) ve uyumluyu ÇIKARMAYLA buluyor.
   Burada üç kova var, çünkü bayatlık alanı ÜÇ DEĞERLİ geliyor (`ZihinModelleri.tsx`
   şerhi): evet · hayır · bildirilmedi. Çıkarma yapsaydık bildirilmeyeni "uyumlu"
   diye sayardık — bir ölçüm boşluğunu iyi haber olarak okumak.

   KÜNYE DÜZEYİNDE OKUNUR: kart yalnız bayatlık bayrağını sayıyor, model metnini
   istemek her ana sayfa ziyaretinde sentezlenmiş paragrafları tele koymak olurdu.
   --------------------------------------------------------------------------- */

const ZIHIN_TAVANI = 200;

export function ZihinModelleriKarti({ bank }: { readonly bank: string }) {
  const yol = `${UC_ZIHIN}?bank=${encodeURIComponent(bank)}&detail=metadata&limit=${ZIHIN_TAVANI}`;
  const durum = useApi<HafizaZarfi<SayfaliGovde<ZihinModeli>>>(yol);

  /* ZARFIN DÖRT HÂLİ PAYLAŞILAN KAPIDAN GEÇER (`parcalar.tsx::ZarfKapisi`): bu
     kartta elle yazılsaydı aynı dört cümlenin beşinci kopyası doğardı ve biri
     düzeltilirken ötekiler eskirdi. */
  return (
    <UcKapisi durum={durum} yol={UC_ZIHIN}>
      {(z) => <ZarfKapisi zarf={z} ne="Zihin modelleri">{(govde) => <ZihinOzeti govde={govde} />}</ZarfKapisi>}
    </UcKapisi>
  );
}

function ZihinOzeti({ govde }: { readonly govde: SayfaliGovde<ZihinModeli> }) {
  if (!Array.isArray(govde.items)) {
    return (
      <Olculemedi
        neden="Model listesi tanınmayan bir biçimde geldi"
        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
      />
    );
  }

  const ogeler = govde.items;
  const toplam = typeof govde.total === "number" && Number.isFinite(govde.total) ? govde.total : null;
  if (ogeler.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        {toplam === 0
          ? "Bu bankada zihin modeli yok — ölçüldü, boş"
          : "Bu okumada model gelmedi ve toplam sayı da bildirilmedi"}
      </p>
    );
  }

  const bayat = ogeler.filter((m) => m.is_stale === true).length;
  const uyumlu = ogeler.filter((m) => m.is_stale === false).length;
  const bilinmeyen = ogeler.length - bayat - uyumlu;

  return (
    <div className="flex flex-col gap-4">
      <IlerlemeSatiri biten={uyumlu} toplam={ogeler.length} teknik="okunan model sayısı ölçülemedi" />
      <div className="grid grid-cols-3 gap-3">
        <Hucre etiket="Güncel" ikon={CheckCircle2} ikonSinifi="text-emerald-500">
          {tam(uyumlu)}
        </Hucre>
        <Hucre etiket="Bayat" ikon={AlertCircle} ikonSinifi="text-amber-500">
          {tam(bayat)}
        </Hucre>
        <Hucre etiket="Okunan" ikon={Brain}>
          {tam(ogeler.length)}
        </Hucre>
      </div>
      {bilinmeyen > 0 ? (
        <p className="text-muted-foreground text-[11px]">
          {tam(bilinmeyen)} modelin tazelik bayrağı gelmedi — ne güncel ne bayat sayıldılar
        </p>
      ) : null}
      {toplam !== null && toplam > ogeler.length ? (
        <p className="text-muted-foreground text-[11px] tabular-nums">
          Bankada toplam {tam(toplam)} model var; bu kart ilk {tam(ogeler.length)} tanesini sayıyor
        </p>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ARKA PLAN İŞLERİ KARTI — üst yüzeyin `bank-stats-view.tsx::OperationsCard`
   ----------------------------------------------------------------------------
   KAYNAK ÖLÇÜLDÜ: üst yüzey bu kartı işler listesinden DEĞİL, banka sayaçlarının
   durum sözlüğünden çiziyor. Ayrı bir uç çağırmak, aynı sayıyı ikinci bir yerden
   okumak (ve iki sayının ayrışma riskini doğurmak) olurdu.

   SIRA ÜST YÜZEYDEN, LİSTE TELDEN: bilinen durumlar üst yüzeyin sırasıyla çizilir,
   tanınmayan durumlar SONA eklenir — düşürülmez.
   --------------------------------------------------------------------------- */

const ISLEM_DURUM_SIRASI = ["completed", "processing", "pending", "failed", "cancelled"] as const;

const ISLEM_DURUM_ETIKETI: Readonly<Record<string, string>> = {
  completed: "tamamlandı",
  processing: "işleniyor",
  pending: "bekliyor",
  failed: "düştü",
  cancelled: "iptal",
};

const ISLEM_DURUM_RENGI: Readonly<Record<string, string>> = {
  completed: "var(--color-seri-9)",
  processing: "var(--color-seri-6)",
  pending: "var(--color-seri-7)",
  failed: "var(--destructive)",
  cancelled: "var(--muted-foreground)",
};

export function IslemlerKarti({ stats }: { readonly stats: BankaSayaclari }) {
  const s = sozluk(stats.operations_by_status);
  if (s === null) {
    return (
      <Olculemedi
        neden="İş durumları gelmedi"
        teknik="durum sözlüğü yanıtta yok ya da sözlük değil — şema sürüklenmiş olabilir"
      />
    );
  }
  const bilinen = ISLEM_DURUM_SIRASI.filter((d) => d in s);
  const digerleri = Object.keys(s).filter((d) => !ISLEM_DURUM_SIRASI.includes(d as (typeof ISLEM_DURUM_SIRASI)[number]));
  const sirali = [...bilinen, ...digerleri];
  const sayilar: (readonly [string, number])[] = [];
  let okunamayan = 0;
  for (const d of sirali) {
    const n = sayi(s[d]);
    if (n === null) okunamayan += 1;
    else sayilar.push([d, n] as const);
  }
  const toplam = sayilar.reduce((a, [, n]) => a + n, 0);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-muted-foreground text-xs">Durumlara göre</span>
        <span className="text-muted-foreground text-xs tabular-nums">toplam {tam(toplam)}</span>
      </div>
      {toplam === 0 ? (
        <p className="text-muted-foreground text-sm">
          {sayilar.length === 0
            ? "Durum sözlüğü okundu ve içi boş geldi — bu ölçülmüş bir boşluktur"
            : "Sayaçlar okundu ve hepsi sıfır — henüz iş koşmamış"}
        </p>
      ) : (
        <>
          <span className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
            {sayilar
              .filter(([, n]) => n > 0)
              .map(([d, n]) => (
                <span
                  key={d}
                  className="h-full"
                  style={{
                    width: `${(n / toplam) * 100}%`,
                    backgroundColor: ISLEM_DURUM_RENGI[d] ?? "var(--muted-foreground)",
                  }}
                  title={`${ISLEM_DURUM_ETIKETI[d] ?? d}: ${tam(n)}`}
                />
              ))}
          </span>
          <div className="flex flex-col gap-1.5">
            {sayilar.map(([d, n]) => (
              <div key={d} className="flex items-center gap-2 text-xs">
                <span
                  className="size-2 shrink-0 rounded-[2px]"
                  style={{ backgroundColor: ISLEM_DURUM_RENGI[d] ?? "var(--muted-foreground)" }}
                  aria-hidden
                />
                <span className="min-w-0 flex-1 truncate text-muted-foreground">{ISLEM_DURUM_ETIKETI[d] ?? d}</span>
                <span className="font-semibold text-foreground tabular-nums">{tam(n)}</span>
                <span className="w-10 text-right text-[10px] text-muted-foreground tabular-nums">
                  {yuzde(n, toplam) ?? ""}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
      {okunamayan > 0 ? (
        <p className="text-muted-foreground text-[11px]">
          {okunamayan} durum sayı olarak gelmedi ve toplama katılmadı
        </p>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   SON BELGELER — üst yüzeyin ana sayfa sağ sütunundaki `recentDocs` kartı
   ----------------------------------------------------------------------------
   ALTI SATIR, ÜST YÜZEYLE AYNI SAYI. Üst yüzey belge adı DİYE bir alan kullanmıyor
   (belge künyesi serbest biçimli), kimliği basıyor — bizde de kimlik basılır ve
   kimlik zaten depo yoludur (ölçüldü: belge kimliği repo yolu).

   SIRALAMA İDDİA EDİLMEZ: üst yüzey de sıralama parametresi göndermiyor, sıra üst
   servisin döndürdüğü sıradır. "En yeni altı" demek, ölçülmemiş bir sıralamayı
   ölçülmüş gibi göstermek olurdu — kart bunu kendi alt satırında yazıyor.
   --------------------------------------------------------------------------- */

const SON_BELGE_SAYISI = 6;

export function SonBelgeler({
  bank,
  simdi,
  git,
}: {
  readonly bank: string;
  readonly simdi: number;
  readonly git: () => void;
}) {
  const yol = `${UC_BELGELER}?bank=${encodeURIComponent(bank)}&limit=${SON_BELGE_SAYISI}`;
  const durum = useApi<HafizaZarfi<SayfaliGovde<HafizaBelgesi>>>(yol);
  return (
    <UcKapisi durum={durum} yol={UC_BELGELER}>
      {(z) => (
        <ZarfKapisi zarf={z} ne="Belge listesi">
          {(govde) => <BelgeSatirlari govde={govde} simdi={simdi} git={git} />}
        </ZarfKapisi>
      )}
    </UcKapisi>
  );
}

function BelgeSatirlari({
  govde,
  simdi,
  git,
}: {
  readonly govde: SayfaliGovde<HafizaBelgesi>;
  readonly simdi: number;
  readonly git: () => void;
}) {
  if (!Array.isArray(govde.items)) {
    return (
      <Olculemedi
        neden="Belge listesi tanınmayan bir biçimde geldi"
        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
      />
    );
  }
  const ogeler = govde.items;
  if (ogeler.length === 0) {
    return <p className="text-muted-foreground text-sm">Bu bankada belge yok — ölçüldü, boş</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-col">
        {ogeler.map((b, i) => {
          const kimlik = metin(b.id);
          const gorece = goreliDamga(b.created_at, simdi);
          return (
            <li key={kimlik ?? `belge-${i}`} className="flex items-center justify-between gap-2 py-1">
              <span className="flex min-w-0 items-center gap-1.5">
                <FileText className="size-3 shrink-0 text-muted-foreground" aria-hidden />
                <span className="min-w-0 truncate font-mono text-xs" title={kimlik ?? undefined}>
                  {kimlik ?? (
                    <Olculemedi neden="Belge kimliği gelmedi" teknik="kimlik alanı yok ya da dizge değil" kisa />
                  )}
                </span>
              </span>
              <span className="shrink-0 text-[11px] text-muted-foreground" title={damga(b.created_at) ?? undefined}>
                {gorece ?? (
                  <Olculemedi
                    neden="Eklenme zamanı gelmedi"
                    teknik="oluşturma damgası yanıtta yok ya da çözülemeyen bir biçimde geldi"
                    kisa
                  />
                )}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="text-muted-foreground text-[11px]">
        Sıra üst servisin döndürdüğü sıradır — bu kart ilk {tam(ogeler.length)} kaydı çiziyor
      </p>
      <Button variant="ghost" size="xs" className="self-start" onClick={git}>
        Tümü <ArrowRight className="size-3" aria-hidden />
      </Button>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   BİLGİ SAYFALARI — üst yüzeyin ana sayfa sağ sütunundaki `pages` kartı
   ----------------------------------------------------------------------------
   ÜST YÜZEY BURADA AĞACIN TAMAMINI, KLASÖRLERİ AÇIK ve SALT-OKUNUR çiziyor
   (`home-view.tsx` → `knowledge-base-view.tsx::TreeRow`). BURADA SAYFA LİSTESİ
   ÇİZİLİYOR ve bu bir SAPMADIR, gerekçesi yazılı: ağaç satırı Bilgi Tabanı
   görünümünün kendi bileşenidir ve ikinci bir kopyasını yazmak, aynı gerçeğin iki
   kopyası olurdu (tek-kaynak yasası). BEDELİ: klasör yapısı bu kartta görünmez —
   kart bunu kendi alt satırında söylüyor, sessizce kaybetmiyor.
   --------------------------------------------------------------------------- */

const SAYFA_SAYISI = 8;

/** Ağacı düz listeye açar — yalnız sayfa düğümleri. */
function sayfalar(dugumler: readonly BilgiDugumu[], cikti: BilgiDugumu[] = []): BilgiDugumu[] {
  for (const d of dugumler) {
    if (metin(d.kind) === "page") cikti.push(d);
    if (Array.isArray(d.children) && d.children.length > 0) sayfalar(d.children, cikti);
  }
  return cikti;
}

export function BilgiSayfalari({ bank, simdi, git }: { readonly bank: string; readonly simdi: number; readonly git: () => void }) {
  const yol = `${UC_AGAC}?bank=${encodeURIComponent(bank)}`;
  const durum = useApi<HafizaZarfi<BilgiAgaci>>(yol);

  /* GÖVDE KAPIDAN GELİR, KAPININ YANINDAN DEĞİL (inceleme M-3): ilk yazım listeyi
     kapının DIŞINDA, okumanın içinden kendisi türetiyordu ve kapının verdiği gövdeyi
     kullanmıyordu. Sonuç bugün doğruydu ama "gövde geldi mi" hükmü iki ayrı yerde
     kuruluyordu; kapının sözleşmesi değiştiği gün bu kart onunla birlikte değişmezdi. */
  return (
    <UcKapisi durum={durum} yol={UC_AGAC}>
      {(z) => (
        <ZarfKapisi zarf={z} ne="Bilgi ağacı">
          {(govde) => <SayfaSatirlari govde={govde} simdi={simdi} git={git} />}
        </ZarfKapisi>
      )}
    </UcKapisi>
  );
}

function SayfaSatirlari({
  govde,
  simdi,
  git,
}: {
  readonly govde: BilgiAgaci;
  readonly simdi: number;
  readonly git: () => void;
}) {
  const kokler = govde.roots;
  /** `null` = ağaç geldi ama kök dizisi tanınmayan biçimde. */
  const liste = useMemo(() => (Array.isArray(kokler) ? sayfalar(kokler) : null), [kokler]);
  if (liste === null) {
    return (
      <Olculemedi
        neden="Bilgi ağacı tanınmayan bir biçimde geldi"
        teknik="beklenen kök dizisi, gelen başka bir tip — şema sürüklenmiş olabilir"
      />
    );
  }
  if (liste.length === 0) {
    return <p className="text-muted-foreground text-sm">Bu bankada bilgi sayfası yok — ölçüldü, boş</p>;
  }

  const cizilen = liste.slice(0, SAYFA_SAYISI);
  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-col">
        {cizilen.map((d, i) => {
          const ad = metin(d.name);
          const gorece = goreliDamga(d.timestamp, simdi);
          return (
            <li key={metin(d.id) ?? `sayfa-${i}`} className="flex items-center justify-between gap-2 py-1">
              <span className="flex min-w-0 items-center gap-1.5">
                <FileText className="size-3 shrink-0 text-muted-foreground" aria-hidden />
                <span className="min-w-0 truncate text-sm" title={ad ?? undefined}>
                  {ad ?? <Olculemedi neden="Sayfanın adı gelmedi" teknik="ad alanı yok ya da dizge değil" kisa />}
                </span>
                {d.is_stale === true ? (
                  <span
                    className="size-1.5 shrink-0 rounded-full bg-amber-500"
                    title="kapsamında okunmamış kayıt var"
                    aria-hidden
                  />
                ) : null}
              </span>
              <span className="shrink-0 text-[11px] text-muted-foreground" title={damga(d.timestamp) ?? undefined}>
                {gorece ?? (
                  <Olculemedi
                    neden="Güncelleme zamanı gelmedi"
                    teknik="güncelleme damgası yanıtta yok ya da çözülemeyen bir biçimde geldi"
                    kisa
                  />
                )}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="text-muted-foreground text-[11px] tabular-nums">
        {tam(liste.length)} sayfanın {tam(cizilen.length)} tanesi çizildi · klasör yapısı Bilgi Tabanı görünümünde
      </p>
      <Button variant="ghost" size="xs" className="self-start" onClick={git}>
        Tümü <ArrowRight className="size-3" aria-hidden />
      </Button>
    </div>
  );
}
