"use client";

/* ============================================================================
   BROKER HESABI — `/api/alpaca` (ajanın aynaladığı Alpaca PAPER hesabı)
   ----------------------------------------------------------------------------
   ÜÇ TUZAK BU BÖLÜMDE AÇIKÇA KARŞILANIYOR, üçü de kaynaktan OKUNARAK bulundu:

   1) HESAP NUMARASI YOK. Brief "hesap numarası maskeli" istiyordu;
      `adapters/alpaca.py::dashboard_view` (satır 1616) yalnız
      equity/cash/status/buying_power/positions/open_orders/endpoint döndürüyor —
      `account_number` HİÇ TAŞINMIYOR. Maskeli bir numara uydurmak ya da
      `endpoint`i numara diye sunmak yalan olurdu; ekranda "ölçülemedi + neden"
      yazıyor ve kimlik izi olarak yalnız GERÇEKTEN gelen `endpoint` gösteriliyor.

   2) BOŞ POZİSYON LİSTESİ "POZİSYON YOK" DEMEK DEĞİL. `alpaca.positions()`
      docstring'i birebir şunu söylüyor: "[] => ya gerçekten pozisyon yok YA DA API
      ulaşılamadı; ayrımı transport() taşır". `/api/alpaca` `transport()`u
      döndürmüyor — ama `/api/diagnostics.saglayicilar` içinde `alpaca_ticaret`
      satırı var ve `ok` alanını taşıyor. Bu yüzden bölüm İKİ ucu yan yana okuyor:
      liste boş VE ticaret taşıması sağlam değilse, ekran "pozisyon yok" demiyor,
      "boş liste bir cevap değil" diyor.

   3) SAYILAR DİZGE GELEBİLİR. `dashboard_view` ham Alpaca alanlarını ayrıştırmadan
      geçiriyor ve Alpaca REST'i sayıları dizge döndürür ("184.31"). `sayiya()`
      ikisini de karşılar, ayrıştıramadığında `null` der — `0` demez.
   ============================================================================ */
import { Landmark } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Kpi, Metin, Olculemedi, OkRozet, Satir, sayiya, sureMetni, zamanMetni } from "./parcalar";
import type { AlpacaGovdesi, AlpacaHesap, SaglayiciSatiri, TeshisGovdesi } from "./uctipleri";

const UPL_CONFIG = {
  upl: { label: "Gerçekleşmemiş K/Z", color: "var(--chart-1)" },
} satisfies ChartConfig;

interface UplNoktasi {
  readonly sembol: string;
  readonly upl: number;
}

/** `/api/diagnostics` içindeki `alpaca_ticaret` satırı — boş liste yorumunun tek dayanağı. */
function ticaretSatiri(t: TeshisGovdesi | null): SaglayiciSatiri | null {
  const xs = t?.saglayicilar?.saglayicilar;
  if (!Array.isArray(xs)) return null;
  return xs.find((s) => s.ad === "alpaca_ticaret") ?? null;
}

function HamHucre({
  deger,
  neden,
  teknik,
  basamak = 2,
}: { readonly deger: unknown; readonly neden: string; readonly teknik?: string; readonly basamak?: number }) {
  const n = sayiya(deger);
  if (n === null) return <Olculemedi neden={neden} teknik={teknik} kisa />;
  return <Deger deger={n} basamak={basamak} neden={neden} />;
}

function PozisyonTablosu({ pozisyonlar }: { readonly pozisyonlar: readonly NonNullable<AlpacaHesap["positions"]>[number][] }) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Sembol</TableHead>
            <TableHead className="text-right">Adet</TableHead>
            <TableHead className="text-right">Ort. giriş</TableHead>
            <TableHead className="text-right">Son</TableHead>
            <TableHead className="text-right">Gerçekleşmemiş K/Z</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {pozisyonlar.map((p, i) => {
            const upl = sayiya(p.upl);
            return (
              <TableRow key={`${p.symbol ?? "?"}-${i}`}>
                <TableCell className="font-medium">
                  <Metin deger={p.symbol} neden="Bu satırın sembolü bildirilmedi" teknik="broker satırında `symbol` yok" />
                </TableCell>
                <TableCell className="text-right">
                  <HamHucre
                    deger={p.qty}
                    neden="Adet okunamadı"
                    teknik="broker satırında `qty` yok ya da sayıya çevrilemedi"
                    basamak={0}
                  />
                </TableCell>
                <TableCell className="text-right">
                  <HamHucre
                    deger={p.avg_entry}
                    neden="Ortalama giriş fiyatı bildirilmedi"
                    teknik="broker satırında `avg_entry_price` yok"
                  />
                </TableCell>
                <TableCell className="text-right">
                  <HamHucre
                    deger={p.current}
                    neden="Son fiyat bildirilmedi"
                    teknik="broker satırında `current_price` yok"
                  />
                </TableCell>
                <TableCell className="text-right">
                  <Deger
                    deger={upl}
                    onek="$"
                    basamak={2}
                    neden="Bu pozisyonun kâr/zararı bildirilmedi"
                    className={
                      upl === null
                        ? undefined
                        : upl >= 0
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-red-600 dark:text-red-400"
                    }
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

function EmirTablosu({ emirler }: { readonly emirler: readonly NonNullable<AlpacaHesap["open_orders"]>[number][] }) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Sembol</TableHead>
            <TableHead>Yön</TableHead>
            <TableHead>Tür</TableHead>
            <TableHead className="text-right">Adet</TableHead>
            <TableHead className="text-right">Stop</TableHead>
            <TableHead className="text-right">Limit</TableHead>
            <TableHead>Durum</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {emirler.map((o, i) => (
            <TableRow key={`${o.symbol ?? "?"}-${i}`}>
              <TableCell className="font-medium">
                <Metin deger={o.symbol} neden="Bu emrin sembolü bildirilmedi" teknik="emir satırında `symbol` yok" />
              </TableCell>
              <TableCell className="text-xs uppercase">
                <Metin
                  deger={o.side}
                  neden="Emrin alış mı satış mı olduğu bildirilmedi"
                  teknik="emir satırında `side` yok"
                />
              </TableCell>
              <TableCell className="text-xs">
                <Metin deger={o.type} neden="Emir türü bildirilmedi" teknik="emir satırında `type` yok" />
              </TableCell>
              <TableCell className="text-right">
                <HamHucre deger={o.qty} neden="Adet bildirilmedi" teknik="emir satırında `qty` yok" basamak={0} />
              </TableCell>
              <TableCell className="text-right">
                <HamHucre deger={o.stop} neden="Bu emirde zarar durdurma fiyatı yok" teknik="emir satırında `stop` yok" />
              </TableCell>
              <TableCell className="text-right">
                <HamHucre deger={o.limit} neden="Bu emirde limit fiyatı yok" teknik="emir satırında `limit` yok" />
              </TableCell>
              <TableCell className="text-xs">
                <Metin deger={o.status} neden="Emrin durumu bildirilmedi" teknik="emir satırında `status` yok" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function Govde({ v, ticaret }: { readonly v: AlpacaGovdesi; readonly ticaret: SaglayiciSatiri | null }) {
  const h = v.account ?? null;
  const pozisyonlar = h?.positions ?? [];
  const emirler = h?.open_orders ?? [];
  const akis = v.stream;

  // K/Z grafiği YALNIZ ölçülebilen satırlardan kurulur; elenen satır sayısı yazılır
  // (sessiz eleme yok — bir pozisyonun grafikte olmaması "K/Z sıfır" diye okunmamalı).
  const noktalar: UplNoktasi[] = [];
  let elenen = 0;
  for (const p of pozisyonlar) {
    const u = sayiya(p.upl);
    const s = typeof p.symbol === "string" && p.symbol !== "" ? p.symbol : null;
    if (u === null || s === null) {
      elenen += 1;
      continue;
    }
    noktalar.push({ sembol: s, upl: u });
  }
  noktalar.sort((a, b) => b.upl - a.upl);

  const bosListeSupheli = pozisyonlar.length === 0 && ticaret?.ok !== true;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono text-xs">
          {typeof v.backend === "string" && v.backend !== "" ? v.backend : "backend ölçülemedi"}
        </Badge>
        <OkRozet
          ok={v.paper_available}
          iyi="kağıt anahtarı var"
          kotu="kağıt anahtarı YOK"
          neden="Kağıt hesap anahtarının kurulu olup olmadığı bildirilmedi"
        />
        <OkRozet
          ok={h?.connected}
          iyi="hesap bağlı"
          kotu="hesap bağlanamadı"
          neden={
            v.paper_available === false
              ? "Kağıt hesap anahtarı olmadığı için hesap hiç sorulmadı"
              : "Hesabın bağlı olup olmadığı bildirilmedi"
          }
        />
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Kpi etiket="Broker sermayesi">
          <Deger deger={h?.equity} onek="$" basamak={2} neden="Broker sermayesi bildirilmedi" />
        </Kpi>
        <Kpi etiket="Nakit">
          <Deger deger={h?.cash} onek="$" basamak={2} neden="Hesaptaki nakit bildirilmedi" />
        </Kpi>
        <Kpi etiket="Alım gücü">
          <Deger deger={h?.buying_power} onek="$" basamak={2} neden="Alım gücü bildirilmedi" />
        </Kpi>
        <Kpi etiket="Açık pozisyon" alt={bosListeSupheli ? "boş liste şüpheli — aşağıya bak" : undefined}>
          <span className="tabular-nums">{pozisyonlar.length}</span>
        </Kpi>
        <Kpi etiket="Açık emir" alt="uç en çok 20 satır taşır">
          <span className="tabular-nums">{emirler.length}</span>
        </Kpi>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col">
          <Satir etiket="hesap durumu">
            <Metin deger={h?.status} neden="Hesap durumu bildirilmedi" teknik="hesap bloğu `status` taşımıyor" />
          </Satir>
          <Satir etiket="uç (kimlik izi)">
            <Metin
              deger={h?.endpoint}
              neden="Bağlanılan sunucu adresi bildirilmedi"
              teknik="hesap bloğu `endpoint` taşımıyor"
              className="font-mono text-xs"
            />
          </Satir>
          <Satir etiket="hesap numarası">
            {/* MASKELİ BİLE OLSA YAZILAMAZ — çünkü GELMİYOR. Bkz. dosya başı, tuzak 1. */}
            <Olculemedi
              neden="Hesap numarası hiç gönderilmiyor — uydurmamak için boş bırakıldı"
              teknik="/api/alpaca hesap numarası döndürmüyor: adapters/alpaca.py::dashboard_view yalnız equity/cash/status/buying_power/positions/open_orders/endpoint taşıyor"
            />
          </Satir>
        </div>

        <div className="flex flex-col">
          <Satir etiket="akış (stream) sağlam mı">
            <OkRozet
              ok={akis?.stream_ok}
              iyi="akış sağlam"
              kotu="akış düşük"
              neden="Fiyat akışı bu süreçte hiç kontrol edilmedi — bozuk demek değil"
            />
          </Satir>
          <Satir etiket="akış bayat mı">
            <OkRozet
              ok={akis?.stream_stale === undefined || akis.stream_stale === null ? akis?.stream_stale : !akis.stream_stale}
              iyi="taze"
              kotu="bayat"
              neden="Fiyat akışının taze olup olmadığı bildirilmedi"
            />
          </Satir>
          <Satir etiket="son olay">
            <Metin
              deger={zamanMetni(akis?.stream_last_event_ts)}
              neden="Son akış olayının zamanı bildirilmedi"
              teknik="akış bloğu `stream_last_event_ts` taşımıyor"
              className="tabular-nums text-xs"
            />
          </Satir>
          <Satir etiket="son kontrol yaşı">
            <Metin
              deger={sureMetni(akis?.stream_checked_age_s)}
              neden="Akışın en son ne zaman kontrol edildiği bildirilmedi"
              teknik="akış bloğu `stream_checked_age_s` taşımıyor"
              className="tabular-nums text-xs"
            />
          </Satir>
          <Satir etiket="son akış hatası">
            <Metin
              deger={akis?.stream_last_error}
              neden="Kayıtlı bir akış hatası yok"
              teknik="akış bloğu bir hata metni taşımıyor"
              className="text-xs"
            />
          </Satir>
        </div>
      </div>

      {/* --- POZİSYONLAR ------------------------------------------------- */}
      <div className="flex flex-col gap-3">
        <h3 className="font-medium text-sm">Açık pozisyonlar</h3>
        {pozisyonlar.length === 0 ? (
          bosListeSupheli ? (
            <p className="text-amber-700 text-xs dark:text-amber-400">
              Liste boş ama bu “pozisyon yok” DEMEK DEĞİL: <code className="text-[11px]">alpaca.positions()</code> API
              ulaşılamadığında da boş liste döndürüyor ve ayrımı{" "}
              <code className="text-[11px]">transport()</code> taşıyor.{" "}
              <code className="text-[11px]">/api/diagnostics</code> içindeki{" "}
              <code className="text-[11px]">alpaca_ticaret</code> satırı{" "}
              {ticaret === null
                ? "hiç okunamadı"
                : ticaret.ok === null || ticaret.ok === undefined
                  ? "sağlığı ölçemedi"
                  : "taşımanın bozuk olduğunu söylüyor"}
              {typeof ticaret?.son_hata === "string" && ticaret.son_hata !== "" ? ` (${ticaret.son_hata})` : ""}.
            </p>
          ) : (
            <p className="text-muted-foreground text-xs">
              Pozisyon yok. Bu satır bir ÖLÇÜM: ticaret taşıması aynı anda sağlam görünüyor
              (<code className="text-[11px]">/api/diagnostics · alpaca_ticaret · ok=true</code>), yani boş liste
              gerçekten boşluğu anlatıyor.
            </p>
          )
        ) : (
          <>
            <PozisyonTablosu pozisyonlar={pozisyonlar} />
            {noktalar.length > 0 ? (
              <ChartContainer config={UPL_CONFIG} className="h-56 w-full">
                <BarChart data={noktalar} margin={{ left: 4, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="sembol" tickLine={false} axisLine={false} tickMargin={8} fontSize={11} />
                  <YAxis tickLine={false} axisLine={false} width={56} fontSize={11} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar isAnimationActive={false} dataKey="upl" radius={4}>
                    {noktalar.map((n) => (
                      // RENK BİR HÜKÜMDÜR: işaret ölçülen değerden geliyor, etiket
                      // ayrıştırmasından değil — biçim değişse de renk ters dönmez.
                      <Cell key={n.sembol} fill={n.upl >= 0 ? "var(--chart-2)" : "var(--destructive)"} />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            ) : (
              <Olculemedi
                neden="Hiçbir pozisyonun kâr/zararı okunamadı — çizilecek nokta yok"
                teknik="hiçbir pozisyon satırı sayıya çevrilebilir bir `unrealized_pl` taşımıyor"
              />
            )}
            {elenen > 0 ? (
              <p className="text-muted-foreground text-xs">
                Grafikten elenen satır: <span className="tabular-nums">{elenen}</span> (sembolü ya da K/Z'si
                ölçülemedi). Tabloda hepsi duruyor.
              </p>
            ) : null}
          </>
        )}
      </div>

      {/* --- AÇIK EMİRLER ------------------------------------------------ */}
      <div className="flex flex-col gap-3">
        <h3 className="font-medium text-sm">Açık emirler</h3>
        {emirler.length === 0 ? (
          <p className="text-muted-foreground text-xs">
            Açık emir yok — ya da <code className="text-[11px]">orders()</code> çağrısı düştü. Bu uç ikisini
            ayırmıyor; ayrım yine <code className="text-[11px]">/api/diagnostics · alpaca_ticaret</code> satırında.
          </p>
        ) : (
          <EmirTablosu emirler={emirler} />
        )}
      </div>

      {typeof v.note === "string" && v.note !== "" ? (
        <p className="text-muted-foreground text-xs">{v.note}</p>
      ) : null}
    </div>
  );
}

export function Broker({
  alpaca,
  teshis,
}: {
  readonly alpaca: Durum<AlpacaGovdesi>;
  readonly teshis: Durum<TeshisGovdesi>;
}) {
  return (
    <BolumKart
      baslik="Broker hesabı"
      soru="Ajanın aynaladığı Alpaca PAPER hesabı ne durumda?"
      ikon={Landmark}
      aksiyon={
        <Badge variant="outline" className="text-xs">
          /api/alpaca
        </Badge>
      }
    >
      <Kapi durum={alpaca} yol="/api/alpaca">
        {(v) => <Govde v={v} ticaret={ticaretSatiri(teshis.veri)} />}
      </Kapi>
    </BolumKart>
  );
}
