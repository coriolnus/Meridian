"use client";

/* ============================================================================
   SEANS TAKVİMİ — hangi günde koşu/döngü kaydı VAR
   ----------------------------------------------------------------------------
   TAKVİM BİR TAKVİM DEĞİL, BİR PENCERE HARİTASIDIR ve bunu ekranda yazmak zorunda:
   işaretsiz bir gün "o gün koşmadı" DEMEK DEĞİLDİR. İki kaynak da SINIRLI:
     · koşu defteri uçta son 40 satırda kırpılıyor (api.py::_hat_cizelgesi) → ~2-3 gece
     · `donguler` son 8 `daily_cycle` olayı ve o da bir OLAY PENCERESİNDEN süzülüyor
       (`obs.recent(3000)`, api.py::_hat_cizelgesi) — pencerenin dışı görünmez
   Bu yüzden takvim yalnız "bu pencerede kanıt gördüm" der. Boş bir hücreye
   "koşmadı" hükmü basmak, penceresi 3 gün olan bir ölçümü tarihin tamamı gibi
   okumak olurdu — bu deponun tekrar eden kusur sınıfı.

   ŞABLONUN TAKVİM BİLEŞENİ KULLANILIYOR (`components/ui/calendar.tsx`,
   react-day-picker) ama SEÇİM MODU YOK: seçilecek bir şey yok, tıklama hiçbir yere
   gitmez. `mode` verilmediğinde bileşen salt-görüntü çalışır; sahte bir etkileşim
   sunmuyoruz.
   ============================================================================ */
import { useMemo } from "react";

import { CalendarClock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { Deger, HukumRozet, Olculemedi, zamanMetni } from "./parcalar";
import type { CizelgeDongusu, CizelgeKosusu, SonDongu } from "./tipler";

/** `YYYY-MM-DD` → yerel `Date` (gün başı). Ayrıştırılamazsa `null`. */
function gunDate(gun: string): Date | null {
  const p = gun.split("-");
  const y = Number(p[0]);
  const a = Number(p[1]);
  const g = Number(p[2]);
  if (!Number.isFinite(y) || !Number.isFinite(a) || !Number.isFinite(g)) return null;
  return new Date(y, a - 1, g);
}

/** ISO damgasının yerel gün anahtarı — takvim işaretleri gün bazında eşleşir. */
function isoGunu(iso: string | undefined): string | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  const d = new Date(t);
  return `${d.getFullYear()}-${`${d.getMonth() + 1}`.padStart(2, "0")}-${`${d.getDate()}`.padStart(2, "0")}`;
}

export function SeansTakvimi({
  kosular,
  donguler,
  sonDongu,
}: {
  readonly kosular: readonly CizelgeKosusu[] | undefined;
  readonly donguler: readonly CizelgeDongusu[] | undefined;
  readonly sonDongu: SonDongu | undefined;
}) {
  const { kosuGunleri, donguGunleri, sonGun } = useMemo(() => {
    const k = new Set<string>();
    for (const r of kosular ?? []) {
      const g = isoGunu(r.started);
      if (g) k.add(g);
    }
    const d = new Set<string>();
    for (const c of donguler ?? []) {
      // `date` SEANS TARİHİDİR (zaten `YYYY-MM-DD`); `ts` olayın yazılma anıdır. Seans
      // tarihi varsa O kullanılır — gece 00:30'da yazılan bir olayın günü, seansın günü değildir.
      const g = c.date ?? isoGunu(c.ts);
      if (g) d.add(g);
    }
    const s = sonDongu?.date ?? isoGunu(sonDongu?.ts) ?? null;
    if (s) d.add(s);
    return { kosuGunleri: k, donguGunleri: d, sonGun: s };
  }, [kosular, donguler, sonDongu]);

  const kosuTarihleri = useMemo(
    () => [...kosuGunleri].map(gunDate).filter((d): d is Date => d !== null),
    [kosuGunleri],
  );
  const donguTarihleri = useMemo(
    () => [...donguGunleri].map(gunDate).filter((d): d is Date => d !== null),
    [donguGunleri],
  );
  // TAKVİM SON KANITIN AYINDA AÇILIR, BUGÜNÜN AYINDA DEĞİL: pencere 2-3 gecelik ve
  // canlı sistemde son koşu geçmiş bir ayda olabilir. Bugünü göstermek, işaretlerin
  // hiçbirinin görünmediği boş bir ay açmak olurdu.
  const acilisAyi = useMemo(() => {
    const hepsi = [...donguTarihleri, ...kosuTarihleri];
    if (hepsi.length === 0) return undefined;
    return hepsi.reduce((en, d) => (d > en ? d : en), hepsi[0] as Date);
  }, [donguTarihleri, kosuTarihleri]);

  const satirlar = useMemo(() => [...(donguler ?? [])], [donguler]);

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
      <div className="shrink-0">
        {kosuTarihleri.length === 0 && donguTarihleri.length === 0 ? (
          <Olculemedi neden="Kayıtlarda okunabilir bir gün damgası yok — takvim çizilmedi" teknik="ne koşu defterinde ne döngü olaylarında ayrıştırılabilir bir gün damgası var" />
        ) : (
          <>
            <Calendar
              mode={undefined}
              defaultMonth={acilisAyi}
              showOutsideDays={false}
              modifiers={{ kosu: kosuTarihleri, dongu: donguTarihleri }}
              // İŞARETLER KATMAN DEĞİL KENAR/ZEMİN: gün hücresinin İÇİNDE bir düğme
              // (`CalendarDayButton`) var ve o düğme kendi zeminini çizebiliyor. Nokta
              // biçimli bir işaret düğmenin ARKASINDA kalabilirdi; halka ve hücre zemini
              // yığılma sırasından bağımsız görünür.
              modifiersClassNames={{
                kosu: "rounded-(--cell-radius) ring-1 ring-primary/60 ring-inset",
                dongu: "rounded-(--cell-radius) bg-emerald-500/15 font-medium text-emerald-700 dark:text-emerald-300",
              }}
              className="rounded-lg border"
            />
            <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm bg-emerald-500/40" /> gece döngüsü kaydı var
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm ring-1 ring-primary/60 ring-inset" /> hat koşusu kaydı var
              </span>
            </div>
          </>
        )}
        <p className="mt-2 max-w-[18rem] text-muted-foreground text-[11px] leading-4">
          İşaretsiz gün <strong>&quot;koşmadı&quot; demek değildir</strong>: koşu defteri son 40
          satırda, döngü olayları son 8 kayıtta kırpık. Takvim yalnız bu pencerede görülen kanıtı
          gösterir.
        </p>
      </div>

      <div className="min-w-0 flex-1">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <CalendarClock className="size-4 text-muted-foreground" aria-hidden />
          <h4 className="font-medium text-sm">Gece döngüleri (pencerede görülen)</h4>
          {sonGun ? <Badge variant="outline">çıpa: {sonGun}</Badge> : null}
        </div>

        {sonDongu !== undefined && sonDongu.var === false ? (
          <p className="mb-3 rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-sm leading-6">
            {sonDongu.neden ?? "son döngü kaydı ölçülemedi"}
          </p>
        ) : null}

        <div className="min-w-0 overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow>
                <TableHead className="whitespace-nowrap">Seans</TableHead>
                <TableHead className="whitespace-nowrap">Yazıldı</TableHead>
                <TableHead className="whitespace-nowrap">Rejim</TableHead>
                <TableHead className="whitespace-nowrap">Aday</TableHead>
                <TableHead className="whitespace-nowrap">Plan</TableHead>
                <TableHead className="whitespace-nowrap">İşleme hazır</TableHead>
                <TableHead className="whitespace-nowrap">Açık poz.</TableHead>
                <TableHead className="whitespace-nowrap">Veri / HALT</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {satirlar.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center">
                    <span className="text-muted-foreground text-sm">
                      Bu olay penceresinde <code className="font-mono text-xs">daily_cycle</code> satırı
                      görülmedi. Döngünün hiç koşmadığı anlamına GELMEZ — pencere sınırlı
                      (çıpa ayrı ölçülüyor, üstteki karta bak).
                    </span>
                  </TableCell>
                </TableRow>
              ) : (
                satirlar.map((c, i) => (
                  <TableRow key={`${c.date ?? c.ts ?? "?"}#${i}`}>
                    <TableCell className="whitespace-nowrap text-xs tabular-nums">
                      {c.date ?? <Olculemedi neden="Seans tarihi kaydedilmemiş" teknik="olay `date` taşımıyor" kisa />}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-xs tabular-nums">
                      {zamanMetni(c.ts) ?? <Olculemedi neden="Yazılma zamanı kaydedilmemiş" teknik="olay `ts` taşımıyor" kisa />}
                    </TableCell>
                    <TableCell className="text-xs">
                      {c.regime ?? <Olculemedi neden="Piyasa rejimi kaydedilmemiş" teknik="olay `regime` taşımıyor" kisa />}
                    </TableCell>
                    <TableCell>
                      <Deger deger={c.candidates} neden="Aday sayısı kaydedilmemiş" teknik="`candidates` yazılmamış" />
                    </TableCell>
                    <TableCell>
                      <Deger deger={c.plans} neden="Plan sayısı kaydedilmemiş" teknik="`plans` yazılmamış" />
                    </TableCell>
                    <TableCell>
                      <Deger deger={c.armed} neden="İşleme hazır plan sayısı kaydedilmemiş" teknik="`armed` yazılmamış" />
                    </TableCell>
                    <TableCell>
                      <Deger deger={c.open_positions} neden="Açık pozisyon sayısı kaydedilmemiş" teknik="`open_positions` yazılmamış" />
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        <HukumRozet
                          ton={c.data_ok === undefined ? "olculemedi" : c.data_ok ? "iyi" : "kotu"}
                          metin={c.data_ok === undefined ? "veri?" : c.data_ok ? "veri ok" : "VERİ BOZUK"}
                          baslik="`data_ok` — o döngünün veri sağlığı beyanı"
                        />
                        <HukumRozet
                          ton={c.halted === undefined ? "olculemedi" : c.halted ? "uyari" : "notr"}
                          metin={c.halted === undefined ? "HALT?" : c.halted ? "HALT çekili" : "serbest"}
                          baslik="`halted` — o döngüde durdurma kolu çekili miydi"
                        />
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
