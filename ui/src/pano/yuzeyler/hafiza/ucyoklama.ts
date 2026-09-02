"use client";

/* ============================================================================
   UÇ YOKLAMASI — JSON DÖNDÜRMEYEN bir sunum ucu gerçekten cevap veriyor mu?
   ----------------------------------------------------------------------------
   Bir bağın "çalışıyor" diye yazılması bir İDDİADIR; bu kanca onu bir ÖLÇÜME
   çevirir. Tek tüketicisi Hafıza yüzeyinin Belgeler görünümündeki belge kaynağı
   şerididir (`Belgeler.tsx`) ve orada `/runbook` yoklanır.

   NEREDEN GELDİ: kanca eski "Belgeler" rafı yüzeyindeydi. Raf 2026-09-02'de
   kalktı ve kanca bir tur boyunca okuyucusuz kaldı; okuyucusuz kod üretilmemiş
   artefaktla aynı sınıftır (Yasa 6) ve o turda silinmişti. Aynı turun incelemesi
   kaybı "düşen çıktı" olarak saydı (bedel yasası) ve ölçüm okuyucusuyla birlikte
   GERİ KONDU — artık hafıza yüzeyinin belge kaynağı şeridinde yaşıyor.

   GÖVDE İNDİRİLMEZ: `/runbook` her istekte bir markdown belgesini HTML sayfasına
   çeviriyor (api.py::runbook) ve biz yalnız "cevap veriyor mu" sorusunu
   soruyoruz. ÖLÇÜLDÜ (2026-08-25): `docs/RUNBOOK.md` 184 776 bayt → sunulan sayfa
   238 785 bayt. Rakam tarihiyle duruyor; tarihsiz bir rakam bayatladığında bunu
   söyleyemez.

   HEAD KENDİLİĞİNDEN GELMEZ — ve bunun tersini varsaymak canlıda 405'in KÖK
   NEDENİYDİ. Doğru ölçüt: FastAPI'de `@app.get` YALNIZ GET kaydeder. Starlette'in
   düz `Route`u HEAD'i kendisi ekler, ama FastAPI'nin `APIRoute`u EKLEMEZ;
   `/runbook` bu yüzden ayrı bir `@app.head` ile de kayıtlı (api.py::runbook). Bu
   kancayla YENİ bir uç yoklanacaksa o uçta da HEAD AYRICA kaydedilmeli, yoksa
   şerit, belge yerinde dururken satırı kırmızı yakar.
   ============================================================================ */
import { useEffect, useState } from "react";

export interface UcYoklamasi {
  /** `null` = henüz ölçülmedi (yoklama sürüyor ya da hiç koşmadı). */
  readonly kod: number | null;
  readonly ok: boolean | null;
  readonly hata: string | null;
}

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
