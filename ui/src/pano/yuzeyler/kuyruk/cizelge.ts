/* ============================================================================
   ÇİZELGENİN NORMALLEŞTİRİLMESİ — damga + bekçi hükmü, tek satırda
   ----------------------------------------------------------------------------
   İKİ AYRI ÖLÇÜM AYNI MEKANİZMAYI ANLATIYOR ve ikisi de tek başına eksik:

     · `/api/diagnostics.cizelge.damgalar` → "bu adım EN SON NE ZAMAN koştu"
       (`mechanism_beats.json`, epoch → ISO; damgası olmayan adımın anahtarı
       dosyada HİÇ YOKTUR — saat üretilmez, api.py:4003 şerhi)
     · `/api/diagnostics.watchdog`        → "bu adım penceresini AŞTI MI"
       (`watchdog.report`, üç kova: `stale` · `never` · `askida`)

   Damga tek başına "geç mi kaldı"yı söyleyemez (pencereyi bilmez); bekçi tek
   başına "ne zaman koştu"yu söyleyemez (yalnız aşımı raporlar). Birleştirmek bu
   yüzden bir süsleme değil, sorunun cevabının ta kendisi.

   ── EN İNCE NOKTA: "PENCERESİNDE" BİR HÜKÜMDÜR, VARSAYIM DEĞİL ──────────────
   Bekçi YALNIZ `EXPECTED` sözlüğündeki mekanizmaları izliyor (watchdog.py:41).
   Damgası olan ama `EXPECTED`te olmayan bir adım hiçbir kovada görünmez — onu
   "penceresinde" saymak, HİÇ İZLENMEYEN bir mekanizmayı yeşile boyamak olurdu.
   `EXPECTED`in adları uçtan gelmiyor; ama SAYISI geliyor (`n_ok` + kova
   uzunlukları). Bu yüzden hüküm bir ÖZDEŞLİK SINAMASINDAN geçer:

       damgalı \ (stale ∪ never ∪ askida)  sayısı  ==  n_ok  ?

   Eşitse, kovalarda görünmeyen her damgalı adım bekçinin "penceresinde" saydığı
   adımlardan biridir — başka türlü olamaz. Eşit DEĞİLSE hüküm verilmez: satır
   "ölçülemedi" der ve sayı tutarsızlığını NEDEN olarak taşır.

   ── "SIRADA NE VAR" KISMEN ÖLÇÜLEBİLİR ──────────────────────────────────────
   Bir adımın bir sonraki beklenen koşusu = son damga + beklenen pencere. Pencere
   (`expected_h`) uçtan YALNIZ geciken ve askıda satırlarda geliyor; penceresinde
   koşan adımlar için `EXPECTED` değeri uca HİÇ açılmıyor. Pencereyi bu dosyaya
   kopyalamak (20 satırlık bir sözlük) ikinci bir doğruluk kaynağı üretirdi ve
   `watchdog.py` değiştiği gün pano sessizce yalan söylerdi. Kopyalanmadı: sıradaki
   koşu o satırlarda "ölçülemedi + neden" olarak durur ve açık kalem olarak
   raporlanır.
   ============================================================================ */
import type { BekciBlogu, BekciGecikmesi, CizelgeBlogu, CizelgeKosusu } from "./tipler";
import { zamanMs } from "./parcalar";

export type AdimHukmu = "penceresinde" | "gecikti" | "hic_kosmadi" | "askida" | "olculemedi";

export const HUKUM_ETIKET: Record<AdimHukmu, string> = {
  penceresinde: "penceresinde",
  gecikti: "GECİKTİ",
  hic_kosmadi: "hiç koşmadı",
  askida: "askıda",
  olculemedi: "ölçülemedi",
};

export interface Adim {
  readonly ad: string;
  /** `mechanism_beats.json` damgası (ISO). `null` = bu adım hiç damgalanmamış. */
  readonly sonKosuIso: string | null;
  readonly sonKosuNeden: string;
  /** Damgadan hesaplanan yaş (saniye). Damga yoksa `null`. */
  readonly yasSaniye: number | null;
  /** Bekçinin KENDİ ölçtüğü boşluk (saat) — yalnız geciken/askıda satırlarda VAR. */
  readonly gapSaat: number | null;
  /** Beklenen azami sessizlik (saat) — yalnız geciken/askıda satırlarda VAR. */
  readonly pencereSaat: number | null;
  readonly pencereNeden: string;
  readonly hukum: AdimHukmu;
  readonly hukumNeden: string;
  /** Askıya alınma gerekçesi (sistemin kendi beyanı) — yalnız `askida` satırlarında. */
  readonly askidaNeden: string | null;
  /** Bir sonraki beklenen koşu (ISO). Pencere bilinmiyorsa `null`. */
  readonly siradakiIso: string | null;
  readonly siradakiNeden: string;
}

export interface CizelgeOzeti {
  readonly adimlar: readonly Adim[];
  /** Bekçi ile damga kümesi ÖZDEŞLİK sınamasını geçti mi (yukarıdaki şerh). */
  readonly hukumGuvenilir: boolean;
  readonly hukumBeyani: string;
  readonly nGecikti: number;
  readonly nHicKosmadi: number;
  readonly nAskida: number;
  readonly nPenceresinde: number;
  readonly nOlculemedi: number;
  /** Uç okunamadıysa dolu; adım listesi o zaman bir ölçüm DEĞİLDİR. */
  readonly neden: string | null;
}

function gecikmeHaritasi(satirlar: readonly BekciGecikmesi[] | undefined): Map<string, BekciGecikmesi> {
  const m = new Map<string, BekciGecikmesi>();
  for (const s of satirlar ?? []) {
    if (s.name) m.set(s.name, s);
  }
  return m;
}

export function cizelgeyiCoz(
  cizelge: CizelgeBlogu | undefined,
  bekci: BekciBlogu | undefined,
  hata: string | null,
  simdi: number,
): CizelgeOzeti {
  if (hata !== null) {
    return {
      adimlar: [],
      hukumGuvenilir: false,
      hukumBeyani: hata,
      nGecikti: 0,
      nHicKosmadi: 0,
      nAskida: 0,
      nPenceresinde: 0,
      nOlculemedi: 0,
      neden: hata,
    };
  }
  if (cizelge === undefined && bekci === undefined) {
    return {
      adimlar: [],
      hukumGuvenilir: false,
      hukumBeyani: "/api/diagnostics `cizelge` ve `watchdog` bloklarını döndürmedi",
      nGecikti: 0,
      nHicKosmadi: 0,
      nAskida: 0,
      nPenceresinde: 0,
      nOlculemedi: 0,
      neden: "/api/diagnostics `cizelge` ve `watchdog` bloklarını döndürmedi — çizelge ölçülemedi",
    };
  }

  const damgalar = cizelge?.damgalar ?? {};
  const stale = gecikmeHaritasi(bekci?.stale);
  const askida = gecikmeHaritasi(bekci?.askida);
  const never = new Set(bekci?.never ?? []);

  // AD KÜMESİ DÖRT KAYNAĞIN BİRLEŞİMİ: damgası olup bekçide görünmeyen adım da,
  // bekçide görünüp damgası olmayan adım da satır hak eder. Birini atlamak, o adımı
  // ekrandan silmek olurdu — ve görünmeyen bir mekanizma durduğunda kimse fark etmez.
  const adlar = new Set<string>([...Object.keys(damgalar), ...stale.keys(), ...askida.keys(), ...never]);

  // ÖZDEŞLİK SINAMASI (dosya başlığındaki şerh): kovalarda görünmeyen damgalı adımların
  // sayısı bekçinin `n_ok`una eşit mi?
  const okAdaylari = [...adlar].filter((a) => !stale.has(a) && !askida.has(a) && !never.has(a));
  const nOk = bekci?.n_ok;
  const hukumGuvenilir = nOk !== undefined && okAdaylari.length === nOk;
  const hukumBeyani =
    nOk === undefined
      ? "bekçi `n_ok` döndürmedi — 'penceresinde' hükmü doğrulanamıyor"
      : hukumGuvenilir
        ? `bekçi ${nOk} adımı penceresinde sayıyor ve kovalarda görünmeyen ${okAdaylari.length} damgalı adım bununla birebir eşleşiyor — hüküm doğrulandı`
        : `bekçi ${nOk} adımı penceresinde sayıyor ama kovalarda görünmeyen damgalı adım sayısı ${okAdaylari.length}. Fark, bekçinin İZLEMEDİĞİ (EXPECTED dışı) damgalı adımlar ya da damgasız izlenen adımlar olabilir — bu satırlara "penceresinde" hükmü VERİLMEDİ.`;

  const adimlar: Adim[] = [];
  for (const ad of [...adlar].sort()) {
    const iso = damgalar[ad] ?? null;
    const ms = zamanMs(iso);
    const yas = ms === null ? null : (simdi - ms) / 1000;

    const gec = stale.get(ad);
    const bek = askida.get(ad);
    const hicKosmadi = never.has(ad);

    let hukum: AdimHukmu;
    let hukumNeden: string;
    if (hicKosmadi) {
      hukum = "hic_kosmadi";
      hukumNeden = "bekçinin `never` kovasında — kurulumdan beri hiç nabız atmadı (en yüksek sesli hâl)";
    } else if (gec) {
      hukum = "gecikti";
      hukumNeden = `bekçinin \`stale\` kovasında — ${gec.gap_h ?? "?"} sa sessiz, pencere ${gec.expected_h ?? "?"} sa`;
    } else if (bek) {
      hukum = "askida";
      hukumNeden =
        "bekçinin `askida` kovasında — pencereyi aştı AMA sistemin kendi beyanıyla beklemeye alınmış (alarm üretmez, OK de sayılmaz)";
    } else if (hukumGuvenilir) {
      hukum = "penceresinde";
      hukumNeden = "hiçbir bekçi kovasında değil ve `n_ok` özdeşlik sınaması tuttu";
    } else {
      hukum = "olculemedi";
      hukumNeden = hukumBeyani;
    }

    const kaynak = gec ?? bek ?? null;
    const pencere = kaynak?.expected_h ?? null;
    const siradakiMs = ms !== null && pencere !== null ? ms + pencere * 3600 * 1000 : null;

    adimlar.push({
      ad,
      sonKosuIso: iso,
      sonKosuNeden: hicKosmadi
        ? "`mechanism_beats.json` bu adım için damga taşımıyor — hiç koşmadı"
        : (cizelge?.damga_neden_yok ?? "bu adımın damgası okunamadı"),
      yasSaniye: yas,
      gapSaat: kaynak?.gap_h ?? null,
      pencereSaat: pencere,
      pencereNeden:
        pencere === null
          ? "beklenen pencere uçtan YALNIZ geciken/askıda satırlarda geliyor (`expected_h`); penceresinde koşan adımın penceresi `watchdog.EXPECTED` içinde ve panoya açılmamış"
          : "bekçinin bu satır için yazdığı `expected_h`",
      hukum,
      hukumNeden,
      askidaNeden: bek?.neden ?? null,
      siradakiIso: siradakiMs === null ? null : new Date(siradakiMs).toISOString(),
      siradakiNeden:
        siradakiMs !== null
          ? "son damga + beklenen pencere (ikisi de uçtan ölçüldü)"
          : ms === null
            ? "son damga yok — sıradaki koşu hesaplanamaz"
            : "beklenen pencere uçtan gelmiyor — sıradaki koşu hesaplanamaz (açık kalem)",
    });
  }

  let nGecikti = 0;
  let nHicKosmadi = 0;
  let nAskida = 0;
  let nPenceresinde = 0;
  let nOlculemedi = 0;
  for (const a of adimlar) {
    if (a.hukum === "gecikti") nGecikti += 1;
    else if (a.hukum === "hic_kosmadi") nHicKosmadi += 1;
    else if (a.hukum === "askida") nAskida += 1;
    else if (a.hukum === "penceresinde") nPenceresinde += 1;
    else nOlculemedi += 1;
  }

  return {
    adimlar,
    hukumGuvenilir,
    hukumBeyani,
    nGecikti,
    nHicKosmadi,
    nAskida,
    nPenceresinde,
    nOlculemedi,
    neden: adimlar.length === 0 ? "ne damga ne bekçi kovası satır döndürdü — çizelge ölçülemedi" : null,
  };
}

/* --- KOŞU SÜRESİ --------------------------------------------------------- */

export interface KosuSatiri {
  readonly kosu: CizelgeKosusu;
  /** `finished - started` (saniye). İkisinden biri okunamazsa `null`. */
  readonly sureSaniye: number | null;
  readonly sureNeden: string;
}

/** Koşu defteri satırlarını süreyle zenginleştirir. Süre TÜRETİLMEZ, İKİ DAMGADAN ÖLÇÜLÜR. */
export function kosulariOlc(kosular: readonly CizelgeKosusu[] | undefined): readonly KosuSatiri[] {
  return (kosular ?? []).map((k) => {
    const b = zamanMs(k.started);
    const s = zamanMs(k.finished);
    if (b === null || s === null) {
      return {
        kosu: k,
        sureSaniye: null,
        sureNeden:
          b === null && s === null
            ? "`started` ve `finished` damgaları okunamadı"
            : b === null
              ? "`started` damgası okunamadı"
              : "`finished` damgası okunamadı — koşu bitmemiş ya da satır yarım yazılmış olabilir",
      };
    }
    return { kosu: k, sureSaniye: (s - b) / 1000, sureNeden: "iki damga arasındaki fark" };
  });
}
