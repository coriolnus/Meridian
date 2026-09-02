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
import type { HafizaZarfi, HamGovde, IstatistikKovasi } from "./uctipleri";

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
 * Damganın MİLİSANİYESİ — aynı kapıdan, aynı gerekçeyle (inceleme I-2).
 *
 * `damga()` bir dizge döndürür; iki damga arasındaki SÜREYİ hesaplayan çağıran
 * ise sayıya ihtiyaç duyar ve kendi `Date.parse`ını yazma eğilimindedir. İlk
 * yazımda Yapılandırma tam bunu yaptı: korumasız `Date.parse` — yani `"3"`
 * dizgesi 01.03.2001'e çözülüp UYDURMA bir süre bastıracak yol (Görev 2
 * incelemesi I-3'ün birebir dönüşü). Üçlü kapı burada TEK yerde durur:
 * dizge mi → ISO'ya benziyor mu → çözülebiliyor mu.
 */
export function damgaMs(deger: unknown): number | null {
  const s = metin(deger);
  if (s === null || !ISO_BENZERI.test(s)) return null;
  const t = Date.parse(s);
  return Number.isFinite(t) ? t : null;
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

/* ============================================================================
   GÖREV 3'ÜN ORTAK PARÇALARI — beş görünümün AYNI üç sorusu
   ----------------------------------------------------------------------------
   Bu blok TSK-108 Görev 3 ile doğdu ve buraya AİT: kalan beş görünüm de aynı üç
   soruyu soruyor — "zarf geldi mi", "hangi pencere seçili", "kova dizisi ne
   diyor". Üçünü beş dosyada beş kez yazmak, `ETIKET_ESLEME` sözlüğünün ilk
   yazımda iki kopyaya bölünmesiyle AYNI sınıftır (Görev 2 incelemesi, I-5):
   aynı gerçeğin iki kopyası sessizce ayrışır.
   ============================================================================ */

/* ---------------------------------------------------------------------------
   ZARF KAPISI — DÖRT HÂL AYRI
   `api.py::_hafiza_zarf` on dokuz uçta aynı zarfı döndürüyor: `{govde, neden}`.
   Dördü tek `if`e indirilseydi "uç gövde alanını hiç döndürmedi" (şema
   sürüklenmesi) ile "ölçüm denendi ve düştü" (ağ/anahtar) ekranda aynı görünür,
   operatör de yanlış yere bakardı.
   --------------------------------------------------------------------------- */
export function ZarfKapisi<G>({
  zarf,
  ne,
  children,
}: {
  readonly zarf: HafizaZarfi<G> | null;
  /** Neyin okunamadığı — gerekçe cümlesinin öznesi. */
  readonly ne: string;
  readonly children: (govde: G) => ReactNode;
}) {
  if (zarf === null) return null;
  if (zarf.neden) return <Olculemedi neden={`${ne} okunamadı`} teknik={zarf.neden} />;
  if (zarf.govde === undefined) {
    return <Olculemedi neden={`${ne} bildirilmedi`} teknik="uç gövde alanını hiç döndürmedi" />;
  }
  if (zarf.govde === null) {
    return (
      <Olculemedi
        neden={`${ne} için ölçüm denendi, gövde gelmedi`}
        teknik="gövde boş döndü ve gerekçe de taşınmadı"
      />
    );
  }
  return <>{children(zarf.govde)}</>;
}

/* ---------------------------------------------------------------------------
   BÖLME — bir görünümün içindeki adlandırılmış bölüm
   Üst yüzey bu bölümleri SEKME olarak ayırıyor; biz sekmeyi de kullanıyoruz ama
   sekmenin içindeki her blok yine kendi başlığını ve — varsa — kapsam cümlesini
   taşıyor. Başlıksız bir blok, iki ölçümü tek ölçüm gibi okutur.
   --------------------------------------------------------------------------- */
export function Bolme({
  baslik,
  aciklama,
  aksiyon,
  children,
}: {
  readonly baslik: string;
  /** Bu bloğun cevapladığı soru ya da kapsamının sınırı. */
  readonly aciklama?: string;
  readonly aksiyon?: ReactNode;
  readonly children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">{baslik}</h4>
        {aksiyon}
      </div>
      {aciklama ? <p className="text-muted-foreground text-xs">{aciklama}</p> : null}
      {children}
    </section>
  );
}

/* ---------------------------------------------------------------------------
   İSTATİSTİK PENCERESİ — SÖZLÜK SUNUCUNUNKİDİR
   `api.py::_HAFIZA_ISTATISTIK_PENCERESI` = ("1d","7d","30d") ve varsayılan
   `_HAFIZA_VARSAYILAN_PENCERE` = "7d". Buraya fazladan bir değer yazmak (ör.
   "90d", ki seri ucunda GEÇERLİdir) düğmeyi çalışır gösterir ama sunucu onu
   tanımaz ve sessizce varsayılana düşerdi: ekran bir pencereyi seçili gösterip
   başka bir pencerenin sayısını çizerdi.
   --------------------------------------------------------------------------- */
/* İHRAÇ EDİLMEZ: tek tüketicisi aşağıdaki `PencereDugmeleri`. Dışarıya açılsaydı
   ikinci bir pencere şeridi doğar ve sunucunun sözlüğüyle sessizce ayrışırdı. */
const ISTATISTIK_PENCERELERI = [
  { deger: "1d", etiket: "1 gün" },
  { deger: "7d", etiket: "7 gün" },
  { deger: "30d", etiket: "30 gün" },
] as const;

export const VARSAYILAN_ISTATISTIK_PENCERESI = "7d";

export function PencereDugmeleri({
  pencere,
  setPencere,
}: {
  readonly pencere: string;
  readonly setPencere: (p: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      {ISTATISTIK_PENCERELERI.map((p) => (
        <Button
          key={p.deger}
          type="button"
          size="sm"
          variant={pencere === p.deger ? "secondary" : "ghost"}
          className="h-7 px-2 text-xs"
          aria-pressed={pencere === p.deger}
          onClick={() => setPencere(p.deger)}
        >
          {p.etiket}
        </Button>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   SEÇİM ŞERİDİ — etiketli tek seçim
   Süzgeç değerlerinin SÖZLÜĞÜ her çağıranda kendi yerinde durur (her uç farklı
   bir sözlük taşıyor); ortak olan yalnız KABIDIR. Kabı da her dosyada yeniden
   yazmak, aynı denetimi beş ayrı biçimde çizmek olurdu.
   --------------------------------------------------------------------------- */
export function Secim({
  etiket,
  deger,
  setDeger,
  secenekler,
  genislik = "w-44",
}: {
  readonly etiket: string;
  readonly deger: string;
  readonly setDeger: (d: string) => void;
  /** `deger: ""` = süzgeç kapalı; çağıran bunu sorguya HİÇ koymaz. */
  readonly secenekler: readonly { readonly deger: string; readonly etiket: string }[];
  readonly genislik?: string;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-muted-foreground text-xs">{etiket}</span>
      <Select value={deger} onValueChange={setDeger}>
        <SelectTrigger className={cn("h-8", genislik)} aria-label={etiket}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {secenekler.map((s) => (
            <SelectItem key={s.deger === "" ? "__hepsi" : s.deger} value={s.deger === "" ? "__hepsi" : s.deger}>
              {s.etiket}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}

/** Seçicinin "hepsi" nöbetçisini sorgu değerine çevirir. Radix boş dizgeli bir
 *  seçenek kabul etmiyor, o yüzden nöbetçi gerekiyor; nöbetçinin sorguya
 *  SIZMAMASI da bu tek yerde garanti edilir. */
export function secimDegeri(ham: string): string {
  return ham === "__hepsi" ? "" : ham;
}

/* ---------------------------------------------------------------------------
   KOVA ŞERİDİ — zaman serisi kovalarının kütüphanesiz çizimi
   ----------------------------------------------------------------------------
   ÜST YÜZEY BUNU BİR ÇİZGİ GRAFİĞİ OLARAK ÇİZİYOR; burada yatay çubuk şeridi
   var ve fark bilinçli: çubuk şeridi her kovanın SAYISINI da yazabiliyor, yani
   ekran "yüksekliği gördün" demekle yetinmiyor, ölçülen sayıyı gösteriyor.

   ÖLÇEK EN BÜYÜK KOVAYA GÖRE ve bu bir SIRALAMA ölçüsüdür, mutlak değil —
   çubuğun uzunluğuna bakıp "çok" demek yalnız aynı şerit içinde anlamlıdır.
   Bu cümle şeridin altında YAZILI durur, çünkü bir grafiği yanlış okumak
   ölçülmemiş bir sonuca varmanın en kolay yoludur.

   ÜÇ HÂL AYRI: dizi değil (şema sürüklenmesi) · boş dizi (ölçülmüş boşluk) ·
   dolu. Sayısı okunamayan kova ATILMAZ, "sayı gelmedi" diye çizilir.
   --------------------------------------------------------------------------- */
export function KovaSeridi({
  kovalar,
  deger,
  ne,
  birim = "",
}: {
  readonly kovalar: unknown;
  /** Kovadan çizilecek sayıyı çeker. `null` = bu kovada sayı ölçülemedi. */
  readonly deger: (k: IstatistikKovasi) => number | null;
  /** Neyin sayıldığı — boşluk cümlesinin öznesi. */
  readonly ne: string;
  readonly birim?: string;
}) {
  if (!Array.isArray(kovalar)) {
    return (
      <Olculemedi
        neden={`${ne} kovaları tanınmayan bir biçimde geldi`}
        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
      />
    );
  }
  /* ÖĞE KAPISI (inceleme M-8): dizinin İÇİ de doğrulanır. `null` bir öğe gelirse
     (şema sürüklenmesi) `deger(k)` bir tip hatası atar ve BÜTÜN görünüm düşer —
     oysa bu dosyanın her yerindeki disiplin "tanımadığını çiz, düşme". Sözlük
     olmayan öğe atılmaz, SAYILIR ve sayısı aşağıda yazılır. */
  const ham = kovalar as readonly unknown[];
  const liste = ham.filter((k): k is IstatistikKovasi => sozluk(k) !== null);
  const taninmayanKova = ham.length - liste.length;
  if (liste.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Bu pencere okundu ve içinde hiç {ne.toLocaleLowerCase("tr-TR")} yok — bu ölçülmüş bir
        boşluktur, "okuyamadım" ile aynı şey değildir
      </p>
    );
  }
  const sayilar = liste.map((k) => deger(k));
  const enBuyuk = sayilar.reduce<number>((m, n) => (n !== null && n > m ? n : m), 0);
  const olculen = sayilar.filter((n): n is number => n !== null);
  const toplam = olculen.reduce((a, b) => a + b, 0);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="tabular-nums">
          toplam {toplam.toLocaleString("tr-TR")}
          {birim}
        </Badge>
        {olculen.length !== liste.length ? (
          <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
            {liste.length - olculen.length} kovanın sayısı okunamadı — toplama katılmadı
          </Badge>
        ) : null}
        {taninmayanKova > 0 ? (
          <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
            {taninmayanKova} kova sözlük olarak okunamadı — hiç çizilmedi
          </Badge>
        ) : null}
      </div>
      <div className="flex flex-col gap-0.5">
        {liste.map((k, i) => {
          const n = deger(k);
          const ham = metin(k.time);
          const etiket = damga(k.time) ?? ham ?? `kova ${i + 1}`;
          const oran = n === null || enBuyuk <= 0 ? 0 : (n / enBuyuk) * 100;
          return (
            <div key={ham ?? `kova-${i}`} className="flex items-center gap-2">
              <span className="w-40 shrink-0 truncate text-[11px] text-muted-foreground" title={ham ?? undefined}>
                {etiket}
              </span>
              <span className="h-3 min-w-0 flex-1 rounded-sm bg-muted">
                <span
                  className="block h-full rounded-sm bg-foreground/25"
                  style={{ width: `${oran}%` }}
                  aria-hidden
                />
              </span>
              <span className="w-24 shrink-0 text-right text-[11px] tabular-nums">
                {n === null ? (
                  <Olculemedi neden="Sayı gelmedi" teknik="kovanın sayacı gelmedi ya da sayı değil" kisa />
                ) : (
                  `${n.toLocaleString("tr-TR")}${birim}`
                )}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-muted-foreground text-[11px]">
        Çubuk uzunluğu ŞERİDİN EN BÜYÜK KOVASINA göredir — iki ayrı şeridin çubukları
        karşılaştırılamaz; karşılaştırılabilen şey yazılı sayılardır
      </p>
    </div>
  );
}

/** Kovanın toplam sayacı — iki istatistik ucunda da `total`. */
export function kovaToplami(k: IstatistikKovasi): number | null {
  return sayi(k.total);
}
