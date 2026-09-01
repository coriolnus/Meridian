/* ============================================================================
   ONAY EYLEMİ — hangi kalem HANGİ uca gider, ve o uç ne yapar
   ----------------------------------------------------------------------------
   BU DOSYA `meridian/api.py` VE `meridian/loop.py` OKUNARAK YAZILDI, TAHMİN
   EDİLMEDİ. Okunan yerler ve okunan şey:

     · `api.py::api_plan_onayla`  — `POST /api/plan/{plan_id}/onayla`.
       GÖVDE OKUNMUYOR (fonksiyon `request.json()` çağırmıyor); kararı
       `loop.operator_onay_ver` veriyor ve dönüşü AYNEN yanıt gövdesi oluyor.
       Ret için `raise HTTPException(status_code=res["kod"], detail=res["neden"])`
       — yani 404/409'un gerekçesi `detail` alanında METİN olarak geliyor.
     · `loop.operator_onay_ver` (loop.py:477) — ret kodları ÖLÇÜLDÜ:
         404 plan defterde yok
         409 NO_GO · REVIEW değil · tarihsiz · seansı geçmiş · HALT · zaten açık
             pozisyon · slot yok
       200 gövdesi: {ok, kod, plan_id, ticker, date, gate_verdict, operator_onayi,
       silahli, zaten_onayliydi, zaten_silahliydi, icra_yasasi, armed_n, ts,
       icra_yolu, gonderim, not, neden}.
       `icra_yolu` GÖNDERİMİN SONUCUNU söyler (loop.py:595-620): ayna kapalıysa
       "broker'a GİTMEZ", açıksa "bracket GÖNDERİLDİ / dedup / DÜŞTÜ / GÖNDERİLEMEDİ".
     · `api.py::api_approve`      — `POST /api/approvals/{approval_id}`.
       GÖVDE: `{"decision": "approve"|"reject", "reason": str}` (`await request.json()`
       ZORUNLU — gövdesiz istek ayrıştırma hatası verir). YALNIZ YAZAR, hiçbir şey
       UYGULAMAZ. Dönüş: {ok, id, decision, davranissal, (not, kunye)}.
       403: `KAPI_OKUYAN_ONEKLER` ("rev", "rec") L0'da reddedilir; tanınmayan önek
       de L0'da 403 alır (fail-closed).

   KİMLİK UZAYI — YANLIŞ UCA GÖNDERMEK SESSİZ BİR KAYIPTIR (api.py:1948, 2044):
     `arming:{kurulum}`        kapı OKUMAZ → karar kaydı, davranış değişmez
     `rev:{skill}`             kapı OKUR   → `POST /api/skills/revision` bunu arar
     `rec:{skill}`             kapı OKUR   → `POST /api/skills/apply` bunu arar
     `kayit:{skill}:{action}`  kapı OKUMAZ → uygulayıcısı OLMAYAN önerinin kaydı
   Uygulanabilir karşılığı olmayan bir Eksen-2 önerisinin kararı `kayit:`e yazılır
   ve gelen kutusu onu `karar_kaydi`ndan OKUR (api.py:_karar_kaydi). Aynı kararı
   `rec:`e yazsaydık: L0'da 403 alırdık, L1'de uygulayıcısı olmayan bir eylemin
   kapısını açardık, VE satır gelen kutusunda "hâlâ bekliyor" görünmeye devam
   ederdi — karar verilir ama kaybolurdu. Hedef kimlik bu yüzden ÖLÇÜLEREK seçilir,
   `oge.id`den varsayılmaz.

   BELİRSİZLİKTE GÖNDERİLMEZ: `uygulanabilir` alanı HİÇ gelmediyse (uç eski, ya da
   alan düştü) iki uzaydan hangisinin doğru olduğu BİLİNMİYOR demektir. Tahmin edip
   göndermek, yukarıdaki sessiz kaybın ta kendisi olurdu — engel döner, sebebiyle.
   ============================================================================ */
import type { KuyrukOgesi } from "./onaylar";
import type { PlanOzeti } from "./tipler";

/* --- YAZAN İSTEK ---------------------------------------------------------- */

/* NEDEN `kimlik/gonder.ts`TEN İMPORT EDİLMEDİ (bilinçli tekrar, `parcalar.tsx`
   başlığındaki gerekçenin aynısı): bu tur paralel ajanlarla koşuyor ve dosya
   ayrıklığı YAZMA tarafını ayırıyor. Başka bir ajanın uçuş hâlindeki dosyasından
   import etmek, onun dışa aktarım kümesi değiştiği an bu yüzeyi derlenemez hâle
   getirirdi. Birleştirme tur-kapanışı işidir. */

export interface GonderSonucu {
  readonly ok: boolean;
  /** HTTP durum kodu. `0` = yanıt HİÇ gelmedi (ağ/iptal) — sunucunun sustuğu hâl. */
  readonly kod: number;
  /** FastAPI `detail` alanı. Okunamadıysa `null` — boş dizge YAZILMAZ (yalan olurdu). */
  readonly detay: string | null;
  /** Başarı gövdesi. Ayrıştırılamadıysa `null`. */
  readonly govde: unknown;
}

function detaydanMetin(g: unknown): string | null {
  if (g === null || typeof g !== "object") return null;
  const d = (g as { detail?: unknown }).detail;
  if (typeof d === "string" && d.trim() !== "") return d;
  // FastAPI doğrulama hatası `detail`i bir DİZİDİR ({loc,msg,type}); `msg`leri birleştiriyoruz.
  if (Array.isArray(d)) {
    const m = d
      .map((x) => (x !== null && typeof x === "object" ? (x as { msg?: unknown }).msg : null))
      .filter((x): x is string => typeof x === "string");
    if (m.length > 0) return m.join(" · ");
  }
  return null;
}

/** Tek POST. Ne fırlatır ne yutar: her hâl dönüş nesnesinde ADIYLA durur. */
export async function apiPost(yol: string, govde?: unknown): Promise<GonderSonucu> {
  let y: Response;
  try {
    y = await fetch(yol, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(govde ?? {}),
    });
  } catch (e) {
    // AĞ DÜŞMESİ BİR HTTP CEVABI DEĞİLDİR: `kod: 0` onu "sunucu bir şey söyledi"den ayırır.
    return { ok: false, kod: 0, detay: e instanceof Error ? e.message : String(e), govde: null };
  }
  let cozulen: unknown = null;
  try {
    cozulen = await y.json();
  } catch {
    // YASA 4 · sessiz-yutma İŞARETLİ: gövde JSON değilse (proxy'nin düz metin 502'si)
    // ayrıştırma hatası ASIL sonucu gizlememeli — durum kodu `kod` alanında duruyor.
  }
  return { ok: y.ok, kod: y.status, detay: detaydanMetin(cozulen), govde: y.ok ? cozulen : null };
}

/* --- PLANIN OKUNAN KESİTİ ------------------------------------------------- */

/**
 * `trade_plans.jsonl` satırının BU EKRANIN okuduğu alanları. `tipler.ts::PlanOzeti`yi
 * genişletir (o dosya Çizelge ile PAYLAŞILAN, imzası bozulmaz).
 *
 * ALAN KÜMESİ ÖLÇÜLDÜ (`state/trade_plans.jsonl` son 40 satırın anahtar birleşimi,
 * 2026-08-25): broker_status · date · dormant_setup · entry_trigger · exploration ·
 * gate_checks · gate_reasons · gate_verdict · id · llm_opinion · p_win_shadow ·
 * profit_target · r_multiple_expected · regime_at_plan · score · sector · setup ·
 * side · size_r · skill_chain · stop · strategy_version · targets · ticker.
 *
 * `risk_dollars` ve ADET (`qty`) BU SATIRDA YOK ve alan olarak da eklenmedi —
 * `broker.size_position` (broker.py:544) ikisini de GÖNDERİM ANINDA öz sermayeden
 * hesaplıyor. Ekranda "ölçülemedi + neden" olarak durur; uydurulmaz.
 */
export interface PlanAyrintisi extends PlanOzeti {
  readonly side?: string;
  readonly stop?: number | null;
  readonly profit_target?: number | null;
  readonly targets?: readonly number[];
  readonly r_multiple_expected?: number | null;
  readonly regime_at_plan?: string;
  readonly strategy_version?: number;
  readonly dormant_setup?: boolean;
  readonly exploration?: boolean;
  readonly p_win_shadow?: number | null;
  readonly broker_status?: string;
  readonly skill_chain?: readonly string[];
  readonly gate_checks?: readonly KapiKontrolu[];
}

/** `gate_checks` satırı — kapının TEK TEK hangi kontrolü geçtiği/düştüğü. */
export interface KapiKontrolu {
  readonly check?: string;
  readonly passed?: boolean;
  /** `"hard"` | `"soft"` — sert kontrol düşerse hüküm NO_GO, yumuşak düşerse REVIEW. */
  readonly severity?: string;
  /** Ölçülen değer: sayı da olabilir metin de (`"industrials"`). */
  readonly value?: unknown;
  readonly threshold?: string;
  readonly note?: string | null;
}

/* --- HEDEF ÇÖZÜMÜ --------------------------------------------------------- */

export type HedefCesidi = "plan" | "defter";

export interface OnayHedefi {
  readonly cesit: HedefCesidi;
  /** POST yolu (kimlik `encodeURIComponent`ten geçmiş hâliyle gömülü). */
  readonly yol: string;
  /** Uca giden HAM kimlik — ekranda aynen yazılır, operatör onu doğrudan curl'e geçirebilsin. */
  readonly kimlik: string;
  /** Uç `reject` kabul ediyor mu? `POST /api/plan/{id}/onayla` ETMİYOR (ölçüldü). */
  readonly redVar: boolean;
  /**
   * Yazılan satır ileride bir UYGULAMA KAPISINI açıyor mu? (`api.py::KAPI_OKUYAN_ONEKLER`)
   * `false` = hiçbir kapı bu öneki okumaz, davranış DEĞİŞMEZ.
   * Plan ucunda kavram başka: orada karar kaydı değil İCRA var — alan `null`.
   */
  readonly kapiAcar: boolean | null;
  /** Uç L1+ istiyor mu? (`rev:`/`rec:` L0'da 403.) */
  readonly l1Gerekir: boolean;
  /** İKİ TIK ARASINDA OKUNAN CÜMLE — uçtan/plandan gelen GERÇEK alanlardan kurulur. */
  readonly nedir: string;
  /** Geri alınabilirlik hükmü + gerekçesi. */
  readonly geriAlinamaz: boolean;
  readonly geriAlmaNotu: string;
}

export interface HedefCozumu {
  readonly hedef: OnayHedefi | null;
  /** `hedef === null` ise NEDEN gönderilemediği. Boş bir ekran yerine bir cümle. */
  readonly engel: string | null;
}

/** Sayıyı okunur metne çevirir; ölçülemeyen değer `null` döner (çağıran neden yazar). */
function sayi(x: number | null | undefined, basamak = 2): string | null {
  if (x === undefined || x === null || !Number.isFinite(x)) return null;
  return x.toLocaleString("tr-TR", { minimumFractionDigits: basamak, maximumFractionDigits: basamak });
}

/**
 * GERİ ALINAMAZ VARSAYILIR — VE BU BİR ÖLÇÜM SONUCU, KORKAKLIK DEĞİL.
 * Panonun elindeki tek broker göstergesi `/api/today.broker` ve o alan
 * `"Alpaca · paper" if _alpaca_present() else "Dahili broker · paper"` (api.py:276),
 * yani ADAPTÖRÜN ERİŞİLEBİLİRLİĞİNİ ölçüyor. Gönderim dalını seçen anahtar ise
 * `config.BROKER == "alpaca_paper"` (loop.py:595) ve o değer HİÇBİR uçtan pano'ya
 * gelmiyor. İki ayrı soru; birine bakıp öbürüne cevap vermek tam da bu deponun
 * "ölçüm bağlamı tuzağı" sınıfı olurdu. Gerçek icra yolu ancak yanıtın `icra_yolu`
 * alanından öğrenilir — yani ONAYDAN SONRA.
 */
const PLAN_GERI_ALMA =
  "GERİ ALINAMAZ VARSAY. Onay iki şey yapar: plan işleme hazır planlara yazılır VE onay ANINDA " +
  "broker aynasına bracket emir gönderilmeye çalışılır (loop.mirror_submit_ve_kalicilastir). " +
  "Gönderilmiş bir emri BU EKRAN geri alamaz — bu yüzeyde iptal ucu bağlı DEĞİL. Depoda " +
  "`POST /api/control/cancel_open` var ama o yalnız DOLMAMIŞ giriş emirlerini iptal eder ve " +
  "burada bağlı değildir; emir DOLDUYSA hiçbir uç onu geri almaz. Ayrıca panonun elinde " +
  "gönderimin gerçekten olup olmayacağını ÖNCEDEN söyleyen bir ölçüm YOK: /api/today.broker " +
  "adaptörün erişilebilirliğini bildirir, gönderim dalını seçen anahtar (config.BROKER) hiçbir " +
  "uçtan gelmez. Gerçek icra yolu ancak yanıtın `icra_yolu` alanında görünür — yani onaydan SONRA.";

const DEFTER_GERI_ALMA_KAPILI =
  "Bu satır DAVRANIŞSAL: `approvals.jsonl`a yazılır ve L1+'ta bir uygulama kapısı (`_onay_kapisi`) " +
  "onu ARAR. Defter salt-ekleme; karar 'silinmez' ama SON SATIR KAZANIR — sonradan `reject` " +
  "yazarak kararı çevirebilirsin. UYGULAMANIN KENDİSİ BU EKRANDA DEĞİL: onu ayrı bir uç yapar " +
  "(`POST /api/skills/revision` · `POST /api/skills/apply`) ve o uçlar bu ekranda bağlı değil.";

const DEFTER_GERI_ALMA_KAPISIZ =
  "Bu satır DAVRANIŞSAL DEĞİL: bu öneki hiçbir uygulama kapısı okumaz (api.py::KAPI_OKUYAN_ONEKLER " +
  "= {rev, rec}). Karar deftere düşer, sistemin davranışı DEĞİŞMEZ. Defter salt-ekleme ve son satır " +
  "kazanır — kararı sonradan çevirebilirsin.";

/** Kimlik önekini ayırır. Önek yoksa `null` (kimlik biçimi tanınmıyor demektir). */
function onek(kimlik: string): string | null {
  const i = kimlik.indexOf(":");
  if (i <= 0 || i === kimlik.length - 1) return null;
  return kimlik.slice(0, i);
}

/** Bir kalemin gideceği uç + o ucun sözleşmesi. Belirsizlikte `hedef: null` + `engel`. */
export function onayHedefi(oge: KuyrukOgesi): HedefCozumu {
  /* ---- PLAN: ayrı uç, ayrı yasa, RED YOK -------------------------------- */
  if (oge.ayrinti.cesit === "plan") {
    const p = oge.ayrinti.plan as PlanAyrintisi;
    const id = p.id;
    if (!id) {
      return {
        hedef: null,
        engel:
          "plan satırı `id` taşımıyor — `POST /api/plan/{plan_id}/onayla` yolu KURULAMAZ. " +
          "Sembolü kimlik yerine koymak yanlış planı onaylatabilirdi; gönderilmiyor.",
      };
    }
    const tetik = sayi(p.entry_trigger);
    const stop = sayi(p.stop);
    const hedefFiyat = sayi(p.profit_target);
    const r = sayi(p.size_r);
    const parca: string[] = [
      `${p.ticker ?? "(sembolsüz plan)"} planını${p.setup ? ` (${p.setup})` : ""} silahlı giriş ` +
        `kuyruğuna alır VE onay ANINDA broker aynasına bracket emir göndermeyi dener.`,
    ];
    if (p.side) parca.push(`Yön: ${p.side}.`);
    if (tetik !== null) parca.push(`Giriş tetiği ${tetik}.`);
    if (stop !== null) parca.push(`Stop ${stop}.`);
    if (hedefFiyat !== null) parca.push(`Kâr hedefi ${hedefFiyat}.`);
    if (r !== null) parca.push(`Risk büyüklüğü ${r} R.`);
    // ADET UYDURULMAZ — VE BU CÜMLE İSTEĞE BAĞLI DEĞİL. Brief "<n> adetlik emir silahlar"
    // diyor; plan satırında adet YOK (ölçüldü) ve `broker.size_position` onu gönderim
    // anında öz sermayeden hesaplıyor. Boş bırakmak yerine yokluğu YAZILIR.
    parca.push(
      "ADET (kaç lot) BURADA ÖLÇÜLEMEZ: plan satırı adet taşımıyor ve lot, gönderim anında " +
        "öz sermayeden hesaplanıyor (broker.size_position). Aynı sebeple `risk_dollars` da " +
        "plan satırında YOK — R cinsinden büyüklük yukarıda.",
    );
    return {
      hedef: {
        cesit: "plan",
        yol: `/api/plan/${encodeURIComponent(id)}/onayla`,
        kimlik: id,
        // ÖLÇÜLDÜ: `api_plan_onayla` yalnız onay alır; gövde bile okunmuyor, `reject` diye
        // bir dal YOK. Sahte bir "Reddet" düğmesi, basıldığında hiçbir şey yapmayan (ya da
        // daha kötüsü, onaylayan) bir düğme olurdu.
        redVar: false,
        kapiAcar: null,
        l1Gerekir: false,
        nedir: parca.join(" "),
        geriAlinamaz: true,
        geriAlmaNotu: PLAN_GERI_ALMA,
      },
      engel: null,
    };
  }

  /* ---- EKSEN-2 ÖNERİSİ: İKİ AYRI KİMLİK UZAYI --------------------------- */
  if (oge.ayrinti.cesit === "oneri") {
    const uyg = oge.ayrinti.oge.uygulanabilir;
    if (uyg === undefined) {
      return {
        hedef: null,
        engel:
          "uç bu öneride `uygulanabilir` alanını döndürmedi — kararın HANGİ kimlik uzayına " +
          "yazılacağı bilinmiyor (`rec:{skill}` kapı okuyan uzay, `kayit:{skill}:{action}` " +
          "kapı okumayan uzay). Tahminle göndermek, kararın gelen kutusunda hiç görünmemesi " +
          "riskini taşır; gönderilmiyor.",
      };
    }
    if (uyg === false) {
      const kk = oge.ayrinti.karar?.id;
      if (!kk) {
        return {
          hedef: null,
          engel:
            "bu öneri uygulanabilir DEĞİL, yani kararı `kayit:{skill}:{action}` uzayına yazılmalı — " +
            "ama uç `karar_kaydi.id` döndürmedi. Kimliği panoda kurmak, aynı dizgeyi İKİ yerde " +
            "üretmek olurdu (api.py `kayit_karar_kimligi` tek kaynak); gönderilmiyor.",
        };
      }
      return {
        hedef: {
          cesit: "defter",
          yol: `/api/approvals/${encodeURIComponent(kk)}`,
          kimlik: kk,
          redVar: true,
          kapiAcar: false,
          l1Gerekir: false,
          nedir:
            `\`${kk}\` kimliğine bir karar satırı yazar (approvals.jsonl). Bu öneri UYGULANABİLİR ` +
            `DEĞİL — uygulayıcısı olmadığı için kararı kapı okumayan "kayıt" uzayına düşer. ` +
            `Gelen kutusu bu satırı okuyup kalemi "karar verilmiş" sayar; sistemin davranışı DEĞİŞMEZ.`,
          geriAlinamaz: false,
          geriAlmaNotu: DEFTER_GERI_ALMA_KAPISIZ,
        },
        engel: null,
      };
    }
  }

  /* ---- GELEN KUTUSU KİMLİĞİYLE GİDEN ÖĞELER -----------------------------
     Plan dalı yukarıda RETURN etti; kalan dört çeşidin (silahlanma · revizyon ·
     uygulanabilir öneri · bilinmeyen) hepsi ham `oge` gövdesini taşıyor ve kimlik
     ORADAN okunur — `KuyrukOgesi.kimlik` alanı DEĞİL, çünkü o alan uç kimliksiz
     döndüğünde `"tür#index"` gibi PANONUN uydurduğu bir dizgeye düşüyor
     (`onaylar.ts`) ve uca öyle bir dizge göndermek tanınmayan bir uzaya yazmaktır. */
  const kimlik = oge.ayrinti.oge.id ?? null;
  if (!kimlik) {
    return {
      hedef: null,
      engel:
        "gelen kutusu bu öğeye `id` yazmamış — `POST /api/approvals/{approval_id}` kimliksiz " +
        "çağrılamaz. Kimliği başlıktan türetmek, kapının aradığı dizgeden BAŞKA bir dizge " +
        "üretme riski taşır (api.py `onay_kimligi` tek kaynak); gönderilmiyor.",
    };
  }
  const on = onek(kimlik);
  if (on === null) {
    return {
      hedef: null,
      engel:
        `kimlik (\`${kimlik}\`) \`{önek}:{ad}\` biçiminde değil — hangi uzaya yazılacağı ` +
        `bilinmiyor. Uç tanınmayan öneki L0'da 403 ile reddeder (fail-closed); gönderilmiyor.`,
    };
  }
  const kapiAcar = on === "rev" || on === "rec";
  if (!kapiAcar && on !== "arming" && on !== "kayit") {
    return {
      hedef: null,
      engel:
        `kimlik öneki \`${on}:\` bu panonun tanıdığı dört uzaydan (arming · rev · rec · kayit) ` +
        `hiçbiri değil — uç yeni bir tür eklemiş olabilir. Tanınmayan öneke karar yazmak, ` +
        `hangi kapının onu okuyacağını BİLMEDEN icra açmak olurdu; gönderilmiyor.`,
    };
  }
  const konu = oge.konu ?? kimlik;
  return {
    hedef: {
      cesit: "defter",
      yol: `/api/approvals/${encodeURIComponent(kimlik)}`,
      kimlik,
      redVar: true,
      kapiAcar,
      l1Gerekir: kapiAcar,
      nedir: kapiAcar
        ? `\`${kimlik}\` kimliğine bir karar satırı yazar (approvals.jsonl). Konu: ${konu}. ` +
          `Bu satır BAĞLAYICI: L1+'ta uygulama kapısı (\`_onay_kapisi\`) bu kimliğe bakar, yani ` +
          `"onayla" demek ileride bir uygulamayı AÇAR. Uygulamayı bu ekran YAPMAZ — uç yalnız yazar.`
        : `\`${kimlik}\` kimliğine bir karar satırı yazar (approvals.jsonl). Konu: ${konu}. ` +
          `Bu öneki hiçbir uygulama kapısı okumaz: karar defterde durur, sistemin davranışı DEĞİŞMEZ.`,
      geriAlinamaz: false,
      geriAlmaNotu: kapiAcar ? DEFTER_GERI_ALMA_KAPILI : DEFTER_GERI_ALMA_KAPISIZ,
    },
    engel: null,
  };
}

/* --- YANIT GÖVDELERİ ------------------------------------------------------ */

/** `POST /api/plan/{id}/onayla` 200 gövdesi (loop.operator_onay_ver dönüşü, AYNEN). */
export interface PlanOnaySonucu {
  readonly ok?: boolean;
  readonly plan_id?: string;
  readonly ticker?: string;
  readonly date?: string;
  readonly gate_verdict?: string;
  readonly operator_onayi?: { readonly ts?: string; readonly kanal?: string };
  readonly silahli?: boolean;
  readonly zaten_onayliydi?: boolean;
  readonly zaten_silahliydi?: boolean;
  readonly icra_yasasi?: boolean;
  readonly armed_n?: number;
  readonly ts?: string;
  /** Gönderimin sonucu — ya da icra yolunun YOKLUĞU. Sessizlik yasak (loop.py İŞ-3a). */
  readonly icra_yolu?: string;
  readonly gonderim?: {
    readonly ok?: boolean;
    readonly submitted?: number;
    readonly detail?: string;
    readonly dropped_ids?: readonly string[];
  } | null;
  readonly not?: string | null;
  readonly neden?: string;
}

/** `POST /api/approvals/{id}` 200 gövdesi. */
export interface DefterKararSonucu {
  readonly ok?: boolean;
  readonly id?: string;
  readonly decision?: string;
  /** Satır bir uygulama kapısı açıyor mu — SUNUCU söyler, istemci önekten çıkarmaz. */
  readonly davranissal?: boolean;
  readonly not?: string;
  readonly kunye?: unknown;
}

/* --- HATA HÂLLERİ: HER KOD AYRI CÜMLE ------------------------------------- */

export interface HataMetni {
  readonly baslik: string;
  readonly govde: string;
  /** 401 ayrı bir hâl: çaresi yeniden giriş, tazeleme değil. */
  readonly oturumDustu: boolean;
}

/**
 * "Bir şeyler ters gitti" YASAK. Her kodun kendi cümlesi ve kendi ÇARESİ var; ucun
 * `detail` metni AYNEN taşınır (api.py ret gerekçelerini oraya yazıyor — YASA 4).
 */
export function hataMetni(sonuc: GonderSonucu, yol: string): HataMetni {
  const d = sonuc.detay;
  if (sonuc.kod === 0) {
    return {
      baslik: "Ağ hatası — yanıt HİÇ gelmedi",
      govde:
        `${yol} isteği bir HTTP yanıtı üretmedi (${d ?? "tarayıcı bir sebep yazmadı"}). ` +
        `DİKKAT: bu "yazılmadı" DEMEK DEĞİLDİR — istek sunucuya ulaşmış ve yanıtı kaybolmuş ` +
        `olabilir. Kuyruğu tazele ve kalemin durumunu KONTROL ET; körlemesine tekrar gönderme.`,
      oturumDustu: false,
    };
  }
  if (sonuc.kod === 401) {
    return {
      baslik: "Oturum düştü (401)",
      govde:
        `${yol} 401 döndü. Bu bir ölçüm hatası değil — panoya yeniden giriş gerekiyor. ` +
        `Karar YAZILMADI: uç yetkiyi gövdeyi okumadan önce sınıyor (\`_auth\`).`,
      oturumDustu: true,
    };
  }
  if (sonuc.kod === 403) {
    return {
      baslik: "Uç bu kimliğe karar yazmayı REDDETTİ (403)",
      govde:
        (d ?? "uç gerekçe yazmadı") +
        " — `rev:` ve `rec:` uzayları YALNIZ L1+'ta yazılabilir (api.py:6086): o satırlar bir " +
        "uygulama kapısı açtığı için L0'da yazılan karar yarın icraya dönüşebilirdi. Karar YAZILMADI.",
      oturumDustu: false,
    };
  }
  if (sonuc.kod === 404) {
    return {
      baslik: "Uç kalemi BULAMADI (404)",
      govde:
        (d ?? "uç gerekçe yazmadı") +
        " — plan defterde yok ya da yol yanlış. Kuyruk bayat olabilir: tazele ve kalemin hâlâ " +
        "orada olduğunu doğrula. Hiçbir şey yazılmadı.",
      oturumDustu: false,
    };
  }
  if (sonuc.kod === 400 || sonuc.kod === 409) {
    return {
      baslik: `Uç REDDETTİ (${sonuc.kod}) — gerekçesi aynen aşağıda`,
      govde:
        (d ?? "uç gerekçe metni döndürmedi (bu bir kusurdur: api.py ret gerekçelerini `detail`e yazar)") +
        " · Bu bir ağ/pano hatası DEĞİL: sunucu isteği aldı, yasayı uyguladı ve HAYIR dedi. " +
        "Hiçbir şey yazılmadı.",
      oturumDustu: false,
    };
  }
  if (sonuc.kod >= 500) {
    return {
      baslik: `Sunucu hatası (${sonuc.kod})`,
      govde:
        `${yol} ${sonuc.kod} döndü${d ? ` — ${d}` : " ve gövdesinde okunabilir bir `detail` yoktu"}. ` +
        `Bu hâlde kararın YAZILIP YAZILMADIĞI pano tarafından BİLİNEMEZ (istisna yazımdan önce de ` +
        `sonra da fırlayabilir). Kuyruğu tazele ve defteri KONTROL ET.`,
      oturumDustu: false,
    };
  }
  return {
    baslik: `Beklenmeyen durum kodu (${sonuc.kod})`,
    govde:
      `${yol} ${sonuc.kod} döndü${d ? ` — ${d}` : " ve gövdesinde `detail` yoktu"}. Bu panonun ` +
      `tanıdığı kodlardan (200/400/401/403/404/409/5xx) hiçbiri değil; sonucu VARSAYMA, defteri kontrol et.`,
    oturumDustu: false,
  };
}
