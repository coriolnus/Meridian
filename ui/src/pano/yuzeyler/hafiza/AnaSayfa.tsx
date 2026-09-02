"use client";

/* ============================================================================
   HAFIZA · ANA SAYFA — hafıza servisinin kendi `home` görünümünün karşılığı
   ----------------------------------------------------------------------------
   ÜST YÜZEYİN ANA SAYFASI BEŞ BLOK ÇİZİYOR ve bizde İKİSİ VAR. Bu bir eksik
   değil, ÖLÇÜLMÜŞ BİR KAPSAM — ve kapsamın yazılı durması bedel yasasının şartı:

     ÇİZİLEN                  kaynak
     · banka sayaç kartı      özet ucunun sayaç bacağı
     · ingest zaman serisi    özet ucunun seri bacağı

     ÇİZİLMEYEN               nedeni
     · bellek takımyıldızı    graf verisi ayrı bir uçtan gelir ve Varlıklar
                              görünümüne aittir (bu turun kapsamı dışında)
     · bilgi sayfası ağacı    Bilgi Tabanı görünümüne ait, aynı tur
     · son eklenen belgeler   Belgeler görünümüne ait, aynı tur
   Üçü de kenar çubuğunda KENDİ duraklarıyla duruyor; ana sayfaya kısayol olarak
   kopyalanmaları sonraki turun işi. Boş bir kutu çizip "yakında" yazmak yerine
   hiç çizmemek, ekranı olduğundan dolu göstermemek demek.

   ---------------------------------------------------------------------------
   "SONRAKİ TAZELEME" NEDEN BİR SAYI DEĞİL, BİR GEREKÇE
   ---------------------------------------------------------------------------
   Üst yüzeyin `next-refresh` parçası ÖLÇÜLDÜ: girdisi bir bankanın sayaçları
   DEĞİL, bir zihin modelinin tetikleyicisidir (`refresh_cron` /
   `refresh_after_consolidation`) ve o alanlar bu ekranın okuduğu sayaç
   gövdesinde YOKTUR. Bir sayı yazmak için elimizde iki seçenek vardı ve ikisi de
   yalan olurdu: panonun kendi yoklama aralığını "servisin tazeleme zamanı" diye
   göstermek, ya da bir varsayılan uydurmak. Ekran bu yüzden değeri değil
   NEDENİNİ yazıyor ve nerede yaşadığını söylüyor.

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
import { useState } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { useApi } from "../../veri";
import { BolumKart, Deger, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";
import { HamSatirlar, ISO_BENZERI, damga, metin, sayi, sozluk } from "./parcalar";
import type { BankaSayaclari, HafizaOzeti, SeriKovasi, ZamanSerisi } from "./uctipleri";

const UC_OZET = "/api/hindsight/ozet";

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

/* SERİLER — RENK BİR KİMLİK KANALI, BİR HÜKÜM DEĞİL. Panonun grafik rampası
   akromatiktir (tema.css) ve anlamı taşıyan şey ETİKETtir; üst yüzeyin mor/pembe/
   çivit paletini taşımak, panonun rezerve renk bantlarına (mod/gezinme/şiddet)
   girmeden de tasarım dilini bozardı. Taşınan şey düzen ve içerik, piksel değil.

   SEMANTİK ROL ÜST YÜZEYLE AYNI ve sıra da aynı: dünya bilgisi · deneyim · gözlem.
   Yığının sırası bir süs değil — aynı sırayı bilen bir okuyucu iki ekranda aynı
   bandı aynı yerde arar. */
const SERI_YAPISI = {
  world: { label: "Dünya bilgisi", color: "var(--chart-2)" },
  experience: { label: "Deneyim", color: "var(--chart-3)" },
  observation: { label: "Gözlem", color: "var(--chart-5)" },
} satisfies ChartConfig;

const SERI_ANAHTARLARI = ["world", "experience", "observation"] as const;
type SeriAnahtari = (typeof SERI_ANAHTARLARI)[number];

/** Y ekseni kısaltması — üst yüzeyin `formatCompact`inin karşılığı, tr-TR ile. */
function kisaSayi(n: number): string {
  return n.toLocaleString("tr-TR", { notation: "compact", maximumFractionDigits: 1 });
}

/* ---------------------------------------------------------------------------
   SAYAÇ ŞERİDİ
   --------------------------------------------------------------------------- */

function Sayac({ etiket, deger, teknik }: { readonly etiket: string; readonly deger: unknown; readonly teknik: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5 rounded-lg border p-3">
      <span className="text-muted-foreground text-xs">{etiket}</span>
      <span className="font-semibold text-lg">
        <Deger deger={sayi(deger)} neden="Bu sayaç gelmedi" teknik={teknik} />
      </span>
    </div>
  );
}

/**
 * BİR SAYI SÖZLÜĞÜNÜN DAĞILIMI — anahtarlar TELDEN gelir.
 *
 * Üst yüzeyin kendi bileşeni bu sözlüğü ÜÇ ada daraltıyor; üst servisin şeması
 * ise onu açık bir sayı sözlüğü ilan ediyor ve kendi örneğinde BAŞKA adlar
 * kullanıyor. Daraltan taraf, yeni bir tür doğduğu gün onu sessizce düşürür ve
 * parçaların toplamı ile toplam tutmaz. Bu yüzden burada anahtar listesi YOK.
 */
function Dagilim({ govde }: { readonly govde: unknown }) {
  const s = sozluk(govde);
  const hepsi: (readonly [string, number])[] = s
    ? Object.entries(s)
        .map(([k, v]) => [k, sayi(v)] as const)
        .filter((p): p is readonly [string, number] => p[1] !== null)
    : [];
  if (s === null) {
    return <Olculemedi neden="Dağılım gelmedi" teknik="alan sözlük değil ya da hiç gelmedi — şema sürüklenmiş olabilir" />;
  }
  if (hepsi.length === 0) {
    return <p className="text-muted-foreground text-sm">Dağılım okundu ve içi boş geldi — bu ölçülmüş bir boşluktur</p>;
  }
  const tavan = Math.max(...hepsi.map(([, v]) => v), 1);
  return (
    <div className="flex flex-col gap-1.5">
      {hepsi.map(([ad, n]) => (
        <div key={ad} className="flex items-center gap-2">
          <span className="w-32 shrink-0 truncate text-muted-foreground text-xs" title={ad}>
            {ad}
          </span>
          <span className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
            <span className="block h-full rounded-full bg-muted-foreground/50" style={{ width: `${(n / tavan) * 100}%` }} />
          </span>
          <span className="w-16 shrink-0 text-right text-sm tabular-nums">{n.toLocaleString("tr-TR")}</span>
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   TAZELİK — "en son ne oldu" sorusunun ölçülebilen yarısı
   --------------------------------------------------------------------------- */

function Tazelik({ stats }: { readonly stats: BankaSayaclari }) {
  const yazim = damga(stats.last_memory_write_at);
  const birlestirme = damga(stats.last_consolidated_at);
  return (
    <div>
      <Satir etiket="Son yazım">
        {yazim ?? (
          <Olculemedi
            neden={stats.last_memory_write_at === null ? "Bu bankaya henüz kayıt girmemiş" : "Son yazım zamanı okunamadı"}
            teknik="son yazım/düzenleme/birleştirme damgası gelmedi ya da çözülemeyen bir biçimde geldi"
            kisa
          />
        )}
      </Satir>
      <Satir etiket="Son birleştirme">
        {birlestirme ?? (
          <Olculemedi
            neden={stats.last_consolidated_at === null ? "Hiç birleştirme yapılmamış" : "Son birleştirme zamanı okunamadı"}
            teknik="birleştirme damgası gelmedi ya da çözülemeyen bir biçimde geldi"
            kisa
          />
        )}
      </Satir>
      {/* SONRAKİ TAZELEME: değeri değil gerekçesi (dosya başlığındaki şerh). */}
      <Satir etiket="Sonraki tazeleme">
        <Olculemedi
          neden="Sonraki tazeleme zamanı bu okumada gelmiyor"
          teknik="üst yüzey bu değeri zihin modeli tetikleyicilerinden (cron / birleştirme sonrası) türetiyor; o alanlar banka sayaçlarında yok ve ilgili görünüm bu turda çizilmiyor"
          kisa
        />
      </Satir>
      <Satir etiket="Birleştirme kuyruğu">
        <span className="flex flex-wrap items-center justify-end gap-1.5">
          <Badge variant="outline" className="tabular-nums">
            bekleyen <Deger deger={sayi(stats.pending_consolidation)} neden="gelmedi" teknik="bekleyen birleştirme sayacı gelmedi" />
          </Badge>
          <Badge variant="outline" className="tabular-nums">
            düşen <Deger deger={sayi(stats.failed_consolidation)} neden="gelmedi" teknik="düşen birleştirme sayacı gelmedi" />
          </Badge>
        </span>
      </Satir>
      <Satir etiket="Arka plan işleri">
        <span className="flex flex-wrap items-center justify-end gap-1.5">
          <Badge variant="outline" className="tabular-nums">
            bekleyen <Deger deger={sayi(stats.pending_operations)} neden="gelmedi" teknik="bekleyen iş sayacı gelmedi" />
          </Badge>
          <Badge variant="outline" className="tabular-nums">
            düşen <Deger deger={sayi(stats.failed_operations)} neden="gelmedi" teknik="düşen iş sayacı gelmedi" />
          </Badge>
        </span>
      </Satir>
    </div>
  );
}

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
 *  sayıyı da değiştirir ve ikisi ayrı yerlerde dursaydı bağ görünmezdi. */
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
              style={{ backgroundColor: `var(--color-${k})`, opacity: acik[k] ? 1 : 0.3 }}
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

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-anasayfa" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi neden="Okunacak banka seçilemedi" teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor" />
      </BolumKart>
    );
  }

  return (
    <>
      <BolumKart kimlik="hafiza-anasayfa" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <UcKapisi durum={ozet} yol={UC_OZET}>
          {(o) => {
            if (o.stats_neden) return <Olculemedi neden="Banka sayaçları okunamadı" teknik={o.stats_neden} />;
            if (o.stats === undefined) return <Olculemedi neden="Sayaçlar bildirilmedi" teknik="uç sayaç bacağını hiç döndürmedi" />;
            if (o.stats === null) {
              return <Olculemedi neden="Ölçüm denendi, sayaçlar gelmedi" teknik="sayaç alanı boş döndü ve gerekçe de taşınmadı" />;
            }
            const s = o.stats;
            return (
              <>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <Sayac etiket="Kayıt" deger={s.total_nodes} teknik="toplam kayıt sayacı gelmedi ya da sayı değil" />
                  <Sayac etiket="Belge" deger={s.total_documents} teknik="toplam belge sayacı gelmedi ya da sayı değil" />
                  <Sayac etiket="Bağ" deger={s.total_links} teknik="toplam bağ sayacı gelmedi ya da sayı değil" />
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Kayıt bileşimi</h3>
                    {/* GÖZLEM SAYACI BURAYA EKLENMEZ — VE İLK YAZIM EKLİYORDU
                        (düzeltme turu 1, inceleme bulgusu I-1). Şerh "gözlem türü
                        dağılımın içinde gelmiyor" diyordu; canlı ölçüm bunu ÇÜRÜTTÜ:
                        tür dağılımı `experience`/`observation`/`world` anahtarlarını
                        TAŞIYOR. Eklemek aynı adı listeye iki kez koyuyordu — ekranda
                        aynı etiketle iki çubuk, üstelik tekrarlı bir React anahtarı.
                        Toplam gözlem sayacı aşağıdaki ham satırlarda görünür. */}
                    <Dagilim govde={s.nodes_by_fact_type} />
                  </div>
                  <div className="flex flex-col gap-2">
                    <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Bağ türleri</h3>
                    <Dagilim govde={s.links_by_link_type} />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Tazelik</h3>
                    <Tazelik stats={s} />
                  </div>
                  <div className="flex flex-col gap-2">
                    <h3 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Sayaç gövdesinin tamamı</h3>
                    {/* Yukarıda ÇİZİLEN alanlar burada tekrarlanmaz; geri kalan her
                        anahtar ham basılır, böylece tanımadığımız bir alan ekrandan
                        sessizce düşmez. */}
                    <HamSatirlar
                      govde={s}
                      atla={[
                        "total_nodes", "total_documents", "total_links", "nodes_by_fact_type",
                        "links_by_link_type", "last_memory_write_at",
                        "last_consolidated_at", "pending_consolidation", "failed_consolidation",
                        "pending_operations", "failed_operations",
                      ]}
                    />
                  </div>
                </div>
              </>
            );
          }}
        </UcKapisi>
      </BolumKart>

      <BolumKart
        kimlik="hafiza-akis"
        baslik="Hafızaya giren kayıtlar"
        soru="Seçilen pencerede ne kadar yazıldı, hangi türden?"
        ikon={kayit.ikon}
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
    </>
  );
}
