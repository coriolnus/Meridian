"use client";

/* ============================================================================
   AÇIK POZİSYONLARIN SEYRİ — bütün pozisyonlar TEK grafikte, GİRİŞE GÖRE YÜZDE
   ----------------------------------------------------------------------------
   ÜSTTEKİ GRAFİKLE AYNI SORUYU SORMUYOR ve ikisi de kalıyor:
     · `PozisyonGrafigi` (yatay çubuk) → "ŞU AN ne kadar?" — TUTAR kanalı, tek an.
     · Bu grafik                       → "ZAMAN İÇİNDE nasıl gitti?" — YÜZDE kanalı,
       giriş anından bugüne. Tutarı buraya bindirmek 50.000$'lık bir pozisyonla
       500$'lığı aynı çizgiye indirir; yüzdeyi öbürüne bindirmek sermayenin nerede
       durduğunu kaybettirirdi. İki soru, iki kart.

   YÜZDENİN TABANI GİRİŞTİR, pencerenin ilk kapanışı DEĞİL: `(kapanış / giriş - 1) × 100`.
   Pencerenin başına göre normalize etmek, "bu pozisyonda ne kazandık?" sorusunu
   "bu hisse 90 günde ne yaptı?" sorusuyla değiştirirdi — ikincisi bizim seyrimiz değil.
   Bu yüzden `ReferenceLine y={0}` grafiğin ANLAM MERKEZİDİR: üstü kâr, altı zarar.

   GİRİŞTEN ÖNCEKİ SEANSLAR ÇİZİLMEZ (`t < açılış` → null, `connectNulls={false}`).
   Pozisyonu almadan önceki fiyat hareketi bizim seyrimiz değil; onu çizmek, hiç
   maruz kalmadığımız bir dalgalanmayı portföyün geçmişi gibi göstermek olurdu.

   KESİKLİ SERİ = KİTAP ORTALAMASI ve EŞİT AĞIRLIKLIDIR (ekranda da beyan ediliyor):
   o tarihte verisi olan pozisyonların yüzdelerinin düz ortalaması. Piyasa değeriyle
   ağırlıklandırmak BUGÜNÜN ağırlıklarını GEÇMİŞE uygulamak olurdu — pozisyonlar farklı
   günlerde ve farklı büyüklüklerde açıldı, o ağırlık serisi hiç ölçülmedi. Ölçülmemiş
   bir varsayımı grafiğe gömmektense düz ortalamayı BEYAN ederek çizmek dürüst olan.

   VERİ: her sembol için `/api/bars/{ticker}?n=90` (marketview.py::bar_serisi). O uç
   BİLİNMEYEN SEMBOLDE 404 DÖNMEZ — `bar: null` + `neden` döner; burada da ekranda
   öyle çizilir: sembol düşer, NEDENİ listelenir. Sessizce eksilen bir grafik,
   portföyü olduğundan iyi/kötü gösterir.
   ============================================================================ */
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart";

import { apiGet, OturumHatasi } from "../../veri";
import type { PozisyonSatiri } from "./birlestir";
import { sayi, yuzde } from "./olcum";

/** 90 SEANS ≈ dört buçuk ay. Alt sınır anlamdan: bu kitapta pozisyonlar haftalarca
 *  tutuluyor (`bars_held`), 20 seanslık bir pencere en eski pozisyonun girişini
 *  pencerenin dışında bırakır ve sembol sessizce düşerdi. Üst sınır yükten: uç
 *  tavanı 500 (api.py::api_bars) ve N sembol × 500 bar her tazelemede ödenirdi. */
const PENCERE_BAR = 90;

/** TAZELEME YAVAŞ ve bu bilinçli: `/api/bars` EOD servis eder (marketview.py::bar_serisi
 *  şerhi — "İKİSİ DE EOD'dur"), yani kaynak veri GÜNDE BİR değişir. 15 saniyelik panonun nabzına bağlamak
 *  N paralel isteği dakikada dörtle çarpar ve karşılığında AYNI seriyi geri getirirdi.
 *  Beş dakika, günde bir değişen bir veriyi zaten 288 kez sormak demek. */
const TAZELEME_MS = 300_000;

/** Rampa `tema.css`te ON jetonla tanımlı (`--color-seri-1..10`). Onuncudan sonra döner
 *  ve DÖNDÜĞÜ EKRANDA YAZAR — renk burada bir kimlik kanalıdır, sessizce tekrarlanamaz. */
const RAMPA_N = 10;

/** X ekseninde her ~10 seansta bir etiket. recharts `interval` ATLANACAK tick sayısıdır,
 *  yani 9 atlamak "onda birini yaz" demektir. 90 seansın 90 etiketi eksende okunmaz
 *  mürekkebe döner; seyrek etiket tarihi kaybettirmez (tooltip tam tarihi taşıyor). */
const ETIKET_ATLA = 9;

/** Tek noktalı serinin nokta yarıçapı. NEDEN NOKTA GEREKİYOR: recharts çizgiyi d3
 *  `line()` ile üretir ve TEK non-null noktada `M x,y Z` yazar — sıfır uzunluklu bir
 *  alt-yol, `stroke-linecap: butt` ile HİÇ boyanmaz. Yani "çizildi" sayılan seri
 *  ekranda yoktur. Nokta yalnız o durumda açılır: 90 seansın hepsini noktalamak
 *  grafiği okunmaz mürekkebe çevirirdi. */
const TEK_NOKTA_R = 3;

/** ChartContainer `config` İSTİYOR ama bu grafikte yapacak işi YOK ve nedeni yazılı olsun:
 *  config'in tek işlevi `--color-<anahtar>` değişkenleri üretmek (chart.tsx::ChartStyle);
 *  burada renk doğrudan `var(--color-seri-N)` olarak çizgiye veriliyor, çünkü seri anahtarı
 *  sembolden türetilseydi "BRK.B" gibi bir ad geçersiz bir CSS değişken adı üretirdi.
 *  Tooltip ve gösterge de bu dosyanın kendi bileşenleri — config'ten etiket okumuyorlar. */
const GRAFIK_CONFIG = {} satisfies ChartConfig;

// ---------------------------------------------------------------------------
// UÇ SÖZLEŞMESİ — `marketview.py::bar_serisi()` OKUNARAK yazıldı, tahmin yok
// ---------------------------------------------------------------------------
/** Tek bar. `c` (kapanış) `_f()`ten geçiyor ve sayı ya da null; yine de `sayi()` kapısından
 *  geçiriyoruz — bu dosyanın tek ayrıştırma kapısı o. */
interface BarNoktasi {
  readonly t?: string;
  readonly c?: unknown;
}

interface BarGovdesi {
  readonly ticker?: string;
  readonly istenen_n?: number;
  readonly n?: number;
  readonly kirpildi?: boolean;
  /** DÖNEN serinin son seansı — "canlı fiyat" değil, ölçümün nereye kadar gittiği. */
  readonly as_of?: string | null;
  /** `null` = seri YOK ve `neden` doludur. Boş dizi DEĞİL: yokluk ile durgunluk ayrı. */
  readonly bar?: readonly BarNoktasi[] | null;
  readonly neden?: string | null;
}

interface SeriDurumu {
  readonly govde: BarGovdesi | null;
  readonly hata: string | null;
  readonly oturumDustu: boolean;
}

type SeriHaritasi = Readonly<Record<string, SeriDurumu>>;

// ---------------------------------------------------------------------------
// ÇİZİM MODELİ
// ---------------------------------------------------------------------------
interface CizimSerisi {
  readonly ticker: string;
  /** recharts `dataKey`i. SEMBOL DEĞİL ve bu bir tuzaktan kaçış: recharts dataKey'i
   *  NOKTALI YOL olarak çözüyor (`getValueByDataKey` → `get(obj, key)`), yani "BRK.B"
   *  nesnede `obj.BRK.B` aranır ve seri sessizce boş çizilirdi. Sentetik anahtar bu
   *  sınıfın tamamını kapatıyor; sembol `name` alanında taşınıyor. */
  readonly anahtar: string;
  readonly renk: string;
  /** Rampa döndüyse (10'dan fazla pozisyon) bu seri BİR RENGİ PAYLAŞIYOR demektir. */
  readonly rampaTekrari: boolean;
  readonly sonYuzde: number | null;
  readonly ilkSeans: string;
  readonly seansSayisi: number;
  /** HAM serinin ÖLÇÜLEN son seansı (girişe göre süzülmeden önce). Tek noktalı bir seride
   *  "seri burada bitiyor" demenin TEK kanıtı bu: `ilkSeans`e eşitse seri gerçekten orada
   *  bitiyordur, değilse seri devam ediyor ve nokta başka bir nedenle tek kalmıştır.
   *  Tarihi okunabilen tek bar yoksa `null` — o durumda hiçbir iddia basılmaz. */
  readonly sonBarTarihi: string | null;
  /** Girişten sonraki barlardan kaçının kapanışı sayıya ÇEVRİLEMEDİĞİ. Sessizce düşen bar
   *  "o gün fiyat yoktu" diye okunurdu; sayılıp ekrana basılıyor. */
  readonly kapanissizBar: number;
  /** Yüzdenin TABANI hangi defterden okundu. Ekrandaki beyan bunu SAYAR; sabit bir
   *  cümle, taban dağılımı değiştiği gün sessizce yalan söylerdi. */
  readonly girisKaynak: PozisyonSatiri["girisKaynak"];
  /** Giriş, 90 seanslık pencerenin BAŞINDAN da eskiyse çizgi girişte değil pencerenin
   *  başında başlar. Yüzdenin tabanı yine giriştir (yani değer doğrudur), ama çizginin
   *  SOL UCU "burada aldık" demek DEĞİLDİR — bu ayrım ekranda yazılır. */
  readonly girisPencereOncesi: boolean;
}

interface Dusen {
  readonly ticker: string;
  readonly neden: string;
}

/** Grafiğin bir X noktası. `t` seans tarihi; her seri kendi sentetik anahtarında
 *  yüzdesini taşır, o tarihte verisi yoksa `null` (recharts boşluk çizer). */
interface Nokta {
  t: string;
  ortalama: number | null;
  [anahtar: string]: number | string | null;
}

interface Cizim {
  readonly veri: readonly Nokta[];
  readonly seriler: readonly CizimSerisi[];
  readonly dusenler: readonly Dusen[];
  readonly alan: readonly [number, number];
  readonly ilkSeans: string | null;
  readonly sonSeans: string | null;
}

const BOS_CIZIM: Cizim = { veri: [], seriler: [], dusenler: [], alan: [-1, 1], ilkSeans: null, sonSeans: null };

const TARIH_DESENI = /^\d{4}-\d{2}-\d{2}$/;
const EKSEN_SAYI = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });

/** Eksen etiketi: Türkçede yüzde işareti sayının ÖNÜNDE, eksi işareti yüzdenin önünde. */
function yuzdeEksen(v: number): string {
  return `${v < 0 ? "-" : ""}%${EKSEN_SAYI.format(Math.abs(v))}`;
}

/** "2026-08-14" → "14.08". Seyrek etiket için gün+ay yeter; yıl tooltip'te tam duruyor. */
function gunAy(t: string): string {
  return `${t.slice(8, 10)}.${t.slice(5, 7)}`;
}

function gunAyYil(t: string): string {
  return `${t.slice(8, 10)}.${t.slice(5, 7)}.${t.slice(0, 4)}`;
}

// ---------------------------------------------------------------------------
// TOOLTIP — kendi içeriğimiz, ÇÜNKÜ shadcn'in `ChartTooltipContent`i sayıyı
// `toLocaleString()` ile basıyor: yüzde işareti ve işaret öneki kaybolur, üstelik
// tarayıcı yereline göre "5.83"/"5,83" ayrışır. `ChartTooltip` (recharts Tooltip)
// aynen kullanılıyor; değişen yalnız gövdenin çizimi.
// `filterNull` recharts'ta varsayılan olarak AÇIK — o tarihte verisi olmayan seri
// (girişten önceki seanslar) tooltip'e hiç girmiyor, yani "null" satırı çizilmiyor.
// ---------------------------------------------------------------------------
interface TooltipSatiri {
  readonly name?: number | string;
  readonly value?: number | string | ReadonlyArray<number | string>;
  readonly color?: string;
}

function SeyirTooltip({
  active,
  label,
  payload,
}: {
  readonly active?: boolean;
  readonly label?: unknown;
  readonly payload?: readonly TooltipSatiri[];
}) {
  if (active !== true || !payload || payload.length === 0) return null;
  const satirlar = payload
    .map((p) => ({
      ad: typeof p.name === "string" ? p.name : null,
      v: typeof p.value === "number" && Number.isFinite(p.value) ? p.value : null,
      renk: typeof p.color === "string" ? p.color : null,
    }))
    .filter((r): r is { ad: string; v: number; renk: string | null } => r.ad !== null && r.v !== null)
    .sort((a, b) => b.v - a.v);
  if (satirlar.length === 0) return null;
  const tarih = typeof label === "string" && TARIH_DESENI.test(label) ? gunAyYil(label) : null;

  return (
    <div className="grid min-w-40 items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl">
      {/* TARİH OKUNAMADIYSA UYDURULMAZ: eksenin verdiği etiket beklenen biçimde
          değilse başlık yerine bunu yazmak, yanlış bir güne bakıyor olma ihtimalini
          okuyucudan saklamamak demek. */}
      <div className="font-medium">{tarih ?? "seans tarihi okunamadı"}</div>
      <div className="grid gap-1.5">
        {satirlar.map((r) => (
          <div className="flex w-full items-center gap-2" key={r.ad}>
            <span
              className="size-2.5 shrink-0 rounded-[2px]"
              style={r.renk === null ? undefined : { backgroundColor: r.renk }}
            />
            <span className="flex-1 text-muted-foreground">{r.ad}</span>
            <span className="font-medium font-mono tabular-nums">{yuzde(r.v)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// BİLEŞEN
// ---------------------------------------------------------------------------
export function PozisyonSeyri({ satirlar }: { satirlar: readonly PozisyonSatiri[] }) {
  const [barlar, setBarlar] = useState<SeriHaritasi | null>(null);
  const [tur, setTur] = useState(0);

  /* SEMBOL LİSTESİ SKALER BİR ANAHTARA İNDİRİLİYOR ve bu şart: `satirlar` bu yüzeyde
     15 saniyelik nabızla YENİDEN KURULUYOR (birlestir() her yanıtta yeni dizi üretir).
     Diziyi doğrudan bağımlılığa koysaydık N paralel bar isteği 15 saniyede bir
     tekrarlanırdı — hem yükü hem de "TEK sefer + yavaş tazeleme" sözleşmesini kırardı.
     Dizge yalnız sembol KÜMESİ değiştiğinde değişir (pozisyon açıldı/kapandı). */
  const tickerAnahtari = useMemo(() => [...satirlar.map((s) => s.ticker)].sort().join(","), [satirlar]);

  /* Giriş fiyatı ve açılış tarihi de aynı sebeple imzaya indirildi: onlar DEĞİŞTİĞİNDE
     çizim yeniden hesaplanmalı (yüzdenin tabanı değişti), ama nabzın her turunda değil. */
  const metaImza = useMemo(
    () => satirlar.map((s) => `${s.ticker}|${s.giris ?? ""}|${s.acilis ?? ""}`).join(";"),
    [satirlar],
  );

  useEffect(() => {
    const tickerlar = tickerAnahtari === "" ? [] : tickerAnahtari.split(",");
    if (tickerlar.length === 0) {
      setBarlar({});
      return;
    }
    let canli = true;
    const kontrol = new AbortController();

    /* N İSTEK PARALEL: sıraya dizmek 7 sembolde 7 gidiş-dönüş demekti ve grafiğin ilk
       karesi o kadar gecikirdi. `Promise.all` burada güvenli çünkü HİÇBİR dal reject
       ETMİYOR — her sembol kendi hatasını DEĞER olarak döndürüyor; bir sembolün düşmesi
       diğer altısının serisini çöpe atmaz. */
    void Promise.all(
      tickerlar.map(async (t): Promise<readonly [string, SeriDurumu]> => {
        try {
          const g = await apiGet<BarGovdesi>(
            `/api/bars/${encodeURIComponent(t)}?n=${PENCERE_BAR}`,
            kontrol.signal,
          );
          return [t, { govde: g, hata: null, oturumDustu: false }];
        } catch (e) {
          if (e instanceof OturumHatasi) {
            return [t, { govde: null, hata: "/api/bars 401 döndü — oturum düştü", oturumDustu: true }];
          }
          return [t, { govde: null, hata: e instanceof Error ? e.message : String(e), oturumDustu: false }];
        }
      }),
    ).then((ciftler) => {
      // İPTAL EDİLMİŞ TURUN SONUCU YAZILMAZ: sembol listesi değiştiğinde eski turun
      // yanıtları hâlâ yoldadır ve onları yazmak, artık portföyde olmayan bir sembolün
      // serisini ekrana geri getirirdi.
      if (!canli || kontrol.signal.aborted) return;
      setBarlar(Object.fromEntries(ciftler));
    });

    return () => {
      canli = false;
      kontrol.abort();
    };
  }, [tickerAnahtari, tur]);

  useEffect(() => {
    const z = window.setInterval(() => setTur((n) => n + 1), TAZELEME_MS);
    return () => window.clearInterval(z);
  }, []);

  /* ÇİZİM TEK BİR useMemo'DA ve bağımlılıkları SKALER: `satirlar` kapanıştan okunuyor
     (dizi kimliği her nabızda değişiyor, İÇERİĞİ değişmiyor). İçerik değiştiğinde
     `metaImza` da değişir, yani bayat bir çizim ihtimali yok. Bu dizinin kimliğini
     nabızla birlikte yenilemek recharts'ta ölçülmüş bir kusur üretiyor (giriş
     animasyonunun başa sarması — PozisyonGrafigi.tsx::PozisyonGrafigi şerhi); animasyon burada da
     kapalı, ama diziyi sabitlemek hem çizimi hem de gereksiz React işini kesiyor. */
  const cizim: Cizim = useMemo(() => {
    if (barlar === null) return BOS_CIZIM;

    interface Aday {
      readonly ticker: string;
      readonly noktalar: ReadonlyMap<string, number>;
      readonly ilkSeans: string;
      readonly sonYuzde: number;
      readonly girisPencereOncesi: boolean;
      readonly girisKaynak: PozisyonSatiri["girisKaynak"];
      readonly sonBarTarihi: string | null;
      readonly kapanissizBar: number;
    }
    const adaylar: Aday[] = [];
    const dusenler: Dusen[] = [];

    for (const s of satirlar) {
      const d = barlar[s.ticker];
      if (d === undefined) {
        dusenler.push({ ticker: s.ticker, neden: "bar isteği bu sembol için henüz dönmedi" });
        continue;
      }
      if (d.hata !== null || d.govde === null) {
        dusenler.push({ ticker: s.ticker, neden: d.hata ?? "/api/bars gövdesi boş döndü" });
        continue;
      }
      const g = d.govde;
      const bar = g.bar;
      if (!Array.isArray(bar) || bar.length === 0) {
        // UCUN KENDİ NEDENİ ÖNCE: "bar dosyası yok", "biçim bozuk" gibi cümleleri o
        // yazıyor ve okuyucuyu doğru yere gönderiyor. Kendi cümlemizi üstüne yazmak
        // teşhisi silmek olurdu.
        dusenler.push({ ticker: s.ticker, neden: g.neden ?? "`bar` alanı boş ve uç neden yazmadı" });
        continue;
      }
      const giris = s.giris;
      if (giris === null) {
        dusenler.push({
          ticker: s.ticker,
          neden: "giriş fiyatı ölçülemedi (ne broker `avg_entry` ne kitap `entry`) — yüzdenin paydası yok",
        });
        continue;
      }
      if (giris <= 0) {
        dusenler.push({ ticker: s.ticker, neden: `giriş fiyatı ${giris} — yüzdenin paydası olamaz` });
        continue;
      }
      const acilis = s.acilis;
      const acilisGun = acilis === null ? null : acilis.slice(0, 10);
      if (acilisGun === null || !TARIH_DESENI.test(acilisGun)) {
        dusenler.push({
          ticker: s.ticker,
          // BROKER-ONLY SATIRIN NEDENİ AYRI YAZILIR ve bu bir üslup tercihi değil, TEŞHİS
          // farkı: `birlestir()` açılış damgasını YALNIZ kitap satırından okur (`ts_open`),
          // çünkü `BrokerPozisyonu` (tipler.ts) symbol/qty/avg_entry/current/upl taşır —
          // tarih alanı YOKTUR. Yalnız aynada duran bir pozisyon bu yüzden HİÇBİR ZAMAN
          // çizilemez. Okuyucuyu "bar dosyası eksik" diye bar ucuna göndermek, olmayan bir
          // veri boşluğunu aratmak olurdu.
          neden:
            acilis !== null
              ? `açılış damgası tarihe çevrilemedi ("${acilis}") — girişten önceki seanslar ayıklanamadı`
              : s.nerede === "yalniz-broker"
                ? "yalnız BROKER aynasında var ve aynada AÇILIŞ DAMGASI yok — ayna satırı symbol/qty/avg_entry/current/upl taşır, tarih taşımaz. Seyir GİRİŞTEN İTİBAREN çizilir; giriş tarihi olmayan pozisyon çizilemez. Bu bir bar eksiği DEĞİL, aynanın şeklinden gelen YAPISAL bir eksik — bar dosyasına bakmak boşuna."
                : "kitap satırında ts_open alanı yok — girişten önceki seanslar ayıklanamadığı için seri ÇİZİLMEDİ",
        });
        continue;
      }

      const noktalar = new Map<string, number>();
      let sonYuzde: number | null = null;
      let ilkBarTarihi: string | null = null;
      let sonBarTarihi: string | null = null;
      let kapanissizBar = 0;
      for (const b of bar) {
        const t = typeof b.t === "string" ? b.t : null;
        // SESSİZ YUTMA (bilinçli): tarihi okunamayan bar `kapanissizBar` kovasına DA
        // yazılmıyor, çünkü o kova "GİRİŞTEN SONRAKİ" barları sayıyor ve tarihsiz bir barın
        // girişten önce mi sonra mı olduğu bilinmiyor — sayarsak ekrana ölçmediğimiz bir
        // iddia basmış oluruz. Tarihsiz bar, tarih taşıyan komşularının arasında yok sayılır.
        if (t === null || !TARIH_DESENI.test(t)) continue;
        if (ilkBarTarihi === null) ilkBarTarihi = t;
        // HAM SERİNİN SON SEANSI, GİRİŞ SÜZGECİNDEN ÖNCE ölçülüyor: tek noktalı bir seride
        // "bar serisi burada bitiyor" iddiasının tek kanıtı bu. Süzgeçten sonra ölçseydik
        // her tek noktalı seri kendini "seri bitti" diye ilan ederdi — döngüsel kanıt.
        sonBarTarihi = t;
        // GİRİŞTEN ÖNCESİ ÇİZİLMEZ. ISO tarihler sözlüksel olarak da kronolojiktir,
        // yani dizge karşılaştırması burada tarih karşılaştırmasıdır (Date kurmak
        // saat dilimi hatası riski getirirdi, karşılığında hiçbir şey vermeden).
        if (t < acilisGun) continue;
        const kapanis = sayi(b.c);
        if (kapanis === null) {
          // SESSİZ YUTMA DEĞİL: kapanışı okunamayan bar SAYILIYOR ve tek noktalı seride
          // ekrana basılıyor — sayılmasaydı "o gün fiyat yoktu" diye okunurdu.
          kapanissizBar += 1;
          continue;
        }
        const y = (kapanis / giris - 1) * 100;
        noktalar.set(t, y);
        sonYuzde = y;
      }

      if (noktalar.size === 0 || sonYuzde === null) {
        const ilkBar = bar[0]?.t ?? "?";
        const sonBar = bar[bar.length - 1]?.t ?? "?";
        dusenler.push({
          ticker: s.ticker,
          neden: `giriş tarihi ${acilisGun} pencerenin DIŞINDA — ${PENCERE_BAR} barlık seri ${ilkBar} → ${sonBar} arasını kapsıyor (${g.n ?? 0} seans)`,
        });
        continue;
      }

      const ilkSeans = [...noktalar.keys()].sort()[0] ?? acilisGun;
      adaylar.push({
        ticker: s.ticker,
        noktalar,
        ilkSeans,
        sonYuzde,
        girisPencereOncesi: ilkBarTarihi !== null && acilisGun < ilkBarTarihi,
        girisKaynak: s.girisKaynak,
        sonBarTarihi,
        kapanissizBar,
      });
    }

    if (adaylar.length === 0) return { ...BOS_CIZIM, dusenler };

    // SIRA EN ESKİ GİRİŞTEN YENİYE: renk rampası ve gösterge aynı sırayı taşır, yani
    // gözle takip edilebilir bir düzen olur. Alfabetik sıra, aynı gün açılmış iki
    // pozisyonu grafiğin iki ucuna atardı.
    adaylar.sort((a, b) => (a.ilkSeans === b.ilkSeans ? a.ticker.localeCompare(b.ticker) : a.ilkSeans < b.ilkSeans ? -1 : 1));

    const seriler: CizimSerisi[] = adaylar.map((a, i) => ({
      ticker: a.ticker,
      anahtar: `p${i}`,
      renk: `var(--color-seri-${(i % RAMPA_N) + 1})`,
      rampaTekrari: i >= RAMPA_N,
      sonYuzde: a.sonYuzde,
      ilkSeans: a.ilkSeans,
      seansSayisi: a.noktalar.size,
      girisPencereOncesi: a.girisPencereOncesi,
      girisKaynak: a.girisKaynak,
      sonBarTarihi: a.sonBarTarihi,
      kapanissizBar: a.kapanissizBar,
    }));

    const tarihler = [...new Set(adaylar.flatMap((a) => [...a.noktalar.keys()]))].sort();

    let enAz = 0;
    let enCok = 0;
    const veri: Nokta[] = tarihler.map((t) => {
      const n: Nokta = { t, ortalama: null };
      let toplam = 0;
      let adet = 0;
      for (let i = 0; i < adaylar.length; i += 1) {
        const a = adaylar[i];
        const seri = seriler[i];
        if (a === undefined || seri === undefined) continue;
        const v = a.noktalar.get(t);
        if (v === undefined) {
          n[seri.anahtar] = null;
          continue;
        }
        n[seri.anahtar] = v;
        toplam += v;
        adet += 1;
        if (v < enAz) enAz = v;
        if (v > enCok) enCok = v;
      }
      // EŞİT AĞIRLIKLI ORTALAMA — payda O TARİHTE verisi olan pozisyon sayısı.
      // Sabit paydaya (toplam pozisyon) bölmek, henüz açılmamış pozisyonları "0%"
      // sayardı ve ortalamayı sıfıra doğru yalancı bir şekilde çekerdi.
      if (adet > 0) n.ortalama = toplam / adet;
      return n;
    });

    /* ALAN AÇIKÇA YAZILIYOR VE SIFIRI HER ZAMAN İÇERİYOR: bu grafiğin anlam merkezi
       giriş çizgisi. Hepsi kârdaysa recharts'ın seçeceği alan sıfırı dışarıda bırakır
       ve "hepsi kârda" bilgisi ekrandan kaybolurdu — çizgiler yine dalgalanır, ama
       neye göre olduğu görünmezdi. ±1 puanlık pay, en uçtaki çizginin kenara
       yapışmasını engelliyor. */
    const alan: readonly [number, number] = [Math.floor(enAz) - 1, Math.ceil(enCok) + 1];

    return {
      veri,
      seriler,
      dusenler,
      alan,
      ilkSeans: tarihler[0] ?? null,
      sonSeans: tarihler[tarihler.length - 1] ?? null,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `satirlar` BİLEREK dışarıda: kimliği her nabızda değişiyor, içeriği `metaImza`da.
  }, [barlar, metaImza]);

  const oturumDustu = barlar !== null && Object.values(barlar).some((d) => d.oturumDustu);
  const rampaDondu = cizim.seriler.some((s) => s.rampaTekrari);
  const pencereOncesi = cizim.seriler.filter((s) => s.girisPencereOncesi);

  /* SAYAÇ ÜÇ KOVA — ADAY OLMAK ÇİZİLMEK DEĞİLDİR. Girişi pencerenin son seansında olan
     bir pozisyonun serisi TEK NOKTALIDIR ve recharts onu sıfır piksel çizer (TEK_NOKTA_R
     şerhi). Eski sayaç onları "çizildi" kovasına yazıyordu: ekranda yedi çizgi varken
     kutu dokuz diyordu. Üçüncü kova (hiç aday olamayanlar) zaten vardı. */
  const tekSeanslik = cizim.seriler.filter((s) => s.seansSayisi < 2);
  const cizilenCizgi = cizim.seriler.length - tekSeanslik.length;

  /* TABAN BEYANI ÖLÇÜMDEN BESLENİR: taban satır satır broker `avg_entry` ya da kitap
     `entry` olabilir (`birlestir()`), ve iki defterin girişi AYRIŞIYOR. Sabit bir cümle,
     dağılım değiştiği gün sessizce yalan söylerdi — bu yüzden sayılıyor. */
  const tabanBroker = cizim.seriler.filter((s) => s.girisKaynak === "broker").length;
  const tabanKitap = cizim.seriler.filter((s) => s.girisKaynak === "kitap").length;
  const yukseklik = 340;

  if (satirlar.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Açık pozisyon yok — çizilecek seyir de yok. Bu bir ölçüm eksiği değil, ölçülmüş bir olgu.
      </p>
    );
  }

  if (barlar === null) {
    return (
      <p className="text-muted-foreground text-sm">
        {satirlar.length} pozisyonun bar serisi çekiliyor (`/api/bars?n={PENCERE_BAR}`, sembol başına bir istek)…
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {oturumDustu && (
        <p className="text-amber-600 text-sm dark:text-amber-400">
          En az bir bar isteği 401 döndü — OTURUM DÜŞTÜ. Aşağıdaki eksiklik "veri yok" değil, "sorulamadı"
          demektir; yeniden giriş yapılmalı.
        </p>
      )}

      {cizim.seriler.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          {satirlar.length} pozisyonun HİÇBİRİ çizilemedi — nedenleri aşağıda satır satır duruyor.
        </p>
      ) : (
        <ChartContainer className="aspect-auto w-full" config={GRAFIK_CONFIG} style={{ height: yukseklik }}>
          <LineChart accessibilityLayer data={cizim.veri} margin={{ bottom: 4, left: 4, right: 12, top: 8 }}>
            <CartesianGrid stroke="var(--border)" strokeOpacity={0.6} vertical={false} />
            <XAxis
              axisLine={false}
              dataKey="t"
              interval={ETIKET_ATLA}
              tickFormatter={gunAy}
              tickLine={false}
              tickMargin={8}
            />
            <YAxis
              axisLine={false}
              domain={[cizim.alan[0], cizim.alan[1]]}
              tickFormatter={yuzdeEksen}
              tickLine={false}
              width={52}
            />
            {/* SIFIR ÇİZGİSİ = GİRİŞ. Etiketli, çünkü etiketsiz bir yatay çizgi
                "eksen" diye okunur; bu çizgi bir eksen değil, bir EŞİK. */}
            <ReferenceLine
              label={{ fill: "var(--muted-foreground)", fontSize: 11, position: "insideTopLeft", value: "giriş" }}
              stroke="var(--muted-foreground)"
              strokeWidth={1}
              y={0}
            />
            <ChartTooltip content={<SeyirTooltip />} cursor={{ stroke: "var(--border)" }} />
            {cizim.seriler.map((s) => (
              /* `type="linear"`: iki seans ARASINDA fiyat ölçülmedi. `monotone` oraya
                 yumuşak bir eğri uydurur ve ölçülmemiş bir yol çizer. Düz parça,
                 "bu iki nokta ölçüldü, arası bilinmiyor" demenin en dürüst biçimi. */
              <Line
                connectNulls={false}
                dataKey={s.anahtar}
                dot={s.seansSayisi < 2 ? { fill: s.renk, r: TEK_NOKTA_R, stroke: s.renk } : false}
                isAnimationActive={false}
                key={s.anahtar}
                name={s.ticker}
                stroke={s.renk}
                strokeWidth={1.75}
                type="linear"
              />
            ))}
            {/* KESİKLİ = TÜRETİLMİŞ. Düz çizgiler ölçülmüş tek bir pozisyonun seyri;
                bu çizgi hiçbir pozisyon değil, onların ortalaması. Kesik desen bu
                farkı renk kullanmadan söylüyor (renk kanalı kimliğe ayrılmış). */}
            <Line
              connectNulls={false}
              dataKey="ortalama"
              dot={
                cizim.veri.length < 2
                  ? { fill: "var(--muted-foreground)", r: TEK_NOKTA_R, stroke: "var(--muted-foreground)" }
                  : false
              }
              isAnimationActive={false}
              name="Kitap ortalaması (eşit ağırlıklı)"
              stroke="var(--muted-foreground)"
              strokeDasharray="6 4"
              strokeWidth={1.75}
              type="linear"
            />
          </LineChart>
        </ChartContainer>
      )}

      {/* ---- GÖSTERGE: sembol + SON yüzde ---------------------------------- */}
      {cizim.seriler.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t pt-3 text-xs">
          {cizim.seriler.map((s) => (
            <span className="flex items-center gap-1.5" key={s.anahtar}>
              <span className="size-2.5 rounded-[2px]" style={{ backgroundColor: s.renk }} />
              <span className="font-medium">{s.ticker}</span>
              <span className="text-muted-foreground tabular-nums">
                {s.sonYuzde === null ? "ölçülemedi" : yuzde(s.sonYuzde)}
              </span>
            </span>
          ))}
          <span className="flex items-center gap-1.5">
            <span className="h-0 w-4 border-muted-foreground border-t-2 border-dashed" />
            <span className="text-muted-foreground">kitap ortalaması (eşit ağırlıklı)</span>
          </span>
        </div>
      )}

      {/* ---- SÖZLEŞMENİN EKRANDAKİ BEYANI ---------------------------------- */}
      <p className="text-muted-foreground text-xs leading-relaxed">
        Y ekseni GİRİŞE göre yüzde: (kapanış / giriş − 1) × 100; sıfır çizgisi giriş fiyatıdır. Girişten önceki
        seanslar çizilmez. Kesikli çizgi kitap ortalamasıdır ve EŞİT AĞIRLIKLIDIR — piyasa değeriyle
        ağırlıklandırmak bugünün ağırlıklarını geçmişe uygulamak, yani ölçülmemiş bir varsayımı grafiğe gömmek
        olurdu.{" "}
        {cizim.ilkSeans !== null && cizim.sonSeans !== null
          ? `Pencere ${gunAyYil(cizim.ilkSeans)} → ${gunAyYil(cizim.sonSeans)} (${cizim.veri.length} seans), kaynak /api/bars?n=${PENCERE_BAR} — EOD kapanış, canlı fiyat değil.`
          : `Kaynak /api/bars?n=${PENCERE_BAR} — EOD kapanış, canlı fiyat değil.`}{" "}
        TABAN: yüzdenin paydası satırın giriş fiyatıdır ve bu, tablodaki "Giriş" sütunuyla AYNI alandır — broker
        avg_entry varsa o, yoksa kitap entry (bu grafikte {tabanBroker} seri broker, {tabanKitap} seri kitap
        tabanlı). Tablodaki "K/Z %" ile buradaki yüzde AYNI OLMAK ZORUNDA DEĞİL, ve fark tabandan değil PAYDAN
        gelir: buradaki pay /api/bars EOD KAPANIŞI, tablodaki pay broker current son fiyatıdır (broker satırı
        yoksa /api/market: ÖNCE seans içi intraday_close — kapanmış DAKİKALIK bar, yalnız silahlı sembollerde
        dolu — ve yalnızca o da yoksa EOD close). İki sayı ayrışıyorsa bu bir kusur değil, iki farklı fiyat
        kanalıdır.
      </p>

      {pencereOncesi.length > 0 && (
        /* ÇİZGİNİN SOL UCU HER ZAMAN "GİRİŞ" DEĞİLDİR ve bunu söylemek zorundayız:
           pencereden (90 seans) daha eski pozisyonlarda çizgi girişte değil, pencerenin
           ilk seansında başlar. Yüzde yine girişe göre — yani değer doğru, başlangıç
           noktası yanıltıcı olabilir. Söylenmeseydi okuyucu sol uçtaki yüzdeyi "aldığımız
           gün" sanardı. */
        <p className="text-muted-foreground text-xs">
          {pencereOncesi.map((s) => s.ticker).join(", ")} — giriş {PENCERE_BAR} seanslık pencereden ÖNCE
          açılmış: çizgi girişte değil, pencerenin ilk seansında başlıyor. Yüzdenin tabanı yine giriş fiyatı.
        </p>
      )}

      {rampaDondu && (
        <p className="text-amber-600 text-xs dark:text-amber-400">
          {cizim.seriler.length} seri çizildi ama renk rampasında {RAMPA_N} ton var — {RAMPA_N + 1}. seriden
          itibaren RENKLER TEKRARLIYOR ({cizim.seriler.filter((s) => s.rampaTekrari).map((s) => s.ticker).join(", ")}).
          Göstergedeki sıra rampanın sırasıdır; aynı renkli iki çizgiyi ayırmak için tooltip'e bakın.
        </p>
      )}

      {/* ---- DÜRÜSTLÜK: kaçın kaçı çizildi --------------------------------- */}
      <div className="rounded-md border border-dashed p-3">
        <p className="font-medium text-sm">
          {satirlar.length} pozisyonun {cizilenCizgi}'i çizildi
          {tekSeanslik.length > 0 ? `, ${tekSeanslik.length}'i tek seanslık (çizgi iki nokta ister)` : ""}
          {cizim.dusenler.length > 0 ? `, ${cizim.dusenler.length}'i çizilemedi:` : "."}
        </p>
        {/* TEK SEANSLIKLAR KENDİ NEDENLERİYLE: "çizilemedi" değiller (yüzdeleri ölçüldü,
            göstergede duruyorlar) ama "çizildi" de değiller — ekrandaki işaretleri bir
            çizgi değil, bir NOKTA. Ara kovayı adlandırmadan sayaç ya şişer ya da eksilir. */}
        {tekSeanslik.length > 0 && (
          <ul className="mt-2 space-y-1">
            {tekSeanslik.map((s) => (
              <li className="text-muted-foreground text-xs" key={s.anahtar}>
                <span className="font-medium text-foreground">{s.ticker}</span> — girişten bu yana ölçülen TEK
                seans {gunAyYil(s.ilkSeans)}
                {s.sonBarTarihi === null
                  ? "; serinin son seansı okunamadı (hiçbir barın tarihi beklenen biçimde değildi), o yüzden serinin nerede bittiği hakkında bir şey söylenmiyor."
                  : s.sonBarTarihi === s.ilkSeans
                    ? "; ham bar serisi de bu seansta bitiyor."
                    : `; ham bar serisi ${gunAyYil(s.sonBarTarihi)} seansına kadar gidiyor ama girişten bu yana yalnız bu seans noktaya çevrilebildi (${s.kapanissizBar} barın kapanışı sayıya çevrilemedi).`}{" "}
                Tek nokta sıfır piksel çizer, bu yüzden seri çizgi değil NOKTA olarak işaretlendi.
              </li>
            ))}
          </ul>
        )}
        {cizim.dusenler.length > 0 && (
          <ul className="mt-2 space-y-1">
            {cizim.dusenler.map((d) => (
              <li className="text-muted-foreground text-xs" key={d.ticker}>
                <span className="font-medium text-foreground">{d.ticker}</span> — {d.neden}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
