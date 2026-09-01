/* ============================================================================
   "GECE NE BULDU" KARTININ SAF MODELİ — huninin basamakları ve düşüşleri
   ----------------------------------------------------------------------------
   ÖLÇÜLEN ARIZA (2026-08-31): operatör kartı "hiç tarama olmadı" diye okudu;
   gerçek "döngü koştu, 0 aday" idi. Üç ayrı kusur bir araya gelmişti:

     (a) İLK BASAMAK YANLIŞ ETİKETLİYDİ. "Taranan aday" yazıyordu ama bağlandığı
         alan eleme SONRASI sayıydı (`candidates`). Huninin AĞZI hiç çizilmiyordu.
     (b) DİPNOT TEK CÜMLEYDİ. Aday 0 iken "ilk basamak yazılı değil" diyordu —
         oysa yazılıydı (0). Gerçek sebep "payda 0, oran hesaplanamaz"dı. İki
         AYRI olgu tek metne indirgenince "ölçemedik" ile "ölçtük, sıfır" aynı
         göründü ve okuyucu birinciyi anladı.
     (c) ELEME ÖNCESİ EVREN HİÇ KAYDEDİLMİYORDU (motor tarafı; `loop.daily_cycle`
         artık `taranan` yazıyor).

   NEDEN SAF DOSYA: bu türetme bir çizim değil bir HÜKÜMdür (hangi sayı payda,
   hangi cümle hangi olguyu anlatır) ve `KararZinciri.tsx` içinde yaşadığı sürece
   yalnız kaynak metninden ölçülebilirdi. Burada React yok: `tests/civiler/
   gece_hunisi_civileri.mjs` bu fonksiyonları node'da ÇAĞIRIYOR.

   GERİYE UYUM BEDELİ ÖLÇÜLDÜ: `taranan` alanı bu turdan ESKİ kayıtlarda YOK. O
   kayıtlarda huni üç basamağa düşer ve payda yine eleme-sonrası adaydır — yani
   eski davranış korunur, YALNIZ etiket dürüstleşir. Bunu sessizce yapmıyoruz:
   payda beyanı hangi dünyada olduğumuzu ekranda söylüyor.
   ============================================================================ */
import type { HuniBasamagi, HuniDususu } from "./huni_cekirdek";
import { huniTabani, tabanNedeni } from "./huni_cekirdek";
import { mantik, metin, nesne, sayi } from "./oku";

/* --------------------------------------------------------------------------
   SON DÖNGÜ — huninin kaynağı. `var:false` ise NEDENİ ekrana yazılır; huniyi
   sıfırlarla çizmek "gece hiçbir şey bulunmadı" yalanı olurdu (ucun kendi
   cümlesi: "'Sıfır aday' DEĞİL: ölçülemedi").
   -------------------------------------------------------------------------- */
export interface SonDongu {
  readonly var: boolean;
  readonly neden: string | null;
  readonly tarih: string | null;
  readonly yasSaat: number | null;
  /** ELEME ÖNCESİ evren: süzgece giren sembol sayısı. null → ölçülemedi. */
  readonly taranan: number | null;
  /** `taranan === null` iken motorun BEYAN ETTİĞİ sebep. İkisi de null ise alan
   *  kayıtta HİÇ YOK demektir (eski kayıt) — bu üçüncü hâl ve ayrı okunur. */
  readonly tarananNeden: string | null;
  /** ELEME SONRASI aday. Payda DEĞİLDİR; `taranan` varken ikinci basamaktır. */
  readonly aday: number | null;
  readonly plan: number | null;
  readonly silahli: number | null;
  readonly veriTamam: boolean | null;
  readonly durduruldu: boolean | null;
  readonly rejim: string | null;
}

export function sonDonguOku(ham: unknown): SonDongu | null {
  const n = nesne(ham);
  if (!n) return null;
  return {
    var: mantik(n["var"]) === true,
    neden: metin(n["neden"]),
    tarih: metin(n["date"]),
    yasSaat: sayi(n["yas_saat"]),
    taranan: sayi(n["taranan"]),
    tarananNeden: metin(n["taranan_neden"]),
    aday: sayi(n["candidates"]),
    plan: sayi(n["plans"]),
    silahli: sayi(n["armed"]),
    veriTamam: mantik(n["data_ok"]),
    durduruldu: mantik(n["halted"]),
    rejim: metin(n["regime"]),
  };
}

/* --------------------------------------------------------------------------
   BASAMAK ADLARI — TEK YERDE. "Taranan aday" adı bilerek ÖLDÜ: iki farklı kümeyi
   (evren, elemeyi geçen) tek ada bağlamak bu turun düzelttiği kusurdu.
   -------------------------------------------------------------------------- */
export const AD_TARANAN = "Taranan";
export const AD_ADAY = "Elemeyi geçen aday";
export const AD_PLAN = "Kurulan plan";
export const AD_HAZIR = "İşleme hazırlanan";

/** Basamak + o basamağa GİRERKEN eriyen kümenin adı (düşüş satırının dili). */
interface Adim {
  readonly basamak: HuniBasamagi;
  readonly eriyenAd: string;
}

export interface GeceModeli {
  readonly basamaklar: readonly HuniBasamagi[];
  readonly dususler: readonly HuniDususu[];
  /** Kaç basamak GERÇEKTEN sayı taşıyor — 0 ise huni hiç çizilmez. */
  readonly olculen: number;
  /** Şeridin altında GÖRÜNEN payda cümlesi; hangi dünyada olduğumuzu söyler. */
  readonly paydaBeyani: string;
}

export function geceModeli(sd: SonDongu): GeceModeli {
  const adimlar: Adim[] = [];

  // (1) HUNİNİN AĞZI — üç hâl, üçü de ayrı:
  //   · sayı var          → basamak çizilir, payda BUDUR
  //   · sayı yok + neden  → basamak ÇİZİLİR ama "ölçülemedi" olarak (neden motorun)
  //   · ikisi de yok      → alan kayıtta HİÇ YOK (eski kayıt): basamak EKLENMEZ,
  //     yoksa eski kayıtların bütün oranları paydasız kalırdı — kazancı ölçüp
  //     bedeli ölçmemek olurdu (bedel yasası). Beyan aşağıda bunu SÖYLER.
  const evrenVar = sd.taranan !== null || sd.tarananNeden !== null;
  if (sd.taranan !== null) {
    adimlar.push({ basamak: { ad: AD_TARANAN, n: sd.taranan }, eriyenAd: "" });
  } else if (sd.tarananNeden !== null) {
    adimlar.push({ basamak: { ad: AD_TARANAN, n: null, neden: sd.tarananNeden }, eriyenAd: "" });
  }

  adimlar.push({
    basamak: sd.aday === null
      ? { ad: AD_ADAY, n: null, neden: "döngü kaydında elemeyi geçen aday sayısı yok" }
      : { ad: AD_ADAY, n: sd.aday },
    eriyenAd: "sembol elemeyi geçemedi",
  });
  adimlar.push({
    basamak: sd.plan === null
      ? { ad: AD_PLAN, n: null, neden: "döngü kaydında kurulan plan sayısı yok" }
      : { ad: AD_PLAN, n: sd.plan },
    eriyenAd: "aday plan olmadı",
  });
  adimlar.push({
    basamak: sd.silahli === null
      ? { ad: AD_HAZIR, n: null, neden: "döngü kaydında işleme hazırlanan sayısı yok" }
      : { ad: AD_HAZIR, n: sd.silahli },
    eriyenAd: "plan işleme hazırlanmadı",
  });

  const basamaklar = adimlar.map((a) => a.basamak);
  // TEK KAYNAK: taban ve nedeni çekirdekten okunuyor; `Huni` şeridi de aynı
  // kuralla çiziyor. İki kopya bir gün ayrışırdı (yüzdeler ile şerit).
  const taban = huniTabani(basamaklar);
  const paydaKusuru = tabanNedeni(basamaklar);

  const dususler: HuniDususu[] = [];
  for (let i = 1; i < adimlar.length; i += 1) {
    const onceki = adimlar[i - 1];
    const su = adimlar[i];
    if (onceki === undefined || su === undefined) continue;
    const ok = `${onceki.basamak.ad} → ${su.basamak.ad}`;
    const once = onceki.basamak.n;
    const sonra = su.basamak.n;
    if (once === null || sonra === null) {
      const eksik = once === null ? onceki.basamak : su.basamak;
      dususler.push({
        ok,
        metin: `${eksik.ad} ölçülemedi — eriyen küme hesaplanamadı`,
        oran: null,
        // KUSUR (b)'NİN TAM YERİ: burada "payda yok" DEMİYORUZ. Eksik olan
        // basamağın kendisi; payda ayrı bir soru ve ayrı cümlesi var.
        neden: `${eksik.ad} bu kayıtta ölçülemedi — sıfır DEĞİL`,
      });
      continue;
    }
    const eriyen = once - sonra;
    if (eriyen < 0) {
      // MONOTONLUK İHLALİ: sonraki basamak öncekini aşıyor, yani iki küme iç içe
      // DEĞİL. Negatif bir "eriyen oranı" basmak (`−−%5`) hem çirkin hem yanlış;
      // `Huni` bu hâli zaten ayrı bir uyarıyla adıyla yazıyor.
      dususler.push({
        ok,
        metin: `${-eriyen} fazla · sonraki basamak öncekini aşıyor, bu iki küme iç içe değil`,
        oran: null,
        neden: "eriyen küme yok — sonraki basamak öncekinden büyük, oran huni gibi okunamaz",
      });
      continue;
    }
    dususler.push({
      ok,
      metin: eriyen > 0
        ? `${eriyen} ${su.eriyenAd} · hangi kapıda düştüğü bu kayıtta YAZMIYOR — kırılım aşağıdaki "Kapı aşamaları" tablosunda`
        // SIFIRIN İKİ ANLAMI AYRILIR (aynı ders `bugun/HukumDagilimi` kartında da
        // alındı): "eriyecek bir şey yoktu" ile "hepsi geçti" aynı sayıyı üretir.
        : once === 0
          ? `${onceki.basamak.ad} basamağı boş — eriyecek bir şey yoktu`
          : `eriyen yok · ${once} ${onceki.basamak.ad.toLocaleLowerCase("tr")} olduğu gibi geçti`,
      oran: taban !== null ? eriyen / taban : null,
      // Payda kusuru ÜÇ HÂLDEN BİRİ olarak gelir (çekirdek ayırıyor): ilk basamak
      // hiç yok · ölçülemedi · ÖLÇÜLDÜ VE SIFIR. Üçünü tek metne indirmek, bu
      // turun düzelttiği yanlış okumanın ta kendisiydi.
      neden: paydaKusuru ?? undefined,
    });
  }

  const paydaBeyani = evrenVar
    ? "Payda: bu gecenin TARANAN evreni — yani süzgece giren sembol sayısı. Kırpılmış sinyal "
      + "defterinden sayılmadı; o uç son 120 satırla kesik ve huninin ağzını olduğundan dar gösterirdi."
    : "Payda: bu döngü kaydının ELEMEYİ GEÇEN ADAY sayısı. Taranan evren bu kayıtta yok (bu ölçüm "
      + "eklenmeden önce yazılmış bir gece), yani huninin AĞZI gösterilemiyor — oranlar elemeden "
      + "SONRAKİ kümeye göredir ve elemenin kendisi bu şeritte görünmez.";

  return {
    basamaklar,
    dususler,
    olculen: basamaklar.filter((b) => b.n !== null).length,
    paydaBeyani,
  };
}
