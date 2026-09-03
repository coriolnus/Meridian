"use client";

/* ============================================================================
   SEANS İÇİ EMİR — SALT OKUMA. Bu bölüm hiçbir kolu ÇEKMEZ.
   ----------------------------------------------------------------------------
   `POST /api/intraday-arm` gerçek bir kapıdır: `state/INTRADAY_ARM` bayrağını
   açar ve otonom seans-içi emrin kapısını kaldırır (`api.py::api_intraday_arm`).
   Bu tur o kolu EKRANA KOYMAZ — geri alınamaz eylem tetiklemek turun kapsamı
   dışında.

   BAYRAK NEREDEN OKUNUYOR: `/api/intraday-arm` yalnız POST'tur, GET yoktur —
   yani durumu ordan öğrenmenin yolu onu DEĞİŞTİRMEKTİR. Okunabilir tek yüzey
   `/api/diagnostics.intraday` (`api.py::api_diagnostics` → `intraday_cycle.health()`),
   ve o blok `armed` alanını `health.intraday_armed()`ten okuyor — aynı dosyadan,
   aynı gerçek.

   İKİ "SİLAHLI" AYRI SORUDUR (`api.py::api_diagnostics` şerhinin uyardığı tuzak):
     · `armed`       → OPERATÖRÜN Faz-4b bayrağı (state/INTRADAY_ARM dosyası).
     · `armed_plans` → defterdeki EOD-silahlı plan SAYISI.
   İkisini tek rozette birleştirmek, "sistem silahlı" cümlesini iki farklı şeye
   birden söyletirdi.

   ----------------------------------------------------------------------------
   KORUMA HÜKMÜ NEDEN AYRI BİR KART (v315)
   ----------------------------------------------------------------------------
   "Aynadaki açık emirler" kartı EMİRLERİ listeler, POZİSYONLARI değil. Korumasız
   bir pozisyonun — tanım gereği — canlı emri YOKTUR, yani o kartta HİÇ SATIRI
   OLMAZ. Canlı ölçüm (kâğıt hesap, 2026-08-25): dokuz pozisyonun sekizinde `held`
   stop var, NVDA'da yok; NVDA emir kartında görünmüyordu ve korumasızlığı hiçbir
   ekranda yazmıyordu. Bu yüzden hüküm POZİSYON başına, kendi kartında çizilir ve
   veri `adapters/alpaca._koruma_hukmu`ndan HAZIR gelir — pano hüküm ÜRETMEZ, o
   ölçümü yeniden yapmaya kalkmak iki farklı anda iki farklı cevap üretirdi.
   ============================================================================ */
import { Lock, ShieldAlert, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { adet as adetBicim, Olculemedi, para, sayi } from "./olcum";
import type { AlpacaHesabi, BrokerEmri, KorumaHukmu, SeansIciBlogu } from "./tipler";

/* KORUMA HÜKMÜNÜN ÜÇ DİZGESİ — `alpaca.KORUMA_VAR/KORUMA_YOK/KORUMA_OLCULEMEDI` ile
   BİREBİR aynı olmak ZORUNDA. Dizge kayarsa üç dal da sessizce düşer ve ekran her
   pozisyon için "hüküm tanınmadı" der; `tests/test_koruma_rozeti_v315.py` iki dosyayı
   birbirine çiviliyor ki kayma derlemede değil TESTTE görünsün. */
const KORUMA_VAR = "korumali";
const KORUMA_YOK = "korumasiz";
const KORUMA_OLCULEMEDI = "olculemedi";

function Sayac({ ad, n, not, uyari = false }: { ad: string; n: number | undefined; not: string; uyari?: boolean }) {
  return (
    <div className="rounded-md border p-2" title={not}>
      <div className={cn("font-semibold text-xl tabular-nums", uyari && (n ?? 0) > 0 ? "text-uyari" : "text-foreground")}>
        {n === undefined ? (
          <Olculemedi kisaMetin="—" neden={`${ad} bildirilmedi.`} teknik={`${ad}: teşhis gövdesinde alan yok`} />
        ) : (
          n
        )}
      </div>
      <div className="text-[11px] leading-snug">{ad}</div>
    </div>
  );
}

/** Haritadaki belirli hükümdeki pozisyon sayısı. Bilinmeyen bir `durum` hiçbir kovaya
 *  düşmez — toplamla kovaların farkı okuyucuya "tanınmayan hüküm" olarak yazılır. */
function korumaSayaci(koruma: Readonly<Record<string, KorumaHukmu>>, durum: string): number {
  return Object.values(koruma).filter((h) => h.durum === durum).length;
}

/** BİR POZİSYONUN KORUMA ROZETİ — üç hâl, ÜÇ AYRI ÇİZİM.
 *
 *  "koruma yok" ÖLÇÜLMÜŞ BİR OLGUDUR (emir listesi okundu, stop yok) ve operatörü elle
 *  stop koymaya çağırır. "ölçülemedi" bir ARIZADIR (liste okunamadı) ve operatörü aynaya
 *  bakmaya çağırır. İkisini tek gösterime indirmek, arızayı olgu diye yazmaktır — bu
 *  yüzden kırmızı rozet YALNIZ ikinci hâlde, nedenli tire YALNIZ üçüncüsünde çizilir. */
function KorumaRozeti({ sembol, h }: { sembol: string; h: KorumaHukmu }) {
  if (h.durum === KORUMA_OLCULEMEDI) {
    return (
      <Olculemedi
        kisaMetin="karar verilmedi"
        neden={
          h.neden ??
          `${sembol}: emir listesi okunamadığı için koruma kararı verilemedi. Bu "koruma yok" demek değildir.`
        }
        teknik={
          h.neden
            ? `${sembol}: \`koruma.durum\` = olculemedi`
            : `${sembol}: gövde \`olculemedi\` dedi ama \`neden\` alanını yazmadı`
        }
      />
    );
  }
  if (h.durum === KORUMA_YOK) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <Badge variant="destructive" className="gap-1">
          <ShieldAlert className="size-3.5" />
          koruma YOK
        </Badge>
        <span className="text-muted-foreground text-xs" title={h.neden ?? undefined}>
          emir listesi okundu, canlı stop yok
        </span>
      </span>
    );
  }
  if (h.durum === KORUMA_VAR) {
    const st = sayi(h.stop);
    const cift = (h.stop_n ?? 0) > 1;
    return (
      <span className="inline-flex flex-wrap items-center gap-1.5">
        <Badge variant="outline" className="gap-1">
          <ShieldCheck className="size-3.5" />
          korumalı
        </Badge>
        <span className="tabular-nums text-sm">
          {st === null ? (
            <Olculemedi
              kisaMetin="stop fiyatı okunamadı"
              neden={
                h.neden ??
                `${sembol}: koruma emri canlı ama stop fiyatı henüz okunamadı. Fiyat uydurulmaz; koruma yine de var.`
              }
              teknik={`${sembol}: koruma emri canlı ama \`stop_price\` okunamadı — iz süren stop tetik fiyatını henüz yayınlamamış olabilir`}
            />
          ) : (
            `stop ${para(st)}`
          )}
        </span>
        {cift && (
          <Badge variant="secondary" title="Aynı hisseyi birden çok canlı stop emri rehin tutuyor">
            çifte koruma · {h.stop_n} emir
          </Badge>
        )}
        {h.neden && st !== null && (
          <Olculemedi kisaMetin="şerhli" neden={h.neden} />
        )}
      </span>
    );
  }
  return (
    <Olculemedi
      kisaMetin="karar tanınmadı"
      neden={`${sembol}: koruma kararı bu ekranın tanımadığı bir değer taşıyor. Tanımadığı bir kararı "korumalı" ya da "korumasız" diye çevirmek uydurma olurdu.`}
      teknik={`${sembol}: gövde \`durum\` alanına ${h.durum ?? "hiçbir değer"} yazdı`}
    />
  );
}

/** Kırpma muhasebesinin tek sayısı. Alan gövdede yoksa TİRE DEĞİL nedenli tire — bu
 *  sayıların hiçbiri panoda elle yazılmaz (tavan/pencere değişince pano sessizce yalan
 *  söylerdi; kusurun kendisi tam olarak buydu). */
function KirpmaSayisi({ v, alan }: { v: number | undefined; alan: string }) {
  if (v === undefined) {
    return (
      <Olculemedi
        kisaMetin="yok"
        neden="Bu sayı bildirilmedi — uydurulmaz"
        teknik={`\`open_orders_kirpma.${alan}\` gövdede yok`}
      />
    );
  }
  return <span className="tabular-nums">{v}</span>;
}

export function SeansIciEmir({
  intraday,
  emirler,
  emirNedeni,
  hesap,
}: {
  intraday: SeansIciBlogu | undefined;
  /** `/api/alpaca.account.open_orders` — hesap bloğu null ise `null` (ayna yok). */
  emirler: readonly BrokerEmri[] | null;
  emirNedeni: string;
  /** `/api/alpaca.account` BLOĞUNUN TAMAMI — koruma hükmü, kırpma muhasebesi ve emir
   *  listesinin GERÇEK arıza nedeni yalnız burada yaşıyor.
   *
   *  NEDEN İSTEĞE BAĞLI: bu prop'u besleyen üst yüzey (`PortfoyYuzey`) bu turun
   *  dosya-ayrıklık sözleşmesinin DIŞINDA kaldı. Bağlanmadığı sürece koruma kartı
   *  "geçirilmedi" diye ÖLÇÜLEMEDİ çizer — boş kart ya da yeşil rozet DEĞİL. */
  hesap?: AlpacaHesabi | null;
}) {
  /* HESABIN KENDİSİ ÜÇ HÂL: prop bağlanmamış (undefined) · blok null (ayna yok) · dolu.
     İlk ikisi koruma hükmünün de kırpma muhasebesinin de KAYNAĞINI yok eder; ayırt
     edilmezlerse ekran "koruma alanı gövdede yok" der ve okuyucuyu API'ye bakmaya
     gönderir — oysa arıza panonun kendi kablosundadır. */
  const hesapYok: string | null =
    hesap === undefined
      ? "üst yüzey `/api/alpaca` hesap bloğunu bu karta GEÇİRMEDİ (`hesap` prop'u bağlanmamış) — arıza uçta değil panonun kablosunda"
      : hesap === null
        ? `\`/api/alpaca\` hesap bloğu null — ${emirNedeni}`
        : null;
  const koruma = hesap?.koruma;
  const kirpma = hesap?.open_orders_kirpma ?? null;

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {/* --- SİLAHLANMA KAPISI ------------------------------------------------ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="size-4 text-muted-foreground" />
            İşleme hazırlık kontrolü
          </CardTitle>
          <CardDescription>
            Faz-4b bayrağı (<code className="text-xs">state/INTRADAY_ARM</code>). Varsayılan KAPALI = yalnız gözlem.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {intraday === undefined ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span> `/api/diagnostics` gövdesinde `intraday`
              bloğu yok — bayrağın durumu okunamıyor. `/api/intraday-arm` yalnız POST olduğu için ikinci bir okuma
              yolu YOK; durumu ordan sormak onu değiştirmek olurdu.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                {intraday.armed === undefined ? (
                  <Olculemedi
                    kisaMetin="bayrak okunamadı"
                    neden="İşleme hazırlık bayrağının durumu bildirilmedi"
                    teknik="`intraday.armed` alanı gövdede yok."
                  />
                ) : (
                  <Badge variant={intraday.armed ? "destructive" : "outline"}>
                    {intraday.armed ? "SİLAHLI · otonom emir kapısı AÇIK" : "silahsız · yalnız gözlem"}
                  </Badge>
                )}
                {intraday.mode && <Badge variant="secondary">mod: {intraday.mode}</Badge>}
                {intraday.enabled === false && <Badge variant="secondary">döngü kapalı (ENABLED=false)</Badge>}
                {intraday.ok === null && (
                  <Olculemedi
                    kisaMetin="tüketici hiç kurulmadı"
                    neden="Seans-içi izleyici bu süreçte hiç kurulmamış — bu bir arıza değil"
                    teknik="`intraday.ok` null"
                  />
                )}
              </div>

              <p className="flex items-start gap-2 rounded-md border border-dashed p-2 text-muted-foreground text-xs">
                <Lock className="mt-0.5 size-3.5 shrink-0" />
                Bu pano kolu ÇEKMEZ. Bayrağı değiştiren uç (<code>POST /api/intraday-arm</code>) geri alınamaz bir
                icra kapısı açar; bu yüzey yalnız okur.
              </p>

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Sayac ad="EOD işleme hazır plan" n={intraday.armed_plans} not="Defterdeki işleme hazır plan sayısı — bayrakla AYRI soru" />
                <Sayac ad="Karar (bugün)" n={intraday.decisions?.today} not="intraday_decisions.jsonl'de bugüne düşen satır" />
                <Sayac ad="Karar (toplam)" n={intraday.decisions?.total} not="Defterin ömür boyu satır sayısı" />
                <Sayac ad="Ateşlenen" n={intraday.decisions?.fired} not="fired=true damgalı karar" />
              </div>

              {intraday.last_error && <p className="text-destructive text-xs">Son hata: {intraday.last_error}</p>}
              {intraday.last_decision_at && (
                <p className="text-muted-foreground text-xs">Son karar: {intraday.last_decision_at}</p>
              )}

              {/* AKIŞ BOŞLUĞU: `null` = zamanlayıcı kancası HİÇ KOŞMADI
                  (`scheduler._intraday_gap_check`). "boşluk yok" diye göstermek, hiç
                  bakılmamış bir şeye temiz raporu vermek olurdu. */}
              <p className="text-muted-foreground text-xs">
                Akış boşluğu ölçümü:{" "}
                {intraday.akis_boslugu === null || intraday.akis_boslugu === undefined ? (
                  <Olculemedi
                    kisaMetin="kanca hiç koşmadı"
                    neden="Akış boşluğu hiç ölçülmedi — 'boşluk yok' değil, 'bakılmadı'"
                    teknik="`intraday.akis_boslugu` null — zamanlayıcı kancası (scheduler._intraday_gap_check) bu süreçte hiç koşmadı"
                  />
                ) : (
                  <code className="text-[11px]">{JSON.stringify(intraday.akis_boslugu)}</code>
                )}
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* --- GÖLGE İCRA -------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Deneme icra</CardTitle>
          <CardDescription>"Tetik kesilseydi ne olurdu" defteri — emir GÖNDERMEZ, yalnız kararı yazar.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {intraday?.shadow === undefined ? (
            <Olculemedi
              kisaMetin="deneme bloğu yok"
              neden={
                intraday === undefined
                  ? "Seans-içi teşhis bloğu hiç gelmedi — denemeye alınmış kararların kaydı da onun içinde yaşıyor, ayrı bir kaynağı yok."
                  : "Denemeye alınmış kararların özeti bu turda derlenmedi."
              }
              teknik={
                intraday === undefined
                  ? "/api/diagnostics gövdesinde `intraday` bloğu HİÇ yok"
                  : "`/api/diagnostics.intraday.shadow` gövdede yok"
              }
            />
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={intraday.shadow.enabled ? "outline" : "secondary"}>
                  {intraday.shadow.enabled ? "deneme açık" : "deneme kapalı"}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Sayac ad="Bugün" n={intraday.shadow.today_n} not="Bugünkü deneme satırı" />
                <Sayac ad="Gönderilirdi" n={intraday.shadow.would_submit_n} not="would_submit damgalı bugünkü satır" />
                <Sayac ad="Engellendi" n={intraday.shadow.blocked_n} not="blocked* damgalı bugünkü satır" uyari />
                <Sayac ad="Toplam" n={intraday.shadow.total} not="Defterin ömür boyu satır sayısı" />
              </div>
              {intraday.shadow.vs_eod === null && (
                <Olculemedi
                  kisaMetin="EOD kıyası yok"
                  neden="Denemeye alınmış kararın gün sonu dolumuyla farkı bu turda ölçülmedi"
                  teknik="`shadow.vs_eod` null"
                />
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* --- POZİSYON KORUMASI -------------------------------------------------- */}
      <Card className="xl:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldAlert className="size-4 text-muted-foreground" />
            Pozisyon koruması
          </CardTitle>
          <CardDescription>
            Broker aynasında duran her pozisyon için stop kararı (<code className="text-xs">
              /api/alpaca account.koruma
            </code>). Bu kart POZİSYONLARI sayar: hiç canlı emri olmayan bir pozisyon aşağıdaki defterde GÖRÜNMEZ ama
            burada KORUMASIZ olarak görünür. Hüküm gövdede verilir, burada yeniden hesaplanmaz.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {hesapYok !== null ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span> {hesapYok}
            </p>
          ) : koruma === undefined ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span> `/api/alpaca account.koruma` alanı
              gövdede YOK — hüküm üreten sürüm dağıtılmamış olabilir. Alan yokken her pozisyonu "korumalı" saymak
              da "korumasız" saymak da uydurma olurdu.
            </p>
          ) : koruma === null ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span>{" "}
              {hesap?.koruma_neden ??
                "`koruma` null ama `koruma_neden` boş — POZİSYON listesi okunamadı, yani hangi sembol için karar verileceği bile bilinmiyor."}
            </p>
          ) : Object.keys(koruma).length === 0 ? (
            <p className="text-muted-foreground text-sm">
              Aynada pozisyon yok — korunacak bir şey de yok. Bu ölçülmüş bir olgu: pozisyon listesi OKUNDU ve boş
              döndü.
            </p>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Sayac
                  ad="korumalı"
                  n={korumaSayaci(koruma, KORUMA_VAR)}
                  not="Sembolde canlı stop-ailesi emri VAR"
                />
                <Sayac
                  ad="KORUMASIZ"
                  n={korumaSayaci(koruma, KORUMA_YOK)}
                  not="Emir listesi okundu ve bu sembolde canlı stop YOK — ölçülmüş olgu"
                  uyari
                />
                <Sayac
                  ad="karar verilmedi"
                  n={korumaSayaci(koruma, KORUMA_OLCULEMEDI)}
                  not="Emir listesi okunamadı — arıza, 'koruma yok' DEĞİL"
                />
                <Sayac
                  ad="tanınmayan karar"
                  n={
                    Object.keys(koruma).length -
                    korumaSayaci(koruma, KORUMA_VAR) -
                    korumaSayaci(koruma, KORUMA_YOK) -
                    korumaSayaci(koruma, KORUMA_OLCULEMEDI)
                  }
                  not="Gövde bu yüzeyin tanımadığı bir `durum` yazdı"
                  uyari
                />
              </div>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Sembol</TableHead>
                      <TableHead>Koruma kararı</TableHead>
                      <TableHead>Şerh</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(koruma).map(([sembol, h]) => (
                      <TableRow key={sembol}>
                        <TableCell className="font-medium">{sembol}</TableCell>
                        <TableCell>
                          <KorumaRozeti sembol={sembol} h={h} />
                        </TableCell>
                        {/* ÇIPLAK TİRE YOK: burada "—" iki farklı şeye çıkardı ("şerh yok"
                            ve "şerh okunamadı"). `neden` null OLMASI ölçülmüş bir olgudur —
                            gövde hükmü verirken hiçbir kayıt düşmedi — ve cümleyle yazılır. */}
                        <TableCell className="text-muted-foreground text-xs">
                          {h.neden ?? "şerh yok"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* --- AYNADAKİ AÇIK EMİRLER ---------------------------------------------
          SAYI GÖVDEDEN OKUNUR, ELLE YAZILMAZ. Bu kartın açıklaması bir zamanlar
          satır tavanını RAKAMLA yazıyordu; gövdedeki tavan
          (`alpaca._PANO_EMIR_TAVANI`) ve pencere (`alpaca._PANO_EMIR_PENCERESI`)
          o cümle yazıldıktan sonra değişti ve pano ÖLÇÜLMEMİŞ bir sayıyı OLGU
          diye beyan eder oldu. Artık iki sayı da `open_orders_kirpma`
          gövdesinden gelir; gövde söylemezse ekran "ölçülemedi" der, sayı
          UYDURMAZ. Bu yüzden çivi (`test_koruma_rozeti_v315`) kartta elle yazılı
          hiçbir çok basamaklı sayı bırakmıyor. */}
      <Card className="xl:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Aynadaki açık emirler</CardTitle>
          <CardDescription>
            Alpaca kâğıt hesabının CANLI emir defteri — koruma bacakları DAHİL (`held` duran stoplar da sayılır).{" "}
            {kirpma === null ? (
              <>
                Satır tavanı ve API penceresi{" "}
                <Olculemedi
                  kisaMetin="ölçülemedi"
                  neden="Satır tavanı ve sorgu penceresi ölçülemedi — liste okunamadığında kırpma muhasebesi de üretilmez. Tavan sayısı uydurulmaz"
                  teknik="`open_orders_kirpma` gövdede yok"
                />
                . Salt okuma.
              </>
            ) : (
              <>
                En çok <KirpmaSayisi v={kirpma.tavan} alan="tavan" /> satır gösterilir; API penceresi{" "}
                <KirpmaSayisi v={kirpma.pencere_istenen} alan="pencere_istenen" /> emir. Salt okuma.
              </>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {kirpma !== null && (
            <div className="flex flex-col gap-1 rounded-md border border-dashed p-2 text-xs">
              <p className="text-muted-foreground">
                Kırpma muhasebesi: canlı <KirpmaSayisi v={kirpma.canli} alan="canli" /> satır ·{" "}
                gövdeye girmeyen <KirpmaSayisi v={kirpma.kirpilan} alan="kirpilan" /> satır · API penceresinden dönen{" "}
                <KirpmaSayisi v={kirpma.pencere_donen} alan="pencere_donen" /> emir.
              </p>
              {(kirpma.kirpilan ?? 0) > 0 && (
                <p className="text-uyari">
                  Tavan aşıldı: <KirpmaSayisi v={kirpma.kirpilan} alan="kirpilan" /> canlı satır gövdeye GİRMEDİ.
                  Aşağıdaki tablo canlı defterin TAMAMI değildir.
                </p>
              )}
              {kirpma.pencere_doygun === undefined ? (
                <Olculemedi
                  kisaMetin="pencere doygunluğu ölçülemedi"
                  neden="Sorgu penceresinin dolup dolmadığı bildirilmedi — 'dolmadı' diye saymak uydurma olurdu"
                  teknik="`open_orders_kirpma.pencere_doygun` gövdede yok"
                />
              ) : kirpma.pencere_doygun ? (
                <p className="text-destructive">
                  API penceresi DOLDU (istenen <KirpmaSayisi v={kirpma.pencere_istenen} alan="pencere_istenen" />,
                  dönen <KirpmaSayisi v={kirpma.pencere_donen} alan="pencere_donen" />) — bu liste TAM DEĞİL. Pencere
                  doygunken "hepsi bu" cümlesi KANITLANMAMIŞTIR; eksik bir emir sessizce dışarıda kalmış olabilir.
                </p>
              ) : (
                <p className="text-muted-foreground">
                  API penceresi doymadı — pencere sınırının BİR emri bile kesmediği ölçüldü, liste bu yönden tam.
                </p>
              )}
            </div>
          )}
          {emirler === null ? (
            <p className="text-muted-foreground text-sm">
              <span className="font-medium text-foreground">Ölçülemedi:</span>{" "}
              {hesap?.open_orders_neden ?? emirNedeni}
              {hesap !== undefined && hesap !== null && !hesap.open_orders_neden && (
                <>
                  {" "}
                  (gövde `open_orders_neden` yazmadı — bu cümle üst yüzeyin hesap teşhisinden geldi, emir
                  katmanının kendi arıza nedeni DEĞİL.)
                </>
              )}
            </p>
          ) : emirler.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              Aynada canlı emir yok. Bu ölçülmüş bir olgu — emir defteri OKUNDU ve `open_orders` boş döndü
              (okunamasaydı `null` gelirdi, bu iki hâl AYRIDIR).
            </p>
          ) : (
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
                  {emirler.map((o, i) => {
                    const q = sayi(o.qty);
                    const st = sayi(o.stop);
                    const lm = sayi(o.limit);
                    return (
                      <TableRow key={`${o.symbol ?? "?"}-${i}`}>
                        <TableCell className="font-medium">
                          {o.symbol ?? (
                            <Olculemedi
                              kisaMetin="sembolsüz"
                              neden="Bu emir hangi hisseye ait, bildirilmemiş"
                              teknik="emir satırında `symbol` yok"
                            />
                          )}
                        </TableCell>
                        <TableCell className="text-sm">{o.side ?? "—"}</TableCell>
                        <TableCell className="text-sm">{o.type ?? "—"}</TableCell>
                        <TableCell className="text-right tabular-nums">
                          {q === null ? (
                            <Olculemedi neden="Emrin adedi okunamadı" teknik="`qty` alanı sayıya çevrilemedi" />
                          ) : (
                            adetBicim(q)
                          )}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {st === null ? (
                            <Olculemedi
                              kisaMetin="stop yok"
                              neden="Bu emir türü stop fiyatı taşımıyor"
                              teknik="`stop_price` boş"
                            />
                          ) : (
                            para(st)
                          )}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {lm === null ? (
                            <Olculemedi
                              kisaMetin="limit yok"
                              neden="Bu emir türü limit fiyatı taşımıyor"
                              teknik="`limit_price` boş"
                            />
                          ) : (
                            para(lm)
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{o.status ?? "durumsuz"}</Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
