"use client";

/* ============================================================================
   KARAR BELGELERİ — "hangi hüküm hangi turda verildi?"
   ----------------------------------------------------------------------------
   BU BÖLÜMÜN CEVABI BUGÜN "SUNULAMIYOR" ve bu bir tasarım tercihi değil, ölçülmüş
   bir eksik.

   ÖLÇÜM (2026-08-25, `meridian/api.py` — 78 rotanın tamamı `@app.get|post|delete`
   ile tarandı): `docs/` altındaki KARAR-* / HUKUM-* dosyalarını LİSTELEYEN ya da
   SUNAN bir uç YOK. Dosya sunan tek iki yer var ve ikisi de tek bir belgeye
   bağlı:
     · `GET /runbook`      → `docs/RUNBOOK.md`, HTML sayfası olarak (api.py:1097)
     · `GET /api/roadmap`  → depo kökündeki `ROADMAP.md`, ayrıştırılmış tahta olarak
                             (api.py:6972; `_roadmap_yolu` şerhi: "`docs/` altındakiler
                             tarihli TÜREVLERDİR ve SSoT değildir")
   Karar/hüküm arşivinin kendisi hiçbir uçtan geçmiyor.

   NEDEN BURAYA SAHTE BİR DOSYA LİSTESİ ÇİZİLMEDİ: elimde dizinin içeriği var
   (bu tur onu okudum) ama panoya YAZILMIŞ bir liste, tarayıcıda HİÇBİR ŞEY
   ÖLÇMEDEN duran bir liste olurdu — bir dosya silinse, on tane eklense sayfa aynı
   kalırdı ve operatör onu canlı sanırdı. Bu tam olarak landing sayfasındaki
   uydurma rakam vakasının tekrarı olurdu (C10 bekçisi o yüzden var).

   BUNUN YERİNE: erişilebilen belgeler ÖLÇÜLEREK gösteriliyor (`/runbook` HEAD ile
   yoklanıyor, `lessons.md` gövdesinden ölçülüyor) ve erişilemeyen raf AÇIK KALEM
   olarak işaretleniyor. Yeni bir uç eklemek bu ajanın yazma izni DIŞINDA
   (`api.py` kapalı) — kalem tur raporuna devrediliyor.
   ============================================================================ */
import { CircleSlash, ExternalLink, FileText, Map as MapIcon, ScrollText } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import Link from "../../rota";
import { bicimSayi, useUcYoklama, type UcYoklamasi } from "./ortak";

/** Rafın satırları. `durum` ÇİZİM ANINDA hesaplanır — sabit bir "hazır" damgası
 *  basmıyoruz; hangi belgenin cevap verdiği ölçümden gelir. */
interface RafSatiri {
  readonly ad: string;
  readonly kaynak: string;
  readonly uc: string | null;
  readonly ikon: typeof FileText;
  readonly aciklama: string;
}

const RAF: readonly RafSatiri[] = [
  {
    ad: "Hafıza damıtımı",
    kaynak: "state/lessons.md",
    uc: "GET /api/memory",
    ikon: ScrollText,
    aciklama: "Ajanın kalıcı hafızası; her yansımaya enjekte ediliyor. Yukarıdaki Hafıza bölümünde tam metin.",
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
    ad: "Karar ve hüküm arşivi",
    kaynak: "docs/KARAR-*.md · docs/HUKUM-*.md",
    uc: null,
    ikon: CircleSlash,
    aciklama: "Tur hükümlerinin yazıldığı yer. Bu dosyaları listeleyen ya da sunan bir uç api.py'de YOK.",
  },
];

export function KararBelgeleri({ hafizaOk, hafizaNeden }: { hafizaOk: boolean; hafizaNeden: string | null }) {
  const runbook = useUcYoklama("/runbook");

  return (
    <div className="flex flex-col gap-4">
      <Alert>
        <CircleSlash />
        <AlertTitle>Karar/hüküm arşivinin sunum ucu yok — bu bölüm eksik, boş değil</AlertTitle>
        <AlertDescription>
          <p>
            `docs/` altındaki KARAR-* ve HUKUM-* dosyalarını listeleyen ya da içeriğini döndüren bir
            uç `meridian/api.py`de bulunmuyor — rota tablosunun tamamı tarandı. Panoya elle yazılmış bir dosya
            listesi koymadım: tarayıcıda hiçbir şey ölçmeyen, dosya silinse bile aynı kalan bir liste,
            canlı sanılan bir yalan olurdu. Aşağıdaki raf YALNIZ gerçekten sunulan belgeleri gösterir
            ve her satırın durumu ölçülür.
          </p>
        </AlertDescription>
      </Alert>

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
                      {s.uc === null ? (
                        <Badge variant="destructive" className="text-[10px]">
                          uç yok
                        </Badge>
                      ) : (
                        <code className="whitespace-nowrap font-mono text-xs">{s.uc}</code>
                      )}
                    </TableCell>
                    <TableCell>
                      <Durum satir={s} runbook={runbook} hafizaOk={hafizaOk} hafizaNeden={hafizaNeden} />
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

      <Card>
        <CardHeader>
          <CardTitle className="leading-none">Açık kalem</CardTitle>
          <CardDescription>Bu bölümün dolması için ne gerekiyor?</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm leading-relaxed">
          <p>
            `docs/` arşivini listeleyen bir uç gerekiyor — en azından ad, tarih ve boyut; tercihen tek
            belge gövdesi de. Uç eklemek bu yüzeyin yazma izni dışında (`meridian/api.py` kapalı), bu
            yüzden kalem tur raporuna açık bırakıldı.
          </p>
          <p className="text-muted-foreground text-xs">
            Uç geldiğinde bu kartın yerine gerçek bir dosya listesi (ızgara + liste görünümü) gelir;
            bugünkü raf tablosu o zaman da kalır, çünkü "hangi belge sunuluyor" sorusu ayrı bir sorudur.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function Durum({
  satir,
  runbook,
  hafizaOk,
  hafizaNeden,
}: {
  satir: RafSatiri;
  runbook: UcYoklamasi;
  hafizaOk: boolean;
  hafizaNeden: string | null;
}) {
  if (satir.uc === null) {
    return (
      <span className="text-muted-foreground text-xs leading-snug">
        ölçülemedi — sunan uç olmadığı için pano bu rafa hiç bakamıyor
      </span>
    );
  }
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
  // ROADMAP: bu yüzey onu ÇİZMİYOR (Karar zinciri çiziyor), o yüzden buradan
  // ölçüm iddiası da yok. "Bilmiyorum" demek, bilmediğini gizlemekten iyidir.
  return (
    <span className="text-muted-foreground text-xs leading-snug">
      bu yüzeyden ölçülmedi — tahtayı Karar zinciri yüzeyi okuyor
    </span>
  );
}

function Acilis({ satir, runbook }: { satir: RafSatiri; runbook: UcYoklamasi }) {
  if (satir.uc === null) {
    return <span className="text-muted-foreground text-xs">—</span>;
  }
  if (satir.uc.endsWith("/api/memory")) {
    return (
      <Button asChild variant="ghost" size="sm" className="text-xs">
        <a href="#/dashboard/file-manager/hafiza">Yukarı</a>
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
