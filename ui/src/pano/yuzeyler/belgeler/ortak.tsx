"use client";

/* ============================================================================
   BELGELER YÜZEYİNİN ORTAK PARÇALARI
   ----------------------------------------------------------------------------
   DÜRÜSTLÜK İLKELERİ TEK YERDEN GELİYOR: `Kapi` (dört hâl) ve `Olculemedi`
   (ölçülemeyen değerin yeri) bu turda Ajan yüzeyiyle BİRLİKTE yazıldı ve iki
   yüzey de aynı uçlara (`/api/memory`) bakıyor. İkinci bir kopya yazmak, aynı
   sözleşmenin iki uygulaması demekti — biri güncellenip diğeri unutulduğunda
   panonun bir yarısı "ölçülemedi" derken öbür yarısı sessizce 0 basardı.
   Buradaki yeniden dışa aktarım, o çatallanmayı en baştan imkânsız kılıyor.

   YEREL EK: `useUcYoklama` — JSON DÖNDÜRMEYEN bir sunum ucunun (örn. `/runbook`
   bir HTML sayfasıdır) gerçekten cevap verip vermediğini ölçer. Bir bağın
   "çalışıyor" diye yazılması bir İDDİADIR; bu kanca onu bir ÖLÇÜME çevirir.
   ============================================================================ */
import { useEffect, useState } from "react";

export { Deger, Kapi, Olculemedi, OlculemediBlok, bicimSayi, dizi, metin, nesne, say, zamanMetni } from "../ajan/ortak";

export interface UcYoklamasi {
  /** `null` = henüz ölçülmedi (yoklama sürüyor ya da hiç koşmadı). */
  readonly kod: number | null;
  readonly ok: boolean | null;
  readonly hata: string | null;
}

/** Bir sunum ucunu HEAD ile yoklar. GÖVDE İNDİRİLMEZ: `/runbook` her istekte bir markdown
 *  belgesini HTML sayfasına çeviriyor (api.py::runbook) ve biz yalnız "cevap veriyor mu"
 *  sorusunu soruyoruz. ÖLÇÜLDÜ (2026-08-25): `docs/RUNBOOK.md` 184 776 bayt → sunulan sayfa
 *  238 785 bayt. Rakam tarihiyle duruyor; tarihsiz bir rakam bayatladığında bunu söyleyemez.
 *
 *  HEAD KENDİLİĞİNDEN GELMEZ — ve bunun tersini varsaymak canlıda 405'in KÖK NEDENİYDİ. Doğru
 *  ölçüt: FastAPI'de `@app.get` YALNIZ GET kaydeder. Starlette'in düz `Route`u HEAD'i kendisi
 *  ekler, ama FastAPI'nin `APIRoute`u EKLEMEZ; `/runbook` bu yüzden ayrı bir `@app.head` ile de
 *  kayıtlı (api.py::runbook). Bu kancayla YENİ bir uç yoklanacaksa o uçta da HEAD AYRICA
 *  kaydedilmeli, yoksa raf, belge yerinde dururken satırı kırmızı yakar. */
export function useUcYoklama(yol: string): UcYoklamasi {
  const [durum, setDurum] = useState<UcYoklamasi>({ kod: null, ok: null, hata: null });

  useEffect(() => {
    let canli = true;
    const kontrol = new AbortController();
    fetch(yol, { method: "HEAD", credentials: "same-origin", signal: kontrol.signal })
      .then((y) => {
        if (!canli) return;
        setDurum({ kod: y.status, ok: y.ok, hata: null });
      })
      .catch((e: unknown) => {
        if (!canli || kontrol.signal.aborted) return;
        // Yutma YOK: ağ hatası da bir ölçümdür ve nedeni ekranda yazılır.
        setDurum({ kod: null, ok: false, hata: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      canli = false;
      kontrol.abort();
    };
  }, [yol]);

  return durum;
}
