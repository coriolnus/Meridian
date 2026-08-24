"use client";

/* ============================================================================
   AÇIK POZİSYONLAR × TUTAR — bu yüzeyin merkezindeki grafik (operatör isteği)
   ----------------------------------------------------------------------------
   İKİ KANAL, İKİ SORU — ve BİRBİRİNE BİNDİRİLMEZ (operatörün açık kuralı):
     · ÇUBUK UZUNLUĞU = piyasa değeri (adet × son fiyat). Her zaman POZİTİF bir
       büyüklük. Kâr/zararla işaretlenseydi, 200$ zarardaki 50.000$'lık bir
       pozisyon ekranda 200$'lık bir çubuk olurdu — sermayenin nerede durduğu
       sorusu cevapsız kalırdı.
     · ÇUBUK RENGİ = açık K/Z'nin İŞARETİ (yeşil/kırmızı/nötr). Büyüklük taşımaz;
       yalnız yön. Ölçülemeyen K/Z'nin rengi yoktur — nötr griye düşer, çünkü
       "bilmiyoruz" yeşil de kırmızı da değildir.

   YATAY ÇUBUK SEÇİMİ TEKNİK: sembol sayısı değişken (bugün 7, yarın 12) ve
   etiket bir hisse kodudur. Dikey çubukta 12 kod eksende eğik yazılır ve okunmaz;
   yatayda her etiket kendi satırında düz durur. Yükseklik satır sayısıyla büyür,
   çubuk kalınlığı sabit kalır — 3 pozisyonluk bir portföy şişmiş görünmez.

   ÇİZİLEMEYEN SATIR GİZLENMEZ: piyasa değeri ölçülemeyen pozisyon grafiğe
   giremez (uzunluğu yok), ama grafiğin ALTINDA adıyla ve NEDENİYLE listelenir.
   Sessizce düşürmek, portföyü olduğundan küçük göstermek olurdu.
   ============================================================================ */
import { useMemo } from "react";
import { Bar, BarChart, Cell, LabelList, type LabelProps, XAxis, YAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

import type { PozisyonSatiri } from "./birlestir";
import { kzDolgusu, kzOrnegi, paraKisa } from "./olcum";

/** Tooltip'in satır adı buradan gelir (chart.tsx:252 `itemConfig?.label`). */
const GRAFIK_CONFIG = {
  tutar: { label: "Piyasa değeri (USD)" },
} satisfies ChartConfig;

interface Nokta {
  readonly ticker: string;
  readonly tutar: number;
  readonly etiket: string;
  readonly kz: number | null;
}

/** Değer etiketi çubuğun SAĞINDA, çizim alanının dışında. Şablonun
 *  `top-traffic-sources.tsx` kalıbı; `x="100%"` + `textAnchor="end"` ikilisi
 *  etiketi sağ kenara yaslar, `margin.right` ona yer açar. */
function tutarEtiketi(props: LabelProps) {
  const { height, value, y } = props;
  // GEOMETRİ GELMEDİYSE ÇİZME: `y`/`height` sayı değilse `Number(...)` NaN üretir
  // ve NaN bir SVG koordinatı olarak etiketi sessizce kaybettirir. Çizmemek,
  // görünmez bir yere çizmekten dürüsttür — eksik etiket boş yer olarak görünür.
  const yy = Number(y);
  const hh = Number(height);
  if (!Number.isFinite(yy) || !Number.isFinite(hh)) return null;
  return (
    <text
      className="fill-foreground tabular-nums"
      dominantBaseline="middle"
      dx={-4}
      fontSize={12}
      textAnchor="end"
      x="100%"
      y={yy + hh / 2}
    >
      {value}
    </text>
  );
}

export function PozisyonGrafigi({ satirlar }: { satirlar: readonly PozisyonSatiri[] }) {
  const cizilebilir = useMemo(
    () => satirlar.filter((s): s is PozisyonSatiri & { piyasaDegeri: number } => s.piyasaDegeri !== null),
    [satirlar],
  );
  const cizilemeyen = satirlar.filter((s) => s.piyasaDegeri === null);

  /* DİZİ KİMLİĞİ HER ÇİZİMDE YENİLENMEMELİ — ölçülmüş bir kusur (2026-08-25).
     Bu yüzey DÖRT ucu ayrı nabızlarla yokluyor; her yanıt bir yeniden çizim tetikliyor
     ve satır içi `.filter().sort().map()` her seferinde YENİ bir dizi üretiyordu.
     recharts yeni dizi kimliğini "veri değişti" sayıp giriş animasyonunu BAŞA SARIYOR:
     çubuklar 0'dan büyümeye başlıyor, bir sonraki yoklama gelince yine 0'a dönüyor.
     Ekranda görülen buydu — tarayıcıda üç ayrı anda 121 px, 74 px ve 0 px ölçüldü;
     veri her seferinde doğruydu, oturan bir kare hiç olmuyordu. */
  const veri: Nokta[] = useMemo(
    () =>
      [...cizilebilir]
        .sort((a, b) => b.piyasaDegeri - a.piyasaDegeri)
        .map((s) => ({ ticker: s.ticker, tutar: s.piyasaDegeri, etiket: paraKisa(s.piyasaDegeri), kz: s.acikKz })),
    [cizilebilir],
  );

  // YÜKSEKLİK SATIR SAYISIYLA BÜYÜR: sabit `aspect-video` (ChartContainer'ın
  // varsayılanı) 3 satırda kocaman boşluk, 14 satırda ezik çubuklar verirdi.
  // 44 px = 28 px çubuk + 16 px nefes; taban 160 px tek satırlık halde bile
  // tooltip'in sığacağı yüksekliktir.
  const yukseklik = Math.max(160, veri.length * 44 + 24);

  return (
    <div className="flex flex-col gap-4">
      {veri.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          {satirlar.length === 0
            ? "Açık pozisyon yok — iki defterin ikisi de boş. Bu bir ölçüm eksiği değil, ölçülmüş bir olgu."
            : `${satirlar.length} açık pozisyonun hiçbirinin piyasa değeri ölçülemedi; aşağıdaki listede her birinin nedeni var.`}
        </p>
      ) : (
        <ChartContainer config={GRAFIK_CONFIG} className="aspect-auto w-full" style={{ height: yukseklik }}>
          <BarChart accessibilityLayer data={veri} layout="vertical" margin={{ left: 0, right: 88, top: 4, bottom: 4 }}>
            <YAxis dataKey="ticker" hide tickLine={false} type="category" />
            {/* ALAN AÇIKÇA YAZILIYOR — ÖLÇÜLDÜ (2026-08-25, tarayıcıda).
                Alansız hâlde recharts'ın seçtiği üst sınır verinin en büyüğünün ~8
                katıydı: en uzun çubuk 1000 px'lik çizim alanının yalnız 121 px'ini
                kaplıyordu (14.500 $ · ölçek 119,6 $/px). Çubuklar teknik olarak
                doğruydu ama KIYAS İMKÂNSIZDI — bu grafiğin tek işi tutarları yan yana
                okutmak ve hepsi sol kenarda ezilmiş bir çizgiye dönüşmüştü.
                `dataMax` sıralı çubuk grafiğinin doğru tabanıdır: en büyük pozisyon
                genişliği belirler, geri kalan ona ORANLA okunur. Taban 0'da sabit —
                sıfırdan başlamayan bir çubuk boyu, oranı yalan söyler. */}
            <XAxis dataKey="tutar" domain={[0, "dataMax"]} hide type="number" />
            <ChartTooltip cursor={false} content={<ChartTooltipContent indicator="line" />} />
            {/* GİRİŞ ANİMASYONU KAPALI ve bu bir üslup tercihi değil bir DÜZELTME: yukarıdaki
                şerhte ölçülen başa-sarma, animasyon varken her yoklamada tekrarlıyor. Bir
                operatör panosunda çubuğun büyümesini izlemenin bilgi değeri yok; oturmuş
                bir kare okumanın değeri var. */}
            <Bar barSize={28} dataKey="tutar" isAnimationActive={false} radius={6} strokeWidth={1.5}>
              {veri.map((n) => (
                // RENK KANALI BURADA: dolgu K/Z'nin İŞARETİNDEN gelir, uzunluktan
                // bağımsızdır. Cell recharts 3'te "deprecated" işaretli ama tek
                // çalışan nokta-başına-stil yolu; Bar.js:685 `cells[index].props`i
                // dikdörtgene aynen basıyor, yani className geçiyor (ölçüldü).
                <Cell key={n.ticker} className={kzDolgusu(n.kz)} />
              ))}
              <LabelList
                className="fill-foreground font-medium"
                dataKey="ticker"
                fontSize={12}
                offset={10}
                position="insideLeft"
              />
              <LabelList content={tutarEtiketi} dataKey="etiket" />
            </Bar>
          </BarChart>
        </ChartContainer>
      )}

      {/* İKİ KANALIN AÇIK BEYANI. Renk skalası olmayan bir grafik, okuyucudan
          rengin ne demek olduğunu tahmin etmesini ister — ve tahmin ettirmek
          uydurmanın okuyucu tarafıdır. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t pt-3 text-xs">
        <span className="text-muted-foreground">Çubuk boyu = tutar · renk = açık K/Z işareti</span>
        {[
          { v: 1, ad: "kârda" },
          { v: -1, ad: "zararda" },
          { v: null, ad: "K/Z ölçülemedi" },
        ].map((o) => (
          <span key={o.ad} className="flex items-center gap-1.5">
            <span className={`size-2.5 rounded-[2px] ${kzOrnegi(o.v)}`} />
            <span className="text-muted-foreground">{o.ad}</span>
          </span>
        ))}
      </div>

      {cizilemeyen.length > 0 && (
        <div className="rounded-md border border-dashed p-3">
          <p className="font-medium text-sm">
            Grafiğe giremeyen {cizilemeyen.length} pozisyon — tutarı ÖLÇÜLEMEDİ (sıfır değil)
          </p>
          <ul className="mt-2 space-y-1">
            {cizilemeyen.map((s) => (
              <li key={s.ticker} className="text-muted-foreground text-xs">
                <span className="font-medium text-foreground">{s.ticker}</span> — {s.degerNedeni ?? "neden yazılmadı"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
