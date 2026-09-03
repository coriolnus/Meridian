"use client";

/* ============================================================================
   STRATEJİ SÜRÜMLERİ — "v1'den bugüne ne değişti, neyi bozdu?"
   ----------------------------------------------------------------------------
   TOPLAM SKOR BİR ŞEYİ GİZLER: bir sürüm ortalamayı yükseltirken belli bir rejimi
   bozmuş olabilir. Bu yüzden burada üç ayrı okuma yan yana duruyor ve hiçbiri
   ötekinin yerine geçmiyor:
     (1) SÜRÜM ÇİZELGESİ  — hangi sürüm ne zaman yayına girdi, kimden türedi, geri
                            alındı mı (kaynak: `/api/agent.rollback`).
     (2) REGRESYON        — sürüm × ortalama R, ve ardışık iki sürüm arasında
                            REJİM BAŞINA delta (kaynak: `/api/agent.regresyon`).
     (3) KALİBRASYON      — tahmin ↔ gerçekleşen saçılımı (kaynak:
                            `/api/agent.calibration_scatter`).

   "AZ ÖRNEK" BİR HÜKÜM DEĞİL UYARIDIR ve uçtan gelir (`az_ornek`, eşik `az_ornek_esigi`).
   Panoda kendi eşiğimi yazsaydım — CLAUDE.md §3'ün yasakladığı şey — sunucununkiyle
   sessizce ayrışırdı. Eşik ekranda uçtan geldiği hâliyle yazılı.

   SAÇILIMDA ÇEYREKLER: x=0 ve y=0 çizgileri, tahminin YÖNÜNÜN tutup tutmadığını
   gösterir (aynı işaretli çeyrekler = yön tuttu). İSABET ORANI BURADA HESAPLANMAZ —
   `calibration.hit_rate` sunucuda ölçülüyor ve kartın üstünde aynen yazılı; ikinci
   bir hesap iki farklı isabet oranı üretirdi.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceLine, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";
import { Cpu } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
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
  pnlRengi,
  Satir,
  sayi,
  yuzde,
} from "./ortak";
import type { AjanGovdesi, RegresyonSurumu, SurumSatiri } from "./tipler";

const SURUM_CONFIG = {
  avg_r: { label: "Ortalama R", color: "var(--chart-2)" },
} satisfies ChartConfig;

const SACILIM_CONFIG = {
  nokta: { label: "Hipotez", color: "var(--chart-1)" },
} satisfies ChartConfig;

export function Surumler({ ajan }: { ajan: Durum<AjanGovdesi> }) {
  return (
    <BolumKarti kimlik="ajan" baslik="Strateji sürümleri" soru="v01'den bugüne ne değişti?" ikon={Cpu}>
      <Kapi durum={ajan} ad="/api/agent" yukseklik="h-72">
        {(v) => (
          <div className="flex flex-col gap-6">
            <Cizelge ajan={v} />
            <Regresyon ajan={v} />
            <Sacilim ajan={v} />
          </div>
        )}
      </Kapi>
    </BolumKarti>
  );
}

/* ---- (1) SÜRÜM ÇİZELGESİ ------------------------------------------------- */

function Cizelge({ ajan }: { ajan: AjanGovdesi }) {
  const r = ajan.rollback;
  if (!r) {
    return (
      <Kutu baslik="Sürüm çizelgesi">
        <Olculemedi
          neden="Sürüm geçmişi bu turda hiç derlenmedi"
          teknik="/api/agent yükünde `rollback` bloğu YOK"
        />
      </Kutu>
    );
  }
  if (r.var === false) {
    return (
      <Kutu baslik="Sürüm çizelgesi">
        <Olculemedi neden={r.neden} />
      </Kutu>
    );
  }
  const surumler: readonly SurumSatiri[] = r.surumler ?? [];

  return (
    <Kutu
      baslik="Sürüm çizelgesi"
      aciklama="Kaynak scoreboard.json. Bir sürümün 'geri alındı' olması bir başarısızlık değil, döngünün BİR KEZ kapandığının kanıtıdır."
    >
      <div className="flex flex-wrap gap-2">
        <Badge variant="outline">
          yayında: {r.current_version === null || r.current_version === undefined ? "ölçülemedi" : `v${r.current_version}`}
        </Badge>
        <Badge variant="outline">geri alınan: {sayi(r.geri_alinan_n, 0) ?? "ölçülemedi"}</Badge>
        <Badge variant="outline">olay penceresi: {sayi(r.olay_penceresi, 0) ?? "ölçülemedi"} satır</Badge>
      </div>

      {surumler.length === 0 ? (
        <Olculemedi
          neden="Tek bir sürüm kaydı bile yok"
          teknik="`rollback.surumler` boş — karne dosyasında kayıt yok"
        />
      ) : (
        <div className="overflow-x-auto">
          <Table className="min-w-[58rem]">
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="h-9">Sürüm</TableHead>
                <TableHead className="h-9">Ebeveyn</TableHead>
                <TableHead className="h-9">Kaynak</TableHead>
                <TableHead className="h-9">Yayına giriş</TableHead>
                <TableHead className="h-9 text-right">İşlem</TableHead>
                <TableHead className="h-9 text-right">Canlı skor</TableHead>
                <TableHead className="h-9 text-right">Backtest OOS</TableHead>
                <TableHead className="h-9">Durum</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {surumler.map((s, i) => (
                // ANAHTAR SÜRÜM ADINDAN, YOKSA SIRADAN: rastgele anahtar her tazelemede
                // satırı yeniden doğururdu (odak ve seçim kaybı) — deterministik olmalı.
                <TableRow key={s.version ?? `sirasiz-${i}`} className={cn("border-border/50", s.guncel && "bg-primary/5")}>
                  <TableCell className="py-2.5 font-medium">
                    v{s.version ?? "?"}
                    {s.guncel ? (
                      <Badge variant="outline" className="ml-2 border-primary/40 text-primary">
                        yayında
                      </Badge>
                    ) : null}
                  </TableCell>
                  <TableCell className="py-2.5 text-muted-foreground tabular-nums">
                    {s.parent === null || s.parent === undefined ? (
                      <OlculemediHucre
                        neden="Bu sürümün hangi sürümden türediği kaydedilmemiş"
                        teknik="`parent` yok — ilk sürüm (v1 tabanı) için normaldir, ama kayıttan ayırt edilemez"
                      />
                    ) : (
                      `v${s.parent}`
                    )}
                  </TableCell>
                  <TableCell className="py-2.5 text-xs">
                    <Deger
                      metin={s.source ?? null}
                      neden="Bu sürümün nasıl doğduğu kaydedilmemiş"
                      teknik="`source` yazılmamış"
                    />
                  </TableCell>
                  <TableCell className="py-2.5 text-xs">
                    <Deger
                      metin={anMetni(s.live_since)}
                      neden="Yayına giriş anı kaydedilmemiş"
                      teknik="`live_since` damgası yok"
                    />
                  </TableCell>
                  <TableCell className="py-2.5 text-right tabular-nums">
                    <Deger
                      metin={sayi(s.n_trades, 0)}
                      neden="Bu sürümde kaç işlem kapandığı bildirilmedi"
                      teknik="`n_trades` yazılmamış"
                    />
                  </TableCell>
                  <TableCell className="py-2.5 text-right tabular-nums">
                    <Deger
                      metin={sayi(s.live_score, 4)}
                      neden="Sürümün canlı skoru ölçülemedi — sıfır değil"
                      teknik="`live_score` yazılmamış"
                    />
                  </TableCell>
                  <TableCell className="py-2.5 text-right tabular-nums">
                    <Deger
                      metin={sayi(s.backtest_oos, 4)}
                      neden="Geçmiş veri sınavının skoru bu kayıtta yok"
                      teknik="`backtest_oos` yazılmamış — kapı skoru"
                    />
                  </TableCell>
                  <TableCell className="py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {s.rolled_back ? (
                        <Badge variant="outline" className="border-uyari-h text-uyari">
                          geri alındı
                        </Badge>
                      ) : null}
                      {s.reinstated ? (
                        <Badge variant="outline" className="border-emerald-500/40 text-emerald-700 dark:text-emerald-300">
                          yeniden yürürlükte
                        </Badge>
                      ) : null}
                      {s.baseline_verdict ? <Badge variant="outline">{s.baseline_verdict}</Badge> : null}
                      {!s.rolled_back && !s.reinstated && !s.baseline_verdict ? (
                        <span className="text-muted-foreground text-xs">—</span>
                      ) : null}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="flex flex-col">
        <Satir etiket="Açık öğrenme döngüsü">
          {r.acik_dongu === null || r.acik_dongu === undefined ? (
            <OlculemediHucre
              neden={r.acik_dongu_neden ?? "Açık döngü kaydı okunamadı ve nedeni bildirilmedi"}
              teknik="`acik_dongu` okunamadı"
            />
          ) : Object.keys(r.acik_dongu).length === 0 ? (
            <span className="text-xs">yok (boş sözlük = açık döngü YOK)</span>
          ) : (
            <span className="text-xs">{Object.keys(r.acik_dongu).length} alanlı açık döngü kaydı var</span>
          )}
        </Satir>
      </div>

      {(r.olaylar ?? []).length > 0 ? (
        <div className="flex flex-col gap-1.5">
          <p className="font-medium text-xs">Geri-alma / döngü olayları (en yeni önce)</p>
          <ul className="flex flex-col gap-1">
            {(r.olaylar ?? []).slice(0, 8).map((o, i) => (
              <li key={`${o.ts ?? i}-${i}`} className="flex flex-wrap gap-x-2 text-muted-foreground text-xs">
                <span className="tabular-nums">{anMetni(o.ts) ?? "damgasız"}</span>
                <code className="rounded bg-muted px-1">{o.event ?? "?"}</code>
                {o.version === null || o.version === undefined ? null : <span>v{String(o.version)}</span>}
                {typeof o.reason === "string" ? <span className="min-w-0 break-words">— {o.reason}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <Beyan>
          Olay penceresinde geri-alma/döngü kaydı yok. Bu, "hiç geri alma olmadı" DEĞİL: pencere son{" "}
          {sayi(r.olay_penceresi, 0) ?? "?"} olayı tarıyor ve daha eskisi bu pencerede görünmez.
        </Beyan>
      )}
    </Kutu>
  );
}

/* ---- (2) REGRESYON ------------------------------------------------------- */

interface SurumNoktasi {
  readonly surum: string;
  readonly avg_r: number;
  readonly n: number;
  readonly az: boolean;
}

function Regresyon({ ajan }: { ajan: AjanGovdesi }) {
  const g = ajan.regresyon;
  if (!g) {
    return (
      <Kutu baslik="Regresyon — neyi düzeltti, neyi bozdu">
        <Olculemedi
          neden="Sürümler arası karşılaştırma bu turda hiç hesaplanmadı"
          teknik="/api/agent yükünde `regresyon` bloğu YOK"
        />
      </Kutu>
    );
  }
  if (g.var === false) {
    return (
      <Kutu baslik="Regresyon — neyi düzeltti, neyi bozdu">
        <Olculemedi neden={g.neden} />
      </Kutu>
    );
  }

  const surumler: readonly RegresyonSurumu[] = g.surumler ?? [];
  const noktalar: SurumNoktasi[] = surumler
    .filter((s): s is RegresyonSurumu & { version: string; avg_r: number } =>
      typeof s.version === "string" && typeof s.avg_r === "number" && Number.isFinite(s.avg_r))
    .map((s) => ({ surum: `v${s.version}`, avg_r: s.avg_r, n: s.n ?? 0, az: s.az_ornek === true }))
    .reverse(); // uç yeniden eskiye sıralı; grafik kronolojik okunmalı

  const olculemeyen = surumler.length - noktalar.length;
  const fark = g.fark;

  return (
    <Kutu
      baslik="Regresyon — neyi düzeltti, neyi bozdu"
      aciklama={`Yalnız \`strategy_version\` damgalı kapanmış işlemlerden türer. Görünürlük çizgisi: n < ${sayi(g.az_ornek_esigi, 0) ?? "?"} → "az örnek".`}
    >
      {noktalar.length === 0 ? (
        <Olculemedi
          neden={`${surumler.length} sürüm var ama hiçbirinin ortalama getirisi ölçülemedi`}
          teknik="hiçbir dilimde `avg_r` sayı değil"
        />
      ) : (
        <ChartContainer config={SURUM_CONFIG} className="aspect-auto h-52 w-full">
          <BarChart data={noktalar} margin={{ bottom: 0, left: 0, right: 8, top: 16 }}>
            <CartesianGrid vertical={false} />
            <XAxis axisLine={false} dataKey="surum" tickLine={false} tickMargin={10} />
            <YAxis axisLine={false} tickLine={false} tickMargin={8} width={52} tickFormatter={(v) => sayi(v, 2) ?? ""} />
            <ReferenceLine y={0} stroke="var(--border)" />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  className="w-56"
                  labelFormatter={(_e, yuk) => {
                    const ilk = Array.isArray(yuk) ? yuk[0] : undefined;
                    const p = (ilk as { payload?: SurumNoktasi } | undefined)?.payload;
                    return p ? `${p.surum} · ${p.n} işlem${p.az ? " · AZ ÖRNEK" : ""}` : "sürüm okunamadı";
                  }}
                  formatter={(deger) => (
                    <span className="text-muted-foreground">
                      ortalama R{" "}
                      <span className="ml-1 font-medium text-foreground tabular-nums">{sayi(deger, 3) ?? "—"}</span>
                    </span>
                  )}
                />
              }
            />
            <Bar isAnimationActive={false} dataKey="avg_r" radius={[4, 4, 0, 0]}>
              <LabelList
                dataKey="avg_r"
                position="top"
                className="fill-muted-foreground"
                fontSize={10}
                formatter={(v: unknown) => sayi(v, 2) ?? ""}
              />
              {noktalar.map((p) => (
                <Cell
                  key={p.surum}
                  fill={p.avg_r >= 0 ? "var(--chart-2)" : "var(--destructive)"}
                  // AZ ÖRNEKLİ DİLİM SOLUK ÇİZİLİR: aynı yükseklikteki iki çubuktan
                  // birinin arkasında 4, ötekinde 100 işlem olabilir; renk yoğunluğu
                  // bu farkı grafiğin kendisinde taşır (tooltip'e bırakmak yetmez).
                  fillOpacity={p.az ? 0.4 : 0.9}
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      )}
      {olculemeyen > 0 ? (
        <Beyan>
          {olculemeyen} sürüm dilimi grafikte YOK: ortalama R'leri ölçülemedi (0 olarak çizmek onları
          "nötr sürüm" gibi gösterirdi).
        </Beyan>
      ) : null}

      {/* ---- DÜZELTTİ / BOZDU ---- */}
      {!fark ? (
        <Olculemedi
          neden="Karşılaştırma için en az iki sürüm gerekiyor — tek sürümde 'neyi bozdu' sorusunun karşılaştırma tarafı yok"
          teknik="`regresyon.fark` null"
        />
      ) : (
        <div className="flex flex-col gap-2">
          <p className="font-medium text-sm">
            v{fark.eski ?? "?"} → v{fark.yeni ?? "?"} · rejim başına delta
          </p>
          <div className="overflow-x-auto">
            <Table className="min-w-[34rem]">
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="h-9">Rejim</TableHead>
                  <TableHead className="h-9 text-right">Δ ortalama R</TableHead>
                  <TableHead className="h-9 text-right">n (yeni / eski)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(fark.rejim ?? []).map((d, i) => (
                  <TableRow key={`${d.ad ?? i}`} className="border-border/50">
                    <TableCell className="py-2.5 font-medium">
                      {d.ad ?? "—"}
                      {d.az_ornek ? (
                        <Badge variant="outline" className="ml-2 text-muted-foreground">
                          az örnek
                        </Badge>
                      ) : null}
                    </TableCell>
                    <TableCell className={cn("py-2.5 text-right tabular-nums", pnlRengi(d.delta_r))}>
                      <Deger
                        metin={sayi(d.delta_r, 3, true)}
                        neden={d.neden ?? "Fark ölçülemedi — iki sürümden birinin ortalama getirisi yok"}
                        teknik="iki dilimden biri `avg_r` taşımıyor"
                      />
                    </TableCell>
                    <TableCell className="py-2.5 text-right text-muted-foreground tabular-nums">
                      {d.n_yeni === undefined || d.n_eski === undefined ? (
                        <OlculemediHucre
                          neden="Karşılaştırılacak iki sürümden biri eksik"
                          teknik="`n_yeni` / `n_eski` alanlarından biri yok"
                        />
                      ) : (
                        `${d.n_yeni} / ${d.n_eski}`
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
      {g.sinir ? <Beyan>{g.sinir}</Beyan> : null}
    </Kutu>
  );
}

/* ---- (3) KALİBRASYON SAÇILIMI -------------------------------------------- */

interface SacilimNoktasi {
  readonly x: number;
  readonly y: number;
  readonly degisken: string;
  readonly durum: string;
}

function Sacilim({ ajan }: { ajan: AjanGovdesi }) {
  const ham = ajan.calibration_scatter ?? [];
  const cal = ajan.calibration;
  const noktalar: SacilimNoktasi[] = ham
    .filter(
      (p): p is { predicted: number; realized: number; variable?: string | null; status?: string | null } =>
        typeof p.predicted === "number" &&
        Number.isFinite(p.predicted) &&
        typeof p.realized === "number" &&
        Number.isFinite(p.realized),
    )
    .map((p) => ({
      x: p.predicted,
      y: p.realized,
      degisken: p.variable ?? "değişken yazılmamış",
      durum: p.status ?? "durum yazılmamış",
    }));

  return (
    <Kutu
      baslik="Kalibrasyon — tahmin ↔ gerçekleşen"
      aciklama="Yalnız `realized_delta`sı YAZILMIŞ hipotezler girer; sonucu beklenen hipotez saçılımda YOKTUR."
    >
      <div className="flex flex-wrap gap-2">
        <Badge variant="outline">çift: {sayi(cal?.n, 0) ?? "ölçülemedi"}</Badge>
        <Badge variant="outline">
          Brier: {cal?.brier === null || cal?.brier === undefined ? "ölçülemedi" : (sayi(cal.brier, 3) ?? "ölçülemedi")}
        </Badge>
        <Badge variant="outline">
          isabet:{" "}
          {cal?.hit_rate === null || cal?.hit_rate === undefined ? "ölçülemedi" : (yuzde(cal.hit_rate, 0) ?? "ölçülemedi")}
        </Badge>
      </div>
      {cal?.note ? <Beyan>{cal.note}</Beyan> : null}

      {noktalar.length === 0 ? (
        <Olculemedi
          neden={`Çizilecek nokta yok: ${ham.length} kaydın hiçbirinde tahmin ile gerçekleşen birlikte yok — döngü henüz kapanmamış olabilir`}
          teknik="hiçbir kayıtta hem `predicted` hem `realized` sayı değil"
        />
      ) : (
        <ChartContainer config={SACILIM_CONFIG} className="aspect-auto h-64 w-full">
          <ScatterChart margin={{ bottom: 8, left: 0, right: 12, top: 12 }}>
            <CartesianGrid />
            <XAxis
              type="number"
              dataKey="x"
              name="tahmin"
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => sayi(v, 2) ?? ""}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="gerçekleşen"
              axisLine={false}
              tickLine={false}
              width={56}
              tickFormatter={(v) => sayi(v, 2) ?? ""}
            />
            <ZAxis range={[70, 70]} />
            <ReferenceLine x={0} stroke="var(--border)" />
            <ReferenceLine y={0} stroke="var(--border)" />
            <ChartTooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={
                <ChartTooltipContent
                  className="w-64"
                  hideLabel
                  formatter={(_d, _ad, yuk) => {
                    const p = (yuk as { payload?: SacilimNoktasi } | undefined)?.payload;
                    if (!p) return <span className="text-muted-foreground">nokta okunamadı</span>;
                    return (
                      <span className="flex flex-col gap-0.5">
                        <span className="font-medium">{p.degisken}</span>
                        <span className="text-muted-foreground tabular-nums">
                          tahmin {sayi(p.x, 4)} → gerçekleşen {sayi(p.y, 4)}
                        </span>
                        <span className="text-muted-foreground text-xs">durum: {p.durum}</span>
                      </span>
                    );
                  }}
                />
              }
            />
            <Scatter data={noktalar} fill="var(--color-nokta)" fillOpacity={0.85} />
          </ScatterChart>
        </ChartContainer>
      )}
      <Beyan>
        Aynı işaretli çeyrekler (sağ-üst, sol-alt) tahminin YÖNÜNÜN tuttuğu hipotezlerdir. İsabet oranı
        burada yeniden hesaplanmıyor — yukarıdaki rozet uçtan geliyor.
      </Beyan>
    </Kutu>
  );
}
