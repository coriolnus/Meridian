/* ============================================================================
   PANO SOHBETİNİN GRAMERİ — saf okuma/biçim mantığı (TSK-012 dalga-B, B2)
   ----------------------------------------------------------------------------
   BU DOSYA VERİ KATMANI DEĞİLDİR ve React'e DOKUNMAZ. Burada duran şey, `/api/sohbet`
   gövdelerinin okunması ve ekrana çıkacak cümlelerin kurulmasıdır — hepsi SAF, yani
   `node` ile gerçekten koşulabiliyor (`tests/civiler/sohbet_civileri.mjs`,
   `tests/test_pano_sohbet_v443.py`). `gramer.ts`in var olma sebebiyle aynı: kaynak
   metninde kimlik arayan bir çivi, ifadeyi bozan ama adı koruyan mutasyonda ISIRMAZ.

   ALAN ADLARI UÇTAN ÖLÇÜLDÜ, TAHMİN EDİLMEDİ (`meridian/sohbet.py::DEFTER_ALANLARI`
   ve `api.py::api_sohbet` / `api_sohbet_gecmis` / `api_sohbet_kota` okundu):
     satır  → ts · oturum · mesaj · cevap · turlar · kaynaklar · model · sure_s ·
              jeton_giris · jeton_cikis · kota_bugun · oneri_id · sema_disi_n · llm_dustu
     geçmiş → {gecmis[], kunye, kota, oturum}
     kota   → {bugun|null, kalan|null, tavan, defter_n, neden|null}

   UYDURMA YASAĞI BU DOSYANIN OMURGASI: ölçülmeyen her alan `null` kalır ve ekrana
   NEDENİYLE çıkar. Üç yer bunu özellikle taşır:
     · `kota_bugun: null` "bugün 0 çağrı" DEĞİLDİR — telemetri halkası bugünün içinde
       dolmuşsa sayım bir ALT SINIRDIR ve uç bunu `neden` ile söyler (sohbet.py::kota_durumu).
     · `llm_dustu` bir ARIZA değil bir DURUMDUR: zincirin hiçbir ayağı cevap vermediğinde
       cevap ÜRETİLMEZ ve ekran bunu hata kılığına sokmaz.
     · `kaynaklar: []` görünür bir beyandır — o liste EDG-2026-086'nın uydurma sayımının
       PAYDASIDIR; sessizce boş bırakmak, atıfsız bir cevabı atıflı gibi göstermek olurdu.
   ============================================================================ */

/* ---- DEFTER SATIRI -------------------------------------------------------- */

/** Cevabın dayandığı araç çıktısı: hangi araç, hangi anahtar. `anahtar` uçta boş
 *  dizge olabilir (araç anahtar üretemedi) — o hâl `null` taşınır, uydurulmaz. */
export interface SohbetKaynagi {
  readonly arac: string;
  readonly anahtar: string | null;
}

/** `sohbet.jsonl` satırının panonun okuduğu kesiti. Ham satır ne taşıyorsa o;
 *  ölçülmeyen alan `null`. `turN` ham `turlar` dizisinin UZUNLUĞUDUR (kaç model
 *  turu döndü) — dizinin kendisi ekranda çizilmiyor, sayısı künyede duruyor. */
export interface SohbetSatiri {
  readonly ts: string | null;
  readonly oturum: string | null;
  readonly mesaj: string;
  readonly cevap: string;
  readonly kaynaklar: readonly SohbetKaynagi[];
  readonly model: string | null;
  readonly sureS: number | null;
  readonly jetonGiris: number | null;
  readonly jetonCikis: number | null;
  readonly kotaBugun: number | null;
  readonly oneriId: string | null;
  readonly semaDisiN: number | null;
  readonly llmDustu: boolean | null;
  readonly turN: number;
}

function nesne(x: unknown): Record<string, unknown> | null {
  return x !== null && typeof x === "object" && !Array.isArray(x) ? (x as Record<string, unknown>) : null;
}

function metin(x: unknown): string | null {
  return typeof x === "string" && x !== "" ? x : null;
}

function sayi(x: unknown): number | null {
  return typeof x === "number" && Number.isFinite(x) ? x : null;
}

/** Ham defter satırı → okunmuş satır. Nesne değilse `null`: boş bir satır
 *  uydurmak, defterde olmayan bir konuşmayı ekrana koymak olurdu. */
export function satirOku(x: unknown): SohbetSatiri | null {
  const o = nesne(x);
  if (o === null) return null;
  const kaynaklar: SohbetKaynagi[] = [];
  if (Array.isArray(o["kaynaklar"])) {
    for (const k of o["kaynaklar"]) {
      const ko = nesne(k);
      const arac = ko === null ? null : metin(ko["arac"]);
      // ARAÇ ADI OLMAYAN ÖĞE KAYNAK DEĞİLDİR: o liste uydurma sayımının paydası
      // (`sohbet.py::AracReddi` şerhi) — anahtarsız bir kaydı saymak paydayı şişirirdi.
      if (arac === null) continue;
      kaynaklar.push({ arac, anahtar: ko === null ? null : metin(ko["anahtar"]) });
    }
  }
  return {
    ts: metin(o["ts"]),
    oturum: metin(o["oturum"]),
    mesaj: typeof o["mesaj"] === "string" ? o["mesaj"] : "",
    cevap: typeof o["cevap"] === "string" ? o["cevap"] : "",
    kaynaklar,
    model: metin(o["model"]),
    sureS: sayi(o["sure_s"]),
    jetonGiris: sayi(o["jeton_giris"]),
    jetonCikis: sayi(o["jeton_cikis"]),
    kotaBugun: sayi(o["kota_bugun"]),
    oneriId: metin(o["oneri_id"]),
    semaDisiN: sayi(o["sema_disi_n"]),
    llmDustu: typeof o["llm_dustu"] === "boolean" ? o["llm_dustu"] : null,
    turN: Array.isArray(o["turlar"]) ? o["turlar"].length : 0,
  };
}

export interface GecmisOkumasi {
  readonly satirlar: readonly SohbetSatiri[];
  /** Geçmiş okunamadıysa NEDENİ. `null` iken liste güvenilir — boş liste ÖLÇÜLMÜŞ boşluktur. */
  readonly neden: string | null;
}

/**
 * `GET /api/sohbet` gövdesi → geçmiş. ÜÇ HÂL AYRI: okunamadı (hata) · henüz okunmadı ·
 * okundu ve boş. Üçünü tek "boş liste"ye indirmek, hiç konuşulmamış gibi göstermek olurdu.
 */
export function gecmisOku(govde: unknown, hata: string | null): GecmisOkumasi {
  if (hata !== null) return { satirlar: [], neden: hata };
  const o = nesne(govde);
  if (o === null) return { satirlar: [], neden: "/api/sohbet henüz okunmadı — geçmiş ölçülmedi" };
  const ham = o["gecmis"];
  if (!Array.isArray(ham)) {
    return {
      satirlar: [],
      neden: "/api/sohbet `gecmis` alanını döndürmedi — boş geçmiş DEĞİL, ölçülemedi",
    };
  }
  const satirlar: SohbetSatiri[] = [];
  for (const s of ham) {
    const okunan = satirOku(s);
    if (okunan !== null) satirlar.push(okunan);
  }
  return { satirlar, neden: null };
}

/* ---- KOTA ---------------------------------------------------------------- */

export interface SohbetKotasi {
  /** Bugünkü çağrı sayısı. `null` = ÖLÇÜLEMEDİ (0 DEĞİL) — `neden` dolu olur. */
  readonly bugun: number | null;
  readonly kalan: number | null;
  readonly tavan: number | null;
  readonly neden: string | null;
  /** Sunucunun KENDİ hükmü: bugün model çağrılmayacak mı (`sohbet.py::_kota_cevabi` ile
   *  AYNI karar — K-1). `null` = uç bu alanı hiç YAZMADI (B1 öncesi sürüm); 0/`false` ile
   *  KARIŞTIRILMAZ, aksi hâlde "ölçüldü, dolu değil" yalanı olurdu. */
  readonly dolu: boolean | null;
}

export function kotaOku(x: unknown): SohbetKotasi | null {
  const o = nesne(x);
  if (o === null) return null;
  return {
    bugun: sayi(o["bugun"]),
    kalan: sayi(o["kalan"]),
    tavan: sayi(o["tavan"]),
    neden: metin(o["neden"]),
    dolu: typeof o["dolu"] === "boolean" ? o["dolu"] : null,
  };
}

export interface KotaGorunumu {
  readonly metin: string;
  /** Rozet uyarı rengine geçer mi: kota dolu ya da ÖLÇÜLEMEDİ. İkisi de "model çağrılmaz" demek. */
  readonly uyari: boolean;
  /** `true` iken giriş kutusu + gönder düğmesi KAPALI (K-1, `gonderimKapaliMi` ile birlikte
   *  TEK kapı). Kaynağı YALNIZ backend'in `dolu` alanı — eşik burada YENİDEN HESAPLANMAZ
   *  (tek-kaynak yasası, `sohbet.py::_kota_cevabi` ile aynı hüküm). Uç bu alanı yazmıyorsa
   *  (`dolu: null`, B1 öncesi sürüm) `false` döner: giriş AÇIK kalır, geriye dönük davranış
   *  korunur — `uyari`nin metin/renk hesabına bilerek BAĞLANMAZ, ikisi ayrı sinyaldir.
   */
  readonly dolu: boolean;
  /** `dolu` iken şeritte gösterilecek beyan; değilse `null`. Sayılar `kota`nın ÖLÇÜLEN
   *  alanlarından (`bugun`/`tavan`) — ölçülemeyen kısım UYDURULMAZ, kendi nedenini taşır. */
  readonly kapaliBeyan: string | null;
}

/**
 * Kota rozetinin cümlesi. SIFIR YAZILMAZ: ölçülemeyen kota "0/120" diye çizilseydi
 * operatör "bugün hiç sormamışım" diye okurdu — oysa ölçülemeyen kota DOLMAMIŞ
 * sayılmaz ve sohbet model çağırmaz (sohbet.py::_kota_cevabi).
 */
export function kotaMetni(kota: SohbetKotasi | null, hata: string | null): KotaGorunumu {
  if (hata !== null) return { metin: `kota ölçülemedi — ${hata}`, uyari: true, dolu: false, kapaliBeyan: null };
  if (kota === null) return { metin: "kota henüz okunmadı", uyari: false, dolu: false, kapaliBeyan: null };

  const dolu = kota.dolu === true;
  const kapaliBeyan = !dolu
    ? null
    : kota.bugun === null
      ? `kota ÖLÇÜLEMEDİ — ${kota.neden ?? "uç neden yazmadı"} · sohbet bugün model çağırmıyor`
      : `kota dolu (${kota.bugun}/${kota.tavan ?? "tavan ölçülemedi"}) — sohbet bugün model çağırmıyor`;

  if (kota.bugun === null) {
    return {
      metin: `kota ÖLÇÜLEMEDİ — ${kota.neden ?? "uç neden yazmadı"}`,
      uyari: true,
      dolu,
      kapaliBeyan,
    };
  }
  if (kota.tavan === null) {
    return { metin: `bugün ${kota.bugun} çağrı · tavan ölçülemedi`, uyari: false, dolu, kapaliBeyan };
  }
  const kalan = kota.kalan === null ? "kalan ölçülemedi" : `kalan ${kota.kalan}`;
  return {
    metin: `bugün ${kota.bugun}/${kota.tavan} · ${kalan}`,
    uyari: kota.bugun >= kota.tavan,
    dolu,
    kapaliBeyan,
  };
}

/**
 * TEK KAPI (K-1): giriş kutusunun `disabled`ı, gönder düğmesinin `disabled`ı VE
 * `useSohbet.gonder`in kendisi AYNI ifadeyi okur. Ayrı ayrı yazılsaydı biri unutulduğunda
 * "kota dolu ama kutu açık" sınıfı geri gelirdi (bu fonksiyonun var olma sebebi).
 */
export function gonderimKapaliMi(taslak: string, gonderiliyor: boolean, kotaDolu: boolean): boolean {
  return gonderiliyor || taslak.trim() === "" || kotaDolu;
}

/* ---- YANITIN DURUMU ------------------------------------------------------ */

/** Üç hâl, üç ayrı görünüm. İkisi HATA DEĞİLDİR: uç 200 döner ve satırı deftere yazar. */
export type YanitDurumu = "cevap" | "model-yok" | "model-cagrilmadi";

export function yanitDurumu(s: SohbetSatiri): YanitDurumu {
  if (s.llmDustu === true) return "model-yok";
  // MODEL ÇAĞRILMAMIŞ HÂL ÖLÇÜLEN İKİ ALANDAN OKUNUR (künye + tur sayısı), cevabın
  // METNİNDEN değil: metne bakmak, ucun cümlesini ayrıştırmak olurdu ve o cümle
  // değiştiği gün pano sessizce yanlış durum çizerdi.
  if (s.model === null && s.turN === 0) return "model-cagrilmadi";
  return "cevap";
}

const DURUM_BEYANI: Readonly<Record<YanitDurumu, string | null>> = {
  cevap: null,
  "model-yok":
    "MODEL YOK — zincirin hiçbir ayağı cevap vermedi. Cevap ÜRETİLMEDİ; uydurulmadı. " +
    "Sebepler ucun cümlesinde (aşağıda) duruyor.",
  "model-cagrilmadi":
    "MODEL ÇAĞRILMADI — bu turda hiç model turu yok (kota kapısı). Gerekçe ucun kendi " +
    "cümlesinde: ölçülemeyen kota dolmamış sayılmaz.",
};

export function durumBeyani(d: YanitDurumu): string | null {
  return DURUM_BEYANI[d];
}

/* ---- KÜNYE CÜMLELERİ ----------------------------------------------------- */

export function kaynakEtiketi(k: SohbetKaynagi): string {
  return k.anahtar === null ? `${k.arac} · anahtar yok` : `${k.arac} · ${k.anahtar}`;
}

/** Atıfsız cevabın GÖRÜNÜR beyanı; atıf varsa `null` (yazacak bir şey yok). */
export function kaynakBeyani(s: SohbetSatiri): string | null {
  if (s.kaynaklar.length > 0) return null;
  return "kaynak atfı yok — bu cevap hiçbir araç çıktısına dayanmıyor";
}

export function modelMetni(s: SohbetSatiri): string {
  return s.model ?? "model künyesi yok — uç `model` yazmadı (ayak hiç dönmemiş olabilir)";
}

/** ONDALIK AYRACI ELDE ÇEVRİLİYOR, `toLocaleString` ile DEĞİL: çivi node'da koşuyor
 *  ve yerel ayar orada tarayıcınınkiyle aynı olmayabilir — biçim ölçülebilir kalmalı. */
export function sureMetni(sn: number | null): string {
  if (sn === null) return "süre ölçülemedi";
  return `${sn.toFixed(1).replace(".", ",")} sn`;
}

export function jetonMetni(giris: number | null, cikis: number | null): string {
  if (giris === null && cikis === null) {
    return "jeton ölçülemedi — hiçbir ayak `usage` bildirmedi";
  }
  const g = giris === null ? "ölçülemedi" : String(giris);
  const c = cikis === null ? "ölçülemedi" : String(cikis);
  return `giriş ${g} · çıkış ${c}`;
}

/* ---- GÖNDERİM HATASI: HER KOD KENDİ CÜMLESİ ------------------------------ */

export interface GonderimHatasi {
  readonly baslik: string;
  readonly govde: string;
  /** 401 AYRI bir hâl: çaresi yeniden giriş, tekrar denemek değil. */
  readonly oturumDustu: boolean;
}

/**
 * "Bir şeyler ters gitti" YASAK (`kuyruk/onayEylem.ts::hataMetni` ile aynı disiplin).
 * ÖNEMLİ AYRIM `kod: 0`DA: yanıt hiç gelmediyse mesajın deftere YAZILMADIĞI
 * söylenemez — sohbet turu dakikalar sürebiliyor (`SOHBET_TIMEOUT_S`, varsayılan 180 s)
 * ve kopan şey yanıt olabilir. Körlemesine tekrar göndermek kotayı ikinci kez yakar.
 */
export function gonderimHatasi(kod: number, detay: string | null): GonderimHatasi {
  if (kod === 0) {
    return {
      baslik: "Ağ hatası — yanıt HİÇ gelmedi",
      govde:
        `POST /api/sohbet bir HTTP yanıtı üretmedi (${detay ?? "tarayıcı bir sebep yazmadı"}). ` +
        "Bu 'mesaj gitmedi' DEMEK DEĞİLDİR: tur sunucuda sürüyor ve dakikalar alabilir. " +
        "Geçmişi yeniden yükle; cevabın orada olup olmadığına BAK, körlemesine tekrar gönderme.",
      oturumDustu: false,
    };
  }
  if (kod === 401) {
    return {
      baslik: "Oturum düştü (401)",
      govde:
        "Uç yetkiyi gövdeyi okumadan önce sınıyor (`_auth`) — mesaj GÖNDERİLMEDİ, deftere " +
        "hiçbir satır yazılmadı. Çare: panodan çık, yeniden gir.",
      oturumDustu: true,
    };
  }
  if (kod === 400) {
    return {
      baslik: "Uç mesajı REDDETTİ (400)",
      govde:
        (detay ?? "uç gerekçe yazmadı") +
        " · Boş mesaj bilerek reddediliyor: cevaplanacak soru yokken model çağırmak kotayı " +
        "harcar ve deftere ölçüm değeri olmayan bir satır yazardı.",
      oturumDustu: false,
    };
  }
  if (kod >= 500) {
    return {
      baslik: `Sunucu hatası (${kod})`,
      govde:
        `POST /api/sohbet ${kod} döndü${detay ? ` — ${detay}` : " ve gövdesinde okunabilir bir gerekçe yoktu"}. ` +
        "Bu hâlde satırın deftere yazılıp yazılmadığı pano tarafından BİLİNEMEZ; geçmişi yeniden yükle.",
      oturumDustu: false,
    };
  }
  return {
    baslik: `Beklenmeyen durum kodu (${kod})`,
    govde:
      `POST /api/sohbet ${kod} döndü${detay ? ` — ${detay}` : " ve gövdesinde gerekçe yoktu"}. ` +
      "Bu panonun tanıdığı kodlardan (200/400/401/5xx) hiçbiri değil; sonucu VARSAYMA, geçmişi kontrol et.",
    oturumDustu: false,
  };
}

/* ---- OTURUM KİMLİĞİ ------------------------------------------------------ */

const OTURUM_ONEKI = "pano-";

/**
 * GÜN BAŞINA TEK OTURUM — ve bu kartın ölçümüne bağlı bir karardır, süs değil:
 * EDG-2026-086 SEANS sayıyor (≥10 seans penceresi) ve her mesaja yeni kimlik üretmek
 * o sayımı anlamsız kılardı. Sunucunun kimliksiz varsayılanı da aynı desende
 * (`sohbet.py::gunun_oturumu` → `pano-<gün>`); buradaki ek soneki tarayıcıyı ayırır,
 * yani iki ayrı pano aynı günde aynı seansa yazmaz.
 *
 * DÜNÜN KİMLİĞİ TAŞINMAZ: `localStorage` kalıcıdır ve taşısaydık defterde tek bir
 * devasa oturum görünürdü.
 */
export function oturumSec(kayitli: string | null, bugun: string, rastgele: () => number): string {
  const onek = `${OTURUM_ONEKI}${bugun}-`;
  if (kayitli !== null && kayitli.startsWith(onek) && kayitli.length > onek.length) return kayitli;
  const ek = Math.floor(rastgele() * 0xffff)
    .toString(16)
    .padStart(4, "0");
  return `${onek}${ek}`;
}

/* ---- ⌘K DEVRİ: PALET → PANEL --------------------------------------------- */

/**
 * TEK SEFERLİK İSTEK KUTUSU. Palet "Ajan'a sor…" komutunu seçtiğinde iki şey ister:
 * sohbet girişine ODAK, ve yazılmış serbest metin varsa onun TAŞINMASI.
 *
 * NEDEN ROTA SORGUSU DEĞİL (ölçüldü): adres zaten sohbet panelindeyken `push` aynı
 * hash'i yazar, `hashchange` ATEŞLENMEZ ve panel isteği hiç görmez — ⌘K ikinci kez
 * sessiz kalırdı. Ayrıca operatörün serbest metnini adres çubuğuna yazmak, geçmişte
 * ve yer imlerinde kalıcı bir kopya bırakırdı.
 *
 * TEK SEFERLİK, ÇÜNKÜ TÜKETİLMİŞ İSTEK İKİNCİ KEZ UYGULANIRSA kutu kendi kendine
 * dolar: panel her yeniden çizimde aynı taslağı geri yazardı.
 */
export interface SohbetIstegi {
  /** Palete yazılmış serbest metin; yoksa `null` (yalnız odak isteği). */
  readonly taslak: string | null;
}

let bekleyenIstek: SohbetIstegi | null = null;
const aboneler = new Set<() => void>();

export function sohbetIstegiBirak(taslak: string | null): void {
  bekleyenIstek = { taslak: taslak === null || taslak.trim() === "" ? null : taslak.trim() };
  for (const f of aboneler) f();
}

/** İsteği ALIR ve KUTUYU BOŞALTIR. İkinci okuma `null` döner. */
export function sohbetIstegiAl(): SohbetIstegi | null {
  const i = bekleyenIstek;
  bekleyenIstek = null;
  return i;
}

/** Abonelik; dönüş değeri aboneliği bırakır (React efekt temizliği). */
export function sohbetIstegiAbone(f: () => void): () => void {
  aboneler.add(f);
  return () => {
    aboneler.delete(f);
  };
}
