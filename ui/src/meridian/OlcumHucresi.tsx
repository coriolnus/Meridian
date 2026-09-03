/* ============================================================================
   ÖLÇÜM HÜCRESİ — panonun tek sayı dilinin shadcn karşılığı
   ----------------------------------------------------------------------------
   `app.js::hucreGovde` (etiket + değer + kanıt çubuğu + meta + rozet) ile AYNI
   anatomi. Fark: orada sözleşme yorumda ve çivide yaşıyordu, burada TİPTE.

   Renk YALNIZ rol jetonundan gelir (index.html:296-299 sözleşmesi). Tailwind'in
   hazır paleti (ör. yeşil/emerald ailesinin literal tonları) bir rol DEĞİLDİR ve bu
   dosyada geçmez — çivi: tests/test_ui_pilot_kapilari_v286.py::test_G1b_ciplak_hex_ve_deger_jetonu_BILESENDE_yok.
   ============================================================================ */
import type { Kanit, Olcum, RozetAnahtari } from "./olcum";
import { ROZET } from "./olcum";
import type { YonSinifi } from "./olcum";

export interface OlcumHucresiProps {
  /** Sayıyı adlandıran alan etiketi (E3 reçetesi: 11px · 500 · aralık yok · UPPERCASE yok). */
  etiket: string;
  /** Ya bir sayı, ya `null` + NEDEN. Ara hâl tipte YOK. */
  olcum: Olcum;
  /** Değerin okunabilir yüzü (para/yüzde/R biçimlemesi çağıranın işi). */
  bicim?: (deger: number) => string;
  /** Kanıt çubuğu. `oran: null` → çubuk doğmaz. `payda` ZORUNLU. */
  kanit?: Kanit;
  /** Bağlam satırı — çubuğun ne ölçtüğünü CÜMLEYLE söyler. */
  meta?: string;
  /** Rozet SÖZLÜKTEN. Serbest dizge kabul edilmez. */
  rozet?: RozetAnahtari;
  /** Yön yalnız İŞARETLİ SAYIYA verilir; şiddet AYRI kanaldır (2px alt çizgi). */
  yon?: YonSinifi;
}

const YON_MUREKKEBI: Record<YonSinifi, string> = {
  arti: "text-[var(--yon-arti)]",
  eksi: "text-[var(--yon-eksi)]",
  notr: "text-[var(--tx)]",
};

/** Kanıt çubuğu — TEK reçete: 3px · hap yarıçap · sabit ölçek rengi · tek değişken GENİŞLİK.
 *  ÇUBUK YÖN TAŞIMAZ (`currentColor` okumaz): ölçtüğü büyüklük ÖRNEKLEM, işaret değil.
 *  Bugün panoda `.pm-conf i{background:currentColor}` matriste yön rengini alıyor,
 *  24 özet hücresinde hiç alamıyor — aynı çubuk bir yerde üç renkte, bir yerde hep siyah. */
function KanitCubugu({ kanit }: { kanit: Kanit }) {
  if (kanit.oran == null) return null; // "ölçemedik" — çubuk DOĞMAZ
  const yuzde = Math.max(0, Math.min(1, kanit.oran)) * 100;
  return (
    <span
      className="mt-2 block h-[3px] w-[min(100%,64px)] overflow-hidden rounded-[var(--r-tag)] bg-[var(--line-2)]"
      role="img"
      aria-label={`kanıt gücü %${Math.round(yuzde)} — payda: ${kanit.payda}`}
      title={`payda: ${kanit.payda}`}
    >
      <span
        className="block h-full rounded-[var(--r-tag)] bg-[var(--olcek-guven)]"
        style={{ width: `${yuzde}%` }}
      />
    </span>
  );
}

export function OlcumHucresi({
  etiket,
  olcum,
  bicim = (d) => String(d),
  kanit,
  meta,
  rozet,
  yon = "notr",
}: OlcumHucresiProps) {
  return (
    // ÜSTTEN AKAR — dikey ortalama YOK. Kardeş hücrede bir katman doğmadığında
    // komşusunun başlığı kıpırdamasın (bugün ölçülen kusur; çivi T1).
    <div className="flex min-w-0 flex-col overflow-hidden p-4">
      <span className="text-[length:var(--t-cap)] font-medium text-[var(--tx3)]">
        {etiket}
      </span>

      {olcum.deger == null ? (
        // ÖLÇÜLEMEDİ ≠ SIFIR. Neden tipte zorunlu olduğu için ekranda da hep var.
        <span
          className="mt-2 text-[length:var(--t-body)] text-[var(--tx3)]"
          title={olcum.neden}
        >
          veri yok
          <span className="sr-only"> — {olcum.neden}</span>
        </span>
      ) : (
        <span
          className={`mt-2 font-mono text-[length:var(--t-lg)] font-semibold tabular-nums ${YON_MUREKKEBI[yon]}`}
        >
          {bicim(olcum.deger)}
        </span>
      )}

      {kanit && <KanitCubugu kanit={kanit} />}

      {meta && (
        <span className="mt-2 text-[length:var(--t-cap)] leading-[1.55] text-[var(--tx2)]">
          {meta}
        </span>
      )}

      {rozet && (
        // TEK ÇİP REÇETESİ: hap yarıçap · 500 · açık sans · görünür kenar YOK.
        // Harf düzeni SÖZLÜKTEN gelir, `text-transform`dan değil.
        <span className="mt-2 self-start rounded-[var(--r-tag)] border border-transparent bg-[var(--olcek-guven-t)] px-2.5 py-[3px] font-sans text-[length:var(--t-cap)] font-medium text-[var(--olcek-guven)]">
          {ROZET[rozet]}
        </span>
      )}
    </div>
  );
}
