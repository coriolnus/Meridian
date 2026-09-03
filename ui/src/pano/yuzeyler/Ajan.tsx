"use client";

/* ============================================================================
   AJAN — "ajana ne sorabilirim, ne cevap verdi?"
   ----------------------------------------------------------------------------
   BU YÜZEYİN İLK CÜMLESİ BİR HAYIRDIR: sorunun ilk yarısına ("ne sorabilirim")
   bugünkü cevap YOK. `meridian/api.py`nin 78 rotası tarandı (2026-08-25) —
   panodan ajana serbest metin gönderen bir uç bulunmuyor. En yakın uçlar mesaj
   değil kumandadır (`POST /api/hermes/reflect` gövdesiz tetik;
   `POST /api/hermes/{action}` yalnız start|stop|backfill|sync_integrations).
   Bu yüzden yazma şeridi ÇİZİLİYOR ama KİLİTLİ ve nedeni şeridin içinde yazıyor
   (`SohbetHatti.tsx::YazmaSeridi` — ÇAPA GÜNCELLENDİ 2026-08-31: `YazmaSeridi.tsx`
   diye ayrı bir dosya bu turda kuruldu ve aynı turda konsolide edilip SİLİNDİ;
   `Filo.tsx:35` doğru sembolü yazıyordu, iki şerh ayrışmıştı — inceleme Ö-8).
   Çalışırmış gibi duran bir metin alanı, panonun
   kurabileceği en sinsi yalandır: operatör yazar, gönderir, cevap bekler —
   beklediği şey hiç olmamıştır.

   İKİ MUHATAP, İKİ KAYNAK, TEK GERÇEK — ve bu yüzey onları AYNI KABUKTA ama
   AYRI muhataplar olarak tutar (mesajlaşma grameri, onaylı maket 2026-08-31):
     · #öneri-hattı — `state/hypotheses.jsonl`. Konuşan taraf ÖNERİ ÜRETECİdir
       (`rationale`) ve cevap veren backtest/bekçi KAPISIdır (`status`).
       Uçları: `/api/agent` (karne + hipotezler + kalibrasyon) ve `/api/memory`
       (yalnız `lessons_md`). Hipotez dizisi İKİSİNDE DE var ve aynı kaynaktan
       geliyor (`memory.all_hypotheses()`); sohbet `/api/agent`inkini kullanıyor.
       İki listeyi birleştirmek, aynı deftere iki gerçek uydurmak olurdu.
     · @sef · @bekci · @karne · ana beyin — `GET /api/ajanlar`, yani
       `~/.hermes` altındaki `state.db` konuşma defterleri + teslim olayları.
   İki kaynak aynı sol listede yan yana durur ama BİRLEŞMEZ: biri düşerse öteki
   çizilmeye devam eder ve her muhatap kendi hükmünü kendi taşır.

   ÜÇ HÜKÜM ÜÇ AYRI YERDE (ucun sözleşmesi, korundu):
     · liste `ok`/`hata`  → sol sütunun ÜSTÜNDEKİ ince şerit (`Filo.tsx::HukumSeridi`)
     · ajan `durum`       → o muhatabın Sohbet panelindeki ölçülemedi hâli
     · `teslimler`        → AYRI kaynak; Teslimler sekmesi kendi hükmünü verir

   NABIZ YOK (periyot 0): bu defterler gün içinde saniyede bir değişmiyor — bir
   yansıma turu dakikalar sürüyor. 15 saniyede bir çekmek, okunan bir sohbeti
   altından kaydırmak demekti. Tazeleme elde: üst bardaki düğme.

   ESKİ DERİN BAĞLAR KIRILMADI ve eşleme `gramer.ts::rotaEsle`te ölçülüyor:
   `…/chat/sohbet|defter|olcum` → #öneri-hattı'nın üç sekmesi, `…/chat/filo` →
   son seçili ajan (yoksa @sef, yoksa ilk ajan). Yeni kanonik biçim tek segmentte
   iki bilgi taşır: `<muhatap>.<sekme>`. Kenar çubuğu kaydı (`alanlar.ts`) ESKİ
   dört kimliği taşımaya devam ediyor — o kimlikler hem gezinmenin hem v288
   parite çivisinin çapası ve bu panellerde `id="bolum-*"` olarak duruyorlar.
   ============================================================================ */
import { useEffect, useMemo, useRef, useState } from "react";

import { Info, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverHeader, PopoverTitle, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

import { YUZEYLER } from "../alanlar";
import { useRota, useRouter } from "../rota";
import { useApi } from "../veri";
import { Filo, KaynakOzeti, SahipsizPaneli } from "./ajan/Filo";
import { Grafikler } from "./ajan/Grafikler";
import { HipotezDefteri } from "./ajan/HipotezDefteri";
import { KanalAkisi, YazmaSeridi } from "./ajan/SohbetHatti";
import { Yanliste, type Onizleme } from "./ajan/Yanliste";
import { filoOku } from "./ajan/filoOku";
import {
  KANAL_DILIMI,
  SAHIPSIZ_DILIMI,
  SEKME_ETIKET,
  SEKME_TAKIMI,
  mesajToplami,
  muhataplar,
  muhatapSec,
  listeSuz,
  penceredekiModeller,
  rotaEsle,
  rotaYaz,
  sekmeSec,
  sonTeslimTs,
  type Muhatap,
  type SekmeAdi,
} from "./ajan/gramer";
import { Kapi, Olculemedi, bicimSayi, dizi, hipotezOku, metin, nesne, say, zamanMetni, type Hipotez } from "./ajan/ortak";
import { bolumOzeti, hafizaAyristir } from "./hafiza/damitim";

const KANAL_ADI = "#öneri-hattı";

/** ESKİ KAYIT KİMLİKLERİNİN ÇAPALARI — TEK KAYNAK.
 *
 *  `alanlar.ts`teki `chat` yüzeyi hâlâ dört bölüm kaydediyor: "sohbet" · "defter" ·
 *  "olcum" · "filo". Kayıt DEĞİŞMEDİ çünkü iki ayrı sözleşme oraya bakıyor: kenar
 *  çubuğu bu dört adrese bağ üretiyor ve v288 paritesi her kayıtlı kimliğin ekranda
 *  bir `bolum-<kimlik>` çapası olmasını arıyor. Yeni gramerde bu adlar birer SEKME
 *  değil, birer İÇERİK: üçü kanalın panelleri, dördüncüsü ajan tarafı. Eşleme
 *  `gramer.ts::rotaEsle`te ve orada çivili. */
const CAPA = {
  "sohbet": "bolum-sohbet",
  "defter": "bolum-defter",
  "olcum": "bolum-olcum",
  "filo": "bolum-filo",
} as const;

/** Sekme çubuğunun `aria-controls` hedefi. Panel kabı TEK ve sekmeye göre içeriği
 *  değişiyor; kimlik bu yüzden sabit (her sekmeye ayrı `id` vermek, o an DOM'da
 *  olmayan bir kimliği işaret eden `aria-controls` üretirdi). */
const PANEL_KIMLIGI = "ajan-panel";

export function Ajan() {
  const y = YUZEYLER.chat;
  const { bolum } = useRota();
  const { push: git } = useRouter();
  const ajan = useApi<Record<string, unknown>>("/api/agent", 0);
  const hafiza = useApi<Record<string, unknown>>("/api/memory", 0);
  // BEDEL BEYANI: bu uç sekme açık olmasa da yüzey açılışında BİR KEZ çekiliyor.
  // Kaba tavan varsayılan yolda ≈240 KB (600 karakter × 20 mesaj × 5 oturum × 4 ajan)
  // ve bedeli her Ajan yüzeyi ziyaretinde ödeniyor. Sekmeye göre koşullu çekmek
  // ucuz görünüyordu ama `useApi` yolu `null`ken `yukleniyor: false` başlıyor —
  // sekme açıldığı KARE boyunca kapı "okunamadı" derdi, yani sağlıklı bir uç
  // arızalı görünürdü. Yanlış alarm, tasarruftan pahalıdır. Yeni kabukta bu ucun
  // yükü ZATEN açılışta gerekli: sol liste onsuz çizilemez.
  const filo = useApi<Record<string, unknown>>("/api/ajanlar", 0);

  const [arama, setArama] = useState("");
  const [sonAjan, setSonAjan] = useState<string | null>(null);
  // AKTİFLİK ÇAPASI DURUMDA TUTULUYOR, `Date.now()` çağrısı çizim içinde DEĞİL:
  // her yeniden çizimde saati yeniden okusaydık "bugün" hükmü kaydırma sırasında
  // bile değişebilirdi ve saf fonksiyon çivilenemezdi. Tazeleme çapayı yeniler.
  const [simdiMs, setSimdiMs] = useState(() => Date.now());

  const yuk = useMemo(() => (filo.veri === null ? null : filoOku(filo.veri)), [filo.veri]);

  const hipotezler: readonly Hipotez[] = useMemo(() => {
    const ham = dizi(ajan.veri?.["hypotheses"]);
    return ham.map(hipotezOku).filter((h): h is Hipotez => h !== null);
  }, [ajan.veri]);

  const hafizaMetni = metin(hafiza.veri?.["lessons_md"]);
  const cozulmusHafiza = useMemo(() => (hafizaMetni === null ? null : hafizaAyristir(hafizaMetni)), [hafizaMetni]);

  const tumListe = useMemo(
    () => muhataplar(yuk === null ? null : yuk.ajanlar, KANAL_ADI),
    [yuk],
  );
  const hedef = rotaEsle(bolum);
  const sahipsizAcik = hedef.muhatap === SAHIPSIZ_DILIMI;
  // SEÇİM TÜM LİSTEDEN YAPILIR, SÜZÜLMÜŞTEN DEĞİL: arama kutusuna yazmak açık
  // sohbeti kapatmamalı — süzgeç listeyi daraltır, muhatabı düşürmez.
  // `listeOlculdu` AYRI TAŞINIR (inceleme Ö-2): roster okunamadığında HER ajan derin
  // bağı "listede yok" kovasına düşerdi ve ekran yanlış teşhis koyardı.
  const secim = muhatapSec(
    tumListe,
    sahipsizAcik ? KANAL_DILIMI : hedef.muhatap,
    sonAjan,
    yuk !== null && yuk.ajanlar !== null,
  );
  const secili = secim.muhatap;
  const seciliTur = sahipsizAcik ? "sahipsiz" : (secili?.tur ?? "kanal");
  const sekme = sekmeSec(seciliTur, hedef.sekme);

  useEffect(() => {
    // Derin bağla bir ajana girildiğinde "son seçili ajan" hafızası da güncellenir;
    // yoksa eski `…/chat/filo` bağı hep @sef'e düşerdi.
    if (!sahipsizAcik && secili !== null && secili.tur === "ajan") setSonAjan(secili.dilim);
  }, [sahipsizAcik, secili]);

  // EN YENİ MESAJA İNİŞ, ELLE (bedel beyanı): eski kabuk `MessageScroller`ın
  // `autoScroll`unu kullanıyordu; yeni kabukta kaydırma kabı sağ panelin kendisi
  // ve o bileşen artık akışı sarmıyor. İnişi düşürmek, sohbeti hep en ESKİ
  // mesajda açmak olurdu — mesajlaşma grameri en yeniyi bekler. Veri sonradan
  // geldiği için `ajan.veri`/`filo.veri` de bağımlılık: ilk karede akış boştur.
  const akisKabi = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (sekme !== "sohbet") return;
    const el = akisKabi.current;
    if (el === null) return;
    el.scrollTop = el.scrollHeight;
    // `secili` kimliği `tumListe` belleğinden geliyor (`useMemo`), yani muhatap
    // gerçekten değişmedikçe sabit — bu bağımlılık döngü kurmaz.
  }, [sekme, secili, ajan.veri, filo.veri]);

  const gitMuhatap = (m: Muhatap) => {
    if (m.tur === "ajan") setSonAjan(m.dilim);
    git(rotaYaz(m.dilim, sekmeSec(m.tur, "sohbet")));
  };
  const gitSekme = (s: SekmeAdi) => {
    git(rotaYaz(sahipsizAcik ? SAHIPSIZ_DILIMI : (secili?.dilim ?? KANAL_DILIMI), s));
  };

  // ÖNİZLEME AKIŞLA AYNI "SON"U GÖSTERİR (inceleme Kü-8): eskiden dizinin SON öğesi
  // alınıyordu, oysa akış (`SohbetHatti::damga`) damgaya göre sıralıyor. JSONL ekleme
  // sırası `ts` sırasından ayrışırsa sol listedeki önizleme ile akışın son balonu
  // FARKLI satırı gösterirdi — aynı gerçeğin iki kopyası, sessizce ayrışan.
  const kanalOnizlemesi: Onizleme = useMemo(() => {
    if (ajan.veri === null) {
      return { metin: ajan.hata ?? "öneri defteri henüz okunmadı", uyari: true };
    }
    if (hipotezler.length === 0) return { metin: "defter okundu, öneri kaydı yok", uyari: false };
    let son: Hipotez | undefined;
    let enTs = Number.NEGATIVE_INFINITY;
    for (const h of hipotezler) {
      // Damgasız satır akışta SONA düşüyor; burada da en yeni sayılmaz.
      const t = h.ts === null ? Number.NEGATIVE_INFINITY : Date.parse(h.ts);
      const ts = Number.isNaN(t) ? Number.NEGATIVE_INFINITY : t;
      if (son === undefined || ts >= enTs) {
        son = h;
        enTs = ts;
      }
    }
    return { metin: son?.gerekce ?? son?.degisken ?? "son önerinin gerekçesi okunamadı", uyari: false };
  }, [ajan.veri, ajan.hata, hipotezler]);

  // SÜZGEÇ KANALI DA ÖNİZLEMESİNDEN GÖRÜR ve AÇIK SOHBET MUAFTIR (inceleme Ö-6).
  const gorunenListe = useMemo(
    () => listeSuz(tumListe, arama, kanalOnizlemesi.metin, sahipsizAcik ? null : (secili?.dilim ?? null)),
    [tumListe, arama, kanalOnizlemesi.metin, sahipsizAcik, secili],
  );

  return (
    <div className="flex min-h-0 flex-col">
      <div className="flex h-[calc(100dvh-var(--dashboard-header-height)-4rem)] min-h-[34rem] flex-col overflow-hidden rounded-xl border bg-background">
        {/* ---- ÜST BAR ---- */}
        <div className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b bg-card px-4 py-2 sm:px-6">
          <h1 className="font-semibold text-sm tracking-tight">{y.baslik}</h1>
          <p className="min-w-0 text-muted-foreground text-xs">{y.soru}</p>
          <div className="ml-auto flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => {
                ajan.tazele();
                hafiza.tazele();
                filo.tazele();
                setSimdiMs(Date.now());
              }}
            >
              <RefreshCw className="size-3.5" aria-hidden />
              Tazele
            </Button>
            <Popover>
              <PopoverTrigger
                aria-label="Hangi defterler okundu?"
                className="grid size-7 place-items-center rounded-full border bg-muted/40 text-muted-foreground transition-colors hover:text-foreground"
              >
                <Info className="size-3.5" aria-hidden />
              </PopoverTrigger>
              <PopoverContent align="end" className="w-[22rem] max-w-[calc(100vw-2rem)]">
                <PopoverHeader>
                  <PopoverTitle>Hangi defterler okundu?</PopoverTitle>
                </PopoverHeader>
                {yuk === null ? (
                  <p className="text-xs">
                    <Olculemedi
                      neden="kaynak künyesi okunamadı, hangi defterlerin tarandığı söylenemez"
                      teknik="`/api/ajanlar` gövdesi yok — uç düştü ya da henüz çekilmedi"
                    />
                  </p>
                ) : (
                  <KaynakOzeti yuk={yuk} />
                )}
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* ---- GÖVDE ---- */}
        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          <Yanliste
            liste={gorunenListe}
            seciliDilim={sahipsizAcik ? null : (secili?.dilim ?? null)}
            sec={gitMuhatap}
            arama={arama}
            aramaDegisti={setArama}
            filo={filo}
            yuk={yuk}
            kanalOnizlemesi={kanalOnizlemesi}
            simdiMs={simdiMs}
            sahipsizAc={() => git(rotaYaz(SAHIPSIZ_DILIMI, "teslimler"))}
            sahipsizSecili={sahipsizAcik}
          />

          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            <Baslik
              sahipsiz={sahipsizAcik}
              m={secili}
              hipotezN={hipotezler.length}
              sekme={sekme}
              sekmeSecildi={gitSekme}
            />

            {/* İKİ AYRI TEŞHİS, İKİ AYRI CÜMLE (inceleme Ö-2): "bu ad listede yok"
                ile "listeyi hiç okuyamadım" aynı şey değildir. İkisini tek cümleye
                indirmek, uç düştüğünde operatöre SAĞLAM bir yer imini sildirirdi. */}
            {secim.bulunamayan === null ? null : secim.listeOlculemedi ? (
              <p className="shrink-0 border-uyari-h border-b bg-uyari-t px-4 py-1.5 text-[11px] text-uyari sm:px-6">
                Ajan listesi okunamadı, bu adresin karşılığı ölçülemedi:{" "}
                <code className="font-mono">{secim.bulunamayan}</code> — adres yanlış OLMAYABİLİR;
                okunamayan şey listenin kendisi. Yer imini silme, tazelemeyi dene.
              </p>
            ) : (
              <p className="shrink-0 border-uyari-h border-b bg-uyari-t px-4 py-1.5 text-[11px] text-uyari sm:px-6">
                Ajan listesi okundu ve istenen muhatap içinde yok:{" "}
                <code className="font-mono">{secim.bulunamayan}</code> — bunun yerine öneri hattı
                açıldı. Bağ eski bir ada işaret ediyor olabilir.
              </p>
            )}

            <div
              ref={akisKabi}
              id={PANEL_KIMLIGI}
              role="tabpanel"
              aria-labelledby={`ajan-sekme-${sekme}`}
              className="flex min-h-0 flex-1 flex-col overflow-y-auto"
            >
              <Govde
                sahipsiz={sahipsizAcik}
                m={secili}
                sekme={sekme}
                ajanDurumu={ajan}
                filoDurumu={filo}
                yuk={yuk}
                hipotezler={hipotezler}
                hafizaBasliklari={cozulmusHafiza === null ? [] : bolumOzeti(cozulmusHafiza)}
                hafizaOlculemediNedeni={
                  hafiza.oturumDustu
                    ? "`/api/memory` 401 döndü — oturum düştü"
                    : hafizaMetni === null
                      ? (hafiza.hata ?? "`/api/memory` gövdesinde `lessons_md` alanı yok ya da boş")
                      : cozulmusHafiza?.bosBeyani === true
                        ? "uç `_No lessons yet._` döndü — `state/lessons.md` dosyası yok"
                        : null
                }
                arama={arama}
                teslimleriAc={() => gitSekme("teslimler")}
              />
            </div>

            {sekme === "sohbet" ? <YazmaSeridi hal={seciliTur === "kanal" ? "kanal" : "ajan"} /> : null}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- MUHATAP BAŞLIĞI ------------------------------------------------------ */

function Baslik({
  sahipsiz,
  m,
  hipotezN,
  sekme,
  sekmeSecildi,
}: {
  sahipsiz: boolean;
  m: Muhatap | null;
  hipotezN: number;
  sekme: SekmeAdi;
  sekmeSecildi: (s: SekmeAdi) => void;
}) {
  const tur = sahipsiz ? "sahipsiz" : (m?.tur ?? "kanal");
  const takim = SEKME_TAKIMI[tur];
  const a = sahipsiz ? null : (m?.ajan ?? null);
  const teslimTs = a === null ? null : sonTeslimTs(a);
  const mesajN = a === null ? null : mesajToplami(a);
  const modelListesi = a === null ? null : penceredekiModeller(a);

  // `m === null` ULAŞILAMAZ ve bu bir SAVUNMA değil TİP KAPISI: `muhataplar()` kanalı
  // her zaman ekliyor, `muhatapSec` de bu yüzden hiç `null` döndürmüyor (inceleme
  // Kü-4). Dal yine de bir cümle taşır — TypeScript'in `Muhatap | null` tipini
  // sessizce `!` ile ezmek, bir gün kanal kaldırılırsa boş bir başlık üretirdi.
  const ad = sahipsiz ? "sahipsiz teslimler" : (m?.ad ?? "muhatap listesi henüz çizilmedi");
  const isaret = sahipsiz ? "📥" : (m?.isaret ?? "?");

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-2 border-b bg-card px-4 py-2 sm:px-6">
      <span
        className={cn(
          "grid size-8 shrink-0 place-items-center border bg-muted font-semibold text-xs",
          tur === "kanal" ? "rounded-lg border-sky-500/25 bg-sky-500/10 text-sky-700 dark:text-sky-400" : null,
          a?.tur === "ana" || sahipsiz ? "rounded-lg" : tur === "kanal" ? null : "rounded-full",
        )}
      >
        {isaret}
      </span>
      <div className="min-w-0">
        <p className="truncate font-semibold text-sm">{ad}</p>
        {/* ÜÇ ÖLÇÜM BURAYA GERİ GELDİ (inceleme Ö-4): silinen `AjanKarti` "mesaj: N",
            "son oturum: …" ve "bu pencerede N FARKLI model" özetlerini çiziyordu ve
            üçü de beyansız düşmüştü. Kayıp kabul edilemezdi çünkü hiçbiri akıştan
            okunamıyor: akış oturum BAŞINA sayı verir (toplam değil), en yeni oturum
            damgasını ayraç içinde saklar, ve geçiş çipi yalnız KOMŞU oturumları
            kıyaslar (pencerede kaç ayrı model geçtiğini söylemez). */}
        <p className="flex flex-wrap items-center gap-x-2 text-[11px] text-muted-foreground">
          <span>
            {sahipsiz
              ? "hiçbir ajana denk düşmeyen teslim olayları"
              : tur === "kanal"
                ? "öneri üreteci ile kapı hükümleri"
                : a?.tur === "ana"
                  ? "ana model · konuşma defteri"
                  : "bot profili · konuşma defteri"}
          </span>
          {a === null ? null : (
            <>
              <span>
                son oturum:{" "}
                {a.sonOturumTs === null ? (
                  <Olculemedi
                    neden="hiç oturum görülmedi"
                    teknik="`son_oturum_ts: null` — ya defterde oturum yok ya damgası çevrilemedi (akıştaki ham değere bak)"
                  />
                ) : (
                  (zamanMetni(a.sonOturumTs) ?? a.sonOturumTs)
                )}
              </span>
              {a.teslimler === null ? (
                <Olculemedi
                  neden="son teslim ölçülemedi"
                  teknik="olay defteri okunamadı — `teslimler: null`"
                />
              ) : teslimTs === null ? (
                <span>son teslim: kayıt yok</span>
              ) : (
                <span className="tabular-nums">son teslim: {zamanMetni(teslimTs) ?? teslimTs}</span>
              )}
              <span>
                mesaj:{" "}
                {mesajN === null ? (
                  <Olculemedi
                    neden="sayılamadı"
                    teknik="oturum listesi ölçülemedi — 0 yazmak 'hiç mesajlaşılmadı' iddiası olurdu"
                  />
                ) : (
                  <strong className="tabular-nums">{bicimSayi(mesajN)}</strong>
                )}
              </span>
              {modelListesi !== null && modelListesi.length > 1 ? (
                <span className="text-uyari">
                  bu pencerede {bicimSayi(modelListesi.length)} FARKLI model:{" "}
                  {modelListesi.join(" · ")}
                </span>
              ) : null}
            </>
          )}
        </p>
      </div>

      {/* GÜNCEL MODEL YALNIZ BAŞLIKTA (maket): her oturum satırında rozet
          tekrarlamak değişimin kendisini gürültüde kaybediyordu. */}
      {tur === "kanal" ? (
        <Badge variant="outline" className="font-mono text-[10px]">
          {bicimSayi(hipotezN)} öneri
        </Badge>
      ) : a === null ? null : a.model === null ? (
        <Olculemedi
          neden="model kaydedilmemiş"
          teknik="`model: null` — en yeni oturumun modeli kayıtlı değil ya da hiç oturum yok; `durum` ayırt eder"
        />
      ) : (
        <Badge variant="outline" className="font-mono text-[10px]">
          {a.model}
        </Badge>
      )}

      <div
        role="tablist"
        aria-label="Muhatap sekmeleri"
        className="ml-auto flex gap-0.5 rounded-lg border bg-muted/40 p-0.5"
      >
        {takim.map((s) => (
          <button
            key={s}
            type="button"
            role="tab"
            id={`ajan-sekme-${s}`}
            // `aria-controls` OLMADAN sekme ile panel eşleşmiyordu (inceleme Kü-9):
            // ekran okuyucu "sekme" der ama neyi açtığını söyleyemezdi.
            aria-controls={PANEL_KIMLIGI}
            aria-selected={s === sekme}
            onClick={() => sekmeSecildi(s)}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs transition-colors",
              s === sekme ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {SEKME_ETIKET[s]}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ---- PANEL GÖVDESİ -------------------------------------------------------- */

/** ÇAPALAR (`id="bolum-*"`) KAYITTAKİ DÖRT KİMLİĞİN KARŞILIĞIDIR: kenar
 *  çubuğundaki derin bağlar ve v288 parite çivisi bu adları arıyor. Adlar eski,
 *  gösterdikleri içerik aynı — `filo` çapası artık ajan panelinin kendisi. */
function Govde({
  sahipsiz,
  m,
  sekme,
  ajanDurumu,
  filoDurumu,
  yuk,
  hipotezler,
  hafizaBasliklari,
  hafizaOlculemediNedeni,
  arama,
  teslimleriAc,
}: {
  sahipsiz: boolean;
  m: Muhatap | null;
  sekme: SekmeAdi;
  ajanDurumu: ReturnType<typeof useApi<Record<string, unknown>>>;
  filoDurumu: ReturnType<typeof useApi<Record<string, unknown>>>;
  yuk: ReturnType<typeof filoOku> | null;
  hipotezler: readonly Hipotez[];
  hafizaBasliklari: readonly { readonly baslik: string; readonly n: number }[];
  hafizaOlculemediNedeni: string | null;
  arama: string;
  teslimleriAc: () => void;
}) {
  if (sahipsiz) {
    return (
      <div id={CAPA.filo} className="flex flex-1 flex-col">
        <SahipsizPaneli yuk={yuk} />
      </div>
    );
  }

  if (m === null) {
    return (
      <p className="px-6 py-8 text-center text-muted-foreground text-sm">
        Muhatap listesi henüz çizilmedi — ne öneri hattı ne de ajan listesi okunabildi.
      </p>
    );
  }

  // AJAN TARAFI ÖNCE ve KENDİ KAPISINDA: `/api/agent` düşse bile ölçülmüş bir ajan
  // defteri "okunamadı" kutusunun arkasında kalmaz.
  if (m.tur === "ajan") {
    return (
      <div id={CAPA.filo} className="flex flex-1 flex-col">
        <Filo durum={filoDurumu} m={m} sekme={sekme} teslimleriAc={teslimleriAc} />
      </div>
    );
  }

  // ---- KANAL: üç sekmenin üçü de `/api/agent` gövdesine bağlı --------------
  return (
    <Kapi durum={ajanDurumu} ad="`/api/agent`" yukseklik="h-96">
      {(govde) =>
        sekme === "defter" ? (
          <div id={CAPA.defter} className="px-4 py-4 sm:px-6">
            {hipotezler.length === 0 ? (
              <Olculemedi
                neden="Gösterilecek öneri kaydı bulunamadı"
                teknik="`/api/agent.hypotheses` boş ya da dizi değil"
              />
            ) : (
              <HipotezDefteri hipotezler={hipotezler} />
            )}
          </div>
        ) : sekme === "olcum" ? (
          <div id={CAPA.olcum} className="flex flex-col gap-4 px-4 py-4 sm:px-6">
            <Kunye govde={govde} hipotezler={hipotezler} />
            <Grafikler govde={govde} hipotezler={hipotezler} />
          </div>
        ) : (
          <div id={CAPA.sohbet} className="flex flex-1 flex-col">
            <KanalAkisi
              hipotezler={hipotezler}
              hafizaBasliklari={hafizaBasliklari}
              hafizaOlculemediNedeni={hafizaOlculemediNedeni}
              arama={arama}
            />
          </div>
        )
      }
    </Kapi>
  );
}

/* ---- KÜNYE: KİMİNLE KONUŞUYORUZ ------------------------------------------ */

/** Karne defterinin ŞU ANKİ sürümü — kanalın "kim olduğu". `/api/agent.scoreboard`
 *  `state/scoreboard.json`u ham taşıyor; alanın VARLIĞI garanti değil.
 *
 *  NEDEN ÖLÇÜM SEKMESİNDE: eski kabukta bu kart üç sekmenin de üstünde duruyordu
 *  ve her sohbet ekranını dört kutuyla açıyordu. Mesajlaşma grameri başlığa
 *  yalnız kimliği koyar; SAYILAR bir ölçümdür ve yeri Ölçüm sekmesidir. Kart
 *  DÜŞÜRÜLMEDİ — taşındı; düşürseydik strateji sürümü ve sonucu ölçülen öneri
 *  sayısı ekrandan tamamen kaybolurdu. */
function Kunye({
  govde,
  hipotezler,
}: {
  govde: Readonly<Record<string, unknown>>;
  hipotezler: readonly Hipotez[];
}) {
  const sb = nesne(govde["scoreboard"]);
  const surum = sb === null ? null : (metin(sb["current_version"]) ?? (say(sb["current_version"]) !== null ? bicimSayi(say(sb["current_version"]) ?? 0) : null));
  const kal = nesne(govde["calibration"]);
  const sonuclanan = say(kal?.["n"]);
  const beyinler = useMemo(() => {
    const k = new Set<string>();
    for (const h of hipotezler) if (h.kaynak?.startsWith("hermes:")) k.add(h.kaynak.slice(7));
    return [...k];
  }, [hipotezler]);

  const sonDamga = useMemo(() => {
    let en: number | null = null;
    for (const h of hipotezler) {
      if (h.ts === null) continue;
      const t = Date.parse(h.ts);
      if (!Number.isNaN(t) && (en === null || t > en)) en = t;
    }
    return en;
  }, [hipotezler]);

  const gunFarki = sonDamga === null ? null : Math.floor((Date.now() - sonDamga) / 86_400_000);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="leading-none">Karşındaki kim?</CardTitle>
        <CardDescription>
          Bu kanalın karşı tarafı bir kişi değil, bir öneri hattı: hipotez üreteçleri + backtest kapısı.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kutu
          etiket="strateji sürümü"
          deger={surum}
          neden="Strateji sürümü kaydedilmemiş"
          teknik="`/api/agent.scoreboard.current_version` yok — karne defteri sürümü yazmamış"
        />
        <Kutu
          etiket="defterdeki öneri"
          deger={bicimSayi(hipotezler.length)}
          neden="Defterdeki kayıt sayısı hesaplanamadı"
          teknik="ulaşılamaz dal: sayı her zaman biçimlenir; metinsiz bir kutu çizmemek için yine de bir cümle taşıyor"
        />
        <Kutu
          etiket="sonucu ölçülen"
          deger={sonuclanan === null ? null : `${bicimSayi(sonuclanan)} / ${bicimSayi(hipotezler.length)}`}
          neden="Kaç önerinin sonucu ölçüldüğü henüz kaydedilmemiş"
          teknik="`/api/agent.calibration.n` yok"
        />
        <div className="rounded-lg border bg-muted/20 px-3 py-2">
          <p className="text-muted-foreground text-xs">son öneri</p>
          {sonDamga === null ? (
            <div className="mt-0.5">
              <Olculemedi
                neden="Son önerinin ne zaman geldiği okunamadı"
                teknik="hiçbir satırda ayrıştırılabilir `ts` yok"
              />
            </div>
          ) : (
            <p className="mt-0.5 font-medium text-sm leading-tight">
              {new Date(sonDamga).toLocaleDateString("tr-TR", { dateStyle: "medium" })}
              {gunFarki === null ? null : (
                <span className="ml-1 font-normal text-muted-foreground text-xs">
                  ({bicimSayi(gunFarki)} gün önce)
                </span>
              )}
            </p>
          )}
        </div>
        <div className="sm:col-span-2 lg:col-span-4">
          <p className="text-muted-foreground text-xs leading-5">
            LLM beyinleri:{" "}
            {beyinler.length === 0 ? (
              <span className="italic">
                defterdeki hiçbir satır `hermes:*` kaynağı taşımıyor — bu öneriler LLM'den değil,
                deterministik üreteçten gelmiş
              </span>
            ) : (
              beyinler.map((b) => (
                <Badge key={b} variant="outline" className="mr-1 text-[10px]">
                  {b}
                </Badge>
              ))
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function Kutu({
  etiket,
  deger,
  neden,
  teknik,
}: { etiket: string; deger: string | null; neden: string; teknik?: string }) {
  return (
    <div className="rounded-lg border bg-muted/20 px-3 py-2">
      <p className="text-muted-foreground text-xs">{etiket}</p>
      {deger === null ? (
        <div className="mt-0.5">
          <Olculemedi neden={neden} teknik={teknik} />
        </div>
      ) : (
        <p className="mt-0.5 font-medium text-lg tabular-nums leading-none">{deger}</p>
      )}
    </div>
  );
}
