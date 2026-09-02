"use client";

/* ============================================================================
   HAFIZA · BELGELER — üst yüzeyin `documents` görünümünün karşılığı
   ----------------------------------------------------------------------------
   SÜTUNLAR OKUNDU, UYDURULMADI: üst yüzeyin tablosu (`documents-view.tsx`) dört
   sütun çiziyor — belge kimliği (+ son güncelleme) · etiketler ve künye · boyut ·
   çıkan kayıt sayısı — ve satıra tıklamak belge çekmecesini açıyor. Alan adlarının
   TAMAMI ayrıca A1'de ölçüldü (2026-09-02), yani bu tablo bu yüzeyin en sağlam
   zeminli parçası.

   BOYUT SÜTUNU BİR ÇEVİRİ TAŞIMAZ: üst yüzey `text_length` alanını BAYT gibi
   biçimlendiriyor (`formatBytes`), oysa alanın adı da şeması da UZUNLUK diyor.
   Çok baytlı harflerde (Türkçe metinlerde her gün) ikisi aynı sayı değildir ve
   "5,3 KB" yazan bir hücre ölçülmemiş bir birimi ölçülmüş gibi gösterirdi. Burada
   sayı KARAKTER olarak yazılıyor — birimi kendi adından geliyor.

   ---------------------------------------------------------------------------
   ÇEKMECEDE ÜÇ SEKME VAR, BİZDE İKİ — VE ÜÇÜNCÜNÜN YOKLUĞU YAZILI
   ---------------------------------------------------------------------------
   Üst yüzeyin belge çekmecesi Genel · Kayıtlar · Parçalar diye üç sekme taşıyor.
   Kayıtlar sekmesi belgeden çıkan bellekleri gömülü bir tablo olarak çiziyor;
   bizim vekilimiz bunu DESTEKLİYOR (liste ucu belge kimliğiyle süzülebiliyor) ama
   iki görünüm arasında süzgeç taşıyan bir bağ bu turun kapsamı dışında. Çekmece
   bunu söylüyor — sekmeyi çizip boş bırakmak, olmayan bir yeteneği var göstermek
   olurdu.

   BELGENİN TAM METNİ BU YÜZEYDE YOK ve bu bir arıza değil, ölçülmüş bir kapsam:
   liste satırı metni taşımıyor (uzunluğunu taşıyor) ve tek-belge ucunun vekili
   açılmadı. Çekmece "metin yok" demez, "bu yüzeyden okunmuyor" der.

   PARÇALAR İSTEK ÜZERİNE OKUNUR: sekmeye basılmadan çağrı açılmaz. Bir belgenin
   parçaları yüzlerce satır olabilir ve tabloyu açan herkes için önden çekmek,
   okunmayan bir yükü her tıklamada taşımak olurdu.
   ============================================================================ */
import { useEffect, useState } from "react";
import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { useApi, type Durum } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";
import {
  Cipler,
  Faz2Dugme,
  Faz2Grup,
  HamSatirlar,
  Sayfalama,
  SuzgecSeridi,
  ZarfKapisi,
  damga,
  listeye,
  metin,
  sayi,
  sozluk,
  uzunlukMetni,
} from "./parcalar";
import type { BelgeParcasi, HafizaBelgesi, HafizaZarfi, SayfaliGovde } from "./uctipleri";

const UC_BELGELER = "/api/hindsight/belgeler";
const UC_PARCALAR = "/api/hindsight/belge-parcalari";

/* Sayfa boyu bir GÖRÜNÜM kararıdır (gerekçe `Bellekler.tsx`te birebir aynı);
   sunucu tavanı burada TEKRAR YAZILMAZ, iki kopya sessizce ayrışır. */
const SAYFA_BOYU = 25;
const PARCA_SAYFA_BOYU = 25;

/* ZARF KAPISI ARTIK ORTAK (`parcalar.tsx`) — VE BU BİR TEK-KAYNAK DÜZELTMESİDİR.
   Bu dosya onu kendi içinde tanımlıyordu; Görev 3'ün beş görünümü de aynı zarfı
   okuyunca ikinci bir kopya doğacaktı ve iki kopya sessizce ayrışırdı (Görev 2
   incelemesi, bulgu I-5'in aynı sınıfı). Ortak sürüm daha GENELdir: yalnız
   sayfalı gövdeyi değil, herhangi bir gövdeyi okur — buradaki kullanım onun bir
   örneğidir. */

/* ---------------------------------------------------------------------------
   PARÇA SATIRI — üst yüzeyin `ChunkRow`unun karşılığı: kapalı hâlde künye,
   açık hâlde metnin tamamı. Metin ÖNDEN kırpılmaz, yalnız kapalıyken önizlenir.
   --------------------------------------------------------------------------- */
function ParcaSatiri({ parca }: { readonly parca: BelgeParcasi }) {
  const [acik, setAcik] = useState(false);
  const govdeMetni = metin(parca.chunk_text);
  const sira = sayi(parca.chunk_index);
  const onizleme = govdeMetni === null ? null : govdeMetni.length > 150 ? `${govdeMetni.slice(0, 150)}…` : govdeMetni;
  return (
    <div className="border-b last:border-b-0">
      <button
        type="button"
        className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-muted/40"
        onClick={() => setAcik((a) => !a)}
      >
        <span className="w-10 shrink-0 font-mono text-muted-foreground text-xs tabular-nums">
          {sira === null ? "—" : `#${sira}`}
        </span>
        <span className="w-32 shrink-0 text-[11px] text-muted-foreground tabular-nums">
          {govdeMetni === null ? "" : `${govdeMetni.length.toLocaleString("tr-TR")} karakter`}
        </span>
        {!acik ? (
          onizleme === null ? (
            <Olculemedi neden="Parçanın metni gelmedi" teknik="parça metni alanı gelmedi ya da dizge değil" kisa />
          ) : (
            <span className="min-w-0 truncate text-foreground/60 text-xs">{onizleme}</span>
          )
        ) : null}
      </button>
      {acik ? (
        <div className="px-3 pb-3">
          {govdeMetni === null ? (
            <Olculemedi neden="Parçanın metni gelmedi" teknik="parça metni alanı gelmedi ya da dizge değil" />
          ) : (
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 font-mono text-[11px] leading-5">
              {govdeMetni}
            </pre>
          )}
          <HamSatirlar govde={parca} atla={["chunk_text"]} />
        </div>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ÇEKMECE
   --------------------------------------------------------------------------- */

function BelgeCekmecesi({
  belge,
  parcalar,
  parcaAtlanan,
  setParcaAtlanan,
  sekme,
  setSekme,
}: {
  readonly belge: HafizaBelgesi;
  readonly parcalar: Durum<HafizaZarfi<SayfaliGovde<BelgeParcasi>>>;
  readonly parcaAtlanan: number;
  readonly setParcaAtlanan: (f: (n: number) => number) => void;
  readonly sekme: string;
  readonly setSekme: (s: string) => void;
}) {
  const kunye = sozluk(belge.document_metadata);
  const alim = sozluk(belge.retain_params);
  return (
    <Tabs value={sekme} onValueChange={setSekme} className="flex min-h-0 flex-1 flex-col gap-3">
      <TabsList>
        <TabsTrigger value="genel">Genel</TabsTrigger>
        <TabsTrigger value="parcalar">Parçalar</TabsTrigger>
      </TabsList>

      <TabsContent value="genel" className="flex flex-col gap-4">
        <div>
          <Satir etiket="Oluşturma">
            {damga(belge.created_at) ?? <Olculemedi neden="Oluşturma zamanı gelmedi" teknik="oluşturma damgası gelmedi ya da çözülemedi" kisa />}
          </Satir>
          <Satir etiket="Son güncelleme">
            {damga(belge.updated_at) ?? <Olculemedi neden="Güncelleme zamanı gelmedi" teknik="güncelleme damgası gelmedi ya da çözülemedi" kisa />}
          </Satir>
          <Satir etiket="Uzunluk">
            {uzunlukMetni(belge.text_length) ?? <Olculemedi neden="Uzunluk gelmedi" teknik="metin uzunluğu alanı gelmedi ya da sayı değil" kisa />}
          </Satir>
          <Satir etiket="Çıkan kayıt">
            {sayi(belge.memory_unit_count) !== null ? (
              <span className="tabular-nums">{(sayi(belge.memory_unit_count) as number).toLocaleString("tr-TR")}</span>
            ) : (
              <Olculemedi neden="Kayıt sayısı gelmedi" teknik="belgeden çıkan kayıt sayacı gelmedi ya da sayı değil" kisa />
            )}
          </Satir>
          <Satir etiket="Etiketler">
            <Cipler degerler={listeye(belge.tags)} tavan={10} ne="Etiket alanı" />
          </Satir>
        </div>

        <div className="flex flex-col gap-2">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Belge künyesi</h4>
          {kunye === null ? (
            <Olculemedi neden="Künye gelmedi" teknik="künye alanı gelmedi ya da sözlük değil — biçimi kaynağa göre değişir ve şeması yoktur" />
          ) : (
            <HamSatirlar govde={kunye} />
          )}
        </div>

        <div className="flex flex-col gap-2">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">İçe aktarım ayarları</h4>
          {alim === null ? (
            <Olculemedi neden="İçe aktarım ayarları gelmedi" teknik="alım parametreleri alanı gelmedi ya da sözlük değil" />
          ) : (
            <HamSatirlar govde={alim} />
          )}
        </div>

        <div className="flex flex-col gap-2">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Satırın tamamı</h4>
          <HamSatirlar govde={belge} atla={["tags", "document_metadata", "retain_params"]} />
        </div>

        <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
          <span className="font-medium">Bu çekmecenin kapsamı: </span>
          belgenin TAM METNİ burada okunmuyor — liste satırı metni değil uzunluğunu taşıyor ve
          tek-belge ucunun panoda karşılığı yok. Belgeden çıkan bellekleri gömülü bir tablo olarak
          göstermek de bu turda çizilmedi; kayıtlar Bellekler görünümünde duruyor.
        </p>

        {/* ÜST YÜZEYDE BURADA BEŞ YAZMA DÜĞMESİ VAR ve yerlerinde duruyorlar. */}
        <Faz2Grup>
          <Faz2Dugme ne="belgeyi baştan işler ve kayıtlarını yeniden çıkarır">Yeniden işle</Faz2Dugme>
          <Faz2Dugme ne="belgenin etiketlerini değiştirir">Etiketleri düzenle</Faz2Dugme>
          <Faz2Dugme ne="belgenin metnini değiştirir">İçeriği düzenle</Faz2Dugme>
          <Faz2Dugme ne="belgeyi dosya olarak dışa aktarır">Dışa aktar</Faz2Dugme>
          <Faz2Dugme ne="belgeyi ve ondan çıkan bütün kayıtları siler">Sil</Faz2Dugme>
        </Faz2Grup>
      </TabsContent>

      <TabsContent value="parcalar" className="flex flex-col gap-3">
        <UcKapisi durum={parcalar} yol={UC_PARCALAR}>
          {(z) => (
            <>
            <ZarfKapisi zarf={z} ne="Belge parçaları">
              {(g) => {
                const ogeler = g.items ?? [];
                if (!Array.isArray(g.items)) {
                  return <Olculemedi neden="Parça listesi tanınmayan bir biçimde geldi" teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir" />;
                }
                if (ogeler.length === 0) {
                  return (
                    <p className="text-muted-foreground text-sm">
                      {parcaAtlanan === 0
                        ? "Bu belge okundu ve parçaya bölünmüş hâli YOK. Bu ölçülmüş bir boşluktur."
                        : "Bu sayfada parça YOK — liste daha önceki bir sayfada bitmiş."}
                    </p>
                  );
                }
                return (
                  <div className="rounded-lg border">
                    {ogeler.map((p, i) => (
                      <ParcaSatiri key={metin(p.chunk_id) ?? `parca-${parcaAtlanan + i}`} parca={p} />
                    ))}
                  </div>
                );
              }}
            </ZarfKapisi>
            {/* Parça sayfalaması da kapının İÇİNDE — aynı gerekçe (M-4). */}
            {z.neden || !z.govde ? null : (
              <Sayfalama
                atlanan={parcaAtlanan}
                gelen={(z.govde.items ?? []).length}
                sayfaBoyu={PARCA_SAYFA_BOYU}
                toplam={z.govde.total}
                setAtlanan={setParcaAtlanan}
              />
            )}
            </>
          )}
        </UcKapisi>
      </TabsContent>
    </Tabs>
  );
}

/* --------------------------------------------------------------------------- */

export function Belgeler({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  const [arama, setArama] = useState("");
  const [etiketler, setEtiketler] = useState("");
  const [esleme, setEsleme] = useState("any");
  const [atlanan, setAtlanan] = useState(0);
  const [acikBelge, setAcikBelge] = useState<HafizaBelgesi | null>(null);
  const [sekme, setSekme] = useState("genel");
  const [parcaAtlanan, setParcaAtlanan] = useState(0);
  /* ÇEKMECE ANAHTARI: yalnız AÇIKKEN ilerler (aşağıdaki `SheetContent` şerhi). */
  const [cekmeceAnahtari, setCekmeceAnahtari] = useState("bos");

  useEffect(() => {
    setAtlanan(0);
    setAcikBelge(null);
  }, [bank, arama, etiketler, esleme]);

  /* ÇEKMECE HER AÇILDIĞINDA GENEL SEKMESİNDEN BAŞLAR: önceki belgenin parça
     sayfasında kalmak, yeni belgenin dördüncü sayfasını sormak olurdu. */
  useEffect(() => {
    setSekme("genel");
    setParcaAtlanan(0);
  }, [acikBelge]);

  const sorgu =
    bank === null
      ? null
      : [
          `${UC_BELGELER}?bank=${encodeURIComponent(bank)}`,
          `limit=${SAYFA_BOYU}`,
          `offset=${atlanan}`,
          arama ? `q=${encodeURIComponent(arama)}` : "",
          etiketler ? `tags=${encodeURIComponent(etiketler)}&tags_match=${encodeURIComponent(esleme)}` : "",
        ]
          .filter(Boolean)
          .join("&");
  const belgeler = useApi<HafizaZarfi<SayfaliGovde<HafizaBelgesi>>>(sorgu);

  /* PARÇALAR YALNIZ SEKME AÇIKKEN OKUNUR (dosya başlığındaki bedel şerhi):
     yol boşken `useApi` hiç istek açmaz. */
  const acikKimlik = acikBelge === null ? null : metin(acikBelge.id);

  /* Anahtar KAPANIŞTA sabit kalır: `acikKimlik` null olduğunda son açık kimlik
     korunur, böylece kapanış animasyonu kesilmez. */
  useEffect(() => {
    if (acikKimlik !== null) setCekmeceAnahtari(acikKimlik);
  }, [acikKimlik]);
  const parcaYolu =
    bank === null || acikKimlik === null || sekme !== "parcalar"
      ? null
      : `${UC_PARCALAR}?bank=${encodeURIComponent(bank)}&belge=${encodeURIComponent(acikKimlik)}&limit=${PARCA_SAYFA_BOYU}&offset=${parcaAtlanan}`;
  const parcalar = useApi<HafizaZarfi<SayfaliGovde<BelgeParcasi>>>(parcaYolu);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-belgeler" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi neden="Okunacak banka seçilemedi" teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor" />
      </BolumKart>
    );
  }

  return (
    <BolumKart kimlik="hafiza-belgeler" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      {/* SÜZGEÇ ŞERİDİ sonuç boş kalsa bile ÇİZİLİR — yoksa listeyi boşaltan bir
          süzgeç geri alınamazdı. Şeridin kendisi ortak (`parcalar.tsx`): sunucunun
          eşleşme sözlüğü iki dosyada iki kopya olarak duruyordu ve sessizce
          ayrışabilirdi (düzeltme turu 1, inceleme bulgusu I-5). */}
      <SuzgecSeridi
        arama={arama}
        setArama={setArama}
        etiketler={etiketler}
        setEtiketler={setEtiketler}
        esleme={esleme}
        setEsleme={setEsleme}
        aramaEtiketi="Belgelerde ara"
      />

      <UcKapisi durum={belgeler} yol={UC_BELGELER}>
        {(z) => (
          <ZarfKapisi zarf={z} ne="Belgeler">
            {(g) => {
              if (!Array.isArray(g.items)) {
                return <Olculemedi neden="Belge listesi tanınmayan bir biçimde geldi" teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir" />;
              }
              if (g.items.length === 0) {
                return (
                  <p className="text-muted-foreground text-sm">
                    {atlanan === 0
                      ? "Bu süzgeçle okundu ve eşleşen belge YOK. Bu ölçülmüş bir boşluktur."
                      : "Bu sayfada belge YOK — liste daha önceki bir sayfada bitmiş."}
                  </p>
                );
              }
              return (
                <div className="overflow-x-auto">
                  <Table className="min-w-[46rem]">
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead>Belge</TableHead>
                        <TableHead className="w-56">Etiketler</TableHead>
                        <TableHead className="w-36 text-right">Uzunluk</TableHead>
                        <TableHead className="w-28 text-right">Kayıt</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {g.items.map((b, i) => {
                        const kimlik = metin(b.id);
                        const guncelleme = damga(b.updated_at);
                        const n = sayi(b.memory_unit_count);
                        return (
                          <TableRow
                            key={kimlik ?? `belge-${atlanan + i}`}
                            className={cn(kimlik !== null && "cursor-pointer hover:bg-muted/50")}
                            onClick={kimlik === null ? undefined : () => setAcikBelge(b)}
                          >
                            <TableCell className="max-w-0">
                              {kimlik === null ? (
                                <Olculemedi neden="Belgenin kimliği okunamadı" teknik="satırda kimlik alanı yok — kimliksiz belgenin parçaları çağrılamaz" kisa />
                              ) : (
                                <span className="block truncate font-mono text-sm" title={kimlik}>
                                  {kimlik}
                                </span>
                              )}
                              <span className="mt-0.5 block text-muted-foreground text-[11px]">
                                {guncelleme ? (
                                  `güncelleme ${guncelleme}`
                                ) : (
                                  <Olculemedi neden="Güncelleme zamanı gelmedi" teknik="güncelleme damgası gelmedi ya da çözülemedi" kisa />
                                )}
                              </span>
                            </TableCell>
                            <TableCell>
                              <Cipler degerler={listeye(b.tags)} tavan={3} ne="Etiket alanı" />
                            </TableCell>
                            <TableCell className="text-right text-muted-foreground text-xs tabular-nums">
                              {uzunlukMetni(b.text_length) ?? (
                                <Olculemedi neden="Uzunluk gelmedi" teknik="metin uzunluğu alanı gelmedi ya da sayı değil" kisa />
                              )}
                            </TableCell>
                            <TableCell className="text-right font-medium tabular-nums">
                              {n === null ? (
                                <Olculemedi neden="Kayıt sayısı gelmedi" teknik="belgeden çıkan kayıt sayacı gelmedi ya da sayı değil" kisa />
                              ) : (
                                n.toLocaleString("tr-TR")
                              )}
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

      {/* SAYFALAMA KAPININ İÇİNDE (inceleme bulgusu M-4): dışarıda dururken istek
          düştüğünde "Okunamadı" uyarısının altında ölçülmemiş bir sayfa konumu
          çiziliyordu. */}
      <UcKapisi durum={belgeler} yol={UC_BELGELER} iskelet={<></>}>
        {(z) =>
          z.neden || !z.govde ? null : (
            <Sayfalama
              atlanan={atlanan}
              gelen={(z.govde.items ?? []).length}
              sayfaBoyu={SAYFA_BOYU}
              toplam={z.govde.total}
              setAtlanan={setAtlanan}
            />
          )
        }
      </UcKapisi>

      {/* ÜST YÜZEYDE TABLONUN ÜSTÜNDE İKİ YAZMA DÜĞMESİ VAR (içe/dışa aktarım). */}
      <Faz2Grup>
        <Faz2Dugme ne="bankaya yeni belge yükler">İçe aktar</Faz2Dugme>
        <Faz2Dugme ne="bankanın belgelerini dosya olarak indirir">Dışa aktar</Faz2Dugme>
      </Faz2Grup>

      <Sheet
        open={acikBelge !== null}
        onOpenChange={(a) => {
          if (!a) setAcikBelge(null);
        }}
      >
        {/* `key` ÇEKMECE ANAHTARIDIR (Görev 2 incelemesi M-5 + T2 yeniden-incelemesi).
            SORUN: veri katmanı yol değişince eski gövdeyi TEMİZLEMİYOR ve kapı
            yalnız "veri boş mu" diye soruyor; anahtar olmadan A belgesinin
            parçaları B'nin başlığı altında çizilebiliyordu — içerik YANLIŞ
            belgeye atfediliyordu.
            AMA ANAHTAR KAPANIŞTA DEĞİŞMEZ: doğrudan `acikKimlik ?? "bos"` yazmak,
            çekmece kapanırken (aynı render'da `open` false olurken) anahtarı da
            değiştiriyordu ve Radix'in kapanış animasyonu atlanıyordu — kutu
            görünüp yok oluyordu. Anahtar bu yüzden SON AÇIK kimlikte kalır ve
            yalnız yeni bir belge açılırken değişir: veri-atıf düzeltmesi korunur,
            kapanış animasyonu geri gelir. */}
        <SheetContent key={cekmeceAnahtari} side="right" className="w-full sm:max-w-2xl">
          <SheetHeader className="pr-10">
            <SheetTitle className="flex items-center gap-2 text-base leading-6">
              <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden />
              Belge
              {sayi(acikBelge?.memory_unit_count) !== null ? (
                <Badge variant="outline" className="tabular-nums">
                  {(sayi(acikBelge?.memory_unit_count) as number).toLocaleString("tr-TR")} kayıt
                </Badge>
              ) : null}
            </SheetTitle>
            <SheetDescription className="break-all font-mono text-[11px]">
              {acikKimlik ?? "belge seçilmedi"}
            </SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
            {acikBelge === null ? (
              <p className="text-muted-foreground text-sm">Tablodaki bir satıra tıkla.</p>
            ) : (
              <BelgeCekmecesi
                belge={acikBelge}
                parcalar={parcalar}
                parcaAtlanan={parcaAtlanan}
                setParcaAtlanan={setParcaAtlanan}
                sekme={sekme}
                setSekme={setSekme}
              />
            )}
          </div>
        </SheetContent>
      </Sheet>
    </BolumKart>
  );
}
