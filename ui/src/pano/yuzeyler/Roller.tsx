"use client";

/* ============================================================================
   ROLLER VE YETKİLER — "Hangi rol neyi yapabilir?"
   ----------------------------------------------------------------------------
   BU DEPODA "ROL" DİYE BİR KAVRAM YOK — ve bu yüzeyin ilk işi bunu söylemek.
   Şablonun roles tablosu "System roles / Custom roles" gruplarıyla, sahipleriyle,
   son gözden geçirme tarihleriyle geliyor; hiçbirinin Meridian'da karşılığı yok.
   O tabloyu doldurmak, olmayan bir erişim yönetimi katmanını var göstermek olurdu.

   BUGÜN GERÇEKTEN VAR OLAN YETKİ KAVRAMI OTONOMİ SEVİYESİDİR:
   `state/goal.yaml → limits.autonomy_level`, üç değerli (L0/L1/L2) ve KİŞİYE
   DEĞİL SİSTEME ait. Seviyelerin adları uydurulmadı, uçtan geliyor:
   `/api/summary.ladder.levels[].name` (analytics.py::autonomy_ladder).

   ÜÇ BÖLÜM, ÜÇ AYRI KAYNAK GÜVENİ:
     · seviyeler → UÇTAN (canlı)
     · izinler   → KAYNAK TARAMASI (elle; tablo bunu kendi altında beyan ediyor)
     · terfi     → UÇTAN (canlı; her çağrıda defterden hesaplanıyor)
   Üçünü tek bir "veri" gibi göstermek, elle yazılmış bir matrisi canlı ölçüm
   sanmaya davet ederdi.
   ============================================================================ */
import { useEffect } from "react";

import { GaugeCircle, Scale, ShieldAlert, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { cn } from "@/lib/utils";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { useApi } from "../veri";
import { IzinMatrisi } from "./yetki/IzinMatrisi";
import { BolumKart, Kapi, Olculemedi } from "./yetki/parcalar";
import { TerfiTablosu } from "./yetki/TerfiTablosu";
import type { MerdivenSeviyesi, OzetGovdesi } from "./yetki/tipler";

/** `/api/summary` skor kırılımını defterin tamamı üzerinden hesaplıyor (analytics);
 *  seviye ve terfi ölçütleri saatler ölçeğinde değişir. 90 sn, ucun maliyetiyle
 *  bilginin tazeliği arasındaki dürüst yer. */
const OZET_MS = 90_000;

export function Roller() {
  const { bolum } = useRota();
  const y = YUZEYLER.roles;
  const ozet = useApi<OzetGovdesi>("/api/summary", OZET_MS);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const merdiven = ozet.veri?.ladder;
  const etkin = typeof merdiven?.current_level === "number" ? merdiven.current_level : null;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">{y.baslik}</h1>
        <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
      </div>

      <Empty className="border">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <UserRound />
          </EmptyMedia>
          <EmptyTitle>Rol ataması 2. aşamada; bugün yetki KİŞİYE değil SİSTEME ait</EmptyTitle>
          <EmptyDescription>
            Kullanıcı yok, dolayısıyla kullanıcıya verilecek rol de yok. Yetki tek bir sayıyla
            ifade ediliyor — otonomi seviyesi — ve o sayı tüm sistemi bağlıyor. Aşağıdaki üç bölüm
            o seviyenin bugün NE anlama geldiğini gösteriyor.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>

      <BolumKart
        kimlik="seviyeler"
        baslik="Otonomi seviyeleri"
        soru="Sistem hangi basamakta duruyor?"
        ikon={Scale}
        aksiyon={
          etkin === null ? null : (
            <Badge variant="outline" className="font-mono">
              etkin: L{etkin}
            </Badge>
          )
        }
      >
        <Kapi durum={ozet} yol="/api/summary">
          {(v) => <SeviyeKartlari seviyeler={v.ladder?.levels} etkin={etkin} />}
        </Kapi>
        <p className="text-muted-foreground text-xs leading-5">
          Seviye adları uçtan geliyor (`/api/summary.ladder.levels[].name`), bu dosyada yazılı değil
          — kaynakta değiştiğinde ekran kendiliğinden düzelir. Etkin seviye
          `state/goal.yaml → limits.autonomy_level` değeridir ve onu DEĞİŞTİRMEK bu panonun yetkisi
          değildir: ajan da, pano da o alana yazamaz (yetki sınırı testle çivili).
        </p>
      </BolumKart>

      <BolumKart
        kimlik="izinler"
        baslik="İzin matrisi"
        soru="Hangi seviye neyi yapabiliyor, kaynağı ne?"
        ikon={ShieldAlert}
      >
        <IzinMatrisi etkinSeviye={etkin} />
      </BolumKart>

      <BolumKart
        kimlik="terfi"
        baslik="L0 → L1 terfi kontrolü"
        soru="Ajanın gerçek paraya ne kadar yakın olduğu neyle ölçülüyor?"
        ikon={GaugeCircle}
      >
        <Kapi durum={ozet} yol="/api/summary">
          {(v) =>
            v.ladder === undefined ? (
              <Olculemedi neden="Otonomi merdiveni bildirilmedi" teknik="`/api/summary` gövdesinde `ladder` bloğu yok" />
            ) : (
              <TerfiTablosu merdiven={v.ladder} />
            )
          }
        </Kapi>
      </BolumKart>
    </div>
  );
}

/** Üç seviye kartı. UÇ BOŞ DİZİ DÖNDÜRÜRSE kart uydurulmaz — sabit bir L0/L1/L2
 *  listesi yazmak, uçtan gelmeyen bir yetki tanımını canlı gibi göstermek olurdu. */
function SeviyeKartlari({
  seviyeler,
  etkin,
}: {
  readonly seviyeler: readonly MerdivenSeviyesi[] | undefined;
  readonly etkin: number | null;
}) {
  if (seviyeler === undefined || seviyeler.length === 0) {
    return (
      <Olculemedi neden="Seviye tanımları kaynaktan okunamadı" teknik="`/api/summary.ladder.levels` gelmedi ya da boş" />
    );
  }
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {seviyeler.map((s, i) => {
        const aktif = s.active === true;
        return (
          <div
            key={s.id ?? `seviye-${i}`}
            className={cn(
              "flex min-w-0 flex-col gap-2 rounded-lg border p-4",
              aktif && "border-primary/40 bg-primary/5",
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono font-semibold text-lg">
                {s.id ?? <Olculemedi neden="Seviyenin numarası bildirilmedi" teknik="seviyenin `id` alanı gelmedi" kisa />}
              </span>
              {aktif ? (
                <Badge variant="outline" className="text-[10px]">
                  etkin
                </Badge>
              ) : null}
            </div>
            {s.name === undefined ? (
              <Olculemedi neden="Seviyenin adı bildirilmedi — uydurulmadı" teknik="seviyenin `name` alanı gelmedi" kisa />
            ) : (
              <span className="text-muted-foreground text-sm leading-5">{s.name}</span>
            )}
          </div>
        );
      })}
      {etkin === null ? (
        <div className="sm:col-span-3">
          <Olculemedi neden="Şu an hangi seviyede olunduğu bildirilmedi — etkin seviye vurgulanamadı" teknik="`/api/summary.ladder.current_level` sayı olarak gelmedi" />
        </div>
      ) : null}
    </div>
  );
}
