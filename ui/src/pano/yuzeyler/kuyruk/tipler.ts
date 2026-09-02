/* ============================================================================
   UÇ GÖVDELERİ — `/api/approvals`, `/api/skills`, `/api/diagnostics`
   ----------------------------------------------------------------------------
   HER ALAN İSTEĞE BAĞLI (`?`) ve bu bilerek. Uç bir şeyi ÖLÇEMEDİĞİNDE alanı hiç
   yazmıyor; `x?: number` ile `x: number | null` arasındaki fark burada anlamlı —
   birincisi "alan yok, hiç ölçülmedi", ikincisi "ölçüldü, sonuç yok". Tipi zorunlu
   yapıp `0` varsaymak, ölçülmemiş bir kuyruğu boş kuyruk diye çizdirirdi.

   `api.py` OKUNARAK YAZILDI, TAHMİN EDİLMEDİ:
     · `api_approvals`            (api.py::api_approvals) — üç öğe türü, alan kümeleri FARKLI
     · `api_skills`               (api.py::api_skills) — `recommendations`/`revisions` HAM satırlar
     · `_hat_cizelgesi`           (api.py::_hat_cizelgesi) — damgalar + koşular + çağrılar + döngüler
     · `watchdog.report`          (watchdog.py::report) — stale / never / askida / n_ok / total
   Emin olunamayan hiçbir alan zorunlu yazılmadı; yokluğu ekranda dürüstçe görünür.
   ============================================================================ */

/* --- /api/approvals ------------------------------------------------------ */

/** Eksen-2 önerisine operatörün verdiği karar (yalnız `uygulanabilir:false` öğelerde VAR). */
export interface KararKaydi {
  readonly id?: string;
  /** `"approve"` | `"reject"` | `null` (karar yok). Alanın yokluğu ≠ `null`. */
  readonly karar?: string | null;
  readonly ts?: string | null;
  readonly gerekce?: string;
  readonly kunye?: unknown;
  readonly okunamadi?: unknown;
  readonly not?: string;
}

/** Gelen kutusu öğesi. ÜÇ TÜRÜN BİRLEŞİMİ — tür başına alan kümesi farklı, hepsi opsiyonel. */
export interface OnayOgesi {
  /** `"arming"` | `"skill_revision"` | `"skill_rec"`. Bilinmeyen tür de çizilir (uç yeni tür ekleyebilir). */
  readonly type?: string;
  readonly id?: string;
  readonly title?: string;
  readonly evidence?: string;
  readonly actions?: readonly string[];
  readonly note?: string;
  /** `skill_revision` ve `skill_rec` taşır; `arming` TAŞIMAZ (konusu kurulum adı, başlıkta). */
  readonly skill?: string;
  /** YALNIZ `skill_rec`: önerilen eylem (`shadow` / `activate` / …). */
  readonly action?: string;
  readonly uygulanabilir?: boolean;
  readonly ornek?: number | null;
  readonly ornek_yeterli?: boolean | null;
  readonly ornek_notu?: string | null;
  readonly karar_kaydi?: KararKaydi;
}

export interface OnayGovdesi {
  readonly level?: number;
  readonly inbox?: readonly OnayOgesi[];
  /** `approvals.jsonl` satırları. L0'da HER ZAMAN `[]` — "defter boş" DEMEK DEĞİL. */
  readonly pending?: readonly Record<string, unknown>[];
  readonly note?: string;
}

/* --- /api/skills (YALNIZ damga ve künye için okunuyor) ------------------- */

/** `skill_recommendations.jsonl` HAM satırı — gelen kutusunun taşımadığı `ts` BURADA. */
export interface SkillOnerisi {
  readonly ts?: string;
  readonly skill?: string;
  readonly action?: string;
  readonly rationale?: string;
  readonly source?: string;
  readonly pending?: boolean;
  readonly applied?: boolean;
}

/** `skill_revisions.json` HAM satırı — geliş damgası `at` (ISO), `ts` DEĞİL. */
export interface SkillRevizyonu {
  readonly skill?: string;
  readonly status?: string;
  readonly rationale?: string;
  readonly at?: string;
  readonly chars?: number;
  readonly evidence?: {
    readonly n?: number | null;
    readonly avg_r?: number | null;
    readonly n_cf?: number | null;
    readonly cf_avg_r?: number | null;
  };
}

export interface SkillGovdesi {
  readonly recommendations?: readonly SkillOnerisi[];
  readonly revisions?: readonly SkillRevizyonu[];
}

/* --- /api/today içindeki planlar (onay bekleyen REVIEW) ------------------ */

/** `todays_plans` satırının BU YÜZEYİN okuduğu kesiti. */
export interface PlanOzeti {
  readonly id?: string;
  readonly date?: string;
  readonly ticker?: string;
  readonly setup?: string;
  readonly score?: number | null;
  readonly gate_verdict?: string;
  readonly gate_reasons?: readonly string[];
  readonly entry_trigger?: number | null;
  readonly size_r?: number | null;
  readonly sector?: string;
  readonly llm_veto?: boolean;
  readonly llm_opinion?: string;
  readonly expired?: boolean;
  readonly age_days?: number;
  readonly traded?: boolean;
  readonly last_close?: number;
  readonly drift_pct?: number;
  /** Sunucu DAMGALAR (`api.py::_onay_bekleyen_damgala`); pano yalnız bayrağı okur. */
  readonly onay_bekliyor?: boolean;
  readonly operator_onayi?: Record<string, unknown>;
}

/* --- /api/diagnostics (çizelge + bekçi + zamanlayıcı + silahlanma) ------- */

export interface CizelgeKosusu {
  readonly run_id?: string;
  readonly pipeline?: string;
  readonly started?: string;
  readonly finished?: string;
  readonly status?: string;
  readonly error?: string | null;
  readonly skills_invoked?: number;
  readonly skills_declared_not_run?: number;
  readonly skills_skipped?: number;
  readonly artifacts?: number;
}

export interface CizelgeCagrisi {
  readonly ts?: string;
  readonly kind?: string;
  readonly model?: string;
  readonly attempt?: number;
  readonly empty?: boolean;
  readonly tool_calls?: number;
}

export interface CizelgeDongusu {
  readonly ts?: string;
  readonly date?: string;
  readonly regime?: string;
  readonly candidates?: number;
  readonly plans?: number;
  readonly armed?: number;
  readonly open_positions?: number;
  readonly data_ok?: boolean;
  readonly halted?: boolean;
}

export interface SonDongu {
  readonly var?: boolean;
  readonly kaynak?: string | null;
  readonly neden?: string;
  readonly date?: string;
  readonly ts?: string;
  readonly yas_saat?: number | null;
  readonly candidates?: number;
  readonly plans?: number;
  readonly armed?: number;
  readonly regime?: string;
  readonly open_positions?: number;
  readonly data_ok?: boolean;
  readonly halted?: boolean;
}

export interface CizelgeBlogu {
  readonly var?: boolean;
  /** mekanizma adı → ISO damgası. Damgasız mekanizma anahtarı HİÇ YOKTUR (saat üretilmez). */
  readonly damgalar?: Readonly<Record<string, string>>;
  readonly damga_neden_yok?: string | null;
  readonly kosular?: readonly CizelgeKosusu[];
  readonly cagrilar?: readonly CizelgeCagrisi[];
  readonly son_dongu?: SonDongu;
  readonly donguler?: readonly CizelgeDongusu[];
  readonly olay_penceresi?: number;
  readonly scheduler_updated?: string;
  readonly bekci_ok?: number | null;
  readonly bekci_total?: number | null;
}

export interface BekciGecikmesi {
  readonly name?: string;
  readonly gap_h?: number;
  readonly expected_h?: number;
  /** YALNIZ `askida` satırlarında: sistemin kendi beyanıyla neden beklemede. */
  readonly neden?: string;
  readonly detay?: string;
}

export interface BekciBlogu {
  readonly stale?: readonly BekciGecikmesi[];
  readonly never?: readonly string[];
  readonly askida?: readonly BekciGecikmesi[];
  /** ÜÇ DEĞERLİ hüküm: `true` hepsi penceresinde · `false` ihlal var · `null` askıda bekleyen var. */
  readonly ok?: boolean | null;
  readonly n_ok?: number;
  readonly total?: number;
}

export interface ZamanlayiciBlogu {
  readonly updated?: string;
  readonly last_tick?: string;
  readonly poll_seconds?: number;
  readonly cycles?: number;
  readonly learn_session?: string;
  readonly y4_session?: string;
  readonly validation_week?: string;
}

export interface SilahlanmaOlcumu {
  readonly status?: string;
  readonly search_p?: number;
  readonly confirm_p?: number;
  readonly p_required?: number;
  readonly incumbent_oos?: number;
  readonly candidate_oos?: number;
  readonly fold_wins?: string;
  readonly why?: string;
  readonly n?: number;
  readonly avg_r?: number;
}

export interface SilahlanmaRaporu {
  readonly checked_at?: string;
  readonly rule?: string;
  readonly measurements?: Readonly<Record<string, SilahlanmaOlcumu>>;
  readonly cf_report?: Readonly<Record<string, { readonly n?: number; readonly win_rate?: number; readonly avg_r?: number }>>;
}

export interface TeshisGovdesi {
  readonly cizelge?: CizelgeBlogu;
  readonly watchdog?: BekciBlogu;
  readonly scheduler?: ZamanlayiciBlogu;
  readonly gatekeeper?: { readonly arming?: SilahlanmaRaporu };
  readonly hesaplama_ts?: string;
  readonly onbellekten?: boolean;
}
