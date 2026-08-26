"use client";

/* ============================================================================
   BELGELER — "ne öğrenildi ve nereye yazıldı?"
   ----------------------------------------------------------------------------
   İKİ BÖLÜM, İKİ AYRI DURUM ve ekran ikisini KARIŞTIRMIYOR:
     · HAFIZA (`bolum-hafiza`)   — GERÇEK ve okunuyor. `GET /api/memory` →
       `state/lessons.md` ham metni; burada belge olarak çiziliyor, aranıyor,
       bölüm dökümü çıkarılıyor.
     · KARAR BELGELERİ (`bolum-belgeler`) — ARTIK SUNULUYOR (2026-08-25 turu).
       Yukarıdaki cümle "uç `api.py`de yok" diyordu ve o gün DOĞRUYDU; uç aynı turda
       eklendi (`api.py::api_karar_belgeleri`). BAYAT BEYAN SİLİNMEZ, DÜZELTİLİR:
       panonun kendi ucunu yalanlaması, olmayan bir uçtan daha kötüdür — okuyucu
       ekrana değil yorumun tarihine güvenmek zorunda kalır.

   NEDEN DOSYA YÖNETİCİSİ GRAMERİ AMA IZGARA YOK: şablonun file-manager sayfası
   ızgara/liste ikilisiyle geliyor; ızgara kutusu "burada N dosya var" der. Bugün
   panonun sayabildiği dosya BİR TANE (lessons.md). Tek kutuluk bir ızgara,
   grameri taşımak uğruna boşluğu süslemek olurdu — bölüm dökümü tablosu ve
   ağırlık grafiği aynı yerde daha çok şey ölçüyor.

   NABIZ YOK: `lessons.md` bir yansıma turunda bir kez yazılıyor; 15 saniyede bir
   çekmek okunan bir belgeyi altından kaydırmak olurdu.
   ============================================================================ */
import { useEffect } from "react";

import { BookOpen, FileText, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { useApi } from "../veri";
import { Hafiza } from "./belgeler/Hafiza";
import { KararBelgeleri } from "./belgeler/KararBelgeleri";
import { Kapi, metin } from "./belgeler/ortak";

export function Belgeler() {
  const y = YUZEYLER["file-manager"];
  const { bolum } = useRota();
  const hafiza = useApi<Record<string, unknown>>("/api/memory", 0);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const ham = metin(hafiza.veri?.["lessons_md"]);
  // "Okundu" iddiası GÖVDEYE bakar, isteğin başarısına değil: 200 dönen ama
  // `lessons_md` taşımayan bir yanıt "okundu" DEĞİLDİR (boş gövde ≠ her şey yolunda).
  const hafizaOk = ham !== null;
  const hafizaNeden = hafiza.oturumDustu
    ? "`/api/memory` 401 döndü — oturum düştü"
    : ham === null
      ? (hafiza.hata ?? "`/api/memory` gövdesinde `lessons_md` alanı yok")
      : null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        <Button variant="outline" size="sm" onClick={hafiza.tazele}>
          <RefreshCw className="size-3.5" aria-hidden />
          Tazele
        </Button>
      </div>

      <Card id="bolum-hafiza" className="scroll-mt-20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            Hafıza
          </CardTitle>
          <CardDescription>lessons.md ne biriktirdi?</CardDescription>
        </CardHeader>
        <CardContent>
          <Kapi durum={hafiza} ad="`/api/memory`" yukseklik="h-80">
            {() =>
              ham === null ? (
                // 200 GELDİ AMA ALAN YOK: bu bir ağ hatası değil, bir SÖZLEŞME
                // ihlali; ikisini aynı kutuya koymak operatörü ağa baktırırdı.
                <p className="text-muted-foreground text-sm">
                  `/api/memory` cevap verdi ama gövdesinde `lessons_md` alanı yok. Bu "hafıza boş"
                  DEĞİL — uç sözleşmesi bu alanı her zaman yazmalı (api.py::api_memory).
                </p>
              ) : (
                <Hafiza ham={ham} />
              )
            }
          </Kapi>
        </CardContent>
      </Card>

      <Card id="bolum-belgeler" className="scroll-mt-20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            Karar belgeleri
          </CardTitle>
          <CardDescription>Hangi karar hangi turda verildi?</CardDescription>
        </CardHeader>
        <CardContent>
          <KararBelgeleri hafizaOk={hafizaOk} hafizaNeden={hafizaNeden} />
        </CardContent>
      </Card>
    </div>
  );
}
