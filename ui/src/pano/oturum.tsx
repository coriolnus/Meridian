"use client";

/* ============================================================================
   OTURUM — `/api/session` TEK yerden çekilir, ve panonun HANGİ YÜZÜNÜ
   göstereceğine burada karar verilir
   ----------------------------------------------------------------------------
   NEDEN BU DOSYA DOĞDU (2026-09-01). Kapı dallanması kabuk seviyesine çıktı:
   kimliksiz ziyaretçi kabuğu HİÇ görmüyor, tam-ekran kapıyı görüyor. O karar
   `App.tsx`te veriliyor, aynı gövdenin ayrıntısı ise Giriş yüzeyinde çiziliyor —
   yani `/api/session` iki okuyucu kazandı. İki `useApi` açmak İKİ AYRI NABIZ ve
   iki ayrı AN demekti: kapı "oturum açık" derken yüzey bir önceki saniyenin
   "kapalı"sını gösterebilirdi (`durum.tsx`teki `/api/today` gerekçesinin aynısı).
   Tek gövde, tek nabız, tek an.

   HÂL SINIFLAMASI DA TEK KAYNAKTIR — `hali()`. İki yerde `password_set === false`
   yazsaydık, kural değiştiğinde biri sessizce eski kararı vermeye devam ederdi
   (tek-kaynak yasası, CLAUDE.md §4). Sıralama Giriş yüzeyindeki özgün makineden
   AYNEN korundu: önce alan VARLIĞI, sonra kurulum, sonra açık oturum.

   `undefined` `false` SAYILMAZ: parolası kurulu bir sisteme "ilk parolanı belirle"
   ekranı göstermek 409'a koşan bir yalan olurdu. Alanlar gelmediğinde hiçbir ekran
   seçilmez — ne kabuk ne kapı — ve seçilemediği YAZILIR.
   ============================================================================ */
import { createContext, use, useCallback, useEffect, useState, type ReactNode } from "react";

import { NABIZ_MS, useApi, type Durum } from "./veri";
import type { OturumGovdesi } from "./yuzeyler/kimlik/uctipleri";

/**
 * `/api/session` gövdesinin BEŞ hâli. Üçü ucun söylediği karar hâlleri, ikisi
 * ölçümün kendi hâlleri — ve ikinci ikisi birinci üçe KARIŞTIRILMAZ:
 *   okunmadi   → gövde henüz elimizde yok (yükleniyor ya da istek düştü)
 *   olculemedi → gövde geldi ama karar alanları YOK
 *   kurulum    → parola hiç kurulmamış
 *   giris      → parola kurulu, oturum kapalı
 *   acik       → oturum açık
 */
export type OturumHali = "okunmadi" | "olculemedi" | "kurulum" | "giris" | "acik";

/**
 * SINIFLAYICI — SAF FONKSİYON, İKİ GİRDİ. Hook yok, yan etki yok, `Date.now()` yok:
 * aynı iki girdi her zaman aynı hâli verir. Bu bir üslup tercihi değil, bu dosyanın
 * tek sınanabilir yüzeyi olması: `ui/` tarafında bir test koşucusu yok (2026-09-02),
 * o yüzden sözleşme AŞAĞIDAKİ TABLODA yazılı ve fonksiyon tablodan okunacak kadar
 * düz tutuluyor. Koşucu geldiği gün tablo doğrudan bir parametreli teste dönüşür.
 *
 * `oturumDustu` NEDEN GİRDİ (düzeltme-2, 2026-09-02 — görev incelemesi bulgusu):
 * `useApi` 401'i AYRI bir bayrakta taşıyor ve hata hâlinde ESKİ VERİYİ SİLMİYOR
 * (`veri.ts`: silmek bir ağ hıçkırığında ekrandaki her sayıyı boşaltırdı). Sınıflayıcı
 * yalnız gövdeye baksaydı şu olurdu: ilk okuma `authenticated:true` der, sonra
 * `/api/session` anormal biçimde 401 dönmeye başlar, bayrak kalkar — ama bayat gövde
 * hâlâ "acik" dedirtir ve KİMSE bir şey göstermez. Bayrak ekranı taşımayan bir
 * ölçüm olurdu; YASA 6'nın tam karşılığı (okuyucusu olmayan yazım).
 *
 * GİRDİ → ÇIKTI TABLOSU (sıra bağlayıcıdır, satırlar YUKARIDAN AŞAĞI okunur):
 *
 *   #  veri            password_set  authenticated  oturumDustu  →  hâl
 *   1  null            —             —              —            →  okunmadi
 *   2  var             undefined     herhangi       —            →  olculemedi
 *   2  var             herhangi      undefined      —            →  olculemedi
 *   3  var             false         herhangi       herhangi     →  kurulum
 *   4  var             true          herhangi       TRUE         →  giris     ← bayrak ezer
 *   5  var             true          true           false        →  acik
 *   6  var             true          false          false        →  giris
 *
 * SIRANIN İKİ GEREKÇESİ VAR ve ikisi de ölçülmüş bir yanlışı önlüyor:
 *   · 3 > 4: parolası KURULMAMIŞ bir sistemde 401 görmek, giriş formu göstermek
 *     için gerekçe DEĞİLDİR — kullanıcının gireceği bir parola yok. O hâlde kapı
 *     kurulum ekranında kalır; 401 orada bir sunucu arızasıdır, bir kimlik hâli değil.
 *   · 4 > 5: bayrak bayat gövdeyi EZER. Tersi sırada 401 sessizce yutulurdu — bu
 *     düzeltmenin doğduğu kusurun ta kendisi.
 *
 * 1. SATIR BAYRAĞI OKUMAZ ve bu bilinçli: hiç başarılı okuma yokken gelen 401,
 * "oturumun düştü" demek için yeterli değil — parolanın kurulu OLUP OLMADIĞINI bile
 * bilmiyoruz, dolayısıyla giriş formu da kurulum formu da bir tahmin olurdu. O hâl
 * `okunmadi` olarak kalır ve kapı 401'i nedeniyle birlikte yazar.
 */
export function hali(v: OturumGovdesi | null, oturumDustu: boolean): OturumHali {
  if (v === null) return "okunmadi";
  if (v.password_set === undefined || v.authenticated === undefined) return "olculemedi";
  if (v.password_set === false) return "kurulum";
  if (oturumDustu) return "giris";
  if (v.authenticated === true) return "acik";
  return "giris";
}

export interface OturumBaglami {
  /** Ham okuma — dört hâli (yükleniyor/hata/oturum düştü/veri) olduğu gibi taşır. */
  readonly durum: Durum<OturumGovdesi>;
  /** Yukarıdaki gövdenin sınıflanmış hâli. Ekran seçimi YALNIZ buradan yapılır. */
  readonly hal: OturumHali;
  /**
   * Bu SEKMEDE daha önce açık bir oturum ÖLÇÜLDÜ mü — "oturum düştü" ile "hiç
   * girmedin" ayrımının tek dayanağı. Sunucu bunu bilmiyor ve bilemez: kapanan
   * bir çerezin arkasında "süre doldu" mu "hiç yoktu" mu olduğunu ayırt eden bir
   * uç yok. Yeni bir sekme bu ayrımı yapamaz ve ekran yapabildiğini iddia etmez.
   */
  readonly onceAcikti: boolean;
  /**
   * Bu sekmedeki girişin `expires_in`i — oturum ÖMRÜNÜN tek ölçülen kaynağı.
   * KABIN ÜSTÜNDE DURUYOR ve bu bir kaza değil: 2026-09-01'den önce ölçüm giriş
   * formunun bağlı olduğu yüzeyin YEREL durumundaydı; kapı tam-ekrana çıkınca o
   * bileşen giriş başarılı olur olmaz SÖKÜLÜYOR ve ölçüm onunla birlikte
   * kaybolurdu. Kapının bedeli sessizce ödenmesin diye ömür buraya taşındı —
   * künyeyi çizen kabuk içi yüzey aynı sayıyı okumaya devam ediyor.
   * Giriş yapılmadıysa `null`: ölçülmedi, sıfır değil.
   */
  readonly omurS: number | null;
  /** Giriş başarılı olduğunda ölçülen `expires_in`i kaydeder (ölçülemediyse `null`). */
  readonly omurBildir: (saniye: number | null) => void;
  /** Operatör BİLEREK çıktı — bir düşme değil. Çağıran: Giriş yüzeyindeki çıkış düğmesi. */
  readonly cikisBildir: () => void;
}

const Baglam = createContext<OturumBaglami | null>(null);

export function OturumSaglayici({ children }: { children: ReactNode }) {
  const durum = useApi<OturumGovdesi>("/api/session", NABIZ_MS);
  const [onceAcikti, setOnceAcikti] = useState(false);
  const [omurS, setOmurS] = useState<number | null>(null);

  // İZ GÖVDEDEN DÜŞER, ZAMANLAYICIDAN DEĞİL: yalnız gerçekten `authenticated:true`
  // OKUDUĞUMUZDA işaretleniyor. "Giriş isteği 200 döndü" yetmez — çerezin gerçekten
  // yerleştiğini söyleyen tek şey bir sonraki `/api/session` gövdesidir.
  useEffect(() => {
    if (durum.veri?.authenticated === true) setOnceAcikti(true);
  }, [durum.veri]);

  const omurBildir = useCallback((saniye: number | null) => setOmurS(saniye), []);
  // BİLEREK ÇIKIŞ İKİ ŞEYİ BİRDEN SIFIRLAR: iz de ölçüm de O oturuma aitti.
  // İzi bırakmak, çıkış yapan operatöre "oturumun düştü" demek olurdu — düşmedi,
  // kapattı. Ömrü bırakmak ise biten bir oturumun süresini canlıymış gibi okutmak.
  const cikisBildir = useCallback(() => {
    setOnceAcikti(false);
    setOmurS(null);
  }, []);

  const deger: OturumBaglami = {
    durum,
    hal: hali(durum.veri, durum.oturumDustu),
    onceAcikti,
    omurS,
    omurBildir,
    cikisBildir,
  };
  return <Baglam value={deger}>{children}</Baglam>;
}

export function useOturum(): OturumBaglami {
  const b = use(Baglam);
  if (!b) throw new Error("OturumSaglayici yok — kapı ve kabuk onun içinde doğmalı");
  return b;
}
