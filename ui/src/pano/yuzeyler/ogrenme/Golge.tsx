"use client";

/* ============================================================================
   GÖLGE — "gölge hüküm gerçek hükümle aynı şeyi mi söylüyor?"
   ----------------------------------------------------------------------------
   BU BÖLÜMDE İKİ AYRI GÖLGE VAR VE KARIŞTIRILMALARI YASAK:

     (1) GÖLGE YASA (`mlops.shadow_law`) — kapı hükmünün İKİ hesabı. Yürürlükteki
         yasa PARA-v3 KARAR verir; ESKİ bileşik yasa her değerlendirmede yalnız
         KAYDA geçer. "Uyum" burada iki yasanın aynı hükmü verip vermediğidir.
     (2) GÖLGE MODEL (`ogrenme.antrenman`) — işlem sonucunu tahmin eden model.
         Onun "uyumu" bir Brier'dir, bir hüküm karşılaştırması değil.

   İkisini tek bir "gölge uyum %" sayısına indirgemek en kolay yalan olurdu: paydaları
   farklı (biri hipotez kaydı, öteki kapanmış işlem çifti) ve biri ölçülemezken öteki
   ölçülebilir. Ayrı kutularda, ayrı paydalarıyla duruyorlar.

   GEÇİŞ ÖNCESİ KAYIT SIFIR DEĞİLDİR. `gecis_oncesi_kayit`, gölge alanı hiç yazılmamış
   kayıtları sayar (retro damga yasağı). Bunları "uyumlu" kovasına saymak, ölçülmemiş bir
   hükmü uyum sayısına yazmak olurdu — grafikte AYRI ve nötr renkte duruyorlar.
   ============================================================================ */
import { Bar, BarChart, CartesianGrid, Cell, LabelList, XAxis, YAxis } from "recharts";
import { FlaskConical } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Progress } from "@/components/ui/progress";

import type { Durum } from "../../veri";
import {
  anMetni,
  Beyan,
  BolumKarti,
  Deger,
  Kapi,
  Kutu,
  Olculemedi,
  Satir,
  sayi,
  UcDegerli,
  yas,
  yuzde,
} from "./ortak";
import type { AntrenmanDurumu, GolgeYasasi, OgrenmeBlogu, TeshisGovdesi } from "./tipler";

const UYUM_CONFIG = {
  n: { label: "Kayıt" },
  uyumlu: { label: "İki yasa aynı hükmü verdi", color: "var(--chart-2)" },
  iraksayan: { label: "Iraksadı", color: "var(--destructive)" },
  olcusuz: { label: "Geçiş öncesi (gölge ölçülmemiş)", color: "var(--muted-foreground)" },
} satisfies ChartConfig;

interface UyumKovasi {
  readonly kova: string;
  readonly n: number;
  readonly renk: string;
  readonly opaklik: number;
  readonly aciklama: string;
}

export function Golge({ teshis }: { teshis: Durum<TeshisGovdesi> }) {
  return (
    <BolumKarti kimlik="golge" baslik="Gölge" soru="Gölge uyum ne gösteriyor?" ikon={FlaskConical}>
      <Kapi durum={teshis} ad="/api/diagnostics" yukseklik="h-64">
        {(v) => (
          <div className="flex flex-col gap-6">
            <GolgeYasaKutusu yasa={v.mlops?.shadow_law} />
            <GolgeModelKutusu ogrenme={v.ogrenme} />
          </div>
        )}
      </Kapi>
    </BolumKarti>
  );
}

/* ---- (1) GÖLGE YASA ------------------------------------------------------ */

function GolgeYasaKutusu({ yasa }: { yasa: GolgeYasasi | undefined }) {
  if (!yasa) {
    return (
      <Kutu baslik="Gölge yasa — iki hesabın uyumu">
        <Olculemedi neden="/api/diagnostics yükünde `mlops.shadow_law` bloğu YOK — çift hesabın uyumu bu turda hiç ölçülmedi." />
      </Kutu>
    );
  }

  const sayilan = typeof yasa.golge_kayit_sayisi === "number" ? yasa.golge_kayit_sayisi : null;
  const iraksayan = typeof yasa.iraksayan_kayit === "number" ? yasa.iraksayan_kayit : null;
  const oncesi = typeof yasa.gecis_oncesi_kayit === "number" ? yasa.gecis_oncesi_kayit : null;
  const uyumlu = sayilan !== null && iraksayan !== null ? sayilan - iraksayan : null;

  const kovalar: UyumKovasi[] = [];
  if (uyumlu !== null) {
    kovalar.push({
      kova: "Uyumlu",
      n: uyumlu,
      renk: "var(--color-uyumlu)",
      opaklik: 0.9,
      aciklama: "PARA-v3 ile eski bileşik yasa AYNI hükmü verdi.",
    });
  }
  if (iraksayan !== null) {
    kovalar.push({
      kova: "Iraksayan",
      n: iraksayan,
      renk: "var(--color-iraksayan)",
      opaklik: 0.9,
      aciklama: "İki yasa FARKLI hüküm verdi — süreklilik bu satırda kırılıyor.",
    });
  }
  if (oncesi !== null) {
    kovalar.push({
      kova: "Geçiş öncesi",
      n: oncesi,
      renk: "var(--color-olcusuz)",
      opaklik: 0.45,
      aciklama: "Gölge alanı hiç yazılmamış (retro damga yasağı) — uyum ya da ıraksama olarak SAYILMAZ.",
    });
  }

  // UYUM ORANI YALNIZ ÖLÇÜLEN PAYDA ÜSTÜNDE: geçiş öncesi kayıtlar paydaya girmez,
  // çünkü onların gölge hükmü hiç hesaplanmadı. Paydaya katsaydım oran mekanik olarak
  // yükselirdi ve yükselişin sebebi "daha çok uyum" değil "daha çok ölçülmemiş kayıt" olurdu.
  const oran = sayilan !== null && sayilan > 0 && uyumlu !== null ? uyumlu / sayilan : null;
  const son = yasa.son_kayit;

  return (
    <Kutu
      baslik="Gölge yasa — iki hesabın uyumu"
      aciklama="Kapı hükmünü PARA-v3 verir; eski bileşik yasa aynı anda ölçülüp kayda geçer. Uyum = ikisinin aynı hükmü verdiği kayıt payı."
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">yasa sürümü: {yasa.yasa_surumu ?? "ölçülemedi"}</Badge>
        {yasa.gecis_tarihi ? <Badge variant="outline">geçiş: {yasa.gecis_tarihi}</Badge> : null}
        <UcDegerli
          deger={yasa.law_transition ?? null}
          evet="geçiş YAPILDI"
          hayir="geçiş yapılmadı"
          neden="`shadow_law.law_transition` yükte yok — hangi yasanın karar verdiği ölçülemedi; p değerlerini hangi yasanın p'si sayacağın belirsiz."
        />
      </div>

      {kovalar.length === 0 ? (
        <Olculemedi neden="`golge_kayit_sayisi` / `iraksayan_kayit` / `gecis_oncesi_kayit` alanlarının hiçbiri sayı taşımıyor — uyum ölçülemedi." />
      ) : (
        <ChartContainer config={UYUM_CONFIG} className="aspect-auto h-44 w-full">
          <BarChart data={kovalar} layout="vertical" margin={{ bottom: 0, left: 0, right: 28, top: 4 }}>
            <CartesianGrid horizontal={false} />
            <XAxis type="number" axisLine={false} tickLine={false} allowDecimals={false} />
            <YAxis type="category" dataKey="kova" axisLine={false} tickLine={false} width={104} />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  className="w-64"
                  formatter={(deger, _ad, yuk) => {
                    const p = (yuk as { payload?: UyumKovasi } | undefined)?.payload;
                    return (
                      <span className="flex flex-col gap-0.5">
                        <span className="text-muted-foreground">
                          kayıt <span className="ml-1 font-medium text-foreground tabular-nums">{String(deger)}</span>
                        </span>
                        {p ? <span className="text-muted-foreground text-xs leading-snug">{p.aciklama}</span> : null}
                      </span>
                    );
                  }}
                />
              }
            />
            <Bar isAnimationActive={false} dataKey="n" radius={4}>
              <LabelList dataKey="n" position="right" className="fill-muted-foreground" fontSize={11} />
              {kovalar.map((k) => (
                <Cell key={k.kova} fill={k.renk} fillOpacity={k.opaklik} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      )}

      <div className="flex flex-col">
        <Satir etiket="Uyum oranı (ölçülen payda üstünde)">
          <Deger
            metin={oran === null ? null : yuzde(oran, 1)}
            neden={
              sayilan === null
                ? "`golge_kayit_sayisi` yok — payda kurulamadı."
                : "gölge hükmü ölçülen kayıt YOK (payda 0) — oran tanımsız, %100 DEĞİL."
            }
          />
        </Satir>
        <Satir etiket="Ölçülen kayıt (payda)">
          <Deger metin={sayi(sayilan, 0)} neden="`golge_kayit_sayisi` yükte yok." />
        </Satir>
        <Satir etiket="Geçiş öncesi (paydaya girmez)">
          <Deger metin={sayi(oncesi, 0)} neden="`gecis_oncesi_kayit` yükte yok." />
        </Satir>
      </div>

      {son ? (
        <div className="rounded-md border border-border/60 p-3">
          <p className="font-medium text-sm">
            Son kayıt {son.id ? <code className="rounded bg-muted px-1 py-0.5 text-xs">{son.id}</code> : null}
            {son.dilim ? <span className="ml-1 text-muted-foreground text-xs">· {son.dilim} dilimi</span> : null}
          </p>
          <div className="mt-2 flex flex-col">
            <Satir etiket="p (PARA-v3, KARAR veren)">
              <Deger metin={sayi(son.p_v3, 3)} neden="`son_kayit.p_v3` yok — karar veren yasanın p'si ölçülemedi." />
            </Satir>
            <Satir etiket="p (eski yasa, yalnız kayıt)">
              <Deger metin={sayi(son.p_eski, 3)} neden="`son_kayit.p_eski` yok — gölge hesap bu kayıtta çalışmamış." />
            </Satir>
            <Satir etiket="Gerekli p">
              <Deger metin={sayi(son.p_required, 3)} neden="`son_kayit.p_required` yok — eşik ölçülemedi." />
            </Satir>
            <Satir etiket="v3 geçti mi?">
              <UcDegerli
                deger={son.v3_gecti ?? null}
                evet="geçti"
                hayir="geçmedi"
                neden="`son_kayit.v3_gecti` yok — kararın kendisi bu kayıttan okunamadı."
              />
            </Satir>
            <Satir etiket="Eski yasa geçirir miydi?">
              <UcDegerli
                deger={son.eski_gecerdi ?? null}
                evet="geçirirdi"
                hayir="geçirmezdi"
                neden="`son_kayit.eski_gecerdi` yok — gölge hüküm bu kayıtta ölçülmemiş."
                evetIyi={son.v3_gecti === true}
              />
            </Satir>
          </div>
        </div>
      ) : (
        <Olculemedi neden="`shadow_law.son_kayit` null — gölge alanı yazılmış tek bir hipotez kaydı bile yok; son karşılaştırma gösterilemiyor." />
      )}

      {yasa.aktif_yasa ? <Beyan>{yasa.aktif_yasa}</Beyan> : null}
      {yasa.golge_yasa ? <Beyan>{yasa.golge_yasa}</Beyan> : null}
      {yasa.beyan ? <Beyan>{yasa.beyan}</Beyan> : null}
    </Kutu>
  );
}

/* ---- (2) GÖLGE MODEL ----------------------------------------------------- */

function GolgeModelKutusu({ ogrenme }: { ogrenme: OgrenmeBlogu | undefined }) {
  if (!ogrenme) {
    return (
      <Kutu baslik="Gölge model — antrenman ve terfi">
        <Olculemedi neden="/api/diagnostics yükünde `ogrenme` bloğu YOK — gölge modelin antrenman durumu bu turda hiç ölçülmedi." />
      </Kutu>
    );
  }
  const a: AntrenmanDurumu | null | undefined = ogrenme.antrenman;
  const fit = ogrenme.son_fit;
  const deneme = ogrenme.son_deneme;
  const terfi = fit?.terfi;
  const nabiz = ogrenme.nabiz?.["shadow_fit"];

  const nLive = a?.terfi?.n_live;
  const esik = a?.terfi?.promote_min_n;
  const yuzdeIlerleme =
    typeof nLive === "number" && typeof esik === "number" && esik > 0
      ? Math.min(100, (nLive / esik) * 100)
      : null;

  const fitYasi = yas(fit?.ts ?? a?.son_fit_ts);
  const denemeYasi = yas(deneme?.ts ?? a?.son_deneme_ts);

  return (
    <Kutu
      baslik="Gölge model — antrenman ve terfi"
      aciklama="Bu, kapı hükmünün değil İŞLEM SONUCUNUN gölgesi: modelin tahmini canlı Brier'le taban orana karşı ölçülür."
    >
      {a === null || a === undefined ? (
        <Olculemedi neden="`ogrenme.antrenman` null — gölge modelin durumu okunamadı (sunucu uyarısı: learning_scorecard_training_failed / learning_automation)." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="flex flex-col">
            <Satir etiket="Model kuruldu mu?">
              <UcDegerli
                deger={a.kuruldu ?? null}
                evet="kurulu"
                hayir="kurulmadı"
                neden="`antrenman.kuruldu` yükte yok — modelin varlığı ölçülemedi."
              />
            </Satir>
            <Satir etiket="Fit satırı (n_fit)">
              <Deger
                metin={sayi(a.n_fit, 0)}
                neden="`n_fit` yok — model hiç kurulmamışsa bu alan UYDURULMAZ (0 DEĞİL)."
              />
            </Satir>
            <Satir etiket="Gerçek / karşı-olgusal satır">
              <Deger
                metin={
                  a.n_real === null || a.n_real === undefined || a.n_cf === null || a.n_cf === undefined
                    ? null
                    : `${sayi(a.n_real, 0)} gerçek · ${sayi(a.n_cf, 0)} cf`
                }
                neden="künye (`n_real`/`n_cf`) yazılmamış — fit'in hangi popülasyondan geldiği ölçülemedi."
              />
            </Satir>
            <Satir etiket="Antrenman Brier'i">
              <Deger metin={sayi(a.brier_train, 4)} neden="`brier_train` yok — eğitim hatası ölçülemedi." />
            </Satir>
            <Satir etiket="En az fit örneklemi">
              <Deger metin={sayi(a.min_fit_n, 0)} neden="`min_fit_n` yükte yok — fit eşiği ölçülemedi." />
            </Satir>
            <Satir etiket="Veri seti taze mi?" ipucu="Üç değerli: null = parmak izi hiç yazılmamış (eski model).">
              <UcDegerli
                deger={a.veri_seti_taze ?? null}
                evet="taze"
                hayir="değişti (yeniden fit gerek)"
                neden="`veri_seti_taze` null — fit parmak izi hiç yazılmamış; 'bayat' demek bir iddia olurdu."
              />
            </Satir>
          </div>

          <div className="flex flex-col">
            <Satir etiket="Son FİT (modelin kurulduğu an)">
              <Deger
                metin={fitYasi === null ? null : `${fitYasi.metin}${anMetni(fit?.ts ?? a.son_fit_ts) ? ` · ${anMetni(fit?.ts ?? a.son_fit_ts)}` : ""}`}
                neden="fit damgası yok — model hiç kurulmamış ya da damga silinmiş olabilir."
                className="text-xs"
              />
            </Satir>
            <Satir etiket="Damga mı, çıkarım mı?">
              <Deger
                metin={
                  (fit?.kaynak ?? a.son_fit_kaynak) === "damga"
                    ? "damga (fit_ts)"
                    : (fit?.kaynak ?? a.son_fit_kaynak) === "kunye"
                      ? "çıkarım (künyedeki generated)"
                      : null
                }
                neden="kaynak alanı yok — yukarıdaki tarihin damga mı çıkarım mı olduğu ölçülemedi."
                className="text-xs"
              />
            </Satir>
            <Satir etiket="Son DENEME (fit denendiği an)">
              <Deger
                metin={denemeYasi === null ? null : denemeYasi.metin}
                neden="deneme damgası yok — kadans hiç koşmamış olabilir; 'az önce koştu' DEĞİL."
                className="text-xs"
              />
            </Satir>
            <Satir etiket="Denemenin atlama nedeni">
              <Deger
                metin={deneme?.atlama_nedeni ?? a.son_atlama_nedeni ?? null}
                neden="atlama nedeni yazılmamış — deneme ya hiç koşmadı ya da fit gerçekten yapıldı."
                className="text-xs"
              />
            </Satir>
            {nabiz ? (
              <Satir etiket="Kadans nabzı" ipucu="Kadans ≠ fit: deneme ilerlerken fit yerinde kalabilir.">
                <span className="text-xs">
                  {nabiz.hic_kosmadi
                    ? "hiç koşmadı"
                    : `${sayi(nabiz.gecen_saat, 1) ?? "?"} sa önce · pencere ${sayi(nabiz.pencere_saat, 1) ?? "?"} sa${
                        nabiz.bayat === true ? " · BAYAT" : nabiz.bayat === false ? " · taze" : " · bayatlık ölçülemedi"
                      }`}
                </span>
              </Satir>
            ) : null}
          </div>
        </div>
      )}

      {/* ---- TERFİ HÜKMÜ ---- */}
      <div className="rounded-md border border-border/60 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-medium text-sm">Terfi hükmü</p>
          <Badge
            variant="outline"
            className={
              terfi?.karar === "EVET"
                ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
                : terfi?.karar === "HAYIR"
                  ? "border-amber-500/40 text-amber-700 dark:text-amber-300"
                  : "text-muted-foreground"
            }
          >
            {terfi?.karar ?? "hüküm yükte yok"}
          </Badge>
        </div>
        <p className="mt-2 text-muted-foreground text-xs leading-relaxed">
          {terfi?.neden ??
            "`son_fit.terfi` bloğu yükte yok — terfinin neden olmadığı (ya da olduğu) bu turda ölçülmedi."}
        </p>
        {yuzdeIlerleme === null ? (
          <Olculemedi
            className="mt-3"
            neden="canlı kıyas çifti (`terfi.n_live`) ya da eşik (`promote_min_n`) yükte yok — terfi eşiğine ne kadar kaldığı ölçülemedi."
          />
        ) : (
          <div className="mt-3 flex flex-col gap-1.5">
            <div className="flex items-baseline justify-between text-xs">
              <span className="text-muted-foreground">Canlı kıyas çifti</span>
              <span className="tabular-nums">
                {sayi(nLive, 0)} / {sayi(esik, 0)}
              </span>
            </div>
            <Progress value={yuzdeIlerleme} className="h-1.5" />
          </div>
        )}
        <div className="mt-3 flex flex-col">
          <Satir etiket="Canlı Brier">
            <Deger
              metin={sayi(a?.terfi?.live_brier, 4)}
              neden="canlı Brier ölçülemedi — gölge tahmini damgalı bir plan henüz kapanmış işleme dönüşmemiş olabilir."
            />
          </Satir>
          <Satir etiket="Taban-oran Brier">
            <Deger metin={sayi(a?.terfi?.baseline_brier, 4)} neden="taban-oran Brier'i ölçülemedi — kıyas yapılamaz." />
          </Satir>
        </div>
      </div>

      {fit?.beyan ? <Beyan>{fit.beyan}</Beyan> : null}
    </Kutu>
  );
}
