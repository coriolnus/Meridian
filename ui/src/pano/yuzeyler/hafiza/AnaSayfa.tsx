"use client";

/* ============================================================================
   HAFIZA · ANA SAYFA — hafıza servisinin kendi `home` görünümünün karşılığı
   ----------------------------------------------------------------------------
   BÖLÜM SIRASI KAYNAKTAN ÖLÇÜLDÜ (2026-09-02, Görev 9 · üst yüzey v0.9.2, çapa
   ebad4782). `home-view.tsx::HomeView` gövdesinin sırası şudur ve ekran onu
   birebir izler:

     1. ÜST SATIR, iki sütun: SOLDA (2/3) bellek takımyıldızı · SAĞDA (1/3) iki
        kart — bilgi sayfaları, sonra son belgeler. Her ikisinin başlığında
        "tümü" bağı ve varış görünümü de oradan ölçüldü.
     2. HAFIZA DEPOSU kartı (`bank-stats-view.tsx::MemoryStoreCard`): üç sayaç
        şeridi + kayıt bileşimi + bağ türleri.
     3. ETKİNLİK: ingest zaman serisi (`::MemoriesActivityChart`).

   ÜÇ BAŞLIKLI BÖLÜM (depo · birleştirme · etkinlik) üst yüzeyin KAYNAĞINDA
   `bank-stats-view.tsx::BankStatsView` bileşenindedir; operatörün ekranında ise
   ana sayfanın altında duruyor. İkisi burada BİLEREK birleştirildi: sıra ve kart
   içerikleri kaynaktan, sayfadaki yerleri operatörün gördüğü ekrandan. Sapma
   gizlenmedi — devir raporunda satır çapalarıyla yazılı.

   ---------------------------------------------------------------------------
   NE ÇİZİLMİYOR VE NEDEN (bedel yasası)
   ---------------------------------------------------------------------------
   · "Sonraki tazeleme" satırı KALKTI. Görev 2'de bir gerekçe satırı olarak
     duruyordu; Görev 9 ölçümü üst yüzeyin ana sayfasında böyle bir parça
     OLMADIĞINI gösterdi (kaynakta ne bileşen ne çağrı var). Ölçülmemiş bir
     eksikliği ekranda taşımak, birebirliği kendi tahminimizle bozmaktı.
   · "Tazelik" bloğu KALKTI: taşıdığı sayıların hepsi artık kendi kartlarında
     (birleştirme kuyruğu → birleştirme kartı, arka plan işleri → işler kartı).
     İki yerde çizmek aynı sayının iki kopyası olurdu. TEK kayıp "son yazım"
     damgasının etiketli satırıydı; o değer ham sayaç dökümünde duruyor ve oradan
     okunabiliyor — sessizce düşmedi.
   · Bilgi sayfaları kartı üst yüzeyde AĞACIN tamamıdır, bizde sayfa listesidir;
     gerekçesi ve bedeli kartın kendi dosyasında yazılı.

   ---------------------------------------------------------------------------
   TAKIMYILDIZ AYRI OKUNUR — VE BU BİR BEDEL KARARIDIR
   ---------------------------------------------------------------------------
   Üst yüzeyin ana sayfası graf verisini KENDİ isteğiyle, sayaçlardan bağımsız
   çekiyor ve gerekçesini de yazıyor: kenar sayısı düğüm sayısıyla süper-doğrusal
   büyüyor (yaklaşık bin düğüm → yetmiş bin kenar), bu yüzden ana sayfada düğüm
   TAVANI var ve okuma panoyu bekletmiyor. Burada da aynı: takımyıldız kendi
   ucunu kendi kartında okur, sayaçlar onu beklemez, o da sayaçları beklemez.
   Tavan da aynı sayıdır (üst yüzeyin ana sayfa çağrısı 200 düğüm).

   Sağ sütunun iki kartı da AYNI desendedir: her biri kendi ucunu okur. Biri
   düşerse öteki çizilmeye devam eder; tek bir toplu okuma, tek arızayı üç
   körlüğe çevirirdi.

   ---------------------------------------------------------------------------
   PENCERE DEĞİŞTİRMENİN BEDELİ (bedel yasası)
   ---------------------------------------------------------------------------
   Pencere ya da zaman alanı değiştiğinde özet ucu BAŞTAN okunur — yani sayaç
   bacağı da yeniden çağrılır, oysa değişen yalnız seri bacağıdır. Kazanç: tek
   uç, tek durum, iki bacağın gerekçeleri hep aynı anın ölçümü. Bedel: pencere
   düğmesine her basışta gereksiz bir sayaç okuması. Ölçülen büyüklük bir ek
   HTTP çağrısı değil, ucun içindeki bir ek bacak — ve o bacak zaten kullanıcı
   tetiğine bağlı, yoklamaya değil.
   ============================================================================ */
import { useCallback, useMemo, useState, type ReactNode } from "react";
import { Activity, Brain, Database, FileText, GitMerge, Layers, Link2, ListChecks, Network } from "lucide-react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Button } from "@/components/ui/button";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

import { yuzeyYolu, type Bolum } from "../../alanlar";
import { useRouter } from "../../rota";
import { useApi, type Durum } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi } from "../sistem/parcalar";
import {
  BAG_TURU_SIRASI,
  BilgiSayfalari,
  Dagilim,
  KAYIT_TURU_SIRASI,
  IslemlerKarti,
  KonsolidasyonKarti,
  SERI_ANAHTARLARI,
  SERI_YAPISI,
  Sayac,
  SonBelgeler,
  ZihinModelleriKarti,
  bagTuruEtiketi,
  bagTuruRengi,
  kayitTuruEtiketi,
  kayitTuruRengi,
  kisaSayi,
  type SeriAnahtari,
} from "./anasayfakartlari";
import { HamSatirlar, ISO_BENZERI, metin, sayi } from "./parcalar";
import { GrafPaneli } from "./takimyildizi";
import type { BankaSayaclari, BellekGrafi, HafizaOzeti, HafizaZarfi, SeriKovasi, ZamanSerisi } from "./uctipleri";

const UC_OZET = "/api/hindsight/ozet";
const UC_BELLEK_GRAF = "/api/hindsight/bellek-graf";

/* TAKIMYILDIZ DÜĞÜM TAVANI — üst yüzeyin ana sayfa çağrısıyla AYNI sayı (200).
   Vekilin kendi tavanı da 200 (`api.py::HAFIZA_LISTE_TAVANI`), yani buraya daha
   büyük bir sayı yazmak sessizce 200'e inerdi ve ekran istediğinden başka bir
   şey aldığını bilmezdi. İki tavan bugün eşit; ayrıştıkları gün istek düşer ve
   kırpma zinciri farkı SAYIYLA gösterir. */
const GRAF_TAVANI = 200;

/* PENCERELER VE ZAMAN ALANLARI SUNUCUNUN SÖZLÜĞÜNDEN GELİR, buradan değil:
   `api.py::_HAFIZA_SERI_PENCERESI` ve `::_HAFIZA_ZAMAN_ALANI` tanımadıkları
   değeri üst servise GÖNDERMİYOR, beyan edilmiş varsayılana oturtuyorlar. Buraya
   fazladan bir değer yazsaydık düğme çalışır görünür, ekran başka bir pencerenin
   sayısını çizerdi. Etiketler bizim, değerler onların. */
const PENCERELER = ["1h", "12h", "1d", "7d", "30d", "90d"] as const;
type Pencere = (typeof PENCERELER)[number];

const ZAMAN_ALANLARI = [
  { deger: "created_at", etiket: "İşlenme", uzun: "Kaydın hafızaya girdiği an" },
  { deger: "mentioned_at", etiket: "Anılma", uzun: "Olayın konuşmada geçtiği an" },
  { deger: "occurred_start", etiket: "Gerçekleşme", uzun: "Olayın gerçekten olduğu an" },
] as const;
type ZamanAlani = (typeof ZAMAN_ALANLARI)[number]["deger"];

/* ---------------------------------------------------------------------------
   ZAMAN SERİSİ
   --------------------------------------------------------------------------- */

/**
 * Kova etiketi — çözünürlük TELDEN gelir, VARSAYILMAZ. Çözünürlük gelmediyse damga
 * ham basılır: "gün" varsaymak, saatlik bir seriyi günlük gibi okuturdu.
 *
 * ISO KORUMASINDAN GEÇER (düzeltme turu 1, inceleme bulgusu I-3). İlk yazım ham
 * `new Date()` çağırıyordu ve bu dosyanın kardeşi tam o tuzağı kapatmak için var:
 * `new Date("3")` V8'de GEÇERLİ bir tarihtir (01.03.2001), yani sayı dizgesine
 * kayan bir damga ekseni uydurma günlere çevirirdi. Biçim ISO'ya benzemiyorsa
 * değer ÇEVRİLMEZ, ham basılır — tanımadığını sessizce yorumlama kuralı.
 *
 * ÇIPLAK "—" DE YOK: gerekçesiz bir tire, ölçülmemiş bir boşluğu ölçülmüş gibi
 * gösterir (`sistem/parcalar.tsx::Olculemedi` sözleşmesi).
 */
/**
 * OFSETSİZ ISO DİZGESİNE UTC ÇIPASI — üst yüzeyin `parseBucketIso` kuralının
 * karşılığı (inceleme M-2, kaynak `bank-stats-view.tsx` @ ebad4782).
 *
 * Kova damgaları zaman serisi ucundan KANONİK UTC olarak geliyor. ECMA-262
 * gereği ofset taşımayan bir ISO dizgesi (`2026-04-18T00:00:00`) `new Date()`
 * tarafından YEREL saat sayılır ve kova, tarayıcının saat dilimi kadar KAYAR.
 * Negatif ofsetli bir tarayıcıda gün kovası bir gün geriye düşerdi — sessizce,
 * çünkü etiket yine geçerli bir tarih basar.
 *
 * Ofset VARSA dokunulmaz: `Z` eklemek o durumda damgayı gerçekten bozardı.
 */
function utcCipasi(iso: string): string {
  return /[+Z-]$/.test(iso) || /[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
}

function kovaEtiketi(zaman: unknown, trunc: unknown): string {
  const s = metin(zaman);
  if (s === null) return "— (kova damgası gelmedi)";
  if (!ISO_BENZERI.test(s)) return s;
  const t = new Date(utcCipasi(s));
  if (Number.isNaN(t.getTime())) return s;
  if (trunc === "day") return t.toLocaleDateString("tr-TR", { day: "2-digit", month: "short" });
  if (trunc === "hour" || trunc === "minute") {
    return t.toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  }
  return t.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

/**
 * ZAMAN SERİSİ — ÜST YÜZEYİN GRAFİĞİYLE AYNI TİP (operatör bulgusu 2026-09-02).
 *
 * İLK YAZIM YIĞILMIŞ ÇUBUK ÇİZİYORDU ve operatör görsel turda "üst yüzeyde
 * sürekli, bizde merdiven" dedi. ÖLÇÜLDÜ (`bank-stats-view.tsx::MemoriesActivityChart`):
 * grafik `AreaChart`tır — üç seri `stackId` ile YIĞILI, `type="monotone"`,
 * 2 piksel çizgi ve tepeden dibe sönen bir dolgu geçişi, animasyon kapalı.
 * Izgara yalnız yatay, X ekseninde etiket sıkışması `minTickGap` ile açılıyor,
 * Y ekseni ondalıksız ve kısaltılmış. Aşağıdaki çizim o ölçümün karşılığıdır.
 *
 * KOVA ÇÖZÜNÜRLÜĞÜ EŞLEMESİ ZATEN BİREBİRDİ VE BU DA ÖLÇÜLDÜ: pencere→kova
 * kararını İSTEMCİ vermiyor, üst servis veriyor ve `trunc` alanında geri
 * bildiriyor. Vekil pencereyi aynen geçiriyor (yalnız tanımadığı değeri beyanlı
 * varsayılana oturtuyor), yani altı pencerenin altısında da bizim kovamız üst
 * yüzeyin kovasıdır. Buraya bir eşleme tablosu yazmak, sunucunun kararını
 * istemcide İKİNCİ kez tahmin etmek olurdu.
 *
 * SERİ ANAHTARLARI TIKLANABİLİR ve toplam SEÇİLİ serilerin toplamıdır — üst
 * yüzeyin davranışının aynısı. Kapalı bir seriyi toplama katmak, ekranda
 * görünmeyen bir sayıyı toplamda göstermek olurdu.
 *
 * BOŞ KOVA GİZLENMEZ: sıfırlı kovalar da eksende yerini alır (üst yüzey de öyle
 * yapıyor) — atlanan bir kova, zaman eksenini sessizce sıkıştırırdı.
 */
function Seri({
  seri,
  neden,
  acik,
  cevir,
}: {
  readonly seri: ZamanSerisi | null | undefined;
  readonly neden: string | null | undefined;
  readonly acik: Readonly<Record<SeriAnahtari, boolean>>;
  readonly cevir: (k: SeriAnahtari) => void;
}) {
  if (neden) return <Olculemedi neden="Zaman serisi okunamadı" teknik={neden} />;
  if (seri === undefined) return <Olculemedi neden="Zaman serisi bildirilmedi" teknik="uç seri bacağını hiç döndürmedi" />;
  if (seri === null) return <Olculemedi neden="Ölçüm denendi, seri gelmedi" teknik="seri alanı boş döndü ve gerekçe de taşınmadı" />;
  const kovalar: readonly SeriKovasi[] = Array.isArray(seri.buckets) ? seri.buckets : [];
  if (!Array.isArray(seri.buckets)) {
    return <Olculemedi neden="Seri kovaları tanınmayan bir biçimde geldi" teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir" />;
  }
  /* SAYAÇLAR `?? 0` İLE ALINIR ÇÜNKÜ ÜST SERVİS ONLARA `default: 0` VERİYOR —
     yani gelmemeleri bir ölçüm sonucudur. Ama ÜÇÜ DE hiçbir kovada sayı değilse
     bu artık eksiklik değil TİP SÜRÜKLENMESİdir ve "hiç kayıt yok" demek
     ölçülmemiş bir boşluğu ölçülmüş ilan etmek olurdu (inceleme bulgusu M-3). */
  const veri = kovalar.map((k) => ({
    etiket: kovaEtiketi(k.time, seri.trunc),
    tam: metin(k.time) ?? "",
    world: sayi(k.world) ?? 0,
    experience: sayi(k.experience) ?? 0,
    observation: sayi(k.observation) ?? 0,
  }));
  const acikAnahtarlar = SERI_ANAHTARLARI.filter((k) => acik[k]);
  const toplam = veri.reduce((a, b) => a + acikAnahtarlar.reduce((x, k) => x + b[k], 0), 0);
  const sayiliKova = kovalar.some((k) => sayi(k.world) !== null || sayi(k.experience) !== null || sayi(k.observation) !== null);

  if (kovalar.length > 0 && !sayiliKova) {
    return (
      <Olculemedi
        neden="Kova sayaçları tanınmayan bir biçimde geldi"
        teknik="kovalar geldi ama hiçbirinde tür sayacı sayı değil — şema sürüklenmiş olabilir; 'hiç kayıt yok' demek yanlış olurdu"
      />
    );
  }
  if (veri.length === 0 || toplam === 0) {
    return (
      <div className="flex flex-col gap-2">
        <SeriAnahtarlari acik={acik} cevir={cevir} toplam={toplam} />
        <p className="text-muted-foreground text-sm">
          {acikAnahtarlar.length === 0
            ? "Seçili tür yok — yukarıdaki anahtarlardan en az birini aç."
            : "Bu pencere okundu ve seçili türlerde hiç kayıt yok — bu ölçülmüş bir boşluktur, \"okuyamadım\" ile aynı şey değildir"}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <SeriAnahtarlari acik={acik} cevir={cevir} toplam={toplam} />
      <ChartContainer config={SERI_YAPISI} className="aspect-auto h-52 w-full">
        <AreaChart data={veri} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
          <defs>
            {acikAnahtarlar.map((k) => (
              <linearGradient key={k} id={`hafiza-seri-${k}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={`var(--color-${k})`} stopOpacity={0.35} />
                <stop offset="100%" stopColor={`var(--color-${k})`} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid vertical={false} strokeDasharray="2 4" />
          <XAxis dataKey="etiket" tickLine={false} axisLine={false} tickMargin={6} minTickGap={20} className="text-[11px]" />
          <YAxis tickLine={false} axisLine={false} width={44} allowDecimals={false} tickFormatter={kisaSayi} className="text-[11px]" />
          <ChartTooltip content={<ChartTooltipContent labelKey="etiket" />} />
          {acikAnahtarlar.map((k) => (
            <Area
              key={k}
              type="monotone"
              dataKey={k}
              stackId="a"
              stroke={`var(--color-${k})`}
              strokeWidth={2}
              fill={`url(#hafiza-seri-${k})`}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ChartContainer>
      <p className="text-muted-foreground text-xs tabular-nums">
        Pencerede toplam {toplam.toLocaleString("tr-TR")} kayıt · kova çözünürlüğü{" "}
        {typeof seri.trunc === "string" && seri.trunc ? seri.trunc : "bildirilmedi"}
      </p>
    </div>
  );
}

/** SERİ ANAHTARLARI — üst yüzeyin tıklanabilir efsanesinin karşılığı.
 *  Toplam yanlarında durur çünkü toplam SEÇİME bağlıdır: anahtarı kapatmak
 *  sayıyı da değiştirir ve ikisi ayrı yerlerde dursaydı bağ görünmezdi.
 *
 *  RENK NOKTASI DOĞRUDAN SERİ TANIMINDAN OKUNUR — VE İLK YAZIM ÖYLE DEĞİLDİ
 *  (T6 dış gözlemi, ölçüldü 2026-09-02). Noktalar grafiğin seri değişkenlerini
 *  kullanıyordu; o değişkenler grafik KABININ içinde tanımlı (shadcn grafik
 *  sarmalayıcısı onları `[data-chart=…]` kapsamında yazıyor) ve bu şerit kabın
 *  DIŞINDA duruyor. Sonuç sessizdi: geçersiz bir arka plan değeri, yani RENKSİZ
 *  noktalar — efsane vardı, rengi yoktu. Seri tanımı zaten tek kaynak (grafiğin
 *  kendi değişkenleri de ondan türetiliyor), o yüzden buradan okumak kopya
 *  üretmez. */
function SeriAnahtarlari({
  acik,
  cevir,
  toplam,
}: {
  readonly acik: Readonly<Record<SeriAnahtari, boolean>>;
  readonly cevir: (k: SeriAnahtari) => void;
  readonly toplam: number;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Kayıt türü anahtarları">
        {SERI_ANAHTARLARI.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => cevir(k)}
            aria-pressed={acik[k]}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-2 py-0.5 font-medium text-[11px] transition-colors",
              acik[k] ? "bg-muted text-foreground" : "text-muted-foreground/70 hover:text-muted-foreground",
            )}
          >
            <span
              className="size-2 rounded-[2px]"
              style={{ backgroundColor: SERI_YAPISI[k].color, opacity: acik[k] ? 1 : 0.3 }}
              aria-hidden
            />
            {SERI_YAPISI[k].label}
          </button>
        ))}
      </div>
      <span className="text-muted-foreground text-xs tabular-nums">
        {toplam.toLocaleString("tr-TR")} kayıt
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   SAYAÇ KAPISI — ÜÇ KART AYNI GÖVDEYİ OKUR, KAPI TEK YERDE
   ----------------------------------------------------------------------------
   Depo, birleştirme ve arka plan işleri kartlarının üçü de aynı sayaç gövdesini
   okuyor. Kapıyı üç kez yazsaydık üç ayrı gerekçe cümlesi doğardı ve biri
   düzeltilirken ötekiler eskirdi (tek-kaynak yasası).
   --------------------------------------------------------------------------- */
function SayaclarKapisi({
  ozet,
  children,
}: {
  readonly ozet: Durum<HafizaOzeti>;
  readonly children: (stats: BankaSayaclari) => ReactNode;
}) {
  return (
    <UcKapisi durum={ozet} yol={UC_OZET}>
      {(o) => {
        if (o.stats_neden) return <Olculemedi neden="Banka sayaçları okunamadı" teknik={o.stats_neden} />;
        if (o.stats === undefined) return <Olculemedi neden="Sayaçlar bildirilmedi" teknik="uç sayaç bacağını hiç döndürmedi" />;
        if (o.stats === null) {
          return <Olculemedi neden="Ölçüm denendi, sayaçlar gelmedi" teknik="sayaç alanı boş döndü ve gerekçe de taşınmadı" />;
        }
        return <>{children(o.stats)}</>;
      }}
    </UcKapisi>
  );
}

/* --------------------------------------------------------------------------- */

export function AnaSayfa({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  const [pencere, setPencere] = useState<Pencere>("7d");
  const [zamanAlani, setZamanAlani] = useState<ZamanAlani>("created_at");
  /* SERİ ANAHTARLARI KABUKTA TUTULUR, GRAFİĞİN İÇİNDE DEĞİL: seçim pencere
     değiştiğinde de korunmalı — grafiğin içinde dursaydı her okumada sıfırlanır
     ve operatör aynı anahtarı her pencerede yeniden kapatırdı. */
  const [acikSeriler, setAcikSeriler] = useState<Record<SeriAnahtari, boolean>>({
    world: true,
    experience: true,
    observation: true,
  });
  const seriCevir = (k: SeriAnahtari) => setAcikSeriler((o) => ({ ...o, [k]: !o[k] }));

  /* YOKLANMAZ (periyot verilmez): bu okuma GEZİNMEYLE tetiklenir. Banka
     sayaçları saniyede bir kaymaz ve otuz saniyede bir yeniden çekmek, operatör
     ekrandaki sayıyı okurken onu altından değiştirirdi. */
  const yol = bank === null ? null : `${UC_OZET}?bank=${encodeURIComponent(bank)}&period=${pencere}&time_field=${zamanAlani}`;
  const ozet = useApi<HafizaOzeti>(yol);

  /* AYRI OKUMA, AYRI DURUM (dosya başlığındaki bedel şerhi): graf ucu ağırdır ve
     pencere/zaman alanı değişimlerinden ETKİLENMEZ — özet yoluna eklenseydi her
     pencere düğmesine basışta yeniden çekilirdi. */
  const grafYolu = bank === null ? null : `${UC_BELLEK_GRAF}?bank=${encodeURIComponent(bank)}&limit=${GRAF_TAVANI}`;
  const graf = useApi<HafizaZarfi<BellekGrafi>>(grafYolu);

  /* GÖRELİ ZAMANIN "ŞİMDİ"Sİ OKUMAYA ÇAPALANIR, ÇİZİME DEĞİL: her çizimde yeniden
     okunsaydı aynı yanıtın iki satırı iki ayrı ana göre yazılabilirdi. Özet
     tazelendiğinde "5 saat önce" cümleleri de tazelenir.

     ÇAPA TEK UCA BAĞLI VE SINIRI YAZILI (inceleme M-6): sayfadaki üç okuma ayrı
     uçlardan geliyor, "şimdi" ise yalnız özet okumasıyla ilerliyor. Özet düşer ama
     belgeler/sayfalar okunursa, sağ sütunun göreli zamanları montaj anına göre
     yazılır — sapma bir okuma penceresi kadardır, damganın kendisi değil. Her karta
     kendi "şimdi"sini vermek, aynı ekranda üç ayrı şimdi doğururdu. */
  const simdi = useMemo(() => Date.now(), [ozet.zaman]);

  const { push: adreseGit } = useRouter();
  /* Üst yüzeyde de böyle: ana sayfadaki graf bir GEZİNME yüzeyidir, kayıt detayı
     Bellekler görünümünün işidir. Düğüm bilgisi kullanılmıyor ve kullanılmadığı
     yazılı — adres kayda değil GÖRÜNÜME gidiyor. Sağ sütunun iki "tümü" bağının
     varış görünümleri de üst yüzeyden ölçüldü. */
  const listeyeGit = useCallback(() => adreseGit(yuzeyYolu("memory", "hafiza-bellekler")), [adreseGit]);
  const bilgiyeGit = useCallback(() => adreseGit(yuzeyYolu("memory", "hafiza-bilgi")), [adreseGit]);
  const belgelereGit = useCallback(() => adreseGit(yuzeyYolu("memory", "hafiza-belgeler")), [adreseGit]);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-anasayfa" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi neden="Okunacak banka seçilemedi" teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor" />
      </BolumKart>
    );
  }

  return (
    <>
      {/* ÜST SATIR — üst yüzeyin ana sayfa ızgarası: takımyıldız solda ve geniş,
          sağda iki dar kart. Sayaçlar bu satırın ALTINDA durur; öne almak, "bu
          bankada ne var" sorusunu bir tabloyla cevaplamak olurdu, oysa üst yüzey
          onu bir HARİTAYLA cevaplıyor ve operatörün beğendiği şey tam olarak bu. */}
      <div className="grid min-w-0 gap-4 lg:grid-cols-3">
        <BolumKart
          kimlik="hafiza-takimyildizi"
          baslik="Bellek takımyıldızı"
          soru="Bu bankadaki kayıtlar birbirine nasıl bağlanıyor?"
          ikon={Network}
          className="min-w-0 lg:col-span-2"
        >
          <UcKapisi durum={graf} yol={UC_BELLEK_GRAF}>
            {/* PANEL PAYLAŞIMLI (inceleme I-1/I-2): kırpma zinciri, rozetler ve
                "tanınmayan biçim" cümlesi Bellekler'deki tam grafla AYNI yerden
                gelir. İki ekran yalnız ad, yükseklik ve tıklamada ayrışır. */}
            {(z) => (
              <GrafPaneli zarf={z} ad="Bellek takımyıldızı" yukseklik={464} dugumTiklandi={listeyeGit} />
            )}
          </UcKapisi>
        </BolumKart>

        <div className="flex min-w-0 flex-col gap-4">
          <BolumKart
            kimlik="hafiza-sayfalar"
            baslik="Bilgi sayfaları"
            soru="Bu bankada hangi sayfalar yazılı?"
            ikon={Layers}
            className="min-w-0"
          >
            <BilgiSayfalari bank={bank} simdi={simdi} git={bilgiyeGit} />
          </BolumKart>

          <BolumKart
            kimlik="hafiza-son-belgeler"
            baslik="Son belgeler"
            soru="Belge listesinin başında hangi kayıtlar duruyor?"
            ikon={FileText}
            className="min-w-0"
          >
            <SonBelgeler bank={bank} simdi={simdi} git={belgelereGit} />
          </BolumKart>
        </div>
      </div>

      {/* HAFIZA DEPOSU — üst yüzeyin `MemoryStoreCard`ı: üç sayaç + iki dağılım */}
      <BolumKart kimlik="hafiza-anasayfa" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <SayaclarKapisi ozet={ozet}>
          {(s) => (
            <>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                <Sayac etiket="Kayıt" ikon={Database} deger={s.total_nodes} teknik="toplam kayıt sayacı gelmedi ya da sayı değil" />
                <Sayac etiket="Belge" ikon={FileText} deger={s.total_documents} teknik="toplam belge sayacı gelmedi ya da sayı değil" />
                <Sayac etiket="Bağ" ikon={Link2} deger={s.total_links} teknik="toplam bağ sayacı gelmedi ya da sayı değil" />
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="flex min-w-0 flex-col gap-2">
                  <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Kayıt bileşimi</h3>
                  {/* GÖZLEM SAYACI BURAYA EKLENMEZ — VE İLK YAZIM EKLİYORDU
                      (düzeltme turu 1, inceleme bulgusu I-1). Şerh "gözlem türü
                      dağılımın içinde gelmiyor" diyordu; canlı ölçüm bunu ÇÜRÜTTÜ:
                      tür dağılımı `experience`/`observation`/`world` anahtarlarını
                      TAŞIYOR. Eklemek aynı adı listeye iki kez koyuyordu — ekranda
                      aynı etiketle iki çubuk, üstelik tekrarlı bir React anahtarı.
                      Toplam gözlem sayacı aşağıdaki ham satırlarda görünür. */}
                  {/* GÖZLEM DİLİMİNİN KAYNAĞI ÜST YÜZEYDEN AYRIŞIYOR VE BU YAZILI
                      (inceleme M-1): üst yüzey üçüncü dilimi ayrı bir toplam gözlem
                      sayacından ve bir özellik bayrağına bağlı çiziyor; biz tür
                      dağılımının kendi anahtarından çiziyoruz (plan ruling'i bu alanı
                      adıyla söylüyor). Seçimin kazancı: parçaların toplamı çubuğun
                      paydasına EŞİT — iki ayrı sayacı karıştıran bir çubuk, yüzdeleri
                      sessizce yanlış yapardı. Bedeli: iki sayaç eşit olmak zorunda
                      değil, yani buradaki gözlem sayısı üst yüzeydekinden farklı
                      çıkabilir. Kıyas canlı pencerede bir kez yapılmalı (devir kalemi). */}
                  <Dagilim
                    govde={s.nodes_by_fact_type}
                    sira={KAYIT_TURU_SIRASI}
                    renk={kayitTuruRengi}
                    etiket={kayitTuruEtiketi}
                    bosCumle="Dağılım okundu ve içi boş geldi — bu ölçülmüş bir boşluktur"
                  />
                </div>
                <div className="flex min-w-0 flex-col gap-2">
                  <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Bağ türleri</h3>
                  <Dagilim
                    govde={s.links_by_link_type}
                    sira={BAG_TURU_SIRASI}
                    renk={bagTuruRengi}
                    etiket={bagTuruEtiketi}
                    bosCumle="Dağılım okundu ve içi boş geldi — bu ölçülmüş bir boşluktur"
                  />
                </div>
              </div>

              <div className="flex min-w-0 flex-col gap-2">
                <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Sayaç gövdesinin tamamı</h3>
                {/* Yukarıda ya da aşağıdaki kartlarda ÇİZİLEN alanlar burada
                    tekrarlanmaz; geri kalan her anahtar ham basılır, böylece
                    tanımadığımız bir alan ekrandan sessizce düşmez. */}
                <HamSatirlar
                  govde={s}
                  atla={[
                    "total_nodes", "total_documents", "total_links", "nodes_by_fact_type",
                    "links_by_link_type", "last_consolidated_at", "pending_consolidation",
                    "failed_consolidation", "operations_by_status",
                  ]}
                />
              </div>
            </>
          )}
        </SayaclarKapisi>
      </BolumKart>

      {/* BİRLEŞTİRME — üst yüzeyin ikinci bölümü: birleştirme kartı + zihin modelleri */}
      <div className="grid min-w-0 gap-4 md:grid-cols-2">
        <BolumKart
          kimlik="hafiza-birlestirme"
          baslik="Birleştirme"
          soru="Kaç kayıt bağlandı, kaçı bekliyor, kaçı düştü?"
          ikon={GitMerge}
          className="min-w-0"
        >
          <SayaclarKapisi ozet={ozet}>
            {/* TAZELEME ÇAĞIRANIN İŞİ: sayaçlar bu sayfanın özet okumasından
                geliyor, kartın kendi okuması yok. Kurtarma düğmesi tuttuğunda
                aynı okuma yeniden yapılır — yoksa ekran, değişmiş bir gerçeği
                eski sayılarla göstermeye devam ederdi. */}
            {(s) => <KonsolidasyonKarti stats={s} bank={bank} simdi={simdi} tazele={ozet.tazele} />}
          </SayaclarKapisi>
        </BolumKart>

        <BolumKart
          kimlik="hafiza-zihin-ozeti"
          baslik="Zihin modelleri"
          soru="Kaç model güncel, kaçının kapsamında okunmamış kayıt var?"
          ikon={Brain}
          className="min-w-0"
        >
          <ZihinModelleriKarti bank={bank} />
        </BolumKart>
      </div>

      {/* ETKİNLİK — üst yüzeyin üçüncü bölümü: ingest grafiği + arka plan işleri */}
      <div className="grid min-w-0 gap-4 lg:grid-cols-3">
        <BolumKart
          kimlik="hafiza-akis"
          baslik="Hafızaya giren kayıtlar"
          soru="Seçilen pencerede ne kadar yazıldı, hangi türden?"
          ikon={Activity}
          className="min-w-0 lg:col-span-2"
          aksiyon={
            <div className="flex flex-wrap items-center gap-1">
              {PENCERELER.map((p) => (
                <Button key={p} variant={p === pencere ? "secondary" : "ghost"} size="xs" onClick={() => setPencere(p)}>
                  {p}
                </Button>
              ))}
            </div>
          }
        >
          <div className="flex flex-wrap items-center gap-1">
            {ZAMAN_ALANLARI.map((z) => (
              <Button
                key={z.deger}
                variant={z.deger === zamanAlani ? "secondary" : "ghost"}
                size="xs"
                title={z.uzun}
                onClick={() => setZamanAlani(z.deger)}
                className={cn(z.deger === zamanAlani && "font-medium")}
              >
                {z.etiket}
              </Button>
            ))}
          </div>
          <UcKapisi durum={ozet} yol={UC_OZET}>
            {(o) => <Seri seri={o.zaman_serisi} neden={o.zaman_serisi_neden} acik={acikSeriler} cevir={seriCevir} />}
          </UcKapisi>
        </BolumKart>

        <BolumKart
          kimlik="hafiza-islemler"
          baslik="Arka plan işleri"
          soru="Bu bankada hangi işler koştu, hangi durumdalar?"
          ikon={ListChecks}
          className="min-w-0"
        >
          <SayaclarKapisi ozet={ozet}>{(s) => <IslemlerKarti stats={s} />}</SayaclarKapisi>
        </BolumKart>
      </div>
    </>
  );
}
