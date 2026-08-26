"use client";

/* ============================================================================
   DÜRÜST KARNE — "öğreniyor mu, yoksa yalnız koşuyor mu?"
   ----------------------------------------------------------------------------
   BU KARTIN TEK İŞİ: döngünün NEREDE takıldığını adıyla söylemek. Sunucu bunu zaten
   ölçüyor (`analytics.learning_scorecard` → `loop_state` + `verdict`) ve o hükmün
   panoda TÜRETİLMESİ yasak: burada `shipped>0 ise ilerledi` gibi bir kural yazsaydım,
   sunucudaki kuralla sessizce ayrışırdı ve hangisinin doğru olduğu hiçbir yerde
   yazmazdı. Merdiven yalnız uçtan gelen `loop_state`i ÇİZER.

   TANINMAYAN `loop_state` UYDURULMAZ: sunucu bir gün altıncı bir hâl eklerse merdiven
   "ölçülemedi" der ve ham değeri ekrana yazar — beşinci hâle katlamak, bilmediğim bir
   şeyi biliyormuş gibi göstermek olurdu.

   DEFTERİN PAYDASI KARNENİN EN BÜYÜK YALANIYDI (analytics.py:711 şerhi): `trades_total`
   ham satır sayısıdır ve gövdesi REPLAY TOHUMUdur. Kompozisyon grafiği bu yüzden dört
   kovayı AYRI çizer ve min_sample paydasının hangi kovalardan oluştuğunu uçtan gelen
   `orneklem_kapsam` cümlesiyle yazar.

   SHIP EŞİĞİNİN SAYISI BU YÜKTE YOK. Karne kaç önerinin geçtiğini/reddedildiğini
   sayar ama kapının eşik SAYISINI (`reflect.py`de yaşıyor) hiçbir uç servis etmiyor —
   o yüzden burada sayı DEĞİL, sayım gösteriliyor ve eksikliği açıkça yazılıyor.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, Cell, LabelList, XAxis, YAxis } from "recharts";
import { Check, CircleDashed, ClipboardCheck, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

import Link from "../../rota";
import type { Durum } from "../../veri";
import { Beyan, BolumKarti, Deger, Kapi, Kutu, Olculemedi, Satir, sayi, yuzde } from "./ortak";
import type { DefterSayaci, HermesGovdesi, OgrenmeKarnesi } from "./tipler";

/* ---- DÖNGÜ MERDİVENİ ----------------------------------------------------- */

const ADIMLAR = [
  { baslik: "Hipotez üretildi", alt: "reflect koştu, öneri defterde" },
  { baslik: "Kapıdan geçti", alt: "OOS/backtest kapısı bir öneriyi yayına aldı" },
  { baslik: "Örneklem birikti", alt: "yayındaki sürüm min_sample kadar işlem kapattı" },
  { baslik: "Sonuç ölçüldü", alt: "realized_delta yazıldı — tahmin gerçekle kıyaslandı" },
  { baslik: "Kalibre ölçülüyor", alt: "yeterli sonuç çifti birikti, Brier/hit-rate hesaplanıyor" },
] as const;

/** `loop_state` → (kaç adım tamam, hangi adım TAKILI, kalibrasyon zayıf mı).
 *  Anahtarlar `analytics.learning_scorecard`ın ürettiği BEŞ dizgedir; başka bir
 *  değer gelirse tablo `undefined` döner ve merdiven "ölçülemedi" çizer. */
const MERDIVEN: Readonly<Record<string, { tamam: number; takili: number | null; zayif?: boolean }>> = {
  no_hypotheses: { tamam: 0, takili: 0 },
  no_ship_v1_stands: { tamam: 1, takili: 1 },
  shipped_awaiting_min_sample: { tamam: 2, takili: 2 },
  closing: { tamam: 4, takili: 4 },
  closed_learning: { tamam: 5, takili: null },
  closed_weak_cal: { tamam: 5, takili: null, zayif: true },
};

function Merdiven({ hal }: { hal: string | undefined }) {
  const k = hal === undefined ? undefined : MERDIVEN[hal];
  if (!k) {
    return (
      <Olculemedi
        neden={
          hal === undefined
            ? "Döngünün hangi adımda olduğu bildirilmedi"
            : `Sistem tanınmayan bir döngü durumu bildirdi ("${hal}") — bilinen bir adıma katlamak yerine boş bırakıldı`
        }
        teknik={
          hal === undefined
            ? "/api/hermes yükünde `learning.loop_state` yok"
            : "`loop_state` panonun tanıdığı beş hâlden biri değil"
        }
      />
    );
  }
  return (
    <ol className="flex flex-col gap-0 md:flex-row md:gap-0">
      {ADIMLAR.map((a, i) => {
        const tamam = i < k.tamam;
        const takili = k.takili === i;
        const zayifSon = k.zayif === true && i === ADIMLAR.length - 1;
        return (
          <li key={a.baslik} className="flex flex-1 gap-3 md:flex-col md:gap-2">
            <div className="flex flex-col items-center md:w-full md:flex-row">
              <span
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full border text-xs tabular-nums",
                  zayifSon
                    ? "border-amber-500/60 bg-amber-500/15 text-amber-700 dark:text-amber-300"
                    : tamam
                      ? "border-emerald-500/60 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                      : takili
                        ? "border-amber-500/60 bg-amber-500/15 text-amber-700 dark:text-amber-300"
                        : "border-border bg-muted/40 text-muted-foreground",
                )}
              >
                {zayifSon ? (
                  <TriangleAlert className="size-3.5" aria-hidden />
                ) : tamam ? (
                  <Check className="size-3.5" aria-hidden />
                ) : takili ? (
                  <CircleDashed className="size-3.5" aria-hidden />
                ) : (
                  i + 1
                )}
              </span>
              {/* Bağlayıcı çizgi: dikey (dar ekran) ve yatay (geniş) — son adımda yok. */}
              {i < ADIMLAR.length - 1 ? (
                <span
                  className={cn(
                    "my-1 w-px flex-1 md:my-0 md:mx-2 md:h-px md:w-auto",
                    tamam ? "bg-emerald-500/40" : "bg-border",
                  )}
                  aria-hidden
                />
              ) : null}
            </div>
            <div className="min-w-0 pb-4 md:pb-0 md:pr-3">
              <p className={cn("font-medium text-sm", !tamam && !takili && "text-muted-foreground")}>{a.baslik}</p>
              <p className="mt-0.5 text-muted-foreground text-xs leading-snug">{a.alt}</p>
              {takili ? (
                <Badge variant="outline" className="mt-1.5 border-amber-500/40 text-amber-700 dark:text-amber-300">
                  burada takılı
                </Badge>
              ) : null}
              {zayifSon ? (
                <Badge variant="outline" className="mt-1.5 border-amber-500/40 text-amber-700 dark:text-amber-300">
                  kalibrasyon zayıf
                </Badge>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

/* ---- DEFTER KOMPOZİSYONU ------------------------------------------------- */

const DEFTER_CONFIG = {
  n: { label: "Satır" },
  canli: { label: "Canlı/paper", color: "var(--chart-2)" },
  tohum: { label: "Replay başlangıç verisi", color: "var(--chart-4)" },
  belirsiz: { label: "Belirsiz", color: "var(--chart-3)" },
  damgasiz: { label: "Damgasız", color: "var(--muted-foreground)" },
} satisfies ChartConfig;

interface DefterKovasi {
  readonly kova: string;
  readonly n: number;
  readonly renk: string;
  readonly aciklama: string;
}

function defterKovalari(d: DefterSayaci | undefined): DefterKovasi[] {
  if (!d) return [];
  const kayitlar: readonly [string, unknown, string, string][] = [
    ["Canlı/paper", d.live_paper_n, "var(--color-canli)", "kanıtlı canlı satır — min_sample paydasının çekirdeği"],
    ["Replay başlangıç verisi", d.replay_seed_n, "var(--color-başlangıç verisi)", "tek toplu yazım, bugünkü evrenle: TRAINING sayılır, paydaya GİRMEZ"],
    ["Belirsiz", d.belirsiz_n, "var(--color-belirsiz)", "damgası var ama kaynağı ayrışmıyor — paydaya girer, kanıt sayılmaz"],
    ["Damgasız", d.damgasiz_n, "var(--color-damgasiz)", "hiç damga yok; başlangıç verisine yazmak uydurma olurdu"],
  ];
  return kayitlar
    .filter((k): k is [string, number, string, string] => typeof k[1] === "number" && Number.isFinite(k[1]))
    .map(([kova, n, renk, aciklama]) => ({ kova, n, renk, aciklama }));
}

/* ---- KAPI SAYIMI --------------------------------------------------------- */

const KAPI_CONFIG = {
  n: { label: "Öneri" },
  gecti: { label: "Geçti", color: "var(--chart-2)" },
  backtest: { label: "Backtest reddi", color: "var(--destructive)" },
  guard: { label: "Guard reddi", color: "var(--chart-4)" },
} satisfies ChartConfig;

/* ---- KPI ----------------------------------------------------------------- */

function Kpi({
  baslik,
  metin: m,
  neden,
  teknik,
  alt,
}: {
  baslik: string;
  metin: string | null;
  neden: string;
  teknik?: string;
  alt: string;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card p-4">
      <p className="text-muted-foreground text-xs">{baslik}</p>
      <p className="mt-1.5 text-2xl leading-none tracking-tight tabular-nums">
        <Deger metin={m} neden={neden} teknik={teknik} />
      </p>
      <p className="mt-2 text-muted-foreground text-xs leading-snug">{alt}</p>
    </div>
  );
}

/* ---- BÖLÜM --------------------------------------------------------------- */

export function Karne({ hermes }: { hermes: Durum<HermesGovdesi> }) {
  return (
    <BolumKarti
      kimlik="karne"
      baslik="Dürüst karne"
      soru="Öğrenme döngüsü gerçekten kapanıyor mu?"
      ikon={ClipboardCheck}
    >
      <KarneGovdesi hermes={hermes} />
    </BolumKarti>
  );
}

function KarneGovdesi({ hermes }: { hermes: Durum<HermesGovdesi> }) {
  // Kapı `/api/hermes` içindir; karne bloğunun KENDİSİ de eksik olabilir ve o AYRI bir hâl:
  // uç okundu ama `learning` üretilmedi. İkisini tek "okunamadı" cümlesine katlamak,
  // ağ arızasıyla eksik hesabı aynı yere yazmak olurdu.
  return (
    <Kapi durum={hermes} ad="/api/hermes" yukseklik="h-64">
      {(v) => {
        const l: OgrenmeKarnesi | undefined = v.learning;
        if (!l) {
          return (
            <Olculemedi
              neden="Karne bu turda hiç hesaplanmadı — kayıtların boş olduğu anlamına gelmez"
              teknik="/api/hermes okundu ama `learning` bloğu YOK"
            />
          );
        }
        const sc = l.status_counts ?? {};
        const cal = l.calibration;
        const defter = l.defter;
        const kovalar = defterKovalari(defter);
        const kovaToplam = kovalar.reduce((t, k) => t + k.n, 0);
        const kapiSatirlari = [
          { ad: "Geçti (ship)", n: l.shipped, renk: "var(--color-gecti)" },
          { ad: "Backtest reddi", n: l.rejected_by_backtest, renk: "var(--color-backtest)" },
          { ad: "Guard reddi", n: l.rejected_by_guard, renk: "var(--color-guard)" },
        ].filter((k): k is { ad: string; n: number; renk: string } => typeof k.n === "number");
        const minOrnek = typeof l.min_sample === "number" ? l.min_sample : null;
        const ornek = typeof defter?.orneklem_n === "number" ? defter.orneklem_n : null;

        return (
          <div className="flex flex-col gap-6">
            {/* HÜKÜM ÖNCE: operatörün ilk okuyacağı cümle uçtan gelen `verdict`tir. */}
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
              <p className="text-muted-foreground text-xs">Uçtan gelen karar</p>
              <p className="mt-1 text-sm leading-relaxed">
                {l.verdict ?? (
                  <span className="text-muted-foreground italic">
                    ölçülemedi — `learning.verdict` yükte yok; döngünün hükmü bu turda yazılmadı.
                  </span>
                )}
              </p>
              {l.loop_state ? (
                <p className="mt-2 text-muted-foreground text-xs">
                  döngü hâli: <code className="rounded bg-muted px-1 py-0.5">{l.loop_state}</code>
                </p>
              ) : null}
            </div>

            <Kutu
              baslik="Döngü merdiveni"
              aciklama="Beş adımın hangisinde takıldığımızı UÇ söylüyor (loop_state); pano yalnız çiziyor."
            >
              <Merdiven hal={l.loop_state} />
            </Kutu>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Kpi
                baslik="Yayına giren öneri"
                metin={sayi(l.shipped, 0)}
                neden="Kaç önerinin yayına girdiği bildirilmedi"
                teknik="/api/hermes `learning.shipped` basmadı"
                alt={`Geri alınan: ${sayi(l.rolled_back, 0) ?? "ölçülemedi"} · terfi: ${sayi(l.promoted, 0) ?? "ölçülemedi"}`}
              />
              <Kpi
                baslik="Ölçülmüş sonuç"
                metin={sayi(l.outcomes_measured, 0)}
                neden="Kaç önerinin sonucu ölçüldüğü kaydedilmemiş"
                teknik="`learning.outcomes_measured` yükte yok"
                alt="realized_delta yazılmış hipotez sayısı — döngünün gerçekten kapandığı tek kanıt."
              />
              <Kpi
                baslik="Kalibrasyon (Brier)"
                metin={cal?.brier === null || cal?.brier === undefined ? null : sayi(cal.brier, 3)}
                neden={
                  cal === undefined
                    ? "Tahmin isabeti hiç hesaplanmadı"
                    : `Tahmin isabeti bu örneklemde hesaplanamadı (${cal.n ?? "bilinmeyen sayıda"} çift)`
                }
                teknik={
                  cal === undefined
                    ? "`learning.calibration` bloğu yok"
                    : "Brier bu örneklemde hesaplanamadı — 0 DEĞİL, ölçülmedi"
                }
                alt={`Çift sayısı: ${sayi(cal?.n, 0) ?? "ölçülemedi"} · isabet: ${
                  cal?.hit_rate === null || cal?.hit_rate === undefined ? "ölçülemedi" : (yuzde(cal.hit_rate, 0) ?? "ölçülemedi")
                }`}
              />
              <Kpi
                baslik="Örneklem / eşik"
                metin={ornek === null || minOrnek === null ? null : `${sayi(ornek, 0)} / ${sayi(minOrnek, 0)}`}
                neden={
                  minOrnek === null
                    ? "Gereken en az işlem sayısı bildirilmedi"
                    : "Şu ana kadar biriken işlem sayısı bildirilmedi"
                }
                teknik={
                  minOrnek === null
                    ? "`learning.min_sample` yükte yok — 30 varsaymak yasak, eşik goal.yaml'dan gelir"
                    : "`learning.defter.orneklem_n` yükte yok"
                }
                alt="Payda = canlı/paper + belirsiz. Replay tohumu TRAINING'dir, buraya girmez."
              />
            </div>

            {/* ---- DEFTERİN KAYNAK KOMPOZİSYONU ---------------------------- */}
            <Kutu
              baslik="Defterin kaynak kompozisyonu"
              aciklama="Ham satır sayısı bir olgunluk kanıtı DEĞİLDİR: başlangıç verisi satırları tek toplu yazımdan gelir ve bugünkü evrenle üretilmiştir."
            >
              {kovalar.length === 0 ? (
                <Olculemedi
                  neden="Kayıtların kaynak dağılımı ölçülemedi"
                  teknik="`learning.defter` kaynak sayaçlarının hiçbiri sayı değil"
                />
              ) : (
                <>
                  <ChartContainer config={DEFTER_CONFIG} className="aspect-auto h-48 w-full">
                    <BarChart data={kovalar} margin={{ bottom: 0, left: 0, right: 8, top: 16 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis axisLine={false} dataKey="kova" tickLine={false} tickMargin={10} />
                      <YAxis axisLine={false} tickLine={false} tickMargin={8} width={44} allowDecimals={false} />
                      <ChartTooltip
                        cursor={false}
                        content={
                          <ChartTooltipContent
                            className="w-64"
                            labelFormatter={(_e, yuk) => {
                              const ilk = Array.isArray(yuk) ? yuk[0] : undefined;
                              const p = (ilk as { payload?: DefterKovasi } | undefined)?.payload;
                              if (!p) return "kova okunamadı";
                              const pay = kovaToplam > 0 ? ` · ${yuzde(p.n / kovaToplam, 1) ?? ""}` : "";
                              return `${p.kova}${pay}`;
                            }}
                            formatter={(deger, _ad, yuk) => {
                              const p = (yuk as { payload?: DefterKovasi } | undefined)?.payload;
                              return (
                                <span className="flex flex-col gap-0.5">
                                  <span className="text-muted-foreground">
                                    satır <span className="ml-1 font-medium text-foreground tabular-nums">{String(deger)}</span>
                                  </span>
                                  {p ? <span className="text-muted-foreground text-xs leading-snug">{p.aciklama}</span> : null}
                                </span>
                              );
                            }}
                          />
                        }
                      />
                      <Bar isAnimationActive={false} dataKey="n" radius={[4, 4, 0, 0]}>
                        <LabelList dataKey="n" position="top" className="fill-muted-foreground" fontSize={11} />
                        {kovalar.map((k) => (
                          <Cell key={k.kova} fill={k.renk} fillOpacity={0.9} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ChartContainer>

                  <div className="flex flex-col">
                    <Satir etiket="Ham satır (trades.jsonl)">
                      <Deger
                        metin={sayi(l.trades_total, 0)}
                        neden="Toplam kayıt sayısı bildirilmedi"
                        teknik="`learning.trades_total` yükte yok"
                      />
                    </Satir>
                    <Satir etiket="Kanıtlı canlı (gercek_canli_n)">
                      <Deger
                        metin={sayi(defter?.gercek_canli_n, 0)}
                        neden="Kanıtlı canlı işlem sayısı bildirilmedi"
                        teknik="`defter.gercek_canli_n` yükte yok"
                      />
                    </Satir>
                    <Satir etiket="Training (başlangıç verisi)">
                      <Deger
                        metin={sayi(defter?.training_n, 0)}
                        neden="Eğitim amaçlı kayıtların payı bildirilmedi"
                        teknik="`defter.training_n` yükte yok"
                      />
                    </Satir>
                    <Satir etiket="Yayındaki sürüm">
                      <Deger
                        metin={l.current_version === null || l.current_version === undefined ? null : `v${l.current_version}`}
                        neden="Hangi sürümün yayında olduğu bu karneden okunamadı"
                        teknik="`learning.current_version` yükte yok"
                      />
                    </Satir>
                    <Satir etiket="Toplam sürüm sayısı">
                      <Deger
                        metin={sayi(l.versions, 0)}
                        neden="Toplam sürüm sayısı bildirilmedi"
                        teknik="`learning.versions` yükte yok"
                      />
                    </Satir>
                    <Satir etiket="Aşırı-uyum şüphelisi">
                      <Deger
                        metin={sayi(l.overfit_suspects, 0)}
                        neden="Şüpheli öneri sayısı bildirilmedi"
                        teknik="`learning.overfit_suspects` yükte yok"
                      />
                    </Satir>
                  </div>
                  {defter?.orneklem_kapsam ? <Beyan>{defter.orneklem_kapsam}</Beyan> : null}
                </>
              )}
            </Kutu>

            {/* ---- SHIP KAPISI --------------------------------------------- */}
            <Kutu
              baslik="Ship kapısı — kaç öneri nerede düştü"
              aciklama="Sayım uçtan geliyor; kapının EŞİK SAYISI hiçbir uçta servis edilmiyor (aşağıdaki not)."
            >
              {kapiSatirlari.length === 0 ? (
                <Olculemedi
                  neden="Önerilerin nerede elendiği sayılamadı"
                  teknik="`learning.shipped` / `rejected_by_backtest` / `rejected_by_guard` alanlarının hiçbiri sayı değil"
                />
              ) : (
                <ChartContainer config={KAPI_CONFIG} className="aspect-auto h-40 w-full">
                  <BarChart
                    data={kapiSatirlari}
                    layout="vertical"
                    margin={{ bottom: 0, left: 0, right: 24, top: 4 }}
                  >
                    <CartesianGrid horizontal={false} />
                    <XAxis type="number" axisLine={false} tickLine={false} allowDecimals={false} />
                    <YAxis type="category" dataKey="ad" axisLine={false} tickLine={false} width={110} />
                    <ChartTooltip cursor={false} content={<ChartTooltipContent className="w-48" />} />
                    <Bar isAnimationActive={false} dataKey="n" radius={4}>
                      <LabelList dataKey="n" position="right" className="fill-muted-foreground" fontSize={11} />
                      {kapiSatirlari.map((k) => (
                        <Cell key={k.ad} fill={k.renk} fillOpacity={0.9} />
                      ))}
                    </Bar>
                  </BarChart>
                </ChartContainer>
              )}
              <div className="flex flex-col">
                {Object.keys(sc).length === 0 ? (
                  <Olculemedi
                    neden="Önerilerin durum dağılımı ölçülemedi"
                    teknik="`learning.status_counts` boş"
                  />
                ) : (
                  Object.entries(sc).map(([ad, n]) => (
                    <Satir key={ad} etiket={ad}>
                      <Deger
                        metin={sayi(n, 0)}
                        neden="Bu durumdaki öneri sayısı bildirilmedi"
                        teknik={`status_counts.${ad} sayı taşımıyor`}
                      />
                    </Satir>
                  ))
                )}
              </div>
              <Beyan>
                Kapının SAYISAL eşiği (ship yetkilisi / ön eleme) bu yükte YOK — `reflect.py` içinde
                yaşıyor ve hiçbir uç onu servis etmiyor. Burada bir sayı yazmak uydurma olurdu; bu
                yüzden yalnız sayım gösteriliyor.
              </Beyan>
            </Kutu>

            {/* ---- BESLEME KANALLARI --------------------------------------- */}
            <Kutu
              baslik="Besleme kanalları — '0'ın nedeni"
              aciklama="Yukarıdaki sayılar dürüst; ama neden düşük oldukları başka bir yerde ölçülüyor."
            >
              <BeslemeSatirlari l={l} />
            </Kutu>
          </div>
        );
      }}
    </Kapi>
  );
}

function BeslemeSatirlari({ l }: { l: OgrenmeKarnesi }) {
  const b = l.besleme;
  if (!b) {
    return (
      <Olculemedi
        neden="Besleme kanalları bu turda hiç ölçülmedi"
        teknik="`learning.besleme` bloğu yükte yok"
      />
    );
  }
  const sprint = b.antrenman_sprinti;
  const dolgu = b.dolgu_kuyrugu;
  const antrenman = b.antrenman;
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-lg border border-border/60 p-3">
        <p className="font-medium text-sm">Antrenman turu</p>
        {sprint === null || sprint === undefined ? (
          <Olculemedi
            className="mt-2"
            neden="Antrenman turunun durumu okunamadı"
            teknik="`besleme.antrenman_sprinti` null (sunucu olayı: learning_scorecard_sprint_failed)"
          />
        ) : (
          <div className="mt-2 flex flex-col">
            <Satir etiket="Şimdi koşmalı mı?">
              <span>{sprint.kos === undefined ? "ölçülemedi" : sprint.kos ? "evet" : "hayır"}</span>
            </Satir>
            <Satir etiket="Sebep">
              <Deger
                metin={sprint.sebep ?? null}
                neden="Otomatik döngünün bu turdaki sebebi kaydedilmemiş"
                teknik="`sprint.sebep` yok"
                className="text-xs"
              />
            </Satir>
            <Satir etiket="Son antrenman turundan geçen gün">
              <Deger
                metin={sayi(sprint.gecen_gun, 0)}
                neden="Son antrenmandan bu yana geçen gün ölçülemedi — hiç koşmamış olabilir"
                teknik="`gecen_gun` yok"
              />
            </Satir>
          </div>
        )}
        <Link
          href="/dashboard/productivity/sprint"
          className="mt-2 inline-block text-primary text-xs underline-offset-4 hover:underline"
        >
          Antrenman yüzeyinde ayrıntısı →
        </Link>
      </div>

      <div className="rounded-lg border border-border/60 p-3">
        <p className="font-medium text-sm">Görüş dolgu kuyruğu</p>
        {dolgu === null || dolgu === undefined ? (
          <Olculemedi
            className="mt-2"
            neden="Eksik görüş kuyruğu okunamadı"
            teknik="`besleme.dolgu_kuyrugu` null (sunucu olayı: learning_scorecard_backfill_failed)"
          />
        ) : (
          <div className="mt-2 flex flex-col">
            <Satir etiket="Dolgulanabilir gün">
              <Deger
                metin={sayi(dolgu.dolgulanabilir_gun, 0)}
                neden="Tamamlanabilir gün sayısı ölçülemedi"
                teknik="`dolgulanabilir_gun` yok"
              />
            </Satir>
            <Satir etiket="Dolgulanabilir satır">
              <Deger
                metin={sayi(dolgu.dolgulanabilir_satir, 0)}
                neden="Tamamlanabilir kayıt sayısı ölçülemedi"
                teknik="`dolgulanabilir_satir` yok"
              />
            </Satir>
            <Satir etiket="Görüşsüz plan (toplam)">
              <Deger
                metin={sayi(dolgu.gorussuz_toplam, 0)}
                neden="Görüş kaydedilmemiş plan sayısı ölçülemedi"
                teknik="`gorussuz_toplam` yok"
              />
            </Satir>
          </div>
        )}
        <Link
          href="/dashboard/productivity/hermes"
          className="mt-2 inline-block text-primary text-xs underline-offset-4 hover:underline"
        >
          Hermes hattında ilerlemesi →
        </Link>
      </div>

      <div className="rounded-lg border border-border/60 p-3">
        <p className="font-medium text-sm">Deneme model antrenmanı</p>
        {antrenman === null || antrenman === undefined ? (
          <Olculemedi
            className="mt-2"
            neden="Model eğitiminin durumu okunamadı"
            teknik="`besleme.antrenman` null (sunucu olayı: learning_scorecard_training_failed)"
          />
        ) : (
          <div className="mt-2 flex flex-col">
            <Satir etiket="Model kuruldu mu?">
              <span>{antrenman.kuruldu === undefined ? "ölçülemedi" : antrenman.kuruldu ? "evet" : "hayır"}</span>
            </Satir>
            <Satir etiket="Fit satırı">
              <Deger
                metin={sayi(antrenman.n_fit, 0)}
                neden="Modelin kaç satırla eğitildiği bildirilmedi — hiç kurulmamış olabilir"
                teknik="`n_fit` yok; 0 yazmak yanlış olurdu"
              />
            </Satir>
            <Satir etiket="Terfi eşiği (çift)">
              <Deger
                metin={
                  antrenman.terfi?.n_live === null || antrenman.terfi?.n_live === undefined
                    ? null
                    : `${sayi(antrenman.terfi.n_live, 0)} / ${sayi(antrenman.terfi.promote_min_n, 0) ?? "?"}`
                }
                neden="Terfi için biriken kıyas sayısı ölçülemedi"
                teknik="`terfi.n_live` yok"
              />
            </Satir>
          </div>
        )}
        <a className="mt-2 inline-block text-primary text-xs underline-offset-4 hover:underline" href="#/dashboard/academy/golge">
          Gölge bölümünde ayrıntısı →
        </a>
      </div>
    </div>
  );
}
