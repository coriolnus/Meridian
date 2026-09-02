"use client";

/* ============================================================================
   ÇİZELGE — şablonun `Calendar` yüzeyi, hattın kendi saatiyle
   ----------------------------------------------------------------------------
   BU SAYFANIN SORDUĞU SORU: "hangi adım ne zaman koştu, sırada ne var?" Cevabı
   TEK bir uçtan geliyor ama DÖRT ayrı blokta duruyor ve dördü de gerekli:

     · `cizelge.damgalar`  → adım başına SON koşu damgası (`mechanism_beats.json`)
     · `watchdog`          → hangi adım penceresini AŞTI (`stale`/`never`/`askida`)
     · `scheduler`         → zamanlayıcının kendi nabzı (tick · poll · kadans damgaları)
     · `cizelge.kosular`   → hat koşularının başlangıç/bitişi (süre BURADA ölçülür)

   TEK İSTEK, TEK AN: dördü de `/api/diagnostics`ten geliyor ve TEK `useApi` ile
   okunuyor. Blok başına ayrı istek açsaydık aynı ekranda "bekçi 17/17" ile
   "çizelge 16 adım" gibi İKİ FARKLI AN görünebilirdi (`durum.tsx`taki gerekçenin
   aynısı). Nabız 45 sn: uç SUNUCUDA 45 sn önbellekli (api.py::DIAG_TTL_S) — daha sık
   sormak aynı kopyayı yeniden indirmek olurdu.

   TAKVİM GÖRÜNÜMÜ VAR AMA BAŞROLDE DEĞİL: veri penceresi 2-3 gecelik (koşu defteri
   40 satırda kırpık), yani bir ay ızgarası çoğunlukla boş kalır. Asıl cevap kadans
   tablosu + zaman çizelgesi; takvim yalnız "hangi günde kanıt gördüm" haritası ve
   işaretsiz günün "koşmadı" OLMADIĞINI kendi altında yazıyor.
   ============================================================================ */
import { useEffect, useMemo } from "react";

import { Activity, CalendarDays, Cpu, ListChecks, Timer } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";
import { AdimTablosu } from "./kuyruk/AdimTablosu";
import { CagriTablosu } from "./kuyruk/CagriTablosu";
import { KosuTablosu } from "./kuyruk/KosuTablosu";
import { SeansTakvimi } from "./kuyruk/SeansTakvimi";
import { cizelgeyiCoz, kosulariOlc } from "./kuyruk/cizelge";
import { BolumKart, Deger, goreliMetin, HukumRozet, KpiKutu, Olculemedi, Satir, sureMetni, zamanMetni, zamanMs } from "./kuyruk/parcalar";
import type { TeshisGovdesi } from "./kuyruk/tipler";

export function Cizelge() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR: `alanlar.ts` bu yüzeyin başlığını ve sorusunu tek yerde tutuyor.
  const y = YUZEYLER.calendar;
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", NABIZ_MS * 3);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  // ŞİMDİ BİR KEZ SABİTLENİR (yükün her tazelenmesinde yeniden): aynı sayfanın iki
  // tablosu iki farklı ANA göre yaş yazsaydı, "3 sa önce" ile "3 sa 2 dk önce"nin
  // hangisinin doğru olduğu bilinemezdi.
  const simdi = useMemo(() => Date.now(), [teshis.veri]);

  const ozet = useMemo(
    () => cizelgeyiCoz(teshis.veri?.cizelge, teshis.veri?.watchdog, teshis.hata, simdi),
    [teshis.veri, teshis.hata, simdi],
  );
  const kosular = useMemo(() => kosulariOlc(teshis.veri?.cizelge?.kosular), [teshis.veri]);

  const sched = teshis.veri?.scheduler;
  const sonTickMs = zamanMs(sched?.last_tick);
  const poll = sched?.poll_seconds;
  // SIRADAKİ TICK ÖLÇÜLEBİLİR (adım pencerelerinin aksine): `last_tick` ve `poll_seconds`
  // ikisi de uçtan geliyor, yani toplama bir tahmin değil bir hesap.
  const siradakiTickMs = sonTickMs !== null && poll !== undefined ? sonTickMs + poll * 1000 : null;
  const tickGecikti = siradakiTickMs !== null && siradakiTickMs < simdi;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <CalendarDays className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {ozet.neden === null ? (
            <>
              <Badge variant={ozet.nGecikti + ozet.nHicKosmadi > 0 ? "destructive" : "outline"}>
                {ozet.nGecikti + ozet.nHicKosmadi} geciken adım
              </Badge>
              {ozet.nAskida > 0 ? <Badge variant="outline">{ozet.nAskida} askıda</Badge> : null}
            </>
          ) : (
            <Badge variant="outline">çizelge ölçülemedi</Badge>
          )}
          {teshis.veri?.onbellekten !== undefined ? (
            <Badge
              variant="outline"
              title={`teşhis yükü sunucuda 45 sn önbellekli; bu kopya ${teshis.veri.onbellekten ? "önbellekten" : "taze hesaplandı"} (hesaplama_ts: ${teshis.veri.hesaplama_ts ?? "yazılmamış"})`}
            >
              {teshis.veri.onbellekten ? "önbellekten" : "taze"}
            </Badge>
          ) : null}
        </div>
      </div>

      {/* ---- 1) ADIMLAR ------------------------------------------------- */}
      <BolumKart
        kimlik="cizelge"
        baslik="Hattın adımları"
        soru="Zamanlanmış işler zamanında koştu mu?"
        ikon={ListChecks}
        aksiyon={
          teshis.veri?.watchdog?.n_ok !== undefined && teshis.veri.watchdog.total !== undefined ? (
            <Badge variant="outline" title="bekçinin kendi sayacı: penceresinde / izlenen toplam">
              bekçi {teshis.veri.watchdog.n_ok}/{teshis.veri.watchdog.total}
            </Badge>
          ) : null
        }
      >
        {teshis.oturumDustu ? (
          <Alert variant="destructive">
            <AlertTitle>Oturum düştü</AlertTitle>
            <AlertDescription>
              /api/diagnostics 401 döndü. Bu bir ölçüm hatası değil — panoya yeniden giriş gerekiyor.
            </AlertDescription>
          </Alert>
        ) : ozet.neden !== null ? (
          <Alert variant="destructive">
            <AlertTitle>Çizelge okunamadı</AlertTitle>
            <AlertDescription>{ozet.neden}</AlertDescription>
          </Alert>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <KpiKutu etiket="Penceresinde" altMetin="bekçi aralıklarının hiçbirinde değil">
                {ozet.nPenceresinde}
              </KpiKutu>
              <KpiKutu etiket="Gecikti" vurgu={ozet.nGecikti > 0} altMetin="`stale` kovası">
                {ozet.nGecikti}
              </KpiKutu>
              <KpiKutu etiket="Hiç koşmadı" vurgu={ozet.nHicKosmadi > 0} altMetin="`never` — kablolanmamış olabilir">
                {ozet.nHicKosmadi}
              </KpiKutu>
              <KpiKutu etiket="Askıda" altMetin="pencereyi aştı ama sistem beklemeye almış">
                {ozet.nAskida}
              </KpiKutu>
              <KpiKutu etiket="Karar yok" altMetin="özdeşlik sınaması tutmadı — karar verilmedi">
                {ozet.nOlculemedi}
              </KpiKutu>
            </div>

            <p
              className={
                ozet.hukumGuvenilir
                  ? "text-muted-foreground text-xs leading-5"
                  : "rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-sm leading-6"
              }
            >
              {ozet.hukumBeyani}
            </p>

            {teshis.veri?.cizelge?.damga_neden_yok ? (
              <Olculemedi neden="Adımların son koşu damgaları okunamadı" teknik={teshis.veri.cizelge.damga_neden_yok} />
            ) : null}

            <AdimTablosu adimlar={ozet.adimlar} simdi={simdi} />
          </>
        )}
      </BolumKart>

      {/* ---- 2) ZAMANLAYICI --------------------------------------------- */}
      <BolumKart
        kimlik="zamanlayici"
        baslik="Zamanlayıcının nabzı"
        soru="Dişliyi çeviren döngü hâlâ dönüyor mu, bir sonraki tur ne zaman?"
        ikon={Timer}
        aksiyon={
          siradakiTickMs === null ? (
            <Badge variant="outline">sıradaki tur ölçülemedi</Badge>
          ) : (
            <HukumRozet
              ton={tickGecikti ? "kotu" : "iyi"}
              metin={tickGecikti ? "tur GECİKTİ" : "tur zamanında"}
              baslik="son tick + poll periyodu; ikisi de uçtan ölçüldü"
            />
          )
        }
      >
        <div className="grid gap-x-8 sm:grid-cols-2">
          <div>
            <Satir etiket="Son tur (last_tick)">
              {zamanMetni(sched?.last_tick) ?? <Olculemedi neden="Zamanlayıcının son turu kaydedilmemiş" teknik="`scheduler.last_tick` yazılmamış" kisa />}
            </Satir>
            <Satir etiket="Turun yaşı">
              {goreliMetin(sonTickMs, simdi) ?? <Olculemedi neden="Son turun ne zaman olduğu okunamadı" teknik="son tur damgası ayrıştırılamadı" kisa />}
            </Satir>
            <Satir etiket="Tur periyodu">
              <Deger deger={poll} birim=" sn" neden="Turlar arası bekleme süresi bildirilmedi" teknik="`poll_seconds` yazılmamış" />
            </Satir>
            <Satir etiket="Beklenen sıradaki tur">
              {siradakiTickMs === null ? (
                <Olculemedi neden="Sıradaki turun zamanı hesaplanamadı" teknik="`last_tick` ya da `poll_seconds` eksik" kisa />
              ) : (
                <span className={tickGecikti ? "font-medium text-destructive tabular-nums" : "tabular-nums"}>
                  {zamanMetni(new Date(siradakiTickMs).toISOString()) ?? "—"}
                  <span className="ml-2 text-muted-foreground text-xs">
                    ({goreliMetin(siradakiTickMs, simdi) ?? ""})
                  </span>
                </span>
              )}
            </Satir>
            <Satir etiket="Toplam tur (cycles)">
              <Deger deger={sched?.cycles} neden="Toplam tur sayısı kaydedilmemiş" teknik="`cycles` yazılmamış" />
            </Satir>
          </div>
          <div>
            <Satir etiket="Durum dosyası güncellendi">
              {zamanMetni(sched?.updated) ?? <Olculemedi neden="Durum dosyasının güncellenme anı kaydedilmemiş" teknik="`scheduler.updated` yazılmamış" kisa />}
            </Satir>
            <Satir etiket="Öğrenme otomatik döngüsü (learn_session)">
              {sched?.learn_session ?? <Olculemedi neden="Son öğrenme turu kaydedilmemiş — hiç koşmamış olabilir" teknik="`learn_session` yazılmamış" kisa />}
            </Satir>
            <Satir etiket="Y4 toplama (y4_session)">
              {sched?.y4_session ?? <Olculemedi neden="Toplama turunun seansı kaydedilmemiş" teknik="`y4_session` yazılmamış" kisa />}
            </Satir>
            <Satir etiket="Doğrulama haftası">
              {sched?.validation_week ?? <Olculemedi neden="Doğrulama haftası kaydedilmemiş" teknik="`validation_week` yazılmamış" kisa />}
            </Satir>
            <Satir etiket="Çizelgenin gördüğü scheduler damgası">
              {zamanMetni(teshis.veri?.cizelge?.scheduler_updated) ?? (
                <Olculemedi neden="Çizelgenin gördüğü zamanlayıcı damgası kaydedilmemiş" teknik="`cizelge.scheduler_updated` yazılmamış" kisa />
              )}
            </Satir>
          </div>
        </div>
        <Separator />
        <p className="text-muted-foreground text-xs leading-5">
          Bu blok <strong>zamanlayıcının kendi</strong> nabzıdır; adımların otomatik döngüsü yukarıdaki
          tabloda. İkisi ayrı sorudur: döngü dönüyor olabilir ama içindeki bir adım susmuş olabilir
          (bekçinin var olma sebebi). Kadans damgaları (<code className="font-mono text-[11px]">learn_session</code>{" "}
          · <code className="font-mono text-[11px]">y4_session</code> ·{" "}
          <code className="font-mono text-[11px]">validation_week</code>) SEANS/HAFTA etiketidir,
          saat değil — saatleri adım damgalarında.
        </p>
      </BolumKart>

      {/* ---- 3) KOŞU DEFTERİ -------------------------------------------- */}
      <BolumKart
        kimlik="kosular"
        baslik="Hat koşuları"
        soru="Hangi hat ne zaman başladı, ne kadar sürdü, ne üretti?"
        ikon={Activity}
        aksiyon={
          <Badge variant="outline" title="uç son 40 koşuyu döndürüyor">
            {kosular.length} koşu
          </Badge>
        }
      >
        {teshis.hata !== null ? (
          <Olculemedi neden="Koşu defteri okunamadı" teknik={teshis.hata} />
        ) : teshis.veri?.cizelge?.kosular === undefined ? (
          <Olculemedi neden="Hat koşularının kaydı bildirilmedi" teknik="/api/diagnostics `cizelge.kosular` döndürmedi" />
        ) : (
          <KosuTablosu satirlar={kosular} />
        )}
      </BolumKart>

      {/* ---- 4) TAKVİM + GECE DÖNGÜLERİ --------------------------------- */}
      <BolumKart
        kimlik="takvim"
        baslik="Seans takvimi"
        soru="Hangi günde koşu ve gece döngüsü kaydı gördük?"
        ikon={CalendarDays}
        aksiyon={
          teshis.veri?.cizelge?.son_dongu?.yas_saat !== undefined &&
          teshis.veri.cizelge.son_dongu.yas_saat !== null ? (
            <Badge variant="outline" title="son gece döngüsünün yaşı — çıpa, pencereden bağımsız okunuyor">
              son döngü {sureMetni(teshis.veri.cizelge.son_dongu.yas_saat * 3600) ?? "—"} önce
            </Badge>
          ) : null
        }
      >
        {teshis.hata !== null ? (
          <Olculemedi neden="Takvim verisi okunamadı" teknik={teshis.hata} />
        ) : (
          <SeansTakvimi
            kosular={teshis.veri?.cizelge?.kosular}
            donguler={teshis.veri?.cizelge?.donguler}
            sonDongu={teshis.veri?.cizelge?.son_dongu}
          />
        )}
      </BolumKart>

      {/* ---- 5) AJAN ÇAĞRILARI ------------------------------------------ */}
      <BolumKart
        kimlik="cagrilar"
        baslik="Ajan çağrıları"
        soru="Model koştu mu, koştuysa dolu cevap verdi mi?"
        ikon={Cpu}
      >
        {teshis.hata !== null ? (
          <Olculemedi neden="Çağrı defteri okunamadı" teknik={teshis.hata} />
        ) : teshis.veri?.cizelge?.cagrilar === undefined ? (
          <Olculemedi neden="Ajan çağrılarının kaydı bildirilmedi" teknik="/api/diagnostics `cizelge.cagrilar` döndürmedi" />
        ) : (
          <CagriTablosu
            cagrilar={teshis.veri.cizelge.cagrilar}
            olayPenceresi={teshis.veri.cizelge.olay_penceresi}
          />
        )}
      </BolumKart>
    </div>
  );
}
