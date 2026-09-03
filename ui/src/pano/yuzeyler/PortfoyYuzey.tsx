"use client";

/* ============================================================================
   PORTFÖY YÜZEYİ — "Kitap nerede duruyor?"
   ----------------------------------------------------------------------------
   MERKEZDE OPERATÖRÜN İSTEDİĞİ GRAFİK VAR: bütün açık pozisyonlar, TUTARLARIYLA.
   Çubuk boyu piyasa değerini (adet × son fiyat) taşır; kâr/zarar AYRI bir kanalda,
   renkte durur. İkisini tek kanala bindirmek — çubuğu K/Z ile işaretlemek —
   50.000$'lık bir pozisyonu 200$'lık bir çubuk yapardı.

   DÖRT UÇ, DÖRT AYRI GEREKÇE (üçüncüsü koşullu):
     · `/api/today`      → `useBugun()` ile PAYLAŞILAN nabız. Kendi isteğini
       açmak yasak (durum.tsx sözleşmesi): üst bar "HALT çekili" derken bu yüzey
       bir önceki saniyenin "sakin"ini gösterirdi.
     · `/api/alpaca`     → brokerın aynası. Son fiyatın ve gerçekleşmemiş K/Z'nin
       BİRİNCİL kaynağı; kitapta fiyat alanı YOK (broker.Position dataclass'ında
       entry/stop var, current yok).
     · `/api/market`     → fiyat YEDEĞİ ve YALNIZ GEREKİNCE çekilir (aşağıdaki
       `piyasaYolu`). Evrenin TAMAMINI döndürüyor (~260 satır) — broker her
       pozisyona `current` verdiğinde bu yükü ödemenin karşılığı yok. Kitapta
       olup aynada olmayan bir sembol çıktığı an açılır.
     · `/api/diagnostics`→ seans-içi silahlanma bayrağının OKUNABİLİR tek yüzeyi.
       `/api/intraday-arm` yalnız POST; durumu ordan sormak onu DEĞİŞTİRMEK olurdu.

   BU YÜZEY HİÇBİR KOLU ÇEKMEZ. Tek POST'u olan uç (`/api/intraday-arm`) burada
   yalnız OKUNUR; geri alınamaz eylem bu turun kapsamı dışında.
   ============================================================================ */
import { ClipboardCheck, Scale, Send } from "lucide-react";
import { useEffect, useMemo } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { YUZEYLER } from "../alanlar";
import { useBugun } from "../durum";
import { useRota } from "../rota";
import type { BugunGovdesi } from "../tipler";
import { NABIZ_MS, useApi } from "../veri";
import { birlestir } from "./portfoy/birlestir";
import { MutabakatMasasi } from "./portfoy/MutabakatMasasi";
import {
  BolumBasligi,
  Deger,
  kzSinifi,
  Olculemedi,
  para,
  sayi,
  TazelikRozeti,
  UcHal,
  yuzde,
} from "./portfoy/olcum";
import { PozisyonGrafigi } from "./portfoy/PozisyonGrafigi";
import { PozisyonSeyri } from "./portfoy/PozisyonSeyri";
import { PozisyonTablosu } from "./portfoy/PozisyonTablosu";
import { SeansIciEmir } from "./portfoy/SeansIciEmir";
import type { AlpacaGovdesi, BugunPortfoyEk, PiyasaGovdesi, TeshisGovdesi } from "./portfoy/tipler";

/** `/api/diagnostics` sunucuda 45 sn önbellekli (api.py). Daha sık sormak aynı
 *  kopyayı tekrar tekrar indirmek olurdu; 60 sn önbelleğin bir tık üstünde. */
const TESHIS_MS = 60_000;
/** `/api/market` EOD kapanıştır — dakikada birden sık tazelemenin ölçülecek bir
 *  karşılığı yok (uç zaten "canlı fiyat servis etmem" diye beyan ediyor). */
const PIYASA_MS = 120_000;

// ---------------------------------------------------------------------------
// KPI KARTI
// ---------------------------------------------------------------------------
function Kpi({
  baslik,
  children,
  alt,
  rozet,
}: {
  baslik: string;
  children: React.ReactNode;
  alt: React.ReactNode;
  rozet?: React.ReactNode;
}) {
  return (
    <Card className="gap-4 rounded-none border-0 border-foreground/10 border-b ring-0 last:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0">
      <CardHeader>
        <CardTitle className="font-normal text-muted-foreground text-sm">{baslik}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-end justify-between gap-2">
        <div className="min-w-0 space-y-1">
          <div className="text-2xl leading-none tracking-tight tabular-nums">{children}</div>
          <div className="text-muted-foreground text-xs leading-snug">{alt}</div>
        </div>
        {rozet}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// YÜZEY
// ---------------------------------------------------------------------------
export function PortfoyYuzey() {
  const { bolum } = useRota();
  const y = YUZEYLER.finance;

  const bugun = useBugun();
  // `/api/today` gövdesinin PORTFÖY yarısı `pano/tipler.ts`te yok — orası panonun
  // ORTAK alanlarının sözleşmesi (üst bar + kenar çubuğu da onu okuyor) ve bu
  // yüzeyin ihtiyacıyla şişirilmemeli. Kesişim daraltması: `BugunGovdesi`in her
  // alanı yerinde kalır, üstüne bu yüzeyin ölçtüğü alanlar eklenir.
  const g = bugun.veri as (BugunGovdesi & BugunPortfoyEk) | null;

  const alpaca = useApi<AlpacaGovdesi>("/api/alpaca", NABIZ_MS);
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", TESHIS_MS);

  const kitapPoz = g?.open_positions ?? null;
  const hesap = alpaca.veri?.account ?? null;
  const brokerPoz = hesap?.positions ?? null;

  // FİYAT YEDEĞİ KOŞULLU: yalnız broker'ın `current` vermediği bir sembol varsa
  // `/api/market` açılır. Evrenin tamamı gelen bir ucu, ihtiyaç olmadan her iki
  // dakikada bir çekmenin ölçülecek bir karşılığı yok.
  const piyasaYolu = useMemo(() => {
    const fiyatli = new Set<string>();
    for (const p of brokerPoz ?? []) {
      const s = typeof p.symbol === "string" ? p.symbol.toUpperCase() : null;
      if (s !== null && sayi(p.current) !== null) fiyatli.add(s);
    }
    const hepsi = new Set<string>();
    for (const p of kitapPoz ?? []) if (typeof p.ticker === "string") hepsi.add(p.ticker.toUpperCase());
    for (const p of brokerPoz ?? []) if (typeof p.symbol === "string") hepsi.add(p.symbol.toUpperCase());
    for (const t of hepsi) if (!fiyatli.has(t)) return "/api/market";
    return null;
  }, [kitapPoz, brokerPoz]);
  const piyasa = useApi<PiyasaGovdesi>(piyasaYolu, PIYASA_MS);

  // ÇAPAYA KAYDIR — GenelYuzey ile aynı desen; derin bağ (`#/dashboard/finance/mutabakat`)
  // sayfayı açmakla kalmaz, bölümü de gösterir.
  //
  // BAĞIMLILIKTA NABIZ YOK VE BU HAYATİ: `bugun.zaman` bağımlılığa girseydi kaydırma
  // 15 saniyede BİR TEKRARLARDI — operatör sayfayı okurken zemin altından kayardı.
  // `veriGeldi` bir kez false→true döner ve orada kalır (veri.ts hata hâlinde eski
  // veriyi SİLMİYOR), yani bu etki en çok iki kez koşar: bölüm değiştiğinde ve ilk
  // veri geldiğinde. İkincisi gerekli, çünkü veri gelmeden bölüm yüksekliği gerçek
  // değildir ve çapa yanlış yere düşer.
  const veriGeldi = g !== null;
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum, veriGeldi]);

  // ---- BROKER TARAFININ NEDENİ (satırlara damgalanır) -----------------------
  const brokerNedeni: string | null = (() => {
    if (alpaca.oturumDustu) return "/api/alpaca 401 döndü — oturum düştü";
    if (alpaca.veri === null) return alpaca.hata ?? "/api/alpaca henüz okunmadı";
    if (alpaca.veri.paper_available === false) return "Alpaca kâğıt aynası yapılandırılmamış (paper_available=false) — hesap bloğu null";
    if (hesap === null) return "/api/alpaca `account` bloğu null döndü";
    if (hesap.connected === false) return "Alpaca hesabına BAĞLANILAMADI (account.connected=false)";
    return null;
  })();

  const piyasaNedeni: string | null =
    piyasaYolu === null
      ? "Fiyat yedeği açılmadı — broker her pozisyona son fiyat verdi"
      : piyasa.veri === null
        ? (piyasa.hata ?? "/api/market henüz okunmadı")
        : null;

  const defter = useMemo(
    () => birlestir(kitapPoz, brokerPoz, piyasa.veri?.rows ?? null, brokerNedeni, piyasaNedeni),
    [kitapPoz, brokerPoz, piyasa.veri, brokerNedeni, piyasaNedeni],
  );

  const koken = g?.sermaye_koken;
  const gunKz = g?.day_pnl_pct ?? null;
  const riskToplam = useMemo(() => {
    let t: number | null = null;
    let n = 0;
    for (const s of defter.satirlar) {
      if (s.riskUsd === null) continue;
      t = (t ?? 0) + s.riskUsd;
      n += 1;
    }
    return { t, n };
  }, [defter]);

  return (
    <div className="flex flex-col gap-6">
      {/* ---- BAŞLIK + DÖRT UCUN TAZELİK ŞERİDİ ------------------------------- */}
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
          <TazelikRozeti yol="/api/today" zaman={bugun.zaman} hata={bugun.hata} />
          <TazelikRozeti yol="/api/alpaca" zaman={alpaca.zaman} hata={alpaca.hata} />
          <TazelikRozeti yol="/api/diagnostics" zaman={teshis.zaman} hata={teshis.hata} />
          {piyasaYolu === null ? (
            <span className="text-muted-foreground text-xs">/api/market · açılmadı (broker fiyat verdi)</span>
          ) : (
            <TazelikRozeti yol="/api/market" zaman={piyasa.zaman} hata={piyasa.hata} />
          )}
        </div>
      </div>

      {/* =====================================================================
          BÖLÜM · BRİFİNG
          ===================================================================== */}
      <section id="bolum-brifing" className="flex scroll-mt-20 flex-col gap-4">
        <BolumBasligi ikon={ClipboardCheck} baslik="Brifing" soru="Sermaye ve açık pozisyonlar ne durumda?" />

        <UcHal
          yol="/api/today"
          yukleniyor={bugun.yukleniyor}
          hata={bugun.hata}
          oturumDustu={bugun.oturumDustu}
          veriVar={g !== null}
        >
          <div className="overflow-hidden rounded-xl bg-card ring-1 ring-foreground/10">
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5">
              <Kpi
                baslik="Kitap sermayesi"
                alt={koken?.ibare ?? "Kitabın nakdi (portfolio.json cash) — otorite nabız değil kitaptır"}
                rozet={
                  gunKz === null ? (
                    <Olculemedi
                      kisaMetin="gün %?"
                      neden="Günlük değişim henüz hesaplanmadı"
                      teknik="`day_pnl_pct` nabızda yok"
                    />
                  ) : (
                    <span className={cn("text-xs tabular-nums", kzSinifi(gunKz))}>{yuzde(gunKz)}</span>
                  )
                }
              >
                <Deger
                  v={koken?.gercek_canli_sermaye}
                  bicim={para}
                  neden="Kitabın nakdi okunamadı"
                  teknik="`sermaye_koken.gercek_canli_sermaye` yok ya da null"
                />
              </Kpi>

              <Kpi
                baslik="Broker sermayesi"
                alt={
                  brokerNedeni ??
                  `Alpaca ${hesap?.status ?? "durumsuz"} · alım gücü ${hesap?.buying_power === null || hesap?.buying_power === undefined ? "ölçülemedi" : para(hesap.buying_power)}`
                }
              >
                {brokerNedeni !== null ? (
                  <Olculemedi kisaMetin="ayna yok" neden={brokerNedeni} />
                ) : (
                  <Deger
                    v={hesap?.equity}
                    bicim={para}
                    neden="Broker hesabının varlık toplamı okunamadı"
                    teknik="/api/alpaca `account.equity` null döndü"
                  />
                )}
              </Kpi>

              <Kpi
                baslik="Broker nakdi"
                alt="Alpaca hesabının serbest nakdi — kitabın nakdinden AYRI bir sayı, ikisi mutabakat masasında köprülenir"
              >
                {brokerNedeni !== null ? (
                  <Olculemedi kisaMetin="ayna yok" neden={brokerNedeni} />
                ) : (
                  <Deger
                    v={hesap?.cash}
                    bicim={para}
                    neden="Hesaptaki nakit okunamadı"
                    teknik="/api/alpaca `account.cash` null döndü"
                  />
                )}
              </Kpi>

              <Kpi
                baslik="Açık pozisyon değeri"
                alt={
                  defter.toplamSatir === 0
                    ? "Açık pozisyon yok"
                    : `${defter.olculenDeger}/${defter.toplamSatir} pozisyonun tutarı ölçüldü${defter.anahtarsiz > 0 ? ` · ${defter.anahtarsiz} sembolsüz satır birleştirilemedi` : ""}`
                }
              >
                {defter.toplamDeger === null ? (
                  <Olculemedi
                    kisaMetin={defter.toplamSatir === 0 ? "0 pozisyon" : "toplanamadı"}
                    neden={
                      defter.toplamSatir === 0
                        ? "İki defter de boş — açık pozisyon yok. Bu ölçülmüş bir olgu."
                        : "Hiçbir pozisyonun piyasa değeri ölçülemedi; nedenleri grafiğin altında satır satır duruyor."
                    }
                  />
                ) : (
                  para(defter.toplamDeger)
                )}
              </Kpi>

              <Kpi
                baslik="Açık K/Z"
                alt={
                  defter.toplamSatir === 0
                    ? "Açık pozisyon yok"
                    : `${defter.olculenKz}/${defter.toplamSatir} pozisyonun K/Z'si ölçüldü · maruziyet ${g?.current_exposure_pct === null || g?.current_exposure_pct === undefined ? "ölçülemedi" : `%${g.current_exposure_pct}`}`
                }
                rozet={
                  riskToplam.t === null ? undefined : (
                    <span className="text-muted-foreground text-xs tabular-nums" title={`${riskToplam.n} pozisyonun giriş riski`}>
                      risk {para(riskToplam.t)}
                    </span>
                  )
                }
              >
                {defter.toplamKz === null ? (
                  <Olculemedi
                    kisaMetin={defter.toplamSatir === 0 ? "—" : "toplanamadı"}
                    neden={
                      defter.toplamSatir === 0
                        ? "Açık pozisyon yok, toplanacak kâr/zarar da yok."
                        : "Hiçbir pozisyonun açık kâr/zararı ölçülemedi."
                    }
                    teknik={
                      defter.toplamSatir === 0
                        ? undefined
                        : "ne broker `unrealized_pl` verdi ne türetme girdisi tamamdı"
                    }
                  />
                ) : (
                  <span className={kzSinifi(defter.toplamKz)}>
                    {defter.toplamKz > 0 ? "+" : ""}
                    {para(defter.toplamKz)}
                  </span>
                )}
              </Kpi>
            </div>
          </div>

          {/* ---- MERKEZDEKİ GRAFİK ------------------------------------------- */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">Açık pozisyonlar · tutar</CardTitle>
              <CardDescription>
                Her çubuk bir pozisyonun piyasa değeri (adet × son fiyat). Fiyat önce brokerın aynasından, yoksa
                `/api/market` kapanışından okunur ve her satır kaynağını taşır.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PozisyonGrafigi satirlar={defter.satirlar} />
            </CardContent>
          </Card>

          {/* ---- AYNI POZİSYONLAR, ÖBÜR SORU ---------------------------------
              Üstteki kart "ŞU AN ne kadar?" (tutar, tek an); bu kart "ZAMAN İÇİNDE
              nasıl gitti?" (girişe göre yüzde, seans seans). İkisi ayrı kart çünkü
              ayrı kanallar: birinde büyüklük dolar, öbüründe yüzde. Tek karta
              bindirmek, 50.000$'lık bir pozisyonla 500$'lığın çizgisini aynı
              ölçeğe koymak olurdu. Bu kart KENDİ ucunu (`/api/bars`) kendi YAVAŞ
              periyoduyla okur — sayfanın 15 sn'lik nabzına bağlı değil (veri EOD). */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">Açık pozisyonların seyri · girişe göre %</CardTitle>
              <CardDescription>
                Her çizgi bir pozisyonun giriş gününden bugüne kapanış seyri; sıfır çizgisi giriş fiyatıdır.
                Kesikli çizgi kitabın EŞİT AĞIRLIKLI ortalaması. Kaynak `/api/bars` — EOD kapanış.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PozisyonSeyri satirlar={defter.satirlar} />
            </CardContent>
          </Card>

          {/* ---- TABLO -------------------------------------------------------- */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">Açık pozisyon defteri</CardTitle>
              <CardDescription>
                Kitap ile brokerın BİRLEŞİMİ — sadece kesişim alınsaydı, tam da mutabakat masasının konusu olan
                satırlar sessizce düşerdi. Sütun başlığına tıklayarak sırala.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PozisyonTablosu satirlar={defter.satirlar} />
              {defter.anahtarsiz > 0 && (
                <p className="mt-3 text-uyari text-xs">
                  {defter.anahtarsiz} satır sembolsüz geldi ve birleştirilemedi — tabloda YOK. Kitap tarafında
                  `ticker`, broker tarafında `symbol` alanı okunamadı.
                </p>
              )}
            </CardContent>
          </Card>
        </UcHal>
      </section>

      {/* =====================================================================
          BÖLÜM · MUTABAKAT MASASI
          ===================================================================== */}
      <section id="bolum-mutabakat" className="flex scroll-mt-20 flex-col gap-4">
        <BolumBasligi ikon={Scale} baslik="Mutabakat masası" soru="Bizim defter ile brokerin defteri tutuyor mu?" />
        <UcHal
          yol="/api/today"
          yukleniyor={bugun.yukleniyor}
          hata={bugun.hata}
          oturumDustu={bugun.oturumDustu}
          veriVar={g !== null}
        >
          <MutabakatMasasi
            kopru={g?.broker_mutabakati}
            adet={g?.pozisyon_mutabakati}
            teyit={g?.defter_teyit}
            reconcile={alpaca.veri?.reconcile}
            akis={alpaca.veri?.stream}
          />
        </UcHal>
      </section>

      {/* =====================================================================
          BÖLÜM · SEANS İÇİ EMİR
          ===================================================================== */}
      <section id="bolum-intraemir" className="flex scroll-mt-20 flex-col gap-4">
        <BolumBasligi ikon={Send} baslik="Seans içi emir" soru="İşleme hazırlık kontrolü açık mı, deneme icrası ne diyor?" />
        <UcHal
          yol="/api/diagnostics"
          yukleniyor={teshis.yukleniyor}
          hata={teshis.hata}
          oturumDustu={teshis.oturumDustu}
          veriVar={teshis.veri !== null}
        >
          <SeansIciEmir
            intraday={teshis.veri?.intraday}
            emirler={hesap?.open_orders ?? null}
            emirNedeni={brokerNedeni ?? "/api/alpaca `account.open_orders` alanı gövdede yok"}
            /* KORUMA HÜKMÜ HESAP BLOĞUNDAN GELİR (v315): pozisyon başına `koruma` alanı
               `open_orders` içinde DEĞİL, hesap gövdesinde durur. Bu prop geçilmezse koruma
               rozeti hiç çizilmez — NVDA'nın korumasızlığı ölçülür ama EKRANA GELMEZ ki
               kalemin var olma sebebi tam olarak onu göstermekti. */
            hesap={hesap}
          />
        </UcHal>
      </section>
    </div>
  );
}
