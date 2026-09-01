"use client";

/* ============================================================================
   BİRİM ANAHTARI — servisi İSTENEN DURUMA çekmenin ekran tarafı
   ----------------------------------------------------------------------------
   OPERATÖR VAKASI (2026-09-02 gecesi, ×2): `meridian-learn` elle durdurulmuştu,
   dağıtım onu geri açtı. "Servislerin üzerine tıklayıp elle durdurabilmeliyim."
   Dağıtım yarısı kapandı (başlatma listesi artık birimin kendi beyanından
   türüyor); bu blok öteki yarısıdır.

   ANAHTAR BİR BAŞLAT/DURDUR DÜĞMESİ DEĞİL, BİR İSTENEN DURUM ANAHTARIDIR ve
   ayrım bu kartın omurgasıdır. Yalnız durduran bir düğme, bir sonraki dağıtımda
   ya da yeniden başlatmada sessizce geri alınırdı — operatörün şikâyeti tam
   olarak buydu. Bu yüzden uç `enable --now` / `disable --now` koşuyor: hem şu
   anki koşumu hem de açılış niyetini AYNI ANDA çeviriyor.

   İSTENEN DURUMUN TEK KAYNAĞI SERVİS YÖNETİCİSİDİR. Panoda ya da depoda ikinci
   bir "şu birim kapalı olsun" defteri TUTULMUYOR: iki kopya sessizce ayrışır ve
   o gün hangisinin doğru olduğu bilinemez.

   İYİMSER GÜNCELLEME YOK — VE BU BİR TASARIM KARARI, İHMAL DEĞİL. Tıklamadan
   sonra anahtar hemen yeni konuma atlamıyor; istek dönene kadar KİLİTLİ kalıyor
   ve sonra SUNUCUNUN GERİ OKUMASINDAN çiziliyor. Sebebi ölçülmüş bir hâl: komut
   başarıyla dönebilir ve birim yine de açılmayabilir (maskeli birim, açılışta
   düşen servis, yetki kuralı eksik). İyimser bir anahtar o durumda "açık" der ve
   operatör kapalı bir servisi açık sanar — panonun yapabileceği en pahalı yalan.

   ÜÇ DEĞİL DÖRT HÂL VAR ve dördü de ekranda ayrı:
     · açık        — açılışta isteniyor VE şu an koşuyor
     · kapalı      — açılışta istenmiyor VE şu an koşmuyor
     · karışık     — ikisi AYRIŞMIŞ (açılışta isteniyor ama düşmüş, ya da tersi).
                     Anahtar İSTENEN durumu gösterir çünkü çevirdiği şey odur;
                     ayrışma ayrıca YAZILIR. Bu hâli "kapalı" diye çizmek iki
                     farklı gerçeği tek kılığa sokardı.
     · bilinmiyor  — iki ölçümden biri yok. Anahtar KİLİTLİ: ölçemediğimiz bir
                     durumu çevirmek, körlemesine komut göndermektir.

   Okuyucular SAF ve DIŞA AKTARILMIŞ (JSX yok, kancasız) — `Bilesenler.tsx`teki
   `beklentiOku`/`kanitKapisi` emsali: davranışları bileşen açmadan okunabilsin
   ve bir gün node'da koşturularak ölçülebilsin.
   ============================================================================ */
import { useState } from "react";

import { Loader2, TriangleAlert } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

/* APIPOST İMPORT EDİLDİ, ÜÇÜNCÜ BİR KOPYA YAZILMADI (tek-kaynak yasası). Depoda bu
   yardımcının bugün İKİ birebir kopyası var (`kimlik/gonder.ts`, `kuyruk/onayEylem.ts`)
   ve ikincisinin şerhi gerekçesini SÜRELİ yazmıştı: "bu tur paralel ajanlarla koşuyor…
   Birleştirme tur-kapanışı işidir." O süre bu dosyayı bağlamaz; üçüncü kopya, ayrışması
   kaçınılmaz üçüncü bir gerçek olurdu. */
import { apiPost } from "../kimlik/gonder";
import { Olculemedi } from "./parcalar";
import type { BirimIstekSonucu, InfraBilesen } from "./uctipleri";

export type AnahtarHali = "acik" | "kapali" | "karisik" | "bilinmiyor";

export interface AnahtarOkumasi {
  readonly hal: AnahtarHali;
  /** Anahtarın çizileceği konum. `bilinmiyor` hâlinde anlamsızdır (anahtar kilitli). */
  readonly cizili: boolean;
  /** Açılışta isteniyor mu (servis yöneticisinin dosya durumu). */
  readonly istenen: string | null;
  /** Şu an koşuyor mu (servis yöneticisinin çalışma durumu). */
  readonly suanki: string | null;
  /** Ölçüm nereden geldi: son isteğin sunucu cevabı mı, satırın kendisi mi. */
  readonly kaynak: "sunucu" | "satir";
  /** Ölçülemeyen yarının teknik gerekçesi; hüküm kurulabildiyse boş. */
  readonly teknik: string | null;
}

/**
 * ANAHTARIN HÜKMÜ — iki ölçümden, hiçbirini varsaymadan.
 *
 * SON İSTEĞİN CEVABI VARSA O KAZANIR (`sonuc`), çünkü satır 8 saniyeye kadar bayat
 * olabilir ve tıklamadan hemen sonra eski değeri geri okumak anahtarı yerine
 * "sektirir" — operatör isteğin düştüğünü sanar. Cevabın kendisi de bir ÖLÇÜMDÜR:
 * uç durumu komuttan değil makineden geri okuyor.
 *
 * BOŞ/EKSİK ÖLÇÜM "KAPALI" SAYILMAZ. Bu, uydurma yasağının bu yüzeydeki karşılığı:
 * kapalı görünen bir anahtar, operatörü kapatılmamış bir servisi kapalı sanmaya
 * götürür ve bir sonraki adımda gerçekten kapatılması gereken şeye dokunmaz.
 */
/* İMZADA ADLANDIRILMIŞ DÖNÜŞ TİPİ YOK VE BU BİR ÖLÇÜM KISITI, ÜŞENGEÇLİK DEĞİL: bu okuyucu
   `tests/conftest.py::tsx_saf_islevleri_cevir` ile SÖKÜLÜP node'da gerçekten koşturuluyor ve o
   sökücü gövdeyi imzadan sonraki süslüden bulur — `): AnahtarOkumasi {` yazsaydık gövde
   bulunamaz, okuyucu ÖLÇÜLEMEZ olurdu. Tip güvenliği kaybolmuyor: dönüş, aşağıda `AnahtarOkumasi`
   olarak TİPLENMİŞ tek bir yerel üzerinden kuruluyor, yani derleyici her alanı yine denetliyor. */
export function anahtarOku(b: InfraBilesen, sonuc: BirimIstekSonucu | null) {
  const kaynak: "sunucu" | "satir" = sonuc === null ? "satir" : "sunucu";
  const istenen = (sonuc === null ? b.etkin_durum : sonuc.enabled) ?? null;
  const suanki = (sonuc === null ? b.durum : sonuc.active) ?? null;
  const ortak = { istenen, suanki, kaynak };

  if (istenen === null || suanki === null) {
    const eksikler = [
      istenen === null
        ? (sonuc === null ? b.etkin_durum_neden : sonuc.enabled_neden) ??
          "birimin açılışta başlaması isteniyor mu bildirilmedi"
        : null,
      suanki === null
        ? (sonuc === null ? b.durum_neden : sonuc.active_neden) ??
          "birimin şu anda koşup koşmadığı bildirilmedi"
        : null,
    ].filter((x): x is string => x !== null);
    const bilinmiyor: AnahtarOkumasi = {
      ...ortak, hal: "bilinmiyor", cizili: false, teknik: eksikler.join(" · "),
    };
    return bilinmiyor;
  }

  // "AÇILIŞTA İSTENİR" DEDİĞİ DOSYA DURUMLARI. `static` ve `masked` BİLEREK dışarıda: ikisi de
  // açılabilir bir birim tarif etmez ("açık" saymak, çevrilemeyecek bir anahtarı açık gösterirdi).
  // Liste modül sabiti DEĞİL, gövde içinde: sökülen okuyucunun dışında kalan bir sabit ölçüm
  // hattında çözülemezdi — yani davranışı ölçülemeyen bir okuyucu olurdu.
  const acikIsteniyor = ["enabled", "enabled-runtime"].includes(istenen);
  const kosuyor = suanki === "active";
  const uyumlu = acikIsteniyor === kosuyor;
  const cikti: AnahtarOkumasi = {
    ...ortak,
    // AYRIŞMADA ANAHTAR İSTENEN DURUMU GÖSTERİR — çevirdiği şey odur; koşma durumu bir SONUÇtur.
    hal: uyumlu ? (acikIsteniyor ? "acik" : "kapali") : "karisik",
    cizili: acikIsteniyor,
    teknik: uyumlu
      ? null
      : `açılış isteği "${istenen}" ama çalışma durumu "${suanki}" — ikisi ayrışmış`,
  };
  return cikti;
}

/**
 * İKİ TIK ARASINDA OKUNAN CÜMLE. İSTENEN DURUM DİLİYLE yazılır ("kapalı tutar"),
 * "durdurur" diye DEĞİL: operatörün vakası tam olarak durdurmanın kalıcı olmamasıydı
 * ve cümle yaptığı işi eksik anlatırsa onay bir onay değildir.
 */
export function onayMetni(ad: string, hedef: "acik" | "kapali"): { baslik: string; govde: string } {
  if (hedef === "kapali") {
    return {
      baslik: `${ad} kapatılsın mı?`,
      govde:
        `Birim şimdi durdurulur VE açılışta başlaması iptal edilir. Dağıtımlar da onu kapalı ` +
        `tutar: dağıtım betiği başlatacağı servisleri birimin kendi beyanından türetiyor, yani ` +
        `bir sonraki dağıtım bu birimi geri açmaz. Yeniden açmak için aynı anahtarı geri çevir.`,
    };
  }
  return {
    baslik: `${ad} açılsın mı?`,
    govde:
      `Birim şimdi başlatılır VE açılışta başlaması istenir. Bundan sonraki dağıtımlar da onu ` +
      `açık tutar. Sonuç, komuttan değil makinenin kendi cevabından okunur — başlatma düşerse ` +
      `anahtar açık görünmez.`,
  };
}

/**
 * ANAHTARI OLMAYAN SATIRIN KISA GEREKÇESİ. Boş hücre bırakmak "burada bir şey yok" diye
 * okunurdu; oysa söylenecek bir şey var ve kısa: bu birim kapsam dışı.
 *
 * ÇEKİRDEK BİRİM AYRI CÜMLE ALIR çünkü ayrı bir sebep: onu panodan kapatmak, panonun kendi
 * altındaki dalı kesmek olurdu (kapatıldığını bildiren yanıt gönderilemezdi).
 */
export function anahtarsizNeden(b: InfraBilesen) {
  // Dönüş tipi imzada YAZILMIYOR — `anahtarOku` şerhindeki ölçüm kısıtının aynısı.
  if (b.ad === "meridian.service") return "anahtar yok — çekirdek birim";
  if (b.sablon) return "anahtar yok — şablon birim";
  return "anahtar yok — kapsam dışı";
}

/**
 * SUNUCU CEVABI NE ZAMAN ÖNCELİĞİNİ KAYBEDER — K1'in çivisi (görev incelemesi, 2026-09-02).
 *
 * KUSUR ŞUYDU: cevap bir kez saklandığında ÖMÜR BOYU kazanıyordu. Yani ilk tıklamadan sonra
 * anahtar o tek geri-okumaya çivilenirdi; birim sonradan DÜŞSE (`active` → `failed`) ya da
 * başka bir yoldan açılıp kapansa pano hâlâ eski cevabı gösterirdi — ve `karisik` tespiti,
 * yani bu görevi doğuran operatör vakasının ta kendisi, sessizce ölürdü.
 *
 * KURAL: cevap YALNIZ kendisinden SONRA okunmuş bir satır gelene kadar kazanır. Sonrası
 * geldiğinde satır daha yeni bir ÖLÇÜMdür ve öncelik ona geçer.
 *
 * BU, İYİMSER GÜNCELLEME YASAĞINI GEVŞETMEZ — TERSİNE SIKILAŞTIRIR: düşülen yer isteğin HEDEFİ
 * değil, sunucudan yeni okunmuş satırdır. Yani her iki kaynak da ölçümdür; aralarında YAŞA göre
 * seçim yapılıyor, ümide göre değil.
 *
 * Damgalar milisaniye (sayı) — `Date` değil: bu okuyucu node'da sökülerek koşturuluyor ve
 * argümanları JSON'dan geçiyor.
 */
export function sonucGecerliMi(sonucTs: number | null, veriTs: number | null) {
  if (sonucTs === null) return false;   // hiç istek yapılmadı
  if (veriTs === null) return true;     // satır hiç okunamadı → cevap eldeki TEK ölçüm
  return veriTs <= sonucTs;             // satır cevaptan ESKİYSE cevap hâlâ daha taze
}

const HAL_METNI: Record<AnahtarHali, string> = {
  acik: "açık",
  kapali: "kapalı",
  karisik: "ayrışmış",
  bilinmiyor: "ölçülemedi",
};

/** İsteğin üç hâli AYRI: gönderiliyor · sunucu cevap verdi · sunucu reddetti. */
type IstekHali =
  | { readonly ad: "bosta" }
  | { readonly ad: "gonderiliyor"; readonly hedef: "acik" | "kapali" }
  | { readonly ad: "reddedildi"; readonly metin: string };

export function BirimAnahtari({
  b,
  veriTs,
  onDegisti,
}: {
  readonly b: InfraBilesen;
  /**
   * Satırın taşındığı gövdenin SON BAŞARILI okuma damgası (ms). Cevabın ne zaman önceliğini
   * kaybettiği buradan ölçülür — `sonucGecerliMi` şerhi. `null` = gövde hiç okunamadı.
   */
  readonly veriTs: number | null;
  /** Sunucu cevabı geldikten SONRA çağrılır — satırı tazelemek çağıranın işi. */
  readonly onDegisti: () => void;
}) {
  const [sonuc, setSonuc] = useState<{ govde: BirimIstekSonucu; ts: number } | null>(null);
  const [istek, setIstek] = useState<IstekHali>({ ad: "bosta" });
  const [soruluyor, setSoruluyor] = useState<"acik" | "kapali" | null>(null);

  const ad = b.ad ?? "";
  // TÜRETİLMİŞ, `useEffect` İLE TEMİZLENMİŞ DEĞİL: efektle silmek önce BAYAT cevapla bir kare
  // çizer, sonra düzeltirdi — anahtarın gözle görülür şekilde "sektiği" hâl. Türetme o kareyi
  // hiç üretmez. Eski cevap bellekte kalır ama HÜKME GİRMEZ.
  const gecerli = sonuc !== null && sonucGecerliMi(sonuc.ts, veriTs);
  const oku = anahtarOku(b, gecerli ? sonuc.govde : null);
  const kilitli = istek.ad === "gonderiliyor" || oku.hal === "bilinmiyor" || ad === "";

  async function gonder(hedef: "acik" | "kapali") {
    setSoruluyor(null);
    setIstek({ ad: "gonderiliyor", hedef });
    const y = await apiPost(`/api/infra/birim/${encodeURIComponent(ad)}/istek`, { hedef });
    if (!y.ok) {
      // HER KOD KENDİ ÇARESİNİ SÖYLER — "bir şeyler ters gitti" yasak. Ucun `detail` metni
      // AYNEN taşınır: sunucu ret gerekçesini oraya yazıyor ve o cümle operatörü doğru yere
      // gönderiyor (yetki kuralı mı eksik, birim mi maskeli, ağ mı düştü).
      const bas =
        y.kod === 0
          ? "Ağ hatası — yanıt hiç gelmedi. İstek makineye ulaşmış ve cevabı kaybolmuş OLABİLİR: " +
            "körlemesine tekrarlama, satırı tazeleyip durumu kontrol et."
          : y.kod === 401
            ? "Oturum düştü. Panoya yeniden gir; birime dokunulmadı."
            : y.kod === 403
              ? "Bu birim panodan anahtarlanamıyor."
              : y.kod === 503
                ? "Servis yöneticisi bu makinede yok — komut hiç koşmadı, birimin durumu değişmedi."
                : `İstek reddedildi (${y.kod}).`;
      setIstek({ ad: "reddedildi", metin: `${bas}${y.detay ? ` ${y.detay}` : ""}` });
      // SATIR YİNE DE TAZELENİR: reddin bir kısmı (zaman aşımı) birimi DEĞİŞTİRMİŞ olabilir.
      onDegisti();
      return;
    }
    // DAMGA CEVAPLA BİRLİKTE SAKLANIR: "bu ölçüm ne zaman alındı" sorusunun cevabı olmadan
    // satırla yaş kıyaslaması kurulamaz ve cevap ömür boyu öncelikli kalırdı (K1).
    setSonuc({ govde: (y.govde ?? {}) as BirimIstekSonucu, ts: Date.now() });
    setIstek({ ad: "bosta" });
    onDegisti();
  }

  const hedefi: "acik" | "kapali" = oku.cizili ? "kapali" : "acik";
  const metin = soruluyor === null ? null : onayMetni(ad, soruluyor);

  return (
    <span className="flex flex-col items-start gap-1">
      <span className="flex items-center gap-2">
        <Switch
          checked={oku.cizili}
          disabled={kilitli}
          onCheckedChange={() => setSoruluyor(hedefi)}
          aria-label={`${ad} birimini ${hedefi === "acik" ? "aç" : "kapat"}`}
          title={
            oku.teknik
              ? `${HAL_METNI[oku.hal]} — ${oku.teknik}`
              : `açılış isteği: ${oku.istenen} · çalışma durumu: ${oku.suanki} · kaynak: ` +
                `${oku.kaynak === "sunucu" ? "son isteğin sunucu cevabı" : "son ölçüm"}`
          }
        />
        {istek.ad === "gonderiliyor" ? (
          <Loader2 className="size-3.5 animate-spin text-muted-foreground" aria-hidden />
        ) : (
          <span
            className={cn(
              "text-xs",
              oku.hal === "acik" && "text-emerald-600 dark:text-emerald-400",
              oku.hal === "karisik" && "text-amber-600 dark:text-amber-400",
              oku.hal !== "acik" && oku.hal !== "karisik" && "text-muted-foreground",
            )}
          >
            {HAL_METNI[oku.hal]}
          </span>
        )}
      </span>

      {oku.hal === "bilinmiyor" ? (
        <Olculemedi
          neden="Birimin istenen durumu okunamadı — anahtar kilitli"
          teknik={oku.teknik ?? undefined}
          kisa
        />
      ) : null}

      {oku.hal === "karisik" ? (
        <span className="flex items-start gap-1 text-amber-600 text-xs dark:text-amber-400" title={oku.teknik ?? undefined}>
          <TriangleAlert className="mt-0.5 size-3 shrink-0" aria-hidden />
          açılış isteği ile çalışma durumu ayrışmış
        </span>
      ) : null}

      {istek.ad === "reddedildi" ? (
        <span className="max-w-[20rem] text-destructive text-xs leading-4">{istek.metin}</span>
      ) : null}

      {gecerli && sonuc.govde.komut ? (
        // ÖLÇÜMÜN KÜNYESİ: operatör sonucu KENDİ ELİYLE doğrulayabilsin — "pano öyle diyor" ile
        // "makineye sordum" arasındaki fark (`beklenmedik_olcum.komut` emsali).
        <span className="font-mono text-[10px] text-muted-foreground" title="Panonun makinede koşturduğu komut">
          {sonuc.govde.komut}
        </span>
      ) : null}

      <AlertDialog open={soruluyor !== null} onOpenChange={(a) => !a && setSoruluyor(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{metin?.baslik ?? ""}</AlertDialogTitle>
            <AlertDialogDescription>{metin?.govde ?? ""}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Vazgeç</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (soruluyor !== null) void gonder(soruluyor);
              }}
            >
              {soruluyor === "kapali" ? "Kapat" : "Aç"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </span>
  );
}
