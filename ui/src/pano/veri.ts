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

/** Bir ucu okur ve (istenirse) periyodik tazeler. Dönen nesne ÜÇ HÂLİ de ayrı taşır. */
export function useApi<T>(yol: string | null, periyotMs = 0): Durum<T> {
  const [veri, setVeri] = useState<T | null>(null);
  const [yukleniyor, setYukleniyor] = useState<boolean>(yol !== null);
  const [hata, setHata] = useState<string | null>(null);
  const [oturumDustu, setOturumDustu] = useState(false);
  const [zaman, setZaman] = useState<Date | null>(null);
  const [tetik, setTetik] = useState(0);
  const iptal = useRef<AbortController | null>(null);

  const tazele = useCallback(() => setTetik((n) => n + 1), []);

  useEffect(() => {
    if (!yol) return;
    let canli = true;
    iptal.current?.abort();
    const kontrol = new AbortController();
    iptal.current = kontrol;

    setYukleniyor(true);
    apiGet<T>(yol, kontrol.signal)
      .then((d) => {
        if (!canli) return;
        setVeri(d);
        setHata(null);
        setOturumDustu(false);
        setZaman(new Date());
      })
      .catch((e: unknown) => {
        if (!canli || kontrol.signal.aborted) return;
        if (e instanceof OturumHatasi) {
          setOturumDustu(true);
          setHata(null);
          return;
        }
        // ESKİ VERİ SİLİNMEZ ama TAZE SAYILMAZ: `zaman` olduğu yerde kalır, `hata` dolar.
        // Silmek, bir ağ hıçkırığında ekrandaki her sayıyı boşaltmak olurdu; taze saymak
        // ise bayat sayıyı canlı diye okutmak. İkisi de yanlış; ayrı tutmak doğru.
        setHata(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (canli) setYukleniyor(false);
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

  return { veri, yukleniyor, hata, oturumDustu, zaman, tazele };
}

/** Panonun nabız periyodu — eski panoyla AYNI (app.js `refreshStatus`, 15 sn). */
export const NABIZ_MS = 15_000;
