"use client";

/* ============================================================================
   #ÖNERİ-HATTI — hipotez defteri, konuşma grameriyle
   ----------------------------------------------------------------------------
   BURADA UYDURULAN BİR MESAJ YOK. Her balon `state/hypotheses.jsonl`in BİR
   satırından geliyor ve iki tarafı var:
     · SOL  (üreteç) — `rationale` alanı. Bu gerçekten ajanın kendi cümlesidir:
                       hermes bir öneri üretirken gerekçesini bu alana yazıyor
                       (ölçüldü: 41/41 satırda dolu, ortalama birkaç yüz karakter).
     · SAĞ  (kapı)   — `status` + `reject_reasons` + varsa `realized_delta`. Yani
                       cevap veren OPERATÖR DEĞİL, backtest/bekçi kapısıdır ve
                       balonun başlığı bunu açıkça yazar. "Sen" diye bir taraf
                       çizmek, hiç kurulmamış bir diyaloğu var göstermek olurdu.

   NEDEN KANAL, NEDEN BOT DEĞİL (2026-08-31, mesajlaşma maketi): bu defterde iki
   taraf var ve ikisi de tek bir "kişi" değil — üreteç kolları (deterministik +
   `hermes:*`) ve kapı. Sol listede bu yüzden AJANLAR bölümünde değil KANALLAR
   bölümünde duruyor: bir kanalda çok konuşan olur, bir botta bir tane.

   KRONOLOJİK VE ESKİDEN YENİYE: sohbet grameri budur. Defterin kendi sırası da
   bu (JSONL ekleme sırası) — yeniden sıralamıyoruz, yalnız `ts` yazılmamış
   satırları sona alıyoruz ki tarih ayracı yalan söylemesin.

   GÜN AYRACI ÖLÇÜLEN DAMGADAN: `ts` yoksa ayraç "tarihsiz" der. Bugünün tarihini
   varsaymak, damgasız bir satırı bugün konuşulmuş gibi gösterirdi.

   ARAMA NEREYE GİTTİ (bedel beyanı): eski kabukta arama kutusu bu panelin
   içindeydi. Maket onu sol sütuna, tek arama kutusuna taşıdı — kutu "ajan, kanal
   ya da mesaj ara" diyor, yani bu paneldeki metinleri de süzmeye devam etmesi
   gerekiyordu ve ediyor (`arama` özelliği yukarıdan iniyor). ÜÇ KOVALI SÜZGEÇ
   (hepsi / sonucu yazılmış / kapıda düşen) DÜŞÜRÜLMEDİ: makette görünmüyordu ama
   kaldırmak ölçülmüş bir işlevi kaybetmekti — panelin üstünde ince bir şerit
   olarak duruyor.
   ============================================================================ */
import { useMemo, useState } from "react";

import { Bot, LockKeyhole, MessageSquareOff, ScrollText, Send, ShieldCheck } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bubble, BubbleContent, BubbleGroup } from "@/components/ui/bubble";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea } from "@/components/ui/input-group";
import { Marker, MarkerContent } from "@/components/ui/marker";
import { Message, MessageAvatar, MessageContent, MessageFooter, MessageHeader } from "@/components/ui/message";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

import { DURUM_SOZLUGU, bicimSayi, gunMetni, zamanMetni, type Hipotez } from "./ortak";

/* ---- SIRALAMA + SÜZME ---------------------------------------------------- */

function damga(h: Hipotez): number {
  if (h.ts === null) return Number.POSITIVE_INFINITY; // damgasız satırlar SONA — tarih ayracı yalan söylemesin
  const t = Date.parse(h.ts);
  return Number.isNaN(t) ? Number.POSITIVE_INFINITY : t;
}

type Suzgec = "hepsi" | "sonuclanan" | "reddedilen";

const SUZGEC_ETIKET: Readonly<Record<Suzgec, string>> = {
  hepsi: "Hepsi",
  sonuclanan: "Sonucu yazılmış",
  reddedilen: "Kapıda düşen",
};

function suzgectenGecer(h: Hipotez, s: Suzgec): boolean {
  if (s === "hepsi") return true;
  if (s === "sonuclanan") return h.gerceklesenDelta !== null;
  return (h.durum ?? "").startsWith("rejected") || h.durum === "rolled_back";
}

/* ---- KANAL AKIŞI --------------------------------------------------------- */

export function KanalAkisi({
  hipotezler,
  hafizaBasliklari,
  hafizaOlculemediNedeni,
  arama,
}: {
  hipotezler: readonly Hipotez[];
  /** `lessons.md` başlıkları — ajanın HER yansımaya enjekte edilen kalıcı hafızası. */
  hafizaBasliklari: readonly { readonly baslik: string; readonly n: number }[];
  hafizaOlculemediNedeni: string | null;
  /** Sol sütundaki tek arama kutusu — liste ile aynı sorgu. */
  arama: string;
}) {
  const [suzgec, setSuzgec] = useState<Suzgec>("hepsi");

  const sirali = useMemo(() => [...hipotezler].sort((a, b) => damga(a) - damga(b)), [hipotezler]);

  const gorunen = useMemo(() => {
    const q = arama.trim().toLocaleLowerCase("tr-TR");
    return sirali.filter((h) => {
      if (!suzgectenGecer(h, suzgec)) return false;
      if (q === "") return true;
      const havuz = [h.degisken, h.gerekce, h.durum, h.kaynak, h.id, h.rejim, ...h.redNedenleri]
        .filter((x): x is string => typeof x === "string")
        .join(" ")
        .toLocaleLowerCase("tr-TR");
      return havuz.includes(q);
    });
  }, [sirali, arama, suzgec]);

  return (
    <div className="flex flex-col gap-4 px-4 py-4 sm:px-6">
      <div className="flex flex-wrap items-center gap-2">
        <ToggleGroup
          type="single"
          variant="outline"
          size="sm"
          spacing={0}
          value={suzgec}
          onValueChange={(v) => {
            // BOŞ DEĞER YUTULMUYOR: ToggleGroup seçimi kaldırınca "" gönderiyor;
            // bunu "hepsi"ye çevirmezsek hiçbir kova seçili olmadan liste boşalır
            // ve operatör bunu "kayıt yok" diye okurdu.
            if (v === "hepsi" || v === "sonuclanan" || v === "reddedilen") setSuzgec(v);
            else setSuzgec("hepsi");
          }}
          aria-label="Öneri süzgeci"
        >
          {(Object.keys(SUZGEC_ETIKET) as Suzgec[]).map((k) => (
            <ToggleGroupItem key={k} value={k} className="text-xs">
              {SUZGEC_ETIKET[k]}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        <span className="text-muted-foreground text-xs tabular-nums">
          {bicimSayi(gorunen.length)} / {bicimSayi(hipotezler.length)} kayıt
        </span>
      </div>

      <HafizaMesaji basliklar={hafizaBasliklari} neden={hafizaOlculemediNedeni} />

      {gorunen.length === 0 ? (
        <Empty className="border-0">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <MessageSquareOff />
            </EmptyMedia>
            <EmptyTitle>Süzgeç hiçbir kaydı geçirmedi</EmptyTitle>
            <EmptyDescription>
              Bu, defterin boş olduğu anlamına GELMEZ: defterde {bicimSayi(hipotezler.length)} kayıt
              var, aramayı/süzgeci daraltan sensin.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        gorunen.map((h, i) => {
          const oncekiGun = i === 0 ? null : gunMetni(gorunen[i - 1]?.ts ?? null);
          const buGun = gunMetni(h.ts);
          return (
            <div key={h.id ?? `satir-${i}`} className="flex flex-col gap-4">
              {buGun !== oncekiGun ? (
                <Marker variant="separator">
                  <MarkerContent>{buGun ?? "tarihsiz (damga alanı yok)"}</MarkerContent>
                </Marker>
              ) : null}
              <UretecBalonu h={h} />
              <KapiBalonu h={h} />
            </div>
          );
        })
      )}
    </div>
  );
}

/* ---- SABİTLENMİŞ DERS ---------------------------------------------------- */

/** Maketin en üstteki mavi kartı: damıtılmış ders. İçerik değişmedi — yeri ve
 *  kabı değişti (balon değil, akışın başına sabitlenmiş kart). */
function HafizaMesaji({
  basliklar,
  neden,
}: {
  basliklar: readonly { readonly baslik: string; readonly n: number }[];
  neden: string | null;
}) {
  return (
    <div className="rounded-xl border border-sky-500/25 bg-sky-500/5 px-4 py-3">
      <p className="flex items-center gap-1.5 font-semibold text-[10px] text-sky-700 uppercase tracking-wider dark:text-sky-400">
        <ScrollText className="size-3.5" aria-hidden />
        sabitlenmiş · kalıcı hafıza
      </p>
      <p className="mt-1.5 text-sm leading-relaxed">
        Bu metin ajanın HER yansımasına enjekte ediliyor. Yani aşağıdaki her öneri, bu hafızayı
        okumuş bir ajandan geliyor.
      </p>
      {neden !== null ? (
        <p className="mt-1.5 text-muted-foreground text-xs leading-relaxed">
          Başlıklar ölçülemedi: {neden}
        </p>
      ) : basliklar.length === 0 ? (
        <p className="mt-1.5 text-muted-foreground text-xs leading-relaxed">
          Metinde `##` başlığı yok — dosya var ama bölümlenmemiş.
        </p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {basliklar.map((b) => (
            <li key={b.baslik}>
              <Badge variant="outline" className="bg-card text-[11px]">
                {b.baslik} · {bicimSayi(b.n)} madde
              </Badge>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-muted-foreground text-xs">
        Tam metin:{" "}
        {/* BAĞ METNİ NEREYE GİDECEĞİNİ SÖYLÜYOR, ADRES DE ORAYA GİDİYOR (nihai
            inceleme Ö-1, 2026-09-03): burada önce sorgusuz adres vardı ve bağ
            "Meridian dersleri" derken sayfa ağacını açıyordu.
            TSK-118'DE GÜNCELLENDİ (2026-09-03, operatör K8): dersler Bilgi
            Tabanı'nın sekmesi olmaktan çıkıp kendi görünümüne (`hafiza-dersler`,
            `alanlar.ts`) taşındı; bağ ve kırıntı metni buna göre değişti. Eski
            sekmeli adres (`hafiza-bilgi?sekme=dersler`) hâlâ çalışır — köprüsü
            `gorunumler.ts::gorunumCoz`de — ama bu bağ artık DOĞRUDAN yeni
            görünüme gider, köprüye ihtiyaç duymaz. */}
        <a className="underline underline-offset-2" href="#/dashboard/memory/hafiza-dersler">
          Hafıza → Meridian dersleri
        </a>
      </p>
    </div>
  );
}

/* ---- BALONLAR ------------------------------------------------------------ */

function bas(kaynak: string | null): string {
  if (kaynak === null) return "?";
  if (kaynak.startsWith("hermes:")) return kaynak.slice(7, 9).toLocaleUpperCase("tr-TR");
  return kaynak.slice(0, 2).toLocaleUpperCase("tr-TR");
}

function UretecBalonu({ h }: { h: Hipotez }) {
  const zaman = zamanMetni(h.ts);
  return (
    <Message align="start">
      <MessageAvatar>
        <Avatar className="size-7">
          <AvatarFallback className="bg-muted text-[11px] text-foreground">
            {h.kaynak?.startsWith("hermes:") ? bas(h.kaynak) : <Bot className="size-3.5" aria-hidden />}
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>
      <MessageContent>
        <MessageHeader className="gap-2">
          <span>üreteç · {h.kaynak ?? "kaynak kaydedilmemiş"}</span>
          {h.id === null ? null : <span className="text-muted-foreground/70">· {h.id}</span>}
          {h.asiriUyumSupheli === true ? (
            <Badge variant="destructive" className="text-[10px]">
              aşırı uyum şüphesi
            </Badge>
          ) : null}
        </MessageHeader>
        <BubbleGroup>
          <Bubble variant="outline" align="start">
            <BubbleContent className="flex flex-col gap-2">
              <p className="font-medium text-sm">
                <code className="font-mono">{h.degisken ?? "(değişken kaydedilmemiş)"}</code>{" "}
                <span className="text-muted-foreground">
                  {h.eski ?? "?"} → {h.yeni ?? "?"}
                </span>
              </p>
              <p className="whitespace-pre-line text-sm leading-relaxed">
                {h.gerekce ?? "Bu satırda gerekçe alanı yok — üreteç nedenini kaydetmemiş."}
              </p>
              <ul className="flex flex-wrap gap-1.5 pt-0.5">
                <Cip etiket="rejim" deger={h.rejim} />
                <Cip etiket="piyasa" deger={h.piyasaRejimi} />
                <Cip etiket="güven" deger={h.guven === null ? null : `%${bicimSayi(h.guven * 100, 0)}`} />
                <Cip
                  etiket="tahmin Δ"
                  deger={h.tahminDelta === null ? null : bicimSayi(h.tahminDelta, 4, true)}
                />
                <Cip etiket="yön" deger={h.tahminYon} />
                <Cip
                  etiket="sürüm"
                  deger={h.surumDen === null && h.surumE === null ? null : `${h.surumDen ?? "?"} → ${h.surumE ?? "?"}`}
                />
              </ul>
            </BubbleContent>
          </Bubble>
        </BubbleGroup>
        <MessageFooter>{zaman ?? "damga yok"}</MessageFooter>
      </MessageContent>
    </Message>
  );
}

function KapiBalonu({ h }: { h: Hipotez }) {
  const sozluk = h.durum === null ? undefined : DURUM_SOZLUGU[h.durum];
  const ton = sozluk?.ton ?? "notr";
  return (
    <Message align="end">
      <MessageAvatar>
        <Avatar className="size-7">
          <AvatarFallback className="bg-muted text-foreground">
            <ShieldCheck className="size-3.5" aria-hidden />
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>
      <MessageContent>
        <MessageHeader className="gap-2">
          <span>kapı · {h.backtestVar ? "backtest + bekçi" : "bekçi"}</span>
        </MessageHeader>
        <BubbleGroup>
          <Bubble
            variant={ton === "olumsuz" ? "destructive" : ton === "olumlu" ? "tinted" : "secondary"}
            align="end"
          >
            <BubbleContent className="flex flex-col gap-2">
              <p className="font-medium text-sm">
                {sozluk?.etiket ?? h.durum ?? "hüküm kaydedilmemiş"}
                {sozluk === undefined && h.durum !== null ? (
                  <span className="ml-1 font-normal text-xs opacity-70">(sözlükte olmayan durum)</span>
                ) : null}
              </p>
              {h.redNedenleri.length > 0 ? (
                <ul className="flex list-disc flex-col gap-1 pl-4 text-xs leading-relaxed">
                  {h.redNedenleri.map((r, i) => (
                    <li key={`${r}-${i}`}>{r}</li>
                  ))}
                </ul>
              ) : null}
              {h.not === null ? null : <p className="text-xs italic leading-relaxed">{h.not}</p>}
              <p className="text-xs leading-relaxed">
                {h.gerceklesenDelta === null ? (
                  // SESSİZ SIFIR YOK: sonucu yazılmamış bir tahmini "0 fark" diye
                  // göstermek, ölçülmemiş bir şeyi ölçülmüş saymak olurdu.
                  <span className="opacity-80">
                    gerçekleşen Δ ölçülmedi — bu satıra sonuç hiç yazılmamış (öneri canlıya
                    çıkmadığı için sonucu da yok)
                  </span>
                ) : (
                  <>
                    gerçekleşen Δ <strong className="tabular-nums">{bicimSayi(h.gerceklesenDelta, 4, true)}</strong>
                    {h.kalibrasyonIsabet === null
                      ? " · kalibrasyon isabeti kaydedilmemiş"
                      : h.kalibrasyonIsabet
                        ? " · tahmin tuttu"
                        : " · tahmin tutmadı"}
                  </>
                )}
              </p>
            </BubbleContent>
          </Bubble>
        </BubbleGroup>
      </MessageContent>
    </Message>
  );
}

function Cip({ etiket, deger }: { etiket: string; deger: string | null }) {
  return (
    <li>
      <Badge
        variant="ghost"
        className="text-[10px]"
        title={deger === null ? `${etiket} alanı kaydedilmemiş` : undefined}
      >
        {etiket}: {deger ?? "kaydedilmemiş"}
      </Badge>
    </li>
  );
}

/* ---- KİLİTLİ YAZMA ŞERİDİ ------------------------------------------------ */

/** ÖLÇÜM (2026-08-25, `meridian/api.py` — 78 rotanın tamamı tarandı): panodan ajana
 *  SERBEST METİN gönderen bir uç YOK. `POST /api/hermes/reflect` bir yansıma turu
 *  TETİKLER ama gövde almaz; `POST /api/hermes/{action}` yalnız
 *  `start|stop|backfill|sync_integrations` tanır; `/api/skills/revision`,
 *  `/api/approvals/{id}` ve `/api/plan/{id}/onayla` karar uçlarıdır, mesaj değil.
 *
 *  GÜNCELLEME (2026-08-31, dalga-A): ARTIK BİR AJAN UCU VAR — `GET /api/ajanlar`.
 *  Ama o uç SALT OKUNUR: botların ve ana beynin konuşma defterlerini okur, hiçbir
 *  şey YAZMAZ. Yani gerekçenin YÖNÜ değişti, hükmü değişmedi: okuma yolu açıldı,
 *  YAZMA yolu hâlâ yok. Kutuyu bugün açmak, var olmayan bir yazma yolunu var
 *  göstermek olurdu — üstelik artık daha inandırıcı bir yalan olurdu, çünkü
 *  üstündeki akış gerçek konuşmaları gösteriyor.
 *
 *  İKİ MUHATAP, İKİ AYRI GEREKÇE (maket sözleşmesi): botta "yazan uç yok",
 *  kanalda "öneriler panodan yazılmaz". Tek metne indirgemek iki ayrı olguyu tek
 *  olgu gibi gösterirdi: birincisi eksik bir YOL, ikincisi bilinçli bir TASARIM.
 *
 *  ŞERİT MAKETTE İNCE: gerekçenin uzun hâli katlanır — ekranda DURUYOR ama
 *  konuşmanın yerini almıyor. Gerekçeyi tamamen kısaltmak, tarihini ve açılma
 *  şartını (dalga-B) ekrandan silmek olurdu; operatör şerh okumaz. */
const YAZMA_GEREKCESI: Readonly<Record<"ajan" | "kanal", string>> = {
  ajan: "Panodan ajana yazan uç yok — kutu bilerek kapalı",
  kanal: "Öneriler panodan yazılmaz — üreteç yansıma turlarında konuşur, kapı ölçümle cevap verir",
};

export function YazmaSeridi({ hal }: { hal: "ajan" | "kanal" }) {
  return (
    <div className="flex shrink-0 flex-col gap-1.5 border-t bg-card px-4 py-2.5 sm:px-6">
      <InputGroup className="border-dashed opacity-70">
        <InputGroupTextarea
          disabled
          aria-disabled
          placeholder={YAZMA_GEREKCESI[hal]}
          className="min-h-9 px-3 py-2 text-xs"
        />
        <InputGroupAddon align="block-end">
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <LockKeyhole className="size-3" aria-hidden />
            gönderme ucu yok
          </span>
          <InputGroupButton type="button" variant="default" size="icon-sm" disabled className="ml-auto">
            <Send />
            <span className="sr-only">Gönder (devre dışı)</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
      <details className="text-[11px] text-muted-foreground">
        <summary className="cursor-pointer text-primary">kutu neden kapalı?</summary>
        <p className="mt-1 leading-relaxed">
          `meridian/api.py` içinde serbest metin kabul eden bir ajan ucu yok. En yakın olanlar mesaj
          değil KUMANDA: `POST /api/hermes/reflect` gövdesiz bir yansıma turu başlatır,
          `POST /api/hermes/{"{action}"}` yalnız `start` · `stop` · `backfill` ·
          `sync_integrations` tanır.
        </p>
        <p className="mt-1 leading-relaxed">
          2026-08-31'de OKUMA yolu açıldı: `GET /api/ajanlar` botların ve ana beynin gerçek
          oturumlarını getiriyor (soldaki ajan satırları). O uç SALT OKUNUR — yazma yolu HÂLÂ yok.
          Bu kutu dalga-B'de, hermes köprüsü ve duruş çivileriyle birlikte açılacak; köprüsüz
          açmak, artık daha inandırıcı olan aynı yalanı söylemek olurdu.
        </p>
      </details>
    </div>
  );
}
