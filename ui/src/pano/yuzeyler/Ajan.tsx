"use client";

/* ============================================================================
   AJAN — "ajana ne sorabilirim, ne cevap verdi?"
   ----------------------------------------------------------------------------
   BU YÜZEYİN İLK CÜMLESİ BİR HAYIRDIR: sorunun ilk yarısına ("ne sorabilirim")
   bugünkü cevap YOK. `meridian/api.py`nin 78 rotası tarandı (2026-08-25) —
   panodan ajana serbest metin gönderen bir uç bulunmuyor. En yakın uçlar mesaj
   değil kumandadır (`POST /api/hermes/reflect` gövdesiz tetik;
   `POST /api/hermes/{action}` yalnız start|stop|backfill|sync_integrations).
   Bu yüzden giriş kutusu ÇİZİLİYOR ama DEVRE DIŞI ve nedeni kutunun üstünde
   yazıyor. Çalışırmış gibi duran bir metin alanı, panonun kurabileceği en sinsi
   yalandır: operatör yazar, gönderir, cevap bekler — beklediği şey hiç olmamıştır.

   SORUNUN İKİNCİ YARISI ("ne cevap verdi") GERÇEKTİR ve ölçülebilir: ajan
   cevaplarını `state/hypotheses.jsonl`e yazıyor. Her satır bir öneri (`rationale`
   alanı ajanın kendi cümlesi) ve bir hüküm (`status` + `reject_reasons`) taşıyor.
   Yüzey bu defteri sohbet grameriyle okutuyor.

   İKİ UÇ, İKİ İSTEK, TEK GERÇEK: `/api/agent` (karne + hipotezler + kalibrasyon)
   ve `/api/memory` (lessons.md + hipotezler). Hipotez dizisi İKİSİNDE DE var ve
   aynı kaynaktan geliyor (`memory.all_hypotheses()`); sohbet `/api/agent`inkini
   kullanıyor, `/api/memory`den YALNIZ `lessons_md` okunuyor. İki listeyi
   birleştirmek ya da hangisinin taze olduğunu tartmak, aynı deftere iki gerçek
   uydurmak olurdu.

   NABIZ YOK (periyot 0): bu defter gün içinde saniyede bir değişmiyor — bir
   yansıma turu dakikalar sürüyor. 15 saniyede bir çekmek, okunan bir sohbeti
   altından kaydırmak demekti. Tazeleme elde: sağ üstteki düğme.

   DÖRDÜNCÜ BÖLÜM — FİLO (2026-08-31): yukarıdaki "ne cevap verdi" cevabı hipotez
   defterinden geliyordu, yani ÖNERİ ÜRETECİNDEN. `GET /api/ajanlar` ucu bugün
   ikinci bir muhatap açtı: @sef · @bekci · @karne botlarının ve ana hermes
   beyninin KENDİ oturum defterleri (`~/.hermes` altındaki `state.db`) + Telegram teslim
   olayları. İkisi AYRI kaynaktır ve bu yüzey onları ayrı sekmede tutuyor —
   birleştirmek, iki defteri tek gerçek sanmak olurdu. Sohbet kutusu HÂLÂ KAPALI:
   yeni uç SALT OKUNUR, yazma dalga-B'nin işi (bkz. `SohbetHatti::Yazamaz`).
   ============================================================================ */
import { useEffect, useMemo } from "react";

import { Bot, MessagesSquare, RefreshCw, Table2, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { YUZEYLER } from "../alanlar";
import { useRota, useRouter } from "../rota";
import { useApi } from "../veri";
import { Filo } from "./ajan/Filo";
import { Grafikler } from "./ajan/Grafikler";
import { HipotezDefteri } from "./ajan/HipotezDefteri";
import { SohbetHatti } from "./ajan/SohbetHatti";
import { Kapi, Olculemedi, bicimSayi, dizi, hipotezOku, metin, nesne, say, type Hipotez } from "./ajan/ortak";
import { bolumOzeti, hafizaAyristir } from "./belgeler/damitim";

const BOLUMLER = ["sohbet", "defter", "olcum", "filo"] as const;
type BolumAdi = (typeof BOLUMLER)[number];

function bolumSec(b: string): BolumAdi {
  return (BOLUMLER as readonly string[]).includes(b) ? (b as BolumAdi) : "sohbet";
}

export function Ajan() {
  const y = YUZEYLER.chat;
  const { bolum } = useRota();
  const { push: git } = useRouter();
  const ajan = useApi<Record<string, unknown>>("/api/agent", 0);
  const hafiza = useApi<Record<string, unknown>>("/api/memory", 0);
  // BEDEL BEYANI: bu uç sekme açık olmasa da yüzey açılışında BİR KEZ çekiliyor.
  // Kaba tavan varsayılan yolda ≈240 KB (600 karakter × 20 mesaj × 5 oturum × 4 ajan)
  // ve bedeli her Ajan yüzeyi ziyaretinde ödeniyor. Sekmeye göre koşullu çekmek
  // ucuz görünüyordu ama `useApi` yolu `null`ken `yukleniyor: false` başlıyor —
  // sekme açıldığı KARE boyunca kapı "okunamadı" derdi, yani sağlıklı bir uç
  // arızalı görünürdü. Yanlış alarm, tasarruftan pahalıdır.
  const filo = useApi<Record<string, unknown>>("/api/ajanlar", 0);

  // ÇAPA SEKMEYİ DE SEÇER: `#/dashboard/chat/defter` bağı sayfayı açıp sekmeyi de
  // değiştirir. Sekmeyi seçmeden yalnız kaydırsaydık, gizli bir sekmedeki bölüme
  // kaydırma denemesi sessizce hiçbir şey yapmazdı — kırık bir bağ gibi görünürdü.
  const secili = bolumSec(bolum);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const hipotezler: readonly Hipotez[] = useMemo(() => {
    const ham = dizi(ajan.veri?.["hypotheses"]);
    return ham.map(hipotezOku).filter((h): h is Hipotez => h !== null);
  }, [ajan.veri]);

  const hafizaMetni = metin(hafiza.veri?.["lessons_md"]);
  const cozulmusHafiza = useMemo(() => (hafizaMetni === null ? null : hafizaAyristir(hafizaMetni)), [hafizaMetni]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            ajan.tazele();
            hafiza.tazele();
            filo.tazele();
          }}
        >
          <RefreshCw className="size-3.5" aria-hidden />
          Tazele
        </Button>
      </div>

      {/* SEKME ROTAYA YAZILIYOR, iç duruma DEĞİL: `#/dashboard/chat/defter`
          bağı paylaşılabilsin ve geri tuşu sekmeler arasında çalışsın diye.
          Yerel `useState` kullansaydık derin bağ sekmeyi hiç açmazdı.

          KAPI ARTIK SEKME ÇUBUĞUNUN ALTINDA: `Filo` AYRI bir uçtan (`/api/ajanlar`)
          besleniyor ve `/api/agent`in düşmesi onu GİZLEMEMELİ. Eski yerleşimde tek
          kapı tüm yüzeyi sarıyordu; hipotez ucu 500 dönseydi, ölçülmüş ve sağlam
          bir ajan defteri de "okunamadı" kutusunun arkasında kalırdı — bir kaynağın
          arızası başka bir kaynağın ölçümünü yutamaz. */}
      <Tabs value={secili} onValueChange={(v) => git(`/dashboard/chat/${v}`)} className="gap-4">
        <TabsList variant="line">
          <TabsTrigger value="sohbet">
            <MessagesSquare className="size-3.5" aria-hidden />
            Sohbet
          </TabsTrigger>
          <TabsTrigger value="defter">
            <Table2 className="size-3.5" aria-hidden />
            Defter
          </TabsTrigger>
          <TabsTrigger value="olcum">
            <Bot className="size-3.5" aria-hidden />
            Ölçüm
          </TabsTrigger>
          <TabsTrigger value="filo">
            <Users className="size-3.5" aria-hidden />
            Filo
          </TabsTrigger>
        </TabsList>

        {secili === "filo" ? (
          <TabsContent value="filo" id="bolum-filo" className="scroll-mt-20">
            <Filo durum={filo} />
          </TabsContent>
        ) : (
          <Kapi durum={ajan} ad="`/api/agent`" yukseklik="h-96">
            {(govde) => (
              <div className="flex flex-col gap-6">
                <Kunye govde={govde} hipotezler={hipotezler} />

                <TabsContent value="sohbet" id="bolum-sohbet" className="scroll-mt-20">
                  <SohbetHatti
                    hipotezler={hipotezler}
                    hafizaBasliklari={cozulmusHafiza === null ? [] : bolumOzeti(cozulmusHafiza)}
                    hafizaOlculemediNedeni={
                      hafiza.oturumDustu
                        ? "`/api/memory` 401 döndü — oturum düştü"
                        : hafizaMetni === null
                          ? (hafiza.hata ?? "`/api/memory` gövdesinde `lessons_md` alanı yok ya da boş")
                          : cozulmusHafiza?.bosBeyani === true
                            ? "uç `_No lessons yet._` döndü — `state/lessons.md` dosyası yok"
                            : null
                    }
                  />
                </TabsContent>

                <TabsContent value="defter" id="bolum-defter" className="scroll-mt-20">
                  {hipotezler.length === 0 ? (
                    <Olculemedi
                      neden="Gösterilecek öneri kaydı bulunamadı"
                      teknik="`/api/agent.hypotheses` boş ya da dizi değil"
                    />
                  ) : (
                    <HipotezDefteri hipotezler={hipotezler} />
                  )}
                </TabsContent>

                <TabsContent value="olcum" id="bolum-olcum" className="scroll-mt-20">
                  <Grafikler govde={govde} hipotezler={hipotezler} />
                </TabsContent>
              </div>
            )}
          </Kapi>
        )}
      </Tabs>
    </div>
  );
}

/* ---- KÜNYE: KİMİNLE KONUŞUYORUZ ------------------------------------------ */

/** Karne defterinin ŞU ANKİ sürümü — ajanın "kim olduğu". `/api/agent.scoreboard`
 *  `state/scoreboard.json`u ham taşıyor; alanın VARLIĞI garanti değil. */
function Kunye({
  govde,
  hipotezler,
}: {
  govde: Readonly<Record<string, unknown>>;
  hipotezler: readonly Hipotez[];
}) {
  const sb = nesne(govde["scoreboard"]);
  const surum = sb === null ? null : (metin(sb["current_version"]) ?? (say(sb["current_version"]) !== null ? bicimSayi(say(sb["current_version"]) ?? 0) : null));
  const kal = nesne(govde["calibration"]);
  const sonuclanan = say(kal?.["n"]);
  const beyinler = useMemo(() => {
    const k = new Set<string>();
    for (const h of hipotezler) if (h.kaynak?.startsWith("hermes:")) k.add(h.kaynak.slice(7));
    return [...k];
  }, [hipotezler]);

  const sonDamga = useMemo(() => {
    let en: number | null = null;
    for (const h of hipotezler) {
      if (h.ts === null) continue;
      const t = Date.parse(h.ts);
      if (!Number.isNaN(t) && (en === null || t > en)) en = t;
    }
    return en;
  }, [hipotezler]);

  const gunFarki =
    sonDamga === null ? null : Math.floor((Date.now() - sonDamga) / 86_400_000);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">Karşındaki kim?</CardTitle>
        <CardDescription>
          Bu sohbetin karşı tarafı bir kişi değil, bir öneri hattı: hipotez üreteçleri + backtest kapısı.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kutu
          etiket="strateji sürümü"
          deger={surum}
          neden="Strateji sürümü kaydedilmemiş"
          teknik="`/api/agent.scoreboard.current_version` yok — karne defteri sürümü yazmamış"
        />
        <Kutu etiket="defterdeki öneri" deger={bicimSayi(hipotezler.length)} neden="" />
        <Kutu
          etiket="sonucu ölçülen"
          deger={sonuclanan === null ? null : `${bicimSayi(sonuclanan)} / ${bicimSayi(hipotezler.length)}`}
          neden="Kaç önerinin sonucu ölçüldüğü henüz kaydedilmemiş"
          teknik="`/api/agent.calibration.n` yok"
        />
        <div className="rounded-lg border bg-muted/20 px-3 py-2">
          <p className="text-muted-foreground text-xs">son öneri</p>
          {sonDamga === null ? (
            <div className="mt-0.5">
              <Olculemedi
                neden="Son önerinin ne zaman geldiği okunamadı"
                teknik="hiçbir satırda ayrıştırılabilir `ts` yok"
              />
            </div>
          ) : (
            <p className="mt-0.5 font-medium text-sm leading-tight">
              {new Date(sonDamga).toLocaleDateString("tr-TR", { dateStyle: "medium" })}
              {gunFarki === null ? null : (
                <span className="ml-1 font-normal text-muted-foreground text-xs">
                  ({bicimSayi(gunFarki)} gün önce)
                </span>
              )}
            </p>
          )}
        </div>
        <div className="sm:col-span-2 lg:col-span-4">
          <p className="text-muted-foreground text-xs leading-5">
            LLM beyinleri:{" "}
            {beyinler.length === 0 ? (
              <span className="italic">
                defterdeki hiçbir satır `hermes:*` kaynağı taşımıyor — bu öneriler LLM'den değil,
                deterministik üreteçten gelmiş
              </span>
            ) : (
              beyinler.map((b) => (
                <Badge key={b} variant="outline" className="mr-1 text-[10px]">
                  {b}
                </Badge>
              ))
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function Kutu({
  etiket,
  deger,
  neden,
  teknik,
}: { etiket: string; deger: string | null; neden: string; teknik?: string }) {
  return (
    <div className="rounded-lg border bg-muted/20 px-3 py-2">
      <p className="text-muted-foreground text-xs">{etiket}</p>
      {deger === null ? (
        <div className="mt-0.5">
          <Olculemedi neden={neden} teknik={teknik} />
        </div>
      ) : (
        <p className="mt-0.5 font-medium text-lg tabular-nums leading-none">{deger}</p>
      )}
    </div>
  );
}
