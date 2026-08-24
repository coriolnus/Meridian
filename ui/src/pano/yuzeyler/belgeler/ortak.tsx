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

/** Bir sunum ucunu HEAD ile yoklar. Gövde İNDİRİLMEZ: `/runbook` ölçülen 163 KB'lık
 *  bir markdown'ı her istekte HTML'e çeviriyor (api.py:1094) ve biz yalnız "cevap
 *  veriyor mu" sorusunu soruyoruz. Starlette GET rotalarına HEAD'i kendisi ekler. */
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
