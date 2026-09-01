"use client";

/* ============================================================================
   MARKA RAYI — şablonun `auth/v2/layout` düzenindeki `bg-primary` sütunu
   ----------------------------------------------------------------------------
   NEDEN AYRI DOSYA (2026-09-01): bu ray artık İKİ yerde çiziliyor —
   kabuk içindeki Giriş yüzeyinin kart panelinde ve kimliksiz ziyaretçinin
   gördüğü tam-ekran kapıda (`pano/GirisKapisi.tsx`). Gövdeyi ikinci kez
   yazmak, aynı cümlelerin zamanla iki farklı hâle ayrışması demekti; bu
   depoda baskın hata deseni tam olarak bu. Tek kaynak burada, iki kap dışarıda.

   ALT BLOK İSTEĞE BAĞLI — VE BU BİR SÜS AYARI DEĞİL, İZLEYİCİ AYRIMI
   (düzeltme-1, 2026-09-01). Ray iki farklı izleyiciye bakıyor:
     · kabuk içinde   → kimliği DOĞRULANMIŞ operatör; iç ayrıntı ona ait
     · tam-ekran kapı → KİMLİKSİZ ziyaretçi; internete açık ilk yüz
   Dış kapı (APISIX basic-auth) kalkana kadar bu ayrım yoktu: rayı yalnız
   operatör görebiliyordu. Kalktığı gün aynı iki sütun ("kullanıcı tablosu
   yok", "sunucu kabuğunda şu komutu koş") anonim bir ziyaretçinin gördüğü
   ekrana taşındı — yani yığın adını ve bir yönetim komutunu ifşa eder oldu.
   Blok bu yüzden ZORUNLU DEĞİL: kapı onu HİÇ vermiyor, kabuk içi panel
   veriyor. İki metin yok, tek metnin İKİ İZLEYİCİSİ var.
   ============================================================================ */
import { Fingerprint } from "lucide-react";
import { Fragment } from "react";

import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

/** Rayın alt bloğundaki tek sütun. İki sütundan fazlası ayıraçla taşınmaz. */
export interface RayAyrintisi {
  readonly baslik: string;
  readonly govde: string;
}

export function MarkaRayi({
  baslik,
  altBaslik,
  ayrintilar,
  className,
}: {
  readonly baslik: string;
  readonly altBaslik: string;
  /**
   * Şablonun iki sütunlu alt bloğu. VERİLMEZSE HİÇ ÇİZİLMEZ — kimliksiz
   * ziyaretçinin gördüğü kapı burayı boş bırakır (bkz. dosya başlığı).
   */
  readonly ayrintilar?: readonly RayAyrintisi[];
  /** Kabın kendi yerleşim kancası (tam-ekran kapı `h-dvh` ızgarasının bir sütunu). */
  readonly className?: string;
}) {
  const ayrintiVar = Boolean(ayrintilar && ayrintilar.length > 0);
  return (
    <div
      className={cn(
        "hidden flex-col bg-primary p-8 text-primary-foreground lg:flex",
        // İKİ BLOK VARSA ŞABLONUN DİZİLİMİ (üstte marka, altta ayrıntı); TEK BLOK
        // KALINCA ORTALANIR. `justify-between` tek çocukla onu tepeye yapıştırır ve
        // altında ekranın üçte ikisi kadar boş, doygun renkli bir alan bırakırdı —
        // yani "buraya bir şey gelecekti" diye okunan bir boşluk.
        ayrintiVar ? "justify-between" : "justify-center",
        className,
      )}
    >
      <div className="space-y-1">
        <Fingerprint className="size-9" aria-hidden />
        <h2 className="font-medium text-2xl">{baslik}</h2>
        <p className="text-primary-foreground/80 text-sm">{altBaslik}</p>
      </div>
      {ayrintiVar && ayrintilar ? (
        <div className="flex gap-3">
          {ayrintilar.map((a, i) => (
            <Fragment key={a.baslik}>
              {i > 0 ? (
                <Separator orientation="vertical" className="h-auto! bg-primary-foreground/20" />
              ) : null}
              <div className="flex-1 space-y-1">
                <h3 className="font-medium text-sm">{a.baslik}</h3>
                <p className="text-primary-foreground/80 text-xs">{a.govde}</p>
              </div>
            </Fragment>
          ))}
        </div>
      ) : null}
    </div>
  );
}
