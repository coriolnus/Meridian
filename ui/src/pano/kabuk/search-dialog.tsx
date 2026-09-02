"use client";

/* ============================================================================
   ⌘K PALETİ — şablonun arama iletişimi + Meridian'ın komutları
   ----------------------------------------------------------------------------
   ŞABLONDAN GELEN: `CommandDialog` iskeleti, gruplama, klavye gezinmesi.
   ŞABLONDA OLMAYAN ve buraya eklenen dört şey:

     1. TÜRKÇE KATLAMALI ARAMA. cmdk'nın kendi süzgeci "gölge" ile "golge"yi
        AYRI dizgi sayıyordu; klavyesinde Türkçe harf olmayan bir operatör için
        paletin yarısı yok demekti (`komutlar.ts::paletFiltresi`).
     2. ANAHTAR KELİMELER. Eski palet her bölüm için el yazısı kelimeler
        taşıyordu — "mutabakat" bölümünü "ayna", "broker", "ghost" da bulur.
        Yalnız başlığı aramak, bir bilgi mimarisi haritasını başlıkların
        alfabesine indirger.
     3. SEMBOL ARAMASI (`/api/market`) — 251 sembollük evren, ölçülen kapanışıyla.
     4. DIŞ BELGELER — /runbook · /workflow · /landing.

   GERİ ALINAMAZ EYLEM PALETTE OLMAZ (bu turun hükmü).
   Eski palet HALT · Cancel-Open · FLATTEN · Halt-Learning · ack kuyrukları ve
   Hermes sprint kollarını da sunuyordu; onları iki adımlı bir onayla korumaya
   çalışıyordu. Yeni palette o sınıfın TAMAMI YOK ve bu bir eksik değil, karar:

     · Palet bir HIZLI ERİŞİM aracıdır — değeri, aradaki adımları silmesinden
       gelir. Geri alınamaz icra ise tam tersini ister: araya adım koymayı,
       operatörün kolun bulunduğu yüzeye GİTMESİNİ, bağlamı (kaç pozisyon açık,
       kesici tetikli mi) görerek basmasını. İki gereksinim aynı yüzeyde
       uzlaşmaz; uzlaştırmaya çalışan tasarım, ikisini de kötü yapar.
     · İki adımlı onay bu farkı KAPATMAZ: palette ikinci Enter, ilkinden 200 ms
       sonra ve AYNI tuşla gelir — kas hafızasının en kolay ezdiği yer. FLATTEN
       "Alpaca'daki TÜM pozisyonları kapat"tır ve elle açılmış pozisyonlar
       dahildir; bunun bedeli bir tuş tekrarına yazılamaz.
     · Kollar kaybolmuyor: Sistem sağlığı → Müdahale kolları yüzeyinde, alarm
       gelen kutusuyla AYNI ekranda duruyorlar ve palet oraya GÖTÜRÜR. Yani
       palet hâlâ en hızlı yol — yalnız son basışı operatöre bırakıyor.

   OTURUM KAPISI KORUNUYOR (eski palet: `palette.js::kapiAcik`). Oturum düşmüşse
   palet AÇILMAZ. Sebep yeni panoda daha da güçlü: her yüzey kendi kapısında
   "oturum düştü" yazacak, yani paletle gezinmek operatörü kapalı kapılar
   arasında dolaştırmak olurdu; tek anlamlı hamle giriş ekranıdır. REDDEDİŞ
   SESSİZ DEĞİL: bir bildirim nedeni yazar ve oraya götüren düğmeyi taşır —
   sessizce açılmayan bir kısayol, bozuk bir kısayoldan ayırt edilemez.
   ============================================================================ */

import * as React from "react";

import { toast } from "sonner";

import { BookOpen, CandlestickChart, ExternalLink, RefreshCw, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { Kbd } from "@/components/ui/kbd";
import { cn } from "@/lib/utils";
import type { NavMainItem } from "@/navigation/sidebar/sidebar-items";
import { yuzeyYolu } from "@/pano/alanlar";
import { useBugun } from "@/pano/durum";
import { gezinmeGruplari as sidebarItems } from "@/pano/gezinme";
import {
  ARAMA_ANAHTARLARI,
  BELGE_ANAHTARLARI,
  DIS_BELGELER,
  kapanisMetni,
  paletFiltresi,
  sembolAra,
  sembolHedefi,
} from "@/pano/komutlar";
import { useRouter } from "@/pano/rota";
import { OturumHatasi, apiGet } from "@/pano/veri";
import type { PiyasaGovdesi, PiyasaSatiri } from "@/pano/yuzeyler/sistem/uctipleri";

type SearchItem = {
  id: string;
  group: string;
  label: string;
  url: string;
  icon?: NavMainItem["icon"];
  disabled?: boolean;
  newTab?: boolean;
};

const sidebarGroupLabels = new Set(sidebarItems.flatMap((group) => (group.label ? [group.label] : [])));

function getSubItemGroup(groupLabel: string | undefined, itemTitle: string) {
  return sidebarGroupLabels.has(itemTitle) ? (groupLabel ?? "Other") : itemTitle;
}

const searchItems: SearchItem[] = sidebarItems.flatMap((group) =>
  group.items.flatMap((item) => {
    if (item.subItems) {
      return item.subItems.map((sub) => ({
        id: sub.id,
        group: getSubItemGroup(group.label, item.title),
        label: sub.title,
        url: sub.url,
        icon: item.icon,
        disabled: sub.disabled,
        newTab: sub.newTab,
      }));
    }
    return [
      {
        id: item.id,
        group: group.label ?? "Other",
        label: item.title,
        url: item.url,
        icon: item.icon,
        disabled: item.disabled,
        newTab: item.newTab,
      },
    ];
  }),
);

function getAvailableItems(items: SearchItem[]) {
  return items.filter((item) => !item.disabled && !item.url.includes("coming-soon"));
}

const recommendations = getAvailableItems(searchItems);

function groupBy(items: SearchItem[]) {
  const groups = [...new Set(items.map((item) => item.group))];
  return groups.map((group) => ({
    group,
    items: items.filter((item) => item.group === group),
  }));
}

/* ---------------------------------------------------------------------------
   EVREN (SEMBOL KAYNAĞI) — DÖRT HÂL, DÖRT AYRI CÜMLE
   "Hiç sorulmadı", "okunuyor", "okundu" ve "okunamadı" AYRI şeylerdir. Üçünü
   tek sessizliğe indirmek, boş bir sonuç listesini "eşleşme yok" diye okutur —
   yani ölçülemeyen bir şeyi ölçülmüş gibi gösterir (UYDURMA YASAĞI).
   --------------------------------------------------------------------------- */
type EvrenHali =
  | { readonly hal: "yok" }
  | { readonly hal: "okunuyor" }
  | { readonly hal: "okundu"; readonly satirlar: readonly PiyasaSatiri[]; readonly asOf: string | null; readonly zaman: number }
  | { readonly hal: "hata"; readonly neden: string };

/** `/api/market` EOD kapanıştır (api.py::api_market) — seans içinde bile saniyede bir
 *  değişmez. Palet her açılışta 251 satırı yeniden çekseydi, bir kısayolun
 *  bedeli ölçülebilir bir ağ yükü olurdu. */
const EVREN_TAZELIK_MS = 10 * 60_000;

function evrenCumlesi(e: EvrenHali): { readonly metin: string; readonly uyari: boolean } {
  switch (e.hal) {
    case "yok":
      return { metin: "sembol araması: /api/market henüz sorulmadı", uyari: false };
    case "okunuyor":
      return { metin: "sembol araması: /api/market okunuyor…", uyari: false };
    case "okundu":
      return {
        metin: `sembol araması: ${e.satirlar.length} satır · as_of ${e.asOf ?? "yazılmamış"} (EOD kapanış)`,
        uyari: false,
      };
    case "hata":
      // "ÖLÇÜLEMEDİ" ile "eşleşme yok" arasındaki fark bu satırda duruyor.
      return { metin: `sembol araması ÖLÇÜLEMEDİ — ${e.neden}`, uyari: true };
  }
}

export function SearchDialog() {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [evren, setEvren] = React.useState<EvrenHali>({ hal: "yok" });
  const router = useRouter();
  const { oturumDustu, tazele: bugunTazele } = useBugun();

  const iptal = React.useRef<AbortController | null>(null);
  const evrenRef = React.useRef<EvrenHali>(evren);
  React.useEffect(() => {
    evrenRef.current = evren;
  }, [evren]);

  const evreniOku = React.useCallback(() => {
    iptal.current?.abort();
    const kontrol = new AbortController();
    iptal.current = kontrol;
    setEvren({ hal: "okunuyor" });
    apiGet<PiyasaGovdesi>("/api/market", kontrol.signal)
      .then((g) => {
        if (kontrol.signal.aborted) return;
        if (g.rows === undefined) {
          // BOŞ DİZİ İLE ALANIN HİÇ GELMEMESİ AYNI ŞEY DEĞİL: ilki "ölçtük, evren
          // boş", ikincisi "ölçemedik". `?? []` yazmak ikincisini birincisi gibi
          // gösterirdi ve palet olmayan bir evreni "eşleşme yok" diye okuturdu.
          setEvren({ hal: "hata", neden: "/api/market `rows` alanını döndürmedi" });
          return;
        }
        setEvren({ hal: "okundu", satirlar: g.rows, asOf: g.as_of ?? null, zaman: Date.now() });
      })
      .catch((e: unknown) => {
        if (kontrol.signal.aborted) return;
        setEvren({
          hal: "hata",
          neden:
            e instanceof OturumHatasi
              ? "oturum düştü — /api/market 401 döndü"
              : e instanceof Error
                ? e.message
                : String(e),
        });
      });
  }, []);

  // AÇILIŞTA OKUNUR, AÇIKKEN DEĞİL. Bağımlılık YALNIZ `open`: `evren`i de
  // dinleseydik "hata" hâli kendi kendini tetikleyip sonsuz döngü kurardı
  // (hata → efekt → istek → hata). Başarısız okuma bir sonraki AÇILIŞTA yeniden
  // denenir; arada elle deneme yolu da var ("Sembol listesini yeniden oku").
  React.useEffect(() => {
    if (!open) return;
    const e = evrenRef.current;
    if (e.hal === "okunuyor") return;
    if (e.hal === "okundu" && Date.now() - e.zaman < EVREN_TAZELIK_MS) return;
    evreniOku();
  }, [open, evreniOku]);

  React.useEffect(() => () => iptal.current?.abort(), []);

  const oturumUyar = React.useCallback(() => {
    toast.warning("Oturum düştü — palet açılmıyor", {
      description:
        "Paletteki her yüzey kendi kapısında 'oturum düştü' yazacak; tek anlamlı hamle yeniden giriş.",
      action: {
        label: "Giriş'e git",
        onClick: () => router.push(yuzeyYolu("authentication", "giris")),
      },
    });
  }, [router]);

  const handleOpenChange = React.useCallback(
    (value: boolean) => {
      if (value && oturumDustu) {
        oturumUyar();
        return;
      }
      setOpen(value);
      if (!value) setQuery("");
    },
    [oturumDustu, oturumUyar],
  );

  // OTURUM AÇIKKEN DÜŞERSE PALET KAPANIR: 15 sn'lik nabız (useBugun) 401 gördüğü
  // anda açık kalan palet, ardındaki hiçbir yüzeyi gerçekten açamayacak bir
  // vaade dönüşür.
  React.useEffect(() => {
    if (!oturumDustu || !open) return;
    setOpen(false);
    setQuery("");
    oturumUyar();
  }, [oturumDustu, open, oturumUyar]);

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      // İKİ TUŞ DA BAĞLI VE İKİSİ DE GERÇEK KAS HAFIZASI: ⌘K eski Meridian
      // paletinin tuşuydu (palette.js:1049), ⌘J şablondan geliyor. Birini
      // düşürmek, o tuşu kullanan operatöre paletin bozulduğunu düşündürürdü.
      const k = e.key.toLowerCase();
      if ((k !== "k" && k !== "j") || !(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey) return;
      // CTRL AÇIKKEN KAPATMAZ — ÇÜNKÜ O TUŞ ARTIK BİZİM DEĞİL. cmdk'nın kendi vim
      // bağları Ctrl+J (aşağı) / Ctrl+K (yukarı) ile listede geziniyor (cmdk root
      // onKeyDown, `vimBindings` varsayılan açık). Palet AÇIKKEN o basışı yakalayıp
      // pencereyi kapatmak, klavyeyle gezinen operatörün listesini elinden almak
      // olurdu. Meta (⌘) cmdk tarafından hiç dinlenmiyor — açarken de kapatırken de
      // çakışmasız; Ctrl ise yalnız KAPALIYKEN açar (kapatmanın yolu Esc).
      if (open && !e.metaKey) return;
      e.preventDefault();
      handleOpenChange(!open);
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [handleOpenChange, open]);

  const handleSelect = (item: SearchItem) => {
    if (item.disabled) return;
    handleOpenChange(false);
    if (item.newTab) {
      window.open(item.url, "_blank", "noopener,noreferrer");
    } else {
      router.push(item.url);
    }
  };

  const sembolSatirlari = React.useMemo(
    () => (evren.hal === "okundu" ? sembolAra(evren.satirlar, query) : []),
    [evren, query],
  );

  const durumCumlesi = evrenCumlesi(evren);

  // BOŞ SONUÇ HER ZAMAN "EŞLEŞME YOK" DEMEK DEĞİLDİR. Evren okunamadıysa liste
  // yüzeyleri kapsar ama SEMBOLLERİ kapsamaz; bunu yazmadan "eşleşme yok" demek,
  // ölçülmemiş bir kümeyi ölçülmüş gibi ilan etmektir.
  const bosMetin =
    evren.hal === "okundu"
      ? "Eşleşme yok."
      : `Yüzeylerde ve belgelerde eşleşme yok — ${durumCumlesi.metin}, yani bu sonuç sembolleri KAPSAMIYOR.`;

  const renderGroups = (items: SearchItem[]) =>
    groupBy(items).map(({ group, items: groupItems }, index) => (
      <React.Fragment key={group}>
        {index > 0 && <CommandSeparator />}
        <CommandGroup heading={group}>
          {groupItems.map((item) => (
            <CommandItem
              disabled={item.disabled}
              key={`${group}-${item.id}`}
              value={`${item.group} ${item.label}`}
              keywords={[...(ARAMA_ANAHTARLARI[item.url] ?? [])]}
              onSelect={() => handleSelect(item)}
            >
              <span className="flex min-w-0 items-center gap-2">
                {item.icon && <item.icon />}
                <span className="truncate">{item.label}</span>
              </span>
            </CommandItem>
          ))}
        </CommandGroup>
      </React.Fragment>
    ));

  return (
    <>
      <Button
        onClick={() => handleOpenChange(true)}
        variant="link"
        className="px-0! font-normal text-muted-foreground hover:no-underline"
        title={
          oturumDustu
            ? "Oturum düştü — palet açılmıyor (komutların hepsi kapalı kapıya götürürdü)"
            : "Yüzey, bölüm, sembol ve belge ara (⌘K)"
        }
      >
        <Search data-icon="inline-start" />
        Ara
        {/* ⌘K ROZETİ DAR EKRANDA YOK (2026-08-31, Rol-1'in 375px ölçümü: üst barda
            hap ile arama üst üste biniyordu). Kırıntı zaten `md` altında gizleniyor —
            aynı eşik kullanıldı, yeni bir kırılma noktası icat edilmedi. Kaybedilen
            şey ÖLÇÜLDÜ ve sıfırdır: `md` altı dokunmatik bir ekranda ⌘ tuşu yoktur,
            yani rozet orada zaten uygulanamayan bir kısayolu ilan ediyordu. "Ara"
            etiketi ve düğmenin `title`ı olduğu gibi duruyor. */}
        <Kbd className="hidden md:inline-flex">⌘K</Kbd>
      </Button>
      <CommandDialog
        open={open}
        onOpenChange={handleOpenChange}
        title="Meridian komut paleti"
        description="Yüzey, bölüm, sembol ve belge arar. Geri alınamaz kollar burada YOKTUR."
      >
        {/* SÜZGEÇ BİZİM: cmdk'nın varsayılanı Türkçeyi katlamıyor (bkz. komutlar.ts). */}
        <Command filter={paletFiltresi}>
          <CommandInput
            placeholder="Yüzey, bölüm, sembol ya da belge ara…"
            value={query}
            onValueChange={setQuery}
          />
          <CommandList>
            <CommandEmpty>{bosMetin}</CommandEmpty>
            {query ? renderGroups(searchItems) : renderGroups(recommendations)}

            {/* ---- SEMBOLLER — yalnız yazılmışken, çünkü 251 satırlık bir liste
                    paletin kendi amacını (daraltmak) yok ederdi. -------------- */}
            {sembolSatirlari.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Semboller · /api/market">
                  {sembolSatirlari.map((r) => {
                    const hedef = sembolHedefi(r);
                    return (
                      <CommandItem
                        key={`sembol-${r.ticker}`}
                        value={`sembol ${r.ticker}`}
                        onSelect={() => {
                          handleOpenChange(false);
                          router.push(hedef.yol);
                        }}
                      >
                        <span className="flex min-w-0 items-center gap-2">
                          <CandlestickChart />
                          <span className="font-medium">{r.ticker}</span>
                          {/* SATIR NEREYE GÖTÜRDÜĞÜNÜ ÖNCEDEN SÖYLER: Piyasa bölümü
                              evreni ÖZETLER, sembolü tek tek listelemez. */}
                          <span className="truncate text-muted-foreground text-xs">{hedef.gerekce}</span>
                        </span>
                        <CommandShortcut className="tabular-nums">{kapanisMetni(r)}</CommandShortcut>
                      </CommandItem>
                    );
                  })}
                </CommandGroup>
              </>
            )}

            {/* ---- BELGELER — panodan AYRILAN okuma yüzeyleri ----------------- */}
            <CommandSeparator />
            <CommandGroup heading="Belgeler">
              {DIS_BELGELER.map((b) => (
                <CommandItem
                  key={b.kimlik}
                  value={`belge ${b.ad}`}
                  keywords={[...(BELGE_ANAHTARLARI[b.kimlik] ?? [])]}
                  onSelect={() => {
                    handleOpenChange(false);
                    // HASH YÖNLENDİRMESİ BUNU TAŞIYAMAZ: pano tek dosya, `#` sunucuya
                    // hiç gitmiyor. Bu yüzden gerçek bir sayfa geçişi.
                    window.location.assign(b.yol);
                  }}
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <BookOpen />
                    <span className="truncate">{b.ad}</span>
                    <span className="truncate text-muted-foreground text-xs">{b.aciklama}</span>
                  </span>
                  <CommandShortcut>
                    <ExternalLink />
                  </CommandShortcut>
                </CommandItem>
              ))}
            </CommandGroup>

            {/* ---- OKUMA — sistemin durumunu DEĞİŞTİRMEYEN, yalnız yeniden
                    SORAN komutlar. Palete girebilen tek "eylem" sınıfı budur. -- */}
            <CommandSeparator />
            <CommandGroup heading="Okuma">
              <CommandItem
                value="okuma durumu yeniden oku"
                keywords={["tazele", "yenile", "refresh", "nabiz", "today", "durum"]}
                onSelect={() => {
                  handleOpenChange(false);
                  bugunTazele();
                  toast.info("Durum yeniden soruldu", {
                    description: "/api/today — sonuç üst bardaki durum hapında görünür.",
                  });
                }}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <RefreshCw />
                  <span className="truncate">Durumu yeniden oku</span>
                  <span className="truncate text-muted-foreground text-xs">
                    /api/today nabzını hemen tetikler (15 sn'lik turu beklemez)
                  </span>
                </span>
              </CommandItem>
              <CommandItem
                value="okuma sembol listesini yeniden oku"
                keywords={["sembol", "evren", "market", "piyasa", "ticker", "yenile"]}
                onSelect={() => {
                  // PALET AÇIK KALIR: bu komutun tek amacı aramanın kendisini
                  // onarmak. Kapatmak, operatörü aynı kısayolu yeniden basmaya
                  // zorlardı. Sonuç aşağıdaki durum satırında görünür.
                  evreniOku();
                }}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <RefreshCw />
                  <span className="truncate">Sembol listesini yeniden oku</span>
                  <span className="truncate text-muted-foreground text-xs">
                    /api/market — palet açık kalır, sonuç alttaki satırda yazar
                  </span>
                </span>
              </CommandItem>
            </CommandGroup>
          </CommandList>

          {/* ARAMANIN KAYNAĞI HER ZAMAN GÖRÜNÜR ve süzgeçten GEÇMEZ: bir durum
              beyanıdır, bir komut değil. Süzgece girseydi tam da gerekli olduğu
              anda — arama boş dönerken — ekrandan kaybolurdu. */}
          <div
            className={cn(
              // `-mx-1`: Command kökünün `p-1` iç boşluğunu taşar, yani ayraç
              // CommandSeparator gibi tam genişlikte durur.
              "-mx-1 mt-1 border-t px-3 py-2 text-xs",
              durumCumlesi.uyari ? "font-medium text-amber-600 dark:text-amber-400" : "text-muted-foreground",
            )}
            role="status"
            aria-live="polite"
          >
            {durumCumlesi.metin}
          </div>
        </Command>
      </CommandDialog>
    </>
  );
}
