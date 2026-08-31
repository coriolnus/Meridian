/* ============================================================================
   AJAN YÜZEYİNİN GRAMERİ — saf görünüm mantığı (2026-08-31, mesajlaşma maketi)
   ----------------------------------------------------------------------------
   BU DOSYA VERİ KATMANI DEĞİLDİR. Uçtan gelen şekli okumak `filoOku.ts`in işi ve
   o sözleşme DEĞİŞMEDİ. Burada duran şey GÖRÜNÜM kararlarıdır: hangi muhatap
   seçili, hangi sekme açık, kim "bugün aktif", oturumlar ekranda hangi sırada
   akıyor. Ayrı dosyada durmalarının tek nedeni ÖLÇÜLEBİLİRLİK: hepsi saf
   fonksiyon, yani `node` ile GERÇEKTEN koşulabiliyorlar — çivileri
   `tests/test_ajan_grameri_v350.py` (esbuild + node düzeneği, emsal
   `tests/test_pano_palet_v152.py`). Kaynak metninde kimlik arayan bir çivi,
   ifadeyi bozan ama adı koruyan mutasyonda ISIRMAZ; bu dosyanın var olma sebebi
   tam olarak bu.

   ÜÇ SÖZLEŞME BURADA BEYAN EDİLİR:

   (1) ROTA ESKİ BAĞLARI KIRMAZ. Dört eski derin bağ (`…/chat/sohbet`, `/defter`,
       `/olcum`, `/filo`) yeni gramere EŞLENİR; URL yeniden YAZILMAZ (yazsaydık
       operatörün geri tuşu kendi ürettiğimiz adrese takılırdı). Yeni kanonik
       biçim tek segmentte iki bilgi taşır: `<muhatap>.<sekme>`. Yönlendirici
       yolu yalnız `parca[2]`ye kadar ayrıştırıyor (`pano/rota.tsx::hashiCoz`) —
       dördüncü segment eklemek tüm yüzeylerin yol sözleşmesini değiştirirdi;
       ayraç bu yüzden segment İÇİNDE (`.`) ve dilimler `-` kullanıyor.

   (2) OTURUMLAR EKRANDA ESKİDEN→YENİYE AKAR — ve bu BEYANLI bir görünüm
       terslemesidir. Uç `oturumlar`ı YENİDEN→ESKİYE gönderiyor
       (`filoOku.ts` başlığı) ve o sıra DEĞİŞTİRİLMİYOR; tersleme TEK yerde,
       `oturumlariEskidenYeniye` içinde ve model-geçiş kıyası da yeni sıraya göre
       düzeltildi (önceki = indeksçe BİR ÖNCEKİ, artık bir sonraki değil). Mesaj
       sırası (eskiden→yeniye) uçtan geldiği gibi kalır; hiçbir yerde
       sıralanmaz — bir satırlık `sort` konuşmayı tersten okuturdu.

   (3) "ŞU AN AKTİF" DETERMİNİSTİKTİR: bir ajan, YEREL GÜN olarak bugüne düşen
       bir oturum YA DA teslim damgası taşıyorsa aktiftir. Ölçülemeyen kaynak
       (`oturumlar`/`teslimler` liste değil) ya da zamana YERLEŞTİRİLEMEYEN bir
       damga varsa hüküm "aktif değil" DEĞİL, "ölçülemedi"dir (amber) — çünkü
       okunamayan defterde bugün konuşulmuş olabilir. Sessizlik ancak HER İKİ
       kaynak da okunmuşken ve her damga yerine oturmuşken iddia edilir.

   UYGULANMAYAN MAKET SÜSLERİ (ön ruling, 2026-08-31): okunmamış-sayı rozeti ve
   kadans etiketi ("günlük 22:01") BASILMAZ — ikisinin de arkasında veri yok,
   basmak uydurma olurdu. Başlıktaki "son teslim" damgası ölçülüdür ve
   `sonTeslimTs` ondan türer.
   ============================================================================ */
import type { FiloAjani, FiloMesaji, FiloOturumu, FiloTeslimi } from "./filoOku";

/* ---- MUHATAP VE SEKME SÖZLÜĞÜ -------------------------------------------- */

/** Öneri hattı bir bot değil, bir KANALdır: iki taraf (üreteç ↔ kapı) tek
 *  deftere yazıyor. Dilimi sabittir çünkü kaynağı roster değil hipotez defteri. */
export const KANAL_DILIMI = "oneri-hatti";

/** Hiçbir profile denk düşmeyen teslim olayları — sol listenin hayalet satırı. */
export const SAHIPSIZ_DILIMI = "sahipsiz-teslimler";

export type SekmeAdi = "sohbet" | "teslimler" | "defter" | "olcum";

export const SEKME_ETIKET: Readonly<Record<SekmeAdi, string>> = {
  sohbet: "Sohbet",
  teslimler: "Teslimler",
  defter: "Defter",
  olcum: "Ölçüm",
};

export type MuhatapTuru = "kanal" | "ajan" | "sahipsiz";

/** SEKME TAKIMI MUHATABA GÖRE DEĞİŞİR (maket sözleşmesi): bir bota "Defter"
 *  sekmesi açmak, hipotez defterini o botun defteriymiş gibi gösterirdi — iki
 *  ayrı kaynak tek muhatapta birleşirdi. */
export const SEKME_TAKIMI: Readonly<Record<MuhatapTuru, readonly SekmeAdi[]>> = {
  kanal: ["sohbet", "defter", "olcum"],
  ajan: ["sohbet", "teslimler"],
  sahipsiz: ["teslimler"],
};

export function sekmeSec(tur: MuhatapTuru, istenen: SekmeAdi): SekmeAdi {
  const takim = SEKME_TAKIMI[tur];
  return takim.includes(istenen) ? istenen : (takim[0] ?? "sohbet");
}

/* ---- ROTA ---------------------------------------------------------------- */

export interface RotaHedefi {
  /** Muhatap dilimi. `null` YALNIZ eski `…/chat/filo` bağında olur ve
   *  "ajan tarafı; hangi ajan olduğunu oturum hafızası söyler" demektir. */
  readonly muhatap: string | null;
  readonly sekme: SekmeAdi;
  /** Eski bir derin bağdan mı çözüldü — URL yeniden yazılmaz, yalnız yorumlanır. */
  readonly eskiBag: boolean;
}

/** ESKİ DÖRT BAĞ. Silinmezler: RUNBOOK bağları, çekmece çipleri ve operatörün
 *  yer imleri bu adresleri taşıyor (`pano/rota.tsx` başlığındaki aynı gerekçe). */
const ESKI_BAGLAR: Readonly<Record<string, RotaHedefi>> = {
  sohbet: { muhatap: KANAL_DILIMI, sekme: "sohbet", eskiBag: true },
  defter: { muhatap: KANAL_DILIMI, sekme: "defter", eskiBag: true },
  olcum: { muhatap: KANAL_DILIMI, sekme: "olcum", eskiBag: true },
  filo: { muhatap: null, sekme: "sohbet", eskiBag: true },
};

function sekmeOku(x: string): SekmeAdi {
  return x === "teslimler" || x === "defter" || x === "olcum" || x === "sohbet" ? x : "sohbet";
}

export function rotaEsle(bolum: string): RotaHedefi {
  const ham = bolum.trim();
  // BOŞ BÖLÜM KANALI AÇAR — ve bu bir URL SÖZLEŞMESİdir, bir tercih değil (inceleme
  // 6.5, 2026-08-31). Eski panoda `#/dashboard/chat/` ve `…/chat/sohbet` aynı ekranı,
  // yani hipotez hattını açıyordu; yer imleri, RUNBOOK bağları ve kenar çubuğunun
  // yüzey bağı bu davranışa dayanıyor. Maket varsayılanı @sef'tir ve bu sapma bilerek
  // yapıldı: korunması gereken şey maketin süsü değil, adresin anlamı.
  //
  // İLK YAZIMDA GEREKÇE YANLIŞ YAZILMIŞTI ("ajan varsayılanı yükten önce muhatapsız
  // kare üretirdi") ve ÖLÇÜMLE ÇELİŞİYORDU: `muhatapSec(liste, null, …)` roster boşken
  // zaten kanala düşüyor — muhatapsız kare mümkün değil, çivisi de var.
  if (ham === "") return { muhatap: KANAL_DILIMI, sekme: "sohbet", eskiBag: false };
  const eski = ESKI_BAGLAR[ham];
  if (eski !== undefined) return eski;
  const nokta = ham.indexOf(".");
  if (nokta === -1) return { muhatap: ham, sekme: "sohbet", eskiBag: false };
  return {
    muhatap: ham.slice(0, nokta),
    sekme: sekmeOku(ham.slice(nokta + 1)),
    eskiBag: false,
  };
}

export function rotaYaz(muhatap: string, sekme: SekmeAdi): string {
  return `/dashboard/chat/${muhatap}.${sekme}`;
}

/** ÜST BAR KIRINTISININ ÇÖZÜCÜSÜ — kayıt sisteminin ÜÇÜNCÜ tüketicisi.
 *
 *  İnceleme Ö-1 (2026-08-31): `alanlar.ts` kaydına bakan yalnız kenar çubuğu ve v288
 *  paritesi değil; `kabuk/Ustbar.tsx` de `rota.bolum`u kayıtlı `kimlik`lerle BİREBİR
 *  eşleştiriyor. Yeni kanonik bölüm (`bot-sef.teslimler`) kayıtta olmadığı için kırıntı
 *  ikinci seviyesini SESSİZCE düşürüyordu — hata yok, çivi yok, sadece kabuğun bir
 *  parçası bu yüzeyde susuyor.
 *
 *  KAYIT SİSTEMİ GENİŞLETİLDİ, KOPYA ÜRETİLMEDİ: `alanlar.ts::Yuzey.bolumCoz` bu
 *  fonksiyonu çağırıyor, yani sekme adları TEK yerde (`SEKME_ETIKET`) duruyor.
 *  Kayda yeni `kimlik` EKLENEMEZDİ: v324 `kimlik` değerinin slug olmasını şart koşuyor
 *  ve `oneri-hatti.sohbet` noktayla slug değildir; ajan dilimleri ise roster'dan
 *  TÜRÜYOR, yani statik kayda hiç sığmaz.
 *
 *  NE GÖSTERİLİYOR VE NEDEN BU KADAR: yalnız SEKME etiketi. Muhatap adını buradan
 *  üretmek uydurma olurdu — elimizde yalnız dilim var (`bot-sef`), adın kendisi değil,
 *  ve `ana-hermes` gibi bir dilimden ad çıkarmak tahmindir. Eski kayıt da tam bunu
 *  veriyordu ("Ajan › Sohbet"), yani kırıntı bu turda hiçbir şey KAYBETMİYOR. */
export function bolumEtiketi(bolum: string): string | null {
  const ham = bolum.trim();
  if (ham === "") return null;
  const nokta = ham.indexOf(".");
  if (nokta === -1) return null; // düz kimlik: kaydın kendi girdisi zaten eşleşir
  return SEKME_ETIKET[sekmeOku(ham.slice(nokta + 1))];
}

/* ---- DİLİMLEME ----------------------------------------------------------- */

const HARF: Readonly<Record<string, string>> = {
  ç: "c", ğ: "g", ı: "i", ö: "o", ş: "s", ü: "u", â: "a", î: "i", û: "u",
};

function sadelestir(x: string): string {
  return x
    .toLocaleLowerCase("tr-TR")
    .replace(/[^a-z0-9]/g, (k) => HARF[k] ?? "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

/** KİMLİK ÇİFTTEN TÜRER (`filoOku.ts::ajanOku` ile aynı gerekçe): bir profil
 *  `hermes` adını taşırsa `tur` ayırır, yoksa iki muhatap tek adrese düşer. */
export function ajanDilimi(a: FiloAjani): string {
  const t = sadelestir(a.tur ?? "") || "ajan";
  const d = sadelestir(a.ad ?? "") || "adsiz";
  return `${t}-${d}`;
}

/* ---- MUHATAP LİSTESİ ----------------------------------------------------- */

export interface Muhatap {
  readonly dilim: string;
  readonly tur: MuhatapTuru;
  readonly ad: string;
  /** Avatar harfi/işareti — ada bağlı, uydurma değil. */
  readonly isaret: string;
  /** Ajan muhataplarda ham kayıt; kanal ve hayalet satırda `null`. */
  readonly ajan: FiloAjani | null;
}

function isaretle(ad: string | null): string {
  const s = (ad ?? "").replace(/^@/, "").trim();
  return s === "" ? "?" : s.slice(0, 1).toLocaleUpperCase("tr-TR");
}

/** Sol listenin sırası: önce AJANLAR (uçtan geldiği sırada), sonra KANALLAR.
 *  `ajanlar === null` (roster ölçülemedi) yalnız kanalı döndürür — boş bir ajan
 *  listesi "bot yok" derdi, oysa ölçülen şey "listeyi okuyamadım"dır ve o hüküm
 *  sol listenin üstündeki şeritte AYRI çiziliyor. */
export function muhataplar(ajanlar: readonly FiloAjani[] | null, kanalAdi: string): readonly Muhatap[] {
  const cikti: Muhatap[] = [];
  if (ajanlar !== null) {
    for (const a of ajanlar) {
      cikti.push({
        dilim: ajanDilimi(a),
        tur: "ajan",
        ad: a.ad ?? "(adsız kayıt)",
        isaret: a.tur === "ana" ? "⌘" : isaretle(a.ad),
        ajan: a,
      });
    }
  }
  cikti.push({ dilim: KANAL_DILIMI, tur: "kanal", ad: kanalAdi, isaret: "#", ajan: null });
  return cikti;
}

export interface MuhatapSecimi {
  readonly muhatap: Muhatap | null;
  /** İstenen dilim listede YOKSA adı burada durur — sessizce kanala düşmek,
   *  kırık bir derin bağı sağlam göstermek olurdu. */
  readonly bulunamayan: string | null;
  /** "Bulunamadı" hükmünün SEBEBİ ölçülemezlikse `true` — ve bu AYRI bir cümledir.
   *
   *  İnceleme Ö-2 (2026-08-31): `ajanlar: null` iken `muhataplar()` yalnız kanalı
   *  döndürür, dolayısıyla HER ajan derin bağı `bulunamayan` kovasına düşerdi ve
   *  ekranda "bu ad listede yok, bağın eski olabilir" yazardı. Teşhis YANLIŞ: ad
   *  muhtemelen doğru, okunamayan şey listenin KENDİSİ — operatör sağlam bir yer
   *  imini silerdi. İki hüküm ayrı taşınır. */
  readonly listeOlculemedi: boolean;
}

/** BAYAT/YANLIŞ DİLİM SESSİZ BOŞ PANEL ÜRETMEZ.
 *  `istenen === null` yalnız eski `…/chat/filo` bağından gelir: o bağ bir AJAN
 *  istiyordu, kanalı değil — bu yüzden sırayla son seçilen ajana, `sef`e ve ilk
 *  ajana düşer; hiç ajan yoksa kanala.
 *
 *  `listeOlculdu` ÇAĞIRANDAN GELİR (`yuk.ajanlar !== null`): bu fonksiyonun elinde
 *  yalnız türetilmiş liste var ve boş bir ajan kümesi ile okunamamış bir roster
 *  ORADA aynı görünür. Ayrımı taşımak çağıranın işi, ayrımı SÖYLEMEK bu tipin. */
export function muhatapSec(
  liste: readonly Muhatap[],
  istenen: string | null,
  sonAjanDilimi: string | null,
  listeOlculdu: boolean,
): MuhatapSecimi {
  if (istenen !== null) {
    const bulundu = liste.find((m) => m.dilim === istenen);
    if (bulundu !== undefined) return { muhatap: bulundu, bulunamayan: null, listeOlculemedi: false };
    const kanal = liste.find((m) => m.tur === "kanal") ?? null;
    return { muhatap: kanal, bulunamayan: istenen, listeOlculemedi: !listeOlculdu };
  }
  const ajanlar = liste.filter((m) => m.tur === "ajan");
  const son = sonAjanDilimi === null ? undefined : ajanlar.find((m) => m.dilim === sonAjanDilimi);
  const sef = ajanlar.find((m) => m.dilim.endsWith("-sef"));
  const secilen = son ?? sef ?? ajanlar[0] ?? liste.find((m) => m.tur === "kanal") ?? null;
  return { muhatap: secilen, bulunamayan: null, listeOlculemedi: false };
}

/** Sol liste araması — ada VE önizleme metnine bakar (arama kutusu "mesaj ara"
 *  diyor; yalnız ada bakmak o vaadi yarım bırakırdı).
 *
 *  İKİ DÜZELTME (inceleme Ö-6, 2026-08-31):
 *  (a) KANAL SATIRI DA ÖNİZLEMESİNDEN SÜZÜLÜR. Eskiden kanal yalnız adına göre
 *      süzülüyordu (`m.ajan === null` önizleme dalına hiç girmiyordu), oysa kanalın
 *      mesajları sağ panelde gerçekten süzülüyor: "RVOL" yazan operatör aradığı
 *      öneriyi sağda görüyor ama SOL sütun "hiçbir kanalı geçirmedi" diyordu.
 *      Kanalın önizlemesi ajan kaydından değil `/api/agent`ten geliyor, bu yüzden
 *      dışarıdan bir sözlükle (`kanalMetni`) veriliyor — tek kaynak korunur.
 *  (b) AÇIK SOHBET LİSTEDEN DÜŞMEZ. Mesajlaşma gramerinde okumakta olduğun konuşmanın
 *      listeden silinmesi, seçimin nereye gittiğini belirsizleştirir; `korunan` dilim
 *      süzgeçten muaftır ve bu MUAFİYET ekranda söylenir (`Yanliste` başlığı). */
export function listeSuz(
  liste: readonly Muhatap[],
  sorgu: string,
  kanalMetni: string | null,
  korunan: string | null,
): readonly Muhatap[] {
  const q = sorgu.trim().toLocaleLowerCase("tr-TR");
  if (q === "") return liste;
  const kucuk = (x: string | null) => (x === null ? "" : x.toLocaleLowerCase("tr-TR"));
  return liste.filter((m) => {
    if (m.dilim === korunan) return true;
    if (kucuk(m.ad).includes(q)) return true;
    if (m.ajan === null) return kucuk(kanalMetni).includes(q);
    const o = sonMesajOzeti(m.ajan);
    return o !== null && kucuk(o.metin).includes(q);
  });
}

/* ---- ZAMAN --------------------------------------------------------------- */

/** YEREL gün anahtarı. UTC kullansaydık gece yarısına yakın damgalar bir gün
 *  kayar, "bugün aktif" hükmü operatörün saatiyle çelişirdi. */
function gunAnahtari(ms: number): string {
  const d = new Date(ms);
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}

/** Damga yerel gün anahtarına; çevrilemiyorsa `null` (uydurma yok). */
export function isoGunu(iso: string | null): string | null {
  if (iso === null) return null;
  const t = Date.parse(iso);
  return Number.isNaN(t) ? null : gunAnahtari(t);
}

function isoMs(iso: string | null): number | null {
  if (iso === null) return null;
  const t = Date.parse(iso);
  return Number.isNaN(t) ? null : t;
}

/* ---- AKTİFLİK ------------------------------------------------------------ */

export type Aktiflik = "aktif" | "sessiz" | "olculemedi";

/** TANIM (beyanlı, §3 yukarıda): bugüne (YEREL gün) düşen bir oturum ya da
 *  teslim damgası varsa "aktif". Yoksa hüküm iki dala ayrılır ve bu ayrım bu
 *  yüzeyin bütün etiği: bir kaynak okunamadıysa ya da bir damga zamana
 *  yerleşmiyorsa "sessiz" DEMEYİZ — o defterde bugün konuşulmuş olabilir. */
export function aktiflik(a: FiloAjani, simdiMs: number): Aktiflik {
  const bugun = gunAnahtari(simdiMs);
  let bugunVar = false;
  let belirsiz = false;

  if (a.oturumlar === null) {
    belirsiz = true;
  } else {
    for (const o of a.oturumlar) {
      const g = isoGunu(o.ts);
      if (g === null) belirsiz = true;
      else if (g === bugun) bugunVar = true;
    }
  }
  if (isoGunu(a.sonOturumTs) === bugun) bugunVar = true;

  if (a.teslimler === null) {
    belirsiz = true;
  } else {
    for (const t of a.teslimler) {
      const g = isoGunu(t.ts);
      if (g === null) belirsiz = true;
      else if (g === bugun) bugunVar = true;
    }
  }

  if (bugunVar) return "aktif";
  return belirsiz ? "olculemedi" : "sessiz";
}

export interface AktiflikSayimi {
  /** Bugün konuşmuş ya da teslim etmiş muhataplar — şeritte avatarı çizilenler. */
  readonly aktif: readonly Muhatap[];
  readonly sessiz: number;
  readonly olculemedi: number;
}

/** "ŞU AN AKTİF" ŞERİDİNİN SAYIMI — ÜÇ HÂL ÜÇ AYRI KOVADA.
 *
 *  İnceleme K-1 (2026-08-31): şerit yalnız `"aktif"`i sayıyor, kalan iki hâli tek
 *  kovaya döküyor ve ekrana "ölçülmüş boşluk" yazıyordu. Üç profilin `state.db`si
 *  kilitliyken şerit "bugüne düşen damga yok — ölçülmüş boşluk" der, hemen altında
 *  üç AMBER nokta dururdu: aynı ekranda iki zıt hüküm, ve üstteki YALAN. `aktiflik()`
 *  içinde M2 mutasyonuyla korunan ayrım, toplulaştırma katmanında geri alınıyordu.
 *  Sayım bu yüzden burada, saf ve çivili: çağıran hangi cümleyi basacağını
 *  UYDURAMAZ, sayıdan okur. */
export function aktiflikSayimi(liste: readonly Muhatap[], simdiMs: number): AktiflikSayimi {
  const aktif: Muhatap[] = [];
  let sessiz = 0;
  let olculemedi = 0;
  for (const m of liste) {
    if (m.tur !== "ajan" || m.ajan === null) continue;
    const h = aktiflik(m.ajan, simdiMs);
    if (h === "aktif") aktif.push(m);
    else if (h === "sessiz") sessiz += 1;
    else olculemedi += 1;
  }
  return { aktif, sessiz, olculemedi };
}

/* ---- TÜRETİLMİŞ ÖZETLER -------------------------------------------------- */

/** Bir ajanın oturumlarındaki TOPLAM mesaj sayısı. `oturumlar` ya da herhangi bir
 *  oturumun `mesajlar`ı ölçülemediyse `null` — 0 yazmak "bu ajanla hiç
 *  mesajlaşılmadı" iddiası olurdu.
 *
 *  `filoOku.ts::mesajSayisi`NİN YERİNİ ALDI (inceleme Ö-5): eski sürümün tek çağıranı
 *  bu turda silinen `AjanKarti`ydı ve ölü kaldı; ölçüm ise KAYBOLMAMALIYDI (bedel
 *  yasası). Yeri değişti — muhatap başlığında duruyor. */
export function mesajToplami(a: FiloAjani): number | null {
  if (a.oturumlar === null) return null;
  let n = 0;
  for (const o of a.oturumlar) {
    if (o.mesajlar === null) return null;
    n += o.mesajlar.length;
  }
  return n;
}

/** Taranan pencerede geçen TEKİL modeller (uçtan geldiği sırada). Liste birden çok
 *  ad taşıyorsa pencerede model değişmiştir.
 *
 *  `filoOku.ts::modeller`İN YERİNİ ALDI (inceleme Ö-5) ve TAŞIDIĞI GÜVENCE AYRI:
 *  akıştaki geçiş çipi yalnız KOMŞU oturumlar arasındaki değişimi gösterir; bu sayı
 *  "pencerede kaç ayrı model geçti" sorusunu cevaplar. İkisi aynı şey değildir —
 *  bir model gidip geri gelirse çip iki kez çıkar ama tekil sayı 2'de kalır. */
export function penceredekiModeller(a: FiloAjani): readonly string[] | null {
  if (a.oturumlar === null) return null;
  const g = new Set<string>();
  for (const o of a.oturumlar) if (o.model !== null) g.add(o.model);
  return [...g];
}

/** En YENİ teslim damgası (başlıktaki "son teslim" bundan türer). Ölçülemeyen
 *  ya da boş listede `null` — 0/"—" yazmak bir teslim iddiası olurdu. */
export function sonTeslimTs(a: FiloAjani): string | null {
  if (a.teslimler === null) return null;
  let en: number | null = null;
  let enIso: string | null = null;
  for (const t of a.teslimler) {
    const ms = isoMs(t.ts);
    if (ms === null) continue;
    if (en === null || ms > en) {
      en = ms;
      enIso = t.ts;
    }
  }
  return enIso;
}

/** Listedeki satırın sağındaki saat: oturum ya da teslim, hangisi daha yeniyse. */
export function sonHareketTs(a: FiloAjani): string | null {
  let en: number | null = null;
  let enIso: string | null = null;
  const bak = (iso: string | null) => {
    const ms = isoMs(iso);
    if (ms === null) return;
    if (en === null || ms > en) {
      en = ms;
      enIso = iso;
    }
  };
  bak(a.sonOturumTs);
  if (a.oturumlar !== null) for (const o of a.oturumlar) bak(o.ts);
  if (a.teslimler !== null) for (const t of a.teslimler) bak(t.ts);
  return enIso;
}

export interface MesajOzeti {
  readonly metin: string | null;
  readonly ts: string | null;
}

/** Listedeki önizleme satırı — EN YENİ mesaj. Uç `oturumlar`ı yeniden eskiye,
 *  `mesajlar`ı eskiden yeniye gönderiyor: en yeni mesaj ilk oturumun SON
 *  satırıdır. Oturum kaynağı ölçülemediyse `null` döner ve çağıran önizleme
 *  yerine nedeni basar. */
export function sonMesajOzeti(a: FiloAjani): MesajOzeti | null {
  if (a.oturumlar === null) return null;
  for (const o of a.oturumlar) {
    const m = o.mesajlar;
    if (m === null || m.length === 0) continue;
    const son = m[m.length - 1];
    if (son === undefined) continue;
    return { metin: son.metin, ts: son.ts ?? o.ts };
  }
  return null;
}

/* ---- OTURUM SIRASI VE MODEL GEÇİŞİ --------------------------------------- */

export interface ModelGecisi {
  readonly onceki: string;
  readonly yeni: string;
}

export interface OturumGorunumu {
  readonly oturum: FiloOturumu;
  /** Bu oturumda model DEĞİŞTİYSE dolu. Kıyas ZAMANCA önceki oturumladır. */
  readonly gecis: ModelGecisi | null;
}

/** TEK TERSLEME NOKTASI (sözleşme §2). Uç yeniden→eskiye gönderir; ekran
 *  eskiden→yeniye okur. Model-geçiş kıyası bu yeni sıraya göre DÜZELTİLDİ:
 *  eski kodda karşılaştırma `oturumlar[i + 1]` ileydi (yeniden→eskiye dizide
 *  bir SONRAKİ, zamanca öncekiydi); terslenmiş dizide zamanca önceki artık
 *  `i - 1`dir. Aynı satırı taşıyıp indeksi düzeltmemek, geçiş çipini bir oturum
 *  kaydırırdı ve hiçbir şey kırmızıya dönmezdi. */
export function oturumlariEskidenYeniye(oturumlar: readonly FiloOturumu[]): readonly OturumGorunumu[] {
  const sirali = [...oturumlar].reverse();
  return sirali.map((o, i) => {
    const onceki = i === 0 ? undefined : sirali[i - 1];
    const gecis =
      onceki !== undefined && onceki.model !== null && o.model !== null && onceki.model !== o.model
        ? { onceki: onceki.model, yeni: o.model }
        : null;
    return { oturum: o, gecis };
  });
}

/* ---- AKIŞ ---------------------------------------------------------------- */

export type AkisOgesi =
  | { readonly tur: "gun"; readonly anahtar: string; readonly ts: string | null }
  | { readonly tur: "gecis"; readonly anahtar: string; readonly gecis: ModelGecisi }
  | { readonly tur: "oturum"; readonly anahtar: string; readonly oturum: FiloOturumu }
  | { readonly tur: "mesaj"; readonly anahtar: string; readonly mesaj: FiloMesaji }
  | { readonly tur: "bosluk"; readonly anahtar: string; readonly olculemedi: boolean }
  | { readonly tur: "teslim"; readonly anahtar: string; readonly teslim: FiloTeslimi }
  | { readonly tur: "yersiz"; readonly anahtar: string; readonly n: number };

function teslimSirasi(x: FiloTeslimi, y: FiloTeslimi): number {
  return (isoMs(x.ts) ?? 0) - (isoMs(y.ts) ?? 0);
}

/** Bot sohbetinin TEK akışı: oturumlar (eskiden→yeniye) + mesajlar (uçtan geldiği
 *  sırada) + teslim olayları, gün ve oturum ayraçlarıyla.
 *
 *  TESLİMLER İKİNCİ BİR KAYNAKTIR ve akışa ZAMANLA yerleşirler: her teslim,
 *  başlangıcı ondan ÖNCE olan SON oturumun arkasına konur. Mesajları damgaya
 *  göre yeniden sıralamıyoruz (damgasız mesaj konuşmayı bozardı) — yerleştirme
 *  oturum sınırında yapılıyor, satır sırası uçtan geldiği gibi kalıyor.
 *  Hiçbir oturumdan önceye düşen teslimler EN BAŞTA, damgası çevrilemeyenler
 *  ise sonda AYRI bir başlıkla durur: sessizce düşürmek, olay defterinde var
 *  olan bir teslimi ekranda yok göstermek olurdu.
 *
 *  `teslimler === null` (ölçülemedi) burada boş listeye düşer ve bu KAYIP
 *  DEĞİLDİR: o hüküm Teslimler sekmesinde ve sol listedeki amber noktada AYRI
 *  çiziliyor — akışın içine "teslim defteri okunamadı" diye bir sistem çipi
 *  koymak aynı hükmü iki yerde anlatır, ayrışmaya açık bir kopya olurdu. */
export function botAkisi(a: FiloAjani): readonly AkisOgesi[] {
  const oturumlar = a.oturumlar;
  if (oturumlar === null) return [];

  const gorunum = oturumlariEskidenYeniye(oturumlar);
  const zamanlar = gorunum.map((g) => isoMs(g.oturum.ts));

  const kovalar: FiloTeslimi[][] = gorunum.map(() => []);
  const oncekiler: FiloTeslimi[] = [];
  const yersizler: FiloTeslimi[] = [];
  const teslimler = a.teslimler === null ? [] : a.teslimler;

  for (const t of teslimler) {
    const z = isoMs(t.ts);
    if (z === null) {
      yersizler.push(t);
      continue;
    }
    let hedef = -1;
    for (let i = 0; i < zamanlar.length; i += 1) {
      const zi = zamanlar[i];
      if (zi !== null && zi !== undefined && zi <= z) hedef = i;
    }
    if (hedef === -1) oncekiler.push(t);
    else kovalar[hedef]?.push(t);
  }
  oncekiler.sort(teslimSirasi);
  for (const k of kovalar) k.sort(teslimSirasi);

  const cikti: AkisOgesi[] = [];
  let sonGun: string | null | undefined;
  const gunEkle = (iso: string | null) => {
    const g = isoGunu(iso);
    if (sonGun !== undefined && g === sonGun) return;
    sonGun = g;
    cikti.push({ tur: "gun", anahtar: `gun-${g ?? "tarihsiz"}-${cikti.length}`, ts: iso });
  };

  oncekiler.forEach((t, i) => {
    gunEkle(t.ts);
    cikti.push({ tur: "teslim", anahtar: `onteslim-${i}`, teslim: t });
  });

  gorunum.forEach((g, i) => {
    gunEkle(g.oturum.ts);
    if (g.gecis !== null) cikti.push({ tur: "gecis", anahtar: `gecis-${i}`, gecis: g.gecis });
    cikti.push({ tur: "oturum", anahtar: `oturum-${g.oturum.id ?? i}`, oturum: g.oturum });
    const mesajlar = g.oturum.mesajlar;
    if (mesajlar === null) {
      cikti.push({ tur: "bosluk", anahtar: `bosluk-${i}`, olculemedi: true });
    } else if (mesajlar.length === 0) {
      cikti.push({ tur: "bosluk", anahtar: `bosluk-${i}`, olculemedi: false });
    } else {
      mesajlar.forEach((m, j) => cikti.push({ tur: "mesaj", anahtar: `mesaj-${i}-${j}`, mesaj: m }));
    }
    (kovalar[i] ?? []).forEach((t, j) => {
      gunEkle(t.ts);
      cikti.push({ tur: "teslim", anahtar: `teslim-${i}-${j}`, teslim: t });
    });
  });

  if (yersizler.length > 0) {
    cikti.push({ tur: "yersiz", anahtar: "yersiz-baslik", n: yersizler.length });
    yersizler.forEach((t, i) => cikti.push({ tur: "teslim", anahtar: `yersiz-${i}`, teslim: t }));
  }
  return cikti;
}

/* ---- MESAJ ROLLERİ ------------------------------------------------------- */

/** Balon HANGİ TARAFA yaslanır. Tetik/operatör solda, ajan sağda (maket). Rol
 *  kaydedilmemişse SAĞA atmıyoruz: tanınmayan bir satırı ajanın ağzına koymak,
 *  ölçülmemiş bir şeyi ajanın cümlesi saymak olurdu. */
export function mesajYani(rol: string | null): "sol" | "sag" {
  return rol === "assistant" ? "sag" : "sol";
}

export const ROL_ETIKET: Readonly<Record<string, string>> = {
  user: "tetik / operatör",
  assistant: "ajan",
  system: "sistem yönergesi",
  tool: "araç",
};
