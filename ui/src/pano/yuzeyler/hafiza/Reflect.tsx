"use client";

/* ============================================================================
   HAFIZA · REFLECT — VE BU DOSYANIN EN ÖNEMLİ CÜMLESİ BİR DÜZELTMEDİR
   ----------------------------------------------------------------------------
   ÖLÇÜLDÜ (2026-09-02, üst yüzeyin sekme tablosu): `reflect` sekmesi bir ÇIKARIM
   LİSTESİ DEĞİLDİR. O sekmede duran şey `think-view.tsx`tir: bankaya bir soru
   sorulan, cevabı bir MODEL ÇAĞRISIYLA üretilen bir oyun alanı (`POST /reflect`).
   Görev 2'nin bu görünüm için yazdığı boş-hâl paneli "çıkarım belgeleri, tarihçe,
   tazelik" diyordu; o liste ölçülmemişti ve YANLIŞTI — çıkarım belgeleri
   (zihin modelleri) üst yüzeyde BİLGİ sekmesinin ikinci sekmesinde yaşıyor ve bu
   turda oraya çizildi (`ZihinModelleri.tsx`).

   VEKİLDE `reflect`İN KARŞILIĞI YOK ve bu bir unutma değil kapsam kararıdır:
   `reflect` bir okuma değil, ücretli bir model çağrısıdır — panodan tetiklenmesi
   Faz-1'in salt-okunur sözleşmesinin dışındadır. Oyun alanı bu yüzden GÖRÜNÜR
   ama ÇALIŞMAZ çizilir: gizlemek "böyle bir yetenek yok" derdi, oysa doğru cümle
   "yetenek var, bu panodan tetiklenmiyor".

   ---------------------------------------------------------------------------
   GÖZLEMLER NEDEN BURADA — VE ÜST YÜZEYDE NEREDE OLDUĞU
   ---------------------------------------------------------------------------
   Üst yüzey gözlem LİSTESİNİ Bellekler sekmesinin üçüncü alt sekmesinde çiziyor
   (`type=observation` süzgeçli aynı tablo) ve bizim Bellekler görünümümüzün tür
   süzgeci o değeri ZATEN sunuyor — yani listeyi orada da okuyabilirsin ve burada
   ikinci bir tam tablo açmak aynı gerçeğin iki kopyası olurdu.

   BURADA OLAN ŞEY LİSTENİN KOPYASI DEĞİL: (1) gözleme ÖZGÜ alanı olan kaynak
   sayısı öne çıkarılmış kısa bir liste, ve (2) GÖZLEM KAPSAMLARI — hangi etiket
   kümesinden kaç gözlem doğduğu. Kapsamların üst yüzeydeki evi gözlem süzgecidir
   ve panoda başka hiçbir ekranda okuru yok. İkisi de reflect'in cevabını KURAN
   malzemedir (üst yüzeyin cevap kartı "neye dayandı" sekmelerinden biri tam
   olarak gözlemlerdir), o yüzden aynı sayfada duruyorlar.

   GÖZLEM TARİHÇESİ ÇİZİLEMİYOR VE ADI YAZILI: üst yüzey bir gözlemin geçmişini
   (`observation-history-view.tsx`) kayıt detay kutusunda, tek-gözlem ucundan
   okuyor. O ucun vekilde karşılığı YOK. "Tarihçe boş" demek yalan olurdu;
   ekran "bu pano onu okumuyor" diyor.
   ============================================================================ */
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";

import type { Bolum } from "../../alanlar";
import { useApi } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";

import { Bolme, Cipler, Sayfalama, ZarfKapisi, damga, listeye, metin, sayi } from "./parcalar";
import type { GozlemKapsami, GozlemKapsamlari, HafizaKaydi, HafizaZarfi, SayfaliGovde } from "./uctipleri";

const UC_GOZLEMLER = "/api/hindsight/gozlemler";
const UC_KAPSAMLAR = "/api/hindsight/gozlem-kapsamlari";

const SAYFA_BOYU = 25;

/** Devre dışı oyun alanının rozeti. `parcalar.tsx::FAZ2_ROZET`ten AYRI, çünkü
 *  söylediği şey farklı: orada yazma yolu bir SIRA kararıyla ertelendi, burada
 *  ucun kendisi vekilde YOK ve nedeni maliyet sınıfı (model çağrısı). İki farklı
 *  gerçeği tek rozete indirmek, ikisini de yanlış anlatırdı. */
const REFLECT_ROZET = "vekilde karşılığı yok — reflect bir model çağrısıdır (Faz-1 dışı)";

/* ---------------------------------------------------------------------------
   DEVRE DIŞI OYUN ALANI — üst yüzeyin sorgu şeridinin birebir düzeni
   Denetimler GERÇEK bileşenlerle çiziliyor (kutu, seçim, işaret kutusu) ama
   hepsi kapalı: bir resim koymak, düzenin gerçekten böyle olduğunu göstermezdi.
   --------------------------------------------------------------------------- */
function KapaliOyunAlani() {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-dashed p-3 opacity-70">
      <div className="flex flex-wrap items-end gap-2">
        <label className="flex min-w-[16rem] flex-1 flex-col gap-1">
          <span className="text-muted-foreground text-xs">Soru</span>
          <Input disabled placeholder="bankaya sorulacak soru" className="h-9" />
        </label>
        <Button type="button" className="h-9" disabled title={`cevabı üretir — ${REFLECT_ROZET}`}>
          Düşün
        </Button>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-muted-foreground text-xs">Bütçe</span>
          <Input disabled value="orta" className="h-8 w-28" readOnly />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted-foreground text-xs">Yanıt bütçesi (jeton)</span>
          <Input disabled value="4096" className="h-8 w-32" readOnly />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted-foreground text-xs">Etiketler</span>
          <Input disabled className="h-8 w-44" />
        </label>
        <label className="flex h-8 items-center gap-1.5 self-end text-sm">
          <Checkbox disabled aria-label="Kayıtları da getir" />
          Kayıtları da getir
        </label>
        <label className="flex h-8 items-center gap-1.5 self-end text-sm">
          <Checkbox disabled aria-label="Araç çağrılarını göster" />
          Araç çağrılarını göster
        </label>
        <label className="flex h-8 items-center gap-1.5 self-end text-sm">
          <Checkbox disabled aria-label="Zihin modellerini dışla" />
          Zihin modellerini dışla
        </label>
      </div>
      <p className="text-muted-foreground text-xs">
        Cevap kartı üst yüzeyde beş "neye dayandı" sekmesi taşıyor: yönergeler · zihin modelleri ·
        gözlemler · dünya · deneyim. Cevap üretilmediği için burada hiçbiri çizilmiyor — bu bir
        ölçüm sonucu değil, ölçümün hiç yapılmamış olması.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" size="sm" disabled title={`geri bildirimi yönerge olarak yazar — ${REFLECT_ROZET}`}>
          Geri bildirim yaz
        </Button>
        <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
          {REFLECT_ROZET}
        </Badge>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   GÖZLEM KAPSAMLARI — boş etiket kümesi bir eksiklik DEĞİL
   --------------------------------------------------------------------------- */
function Kapsamlar({ govde }: { readonly govde: GozlemKapsamlari }) {
  /* İKİ AD DA OKUNUR (`fact_type`/`type` deseninin aynısı): bu ucun gövdesi bu
     makinede ölçülmedi; üst yüzeyin bileşeni `scopes` diyor, vekilin zarf
     tanıyıcısı ise `items`ı da biliyor. Tek ada bağlanmak, ötekinde ekranı
     SESSİZCE boşaltırdı. */
  const ham = Array.isArray(govde.scopes) ? govde.scopes : Array.isArray(govde.items) ? govde.items : null;
  if (ham === null) {
    return (
      <Olculemedi
        neden="Kapsam listesi tanınmayan bir biçimde geldi"
        teknik="ne kapsam dizisi ne de öğe dizisi bulundu — şema sürüklenmiş olabilir"
      />
    );
  }
  if (ham.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Kapsamlar okundu ve tanımlı kapsam YOK. Bu ölçülmüş bir boşluktur.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-1">
      {ham.map((k: GozlemKapsami, i: number) => {
        const etiketler = listeye(k.tags);
        const n = sayi(k.count);
        return (
          <div
            key={`${JSON.stringify(k.tags)}-${i}`}
            className="flex flex-wrap items-center justify-between gap-2 border-b py-1.5 last:border-b-0"
          >
            {etiketler === null ? (
              <Olculemedi
                neden="Kapsamın etiketleri gelmedi"
                teknik="etiket alanı yok ya da liste olarak okunamayan bir tiple geldi"
                kisa
              />
            ) : etiketler.length === 0 ? (
              /* BOŞ ETİKET KÜMESİ = KÜRESEL KAPSAM (üst yüzeyin kendi ayrımı).
                 "boş" diye çizmek, tanımlı ve anlamlı bir kapsamı eksik gösterirdi. */
              <span className="text-sm italic">küresel kapsam (etiketsiz)</span>
            ) : (
              <Cipler degerler={etiketler} tavan={8} ne="Kapsamın etiket alanı" />
            )}
            <span className="shrink-0 text-muted-foreground text-xs tabular-nums">
              {n === null ? (
                <Olculemedi neden="Kapsam sayısı gelmedi" teknik="sayaç gelmedi ya da sayı değil" kisa />
              ) : (
                `${n.toLocaleString("tr-TR")} gözlem`
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function Reflect({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  const [atlanan, setAtlanan] = useState(0);

  useEffect(() => {
    setAtlanan(0);
  }, [bank]);

  const gozlemYolu =
    bank === null
      ? null
      : `${UC_GOZLEMLER}?bank=${encodeURIComponent(bank)}&limit=${SAYFA_BOYU}&offset=${atlanan}`;
  const kapsamYolu = bank === null ? null : `${UC_KAPSAMLAR}?bank=${encodeURIComponent(bank)}`;

  const gozlemler = useApi<HafizaZarfi<SayfaliGovde<HafizaKaydi>>>(gozlemYolu);
  const kapsamlar = useApi<HafizaZarfi<GozlemKapsamlari>>(kapsamYolu);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-reflect" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi
          neden="Okunacak banka seçilemedi"
          teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor"
        />
      </BolumKart>
    );
  }

  return (
    <BolumKart kimlik="hafiza-reflect" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <Bolme
        baslik="Düşünme oyun alanı"
        aciklama="Üst yüzeyde bu sekmede duran şey bir cevap üreticisidir; düzeni birebir, denetimleri kapalı."
      >
        <KapaliOyunAlani />
      </Bolme>

      <Bolme
        baslik="Gözlemler"
        aciklama="Bankanın kendi türettiği kayıtlar. Tam tablo ve süzgeçler Bellekler görünümünde; burada gözleme özgü olan kaynak sayısı öne çıkıyor."
      >
        <UcKapisi durum={gozlemler} yol={UC_GOZLEMLER}>
          {(z) => (
            <ZarfKapisi zarf={z} ne="Gözlemler">
              {(g) => {
                if (!Array.isArray(g.items)) {
                  return (
                    <Olculemedi
                      neden="Gözlem listesi tanınmayan bir biçimde geldi"
                      teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                    />
                  );
                }
                if (g.items.length === 0) {
                  return (
                    <p className="text-muted-foreground text-sm">
                      {atlanan === 0
                        ? "Bu banka okundu ve türetilmiş gözlem YOK. Bu ölçülmüş bir boşluktur."
                        : "Bu sayfada gözlem YOK — liste daha önceki bir sayfada bitmiş."}
                    </p>
                  );
                }
                return (
                  <div className="flex flex-col gap-2">
                    {g.items.map((o, i) => (
                      <div key={metin(o.id) ?? `gozlem-${atlanan + i}`} className="rounded-lg border p-3">
                        <p className="text-sm">
                          {metin(o.text) ?? (
                            <Olculemedi
                              neden="Gözlem metni gelmedi"
                              teknik="metin alanı gelmedi ya da dizge değil"
                            />
                          )}
                        </p>
                        <div className="mt-2">
                          <Satir etiket="Kaynak sayısı">
                            {sayi(o.proof_count) === null ? (
                              <Olculemedi
                                neden="Kaynak sayısı gelmedi"
                                teknik="kanıt sayacı gelmedi ya da sayı değil — gözlemin kaç kayda dayandığı okunamıyor"
                                kisa
                              />
                            ) : (
                              <span className="tabular-nums">
                                {(sayi(o.proof_count) as number).toLocaleString("tr-TR")}
                              </span>
                            )}
                          </Satir>
                          <Satir etiket="Etiketler">
                            <Cipler degerler={listeye(o.tags)} tavan={8} ne="Etiket alanı" />
                          </Satir>
                          <Satir etiket="Anılma">
                            {damga(o.mentioned_at) ?? (
                              <Olculemedi
                                neden="Anılma zamanı gelmedi"
                                teknik="anılma damgası gelmedi ya da çözülemedi"
                                kisa
                              />
                            )}
                          </Satir>
                          <Satir etiket="Birleştirme">
                            {damga(o.consolidated_at) ?? (
                              <Olculemedi
                                neden="Birleştirme zamanı gelmedi"
                                teknik="birleştirme damgası gelmedi ya da çözülemedi — gözlem hiç birleştirilmemiş olabilir"
                                kisa
                              />
                            )}
                          </Satir>
                        </div>
                      </div>
                    ))}
                  </div>
                );
              }}
            </ZarfKapisi>
          )}
        </UcKapisi>

        {/* Sayfalama kapının İÇİNDE (Görev 2 incelemesi, bulgu M-4). */}
        <UcKapisi durum={gozlemler} yol={UC_GOZLEMLER} iskelet={<></>}>
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
      </Bolme>

      <Bolme
        baslik="Gözlem kapsamları"
        aciklama="Hangi etiket kümesinden kaç gözlem doğdu. Bu okumanın panoda başka okuru yok."
      >
        <UcKapisi durum={kapsamlar} yol={UC_KAPSAMLAR}>
          {(z) => (
            <ZarfKapisi zarf={z} ne="Gözlem kapsamları">
              {(g) => <Kapsamlar govde={g} />}
            </ZarfKapisi>
          )}
        </UcKapisi>
      </Bolme>

      <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
        <span className="font-medium">Bu görünümün kapsamı: </span>
        bir gözlemin TARİHÇESİ (hangi tazelemede metni ve etiketleri nasıl değişti) üst yüzeyde
        kayıt detay kutusunda, tek-gözlem okumasıyla çiziliyor; o okumanın vekilde karşılığı YOK.
        Çıkarım belgelerinin (zihin modelleri) kendisi ise Bilgi Tabanı görünümünün ikinci
        sekmesinde — üst yüzeyde de orada duruyorlar.
      </p>
    </BolumKart>
  );
}
