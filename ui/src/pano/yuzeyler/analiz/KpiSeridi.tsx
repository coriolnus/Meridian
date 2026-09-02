"use client";

/* ============================================================================
   KPI ŞERİDİ — defterin dört (beş) sayısı, hiçbiri uydurulmadan
   ----------------------------------------------------------------------------
   ŞERİT `score_detail`E BAKAR VE O UÇ İKİ ŞEKİLLİDİR (score.py::score_detail):
   örneklem `min_sample`in altındayken uç YALNIZ `{score, n, min_sample, reason}`
   basar — `win_rate`, `avg_r`, `max_drawdown`, `sharpe` alanları HİÇ YOKTUR.
   Bu yüzden her kart alanın VARLIĞINI sorar (`=== undefined`), değerine bakmaz;
   yoksa uçtan gelen `reason` cümlesini ekrana taşır. Kartı 0 ile doldurmak
   "ölçtük, sıfır çıktı" derdi — oysa doğru cümle "yeterli işlem yok".

   SHARPE'IN AYRI BİR TUZAĞI VAR: uç ölçemediğinde `sharpe`ı 0.0 basar (muhafazakâr
   taraf, kapıyı gevşetmesin diye) ve ölçülebilirliği AYRI bir bayrakla söyler
   (`sharpe_measurable`, score.py::score_detail). Yalnız sayıya bakan bir kart "Sharpe 0"
   yazar ve bu YANLIŞ okunur. Kart önce bayrağa bakar.
   ============================================================================ */
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { Durum } from "../../veri";
import { Deger, Kapi, pnlRengi, rKati, sayi, yuzde } from "./ortak";
import type { PerformansGovdesi, SkorKirilimi } from "./tipler";

/** EKRANDA GÖRÜNEN cümle: NE eksik, kullanıcının diliyle. İç ayrıntı `eksikTeknik`te. */
function eksikNeden(sd: SkorKirilimi | undefined, alanAdi: string): string {
  if (!sd) return `Skor kırılımı hiç gelmedi — ${alanAdi} hesaplanmadı.`;
  if (typeof sd.reason === "string" && sd.reason.length > 0) {
    return `Yeterli kapanmış işlem yok — bu eşiğin altında ${alanAdi} hiç hesaplanmıyor (sıfır değil: hesaplanmadı).`;
  }
  return `${alanAdi} bu turda hesaplanmadı ve nedeni de bildirilmedi.`;
}

/** ÜSTÜNE GELİNCE ÇIKAN katman: alanın neden basılmadığı, ucun kendi cümlesiyle.
 *  Düşürülmesi yasak — teşhis eden kişinin tek ipucu bu. */
function eksikTeknik(sd: SkorKirilimi | undefined, alanAdi: string): string {
  if (!sd) return `/api/performance yükünde score_detail bloğu yok — ${alanAdi} hiç hesaplanmadı`;
  if (typeof sd.reason === "string" && sd.reason.length > 0) return sd.reason;
  return `score_detail bu turda ${alanAdi} alanını basmadı; uç nedenini de yazmadı`;
}

function KpiKart({
  baslik,
  metin,
  neden,
  teknik,
  alt,
  renk,
}: {
  baslik: string;
  metin: string | null;
  neden: string;
  teknik?: string;
  alt: string;
  renk?: string;
}) {
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="font-normal text-muted-foreground text-sm">{baslik}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <div className={`text-2xl leading-none tracking-tight tabular-nums ${renk ?? ""}`}>
          <Deger metin={metin} neden={neden} teknik={teknik} />
        </div>
        <p className="text-muted-foreground text-xs leading-snug">{alt}</p>
      </CardContent>
    </Card>
  );
}

export function KpiSeridi({ perf }: { perf: Durum<PerformansGovdesi> }) {
  return (
    <Kapi durum={perf} ad="/api/performance" yukseklik="h-24">
      {(v) => {
        const sd = v.score_detail;
        const n = typeof sd?.n === "number" ? sd.n : v.n_trades;
        const minOrneklem = typeof sd?.min_sample === "number" ? sd.min_sample : null;
        // SHARPE: önce bayrak, sonra sayı (bkz. dosya başı şerhi).
        const sharpeOlculdu = sd?.sharpe_measurable === true;

        return (
          <div className="overflow-hidden rounded-xl bg-card shadow-xs ring-1 ring-foreground/10">
            <div className="grid divide-y *:data-[slot=card]:rounded-none *:data-[slot=card]:ring-0 md:grid-cols-2 md:divide-x md:divide-y-0 xl:grid-cols-5">
              <KpiKart
                baslik="Kapanmış işlem"
                metin={sayi(n, 0)}
                neden="Kapanmış işlem sayısı okunamadı"
                teknik="/api/performance ne score_detail.n ne de n_trades bastı"
                alt={
                  minOrneklem === null
                    ? "Skor eşiği (min_sample) uçtan gelmedi."
                    : `Skor kapısının eşiği ${minOrneklem} işlem.`
                }
              />
              <KpiKart
                baslik="Tutan oran"
                metin={sd?.win_rate === undefined ? null : yuzde(sd.win_rate, 1)}
                neden={eksikNeden(sd, "tutan oran")}
                teknik={eksikTeknik(sd, "tutan oran")}
                alt="r_multiple > 0 olan kapanmış işlemlerin payı."
              />
              <KpiKart
                baslik="Ortalama R"
                metin={sd?.avg_r === undefined ? null : rKati(sd.avg_r)}
                neden={eksikNeden(sd, "ortalama R")}
                teknik={eksikTeknik(sd, "ortalama R")}
                alt="1R = plan kurulurken göze alınan risk."
                renk={pnlRengi(sd?.avg_r)}
              />
              <KpiKart
                baslik="En kötü düşüş"
                metin={sd?.max_drawdown === undefined ? null : yuzde(sd.max_drawdown, 1)}
                neden={eksikNeden(sd, "en kötü düşüş")}
                teknik={eksikTeknik(sd, "en kötü düşüş")}
                alt="Kapanmış işlem eğrisi üstünde; açık pozisyon düşüşü ayrı ölçülür."
              />
              <KpiKart
                baslik="Sharpe"
                metin={sharpeOlculdu ? sayi(sd?.sharpe, 2) : null}
                neden={
                  sd?.sharpe_measurable === false
                    ? "Sharpe ölçülemedi — örneklem üçün altında ya da işlem getirilerinin oynaklığı sıfır. Buradaki boşluk 'ölçüldü, sıfır çıktı' demek değil."
                    : eksikNeden(sd, "Sharpe")
                }
                teknik={
                  sd?.sharpe_measurable === false
                    ? "score_detail.sharpe_measurable=false — uç bu hâlde sayıyı 0.0 basar"
                    : eksikTeknik(sd, "Sharpe")
                }
                alt="Yıllıklandırılmış; ölçülebilirliği ayrı bayrakla gelir."
              />
            </div>
          </div>
        );
      }}
    </Kapi>
  );
}
