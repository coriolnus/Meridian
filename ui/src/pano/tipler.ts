/* ============================================================================
   API GÖVDE TİPLERİ — `/api/today` ve `/api/session`
   ----------------------------------------------------------------------------
   HEPSİ İSTEĞE BAĞLI ve bu bilerek: uçlar bir alanı ÖLÇEMEDİĞİNDE onu hiç
   yazmıyor (uydurma yasağının sunucu tarafı). `equity?: number` ile
   `equity: number | null` arasındaki fark burada anlamlıdır — birincisi "alan
   yok, hiç ölçülmedi", ikincisi "ölçüldü, sonuç yok" demek. Tipi zorunlu yapıp
   `0` varsaymak, ölçülmemiş bir sermayeyi sıfır sermaye diye çizdirirdi.
   ============================================================================ */

export interface Nabiz {
  readonly version?: number;
  readonly breaker_tripped?: boolean;
}

export interface SermayeKokeni {
  readonly renk?: string;
  readonly ibare?: string;
}

export interface BugunGovdesi {
  readonly halted?: boolean;
  readonly stale?: boolean;
  readonly data_ok?: boolean;
  readonly broker?: string;
  readonly mode?: string;
  readonly equity?: number | null;
  readonly autonomy_level?: string | number | null;
  readonly sermaye_koken?: SermayeKokeni;
  readonly heartbeat?: Nabiz;
  readonly verdict_counts?: Readonly<Record<string, number>>;
  readonly todays_plans?: readonly unknown[];
  readonly open_positions?: readonly unknown[];
  /** Gelen kutusu — senden İŞ isteyen karar sayısı. `pending_count` ile AYNI ŞEY DEĞİL. */
  readonly inbox_count?: number | null;
  /** O seans KURULAN plan sayısı (GO/REVIEW). Kimseden bir şey istemez. */
  readonly pending_count?: number | null;
}

export interface OturumGovdesi {
  readonly authenticated?: boolean;
  readonly password_set?: boolean;
}
