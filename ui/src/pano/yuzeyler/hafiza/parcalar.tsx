"use client";

/* ============================================================================
   HAFIZA YÜZEYİNİN ORTAK PARÇALARI
   ----------------------------------------------------------------------------
   Sekiz görünüm AYNI üç soruyu tekrar tekrar soruyor: "zarf geldi mi", "alan
   geldi mi", "gelen değer ne". Üçünü her görünümde elle yazmak, birinde
   unutulduğunda ekranın SESSİZCE yalan söylemesi demekti — boş bir kart
   "ölçtük, hiçbir şey yok" diye okunur. `sistem/parcalar.tsx`in bu yüzeye özgü
   kardeşi: oradaki `Kapi`/`Olculemedi`/`Satir` AYNEN kullanılır, burada yalnız
   Hindsight'a özgü olanlar yaşar.

   ---------------------------------------------------------------------------
   YAZMA YOLU YOK — VE BU EKRANDA GÖRÜNÜR
   ---------------------------------------------------------------------------
   Hindsight'ın kendi denetim yüzeyinde bellek düzenleme, geçersiz kılma, belge
   yeniden işleme, yapılandırma yazımı ve değerlendirme tetikleme düğmeleri VAR.
   Bizim vekilimizde onların KARŞILIĞI YOK (kapsam kararı: Faz-1 salt-okunur).

   Düğmeleri GİZLEMİYORUZ, DEVRE DIŞI çiziyoruz. Gizlemek iki şeyi birbirine
   karıştırırdı: "böyle bir yetenek yok" ile "yetenek var, bu panodan
   kullanılamıyor". İkincisi doğru olan ve operatörün bilmesi gereken. Rozet
   nedenini söylüyor, düğme tıklanmıyor.
   ============================================================================ */
import { useState, type ReactNode } from "react";
import { Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

import { Olculemedi, Satir, zamanMetni } from "../sistem/parcalar";
import type { HamGovde } from "./uctipleri";

/* ---------------------------------------------------------------------------
   HAM GÖVDE ÇİZİMİ — "tanımadığını sessizce boş sayma" ilkesinin ekran karşılığı
   Bu yüzeyin gösterdiği değerlerin BÜYÜK KISMI depo tarafından KURULMAZ, yalnız
   TAŞINIR (`uctipleri.ts` başlığı). Alan adlarını burada sabitlemek
   `api.py::_hafiza_surum`un ölçülmüş dersini tekrarlamak olurdu: `version`
   varsayılmıştı, canlıda alan `api_version`dı, ve sürüm SESSİZCE boş kalacaktı.
   Bu yüzden anahtarlar TELDEN gelir ve tanınmayan anahtar ATILMAZ, ham basılır.
   --------------------------------------------------------------------------- */

/** JSON değerini insan metnine çevirir. Çeviremediğinde `null` — çağıran ham basar.
 *  İHRAÇ EDİLMEZ: tek tüketicisi bu dosya. İhraç edilmiş bir yardımcı okuru olmayan
 *  bir yüzeydir ve ilk kullanan onu kendi anlamıyla eğer (Yasa 6'nın ruhu). */
function hamMetin(deger: unknown): string | null {
  if (typeof deger === "string") return deger;
  if (typeof deger === "number") return Number.isFinite(deger) ? deger.toLocaleString("tr-TR") : null;
  if (typeof deger === "boolean") return deger ? "evet" : "hayır";
  return null;
}

/**
 * ISO-BENZERİ DAMGA TESTİ — ve NEDEN VAR (Görev 1 düzeltme turu, bulgu B-1).
 *
 * İlk yazımda `HamDeger` HER skaleri `zamanMetni`ne veriyordu: "alan adını bilmiyorum, belki
 * tarihtir" mantığıyla. ÖLÇÜLDÜ ki bu, ekrana UYDURMA TARİH bastırıyordu — V8'de
 * `new Date("3")` GEÇERLİ bir tarihtir (01.03.2001). Yani 0-999 arası her sayaç (olay sayısı,
 * istek sayısı) ekranda bir tarihe dönüşüyordu; 1000 ve üstü yalnız KAZARA kurtuluyordu, çünkü
 * `toLocaleString("tr-TR")` binlik ayracı olarak nokta koyuyor ve `new Date("1.234")` geçersiz
 * oluyordu. Bir sayacı tarihe çevirmek, uydurma yasağının en sinsi biçimi: ekran hem yanlış hem
 * kendinden emin görünür.
 *
 * KURAL: `zamanMetni` bu yüzeyde ancak biçimi ISO damgasına BENZEYEN bir dizgeye uygulanır.
 * Alan adı BİLİNEN yerlerde (`created_at`, `mentioned_at` …) kural yine geçerli: bilinen bir
 * ad da bozuk bir damga taşıyabilir ve `zamanMetni` onu zaten `null` döndürür.
 */
export const ISO_BENZERI = /^\d{4}-\d{2}-\d{2}T/;

/** Düz sözlük mü? Dizi ve boş değer BURADA sözlük DEĞİLDİR — ikisi de ayrı çizilir. */
export function sozluk(deger: unknown): HamGovde | null {
  return typeof deger === "object" && deger !== null && !Array.isArray(deger) ? (deger as HamGovde) : null;
}

/** Dizge mi? Boş dizge burada DEĞER SAYILMAZ — ekranda boş bir hücre bırakırdı. */
export function metin(deger: unknown): string | null {
  return typeof deger === "string" && deger.length > 0 ? deger : null;
}

/** Sonlu sayı mı? Sayıya ÇEVİRMEYE ÇALIŞMAZ: `"12"` dizgesini sayı saymak, üst
 *  servisin tip sürüklenmesini sessizce onarmak (ve gizlemek) olurdu. */
export function sayi(deger: unknown): number | null {
  return typeof deger === "number" && Number.isFinite(deger) ? deger : null;
}

/** Damga metni — yalnız ISO benzeri dizgeye uygulanır (yukarıdaki şerh). */
export function damga(deger: unknown): string | null {
  const s = metin(deger);
  return s !== null && ISO_BENZERI.test(s) ? zamanMetni(s) : null;
}

/**
 * ETİKET/VARLIK LİSTESİ — İKİ BİÇİM DE KARŞILANIR, VE BU ÖLÇÜLDÜ.
 *
 * Upstream'in kayıt örneği `entities`i virgüllü TEK DİZGE veriyor
 * (`"Alice (PERSON), Google (ORGANIZATION)"`) ve üst yüzey de onu ", " ile
 * bölüyor; aynı alan başka yerde DİZİ geliyor. Tek biçime bağlanan taraf
 * ötekinde ya boş kalır ya da tek satırda hepsini basar.
 */
export function listeye(deger: unknown): readonly string[] | null {
  /* ÜÇ HÂL, İKİ KANAL — VE BU BİR DÜZELTMEDİR (inceleme bulgusu I-6). İlk yazımda
     `listeye(undefined)` ile `listeye([])` AYNI boş diziyi üretiyordu, yani ekranda
     "bu kayıtta etiket yok" ile "etiket alanı hiç gelmedi" ayırt edilemiyordu. Aynı
     paketin ithal ettiği bileşenin sözleşmesi bunu yasaklıyor (`sistem/parcalar.tsx`:
     "`neden` ZORUNLU — '—' tek başına yalandır"). `null` = OKUNAMADI (alan yok ya da
     tanınmayan bir tiple geldi); boş dizi = ÖLÇÜLDÜ, içi boş. */
  if (Array.isArray(deger)) {
    return deger
      .map((x) => (typeof x === "string" ? x : sozluk(x) ? (metin((x as HamGovde).name) ?? JSON.stringify(x)) : hamMetin(x)))
      .filter((x): x is string => typeof x === "string" && x.length > 0);
  }
  if (deger === null) return [];          // alan geldi, değeri boş
  if (deger === undefined) return null;   // alan hiç gelmedi
  const s = metin(deger);
  if (s === null) return null;            // tanınmayan tip — "boş" demek yalan olurdu
  return s.split(",").map((p) => p.trim()).filter((p) => p.length > 0);
}

/** Karakter sayısı → insan okuru. Ölçülemeyen değer için `null` (uydurma yasağı). */
export function uzunlukMetni(deger: unknown): string | null {
  const n = sayi(deger);
  if (n === null) return null;
  if (n < 1000) return `${n.toLocaleString("tr-TR")} karakter`;
  return `${(n / 1000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} bin karakter`;
}

/** Tek bir ham değer. Üç hâl AYRI: alan yok · değer boş · değer var. */
export function HamDeger({ deger }: { readonly deger: unknown }) {
  if (deger === undefined) {
    return <Olculemedi neden="Bu alan bildirilmedi" teknik="anahtar üst servisin gövdesinde hiç yok" kisa />;
  }
  if (deger === null) {
    return <Olculemedi neden="Ölçüldü, sonuç yok" teknik="alan geldi ama değeri boş — sıfır ile aynı şey değil" kisa />;
  }
  /* ZAMAN ÇEVİRİSİ YALNIZ DİZGEYE VE YALNIZ ISO BİÇİMİNDE (yukarıdaki şerh):
     sayıyı tarihe çevirmek ölçülmüş bir sayacı uydurma bir güne dönüştürürdü. */
  if (typeof deger === "string") {
    return <span className="tabular-nums">{damga(deger) ?? deger}</span>;
  }
  const duz = hamMetin(deger);
  if (duz !== null) {
    return <span className="tabular-nums">{duz}</span>;
  }
  /* İÇ İÇE GÖVDE: şekli ölçülmedi. Atmak "böyle bir veri yok" derdi; ham basmak
     "böyle bir veri var, biçimini tanımıyorum" der. İkincisi doğru olandır. */
  const yazi = JSON.stringify(deger);
  return (
    <code className="break-all text-[11px]" title={yazi}>
      {yazi.length > 140 ? `${yazi.slice(0, 140)}…` : yazi}
    </code>
  );
}

/**
 * Bir gövdenin TAMAMI — anahtarlarıyla birlikte.
 *
 * ANAHTARLAR ÇEVRİLMEZ VE BU BİR EKSİK DEĞİL, BEYAN: üst servisin alan sözlüğü
 * bizim sözleşmemiz değil ve bir çeviri tablosu yazmak, uydurulmuş bir ad
 * kümesini ekranın birincil metni yapardı. Tanınmayan bir alan geldiği gün ham
 * adıyla görünür — kaybolmaz.
 */
export function HamSatirlar({
  govde,
  atla = [],
}: {
  readonly govde: HamGovde;
  /** Yukarıda ZATEN çizilmiş alanlar. Atlanan alan kaybolmaz; çağıran onu kendi
   *  biçiminde göstermiş olur — bu liste bir gizleme değil, tekrar önlemedir. */
  readonly atla?: readonly string[];
}) {
  const satirlar = Object.entries(govde)
    .filter(([anahtar]) => !atla.includes(anahtar))
    .sort((a, b) => a[0].localeCompare(b[0]));
  if (satirlar.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Gövde okundu ve gösterilecek başka alan gelmedi — bu ölçülmüş bir boşluktur, "okuyamadım"
        ile aynı şey değildir
      </p>
    );
  }
  return (
    <div>
      {satirlar.map(([anahtar, deger]) => (
        <Satir key={anahtar} etiket={anahtar}>
          <HamDeger deger={deger} />
        </Satir>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ETİKET VE VARLIK ÇİPLERİ — üst yüzeyin iki ayrı çip sınıfının karşılığı
   Ayrı çizilmelerinin sebebi anlam: etiket ARAMA EKSENİDİR (filtreye tıklanır),
   varlık ise kaydın İÇERİĞİDİR. Aynı çipe indirmek ikisini tek şey sanmaktı.
   --------------------------------------------------------------------------- */

export function Cipler({
  degerler,
  tavan = 3,
  bicim,
  ne = "Bu alan",
}: {
  /** `null` = okunamadı (alan yok ya da tanınmayan tip); boş dizi = ölçüldü, içi boş. */
  readonly degerler: readonly string[] | null;
  readonly tavan?: number;
  readonly bicim?: string;
  /** Gerekçe cümlesinin öznesi — hangi alanın gelmediğini söyler. */
  readonly ne?: string;
}) {
  if (degerler === null) {
    return <Olculemedi neden={`${ne} gelmedi`} teknik="alan yanıtta yok ya da liste olarak okunamayan bir tiple geldi" kisa />;
  }
  if (degerler.length === 0) {
    return <span className="text-muted-foreground text-xs italic">boş</span>;
  }
  const gorunen = degerler.slice(0, tavan);
  const kalan = degerler.length - gorunen.length;
  return (
    <div className="flex flex-wrap items-center gap-1">
      {gorunen.map((d) => (
        <Badge key={d} variant="outline" className={cn("max-w-[12rem] truncate font-normal text-[11px]", bicim)} title={d}>
          {d}
        </Badge>
      ))}
      {kalan > 0 ? (
        <span className="text-[11px] text-muted-foreground tabular-nums" title={degerler.join(" · ")}>
          +{kalan}
        </span>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   ETİKET SÜZGECİ — SÖZLÜK VE ŞERİT TEK KAYNAKTA (inceleme bulgusu I-5)
   ----------------------------------------------------------------------------
   Beş değerli eşleşme sözlüğü ÖNCE İKİ dosyada iki kopya olarak duruyordu ve
   ikisi de aynı sunucu çapasını gösteren aynı şerhi taşıyordu — yani §4'ün
   "aynı gerçeğin iki kopyası sessizce ayrışır" sınıfının ders kitabı hâli.
   Sunucudaki demet bir gün büyürse bir ekran seçeneği sunar, öteki sunmaz ve
   fark yalnız kaynağı okuyanın gözünden anlaşılırdı.

   ŞERİDİN KENDİSİ DE BURADA, AMA YALNIZ ORTAK OLAN ÜÇ DENETİM: arama kutusu,
   etiket kutusu ve eşleşme seçicisi. Görünüme ÖZGÜ denetimler (tür/durum
   düğmeleri) çağıranda kalır — hepsini tek bileşene doldurmak, iki çağıranın
   farklı süzgeç kümelerini tek soyutlamaya zorlamak olurdu (erken soyutlama).
   --------------------------------------------------------------------------- */

/** `api.py::_HAFIZA_ETIKET_ESLEME` — beş değer, üst servisin şemasından ölçüldü.
 *  Buraya fazladan bir değer yazmak düğmeyi çalışır gösterir ama süzgeci sessizce
 *  düşürürdü: sunucu tanımadığı değeri üst servise GÖNDERMİYOR. */
export const ETIKET_ESLEME = [
  { deger: "any", etiket: "herhangi biri" },
  { deger: "all", etiket: "hepsi" },
  { deger: "any_strict", etiket: "herhangi biri, yalnız bunlar" },
  { deger: "all_strict", etiket: "hepsi, yalnız bunlar" },
  { deger: "exact", etiket: "birebir aynı küme" },
] as const;

/**
 * Arama + etiket + eşleşme şeridi.
 *
 * KUTUDA YAZILAN ile ÜST SERVİSE GİDEN ayrı tutulur ve ayrım BURADA yaşar: her
 * tuşta bir sorgu açmak hem gereksiz yük olurdu hem de yarım yazılmış bir
 * kelimenin boş sonucu "kayıt yok" diye okunurdu. Uygulama Enter'da, temizleme
 * Escape'te.
 */
export function SuzgecSeridi({
  arama,
  setArama,
  etiketler,
  setEtiketler,
  esleme,
  setEsleme,
  aramaEtiketi,
}: {
  readonly arama: string;
  readonly setArama: (s: string) => void;
  readonly etiketler: string;
  readonly setEtiketler: (s: string) => void;
  readonly esleme: string;
  readonly setEsleme: (s: string) => void;
  /** "Metinde ara" / "Belgelerde ara" — tek fark bu. */
  readonly aramaEtiketi: string;
}) {
  const [aramaKutusu, setAramaKutusu] = useState(arama);
  const [etiketKutusu, setEtiketKutusu] = useState(etiketler);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-end gap-2">
        <label className="flex min-w-[14rem] flex-1 flex-col gap-1">
          <span className="text-muted-foreground text-xs">{aramaEtiketi}</span>
          <span className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden />
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
        <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
          <span className="text-muted-foreground text-xs">Etiketler (virgülle)</span>
          <Input
            value={etiketKutusu}
            onChange={(e) => setEtiketKutusu(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") setEtiketler(etiketKutusu.trim());
              if (e.key === "Escape") {
                setEtiketKutusu("");
                setEtiketler("");
              }
            }}
            placeholder="yazıp Enter'a bas"
            className="h-8"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted-foreground text-xs">Etiket eşleşmesi</span>
          <Select value={esleme} onValueChange={setEsleme}>
            <SelectTrigger className="h-8 w-52" aria-label="Etiket eşleşmesi">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ETIKET_ESLEME.map((e) => (
                <SelectItem key={e.deger} value={e.deger}>
                  {e.etiket}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
      </div>
      {etiketler === "" ? (
        <p className="text-muted-foreground text-[11px]">
          Etiket eşleşmesi yalnız etiket verildiğinde gönderilir — tek başına gönderilseydi
          süzgeçsiz bir listelemede üst servisin kendi varsayılanını sessizce değiştirirdi
        </p>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   FAZ-2 DÜĞMELERİ — GÖRÜNÜR AMA ÇALIŞMAZ
   --------------------------------------------------------------------------- */

/** Rozetin metni TEK YERDE: on beş düğmenin yanında elle yazılsaydı biri
 *  ötekinden ayrışır ve iki farklı vaat gibi okunurdu (tek-kaynak yasası). */
export const FAZ2_ROZET = "yazma yolu Faz-2 (operatör kararı bekler)";

/**
 * Devre dışı bir yazma düğmesi. `neden` DÜĞMENİN KENDİSİNDE durur — rozet
 * grubun başında bir kez.
 *
 * GEREKÇE FAREYE DEĞİL ADA BAĞLIDIR (inceleme bulgusu M-6): `title` yalnız
 * üstüne gelene okunur; devre dışı düğme odak da alamadığı için klavyeyle hiç
 * ulaşılamıyordu. Gerekçe artık düğmenin ERİŞİLEBİLİR ADININ parçası — ekran
 * okuyucu tarama kipinde onu düğmenin kendisiyle birlikte okur. Görünen metin
 * adın içinde kaldığı için sesli komutla söylenen ad da çalışmaya devam eder.
 */
export function Faz2Dugme({
  children,
  ne,
}: {
  readonly children: ReactNode;
  /** Bu düğme ne yapacaktı — gerekçe cümlesinin öznesi. */
  readonly ne: string;
}) {
  return (
    <Button variant="outline" size="sm" disabled title={`${ne} — ${FAZ2_ROZET}`}>
      {children}
      <span className="sr-only"> — {ne} — {FAZ2_ROZET}</span>
    </Button>
  );
}

/** Devre dışı düğmelerin kabı: rozet bir kez, düğmeler yan yana. */
export function Faz2Grup({ children }: { readonly children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {children}
      <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
        {FAZ2_ROZET}
      </Badge>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   SAYFALAMA — VE SÖYLEYEBİLDİĞİNİN SINIRI
   Toplam sayı GELDİYSE aralık gerçek bir ölçümdür ("150 kayıttan 1-50 arası").
   GELMEDİYSE "sonraki"nin açık olması bir ÇIKARIMDIR (sayfa dolu geldi), bir
   ölçüm değil — ve bu ayrım düğmenin yanında yazılı durur.
   --------------------------------------------------------------------------- */

export function Sayfalama({
  atlanan,
  gelen,
  sayfaBoyu,
  toplam,
  setAtlanan,
}: {
  readonly atlanan: number;
  readonly gelen: number;
  readonly sayfaBoyu: number;
  /** `null` = kaç kayıt olduğu ölçülemedi; sıfır anlamına GELMEZ. */
  readonly toplam: number | null | undefined;
  readonly setAtlanan: (f: (n: number) => number) => void;
}) {
  const toplamVar = typeof toplam === "number" && Number.isFinite(toplam);
  const doluSayfa = gelen === sayfaBoyu;
  const devamiVar = toplamVar ? atlanan + gelen < (toplam as number) : doluSayfa;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-muted-foreground text-xs tabular-nums">
          {gelen > 0
            ? `${atlanan + 1}–${atlanan + gelen} arası okundu`
            : `${atlanan}. kayıttan sonrası okundu`}
          {toplamVar ? ` · toplam ${(toplam as number).toLocaleString("tr-TR")}` : ""}
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={atlanan === 0}
            onClick={() => setAtlanan((n) => Math.max(0, n - sayfaBoyu))}
          >
            Önceki
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={!devamiVar}
            title={
              toplamVar
                ? "toplam sayı üst servisten geldi — bu bir ölçümdür"
                : devamiVar
                  ? "sayfa dolu geldi, devamı OLABİLİR; toplam sayı gelmediği için bu bir çıkarımdır"
                  : "sayfa dolmadan bitti — okunacak başka kayıt görünmüyor"
            }
            onClick={() => setAtlanan((n) => n + sayfaBoyu)}
          >
            Sonraki
          </Button>
        </div>
      </div>
      {!toplamVar ? (
        <p className="text-muted-foreground text-[11px]">
          Toplam kayıt sayısı bu okumada gelmedi: kaçıncı sayfada olduğun ekranda yazamaz, çünkü o
          sayı ölçülmüş değil
        </p>
      ) : null}
    </div>
  );
}
