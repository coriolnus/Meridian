/* ============================================================================
   BUGÜN YÜZEYİ — GÖVDE TİPLERİ (ölçülerek yazıldı, tahminle DEĞİL)
   ----------------------------------------------------------------------------
   Kaynak: `meridian/api.py::api_today` + `meridian/analytics.py::today` +
   `meridian/api.py::api_performance`. Her alan o iki
   fonksiyonun GERÇEKTEN yazdığı anahtardır; şekli tahmin edilen tek alan yok.

   NEDEN `pano/tipler.ts` GENİŞLETİLİYOR, KOPYALANMIYOR: paylaşılan `BugunGovdesi`
   üst barın ve kenar çubuğunun de baktığı sözleşmedir ve bu turda BANA KAPALI.
   Ondan türeyip yalnız bu yüzeyin okuduğu alanları eklemek, iki ayrı gövde tipi
   tutmaktan güvenli: ortak alanlar tek yerde kalır, ayrışamaz.

   HEPSİ İSTEĞE BAĞLI ve bu bilerek (üst tipin başlığındaki yasa): uç bir alanı
   ÖLÇEMEDİĞİNDE onu hiç yazmaz. `alan === undefined` "hiç ölçülmedi", `alan === null`
   "ölçüldü, sonuç yok" demektir; ikisi ekranda AYNI cümleyi kurmaz.
   ============================================================================ */
import type { BugunGovdesi, Nabiz, SermayeKokeni } from "../../tipler";

/** `state/heartbeat.json` HAM gövdesi. Ölçülen anahtarlar (yerel dosya, 2026-08-25):
 *  armed · autonomy_level · breaker_tripped · data_ok · day_pnl_pct · equity · explore_mode ·
 *  exposure_budget_pct · halted · last_bar · last_date · mirror_drift · mode · n_trades · note ·
 *  open_positions · regime · replay_seeded · score · ts · version.
 *  ALANLARIN VARLIĞI GARANTİ DEĞİL: tohum nabzı canlı-döngü nabzından daha az anahtar taşır
 *  (`api_digest` içindeki "source live fields defensively" şerhi aynı gerçeği söylüyor). */
export interface NabizTam extends Nabiz {
  readonly data_ok?: boolean;
  readonly regime?: string;
  readonly last_bar?: string;
  readonly explore_mode?: boolean;
  readonly exposure_budget_pct?: number;
}

/** `sermaye.koken()`. Bu yüzey yalnız üç alanını okuyor;
 *  gerisi Portföy yüzeyinin işi — okumadığım alanı tipe yazmak, okunuyormuş gibi görünürdü. */
export interface SermayeKokeniTam extends SermayeKokeni {
  readonly gercek_canli_sermaye?: number | null;
  readonly canli_islem_n?: number | null;
}

/** Bir plan satırı. Çekirdek alanlar `loop`un yazdığı plan kaydından; `expired`/`traded`/
 *  `last_close`/`drift_pct`/`onay_bekliyor` UÇ KATMANI EKLERİDİR (`_enrich_stale_plans`,
 *  `_onay_bekleyen_damgala`) ve yalnız o damgalama koştuysa VARDIR.
 *  YEREL DEFTERDE ÖLÇÜLDÜ (2026-08-25, son seans 2026-07-28, 10 plan): `exploration` ve
 *  `llm_veto` satırlarda YOKTU — bu yüzden ikisi de opsiyonel ve yoklukları ekranda
 *  "yok" değil, hiç çizilmeyerek karşılanıyor. */
export interface Plan {
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
  readonly exploration?: boolean | null;
  readonly llm_veto?: boolean | null;
  readonly expired?: boolean;
  readonly age_days?: number;
  readonly traded?: boolean;
  readonly last_close?: number;
  readonly drift_pct?: number;
  readonly onay_bekliyor?: boolean;
}

/** `_son_dongu()` — günlük döngünün KENDİ kaydı (`events.jsonl`
 *  içindeki son `daily_cycle` satırı). BU YÜZEY YALNIZ ÜÇ ALANINI OKUYOR ve bu
 *  bilinçli: kardeş kartın (Karar zinciri hunisi) hangi SEANSI anlattığını
 *  söyleyebilmek için damga + damganın yokluk nedeni yeterli. Sayıları
 *  (`candidates`/`plans`/`armed`) buraya yazmak, okunmayan alanı okunuyormuş gibi
 *  gösterirdi — dosyanın başındaki kural.
 *
 *  `var: false` iken `date` YOKTUR ve `neden` doludur; ikisini birden okuyup
 *  "damga ölçülemedi + NEDEN" yazmak, tarih uydurmanın alternatifidir. */
export interface SonDonguDamgasi {
  readonly var?: boolean;
  readonly neden?: string | null;
  readonly date?: string | null;
}

/** `GET /api/today` — paylaşılan nabzın gövdesi, bu yüzeyin okuduğu alanlarla. */
export interface BugunTam extends BugunGovdesi {
  readonly son_dongu?: SonDonguDamgasi;
  readonly heartbeat?: NabizTam;
  readonly heartbeat_age_seconds?: number | null;
  readonly sermaye_koken?: SermayeKokeniTam;
  readonly todays_plans?: readonly Plan[];
  readonly todays_plan_date?: string | null;
  readonly day_pnl_pct?: number | null;
  readonly current_exposure_pct?: number | null;
  readonly broker?: string;
}

/** `_egri_beyani` — eğrinin PENCERE BEYANI. Grafiğin altındaki şerit budur:
 *  seri kaç nokta, nereden nereye, kitabın son seansından ne kadar geride, nerede kırık. */
export interface EgriBeyani {
  readonly n_nokta?: number;
  readonly okunamayan_nokta?: number;
  readonly ilk?: readonly [string, number] | null;
  readonly son?: readonly [string, number] | null;
  readonly son_seans?: string | null;
  readonly gecikme_gun?: number | null;
  readonly n_bosluk?: number;
  readonly bosluk_esigi_gun?: number;
  readonly reset_isaretleri?: readonly {
    readonly id?: string;
    readonly tarih?: string;
    readonly i?: number | null;
    readonly konum_neden?: string | null;
  }[];
  readonly tohum_siniri?: {
    readonly replay_end?: string | null;
    readonly kaynak?: string | null;
    readonly i?: number | null;
    readonly konum_neden?: string | null;
  } | null;
  readonly beyan?: string;
}

/** `GET /api/performance` — bu yüzey YALNIZ eğriyi ve beyanını okuyor.
 *  ÖLÇÜLDÜ (state/equity_curve.json, 2026-08-25): 882 nokta, `[["2023-01-12", 100000.0], …]`,
 *  son nokta 2026-07-20. `/api/plots` AYNI SORUYU CEVAPLAMIYOR — o uç kurulum × rejim
 *  MATRİSİ döndürür (setups/regimes/grid), hiçbir zaman serisi taşımaz (`api_plots`).
 *  Eğri bu yüzden buradan geliyor; seçim ölçülerek yapıldı, varsayılarak değil. */
export interface PerformansGovdesi {
  readonly equity_curve?: { readonly points?: readonly (readonly unknown[])[] };
  readonly equity_curve_beyani?: EgriBeyani;
}
