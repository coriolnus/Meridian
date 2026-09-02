/* ============================================================================
   KRİZ UÇLARI — sözleşme katmanı (OKUNARAK yazıldı, TAHMİN EDİLMEDİ)
   ----------------------------------------------------------------------------
   Bu dosya `meridian/api.py` ve `meridian/adapters/alpaca.py` AÇILIP okunarak
   yazıldı. Aşağıdaki her satır bir kaynak satırına dayanıyor; bir cümlenin
   arkasında dosya:satır yoksa o cümle buraya girmedi.

   ── 1 · SOFT HALT ──────────────────────────────────────────────────────────
   `POST /api/halt` (api.py::api_halt). Gövde OKUNMUYOR (`request.json()` çağrısı YOK).
   `health.set_halt(True)`e delege eder — bayrak dosyasına kendi eliyle dokunmaz.
   Yan etkiler: nabız `note: "HALT via dashboard"` ile YENİDEN yazılır (mevcut
   alanlar korunur), `obs.alarm(ALARM_HALT)` düşer, `notify.halted(True)` denenir,
   teşhis önbelleği boşaltılır.
   DÖNÜŞ: `{"halted": true, "message": "state/HALT created — new entries stop
   within one bar."}`.  GERİ ALINABİLİR: `POST /api/resume`.

   ── 1' · RESUME ────────────────────────────────────────────────────────────
   `POST /api/resume` (api.py::api_resume). `health.set_halt(False)`; İDEMPOTENT (bayrak
   dosyası yoksa no-op). DÖNÜŞ: `{"halted": false, "message": "HALT cleared."}`.

   ── 2 · CANCEL-OPEN ────────────────────────────────────────────────────────
   `POST /api/control/cancel_open` (api.py::api_control_cancel_open). Gövde OKUNMUYOR (senkron `def`).
   `alpaca.cancel_open_entries()` (alpaca.py::cancel_open_entries) çağrılır:
     · Açık emirler `nested=True` çekilir (OCO/bracket bacakları `legs` altında).
     · Her emir `coid_sinifi` ile sınıflanır: `giris` · `koruma` · `yabanci`.
     · YALNIZ `giris` sınıfı VE `filled_qty == 0` VE durumu
       new/accepted/pending_new/held olan MOTOR emri (`P-` öneki) iptal edilir.
     · `koruma` bacaklarına DOKUNULMAZ (çıplak pozisyon yasağı); `yabanci`
       (operatörün kendi emri) SAYILIR ama dokunulmaz.
   DÖNÜŞ: `{ok, cancelled[], kept[], foreign[], siniflar{giris,koruma,yabanci}}`.
   ⚠ ADAPTÖR ARIZASI HTTP 200 İÇİNDE GELİR: `except` dalı `{"ok": false, "detail":
   "..."}` DÖNDÜRÜR (alpaca.py::cancel_open_entries) ve uç bunu 200 ile geçirir. Yani "200 = oldu"
   BURADA YANLIŞTIR; hüküm `ok` alanından okunur.

   ── 3 · FLATTEN ────────────────────────────────────────────────────────────
   `POST /api/alpaca/close_all?confirm=FLATTEN-PAPER` (api.py::api_alpaca_close_all · alpaca.py::close_all).
   `confirm` bir SORGU parametresidir, gövde değil. Jeton `CLOSE_ALL_CONFIRM`
   (alpaca.py::CLOSE_ALL_CONFIRM) = "FLATTEN-PAPER".
     · JETONSUZ çağrı HİÇBİR ŞEYE DOKUNMAZ (alpaca.py::close_all): yalnız
       `{"ok": false, "detail": "confirm token required", "dry_run": true,
         "would_flatten": [...], "foreign": [...]}` raporlar. KURU KOŞU budur ve
       bu ekran ölçümünü ORADAN alır — sunucunun kendi cevabı, panonun tahmini değil.
     · JETONLU çağrı: `DELETE /v2/orders` + `DELETE /v2/positions?cancel_orders=true`.
       DÖNÜŞ `{"ok": r.status_code < 400, "status": <int>}`; istisnada
       `{"ok": false, "detail": "..."}` — yine HTTP 200 içinde.
   GERİ ALINAMAZ. Ve `foreign` boş değilse bu emir OPERATÖRÜN KENDİ varlığına
   dokunur (alpaca.py::close_all — "İNSANIN varlığına dokunmasıdır").

   ── 4 · HALT LEARNING ──────────────────────────────────────────────────────
   `POST /api/control/learn_halt` (api.py::api_control_learn_halt). `async def` ve `await request.json()`
   ZORUNLU: gövdesiz istek ayrıştırma hatası verir. Gövde `{"on": bool}`.
   `health.set_learn_halt(on)`; işlemler DEVAM eder, `reflect.submit` erken döner
   (yeni strateji sürümü SHIP EDİLEMEZ), rollback güvenlik olarak açık kalır.
   DÖNÜŞ: `{"learn_halted": bool}`. GERİ ALINABİLİR: aynı uca `on: false`.

   ── ORTAK: 401 GERÇEKTEN "HİÇBİR ŞEY OLMADI" DEMEK ─────────────────────────
   Beş ucun BEŞİNDE de `_auth(request)` gövdenin ilk satırıdır — yetki, gövde
   okunmadan ve hiçbir yan etki üretilmeden sınanır. Bu yüzden 401 hâlinde
   "kol ÇEKİLMEDİ" demek bir tahmin değil, okunmuş bir olgudur.

   ── ORTAK: AĞ HATASI ("kod 0") BU KOLLARDA HAYATİ ──────────────────────────
   Bir onay ekranında "ulaştı mı bilinmiyor" rahatsız edicidir; BURADA hayat
   kurtarır. HALT isteği ağda kaybolduysa sistem DURMAMIŞ olabilir — ve operatör
   durduğunu sanır. Bu yüzden `kod: 0` ayrı bir hâldir ve metni "yazılmadı"
   DEMEZ; "durumu ÖLÇ, körlemesine tekrar gönderme" der.
   ============================================================================ */

/** `alpaca.CLOSE_ALL_CONFIRM` (alpaca.py::CLOSE_ALL_CONFIRM) — jeton BURADA da literal, çünkü
    sorgu parametresini pano yazıyor. Değişirse uç 200/dry_run döner ve ekran
    bunu BAŞARISIZLIK olarak okur (bkz. `flattenSonucu`). */
export const FLATTEN_JETON = "FLATTEN-PAPER";

/* ---- YAZAN İSTEK --------------------------------------------------------- */

export interface GonderSonucu {
  readonly ok: boolean;
  /** HTTP durum kodu. `0` = yanıt HİÇ gelmedi (ağ/iptal) — sunucunun sustuğu hâl. */
  readonly kod: number;
  /** FastAPI `detail` alanı. Okunamadıysa `null` — boş dizge YAZILMAZ (yalan olurdu). */
  readonly detay: string | null;
  /** Yanıt gövdesi. HATA gövdesi de TUTULUR: bu uçlarda `ok:false` 200 içinde gelir. */
  readonly govde: unknown;
}

function detaydanMetin(g: unknown): string | null {
  if (g === null || typeof g !== "object") return null;
  const d = (g as { detail?: unknown }).detail;
  if (typeof d === "string" && d.trim() !== "") return d;
  // FastAPI doğrulama hatası `detail`i bir DİZİDİR ({loc,msg,type}); `msg`leri birleştiriyoruz.
  if (Array.isArray(d)) {
    const m = d
      .map((x) => (x !== null && typeof x === "object" ? (x as { msg?: unknown }).msg : null))
      .filter((x): x is string => typeof x === "string");
    if (m.length > 0) return m.join(" · ");
  }
  return null;
}

/**
 * Tek POST. Ne fırlatır ne yutar: her hâl dönüş nesnesinde ADIYLA durur.
 *
 * NEDEN `veri.ts::apiGet` KULLANILMIYOR: o yol GET içindir ve 401'i `OturumHatasi`
 * DİYE FIRLATIR. Fırlatan bir yol, bir icra kolunda "ne oldu" sorusunu try/catch'e
 * havale eder ve `kod 0` (ağ) ile `kod 401` (oturum) aynı catch dalında birleşir —
 * oysa bu iki hâlin operatöre söylediği şey taban tabana zıt: biri "hiçbir şey
 * olmadı, yeniden gir", diğeri "olmuş OLABİLİR, git ÖLÇ".
 *
 * NEDEN `kuyruk/onayEylem.ts`TEN İMPORT EDİLMEDİ (bilinçli tekrar): tur paralel
 * ajanlarla koşuyor ve dosya-ayrıklığı sözleşmesi YAZMA tarafını ayırıyor. Uçuş
 * hâlindeki bir dosyadan import etmek, onun dışa aktarım kümesi değiştiği an
 * ÜST BARI — yani panonun her sayfasını — derlenemez hâle getirirdi. Kriz
 * kollarının derlenmemesi, kriz kollarının olmaması demektir. Birleştirme
 * tur-kapanışı işidir.
 */
export async function krizPost(yol: string, govde?: unknown): Promise<GonderSonucu> {
  let y: Response;
  try {
    y = await fetch(yol, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(govde ?? {}),
    });
  } catch (e) {
    // AĞ DÜŞMESİ BİR HTTP CEVABI DEĞİLDİR: `kod: 0` onu "sunucu bir şey söyledi"den ayırır.
    return { ok: false, kod: 0, detay: e instanceof Error ? e.message : String(e), govde: null };
  }
  let cozulen: unknown = null;
  try {
    cozulen = await y.json();
  } catch {
    // YASA 4 · sessiz-yutma İŞARETLİ: gövde JSON değilse (proxy'nin düz metin 502'si,
    // Caddy'nin kendi hata sayfası) ayrıştırma hatası ASIL sonucu gizlememeli — durum
    // kodu `kod` alanında duruyor ve hüküm oradan da verilebilir.
  }
  // GÖVDE HATA HÂLİNDE DE TUTULUR (`onayEylem.ts`ten AYRILAN nokta ve bilinçli):
  // bu ailede `ok:false` 200 İÇİNDE geliyor; gövdeyi yalnız `y.ok` iken saklamak,
  // adaptör arızasının teşhisini (`detail`) çöpe atmak olurdu.
  return { ok: y.ok, kod: y.status, detay: detaydanMetin(cozulen), govde: cozulen };
}

/* ---- KOL KATALOĞU -------------------------------------------------------- */

export type KolKimlik = "soft_halt" | "resume" | "cancel_open" | "flatten" | "learn_halt";

export interface Kol {
  readonly kimlik: KolKimlik;
  /** Eski panodaki kademe numarası — kas hafızası ORAYA bağlı (index.html:2682-2685). */
  readonly kademe: string;
  readonly ad: string;
  /** Kolun ne yaptığı, TEK satır — listede okunur. */
  readonly ozet: string;
  /** İki tık ARASINDA okunacak cümle. Uç gövdesinden çıkarıldı, uydurulmadı. */
  readonly nedir: string;
  readonly geriAlinabilir: boolean;
  readonly geriAlmaNotu: string;
  /** FLATTEN AYRI SINIFTA: ağır kapı (ölçüm + jeton yazımı) yalnız bunda açılır. */
  readonly agir: boolean;
}

export const KOLLAR: Readonly<Record<KolKimlik, Kol>> = {
  soft_halt: {
    kimlik: "soft_halt",
    kademe: "Kademe 1",
    ad: "Soft Halt",
    ozet: "Yeni giriş durur; açık pozisyonlar yönetilmeye devam eder.",
    nedir:
      "`POST /api/halt` → `health.set_halt(True)`: `state/HALT` bayrağı doğar ve YENİ emir girişi " +
      "bir bar içinde durur. Açık pozisyonların yönetimi (stop/hedef bacakları) DEVAM eder — bu kol " +
      "pozisyon KAPATMAZ. Yan etki: nabza `note: HALT via dashboard` yazılır, `ALARM_HALT` alarmı " +
      "düşer, bildirim kanalı denenir, teşhis önbelleği boşaltılır.",
    geriAlinabilir: true,
    geriAlmaNotu: "GERİ ALINABİLİR: `POST /api/resume` aynı bayrağı kaldırır (idempotent).",
    agir: false,
  },
  resume: {
    kimlik: "resume",
    kademe: "Kademe 1",
    ad: "DEVAM et",
    ozet: "HALT bayrağı kalkar; sistem yeniden giriş alabilir hâle gelir.",
    nedir:
      "`POST /api/resume` → `health.set_halt(False)`: `state/HALT` bayrağı kalkar ve sistem YENİDEN " +
      "giriş emri üretebilir hâle gelir. İDEMPOTENT — bayrak zaten yoksa hiçbir şey olmaz. " +
      "`resume` olayı deftere yazılır ve bildirim kanalı denenir.",
    geriAlinabilir: true,
    geriAlmaNotu: "GERİ ALINABİLİR: `POST /api/halt` kolu yeniden çeker.",
    agir: false,
  },
  cancel_open: {
    kimlik: "cancel_open",
    kademe: "Kademe 2",
    ad: "Cancel-Open",
    ozet: "Dolmamış GİRİŞ emirleri iptal; koruma bacaklarına dokunulmaz.",
    nedir:
      "`POST /api/control/cancel_open` → `alpaca.cancel_open_entries()`: broker'daki AÇIK emirler " +
      "taranır ve her biri `coid_sinifi` ile sınıflanır. YALNIZ `giris` sınıfındaki, HİÇ DOLMAMIŞ " +
      "(`filled_qty = 0`), motorun gönderdiği (`P-` önekli) emirler iptal edilir. Koruyucu " +
      "stop/hedef bacakları (`koruma`) ve SENİN elle girdiğin emirler (`yabanci`) sayılır ama " +
      "DOKUNULMAZ — çıplak pozisyon yasağı bu kolun içinde yazılı.",
    geriAlinabilir: false,
    geriAlmaNotu:
      "GERİ ALINAMAZ: iptal edilmiş emir geri getirilemez. Motor bir sonraki döngüde benzer bir " +
      "emir üretebilir, ama o AYNI emir değildir (yeni coid, yeni sıra).",
    agir: false,
  },
  flatten: {
    kimlik: "flatten",
    kademe: "Kademe 3",
    ad: "Flatten",
    ozet: "TÜM pozisyonlar piyasadan kapanır — seninkiler dahil.",
    nedir:
      "`POST /api/alpaca/close_all?confirm=" +
      FLATTEN_JETON +
      "` → `DELETE /v2/orders` ardından `DELETE /v2/positions?cancel_orders=true`: Alpaca kağıt " +
      "hesabındaki TÜM açık emirler iptal edilir ve TÜM pozisyonlar PİYASA fiyatından kapatılır. " +
      "Bu hesap yalnız motorun değil — senin elle aldığın pozisyonlar da burada ve onlar da kapanır.",
    geriAlinabilir: false,
    geriAlmaNotu:
      "GERİ ALINAMAZ ve bu kolun geri alınamazlığı diğerlerinden BAŞKA cinstir: bayrak kaldırmak " +
      "değil, piyasada işlem yapmaktır. Kapanan pozisyon o anki fiyattan kapanmıştır; geri açmak " +
      "yeni bir işlemdir ve aynı fiyatı vermez.",
    agir: true,
  },
  learn_halt: {
    kimlik: "learn_halt",
    kademe: "Kademe 4",
    ad: "Halt Learning",
    ozet: "İşlem sürer; yeni strateji sürümü ship EDİLEMEZ.",
    nedir:
      "`POST /api/control/learn_halt` (gövde `{on: …}`) → `health.set_learn_halt(on)`: işlemler " +
      "DEVAM eder — bu kol ticareti durdurmaz. Duran şey ÖĞRENMEDİR: `reflect.submit` erken döner, " +
      "yeni strateji sürümü SHIP EDİLEMEZ. Rollback güvenlik olarak açık kalır.",
    geriAlinabilir: true,
    geriAlmaNotu: "GERİ ALINABİLİR: aynı uca `{on: false}` gönderilir.",
    agir: false,
  },
};

/** Kolun gideceği yol + gövde. `learn_halt` yönü çağıranda belirlenir (aç/kaldır). */
export function kolIstegi(kimlik: KolKimlik, learnHaltAc?: boolean): { yol: string; govde: unknown } {
  switch (kimlik) {
    case "soft_halt":
      return { yol: "/api/halt", govde: {} };
    case "resume":
      return { yol: "/api/resume", govde: {} };
    case "cancel_open":
      return { yol: "/api/control/cancel_open", govde: {} };
    case "flatten":
      return { yol: `/api/alpaca/close_all?confirm=${encodeURIComponent(FLATTEN_JETON)}`, govde: {} };
    case "learn_halt":
      // GÖVDE ZORUNLU: uç `await request.json()` çağırıyor (api.py::api_control_learn_halt). `undefined`
      // geçilseydi `krizPost` yine `{}` yazardı ve `on` sessizce `false` olurdu — yani
      // "ship'i durdur" düğmesi ship'i SERBEST BIRAKIRDI. Yön burada AÇIKÇA taşınır.
      return { yol: "/api/control/learn_halt", govde: { on: learnHaltAc === true } };
  }
}

/* ---- HATA GRAMERİ — ÜÇ HÂL AYRI, ÇÜNKÜ ÇARELERİ AYRI --------------------- */

export interface HataMetni {
  readonly baslik: string;
  readonly govde: string;
  readonly oturumDustu: boolean;
  /** İSTEĞİN ULAŞIP ULAŞMADIĞI BİLİNİYOR MU? `false` iken operatör ÖLÇMEDEN tekrar göndermemeli. */
  readonly sonucBiliniyor: boolean;
}

export function krizHatasi(sonuc: GonderSonucu, yol: string, kol: Kol): HataMetni {
  const d = sonuc.detay;
  if (sonuc.kod === 0) {
    return {
      baslik: "AĞ HATASI — yanıt hiç gelmedi, kol çekildi mi BİLİNMİYOR",
      govde:
        `${yol} isteği bir HTTP yanıtı üretmedi (${d ?? "tarayıcı bir sebep yazmadı"}). ` +
        `Bu "${kol.ad} çekilmedi" DEMEK DEĞİLDİR: istek sunucuya ulaşmış ve YANITI kaybolmuş ` +
        `olabilir — o hâlde kol ÇEKİLMİŞTİR ve ekran bunu bilmiyordur. ` +
        (kol.geriAlinabilir
          ? "Önce durumu ÖLÇ (üst bardaki durum hapı / bu paneli kapat-aç), sonra karar ver."
          : "BU KOL GERİ ALINAMAZ: körlemesine tekrar göndermek aynı işlemi İKİNCİ kez yapabilir. " +
            "Önce broker'ı ve olay defterini ÖLÇ."),
      oturumDustu: false,
      sonucBiliniyor: false,
    };
  }
  if (sonuc.kod === 401) {
    return {
      baslik: "Oturum düştü (401) — kol ÇEKİLMEDİ",
      govde:
        `${yol} 401 döndü. Bu bir ölçüm hatası değil: panoya yeniden giriş gerekiyor. ` +
        `Hiçbir yan etki oluşmadı — uç yetkiyi (\`_auth\`) gövdeyi okumadan ve hiçbir bayrağa ` +
        `dokunmadan sınıyor. Çare: panodan çık, yeniden gir. Tazelemek bu hâli düzeltmez.`,
      oturumDustu: true,
      sonucBiliniyor: true,
    };
  }
  if (sonuc.kod >= 400 && sonuc.kod < 500) {
    return {
      baslik: `Uç REDDETTİ (${sonuc.kod}) — gerekçesi aynen aşağıda`,
      govde:
        (d ?? "uç gerekçe metni döndürmedi (bu bir kusurdur: api.py ret gerekçelerini `detail`e yazar)") +
        " · Bu bir ağ/pano hatası DEĞİL: sunucu isteği ALDI, yasayı uyguladı ve HAYIR dedi. " +
        "Kol çekilmedi.",
      oturumDustu: false,
      sonucBiliniyor: true,
    };
  }
  if (sonuc.kod >= 500) {
    return {
      baslik: `Sunucu hatası (${sonuc.kod}) — sonuç BİLİNMİYOR`,
      govde:
        `${yol} ${sonuc.kod} döndü${d ? ` — ${d}` : " ve gövdesinde okunabilir bir `detail` yoktu"}. ` +
        `İstisna yan etkiden ÖNCE de SONRA da fırlamış olabilir; yani kolun çekilip çekilmediği ` +
        `pano tarafından BİLİNEMEZ. Durumu ÖLÇ, körlemesine tekrar gönderme.`,
      oturumDustu: false,
      sonucBiliniyor: false,
    };
  }
  return {
    baslik: `Beklenmeyen durum kodu (${sonuc.kod})`,
    govde:
      `${yol} ${sonuc.kod} döndü${d ? ` — ${d}` : ""}. Bu kod bu uç ailesinde beklenmiyor; ` +
      `sonucu ölçmeden ikinci kez gönderme.`,
    oturumDustu: false,
    sonucBiliniyor: false,
  };
}

/* ---- SONUÇ OKUMA — "200" BAŞARI DEĞİLDİR -------------------------------- */

export interface KolSonucu {
  readonly basarili: boolean;
  readonly baslik: string;
  /** Uçtan gelen GÖVDEDEN kurulmuş satırlar. Panonun yorumu değil. */
  readonly satirlar: readonly string[];
}

function sayi(x: unknown): number | null {
  if (typeof x === "number" && Number.isFinite(x)) return x;
  if (typeof x === "string" && x.trim() !== "") {
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function uzunluk(x: unknown): number | null {
  return Array.isArray(x) ? x.length : null;
}

/**
 * Uçtan dönen 200 gövdesini HÜKME çevirir. Her kolun "oldu" ölçütü AYRIDIR ve
 * hiçbiri "HTTP 200" değildir — `cancel_open` ve `close_all` adaptör arızasını
 * 200 içinde `ok:false` olarak taşıyor.
 */
export function kolSonucu(kimlik: KolKimlik, govde: unknown, learnHaltAc?: boolean): KolSonucu {
  const g = (govde !== null && typeof govde === "object" ? govde : {}) as Record<string, unknown>;

  if (kimlik === "soft_halt" || kimlik === "resume") {
    const beklenen = kimlik === "soft_halt";
    const h = g["halted"];
    if (typeof h !== "boolean") {
      return {
        basarili: false,
        baslik: "Yanıt `halted` alanını YAZMADI — kolun hâli ölçülemedi",
        satirlar: [
          "Uç 200 döndü ama gövdesinde `halted` yok. Bu uçlar (api.py::api_halt · api.py::api_resume) onu HER ZAMAN " +
            "yazar; yokluğu bir kusurdur. Kolun çekilip çekilmediğini üst bardaki durum hapından ÖLÇ.",
        ],
      };
    }
    const mesaj = typeof g["message"] === "string" ? (g["message"] as string) : null;
    if (h !== beklenen) {
      return {
        basarili: false,
        baslik: `Uç TERS hâl bildirdi: \`halted = ${String(h)}\``,
        satirlar: [
          `Gönderilen niyet "${beklenen ? "durdur" : "devam et"}" idi, uç ise \`halted=${String(h)}\` ` +
            "döndü. İki gerçek arasında panonun yorumu YOK: ekranı tazele ve durumu yeniden ölç.",
          ...(mesaj ? [`uç mesajı: ${mesaj}`] : []),
        ],
      };
    }
    return {
      basarili: true,
      baslik: beklenen ? "HALT çekildi — `halted = true`" : "HALT kaldırıldı — `halted = false`",
      satirlar: mesaj ? [`uç mesajı: ${mesaj}`] : ["uç `message` yazmadı"],
    };
  }

  if (kimlik === "learn_halt") {
    const lh = g["learn_halted"];
    if (typeof lh !== "boolean") {
      return {
        basarili: false,
        baslik: "Yanıt `learn_halted` alanını YAZMADI — kolun hâli ölçülemedi",
        satirlar: ["Uç (api.py::api_control_learn_halt) bu alanı her zaman yazar; yokluğu bir kusurdur. Paneli kapat-aç ve ölç."],
      };
    }
    if (lh !== (learnHaltAc === true)) {
      return {
        basarili: false,
        baslik: `Uç TERS hâl bildirdi: \`learn_halted = ${String(lh)}\``,
        satirlar: [
          `Gönderilen \`on\` değeri ${String(learnHaltAc === true)} idi. Ekranı tazele ve hâli yeniden ölç.`,
        ],
      };
    }
    return {
      basarili: true,
      baslik: lh ? "Öğrenme durduruldu — `learn_halted = true`" : "Öğrenme serbest — `learn_halted = false`",
      satirlar: [
        lh
          ? "İşlemler DEVAM ediyor; duran şey ship yolu (`reflect.submit` erken döner)."
          : "Ship yolu yeniden açık; rollback zaten hep açıktı.",
      ],
    };
  }

  if (kimlik === "cancel_open") {
    const ok = g["ok"] === true;
    const iptal = uzunluk(g["cancelled"]);
    const korunan = uzunluk(g["kept"]);
    const yabanci = uzunluk(g["foreign"]);
    const s = (g["siniflar"] !== null && typeof g["siniflar"] === "object"
      ? (g["siniflar"] as Record<string, unknown>)
      : {}) as Record<string, unknown>;
    const sg = sayi(s["giris"]);
    const sk = sayi(s["koruma"]);
    const sy = sayi(s["yabanci"]);
    // KORUMA BACAĞININ GEREKÇESİ OKUNUR (YASA 6): `cancel_open_entries` her korunan
    // satıra `neden` yazıyor ve o cümle "neden iptal edilmedi"nin cevabı. Yazmasaydık
    // alan üretilir ama okunmazdı.
    const kept = Array.isArray(g["kept"]) ? (g["kept"] as readonly unknown[]) : [];
    const korumaBacak = kept.filter(
      (k) => k !== null && typeof k === "object" && (k as { sinif?: unknown }).sinif === "koruma",
    );
    const ilkNeden = korumaBacak.length > 0 ? (korumaBacak[0] as { neden?: unknown }).neden : null;

    if (!ok) {
      return {
        basarili: false,
        baslik: "Süpürücü ARIZA bildirdi — `ok: false` (HTTP 200 içinde)",
        satirlar: [
          typeof g["detail"] === "string"
            ? `uç gerekçesi: ${g["detail"] as string}`
            : "uç `detail` yazmadı — arızanın sebebi ölçülemedi",
          "Hiçbir emir iptal edilmemiş OLABİLİR ama bu KESİN DEĞİL: adaptör döngünün ortasında " +
            "düşerse bir kısmı iptal edilmiş olur. Broker'ı ÖLÇ.",
        ],
      };
    }
    return {
      basarili: true,
      baslik: `Süpürme tamam — ${iptal ?? "?"} giriş emri iptal edildi`,
      satirlar: [
        `iptal (giriş): ${iptal ?? "uç `cancelled` dizisini yazmadı"} · korunan: ${
          korunan ?? "uç `kept` dizisini yazmadı"
        }`,
        sg === null && sk === null && sy === null
          ? "sınıf dökümü ÖLÇÜLEMEDİ — uç `siniflar` yazmadı (eski sunucu sürümü olabilir)"
          : `sınıf dökümü — giriş ${sg ?? "?"} · koruma ${sk ?? "?"} · yabancı ${sy ?? "?"}`,
        korumaBacak.length > 0
          ? `koruma bacağı DOKUNULMADI (${korumaBacak.length}): ${
              typeof ilkNeden === "string" ? ilkNeden.slice(0, 140) : "gerekçe yazılmamış"
            }`
          : "korunan satırlar arasında `koruma` sınıfı YOK",
        yabanci !== null && yabanci > 0
          ? `yabancı (senin emirlerin, dokunulmadı): ${yabanci}`
          : "yabancı emir yok (ya da uç `foreign` yazmadı)",
      ],
    };
  }

  // flatten
  return flattenSonucu(g);
}

function flattenSonucu(g: Record<string, unknown>): KolSonucu {
  // JETON ULAŞMADIYSA BU BİR BAŞARI DEĞİL: `dry_run: true` dönmesi, sorgu parametresinin
  // uca varmadığı (proxy düşürdü, jeton değişti) demektir — HİÇBİR pozisyon kapanmadı ve
  // ekranın "gönderildi" demesi tam da P-2026-08-07-VLO sınıfı bir yalan olurdu.
  if (g["dry_run"] === true) {
    return {
      basarili: false,
      baslik: "JETON UCA ULAŞMADI — hiçbir pozisyon kapatılmadı",
      satirlar: [
        `Uç kuru koşu (\`dry_run: true\`) döndürdü; yani \`confirm=${FLATTEN_JETON}\` parametresi ` +
          "uca varmamış (ara katman düşürmüş ya da jeton değişmiş olabilir).",
        typeof g["detail"] === "string" ? `uç gerekçesi: ${g["detail"] as string}` : "uç `detail` yazmadı",
        "HİÇBİR ŞEY DÜZLEŞTİRİLMEDİ. Kolu yeniden çekmeden önce sebebi bul.",
      ],
    };
  }
  if (g["ok"] === true) {
    const st = sayi(g["status"]);
    return {
      basarili: true,
      baslik: "Flatten GÖNDERİLDİ — broker kabul etti",
      satirlar: [
        st === null
          ? "uç `status` yazmadı — broker'ın HTTP kodu ölçülemedi"
          : `broker yanıt kodu: ${st} (uç \`ok\`u \`status < 400\` diye hesaplıyor)`,
        "İKİ ÇAĞRI GİTTİ: önce tüm açık emirler iptal (`DELETE /v2/orders`), sonra tüm pozisyonlar " +
          "piyasadan kapatıldı (`DELETE /v2/positions?cancel_orders=true`).",
        "DOLUM AYRI BİR ŞEYDİR: broker isteği kabul etti demek her pozisyonun DOLDUĞU demek değildir. " +
          "Pozisyonların gerçekten kapandığını broker ekranından / mutabakattan ÖLÇ.",
      ],
    };
  }
  return {
    basarili: false,
    baslik: "Flatten BAŞARISIZ — `ok: false` (HTTP 200 içinde)",
    satirlar: [
      typeof g["detail"] === "string"
        ? `uç gerekçesi: ${g["detail"] as string}`
        : "uç `detail` yazmadı — arızanın sebebi ölçülemedi",
      sayi(g["status"]) !== null ? `broker yanıt kodu: ${sayi(g["status"])}` : "broker HTTP kodu ölçülemedi",
      "İLK ÇAĞRI (emir iptali) GEÇMİŞ OLABİLİR: iki `DELETE` ardışıktır ve ikincisi düşse de " +
        "birincisi çoktan uygulanmış olur. Broker'ı ÖLÇ — 'hiçbir şey olmadı' varsayma.",
    ],
  };
}

/* ---- ÖLÇÜM: FLATTEN'IN ONAY CÜMLESİNİ KURAN SAYILAR ---------------------- */

/** `/api/alpaca` gövdesinin BU EKRANIN okuduğu kesiti (api.py::api_alpaca · alpaca.py::dashboard_view). */
export interface AlpacaGovdesi {
  readonly paper_available?: boolean;
  readonly account?: {
    readonly connected?: boolean;
    readonly equity?: number | null;
    readonly positions?: readonly {
      readonly symbol?: string | null;
      readonly qty?: string | number | null;
      readonly current?: string | number | null;
      readonly upl?: string | number | null;
    }[];
    readonly open_orders?: readonly unknown[];
  } | null;
}

/** Jetonsuz `close_all` yanıtı — KURU KOŞU (alpaca.py::close_all). Hiçbir şeye dokunmaz. */
export interface KuruKosu {
  readonly dry_run?: boolean;
  readonly would_flatten?: readonly string[];
  readonly foreign?: readonly string[];
  readonly detail?: string;
}

export interface PozisyonOlcumu {
  /** Broker'da sayılan pozisyon adedi. Ölçülemediyse `null` + `neden`. */
  readonly adet: number | null;
  readonly semboller: readonly string[];
  /** Σ |qty × current|. Hiçbir satır çözülemediyse `null`. */
  readonly piyasaDegeri: number | null;
  /** Piyasa değeri çözülemeyen semboller — kısmi toplam "en az" diye okunur. */
  readonly degeriOlculemeyen: readonly string[];
  /** `adet`/`piyasaDegeri` null ise NEDENİ. Ölçüm tamsa boş dizge DEĞİL, `null`. */
  readonly neden: string | null;
}

/**
 * Broker pozisyonlarını ÖLÇER. Kitabın (`/api/today.open_positions`) değil,
 * BROKER'ın pozisyonlarını — çünkü Flatten broker'da işlem yapar ve bu iki defterin
 * AYRIŞTIĞI bu depoda ölçülmüş bir olgudur (`sermaye.pozisyon_mutabakati`,
 * api.py::api_today: "yedi açık pozisyonun yedisinde de adet ayrışıyordu"). Yanlış deftere
 * bakan bir onay cümlesi, doğru görünen bir yalandır.
 *
 * `[]` BOŞLUĞU KANITLAMAZ: `alpaca.positions()` arıza hâlinde de `[]` döner
 * (alpaca.py::positions — "ya gerçekten pozisyon yok YA DA API ulaşılamadı"). Bu yüzden
 * sıfır adet, `connected` bayrağıyla BİRLİKTE okunur ve belirsizlik `neden`e yazılır.
 */
export function pozisyonlariOlc(a: AlpacaGovdesi | null, hata: string | null): PozisyonOlcumu {
  const bos: PozisyonOlcumu = { adet: null, semboller: [], piyasaDegeri: null, degeriOlculemeyen: [], neden: "" };
  if (hata !== null) {
    return { ...bos, neden: `/api/alpaca okunamadı — ${hata}` };
  }
  if (a === null) {
    return { ...bos, neden: "/api/alpaca henüz okunmadı" };
  }
  if (a.paper_available === false) {
    return { ...bos, neden: "kağıt hesap ERİŞİLEBİLİR DEĞİL (`paper_available: false`) — pozisyonlar sayılamaz" };
  }
  const acct = a.account ?? null;
  if (acct === null) {
    return { ...bos, neden: "`account` alanı null — hesap görünümü kurulamadı" };
  }
  const poz = acct.positions;
  if (!Array.isArray(poz)) {
    return { ...bos, neden: "`account.positions` bir dizi değil — pozisyon listesi ölçülemedi" };
  }
  const semboller = poz.map((p, i) => (typeof p.symbol === "string" && p.symbol !== "" ? p.symbol : `#${i} (sembolsüz)`));
  const olculemeyen: string[] = [];
  let toplam = 0;
  let cozulen = 0;
  poz.forEach((p, i) => {
    const q = sayi(p.qty);
    const c = sayi(p.current);
    const ad = semboller[i] ?? `#${i}`;
    if (q === null || c === null) {
      olculemeyen.push(ad);
      return;
    }
    // PİYASA DEĞERİ TÜRETİLDİ, OKUNMADI: `dashboard_view` (alpaca.py::dashboard_view) Alpaca'nın
    // `market_value` alanını GEÇİRMİYOR — yalnız qty/current/avg_entry/upl. Çarpım bu
    // yüzden burada yapılıyor ve türetilmiş olduğu ekranda YAZILI.
    toplam += Math.abs(q * c);
    cozulen += 1;
  });
  const bagli = acct.connected === true;
  const neden =
    poz.length === 0
      ? bagli
        ? "broker LİSTE BOŞ döndü ve hesap bağlı görünüyor — ama `positions()` arızada da boş döner " +
          "(alpaca.py::positions), yani \"pozisyon yok\" KANITLANMIŞ değildir"
        : "broker liste boş VE `connected` doğrulanmadı — bu boşluk büyük olasılıkla ÖLÇÜM EKSİKLİĞİ"
      : null;
  return {
    adet: poz.length,
    semboller,
    piyasaDegeri: cozulen > 0 ? toplam : null,
    degeriOlculemeyen: olculemeyen,
    neden,
  };
}

/** Para biçimi — ölçülemeyeni asla `0` diye basmamak için `null` girişi ayrı ele alınır. */
export function paraMetni(n: number | null): string | null {
  if (n === null) return null;
  return n.toLocaleString("tr-TR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

/** `/api/diagnostics` gövdesinin BU EKRANIN okuduğu kesiti — yalnız öğrenme kolunun hâli. */
export interface TeshisKesiti {
  readonly hud?: { readonly learn_halted?: boolean; readonly halted?: boolean };
  readonly risk?: { readonly learn_halted?: boolean; readonly halted?: boolean };
}
