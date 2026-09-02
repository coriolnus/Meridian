"use client";

/* ============================================================================
   KARAR ARŞİVİ OKUYUCUSU — "hangi hüküm hangi turda verildi?"
   ----------------------------------------------------------------------------
   Meridian'ın kendi karar ve hüküm belgelerinin künyesi. Bir zamanlar kendi
   yüzeyi vardı ("Belgeler" rafı); operatör kararı 2026-09-02 o yüzeyi kaldırdı
   ve künyeyi Hafıza yüzeyinin Belgeler görünümüne BİRLEŞTİRDİ — o dosyalar
   hafıza bankasına zaten işlenmiş durumda ve iki ayrı sayfada iki ayrı liste,
   aynı belgeleri iki kez göstermek olurdu.

   UCUN SÖZLEŞMESİNİ BİLEN TEK YER BURASI: okuma iki yere bölünseydi aynı uç iki
   kez çağrılır ve iki ekran iki farklı anın sayısını gösterirdi. Kanca tek çağrı
   verir; çağıran hem ham durumu (yükleniyor / oturum düştü / hata) hem çözülmüş
   gövdeyi alır. İkisini ayırmak, "okunuyor" ile "okundu ama boş" ayrımını
   çağırana yeniden kurdururdu.

   UCUN DOKUZ ALANININ HEPSİ BURADA OKUNUR (Yasa 6) ve `ok` ile `dizin` de buna
   dahildir — ilk birleşme turunda ikisi üretilip okunmadı ve `ok:false` uyarısı
   ekrandan sessizce kalktı; sonuç, EKSİK bir arşivden "bankada yok" hükmü
   kurulabilmesiydi. Okuyucuları artık ekranda (`Belgeler.tsx` karar şeridi).

   HÂLÂ SUNULMAYAN, ve bu ÖLÇÜLEREK yazılıyor: belge GÖVDESİ. Uç yalnız künye
   döndürüyor, bir kararın metnini panodan okumak bugün mümkün değil. Uç
   kullanıcıdan hiçbir dize almıyor (api.py::api_karar_belgeleri, request dışında
   parametre yok) ve gövde sunumu geldiğinde o kapı bilerek yeniden açılacak —
   sessizce değil.

   NABIZ YOK: arşiv tur kapanışında insan eliyle yazılıyor. On beş saniyede bir
   çekmek, okunan bir listeyi altından kaydırmak olurdu.
   ============================================================================ */
import { useApi, type Durum as UcDurumu } from "../../veri";
import { metin, sayi, sozluk } from "./parcalar";

const ARSIV_UCU = "/api/karar-belgeleri";

export interface ArsivKaydi {
  readonly ad: string | null;
  readonly tarih: string | null;
  readonly baslik: string | null;
  readonly bayt: number | null;
  /** Uç ölçemediği alanın SEBEBİNİ buraya yazar; null = her şey ölçüldü. */
  readonly neden: string | null;
}

export interface Arsiv {
  /** Uç okumayı TAM bitirebildi mi. `false` = liste EKSİK olabilir — bu bayrak
   *  düşükken "bankada yok" gibi kapsayıcı hükümler kurulamaz. */
  readonly ok: boolean;
  readonly dizin: string | null;
  /** `null` = dizin AÇILAMADI. Boş liste ile aynı şey DEĞİL: boş liste "arşiv boş" der. */
  readonly belgeler: readonly ArsivKaydi[] | null;
  readonly hata: string | null;
}

function kayitOku(v: unknown): ArsivKaydi {
  const k = sozluk(v);
  if (k === null) {
    return {
      ad: null,
      tarih: null,
      baslik: null,
      bayt: null,
      neden: "uç, belgeler listesine nesne olmayan bir öğe koydu — künye okunamadı",
    };
  }
  return {
    ad: metin(k["ad"]),
    tarih: metin(k["tarih"]),
    baslik: metin(k["baslik"]),
    bayt: sayi(k["bayt"]),
    neden: metin(k["neden"]),
  };
}

/** Uç gövdesini tipe çevirir. Gövde nesne değilse `null` döner — çağıran "ölçülemedi"
 *  yazmak ZORUNDA kalır, boş bir tablo çizemez. */
function arsivOku(v: unknown): Arsiv | null {
  const g = sozluk(v);
  if (g === null) return null;
  const ham = g["belgeler"];
  return {
    ok: g["ok"] === true,
    dizin: metin(g["dizin"]),
    // ÜÇ HÂL AYRI: dizi → liste · null → dizin açılamadı · başka bir şey → sözleşme
    // ihlali. Üçüncüsünü boş diziye indirmek, ihlali "arşiv boş" diye okuturdu.
    belgeler: Array.isArray(ham) ? ham.map(kayitOku) : null,
    hata: metin(g["hata"]),
  };
}

/** Arşiv okuması. `etkin=false` iken HİÇ çağrı açılmaz — okuyucusu olmayan bir
 *  isteğin maliyeti bedavaya gitmesin (banka seçilemediğinde ekran zaten çizilmiyor). */
export function useArsiv(etkin: boolean): {
  durum: UcDurumu<Record<string, unknown>>;
  okunan: Arsiv | null;
} {
  const durum = useApi<Record<string, unknown>>(etkin ? ARSIV_UCU : null, 0);
  return { durum, okunan: arsivOku(durum.veri) };
}
