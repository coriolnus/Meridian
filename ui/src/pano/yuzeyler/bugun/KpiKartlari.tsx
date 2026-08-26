"use client";

/* ============================================================================
   KPI IZGARASI — açılış ekranının altı sayısı
   ----------------------------------------------------------------------------
   Şablonun `default/_components/metric-cards.tsx` grameri (ikon kutusu + etiket +
   büyük tabular sayı + rozet + tek satır açıklama) AYNEN korunuyor; değişen tek şey,
   şablonun sabit sayılarının yerine ölçülmüş alanların gelmesi VE her kartın
   "ölçemedim" diyebilmesi.

   HER KART ALANIN VARLIĞINI SORAR, DOĞRULUĞUNU DEĞİL (`x.alan === undefined`).
   Neden: `/api/today` bir alanı ölçemediğinde onu HİÇ YAZMAZ; `equity ?? 0` yazan
   bir kart, ölçülmemiş sermayeyi "sıfır sermaye" diye çizerdi. Bu deponun birinci
   yasası tam olarak bunu yasaklıyor.

   `inbox_count` ile `pending_count` AYNI KARTTA ama AYNI SATIRDA DEĞİL — çünkü aynı
   şey değiller ve panonun eski kusuru ikisini karıştırmaktı (`_onay_bekleyen_damgala`
   şerhi:
   üç plan onay beklerken ekran "0 bekleyen onay" yazıyordu). Büyük sayı senden İŞ
   isteyeni sayar; alt satır o seans KURULAN planı sayar ve kimseden bir şey istemez.
   ============================================================================ */
import { Cpu, Database, Gauge, Inbox, Layers, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { Olculemedi, bicimOran, bicimPara, bicimSayi, pnlRengi } from "./ortak";
import type { BugunTam } from "./tipler";

const IZGARA =
  "grid grid-cols-1 gap-4 *:data-[slot=card]:bg-linear-to-t *:data-[slot=card]:from-primary/5 " +
  "*:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs sm:grid-cols-2 lg:grid-cols-3 " +
  "2xl:grid-cols-6 dark:*:data-[slot=card]:bg-card";

function Kart({
  ikon: Ikon,
  etiket,
  children,
  dip,
}: {
  ikon: LucideIcon;
  etiket: string;
  children: ReactNode;
  dip: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <div className="flex size-7 items-center justify-center rounded-lg border bg-muted text-muted-foreground">
            <Ikon className="size-4" aria-hidden />
          </div>
        </CardTitle>
        <CardDescription>{etiket}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">{children}</div>
        <p className="text-muted-foreground text-sm leading-snug">{dip}</p>
      </CardContent>
    </Card>
  );
}

/** Büyük sayının tek biçimi — altı kartın hepsinde aynı ölçü ve `tabular-nums`
 *  (rakam genişliği sabit; 15 saniyede bir tazelenen bir sayının yatay olarak
 *  zıplaması, değişmemiş bir kartı değişmiş gibi gösterir). */
function Sayi({ children, renk }: { children: ReactNode; renk?: string }) {
  return (
    <div className={`font-medium text-3xl tabular-nums leading-none tracking-tight ${renk ?? ""}`}>{children}</div>
  );
}

export function KpiIskeleti() {
  return (
    <div className={IZGARA}>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Card key={i}>
          <CardHeader>
            <CardTitle>
              <Skeleton className="size-7 rounded-lg" />
            </CardTitle>
            <CardDescription>
              <Skeleton className="h-4 w-24" />
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <Skeleton className="h-8 w-28" />
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function KpiKartlari({ b }: { b: BugunTam }) {
  const hb = b.heartbeat;
  const gunPnl = b.day_pnl_pct;
  const pozlar = b.open_positions;
  const planlar = b.todays_plans;

  return (
    <div className={IZGARA}>
      {/* 1 — SERMAYE. Rakamın YANINDA kökeni duruyor: ölçülen kusur (`api_today` içindeki
          `sermaye_koken` şerhi)
          panonun "94.457,91$" yazıp bunun bir ANTRENMAN artefaktı olduğunu söylememesiydi. */}
      <Kart
        ikon={Wallet}
        etiket="Sermaye"
        dip={
          b.sermaye_koken?.ibare !== undefined
            ? b.sermaye_koken.ibare
            : "kökeni ölçülemedi — gövdede `sermaye_koken.ibare` yok"
        }
      >
        {b.equity === undefined ? (
          <Olculemedi neden="Sermaye bildirilmedi" teknik="`/api/today` gövdesinde `equity` alanı yok" />
        ) : b.equity === null ? (
          <Olculemedi neden="Sermaye okunamadı" teknik="uç `equity` alanını ölçemedi (null döndü)" />
        ) : (
          <>
            <Sayi>{bicimPara(b.equity)}</Sayi>
            {gunPnl === undefined || gunPnl === null ? (
              <Badge variant="outline" className="text-muted-foreground">
                gün K/Z ölçülemedi
              </Badge>
            ) : (
              <Badge variant="outline" className={pnlRengi(gunPnl)}>
                {gunPnl >= 0 ? <TrendingUp className="size-3" aria-hidden /> : <TrendingDown className="size-3" aria-hidden />}
                {bicimOran(gunPnl)}
              </Badge>
            )}
          </>
        )}
      </Kart>

      {/* 2 — AÇIK POZİSYON. `open_positions` `analytics.today()`de HER ZAMAN liste olarak
          yazılır; yokluğu "sıfır pozisyon" değil "gövde beklenen şekilde gelmedi" demektir. */}
      <Kart
        ikon={Layers}
        etiket="Açık pozisyon"
        dip={
          b.current_exposure_pct === undefined || b.current_exposure_pct === null
            ? "maruziyet ölçülemedi — gövdede `current_exposure_pct` yok"
            : `maruziyet: sermayenin %${bicimSayi(b.current_exposure_pct)}'i risk altında`
        }
      >
        {pozlar === undefined ? (
          <Olculemedi
            neden="Açık pozisyon listesi bildirilmedi"
            teknik="`/api/today` gövdesinde `open_positions` alanı yok"
          />
        ) : (
          <Sayi>{bicimSayi(pozlar.length)}</Sayi>
        )}
      </Kart>

      {/* 3 — BEKLEYEN KARAR. Büyük sayı `inbox_count`; dip satırı `pending_count`. */}
      <Kart
        ikon={Inbox}
        etiket="Senden iş isteyen"
        dip={
          b.pending_count === undefined || b.pending_count === null
            ? "kurulan plan sayısı ölçülemedi — gövdede `pending_count` yok"
            : `ayrıca ${bicimSayi(b.pending_count)} plan bu seans kuruldu (GO/REVIEW) — onlar senden bir şey istemez`
        }
      >
        {b.inbox_count === undefined ? (
          <Olculemedi
            neden="Senden iş isteyen kalem sayısı bildirilmedi"
            teknik="`/api/today` gövdesinde `inbox_count` alanı yok"
          />
        ) : b.inbox_count === null ? (
          <Olculemedi neden="Bekleyen kararlar sayılamadı" teknik="uç gelen kutusunu sayamadı (null döndü)" />
        ) : (
          <>
            <Sayi>{bicimSayi(b.inbox_count)}</Sayi>
            {b.inbox_count > 0 ? <Badge variant="default">karar bekliyor</Badge> : null}
          </>
        )}
      </Kart>

      {/* 4 — GÜNÜN PLANI. Tarih dipte: "10 plan" cümlesi hangi seansın planı olduğunu
          söylemeden eksiktir ve defterin son tarihi bugünün tarihi OLMAYABİLİR. */}
      <Kart
        ikon={Gauge}
        etiket="Günün planı"
        dip={
          b.todays_plan_date === undefined
            ? "seans tarihi ölçülemedi — gövdede `todays_plan_date` yok"
            : b.todays_plan_date === null
              ? "defterde tarihli plan yok — hangi seans olduğu söylenemez"
              : `seans: ${b.todays_plan_date}`
        }
      >
        {planlar === undefined ? (
          <Olculemedi
            neden="Günün plan listesi bildirilmedi"
            teknik="`/api/today` gövdesinde `todays_plans` alanı yok"
          />
        ) : (
          <Sayi>{bicimSayi(planlar.length)}</Sayi>
        )}
      </Kart>

      {/* 5 — VERİ KAPISI. `data_ok` NABZIN İÇİNDE yaşıyor (`loop.daily_cycle` onu
          `health.write_heartbeat` çağrısıyla oraya yazar),
          `/api/today`in kendi üst düzeyinde DEĞİL — üst düzeyde arayan bir kart her zaman
          "ölçülemedi" derdi ve bu, ölçülmüş bir gerçeği yanlış olumsuzlamak olurdu. */}
      <Kart
        ikon={Database}
        etiket="Veri kalite kontrolü"
        dip={
          b.heartbeat_age_seconds === undefined || b.heartbeat_age_seconds === null
            ? "nabız yaşı ölçülemedi — gövdede `heartbeat_age_seconds` yok"
            : `nabız ${bicimSayi(Math.round(b.heartbeat_age_seconds))} sn önce${
                b.stale === undefined ? " · bayatlık ölçülemedi" : b.stale ? " · BAYAT" : ""
              }`
        }
      >
        {hb === undefined ? (
          <Olculemedi neden="Sistem nabzı bu turda gelmedi" teknik="`/api/today` gövdesinde `heartbeat` alanı yok" />
        ) : hb.data_ok === undefined ? (
          <Olculemedi
            neden="Veri sağlığı bu nabızda bildirilmedi"
            teknik="nabız `data_ok` taşımıyor (başlangıç verisi nabzı canlı-döngü nabzından az anahtar taşır)"
          />
        ) : (
          <>
            <Sayi renk={hb.data_ok ? undefined : "text-destructive"}>{hb.data_ok ? "sağlam" : "ŞÜPHELİ"}</Sayi>
            {hb.regime !== undefined ? (
              <Badge variant="outline" className="text-muted-foreground">
                rejim: {hb.regime}
              </Badge>
            ) : null}
          </>
        )}
      </Kart>

      {/* 6 — OTONOMİ. Seviye tek başına bir sayı; anlamı modla birlikte doğuyor
          (L0'da onay kuyruğu operatörde, L1+'da uç kendi işliyor). İkisi ayrılmaz. */}
      <Kart
        ikon={Cpu}
        etiket="Otonomi"
        dip={
          b.broker === undefined
            ? "broker ölçülemedi — gövdede `broker` alanı yok"
            : `broker: ${b.broker}`
        }
      >
        {b.autonomy_level === undefined ? (
          <Olculemedi
            neden="Otonomi düzeyi bildirilmedi"
            teknik="`/api/today` gövdesinde `autonomy_level` alanı yok"
          />
        ) : b.autonomy_level === null ? (
          <Olculemedi neden="Otonomi düzeyi okunamadı" teknik="uç özerklik düzeyini ölçemedi (null döndü)" />
        ) : (
          <>
            <Sayi>L{b.autonomy_level}</Sayi>
            {b.mode !== undefined ? (
              <Badge variant="outline" className="text-muted-foreground">
                {b.mode}
              </Badge>
            ) : null}
          </>
        )}
      </Kart>
    </div>
  );
}
