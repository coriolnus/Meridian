/* ============================================================================
   YAZAN İSTEKLER — kimlik kapısının dört ucu (`veri.ts` yalnız OKUYOR)
   ----------------------------------------------------------------------------
   `veri.ts::apiGet` bu panonun tek okuma kapısı ve BİLEREK yalnız GET yapıyor.
   Kimlik kapısı ise üç POST istiyor (`/api/login`, `/api/setup-password`,
   `/api/logout`) ve bunların hata yüzeyi bir GET'inkinden BAŞKA: burada 401
   "oturum düştü" DEĞİL "parola hatalı"dır, 409 "kurulum zaten yapılmış"tır ve
   429 "kaba-kuvvet kilidi"dir. Üçünü tek bir `hata: string` alanına ezmek,
   operatöre yanlış işi yaptırırdı (yeniden giriş / kabuktan sıfırlama / bekleme
   — üç ayrı çare).

   BU YÜZDEN DÖNÜŞ HTTP KODUNU TAŞIR. Çağıran koda göre dallanır; metni uydurmaz,
   sunucunun `detail`ini basar. Kod okunamadıysa (ağ düştü) `kod: 0` döner ve bu
   "sunucu bir şey söyledi" hâlinden AYRI durur — 0 bir HTTP kodu değildir, tam da
   bu yüzden seçildi.

   ÖLÇÜLEN SÖZLEŞME (`meridian/api.py`, okundu — tahmin değil):
     · POST /api/login          gövde {"password": str} → 200 {ok, expires_in}
                                401 {detail:"parola hatalı"} · 429 {detail:"cok fazla deneme — N sn sonra"}
     · POST /api/setup-password gövde {"password": str} → 200 {ok}
                                409 {detail:"parola zaten kurulu"} · 400 {detail:<ValueError metni>}
     · POST /api/logout         gövde YOK → 200 {ok:true}; yetki İSTEMEZ
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
