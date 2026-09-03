"use client";

/* ============================================================================
   ANALİZ YÜZEYİNİN ORTAK PARÇALARI — üç hâl kapısı + dürüst sayı basımı
   ----------------------------------------------------------------------------
   BU DOSYANIN VAR OLMA NEDENİ TEK: "ölçülemedi" ile "sıfır" bu yüzeyde ASLA aynı
   piksele düşmesin. Yüzey altı bileşene bölündü ve her biri kendi kartında sayı
   basıyor; kural her dosyada yeniden yazılsaydı biri unutur, o kart sessizce 0
   yazardı — ve 0, okuyucuya "ölçtük, sonuç bu" der.

   `Kapi` ÜÇ HÂLİ AYRI KARŞILAR (veri.ts'in sözleşmesi): yükleniyor / okunamadı /
   oturum düştü. Dördüncü bir hâl daha var ve o da burada: ELDE ESKİ VERİ VARKEN
   tazeleme düşmüş. O durumda kart boşaltılmaz (bir ağ hıçkırığında ekrandaki her
   sayı kaybolurdu) ama TAZE de sayılmaz — üstüne bayat şeridi çizilir.
   ============================================================================ */
import { LockKeyhole, TriangleAlert } from "lucide-react";

import { Bildiri } from "../../parcalar/bildiri";
import { BayatSerit, YukleniyorIskeleti } from "../../parcalar/bayat";
import { type AdEki, kapiKur } from "../../parcalar/kapi";
import { olculemediKur } from "../../parcalar/olculemedi";

/* ---- SAYI BASIMI --------------------------------------------------------- */

// Intl örneği pahalı; basamak başına bir kez kurulur. (Ölçüm değil, bilinen maliyet.)
const BICIMLER = new Map<string, Intl.NumberFormat>();

function bicim(basamak: number, isaretli: boolean): Intl.NumberFormat {
  const anahtar = `${basamak}|${isaretli}`;
  let b = BICIMLER.get(anahtar);
  if (!b) {
    b = new Intl.NumberFormat("tr-TR", {
      minimumFractionDigits: basamak,
      maximumFractionDigits: basamak,
      signDisplay: isaretli ? "exceptZero" : "auto",
    });
    BICIMLER.set(anahtar, b);
  }
  return b;
}

/** Sayıysa biçimlenmiş dizge, DEĞİLSE `null`. `null` dönüşü çağıranı "ölçülemedi"
 *  yazmaya ZORLAR — burada "—" ya da "0" döndürmek yasağın tam ihlali olurdu. */
export function sayi(v: unknown, basamak = 2, isaretli = false): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return bicim(basamak, isaretli).format(v);
}

/** Oran (0..1) → yüzde. Türkçe biçimde işaret ÖNDE: `%61,4`. */
export function yuzde(v: unknown, basamak = 1, isaretli = false): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  const s = bicim(basamak, isaretli).format(v * 100);
  return s.startsWith("-") ? `-%${s.slice(1)}` : `%${s}`;
}

/** R katı — defterin kendi birimi, bu yüzden ayrı bir basım. */
export function rKati(v: unknown, basamak = 2): string | null {
  const s = sayi(v, basamak, true);
  return s === null ? null : `${s}R`;
}

export function para(v: unknown): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return `$${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(v)}`;
}

/** Kâr/zarar rengi. `null`/0 için NÖTR: sıfırı yeşile boyamak "kazandık" der. */
export function pnlRengi(v: unknown): string {
  if (typeof v !== "number" || !Number.isFinite(v) || v === 0) return "text-foreground";
  return v > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400";
}

/* ---- ÖLÇÜLEMEDİ ----------------------------------------------------------
   TANIM BURADA DEĞİL (TSK-121, 2026-09-03): tek kaynak `parcalar/olculemedi.tsx`. Bu yüzeyin
   iki gövdesi (blok + satır-içi) "hucre" ailesinin iki `bicim`i — `Olculemedi` blok-biçimli,
   `OlculemediHucre` satır-içi; `ogrenme/ortak.tsx` bu ailenin diğer üyesi (blok'ta teknik-
   koşullu altçizgi EK DALI taşır, burada taşımaz — `altCizgiTeknikte: false`). */

/** Blok biçimi: nedeni GÖRÜNÜR yazar. Kart gövdesinde kullanılır. */
export const Olculemedi = olculemediKur("hucre", { bicim: "blok", altCizgiTeknikte: false });

/** Satır-içi biçim: dar hücrede nedeni `title` ile taşır (noktalı altı çizgi =
 *  "üstüne gel"). Nedeni tamamen düşürmek yasak; yalnız yerleşimi değişir. */
export const OlculemediHucre = olculemediKur("hucre", { bicim: "satirici", altCizgiTeknikte: false });

/** Sayı varsa yazar, yoksa `neden`i taşıyan "ölçülemedi" basar. */
export function Deger({
  metin,
  neden,
  teknik,
  className,
}: {
  metin: string | null;
  neden: string;
  teknik?: string;
  className?: string;
}) {
  if (metin === null) return <OlculemediHucre neden={neden} teknik={teknik} />;
  return <span className={className}>{metin}</span>;
}

/* ---- ÜÇ (DÖRT) HÂL KAPISI ------------------------------------------------
   `Bildiri`/`YukleniyorIskeleti`/`BayatSerit` TANIMLARI BURADA DEĞİL (TSK-121, 2026-09-03):
   tek kaynak `parcalar/bildiri.tsx` ve `parcalar/bayat.tsx` — üçü de yukarıda ithal edilir. */

/** Yükleniyor / okunamadı / oturum düştü / bayat-ama-var — dördü AYRI çare ister.
 *  TANIM BURADA DEĞİL (TSK-113, 2026-09-03): yedi yüzey aynı `Kapi<T>` gövdesini kopyalıyordu.
 *  KARAR tek kaynakta (`parcalar/kapi.tsx`), ÇİZİM burada — bu yüzeyin metinleri kendisinindir,
 *  sıra ortaktır. `bayat` verildiği için hata veriyi EZMEZ: veri varken şerit olur (A ailesinin
 *  `Alert` kapıları bunun tersini yapar ve bu ayrım kabuktan türetilir). */
export const Kapi = kapiKur<AdEki>({
  oturum: ({ ad }) => (
    <Bildiri
      ikon={LockKeyhole}
      tonu="notr"
      baslik="Oturum düştü"
      metin={`${ad} okunamıyor: sunucu 401 döndü. Bu bir veri arızası DEĞİL — yeniden giriş gerekiyor.`}
    />
  ),
  bos: (hata, { ad }) => (
    <Bildiri
      ikon={TriangleAlert}
      tonu="uyari"
      baslik={`${ad} okunamadı`}
      metin={hata ?? `${ad} boş gövde döndürdü — çizilecek bir şey yok ve nedeni uçtan gelmedi.`}
    />
  ),
  iskelet: ({ yukseklik }) => <YukleniyorIskeleti yukseklik={yukseklik} />,
  bayat: (hata, zaman) => <BayatSerit hata={hata} zaman={zaman} />,
});
