"use client";

/* ============================================================================
   DURUM SÖZLÜĞÜ — `/api/diagnostics.durum_sozlugu` (TSK-070 A2/A8, tasarım §9.2)
   ----------------------------------------------------------------------------
   NİYE VAR: bu sistemde bir mekanizmanın "iyi" olduğunu söyleyen ONLARCA alan var
   ve hepsi kendi kelimesini konuşuyordu — bekçi raporu başka, kadans nabzı başka,
   kilit kolu bambaşka. Aynı gerçek için üç kelime, üç okuyucu demektir ve üçü
   birbirini yanlış anlar. Kanonik sözlük (`meridian/durum_sozlugu.py`) bu yüzden
   var; bu yüzey onun PANODAKİ tek okuyucusudur (Yasa 6: okunmayan artefakt
   üretilmemişten farksızdır — sözlük 2026-08-23'ten 2026-09-15'e kadar yalnız eski
   `app.js`te okunuyordu, yani operatörün varsayılan ekranında HİÇ yoktu).

   KELİME BURADA ÜRETİLMEZ, YALNIZ BASILIR. Panoda ikinci bir çeviri tablosu YOK ve
   olmayacak: üretici kodu (`watchdog` rapor kovası, kitap damga sınıfı, hermes
   atlama kodu…) → kelime dönüşümü BACKEND'in işidir (`PANO_KELIME`, tek kaynak).
   Bugün eski `app.js` tam da bu çeviriyi satır içinde yapıyor ve yeni yüzeyin varlık
   sebeplerinden biri o tekrarı YAPMAMAKTIR — iki sözlük sessizce ayrışır ve ayrışma
   ancak yanlış bir teşhisle fark edilir. Çivi: `tests/test_pano_durum_sozlugu_v504.py`.

   AİLE ADI DA ÇEVRİLMEZ: grup başlığı uçtan gelen ham aile kimliğini basar (kadans ·
   dedektor · canlilik · bekci · kitap · kilit · mandal · hermes · intraday). Türkçe
   bir etiket sözlüğü yazmak, yukarıdaki kuralı kelimede tutup ailede delmek olurdu.
   Sıra (`AILE_SIRA`) bir SUNUM kararıdır, bir sözlük değil: triyaj yukarıdan aşağı
   okunur (önce kadans nabzı, sonra dedektörler, sonra canlılık…). Sırada OLMAYAN bir
   aile DÜŞMEZ, sona eklenir ve ekranda "sıra bayat" diye söylenir — backend yeni bir
   aile doğurduğunda pano onu sessizce yutarsa körlük sessiz olur (bedel yasası).

   SAYI SÜTUNUNUN ÜÇ HÂLİ ve aralarındaki fark bu ailenin bütün değeri:
     · sayı        — ölçüldü (`0` GERÇEKTEN sıfırdır)
     · ÖLÇÜLEMEDİ  — `n: null` + satır `olculemedi`: sayı ölçülemedi, 0 DEĞİL
     · boş hücre   — satır sayı TAŞIMAZ (bir kadans mekanizmasının sayacı yoktur)
   BEYANLI BEDEL: `olculemedi` satırların bir kısmı sayı değil bir BAYRAK ölçemedi
   (kilit kolu gibi) ve sütun onlarda da "ÖLÇÜLEMEDİ (0 DEĞİL)" basar. Alternatif,
   panoda "hangi aile sayı taşır" diye İKİNCİ bir tablo tutmaktı — tam da kaçındığımız
   sınıf. Satırın kelimesi zaten ÖLÇÜLEMEDİ olduğu için ekran yanlış bir şey demiyor.

   KENDİ İSTEĞİNİ AÇMAZ: `/api/diagnostics` bu yüzeyde TEK yerde okunur
   (`SistemSagligiYuzey.tsx` şerhi) ve gövde prop olarak iner — ikinci bir anket aynı
   ekranda iki farklı ANI gösterirdi.
   ============================================================================ */
import { ScrollText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Durum } from "../../veri";
import { BolumKart, Deger, Kapi, Olculemedi, Satir, zamanMetni } from "./parcalar";
import type { DurumSozluguSatiri, TeshisGovdesi } from "./uctipleri";

/** Triyaj sırası (tasarım §9.2). Sunum kararı — sözlük DEĞİL; eksik aile sona düşer. */
const AILE_SIRA: readonly string[] = [
  "kadans",
  "dedektor",
  "canlilik",
  "bekci",
  "kitap",
  "kilit",
  "mandal",
  "hermes",
  "intraday",
];

/** Kanonik kelimenin rozeti. RENK BİR HÜKÜMDÜR ve hükmü `ok` verir:
 *  true → nötr (sağlıklı hâl ekranı boyamaz), false → şiddet, null → bilgi
 *  (ölçülemedi/askıda/kapsam dışı "bozuk" DEĞİLDİR). Renkler jetonlardan gelir. */
function KelimeRozeti({ satir }: { readonly satir: DurumSozluguSatiri }) {
  if (satir.kelime === undefined) {
    return <Olculemedi neden="Satır kanonik kelime taşımıyor" teknik="`kelime` alanı gelmedi" kisa />;
  }
  if (satir.ok === true) return <Badge variant="secondary">{satir.kelime}</Badge>;
  if (satir.ok === false) return <Badge variant="destructive">{satir.kelime}</Badge>;
  return (
    <Badge variant="outline" className="border-bilgi-h bg-bilgi-t text-bilgi">
      {satir.kelime}
    </Badge>
  );
}

/** Satırın sayısı — üç hâl (dosya başlığındaki şerh). */
function SatirSayisi({ satir }: { readonly satir: DurumSozluguSatiri }) {
  if (typeof satir.n === "number" && Number.isFinite(satir.n)) {
    return <span className="tabular-nums">{satir.n.toLocaleString("tr-TR")}</span>;
  }
  if (satir.olculemedi) {
    return <Olculemedi neden="ÖLÇÜLEMEDİ (0 DEĞİL)" teknik="satır `n: null` ve `olculemedi` dolu" kisa />;
  }
  return null;
}

function AileGrubu({
  aile,
  satirlar,
  kayitliN,
  sirada,
}: {
  readonly aile: string;
  readonly satirlar: readonly DurumSozluguSatiri[];
  readonly kayitliN: number | undefined;
  readonly sirada: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-baseline gap-2">
        <h3 className="font-mono font-semibold text-sm">{aile}</h3>
        {/* SAYI UÇTAN OKUNUR (`aileler`), PANODA SAYILMAZ: iki sayım ayrışırsa hangisinin
            doğru olduğu sorulamaz. Ayrışmayı gizlemiyoruz da — aşağıdaki şerit söyler. */}
        <span className="text-muted-foreground text-xs">
          <Deger deger={kayitliN} birim=" satır" neden="Uç bu ailenin sayısını vermedi" teknik="`aileler` bu aileyi taşımıyor" />
        </span>
        {kayitliN !== undefined && kayitliN !== satirlar.length ? (
          <span className="text-uyari text-xs">
            uç sayımı ({kayitliN}) ile basılan satır ({satirlar.length}) AYRIŞTI
          </span>
        ) : null}
        {sirada ? null : (
          <span className="text-uyari text-xs">
            panonun aile sırasında YOK — sona eklendi (sıra bayat, tasarım §9.2)
          </span>
        )}
      </div>
      <div className="overflow-x-auto">
        <Table className="min-w-[48rem]">
          <TableHeader className="bg-muted/50">
            <TableRow>
              <TableHead className="w-[12rem]">Durum</TableHead>
              <TableHead>Mekanizma</TableHead>
              <TableHead className="text-right">Sayı</TableHead>
              <TableHead>Ne diyor</TableHead>
              <TableHead>Okunan alan</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {satirlar.map((s, i) => (
              <TableRow key={`${aile}-${s.kimlik ?? "?"}-${i}`}>
                <TableCell>
                  <KelimeRozeti satir={s} />
                </TableCell>
                <TableCell className="font-medium font-mono text-xs">
                  {s.kimlik ?? <Olculemedi neden="Satır kimliksiz geldi" teknik="`kimlik` alanı yok" kisa />}
                </TableCell>
                <TableCell className="text-right">
                  <SatirSayisi satir={s} />
                </TableCell>
                <TableCell className="max-w-[24rem] text-xs">
                  {s.beyan ? <span>{s.beyan}</span> : null}
                  {s.neden ? <span className="text-muted-foreground"> · {s.neden}</span> : null}
                  {!s.beyan && !s.neden ? (
                    <Olculemedi neden="Satır gerekçe taşımıyor" teknik="`beyan` ve `neden` boş" kisa />
                  ) : null}
                </TableCell>
                <TableCell className="whitespace-nowrap font-mono text-muted-foreground text-xs">
                  {s.kaynak_alan ? s.kaynak_alan : <Olculemedi neden="Hükmün okunduğu alan bildirilmedi" teknik="`kaynak_alan` boş" kisa />}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

export function DurumSozlugu({ teshis }: { readonly teshis: Durum<TeshisGovdesi> }) {
  return (
    <BolumKart
      kimlik="durum-sozlugu"
      baslik="Durum sözlüğü"
      soru="Her mekanizma tek dilde ne diyor?"
      ikon={ScrollText}
    >
      <Kapi durum={teshis} yol="/api/diagnostics">
        {(d) => {
          const s = d.durum_sozlugu;
          if (s === undefined) {
            return (
              <p className="text-sm">
                <Olculemedi
                  neden="Kanonik durum sözlüğü ölçülemedi"
                  teknik="/api/diagnostics `durum_sozlugu` alanını döndürmedi — satır YOK demek DEĞİL"
                />
              </p>
            );
          }

          const satirlar = s.satirlar;
          if (satirlar === undefined) {
            return (
              <p className="text-sm">
                <Olculemedi
                  neden="Sözlük satırları ölçülemedi"
                  teknik="`durum_sozlugu` geldi ama `satirlar` alanı yok"
                />
              </p>
            );
          }

          // GRUPLAMA PANODA, HÜKÜM UÇTA: satırlar aileye göre yalnız TOPLANIR, hiçbir
          // alan yeniden hesaplanmaz (sentez yasağı, tasarım §9.2).
          const gruplar = new Map<string, DurumSozluguSatiri[]>();
          for (const r of satirlar) {
            const aile = r.aile ?? "(aile bildirilmedi)";
            const mevcut = gruplar.get(aile);
            if (mevcut) mevcut.push(r);
            else gruplar.set(aile, [r]);
          }
          const sirali = [
            ...AILE_SIRA.filter((a) => gruplar.has(a)),
            ...[...gruplar.keys()].filter((a) => !AILE_SIRA.includes(a)),
          ];
          const sayaclar = Object.entries(s.esanlamli_okumalar ?? {}).sort((a, b) => b[1] - a[1]);

          return (
            <>
              <div className="grid gap-x-6 sm:grid-cols-2">
                <div>
                  <Satir etiket="Basılan satır">
                    <span className="tabular-nums">{satirlar.length}</span>
                  </Satir>
                  <Satir etiket="Aile">
                    <span className="tabular-nums">{sirali.length}</span>
                  </Satir>
                  <Satir etiket="Sayaç rejimi">
                    {s.sayac_rejimi ?? (
                      <Olculemedi neden="Sayaç rejimi bildirilmedi" teknik="`sayac_rejimi` alanı yok" kisa />
                    )}
                  </Satir>
                </div>
                <div>
                  {/* PENCERE OLMADAN "0" HÜKÜM TAŞIMAZ: bir saatlik sıfır ile otuz günlük
                      sıfır aynı şey değildir — eski adın okuyucusu ancak pencereyle ölür. */}
                  <Satir etiket="Sayaç penceresi (ilk kayıt)">
                    {zamanMetni(s.pencere?.ilk_kayit_utc) ?? (
                      <Olculemedi neden="Defterde hiç kayıt yok — ölçüm HENÜZ başlamamış" teknik="`pencere.ilk_kayit_utc` boş" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Son kayıt">
                    {zamanMetni(s.pencere?.son_kayit_utc) ?? (
                      <Olculemedi neden="Son kayıt damgası yok" teknik="`pencere.son_kayit_utc` boş" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Pencere">
                    <Deger
                      deger={s.pencere?.gun}
                      birim=" gün"
                      neden="Pencere günü ölçülemedi (damga yok/çözülemedi) — 0 DEĞİL"
                      teknik="`pencere.gun` null"
                    />
                  </Satir>
                </div>
              </div>

              {satirlar.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  Uç sözlüğü döndürdü ama HİÇ satır taşımıyor. Bu "her şey yolunda" DEĞİL: aile
                  adaptörleri hiçbir gövde okuyamamış olabilir (teşhis dilimi boş gelmiştir).
                </p>
              ) : (
                <div className="flex flex-col gap-6">
                  {sirali.map((aile) => (
                    <AileGrubu
                      key={aile}
                      aile={aile}
                      satirlar={gruplar.get(aile) ?? []}
                      kayitliN={s.aileler?.[aile]}
                      sirada={AILE_SIRA.includes(aile)}
                    />
                  ))}
                </div>
              )}

              {/* GEÇİŞ REJİMİNİN SAYACI — eski adların okunma sayısı. Sıfır bir başarıdır
                  AMA yalnız yukarıdaki pencereyle birlikte okunur. */}
              <div className="flex flex-col gap-2">
                <h3 className="font-semibold text-sm">Eşanlamlı okuma sayaçları</h3>
                {s.esanlamli_okumalar === undefined ? (
                  <Olculemedi
                    neden="Eşanlamlı okuma sayaçları ölçülemedi"
                    teknik="`esanlamli_okumalar` alanı gelmedi — 'hiç okunmadı' DEĞİL"
                  />
                ) : sayaclar.length === 0 ? (
                  <p className="text-muted-foreground text-sm">
                    Defter boş: pencerede hiçbir eski ad okunmadı (defter hiç yazılmamışsa ölçüm
                    HENÜZ başlamamıştır — yukarıdaki pencere hangisi olduğunu söyler).
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {sayaclar.map(([ad, n]) => (
                      <Badge key={ad} variant="outline" className="gap-1.5 font-mono text-xs">
                        {ad}
                        <span className="tabular-nums">{n}</span>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <p className="text-muted-foreground text-xs">
                {s.beyan ?? "Geçiş rejimi beyanı uçtan gelmedi (`beyan` alanı yok)."}
              </p>
            </>
          );
        }}
      </Kapi>
    </BolumKart>
  );
}
