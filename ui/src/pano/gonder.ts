/* ============================================================================
   YAZMA KATMANI — FastAPI POST uçlarına tek kapı (`veri.ts`nin yazan kardeşi)
   ----------------------------------------------------------------------------
   `veri.ts::apiGet` panonun OKUMA kapısı ve BİLEREK yalnız GET yapıyor (o
   dosyanın başlığı: "pano SUNUCUDA render edilmiyor, veri tarayıcıda /api/*ten
   çekiliyor"). Panonun YAZMA tarafı — onay, kimlik, birim anahtarı gibi POST
   isteyen her yüzey — o kapıdan GEÇMEZ: yazma isteklerinin hata yüzeyi bir
   GET'inkinden BAŞKA (401/403/409/429 her biri ayrı çare ister, ayrı cümle
   ister) ve `apiGet` bunları TEK bir `hata: string` alanına ezerdi. Bu yüzden
   yazma tarafı KENDİ kapısını taşır: bu dosya.

   AYRIM BİLEREK KORUNUYOR — birleştirilmeyecek: okuma tarafı "veri geldi mi,
   ne zaman, oturum düştü mü" sorusuna cevap verir ve periyodik tazelemeyle
   yaşar (`useApi`); yazma tarafı "istek gitti mi, hangi kod döndü, gövde
   neydi" sorusuna cevap verir ve HER ZAMAN tek seferliktir (bir tıklama →
   bir sonuç). İkisini tek bir "genel fetch sarmalayıcısı"na eritmek, GET'in
   401'ini ("oturum düştü, tazeleme farklı") POST'un 401'iyle ("parola hatalı"
   ya da "karar yazılmadı") aynı kılığa sokardı.

   BU MODÜL TEK-KAYNAK YASASININ UYGULANMASIdır (CLAUDE.md §4): `GonderSonucu` +
   `apiPost` bugüne kadar `kimlik/gonder.ts` ve `kuyruk/onayEylem.ts`te İKİ birebir
   kopya olarak yaşıyordu (ikincisi paralel-ajan turu için süreli bir tekrardı).
   Tüketiciler artık BURADAN alır; `kimlik/gonder.ts` yalnız kendi uçlarının
   sözleşme dokümantasyonunu taşıyan bir geçiş yüzeyi olarak kalır.
   ============================================================================ */

export interface GonderSonucu {
  readonly ok: boolean;
  /** HTTP durum kodu. `0` = yanıt HİÇ gelmedi (ağ/iptal) — sunucunun sustuğu hâl. */
  readonly kod: number;
  /** FastAPI `detail` alanı. Okunamadıysa `null` — boş dizge YAZILMAZ (yalan olurdu). */
  readonly detay: string | null;
  /** Başarı gövdesi (ör. `{ok, expires_in}`). Ayrıştırılamadıysa `null`. */
  readonly govde: unknown;
}

function detaydanMetin(g: unknown): string | null {
  if (g === null || typeof g !== "object") return null;
  const d = (g as { detail?: unknown }).detail;
  if (typeof d === "string" && d.trim() !== "") return d;
  // FastAPI doğrulama hatası `detail`i bir DİZİDİR ({loc,msg,type} nesneleri). Düz
  // metne indirgerken `msg` alanlarını birleştiriyoruz; hiçbiri yoksa null döneriz.
  if (Array.isArray(d)) {
    const m = d
      .map((x) => (x !== null && typeof x === "object" ? (x as { msg?: unknown }).msg : null))
      .filter((x): x is string => typeof x === "string");
    if (m.length > 0) return m.join(" · ");
  }
  return null;
}

/** Tek POST. Ne fırlatır ne yutar: her hâl dönüş nesnesinde ADIYLA durur. */
export async function apiPost(yol: string, govde?: unknown): Promise<GonderSonucu> {
  let y: Response;
  try {
    y = await fetch(yol, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(govde ?? {}),
    });
  } catch (e) {
    // AĞ DÜŞMESİ BİR HTTP CEVABI DEĞİLDİR ve öyle gösterilemez: `kod: 0` ile
    // "sunucu bir şey söyledi" hâlinden ayrılır, mesaj tarayıcının kendi metnidir.
    return { ok: false, kod: 0, detay: e instanceof Error ? e.message : String(e), govde: null };
  }

  let cozulen: unknown = null;
  try {
    cozulen = await y.json();
  } catch {
    // YASA 4 · sessiz-yutma İŞARETLİ: gövde JSON değilse (proxy'nin düz metin 502'si,
    // Caddy'nin hata sayfası) ayrıştırma hatası ASIL sonucu gizlememeli — durum kodu
    // zaten `kod` alanında taşınıyor ve çağıranın dallanması için yeterli.
  }

  return { ok: y.ok, kod: y.status, detay: detaydanMetin(cozulen), govde: y.ok ? cozulen : null };
}
