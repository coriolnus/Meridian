"use client";

/* ============================================================================
   SOL SÜTUN — muhatap listesi (maket: arama · şu an aktif · AJANLAR · KANALLAR)
   ----------------------------------------------------------------------------
   BU SÜTUN İKİ AYRI KAYNAĞI YAN YANA KOYAR AMA BİRLEŞTİRMEZ: AJANLAR bölümü
   `GET /api/ajanlar` roster'ından, KANALLAR bölümündeki tek satır ise hipotez
   defterinden (`/api/agent`) geliyor. Uçlardan biri düşerse ÖTEKİ BÖLÜM
   ÇİZİLMEYE DEVAM EDER — eski kabukta tek bir kapı tüm yüzeyi sarıyordu ve bir
   kaynağın arızası ötekinin ölçümünü yutuyordu.

   NOKTANIN ÜÇ HÂLİ ÖLÇÜLÜDÜR ve tanımı `gramer.ts::aktiflik`te beyanlı:
   yeşil = bugün (yerel gün) konuşma ya da teslim damgası var · gri = ölçüldü,
   bugün kaydı yok · AMBER = ÖLÇÜLEMEDİ. Amber "kötü" demek değil "bilmiyorum"
   demek; lejantı ⓘ künyesinde yazılı, çünkü renk tek başına anlam taşımaz.

   ÜÇ HÂL ŞERİTTE DE ÜÇ AYRI KOVADA KALIR (inceleme K-1, 2026-08-31). Şerit eskiden
   yalnız "aktif"i sayıyor, kalan ikisini tek kovaya döküp ekrana "ölçülmüş boşluk"
   yazıyordu: üç profilin defteri kilitliyken üstte "bugüne düşen damga yok", hemen
   altında üç AMBER nokta duruyordu — aynı ekranda iki zıt hüküm ve üstteki YALAN.
   Sayım artık `gramer.ts::aktiflikSayimi`den geliyor ve ÖLÇÜLEMEYEN VARKEN cümle
   "boşluk" demez, "okunamadı, bugün konuşulmuş olabilir" der.

   ŞERİDİ ARAMA DARALTIR VE BU SÖYLENİR: şerit süzülmüş listeden besleniyor (seçim ve
   liste tek gerçeği paylaşsın diye), o yüzden sorgu doluyken başlık "(aramaya göre)"
   ekler. Sessizce daraltmak, boşluğun sebebi operatörün kendi sorgusuyken onu
   ölçülmüş bir sessizlik gibi okuturdu.

   UYGULANMAYAN MAKET SÜSLERİ (ön ruling): satırlardaki okunmamış-sayı rozeti ve
   kadans etiketi ("günlük 22:01") BASILMADI — ikisinin de arkasında veri yok.
   Rozet için okundu-izleme defteri, kadans için zamanlayıcı kaydı gerekirdi;
   ikisi de bugün ölçülmüyor ve uydurmak yasak. Satırın sağındaki saat ise
   ÖLÇÜLÜ: en yeni oturum ya da teslim damgasından türüyor.
   ============================================================================ */
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";
import { HukumSeridi, ListeYok } from "./Filo";
import { Olculemedi, bicimSayi, saatMetni } from "./ortak";
import {
  aktiflik,
  aktiflikSayimi,
  sonHareketTs,
  sonMesajOzeti,
  type Aktiflik,
  type Muhatap,
} from "./gramer";
import type { FiloYuku } from "./filoOku";

const NOKTA: Readonly<Record<Aktiflik, string>> = {
  aktif: "bg-basari",
  sessiz: "bg-muted-foreground",
  olculemedi: "bg-uyari",
};

const NOKTA_BASLIK: Readonly<Record<Aktiflik, string>> = {
  aktif: "bugün konuşma ya da teslim damgası var",
  sessiz: "iki kaynak da okundu, bugüne düşen kayıt yok",
  olculemedi: "kaynaklardan biri okunamadı ya da bir damga zamana yerleşmedi — bugün konuşulmuş olabilir",
};

/* ---- SATIR --------------------------------------------------------------- */

function Avatar({ m, aktif }: { m: Muhatap; aktif: Aktiflik | null }) {
  return (
    <span
      className={cn(
        "relative grid size-9 shrink-0 place-items-center border bg-muted font-semibold text-sm",
        m.tur === "kanal" ? "rounded-lg border-bilgi-h bg-bilgi-t text-bilgi" : null,
        m.ajan?.tur === "ana" ? "rounded-lg" : m.tur === "kanal" ? null : "rounded-full",
      )}
    >
      {m.isaret}
      {aktif === null ? null : (
        <span
          className={cn("absolute -right-0.5 -bottom-0.5 size-2.5 rounded-full ring-2 ring-card", NOKTA[aktif])}
          title={NOKTA_BASLIK[aktif]}
          aria-label={NOKTA_BASLIK[aktif]}
        />
      )}
    </span>
  );
}

export interface Onizleme {
  readonly metin: string | null;
  /** Metin yerine bir ölçülemedi/boşluk cümlesi mi basılacak. */
  readonly uyari: boolean;
}

function ajanOnizlemesi(m: Muhatap): Onizleme {
  const a = m.ajan;
  if (a === null) return { metin: null, uyari: false };
  if (a.oturumlar === null) {
    return { metin: a.neden ?? "konuşma defteri ölçülemedi", uyari: true };
  }
  const ozet = sonMesajOzeti(a);
  if (ozet === null) return { metin: "defter okundu, konuşma kaydı yok", uyari: false };
  if (ozet.metin === null) return { metin: "son satırın gövdesi okunamadı", uyari: true };
  if (ozet.metin === "") return { metin: "son satır ölçüldü ve boş", uyari: false };
  return { metin: ozet.metin, uyari: false };
}

function Satir({
  m,
  secili,
  sec,
  onizleme,
  aktif,
  saat,
}: {
  m: Muhatap;
  secili: boolean;
  sec: () => void;
  onizleme: Onizleme;
  aktif: Aktiflik | null;
  saat: string | null;
}) {
  return (
    <button
      type="button"
      onClick={sec}
      aria-current={secili ? "true" : undefined}
      className={cn(
        "flex w-full items-center gap-2.5 border-l-2 px-3 py-2 text-left transition-colors",
        secili ? "border-l-primary bg-muted/60" : "border-l-transparent hover:bg-muted/40",
      )}
    >
      <Avatar m={m} aktif={aktif} />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline gap-2">
          <span className="truncate font-medium text-sm">{m.ad}</span>
          <span className="ml-auto shrink-0 text-[11px] text-muted-foreground tabular-nums">
            {saat ?? ""}
          </span>
        </span>
        <span
          className={cn(
            "block truncate text-xs",
            onizleme.uyari ? "text-uyari italic" : "text-muted-foreground",
          )}
        >
          {onizleme.metin ?? "önizleme ölçülemedi"}
        </span>
      </span>
    </button>
  );
}

function BolumBasligi({ metin }: { metin: string }) {
  return (
    <p className="px-3 pt-3 pb-1 font-semibold text-[10px] text-muted-foreground uppercase tracking-wider">
      {metin}
    </p>
  );
}

/* ---- SÜTUN --------------------------------------------------------------- */

export function Yanliste({
  liste,
  seciliDilim,
  sec,
  arama,
  aramaDegisti,
  filo,
  yuk,
  kanalOnizlemesi,
  simdiMs,
  sahipsizAc,
  sahipsizSecili,
}: {
  liste: readonly Muhatap[];
  seciliDilim: string | null;
  sec: (m: Muhatap) => void;
  arama: string;
  aramaDegisti: (x: string) => void;
  filo: Durum<Record<string, unknown>>;
  yuk: FiloYuku | null;
  kanalOnizlemesi: Onizleme;
  /** Aktiflik hükmünün ÇAPASI dışarıdan gelir — bileşen kendi `Date.now()`unu
   *  çağırsaydı hüküm her yeniden çizimde kayardı ve çivilenemezdi. */
  simdiMs: number;
  sahipsizAc: () => void;
  sahipsizSecili: boolean;
}) {
  const ajanlar = liste.filter((m) => m.tur === "ajan");
  const kanallar = liste.filter((m) => m.tur === "kanal");
  const sayim = aktiflikSayimi(liste, simdiMs);
  const suzuluyor = arama.trim() !== "";
  const sahipsiz = yuk?.eslesmeyenTeslimler ?? null;
  const sahipsizToplam = yuk?.kaynak?.eslesmeyenToplam ?? null;

  return (
    <div className="flex min-h-0 w-full flex-col border-b bg-card md:w-[19rem] md:shrink-0 md:border-r md:border-b-0">
      {/* HÜKÜM ŞERİDİ ⓘ'YE GİRMEZ (ruling 2026-08-31): liste eksik ölçüldüyse
          operatörün gördüğü ajan listesi eksik demektir — bir düğmenin arkasına
          saklamak, gürültü azaltmak adına körlük satın almak olurdu. */}
      {yuk === null ? null : <HukumSeridi yuk={yuk} />}
      <div className="p-2.5 pb-1">
        <div className="relative">
          <Search className="-translate-y-1/2 absolute top-1/2 left-2.5 size-3.5 text-muted-foreground" aria-hidden />
          <Input
            value={arama}
            onChange={(e) => aramaDegisti(e.target.value)}
            placeholder="Ajan, kanal ya da mesaj ara…"
            className="h-8 pl-8 text-xs"
            aria-label="Ajan, kanal ya da mesaj ara"
          />
        </div>
        {/* MUAFİYET SÖYLENİR: açık sohbet süzgeçten düşmez (`gramer.ts::listeSuz`
            `korunan`). Sessiz bir muafiyet, listede "sorguya uymayan" bir satır
            gören operatöre süzgecin bozuk olduğunu düşündürürdü. */}
        {suzuluyor ? (
          <p className="mt-1 text-[10px] text-muted-foreground">
            Açık sohbet süzgeçten muaf; kalanlar ada ve son mesaja göre süzülüyor.
          </p>
        ) : null}
      </div>

      {/* ŞU AN AKTİF — üç hâl ÜÇ AYRI KOVADA (K-1). Avatarlar yalnız ÖLÇÜLMÜŞ
          aktiflikten; ölçülemeyenler kendi cümlesini alır ve "boşluk" denmez. */}
      <div className="px-3 pt-2">
        <p className="font-semibold text-[10px] text-muted-foreground uppercase tracking-wider">
          Şu an aktif{suzuluyor ? " (aramaya göre)" : ""}
        </p>
        {filo.veri === null && filo.yukleniyor ? (
          <Skeleton className="mt-2 h-8 w-24" />
        ) : yuk === null || yuk.ajanlar === null ? (
          <p className="mt-1.5 text-[11px]">
            <Olculemedi
              neden="ajan listesi okunamadı, kimin bugün konuştuğu söylenemez"
              teknik="`/api/ajanlar` gövdesinde `ajanlar` bir dizi değil ya da uç düştü"
            />
          </p>
        ) : (
          <>
            {sayim.aktif.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-2">
                {sayim.aktif.map((m) => (
                  <button
                    key={m.dilim}
                    type="button"
                    onClick={() => sec(m)}
                    title={m.ad}
                    className={cn(
                      "grid size-8 place-items-center border-2 border-basari bg-muted font-semibold text-xs",
                      m.ajan?.tur === "ana" ? "rounded-lg" : "rounded-full",
                    )}
                  >
                    {m.isaret}
                  </button>
                ))}
              </div>
            ) : sayim.olculemedi === 0 && sayim.sessiz > 0 ? (
              // YALNIZ burada "ölçülmüş boşluk" denebilir: iki kaynak da okundu,
              // her damga yerine oturdu ve hiçbiri bugüne düşmedi.
              <p className="mt-1.5 text-[11px] text-muted-foreground leading-relaxed">
                Bugüne düşen konuşma ya da teslim damgası yok — ölçülmüş boşluk.
              </p>
            ) : sayim.olculemedi === 0 && sayim.sessiz === 0 ? (
              <p className="mt-1.5 text-[11px] text-muted-foreground leading-relaxed">
                {suzuluyor ? "Arama hiçbir ajanı geçirmedi." : "Listede ajan yok."}
              </p>
            ) : null}
            {sayim.olculemedi > 0 ? (
              <p className="mt-1.5 text-[11px] leading-relaxed">
                <Olculemedi
                  className="text-uyari"
                  neden={`${bicimSayi(sayim.olculemedi)} ajanın defteri okunamadı, bugün konuşmuş olabilirler`}
                  teknik="bu ajanlarda `oturumlar`/`teslimler` liste değil ya da bir damga zamana yerleşmedi — sessizlik iddia edilemez"
                />
              </p>
            ) : null}
          </>
        )}
      </div>

      <div className="mt-1 min-h-0 flex-1 overflow-y-auto pb-2">
        <BolumBasligi metin="Ajanlar" />
        {filo.veri === null && filo.yukleniyor ? (
          <div className="flex flex-col gap-2 px-3 py-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        ) : filo.oturumDustu ? (
          <p className="px-3 py-2 text-[11px] text-muted-foreground leading-relaxed">
            Oturum düştü — ajan listesi bu yüzden boş, veri arızası değil. Yeniden giriş gerekiyor.
          </p>
        ) : yuk === null ? (
          <p className="px-3 py-2 text-[11px] leading-relaxed">
            <Olculemedi
              neden="Ajan listesi okunamadı"
              teknik={filo.hata ?? "`/api/ajanlar` ne tamamlandı ne düştü — gövde yok"}
            />
          </p>
        ) : yuk.ajanlar === null ? (
          // UCUN KENDİ HÜKMÜ EKRANA ULAŞIR: şeklin tanınmadığı BİZİM hükmümüz,
          // `hata` UCUN hükmü — biri ötekinin yerine geçmez (`filoOku::ajanListesiNedeni`).
          <ListeYok yuk={yuk} />
        ) : ajanlar.length === 0 ? (
          <p className="px-3 py-2 text-[11px] text-muted-foreground leading-relaxed">
            {arama.trim() === ""
              ? "Liste okundu ve içinde ajan yok — ölçülmüş boşluk."
              : "Arama hiçbir ajanı geçirmedi; liste boş değil, sorgu daraltıyor."}
          </p>
        ) : (
          ajanlar.map((m) => (
            <Satir
              key={m.dilim}
              m={m}
              secili={m.dilim === seciliDilim}
              sec={() => sec(m)}
              onizleme={ajanOnizlemesi(m)}
              aktif={m.ajan === null ? null : aktiflik(m.ajan, simdiMs)}
              saat={m.ajan === null ? null : saatMetni(sonHareketTs(m.ajan))}
            />
          ))
        )}

        <BolumBasligi metin="Kanallar" />
        {kanallar.length === 0 ? (
          <p className="px-3 py-2 text-[11px] text-muted-foreground leading-relaxed">
            Arama hiçbir kanalı geçirmedi.
          </p>
        ) : (
          kanallar.map((m) => (
            <Satir
              key={m.dilim}
              m={m}
              secili={m.dilim === seciliDilim}
              sec={() => sec(m)}
              onizleme={kanalOnizlemesi}
              aktif={null}
              saat={null}
            />
          ))
        )}
      </div>

      {/* HAYALET SATIR: hiçbir profile denk düşmeyen teslim olayları. Sessizce
          düşürmek, panonun "tüm ajan iletişimi burada" iddiasını yalan yapardı. */}
      <button
        type="button"
        onClick={sahipsizAc}
        className={cn(
          "flex shrink-0 items-center gap-2 border-t border-dashed px-3 py-2.5 text-left text-xs transition-colors",
          sahipsizSecili ? "bg-muted/60 text-foreground" : "text-muted-foreground hover:bg-muted/40",
        )}
      >
        <span aria-hidden>📥</span>
        <span className="min-w-0 flex-1 truncate">sahipsiz teslimler</span>
        <span className="shrink-0 tabular-nums">
          {sahipsizToplam !== null
            ? sahipsizToplam
            : sahipsiz !== null
              ? sahipsiz.length
              : "ölçülemedi"}
        </span>
      </button>
    </div>
  );
}
