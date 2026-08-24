/* ============================================================================
   ANALİZ YÜZEYİNİN GÖVDE TİPLERİ — /api/performance · /api/plots · /api/topviews
   ----------------------------------------------------------------------------
   HEPSİ OKUNARAK YAZILDI, TAHMİN EDİLMEDİ. Kaynak satırlar:
     · `meridian/api.py::api_performance` (2626) — equity_curve, equity_curve_beyani,
       score_detail, kelly, tail_risk, n_trades, recent_trades
     · `meridian/api.py::_egri_beyani`   (2485) — eğrinin pencere beyanı
     · `meridian/score.py::score_detail` (101)  — İKİ AYRI ŞEKİL döndürür (aşağıda)
     · `meridian/api.py::api_plots`      (2266) — kurulum × rejim matrisi
     · `meridian/topviews.py::topviews`  (289)  — dokuz facet

   NEDEN NEREDEYSE HER ALAN İSTEĞE BAĞLI: bu deponun birinci yasası ölçülemeyeni
   YAZMAMAK. Uçlar bir sayıyı ölçemediğinde ya alanı hiç basmıyor ya da `null`
   basıp NEDENİNİ ayrı bir alanda taşıyor. `alan?: number` ile `alan: number|null`
   arasındaki fark bu yüzden anlamlı: birincisi "hiç ölçülmedi", ikincisi
   "ölçüldü, sonuç yok". İkisini `number` yapıp 0 varsaymak ekrana yalan yazardı.

   `score_detail` İKİ ŞEKİLLİDİR ve bu tipte görünür olmak zorunda: örneklem
   `min_sample`in ALTINDAYKEN uç YALNIZ `{score:null, n, min_sample, reason}`
   döner — `win_rate`, `avg_r`, `max_drawdown`, `sharpe` ALANLARI HİÇ YOKTUR
   (null değil, yok). Bu yüzden hepsi opsiyonel ve KPI şeridi yokluklarını
   `reason` ile birlikte çiziyor.
   ============================================================================ */

/* ---- /api/performance ---------------------------------------------------- */

export interface SkorKirilimi {
  /** `null` = örneklem yetmedi (kapı tanımsız). Sayı = 0..1 bileşik skor. */
  readonly score?: number | null;
  readonly n?: number;
  readonly min_sample?: number;
  /** YALNIZ `n < min_sample` iken var: "12/30 closed trades — score undefined". */
  readonly reason?: string;
  readonly total_return?: number;
  readonly realized_30d?: number;
  readonly max_drawdown?: number;
  readonly sharpe?: number;
  /** `sharpe: 0.0` "ölçüldü sıfır" mı "ölçülemedi" mi — ayracı BU bayrak (score.py:135). */
  readonly sharpe_measurable?: boolean;
  readonly avg_r?: number;
  readonly win_rate?: number;
  readonly components?: {
    readonly ret?: number;
    readonly dd?: number;
    readonly sharpe?: number;
  };
  readonly targets?: {
    readonly target_return_30d?: number;
    readonly max_drawdown?: number;
    readonly min_sharpe?: number;
  };
}

/** Eğrideki bir boşluk: `i` = boşluğun SOLUNDAKİ ham nokta dizini (api.py:2537). */
export interface EgriBoslugu {
  readonly onceki?: string;
  readonly sonraki?: string;
  readonly gun?: number;
  readonly i?: number;
}

export interface ResetIsareti {
  readonly i?: number | null;
  readonly konum_neden?: string | null;
  readonly egri_son_nokta?: unknown;
  readonly tarih?: string;
}

export interface TohumSiniri {
  readonly replay_end?: string | null;
  readonly kaynak?: string | null;
  readonly guven?: string | null;
  readonly i?: number | null;
  readonly konum_neden?: string | null;
}

export interface EgriBeyani {
  readonly n_nokta?: number;
  readonly okunamayan_nokta?: number;
  /** `[tarih, sermaye]` — çift değilse eğri hiç çizilemez. */
  readonly ilk?: readonly [string, number] | null;
  readonly son?: readonly [string, number] | null;
  readonly son_seans?: string | null;
  /** Kitabın son seansı ile eğrinin son noktası arasındaki gün. `null` = kıyas yapılamadı. */
  readonly gecikme_gun?: number | null;
  readonly bosluk_esigi_gun?: number;
  readonly n_bosluk?: number;
  readonly bosluklar?: readonly EgriBoslugu[];
  readonly en_buyuk_bosluk?: EgriBoslugu | null;
  readonly bosluk_kirpildi?: boolean;
  readonly bosluk_tavani?: number;
  readonly reset_isaretleri?: readonly ResetIsareti[];
  readonly n_isaret?: number;
  readonly tohum_siniri?: TohumSiniri | null;
  readonly son_yazim?: Record<string, unknown> | null;
  readonly son_dongu_tarih?: string | null;
  readonly beyan?: string;
}

export interface EgriGovdesi {
  /** HAM `state/equity_curve.json`. Nokta `[tarih, sermaye]` OLMAYABİLİR — çözerken sayılır. */
  readonly points?: readonly unknown[];
}

export interface Kelly {
  readonly win_rate?: number;
  readonly win_loss_ratio?: number;
  readonly full_kelly?: number;
  readonly half_kelly?: number;
  readonly n?: number;
}

export interface KuyrukRiski {
  readonly horizon?: number;
  readonly alpha?: number;
  readonly n?: number;
  readonly var_r?: number;
  readonly cvar_r?: number;
  readonly worst_r?: number;
  readonly mean_r?: number;
}

export interface Islem {
  readonly id?: string;
  readonly ticker?: string;
  readonly setup?: string;
  readonly regime?: string;
  readonly ts_open?: string;
  readonly ts_close?: string;
  readonly r_multiple?: number;
  readonly pnl_pct?: number;
  readonly pnl_dollars?: number;
  readonly bars_held?: number;
  readonly exit_reason?: string;
}

export interface PerformansGovdesi {
  readonly equity_curve?: EgriGovdesi;
  readonly equity_curve_beyani?: EgriBeyani;
  readonly score_detail?: SkorKirilimi;
  /** `null` = n<12 ya da tek yönlü defter — Kelly tanımsız (score.py:kelly_fraction). */
  readonly kelly?: Kelly | null;
  /** `null` = TAIL_MIN_SAMPLE=12 altı; dürüst "bilinmiyor". */
  readonly tail_risk?: KuyrukRiski | null;
  readonly n_trades?: number;
  readonly recent_trades?: readonly Islem[];
  readonly holdout_note?: string;
}

/* ---- /api/plots ---------------------------------------------------------- */

export interface PlotHucre {
  readonly n?: number;
  readonly mean_r?: number;
  readonly hit?: number;
  readonly exits?: readonly (readonly [string, number])[];
}

export interface PlotSatiri {
  readonly setup?: string;
  /** `cells[i]` ↔ `regimes[i]` HİZALI. `null` = ekilmemiş parsel (o hücrede işlem YOK). */
  readonly cells?: readonly (PlotHucre | null)[];
}

export interface PlotlarGovdesi {
  readonly setups?: readonly string[];
  readonly regimes?: readonly string[];
  readonly grid?: readonly PlotSatiri[];
  /** setup VE regime etiketi olan işlemler. */
  readonly n_trades?: number;
  /** Defterin tamamı — farkı etiketsiz işlem sayısıdır ve ekranda yazılır. */
  readonly n_trades_total?: number;
}

/* ---- /api/topviews ------------------------------------------------------- */

export interface FacetSatiri {
  readonly deger?: string;
  readonly n?: number;
  /** Kaç satır GERÇEKTEN r_multiple taşıyor — `n` ile aynı olmak ZORUNDA DEĞİL. */
  readonly r_n?: number;
  readonly sum_r?: number | null;
  readonly gross_win?: number | null;
  readonly gross_loss?: number | null;
  readonly wins?: number;
  readonly pf?: number | null;
  readonly kazanma?: number | null;
  /** `pf === null` iken NEDEN — sonsuz DEĞİL, tanımsız (topviews.py:92-96). */
  readonly pf_yok_nedeni?: string | null;
}

export interface FacetBloku {
  /** `null` = facet ÖLÇÜLEMEDİ. Boş dizi DEĞİL — boş dizi "hiç yok" der, bu başka cümle. */
  readonly satirlar?: readonly FacetSatiri[] | null;
  readonly olculemedi_neden?: string | null;
  readonly etiketsiz_n?: number;
  readonly etiketsiz_neden?: string;
  /** true = bir satır birden çok kovaya girebilir; `n` toplamı paydayı AŞAR. */
  readonly cok_etiketli?: boolean;
  readonly ek?: Readonly<Record<string, number>>;
}

export interface FacetKaynagi {
  readonly kaynak?: string;
  /** `_pencere()` DİZGE döndürür ("2026-01-02 → 2026-08-20 (ts_close)"), sözlük değil. */
  readonly pencere?: string;
  readonly n?: number;
  readonly payda?: string;
}

export interface TopviewsGovdesi {
  readonly as_of?: string;
  readonly kaynak_defter?: string;
  readonly toplam_islem?: number;
  readonly toplam_plan?: number;
  readonly kapsam?: string;
  readonly aileler?: Readonly<Record<string, Readonly<Record<string, FacetBloku>>>>;
  readonly facet_kaynaklari?: Readonly<Record<string, FacetKaynagi>>;
}
