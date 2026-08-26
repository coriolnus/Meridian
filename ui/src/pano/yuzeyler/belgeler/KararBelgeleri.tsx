"use client";

/* ============================================================================
   KARAR BELGELERİ — "hangi hüküm hangi turda verildi?"
   ----------------------------------------------------------------------------
   İKİ AYRI SORU, İKİ AYRI TABLO ve bilerek birleştirilmiyorlar:
     · BELGE RAFI — "hangi belge panodan okunabiliyor?" Dört satır, her satırın
       durumu ÇİZİM ANINDA ölçülür; sabit bir "hazır" damgası basılmaz.
     · ARŞİV      — `GET /api/karar-belgeleri` künyesi: ad · tarih · başlık · bayt.
       Bu "hangi belgeler var" sorusudur; raf ise "hangisi sunuluyor" sorusu.
   Tek tabloya indirmek, uç düştüğünde rafın da kaybolması demekti — oysa "runbook
   cevap veriyor" bilgisi arşiv ucundan bağımsız bir ölçümdür.

   BAYAT BEYAN VAKASI (2026-08-25, düzeltildi): bu dosya bir tur boyunca "docs/
   altındaki KARAR ve HUKUM dosyalarını veren bir uç api.py’de YOK" yazdı. Cümle
   YAZILDIĞI ANDA doğruydu; uç aynı turda eklendi (api.py::api_karar_belgeleri) ve
   cümle yerinde kaldı — pano kendi ucunu yalanladı. Ders iki başlı: (1) YASA 6,
   yazılan alanın okuyucusunu ister; (2) ölçülmüş bir cümlenin TARİHİ vardır, uç
   değişince beyan da değişir. Çivileri tests/test_belge_rafi_v312.py taşıyor.

   HÂLÂ SUNULMAYAN, ve bu sefer ÖLÇÜLEREK yazılıyor: belge GÖVDESİ. Uç yalnız künye
   döndürüyor, bir kararın metnini panodan okumak bugün mümkün değil. Uç kullanıcıdan
   hiçbir dize almıyor (api.py::api_karar_belgeleri, `request` dışında parametre yok)
   ve gövde sunumu geldiğinde o kapı bilerek yeniden açılacak — sessizce değil.

   NABIZ YOK: arşiv tur kapanışında insan eliyle yazılıyor. 15 saniyede bir çekmek,
   okunan bir listeyi altından kaydırmak olurdu; tazeleme düğmesi kartın kendisinde.
   ============================================================================ */
import { Archive, ExternalLink, FileText, Map as MapIcon, RefreshCw, ScrollText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import Link from "../../rota";
import { useApi, type Durum as UcDurumu } from "../../veri";
import {
  bicimSayi,
  dizi,
  Kapi,
  metin,
  nesne,
  Olculemedi,
  OlculemediBlok,
  say,
  useUcYoklama,
  type UcYoklamasi,
} from "./ortak";

/** Arşiv kartının çapası. Kaydırma `href="#…"` ile YAPILMIYOR: pano hash yönlendirme
 *  kullanıyor (`#/dashboard/...`) ve çıplak bir parça bağı yönlendiriciyi kaçırırdı. */
const ARSIV_CAPASI = "belge-rafi-arsiv";

const ARSIV_UCU = "/api/karar-belgeleri";

/* ---- UCUN OKUYUCUSU ------------------------------------------------------ */

interface ArsivKaydi {
  readonly ad: string | null;
  readonly tarih: string | null;
  readonly baslik: string | null;
  readonly bayt: number | null;
  /** Uç ölçemediği alanın SEBEBİNİ buraya yazar; null = her şey ölçüldü. */
  readonly neden: string | null;
}

interface Arsiv {
  readonly ok: boolean;
  readonly dizin: string | null;
  /** `null` = dizin AÇILAMADI. Boş liste ile aynı şey DEĞİL: boş liste "arşiv boş" der. */
  readonly belgeler: readonly ArsivKaydi[] | null;
  readonly hata: string | null;
}

function kayitOku(v: unknown): ArsivKaydi {
  const k = nesne(v);
  if (k === null) {
    return {
      ad: null,
      tarih: null,
      baslik: null,
      bayt: null,
      neden: "uç, belgeler listesine nesne olmayan bir öğe koydu — künye okunamadı",
    };
  }
  return {
    ad: metin(k["ad"]),
    tarih: metin(k["tarih"]),
    baslik: metin(k["baslik"]),
    bayt: say(k["bayt"]),
    neden: metin(k["neden"]),
  };
}

/** Uç gövdesini tipe çevirir. Gövde nesne değilse `null` döner — çağıran "ölçülemedi"
 *  yazmak ZORUNDA kalır, boş bir tablo çizemez. */
function arsivOku(v: unknown): Arsiv | null {
  const g = nesne(v);
  if (g === null) return null;
  const ham = g["belgeler"];
  return {
    ok: g["ok"] === true,
    dizin: metin(g["dizin"]),
    // ÜÇ HÂL AYRI: dizi → liste · null → dizin açılamadı · başka bir şey → sözleşme
    // ihlali. Üçüncüsünü boş diziye indirmek, ihlali "arşiv boş" diye okuturdu.
    belgeler: Array.isArray(ham) ? dizi(ham).map(kayitOku) : null,
    hata: metin(g["hata"]),
  };
}

/* ---- BELGE RAFI ---------------------------------------------------------- */

/** Rafın satırları. `durum` ÇİZİM ANINDA hesaplanır — sabit bir "hazır" damgası
 *  basmıyoruz; hangi belgenin cevap verdiği ölçümden gelir. */
interface RafSatiri {
  readonly ad: string;
  readonly kaynak: string;
  readonly uc: string;
  readonly ikon: typeof FileText;
  readonly aciklama: string;
}

const RAF: readonly RafSatiri[] = [
  {
    ad: "Hafıza damıtımı",
    kaynak: "state/lessons.md",
    uc: "GET /api/memory",
    ikon: ScrollText,
    aciklama: "Ajanın kalıcı hafızası; her değerlendirmeye enjekte ediliyor. Yukarıdaki Hafıza bölümünde tam metin.",
  },
  {
    ad: "Runbook",
    kaynak: "docs/RUNBOOK.md",
    uc: "GET /runbook",
    ikon: FileText,
    aciklama: "Alarm satırlarının ve sessiz-hat sapmalarının hedefi. HTML sayfa olarak sunuluyor, JSON değil.",
  },
  {
    ad: "Yol haritası",
    kaynak: "ROADMAP.md (depo kökü)",
    uc: "GET /api/roadmap",
    ikon: MapIcon,
    aciklama: "Kalemlerin durum tahtası. Panoda Karar zinciri yüzeyinde çiziliyor — burada tekrar edilmiyor.",
  },
  {
    ad: "Karar arşivi",
    kaynak: "docs/KARAR-*.md · docs/HUKUM-*.md",
    uc: `GET ${ARSIV_UCU}`,
    ikon: Archive,
    aciklama: "Tur kararlarının yazıldığı yer. Uç KÜNYE döndürüyor; belge gövdesi henüz sunulmuyor.",
  },
];

export function KararBelgeleri({ hafizaOk, hafizaNeden }: { hafizaOk: boolean; hafizaNeden: string | null }) {
  const runbook = useUcYoklama("/runbook");
  const arsiv = useApi<Record<string, unknown>>(ARSIV_UCU, 0);
  const okunan = arsivOku(arsiv.veri);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="leading-none">Belge rafı</CardTitle>
          <CardDescription>Hangi belge panodan okunabiliyor, hangisi yalnız diskte duruyor?</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="min-w-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-0">Belge</TableHead>
                  <TableHead>Kaynak</TableHead>
                  <TableHead>Sunum ucu</TableHead>
                  <TableHead>Ölçülen durum</TableHead>
                  <TableHead className="text-right">Aç</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {RAF.map((s) => (
                  <TableRow key={s.ad}>
                    <TableCell className="pl-0">
                      <div className="flex min-w-0 items-center gap-2">
                        <s.ikon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                        <div className="min-w-0">
                          <p className="font-medium text-sm">{s.ad}</p>
                          <p className="text-muted-foreground text-xs leading-snug">{s.aciklama}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="break-all font-mono text-xs">{s.kaynak}</code>
                    </TableCell>
                    <TableCell>
                      <code className="whitespace-nowrap font-mono text-xs">{s.uc}</code>
                    </TableCell>
                    <TableCell>
                      <RafDurumu
                        satir={s}
                        runbook={runbook}
                        hafizaOk={hafizaOk}
                        hafizaNeden={hafizaNeden}
                        arsiv={arsiv}
                        okunan={okunan}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      <Acilis satir={s} runbook={runbook} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card id={ARSIV_CAPASI} className="scroll-mt-20">
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <CardTitle className="leading-none">Arşiv künyesi</CardTitle>
              <CardDescription>
                Tur kararları: hangi belge, hangi tarih, ne kadar yer tutuyor?
              </CardDescription>
            </div>
            {/* AYRI TAZELEME: yüzeyin üstündeki düğme `/api/memory` okumasını yeniliyor,
                bu kart ayrı bir uca bakıyor. Tek düğme ikisini de yeniliyormuş gibi
                göstermek, tazelenmemiş bir listeyi taze diye okutmak olurdu. */}
            <Button variant="outline" size="sm" onClick={arsiv.tazele}>
              <RefreshCw className="size-3.5" aria-hidden />
              Arşivi tazele
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Kapi durum={arsiv} ad={`\`${ARSIV_UCU}\``} yukseklik="h-64">
            {(g) => <ArsivGovdesi arsiv={arsivOku(g)} />}
          </Kapi>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="leading-none">Henüz eklenmedi</CardTitle>
          <CardDescription>Bu bölümün tamamlanması için ne eksik?</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm leading-relaxed">
          <p>
            Künye geldi, GÖVDE gelmedi: bir kararın metnini panodan okumak hâlâ mümkün değil.
            Uç bugün kullanıcıdan hiçbir dize almıyor, yani dosya adı üzerinden bir yol geçişi
            yüzeyi de yok. Gövde sunumu bir `?ad=` parametresi getirdiğinde o kapı bilerek
            açılacak — çivileri şimdiden kurulu (tests/test_belge_rafi_v312.py).
          </p>
          <p className="text-muted-foreground text-xs">
            Gövde geldiğinde bu kartın yerine belge okuyucusu gelir; yukarıdaki iki tablo o zaman
            da kalır, çünkü "hangi belgeler var" ile "hangi belge sunuluyor" ayrı sorulardır.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

/* ---- ARŞİV GÖVDESİ ------------------------------------------------------- */

function ArsivGovdesi({ arsiv }: { arsiv: Arsiv | null }) {
  if (arsiv === null) {
    return (
      <OlculemediBlok
        baslik="Arşiv künyesi okunamadı"
        neden="Sunucu cevap verdi ama içeriği beklenen biçimde değil. Bu, arşivin boş olduğu anlamına gelmez — sunucu tarafında bir uyumsuzluk var"
        teknik={`\`${ARSIV_UCU}\` 200 döndü ama gövdesi bir JSON nesnesi değil`}
      />
    );
  }
  if (arsiv.belgeler === null) {
    // İKİ AYRI SEBEP, İKİ AYRI BAŞLIK: uç gerekçe yazdıysa dizini açamamıştır (ölçülmüş bir
    // arıza); yazmadıysa alanın kendisi sözleşme dışıdır. Birine ötekinin adını vermek,
    // operatörü yanlış yere — diske ya da sunucuya — bakmaya gönderirdi.
    return (
      <OlculemediBlok
        baslik={arsiv.hata === null ? "Belge listesi beklenen biçimde gelmedi" : "Arşiv klasörü açılamadı"}
        neden={
          arsiv.hata ??
          "Belge listesi ne liste ne de boş olarak geldi ve nedeni yazılmadı — sunucu tarafına bakılmalı."
        }
        teknik={`\`${ARSIV_UCU}\` \`belgeler\` alanını ne dizi ne null döndürdü ve \`hata\` da yazmadı`}
      />
    );
  }

  const belgeler = arsiv.belgeler;
  const kararN = belgeler.filter((b) => b.ad !== null && b.ad.startsWith("KARAR-")).length;
  const hukumN = belgeler.filter((b) => b.ad !== null && b.ad.startsWith("HUKUM-")).length;
  const digerN = belgeler.length - kararN - hukumN;

  // TOPLAM YALNIZ ÖLÇÜLENLERİN TOPLAMIDIR ve ölçülemeyenlerin SAYISI yanına yazılır.
  // Ölçülemeyeni 0 sayıp toplama katmak, eksik bir toplamı tam gibi göstermek olurdu.
  let toplamBayt = 0;
  let baytsizN = 0;
  for (const b of belgeler) {
    if (b.bayt === null) baytsizN += 1;
    else toplamBayt += b.bayt;
  }

  return (
    <div className="flex flex-col gap-3">
      {arsiv.ok ? null : (
        <div className="rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2">
          <p className="break-words text-amber-700 text-xs leading-relaxed dark:text-amber-300">
            Uç `ok: false` dedi ama yine de bir liste verdi — aşağısı EKSİK olabilir.{" "}
            {arsiv.hata ?? "Gerekçe yazılmamış."}
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="gap-1">
          <Archive className="size-3" aria-hidden />
          {arsiv.dizin ?? (
            <Olculemedi
              neden="Hangi klasörün tarandığı bildirilmedi"
              teknik="uç `dizin` alanını yazmadı"
            />
          )}
        </Badge>
        <Badge variant="ghost">{bicimSayi(belgeler.length)} belge</Badge>
        <Badge variant="ghost">{bicimSayi(kararN)} KARAR</Badge>
        <Badge variant="ghost">{bicimSayi(hukumN)} HÜKÜM</Badge>
        {digerN === 0 ? null : (
          // Desen dışı bir ad rafa giremez (uç süzüyor); yine de sayılıyor ki uç gevşerse
          // sessizce değil, ekranda görünsün.
          <Badge variant="destructive" className="text-[10px]">
            {bicimSayi(digerN)} desen dışı
          </Badge>
        )}
        <Badge variant="ghost">
          {bicimSayi(toplamBayt)} bayt
          {baytsizN === 0 ? null : ` (${bicimSayi(baytsizN)} belge ölçülemedi)`}
        </Badge>
      </div>

      {belgeler.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Dizin okundu ve içinde KARAR-*.md / HUKUM-*.md deseni taşıyan dosya YOK. Bu ölçülmüş bir
          boşluktur — "okuyamadım" ile aynı şey değil.
        </p>
      ) : (
        <div className="min-w-0 overflow-x-auto">
          {/* SIRA UÇTAN GELİR (en yeni önce, tarihsiz sona) ve burada YENİDEN sıralanmaz:
              iki ayrı sıralama kuralı, hangisinin geçerli olduğunu hiçbir yere yazmadan
              ayrışırdı. Tek kural, tek yer. */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-0">Belge</TableHead>
                <TableHead>Tarih</TableHead>
                <TableHead className="text-right">Boyut</TableHead>
                <TableHead>Ölçülemeyen</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {belgeler.map((b, i) => (
                <TableRow key={b.ad ?? `adsiz-${i}`}>
                  <TableCell className="pl-0">
                    <div className="min-w-0">
                      <p className="font-medium text-sm leading-snug">
                        {b.baslik ?? (
                          <Olculemedi
                            neden={b.neden ?? "Belgenin başlığı bildirilmedi ve nedeni de yazılmadı"}
                            className="text-sm"
                          />
                        )}
                      </p>
                      <code className="break-all font-mono text-muted-foreground text-xs">
                        {b.ad ?? "(uç `ad` alanını yazmadı)"}
                      </code>
                    </div>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-xs tabular-nums">
                    {b.tarih ?? <Olculemedi neden={b.neden ?? "Belgenin tarihi bildirilmedi ve nedeni de yazılmadı"} />}
                  </TableCell>
                  <TableCell className="text-right text-xs tabular-nums">
                    {b.bayt === null ? (
                      <Olculemedi neden={b.neden ?? "Belgenin boyutu bildirilmedi ve nedeni de yazılmadı"} />
                    ) : (
                      bicimSayi(b.bayt)
                    )}
                  </TableCell>
                  <TableCell>
                    {b.neden === null ? (
                      <span className="text-muted-foreground text-xs">tüm alanlar ölçüldü</span>
                    ) : (
                      <span className="break-words text-muted-foreground text-xs leading-snug">{b.neden}</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

/* ---- RAF HÜCRELERİ ------------------------------------------------------- */

function RafDurumu({
  satir,
  runbook,
  hafizaOk,
  hafizaNeden,
  arsiv,
  okunan,
}: {
  satir: RafSatiri;
  runbook: UcYoklamasi;
  hafizaOk: boolean;
  hafizaNeden: string | null;
  arsiv: UcDurumu<Record<string, unknown>>;
  okunan: Arsiv | null;
}) {
  if (satir.uc.endsWith("/api/memory")) {
    return hafizaOk ? (
      <Badge variant="outline" className="text-[10px]">
        okundu
      </Badge>
    ) : (
      <span className="text-muted-foreground text-xs leading-snug">{hafizaNeden ?? "okunamadı"}</span>
    );
  }
  if (satir.uc.endsWith("/runbook")) {
    if (runbook.ok === null && runbook.hata === null) {
      return <span className="text-muted-foreground text-xs">yoklanıyor…</span>;
    }
    if (runbook.hata !== null) {
      return <span className="text-muted-foreground text-xs leading-snug">yoklanamadı: {runbook.hata}</span>;
    }
    return runbook.ok === true ? (
      <Badge variant="outline" className="text-[10px]">
        HTTP {bicimSayi(runbook.kod ?? 0)} · cevap veriyor
      </Badge>
    ) : (
      <Badge variant="destructive" className="text-[10px]" title="503 = docs/RUNBOOK.md henüz üretilmemiş">
        HTTP {runbook.kod === null ? "?" : bicimSayi(runbook.kod)}
      </Badge>
    );
  }
  if (satir.uc.endsWith(ARSIV_UCU)) {
    if (arsiv.oturumDustu) {
      return <span className="text-muted-foreground text-xs leading-snug">oturum düştü — 401</span>;
    }
    if (okunan === null) {
      return arsiv.yukleniyor ? (
        <span className="text-muted-foreground text-xs">okunuyor…</span>
      ) : (
        <span className="text-muted-foreground text-xs leading-snug">
          {arsiv.hata ?? "uç gövdesi JSON nesnesi değil"}
        </span>
      );
    }
    if (okunan.belgeler === null) {
      return (
        <span className="text-muted-foreground text-xs leading-snug">
          {okunan.hata ?? "dizin açılamadı, gerekçe de yazılmadı"}
        </span>
      );
    }
    // BAYAT AMA VAR: tazeleme düştüğünde `veri` yerinde kalır ve `hata` dolar (veri.ts
    // sözleşmesi). Sayıyı taze gibi basmak, ölçülmemiş bir anı ölçülmüş gibi göstermek olurdu.
    return arsiv.hata === null ? (
      <Badge variant="outline" className="text-[10px]">
        {bicimSayi(okunan.belgeler.length)} belge · künye okundu
      </Badge>
    ) : (
      <span className="text-muted-foreground text-xs leading-snug">
        {bicimSayi(okunan.belgeler.length)} belge — BAYAT, tazeleme düştü: {arsiv.hata}
      </span>
    );
  }
  // ROADMAP: bu yüzey onu ÇİZMİYOR (Karar zinciri çiziyor), o yüzden buradan
  // ölçüm iddiası da yok. "Bilmiyorum" demek, bilmediğini gizlemekten iyidir.
  return (
    <span className="text-muted-foreground text-xs leading-snug">
      bu yüzeyden ölçülmedi — tahtayı Karar zinciri yüzeyi okuyor
    </span>
  );
}

function Acilis({ satir, runbook }: { satir: RafSatiri; runbook: UcYoklamasi }) {
  if (satir.uc.endsWith("/api/memory")) {
    return (
      <Button asChild variant="ghost" size="sm" className="text-xs">
        <a href="#/dashboard/file-manager/hafiza">Yukarı</a>
      </Button>
    );
  }
  if (satir.uc.endsWith(ARSIV_UCU)) {
    return (
      <Button
        variant="ghost"
        size="sm"
        className="text-xs"
        onClick={() =>
          document.getElementById(ARSIV_CAPASI)?.scrollIntoView({ behavior: "smooth", block: "start" })
        }
      >
        Künye
      </Button>
    );
  }
  if (satir.uc.endsWith("/runbook")) {
    // BAĞ ÖLÇÜME GÖRE SÖNÜKLEŞİR ama `disabled` KULLANILMAZ: `asChild` bir <a>
    // çiziyor ve `disabled` bir bağlantı elemanının özelliği değil (React uyarısı
    // + ekran okuyucuda anlamsız). Doğru sinyal `aria-disabled` + tıklamayı kesmek.
    const kapali = runbook.ok === false;
    return (
      <Button
        asChild
        variant="ghost"
        size="sm"
        className={kapali ? "pointer-events-none text-xs opacity-50" : "text-xs"}
      >
        <a
          href="/runbook"
          target="_blank"
          rel="noreferrer"
          aria-disabled={kapali || undefined}
          title={kapali ? `uç HTTP ${runbook.kod ?? "?"} döndü — belge üretilmemiş olabilir` : undefined}
        >
          Aç
          <ExternalLink className="size-3" aria-hidden />
        </a>
      </Button>
    );
  }
  return (
    <Button asChild variant="ghost" size="sm" className="text-xs">
      <Link href="/dashboard/kanban">Tahta</Link>
    </Button>
  );
}
