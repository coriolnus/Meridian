/* ============================================================================
   HAFIZA · ARAMA — `GET /api/arama` GÖVDE TİPLERİ, SORGU KURULUMU VE DURUM AYRIMI
   ----------------------------------------------------------------------------
   DOSYA ADI `arama.ts` DEĞİL — VE BU ÖLÇÜLDÜ, TERCİH EDİLMEDİ (2026-09-08):
   görünüm gövdesi `Arama.tsx` ve macOS'un dosya sistemi harf-duyarsız. İki dosya
   YALNIZ BÜYÜK-KÜÇÜK HARFTE ayrıldığı sürece `import … from "./Arama"` ifadesi bu
   modüle çözülüyor ve `tsc` iki hatayla birden duruyordu (TS2305 "Arama diye bir
   dışa aktarım yok" + TS1149 "dosya adı yalnız harf büyüklüğünde farklı"). Linux'ta
   (CI, A1) aynı iki dosya sessizce ÇALIŞIRDI — yani hata yalnız bir tarafta görünen
   sınıftandı. Ad bu yüzden harf büyüklüğünden BAĞIMSIZ olarak ayrıştırıldı.
   ----------------------------------------------------------------------------
   BU DOSYA NEDEN `uctipleri.ts`TE DEĞİL: o dosyanın kapsamı adıyla `/api/hindsight*`
   vekilidir — bir dış servisin (Hindsight CP) aynen taşınan gövdeleri. `/api/arama`
   BAŞKA BİR KAYNAKTIR: deponun git-HEAD blob'larından kurulan sqlite-vec taban
   indeksi (EDG-2026-067 hükmü, 2026-09-06: melez değil TABAN). İkisini tek dosyaya
   koymak, "hafıza bankası" ile "belge indeksi" ayrımını tipte kaybetmek olurdu ve
   ekrandaki banka beyanı (aşağıda) o kaybın telafisi hâline gelirdi.

   ALAN ADLARI OKUNARAK YAZILDI, TAHMİNLE DEĞİL. Kaynak SEMBOL ADIYLA çapalanır,
   satır numarasıyla DEĞİL (codelaw çapa yasası):
     · zarfın ŞEKLİ → `meridian/arama.py::_zarf` (rota bunu aynen döndürür; şeklin sahibi
       ince HTTP sarmalayıcısı değil, sarmalanan modüldür)
     · zarf alanları ve kelepçeler → `meridian/arama.py::ara` · `::_zarf` ·
       `::KORPUS_ONEKLERI` · `::K_TAVANI` · `::ARAMA_KESIT_TAVANI` · `::MESGUL_NEDENI`
     · satır alanları (CLI'ın `--json` çıktısı) →
       `research/olcumler/edg067_hindsight_faz1/taban_indeks.py::en_yakin`

   ÜÇ DEĞİL DÖRT HÂL VAR — VE SIRALARI SÖZLEŞMENİN PARÇASI (Task 1 raporu §"Dört
   durum"): `mesgul: true` dalında `neden` DE doludur (`arama.MESGUL_NEDENI`), çünkü
   boş bir gerekçe dürüst olmazdı. Bu yüzden `mesgul` ÖNCE okunur; ters sırada meşgul
   hâli ekranda "Ölçülemedi" diye çizilir ve operatör başka bir aramanın koştuğunu
   ÖĞRENEMEZ — sistemin arızalandığını sanar. Sıra `durumCoz`ta bir kez yazılır ve
   çivilidir (`tests/test_arama_ui_v460.py::test_MESGUL_NEDENDEN_ONCE_dallanir`).

   ARIZA ZARFI 200'DÜR (Rol-1 hükmü K1, 2026-09-08): uç arızada da 200 + `neden`
   döner (hafıza recall vekilinin emsali) — pano kararmaz, gerekçe ekrana çıkar.
   ============================================================================ */

/** Uç yolu TEK yerde. Görünüm bunu `ARAMA_UC` adıyla alır, ikinci kez yazmaz. */
export const ARAMA_UC = "/api/arama";

/* ---------------------------------------------------------------------------
   GÖVDE TİPLERİ — ÜÇ DURUM TİPTE DE AYRI (`uctipleri.ts` sözleşmesi devralındı)
     `x?: T`        alan HİÇ gelmedi (eski gövde, kırpılmış yanıt)
     `x: T | null`  ölçüldü, sonuç yok
     `neden` dolu   ÖLÇÜLEMEDİ
   --------------------------------------------------------------------------- */

export interface AramaSatiri {
  /** Korpus içindeki yol (`docs/…`, `research/cards/…`, `ROADMAP.md%237`, günlük). */
  readonly dosya?: string | null;
  /** Kesitin içinde bulunduğu başlık — CLI'ın bölüm çapası. */
  readonly bolum?: string | null;
  /** HAM mesafe; yuvarlanmaz (`Recall.tsx`in ölçülmüş gerekçesi, ekranda tekrar edilir). */
  readonly mesafe?: number | null;
  /** Kesitin geldiği git blob'u — içerik-adresli künye. */
  readonly blob_sha?: string | null;
  /** Uçta `ARAMA_KESIT_TAVANI` (600) ile kırpılmış metin. */
  readonly kesit?: string | null;
  /** Kırpma BEYANI — bedel yasası: kırpıldıysa ekran bunu yazmak zorunda. */
  readonly kesit_kirpildi?: boolean | null;
  /** Kırpma ÖNCESİ (scrub sonrası) uzunluk; "+N karakter" bu ikisinden türer. */
  readonly metin_uzunluk?: number | null;
}

/**
 * İNDEKS KÜNYESİ — DEĞERLERİ DİZGEDİR (Task 1 raporu, bağlayıcı not).
 * `chunk_sayisi` bir sayı gibi görünür ama dizgedir; üzerinde `toLocaleString`
 * çağırmak sessizce `NaN` basardı. Eksik alan `null` gelir — CLI'ın "ölçülemedi"
 * beyanı bir değere çevrilmez.
 */
export interface AramaKunyesi {
  readonly uretim_ts?: string | null;
  readonly head_commit?: string | null;
  readonly chunk_sayisi?: string | null;
  readonly dosya_sayisi?: string | null;
}

export interface AramaZarfi {
  readonly sonuclar?: readonly AramaSatiri[] | null;
  readonly kunye?: AramaKunyesi | null;
  readonly n?: number | null;
  /** Korpus öneki süzgecinin DÜŞÜRDÜĞÜ satır sayısı — sessizce yutulmaz. */
  readonly korpus_disi_n?: number | null;
  readonly sure_s?: number | null;
  readonly mesgul?: boolean | null;
  readonly neden?: string | null;
}

/* ---------------------------------------------------------------------------
   OKUMA TALİMATI — SAYI TEK KAYNAKTAN
   ---------------------------------------------------------------------------
   İSABET ORANI ÖLÇÜLDÜ, TAHMİN EDİLMEDİ: EDG-2026-067 kıyas turu (2026-09-06,
   n=36 soru) `dosya@3` isabetini %55,6 ölçtü (`bolum@3` %27,8). Sayı BURADA bir
   kez yaşar; görünüm onu içe aktarır, ekrana ikinci kez YAZMAZ — ölçüm yenilendiği
   gün iki kopyadan biri sessizce bayatlardı (tek-kaynak yasası).

   CÜMLENİN KENDİSİ DE ÖLÇÜMÜN PARÇASI: üçte biri kaçıran bir listeyi "cevap" diye
   sunmak, ölçülmemiş bir güveni ölçülmüş gibi göstermek olurdu.
   --------------------------------------------------------------------------- */
export const ISABET_BEYANI =
  "İlk üç sonuçtan birinin doğru dosya olma oranı ölçülmüş %55,6 (EDG-2026-067 kıyası, " +
  "2026-09-06, n=36) — bu bir CEVAP değil ADAY LİSTESİdir.";

/* ---------------------------------------------------------------------------
   KUTUNUN KAPALI LİSTELERİ
   --------------------------------------------------------------------------- */

/**
 * `k` — PANO 20 SUNMAZ (Rol-1 hükmü K6, 2026-09-08).
 *
 * API tavanı `arama.K_TAVANI = 20` (sohbetle ortak sabit) ve o sabit BURAYA
 * KOPYALANMAZ: pano kendi dar listesini sunar, kelepçe sunucuda kalır. Darlığın
 * gerekçesi ölçülü — her sorgu A1'in 4 OCPU'sunda yeni bir ONNX oturumu kurar ve
 * CLI `k×4` aday çekip süzer; `k` büyüdükçe bedel doğrusal büyür, isabet ise
 * (ölçülen `@3` penceresinde) büyümez.
 */
export const K_SECENEKLERI = [5, 10] as const;

export type KSecenegi = (typeof K_SECENEKLERI)[number];

export const VARSAYILAN_K: KSecenegi = 5;

/**
 * `--dosya` öneki — SUNUCUNUN BEYAZ LİSTESİNİN ALT KÜMESİ.
 *
 * Tek kaynak `meridian/arama.py::KORPUS_ONEKLERI`; buraya İKİNCİ bir liste yazmak
 * yerine onun ALT KÜMESİ sunuluyor ve ayrışma çivilendi
 * (`tests/test_arama_ui_v460.py::test_dosya_secenekleri_KORPUS_ONEKLERININ_ALT_KUMESI`).
 * Liste dışı bir önek uçta 400 olur — düğme çalışır görünüp reddedilirdi.
 *
 * HAM `ROADMAP.md` BİLEREK YOK: indekste yalnız `ROADMAP.md%237` kesiti var
 * (`manifest_uret.py` korpusu), yani çıplak `ROADMAP.md` seçeneği hiçbir zaman
 * eşleşmezdi ve "yol haritasında sonuç yok" diye okunurdu.
 */
export const DOSYA_SECENEKLERI = [
  { deger: "", etiket: "hepsi" },
  { deger: "docs/", etiket: "docs/" },
  { deger: "research/cards/", etiket: "research/cards/" },
  { deger: "MERIDIAN_ENGINEERING_LOG.md", etiket: "mühendislik günlüğü" },
] as const;

/* ---------------------------------------------------------------------------
   SORGU ADRESİ — TEK YERDE, KAÇIRILMIŞ
   `URLSearchParams` elle birleştirmenin yerine geçiyor: soru operatörün serbest
   metnidir ve `&`/`#`/boşluk içerebilir. Elle kurulan bir sorgu dizgesi o karakterleri
   sessizce ikinci bir parametreye çevirirdi.
   --------------------------------------------------------------------------- */
export function aramaYolu(soru: string, k: number, dosya: string): string {
  const p = new URLSearchParams({ soru: soru.trim(), k: String(k) });
  // BOŞ ÖNEK HİÇ GÖNDERİLMEZ: uç `dosya=` parametresini beyaz listeden geçiriyor ve
  // boş dizge "süzgeç yok" ile "geçersiz önek" arasında bir ayrım doğurmamalı.
  if (dosya !== "") p.set("dosya", dosya);
  return `${ARAMA_UC}?${p.toString()}`;
}

/* ---------------------------------------------------------------------------
   DÖRT HÂL — TEK YERDE ÇÖZÜLÜR
   --------------------------------------------------------------------------- */

export type AramaDurumu =
  | { readonly tur: "mesgul"; readonly neden: string }
  | { readonly tur: "olculemedi"; readonly neden: string }
  | { readonly tur: "bos" }
  | { readonly tur: "dolu"; readonly satirlar: readonly AramaSatiri[] };

/**
 * SIRA SÖZLEŞMEDİR (dosya başlığındaki gerekçe): `mesgul` ÖNCE, `neden` SONRA.
 *
 * `sonuclar` dizi DEĞİLSE ve `neden` de boşsa üçüncü bir hâl doğar — ölçüm denendi,
 * gövde gelmedi. Onu `bos` saymak "ölçtük, hiçbir şey yok" demek olurdu ve bu bir
 * yalandır (`Recall.tsx`in kurucu dersi: "ölçülemedi" ile "henüz sorulmadı"/"boş"
 * tek `null`da birleşemez).
 */
export function durumCoz(zarf: AramaZarfi): AramaDurumu {
  if (zarf.mesgul === true) {
    return {
      tur: "mesgul",
      neden:
        typeof zarf.neden === "string" && zarf.neden !== ""
          ? zarf.neden
          : "başka bir arama koşuyor (uç gerekçe metnini taşımadı)",
    };
  }
  if (typeof zarf.neden === "string" && zarf.neden !== "") {
    return { tur: "olculemedi", neden: zarf.neden };
  }
  if (!Array.isArray(zarf.sonuclar)) {
    return {
      tur: "olculemedi",
      neden:
        zarf.sonuclar === null
          ? "uç sonuç listesini döndürmedi ve gerekçe de taşımadı"
          : "sonuç listesi tanınmayan bir biçimde geldi — şema sürüklenmiş olabilir",
    };
  }
  return zarf.sonuclar.length === 0
    ? { tur: "bos" }
    : { tur: "dolu", satirlar: zarf.sonuclar };
}

/**
 * KIRPMA BEDELİNİN CÜMLESİ — kaç karakter GÖRÜNMÜYOR.
 *
 * `null` = kırpma yok ya da ölçülemiyor. Uzunluk gelmemişse SAYI UYDURULMAZ: bayrak
 * doluysa görünüm bayrağı yine de yazar, ama "+N" yerine sayısız bir beyanla.
 */
export function kirpmaFarki(satir: AramaSatiri): number | null {
  if (satir.kesit_kirpildi !== true) return null;
  const tam = satir.metin_uzunluk;
  const gorunen = typeof satir.kesit === "string" ? satir.kesit.length : null;
  if (typeof tam !== "number" || gorunen === null) return null;
  const fark = tam - gorunen;
  return fark > 0 ? fark : null;
}

/* ---------------------------------------------------------------------------
   ⌘K DEVRİ: PALET → GÖRÜNÜM
   ---------------------------------------------------------------------------
   `sohbet.ts::sohbetIstegiBirak` EMSALİ BİREBİR ve aynı iki gerekçeyle:

   (1) NEDEN ROTA SORGUSU DEĞİL — operatör zaten arama adresindeyken `push` aynı
       hash'i yazar, `hashchange` ATEŞLENMEZ ve görünüm isteği hiç görmez; ⌘K ikinci
       kez sessiz kalırdı. Ayrıca `gorunumler.ts::sekmeliYol` bugün TEK sorgu anahtarı
       biliyor (`sekme`) ve ikincisini sessizce düşürürdü (ölçülmüş sınır). Üstüne,
       serbest metni adres çubuğuna yazmak geçmişte ve yer imlerinde kalıcı bir kopya
       bırakırdı.

   (2) TEK SEFERLİK — tüketilmiş istek ikinci kez uygulanırsa kutu her yeniden çizimde
       kendi kendine dolar.

   VE SORGU ATEŞLENMEZ: palet GÖTÜRÜR, göndermez ("hızlı erişim ≠ icra",
   `search-dialog.tsx` hükmü). Burada ek bir gerekçe daha var — her tuş vuruşunda bir
   ONNX süreci doğurmamak.
   --------------------------------------------------------------------------- */

export interface AramaIstegi {
  /** Palete yazılmış serbest metin; yoksa `null` (yalnız odak isteği). */
  readonly taslak: string | null;
}

let bekleyenIstek: AramaIstegi | null = null;
const aboneler = new Set<() => void>();

export function aramaIstegiBirak(taslak: string | null): void {
  bekleyenIstek = { taslak: taslak === null || taslak.trim() === "" ? null : taslak.trim() };
  for (const f of aboneler) f();
}

/** İsteği ALIR ve KUTUYU BOŞALTIR. İkinci okuma `null` döner. */
export function aramaIstegiAl(): AramaIstegi | null {
  const i = bekleyenIstek;
  bekleyenIstek = null;
  return i;
}

/** Abonelik; dönüş değeri aboneliği bırakır (React efekt temizliği). */
export function aramaIstegiAbone(f: () => void): () => void {
  aboneler.add(f);
  return () => {
    aboneler.delete(f);
  };
}
