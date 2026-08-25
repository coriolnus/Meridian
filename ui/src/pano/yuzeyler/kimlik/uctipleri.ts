/* ============================================================================
   UÇ TİPLERİ — Giriş ve Operatör yüzeylerinin okuduğu dört gövde
   ----------------------------------------------------------------------------
   HER ALAN OPSİYONEL ve bu bir tembellik değil bir ÖLÇÜM: `meridian/api.py`
   okundu ve bu uçların hiçbiri alan VARLIĞINI garanti etmiyor. `?` işareti
   "gelmeyebilir" demek; gelmediğinde ekran `Olculemedi` çizer, `0` ya da `—`
   DEĞİL. Zorunlu (`readonly x: T`) yazmak, derleyiciye ölçmediğimiz bir şeyi
   garanti ettirmek olurdu — ve TypeScript o yalanı çalışma anında yakalayamaz.

   TİPLER `api.py`DEN OKUNARAK YAZILDI, TAHMİN EDİLMEDİ:
     · /api/session  → api.py::api_session       (yetkisiz TEK uç)
     · /api/alpaca   → api.py::api_alpaca + adapters/alpaca.py::dashboard_view
     · /api/secrets  → api.py::api_secrets + secrets.py::status
     · /api/diagnostics.saglayicilar → api.py::_saglayicilar / _saglayici_satiri
   ============================================================================ */

/* --- /api/session -------------------------------------------------------- */

export interface OturumGovdesi {
  readonly authenticated?: boolean;
  readonly password_set?: boolean;
  /** Çerez `Secure` işaretlenecek mi — yani bağlantı TLS'li mi görünüyor. */
  readonly tls?: boolean;
}

/** `/api/login` başarı gövdesi. `expires_in` oturum ömrünün TEK ÖLÇÜLEN kaynağı. */
export interface GirisBasarisi {
  readonly ok?: boolean;
  readonly expires_in?: number;
}

/* --- /api/alpaca --------------------------------------------------------- */

/* DİKKAT — POZİSYON/EMİR ALANLARI HAM ALPACA JSON'UDUR. `dashboard_view` bu alanları
   ayrıştırmadan geçiriyor (`p.get("qty")`) ve Alpaca REST'i sayıları DİZGE olarak
   döndürür ("12", "184.31"). `number` yazsaydık tip doğru görünür, çalışma anında
   `.toFixed` patlardı; `sayiya()` ikisini de karşılar ve ayrıştıramadığında null der. */
export type HamSayi = string | number | null;

export interface AlpacaPozisyon {
  readonly symbol?: string | null;
  readonly qty?: HamSayi;
  readonly avg_entry?: HamSayi;
  readonly current?: HamSayi;
  readonly upl?: HamSayi;
}

export interface AlpacaEmir {
  readonly symbol?: string | null;
  readonly side?: string | null;
  readonly type?: string | null;
  readonly qty?: HamSayi;
  readonly status?: string | null;
  readonly stop?: HamSayi;
  readonly limit?: HamSayi;
}

/** `alpaca._koruma_hukmu` satırı — POZİSYON başına koruma hükmü. `durum` üç değerden
 *  biridir: `korumali` · `korumasiz` (ÖLÇÜLMÜŞ olgu) · `olculemedi` (ARIZA). İkincisiyle
 *  üçüncüsü asla aynı gösterimi almaz. `stop` null iken durum yine `korumali` olabilir —
 *  emir canlıdır, tetik fiyatı henüz yayınlanmamıştır; fiyat UYDURULMAZ. */
export interface AlpacaKoruma {
  readonly durum?: string;
  readonly stop?: number | null;
  readonly stop_n?: number;
  readonly neden?: string | null;
}

/** `dashboard_view` kırpma muhasebesi. `pencere_doygun` true iken API penceresinin KENDİSİ
 *  dolmuştur: listenin "hepsi bu" olduğu KANITLANMAMIŞTIR. */
export interface AlpacaEmirKirpmasi {
  readonly tavan?: number;
  readonly canli?: number;
  readonly kirpilan?: number;
  readonly pencere_istenen?: number;
  readonly pencere_donen?: number;
  readonly pencere_doygun?: boolean;
}

export interface AlpacaHesap {
  readonly connected?: boolean;
  readonly equity?: number | null;
  readonly cash?: number | null;
  readonly status?: string | null;
  readonly buying_power?: number | null;
  readonly positions?: AlpacaPozisyon[];
  /** ÜÇ HÂL: dizi (okundu) · `null` (OKUNAMADI — nedeni `open_orders_neden`de) · alan yok.
   *  `?? []` ile karşılamak "API düştü" ile "emir yok"u aynı cümleye çıkarır. */
  readonly open_orders?: AlpacaEmir[] | null;
  /** `null` = liste ölçüldü. Dolu = liste neden okunamadı. */
  readonly open_orders_neden?: string | null;
  /** Liste okunamadıysa `null` — olmayan listenin muhasebesi olmaz. */
  readonly open_orders_kirpma?: AlpacaEmirKirpmasi | null;
  /** Sembol → hüküm. `null` ⟺ `koruma_neden` dolu ⟺ POZİSYON listesi okunamadı. */
  readonly koruma?: Readonly<Record<string, AlpacaKoruma>> | null;
  readonly koruma_neden?: string | null;
  /** Hesabın TEK kimlik izi — `dashboard_view` hesap NUMARASI döndürmüyor. */
  readonly endpoint?: string | null;
}

export interface AkisGovdesi {
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
  /** `paper_available` false iken TÜM blok null döner — boş nesne değil. */
  readonly account?: AlpacaHesap | null;
  readonly stream?: AkisGovdesi;
  readonly note?: string;
}

/* --- /api/secrets -------------------------------------------------------- */

export interface SirDurumu {
  readonly set?: boolean;
  /** "env" | "file" | "gcp" — kurulu değilse null. */
  readonly source?: string | null;
  /** MASKELİ ipucu (`••••1234`). BU PANO ONU ÇİZMEZ — bkz. `Sirlar.tsx` başlığı. */
  readonly hint?: string | null;
}

export interface SirlarGovdesi {
  readonly secrets?: Record<string, SirDurumu>;
  readonly live_enabled?: boolean;
  readonly mode?: string;
  readonly autonomy_level?: number;
  readonly model_defaults?: {
    readonly GEMINI_MODEL?: string;
    readonly NOUS_MODEL?: string | null;
  };
  readonly note?: string;
}

/* --- /api/diagnostics (yalnız `saglayicilar` bloğu okunuyor) -------------- */

export interface SaglayiciSatiri {
  readonly ad?: string;
  /** ÜÇ DEĞERLİ: true sağlam · false bozuk · null/undefined ölçülmedi. */
  readonly ok?: boolean | null;
  readonly son_basari_ts?: string | null;
  readonly son_cagri_ts?: string | null;
  readonly hata_orani?: number | null;
  readonly cagri?: number | null;
  readonly hata?: number | null;
  readonly son_hata?: string | null;
  readonly son_durum?: number | string | null;
  /** Sağlık okuması PATLADIYSA yalnız bu alan gelir (`ok: null` ile birlikte). */
  readonly olculemedi?: string;
  readonly ek?: Record<string, unknown>;
}

export interface TeshisGovdesi {
  readonly onbellekten?: boolean;
  readonly hesaplama_ts?: string;
  readonly saglayicilar?: {
    readonly kapsam?: string;
    readonly beyan?: string;
    readonly saglayicilar?: SaglayiciSatiri[];
  };
}
