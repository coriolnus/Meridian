"use client";

/* ============================================================================
   TAM-EKRAN GİRİŞ KAPISI — kimliksiz ziyaretçinin gördüğü TEK yüz
   ----------------------------------------------------------------------------
   ÖNCÜLÜN ÖLDÜĞÜ GÜN: 2026-09-01. Pano bugüne kadar bir DIŞ kapının (tünel,
   ardından APISIX basic-auth) arkasındaydı ve giriş, kabuğun İÇİNDE bir yüzeydi.
   O tercihin gerekçesi "dış kapı zaten var, ikinci bir kapı olmayan bir
   yönlendirme katmanı varmış gibi gösterirdi" idi. Basic-auth operatör kararıyla
   KALDIRILDI; tek kimlik katmanı artık uygulamanın kendi oturum sistemi. Yani
   kimliksiz ziyaretçi bugün uygulamanın İLK yüzünü görüyor ve o yüz kenar çubuğu,
   yüzey adları ve 401'e düşen paneller OLAMAZ.

   KABUK BURADA MOUNT EDİLMEZ: karar `App.tsx`te, oturum açık DEĞİLKEN `Kabuk`
   hiç doğmuyor. Gizlemek yetmezdi — kabuk doğsaydı kendi nabızlarını açar, her
   biri 401 yer ve ziyaretçiye sistemin yüzey haritasını okuturdu.

   ÜÇ HÂLLİ MAKİNE YENİDEN YAZILMADI: sınıflama `pano/oturum.tsx::hali`de TEK
   kaynak, ekran gövdeleri `yuzeyler/kimlik/KapiEkrani.tsx`te TEK kaynak. Bu dosya
   yalnız ÇERÇEVEDİR — şablonun `auth/v2` bölünmüş paneli, `h-dvh`.
   ============================================================================ */
import { RefreshCw } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

import { useOturum } from "./oturum";
import { GirisEkrani, KurulumEkrani, type KapiSekmesi } from "./yuzeyler/kimlik/KapiEkrani";
import { MarkaRayi } from "./yuzeyler/kimlik/MarkaRayi";

/* --- ÇERÇEVE -------------------------------------------------------------- */

/* RAY METNİ SABİT VE NÖTR — HÂLE GÖRE DEĞİŞMİYOR (düzeltme-1, 2026-09-01).
   Önce burada hâl başına bir alt başlık vardı ("Kapı henüz kurulmadı…",
   "Operatör kapısı — giriş bekleniyor") ve rayın altında iki operatör sütunu
   duruyordu. İkisi de dış kapının (basic-auth) arkasında yazılmıştı; o kapı
   kalkınca aynı metinler anonim ziyaretçinin ekranına taşındı. Ray artık tek
   şey söylüyor: bu sistemin ne olduğu. Hangi ekranda olduğunu SAĞ SÜTUN
   zaten söylüyor ve orası da iç ad taşımıyor.

   TEK CÜMLE, ABARTISIZ: ne pazarlama ("kurumsal-sınıf otonom alfa motoru")
   ne de yığın ifşası. Ziyaretçinin bilmesi gereken ve bilmesinde sakınca
   olmayan tek şey, kapıyı çaldığı kapının ne olduğu. */
const RAY_BASLIK = "Meridian";
const RAY_ALT = "Hisse senedi araştırma ve kâğıt-icra panosu.";

/**
 * Şablonun `auth/v2/layout`u: solda marka rayı, sağda form, ekranın tamamı.
 * Ray `lg` altında GİZLİ (kendi sınıfı), o yüzden dar ekranda tek sütun kalır.
 *
 * KAYDIRMA DIŞ KAPTA, İÇ KAPTA DEĞİL: `items-center` ile ortalanmış bir içerik
 * viewport'tan uzun olduğunda ÜSTÜNDEN kırpılır ve kırpılan yer forma erişilemeyen
 * bir alan olurdu (uzun hata metni + iki alanlı kurulum formu bunu 700px yükseklikte
 * gerçekten yapıyor). `min-h-full` + dışta `overflow-y-auto` ikisini de karşılar:
 * sığarken ortalı, sığmazken kaydırılır.
 */
function Cerceve({ children }: { readonly children: ReactNode }) {
  return (
    <div className="grid h-dvh bg-background lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1fr)]">
      {/* `ayrintilar` BİLEREK VERİLMİYOR — rayın alt bloğu operatöre aittir. */}
      <MarkaRayi baslik={RAY_BASLIK} altBaslik={RAY_ALT} />
      <div className="min-h-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </div>
    </div>
  );
}

/* --- NE KABUK NE KAPI: hâl ölçülemedi ------------------------------------- */

/**
 * DÖRDÜNCÜ HÂL EKRANI. Kabuk da kapı da bir İDDİADIR: kabuk "girdin" der, kapı
 * "girmedin" der. Gövde okunamadığında ikisi de tahmin olurdu — bu yüzden burada
 * hiçbir ekran seçilmiyor ve seçilemediğinin NEDENİ yazılıyor. Kabuğun içindeki
 * Giriş yüzeyi 2026-08-25'ten beri aynı dürüstlüğü taşıyordu; kapı dışarı
 * taşınırken o hâl de dışarı taşındı, düşürülmedi.
 *
 * MARKA RAYI BİLEREK YOK: ray kapının kendi çerçevesi ve üstündeki iki cümle
 * ("parolayı unuttuysan…") bir GİRİŞ ekranının cümleleridir. Hâl ölçülmemişken
 * onu çizmek, seçilmediğini söylediğimiz ekranı yine de seçmek olurdu. Bekleme
 * NÖTRDÜR: aynı zemin, ortada tek bir cümle ve nedeni.
 */
function Bekleme() {
  const { durum } = useOturum();

  /* İKİ KATMAN, DEPONUN KENDİ İDİOMU (`Olculemedi(neden, teknik)`): görünen cümle
     insan cümlesidir, teşhis `title`da durur. Burada bu bir üslup tercihi DEĞİL
     bir sınır: bu ekranı kimliksiz ziyaretçi görüyor ve `durum.hata` ham metni uç
     yolunu taşıyor ("/api/session → HTTP 502 …"). Teşhisi DÜŞÜRMEK de olmazdı —
     sunucuya bakacak kişi tam olarak o satırı arıyor. Görünürden kaldırıldı,
     erişilebilirden değil. */
  /* DALLAR `hali()` TABLOSUYLA AYNI SIRADA (düzeltme-2): bu ekran yalnız
     `okunmadi` ve `olculemedi` hâllerinde çiziliyor. `okunmadi` ⟺ `veri === null`,
     yani ilk üç dalın hepsi ÖNCE o koşulu sınıyor; dördüncü dal geriye kalan tek
     hâldir (gövde var, alanlar yok). Eskiden `oturumDustu` en başta sınanıyordu ve
     tablo değiştikten sonra bu YANLIŞ olurdu: bayrak artık gövde varken hâli
     `giris`e taşıyor, yani buraya hiç düşmüyor — o sıra "alanlar gelmedi" durumunu
     401 cümlesiyle anlatırdı. İki yerde iki farklı sıra, sessizce ayrışan iki kural. */
  const govde = durum.veri === null && durum.oturumDustu ? (
    <Alert variant="destructive">
      <AlertTitle>Oturum durumu sorulamadı</AlertTitle>
      <AlertDescription title="/api/session 401 döndürdü — bu uç yetki aramaz">
        Sunucu, oturum durumu sorusunu yetki reddiyle karşıladı. Bu soru yetki istemez; araya giren bir vekil sunucu
        yanıtı değiştiriyor olabilir.
      </AlertDescription>
    </Alert>
  ) : durum.veri === null && durum.hata !== null ? (
    <Alert variant="destructive">
      <AlertTitle>Oturum durumu okunamadı</AlertTitle>
      <AlertDescription title={durum.hata}>
        Sunucuya ulaşıldı ama oturum durumu alınamadı. Sunucu ayaktaysa birkaç saniye içinde kendiliğinden düzelir.
      </AlertDescription>
    </Alert>
  ) : durum.veri === null ? (
    <div className="flex items-center gap-3 text-muted-foreground text-sm">
      <Spinner />
      Oturum durumu okunuyor…
    </div>
  ) : (
    <Alert variant="destructive">
      <AlertTitle>Hangi ekranın gösterileceği ölçülemedi</AlertTitle>
      <AlertDescription
        title={`password_set: ${String(durum.veri.password_set)} · authenticated: ${String(durum.veri.authenticated)}`}
      >
        Sunucu cevap verdi ama oturum durumunu eksik bildirdi: hangi ekranın gösterileceğini söyleyen iki alan gelmedi.
        Onlar olmadan kurulum, giriş ve pano arasında seçim yapmak tahmin olurdu.
      </AlertDescription>
    </Alert>
  );

  return (
    <div className="flex h-dvh flex-col items-center justify-center gap-4 bg-background p-6">
      <div className="flex w-full max-w-md flex-col gap-4">
        {govde}
        <Button variant="outline" className="w-full" onClick={durum.tazele}>
          <RefreshCw className="size-4" aria-hidden />
          Yeniden sor
        </Button>
      </div>
    </div>
  );
}

/* --- KAPI ----------------------------------------------------------------- */

/**
 * Oturum AÇIK DEĞİLKEN çizilen tek şey. `App.tsx` yalnız iki yol tanır: açık
 * oturum → kabuk, geri kalan HER hâl → burası. Ara bir ekran (yarı kabuk, kilitli
 * panolar) BİLEREK yok — yarım kabuk, olmayan bir yetkiyi varmış gibi gösterir.
 */
export function GirisKapisi() {
  const { durum, hal, onceAcikti, omurBildir } = useOturum();
  // SEKME YEREL: bu kapıda rota YOK (`RotaSaglayici` kabuğun içinde doğuyor) ve
  // olmasını da istemiyoruz — kimliksiz ziyaretçiye derin bağ vermek, gidemeyeceği
  // adresleri okutmak olurdu.
  const [sekme, setSekme] = useState<KapiSekmesi>("giris");

  // "DÜŞTÜ" İKİ KAYNAKTAN GELİR ve ikisi de aynı cümleyi hak eder: bu sekmede açık
  // bir oturum ölçülmüş olması (`onceAcikti`), YA DA oturum ucunun 401 dönmesi
  // (`oturumDustu` — `hali()` tablosunun 4. satırı bizi buraya o yüzden düşürmüş
  // olabilir). İkincisini atlasaydık bayrak yüzünden giriş ekranına düşen kullanıcı
  // "hiç girmedin" cümlesini okurdu — oysa bir şey BİTTİ.
  const dustu = onceAcikti || durum.oturumDustu;

  if (hal === "okunmadi" || hal === "olculemedi") return <Bekleme />;

  if (hal === "kurulum") {
    return (
      <Cerceve>
        <KurulumEkrani onBasari={durum.tazele} />
      </Cerceve>
    );
  }

  return (
    <Cerceve>
      <GirisEkrani
        sekme={sekme}
        onSekme={setSekme}
        dustu={dustu}
        // ÖMÜR YEREL DURUMDA TUTULAMAZ: bu bileşen giriş başarılı olur olmaz
        // sökülüyor (kabuk doğuyor) ve ölçüm onunla birlikte kaybolurdu —
        // kapının sessiz bedeli tam olarak bu olurdu. Sağlayıcıya yazılıyor;
        // okuyucusu kabuk içindeki kapı künyesi.
        onBasari={(omur) => {
          omurBildir(omur);
          durum.tazele();
        }}
      />
    </Cerceve>
  );
}
