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

   ---------------------------------------------------------------------------
   KARAR ARŞİVİ BURAYA BİRLEŞTİ (operatör kararı 2026-09-02, görsel tur)
   ---------------------------------------------------------------------------
   Panonun ayrı bir "Belgeler" rafı yüzeyi vardı ve orada Meridian'ın karar/hüküm
   dosyalarının künyesi listeleniyordu. O dosyalar hafıza bankasına ZATEN
   işlenmiş durumda, yani iki sayfa aynı belgeleri iki kez gösteriyordu — raf
   yüzeyi kalktı, künye bu tabloya BİRLEŞTİ.

   EŞLEME ANAHTARI DOSYA ADIDIR, VE NEDEN ÖYLE OLDUĞU ÖLÇÜLDÜ: banka belgesinin
   kimliği (`id`) içe aktarımda depo yoludur; arşiv ucu ise yalnız dosya ADINI
   döndürüyor (`ad`). İki tarafın ORTAK olduğu tek parça son yol parçasıdır. Bu
   yüzden karşılaştırma iki tarafın da son parçası üzerinden yapılır.

   ÖLÇÜMÜN SINIRI YAZILI (uydurma yasağı): kimliğin GERÇEK biçimi bu turda
   ölçülemedi — canlı ölçüm yalnız ANAHTAR ADLARINI saydı, değerleri değil. Yani
   eşleşmeme bir arıza olabileceği gibi kimliğin başka bir biçimde tutulması da
   olabilir; ekran bu yüzden "eşleşmedi" der ve NEDENİNİ yazar, "bu belge yok"
   demez.

   "HİNDSIGHT'TA YOK" HÜKMÜ ANCAK LİSTENİN TAMAMI ELDEYKEN KURULUR: tablo
   sayfalı ve bir sayfada eşleşmeyen belge sonraki sayfada duruyor olabilir.
   Hüküm bu yüzden iki kademeli — tüm liste tek sayfada geldiyse "bankada yok",
   gelmediyse "bu sayfada eşleşmedi".
   ============================================================================ */
import { useEffect, useMemo, useState } from "react";
import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { useArsiv, type Arsiv, type ArsivKaydi } from "./kararArsivi";
import { useUcYoklama, type UcYoklamasi } from "./ucyoklama";

const UC_BELGELER = "/api/hindsight/belgeler";
const UC_PARCALAR = "/api/hindsight/belge-parcalari";

/* Sayfa boyu bir GÖRÜNÜM kararıdır (gerekçe `Bellekler.tsx`te birebir aynı);
   sunucu tavanı burada TEKRAR YAZILMAZ, iki kopya sessizce ayrışır. */
const SAYFA_BOYU = 25;
const PARCA_SAYFA_BOYU = 25;

/* ---------------------------------------------------------------------------
   KARAR ARŞİVİ EŞLEMESİ — dosya başlığındaki şerhin mekaniği
   --------------------------------------------------------------------------- */

/** Bir yolun son parçası. Yol ayracı taşımayan dizge kendisidir — "yol değil"
 *  demek için ayrıca bir kural yazmak, olmayan bir ayrımı uydurmak olurdu. */
function dosyaAdi(deger: string | null): string | null {
  if (deger === null) return null;
  const parcalar = deger.split("/").filter((p) => p.length > 0);
  return parcalar.at(-1) ?? null;
}

/** Arşiv kaydının TÜRÜ dosya adının önekinden okunur — uç ayrı bir tür alanı
 *  döndürmüyor ve uydurmak yerine adın kendisinden türetmek ölçülebilir. Desen
 *  dışı ad ATILMAZ: "diğer" diye anılır, çünkü uç bir gün deseni gevşetebilir. */
type ArsivTuru = "karar" | "hukum" | "diger";

function arsivTuru(ad: string | null): ArsivTuru {
  if (ad === null) return "diger";
  if (ad.startsWith("KARAR-")) return "karar";
  if (ad.startsWith("HUKUM-")) return "hukum";
  return "diger";
}

const TUR_ETIKET: Readonly<Record<ArsivTuru, string>> = {
  karar: "Karar",
  hukum: "Hüküm",
  diger: "Arşiv",
};

/** Tablo üstündeki süzgeç. "diğer" = arşivde HİÇ eşleşmeyen banka belgesi. */
const TUR_SUZGECLERI = [
  { deger: "hepsi", etiket: "Hepsi" },
  { deger: "arsiv", etiket: "Karar / Hüküm" },
  { deger: "diger", etiket: "Diğer belgeler" },
] as const;
type TurSuzgeci = (typeof TUR_SUZGECLERI)[number]["deger"];

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
        {/* ÇIPLAK "—" YOK (nihai inceleme Ö-4, 2026-09-03): burada gerekçesiz bir
            tire basılıyordu ve bu, dizin genelinde ölçülen TEK çıplak tireydi —
            üstelik AYNI SATIRDAKİ metin `Olculemedi` ile dürüstçe çiziliyordu.
            Kuralı bu dalın kendi iki dosyası yazıyor (`AnaSayfa::seriKovaEtiketi`
            şerhi: "gerekçesiz bir tire, ölçülmemiş bir boşluğu ölçülmüş gibi
            gösterir"; `Bellekler.tsx` başlığı: "hücre '—' değil GEREKÇE taşır"). */}
        {/* HÜCRE `overflow-hidden` VE `neden` KISA (düzeltme turu 2, Y-9): `Olculemedi kisa`
            varyantı `inline-block … truncate` (yani `white-space: nowrap`) taşıyor ve nowrap'li
            bir inline-block 2,5rem'lik bir hücreye shrink-to-fit ile İNMEZ — uzun gerekçe komşu
            sütuna taşardı. Uzun hâl `teknik`te yaşıyor (fareyle ve erişilebilir adla okunur). */}
        <span className="w-10 shrink-0 overflow-hidden font-mono text-muted-foreground text-xs tabular-nums">
          {sira === null ? (
            <Olculemedi
              neden="sıra gelmedi"
              teknik="parça sıra alanı gelmedi ya da sayı değil — parçanın belgedeki yeri okunamıyor"
              kisa
            />
          ) : (
            `#${sira}`
          )}
        </span>
        {/* UZUNLUK METİNDEN TÜRETİLİR: metin gelmediyse yazacak bir sayı da yok ve
            "0 karakter" yazmak ölçülmemiş bir uzunluk uydurmak olurdu. Boş dizge
            burada gerekçesiz DEĞİL — yanındaki önizleme hücresi aynı yokluğun
            gerekçesini `Olculemedi` ile zaten taşıyor (iki kez yazmak gürültü). */}
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

/* ---------------------------------------------------------------------------
   KARAR ŞERİDİ — düşen üç çıktının evi (bedel yasası, inceleme R26 + I-1)
   ----------------------------------------------------------------------------
   Raf yüzeyi kalkarken ÜÇ ölçüm ekrandan düşmüştü ve üçü de burada geri:
     · arşiv künye özeti  — hangi klasör, kaç belge, kaç karar/hüküm, kaç bayt
     · uç yoklaması       — teşhis belgesi (runbook) cevap veriyor mu (HEAD)
     · EKSİK OKUMA UYARISI — uç `ok:false` dediğinde liste KISMİ olabilir

   ÜÇÜNCÜSÜ BİR SÜS DEĞİL, HÜKÜM KAPISI: `ok:false` iken aşağıdaki "bankada yok"
   hükmü EKSİK bir arşivden kurulurdu ve operatör eksikliği hiçbir yerden
   okuyamazdı. Uyarı ekranda, hüküm de o bayrağa bağlı (aşağıdaki `arsivTam`).

   SAYILAR YALNIZ ÖLÇÜLENİN TOPLAMIDIR: boyutu okunamayan belge sıfır sayılıp
   toplama katılmaz, SAYISI yanına yazılır — eksik bir toplamı tam gibi
   göstermek, ölçülmemişi ölçülmüş ilan etmektir.
   --------------------------------------------------------------------------- */
function KararSeridi({
  arsiv,
  govde,
  runbook,
}: {
  readonly arsiv: Durum<Record<string, unknown>>;
  readonly govde: Arsiv | null;
  readonly runbook: UcYoklamasi;
}) {
  const kayitlar = govde?.belgeler ?? null;
  const kararN = (kayitlar ?? []).filter((k) => arsivTuru(k.ad) === "karar").length;
  const hukumN = (kayitlar ?? []).filter((k) => arsivTuru(k.ad) === "hukum").length;
  const digerN = (kayitlar ?? []).length - kararN - hukumN;
  let toplamBayt = 0;
  let baytsizN = 0;
  for (const k of kayitlar ?? []) {
    if (k.bayt === null) baytsizN += 1;
    else toplamBayt += k.bayt;
  }
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-muted-foreground text-xs">Karar arşivi</span>
        {kayitlar === null ? (
          <Olculemedi
            neden={arsiv.oturumDustu ? "Oturum düştü" : "Depo arşivi okunamadı"}
            teknik={
              arsiv.oturumDustu
                ? "arşiv ucu 401 döndü — çaresi yeniden giriş"
                : (arsiv.hata ??
                  govde?.hata ??
                  (arsiv.yukleniyor
                    ? "okuma sürüyor"
                    : "arşiv gövdesi belge listesini ne dizi ne boş olarak döndürdü"))
            }
          />
        ) : (
          <>
            {/* KLASÖRÜN ADI DA BİR ÖLÇÜMDÜR: hangi dizinin tarandığı yazılmazsa
                sayılar "neyin" sayısı olduğunu söylemez. */}
            {govde?.dizin === null || govde?.dizin === undefined ? (
              <Olculemedi neden="Taranan klasör bildirilmedi" teknik="arşiv gövdesi dizin alanını yazmadı" kisa />
            ) : (
              <Badge variant="outline" className="font-mono font-normal text-[11px]">{govde.dizin}</Badge>
            )}
            <Badge variant="outline" className="font-normal text-[11px] tabular-nums">
              {kayitlar.length.toLocaleString("tr-TR")} belge
            </Badge>
            <Badge variant="outline" className="font-normal text-[11px] tabular-nums">
              {kararN.toLocaleString("tr-TR")} karar
            </Badge>
            <Badge variant="outline" className="font-normal text-[11px] tabular-nums">
              {hukumN.toLocaleString("tr-TR")} hüküm
            </Badge>
            {digerN === 0 ? null : (
              <Badge variant="destructive" className="text-[10px] tabular-nums" title="desen dışı ad — uç süzgeci gevşemiş olabilir">
                {digerN.toLocaleString("tr-TR")} desen dışı
              </Badge>
            )}
            <Badge variant="outline" className="font-normal text-[11px] tabular-nums">
              {toplamBayt.toLocaleString("tr-TR")} bayt
              {baytsizN === 0 ? null : ` (${baytsizN.toLocaleString("tr-TR")} ölçülemedi)`}
            </Badge>
          </>
        )}
        <span className="text-muted-foreground text-xs">· Teşhis belgesi</span>
        <RunbookRozeti runbook={runbook} />
      </div>
      {/* EKSİK OKUMA UYARISI — hüküm kapısının görünür yüzü (I-1). */}
      {govde !== null && govde.belgeler !== null && !govde.ok ? (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-amber-700 text-xs leading-relaxed dark:text-amber-300">
          Arşiv EKSİK okundu: uç listeyi verdi ama işi tamamlayamadığını bildirdi. Aşağıdaki
          eşleşme sayıları ve &quot;bankada yok&quot; hükmü bu yüzden KURULMUYOR.{" "}
          {govde.hata ?? "Gerekçe yazılmamış."}
        </p>
      ) : null}
    </div>
  );
}

function RunbookRozeti({ runbook }: { readonly runbook: UcYoklamasi }) {
  if (runbook.ok === null && runbook.hata === null) {
    return <span className="text-muted-foreground text-xs">yoklanıyor…</span>;
  }
  if (runbook.hata !== null) {
    return <Olculemedi neden="Teşhis belgesi yoklanamadı" teknik={runbook.hata} kisa />;
  }
  return runbook.ok === true ? (
    <Badge variant="outline" className="font-normal text-[11px] tabular-nums">
      HTTP {(runbook.kod ?? 0).toLocaleString("tr-TR")} · cevap veriyor
    </Badge>
  ) : (
    <Badge variant="destructive" className="text-[10px] tabular-nums" title="503 = teşhis belgesi henüz üretilmemiş olabilir">
      HTTP {runbook.kod === null ? "?" : runbook.kod.toLocaleString("tr-TR")}
    </Badge>
  );
}

function KararKunyesi({ kayit }: { readonly kayit: ArsivKaydi }) {
  return (
    <div className="flex flex-col gap-2">
      <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
        Karar arşivi künyesi
      </h4>
      <div>
        <Satir etiket="Tür">
          <Badge variant="outline">{TUR_ETIKET[arsivTuru(kayit.ad)]}</Badge>
        </Satir>
        <Satir etiket="Dosya">
          {kayit.ad === null ? (
            <Olculemedi neden="Dosya adı gelmedi" teknik="arşiv künyesinde ad alanı yok ya da dizge değil" kisa />
          ) : (
            <span className="break-all font-mono text-xs">{kayit.ad}</span>
          )}
        </Satir>
        <Satir etiket="Başlık">
          {kayit.baslik ?? (
            <Olculemedi
              neden={kayit.neden === null ? "Başlık gelmedi" : "Başlık ölçülemedi"}
              teknik={kayit.neden ?? "arşiv künyesinde başlık alanı yok ya da dizge değil"}
              kisa
            />
          )}
        </Satir>
        <Satir etiket="Tarih">
          {kayit.tarih ?? (
            <Olculemedi
              neden={kayit.neden === null ? "Tarih gelmedi" : "Tarih ölçülemedi"}
              teknik={kayit.neden ?? "arşiv künyesinde tarih alanı yok ya da dizge değil"}
              kisa
            />
          )}
        </Satir>
        <Satir etiket="Boyut">
          {kayit.bayt === null ? (
            <Olculemedi
              neden={kayit.neden === null ? "Boyut gelmedi" : "Boyut ölçülemedi"}
              teknik={kayit.neden ?? "arşiv künyesinde bayt alanı yok ya da sayı değil"}
              kisa
            />
          ) : (
            <span className="tabular-nums">{kayit.bayt.toLocaleString("tr-TR")} bayt</span>
          )}
        </Satir>
      </div>
      <p className="text-muted-foreground text-xs">
        Bu satır depo arşivinden geldi ve banka belgesiyle dosya adı üzerinden eşleşti. Kararın TAM
        METNİ bu panoda okunmuyor: arşiv ucu yalnız künye döndürüyor.
      </p>
    </div>
  );
}

function BelgeCekmecesi({
  belge,
  arsivKaydi,
  parcalar,
  parcaAtlanan,
  setParcaAtlanan,
  sekme,
  setSekme,
}: {
  readonly belge: HafizaBelgesi;
  /** Depo arşivinde eşleşen künye; `null` = eşleşmedi (gerekçe çekmecede yazılı). */
  readonly arsivKaydi: ArsivKaydi | null;
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

        {arsivKaydi === null ? null : <KararKunyesi kayit={arsivKaydi} />}

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
  const [turSuzgeci, setTurSuzgeci] = useState<TurSuzgeci>("hepsi");
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

  /* DEPO ARŞİVİ AYRI BİR UÇTAN, AYRI BİR GEREKÇEYLE: banka listesi düşse bile
     arşiv okunur, arşiv düşse bile banka listesi çizilir. İkisini bağlamak tek
     arızayı iki körlüğe çevirirdi (`ozet` ucunun iki bacağıyla aynı desen). */
  const { durum: arsiv, okunan: arsivGovdesi } = useArsiv(bank !== null);
  /* TEŞHİS BELGESİ YOKLAMASI (R26): bir bağın "çalışıyor" diye yazılması bir
     iddiadır; HEAD bunu ölçüme çevirir. Gövde indirilmez (gerekçe `ucyoklama.ts`). */
  const runbook = useUcYoklama("/runbook");
  const arsivKayitlari = arsivGovdesi?.belgeler ?? null;

  /* ARŞİV ARIZASININ GEREKÇESİ TEK YERDE TÜRETİLİR (inceleme I-4): süzgeç dalı
     ile aşağıdaki eşleşme bloğu aynı soruyu iki ayrı yerde sormasın. `null` =
     arşiv okundu; dolu = okunamadı ve NEDENİ budur. */
  const arsivNeden: string | null = arsiv.oturumDustu
    ? "arşiv ucu 401 döndü — çaresi yeniden giriş"
    : arsivKayitlari === null
      ? (arsiv.hata ??
        arsivGovdesi?.hata ??
        (arsiv.yukleniyor
          ? "arşiv okuması henüz dönmedi"
          : "arşiv gövdesi belge listesini ne dizi ne boş olarak döndürdü"))
      : null;

  /* ARŞİV TAM MI (inceleme I-1): uç `ok:false` dediğinde liste KISMİ olabilir ve
     kapsayıcı hükümler ("bankada yok", "hepsi eşleşti") o listeden KURULAMAZ. */
  const arsivTam = arsivNeden === null && arsivGovdesi?.ok === true;

  /* EŞLEME HARİTASI DOSYA ADIYLA KURULUR (dosya başlığındaki ölçüm). Adsız kayıt
     haritaya GİRMEZ — anahtarsız bir satırı boş anahtara koymak, adsız iki kaydı
     birbirine eşitlerdi. */
  const arsivHaritasi = useMemo(() => {
    const m = new Map<string, ArsivKaydi>();
    for (const k of arsivKayitlari ?? []) {
      const ad = dosyaAdi(k.ad);
      if (ad !== null && !m.has(ad)) m.set(ad, k);
    }
    return m;
  }, [arsivKayitlari]);

  const arsivKaydi = (belge: HafizaBelgesi): ArsivKaydi | null => {
    const ad = dosyaAdi(metin(belge.id));
    return ad === null ? null : (arsivHaritasi.get(ad) ?? null);
  };

  /* PARÇALAR YALNIZ SEKME AÇIKKEN OKUNUR (dosya başlığındaki bedel şerhi):
     yol boşken `useApi` hiç istek açmaz. */
  const acikKimlik = acikBelge === null ? null : metin(acikBelge.id);
  const acikArsiv = acikBelge === null ? null : arsivKaydi(acikBelge);

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

      {/* TÜR SÜZGECİ SUNUCUDA DEĞİL, BU SAYFADA ÇALIŞIR — ve bu ekranda YAZILI.
          Uç bir "tür" parametresi tanımıyor; süzgeci sorguya koymak, sunucunun
          sessizce yok sayacağı bir parametre göndermek olurdu. Sayfa-içi süzgeç
          dürüsttür ama sınırlıdır: yalnız AÇIK SAYFADAKİ satırları eler. */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-muted-foreground text-xs">Tür</span>
        <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Belge türü süzgeci">
          {TUR_SUZGECLERI.map((t) => (
            <Button
              key={t.deger}
              type="button"
              variant={t.deger === turSuzgeci ? "secondary" : "ghost"}
              size="xs"
              aria-pressed={t.deger === turSuzgeci}
              onClick={() => setTurSuzgeci(t.deger)}
            >
              {t.etiket}
            </Button>
          ))}
        </div>
        <span className="text-muted-foreground text-[11px]">
          bu süzgeç yalnız açık sayfayı eler — sunucu tür parametresi tanımıyor
        </span>
      </div>

      <KararSeridi arsiv={arsiv} govde={arsivGovdesi} runbook={runbook} />

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
              /* SÜZGEÇ ARŞİVE BAĞLIDIR VE ARIZASINI YUTMAZ (inceleme I-4): arşiv
                 okunamadığında harita BOŞ kalır ve "Karar / Hüküm" süzgeci hiçbir
                 satırı geçiremez — bunu "eşleşme yok" diye yazmak, bir ölçüm
                 ARIZASINI ölçüm SONUCU gibi göstermek olurdu. */
              if (turSuzgeci !== "hepsi" && arsivNeden !== null) {
                return (
                  <Olculemedi
                    neden="Tür süzgeci uygulanamadı: karar arşivi okunamadı"
                    teknik={arsivNeden}
                  />
                );
              }
              const satirlar = g.items.filter((b) => {
                if (turSuzgeci === "hepsi") return true;
                const eslesen = arsivKaydi(b) !== null;
                return turSuzgeci === "arsiv" ? eslesen : !eslesen;
              });
              if (satirlar.length === 0) {
                return (
                  <p className="text-muted-foreground text-sm">
                    Tür süzgeci bu sayfada hiçbir satırı geçirmedi — liste boş DEĞİL, sonraki
                    sayfada eşleşen satır olabilir.
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
                      {satirlar.map((b, i) => {
                        const kimlik = metin(b.id);
                        const guncelleme = damga(b.updated_at);
                        const n = sayi(b.memory_unit_count);
                        const kunye = arsivKaydi(b);
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
                                /* DÜĞME, ÇÜNKÜ KLAVYE (nihai inceleme Ö-6): satır
                                   tıklanabilirdi ama odaklanamıyordu — çekmeceye tek
                                   yol fareydi. `Varliklar.tsx` deseni, aynı gerekçeyle. */
                                <button
                                  type="button"
                                  className="block w-full truncate text-left font-mono text-sm hover:underline"
                                  title={kimlik}
                                  onClick={() => setAcikBelge(b)}
                                >
                                  {kimlik}
                                </button>
                              )}
                              <span className="mt-0.5 flex flex-wrap items-center gap-1.5 text-muted-foreground text-[11px]">
                                {/* TÜR ROZETİ YALNIZ EŞLEŞEN SATIRDA ÇIKAR: eşleşmeyene
                                    "diğer" rozeti basmak, ölçülmemiş bir sınıflandırmayı
                                    ölçülmüş gibi göstermek olurdu. */}
                                {kunye === null ? null : (
                                  <Badge variant="outline" className="font-normal text-[10px]">
                                    {TUR_ETIKET[arsivTuru(kunye.ad)]}
                                  </Badge>
                                )}
                                {guncelleme ? (
                                  `güncelleme ${guncelleme}`
                                ) : (
                                  <Olculemedi neden="Güncelleme zamanı gelmedi" teknik="güncelleme damgası gelmedi ya da çözülemedi" kisa />
                                )}
                                {kunye?.tarih ? <span className="tabular-nums">arşiv {kunye.tarih}</span> : null}
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

      {/* ARŞİVDE OLUP LİSTEDE EŞLEŞMEYENLER — hüküm İKİ KADEMELİ (dosya başlığı).
          Liste sayfalıysa "bankada yok" diyemeyiz: eşleşmeyen belge sonraki
          sayfada duruyor olabilir. Blok bu yüzden önce ne bildiğini söyler. */}
      {/* AYNI HATA ÜÇÜNCÜ KEZ ÇİZİLMESİN (inceleme M-3): bu blok kendi `UcKapisi`sını
          kurmuyor — uç düştüğünde ya da 401'de yukarıdaki iki kapı zaten konuşuyor,
          üçüncü bir kopya uyarıyı gürültüye çevirirdi. Veri yoksa blok susar. */}
      {(() => {
        const z = belgeler.veri;
        if (belgeler.hata !== null || belgeler.oturumDustu) return null;
        if (!z || z.neden || !z.govde || !Array.isArray(z.govde.items)) return null;
        {
          const toplam = sayi(z.govde.total);
          /* HÜKÜM İKİ KAPIDAN GEÇER (inceleme I-1): (1) banka listesinin TAMAMI
             elimizde mi, (2) ARŞİV tam okundu mu. İkincisi düşükken kısmi bir
             arşivden "bankada yok" demek, ölçülmemişi ölçülmüş ilan etmektir. */
          const tamListe = atlanan === 0 && toplam !== null && z.govde.items.length >= toplam;
          const hukumKurulabilir = tamListe && arsivTam;
          const gorulen = new Set(
            z.govde.items.map((b) => dosyaAdi(metin(b.id))).filter((a): a is string => a !== null),
          );
          /* ADI ÖLÇÜLEMEYEN KAYIT AYRI KOVADA (nihai inceleme Ö-7, 2026-09-03).
             Önce adsız kayıtlar "eşleşmedi" sayılıyordu ve aynı satırda İKİ ZIT
             İDDİA çiziliyordu: "adı gelmedi, eşleme anahtarı kurulamadı" ve
             "bankada yok". Anahtarı OLMAYAN bir kayıt hakkında "yok" hükmü
             ÖLÇÜLMEMİŞTİR — bu, Recall'daki M-4 düzeltmesinin ("dizi değilse önce
             0 yazıyordu, altında 'tanınmayan biçim' diyordu") birebir kardeşi.
             Hüküm artık YALNIZ adı ölçülen kayıtlar için kurulur; adsızlar
             sayılır ve ayrı bir cümleyle yazılır (uydurma yasağı: sayılan şey
             "eşleşmeyen" değil "eşleştirilemeyen"dir). */
          const adsiz = (arsivKayitlari ?? []).filter((k) => dosyaAdi(k.ad) === null);
          const eslesmeyen = (arsivKayitlari ?? []).filter((k) => {
            const ad = dosyaAdi(k.ad);
            return ad !== null && !gorulen.has(ad);
          });
          return (
            <div className="flex flex-col gap-2 rounded-lg border p-3">
              <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                Depo arşivinde olup bu listede eşleşmeyenler
              </h4>
              {/* GEREKÇE TEK KAYNAKTAN (`arsivNeden`): süzgeç dalı ile bu blok aynı
                  soruyu iki ayrı biçimde cevaplasaydı sessizce ayrışırlardı. */}
              {arsivNeden !== null ? (
                <Olculemedi neden="Depo arşivi okunamadı" teknik={arsivNeden} />
              ) : eslesmeyen.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  {arsivTam
                    ? "Adı ölçülebilen her arşiv kaydı bu sayfadaki bir banka belgesiyle eşleşti."
                    : "Adı ölçülebilen arşiv kayıtlarının hepsi eşleşti — ama arşiv EKSİK okundu, yani okunamayanlar bu cümlenin dışında."}
                </p>
              ) : (
                <>
                  <p className="text-muted-foreground text-xs">
                    {hukumKurulabilir
                      ? "Banka listesinin tamamı tek sayfada geldi ve arşiv tam okundu, yani aşağıdakiler bankada YOK — henüz işlenmemiş olabilirler."
                      : !arsivTam
                        ? "Arşiv EKSİK okundu: aşağıdakiler hakkında hüküm KURULMUYOR — liste kısmi olabilir."
                        : "Liste sayfalı: aşağıdakiler BU SAYFADA eşleşmedi. Sonraki sayfalarda duruyor olabilirler — kesin hüküm için listenin tamamı gerekir."}
                  </p>
                  <ul className="flex flex-col gap-1">
                    {eslesmeyen.map((k, i) => (
                      <li key={k.ad ?? `eslesmeyen-${i}`} className="flex flex-wrap items-center gap-2 text-xs">
                        <Badge variant="outline" className="font-normal text-[10px]">
                          {TUR_ETIKET[arsivTuru(k.ad)]}
                        </Badge>
                        <span className="break-all font-mono">{k.ad}</span>
                        <span className="text-muted-foreground">
                          {k.baslik ?? "başlık gelmedi"}
                        </span>
                        <Badge variant="outline" className="font-normal text-[10px] text-muted-foreground">
                          {hukumKurulabilir
                            ? "bankada yok"
                            : arsivTam
                              ? "bu sayfada eşleşmedi"
                              : "— (arşiv eksik okundu)"}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                </>
              )}
              {/* ADSIZ KOVA — ROZET YOK, ÇÜNKÜ HÜKÜM YOK (Ö-7). Sayı yazılır:
                  sessizce düşürülen kayıt, olmayan kayıttan ayırt edilemezdi. */}
              {adsiz.length > 0 ? (
                <div className="flex flex-col gap-1 border-t pt-2">
                  <p className="text-muted-foreground text-xs">
                    Adı gelmediği için eşleştirilemeyen {adsiz.length} kayıt — bunlar hakkında "bankada
                    var/yok" hükmü KURULMUYOR: eşleme anahtarı dosya adıdır ve o alan ölçülemedi.
                  </p>
                  <ul className="flex flex-col gap-1">
                    {adsiz.map((k, i) => (
                      <li key={`adsiz-${i}`} className="flex flex-wrap items-center gap-2 text-xs">
                        <Olculemedi
                          neden="Dosya adı gelmedi"
                          teknik={k.neden ?? "arşiv künyesinde ad alanı yok — eşleme anahtarı kurulamadı"}
                          kisa
                        />
                        <span className="text-muted-foreground">{k.baslik ?? "başlık gelmedi"}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              <p className="text-muted-foreground text-[11px]">
                Eşleme anahtarı DOSYA ADIDIR: banka belgesinin kimliği içe aktarımda depo yoludur,
                arşiv ucu yalnız adı döndürür. Kimliğin gerçek biçimi bu turda ölçülmedi — eşleşmeme
                bir işleme boşluğu kadar, kimliğin başka biçimde tutulması da olabilir.
              </p>
            </div>
          );
        }
      })()}

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
                arsivKaydi={acikArsiv}
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
