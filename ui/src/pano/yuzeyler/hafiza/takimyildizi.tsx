"use client";

/* ============================================================================
   TAKIMYILDIZI — üst yüzeyin `constellation.tsx` görselinin kural karşılığı
   ----------------------------------------------------------------------------
   OPERATÖR GÖRSEL TURU (2026-09-02): "orijinaldeki bayağı başarılı, bizimkinin
   alakası yok." Bu dosya o bulgunun karşılığıdır: üst yüzeyin takımyıldız
   görseli KURAL KURAL okundu (canvas, 1.642 satır, `constellation.tsx` @
   ebad478240d3171bb88201ececda5e8d9883d22d) ve buraya YENİDEN YAZILDI. Kod
   taşınmadı, kütüphane taşınmadı — kural taşındı ve her kuralın kaynağı aşağıda
   adıyla yazılı.

   KÜTÜPHANE YOK, İKİ AYRI SEBEPLE. Üst yüzey çizimi için hiçbir graf
   kütüphanesi kullanmıyor (kuvvet simülasyonu YOK — yerleşim deterministiktir,
   aşağıda), yalnız metin sarma için `@chenglou/pretext` kullanıyor. İkincisi
   buraya alınmadı: panoya yeni bir bağımlılık, tek bir işlev (satır kırma) için
   ölçülmemiş bir yüzey demekti. Karşılığı bu dosyadaki `satirlaraBol` —
   tuvalin kendi `measureText`i ile, önbellekli.

   ---------------------------------------------------------------------------
   TAŞINAN KURALLAR (üst yüzeyden ÖLÇÜLDÜ, uydurulmadı)
   ---------------------------------------------------------------------------
   · YERLEŞİM DETERMİNİSTİK: kimlik özetinden (hash) türeyen bir HALKA. Aynı
     gövde her açılışta AYNI şekli çizer — kuvvet simülasyonunun her açılışta
     başka bir şekil vermesi, operatöre "graf değişti" dedirtirdi.
   · KÜMELEME: küme anahtarı taşıyan düğümler kendi küme merkezleri etrafında
     toplanır, küme yarı-saydam bir "kabarcık" ile sarılır ve etiketi bir hapta
     yazılır. Üç noktadan azsa kabarcık dışbükey zarf değil ÇEMBERdir (üç nokta
     olmadan çokgen yoktur).
   · NOKTA YARIÇAPI bağ sayısından türer (boyut işlevi verilmediyse); ısı rengi
     bağ sayısının karekök normalizasyonundan.
   · BAĞ ÇİZİM TAVANI 6.000: üstü çizilmez ve KAÇININ çizilmediği ekranda yazar.
   · ETKİLEŞİM: tekerlek yakınlaştırır, sürükleme kaydırır, üzerine gelmek
     komşuları vurgular, tıklamak seçer.

   ---------------------------------------------------------------------------
   BİLEREK TAŞINMAYANLAR — "eksik" ile "kapsam dışı" ayrı yazılır
   ---------------------------------------------------------------------------
   · Üst yüzeyin renkleri (sabit altıgen kodlar) taşınmadı: pano kendi çok-serili
     rampasını kullanır ve rampa TEMAYLA döner. Hue eşlemesi birebir yapıldı
     (mavi→mavi, mor→mor, turuncu→turuncu, camgöbeği→camgöbeği, pembe→pembe),
     yani renk KİMLİK kanalı olarak aynı yerde durur, jeton bizimdir.
   · "Poster olarak dışa aktar" düğmesi: üst yüzeyin markalı paylaşım çıktısıdır
     (kendi logosunu gömer), panonun işi değil.
   · Tam ekran düğmesi: kapsam listesinde yok, eklenmedi.
   · Venn/Euler kipi: üst yüzeyde var ama görünümlerin hiçbiri kullanmıyor
     (ölçüldü) — okuyucusu olmayan bir yüzey buraya taşınmadı.

   ---------------------------------------------------------------------------
   HAREKET VE BEDELİ
   ---------------------------------------------------------------------------
   Üst yüzey kareyi DURMADAN yeniler (sürüklenme + parıltı + nabız). Bunun bedeli
   ölçülebilir: sekme açık kaldığı sürece süren bir çizim döngüsü. Burada üç kapı
   var ve üçü de davranışı DEĞİŞTİRİR, gizlemez:
     1. Hareket azaltma tercihi açıksa sürüklenme/nabız/parıltı KAPANIR ve döngü
        sürekli olmaktan çıkar — kare yalnız etkileşimde (üzerine gelme, kaydırma,
        yakınlaştırma, yeniden boyutlanma, tema) çizilir.
     2. Tuval ekranda görünmüyorsa (kaydırılıp çıktıysa) ya da sekme arka
        plandaysa döngü DURUR, görünür olunca kaldığı yerden devam eder.
     3. Bileşen kaldırılınca kare isteği iptal edilir, dinleyiciler sökülür.
   ============================================================================ */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";

import { Olculemedi } from "../sistem/parcalar";
import { KirpmaZinciri, damga, listeye, metin, sayi, sozluk } from "./parcalar";
import type {
  BellekGrafi,
  GrafSatiri,
  HafizaZarfi,
  HamGovde,
  TakimyildiziBagi,
  TakimyildiziDugumu,
  TakimyildiziVerisi,
  VarlikGrafi,
} from "./uctipleri";

/* ---------------------------------------------------------------------------
   PALET — YALNIZ JETONLARDAN. SABİT RENK YOK, YEDEK RENK DE YOK.
   ----------------------------------------------------------------------------
   Tuval CSS değişkeni ANLAMAZ: renk değeri olarak bir değişken adı verildiğinde
   atama sessizce yok sayılır ve ekranda bir önceki renk kalır. Bu yüzden jetonlar
   okunur, tuvalin KENDİ renk çözücüsüyle sayıya çevrilir ve tema değişince
   YENİDEN okunur.

   YEDEK SABİT LİSTESİ KALDIRILDI (düzeltme turu 1, çivi G1b). İlk yazımda her
   jetonun yanında bir yedek renk vardı ve gerekçesi "jeton çözülemezse ekran boş
   kalmasın"dı. Ölçülen sonuç şuydu: o yedekler tema anahtarına KATILMAYAN sabit
   renklerdi — gece temasına geçildiğinde olduğu gibi kalırlardı ve kusur SESSİZ
   olurdu (yanlış renk, hata yok). Kural bu depoda zaten yazılı: pano bileşeninde
   çıplak renk yok, renk jetondan okunur.

   YEDEĞİN YERİNE DÜRÜST HÂL GEÇTİ: bir jeton çözülemezse palet KURULMAZ, graf
   ÇİZİLMEZ ve ekran neyin çözülemediğini yazar. "Yanlış renkli bir graf" ile
   "graf çizilemedi" iki ayrı cümledir ve ikincisi doğru olandır.
   --------------------------------------------------------------------------- */

/** Jeton adı → panonun jeton değişkeni. Başka renk kaynağı YOKTUR. */
/* İHRAÇ EDİLDİ (Görev 9): ana sayfanın "bağ türleri" çubuğu AYNI hue eşlemesini
   ve AYNI kelimeleri kullanır. İkinci bir eşleme yazmak, aynı sayfada aynı bağ
   türünü iki renkte ve iki adla göstermek olurdu (tek-kaynak yasası). */
export const JETONLAR = {
  mavi: "--color-seri-6",
  turuncu: "--color-seri-7",
  mor: "--color-seri-8",
  camgobegi: "--color-seri-9",
  pembe: "--color-seri-10",
  zemin: "--background",
  yazi: "--foreground",
  soluk: "--muted-foreground",
  cerceve: "--border",
  kart: "--card",
} as const satisfies Record<string, string>;

type JetonAdi = keyof typeof JETONLAR;

type Rgb = readonly [number, number, number];

interface Palet {
  readonly koyu: boolean;
  readonly renk: Readonly<Record<JetonAdi, string>>;
  /** Aynı renkler SAYI olarak — karışım ve saydamlık için. Çizim sırasında
   *  yeniden çözülmezler: renk çözümü bir tuval nesnesi doğurur ve onu kare
   *  başına yapmak, ölçülebilir bir çöp üretimidir. */
  readonly rgb: Readonly<Record<JetonAdi, Rgb>>;
  /** Isı rampasının üç durağı — soğuk → köprü → sıcak (üst yüzeyle aynı yapı).
   *  ÜÇLÜ olarak yazılı, dizi olarak değil: sayıyı tip taşıyınca ara durak
   *  sessizce düşemez ve karışım kodunda "belki yok" hâli hiç doğmaz. */
  readonly isiDuraklari: readonly [Rgb, Rgb, Rgb];
}

/**
 * Bir renk dizgesini tuvalin KENDİ çözücüsüyle kırmızı/yeşil/mavi üçlüsüne
 * çevirir. Elle bir renk-uzayı ayrıştırıcısı yazmak, tarayıcının zaten yaptığı
 * dönüşümü ikinci kez ve muhtemelen farklı yapmak olurdu — jetonlar bugün algısal
 * bir renk uzayında yazılı ve o dönüşüm önemsiz değil.
 *
 * `null` = renk GEÇERSİZ. Sınama şu ölçülmüş davranışa dayanır: geçersiz bir
 * değer atandığında tuval atamayı SESSİZCE yok sayar ve önceki renk kalır. İKİ
 * FARKLI başlangıçtan denenir ve okunan iki değerin AYNI olması aranır: tek
 * başlangıçla sınayan bir sürüm, değerin tam da o başlangıca eşit olduğu durumda
 * geçerli bir rengi geçersiz sayardı.
 */
function rgbCoz(deger: string): Rgb | null {
  if (typeof document === "undefined" || deger === "") return null;
  const tuval = document.createElement("canvas");
  tuval.width = 1;
  tuval.height = 1;
  const ctx = tuval.getContext("2d", { willReadFrequently: true });
  if (!ctx) return null;
  const dene = (baslangic: string): string => {
    ctx.fillStyle = baslangic;
    ctx.fillStyle = deger;
    return String(ctx.fillStyle);
  };
  if (dene("rgb(1,2,3)") !== dene("rgb(250,251,252)")) return null;
  ctx.fillRect(0, 0, 1, 1);
  const [k, y, m] = ctx.getImageData(0, 0, 1, 1).data;
  return k === undefined || y === undefined || m === undefined ? null : [k, y, m];
}

function rgbDizgesi(c: Rgb): string {
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

function rgbaDizgesi(c: Rgb, alfa: number): string {
  return `rgba(${c[0]},${c[1]},${c[2]},${alfa})`;
}

/** Bağıl parlaklık (erişilebilirlik tanımı). Zıtlık seçimi için — "koyu tema mı"
 *  sorusu yetmez, çünkü küme hapının zemini TEMA rengi değil KÜME rengidir. */
function parlaklik(c: Rgb): number {
  const kanal = (v: number) => {
    const x = v / 255;
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * kanal(c[0]) + 0.7152 * kanal(c[1]) + 0.0722 * kanal(c[2]);
}

/**
 * Verilen zemin üzerinde OKUNUR yazı rengi — iki tema jetonundan hangisi daha
 * zıtsa o.
 *
 * İLK YAZIM BURAYA BEYAZ SABİTİ KOYUYORDU (çivi G1b). Sabit, dört hazır temanın
 * dördünde de aynı kalırdı; oysa hapın zemini küme rengidir ve o renk temayla
 * döner. Zıtlık hesaplanınca hem sabit kalkıyor hem de karar ÖLÇÜLMÜŞ oluyor.
 */
function okunurYazi(palet: Palet, zemin: Rgb): string {
  const zit = (a: Rgb, b: Rgb) => {
    const [x, y] = [parlaklik(a), parlaklik(b)];
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  };
  return zit(palet.rgb.zemin, zemin) >= zit(palet.rgb.yazi, zemin) ? palet.renk.zemin : palet.renk.yazi;
}

/**
 * Paleti jetonlardan kurar. `null` = EN AZ BİR JETON ÇÖZÜLEMEDİ.
 *
 * Kısmi palet döndürmüyoruz: eksik jetonun yerine bir şey koymak, yedek sabitlerin
 * kaldırılma gerekçesinin aynısını arka kapıdan geri getirirdi.
 */
function paletOku(): Palet | null {
  if (typeof document === "undefined") return null;
  const bicim = getComputedStyle(document.documentElement);
  const cozulen = {} as Record<JetonAdi, Rgb>;
  const renk = {} as Record<JetonAdi, string>;
  for (const [ad, degisken] of Object.entries(JETONLAR) as [JetonAdi, string][]) {
    const c = rgbCoz(bicim.getPropertyValue(degisken).trim());
    if (c === null) return null;
    cozulen[ad] = c;
    renk[ad] = rgbDizgesi(c);
  }
  return {
    koyu: document.documentElement.classList.contains("dark"),
    renk,
    rgb: cozulen,
    /* ÜST YÜZEYİN YAPISI AYNEN: soğuk (az) → ara köprü → sıcak (çok). Ara durak
       parlaklığı tek yönlü tutar, yani okuyucu çubuğa bakmadan da sıralayabilir. */
    isiDuraklari: [cozulen.mavi, cozulen.mor, cozulen.turuncu],
  };
}

/** 0..1 → ısı rengi. Üst yüzeyin üç duraklı doğrusal karışımının aynısı. */
function isiRengi(palet: Palet, t: number): Rgb {
  const v = Math.max(0, Math.min(1, t));
  const [soguk, orta, sicak] = palet.isiDuraklari;
  const [a, b, f] = v < 0.5 ? ([soguk, orta, v * 2] as const) : ([orta, sicak, (v - 0.5) * 2] as const);
  return [
    Math.round(a[0] + (b[0] - a[0]) * f),
    Math.round(a[1] + (b[1] - a[1]) * f),
    Math.round(a[2] + (b[2] - a[2]) * f),
  ];
}

/* BAĞ TÜRÜ RENKLERİ — üst yüzeyin dört türü, hue eşlemesiyle bizim jetonlarımıza.
   Üst yüzey: anlamsal mavi · zamansal camgöbeği-yeşil · varlık kehribar · nedensel
   mor. Aşağıdaki eşleme aynı hue sırasını korur. */
export const BAG_TURU_JETONU: Readonly<Record<string, JetonAdi>> = {
  semantic: "mavi",
  temporal: "camgobegi",
  entity: "turuncu",
  causal: "mor",
};

export const BAG_TURU_ETIKETI: Readonly<Record<string, string>> = {
  semantic: "anlamsal",
  temporal: "zamansal",
  entity: "varlık",
  causal: "nedensel",
  cooccurrence: "birlikte geçiş",
};

/* KÜME RENKLERİ — bellek grafının üç kayıt türü. Üst yüzeyin ana sayfası da
   kümeleri kayıt türüne göre renklendiriyor (mor / pembe / çivit); eşleme yine
   hue düzeyinde birebir. */
const KUME_JETONU: Readonly<Record<string, JetonAdi>> = {
  world: "mor",
  experience: "pembe",
  observation: "mavi",
  entity: "camgobegi",
};

const KUME_ETIKETI: Readonly<Record<string, string>> = {
  world: "dünya bilgisi",
  experience: "deneyim",
  observation: "gözlem",
};

/* ---------------------------------------------------------------------------
   ÇİZİM SABİTLERİ — hepsi üst yüzeyden ÖLÇÜLDÜ
   --------------------------------------------------------------------------- */

/** Bir karede çizilen en fazla bağ sayısı. Aşan bağlar çizilmez ve SAYILIR. */
const BAG_CIZIM_TAVANI = 6000;
/** Sürüklenme genliği (dünya birimi) — alanın "nefes alması". */
const SURUKLENME = 16;
/** Kaydırma/yakınlaştırmanın yumuşama katsayısı. */
const YUMUSAMA = 0.12;
/** Görünürlük kenar payı (piksel). */
const KENAR_PAYI = 60;
const EN_KUCUK_YAKINLIK = 0.03;
const EN_BUYUK_YAKINLIK = 8;

const YAZITIPI_KUCUK = '11px Inter, -apple-system, "Segoe UI", sans-serif';
const YAZITIPI_KALIN = '600 10px Inter, -apple-system, "Segoe UI", sans-serif';
const YAZITIPI_TEK_ARALIK = '11px "SF Mono", "Fira Code", Consolas, monospace';

/* ---------------------------------------------------------------------------
   HAZIRLIK — yerleşim, bir kez
   --------------------------------------------------------------------------- */

interface HazirDugum {
  readonly dugum: TakimyildiziDugumu;
  /** Dünya koordinatı (kaydırma/yakınlaştırma öncesi). */
  readonly dx: number;
  readonly dy: number;
  readonly bagSayisi: number;
  /** Nokta rengi — kümedeyse küme rengi, değilse ısı rengi. */
  readonly renk: Rgb;
  /** Her düğüme kimlik özetinden düşen faz; nabız ve sürüklenme kilitlenmez. */
  readonly faz: number;
}

interface HazirKume {
  readonly anahtar: string;
  readonly uyeler: readonly number[];
  readonly renk: Rgb;
  readonly etiket: string;
}

interface HazirBag {
  readonly a: number;
  readonly b: number;
  readonly renk: string;
  readonly tur: string;
}

interface Hazirlik {
  readonly dugumler: readonly HazirDugum[];
  readonly baglar: readonly HazirBag[];
  /** Düğüm indeksi → o düğüme değen bağların indeksleri. Üzerine gelme
   *  vurgusunun tüm bağ listesini taramamasını sağlar (kare başına O(bağ) yerine
   *  O(komşu)); kurulumu bir kez, O(bağ). */
  readonly bagIndeksi: ReadonlyMap<number, readonly number[]>;
  readonly kumeler: readonly HazirKume[];
  /** Veride GERÇEKTEN geçen bağ türleri — efsane bunlardan kurulur. */
  readonly bagTurleri: readonly string[];
  /** İki ucundan biri dönen dilimde olmadığı için çizilemeyen bağ sayısı. */
  readonly askidaBag: number;
}

/** Bir düğümün O KAREDEKİ ekran konumu. Hazırlık değişince yeniden kurulur,
 *  kare başına yalnız güncellenir. */
interface Konum {
  readonly i: number;
  readonly g: HazirDugum;
  x: number;
  y: number;
  gorunur: boolean;
}

const BOS_HAZIRLIK: Hazirlik = {
  dugumler: [],
  baglar: [],
  bagIndeksi: new Map(),
  kumeler: [],
  bagTurleri: [],
  askidaBag: 0,
};

function ozet(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return h;
}

type Nokta = readonly [number, number];

/** Tek yönlü dışbükey zarf (monoton zincir). Üç noktadan azında çokgen yoktur —
 *  çağıran o hâlde çember çizer. */
function disbukeyZarf(noktalar: readonly Nokta[]): Nokta[] {
  if (noktalar.length < 3) return noktalar.slice();
  const p = noktalar.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const capraz = (o: Nokta, a: Nokta, b: Nokta) =>
    (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  /* Zincirin son iki noktası dizinin SONUNDAN okunur; boyut denetimi zaten
     yapılıyor ama okuma yine de açıkça sınanır — "olamaz" diye atlanan bir
     denetim, kütüphanesiz bir geometri kodunda en pahalı sessizliktir. */
  const zincir = (sirali: readonly Nokta[]): Nokta[] => {
    const yigin: Nokta[] = [];
    for (const n of sirali) {
      for (;;) {
        const o = yigin.at(-2);
        const a = yigin.at(-1);
        if (o === undefined || a === undefined || capraz(o, a, n) > 0) break;
        yigin.pop();
      }
      yigin.push(n);
    }
    yigin.pop();
    return yigin;
  };
  return zincir(p).concat(zincir(p.slice().reverse()));
}

/** Küme anahtarının paletteki karşılığı; tanınmayan anahtar varsayılan jetona
 *  düşer — renk bir ÖLÇÜM değil bir kimlik kanalıdır, bilinmeyen bir tür de
 *  çizilir. */
function kumeRgb(palet: Palet, anahtar: string): Rgb {
  return palet.rgb[KUME_JETONU[anahtar] ?? "mavi"];
}

function hazirla(
  veri: TakimyildiziVerisi,
  palet: Palet,
  kumele: boolean,
  isiFn: ((d: TakimyildiziDugumu) => number) | undefined,
): Hazirlik {
  const dugumler = veri.dugumler;
  if (dugumler.length === 0) return BOS_HAZIRLIK;

  const indeks = new Map<string, number>();
  dugumler.forEach((d, i) => indeks.set(d.kimlik, i));

  const bagSayaci = new Map<string, number>();
  for (const b of veri.baglar) {
    bagSayaci.set(b.kaynak, (bagSayaci.get(b.kaynak) ?? 0) + 1);
    bagSayaci.set(b.hedef, (bagSayaci.get(b.hedef) ?? 0) + 1);
  }
  let enCokBag = 1;
  for (const n of bagSayaci.values()) if (n > enCokBag) enCokBag = n;

  /* KÜME ÖN HESABI: küme anahtarı taşıyan düğümler anahtara göre gruplanır ve her
     grup KENDİ merkezinin çevresine dağılır. Anahtarsız düğüm halkada kalır —
     "kümesi yok" ile "kümesi boş" ayrı hâllerdir ve ikincisi uydurulmaz. */
  const sayi_ = dugumler.length;
  /** Düğümün küme anahtarı — kümeleme kapalıysa ya da alan boşsa `null`. */
  const kumeAnahtari = (d: TakimyildiziDugumu): string | null => {
    if (!kumele) return null;
    const a = d.kume;
    return a === null || a === undefined || a === "" ? null : a;
  };

  interface KumeBilgisi {
    readonly uyeler: number[];
    cx: number;
    cy: number;
    r: number;
  }
  const kumeler_ = new Map<string, KumeBilgisi>();
  dugumler.forEach((d, i) => {
    const a = kumeAnahtari(d);
    if (a === null) return;
    const mevcut = kumeler_.get(a);
    if (mevcut) mevcut.uyeler.push(i);
    else kumeler_.set(a, { uyeler: [i], cx: 0, cy: 0, r: 0 });
  });
  const kumeSirasi = [...kumeler_.keys()].sort();
  const kumeHalkasi = Math.sqrt(Math.max(sayi_, 1)) * 60;
  kumeSirasi.forEach((a, ci) => {
    const bilgi = kumeler_.get(a);
    if (bilgi === undefined) return;
    const aci = (ci / Math.max(kumeSirasi.length, 1)) * Math.PI * 2;
    bilgi.cx = Math.cos(aci) * kumeHalkasi;
    bilgi.cy = Math.sin(aci) * kumeHalkasi;
    bilgi.r = 22 + Math.sqrt(bilgi.uyeler.length) * 18;
  });

  const hazirDugumler: HazirDugum[] = dugumler.map((d, i) => {
    const anahtar = kumeAnahtari(d);
    const merkez = anahtar === null ? undefined : kumeler_.get(anahtar);
    const tohum = ozet(d.kimlik);
    let dx: number;
    let dy: number;
    if (merkez) {
      /* Küme merkezinin çevresine küçük bir diskte dağıt: aynı kümedeki kayıtlar
         tek noktada üst üste binmesin. Açı üyelik sırasından, yarıçap özetten —
         ikisi de deterministik. */
      const j = merkez.uyeler.indexOf(i);
      const aci = (j / Math.max(merkez.uyeler.length, 1)) * Math.PI * 2 + ((tohum % 100) / 100) * 0.6;
      const yaricap = merkez.r * (0.25 + 0.75 * ((Math.abs(tohum) % 1000) / 1000));
      dx = merkez.cx + Math.cos(aci) * yaricap;
      dy = merkez.cy + Math.sin(aci) * yaricap;
    } else {
      const aci = (i / sayi_) * Math.PI * 2 + ((tohum % 100) / 100) * 0.5;
      const taban = Math.sqrt(sayi_) * 30;
      const yaricap = taban * 0.3 + ((Math.abs(tohum) % 1000) / 1000) * taban * 0.7;
      dx = Math.cos(aci) * yaricap + ((tohum % 200) - 100) * 0.5;
      dy = Math.sin(aci) * yaricap + (((tohum >> 8) % 200) - 100) * 0.5;
    }

    const lc = bagSayaci.get(d.kimlik) ?? 0;
    /* KAREKÖK: üst yüzeyin kendi gerekçesi — doğrusal normalizasyonda neredeyse
       her düğüm rampanın sıcak ucuna yığılıyor. */
    const isi = isiFn ? isiRengi(palet, isiFn(d)) : isiRengi(palet, Math.sqrt(lc / enCokBag));
    const kumeRengi = merkez === undefined || anahtar === null ? null : kumeRgb(palet, anahtar);
    return {
      dugum: d,
      dx,
      dy,
      bagSayisi: lc,
      renk: kumeRengi ?? isi,
      faz: ((Math.abs(tohum) % 1000) / 1000) * Math.PI * 2,
    };
  });

  const kumeler: HazirKume[] = [];
  for (const anahtar of kumeSirasi) {
    const bilgi = kumeler_.get(anahtar);
    if (bilgi === undefined) continue;
    kumeler.push({
      anahtar,
      uyeler: bilgi.uyeler,
      renk: kumeRgb(palet, anahtar),
      etiket: KUME_ETIKETI[anahtar] ?? anahtar,
    });
  }

  const baglar: HazirBag[] = [];
  const bagIndeksi = new Map<number, number[]>();
  const turler = new Set<string>();
  let askidaBag = 0;
  for (const bag of veri.baglar) {
    const a = indeks.get(bag.kaynak);
    const b = indeks.get(bag.hedef);
    if (a === undefined || b === undefined) {
      askidaBag += 1;
      continue;
    }
    const tur = bag.tur ?? "semantic";
    turler.add(tur);
    const renk = palet.renk[BAG_TURU_JETONU[tur] ?? "mavi"];
    const i = baglar.length;
    baglar.push({ a, b, renk, tur });
    const listeA = bagIndeksi.get(a);
    if (listeA) listeA.push(i);
    else bagIndeksi.set(a, [i]);
    const listeB = bagIndeksi.get(b);
    if (listeB) listeB.push(i);
    else bagIndeksi.set(b, [i]);
  }

  return {
    dugumler: hazirDugumler,
    baglar,
    bagIndeksi,
    kumeler,
    bagTurleri: [...turler].sort(),
    askidaBag,
  };
}

/* ---------------------------------------------------------------------------
   METİN SARMA — kütüphanenin yerine geçen ölçüm
   --------------------------------------------------------------------------- */

/** Metni verilen genişliğe göre satırlara böler; sığmayan tek kelime harf harf
 *  kırılır. Önbellek çağırana ait: yazıtipi sabit olduğu için ölçüm değişmez. */
function satirlaraBol(
  ctx: CanvasRenderingContext2D,
  yazi: string,
  genislik: number,
  onbellek: Map<string, string[]>,
): string[] {
  const anahtar = `${Math.round(genislik)}|${yazi}`;
  const varolan = onbellek.get(anahtar);
  if (varolan) return varolan;
  const satirlar: string[] = [];
  let gecerli = "";
  for (const kelime of yazi.split(/\s+/).filter(Boolean)) {
    const aday = gecerli === "" ? kelime : `${gecerli} ${kelime}`;
    if (ctx.measureText(aday).width <= genislik) {
      gecerli = aday;
      continue;
    }
    if (gecerli !== "") {
      satirlar.push(gecerli);
      gecerli = "";
    }
    let parca = "";
    for (const harf of kelime) {
      if (ctx.measureText(parca + harf).width <= genislik) {
        parca += harf;
        continue;
      }
      if (parca !== "") satirlar.push(parca);
      parca = harf;
    }
    gecerli = parca;
  }
  if (gecerli !== "") satirlar.push(gecerli);
  if (satirlar.length === 0) satirlar.push("");
  /* ÖNBELLEK SINIRLI: anahtar (genişlik, metin) ikilisidir ve genişlik
     yakınlaştırmayla sürekli değişir — sınırsız bırakılsaydı uzun bir oturumda
     sessizce büyürdü. Dolunca tamamen boşalır: en-az-kullanılanı ayıklamak,
     ölçülmemiş bir kazanç için ölçülebilir bir karmaşıklık olurdu. */
  if (onbellek.size > 2000) onbellek.clear();
  onbellek.set(anahtar, satirlar);
  return satirlar;
}

/**
 * SIĞDIRMA YAKINLIĞI — üst yüzeyin kuralı, artı bir kapı.
 *
 * Kural: en uzak düğümün merkeze uzaklığı kısa kenara 2,5 katıyla oturur. KAPI
 * bizim eklediğimiz: üst yüzey sonucu sınırlamıyor ve iki-üç düğümlük bir grafta
 * çarpan uçuyor — tekerleğin izin verdiği en büyük yakınlığın ötesine geçen bir
 * açılış, operatörün geri çıkamadığı bir kadraj demek. Sınırlar tekerleğinkiyle
 * AYNI sabitlerdir; ikinci bir sayı yazmak iki sınırı sessizce ayırırdı.
 */
function sigdirmaYakinligi(enUzak: number, G: number, Y: number): number {
  const ham = enUzak > 0 && G > 0 && Y > 0 ? Math.min(G, Y) / (enUzak * 2.5) : 0.5;
  return Math.max(EN_KUCUK_YAKINLIK, Math.min(EN_BUYUK_YAKINLIK, ham));
}

function yuvarlakDikdortgen(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  g: number,
  y2: number,
  r: number,
): void {
  ctx.beginPath();
  if (typeof ctx.roundRect === "function") ctx.roundRect(x, y, g, y2, r);
  else ctx.rect(x, y, g, y2);
}

/* ---------------------------------------------------------------------------
   BİLEŞEN
   --------------------------------------------------------------------------- */

export interface TakimyildiziOzellikleri {
  readonly veri: TakimyildiziVerisi;
  readonly yukseklik?: number;
  /** Bir düğüme tıklanınca. Verilmezse tıklama bir şey YAPMAZ ve imleç de
   *  değişmez — "tıklanabilir görünüp tepki vermeyen" hâl bu yüzden yok. */
  readonly dugumTiklandi?: (dugum: TakimyildiziDugumu) => void;
  /** Nokta yarıçapı (piksel, yakınlaştırma öncesi). Verilmezse bağ sayısından. */
  readonly boyutFn?: (dugum: TakimyildiziDugumu) => number;
  /** Isı değeri 0..1. Verilmezse bağ sayısının karekök normalizasyonu.
   *  DEĞİŞMEZ BİR REFERANS OLMALI (`useCallback`): yerleşim bu işleve bağlı. */
  readonly isiFn?: (dugum: TakimyildiziDugumu) => number;
  readonly isiEtiketi?: string;
  readonly isiUclari?: readonly [string, string];
  /** Nokta boyutu anlamlı bir boyutu kodluyorsa efsanesinin başlığı. */
  readonly boyutEtiketi?: string;
  /** Kısa etiketler (varlık adları) için sık yerleşim. */
  readonly sikEtiket?: boolean;
  /** Küme anahtarına göre kümele — düğümler `kume` alanı taşımıyorsa etkisiz. */
  readonly kumele?: boolean;
  /** Ekran okuyucuya ne olduğu. */
  readonly aciklama: string;
}

export function Takimyildizi({
  veri,
  yukseklik = 460,
  dugumTiklandi,
  boyutFn,
  isiFn,
  isiEtiketi,
  isiUclari,
  boyutEtiketi,
  sikEtiket = false,
  kumele = false,
  aciklama,
}: TakimyildiziOzellikleri) {
  const tuvalRef = useRef<HTMLCanvasElement>(null);
  const balonRef = useRef<HTMLDivElement>(null);
  const [palet, setPalet] = useState<Palet | null>(() => paletOku());
  const [ustuneGelinen, setUstuneGelinen] = useState<number>(-1);
  /* BOŞ HÂLDE TUVAL HİÇ ÇİZİLMEZ ve bu kurulum etkisinin BAĞIMLILIĞIDIR — sabit
     bir bağımlılık listesi bırakılsaydı etki boş hâlde bir kez koşar, tuvali
     bulamaz ve veri sonradan geldiğinde BİR DAHA koşmazdı: graf sessizce ölü
     kalırdı (yükleme sırası her açılışta aynı olmadığı için ara ara). */
  const bos = veri.dugumler.length === 0;
  /* ÇİZİLEBİLİR = veri VAR ve palet KURULDU. İkisi de kurulum etkisinin
     bağımlılığıdır: hangisi sonradan gelirse gelsin etki yeniden koşar ve tuvali
     bulur. Sabit bir bağımlılık listesi, sonradan gelen veride grafı sessizce ölü
     bırakırdı. */
  const cizilebilir = !bos && palet !== null;

  const hazir = useMemo(
    () => (palet === null ? BOS_HAZIRLIK : hazirla(veri, palet, kumele, isiFn)),
    [veri, palet, kumele, isiFn],
  );

  /* İŞLEVLER REFERANSTA TUTULUR, BAĞIMLILIKTA DEĞİL: çizim her karede okur ve
     çağıran satır içi bir ok işlevi verse bile yerleşim yeniden hesaplanmaz.
     (Isı işlevi bunun DIŞINDA: o rengi belirler ve hazırlıkta kullanılır.) */
  const boyutRef = useRef(boyutFn);
  boyutRef.current = boyutFn;
  const tiklamaRef = useRef(dugumTiklandi);
  tiklamaRef.current = dugumTiklandi;

  const hazirRef = useRef(hazir);
  const konumRef = useRef<Konum[]>([]);
  const paletRef = useRef(palet);
  const sarmaOnbellegi = useRef(new Map<string, string[]>());
  const kareRef = useRef(0);
  const hareketRef = useRef(true);
  const gorunurRef = useRef(true);

  const durum = useRef({
    kaydirmaX: 0,
    kaydirmaY: 0,
    yakinlik: 0.5,
    hedefKaydirmaX: 0,
    hedefKaydirmaY: 0,
    hedefYakinlik: 0.5,
    fareX: -1,
    fareY: -1,
    surukluyor: false,
    surukleBasX: 0,
    surukleBasY: 0,
    kaydirmaBasX: 0,
    kaydirmaBasY: 0,
    ustDugum: -1,
    G: 0,
    Y: 0,
    dpr: 1,
  });

  /* ---- kare zamanlayıcı: tek istek, sürekli kip yalnız hareket açıkken ---- */
  const kareIste = useRef<() => void>(() => undefined);
  const balonKonumRef = useRef<() => void>(() => undefined);

  /* ---- palet ilk okumada kurulamadıysa boyamadan SONRA bir kez daha dene ----
     İlk okuma çizim öncesi yapılıyor; biçim sayfası o an henüz uygulanmamışsa
     jetonlar boş okunur. Bu etki boyamadan sonra koştuğu için o pencereyi kapatır.
     DÖNGÜ YOK: ikinci deneme de başarısızsa değer yine boş kalır ve React aynı
     değere yeniden çizim yapmaz — dürüst hâl olduğu yerde durur. */
  useEffect(() => {
    if (palet === null) setPalet(paletOku());
  }, [palet]);

  /* ---- tema değişimini izle ---- */
  useEffect(() => {
    if (typeof document === "undefined") return;
    const gozlemci = new MutationObserver(() => setPalet(paletOku()));
    gozlemci.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "data-theme-preset"],
    });
    return () => gozlemci.disconnect();
  }, []);

  /* ---- hareket azaltma tercihi ---- */
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const sorgu = window.matchMedia("(prefers-reduced-motion: reduce)");
    const uygula = () => {
      hareketRef.current = !sorgu.matches;
      kareIste.current();
    };
    uygula();
    sorgu.addEventListener("change", uygula);
    return () => sorgu.removeEventListener("change", uygula);
  }, []);

  useEffect(() => {
    hazirRef.current = hazir;
    konumRef.current = hazir.dugumler.map((g, i) => ({ i, g, x: 0, y: 0, gorunur: false }));
    sarmaOnbellegi.current.clear();
    /* TEMA DEĞİŞİMİ DE BURAYA DÜŞER VE KADRAJI SIFIRLAR (inceleme M-6). Hazırlık
       palete bağlı, çünkü nokta renkleri hazırlıkta atanıyor; palet değişince
       hazırlık yenilenir ve yakınlaştırma/kaydırma başa döner. Üst yüzeyde de
       AYNI davranış var (çizim döngüsü tema bayrağına, kurulum etkisi döngüye
       bağlı). Bilinçli: temayı değiştirmek nadir, kadrajı korumak için ikinci bir
       "yalnız renk yenile" yolu açmak iki hazırlık yolu demekti.

       YENİ GÖVDE = YENİ ÇERÇEVELEME. Üst yüzeyin "sığdır" hesabı: en uzak düğümün
       merkeze uzaklığı, kısa kenara 2,5 katıyla oturtulur. */
    const d = durum.current;
    let enUzak = 0;
    for (const n of hazir.dugumler) {
      const u = Math.sqrt(n.dx * n.dx + n.dy * n.dy);
      if (u > enUzak) enUzak = u;
    }
    const sigdir = sigdirmaYakinligi(enUzak, d.G, d.Y);
    d.yakinlik = sigdir;
    d.hedefYakinlik = sigdir;
    d.kaydirmaX = 0;
    d.kaydirmaY = 0;
    d.hedefKaydirmaX = 0;
    d.hedefKaydirmaY = 0;
    d.ustDugum = -1;
    setUstuneGelinen(-1);
    kareIste.current();
  }, [hazir]);

  useEffect(() => {
    paletRef.current = palet;
    kareIste.current();
  }, [palet]);

  /* ------------------------------------------------------------------------
     ÇİZİM
     ------------------------------------------------------------------------ */
  const ciz = useCallback(() => {
    const tuval = tuvalRef.current;
    if (!tuval) return false;
    const ctx = tuval.getContext("2d");
    if (!ctx) return false;

    const d = durum.current;
    const h = hazirRef.current;
    const p = paletRef.current;
    if (p === null) return false;
    const hareket = hareketRef.current;

    if (hareket) {
      d.kaydirmaX += (d.hedefKaydirmaX - d.kaydirmaX) * YUMUSAMA;
      d.kaydirmaY += (d.hedefKaydirmaY - d.kaydirmaY) * YUMUSAMA;
      d.yakinlik += (d.hedefYakinlik - d.yakinlik) * YUMUSAMA;
    } else {
      d.kaydirmaX = d.hedefKaydirmaX;
      d.kaydirmaY = d.hedefKaydirmaY;
      d.yakinlik = d.hedefYakinlik;
    }
    const yerlesiyor =
      Math.abs(d.hedefKaydirmaX - d.kaydirmaX) > 0.4 ||
      Math.abs(d.hedefKaydirmaY - d.kaydirmaY) > 0.4 ||
      Math.abs(d.hedefYakinlik - d.yakinlik) > 0.001;

    const { G, Y, dpr, yakinlik } = d;
    const mx = G / 2 + d.kaydirmaX;
    const my = Y / 2 + d.kaydirmaY;

    ctx.clearRect(0, 0, tuval.width, tuval.height);
    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.fillStyle = p.renk.zemin;
    ctx.fillRect(0, 0, G, Y);

    const zaman = hareket ? (typeof performance !== "undefined" ? performance.now() : 0) / 1000 : 0;

    /* KONUM DİZİSİ KARE BAŞINA YENİDEN KURULMAZ, YERİNDE GÜNCELLENİR: her karede
       200 nesne doğurup atmak, hiçbir şey kazandırmayan bir çöp üretimidir. */
    const n = h.dugumler.length;
    const konumlar = konumRef.current;
    for (const k of konumlar) {
      const g = k.g;
      k.x = mx + (g.dx + (hareket ? SURUKLENME * Math.sin(zaman * 0.6 + g.faz) : 0)) * yakinlik;
      k.y = my + (g.dy + (hareket ? SURUKLENME * Math.cos(zaman * 0.5 + g.faz * 1.3) : 0)) * yakinlik;
      k.gorunur =
        k.x > -KENAR_PAYI && k.x < G + KENAR_PAYI && k.y > -KENAR_PAYI && k.y < Y + KENAR_PAYI;
    }

    /* İSABET SINAMASI: en yakın görünür düğüm. Yakınlaştırıldığında tolerans
       genişler — üst yüzeyin ölçüsü. */
    if (d.fareX >= 0 && !d.surukluyor) {
      let enIyi = yakinlik > 1.5 ? 80 : 30;
      let indeks = -1;
      for (const k of konumlar) {
        if (!k.gorunur) continue;
        const fx = d.fareX - k.x;
        const fy = d.fareY - k.y;
        const uz = Math.sqrt(fx * fx + fy * fy);
        if (uz < enIyi) {
          enIyi = uz;
          indeks = k.i;
        }
      }
      d.ustDugum = indeks;
    }
    const ust = d.ustDugum;

    const ustBaglar = new Set<number>();
    if (ust >= 0) for (const i of h.bagIndeksi.get(ust) ?? []) ustBaglar.add(i);

    /* ---- BAĞLAR ---- */
    let cizilenBag = 0;
    let tavanDisi = 0;
    if (ust >= 0) {
      ctx.lineWidth = 1.5;
      for (const bi of ustBaglar) {
        const bag = h.baglar[bi];
        const ka = bag === undefined ? undefined : konumlar[bag.a];
        const kb = bag === undefined ? undefined : konumlar[bag.b];
        if (bag === undefined || ka === undefined || kb === undefined) continue;
        const ax = ka.x;
        const ay = ka.y;
        const bx = kb.x;
        const by = kb.y;
        const ox = (ax + bx) / 2 + (by - ay) * 0.08;
        const oy = (ay + by) / 2 - (bx - ax) * 0.08;
        ctx.strokeStyle = bag.renk;
        ctx.globalAlpha = 0.5;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.quadraticCurveTo(ox, oy, bx, by);
        ctx.stroke();
        if (hareket) {
          /* Eğri boyunca yürüyen ışık boncuğu: bağ statik bir çizgi değil, akan
             bir yol gibi okunur. Yön ÜZERİNE GELİNEN düğümden dışarıdır. */
          const ustten = bag.a === ust;
          const ham = (zaman * 0.22 + (bi % 13) / 13) % 1;
          const u = ustten ? ham : 1 - ham;
          const t = 1 - u;
          const px = t * t * ax + 2 * t * u * ox + u * u * bx;
          const py = t * t * ay + 2 * t * u * oy + u * u * by;
          ctx.globalAlpha = 0.9 * (0.4 + 0.6 * Math.sin(u * Math.PI));
          ctx.fillStyle = bag.renk;
          /* Boncuğun kendi parıltısı (üst yüzey `631-636`): gölge rengi bağın
             rengidir, yani jetondan gelir — sabit bir renk doğmuyor. */
          ctx.shadowColor = bag.renk;
          ctx.shadowBlur = 6;
          ctx.beginPath();
          ctx.arc(px, py, 2, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }
        cizilenBag++;
      }
      ctx.globalAlpha = 1;
    } else {
      const parilti = hareket ? 1 + 0.18 * Math.sin(zaman * 0.6) : 1;
      const alfa = (0.06 + Math.min(yakinlik * 0.04, 0.1)) * parilti;
      ctx.lineWidth = 0.4;
      ctx.globalAlpha = alfa;
      for (const [bi, bag] of h.baglar.entries()) {
        if (cizilenBag >= BAG_CIZIM_TAVANI) {
          /* TAVANIN DIŞINDA KALAN SAYILIR — ekran dışına düşenlerle KARIŞTIRILMAZ.
             İlk yazımda sayaç "çizilmeyen her bağ"dı ve kadraj dışındaki bağları da
             tavan kurbanı gibi gösteriyordu: kaydırınca değişen bir "tavan" sayısı,
             tavanı ölçülmüş bir sınır değil rastgele bir sayı gibi okuturdu. */
          tavanDisi = h.baglar.length - bi;
          break;
        }
        const ka = konumlar[bag.a];
        const kb = konumlar[bag.b];
        if (ka === undefined || kb === undefined) continue;
        const ax = ka.x;
        const ay = ka.y;
        const bx = kb.x;
        const by = kb.y;
        if (
          (ax < -KENAR_PAYI && bx < -KENAR_PAYI) ||
          (ax > G + KENAR_PAYI && bx > G + KENAR_PAYI) ||
          (ay < -KENAR_PAYI && by < -KENAR_PAYI) ||
          (ay > Y + KENAR_PAYI && by > Y + KENAR_PAYI)
        )
          continue;
        ctx.strokeStyle = bag.renk;
        const ox = (ax + bx) / 2 + (by - ay) * 0.08;
        const oy = (ay + by) / 2 - (bx - ax) * 0.08;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.quadraticCurveTo(ox, oy, bx, by);
        ctx.stroke();
        cizilenBag++;
      }
      ctx.globalAlpha = 1;
    }

    /* ---- KÜME KABARCIKLARI (noktaların ALTINDA) ---- */
    if (h.kumeler.length > 0) {
      ctx.save();
      ctx.lineJoin = "round";
      for (const kume of h.kumeler) {
        const noktalar: Nokta[] = [];
        for (const i of kume.uyeler) {
          const k = konumlar[i];
          if (k !== undefined) noktalar.push([k.x, k.y]);
        }
        if (noktalar.length === 0) continue;
        let ox = 0;
        let oy = 0;
        for (const [x, y] of noktalar) {
          ox += x;
          oy += y;
        }
        ox /= noktalar.length;
        oy /= noktalar.length;

        const pay = 26;
        let yaricap = pay;
        ctx.fillStyle = rgbaDizgesi(kume.renk, p.koyu ? 0.1 : 0.08);
        ctx.strokeStyle = rgbaDizgesi(kume.renk, 0.35);
        ctx.lineWidth = 1.25;
        ctx.beginPath();
        if (noktalar.length < 3) {
          for (const [x, y] of noktalar) yaricap = Math.max(yaricap, Math.hypot(x - ox, y - oy) + pay);
          ctx.arc(ox, oy, yaricap, 0, Math.PI * 2);
        } else {
          const zarf = disbukeyZarf(noktalar);
          for (const [j, [zx, zy]] of zarf.entries()) {
            const fx = zx - ox;
            const fy = zy - oy;
            const u = Math.hypot(fx, fy) || 1;
            const ex = zx + (fx / u) * pay;
            const ey = zy + (fy / u) * pay;
            if (j === 0) ctx.moveTo(ex, ey);
            else ctx.lineTo(ex, ey);
          }
          ctx.closePath();
        }
        ctx.fill();
        ctx.stroke();

        if (kume.etiket && yakinlik > 0.15) {
          ctx.font = '600 11px Inter, -apple-system, "Segoe UI", sans-serif';
          const genislik = ctx.measureText(kume.etiket).width + 16;
          let tepe = oy;
          for (const [, y] of noktalar) tepe = Math.min(tepe, y);
          const ey = tepe - pay - 12;
          ctx.fillStyle = rgbDizgesi(kume.renk);
          yuvarlakDikdortgen(ctx, ox - genislik / 2, ey - 9.5, genislik, 19, 9.5);
          ctx.fill();
          ctx.fillStyle = okunurYazi(p, kume.renk);
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(kume.etiket, ox, ey + 0.5);
        }
      }
      ctx.restore();
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
    }

    /* ---- NOKTALAR VE ETİKETLER ---- */
    const HUCRE = sikEtiket ? 28 : 90;
    const izgara = new Set<string>();
    const yerVar = (x: number, y: number, g: number, yk: number) => {
      const s0 = Math.floor(x / HUCRE);
      const s1 = Math.floor((x + g) / HUCRE);
      const r0 = Math.floor(y / HUCRE);
      const r1 = Math.floor((y + yk) / HUCRE);
      for (let s = s0; s <= s1; s++) for (let r = r0; r <= r1; r++) if (izgara.has(`${s},${r}`)) return false;
      return true;
    };
    const yerAl = (x: number, y: number, g: number, yk: number) => {
      const s0 = Math.floor(x / HUCRE);
      const s1 = Math.floor((x + g) / HUCRE);
      const r0 = Math.floor(y / HUCRE);
      const r1 = Math.floor((y + yk) / HUCRE);
      for (let s = s0; s <= s1; s++) for (let r = r0; r <= r1; r++) izgara.add(`${s},${r}`);
    };

    const etiketCiz = (
      g: HazirDugum,
      sx: number,
      sy: number,
      r: number,
      ustunde: boolean,
      zorla: boolean,
    ) => {
      const yazi = g.dugum.etiket;
      if (yakinlik > 1.5 || ustunde) {
        const kartG = Math.min(220, 80 + yakinlik * 25);
        ctx.font = YAZITIPI_KUCUK;
        const satirlar = satirlaraBol(ctx, yazi, kartG - 16, sarmaOnbellegi.current);
        const enFazla = ustunde ? Math.min(satirlar.length, 5) : Math.min(satirlar.length, Math.floor(yakinlik));
        if (enFazla <= 0) return;
        const kartY = 8 + enFazla * 15 + 8;
        const kx = sx - kartG / 2;
        const ky = sy + r + 4;
        ctx.fillStyle = ustunde ? p.renk.kart : rgbaDizgesi(p.rgb.zemin, 0.92);
        yuvarlakDikdortgen(ctx, kx, ky, kartG, kartY, 6);
        ctx.fill();
        ctx.strokeStyle = ustunde ? rgbDizgesi(g.renk) : p.renk.cerceve;
        ctx.lineWidth = ustunde ? 1.5 : 0.5;
        yuvarlakDikdortgen(ctx, kx, ky, kartG, kartY, 6);
        ctx.stroke();
        if (ustunde) {
          /* Kartın renkli halesi (üst yüzey `1035-1042`) — düğümün kendi rengiyle,
             yani jetondan. Kartı arkasındaki noktalardan ayıran şey bu. */
          ctx.shadowColor = rgbDizgesi(g.renk);
          ctx.shadowBlur = 15;
          yuvarlakDikdortgen(ctx, kx, ky, kartG, kartY, 6);
          ctx.stroke();
          ctx.shadowBlur = 0;
        }
        ctx.fillStyle = ustunde ? p.renk.yazi : p.renk.soluk;
        ctx.textAlign = "left";
        for (const [j, satir] of satirlar.slice(0, enFazla).entries()) {
          ctx.fillText(satir, kx + 8, ky + 8 + j * 15 + 11);
        }
      } else {
        ctx.font = YAZITIPI_KUCUK;
        ctx.fillStyle = ustunde ? p.renk.yazi : p.renk.soluk;
        ctx.globalAlpha = ustunde ? 1 : zorla ? 0.85 : Math.min(1, (yakinlik - 0.3) * 2.5);
        ctx.textAlign = "left";
        ctx.fillText(yazi.length > 45 ? `${yazi.slice(0, 45)}...` : yazi, sx + r + 5, sy + 4);
        ctx.globalAlpha = 1;
      }
    };

    let etiketSayisi = 0;
    let gorunurSayi = 0;
    /* ÜZERİNE GELİNEN EN SONA: en üstte çizilsin. Sıra bir liste kopyasıdır,
       indeks değil — konum nesnesi düğümü de taşıdığı için ikinci bir arama yok. */
    const sira: Konum[] = [];
    let ustKonum: Konum | null = null;
    for (const k of konumlar) {
      if (!k.gorunur) continue;
      if (k.i === ust) ustKonum = k;
      else sira.push(k);
    }
    if (ustKonum !== null) sira.push(ustKonum);

    for (const k of sira) {
      const g = k.g;
      const sx = k.x;
      const sy = k.y;
      gorunurSayi++;
      const ustunde = k.i === ust;
      const komsu =
        ustBaglar.size > 0 && (h.bagIndeksi.get(k.i) ?? []).some((bi) => ustBaglar.has(bi));

      const hamR = boyutRef.current
        ? boyutRef.current(g.dugum)
        : 2.5 + Math.min(g.bagSayisi * 0.15, 2.5);
      const nabiz = hareket ? 1 + 0.13 * Math.sin(zaman * 1.05 + g.faz) : 1;
      const r = Math.max(1.5, hamR * nabiz * Math.min(yakinlik, 2));

      const kirpisma = hareket ? 0.82 + 0.18 * Math.sin(zaman * 1.4 + g.faz * 2.1) : 1;
      const tabanAlfa = (0.45 + Math.min(g.bagSayisi * 0.03, 0.5)) * kirpisma;

      ctx.beginPath();
      ctx.arc(sx, sy, r, 0, Math.PI * 2);
      ctx.fillStyle = rgbDizgesi(g.renk);
      ctx.globalAlpha = ustunde ? 1 : komsu ? 0.95 : ust >= 0 ? 0.08 : tabanAlfa;
      if (ustunde || komsu) {
        ctx.shadowColor = rgbDizgesi(g.renk);
        ctx.shadowBlur = ustunde ? 20 : 10;
      }
      ctx.fill();

      if (g.bagSayisi > 3 && !ustunde && ust < 0) {
        const t = hareket ? 1 + 0.25 * Math.sin(zaman * 0.9 + g.faz * 1.7) : 1;
        ctx.beginPath();
        ctx.arc(sx, sy, r * 2, 0, Math.PI * 2);
        ctx.fillStyle = rgbDizgesi(g.renk);
        ctx.globalAlpha = (0.06 + Math.min(g.bagSayisi * 0.005, 0.08)) * t;
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;

      if (ustunde) {
        etiketCiz(g, sx, sy, r, true, true);
        etiketSayisi++;
      } else if (yakinlik > 1.5) {
        const kartG = Math.min(200, 80 + yakinlik * 25);
        const kx = sx - kartG / 2;
        const ky = sy + r + 4;
        if (yerVar(kx, ky, kartG, 50)) {
          yerAl(kx, ky, kartG, 50);
          etiketCiz(g, sx, sy, r, false, komsu);
          etiketSayisi++;
        }
      } else if (sikEtiket || yakinlik > 0.5 || komsu) {
        const eg = sikEtiket ? 60 : 155;
        const ey = sikEtiket ? 12 : 16;
        const kx = sx + r + 5;
        const ky = sy - 8;
        if (yerVar(kx, ky, eg, ey)) {
          yerAl(kx, ky, eg, ey);
          etiketCiz(g, sx, sy, r, false, komsu);
          etiketSayisi++;
        }
      }
    }

    /* ---- SAYAÇ ŞERİDİ (tuvalin altı) ---- */
    ctx.font = YAZITIPI_TEK_ARALIK;
    ctx.fillStyle = p.renk.soluk;
    ctx.textAlign = "left";
    ctx.fillText(
      `${n} düğüm · ${gorunurSayi} görünür · ${etiketSayisi} etiket · ${cizilenBag} bağ çizildi` +
        (tavanDisi > 0 ? ` (${tavanDisi} bağ çizim tavanının dışında)` : "") +
        ` · yakınlaştırma ${yakinlik.toFixed(2)}x`,
      12,
      Y - 12,
    );

    /* ---- BAĞ TÜRÜ EFSANESİ — YALNIZ VERİDE GEÇEN TÜRLER ----
       Üst yüzey dört türü SABİT çiziyor. Burada efsane veriden türer: veride
       olmayan bir türü çizmek, ekranda o türden bağ VARMIŞ gibi okunurdu
       (varlık grafında tek tür geçiyor ve dördü de yazsaydık üçü hayalet olurdu). */
    ctx.textAlign = "right";
    ctx.font = YAZITIPI_KALIN;
    let efsaneX = G - 12;
    for (const tur of [...h.bagTurleri].reverse()) {
      const etiket = BAG_TURU_ETIKETI[tur] ?? tur;
      const genislik = ctx.measureText(etiket).width;
      ctx.fillStyle = p.renk.soluk;
      ctx.fillText(etiket, efsaneX, Y - 12);
      efsaneX -= genislik + 4;
      ctx.fillStyle = p.renk[BAG_TURU_JETONU[tur] ?? "mavi"];
      ctx.beginPath();
      ctx.arc(efsaneX, Y - 15, 3, 0, Math.PI * 2);
      ctx.fill();
      efsaneX -= 14;
    }

    /* ---- ISI EFSANESİ — kümelendiğinde SUSAR, çünkü renk artık kümeyi anlatır ---- */
    if (h.kumeler.length === 0) {
      ctx.textAlign = "left";
      ctx.font = YAZITIPI_KALIN;
      ctx.fillStyle = p.renk.soluk;
      ctx.fillText((isiEtiketi ?? "BAĞ SAYISI").toLocaleUpperCase("tr-TR"), 12, 36);
      const [alt, ustUc] = isiUclari ?? ["az", "çok"];
      ctx.font = YAZITIPI_TEK_ARALIK;
      const bar = Math.max(80, ctx.measureText(alt).width + ctx.measureText(ustUc).width + 12);
      for (let x = 0; x < bar; x++) {
        ctx.fillStyle = rgbDizgesi(isiRengi(p, x / bar));
        ctx.fillRect(12 + x, 42, 1, 6);
      }
      ctx.fillStyle = p.renk.soluk;
      ctx.fillText(alt, 12, 60);
      ctx.textAlign = "right";
      ctx.fillText(ustUc, 12 + bar, 60);
    }

    /* ---- BOYUT EFSANESİ — yalnız boyut anlamlı bir şeyi kodluyorsa ---- */
    if (boyutEtiketi) {
      ctx.textAlign = "left";
      ctx.font = YAZITIPI_KALIN;
      ctx.fillStyle = p.renk.soluk;
      ctx.fillText(boyutEtiketi.toLocaleUpperCase("tr-TR"), 12, 82);
      ctx.font = YAZITIPI_TEK_ARALIK;
      ctx.fillText("az", 12, 98);
      const bas = 12 + ctx.measureText("az").width + 8;
      for (const [dx, dr] of [
        [2, 2],
        [14, 4],
        [30, 6],
      ] as const) {
        ctx.beginPath();
        ctx.arc(bas + dx, 94, dr, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillText("çok", bas + 42, 98);
    }

    /* ---- KULLANIM ---- */
    ctx.textAlign = "left";
    ctx.font = YAZITIPI_TEK_ARALIK;
    ctx.fillStyle = p.renk.soluk;
    ctx.fillText(
      dugumTiklandi
        ? "Tekerlek: yakınlaştır · Sürükle: kaydır · Üzerine gel: incele · Tıkla: aç"
        : "Tekerlek: yakınlaştır · Sürükle: kaydır · Üzerine gel: incele",
      12,
      16,
    );

    ctx.restore();

    /* Balonun içeriği React tarafında; burada yalnız HANGİ düğüm olduğu bildirilir. */
    if (ust !== ustuneGelinen) setUstuneGelinen(ust);

    return hareket || yerlesiyor;
  }, [boyutEtiketi, dugumTiklandi, isiEtiketi, isiUclari, sikEtiket, ustuneGelinen]);

  const cizRef = useRef(ciz);
  cizRef.current = ciz;

  /* ------------------------------------------------------------------------
     DÖNGÜ + OLAYLAR — bir kez kurulur, güncel değerleri referanstan okur
     ------------------------------------------------------------------------ */
  useEffect(() => {
    const tuval = tuvalRef.current;
    if (!tuval) return;

    const kare = () => {
      kareRef.current = 0;
      const devam = cizRef.current();
      if (devam && gorunurRef.current) {
        kareRef.current = requestAnimationFrame(kare);
      }
    };
    const iste = () => {
      if (kareRef.current || !gorunurRef.current) return;
      kareRef.current = requestAnimationFrame(kare);
    };
    kareIste.current = iste;

    const olc = () => {
      const dpr = window.devicePixelRatio || 1;
      const kutu = tuval.getBoundingClientRect();
      tuval.width = Math.max(1, Math.round(kutu.width * dpr));
      tuval.height = Math.max(1, Math.round(kutu.height * dpr));
      durum.current.dpr = dpr;
      durum.current.G = kutu.width;
      durum.current.Y = kutu.height;
    };
    olc();

    /* İLK ÇERÇEVELEME: `hazir` etkisi ölçümden ÖNCE koşmuş olabilir (genişlik o
       an 0'dı), o yüzden sığdırma burada bir kez daha kurulur. */
    let enUzak = 0;
    for (const g of hazirRef.current.dugumler) {
      const u = Math.sqrt(g.dx * g.dx + g.dy * g.dy);
      if (u > enUzak) enUzak = u;
    }
    const sigdir = sigdirmaYakinligi(enUzak, durum.current.G, durum.current.Y);
    durum.current.yakinlik = sigdir;
    durum.current.hedefYakinlik = sigdir;

    const pencereBoyu = () => {
      olc();
      iste();
    };
    const tekerlek = (e: WheelEvent) => {
      e.preventDefault();
      const kat = e.deltaY > 0 ? 0.9 : 1.1;
      durum.current.hedefYakinlik = Math.max(
        EN_KUCUK_YAKINLIK,
        Math.min(EN_BUYUK_YAKINLIK, durum.current.hedefYakinlik * kat),
      );
      iste();
    };
    /* KONUM FARENİN YANINDA AMA TUVALİN İÇİNDE. Ölçüm balonun KENDİ boyutuna
       bağlı; balon henüz gizliyken o boyut sıfırdır, o yüzden görünür olduğu anda
       bir kez daha çağrılır (aşağıdaki etki). Tek çağrıyla bırakılsaydı balon ilk
       göründüğü karede sağ/alt kenardan taşabilirdi. */
    const balonKonumu = () => {
      const balon = balonRef.current;
      if (!balon) return;
      const { fareX, fareY, G: g, Y: y } = durum.current;
      if (fareX < 0) return;
      balon.style.left = `${Math.max(4, Math.min(fareX + 16, g - balon.offsetWidth - 12))}px`;
      balon.style.top = `${Math.max(4, Math.min(fareY + 16, y - balon.offsetHeight - 12))}px`;
    };
    balonKonumRef.current = balonKonumu;
    const fareHareket = (e: MouseEvent) => {
      const kutu = tuval.getBoundingClientRect();
      durum.current.fareX = e.clientX - kutu.left;
      durum.current.fareY = e.clientY - kutu.top;
      if (durum.current.surukluyor) {
        durum.current.hedefKaydirmaX = durum.current.kaydirmaBasX + (e.clientX - durum.current.surukleBasX);
        durum.current.hedefKaydirmaY = durum.current.kaydirmaBasY + (e.clientY - durum.current.surukleBasY);
        tuval.style.cursor = "grabbing";
      } else {
        tuval.style.cursor =
          durum.current.ustDugum >= 0 && tiklamaRef.current ? "pointer" : "default";
        balonKonumu();
      }
      iste();
    };
    const fareBas = (e: MouseEvent) => {
      durum.current.surukluyor = true;
      durum.current.surukleBasX = e.clientX;
      durum.current.surukleBasY = e.clientY;
      durum.current.kaydirmaBasX = durum.current.kaydirmaX;
      durum.current.kaydirmaBasY = durum.current.kaydirmaY;
    };
    const fareBirak = () => {
      if (durum.current.surukluyor) {
        const fx = Math.abs(durum.current.kaydirmaX - durum.current.kaydirmaBasX);
        const fy = Math.abs(durum.current.kaydirmaY - durum.current.kaydirmaBasY);
        if (fx < 3 && fy < 3 && durum.current.ustDugum >= 0) {
          const g = hazirRef.current.dugumler[durum.current.ustDugum];
          if (g && tiklamaRef.current) tiklamaRef.current(g.dugum);
        }
      }
      durum.current.surukluyor = false;
      iste();
    };
    const fareCik = () => {
      durum.current.fareX = -1;
      durum.current.fareY = -1;
      durum.current.surukluyor = false;
      durum.current.ustDugum = -1;
      iste();
    };

    window.addEventListener("resize", pencereBoyu);
    tuval.addEventListener("wheel", tekerlek, { passive: false });
    tuval.addEventListener("mousemove", fareHareket);
    tuval.addEventListener("mousedown", fareBas);
    tuval.addEventListener("mouseup", fareBirak);
    tuval.addEventListener("mouseleave", fareCik);

    /* Kap yeniden akınca (yan panel açılması gibi) pencere olayı GELMEZ; tuvalin
       arkasındaki bitmap eski ölçüde kalır ve CSS onu gerdiği için yazı ezilir. */
    const boyutGozlemcisi =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            olc();
            iste();
          })
        : null;
    boyutGozlemcisi?.observe(tuval);

    /* GÖRÜNÜRLÜK KAPISI: ekranda olmayan bir tuval için kare harcamak, ölçülebilir
       bir bedeldir ve karşılığı hiçbir şeydir. */
    /* İKİ AYRI BAYRAK, "VE" İLE (inceleme M-7). Tek değişkene yazan ilk yazımda
       sekmeye geri dönmek, tuval ekranın DIŞINDA olsa bile döngüyü başlatıyordu
       (bir sonraki kesişme bildirimine kadar boşa dönen kareler). İki koşul ayrı
       ölçülüyor çünkü ayrı şeyler: "tuval kadrajda mı" ve "sekme önde mi". */
    let kadrajda = true;
    let sekmeOnde = typeof document === "undefined" || !document.hidden;
    const gorunurluk = () => {
      const deger = kadrajda && sekmeOnde;
      gorunurRef.current = deger;
      if (deger) iste();
      else if (kareRef.current) {
        cancelAnimationFrame(kareRef.current);
        kareRef.current = 0;
      }
    };
    const kesisme =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver((girisler) => {
            kadrajda = girisler.some((g) => g.isIntersecting);
            gorunurluk();
          })
        : null;
    kesisme?.observe(tuval);
    const sekme = () => {
      sekmeOnde = !document.hidden;
      gorunurluk();
    };
    document.addEventListener("visibilitychange", sekme);

    iste();

    return () => {
      if (kareRef.current) cancelAnimationFrame(kareRef.current);
      kareRef.current = 0;
      kareIste.current = () => undefined;
      balonKonumRef.current = () => undefined;
      window.removeEventListener("resize", pencereBoyu);
      tuval.removeEventListener("wheel", tekerlek);
      tuval.removeEventListener("mousemove", fareHareket);
      tuval.removeEventListener("mousedown", fareBas);
      tuval.removeEventListener("mouseup", fareBirak);
      tuval.removeEventListener("mouseleave", fareCik);
      boyutGozlemcisi?.disconnect();
      kesisme?.disconnect();
      document.removeEventListener("visibilitychange", sekme);
    };
  }, [cizilebilir]);

  /* Balon GÖRÜNÜR olduğu anda yeniden konumlanır: gizliyken ölçüsü sıfırdı ve
     ilk konum hesabı kenar taşmasını göremezdi. */
  useEffect(() => {
    if (ustuneGelinen >= 0) balonKonumRef.current();
  }, [ustuneGelinen]);

  if (palet === null) {
    return (
      <Olculemedi
        neden="Grafın renkleri okunamadı, bu yüzden graf çizilmedi"
        teknik="panonun tema renk değişkenleri okunamadı ya da tarayıcı bu renk biçimini çözemedi — sabit bir renkle çizmek tema anahtarını kıracağı için çizim durduruldu"
      />
    );
  }

  if (bos) {
    return (
      <p className="text-muted-foreground text-sm">
        Graf okundu ve çizilebilir düğüm YOK. Bu ölçülmüş bir boşluktur: ya bu bankada bağ kurulmuş
        kayıt yok, ya da seçilen süzgeç hepsini eliyor.
      </p>
    );
  }

  const ustDugum = ustuneGelinen >= 0 ? hazir.dugumler[ustuneGelinen] : null;

  return (
    <div className="flex flex-col gap-2">
      <div className="relative overflow-hidden rounded-lg border" style={{ height: `${yukseklik}px` }}>
        <canvas
          ref={tuvalRef}
          className="block h-full w-full touch-none"
          role="img"
          aria-label={aciklama}
        />
        <div
          ref={balonRef}
          className="pointer-events-none absolute z-20 max-w-[22rem] rounded-lg border bg-card p-3 text-xs shadow-lg"
          style={{ display: ustDugum ? "block" : "none" }}
        >
          {ustDugum ? <DugumKunyesi dugum={ustDugum.dugum} bagSayisi={ustDugum.bagSayisi} /> : null}
        </div>
      </div>
      {hazir.askidaBag > 0 ? (
        <p className="text-muted-foreground text-[11px] tabular-nums">
          {hazir.askidaBag.toLocaleString("tr-TR")} bağın öteki ucu dönen dilimde yok — bu uç
          sunucuda kırpılıyor, yani bağın karşı tarafı bankada var ama bu okumada gelmedi.
        </p>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ÜZERİNE GELİNEN DÜĞÜMÜN KÜNYESİ
   ----------------------------------------------------------------------------
   ÜST YÜZEY BUNU `innerHTML` İLE KURUYOR. Aynı şeyi yapmak, hafıza kaydının
   metnini — yani dışarıdan gelen içeriği — kaçırmadan sayfaya yazmak olurdu.
   Burada React çiziyor: içerik metin olarak kalır, işaretlemeye dönüşmez.
   --------------------------------------------------------------------------- */
function DugumKunyesi({ dugum, bagSayisi }: { readonly dugum: TakimyildiziDugumu; readonly bagSayisi: number }) {
  const k = dugum.kunye ?? null;
  const tur = k === null ? null : metin(k.fact_type);
  const govde = (k === null ? null : metin(k.text)) ?? dugum.etiket;
  const baglam = k === null ? null : metin(k.context);
  const baslangic = k === null ? null : damga(k.occurred_start);
  const bitis = k === null ? null : damga(k.occurred_end);
  const anilma = k === null ? null : damga(k.mentioned_at);
  /* KÜNYE SATIRI GELMEYEN DÜĞÜMDE DÜĞÜMÜN KENDİ TARİHİ OKUNUR (inceleme M-8).
     Bellek grafının düğümleri kendi gövdelerinde de bir tarih taşıyor; künye
     satırı eşleşmediğinde kartın tarih satırını boş bırakmak, elde duran bir
     ölçümü çizmemek olurdu. Künye varsa onun alanları tercih edilir — biri
     olayın zamanını, öteki kaydın damgasını söylüyor. */
  const dugumTarihi = baslangic === null && anilma === null && k !== null ? damga(k.date) : null;
  const kanit = k === null ? null : sayi(k.proof_count);
  const belge = k === null ? null : metin(k.document_id);
  const varliklar = k === null ? null : listeye(k.entities);
  const etiketler = k === null ? null : listeye(k.tags);

  return (
    <div className="flex flex-col gap-1.5">
      {/* TÜR ROZETİ YOKSA BOŞLUK DA YOK — VE BU BİR SESSİZLİK DEĞİL. Türü olmayan
          düğüm iki ayrı sebeple olabilir: varlık grafında böyle bir kavram YOKTUR
          (rozetin yeri de yoktur), bellek grafında ise künye satırı gelmemiştir ve
          KAÇININ öyle olduğu panelin üstünde sayıyla yazar. Buraya her düğüm için
          bir "gelmedi" cümlesi koymak, birinci hâli ikinciymiş gibi okuturdu. */}
      <div className="flex flex-wrap items-center gap-1.5">
        {tur === null ? null : (
          <Badge variant="outline" className="font-mono text-[10px]">
            {KUME_ETIKETI[tur] ?? tur}
          </Badge>
        )}
        <span className="text-muted-foreground text-[10px] tabular-nums">
          {bagSayisi.toLocaleString("tr-TR")} bağ
        </span>
      </div>
      <p className="line-clamp-6 text-xs leading-5">{govde}</p>
      {baglam || baslangic || anilma || dugumTarihi || kanit !== null || belge ? (
        <div className="flex flex-col gap-0.5 border-t pt-1.5">
          {baglam ? <KunyeSatiri etiket="Bağlam" deger={baglam} /> : null}
          {baslangic ? (
            <KunyeSatiri
              etiket="Gerçekleşme"
              deger={bitis && bitis !== baslangic ? `${baslangic} → ${bitis}` : baslangic}
            />
          ) : null}
          {anilma ? <KunyeSatiri etiket="Anılma" deger={anilma} /> : null}
          {dugumTarihi ? <KunyeSatiri etiket="Tarih" deger={dugumTarihi} /> : null}
          {kanit !== null && kanit > 1 ? (
            <KunyeSatiri etiket="Dayanak" deger={`${kanit.toLocaleString("tr-TR")} kaynak`} />
          ) : null}
          {belge ? <KunyeSatiri etiket="Belge" deger={belge} /> : null}
        </div>
      ) : null}
      {varliklar && varliklar.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {varliklar.slice(0, 8).map((v) => (
            <span key={v} className="rounded bg-muted px-1.5 py-0.5 text-[10px]">
              {v}
            </span>
          ))}
        </div>
      ) : null}
      {etiketler && etiketler.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {etiketler.slice(0, 8).map((e) => (
            <span key={e} className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
              #{e}
            </span>
          ))}
        </div>
      ) : null}
      {/* Kimlik en küçük adımda yazılır — üst yüzey burada 9 piksel kullanıyor ama
          panonun kendi tipografi rampasının en küçük basamağı 10; bir basamak
          uydurmak, tek bir satır için rampayı kırmak olurdu. */}
      <span className="break-all font-mono text-[10px] text-muted-foreground">{dugum.kimlik}</span>
    </div>
  );
}

function KunyeSatiri({ etiket, deger }: { readonly etiket: string; readonly deger: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="shrink-0 text-[10px] text-muted-foreground uppercase tracking-wide">{etiket}</span>
      <span className="min-w-0 truncate text-[11px]" title={deger}>
        {deger}
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   BELLEK GRAFI PANELİ — İKİ EKRANIN TEK KAYNAĞI
   ----------------------------------------------------------------------------
   İKİ KOPYA VARDI VE AYRIŞMAYA BAŞLAMIŞTI (inceleme I-1/I-2). Ana Sayfa'nın
   takımyıldızı ile Bellekler'in "Tam graf" paneli yapı olarak aynı bileşendi:
   aynı çözücü, aynı üç kapı, aynı kırpma zinciri, aynı rozet — ve aynı CÜMLELER
   iki (bir tanesi üç) dosyada birden yazılıydı. Ayrışma daha başlamıştı bile:
   kimliği okunamayan düğüm rozetini Ana Sayfa çiziyor, Tam graf ÇİZMİYORDU; yani
   aynı uç, aynı arıza, iki ayrı dürüstlük seviyesi. Operatör Tam graf kipinde
   "çizilen < vekil" farkını görüp NEDENİNİ göremiyordu.

   İKİ EKRAN ARTIK YALNIZ ÜÇ ŞEYDE AYRIŞIR ve üçü de prop: adı (ekran okuyucuya
   ne dendiği), yüksekliği, tıklama davranışı. Geri kalan her cümle burada, TEK
   yerde yaşar.
   --------------------------------------------------------------------------- */

export function GrafPaneli({
  zarf,
  ad,
  yukseklik,
  dugumTiklandi,
}: {
  readonly zarf: HafizaZarfi<BellekGrafi>;
  /** Ekran okuyucuya bu grafın adı — iki ekranda farklı, gerisi aynı. */
  readonly ad: string;
  readonly yukseklik: number;
  readonly dugumTiklandi?: (dugum: TakimyildiziDugumu) => void;
}) {
  const govde = zarf.govde ?? null;
  const cozum = useMemo(() => (govde === null ? null : bellekGrafiniCoz(govde)), [govde]);

  /* NOKTA BOYUTU — üst yüzeyin ana sayfa kuralı (`home-view.tsx:160-173`):
     bağ ağırlıklarının düğüm başına toplamı, karekök ölçekli. Ağırlık toplamı TEK
     yerde hesaplanır ve en büyüğü ondan türer: iki ayrı döngü aynı sayıyı iki kez
     üretirdi ve biri değişince öteki sessizce eskirdi. */
  const agirlik = useMemo(() => {
    const toplamlar = new Map<string, number>();
    if (cozum !== null) {
      for (const b of cozum.veri.baglar) {
        const w = b.agirlik !== null && b.agirlik > 0 ? b.agirlik : 1;
        toplamlar.set(b.kaynak, (toplamlar.get(b.kaynak) ?? 0) + w);
        toplamlar.set(b.hedef, (toplamlar.get(b.hedef) ?? 0) + w);
      }
    }
    let enAgir = 1;
    for (const v of toplamlar.values()) if (v > enAgir) enAgir = v;
    return { toplamlar, enAgir };
  }, [cozum]);

  const boyutFn = useCallback(
    (d: TakimyildiziDugumu) => 4 + Math.sqrt((agirlik.toplamlar.get(d.kimlik) ?? 0) / agirlik.enAgir) * 9,
    [agirlik],
  );

  if (zarf.neden) return <Olculemedi neden="Bellek grafı okunamadı" teknik={zarf.neden} />;
  if (govde === null || cozum === null) {
    return <Olculemedi neden="Bellek grafı için ölçüm denendi, gövde gelmedi" teknik="gövde boş döndü ve gerekçe de taşınmadı" />;
  }
  if (!Array.isArray(govde.nodes)) return <TaninmayanBicim />;

  return (
    <div className="flex flex-col gap-3">
      <KirpmaZinciri
        ne="kayıt"
        cizilen={cozum.veri.dugumler.length}
        vekil={cozum.vekilDugum}
        tavan={cozum.tavan}
        toplam={cozum.toplam}
      />

      <div className="flex flex-wrap items-center gap-2">
        <KimliksizRozeti sayi={cozum.kimliksiz} />
        {cozum.tursuz > 0 ? (
          <Badge
            variant="outline"
            className="font-normal text-[11px] text-muted-foreground"
            title="kayıt türü düğümün kendi gövdesinde değil, künye satırlarında yaşıyor; bu düğümlerin künyesi bu okumada gelmedi"
          >
            {cozum.tursuz} düğümün kayıt türü gelmedi — kümesiz çizildiler
          </Badge>
        ) : null}
      </div>

      <Takimyildizi
        veri={cozum.veri}
        yukseklik={yukseklik}
        kumele
        boyutFn={boyutFn}
        dugumTiklandi={dugumTiklandi}
        aciklama={`${ad}: ${cozum.veri.dugumler.length} kayıt, ${cozum.veri.baglar.length} bağ`}
      />

      {cozum.tursuz === cozum.veri.dugumler.length && cozum.veri.dugumler.length > 0 ? (
        <p className="text-muted-foreground text-[11px]">
          Kümeleme çizilmedi: bu okumada hiçbir düğümün kayıt türü gelmedi, o yüzden düğümler tek
          bir halkada duruyor ve renk kümeyi değil bağ sayısını gösteriyor.
        </p>
      ) : null}
    </div>
  );
}

/** "Gövde geldi ama düğümler dizi değil" cümlesi — ÜÇ dosyada birden yazılıydı
 *  (inceleme I-1). Şema sürüklenmesinin tarifi tek yerden gelir; iki kopya
 *  düzeltilirken biri unutulunca ekranda iki ayrı gerekçe kalırdı. */
export function TaninmayanBicim() {
  return (
    <Olculemedi
      neden="Graf düğümleri tanınmayan bir biçimde geldi"
      teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
    />
  );
}

/** Kimliği okunamayan/tekrarlı düğüm rozeti. Sıfırsa hiç çizilmez — sıfırı yazmak
 *  ölçülmüş bir boşluğu gürültüye çevirirdi. */
export function KimliksizRozeti({ sayi: adet }: { readonly sayi: number }) {
  if (adet <= 0) return null;
  return (
    <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
      {adet} düğümün kimliği okunamadı ya da tekrarlı geldi
    </Badge>
  );
}

/* ---------------------------------------------------------------------------
   TEL BİÇİMİ → ÇİZİLEBİLİR BİÇİM
   ----------------------------------------------------------------------------
   İki ayrı gövde, iki ayrı çevirici — ve ikisi de BURADA, çünkü ikisinin de tek
   tüketicisi bu bileşendir. Üst yüzey de aynı ayrımı yapıyor (paylaşılan bir
   `graph-data` modülü + görünüm başına eşleme).
   --------------------------------------------------------------------------- */

/**
 * Etiket kuralı — üst yüzeyin KENDİ çeviricisinden (`graph-data.ts:58-64`):
 * etiket → tablo satırının metni (40 karakterde kırpılır, üç nokta eklenir) →
 * kimliğin ilk 8 karakteri. Sayılar oradan, uydurma değil.
 *
 * NOT: takımyıldızın kendi iç yedeği BAŞKA bir sayı kullanıyor
 * (`constellation.tsx:372,1056`, kimliğin ilk 12'si) ve o yedek bizde HİÇ
 * çalışmaz: buradaki zincir her düğüme zaten bir etiket verdiği için çizim
 * tarafına boş etiket ulaşmıyor.
 */
function etiketSec(etiket: string | null, satirMetni: string | null, kimlik: string): string {
  if (etiket !== null && etiket !== "") return etiket;
  if (satirMetni !== null && satirMetni !== "") {
    return satirMetni.length > 40 ? `${satirMetni.slice(0, 40)}...` : satirMetni;
  }
  return kimlik.slice(0, 8);
}

export interface BellekGrafiCozumu {
  readonly veri: TakimyildiziVerisi;
  /** Vekilin DÖNDÜRDÜĞÜ düğüm/bağ sayısı (kırpma sonrası). */
  readonly vekilDugum: number;
  readonly vekilBag: number;
  /** Bankadaki toplam kayıt — `null` = alan gelmedi, UYDURULMAZ. */
  readonly toplam: number | null;
  /** Sunucunun uyguladığı tavan — `null` = bildirilmedi. */
  readonly tavan: number | null;
  /** Kimliği okunamadığı için hiç çizilemeyen düğüm sayısı. */
  readonly kimliksiz: number;
  /** Tablo satırında kayıt türü BULUNAMAYAN düğüm sayısı — kümesiz kalırlar. */
  readonly tursuz: number;
}

/**
 * BELLEK GRAFI — `nodes` / `edges` / `table_rows` üçlüsü.
 *
 * KÜME ANAHTARI ÖLÇÜLDÜ VE DÜĞÜMDE DEĞİL (A1, 2026-09-02): düğümün kendi
 * gövdesinde kayıt türü YOK; tür `table_rows` satırlarında yaşıyor ve kimlikle
 * eşleşiyor. Üst yüzey kümeyi düğümün tür alanından kuruyor — o alan bizim
 * ölçtüğümüz gövdede bulunmadığı için burada EŞLEME ile kuruluyor. Ölçülmüş bir
 * sapmadır; eşleşmeyen düğüm kümesiz kalır ve KAÇI olduğu sayılır.
 */
export function bellekGrafiniCoz(govde: BellekGrafi): BellekGrafiCozumu {
  const hamDugumler = Array.isArray(govde.nodes) ? govde.nodes : [];
  const hamBaglar = Array.isArray(govde.edges) ? govde.edges : [];
  const hamSatirlar = Array.isArray(govde.table_rows) ? govde.table_rows : [];

  const satirlar = new Map<string, GrafSatiri>();
  for (const s of hamSatirlar) {
    // ÖĞE KAPISI (nihai inceleme K-1, `parcalar.tsx::KovaSeridi` deseni): dizinin
    // İÇİ de doğrulanır. `null` bir öğe gelirse (şema sürüklenmesi) `s.id` bir tip
    // hatası atar ve BÜTÜN graf düşer — oysa bu dosyanın disiplini "tanımadığını
    // çiz, düşme". Kapı olmayan bir çözücü, sertleştirmenin eşit uygulanmamasıdır.
    if (sozluk(s) === null) continue;
    const kimlik = metin(s.id);
    if (kimlik !== null) satirlar.set(kimlik, s);
  }

  const dugumler: TakimyildiziDugumu[] = [];
  const kimlikler = new Set<string>();
  let kimliksiz = 0;
  let tursuz = 0;
  for (const d of hamDugumler) {
    // ÖĞE KAPISI (K-1): `d` sözlük değilse `d.data` bir tip hatası atar — `?.`
    // yalnız `d.data`nın YOKLUĞUNU karşılar, `d`nin kendisinin `null` olmasını
    // DEĞİL. Sözlük olmayan öğenin okunabilir bir kimliği yoktur; rozetin
    // cümlesi ("kimliği okunamadı") tam olarak bu hâli de tarif eder.
    const kimlik = sozluk(d) === null ? null : metin(d.data?.id);
    if (kimlik === null || kimlikler.has(kimlik)) {
      kimliksiz += 1;
      continue;
    }
    kimlikler.add(kimlik);
    const satir = satirlar.get(kimlik) ?? null;
    const tur = satir === null ? null : metin(satir.fact_type);
    if (tur === null) tursuz += 1;
    dugumler.push({
      kimlik,
      etiket: etiketSec(metin(d.data?.label), satir === null ? null : metin(satir.text), kimlik),
      kume: tur,
      kunye: satir === null ? (sozluk(d.data) as HamGovde | null) : (satir as HamGovde),
    });
  }

  const baglar: TakimyildiziBagi[] = [];
  for (const b of hamBaglar) {
    if (sozluk(b) === null) continue;              // ÖĞE KAPISI (K-1)
    const kaynak = metin(b.data?.source);
    const hedef = metin(b.data?.target);
    if (kaynak === null || hedef === null) continue;
    baglar.push({
      kaynak,
      hedef,
      tur: metin(b.data?.linkType) ?? (b.data?.lineStyle === "dashed" ? "temporal" : "semantic"),
      agirlik: sayi(b.data?.weight) ?? sayi(b.data?.similarity),
    });
  }

  return {
    veri: { dugumler, baglar },
    vekilDugum: hamDugumler.length,
    vekilBag: hamBaglar.length,
    toplam: sayi(govde.total_units),
    tavan: sayi(govde.limit),
    kimliksiz,
    tursuz,
  };
}

export interface VarlikGrafiCozumu {
  readonly veri: TakimyildiziVerisi;
  readonly vekilDugum: number;
  readonly vekilBag: number;
  readonly toplamDugum: number | null;
  readonly toplamBag: number | null;
  readonly tavan: number | null;
  readonly kimliksiz: number;
  /** Bağ ağırlıklarının düğüm başına toplamı — nokta boyutu bundan türer. */
  readonly agirliklar: ReadonlyMap<string, number>;
  /** Düğüm başına EN SON birlikte geçiş (ms) — ısı rengi bundan türer. */
  readonly tazelikler: ReadonlyMap<string, number>;
  /**
   * Isı ölçeğinin İKİ UCU — üst yüzeyin kuralı (`entities-view.tsx:200-219`):
   * aralık BÜTÜN kenar damgalarından kurulur, düğüm başına en son damgalardan
   * DEĞİL. İki türetim aynı değil: düğüm başına maksimumların en küçüğü, tüm
   * damgaların en küçüğünden her zaman eşit ya da DAHA YENİdir — yani efsanenin
   * sol ucundaki tarih ve rengin dağılımı sessizce kayardı.
   *
   * `null` = ölçek çizilemez (hiç damga yok ya da hepsi aynı ana düşüyor); üst
   * yüzey de o durumda ısı işlevini hiç vermiyor.
   */
  readonly tazelikAraligi: { readonly alt: number; readonly ust: number } | null;
}

/** VARLIK GRAFI — `nodes` / `edges`, tablo satırı YOK. */
export function varlikGrafiniCoz(govde: VarlikGrafi, damgaMs: (d: unknown) => number | null): VarlikGrafiCozumu {
  const hamDugumler = Array.isArray(govde.nodes) ? govde.nodes : [];
  const hamBaglar = Array.isArray(govde.edges) ? govde.edges : [];

  const dugumler: TakimyildiziDugumu[] = [];
  const kimlikler = new Set<string>();
  let kimliksiz = 0;
  for (const d of hamDugumler) {
    // ÖĞE KAPISI (K-1): `d` sözlük değilse `d.data` bir tip hatası atar — `?.`
    // yalnız `d.data`nın YOKLUĞUNU karşılar, `d`nin kendisinin `null` olmasını
    // DEĞİL. Sözlük olmayan öğenin okunabilir bir kimliği yoktur; rozetin
    // cümlesi ("kimliği okunamadı") tam olarak bu hâli de tarif eder.
    const kimlik = sozluk(d) === null ? null : metin(d.data?.id);
    if (kimlik === null || kimlikler.has(kimlik)) {
      kimliksiz += 1;
      continue;
    }
    kimlikler.add(kimlik);
    dugumler.push({
      kimlik,
      etiket: etiketSec(metin(d.data?.label), null, kimlik),
      kume: null,
      kunye: sozluk(d.data) as HamGovde | null,
    });
  }

  const baglar: TakimyildiziBagi[] = [];
  const agirliklar = new Map<string, number>();
  const tazelikler = new Map<string, number>();
  let enEski = Number.POSITIVE_INFINITY;
  let enYeni = Number.NEGATIVE_INFINITY;
  for (const b of hamBaglar) {
    if (sozluk(b) === null) continue;              // ÖĞE KAPISI (K-1)
    const kaynak = metin(b.data?.source);
    const hedef = metin(b.data?.target);
    if (kaynak === null || hedef === null) continue;
    const w = sayi(b.data?.weight) ?? sayi(b.data?.similarity) ?? 1;
    agirliklar.set(kaynak, (agirliklar.get(kaynak) ?? 0) + w);
    agirliklar.set(hedef, (agirliklar.get(hedef) ?? 0) + w);
    const son = damgaMs(b.data?.lastCooccurred);
    if (son !== null) {
      for (const u of [kaynak, hedef]) {
        const onceki = tazelikler.get(u);
        if (onceki === undefined || son > onceki) tazelikler.set(u, son);
      }
      if (son < enEski) enEski = son;
      if (son > enYeni) enYeni = son;
    }
    baglar.push({ kaynak, hedef, tur: metin(b.data?.linkType), agirlik: w });
  }

  return {
    veri: { dugumler, baglar },
    vekilDugum: hamDugumler.length,
    vekilBag: hamBaglar.length,
    toplamDugum: sayi(govde.total_entities),
    toplamBag: sayi(govde.total_edges),
    tavan: sayi(govde.limit),
    kimliksiz,
    agirliklar,
    tazelikler,
    tazelikAraligi:
      Number.isFinite(enEski) && Number.isFinite(enYeni) && enYeni !== enEski
        ? { alt: enEski, ust: enYeni }
        : null,
  };
}
