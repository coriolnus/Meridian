"use client";

/* ============================================================================
   SEKME 1 — KARAR ZİNCİRİ: aday → kapı → hüküm
   ----------------------------------------------------------------------------
   Bu tahta bir İŞ TAHTASI DEĞİL, bir KARAR KAYDIdır. Şablonun kanban'ında kart
   sürüklenir; burada sürüklenmez ve bu kasıtlı: kolonlar `gate_verdict`in
   kendisidir (`guard.classify_gate` çıktısı), yani bir kartı elle taşımak kapının
   hükmünü elle değiştirmek olurdu. Pano hükmü GÖSTERİR, kurmaz — onay yolu ayrı
   ve yetkili bir uçtan geçer (`POST /api/plan/{id}/onayla`, Onay kuyruğu yüzeyi).

   İKİ EKSEN AYNI ANDA: üstteki tahta HÜKÜM eksenidir (NO_GO/REVIEW/GO), alttaki
   tablo KAPI AŞAMASI eksenidir (hangi ölçüt kaç adayı eledi). İkisi aynı planları
   iki farklı soruyla kesiyor; birini seçtirmek diğerini kaybettirirdi.

   SAYIM ÇAPRAZ DENETLENİR: kolon sayaçlarını kendimiz sayıyoruz ama uç da
   `verdict_counts` gönderiyor (analytics.py:259). İkisi ayrışırsa EKRANDA YAZAR —
   sessizce kendi sayımıza güvenmek, ucun ve panonun iki farklı gerçeği
   göstermesi demek olurdu.
   ============================================================================ */
import { useMemo } from "react";

import { Activity, AlertTriangle, Layers, Radar, ScanSearch } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { useBugun } from "../../durum";
import { useApi } from "../../veri";
import { Hal, OlculemedBlok, Olculemedi } from "./Hal";
import { HukumGrafigi, HuniGrafigi, type HuniAsamasi, type SeansHukmu } from "./Grafikler";
import { KapiTablosu, kapilariOzetle } from "./KapiTablosu";
import { PlanKarti } from "./PlanKarti";
import { kisaTarih, mantik, metin, nesne, sayi } from "./oku";
import { HUKUM_BASLIGI, HUKUM_SIRASI, hukumu, planlariOku, type Hukum, type Plan } from "./planlar";

/* --------------------------------------------------------------------------
   SON DÖNGÜ — huninin kaynağı. `var:false` ise NEDENİ ekrana yazılır; huniyi
   sıfırlarla çizmek "gece hiçbir şey bulunmadı" yalanı olurdu (api.py:1584'ün
   kendi cümlesi: "'Sıfır aday' DEĞİL: ölçülemedi").
   -------------------------------------------------------------------------- */
interface SonDongu {
  readonly var: boolean;
  readonly neden: string | null;
  readonly tarih: string | null;
  readonly yasSaat: number | null;
  readonly aday: number | null;
  readonly plan: number | null;
  readonly silahli: number | null;
  readonly veriTamam: boolean | null;
  readonly durduruldu: boolean | null;
  readonly rejim: string | null;
}

function sonDonguOku(ham: unknown): SonDongu | null {
  const n = nesne(ham);
  if (!n) return null;
  return {
    var: mantik(n["var"]) === true,
    neden: metin(n["neden"]),
    tarih: metin(n["date"]),
    yasSaat: sayi(n["yas_saat"]),
    aday: sayi(n["candidates"]),
    plan: sayi(n["plans"]),
    silahli: sayi(n["armed"]),
    veriTamam: mantik(n["data_ok"]),
    durduruldu: mantik(n["halted"]),
    rejim: metin(n["regime"]),
  };
}

function GeceKarti({ sd }: { sd: SonDongu | null }) {
  if (sd === null) {
    return (
      <OlculemedBlok
        baslik="Son döngü"
        neden="`/api/today` gövdesinde `son_dongu` bloğu YOK — bu uç sürümü o bloğu göndermiyor."
      />
    );
  }
  if (!sd.var) {
    return (
      <OlculemedBlok
        baslik="Son döngü"
        neden={sd.neden ?? "`son_dongu.var` false ama `neden` alanı yazılmamış — nedeni okuyamıyoruz."}
      />
    );
  }

  // HUNİ YALNIZ ÖLÇÜLEN AŞAMALARDAN kurulur; eksik aşama çubuk olarak DEĞİL,
  // altındaki "ölçülemedi" satırı olarak görünür. Sıfır çubuk çizmek, kaydı
  // olmayan bir aşamayı "hiçbiri geçmedi" diye okutur.
  const adaylar: readonly [string, number | null][] = [
    ["Taranan aday", sd.aday],
    ["Kurulan plan", sd.plan],
    ["Silahlanan", sd.silahli],
  ];
  const asamalar: HuniAsamasi[] = [];
  const eksik: string[] = [];
  for (const [ad, n] of adaylar) {
    if (n === null) eksik.push(ad);
    else asamalar.push({ asama: ad, n });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ScanSearch className="size-4 text-muted-foreground" aria-hidden />
          Gece ne buldu
        </CardTitle>
        <CardDescription>
          Günlük döngünün KENDİ kaydı (`events.jsonl` · `daily_cycle`) — kırpılmış sinyal defterinden
          sayılmadı.
        </CardDescription>
        <CardAction className="flex flex-wrap items-center gap-1.5">
          {sd.tarih ? <Badge variant="outline">{kisaTarih(sd.tarih)}</Badge> : null}
          {sd.yasSaat === null ? (
            <Olculemedi kisa neden="döngü kaydının damgası okunamadı — yaş hesaplanamadı (0 saat DEĞİL)" />
          ) : (
            <Badge variant="ghost" className="tabular-nums">
              {sd.yasSaat} sa önce
            </Badge>
          )}
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {asamalar.length > 0 ? (
          <HuniGrafigi asamalar={asamalar} />
        ) : (
          <p className="text-muted-foreground text-sm">
            Döngü kaydı var ama hiçbir aşama sayısı yazılmamış — huni çizilemedi.
          </p>
        )}

        {eksik.length > 0 ? (
          <p className="text-muted-foreground text-xs leading-5">
            Ölçülemeyen aşama: {eksik.join(", ")} — döngü kaydında bu alan yok, sıfır DEĞİL.
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-1.5 border-t pt-3">
          {sd.rejim ? <Badge variant="secondary">rejim · {sd.rejim}</Badge> : null}
          {sd.veriTamam === null ? (
            <Olculemedi kisa neden="döngü kaydında `data_ok` alanı yok" />
          ) : (
            <Badge variant={sd.veriTamam ? "secondary" : "destructive"}>
              veri {sd.veriTamam ? "tamam" : "eksik"}
            </Badge>
          )}
          {sd.durduruldu === true ? <Badge variant="destructive">HALT çekili</Badge> : null}
        </div>
      </CardContent>
    </Card>
  );
}

/* --------------------------------------------------------------------------
   HÜKÜM TAHTASI
   -------------------------------------------------------------------------- */

function Kolon({ hukum, planlar }: { hukum: Hukum; planlar: readonly Plan[] }) {
  return (
    <section className="flex min-h-0 flex-col rounded-xl border bg-muted/50">
      <div className="flex items-start justify-between gap-3 px-4 pt-4 pb-3">
        <div className="min-w-0 space-y-1">
          <h3 className="truncate font-medium text-base leading-none">{HUKUM_BASLIGI[hukum]}</h3>
          <p className="text-muted-foreground text-sm tabular-nums leading-none">
            {planlar.length} plan
          </p>
        </div>
      </div>
      <div className="flex max-h-[34rem] min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-3 pb-3 [scrollbar-color:var(--border)_transparent] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1">
        {planlar.length === 0 ? (
          <p className="rounded-lg border border-dashed px-3 py-6 text-center text-muted-foreground text-xs">
            bu hükümde plan yok
          </p>
        ) : (
          planlar.map((p, i) => <PlanKarti key={p.id ?? `${p.sembol ?? "?"}-${i}`} p={p} />)
        )}
      </div>
    </section>
  );
}

function Tahta({
  planlar,
  ucSayimi,
}: {
  planlar: readonly Plan[];
  ucSayimi: Readonly<Record<string, number>> | null;
}) {
  const kovalar = useMemo(() => {
    const k: Record<Hukum, Plan[]> = { NO_GO: [], REVIEW: [], GO: [], "?": [] };
    for (const p of planlar) k[hukumu(p)].push(p);
    // SKORA GÖRE AZALAN: kolon içi sıra bir karar taşımıyor, ama skorsuz planları
    // sona atmak onları görünmez kılardı — skorsuzlar en sona DEĞİL, kendi
    // aralarında defter sırasında kalıyor.
    for (const h of Object.keys(k) as Hukum[]) {
      k[h].sort((a, b) => (b.skor ?? Number.NEGATIVE_INFINITY) - (a.skor ?? Number.NEGATIVE_INFINITY));
    }
    return k;
  }, [planlar]);

  const gosterilecek: Hukum[] = [...HUKUM_SIRASI];
  if (kovalar["?"].length > 0) gosterilecek.push("?");

  // ÇAPRAZ DENETİM: kendi sayımımız ile ucun `verdict_counts`u.
  const ayrisan: string[] = [];
  if (ucSayimi) {
    for (const h of ["NO_GO", "REVIEW", "GO", "?"] as const) {
      const bizim = kovalar[h].length;
      const onun = ucSayimi[h] ?? 0;
      if (bizim !== onun) ayrisan.push(`${h}: pano ${bizim} · uç ${onun}`);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {ucSayimi === null ? (
        <Alert>
          <AlertTriangle />
          <AlertTitle>Çapraz denetim yapılamadı</AlertTitle>
          <AlertDescription>
            `/api/today` gövdesinde `verdict_counts` alanı yok — kolon sayaçları yalnız panonun kendi
            sayımıdır, ikinci bir kaynakla doğrulanmadı.
          </AlertDescription>
        </Alert>
      ) : ayrisan.length > 0 ? (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertTitle>Sayaçlar ayrışıyor</AlertTitle>
          <AlertDescription>
            Panonun saydığı ile ucun `verdict_counts` sayımı tutmuyor ({ayrisan.join(" · ")}). İkisi de
            aynı `todays_plans` listesine bakmalıydı; ayrışma bir okuma hatasına işaret eder.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3 xl:grid-cols-4">
        {gosterilecek.map((h) => (
          <Kolon key={h} hukum={h} planlar={kovalar[h]} />
        ))}
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------------
   HÜKÜM GEÇMİŞİ — `/api/signals.plans` üstünde seans başına sayım
   -------------------------------------------------------------------------- */

function seanslariSay(planlar: readonly Plan[]): { seanslar: SeansHukmu[]; tarihsiz: number } {
  const kova = new Map<string, { no_go: number; review: number; go: number; belirsiz: number }>();
  let tarihsiz = 0;
  for (const p of planlar) {
    if (!p.tarih) {
      tarihsiz += 1;
      continue;
    }
    const s = kova.get(p.tarih) ?? { no_go: 0, review: 0, go: 0, belirsiz: 0 };
    const h = hukumu(p);
    if (h === "NO_GO") s.no_go += 1;
    else if (h === "REVIEW") s.review += 1;
    else if (h === "GO") s.go += 1;
    else s.belirsiz += 1;
    kova.set(p.tarih, s);
  }
  const seanslar = [...kova.entries()]
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .map(([gun, s]) => ({ gun, ...s }));
  return { seanslar, tarihsiz };
}

/* ========================================================================== */

export function KararZinciri() {
  const bugun = useBugun();
  // NABIZ 60 sn, `/api/today`in 15 sn'si DEĞİL: bu uç 120 aday + 120 plan taşıyor
  // (kırpma tavanı api_signals:1731) ve buradan çizilen tek şey SEANS BAŞINA hüküm
  // dağılımı — gün içinde saniyede değişen bir sayı değil. 15 sn'de çekmek aynı
  // grafiği dört katı yükle yeniden çizerdi.
  const sinyaller = useApi<unknown>("/api/signals", 60_000);

  const ham = nesne(bugun.veri);
  // MEMO ŞART: `planlariOku` her satır için yeni nesne kuruyor. Memosuz her render
  // yeni bir dizi doğururdu ve aşağıdaki `useMemo`ların bağımlılığı her turda
  // değişirdi — yani memo hiç tutmazdı (ölçülmedi ama mekanik kesin).
  const defter = useMemo(() => planlariOku(ham?.["todays_plans"]), [ham]);
  const planlar = useMemo(() => defter?.planlar ?? [], [defter]);
  const planTarihi = metin(ham?.["todays_plan_date"]);
  const ucSayimiHam = nesne(ham?.["verdict_counts"]);
  const ucSayimi = ucSayimiHam
    ? Object.fromEntries(
        Object.entries(ucSayimiHam).flatMap(([k, v]) => {
          const n = sayi(v);
          return n === null ? [] : [[k, n] as const];
        }),
      )
    : null;

  const kapiOzeti = useMemo(() => kapilariOzetle(planlar), [planlar]);

  return (
    <div className="flex flex-col gap-8">
      {/* ---------------------------- ADAYLAR --------------------------- */}
      <section id="bolum-adaylar" className="flex scroll-mt-20 flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h2 className="flex items-center gap-2 font-semibold text-lg tracking-tight">
              <Layers className="size-4 text-muted-foreground" aria-hidden />
              Adaylar
            </h2>
            <p className="text-muted-foreground text-sm">Bu seans hangi planlar kuruldu?</p>
          </div>
          {planTarihi ? (
            <Badge variant="outline" className="tabular-nums">
              plan seansı · {kisaTarih(planTarihi)}
            </Badge>
          ) : null}
        </div>

        <Hal
          d={bugun}
          ad="/api/today"
          iskelet={<Skeleton className="h-40 w-full" />}
          ciz={() => (
            <div className="flex flex-col gap-4">
              <GeceKarti sd={sonDonguOku(ham?.["son_dongu"])} />

              {defter === null ? (
                <OlculemedBlok
                  baslik="Plan tahtası"
                  neden="`/api/today.todays_plans` bir dizi değil — plan defteri okunamadı."
                />
              ) : planTarihi === null ? (
                <OlculemedBlok
                  baslik="Plan tahtası"
                  neden="`todays_plan_date` boş: plan defterinde TARİHLİ satır yok. Bu 'bu seans sıfır aday' DEĞİL — hangi seansın planlarına bakacağımızı ölçemedik."
                />
              ) : (
                <>
                  {defter.okunamayan > 0 ? (
                    <Alert variant="destructive">
                      <AlertTriangle />
                      <AlertTitle>{defter.okunamayan} plan satırı okunamadı</AlertTitle>
                      <AlertDescription>
                        Bu satırlar nesne değildi ve tahtanın DIŞINDA kaldı — kolon sayaçları onları
                        içermiyor.
                      </AlertDescription>
                    </Alert>
                  ) : null}
                  <Tahta planlar={planlar} ucSayimi={ucSayimi} />
                </>
              )}
            </div>
          )}
        />
      </section>

      {/* ---------------------------- KAPILAR --------------------------- */}
      <section id="bolum-kapilar" className="flex scroll-mt-20 flex-col gap-4">
        <div>
          <h2 className="flex items-center gap-2 font-semibold text-lg tracking-tight">
            <Radar className="size-4 text-muted-foreground" aria-hidden />
            Kapılar
          </h2>
          <p className="text-muted-foreground text-sm">Aday hangi kapıda düştü, hangisinden geçti?</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Kapı aşamaları — bu seans</CardTitle>
            <CardDescription>
              `gate_checks` satırlarından sayıldı. Bir kapı YALNIZ onu yazan planlarda değerlendirilir.
            </CardDescription>
            <CardAction>
              <Badge variant="outline" className="tabular-nums">
                {kapiOzeti.satirlar.length} kapı
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent>
            {kapiOzeti.satirlar.length === 0 ? (
              <OlculemedBlok
                baslik="Kapı aşamaları"
                neden={
                  planlar.length === 0
                    ? "bu seansın plan listesi boş — sayılacak kapı satırı yok"
                    : `bu seansın ${planlar.length} planının HİÇBİRİ \`gate_checks\` dizisi taşımıyor — hangi ölçütte takıldıkları YAZILMAMIŞ`
                }
              />
            ) : (
              <KapiTablosu ozet={kapiOzeti} />
            )}
          </CardContent>
        </Card>

        <Hal
          d={sinyaller}
          ad="/api/signals"
          iskelet={<Skeleton className="h-64 w-full" />}
          ciz={(v) => {
            const s = nesne(v);
            const gecmis = planlariOku(s?.["plans"]);
            if (gecmis === null) {
              return (
                <OlculemedBlok
                  baslik="Hüküm geçmişi"
                  neden="`/api/signals.plans` bir dizi değil — seans geçmişi okunamadı."
                />
              );
            }
            const { seanslar, tarihsiz } = seanslariSay(gecmis.planlar);
            const kayit = nesne(s?.["ledger"]);
            const toplam = sayi(kayit?.["plans_total"]);
            const gosterilen = sayi(kayit?.["plans_shown"]);

            return (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="size-4 text-muted-foreground" aria-hidden />
                    Hüküm geçmişi
                  </CardTitle>
                  <CardDescription>
                    Seans başına NO_GO / REVIEW / GO dağılımı — sinyal defterinin gösterilen
                    penceresinden sayıldı.
                  </CardDescription>
                  <CardAction>
                    <Badge variant="outline" className="tabular-nums">
                      {seanslar.length} seans
                    </Badge>
                  </CardAction>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  {seanslar.length === 0 ? (
                    <OlculemedBlok
                      baslik="Hüküm geçmişi"
                      neden="gösterilen plan penceresinde TARİHLİ satır yok — seans ekseni kurulamadı."
                    />
                  ) : (
                    <div className="min-w-0 overflow-x-auto">
                      <HukumGrafigi seanslar={seanslar} />
                    </div>
                  )}

                  <p className="text-muted-foreground text-xs leading-5">
                    {toplam === null || gosterilen === null ? (
                      <>
                        PENCERE: uç `ledger` kırpma beyanını göndermedi — bu grafiğin defterin ne
                        kadarını gördüğü ÖLÇÜLEMEDİ.
                      </>
                    ) : (
                      <>
                        PENCERE: defterdeki {toplam} planın son {gosterilen} tanesi gösteriliyor
                        (`/api/signals` kırpma tavanı). Grafik defterin TAMAMI değildir.
                      </>
                    )}
                    {tarihsiz > 0 ? ` ${tarihsiz} plan tarihsiz olduğu için eksene giremedi.` : ""}
                    {gecmis.okunamayan > 0 ? ` ${gecmis.okunamayan} satır okunamadı.` : ""}
                  </p>
                </CardContent>
              </Card>
            );
          }}
        />
      </section>
    </div>
  );
}
