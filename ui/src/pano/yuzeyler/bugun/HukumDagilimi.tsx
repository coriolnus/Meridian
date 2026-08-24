"use client";

/* ============================================================================
   HÜKÜM DAĞILIMI → SEÇİMİN HUNİSİ — kapının o seans ne dediği
   ----------------------------------------------------------------------------
   Kaynak `/api/today.verdict_counts`: `analytics.today()` (analytics.py:259)
   günün planlarını `gate_verdict` alanına göre sayar ve alanı olmayan planı `"?"`
   kovasına koyar. Yani `"?"` bir hata değil, ÖLÇÜLMÜŞ bir kova.

   NEDEN ARTIK HUNİ — VE DAĞILIMIN NEDEN HUNİ ÇİZİLEMEDİĞİ: operatör Karar
   zincirindeki huniyi beğendi ve bu kartın da huni olmasını istedi. AMA hüküm
   dağılımı bir BÖLÜŞÜMdür: REVIEW ile NO_GO kardeştir, biri ötekinin İÇİNDEN
   GEÇMEZ. Kovaları doğrudan huniye dizmek "NO_GO, REVIEW'ün alt kümesidir" diye
   okunurdu — grafik veriyi YANLIŞ anlatırdı. Bu yüzden aynı sayılardan GERÇEKTEN
   iç içe olan sıra çıkarıldı:

       Kurulan plan (N)  →  Kapıyı geçen / NO_GO değil (N − NO_GO)  →  GO

   Üçü gerçekten alt küme zinciridir: her GO aynı zamanda "NO_GO değil"dir, her
   "NO_GO değil" bir plandır. Bölüşümün kendisi (NO_GO / REVIEW / GO / "?")
   SİLİNMEDİ — huninin altındaki "Nerede, neden elendi" satırlarına taşındı,
   çünkü operatör o kırılımı kullanıyor.

   İKİNCİ BASAMAĞIN DÜRÜST ADI: "kapıyı geçen" DEĞİL, "NO_GO DEĞİL". Hükmü hiç
   yazılmamış (`"?"`) bir plan da bu basamakta durur ve onun kapıdan geçtiği
   ÖLÇÜLMEDİ. Fark aşağıdaki düşüş satırında adıyla yazılıyor.

   PAYDA TEK: üç basamak da `verdict_counts` SAYACININ toplamından türüyor.
   `todays_plans` uzunluğu tabana KARIŞTIRILMADI — iki farklı defteri tek orana
   toplamak bu deponun adı konmuş kusuru. O sayı yalnız ÇAPRAZ DENETİMDE
   kullanılıyor (aşağıdaki ayrışma şeridi).

   BOŞ GÖVDE "HER ŞEY YOLUNDA" DEĞİLDİR: `verdict_counts` YOKSA ölçülemedi denir;
   `{}` ise "bu seansta hüküm verilmiş plan yok" denir. GO = 0 ise huni son
   basamakta sıfıra iner ve bu DOĞRU bir okumadır, "veri yok" değil.
   ============================================================================ */
import { useMemo } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { Huni, SeansUzlasmasi, type HuniBasamagi, type HuniDususu, type HuniKarsiKart } from "../kanban/Huni";
import { Olculemedi, bicimSayi } from "./ortak";
import type { BugunTam } from "./tipler";

/** Bu kartın SEANS KAYNAĞI — günün plan defteri. Tek satırda beyan edilir çünkü
 *  kardeş kart (Karar zinciri hunisi) BAŞKA bir defterden sayıyor ve ikisi farklı
 *  seansı anlatabilir. */
const KAYNAK = "günün plan defteri (`/api/today.verdict_counts`)";
const KARSI_KAYNAK = "döngünün kendi kaydı (`events.jsonl` · `daily_cycle`)";

/** Bilinen kovalar. Listede OLMAYAN bir hüküm (uç yeni bir kova açarsa)
 *  yutulmaz — "NO_GO değil" basamağının içinde kalır ve düşüş satırında ADIYLA
 *  yazılır. Bilinmeyen bir kovayı sessizce elemek, ölçülmüş bir planı ekrandan
 *  silmek olurdu. */
const BILINEN = ["GO", "REVIEW", "NO_GO", "?"] as const;

export function HukumDagilimi({ b }: { b: BugunTam }) {
  const sayimlar = b.verdict_counts;

  /** KARDEŞ KARTIN DAMGASI — aynı gövdeden okunuyor (`/api/today.son_dongu`),
   *  yani ikinci bir istek yok. Karar zinciri hunisi sayılarını o bloktan alır;
   *  damgası burada görünmezse okuyucu iki kartı karşılaştıramaz. */
  const karsi: HuniKarsiKart = useMemo(() => {
    const sd = b.son_dongu;
    const damga = typeof sd?.date === "string" && sd.date.trim() !== "" ? sd.date : null;
    return {
      ad: "Karar zinciri · Gece ne buldu",
      damga,
      neden:
        sd === undefined
          ? "`/api/today` gövdesinde `son_dongu` bloğu yok"
          : sd.var === false
            ? (sd.neden ?? "`son_dongu.var` false ama `neden` alanı yazılmamış")
            : "`son_dongu` bloğunda `date` alanı yok — döngü kaydının seansı okunamadı",
      kaynak: KARSI_KAYNAK,
    };
  }, [b.son_dongu]);

  /** UNDEFINED İLE NULL AYRI CÜMLE (tipler.ts'in kuralı): alan hiç gelmediyse
   *  "uç bunu göndermiyor", null geldiyse "defterde tarihli satır yok". İkisini
   *  tek metne toplamak operatörü yanlış yere bakmaya gönderir. */
  const damga = b.todays_plan_date ?? null;
  const damgaNeden =
    b.todays_plan_date === undefined
      ? "`/api/today` gövdesinde `todays_plan_date` alanı YOK — bu uç sürümü göndermiyor"
      : "`todays_plan_date` null — plan defterinde TARİHLİ satır yok (bu 'sıfır plan' DEĞİL)";

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="leading-none">Hüküm dağılımı</CardTitle>
        <CardDescription>Kurulan plandan GO'ya: kaç tanesi sağ çıktı?</CardDescription>
      </CardHeader>
      <CardContent>
        {sayimlar === undefined ? (
          <Olculemedi neden="`/api/today` gövdesinde `verdict_counts` alanı yok" />
        ) : (
          <Icerik
            sayimlar={sayimlar}
            planN={b.todays_plans?.length}
            damga={damga}
            damgaNeden={damgaNeden}
            karsi={karsi}
          />
        )}
      </CardContent>
    </Card>
  );
}

function Icerik({
  sayimlar,
  planN,
  damga,
  damgaNeden,
  karsi,
}: {
  sayimlar: Readonly<Record<string, number>>;
  planN: number | undefined;
  damga: string | null;
  damgaNeden: string;
  karsi: HuniKarsiKart;
}) {
  const seans = useMemo(
    () => ({ damga, neden: damgaNeden, kaynak: KAYNAK }),
    [damga, damgaNeden],
  );

  /** MEMO ŞART (ortak kural): bu kart 15 sn'de bir yeniden çiziliyor; her turda
   *  yeni dizi doğurmak alt bileşenin bütün türetmelerini boşuna tazelerdi. */
  const model = useMemo(() => {
    const no_go = sayimlar["NO_GO"] ?? 0;
    const review = sayimlar["REVIEW"] ?? 0;
    const go = sayimlar["GO"] ?? 0;
    const hukumsuz = sayimlar["?"] ?? 0;
    // BİLİNMEYEN KOVALAR: adıyla toplanır, yutulmaz.
    const diger = Object.entries(sayimlar).filter(
      ([k]) => !(BILINEN as readonly string[]).includes(k),
    );
    const digerN = diger.reduce((a, [, v]) => a + v, 0);
    const toplam = Object.values(sayimlar).reduce((a, v) => a + v, 0);
    const gecen = toplam - no_go;

    const basamaklar: HuniBasamagi[] = [
      { ad: "Kurulan plan", n: toplam },
      { ad: "NO_GO değil", n: gecen },
      { ad: "GO", n: go },
    ];

    // GO OLMAYANIN KIRILIMI — bölüşüm bilgisi burada yaşıyor.
    const kalanParcalar: string[] = [];
    if (review > 0) kalanParcalar.push(`${bicimSayi(review)} REVIEW`);
    if (hukumsuz > 0) kalanParcalar.push(`${bicimSayi(hukumsuz)} hükümsüz (?)`);
    for (const [k, v] of diger) kalanParcalar.push(`${bicimSayi(v)} ${k}`);

    const dususler: HuniDususu[] = [
      {
        ok: "Kurulan plan → NO_GO değil",
        metin:
          no_go > 0
            ? `${bicimSayi(no_go)} plan kapıda takıldı · kapı: ${bicimSayi(no_go)} NO_GO`
            : "kapıda takılan yok · 0 NO_GO",
        oran: toplam > 0 ? no_go / toplam : null,
        neden: "payda ölçülemedi — sayaç toplamı 0",
      },
      {
        ok: "NO_GO değil → GO",
        // ÜÇ AYRI CÜMLE, TEK "eriyen yok" DEĞİL: geçen küme BOŞken "hepsi GO oldu"
        // yazmak düpedüz yanlıştı (hepsi NO_GO iken de eriyen 0 çıkıyor) — sıfırın
        // iki farklı anlamı var ve ekranda ayrılmak zorunda.
        metin:
          gecen === 0
            ? "NO_GO değil basamağı boş — eriyecek plan kalmamıştı"
            : gecen - go > 0
              ? `${bicimSayi(gecen - go)} plan GO olmadı · ${kalanParcalar.join(" · ")}`
              : "geçenlerin hepsi GO oldu",
        oran: toplam > 0 ? (gecen - go) / toplam : null,
        neden: "payda ölçülemedi — sayaç toplamı 0",
      },
    ];

    // YALNIZ EKRANDA OKUYUCUSU OLAN ALANLAR DÖNER (YASA 6): `no_go`/`review`/`go`
    // düşüş satırlarının metnine zaten girdi; ikinci kez taşımak, bir sonraki
    // düzenlemede iki kaynaktan iki farklı sayı okunması riskidir.
    return { toplam, hukumsuz, digerN, basamaklar, dususler };
  }, [sayimlar]);

  /** SAYAÇ BOŞ: "ölçtük, sıfır çıktı" — ölçülemedi DEĞİL. Huni çizilmez çünkü
   *  payda yok (0 tabanlı bir oran uydurma olurdu), ama iki kartın damgası yine
   *  de yan yana durur: karşılaştırma sorusu sayaç boşken de geçerli. */
  if (model.toplam === 0) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-muted-foreground text-sm">
          Bu seansta hüküm verilmiş plan yok — sayaç boş döndü (ölçüldü, bilgi eksikliği değil). Huni
          çizilmedi: payda 0, oran uydurulamaz.
          {planN !== undefined && planN > 0
            ? ` DİKKAT: aynı gövdede ${bicimSayi(planN)} plan var; sayaç ile liste ayrışıyor.`
            : null}
        </p>
        <SeansUzlasmasi seans={seans} karsi={karsi} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <Huni
        basamaklar={model.basamaklar}
        dususler={model.dususler}
        seans={seans}
        karsi={karsi}
        paydaBeyani={`Payda: ${KAYNAK} sayacının TOPLAMI (${bicimSayi(model.toplam)} plan) — döngü kaydından sayılmadı.`}
      />

      {/* İKİNCİ BASAMAĞIN SINIRI: "NO_GO değil" ile "kapıdan geçti" AYNI ŞEY DEĞİL. */}
      {model.hukumsuz > 0 ? (
        <p className="text-muted-foreground text-xs leading-5">
          İkinci basamak "NO_GO DEĞİL" demektir, "kapıdan geçti" demez: içinde hükmü hiç yazılmamış{" "}
          {bicimSayi(model.hukumsuz)} plan var (`gate_verdict` alanı yok) — onların kapıdan geçtiği
          ölçülmedi.
        </p>
      ) : null}

      {model.digerN > 0 ? (
        <p className="text-muted-foreground text-xs leading-5">
          Sayaçta bu panonun tanımadığı kova(lar) var ({bicimSayi(model.digerN)} plan) — yutulmadılar,
          düşüş satırında adlarıyla yazıldılar ve "NO_GO değil" basamağının içindeler.
        </p>
      ) : null}

      {planN !== undefined && planN !== model.toplam ? (
        <p className="text-destructive text-xs leading-5">
          Sayaç {bicimSayi(model.toplam)} plan sayıyor, liste {bicimSayi(planN)} plan taşıyor — aynı
          gövdede iki farklı cevap. Bu bir ekran hatası değil, gövdenin kendisinde ayrışma. Huninin
          tabanı SAYAÇTIR (tek payda); liste tabana karıştırılmadı.
        </p>
      ) : null}
    </div>
  );
}
