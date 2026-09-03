/* ============================================================================
   VERİ KATMANI — FastAPI uçlarına tek kapı
   ----------------------------------------------------------------------------
   Pano SUNUCUDA render edilmiyor: sayfa statik olarak sunuluyor (FastAPI,
   `meridian/api.py`), veri tarayıcıda `/api/*`ten çekiliyor. Bu yüzden "yükleniyor",
   "boş" ve "okunamadı" ÜÇ AYRI HÂLDİR ve üçü de tipte ayrı durur.

   UYDURMA YASAĞI BURADA BAŞLAR (CLAUDE.md §4): ölçülemeyen bir değer `null` döner
   ve NEDENİNİ taşır. Bir isteğin düşmesi sessizce boş bir kart çizdirmez — boş kart,
   okuyucuya "ölçtük, hiçbir şey yok" der ve bu bir yalandır. `hata` alanı doluyken
   çizen bileşen bunu yazmak ZORUNDA.

   OTURUM DÜŞMESİ AYRI BİR HÂL: pano parola kapısının arkasında (api.py::_auth) ve
   oturum süresi dolduğunda uçlar 401 döner. Bunu "veri okunamadı" diye göstermek
   operatörü yanlış yere — ağa, sunucuya — bakmaya gönderirdi.
   ============================================================================ */
import { useCallback, useEffect, useRef, useState } from "react";

export interface Durum<T> {
  readonly veri: T | null;
  readonly yukleniyor: boolean;
  /** Okunamadıysa NEDENİ. `null` iken veri güvenilir. */
  readonly hata: string | null;
  /** 401 — oturum düşmüş. `hata`dan AYRI: çaresi farklı (yeniden giriş, tazeleme değil). */
  readonly oturumDustu: boolean;
  /** Son başarılı okumanın zamanı; hiç okunmadıysa `null`. */
  readonly zaman: Date | null;
  readonly tazele: () => void;
}

export class OturumHatasi extends Error {}

/**
 * RET GÖVDESİNİN CÜMLESİ — ÜÇ AD, TEK OKUYUCU.
 *
 * GÖVDE OKUNUR ÇÜNKÜ TEŞHİS ORADA: sunucunun hata gövdeleri "dağıtım eksik",
 * "sunulan kümede YOK" gibi cümleler taşıyor ve o cümle operatörü doğru yere
 * gönderiyor. Yutmak, "500" yazıp teşhisi çöpe atmak olurdu.
 *
 * SIRA GERİYE DÖNÜK UYUMLUDUR VE CÜMLEYLE YAZILI (inceleme, düzeltme turu 1):
 * `detail` ve `error` ESKİ adlardır ve ikisinden biri varsa KAZANIR; `neden`
 * ancak ikisi de yokken devreye girer, yani hiçbir mevcut uçta gösterilen mesaj
 * DEĞİŞMEZ. Üçüncü ad bir ölçüm sonucu (TSK-112): hafıza vekilinin tek 4xx
 * döndüren okuma ucu (`api.py::api_hindsight_varlik`) gerekçesini kendi zarf
 * adıyla taşıyor — iki ada bakan bir okuyucu o cümleyi yutar ve ekranda yalnız
 * durum kodu kalırdı ("kimlik reddedildi" ile "sunucu düştü" ayırt edilemezdi).
 *
 * TEK KAPI, ÇÜNKÜ İKİNCİ KOPYA GERİDE KALDI (inceleme I-2): aynı dört satır
 * `Recall.tsx`in kendi gönderiminde de yaşıyordu ve üçüncü adı ÖĞRENMEMİŞTİ.
 * "Ret gövdesi neye benzer" tek bir gerçektir; iki kopyası sessizce ayrışır.
 */
export function hataEki(govde: unknown): string {
  const g = govde as { detail?: unknown; error?: unknown; neden?: unknown } | null | undefined;
  const d = g?.detail ?? g?.error ?? g?.neden;
  return typeof d === "string" ? ` — ${d}` : "";
}

export async function apiGet<T>(yol: string, signal?: AbortSignal): Promise<T> {
  const y = await fetch(yol, { signal, credentials: "same-origin", headers: { Accept: "application/json" } });
  if (y.status === 401) throw new OturumHatasi("oturum düştü");
  if (!y.ok) {
    let ek = "";
    try {
      ek = hataEki(await y.json());
    } catch {
      // YASA 4 · sessiz-yutma İŞARETLİ: gövde JSON değilse (proxy'nin düz metin 502'si,
      // Caddy'nin kendi hata sayfası) ayrıştırma hatası ASIL hatayı gizlememeli; durum
      // kodu zaten aşağıda yazılıyor ve teşhis için yeterli.
    }
    throw new Error(`${yol} → HTTP ${y.status}${ek}`);
  }
  return (await y.json()) as T;
}

/**
 * BAYAT GÖVDE SINIFI (TSK-110, ölçüm TSK-108 T3 M-7): `veri`/`hata` eskiden `yol`dan BAĞIMSIZ
 * durumlardı. Çekmece/kapı yeniden açılıp `yol` A→B değişince yeni istek bitene kadar `veri`
 * A'nınkini taşırdı — tüketici ("veri !== null → children(veri)") A'nın gövdesini B'nin başlığı
 * altında çizerdi. Alt bileşene `key` vermek çözmez, çünkü hook EBEVEYNDE yaşıyor (key ebeveyni
 * yeniden kurmaz). Aynı sınıf `hata` için de geçerliydi: eski yolun "okunamadı" metni yeni yolun
 * altında görünürdü.
 *
 * ÇARE — TÜRETİM, SIFIRLAMA DEĞİL: iç durum yol-bağlı KAYDA döner (`okuma` = {yol, veri, zaman}
 * TEK atomik kayıt; `hataKaydi` = {yol, metin} TEK kayıt) ve DIŞARI VERİLEN `veri`/`hata`/`zaman`
 * her render'da `okuma.yol === yol` / `hataKaydi.yol === yol` eşitliğiyle TÜRETİLİR. Efektte
 * `yol` değiştiğinde `setOkuma(null)` ÇAĞRILMAZ — sıfırlama React'ın boyama SIRASINDA değil
 * SONRA koşan bir efektte olurdu ve bu bir kare (boyama → efekt) bayat gövde çizdirirdi (TSK-112
 * `cekmeceAnahtari`nin RENDER sırasında ilerlemesiyle AYNI ders — Varliklar.tsx). Türetim ise
 * yeni `yol` geldiği ANKİ render'da zaten `okuma.yol !== yol` olduğu için `null` döner; ara kare
 * yoktur.
 *
 * KORUNAN SÖZLEŞMELER (brief TSK-110, madde madde):
 * (1) AYNI yolun tazelemesi düşerse eski veri SİLİNMEZ, taze SAYILMAZ — `hataKaydi` dolar,
 *     `okuma` (dolayısıyla `zaman`) olduğu yerde kalır. Bir ağ hıçkırığında ekranı boşaltmak da
 *     yanlış, bayatı taze diye okutmak da yanlış; ayrı tutmak doğru (eski şerh aynen).
 * (2) FARKLI yola geçince (`okuma.yol !== yol`) eski veri/hata GÖRÜNMEZ — tüketiciye `null` gider,
 *     `Kapi` iskelet/yükleniyor çizer. `okuma`/`hataKaydi` kaydın kendisi bellekte kalabilir (yeni
 *     yol için gövde henüz gelmedi) ama TÜRETİLEN alan onu dışarı sızdırmaz.
 *     TEK-SLOT KAYIT, YOL-BAŞINA ÖNBELLEK DEĞİL (inceleme ⚠️, düzeltme turu 1, 2026-09-03): `okuma`/
 *     `hataKaydi` yalnız EN SON tamamlanan isteğin kaydını tutar. A→B→A geçişinde B başarıyla
 *     dönerse `okuma.yol` B'ye geçer; A'ya dönüldüğünde `okuma.yol(=B) !== A` olduğu için A'nın
 *     ESKİ gövdesi GERİ GELMEZ — A yeniden "yükleniyor" görünür, B'nin gövdesiyle DEĞİL (çapraz-yol
 *     sızıntısı yok, madde-(2) ile çelişmez — tersine daha muhafazakâr). "Aynı yolun son başarılı
 *     okuması" ifadesi yol-başına-ayrı-cache izlenimi verebilirdi; gerçek davranış öyle değil.
 * (3) `yol === null` → türetilen veri/zaman/hata hepsi `null` (eşitlik zaten `yol !== null` şartı
 *     taşıyor).
 * (4) `oturumDustu` yoldan BAĞIMSIZ kalır — 401 küreseldir (oturum kapısı tek, hangi uç düşürdüğü
 *     önemsiz), yol-bağlı kayda taşınmaz.
 * (5) `periyotMs` tazelemesi aynı yolda çalışır; davranış değişmedi (tetik → aynı `yol` için efekt
 *     yeniden koşar → `okuma.yol === yol` zaten doğru kalır, yalnız `zaman` ilerler).
 * (6) `apiGet`/`hataEki`/`OturumHatasi`/`NABIZ_MS` DOKUNULMADI.
 *
 * `Durum<T>` ARAYÜZÜ SABİT: altı alan aynen (veri·yukleniyor·hata·oturumDustu·zaman·tazele) —
 * bu satırın altında hiçbir tüketici ve hiçbir `Kapi` gövdesi dokunulmadı.
 * KOPYA SAYISI 1'DİR (TSK-113, 2026-09-03): `function Kapi<` tanımı taşıyan YEDİ dosya
 * (sistem/kuyruk/kimlik/yetki `parcalar.tsx` + ogrenme/ajan/analiz `ortak.tsx`) TEK tanıma indi —
 * `parcalar/kapi.tsx`. Yedi yüzey artık yalnız kabuk bağlar ve `Kapi`yi yeniden dışa aktarır.
 * ÖNCEKİ KAYIT BURADA "KOPYA SAYISI 7'DİR … birleştirilmesi AYRI bir ROADMAP kalemi" diyordu;
 * o kalem KAPANDI ve cümle bayatladı (tek-kaynak yasası: aynı gerçeğin iki kopyası sessizce
 * ayrışır — bu satır ayrışmanın kendisiydi). Sayının çivisi `tests/test_kovab_b12_v384.py` +
 * `tests/test_pano_bayat_govde_v381.py` (dinamik tarama, `== 1`).
 *
 * `yukleniyor` DE TÜRETİLİR, DÜZ EFEKT-STATE DEĞİL (inceleme Önemli-2, düzeltme turu 1): `yol`
 * değiştiği ANDA (aynı render'da) efekt henüz koşmamıştır — efekt render'dan SONRA çalışır — ve
 * o anki render'da `guncel`/`hata` zaten (doğru biçimde) `null`e düşmüştür. Yalnız efekt-state'e
 * (`yukleniyorDurumu`) güvenmek bir kare "veri=null (doğru) + yukleniyor=false (henüz
 * güncellenmemiş) + hata=null" görünmesine yol açardı — `Kapi` bu kareyi YANLIŞ veri göstermeden
 * ama iskeleti VE yükleniyor göstergesini birlikte kapatarak geçirirdi. `yukleniyorDurumu ||
 * (bu yol için ne okuma ne hata var)` türetimi bu kareyi kapatır.
 */
export function useApi<T>(yol: string | null, periyotMs = 0): Durum<T> {
  const [okuma, setOkuma] = useState<{ readonly yol: string; readonly veri: T; readonly zaman: Date } | null>(null);
  const [hataKaydi, setHataKaydi] = useState<{ readonly yol: string; readonly metin: string } | null>(null);
  // Ham efekt bayrağı — DIŞARI VERİLEN `yukleniyor` bu DEĞİL, aşağıda türetilen hâli (şerh yukarıda).
  const [yukleniyorDurumu, setYukleniyorDurumu] = useState<boolean>(yol !== null);
  const [oturumDustu, setOturumDustu] = useState(false);
  const [tetik, setTetik] = useState(0);
  const iptal = useRef<AbortController | null>(null);

  const tazele = useCallback(() => setTetik((n) => n + 1), []);

  useEffect(() => {
    if (!yol) return;
    let canli = true;
    iptal.current?.abort();
    const kontrol = new AbortController();
    iptal.current = kontrol;

    setYukleniyorDurumu(true);
    apiGet<T>(yol, kontrol.signal)
      .then((d) => {
        if (!canli) return;
        setOkuma({ yol, veri: d, zaman: new Date() });
        setHataKaydi(null);
        setOturumDustu(false);
      })
      .catch((e: unknown) => {
        if (!canli || kontrol.signal.aborted) return;
        if (e instanceof OturumHatasi) {
          setOturumDustu(true);
          setHataKaydi(null);
          return;
        }
        // ESKİ VERİ SİLİNMEZ ama TAZE SAYILMAZ: `okuma` (ve dolayısıyla `zaman`) olduğu yerde
        // kalır, `hataKaydi` bu yolla dolar. Silmek, bir ağ hıçkırığında ekrandaki her sayıyı
        // boşaltmak olurdu; taze saymak ise bayat sayıyı canlı diye okutmak. İkisi de yanlış;
        // ayrı tutmak doğru.
        setHataKaydi({ yol, metin: e instanceof Error ? e.message : String(e) });
      })
      .finally(() => {
        if (canli) setYukleniyorDurumu(false);
      });

    return () => {
      canli = false;
      kontrol.abort();
    };
  }, [yol, tetik]);

  useEffect(() => {
    if (!yol || periyotMs <= 0) return;
    const t = window.setInterval(tazele, periyotMs);
    return () => window.clearInterval(t);
  }, [yol, periyotMs, tazele]);

  // TÜRETİM (sıfırlama DEĞİL — yukarıdaki şerh): kayıt hâlâ eski yola aitse dışarı sızmaz.
  const guncel = yol !== null && okuma !== null && okuma.yol === yol ? okuma : null;
  const hata = yol !== null && hataKaydi !== null && hataKaydi.yol === yol ? hataKaydi.metin : null;
  // TEK KARE İSKELET-FLAŞI KAPATILIYOR (şerh yukarıda): bu yol için ne okuma ne hata varsa
  // efekt henüz koşmamış olsa BİLE "okuma sürüyor" sayılır.
  const yukleniyor = yukleniyorDurumu || (yol !== null && guncel === null && hata === null && !oturumDustu);

  return { veri: guncel?.veri ?? null, yukleniyor, hata, oturumDustu, zaman: guncel?.zaman ?? null, tazele };
}

/** Panonun nabız periyodu — eski panoyla AYNI (app.js `refreshStatus`, 15 sn). */
export const NABIZ_MS = 15_000;
