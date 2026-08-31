"use client";

/* ============================================================================
   FİLO — üç bot + ana hermes beyni, GERÇEK defterlerinden (2026-08-31)
   ----------------------------------------------------------------------------
   BU BÖLÜM `Sohbet` SEKMESİNİN CEVAP VEREMEDİĞİ SORUYU CEVAPLAR. Yandaki sekme
   hipotez defterini (`state/hypotheses.jsonl`) sohbet grameriyle okutuyor: orada
   konuşan taraf öneri üretecidir. Burada konuşan taraf AJANLARIN KENDİSİdir —
   `~/.hermes/profiles/<ad>/state.db` ve `~/.hermes/state.db` defterleri, yani
   @sef · @bekci · @karne botlarının ve ana beynin gerçek oturumları.

   ÜÇ HÜKÜM ÜÇ AYRI YERDE DURUR ve bu yüzey onları KARIŞTIRMAZ (ucun sözleşmesi):
     · `ok`/`hata`      — LİSTE hakkında: roster ve olay defteri okunabildi mi.
     · ajan `durum`     — YALNIZ o ajanın OTURUM kaynağı hakkında.
     · `teslimler`      — AYRI bir kaynak (`state/events.jsonl`); oturumları
                          ölçülemeyen bir ajanın teslimleri ölçülmüş OLABİLİR ve
                          bu yüzey onu o hâlde de çizer.

   `durum: olculemedi` BİR BOŞ DURUM DEĞİLDİR. Boş bir kart "bu ajanla iletişim
   yok" diye okunur — bir İDDİA. Ölçülemeyen ajan bu yüzden nedeniyle birlikte,
   uyarı kabında çizilir; boş-durum grafiğiyle DEĞİL.

   ULTRA GEÇİŞİ GÖRÜNÜR: her oturum satırı kendi model rozetini taşır ve model
   bir önceki (ESKİ) oturumdan farklıysa satır bunu ayrıca söyler. Karşılaştırma
   dizinin BİR SONRAKİ öğesiyle yapılır çünkü uç `oturumlar`ı YENİDEN→ESKİYE
   gönderiyor ve bu yüzey o sırayı DEĞİŞTİRMİYOR (plan sözleşmesi) — tersleme
   yalnız bu tek karşılaştırmanın içinde, beyanla yapılıyor.

   SOHBET HÂLÂ TEK YÖNLÜ: bu uç SALT OKUNUR. Yazma/gönderme dalga-B'nin işi.
   ============================================================================ */
import { useState } from "react";

import { Bot, Cpu, Database, Inbox, Radio, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import type { Durum } from "../../veri";
import { Kapi, Olculemedi, OlculemediBlok, bicimSayi, zamanMetni } from "./ortak";
import {
  ajanListesiNedeni,
  aktifAnahtar,
  filoOku,
  mesajSayisi,
  modeller,
  type FiloAjani,
  type FiloOturumu,
  type FiloTeslimi,
  type FiloYuku,
} from "./filoOku";

/* ---- GİRİŞ --------------------------------------------------------------- */

export function Filo({ durum }: { durum: Durum<Record<string, unknown>> }) {
  return (
    <Kapi durum={durum} ad="`/api/ajanlar`" yukseklik="h-96">
      {(govde) => <FiloGovdesi yuk={filoOku(govde)} />}
    </Kapi>
  );
}

function FiloGovdesi({ yuk }: { yuk: FiloYuku }) {
  const ajanlar = yuk.ajanlar;
  const [secili, setSecili] = useState<string | null>(null);

  // BU DAL DA TAM KABUKLA ÇİZİLİR (inceleme B2): eskiden `HukumSeridi`den ve `KaynakKarti`dan
  // ÖNCE dönülüyordu, yani ucun kendi `hata`sı ve OKUDUĞU YOLLAR ekrana hiç ulaşmıyordu —
  // "hangi defter okunamadı" sorusunun cevabı tam da bu dalda en çok gerekli.
  if (ajanlar === null) {
    return (
      <div className="flex flex-col gap-4">
        <HukumSeridi yuk={yuk} />
        <OlculemediBlok
          baslik="Ajan listesi ölçülemedi"
          neden={ajanListesiNedeni(yuk)}
          teknik="filoOku.ts::filoOku"
        />
        <KaynakKarti yuk={yuk} />
      </div>
    );
  }

  // BAYAT SEÇİM SESSİZ BOŞ PANEL ÜRETMEZ — gerekçe ve davranış `filoOku.ts::aktifAnahtar`ta,
  // çivisi `node` ile GERÇEKTEN koşuluyor (roster-değişimi senaryosu).
  const aktif = aktifAnahtar(ajanlar, secili) ?? "";

  return (
    <div className="flex flex-col gap-4">
      <HukumSeridi yuk={yuk} />
      <KaynakKarti yuk={yuk} />

      {ajanlar.length === 0 ? (
        <OlculemediBlok
          baslik="Roster boş döndü"
          neden="Uç hiçbir ajan kaydı göndermedi. Bu ÖLÇÜLMÜŞ bir boşluktur (liste okundu, içi boş) — `kaynak.botlar` ve `suzgec` alanları hangisi olduğunu söyler."
          teknik="`ajanlar: []`"
        />
      ) : (
        <Tabs value={aktif} onValueChange={setSecili} className="gap-4">
          <TabsList variant="line" className="flex-wrap">
            {ajanlar.map((a) => (
              <TabsTrigger key={a.anahtar} value={a.anahtar}>
                {a.tur === "ana" ? <Cpu className="size-3.5" aria-hidden /> : <Bot className="size-3.5" aria-hidden />}
                {a.ad ?? "(adsız kayıt)"}
                {a.durum === "olculemedi" ? (
                  <Badge variant="destructive" className="ml-1 text-[10px]">
                    ölçülemedi
                  </Badge>
                ) : null}
              </TabsTrigger>
            ))}
          </TabsList>

          {ajanlar.map((a) => (
            <TabsContent key={a.anahtar} value={a.anahtar}>
              <AjanKarti a={a} />
            </TabsContent>
          ))}
        </Tabs>
      )}

      <EslesmeyenKarti yuk={yuk} />
    </div>
  );
}

/* ---- HÜKÜM ŞERİDİ: LİSTE HAKKINDA ---------------------------------------- */

function HukumSeridi({ yuk }: { yuk: FiloYuku }) {
  // `ok === false` LİSTE hakkındadır, tek bir ajan hakkında değil — ucun kendi
  // ayrımı. Bunu ajan kartlarının içine karıştırmak, bir profilin okunamamasını
  // "tüm filo okunamadı" diye gösterirdi.
  if (yuk.ok === true) return null;
  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-500/40 border-dashed bg-amber-500/5 p-3">
      <TriangleAlert className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
      <div className="min-w-0">
        <p className="font-medium text-sm">
          {yuk.ok === null ? "Liste hükmü ölçülemedi" : "Filo listesi eksik ölçüldü"}
        </p>
        <p className="mt-0.5 break-words text-muted-foreground text-xs leading-relaxed">
          {yuk.hata ??
            "Uç `ok: false` dedi ama `hata` alanı boş geldi — hangi kaynağın düştüğü söylenmemiş."}
        </p>
      </div>
    </div>
  );
}

/* ---- KAYNAK KARTI: HANGİ DOSYALAR OKUNDU --------------------------------- */

function KaynakKarti({ yuk }: { yuk: FiloYuku }) {
  const k = yuk.kaynak;
  const s = yuk.suzgec;
  if (k === null) {
    return (
      <OlculemediBlok
        baslik="Kaynak bloğu yok"
        neden="Uç hangi defterleri okuduğunu söylemedi — gövdede `kaynak` alanı bir nesne değil."
      />
    );
  }
  const kirpildi = s !== null && s.limit !== null && s.limitIstenen !== null && s.limitIstenen > s.limit;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 leading-none">
          <Database className="size-4" aria-hidden />
          Hangi defterler okundu?
        </CardTitle>
        <CardDescription>
          Üç kaynak, üç ayrı hüküm: bot roster'ı (dizin) · oturum defterleri (sqlite, SALT OKUNUR) ·
          teslim olayları (`events.jsonl`). Biri düşerse ötekiler ölçülmeye devam eder.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 text-xs">
        <Satir etiket="roster kökü" deger={k.botKoku} neden="`kaynak.bot_koku` yazılmamış" />
        <Satir etiket="profil kökü" deger={k.profilKoku} neden="`kaynak.profil_koku` yazılmamış" />
        <Satir etiket="ana beyin" deger={k.anaBeyin} neden="`kaynak.ana_beyin` yazılmamış" />
        <Satir etiket="olay defteri" deger={k.events} neden="`kaynak.events` yazılmamış" />
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <span className="w-28 shrink-0 text-muted-foreground">roster</span>
          {k.botlar === null ? (
            <Olculemedi
              neden="bot listesi ölçülemedi"
              teknik="`kaynak.botlar: null` — boş liste 'bot yok' derdi; ölçülen şey 'listeyi okuyamadım'"
            />
          ) : (
            <span className="flex flex-wrap gap-1">
              {k.botlar.length === 0 ? (
                <span className="text-muted-foreground italic">dizin okundu, içinde profil yok</span>
              ) : (
                k.botlar.map((b) => (
                  <Badge key={b} variant="outline" className="text-[10px]">
                    {b}
                  </Badge>
                ))
              )}
            </span>
          )}
        </div>
        {k.eventsNeden === null ? null : (
          <p className="rounded-md border border-dashed bg-muted/30 px-2 py-1.5 text-muted-foreground leading-relaxed">
            Teslim olayları ölçülemedi: {k.eventsNeden}
          </p>
        )}
        <Separator className="my-1" />
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
          <span>
            oturum penceresi:{" "}
            {s === null || s.limit === null ? (
              <Olculemedi neden="`suzgec.limit` yok" />
            ) : (
              <strong className="tabular-nums">{bicimSayi(s.limit)}</strong>
            )}
            {kirpildi && s !== null && s.limitIstenen !== null ? (
              <span className="ml-1 text-amber-700 dark:text-amber-400">
                (istenen {bicimSayi(s.limitIstenen)} TAVANDA kırpıldı)
              </span>
            ) : null}
          </span>
          <span>
            teslim tavanı:{" "}
            {k.teslimTavani === null ? (
              <Olculemedi neden="`kaynak.teslim_tavani` yok" />
            ) : (
              <strong className="tabular-nums">{bicimSayi(k.teslimTavani)}</strong>
            )}
          </span>
          <span>
            eşleşmeyen teslim:{" "}
            {k.eslesmeyenToplam === null ? (
              <Olculemedi
                neden="ölçülemedi"
                teknik="roster ya da olay defteri okunamadan kimin sahipsiz olduğu söylenemez"
              />
            ) : (
              <strong className="tabular-nums">{bicimSayi(k.eslesmeyenToplam)}</strong>
            )}
          </span>
          <span>
            süzgeç:{" "}
            {s === null || s.ajan === null ? (
              <span>yok (tüm filo)</span>
            ) : (
              <Badge variant="secondary" className="text-[10px]">
                ajan={s.ajan}
              </Badge>
            )}
            {s === null || s.eslesenN === null || s.toplamN === null ? null : (
              <span className="ml-1 tabular-nums">
                · {bicimSayi(s.eslesenN)} / {bicimSayi(s.toplamN)} kayıt
              </span>
            )}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function Satir({ etiket, deger, neden }: { etiket: string; deger: string | null; neden: string }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-2">
      <span className="w-28 shrink-0 text-muted-foreground">{etiket}</span>
      {deger === null ? (
        <Olculemedi neden={neden} />
      ) : (
        <code className="min-w-0 break-all font-mono text-[11px]">{deger}</code>
      )}
    </div>
  );
}

/* ---- AJAN KARTI ---------------------------------------------------------- */

function AjanKarti({ a }: { a: FiloAjani }) {
  const mesajN = mesajSayisi(a);
  const modelListesi = modeller(a);
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2 leading-none">
            {a.ad ?? "(adsız kayıt)"}
            <Badge variant={a.tur === "ana" ? "default" : "secondary"} className="text-[10px]">
              {a.tur ?? "tür yazılmamış"}
            </Badge>
            {a.model === null ? (
              <Olculemedi
                neden="model rozeti yok"
                teknik="`model: null` — en yeni oturumun modeli kayıtlı değil ya da hiç oturum yok; `durum` ayırt eder"
              />
            ) : (
              <Badge variant="outline" className="font-mono text-[10px]">
                {a.model}
              </Badge>
            )}
          </CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span>
              son oturum:{" "}
              {a.sonOturumTs === null ? (
                <Olculemedi
                  neden="hiç oturum görülmedi"
                  teknik="`son_oturum_ts: null` — ya defterde oturum yok ya damgası çevrilemedi (oturum satırındaki HAM değere bak)"
                />
              ) : (
                (zamanMetni(a.sonOturumTs) ?? a.sonOturumTs)
              )}
            </span>
            <span>
              mesaj:{" "}
              {mesajN === null ? (
                <Olculemedi neden="sayılamadı" teknik="oturum listesi ölçülemedi — 0 yazmak 'hiç mesajlaşılmadı' iddiası olurdu" />
              ) : (
                <strong className="tabular-nums">{bicimSayi(mesajN)}</strong>
              )}
            </span>
            {modelListesi !== null && modelListesi.length > 1 ? (
              <span className="text-amber-700 dark:text-amber-400">
                bu pencerede {bicimSayi(modelListesi.length)} FARKLI model: {modelListesi.join(" · ")}
              </span>
            ) : null}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <OturumBolumu a={a} />
        </CardContent>
      </Card>

      <TeslimKarti a={a} />
    </div>
  );
}

/* ---- OTURUM ZAMAN ÇİZELGESİ ---------------------------------------------- */

function OturumBolumu({ a }: { a: FiloAjani }) {
  const oturumlar = a.oturumlar;

  // ÖLÇÜLEMEYEN AJAN BOŞ-DURUM GİBİ ÇİZİLMEZ. Boş bir kart "bu ajanla konuşulmamış"
  // diye okunur; ölçülen şey ise "defteri okuyamadım"dır ve nedeni ekranda DURUR.
  if (oturumlar === null) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-destructive/40 border-dashed bg-destructive/5 p-4">
        <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden />
        <div className="min-w-0">
          <p className="font-medium text-sm">Oturum defteri ölçülemedi — bu "iletişim yok" DEĞİLDİR</p>
          <p className="mt-0.5 break-words text-muted-foreground text-xs leading-relaxed">
            {a.neden ?? "Uç `oturumlar: null` döndürdü ama `neden` yazmadı — hangi defterin okunamadığı söylenmemiş."}
          </p>
          <p className="mt-1 text-muted-foreground text-[11px]">
            durum: <code className="font-mono">{a.durum ?? "yazılmamış"}</code>
          </p>
        </div>
      </div>
    );
  }

  if (oturumlar.length === 0) {
    return (
      <div className="rounded-lg border border-dashed bg-muted/30 p-4 text-muted-foreground text-xs leading-relaxed">
        Defter OKUNDU ve içinde oturum yok. Bu ölçülmüş bir boşluktur — yukarıdaki "ölçülemedi"
        kutusundan farklıdır: profil koştu, konuşma kaydı üretmedi (ya da defteri yeni açılmış).
      </div>
    );
  }

  return (
    <Accordion type="multiple" className="rounded-lg border">
      {oturumlar.map((o, i) => (
        <AccordionItem key={o.id ?? `oturum-${i}`} value={o.id ?? `oturum-${i}`} className="px-3">
          <AccordionTrigger className="gap-2 py-3 text-left hover:no-underline">
            <OturumBasligi o={o} onceki={oturumlar[i + 1] ?? null} />
          </AccordionTrigger>
          <AccordionContent className="pb-3">
            <MesajAkisi o={o} />
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}

/** `onceki` = dizide BİR SONRAKİ öğe. Uç `oturumlar`ı YENİDEN→ESKİYE gönderiyor,
 *  yani indeksçe sonraki olan zamanca ÖNCEKİdir. Sıra DEĞİŞTİRİLMİYOR; tersleme
 *  yalnız bu karşılaştırmanın içinde ve BEYANLA yapılıyor (plan sözleşmesi). */
function OturumBasligi({ o, onceki }: { o: FiloOturumu; onceki: FiloOturumu | null }) {
  const gecis = onceki !== null && onceki.model !== null && o.model !== null && onceki.model !== o.model;
  const n = o.mesajlar === null ? null : o.mesajlar.length;
  return (
    <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-2 gap-y-1">
      <Damga ts={o.ts} tsHam={o.tsHam} neden="oturum damgası yok" />
      {o.model === null ? (
        <Olculemedi neden="model yazılmamış" teknik="`oturum.model: null`" />
      ) : (
        <Badge variant="outline" className="font-mono text-[10px]">
          {o.model}
        </Badge>
      )}
      {gecis && onceki !== null ? (
        <Badge variant="destructive" className="text-[10px]">
          model değişti: {onceki.model} → {o.model}
        </Badge>
      ) : null}
      <span className="text-muted-foreground text-xs tabular-nums">
        {n === null ? "mesaj listesi ölçülemedi" : `${bicimSayi(n)} mesaj`}
      </span>
      {o.id === null ? null : (
        <code className="ml-auto truncate font-mono text-[10px] text-muted-foreground/70">{o.id}</code>
      )}
    </div>
  );
}

/** Damga ÇEVRİLEMEDİYSE HAM DEĞER GÖSTERİLİR — "geçersiz tarih" ya da boşluk
 *  yerine defterde NE YAZDIĞI. Ham'ı gizlemek ölçülemezliği iki kat yapardı:
 *  operatör hem damgayı göremez hem defterdeki değeri öğrenemezdi. */
function Damga({ ts, tsHam, neden }: { ts: string | null; tsHam: string | null; neden: string }) {
  if (ts !== null) {
    return <span className="font-medium text-sm">{zamanMetni(ts) ?? ts}</span>;
  }
  if (tsHam !== null) {
    return (
      <span
        className="font-mono text-amber-700 text-xs dark:text-amber-400"
        title="damga ISO-8601'e çevrilemedi — bu, defterde YAZAN ham değerdir (`ts_ham`)"
      >
        ham damga: {tsHam}
      </span>
    );
  }
  return <Olculemedi neden={neden} teknik="`ts` ve `ts_ham` ikisi de null — defterde damga alanı boş" />;
}

const ROL_ETIKET: Readonly<Record<string, string>> = {
  user: "operatör / tetik",
  assistant: "ajan",
  system: "sistem yönergesi",
  tool: "araç",
};

function MesajAkisi({ o }: { o: FiloOturumu }) {
  const mesajlar = o.mesajlar;
  if (mesajlar === null) {
    return (
      <Olculemedi
        neden="Mesaj listesi ölçülemedi"
        teknik="`oturum.mesajlar` bir dizi değil — boş liste 'bu oturumda hiç mesaj yok' derdi"
      />
    );
  }
  if (mesajlar.length === 0) {
    return (
      <p className="text-muted-foreground text-xs leading-relaxed">
        Oturum kaydı var, mesaj satırı YOK. Ölçülmüş boşluk — oturum açılmış ama konuşma yazılmamış.
      </p>
    );
  }
  return (
    // SIRA ESKİDEN→YENİYE gelir (ucun sözleşmesi, okuma akışı) ve burada
    // DEĞİŞTİRİLMEZ. Yeniden sıralayan bir yüzey, tek satırlık bir `sort` ile
    // konuşmayı tersten okuturdu ve hiçbir şey kırmızıya dönmezdi.
    <ul className="flex flex-col gap-2">
      {mesajlar.map((m, i) => (
        <li
          key={`${o.id ?? "oturum"}-${i}`}
          className="rounded-md border bg-muted/20 px-3 py-2"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={m.rol === "assistant" ? "secondary" : "ghost"} className="text-[10px]">
              {m.rol === null ? "rol yazılmamış" : (ROL_ETIKET[m.rol] ?? m.rol)}
            </Badge>
            <span className="text-muted-foreground text-[11px]">
              <Damga ts={m.ts} tsHam={m.tsHam} neden="mesaj damgası yok" />
            </span>
          </div>
          {m.metin === null ? (
            <p className="mt-1">
              <Olculemedi neden="gövde okunamadı" teknik="`mesaj.metin` bir dizge değil" />
            </p>
          ) : m.metin === "" ? (
            <p className="mt-1 text-muted-foreground text-xs italic">
              gövde ÖLÇÜLDÜ ve boş — defterde içeriksiz bir satır
            </p>
          ) : (
            <p className="mt-1 whitespace-pre-wrap break-words text-sm leading-relaxed">{m.metin}</p>
          )}
          {m.kirpildi === true ? (
            <p className="mt-1 text-amber-700 text-[11px] dark:text-amber-400">
              … devamı var — bu gövde uçta KIRPILDI
              {m.hamUzunluk === null ? " (ham uzunluk yazılmamış)" : `; tam metin ${bicimSayi(m.hamUzunluk)} karakter`}
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

/* ---- TESLİM DAMGALARI ---------------------------------------------------- */

function TeslimKarti({ a }: { a: FiloAjani }) {
  const teslimler = a.teslimler;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 leading-none">
          <Radio className="size-4" aria-hidden />
          Teslim damgaları
        </CardTitle>
        <CardDescription>
          `state/events.jsonl` içindeki `{a.ad ?? "<ad>"}_brifingi_teslim` olayları — oturum
          defterinden AYRI bir kaynak. En yeniden eskiye.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {teslimler === null ? (
          <OlculemediBlok
            baslik="Teslim defteri ölçülemedi"
            neden="Olay defteri okunamadı — boş liste 'hiç brifing teslim edilmedi' derdi ve bu AYRI bir iddiadır. Nedeni kaynak kartında yazılı."
            teknik="`teslimler: null`"
          />
        ) : teslimler.length === 0 ? (
          <p className="rounded-lg border border-dashed bg-muted/30 p-3 text-muted-foreground text-xs leading-relaxed">
            Olay defteri OKUNDU ve bu ajana ait teslim olayı yok. Ölçülmüş boşluk — defterin taranan
            kuyruğunda bu ajanın damgası geçmiyor.
          </p>
        ) : (
          <>
            {a.teslimKirpildi === true ? (
              <p className="rounded-md border border-amber-500/40 bg-amber-500/5 px-2 py-1.5 text-amber-700 text-xs leading-relaxed dark:text-amber-400">
                KESİLDİ: aşağıdaki son {bicimSayi(teslimler.length)} olay gösteriliyor
                {a.teslimToplam === null
                  ? " — toplam sayı yazılmamış"
                  : `, taranan pencerede toplam ${bicimSayi(a.teslimToplam)} olay var`}
                .
              </p>
            ) : null}
            <ul className="flex flex-col gap-2">
              {teslimler.map((t, i) => (
                <TeslimSatiri key={`${t.olay ?? "olay"}-${t.ts ?? i}`} t={t} />
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function TeslimSatiri({ t }: { t: FiloTeslimi }) {
  return (
    <li className="rounded-md border bg-muted/20 px-3 py-2 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium">
          {t.ts === null ? (
            <Olculemedi neden="damga yok" teknik="olayda `ts` alanı yok" />
          ) : (
            (zamanMetni(t.ts) ?? t.ts)
          )}
        </span>
        <Badge variant="outline" className="font-mono text-[10px]">
          {t.olay ?? "olay adı yazılmamış"}
        </Badge>
      </div>
      {t.detay === null ? null : <p className="mt-1 break-words leading-relaxed">{t.detay}</p>}
      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="text-muted-foreground">damgalanan:</span>
        {t.damgalanan === null ? (
          <Olculemedi neden="üretici bu alanı basmadı" teknik="olayda `damgalanan` alanı YOK — boş liste 'hiçbir şey damgalanmadı' derdi" />
        ) : t.damgalanan.length === 0 ? (
          <span className="text-muted-foreground italic">alan var, liste boş</span>
        ) : (
          t.damgalanan.map((d, i) => (
            <Badge key={`${d}-${i}`} variant="ghost" className="text-[10px]">
              {d}
            </Badge>
          ))
        )}
      </div>
      {/* ÖLÇÜLEMEYENLER DÜŞÜRÜLMEZ, ROZETLENİR: üreticinin "şu kaynakları
          ölçemedim" beyanı tam da bu yüzeyin konusudur — onu gizlemek,
          ölçülemezliği göstermek için yazılmış bir alanı kaybetmek olurdu. */}
      {t.olculemeyen === null ? null : t.olculemeyen.length === 0 ? (
        <p className="mt-1 text-muted-foreground">ölçülemeyen kaynak: yok (üretici hepsini ölçmüş)</p>
      ) : (
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="text-amber-700 dark:text-amber-400">ölçülemeyen kaynak:</span>
          {t.olculemeyen.map((o, i) => (
            <Badge key={`${o}-${i}`} variant="destructive" className="text-[10px]">
              {o}
            </Badge>
          ))}
        </div>
      )}
    </li>
  );
}

/* ---- EŞLEŞMEYEN TESLİMLER ------------------------------------------------ */

/** Hiçbir profile karşılık gelmeyen teslim olayı (`oneri_brifingi_teslim` gibi).
 *  Sessizce düşürmek, panonun "tüm ajan iletişimi burada" iddiasını yalan yapardı. */
function EslesmeyenKarti({ yuk }: { yuk: FiloYuku }) {
  const liste = yuk.eslesmeyenTeslimler;
  const toplam = yuk.kaynak?.eslesmeyenToplam ?? null;
  if (liste !== null && liste.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 leading-none">
          <Inbox className="size-4" aria-hidden />
          Sahipsiz teslimler
        </CardTitle>
        <CardDescription>
          `*_brifingi_teslim` sonekini taşıyan ama roster'daki hiçbir ajana denk düşmeyen olaylar.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {liste === null ? (
          <OlculemediBlok
            baslik="Sahipsiz teslimler ölçülemedi"
            neden="Roster ya da olay defteri okunamadı; kimin sahipsiz olduğu ancak TAM liste bilinirken söylenebilir."
            teknik="`eslesmeyen_teslimler: null`"
          />
        ) : (
          <>
            {toplam !== null && toplam > liste.length ? (
              <p className="mb-2 text-amber-700 text-xs dark:text-amber-400">
                KESİLDİ: son {bicimSayi(liste.length)} olay gösteriliyor, toplam {bicimSayi(toplam)}.
              </p>
            ) : null}
            <ul className="flex flex-col gap-2">
              {liste.map((t, i) => (
                <TeslimSatiri key={`${t.olay ?? "olay"}-${t.ts ?? i}`} t={t} />
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}
