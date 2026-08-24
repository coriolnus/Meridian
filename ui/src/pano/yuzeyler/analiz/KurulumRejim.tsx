"use client";

/* ============================================================================
   KURULUM × REJİM — verim matrisi (şerit parsel haritası)
   ----------------------------------------------------------------------------
   YOĞUNLUĞU `n` ÇİZİYOR, ORTALAMAYI RENK DEĞİL. Uç `n`i tam bu iş için dışarı
   veriyor (api.py:2266 şerhi: "pano onu yoğunluk olarak çizer — 3 işlemlik bir
   hücre seyrek görünür, 55 işlemlik hücre dolu. Az örnekli bir ortalamayı çok
   örnekliymiş gibi göstermek bu sistemin reddettiği tek şeydir"). Bu yüzden
   hücrenin ZEMİNİ örneklem yoğunluğunu, YAZI RENGİ ise ortalama R'nin işaretini
   taşıyor: koyu bir hücre "çok işlem", yeşil bir sayı "artıda" demek. Tek kanala
   sıkıştırmak, 3 işlemlik parlak bir hücreyi 55 işlemlikle aynı gösterirdi.

   BOŞ HÜCRE "ÖLÇÜLEMEDİ" DEĞİL, "EKİLMEMİŞ": uç bu hücreye `null` bastığında o
   kurulum o rejimde HİÇ işlem görmemiş demektir — sayım yapıldı ve sıfır çıktı.
   Ayrımı ekranda yazmak zorundayız, yoksa okur ikisini karıştırır.
   ============================================================================ */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import type { Durum } from "../../veri";
import { Deger, Kapi, Olculemedi, pnlRengi, rKati, sayi, yuzde } from "./ortak";
import type { PlotHucre, PlotlarGovdesi } from "./tipler";

/** Zemin yoğunluğu = hücrenin örneklem payı. Jetondan türetilir, çıplak renk YOK. */
function zemin(n: number, enCok: number): string {
  if (enCok <= 0) return "transparent";
  const oran = Math.max(0, Math.min(1, n / enCok));
  return `color-mix(in oklab, var(--chart-2) ${Math.round(oran * 55)}%, transparent)`;
}

function cikisOzeti(h: PlotHucre): string {
  const cikislar = h.exits ?? [];
  if (cikislar.length === 0) return "çıkış nedeni etiketi yok";
  return cikislar.map(([ad, adet]) => `${ad}: ${adet}`).join(" · ");
}

export function KurulumRejim({ plots }: { plots: Durum<PlotlarGovdesi> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Kurulum × rejim verimi</CardTitle>
        <CardDescription>
          Hangi kurulum hangi rejimde ne verdi? Zemin koyuluğu örneklem yoğunluğu, sayının rengi ortalama R'nin
          işareti.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Kapi durum={plots} ad="/api/plots" yukseklik="h-56">
          {(v) => <MatrisGovdesi veri={v} />}
        </Kapi>
      </CardContent>
    </Card>
  );
}

function MatrisGovdesi({ veri }: { veri: PlotlarGovdesi }) {
  const kurulumlar = veri.setups ?? [];
  const rejimler = veri.regimes ?? [];
  const izgara = veri.grid ?? [];

  if (kurulumlar.length === 0 || rejimler.length === 0) {
    return (
      <Olculemedi
        neden={`Matrisin ekseni kurulamadı: ${kurulumlar.length} kurulum, ${rejimler.length} rejim geldi. Uç yalnız setup VE regime etiketi taşıyan kapanmış işlemleri sayıyor — defterde böyle işlem yoksa eksen boş kalır (defterin tamamı: ${sayi(veri.n_trades_total, 0) ?? "ölçülemedi"} işlem).`}
      />
    );
  }

  let enCok = 0;
  izgara.forEach((satir) => {
    (satir.cells ?? []).forEach((h) => {
      if (h && typeof h.n === "number" && h.n > enCok) enCok = h.n;
    });
  });

  const etiketli = veri.n_trades;
  const tumu = veri.n_trades_total;
  const etiketsiz =
    typeof etiketli === "number" && typeof tumu === "number" ? Math.max(0, tumu - etiketli) : null;

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] border-separate border-spacing-1 text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-card px-2 py-1 text-left font-normal text-muted-foreground text-xs">
                kurulum \ rejim
              </th>
              {rejimler.map((r) => (
                <th key={r} className="px-2 py-1 text-center font-normal text-muted-foreground text-xs">
                  {r}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {izgara.map((satir, si) => {
              const ad = satir.setup ?? kurulumlar[si] ?? `satır ${si}`;
              const hucreler = satir.cells ?? [];
              return (
                <tr key={ad}>
                  <th className="sticky left-0 z-10 max-w-40 truncate bg-card px-2 py-2 text-left font-medium text-xs">
                    {ad}
                  </th>
                  {rejimler.map((rej, ri) => {
                    const h = hucreler[ri] ?? null;
                    if (!h) {
                      return (
                        <td
                          key={rej}
                          className="rounded-md border border-border/50 border-dashed px-2 py-2 text-center text-muted-foreground text-xs"
                          title={`${ad} × ${rej}: ekilmemiş parsel — bu kurulum bu rejimde hiç kapanmış işlem üretmedi (sayım yapıldı, sonuç sıfır).`}
                        >
                          ·
                        </td>
                      );
                    }
                    const n = typeof h.n === "number" ? h.n : 0;
                    return (
                      <td
                        key={rej}
                        className="rounded-md border border-border/40 px-2 py-1.5 text-center align-middle"
                        style={{ backgroundColor: zemin(n, enCok) }}
                        title={`${ad} × ${rej} · n=${n} · isabet ${yuzde(h.hit, 1) ?? "ölçülemedi"} · ${cikisOzeti(h)}`}
                      >
                        <div className={`font-medium text-sm tabular-nums ${pnlRengi(h.mean_r)}`}>
                          <Deger
                            metin={rKati(h.mean_r)}
                            neden={`${ad} × ${rej} hücresinde ${n} işlem var ama uç mean_r basmadı — ortalama R ölçülemedi (0,0 DEĞİL).`}
                          />
                        </div>
                        <div className="text-muted-foreground text-[11px] tabular-nums">
                          n={sayi(n, 0)} ·{" "}
                          <Deger
                            metin={yuzde(h.hit, 0)}
                            neden={`${ad} × ${rej} hücresinde isabet oranı gelmedi — kazanan işlem payı ölçülemedi.`}
                          />
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-1.5 text-muted-foreground text-xs leading-relaxed">
        <p>
          <span className="font-medium text-foreground">·</span> işaretli hücre EKİLMEMİŞ parsel: o kurulum o rejimde
          hiç kapanmış işlem üretmedi. "Ölçülemedi" ile aynı şey değil — sayım yapıldı, sonuç sıfır.
        </p>
        <p>
          Matrise giren işlem: {sayi(etiketli, 0) ?? "ölçülemedi"} · defterin tamamı {sayi(tumu, 0) ?? "ölçülemedi"}
          {etiketsiz === null
            ? " · aradaki fark ölçülemedi (uç iki sayaçtan birini basmadı)"
            : etiketsiz > 0
              ? ` · ${etiketsiz} işlem setup ya da regime etiketi taşımadığı için matrise HİÇ girmedi`
              : " · etiketsiz işlem yok"}
        </p>
        <p>En yoğun hücre n={sayi(enCok, 0) ?? "ölçülemedi"} — zemin koyuluğu buna göre ölçeklendi.</p>
      </div>
    </div>
  );
}
