/* ============================================================================
   PALET ENVANTERİ — ⌘K'nın Meridian tarafı
   ----------------------------------------------------------------------------
   NEDEN VAR: şablonun `SearchDialog`u yalnız kenar çubuğu maddelerini arıyordu,
   yani paletin bildiği tek kelime dağarcığı YÜZEY BAŞLIKLARIYDI. Eski panonun
   paleti (`meridian/web/palette.js`, 54 KB) bundan fazlasını yapıyordu ve
   farkın üç sınıfı vardı:

     (a) GEZİNME — yüzey + bölüm çapaları, Türkçe-katlamalı bulanık aramayla ve
         her bölüm için EL YAZISI ANAHTAR KELİMELERLE ("mutabakat" bölümünü
         "ayna", "broker", "ghost" da bulur). Bu dosya bunu geri getiriyor.
     (b) OKUMA — panoyu yeniden okut, sembol ara, belgeye git.
     (c) YAZMA — HALT / Cancel-Open / FLATTEN / Halt-Learning / ack kuyrukları /
         Hermes sprint kolları. BU SINIF YENİ PALETE ALINMADI ve gerekçesi
         `search-dialog.tsx`in başındaki şerhte yazılı: geri alınamaz icranın
         en kötü eşleşmesi hızlı erişimdir.

   ÜÇ ŞEY BİLEREK BURADA, BİLEŞENDE DEĞİL: katlama, skorlayıcı ve anahtar kelime
   tablosu. Üçü de SAF — DOM'a, ağa, React'e dokunmaz; bir davranış tartışması
   çıktığında bileşen açmadan okunur (eski palet de tam bu sebeple çekirdeğini
   ayırmıştı, bkz. palette.js "BÖLÜM 1 — SAF ÇEKİRDEK").
   ============================================================================ */
import { YUZEYLER, YUZEY_ANAHTARLARI, yuzeyYolu } from "./alanlar";
import type { PiyasaSatiri } from "./yuzeyler/sistem/uctipleri";

/* ---------------------------------------------------------------------------
   TÜRKÇE KATLAMA
   `toLowerCase()` TEK BAŞINA YETMEZ: "İ".toLowerCase() bileşik bir "i̇" (i +
   birleşen nokta) üretir ve o dizgi "i" ile EŞLEŞMEZ — arama sessizce boş
   dönerdi. Bu yüzden katlama ÖNCE, küçültme SONRA. Ayrıca klavyede Türkçe harf
   olmayabilir ve olsa bile kimse "Öğrenme" yazmak için ö'yü aramaz.
   (Tablo eski paletten birebir taşındı — aynı aramanın iki farklı sonucu
   olmasın diye.)
   --------------------------------------------------------------------------- */
const KATLAMA: Readonly<Record<string, string>> = {
  İ: "I", I: "I", ı: "i", Ş: "S", ş: "s", Ğ: "G", ğ: "g",
  Ü: "U", ü: "u", Ö: "O", ö: "o", Ç: "C", ç: "c",
  Â: "A", â: "a", Î: "I", î: "i", Û: "U", û: "u",
};

export function katla(s: string | null | undefined): string {
  if (s == null) return "";
  let out = "";
  for (const c of String(s)) out += KATLAMA[c] ?? c;
  return out.toLowerCase();
}

/** Kelime sınırı: bu karakterlerden SONRA gelen harf yeni bir kelimenin başıdır
 *  ve baş harf eşleşmesi orta-kelime eşleşmesinden daha anlamlıdır. */
const SINIR = /[\s·\-_/(),.'"⌘→⚠]/;

/** ALT DİZİ eşleşmesi + biçim ödülleri. Eşleşme yoksa `null` — bu bir EŞİK
 *  değil, GERÇEK yokluk. Ağırlıklar eski paletten taşındı. */
export function bulanikSkor(hedef: string, sorgu: string): number | null {
  const h = katla(hedef);
  const s = katla(sorgu);
  if (!s) return 0; // boş sorgu her şeyle eşleşir; sıralamayı çağıran yapar
  if (!h) return null;
  let skor = 0;
  let imlec = 0;
  let onceki = -2;
  for (const c of s) {
    let bulundu = -1;
    for (let k = imlec; k < h.length; k++) {
      if (h[k] === c) {
        bulundu = k;
        break;
      }
    }
    if (bulundu < 0) return null; // bir harf bile düşerse eşleşme YOK
    const bitisik = bulundu === onceki + 1;
    const sinirda = bulundu === 0 || SINIR.test(h[bulundu - 1] ?? "");
    skor += 3;
    if (bitisik) skor += 12; // bitişiklik en güçlü sinyal: yazdığın gibi duruyor
    if (sinirda) skor += 9; // kelime başı: baş harf kısaltmaları çalışsın
    if (!bitisik && !sinirda) skor -= Math.min(6, (bulundu - onceki - 1) * 0.4);
    onceki = bulundu;
    imlec = bulundu + 1;
  }
  if (h.indexOf(s) === 0) skor += 30; // gerçek ön ek (baştan başlayan eşleşme dahil)
  skor -= Math.min(10, h.length * 0.2); // eşitlikte KISA hedef kazanır
  return skor;
}

/* cmdk'nın kendi süzgeci (command-score) Türkçeyi katlamıyor: "gölge" yazan
   "Gölge kollar"ı buluyor ama "golge" yazan HİÇBİR ŞEY bulamıyordu — ve klavyede
   Türkçe harf olmayan bir operatör için bu, paletin yarısının yok olması demek.
   İmza cmdk'nın: (değer, sorgu, anahtarlar) → skor; 0 "eşleşme yok" demektir.

   SIKIŞTIRMA LOJİSTİK, KIRPMA DEĞİL: ham skor cezalarla EKSİYE düşebilir ve
   `Math.max(0, …)` gibi bir kırpma o satırı listeden SESSİZCE düşürürdü —
   yani bulunan bir eşleşme "yok" diye okunurdu. Lojistik eğri sırayı birebir
   korur ve çıktısı hiçbir zaman 0 olmaz. */
function sikistir(ham: number): number {
  return 1 / (1 + Math.exp(-ham / 25));
}

export function paletFiltresi(deger: string, sorgu: string, anahtarlar?: string[]): number {
  const a = bulanikSkor(deger, sorgu);
  if (a !== null) return sikistir(a);
  // ANAHTAR KELİME EŞLEŞMESİ ADDAN ZAYIFTIR: satırın görünen metni eşleşmiyorsa
  // operatör neden çıktığını gözle doğrulayamaz; üste çıkması yanıltıcı olur.
  let en: number | null = null;
  for (const k of anahtarlar ?? []) {
    const r = bulanikSkor(k, sorgu);
    if (r !== null && (en === null || r > en)) en = r;
  }
  // ZAYIFLATMA SIKIŞTIRMADAN SONRA: ham skoru 0,8 ile çarpmak NEGATİF skorları
  // (uzak harfli, cezalı eşleşmeler) sıfıra YAKLAŞTIRIR, yani zayıflatmak yerine
  // güçlendirirdi. Sıkıştırılmış değer her zaman (0,1) aralığında olduğu için
  // çarpım burada her yönde zayıflatır ve hiçbir zaman 0 üretmez.
  return en === null ? 0 : sikistir(en) * 0.8;
}

/* ---------------------------------------------------------------------------
   ANAHTAR KELİME TABLOSU — operatörün AKLINDAKİ kelime, başlıktaki kelime değil
   Eski paletin `BOLUMLER` tablosundan taşındı; yeni bölümler (roadmap · sprint ·
   belgeler · sohbet · defter · olcum · tercihler · giris · kayit) eklendi.
   Değerler KATLANMIŞ yazılır (ö/ü/ş yok): eşleştirici zaten katlıyor, tabloyu da
   katlanmış tutmak "hangi biçimde yazıldı?" sorusunu tamamen ortadan kaldırıyor.
   --------------------------------------------------------------------------- */
const BOLUM_EK: Readonly<Record<string, readonly string[]>> = {
  brifing: ["kitap", "pozisyon", "sermaye", "equity", "brifing", "bugun"],
  mutabakat: ["ayna", "broker", "ghost", "hwm", "dolum", "reconcile", "sapma"],
  intraemir: ["intraday", "golge", "silah", "arm", "tetik", "icra", "seans ici"],
  adaylar: ["aday", "tarama", "sinyal", "plan", "candidate", "elenen", "tahta"],
  kapilar: ["kapi", "gate", "matris", "eleme", "rejim", "karartma", "karar agaci"],
  roadmap: ["yol haritasi", "roadmap", "is kalemi", "tur", "sira"],
  onaylar: ["onay", "kuyruk", "approve", "bekleyen", "senden is isteyen"],
  topviews: ["toplulastirma", "kirilim", "facet", "kesif", "sektor", "beceri"],
  performans: ["egri", "birikim", "islem", "trade", "dusus", "kelly", "para egrisi"],
  operasyon: ["alarm", "bekci", "olay", "gozetim", "butce", "gelen kutusu", "nabiz"],
  mudahale: ["kademe", "kol", "halt", "kilit", "flatten", "cancel", "acil", "durdur"],
  veriboru: ["karantina", "butunluk", "veri", "hat", "dedektor", "saglayici"],
  market: ["piyasa", "evren", "sembol", "ticker", "universe", "tazelik", "kapanis"],
  intraday: ["akis", "bar", "stream", "redis", "bosluk", "dakika"],
  cizelge: ["hat", "boru", "pipeline", "adim", "kadans", "zamanlanmis", "gece hatti"],
  karne: ["ogrenme", "skor", "hukum", "kalibrasyon", "rejim", "durust karne"],
  golge: ["shadow", "kagit", "varyant", "trend kolu", "golge kol"],
  bilesenic: ["kenar", "edge", "ic", "bilesen", "bayes", "selale", "dogrulama"],
  ajan: ["hipotez", "surum", "revizyon", "strateji", "v01", "defter"],
  skiller: ["skill", "arac", "beceri", "katki", "emekli", "kutuphane"],
  hermes: ["beyin", "llm", "mlops", "dikkat", "oz-degerlendirme", "dusun", "reflect", "backfill"],
  sprint: ["antrenman", "train", "kmax", "butce", "kosu"],
  hafiza: ["ders", "lesson", "memory", "cikarim", "lessons.md"],
  belgeler: ["karar belgesi", "hukum", "docs", "tur", "arsiv"],
  sohbet: ["ajan", "oneri", "konusma", "chat", "soru"],
  defter: ["kayit", "siralama", "oneri", "tablo"],
  olcum: ["tahmin", "kapi", "kim konustu", "isabet"],
  ayarlar: ["anahtar", "key", "yapilandirma", "alpaca", "sir", "secret", "broker"],
  tercihler: ["tema", "yerlesim", "yuz", "arayuz", "gece", "gunduz"],
  giris: ["login", "parola", "oturum", "sifre", "kapi"],
  kayit: ["register", "yeni kullanici", "signup", "ilk parola"],
  // KAPI YÜZEYİ (TSK-090). Kimlikler `kapi-` önekli (kayıt sözlüğü bölüm kimliğini KÜRESEL
  // tutuyor) ama operatör "apisix", "rota", "429" diye arar — anahtarlar onun aklındaki
  // kelimeyi taşır, başlıktakini değil.
  "kapi-saglik": ["apisix", "gateway", "admin api", "prometheus", "9180", "9091"],
  "kapi-rotalar": ["rota", "route", "llm", "openrouter", "model", "fallback", "zincir", "egress"],
  "kapi-metrikler": ["trafik", "istek", "durum kodu", "429", "sayac", "metrik"],
  "kapi-fazlar": ["faz", "tsk-089", "kurulum", "ingress", "filo", "kota"],
  // HAFIZA YÜZEYİ (TSK-091, bilgi mimarisi TSK-108'de sekiz görünüme genişledi).
  // Kapı ile aynı gerekçe: kimlikler `hafiza-` önekli (kayıt sözlüğü bölüm kimliğini
  // KÜRESEL tutuyor ve çıplak `hafiza` Belgeler'de dolu) ama operatör "recall", "bank",
  // "token" diye arar — anahtarlar onun aklındaki kelimeyi taşır, başlıktakini değil.
  // Değerler KATLANMIŞ yazılır (ö/ü/ş yok), tablonun geri kalanıyla aynı biçimde.
  //
  // EMEKLİ ÜÇ KİMLİĞİN ANAHTARLARI KAYBOLMADI, TAŞINDI: `hafiza-bankalar`ın kelimeleri
  // Ana Sayfa'ya, `hafiza-operasyon` ve `hafiza-kota`nınkiler Yapılandırma'ya geçti.
  // Emekli bir kimliği bu tabloda BIRAKMAK ölü satır olurdu — anahtar tablosu yalnız
  // KAYITLI bölümler için okunuyor (`ARAMA_ANAHTARLARI`), yani orada kalan satır
  // hiçbir aramayı bulmaz ve okunmadığı için de bayatladığı fark edilmez.
  "hafiza-anasayfa": ["bank", "hindsight", "banka", "arsiv", "fact", "ozet", "istatistik", "tazelik"],
  "hafiza-bellekler": ["kayit", "bellek", "memory", "ders", "metin", "world", "experience", "gozlem"],
  //
  // "ZIHIN MODELI" TSK-108 GÖREV 3'TE REFLECT'TEN BILGI'YE TAŞINDI — ve bu bir
  // ölçüm sonucudur, tercih değil: üst yüzeyde çıkarım belgeleri `knowledge`
  // sekmesinin ikinci alt sekmesindedir. Anahtar eski yerinde kalsaydı palet
  // operatörü modelleri ÇİZMEYEN bir sayfaya gönderirdi — çalışan ama yanlış
  // yere giden bir bağ, çalışmayan bağdan daha sinsidir.
  "hafiza-bilgi": ["bilgi", "knowledge", "sayfa", "agac", "not", "zihin modeli", "mental model",
                   "cikarim", "tazelik", "cron"],
  "hafiza-recall": ["recall", "sorgu", "arama", "cevap", "getir", "skor", "iz", "trace"],
  "hafiza-reflect": ["reflect", "dusun", "think", "gozlem", "observation", "kapsam", "scope",
                     "consolidation"],
  "hafiza-belgeler": ["belge", "document", "parca", "chunk", "ice aktarim", "kaynak"],
  "hafiza-varliklar": ["varlik", "entity", "isim", "graf", "kisi", "bag", "harita", "birlikte"],
  "hafiza-yapilandirma": ["config", "ayar", "retain", "denetim", "audit", "hareket", "yazim",
                          "llm", "kota", "token", "cagri", "kullanim", "islem", "operations",
                          "webhook", "bellek savunmasi", "memory defense"],
};

const YUZEY_EK: Readonly<Record<string, readonly string[]>> = {
  default: ["bugun", "genel", "ozet", "acilis", "ana ekran"],
  finance: ["portfoy", "kitap", "sermaye", "pozisyon"],
  analytics: ["analiz", "birikim", "egri"],
  productivity: ["antrenman", "sprint", "hermes", "makine"],
  academy: ["ogrenme", "karne", "akademi", "beyin"],
  infrastructure: ["saglik", "altyapi", "sistem", "makine", "alarm", "kilit"],
  gateway: ["kapi", "apisix", "gateway", "rota", "llm", "egress", "proxy", "vekil"],
  memory: ["hafiza", "hindsight", "bellek", "bank", "retain", "consolidation", "recall"],
  "file-manager": ["belge", "hafiza", "dosya", "ders"],
  chat: ["ajan", "sohbet", "chat"],
  calendar: ["cizelge", "takvim", "zamanlanmis"],
  kanban: ["karar", "zincir", "tahta", "aday"],
  tasks: ["onay", "kuyruk", "gorev", "bekleyen"],
  profile: ["operator", "hesap", "profil", "ayar"],
  users: ["kullanici", "erisim", "kim"],
  roles: ["rol", "yetki", "izin"],
  authentication: ["giris", "oturum", "kimlik", "login"],
};

/* ANAHTAR YOL'DUR, KENAR ÇUBUĞU KİMLİĞİ DEĞİL. Kenar çubuğu maddesinin `id`si
   `gezinme.ts`de elle kuruluyor (`${anahtar}-${kimlik}`); ona bağlansaydık o
   biçim değiştiği gün anahtar kelimeler SESSİZCE düşerdi. `url` ise iki tarafta
   da AYNI fonksiyondan (`yuzeyYolu`) doğuyor — tek kaynak. */
export const ARAMA_ANAHTARLARI: Readonly<Record<string, readonly string[]>> = (() => {
  const m: Record<string, readonly string[]> = {};
  for (const a of YUZEY_ANAHTARLARI) {
    const y = YUZEYLER[a];
    m[yuzeyYolu(a)] = [a, y.sablon, y.soru, ...(YUZEY_EK[a] ?? [])];
    for (const b of y.bolumler) {
      // BÖLÜM KİMLİĞİ DE ANAHTARDIR: eski panonun çapa adları (`#mutabakat`,
      // `#failsub` …) operatörün kas hafızasında duruyor ve palet onları
      // tanımazsa yer imi bilen bir operatör aramada boş dönerdi.
      m[yuzeyYolu(a, b.kimlik)] = [b.kimlik, b.soru, y.baslik, ...(BOLUM_EK[b.kimlik] ?? [])];
    }
  }
  return m;
})();

/* ---------------------------------------------------------------------------
   DIŞ BELGELER — panonun DIŞINDAKİ okuma yüzeyleri
   Üçü de `meridian/api.py`de gerçek rota: `/runbook` (1097, oturum ister),
   `/workflow` (946), `/landing` (829). Uydurma bağ YOK.
   Hash yönlendirmesi bunları taşıyamaz (pano tek dosya, `#` sunucuya hiç gitmez)
   — bu yüzden satır "panodan ayrılır" diyor ve bunu SÖYLEYEREK yapıyor.
   --------------------------------------------------------------------------- */
export interface DisBelge {
  readonly kimlik: string;
  readonly ad: string;
  readonly yol: string;
  readonly aciklama: string;
}

export const DIS_BELGELER: readonly DisBelge[] = [
  {
    kimlik: "runbook",
    ad: "Runbook · teşhis belgesi",
    yol: "/runbook",
    aciklama: "alarm → belirti → teşhis → çözüm. Panodan ayrılır.",
  },
  {
    kimlik: "workflow",
    ad: "Karar hattı şeması",
    yol: "/workflow",
    aciklama: "günlük karar hattının uçtan uca akışı. Panodan ayrılır.",
  },
  {
    kimlik: "landing",
    ad: "Tanıtım sayfası",
    yol: "/landing",
    aciklama: "sistemin dışa dönük anlatımı. Panodan ayrılır.",
  },
];

export const BELGE_ANAHTARLARI: Readonly<Record<string, readonly string[]>> = {
  runbook: ["runbook", "teshis", "alarm", "bekci", "mekanizma", "ne yapmali", "olay"],
  workflow: ["workflow", "akis", "sema", "karar hatti", "diyagram", "boru hatti"],
  landing: ["landing", "tanitim", "anasayfa", "dis yuzey"],
};

/* ---------------------------------------------------------------------------
   SEMBOL ARAMASI — `/api/market` evren listesi
   --------------------------------------------------------------------------- */

export interface SembolHedefi {
  readonly yol: string;
  /** Satırın NEDEN oraya götürdüğü — ekranda aynen yazılır. */
  readonly gerekce: string;
}

/* HEDEF SATIRIN ÖLÇÜLEN HÂLİNDEN TÜRETİLİR, TAHMİNDEN DEĞİL.

   `plans_n` BİLEREK KULLANILMIYOR: `marketview.build()` onu `trade_plans.jsonl`in
   TAMAMINDAN sayıyor (marketview.py::build), yani "bir zamanlar planı olmuş"
   demek — "bugünkü aday tahtasında var" DEMEK DEĞİL. Onunla Adaylar'a götürseydik
   palet, tahtada bulunmayan bir kartı vaat ederdi. `position` ise `portfolio.json`
   pozisyonlarından geliyor ve BUGÜNÜN gerçeği: Portföy · Brifing'deki pozisyon
   tablosunda o satır GERÇEKTEN var.

   PİYASA BÖLÜMÜ İÇİN VAAT KÜÇÜK TUTULUYOR: `Piyasa.tsx` evreni ÖZETLER (tazelik
   dağılımı + en bayat 25 satır), 251 sembolü tek tek listelemez. "Sembolüne git"
   demek yalan olurdu; satır ne bulacağını önceden söylüyor. */
export function sembolHedefi(r: PiyasaSatiri): SembolHedefi {
  if (r.position) {
    return {
      yol: yuzeyYolu("finance", "brifing"),
      gerekce: "açık pozisyon — Portföy · Brifing'deki pozisyon tablosunda satırı var",
    };
  }
  if (r.retired) {
    return {
      yol: yuzeyYolu("infrastructure", "market"),
      gerekce: "EMEKLİ sembol — Piyasa bölümü (evren özeti; satır satır tablo değil)",
    };
  }
  return {
    yol: yuzeyYolu("infrastructure", "market"),
    gerekce: "izlenen evrende — Piyasa bölümü (evren özeti; satır satır tablo değil)",
  };
}

/** Sembol eşleştirmesi ÖN EK ÖNCELİKLİ ve bu bilinçli: ticker'lar 1-5 harf ve
 *  bulanık alt dizi araması burada gürültü üretir ("AAPL" yazan "A…A…P…L" taşıyan
 *  bir düzine sembol görmek istemez). Önce baştan eşleşenler, sonra içerenler. */
export function sembolAra(
  satirlar: readonly PiyasaSatiri[],
  sorgu: string,
  tavan = 8,
): readonly PiyasaSatiri[] {
  const q = katla(sorgu).trim();
  if (!q) return [];
  const onek: PiyasaSatiri[] = [];
  const iceren: PiyasaSatiri[] = [];
  for (const r of satirlar) {
    if (typeof r.ticker !== "string") continue; // tickersız satır bir sembol değildir
    const t = katla(r.ticker);
    if (t.startsWith(q)) onek.push(r);
    else if (t.includes(q)) iceren.push(r);
  }
  const sirala = (a: PiyasaSatiri, b: PiyasaSatiri) => (a.ticker ?? "").localeCompare(b.ticker ?? "");
  return [...onek.sort(sirala), ...iceren.sort(sirala)].slice(0, tavan);
}

/** Satırın ÖLÇÜLEN kapanışı — palet burada bir OKUMA da yapar (sembole gitmeden
 *  önce sayıyı görmek çoğu zaman zaten aranan şeydir). Ölçülemeyen değer sayı
 *  gibi görünmez: nedeni yazılır (UYDURMA YASAĞI). */
export function kapanisMetni(r: PiyasaSatiri): string {
  if (typeof r.close !== "number") return "kapanış ölçülemedi";
  return `${r.close.toFixed(2)} · ${r.last_date ?? "seansı yazılmamış"}`;
}
