"use client";

/* ============================================================================
   HERMES — yansıma hattı: "makine düşünüyor mu, yoksa yalnız bekliyor mu?"
   ----------------------------------------------------------------------------
   CANLILIK ÜÇ DEĞERLİDİR VE BURADA ÜÇ DEĞERLİ ÇİZİLİR. `status.active` `true|false|
   null` döner: `null`, kalp atışının OKUNAMADIĞI hâldir ve "durdu" demek bir İDDİA
   olurdu (hermes_runtime.status'ın kendi şerhi). Üstelik dördüncü bir incelik var ve
   uç onu da beyan ediyor: uzun bir arama sırasında kalp bayatlar ama arama ilerlemesi
   tazedir — o durumda `active=true` gelir ve NEDENİ `active_neden`de yazar. O cümle
   ekranda aynen duruyor; yoksa "kalp bayat ama canlı" hâli açıklanamaz görünürdü.

   GERİ SAYIM TEK KAYNAKTAN. "Sonraki yansımaya kaç işlem kaldı" panoda HESAPLANMAZ:
   eski arayüz `every - closed_trades` formülünü kendi yazıyordu ve defter `every`den
   büyük olan her kitapta 0 veriyordu — yani ekran hep "hazır" diyordu, ki yanlıştı.
   Sunucu artık `trades_until_next`i kendisi ölçüyor; pano onu ÇİZİYOR.

   UFUK BİR VE'DİR, VEYA DEĞİL. Yansıma için hem işlem sayısı hem TAKVİM AÇIKLIĞI
   birlikte dolmalı (`_horizon_ok` STRICT AND). İki çubuk ayrı çiziliyor: biri dolup
   öteki boşken "hazır" yazmak, guardrail'in tam olarak engellediği şeyi göstermek olurdu.

   BEYİN ZİNCİRİNDE AD SAYMAK KOTA SAYMAK DEĞİLDİR. `independent_upstreams` çoğu
   kurulumda `null` gelir ve nedeni yükte yazılıdır ("yerel ajanın çağrı başına hangi
   uca gittiği ÖLÇÜLMÜYOR"). Zincirdeki üç adı üç yedek sanmak canlıda ölçülmüş bir
   yanılgıydı; `same_model_ids` aynı modele giden adları ADIYLA gösterir.
   ============================================================================ */
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import {
  anMetni,
  Beyan,
  BolumKarti,
  Deger,
  Kapi,
  Kutu,
  Olculemedi,
  OlculemediHucre,
  para,
  Satir,
  sayi,
  UcDegerli,
  yas,
  yuzde,
} from "../ogrenme/ortak";
import type {
  DolguKuyrugu,
  HarcamaDetayi,
  HermesDurumu,
  HermesGovdesi,
  Isinma,
  TeshisGovdesi,
} from "../ogrenme/tipler";

const HARCAMA_CONFIG = {
  cost_usd: { label: "Günlük maliyet (USD)", color: "var(--chart-2)" },
} satisfies ChartConfig;

export function Hermes({ hermes, teshis }: { hermes: Durum<HermesGovdesi>; teshis: Durum<TeshisGovdesi> }) {
  return (
    <BolumKarti kimlik="hermes" baslik="Hermes" soru="Yansıma hattı ne durumda, geri dolum nerede?" ikon={Sparkles}>
      <Kapi durum={hermes} ad="/api/hermes" yukseklik="h-64">
        {(v) => (
          <div className="flex flex-col gap-6">
            <HatDurumu s={v.status} />
            <GeriSayim s={v.status} />
            <BeyinZinciri s={v.status} />
            <Dolgu kuyruk={v.learning?.besleme?.dolgu_kuyrugu ?? null} />
            <HarcamaKutusu govde={v} />
            {/* ISINMA AYRI UÇTAN GELİR: kendi kapısını taşır ki `/api/diagnostics`
                düşerse Hermes kartının geri kalanı çizilmeye devam etsin. */}
            <Kutu
              baslik="Isınma (warmup) — ajan yoklaması"
              aciklama="Kaynak /api/diagnostics `mlops.warmup`. Yansımadan AYRI bir kadans: model uçlarını yoklar."
            >
              <Kapi durum={teshis} ad="/api/diagnostics" yukseklik="h-24">
                {(t) => <IsinmaSatirlari w={t.mlops?.warmup} />}
              </Kapi>
            </Kutu>
          </div>
        )}
      </Kapi>
    </BolumKarti>
  );
}

/* ---- (1) HAT DURUMU ------------------------------------------------------ */

function HatDurumu({ s }: { s: HermesDurumu | undefined }) {
  if (!s) {
    return <Olculemedi neden="/api/hermes yükünde `status` bloğu YOK — yansıma hattının durumu bu turda hiç ölçülmedi." />;
  }
  const pollYasi = yas(s.last_poll);
  const poll = typeof s.poll_seconds === "number" ? s.poll_seconds : null;
  // BAYATLIK HÜKMÜ PANODA VERİLMEZ, YALNIZ GÖSTERİLİR: eşik sunucunun kanunudur
  // (KALP_PAY × poll). Burada kendi çarpanımı yazsaydım iki ayrı bayatlık tanımı olurdu.
  const pollOrani = pollYasi !== null && poll !== null && poll > 0 ? pollYasi.saniye / poll : null;

  return (
    <Kutu baslik="Yansıma hattı" aciklama="Kalp atışı, süreç konumu ve son yansımanın sonucu.">
      <div className="flex flex-wrap items-center gap-2">
        <UcDegerli
          deger={s.active ?? null}
          evet="hat CANLI"
          hayir="hat DURMUŞ"
          neden={s.active_neden ?? "`status.active` null — kalp atışı okunamadı; 'durdu' demek ölçülmemiş bir iddia olurdu."}
        />
        <Badge variant="outline">{s.surec_ici ? "süreç içi iplik" : "ayrı birim (systemd)"}</Badge>
        {s.reflecting === true ? (
          <Badge variant="outline" className="border-primary/40 text-primary">
            şu an yansıma koşuyor
          </Badge>
        ) : null}
        <UcDegerli
          deger={s.brain_degraded ?? null}
          evet="deterministik yola düştü"
          hayir="LLM beyni aktif"
          neden="`brain_degraded` yükte yok — beynin bozunup bozunmadığı ölçülemedi."
          evetIyi={false}
        />
      </div>
      {s.active_neden ? <Beyan>Canlılık gerekçesi: {s.active_neden}</Beyan> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col">
          <Satir etiket="Son yoklama (poll)">
            <Deger
              metin={
                pollYasi === null
                  ? null
                  : `${pollYasi.metin}${anMetni(s.last_poll) ? ` · ${anMetni(s.last_poll)}` : ""}`
              }
              neden="`last_poll` damgası yok — döngü bu süreçte hiç yoklama yapmamış."
              className="text-xs"
            />
          </Satir>
          <Satir etiket="Yoklama periyodu">
            <Deger metin={poll === null ? null : `${sayi(poll, 0)} sn`} neden="`poll_seconds` yükte yok." />
          </Satir>
          <Satir etiket="Yoklama gecikmesi (periyodun katı)">
            <Deger
              metin={pollOrani === null ? null : `${sayi(pollOrani, 1)}×`}
              neden="damga ya da periyot eksik — gecikme oranı ölçülemedi. Bayatlık eşiği sunucunun kanunudur, panoda yeniden tanımlanmaz."
            />
          </Satir>
          <Satir etiket="Arama durumu">
            <Deger
              metin={s.search_durumu ?? null}
              neden="`search_durumu` yükte yok — koordinat-inişi aramasının durumu ölçülemedi (üç değerli: kosuyor/yok/olculemedi)."
              className="text-xs"
            />
          </Satir>
        </div>
        <div className="flex flex-col">
          <Satir etiket="Toplam yansıma">
            <Deger metin={sayi(s.reflections, 0)} neden="`reflections` sayacı yükte yok." />
          </Satir>
          <Satir etiket="Son yansıma">
            <Deger
              metin={(() => {
                const y = yas(s.last_reflection);
                return y === null ? null : y.metin;
              })()}
              neden="`last_reflection` damgası yok — hiç yansıma koşmamış (az önce koştu DEĞİL)."
              className="text-xs"
            />
          </Satir>
          <Satir etiket="Son sonuç">
            <Deger metin={s.last_result ?? null} neden="`last_result` yok — son yansımanın kolu kaydedilmemiş." className="text-xs" />
          </Satir>
          <Satir etiket="Son değişken">
            <Deger metin={s.last_variable ?? null} neden="`last_variable` yok — son yansımanın dokunduğu parametre kaydedilmemiş." className="text-xs" />
          </Satir>
          <Satir etiket="Beyin / model">
            <Deger
              metin={s.brain || s.model ? `${s.brain ?? "?"} · ${s.model ?? "model adı yok"}` : null}
              neden="`brain`/`model` yükte yok — hangi beynin koştuğu ölçülemedi."
              className="text-xs"
            />
          </Satir>
        </div>
      </div>

      {s.search?.running === true ? (
        <div className="rounded-md border border-primary/30 bg-primary/5 p-3">
          <p className="font-medium text-xs">Koşan arama</p>
          <p className="mt-1 text-muted-foreground text-xs">
            faz {s.search.phase ?? "?"} · sonda {sayi(s.search.i, 0) ?? "?"}/{sayi(s.search.total, 0) ?? "?"} ·
            değişken {s.search.variable ?? "?"} · damga {anMetni(s.search.updated_at) ?? "yok"}
          </p>
        </div>
      ) : null}
    </Kutu>
  );
}

/* ---- (2) GERİ SAYIM + UFUK ----------------------------------------------- */

function CubuklulSatir({
  etiket,
  pay,
  payda,
  birim,
  neden,
}: {
  etiket: string;
  pay: number | null;
  payda: number | null;
  birim: string;
  neden: string;
}) {
  if (pay === null || payda === null || payda <= 0) {
    return (
      <div className="flex flex-col gap-1">
        <span className="text-muted-foreground text-xs">{etiket}</span>
        <OlculemediHucre neden={neden} />
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between text-xs">
        <span className="text-muted-foreground">{etiket}</span>
        <span className="tabular-nums">
          {sayi(pay, 0)} / {sayi(payda, 0)} {birim}
        </span>
      </div>
      <Progress value={Math.min(100, (pay / payda) * 100)} className="h-1.5" />
    </div>
  );
}

function GeriSayim({ s }: { s: HermesDurumu | undefined }) {
  if (!s) return null;
  const h = s.horizon;
  return (
    <Kutu
      baslik="Sonraki yansımaya ne kaldı?"
      aciklama="İki koşul BİRLİKTE dolmalı (STRICT AND): yeterli yeni işlem VE yeterli takvim açıklığı. Biri dolup öteki boşken hat hazır DEĞİLDİR."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <CubuklulSatir
          etiket="Yansıma sayacı (yeni kapanan işlem)"
          pay={typeof s.trades_since_last_reflection === "number" ? s.trades_since_last_reflection : null}
          payda={typeof s.reflection_every === "number" ? s.reflection_every : null}
          birim="işlem"
          neden="`trades_since_last_reflection` ya da `reflection_every` yükte yok — geri sayım ölçülemedi. Panoda formül yeniden yazılmaz."
        />
        <CubuklulSatir
          etiket="Ufuk · işlem bacağı"
          pay={typeof h?.trades === "number" ? h.trades : null}
          payda={typeof h?.trades_needed === "number" ? h.trades_needed : null}
          birim="işlem"
          neden="`horizon.trades` / `trades_needed` yok — ufkun işlem bacağı ölçülemedi."
        />
        <CubuklulSatir
          etiket="Ufuk · takvim bacağı"
          pay={typeof h?.span_days === "number" ? h.span_days : null}
          payda={typeof h?.min_days === "number" ? h.min_days : null}
          birim="gün"
          neden="`horizon.span_days` / `min_days` yok — ufkun takvim bacağı ölçülemedi."
        />
      </div>
      <div className="flex flex-col">
        <Satir etiket="Kalan işlem (uçtan)">
          <Deger
            metin={sayi(s.trades_until_next, 0)}
            neden="`trades_until_next` yükte yok — geri sayım sunucuda hesaplanmamış; pano kendi formülünü YAZMAZ."
          />
        </Satir>
        <Satir etiket="Kapanmış işlem (defterin boyu)">
          <Deger metin={sayi(s.closed_trades, 0)} neden="`closed_trades` yükte yok." />
        </Satir>
        <Satir etiket="Ufuk hazır mı?">
          <UcDegerli
            deger={s.horizon_ready ?? h?.ready ?? null}
            evet="hazır"
            hayir="henüz değil"
            neden="`horizon_ready` yükte yok — ufkun hükmü ölçülemedi."
          />
        </Satir>
        <Satir etiket="Ufkun ölçüldüğü rejim">
          <Deger
            metin={s.horizon_regime ?? h?.regime ?? null}
            neden="rejim null — ufuk rejim-bağımsız ölçülüyor (regime.json geçersiz/boş olabilir); bu bir arıza DEĞİL."
            className="text-xs"
          />
        </Satir>
      </div>
    </Kutu>
  );
}

/* ---- (3) BEYİN ZİNCİRİ --------------------------------------------------- */

function BeyinZinciri({ s }: { s: HermesDurumu | undefined }) {
  const z = s?.brain_chain;
  return (
    <Kutu
      baslik="Beyin zinciri — yedeklilik gerçek mi?"
      aciklama="Zincirdeki AD sayısı yedek sayısı DEĞİLDİR: iki ad aynı model kimliğine gidiyorsa tek uç vardır."
    >
      {!z ? (
        <Olculemedi neden="`status.brain_chain` yükte yok — zincirin yedekliliği bu turda hiç ölçülmedi." />
      ) : z.error ? (
        <Olculemedi
          neden={`zincir ölçümünün KENDİSİ düştü (${z.error}) — bu 'hermes hiç koşmadı' DEĞİL, denetimin bozulduğu hâldir.`}
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <Table className="min-w-[30rem]">
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="h-9">Sıra</TableHead>
                  <TableHead className="h-9">Beyin</TableHead>
                  <TableHead className="h-9">Model kimliği</TableHead>
                  <TableHead className="h-9">Hazır mı?</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(z.order ?? []).map((ad, i) => {
                  const hazir = (z.ready ?? []).includes(ad);
                  const uygun = s?.brain_availability?.[ad];
                  return (
                    <TableRow key={ad} className="border-border/50">
                      <TableCell className="py-2.5 tabular-nums">{i + 1}</TableCell>
                      <TableCell className="py-2.5 font-medium">{ad}</TableCell>
                      <TableCell className="py-2.5 text-muted-foreground text-xs">
                        <Deger
                          metin={z.models?.[ad] ?? null}
                          neden="bu beynin model kimliği ölçülemedi — hangi uca gittiği bilinmiyor."
                        />
                      </TableCell>
                      <TableCell className="py-2.5">
                        <Badge
                          variant="outline"
                          className={
                            hazir
                              ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
                              : "text-muted-foreground"
                          }
                          title={uygun?.reason ?? undefined}
                        >
                          {hazir ? "hazır" : uygun?.credentials === false ? "anahtar yok" : "hazır değil"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          <div className="flex flex-col">
            <Satir etiket="Bağımsız uç sayısı">
              {z.independent_upstreams === null || z.independent_upstreams === undefined ? (
                <OlculemediHucre
                  neden={
                    z.independent_upstreams_reason ??
                    "`independent_upstreams` null ve uç nedenini yazmadı — bağımsız uç sayısı UYDURULMAZ."
                  }
                />
              ) : (
                <span className="tabular-nums">{sayi(z.independent_upstreams, 0)}</span>
              )}
            </Satir>
            <Satir etiket="Aynı model kimliğine giden adlar">
              {(z.same_model_ids ?? []).length === 0 ? (
                <span className="text-xs">ölçülen çakışma yok</span>
              ) : (
                <span className="text-xs">
                  {(z.same_model_ids ?? []).map((c) => c.join(" = ")).join(" · ")}
                </span>
              )}
            </Satir>
            <Satir etiket="Yerel ajan kipi">
              <Deger metin={z.nous_mode ?? null} neden="`nous_mode` yükte yok." className="text-xs" />
            </Satir>
          </div>
          {z.independent_upstreams_reason ? <Beyan>{z.independent_upstreams_reason}</Beyan> : null}
        </>
      )}
    </Kutu>
  );
}

/* ---- (4) GERİ DOLUM ------------------------------------------------------ */

function Dolgu({ kuyruk }: { kuyruk: DolguKuyrugu | null }) {
  return (
    <Kutu
      baslik="Görüş geri dolumu"
      aciklama="Kalibrasyonu besleyen kuyruk. Dolgu YALNIZ sonucu BİLİNEN planlara dokunabilir — o yüzden 'görüşsüz toplam' her zaman daha büyüktür ve bu bir arıza değildir."
    >
      {!kuyruk ? (
        <Olculemedi neden="`learning.besleme.dolgu_kuyrugu` null — kuyruk bu turda okunamadı (sunucu uyarısı: learning_scorecard_backfill_failed)." />
      ) : (
        <>
          {(() => {
            const toplam = kuyruk.n_plan;
            const gorussuz = kuyruk.gorussuz_toplam;
            if (typeof toplam !== "number" || typeof gorussuz !== "number" || toplam <= 0) {
              return (
                <Olculemedi neden="`n_plan` ya da `gorussuz_toplam` yükte yok — görüş kapsamı ölçülemedi (%100 DEĞİL)." />
              );
            }
            const gorusluOran = (toplam - gorussuz) / toplam;
            return (
              <div className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-muted-foreground">Görüşü olan plan</span>
                  <span className="tabular-nums">
                    {sayi(toplam - gorussuz, 0)} / {sayi(toplam, 0)} ({yuzde(gorusluOran, 1) ?? "?"})
                  </span>
                </div>
                <Progress value={Math.min(100, gorusluOran * 100)} className="h-1.5" />
              </div>
            );
          })()}
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="flex flex-col">
              <Satir etiket="Dolgulanabilir gün">
                <Deger metin={sayi(kuyruk.dolgulanabilir_gun, 0)} neden="`dolgulanabilir_gun` yükte yok." />
              </Satir>
              <Satir etiket="Dolgulanabilir satır">
                <Deger metin={sayi(kuyruk.dolgulanabilir_satir, 0)} neden="`dolgulanabilir_satir` yükte yok." />
              </Satir>
              <Satir etiket="En eski / en yeni gün">
                <Deger
                  metin={kuyruk.en_eski && kuyruk.en_yeni ? `${kuyruk.en_eski} → ${kuyruk.en_yeni}` : null}
                  neden="kuyrukta dolgulanabilir gün yok — aralık tanımsız."
                  className="text-xs"
                />
              </Satir>
            </div>
            <div className="flex flex-col">
              <Satir etiket="Gece tavanı">
                <Deger metin={sayi(kuyruk.gece_tavani, 0)} neden="`gece_tavani` yükte yok." />
              </Satir>
              <Satir etiket="Tahmini gece sayısı">
                <Deger
                  metin={sayi(kuyruk.tahmini_gece, 0)}
                  neden="tahmin null — kuyruk boş ya da tavan sıfır; 'bu gece biter' DEĞİL."
                />
              </Satir>
              <Satir etiket="Tavanın kaynağı">
                <Deger metin={kuyruk.tavan_kaynagi ?? null} neden="`tavan_kaynagi` yükte yok." className="text-xs" />
              </Satir>
            </div>
          </div>
          {kuyruk.tavan_formulu ? <Beyan>Tavan formülü: {kuyruk.tavan_formulu}</Beyan> : null}
          {kuyruk.beyan ? <Beyan>{kuyruk.beyan}</Beyan> : null}
        </>
      )}
    </Kutu>
  );
}

/* ---- (5) HARCAMA --------------------------------------------------------- */

function HarcamaKutusu({ govde }: { govde: HermesGovdesi }) {
  const h = govde.spend;
  const d: HarcamaDetayi | undefined = govde.spend_detay;
  const harcanan = typeof h?.spent_usd === "number" ? h.spent_usd : null;
  const butce = typeof h?.budget_usd === "number" ? h.budget_usd : null;
  const oran = harcanan !== null && butce !== null && butce > 0 ? harcanan / butce : null;

  const gunler = d && d.var === true ? (d.gunler ?? []) : [];
  const cizilebilir = gunler.filter(
    (g): g is { gun: string; cost_usd: number; n?: number } =>
      typeof g.gun === "string" && typeof g.cost_usd === "number" && Number.isFinite(g.cost_usd),
  );

  return (
    <Kutu baslik="Harcama" aciklama="Aylık bütçe ve gece maliyeti. Bu kart LLM harcamasını ölçer — kotayı değil.">
      {!h ? (
        <Olculemedi neden="/api/hermes yükünde `spend` bloğu YOK — aylık harcama bu turda ölçülemedi ('sıfır harcama' DEĞİL)." />
      ) : (
        <>
          {oran === null ? (
            <Olculemedi neden="`spent_usd` ya da `budget_usd` yükte yok (veya bütçe sıfır) — doluluk oranı ölçülemedi." />
          ) : (
            <div className="flex flex-col gap-1.5">
              <div className="flex items-baseline justify-between text-xs">
                <span className="text-muted-foreground">Bu ay ({h.month ?? "ay yazılmamış"})</span>
                <span className="tabular-nums">
                  {para(harcanan)} / {para(butce)} ({yuzde(oran, 0) ?? "?"})
                </span>
              </div>
              <Progress value={Math.min(100, oran * 100)} className="h-1.5" />
            </div>
          )}
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="flex flex-col">
              <Satir etiket="Bu ayki çağrı">
                <Deger metin={sayi(h.calls_this_month, 0)} neden="`calls_this_month` yükte yok." />
              </Satir>
              <Satir etiket="Kalan bütçe">
                <Deger metin={para(h.remaining_usd)} neden="`remaining_usd` yükte yok." />
              </Satir>
            </div>
            <div className="flex flex-col">
              <Satir etiket="Düşünce jetonu">
                <Deger
                  metin={sayi(h.thought_tokens, 0)}
                  neden="hiçbir harcama satırı düşünce jetonu taşımıyor — alan null gelir ve bu 0 DEĞİLDİR."
                />
              </Satir>
              <Satir etiket="Bütçe aşıldı mı?">
                <UcDegerli
                  deger={h.over_budget ?? null}
                  evet="AŞILDI"
                  hayir="aşılmadı"
                  neden="`over_budget` yükte yok — bütçe hükmü ölçülemedi."
                  evetIyi={false}
                />
              </Satir>
            </div>
          </div>
        </>
      )}

      {d === undefined ? (
        <Olculemedi neden="`spend_detay` yükte yok — günlük kırılım bu turda hiç üretilmedi." />
      ) : d.var === false ? (
        <Olculemedi neden={d.neden ?? "`spend_detay.var` false ve uç nedenini yazmadı."} />
      ) : cizilebilir.length === 0 ? (
        <Olculemedi neden={`harcama defterinde ${gunler.length} gün var ama hiçbiri hem \`gun\` hem \`cost_usd\` taşımıyor — günlük eğri çizilemedi.`} />
      ) : (
        <>
          <ChartContainer config={HARCAMA_CONFIG} className="aspect-auto h-44 w-full">
            <AreaChart data={cizilebilir} margin={{ bottom: 0, left: 0, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis axisLine={false} dataKey="gun" tickLine={false} tickMargin={8} minTickGap={24} />
              <YAxis axisLine={false} tickLine={false} tickMargin={8} width={52} tickFormatter={(v) => para(v, 2) ?? ""} />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    className="w-52"
                    formatter={(deger, _ad, yuk) => {
                      const p = (yuk as { payload?: { n?: number } } | undefined)?.payload;
                      return (
                        <span className="flex flex-col gap-0.5">
                          <span className="text-muted-foreground">
                            maliyet{" "}
                            <span className="ml-1 font-medium text-foreground tabular-nums">
                              {para(deger, 4) ?? "—"}
                            </span>
                          </span>
                          <span className="text-muted-foreground text-xs">
                            {typeof p?.n === "number" ? `${p.n} çağrı` : "çağrı sayısı ölçülemedi"}
                          </span>
                        </span>
                      );
                    }}
                  />
                }
              />
              <Area isAnimationActive={false}
                dataKey="cost_usd"
                type="monotone"
                stroke="var(--color-cost_usd)"
                fill="var(--color-cost_usd)"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </AreaChart>
          </ChartContainer>
          <Beyan>
            Defterin {sayi(d.satir_n, 0) ?? "?"} satırının {sayi(d.olculemeyen_satir, 0) ?? "?"} tanesi `cost_usd`
            taşımıyor; toplama 0 katkısıyla girdiler ve burada beyan ediliyorlar — toplam tek başına
            okunursa o çağrılar "bedava" görünürdü.
          </Beyan>
        </>
      )}
    </Kutu>
  );
}

/* ---- (6) ISINMA ---------------------------------------------------------- */

function IsinmaSatirlari({ w }: { w: Isinma | undefined }) {
  if (!w) {
    return <Olculemedi neden="/api/diagnostics yükünde `mlops.warmup` bloğu YOK — ısınma kadansı bu turda ölçülemedi." />;
  }
  return (
    <div className="flex flex-col">
      <Satir etiket="Son ısınma">
        <Deger
          metin={(() => {
            const y = yas(w.last);
            return y === null ? null : `${y.metin}${anMetni(w.last) ? ` · ${anMetni(w.last)}` : ""}`;
          })()}
          neden="`warmup.last` damgası yok — ısınma hiç koşmamış."
          className="text-xs"
        />
      </Satir>
      <Satir etiket="Tik / periyot">
        <Deger
          metin={
            typeof w.ticks === "number" && typeof w.every === "number" ? `${sayi(w.ticks, 0)} / ${sayi(w.every, 0)}` : null
          }
          neden="`ticks` ya da `every` yükte yok — ısınma sayacı ölçülemedi."
        />
      </Satir>
      <Satir etiket="Hiç yoklandı mı?">
        <UcDegerli
          deger={w.polled ?? null}
          evet="yoklandı"
          hayir="hiç yoklanmadı"
          neden="`warmup.polled` yükte yok — yoklama olgusu ölçülemedi."
        />
      </Satir>
      <Satir etiket="UCB başı (en umutlu adaylar)">
        {(w.ucb_top ?? []).length === 0 ? (
          <OlculemediHucre neden="`ucb_top` boş — ısınma hiç aday sıralamamış olabilir." />
        ) : (
          <span className="text-xs">{(w.ucb_top ?? []).join(", ")}</span>
        )}
      </Satir>
    </div>
  );
}
