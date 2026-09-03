"use client";

/* ============================================================================
   HAFIZA · BİLGİ TABANI — üst yüzeyin `knowledge` sekmesinin karşılığı
   ----------------------------------------------------------------------------
   İKİ ALT SEKME OKUNDU, UYDURULMADI: üst yüzeyde bu sekme "Sayfalar" ve "Zihin
   Modelleri" diye ikiye ayrılıyor ve varsayılan Sayfalar. İkisini iki ayrı
   kenar çubuğu durağına bölmek daha "düzenli" görünürdü ama o yüzeyi bilen bir
   okuyucu modelleri aradığı yerde bulamazdı.

   ÜÇÜNCÜ SEKME EMEKLİ OLDU (TSK-118, 2026-09-03, operatör K8: "dokuzuncu nav
   durağı aç"): "Meridian dersleri" bir süre burada ÜÇÜNCÜ (üst yüzeyde karşılığı
   olmayan) bir sekmeydi. TSK-118 onu TAŞIDI, çoğaltmadı (TSK-124 dersi): içerik
   artık kendi görünümü (`hafiza-dersler`, `alanlar.ts::YUZEYLER.memory.
   bolumler`), gövdesi `Dersler.tsx`. Bu dosya `MeridianDersleri`yi ARTIK içe
   aktarmıyor — iki yerden aynı bileşene erişim tek-kaynak yasasını ihlal ederdi.

   ÜST YÜZEYİN KENDİ ŞERHİ BUNU AÇIKLIYOR: bir SAYFA, ağaçta yeri olan bir ZİHİN
   MODELİDİR — sayfanın tazelik satırı ile modelin tazelik satırı aynı şeydir.
   Bu yüzden ikisi de aynı bileşenle çiziliyor (`ZihinModelleri.tsx::TazelikSatiri`);
   iki ayrı satır yazsaydık aynı gerçeğin iki kopyası sessizce ayrışırdı.

   ---------------------------------------------------------------------------
   ARAMA AĞACIN YERİNE GEÇER, YANINA DEĞİL
   ---------------------------------------------------------------------------
   Üst yüzeyde boş olmayan bir sorgu ağacı sıralı vuruşlarla DEĞİŞTİRİYOR; aynı
   davranış burada da var. İkisini yan yana çizmek, hangi listenin süzülmüş
   olduğunu ekrandan okunamaz kılardı.

   BOŞ SORGU ÜST SERVİSE GİTMEZ ve bu bir bedel kararıdır (vekil de aynısını
   yapıyor): boş sorgu bir BM25+vektör aramasını bedelsiz tetiklerdi. Ekran bunu
   "sonuç yok" diye DEĞİL, "arama yapılmadı" diye yazar.

   ---------------------------------------------------------------------------
   SAYFANIN METNİ HAM BASILIR
   ---------------------------------------------------------------------------
   Üst yüzey metni markdown olarak işliyor; panoda markdown işleyicisi yok ve bu
   turda bir tane eklemek kapsam dışı. Ham metin, yarım işlenmiş bir metinden
   dürüsttür: hiçbir başlık kaybolmaz, yalnız biçimlenmez.
   ============================================================================ */
import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, FileText, Folder, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { useRota, useRouter } from "../../rota";
import { useApi } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";

import { bilgiSekmesiCoz, sekmeliYol, type HafizaBilgiSekmesi } from "./gorunumler";
import { Bolme, Cipler, Faz2Dugme, Faz2Grup, HamSatirlar, ZarfKapisi, damga, listeye, metin, sayi, sozluk } from "./parcalar";
import { TazelikSatiri, ZihinModelleri } from "./ZihinModelleri";
import type { BilgiAgaci, BilgiAramaGovdesi, BilgiDugumu, BilgiSayfasi, HafizaZarfi, ZihinModeli } from "./uctipleri";

const UC_AGAC = "/api/hindsight/bilgi-tabani";
const UC_ARAMA = "/api/hindsight/bilgi-arama";
const UC_SAYFA = "/api/hindsight/bilgi-sayfasi";

/** `api.py::api_hindsight_bilgi_arama` bu uçta tavanı 50'ye indiriyor (ölçüldü:
 *  upstream `limit.maximum`). Üst yüzey 20 istiyor; aynı sayı burada da. */
const ARAMA_TAVANI = 20;

/**
 * Ağacı düz listeye açar — üst yüzeyin kendi `flatten`ının karşılığı.
 *
 * NEDEN GEREKİYOR (ve bu ÖLÇÜLDÜ): sayfanın TAZELİĞİ ve TETİKLEYİCİSİ tek-sayfa
 * gövdesinde GELMİYOR; üst yüzey de onları açık sayfanın AĞAÇTAKİ düğümünden
 * okuyor. İkisini sayfa gövdesinde aramak, her sayfada "tazelik bildirilmedi"
 * yazdırırdı — doğru cümle değil: değer var, başka gövdede.
 */
/** Düz listenin SONUCU + DÜŞÜRÜLEN ÖĞE SAYISI — `KovaSeridi` emsali (say + atla). */
export interface DuzAgac {
  readonly dugumler: readonly BilgiDugumu[];
  /** Sözlük olarak okunamadığı için atlanan düğüm sayısı. `0` = ölçüldü, hepsi okundu. */
  readonly okunamayan: number;
}

function duzListe(dugumler: readonly BilgiDugumu[]): DuzAgac {
  const cikti: BilgiDugumu[] = [];
  let okunamayan = 0;
  const gez = (liste: readonly BilgiDugumu[]) => {
    for (const d of liste) {
      // ÖĞE KAPISI (nihai inceleme K-1, `parcalar.tsx::KovaSeridi` deseni): dizinin
      // İÇİ de doğrulanır. `null` bir öğe gelirse aşağıdaki `d.children` okuması bir
      // tip hatası atar ve BÜTÜN ağaç düşer — oysa bu yüzeyin disiplini
      // "tanımadığını çiz, düşme".
      //
      // ATLAMAK YETMEZ, SAYMAK GEREKİR (düzeltme turu 2, Y-4): sessizce düşen bir düğüm
      // ekrandaki sayıyı İŞARETSİZ küçültürdü — `KovaSeridi`nin kendi dersi ("okunamayan
      // öğeyi sıfır sayma, SAYIP yaz"). Sayının okuyucusu çağıranda.
      if (sozluk(d) === null) {
        okunamayan += 1;
        continue;
      }
      cikti.push(d);
      if (Array.isArray(d.children) && d.children.length > 0) gez(d.children);
    }
  };
  gez(dugumler);
  return { dugumler: cikti, okunamayan };
}

/* ---------------------------------------------------------------------------
   AĞAÇ SATIRI — klasör ile sayfa AYRI, ve "türü bildirilmedi" ÜÇÜNCÜ hâl
   Tür gelmediğinde klasör varsaymak sayfayı açılamaz bir kutuya çevirirdi;
   sayfa varsaymak da içi olmayan bir sayfa açardı. Üçüncü hâl ayrı çizilir.
   --------------------------------------------------------------------------- */
function AgacSatiri({
  dugum,
  derinlik,
  acikKlasorler,
  klasorAc,
  secili,
  sec,
}: {
  readonly dugum: BilgiDugumu;
  readonly derinlik: number;
  readonly acikKlasorler: ReadonlySet<string>;
  readonly klasorAc: (kimlik: string) => void;
  readonly secili: string | null;
  readonly sec: (kimlik: string) => void;
}) {
  /* ÖĞE KAPISI — İKİNCİ HAT (düzeltme turu 2 Y-4 → düzeltme turu 4 K-1).
     BİRİNCİ HAT ÇAĞRI YERİNDEDİR: iki `.map` da listeyi `sozluk` ile SÜZER, yani bu bileşene
     `null` bir düğüm bugün ULAŞAMAZ. Bu satır yine de duruyor ve bu bir tercih: üçüncü bir
     çağrı yeri eklendiği gün (ör. arama sonucundan ağaca dönen bir yol) süzmeyi unutmak
     BÜTÜN ağacı düşürürdü — `_kapi_maskele`nin "ikinci hattın anlamı birinci hattın delindiği
     günü karşılamaktır" gerekçesinin aynısı. "Say + atla" BURADA yapılmaz: sayının okuyucusu
     çağırandadır (`Sayfalar` altındaki "N düğüm okunamadı" satırı) ve o sayım `duzListe`den
     gelir — ikinci bir sayaç aynı gerçeğin iki kopyası olurdu. */
  if (sozluk(dugum) === null) return null;
  const kimlik = metin(dugum.id);
  const ad = metin(dugum.name);
  const tur = metin(dugum.kind);
  const cocuklar = Array.isArray(dugum.children) ? dugum.children : [];
  const klasor = tur === "folder";
  const sayfa = tur === "page";
  const acik = kimlik !== null && acikKlasorler.has(kimlik);

  /* TEK EYLEM KAPISI: fare de klavye de BURADAN geçer. İki ayrı gövde yazmak,
     zamanla iki farklı davranışın başlangıcı olurdu. */
  const ac = () => {
    if (kimlik === null) return;
    if (klasor) klasorAc(kimlik);
    else sec(kimlik);
  };

  return (
    <div>
      {/* TREEITEM + KLAVYE (nihai inceleme Ö-6, 2026-09-03): satır `onClick` +
          `cursor-pointer` ile tıklanabilirdi ama odaklanamıyordu (ne `tabIndex`,
          ne `onKeyDown`, ne içinde bir düğme) — yani ağacın TAMAMI yalnız fareyle
          gezilebiliyordu. Kardeşi `Varliklar.tsx` aynı sorunu bu dalda çözmüş ve
          v380 çiviliyor. Klasörde `aria-expanded` de bildirilir: açık/kapalı
          yalnız bir ok ikonuyla söyleniyordu, yani görsel tek kanaldı. */}
      <div
        role="treeitem"
        tabIndex={kimlik === null ? -1 : 0}
        aria-expanded={klasor ? acik : undefined}
        aria-selected={secili !== null && secili === kimlik}
        className={cn(
          "flex items-center gap-1.5 rounded-md px-1.5 py-1 text-sm",
          kimlik !== null && "cursor-pointer hover:bg-muted/60",
          secili !== null && secili === kimlik && "bg-muted",
        )}
        style={{ paddingLeft: `${derinlik * 0.9 + 0.375}rem` }}
        onClick={ac}
        onKeyDown={(e) => {
          if (e.key !== "Enter" && e.key !== " ") return;
          // BOŞLUK SAYFAYI KAYDIRMASIN: `treeitem` bir düğme gibi davranıyor.
          e.preventDefault();
          ac();
        }}
      >
        {klasor ? (
          acik ? (
            <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
          ) : (
            <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
          )
        ) : (
          <span className="size-3.5 shrink-0" />
        )}
        {klasor ? (
          <Folder className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
        ) : sayfa ? (
          <FileText className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
        ) : null}
        <span className="min-w-0 flex-1 truncate" title={ad ?? undefined}>
          {ad ?? (
            <Olculemedi neden="Düğümün adı gelmedi" teknik="ad alanı yok ya da dizge değil" kisa />
          )}
        </span>
        {!klasor && !sayfa ? (
          <Badge variant="outline" className="font-normal text-[10px] text-muted-foreground">
            {tur === null ? "türü bildirilmedi" : `bilinmeyen tür: ${tur}`}
          </Badge>
        ) : null}
        {dugum.managed === true ? (
          <Badge variant="outline" className="font-normal text-[10px] text-muted-foreground">
            yönetilen
          </Badge>
        ) : null}
        {dugum.is_stale === true ? (
          <span className="size-1.5 shrink-0 rounded-full bg-foreground/50" title="kapsamında okunmamış kayıt var" />
        ) : null}
        <span className="shrink-0 text-[10px] text-muted-foreground tabular-nums">
          {damga(dugum.timestamp) ?? (
            <Olculemedi neden="güncelleme yok" teknik="güncelleme damgası gelmedi ya da çözülemedi" kisa />
          )}
        </span>
      </div>
      {/* TÜRÜ BİLDİRİLMEYEN DÜĞÜMÜN ÇOCUKLARI SESSİZCE DÜŞMEZ (inceleme M-3):
          alt ağaç çizilemiyor (düğüm açılamıyor, çünkü klasör olduğu ölçülmedi)
          ama KAÇ TANE olduğu yazılıyor. Sayıyı yazmasaydık eksik bir ağaç tam
          görünürdü — bu dosyanın graf kardeşiyle aynı yasak. */}
      {!klasor && !sayfa && cocuklar.length > 0 ? (
        <div
          className="text-[10px] text-muted-foreground"
          style={{ paddingLeft: `${(derinlik + 1) * 0.9 + 0.375}rem` }}
        >
          {cocuklar.length} alt düğüm çizilmedi — bu düğümün türü bildirilmediği için açılamıyor
        </div>
      ) : null}
      {/* ÇOCUKLAR `role="group"` İÇİNDE (ARIA ağaç sözleşmesi): grup kabı ÖĞENİN
          KENDİSİ değil, öğenin ALTINDAKİ listedir — öğeyi sarmak `aria-expanded`
          ile grubu ilişkilendirmeyi bozardı. */}
      {klasor && acik ? (
        <div role="group">
          {/* AYNI SÜZME, ÖZYİNELEMEDE (düzeltme turu 4, K-1): `key={metin(c.id) …}` de bileşen
              çağrılmadan değerlendirilir. `cocuklar` HAM kalır (yukarıdaki "N alt düğüm
              çizilmedi" sayısı okunamayanları da SAYMALI — çizilmeyen çizilmeyendir). */}
          {cocuklar.filter((c) => sozluk(c) !== null).map((c, i) => (
            <AgacSatiri
              key={metin(c.id) ?? `dugum-${derinlik}-${i}`}
              dugum={c}
              derinlik={derinlik + 1}
              acikKlasorler={acikKlasorler}
              klasorAc={klasorAc}
              secili={secili}
              sec={sec}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

/* --------------------------------------------------------------------------- */

function Sayfalar({ bank }: { readonly bank: string }) {
  const [aramaKutusu, setAramaKutusu] = useState("");
  const [arama, setArama] = useState("");
  const [acikKlasorler, setAcikKlasorler] = useState<ReadonlySet<string>>(new Set());
  const [secili, setSecili] = useState<string | null>(null);

  useEffect(() => {
    setSecili(null);
    setAcikKlasorler(new Set());
  }, [bank]);

  const agacYolu = `${UC_AGAC}?bank=${encodeURIComponent(bank)}`;
  const aramaYolu =
    arama.trim() === ""
      ? null
      : `${UC_ARAMA}?bank=${encodeURIComponent(bank)}&q=${encodeURIComponent(arama.trim())}&limit=${ARAMA_TAVANI}`;
  const sayfaYolu = secili === null ? null : `${UC_SAYFA}?bank=${encodeURIComponent(bank)}&sayfa=${encodeURIComponent(secili)}`;

  const agac = useApi<HafizaZarfi<BilgiAgaci>>(agacYolu);
  const vuruslar = useApi<HafizaZarfi<BilgiAramaGovdesi>>(aramaYolu);
  const sayfa = useApi<HafizaZarfi<BilgiSayfasi>>(sayfaYolu);

  /* AÇIK SAYFANIN AĞAÇTAKİ DÜĞÜMÜ — tazelik ve tetikleyici oradan gelir (yukarıdaki
     şerh). Bulunamazsa `null` ve tazelik satırı bunu kendi diliyle yazar; sessiz
     bir varsayılan koysaydık bayat bir sayfa "güncel" görünürdü. */
  const duz: DuzAgac = Array.isArray(agac.veri?.govde?.roots)
    ? duzListe(agac.veri.govde.roots)
    : { dugumler: [], okunamayan: 0 };
  const agacDugumleri = duz.dugumler;
  const seciliDugum = secili === null ? null : (agacDugumleri.find((d) => metin(d.id) === secili) ?? null);

  const klasorAc = (kimlik: string) =>
    setAcikKlasorler((mevcut) => {
      const yeni = new Set(mevcut);
      if (yeni.has(kimlik)) yeni.delete(kimlik);
      else yeni.add(kimlik);
      return yeni;
    });

  return (
    <div className="grid gap-4 lg:grid-cols-[20rem_minmax(0,1fr)]">
      <div className="flex min-w-0 flex-col gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-muted-foreground text-xs">Sayfalarda ara</span>
          <span className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              value={aramaKutusu}
              onChange={(e) => setAramaKutusu(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") setArama(aramaKutusu.trim());
                if (e.key === "Escape") {
                  setAramaKutusu("");
                  setArama("");
                }
              }}
              placeholder="yazıp Enter'a bas"
              className="h-8 pl-8"
            />
          </span>
        </label>

        {arama.trim() === "" ? (
          <UcKapisi durum={agac} yol={UC_AGAC}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Bilgi ağacı">
                {(g) => {
                  if (!Array.isArray(g.roots)) {
                    return (
                      <Olculemedi
                        neden="Ağaç kökleri tanınmayan bir biçimde geldi"
                        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                      />
                    );
                  }
                  if (g.roots.length === 0) {
                    return (
                      <p className="text-muted-foreground text-sm">
                        Ağaç okundu ve kayıtlı sayfa YOK. Bu ölçülmüş bir boşluktur.
                      </p>
                    );
                  }
                  return (
                    /* YAPI DA BİLDİRİLİR (nihai inceleme Ö-6, 2026-09-03): satırlar
                       tıklanabilir ama odaklanamıyordu VE ağaç olduğu hiçbir yerde
                       yazmıyordu — ekran okuyucu için burası yalnız iç içe kutulardı. */
                    <div className="flex flex-col gap-1">
                      {/* OKUNAMAYAN DÜĞÜM SAYISI EKRANDA (düzeltme turu 2, Y-4 · `KovaSeridi`
                          emsali): sessizce atlanan bir düğüm, ağaçtaki eksikliği İŞARETSİZ
                          bırakırdı — "okuyamadım" ile "yok" aynı görünürdü. */}
                      {duz.okunamayan > 0 ? (
                        <p className="text-muted-foreground text-[11px]">
                          {duz.okunamayan} düğüm okunamadı — sözlük olarak çözülemedi, ağaçta
                          çizilmedi (şema sürüklenmiş olabilir)
                        </p>
                      ) : null}
                      <div className="rounded-lg border p-1" role="tree" aria-label="Bilgi tabanı ağacı">
                        {/* SÜZME `.map`TEN ÖNCE (düzeltme turu 4, tur-2 yeniden-incelemesi K-1):
                            kapı `AgacSatiri` GÖVDESİNİN ilk satırındaydı, ama `key={metin(d.id) …}`
                            bileşen HİÇ ÇAĞRILMADAN önce değerlendirilir — `d` `null` ise orada
                            senkron TypeError atar ve "bütün ağaç düşer" sınıfı bir satır YUKARI
                            taşınmış olurdu. Süzme, sınıfı taşımak yerine YOK EDER: bileşene
                            `null` bir düğüm hiç ulaşmaz. Düşürülen SAYILIR ve yukarıda yazılır —
                            sayım `duzListe`den gelir (aynı ağaç, tek sayaç); burada ikinci bir
                            sayaç kurmak aynı gerçeğin iki kopyası olurdu. */}
                        {g.roots.filter((d) => sozluk(d) !== null).map((d, i) => (
                          <AgacSatiri
                            key={metin(d.id) ?? `kok-${i}`}
                            dugum={d}
                            derinlik={0}
                            acikKlasorler={acikKlasorler}
                            klasorAc={klasorAc}
                            secili={secili}
                            sec={setSecili}
                          />
                        ))}
                      </div>
                    </div>
                  );
                }}
              </ZarfKapisi>
            )}
          </UcKapisi>
        ) : (
          <UcKapisi durum={vuruslar} yol={UC_ARAMA}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Sayfa araması">
                {(g) => {
                  if (!Array.isArray(g.results)) {
                    return (
                      <Olculemedi
                        neden="Arama sonuçları tanınmayan bir biçimde geldi"
                        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                      />
                    );
                  }
                  if (g.results.length === 0) {
                    return (
                      <p className="text-muted-foreground text-sm">
                        Bu sorgu okundu ve eşleşen sayfa YOK. Bu ölçülmüş bir boşluktur.
                      </p>
                    );
                  }
                  return (
                    <div className="flex flex-col gap-1 rounded-lg border p-1">
                      {g.results.map((r, i) => {
                        const kimlik = metin(r.id);
                        const n = sayi(r.score);
                        return (
                          <button
                            key={kimlik ?? `vurus-${i}`}
                            type="button"
                            className="flex flex-col gap-0.5 rounded-md px-2 py-1.5 text-left hover:bg-muted/60"
                            disabled={kimlik === null}
                            onClick={() => kimlik !== null && setSecili(kimlik)}
                          >
                            <span className="flex items-center justify-between gap-2">
                              <span className="min-w-0 truncate text-sm">
                                {metin(r.name) ?? (
                                  <Olculemedi
                                    neden="Sayfanın adı gelmedi"
                                    teknik="ad alanı yok ya da dizge değil"
                                    kisa
                                  />
                                )}
                              </span>
                              <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                                {n === null ? "" : String(n)}
                              </span>
                            </span>
                            {metin(r.snippet) !== null ? (
                              <span className="line-clamp-2 text-[11px] text-muted-foreground">
                                {metin(r.snippet)}
                              </span>
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  );
                }}
              </ZarfKapisi>
            )}
          </UcKapisi>
        )}

        {/* ÜST YÜZEYDE AĞACIN BAŞINDA VE HER KLASÖRÜN YANINDA OLUŞTURMA
            DÜĞMELERİ VAR; sayfa başlığında da düzenle/sil duruyor. */}
        <Faz2Grup>
          <Faz2Dugme ne="yeni bir klasör açar">Klasör oluştur</Faz2Dugme>
          <Faz2Dugme ne="yeni bir bilgi sayfası açar">Sayfa oluştur</Faz2Dugme>
        </Faz2Grup>
      </div>

      <div className="flex min-w-0 flex-col gap-3">
        {secili === null ? (
          <p className="text-muted-foreground text-sm">
            Soldan bir sayfa seç. Klasörler açılır, sayfalar burada okunur.
          </p>
        ) : (
          <UcKapisi durum={sayfa} yol={UC_SAYFA}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Bilgi sayfası">
                {(s) => (
                  <div className="flex flex-col gap-3">
                    <div>
                      <h3 className="font-semibold text-lg">
                        {metin(s.name) ?? (
                          <Olculemedi neden="Sayfanın adı gelmedi" teknik="ad alanı yok ya da dizge değil" />
                        )}
                      </h3>
                      {/* TAZELİK SATIRI MODELİNKİYLE AYNI BİLEŞEN: bir sayfa
                          ağaçta yeri olan bir zihin modelidir (dosya başlığı). */}
                      <TazelikSatiri
                        model={{
                          last_refreshed_at: s.timestamp,
                          is_stale: seciliDugum?.is_stale,
                          trigger: seciliDugum?.trigger as ZihinModeli["trigger"],
                        }}
                      />
                    </div>
                    <div>
                      <Satir etiket="Kaynak sorgu">
                        {metin(s.description) ?? (
                          <Olculemedi
                            neden="Kaynak sorgu gelmedi"
                            teknik="sayfayı besleyen sorgu alanı gelmedi ya da dizge değil"
                            kisa
                          />
                        )}
                      </Satir>
                      <Satir etiket="Etiketler">
                        <Cipler degerler={listeye(s.tags)} tavan={10} ne="Etiket alanı" />
                      </Satir>
                    </div>
                    {metin(s.body) === null ? (
                      <Olculemedi
                        neden="Sayfanın metni gelmedi"
                        teknik="metin alanı gelmedi ya da dizge değil — sayfa henüz hiç sentezlenmemiş olabilir"
                      />
                    ) : (
                      <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-[12px] leading-5">
                        {metin(s.body)}
                      </pre>
                    )}
                    <div className="flex flex-col gap-2">
                      <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                        Sayfanın tamamı
                      </h4>
                      <HamSatirlar govde={s} atla={["body", "tags", "name", "description"]} />
                    </div>
                    <Faz2Grup>
                      <Faz2Dugme ne="sayfanın adını ve kaynak sorgusunu değiştirir">Düzenle</Faz2Dugme>
                      <Faz2Dugme ne="sayfayı besleyen modelin ayarlarını açar">Model ayarları</Faz2Dugme>
                      <Faz2Dugme ne="sayfayı siler">Sil</Faz2Dugme>
                    </Faz2Grup>
                  </div>
                )}
              </ZarfKapisi>
            )}
          </UcKapisi>
        )}
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function BilgiTabani({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  /* SEKME ADRESTEN TÜRER, YEREL DURUMDAN DEĞİL (nihai inceleme Ö-1, 2026-09-03).
     İlk yazım `useState("sayfalar")` idi ve üç giriş kapısı da (sohbet hattındaki
     "Bilgi Tabanı → Meridian dersleri" bağı, `#hafiza` yer imi, ⌘K'nın ders
     anahtarları) hep sayfa ağacını açıyordu: bağ çalışıyor, varış yanlış.
     Görünümün kendisi zaten adresten türüyordu (`HafizaYuzey.tsx`); sekme aynı
     kuralın bir kademe altıdır. */
  const rota = useRota();
  const router = useRouter();
  const sekme = bilgiSekmesiCoz(rota.sorgu);
  const sekmeSec = (yeni: string) => router.push(sekmeliYol(rota.yol, yeni as HafizaBilgiSekmesi));

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-bilgi" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi
          neden="Okunacak banka seçilemedi"
          teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor"
        />
      </BolumKart>
    );
  }

  return (
    <BolumKart kimlik="hafiza-bilgi" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <Tabs value={sekme} onValueChange={sekmeSec} className="flex flex-col gap-3">
        <TabsList>
          <TabsTrigger value="sayfalar">Sayfalar</TabsTrigger>
          <TabsTrigger value="modeller">Zihin modelleri</TabsTrigger>
        </TabsList>
        <TabsContent value="sayfalar">
          <Sayfalar bank={bank} />
        </TabsContent>
        <TabsContent value="modeller">
          <Bolme
            baslik="Çıkarım belgeleri"
            aciklama="Bankanın kendi sentezlediği metinler. Bir sayfa, ağaçta yeri olan bir zihin modelidir — bu sekme yeri OLMAYANLARI da gösterir."
          >
            <ZihinModelleri bank={bank} />
          </Bolme>
        </TabsContent>
      </Tabs>
    </BolumKart>
  );
}
