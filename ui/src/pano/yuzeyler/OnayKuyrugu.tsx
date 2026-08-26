"use client";

/* ============================================================================
   ONAY KUYRUĞU — şablonun `Tasks` yüzeyi, Meridian'ın gelen kutusuyla
   ----------------------------------------------------------------------------
   BU SAYFANIN SORDUĞU TEK SORU: "senden İŞ isteyen ne var?" — yani kuyruk bir
   olay akışı değil bir GÖREV LİSTESİDİR. Görev listesi grameri: ne · hangi konu ·
   ne zaman geldi · ne bekliyor. Dördü de sütun; beşincisi (kanıt) çekmecede.

   DÖRT UÇ, ÜÇ NABIZ — TEK YERDE AÇILIR:
     · /api/approvals   15 sn — kuyruğun kendisi
     · /api/today       15 sn — `useBugun()` paylaşılan nabız; onay bekleyen REVIEW
       planları BURADA (gelen kutusu ucunda DEĞİL) ve `inbox_count` çapraz kontrolü
     · /api/skills       5 dk — YALNIZ geliş damgası ve ham kanıt için (gelen kutusu
       öğeleri damga taşımıyor; gerekçe `onaylar.ts` başlığında). Seyrek olmasının
       AYRI bir sebebi var: bu uç salt-okuma değil, kayıt defterine yazıyor.
     · /api/diagnostics 45 sn — YALNIZ silahlanma raporu (`gatekeeper.arming`);
       sunucuda 45 sn önbellekli (api.py:4348), daha sık sormak aynı kopyayı
       yeniden indirmek olurdu

   KARAR YOLU BAĞLI — AMA SATIR SONUNDA DEĞİL (2026-08-25). Önceki turda onay/ret
   düğmesi bilerek dışarıda bırakılmıştı: bu kuyruktaki bir kalem (REVIEW planı)
   onay ANINDA aynaya emir gönderiyor ve bir görev listesinin satır sonundaki düğme
   "listeyi temizle" refleksiyle basılır. Gerekçe doğruydu, sonucu yanlıştı —
   operatör kararı hiç veremiyordu ("review butonuna basınca onaylayabilmem için
   bir ekran açılması gerekli"). Şimdi satırdaki eylem yalnız İNCELE; karar
   kalemin TAM kanıtının altında, ÇİFT ADIMLI ve iki tık arasında ne olacağı
   yazılı olarak veriliyor (`kuyruk/KararPaneli.tsx`).

   BOŞ KUYRUK "SIFIR BEKLEYEN" DEĞİLDİR: uç düştüyse ya da `inbox` alanını hiç
   döndürmediyse tablo yerine NEDEN yazılır. Bu ayrım bu sayfanın var olma
   sebebidir — okunmamış onay, alınmamış karardır.
   ============================================================================ */
import { useEffect, useMemo, useState } from "react";

import { CheckCheck, Inbox, ListTodo } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

import { YUZEYLER } from "../alanlar";
import { useBugun } from "../durum";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";
import { BolumKart, Deger, KpiKutu, Olculemedi, Satir } from "./kuyruk/parcalar";
import { OnayCekmecesi } from "./kuyruk/OnayCekmecesi";
import { OnayDefteri } from "./kuyruk/OnayDefteri";
import { OnayTablosu } from "./kuyruk/OnayTablosu";
import { kuyrugaCevir, TUR_ETIKET, type KuyrukOgesi, type KuyrukTuru } from "./kuyruk/onaylar";
import type { OnayGovdesi, PlanOzeti, SkillGovdesi, TeshisGovdesi } from "./kuyruk/tipler";

const GRAFIK: ChartConfig = {
  isIsteyen: { label: "iş istiyor", color: "var(--chart-1)" },
  kayit: { label: "karar verilmiş", color: "var(--chart-3)" },
};

const TUR_SIRASI: readonly KuyrukTuru[] = ["plan", "silahlanma", "revizyon", "oneri", "bilinmeyen"];

export function OnayKuyrugu() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR, ELLE YAZILMAZ: `alanlar.ts` bu yüzeyin başlığını ve cevapladığı
  // SORUYU tek yerde tutuyor; ikinci kez yazsaydık kayıt değiştiğinde ekran sessizce eski
  // soruyu sormaya devam ederdi.
  const y = YUZEYLER.tasks;

  const onay = useApi<OnayGovdesi>("/api/approvals", NABIZ_MS);
  // `/api/skills` NABZI BİLEREK SEYREK (5 dk) — ÖLÇÜLMÜŞ BİR YAN ETKİ YÜZÜNDEN: bu uç
  // salt-okuma DEĞİL, `skills.reconcile_enablement()` çağırıyor ve kayıt defterine YAZIYOR
  // (api.py:1828). Bu sayfanın ondan tek istediği geliş damgaları (`ts`/`at`) ve o damgalar
  // dakikada bir değişmiyor. Kuyruk açık dururken sunucuya dakikada bir defter yazdırmak,
  // okumak için yazmak olurdu.
  const skiller = useApi<SkillGovdesi>("/api/skills", NABIZ_MS * 20);
  const teshis = useApi<TeshisGovdesi>("/api/diagnostics", NABIZ_MS * 3);
  const bugun = useBugun();

  const [secili, setSecili] = useState<KuyrukOgesi | null>(null);
  const [yalnizIsIsteyen, setYalnizIsIsteyen] = useState(false);

  // ÇAPAYA KAYDIR — `GenelYuzey.tsx`teki desenin aynısı ve aynı gerekçeyle.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const ozet = useMemo(
    () =>
      kuyrugaCevir(
        onay.veri,
        onay.hata,
        skiller.veri,
        skiller.hata,
        teshis.veri?.gatekeeper?.arming ?? null,
        teshis.hata,
        // `todays_plans` uçta `unknown[]` olarak tiplendi (pano/tipler.ts, kasten): buradaki
        // daraltma bir İDDİA değil, okunacak alanların HEPSİ opsiyonel olduğu için güvenli.
        (bugun.veri?.todays_plans as readonly PlanOzeti[] | undefined) ?? null,
        bugun.hata,
      ),
    [onay.veri, onay.hata, skiller.veri, skiller.hata, teshis.veri, teshis.hata, bugun.veri, bugun.hata],
  );

  const gosterilen = useMemo(
    () => (yalnizIsIsteyen ? ozet.ogeler.filter((o) => o.isIstiyor) : ozet.ogeler),
    [ozet.ogeler, yalnizIsIsteyen],
  );

  const grafikVerisi = useMemo(
    () =>
      TUR_SIRASI.map((t) => {
        const hepsi = ozet.ogeler.filter((o) => o.tur === t);
        return {
          tur: TUR_ETIKET[t],
          isIsteyen: hepsi.filter((o) => o.isIstiyor).length,
          kayit: hepsi.filter((o) => !o.isIstiyor).length,
        };
      }).filter((s) => s.isIsteyen + s.kayit > 0),
    [ozet.ogeler],
  );

  const sunucuSayisi = bugun.veri?.inbox_count;
  // ÇAPRAZ KONTROL BİR ALARM DEĞİL BİR BEYAN: iki uç İKİ AYRI ANDA okundu (biri 15 sn'lik
  // nabız, öteki 60 sn'lik). Fark her zaman kusur değildir — ama sessiz kalırsa, panonun
  // saydığı ile kenar çubuğundaki rozetin saydığı ayrışır ve hangisine inanılacağı bilinmez.
  const sayimAyristi =
    sunucuSayisi !== undefined && sunucuSayisi !== null && ozet.inboxNeden === null && ozet.planNeden === null
      ? sunucuSayisi !== ozet.isIsteyen
      : false;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <ListTodo className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {ozet.inboxNeden === null ? (
            <Badge variant={ozet.isIsteyen > 0 ? "destructive" : "outline"}>{ozet.isIsteyen} iş istiyor</Badge>
          ) : (
            <Badge variant="outline">kuyruk ölçülemedi</Badge>
          )}
          {onay.veri?.level !== undefined ? <Badge variant="outline">otonomi L{onay.veri.level}</Badge> : null}
        </div>
      </div>

      <BolumKart
        kimlik="onaylar"
        baslik="Onayını bekleyen kalemler"
        soru="Hangi karar senin onayında duruyor?"
        ikon={Inbox}
        aksiyon={
          <label className="flex cursor-pointer items-center gap-2 text-muted-foreground text-xs">
            <Switch checked={yalnizIsIsteyen} onCheckedChange={setYalnizIsIsteyen} />
            yalnız iş isteyenler
          </label>
        }
      >
        {/* ---- ÖNCE OKUNAMAYANLAR: boş tablo çizmeden önce eksik olanı söyle ---- */}
        {onay.oturumDustu || bugun.oturumDustu ? (
          <Alert variant="destructive">
            <AlertTitle>Oturum düştü</AlertTitle>
            <AlertDescription>
              /api/approvals 401 döndü. Bu bir ölçüm hatası değil — panoya yeniden giriş gerekiyor.
            </AlertDescription>
          </Alert>
        ) : null}
        {ozet.inboxNeden !== null && !onay.oturumDustu ? (
          <Alert variant="destructive">
            <AlertTitle>Gelen kutusu okunamadı</AlertTitle>
            <AlertDescription>
              {ozet.inboxNeden} — aşağıdaki liste kuyruğun TAMAMI DEĞİL. &quot;Sıfır bekleyen&quot;
              diye okuma.
            </AlertDescription>
          </Alert>
        ) : null}
        {ozet.planNeden !== null ? (
          <Alert variant="destructive">
            <AlertTitle>Onay bekleyen planlar okunamadı</AlertTitle>
            <AlertDescription>{ozet.planNeden}</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <KpiKutu
            etiket="İş isteyen kalem"
            vurgu={ozet.isIsteyen > 0}
            altMetin="panonun kendi sayımı — sunucunun `inbox_count` ölçütüyle aynı kural"
          >
            {ozet.inboxNeden === null ? ozet.isIsteyen : <Olculemedi neden={ozet.inboxNeden} kisa />}
          </KpiKutu>
          <KpiKutu etiket="Sunucunun sayımı" altMetin="/api/today `inbox_count` — kenar çubuğu rozetinin kaynağı">
            <Deger
              deger={sunucuSayisi}
              neden="Sunucunun kendi sayımı bildirilmedi"
              teknik="/api/today `inbox_count` döndürmedi"
            />
          </KpiKutu>
          <KpiKutu
            etiket="Kayıt olarak duran"
            altMetin="karar verilmiş (kabul/ret) — listede görünür, iş istemez"
          >
            {ozet.inboxNeden === null ? (
              ozet.ogeler.length - ozet.isIsteyen
            ) : (
              <Olculemedi neden={ozet.inboxNeden} kisa />
            )}
          </KpiKutu>
          <KpiKutu etiket="Listedeki toplam satır" altMetin="gelen kutusu + onay bekleyen REVIEW planları">
            {ozet.ogeler.length}
          </KpiKutu>
        </div>

        {sayimAyristi ? (
          <p className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-sm leading-6">
            Panonun sayımı ({ozet.isIsteyen}) ile sunucunun <code className="font-mono text-xs">inbox_count</code>u
            ({sunucuSayisi}) ayrışıyor. İki uç İKİ AYRI ANDA okundu (
            <code className="font-mono text-xs">/api/approvals</code> 15 sn,
            <code className="font-mono text-xs"> /api/today</code> 15 sn) — fark bir tazelik farkı
            olabilir. Fark KALICIYSA sayım ölçütlerinden biri ayrışmış demektir.
          </p>
        ) : null}

        {ozet.damgaNeden !== null ? (
          <p className="text-muted-foreground text-xs leading-5">
            Geliş damgaları ölçülemedi: {ozet.damgaNeden}. Satırlar yine listelenir — damga sütunu
            &quot;ölçülemedi&quot; der, tarih UYDURULMAZ.
          </p>
        ) : null}

        {grafikVerisi.length > 0 ? (
          <ChartContainer config={GRAFIK} className="aspect-auto h-56 w-full">
            <BarChart data={grafikVerisi} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" tickLine={false} axisLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="tur" tickLine={false} axisLine={false} width={120} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar isAnimationActive={false} dataKey="isIsteyen" stackId="a" fill="var(--color-isIsteyen)" radius={[0, 0, 0, 0]} />
              <Bar isAnimationActive={false} dataKey="kayit" stackId="a" fill="var(--color-kayit)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ChartContainer>
        ) : null}

        <OnayTablosu
          ogeler={gosterilen}
          sec={setSecili}
          bosMetin={
            ozet.inboxNeden !== null
              ? "Kuyruk ÖLÇÜLEMEDİ (yukarıdaki uyarı) — bu boşluk 'bekleyen yok' demek değildir."
              : yalnizIsIsteyen && ozet.ogeler.length > 0
                ? "İş isteyen kalem yok. Süzgeci kapatınca karar verilmiş kayıtlar görünür."
                : "Gelen kutusu boş ve onay bekleyen REVIEW planı yok — senden şu an bir şey beklenmiyor."
          }
        />

        <p className="text-muted-foreground text-xs leading-5">
          <strong>İncele</strong>: kalemin tam kanıtı çekmecede açılır ve karar ORADA verilir —
          çift adımlı. Satır sonunda tek tıkla onay YOK, çünkü bu kuyruktaki bir kalem (REVIEW
          planı) onaylandığı ANDA aynaya emir göndermeyi deniyor
          (<code className="font-mono text-[11px]">POST /api/plan/&#123;id&#125;/onayla</code>). Geri
          alınamaz bir icra, bir görev listesinin satır sonuna konmaz; kanıtın altına, iki tık
          arasında ne olacağı yazılı hâlde konur.
        </p>
      </BolumKart>

      <OnayDefteri
        satirlar={onay.veri?.pending}
        seviye={onay.veri?.level}
        neden={
          onay.hata !== null
            ? onay.hata
            : onay.veri === null
              ? "/api/approvals henüz okunmadı"
              : onay.veri.pending === undefined
                ? "/api/approvals `pending` alanını döndürmedi"
                : null
        }
      />

      <BolumKart
        kimlik="sozlesme"
        baslik="Kuyruğun sözleşmesi"
        soru="Bu liste neyi kapsıyor, neyi kapsamıyor?"
        ikon={CheckCheck}
      >
        <div className="grid gap-x-8 sm:grid-cols-2">
          <div>
            <Satir etiket="Gelen kutusu kaynağı">
              <code className="font-mono text-xs">/api/approvals.inbox</code>
            </Satir>
            <Satir etiket="Plan kaynağı">
              <code className="font-mono text-xs">/api/today.todays_plans[onay_bekliyor]</code>
            </Satir>
            <Satir etiket="Geliş damgası kaynağı">
              <code className="font-mono text-xs">/api/skills</code>
            </Satir>
            <Satir etiket="Silahlanma kanıtı">
              <code className="font-mono text-xs">/api/diagnostics.gatekeeper.arming</code>
            </Satir>
          </div>
          <div>
            <Satir etiket="Ucun notu">
              {onay.veri?.note ?? <Olculemedi neden="Kuyruk ucunun notu bildirilmedi" teknik="/api/approvals `note` döndürmedi" kisa />}
            </Satir>
            <Satir etiket="Kırpma">
              <span className="text-xs">
                yok — uç gelen kutusunu kırpmıyor, pano da kırpmıyor (defter ayrı: en yeni 40)
              </span>
            </Satir>
          </div>
        </div>
        <Separator />
        <p className="text-muted-foreground text-xs leading-5">
          <strong>Kapsam dışı:</strong> canlı emir onayları yalnız L1+&apos;ta doğar; sistem L0
          iken <code className="font-mono text-[11px]">pending</code> defteri HİÇ döndürülmez. Bir
          Eksen-2 önerisine karar verildiğinde satır kuyrukta KALIR (üreteç aynı öneriyi yarın
          yeniden yazabilir, karar geçmişi görünür kalmalı) ama &quot;iş istiyor&quot; sayılmaz.
        </p>
      </BolumKart>

      {/* KARAR BAĞLAMI ÇEKMECEYE TAŞINIR, ORADA YENİDEN OKUNMAZ: seviye/HALT/broker bu
          sayfada zaten çekilmiş nabızlardan geliyor. Çekmece kendi isteğini açsaydı aynı
          soruya iki farklı ANIN cevabı olurdu (`durum.tsx` başlığındaki gerekçe).
          `tazele` ÜÇ UCU birden yeniler: karar `/api/approvals` defterini, plan onayı ise
          `/api/today` plan listesini kıpırdatır — hangisinin değiştiğini panonun tahmin
          etmesi, tazelenmeyen bir uçta kararı görünmez kılardı. */}
      <OnayCekmecesi
        oge={secili}
        acik={secili !== null}
        kapat={() => setSecili(null)}
        seviye={onay.veri?.level}
        seviyeNeden={
          onay.hata !== null
            ? onay.hata
            : onay.veri === null
              ? "/api/approvals henüz okunmadı"
              : "/api/approvals `level` alanını döndürmedi"
        }
        halt={bugun.veri?.halted}
        broker={bugun.veri?.broker}
        mod={bugun.veri?.mode}
        tazele={() => {
          onay.tazele();
          bugun.tazele();
          skiller.tazele();
        }}
      />
    </div>
  );
}
