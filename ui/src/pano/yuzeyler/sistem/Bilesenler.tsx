"use client";

/* ============================================================================
   KATMAN 2 — MERIDIAN BİLEŞENLERİ (`/api/infra` · `bilesenler`)
   ----------------------------------------------------------------------------
   Makineden AYRI bir bölüm, çünkü ayrı bir soru: kutu boştayken tek bir birim
   belleği yiyor olabilir; kutu doluyken suçlu bir birim OLMAYABİLİR. İki katmanı
   tek tabloya sıkıştırmak, hangi müdahalenin (birimi yeniden başlat / makineyi
   büyüt) doğru olduğunu okunamaz hâle getirirdi.

   DÖRT TUZAK BURADA AÇIKÇA KARŞILANIYOR — dördü de bu depoda ÖLÇÜLMÜŞ vakalar:
   0) "inactive" TEK BAŞINA BİR HÜKÜM DEĞİLDİR (operatör, 2026-08-25: "neden kurulu
      değil, inaktif ve ölçülemedi gözüküyor"). Tablo ÜÇ AYRI DÜNYAYI tek kılıkta
      gösteriyordu: koşumlar arasında dinlenen bir `Type=oneshot` (timer'ı aktif),
      hiçbir şey arızalanmadığı için sessiz duran bir `OnFailure` kancası, ve
      gerçekten düşmüş bir servis. Rozet artık ham `ActiveState`ten değil, ucun
      ölçüme dayalı hükmünden (`durum_sinifi`) üretiliyor — ham alanlar ipucunda.
      TERS YÖN DE ÇİVİLİ: `oneshot` OLDUĞU ölçülemeyen bir duruş "sağlıklı" SAYILMAZ;
      gürültüyü susturayım derken sinyali susturmak kusuru ikiye katlardı.
      Aynı kusurun ikinci yarısı: "kurulu değil" İKİ AYRI İŞTİR — biri operatörden
      sudo bekler (`meridian-aylik-bucket-kopya`), öteki hiçbir şey beklemez
      (`deploy/` kökündeki eski kopyalar). Ayrımın otoritesi `dagit.sh`.
   1) ŞABLON BİRİM (`meridian-sprint@.service`): düz adla `systemctl show` SAHTE
      bir `inactive` döndürür. Hafıza kaydı "meridian-sprint şablon birim": pano
      "koşmuyor" dedi, gerçek ise "koştu, aday geçmedi"ydi. Uç şablonun durumunu
      UYDURMUYOR (None + neden) ve tablo bunu "ölçülemedi" diye gösteriyor —
      "kapalı" diye DEĞİL.
   2) `MemoryCurrent` SENTİNELİ: systemd ayarsızken 2^64-1 döndürür. 18 exabaytlık
      bir RSS çizmek, ölçülmemiş bir değeri sayıya çevirmenin ders kitabı örneği.
      Uç onu None + neden yapıyor; biz de payı hesaplarken o satırı DIŞARIDA
      bırakıyor ve kaç satır elendiğini yazıyoruz (sessiz eleme yok).
   3) CPU BİR DELTA'DIR: tek örnekle ölçülemez. İlk ankette `cpu_yuzde` None +
      neden gelir ve sütun `0,0%` DEĞİL "ölçülemedi" der.

   `bilesenler === null` İLE BOŞ LİSTE AYRI: birincisi "systemctl yok / ölçemedim"
   (uç `bilesenler_olculemedi_neden` ile söylüyor), ikincisi "hiç birim yok".
   ============================================================================ */
import { Boxes } from "lucide-react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, Satir, baytMetni, sureMetni } from "./parcalar";
import type { InfraBilesen, InfraDurumSinifi, InfraGovdesi } from "./uctipleri";

/** Yığılmış çubukta en çok bu kadar AYRI bileşen; kalanı tek "diğer" dilimine iner.
 *  Sınır palet genişliğinden geliyor: `--chart-1..5` beş rol jetonu var ve altıncı
 *  dilim bir rengi TEKRAR ederdi — aynı renk iki farklı bileşen demek okunamaz bir grafiktir. */
const DILIM_TAVANI = 5;

/* --- ROZET SÖZLÜĞÜ ---------------------------------------------------------
   "inactive" TEK BAŞINA BİR HÜKÜM DEĞİLDİR (operatör kusuru, 2026-08-25). Ham `ActiveState`
   basmak üç ayrı dünyayı tek kılığa sokuyordu: koşumlar arasında dinlenen bir `oneshot`, hiçbir
   şey arızalanmadığı için sessiz duran bir `OnFailure` kancası, ve gerçekten düşmüş bir servis.
   Hükmü uç kuruyor (`api.py::_infra_durum_sinifi`) çünkü hüküm ÖLÇÜMDEN doğar — `Type`,
   `TriggeredBy`, `OnFailureOf`. Burası yalnız o hükmü İNSAN DİLİNE çevirir.

   TON, HÜKMÜN AĞIRLIĞIDIR: `iyi` yeşil (eylem yok), `notr` sessiz (eylem yok, gürültü),
   `dikkat` amber (bakmak gerek — sağlık İDDİA EDİLMİYOR), `kotu` kırmızı (gerçek arıza).
   `dikkat` ile `iyi` arasındaki sınır bu kartın omurgası: ölçemediğimiz bir tetikleyiciyi
   "sağlıklı" saymak, gürültüyü susturayım derken SİNYALİ susturmak olurdu. */
type RozetTonu = "iyi" | "notr" | "dikkat" | "kotu";

const SINIF: Record<InfraDurumSinifi, { etiket: string; ton: RozetTonu; ipucu: string }> = {
  kosuyor: { etiket: "koşuyor", ton: "iyi", ipucu: "`ActiveState=active`" },
  sirada_timer: {
    etiket: "sırada · timer aktif",
    ton: "iyi",
    ipucu: "`Type=oneshot`: birim koşumlar ARASINDA durur. Tetikleyen timer aktif ölçüldü.",
  },
  ariza_yok_onfailure: {
    etiket: "arıza yok · OnFailure",
    ton: "iyi",
    ipucu: "Timer'ı yok; `OnFailure` ile tetiklenir. Durması HİÇBİR ŞEY ARIZALANMADI demektir.",
  },
  tetikleyici_bozuk: {
    etiket: "timer'ı ölü",
    ton: "kotu",
    ipucu: "`Type=oneshot` ama tetikleyen timer aktif değil — bu birim HİÇ koşmuyor olabilir.",
  },
  tetikleyici_olculemedi: {
    etiket: "tetikleyici ölçülemedi",
    ton: "dikkat",
    ipucu: "Tetikleyici bu istekte ölçülmedi — sağlıklı olduğu VARSAYILMIYOR.",
  },
  tetikleyici_yok: {
    etiket: "tetikleyicisiz",
    ton: "dikkat",
    ipucu: "`Type=oneshot` ama ne timer ne `OnFailure` bağı görüldü — bağlanmayı bekliyor olabilir.",
  },
  olu: {
    etiket: "durmuş",
    ton: "kotu",
    ipucu: "Koşumlar arasında dinlenen bir `oneshot` OLDUĞU ölçülmedi — bu duruş sağlıklı sayılmaz.",
  },
  arizali: { etiket: "arızalı", ton: "kotu", ipucu: "`failed`: koşmadı DEĞİL — koştu ve DÜŞTÜ." },
  kurulmali: {
    etiket: "kurulmalı",
    ton: "dikkat",
    ipucu: "Birim dosyası `deploy/<host>/` altında var ama makineye kurulmamış — sudo, operatör işi.",
  },
  envanter_gurultusu: {
    etiket: "kurulması beklenmiyor",
    ton: "notr",
    ipucu: "`deploy/` kökünde duran eski/genel kopya — dagit kurulum kıyasına almaz. Eksik DEĞİL.",
  },
  olculemedi: {
    etiket: "ölçülemedi",
    ton: "notr",
    ipucu: "Şablon birim / bütçe aşımı / systemctl hatası — durum UYDURULMUYOR.",
  },
};

const TON_METNI: Record<RozetTonu, string> = {
  iyi: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  notr: "text-muted-foreground",
  dikkat: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  kotu: "",
};
const TON_NOKTASI: Record<RozetTonu, string> = {
  iyi: "bg-emerald-500",
  notr: "bg-muted-foreground/60",
  dikkat: "bg-amber-500",
  kotu: "bg-destructive",
};

/* --- BEKLENEN ile ÖLÇÜLEN: İKİ AYRI SORU, İKİ AYRI KAYNAK ------------------
   "Bu birim kurulu MU" (systemd `LoadState`) ile "kurulu OLMALI MIYDI" (`deploy/<host>/`
   altında dosyası var mı; otorite `dagit.sh`) farklı dünyalardır ve uç ikisini AYRI alanlarda
   yayınlar. Pano bugüne dek yalnız ucun VARDIĞI SONUCU (`durum_sinifi`) çiziyordu; sonucun
   dayandığı `beklenen`/`beklenen_neden`/`servis_turu_neden` alanlarının HİÇ okuyucusu yoktu
   (YASA 6 boşluğu). Aşağıdaki dört okuyucu o boşluğu kapatır ve saf tutulur (JSX yok, kancasız):
   davranışları `tests/test_infra_okuyucu_v316.py` içinde node'da GERÇEKTEN koşturularak ölçülür,
   "kaynakta şu dize geçiyor mu" diye değil. */

export type BeklentiHali = "kurulmali" | "beklenmiyor" | "olculemedi";

/**
 * BEKLENEN taraf — kaynağı DİSK (`deploy/<host>/`), systemd DEĞİL. Üç değerli.
 *
 * TUZAK, ÖLÇÜLDÜ (2026-08-25): `beklenen_neden` bir "ölçülemedi" İŞARETİ DEĞİLDİR —
 * `api.py::_infra_birim_adlari` onu HEM `true` HEM `false` dalında doldurur, yani her zaman
 * doludur ve GEREKÇEdir. "Ölçülemedi" hâlinin tek işareti `beklenen`in kendisinin gelmemesidir
 * (uç eski gövde döndürürse). Nedene bakıp hüküm kurmak, her satırı "ölçülemedi" ilan ederdi.
 */
export function beklentiOku(b: InfraBilesen): { hal: BeklentiHali; neden: string } {
  if (b.beklenen === true)
    return {
      hal: "kurulmali",
      neden: b.beklenen_neden ?? "uç `beklenen: true` dedi ama gerekçesini yazmadı",
    };
  if (b.beklenen === false)
    return {
      hal: "beklenmiyor",
      neden: b.beklenen_neden ?? "uç `beklenen: false` dedi ama gerekçesini yazmadı",
    };
  // `false` VARSAYILMAZ: "kurulması beklenmiyor" bir SUSTURMA hükmüdür ve gerçek bir eksiği
  // envanter gürültüsü sayardı. Ölçülmeyen beklenti hüküm kurdurmaz.
  return {
    hal: "olculemedi",
    neden:
      b.beklenen_neden ??
      "/api/infra bu satır için `beklenen` bildirmedi — birimin kurulmasının BEKLENİP beklenmediği bilinmiyor",
  };
}

/** ÖLÇÜLEN taraf — systemd `LoadState`. `null` = sorulamadı (şablon/bütçe/systemctl hatası). */
export function kuruluOku(b: InfraBilesen): {
  hal: "kurulu" | "kurulu_degil" | "olculemedi";
  neden: string;
} {
  if (b.kurulu === true) return { hal: "kurulu", neden: b.kurulu_neden ?? "`LoadState=loaded` ölçüldü" };
  if (b.kurulu === false)
    return {
      hal: "kurulu_degil",
      neden: b.kurulu_neden ?? "uç `kurulu: false` dedi ama gerekçesini yazmadı",
    };
  return {
    hal: "olculemedi",
    neden: b.kurulu_neden ?? "/api/infra bu satır için `kurulu` bildirmedi — `LoadState` sorulamadı",
  };
}

/**
 * KANIT KAPISI — rozetin yeşil/sessiz tonu bir SAĞLIK İDDİASIDIR ve iddia ancak KANITI
 * ÖLÇÜLDÜYSE kurulur (UYDURMA YASAĞI'nın ekran tarafı).
 *
 * Hangi iddia neye dayanıyor: `sirada_timer` ve `ariza_yok_onfailure` "duruş NORMAL" der ve bu
 * tamamen `Type=oneshot` ölçümüne dayanır — `servis_turu` gelmediyse (şablon / bütçe aşımı /
 * `systemctl` hatası dallarında gelmez, gerekçe `servis_turu_neden`dedir) birimin koşumlar
 * arasında dinlenen bir oneshot OLDUĞU bilinmiyordur. `envanter_gurultusu` ise "eksik DEĞİL" der
 * ve tamamen `beklenen === false` ölçümüne dayanır. `kosuyor` yeşili ham `ActiveState=active`
 * ölçümüne dayanır; sınıf ile ham durum ayrıştıysa (uç gerilemesi) yeşil iddia edilemez.
 *
 * Kanıt eksikse ton `dikkat`e düşer — susturmak DEĞİL, sağlığı İDDİA ETMEMEK.
 */
export function kanitKapisi(
  b: InfraBilesen,
  sinif: InfraDurumSinifi,
  ton: RozetTonu,
): { ton: RozetTonu; eksik: string | null } {
  const turNedeni = b.servis_turu_neden ?? "uç `servis_turu` de `servis_turu_neden` de yazmadı";
  if (sinif === "sirada_timer" || sinif === "ariza_yok_onfailure") {
    if (b.servis_turu !== "oneshot")
      return { ton: "dikkat", eksik: `\`Type=oneshot\` ölçülmedi — ${turNedeni}` };
  } else if (sinif === "envanter_gurultusu") {
    if (b.beklenen !== false)
      return { ton: "dikkat", eksik: `\`beklenen === false\` ölçülmedi — ${beklentiOku(b).neden}` };
  } else if (sinif === "kurulmali") {
    if (b.beklenen !== true)
      return { ton: "dikkat", eksik: `\`beklenen === true\` ölçülmedi — ${beklentiOku(b).neden}` };
  } else if (sinif === "kosuyor") {
    if (b.durum !== "active")
      return {
        ton: "dikkat",
        eksik: `sınıf \`kosuyor\` ama ham \`ActiveState\` \`${b.durum ?? "gelmedi"}\` — ikisi ayrışmış`,
      };
  }
  return { ton, eksik: null };
}

/**
 * systemd BAĞ LİSTELERİ (`TriggeredBy` / `OnFailureOf`). BOŞ LİSTE BİR CEVAP DEĞİLDİR.
 *
 * Satır sözlüğü bu iki alanı `[]` ile başlatır ve şablon / bütçe aşımı / `systemctl` hatası
 * dallarında `[]` olarak gövdeye gider — o dallarda `_neden` eşleri YOKTUR, yani "sorulmadı" ile
 * "soruldu, bağ yok" gövdede aynı görünür. Ucun kendi şerhi de bunu söyler
 * (`api.py::_systemd_liste`: boş liste "bağ yok" DEĞİL "bu çıktıda bağ görünmedi" demektir).
 * Bu yüzden boş liste burada bir OLUMSUZLUK KANITI'na çevrilmez.
 */
export function baglarOku(b: InfraBilesen): {
  timerlar: readonly string[];
  onfailure: readonly string[];
  olculdu: boolean;
  neden: string | null;
} {
  const timerlar = b.tetikleyen_timerlar ?? [];
  const onfailure = b.onfailure_kaynaklari ?? [];
  if (timerlar.length > 0 || onfailure.length > 0) return { timerlar, onfailure, olculdu: true, neden: null };
  return {
    timerlar,
    onfailure,
    olculdu: false,
    neden: b.servis_turu_neden
      ? `\`TriggeredBy\`/\`OnFailureOf\` bu satırda sorulamadı — ${b.servis_turu_neden}`
      : "`TriggeredBy`/`OnFailureOf` çıktıda görünmedi — uç boş listeyi 'bağ yok' diye YAZMIYOR " +
        "(`api.py::_systemd_liste` şerhi), bağın olmadığı İDDİA EDİLMİYOR",
  };
}

const BEKLENTI_METNI: Record<BeklentiHali, string> = {
  kurulmali: "kurulu olmalı",
  beklenmiyor: "kurulması beklenmiyor",
  olculemedi: "ölçülemedi",
};

/** Satırın kendi sınıfı; uç bildirmediyse (eski gövde) UYDURULMAZ — `olculemedi`ye düşer. */
function sinifiOku(b: InfraBilesen): { sinif: InfraDurumSinifi; neden: string } {
  const s = b.durum_sinifi;
  if (s && s in SINIF) return { sinif: s, neden: b.durum_sinifi_neden ?? "uç gerekçe yazmadı" };
  return {
    sinif: "olculemedi",
    neden:
      "/api/infra bu satır için `durum_sinifi` bildirmedi — ham `ActiveState` tek başına bir hüküm " +
      "değildir (oneshot birimler koşumlar arasında zaten `inactive` görünür), o yüzden hüküm kurulmuyor",
  };
}

function durumRozeti(b: InfraBilesen) {
  const { sinif, neden } = sinifiOku(b);
  const k = SINIF[sinif];
  // TON KAPIDAN GELİR, ham sınıftan DEĞİL: kanıtı ölçülmemiş bir hüküm yeşile boyanamaz.
  const kapi = kanitKapisi(b, sinif, k.ton);
  const bag = baglarOku(b);
  const bek = beklentiOku(b);
  // Ham `ActiveState`/`Type`/tetikleyici İPUCUNDA kalır: hüküm ekranda, kanıtı fare altında.
  // `Type` YOKLUĞU DA BİR KAYIT: eskiden satır sessizce atlanıyordu ve ipucu "Type ölçülmedi" ile
  // "Type ölçüldü, oneshot değil" arasındaki farkı hiç göstermiyordu.
  const kanit = [
    b.durum ? `ActiveState=${b.durum}` : null,
    b.alt_durum ? `SubState=${b.alt_durum}` : null,
    b.servis_turu
      ? `Type=${b.servis_turu}`
      : `Type ölçülmedi — ${b.servis_turu_neden ?? "uç gerekçe yazmadı"}`,
    bag.olculdu
      ? [
          bag.timerlar.length > 0 ? `TriggeredBy=${bag.timerlar.join(" ")}` : null,
          bag.onfailure.length > 0 ? `OnFailureOf=${bag.onfailure.join(" ")}` : null,
        ]
          .filter(Boolean)
          .join(" · ")
      : bag.neden,
    `beklenen: ${BEKLENTI_METNI[bek.hal]} — ${bek.neden}`,
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <Badge
      variant={kapi.ton === "kotu" ? "destructive" : "outline"}
      className={cn("gap-1.5", TON_METNI[kapi.ton])}
      title={`${k.ipucu}\n${neden}${kapi.eksik ? `\nKANIT EKSİK: ${kapi.eksik}` : ""}\n${kanit}`}
    >
      <span className={cn("size-1.5 rounded-full", TON_NOKTASI[kapi.ton])} />
      {k.etiket}
      {kapi.eksik ? " · kanıtsız" : ""}
    </Badge>
  );
}

/**
 * BEKLENEN ile ÖLÇÜLEN'i AYNI HÜCREDE ama AYRI SATIRLARDA gösterir — operatörün
 * 2026-08-25'te sorduğu soru ("neden kurulu değil, inaktif ve ölçülemedi gözüküyor")
 * tam olarak bu iki dünyanın tek kılığa girmesinden doğmuştu.
 *
 * ÜÇÜNCÜ SATIR BAĞLAR: boş liste "bağ yok" DİYE ÇİZİLMEZ (`baglarOku` şerhi); ölçülmediyse
 * ekranda da bir cevap gibi durmaz.
 */
function BeklentiHucresi({ b }: { readonly b: InfraBilesen }) {
  const bek = beklentiOku(b);
  const kur = kuruluOku(b);
  const bag = baglarOku(b);
  const bagMetni = [...bag.timerlar, ...bag.onfailure].join(" ");
  return (
    <span className="flex flex-col gap-0.5 text-xs">
      <span title={bek.neden}>
        <span className="text-muted-foreground">beklenen: </span>
        <span
          className={cn(
            bek.hal === "kurulmali" && "text-amber-600 dark:text-amber-400",
            bek.hal === "olculemedi" && "text-muted-foreground italic",
          )}
        >
          {BEKLENTI_METNI[bek.hal]}
        </span>
      </span>
      <span title={kur.neden}>
        <span className="text-muted-foreground">ölçülen: </span>
        {kur.hal === "olculemedi" ? (
          <span className="text-muted-foreground italic">ölçülemedi</span>
        ) : (
          <span className={cn(kur.hal === "kurulu_degil" && "text-amber-600 dark:text-amber-400")}>
            {kur.hal === "kurulu" ? "kurulu" : "kurulu değil"}
          </span>
        )}
      </span>
      <span className="truncate text-muted-foreground" title={bag.neden ?? bagMetni}>
        bağ: {bag.olculdu ? bagMetni : <span className="italic">çıktıda görünmedi</span>}
      </span>
    </span>
  );
}

export function Bilesenler({ durum }: { readonly durum: Durum<InfraGovdesi> }) {
  return (
    <BolumKart
      kimlik="bilesenler"
      baslik="Meridian bileşenleri"
      soru="Hangi birim koşuyor, ne kadar kaynak yiyor?"
      ikon={Boxes}
    >
      <Kapi durum={durum} yol="/api/infra">
        {(g) => {
          if (g.bilesenler === null) {
            return (
              <Olculemedi
                neden="Bileşen listesi ölçülemedi"
                teknik={
                  g.bilesenler_olculemedi_neden ??
                  "/api/infra `bilesenler` null döndürdü ama nedenini yazmadı — boş liste 'bileşen yok' diye okunurdu"
                }
              />
            );
          }
          if (g.bilesenler === undefined) {
            return <Olculemedi neden="Bileşen listesi bildirilmedi" teknik="/api/infra `bilesenler` alanını hiç döndürmüyor" />;
          }
          const satirlar = g.bilesenler;
          if (satirlar.length === 0) {
            return (
              <p className="text-muted-foreground text-sm">
                Uç ölçtü ve HİÇ birim bulmadı (boş liste). Bu "ölçemedim" DEĞİL — ölçemediğinde uç
                `bilesenler: null` + neden döndürüyor.
              </p>
            );
          }

          // --- BELLEK PAYI: yalnız RSS'İ ÖLÇÜLMÜŞ satırlar; elenenler sayılıp yazılır.
          const olculen = satirlar.filter((b) => typeof b.rss_bayt === "number" && b.rss_bayt >= 0);
          const elenen = satirlar.length - olculen.length;
          const sirali = [...olculen].sort((a, b) => (b.rss_bayt ?? 0) - (a.rss_bayt ?? 0));
          const ust = sirali.slice(0, DILIM_TAVANI);
          const kalan = sirali.slice(DILIM_TAVANI);
          const kalanToplam = kalan.reduce((t, b) => t + (b.rss_bayt ?? 0), 0);
          const toplamRss = sirali.reduce((t, b) => t + (b.rss_bayt ?? 0), 0);

          // Anahtarlar CSS değişkeni adına giriyor (`--color-<anahtar>`), bu yüzden birim adı
          // DEĞİL güvenli bir takma ad kullanılıyor: `meridian-sprint@.service` içindeki `@` ve `.`
          // geçerli bir özel-özellik adı üretmez.
          const yapilandirma: ChartConfig = {};
          ust.forEach((b, i) => {
            yapilandirma[`b${i}`] = { label: b.ad ?? `birim #${i + 1}`, color: `var(--chart-${i + 1})` };
          });
          if (kalan.length > 0) {
            yapilandirma.diger = { label: `diğer (${kalan.length} bileşen)`, color: "var(--muted-foreground)" };
          }
          const cubuk: Record<string, number | string> = { ad: "RSS payı" };
          ust.forEach((b, i) => {
            cubuk[`b${i}`] = b.rss_bayt ?? 0;
          });
          if (kalan.length > 0) cubuk.diger = kalanToplam;

          const sayi = (...siniflar: readonly InfraDurumSinifi[]) =>
            satirlar.filter((b) => siniflar.includes(sinifiOku(b).sinif)).length;
          const aktifN = sayi("kosuyor");
          // SAĞLIKLI BEKLEYİŞ: `inactive` görünen ama tetikleyicisi ÖLÇÜLMÜŞ ve sağlam birimler.
          // Bu sayı olmasaydı operatör tabloda üç "duruyor" görür ve üçünü de iş sanardı.
          const bekleyenN = sayi("sirada_timer", "ariza_yok_onfailure");
          // İKİ "KURULU DEĞİL" AYRI SAYILIR: biri sudo bekler, öteki hiçbir şey beklemez.
          // Tek sayıya toplamak, gerçek eylemi envanter gürültüsünün içinde kaybediyordu.
          const kurulmaliN = satirlar.filter((b) => sinifiOku(b).sinif === "kurulmali").length;
          const gurultuN = sayi("envanter_gurultusu");
          const sablonN = satirlar.filter((b) => b.sablon).length;
          // DİKKAT KOVASI: gerçekten düşmüş servisler + sağlığı ÖLÇÜLEMEYEN tetikleyiciler.
          // Şablon ve envanter satırları buraya GİRMEZ (adlandırılmış, eylemsiz hâller).
          const dikkatN = sayi("olu", "arizali", "tetikleyici_bozuk", "tetikleyici_olculemedi",
                               "tetikleyici_yok");
          // BEKLENTİSİ ÖLÇÜLEMEYEN SATIRLAR AYRI SAYILIR: "kurulmalı" ile "beklenmiyor" arasındaki
          // fark bir EYLEM farkıdır (sudo mu, hiçbir şey mi) ve ölçülemediğinde ikisi de iddia
          // edilemez. Sayı ekranda durmasaydı, hüküm kurulamayan satırlar tabloda kaybolurdu.
          const beklentisizN = satirlar.filter((b) => beklentiOku(b).hal === "olculemedi").length;
          // KANITI EKSİK OLDUĞU İÇİN İDDİASI GERİ ÇEKİLEN SATIRLAR (`kanitKapisi`).
          const kanitsizN = satirlar.filter((b) => kanitKapisi(b, sinifiOku(b).sinif,
                                                               SINIF[sinifiOku(b).sinif].ton).eksik !== null).length;
          const surec = g.surec;

          return (
            <>
              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="Bildirilen birim">
                    <span className="tabular-nums">{satirlar.length}</span>
                  </Satir>
                  <Satir etiket="Koşan (active)">
                    <span className="tabular-nums text-emerald-600 dark:text-emerald-400">{aktifN}</span>
                  </Satir>
                  <Satir etiket="Sağlıklı bekleyiş (oneshot)">
                    <span
                      className="tabular-nums text-emerald-600 dark:text-emerald-400"
                      title="Duruyor görünen ama tetikleyicisi ÖLÇÜLMÜŞ ve sağlam birimler: timer'ı aktif olanlar + `OnFailure` kancaları. Eylem gerektirmez."
                    >
                      {bekleyenN}
                    </span>
                  </Satir>
                  <Satir etiket="Kurulmalı (eylem) / şablon">
                    <span className="tabular-nums">
                      <span
                        className={cn(kurulmaliN > 0 && "font-medium text-amber-600 dark:text-amber-400")}
                        title="Birim dosyası `deploy/<host>/` altında var ama makineye kurulmamış — sudo ister, operatör işi."
                      >
                        {kurulmaliN}
                      </span>
                      {" / "}
                      <span title="`@.service` şablonu — düz adla sorgu sahte `inactive` verir, durumu `/api/sprint`ten okunur">
                        {sablonN}
                      </span>
                    </span>
                  </Satir>
                  <Satir etiket="Envanter kopyası (eylemsiz)">
                    <span
                      className="tabular-nums text-muted-foreground"
                      title="`deploy/` kökünde duran eski/genel birim dosyaları — kurulmaları BEKLENMİYOR, eksik değiller."
                    >
                      {gurultuN}
                    </span>
                  </Satir>
                  <Satir etiket="Dikkat gerektiren">
                    <span className={cn("tabular-nums", dikkatN > 0 && "text-amber-600 dark:text-amber-400")}>
                      {dikkatN}
                      {dikkatN > 0 ? " (durmuş / arızalı / tetikleyicisi ölçülemeyen)" : ""}
                    </span>
                  </Satir>
                  <Satir etiket="Kurulum beklentisi ölçülemeyen">
                    <span
                      className="tabular-nums text-muted-foreground"
                      title="Uç bu satırlar için `beklenen` bildirmedi — birimin kurulmasının BEKLENİP beklenmediği bilinmiyor. `false` varsaymak gerçek bir eksiği envanter gürültüsü sayardı."
                    >
                      {beklentisizN}
                    </span>
                  </Satir>
                  <Satir etiket="İddiası kanıtsız kalan">
                    <span
                      className={cn("tabular-nums", kanitsizN > 0 && "text-amber-600 dark:text-amber-400")}
                      title="Ucun sınıfı bir sağlık iddiası taşıyor ama dayandığı ölçüm (`Type=oneshot` / `beklenen` / ham `ActiveState`) bu satırda yok — rozet yeşile boyanmadı, `kanıtsız` işaretiyle amber'e düştü."
                    >
                      {kanitsizN}
                    </span>
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Toplam ölçülen RSS">
                    {olculen.length === 0 ? (
                      <Olculemedi neden="Hiçbir birimin bellek kullanımı ölçülemedi" teknik="hiçbir satırda `rss_bayt` ölçülmedi" kisa />
                    ) : (
                      <span className="tabular-nums">{baytMetni(toplamRss)}</span>
                    )}
                  </Satir>
                  <Satir etiket="Paydan elenen satır">
                    <span className="tabular-nums">
                      {elenen}
                      {elenen > 0 ? " (RSS ölçülemedi — 0 sayılmadı)" : ""}
                    </span>
                  </Satir>
                  <Satir etiket="Restart taşıyan birim">
                    <span className="tabular-nums">
                      {satirlar.filter((b) => (b.restart_n ?? 0) > 0).length}
                    </span>
                  </Satir>
                </div>
              </div>

              {/* --- ÜÇÜNCÜ KAT: PANO SÜRECİNİN KENDİSİ ---
                  systemd'nin `meridian.service` satırıyla AYNI ŞEY DEĞİL (o birim compose'u sarar);
                  uç bunu ayrı bir blok olarak veriyor (`api.py::_infra_surec`) ve operatörün ilk sorusu bu:
                  "panoyu servis eden süreç kendisi ne kadar yiyor?" */}
              {surec === undefined ? (
                <Olculemedi neden="Panoyu servis eden sürecin ölçümü bildirilmedi" teknik="/api/infra `surec` bloğunu döndürmedi" />
              ) : (
                <div className="rounded-lg border bg-muted/30 p-3">
                  <div className="mb-1 flex items-center gap-2">
                    <span className="font-medium text-sm">Bu API süreci</span>
                    <Badge variant="outline" className="text-[10px]" title="systemd biriminden AYRI ölçüm">
                      systemd birimi DEĞİL
                    </Badge>
                  </div>
                  <div className="grid gap-x-6 sm:grid-cols-2">
                    <div>
                      <Satir etiket="PID">
                        <Deger deger={surec.pid} neden="Sürecin numarası bildirilmedi" teknik="`surec.pid` gelmedi" />
                      </Satir>
                      <Satir etiket="Çalışma süresi">
                        {sureMetni(surec.uptime_s) ?? <Olculemedi neden="Sürecin çalışma süresi bildirilmedi" teknik="`surec.uptime_s` gelmedi" kisa />}
                      </Satir>
                    </div>
                    <div>
                      <Satir etiket="CPU">
                        {surec.cpu_yuzde === null || surec.cpu_yuzde === undefined ? (
                          <Olculemedi
                            neden="İşlemci kullanımı ilk ölçümde hesaplanamaz"
                            teknik={surec.cpu_yuzde_neden ?? "CPU bir DELTA'dır — ilk örnekte ölçülemez"}
                            kisa
                          />
                        ) : (
                          <span className="tabular-nums">{surec.cpu_yuzde.toFixed(1)}%</span>
                        )}
                      </Satir>
                      <Satir etiket="RSS">
                        {typeof surec.rss_bayt === "number" ? (
                          <span className="tabular-nums">{baytMetni(surec.rss_bayt)}</span>
                        ) : (
                          <Olculemedi
                            neden="Sürecin bellek kullanımı ölçülemedi"
                            teknik={surec.rss_bayt_neden ?? "`surec.rss_bayt` gelmedi"}
                            kisa
                          />
                        )}
                      </Satir>
                    </div>
                  </div>
                </div>
              )}

              {/* --- YIĞILMIŞ ÇUBUK: BELLEK PAYI --- */}
              {olculen.length > 0 ? (
                <>
                  <ChartContainer config={yapilandirma} className="aspect-auto h-16 w-full">
                    <BarChart data={[cubuk]} layout="vertical" margin={{ left: 0, right: 0, top: 4, bottom: 0 }}>
                      <XAxis type="number" hide />
                      <YAxis type="category" dataKey="ad" hide />
                      <ChartTooltip
                        cursor={false}
                        content={
                          <ChartTooltipContent
                            hideLabel
                            formatter={(deger, ad) => {
                              const b = baytMetni(typeof deger === "number" ? deger : null);
                              const etiket = yapilandirma[String(ad)]?.label ?? String(ad);
                              return (
                                <span className="flex w-full justify-between gap-4">
                                  <span className="text-muted-foreground">{etiket}</span>
                                  <span className="font-mono tabular-nums">{b ?? "ölçülemedi"}</span>
                                </span>
                              );
                            }}
                          />
                        }
                      />
                      {ust.map((b, i) => (
                        <Bar isAnimationActive={false}
                          key={b.ad ?? `b${i}`}
                          dataKey={`b${i}`}
                          stackId="rss"
                          barSize={26}
                          fill={`var(--color-b${i})`}
                          radius={i === 0 ? [4, 0, 0, 4] : kalan.length === 0 && i === ust.length - 1 ? [0, 4, 4, 0] : 0}
                        />
                      ))}
                      {kalan.length > 0 ? (
                        <Bar isAnimationActive={false} dataKey="diger" stackId="rss" barSize={26} fill="var(--color-diger)" radius={[0, 4, 4, 0]} />
                      ) : null}
                    </BarChart>
                  </ChartContainer>
                  <div className="flex flex-wrap gap-x-4 gap-y-1">
                    {/* KÜNYE RECHARTS'IN LEGEND'İ DEĞİL: onunki tek satırdır ve birim adları uzun
                        (`meridian-tick-watchdog.service`) — altı dilim yan yana taşardı. */}
                    {Object.entries(yapilandirma).map(([anahtar, k]) => (
                      <span key={anahtar} className="flex items-center gap-1.5 text-xs">
                        {/* RENK DOĞRUDAN YAPILANDIRMADAN: `--color-<anahtar>` değişkenlerini
                            `ChartStyle` YALNIZ `[data-chart=…]` kapsayıcısının İÇİNE yazıyor
                            (chart.tsx). Bu şerit kapsayıcının DIŞINDA, orada o değişken çözülmez
                            ve şeritteki her kare şeffaf kalırdı. */}
                        <span
                          className="size-2 shrink-0 rounded-[2px]"
                          style={{ backgroundColor: k.color ?? "var(--muted-foreground)" }}
                        />
                        <span className="text-muted-foreground">{k.label}</span>
                      </span>
                    ))}
                  </div>
                  <p className="text-muted-foreground text-xs">
                    Yığılmış çubuk, ÖLÇÜLEN RSS toplamının ({baytMetni(toplamRss)}) bileşenlere dağılımıdır —
                    makinenin toplam belleğinin değil. En büyük {Math.min(DILIM_TAVANI, ust.length)} bileşen
                    ayrı dilim; kalanlar "diğer"de.
                    {elenen > 0
                      ? ` RSS'i ölçülemeyen ${elenen} satır paya HİÇ girmedi (0 saymak, ölçülmemişi boşta göstermek olurdu).`
                      : ""}
                  </p>
                </>
              ) : (
                <Olculemedi neden="Hiçbir bileşenin bellek kullanımı ölçülemedi — pay çubuğu çizilemez" teknik="hiçbir bileşenin `rss_bayt` değeri ölçülmedi" />
              )}

              {/* --- BİLEŞEN TABLOSU --- */}
              <div className="overflow-x-auto">
                <Table className="min-w-[62rem]">
                  <TableHeader className="bg-muted/50">
                    <TableRow>
                      <TableHead>Birim</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Beklenti · ölçüm · bağ</TableHead>
                      <TableHead className="text-right">CPU</TableHead>
                      <TableHead className="text-right">RSS</TableHead>
                      <TableHead className="text-right">Bellek payı</TableHead>
                      <TableHead className="text-right">Çalışma süresi</TableHead>
                      <TableHead className="text-right">Restart</TableHead>
                      <TableHead>Tanım</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {satirlar.map((b, i) => {
                      const pay =
                        typeof b.rss_bayt === "number" && toplamRss > 0 ? (b.rss_bayt / toplamRss) * 100 : null;
                      return (
                        <TableRow key={b.ad ?? `bilesen-${i}`}>
                          <TableCell className="font-medium font-mono text-xs">
                            <span className="flex items-center gap-1.5">
                              {b.ad ?? <Olculemedi neden="Birimin adı bildirilmedi" teknik="satır `ad` taşımıyor" kisa />}
                              {b.sablon ? (
                                <Badge
                                  variant="outline"
                                  className="text-[10px]"
                                  title="Şablon birim (`@.service`) — düz adla sorgu sahte `inactive` verir; durumu uydurulmaz."
                                >
                                  şablon
                                </Badge>
                              ) : null}
                              {b.tur === "timer" ? (
                                <Badge variant="outline" className="text-[10px]" title="systemd timer birimi">
                                  timer
                                </Badge>
                              ) : null}
                            </span>
                          </TableCell>
                          <TableCell>{durumRozeti(b)}</TableCell>
                          <TableCell className="max-w-[14rem]">
                            <BeklentiHucresi b={b} />
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {b.cpu_yuzde === null || b.cpu_yuzde === undefined ? (
                              <Olculemedi
                                neden="İşlemci kullanımı tek örnekle hesaplanamaz"
                                teknik={b.cpu_yuzde_neden ?? "CPU bir DELTA'dır — tek örnekle ölçülemez"}
                                kisa
                              />
                            ) : (
                              `${b.cpu_yuzde.toFixed(1)}%`
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {typeof b.rss_bayt === "number" ? (
                              baytMetni(b.rss_bayt)
                            ) : (
                              <Olculemedi
                                neden="Bellek kullanımı ölçülemedi"
                                teknik={b.rss_bayt_neden ?? "`rss_bayt` ölçülemedi (systemd sentineli olabilir)"}
                                kisa
                              />
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {pay === null ? (
                              <span className="text-muted-foreground text-xs">—</span>
                            ) : (
                              <span className="flex items-center justify-end gap-2">
                                <span className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-muted-foreground/20 sm:block">
                                  <span
                                    className="block h-full rounded-full bg-primary"
                                    style={{ width: `${Math.min(100, pay)}%` }}
                                  />
                                </span>
                                {pay.toFixed(1)}%
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums text-xs">
                            {sureMetni(b.uptime_s) ?? (
                              <Olculemedi neden="Çalışma süresi bildirilmedi" teknik={b.uptime_s_neden ?? "`uptime_s` gelmedi"} kisa />
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {b.restart_n === null || b.restart_n === undefined ? (
                              <Olculemedi neden="Yeniden başlatma sayısı bildirilmedi" teknik={b.restart_n_neden ?? "`restart_n` gelmedi"} kisa />
                            ) : (
                              <span
                                className={cn(
                                  b.restart_n > 0 && "font-medium text-amber-600 dark:text-amber-400",
                                )}
                              >
                                <Deger deger={b.restart_n} neden="Yeniden başlatma sayacı bildirilmedi" teknik="restart sayacı gelmedi" />
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="max-w-[20rem] truncate text-muted-foreground text-xs">
                            {b.aciklama ?? b.dosya ?? (
                              <Olculemedi neden="Birimin ne iş yaptığı bildirilmedi" teknik="birim tanımı/dosya adı gelmedi" kisa />
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>

              <p className="text-muted-foreground text-xs">
                Birim adları `{g.bilesen_kaynagi?.dizin ?? "deploy/"}` altındaki GERÇEK
                `.service`/`.timer` dosyalarından geliyor ({g.bilesen_kaynagi?.birim_n ?? satirlar.length} dosya) —
                uç uydurulmuş bir ad bildirirse çivi (`test_birim_adlari_diskteki_gercek_dosyalardan_gelir`)
                kırmızıya döner. `systemctl` yolu:{" "}
                {g.bilesen_kaynagi?.systemctl_yolu ?? (
                  <Olculemedi
                    neden="Servis yönetim aracının yeri bildirilmedi"
                    teknik={g.bilesen_kaynagi?.systemctl_yolu_neden ?? "yol beyanı gelmedi"}
                    kisa
                  />
                )}
                . Bu tablo hiçbir birimi başlatmaz/durdurmaz; salt okunurdur.
              </p>
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
