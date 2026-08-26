"use client";

/* ============================================================================
   KATMAN 1 — MAKİNE (`/api/infra` · `makine` bloğu)
   ----------------------------------------------------------------------------
   OPERATÖRÜN AYRIMI: "sistemin çalıştığı altyapı bileşenlerini AYRI, Meridian'ın
   alt bileşenlerini AYRI". Bu bölüm YALNIZ makineyi anlatır — kutunun kendisi.
   Meridian'ın süreçleri bir alt bölümde ve o ayrım bilerek keskin: bir birimin
   %100 CPU yemesi ile makinenin doyması aynı arıza değildir ve aynı müdahaleyi
   istemez.

   PLATFORM FARKI GİZLENMEZ: bu depo YERELDE macOS, CANLIDA Linux koşuyor ve
   `/proc` macOS'ta YOK. Uç bu durumda `cpu_yuzde`/`uptime_s`i None + neden ile
   döndürüyor (test C maddesi) — biz de kadran çizmek yerine nedeni basıyoruz.
   Boş bir kadran "%0 kullanım" diye okunur ve o yalanın adı bu depoda uydurmadır.

   ZAMAN SERİSİ TARAYICIDA BİRİKİR ve bu ekranda AÇIKÇA yazıyor: uç geçmiş
   tutmuyor (gövdede seri alanı YOK), her anket TEK bir anlık ölçüm veriyor.
   Örnekler `hesaplama_ts`e göre TEKİLLEŞTİRİLİR — uç 15 sn önbellekli ve aynı
   ölçümü iki kez çizmek, duran bir sayıyı "yeni ölçüm" diye göstermek olurdu.
   Sayfa yenilendiğinde seri sıfırlanır; bu bir kayıp değil, serinin ne olduğunun
   dürüst sonucudur.
   ============================================================================ */
import { useEffect, useRef, useState } from "react";
import { Cpu } from "lucide-react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

import type { Durum } from "../../veri";
import { Gosterge } from "./Gosterge";
import { BolumKart, Deger, Kapi, Olculemedi, OlcekCubugu, Satir, baytMetni, sureMetni, zamanMetni } from "./parcalar";
import type { InfraGovdesi, InfraMakine } from "./uctipleri";

const SERI_TAVANI = 60; // ≈15 dk (15 sn nabızla). Sınırsız dizi, saatlerce açık kalan panoda sızıntıdır.

const SERI_GRAFIGI: ChartConfig = {
  cpu: { label: "CPU %", color: "var(--chart-1)" },
  ram: { label: "Bellek %", color: "var(--chart-3)" },
};

interface Ornek {
  readonly ts: string;
  readonly saat: string;
  readonly cpu: number | null;
  readonly ram: number | null;
}

/**
 * Bellek doluluğunu UÇ ÖLÇÜYOR (`bellek.kullanim_yuzde`, api.py:6240) — burada YENİDEN
 * HESAPLANMAZ. İkinci bir hesap, aynı yasanın iki kaynağı demektir ve ucun yuvarlaması ile
 * bizimki ayrıştığında ekranda hangisinin doğru olduğu bilinemezdi.
 */
function bellekYuzdesi(m: InfraMakine | undefined): number | null {
  const v = m?.bellek?.kullanim_yuzde;
  return typeof v === "number" ? v : null;
}

/** Disk doluluğu da ucun kendi ölçümüdür (`disk[].kullanim_yuzde`) — türetilmez. */
function diskYuzdesi(d: { readonly kullanim_yuzde?: number | null }): number | null {
  return typeof d.kullanim_yuzde === "number" ? d.kullanim_yuzde : null;
}

/**
 * Anket örneklerini biriktirir. `hesaplama_ts` TEKİLLEŞTİRİCİDİR: uç 15 sn önbellekli
 * (`onbellekten: true` kopyası aynı damgayı taşır) ve aynı ölçümü ikinci kez çizmek,
 * grafiğe var olmayan bir gözlem eklemek olurdu.
 */
function useOrnekler(veri: InfraGovdesi | null): readonly Ornek[] {
  const [ornekler, setOrnekler] = useState<readonly Ornek[]>([]);
  const sonDamga = useRef<string | null>(null);

  useEffect(() => {
    const ts = veri?.hesaplama_ts;
    if (!ts || ts === sonDamga.current) return;
    sonDamga.current = ts;
    const t = new Date(ts);
    const cpu = veri?.makine?.cpu_yuzde;
    const yeni: Ornek = {
      ts,
      saat: Number.isNaN(t.getTime()) ? ts.slice(11, 19) : t.toLocaleTimeString("tr-TR", { timeStyle: "medium" }),
      cpu: typeof cpu === "number" ? cpu : null,
      ram: bellekYuzdesi(veri?.makine),
    };
    setOrnekler((eski) => [...eski, yeni].slice(-SERI_TAVANI));
  }, [veri]);

  return ornekler;
}

export function Makine({ durum }: { readonly durum: Durum<InfraGovdesi> }) {
  const ornekler = useOrnekler(durum.veri);

  return (
    <BolumKart
      kimlik="makine"
      baslik="Makine"
      soru="Kutu sağlam mı — işlemci, bellek, disk nerede duruyor?"
      ikon={Cpu}
      aksiyon={
        durum.veri?.onbellekten !== undefined ? (
          <Badge
            variant="outline"
            title={`hesaplama_ts: ${durum.veri.hesaplama_ts ?? "yok"} — kopya kendini taze gibi damgalamaz`}
          >
            {durum.veri.onbellekten
              ? `önbellekten · ${durum.veri.zarf_yasi_s ?? "?"} sn yaşında`
              : "taze ölçüm"}
          </Badge>
        ) : null
      }
    >
      <Kapi durum={durum} yol="/api/infra">
        {(g) => {
          const m = g.makine;
          if (m === undefined) {
            return <Olculemedi neden="Makine ölçümleri bildirilmedi" teknik="/api/infra `makine` bloğunu döndürmüyor" />;
          }
          const ramYuzde = bellekYuzdesi(m);
          const diskler = m.disk ?? [];
          const bellek = m.bellek;

          return (
            <>
              {/* --- KADRANLAR --- */}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <Gosterge
                  baslik="İşlemci"
                  yuzde={m.cpu_yuzde}
                  neden="İşlemci kullanımı ölçülemedi"
                  teknik={m.cpu_yuzde_neden ?? "/api/infra `makine.cpu_yuzde` alanını döndürmüyor"}
                  altMetin={
                    m.cekirdek_n !== undefined && m.cekirdek_n !== null ? `${m.cekirdek_n} çekirdek` : null
                  }
                />
                <Gosterge
                  baslik="Bellek"
                  yuzde={ramYuzde}
                  neden="Bellek doluluğu hesaplanamadı"
                  teknik={
                    bellek?.olculemedi_neden ??
                    "kullanılan/toplam bayt birlikte gelmedi — doluluk TÜRETİLEMEZ (uydurma yasağı)"
                  }
                  altMetin={
                    bellek
                      ? `${baytMetni(bellek.kullanilan_bayt) ?? "?"} / ${baytMetni(bellek.toplam_bayt) ?? "?"}`
                      : null
                  }
                />
                {diskler.slice(0, 2).map((d, i) => {
                  const ad = d.yol ?? `disk #${i + 1}`;
                  return (
                    <Gosterge
                      key={ad}
                      baslik={`Disk ${ad}`}
                      yuzde={diskYuzdesi(d)}
                      neden="Disk doluluğu ölçülemedi"
                      teknik={d.olculemedi_neden ?? "/api/infra bu bölüm için `kullanim_yuzde` döndürmedi"}
                      altMetin={`${baytMetni(d.kullanilan_bayt) ?? "?"} / ${baytMetni(d.toplam_bayt) ?? "?"}`}
                    />
                  );
                })}
                {diskler.length === 0 ? (
                  <div className="col-span-2 flex min-h-40 items-center justify-center rounded-lg border border-dashed p-4">
                    <Olculemedi neden="Makinenin diskleri bildirilmedi" teknik="/api/infra `makine.disk` listesi boş ya da yok" />
                  </div>
                ) : null}
              </div>

              {/* --- ZAMAN SERİSİ (tarayıcıda biriken) --- */}
              {ornekler.length >= 2 ? (
                <>
                  <ChartContainer config={SERI_GRAFIGI} className="aspect-auto h-52 w-full">
                    <AreaChart data={[...ornekler]} margin={{ left: 4, right: 8 }}>
                      <defs>
                        <linearGradient id="infraCpu" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--color-cpu)" stopOpacity={0.7} />
                          <stop offset="95%" stopColor="var(--color-cpu)" stopOpacity={0.05} />
                        </linearGradient>
                        <linearGradient id="infraRam" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--color-ram)" stopOpacity={0.7} />
                          <stop offset="95%" stopColor="var(--color-ram)" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="saat" tickLine={false} axisLine={false} minTickGap={40} tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tickLine={false} axisLine={false} width={36} unit="%" />
                      <ChartTooltip cursor={false} content={<ChartTooltipContent indicator="dot" />} />
                      <Area isAnimationActive={false}
                        dataKey="cpu"
                        type="monotone"
                        connectNulls={false}
                        fill="url(#infraCpu)"
                        stroke="var(--color-cpu)"
                      />
                      <Area isAnimationActive={false}
                        dataKey="ram"
                        type="monotone"
                        connectNulls={false}
                        fill="url(#infraRam)"
                        stroke="var(--color-ram)"
                      />
                    </AreaChart>
                  </ChartContainer>
                  <p className="text-muted-foreground text-xs">
                    Seriyi UÇ DEĞİL, BU SAYFA topluyor: `/api/infra` geçmiş tutmuyor, her anket tek bir
                    anlık ölçüm veriyor. Örnekler `hesaplama_ts`e göre tekilleştirildi (önbellekten gelen
                    kopya yeniden çizilmez); pencere en çok {SERI_TAVANI} örnek, sayfa yenilenince sıfırlanır.
                    Şu an {ornekler.length} örnek var. Kopuk çizgi = o ankette değer ölçülemedi (sıfır DEĞİL).
                  </p>
                </>
              ) : (
                <p className="text-muted-foreground text-xs">
                  Zaman serisi için en az iki AYRI ölçüm gerekiyor; şu an {ornekler.length} örnek var. Uç
                  geçmiş tutmadığı için seri bu sayfa açık kaldıkça birikir — geçmişi geriye dönük
                  UYDURMUYORUZ.
                </p>
              )}

              {/* --- KÜNYE --- */}
              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="Ana makine adı">
                    {m.hostname ?? <Olculemedi neden="Makinenin adı bildirilmedi" teknik="/api/infra `makine.hostname` döndürmedi" kisa />}
                  </Satir>
                  <Satir etiket="Platform">
                    {m.platform?.sistem ? (
                      <span>
                        {m.platform.sistem}
                        {m.platform.surum ? ` · ${m.platform.surum}` : ""}
                        {m.platform.makine ? ` · ${m.platform.makine}` : ""}
                      </span>
                    ) : (
                      <Olculemedi neden="İşletim sistemi bildirilmedi" teknik="/api/infra `makine.platform.sistem` döndürmedi" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Çekirdek sayısı">
                    <Deger deger={m.cekirdek_n} neden="Çekirdek sayısı bildirilmedi" teknik={m.cekirdek_n_neden ?? "/api/infra `makine.cekirdek_n` döndürmedi"} />
                  </Satir>
                  <Satir etiket="Çalışma süresi">
                    {sureMetni(m.uptime_s) ?? (
                      <Olculemedi
                        neden="Makinenin ne zamandır açık olduğu ölçülemedi"
                        teknik={m.uptime_s_neden ?? "/api/infra `makine.uptime_s` döndürmedi"}
                        kisa
                      />
                    )}
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Yük ortalaması (1 / 5 / 15 dk)">
                    {m.yuk ? (
                      <span
                        className="tabular-nums"
                        title={
                          m.cekirdek_n
                            ? `${m.cekirdek_n} çekirdek — yük ≈ çekirdek sayısı, kuyruk oluşmaya başladığı yerdir`
                            : undefined
                        }
                      >
                        {[m.yuk["1dk"], m.yuk["5dk"], m.yuk["15dk"]]
                          .map((v) => (typeof v === "number" ? v.toFixed(2) : "?"))
                          .join(" / ")}
                      </span>
                    ) : (
                      <Olculemedi
                        neden="Makinenin yük ortalaması bildirilmedi"
                        teknik={m.yuk_neden ?? "/api/infra `makine.yuk` alanını döndürmedi"}
                        kisa
                      />
                    )}
                  </Satir>
                  {/* AĞ SAYAÇLARI BU UÇTA YOK ve bu bir eksiklik olarak YAZILIYOR: operatörün
                      KATMAN-1 listesinde ağ vardı, `/api/infra` gövdesinde (api.py:6304 return
                      bloğu) yok. Boş bir satır çizip geçmek, sorulan soruyu sorulmamış saymak
                      olurdu; açık kalem olarak duruyor. */}
                  <Satir etiket="Ağ (rx/tx)">
                    <Olculemedi
                      neden="Ağ trafiği bu sürümde hiç ölçülmüyor — ölçüm henüz eklenmedi"
                      teknik="/api/infra makine bloğunda ağ sayacı YOK (uç `hostname/platform/cekirdek_n/yuk/cpu_yuzde/bellek/disk/uptime_s` döndürüyor)"
                      kisa
                    />
                  </Satir>
                  <Satir etiket="Bellek (kullanılan / toplam)">
                    {bellek === undefined ? (
                      <Olculemedi neden="Bellek bilgisi bildirilmedi" teknik="/api/infra `makine.bellek` bloğunu döndürmedi" kisa />
                    ) : bellek.kullanilan_bayt === null || bellek.kullanilan_bayt === undefined ? (
                      <Olculemedi neden="Kullanılan bellek okunamadı" teknik={bellek.olculemedi_neden ?? "bellek ölçülemedi, neden de yazılmadı"} kisa />
                    ) : (
                      <span className="tabular-nums" title={`kaynak: ${bellek.kaynak ?? "beyan edilmedi"}`}>
                        {baytMetni(bellek.kullanilan_bayt)} / {baytMetni(bellek.toplam_bayt) ?? "toplam ölçülemedi"}
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="Ölçüm damgası">
                    {zamanMetni(g.hesaplama_ts) ?? (
                      <Olculemedi neden="Ölçümün yapıldığı an bildirilmedi" teknik="/api/infra `hesaplama_ts` döndürmedi" kisa />
                    )}
                  </Satir>
                </div>
              </div>

              {/* --- TÜM DİSKLER --- */}
              {diskler.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {diskler.map((d, i) => {
                    const ad = d.yol ?? `disk #${i + 1}`;
                    // AYNI BÖLÜMÜ paylaşan yollar TEK satırda toplanıyor (uç `kapsayan_yollar` ile
                    // söylüyor): `/`, depo kökü ve `state/` çoğu kurulumda tek dosya sistemidir ve
                    // üç ayrı satır aynı sayıyı üç kez basıp "üç disk" sandırırdı.
                    const kapsanan = d.kapsayan_yollar ?? [];
                    return (
                      <OlcekCubugu
                        key={`cubuk-${ad}-${i}`}
                        etiket={kapsanan.length > 1 ? `${ad} (+${kapsanan.length - 1} yol)` : ad}
                        yuzde={diskYuzdesi(d)}
                        neden="Disk doluluğu ölçülemedi"
                        teknik={d.olculemedi_neden ?? "/api/infra bu bölüm için `kullanim_yuzde` döndürmedi"}
                        altMetin={`${baytMetni(d.kullanilan_bayt) ?? "?"} kullanılıyor · ${
                          baytMetni(d.bos_bayt) ?? "?"
                        } boş`}
                      />
                    );
                  })}
                </div>
              ) : null}

              <p className="text-muted-foreground text-xs">
                Ölçüm yolu: {g.olcum_yolu ?? "uç `olcum_yolu` beyanını döndürmedi"}. Bu yüzden YEREL
                macOS'ta CPU/bellek/uptime "ölçülemedi" görünür ve bu DOĞRUDUR — `/proc` orada yok;
                dolu tablo canlı A1 Linux sunucusunda okunur.
                {typeof durum.veri?.zarf_yasi_s === "number" && durum.veri.zarf_yasi_s > 0
                  ? ` Önbellekten servis edilen bu kopyada çalışma süreleri zarf yaşıyla (${durum.veri.zarf_yasi_s} sn) TOPLANDI — hiçbir alan zarfından taze görünmez.`
                  : ""}
              </p>
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
