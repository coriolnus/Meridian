"use client";

/* ============================================================================
   HAFIZA · ARAMA — ONUNCU DURAĞIN GÖVDESİ (TSK-167 dilim-2, Rol-1 hükmü K7)
   ----------------------------------------------------------------------------
   NE OKUR: `GET /api/arama` — gövdeyi kuran modül `meridian/arama.py::ara`; rota onun
   döndürdüğünü `_auth` + `run_in_threadpool` ile aynen taşıyan ince bir sarmalayıcıdır.

   Rota işleyicisi `api.py::api_arama` (merge sonrası eklendi, 2026-09-08 — Task 2 dalında
   sembol henüz yoktu, çapa yasası çürüyen sayardı; rapor açık kalem 2). Modül çapaları
   (`arama.py::…`) ana dalda çözülür.
   A1'de kurulu
   sqlite-vec + bge-m3 taban indeksi. Kaynak deponun git-HEAD blob'larıdır
   (`manifest_uret.py` korpusu: günlük · `ROADMAP.md%237` · `research/cards` altındaki
   YAML kartları · `docs` altındaki Markdown belgeleri, RUNBOOK hariç), hafıza bankası
   DEĞİL.

   GLOB YAZILMIYOR VE BU BİR ÜSLUP TERCİHİ DEĞİL: `docs` + çift yıldız + `/` dizisi bir
   BLOK YORUMUNU ORTASINDAN KAPATIR (yıldız-eğik çizgi). TypeScript'in sözcük çözücüsü de
   tam orada yorumu bitirir ve gerisi koda dönüşür — `npm run kontrol` kırılır. Bu satır
   ilk yazımda gerçekten öyleydi; kaynak-tarama çivisi (v460 `useApi` yokluğu) onu
   yakaladı, çünkü "yorumda kalması gereken metin" koda sızmıştı.

   ---------------------------------------------------------------------------
   BANKA SEÇİCİSİ BU GÖRÜNÜMÜ ETKİLEMEZ — VE BU EKRANDA YAZILI (Rol-1 hükmü K3)
   ---------------------------------------------------------------------------
   Kabuk (`HafizaYuzey.tsx`) her görünümün üstüne bir "Banka" seçicisi çiziyor ve o
   seçici bu görünümde HİÇBİR ŞEYİ değiştirmiyor. İki yol vardı: kabuğun seçiciyi
   görünüm bazında gizlemesi (kabuk değişikliği, ayrı dilim) ya da görünümün
   etkisizliği BEYAN ETMESİ. K3 ikincisini seçti — ve beyan bir süs değil: sessizce
   yok saymak, operatöre etkisi olmayan bir denetim göstermek olurdu ("çalıştırdım,
   hiçbir şey değişmedi, nedenini kimse yazmamış" sınıfı).

   Gövde bu yüzden `bank` özelliğini HİÇ okumaz (çivili) — beyan kendi kodunu
   yalanlayamaz.

   ---------------------------------------------------------------------------
   YOKLAMA YOK — SORGU OPERATÖR EYLEMİYLE KOŞAR
   ---------------------------------------------------------------------------
   Kardeş görünümlerin çoğu `useApi(yol, periyot)` ile 15/30 sn'de bir okuyor. Burada
   o kanca BİLEREK yok: her sorgu A1'in 4 OCPU'sunda yeni bir `onnxruntime`
   oturumu kurar (soğuk açılış maliyeti bu dilimde HÂLÂ ÖLÇÜLMEDİ — Görev 3'ün ilk
   gerçek A1 sorgusu ölçecek). Yoklama, kimsenin bakmadığı bir ekran için dakikada
   dört ONNX oturumu demekti.

   Bedeli ödenen şey de yazılı: liste kendiliğinden tazelenmez. İndeks zaten HAFTALIK
   tazeleniyor (Pazar 08:15Z `hindsight-taban-tazele.timer`), yani 30 saniyelik bir
   yoklamanın getireceği yeni bilgi ÖLÇÜLEBİLİR BİÇİMDE SIFIRDI.

   ---------------------------------------------------------------------------
   BELGE AÇILMAZ — VE BU DA BEYAN
   ---------------------------------------------------------------------------
   `/api/belge?yol=` diye bir uç YOKTUR (ölçüldü 2026-09-08). Satırı tıklanabilir
   yapmak olmayan bir yeteneği var göstermek olurdu; satır bunun yerine yolunu
   KOPYALATIR. `ROADMAP.md%237` sonucu ROADMAP yüzeyine derin bağ da TAŞIMAZ: kesitin
   document_id'si bir sayfa çapası değildir ve bağ operatörü doğru sayfanın yanlış
   yerine götürürdü. Belge görüntüleyici AYRI DİLİM.
   ============================================================================ */
import { useEffect, useRef, useState } from "react";
import { FileSearch } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { OturumHatasi, apiGet } from "../../veri";
import { BolumKart, Olculemedi } from "../sistem/parcalar";
import { Bolme, Secim, secimDegeri } from "./parcalar";
import {
  ARAMA_UC,
  DOSYA_SECENEKLERI,
  ISABET_BEYANI,
  K_SECENEKLERI,
  VARSAYILAN_K,
  type AramaSatiri,
  type AramaZarfi,
  aramaIstegiAbone,
  aramaIstegiAl,
  aramaYolu,
  durumCoz,
  kirpmaFarki,
} from "./aramaMantigi";
import type { GorunumOzellikleri } from "./gorunumler";

/* --------------------------------------------------------------------------- */

/** İndeks künyesi — bayatlık ROZETTE, çünkü bu liste "canlı depo" DEĞİLDİR.
 *
 *  DEĞERLER DİZGE (`arama.ts::AramaKunyesi` şerhi): hiçbiri sayı gibi
 *  biçimlendirilmez — `toLocaleString` sessizce `NaN` basardı. */
function Kunye({ kunye }: { readonly kunye: AramaZarfi["kunye"] }) {
  if (kunye === undefined || kunye === null) {
    return (
      <Olculemedi
        neden="İndeks künyesi gelmedi"
        teknik="uç künye alanını döndürmedi — sonucun hangi depo anına ait olduğu okunamıyor"
        kisa
      />
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      {kunye.head_commit ? (
        <Badge variant="outline" className="font-mono text-[11px]" title="İndeksin kurulduğu depo anı">
          HEAD {kunye.head_commit}
        </Badge>
      ) : (
        <Olculemedi neden="İndeksin commit'i bildirilmedi" teknik="head_commit alanı boş" kisa />
      )}
      {kunye.uretim_ts ? (
        <Badge variant="outline" className="font-mono text-[11px]">
          üretim {kunye.uretim_ts}
        </Badge>
      ) : null}
      {kunye.chunk_sayisi ? (
        <Badge variant="outline" className="font-mono text-[11px]">
          {kunye.chunk_sayisi} kesit
        </Badge>
      ) : null}
    </div>
  );
}

/** Tek sonuç satırı. Mesafe HAM basılır (`Recall.tsx`in ölçülmüş gerekçesi:
 *  `0,001125` ile `0,001004` yuvarlandığında ikisi de "0,001" olur ve sıralamanın
 *  niçin böyle olduğu okunamaz hâle gelir). */
function Satir({
  satir,
  sira,
  kopyala,
  kopya,
}: {
  readonly satir: AramaSatiri;
  readonly sira: number;
  readonly kopyala: (yol: string) => void;
  readonly kopya: { readonly yol: string; readonly ok: boolean } | null;
}) {
  const yol = typeof satir.dosya === "string" && satir.dosya !== "" ? satir.dosya : null;
  const fark = kirpmaFarki(satir);
  const bunun = kopya !== null && yol !== null && kopya.yol === yol ? kopya : null;

  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-start gap-3">
        <span className="w-6 shrink-0 text-center font-medium text-muted-foreground text-xs tabular-nums">
          {sira}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            {yol === null ? (
              <Olculemedi neden="Yol gelmedi" teknik="dosya alanı boş ya da dizge değil" kisa />
            ) : (
              <code className="min-w-0 break-all font-mono text-sm">{yol}</code>
            )}
            {satir.bolum ? (
              <span className="truncate text-muted-foreground text-xs" title={satir.bolum}>
                {satir.bolum}
              </span>
            ) : null}
            {typeof satir.mesafe === "number" ? (
              <span className="font-mono text-[11px] text-muted-foreground" title="Ham mesafe — yuvarlanmaz">
                mesafe {String(satir.mesafe)}
              </span>
            ) : (
              <Olculemedi neden="Mesafe gelmedi" teknik="mesafe alanı sayı değil — sıralama okunamaz" kisa />
            )}
          </div>

          {typeof satir.kesit === "string" && satir.kesit !== "" ? (
            <p className="mt-2 whitespace-pre-wrap text-sm">{satir.kesit}</p>
          ) : (
            <div className="mt-2">
              <Olculemedi neden="Kesit gelmedi" teknik="kesit alanı boş ya da dizge değil" kisa />
            </div>
          )}

          {/* KIRPMA BEDELİ GÖRÜNÜR (bedel yasası): uç kesiti 600 karakterde kırpıyor ve
              bunu `kesit_kirpildi` + `metin_uzunluk` ile beyan ediyor. Ekran o beyanı
              çizmezse kırpma görünmez olur ve operatör kesik bir kesiti TAM sanar.
              Fark hesaplanamıyorsa SAYI UYDURULMAZ — bayrak yine de yazılır. */}
          {satir.kesit_kirpildi === true ? (
            <p className="mt-1 text-[11px] text-muted-foreground">
              {fark === null
                ? "kesit kırpıldı — kaç karakterin görünmediği ölçülemedi (tam uzunluk gelmedi)"
                : `kesit kırpıldı — …(+${fark} karakter) ekranda yok`}
            </p>
          ) : null}

          <div className="mt-2 flex flex-wrap items-center gap-2">
            {satir.blob_sha ? (
              <Badge variant="outline" className="font-mono text-[10px]" title="Kesitin geldiği git blob'u">
                blob {satir.blob_sha}
              </Badge>
            ) : null}
            {typeof satir.metin_uzunluk === "number" ? (
              <span className="font-mono text-[10px] text-muted-foreground tabular-nums">
                tam uzunluk {satir.metin_uzunluk}
              </span>
            ) : null}
            {yol === null ? null : (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-6 px-2 text-[11px]"
                onClick={() => kopyala(yol)}
              >
                Yolu kopyala
              </Button>
            )}
            {bunun === null ? null : bunun.ok ? (
              <span className="text-[11px] text-muted-foreground">kopyalandı</span>
            ) : (
              <span className="text-[11px] text-muted-foreground">
                kopyalanamadı — yol yukarıda seçilebilir duruyor (tarayıcı pano iznini vermedi
                ya da bağlam güvenli değil)
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function Arama({ kayit }: GorunumOzellikleri) {
  const [soru, setSoru] = useState("");
  const [k, setK] = useState<number>(VARSAYILAN_K);
  const [dosya, setDosya] = useState("");

  const [zarf, setZarf] = useState<AramaZarfi | null>(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState<string | null>(null);
  const [oturumDustu, setOturumDustu] = useState(false);
  const [soruldu, setSoruldu] = useState(false);
  const [kopya, setKopya] = useState<{ readonly yol: string; readonly ok: boolean } | null>(null);

  const kutu = useRef<HTMLInputElement | null>(null);
  const iptal = useRef<AbortController | null>(null);

  /* ⌘K DEVRİ: METİN TAŞINIR, SORGU ATEŞLENMEZ (`arama.ts` istek kutusu şerhi).
     Palet "Belgelerde ara…" komutunda yazılmış metni bırakır; burada tüketilir,
     kutuya yazılır ve odak verilir. Gönderme kararı operatörün İKİNCİ eylemidir —
     paletin "hızlı erişim ≠ icra" hükmü, artı her tuş vuruşunda bir ONNX süreci
     doğurmama gerekçesi. */
  useEffect(() => {
    const uygula = () => {
      const istek = aramaIstegiAl();
      if (istek === null) return;
      if (istek.taslak !== null) setSoru(istek.taslak);
      kutu.current?.focus();
    };
    uygula();
    return aramaIstegiAbone(uygula);
  }, []);

  /* SON İSTEK KAZANIR: operatör ikinci kez "Ara"ya bastığında birinci turun yanıtı
     hâlâ yoldadır ve onu yazmak, ESKİ sorgunun sonucunu YENİ sorgunun başlığı altında
     bırakırdı (`veri.ts`in bayat-gövde sınıfının aynısı, burada elle). */
  const ara = async () => {
    if (soru.trim() === "") return;
    iptal.current?.abort();
    const kontrol = new AbortController();
    iptal.current = kontrol;
    setYukleniyor(true);
    setHata(null);
    setOturumDustu(false);
    setSoruldu(true);
    setKopya(null);
    try {
      const g = await apiGet<AramaZarfi>(aramaYolu(soru, k, dosya), kontrol.signal);
      if (kontrol.signal.aborted) return;
      setZarf(g);
    } catch (e: unknown) {
      if (kontrol.signal.aborted) return;
      if (e instanceof OturumHatasi) {
        setOturumDustu(true);
        setZarf(null);
      } else {
        setHata(e instanceof Error ? e.message : String(e));
      }
    } finally {
      if (!kontrol.signal.aborted) setYukleniyor(false);
    }
  };

  /* PANO API'Sİ HER BAĞLAMDA YOK: güvensiz bağlamda (`http://`) `navigator.clipboard`
     tanımsızdır. Sessizce hiçbir şey yapmak yerine BAŞARISIZLIK yazılıyor — yol zaten
     ekranda seçilebilir duruyor, yani telafi de görünür. */
  const kopyala = (yol: string) => {
    const pano = typeof navigator === "undefined" ? undefined : navigator.clipboard;
    if (pano === undefined) {
      setKopya({ yol, ok: false });
      return;
    }
    void pano.writeText(yol).then(
      () => setKopya({ yol, ok: true }),
      () => setKopya({ yol, ok: false }),
    );
  };

  const durum = zarf === null ? null : durumCoz(zarf);

  return (
    <BolumKart kimlik="hafiza-arama" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-[18rem] flex-1 flex-col gap-1">
            <span className="text-muted-foreground text-xs">Soru</span>
            <span className="relative">
              <FileSearch
                className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
                aria-hidden
              />
              <Input
                ref={kutu}
                value={soru}
                onChange={(e) => setSoru(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void ara();
                }}
                placeholder="belgelerde aranacak soru"
                className="h-9 pl-8"
              />
            </span>
          </label>
          <Button
            type="button"
            className="h-9"
            disabled={yukleniyor || soru.trim() === ""}
            onClick={() => void ara()}
          >
            {yukleniyor ? "Aranıyor…" : "Ara"}
          </Button>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          {/* `k` YALNIZ 5/10 (Rol-1 hükmü K6): API tavanı 20 ama pano onu SUNMAZ —
              gerekçe `arama.ts::K_SECENEKLERI` şerhinde, buraya kopyalanmıyor. */}
          <Secim
            etiket="Kaç sonuç"
            deger={String(k)}
            setDeger={(d) => {
              const n = Number.parseInt(d, 10);
              if (Number.isFinite(n)) setK(n);
            }}
            secenekler={K_SECENEKLERI.map((n) => ({ deger: String(n), etiket: `${n} sonuç` }))}
            genislik="w-32"
          />
          {/* KAPALI LİSTE, SUNUCUNUN BEYAZ LİSTESİNİN ALT KÜMESİ (`arama.ts` şerhi):
              liste dışı bir önek uçta 400 olur ve düğme çalışır görünüp reddedilirdi. */}
          <Secim
            etiket="Yol öneki"
            deger={dosya === "" ? "__hepsi" : dosya}
            setDeger={(d) => setDosya(secimDegeri(d))}
            secenekler={DOSYA_SECENEKLERI.map((s) => ({ deger: s.deger, etiket: s.etiket }))}
            genislik="w-56"
          />
        </div>

        {/* OKUMA TALİMATI — SAYI TEK KAYNAKTAN (`arama.ts::ISABET_BEYANI`). Ekrana elle
            ikinci bir oran yazılmaz: ölçüm yenilendiği gün iki kopyadan biri sessizce
            bayatlardı. */}
        <p className="text-muted-foreground text-[11px]">{ISABET_BEYANI}</p>
      </div>

      {/* BANKA SEÇİCİ BEYANI (Rol-1 hükmü K3) — dosya başlığındaki gerekçe. */}
      <div className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
        <span className="font-medium">Banka seçicisi bu görünümü etkilemez: </span>
        arama hafıza bankasına değil, deponun git-HEAD blob'larından haftalık kurulan
        sqlite-vec taban indeksine sorulur. Yukarıdaki seçici hangi bankada olursa olsun aynı
        sonuç döner; seçiciyi görünüm bazında gizlemek bir kabuk değişikliğidir ve ayrı bir
        dilime bırakıldı. Belge açılmaz — pano bir belge görüntüleyici ucu taşımıyor (ölçüldü);
        satırların yolu kopyalanabilir, yol haritası sonucu da yol haritası yüzeyine bağ taşımaz.
      </div>

      {oturumDustu ? (
        <Olculemedi neden="Oturum düştü" teknik={`${ARAMA_UC} 401 döndü — çaresi yeniden giriş`} />
      ) : hata !== null ? (
        <Olculemedi neden="Arama okunamadı" teknik={hata} />
      ) : !soruldu ? (
        <p className="text-muted-foreground text-sm">
          Henüz aranmadı — boş bir soru uca hiç gitmez, yani bu ekran bir ölçüm sonucu
          göstermiyor. Sorgu kendiliğinden tazelenmez: her arama A1'de yeni bir gömme oturumu
          kurar, o yüzden yoklama YOK.
        </p>
      ) : yukleniyor ? (
        <p className="text-muted-foreground text-sm">Aranıyor…</p>
      ) : durum === null ? null : durum.tur === "mesgul" ? (
        /* MEŞGUL AYRI HÂL VE `neden`DEN ÖNCE ÇÖZÜLÜR (`arama.ts::durumCoz` sözleşmesi):
           bu dalda `neden` DE doludur; sırayı ters çevirmek meşgul hâlini "Ölçülemedi"
           diye çizerdi ve operatör başka bir aramanın koştuğunu öğrenemezdi. */
        <div className="rounded-md border border-dashed p-3 text-sm">
          <span className="font-medium">Başka bir arama koşuyor. </span>
          Aynı anda tek arama çalışır (uç bir kilit tutuyor) — ikinci istek süreç doğurmadan
          döndü. Teknik gerekçe: <span className="font-mono text-xs">{durum.neden}</span>
        </div>
      ) : durum.tur === "olculemedi" ? (
        <Olculemedi neden="Arama ölçülemedi" teknik={durum.neden} />
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="tabular-nums">
              {durum.tur === "bos" ? 0 : durum.satirlar.length} sonuç
            </Badge>
            {typeof zarf?.sure_s === "number" ? (
              <Badge variant="outline" className="tabular-nums">
                {String(zarf.sure_s)} sn
              </Badge>
            ) : null}
            {/* KORPUS DIŞI SATIR SESSİZCE YUTULMAZ: uç süzgeci düşürdüğü satırların
                sayısını beyan ediyor; ekran o sayıyı yutarsa süzgeç görünmez olur. */}
            {typeof zarf?.korpus_disi_n === "number" && zarf.korpus_disi_n > 0 ? (
              <Badge variant="outline" className="tabular-nums">
                {zarf.korpus_disi_n} satır korpus dışı — düşürüldü
              </Badge>
            ) : null}
          </div>

          <Bolme
            baslik="İndeks künyesi"
            aciklama="İndeks HAFTALIK tazelenir (Pazar 08:15Z); aşağıdaki sonuçlar bu depo anına aittir, çalışma ağacına DEĞİL."
          >
            <Kunye kunye={zarf?.kunye} />
          </Bolme>

          <Bolme
            baslik="Sonuçlar"
            aciklama="Sıra taban indeksinin mesafesidir; ekran yeniden sıralamaz ve yol açmaz."
          >
            {durum.tur === "bos" ? (
              <p className="text-muted-foreground text-sm">
                Bu soru indekse soruldu ve dönen liste BOŞ. Eşik yok, sıralama saf mesafedir —
                yani bir eşiğin altında kalan aday elenmedi, indeks gerçekten hiçbir kesit
                döndürmedi. Yol öneki seçiliyse süzgeç istemci tarafında uygulanır ve az sonuç
                NORMALDİR.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {durum.satirlar.map((s, i) => (
                  <Satir
                    key={`${s.dosya ?? "yolsuz"}-${s.blob_sha ?? i}-${i}`}
                    satir={s}
                    sira={i + 1}
                    kopyala={kopyala}
                    kopya={kopya}
                  />
                ))}
              </div>
            )}
          </Bolme>
        </div>
      )}
    </BolumKart>
  );
}
