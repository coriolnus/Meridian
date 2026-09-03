"use client";

/* ============================================================================
   HUNİ — İKİ YÜZEYİN TEK GÖVDESİ (Karar zinciri · Bugün)
   ----------------------------------------------------------------------------
   NEDEN ORTAK GÖVDE: bu deponun baskın hata deseni "aynı kavramın iki kopyası
   zamanla ayrışır". Ölçülmüş örneği `src/meridian/olcum.ts::ROZET` şerhinde:
   TEK eşik ekranda BEŞ ayrı biçimde çıkmıştı. İki huni iki dosyada yaşasaydı,
   birine eklenen bir beyan (payda, karekök ölçek, düşüş listesi) ötekinde eksik
   kalırdı ve okuyucu AYNI ŞEKLİ iki farklı sözleşmeyle okurdu.

   NEDEN `kanban/` ALTINDA: bağımlılık ÖDÜNÇ ALAN yönde akar. Huni grameri karar
   zincirinin sorusudur ("gece ne buldu, nerede eridi"); Bugün yüzeyi onu ödünç
   alıyor. Ters yön (gövdeyi `bugun/` altına koyup kanban'dan import etmek)
   referans yüzeyi türevine bağlardı. Bu turun yazma penceresi zaten bu iki
   dizinle sınırlıydı — üçüncü bir "paylaşılan" dizin seçeneği YOKTU. Şerh o
   kısıtı gizlemek için değil, sonraki turun taşıma kararını bilerek vermesi için
   burada: gövde bir gün `pano/ortak/` altına çıkarsa iki yüzey de import yolunu
   değiştirir, gramer değişmez.

   GRAMERİN KAYNAĞI ÖLÇÜLDÜ, VARSAYILMADI (2026-08-25): şerit biçimi (üç katmanlı
   Sankey bandı), karekök ölçek (üs 0,42), "ad · sayı · yüzde" basamak etiketi,
   "Nerede, neden elendi" listesi ve monotonluk denetimi
   `meridian/web/app.js:2148-2265` (`pvAkisGovdeHTML` + `pvHuniNot` +
   `pvMonotonUyariHTML`) hattından BİREBİR taşındı. Panonun React tarafındaki
   eski `HuniGrafigi` bunların HİÇBİRİNİ taşımıyordu — düz bir Recharts çubuğuydu:
   ne yüzde, ne payda beyanı, ne karekök beyanı, ne düşüş listesi. Yani "iki huni
   aynı dili konuşsun" işi bir kopyalama değil, ESKİ YÜZEYİN GRAMERİNİ yeni
   yüzeye geri getirmekti; kanban hunisi de bu turda o dile taşındı.

   RECHARTS DEĞİL, ELDE SVG — ve `isAnimationActive` bu yüzden YOK: karekök
   ölçekli, üç haleli, eğri kenarlı Sankey bandı Recharts'ın çizemediği bir
   şekil. Animasyon kusuru (`portfoy/PozisyonGrafigi.tsx` şerhi: her yoklamada
   grafik başa sarıyordu) burada YAPISAL OLARAK yok — hiçbir geçiş tanımlı değil,
   `<path>` her render aynı `d` ile doğar. Veri dizileri yine `useMemo` ile
   sabitleniyor: 15/60 sn'lik yoklama her turda yeni dizi doğurursa alt bileşenler
   boşuna yeniden çizilir.

   RENK — `--huni-1..3` KULLANILMADI ve nedeni ölçüldü: o üç rol jetonu
   `src/jetonlar.css`te tanımlı ama O DOSYA BU UYGULAMAYA BAĞLI DEĞİL
   (`src/stil.css` yalnız `yazitipi.css` + `tema.css` import ediyor, ölçüldü
   2026-08-25). Tanımsız bir `var()` SVG `fill`inde siyaha düşer — yani jetonu
   "doğru olduğu için" yazmak şeridi sessizce simsiyah boyardı. Bu yüzden renk
   `tema.css`in ÇOK SERİLİ RAMPASINDAN okunuyor (`--color-seri-*`, aynı dosyada
   tanımlı ve `portfoy/PozisyonSeyri.tsx` zaten aynı yoldan okuyor). Yolculuk
   yapısı app.js'ten aynen korundu: ilk basamaklar bir renk, VARIŞ ayrı bir renk.
   ============================================================================ */
import { type CSSProperties, useMemo } from "react";

import { Badge } from "@/components/ui/badge";

import { Olculemedi } from "./Hal";
import { huniTabani } from "./huni_cekirdek";
import type { HuniBasamagi, HuniDususu, HuniKarsiKart, HuniSeansi } from "./huni_cekirdek";

/* ---- TİPLER: ÇEKİRDEKTE, BURADAN YENİDEN DIŞA VERİLİYOR -------------------
   Tipler ve taban kuralı `huni_cekirdek.ts`e taşındı çünkü orası REACT'SİZ ve
   node'da çağrılabilir — huninin grameri artık kaynak metninden değil,
   çağrılarak ölçülüyor (`tests/civiler/gece_hunisi_civileri.mjs`). Yeniden dışa
   verme mevcut çağrı yerlerini (`KararZinciri`, `HukumDagilimi`) kırmıyor:
   `import { type HuniBasamagi } from "./Huni"` aynen çalışmaya devam ediyor. */
export type { HuniBasamagi, HuniDususu, HuniKarsiKart, HuniSeansi };

/* ---- ÖLÇEK ----------------------------------------------------------------
   KAREKÖK ÖLÇEK — `app.js::PV_HUNI_US` ile AYNI SABİT (0,42) ve aynı gerekçe:
   251'den 1'e düşen bir huni doğrusal ölçekte son basamakları görünmez kılar.
   Beyanı şeridin altında GÖRÜNÜR duruyor; o beyan bir süs değil, genişliği yüzde
   sanmayı engelleyen şey. Sabiti iki yüzeye ayrı ayrı yazmak, birinin bir gün
   0,5'e kayması demekti — tek tanım. */
const US = 0.42;
const W = 1160;
const H = 240;

/** Üç katman: iki soluk HALE + bir dolu çekirdek. Katsayılar maketin kendi
 *  koordinatlarından geri-hesaplanmıştı (app.js şerhi), uydurulmadı. */
const HALE: readonly (readonly [number, number])[] = [
  [1.45, 0.1],
  [1.18, 0.18],
  [1.0, 0.92],
];

const RENK_ILK = "var(--color-seri-6)";
const RENK_ORTA = "var(--color-seri-8)";
const RENK_VARIS = "var(--color-seri-9)";

/** app.js `segRenk` ile aynı kural: son segment VARIŞ rengini alır. */
function segRenk(i: number, nSeg: number): string {
  if (i === nSeg - 1) return RENK_VARIS;
  return i < 2 ? RENK_ILK : RENK_ORTA;
}

function genislikOrani(n: number | null, taban: number | null): number | null {
  if (taban === null || taban <= 0 || n === null) return null;
  return Math.pow(Math.max(0, n) / taban, US);
}

/* ---- BİÇİM ----------------------------------------------------------------
   `bugun/ortak.tsx::bicimSayi` DIŞARIDAN ALINMADI: gövde `kanban/` altında ve
   `bugun/`den import etmek bağımlılığı iki yöne birden açardı (döngü riski,
   üstelik yukarıdaki "ödünç alan yön" gerekçesini tersine çevirirdi). Ayrı
   biçimlendirici çünkü ayrı soru: buradaki sayılar ADETtir ve ondalık taşımaz —
   `bicimSayi` 2 basamağa kadar ondalık yazıyor. */
const ADET = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const YUZDE = new Intl.NumberFormat("tr-TR", { style: "percent", maximumFractionDigits: 1 });

/* ========================================================================== */

export function Huni({
  basamaklar,
  dususler = [],
  seans,
  karsi,
  paydaBeyani,
}: {
  readonly basamaklar: readonly HuniBasamagi[];
  readonly dususler?: readonly HuniDususu[];
  readonly seans: HuniSeansi;
  readonly karsi?: HuniKarsiKart;
  /** Sayıların paydası — ZORUNLU. Paydasız şerit okuru kendi uydurduğu tavana
   *  göre okutur (`app.js::hucreCubuk` kuralının bileşen sınırındaki hâli). */
  readonly paydaBeyani: string;
}) {
  /** TABAN = ilk basamak. Yüzdeler ve şerit genişliği buna göre; ilk basamak
   *  ölçülemediyse ORAN DA ÖLÇÜLEMEZ (0 varsayılmaz). KURAL ÇEKİRDEKTEN OKUNUR:
   *  kartlar düşüş oranlarını aynı tabana bölüyor ve iki kopya bir gün sessizce
   *  ayrışırdı — şerit bir şey, yüzdeler başka bir şey gösterirdi. */
  const taban = useMemo(() => huniTabani(basamaklar), [basamaklar]);

  const kol = basamaklar.length > 1 ? W / (basamaklar.length - 1) : W;

  /* ETİKET TAVANI HESAPLANIR, GÖZLE SEÇİLMEZ. Kenar etiketleri hizalı (sol/sağ),
     aradakiler düğümün üstünde ORTALI. Üst üste binmemeleri için genişlik tavanı
     w ≤ (2/3)·(100/k) olmalı — sıfırıncı etiketin sağ kenarı (w) ile birinci
     etiketin sol kenarı (100/k − w/2) çakışmasın diye. Sabit bir yüzde yazmak
     (örn. %36) iki basamaklı huni için doğru, dört basamaklı için SESSİZCE yanlış
     olurdu: etiketler birbirinin üstüne biner ve okuyucu yüzdeyi yanlış basamağa
     bağlar. */
  const etiketTavani = `${((200 / 3) / Math.max(1, basamaklar.length - 1)).toFixed(1)}%`;

  const segmentler = useMemo(() => {
    const cikti: { anahtar: string; d: string; renk: string; opaklik: number }[] = [];
    const nSeg = basamaklar.length - 1;
    for (let i = 0; i < nSeg; i += 1) {
      const su = basamaklar[i];
      const sonraki = basamaklar[i + 1];
      if (su === undefined || sonraki === undefined) continue;
      const g0 = genislikOrani(su.n, taban);
      const g1 = genislikOrani(sonraki.n, taban);
      // ÖLÇÜLEMEYEN BASAMAK ŞERİT DOĞURMAZ: sıfır genişlik çizmek "hiçbiri
      // geçmedi" diye okunurdu, oysa cevap "ölçemedik".
      if (g0 === null || g1 === null) continue;
      const x0 = i * kol;
      const x1 = (i + 1) * kol;
      const c0 = x0 + kol * 0.45;
      const c1 = x1 - kol * 0.45;
      const renk = segRenk(i, nSeg);
      for (const [kat, op] of HALE) {
        const a0 = Math.min(1.6, g0 * kat);
        const a1 = Math.min(1.6, g1 * kat);
        const y0a = H / 2 - (H / 2) * a0;
        const y0b = H / 2 + (H / 2) * a0;
        const y1a = H / 2 - (H / 2) * a1;
        const y1b = H / 2 + (H / 2) * a1;
        cikti.push({
          anahtar: `${i}-${kat}`,
          renk,
          opaklik: op,
          d:
            `M${x0.toFixed(1)} ${y0a.toFixed(1)} ` +
            `C${c0.toFixed(1)} ${y0a.toFixed(1)} ${c1.toFixed(1)} ${y1a.toFixed(1)} ${x1.toFixed(1)} ${y1a.toFixed(1)} ` +
            `L${x1.toFixed(1)} ${y1b.toFixed(1)} ` +
            `C${c1.toFixed(1)} ${y1b.toFixed(1)} ${c0.toFixed(1)} ${y0b.toFixed(1)} ${x0.toFixed(1)} ${y0b.toFixed(1)} Z`,
        });
      }
    }
    return cikti;
  }, [basamaklar, kol, taban]);

  const eksikler = useMemo(
    () => basamaklar.filter((b): b is Extract<HuniBasamagi, { n: null }> => b.n === null),
    [basamaklar],
  );

  /** MONOTONLUK ÖLÇÜLÜR, VARSAYILMAZ (app.js `pvMonotonUyariHTML`): sonraki
   *  basamak öncekini aşarsa şekil artık bir HUNİ DEĞİLDİR ve genişleyen şerit
   *  "alt küme büyüdü" diye okunur. Sayı KIRPILMAZ — ihlal adıyla yazılır. */
  const ihlaller = useMemo(() => {
    const liste: string[] = [];
    for (let i = 1; i < basamaklar.length; i += 1) {
      const onceki = basamaklar[i - 1];
      const su = basamaklar[i];
      if (onceki === undefined || su === undefined) continue;
      if (onceki.n !== null && su.n !== null && su.n > onceki.n) {
        liste.push(`${onceki.ad} ${ADET.format(onceki.n)} → ${su.ad} ${ADET.format(su.n)}`);
      }
    }
    return liste;
  }, [basamaklar]);

  const okunur = basamaklar
    .map((b) => `${b.ad} ${b.n === null ? "ölçülemedi" : ADET.format(b.n)}`)
    .join(", ");

  return (
    <div className="flex flex-col gap-3">
      {/* ---- SEANS DAMGASI: hangi güne ait? Damga yoksa TARİH UYDURULMAZ. ---- */}
      <div className="flex flex-wrap items-center gap-1.5">
        {seans.damga === null ? (
          <Olculemedi
            kisa
            neden={seans.neden ?? "Bu huninin hangi güne ait olduğu okunamadı"}
            teknik="kayıtta seans damgası yok"
          />
        ) : (
          <Badge variant="outline" className="tabular-nums">
            seans · {seans.damga}
          </Badge>
        )}
        <span className="text-muted-foreground text-xs">kaynak: {seans.kaynak}</span>
      </div>

      {/* ---- ŞERİT + BASAMAK ETİKETLERİ ---- */}
      <div>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="h-32 w-full"
          role="img"
          aria-label={`Huni: ${okunur}`}
        >
          {/* BASAMAK AYRAÇLARI. `vectorEffect` şart: `preserveAspectRatio="none"`
              konturu da eziyor — 1160 birimlik kutu 350 px'lik kolona sıkışınca
              dikey çizgi 0,3 px'e düşer ve sessizce kaybolur. Bu bayrak kontur
              kalınlığını cihaz pikselinde sabit tutar. */}
          {basamaklar.slice(1, -1).map((b, i) => (
            <line
              key={`ayrac-${b.ad}`}
              x1={((i + 1) * kol).toFixed(1)}
              y1={0}
              x2={((i + 1) * kol).toFixed(1)}
              y2={H}
              stroke="var(--border)"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          ))}
          {segmentler.map((s) => (
            <path key={s.anahtar} d={s.d} fill={s.renk} opacity={s.opaklik} />
          ))}
        </svg>

        {/* BASAMAK ETİKETİ: ad · sayı · yüzde — üçü alt alta, konum şeridin
            düğümünün üstünde (app.js `pv-hasama` yerleşimi). Mutlak konum
            bilinçli: akış kabında etiketler düğümlerden kayar ve okuyucu
            yüzdeyi yanlış basamağa bağlar. */}
        <div className="relative mt-1 h-14">
          {basamaklar.map((b, i) => {
            const son = i === basamaklar.length - 1;
            const konum: CSSProperties = son
              ? { right: 0, textAlign: "right", maxWidth: etiketTavani }
              : i === 0
                ? { left: 0, maxWidth: etiketTavani }
                : {
                    left: `${((100 * i) / Math.max(1, basamaklar.length - 1)).toFixed(2)}%`,
                    transform: "translateX(-50%)",
                    textAlign: "center",
                    maxWidth: etiketTavani,
                  };
            const oran = taban !== null && b.n !== null ? b.n / taban : null;
            return (
              <div key={b.ad} className="absolute top-0 break-words" style={konum}>
                <div className="text-[11px] text-muted-foreground leading-tight">{b.ad}</div>
                <div className="font-medium text-sm tabular-nums leading-tight">
                  {b.n === null ? <Olculemedi kisa neden={b.neden} /> : ADET.format(b.n)}
                </div>
                <div className="text-[10px] text-muted-foreground tabular-nums leading-tight">
                  {oran === null ? "" : YUZDE.format(oran)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ---- BEYAN: karekök ölçek + payda. İkisi de şeridin altında GÖRÜNÜR. ---- */}
      <p className="text-muted-foreground text-xs leading-5">
        Şerit genişliği <b className="font-medium">karekök ölçeklidir</b> (üs 0,42) — genişlik oranı{" "}
        <b className="font-medium">yüzde DEĞİLDİR</b>; yüzdeler basamağın kendi etiketinde yazar ve ilk
        basamağa göredir. {paydaBeyani}
      </p>

      {eksikler.length > 0 ? (
        <p className="text-muted-foreground text-xs leading-5">
          Ölçülemeyen basamak:{" "}
          {eksikler.map((b) => `${b.ad} (${b.neden})`).join(" · ")} — sıfır DEĞİL, şerit orada çizilmedi.
        </p>
      ) : null}

      {ihlaller.length > 0 ? (
        <p className="text-destructive text-xs leading-5">
          Bu şerit bir HUNİ DEĞİL: sonraki basamak öncekini aşıyor ({ihlaller.join(" · ")}). İki basamak
          iç içe değilse oranları huni gibi okuma — sayılar olduğu gibi basıldı, kırpılmadı.
        </p>
      ) : null}

      {/* ---- NEREDE, NEDEN ELENDİ ---- */}
      {dususler.length > 0 ? (
        <div className="flex flex-col gap-1 border-t pt-3">
          <div className="font-medium text-xs uppercase tracking-wide">Nerede, neden elendi</div>
          {dususler.map((d) => (
            <div key={d.ok} className="flex items-baseline justify-between gap-3 text-sm">
              <span className="min-w-0">
                <span className="text-muted-foreground text-xs">{d.ok}</span>{" "}
                <span>{d.metin}</span>
              </span>
              <span className="shrink-0 tabular-nums">
                {d.oran === null ? (
                  <Olculemedi kisa neden={d.neden ?? "payda ölçülemedi"} />
                ) : (
                  `−${YUZDE.format(d.oran)}`
                )}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {karsi ? <SeansUzlasmasi seans={seans} karsi={karsi} /> : null}
    </div>
  );
}

/* --------------------------------------------------------------------------
   İKİ KARTIN SEANSI — ölçülmüş kusur (2026-08-25, yerel fikstür): Karar zinciri
   hunisi "2 plan · 2 NO_GO", Bugün'ün dağılımı "5 plan · 3 NO_GO" diyordu ve
   okuyucu hangisinin hangi güne ait olduğunu ANLAYAMIYORDU — biri seansını
   yazıyor, öteki yazmıyordu. İki kartın FARKLI seansı anlatması meşru olabilir
   (iki ayrı defter, iki ayrı yazım anı) ama SÖYLENMEDEN meşru olamaz.

   BU BLOK HÜKÜM VERMEZ: "hangisi doğru" sorusu bu yüzeyin ölçümü değildir ve
   burada cevaplanmaz — yalnız iki damgayı yan yana koyar. Şiddet jetonu
   (`destructive`) da bilerek kullanılmadı: ayrışma bir ARIZA değil, beyan
   edilmesi gereken bir olgu; kırmızı kutu her meşru farkı olay gibi gösterirdi.
   -------------------------------------------------------------------------- */
export function SeansUzlasmasi({ seans, karsi }: { seans: HuniSeansi; karsi: HuniKarsiKart }) {
  const ikisiDeVar = seans.damga !== null && karsi.damga !== null;
  const ayni = ikisiDeVar && seans.damga === karsi.damga;

  return (
    <div className="rounded-md border border-dashed px-2.5 py-2 text-xs leading-5">
      {!ikisiDeVar ? (
        <>
          Karşılaştırma YAPILAMADI:{" "}
          {seans.damga === null
            ? `bu huninin seans damgası ölçülemedi (${seans.neden ?? "kayıtta damga yok"})`
            : `${karsi.ad} kartının seans damgası ölçülemedi (${karsi.neden ?? "kayıtta damga yok"})`}
          . İki damga da görünmeden hangi kartın hangi güne ait olduğu söylenemez.
        </>
      ) : ayni ? (
        <>
          Bu huni ile <b className="font-medium">{karsi.ad}</b> AYNI seansı ({seans.damga}) anlatıyor —
          ama sayıları ayrı defterlerden geliyor (burada {seans.kaynak}, orada {karsi.kaynak}), yani
          eşitlik garanti değil.
        </>
      ) : (
        <>
          Bu huni <b className="font-medium">{seans.damga}</b> seansını, <b className="font-medium">{karsi.ad}</b>{" "}
          ise <b className="font-medium">{karsi.damga}</b> seansını anlatıyor —{" "}
          <b className="font-medium">iki kart aynı güne bakmıyor</b>. Kaynaklar da ayrı (burada{" "}
          {seans.kaynak}, orada {karsi.kaynak}). Hangisinin doğru olduğu BU YÜZEYDE ölçülmedi; iki sayıyı
          birbirine karşı okumadan önce damgalara bak.
        </>
      )}
    </div>
  );
}
