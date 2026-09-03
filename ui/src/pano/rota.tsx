/* ============================================================================
   YÖNLENDİRME — Next App Router'ın YERİNE, hash üstünde
   ----------------------------------------------------------------------------
   NEDEN HASH: pano TEK bir HTML dosyası olarak sunuluyor ve sunucusu FastAPI
   (`meridian/api.py`). Yol-tabanlı bir SPA yönlendirmesi, sunucuda "her yolu
   index'e düşür" kuralı ister; o kural `StaticFiles` montajına ya da bir
   yakala-hepsini rotasına dayanır ve ikisi de api.py'nin BİLEREK reddettiği şey
   (satır 650: montaj, dizine düşen her taslağı yayına açar). Hash sunucuya hiç
   gitmez — yönlendirme tamamen tarayıcıda kalır, sunum yüzeyi tek dosya olarak
   dar kalır.

   ESKİ YER İMLERİ KIRILMAZ: bugünkü pano `#bugun`, `#karar`, `#saglik` … yazıyor
   (app.js:682) ve RUNBOOK bağları, çekmece çipleri, operatörün yer imleri hep bu
   biçimde. Kanonik biçim AYNEN korunuyor; bölüm çapası `#alan/bolum` olarak
   EKLENİYOR — bugün çapa hash'e hiç yazılmıyordu (go() onu yutuyor), yani bu bir
   kayıp değil kazanç.

   ARAYÜZ BİLEREK NEXT'İNKİYLE AYNI ADLARI TAŞIR (`Link` / `usePathname` /
   `useRouter`): şablondan alınan kabuk bileşenleri bu üç adı çağırıyor. Aynı adı
   vermek, o dosyalarda yalnız import satırının değişmesi demek — gövdeye hiç
   dokunulmadı, yani şablonun bir sonraki sürümüyle fark almak hâlâ mümkün.
   ============================================================================ */
import { createContext, use, useCallback, useEffect, useMemo, useState } from "react";
import type { AnchorHTMLAttributes, ReactNode } from "react";

import {
  ROTA_TAKMA_ADLARI,
  VARSAYILAN_YUZEY,
  YUZEYLER,
  yuzeyYolu,
  type YuzeyAnahtari,
} from "./alanlar";

export interface Rota {
  /** `YUZEYLER`in anahtarı. Tanınmayan hash varsayılana düşer — 404 yok. */
  readonly yuzey: YuzeyAnahtari;
  /** Sayfa içi bölüm çapası; yoksa boş dizge. */
  readonly bolum: string;
  /** Şablon biçimli yol: `/dashboard/finance` ya da `/dashboard/finance/mutabakat`. */
  readonly yol: string;
  /**
   * HASH İÇİNDEKİ SORGU — bölümün ALTINDAKİ kademe. Yoksa boş nesne.
   *
   * NEDEN VAR (nihai inceleme Ö-1, 2026-09-03): "Bilgi Tabanı → Meridian dersleri"
   * diyen bir bağ, sekmeyi YEREL DURUMDA tutan bir görünüme gidiyordu ve hep
   * varsayılan sekmeyi açıyordu — "çalışan ama yanlış yere giden bağ, çalışmayan
   * bağdan daha sinsidir" (bu deponun kendi kuralı, `komutlar.ts`).
   *
   * NEDEN SORGU, NEDEN ÜÇÜNCÜ BİR YOL PARÇASI DEĞİL — ÖLÇÜLDÜ: `yol`un ilk üç
   * parçası (`dashboard/<yüzey>/<bölüm>`) yüzey KAYDININ (`alanlar.ts`) kimlik
   * uzayıdır; oraya dördüncü bir parça eklemek, kaydın saymadığı bir bölüm
   * kimliği doğurur (`alanlar.ts` bölüm sayacı, kırıntı, ⌘K anahtarları hepsi o
   * uzaydan besleniyor). Sekme bir bölüm DEĞİL, bölümün içindeki bir seçimdir —
   * sorgu tam olarak bunun için var. `yol` bu yüzden sorguyu TAŞIMAZ: kenar
   * çubuğu etkinliği (`alanKoku`) ve kırıntı onu okuyor.
   */
  readonly sorgu: Readonly<Record<string, string>>;
}

/** `sekme=dersler&x=1` → `{sekme:"dersler", x:"1"}`. Boş/bozuk girdi boş nesne verir. */
function sorguCoz(ham: string): Readonly<Record<string, string>> {
  if (!ham) return {};
  const out: Record<string, string> = {};
  for (const parca of ham.split("&")) {
    if (!parca) continue;
    const esit = parca.indexOf("=");
    const ad = esit === -1 ? parca : parca.slice(0, esit);
    const deger = esit === -1 ? "" : parca.slice(esit + 1);
    if (!ad) continue;
    // `decodeURIComponent` bozuk yüzde-dizisinde ATAR; sorgu bir GÖRÜNÜM
    // seçimidir ve bozuk bir yer imi panoyu karartamaz (Yasa 4: yutma DEĞİL —
    // ham değer korunur, yani bilgi kaybolmaz, yalnız çözülemediği söylenmez
    // çünkü söylenecek bir okuyucusu yok: çağıran tanımadığı sekmeyi zaten
    // varsayılana düşürür).
    try {
      out[decodeURIComponent(ad)] = decodeURIComponent(deger);
    } catch {
      out[ad] = deger;
    }
  }
  return out;
}

function hashiCoz(ham: string): Rota {
  // ÜÇ BİÇİM DE GİRER ve üçü de gerçek trafiktir:
  //   · yeni  `#/dashboard/finance/mutabakat`  — panonun kendi ürettiği bağlar
  //   · eski  `#karar` / `#adaylar`            — RUNBOOK bağları, tarayıcı yer imleri
  //   · boş   `#`                              — ilk açılış
  const bos = ham.replace(/^#/, "").replace(/^\//, "");
  const soru = bos.indexOf("?");
  const temiz = soru === -1 ? bos : bos.slice(0, soru);
  const sorgu = sorguCoz(soru === -1 ? "" : bos.slice(soru + 1));
  const parca = temiz.split("/").filter(Boolean);

  if (parca[0] === "dashboard") {
    const aday = parca[1] ?? "";
    if (aday in YUZEYLER) {
      const yuzey = aday as YuzeyAnahtari;
      const bolum = parca[2] ?? "";
      return { yuzey, bolum, yol: yuzeyYolu(yuzey, bolum || undefined), sorgu };
    }
    // TANINMAYAN ALT YOL VARSAYILANA DÜŞER, boş ekrana DEĞİL: bu pano tek dosya
    // olarak sunuluyor, yani yanlış bir hash sunucudan 404 alamaz — düşmezse
    // operatör bomboş bir kabuk görür ve neden boş olduğunu hiçbir yerden okuyamaz.
    return { yuzey: VARSAYILAN_YUZEY, bolum: "", yol: yuzeyYolu(VARSAYILAN_YUZEY), sorgu: {} };
  }

  const takma = ROTA_TAKMA_ADLARI[parca[0] ?? ""];
  if (takma) {
    const bolum = takma.bolum ?? parca[1] ?? "";
    // TAKMA ADIN KENDİ SORGUSU, ADRESTEKİNİ EZMEZ: `#hafiza?sekme=modeller` yazan
    // bir yer imi kendi seçimini korur. Takma adın sorgusu yalnız BOŞLUĞU doldurur.
    return {
      yuzey: takma.yuzey,
      bolum,
      yol: yuzeyYolu(takma.yuzey, bolum || undefined),
      sorgu: Object.keys(sorgu).length > 0 ? sorgu : (takma.sorgu ?? {}),
    };
  }

  return { yuzey: VARSAYILAN_YUZEY, bolum: "", yol: yuzeyYolu(VARSAYILAN_YUZEY), sorgu: {} };
}

/** Bir yolun YÜZEY kökü: `/dashboard/finance/mutabakat` → `/dashboard/finance`.
 *  Kenar çubuğu etkinliği bunu okur — bkz. nav-main.tsx'teki uyarlama şerhi. */
export function alanKoku(yol: string): string {
  const p = yol.replace(/^\//, "").split("/");
  return `/${p.slice(0, 2).join("/")}`;
}

/** `/dashboard/finance` → `#/dashboard/finance`. Dış bağlar (http, mailto) aynen geçer. */
export function yolaHash(href: string): string {
  if (!href.startsWith("/")) return href; // http(s), mailto, zaten hash — dokunma
  return `#${href}`;
}

const RotaBaglami = createContext<{ rota: Rota; git: (href: string) => void } | null>(null);

export function RotaSaglayici({ children }: { children: ReactNode }) {
  const [rota, setRota] = useState<Rota>(() => hashiCoz(window.location.hash));

  useEffect(() => {
    const dinle = () => setRota(hashiCoz(window.location.hash));
    window.addEventListener("hashchange", dinle);
    // İLK YÜKLEMEDE HASH BOŞ OLABİLİR: yazmazsak geri tuşu panoyu terk eder
    // (tarayıcı geçmişinde pano için hiç giriş olmaz) — operatör "geri"ye basınca
    // önceki SİTEYE düşer. Boşken varsayılanı yazmak o girişi doğurur.
    if (!window.location.hash) window.location.hash = yuzeyYolu(VARSAYILAN_YUZEY);
    return () => window.removeEventListener("hashchange", dinle);
  }, []);

  const git = useCallback((href: string) => {
    window.location.hash = href;
  }, []);

  const deger = useMemo(() => ({ rota, git }), [rota, git]);
  return <RotaBaglami value={deger}>{children}</RotaBaglami>;
}

function baglam() {
  const b = use(RotaBaglami);
  if (!b) throw new Error("RotaSaglayici yok — kabuk <RotaSaglayici> içine sarılmalı");
  return b;
}

/** Etkin rotanın tamamı (alan + bölüm). Sayfalar bunu okur. */
export function useRota(): Rota {
  return baglam().rota;
}

/** Next'in `usePathname()` karşılığı — kabuk bileşenleri `/karar` bekliyor. */
export function usePathname(): string {
  return baglam().rota.yol;
}

/** Next'in `useRouter()` karşılığı; yalnız `push` kullanılıyor. */
export function useRouter(): { push: (href: string) => void } {
  const { git } = baglam();
  return useMemo(() => ({ push: git }), [git]);
}

/** Next'in `<Link>`i yerine düz `<a>`. `href` yol biçiminde verilir, hash'e çevrilir. */
export default function Link({
  href,
  children,
  ...kalan
}: { href: string } & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href">) {
  return (
    <a href={yolaHash(href)} {...kalan}>
      {children}
    </a>
  );
}

export { Link };
