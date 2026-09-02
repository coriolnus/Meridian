/* ============================================================================
   PLAN OKUMA — `/api/today.todays_plans` ve `/api/signals.plans` satırları
   ----------------------------------------------------------------------------
   Plan satırı `state/trade_plans.jsonl`in HAM satırıdır: alan kümesi zamanla
   büyümüş, ESKİ satırlarda yeni alanlar YOK. Bayatlık damgaları (`expired`,
   `traded`, `last_close`, `drift_pct`) YALNIZ en taze sinyal gününün planlarına
   basılıyor (`api.py::_enrich_stale_plans`, `api_signals` 1743. satır) — yani
   geçmiş planlarda bu alanların yokluğu bir ARIZA DEĞİL, sözleşmenin kendisi.
   Bu yüzden hepsi isteğe bağlı ve yokluk ekranda "yok" diye geçer, "false" diye
   değil.

   `gate_checks` satırının şekli `loop.py::daily_cycle`dan ÖLÇÜLDÜ:
   `{check, passed, severity, value, threshold, coverage?, note?}`. `note` bilerek
   `null` olabiliyor (kontrol geçtiyse söylenecek bir şey yok).
   ============================================================================ */
import { dizi, mantik, metin, metinDizisi, nesne, sayi } from "./oku";

export interface KapiKontrolu {
  readonly ad: string | null;
  readonly gecti: boolean | null;
  readonly siddet: string | null;
  readonly not: string | null;
  readonly kapsam: string | null;
}

export interface Plan {
  readonly id: string | null;
  readonly tarih: string | null;
  readonly sembol: string | null;
  readonly kurulum: string | null;
  readonly skor: number | null;
  readonly hukum: string | null;
  readonly gerekceler: readonly string[] | null;
  readonly kontroller: readonly KapiKontrolu[] | null;
  /** `gate_checks` alanı satırda HİÇ YOK MU? `kontroller === null` bunu da,
   *  "alan var ama dizi değil"i de kapsıyor; ayrımı burada tutuyoruz. */
  readonly kontrolAlaniYok: boolean;
  readonly kesif: boolean | null;
  readonly llmVeto: boolean | null;
  readonly sektor: string | null;
  readonly girisTetigi: number | null;
  readonly boyutR: number | null;
  /* --- uç katmanı ekleri: YALNIZ en taze sinyal gününde basılır --- */
  readonly bayat: boolean | null;
  readonly yasGun: number | null;
  readonly islendi: boolean | null;
  readonly sonKapanis: number | null;
  readonly sapmaYuzde: number | null;
  readonly onayBekliyor: boolean | null;
  readonly onaylandi: boolean;
}

function kontrolOku(x: unknown): KapiKontrolu | null {
  const n = nesne(x);
  if (!n) return null;
  return {
    ad: metin(n["check"]),
    gecti: mantik(n["passed"]),
    siddet: metin(n["severity"]),
    not: metin(n["note"]),
    kapsam: metin(n["coverage"]),
  };
}

/** Ham satırı okur. Nesne DEĞİLSE `null` döner — çağıran bu satırı SAYAR ve
 *  "okunamayan satır" olarak ekrana yazar; sessizce atlamak defteri eksik gösterirdi. */
export function planOku(x: unknown): Plan | null {
  const n = nesne(x);
  if (!n) return null;
  const hamKontrol = dizi(n["gate_checks"]);
  const kontroller = hamKontrol
    ? hamKontrol.map(kontrolOku).filter((k): k is KapiKontrolu => k !== null)
    : null;
  return {
    id: metin(n["id"]),
    tarih: metin(n["date"]),
    sembol: metin(n["ticker"]),
    kurulum: metin(n["setup"]),
    skor: sayi(n["score"]),
    hukum: metin(n["gate_verdict"]),
    gerekceler: metinDizisi(n["gate_reasons"]),
    kontroller,
    kontrolAlaniYok: !("gate_checks" in n),
    kesif: mantik(n["exploration"]),
    llmVeto: mantik(n["llm_veto"]),
    sektor: metin(n["sector"]),
    girisTetigi: sayi(n["entry_trigger"]),
    boyutR: sayi(n["size_r"]),
    bayat: mantik(n["expired"]),
    yasGun: sayi(n["age_days"]),
    islendi: mantik(n["traded"]),
    sonKapanis: sayi(n["last_close"]),
    sapmaYuzde: sayi(n["drift_pct"]),
    onayBekliyor: mantik(n["onay_bekliyor"]),
    onaylandi: nesne(n["operator_onayi"]) !== null,
  };
}

export interface PlanDefteri {
  readonly planlar: readonly Plan[];
  /** Nesne olmadığı için okunamayan satır sayısı. > 0 ise ekranda YAZILIR. */
  readonly okunamayan: number;
}

export function planlariOku(ham: unknown): PlanDefteri | null {
  const d = dizi(ham);
  if (!d) return null;
  const planlar: Plan[] = [];
  let okunamayan = 0;
  for (const s of d) {
    const p = planOku(s);
    if (p) planlar.push(p);
    else okunamayan += 1;
  }
  return { planlar, okunamayan };
}

/* ---------------------------------------------------------------------------
   HÜKÜM EKSENİ — kolonlar. Sıra kapının YÖNÜdür: reddedilen solda, geçen sağda.
   `?` kolonu UYDURMA DEĞİL, ölçümün kendisi: `analytics.today()` bir planın
   `gate_verdict` alanı yoksa onu `"?"` diye sayıyor (analytics.py::today) ve o plan
   gerçekten var — kolonu gizlemek onu yok saymak olurdu.
   --------------------------------------------------------------------------- */
export const HUKUM_SIRASI = ["NO_GO", "REVIEW", "GO"] as const;
export type Hukum = (typeof HUKUM_SIRASI)[number] | "?";

export function hukumu(p: Plan): Hukum {
  const h = p.hukum;
  if (h === "NO_GO" || h === "REVIEW" || h === "GO") return h;
  return "?";
}

export const HUKUM_BASLIGI: Record<Hukum, string> = {
  NO_GO: "NO_GO — kapıda düştü",
  REVIEW: "REVIEW — ikinci göz",
  GO: "GO — kapıdan geçti",
  "?": "? — hüküm yazılmamış",
};

/* ---------------------------------------------------------------------------
   DÜŞTÜĞÜ KAPI. Dört ayrı cevap var ve dördü de FARKLI şey söylüyor; tek bir
   "—" hepsini aynı görünüme sıkıştırırdı:
     · alan yok            → plan `gate_checks` TAŞIMIYOR (eski satır / replay tohumu;
                             `backtest.py::replay` bunun ölçülmüş vakası)
     · dizi boş            → alan var, hiç kontrol yazılmamış
     · düşen kontrol var   → adı + notu (ölçülen cevap)
     · hepsi geçti         → hüküm başka yerden geldi; gerekçe `gate_reasons`ta
   --------------------------------------------------------------------------- */
export type KapiCevabi =
  | { readonly tur: "olculdu"; readonly ad: string; readonly not: string | null; readonly siddet: string | null }
  | { readonly tur: "olculemedi"; readonly neden: string }
  | { readonly tur: "hepsi_gecti"; readonly n: number };

export function dustuguKapi(p: Plan): KapiCevabi {
  if (p.kontrolAlaniYok) {
    return {
      tur: "olculemedi",
      neden: "plan satırında `gate_checks` alanı YOK — hangi kapıda düştüğü hiç yazılmamış",
    };
  }
  if (p.kontroller === null) {
    return { tur: "olculemedi", neden: "`gate_checks` alanı var ama dizi değil — okunamadı" };
  }
  if (p.kontroller.length === 0) {
    return { tur: "olculemedi", neden: "`gate_checks` boş — bu planda hiç kapı satırı yazılmamış" };
  }
  const dusen = p.kontroller.find((k) => k.gecti === false);
  if (dusen) {
    return { tur: "olculdu", ad: dusen.ad ?? "(kontrol adı yazılmamış)", not: dusen.not, siddet: dusen.siddet };
  }
  const olculemeyen = p.kontroller.filter((k) => k.gecti === null).length;
  if (olculemeyen === p.kontroller.length) {
    return { tur: "olculemedi", neden: `${olculemeyen} kapı satırının hiçbirinde \`passed\` alanı yok` };
  }
  return { tur: "hepsi_gecti", n: p.kontroller.filter((k) => k.gecti === true).length };
}
