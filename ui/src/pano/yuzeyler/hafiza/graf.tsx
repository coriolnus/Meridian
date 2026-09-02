"use client";

/* ============================================================================
   VARLIK GRAFI — KÜTÜPHANESİZ, SADE SVG
   ----------------------------------------------------------------------------
   TAŞINAN ŞEY VERİ, ÇİZİM DEĞİL (plan kararı, `api.py::api_hindsight_varlik_graf`
   şerhinde de yazılı): birebirleştirme DÜZEN ve BİLGİ düzeyindedir, piksel
   düzeyinde değil. Üst yüzey bu grafı bir kuvvet-yönlendirmeli "takımyıldız"
   olarak çiziyor (kendi `constellation.tsx`i, 1.642 satır, canvas + animasyon).
   Onu taşımak, ölçülmemiş bir yerleşim algoritmasını panoya sokmak ve her kare
   yeniden hesaplanan bir düzeni "veri" gibi göstermek olurdu.

   BU ÇİZİMİN SINIRLARI — HEPSİ EKRANDA DA YAZILI, YALNIZ BURADA DEĞİL:
     1. YERLEŞİM SABİT VE ANLAMSIZDIR. Düğümler bir ÇEMBER üzerinde, ağırlığa
        göre sıralı durur. İki düğümün ekrandaki YAKINLIĞI bir ölçüm DEĞİLDİR —
        anlam taşıyan tek şey ARALARINDAKİ ÇİZGİdir. Kuvvet yerleşiminde
        yakınlık bir şey söyler; burada söylemez ve bu fark yazılmazsa okuyucu
        onu kendi kafasında uydurur.
     2. YAKINLAŞTIRMA/KAYDIRMA YOK. Kalabalık graf okunmaz hâle gelir; çare
        `min_count` süzgecidir (sunucu tarafında, ölçülmüş bir sınır).
     3. İKİ TAVAN VAR VE İKİSİ DE SAYIYLA YAZILIR — SUNUCUNUNKİ DE.
        Kırpma zinciri üç halkalıdır: bankadaki TOPLAM (`total_entities` /
        `total_edges`, üst servisten) → VEKİLİN DÖNDÜRDÜĞÜ dilim (vekil limiti
        kendi tavanına indiriyor: `api.py::_hafiza_sayi` + `HAFIZA_LISTE_TAVANI`)
        → EKRANIN ÇİZDİĞİ en ağır `DUGUM_TAVANI` düğüm. Üçü de başlıkta adıyla
        durur; toplam gelmezse yerinde "— (alan gelmedi)" yazar, sayı uydurulmaz.
        İlk yazımda yalnız ÜÇÜNCÜ halka sayılıyordu (inceleme I-1) ve sunucunun
        elediği binlerce isim hiçbir yerde görünmüyordu: eksik bir graf TAM
        görünüyordu, yani tam olarak bu maddenin yasakladığı şey oluyordu.
     4. RENK BİR ÖLÇÜM DEĞİLDİR. Üst yüzey düğümleri tazeliğe göre renklendiriyor
        (`lastCooccurred` ısı ölçeği); burada tek renk var, çünkü bir ısı ölçeği
        çizip ölçeğin uçlarını yazmamak sayıyı gizleyip rengi öne çıkarırdı ve
        panonun rezerve renk bantları kuralı da bunu (mod/nav/şiddet dışı hue)
        kısıtlıyor. Tazelik SAYI olarak seçili düğümün künyesinde yazıyor.
   ============================================================================ */
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { Olculemedi, Satir } from "../sistem/parcalar";
import { damga, metin, sayi } from "./parcalar";
import type { GrafKenari, VarlikGrafi } from "./uctipleri";

/** En ağır kaç düğüm çizilir. Ölçülmüş bir eşik DEĞİL, bir çizim kararıdır ve
 *  öyle adlandırılmıştır: bunun üstünde çember üzerindeki etiketler üst üste
 *  biner ve şekil okunmaz olur. */
const DUGUM_TAVANI = 90;
/** Aynı sınıf karar: en ağır kaç kenar çizilir. */
const KENAR_TAVANI = 400;

const GENISLIK = 720;
const YUKSEKLIK = 520;

interface CizilenDugum {
  readonly kimlik: string;
  readonly etiket: string;
  readonly agirlik: number;
  readonly x: number;
  readonly y: number;
  readonly yaricap: number;
}

interface CizilenKenar {
  readonly kaynak: string;
  readonly hedef: string;
  readonly agirlik: number;
  readonly tur: string | null;
  readonly son: string | null;
}

/** Kenarın ağırlığı: önce `weight`, yoksa `similarity` (CP `graph-data.ts` aynı
 *  sırayı kullanıyor). İkisi de yoksa 1 — ve bu bir VARSAYIM değil, "bu kenar
 *  var" bilgisinin en küçük hâli: kenarın kendisi ölçülmüş bir gerçektir. */
function kenarAgirligi(k: GrafKenari): number {
  return sayi(k.data?.weight) ?? sayi(k.data?.similarity) ?? 1;
}

/** Grafın ölçülebilir özeti — çizimden ÖNCE, çizimden BAĞIMSIZ.
 *  İHRAÇ EDİLMEZ: tek tüketicisi bu dosya (`parcalar.tsx::hamMetin` emsali —
 *  okuru olmayan bir ihracat, ilk kullananın kendi anlamıyla eğdiği bir yüzeydir). */
interface GrafOzeti {
  readonly dugumler: readonly CizilenDugum[];
  readonly kenarlar: readonly CizilenKenar[];
  /** Gövdede olup ÇİZİLMEYEN düğüm sayısı (tavan). */
  readonly disaridaDugum: number;
  /** Gövdede olup ÇİZİLMEYEN kenar sayısı (tavan ya da ucu çizilmeyen düğüm). */
  readonly disaridaKenar: number;
  /** Kimliği okunamadığı için hiç sayılamayan düğüm sayısı. */
  readonly kimliksizDugum: number;
  /**
   * İki ucundan biri DÖNEN düğüm listesinde olmayan kenar sayısı.
   *
   * GEREKÇE DÜZELTİLDİ (inceleme I-1): burada önce "düğüm listesinde yok" deniyordu
   * ve bu, bozuk veri gibi okunuyordu. Ölçülen sebep BAŞKA: bu uç sunucuda
   * kırpılıyor, yani kenarın öteki ucu bankada VARDIR ama dönen dilimde yoktur.
   * Yanlış bir gerekçe, gerekçesizlikten kötüdür — operatörü şema aramaya gönderir.
   */
  readonly askidaKenar: number;
  /** Vekilin DÖNDÜRDÜĞÜ düğüm/kenar sayısı (kırpma sonrası, çizim tavanı öncesi). */
  readonly vekilDugum: number;
  readonly vekilKenar: number;
  /** Bankadaki TOPLAM sayı — sınıf (A). `null` = alan gelmedi, UYDURULMAZ. */
  readonly toplamDugum: number | null;
  readonly toplamKenar: number | null;
  /** Sunucunun uyguladığı tavan. `null` = bildirilmedi. */
  readonly vekilTavani: number | null;
}

/**
 * Gövdeyi çizilebilir hâle getirir. HİÇBİR ŞEY UYDURMAZ: kimliksiz düğüm ve
 * askıda kenar ATILMAZ, SAYILIR ve sayıları ekranda görünür — sessizce düşen
 * bir düğüm, grafiği eksik ama sağlam gösterirdi.
 */
function grafiCoz(govde: VarlikGrafi): GrafOzeti {
  const hamDugumler = Array.isArray(govde.nodes) ? govde.nodes : [];
  const hamKenarlar = Array.isArray(govde.edges) ? govde.edges : [];

  const etiketler = new Map<string, string>();
  let kimliksizDugum = 0;
  for (const d of hamDugumler) {
    const kimlik = metin(d.data?.id);
    if (kimlik === null) {
      kimliksizDugum += 1;
      continue;
    }
    etiketler.set(kimlik, metin(d.data?.label) ?? kimlik);
  }

  const agirliklar = new Map<string, number>();
  const gecerli: CizilenKenar[] = [];
  let askidaKenar = 0;
  for (const k of hamKenarlar) {
    const kaynak = metin(k.data?.source);
    const hedef = metin(k.data?.target);
    if (kaynak === null || hedef === null || !etiketler.has(kaynak) || !etiketler.has(hedef)) {
      askidaKenar += 1;
      continue;
    }
    const w = kenarAgirligi(k);
    agirliklar.set(kaynak, (agirliklar.get(kaynak) ?? 0) + w);
    agirliklar.set(hedef, (agirliklar.get(hedef) ?? 0) + w);
    gecerli.push({
      kaynak,
      hedef,
      agirlik: w,
      tur: metin(k.data?.linkType),
      son: metin(k.data?.lastCooccurred),
    });
  }

  /* SIRALAMA AĞIRLIĞA GÖRE VE KARARLI: eşit ağırlıkta kimliğe göre. Kararsız bir
     sıralama her okumada başka bir şekil çizerdi ve operatör "graf değişti"
     sanırdı — oysa değişen yalnız sıralama olurdu. */
  const sirali = [...etiketler.keys()].sort((a, b) => {
    const fark = (agirliklar.get(b) ?? 0) - (agirliklar.get(a) ?? 0);
    return fark !== 0 ? fark : a.localeCompare(b);
  });
  const secilen = sirali.slice(0, DUGUM_TAVANI);
  const secilenKume = new Set(secilen);

  const enAgir = secilen.reduce((m, k) => Math.max(m, agirliklar.get(k) ?? 0), 0);
  const merkezX = GENISLIK / 2;
  const merkezY = YUKSEKLIK / 2;
  const yaricapX = merkezX - 90;
  const yaricapY = merkezY - 40;
  const dugumler: CizilenDugum[] = secilen.map((kimlik, i) => {
    const aci = (2 * Math.PI * i) / Math.max(1, secilen.length) - Math.PI / 2;
    const w = agirliklar.get(kimlik) ?? 0;
    /* KARE KÖK: uzun kuyruğu düzleştirir, yani bir merkez düğüm ötekileri
       görünmez kılmaz. Yarıçap bir SIRALAMA göstergesidir, mutlak bir ölçü değil. */
    const t = enAgir > 0 ? Math.sqrt(w / enAgir) : 0;
    return {
      kimlik,
      etiket: etiketler.get(kimlik) ?? kimlik,
      agirlik: w,
      x: merkezX + yaricapX * Math.cos(aci),
      y: merkezY + yaricapY * Math.sin(aci),
      yaricap: 3 + t * 7,
    };
  });

  const cizilebilir = gecerli.filter((k) => secilenKume.has(k.kaynak) && secilenKume.has(k.hedef));
  const kenarSirali = [...cizilebilir].sort((a, b) => b.agirlik - a.agirlik);
  const kenarlar = kenarSirali.slice(0, KENAR_TAVANI);

  return {
    dugumler,
    kenarlar,
    disaridaDugum: sirali.length - secilen.length,
    disaridaKenar: gecerli.length - kenarlar.length,
    kimliksizDugum,
    askidaKenar,
    vekilDugum: hamDugumler.length,
    vekilKenar: hamKenarlar.length,
    toplamDugum: sayi(govde.total_entities),
    toplamKenar: sayi(govde.total_edges),
    vekilTavani: sayi(govde.limit),
  };
}

/**
 * KIRPMA ZİNCİRİ — "çizilen / vekilin döndürdüğü / bankadaki toplam".
 *
 * Üç sayı da ADIYLA yazılır ve eksik olan UYDURULMAZ: toplam gelmezse yerinde
 * "— (alan gelmedi)" durur. Tek bir "N çizildi" rozetinin sorunu, doğru olmasına
 * rağmen eksik olmasıydı — okuyucu N'yi bankanın tamamı sanıyordu.
 */
function Zincir({
  ne,
  cizilen,
  vekil,
  tavan,
  toplam,
}: {
  readonly ne: string;
  readonly cizilen: number;
  readonly vekil: number;
  /** Sunucunun uyguladığı tavan; `null` = bildirilmedi. */
  readonly tavan: number | null;
  /** Bankadaki toplam; `null` = alan gelmedi. */
  readonly toplam: number | null;
}) {
  const n = (x: number) => x.toLocaleString("tr-TR");
  return (
    <p className="text-muted-foreground text-xs tabular-nums">
      <span className="font-medium text-foreground">{n(cizilen)}</span> {ne} çizildi
      {" · "}vekil {n(vekil)} döndürdü
      {tavan === null ? " (tavan bildirilmedi)" : ` (tavan ${n(tavan)})`}
      {" · "}bankada toplam{" "}
      {toplam === null ? (
        <Olculemedi
          neden="— (alan gelmedi)"
          teknik="üst servisin toplam sayacı bu yanıtta yok — kaçının dışarıda kaldığı ölçülemiyor"
          kisa
        />
      ) : (
        <span className="font-medium text-foreground">{n(toplam)}</span>
      )}
    </p>
  );
}

/* --------------------------------------------------------------------------- */

export function Graf({ govde }: { readonly govde: VarlikGrafi }) {
  const ozet = useMemo(() => grafiCoz(govde), [govde]);
  const [secili, setSecili] = useState<string | null>(null);

  if (!Array.isArray(govde.nodes)) {
    return (
      <Olculemedi
        neden="Graf düğümleri tanınmayan bir biçimde geldi"
        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
      />
    );
  }
  if (ozet.dugumler.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Graf okundu ve çizilebilir düğüm YOK. Bu ölçülmüş bir boşluktur: ya bu bankada birlikte
        geçen isim yok, ya da eşik (en az anılma) bütün düğümleri eliyor.
      </p>
    );
  }

  const seciliDugum = secili === null ? null : ozet.dugumler.find((d) => d.kimlik === secili) ?? null;
  const komsular =
    secili === null
      ? []
      : ozet.kenarlar
          .filter((k) => k.kaynak === secili || k.hedef === secili)
          .map((k) => ({ ...k, oteki: k.kaynak === secili ? k.hedef : k.kaynak }))
          .sort((a, b) => b.agirlik - a.agirlik);
  const etiketi = (kimlik: string) => ozet.dugumler.find((d) => d.kimlik === kimlik)?.etiket ?? kimlik;
  const enAgirKenar = ozet.kenarlar.reduce((m, k) => Math.max(m, k.agirlik), 0);

  return (
    <div className="flex flex-col gap-3">
      {/* KIRPMA ZİNCİRİ — ÜÇ SAYI, ÜÇÜ DE ADIYLA (inceleme I-1).
          Önce yalnız "çizilen" ve "çizim tavanının dışında kalan" yazıyordu; o
          rozet SUNUCUNUN elediklerini hiç saymıyordu ve eksik bir graf tam
          görünüyordu — dosyanın kendi yasağının ihlali. Üç sayı da telde vardı
          (`total_entities`/`total_edges`/`limit`, A1'de ölçüldü) ve okunmuyordu. */}
      <div className="flex flex-col gap-1">
        <Zincir
          ne="isim"
          cizilen={ozet.dugumler.length}
          vekil={ozet.vekilDugum}
          tavan={ozet.vekilTavani}
          toplam={ozet.toplamDugum}
        />
        <Zincir
          ne="bağ"
          cizilen={ozet.kenarlar.length}
          vekil={ozet.vekilKenar}
          tavan={ozet.vekilTavani}
          toplam={ozet.toplamKenar}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {ozet.kimliksizDugum > 0 ? (
          <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
            {ozet.kimliksizDugum} düğümün kimliği okunamadı
          </Badge>
        ) : null}
        {ozet.askidaKenar > 0 ? (
          <Badge
            variant="outline"
            className="font-normal text-[11px] text-muted-foreground"
            title="bu uç sunucuda kırpılıyor: kenarın öteki ucu bankada var ama dönen dilimde yok"
          >
            {ozet.askidaKenar} bağın öteki ucu dönen dilimde yok
          </Badge>
        ) : null}
      </div>

      <div className="overflow-x-auto rounded-lg border">
        <svg
          viewBox={`0 0 ${GENISLIK} ${YUKSEKLIK}`}
          className="h-auto w-full min-w-[36rem]"
          role="img"
          aria-label={`Varlık bağ haritası: ${ozet.dugumler.length} isim, ${ozet.kenarlar.length} bağ`}
        >
          <g>
            {ozet.kenarlar.map((k, i) => {
              const a = ozet.dugumler.find((d) => d.kimlik === k.kaynak);
              const b = ozet.dugumler.find((d) => d.kimlik === k.hedef);
              if (!a || !b) return null;
              const vurgulu = secili !== null && (k.kaynak === secili || k.hedef === secili);
              const kalinlik = enAgirKenar > 0 ? 0.4 + (k.agirlik / enAgirKenar) * 1.6 : 0.4;
              return (
                <line
                  key={`${k.kaynak}|${k.hedef}|${i}`}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  strokeWidth={vurgulu ? kalinlik + 0.8 : kalinlik}
                  className={cn(
                    "stroke-foreground",
                    secili === null ? "opacity-15" : vurgulu ? "opacity-50" : "opacity-5",
                  )}
                />
              );
            })}
          </g>
          <g>
            {ozet.dugumler.map((d) => {
              const vurgulu = secili === d.kimlik;
              return (
                <circle
                  key={d.kimlik}
                  cx={d.x}
                  cy={d.y}
                  r={vurgulu ? d.yaricap + 2 : d.yaricap}
                  className={cn(
                    "cursor-pointer fill-foreground",
                    vurgulu ? "opacity-90" : secili === null ? "opacity-60" : "opacity-25",
                  )}
                  onClick={() => setSecili((s) => (s === d.kimlik ? null : d.kimlik))}
                >
                  <title>{`${d.etiket} — bağ ağırlığı ${d.agirlik.toLocaleString("tr-TR")}`}</title>
                </circle>
              );
            })}
          </g>
        </svg>
      </div>

      <p className="text-muted-foreground text-[11px]">
        Düğümlerin ekrandaki YERİ bir ölçüm değildir: çember üzerinde ağırlığa göre sıralı
        duruyorlar, yani iki ismin yan yana olması bir yakınlık anlamına GELMEZ. Anlam taşıyan
        şey aralarındaki çizgidir. Bir isme tıklayınca yalnız onun bağları vurgulanır ve künyesi
        aşağıda açılır.
      </p>

      {seciliDugum === null ? (
        <p className="text-muted-foreground text-sm">Bir isme tıkla — bağları burada listelenir.</p>
      ) : (
        <div className="rounded-lg border p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium text-sm">{seciliDugum.etiket}</span>
            <Badge variant="outline" className="font-mono text-[11px]">
              {seciliDugum.kimlik}
            </Badge>
          </div>
          <div className="mt-2">
            <Satir etiket="Bağ ağırlığı toplamı">
              <span className="tabular-nums">{seciliDugum.agirlik.toLocaleString("tr-TR")}</span>
            </Satir>
            <Satir etiket="Çizilen bağ sayısı">
              <span className="tabular-nums">{komsular.length.toLocaleString("tr-TR")}</span>
            </Satir>
          </div>
          {komsular.length === 0 ? (
            <p className="mt-2 text-muted-foreground text-xs">
              Bu ismin çizilen hiçbir bağı yok — bağları çizim tavanının dışında kalmış olabilir
            </p>
          ) : (
            <ul className="mt-2 flex flex-col gap-1">
              {komsular.slice(0, 20).map((k, i) => (
                <li
                  key={`${k.oteki}-${i}`}
                  className="flex flex-wrap items-baseline justify-between gap-2 border-b py-1 text-xs last:border-b-0"
                >
                  <button
                    type="button"
                    className="min-w-0 truncate text-left underline-offset-2 hover:underline"
                    onClick={() => setSecili(k.oteki)}
                  >
                    {etiketi(k.oteki)}
                  </button>
                  <span className="flex shrink-0 items-center gap-2 text-muted-foreground">
                    <span className="tabular-nums">{k.agirlik.toLocaleString("tr-TR")}</span>
                    {k.tur ? <span className="font-mono text-[10px]">{k.tur}</span> : null}
                    {k.son ? (
                      <span className="text-[10px]">{damga(k.son) ?? k.son}</span>
                    ) : (
                      <Olculemedi
                        neden="Son birlikte geçiş gelmedi"
                        teknik="kenarın son-birlikte-geçiş damgası gelmedi ya da çözülemedi"
                        kisa
                      />
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {komsular.length > 20 ? (
            <p className="mt-1 text-muted-foreground text-[11px] tabular-nums">
              ilk 20 bağ listelendi, {komsular.length - 20} tanesi daha var
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
