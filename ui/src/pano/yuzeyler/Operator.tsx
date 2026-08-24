"use client";

/* ============================================================================
   OPERATÖR YÜZEYİ — şablonun `Profile` sayfası, Meridian'ın tek operatörüyle
   ----------------------------------------------------------------------------
   ŞABLONUN PROFİL SAYFASI BİR KİŞİYİ anlatıyordu (avatar, ad, e-posta, bio,
   sosyal bağlar). Meridian'da böyle bir kayıt YOK: kullanıcı tablosu yok, tek bir
   parola hash'i var (`meridian/auth.py`). Kişi kartı çizmek, olmayan bir kaydı
   varmış gibi göstermek olurdu. Bu yüzden sayfanın cevapladığı soru değişti —
   "ben kimim" değil, "HESABIM NASIL BAĞLI, TERCİHLERİM NE" (`alanlar.ts`ten
   birebir bu yüzeyin sorusu).

   İKİ BÖLÜM, KAYITTAKİ KİMLİKLERLE (`alanlar.ts::YUZEYLER.profile.bolumler`):
     · `bolum-ayarlar`  → broker + güvenlik duruşu + anahtarlar + sağlayıcı sağlığı
     · `bolum-tercihler` → arayüz tercihleri
   Çapa BİR SARMALAYICI `<section>` üstünde duruyor, tek bir kart üstünde değil:
   "ayarlar" kayıtta TEK bir bölüm ama dört ayrı soruya bakıyor ve dördünü tek
   karta sıkıştırmak, üç arıza türünü aynı kutuya koymak olurdu.

   ÜÇ UÇ, ÜÇ AYRI RİTİM ve her biri gerekçeli:
     · /api/alpaca      15 sn — broker aynası; pozisyon/emir seans içinde değişir
     · /api/secrets     0     — anahtar kurulumu bir OPERATÖR eylemidir, kendi
                                kendine değişmez; yoklamak boşuna istek olurdu
     · /api/diagnostics 0     — ucun kendi önbelleği 45 sn (api.py) ve bu sayfada
                                yalnız `saglayicilar` bloğu okunuyor; sürekli
                                yoklamak ~35 bloğu boşuna hesaplattırırdı
   İkisi de elle tazelenebiliyor (başlıktaki düğme) ve son okuma anı yazılı —
   "0 periyot" sessiz bir bayatlık kaynağı olmasın diye.
   ============================================================================ */
import { RefreshCw, Settings2, UserRound } from "lucide-react";
import { useEffect } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";
import { Broker } from "./kimlik/Broker";
import { Sirlar } from "./kimlik/Sirlar";
import { Tercihler } from "./kimlik/Tercihler";
import { zamanMetni } from "./kimlik/parcalar";
import type { AlpacaGovdesi, SirlarGovdesi, TeshisGovdesi } from "./kimlik/uctipleri";

export function Operator() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR, ELLE YAZILMAZ (SistemSagligiYuzey'deki gerekçenin aynısı).
  const y = YUZEYLER.profile;

  const alpaca = useApi<AlpacaGovdesi>("/api/alpaca", NABIZ_MS);
  const sirlar = useApi<SirlarGovdesi>("/api/secrets", 0);
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", 0);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const durgunZaman = sirlar.zaman ?? teshis.zaman;
  const durgunMetin = durgunZaman === null ? null : zamanMetni(durgunZaman.toISOString());

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <UserRound className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        {/* ROZETLER YALNIZ ÖLÇÜLENİ TAŞIR: alan gelmediyse rozet HİÇ çizilmez —
            boş bir "paper" rozeti, modu ölçmeden iddia etmek olurdu. */}
        <div className="flex flex-wrap items-center gap-2">
          {typeof sirlar.veri?.mode === "string" ? (
            <Badge variant="outline" className="font-mono text-xs">
              mod: {sirlar.veri.mode}
            </Badge>
          ) : null}
          {sirlar.veri?.live_enabled !== undefined ? (
            <Badge variant={sirlar.veri.live_enabled ? "destructive" : "outline"}>
              {sirlar.veri.live_enabled ? "CANLI PARA AÇIK" : "canlı para kapalı"}
            </Badge>
          ) : null}
          {typeof sirlar.veri?.autonomy_level === "number" ? (
            <Badge variant="outline">L{sirlar.veri.autonomy_level}</Badge>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              sirlar.tazele();
              teshis.tazele();
            }}
            title={
              durgunMetin === null
                ? "Bu iki uç periyodik yoklanmıyor; henüz bir kez bile okunmadı."
                : `Bu iki uç periyodik yoklanmıyor. Son okuma: ${durgunMetin}`
            }
          >
            <RefreshCw className="size-3.5" aria-hidden />
            Anahtar/sağlık tazele
          </Button>
        </div>
      </div>

      {durgunMetin !== null ? (
        <p className="-mt-2 text-muted-foreground text-xs">
          Anahtar ve sağlayıcı blokları periyodik yoklanmıyor (operatör eylemiyle değişirler). Son okuma:{" "}
          <span className="tabular-nums">{durgunMetin}</span>. Broker aynası 15 saniyede bir tazeleniyor.
        </p>
      ) : null}

      {/* --- AYARLAR ------------------------------------------------------ */}
      <section id="bolum-ayarlar" className="flex scroll-mt-20 flex-col gap-4">
        <div className="flex items-center gap-2">
          <Settings2 className="size-4 text-muted-foreground" aria-hidden />
          <h2 className="font-medium text-sm">{y.bolumler[0]?.baslik ?? "Broker ve sırlar"}</h2>
          <span className="text-muted-foreground text-xs">{y.bolumler[0]?.soru ?? ""}</span>
        </div>
        <Broker alpaca={alpaca} teshis={teshis} />
        <Sirlar sirlar={sirlar} teshis={teshis} />
      </section>

      {/* --- TERCİHLER ---------------------------------------------------- */}
      <Tercihler />
    </div>
  );
}
