/* ============================================================================
   ROADMAP GÖVDE OKUYUCUSU — `GET /api/roadmap` (ÖLÇÜLDÜ, tahmin edilmedi)
   ----------------------------------------------------------------------------
   Alan adları `meridian/api.py::api_roadmap` + `_roadmap_ayristir` OKUNARAK
   alındı (api.py:6654-6798). Şekil bir DÜZ LİSTE DEĞİL, BÖLÜM AĞACIdır:

     { ok, yol, bayt, satir_n, mtime, baslik,
       bolumler: [ {no, baslik, ham_baslik, seviye, satir,
                    maddeler: [...], alt_bolumler: [...],
                    madde_n, madde_n_toplam} ] | null,
       sayim: {bolum_n, alt_bolum_n, madde_n, durum:{kapali,bloke,askida,acik,belirsiz}},
       ham_tavan: number|null, suzgec: {...} }

   ve madde:
     {satir, girinti, baslik, ham, ham_kirpildi, ham_uzunluk,
      durum, durum_kanit, ustu_cizili}

   ÜÇ TUZAK, ÜÇÜ DE BURADA KARŞILANIYOR:

   1) `bolumler: null` "yol haritası boş" DEĞİLDİR — ucun kendi şerhi: dosya
      okunamadığında 404 yerine 200 + `hata` + `yol` dönüyor ki operatör HANGİ
      yolun okunamadığını görebilsin. Boş liste ile null'u aynı çizmek o tasarımı
      çöpe atardı.

   2) `durum: "belirsiz"` "açık" DEĞİLDİR. Ucun başlığındaki cümle: 419 maddenin
      çoğu düzyazı ve işaret taşımıyor; onları "açık" saymak tahtanın üstüne
      ölçülmemiş bir sayı yazmak olurdu. Pano bu beş kovayı OLDUĞU GİBİ taşır,
      birleştirmez.

   3) `ham_kirpildi` — madde gövdesi varsayılanda 400 karakterde kesiliyor
      (`_ROADMAP_HAM_TAVAN`). Kırpılmış metni tam sanmamak için kart bunu
      damgalıyor.

   DÜZLEŞTİRME: kolonlar KÖK bölümlerdir (§0…§8) ama maddelerin çoğu alt
   başlıklarda (§3 → WP1…WP11). Alt bölümleri kolon yapmak tahtaya kırk kolon
   koyardı; maddeleri kök kolona düzleştirip kartta alt başlığı YAZMAK hem sayıyı
   hem yeri koruyor.
   ============================================================================ */
import { dizi, mantik, metin, nesne, sayi } from "./oku";

export interface RoadmapMaddesi {
  /** React anahtarı — `satir` benzersizdir (dosyadaki satır numarası). */
  readonly anahtar: string;
  readonly satir: number | null;
  readonly baslik: string | null;
  readonly ham: string | null;
  readonly hamKirpildi: boolean;
  readonly hamUzunluk: number | null;
  readonly durum: string | null;
  readonly durumKanit: string | null;
  readonly ustuCizili: boolean;
  /** Maddenin geldiği ALT başlık zinciri ("WP3 — Öğrenme Döngüsü"); kök bölümün
   *  kendi maddesiyse `null`. Düzleştirmede kaybolmasın diye taşınıyor. */
  readonly altBolum: string | null;
}

export interface RoadmapBolumu {
  readonly anahtar: string;
  readonly no: string | null;
  readonly baslik: string | null;
  readonly hamBaslik: string | null;
  /** Alt bölümler dahil DÜZLEŞTİRİLMİŞ madde listesi. */
  readonly maddeler: readonly RoadmapMaddesi[];
  /** Ucun kendi beyanı (`madde_n_toplam`). Bizim saydığımızla karşılaştırılır. */
  readonly beyanEdilenN: number | null;
  readonly altBolumN: number;
}

export interface RoadmapSayimi {
  readonly bolumN: number | null;
  readonly altBolumN: number | null;
  readonly maddeN: number | null;
  readonly durum: ReadonlyMap<string, number>;
}

export interface RoadmapKunyesi {
  readonly yol: string | null;
  readonly bayt: number | null;
  readonly satirN: number | null;
  readonly mtime: string | null;
  readonly belgeBasligi: string | null;
  readonly hamTavan: number | null;
}

export type RoadmapOkumasi =
  | { readonly tur: "hata"; readonly hata: string; readonly yol: string | null }
  | { readonly tur: "tanimadi"; readonly ustAnahtarlar: readonly string[]; readonly ornek: string }
  | {
      readonly tur: "tahta";
      readonly bolumler: readonly RoadmapBolumu[];
      readonly sayim: RoadmapSayimi;
      readonly kunye: RoadmapKunyesi;
      /** Nesne olmadığı için okunamayan bölüm/madde satırı sayısı. */
      readonly okunamayan: number;
    };

/* Durum kovaları ucun sözlüğünden AYNEN alındı (`_roadmap_madde_durumu`).
   Sıra "kapanmışa doğru" değil, KARAR AĞIRLIĞINA göre: önce senden iş isteyenler. */
export const DURUM_SIRASI = ["bloke", "acik", "askida", "belirsiz", "kapali"] as const;

export const DURUM_ETIKETI: Record<string, string> = {
  bloke: "bloke",
  acik: "açık",
  askida: "askıda",
  belirsiz: "belirsiz",
  kapali: "kapalı",
};

function maddeOku(x: unknown, altBolum: string | null): RoadmapMaddesi | null {
  const n = nesne(x);
  if (!n) return null;
  const satir = sayi(n["satir"]);
  return {
    anahtar: satir === null ? `madde-${Math.random().toString(36).slice(2)}` : `s${satir}`,
    satir,
    baslik: metin(n["baslik"]),
    ham: metin(n["ham"]),
    hamKirpildi: mantik(n["ham_kirpildi"]) === true,
    hamUzunluk: sayi(n["ham_uzunluk"]),
    durum: metin(n["durum"]),
    durumKanit: metin(n["durum_kanit"]),
    ustuCizili: mantik(n["ustu_cizili"]) === true,
    altBolum,
  };
}

/** Bir bölümü ve TÜM alt bölümlerini gezip maddeleri düzleştirir.
 *  `yol` alt başlık zinciridir; kök bölümün kendi maddelerinde boş kalır. */
function maddeleriTopla(
  b: Record<string, unknown>,
  yol: readonly string[],
  cikti: RoadmapMaddesi[],
): number {
  let okunamayan = 0;
  const etiket = yol.length === 0 ? null : yol.join(" › ");
  for (const m of dizi(b["maddeler"]) ?? []) {
    const okunan = maddeOku(m, etiket);
    if (okunan) cikti.push(okunan);
    else okunamayan += 1;
  }
  for (const alt of dizi(b["alt_bolumler"]) ?? []) {
    const an = nesne(alt);
    if (!an) {
      okunamayan += 1;
      continue;
    }
    const ad = metin(an["baslik"]) ?? metin(an["ham_baslik"]);
    okunamayan += maddeleriTopla(an, ad === null ? yol : [...yol, ad], cikti);
  }
  return okunamayan;
}

function altBolumSay(b: Record<string, unknown>): number {
  let n = 0;
  for (const alt of dizi(b["alt_bolumler"]) ?? []) {
    const an = nesne(alt);
    if (!an) continue;
    n += 1 + altBolumSay(an);
  }
  return n;
}

export function roadmapOku(ham: unknown): RoadmapOkumasi {
  const g = nesne(ham);
  if (!g) {
    return { tur: "tanimadi", ustAnahtarlar: [], ornek: JSON.stringify(ham).slice(0, 600) };
  }

  // HATA YOLU: uç dosyayı okuyamadığında 200 + {ok:false, bolumler:null, hata, yol} döner.
  // `bolumler`in boş liste DEĞİL null olması bilinçli (api.py:6760) — o ayrımı koruyoruz.
  const hata = metin(g["hata"]);
  if (hata !== null || mantik(g["ok"]) === false) {
    return {
      tur: "hata",
      hata: hata ?? "uç `ok:false` döndü ama `hata` metni yazmadı — nedeni okuyamıyoruz",
      yol: metin(g["yol"]),
    };
  }

  const hamBolumler = dizi(g["bolumler"]);
  if (hamBolumler === null) {
    // `bolumler` var ama dizi değil (ya da hiç yok). Bu bir ŞEKİL sorunudur, boş tahta değil.
    return {
      tur: "tanimadi",
      ustAnahtarlar: Object.keys(g),
      ornek: JSON.stringify(g).slice(0, 600),
    };
  }

  let okunamayan = 0;
  const bolumler: RoadmapBolumu[] = [];
  hamBolumler.forEach((b, i) => {
    const bn = nesne(b);
    if (!bn) {
      okunamayan += 1;
      return;
    }
    const maddeler: RoadmapMaddesi[] = [];
    okunamayan += maddeleriTopla(bn, [], maddeler);
    const no = metin(bn["no"]);
    bolumler.push({
      anahtar: no ?? metin(bn["ham_baslik"]) ?? `bolum-${i}`,
      no,
      baslik: metin(bn["baslik"]),
      hamBaslik: metin(bn["ham_baslik"]),
      maddeler,
      beyanEdilenN: sayi(bn["madde_n_toplam"]),
      altBolumN: altBolumSay(bn),
    });
  });

  const sayimN = nesne(g["sayim"]);
  const durumN = nesne(sayimN?.["durum"]);
  const durum = new Map<string, number>();
  if (durumN) {
    for (const [k, v] of Object.entries(durumN)) {
      const n = sayi(v);
      if (n !== null) durum.set(k, n);
    }
  }

  return {
    tur: "tahta",
    bolumler,
    sayim: {
      bolumN: sayi(sayimN?.["bolum_n"]),
      altBolumN: sayi(sayimN?.["alt_bolum_n"]),
      maddeN: sayi(sayimN?.["madde_n"]),
      durum,
    },
    kunye: {
      yol: metin(g["yol"]),
      bayt: sayi(g["bayt"]),
      satirN: sayi(g["satir_n"]),
      mtime: metin(g["mtime"]),
      belgeBasligi: metin(g["baslik"]),
      hamTavan: sayi(g["ham_tavan"]),
    },
    okunamayan,
  };
}

/** Kolon başlığı: `§3 — AKTİF WP'ler`. `no` yoksa yalnız başlık — uydurulmuş bir
 *  numara TAKILMAZ (önsöz bölümünün `no`su gerçekten null'dır). */
export function bolumBasligi(b: RoadmapBolumu): string {
  const ad = b.baslik ?? b.hamBaslik ?? "(başlıksız bölüm)";
  return b.no === null ? ad : `${b.no} · ${ad}`;
}
