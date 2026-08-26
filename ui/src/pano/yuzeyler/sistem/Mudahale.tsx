"use client";

/* ============================================================================
   MÜDAHALE KOLLARI — DURUM, TETİKLEME DEĞİL
   ----------------------------------------------------------------------------
   BU BÖLÜM HİÇBİR KOLU ÇEKMEZ ve bu bir eksiklik değil bir karardır: kollar
   `POST /api/halt`, `/api/control/learn_halt`, `/api/control/cancel_open`,
   `/api/alpaca/close_all` uçlarına bağlı ve hepsi CANLI sisteme yazar. Bir OKUMA
   yüzeyinin içine yazma düğmesi koymak, yanlış tıklamayla canlı ticareti durdurmak
   demektir. Burada yalnız "hangi kol nerede duruyor" yazar.

   ~~çekme yetkisi kendi turunda, onay adımıyla gelir~~ — O TUR GELDİ (2026-08-25):
   kollar `kabuk/KrizKollari.tsx`te, ÜST BARDA ve çift adımlı. Yeri burası DEĞİL ve
   sebebi değişmedi: üst bar SABİT bir evdir (kas hafızası; sayfa değişince yerinden
   oynamaz), bu bölüm ise bir yüzeyin içinde kayan bir karttır. Acil bir anda kolun
   nerede olduğunu aramak, kolun kendisinden pahalıdır.
   Bu kart hâlâ DURUMU okur — ikisi çelişmez: burada "hangi kol çekili", üst barda
   "çek/bırak". Şerh silinmedi çünkü gerekçesi hâlâ doğru; yalnız artık nerede
   olduğunu da söylüyor.

   RENK SÖZLEŞMESİ: çekili kol AMBER, kırmızı DEĞİL. Kırmızı "arıza" der; HALT bir
   arıza değil bir KARARDIR. Kırmızı yalnız ölçülemeyen/bozuk bileşene ayrıldı.

   EYLEMSİZLİĞİN ADI (`risk.eylemsizlik`): "bugün neden hiçbir şey olmadı"nın
   cevabı. Uç dört zorlayıcı nedeni SIRALI arar (HALT → bütçe 0 → seans ertelendi →
   kazanç karartması); ilki "birincil"dir. Hiçbiri yoksa uç bunu da söylüyor ve
   sebebi kapı kararlarına havale ediyor — biz o cümleyi aynen basıyoruz, kendi
   yorumumuzu eklemiyoruz.
   ============================================================================ */
import { Radar } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { BugunGovdesi } from "../../tipler";
import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, KolRozet, Olculemedi, Satir } from "./parcalar";
import type { TeshisGovdesi } from "./uctipleri";

interface Kol {
  readonly ad: string;
  readonly cekili: boolean | null | undefined;
  readonly cekiliMetin: string;
  readonly serbestMetin: string;
  readonly kaynak: string;
  readonly aciklama: string;
}

export function Mudahale({
  teshis,
  bugun,
}: {
  readonly teshis: Durum<TeshisGovdesi>;
  readonly bugun: Durum<BugunGovdesi>;
}) {
  return (
    <BolumKart
      kimlik="mudahale"
      baslik="Müdahale kolları"
      soru="Hangi durdurma kolu çekili?"
      ikon={Radar}
      aksiyon={
        <Badge variant="outline" title="Bu bölüm yalnız OKUR. Kolları çekmek üst bardaki KRİZ düğmesinde — orada, çift adımlı onayla.">
          salt okunur · kollar üst barda
        </Badge>
      }
    >
      <Kapi durum={teshis} yol="/api/diagnostics">
        {(d) => {
          const hud = d.hud ?? {};
          const risk = d.risk ?? {};
          const ey = risk.eylemsizlik;
          const intra = d.intraday;

          const kollar: readonly Kol[] = [
            {
              ad: "HALT — ticaret durdurma",
              // İKİ KAYNAK BİLEREK ÇAPRAZLANIYOR: `/api/today.halted` ile
              // `/api/diagnostics.hud.halted` aynı `health.halted()`u okur ama teşhis
              // 45 sn önbelleklidir. Çelişki OLURSA görünsün diye ikisi de aşağıda yazılı.
              cekili: risk.halted ?? hud.halted,
              cekiliMetin: "ÇEKİLİ — yeni risk alınmaz",
              serbestMetin: "serbest",
              kaynak: "health.halted() · /api/diagnostics risk.halted",
              aciklama: "Yeni pozisyon açılmaz. Açık pozisyonların yönetimi devam eder.",
            },
            {
              ad: "Öğrenme HALT",
              cekili: risk.learn_halted ?? hud.learn_halted,
              cekiliMetin: "ÇEKİLİ — değerlendirme/terfi durdu",
              serbestMetin: "serbest",
              kaynak: "health.learn_halted() · /api/diagnostics risk.learn_halted",
              aciklama: "Hipotez üretimi ve sürüm terfisi durur; ticaret etkilenmez.",
            },
            {
              ad: "Seans içi işleme hazırlık (Faz-4)",
              cekili: intra?.armed,
              cekiliMetin: "SİLAHLI — gün içi emir gidebilir",
              serbestMetin: "gözlem modu",
              kaynak: "/api/diagnostics intraday.armed · POST /api/intraday-arm",
              aciklama: "İşleme hazırken intraday karar hattı gerçek emir gönderebilir.",
            },
            {
              ad: "Keşif modu (explore)",
              cekili: hud.explore_mode,
              cekiliMetin: "AÇIK — keşif planları üretilir",
              serbestMetin: "kapalı",
              kaynak: "/api/diagnostics hud.explore_mode",
              aciklama: "Bir durdurma kolu DEĞİL; risk profilini genişleten bir anahtar.",
            },
          ];

          return (
            <>
              <div className="overflow-x-auto">
                <Table className="min-w-[52rem]">
                  <TableHeader className="bg-muted/50">
                    <TableRow>
                      <TableHead>Kol</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Ne yapar</TableHead>
                      <TableHead>Kaynak</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {kollar.map((k) => (
                      <TableRow key={k.ad}>
                        <TableCell className="font-medium">{k.ad}</TableCell>
                        <TableCell>
                          <KolRozet cekili={k.cekili} cekiliMetin={k.cekiliMetin} serbestMetin={k.serbestMetin} />
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{k.aciklama}</TableCell>
                        <TableCell className="font-mono text-[11px] text-muted-foreground">{k.kaynak}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="Maruziyet bütçesi">
                    <Deger
                      deger={hud.exposure_budget_pct}
                      birim="%"
                      basamak={1}
                      neden="Maruziyet bütçesi bildirilmedi"
                      teknik="/api/diagnostics hud.exposure_budget_pct döndürmedi"
                    />
                  </Satir>
                  <Satir etiket="Rejim">
                    {hud.regime ?? <Olculemedi neden="Piyasa rejimi bildirilmedi" teknik="hud.regime yok — regime.json boş olabilir" kisa />}
                  </Satir>
                  <Satir etiket="Mod / broker">
                    {hud.mode ?? "?"} · {hud.broker ?? "?"}
                  </Satir>
                </div>
                <div>
                  <Satir etiket="/api/today HALT (çapraz kontrol)">
                    <KolRozet cekili={bugun.veri?.halted} cekiliMetin="ÇEKİLİ" serbestMetin="serbest" />
                  </Satir>
                  <Satir etiket="Özerklik düzeyi">
                    {bugun.veri?.autonomy_level ?? (
                      <Olculemedi
                        neden="Özerklik düzeyi bildirilmedi"
                        teknik="/api/today autonomy_level döndürmedi"
                        kisa
                      />
                    )}
                  </Satir>
                  <Satir etiket="Veri sağlığı (data_ok)">
                    {hud.data_ok === undefined || hud.data_ok === null ? (
                      <Olculemedi neden="Veri sağlığı bildirilmedi" teknik="nabız `data_ok` alanını taşımıyor" kisa />
                    ) : (
                      <KolRozet cekili={!hud.data_ok} cekiliMetin="veri BOZUK" serbestMetin="veri temiz" />
                    )}
                  </Satir>
                </div>
              </div>

              {ey === undefined ? (
                <Olculemedi
                  neden="Bugün neden işlem yapılmadığı bildirilmedi"
                  teknik="/api/diagnostics risk.eylemsizlik bloğunu döndürmedi"
                />
              ) : ey.birincil ? (
                <Alert>
                  <AlertTitle>Eylemsizliğin birincil nedeni: {ey.birincil.ad ?? "?"}</AlertTitle>
                  <AlertDescription>
                    {ey.birincil.aciklama ?? ""}
                    {ey.birincil.kanit ? (
                      <span className="mt-1 block font-mono text-[11px] text-muted-foreground">
                        kanıt: {ey.birincil.kanit}
                      </span>
                    ) : null}
                    {(ey.nedenler?.length ?? 0) > 1 ? (
                      <span className="mt-1 block text-xs">
                        Ayrıca {(ey.nedenler?.length ?? 1) - 1} neden daha ölçüldü:{" "}
                        {(ey.nedenler ?? [])
                          .slice(1)
                          .map((n) => n.ad ?? "?")
                          .join(" · ")}
                      </span>
                    ) : null}
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert>
                  <AlertTitle>Zorlayıcı bir durdurma nedeni ölçülmedi</AlertTitle>
                  <AlertDescription>
                    {ey.neden_yok_aciklama ??
                      "Uç `neden_yok_aciklama` döndürmedi — nedenin yokluğu da açıklanmadı."}
                    <span className="mt-1 block text-muted-foreground text-xs tabular-nums">
                      taranan olay penceresi: {ey.olay_penceresi ?? "?"} kayıt
                    </span>
                  </AlertDescription>
                </Alert>
              )}
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
