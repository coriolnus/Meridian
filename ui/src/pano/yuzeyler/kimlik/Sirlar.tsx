"use client";

/* ============================================================================
   SIRLAR VE GÜVENLİK DURUŞU — `/api/secrets` + `/api/diagnostics.saglayicilar`
   ----------------------------------------------------------------------------
   BU BÖLÜMÜN BİRİNCİ KURALI BİR ÇİZİM KURALI DEĞİL, BİR GÜVENLİK KURALI:
   SIR DEĞERİ HİÇBİR KOŞULDA EKRANA GELMEZ. `/api/secrets` gövdesinde her satır
   `hint` alanı taşıyor ve o alan sunucuda ZATEN maskeli (`secrets.py::mask` →
   `••••` + son 4 karakter). Buna rağmen ÇİZİLMİYOR ve tip dosyasında yanına
   "BU PANO ONU ÇİZMEZ" yazıyor: son dört karakter bir anahtarı tanımak için
   yeterli bir parmak izidir, ve bu pano bir tünelden açılabiliyor. Ekranın
   cevapladığı soru "anahtar ne" değil, "anahtar KURULU MU"dur.

   ~~YENİ SIR GİRME FORMU DA YOK — bilinçli.~~ 2026-08-25'te DEĞİŞTİ ve şerh
   düzeltiliyor: operatör anahtar girebileceği bir alan olmadığını bildirdi
   ("KEY'leri girebileceğim bir alan göremedim") ve form eklendi — `SirGirisi.tsx`,
   bu tablonun hemen ALTINDA. İş bölümü NET kalsın diye iki bileşen ayrı:
   BU dosya "anahtar kurulu mu" sorusunu okur, ÖTEKİ "anahtarı gir" eylemini taşır.
   Eski gerekçe ("parolayı gören her sekme bir yazma yüzeyine dönerdi") YANLIŞ
   değildi ama EKSİKTİ: yazma yetkisi zaten oturumun kendisinde — `POST
   /api/secrets/{name}` `_auth` istiyor ve panoya girebilen zaten o yetkiye sahip.
   Formu saklamak yetkiyi daraltmıyordu, yalnız operatörü terminale gönderiyordu.

   "SON TEST SONUCU" NEREDEN GELİYOR: `GET /api/secrets/test/{provider}` CANLI bir
   ağ çağrısı yapar — panonun her açılışında beş sağlayıcıya ping atmak, ölçmek
   isterken sistemi yormak olurdu. Onun yerine `/api/diagnostics.saglayicilar`
   okunuyor: AĞ ÇAĞRISI YOK, hepsi süreç-içi sayaç (api.py::_saglayicilar). Ucun
   kendi beyanı da ekranda: "sağlık sayaçları DİSKE YAZILMAZ — boş bir kart
   'sağlayıcı bozuk' değil 'bu süreçte henüz çağrı yapılmadı' demektir."
   ============================================================================ */
import { KeyRound, ShieldAlert } from "lucide-react";
import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { type ChartConfig, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Metin, Olculemedi, OkRozet, Satir, zamanMetni } from "./parcalar";
import type { SirlarGovdesi, TeshisGovdesi } from "./uctipleri";

/* KATEGORİLER `meridian/secrets.py::ALLOWED` OKUNARAK yazıldı — orada her adın
   yanında ne işe yaradığı şerh edilmiş. Listede OLMAYAN bir ad gelirse (izin
   listesi büyürse) satır "sınıflanmadı" kovasına düşer ve tabloda öyle görünür;
   sessizce bir kovaya sokmak, yeni bir anahtarın yanlış başlık altında
   görünmesi demek olurdu. */
const KATEGORI: Readonly<Record<string, string>> = {
  FMP_API_KEY: "veri",
  FMP_API_KEY_2: "veri",
  FINVIZ_API_KEY: "veri",
  MASSIVE_API_KEY: "veri",
  ALPACA_PAPER_KEY: "broker (kağıt)",
  ALPACA_PAPER_SECRET: "broker (kağıt)",
  ALPACA_PAPER_ENDPOINT: "broker (kağıt)",
  TELEGRAM_BOT_TOKEN: "bildirim",
  TELEGRAM_CHAT_ID: "bildirim",
  MERIDIAN_WEBHOOK_URL: "bildirim",
  HERMES_API_KEY: "beyin (LLM)",
  ANTHROPIC_API_KEY: "beyin (LLM)",
  NOUS_API_KEY: "beyin (LLM)",
  NOUS_ENDPOINT: "beyin (LLM)",
  NOUS_MODEL: "beyin (LLM)",
  NOUS_FALLBACK_MODEL: "beyin (LLM)",
  GEMINI_API_KEY: "beyin (LLM)",
  GEMINI_OAUTH_TOKEN: "beyin (LLM)",
  GEMINI_MODEL: "beyin (LLM)",
  HERMES_BRAIN_ORDER: "beyin (LLM)",
  LITESTREAM_ACCESS_KEY_ID: "yedekleme",
  LITESTREAM_SECRET_ACCESS_KEY: "yedekleme",
};

const SINIFLANMADI = "sınıflanmadı";

const KOVA_CONFIG = {
  kurulu: { label: "Kurulu", color: "var(--chart-2)" },
  eksik: { label: "Kurulu değil", color: "var(--chart-4)" },
  olculemedi: { label: "Ölçülemedi", color: "var(--muted-foreground)" },
} satisfies ChartConfig;

interface KovaSatiri {
  readonly kategori: string;
  readonly kurulu: number;
  readonly eksik: number;
  readonly olculemedi: number;
}

interface SirSatiri {
  readonly ad: string;
  readonly kategori: string;
  /** ÜÇ DEĞERLİ: uç `set` alanını hiç döndürmezse `undefined` kalır. */
  readonly kurulu: boolean | undefined;
  readonly kaynak: string | null | undefined;
}

function satirlariCikar(v: SirlarGovdesi): readonly SirSatiri[] {
  const s = v.secrets;
  if (s === undefined || s === null || typeof s !== "object") return [];
  return Object.keys(s)
    .sort()
    .map((ad) => {
      const d = s[ad];
      return {
        ad,
        kategori: KATEGORI[ad] ?? SINIFLANMADI,
        kurulu: typeof d?.set === "boolean" ? d.set : undefined,
        kaynak: d?.source,
      };
    });
}

function kovalariKur(satirlar: readonly SirSatiri[]): readonly KovaSatiri[] {
  const m = new Map<string, { kurulu: number; eksik: number; olculemedi: number }>();
  for (const r of satirlar) {
    const k = m.get(r.kategori) ?? { kurulu: 0, eksik: 0, olculemedi: 0 };
    if (r.kurulu === true) k.kurulu += 1;
    else if (r.kurulu === false) k.eksik += 1;
    else k.olculemedi += 1; // `set` alanı GELMEDİ — "eksik" saymak yalan olurdu
    m.set(r.kategori, k);
  }
  return [...m.entries()]
    .map(([kategori, k]) => ({ kategori, ...k }))
    .sort((a, b) => b.kurulu + b.eksik + b.olculemedi - (a.kurulu + a.eksik + a.olculemedi));
}

/* --- SIR TABLOSU + KOVA GRAFİĞİ ------------------------------------------ */

function SirGovdesi({ v }: { readonly v: SirlarGovdesi }) {
  const satirlar = useMemo(() => satirlariCikar(v), [v]);
  const kovalar = useMemo(() => kovalariKur(satirlar), [satirlar]);
  const kuruluN = satirlar.filter((r) => r.kurulu === true).length;
  const olculemeyenN = satirlar.filter((r) => r.kurulu === undefined).length;

  if (satirlar.length === 0) {
    return (
      <Olculemedi neden="/api/secrets `secrets` sözlüğünü döndürmedi ya da boş döndürdü — hangi anahtarların bilindiği bile okunamadı" />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">
          <span className="tabular-nums">
            {kuruluN}/{satirlar.length}
          </span>{" "}
          anahtar kurulu
        </Badge>
        {olculemeyenN > 0 ? (
          <Badge variant="outline" title="uç bu satırlarda `set` alanını döndürmedi">
            <span className="tabular-nums">{olculemeyenN}</span> satır ölçülemedi
          </Badge>
        ) : null}
      </div>

      <ChartContainer config={KOVA_CONFIG} className="h-56 w-full">
        <BarChart data={[...kovalar]} layout="vertical" margin={{ left: 8, right: 12, top: 4, bottom: 0 }}>
          <CartesianGrid horizontal={false} />
          <XAxis type="number" tickLine={false} axisLine={false} allowDecimals={false} fontSize={11} />
          <YAxis type="category" dataKey="kategori" tickLine={false} axisLine={false} width={112} fontSize={11} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar isAnimationActive={false} dataKey="kurulu" stackId="a" fill="var(--color-kurulu)" radius={[0, 0, 0, 0]} />
          <Bar isAnimationActive={false} dataKey="eksik" stackId="a" fill="var(--color-eksik)" radius={[0, 0, 0, 0]} />
          <Bar isAnimationActive={false} dataKey="olculemedi" stackId="a" fill="var(--color-olculemedi)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ChartContainer>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Anahtar</TableHead>
              <TableHead className="w-[9rem]">Kategori</TableHead>
              <TableHead className="w-[10rem]">Durum</TableHead>
              <TableHead className="w-[7rem]">Kaynak</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {satirlar.map((r) => (
              <TableRow key={r.ad}>
                <TableCell className="font-mono text-xs">{r.ad}</TableCell>
                <TableCell className="text-muted-foreground text-xs">{r.kategori}</TableCell>
                <TableCell>
                  <OkRozet
                    ok={r.kurulu}
                    iyi="kurulu"
                    kotu="kurulu değil"
                    neden="/api/secrets bu satırda `set` alanını döndürmedi"
                  />
                </TableCell>
                <TableCell className="text-xs">
                  <Metin deger={r.kaynak} neden="kurulu değil — kaynak diye bir şey yok" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <p className="text-muted-foreground text-xs">
        Değer sütunu YOK ve olmayacak: uç maskeli bir <code className="text-[11px]">hint</code> döndürüyor
        (<code className="text-[11px]">••••</code> + son 4 karakter) ama son dört karakter bir anahtarı tanımaya yeter.
        Bu ekranın cevapladığı soru “anahtar ne” değil, “anahtar kurulu mu”. Anahtar girmek için aşağıdaki forma bak.
      </p>
    </div>
  );
}

/* --- GÜVENLİK DURUŞU ------------------------------------------------------ */

function GuvenlikGovdesi({ v }: { readonly v: SirlarGovdesi }) {
  return (
    <div className="flex flex-col">
      <Satir etiket="mod (config.MODE)">
        <Metin deger={v.mode} neden="/api/secrets `mode` alanını döndürmedi" className="font-mono text-xs" />
      </Satir>
      <Satir etiket="canlı işlem açık mı">
        {/* `live_enabled` MODDAN AYRI BİR SORU: mod + risk kabulünün VE'si. "mod live
            ama risk kabulü yok" hâlinde bu false döner ve mod satırı yine "live" der. */}
        <OkRozet
          ok={v.live_enabled}
          iyi="AÇIK — gerçek para yolu"
          kotu="kapalı"
          neden="/api/secrets `live_enabled` alanını döndürmedi"
        />
      </Satir>
      <Satir etiket="özerklik düzeyi">
        <Deger deger={v.autonomy_level} neden="/api/secrets `autonomy_level` alanını döndürmedi" />
      </Satir>
      <Satir etiket="varsayılan Gemini modeli">
        <Metin
          deger={v.model_defaults?.GEMINI_MODEL}
          neden="/api/secrets `model_defaults.GEMINI_MODEL` alanını döndürmedi"
          className="font-mono text-xs"
        />
      </Satir>
      <Satir etiket="varsayılan Nous modeli">
        <Metin
          deger={v.model_defaults?.NOUS_MODEL}
          neden="hermes modülü NOUS_DEFAULT_MODEL sabiti taşımıyor (uç bu alanı null döndürür)"
          className="font-mono text-xs"
        />
      </Satir>
    </div>
  );
}

/* --- SAĞLAYICI SAĞLIĞI (son test sonucu) ---------------------------------- */

function SaglayiciGovdesi({ v }: { readonly v: TeshisGovdesi }) {
  const blok = v.saglayicilar;
  const xs = blok?.saglayicilar;
  if (!Array.isArray(xs) || xs.length === 0) {
    return (
      <Olculemedi neden="/api/diagnostics `saglayicilar.saglayicilar` listesi gelmedi — sağlayıcı sağlığı bu istekte okunamadı" />
    );
  }
  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Sağlayıcı</TableHead>
              <TableHead className="w-[9rem]">Son durum</TableHead>
              <TableHead className="text-right">Çağrı</TableHead>
              <TableHead className="text-right">Hata</TableHead>
              <TableHead className="text-right">Hata oranı</TableHead>
              <TableHead>Son çağrı</TableHead>
              <TableHead>Son hata</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {xs.map((s, i) => (
              <TableRow key={s.ad ?? `satir-${i}`}>
                <TableCell className="font-mono text-xs">
                  <Metin deger={s.ad} neden="satır `ad` taşımıyor" />
                </TableCell>
                <TableCell>
                  <OkRozet
                    ok={s.ok}
                    iyi="son çağrı başarılı"
                    kotu="son çağrı düştü"
                    neden={s.olculemedi ?? "bu süreçte henüz çağrı yapılmadı — 'bozuk' DEĞİL"}
                  />
                </TableCell>
                <TableCell className="text-right">
                  <Deger deger={s.cagri} neden="sayaç gelmedi" />
                </TableCell>
                <TableCell className="text-right">
                  <Deger deger={s.hata} neden="sayaç gelmedi" />
                </TableCell>
                <TableCell className="text-right">
                  <Deger
                    deger={typeof s.hata_orani === "number" ? s.hata_orani * 100 : s.hata_orani}
                    birim="%"
                    basamak={1}
                    neden="çağrı sayacı yok ya da biçimsiz — oran hesaplanamadı (0 yazmak 'hiç bozulmadı' diye okunurdu)"
                  />
                </TableCell>
                <TableCell className="text-xs">
                  <Metin deger={zamanMetni(s.son_cagri_ts)} neden="satır bir zaman damgası taşımıyor" />
                </TableCell>
                <TableCell className="max-w-[16rem] truncate text-xs" title={s.son_hata ?? undefined}>
                  <Metin deger={s.son_hata} neden="bu süreçte kaydedilmiş hata yok" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {typeof blok?.beyan === "string" && blok.beyan !== "" ? (
        <p className="text-muted-foreground text-xs">{blok.beyan}</p>
      ) : null}
    </div>
  );
}

/* --- DIŞA AÇILAN BÖLÜM ---------------------------------------------------- */

export function Sirlar({
  sirlar,
  teshis,
}: {
  readonly sirlar: Durum<SirlarGovdesi>;
  readonly teshis: Durum<TeshisGovdesi>;
}) {
  return (
    <>
      <BolumKart
        baslik="Güvenlik duruşu"
        soru="Hangi modda koşuyoruz, canlı para yolu açık mı?"
        ikon={ShieldAlert}
        aksiyon={
          <Badge variant="outline" className="text-xs">
            /api/secrets
          </Badge>
        }
      >
        <Kapi durum={sirlar} yol="/api/secrets">
          {(v) => <GuvenlikGovdesi v={v} />}
        </Kapi>
      </BolumKart>

      <BolumKart
        baslik="Anahtarlar"
        soru="Hangi anahtar kurulu, hangisi eksik? (değer ASLA gösterilmez)"
        ikon={KeyRound}
        aksiyon={
          <Badge variant="outline" className="text-xs">
            /api/secrets
          </Badge>
        }
      >
        <Kapi durum={sirlar} yol="/api/secrets">
          {(v) => <SirGovdesi v={v} />}
        </Kapi>
      </BolumKart>

      <BolumKart
        baslik="Sağlayıcıların son hâli"
        soru="Kurulu anahtarlar gerçekten çalışıyor mu?"
        ikon={ShieldAlert}
        aksiyon={
          <Badge variant="outline" className="text-xs">
            /api/diagnostics · saglayicilar
          </Badge>
        }
      >
        <Kapi durum={teshis} yol="/api/diagnostics">
          {(v) => <SaglayiciGovdesi v={v} />}
        </Kapi>
      </BolumKart>
    </>
  );
}
