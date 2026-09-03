"use client";

/* ============================================================================
   HAFIZA YAZMA EYLEMLERİ — DÖRT DÜĞMENİN TEK KAPISI
   ----------------------------------------------------------------------------
   Bu yüzeyin bugüne kadarki tek fiili OKUMAKtı. Dört eylem bunu bozuyor ve
   operatörün isteğiyle geliyor: işlem satırında "İptal et · Yeniden dene ·
   Kaydı sil", ana sayfanın düşen birleştirmeler penceresinde "Hepsini yeniden
   dene". Kalan yazma düğmeleri (ayar kaydetme, kayıt düzenleme/geçersiz kılma,
   belge yeniden işleme, webhook, değerlendirme tetikleme) DEVRE DIŞI kalıyor ve
   rozetlerini koruyor — bu dosya o rozeti yalnız DÖRT eylemden kaldırır.

   ---------------------------------------------------------------------------
   NEDEN TEK BİLEŞEN — VE NEDEN ONAY İKİ ADIM
   ---------------------------------------------------------------------------
   Dört eylem dört yerde çiziliyor ama SÖZLEŞMELERİ aynı: niyet → onay → uygula →
   sonucu oku. Dört kopya yazsaydık, birinde onay penceresi unutulur ya da biri
   "geri alınamaz" uyarısını düşürürdü ve fark ancak yıkıcı bir tıklamadan sonra
   görünürdü (tek-kaynak yasası). Onay penceresi bu yüzden TEK bileşendir ve
   eylemler arasındaki tüm fark PROP olarak geçer.

   ÜST YÜZEY ONAY SORMUYOR — VE BU BİLEREK AYRIŞTIRILDI. Ölçüldü: üst yüzeyin
   işlemler görünümünde üç düğme de doğrudan çağrı atıyor, penceresiz. Bizim
   panomuzda "Kaydı sil" GERİ ALINAMAZ bir fiildir ve tek tıklamayla bir tablo
   satırından tetiklenebilir olsaydı, yanlış satıra basmanın bedeli geri
   alınamaz olurdu. Birebirlik BİLGİ MİMARİSİNDEDİR, yıkıcı fiillerin
   sürtünmesinde değil.

   ---------------------------------------------------------------------------
   YASA 6 — SONUÇ OKUNMADAN İSTEK YOK
   ---------------------------------------------------------------------------
   Her isteğin bir okuyucusu var ve okuyucu EKRANDAdır: başarıda bildirim +
   listenin/sayaçların yeniden okunması, başarısızlıkta pencerenin İÇİNDE duran
   gerekçe. Bu yüzden istek uçarken pencere kapanmaz (kaçış tuşu da kapatmaz):
   kapansaydı gerekçe hiç okunmadan yok olurdu. Panonun kendi kaydı yeterli
   değil diye ikinci bir iz TUTULMUYOR — izi sunucu tutuyor (vekil her yazma
   çağrısında deftere yazıyor); tarayıcı konsoluna yazmak, kimsenin okumadığı
   ikinci bir kayıt üretmek olurdu.

   ---------------------------------------------------------------------------
   UYDURMA YASAĞI — GEREKÇE SUNUCUNUNDUR
   ---------------------------------------------------------------------------
   Vekil dört alanlı bir zarf döndürüyor: tuttu mu · hangi durum kodu · üst
   servisin gövdesi · tutmadıysa gerekçe. Gerekçe cümlesi EKRANA AYNEN çıkar;
   burada "bir şeyler ters gitti" yazılmaz. Durum kodu ölçülemediğinde (yanıt
   hiç gelmedi) `0` YAZILMAZ, ölçülemediği söylenir — sıfır bir koddur,
   "bilmiyorum" değildir.
   ============================================================================ */
import { useRef, useState, type ComponentType } from "react";
import { Loader2, TriangleAlert } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { apiPost } from "../../gonder";
import { Olculemedi } from "../sistem/parcalar";
import { sayi, sozluk } from "./parcalar";

/* ---------------------------------------------------------------------------
   UÇLAR — vekilin yazma yolları (sözleşme: iki adı da olan kapalı bir sözlük)
   --------------------------------------------------------------------------- */

const UC_ISLEM = "/api/hindsight/islem";
const UC_KURTAR = "/api/hindsight/konsolidasyon/kurtar";
/** Kurtarmanın ikinci bacağı. Vekilde HENÜZ OLMAYABİLİR — aşağıdaki şerhe bak. */
const UC_TETIKLE = "/api/hindsight/konsolidasyon/tetikle";

/* ---------------------------------------------------------------------------
   VEKİLİN DÖRT ALANLI ZARFI
   --------------------------------------------------------------------------- */

export interface YazmaZarfi {
  /** Üst servis isteği kabul etti mi. */
  readonly ok: boolean;
  /** Üst servisin durum kodu; ölçülemediyse `null` — `0` YAZILMAZ. */
  readonly http: number | null;
  /** Üst servisin gövdesi, aynen. */
  readonly govde: unknown;
  /** Tutmadıysa gerekçe — sunucunun cümlesi, aynen taşınır. */
  readonly neden: string | null;
}

/** Yanıtı zarf olarak okur; bu ucun sözleşmesinden değilse `null`. */
function zarfOku(ham: unknown): YazmaZarfi | null {
  const g = sozluk(ham);
  if (g === null) return null;
  if (typeof g.ok !== "boolean") return null;
  if (!("neden" in g) || !("http" in g)) return null;
  const kod = g.http;
  return {
    ok: g.ok,
    http: typeof kod === "number" && Number.isFinite(kod) ? kod : null,
    govde: g.govde ?? null,
    neden: typeof g.neden === "string" && g.neden.trim() !== "" ? g.neden : null,
  };
}

/**
 * TEK YAZMA ÇAĞRISI. Ne fırlatır ne yutar: her hâl zarfta adıyla durur.
 *
 * ZARF ÖNCE OKUNUR, DURUM KODUNA SONRA BAKILIR — ve sıra önemli: vekil hem
 * başarıda hem üst servis arızasında (200) hem de isteği reddederken (400/404)
 * AYNI dört alanı gönderiyor. Önce koda baksaydık, reddin gerekçesini kendi
 * uydurduğumuz bir cümleyle değiştirirdik.
 */
export async function hafizaYaz(yol: string, govde: unknown): Promise<YazmaZarfi> {
  const y = await apiPost(yol, govde);
  const zarf = zarfOku(y.ham);
  if (zarf !== null) return zarf;

  /* ZARF GELMEDİ: yanıt bu ucun sözleşmesinden değil. Her kod KENDİ çaresini
     söyler — "bir şeyler ters gitti" yasak (birim anahtarı emsali). */
  if (y.kod === 0) {
    return {
      ok: false,
      http: null,
      govde: null,
      neden:
        "Yanıt hiç gelmedi — istek makineye ulaşmış ve cevabı kaybolmuş OLABİLİR. " +
        "Körlemesine tekrarlama: listeyi tazeleyip durumu gör" +
        (y.detay ? ` (tarayıcının bildirdiği: ${y.detay})` : ""),
    };
  }
  if (y.kod === 401) {
    return {
      ok: false,
      http: 401,
      govde: null,
      neden:
        "Oturum düştü — panoya yeniden girmeden eylem uygulanamaz; hafızaya dokunulmadı" +
        (y.detay ? ` — ${y.detay}` : ""),
    };
  }
  if (y.kod === 404) {
    /* UYUYAN EMNİYET AĞI — VE BUGÜN BEKLENEN YOL DEĞİL (ölçüldü 2026-09-03).
       Dört yazma ucunun DÖRDÜ DE vekilde var (işlem sözlüğü + konsolidasyon
       sözlüğü: kurtar ve tetikle). Yani bu dal yalnız eksik/eski bir dağıtımda
       ateşlenir. Silinmedi, çünkü sessiz kalsaydı eksik dağıtım "üst servis
       arızası" gibi okunurdu: vekilin TANIDIĞI bir yoldaki "tanınmayan eylem"
       404'ü ZARFLA gelir ve yukarıda okunur; buraya düşen 404 ise sunucuda
       böyle bir YOL olmadığı hâldir ve çaresi başkadır (dağıtım). */
    return {
      ok: false,
      http: 404,
      govde: null,
      neden:
        "Bu eylemin sunucu ucu bu sürümde yok — istek üst servise hiç iletilmedi; " +
        "pano ile sunucu sürümü ayrışmış olabilir" +
        (y.detay ? ` — ${y.detay}` : ""),
    };
  }
  return {
    ok: false,
    http: y.kod,
    govde: null,
    neden:
      `Sunucu isteği reddetti (durum kodu ${y.kod}) ve sonuç zarfını döndürmedi` +
      (y.detay ? ` — ${y.detay}` : ""),
  };
}

/* ---------------------------------------------------------------------------
   EKRANA ÇIKAN SONUÇ
   --------------------------------------------------------------------------- */

/**
 * BİR ÇAĞRININ SONUCU — ZİNCİRDE HER BACAK KENDİ SATIRINI TAŞIR.
 *
 * İlk yazımda kısmi başarı TEK bir `http` alanı taşıyordu ve o alan KURTARMA
 * bacağınındı, oysa şerh TETİKLEME bacağının arızasını anlatıyordu (inceleme
 * bulgusu M-6): ölü ama yanıltıcı bir alan. Artık her bacak kendi adını, kendi
 * durum kodunu ve kendi gerekçesini taşıyor — hangi çağrının tuttuğu ekrandan
 * okunur, çıkarılmaz.
 */
export interface YazmaBacagi {
  /** Bu bacağın operatöre görünen adı. */
  readonly ad: string;
  readonly ok: boolean;
  /** Sunucunun bildirdiği durum kodu; ölçülemediyse `null` — `0` YAZILMAZ. */
  readonly http: number | null;
  /** Tutmadıysa sunucunun gerekçesi, aynen. */
  readonly neden: string | null;
}

export interface YazmaSonucu {
  /** Zincirin TAMAMI tuttu mu — bir bacak bile düşmüşse `false` DEĞİL, `eksik` dolu olur. */
  readonly ok: boolean;
  /** Tek satır özet — bildirimin metni. Yalnız ÖLÇÜLEN sayılarla kurulur. */
  readonly ozet: string;
  /** Her çağrının kendi sonucu, sırasıyla. */
  readonly bacaklar: readonly YazmaBacagi[];
  /**
   * KISMİ BAŞARI: istek tuttu ama işin TAMAMI yapılmadı — NE YAPILMADIĞINI düz
   * cümleyle söyler. Dolu olduğunda pencere KAPANMAZ (Yasa 6): en nüanslı mesaj
   * dört saniyelik bir bildirime emanet edilemez (inceleme bulgusu I-2).
   */
  readonly eksik: string | null;
}

function bacak(ad: string, z: YazmaZarfi): YazmaBacagi {
  return { ad, ok: z.ok, http: z.http, neden: z.neden };
}

function basarisiz(ad: string, z: YazmaZarfi): YazmaSonucu {
  return { ok: false, ozet: "", bacaklar: [bacak(ad, z)], eksik: null };
}

/* ---------------------------------------------------------------------------
   İŞLEM SATIRI EYLEMLERİ — ÜÇ EYLEM, KAPALI SÖZLÜK
   ----------------------------------------------------------------------------
   Eylem kimlikleri vekilin yol sözlüğüyle AYNI kelimelerdir (`iptal` ·
   `yeniden-dene` · `sil`); serbest metin gönderilmez, çünkü tanınmayan bir
   kelime sunucuda 404 olur ve ekran "eylem yok" ile "yol yanlış yazıldı"
   arasındaki farkı gösteremezdi.
   --------------------------------------------------------------------------- */

export type IslemEylemi = "iptal" | "yeniden-dene" | "sil";

/**
 * DURUM KAPILARI — ÜST YÜZEYDEN ÖLÇÜLDÜ, TAHMİN EDİLMEDİ.
 *
 * Üst yüzeyin işlemler görünümü satır düğmelerini şu kapılarla çiziyor
 * (ölçüldü 2026-09-02, `bank-operations-view.tsx` satır tablosu; aynı üç kapı
 * detay penceresinde de tekrarlanıyor):
 *     iptal        → yalnız bekleyen (`pending`)
 *     yeniden dene → düşen ya da iptal edilmiş (`failed` · `cancelled`)
 *     sil          → düşen · iptal edilmiş · bitmiş (`completed`)
 *
 * KAPI VEKİLDE DEĞİL BURADA: vekil bilerek kapı koymadı (üst servisin izin
 * verdiğini reddeden ikinci bir kopya, sessizce ayrışan bir kural olurdu). Kapı
 * bir GÖRÜNÜM kuralıdır ve tek yerde, burada yaşar.
 *
 * `processing` HİÇBİR kapıda yok ve bu bir ölçüm sonucudur: koşan bir işe bu üç
 * düğmenin hiçbiri uygulanmıyor.
 */
export const ISLEM_KAPILARI: Record<IslemEylemi, readonly string[]> = {
  iptal: ["pending"],
  "yeniden-dene": ["failed", "cancelled"],
  sil: ["failed", "cancelled", "completed"],
};

/** Bu duruma hangi eylemler uygulanabilir. Durum ölçülemediyse HİÇBİRİ. */
export function islemEylemleri(durum: string | null): readonly IslemEylemi[] {
  if (durum === null) return [];
  return (Object.keys(ISLEM_KAPILARI) as IslemEylemi[]).filter((e) =>
    ISLEM_KAPILARI[e].includes(durum),
  );
}

/* ---------------------------------------------------------------------------
   BÜTÇE UYARISI — TEK CÜMLE, İKİ YERDE OKUNUR
   ----------------------------------------------------------------------------
   Yeniden deneme ve kuyruğa alma üst serviste model çağrısı doğurur; günlük
   ücretsiz hakkın dolduğu bir günde bu çağrı düşer. Uyarı onay penceresindedir,
   çünkü kararın verildiği an orasıdır.
   --------------------------------------------------------------------------- */
export const BUTCE_UYARISI =
  "Bu eylem üst serviste birleştirme işi doğurur ve birleştirme model çağrısı üretir. " +
  "Günlük ücretsiz hak dolmuşsa çağrı 429 ile düşer ve iş yeniden bekleyene döner.";

/* ---------------------------------------------------------------------------
   EYLEM KÜNYELERİ — düğme metni, pencere metni, geri alınabilirlik
   --------------------------------------------------------------------------- */

export interface EylemKunyesi {
  /** Kimlik — çivilerin ve derin bağların tutunduğu ad. */
  readonly kimlik: string;
  /** Düğmenin üstündeki metin. */
  readonly etiket: string;
  /** Onay penceresinin başlığı. */
  readonly baslik: string;
  /** Ne olacağını anlatan cümle — pencerenin ilk satırı. */
  readonly ne: string;
  /** Geri alınabilir mi — pencerede AÇIKÇA yazılır. */
  readonly geriAlinabilir: boolean;
  /** Bütçe uyarısı gösterilsin mi. */
  readonly butce: boolean;
  /** Yıkıcı mı — onay düğmesinin rengi buradan. */
  readonly yikici: boolean;
  /** Onay düğmesinin metni. */
  readonly uygula: string;
  /**
   * BAŞARIDA GÖSTERİLEN CÜMLE. Düğme etiketinden TÜRETİLMİYOR: "Kaydı sil
   * uygulandı" dürüsttü ama Türkçesi tökezliyordu (inceleme bulgusu M-9).
   * Zincirli eylemlerde bu alan kullanılmaz — orada özet ÖLÇÜLEN sayıyla kurulur.
   */
  readonly basariMetni: string;
}

export const ISLEM_KUNYELERI: Record<IslemEylemi, EylemKunyesi> = {
  iptal: {
    kimlik: "hafiza-islem-iptal",
    etiket: "İptal et",
    baslik: "Bekleyen iş iptal edilsin mi?",
    ne: "Sıradaki iş iptal edilir ve çalışmaya hiç başlamaz.",
    geriAlinabilir: true,
    butce: false,
    yikici: false,
    uygula: "İptal et",
    basariMetni: "Bekleyen iş iptal edildi",
  },
  "yeniden-dene": {
    kimlik: "hafiza-islem-yeniden-dene",
    etiket: "Yeniden dene",
    baslik: "İş yeniden kuyruğa alınsın mı?",
    ne: "Düşmüş iş yeniden sıraya konur ve baştan çalışır.",
    geriAlinabilir: true,
    butce: true,
    yikici: false,
    uygula: "Yeniden dene",
    basariMetni: "İş yeniden kuyruğa alındı",
  },
  sil: {
    kimlik: "hafiza-islem-sil",
    etiket: "Kaydı sil",
    baslik: "İşlem kaydı silinsin mi?",
    ne: "İşin kaydı listeden kalıcı olarak silinir; işin ürettiği kayıtlara dokunulmaz.",
    geriAlinabilir: false,
    butce: false,
    yikici: true,
    uygula: "Sil",
    basariMetni: "İşlem kaydı silindi",
  },
};

export const KURTARMA_KUNYESI: EylemKunyesi = {
  kimlik: "hafiza-konsolidasyon-kurtar",
  etiket: "Hepsini yeniden dene",
  baslik: "Düşen birleştirmeler yeniden denensin mi?",
  ne:
    "Bu bankadaki düşen birleştirmelerin düşme işareti temizlenir, sonra birleştirme " +
    "işi kuyruğa alınır.",
  geriAlinabilir: true,
  butce: true,
  yikici: false,
  uygula: "Yeniden dene",
  basariMetni: "Düşen birleştirmeler yeniden denenmek üzere kuyruğa alındı",
};

/* ---------------------------------------------------------------------------
   ÇAĞRILAR
   --------------------------------------------------------------------------- */

/** Bir işlem satırı eylemi. Gövde vekilin istediği iki alandır: banka ve kimlik. */
export async function islemUygula(
  eylem: IslemEylemi,
  bank: string,
  kimlik: string,
): Promise<YazmaSonucu> {
  const ad = ISLEM_KUNYELERI[eylem].etiket;
  const z = await hafizaYaz(`${UC_ISLEM}/${eylem}`, { bank, id: kimlik });
  if (!z.ok) return basarisiz(ad, z);
  return {
    ok: true,
    ozet: ISLEM_KUNYELERI[eylem].basariMetni,
    bacaklar: [bacak(ad, z)],
    eksik: null,
  };
}

/**
 * KURTARMA İKİ BACAKLIDIR — VE İKİNCİSİ ÜST YÜZEYDEN ÖLÇÜLDÜ.
 *
 * Üst servisin kurtarma ucu YALNIZ düşme işaretini temizler; işi kuyruğa ALMAZ.
 * Üst yüzey de bu yüzden kurtarmadan sonra ikinci bir çağrı yapıyor ve kendi
 * kodunda gerekçesini yazıyor. Tek bacakla bıraksaydık düğme "çalıştı" der ama
 * hiçbir şey kuyruğa girmezdi — operatör bunu ekrandan okuyamazdı.
 *
 * İKİNCİ BACAK VEKİLDE VAR (ölçüldü 2026-09-03): tetikleme ucu 11-A düzeltme
 * turunda açıldı. Yine de bu bacağın DÜŞEBİLECEĞİ varsayılıyor ve beklenen
 * arıza artık "uç yok" değil ÜST SERVİSİN KENDİSİ: birleştirme model çağrısı
 * üretir ve günlük ücretsiz hak dolduğunda 429 ile düşer — yani kısmi başarı
 * bu düğmenin en olası gerçek sonucudur, kenar durum değil. O yüzden sonuç
 * KISMİ BAŞARI olarak bildirilir ve pencerede KALIR: "tamam" demek, yapılmamış
 * bir işi yapılmış göstermek olurdu.
 *
 * KAÇ KAYIT KURTARILDIĞI BİLİNMİYORSA İKİNCİ BACAK ATILMAZ: üst yüzey de
 * yalnız sayı sıfırdan büyükken tetikliyor. Sayı gelmediğinde "belki vardır"
 * diye tetiklemek, ölçülmemiş bir sayıyı varsaymak olurdu.
 */
export async function kurtarVeTetikle(bank: string): Promise<YazmaSonucu> {
  const AD1 = "Düşme işaretini temizleme";
  const AD2 = "Kuyruğa alma";

  const kurtar = await hafizaYaz(UC_KURTAR, { bank });
  if (!kurtar.ok) return basarisiz(AD1, kurtar);

  const sayac = sayi(sozluk(kurtar.govde)?.retried_count);
  if (sayac === null) {
    return {
      ok: true,
      ozet: "Düşme işareti temizlendi",
      bacaklar: [bacak(AD1, kurtar)],
      eksik:
        "Kaç kaydın kurtarıldığı bildirilmedi, bu yüzden kuyruğa alma çağrısı yapılmadı — " +
        "listeyi tazeleyip durumu gör",
    };
  }
  if (sayac === 0) {
    return {
      ok: true,
      ozet: "Kurtarılacak düşen kayıt çıkmadı (0 kayıt)",
      bacaklar: [bacak(AD1, kurtar)],
      eksik: null,
    };
  }

  /* İKİNCİ BACAK GÖVDESİZ GİDER — ÖLÇÜLDÜ, TAHMİN DEĞİL: üst yüzeyin istemcisi
     birleştirmeyi tetiklerken yalnız yöntem gönderiyor, gövde YOK. Vekil bir
     gözlem-kapsamı alanını beyaz listede tutuyor ama biz onu GÖNDERMİYORUZ:
     göndersek üst servisin kendi varsayılanını sessizce değiştirirdik. */
  const tetikle = await hafizaYaz(UC_TETIKLE, { bank });
  if (!tetikle.ok) {
    return {
      ok: true,
      ozet: `${sayac} kaydın düşme işareti temizlendi`,
      bacaklar: [bacak(AD1, kurtar), bacak(AD2, tetikle)],
      eksik: `Kuyruğa alma başarısız: ${tetikle.neden ?? "sunucu bir gerekçe bildirmedi"}`,
    };
  }

  /* "ZATEN KUYRUKTAYDI" AYRI BİR HÂLDİR: üst servis aynı işi ikinci kez
     açmıyor ve bunu bir alanla söylüyor. Onu yutmak, operatöre yeni bir iş
     başlattığını söylemek olurdu. Alan gelmediyse hiçbir şey EKLENMEZ. */
  const ayni = sozluk(tetikle.govde)?.deduplicated === true;
  return {
    ok: true,
    ozet: ayni
      ? `${sayac} kayıt kurtarıldı; birleştirme zaten kuyrukta olduğu için yeni iş açılmadı`
      : `${sayac} kayıt yeniden denenmek üzere kuyruğa alındı`,
    bacaklar: [bacak(AD1, kurtar), bacak(AD2, tetikle)],
    eksik: null,
  };
}

/* ---------------------------------------------------------------------------
   ONAY PENCERESİ — DÖRT EYLEMİN ORTAK YÜZEYİ
   --------------------------------------------------------------------------- */

/** Bir çağrının künyesi: adı, tuttu mu, hangi kodla. Kod ölçülemediyse SÖYLENİR. */
/**
 * ÜÇÜNCÜ HÂL: "ÇAĞRI GİTTİ, CEVABI OKUNAMADI" (nihai inceleme Ö3, 2026-09-03).
 *
 * Vekilin `_hafiza_yaz` sözleşmesi şunu BEYAN ediyor: "`ok:false` yalnız
 * 'cevabını kullanamadım' demektir" ve "UI bunu 'olmadı' diye çizemez". Bu satır
 * o yükümlülüğü yerine getirmiyordu: `b.ok ? "tuttu" : "tutmadı"` iki hâl
 * çiziyordu, ayrı dal YALNIZ `http === null` içindi. Ulaşılabilir üçüncü hâl
 * şudur — upstream 204/boş gövde döner, `http` 2xx kalır, `ok` False olur:
 * operatör "tutmadı" okur ve TEKRAR BASAR. `sil`de bu, dalın kendi adlandırdığı
 * GERİ ALINAMAZ çift-gönderim sınıfıdır.
 *
 * BAŞARI RENGİ JETONDAN (K-5, Rol-1 hükmü): burada `emerald-*` vardı — bu dalda
 * doğan yeni bir palet kaynağı. Gece yeni bir jeton DOĞMAZ; renk `ISLEM_DURUM_RENGI`
 * hangi rampayı kullanıyorsa oradan okunur (`completed` → `var(--color-seri-9)`).
 *
 * BEDEL ÖLÇÜLDÜ VE ÖDENDİ (bedel yasası, düzeltme turu 2 Y-8): `--seri-9` CAMGÖBEĞİdir
 * (light `cyan-600` / dark `cyan-400`) ve AYNI jeton `takimyildizi.tsx::JETONLAR`da bir
 * graf KÜMESİNİ boyuyor. Kazanç: yeni bir palet kaynağı doğmadı ve renk tema duyarlı kaldı.
 * Kayıp: "başarı" ile bir graf kümesi aynı hue'ya oturdu ve YEŞİLİN EVRENSEL OKUMASI gitti —
 * operatör bu satırı artık renkten değil METİNDEN okuyor ("tuttu"). Kalıcı çare bir palet
 * kararıdır (rezerve hue bandı: mod/nav/şiddet gibi "başarı" da bant ister); o karar
 * operatörün palet turuna aittir, gece verilmez.
 */
function BacakSatiri({ b }: { readonly b: YazmaBacagi }) {
  const kodOlculdu = b.http !== null;
  const cevapsizBasari = !b.ok && kodOlculdu && b.http >= 200 && b.http < 300;
  return (
    <div className="flex items-baseline justify-between gap-3 border-b py-1 last:border-b-0">
      <span className="shrink-0 text-xs">{b.ad}</span>
      <span className="min-w-0 text-right">
        <span
          className={cn(
            "text-xs",
            b.ok ? "text-[var(--color-seri-9)]" : cevapsizBasari ? "text-foreground" : "text-destructive",
          )}
        >
          {b.ok ? "tuttu" : cevapsizBasari ? "çağrı gitti, cevabı okunamadı" : "tutmadı"}
        </span>
        <span className="ml-2 text-[11px] text-muted-foreground">
          {b.http === null ? (
            <Olculemedi
              neden="durum kodu ölçülemedi"
              teknik="yanıt hiç gelmedi ya da kod taşımıyor — sıfır yazmak bir kod uydurmak olurdu"
              kisa
            />
          ) : (
            `durum kodu ${b.http}`
          )}
        </span>
        {cevapsizBasari ? (
          <span className="mt-0.5 block text-[11px] leading-4">
            TEKRAR BASMA — üst servis {b.http} döndü, yani istek ULAŞTI; okunamayan şey yalnız cevabın gövdesi.
          </span>
        ) : null}
        {b.neden !== null ? (
          <span className="mt-0.5 block text-[11px] text-destructive leading-4">{b.neden}</span>
        ) : null}
      </span>
    </div>
  );
}

export function YazmaOnayi({
  kunye,
  hedef,
  hedefEtiketi = "Uygulanacağı kayıt",
  ikon: Ikon,
  calistir,
  basarili,
  kisa = false,
  engel = null,
}: {
  readonly kunye: EylemKunyesi;
  /** Eylemin uygulanacağı şeyin operatöre görünen adı; ölçülemediyse `null`. */
  readonly hedef: string | null;
  /** Hedefin NE OLDUĞU — bir işlem satırı ile bir bankanın tamamı aynı kelimeyle
   *  anlatılamaz; onay penceresinin en önemli satırı budur. */
  readonly hedefEtiketi?: string;
  readonly ikon?: ComponentType<{ readonly className?: string }>;
  /** İsteği atan çağrı — sonucu ZARFTAN kurar, uydurmaz. */
  readonly calistir: () => Promise<YazmaSonucu>;
  /** Durum DEĞİŞTİKTEN sonra çağrılır: listeyi/sayaçları yeniden okumak çağıranın işi. */
  readonly basarili: () => void;
  /** Tablo satırında küçük düğme. */
  readonly kisa?: boolean;
  /** Düğme neden basılamıyor; basılabiliyorsa `null`. */
  readonly engel?: string | null;
}) {
  const [acik, setAcik] = useState(false);
  const [ucusta, setUcusta] = useState(false);
  const [sonuc, setSonuc] = useState<YazmaSonucu | null>(null);
  /* KİLİDİN GERÇEK HATTI BİR REF'TİR (inceleme bulgusu M-3). `ucusta` bir
     `useState` FOTOĞRAFIdır: aynı tikte gelen iki tıklama ikisi de `false`
     görürdü ve "iki hatlı kilit" iddiası tek hatta inerdi. Ref anında yazılır,
     yani ikinci çağrı gerçekten kapıdan döner; `ucusta` ise ÇİZİM içindir
     (düğme kilidi + iğ). İki hat iki AYRI şey ölçüyor, biri ötekinin kopyası
     değil. */
  const kilit = useRef(false);

  async function uygula() {
    if (kilit.current) return;
    kilit.current = true;
    setUcusta(true);
    setSonuc(null);
    let s: YazmaSonucu;
    try {
      s = await calistir();
    } catch (e) {
      // İSTİSNA YUTULMAZ: çağrı katmanı fırlatmıyor, ama fırlatsaydı sessiz bir
      // "hiçbir şey olmadı" hâli doğardı — mesaj ekrana çıkar.
      s = {
        ok: false,
        ozet: "",
        bacaklar: [
          {
            ad: kunye.etiket,
            ok: false,
            http: null,
            neden: `İstek gönderilemedi: ${e instanceof Error ? e.message : String(e)}`,
          },
        ],
        eksik: null,
      };
    } finally {
      kilit.current = false;
      setUcusta(false);
    }

    if (!s.ok) {
      // HİÇBİR ŞEY DEĞİŞMEDİ: pencere açık kalır, gerekçe okunmadan kaybolmaz.
      setSonuc(s);
      return;
    }

    /* BURAYA GELEN HER HÂLDE DURUM DEĞİŞTİ — kısmi başarıda da. Kurtarma tuttuğu
       hâlde tetikleme düşse bile düşme işaretleri temizlenmiştir; okumaları
       tazelememek, değişmiş bir gerçeği eski sayılarla göstermek olurdu. */
    setSonuc(s);
    basarili();

    if (s.eksik !== null) {
      /* KISMİ BAŞARI PENCEREDE KALIR (I-2): en nüanslı mesaj dört saniyelik bir
         bildirime emanet edilemez. Bildirim yalnız TEK SATIR özet taşır;
         ayrıntı — iki bacağın kodları ve gerekçesi — pencerede durur. */
      toast.warning(s.ozet);
      return;
    }
    setAcik(false);
    setSonuc(null);
    toast.success(s.ozet);
  }

  const kismi = sonuc !== null && sonuc.ok && sonuc.eksik !== null;
  const dustu = sonuc !== null && !sonuc.ok;

  return (
    <>
      <Button
        type="button"
        variant={kisa ? "ghost" : "outline"}
        size="sm"
        className={cn(kisa && "h-7 px-2 text-xs", kunye.yikici && "hover:text-destructive")}
        disabled={engel !== null}
        title={engel ?? `${kunye.ne} Uygulamadan önce onay sorulur.`}
        onClick={() => {
          setSonuc(null);
          setAcik(true);
        }}
      >
        {Ikon ? <Ikon className="size-3" /> : null}
        {kunye.etiket}
        {/* GEREKÇE FAREYE DEĞİL ADA BAĞLIDIR (`parcalar.tsx::Faz2Dugme` kuralı,
            inceleme bulgusu M-6): devre dışı bir düğme odak alamaz, `title`
            ipucu da çoğu tarayıcıda bastırılır — yani engelin nedeni klavyeyle
            HİÇ okunamazdı. Neden artık düğmenin ERİŞİLEBİLİR ADININ parçası. */}
        {engel !== null ? <span className="sr-only"> — {engel}</span> : null}
      </Button>

      <AlertDialog
        open={acik}
        onOpenChange={(a) => {
          /* UÇUŞTA KAPANMAZ: kapansaydı istek yolda kalır ve sonucu okuyan
             kimse olmazdı. Kaçış tuşu da aynı kapıdan geçer. */
          if (ucusta) return;
          setAcik(a);
          if (!a) setSonuc(null);
        }}
      >
        <AlertDialogContent
          className="max-w-md sm:max-w-md"
          onEscapeKeyDown={(e) => {
            if (ucusta) e.preventDefault();
          }}
        >
          <AlertDialogHeader>
            <AlertDialogTitle>{kismi ? "İşin bir kısmı yapılmadı" : kunye.baslik}</AlertDialogTitle>
            <AlertDialogDescription>{kismi ? sonuc.ozet : kunye.ne}</AlertDialogDescription>
          </AlertDialogHeader>

          <div className="flex flex-col gap-3 text-sm">
            <div className="flex items-baseline justify-between gap-4 border-b py-1.5">
              <span className="shrink-0 text-muted-foreground text-xs">{hedefEtiketi}</span>
              {hedef === null ? (
                <Olculemedi
                  neden="Hedef okunamadı"
                  teknik="eylemin uygulanacağı kaydın kimliği gelmedi — hedefsiz istek gönderilmez"
                  kisa
                />
              ) : (
                <span className="truncate font-mono text-xs" title={hedef}>
                  {hedef}
                </span>
              )}
            </div>

            {kismi ? null : (
              <p className={cn("text-xs", kunye.geriAlinabilir ? "text-muted-foreground" : "text-destructive")}>
                {kunye.geriAlinabilir
                  ? "Geri alınabilir: aynı kayıt daha sonra yeniden denenebilir ya da yeniden düşebilir."
                  : "GERİ ALINAMAZ: silinen kayıt panodan da üst servisten de geri getirilemez."}
              </p>
            )}

            {kunye.butce && !kismi ? (
              <p className="flex items-start gap-1.5 rounded-md border border-uyari-h bg-uyari-t p-2 text-uyari text-xs">
                <TriangleAlert className="mt-0.5 size-3 shrink-0" aria-hidden />
                <span>{BUTCE_UYARISI}</span>
              </p>
            ) : null}

            {kismi ? (
              /* KISMİ BAŞARI BLOĞU — kehribar, çünkü ne yeşil ne kırmızı: bir
                 kısmı oldu. Düz cümle önce, bacak künyeleri sonra. */
              <div
                className="flex flex-col gap-1 rounded-md border border-uyari-h bg-uyari-t p-2"
                role="status"
                aria-live="polite"
              >
                <span className="text-uyari text-xs leading-4">{sonuc.eksik}</span>
                <div className="mt-1">
                  {sonuc.bacaklar.map((b) => (
                    <BacakSatiri key={b.ad} b={b} />
                  ))}
                </div>
              </div>
            ) : null}

            {dustu ? (
              <div
                className="flex flex-col gap-1 rounded-md border border-destructive/40 bg-destructive/5 p-2"
                role="alert"
                aria-live="assertive"
              >
                <span className="font-medium text-destructive text-xs">Eylem uygulanmadı</span>
                <div>
                  {sonuc.bacaklar.map((b) => (
                    <BacakSatiri key={b.ad} b={b} />
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <AlertDialogFooter>
            {/* VAZGEÇ ÖNCE VE ODAKTA: bu pencere açılınca odak vazgeçme
                düğmesine düşer, yani boşuna basılan bir giriş tuşu YIKICI
                eylemi değil vazgeçmeyi çalıştırır. Onay düğmesi bilerek
                gönderim düğmesi (`submit`) değildir — bir form içinde
                olsaydı giriş tuşu onu tetiklerdi. */}
            <AlertDialogCancel disabled={ucusta}>{kismi ? "Kapat" : "Vazgeç"}</AlertDialogCancel>
            <Button
              type="button"
              variant={kunye.yikici ? "destructive" : "default"}
              disabled={ucusta || hedef === null}
              onClick={() => void uygula()}
            >
              {ucusta ? <Loader2 className="size-3.5 animate-spin" aria-hidden /> : null}
              {ucusta ? "Uygulanıyor…" : kismi ? "Yeniden dene" : kunye.uygula}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
