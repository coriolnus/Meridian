"use client";

/* ============================================================================
   İZİN MATRİSİ — hangi SEVİYE neyi yapabiliyor
   ----------------------------------------------------------------------------
   ŞABLONUN "permission sets" TABLOSUNUN GRAMERİ, MERİDİAN'IN GERÇEK YETKİ EKSENİ.
   Bu depoda "rol" diye bir kavram YOK; yetki tek bir sayıyla ifade ediliyor:
   `state/goal.yaml → limits.autonomy_level`. O sayı bir KİŞİYE değil SİSTEME ait,
   ve üç değeri var (L0/L1/L2 — analytics.py::autonomy_ladder).

   HER HÜCRE BİR KAYNAK SATIRI TAŞIR. Bir yetki matrisinde "muhtemelen şöyledir"
   diye doldurulmuş bir hücre, olmayan bir kısıtı var (ya da var olan bir kısıtı
   yok) göstermek demektir; bu ekranda o hata gerçek parayı ilgilendirir. Bu
   yüzden satırlar kaynak taramasıyla ölçüldü ve `kaynak` kolonu ekranda duruyor.

   MATRİS UÇTAN GELMİYOR — kaynak taramasıdır (2026-08-25). Uçtan gelen tek şey
   ETKİN SEVİYEDİR (`/api/summary.ladder.current_level`) ve o sütun vurgulanıyor.
   Bu ayrımı gizlemek, elle yazılmış bir tabloyu canlı ölçüm gibi göstermek olurdu.
   ============================================================================ */
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { type IzinDegeri, IzinHucresi } from "./parcalar";

interface Hucre {
  readonly deger: IzinDegeri;
  readonly not: string;
}

interface YetkiSatiri {
  readonly kimlik: string;
  readonly yetki: string;
  readonly l0: Hucre;
  readonly l1: Hucre;
  readonly l2: Hucre;
  readonly kaynak: string;
}

/** Ölçülmüş yetki satırları. L1/L2 hücrelerinin bir kısmı SEVİYE ADINDAN okunur
 *  (`analytics.autonomy_ladder` levels[].name) — bugün canlı sistem L0'da olduğu
 *  için o iki seviyenin davranışı ÇALIŞIRKEN gözlenmedi ve hücre notu bunu söylüyor. */
const SATIRLAR: readonly YetkiSatiri[] = [
  {
    kimlik: "gercek-para",
    yetki: "Gerçek para ile emir",
    l0: { deger: "yok", not: "canlı mod istense bile REDDEDİLİR — guard: `autonomy_level<1`" },
    l1: { deger: "kosullu", not: "seviye adı: “Live, every order approved” — her emir onaydan geçer" },
    l2: { deger: "var", not: "seviye adı: “Live, autonomous”" },
    kaynak: "guard.py::check_trade · analytics.py::autonomy_ladder",
  },
  {
    kimlik: "onay-defteri",
    yetki: "Onay defterine karar yazma (`POST /api/approvals/{id}`)",
    l0: { deger: "kosullu", not: "403 `approvals are L1+ only`. İSTİSNA: kapıya BAĞLANMAYAN kimlikler yazılabilir" },
    l1: { deger: "var", not: "karar deftere düşer ve uygulama kapısını açar" },
    l2: { deger: "var", not: "aynı defter; kapı L1'deki gibi bağlar" },
    kaynak: "api.py::_onay_bekleyen_damgala",
  },
  {
    kimlik: "onay-kapisi",
    yetki: "Skill revizyonu/önerisi uygulaması onay ARAR mı",
    l0: { deger: "yok", not: "kapı NÖTR: deftere hiç bakmaz, `gecti=True` döner — davranış birebir eski hâl" },
    l1: { deger: "var", not: "`approve` satırı yoksa uygulama yapılmaz (fail-closed)" },
    l2: { deger: "var", not: "aynı kapı; onay kimliğe bağlı, öneri örneğine değil" },
    kaynak: "api.py::_onay_kapisi",
  },
  {
    kimlik: "pending-defteri",
    yetki: "`/api/approvals.pending` defterinin görünmesi",
    l0: { deger: "yok", not: "HER ZAMAN boş dizi — “defter boş” anlamına GELMEZ, defter hiç okunmaz" },
    l1: { deger: "var", not: "`approvals.jsonl` satırları listelenir" },
    l2: { deger: "var", not: "aynı defter" },
    kaynak: "api.py::api_approvals",
  },
  {
    kimlik: "canli-import",
    yetki: "Canlı icra yolunun yüklenebilmesi",
    l0: { deger: "kosullu", not: "SEVİYEDEN BAĞIMSIZ: elle kurulan iki ortam bayrağına bağlı" },
    l1: { deger: "kosullu", not: "aynı iki bayrak; seviye tek başına yetmez" },
    l2: { deger: "kosullu", not: "aynı iki bayrak; seviye tek başına yetmez" },
    kaynak: "config.py::live_enabled — `MERIDIAN_MODE=live` + `MERIDIAN_I_ACCEPT_RISK=true`",
  },
];

const SEVIYELER = [
  { no: 0, id: "L0", alan: "l0" },
  { no: 1, id: "L1", alan: "l1" },
  { no: 2, id: "L2", alan: "l2" },
] as const;

export function IzinMatrisi({ etkinSeviye }: { readonly etkinSeviye: number | null }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="min-w-0 overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow>
              <TableHead className="min-w-56 font-normal">Yetki</TableHead>
              {SEVIYELER.map((s) => (
                <TableHead
                  key={s.id}
                  className={cn("min-w-52 font-normal", etkinSeviye === s.no && "bg-primary/5 text-foreground")}
                >
                  <span className="inline-flex items-center gap-2">
                    <span className="font-mono">{s.id}</span>
                    {etkinSeviye === s.no ? (
                      <Badge variant="outline" className="text-[10px]">
                        etkin
                      </Badge>
                    ) : null}
                  </span>
                </TableHead>
              ))}
              <TableHead className="min-w-56 font-normal">Kaynak</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {SATIRLAR.map((satir) => (
              <TableRow key={satir.kimlik} className="border-border/50">
                <TableCell className="py-3 align-top font-medium text-sm leading-5">{satir.yetki}</TableCell>
                {SEVIYELER.map((s) => {
                  const h = satir[s.alan];
                  return (
                    <TableCell
                      key={s.id}
                      className={cn("py-3 align-top", etkinSeviye === s.no && "bg-primary/5")}
                    >
                      <IzinHucresi deger={h.deger} not={h.not} />
                    </TableCell>
                  );
                })}
                <TableCell className="py-3 align-top">
                  <code className="break-all font-mono text-[11px] text-muted-foreground leading-4">
                    {satir.kaynak}
                  </code>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <p className="text-muted-foreground text-xs leading-5">
        KAYNAK BEYANI: matrisin {SATIRLAR.length} satırı 2026-08-25'te KAYNAK TARAMASIYLA ölçüldü, bir
        uçtan gelmiyor — kod değişirse elle güncellenir. Uçtan gelen tek şey vurgulanan{" "}
        {etkinSeviye === null ? "sütun (etkin seviye ÖLÇÜLEMEDİ)" : `sütun (L${etkinSeviye} etkin)`}.
        L1 ve L2 hücreleri sistemin ÇALIŞIRKEN gözlenmiş davranışı değildir; canlı sistem L0'dadır ve
        o iki sütun kodun yazdığını söyler, olanı değil.
      </p>
    </div>
  );
}
