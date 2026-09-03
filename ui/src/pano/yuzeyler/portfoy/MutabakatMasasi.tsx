"use client";

/* ============================================================================
   MUTABAKAT MASASI — "Alpaca'daki para panodakinden farklı" sorusunun masası
   ----------------------------------------------------------------------------
   Bu bölüm bir FARKI göstermez, farkı AÇIKLAR. Sistem ayrışmayı zaten biliyordu
   (`sermaye_koken.ayrisik`); eksik olan köprüydü — operatör iki sayı görüyor,
   aradaki terimleri göremiyordu (api.py::api_today şerhi, operatör şikâyeti 2026-08-21).

   ÜÇ AYRI SORU, ÜÇ AYRI KART — ve birbirinin yerine GEÇMEZLER:
     1. PARA köprüsü (`broker_mutabakati`): farkın BÜYÜKLÜĞÜ, terim terim.
     2. ADET mutabakatı (`pozisyon_mutabakati`): farkın NEREDEN geldiği. Yön
        kaybolmaz — "kitapta var brokerda yok" (karşılıksız) ile tersi (kitabın
        bilmediği pozisyon) ayrı kovalardadır (sermaye.py::pozisyon_mutabakati).
     3. AYNA turu (`/api/alpaca.reconcile`): son mutabakat turu ne yaptı, neyi
        atladı, hangi gönderim reddedildi.

   `aciklanamayan === null` "fark yok" DEĞİLDİR. Beş terimden biri bile
   ölçülemediyse kalıntı UYDURULMAZ (sermaye.py::broker_mutabakati) — kart o hâlde tutarı değil
   `olculemedi_neden`i yazar. `defter_teyit` ise `try` bloğunun içinde doğuyor
   (api.py::api_today): köprü patlarsa alan HİÇ YOKTUR, `null` değil — bu yüzden
   `=== undefined` sınanır, doğruluğu değil VARLIĞI.
   ============================================================================ */
import { AlertTriangle, ArrowLeftRight, Check } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { Deger, Olculemedi, para, sayi } from "./olcum";
import type { AkisSagligi, BrokerMutabakati, DefterTeyit, MutabakatKaydi, PozisyonMutabakati } from "./tipler";

// ---------------------------------------------------------------------------
// 1 · PARA KÖPRÜSÜ
// ---------------------------------------------------------------------------
interface KopruSatiri {
  readonly etiket: string;
  readonly deger: number | null | undefined;
  readonly isaret: "" | "+" | "−" | "=";
  readonly vurgu?: boolean;
  readonly aciklama: string;
}

function KopruKarti({ m }: { m: BrokerMutabakati | undefined }) {
  if (!m) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Broker ↔ kitap köprüsü</CardTitle>
        </CardHeader>
        <CardContent>
          <Olculemedi
            kisaMetin="alan hiç gelmedi"
            neden="Broker ile kitap arasındaki köprü bu turda hiç gelmedi"
            teknik="/api/today gövdesinde `broker_mutabakati` anahtarı YOK. api.py::api_today onu her iki dalda da yazıyor — anahtarın hiç olmaması, uç sürümünün bu alandan önceki hâlde olduğunu ya da gövdenin kırpıldığını gösterir."
          />
        </CardContent>
      </Card>
    );
  }

  const satirlar: readonly KopruSatiri[] = [
    { etiket: "Broker sermayesi (mark-to-market)", deger: m.broker_equity, isaret: "", aciklama: "Alpaca hesabının şu andaki equity'si" },
    { etiket: "Gerçekleşmemiş K/Z", deger: m.gerceklesmemis_pnl, isaret: "−", aciklama: "Açık pozisyonların unrealized_pl toplamı" },
    { etiket: "Broker · maliyet bazlı", deger: m.broker_maliyet_bazli, isaret: "=", vurgu: true, aciklama: "Mark-to-market'ten açık kâr çıkarılmış hâli" },
    { etiket: "Broker · reset günü sermayesi", deger: m.broker_reset_gunu_equity, isaret: "−", aciklama: `Reset tarihindeki (${m.reset_tarihi ?? "?"}) broker equity'si` },
    { etiket: "Broker · reset sonrası kazanç", deger: m.broker_reset_sonrasi, isaret: "=", vurgu: true, aciklama: "Brokerın reset'ten bugüne net kazancı" },
    { etiket: "Kitap nakdi", deger: m.kitap_cash, isaret: "", aciklama: "portfolio.json cash" },
    { etiket: "Sermaye tabanı", deger: m.sermaye_tabani, isaret: "−", aciklama: "Reset beyanının tabanı" },
    { etiket: "Kitap · reset sonrası kazanç", deger: m.kitap_reset_sonrasi, isaret: "=", vurgu: true, aciklama: "Kitabın reset'ten bugüne gerçekleşmiş kazancı" },
  ];

  const kalinti = m.aciklanamayan ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ArrowLeftRight className="size-4 text-muted-foreground" />
          Broker ↔ kitap köprüsü
        </CardTitle>
        <CardDescription>
          İki sayı elmayla armut: broker mark-to-market ve hesap ömrü boyunca kümülatif, kitap gerçekleşmiş ve
          reset'ten sonra yeniden tabanlanmış. Köprü terimleri açar.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8" />
                <TableHead>Terim</TableHead>
                <TableHead className="text-right">Tutar</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {satirlar.map((s) => (
                <TableRow key={s.etiket} className={s.vurgu ? "bg-muted/40" : undefined}>
                  <TableCell className="text-center text-muted-foreground tabular-nums">{s.isaret}</TableCell>
                  <TableCell className={cn("text-sm", s.vurgu && "font-medium")} title={s.aciklama}>
                    {s.etiket}
                  </TableCell>
                  <TableCell className="text-right">
                    <Deger
                      v={s.deger}
                      bicim={para}
                      className={s.vurgu ? "font-medium" : undefined}
                      neden={
                        m.olculemedi_neden ??
                        `${s.etiket} bildirilmedi. Türetmek yasak — bilgisizliğimiz para farkı gibi okunamaz.`
                      }
                      teknik="uç bu terimi döndürmedi (sermaye.py::broker_mutabakati: beş terimin biri eksikse köprü türetilmez)"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="rounded-md border p-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <span className="font-medium text-sm">Açıklanamayan kalıntı</span>
            {kalinti === null ? (
              <Olculemedi
                kisaMetin="ölçülemedi"
                neden={
                  m.olculemedi_neden ??
                  "Kalıntı hesaplanmadı ve nedeni bildirilmedi. Bu bir 'fark yok' cevabı değil — beş terimin beşi ölçülmeden kalıntı üretilmez."
                }
                teknik="`aciklanamayan` null ve `olculemedi_neden` boş (sermaye.py::broker_mutabakati)"
              />
            ) : (
              /* KALINTININ RENGİ K/Z RENGİ DEĞİLDİR — bilerek. Pozitif kalıntı
                 "kâr" demek değil, "brokerın reset sonrası kazancı kitabınkinden
                 fazla" demektir; ikisi de aynı derecede kayıt eksiğidir. Yeşile
                 boyamak, bir ayrışmayı iyi haber gibi okutmak olurdu. */
              <span
                className={cn(
                  "font-semibold text-lg tabular-nums",
                  kalinti === 0 ? "text-muted-foreground" : "text-uyari",
                )}
              >
                {para(kalinti)}
              </span>
            )}
          </div>
          <p className="mt-1 text-muted-foreground text-xs">
            Broker reset sonrası − kitap reset sonrası. Sıfırdan uzaklaştıkça iki defter arasında KAYIT eksiği var
            demektir; tarihî bir artefakt değil, yaşayan bir ayrışma.
            {m.broker_gecmis_neden ? ` Broker geçmişi: ${m.broker_gecmis_neden}` : ""}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 2 · ADET MUTABAKATI
// ---------------------------------------------------------------------------
function AdetKarti({ m }: { m: PozisyonMutabakati | undefined }) {
  if (!m) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pozisyon adet mutabakatı</CardTitle>
        </CardHeader>
        <CardContent>
          <Olculemedi
            kisaMetin="alan hiç gelmedi"
            neden="Pozisyon adet mutabakatı bu turda hiç gelmedi"
            teknik="/api/today gövdesinde `pozisyon_mutabakati` anahtarı YOK."
          />
        </CardContent>
      </Card>
    );
  }

  const kovalar = [
    { ad: "Adet ayrışan", satirlar: m.ayrisan ?? [], aciklama: "İki defter de sembolü biliyor ama adet tutmuyor" },
    { ad: "Yalnız kitapta", satirlar: m.yalniz_kitapta ?? [], aciklama: "Karşılıksız pozisyon — brokerda izi yok" },
    { ad: "Yalnız brokerda", satirlar: m.yalniz_brokerda ?? [], aciklama: "Kitabın hiç bilmediği pozisyon" },
  ];
  const olculemedi = m.olculemedi_neden ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Pozisyon adet mutabakatı</CardTitle>
        <CardDescription>
          Para köprüsü farkın BÜYÜKLÜĞÜNÜ verir; bu kart NEREDEN geldiğini. Yön kaybolmaz: karşılıksız pozisyon ile
          kitabın bilmediği pozisyon ayrı kovalardadır.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {olculemedi ? (
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Ölçülemedi:</span> {olculemedi}
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="text-muted-foreground">Ayrışan sembol:</span>
              <Deger
                v={m.ayrisan_sayisi}
                bicim={(n) => String(n)}
                className="font-semibold"
                neden="Ayrışan sembol sayısı okunamadı — iki taraftan biri okunamadı, '0 ayrışma' demek değil"
                teknik="`ayrisan_sayisi` null döndü"
              />
              <span className="text-muted-foreground">/ toplam</span>
              <Deger
                v={m.toplam_sembol}
                bicim={(n) => String(n)}
                neden="Toplam sembol sayısı ölçülemedi"
                teknik="`toplam_sembol` null ya da gövdede yok"
              />
              {m.ayrisan_sayisi === 0 && (
                <Badge variant="outline" className="gap-1">
                  <Check className="size-3" /> iki defter tutuyor
                </Badge>
              )}
            </div>

            {kovalar.map((k) => (
              <div key={k.ad}>
                <div className="flex items-baseline gap-2">
                  <span className="font-medium text-sm">{k.ad}</span>
                  <span className="text-muted-foreground text-xs">
                    {k.satirlar.length} · {k.aciklama}
                  </span>
                </div>
                {k.satirlar.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {k.satirlar.map((r, i) => (
                      <Badge
                        key={`${r.ticker ?? "?"}-${i}`}
                        variant="outline"
                        className="gap-1 tabular-nums"
                        title={`kitap ${r.kitap ?? "?"} · broker ${r.broker ?? "?"}`}
                      >
                        <AlertTriangle className="size-3 text-uyari" />
                        {r.ticker ?? "sembolsüz"} {r.kitap ?? "?"}/{r.broker ?? "?"}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 3 · DEFTER TEYİDİ
// ---------------------------------------------------------------------------
function TeyitKarti({ t }: { t: DefterTeyit | undefined }) {
  // ALANIN VARLIĞI SINANIR, DOĞRULUĞU DEĞİL: `defter_teyit` api.py::api_today içinde `try`
  // bloğunun İÇİNDE yazılıyor — broker köprüsü patlarsa anahtar HİÇ olmaz.
  // `{}` ile "hepsi sıfır" arasındaki fark tam olarak budur.
  if (t === undefined) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Defterin broker teyidi</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            <span className="font-medium text-foreground">Ölçülemedi:</span> `/api/today` gövdesinde `defter_teyit`
            anahtarı YOK. Bu alan broker köprüsü try bloğunun içinde yazılıyor (api.py::api_today) — anahtarın olmaması,
            köprünün o istekte patladığını gösterir. Sıfır teyit ile bakılamamış teyit aynı şey değildir.
          </p>
        </CardContent>
      </Card>
    );
  }

  const kovalar = [
    { ad: "Teyitli", n: t.teyitli, renk: "text-basari", not: "Broker emir defterinde plan kimliğiyle dolmuş emir var" },
    { ad: "Karşılıksız", n: t.karsiliksiz, renk: "text-red-600 dark:text-red-400", not: "Brokerda hiç iz yok — ve defter kırpık DEĞİLKEN bakıldı" },
    { ad: "Bakılamadı", n: t.olculemedi, renk: "text-muted-foreground", not: "Pencere/kimlik/kırpık defter — 'karşılıksız' DEĞİL" },
    { ad: "Kapsam dışı", n: t.kapsam_disi, renk: "text-muted-foreground", not: "Başlangıç verisi/belirsiz satır: kill kriteri gereği kıyasa girmez" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Defterin broker teyidi</CardTitle>
        <CardDescription>"Canlı" damgalı kapanmış işlemin kaçı gerçekten brokerın emir defterinde bulundu.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {kovalar.map((k) => (
          <div key={k.ad} className="rounded-md border p-3">
            <div className={cn("font-semibold text-2xl tabular-nums", k.renk)}>
              {k.n === undefined ? (
                <Olculemedi kisaMetin="—" neden={`${k.ad} kovası bildirilmedi.`} teknik="`defter_teyit` bu kovayı taşımıyor" />
              ) : (
                k.n
              )}
            </div>
            <div className="text-sm">{k.ad}</div>
            <div className="mt-0.5 text-[11px] text-muted-foreground leading-snug">{k.not}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 4 · SON AYNA TURU + AKIŞ
// ---------------------------------------------------------------------------
function AynaKarti({ r, akis }: { r: MutabakatKaydi | undefined; akis: AkisSagligi | undefined }) {
  if (!r) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Son ayna turu</CardTitle>
        </CardHeader>
        <CardContent>
          <Olculemedi
            kisaMetin="alan hiç gelmedi"
            neden="Son mutabakat turunun kaydı gelmedi"
            teknik="/api/alpaca gövdesinde `reconcile` anahtarı yok."
          />
        </CardContent>
      </Card>
    );
  }

  const atlandi = r.checked === false;
  const acikRet = r.failed_submissions?.open ?? [];
  const kapaliRet = r.failed_submissions?.acked ?? [];
  const hayalet = r.ghosts ?? [];
  const soyulan = r.stripped ?? [];
  const adetSapmasi = r.positions?.qty_drift ?? [];
  const aynadaYok = r.positions?.missing_on_alpaca ?? [];
  const disPozisyon = r.positions?.external ?? [];

  const sayaclar = [
    { ad: "Hayalet emir", n: hayalet.length, not: "Aynada canlı, kitapta karşılığı olmayan emir" },
    { ad: "Soyulan işleme hazır plan", n: soyulan.length, not: "Ayna emri ölmüş, plan işleme hazır planlardan çıkarıldı" },
    { ad: "Adet sapması", n: adetSapmasi.length, not: "İç adet ile Alpaca adedi %25'ten fazla ayrıldı" },
    { ad: "Aynada kayıp", n: aynadaYok.length, not: "İçeride açık, Alpaca'da ne pozisyon ne emir (split-brain)" },
    { ad: "Kitap dışı pozisyon", n: disPozisyon.length, not: "Alpaca'da var, kitabın hiç bilmediği sembol" },
    { ad: "Açık ret", n: acikRet.length, not: "Reddedilmiş gönderim, henüz kapatılmadı" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Son ayna turu</CardTitle>
        <CardDescription>
          {r.date ? `Tur tarihi ${r.date}` : "Tur tarihi yazılmamış"}
          {r.updated ? ` · yazım ${r.updated}` : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {r.api_ok === undefined ? (
            <Olculemedi
              kisaMetin="api_ok yok"
              neden="Turun broker tarafına ulaşıp ulaşamadığı bildirilmedi"
              teknik="`reconcile.api_ok` gövdede yok"
            />
          ) : (
            <Badge variant={r.api_ok ? "outline" : "destructive"}>{r.api_ok ? "broker API ulaşıldı" : "broker API'sine ULAŞILAMADI"}</Badge>
          )}
          {atlandi && (
            <Badge variant="secondary" title={r.skip_reason ?? undefined}>
              tur ATLANDI{r.skip_sinif ? ` · ${r.skip_sinif}` : ""}
            </Badge>
          )}
          {r.mirror_drift === true && <Badge variant="destructive">emir sapması</Badge>}
          {r.position_drift === true && <Badge variant="destructive">pozisyon sapması</Badge>}
          {r.positions?.api_ok === false && <Badge variant="destructive">pozisyon listesi okunamadı</Badge>}
        </div>

        {atlandi && r.skip_reason && (
          <p className="text-muted-foreground text-sm">
            <span className="font-medium text-foreground">Atlama nedeni:</span> {r.skip_reason}
          </p>
        )}

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {sayaclar.map((s) => (
            <div key={s.ad} className="rounded-md border p-2" title={s.not}>
              <div className={cn("font-semibold text-xl tabular-nums", s.n > 0 ? "text-uyari" : "text-muted-foreground")}>
                {s.n}
              </div>
              <div className="text-[11px] leading-snug">{s.ad}</div>
            </div>
          ))}
        </div>

        {adetSapmasi.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {adetSapmasi.map((d, i) => (
              <Badge key={`${d.ticker ?? "?"}-${i}`} variant="outline" className="tabular-nums" title={d.drift_sinifi ?? "sapma sınıfı yazılmamış"}>
                {d.ticker ?? "sembolsüz"} · iç {sayi(d.local_qty) ?? "?"} / ayna {sayi(d.alpaca_qty) ?? "?"}
              </Badge>
            ))}
          </div>
        )}

        {kapaliRet.length > 0 && (
          <p className="text-muted-foreground text-xs">
            {kapaliRet.length} reddedilmiş gönderim ACK'lendi — tarihçe silinmedi, sesi kısıldı.
          </p>
        )}

        {/* AKIŞ SAĞLIĞI: `stream_ok === null` ÜÇÜNCÜ HÂLDİR (api.py::_stream_view) — ayna hiç
            koşmamış demek, "KOPUK" demek değil. İkisini aynı renge boyamak, ayna
            kullanmayan bir kurulumda sonsuza dek arıza raporlamak olurdu. */}
        <div className="border-t pt-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-sm">Ayna akışı</span>
            {akis === undefined ? (
              <Olculemedi
                kisaMetin="stream bloğu yok"
                neden="Broker tarafındaki canlı akışın durumu bildirilmedi"
                teknik="/api/alpaca gövdesinde `stream` anahtarı yok."
              />
            ) : akis.stream_ok === null || akis.stream_ok === undefined ? (
              <Olculemedi
                kisaMetin="hiç koşmadı"
                neden="Canlı akış bu kurulumda hiç çalışmamış — bu 'kopuk' demek değildir"
                teknik="`stream_ok` null: nabız damgası da, son olay da, kopuş anı da yok"
              />
            ) : (
              <Badge variant={akis.stream_ok ? "outline" : "destructive"}>{akis.stream_ok ? "akış canlı" : "akış KOPUK"}</Badge>
            )}
            {akis?.stream_down_since && <span className="text-muted-foreground text-xs">kopuş: {akis.stream_down_since}</span>}
            {akis?.stream_checked_age_s !== null && akis?.stream_checked_age_s !== undefined && (
              <span className="text-muted-foreground text-xs">nabız yaşı {Math.round(akis.stream_checked_age_s)} sn</span>
            )}
          </div>
          {akis?.stream_last_error && <p className="mt-1 text-destructive text-xs">{akis.stream_last_error}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export function MutabakatMasasi({
  kopru,
  adet,
  teyit,
  reconcile,
  akis,
}: {
  kopru: BrokerMutabakati | undefined;
  adet: PozisyonMutabakati | undefined;
  teyit: DefterTeyit | undefined;
  reconcile: MutabakatKaydi | undefined;
  akis: AkisSagligi | undefined;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <KopruKarti m={kopru} />
      <div className="flex flex-col gap-4">
        <AdetKarti m={adet} />
        <TeyitKarti t={teyit} />
      </div>
      <div className="xl:col-span-2">
        <AynaKarti r={reconcile} akis={akis} />
      </div>
    </div>
  );
}
