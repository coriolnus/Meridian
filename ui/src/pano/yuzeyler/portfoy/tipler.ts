/* ============================================================================
   PORTFÖY YÜZEYİNİN GÖVDE TİPLERİ — hepsi `meridian/api.py` OKUNARAK yazıldı
   ----------------------------------------------------------------------------
   TAHMİN YOK: her alan aşağıdaki kaynak satırlardan geldi ve alan adı orada ne
   ise burada da odur.
     · `/api/today`   → api.py::api_today + analytics.today()
     · `/api/alpaca`  → api.py::api_alpaca + adapters/alpaca.dashboard_view()
     · `/api/market`  → api.py::api_market + marketview.build()
     · `/api/diagnostics` → api.py::api_diagnostics + intraday_cycle.health()

   HEPSİ İSTEĞE BAĞLI (`?:`) ve bu bilinçli — `pano/tipler.ts`teki aynı gerekçe:
   uç bir alanı ÖLÇEMEDİĞİNDE onu hiç yazmıyor. `alan?: T | null` üç hâl taşır:
   alan yok (hiç ölçülmedi) · alan null (ölçüldü, sonuç yok) · alan dolu.

   SAYILAR NEDEN `unknown` (fiyat/adet alanlarında): `/api/alpaca` Alpaca REST
   yanıtını HAM geçiriyor (`adapters/alpaca.positions()` → `r.json()`)
   ve Alpaca sayısal alanları DİZGE olarak döndürür ("qty":"10"). Tipi `number`
   yazsaydık derleyici tatmin olur, çalışma zamanı `10 * "123.45"` üretirdi.
   Ayrıştırma tek kapıdan geçer: `olcum.ts::sayi()`.
   ============================================================================ */

/** `portfolio.json.positions` değeri — `broker.Position` dataclass'ının `asdict`i
 *  (`loop._save_broker`). `ticker` KAYBOLMAZ: dataclass alanı olarak satırın içinde durur. */
export interface KitapPozisyonu {
  readonly ticker?: string;
  readonly qty?: unknown;
  readonly entry?: unknown;
  readonly stop?: unknown;
  readonly trail_stop?: unknown;
  readonly target?: unknown;
  readonly risk_dollars?: unknown;
  readonly size_r?: unknown;
  readonly ts_open?: string | null;
  readonly bars_held?: unknown;
  readonly setup?: string | null;
  readonly regime_at_plan?: string | null;
  readonly plan_id?: string | null;
  readonly scaled_out?: boolean;
}

/** `sermaye.broker_mutabakati()` — köprünün TERİMLERİ + kalıntı.
 *  `aciklanamayan` yalnız BEŞ terimin beşi de ölçüldüyse sayı olur; aksi hâlde null
 *  ve `olculemedi_neden` hangi terimin eksik olduğunu yazar. */
export interface BrokerMutabakati {
  readonly broker_equity?: number | null;
  readonly gerceklesmemis_pnl?: number | null;
  readonly broker_reset_gunu_equity?: number | null;
  readonly kitap_cash?: number | null;
  readonly sermaye_tabani?: number | null;
  readonly broker_maliyet_bazli?: number | null;
  readonly broker_reset_sonrasi?: number | null;
  readonly kitap_reset_sonrasi?: number | null;
  readonly aciklanamayan?: number | null;
  readonly olculemedi_neden?: string | null;
  readonly reset_tarihi?: string | null;
  readonly broker_gecmis_neden?: string | null;
}

/** `sermaye.pozisyon_mutabakati()`. YÖN AYRI KOVALARDA:
 *  "kitapta var broker'da yok" (karşılıksız) ile tersi (kitabın bilmediği pozisyon)
 *  aynı şey DEĞİL — fonksiyonun kendi docstring'inin yasası. */
export interface PozisyonMutabakati {
  readonly ayrisan?: readonly { ticker?: string; kitap?: number; broker?: number; fark?: number }[];
  readonly yalniz_kitapta?: readonly { ticker?: string; kitap?: number; broker?: number }[];
  readonly yalniz_brokerda?: readonly { ticker?: string; kitap?: number; broker?: number }[];
  readonly ayrisan_sayisi?: number | null;
  readonly toplam_sembol?: number | null;
  readonly olculemedi_neden?: string | null;
}

/** `sermaye.koken()` — panonun okuduğu TEK sermaye yüzeyi. */
export interface SermayeKokeniTam {
  readonly gercek_canli_sermaye?: number | null;
  readonly canli_islem_n?: number;
  readonly tohum_islem_n?: number;
  readonly belirsiz_islem_n?: number;
  readonly canli_pnl_usd?: number | null;
  readonly tohum_etkisi_usd?: number | null;
  readonly tohum_etkisi_neden?: string | null;
  readonly tohum_etkisi_durum?: string | null;
  readonly tohum_etkisi_ibare?: string | null;
  readonly reset_tarihi?: string | null;
  readonly ayrisik?: boolean | null;
  readonly sermaye_tabani?: number | null;
  readonly renk?: string;
  readonly ibare?: string;
  readonly nabiz_sermaye?: number | null;
  readonly nabiz_ayrisik?: boolean | null;
  readonly beyan?: string;
}

/** `ledgerstamp.teyit_counts()`. Anahtarlar `ledgerstamp` sabitlerinden gelir
 *  (`TEYITLI` / `KARSILIKSIZ` / `TEYIT_OLCULEMEDI` / `TEYIT_KAPSAM_DISI`) — `olculemedi`
 *  "karşılıksız" DEĞİLDİR, bakılamadı demektir. */
export interface DefterTeyit {
  readonly teyitli?: number;
  readonly karsiliksiz?: number;
  readonly olculemedi?: number;
  readonly kapsam_disi?: number;
}

/** `/api/today` gövdesinin PORTFÖY yarısı. `pano/tipler.ts::BugunGovdesi` panonun
 *  ORTAK alanlarını taşıyor (üst bar + kenar çubuğu de onu okuyor); bu arayüz o
 *  sözleşmeye dokunmadan yalnız bu yüzeyin ek alanlarını ekler. */
export interface BugunPortfoyEk {
  readonly open_positions?: readonly KitapPozisyonu[];
  readonly kitap?: {
    readonly realized_pnl?: number | null;
    readonly day_start_equity?: number | null;
    readonly peak_equity?: number | null;
  };
  readonly sermaye_koken?: SermayeKokeniTam;
  readonly broker_mutabakati?: BrokerMutabakati;
  readonly pozisyon_mutabakati?: PozisyonMutabakati;
  /** DİKKAT (`api.py::api_today`): `try` bloğunun İÇİNDE yazılır — broker köprüsü patlarsa
   *  alan HİÇ YOKTUR (null değil). `undefined` kontrolü ZORUNLU. */
  readonly defter_teyit?: DefterTeyit;
  readonly current_exposure_pct?: number | null;
  readonly day_pnl_pct?: number | null;
  readonly equity?: number | null;
  readonly armed_plans?: readonly { ticker?: string; id?: string; setup?: string }[];
  readonly alpaca_submitted?: readonly string[];
  readonly latest_session?: string | null;
}

// ---- /api/alpaca ------------------------------------------------------------
/** Alpaca REST pozisyon satırının `dashboard_view` izdüşümü.
 *  Sayısal alanlar HAM Alpaca dizgeleri olabilir — bkz. dosya başlığı. */
export interface BrokerPozisyonu {
  readonly symbol?: string;
  readonly qty?: unknown;
  readonly avg_entry?: unknown;
  readonly current?: unknown;
  readonly upl?: unknown;
}

export interface BrokerEmri {
  readonly symbol?: string;
  readonly side?: string;
  readonly type?: string;
  readonly qty?: unknown;
  readonly status?: string;
  readonly stop?: unknown;
  readonly limit?: unknown;
}

/** `alpaca._koruma_hukmu` satırı — POZİSYON başına koruma hükmü.
 *
 *  `durum` ÜÇ DEĞERDEN BİRİDİR ve üçü ayrı olgudur: `korumali` (sembolde canlı stop var) ·
 *  `korumasiz` (emir listesi OKUNDU, stop YOK — ölçülmüş olgu) · `olculemedi` (emir listesi
 *  okunamadı, hüküm VERİLMEDİ — arıza). Tipi `string` bırakmak bilinçli: gövde yarın dördüncü
 *  bir hâl yazarsa birlik-tipi onu derleme anında değil ÇALIŞMA anında sessizce düşürürdü;
 *  okuyucu bilinmeyen hâli "tanınmadı" diye ÇİZER.
 *
 *  `stop` null iken durum yine `korumali` olabilir: emir CANLIDIR ama tetik fiyatı henüz
 *  yayınlanmamıştır (iz süren stop). Fiyat UYDURULMAZ, `neden` bunu yazar.
 *  `stop_n` > 1 ÇİFTE KORUMA demektir — aynı hisseyi iki emir rehin tutar. */
export interface KorumaHukmu {
  readonly durum?: string;
  readonly stop?: number | null;
  readonly stop_n?: number;
  readonly neden?: string | null;
}

/** `alpaca.dashboard_view` kırpma muhasebesi — SESSİZ KIRPMA YOK.
 *
 *  `kirpilan` gövdeye GİRMEYEN canlı satır sayısıdır. `pencere_doygun` true iken API
 *  penceresinin KENDİSİ dolmuştur ve listenin "hepsi bu" olduğu KANITLANMAMIŞTIR — bu
 *  ikisi ayrı sorudur (biri bizim tavanımız, öteki Alpaca'nın penceresi). */
export interface EmirKirpmasi {
  readonly tavan?: number;
  readonly canli?: number;
  readonly kirpilan?: number;
  readonly pencere_istenen?: number;
  readonly pencere_donen?: number;
  readonly pencere_doygun?: boolean;
}

export interface AlpacaHesabi {
  readonly connected?: boolean;
  readonly equity?: number | null;
  readonly cash?: number | null;
  readonly status?: string | null;
  readonly buying_power?: number | null;
  readonly positions?: readonly BrokerPozisyonu[];
  /** ÜÇ HÂL: dizi (okundu) · `null` (OKUNAMADI — nedeni `open_orders_neden`de) · alan yok
   *  (eski gövde). Eskiden arıza da boş dizi dönüyordu, yani "API düştü" ile "emir yok"
   *  panoda AYNI cümleye çıkıyordu. `?? []` ile karşılamak o yalanı geri getirir. */
  readonly open_orders?: readonly BrokerEmri[] | null;
  /** `null` = liste ölçüldü. Dolu = liste neden okunamadı (gerçek arıza cümlesi). */
  readonly open_orders_neden?: string | null;
  /** Liste okunamadıysa `null` — olmayan listenin muhasebesi olmaz. */
  readonly open_orders_kirpma?: EmirKirpmasi | null;
  /** Sembol → hüküm. `null` ⟺ `koruma_neden` dolu ⟺ POZİSYON listesi okunamadı, yani hangi
   *  sembol için hüküm verileceği bile bilinmiyor. Emir listesi okunamadıysa harita KURULUR
   *  ama her girdi `olculemedi` olur — "koruma yok" DEMEZ. */
  readonly koruma?: Readonly<Record<string, KorumaHukmu>> | null;
  readonly koruma_neden?: string | null;
  readonly endpoint?: string;
}

/** `broker_reconcile.json` HAM alanları (`loop.reconcile_broker_state`) + uç katmanının
 *  ayrıştırdığı `failed_submissions` (`api.py::api_alpaca`). DİKKAT: `hwm_pairs` ve
 *  `partial_fills` bu uçta YOKTUR — onları /api/diagnostics katmanı ekliyor. */
export interface MutabakatKaydi {
  readonly date?: string | null;
  readonly updated?: string | null;
  readonly api_ok?: boolean;
  readonly checked?: boolean;
  readonly skip_reason?: string | null;
  readonly skip_sinif?: string | null;
  readonly mirror_drift?: boolean;
  readonly position_drift?: boolean;
  readonly stripped?: readonly (string | null)[];
  readonly drift?: readonly Record<string, unknown>[];
  readonly ghosts?: readonly Record<string, unknown>[];
  readonly force_sync?: { stripped?: number; trail_patched?: number; trail_failed?: number };
  readonly positions?: {
    readonly api_ok?: boolean;
    readonly missing_on_alpaca?: readonly string[];
    readonly qty_drift?: readonly { ticker?: string; local_qty?: number; alpaca_qty?: number; drift_sinifi?: string | null }[];
    readonly external?: readonly string[];
    readonly engine_orphans?: readonly unknown[];
    readonly exit_orphans?: readonly unknown[];
  };
  readonly failed_submissions?: {
    readonly open?: readonly Record<string, unknown>[];
    readonly acked?: readonly Record<string, unknown>[];
  };
  readonly alive_order_syms?: readonly string[];
}

/** `api.py::_stream_view()` — `stream_ok` NABIZLA ÇARPILMIŞ bayraktır,
 *  ham değil; `null` = ayna hiç koşmadı (üçüncü hâl, "KOPUK" DEĞİL). */
export interface AkisSagligi {
  readonly stream_ok?: boolean | null;
  readonly stream_flag?: boolean | null;
  readonly stream_stale?: boolean | null;
  readonly stream_down_since?: string | null;
  readonly stream_checked_age_s?: number | null;
  readonly stream_last_event_ts?: string | null;
  readonly stream_last_error?: string | null;
}

export interface AlpacaGovdesi {
  readonly backend?: string;
  readonly paper_available?: boolean;
  /** `paper_available` false ise TÜM blok null (`api.py::api_alpaca`). */
  readonly account?: AlpacaHesabi | null;
  readonly reconcile?: MutabakatKaydi;
  readonly stream?: AkisSagligi;
  readonly note?: string;
}

// ---- /api/market ------------------------------------------------------------
/** `marketview.build()` satırı. EOD KAPANIŞTIR — bu uç canlı fiyat servis ETMEZ ve
 *  etmediğini `as_of` ile söyler (`api.py::api_market`). `intraday_close` yalnız KAPANMIŞ
 *  + TAZE dakikalık bar demektir, o da yalnız silahlı sembollerde. */
export interface PiyasaSatiri {
  readonly ticker?: string;
  readonly close?: number | null;
  readonly last_date?: string | null;
  readonly intraday_close?: number | null;
  readonly intraday_ts?: string | null;
  readonly position?: boolean;
}

export interface PiyasaGovdesi {
  readonly as_of?: string | null;
  readonly n?: number;
  readonly stale_n?: number;
  readonly rows?: readonly PiyasaSatiri[];
  readonly intraday?: { tracked_n?: number; measured_n?: number; reason?: string; stale_tol_s?: number };
}

// ---- /api/diagnostics (yalnız `intraday` bloğu okunuyor) --------------------
/** `intraday_cycle.health()` + `api.py`nin eklediği dört alan (`api.py::api_diagnostics`).
 *  `armed` OPERATÖRÜN Faz-4b bayrağıdır (state/INTRADAY_ARM); `armed_plans` ise
 *  defterdeki EOD-silahlı plan sayısı. İKİSİ AYRI SORU (`api.py::api_diagnostics` şerhi). */
export interface SeansIciBlogu {
  readonly ok?: boolean | null;
  readonly enabled?: boolean;
  readonly armed?: boolean;
  readonly mode?: string;
  readonly events_handled?: number;
  readonly decisions_written?: number;
  readonly watched?: number;
  readonly watched_planned?: number;
  readonly submitted_4b?: number;
  readonly last_decision_at?: string | null;
  readonly last_error?: string | null;
  readonly skipped?: Readonly<Record<string, number>>;
  readonly armed_plans?: number;
  readonly decisions?: {
    readonly total?: number;
    readonly fired?: number;
    readonly today?: number;
    readonly recent?: readonly Record<string, unknown>[];
  };
  readonly shadow?: {
    readonly enabled?: boolean;
    readonly total?: number;
    readonly today_n?: number;
    readonly would_submit_n?: number;
    readonly blocked_n?: number;
    readonly vs_eod?: Record<string, unknown> | null;
  };
  /** `null` = zamanlayıcı kancası bu süreçte HİÇ KOŞMADI — "boşluk yok" DEĞİL. */
  readonly akis_boslugu?: Record<string, unknown> | null;
}

export interface TeshisGovdesi {
  readonly onbellekten?: boolean;
  readonly hesaplama_ts?: string;
  readonly intraday?: SeansIciBlogu;
}
