"use client";

/* ============================================================================
   KARAR PANELİ — çift adımlı onay, ve iki tık arasında YAZILI olan şey
   ----------------------------------------------------------------------------
   OPERATÖR ŞİKÂYETİ (2026-08-25): "review butonuna basınca onaylayabilmem için
   bir ekran açılması gerekli." Önceki turda onay bilerek dışarıda bırakılmıştı
   (gerekçesi `OnayCekmecesi.tsx` başlığında: geri alınamaz icra, bir görev
   listesinin satır sonuna konmaz). O gerekçe HÂLÂ GEÇERLİ — bu yüzden düğme
   satır sonunda değil, kalemin TAM kanıtının altında ve ÇİFT ADIMLI duruyor.

   ÇİFT ADIMIN TEK İŞİ "yanlışlıkla basma"yı önlemek DEĞİL; iki tık arasına
   OKUNACAK BİR CÜMLE koymaktır. O cümle `onayEylem.ts::onayHedefi` tarafından
   UÇTAN/PLANDAN GELEN GERÇEK ALANLARDAN kuruluyor — ekranda uydurma bir "n adet"
   yazmıyoruz, çünkü plan satırı adet TAŞIMIYOR (broker.size_position lotu gönderim
   anında öz sermayeden hesaplıyor) ve o yokluk cümlenin İÇİNDE yazılı.

   İYİMSER GÜNCELLEME YOK: gönderim bittiğinde ekranda görünen her şey UÇTAN GELEN
   GÖVDEDİR. Panonun "oldu herhâlde" diye çizdiği bir başarı, `icra_yolu` "ayna:
   GÖNDERİLEMEDİ" derken operatöre emir gitti dedirtirdi — P-2026-08-07-VLO tam
   olarak bu sınıftı (onay verildi, emir hiç gitmedi, kimse görmedi).

   HATA HÂLLERİ AYRI VE ADLI (`onayEylem.ts::hataMetni`): 400/409 ucun REDDİ (gerekçe
   aynen), 401 oturum düşmesi, 403 L0 kısıtı, 404 kalem yok, 5xx sunucu, 0 ağ. Ağ
   hâlinde "yazılmadı" DEMİYORUZ: istek gitmiş, yanıt kaybolmuş olabilir.
   ============================================================================ */
import { useState } from "react";

import { CircleAlert, ShieldAlert, Send, Ban, Undo2 } from "lucide-react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";

import { Olculemedi, Satir, zamanMetni } from "./parcalar";
import type { KuyrukOgesi } from "./onaylar";
import {
  apiPost,
  hataMetni,
  onayHedefi,
  type DefterKararSonucu,
  type HataMetni,
  type OnayHedefi,
  type PlanOnaySonucu,
} from "./onayEylem";

/** Operatörün seçtiği yön. Plan ucunda YALNIZ `approve` vardır (uçta red dalı yok). */
type Yon = "approve" | "reject";

type Asama =
  | { readonly ad: "hazir" }
  /** Birinci tık alındı; ikinci tık bekleniyor ve arada cümle OKUNUYOR. */
  | { readonly ad: "teyit"; readonly yon: Yon }
  | { readonly ad: "gonderiliyor"; readonly yon: Yon }
  | { readonly ad: "bitti"; readonly yon: Yon; readonly basarili: boolean };

/** Plan yanıtındaki gönderim bloğu bir HÜKÜM taşır; tonu tek yerde eşlenir. */
function gonderimTonu(s: PlanOnaySonucu): "iyi" | "uyari" {
  const g = s.gonderim;
  if (g && g.ok === true && (g.submitted ?? 0) > 0) return "iyi";
  return "uyari";
}

function YonEtiket({ yon }: { readonly yon: Yon }) {
  return (
    <Badge variant={yon === "approve" ? "default" : "destructive"} className="font-mono text-[10px]">
      {yon}
    </Badge>
  );
}

export function KararPaneli({
  oge,
  seviye,
  seviyeNeden,
  halt,
  broker,
  mod,
  tazele,
}: {
  readonly oge: KuyrukOgesi;
  /** `/api/approvals.level` — otonomi seviyesi. `undefined` = ölçülemedi (0 DEĞİL). */
  readonly seviye: number | undefined;
  readonly seviyeNeden: string;
  /** `/api/today.halted`. `undefined` = ölçülemedi. */
  readonly halt: boolean | undefined;
  /** `/api/today.broker` — ADAPTÖR erişilebilirliği; gönderim anahtarı DEĞİL (bkz. onayEylem.ts). */
  readonly broker: string | undefined;
  readonly mod: string | undefined;
  /** Kuyruğu yeniden okur. Gönderimden SONRA çağrılır — iyimser güncelleme yerine yeniden ölçüm. */
  readonly tazele: () => void;
}) {
  const { hedef, engel } = onayHedefi(oge);
  const [asama, setAsama] = useState<Asama>({ ad: "hazir" });
  const [gerekce, setGerekce] = useState("");
  const [planSonuc, setPlanSonuc] = useState<PlanOnaySonucu | null>(null);
  const [defterSonuc, setDefterSonuc] = useState<DefterKararSonucu | null>(null);
  const [hata, setHata] = useState<HataMetni | null>(null);

  /* ---- GÖNDERİLEMEZ HÂLLER: DÜĞME YERİNE CÜMLE -------------------------- */
  if (hedef === null) {
    return (
      <Alert>
        <Ban />
        <AlertTitle>Bu kalem bu ekrandan karara bağlanamaz</AlertTitle>
        <AlertDescription>
          {engel ?? "sebep ölçülemedi — `onayHedefi` engel metni döndürmedi (bu bir kusurdur)"}
        </AlertDescription>
      </Alert>
    );
  }

  // L0 KAPISI ÖNCEDEN OKUNUR AMA UYDURULMAZ: seviye ölçülemediyse ENGEL KOYMAYIZ —
  // uç zaten fail-closed ve 403'ün gerekçesini metin olarak veriyor. "Ölçemedim" diyerek
  // bir kararı engellemek, ölçülemeyen bir değere dayanarak karar vermektir.
  const l0Kilidi = hedef.l1Gerekir && seviye !== undefined && seviye < 1;

  async function gonder(yon: Yon, h: OnayHedefi) {
    setAsama({ ad: "gonderiliyor", yon });
    setHata(null);
    // PLAN UCU GÖVDE OKUMUYOR (`api.py::api_plan_onayla` — `request.json()` çağrısı YOK); yine de boş
    // nesne gidiyor çünkü `apiPost` her istekte bir gövde yazıyor ve FastAPI okumadığı
    // gövdeyi görmezden geliyor. Defter ucu ise gövdeyi ZORUNLU okuyor.
    const govde = h.cesit === "plan" ? {} : { decision: yon, reason: gerekce.trim() };
    const s = await apiPost(h.yol, govde);
    if (!s.ok) {
      const hm = hataMetni(s, h.yol);
      setHata(hm);
      setAsama({ ad: "bitti", yon, basarili: false });
      toast.error(hm.baslik, { description: hm.govde });
      return;
    }
    if (h.cesit === "plan") {
      const g = (s.govde ?? {}) as PlanOnaySonucu;
      setPlanSonuc(g);
      setAsama({ ad: "bitti", yon, basarili: true });
      // BAŞLIK UÇTAN: "onaylandı" demek yetmez — asıl haber `icra_yolu`dur (emir gitti mi).
      toast.success(`Plan onaylandı: ${g.ticker ?? h.kimlik}`, {
        description: g.icra_yolu ?? "uç `icra_yolu` yazmadı — gönderimin sonucu ÖLÇÜLEMEDİ",
      });
    } else {
      const g = (s.govde ?? {}) as DefterKararSonucu;
      setDefterSonuc(g);
      setAsama({ ad: "bitti", yon, basarili: true });
      toast.success(`Karar deftere yazıldı: ${g.decision ?? yon}`, {
        description:
          g.davranissal === true
            ? "satır BAĞLAYICI — L1+'ta uygulama kapısı bu kimliği arar"
            : (g.not ?? "satır davranışsal değil — sistemin davranışı değişmedi"),
      });
    }
    // KUYRUK YENİDEN OKUNUR (iyimser güncelleme yerine yeniden ölçüm). Bu paneldeki
    // kanıt bloğu gönderim ANININ kopyasıdır ve öyle kalır; tazelenen şey LİSTEDİR.
    tazele();
  }

  const gonderiliyor = asama.ad === "gonderiliyor";

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Karar</h4>
        <Badge variant="outline" className="font-mono text-[10px]">
          POST {hedef.yol}
        </Badge>
      </div>

      {/* ---- GERİ ALINABİLİRLİK: EKRAN KENDİ SINIRINI SÖYLER --------------- */}
      <Alert variant={hedef.geriAlinamaz ? "destructive" : "default"}>
        {hedef.geriAlinamaz ? <ShieldAlert /> : <CircleAlert />}
        <AlertTitle>
          {hedef.geriAlinamaz ? "GERİ ALINAMAZ — gerçek emir gönderilebilir" : "Geri alınabilir: defter kararı"}
        </AlertTitle>
        <AlertDescription>
          <span className="leading-6">{hedef.geriAlmaNotu}</span>
        </AlertDescription>
      </Alert>

      {/* ---- ÖLÇÜLEN BAĞLAM: uç reddedebilir, sebebi ŞİMDİDEN görünsün ------ */}
      <div className="rounded-md border bg-muted/30 p-3">
        <Satir etiket="Gidecek kimlik">
          <code className="break-all font-mono text-xs">{hedef.kimlik}</code>
        </Satir>
        <Satir etiket="Uçta red yolu">
          {hedef.redVar ? (
            <span className="text-xs">
              var — <code className="font-mono text-[11px]">decision: &quot;reject&quot;</code>
            </span>
          ) : (
            <span className="text-xs">
              YOK — <code className="font-mono text-[11px]">POST /api/plan/&#123;id&#125;/onayla</code> yalnız
              onay alır (gövde bile okunmuyor). Sahte bir &quot;Reddet&quot; düğmesi konmadı.
            </span>
          )}
        </Satir>
        <Satir etiket="Uygulama kapısı açar mı">
          {hedef.kapiAcar === null ? (
            <span className="text-xs">ilgisiz — bu uç karar YAZMAZ, İCRA eder</span>
          ) : hedef.kapiAcar ? (
            <span className="text-xs">EVET — satır L1+&apos;ta bir uygulamayı açar (davranışsal)</span>
          ) : (
            <span className="text-xs">hayır — hiçbir kapı bu öneki okumaz</span>
          )}
        </Satir>
        <Satir etiket="Otonomi seviyesi">
          {seviye === undefined ? <Olculemedi neden={seviyeNeden} kisa /> : <span className="text-xs">L{seviye}</span>}
        </Satir>
        {hedef.cesit === "plan" ? (
          <>
            <Satir etiket="HALT">
              {halt === undefined ? (
                <Olculemedi neden="Durdurma kolunun çekili olup olmadığı bildirilmedi" teknik="/api/today `halted` alanını döndürmedi" kisa />
              ) : (
                <span className="text-xs">{halt ? "ÇEKİLİ — uç 409 verir" : "çekili değil"}</span>
              )}
            </Satir>
            <Satir etiket="Broker (adaptör)">
              {broker === undefined ? (
                <Olculemedi neden="Hangi broker bağlantısının kullanıldığı bildirilmedi" teknik="/api/today `broker` alanını döndürmedi" kisa />
              ) : (
                <span className="text-xs">
                  {broker}
                  {mod ? ` · mod ${mod}` : ""}
                </span>
              )}
            </Satir>
          </>
        ) : null}
      </div>

      {hedef.cesit === "plan" && halt === true ? (
        <p className="rounded-md border border-uyari-h bg-uyari-t p-3 text-sm leading-6">
          HALT çekili görünüyor. Uç bu durumda onayı REDDEDER (409: &quot;HALT aktif — yeni giriş
          silahlanmaz&quot;). Düğme yine de kilitlenmedi: bu bayrak 15 sn&apos;lik bir nabızdan geliyor
          ve kararı UÇ verir — panonun bayat bir okumayla onayı engellemesi, ölçülemeyen bir değere
          dayanarak karar vermek olurdu.
        </p>
      ) : null}

      {l0Kilidi ? (
        <Alert>
          <Ban />
          <AlertTitle>Bu uzaya L0&apos;da karar yazılamaz</AlertTitle>
          <AlertDescription>
            Kimlik öneki bir uygulama kapısı açıyor (<code className="font-mono text-[11px]">rev:</code> /{" "}
            <code className="font-mono text-[11px]">rec:</code>) ve uç bunları L1+&apos;a kısıtlıyor
            (api.py::api_approve): L0&apos;da yazılan bir <code className="font-mono text-[11px]">approve</code>{" "}
            yarın icraya dönüşebilirdi. Sistem şu an L{seviye}. Düğme kilitli — 403 alacağı belli olan
            bir isteği göndermek, operatöre yanlış bir &quot;denedim&quot; hissi verirdi.
          </AlertDescription>
        </Alert>
      ) : null}

      {/* ---- GEREKÇE (yalnız defter ucunda alan var) ----------------------- */}
      {hedef.cesit === "defter" && asama.ad !== "bitti" ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="karar-gerekce" className="text-xs">
            Gerekçe (isteğe bağlı — <code className="font-mono text-[11px]">reason</code> alanına yazılır)
          </Label>
          <Textarea
            id="karar-gerekce"
            value={gerekce}
            onChange={(e) => setGerekce(e.target.value)}
            disabled={gonderiliyor || l0Kilidi}
            rows={2}
            placeholder="Neden bu kararı verdin? Defterde kalır; boş bırakılabilir."
          />
          <p className="text-muted-foreground text-[11px] leading-4">
            Gerekçe yazarsan uç ayrıca <code className="font-mono text-[11px]">memory.distill_lessons()</code>{" "}
            çağırıyor (api.py::api_approve) — yani metin ders damıtmasına girer. Boşsa çağrılmaz.
          </p>
        </div>
      ) : null}

      <Separator />

      {/* ---- BİRİNCİ TIK --------------------------------------------------- */}
      {asama.ad === "hazir" ? (
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant={hedef.geriAlinamaz ? "destructive" : "default"}
            disabled={l0Kilidi}
            onClick={() => setAsama({ ad: "teyit", yon: "approve" })}
          >
            <Send aria-hidden />
            {hedef.cesit === "plan" ? "Planı onayla…" : "Onayla…"}
          </Button>
          {hedef.redVar ? (
            <Button
              type="button"
              variant="outline"
              disabled={l0Kilidi}
              onClick={() => setAsama({ ad: "teyit", yon: "reject" })}
            >
              <Ban aria-hidden />
              Reddet…
            </Button>
          ) : null}
          <span className="self-center text-muted-foreground text-[11px]">
            İki adım: bu tık niyeti alır, gönderim ikinci tıkla olur.
          </span>
        </div>
      ) : null}

      {/* ---- İKİ TIK ARASI: NE OLACAĞI YAZILI ------------------------------ */}
      {asama.ad === "teyit" || asama.ad === "gonderiliyor" ? (
        <div
          className={
            asama.yon === "approve" && hedef.geriAlinamaz
              ? "rounded-md border border-destructive/40 bg-destructive/5 p-3"
              : "rounded-md border bg-muted/30 p-3"
          }
          aria-live="polite"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-sm">İkinci tık şunu yapacak</span>
            <YonEtiket yon={asama.yon} />
          </div>
          <p className="mt-2 text-sm leading-6">
            {asama.yon === "approve"
              ? hedef.nedir
              : `\`${hedef.kimlik}\` kimliğine bir "reject" satırı yazar (approvals.jsonl). ` +
                (hedef.kapiAcar
                  ? "Bekleyen uygulama kapısı KAPALI kalır — fail-closed zaten reddediyordu, bu satır reddi KAYDA geçirir."
                  : "Hiçbir kapı bu öneki okumaz; karar yalnız deftere düşer.")}
          </p>
          {hedef.cesit === "defter" && gerekce.trim() !== "" ? (
            <p className="mt-2 whitespace-pre-wrap rounded-md border bg-background p-2 text-xs leading-5">
              gerekçe: {gerekce.trim()}
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              variant={asama.yon === "approve" && hedef.geriAlinamaz ? "destructive" : "default"}
              disabled={gonderiliyor}
              onClick={() => void gonder(asama.yon, hedef)}
            >
              {gonderiliyor ? <Spinner /> : <Send aria-hidden />}
              {gonderiliyor ? "Gönderiliyor — bekle" : "EVET, GÖNDER"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={gonderiliyor}
              onClick={() => setAsama({ ad: "hazir" })}
            >
              <Undo2 aria-hidden />
              Vazgeç
            </Button>
          </div>
        </div>
      ) : null}

      {/* ---- SONUÇ: UÇTAN GELEN GÖVDE, PANONUN YORUMU DEĞİL ---------------- */}
      {hata !== null ? (
        <Alert variant="destructive">
          <CircleAlert />
          <AlertTitle>{hata.baslik}</AlertTitle>
          <AlertDescription>
            <span className="leading-6">{hata.govde}</span>
            {hata.oturumDustu ? (
              <span className="mt-1 block font-medium">
                Çare: panodan çık, yeniden gir. Tazelemek bu hâli düzeltmez.
              </span>
            ) : null}
          </AlertDescription>
        </Alert>
      ) : null}

      {planSonuc !== null ? (
        <div className="rounded-md border bg-muted/30 p-3">
          <h5 className="text-muted-foreground text-[11px] uppercase">
            Ucun yanıtı — <code className="font-mono">POST {hedef.yol}</code>
          </h5>
          <Satir etiket="Sembol / plan">
            <span className="text-xs">
              {planSonuc.ticker ?? "?"} · <code className="font-mono">{planSonuc.plan_id ?? hedef.kimlik}</code>
            </span>
          </Satir>
          <Satir etiket="Kontrol kararı (DEĞİŞMEZ)">
            {planSonuc.gate_verdict ?? <Olculemedi neden="Kontrollerin kararı bildirilmedi" teknik="yanıt `gate_verdict` yazmadı" kisa />}
          </Satir>
          <Satir etiket="Onay damgası">
            {zamanMetni(planSonuc.operator_onayi?.ts ?? planSonuc.ts) ?? (
              <Olculemedi neden="Onayın hangi anda işlendiği bildirilmedi" teknik="yanıt `operator_onayi.ts` / `ts` yazmadı" kisa />
            )}
          </Satir>
          <Satir etiket="İşleme hazır planlarda">
            {planSonuc.silahli === undefined ? (
              <Olculemedi neden="Planın işleme hazır listeye girip girmediği bildirilmedi" teknik="yanıt `silahli` yazmadı" kisa />
            ) : (
              <span className="text-xs">
                {planSonuc.silahli ? "evet" : "HAYIR — gönderim düştü ve plan kümeden çıkarıldı"}
                {planSonuc.armed_n === undefined ? "" : ` · kümede ${planSonuc.armed_n} plan`}
              </span>
            )}
          </Satir>
          <Satir etiket="Zaten onaylıydı / hazırdı">
            <span className="text-xs">
              {planSonuc.zaten_onayliydi === undefined ? "?" : planSonuc.zaten_onayliydi ? "evet" : "hayır"} /{" "}
              {planSonuc.zaten_silahliydi === undefined ? "?" : planSonuc.zaten_silahliydi ? "evet" : "hayır"}
            </span>
          </Satir>
          {/* ASIL HABER BURADA: "onaylandı" cümlesi emir gitti demek DEĞİL. */}
          <div
            className={
              gonderimTonu(planSonuc) === "iyi"
                ? "mt-2 rounded-md border border-basari-h bg-basari-t p-3"
                : "mt-2 rounded-md border border-uyari-h bg-uyari-t p-3"
            }
          >
            <div className="text-muted-foreground text-[11px] uppercase">İcra yolu (uç ne yaptı)</div>
            <p className="mt-1 text-sm leading-6">
              {planSonuc.icra_yolu ?? (
                <Olculemedi neden="Emrin gönderilip gönderilmediği bildirilmedi — gittiğini varsayma" teknik="yanıt `icra_yolu` yazmadı — gönderimin sonucu ölçülemedi" />
              )}
            </p>
            {planSonuc.gonderim === null ? (
              <p className="mt-1 text-muted-foreground text-[11px] leading-4">
                `gonderim` null — ayna kapalı, gönderim hiç DENENMEDİ.
              </p>
            ) : planSonuc.gonderim !== undefined ? (
              <p className="mt-1 text-muted-foreground text-[11px] leading-4">
                gonderim.ok={String(planSonuc.gonderim.ok)} · submitted={String(planSonuc.gonderim.submitted)}
                {planSonuc.gonderim.detail ? ` · ${planSonuc.gonderim.detail}` : ""}
                {planSonuc.gonderim.dropped_ids && planSonuc.gonderim.dropped_ids.length > 0
                  ? ` · düşen: ${planSonuc.gonderim.dropped_ids.join(", ")}`
                  : ""}
              </p>
            ) : null}
          </div>
          {planSonuc.icra_yasasi === false && planSonuc.not ? (
            <p className="mt-2 rounded-md border border-uyari-h bg-uyari-t p-3 text-sm leading-6">
              {planSonuc.not}
            </p>
          ) : null}
          {planSonuc.neden ? (
            <p className="mt-2 text-muted-foreground text-[11px] leading-4">{planSonuc.neden}</p>
          ) : null}
          <p className="mt-2 text-muted-foreground text-[11px] leading-4">
            Bu blok GÖNDERİM ANININ yanıtıdır ve donuktur. Kuyruk yeniden okundu; yukarıdaki kanıt
            bloğu hâlâ onay ÖNCESİNİN kopyasını gösteriyor — çekmeceyi kapatıp satırı yeniden aç.
          </p>
        </div>
      ) : null}

      {defterSonuc !== null ? (
        <div className="rounded-md border bg-muted/30 p-3">
          <h5 className="text-muted-foreground text-[11px] uppercase">
            Ucun yanıtı — <code className="font-mono">POST {hedef.yol}</code>
          </h5>
          <Satir etiket="Yazılan kimlik">
            <code className="break-all font-mono text-xs">{defterSonuc.id ?? hedef.kimlik}</code>
          </Satir>
          <Satir etiket="Karar">
            {defterSonuc.decision === undefined ? (
              <Olculemedi neden="Hangi kararın yazıldığı bildirilmedi" teknik="yanıt `decision` yazmadı" kisa />
            ) : (
              <Badge variant="outline" className="font-mono text-[10px]">
                {defterSonuc.decision}
              </Badge>
            )}
          </Satir>
          <Satir etiket="Davranışsal mı">
            {defterSonuc.davranissal === undefined ? (
              <Olculemedi neden="Kararın sistemi bağlayıp bağlamadığı bildirilmedi" teknik="yanıt `davranissal` yazmadı — bağlayıcılığı önekten çıkarma" kisa />
            ) : (
              <span className="text-xs">
                {defterSonuc.davranissal
                  ? "EVET — L1+'ta uygulama kapısı bu satırı arar"
                  : "hayır — davranış DEĞİŞMEDİ"}
              </span>
            )}
          </Satir>
          {defterSonuc.not ? (
            <p className="mt-2 rounded-md border bg-background p-2 text-sm leading-6">{defterSonuc.not}</p>
          ) : null}
          <p className="mt-2 text-muted-foreground text-[11px] leading-4">
            Karar YAZILDI — UYGULANMADI. Uç yalnız deftere satır ekler (api.py::api_approve sözleşmesi);
            uygulamayı ayrı uçlar yapar (<code className="font-mono">POST /api/skills/revision</code> ·{" "}
            <code className="font-mono">POST /api/skills/apply</code>) ve onlar bu ekranda bağlı DEĞİL.
          </p>
        </div>
      ) : null}

      {asama.ad === "bitti" ? (
        <Button type="button" variant="ghost" size="sm" onClick={() => setAsama({ ad: "hazir" })}>
          <Undo2 aria-hidden />
          {asama.basarili ? "Bu kalem için yeni bir karar yaz" : "Yeniden dene"}
        </Button>
      ) : null}
    </section>
  );
}
