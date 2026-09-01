"use client";

/* ============================================================================
   SEKME 2 — YOL HARİTASI: ROADMAP.md'nin tahtası (SALT OKUNUR)
   ----------------------------------------------------------------------------
   Operatörün isteği: "roadmap'i düzenli tutabileceğimiz şekilde". Bu turda tahta
   YALNIZ GÖSTERİR — yazma ucu yok, sürükleme yok, düğme yok. Rozet bunu ekranda
   söylüyor: taşınabilir sandığı bir kartı taşıyan operatör, hiçbir yere
   kaydedilmeyen bir düzenleme yapmış olurdu. Kaynak dosyayı bir İNSAN düzenliyor
   (`ROADMAP.md`, 562 KB) ve uç da bunu başlığında yazıyor.

   KOLONLAR BELGENİN KENDİ § BÖLÜMLERİDİR, sabit kodlama YOK. Gerekçe belgenin
   kendi tarihinde yazılı: §-numaraları 2026-08-17'de yeniden numaralandı
   (§1→§3, §2→§4 …) ve 151 atıf çevrildi. Kolon adlarını buraya gömmek, belgenin
   bir sonraki yeniden örgütlenmesinde panoyu SESSİZCE yanlış yapardı.

   TABLO SATIRLARI DA ÇİZİLİR (2026-08-31'de eklendi, ÖLÇÜMLE). Bu yüzey açıldığı
   günden 2026-08-31'e dek yalnız `maddeler`i okuyordu; ucun gönderdiği `tablolar[]`
   hiçbir yerde tüketilmiyordu. Ölçülen bedel: belgede 450 düzyazı maddesi ve 188
   tablo satırı var ve `§2 TAHTA` — AKTİF KALEM tahtası, tamamı tablo — panoda
   "0 madde" olarak çiziliyordu. Operatörün gördüğü grafikte tahta BOŞ bir satırdı,
   grafiği ise `§7 KARAR GÜNLÜĞÜ`nün 197 düzyazı maddesi dolduruyordu. İKİ SAYIM
   TOPLANMAZ (ucun kendi şerhi): madde ile tablo satırı ayrı BİRİMdir, ayrı çizilir,
   ayrı sayılır. Toplasaydık "belgede 638 kalem var" derdik — böyle bir kalem yok.

   "BELİRSİZ" KOVASI BİRLEŞTİRİLMEZ. Ucun ayrıştırıcısının en önemli satırı:
   işaretsiz kalem "açık" değil "belirsiz"dir (api.py:6605). Panoda o beş kovayı
   dörde indirmek — ya da "belirsiz"i "açık"a katmak — ölçülmemiş bir sayıyı
   yönetim kararına çevirirdi.
   ============================================================================ */
import { useMemo, useState } from "react";

import {
  FileQuestion,
  FileWarning,
  Info,
  ListChecks,
  Map as MapIkonu,
  Rows3,
  Strikethrough,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { useApi } from "../../veri";
import { Hal, SaltOkunurRozet } from "./Hal";
import {
  DURUM_ETIKETI,
  DURUM_SIRASI,
  SINIF_SIRASI,
  STATUS_ETIKETI,
  TABLO_DURUM_SIRASI,
  bolumBasligi,
  roadmapOku,
  statusSirala,
  tahtaSatirlari,
  tahtaSinifi,
  type RoadmapBolumu,
  type RoadmapMaddesi,
  type RoadmapOkumasi,
  type RoadmapTabloSatiri,
  type TahtaSatiri,
} from "./roadmap";

/* KART TAVANI: §7 karar günlüğü tek başına yüzlerce madde taşıyor (belge 4622
   satır). Hepsini basmak tarayıcıyı da okuyucuyu da boğardı. Tavan var AMA
   GİZLİ DEĞİL — her kolonun altında "gösterilen / toplam" yazıyor. */
const KART_TAVANI = 25;

const durumAyari = {
  bloke: { label: "bloke", color: "var(--destructive)" },
  acik: { label: "açık", color: "var(--primary)" },
  askida: { label: "askıda", color: "var(--chart-3)" },
  atif: { label: "atıf", color: "var(--chart-2)" },
  belirsiz: { label: "belirsiz", color: "var(--chart-1)" },
  kapali: { label: "kapalı", color: "var(--chart-4)" },
  cok_isaretli: { label: "çok işaretli", color: "var(--chart-5)" },
} satisfies ChartConfig;

/** Bir tablo satırının kovası. Uç satırı tek hükme indiremediyse `durum` null gelir
 *  ve nedeni `durum_neden`de yazar — o satır "belirsiz" DEĞİLDİR (işaretsiz değil,
 *  ÇOK işaretli) ve kendi kovasına gider. Alan hiç yoksa hüküm YOK: `null` döner ve
 *  çağıran onu "durumsuz" diye SAYAR, bir kovaya sıvamaz. */
function tabloKovasi(r: RoadmapTabloSatiri): string | null {
  if (r.durum !== null) return r.durum;
  return r.durumNeden !== null ? "cok_isaretli" : null;
}

function durumRozetiTonu(durum: string | null): "default" | "secondary" | "destructive" | "outline" | "ghost" {
  if (durum === "bloke") return "destructive";
  if (durum === "acik") return "default";
  if (durum === "askida") return "secondary";
  if (durum === "kapali") return "outline";
  return "ghost";
}

function MaddeKarti({ m }: { m: RoadmapMaddesi }) {
  // BAŞLIK ile HAM aynıysa gövdeyi ikinci kez basmıyoruz: `_roadmap_madde_basligi`
  // kısa maddelerde başlığı gövdenin kendisinden üretiyor, yani ikisi eş olabilir.
  const govde = m.ham !== null && m.ham !== m.baslik ? m.ham : null;

  return (
    <article className="flex flex-col gap-2 rounded-xl border bg-card p-3.5 text-card-foreground shadow-xs">
      <div className="flex items-start justify-between gap-2">
        {/* BAŞLIĞA ÜSTÜ-ÇİZİK UYGULANMIYOR: `ustu_cizili` maddenin GÖVDESİNDE bir
            üstü-çizik ARALIĞI olduğunu söyler, başlığın kendisinin çizildiğini DEĞİL
            (ayrıştırıcı başlığı üretirken `~~...~~` işaretlerini zaten söküyor,
            api.py:6648). Tüm başlığı çizmek, ölçülenden fazlasını iddia ederdi —
            bilgi aşağıdaki "geri alınmış" rozetinde duruyor. */}
        <h4 className="min-w-0 font-medium text-sm leading-5">
          {m.baslik ?? <span className="text-muted-foreground italic">başlık çıkarılamadı</span>}
        </h4>
        {m.durum ? (
          <Badge
            variant={durumRozetiTonu(m.durum)}
            className="shrink-0 text-[11px]"
            title={m.durumKanit ?? "ayrıştırıcı bu durumu hangi kelimeden okuduğunu yazmadı"}
          >
            {DURUM_ETIKETI[m.durum] ?? m.durum}
          </Badge>
        ) : (
          <Badge variant="ghost" className="shrink-0 text-[11px]" title="madde satırında `durum` alanı yok">
            durumsuz
          </Badge>
        )}
      </div>

      {govde ? <p className="line-clamp-3 text-muted-foreground text-xs leading-5">{govde}</p> : null}

      <div className="flex flex-wrap items-center gap-1.5">
        {m.altBolum ? (
          <Badge variant="secondary" className="max-w-full truncate text-[10px]" title={m.altBolum}>
            {m.altBolum}
          </Badge>
        ) : null}
        {m.ustuCizili ? (
          <Badge
            variant="outline"
            className="gap-1 text-[10px]"
            title="dosyada üstü çizili — bir kapanış iddiası GERİ ALINMIŞ olabilir; kapalı sayılmaz"
          >
            <Strikethrough className="size-3" aria-hidden />
            geri alınmış
          </Badge>
        ) : null}
        {m.hamKirpildi ? (
          <Badge
            variant="ghost"
            className="text-[10px]"
            title={`madde gövdesi uçta kırpıldı — tam uzunluk ${m.hamUzunluk ?? "?"} karakter`}
          >
            kırpıldı
          </Badge>
        ) : null}
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {m.satir === null ? "satırsız" : `satır ${m.satir}`}
        </span>
      </div>
    </article>
  );
}

/* TABLO SATIRI KARTI — madde kartından AYRI, çünkü birim ayrı. Bir tablo satırının
   "başlığı" yoktur; ilk hücre kalemin adıdır, kalanlar ADLI alanlardır ve o adlar
   tablonun kendi başlık satırından gelir (uydurulmuyor: `basliklar`). Hücre metni
   uçta 400 karakterde kırpılabilir ve kart bunu damgalar. */
function TabloSatiriKarti({ r }: { r: RoadmapTabloSatiri }) {
  const kova = tabloKovasi(r);
  const [ilk, ...kalan] = r.hucreler;

  return (
    <article className="flex flex-col gap-2 rounded-xl border border-dashed bg-card p-3.5 text-card-foreground shadow-xs">
      <div className="flex items-start justify-between gap-2">
        <h4 className="min-w-0 font-medium text-sm leading-5">
          {ilk !== undefined && ilk.trim() !== "" ? (
            <span className="line-clamp-2">{ilk}</span>
          ) : (
            <span className="text-muted-foreground italic">ilk hücre boş</span>
          )}
        </h4>
        {kova === null ? (
          <Badge variant="ghost" className="shrink-0 text-[11px]" title="satırda `durum` da `durum_neden` de yok">
            durumsuz
          </Badge>
        ) : (
          <Badge
            variant={kova === "cok_isaretli" ? "secondary" : durumRozetiTonu(kova)}
            className="shrink-0 text-[11px]"
            title={
              r.durumNeden ??
              "durum satırın hücrelerinde arandı; hangi kelimeden okunduğu `hucre_durum`da"
            }
          >
            {DURUM_ETIKETI[kova] ?? kova}
          </Badge>
        )}
      </div>

      {kalan.length > 0 ? (
        <dl className="flex flex-col gap-1">
          {kalan.map((h, i) => {
            const ad = r.basliklar[i + 1];
            if (h.trim() === "") return null;
            return (
              <div key={`${r.anahtar}-h${i}`} className="flex min-w-0 gap-1.5 text-xs leading-5">
                <dt className="shrink-0 text-[10px] text-muted-foreground uppercase">
                  {ad !== undefined && ad.trim() !== "" ? ad : `alan ${i + 2}`}
                </dt>
                <dd className="line-clamp-2 min-w-0 text-muted-foreground">{h}</dd>
              </div>
            );
          })}
        </dl>
      ) : null}

      <div className="flex flex-wrap items-center gap-1.5">
        {r.altBolum ? (
          <Badge variant="secondary" className="max-w-full truncate text-[10px]" title={r.altBolum}>
            {r.altBolum}
          </Badge>
        ) : null}
        {r.ustuCizili ? (
          <Badge
            variant="outline"
            className="gap-1 text-[10px]"
            title="satırda üstü çizili metin var — bir kapanış iddiası GERİ ALINMIŞ olabilir"
          >
            <Strikethrough className="size-3" aria-hidden />
            geri alınmış
          </Badge>
        ) : null}
        {r.kirpildi ? (
          <Badge variant="ghost" className="text-[10px]" title="satırın en az bir hücresi uçta kırpıldı">
            kırpıldı
          </Badge>
        ) : null}
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {r.satir === null ? "satırsız" : `satır ${r.satir}`}
        </span>
      </div>
    </article>
  );
}

/* ==================================================================================
   ŞEMA TAHTASI — belgenin kendi alanlarından çizilen DİNAMİK tahta
   ----------------------------------------------------------------------------------
   2026-09-01 göçünden önce bu yüzeyin tek anlatısı "kaç madde, hangi kovada"ydı;
   kalemin kendisi (kim sahibi, ne kadar iş, neyi bekliyor) yalnız ham metnin
   içinde yaşıyordu ve panoda OKUNAMIYORDU. Uç artık başlık satırını alanlarına
   ayırıyor (`sema`) ve tahta o alanlardan doğuyor.

   ÜÇ KURAL, ÜÇÜ DE ÖLÇÜLMÜŞ BİR KUSURUN KARŞILIĞI:
   1) SÜZGEÇ SEÇENEKLERİ GÖMÜLÜ DEĞİL — durum/bölüm/sahip listeleri gelen veriden
      doğar. Sözlüğü buraya yazmak, belgenin bir sonraki ekinde panoyu sessizce
      eksik gösterirdi (bu dosyanın kolon başlığındaki aynı yasak).
   2) İKİ BİRİM TOPLANMAZ — bullet madde ile `§2` tablo satırı aynı gramerle
      çizilir ama sayaç iki ayrı sayı basar: aynı `TSK` numarası ikisinde birden
      yaşayabilir (belgenin bilinçli geri-bağlantı deseni) ve toplamak çift sayardı.
   3) MUAF TARİHÇE BORÇ DEĞİL — `§7`/`§8` şema dışıdır ve öyle kalmasına operatör
      karar verdi. Sayısı GÖSTERİLİR ama "eksik" diye değil, kapsam beyanı olarak.
   ================================================================================== */
const SEMA_TAHTA_TAVANI = 40;

function statusRozetiTonu(status: string | null): "default" | "secondary" | "destructive" | "outline" | "ghost" {
  if (status === "OPERATOR") return "destructive";
  if (status === "ACTIVE" || status === "QUEUED" || status === "INTERIM") return "default";
  if (status === "GATED") return "secondary";
  if (status === "DONE" || status === "DROPPED") return "outline";
  return "ghost";
}

function SemaSatiri({ s }: { s: TahtaSatiri }) {
  const { sema } = s;
  return (
    <li className="flex flex-col gap-1.5 px-3 py-2.5">
      <div className="flex flex-wrap items-start gap-2">
        <Badge variant="outline" className="shrink-0 font-mono text-[11px]">
          {sema.id ?? "kimliksiz"}
        </Badge>
        <span className="min-w-0 flex-1 text-sm leading-5">
          {sema.ad ?? <span className="text-muted-foreground italic">ad okunamadı</span>}
        </span>
        {sema.status === null ? (
          <Badge
            variant="ghost"
            className="shrink-0 text-[11px]"
            title={sema.statusNeden ?? "uç durumu ölçemedi ve nedenini de yazmadı"}
          >
            {s.durum === "atif" ? "atıf" : "durum okunamadı"}
          </Badge>
        ) : (
          <Badge
            variant={statusRozetiTonu(sema.status)}
            className="shrink-0 text-[11px]"
            title={sema.statusDetay ?? sema.status}
          >
            {STATUS_ETIKETI[sema.status] ?? sema.status}
          </Badge>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[11px] text-muted-foreground">
        <span className="font-mono">{sema.section ?? "bölümsüz"}</span>
        {/* ALT BAŞLIK KIRPILIR AMA KAYBOLMAZ: `§2`nin tablo başlıkları sayaç ve tarih
            notlarıyla uzun (`H1 — … **10 açık** (2026-08-31 …)`), satıra sığmaz; tam
            metin `title`da durur. Kırpıp başlığı hiç göstermemek, satırın NEREDEN
            geldiğini silerdi — düzleştirmenin ilk kaybı tam olarak odur. */}
        {s.altBolum ? (
          <span className="max-w-[16rem] truncate" title={s.altBolum}>
            {s.altBolum}
          </span>
        ) : null}
        <span>{sema.owner ?? "sahipsiz"}</span>
        <span title="iş büyüklüğü; ölçülemediğinde belgede tire ile beyan edilir">
          boyut {sema.size ?? "yazılmadı"}
        </span>
        {sema.born ? <span>doğum {sema.born.slice(0, 10)}</span> : null}
        <Badge variant="ghost" className="text-[10px]" title="bullet madde mi, tahta tablosunun satırı mı">
          {sema.kaynak === "tablo" ? "tablo satırı" : "madde"}
        </Badge>
        <span className="ml-auto font-mono">{s.satir === null ? "satırsız" : `satır ${s.satir}`}</span>
      </div>

      {sema.status === "GATED" && sema.trigger ? (
        <p className="text-muted-foreground text-xs leading-5">
          <span className="text-[10px] uppercase">tetik</span> {sema.trigger}
        </p>
      ) : null}
      {sema.status === null && sema.statusNeden ? (
        <p className="text-muted-foreground text-xs leading-5">{sema.statusNeden}</p>
      ) : null}
    </li>
  );
}

function SuzgecSeridi({
  ad,
  secili,
  secenekler,
  sec,
}: {
  ad: string;
  secili: string | null;
  secenekler: readonly (readonly [string, string, number])[];
  sec: (v: string | null) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="mr-1 w-14 shrink-0 text-muted-foreground text-xs">{ad}</span>
      <Button
        variant={secili === null ? "default" : "outline"}
        size="sm"
        className="h-7 px-2.5 text-xs"
        onClick={() => sec(null)}
      >
        hepsi
      </Button>
      {secenekler.map(([deger, etiket, n]) => (
        <Button
          key={deger}
          variant={secili === deger ? "default" : "outline"}
          size="sm"
          className="h-7 px-2.5 text-xs"
          onClick={() => sec(secili === deger ? null : deger)}
        >
          {etiket} · {n}
        </Button>
      ))}
    </div>
  );
}

function SemaTahtasi({
  satirlar,
  muafTarihce,
  ihlalN,
}: {
  satirlar: readonly TahtaSatiri[];
  muafTarihce: number | null;
  ihlalN: number | null;
}) {
  const [status, setStatus] = useState<string | null>(null);
  const [bolum, setBolum] = useState<string | null>(null);
  const [sahip, setSahip] = useState<string | null>(null);

  const say = (secilenler: readonly TahtaSatiri[], anahtar: (s: TahtaSatiri) => string | null) => {
    const m = new Map<string, number>();
    for (const s of secilenler) {
      const k = anahtar(s);
      if (k !== null) m.set(k, (m.get(k) ?? 0) + 1);
    }
    return m;
  };

  const statusSayimi = say(satirlar, (s) => s.sema.status);
  const bolumSayimi = say(satirlar, (s) => s.sema.section);
  const sahipSayimi = say(satirlar, (s) => s.sema.owner);
  const olculemeyen = satirlar.filter((s) => s.sema.status === null).length;

  const suzulmus = satirlar.filter(
    (s) =>
      (status === null || s.sema.status === status) &&
      (bolum === null || s.sema.section === bolum) &&
      (sahip === null || s.sema.owner === sahip),
  );

  const gruplar = SINIF_SIRASI.map((g) => ({
    ad: g,
    satirlar: suzulmus.filter((s) => tahtaSinifi(s.sema) === g),
  })).filter((g) => g.satirlar.length > 0);

  const maddeN = suzulmus.filter((s) => s.sema.kaynak !== "tablo").length;
  const tabloN = suzulmus.length - maddeN;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ListChecks className="size-4 text-muted-foreground" aria-hidden />
          Kalem tahtası
        </CardTitle>
        <CardDescription>
          Belgenin kendi alanlarından çiziliyor — durum, sahip ve boyut kalemin başlık satırında
          yazılı; pano onları yorumlamıyor, okuyor.
        </CardDescription>
        <CardAction className="flex flex-wrap gap-1.5">
          <Badge variant="outline" className="tabular-nums">
            {maddeN} madde
          </Badge>
          <Badge variant="outline" className="tabular-nums">
            {tabloN} tablo satırı
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {ihlalN !== null && ihlalN > 0 ? (
          <Alert variant="destructive">
            <Info />
            <AlertTitle>{ihlalN} kalem başlık düzenine uymuyor</AlertTitle>
            <AlertDescription>
              Bu satırlar düzenli bir kalem gibi yazılmış ama alanları eksik ya da sırası bozuk —
              tahtada görünmüyorlar. Tarihçe muafiyetiyle karıştırılmamalı: bu bir bozulma.
            </AlertDescription>
          </Alert>
        ) : null}

        <SuzgecSeridi
          ad="DURUM"
          secili={status}
          secenekler={statusSirala(statusSayimi.keys()).flatMap((k) => {
            const n = statusSayimi.get(k);
            return n === undefined ? [] : [[k, STATUS_ETIKETI[k] ?? k, n] as const];
          })}
          sec={setStatus}
        />
        <SuzgecSeridi
          ad="BÖLÜM"
          secili={bolum}
          secenekler={[...bolumSayimi.entries()].sort().map(([k, n]) => [k, k, n] as const)}
          sec={setBolum}
        />
        <SuzgecSeridi
          ad="SAHİP"
          secili={sahip}
          secenekler={[...sahipSayimi.entries()].sort().map(([k, n]) => [k, k, n] as const)}
          sec={setSahip}
        />

        {gruplar.length === 0 ? (
          <p className="rounded-lg border border-dashed px-3 py-6 text-center text-muted-foreground text-xs">
            bu süzgeçte kalem yok
          </p>
        ) : null}

        {gruplar.map((g) => {
          const gosterilen = g.satirlar.slice(0, SEMA_TAHTA_TAVANI);
          return (
            <section key={g.ad} className="rounded-xl border">
              <header className="flex items-baseline justify-between gap-2 border-b bg-muted/30 px-3 py-2">
                <h4 className="font-medium text-sm">{g.ad}</h4>
                <span className="text-muted-foreground text-xs tabular-nums">
                  {g.satirlar.filter((s) => s.sema.kaynak !== "tablo").length} madde ·{" "}
                  {g.satirlar.filter((s) => s.sema.kaynak === "tablo").length} tablo satırı
                </span>
              </header>
              <ul className="divide-y">
                {gosterilen.map((s) => (
                  <SemaSatiri key={s.anahtar} s={s} />
                ))}
              </ul>
              {g.satirlar.length > gosterilen.length ? (
                <p className="border-t px-3 py-2 text-center text-muted-foreground text-xs">
                  {gosterilen.length} / {g.satirlar.length} gösteriliyor — kalan{" "}
                  {g.satirlar.length - gosterilen.length} satır çizilmedi (liste tavanı{" "}
                  {SEMA_TAHTA_TAVANI}).
                </p>
              ) : null}
            </section>
          );
        })}

        <p className="text-muted-foreground text-xs leading-5">
          İki birim ayrı sayılır ve TOPLANMAZ: aynı kalem numarası hem sıralı listede hem tahta
          tablosunda yaşayabilir; iki satırı tek sayıya katmak o kalemi çift sayardı.
          {olculemeyen > 0
            ? ` ${olculemeyen} satırın durumu bu satırda yazmıyor — başka bir kaleme havale ediyor ve o kalemin satırında okunuyor.`
            : ""}
          {muafTarihce !== null
            ? ` Ayrıca ${muafTarihce} kalem bu düzenin dışında: karar günlüğü ve arşiv bölümleri olduğu gibi korunuyor, düzene çevrilmiyor.`
            : " Düzen dışı kalem sayısı bildirilmedi."}
        </p>
      </CardContent>
    </Card>
  );
}

function Kolon({
  b,
  maddeler,
  tabloSatirlari,
}: {
  b: RoadmapBolumu;
  maddeler: readonly RoadmapMaddesi[];
  tabloSatirlari: readonly RoadmapTabloSatiri[];
}) {
  const gosterilen = maddeler.slice(0, KART_TAVANI);
  const tabloGosterilen = tabloSatirlari.slice(0, KART_TAVANI);
  const bosMu = gosterilen.length === 0 && tabloGosterilen.length === 0;

  return (
    <section className="flex min-h-0 flex-col rounded-xl border bg-muted/50">
      <div className="px-4 pt-4 pb-3">
        <h3 className="break-words font-medium text-base leading-tight">{bolumBasligi(b)}</h3>
        <p className="mt-1 text-muted-foreground text-sm tabular-nums leading-none">
          {maddeler.length} madde · {tabloSatirlari.length} tablo satırı
          {b.altBolumN > 0 ? ` · ${b.altBolumN} alt başlık` : ""}
        </p>
      </div>
      <div className="flex max-h-[34rem] min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto px-3 pb-3 [scrollbar-color:var(--border)_transparent] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1">
        {bosMu ? (
          <p className="rounded-lg border border-dashed px-3 py-6 text-center text-muted-foreground text-xs">
            bu süzgeçte kalem yok
          </p>
        ) : null}
        {gosterilen.map((m) => (
          <MaddeKarti key={m.anahtar} m={m} />
        ))}
        {maddeler.length > gosterilen.length ? (
          <p className="rounded-lg border border-dashed px-3 py-2 text-center text-muted-foreground text-xs">
            {gosterilen.length} / {maddeler.length} gösteriliyor — kalan {maddeler.length - gosterilen.length}{" "}
            madde tahtada ÇİZİLMEDİ (kart tavanı {KART_TAVANI}).
          </p>
        ) : null}
        {tabloGosterilen.map((r) => (
          <TabloSatiriKarti key={r.anahtar} r={r} />
        ))}
        {tabloSatirlari.length > tabloGosterilen.length ? (
          <p className="rounded-lg border border-dashed px-3 py-2 text-center text-muted-foreground text-xs">
            {tabloGosterilen.length} / {tabloSatirlari.length} tablo satırı gösteriliyor — kalan{" "}
            {tabloSatirlari.length - tabloGosterilen.length} satır ÇİZİLMEDİ (kart tavanı {KART_TAVANI}).
          </p>
        ) : null}
        {b.tabloAtlananN > 0 ? (
          <p
            className="rounded-lg border border-dashed px-3 py-2 text-center text-muted-foreground text-xs"
            title="uç bu blokları `|` ile başlıyor diye tablo sanmadı; nedenlerini gövdede sayıyor"
          >
            {b.tabloAtlananN} boru-karakterli blok tablo SAYILMADI (uç atladı, sessizce düşürmedi).
          </p>
        ) : null}
      </div>
    </section>
  );
}

export function YolHaritasi() {
  // NABIZ YOK (0): yol haritası bir BELGEdir, canlı bir ölçüm değil — dosyayı bir
  // insan düzenliyor. Zamanlayıcıyla çekmek 562 KB'lık ayrıştırmayı boşuna
  // tekrarlatır (uç önbellekli ama istek yine gider). Tazeleme yüzeye girişte olur.
  const uc = useApi<unknown>("/api/roadmap", 0);

  return (
    <section id="bolum-roadmap" className="flex scroll-mt-20 flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="flex items-center gap-2 font-semibold text-lg tracking-tight">
            <MapIkonu className="size-4 text-muted-foreground" aria-hidden />
            Yol haritası
          </h2>
          <p className="text-muted-foreground text-sm">Hangi iş hangi bölümde, hangi durumda?</p>
        </div>
        <SaltOkunurRozet not="Bu turda yazma ucu YOK — tahta yalnız gösterir; kaynağı ROADMAP.md ve onu bir insan düzenliyor." />
      </div>

      <Hal d={uc} ad="/api/roadmap" iskelet={<Skeleton className="h-64 w-full" />} ciz={(v) => <Tahta ham={v} />} />
    </section>
  );
}

function Tahta({ ham }: { ham: unknown }) {
  const okuma: RoadmapOkumasi = useMemo(() => roadmapOku(ham), [ham]);
  const [suzgec, setSuzgec] = useState<string | null>(null);
  /* GRAFİK SÜZGECİ (yalnız iki çubuk grafiği etkiler, tahtayı DEĞİL): işaretsiz
     kalemler dağılımı boğuyor — belgenin 450 maddesinin 327'si düzyazıdır ve
     `§7 KARAR GÜNLÜĞÜ` tek başına 163'ünü taşır. Çözüm §7'yi ADIYLA gizlemek
     DEĞİL (§-numaraları 2026-08-17'de bir kez zaten kaydı; bölüm adı gömmek bu
     dosyanın kendi başlığındaki yasağa girer), İŞARETSİZ KOVASINI kapatmaktır:
     kural bölüm ayrımı yapmaz, her bölüme aynı ölçütle uygulanır ve bir günlük
     bölümü kendiliğinden sıfıra iner — çünkü kayıt kalem değildir. */
  const [isaretsizGizli, setIsaretsizGizli] = useState(false);

  if (okuma.tur === "hata") {
    return (
      <Alert variant="destructive">
        <FileWarning />
        <AlertTitle>Yol haritası dosyası okunamadı</AlertTitle>
        <AlertDescription>
          <span className="block">{okuma.hata}</span>
          {okuma.yol ? (
            <span className="mt-1 block">
              Aranan yol: <code className="font-mono text-xs">{okuma.yol}</code>
            </span>
          ) : (
            <span className="mt-1 block">Uç hangi yolu denediğini yazmadı.</span>
          )}
          <span className="mt-1 block">Bu "yol haritası boş" DEĞİL — dosyaya erişilemedi.</span>
        </AlertDescription>
      </Alert>
    );
  }

  if (okuma.tur === "tanimadi") {
    return (
      <Alert variant="destructive">
        <FileQuestion />
        <AlertTitle>`/api/roadmap` gövde şekli tanınmadı</AlertTitle>
        <AlertDescription>
          <span className="block">
            Uç cevap verdi ama `bolumler` bir dizi değil. Tahtayı hangi alandan kuracağımızı
            ölçemedik — bu "yol haritası boş" DEĞİL.
          </span>
          <span className="mt-2 block">
            Üst düzey anahtarlar:{" "}
            {okuma.ustAnahtarlar.length === 0 ? (
              <em>hiç yok (gövde nesne değil)</em>
            ) : (
              <code className="font-mono text-xs">{okuma.ustAnahtarlar.join(", ")}</code>
            )}
          </span>
          <code className="mt-2 block max-h-32 overflow-auto rounded bg-muted p-2 font-mono text-[11px] text-muted-foreground">
            {okuma.ornek}
          </code>
        </AlertDescription>
      </Alert>
    );
  }

  const { bolumler, sayim, kunye } = okuma;
  const tumMaddeler = bolumler.flatMap((b) => b.maddeler);
  // ŞEMALI KALEMLER — iki birimden gelir, TOPLANMAZ; `tahtaSatirlari` her satıra
  // hangisinden geldiğini yazar ve tahta iki sayacı ayrı basar.
  const semaSatirlari = tahtaSatirlari(bolumler);

  // KENDİ SAYIMIMIZ — kart başına bir madde. Ucun `sayim.madde_n` beyanıyla
  // karşılaştırılıyor: ayrışırsa düzleştirme bir dalı atlıyordur ve bunu ekranda
  // söylemek, sessizce eksik tahta çizmekten iyidir.
  const bizimN = tumMaddeler.length;
  const beyanAyrisiyor = sayim.maddeN !== null && sayim.maddeN !== bizimN;

  const kendiDurumSayimi = new Map<string, number>();
  let durumsuz = 0;
  for (const m of tumMaddeler) {
    if (m.durum === null) durumsuz += 1;
    else kendiDurumSayimi.set(m.durum, (kendiDurumSayimi.get(m.durum) ?? 0) + 1);
  }

  // TABLO TARAFI — madde tarafının birebir ikizi, ve İKİSİ TOPLANMAZ.
  const tumTabloSatirlari = bolumler.flatMap((b) => b.tabloSatirlari);
  const bizimTabloN = tumTabloSatirlari.length;
  const tabloBeyanAyrisiyor = sayim.tabloSatirN !== null && sayim.tabloSatirN !== bizimTabloN;
  const kendiTabloSayimi = new Map<string, number>();
  let tabloDurumsuz = 0;
  for (const r of tumTabloSatirlari) {
    const k = tabloKovasi(r);
    if (k === null) tabloDurumsuz += 1;
    else kendiTabloSayimi.set(k, (kendiTabloSayimi.get(k) ?? 0) + 1);
  }

  const suzulmus = (b: RoadmapBolumu) =>
    suzgec === null ? b.maddeler : b.maddeler.filter((m) => m.durum === suzgec);
  const suzulmusTablo = (b: RoadmapBolumu) =>
    suzgec === null ? b.tabloSatirlari : b.tabloSatirlari.filter((r) => tabloKovasi(r) === suzgec);

  const kolonAdi = (b: RoadmapBolumu) => b.no ?? (b.baslik ?? "?").slice(0, 18);
  const grafikKovalari = isaretsizGizli
    ? DURUM_SIRASI.filter((d) => d !== "belirsiz")
    : DURUM_SIRASI;
  const tabloGrafikKovalari = isaretsizGizli
    ? TABLO_DURUM_SIRASI.filter((d) => d !== "belirsiz")
    : TABLO_DURUM_SIRASI;

  const grafikVerisi = bolumler.map((b) => {
    const satir: Record<string, string | number> = { bolum: kolonAdi(b) };
    for (const d of grafikKovalari) satir[d] = b.maddeler.filter((m) => m.durum === d).length;
    return satir;
  });
  const tabloGrafikVerisi = bolumler.map((b) => {
    const satir: Record<string, string | number> = { bolum: kolonAdi(b) };
    for (const d of tabloGrafikKovalari) {
      satir[d] = b.tabloSatirlari.filter((r) => tabloKovasi(r) === d).length;
    }
    return satir;
  });
  const gizlenenN = (kendiDurumSayimi.get("belirsiz") ?? 0) + (kendiTabloSayimi.get("belirsiz") ?? 0);

  interface DurumSatiri {
    readonly durum: string;
    readonly ucSayimi: number | null;
    readonly panoSayimi: number;
    readonly tabloUc: number | null;
    readonly tabloPano: number;
  }
  const durumSatiriKur = (d: string): DurumSatiri => ({
    durum: d,
    ucSayimi: sayim.durum.get(d) ?? null,
    panoSayimi: kendiDurumSayimi.get(d) ?? 0,
    tabloUc: sayim.tabloDurum.get(d) ?? null,
    tabloPano: kendiTabloSayimi.get(d) ?? 0,
  });
  // Ucun sözlüğünde OLMAYAN bir durum gelirse (ayrıştırıcı büyürse) sessizce
  // düşmesin: bilinmeyen kovalar da tabloya girer. Kaynak ÜÇ küme: bildiğimiz sıra
  // + panonun madde sayımı + panonun tablo sayımı.
  const tumKovalar: string[] = [...TABLO_DURUM_SIRASI];
  for (const d of [...kendiDurumSayimi.keys(), ...kendiTabloSayimi.keys()]) {
    if (!tumKovalar.includes(d)) tumKovalar.push(d);
  }
  const durumSatirlari: DurumSatiri[] = tumKovalar.map(durumSatiriKur);

  return (
    <div className="flex flex-col gap-4">
      {/* ------------------------------ KÜNYE ---------------------------- */}
      <div className="flex flex-wrap items-center gap-1.5 rounded-lg border bg-muted/30 p-3">
        <span className="text-muted-foreground text-xs">KAYNAK</span>
        <code className="font-mono text-xs">{kunye.yol ?? "yol yazılmadı"}</code>
        {kunye.satirN !== null ? (
          <Badge variant="ghost" className="tabular-nums text-[11px]">
            {kunye.satirN} satır
          </Badge>
        ) : null}
        {kunye.bayt !== null ? (
          <Badge variant="ghost" className="tabular-nums text-[11px]">
            {Math.round(kunye.bayt / 1024)} KB
          </Badge>
        ) : null}
        {kunye.mtime !== null ? (
          <Badge variant="outline" className="text-[11px]" title="dosyanın son değişiklik damgası (UTC)">
            {kunye.mtime.replace("T", " ").replace("+00:00", "Z")}
          </Badge>
        ) : (
          <Badge variant="ghost" className="text-[11px]" title="uç `mtime` göndermedi">
            tarih ölçülemedi
          </Badge>
        )}
        {kunye.hamTavan !== null ? (
          <Badge
            variant="ghost"
            className="text-[11px]"
            title="madde gövdeleri bu karakterde kırpılıyor; kırpılan kart 'kırpıldı' damgası taşır"
          >
            gövde tavanı {kunye.hamTavan}
          </Badge>
        ) : null}
      </div>

      {okuma.okunamayan > 0 ? (
        <Alert variant="destructive">
          <Info />
          <AlertTitle>{okuma.okunamayan} satır okunamadı</AlertTitle>
          <AlertDescription>
            Bu bölüm/madde satırları nesne değildi ve tahtanın DIŞINDA kaldı — sayaçlar onları
            içermiyor.
          </AlertDescription>
        </Alert>
      ) : null}

      {beyanAyrisiyor ? (
        <Alert variant="destructive">
          <Info />
          <AlertTitle>Madde sayısı ayrışıyor</AlertTitle>
          <AlertDescription>
            Uç {sayim.maddeN} madde beyan etti, pano ağacı düzleştirince {bizimN} madde saydı. İkisi
            aynı ağaca bakmalıydı; fark, tahtanın belgenin bir dalını atladığına işaret eder.
          </AlertDescription>
        </Alert>
      ) : null}

      {tabloBeyanAyrisiyor ? (
        <Alert variant="destructive">
          <Info />
          <AlertTitle>Tablo satırı sayısı ayrışıyor</AlertTitle>
          <AlertDescription>
            Uç {sayim.tabloSatirN} tablo satırı beyan etti, pano {bizimTabloN} saydı. Madde tarafının
            ikizi bir kapı: tablo dalı sessizce atlanırsa `§2 TAHTA` yine boş görünürdü — bu yüzey
            bir kez tam olarak bu yüzden yanlış çizmişti.
          </AlertDescription>
        </Alert>
      ) : null}

      {sayim.tabloAtlananN !== null && sayim.tabloAtlananN > 0 ? (
        <Alert>
          <Info />
          <AlertTitle>{sayim.tabloAtlananN} boru-karakterli blok tablo sayılmadı</AlertTitle>
          <AlertDescription>
            Uç bu blokları markdown tablosu olarak ayrıştıramadı (ayraç satırı yok ya da başlık
            satırı üstünde değil) ve bunu SESSİZCE düşürmek yerine sayıyor. İçlerindeki satırlar
            aşağıdaki hiçbir sayaca girmiyor.
          </AlertDescription>
        </Alert>
      ) : null}

      {/* ----------------------- ŞEMA TAHTASI ---------------------------- */}
      {/* EN ÜSTTE, ÇÜNKÜ ASIL SORU BU: "hangi iş hangi durumda, kimde?"
          Aşağıdaki grafikler belgenin YAPISINI ölçüyor (kaç madde, kaç tablo
          satırı, hangi kovada) — okuyucunun ilk ihtiyacı o değil, kalemin
          kendisi. Şema alanları açılana dek bu soruyu pano cevaplayamıyordu. */}
      <SemaTahtasi
        satirlar={semaSatirlari}
        muafTarihce={sayim.sema.muafTarihce}
        ihlalN={sayim.sema.ihlalN}
      />

      {/* --------------------------- ÜÇ ÖLÇÜM --------------------------- */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-muted-foreground text-xs">GRAFİK</span>
        <Button
          variant={isaretsizGizli ? "default" : "outline"}
          size="sm"
          className="h-7 px-2.5 text-xs"
          onClick={() => setIsaretsizGizli(!isaretsizGizli)}
          title="Yalnız iki çubuk grafiğini etkiler; aşağıdaki tahta ve süzgeç değişmez."
        >
          {isaretsizGizli ? "işaretsizler gizli" : "işaretsizleri gizle"} · {gizlenenN}
        </Button>
        <span className="text-muted-foreground text-xs leading-5">
          {isaretsizGizli
            ? "İşaretsiz kova iki grafikten de çıkarıldı — kural bölüm ayırmaz, hepsine aynı uygulanır. Kronolojik bir günlük bölümü kendiliğinden sıfıra iner: kayıt kalem değildir."
            : "İşaretsiz kova dağılımı boğuyorsa kapatabilirsin. Sayı SİLİNMEZ, yalnız çizilmez."}
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rows3 className="size-4 text-muted-foreground" aria-hidden />
              Bölüm başına madde
            </CardTitle>
            <CardDescription>
              Kolonlar bu dağılımdan doğuyor — bölüm adları belgeden okundu, panoya gömülü değil.
            </CardDescription>
            <CardAction>
              <Badge variant="outline" className="tabular-nums">
                {bolumler.length} bölüm
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="min-w-0 overflow-x-auto">
              <ChartContainer
                config={durumAyari}
                className="w-full"
                style={{ height: `${Math.max(200, bolumler.length * 34 + 40)}px` }}
              >
                <BarChart accessibilityLayer data={grafikVerisi} layout="vertical" margin={{ left: 4, right: 16 }}>
                  <CartesianGrid horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="bolum"
                    axisLine={false}
                    tickLine={false}
                    tickMargin={6}
                    width={64}
                    tick={{ fontSize: 11 }}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "var(--muted)" }} />
                  <ChartLegend
                    align="right"
                    verticalAlign="top"
                    content={<ChartLegendContent className="justify-end" />}
                  />
                  {grafikKovalari.map((d) => (
                    <Bar isAnimationActive={false} key={d} dataKey={d} stackId="d" fill={`var(--color-${d})`} />
                  ))}
                </BarChart>
              </ChartContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rows3 className="size-4 text-muted-foreground" aria-hidden />
              Bölüm başına tablo satırı
            </CardTitle>
            <CardDescription>
              Maddeyle TOPLANMAZ — ayrı birim. `§2 TAHTA` tamamen tablodur ve bu grafik açılana dek
              panoda hiç görünmüyordu.
            </CardDescription>
            <CardAction>
              <Badge variant="outline" className="tabular-nums">
                {bizimTabloN} satır
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="min-w-0 overflow-x-auto">
              <ChartContainer
                config={durumAyari}
                className="w-full"
                style={{ height: `${Math.max(200, bolumler.length * 34 + 40)}px` }}
              >
                <BarChart
                  accessibilityLayer
                  data={tabloGrafikVerisi}
                  layout="vertical"
                  margin={{ left: 4, right: 16 }}
                >
                  <CartesianGrid horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="bolum"
                    axisLine={false}
                    tickLine={false}
                    tickMargin={6}
                    width={64}
                    tick={{ fontSize: 11 }}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "var(--muted)" }} />
                  <ChartLegend
                    align="right"
                    verticalAlign="top"
                    content={<ChartLegendContent className="justify-end" />}
                  />
                  {tabloGrafikKovalari.map((d) => (
                    <Bar isAnimationActive={false} key={d} dataKey={d} stackId="t" fill={`var(--color-${d})`} />
                  ))}
                </BarChart>
              </ChartContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <Card>
          <CardHeader>
            <CardTitle>Durum dağılımı</CardTitle>
            <CardDescription>
              Ucun ayrıştırıcısının kovaları, İKİ BİRİM için ayrı ayrı — pano bunları birleştirmiyor,
              yorumlamıyor, toplamıyor. Her kovada uç beyanı ile pano sayımı yan yana: ayrışırlarsa
              kırmızı.
            </CardDescription>
            <CardAction className="flex gap-1.5">
              <Badge variant="outline" className="tabular-nums">
                {bizimN} madde
              </Badge>
              <Badge variant="outline" className="tabular-nums">
                {bizimTabloN} satır
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="min-w-0 overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow>
                    <TableHead>Durum</TableHead>
                    <TableHead>Madde: uç</TableHead>
                    <TableHead>Madde: pano</TableHead>
                    <TableHead>Tablo: uç</TableHead>
                    <TableHead>Tablo: pano</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {durumSatirlari.map((s) => (
                    <TableRow key={s.durum}>
                      <TableCell>
                        <Badge variant={durumRozetiTonu(s.durum)} className="text-[11px]">
                          {DURUM_ETIKETI[s.durum] ?? s.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="tabular-nums text-xs">
                        {s.ucSayimi === null ? (
                          <span className="text-muted-foreground" title="uç bu aralığı `sayim.durum` içinde göndermedi">
                            ölçülemedi
                          </span>
                        ) : (
                          s.ucSayimi
                        )}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "tabular-nums text-xs",
                          s.ucSayimi !== null && s.ucSayimi !== s.panoSayimi && "font-medium text-destructive",
                        )}
                      >
                        {s.panoSayimi}
                      </TableCell>
                      <TableCell className="tabular-nums text-xs">
                        {s.tabloUc === null ? (
                          <span
                            className="text-muted-foreground"
                            title="uç bu kovayı `sayim.tablo_durum` içinde göndermedi"
                          >
                            ölçülemedi
                          </span>
                        ) : (
                          s.tabloUc
                        )}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "tabular-nums text-xs",
                          s.tabloUc !== null && s.tabloUc !== s.tabloPano && "font-medium text-destructive",
                        )}
                      >
                        {s.tabloPano}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <p className="text-muted-foreground text-xs leading-5">
              "belirsiz" AÇIK DEMEK DEĞİLDİR: belgedeki maddelerin çoğu düzyazıdır ve durum işareti
              taşımaz. Onları "açık" saymak, tahtanın üstüne ölçülmemiş bir sayı yazmak olurdu.
              "çok işaretli" de belirsiz DEĞİLDİR: uç o satırı tek hükme indirmedi çünkü hücreleri
              iki rozet taşıyor (örn. karar verilmiş = kapalı AMA kapı operatörde = bloke) — çelişki
              olmayabilir de, ve onu bir sezgiyle çözmek ölçülmemiş bir hükmü ölçülmüş göstermek
              olurdu.
              {durumsuz > 0 ? ` Ayrıca ${durumsuz} maddede \`durum\` alanı hiç yok.` : ""}
              {tabloDurumsuz > 0 ? ` ${tabloDurumsuz} tablo satırında ne \`durum\` ne \`durum_neden\` var.` : ""}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* --------------------------- SÜZGEÇ ------------------------------ */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-muted-foreground text-xs">SÜZGEÇ</span>
        <Button
          variant={suzgec === null ? "default" : "outline"}
          size="sm"
          className="h-7 px-2.5 text-xs"
          onClick={() => setSuzgec(null)}
        >
          hepsi · {bizimN}+{bizimTabloN}
        </Button>
        {durumSatirlari.map((s) => (
          <Button
            key={s.durum}
            variant={suzgec === s.durum ? "default" : "outline"}
            size="sm"
            className="h-7 px-2.5 text-xs"
            onClick={() => setSuzgec(suzgec === s.durum ? null : s.durum)}
            title={`${s.panoSayimi} madde · ${s.tabloPano} tablo satırı — ayrı birim, toplanmaz`}
          >
            {DURUM_ETIKETI[s.durum] ?? s.durum} · {s.panoSayimi}+{s.tabloPano}
          </Button>
        ))}
      </div>

      {/* ---------------------------- TAHTA ------------------------------ */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {bolumler.map((b) => (
          <Kolon key={b.anahtar} b={b} maddeler={suzulmus(b)} tabloSatirlari={suzulmusTablo(b)} />
        ))}
      </div>
    </div>
  );
}
