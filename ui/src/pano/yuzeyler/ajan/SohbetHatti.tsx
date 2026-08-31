"use client";

/* ============================================================================
   SOHBET HATTI — hipotez defteri, konuşma grameriyle
   ----------------------------------------------------------------------------
   BURADA UYDURULAN BİR MESAJ YOK. Her balon `state/hypotheses.jsonl`in BİR
   satırından geliyor ve iki tarafı var:
     · SOL  (ajan)  — `rationale` alanı. Bu gerçekten ajanın kendi cümlesidir:
                      hermes bir öneri üretirken gerekçesini bu alana yazıyor
                      (ölçüldü: 41/41 satırda dolu, ortalama birkaç yüz karakter).
     · SAĞ  (kapı)  — `status` + `reject_reasons` + varsa `realized_delta`. Yani
                      cevap veren OPERATÖR DEĞİL, backtest/bekçi kapısıdır ve
                      balonun başlığı bunu açıkça yazar. "Sen" diye bir taraf
                      çizmek, hiç kurulmamış bir diyaloğu var göstermek olurdu.

   KRONOLOJİK VE ESKİDEN YENİYE: sohbet grameri budur ve `autoScroll` en yeniye
   iner. Defterin kendi sırası da bu (JSONL ekleme sırası) — yeniden sıralamıyoruz,
   yalnız `ts` yazılmamış satırları sona alıyoruz ki tarih ayracı yalan söylemesin.

   GÜN AYRACI ÖLÇÜLEN DAMGADAN: `ts` yoksa ayraç "tarihsiz" der. Bugünün tarihini
   varsaymak, damgasız bir satırı bugün konuşulmuş gibi gösterirdi.
   ============================================================================ */
import { useMemo, useState } from "react";

import { Ban, Bot, MessageSquareOff, ScrollText, Search, Send, ShieldCheck } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bubble, BubbleContent, BubbleGroup } from "@/components/ui/bubble";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea } from "@/components/ui/input-group";
import { Input } from "@/components/ui/input";
import { Marker, MarkerContent } from "@/components/ui/marker";
import { Message, MessageAvatar, MessageContent, MessageFooter, MessageHeader } from "@/components/ui/message";
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller";
import { Separator } from "@/components/ui/separator";
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

/* ---- HAT ----------------------------------------------------------------- */

export function SohbetHatti({
  hipotezler,
  hafizaBasliklari,
  hafizaOlculemediNedeni,
}: {
  hipotezler: readonly Hipotez[];
  /** `lessons.md` başlıkları — ajanın HER yansımaya enjekte edilen kalıcı hafızası. */
  hafizaBasliklari: readonly { readonly baslik: string; readonly n: number }[];
  hafizaOlculemediNedeni: string | null;
}) {
  const [arama, setArama] = useState("");
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
    <div className="flex min-h-0 flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-56 flex-1">
          <Search className="-translate-y-1/2 absolute top-1/2 left-2.5 size-3.5 text-muted-foreground" aria-hidden />
          <Input
            value={arama}
            onChange={(e) => setArama(e.target.value)}
            placeholder="Gerekçede, değişkende, ret nedeninde ara…"
            className="h-9 pl-8 text-sm"
            aria-label="Sohbette ara"
          />
        </div>
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
          aria-label="Sohbet süzgeci"
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

      <div className="min-h-0 rounded-lg border">
        <MessageScrollerProvider autoScroll>
          <MessageScroller className="h-[34rem]">
            <MessageScrollerViewport>
              <MessageScrollerContent className="gap-6 px-3 py-6 sm:px-4">
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
                      <div key={h.id ?? `satir-${i}`} className="flex flex-col gap-6">
                        {buGun !== oncekiGun ? (
                          <Marker variant="separator">
                            <MarkerContent>{buGun ?? "tarihsiz (ts alanı yok)"}</MarkerContent>
                          </Marker>
                        ) : null}
                        <MessageScrollerItem
                          messageId={h.id ?? `satir-${i}`}
                          scrollAnchor={i === gorunen.length - 1}
                        >
                          <div className="flex flex-col gap-4">
                            <AjanBalonu h={h} />
                            <KapiBalonu h={h} />
                          </div>
                        </MessageScrollerItem>
                      </div>
                    );
                  })
                )}
              </MessageScrollerContent>
            </MessageScrollerViewport>
            <MessageScrollerButton />
          </MessageScroller>
        </MessageScrollerProvider>

        <Separator />
        <Yazamaz />
      </div>
    </div>
  );
}

/* ---- BALONLAR ------------------------------------------------------------ */

function HafizaMesaji({
  basliklar,
  neden,
}: {
  basliklar: readonly { readonly baslik: string; readonly n: number }[];
  neden: string | null;
  teknik?: string;
}) {
  return (
    <Message align="start">
      <MessageAvatar>
        <Avatar>
          <AvatarFallback className="bg-muted text-foreground">
            <ScrollText className="size-4" aria-hidden />
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>
      <MessageContent>
        <MessageHeader>kalıcı hafıza · state/lessons.md</MessageHeader>
        <BubbleGroup>
          <Bubble variant="outline" align="start">
            <BubbleContent className="flex flex-col gap-2">
              <p className="text-sm leading-relaxed">
                Bu metin ajanın HER yansımasına enjekte ediliyor (uç şerhi: "Injected into every
                reflection"). Yani aşağıdaki her öneri, bu hafızayı okumuş bir ajandan geliyor.
              </p>
              {neden !== null ? (
                <p className="text-muted-foreground text-xs leading-relaxed">
                  Başlıklar ölçülemedi: {neden}
                </p>
              ) : basliklar.length === 0 ? (
                <p className="text-muted-foreground text-xs leading-relaxed">
                  Metinde `##` başlığı yok — dosya var ama bölümlenmemiş.
                </p>
              ) : (
                <ul className="flex flex-wrap gap-1.5">
                  {basliklar.map((b) => (
                    <li key={b.baslik}>
                      <Badge variant="outline" className="text-[11px]">
                        {b.baslik} · {bicimSayi(b.n)} madde
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-muted-foreground text-xs">
                Tam metin: <a className="underline underline-offset-2" href="#/dashboard/file-manager/hafiza">Belgeler → Hafıza</a>
              </p>
            </BubbleContent>
          </Bubble>
        </BubbleGroup>
      </MessageContent>
    </Message>
  );
}

function bas(kaynak: string | null): string {
  if (kaynak === null) return "?";
  if (kaynak.startsWith("hermes:")) return kaynak.slice(7, 9).toLocaleUpperCase("tr-TR");
  return kaynak.slice(0, 2).toLocaleUpperCase("tr-TR");
}

function AjanBalonu({ h }: { h: Hipotez }) {
  const zaman = zamanMetni(h.ts);
  return (
    <Message align="start">
      <MessageAvatar>
        <Avatar>
          <AvatarFallback className="bg-muted text-foreground text-xs">
            {h.kaynak?.startsWith("hermes:") ? bas(h.kaynak) : <Bot className="size-4" aria-hidden />}
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>
      <MessageContent>
        <MessageHeader className="gap-2">
          <span>{h.kaynak ?? "kaynak yazılmamış"}</span>
          {h.id === null ? null : <span className="text-muted-foreground/70">· {h.id}</span>}
          {h.asiriUyumSupheli === true ? (
            <Badge variant="destructive" className="text-[10px]">
              aşırı uyum şüphesi
            </Badge>
          ) : null}
        </MessageHeader>
        <BubbleGroup>
          <Bubble variant="muted" align="start">
            <BubbleContent className="flex flex-col gap-2">
              <p className="font-medium text-sm">
                <code className="font-mono">{h.degisken ?? "(değişken yazılmamış)"}</code>{" "}
                <span className="text-muted-foreground">
                  {h.eski ?? "?"} → {h.yeni ?? "?"}
                </span>
              </p>
              <p className="whitespace-pre-line text-sm leading-relaxed">
                {h.gerekce ?? "Bu satırda `rationale` alanı yok — ajan gerekçesini yazmamış."}
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
        <Avatar>
          <AvatarFallback className="bg-muted text-foreground">
            <ShieldCheck className="size-4" aria-hidden />
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
                {sozluk?.etiket ?? h.durum ?? "hüküm yazılmamış"}
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
                    gerçekleşen Δ ölçülmedi — bu satıra `realized_delta` hiç yazılmamış (öneri canlıya
                    çıkmadığı için sonucu da yok)
                  </span>
                ) : (
                  <>
                    gerçekleşen Δ <strong className="tabular-nums">{bicimSayi(h.gerceklesenDelta, 4, true)}</strong>
                    {h.kalibrasyonIsabet === null
                      ? " · kalibrasyon isabeti yazılmamış"
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
      <Badge variant="ghost" className="text-[10px]" title={deger === null ? `${etiket} alanı yazılmamış` : undefined}>
        {etiket}: {deger ?? "yazılmamış"}
      </Badge>
    </li>
  );
}

/* ---- GİRİŞ KUTUSU: KAPALI VE NEDENİ YAZILI ------------------------------- */

/** ÖLÇÜM (2026-08-25, `meridian/api.py` — 78 rotanın tamamı tarandı): panodan ajana
 *  SERBEST METİN gönderen bir uç YOK. `POST /api/hermes/reflect` bir yansıma turu
 *  TETİKLER ama gövde almaz; `POST /api/hermes/{action}` yalnız
 *  `start|stop|backfill|sync_integrations` tanır; `/api/skills/revision`,
 *  `/api/approvals/{id}` ve `/api/plan/{id}/onayla` karar uçlarıdır, mesaj değil.
 *
 *  GÜNCELLEME (2026-08-31, dalga-A): ARTIK BİR AJAN UCU VAR — `GET /api/ajanlar`.
 *  Ama o uç SALT OKUNUR: botların ve ana beynin oturum defterlerini okur, hiçbir
 *  şey YAZMAZ (yüzeyi bu sayfanın `Filo` sekmesi). Yani gerekçenin YÖNÜ değişti,
 *  hükmü değişmedi: okuma yolu açıldı, YAZMA yolu hâlâ yok. Kutuyu bugün açmak,
 *  var olmayan bir yazma yolunu var göstermek olurdu — üstelik artık daha inandırıcı
 *  bir yalan olurdu, çünkü yanındaki sekme gerçek konuşmaları gösteriyor.
 *
 *  DALGA-B'DE AÇILACAK ve şartı yazılıdır: hermes köprüsü (panodan profile mesaj
 *  taşıyan yazma ucu) + DURUŞ ÇİVİLERİ (kimin yazabildiği, neyin kaydedildiği,
 *  yazılan mesajın ajanın kararına ne yaptığı ölçülmeden bu kutu açılmaz).
 *
 *  Kutu bu yüzden ÇALIŞIR GÖRÜNMÜYOR. Yazılabilen ama hiçbir yere gitmeyen bir
 *  metin alanı, arayüzün söyleyebileceği en sinsi yalandır: operatör mesajı yazar,
 *  gönderir, cevap bekler — ve beklediği şey hiç var olmamıştır. */
function Yazamaz() {
  return (
    <div className="flex flex-col gap-3 p-3">
      <Alert>
        <Ban />
        <AlertTitle>Bu pano ajana mesaj gönderemez — kutu bilerek kapalı (dalga-B)</AlertTitle>
        <AlertDescription>
          <p>
            `meridian/api.py` içinde serbest metin kabul eden bir ajan ucu yok. En yakın olanlar mesaj
            değil, KUMANDA: `POST /api/hermes/reflect` gövdesiz bir yansıma turu başlatır,
            `POST /api/hermes/{"{action}"}` yalnız `start` · `stop` · `backfill` ·
            `sync_integrations` tanır. Ajanla konuşmanın bugünkü yolu tek yönlü: sen eşiği/kartı
            değiştirirsin, o bir sonraki turda cevabını bu deftere yazar.
          </p>
          <p className="mt-2">
            2026-08-31'de OKUMA yolu açıldı: `GET /api/ajanlar` botların ve ana beynin gerçek
            oturumlarını getiriyor (yandaki `Filo` sekmesi). O uç SALT OKUNUR — yazma yolu HÂLÂ
            yok. Bu kutu dalga-B'de, hermes köprüsü ve duruş çivileriyle birlikte açılacak;
            köprüsüz açmak, artık daha inandırıcı olan aynı yalanı söylemek olurdu.
          </p>
        </AlertDescription>
      </Alert>

      <InputGroup className="opacity-60">
        <InputGroupTextarea
          disabled
          aria-disabled
          placeholder="Gönderme ucu yok — bu alan dalga-B'ye kadar devre dışı (bkz. yukarıdaki gerekçe)"
          className="min-h-14 px-3 py-2.5 text-sm"
        />
        <InputGroupAddon align="block-end">
          <InputGroupButton type="button" variant="default" size="icon-sm" disabled className="ml-auto">
            <Send />
            <span className="sr-only">Gönder (devre dışı)</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    </div>
  );
}
