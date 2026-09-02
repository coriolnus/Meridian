"use client";

/* ============================================================================
   KULLANICILAR — "Sisteme kimler erişebiliyor?"
   ----------------------------------------------------------------------------
   OPERATÖR KARARI (2026-08-25): bu yüzey çok kullanıcılı yapının 2. AŞAMA
   İSKELETİDİR. Bugün Meridian TEK OPERATÖRLÜ — `meridian/api.py::api_login` bir
   PAROLA doğruluyor, kullanıcı tablosu YOK; kimlik defteri (`state/auth.json`)
   yalnız `{salt, hash}` tutuyor (auth.py::set_password).

   BU TURUN EN ÖNEMLİ KISITI: dolu görünen ama hiçbir kaydı olmayan bir tablo
   çizmek, olmayan bir yeteneği VAR göstermektir. Şablonun users tablosu on
   uydurma kullanıcıyla geliyor; o veri BURAYA TAŞINMADI. Tablo, bugün gerçekten
   var olan tek şeyi gösteriyor: AÇIK OTURUM. Geri kalan her şey "eksik
   envanteri"nde tek tek sayılı ve her satır kendi kanıtını taşıyor.

   ŞABLONUN GRAMERİ DURUYOR (kolonlar · arama · süzgeç · sayfalama · rozetler):
   2. aşamada değişecek olan VERİ KAYNAĞIDIR, iskelet değil.

   İKİ UÇ, İKİ GEREKÇE:
     · `/api/session`  → bu deponun TEK yetkisiz /api ucu (api.py::api_session). Kimlik
       hakkında sistemin bildiği HER ŞEY burada: oturum geçerli mi, parola kurulu
       mu, çerez Secure mi. Nadiren değişir — 60 sn'de bir yoklanıyor, panonun
       15 sn'lik nabzıyla yarıştırmanın ölçülecek bir karşılığı yok.
     · `useBugun()`    → PAYLAŞILAN `/api/today` nabzı (durum.tsx sözleşmesi).
       Otonomi seviyesi, mod ve broker oradan okunur; kendi isteğini açmak aynı
       ekranda iki farklı "şu an" doğurur.
   ============================================================================ */
import { useEffect, useMemo, type ReactNode } from "react";

import { Fingerprint, ListChecks, Users } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";

import { YUZEYLER } from "../alanlar";
import { useBugun } from "../durum";
import { useRota } from "../rota";
import { useApi } from "../veri";
import { EKSIKLER, EksikEnvanteri } from "./yetki/EksikEnvanteri";
import { type ErisimSatiri, OperatorTablosu } from "./yetki/OperatorTablosu";
import { BolumKart, Kapi, Olculemedi } from "./yetki/parcalar";
import type { OturumGovdesi } from "./yetki/tipler";

/** `/api/session` üç mantık değeri döndürüyor ve üçü de saatler boyunca aynı kalır;
 *  panonun 15 sn'lik nabzına bağlamak aynı cevabı dört kat sık indirmek olurdu. */
const OTURUM_MS = 60_000;

/** `?: T` (alan hiç gelmedi) → `T | null` (ölçüldü/ölçülemedi) çevirisi. Varsayılan
 *  vermek, gelmemiş bir güvenlik alanını "false" diye okutmak olurdu. */
function ucDeger(v: boolean | undefined): boolean | null {
  return v === undefined ? null : v;
}

export function Kullanicilar() {
  const { bolum } = useRota();
  const y = YUZEYLER.users;
  const oturum = useApi<OturumGovdesi>("/api/session", OTURUM_MS);
  const bugun = useBugun();

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  // OTONOMİ SEVİYESİ AYRI BİR UÇTAN GELİYOR ve AYRI DÜŞEBİLİR: `/api/session` okunup
  // `/api/today` düşerse satır çizilir ama "rol" hücresi ölçülemedi der. İki ucu tek
  // kapıya bağlamak, okunabilen bilgiyi de gizlemek olurdu.
  const seviyeBilgisi = useMemo(() => {
    const ham = bugun.veri?.autonomy_level;
    if (typeof ham === "number" && Number.isFinite(ham)) return { seviye: `L${ham}`, no: ham };
    if (typeof ham === "string" && ham.trim() !== "") return { seviye: ham, no: null };
    return { seviye: null, no: null };
  }, [bugun.veri]);

  const seviyeNeden =
    bugun.oturumDustu
      ? "`/api/today` 401 döndü — oturum düştü"
      : bugun.hata !== null
        ? `\`/api/today\` okunamadı — ${bugun.hata}`
        : bugun.veri === null
          ? "`/api/today` henüz okunmadı"
          : "`/api/today` gövdesinde `autonomy_level` alanı yok";

  const modBroker = useMemo(() => {
    const b = bugun.veri;
    const parcalar: string[] = [];
    if (typeof b?.mode === "string" && b.mode !== "") parcalar.push(`mod: ${b.mode}`);
    if (typeof b?.broker === "string" && b.broker !== "") parcalar.push(`broker: ${b.broker}`);
    return parcalar.length > 0 ? parcalar.join(" · ") : null;
  }, [bugun.veri]);

  const satirlar = useMemo<readonly ErisimSatiri[]>(() => {
    const s = oturum.veri;
    if (s === null) return [];
    return [
      {
        kimlik: "oturum-sahibi",
        etiket: "Oturum sahibi",
        seviye: seviyeBilgisi.seviye,
        seviyeNeden,
        modBroker,
        modNeden: "`/api/today` gövdesinde `mode`/`broker` alanları yok",
        parolaKurulu: ucDeger(s.password_set),
        oturumAcik: ucDeger(s.authenticated),
        tls: ucDeger(s.tls),
      },
    ];
  }, [oturum.veri, seviyeBilgisi.seviye, seviyeNeden, modBroker]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
      </div>

      {/* KÜNYE ŞERİDİ — üç sayı, üçü de ölçülmüş. "Kayıt" sayısı tablodan,
          seviye `/api/today`ten, eksik sayısı kaynak taramasından gelir. */}
      <Card>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <Kunye baslik="Erişim kaydı">
            <Kapi durum={oturum} yol="/api/session">
              {() => (
                <span className="font-semibold text-2xl tabular-nums">
                  {satirlar.length}
                  <span className="ms-2 font-normal text-muted-foreground text-xs">
                    kullanıcı kaydı yok — bu bir OTURUM
                  </span>
                </span>
              )}
            </Kapi>
          </Kunye>
          <Kunye baslik="Yetki seviyesi">
            {seviyeBilgisi.seviye === null ? (
              <Olculemedi neden={seviyeNeden} />
            ) : (
              <span className="font-semibold text-2xl tabular-nums">
                {seviyeBilgisi.seviye}
                <span className="ms-2 font-normal text-muted-foreground text-xs">
                  kişiye değil SİSTEME ait
                </span>
              </span>
            )}
          </Kunye>
          <Kunye baslik="2. aşamada gelecek">
            <span className="font-semibold text-2xl tabular-nums">
              {EKSIKLER.length}
              <span className="ms-2 font-normal text-muted-foreground text-xs">kalem, kaynak taramasıyla</span>
            </span>
          </Kunye>
        </CardContent>
      </Card>

      <BolumKart
        kimlik="oturum"
        baslik="Bugün gerçekten var olan erişim"
        soru="Sisteme kim girebiliyor ve hangi yetkiyle?"
        ikon={Users}
      >
        <Kapi durum={oturum} yol="/api/session">
          {() => <OperatorTablosu satirlar={satirlar} />}
        </Kapi>
        <p className="text-muted-foreground text-xs leading-5">
          Bu tablo tek satırlıdır çünkü sistemde tek kayıt vardır. `api_login` bir PAROLA doğruluyor,
          bir KİMLİK değil (api.py::api_login) — yani "kim girdi" sorusunun cevabı bugün
          yalnızca "geçerli parolayı bilen biri"dir. Satırın adı bile ölçülmüş değil; sistemin ad
          alanı yok.
        </p>
      </BolumKart>

      <BolumKart
        kimlik="eksikler"
        baslik="Çok kullanıcılı yapı — 2. aşama"
        soru="Bu yüzeyin gerçekten dolması için ne gerekiyor?"
        ikon={ListChecks}
      >
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Fingerprint />
            </EmptyMedia>
            <EmptyTitle>Çok kullanıcılı yapı 2. aşamada; bugün tek operatör</EmptyTitle>
            <EmptyDescription>
              Kullanıcı tablosu, davet ucu ve rol ataması bu depoda HENÜZ YOK. Aşağıdaki envanter
              onları tek tek sayıyor ve her satır hangi dosyadan ölçüldüğünü yazıyor — "sonra
              yaparız" cümlesi ancak sayılabildiğinde bir plandır.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>

        <EksikEnvanteri />

        <p className="text-muted-foreground text-xs leading-5">
          GRAFİK YOK — ve bu bir eksiklik değil bir hüküm: tek kayıtlı bir kümenin dağılım grafiği
          okuyucuya bir dağılım VARMIŞ gibi görünür. Çizilecek dağılım doğduğunda (2. aşama) grafik
          de bu bölüme gelir.
        </p>
      </BolumKart>
    </div>
  );
}

function Kunye({ baslik, children }: { readonly baslik: string; readonly children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-muted-foreground text-xs">{baslik}</span>
      {children}
    </div>
  );
}
