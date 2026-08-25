"use client";

/* ============================================================================
   ALARM GELEN KUTUSU — `/api/alerts`
   ----------------------------------------------------------------------------
   NEDEN İMZA BAZLI: uç alarmları tek tek değil `token` (imza) bazında gruplar
   (`notify.inbox()`); aynı arıza 400 kere ötmüşse bu 400 satır değil BİR arıza +
   bir sayaçtır. Grafik de bunu gösterir: hangi imza gelen kutusunu dolduruyor.

   `pending` İLE `groups.length` FARKLI İKİ SAYIDIR ve ikisi de ekranda duruyor:
   `groups` 60'ta kırpılır, `pending` kırpılmaz. Yalnız tabloyu göstermek, 60'tan
   sonrasını sessizce yutmak olurdu — kartın üstündeki sayaç bu yüzden var.

   ACK DÜĞMESİ (2026-08-25): uç (`POST /api/alerts/ack`) BAŞINDAN BERİ vardı, panoda
   düğmesi YOKTU — yani operatörün gelen kutusunu kapatmanın tek yolu curl'dü ve pratikte
   kimse kapatmıyordu. 23 alarm birikmişti (9'u 2026-08-09'dan NAKED_POSITION). Kalıcı
   kırmızı, hiç kırmızı olmamakla aynı bilgiyi taşır: kimse bakmaz.

   TEK ADIM, ÇİFT DEĞİL — ve bu bilinçli: ACK SİLMEZ, SUSTURUR (`notify.py` yasası; satır
   defterde tam alanlarıyla kalır). Kriz kollarının çift onayı YIKICI eylem içindir; buraya
   aynı sürtünmeyi koymak, sürtünmeyi ANLAMSIZLAŞTIRIR ve asıl gerektiği yerde de tıklanır
   hâle getirir. Yine de geri-alınamaz olduğu için düğme NE YAPTIĞINI yazar.

   SINIR AÇIKÇA YAZILI: uç, okunma sınırını "şimdi"ye değil GÖSTERİLEN EN YENİ olaya
   ilerletir (api.py `_seen_max`) — yani ekranda görünmeyen bir alarm ACK'lenmez. Düğmenin
   metni bunu söylüyor; söylemezse operatör "hepsini kapattım" sanır.

   VLO DERSİ (hafıza: oturum-basi-canli-triyaj): "alarm öttü, kimse dinlemedi".
   Bu yüzden kanal yapılandırması (`channel_configured`) sayfanın en görünür
   yerinde: uzak kanal yoksa alarm YALNIZ bu ekrandadır ve kimse bakmıyorsa
   gerçekten kimse duymuyor demektir.
   ============================================================================ */
import { BellRing, Check, Inbox, Loader2 } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { krizPost } from "../../kabuk/krizUclari";
import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, OkRozet, Satir, zamanMetni } from "./parcalar";
import type { AlarmGovdesi, AlarmGrubu } from "./uctipleri";

const GRAFIK: ChartConfig = { n: { label: "kayıt", color: "var(--chart-1)" } };

function kisaImza(t: string | undefined, i: number): string {
  if (!t) return `imza #${i + 1}`;
  return t.length > 34 ? `${t.slice(0, 33)}…` : t;
}

function AckDugmesi({
  bekleyen,
  gosterilen,
  onBitti,
}: {
  readonly bekleyen: number | undefined;
  readonly gosterilen: number;
  readonly onBitti: () => void;
}) {
  const [gidiyor, setGidiyor] = useState(false);

  // DÜĞME OLMADIĞI HÂL DE BİR HÜKÜMDÜR: sayı ölçülemediyse ACK teklif edilmez — kaç alarmı
  // kapattığını bilmeden "gördüm" demek, görmeden imzalamaktır.
  if (bekleyen === undefined || bekleyen === null) return null;
  if (bekleyen <= 0) {
    return (
      <Badge variant="outline" className="gap-1">
        <Check className="size-3" /> gelen kutusu temiz
      </Badge>
    );
  }

  async function gonder() {
    setGidiyor(true);
    const s = await krizPost("/api/alerts/ack");
    setGidiyor(false);
    if (!s.ok) {
      // SESSİZ BAŞARISIZLIK YOK: kod 0 ağ düşmesidir, 401 oturumdur — ikisi ayrı çare ister.
      toast.error("ACK gitmedi — gelen kutusu OLDUĞU GİBİ duruyor", {
        description: s.kod === 0 ? `ağa ulaşılamadı: ${s.detay}` : `HTTP ${s.kod} · ${s.detay ?? ""}`,
      });
      return;
    }
    const g = (s.govde ?? {}) as { readonly inbox?: { readonly pending?: number }; readonly ack_ts?: string };
    const kalan = g.inbox?.pending;
    toast.success("Okundu işaretlendi", {
      description:
        kalan === undefined
          ? "uç yeni `pending` döndürmedi — sayı bir sonraki okumada görünecek"
          : `kalan bekleyen: ${kalan}${g.ack_ts ? ` · sınır ${g.ack_ts}` : ""}`,
    });
    // İYİMSER GÜNCELLEME YOK: uç cevabına değil, YENİDEN OKUMAYA güveniyoruz (kriz kolları emsali).
    onBitti();
  }

  return (
    <Button
      size="sm"
      variant="outline"
      disabled={gidiyor}
      onClick={() => void gonder()}
      title={
        "ACK SİLMEZ, SUSTURUR: satırlar defterde tam alanlarıyla kalır. Okunma sınırı " +
        "'şimdi'ye değil GÖSTERİLEN en yeni olaya ilerler — ekranda görünmeyen bir alarm " +
        "kapanmaz."
      }
    >
      {gidiyor ? <Loader2 className="size-3.5 animate-spin" /> : <Check className="size-3.5" />}
      {gidiyor ? "gönderiliyor…" : `${bekleyen} alarmı okundu işaretle`}
      {gosterilen > 0 ? (
        <span className="text-muted-foreground ml-1 text-[11px]">· gösterilen {gosterilen} gruba kadar</span>
      ) : null}
    </Button>
  );
}


export function Operasyon({ durum }: { readonly durum: Durum<AlarmGovdesi> }) {
  return (
    <BolumKart
      kimlik="operasyon"
      baslik="Alarm gelen kutusu"
      soru="Çalan bir alarm var mı?"
      ikon={BellRing}
      aksiyon={
        <div className="flex flex-wrap items-center gap-2">
          {durum.veri?.pending !== undefined ? (
            <Badge variant={durum.veri.pending > 0 ? "destructive" : "secondary"}>
              {durum.veri.pending} bekleyen
            </Badge>
          ) : null}
          <AckDugmesi
            bekleyen={durum.veri?.pending}
            gosterilen={(durum.veri?.groups ?? []).length}
            onBitti={durum.tazele}
          />
        </div>
      }
    >
      <Kapi durum={durum} yol="/api/alerts">
        {(a) => {
          const gruplar: readonly AlarmGrubu[] = a.groups ?? [];
          const veri = gruplar
            .slice()
            .sort((x, y) => (y.n ?? 0) - (x.n ?? 0))
            .slice(0, 10)
            .map((g, i) => ({ imza: kisaImza(g.token, i), n: g.n ?? 0, tam: g.token ?? "" }));

          return (
            <>
              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="ACK'lenmemiş toplam">
                    <Deger deger={a.pending} neden="/api/alerts `pending` döndürmedi" />
                  </Satir>
                  <Satir etiket="Gösterilen imza grubu">
                    {a.groups === undefined ? (
                      <Olculemedi neden="/api/alerts `groups` döndürmedi" kisa />
                    ) : (
                      <span className="tabular-nums">
                        {gruplar.length}
                        {gruplar.length >= 60 ? " (60'ta kırpıldı)" : ""}
                      </span>
                    )}
                  </Satir>
                  <Satir etiket="Son 'gördüm' damgası">
                    {zamanMetni(a.ack_ts) ?? <Olculemedi neden="ack_ts yok — hiç ACK verilmemiş" kisa />}
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Uzak kanal (Telegram/webhook)">
                    <OkRozet
                      ok={a.channel_configured}
                      iyi="yapılandırılmış"
                      kotu="YOK — alarm yalnız bu ekranda"
                      neden="/api/alerts `channel_configured` döndürmedi"
                    />
                  </Satir>
                  <Satir etiket="Taranan olay penceresi">
                    <Deger deger={a.window_lines} birim=" satır" neden="/api/alerts `window_lines` döndürmedi" />
                  </Satir>
                  <Satir etiket="Pencere kırpıldı mı">
                    {a.window_truncated === null || a.window_truncated === undefined ? (
                      <Olculemedi neden="ACK yok — kırpılma ölçülemez (null, false DEĞİL)" kisa />
                    ) : (
                      <OkRozet ok={!a.window_truncated} iyi="tamamı tarandı" kotu="pencere kırpıldı" />
                    )}
                  </Satir>
                </div>
              </div>

              {veri.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  {a.groups === undefined
                    ? "Gelen kutusu ölçülemedi — /api/alerts `groups` alanını döndürmüyor."
                    : "ACK'lenmemiş alarm yok. (Bu, olay defterinin boş olduğu anlamına gelmez — yalnız bu pencerede ACK bekleyen imza yok.)"}
                </p>
              ) : (
                <>
                  <ChartContainer config={GRAFIK} className="aspect-auto h-64 w-full">
                    <BarChart data={veri} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <CartesianGrid horizontal={false} />
                      <XAxis type="number" dataKey="n" tickLine={false} axisLine={false} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="imza"
                        tickLine={false}
                        axisLine={false}
                        width={190}
                        tick={{ fontSize: 11 }}
                      />
                      <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel />} />
                      <Bar isAnimationActive={false} dataKey="n" fill="var(--color-n)" radius={4} />
                    </BarChart>
                  </ChartContainer>

                  <div className="overflow-x-auto">
                    <Table className="min-w-[46rem]">
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead>İmza</TableHead>
                          <TableHead className="text-right">Kayıt</TableHead>
                          <TableHead>İlk</TableHead>
                          <TableHead>Son</TableHead>
                          <TableHead>Mesaj</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {gruplar.map((g, i) => (
                          <TableRow key={g.token ?? `grup-${i}`}>
                            <TableCell className="font-medium">
                              {g.token ?? <Olculemedi neden="grup `token` taşımıyor" kisa />}
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              <Deger deger={g.n} neden="grup `n` taşımıyor" />
                            </TableCell>
                            <TableCell className="whitespace-nowrap text-muted-foreground text-xs">
                              {zamanMetni(g.first_ts) ?? <Olculemedi neden="first_ts yok" kisa />}
                            </TableCell>
                            <TableCell className="whitespace-nowrap text-muted-foreground text-xs">
                              {zamanMetni(g.last_ts) ?? <Olculemedi neden="last_ts yok" kisa />}
                            </TableCell>
                            <TableCell className="max-w-[26rem] truncate text-xs" title={g.message ?? ""}>
                              {g.message ?? <Olculemedi neden="grup `message` taşımıyor" kisa />}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </>
              )}

              <p className="flex items-start gap-1.5 text-muted-foreground text-xs">
                <Inbox className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                Kaynak `events.jsonl` — ikinci bir alarm defteri YOK. "Gördüm" işareti hiçbir alarmı
                silmez, yalnız okunma sınırını ilerletir (api.py:2963).
              </p>
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
