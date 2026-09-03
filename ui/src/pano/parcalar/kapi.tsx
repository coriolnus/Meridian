/**
 * kapi.tsx — ÜÇ/DÖRT HÂL KAPISININ TEK TANIMI (TSK-113, 2026-09-03).
 *
 * ÖLÇÜM: yedi yüzey dosyası kendi `Kapi<T>` gövdesini taşıyordu (sistem/kuyruk/kimlik/yetki
 * `parcalar.tsx` + ogrenme/ajan/analiz `ortak.tsx`; 36/35/36/34/40/57/40 satır, dört ayrı md5).
 * Tek-kaynak yasası (§4): aynı gerçeğin yedi kopyası sessizce ayrışır — TSK-110'un bayatlık
 * çaresi `veri.ts`te çözülmüştü ama kopyalar o çareyi HER BİRİ ayrı yorumlayabilirdi.
 *
 * KOPYALAR AYNI ŞEY DEĞİLDİ — İKİ DURUM MAKİNESİ ÖLÇÜLDÜ:
 *   A ailesi (sistem/kuyruk/kimlik/yetki): `Alert` kabuğu, etiket `yol`. `hata !== null` VERİYİ
 *     EZER — bu yüzeylerde bayat gövde HİÇ çizilmez. İskelet `veri === null` ile.
 *   B ailesi (ogrenme/analiz/ajan): `Bildiri` kabuğu, etiket `ad`. `hata` yalnız VERİ YOKKEN
 *     kart olur; veri varken BAYAT ŞERİDİ olur. İskelet `veri === null && yukleniyor` ile.
 *
 * TASARIM — KARAR TEK YERDE, ÇİZİM YÜZEYDE: `kapiKur` bir kabuk (`KapiKabugu`) alır ve bağlı bir
 * `Kapi` döndürür. Hiçbir yüzeyin EKRANI DEĞİŞMEZ; değişen tek şey kararın nerede verildiğidir.
 * İki durum makinesi TEK sıraya indi ve aradaki tek ayrım BEYANLI + TÜRETİLMİŞTİR:
 * `kabuk.bayat === null` ⇒ bu yüzeyin bayat şeridi YOKTUR ⇒ hata veriyi ezer. Elle bir
 * `aile: "A" | "B"` bayrağı OLSAYDI iki gerçek (kabuk + bayrak) sessizce ayrışabilirdi — tam
 * kapatmaya çalıştığımız sınıf. Çivi: `tests/test_kovab_b12_v384.py`.
 *
 * BEYANLI BEDEL: (1) prop yüzeyi genişledi — `kuyruk`un kapısı artık `iskelet?` prop'unu da kabul
 * eder (eski gövdesinde yoktu; hiçbir çağrı yeri geçmiyor, çizim aynı). (2) Kabuk çizimleri hâlâ
 * yüzeylerde durur (`Bildiri`/`BayatSerit` kopyaları ogrenme/analiz/ajan'da) — o ayrı bir kalem,
 * bu dilimin kapsamı `Kapi`nin KARARIdır.
 */
import type { ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

import type { Durum } from "../veri";

/** Her kapının taşıdığı çekirdek — kabuktan bağımsız. */
export interface KapiCekirdegi<T> {
  readonly durum: Durum<T>;
  readonly children: (veri: T) => ReactNode;
}

/**
 * Bir yüzeyin ÇİZİM dili. `D` o yüzeyin kendi ek prop'ları (`{ yol, iskelet? }` ya da
 * `{ ad, yukseklik? }`) — kabuk çizerken tüm prop'ları görür, yani etiketi kendi adıyla okur.
 */
export interface KapiKabugu<D> {
  /** 401 — `hata`dan AYRI: çaresi yeniden giriştir, tazeleme değil. */
  readonly oturum: (ek: D) => ReactNode;
  /** Çizilecek veri YOK. `hata` uçtan geldiyse nedeni odur; gelmediyse `null`. */
  readonly bos: (hata: string | null, ek: D) => ReactNode;
  /** Veri henüz yok ama yolda — "0" değil iskelet. */
  readonly iskelet: (ek: D) => ReactNode;
  /**
   * Elde ESKİ veri var ve tazeleme düştü: çiz + damgala. `null` ise bu yüzey bayat gövde
   * çizemez ve hata veriyi EZER (A ailesi) — politika buradan TÜRETİLİR, ayrı bayrakla değil.
   */
  readonly bayat: ((hata: string, zaman: Date | null, ek: D) => ReactNode) | null;
}

/**
 * TEK TANIM. Verilen kabuğa bağlı bir `Kapi` bileşeni üretir.
 *
 * Sıra tek ve ortaktır; `bayatCizilebilir` iki ailenin farkını taşır:
 *   401 → (bayat çizilemiyorsa) hata → veri yok → (bayat varsa şerit) + çocuklar.
 */
export function kapiKur<D>(kabuk: KapiKabugu<D>) {
  return function Kapi<T>(o: KapiCekirdegi<T> & D): ReactNode {
    const { durum } = o;
    if (durum.oturumDustu) return <>{kabuk.oturum(o)}</>;

    const bayatCizilebilir = kabuk.bayat !== null;
    // A ailesi: bayat şeridi olmayan yüzeyde hata veriyi EZER — eski gövdeyi "taze" diye
    // okutmaktansa okunamadığını söylemek dürüsttür (dört kopyanın da ortak hükmüydü).
    if (!bayatCizilebilir && durum.hata !== null) return <>{kabuk.bos(durum.hata, o)}</>;

    if (durum.veri === null) {
      // YÜKLENİYOR ile BOŞ AYRI: veri henüz yokken iskelet çizilir, "0" değil. Boş bir tablo
      // "ölçtük, hiçbir şey yok" der ve bu, istek daha dönmeden söylenmiş bir yalandır.
      if (bayatCizilebilir && !durum.yukleniyor) return <>{kabuk.bos(durum.hata, o)}</>;
      return <>{kabuk.iskelet(o)}</>;
    }

    return (
      <>
        {durum.hata === null || kabuk.bayat === null ? null : kabuk.bayat(durum.hata, durum.zaman, o)}
        {o.children(durum.veri)}
      </>
    );
  };
}

/* ---- A AİLESİ: `Alert` kabuğu, etiket `yol` ------------------------------- */

export interface YolEki {
  /** Hangi uç — hata metninde operatöre nereye bakacağını söyler. */
  readonly yol: string;
  readonly iskelet?: ReactNode;
}

/**
 * sistem/kuyruk/kimlik/yetki yüzeylerinin ortak kabuğu.
 * @param oturumEki 401 cümlesinin sonuna eklenecek metin — `kimlik` yüzeyi " (Giriş yüzeyi)"
 *   diyordu. Dört gövde arasındaki TEK metin farkı buydu; kopya gerekçesi değil parametre.
 */
export function yolKabugu(oturumEki = ""): KapiKabugu<YolEki> {
  return {
    oturum: ({ yol }) => (
      <Alert variant="destructive">
        <AlertTitle>Oturum düştü</AlertTitle>
        <AlertDescription>
          {yol} 401 döndü. Bu bir ölçüm hatası değil — panoya yeniden giriş gerekiyor{oturumEki}.
        </AlertDescription>
      </Alert>
    ),
    bos: (hata) => (
      <Alert variant="destructive">
        <AlertTitle>Okunamadı</AlertTitle>
        <AlertDescription>{hata}</AlertDescription>
      </Alert>
    ),
    iskelet: ({ iskelet }) => iskelet ?? <Skeleton className="h-24 w-full" />,
    bayat: null,
  };
}

/** A ailesinin varsayılan bağı — sistem/kuyruk/yetki bunu doğrudan yeniden dışa aktarır. */
export const Kapi = kapiKur(yolKabugu());

/* ---- B AİLESİ: `Bildiri` kabuğu, etiket `ad` ------------------------------ */

export interface AdEki {
  /** Hangi ucun okunamadığı ekranda ADIYLA yazsın diye. */
  readonly ad: string;
  readonly yukseklik?: string;
}
