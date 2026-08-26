"use client";

/* ============================================================================
   FLATTEN KAPISI — diğer üç koldan AYRI SINIF, ve ayrılığı yazılı
   ----------------------------------------------------------------------------
   Kademe 1/2/4 bir BAYRAĞA dokunur; bu kol PİYASADA İŞLEM YAPAR. Geri alınamazlığı
   da başka cinstir: HALT'ı kaldırmak bayrağı eski hâline getirir, kapanmış bir
   pozisyonu "geri açmak" ise YENİ bir işlemdir ve aynı fiyatı vermez. O yüzden
   onayı da diğerlerinden ağırdır ve ağırlığı üç ayrı katmandan gelir:

   1 · ÖLÇÜM — kaç pozisyon, hangi semboller, ne kadar piyasa değeri. Kaynak
       BROKER (`/api/alpaca`), kitap DEĞİL: Flatten broker'da işlem yapar ve iki
       defterin ayrıştığı bu depoda ÖLÇÜLMÜŞTÜR (api.py:1687 — "yedi açık
       pozisyonun yedisinde de adet ayrışıyordu"). Kitaba bakan bir onay cümlesi
       doğru görünen bir yalan olurdu.

   2 · SUNUCUNUN KENDİ CEVABI — jetonsuz `POST /api/alpaca/close_all` bir KURU
       KOŞUDUR ve hiçbir şeye dokunmaz (alpaca.py:1120-1124: jeton yoksa yalnız
       `would_flatten` + `foreign` raporlanır, tek satır bile emir çıkmaz). Bu,
       "ne olacak" sorusunun panodan değil UÇTAN gelen cevabıdır — ve tek başına
       `/api/alpaca`nın veremeyeceği bir şeyi verir: hangi pozisyonun MOTORA ait
       OLMADIĞINI (`foreign` = senin elle aldıkların).

   3 · JETON YAZIMI — son düğme, `FLATTEN-PAPER` elle yazılmadan açılmaz.
       NEDEN SEMBOL DEĞİL DE JETON: sembolü yazdırmak, ölçüm düştüğünde onayı
       İMKÂNSIZ kılardı — broker okunamıyorken hangi sembolü yazacaktı operatör?
       Acil bir anda ölçüm eksikliğinin operatörü ENGELLEMEMESİ turun açık şartı.
       Jeton ise ucun kendi sözleşmesidir (alpaca.py:60), her koşulda bilinir ve
       yazılabilir; kas hafızasıyla değil, okuyarak yazılır — istenen fren bu.

   ÖLÇÜM DÜŞERSE KAPI YİNE AÇILIR: her ölçüm satırı "ölçülemedi + neden" yazar ve
   jeton alanı çalışmaya devam eder. Ölçemediğimiz için operatörü acil durumda
   engellemek, bu koldaki en pahalı yanlış olurdu.
   ============================================================================ */
import { useEffect, useState } from "react";

import { CircleAlert, RefreshCw, ShieldAlert, TriangleAlert, Undo2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";

import type { Durum } from "../veri";
import {
  FLATTEN_JETON,
  KOLLAR,
  krizPost,
  paraMetni,
  pozisyonlariOlc,
  type AlpacaGovdesi,
  type KuruKosu,
} from "./krizUclari";

/** Kuru koşunun üç hâli AYRI: koşuluyor · okundu · okunamadı. */
type KuruHal =
  | { readonly ad: "kosuyor" }
  | { readonly ad: "okundu"; readonly govde: KuruKosu }
  | { readonly ad: "okunamadi"; readonly neden: string };

function Olculemedi({ neden, teknik }: { readonly neden: string; readonly teknik?: string }) {
  return (
    <span
      className="text-muted-foreground text-xs italic"
      title={teknik ? `${neden} — ${teknik}` : neden}
    >
      ölçülemedi — <span className="not-italic">{neden}</span>
    </span>
  );
}

export function FlattenKapisi({
  alpaca,
  gonderiliyor,
  onGonder,
  onVazgec,
}: {
  /** `/api/alpaca` — panelin AÇILDIĞINDA bir kez okuduğu broker görünümü. */
  readonly alpaca: Durum<AlpacaGovdesi>;
  readonly gonderiliyor: boolean;
  readonly onGonder: () => void;
  readonly onVazgec: () => void;
}) {
  const [kuru, setKuru] = useState<KuruHal>({ ad: "kosuyor" });
  const [jeton, setJeton] = useState("");

  // KURU KOŞU KAPI AÇILIRKEN BİR KEZ. `POST` olması rahatsız edici görünebilir; kaynağı
  // okundu ve jetonsuz dal broker'a yalnız GET atıyor (orders + positions), sonra dönüyor
  // (alpaca.py:1120-1124). Yani bu POST'un yan etkisi YOKTUR — ve karşılığında sunucunun
  // "ben şunları düzleştirirdim" cevabını veriyor.
  useEffect(() => {
    let canli = true;
    setKuru({ ad: "kosuyor" });
    void krizPost("/api/alpaca/close_all").then((s) => {
      if (!canli) return;
      if (s.kod === 0) {
        setKuru({ ad: "okunamadi", neden: `ağ — ${s.detay ?? "sebep yazılmadı"}` });
        return;
      }
      if (s.kod === 401) {
        setKuru({ ad: "okunamadi", neden: "oturum düştü (401) — panoya yeniden gir" });
        return;
      }
      const g = s.govde;
      if (g === null || typeof g !== "object") {
        setKuru({ ad: "okunamadi", neden: `HTTP ${s.kod} — gövde okunamadı` });
        return;
      }
      setKuru({ ad: "okundu", govde: g as KuruKosu });
    });
    return () => {
      canli = false;
    };
  }, []);

  const olcum = pozisyonlariOlc(alpaca.veri, alpaca.hata ?? (alpaca.oturumDustu ? "oturum düştü (401)" : null));
  const para = paraMetni(olcum.piyasaDegeri);
  const kuruGovde = kuru.ad === "okundu" ? kuru.govde : null;
  const kuruListe = Array.isArray(kuruGovde?.would_flatten) ? kuruGovde.would_flatten : null;
  const kuruYabanci = Array.isArray(kuruGovde?.foreign) ? kuruGovde.foreign : null;
  const jetonTamam = jeton.trim() === FLATTEN_JETON;

  return (
    <div className="rounded-md border border-destructive/50 bg-destructive/5 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <ShieldAlert className="size-4 text-destructive" aria-hidden />
        <span className="font-medium text-sm">Son düğme şunu yapacak</span>
        <Badge variant="destructive" className="font-mono text-[10px]">
          GERİ ALINAMAZ
        </Badge>
      </div>

      <p className="mt-2 text-sm leading-6">{KOLLAR.flatten.nedir}</p>
      <p className="mt-1 text-destructive text-xs leading-5">{KOLLAR.flatten.geriAlmaNotu}</p>

      {/* ---- ÖLÇÜM · BROKER (kitap DEĞİL) --------------------------------- */}
      <div className="mt-3 rounded-md border bg-background p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h6 className="text-muted-foreground text-[11px] uppercase tracking-wide">
            Ne kapanacak — ölçüm kaynağı <code className="font-mono normal-case">GET /api/alpaca</code>
          </h6>
          <Button
            type="button"
            variant="ghost"
            size="xs"
            onClick={alpaca.tazele}
            disabled={alpaca.yukleniyor || gonderiliyor}
          >
            {alpaca.yukleniyor ? <Spinner className="size-3" /> : <RefreshCw aria-hidden />}
            yeniden ölç
          </Button>
        </div>

        <dl className="mt-2 grid grid-cols-1 gap-1.5 text-xs sm:grid-cols-[9rem_1fr]">
          <dt className="text-muted-foreground">Pozisyon adedi</dt>
          <dd>
            {olcum.adet === null ? (
              <Olculemedi neden={olcum.neden ?? "sebep yazılmadı (bu bir kusurdur)"} />
            ) : (
              <span className="font-mono font-medium tabular-nums">{olcum.adet}</span>
            )}
          </dd>

          <dt className="text-muted-foreground">Semboller</dt>
          <dd>
            {olcum.semboller.length === 0 ? (
              <Olculemedi neden={olcum.neden ?? "broker liste boş döndü"} />
            ) : (
              <span className="font-mono break-words">{olcum.semboller.join(" · ")}</span>
            )}
          </dd>

          <dt className="text-muted-foreground">Piyasa değeri</dt>
          <dd>
            {para === null ? (
              <Olculemedi
                neden="Pozisyonların piyasa değeri hesaplanamadı"
                teknik="hiçbir satırda `qty × current` çözülemedi — `dashboard_view` `market_value` alanını geçirmiyor"
              />
            ) : (
              <span className="font-medium tabular-nums">
                {olcum.degeriOlculemeyen.length > 0 ? "en az " : ""}
                {para}
                <span className="ml-1.5 font-normal text-muted-foreground text-[11px]">
                  (`qty × current` çarpımıyla TÜRETİLDİ — uç `market_value` yollamıyor)
                </span>
              </span>
            )}
            {olcum.degeriOlculemeyen.length > 0 ? (
              <span className="mt-0.5 block text-muted-foreground text-[11px]">
                {olcum.degeriOlculemeyen.length} pozisyonun değeri okunamadı ({olcum.degeriOlculemeyen.join(", ")}) —
                toplam bu yüzden &quot;en az&quot;dır, tam değer DEĞİL.
              </span>
            ) : null}
          </dd>
        </dl>

        {olcum.adet === 0 && olcum.neden !== null ? (
          <p className="mt-2 rounded-sm border border-amber-500/40 bg-amber-500/10 p-2 text-[11px] leading-5 text-amber-700 dark:text-amber-400">
            SIFIR &quot;POZİSYON YOK&quot; DEMEK DEĞİL: {olcum.neden}. Boş bir listeye bakıp
            &quot;kapatacak bir şey yok&quot; sonucunu çıkarma.
          </p>
        ) : null}
      </div>

      {/* ---- SUNUCUNUN KENDİ CEVABI · KURU KOŞU ---------------------------- */}
      <div className="mt-2 rounded-md border bg-background p-2.5">
        <h6 className="text-muted-foreground text-[11px] uppercase tracking-wide">
          Ucun kendi cevabı — jetonsuz{" "}
          <code className="font-mono normal-case">POST /api/alpaca/close_all</code> (kuru koşu, hiçbir şeye dokunmaz)
        </h6>
        {kuru.ad === "kosuyor" ? (
          <p className="mt-1.5 flex items-center gap-1.5 text-muted-foreground text-xs">
            <Spinner className="size-3" /> uca soruluyor…
          </p>
        ) : kuru.ad === "okunamadi" ? (
          <p className="mt-1.5 text-xs">
            <Olculemedi neden={kuru.neden} />
            <span className="mt-0.5 block text-muted-foreground text-[11px]">
              Kuru koşu okunamadı; yukarıdaki broker ölçümü tek kaynak kaldı ve{" "}
              <b>hangi pozisyonun SENİN olduğu bilinmiyor</b>. Kapı yine de açık — engellenmek daha
              pahalı olurdu.
            </span>
          </p>
        ) : (
          <dl className="mt-2 grid grid-cols-1 gap-1.5 text-xs sm:grid-cols-[9rem_1fr]">
            <dt className="text-muted-foreground">Düzleştirilecek</dt>
            <dd>
              {kuruListe === null ? (
                <Olculemedi
                  neden="Hangi pozisyonların kapatılacağı bildirilmedi"
                  teknik="yanıt `would_flatten` yazmadı"
                />
              ) : kuruListe.length === 0 ? (
                <span className="text-xs">
                  uç boş liste döndü —{" "}
                  <span className="text-muted-foreground">
                    aynı belirsizlik: `positions()` arızada da boş döner
                  </span>
                </span>
              ) : (
                <span className="font-mono break-words">
                  {kuruListe.length} · {kuruListe.join(" · ")}
                </span>
              )}
            </dd>
            <dt className="text-muted-foreground">Bunların SENİN olanı</dt>
            <dd>
              {kuruYabanci === null ? (
                <Olculemedi
                  neden="Bunlardan hangilerinin senin olduğu bildirilmedi"
                  teknik="yanıt `foreign` yazmadı"
                />
              ) : kuruYabanci.length === 0 ? (
                <span className="text-xs">yok — listedeki her pozisyon motorun emirlerinden doğmuş görünüyor</span>
              ) : (
                <span className="font-mono font-medium break-words text-destructive">
                  {kuruYabanci.length} · {kuruYabanci.join(" · ")}
                </span>
              )}
            </dd>
          </dl>
        )}
        {kuruYabanci !== null && kuruYabanci.length > 0 ? (
          <Alert variant="destructive" className="mt-2">
            <TriangleAlert />
            <AlertTitle>Bu emir SENİN varlığına dokunuyor</AlertTitle>
            <AlertDescription>
              <span className="leading-5">
                {kuruYabanci.join(", ")} motorun açtığı pozisyon(lar) DEĞİL — elle aldıkların. Flatten
                onları da piyasadan kapatır; uç bu ayrımı yapmaz, yalnız BİLDİRİR.
              </span>
            </AlertDescription>
          </Alert>
        ) : null}
      </div>

      {/* ---- JETON YAZIMI --------------------------------------------------- */}
      <div className="mt-3 flex flex-col gap-1.5">
        <Label htmlFor="flatten-jeton" className="text-xs">
          Onaylamak için <code className="font-mono text-[11px]">{FLATTEN_JETON}</code> yaz
        </Label>
        <Input
          id="flatten-jeton"
          value={jeton}
          onChange={(e) => setJeton(e.target.value)}
          disabled={gonderiliyor}
          autoComplete="off"
          spellCheck={false}
          placeholder={FLATTEN_JETON}
          aria-invalid={jeton.trim() !== "" && !jetonTamam}
          className="max-w-64 font-mono"
        />
        <p className="text-muted-foreground text-[11px] leading-4">
          Bu, ucun kendi onay jetonu (<code className="font-mono text-[11px]">alpaca.CLOSE_ALL_CONFIRM</code>) ve
          sorgu parametresi olarak gönderilir. Sembol yazdırmadık: broker okunamadığında hangi sembolün
          yazılacağı bilinemezdi ve ölçüm eksikliği acil durumda operatörü ENGELLERDİ.
        </p>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button type="button" variant="destructive" disabled={gonderiliyor || !jetonTamam} onClick={onGonder}>
          {gonderiliyor ? <Spinner /> : <TriangleAlert aria-hidden />}
          {gonderiliyor ? "Gönderiliyor — bekle" : "EVET, TÜM POZİSYONLARI KAPAT"}
        </Button>
        <Button type="button" variant="ghost" disabled={gonderiliyor} onClick={onVazgec}>
          <Undo2 aria-hidden />
          Vazgeç
        </Button>
        {!jetonTamam ? (
          <span className="flex items-center gap-1.5 self-center text-muted-foreground text-[11px]">
            <CircleAlert className="size-3.5" aria-hidden />
            düğme jeton yazılana kadar kilitli
          </span>
        ) : null}
      </div>
    </div>
  );
}
