/* ============================================================================
   ÖĞRENME + ANTRENMAN — UÇ TİPLERİ
   ----------------------------------------------------------------------------
   HER ALAN OPSİYONEL ve bu tembellik değil ÖLÇÜM: bu iki yüzeyin okuduğu uçlar
   dosyadan okunan HAM sözlükleri taşıyor (`hermes_status.json`, `scoreboard.json`,
   `component_ic.json`, `skills_registry.json` …). Dosya yoksa uç `None`/`{}` döner
   ve bir alanın VARLIĞI hiçbir yerde garanti değildir. `x: number` yazmak, tipi
   ölçmediğim bir şeye söz verdirmek olurdu; `noUncheckedIndexedAccess` açıkken
   bile `undefined` sessizce `0` gibi biçimlenebilirdi.

   TİPLER SÖZLEŞMEYİ DEĞİL, ÖLÇÜLENİ TARİF EDER. Şekiller `meridian/api.py`,
   `analytics.learning_scorecard`, `hermes_runtime.status`, `sprint.status`,
   `shadow_model.training_status`, `skills.catalog` OKUNARAK yazıldı; canlı
   `state/*.json` dosyalarından da doğrulandı (2026-08-25).
   ============================================================================ */

/* ---- /api/hermes --------------------------------------------------------- */

export interface BeyinDurumu {
  readonly credentials?: boolean;
  readonly cooling_s?: number;
  readonly ready?: boolean;
  readonly reason?: string | null;
  readonly model_id?: string | null;
}

export interface BeyinZinciri {
  readonly order?: readonly string[];
  readonly ready?: readonly string[];
  readonly models?: Readonly<Record<string, string | null>>;
  readonly same_model_ids?: readonly (readonly string[])[];
  readonly nous_mode?: string | null;
  readonly agent_config_provider?: string | null;
  /** ÜÇ DEĞERLİ: sayı | null (=ölçülmedi, `..._reason` dolu). 0 DEĞİL. */
  readonly independent_upstreams?: number | null;
  readonly independent_upstreams_reason?: string | null;
  /** Ölçümün KENDİSİ düştüyse yalnız bu alan gelir (hermes_runtime._brain_chain). */
  readonly error?: string;
}

export interface Ufuk {
  readonly regime?: string | null;
  readonly trades?: number;
  readonly trades_needed?: number;
  readonly span_days?: number;
  readonly min_days?: number;
  readonly ready?: boolean;
}

export interface AramaKaydi {
  readonly running?: boolean;
  readonly phase?: string | null;
  readonly status?: string | null;
  readonly i?: number;
  readonly total?: number;
  readonly variable?: string | null;
  readonly old?: unknown;
  readonly new?: unknown;
  readonly updated_at?: string | null;
}

export interface HermesDurumu {
  /** ÜÇ DEĞERLİ: true/false/null. `null` = canlılık ÖLÇÜLEMEDİ (`active_neden` dolu). */
  readonly active?: boolean | null;
  readonly active_neden?: string | null;
  readonly surec_ici?: boolean;
  readonly search_durumu?: string;
  readonly brain?: string | null;
  readonly model?: string | null;
  readonly brain_availability?: Readonly<Record<string, BeyinDurumu>>;
  readonly brain_chain?: BeyinZinciri;
  readonly brain_degraded?: boolean;
  readonly reflection_every?: number;
  readonly closed_trades?: number;
  readonly trades_since_last_reflection?: number;
  readonly trades_until_next?: number;
  readonly horizon?: Ufuk;
  readonly horizon_ready?: boolean;
  readonly horizon_regime?: string | null;
  readonly search?: AramaKaydi;
  readonly reflecting?: boolean;
  readonly reflections?: number;
  readonly last_reflection?: string | null;
  readonly last_poll?: string | null;
  readonly last_result?: string | null;
  readonly last_variable?: string | null;
  readonly last_reflect_at?: number | null;
  readonly poll_seconds?: number;
  readonly started_at?: string | null;
  readonly updated?: string | null;
}

export interface Harcama {
  readonly month?: string;
  readonly spent_usd?: number;
  readonly budget_usd?: number;
  readonly remaining_usd?: number;
  readonly over_budget?: boolean;
  readonly calls_this_month?: number;
  /** Hiçbir satır taşımıyorsa `null` — 0 DEĞİL. */
  readonly thought_tokens?: number | null;
}

/** `_topla()` çıktısı — beş alanın hepsi TOPLAMDIR, ortalama değil. */
export interface HarcamaToplami {
  readonly n?: number;
  readonly in_tokens?: number;
  readonly out_tokens?: number;
  readonly cost_usd?: number;
  readonly thought_tokens?: number;
}

export type HarcamaGunu = HarcamaToplami & { readonly gun?: string };
export type HarcamaKolu = HarcamaToplami & { readonly ad?: string };

export type HarcamaDetayi =
  | { readonly var: false; readonly neden?: string }
  | {
      readonly var: true;
      readonly toplam?: HarcamaToplami;
      readonly bu_ay?: HarcamaToplami;
      readonly ay?: string;
      readonly modeller?: Readonly<Record<string, unknown>>;
      readonly kollar?: readonly HarcamaKolu[];
      readonly gunler?: readonly HarcamaGunu[];
      readonly son?: readonly unknown[];
      readonly olculemeyen_satir?: number;
      readonly satir_n?: number;
    };

export interface DefterSayaci {
  readonly live_paper_n?: number;
  readonly replay_seed_n?: number;
  readonly belirsiz_n?: number;
  readonly damgasiz_n?: number;
  readonly toplam?: number;
  readonly training_n?: number;
  readonly gercek_canli_n?: number;
  readonly orneklem_n?: number;
  readonly orneklem_kapsam?: string;
  readonly sinir?: unknown;
}

export interface Kalibrasyon {
  readonly n?: number;
  readonly brier?: number | null;
  readonly hit_rate?: number | null;
  readonly reliability?: readonly { readonly bin?: string; readonly n?: number; readonly observed?: number }[];
  readonly note?: string;
}

export interface AntrenmanTerfisi {
  readonly promoted?: boolean | null;
  readonly n_live?: number | null;
  readonly live_brier?: number | null;
  readonly baseline_brier?: number | null;
  readonly promote_min_n?: number;
  readonly kural?: string | null;
}

export interface AntrenmanDurumu {
  readonly kuruldu?: boolean;
  readonly n_fit?: number | null;
  readonly n_real?: number | null;
  readonly n_cf?: number | null;
  readonly brier_train?: number | null;
  readonly son_fit_ts?: string | null;
  readonly son_fit_kaynak?: "damga" | "kunye" | null;
  readonly son_deneme_ts?: string | null;
  readonly son_atlama_nedeni?: string | null;
  /** ÜÇ DEĞERLİ: null = parmak izi hiç yazılmamış (geriye-uyumluluk hâli). */
  readonly veri_seti_taze?: boolean | null;
  readonly min_fit_n?: number;
  readonly terfi?: AntrenmanTerfisi;
}

export interface DolguKuyrugu {
  readonly gorussuz_toplam?: number;
  readonly n_plan?: number;
  readonly dolgulanabilir_gun?: number;
  readonly dolgulanabilir_satir?: number;
  readonly en_eski?: string | null;
  readonly en_yeni?: string | null;
  readonly gece_tavani?: number;
  readonly tavan_kaynagi?: string;
  readonly tavan_formulu?: string;
  readonly tahmini_gece?: number | null;
  readonly beyan?: string;
}

export interface SprintKadansi {
  readonly kos?: boolean;
  readonly sebep?: string;
  readonly gecen_gun?: number | null;
  readonly taze_hipotez?: number | null;
  readonly cfg?: Readonly<Record<string, unknown>>;
  readonly tetik?: {
    readonly haftalik_gun?: number;
    readonly taze_hipotez_esigi?: number;
    readonly gece_dilimi?: readonly number[];
  };
}

export interface Besleme {
  readonly antrenman?: AntrenmanDurumu | null;
  readonly dolgu_kuyrugu?: DolguKuyrugu | null;
  readonly antrenman_sprinti?: SprintKadansi | null;
}

export interface OgrenmeKarnesi {
  readonly status_counts?: Readonly<Record<string, number>>;
  readonly shipped?: number;
  readonly promoted?: number;
  readonly rolled_back?: number;
  readonly rejected_by_backtest?: number;
  readonly rejected_by_guard?: number;
  readonly outcomes_measured?: number;
  readonly trades_total?: number;
  readonly loop_state?: string;
  readonly defter?: DefterSayaci;
  readonly calibration?: Kalibrasyon;
  readonly overfit_suspects?: number;
  readonly versions?: number;
  readonly current_version?: number | string | null;
  readonly min_sample?: number;
  readonly besleme?: Besleme;
  /** TSK-074 r1 (2026-09-04): Ö-48 hayalet süzgeci öneri katmanına kablolandıktan sonraki canlı
   *  kanıt sayacı — KÜMÜLATİF (kablolama gününden BUGÜNE, kayan pencere DEĞİL),
   *  `analytics._hayalet_suzulen_n` (events.jsonl, GERÇEKTEN süzülen farklı düğme adlarının
   *  kümesi; okuma kuyruk-sınırlı, bilinen sınır `analytics.HAYALET_SAYAC_N_SATIR`de). Operatör
   *  kapısı: 2 hafta sonra bu sayı okunur, sıfırsa kablolama geri alınır. */
  readonly hayalet_suzulen_n?: number;
  readonly verdict?: string;
}

export interface SprintIzi {
  readonly variable?: string;
  readonly old?: unknown;
  readonly new?: unknown;
  readonly candidate_oos?: number | null;
  readonly incumbent_oos?: number | null;
  readonly fold_wins?: string | null;
  readonly tail_ok?: boolean | null;
  readonly passes?: boolean;
  readonly why?: string | null;
}

export interface SprintAramasi {
  readonly status?: string | null;
  readonly evaluated?: number | null;
  readonly cleared?: number | null;
  readonly incumbent_oos?: number | null;
  readonly best?: {
    readonly variable?: string;
    readonly old?: unknown;
    readonly new?: unknown;
    readonly candidate_oos?: number | null;
    readonly incumbent_oos?: number | null;
  } | null;
  readonly trace?: readonly SprintIzi[];
}

export interface SprintKosusu {
  readonly ts?: string;
  readonly sid?: string;
  readonly sandbox?: string;
  readonly status?: string;
  readonly evaluated?: number | null;
  readonly cleared?: number | null;
  readonly incumbent_oos?: number | null;
  readonly best?: SprintAramasi["best"];
  readonly trace?: readonly SprintIzi[];
}

export interface SprintDurumu {
  readonly pid?: number | null;
  readonly sid?: string | null;
  readonly sbroot?: string | null;
  readonly started_at?: string | null;
  readonly updated?: string | null;
  readonly eval_start?: string | null;
  readonly cutoff?: string | null;
  /** starting|baseline|search|candidate|done|stopped|error — YOKSA hiç koşmamış. */
  readonly phase?: string | null;
  readonly progress?: number | null;
  readonly total?: number | null;
  readonly n_v1?: number | null;
  readonly n_v2?: number | null;
  readonly v2?: number | string | null;
  readonly shipped?: boolean | null;
  readonly loop_closed?: boolean | null;
  readonly realized?: number | null;
  readonly note?: string | null;
  readonly error?: string | null;
  readonly search?: SprintAramasi | null;
  readonly active?: boolean;
  readonly orphan?: boolean;
  readonly orphan_note?: string | null;
  readonly runs?: readonly SprintKosusu[];
  readonly runs_ledger?: "var" | "YOK";
  readonly runs_kaynak?: string | null;
  readonly runs_note?: string | null;
  readonly n_hyp_at_start?: number | null;
  readonly cfg?: Readonly<Record<string, unknown>>;
}

export interface HermesGovdesi {
  readonly status?: HermesDurumu;
  readonly spend?: Harcama;
  readonly spend_detay?: HarcamaDetayi;
  readonly autostart?: boolean;
  readonly recent?: readonly unknown[];
  readonly skill_count?: number;
  readonly learning?: OgrenmeKarnesi;
  readonly scheduler?: Readonly<Record<string, unknown>>;
  readonly sprint?: SprintDurumu;
  readonly note?: string;
}

/* ---- /api/diagnostics (yalnız okuduğumuz dallar) ------------------------- */

export interface GolgeYasasi {
  readonly law_transition?: boolean;
  readonly yasa_surumu?: string | null;
  readonly gecis_tarihi?: string | null;
  readonly aktif_yasa?: string;
  readonly golge_yasa?: string;
  readonly golge_kayit_sayisi?: number;
  readonly iraksayan_kayit?: number;
  readonly gecis_oncesi_kayit?: number;
  readonly son_kayit?: {
    readonly id?: string;
    readonly dilim?: string;
    readonly p_v3?: number | null;
    readonly p_eski?: number | null;
    readonly p_required?: number | null;
    readonly v3_gecti?: boolean;
    readonly eski_gecerdi?: boolean;
    readonly yasa_surumu?: string | null;
  } | null;
  readonly beyan?: string;
}

export interface IcHucresi {
  readonly ic?: number | null;
  readonly n?: number | null;
  readonly neden?: string | null;
  readonly ci?: { readonly lo?: number | null; readonly hi?: number | null; readonly seviye?: number };
  readonly anlamli?: boolean;
}

export interface BilesenIcBelgesi {
  readonly horizons?: readonly number[];
  readonly components?: readonly string[];
  readonly layers?: readonly string[];
  readonly tablo?: Readonly<Record<string, Readonly<Record<string, Readonly<Record<string, IcHucresi>>>>>>;
  readonly en_guclu?: {
    readonly bilesen?: string;
    readonly horizon?: number;
    readonly ic?: number | null;
    readonly n?: number | null;
    readonly ci?: { readonly lo?: number | null; readonly hi?: number | null };
    readonly anlamli?: boolean;
  } | null;
  readonly verdict?: string;
  readonly anlamli_sayim?: Readonly<Record<string, number>>;
  readonly n_gozlem?: Readonly<Record<string, number>>;
  readonly getiri_tanimi?: string;
  readonly ci_yontem?: string;
  readonly ci_varsayim?: string;
  readonly cf_katman_gerekce?: string;
}

export interface KucultulmusIc {
  readonly n_hucre?: number;
  readonly kucultuldu?: boolean;
  readonly neden?: string;
  readonly kaynak?: string;
  readonly rol?: string;
  readonly tau?: number | null;
  readonly mu?: number | null;
  readonly tablo_ici_eb?: { readonly var?: boolean; readonly neden?: string } & Readonly<Record<string, unknown>>;
}

export interface TerfiHukmu {
  readonly karar?: "EVET" | "HAYIR" | "ÖLÇÜLEMEDİ" | string;
  readonly sinif?: string;
  readonly neden?: string;
}

export interface OgrenmeBlogu {
  readonly antrenman?: AntrenmanDurumu | null;
  readonly dolgu_kuyrugu?: DolguKuyrugu | null;
  readonly eksen2?: Readonly<Record<string, unknown>> | null;
  readonly son_kosu?: Readonly<Record<string, unknown>> | null;
  readonly nabiz?: Readonly<Record<string, { readonly gecen_saat?: number | null; readonly pencere_saat?: number; readonly bayat?: boolean | null; readonly hic_kosmadi?: boolean }>>;
  readonly son_fit?: {
    readonly ts?: string | null;
    readonly n?: number | null;
    readonly n_real?: number | null;
    readonly n_cf?: number | null;
    readonly brier_train?: number | null;
    readonly terfi?: TerfiHukmu;
    readonly kaynak?: string | null;
    readonly beyan?: string;
  };
  readonly son_deneme?: {
    readonly ts?: string | null;
    readonly atlama_nedeni?: string | null;
    readonly damga_var?: boolean;
  };
}

export interface Isinma {
  readonly last?: string | null;
  readonly ucb_top?: readonly string[];
  readonly ticks?: number;
  readonly every?: number;
  readonly skip?: unknown;
  readonly polled?: boolean;
  readonly horizon_ready?: boolean | null;
}

export interface TeshisGovdesi {
  readonly onbellekten?: boolean;
  readonly hesaplama_ts?: string;
  readonly ogrenme?: OgrenmeBlogu;
  readonly mlops?: {
    readonly shadow_law?: GolgeYasasi;
    readonly shadowlaw_drift?: unknown;
    readonly component_ic?: BilesenIcBelgesi | null;
    readonly shrunk_component_ic?: KucultulmusIc;
    readonly warmup?: Isinma;
  };
}

/* ---- /api/agent ---------------------------------------------------------- */

export interface SurumSatiri {
  readonly version?: string;
  readonly rolled_back?: boolean | null;
  readonly reinstated?: boolean | null;
  readonly source?: string | null;
  readonly note?: string | null;
  readonly parent?: number | string | null;
  readonly live_score?: number | null;
  readonly backtest_oos?: number | null;
  readonly baseline_verdict?: string | null;
  readonly baseline_source?: string | null;
  readonly baseline_n_trades?: number | null;
  readonly n_trades?: number | null;
  readonly live_since?: string | null;
  readonly guncel?: boolean;
}

export type RollbackSicili =
  | { readonly var: false; readonly neden: string }
  | {
      readonly var: true;
      readonly current_version?: number | string | null;
      readonly surumler?: readonly SurumSatiri[];
      readonly geri_alinan_n?: number;
      readonly acik_dongu?: Readonly<Record<string, unknown>> | null;
      readonly acik_dongu_neden?: string | null;
      readonly olaylar?: readonly {
        readonly ts?: string;
        readonly event?: string;
        readonly version?: unknown;
        readonly parent?: unknown;
        readonly reason?: unknown;
      }[];
      readonly olay_penceresi?: number;
    };

export interface RegresyonDilimi {
  readonly ad?: string;
  readonly n?: number;
  readonly avg_r?: number | null;
  readonly az_ornek?: boolean;
}

export interface RegresyonSurumu {
  readonly version?: string;
  readonly n?: number;
  readonly avg_r?: number | null;
  readonly az_ornek?: boolean;
  readonly rejim?: readonly RegresyonDilimi[];
  readonly cikis?: readonly RegresyonDilimi[];
  readonly setup?: readonly RegresyonDilimi[];
}

export type RegresyonKirilimi =
  | { readonly var: false; readonly neden: string }
  | {
      readonly var: true;
      readonly surumler?: readonly RegresyonSurumu[];
      readonly fark?: {
        readonly yeni?: string;
        readonly eski?: string;
        readonly rejim?: readonly {
          readonly ad?: string;
          readonly delta_r?: number | null;
          readonly neden?: string;
          readonly n_yeni?: number;
          readonly n_eski?: number;
          readonly az_ornek?: boolean;
        }[];
      } | null;
      readonly hipotezler?: readonly unknown[];
      readonly az_ornek_esigi?: number;
      readonly islem_n?: number;
      readonly sinir?: string;
    };

export interface AjanGovdesi {
  readonly scoreboard?: {
    readonly current_version?: number | string | null;
    readonly versions?: Readonly<Record<string, Readonly<Record<string, unknown>>>>;
  };
  readonly hypotheses?: readonly unknown[];
  readonly calibration_scatter?: readonly {
    readonly predicted?: number | null;
    readonly realized?: number | null;
    readonly variable?: string | null;
    readonly status?: string | null;
  }[];
  readonly calibration?: Kalibrasyon;
  readonly skill_attribution?: { readonly skills?: readonly unknown[] };
  readonly rollback?: RollbackSicili;
  readonly regresyon?: RegresyonKirilimi;
}

/* ---- /api/skills --------------------------------------------------------- */

export interface KatalogSatiri {
  readonly name?: string;
  readonly description?: string;
  readonly category?: string | null;
  readonly enabled?: boolean;
  readonly mode?: string | null;
  readonly shadow?: boolean;
  readonly pipeline?: string | null;
  readonly protected?: boolean;
  readonly retired?: boolean;
  readonly yasam_dongusu?: string | null;
  readonly requires?: readonly string[];
  readonly n?: number;
  readonly win_rate?: number | null;
  readonly avg_r?: number | null;
  readonly n_cf?: number;
  readonly cf_avg_r?: number | null;
  readonly ajan_yukleme_n?: number | null;
  readonly ajan_acilma_n?: number | null;
  readonly son_yukleme?: string | null;
  readonly son_acilma?: string | null;
  readonly ajan_kullanim_neden?: string | null;
  readonly ajan_kullanim_kaynak?: string | null;
}

/* ---- GÖLGE SIRALAMA KOLU (EDG-2026-078 Aşama A) — `gorus_defteri.golge_kol` ---------------- */

export interface GolgeKolRaporu {
  readonly durum?: "ölçüldü" | "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ" | "ÖLÇÜLEMEDİ" | string;
  readonly kart?: string;
  readonly neden?: string | null;
  readonly n_seans?: number | null;
  readonly n_min_seans?: number;
  readonly delta_rank_ic?: {
    readonly ort?: number | null;
    readonly lo?: number | null;
    readonly hi?: number | null;
    readonly n_kume?: number | null;
    readonly yontem?: string;
  } | null;
  readonly ustN_kesisim_ort?: number | null;
  readonly n_kesisim_seans?: number;
  readonly ustN_kesisim_esik?: number;
  readonly ustN_kesisim_esigi_gecti?: boolean | null;
  readonly sure_p95_ms?: number | null;
  readonly eslesmeyen_n?: number | null;
  readonly beyan?: string;
}

export interface SkillGovdesi {
  readonly counts?: {
    readonly total?: number;
    readonly enabled?: number;
    readonly disabled?: number;
    readonly active_in_pipelines?: number;
  };
  readonly catalog?: readonly KatalogSatiri[];
  readonly recommendations?: readonly unknown[];
  readonly revisions?: readonly unknown[];
  readonly recent_runs?: readonly Readonly<Record<string, unknown>>[];
  readonly envanter?: {
    readonly kayit?: { readonly toplam?: number; readonly aktif?: number; readonly arsiv?: number };
    readonly klasor?: Readonly<Record<string, number>>;
    readonly fark?: Readonly<Record<string, readonly string[]>>;
    readonly hukum?: string;
  };
  readonly golge_beyani?: string;
  // `api._eksen2_gorus()`ın TAM gövdesi burada modellenmez (okunmayan alanı tiplemek tembelliktir);
  // yalnız Araçlar sekmesinin fiilen okuduğu `golge_kol` (EDG-2026-078 Aşama A) taşınır.
  readonly gorus_defteri?: {
    readonly durum?: string;
    readonly golge_kol?: GolgeKolRaporu | null;
  } | null;
}
