"use client";

/* ============================================================================
   KATMAN 2 — MERIDIAN BİLEŞENLERİ (`/api/infra` · `bilesenler`)
   ----------------------------------------------------------------------------
   Makineden AYRI bir bölüm, çünkü ayrı bir soru: kutu boştayken tek bir birim
   belleği yiyor olabilir; kutu doluyken suçlu bir birim OLMAYABİLİR. İki katmanı
   tek tabloya sıkıştırmak, hangi müdahalenin (birimi yeniden başlat / makineyi
   büyüt) doğru olduğunu okunamaz hâle getirirdi.

   ÜÇ TUZAK BURADA AÇIKÇA KARŞILANIYOR — üçü de bu depoda ÖLÇÜLMÜŞ vakalar:
   1) ŞABLON BİRİM (`meridian-sprint@.service`): düz adla `systemctl show` SAHTE
      bir `inactive` döndürür. Hafıza kaydı "meridian-sprint şablon birim": pano
      "koşmuyor" dedi, gerçek ise "koştu, aday geçmedi"ydi. Uç şablonun durumunu
      UYDURMUYOR (None + neden) ve tablo bunu "ölçülemedi" diye gösteriyor —
      "kapalı" diye DEĞİL.
   2) `MemoryCurrent` SENTİNELİ: systemd ayarsızken 2^64-1 döndürür. 18 exabaytlık
      bir RSS çizmek, ölçülmemiş bir değeri sayıya çevirmenin ders kitabı örneği.
      Uç onu None + neden yapıyor; biz de payı hesaplarken o satırı DIŞARIDA
      bırakıyor ve kaç satır elendiğini yazıyoruz (sessiz eleme yok).
   3) CPU BİR DELTA'DIR: tek örnekle ölçülemez. İlk ankette `cpu_yuzde` None +
      neden gelir ve sütun `0,0%` DEĞİL "ölçülemedi" der.

   `bilesenler === null` İLE BOŞ LİSTE AYRI: birincisi "systemctl yok / ölçemedim"
   (uç `bilesenler_olculemedi_neden` ile söylüyor), ikincisi "hiç birim yok".
   ============================================================================ */
import { Boxes } from "lucide-react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, Satir, baytMetni, sureMetni } from "./parcalar";
import type { InfraBilesen, InfraGovdesi } from "./uctipleri";

/** Yığılmış çubukta en çok bu kadar AYRI bileşen; kalanı tek "diğer" dilimine iner.
 *  Sınır palet genişliğinden geliyor: `--chart-1..5` beş rol jetonu var ve altıncı
 *  dilim bir rengi TEKRAR ederdi — aynı renk iki farklı bileşen demek okunamaz bir grafiktir. */
const DILIM_TAVANI = 5;

function durumRozeti(b: InfraBilesen) {
  // KURULU DEĞİL ≠ DURMUŞ. Depoda dosyası olan ama bu makineye kurulmamış birimler var
  // (örn. taslak `litestream.service`). Onları "inactive" diye basmak, kurulu ama durmuş bir
  // birimle AYNI rozeti vermek olurdu — iki farklı gerçek, iki farklı iş.
  if (b.kurulu === false) {
    return (
      <Badge
        variant="outline"
        className="gap-1.5"
        title={b.kurulu_neden ?? "LoadState `loaded` değil — birim bu makineye kurulmamış"}
      >
        <span className="size-1.5 rounded-full bg-muted-foreground/60" />
        kurulu değil
      </Badge>
    );
  }
  if (b.durum === null || b.durum === undefined) {
    return (
      <Badge variant="outline" className="gap-1.5" title={b.durum_neden ?? "durum alanı gelmedi"}>
        <span className="size-1.5 rounded-full bg-muted-foreground/60" />
        ölçülemedi
      </Badge>
    );
  }
  const aktif = b.durum === "active";
  const arizali = b.durum === "failed";
  return (
    <Badge
      variant={arizali ? "destructive" : "secondary"}
      className={cn("gap-1.5", aktif && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400")}
      title={b.alt_durum ? `alt durum: ${b.alt_durum}` : undefined}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          aktif ? "bg-emerald-500" : arizali ? "bg-destructive" : "bg-muted-foreground/60",
        )}
      />
      {b.durum}
    </Badge>
  );
}

export function Bilesenler({ durum }: { readonly durum: Durum<InfraGovdesi> }) {
  return (
    <BolumKart
      kimlik="bilesenler"
      baslik="Meridian bileşenleri"
      soru="Hangi birim koşuyor, ne kadar kaynak yiyor?"
      ikon={Boxes}
    >
      <Kapi durum={durum} yol="/api/infra">
        {(g) => {
          if (g.bilesenler === null) {
            return (
              <Olculemedi
                neden={
                  g.bilesenler_olculemedi_neden ??
                  "/api/infra `bilesenler` null döndürdü ama nedenini yazmadı — boş liste 'bileşen yok' diye okunurdu"
                }
              />
            );
          }
          if (g.bilesenler === undefined) {
            return <Olculemedi neden="/api/infra `bilesenler` alanını hiç döndürmüyor" />;
          }
          const satirlar = g.bilesenler;
          if (satirlar.length === 0) {
            return (
              <p className="text-muted-foreground text-sm">
                Uç ölçtü ve HİÇ birim bulmadı (boş liste). Bu "ölçemedim" DEĞİL — ölçemediğinde uç
                `bilesenler: null` + neden döndürüyor.
              </p>
            );
          }

          // --- BELLEK PAYI: yalnız RSS'İ ÖLÇÜLMÜŞ satırlar; elenenler sayılıp yazılır.
          const olculen = satirlar.filter((b) => typeof b.rss_bayt === "number" && b.rss_bayt >= 0);
          const elenen = satirlar.length - olculen.length;
          const sirali = [...olculen].sort((a, b) => (b.rss_bayt ?? 0) - (a.rss_bayt ?? 0));
          const ust = sirali.slice(0, DILIM_TAVANI);
          const kalan = sirali.slice(DILIM_TAVANI);
          const kalanToplam = kalan.reduce((t, b) => t + (b.rss_bayt ?? 0), 0);
          const toplamRss = sirali.reduce((t, b) => t + (b.rss_bayt ?? 0), 0);

          // Anahtarlar CSS değişkeni adına giriyor (`--color-<anahtar>`), bu yüzden birim adı
          // DEĞİL güvenli bir takma ad kullanılıyor: `meridian-sprint@.service` içindeki `@` ve `.`
          // geçerli bir özel-özellik adı üretmez.
          const yapilandirma: ChartConfig = {};
          ust.forEach((b, i) => {
            yapilandirma[`b${i}`] = { label: b.ad ?? `birim #${i + 1}`, color: `var(--chart-${i + 1})` };
          });
          if (kalan.length > 0) {
            yapilandirma.diger = { label: `diğer (${kalan.length} bileşen)`, color: "var(--muted-foreground)" };
          }
          const cubuk: Record<string, number | string> = { ad: "RSS payı" };
          ust.forEach((b, i) => {
            cubuk[`b${i}`] = b.rss_bayt ?? 0;
          });
          if (kalan.length > 0) cubuk.diger = kalanToplam;

          const aktifN = satirlar.filter((b) => b.durum === "active").length;
          const kurulmamisN = satirlar.filter((b) => b.kurulu === false).length;
          const sablonN = satirlar.filter((b) => b.sablon).length;
          // Durumu ölçülemeyenlerden ŞABLON ve KURULMAMIŞ olanlar DÜŞÜLÜR: onların "ölçülemedi"si
          // bir arıza değil, bilinen ve adlandırılmış bir hâl. Aynı kovaya atmak, gerçekten
          // sorgulanamayan birimleri (systemctl hatası, bütçe aşımı) görünmez kılardı.
          const olcusuzDurum = satirlar.filter(
            (b) => (b.durum === null || b.durum === undefined) && !b.sablon && b.kurulu !== false,
          ).length;
          const surec = g.surec;

          return (
            <>
              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="Bildirilen birim">
                    <span className="tabular-nums">{satirlar.length}</span>
                  </Satir>
                  <Satir etiket="Koşan (active)">
                    <span className="tabular-nums text-emerald-600 dark:text-emerald-400">{aktifN}</span>
                  </Satir>
                  <Satir etiket="Kurulu değil / şablon">
                    <span className="tabular-nums" title="ikisi de arıza DEĞİL: biri bu makineye kurulmamış birim, öteki `@.service` şablonu">
                      {kurulmamisN} / {sablonN}
                    </span>
                  </Satir>
                  <Satir etiket="Durumu gerçekten ölçülemeyen">
                    <span className={cn("tabular-nums", olcusuzDurum > 0 && "text-amber-600 dark:text-amber-400")}>
                      {olcusuzDurum}
                      {olcusuzDurum > 0 ? " (systemctl hatası / bütçe aşımı)" : ""}
                    </span>
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Toplam ölçülen RSS">
                    {olculen.length === 0 ? (
                      <Olculemedi neden="hiçbir satırda `rss_bayt` ölçülmedi" kisa />
                    ) : (
                      <span className="tabular-nums">{baytMetni(toplamRss)}</span>
                    )}
                  </Satir>
                  <Satir etiket="Paydan elenen satır">
                    <span className="tabular-nums">
                      {elenen}
                      {elenen > 0 ? " (RSS ölçülemedi — 0 sayılmadı)" : ""}
                    </span>
                  </Satir>
                  <Satir etiket="Restart taşıyan birim">
                    <span className="tabular-nums">
                      {satirlar.filter((b) => (b.restart_n ?? 0) > 0).length}
                    </span>
                  </Satir>
                </div>
              </div>

              {/* --- ÜÇÜNCÜ KAT: PANO SÜRECİNİN KENDİSİ ---
                  systemd'nin `meridian.service` satırıyla AYNI ŞEY DEĞİL (o birim compose'u sarar);
                  uç bunu ayrı bir blok olarak veriyor (api.py:6322) ve operatörün ilk sorusu bu:
                  "panoyu servis eden süreç kendisi ne kadar yiyor?" */}
              {surec === undefined ? (
                <Olculemedi neden="/api/infra `surec` bloğunu döndürmedi" />
              ) : (
                <div className="rounded-lg border bg-muted/30 p-3">
                  <div className="mb-1 flex items-center gap-2">
                    <span className="font-medium text-sm">Bu API süreci</span>
                    <Badge variant="outline" className="text-[10px]" title="systemd biriminden AYRI ölçüm">
                      systemd birimi DEĞİL
                    </Badge>
                  </div>
                  <div className="grid gap-x-6 sm:grid-cols-2">
                    <div>
                      <Satir etiket="PID">
                        <Deger deger={surec.pid} neden="`surec.pid` gelmedi" />
                      </Satir>
                      <Satir etiket="Çalışma süresi">
                        {sureMetni(surec.uptime_s) ?? <Olculemedi neden="`surec.uptime_s` gelmedi" kisa />}
                      </Satir>
                    </div>
                    <div>
                      <Satir etiket="CPU">
                        {surec.cpu_yuzde === null || surec.cpu_yuzde === undefined ? (
                          <Olculemedi
                            neden={surec.cpu_yuzde_neden ?? "CPU bir DELTA'dır — ilk örnekte ölçülemez"}
                            kisa
                          />
                        ) : (
                          <span className="tabular-nums">{surec.cpu_yuzde.toFixed(1)}%</span>
                        )}
                      </Satir>
                      <Satir etiket="RSS">
                        {typeof surec.rss_bayt === "number" ? (
                          <span className="tabular-nums">{baytMetni(surec.rss_bayt)}</span>
                        ) : (
                          <Olculemedi
                            neden={surec.rss_bayt_neden ?? "`surec.rss_bayt` gelmedi"}
                            kisa
                          />
                        )}
                      </Satir>
                    </div>
                  </div>
                </div>
              )}

              {/* --- YIĞILMIŞ ÇUBUK: BELLEK PAYI --- */}
              {olculen.length > 0 ? (
                <>
                  <ChartContainer config={yapilandirma} className="aspect-auto h-16 w-full">
                    <BarChart data={[cubuk]} layout="vertical" margin={{ left: 0, right: 0, top: 4, bottom: 0 }}>
                      <XAxis type="number" hide />
                      <YAxis type="category" dataKey="ad" hide />
                      <ChartTooltip
                        cursor={false}
                        content={
                          <ChartTooltipContent
                            hideLabel
                            formatter={(deger, ad) => {
                              const b = baytMetni(typeof deger === "number" ? deger : null);
                              const etiket = yapilandirma[String(ad)]?.label ?? String(ad);
                              return (
                                <span className="flex w-full justify-between gap-4">
                                  <span className="text-muted-foreground">{etiket}</span>
                                  <span className="font-mono tabular-nums">{b ?? "ölçülemedi"}</span>
                                </span>
                              );
                            }}
                          />
                        }
                      />
                      {ust.map((b, i) => (
                        <Bar isAnimationActive={false}
                          key={b.ad ?? `b${i}`}
                          dataKey={`b${i}`}
                          stackId="rss"
                          barSize={26}
                          fill={`var(--color-b${i})`}
                          radius={i === 0 ? [4, 0, 0, 4] : kalan.length === 0 && i === ust.length - 1 ? [0, 4, 4, 0] : 0}
                        />
                      ))}
                      {kalan.length > 0 ? (
                        <Bar isAnimationActive={false} dataKey="diger" stackId="rss" barSize={26} fill="var(--color-diger)" radius={[0, 4, 4, 0]} />
                      ) : null}
                    </BarChart>
                  </ChartContainer>
                  <div className="flex flex-wrap gap-x-4 gap-y-1">
                    {/* KÜNYE RECHARTS'IN LEGEND'İ DEĞİL: onunki tek satırdır ve birim adları uzun
                        (`meridian-tick-watchdog.service`) — altı dilim yan yana taşardı. */}
                    {Object.entries(yapilandirma).map(([anahtar, k]) => (
                      <span key={anahtar} className="flex items-center gap-1.5 text-xs">
                        {/* RENK DOĞRUDAN YAPILANDIRMADAN: `--color-<anahtar>` değişkenlerini
                            `ChartStyle` YALNIZ `[data-chart=…]` kapsayıcısının İÇİNE yazıyor
                            (chart.tsx). Bu şerit kapsayıcının DIŞINDA, orada o değişken çözülmez
                            ve şeritteki her kare şeffaf kalırdı. */}
                        <span
                          className="size-2 shrink-0 rounded-[2px]"
                          style={{ backgroundColor: k.color ?? "var(--muted-foreground)" }}
                        />
                        <span className="text-muted-foreground">{k.label}</span>
                      </span>
                    ))}
                  </div>
                  <p className="text-muted-foreground text-xs">
                    Yığılmış çubuk, ÖLÇÜLEN RSS toplamının ({baytMetni(toplamRss)}) bileşenlere dağılımıdır —
                    makinenin toplam belleğinin değil. En büyük {Math.min(DILIM_TAVANI, ust.length)} bileşen
                    ayrı dilim; kalanlar "diğer"de.
                    {elenen > 0
                      ? ` RSS'i ölçülemeyen ${elenen} satır paya HİÇ girmedi (0 saymak, ölçülmemişi boşta göstermek olurdu).`
                      : ""}
                  </p>
                </>
              ) : (
                <Olculemedi neden="hiçbir bileşenin `rss_bayt` değeri ölçülmedi — pay çubuğu çizilemez" />
              )}

              {/* --- BİLEŞEN TABLOSU --- */}
              <div className="overflow-x-auto">
                <Table className="min-w-[62rem]">
                  <TableHeader className="bg-muted/50">
                    <TableRow>
                      <TableHead>Birim</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead className="text-right">CPU</TableHead>
                      <TableHead className="text-right">RSS</TableHead>
                      <TableHead className="text-right">Bellek payı</TableHead>
                      <TableHead className="text-right">Çalışma süresi</TableHead>
                      <TableHead className="text-right">Restart</TableHead>
                      <TableHead>Tanım</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {satirlar.map((b, i) => {
                      const pay =
                        typeof b.rss_bayt === "number" && toplamRss > 0 ? (b.rss_bayt / toplamRss) * 100 : null;
                      return (
                        <TableRow key={b.ad ?? `bilesen-${i}`}>
                          <TableCell className="font-medium font-mono text-xs">
                            <span className="flex items-center gap-1.5">
                              {b.ad ?? <Olculemedi neden="satır `ad` taşımıyor" kisa />}
                              {b.sablon ? (
                                <Badge
                                  variant="outline"
                                  className="text-[10px]"
                                  title="Şablon birim (`@.service`) — düz adla sorgu sahte `inactive` verir; durumu uydurulmaz."
                                >
                                  şablon
                                </Badge>
                              ) : null}
                              {b.tur === "timer" ? (
                                <Badge variant="outline" className="text-[10px]" title="systemd timer birimi">
                                  timer
                                </Badge>
                              ) : null}
                            </span>
                          </TableCell>
                          <TableCell>{durumRozeti(b)}</TableCell>
                          <TableCell className="text-right tabular-nums">
                            {b.cpu_yuzde === null || b.cpu_yuzde === undefined ? (
                              <Olculemedi
                                neden={b.cpu_yuzde_neden ?? "CPU bir DELTA'dır — tek örnekle ölçülemez"}
                                kisa
                              />
                            ) : (
                              `${b.cpu_yuzde.toFixed(1)}%`
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {typeof b.rss_bayt === "number" ? (
                              baytMetni(b.rss_bayt)
                            ) : (
                              <Olculemedi
                                neden={b.rss_bayt_neden ?? "`rss_bayt` ölçülemedi (systemd sentineli olabilir)"}
                                kisa
                              />
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {pay === null ? (
                              <span className="text-muted-foreground text-xs">—</span>
                            ) : (
                              <span className="flex items-center justify-end gap-2">
                                <span className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-muted-foreground/20 sm:block">
                                  <span
                                    className="block h-full rounded-full bg-primary"
                                    style={{ width: `${Math.min(100, pay)}%` }}
                                  />
                                </span>
                                {pay.toFixed(1)}%
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums text-xs">
                            {sureMetni(b.uptime_s) ?? (
                              <Olculemedi neden={b.uptime_s_neden ?? "`uptime_s` gelmedi"} kisa />
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {b.restart_n === null || b.restart_n === undefined ? (
                              <Olculemedi neden={b.restart_n_neden ?? "`restart_n` gelmedi"} kisa />
                            ) : (
                              <span
                                className={cn(
                                  b.restart_n > 0 && "font-medium text-amber-600 dark:text-amber-400",
                                )}
                              >
                                <Deger deger={b.restart_n} neden="restart sayacı gelmedi" />
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="max-w-[20rem] truncate text-muted-foreground text-xs">
                            {b.aciklama ?? b.dosya ?? (
                              <Olculemedi neden="birim tanımı/dosya adı gelmedi" kisa />
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>

              <p className="text-muted-foreground text-xs">
                Birim adları `{g.bilesen_kaynagi?.dizin ?? "deploy/"}` altındaki GERÇEK
                `.service`/`.timer` dosyalarından geliyor ({g.bilesen_kaynagi?.birim_n ?? satirlar.length} dosya) —
                uç uydurulmuş bir ad bildirirse çivi (`test_birim_adlari_diskteki_gercek_dosyalardan_gelir`)
                kırmızıya döner. `systemctl` yolu:{" "}
                {g.bilesen_kaynagi?.systemctl_yolu ?? (
                  <Olculemedi
                    neden={g.bilesen_kaynagi?.systemctl_yolu_neden ?? "yol beyanı gelmedi"}
                    kisa
                  />
                )}
                . Bu tablo hiçbir birimi başlatmaz/durdurmaz; salt okunurdur.
              </p>
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
