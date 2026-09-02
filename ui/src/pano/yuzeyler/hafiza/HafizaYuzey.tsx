"use client";

/* ============================================================================
   HAFIZA YÜZEYİ — hafıza servisinin kendi denetim panelinin bilgi mimarisi
   ----------------------------------------------------------------------------
   TARAYICI 8888'E ASLA GİTMEZ. Hindsight loopback'te dinler ve `/v1/*` uçları bir
   tenant anahtarı ister; o anahtar A1'de 0600 bir dosyada durur. Tarayıcıyı oraya
   bağlamanın iki yolu olurdu — portu dışarı açmak ya da anahtarı panoya indirmek —
   ve ikisi de bütün hafızayı bir XSS'in menziline sokardı. Bu sayfanın okuduğu TEK
   yer `api.py`nin hafıza vekilidir: sunucu okur, maskeler, anahtarsız bir gövde
   döner.

   YAZMA YOLU YOK. Vekilin yirmi iki ucundan yirmi biri salt-okunur GET; tek
   istisna `recall`dır ve o da bir SORGUdur (durum değiştirmez, gövdesi beyaz
   listeyle süzülür). Hafızaya yazan/silen/düzelten fiillerin bu panoda karşılığı
   YOKTUR. Düğmeleri GİZLEMİYORUZ (`parcalar.tsx::Faz2Grup` şerhi): görünür ama
   devre dışı duruyorlar, çünkü "böyle bir yetenek yok" ile "yetenek var, bu
   panodan kullanılamıyor" iki ayrı cümledir.

   ---------------------------------------------------------------------------
   NEDEN SEKİZ GÖRÜNÜM — VE NEDEN BU SIRA
   ---------------------------------------------------------------------------
   Bu sayfa DÖRT bölümlü tek bir kaydırma sütunuydu. Yeni hâli, hafıza servisinin
   KENDİ denetim yüzeyinin bilgi mimarisidir: sekiz görünüm ve o yüzeyin
   `sidebar.tsx` dosyasından okunan SIRA (gerekçe `gorunumler.ts`).

   AMA GEZİNME KABI PANONUNKİDİR — VE BU BİR OPERATÖR KARARIDIR (2026-09-02,
   dağıtım sonrası ekran görüntüsü). İlk hâlde sekiz durak bu sayfanın İÇİNDE,
   solda ikinci bir kenar çubuğunda duruyordu ve küresel sol nav da aynı sekizi
   asıyordu — çift gezinme. Ara çözüm küresel çubuğu susturmuştu; operatör
   TERSİNİ seçti: "alt başlıklar sol nav'da, Hafıza'nın altında; sağdaki ikinci
   sütun tamamen kalkar". Yüzey içi kenar çubuğu bu yüzden YOK ve bu sayfa artık
   panonun on beş yüzeyiyle aynı kalıpta: gezinme solda, gövde tek sütun.

   Kazanç: aynı servisi iki yerde tanıyan bir operatör aynı SIRAYI bulur, ve
   panonun her sayfasında olduğu gibi "neredeyim" sorusunun tek bir cevabı olur.
   Bedel, ve açıkça yazılı: BİR EKRANDA HEPSİNİ GÖRME hâli kayboldu — eski sayfa
   dört bloğu alt alta çiziyordu, yenisinde her seferinde bir görünüm var. Bu,
   birebirleştirmenin bilinçli olarak ödenen bedeli.

   ---------------------------------------------------------------------------
   AÇIK GÖRÜNÜM ADRESTEN TÜRER — İLK YAZIM ONU YEREL DURUMDA TUTUYORDU
   ---------------------------------------------------------------------------
   Hangi görünümün açık olduğu ayrı bir durum değişkeninde değil, PANONUN KENDİ
   adresinde yaşıyor: `#/dashboard/memory/<bölüm>`. Görünüm o adresten türetilir;
   ikinci bir kopya yoktur, dolayısıyla ayrışacak bir kopya da yoktur.

   İLK YAZIM YEREL DURUM TUTUYORDU, ölçülen sonucu şuydu (inceleme bulgusu I-4):
   panonun KÜRESEL kenar çubuğu etkin alt maddeyi adresten okuyor, yüzey içi çubuk
   ise adresi hiç yazmıyordu. Üç adımda ayrışıyorlardı — (1) küresel çubuktan
   "Belgeler", iki taraf uyumlu; (2) yüzey içi çubuktan "Bellekler", gövde
   değişiyor ama küresel çubuk hâlâ "Belgeler"i vurguluyor; (3) operatör vurgulanan
   "Belgeler"e basıyor, adres zaten o olduğu için HİÇBİR ŞEY olmuyor. İki gezinme
   "neredesin" sorusuna iki ayrı cevap veriyor, bağ bozuk görünüyordu.

   O ayrışma artık YAPISAL OLARAK İMKÂNSIZ: ikinci çubuk kalktı, geriye tek
   gezinme kaldı ve o da adresi yazan taraf. Adres hâlâ tek kaynak — görünüm
   ondan türer, paletin derin bağları (`komutlar.ts`, aynı adres biçimi) da onu
   seçer.

   BEDEL ÖLÇÜLDÜ VE ÖDENDİ: artık her görünüm değişimi bir tarayıcı geçmişi
   girdisi doğuruyor, yani "geri" önceki sayfaya değil önceki görünüme dönüyor.
   Kaybedilen, sayfadan tek adımda çıkabilmek. Karşılığında panonun geri kalanıyla
   aynı kural geçerli: nerede olduğunu adres söyler.

   ---------------------------------------------------------------------------
   KADANS — EMSALDEN ÖLÇÜLDÜ, TAHMİN EDİLMEDİ
   ---------------------------------------------------------------------------
   Toplu uç 30 sn'de bir yoklanır (`NABIZ_MS * 2`, `KapiYuzey.tsx` emsali) ve
   gerekçesi bu uçta DAHA güçlü: uç banka başına üç çağrı yapar, önbelleği yoktur
   ve banka sayısına TAVAN YOKTUR. Panonun 15 sn'lik nabzıyla sormak bu maliyeti
   ikiye katlar, karşılığında hiçbir yeni bilgi getirmezdi.

   GÖRÜNÜMLERİN KENDİ OKUMALARI YOKLANMAZ ve bu bilinçli bir AYRIMDIR: hepsi
   gezinmeyle tetiklenen okumalardır. Sayfalanmış bir listeyi otuz saniyede bir
   yeniden çekmek, operatör satırları okurken altındaki tabloyu değiştirirdi.

   AÇIK RİSK (uydurma yasağı — çözülmüş gibi yazılmıyor): bugün iki banka var
   (ölçüldü 2026-09-02). Bot bankaları doğduğunda üç-çarpı-N çağrı 30 sn'lik
   yoklamanın altında kalmayabilir. Buraya bir tavan YAZILMADI çünkü ölçülmemiş
   bir eşik, ölçülmüş bir sayı gibi okunurdu; bu satır o günü BEKLEYEN kayıttır.
   ============================================================================ */
import { useEffect, useState, type ComponentType } from "react";
import { Brain } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { YUZEYLER } from "../../alanlar";
import { useRota } from "../../rota";
import { NABIZ_MS, useApi, type Durum } from "../../veri";
import { Olculemedi } from "../sistem/parcalar";
import { AnaSayfa } from "./AnaSayfa";
import { Bellekler } from "./Bellekler";
import { Belgeler } from "./Belgeler";
import { BilgiTabani } from "./BilgiTabani";
import { Recall } from "./Recall";
import { Reflect } from "./Reflect";
import { Varliklar } from "./Varliklar";
import { Yapilandirma } from "./Yapilandirma";
import {
  VARSAYILAN_GORUNUM,
  bolumKaydi,
  gorunumCoz,
  type GorunumOzellikleri,
  type HafizaGorunumu,
} from "./gorunumler";
import { sayi, sozluk } from "./parcalar";
import type { HafizaGovdesi } from "./uctipleri";

const UC = "/api/hindsight";

/* GÖVDE TABLOSU AÇIK VE EKSİKSİZ (`Yuzey.tsx` deseni ve aynı gerekçe): sekiz
   görünümün hepsi burada adıyla var ve hiçbiri sessiz bir yedeğe düşmüyor.
   `Record<HafizaGorunumu, …>` tipi derleme anında zorluyor — `gorunumler.ts`e
   yeni bir görünüm eklendiğinde burası da yazılmadan derleme GEÇMEZ. Sessiz
   yedek olsaydı UNUTULAN bir görünüm ile BİLEREK ertelenmiş bir görünüm ekranda
   aynı görünürdü. */
const GOVDELER: Record<HafizaGorunumu, ComponentType<GorunumOzellikleri>> = {
  "hafiza-anasayfa": AnaSayfa,
  "hafiza-bellekler": Bellekler,
  "hafiza-bilgi": BilgiTabani,
  "hafiza-recall": Recall,
  "hafiza-reflect": Reflect,
  "hafiza-belgeler": Belgeler,
  "hafiza-varliklar": Varliklar,
  "hafiza-yapilandirma": Yapilandirma,
};

/** Banka kimliklerini gövdeden çıkarır — kimliksiz satır sayılmaz, uydurulmaz. */
function bankaKimlikleri(g: HafizaGovdesi | null): readonly string[] {
  return (g?.bankalar ?? []).map((b) => b.bank_id).filter((k): k is string => typeof k === "string" && k.length > 0);
}

/**
 * BANKA SEÇİCİ — ve seçicide GÖRÜNMEYEN şeyin gerekçesi.
 *
 * Hafıza servisinin kendi seçicisi her satırda bir kayıt sayacı çubuğu ve son
 * yazım zamanı gösteriyor; o alanlar banka LİSTESİ gövdesinde geliyor ama vekil
 * listeden yalnız kimliği alıp gerisini düşürüyor (gerekçe `uctipleri.ts`
 * içindeki bedel beyanı). Buradaki satır bu yüzden kimliği ve — ayrı çağrıdan
 * gelen sayaçlar okunabildiyse — kayıt sayısını taşır. Sayaç gelmediyse sayı
 * UYDURULMAZ, satır yalnız kimlikle çizilir.
 */
function BankaSecici({
  durum,
  aktif,
  sec,
}: {
  readonly durum: Durum<HafizaGovdesi>;
  readonly aktif: string | null;
  readonly sec: (b: string) => void;
}) {
  const g = durum.veri;
  const bankalar = bankaKimlikleri(g);
  const sayac = (kimlik: string): number | null => {
    const b = (g?.bankalar ?? []).find((x) => x.bank_id === kimlik);
    const s = sozluk(b?.stats);
    return s === null ? null : sayi(s.total_nodes);
  };

  if (durum.veri === null && durum.hata === null && !durum.oturumDustu) {
    return <span className="text-muted-foreground text-sm">Bankalar okunuyor…</span>;
  }
  if (durum.oturumDustu) {
    return <Olculemedi neden="Oturum düştü" teknik="banka listesi 401 döndü — çaresi yeniden giriş" kisa />;
  }
  if (durum.hata !== null) {
    return <Olculemedi neden="Banka listesi okunamadı" teknik={durum.hata} kisa />;
  }
  if (g?.bankalar === undefined) {
    return <Olculemedi neden="Bankalar bildirilmedi" teknik="uç banka listesi alanını döndürmedi" kisa />;
  }
  if (g.bankalar_neden) {
    /* ÖLÇÜLEMEDİ — boş liste burada bir ölçüm SONUCU değil, bir ölçüm YOKLUĞU.
       Bu makinede anahtar dosyası yok, yani normal hâl budur ve "banka yok"
       diye çizen bir ekran her gün yalan söylerdi. */
    return <Olculemedi neden="Bankalar okunamadı" teknik={g.bankalar_neden} kisa />;
  }
  if (bankalar.length === 0) {
    return <span className="text-muted-foreground text-sm">Banka listesi okundu ve tanımlı banka YOK</span>;
  }

  return (
    <Select value={aktif ?? ""} onValueChange={sec}>
      <SelectTrigger className="w-64" aria-label="Hafıza bankası seç">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {bankalar.map((b) => {
          const n = sayac(b);
          return (
            <SelectItem key={b} value={b}>
              <span className="flex w-full items-center justify-between gap-3">
                <span className="truncate">{b}</span>
                {n !== null ? (
                  <span className="text-muted-foreground text-xs tabular-nums">{n.toLocaleString("tr-TR")}</span>
                ) : null}
              </span>
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}

/* --------------------------------------------------------------------------- */

export function HafizaYuzey() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR (KapiYuzey deseni): `alanlar.ts` bu yüzeyin başlığını ve
  // cevapladığı SORUYU tek yerde tutuyor. İkinci kez yazsaydık kayıt değiştiğinde
  // ekran sessizce eski soruyu sormaya devam ederdi.
  const y = YUZEYLER.memory;
  const hafiza = useApi<HafizaGovdesi>(UC, NABIZ_MS * 2);

  const [secilenBanka, setSecilenBanka] = useState<string | null>(null);

  /* GÖRÜNÜM ADRESTEN TÜRER, KOPYALANMAZ (dosya başlığındaki şerh). Tanınmayan
     bölüm varsayılana düşer — yüzeyin adressiz ilk açılışıyla AYNI hâl. */
  const gorunum = gorunumCoz(bolum) ?? VARSAYILAN_GORUNUM;
  /* GÖRÜNÜME GİDEN BAĞLARI ARTIK BU SAYFA ÜRETMİYOR: küresel sol gezinme
     üretiyor (`gezinme.ts`, `alanlar.ts` kaydından). Burada ikinci bir üretici
     tutmak, aynı adresin iki yerde kurulması demekti. */

  /* GÖRÜNÜM DEĞİŞİNCE BAŞA DÖN: eski sayfa tek bir kaydırma sütunuydu ve derin bağ
     çapaya kaydırıyordu; yenisinde görünümler birbirinin YERİNE geçiyor. Kaydırma
     konumunu korumak, kısa bir görünümden uzun birine geçen operatörü yeni sayfanın
     ortasında bırakırdı — üstteki başlığı hiç görmeden. */
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [gorunum]);

  /* SEÇİM TÜRETİLİR, KOPYALANMAZ: seçili banka boşken listenin İLKİ kullanılır.
     Bunu bir efektle duruma yazmak, aynı gerçeğin ikinci kopyasını üretirdi —
     banka listesi değiştiğinde kopya bayatlar ve ekran artık var olmayan bir
     bankayı sorar. */
  const bankalar = bankaKimlikleri(hafiza.veri);
  const bank = (secilenBanka !== null && bankalar.includes(secilenBanka) ? secilenBanka : bankalar[0]) ?? null;

  const kayit = bolumKaydi(gorunum);
  const Govde = GOVDELER[gorunum];
  const saglik = hafiza.veri?.saglik;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {/* BAŞLIK AÇIK GÖRÜNÜMÜ DE SÖYLER (2026-09-02): yüzey içi kenar çubuğu
              kalkınca "hangi görünümdeyim" sorusunun tek cevabı sol gezinmenin
              vurgusu kalırdı; sayfanın kendisi de söylemeli. İkon ve ad KAYITTAN
              gelir — ikinci bir başlık listesi tutmak, gezinmedeki adla gövdedeki
              adın sessizce ayrışması demekti. */}
          <h1 className="flex flex-wrap items-center gap-2 font-semibold text-2xl tracking-tight">
            <Brain className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
            {kayit === null ? null : (
              <>
                <span className="text-muted-foreground/50" aria-hidden>
                  /
                </span>
                <kayit.ikon className="size-5 shrink-0 text-muted-foreground" aria-hidden />
                <span>{kayit.baslik}</span>
              </>
            )}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{kayit === null ? y.soru : kayit.soru}</p>
        </div>
        {/* ROZET ŞERİDİ YALNIZ ÖLÇÜLENİ TAŞIR (KapiYuzey kuralı): banka sayısı
            ancak gerekçe BOŞKEN basılır — aksi hâlde o sıfır bir ölçüm değil,
            bir ölçüm yokluğudur ve "0 banka" diye okunurdu. */}
        <div className="flex flex-wrap items-center gap-2">
          {hafiza.veri?.bankalar !== undefined && !hafiza.veri.bankalar_neden ? (
            <Badge variant="outline" className="tabular-nums">
              {hafiza.veri.bankalar.length} banka
            </Badge>
          ) : null}
          {saglik?.surum ? (
            <Badge variant="outline" className="font-mono text-[11px]" title="Hafıza servisinin bildirdiği sürüm">
              v{saglik.surum}
            </Badge>
          ) : null}
          {saglik?.erisilebilir === false ? <Badge variant="destructive">servise ulaşılamadı</Badge> : null}
        </div>
      </div>

      {/* BANKA SEÇİCİ KABUĞUN ÜSTÜNDE ve sekiz görünümün HEPSİNİ birden etkiler:
          her görünüm kendi seçicisini taşısaydı, iki görünüm aynı anda iki farklı
          bankayı gösterebilirdi ve operatör hangisine baktığını ekrandan
          okuyamazdı. */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border p-3">
        <span className="font-medium text-sm">Banka</span>
        <BankaSecici durum={hafiza} aktif={bank} sec={setSecilenBanka} />
        {saglik?.neden ? <span className="text-destructive text-xs">{saglik.neden}</span> : null}
      </div>

      {/* TEK SÜTUN: görünüm SEÇİCİSİ ARTIK BU SAYFADA DEĞİL, küresel sol
          gezinmede (operatör kararı 2026-09-02). Burada bir kenar çubuğu daha
          çizmek, aynı sekiz durağı ikinci kez asmak olurdu. */}
      <div className="flex min-w-0 flex-col gap-4">
        {kayit === null ? (
          <Olculemedi
            neden="Bu görünüm yüzey kaydında bulunamadı"
            teknik={`${gorunum} kimliği yüzey kaydından düşmüş — gezinme ve ekran ayrışmış olabilir`}
          />
        ) : (
          <Govde bank={bank} kayit={kayit} toplu={hafiza} />
        )}
      </div>
    </div>
  );
}
