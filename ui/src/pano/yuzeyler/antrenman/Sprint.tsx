"use client";

/* ============================================================================
   SPRINT — "antrenman koşuyor mu, kaç aday değerlendirildi?"
   ----------------------------------------------------------------------------
   BU KARTIN VAR OLMA NEDENİ TEK BİR AYRIM: "KOŞMUYOR" ile "KOŞTU, ADAY GEÇMEDİ"
   AYNI CÜMLE DEĞİLDİR. Eski panoda ikisi tek satıra sıkışıyordu ve `cleared: 0`
   olan bir sprint "sistem çalışmıyor" diye okunuyordu — oysa makine koşmuş, sekiz
   adayı değerlendirmiş, hiçbiri OOS kapısını geçememişti. Bu iki cümle iki AYRI
   satırda duruyor ve ikisi iki AYRI alandan geliyor:

     ŞU AN    ← `active` (pid sinyalle yoklandı) + `orphan` (ölü pid, terminal
                olmayan faz) + `phase`. Faz HİÇ yoksa sprint hiç koşmamıştır.
     SON KOŞU ← `search.status` / `evaluated` / `cleared` / `shipped` + `note`.

   DÖRDÜNCÜ BİR HÂL DAHA VAR ve gizlenmiyor: YETİM (orphan). Süreç ölmüş ama faz
   donmuş — ilerleme çubuğu "%53" göstermeye devam eder ve o yüzden `active` tek
   başına "koşuyor mu?"yu yanıtlamaz. Uç bunu kendi cümlesiyle söylüyor
   (`orphan_note`) ve o cümle ekranda AYNEN duruyor.

   DEFTERİN KENDİSİ DE ÜÇ DEĞERLİ: `runs_ledger` "var"/"YOK" der ve "YOK" iki farklı
   şey olabilir (hiç satır yazılmadı / defter kum havuzunda). `runs_kaynak` hangisi
   olduğunu söyler; ikisini "son koşu yok" diye tek cümleye katlamak, ölçüm boşluğunu
   olgu gibi göstermek olurdu.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts";
import { Activity, CircleDot, CircleSlash, Pause, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

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
  Satir,
  sayi,
  yas,
} from "../ogrenme/ortak";
import type { HermesGovdesi, SprintDurumu, SprintIzi, SprintKadansi, SprintKosusu } from "../ogrenme/tipler";

/** `sprint.py::_TERMINAL_PHASES` ile AYNI küme. Panoda ikinci bir tanım yazmak
 *  istemezdim ama uç bu kümeyi servis etmiyor; ayrışırsa "yarıda kaldı" hükmü
 *  sessizce değişir, o yüzden kaynağı burada adıyla yazılı. */
const TERMINAL_FAZLAR = new Set(["done", "stopped", "stopping", "error"]);

const KOSU_CONFIG = {
  evaluated: { label: "Değerlendirilen aday", color: "var(--chart-3)" },
  cleared: { label: "Kapıyı geçen aday", color: "var(--chart-2)" },
} satisfies ChartConfig;

type Hal =
  | { kod: "kosuyor"; baslik: string; metin: string }
  | { kod: "yarida"; baslik: string; metin: string }
  | { kod: "bitti"; baslik: string; metin: string }
  | { kod: "hic"; baslik: string; metin: string }
  | { kod: "belirsiz"; baslik: string; metin: string };

/** ŞU AN ne olduğunu ÜÇ alandan türetir; hiçbirini ötekinin yerine kullanmaz. */
function haliCoz(s: SprintDurumu): Hal {
  const faz = typeof s.phase === "string" ? s.phase : null;
  if (s.active === true) {
    return {
      kod: "kosuyor",
      baslik: "Şu an KOŞUYOR",
      metin: `Çocuk süreç canlı (pid ${s.pid ?? "?"}) ve faz "${faz ?? "damgasız"}".`,
    };
  }
  if (s.orphan === true) {
    return {
      kod: "yarida",
      baslik: "YARIDA KALDI (yetim)",
      metin:
        s.orphan_note ??
        `pid ${s.pid ?? "?"} ölü ama faz "${faz ?? "?"}" terminal değil — ilerleme donmuş, "koşuyor" DEĞİL.`,
    };
  }
  if (faz === null) {
    return {
      kod: "hic",
      baslik: "HİÇ KOŞMADI",
      metin:
        "`sprint_status.json` faz damgası taşımıyor — bu kurulumda antrenman sprinti hiç başlatılmamış. Bu bir arıza DEĞİL, bir boşluk.",
    };
  }
  if (TERMINAL_FAZLAR.has(faz)) {
    return {
      kod: "bitti",
      baslik: "Şu an koşmuyor (son koşu bitti)",
      metin: `Faz "${faz}" — süreç düzgün sonlandı. Aşağıdaki "son koşunun hükmü" ayrı bir sorudur: koşmamak ile aday geçirememek aynı şey değildir.`,
    };
  }
  return {
    kod: "belirsiz",
    baslik: "Durum belirsiz",
    metin: `Faz "${faz}" terminal değil ama süreç canlı da değil ve uç yetim damgası basmadı (\`orphan\` ${String(s.orphan)}). "Koşuyor" demek uydurma olurdu.`,
  };
}

const HAL_STILI: Readonly<Record<Hal["kod"], { ikon: typeof Activity; sinif: string }>> = {
  kosuyor: { ikon: CircleDot, sinif: "border-emerald-500/40 bg-emerald-500/5 text-emerald-700 dark:text-emerald-300" },
  yarida: { ikon: TriangleAlert, sinif: "border-amber-500/40 bg-amber-500/5 text-amber-700 dark:text-amber-300" },
  bitti: { ikon: Pause, sinif: "border-border bg-muted/30 text-foreground" },
  hic: { ikon: CircleSlash, sinif: "border-border bg-muted/30 text-muted-foreground" },
  belirsiz: { ikon: TriangleAlert, sinif: "border-amber-500/40 bg-amber-500/5 text-amber-700 dark:text-amber-300" },
};

export function Sprint({ hermes }: { hermes: Durum<HermesGovdesi> }) {
  return (
    <BolumKarti
      kimlik="sprint"
      baslik="Sprint"
      soru="Antrenman koşuyor mu, kaç aday değerlendirildi?"
      ikon={Activity}
    >
      <Kapi durum={hermes} ad="/api/hermes" yukseklik="h-64">
        {(v) =>
          !v.sprint ? (
            <Olculemedi
              neden="Antrenman durumu bu turda hiç ölçülmedi — 'koşmuyor' demek değil"
              teknik="/api/hermes okundu ama `sprint` bloğu YOK"
            />
          ) : (
            <Govde s={v.sprint} kadans={v.learning?.besleme?.antrenman_sprinti ?? null} />
          )
        }
      </Kapi>
    </BolumKarti>
  );
}

function Govde({ s, kadans }: { s: SprintDurumu; kadans: SprintKadansi | null }) {
  const hal = haliCoz(s);
  const stil = HAL_STILI[hal.kod];
  const Ikon = stil.ikon;

  const ilerleme =
    typeof s.progress === "number" && typeof s.total === "number" && s.total > 0
      ? Math.min(100, (s.progress / s.total) * 100)
      : null;

  const arama = s.search;
  const kosular = [...(s.runs ?? [])].reverse(); // uç yeniden eskiye verir; grafik kronolojik
  const noktalar = kosular
    .filter((k): k is SprintKosusu & { ts: string } => typeof k.ts === "string")
    .map((k) => ({
      etiket: k.ts,
      evaluated: typeof k.evaluated === "number" ? k.evaluated : null,
      cleared: typeof k.cleared === "number" ? k.cleared : null,
      durum: k.status ?? "durum yazılmamış",
    }));
  const cizilebilir = noktalar.filter((p) => p.evaluated !== null || p.cleared !== null);

  return (
    <div className="flex flex-col gap-6">
      {/* ---- (1) ŞU AN ---- */}
      <div className={cn("flex items-start gap-3 rounded-lg border p-4", stil.sinif)}>
        <Ikon className="mt-0.5 size-4 shrink-0" aria-hidden />
        <div className="min-w-0">
          <p className="font-medium text-sm">{hal.baslik}</p>
          <p className="mt-0.5 break-words text-xs leading-relaxed opacity-90">{hal.metin}</p>
          {hal.kod === "kosuyor" && ilerleme !== null ? (
            <div className="mt-3 flex flex-col gap-1.5">
              <div className="flex items-baseline justify-between text-xs">
                <span>ilerleme</span>
                <span className="tabular-nums">
                  {sayi(s.progress, 0)} / {sayi(s.total, 0)}
                </span>
              </div>
              <Progress value={ilerleme} className="h-1.5" />
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col">
          <Satir etiket="Sprint kimliği (sid)">
            <Deger
              metin={s.sid ?? null}
              neden="Henüz hiç sprint başlatılmamış"
              teknik="`sid` yok"
              className="text-xs"
            />
          </Satir>
          <Satir etiket="Başlangıç">
            <Deger
              metin={(() => {
                const y = yas(s.started_at);
                const a = anMetni(s.started_at);
                return y === null ? null : a === null ? y.metin : `${y.metin} · ${a}`;
              })()}
              neden="Sprint henüz hiç başlamamış"
              teknik="`started_at` damgası yok"
              className="text-xs"
            />
          </Satir>
          <Satir etiket="Son güncelleme">
            <Deger
              metin={(() => {
                const y = yas(s.updated);
                return y === null ? null : y.metin;
              })()}
              neden="Durum kaydı hiç kaydedilmemiş"
              teknik="`updated` damgası yok — durum dosyası"
              className="text-xs"
            />
          </Satir>
          <Satir etiket="Faz">
            <Deger
              metin={s.phase ?? null}
              neden="Sprint henüz hiç koşmamış"
              teknik="`phase` yok"
              className="text-xs"
            />
          </Satir>
        </div>
        <div className="flex flex-col">
          <Satir etiket="Kum havuzu değerlendirme başlangıcı">
            <Deger
              metin={s.eval_start ?? null}
              neden="Değerlendirme penceresinin başlangıcı bildirilmedi"
              teknik="`eval_start` yok — pencere ölçülemedi"
              className="text-xs"
            />
          </Satir>
          <Satir etiket="Ayrım tarihi (cutoff)">
            <Deger
              metin={s.cutoff ?? null}
              neden="Seçim ve onay pencerelerini ayıran tarih bildirilmedi"
              teknik="`cutoff` yok"
              className="text-xs"
            />
          </Satir>
          <Satir etiket="v1 taban işlemi">
            <Deger
              metin={sayi(s.n_v1, 0)}
              neden="Taban sürümün işlem sayısı ölçülmemiş"
              teknik="`n_v1` yok — ileri taban"
            />
          </Satir>
          <Satir etiket="Aday sürüm (v2) işlemi">
            <Deger
              metin={s.v2 === null || s.v2 === undefined ? null : `v${s.v2} · ${sayi(s.n_v2, 0) ?? "?"} işlem`}
              neden="Aday sürüm hiç kurulmadı — hiçbir aday elemeyi geçemedi; bu bir arıza değil, bir sonuç"
              teknik="`v2`/`n_v2` yok — arama kapıdan aday geçiremedi"
              className="text-xs"
            />
          </Satir>
        </div>
      </div>

      {/* ---- (2) SON KOŞUNUN HÜKMÜ ---- */}
      <Kutu
        baslik="Son koşunun hükmü"
        aciklama="Bu satır 'koşuyor mu?' sorusundan AYRIDIR: makine koşup hiçbir adayı geçirememiş olabilir."
      >
        {!arama ? (
          <Olculemedi
            neden="Son koşu arama aşamasına hiç ulaşmamış olabilir"
            teknik="`sprint.search` yok — Faz A min_sample'a takılırsa arama hiç başlamaz"
          />
        ) : (
          <>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">durum: {arama.status ?? "ölçülemedi"}</Badge>
              <Badge variant="outline">
                değerlendirilen: {sayi(arama.evaluated, 0) ?? "ölçülemedi"}
              </Badge>
              <Badge
                variant="outline"
                className={
                  arama.cleared === 0
                    ? "border-amber-500/40 text-amber-700 dark:text-amber-300"
                    : typeof arama.cleared === "number"
                      ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
                      : ""
                }
              >
                kapıyı geçen: {sayi(arama.cleared, 0) ?? "ölçülemedi"}
              </Badge>
              <Badge variant="outline">
                yayına alındı mı: {s.shipped === true ? "evet" : s.shipped === false ? "hayır" : "ölçülemedi"}
              </Badge>
              <Badge variant="outline">
                döngü kapandı mı: {s.loop_closed === true ? "evet" : s.loop_closed === false ? "hayır" : "ölçülemedi"}
              </Badge>
            </div>
            {arama.cleared === 0 ? (
              <Beyan>
                Sıfır aday geçti — ama arama KOŞTU ({sayi(arama.evaluated, 0) ?? "?"} aday denendi). "Koşmuyor"
                ile "koştu, aday geçmedi" aynı şey değildir; bu satır ikincisini söylüyor.
              </Beyan>
            ) : null}
            <div className="flex flex-col">
              <Satir etiket="Yürürlükteki sürümün OOS skoru">
                <Deger
                  metin={sayi(arama.incumbent_oos, 4)}
                  neden="Yürürlükteki sürümün skoru ölçülemedi — kıyas tabanı yok"
                  teknik="`incumbent_oos` yok"
                />
              </Satir>
              {arama.best ? (
                <Satir etiket="En iyi aday">
                  <span className="text-xs">
                    {arama.best.variable ?? "?"}: {String(arama.best.old ?? "?")} → {String(arama.best.new ?? "?")} ·
                    OOS {sayi(arama.best.candidate_oos, 4) ?? "ölçülemedi"}
                  </span>
                </Satir>
              ) : (
                <Satir etiket="En iyi aday">
                  <OlculemediHucre
                    neden="Hiçbir aday en iyi olarak kaydedilmemiş"
                    teknik="`search.best` null"
                  />
                </Satir>
              )}
            </div>
            {s.note ? <Beyan>{s.note}</Beyan> : null}
            {s.error ? <Beyan>Hata damgası: {s.error}</Beyan> : null}
            <IzTablosu iz={arama.trace ?? []} evaluated={arama.evaluated ?? null} />
          </>
        )}
      </Kutu>

      {/* ---- (3) KOŞU TARİHÇESİ ---- */}
      <Kutu
        baslik="Koşu tarihçesi — değerlendirilen / geçen aday"
        aciklama="Kaynak kum havuzu defterleri (`sprint_runs.jsonl`). Çocuk süreç canlı state'e YAZMAZ; okuyucu havuzları gezer."
      >
        {cizilebilir.length === 0 ? (
          <Olculemedi
            neden={
              s.runs_note ??
              (s.runs_ledger === "YOK"
                ? "Hiçbir kum havuzunda koşu kaydı yok — sprint arama aşamasına hiç ulaşmamış olabilir"
                : "Koşu geçmişi okundu ama hiçbir satırda sayı yok — grafik çizilemedi")
            }
            teknik={
              s.runs_ledger === "YOK"
                ? "hiçbir kum havuzunda `sprint_runs.jsonl` yok"
                : "hiçbir satır `evaluated`/`cleared` taşımıyor"
            }
          />
        ) : (
          <>
            <ChartContainer config={KOSU_CONFIG} className="aspect-auto h-56 w-full">
              <BarChart data={cizilebilir} margin={{ bottom: 0, left: 0, right: 8, top: 16 }}>
                <CartesianGrid vertical={false} />
                <XAxis axisLine={false} dataKey="etiket" tickLine={false} tickMargin={10} />
                <YAxis axisLine={false} tickLine={false} tickMargin={8} width={40} allowDecimals={false} />
                <ChartTooltip
                  cursor={false}
                  content={
                    <ChartTooltipContent
                      className="w-60"
                      labelFormatter={(etiket, yuk) => {
                        const ilk = Array.isArray(yuk) ? yuk[0] : undefined;
                        const p = (ilk as { payload?: { durum: string } } | undefined)?.payload;
                        return `${String(etiket)}${p ? ` · ${p.durum}` : ""}`;
                      }}
                    />
                  }
                />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar isAnimationActive={false} dataKey="evaluated" fill="var(--color-evaluated)" fillOpacity={0.55} radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="evaluated" position="top" className="fill-muted-foreground" fontSize={10} />
                </Bar>
                <Bar isAnimationActive={false} dataKey="cleared" fill="var(--color-cleared)" fillOpacity={0.9} radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="cleared" position="top" className="fill-muted-foreground" fontSize={10} />
                </Bar>
              </BarChart>
            </ChartContainer>

            <div className="overflow-x-auto">
              <Table className="min-w-[38rem]">
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="h-9">Tarih</TableHead>
                    <TableHead className="h-9">Sonuç</TableHead>
                    <TableHead className="h-9 text-right">Değerlendirilen</TableHead>
                    <TableHead className="h-9 text-right">Geçen</TableHead>
                    <TableHead className="h-9 text-right">Taban OOS</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...kosular].reverse().map((k, i) => (
                    <TableRow key={`${k.sid ?? k.ts ?? i}`} className="border-border/50">
                      <TableCell className="py-2.5 font-medium tabular-nums">{k.ts ?? "damgasız"}</TableCell>
                      <TableCell className="py-2.5 text-xs">{k.status ?? "—"}</TableCell>
                      <TableCell className="py-2.5 text-right tabular-nums">
                        <Deger
                          metin={sayi(k.evaluated, 0)}
                          neden="Bu koşuda değerlendirilen aday sayısı kaydedilmemiş"
                          teknik="`evaluated` yok"
                        />
                      </TableCell>
                      <TableCell className="py-2.5 text-right tabular-nums">
                        <Deger
                          metin={sayi(k.cleared, 0)}
                          neden="Bu koşuda geçen aday sayısı kaydedilmemiş"
                          teknik="`cleared` yok"
                        />
                      </TableCell>
                      <TableCell className="py-2.5 text-right tabular-nums">
                        <Deger
                          metin={sayi(k.incumbent_oos, 4)}
                          neden="Bu koşuda taban skoru kaydedilmemiş"
                          teknik="`incumbent_oos` yok — taban OOS"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </>
        )}
        <Beyan>
          Defter: {s.runs_ledger ?? "beyan edilmedi"}
          {s.runs_kaynak ? ` · kaynak ${s.runs_kaynak}` : " · kaynak beyan edilmedi"} · gösterilen{" "}
          {kosular.length} koşu (uç en çok 5 satır taşır — bu bir tavan, defterin boyu DEĞİL).
        </Beyan>
      </Kutu>

      {/* ---- (4) KADANS: SIRADA NE VAR ---- */}
      <Kutu baslik="Kadans — bir sonraki sprint ne zaman?" aciklama="`sprint.should_run()` her cevabın yanına SEBEBİNİ yazar.">
        {!kadans ? (
          <Olculemedi
            neden="Otomatik döngünün kararı bu turda ölçülemedi"
            teknik="`learning.besleme.antrenman_sprinti` yükte yok"
          />
        ) : (
          <div className="flex flex-col">
            <Satir etiket="Şimdi koşmalı mı?">
              <Badge
                variant="outline"
                className={
                  kadans.kos === true
                    ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
                    : kadans.kos === false
                      ? "text-muted-foreground"
                      : ""
                }
              >
                {kadans.kos === undefined ? "ölçülemedi" : kadans.kos ? "evet" : "hayır"}
              </Badge>
            </Satir>
            <Satir etiket="Sebep">
              <Deger
                metin={kadans.sebep ?? null}
                neden="Otomatik döngü kararının gerekçesini kaydetmemiş"
                teknik="kadans sebep yazmadı — 'arıza mı, disiplin mi' ayırt edilemez"
                className="text-xs"
              />
            </Satir>
            <Satir etiket="Son sprintten geçen gün">
              <Deger
                metin={sayi(kadans.gecen_gun, 0)}
                neden="Henüz hiç sprint koşmamış — 'sıfır gün' demek değil"
                teknik="`gecen_gun` null"
              />
            </Satir>
            <Satir etiket="Sprint sonrası taze hipotez">
              <Deger
                metin={sayi(kadans.taze_hipotez, 0)}
                neden="Sprint sonrası taze hipotez sayısı ölçülemedi"
                teknik="`taze_hipotez` ölçülemedi"
              />
            </Satir>
            <Satir etiket="Tetik eşikleri">
              <span className="text-xs">
                haftalık {sayi(kadans.tetik?.haftalik_gun, 0) ?? "?"} gün · taze hipotez ≥{" "}
                {sayi(kadans.tetik?.taze_hipotez_esigi, 0) ?? "?"} · gece dilimi{" "}
                {kadans.tetik?.gece_dilimi?.join("–") ?? "?"}
              </span>
            </Satir>
          </div>
        )}
      </Kutu>
    </div>
  );
}

/* ---- ARAMA İZİ ----------------------------------------------------------- */

function IzTablosu({ iz, evaluated }: { iz: readonly SprintIzi[]; evaluated: number | null }) {
  if (iz.length === 0) {
    return (
      <Olculemedi
        neden="Hangi adayın neden elendiği bu koşuda kaydedilmemiş — gerekçe olmadan sprint bir şey öğretmez"
        teknik="`search.trace` boş"
      />
    );
  }
  const disarida = evaluated === null ? null : Math.max(0, evaluated - iz.length);
  return (
    <div className="flex flex-col gap-2">
      <p className="font-medium text-sm">Arama izi</p>
      <div className="overflow-x-auto">
        <Table className="min-w-[44rem]">
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-9">Değişken</TableHead>
              <TableHead className="h-9">Deneme</TableHead>
              <TableHead className="h-9 text-right">Aday OOS</TableHead>
              <TableHead className="h-9 text-right">Kat galibiyeti</TableHead>
              <TableHead className="h-9">Hüküm</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {iz.map((t, i) => (
              <TableRow key={`${t.variable ?? i}-${i}`} className="border-border/50">
                <TableCell className="py-2.5 font-medium text-xs">{t.variable ?? "—"}</TableCell>
                <TableCell className="py-2.5 text-muted-foreground text-xs tabular-nums">
                  {String(t.old ?? "?")} → {String(t.new ?? "?")}
                </TableCell>
                <TableCell className="py-2.5 text-right tabular-nums">
                  <Deger
                    metin={sayi(t.candidate_oos, 4)}
                    neden="Bu denemede aday skoru kaydedilmemiş"
                    teknik="`candidate_oos` yok — aday OOS"
                  />
                </TableCell>
                <TableCell className="py-2.5 text-right text-xs tabular-nums">{t.fold_wins ?? "—"}</TableCell>
                <TableCell className="py-2.5">
                  {t.passes ? (
                    <Badge variant="outline" className="border-emerald-500/40 text-emerald-700 dark:text-emerald-300">
                      kapıyı geçti
                    </Badge>
                  ) : (
                    <div className="flex flex-col gap-0.5">
                      <Badge variant="outline" className="w-fit text-muted-foreground">
                        reddedildi
                      </Badge>
                      {t.why ? <span className="text-muted-foreground text-xs leading-snug">{t.why}</span> : null}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {disarida !== null && disarida > 0 ? (
        <Beyan>
          {disarida} deneme bu izin DIŞINDA kaldı: durum dosyası bir okuma-modelidir ve izi kırpar
          (geçenlerden en çok 6, reddedilenlerden en çok 4 satır). Kırpılan denemeler yok sayılmadı —
          `evaluated` ile iz uzunluğunun farkı burada.
        </Beyan>
      ) : null}
    </div>
  );
}
