/* ============================================================================
   POZİSYON BİRLEŞTİRME — İKİ DEFTER, TEK SATIR, KAYNAK DAMGALI
   ----------------------------------------------------------------------------
   NEDEN BİRLEŞTİRME GEREKLİ: "açık pozisyon" sorusunun bu sistemde İKİ cevabı
   var ve ikisi de gerçek —
     · KİTAP  (`/api/today.open_positions`): adet, giriş, stop, risk. FİYAT YOK.
     · BROKER (`/api/alpaca.account.positions`): adet, ortalama giriş, SON FİYAT,
       gerçekleşmemiş K/Z. Stop/risk yok.
   Tutarı (piyasa değeri) ölçmek için ikisi de gerekir. Yalnız birine bakan bir
   grafik, diğerinde olup burada olmayan pozisyonu SESSİZCE düşürürdü — ve tam
   olarak o düşen satır mutabakat masasının konusudur (sermaye.py::pozisyon_mutabakati "yön
   kaybolmaz" yasası). Bu yüzden BİRLEŞİM alınır, kesişim değil.

   ÜÇÜNCÜ KAYNAK — FİYAT YEDEĞİ: broker aynası düştüğünde (ya da kitapta olup
   broker'da olmayan bir sembolde) son fiyat `/api/market` satırından okunur.
   O uç EOD KAPANIŞTIR ve canlı fiyat servis ETMEDİĞİNİ kendisi beyan ediyor
   (api.py::api_market). Bu yüzden her satır fiyatının NEREDEN geldiğini taşır; ekranda
   "brokerden gelen 128,40$" ile "dün kapanışından okunan 128,40$" aynı görünmez.

   UYDURMA YASAĞI BURADA ÜÇ YERDE İŞLER:
     · adet YOKSA piyasa değeri null + neden (0 değil).
     · fiyat YOKSA piyasa değeri null + neden (giriş fiyatını "son fiyat" diye
       kullanmak, hiç hareket etmemiş bir pozisyon uydurmak olurdu).
     · K/Z broker'dan geliyorsa "broker", giriş × adet farkından hesaplandıysa
       "türetildi" damgası taşır — ikisi aynı güvende değil (broker maliyet
       bazını bilir, biz kitabın giriş fiyatını biliriz ve ikisi AYRIŞIYOR:
       `pozisyon_mutabakati` yedi sembolde yedi ayrışma ölçtü, sermaye.py::pozisyon_mutabakati).
   ============================================================================ */
import { metin, sayi } from "./olcum";
import type { BrokerPozisyonu, KitapPozisyonu, PiyasaSatiri } from "./tipler";

export type FiyatKaynagi = "broker" | "seans-ici" | "eod" | null;
export type Nerede = "iki" | "yalniz-kitap" | "yalniz-broker";

export interface PozisyonSatiri {
  readonly ticker: string;
  readonly nerede: Nerede;
  readonly kitapAdet: number | null;
  readonly brokerAdet: number | null;
  /** Piyasa değerinin ÇARPANI. Broker adedi varsa o; yoksa kitabınki. */
  readonly adet: number | null;
  readonly adetKaynak: "broker" | "kitap" | null;
  /** İki defter aynı sembolde farklı adet söylüyorsa fark; biri yoksa `null`. */
  readonly adetFarki: number | null;
  readonly giris: number | null;
  readonly girisKaynak: "kitap" | "broker" | null;
  readonly sonFiyat: number | null;
  readonly fiyatKaynak: FiyatKaynagi;
  /** Fiyatın ANI — EOD'da seans tarihi, seans içinde dakikalık barın damgası. */
  readonly fiyatAni: string | null;
  readonly piyasaDegeri: number | null;
  /** `piyasaDegeri === null` iken DOLU: hangi girdinin eksik olduğu. */
  readonly degerNedeni: string | null;
  readonly acikKz: number | null;
  readonly acikKzKaynak: "broker" | "turetildi" | null;
  readonly kzYuzde: number | null;
  readonly kzNedeni: string | null;
  readonly stop: number | null;
  readonly riskUsd: number | null;
  readonly setup: string | null;
  readonly acilis: string | null;
}

export interface BirlesikDefter {
  readonly satirlar: readonly PozisyonSatiri[];
  /** Ölçülen piyasa değerlerinin toplamı; hiçbiri ölçülemediyse `null`. */
  readonly toplamDeger: number | null;
  readonly toplamKz: number | null;
  readonly olculenDeger: number;
  readonly olculenKz: number;
  readonly toplamSatir: number;
  /** ANAHTARSIZ (ticker/symbol okunamayan) satır sayısı. Birleştirilemez ama
   *  YOK SAYILAMAZ: sessizce düşen bir pozisyon, olmayan bir portföy demektir. */
  readonly anahtarsiz: number;
}

function sembol(v: unknown): string | null {
  const s = metin(v);
  return s === null ? null : s.toUpperCase();
}

/** Fiyat yedeğini `/api/market` satırından çıkarır. Seans içi kapanış EOD'a
 *  TERCİH EDİLİR ama ikisi ayrı damgalanır — marketview yalnız SİLAHLI sembollerde
 *  ve yalnız KAPANMIŞ + TAZE dakikalık barda `intraday_close` yazıyor
 *  (marketview modül başlığı şerhi), yani varlığı bir istisnadır, kural değil. */
function piyasaFiyati(r: PiyasaSatiri | undefined): { fiyat: number; kaynak: FiyatKaynagi; an: string | null } | null {
  if (!r) return null;
  const ic = sayi(r.intraday_close);
  if (ic !== null) return { fiyat: ic, kaynak: "seans-ici", an: metin(r.intraday_ts) };
  const c = sayi(r.close);
  if (c !== null) return { fiyat: c, kaynak: "eod", an: metin(r.last_date) };
  return null;
}

export function birlestir(
  kitap: readonly KitapPozisyonu[] | null,
  broker: readonly BrokerPozisyonu[] | null,
  piyasa: readonly PiyasaSatiri[] | null,
  /** Broker tarafının NEDEN okunamadığı — satırın `degerNedeni`ne geçer. */
  brokerNedeni: string | null,
  piyasaNedeni: string | null,
): BirlesikDefter {
  let anahtarsiz = 0;
  const kMap = new Map<string, KitapPozisyonu>();
  for (const p of kitap ?? []) {
    const t = sembol(p.ticker);
    // ANAHTARSIZ SATIR SESSİZCE DÜŞMEZ, ama birleştirilemez de: sembolü olmayan
    // bir satırı broker tarafıyla eşleştirmenin yolu yok. Sayacı dışarı çıkar —
    // kaybı görünür kılan tek şey o sayaç (yüzey onu ekrana yazar).
    if (t === null) anahtarsiz += 1;
    else kMap.set(t, p);
  }
  const bMap = new Map<string, BrokerPozisyonu>();
  for (const p of broker ?? []) {
    const t = sembol(p.symbol);
    if (t === null) anahtarsiz += 1;
    else bMap.set(t, p);
  }
  const pMap = new Map<string, PiyasaSatiri>();
  for (const r of piyasa ?? []) {
    const t = sembol(r.ticker);
    if (t !== null) pMap.set(t, r);
  }

  const tickerlar = [...new Set([...kMap.keys(), ...bMap.keys()])].sort();
  const satirlar: PozisyonSatiri[] = [];

  for (const ticker of tickerlar) {
    const k = kMap.get(ticker);
    const b = bMap.get(ticker);
    const nerede: Nerede = k && b ? "iki" : k ? "yalniz-kitap" : "yalniz-broker";

    const kitapAdet = k ? sayi(k.qty) : null;
    const brokerAdet = b ? sayi(b.qty) : null;
    const adet = brokerAdet ?? kitapAdet;
    const adetKaynak = brokerAdet !== null ? "broker" : kitapAdet !== null ? "kitap" : null;
    const adetFarki = kitapAdet !== null && brokerAdet !== null ? kitapAdet - brokerAdet : null;

    // GİRİŞ FİYATINDA BROKER ÖNCE — VE BU BİR TUTARLILIK KARARI, tercih değil.
    // Kitabın `entry`si planın TETİK fiyatıdır (bizim kararımız); brokerın
    // `avg_entry`i DOLUMUN ortalamasıdır (paranın gerçekte girdiği fiyat).
    // Açık K/Z brokerdan geldiğinde onun tabanı `avg_entry`dir; yüzdeyi kitabın
    // tetiğine bölseydik aynı satırda "+105,00$" ile "%6,13" yan yana durur ve
    // İKİSİ FARKLI TABANDAN konuşurdu (broker tabanıyla %5,83). Aynı satırda iki
    // gerçek olamaz: giriş, K/Z ve yüzde ÜÇÜ DE aynı tabandan okunur. Broker
    // satırı yoksa üçü birden kitabın tabanına düşer — yine tutarlı.
    const kGiris = k ? sayi(k.entry) : null;
    const bGiris = b ? sayi(b.avg_entry) : null;
    const giris = bGiris ?? kGiris;
    const girisKaynak = bGiris !== null ? "broker" : kGiris !== null ? "kitap" : null;

    let sonFiyat: number | null = b ? sayi(b.current) : null;
    let fiyatKaynak: FiyatKaynagi = sonFiyat !== null ? "broker" : null;
    let fiyatAni: string | null = null;
    if (sonFiyat === null) {
      const y = piyasaFiyati(pMap.get(ticker));
      if (y) {
        sonFiyat = y.fiyat;
        fiyatKaynak = y.kaynak;
        fiyatAni = y.an;
      }
    }

    let piyasaDegeri: number | null = null;
    let degerNedeni: string | null = null;
    if (adet === null && sonFiyat === null) {
      degerNedeni = `${ticker}: ne adet ne son fiyat ölçüldü — ${brokerNedeni ?? "broker satırı yok"}; ${piyasaNedeni ?? "piyasa satırı yok"}`;
    } else if (adet === null) {
      degerNedeni = `${ticker}: son fiyat var ama ADET ölçülemedi (kitap ve broker satırlarında qty sayıya çevrilemedi) — tutar 0 DEĞİL, bilinmiyor`;
    } else if (sonFiyat === null) {
      degerNedeni = `${ticker}: adet ${adet} ama SON FİYAT ölçülemedi — ${brokerNedeni ?? "broker current alanı yok"}; ${piyasaNedeni ?? "/api/market satırında ne intraday_close ne close var"}. Giriş fiyatını son fiyat saymak, hiç hareket etmemiş bir pozisyon uydurmak olurdu.`;
    } else {
      piyasaDegeri = adet * sonFiyat;
    }

    // K/Z: broker'ın `unrealized_pl`i BİRİNCİL — maliyet bazını broker bilir.
    // Yoksa (giriş, son fiyat, adet) üçlüsünden TÜRETİLİR ve damgası öyle basılır.
    let acikKz: number | null = b ? sayi(b.upl) : null;
    let acikKzKaynak: "broker" | "turetildi" | null = acikKz !== null ? "broker" : null;
    let kzNedeni: string | null = null;
    if (acikKz === null) {
      if (giris !== null && sonFiyat !== null && adet !== null) {
        acikKz = (sonFiyat - giris) * adet;
        acikKzKaynak = "turetildi";
      } else {
        const eksik = [giris === null ? "giriş" : null, sonFiyat === null ? "son fiyat" : null, adet === null ? "adet" : null]
          .filter((x): x is string => x !== null)
          .join(", ");
        kzNedeni = `${ticker}: broker unrealized_pl alanı yok ve türetme girdisi eksik (${eksik}) — açık K/Z ölçülemedi`;
      }
    }
    const kzYuzde = giris !== null && giris !== 0 && sonFiyat !== null ? ((sonFiyat - giris) / giris) * 100 : null;

    satirlar.push({
      ticker,
      nerede,
      kitapAdet,
      brokerAdet,
      adet,
      adetKaynak,
      adetFarki,
      giris,
      girisKaynak,
      sonFiyat,
      fiyatKaynak,
      fiyatAni,
      piyasaDegeri,
      degerNedeni,
      acikKz,
      acikKzKaynak,
      kzYuzde,
      kzNedeni,
      stop: k ? (sayi(k.trail_stop) ?? sayi(k.stop)) : null,
      riskUsd: k ? sayi(k.risk_dollars) : null,
      setup: k ? metin(k.setup) : null,
      acilis: k ? metin(k.ts_open) : null,
    });
  }

  // TOPLAM BEYANLI: kaç satırın ölçüldüğü toplamın YANINDA durur. "7 pozisyonun
  // 5'i toplandı" ile "7 pozisyon toplandı" aynı sayı olsa bile aynı cümle değil.
  let toplamDeger: number | null = null;
  let olculenDeger = 0;
  for (const s of satirlar) {
    if (s.piyasaDegeri === null) continue;
    toplamDeger = (toplamDeger ?? 0) + s.piyasaDegeri;
    olculenDeger += 1;
  }
  let toplamKz: number | null = null;
  let olculenKz = 0;
  for (const s of satirlar) {
    if (s.acikKz === null) continue;
    toplamKz = (toplamKz ?? 0) + s.acikKz;
    olculenKz += 1;
  }

  return { satirlar, toplamDeger, toplamKz, olculenDeger, olculenKz, toplamSatir: satirlar.length, anahtarsiz };
}
