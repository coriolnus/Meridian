"use client";

/* ============================================================================
   OTURUM YÜZEYİ (kabuk içi) — "oturumum açık mı, nasıl çıkarım"
   ----------------------------------------------------------------------------
   KAPSAM DARALDI, TEK CÜMLEYLE: kapı 2026-09-01'de `pano/App.tsx` seviyesine
   çıktığı için bu yüzey ARTIK YALNIZ oturum AÇIKKEN mount ediliyor; işi de o
   kadar — oturumun ölçülen hâlini göstermek ve çıkış kolunu taşımak.

   ÜÇ HÂLLİ MAKİNE BURADAN GİTTİ (düzeltme-2, 2026-09-02). Kapı taşındıktan sonra
   bu dosyada duran kurulum/giriş dalları YAPISAL OLARAK erişilemez hâle gelmişti:
   `App.tsx` kabuğu yalnız `hal === "acik"` iken doğuruyor, yani `Giris` mount
   olduğunda hâl zaten "acik". Bir tur boyunca "yüzeyin dürüstlüğü kapıya BAĞLI
   olmasın" diye bırakıldılar; bu gerekçe yanlıştı — çalışmayan bir yedek, yedek
   değildir. Ölü dal okuyucusuna "burası da olabilir" der ve bir sonraki eli yanlış
   yere bakmaya gönderir. Tarihçesi git'te; makinenin kendisi tek elde:
   sınıflama `pano/oturum.tsx::hali`, ekran gövdeleri `kimlik/KapiEkrani.tsx`.

   ~~YÜZEY KABUĞUN İÇİNDE ÇİZİLİYOR~~ — ÖNCÜLÜ ÖLDÜ (2026-09-01, kapı basic-auth
   emekliliği). Kayıt siliNMEDİ, çünkü kararın NEDEN değiştiğini yalnız eski gerekçe
   gösterir. Eski karar şuydu: "şablonun `h-dvh` tam-ekran auth düzeni BİLEREK
   alınmadı; oturum kapısı uygulamanın ÖNÜNDE değil İÇİNDE bir yüzey — kabuğu
   gizlemek, olmayan bir yönlendirme katmanı varmış gibi göstermek olurdu."
   Dayandığı önerme "pano zaten bir DIŞ kapının (tünel, sonra APISIX basic-auth)
   arkasında" idi. O kapı 2026-09-01'de operatör kararıyla kaldırıldı; tek kimlik
   katmanı artık uygulamanın kendi oturumu ve kimliksiz ziyaretçi uygulamanın İLK
   yüzünü görüyor — ona kabuk değil, tam-ekran kapı çıkıyor.

   ŞABLONDAN NE KALDI: bölünmüş panel (solda `bg-primary` marka rayı, sağda gövde)
   ve `Field*` grameri. Kaynak: `auth/v2/layout`, `auth/_components/*`.

   NABIZ 15 SANİYE ve bu bir israf değil: kayan oturum middleware'i (api.py
   `KayanOturumMiddleware`) ÇEREZLİ HER isteği tazeleme fırsatı sayar, yani bu
   yoklama panonun geri kalanıyla aynı ritimde hem oturumu ayakta tutar hem de
   düşme anını saniyeler içinde ekrana taşır. Nabzın SAHİBİ artık bu yüzey değil
   `OturumSaglayici` — gövde tek yerden çekiliyor ki kapı ile yüzey aynı ANI
   okusun (`durum.tsx`teki `/api/today` gerekçesinin aynısı). Oturum düştüğünde
   bu yüzey bir şey ÇİZMEZ: sağlayıcı hâli "giris"e taşır ve kabuk tümden sökülür.
   ============================================================================ */
import { Fingerprint, LogOut } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";

import { YUZEYLER } from "../alanlar";
import { useOturum } from "../oturum";
import { useRota } from "../rota";
import { KapiKunyesi } from "./kimlik/KapiKunyesi";
import { MarkaRayi } from "./kimlik/MarkaRayi";
import { apiPost, type GonderSonucu } from "./kimlik/gonder";

/* RAYIN ALT BLOĞU YALNIZ BURADA — kabuğun içi, yani kimliği DOĞRULANMIŞ operatör.
   Tam-ekran kapı aynı rayı ayrıntısız çağırıyor (bkz. `MarkaRayi.tsx` başlığı):
   "kullanıcı tablosu yok" bir sistem gerçeğidir ve anonim bir ziyaretçiye
   söylenecek şey değildir.

   SIFIRLAMA KOMUTU EKRANDAN KALKTI (düzeltme-1, 2026-09-01) ve gerekçesi kapıya
   değil İLKEYE dayanıyor: bir yönetim komutu bir ekran öğesi değildir. Operatörün
   gece yarısı ihtiyacı olan bilgi "panodan sıfırlanmaz" — o duruyor; komutun
   kendisi runbook'ta, tek kaynağında. `KurulumFormu.tsx` başlığı da aynı komutu
   şerh olarak taşıyor; şerh ekran metni değildir, orada kalıyor. */
const OPERATOR_AYRINTILARI = [
  {
    baslik: "Tek operatör",
    govde: "Kullanıcı tablosu yok; kapı tek bir parola hash'i tutuyor (meridian/auth.py).",
  },
  {
    baslik: "Parolayı unuttuysan",
    govde: "Panodan sıfırlanmaz. Sıfırlama yordamı sunucu tarafındadır ve runbook'ta yazılıdır.",
  },
] as const;

/** Bölünmüş panel kabı — üç hâlin üçü de bunun içinde çiziliyor. Tam-ekran kapı
 *  AYNI rayı `h-dvh` bir ızgarada kullanıyor; kap farklı, ray tek. */
function Panel({
  marka,
  markaAlt,
  children,
}: {
  readonly marka: string;
  readonly markaAlt: string;
  readonly children: React.ReactNode;
}) {
  return (
    <Card className="gap-0 overflow-hidden p-0">
      <div className="grid lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1fr)]">
        <MarkaRayi baslik={marka} altBaslik={markaAlt} ayrintilar={OPERATOR_AYRINTILARI} />
        <CardContent className="p-6 sm:p-8">{children}</CardContent>
      </div>
    </Card>
  );
}

/* --- OTURUM AÇIKKEN: durum + çıkış ---------------------------------------- */

function OturumAcik({ onCikis }: { readonly onCikis: () => void }) {
  const [gonderiliyor, setGonderiliyor] = useState(false);
  const [sonuc, setSonuc] = useState<GonderSonucu | null>(null);

  async function cikis() {
    setGonderiliyor(true);
    const s = await apiPost("/api/logout");
    setGonderiliyor(false);
    setSonuc(s);
    // BAŞARISIZ ÇIKIŞTA DA TAZELE: `/api/logout` çerezi siler ve yetki aramaz, ama
    // yanıt gövdesi okunamadıysa (proxy düz metin döndürdü) çerezin silinip
    // silinmediğini yalnız `/api/session`ı yeniden sorarak öğrenebiliriz.
    onCikis();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="space-y-1">
        <h2 className="font-medium text-xl">Oturum açık</h2>
        <p className="text-muted-foreground text-sm">
          Bu tarayıcının imzalı çerezi geçerli. Çerez kayan ömürlü: pano her istekle onu tazeliyor
          (api.py <code className="text-[11px]">KayanOturumMiddleware</code>).
        </p>
      </div>

      <Button variant="outline" className="w-full" onClick={cikis} disabled={gonderiliyor}>
        {gonderiliyor ? <Spinner /> : <LogOut className="size-4" aria-hidden />}
        {gonderiliyor ? "Çıkılıyor…" : "Çıkış yap"}
      </Button>

      {sonuc && !sonuc.ok ? (
        <Alert variant="destructive">
          <AlertTitle>Çıkış isteği düştü (HTTP {sonuc.kod})</AlertTitle>
          <AlertDescription>
            {sonuc.detay ?? "sunucu gerekçe metni döndürmedi"} — yukarıdaki oturum satırı çerezin gerçekten silinip
            silinmediğini söyler.
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}

/* --- YÜZEY ---------------------------------------------------------------- */

export function Giris() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR, ELLE YAZILMAZ: `alanlar.ts` bu yüzeyin başlığını ve
  // cevapladığı SORUYU tek yerde tutuyor; ikinci kez yazsaydık kayıt değiştiğinde
  // ekran sessizce eski soruyu sormaya devam ederdi.
  const y = YUZEYLER.authentication;
  // GÖVDE SAĞLAYICIDAN: bu yüzey kendi `useApi("/api/session")`sini AÇMIYOR.
  // Açsaydı kapı ile yüzey iki ayrı nabızda iki ayrı an okurdu — ve aynı ekranda
  // iki farklı gerçek, operatörün hangisine inanacağını bilemediği bir arayüzdür.
  const { durum: oturum, omurS, cikisBildir } = useOturum();

  // DERİN BAĞ KAYDIRMASI — NE HEDEFLİYOR, NE HEDEFLEYEMİYOR (düzeltme-3):
  //   · `alanlar.ts`in bu yüzey için KAYITLI iki bölümü (`giris` · `kayit`) artık
  //     yalnız tam-ekran kapıda çiziliyor (`kimlik/KapiEkrani.tsx`). Kabuğun içinde
  //     o çapalar YOK, yani `#/dashboard/authentication/giris` buraya geldiğinde
  //     kaydıracak bir düğüm bulamaz: bilinçli no-op. Kalıcı çözüm bir kayıt kararı
  //     ve `KapiEkrani.tsx` başlığında AÇIK KALEM olarak duruyor.
  //   · Bu yüzeyde çizilen tek çapa künye kartının `bolum-kapi`si (`KapiKunyesi`,
  //     `kimlik="kapi"` → `BolumKart` onu `id="bolum-kapi"` yapar) ve o KAYITSIZ:
  //     kenar çubuğunda görünmez, yalnız elle yazılan hash onu hedefler. Efekt
  //     bunun için duruyor. (Kapı yüzeyinin `bolum-kapi-*` çapaları BAŞKA bir
  //     yüzeye ait — ad benzerliği aldatıcı, akrabalık yok.)
  // `sekme` bağımlılığı düzeltme-2'de düştü; kare beklemesi KALDI ve gerekçesi
  // değişti: düğüm artık aynı commit'te DOM'da, ama yumuşak kaydırma yerleşim
  // oturmadan başlarsa hedefi ıskalar.
  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    const kare = window.requestAnimationFrame(() => {
      document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return () => window.cancelAnimationFrame(kare);
  }, [bolum]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <Fingerprint className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        {/* ROZET SABİT ve bu bir ölçüm iddiası DEĞİL, ölçümün SONUCU: bu yüzey
            yalnız `hal === "acik"` iken mount ediliyor (`App.tsx`), yani MOUNT'UN
            KENDİSİ ölçümdür. Eskiden burada `authenticated !== undefined` koşulu ve
            "oturum kapalı" dalı vardı; ikisi de kapı taşındıktan sonra erişilemez
            kaldı — koşul her zaman doğru, dal hiç seçilemez (düzeltme-2). Ölçülmemiş
            bir oturumu "kapalı" ilan etmeme disiplini korunuyor: o hâl artık bu
            yüzeyde değil, kapıda karşılanıyor. */}
        <Badge variant="secondary" className="shrink-0">
          oturum açık
        </Badge>
      </div>

      {/* `Kapi` SARMALAYICISI BU ÇAĞRI NOKTASINDAN KALKTI (düzeltme-3) — bileşenin
          KENDİSİ yerinde, başka çağrı yerleri meşru. Buradaki sorun sarmalayıcının
          dört dalından üçünün bu noktada yanlış davranması:
            · "Oturum düştü" → ERİŞİLEMEZ. Yüzey yalnız `hal === "acik"` iken mount
              oluyor ve `hali()` tablosu o hâlde `oturumDustu === false` olmasını
              ZORUNLU kılıyor (4. satır bayrağı görürse hâl "giris" olurdu).
            · "veri yok" iskeleti → ERİŞİLEMEZ. "acik" hâli `veri !== null` demek.
            · "Okunamadı" → ERİŞİLEBİLİR AMA ZARARLI. `hata` bir tazeleme düşünce
              doluyor ve `veri.ts` eski gövdeyi BİLEREK silmiyor; sarmalayıcı ise
              `hata`yı `veri`nin ÖNÜNDE sınıyor. Sonuç: 15 sn'lik nabızda bir ağ
              hıçkırığı, elde sağlam (bir tur bayat) gövde varken çıkış düğmesini ve
              künyeyi ekrandan siler. Oysa künyenin işi tam da bu: "son okuma"
              satırıyla verinin YAŞINI söyler. Bayat veriyi zaman damgasıyla
              göstermek, sağlam veriyi hata diye gizlemekten dürüsttür.
          Kalan tek ihtiyaç tip daraltmasıydı; onu `?? {}` karşılıyor — `OturumGovdesi`in
          her alanı opsiyonel ve künye zaten alan-alan "bildirilmedi" çiziyor, yani
          gövdesiz hâl UYDURULMUYOR, olduğu gibi gösteriliyor. */}
      <Panel marka="Meridian" markaAlt="Operatör kapısı — oturum açık">
        <OturumAcik
          onCikis={() => {
            // BİLEREK ÇIKIŞ BİR DÜŞME DEĞİLDİR: iz de ölçülen ömür de o oturuma
            // aitti, ikisi de sağlayıcıda sıfırlanıyor. İzi bırakmak, kapının bir
            // sonraki açılışında "oturumun düştü" demek olurdu.
            cikisBildir();
            oturum.tazele();
          }}
        />
      </Panel>
      <KapiKunyesi oturum={oturum.veri ?? {}} zaman={oturum.zaman} omurS={omurS} />
    </div>
  );
}
