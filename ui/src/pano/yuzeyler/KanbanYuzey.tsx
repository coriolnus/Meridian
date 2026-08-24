"use client";

/* ============================================================================
   KANBAN YÜZEYİ — iki tahta, tek sekme çubuğu
   ----------------------------------------------------------------------------
   SEKME 1 · KARAR ZİNCİRİ: sistemin gece verdiği kararlar (aday → kapı → hüküm).
   SEKME 2 · YOL HARİTASI: bizim verdiğimiz kararlar (ne yapılacak, hangi bölümde).
   İkisi aynı yüzeyde çünkü ikisi de AYNI GRAMERİN tahtası (kolon + kart + sayaç)
   ve operatör ikisini de "neyin nerede takıldığı" sorusuyla okuyor. Ayrı yüzeylere
   bölmek kenar çubuğuna iki satır daha eklerdi; gezinme ağacı şablonundur ve
   şişirilmiyor (`alanlar.ts` başlığı).

   HİÇBİRİNDE SÜRÜKLEME YOK ve iki ayrı gerekçeyle:
     · karar zincirinde kartı taşımak KAPI HÜKMÜNÜ elle değiştirmek olurdu;
     · yol haritasında yazma ucu YOK — taşıma hiçbir yere kaydedilmezdi.
   İkisinin de sebebi ekranda yazılı (kart altı şerhi / "salt okunur" rozeti).

   DERİN BAĞ SEKMEYİ DE AÇAR: `#/dashboard/kanban/kapilar` yalnız kaydırmaz, o
   bölümün DURDUĞU sekmeyi seçer. Seçmeseydi bağ, kapalı bir sekmenin içindeki
   çapaya kayıp gitmeye çalışırdı — operatör bağı tıklar, hiçbir şey olmaz.
   ============================================================================ */
import { useEffect, useState } from "react";

import { Kanban as KanbanIkonu, Map as MapIkonu } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { KararZinciri } from "./kanban/KararZinciri";
import { YolHaritasi } from "./kanban/YolHaritasi";

/** Hangi bölüm hangi sekmede duruyor. `adaylar`/`kapilar` `alanlar.ts`teki kayıtlı
 *  bölümler; `roadmap` bu yüzeyin kendi çapası (kayıtta bölüm olarak durmuyor —
 *  kayıt dosyası bana kapalı, çapayı burada tanımlıyorum ki bağ yine de çalışsın). */
const BOLUM_SEKMESI: Record<string, "zincir" | "roadmap"> = {
  adaylar: "zincir",
  kapilar: "zincir",
  roadmap: "roadmap",
};

export function KanbanYuzey() {
  const { bolum } = useRota();
  const y = YUZEYLER.kanban;
  const [sekme, setSekme] = useState<"zincir" | "roadmap">(() => BOLUM_SEKMESI[bolum] ?? "zincir");

  useEffect(() => {
    const hedef = BOLUM_SEKMESI[bolum];
    if (hedef) setSekme(hedef);
  }, [bolum]);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    // SEKME GEÇİŞİNDEN SONRA kaydır: `TabsContent` etkin olmayan sekmede DOM'da
    // olmayabilir, bu yüzden aynı turda `getElementById` boş döner. Bir kare
    // beklemek (rAF) sekmenin gövdesi bağlandıktan sonra çapayı bulmayı garantiler.
    const kare = window.requestAnimationFrame(() => {
      document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return () => window.cancelAnimationFrame(kare);
  }, [bolum, sekme]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
      </div>

      <Tabs value={sekme} onValueChange={(v) => setSekme(v === "roadmap" ? "roadmap" : "zincir")}>
        <TabsList>
          <TabsTrigger value="zincir">
            <KanbanIkonu className="size-3.5" aria-hidden />
            Karar zinciri
          </TabsTrigger>
          <TabsTrigger value="roadmap">
            <MapIkonu className="size-3.5" aria-hidden />
            Yol haritası
          </TabsTrigger>
        </TabsList>

        <TabsContent value="zincir" className="mt-2">
          <KararZinciri />
        </TabsContent>
        <TabsContent value="roadmap" className="mt-2">
          <YolHaritasi />
        </TabsContent>
      </Tabs>
    </div>
  );
}
