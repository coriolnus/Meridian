"use client";

/* ============================================================================
   GENEL YÜZEY — bir yüzeyin başlığı + bölümlerinin sırası
   ----------------------------------------------------------------------------
   Bölüm gövdeleri henüz TAŞINMADI ve bu ekranda AÇIKÇA yazıyor. Boş bir kart
   çizip geçmek operatöre "bu bölümde bir şey yok" derdi; doğru cümle "bu bölüm
   henüz yeni panoya taşınmadı, eskisinde duruyor" — ve yanında oraya giden bağ.
   Göç bitene kadar bu kartlar bir SAYAÇTIR: kaç bölüm kaldığı ekrandan okunur,
   bir belgeden değil.

   BÖLÜMSÜZ YÜZEYLER (Ajan · Operatör · Evren) burada yalnız başlığını gösterir;
   onların gövdesi kendi turunda gelecek ve o tur geldiğinde bu bileşen değil,
   yüzeye özel bir bileşen çizecek (bkz. `yuzeyler/index.ts` tablosu).
   ============================================================================ */
import { ArrowUpRight } from "lucide-react";
import { useEffect } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";

export function GenelYuzey() {
  const { yuzey, bolum } = useRota();
  const y = YUZEYLER[yuzey];

  // ÇAPAYA KAYDIR: `#/dashboard/infrastructure/market` bağı sayfayı açmakla kalmaz,
  // bölümü de gösterir. Eski panoda çapa hash'e hiç yazılmıyordu (app.js:682 onu
  // yutuyordu) — yani bu bir kayıp değil, kazanç.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [yuzey, bolum]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
      </div>

      {y.bolumler.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Bu yüzey henüz taşınmadı</CardTitle>
            <CardDescription>
              Gövdesi kendi turunda gelecek. O zamana kadar aynı soruların cevabı eski panoda duruyor.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {y.bolumler.map((b) => (
            <Card key={b.kimlik} id={`bolum-${b.kimlik}`} className="scroll-mt-20">
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <CardTitle className="flex items-center gap-2">
                      <b.ikon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                      {b.baslik}
                    </CardTitle>
                    <CardDescription className="mt-1">{b.soru}</CardDescription>
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    taşınmadı
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <a
                  className="inline-flex items-center gap-1 text-primary text-sm underline-offset-4 hover:underline"
                  href={`/#${b.kimlik}`}
                >
                  Bu bölüm eski panoda <ArrowUpRight className="size-3.5" aria-hidden />
                </a>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
