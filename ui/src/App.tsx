/* ============================================================================
   PİLOT YÜZEYİ — İş akışı, shadcn "application shell" gramerinde
   ----------------------------------------------------------------------------
   PİLOTUN AMACI sayfayı güzelleştirmek DEĞİL, üç kapıyı ölçmek:
     G1  jeton/kontrast denkliği   → renk YALNIZ rol jetonundan gelir
     G2  dağıtım bütünlüğü         → CSP uyumlu, dış origin yok, artefakt taze
     G3  epistemik değişmezler     → payda zorunlu, ölçülemedi ≠ sıfır

   Bu dosya G1'in bileşen ayağını taşır: burada TEK bir çıplak hex ya da Tailwind
   hazır renk skalası (`text-green-600`) geçmez. Geçerse çivi düşer.
   ============================================================================ */
import { useState } from "react";
import {
  OlcumHucresi,
} from "./meridian/OlcumHucresi";
import {
  azOrnek,
  gurultuBandiAciklamasi,
  kanitOrani,
  yonSinifi,
} from "./meridian/olcum";
import type { Olcum } from "./meridian/olcum";

/* --- KENAR ÇUBUĞU: gruplu gezinme (shadcn shell grameri) --------------------- */
const RAY = [
  {
    grup: "Karar",
    ogeler: [
      { ad: "Bugün", yol: "/#bugun" },
      { ad: "Karar", yol: "/#karar" },
      { ad: "Analiz", yol: "/#analiz" },
    ],
  },
  {
    grup: "İşletme",
    ogeler: [
      { ad: "Portföy", yol: "/#portfoy" },
      { ad: "Sağlık", yol: "/#saglik" },
      { ad: "Operasyon", yol: "/#operasyon" },
    ],
  },
  {
    grup: "Belge",
    ogeler: [
      { ad: "İş akışı", yol: "/pilot-workflow.html", secili: true },
      { ad: "Runbook", yol: "/runbook" },
    ],
  },
] as const;

/* --- ÖRNEK ÖLÇÜMLER --------------------------------------------------------
   Sayılar SABİT ve bu bilerek: pilot bir VERİ yüzeyi değil, bir GRAMER denemesi.
   Canlı uca bağlanmadı çünkü pilotun sorusu "shadcn Meridian'ın kurallarını
   taşıyabiliyor mu", "veri akıyor mu" değil. Bağlanmış olsaydı yanlış bir sayıyı
   canlı sanma riski doğardı — UYDURMA YASAĞI'nın yüzey karşılığı. */
const ORNEKLER: {
  etiket: string;
  olcum: Olcum;
  n: number;
  ortalama: number | null;
  meta: string;
  bicim?: (d: number) => string;
}[] = [
  {
    etiket: "exhaustion_hammer · yükseliş",
    olcum: { deger: 0.21 },
    n: 190,
    ortalama: 0.21,
    meta: "190 işlem · %27 tutan",
    bicim: (d) => `${d > 0 ? "+" : ""}${d.toFixed(2)}R`,
  },
  {
    etiket: "exhaustion_hammer · yatay",
    olcum: { deger: 0.12 },
    n: 38,
    ortalama: 0.12,
    meta: "38 işlem · %34 tutan",
    bicim: (d) => `${d > 0 ? "+" : ""}${d.toFixed(2)}R`,
  },
  {
    etiket: "pullback · yükseliş",
    olcum: { deger: -0.79 },
    n: 5,
    ortalama: -0.79,
    meta: "5 işlem · %0 tutan",
    bicim: (d) => `${d > 0 ? "+" : ""}${d.toFixed(2)}R`,
  },
  {
    etiket: "pullback · düşüş",
    // ÖLÇÜLEMEDİ — ve NEDENİ tipte zorunlu olduğu için ekranda da var.
    olcum: { deger: null, neden: "bu kesitte hiç işlem kapanmadı — ortalama tanımsız" },
    n: 0,
    ortalama: null,
    meta: "ekilmemiş parsel",
  },
];

export function App() {
  const [rayAcik, setRayAcik] = useState(true);

  return (
    <div className="grid min-h-screen" style={{ gridTemplateColumns: rayAcik ? "240px 1fr" : "64px 1fr" }}>
      {/* ---- KENAR ÇUBUĞU ---- */}
      <aside className="border-r border-cizgi bg-kart px-3 py-5">
        <div className="mb-6 flex items-center gap-2 px-2">
          <span className="inline-block h-2 w-2 rounded-cip bg-nav" aria-hidden />
          {rayAcik && (
            <span className="text-[length:var(--t-body)] font-semibold text-murekkep">
              Meridian
            </span>
          )}
        </div>

        {RAY.map((g) => (
          <nav key={g.grup} className="mb-5">
            {rayAcik && (
              /* E1 — MİKRO BÖLÜM BAŞLIĞI: 11px · 600 · .04em · UPPERCASE · --tx3 */
              <div className="mb-2 px-2 text-[length:var(--t-cap)] font-semibold uppercase tracking-[.04em] text-murekkep-3">
                {g.grup}
              </div>
            )}
            <ul className="flex flex-col gap-0.5">
              {g.ogeler.map((o) => (
                <li key={o.ad}>
                  <a
                    href={o.yol}
                    aria-current={"secili" in o && o.secili ? "page" : undefined}
                    className={`flex min-h-[36px] items-center gap-2.5 rounded-dugme px-2 text-[length:var(--t-body)] no-underline transition-colors hover:bg-zemin-2 ${
                      "secili" in o && o.secili
                        ? "bg-zemin-2 font-medium text-murekkep"
                        : "text-murekkep-2"
                    }`}
                    title={rayAcik ? undefined : o.ad}
                  >
                    <span className="inline-block h-1.5 w-1.5 shrink-0 rounded-cip bg-cizgi-2" aria-hidden />
                    {rayAcik && o.ad}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </aside>

      {/* ---- İÇERİK ---- */}
      <div className="flex min-w-0 flex-col">
        {/* ÜST BAR: daraltma düğmesi + KIRINTI (bugün panoda eksik olan tek şey) */}
        <header className="flex items-center gap-3 border-b border-cizgi px-5 py-3">
          <button
            type="button"
            onClick={() => setRayAcik((v) => !v)}
            aria-expanded={rayAcik}
            aria-label={rayAcik ? "Kenar çubuğunu daralt" : "Kenar çubuğunu aç"}
            className="grid h-8 w-8 place-items-center rounded-dugme border border-cizgi bg-kart text-murekkep-2 hover:bg-zemin-2"
          >
            <span aria-hidden>{rayAcik ? "‹" : "›"}</span>
          </button>
          <span className="h-4 w-px bg-cizgi" aria-hidden />
          <nav aria-label="Kırıntı">
            <ol className="flex items-center gap-2 text-[length:var(--t-cap)] text-murekkep-3">
              <li><a href="/" className="no-underline hover:text-murekkep-2">Meridian</a></li>
              <li aria-hidden>/</li>
              <li>Belge</li>
              <li aria-hidden>/</li>
              <li className="text-murekkep">İş akışı</li>
            </ol>
          </nav>
        </header>

        <main className="p-5">
          <h1 className="mb-1 text-[length:var(--t-h)] font-semibold text-murekkep">
            Kurulum × rejim
          </h1>
          <p className="mb-5 max-w-[65ch] text-[length:var(--t-body)] text-murekkep-2">
            shadcn kabuğu üstünde Meridian ölçüm hücresi. Hücrelerin hepsi aynı
            bileşenden doğuyor; renk yalnız rol jetonundan geliyor.
          </p>

          {/* DÖRTLÜ SAYISAL BAND — TEK GRAMER: kapalı kap + paylaşılan kenar + gap:0.
              Maketin yedi blok kabının yedisinde aynı reçete (çivi T4). */}
          <div className="overflow-hidden rounded-kart border border-cizgi bg-kart">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
              {ORNEKLER.map((o, i) => (
                <div
                  key={o.etiket}
                  className={
                    i < ORNEKLER.length - 1
                      ? "border-b border-cizgi lg:border-b-0 lg:border-r"
                      : ""
                  }
                >
                  <OlcumHucresi
                    etiket={o.etiket}
                    olcum={o.olcum}
                    bicim={o.bicim}
                    meta={o.meta}
                    yon={yonSinifi(o.ortalama, o.n)}
                    kanit={
                      o.n > 0
                        ? { oran: kanitOrani(o.n), payda: `işlem sayısı · log ölçek, n=55 dolu` }
                        : undefined
                    }
                    rozet={o.n > 0 && azOrnek(o.n) ? "az_ornek" : undefined}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* GÜRÜLTÜ BANDI LEJANTI — operatörün sahne C'de gördüğü "aynı anlam iki
              renkte" okumasının gerçek cevabı. Kural doğruydu ama EKRANDA
              AÇIKLANMIYORDU; kuralı değil görünürlüğünü düzeltiyoruz. */}
          <section
            className="mt-4 rounded-serit bg-zemin-2 p-4"
            aria-label="Renk kuralı"
          >
            <div className="mb-2 text-[length:var(--t-cap)] font-semibold uppercase tracking-[.04em] text-murekkep-3">
              Renk neden bazı hücrelerde yok
            </div>
            <p className="max-w-[65ch] text-[length:var(--t-body)] leading-[1.6] text-murekkep-2">
              Ortalama, örneklem gürültüsünün <span className="font-mono">(1/√n)</span> içinde
              kalıyorsa hücre ne yeşil ne kırmızı olur — o sayı sıfırdan ayırt edilemez ve
              renk taşırsa bir hüküm gibi okunur. İşaret sayının kendisinde durur.
            </p>
            <ul className="mt-3 flex flex-col gap-1">
              {ORNEKLER.filter((o) => o.ortalama != null).map((o) => {
                const aciklama = gurultuBandiAciklamasi(o.ortalama, o.n);
                return (
                  <li
                    key={o.etiket}
                    className="flex flex-wrap items-baseline gap-2 text-[length:var(--t-cap)] text-murekkep-2"
                  >
                    <span className="font-mono tabular-nums text-murekkep">{o.etiket}</span>
                    <span>{aciklama ?? "bandın dışında — renk bir okuma taşıyor"}</span>
                  </li>
                );
              })}
            </ul>
          </section>
        </main>
      </div>
    </div>
  );
}
