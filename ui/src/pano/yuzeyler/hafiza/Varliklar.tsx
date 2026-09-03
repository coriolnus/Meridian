"use client";

/* ============================================================================
   HAFIZA · VARLIKLAR — üst yüzeyin `entities` görünümünün karşılığı
   ----------------------------------------------------------------------------
   İKİ KİP OKUNDU, UYDURULMADI: üst yüzey (`entities-view.tsx`) bu görünümü İKİ
   kiple çiziyor — "ilişkiler" (bağ haritası) ve "liste" (tablo) — ve açılışta
   İLİŞKİLER kipinde duruyor. Tablonun dört sütunu da oradan: isim · anılma
   sayısı · ilk görülme · son görülme. Alan adlarının TAMAMI ayrıca A1'de
   ölçüldü (`entities?limit=2` → `canonical_name, mention_count, first_seen,
   last_seen, id, metadata`), yani bu görünümün zemini sağlam.

   GRAF YALNIZ İLİŞKİLER KİPİNDE OKUNUR ve bu bir bedel kararıdır: graf ucu
   bankadaki bütün birlikte-geçişleri tarar; liste kipinde duran bir operatör
   için onu önden çekmek, okunmayan bir yükü her açılışta taşımak olurdu. Üst
   yüzey de aynı ayrımı yapıyor (kip değişince yüklüyor).

   ---------------------------------------------------------------------------
   KÜNYE PANELİ — ESKİ "TIKLANAMAZ" BEYANININ KAPANIŞI (TSK-112)
   ---------------------------------------------------------------------------
   Bu dosya bir zamanlar şunu yazıyordu: bir isme tıklamanın açacağı iki okuma
   (tek-varlık ucu ve o ismin geçtiği kayıtlar) vekilde YOKTU, o yüzden ne düğüm
   ne satır tıklanabilirdi. O beyan artık BAYAT ve silindi — ikisi de açıldı
   (`api.py::api_hindsight_varlik` ve kayıt listesinin varlık süzgeci). Bayat bir
   gerekçe, gerekçesizlikten kötüdür: okuyucuya olmayan bir sınırı öğretir.

   ÜST YÜZEYİN ETKİLEŞİMİ ÖLÇÜLDÜ, TAHMİN EDİLMEDİ (`entities-view.tsx`, sürüm
   çapası ebad4782):
     · Tablo satırı tıklanabilir (satır 344) ve seçili satır vurgulanıyor.
     · Takımyıldız düğümü AYNI işlevi çağırıyor (satır 232-237, 287) — iki okuma
       biçimi, TEK panel. Bizde de öyle.
     · Panel iki okumayı BAĞIMSIZ açıyor (satır 95-124): künye düşse bağlı
       kayıtlar yine çizilir, tersi de doğru. İki ayrı gerekçe, iki ayrı kapı.
     · Bağlı kayıtlar çizelgesi kayıtları `occurred_start`a göre ARTAN sıralıyor
       ve aya göre kovalıyor (`data-view.tsx::TimelineView`); damgası olmayan
       kayıt çizelgeye girmez ama SAYILIR.

   ÜST YÜZEYDEN İKİ SAPMA VAR VE İKİSİ DE BİLİNÇLİ:
     1. KÜNYE PANELİ ORADA ÜÇ ALAN BASIYOR (anılma · ilk görülme · kimlik, satır
        459-484); gövde ise SON GÖRÜLME, `metadata` ve gözlem dizisini de
        taşıyor. Biz ölçülen gövdenin tamamını gösteriyoruz: alanı almak ama
        çizmemek, ölçülmüş bir şeyi ekrandan saklamak olurdu.
     2. ÇİZELGE SATIRI TIKLANMIYOR. Üst yüzeyde bir satır kaydın tamamını bir
        kutuda açıyor; bizde kayıt yüzeyi AYRI bir görünümde (Bellekler) yaşıyor
        ve iç içe ikinci bir çekmece bu turun kapsamında değil. Vekil ucu VAR —
        yani bu bir eksik yetenek değil, bağlanmamış bir yol; satırlar da
        tıklanabilir GÖRÜNMÜYOR (imleç değişmiyor) ve cümle panelde yazılı.

   ---------------------------------------------------------------------------
   ÇEMBER YERLEŞİMİ EMEKLİ (operatör görsel turu, 2026-09-02)
   ---------------------------------------------------------------------------
   Bu görünümün ilk grafı kütüphanesiz bir SVG çemberdi: düğümler ağırlığa göre
   sıralı, yerleşim anlamsız, yakınlaştırma yok. Operatör üst yüzeyle kıyasladı
   ("orijinaldeki bayağı başarılı, bizimkinin alakası yok") ve karar verildi:
   varlık grafı da bellek grafıyla AYNI takımyıldız görseline geçer. Kazanç:
   yakınlaştırma/kaydırma, komşu vurgusu, üst yüzeyin kendi ısı ve boyut
   kuralları. Bedel ve ödendiği yer: seçili düğümün bağ LİSTESİ kayboldu —
   yerine üzerine gelince açılan künye geldi; bağların tek tek okunması gereken
   bir soru için liste kipi hâlâ duruyor.
   ============================================================================ */
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { useApi } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";
import { KimliksizRozeti, Takimyildizi, TaninmayanBicim, varlikGrafiniCoz } from "./takimyildizi";

import {
  Bolme,
  HamSatirlar,
  KayitOzeti,
  KirpmaZinciri,
  Sayfalama,
  Secim,
  ZarfKapisi,
  damga,
  damgaMs,
  goreliDamga,
  metin,
  sayi,
} from "./parcalar";
import type {
  HafizaKaydi,
  HafizaListesi,
  HafizaZarfi,
  SayfaliGovde,
  TakimyildiziDugumu,
  VarlikGrafi,
  VarlikKaydi,
  VarlikKunyesi,
} from "./uctipleri";

const UC_VARLIKLAR = "/api/hindsight/varliklar";
const UC_GRAF = "/api/hindsight/varlik-graf";
const UC_VARLIK = "/api/hindsight/varlik";
const UC_LISTE = "/api/hindsight/liste";

/* Sayfa boyu bir GÖRÜNÜM kararıdır; sunucu tavanı (`HAFIZA_LISTE_TAVANI`) burada
   TEKRAR YAZILMAZ — iki kopya sessizce ayrışır. Üst yüzeyin kendi sayfası 50. */
const SAYFA_BOYU = 50;

/* GRAF TAVANI: üst yüzey `limit: 2000, min_count: 1` ile çağırıyor. Bizim
   vekilimiz limiti KENDİ tavanına (200) kırpıyor (`api.py::_hafiza_sayi` +
   `HAFIZA_LISTE_TAVANI`), yani 2000 yazmak sessizce 200 olurdu ve ekran
   istediğinden başka bir şey aldığını bilmezdi. 200 YAZILI ve sunucununkiyle
   AYNI sayı olduğu için ayrışma da görünür olur (istek düşerse gerekçeye döner). */
const GRAF_TAVANI = 200;

/* BAĞLI KAYIT TAVANI — AYNI GEREKÇE, İKİNCİ KEZ. Üst yüzey bu okumayı
   `limit: 500` ile yapıyor (`entities-view.tsx` satır 112-116); vekil onu yine
   200'e kırpardı ve ekran 500 istediğini sanırken 200 alırdı. Sunucunun tavanı
   yazılı, kırpma zinciri de üç sayıyla panelde duruyor: bir isme bağlı kayıt
   sayısı bu tavanı aşarsa fark GÖRÜNÜR. */
const BAGLI_KAYIT_TAVANI = 200;

/** En az kaç kez birlikte geçmiş bağlar çizilsin. Sunucu 1 ile 2^31 arasına
 *  kırpıyor; buradaki liste bir SEÇENEK kümesidir, sunucu sözlüğü değil —
 *  o yüzden "geçersiz değer" hâli yok, yalnız daha dar/geniş bir graf var. */
const ESIK_SECENEKLERI = [
  { deger: "1", etiket: "en az 1 kez" },
  { deger: "2", etiket: "en az 2 kez" },
  { deger: "3", etiket: "en az 3 kez" },
  { deger: "5", etiket: "en az 5 kez" },
  { deger: "10", etiket: "en az 10 kez" },
] as const;

type Kip = "iliskiler" | "liste";

/* ---------------------------------------------------------------------------
   ZAMAN ÇİZELGESİNİN KOVALARI — üst yüzeyin dört yakınlık düzeyi
   ----------------------------------------------------------------------------
   Üst yüzeyin çizelgesi kayıtları yıl/ay/hafta/gün kovalarına atıyor ve AY ile
   açılıyor (`data-view.tsx::TimelineView`). Dördü de burada var; taşınMAYAN şey
   kova kova gezinme düğmeleri — bu çizelge bir çekmecenin içinde yaşıyor ve
   kaydırma zaten çekmecenin kendisinde. Kaybı yazıyoruz: uzun bir çizelgede
   "ilk kovaya git" tek tıkla değil, kaydırarak yapılıyor.
   --------------------------------------------------------------------------- */
type Ayrinti = "yil" | "ay" | "hafta" | "gun";

/* `satisfies` ÇİFTİ DENETLENİR KILAR (inceleme M-2): sözlük ile tip bir gün
   ayrışırsa derleyici burada konuşur — önceki yazımda seçim `as Ayrinti` ile
   zorlanıyordu ve ayrışma sessiz kalırdı. */
const AYRINTI_SECENEKLERI = [
  { deger: "yil", etiket: "yıla göre" },
  { deger: "ay", etiket: "aya göre" },
  { deger: "hafta", etiket: "haftaya göre" },
  { deger: "gun", etiket: "güne göre" },
] as const satisfies readonly { readonly deger: Ayrinti; readonly etiket: string }[];

/** Kovanın BAŞLANGICI. Hafta üst yüzeyin kuralıyla pazar günü başlar. */
function kovaBasi(t: number, ayrinti: Ayrinti): Date {
  const d = new Date(t);
  if (ayrinti === "yil") return new Date(d.getFullYear(), 0, 1);
  if (ayrinti === "ay") return new Date(d.getFullYear(), d.getMonth(), 1);
  if (ayrinti === "hafta") return new Date(d.getFullYear(), d.getMonth(), d.getDate() - d.getDay());
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function kovaEtiketi(bas: Date, ayrinti: Ayrinti): string {
  if (ayrinti === "yil") return String(bas.getFullYear());
  if (ayrinti === "ay") return bas.toLocaleDateString("tr-TR", { year: "numeric", month: "long" });
  if (ayrinti === "hafta") {
    const son = new Date(bas.getFullYear(), bas.getMonth(), bas.getDate() + 6);
    const kisa = (x: Date) => x.toLocaleDateString("tr-TR", { day: "numeric", month: "short" });
    return `${kisa(bas)} – ${kisa(son)} ${son.getFullYear()}`;
  }
  return bas.toLocaleDateString("tr-TR", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

/* ---------------------------------------------------------------------------
   BAĞ HARİTASI — takımyıldız, üst yüzeyin varlık görünümünün KENDİ ayarlarıyla
   ----------------------------------------------------------------------------
   Üç kural üst yüzeyin `entities-view` dosyasından ölçüldü ve birebir taşındı:
     · NOKTA BOYUTU birlikte geçiş ağırlıklarının toplamından, karekök ölçekli
       (3 piksel yalnız kalan isim → 14 piksel merkez isim). Karekök uzun kuyruğu
       düzleştirir: tek bir merkez ötekileri görünmez kılmaz.
     · RENK TAZELİK: düğümün EN SON birlikte geçişi. Boyut "ne kadar", renk "ne
       zaman" der — iki eksen birbirine karışmaz.
     · ETİKETLER SIK: varlık adları kısadır; kayıt metinlerine göre ayarlanmış
       seyrek yerleşim burada etiketlerin çoğunu gizlerdi.
   Tazelik damgası HİÇ gelmezse ısı ekseni ÇİZİLMEZ (üst yüzey de öyle yapıyor):
   bir ölçek çizip uçlarını yazamamak, rengi ölçüm gibi gösterirdi.
   --------------------------------------------------------------------------- */
function BagHaritasi({
  govde,
  dugumSecildi,
}: {
  readonly govde: VarlikGrafi;
  readonly dugumSecildi: (dugum: TakimyildiziDugumu) => void;
}) {
  const cozum = useMemo(() => varlikGrafiniCoz(govde, damgaMs), [govde]);

  const enAgir = useMemo(() => {
    let m = 1;
    for (const w of cozum.agirliklar.values()) if (w > m) m = w;
    return m;
  }, [cozum]);

  /* ISI ARALIĞI ÇÖZÜCÜDEN GELİR, DÜĞÜMLERDEN TÜRETİLMEZ (inceleme M-3).
     İlk yazım aralığı düğüm başına EN SON damgaların en küçüğü/en büyüğü olarak
     kuruyordu; üst yüzey ise BÜTÜN kenar damgalarından kuruyor. Fark sessiz ama
     gerçek: bizim alt ucumuz her zaman üst yüzeyinkine eşit ya da ondan YENİ
     çıkardı, yani efsanenin sol ucundaki tarih ve renk dağılımı ayrışırdı. */
  const tazelikAraligi = cozum.tazelikAraligi;

  const boyutFn = useCallback(
    (d: TakimyildiziDugumu) => 3 + Math.sqrt((cozum.agirliklar.get(d.kimlik) ?? 0) / enAgir) * 11,
    [cozum, enAgir],
  );
  const isiFn = useCallback(
    (d: TakimyildiziDugumu) => {
      if (tazelikAraligi === null) return 0.5;
      const t = cozum.tazelikler.get(d.kimlik);
      if (t === undefined) return 0;
      return (t - tazelikAraligi.alt) / (tazelikAraligi.ust - tazelikAraligi.alt);
    },
    [cozum, tazelikAraligi],
  );

  const gun = (ms: number) => new Date(ms).toLocaleDateString("tr-TR");

  if (!Array.isArray(govde.nodes)) return <TaninmayanBicim />;

  return (
    <div className="flex flex-col gap-3">
      {/* KIRPMA ZİNCİRİ — ÜÇ SAYI, ÜÇÜ DE ADIYLA. Bu uç SUNUCUDA kırpılıyor ve
          yalnız dönen diziyi sayan bir ekran eksik bir grafiği TAM gösterirdi. */}
      <div className="flex flex-col gap-1">
        <KirpmaZinciri
          ne="isim"
          cizilen={cozum.veri.dugumler.length}
          vekil={cozum.vekilDugum}
          tavan={cozum.tavan}
          toplam={cozum.toplamDugum}
        />
        <KirpmaZinciri
          ne="bağ"
          cizilen={cozum.veri.baglar.length}
          vekil={cozum.vekilBag}
          tavan={cozum.tavan}
          toplam={cozum.toplamBag}
        />
      </div>

      <KimliksizRozeti sayi={cozum.kimliksiz} />

      <Takimyildizi
        veri={cozum.veri}
        yukseklik={560}
        dugumTiklandi={dugumSecildi}
        boyutFn={boyutFn}
        isiFn={tazelikAraligi === null ? undefined : isiFn}
        isiEtiketi={tazelikAraligi === null ? undefined : "tazelik · son birlikte geçiş"}
        isiUclari={tazelikAraligi === null ? undefined : [gun(tazelikAraligi.alt), gun(tazelikAraligi.ust)]}
        boyutEtiketi="birlikte geçiş"
        sikEtiket
        aciklama={`Varlık bağ haritası: ${cozum.veri.dugumler.length} isim, ${cozum.veri.baglar.length} bağ`}
      />

      {tazelikAraligi === null ? (
        <p className="text-muted-foreground text-[11px]">
          Isı ekseni çizilmedi: bağların son birlikte geçiş zamanı bu okumada gelmedi ya da hepsi
          aynı ana düşüyor. Renk bu durumda bağ sayısını gösterir.
        </p>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   KÜNYE — üst yüzeyin panel başlığının karşılığı, ÖLÇÜLEN GÖVDENİN TAMAMIYLA
   --------------------------------------------------------------------------- */

function DamgaSatiri({
  etiket,
  deger,
  simdi,
  neden,
}: {
  readonly etiket: string;
  readonly deger: unknown;
  readonly simdi: number;
  readonly neden: string;
}) {
  const mutlak = damga(deger);
  const gorece = goreliDamga(deger, simdi);
  return (
    <Satir etiket={etiket}>
      {mutlak === null ? (
        <Olculemedi neden={neden} teknik="damga alanı gelmedi ya da çözülemedi" kisa />
      ) : (
        <span className="tabular-nums">
          {mutlak}
          {gorece === null ? null : <span className="ml-2 text-muted-foreground text-xs">{gorece}</span>}
        </span>
      )}
    </Satir>
  );
}

function Kunye({ govde, simdi }: { readonly govde: VarlikKunyesi; readonly simdi: number }) {
  const ad = metin(govde.canonical_name);
  const anilma = sayi(govde.mention_count);
  const kimlik = metin(govde.id);
  return (
    <div className="flex flex-col gap-3">
      {ad === null ? (
        <Olculemedi
          neden="Bu ismin kendisi gelmedi"
          teknik="kanonik ad alanı yanıtta yok ya da dizge değil"
        />
      ) : (
        <h3 className="font-semibold text-base leading-6">{ad}</h3>
      )}

      <div>
        <Satir etiket="Anılma">
          {anilma === null ? (
            <Olculemedi
              neden="Anılma sayısı gelmedi"
              teknik="anılma sayacı gelmedi ya da sayı değil"
              kisa
            />
          ) : (
            <span className="tabular-nums">{anilma.toLocaleString("tr-TR")}</span>
          )}
        </Satir>
        <DamgaSatiri etiket="İlk görülme" deger={govde.first_seen} simdi={simdi} neden="İlk görülme gelmedi" />
        <DamgaSatiri etiket="Son görülme" deger={govde.last_seen} simdi={simdi} neden="Son görülme gelmedi" />
        <Satir etiket="Kimlik">
          {kimlik === null ? (
            <Olculemedi neden="Kimlik gelmedi" teknik="kimlik alanı yanıtta yok ya da dizge değil" kisa />
          ) : (
            <span className="break-all font-mono text-[11px]">{kimlik}</span>
          )}
        </Satir>
      </div>

      {/* KALAN ALANLAR HAM AMA ETİKETLİ: üst yüzeyin panelinde çizilmeyen
          `metadata` ve gözlem dizisi burada kaybolmuyor. Alan adları
          ÇEVRİLMİYOR — çeviri tablosu uydurulmuş bir sözlüğü ekranın birincil
          metni yapardı (`parcalar.tsx::HamSatirlar` şerhi). */}
      <div className="flex flex-col gap-2">
        <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
          Künyenin kalanı
        </h4>
        <HamSatirlar
          govde={govde}
          atla={["canonical_name", "mention_count", "first_seen", "last_seen", "id"]}
        />
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   BAĞLI KAYITLAR — zaman çizelgesi
   --------------------------------------------------------------------------- */

function ZamanCizelgesi({
  liste,
  ayrinti,
}: {
  readonly liste: HafizaListesi;
  readonly ayrinti: Ayrinti;
}) {
  const ogeler = liste.ogeler;

  /* SIRALAMA VE KOVALAMA ÜST YÜZEYİN KURALI: artan `occurred_start`, damgasız
     kayıtlar çizelgeye GİRMEZ ama SAYILIR. Damga çözümü tek kapıdan geçer
     (`parcalar.tsx::damgaMs`) — korumasız bir çözüm, sayı benzeri bir dizgeyi
     tarihe çevirip uydurma bir kova üretirdi. */
  const { kovalar, cizilen, damgasiz } = useMemo(() => {
    const damgali: { readonly t: number; readonly kayit: HafizaKaydi }[] = [];
    let damgasizSayisi = 0;
    for (const o of ogeler ?? []) {
      const t = damgaMs(o.occurred_start);
      if (t === null) damgasizSayisi += 1;
      else damgali.push({ t, kayit: o });
    }
    damgali.sort((a, b) => a.t - b.t);

    const harita = new Map<number, { readonly bas: Date; ogeler: HafizaKaydi[] }>();
    for (const { t, kayit } of damgali) {
      const bas = kovaBasi(t, ayrinti);
      const anahtar = bas.getTime();
      const mevcut = harita.get(anahtar);
      if (mevcut) mevcut.ogeler.push(kayit);
      else harita.set(anahtar, { bas, ogeler: [kayit] });
    }
    return {
      kovalar: [...harita.entries()].sort((a, b) => a[0] - b[0]).map(([anahtar, k]) => ({ anahtar, ...k })),
      cizilen: damgali.length,
      damgasiz: damgasizSayisi,
    };
  }, [ogeler, ayrinti]);

  const kisaGun = (deger: unknown) => {
    const t = damgaMs(deger);
    return t === null ? null : new Date(t).toLocaleDateString("tr-TR", { day: "numeric", month: "short" });
  };
  const kisaSaat = (deger: unknown) => {
    const t = damgaMs(deger);
    return t === null
      ? null
      : new Date(t).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", hour12: false });
  };

  return (
    <div className="flex flex-col gap-2">
      {/* ÜÇ SAYI, ÜÇÜ DE ADIYLA — bu isme bağlı toplam, vekilin döndürdüğü dilim,
          çizelgeye giren kadarı. Aradaki farkın adı hemen altında yazılı.

          ÜÇÜNCÜ SAYININ ADI BURADA DEĞİŞİYOR (inceleme I-1): bileşenin varsayılan
          metni "bankada toplam" ve üç eski çağıranı için doğru — ama bu zincir
          `entity_id` ile SÜZÜLMÜŞ bir yanıtın toplamını basıyor. Varsayılanla
          bırakmak, doğru sayıyı yanlış adla göstermek olurdu: operatör bankada
          o kadar kayıt olduğunu sanırdı. */}
      <KirpmaZinciri
        ne="kayıt"
        cizilen={cizilen}
        vekil={(ogeler ?? []).length}
        tavan={BAGLI_KAYIT_TAVANI}
        toplam={liste.toplam ?? null}
        toplamEtiketi="bu isme bağlı toplam"
      />
      {damgasiz > 0 ? (
        <p className="text-muted-foreground text-[11px]">
          {damgasiz.toLocaleString("tr-TR")} kayıt çizelgeye girmedi: gerçekleşme zamanı bu kayıtlarda
          yok. Sayı yukarıdaki çizilen sayısının dışında — kayıtlar duruyor, zamanları ölçülmemiş.
        </p>
      ) : null}

      {kovalar.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Bu isme bağlı kayıtların hiçbirinde gerçekleşme zamanı yok — çizelge çizilemiyor. Bu bir
          okuma arızası değil, ölçülmüş bir boşluk.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {kovalar.map((k) => (
            <div key={k.anahtar} className="flex flex-col gap-1.5">
              <div className="flex items-baseline gap-2 border-b pb-1">
                <span className="font-semibold text-primary text-xs">{kovaEtiketi(k.bas, ayrinti)}</span>
                <span className="text-[10px] text-muted-foreground tabular-nums">
                  {k.ogeler.length.toLocaleString("tr-TR")} kayıt
                </span>
              </div>
              {k.ogeler.map((o, i) => (
                <div key={metin(o.id) ?? `kayit-${k.anahtar}-${i}`} className="flex items-start gap-2">
                  <div className="w-14 shrink-0 pt-1 text-right">
                    <div className="text-[10px] text-muted-foreground tabular-nums">
                      {kisaGun(o.occurred_start) ?? ""}
                    </div>
                    {/* SAAT SATIRI DA 10 PİKSEL: üst yüzey burada 9 kullanıyor ama bu
                        panoda 9 piksellik bir basamak YOK — tipografi merdiveninin
                        dışına tek bir satır için çıkmak, merdiveni bozmanın en sessiz
                        yoludur. Ayrım rengin soluklaşmasıyla korunuyor. */}
                    <div className="text-[10px] text-muted-foreground/70 tabular-nums">
                      {kisaSaat(o.occurred_start) ?? ""}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1 rounded border p-2">
                    <KayitOzeti kayit={o} varliklar />
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BagliKayitlar({ liste, ayrinti }: { readonly liste: HafizaListesi; readonly ayrinti: Ayrinti }) {
  if (liste.neden) return <Olculemedi neden="Bağlı kayıtlar okunamadı" teknik={liste.neden} />;
  if (liste.ogeler === undefined) {
    return (
      <Olculemedi neden="Bağlı kayıt listesi bildirilmedi" teknik="uç kayıt dizisini döndürmedi" />
    );
  }
  if (liste.ogeler.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Bu isme bağlı kayıt YOK. Ad kayıtlarda geçiyor olabilir ama üst servis bu isme bağlı bir
        kayıt döndürmedi — ölçülmüş bir boşluk.
      </p>
    );
  }
  return <ZamanCizelgesi liste={liste} ayrinti={ayrinti} />;
}

/* ---------------------------------------------------------------------------
   ÇEKMECE — İKİ BAĞIMSIZ OKUMA, TEK PANEL
   ----------------------------------------------------------------------------
   İSTEK YALNIZ PANEL AÇIKKEN AÇILIR (Yasa 6): yol boşken veri katmanı hiç istek
   kurmaz, kapanışta ise yol düşer ve uçuştaki istek İPTAL edilir (`veri.ts`nin
   kendi temizliği). Hızlı iki tıklamada da son seçilen kazanır: önceki istek
   yol değişiminde iptal edilir.

   BİLEŞEN ANAHTARLA YENİDEN KURULUR (Belgeler'in ölçülmüş dersi, M-5): veri
   katmanı yol değişince ESKİ gövdeyi temizlemiyor ve kapı yalnız "veri boş mu"
   diye soruyor — anahtar olmasa A isminin künyesi B'nin başlığı altında
   çizilebilirdi. Anahtar KAPANIŞTA değişmez, yoksa çekmecenin kapanış
   animasyonu kesilir.
   --------------------------------------------------------------------------- */
function VarlikCekmecesi({
  bank,
  kimlik,
  acik,
}: {
  readonly bank: string;
  readonly kimlik: string;
  readonly acik: boolean;
}) {
  const [ayrinti, setAyrinti] = useState<Ayrinti>("ay");

  const kunyeYolu = acik
    ? `${UC_VARLIK}?bank=${encodeURIComponent(bank)}&id=${encodeURIComponent(kimlik)}`
    : null;
  /* KAYIT SÜZGECİ ÜST SERVİSİN KENDİ PARAMETRESİ (`entity_id`) — istemcide
     süzmek, tavanın ilk 200 kaydını çekip içinden bu isme bağlı olanları
     ayıklamak olurdu: ekran "bu isme bağlı kayıt yok" derken sebep yalnızca
     sayfanın bitmiş olması olabilirdi. */
  const kayitYolu = acik
    ? `${UC_LISTE}?bank=${encodeURIComponent(bank)}&entity_id=${encodeURIComponent(kimlik)}&limit=${BAGLI_KAYIT_TAVANI}`
    : null;

  /* İKİ BACAK BİRBİRİNİ DÜŞÜRMEZ (üst yüzeyin kendi ayrımı): künye okunamazsa
     bağlı kayıtlar yine çizilir, tersi de doğru. Tek bir gerekçeye indirmek bir
     arızayı iki körlüğe çevirirdi. */
  const kunye = useApi<HafizaZarfi<VarlikKunyesi>>(kunyeYolu);
  const kayitlar = useApi<HafizaListesi>(kayitYolu);

  /* "ŞİMDİ" OKUMANIN ANINA ÇİVİLENİR: her çizimde yeniden okunsaydı aynı yanıtın
     iki satırı iki ayrı şimdiye göre yazılabilirdi (`parcalar.tsx::goreliDamga`). */
  const simdi = useMemo(() => Date.now(), [kunye.zaman]);

  /* BAŞLIK KÜNYE ÇÖZÜLÜNCE ADI TAŞIR (inceleme M-4): üst yüzeyin paneli de adı
     başlığa yazıyor, bizde ise çekmecenin erişilebilir adı ham bir kimlikti.
     Ad ÇÖZÜLMEDEN ÖNCE genel sözcükte kalır — uydurma bir başlık yazılmaz — ve
     dört hâli ayıran kapı gövdede AYNEN duruyor: bu okuma yalnız başlık için,
     gövdenin ölçüm zincirinin yerine geçmiyor. */
  const ad = metin(kunye.veri?.govde?.canonical_name);

  return (
    <>
      <SheetHeader className="pr-10">
        <SheetTitle className="text-base leading-6">{ad ?? "Varlık künyesi"}</SheetTitle>
        <SheetDescription className="break-all font-mono text-[11px]">{kimlik}</SheetDescription>
      </SheetHeader>
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
        <Bolme baslik="Künye" aciklama="Bu ismin kendisi hakkında üst servisin döndürdüğü her şey.">
          <UcKapisi durum={kunye} yol={UC_VARLIK}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Varlık künyesi">
                {(v) => <Kunye govde={v} simdi={simdi} />}
              </ZarfKapisi>
            )}
          </UcKapisi>
        </Bolme>

        <Bolme
          baslik="Bağlı kayıtlar"
          aciklama="Bu ismin geçtiği kayıtlar, gerçekleşme zamanına göre eskiden yeniye. Satırlar tıklanabilir değil: kaydın tamamı Bellekler görünümünde açılıyor ve iç içe ikinci bir panel bu turda bağlanmadı."
          aksiyon={
            <Secim
              etiket="Çizelge yakınlığı"
              deger={ayrinti}
              setDeger={(d) => {
                const s = AYRINTI_SECENEKLERI.find((x) => x.deger === d);
                if (s) setAyrinti(s.deger);
              }}
              secenekler={AYRINTI_SECENEKLERI}
              genislik="w-36"
            />
          }
        >
          <UcKapisi durum={kayitlar} yol={UC_LISTE}>
            {(l) => <BagliKayitlar liste={l} ayrinti={ayrinti} />}
          </UcKapisi>
        </Bolme>
      </div>
    </>
  );
}

export function Varliklar({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  /* AÇILIŞ KİPİ ÜST YÜZEYDEN: orada da varsayılan "ilişkiler". Liste ile açsaydık
     birebirleştirmenin ölçülebilir yarısını kaybederdik. */
  const [kip, setKip] = useState<Kip>("iliskiler");
  const [atlanan, setAtlanan] = useState(0);
  const [esik, setEsik] = useState("1");
  const [secili, setSecili] = useState<string | null>(null);
  /* ÇEKMECE ANAHTARI: yalnız AÇIKKEN ilerler (çekmece şerhi). */
  const [cekmeceAnahtari, setCekmeceAnahtari] = useState("bos");
  /* ANAHTAR RENDER SIRASINDA İLERLER, ETKİDE DEĞİL (inceleme M-1): etki boyamadan
     SONRA koştuğu için A'nın çekmecesi açıkken B'ye tıklandığında bir kare boyunca
     B ile vurgulanmış satırın altında A'nın gövdesi boyanabiliyordu. Render
     sırasında durum güncellemek React'in belgelediği yoldur: bileşen boyamadan
     önce yeniden çalışır, yani bayat kare hiç çizilmez. */
  if (secili !== null && secili !== cekmeceAnahtari) setCekmeceAnahtari(secili);

  /* TEK SEÇİM KAPISI: düğüm de satır da BURADAN geçer. İki ayrı kurucu yazmak,
     iki okuma biçiminin zamanla iki ayrı panele ayrılmasının başlangıcı olurdu. */
  const varligiSec = useCallback((k: string) => setSecili(k), []);
  const grafDugumu = useCallback((d: TakimyildiziDugumu) => varligiSec(d.kimlik), [varligiSec]);

  useEffect(() => {
    setAtlanan(0);
    setSecili(null);
  }, [bank]);

  const listeYolu =
    bank === null || kip !== "liste"
      ? null
      : `${UC_VARLIKLAR}?bank=${encodeURIComponent(bank)}&limit=${SAYFA_BOYU}&offset=${atlanan}`;
  const grafYolu =
    bank === null || kip !== "iliskiler"
      ? null
      : `${UC_GRAF}?bank=${encodeURIComponent(bank)}&limit=${GRAF_TAVANI}&min_count=${encodeURIComponent(esik)}`;

  const liste = useApi<HafizaZarfi<SayfaliGovde<VarlikKaydi>>>(listeYolu);
  const graf = useApi<HafizaZarfi<VarlikGrafi>>(grafYolu);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-varliklar" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi
          neden="Okunacak banka seçilemedi"
          teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor"
        />
      </BolumKart>
    );
  }

  return (
    <BolumKart
      kimlik="hafiza-varliklar"
      baslik={kayit.baslik}
      soru={kayit.soru}
      ikon={kayit.ikon}
      aksiyon={
        <div className="flex items-center gap-1 rounded-lg bg-muted p-1">
          <Button
            type="button"
            size="sm"
            variant={kip === "iliskiler" ? "secondary" : "ghost"}
            className="h-7 px-2 text-xs"
            aria-pressed={kip === "iliskiler"}
            onClick={() => setKip("iliskiler")}
          >
            İlişkiler
          </Button>
          <Button
            type="button"
            size="sm"
            variant={kip === "liste" ? "secondary" : "ghost"}
            className="h-7 px-2 text-xs"
            aria-pressed={kip === "liste"}
            onClick={() => setKip("liste")}
          >
            Liste
          </Button>
        </div>
      }
    >
      {kip === "iliskiler" ? (
        <Bolme
          baslik="Bağ haritası"
          aciklama="Hangi isim hangisiyle birlikte geçiyor. Nokta büyüklüğü birlikte geçiş ağırlığını, rengi son geçişin tazeliğini gösterir; sınırlar haritanın üstünde sayıyla yazılı. Bir düğüme tıklamak o ismin künyesini yandaki panelde açar."
          aksiyon={<Secim etiket="Bağ eşiği" deger={esik} setDeger={setEsik} secenekler={ESIK_SECENEKLERI} genislik="w-36" />}
        >
          <UcKapisi durum={graf} yol={UC_GRAF}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Bağ haritası">
                {(g) => <BagHaritasi govde={g} dugumSecildi={grafDugumu} />}
              </ZarfKapisi>
            )}
          </UcKapisi>
          {/* KLAVYE YOLU DÜRÜSTÇE YAZILI: harita bir tuval ve tuvalin içindeki
              düğümler klavyeyle gezilemiyor. Aynı isimler liste kipinde düğme
              olarak duruyor — kapsam sınırı değil, ikinci bir yol. */}
          <p className="text-muted-foreground text-[11px]">
            Haritadaki düğümler klavyeyle gezilemiyor; aynı isimler liste kipinde klavyeyle
            seçilebilen satırlar hâlinde duruyor.
          </p>
        </Bolme>
      ) : (
        <Bolme
          baslik="İsim listesi"
          aciklama="Kayıtlarda geçen isimler: kaç kez anıldı, ilk ve son ne zaman görüldü. Bir satıra tıklamak o ismin künyesini açar."
        >
          <UcKapisi durum={liste} yol={UC_VARLIKLAR}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Varlık listesi">
                {(g) => {
                  if (!Array.isArray(g.items)) {
                    return (
                      <Olculemedi
                        neden="Varlık listesi tanınmayan bir biçimde geldi"
                        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                      />
                    );
                  }
                  if (g.items.length === 0) {
                    return (
                      <p className="text-muted-foreground text-sm">
                        {atlanan === 0
                          ? "Bu banka okundu ve kayıtlı isim YOK. Bu ölçülmüş bir boşluktur."
                          : "Bu sayfada isim YOK — liste daha önceki bir sayfada bitmiş."}
                      </p>
                    );
                  }
                  return (
                    <div className="overflow-x-auto">
                      <Table className="min-w-[40rem]">
                        <TableHeader className="bg-muted/50">
                          <TableRow>
                            <TableHead>İsim</TableHead>
                            <TableHead className="w-28 text-right">Anılma</TableHead>
                            <TableHead className="w-44">İlk görülme</TableHead>
                            <TableHead className="w-44">Son görülme</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {g.items.map((v, i) => {
                            const ad = metin(v.canonical_name);
                            const kimlik = metin(v.id);
                            const n = sayi(v.mention_count);
                            const ilk = damga(v.first_seen);
                            const son = damga(v.last_seen);
                            return (
                              <TableRow
                                key={kimlik ?? `varlik-${atlanan + i}`}
                                className={cn(
                                  kimlik !== null && "cursor-pointer hover:bg-muted/50",
                                  kimlik !== null && kimlik === secili && "bg-primary/10",
                                )}
                                /* `aria-current`, `aria-selected` DEĞİL (inceleme M-5):
                                   ikincisi yalnız ızgara/ağaç rollerinde tanımlı, düz
                                   tabloda yardımcı teknoloji onu yok sayabilir. */
                                aria-current={kimlik !== null && kimlik === secili ? "true" : undefined}
                                onClick={kimlik === null ? undefined : () => varligiSec(kimlik)}
                              >
                                <TableCell className="max-w-0">
                                  {ad === null ? (
                                    <Olculemedi
                                      neden="İsim gelmedi"
                                      teknik="satırda kanonik ad alanı yok ya da dizge değil"
                                      kisa
                                    />
                                  ) : kimlik === null ? (
                                    <span className="block truncate font-medium text-sm" title={ad}>
                                      {ad}
                                    </span>
                                  ) : (
                                    /* DÜĞME, ÇÜNKÜ KLAVYE: satırın kendisi tıklanabilir ama
                                       odaklanamaz — isim hücresini düğme yapmak aynı eylemi
                                       sekme tuşuyla da erişilebilir kılar. */
                                    <button
                                      type="button"
                                      className="block w-full truncate text-left font-medium text-sm hover:underline"
                                      title={ad}
                                      onClick={() => varligiSec(kimlik)}
                                    >
                                      {ad}
                                    </button>
                                  )}
                                  <span className="mt-0.5 block truncate font-mono text-[11px] text-muted-foreground">
                                    {kimlik ?? (
                                      <Olculemedi
                                        neden="kimlik gelmedi"
                                        teknik="satırda kimlik alanı yok ya da dizge değil"
                                        kisa
                                      />
                                    )}
                                  </span>
                                  {kimlik === null ? (
                                    <span className="mt-1 block text-[11px] text-muted-foreground italic">
                                      kimliği gelmediği için bu ismin künyesi açılamaz
                                    </span>
                                  ) : null}
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  {n === null ? (
                                    <Olculemedi
                                      neden="Anılma sayısı gelmedi"
                                      teknik="anılma sayacı gelmedi ya da sayı değil"
                                      kisa
                                    />
                                  ) : (
                                    n.toLocaleString("tr-TR")
                                  )}
                                </TableCell>
                                <TableCell className="text-muted-foreground text-xs tabular-nums">
                                  {ilk ?? (
                                    <Olculemedi
                                      neden="İlk görülme gelmedi"
                                      teknik="ilk görülme damgası gelmedi ya da çözülemedi"
                                      kisa
                                    />
                                  )}
                                </TableCell>
                                <TableCell className="text-muted-foreground text-xs tabular-nums">
                                  {son ?? (
                                    <Olculemedi
                                      neden="Son görülme gelmedi"
                                      teknik="son görülme damgası gelmedi ya da çözülemedi"
                                      kisa
                                    />
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

          {/* SAYFALAMA KAPININ İÇİNDE (Görev 2 incelemesi, bulgu M-4): dışarıda
              dururken istek düştüğünde "Okunamadı" uyarısının altında ölçülmemiş
              bir sayfa konumu çiziliyordu. */}
          <UcKapisi durum={liste} yol={UC_VARLIKLAR} iskelet={<></>}>
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
      )}

      {/* ÜST YÜZEYDE BU GÖRÜNÜMDE YAZAN DÜĞME YOK — ve bunu yazmak gerekiyor:
          boş bir düğme şeridi "unutulmuş" diye okunurdu. */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
          bu görünümde yazan bir düğme yok — üst yüzeyde de yok, hepsi okuma
        </Badge>
      </div>

      <Sheet
        open={secili !== null}
        onOpenChange={(a) => {
          if (!a) setSecili(null);
        }}
      >
        {/* BAŞLIK VE GÖVDE ARTIK AYNI BİLEŞENDE (inceleme M-4): başlığın taşıdığı
            ad künyenin okunduğu yerde yaşıyor, yani ikinci bir kaynaktan
            beslenmiyor. Hiç isim seçilmemiş hâl yalnız çekmece kapalıyken
            görülebilir; başlık orada da ZORUNLUdur (erişilebilir ad). */}
        <SheetContent key={cekmeceAnahtari} side="right" className="w-full sm:max-w-xl">
          {cekmeceAnahtari === "bos" ? (
            <SheetHeader className="pr-10">
              <SheetTitle className="text-base leading-6">Varlık künyesi</SheetTitle>
              <SheetDescription>Bir isme tıkla.</SheetDescription>
            </SheetHeader>
          ) : (
            <VarlikCekmecesi bank={bank} kimlik={cekmeceAnahtari} acik={secili !== null} />
          )}
        </SheetContent>
      </Sheet>
    </BolumKart>
  );
}
