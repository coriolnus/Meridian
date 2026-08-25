"use client";

/* ============================================================================
   KRİZ KOLLARI — panonun en yüksek bahisli dört düğmesi, SABİT bir evde
   ----------------------------------------------------------------------------
   NEDEN ÜST BAR VE NEDEN BURASI SABİT: eski panoda şerh aynen şuydu — "HALT'ın
   SABİT bir evi olmak zorunda (kas hafızası)". Acil bir anda operatör düğmeyi
   ARAMAZ; elini gittiği yere götürür. Bu bileşen `Kabuk`un başlığında yaşıyor,
   yani yönlendirilen içeriğin DIŞINDA: sayfa değişince yeniden monte edilmez ve
   yerinden oynamaz.

   YERLEŞİM ÇİVİSİ (görünmez ama kasıtlı): `DEVAM` düğmesi KRİZ'in SOLUNA
   ekleniyor. Üst barın sağ öbeği sağ kenara yaslı; bir öğeyi KRİZ'den önce
   koymak yalnız kendisinden ÖNCEKİLERİ kaydırır, KRİZ ve sağındakiler yerinde
   kalır. Sonradan eklenecek bir kol da bu yüzden soldan eklenir — HALT
   çekildiğinde düğmenin yer değiştirmesi, kas hafızasının tam olarak kaybolma
   biçimidir.

   ÇİFT ADIMIN TEK İŞİ "yanlışlıkla basma"yı önlemek DEĞİL (gramer
   `yuzeyler/kuyruk/KararPaneli.tsx`ten alındı): iki tık arasına OKUNACAK BİR
   CÜMLE koymaktır. O cümle `krizUclari.ts`te uçların GÖVDESİ okunarak kuruldu ve
   Flatten'da sayılar da UÇTAN ölçülüyor (`FlattenKapisi.tsx`).

   İYİMSER GÜNCELLEME YOK: gönderim bittiğinde ekranda görünen her şey UÇTAN GELEN
   GÖVDEDİR. "200 = oldu" bu ailede YANLIŞTIR — `cancel_open` ve `close_all`
   adaptör arızasını 200 içinde `ok:false` olarak taşıyor; hüküm `kolSonucu`da
   alan alan okunuyor.

   HATA HÂLLERİ AYRI VE ADLI: 4xx ucun REDDİ (gerekçe aynen), 401 oturum düşmesi
   (kol ÇEKİLMEDİ — `_auth` gövdeden önce koşar), 0/5xx "ulaştı mı BİLİNMİYOR".
   Bu ayrım her ekranda önemlidir; BU kollarda hayatidir.
   ============================================================================ */
import { useEffect, useState, type ReactNode } from "react";

import { OctagonPause, Play, RefreshCw, Send, Siren, TriangleAlert, Undo2 } from "lucide-react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

import { useBugun } from "../durum";
import { useApi, type Durum } from "../veri";
import { FlattenKapisi } from "./FlattenKapisi";
import {
  KOLLAR,
  kolIstegi,
  kolSonucu,
  krizHatasi,
  krizPost,
  type AlpacaGovdesi,
  type HataMetni,
  type KolKimlik,
  type KolSonucu,
  type TeshisKesiti,
} from "./krizUclari";

type Asama =
  | { readonly ad: "hazir" }
  /** Birinci tık alındı; ikinci tık bekleniyor ve arada cümle OKUNUYOR. */
  | { readonly ad: "teyit"; readonly kol: KolKimlik; readonly learnAc?: boolean }
  | { readonly ad: "gonderiliyor"; readonly kol: KolKimlik; readonly learnAc?: boolean }
  | { readonly ad: "bitti"; readonly kol: KolKimlik; readonly learnAc?: boolean; readonly basarili: boolean };

/** Üç durumlu bayrak rozeti. `undefined` "serbest" DEĞİLDİR — ölçülemedi demektir. */
function HalRozet({ cekili, cekiliMetin }: { readonly cekili: boolean | undefined; readonly cekiliMetin: string }) {
  if (cekili === undefined) {
    return (
      <Badge variant="outline" className="text-[10px] text-muted-foreground">
        hâl ölçülemedi
      </Badge>
    );
  }
  return cekili ? (
    <Badge variant="destructive" className="text-[10px]">
      {cekiliMetin}
    </Badge>
  ) : (
    <Badge variant="outline" className="text-[10px]">
      serbest
    </Badge>
  );
}

function yasMetni(zaman: Date | null): string {
  if (zaman === null) return "hiç okunmadı";
  const sn = Math.max(0, Math.round((Date.now() - zaman.getTime()) / 1000));
  return sn < 90 ? `${sn} sn önce okundu` : `${Math.round(sn / 60)} dk önce okundu`;
}

/* ---- KOL SATIRI — MODÜL DÜZEYİNDE, ve bu bir üslup tercihi DEĞİL -----------
   Bu bileşen önce `KrizKollari`ın İÇİNDE tanımlanmıştı ve derleyici bundan
   şikâyet etmiyordu; kusur çalışma zamanındaydı. İç içe tanımlanan bir bileşenin
   FONKSİYON KİMLİĞİ her render'da değişir, React da onu "başka bir bileşen" sayıp
   ağacı SÖKÜP yeniden kurar. Sonuç: `useBugun` 15 saniyede bir nabız attığı için
   ebeveyn her 15 saniyede yeniden render olur ve `FlattenKapisi` her seferinde
   YENİDEN MONTE OLURDU — operatörün yazdığı `FLATTEN-PAPER` jetonu silinir ve
   kuru koşu POST'u baştan atılırdı. Yani acil bir anda düğme, tam yazarken
   sıfırlanan bir düğme olurdu. Props uzun; sökülmeyen bir ağaç buna değer.
   -------------------------------------------------------------------------- */
function KolSatiri({
  kol,
  rozet,
  dugmeler,
  asama,
  gonderiliyor,
  hata,
  sonuc,
  alpaca,
  onGonder,
  onVazgec,
}: {
  readonly kol: KolKimlik;
  readonly rozet?: ReactNode;
  readonly dugmeler: ReactNode;
  readonly asama: Asama;
  readonly gonderiliyor: boolean;
  readonly hata: HataMetni | null;
  readonly sonuc: KolSonucu | null;
  readonly alpaca: Durum<AlpacaGovdesi>;
  readonly onGonder: (kol: KolKimlik, learnAc?: boolean) => void;
  readonly onVazgec: () => void;
}) {
  const k = KOLLAR[kol];
  const acikKol = asama.ad !== "hazir" && asama.kol === kol;
  return (
    <div className={cn("rounded-md border p-2.5", k.agir && "border-destructive/40")}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-medium text-sm">
              {k.kademe} · {k.ad}
            </span>
            {k.agir ? (
              <Badge variant="destructive" className="text-[10px]">
                GERİ ALINAMAZ
              </Badge>
            ) : k.geriAlinabilir ? null : (
              <Badge variant="outline" className="text-[10px]">
                geri alınamaz
              </Badge>
            )}
            {rozet}
          </div>
          <p className="mt-0.5 text-muted-foreground text-xs leading-5">{k.ozet}</p>
        </div>
        {/* BİR ANDA TEK KOL KURULU: bir kol niyet aldığında TÜM satırların birinci-tık
            düğmeleri kaybolur. İki kol aynı anda kurulu olsaydı ekranda iki "EVET,
            GÖNDER" dururdu ve hangisinin ne göndereceği bakışla ayrılamazdı. */}
        {asama.ad === "hazir" ? <div className="flex shrink-0 flex-wrap gap-1.5">{dugmeler}</div> : null}
      </div>

      {/* ---- İKİ TIK ARASI: NE OLACAĞI YAZILI ---------------------------- */}
      {acikKol && (asama.ad === "teyit" || asama.ad === "gonderiliyor") ? (
        k.agir ? (
          <div className="mt-2.5">
            <FlattenKapisi
              alpaca={alpaca}
              gonderiliyor={gonderiliyor}
              onGonder={() => onGonder(kol)}
              onVazgec={onVazgec}
            />
          </div>
        ) : (
          <div className="mt-2.5 rounded-md border bg-muted/40 p-2.5" aria-live="polite">
            <span className="font-medium text-sm">İkinci tık şunu yapacak</span>
            <p className="mt-1.5 text-sm leading-6">{k.nedir}</p>
            <p className={cn("mt-1 text-xs leading-5", k.geriAlinabilir ? "text-muted-foreground" : "text-destructive")}>
              {k.geriAlmaNotu}
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              <Button
                type="button"
                variant={k.geriAlinabilir ? "default" : "destructive"}
                disabled={gonderiliyor}
                onClick={() => onGonder(kol, asama.learnAc)}
              >
                {gonderiliyor ? <Spinner /> : <Send aria-hidden />}
                {gonderiliyor ? "Gönderiliyor — bekle" : "EVET, GÖNDER"}
              </Button>
              <Button type="button" variant="ghost" disabled={gonderiliyor} onClick={onVazgec}>
                <Undo2 aria-hidden />
                Vazgeç
              </Button>
            </div>
          </div>
        )
      ) : null}

      {/* ---- SONUÇ: UÇTAN GELEN GÖVDE, PANONUN YORUMU DEĞİL -------------- */}
      {acikKol && asama.ad === "bitti" ? (
        <div className="mt-2.5">
          {hata !== null ? (
            <Alert variant="destructive">
              <TriangleAlert />
              <AlertTitle>{hata.baslik}</AlertTitle>
              <AlertDescription>
                <span className="leading-5">{hata.govde}</span>
                {hata.oturumDustu ? (
                  <span className="mt-1 block font-medium">
                    Çare: panodan çık, yeniden gir. Tazelemek bu hâli düzeltmez.
                  </span>
                ) : null}
                {!hata.sonucBiliniyor ? (
                  <span className="mt-1 block font-medium">
                    SONUÇ BİLİNMİYOR: körlemesine tekrar gönderme, önce durumu ölç.
                  </span>
                ) : null}
              </AlertDescription>
            </Alert>
          ) : sonuc !== null ? (
            <Alert variant={sonuc.basarili ? "default" : "destructive"}>
              {sonuc.basarili ? <Send /> : <TriangleAlert />}
              <AlertTitle>{sonuc.baslik}</AlertTitle>
              <AlertDescription>
                {/* ANAHTAR SIRA NUMARASI: satırlar uçtan gelen METİNLER ve iki satırın
                    aynı cümleyi taşıması mümkün (ör. iki kez "uç `detail` yazmadı").
                    Metni anahtar yapmak o durumda çakışırdı; liste statik ve hiç
                    yeniden sıralanmıyor, sıra numarası burada doğru anahtardır. */}
                <ul className="mt-0.5 list-disc space-y-0.5 pl-4 leading-5">
                  {sonuc.satirlar.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          ) : null}
          <Button type="button" variant="ghost" size="sm" className="mt-2" onClick={onVazgec}>
            <Undo2 aria-hidden />
            Kollara dön
          </Button>
        </div>
      ) : null}
    </div>
  );
}

export function KrizKollari() {
  const bugun = useBugun();
  const [acik, setAcik] = useState(false);
  const [asama, setAsama] = useState<Asama>({ ad: "hazir" });
  const [sonuc, setSonuc] = useState<KolSonucu | null>(null);
  const [hata, setHata] = useState<HataMetni | null>(null);

  // İKİ OKUMA TEMBEL VE NABIZSIZ: `/api/alpaca` broker'a üç HTTP çağrısı yapıyor,
  // `/api/diagnostics` 45 sn önbellekli ama yine de ağır. Üst bar bunları HER sayfada
  // 15 sn'de bir çekseydi, kapalı bir panel için sürekli broker trafiği üretirdik.
  // `useApi(null)` hiç istek atmaz; panel açılınca yol dolar ve bir kez okunur.
  const alpaca = useApi<AlpacaGovdesi>(acik ? "/api/alpaca" : null);
  const teshis = useApi<TeshisKesiti>(acik ? "/api/diagnostics" : null);

  const halted = bugun.veri?.halted;
  // ÇAPRAZ OKUMA, ÇAPRAZ UYDURMA DEĞİL: `risk.learn_halted` ve `hud.learn_halted` aynı
  // `health.learn_halted()`u okur (api.py:4632 / 4561). İlki yoksa ikincisi denenir;
  // ikisi de yoksa `undefined` KALIR — "serbest"e çevrilmez.
  const learnHalted = teshis.veri?.risk?.learn_halted ?? teshis.veri?.hud?.learn_halted;

  // PANEL KAPANINCA HER ŞEY SIFIRLANIR: yarım kalmış bir "teyit" hâli, panel yeniden
  // açıldığında operatörün başlatmadığı bir niyeti hazır bekletirdi.
  useEffect(() => {
    if (!acik) {
      setAsama({ ad: "hazir" });
      setSonuc(null);
      setHata(null);
    }
  }, [acik]);

  const gonderiliyor = asama.ad === "gonderiliyor";

  async function gonder(kol: KolKimlik, learnAc?: boolean) {
    setAsama({ ad: "gonderiliyor", kol, learnAc });
    setHata(null);
    setSonuc(null);
    const { yol, govde } = kolIstegi(kol, learnAc);
    const s = await krizPost(yol, govde);
    if (!s.ok) {
      const h = krizHatasi(s, yol, KOLLAR[kol]);
      setHata(h);
      setAsama({ ad: "bitti", kol, learnAc, basarili: false });
      toast.error(h.baslik, { description: h.govde });
      return;
    }
    const r = kolSonucu(kol, s.govde, learnAc);
    setSonuc(r);
    setAsama({ ad: "bitti", kol, learnAc, basarili: r.basarili });
    const ilk = r.satirlar[0] ?? "";
    if (r.basarili) toast.success(r.baslik, { description: ilk });
    else toast.error(r.baslik, { description: ilk });
    // YENİDEN ÖLÇÜM, İYİMSER GÜNCELLEME DEĞİL: üç kaynak da yeniden okunur. Uçlar
    // `_diag_onbellek_bosalt` çağırdığı için teşhis önbelleği bu noktada zaten düşmüş olur.
    bugun.tazele();
    teshis.tazele();
    alpaca.tazele();
  }

  /* Beş satırın PAYLAŞTIĞI props tek yerde kurulur. Tek tek yazılsalardı bir satırda
     `sonuc` unutulur ve o kolun sonucu SESSİZCE görünmez olurdu — bu ailede
     "gönderdim ama cevabı göremedim" en pahalı kusur. */
  const ortak = {
    asama,
    gonderiliyor,
    hata,
    sonuc,
    alpaca,
    onGonder: (kol: KolKimlik, learnAc?: boolean) => void gonder(kol, learnAc),
    onVazgec: () => setAsama({ ad: "hazir" }),
  };

  return (
    <>
      {/* DEVAM DÜĞMESİ KRİZ'İN SOLUNDA: HALT çekiliyken geri alma yolu üst barın
          KENDİSİNDE olmalı (turun şartı) — bir menünün içinde değil. Sağ öbek sağa
          yaslı olduğu için soldan eklemek KRİZ'i yerinden oynatmaz. */}
      {halted === true ? (
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="shrink-0 border-destructive/50 text-destructive"
          title="HALT çekili — `POST /api/resume` ile kaldır"
          onClick={() => {
            setAsama({ ad: "teyit", kol: "resume" });
            setAcik(true);
          }}
        >
          <Play aria-hidden />
          DEVAM
        </Button>
      ) : null}

      <Dialog
        open={acik}
        onOpenChange={(a) => {
          // GÖNDERİM SIRASINDA KAPANMAZ: uçuş hâlindeki bir icra emrini ekrandan silmek,
          // sonucu hiç okumamak demektir.
          if (gonderiliyor) return;
          setAcik(a);
        }}
      >
        <DialogTrigger asChild>
          <Button
            type="button"
            variant={halted === true ? "destructive" : "outline"}
            size="sm"
            className="shrink-0"
            title="Müdahale kolları — Soft Halt · Cancel-Open · Flatten · Halt Learning"
          >
            <Siren aria-hidden />
            KRİZ
          </Button>
        </DialogTrigger>

        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Siren className="size-4" aria-hidden />
              Müdahale kolları
            </DialogTitle>
            <DialogDescription>
              Dört kademe, artan sertlikte. Her kol ÇİFT ADIMLI: birinci tık niyeti alır, ikinci tıktan önce
              ne olacağı yazılı durur. Sonuç uçtan gelen gövdeyle bildirilir — pano hiçbir şeyi &quot;olmuş
              sayar&quot; diye çizmez.
            </DialogDescription>
          </DialogHeader>

          {/* ---- ÖLÇÜLEN HÂL, EN ÜSTTE ------------------------------------- */}
          <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 px-2.5 py-2 text-xs">
            <span className="text-muted-foreground">Ölçülen hâl:</span>
            {bugun.oturumDustu ? (
              <span className="font-medium text-destructive">oturum düştü — hiçbir kolun hâli okunamıyor</span>
            ) : halted === undefined ? (
              <span className="text-muted-foreground italic">
                HALT ölçülemedi — {bugun.hata ?? "`/api/today` `halted` alanını yazmadı"}
              </span>
            ) : halted ? (
              <span className="font-medium text-destructive">HALT ÇEKİLİ — yeni giriş durmuş durumda</span>
            ) : (
              <span className="font-medium">HALT serbest — sistem yeni giriş alabilir</span>
            )}
            <span className="text-muted-foreground">
              (<code className="font-mono">/api/today</code>, {yasMetni(bugun.zaman)})
            </span>
            <Button
              type="button"
              variant="ghost"
              size="xs"
              className="ml-auto"
              disabled={gonderiliyor}
              onClick={() => {
                bugun.tazele();
                teshis.tazele();
                alpaca.tazele();
              }}
            >
              <RefreshCw aria-hidden />
              yeniden ölç
            </Button>
          </div>

          <div className="flex flex-col gap-2">
            {/* ---- KADEME 1 -------------------------------------------------
                ÜÇ HÂL, ÜÇ AYRI YERLEŞİM — ve `undefined` dalı bir kusurun düzeltmesi:
                önce tek bir `soft_halt` satırı çizilip içine bir "DEVAM et…" düğmesi
                konmuştu. Düğme `resume` niyetini kuruyordu ama ekranda `resume`
                satırı YOKTU, yani teyit bloğu HİÇBİR YERDE görünmüyordu: operatör
                tıklıyor, hiçbir şey olmuyordu. Ölçülemeyen hâlde iki yön İKİ AYRI
                SATIRDIR — her niyetin görünecek bir evi olur.

                Tek bir "tersini yap" düğmesi zaten yazılamazdı: etiketi okunamayan
                bir hâlden TAHMİN edilirdi ve tahmin yanlışsa operatör durdurmak
                isterken sistemi devam ettirirdi. */}
            {halted === true ? (
              <KolSatiri
                {...ortak}
                kol="resume"
                rozet={<HalRozet cekili={halted} cekiliMetin="ÇEKİLİ" />}
                dugmeler={
                  <Button type="button" size="sm" onClick={() => setAsama({ ad: "teyit", kol: "resume" })}>
                    <Play aria-hidden />
                    DEVAM et…
                  </Button>
                }
              />
            ) : (
              <>
                <KolSatiri
                  {...ortak}
                  kol="soft_halt"
                  rozet={<HalRozet cekili={halted} cekiliMetin="ÇEKİLİ" />}
                  dugmeler={
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => setAsama({ ad: "teyit", kol: "soft_halt" })}
                    >
                      <OctagonPause aria-hidden />
                      Soft Halt…
                    </Button>
                  }
                />
                {halted === undefined ? (
                  <KolSatiri
                    {...ortak}
                    kol="resume"
                    rozet={
                      <Badge variant="outline" className="text-[10px] text-muted-foreground">
                        hâl ölçülemedi — ters yön de açık
                      </Badge>
                    }
                    dugmeler={
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setAsama({ ad: "teyit", kol: "resume" })}
                      >
                        <Play aria-hidden />
                        DEVAM et…
                      </Button>
                    }
                  />
                ) : null}
              </>
            )}

            {/* ---- KADEME 2 --------------------------------------------------- */}
            <KolSatiri
              {...ortak}
              kol="cancel_open"
              rozet={
                <Badge variant="outline" className="text-[10px] text-muted-foreground">
                  anlık eylem
                </Badge>
              }
              dugmeler={
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setAsama({ ad: "teyit", kol: "cancel_open" })}
                >
                  <Send aria-hidden />
                  İptal et…
                </Button>
              }
            />

            {/* ---- KADEME 3 · AYRI SINIF -------------------------------------- */}
            <KolSatiri
              {...ortak}
              kol="flatten"
              rozet={
                <Badge variant="outline" className="text-[10px] text-muted-foreground">
                  ölçüm + jeton ister
                </Badge>
              }
              dugmeler={
                <Button
                  type="button"
                  size="sm"
                  variant="destructive"
                  onClick={() => setAsama({ ad: "teyit", kol: "flatten" })}
                >
                  <TriangleAlert aria-hidden />
                  FLATTEN…
                </Button>
              }
            />

            {/* ---- KADEME 4 --------------------------------------------------- */}
            <KolSatiri
              {...ortak}
              kol="learn_halt"
              rozet={
                teshis.yukleniyor && learnHalted === undefined ? (
                  <Badge variant="outline" className="text-[10px] text-muted-foreground">
                    hâl okunuyor…
                  </Badge>
                ) : (
                  <HalRozet cekili={learnHalted} cekiliMetin="ÇEKİLİ" />
                )
              }
              dugmeler={
                <>
                  {learnHalted !== true ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => setAsama({ ad: "teyit", kol: "learn_halt", learnAc: true })}
                    >
                      <OctagonPause aria-hidden />
                      Ship&apos;i durdur…
                    </Button>
                  ) : null}
                  {learnHalted !== false ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setAsama({ ad: "teyit", kol: "learn_halt", learnAc: false })}
                    >
                      <Play aria-hidden />
                      Kaldır…
                    </Button>
                  ) : null}
                </>
              }
            />
          </div>

          <Separator />
          <p className="text-muted-foreground text-[11px] leading-5">
            Bu kollar eski panodaki <b>KRİZ ⚠</b> kapağının AYNI uçlarına gider — ikinci bir yetki yolu yok.
            Kademe 1 ile üst bardaki HALT tek ve aynı mekanizmadır (<code className="font-mono">state/HALT</code>{" "}
            bayrağı). Kademe 2 ve 3 geri alınamaz.
          </p>
        </DialogContent>
      </Dialog>
    </>
  );
}
