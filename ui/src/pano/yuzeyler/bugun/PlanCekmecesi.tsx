"use client";

/* ============================================================================
   PLAN ÇEKMECESİ — sembolün tam gövdesi, ve ALTINDA çift adımlı karar
   ----------------------------------------------------------------------------
   OPERATÖR İSTEĞİ (2026-08-25): "sembollerin üzerine tıklayıp bilgilerini
   görebilmeliyim, ve review da ise onaylayabilmeliyim veya reddedebilmeliyim."

   DESEN TAKLİT EDİLDİ, YENİDEN İCAT EDİLMEDİ: kuyruk yüzeyindeki `OnayCekmecesi`
   + `KararPaneli` ikilisi tam bu işi yapıyor — satırda YALNIZ açma eylemi, karar
   KANITIN ALTINDA ve ÇİFT ADIMLI. Buradaki tek fark girdinin nereden geldiği:
   kuyruk gelen-kutusu öğesi taşır, bu yüzey `/api/today.todays_plans` satırının
   HAM kendisini.

   ÜÇ HÜKÜM, ÜÇ AYRI EKRAN — ve ayrım UÇTAN OKUNDU (`loop.operator_onay_ver` /
   `loop.operator_ret_ver` gövdeleri):
     · REVIEW → onay VE ret. Onay = İCRA YETKİSİ: silahlı kümeye yazar ve onay
       ANINDA aynaya emir dener (tek kapı: `mirror_submit_ve_kalicilastir`).
     · NO_GO  → onay ÇİZİLMEZ. `operator_onay_ver` NO_GO'yu MUTLAK reddeder; bir
       düğme çizip 409 yedirmek, operatöre kapının ezilebileceğini söylerdi.
       Ret yine mümkün ama bir GÖRME kaydıdır — kaydın kendisi `icra_etkisi:false`
       taşıyor ve ekran bunu aynen yazar.
     · GO     → plan zaten silahlanır; karar düğmesi yoktur, durumu yazılır.

   ONAY KAPISI "REVIEW" DEĞİLDİR (2026-08-25 denetimi): `operator_onay_ver` REVIEW'ün
   ÜSTÜNE beş kapı daha koyar — tarihsiz plan · seansı geçmiş plan (`pdate < book_at`) ·
   HALT · sembol zaten açık pozisyon · slot tavanı. İlk ikisi plan satırından ÖLÇÜLEBİLİR
   (`date`, `expired`) ve artık düğmeyi burada kesiyor; kalan üçü ölçülemez ve ekranda
   BEYAN ediliyor. Ölçülebilen bir kapıyı çizmemek, bu dosyanın kendi cümlesini çiğnerdi.

   GO'DA RET NEDEN YOK — CÜMLE İCRAYA DARALTILDI: eski metin "ikisi de hiçbir şeyi
   değiştirmezdi" diyordu ve bu RET için YANLIŞTI. `operator_ret_ver` kapı hükmüne HİÇ
   bakmaz: GO planına gönderilen ret 200 döner ve deftere gerekçeli bir GÖRME kaydı YAZAR.
   Düğme yine de çizilmiyor — ama artık "uç reddederdi" diye değil, "bu plan ŞU AN icraya
   gidiyor, buradaki bir ret durdurma yanılsaması verirdi" diye. Deftere yazan ama icrayı
   durdurmayan bir düğme, bu çekmecenin önlemek için var olduğu yanılsamanın ta kendisi.

   RET BİR DURDURMA DEĞİLDİR (bu dosyanın en pahalı cümlesi): `loop.girise_uygun`
   yasası "GO ya da (REVIEW ve onaylı)" diyor — yani ONAYLANMAYAN bir REVIEW planı
   ZATEN icra edilmiyor. Ret hiçbir şeyi durdurmaz çünkü durduracak bir şey yok.
   Ekran bunu yazmazsa operatör bir şeyi durdurduğunu SANIR; sistemin en tehlikeli
   yanılsaması budur ve bir cümleyle önlenebilir.

   İYİMSER GÜNCELLEME YOK: gönderim bittiğinde ekranda görünen her şey UÇTAN GELEN
   GÖVDEDİR ve liste `tazele()` ile YENİDEN OKUNUR. Panonun "oldu herhâlde" diye
   çizdiği bir başarı, `icra_yolu` "ayna: GÖNDERİLEMEDİ" derken operatöre emir gitti
   dedirtirdi — P-2026-08-07-VLO tam olarak bu sınıftı.

   UYDURMA YASAĞI: gövdenin yazmadığı alan "ölçülemedi + NEDEN" olur. Sıfır da tire
   de yazılmaz; ikisi de ölçülmemiş bir şeyi ölçülmüş gibi gösterir.
   ============================================================================ */
import { useState, type ReactNode } from "react";

import { Ban, CircleAlert, Send, ShieldAlert, Undo2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";

import { krizPost } from "../../kabuk/krizUclari";
import type { Plan } from "./tipler";

/** `loop.RET_MIN_GEREKCE` — uç gerekçesi bu eşiğin altındaki isteği 400'ler. Sayı BURADA da
 *  literal, çünkü ekranın kullanıcıya söylediği eşik ile ucun dayattığı eşik AYNI olmak
 *  zorunda; ayrıştıklarında kullanıcı 400'ü ancak gönderdikten sonra öğrenir. */
const RET_MIN_GEREKCE = 12;

/* ---- GÖVDE TİPLERİ (ÖLÇÜLDÜ, TAHMİN EDİLMEDİ) -----------------------------
   `state/trade_plans.jsonl` son seans satırlarının anahtar birleşimi ölçüldü
   (2026-08-25, 2026-07-28 seansı, 10 satır): id · date · ticker · side ·
   entry_trigger · stop · targets · size_r · r_multiple_expected · regime_at_plan ·
   sector · score · setup · dormant_setup · profit_target · strategy_version ·
   skill_chain · gate_verdict · gate_reasons · gate_checks · p_win_shadow.
   `analytics.today` bu satırları KIRPMADAN geçiriyor, uç katmanı üstüne bayatlık ve
   onay damgalarını ekliyor (`_enrich_stale_plans`, `_onay_bekleyen_damgala`).

   NEDEN `bugun/tipler.ts::Plan` GENİŞLETİLİYOR: o tip tablo sütunlarının okuduğu
   kesiti tanımlıyor ve bu turda bana KAPALI. Ondan türeyip yalnız çekmecenin okuduğu
   alanları eklemek, iki ayrı plan tipi tutmaktan güvenli. HEPSİ İSTEĞE BAĞLI: gelmeyen
   alan `undefined` kalır ve ekranda "ölçülemedi + neden" olur. */

/** Tek bir disiplin kapısının hükmü (`gate_checks[]`). */
export interface KapiKontrolu {
  readonly check?: string;
  readonly passed?: boolean;
  readonly severity?: string;
  readonly value?: unknown;
  readonly threshold?: string;
  readonly note?: string | null;
}

/** Operatör onayı/reddi damgası — `loop.ONAY_ALANI` / `loop.RET_ALANI`. */
export interface OperatorDamgasi {
  readonly ts?: string;
  readonly kanal?: string;
  readonly gerekce?: string;
  readonly icra_etkisi?: boolean;
  readonly beyan?: string;
}

export interface PlanTamGovde extends Plan {
  readonly side?: string;
  readonly stop?: number | null;
  readonly profit_target?: number | null;
  readonly targets?: readonly number[];
  readonly r_multiple_expected?: number | null;
  readonly regime_at_plan?: string;
  readonly strategy_version?: number | string;
  readonly p_win_shadow?: number | null;
  readonly dormant_setup?: boolean;
  readonly skill_chain?: readonly string[];
  readonly gate_checks?: readonly KapiKontrolu[];
  readonly operator_onayi?: OperatorDamgasi;
  readonly operator_reddi?: OperatorDamgasi;
}

/** İki ucun yanıt gövdesinin BİRLEŞİMİ. Tek tip, çünkü iki uç aynı sözleşmeyi paylaşıyor
 *  ({ok, kod, neden, …}) ve ekran her alanı yokluğa dayanıklı basıyor: gelmeyen alan
 *  çizilmez, "0" ya da "başarılı" diye yorumlanmaz. */
export interface UcYaniti {
  readonly plan_id?: string;
  readonly ticker?: string;
  readonly gate_verdict?: string;
  readonly silahli?: boolean;
  readonly armed_n?: number;
  readonly zaten_onayliydi?: boolean;
  readonly zaten_silahliydi?: boolean;
  readonly zaten?: boolean;
  readonly icra_yasasi?: boolean;
  readonly icra_yolu?: string;
  readonly gonderim?: {
    readonly ok?: boolean;
    readonly submitted?: number;
    readonly detail?: string;
    readonly dropped_ids?: readonly string[];
  } | null;
  readonly not?: string | null;
  readonly neden?: string;
  readonly ts?: string;
  readonly operator_reddi?: OperatorDamgasi;
}

type Yon = "onayla" | "reddet";

/* ---- DÜRÜSTLÜK PARÇALARI --------------------------------------------------- */

/** Ölçülemeyen alanın tek biçimi. `neden` ZORUNLU — nedensiz bir "ölçülemedi",
 *  okuyucuyu sunucu günlüklerine gönderir; oysa cevap burada yazılabilir.
 *
 *  İKİ KATMAN (2026-08-26 sözleşmesi): `neden` EKRANDA duran insan cümlesidir;
 *  `teknik` iç ayrıntıdır (alan adı, uç yolu) ve yalnız üstüne gelince çıkar.
 *  `teknik` düşürülmez — teşhis eden kişinin aradığı tam olarak odur. */
function Yok({ neden, teknik }: { readonly neden: string; readonly teknik?: string }) {
  return (
    <span className="text-muted-foreground text-xs italic" title={teknik ? `${neden} — ${teknik}` : neden}>
      ölçülemedi — {neden}
    </span>
  );
}

/** İç ayrıntının iki parçasını (çağıranın verdiği alan adı + hücrenin ölçtüğü hâl)
 *  TEK `teknik` dizesinde birleştirir. Biri düşerse öteki de anlamsız kalırdı. */
function teknikBirlestir(teknik: string | undefined, hal: string): string {
  return teknik ? `${teknik} · ${hal}` : hal;
}

function Satir({ etiket, children }: { readonly etiket: string; readonly children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5 border-b py-1.5 last:border-b-0">
      <span className="text-muted-foreground text-xs">{etiket}</span>
      <span className="text-right text-sm">{children}</span>
    </div>
  );
}

/** Sayı hücresi. `undefined` ile `null` AYRI cümle kurar: biri "hiç yazılmadı",
 *  diğeri "yazıldı ama ölçülemedi". İkisini birleştirmek bilgi kaybıdır.
 *
 *  BURADA `neden` BİR ÖZNEDİR, cümle DEĞİL ("Skor", "Giriş tetiği"): üç hâlin
 *  yüklemini hücrenin kendisi ekler, çünkü hangi hâlde olduğumuzu yalnız o bilir.
 *  Alan adı gibi iç ayrıntı `teknik`e verilir ve üç hâlin damgasıyla birleşir. */
function Sayi({
  deger,
  neden,
  teknik,
  basamak = 2,
}: {
  readonly deger: number | null | undefined;
  readonly neden: string;
  readonly teknik?: string;
  readonly basamak?: number;
}) {
  if (deger === undefined)
    return <Yok neden={`${neden} yazılmamış`} teknik={teknikBirlestir(teknik, "alan gövdede YOK")} />;
  if (deger === null)
    return <Yok neden={`${neden} ölçülememiş`} teknik={teknikBirlestir(teknik, "alan yazıldı ama null")} />;
  if (!Number.isFinite(deger))
    return <Yok neden={`${neden} okunamadı`} teknik={teknikBirlestir(teknik, "sayı sonlu değil")} />;
  return (
    <span className="tabular-nums">
      {deger.toLocaleString("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: basamak })}
    </span>
  );
}

function Metin({
  deger,
  neden,
  teknik,
}: {
  readonly deger: string | undefined;
  readonly neden: string;
  readonly teknik?: string;
}) {
  if (deger === undefined || deger === "") return <Yok neden={neden} teknik={teknik} />;
  return <span>{deger}</span>;
}

/** `gate_checks[].value` sayı da olabilir metin de — tipe göre basılır, zorlanmaz. */
function kontrolDegeri(v: unknown): string {
  if (v === null || v === undefined) return "değer yazılmamış";
  if (typeof v === "number") return Number.isFinite(v) ? v.toLocaleString("tr-TR") : String(v);
  if (typeof v === "boolean") return v ? "evet" : "hayır";
  if (typeof v === "string") return v;
  return JSON.stringify(v);
}

/* ---- KAPI DÖKÜMÜ ----------------------------------------------------------- */

/** Geçen kapılar da gösterilir: operatör neyi onayladığını görecekse, kararın DAYANDIĞI
 *  zemini de görmeli. "Yalnız düşenleri göster" bir karar ekranında zemini gizlemektir. */
function KapiDokumu({ kontroller }: { readonly kontroller: readonly KapiKontrolu[] }) {
  const dusen = kontroller.filter((k) => k.passed === false);
  const gecen = kontroller.filter((k) => k.passed === true);
  const belirsiz = kontroller.filter((k) => k.passed !== true && k.passed !== false);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-1.5">
        <Badge variant="outline">{dusen.length} düştü</Badge>
        <Badge variant="outline" className="text-muted-foreground">
          {gecen.length} geçti
        </Badge>
        {belirsiz.length > 0 ? (
          <Badge variant="outline" className="text-muted-foreground">
            {belirsiz.length} hükmü okunamadı
          </Badge>
        ) : null}
      </div>
      <ul className="flex flex-col gap-1">
        {[...dusen, ...belirsiz, ...gecen].map((k, i) => (
          <li
            key={`${k.check ?? "adsiz"}-${i}`}
            className={
              k.passed === false ? "rounded-md border border-destructive/30 bg-destructive/5 p-2" : "rounded-md border p-2"
            }
          >
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <code className="font-mono text-xs">{k.check ?? "(adsız kontrol)"}</code>
              <Badge variant="outline" className="text-[10px]">
                {k.severity ?? "şiddet yazılmamış"}
              </Badge>
              <span className="text-muted-foreground text-[11px]">
                {k.passed === true ? "geçti" : k.passed === false ? "DÜŞTÜ" : "karar okunamadı"}
              </span>
              <span className="ml-auto tabular-nums text-[11px]">
                {kontrolDegeri(k.value)} {k.threshold ? `↔ ${k.threshold}` : "(eşik yazılmamış)"}
              </span>
            </div>
            {k.note ? <p className="mt-1 text-sm leading-5">{k.note}</p> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---- ÇEKMECE --------------------------------------------------------------- */

export function PlanCekmecesi({
  plan,
  acik,
  kapat,
  tazele,
}: {
  readonly plan: PlanTamGovde | null;
  readonly acik: boolean;
  readonly kapat: () => void;
  /** Karar gönderildikten SONRA `/api/today`i yeniden okur (iyimser güncelleme yok). */
  readonly tazele: () => void;
}) {
  return (
    <Sheet open={acik} onOpenChange={(a) => (a ? undefined : kapat())}>
      <SheetContent side="right" className="w-full sm:max-w-xl">
        {plan === null ? (
          <SheetHeader>
            <SheetTitle>Plan seçilmedi</SheetTitle>
            <SheetDescription>Tablodaki bir sembole tıkla.</SheetDescription>
          </SheetHeader>
        ) : (
          /* `key` PLAN KİMLİĞİ: çekmece açıkken başka bir sembole geçilirse iç durum
             (alınmış niyet, yazılmış gerekçe, önceki yanıt) SIFIRLANMALI. Aksi hâlde
             A planı için alınmış bir niyet, B planı açıldığında ekranda durur ve
             ikinci tık B'yi gönderirdi. */
          <PlanIcerik key={plan.id ?? "kimliksiz"} plan={plan} tazele={tazele} />
        )}
      </SheetContent>
    </Sheet>
  );
}

function PlanIcerik({ plan, tazele }: { readonly plan: PlanTamGovde; readonly tazele: () => void }) {
  const [niyet, setNiyet] = useState<Yon | null>(null);
  const [gerekce, setGerekce] = useState("");
  const [gonderiliyor, setGonderiliyor] = useState(false);
  const [sonuc, setSonuc] = useState<UcYaniti | null>(null);
  const [hata, setHata] = useState<{ readonly kod: number; readonly detay: string | null } | null>(null);

  const kimlik = plan.id;
  const hukum = plan.gate_verdict;
  const zatenOnayli = typeof plan.operator_onayi?.ts === "string";
  const zatenReddedildi = typeof plan.operator_reddi?.ts === "string";

  // ONAY KAPISI = UCUN KAPISI, VE UCUN KAPISI "REVIEW" DEĞİL. `loop.operator_onay_ver`
  // REVIEW eşitliğinin ÜSTÜNE beş kapı daha koyar, hepsi 409: (1) tarihsiz plan,
  // (2) seansı geçmiş plan (`pdate < book_at`), (3) HALT aktif, (4) sembol zaten açık
  // pozisyon, (5) slot tavanı (`max_open_positions`).
  // İLK İKİSİ PLAN SATIRINDAN ÖLÇÜLEBİLİR, bu yüzden düğmeyi BURADA kesiyorlar:
  //   · `expired` ucun kapısının BİREBİR aynısıdır — `_enrich_stale_plans` onu
  //     `plan.date < latest_session` diye yazar ve `latest_session` da
  //     `portfolio.json.last_date`tir, yani `operator_onay_ver`in okuduğu `book_at` ile
  //     AYNI sayı. İki ayrı ölçüt değil, tek ölçütün iki adı.
  //   · Tarihsizlik AYRI bir daldır: uç "seans geçerliliği ÖLÇÜLEMİYOR" deyip reddeder.
  // Kapıyı burada gevşetmek — yalnız `hukum === "REVIEW"` yazmak — seansı geçmiş bir
  // planda düğme çizip operatöre 409 yedirirdi; NO_GO'ya düğme çizmekle aynı kusur sınıfı.
  // KALAN ÜÇÜ BU ÇEKMECEDEN ÖLÇÜLEMEZ (çekmece kitabı ve sağlık durumunu değil, YALNIZ
  // plan satırını okur). Kapatamadığımız kapı susularak değil, ekranda BEYAN edilerek geçilir.
  const seansiGecmis = plan.expired === true;
  const tarihsiz = plan.date === undefined || plan.date === "";
  const onaylanabilir = hukum === "REVIEW" && !seansiGecmis && !tarihsiz;
  // REVIEW olup da düğmesi çizilmeyen satır SESSİZ KALAMAZ: düğmenin yokluğu bir pano
  // kusuru gibi okunurdu. Sebep yazılır (aşağıdaki şerit bu bayrağın altında durur).
  const onayiOlculenKapiKesti = hukum === "REVIEW" && !onaylanabilir;
  // RET NO_GO'DA DA VARDIR (görme kaydı) AMA ONAYLI PLANDA YOKTUR: onay icra yetkisidir
  // ve ayna emri gitmiş olabilir; "reddetmek" onu geri almaz (uç 409 verir).
  const reddedilebilir = (hukum === "REVIEW" || hukum === "NO_GO") && !zatenOnayli;
  // DÖRDÜNCÜ DAL GERÇEKTİR: `gate_verdict` opsiyoneldir ve tablo sütunu bu yokluğu zaten
  // çiziyor. Üç dalın da tutmadığı bir satırda karar bölümünün BOŞ kalması, "burada
  // yapılacak bir şey yok" demenin sessiz hâli olurdu; doğru cümle hükmün okunamadığıdır.
  const hukumTanindi = hukum === "GO" || hukum === "REVIEW" || hukum === "NO_GO";
  const gerekceYetersiz = gerekce.trim().length < RET_MIN_GEREKCE;

  async function gonder(y: Yon) {
    // SESSİZ ÇIKIŞ DEĞİL, KURULUŞ GEREĞİ ERİŞİLEMEZ DAL: kimliksiz planda karar bölümü hiç
    // çizilmiyor (yukarıdaki "Bu plana karar yazılamaz" uyarısı onun yerine duruyor), yani bu
    // dalın koşabildiği bir yol yok. Yine de duruyor çünkü tipin daraltılması gerekiyor —
    // uydurulmuş bir kimlikle uca istek göndermektense hiç göndermemek.
    if (kimlik === undefined) return;
    setGonderiliyor(true);
    setHata(null);
    const s =
      y === "onayla"
        ? await krizPost(`/api/plan/${encodeURIComponent(kimlik)}/onayla`)
        : await krizPost(`/api/plan/${encodeURIComponent(kimlik)}/reddet`, { gerekce: gerekce.trim() });
    setGonderiliyor(false);
    setNiyet(null);
    if (!s.ok) {
      // UCUN METNİ AYNEN: 400 ("gerekçe en az 12 karakter…") ve 409 ("NO_GO onaylanamaz…")
      // gövdelerinde kararın TAM sebebi yazılı. Kendi cümlemizle özetlemek, ucun bildiği
      // bir şeyi kaybetmek olurdu.
      setHata({ kod: s.kod, detay: s.detay });
      return;
    }
    setSonuc((s.govde ?? {}) as UcYaniti);
    // LİSTE YENİDEN OKUNUR: iyimser güncelleme yerine yeniden ölçüm.
    tazele();
  }

  return (
    <>
      <SheetHeader className="pr-10">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{hukum ?? "hüküm yazılmamış"}</Badge>
          {zatenOnayli ? <Badge variant="default">operatör onaylı</Badge> : null}
          {zatenReddedildi ? <Badge variant="secondary">operatör reddi kayıtlı</Badge> : null}
          {plan.expired === true ? (
            <Badge variant="outline" className="text-muted-foreground">
              seansı geçmiş
            </Badge>
          ) : null}
        </div>
        <SheetTitle className="text-base leading-6">
          {plan.ticker ?? "sembolü ölçülemedi"} · {plan.setup ?? "kurulumu ölçülemedi"}
        </SheetTitle>
        <SheetDescription className="break-all font-mono text-[11px]">
          {kimlik ?? "plan kimliği YOK — bu plana uç çağrılamaz"}
        </SheetDescription>
      </SheetHeader>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
        <section className="flex flex-col gap-1">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Künye</h4>
          <div>
            <Satir etiket="Sembol">
              <Metin deger={plan.ticker} neden="Sembol kaydedilmemiş" teknik="plan satırında `ticker` yok" />
            </Satir>
            <Satir etiket="Yön">
              <Metin deger={plan.side} neden="Yön kaydedilmemiş" teknik="plan satırında `side` yok" />
            </Satir>
            <Satir etiket="Kurulum">
              <Metin deger={plan.setup} neden="Kurulum kaydedilmemiş" teknik="plan satırında `setup` yok" />
            </Satir>
            <Satir etiket="Sektör">
              <Metin deger={plan.sector} neden="Sektör kaydedilmemiş" teknik="plan satırında `sector` yok" />
            </Satir>
            <Satir etiket="Seans tarihi">
              <Metin deger={plan.date} neden="Seans tarihi kaydedilmemiş" teknik="plan satırında `date` yok" />
            </Satir>
            <Satir etiket="Kontrol kararı">
              <Metin deger={hukum} neden="Kontrol kararı kaydedilmemiş" teknik="plan satırında `gate_verdict` yok" />
            </Satir>
            <Satir etiket="Skor">
              <Sayi deger={plan.score} neden="Plan skoru kaydedilmemiş" teknik="plan satırının `score` alanı" basamak={3} />
            </Satir>
            <Satir etiket="Rejim (plan anı)">
              <Metin
                deger={plan.regime_at_plan}
                neden="Plan anındaki piyasa rejimi kaydedilmemiş"
                teknik="plan satırında `regime_at_plan` yok"
              />
            </Satir>
            <Satir etiket="Strateji sürümü">
              <Metin
                deger={plan.strategy_version === undefined ? undefined : String(plan.strategy_version)}
                neden="Strateji sürümü kaydedilmemiş"
                teknik="plan satırında `strategy_version` yok"
              />
            </Satir>
          </div>
        </section>

        <section className="flex flex-col gap-1">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Seviyeler ve risk</h4>
          <div>
            <Satir etiket="Giriş tetiği">
              <Sayi deger={plan.entry_trigger} neden="Giriş tetiği kaydedilmemiş" teknik="plan satırının `entry_trigger` alanı" />
            </Satir>
            <Satir etiket="Stop">
              <Sayi deger={plan.stop} neden="Zarar durdurma seviyesi kaydedilmemiş" teknik="plan satırının `stop` alanı" />
            </Satir>
            <Satir etiket="Kâr hedefi">
              <Sayi deger={plan.profit_target} neden="Kâr hedefi kaydedilmemiş" teknik="plan satırının `profit_target` alanı" />
            </Satir>
            <Satir etiket="Beklenen R katsayısı">
              <Sayi
                deger={plan.r_multiple_expected}
                neden="Beklenen R katsayısı"
                teknik="plan satırının `r_multiple_expected` alanı"
              />
            </Satir>
            <Satir etiket="Risk büyüklüğü (R)">
              <Sayi deger={plan.size_r} neden="Risk büyüklüğü kaydedilmemiş" teknik="plan satırının `size_r` alanı" />
            </Satir>
            <Satir etiket="Son kapanış">
              <Sayi
                deger={plan.last_close}
                neden="Son kapanış fiyatı kaydedilmemiş"
                teknik="plan satırının `last_close` alanı — günün barı okunamadı"
              />
            </Satir>
            <Satir etiket="Tetikten sapma (%)">
              <Sayi
                deger={plan.drift_pct}
                neden="Tetikten sapma hesaplanamadı"
                teknik="plan satırının `drift_pct` alanı — tetik 0 ya da yazılmamış olabilir"
                basamak={1}
              />
            </Satir>
            <Satir etiket="Adet (lot)">
              <Yok
                neden="Lot adedi planda yazmaz — gönderim anında sermayeden hesaplanır"
                teknik="plan satırı adet TAŞIMIYOR; lot `broker.size_position` içinde öz sermayeden çıkar"
              />
            </Satir>
          </div>
        </section>

        <section className="flex flex-col gap-1">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
            Kapılar — geçen ve düşen
          </h4>
          {plan.gate_checks && plan.gate_checks.length > 0 ? (
            <KapiDokumu kontroller={plan.gate_checks} />
          ) : (
            <Yok
              neden="Tek tek kontrol sonuçları bu plana kaydedilmemiş"
              teknik="plan satırı `gate_checks` taşımıyor"
            />
          )}
        </section>

        <section className="flex flex-col gap-1">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
            Kontrol gerekçeleri (kararın metni)
          </h4>
          {plan.gate_reasons && plan.gate_reasons.length > 0 ? (
            <ul className="list-disc pl-5 text-sm leading-6">
              {plan.gate_reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          ) : (
            <Yok
              neden="Kararın gerekçe metni kaydedilmemiş"
              teknik="`gate_reasons` boş ya da plan satırında yok"
            />
          )}
        </section>

        {zatenReddedildi ? (
          <section className="rounded-md border bg-muted/30 p-3">
            <h4 className="text-muted-foreground text-[11px] uppercase">Kayıtlı operatör reddi</h4>
            <Satir etiket="Damga">
              <Metin
                deger={plan.operator_reddi?.ts}
                neden="Ret zamanı kaydedilmemiş"
                teknik="plan satırında `operator_reddi.ts` yok"
              />
            </Satir>
            <Satir etiket="Gerekçe">
              <Metin
                deger={plan.operator_reddi?.gerekce}
                neden="Ret gerekçesi kaydedilmemiş"
                teknik="plan satırında `operator_reddi.gerekce` yok"
              />
            </Satir>
            {plan.operator_reddi?.beyan ? (
              <p className="mt-2 text-muted-foreground text-[11px] leading-4">{plan.operator_reddi.beyan}</p>
            ) : null}
          </section>
        ) : null}

        <Separator />

        {/* ---- KARAR: kanıtın ALTINDA, çift adımlı ------------------------- */}
        <section className="flex flex-col gap-3">
          <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Karar</h4>

          {kimlik === undefined ? (
            <Alert>
              <Ban />
              <AlertTitle>Bu plana karar yazılamaz</AlertTitle>
              <AlertDescription>
                Plan kimliği yok. Uçlar kimliği yol parçası olarak alır; kimliksiz bir plana istek
                gönderilemez.
              </AlertDescription>
            </Alert>
          ) : null}

          {hukum === "GO" ? (
            <Alert>
              <CircleAlert />
              <AlertTitle>GO planı zaten işleme hazırlanır</AlertTitle>
              <AlertDescription>
                <span className="leading-6">
                  Kapı GO dedi; plan operatör onayı BEKLEMEDEN giriş kuyruğuna girer. Onay düğmesi
                  yok: <code className="font-mono text-[11px]">operator_onay_ver</code> yalnız REVIEW
                  alır, GO hükmünü 409 ile reddeder — ve kabul etseydi bile İCRAYI değiştirmezdi,
                  çünkü plan onaysız da silahlanıyor.
                </span>
                <span className="mt-2 block leading-6">
                  RET DÜĞMESİ DE YOK, AMA SEBEBİ BAŞKA:{" "}
                  <code className="font-mono text-[11px]">operator_ret_ver</code> kapı hükmüne HİÇ
                  BAKMAZ — gönderilseydi 200 dönerdi ve deftere gerekçeli bir GÖRME kaydı yazardı.
                  Yani &quot;hiçbir şey değişmezdi&quot; DEĞİL: defter değişirdi, icra değişmezdi.
                  Düğmeyi yine de çizmiyoruz ve sebebi yazılı olsun: bu plan ŞU AN icraya gidiyor,
                  buradaki bir &quot;reddet&quot; operatöre durdurduğu YANILSAMASI verirdi — bu
                  çekmecenin var olma sebebi tam olarak o yanılsamayı önlemek. İcrayı durduran kol
                  üst bardaki kriz kollarıdır (açık emri iptal / pozisyonu düzleştir).
                </span>
              </AlertDescription>
            </Alert>
          ) : null}

          {!hukumTanindi ? (
            <Alert>
              <CircleAlert />
              <AlertTitle>Kontrol kararı okunamadı — karar yolu kapalı</AlertTitle>
              <AlertDescription>
                Plan satırında <code className="font-mono text-[11px]">gate_verdict</code> ya yok ya
                da tanınmayan bir değer taşıyor. Onay ucu yalnız REVIEW alır, ret ucu REVIEW ve
                NO_GO alır; hangisi olduğunu ÖLÇEMEDİĞİMİZ için düğme çizilmedi. Boş bir bölüm
                çizmek, &quot;yapılacak bir şey yok&quot; demenin sessiz hâli olurdu.
              </AlertDescription>
            </Alert>
          ) : null}

          {hukum === "NO_GO" ? (
            <Alert>
              <ShieldAlert />
              <AlertTitle>NO_GO onaylanamaz</AlertTitle>
              <AlertDescription>
                Onay düğmesi bilerek çizilmedi: disiplin kapısının sert reddi MUTLAKTIR ve onay
                yalnız &quot;insan baksın&quot; diyen REVIEW hükmünü kapatır. Aşağıdaki ret bir GÖRME
                kaydıdır — bu planı zaten hiçbir yol icraya taşımıyordu, kayıt İCRAYI DEĞİŞTİRMEZ.
              </AlertDescription>
            </Alert>
          ) : null}

          {onayiOlculenKapiKesti ? (
            <Alert>
              <ShieldAlert />
              <AlertTitle>Seansı geçmiş ya da tarihsiz REVIEW planı onaylanamaz</AlertTitle>
              <AlertDescription>
                <span className="leading-6">
                  Hüküm REVIEW ama onay düğmesi bilerek çizilmedi:{" "}
                  {seansiGecmis
                    ? "planın seansı GEÇMİŞ (kitabın son işlenmiş seansından eski). Planlar TEK SEANS geçerlidir; seviyeleri bayat ve bu plan bir daha işleme hazırlanamaz."
                    : "planda seans tarihi YOK, yani geçerliliği ÖLÇÜLEMİYOR."}{" "}
                  <code className="font-mono text-[11px]">operator_onay_ver</code> aynı sebeple 409
                  verirdi; düğme çizip 409 yedirmek, operatöre kapının ezilebileceğini söylerdi.
                </span>
                {/* RET YOLUNUN DURUMU İKİ CÜMLE DEĞİL, TEK CÜMLE OLMALI: seansı geçmiş bir plan
                    ONAYLI da olabilir (onayın ERTESİ GÜNÜ — bayat plan listeden atılmıyor). O
                    satırda `reddedilebilir` FALSE'tur ve aşağıdaki onaylı-şeridi "Ret yolu kapalı"
                    yazar; burada koşulsuz "ret açık" demek ekranı kendisiyle çeliştirirdi. */}
                {reddedilebilir ? (
                  <span className="mt-2 block leading-6">
                    RET YOLU AÇIK KALIR ve bu bir tutarsızlık değil:{" "}
                    <code className="font-mono text-[11px]">operator_ret_ver</code> seans/HALT/slot
                    kapılarını KOŞMAZ — onlar İCRA kapılarıdır, ret icra etmez. Bayat bir planı da
                    &quot;gördüm ve istemedim&quot; diye kapatmak meşrudur.
                  </span>
                ) : null}
              </AlertDescription>
            </Alert>
          ) : null}

          {onaylanabilir ? (
            <Alert variant="destructive">
              <ShieldAlert />
              <AlertTitle>ONAY = İCRA YETKİSİDİR</AlertTitle>
              <AlertDescription>
                <span className="leading-6">
                  Onay planı silahlı kümeye yazar VE onay anında aynaya emir gönderir. Geri alınamaz:
                  gönderilen emri iptal etmek ayrı bir koldur (üst bardaki kriz kolları). Ucun ne
                  yaptığı gönderim sonrası
                  <code className="mx-1 font-mono text-[11px]">icra_yolu</code>
                  satırında yazılı olacak.
                </span>
                <span className="mt-2 block leading-6">
                  DÜĞMENİN ÇİZİLMESİ ONAYIN GEÇECEĞİ ANLAMINA GELMEZ. Bu çekmece yalnız plan
                  satırını okuyor; kitabı ve sağlık durumunu değil. Ölçebildiğim iki kapıyı
                  (tarih · seans) yukarıda uyguladım, ama uç ayrıca şu kapıları koyar ve
                  üçünü de 409 ile döndürür: HALT aktifse yeni giriş silahlanmaz ·
                  sembol zaten açık pozisyonsa aynı isimde ikinci giriş yok ·
                  slot tavanı doluysa (max_open_positions) onay kapıyı gevşetemez.
                  Bu üçünün hükmünü ancak gönderimden sonra, ucun 409 metninde göreceksin —
                  o metin aşağıda AYNEN basılır, panonun özeti olarak değil.
                </span>
              </AlertDescription>
            </Alert>
          ) : null}

          {/* DÜRÜSTLÜK ŞERİDİ — ret bir durdurma DEĞİL. */}
          {reddedilebilir ? (
            <p className="rounded-md border bg-muted/30 p-3 text-sm leading-6">
              Ret ne yapar, ne yapmaz: onaylamazsan bu plan zaten icra EDİLMEZ; ret bir KAYITTIR ve
              hükmünün deftere geçmesini sağlar. Sessiz zaman aşımı ile &quot;gördüm ve şu sebeple
              istemedim&quot; bugüne kadar aynı görünüyordu — ayrımı bu kayıt üretir.
            </p>
          ) : null}

          {zatenOnayli ? (
            <p className="rounded-md border border-uyari-h bg-uyari-t p-3 text-sm leading-6">
              Bu plan ONAYLI (damga:{" "}
              <Metin
                deger={plan.operator_onayi?.ts}
                neden="Onay zamanı kaydedilmemiş"
                teknik="plan satırında `operator_onayi.ts` yok"
              />
              ). Ret yolu kapalı: onay icra yetkisidir ve ayna emri gitmiş olabilir; reddetmek onu
              geri almaz. Yeniden onay göndermek İKİNCİ emir doğurmaz (uç dedup yapar) — yalnız
              düşmüş bir ayna gönderimini yeniden dener.
            </p>
          ) : null}

          {/* ---- GEREKÇE: ZORUNLU, EŞİĞİ YAZILI ---------------------------- */}
          {reddedilebilir ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="plan-ret-gerekce" className="text-xs">
                Ret gerekçesi (ZORUNLU — en az {RET_MIN_GEREKCE} karakter)
              </Label>
              <Textarea
                id="plan-ret-gerekce"
                value={gerekce}
                onChange={(e) => setGerekce(e.target.value)}
                disabled={gonderiliyor}
                rows={2}
                placeholder="Neden istemedin? Gerekçesiz ret, sessiz zaman aşımından farksız bir satırdır."
              />
              <p className="text-muted-foreground text-[11px] leading-4">
                Uç gerekçesiz isteği 400 ile reddeder: kaydın TÜM değeri gerekçededir. Şu an{" "}
                {gerekce.trim().length} karakter yazıldı.
              </p>
            </div>
          ) : null}

          {/* ---- BİRİNCİ TIK ----------------------------------------------- */}
          {niyet === null && kimlik !== undefined ? (
            <div className="flex flex-wrap gap-2">
              {onaylanabilir ? (
                <Button type="button" variant="destructive" onClick={() => setNiyet("onayla")}>
                  <Send aria-hidden />
                  Onayla…
                </Button>
              ) : null}
              {reddedilebilir ? (
                <Button
                  type="button"
                  variant="outline"
                  disabled={gerekceYetersiz}
                  onClick={() => setNiyet("reddet")}
                >
                  <Ban aria-hidden />
                  Reddet…
                </Button>
              ) : null}
              {onaylanabilir || reddedilebilir ? (
                <span className="self-center text-muted-foreground text-[11px]">
                  İki adım: bu tık niyeti alır, gönderim ikinci tıkla olur.
                </span>
              ) : null}
            </div>
          ) : null}

          {/* ---- İKİ TIK ARASI: NE OLACAĞI YAZILI --------------------------- */}
          {niyet !== null ? (
            <div
              className={
                niyet === "onayla"
                  ? "rounded-md border border-destructive/40 bg-destructive/5 p-3"
                  : "rounded-md border bg-muted/30 p-3"
              }
              aria-live="polite"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-sm">İkinci tık şunu yapacak</span>
                <Badge variant={niyet === "onayla" ? "default" : "secondary"} className="font-mono text-[10px]">
                  {niyet}
                </Badge>
              </div>
              <p className="mt-2 text-sm leading-6">
                {niyet === "onayla"
                  ? "Planı işleme hazır planlara yazar ve ONAY ANINDA aynaya emir gönderir. Kontrol kararı DEĞİŞMEZ (onay bir olaydır, karar geriye dönük yazılmaz)."
                  : "Plan satırına gerekçeli bir ret damgası yazar. İCRAYA DOKUNMAZ — durduracak bir şey zaten yoktu."}
              </p>
              {niyet === "reddet" ? (
                <p className="mt-2 whitespace-pre-wrap rounded-md border bg-background p-2 text-xs leading-5">
                  gerekçe: {gerekce.trim()}
                </p>
              ) : null}
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant={niyet === "onayla" ? "destructive" : "default"}
                  disabled={gonderiliyor || (niyet === "reddet" && gerekceYetersiz)}
                  onClick={() => void gonder(niyet)}
                >
                  {gonderiliyor ? <Spinner /> : <Send aria-hidden />}
                  {gonderiliyor ? "Gönderiliyor — bekle" : "EVET, GÖNDER"}
                </Button>
                <Button type="button" variant="ghost" disabled={gonderiliyor} onClick={() => setNiyet(null)}>
                  <Undo2 aria-hidden />
                  Vazgeç
                </Button>
              </div>
            </div>
          ) : null}

          {/* ---- HATA: UCUN METNİ AYNEN ------------------------------------ */}
          {hata !== null ? (
            <Alert variant="destructive">
              <CircleAlert />
              <AlertTitle>
                {hata.kod === 0 ? "Yanıt gelmedi (ağ)" : `Uç reddetti — HTTP ${hata.kod}`}
              </AlertTitle>
              <AlertDescription>
                <span className="leading-6">
                  {hata.detay ?? "uç gövdesinde metin YOK — sebep ölçülemedi, durum kodu tek kanıt"}
                </span>
                {hata.kod === 0 ? (
                  <span className="mt-1 block font-medium">
                    İstek gitmiş, yanıt kaybolmuş OLABİLİR. Körlemesine tekrar gönderme; önce planın
                    durumunu ölç.
                  </span>
                ) : null}
              </AlertDescription>
            </Alert>
          ) : null}

          {/* ---- SONUÇ: UÇTAN GELEN GÖVDE, PANONUN YORUMU DEĞİL ------------- */}
          {sonuc !== null ? (
            <div className="rounded-md border bg-muted/30 p-3">
              <h5 className="text-muted-foreground text-[11px] uppercase">Ucun yanıtı</h5>
              <Satir etiket="Plan">
                <code className="break-all font-mono text-xs">{sonuc.plan_id ?? kimlik}</code>
              </Satir>
              <Satir etiket="Kontrol kararı (DEĞİŞMEZ)">
                <Metin
                  deger={sonuc.gate_verdict}
                  neden="Yanıt kontrol kararını bildirmedi"
                  teknik="yanıt gövdesinde `gate_verdict` yok"
                />
              </Satir>
              <Satir etiket="İşleme hazır planlarda">
                {sonuc.silahli === undefined ? (
                  <Yok
                    neden="Planın işleme hazır kümeye girip girmediği bildirilmedi"
                    teknik="yanıt `silahli` yazmadı — ret yanıtında bu alan zaten yoktur"
                  />
                ) : (
                  <span className="text-xs">
                    {sonuc.silahli ? "evet" : "HAYIR — gönderim düştü ve plan kümeden çıkarıldı"}
                  </span>
                )}
              </Satir>
              {/* ASIL HABER: "onaylandı" cümlesi emir gitti demek DEĞİL. */}
              <div className="mt-2 rounded-md border p-3">
                <div className="text-muted-foreground text-[11px] uppercase">İcra yolu (uç ne yaptı)</div>
                <p className="mt-1 text-sm leading-6">
                  {sonuc.icra_yolu ?? (
                    <Yok
                      neden="Bu kararın işleme nasıl döndüğü bildirilmedi"
                      teknik="yanıt `icra_yolu` yazmadı — ret ucunda icra yolu YOKTUR (ret icra etmez); onay ucunda yokluğu bir kusurdur"
                    />
                  )}
                </p>
                {sonuc.gonderim === null ? (
                  <p className="mt-1 text-muted-foreground text-[11px] leading-4">
                    gonderim null — ayna kapalı, gönderim hiç DENENMEDİ.
                  </p>
                ) : sonuc.gonderim !== undefined ? (
                  <p className="mt-1 text-muted-foreground text-[11px] leading-4">
                    gonderim.ok={String(sonuc.gonderim.ok)} · submitted={String(sonuc.gonderim.submitted)}
                    {sonuc.gonderim.detail ? ` · ${sonuc.gonderim.detail}` : ""}
                  </p>
                ) : null}
              </div>
              {sonuc.operator_reddi?.beyan ? (
                <p className="mt-2 rounded-md border bg-background p-2 text-sm leading-6">
                  {sonuc.operator_reddi.beyan}
                </p>
              ) : null}
              {sonuc.not ? (
                <p className="mt-2 rounded-md border border-uyari-h bg-uyari-t p-3 text-sm leading-6">
                  {sonuc.not}
                </p>
              ) : null}
              {sonuc.neden ? <p className="mt-2 text-muted-foreground text-[11px] leading-4">{sonuc.neden}</p> : null}
              <p className="mt-2 text-muted-foreground text-[11px] leading-4">
                Bu blok GÖNDERİM ANININ yanıtıdır ve donuktur. Liste yeniden okundu; yukarıdaki gövde
                hâlâ karar ÖNCESİNİN kopyasını gösteriyor — çekmeceyi kapatıp sembolü yeniden aç.
              </p>
            </div>
          ) : null}
        </section>
      </div>
    </>
  );
}
