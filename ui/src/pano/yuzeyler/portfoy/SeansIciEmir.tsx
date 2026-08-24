"use client";

/* ============================================================================
   SEANS İÇİ EMİR — SALT OKUMA. Bu bölüm hiçbir kolu ÇEKMEZ.
   ----------------------------------------------------------------------------
   `POST /api/intraday-arm` gerçek bir kapıdır: `state/INTRADAY_ARM` bayrağını
   açar ve otonom seans-içi emrin kapısını kaldırır (api.py:2872). Bu tur o kolu
   EKRANA KOYMAZ — geri alınamaz eylem tetiklemek turun kapsamı dışında.

   BAYRAK NEREDEN OKUNUYOR: `/api/intraday-arm` yalnız POST'tur, GET yoktur —
   yani durumu ordan öğrenmenin yolu onu DEĞİŞTİRMEKTİR. Okunabilir tek yüzey
   `/api/diagnostics.intraday` (api.py:4468 → `intraday_cycle.health()`), ve o
   blok `armed` alanını `health.intraday_armed()`ten okuyor — aynı dosyadan,
   aynı gerçek.

   İKİ "SİLAHLI" AYRI SORUDUR (api.py:4475 şerhinin uyardığı tuzak):
     · `armed`       → OPERATÖRÜN Faz-4b bayrağı (state/INTRADAY_ARM dosyası).
     · `armed_plans` → defterdeki EOD-silahlı plan SAYISI.
   İkisini tek rozette birleştirmek, "sistem silahlı" cümlesini iki farklı şeye
   birden söyletirdi.
   ============================================================================ */
import { Lock, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { adet as adetBicim, Olculemedi, para, sayi } from "./olcum";
import type { BrokerEmri, SeansIciBlogu } from "./tipler";

function Sayac({ ad, n, not, uyari = false }: { ad: string; n: number | undefined; not: string; uyari?: boolean }) {
  return (
    <div className="rounded-md border p-2" title={not}>
      <div className={cn("font-semibold text-xl tabular-nums", uyari && (n ?? 0) > 0 ? "text-amber-600 dark:text-amber-400" : "text-foreground")}>
        {n === undefined ? <Olculemedi kisa="—" neden={`${ad}: teşhis gövdesinde alan yok.`} /> : n}
      </div>
      <div className="text-[11px] leading-snug">{ad}</div>
    </div>
  );
}

export function SeansIciEmir({
  intraday,
  emirler,
  emirNedeni,
}: {
  intraday: SeansIciBlogu | undefined;
  /** `/api/alpaca.account.open_orders` — hesap bloğu null ise `null` (ayna yok). */
  emirler: readonly BrokerEmri[] | null;
  emirNedeni: string;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {/* --- SİLAHLANMA KAPISI ------------------------------------------------ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="size-4 text-muted-foreground" />
            Silahlanma kapısı
          </CardTitle>
          <CardDescription>
            Faz-4b bayrağı (<code className="text-xs">state/INTRADAY_ARM</code>). Varsayılan KAPALI = yalnız gözlem.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {intraday === undefined ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span> `/api/diagnostics` gövdesinde `intraday`
              bloğu yok — bayrağın durumu okunamıyor. `/api/intraday-arm` yalnız POST olduğu için ikinci bir okuma
              yolu YOK; durumu ordan sormak onu değiştirmek olurdu.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                {intraday.armed === undefined ? (
                  <Olculemedi kisa="bayrak okunamadı" neden="`intraday.armed` alanı gövdede yok." />
                ) : (
                  <Badge variant={intraday.armed ? "destructive" : "outline"}>
                    {intraday.armed ? "SİLAHLI · otonom emir kapısı AÇIK" : "silahsız · yalnız gözlem"}
                  </Badge>
                )}
                {intraday.mode && <Badge variant="secondary">mod: {intraday.mode}</Badge>}
                {intraday.enabled === false && <Badge variant="secondary">döngü kapalı (ENABLED=false)</Badge>}
                {intraday.ok === null && (
                  <Olculemedi kisa="tüketici hiç kurulmadı" neden="`intraday.ok` null: seans-içi tüketici bu süreçte hiç kurulmamış — arıza DEĞİL, üçüncü hâl." />
                )}
              </div>

              <p className="flex items-start gap-2 rounded-md border border-dashed p-2 text-muted-foreground text-xs">
                <Lock className="mt-0.5 size-3.5 shrink-0" />
                Bu pano kolu ÇEKMEZ. Bayrağı değiştiren uç (<code>POST /api/intraday-arm</code>) geri alınamaz bir
                icra kapısı açar; bu yüzey yalnız okur.
              </p>

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Sayac ad="EOD silahlı plan" n={intraday.armed_plans} not="Defterdeki silahlı plan sayısı — bayrakla AYRI soru" />
                <Sayac ad="Karar (bugün)" n={intraday.decisions?.today} not="intraday_decisions.jsonl'de bugüne düşen satır" />
                <Sayac ad="Karar (toplam)" n={intraday.decisions?.total} not="Defterin ömür boyu satır sayısı" />
                <Sayac ad="Ateşlenen" n={intraday.decisions?.fired} not="fired=true damgalı karar" />
              </div>

              {intraday.last_error && <p className="text-destructive text-xs">Son hata: {intraday.last_error}</p>}
              {intraday.last_decision_at && (
                <p className="text-muted-foreground text-xs">Son karar: {intraday.last_decision_at}</p>
              )}

              {/* AKIŞ BOŞLUĞU: `null` = zamanlayıcı kancası HİÇ KOŞMADI (api.py:4490).
                  "boşluk yok" diye göstermek, hiç bakılmamış bir şeye temiz raporu
                  vermek olurdu. */}
              <p className="text-muted-foreground text-xs">
                Akış boşluğu ölçümü:{" "}
                {intraday.akis_boslugu === null || intraday.akis_boslugu === undefined ? (
                  <Olculemedi
                    kisa="kanca hiç koşmadı"
                    neden="`intraday.akis_boslugu` null — zamanlayıcı kancası (scheduler._intraday_gap_check) bu süreçte hiç koşmadı. 'Boşluk yok' DEĞİL, 'bakılmadı'."
                  />
                ) : (
                  <code className="text-[11px]">{JSON.stringify(intraday.akis_boslugu)}</code>
                )}
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* --- GÖLGE İCRA -------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Gölge icra</CardTitle>
          <CardDescription>"Tetik kesilseydi ne olurdu" defteri — emir GÖNDERMEZ, yalnız kararı yazar.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {intraday?.shadow === undefined ? (
            <Olculemedi
              kisa="gölge bloğu yok"
              neden={
                intraday === undefined
                  ? "/api/diagnostics gövdesinde `intraday` bloğu HİÇ yok — gölge defteri de onun içinde yaşıyor, ayrı bir kaynağı yok."
                  : "`/api/diagnostics.intraday.shadow` gövdede yok — gölge defterinin özeti bu turda derlenmedi."
              }
            />
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={intraday.shadow.enabled ? "outline" : "secondary"}>
                  {intraday.shadow.enabled ? "gölge açık" : "gölge kapalı"}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Sayac ad="Bugün" n={intraday.shadow.today_n} not="Bugünkü gölge satırı" />
                <Sayac ad="Gönderilirdi" n={intraday.shadow.would_submit_n} not="would_submit damgalı bugünkü satır" />
                <Sayac ad="Engellendi" n={intraday.shadow.blocked_n} not="blocked* damgalı bugünkü satır" uyari />
                <Sayac ad="Toplam" n={intraday.shadow.total} not="Defterin ömür boyu satır sayısı" />
              </div>
              {intraday.shadow.vs_eod === null && (
                <Olculemedi kisa="EOD kıyası yok" neden="`shadow.vs_eod` null — gölge kararının EOD dolumuyla farkı bu turda ölçülmedi." />
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* --- AYNADAKİ AÇIK EMİRLER --------------------------------------------- */}
      <Card className="xl:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Aynadaki açık emirler</CardTitle>
          <CardDescription>
            Alpaca kâğıt hesabının açık emir defteri — en çok 20 satır (alpaca.py:1631 tavanı). Salt okuma.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {emirler === null ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span> {emirNedeni}
            </p>
          ) : emirler.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              Aynada açık emir yok. Bu ölçülmüş bir olgu — hesap bloğu okundu ve `open_orders` boş döndü.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Sembol</TableHead>
                    <TableHead>Yön</TableHead>
                    <TableHead>Tür</TableHead>
                    <TableHead className="text-right">Adet</TableHead>
                    <TableHead className="text-right">Stop</TableHead>
                    <TableHead className="text-right">Limit</TableHead>
                    <TableHead>Durum</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {emirler.map((o, i) => {
                    const q = sayi(o.qty);
                    const st = sayi(o.stop);
                    const lm = sayi(o.limit);
                    return (
                      <TableRow key={`${o.symbol ?? "?"}-${i}`}>
                        <TableCell className="font-medium">{o.symbol ?? <Olculemedi kisa="sembolsüz" neden="Emir satırında `symbol` yok." />}</TableCell>
                        <TableCell className="text-sm">{o.side ?? "—"}</TableCell>
                        <TableCell className="text-sm">{o.type ?? "—"}</TableCell>
                        <TableCell className="text-right tabular-nums">
                          {q === null ? <Olculemedi neden="Emrin `qty` alanı sayıya çevrilemedi." /> : adetBicim(q)}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {st === null ? <Olculemedi kisa="stop yok" neden="Bu emir türü stop fiyatı taşımıyor (`stop_price` boş)." /> : para(st)}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {lm === null ? <Olculemedi kisa="limit yok" neden="Bu emir türü limit fiyatı taşımıyor (`limit_price` boş)." /> : para(lm)}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{o.status ?? "durumsuz"}</Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
