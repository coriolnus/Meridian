/* ============================================================================
   FİLO GÖVDE OKUYUCUSU — `GET /api/ajanlar` (2026-08-31)
   ----------------------------------------------------------------------------
   Alan adları `meridian/api.py::api_ajanlar` + `_ajan_oturumlar` +
   `_ajan_teslimleri` OKUNARAK alındı (çapa SEMBOL, satır DEĞİL: satır kayar).

   BU DOSYANIN TEK İŞİ BİR AYRIMI KORUMAK: `null` ≠ `[]`.
   Ucun kendi şerhi bunu şöyle yazıyor — "`oturumlar: []` 'bu ajanla hiç
   konuşulmamış' DER, bir İDDİADIR; `oturumlar: null` + `neden` ise 'defteri
   okuyamadım' der". Panonun bu ucu bozmasının en kolay yolu ikisini tek boş
   duruma indirgemektir: `?? []` yazmak sözdizimsel olarak bedavadır ve ekranda
   ölçülmemiş bir sessizliği ölçülmüş bir sessizlik gibi gösterir. Bu yüzden
   liste okuyucusu `dizi()`dir (dizi DEĞİLSE `null`), `ortak.tsx`in `dizi()`si
   DEĞİL — o boş dizi döndürür ve tam olarak bu ayrımı siler.

   SIRA UÇTAN GELİR, BURADA DEĞİŞTİRİLMEZ (plan sözleşmesi T1'DEN MİRAS):
     · `oturumlar`  YENİDEN → ESKİYE
     · `mesajlar`   ESKİDEN → YENİYE (okuma akışı)
     · `teslimler`  YENİDEN → ESKİYE
   Bu dosya hiçbir `sort`/`reverse` çağırmaz. Görsel katman bir terslemeye
   ihtiyaç duyarsa onu BEYAN EDEREK yapar (`Filo.tsx::OturumBasligi` — model
   değişimini ESKİ komşuyla karşılaştırır ve bunu şerhinde söyler).

   SKALER `null` ANLAMLARI birbirinden de ayrıdır ve tipte tek "boş"a düşmezler:
     · `model`         — oturum kaydı yok (ya da modeli yazılmamış)
     · `sonOturumTs`   — hiç oturum görülmedi
     · `ts` + `tsHam`  — damga ÇEVRİLEMEDİ; ham değer `tsHam`ta KORUNUR ve
                         yüzey HAM'ı gösterir (uydurulmuş bir tarih yerine)
     · `damgalanan` / `detail` / `olculemeyen` — üretici o alanı olaya BASMADI

   KIRPMALAR KENDİLERİNİ SÖYLER, üçü de taşınır: mesaj gövdesi
   (`kirpildi`+`hamUzunluk`) · oturum sayısı (`suzgec.limitIstenen`) · teslim
   listesi (`teslimKirpildi`+`teslimToplam`, tavan `kaynak.teslimTavani`).
   ============================================================================ */
import { dizi, mantik, metin, nesne, sayi } from "../kanban/oku";

/* ---- GÖVDE OKUYUCUSU: BOŞ METİN BİR DEĞERDİR ----------------------------- */

/** Mesaj gövdesi için ham dizge okuyucusu. `metin()`ten AYRI bir sözleşmesi var
 *  ve ayrım bilinçli: `metin()` boş/boşluk dizgesini `null` sayar (ölçülemedi),
 *  oysa BOŞ BİR MESAJ GÖVDESİ ölçülmüş bir değerdir — defterde gerçekten boş bir
 *  `content` satırı olabilir. İkisini birleştirmek "boş mesaj" ile "mesaj
 *  okunamadı"yı aynı kutuya koyardı. */
function govde(x: unknown): string | null {
  return typeof x === "string" ? x : null;
}

/* ---- ŞEKİLLER ------------------------------------------------------------ */

export interface FiloMesaji {
  readonly rol: string | null;
  readonly ts: string | null;
  /** Damga çevrilemediyse defterde YAZAN değer. Başarıda `null`. */
  readonly tsHam: string | null;
  readonly metin: string | null;
  readonly kirpildi: boolean | null;
  readonly hamUzunluk: number | null;
}

export interface FiloOturumu {
  readonly id: string | null;
  readonly ts: string | null;
  readonly tsHam: string | null;
  readonly model: string | null;
  /** Uç her oturumda liste basar; dizi DEĞİLSE `null` (şekil bozulmuş). */
  readonly mesajlar: readonly FiloMesaji[] | null;
}

export interface FiloTeslimi {
  readonly ts: string | null;
  readonly olay: string | null;
  /** Olayda alan YOKSA `null` — boş liste "hiçbir şey damgalanmadı" derdi. */
  readonly damgalanan: readonly string[] | null;
  readonly detay: string | null;
  /** `ops/sef_brifingi.py`nin bastığı "hangi kaynaklar ölçülemedi" listesi. */
  readonly olculemeyen: readonly string[] | null;
}

export interface FiloAjani {
  /** KİMLİK `(ad, tur)` ÇİFTİDİR — bir profil `hermes` adını taşırsa `tur` ayırır. */
  readonly ad: string | null;
  readonly tur: string | null;
  readonly anahtar: string;
  readonly model: string | null;
  readonly sonOturumTs: string | null;
  readonly oturumlar: readonly FiloOturumu[] | null;
  readonly teslimler: readonly FiloTeslimi[] | null;
  readonly teslimToplam: number | null;
  readonly teslimKirpildi: boolean | null;
  /** `"ok"` | `"olculemedi"` — YALNIZ oturum kaynağı hakkında. `teslimler` AYRI
   *  bir kaynaktan gelir ve `olculemedi` bir ajanda bile ölçülmüş olabilir. */
  readonly durum: string | null;
  readonly neden: string | null;
}

export interface FiloKaynagi {
  readonly profilKoku: string | null;
  readonly anaBeyin: string | null;
  readonly botKoku: string | null;
  /** `null` = roster ÖLÇÜLEMEDİ (boş liste "bot yok" derdi). */
  readonly botlar: readonly string[] | null;
  readonly events: string | null;
  readonly eventsNeden: string | null;
  readonly teslimTavani: number | null;
  readonly eslesmeyenToplam: number | null;
}

export interface FiloSuzgeci {
  readonly limit: number | null;
  readonly limitIstenen: number | null;
  readonly ajan: string | null;
  readonly eslesenN: number | null;
  readonly toplamN: number | null;
}

export interface FiloYuku {
  /** LİSTENİN kendisi hakkında hüküm: roster + olay defteri okunabildi mi. */
  readonly ok: boolean | null;
  readonly hata: string | null;
  readonly ajanlar: readonly FiloAjani[] | null;
  readonly eslesmeyenTeslimler: readonly FiloTeslimi[] | null;
  readonly kaynak: FiloKaynagi | null;
  readonly suzgec: FiloSuzgeci | null;
}

/* ---- OKUYUCULAR ---------------------------------------------------------- */

/** Dizedeki metin öğeleri; dizi değilse `null`. `damgalanan`/`olculemeyen`
 *  serbest defter alanlarıdır — metin olmayan öğe düşürülmez, YAZIYA çevrilir:
 *  düşürmek listeyi sessizce kısaltır ve sayı ekranda yanlış okunur. */
function dizgeler(x: unknown): readonly string[] | null {
  const d = dizi(x);
  if (d === null) return null;
  return d.map((e) => (typeof e === "string" ? e : JSON.stringify(e)));
}

function mesajOku(x: unknown): FiloMesaji | null {
  const m = nesne(x);
  if (m === null) return null;
  return {
    rol: metin(m["rol"]),
    ts: metin(m["ts"]),
    tsHam: metin(m["ts_ham"]),
    metin: govde(m["metin"]),
    kirpildi: mantik(m["kirpildi"]),
    hamUzunluk: sayi(m["ham_uzunluk"]),
  };
}

function oturumOku(x: unknown): FiloOturumu | null {
  const o = nesne(x);
  if (o === null) return null;
  const ham = dizi(o["mesajlar"]);
  return {
    id: metin(o["id"]),
    ts: metin(o["ts"]),
    tsHam: metin(o["ts_ham"]),
    model: metin(o["model"]),
    mesajlar: ham === null ? null : ham.map(mesajOku).filter((m): m is FiloMesaji => m !== null),
  };
}

function teslimOku(x: unknown): FiloTeslimi | null {
  const t = nesne(x);
  if (t === null) return null;
  return {
    ts: metin(t["ts"]),
    olay: metin(t["event"]),
    damgalanan: dizgeler(t["damgalanan"]),
    detay: metin(t["detail"]),
    olculemeyen: dizgeler(t["olculemeyen"]),
  };
}

function teslimListesi(x: unknown): readonly FiloTeslimi[] | null {
  const d = dizi(x);
  if (d === null) return null;
  return d.map(teslimOku).filter((t): t is FiloTeslimi => t !== null);
}

function ajanOku(x: unknown, sira: number): FiloAjani | null {
  const a = nesne(x);
  if (a === null) return null;
  const ad = metin(a["ad"]);
  const tur = metin(a["tur"]);
  const ham = dizi(a["oturumlar"]);
  return {
    ad,
    tur,
    // ANAHTAR ÇİFTTEN TÜRER, `ad`dan DEĞİL: T1 raporunun uyarısı — bir profil
    // `hermes` adını taşırsa iki kayıt aynı React anahtarını alır ve biri kaybolur.
    anahtar: `${tur ?? "?"}:${ad ?? `sirasiz-${sira}`}`,
    model: metin(a["model"]),
    sonOturumTs: metin(a["son_oturum_ts"]),
    oturumlar: ham === null ? null : ham.map(oturumOku).filter((o): o is FiloOturumu => o !== null),
    teslimler: teslimListesi(a["teslimler"]),
    teslimToplam: sayi(a["teslim_toplam"]),
    teslimKirpildi: mantik(a["teslim_kirpildi"]),
    durum: metin(a["durum"]),
    neden: metin(a["neden"]),
  };
}

function kaynakOku(x: unknown): FiloKaynagi | null {
  const k = nesne(x);
  if (k === null) return null;
  return {
    profilKoku: metin(k["profil_koku"]),
    anaBeyin: metin(k["ana_beyin"]),
    botKoku: metin(k["bot_koku"]),
    botlar: dizgeler(k["botlar"]),
    events: metin(k["events"]),
    eventsNeden: metin(k["events_neden"]),
    teslimTavani: sayi(k["teslim_tavani"]),
    eslesmeyenToplam: sayi(k["eslesmeyen_toplam"]),
  };
}

function suzgecOku(x: unknown): FiloSuzgeci | null {
  const s = nesne(x);
  if (s === null) return null;
  return {
    limit: sayi(s["limit"]),
    limitIstenen: sayi(s["limit_istenen"]),
    ajan: metin(s["ajan"]),
    eslesenN: sayi(s["eslesen_n"]),
    toplamN: sayi(s["toplam_n"]),
  };
}

export function filoOku(govdeJson: unknown): FiloYuku {
  const g = nesne(govdeJson);
  const ham = g === null ? null : dizi(g["ajanlar"]);
  return {
    ok: g === null ? null : mantik(g["ok"]),
    hata: g === null ? null : metin(g["hata"]),
    ajanlar: ham === null ? null : ham.map(ajanOku).filter((a): a is FiloAjani => a !== null),
    eslesmeyenTeslimler: g === null ? null : teslimListesi(g["eslesmeyen_teslimler"]),
    kaynak: g === null ? null : kaynakOku(g["kaynak"]),
    suzgec: g === null ? null : suzgecOku(g["suzgec"]),
  };
}

/* ---- TÜRETİLMİŞ ÖLÇÜMLER (sayı UYDURULMAZ) ------------------------------- */

/** Bir ajanın oturumlarındaki mesaj sayısı. `oturumlar` ölçülemediyse `null` —
 *  0 yazmak "bu ajanla hiç mesajlaşılmadı" iddiası olurdu. */
export function mesajSayisi(a: FiloAjani): number | null {
  if (a.oturumlar === null) return null;
  let n = 0;
  for (const o of a.oturumlar) {
    if (o.mesajlar === null) return null;
    n += o.mesajlar.length;
  }
  return n;
}

/** SEKMEDE GÖSTERİLECEK ajan anahtarı — BAYAT SEÇİM SESSİZ BOŞ PANEL ÜRETMEZ.
 *
 *  ARIZA MODU (inceleme B1, 2026-08-31): iç sekme seçimi bileşen durumunda tutuluyor. Operatör
 *  `bekci`yi seçip "Tazele"ye bastığında roster DEĞİŞEBİLİR (profil eklendi/silindi, ya da
 *  roster o an ölçülemedi). Seçili anahtar artık hiçbir `TabsTrigger`/`TabsContent` ile
 *  eşleşmez ve Radix hiçbir panel çizmez: ekran SESSİZCE boşalır — ne "ölçülemedi" kutusu, ne
 *  hata, ne iz. Bu deponun tüm etiği sessiz boşluğun olmaması üzerine kurulu; bir satırlık
 *  `secili ?? ajanlar[0]?.anahtar` o etiğe delik açıyordu.
 *
 *  ÇÖZÜM SEÇİMİ BEYANLI: `Ajan.tsx`in şerhi "sekme ROTAYA yazılır, iç duruma DEĞİL" diyor ve bu
 *  fonksiyon o ilkeden SAPIYOR — sapma bilinçli ve ölçülmüş bir sınıra dayanıyor: `pano/rota.tsx`
 *  yolu `parca[2]`ye kadar ayrıştırıyor (`/dashboard/<yuzey>/<bolum>`), DÖRDÜNCÜ segment
 *  (`…/filo/<ajan>`) yok. Ajan başına derin bağ, yönlendiricinin sözleşmesini ve `yuzeyYolu`yu
 *  değiştirmeyi gerektirirdi — bu turun kapsamı dışı (devir kalemi). Kapsam içindeki hüküm şu:
 *  derin bağ OLMASA DA sessiz boşluk OLMAYACAK.
 *
 *  Saf fonksiyon olması da bilinçli: davranışı `node` ile GERÇEKTEN koşulabilsin diye
 *  (emsal `test_pano_palet_v152`), kaynak metninde kimlik arayan bir çiviyle değil. */
export function aktifAnahtar(ajanlar: readonly FiloAjani[], secili: string | null): string | null {
  if (secili !== null && ajanlar.some((a) => a.anahtar === secili)) return secili;
  return ajanlar[0]?.anahtar ?? null;
}

/** `ajanlar` hiç dizi değilse ekrana yazılacak neden — UCUN KENDİ HÜKMÜNÜ YUTMAZ.
 *
 *  İnceleme B2: bu dal sabit bir metin basıyordu ve `yuk.hata` ekrana hiç ulaşmıyordu; yani
 *  panonun "neden ekranda durur" kuralının tek istisnası buydu. Uç bir gün `ajanlar: null`
 *  basarsa operatör HANGİ kaynağın düştüğünü göremezdi. İki cümle de taşınır: şeklin
 *  tanınmadığı BİZİM hükmümüz, `hata` ise UCUN hükmü — biri ötekinin yerine geçmez. */
export function ajanListesiNedeni(yuk: FiloYuku): string {
  const taban =
    "`/api/ajanlar` gövdesinde `ajanlar` bir dizi değil — bu 'ajan yok' DEĞİL, şeklin tanınmadığıdır.";
  return yuk.hata === null ? taban : `${taban} Ucun kendi hükmü: ${yuk.hata}`;
}

/** Oturum listesinde geçen MODELLER (yeniden eskiye, ilk görülen sırada, tekil).
 *  Ultra geçişi tam olarak burada görünür: liste iki ad taşıyorsa model değişmiş. */
export function modeller(a: FiloAjani): readonly string[] | null {
  if (a.oturumlar === null) return null;
  const g = new Set<string>();
  for (const o of a.oturumlar) if (o.model !== null) g.add(o.model);
  return [...g];
}
