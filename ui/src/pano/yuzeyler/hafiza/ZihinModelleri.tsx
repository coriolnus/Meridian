"use client";

/* ============================================================================
   HAFIZA · ZİHİN MODELLERİ — Bilgi Tabanı görünümünün İKİNCİ sekmesi
   ----------------------------------------------------------------------------
   YERİ ÖLÇÜLDÜ, SEÇİLMEDİ: üst yüzeyde zihin modellerinin ayrı bir kenar çubuğu
   durağı YOKTUR; `knowledge` sekmesinin iki alt sekmesinden ikincisidir
   (birincisi Sayfalar). Ayrı bir durak açsaydık kenar çubuğu dokuz maddeye
   çıkar ve birebirleştirmenin ölçülebilir yarısı (aynı yerde aynı madde)
   kaybolurdu.

   AYNI ÖLÇÜM BİR ŞEY DAHA SÖYLÜYOR ve üst yüzeyin kendi şerhi de bunu yazıyor:
   BİR SAYFA, AĞAÇTA YERİ OLAN BİR ZİHİN MODELİDİR. İki sekme aynı nesnenin iki
   yüzüdür; bu yüzden tazelik satırı ikisinde de AYNI biçimde çizilir.

   ---------------------------------------------------------------------------
   "SONRAKİ TAZELEME" BURADA YAŞIYOR — VE HESAPLANMIYOR
   ---------------------------------------------------------------------------
   Görev 2 bu değeri Ana Sayfa'da çizemedi ve gerekçesini yazdı: girdisi bir
   BANKA alanı değil, bir zihin modelinin TETİKLEYİCİSİdir. Ölçüm doğrulandı ve
   değerin evi burasıdır.

   AMA SAAT HESAPLANMAZ. Üst yüzey cron ifadesini kendi cron kütüphanesiyle
   çözüp "3 saat sonra" yazıyor. Bir cron çözücüyü panoya taşımak, ölçülmemiş
   bir zamanlama semantiğini (saat dilimi, adım sözdizimi, ay/gün çakışması)
   ikinci kez uygulamak olurdu — ve yanlış hesaplanmış bir saat, hiç
   hesaplanmamış bir saatten daha zararlıdır, çünkü kendinden emin görünür.
   Ekran bu yüzden İFADENİN KENDİSİNİ basar; "ne zaman"ı operatör okur.
   ============================================================================ */
import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import { useApi } from "../../veri";
import { Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";

import { Bolme, Cipler, Faz2Dugme, Faz2Grup, HamSatirlar, Sayfalama, Secim, SuzgecSeridi, ZarfKapisi, damga, listeye, metin, sayi, sozluk } from "./parcalar";
import type { HafizaZarfi, HamGovde, SayfaliGovde, ZihinModeli } from "./uctipleri";

const UC_LISTE = "/api/hindsight/zihin-modelleri";
const UC_TEK = "/api/hindsight/zihin-modeli";
const UC_TARIHCE = "/api/hindsight/zihin-modeli-tarihce";

const SAYFA_BOYU = 25;

/** `api.py::_HAFIZA_DETAY_DUZEYI` — üç değer, üst servisin şemasından ölçüldü.
 *  Buraya fazladan bir değer yazmak seçeneği çalışır gösterir ama sunucu onu
 *  tanımaz ve parametreyi HİÇ göndermez: ekran bir ayrıntı düzeyi seçili
 *  gösterip başka bir düzeyin gövdesini çizerdi. */
const DETAY_DUZEYLERI = [
  { deger: "metadata", etiket: "yalnız künye" },
  { deger: "content", etiket: "künye + metin" },
  { deger: "full", etiket: "tamamı" },
] as const;

/**
 * TAZELİK SATIRI — üst yüzeyin `freshness-line` parçasının karşılığı.
 *
 * `is_stale` ÜÇ DEĞERLİDİR ve üçü ekranda ayrı: `true` (kapsamında yeni kayıt
 * var, model onu okumadı) · `false` (güncel) · gelmedi. Gelmediğinde "güncel"
 * demek ölçülmemiş bir bileşeni yeşile boyamak olurdu.
 */
export function TazelikSatiri({ model }: { readonly model: ZihinModeli }) {
  const tetik = sozluk(model.trigger);
  const cron = tetik === null ? null : metin(tetik.refresh_cron);
  const birlestirmeSonrasi = tetik === null ? undefined : tetik.refresh_after_consolidation;
  const bayat = model.is_stale;
  const tazelendi = damga(model.last_refreshed_at);
  const okunan = damga(model.last_memory_seen_at);

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
      {bayat === true ? (
        <Badge variant="outline" className="font-normal text-[11px]">
          kapsamında okunmamış kayıt var
        </Badge>
      ) : bayat === false ? (
        <Badge variant="outline" className="font-normal text-[11px]">
          güncel
        </Badge>
      ) : (
        <Olculemedi
          neden="Tazelik bildirilmedi"
          teknik="bayatlık alanı gelmedi — 'güncel' demek ölçülmemiş bir durumu ölçülmüş göstermek olurdu"
          kisa
        />
      )}
      <span>
        tazelendi{" "}
        {tazelendi ?? (
          <Olculemedi neden="tazeleme zamanı gelmedi" teknik="tazeleme damgası gelmedi ya da çözülemedi" kisa />
        )}
      </span>
      <span>
        okuduğu son kayıt{" "}
        {okunan ?? (
          <Olculemedi
            neden="okunan kayıt damgası gelmedi"
            teknik="model hiç kayıt okumamış olabilir ya da damga çözülemedi"
            kisa
          />
        )}
      </span>
      <span>
        sonraki:{" "}
        {cron !== null ? (
          <span className="font-mono" title="cron ifadesi — bir sonraki koşum saati bu panoda hesaplanmaz">
            {cron}
          </span>
        ) : birlestirmeSonrasi === true ? (
          "birleştirmeden sonra"
        ) : birlestirmeSonrasi === false ? (
          "elle"
        ) : (
          <Olculemedi
            neden="tetikleyici gelmedi"
            teknik="ne zamanlama ifadesi ne de birleştirme bayrağı geldi — sonraki tazeleme okunamıyor"
            kisa
          />
        )}
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ÇEKMECE
   --------------------------------------------------------------------------- */
function ModelCekmecesi({
  model,
  detay,
  tarihce,
  sekme,
  setSekme,
}: {
  readonly model: ZihinModeli;
  readonly detay: ReturnType<typeof useApi<HafizaZarfi<ZihinModeli>>>;
  readonly tarihce: ReturnType<typeof useApi<HafizaZarfi<HamGovde>>>;
  readonly sekme: string;
  readonly setSekme: (s: string) => void;
}) {
  return (
    <Tabs value={sekme} onValueChange={setSekme} className="flex min-h-0 flex-1 flex-col gap-3">
      <TabsList>
        <TabsTrigger value="genel">Genel</TabsTrigger>
        <TabsTrigger value="tarihce">Tarihçe</TabsTrigger>
      </TabsList>

      <TabsContent value="genel" className="flex flex-col gap-4">
        <TazelikSatiri model={model} />
        <UcKapisi durum={detay} yol={UC_TEK}>
          {(z) => (
            <ZarfKapisi zarf={z} ne="Zihin modeli">
              {(m) => (
                <div className="flex flex-col gap-4">
                  <div>
                    <Satir etiket="Kaynak sorgu">
                      {metin(m.source_query) ?? (
                        <Olculemedi
                          neden="Kaynak sorgu gelmedi"
                          teknik="modelin kapsamını belirleyen sorgu alanı gelmedi ya da dizge değil"
                          kisa
                        />
                      )}
                    </Satir>
                    <Satir etiket="Etiketler">
                      <Cipler degerler={listeye(m.tags)} tavan={10} ne="Etiket alanı" />
                    </Satir>
                    <Satir etiket="Yanıt bütçesi">
                      {sayi(m.max_tokens) === null ? (
                        <Olculemedi neden="Bütçe gelmedi" teknik="jeton bütçesi gelmedi ya da sayı değil" kisa />
                      ) : (
                        <span className="tabular-nums">
                          {(sayi(m.max_tokens) as number).toLocaleString("tr-TR")} jeton
                        </span>
                      )}
                    </Satir>
                    <Satir etiket="Oluşturma">
                      {damga(m.created_at) ?? (
                        <Olculemedi
                          neden="Oluşturma zamanı gelmedi"
                          teknik="oluşturma damgası gelmedi ya da çözülemedi"
                          kisa
                        />
                      )}
                    </Satir>
                  </div>

                  <div className="flex flex-col gap-2">
                    <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      Sentezlenmiş metin
                    </h4>
                    {metin(m.content) === null ? (
                      <Olculemedi
                        neden="Metin gelmedi"
                        teknik="metin yalnız ayrıntı düzeyi 'künye + metin' ya da 'tamamı' iken gelir; düzey künyeyse bu bir eksiklik değildir"
                      />
                    ) : (
                      /* MARKDOWN ÇİZİLMEZ: üst yüzey metni markdown olarak
                         işliyor, panoda markdown işleyicisi yok ve bir tane
                         eklemek bu turun kapsamı dışında. Ham metin, biçimlenmiş
                         ama YANLIŞ bir metinden dürüsttür. */
                      <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-[12px] leading-5">
                        {metin(m.content)}
                      </pre>
                    )}
                  </div>

                  <div className="flex flex-col gap-2">
                    <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      Tetikleyici
                    </h4>
                    {sozluk(m.trigger) === null ? (
                      <Olculemedi
                        neden="Tetikleyici gelmedi"
                        teknik="tetikleyici alanı gelmedi ya da sözlük değil — tazeleme kuralı okunamıyor"
                      />
                    ) : (
                      <HamSatirlar govde={sozluk(m.trigger) as HamGovde} />
                    )}
                  </div>

                  <div className="flex flex-col gap-2">
                    <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      Kaydın tamamı
                    </h4>
                    <HamSatirlar govde={m} atla={["content", "trigger", "tags"]} />
                  </div>
                </div>
              )}
            </ZarfKapisi>
          )}
        </UcKapisi>

        {/* ÜST YÜZEYDE BURADA DÖRT YAZMA DÜĞMESİ VAR ve yerlerinde duruyorlar. */}
        <Faz2Grup>
          <Faz2Dugme ne="modeli şimdi yeniden sentezler">Şimdi tazele</Faz2Dugme>
          <Faz2Dugme ne="tazelemeyi yazmadan dener ve sonucu gösterir">Kuru koşum</Faz2Dugme>
          <Faz2Dugme ne="modelin metnini boşaltır">İçeriği temizle</Faz2Dugme>
          <Faz2Dugme ne="modeli siler">Sil</Faz2Dugme>
        </Faz2Grup>
      </TabsContent>

      <TabsContent value="tarihce" className="flex flex-col gap-3">
        <UcKapisi durum={tarihce} yol={UC_TARIHCE}>
          {(z) => (
            <ZarfKapisi zarf={z} ne="Model tarihçesi">
              {(g) => (
                <>
                  {/* TARİHÇENİN ŞEKLİ ÖLÇÜLMEDİ (Görev 1 bulgusu I-2: upstream'de
                      bu yanıtın şeması literal `{}`). Ham basılıyor ve bu bir
                      eksiklik değil, ölçülmemiş bir şeklin dürüst çizimi. */}
                  <HamSatirlar govde={g} />
                  <p className="text-muted-foreground text-[11px]">
                    Tarihçenin alan şeması üst servisin sözleşmesinde boş — bu yüzden gövde
                    anahtarlarıyla ham basılıyor; alan adı UYDURULMUYOR
                  </p>
                </>
              )}
            </ZarfKapisi>
          )}
        </UcKapisi>
      </TabsContent>
    </Tabs>
  );
}

/* --------------------------------------------------------------------------- */

export function ZihinModelleri({ bank }: { readonly bank: string }) {
  const [arama, setArama] = useState("");
  const [etiketler, setEtiketler] = useState("");
  const [esleme, setEsleme] = useState("any");
  const [detayDuzeyi, setDetayDuzeyi] = useState("metadata");
  const [atlanan, setAtlanan] = useState(0);
  const [acik, setAcik] = useState<ZihinModeli | null>(null);
  const [sekme, setSekme] = useState("genel");
  /* ÇEKMECE ANAHTARI: yalnız AÇIKKEN ilerler (aşağıdaki `SheetContent` şerhi). */
  const [cekmeceAnahtari, setCekmeceAnahtari] = useState("model");

  useEffect(() => {
    setAtlanan(0);
    setAcik(null);
  }, [bank, etiketler, esleme]);

  useEffect(() => {
    setSekme("genel");
  }, [acik]);

  /* LİSTE KÜNYE DÜZEYİNDE OKUNUR: metni de istemek her satırda sentezlenmiş
     paragrafları taşımak olurdu ve tablo onu zaten çizmiyor. Metin ancak
     çekmece açıldığında, TEK model için isteniyor. */
  const listeYolu = [
    `${UC_LISTE}?bank=${encodeURIComponent(bank)}`,
    `limit=${SAYFA_BOYU}`,
    `offset=${atlanan}`,
    "detail=metadata",
    etiketler ? `tags=${encodeURIComponent(etiketler)}&tags_match=${encodeURIComponent(esleme)}` : "",
  ]
    .filter(Boolean)
    .join("&");
  const liste = useApi<HafizaZarfi<SayfaliGovde<ZihinModeli>>>(listeYolu);

  const acikKimlik = acik === null ? null : metin(acik.id);

  /* Anahtar KAPANIŞTA sabit kalır: kapanış render'ında anahtarı değiştirmek
     Radix'in kapanış animasyonunu atlatırdı (T2 yeniden-incelemesi). */
  useEffect(() => {
    if (acikKimlik !== null) setCekmeceAnahtari(acikKimlik);
  }, [acikKimlik]);
  const detayYolu =
    acikKimlik === null
      ? null
      : `${UC_TEK}?bank=${encodeURIComponent(bank)}&kimlik=${encodeURIComponent(acikKimlik)}&detail=${encodeURIComponent(detayDuzeyi)}`;
  const detay = useApi<HafizaZarfi<ZihinModeli>>(detayYolu);

  const tarihceYolu =
    acikKimlik === null || sekme !== "tarihce"
      ? null
      : `${UC_TARIHCE}?bank=${encodeURIComponent(bank)}&kimlik=${encodeURIComponent(acikKimlik)}`;
  const tarihce = useApi<HafizaZarfi<HamGovde>>(tarihceYolu);

  /* ARAMA KUTUSU YEREL SÜZER VE BUNU SÖYLER: bu ucun metin araması YOK
     (`api.py::api_hindsight_zihin_modelleri` yalnız etiket süzgeci taşıyor).
     Kutuyu sunucuya bağlıymış gibi göstermek, gelmeyen sonuçları "kayıt yok"
     diye okuturdu; yerel süzme ise yalnız AÇIK SAYFAYI süzer. */
  const yerelSuz = (ogeler: readonly ZihinModeli[]): readonly ZihinModeli[] => {
    const q = arama.trim().toLocaleLowerCase("tr-TR");
    if (q === "") return ogeler;
    return ogeler.filter((m) => (metin(m.name) ?? "").toLocaleLowerCase("tr-TR").includes(q));
  };

  return (
    <div className="flex flex-col gap-4">
      <SuzgecSeridi
        arama={arama}
        setArama={setArama}
        etiketler={etiketler}
        setEtiketler={setEtiketler}
        esleme={esleme}
        setEsleme={setEsleme}
        aramaEtiketi="Modellerde ara (yalnız açık sayfada)"
      />
      <p className="text-muted-foreground text-[11px]">
        Metin araması bu uçta YOKTUR — kutu yalnız AÇIK SAYFAYI süzer ve bu yüzden boş sonuç
        "bankada yok" demek değildir; etiket süzgeci ise sunucuda çalışır
      </p>

      <UcKapisi durum={liste} yol={UC_LISTE}>
        {(z) => (
          <ZarfKapisi zarf={z} ne="Zihin modelleri">
            {(g) => {
              if (!Array.isArray(g.items)) {
                return (
                  <Olculemedi
                    neden="Model listesi tanınmayan bir biçimde geldi"
                    teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                  />
                );
              }
              if (g.items.length === 0) {
                return (
                  <p className="text-muted-foreground text-sm">
                    {atlanan === 0
                      ? "Bu banka okundu ve tanımlı zihin modeli YOK. Bu ölçülmüş bir boşluktur."
                      : "Bu sayfada model YOK — liste daha önceki bir sayfada bitmiş."}
                  </p>
                );
              }
              const gorunen = yerelSuz(g.items);
              if (gorunen.length === 0) {
                return (
                  <p className="text-muted-foreground text-sm">
                    Bu sayfada arama kutusuna uyan model yok — kutu yalnız açık sayfayı süzüyor,
                    sonraki sayfalarda olabilir
                  </p>
                );
              }
              return (
                <div className="overflow-x-auto">
                  <Table className="min-w-[46rem]">
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead>Model</TableHead>
                        <TableHead className="w-52">Etiketler</TableHead>
                        <TableHead>Tazelik</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {gorunen.map((m, i) => {
                        const kimlik = metin(m.id);
                        const ad = metin(m.name);
                        return (
                          <TableRow
                            key={kimlik ?? `model-${atlanan + i}`}
                            className={cn(kimlik !== null && "cursor-pointer hover:bg-muted/50")}
                            onClick={kimlik === null ? undefined : () => setAcik(m)}
                          >
                            <TableCell className="max-w-0">
                              {ad === null ? (
                                <Olculemedi
                                  neden="Modelin adı gelmedi"
                                  teknik="ad alanı yok ya da dizge değil"
                                  kisa
                                />
                              ) : kimlik === null ? (
                                <span className="block truncate font-medium text-sm" title={ad}>
                                  {ad}
                                </span>
                              ) : (
                                /* DÜĞME, ÇÜNKÜ KLAVYE (nihai inceleme Ö-6): satır
                                   tıklanabilirdi ama odaklanamıyordu — `Varliklar.tsx`
                                   deseni, aynı gerekçeyle. */
                                <button
                                  type="button"
                                  className="block w-full truncate text-left font-medium text-sm hover:underline"
                                  title={ad}
                                  onClick={() => setAcik(m)}
                                >
                                  {ad}
                                </button>
                              )}
                              <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                                {metin(m.source_query) ?? (
                                  <Olculemedi
                                    neden="kaynak sorgu gelmedi"
                                    teknik="modelin kapsamını belirleyen sorgu alanı yok ya da dizge değil"
                                    kisa
                                  />
                                )}
                              </span>
                            </TableCell>
                            <TableCell>
                              <Cipler degerler={listeye(m.tags)} tavan={3} ne="Etiket alanı" />
                            </TableCell>
                            <TableCell>
                              <TazelikSatiri model={m} />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              );
            }}
          </ZarfKapisi>
        )}
      </UcKapisi>

      <UcKapisi durum={liste} yol={UC_LISTE} iskelet={<></>}>
        {(z) =>
          z.neden || !z.govde ? null : (
            <Sayfalama
              atlanan={atlanan}
              gelen={(z.govde.items ?? []).length}
              sayfaBoyu={SAYFA_BOYU}
              toplam={sayi(z.govde.total)}
              setAtlanan={setAtlanan}
            />
          )
        }
      </UcKapisi>

      <Bolme baslik="Yeni model" aciklama="Üst yüzey bu listenin başında bir oluşturma düğmesi taşıyor.">
        <Faz2Grup>
          <Faz2Dugme ne="yeni bir zihin modeli tanımlar">Model oluştur</Faz2Dugme>
        </Faz2Grup>
      </Bolme>

      <Sheet
        open={acik !== null}
        onOpenChange={(a) => {
          if (!a) setAcik(null);
        }}
      >
        {/* `key` MODEL KİMLİĞİDİR (Görev 2 incelemesi, bulgu M-5): veri katmanı yol
            değişince eski gövdeyi TEMİZLEMİYOR ve kapı yalnız "veri boş mu" diye
            soruyor. Anahtar olmadan A modelinin metni B'nin başlığı altında
            çizilebilirdi. Kapanışta anahtar SABİT kalır (`cekmeceAnahtari`):
            `open` false olan render'da anahtarı değiştirmek çekmecenin kapanış
            animasyonunu atlatırdı (T2 yeniden-incelemesi). */}
        <SheetContent key={cekmeceAnahtari} side="right" className="w-full sm:max-w-2xl">
          <SheetHeader className="pr-10">
            <SheetTitle className="flex items-center gap-2 text-base leading-6">
              <Sparkles className="size-4 shrink-0 text-muted-foreground" aria-hidden />
              {acik === null ? "Zihin modeli" : (metin(acik.name) ?? "Zihin modeli")}
            </SheetTitle>
            <SheetDescription className="break-all font-mono text-[11px]">
              {acikKimlik ?? "model seçilmedi"}
            </SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
            {acik === null ? (
              <p className="text-muted-foreground text-sm">Tablodaki bir satıra tıkla.</p>
            ) : (
              <>
                <Secim
                  etiket="Ayrıntı düzeyi"
                  deger={detayDuzeyi}
                  setDeger={setDetayDuzeyi}
                  secenekler={DETAY_DUZEYLERI}
                  genislik="w-44"
                />
                <ModelCekmecesi
                  model={acik}
                  detay={detay}
                  tarihce={tarihce}
                  sekme={sekme}
                  setSekme={setSekme}
                />
              </>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
