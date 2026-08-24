/* ============================================================================
   SİSTEM SAĞLIĞI — UÇ GÖVDE TİPLERİ
   ----------------------------------------------------------------------------
   HER ALAN İSTEĞE BAĞLI ve bu bilinçli (bkz. `pano/tipler.ts` başlığı): uçlar bir
   alanı ÖLÇEMEDİĞİNDE onu HİÇ YAZMIYOR. `x?: number` ile `x: number | null`
   arasındaki fark burada anlamlıdır — birincisi "alan yok, hiç ölçülmedi",
   ikincisi "ölçüldü, sonuç yok". Tipi zorunlu yapıp `0` varsaymak, ölçülmemiş bir
   CPU'yu boşta göstermek olurdu.

   TİPLER `meridian/api.py` OKUNARAK yazıldı, tahminle DEĞİL (brief'in açık şartı).
   Kaynak satırları alanların yanında duruyor ki bir sonraki tur alanın nereden
   geldiğini git geçmişinden değil koddan doğrulasın.
   ============================================================================ */

/* --- /api/alerts · api.py:2952 → notify.inbox() -------------------------- */

export interface AlarmGrubu {
  readonly token?: string;
  readonly n?: number;
  readonly first_ts?: string | null;
  readonly last_ts?: string | null;
  readonly message?: string;
}

export interface AlarmGovdesi {
  readonly ack_ts?: string | null;
  /** TÜM grupların toplamı — `groups` 60'ta kırpılır, bu KIRPILMAZ. */
  readonly pending?: number;
  readonly groups?: readonly AlarmGrubu[];
  readonly channel_configured?: boolean;
  /** null = ACK yok, ölçülemedi (false ile AYNI ŞEY DEĞİL). */
  readonly window_truncated?: boolean | null;
  readonly window_lines?: number;
  readonly window_oldest_ts?: string | null;
}

/* --- /api/market · api.py:1757 → marketview.build() ---------------------- */

export interface PiyasaSatiri {
  readonly ticker?: string;
  readonly source?: string;
  readonly last_date?: string | null;
  readonly close?: number | null;
  readonly chg1_pct?: number | null;
  readonly chg20_pct?: number | null;
  readonly adv20_usd?: number | null;
  readonly position?: boolean;
  readonly armed?: boolean;
  readonly retired?: boolean;
  readonly plans_n?: number;
  readonly intraday_close?: number | null;
  readonly intraday_ts?: string | null;
  readonly earnings_date?: string | null;
}

export interface PiyasaGovdesi {
  readonly as_of?: string | null;
  readonly n?: number;
  readonly stale_n?: number;
  readonly retired_n?: number;
  readonly source?: { readonly bars?: number; readonly finviz_extra?: number; readonly finviz_reason?: string };
  readonly intraday?: {
    readonly tracked_n?: number;
    readonly measured_n?: number;
    /** '' = ölçüldü; dolu dize = neden ölçülemedi. */
    readonly reason?: string;
    readonly stale_tol_s?: number;
  };
  readonly regime?: Readonly<Record<string, unknown>>;
  readonly rows?: readonly PiyasaSatiri[];
}

/* --- /api/diagnostics · api.py:4342 ------------------------------------- */

export interface SaglayiciSatiri {
  readonly ad?: string;
  /** ÜÇ DEĞERLİ: true/false/null — null "bu süreçte hiç çağrı yapılmadı". */
  readonly ok?: boolean | null;
  readonly son_basari_ts?: string | null;
  readonly son_cagri_ts?: string | null;
  readonly hata_orani?: number | null;
  readonly cagri?: number | null;
  readonly hata?: number | null;
  readonly son_hata?: string | null;
  readonly son_durum?: number | string | null;
  readonly ek?: Readonly<Record<string, unknown>>;
  /** `_saglayicilar` istisna yakalarsa satır YALNIZ {ad, ok:null, olculemedi} olur. */
  readonly olculemedi?: string;
}

export interface IntradayKarari {
  readonly ts?: string;
  readonly ticker?: string;
  readonly action?: string;
  readonly reason?: string;
  readonly [k: string]: unknown;
}

export interface TeshisGovdesi {
  readonly onbellekten?: boolean;
  readonly hesaplama_ts?: string;
  readonly hud?: {
    readonly mode?: string;
    readonly broker?: string;
    readonly regime?: string | null;
    readonly exposure_budget_pct?: number | null;
    readonly explore_mode?: boolean;
    readonly equity?: number | null;
    readonly last_bar?: string | null;
    readonly heartbeat_age_s?: number | null;
    readonly halted?: boolean;
    readonly learn_halted?: boolean;
    readonly data_ok?: boolean | null;
    readonly stream_ok?: boolean | null;
    readonly stream_stale?: boolean | null;
    readonly stream_down_since?: string | null;
    readonly stream_last_event_ts?: string | null;
    readonly stream_last_error?: string | null;
  };
  readonly scheduler?: {
    readonly updated?: string | null;
    readonly last_tick?: string | null;
    readonly poll_seconds?: number | null;
    readonly cycles?: number | null;
  };
  readonly saglayicilar?: {
    readonly kapsam?: string;
    readonly beyan?: string;
    readonly saglayicilar?: readonly SaglayiciSatiri[];
  };
  readonly risk?: {
    readonly halted?: boolean;
    readonly learn_halted?: boolean;
    readonly blackout_radar?: unknown;
    readonly eylemsizlik?: {
      readonly exposure_budget_pct?: number | null;
      readonly birincil?: { readonly ad?: string; readonly aciklama?: string; readonly kanit?: string } | null;
      readonly nedenler?: readonly { readonly ad?: string; readonly aciklama?: string; readonly kanit?: string }[];
      readonly neden_yok_aciklama?: string | null;
      readonly verdict_counts?: Readonly<Record<string, number>>;
      readonly gate_reasons?: Readonly<Record<string, number>>;
      readonly olay_sayaci?: Readonly<Record<string, number>>;
      readonly olay_penceresi?: number;
      readonly halted?: boolean;
      readonly learn_halted?: boolean;
      readonly data_ok?: boolean | null;
    };
  };
  readonly hotstate?: Readonly<Record<string, unknown>> & { readonly ok?: boolean | null };
  readonly marketstream?: Readonly<Record<string, unknown>> & { readonly ok?: boolean | null };
  readonly barfeed?: Readonly<Record<string, unknown>> & { readonly ok?: boolean | null };
  readonly intraday?: {
    readonly ok?: boolean | null;
    readonly enabled?: boolean;
    readonly armed?: boolean;
    readonly mode?: string;
    readonly events_handled?: number;
    readonly decisions_written?: number;
    readonly watched?: number;
    readonly watched_planned?: number;
    readonly decisions_armed?: number;
    readonly decisions_planned?: number;
    readonly shadow_written?: number;
    readonly submitted_4b?: number;
    readonly skipped?: Readonly<Record<string, number>>;
    readonly last_decision_at?: string | null;
    readonly last_error?: string | null;
    readonly decisions?: {
      readonly total?: number;
      readonly fired?: number;
      readonly today?: number;
      readonly recent?: readonly IntradayKarari[];
    };
    readonly armed_plans?: number;
    /** intraday_shadow.summarize() — gölge emir GÖNDERMEZ, "tetik kesilseydi ne olurdu"yu tutar. */
    readonly shadow?: Readonly<Record<string, unknown>>;
    /**
     * scheduler `intraday_gap` kopyası. null = kanca BU SÜREÇTE HİÇ KOŞMADI — "boşluk yok"
     * DEĞİL (api.py:4491 şerhi). `durum` üç arıza hâli taşıyabilir: seans_disi / arsiv_yok /
     * takvim_yok; o üçünde blok yalnız {durum, gun, olculdu} olur (scheduler.py:840).
     */
    readonly akis_boslugu?: {
      readonly durum?: string;
      readonly gun?: string;
      readonly olculdu?: string;
      readonly bosluk_sayisi?: number;
      readonly yeni_uyari?: number;
      readonly gelen_bar?: number;
      readonly bozuk_satir?: number;
      readonly sembol?: number | string | null;
      readonly bosluklar?: readonly {
        readonly tur?: string;
        readonly sembol?: string | null;
        readonly baslangic?: string;
        readonly bitis?: string;
        readonly eksik_dk?: number;
        readonly beklenen?: number;
        readonly gelen?: number;
      }[];
      readonly esik?: Readonly<Record<string, unknown>>;
    } | null;
  };
  readonly dagitim?: Readonly<Record<string, unknown>> & { readonly olculemedi?: string };
  readonly coverage?: Readonly<Record<string, unknown>>;
  readonly pipeline?: {
    readonly refetch_attempts?: number;
    readonly refetch_max?: number;
    readonly last_refetch_session?: string | null;
    readonly earnings_attempts?: number;
    /** data_quality.json `tickers_failed` — bu seans veri alınamayan semboller. */
    readonly quarantine?: readonly string[];
    /** adapters.data.seam_report() — geçmişi artık yayın yapmayan kaynağa sabitli semboller. */
    readonly bar_source_seams?: {
      readonly tickers?: number;
      readonly by_pair?: Readonly<Record<string, number>>;
      readonly oldest?: string | null;
      readonly note?: string;
    };
    /** adapters.data.no_data_report() — "kaynak hatası" ile "sembol yok" AYRI sayılır. */
    readonly symbol_no_data?: {
      readonly tracked?: number;
      readonly confirmed_no_data?: readonly string[];
      readonly suspect?: readonly string[];
      readonly source_error_only?: readonly string[];
      readonly retired?: readonly string[];
      readonly confirm_streak?: number;
      readonly note?: string;
    };
    /** adapters.fmp.usage() — dosya yoksa BOŞ SÖZLÜK döner ("muhasebe yok"), null değil. */
    readonly fmp_usage?: {
      readonly date?: string;
      readonly calls?: number;
      readonly fails?: number;
      readonly blocked_at?: string | null;
    };
    /** adapters.finviz.status() — token son-4 MASKELİ. */
    readonly finviz?: {
      readonly elite_token?: string | null;
      readonly health?: Readonly<Record<string, unknown>>;
      readonly last?: {
        readonly date?: string | null;
        readonly source?: string | null;
        readonly n?: number | null;
        readonly reason?: string | null;
        readonly at?: string | null;
      };
    };
    /** store.io_stats() — p95 <20 örnekle ÖLÇÜLMEZ ve None kalır (sayı uydurulmaz). */
    readonly io?: {
      readonly writes?: number;
      readonly recent_n?: number;
      readonly p50_ms?: number | null;
      readonly p95_ms?: number | null;
      readonly max_ms?: number | null;
    };
  };
  readonly ledgers?: {
    readonly cf_open?: number;
    readonly cf_cap?: number;
    readonly cf_resolved?: number;
    readonly trades?: number;
  };
  readonly alarm_butcesi?: Readonly<Record<string, unknown>> & { readonly yas_s?: number };
}

/* --- /api/infra?taze=0|1 · api.py:6558 ------------------------------------
   ÜÇ KAT, ÜÇÜ DE AYRI (ucun kendi ayrımı):
     · `makine`     — kutunun kendisi (hostname, çekirdek, yük, CPU, bellek, disk, uptime)
     · `surec`      — BU API sürecinin kendisi. systemd'nin `meridian.service` satırıyla AYNI ŞEY
                      DEĞİL (o birim compose'u sarar) — api.py:6322 şerhi.
     · `bilesenler` — `deploy/` altındaki GERÇEK systemd birimleri
   Alan adları `meridian/api.py::_infra_makine/_infra_surec/_infra_bilesenler` OKUNARAK yazıldı;
   sözleşmenin çivisi `tests/test_pano_altyapi_v287.py`.

   PSUTIL YOK (`olcum_yolu`): ölçüm stdlib ile yapılıyor — `/proc` + `os` + `shutil.disk_usage` +
   `systemctl`. Sonuç: macOS'ta (`/proc` yok) CPU/bellek/uptime ölçülemez ve uç bunu None + neden
   ile SÖYLER. Pano bu yüzden yerelde bomboş görünür ve bu doğrudur — canlı A1 Linux'ta doludur.
   ------------------------------------------------------------------------ */

export interface InfraDisk {
  /** Ölçülen yol (`/`, depo kökü, `state/`). */
  readonly yol?: string;
  /** AYNI BÖLÜMÜ paylaşan Meridian yolları — üç satır aynı sayıyı üç kez basmasın diye tek satır. */
  readonly kapsayan_yollar?: readonly string[];
  readonly toplam_bayt?: number | null;
  readonly kullanilan_bayt?: number | null;
  readonly bos_bayt?: number | null;
  readonly kullanim_yuzde?: number | null;
  readonly olculemedi_neden?: string | null;
}

export interface InfraBellek {
  readonly toplam_bayt?: number | null;
  readonly kullanilan_bayt?: number | null;
  readonly kullanilabilir_bayt?: number | null;
  readonly kullanim_yuzde?: number | null;
  /** '/proc/meminfo' | 'sysconf' | null — sayının NEREDEN geldiği. */
  readonly kaynak?: string | null;
  readonly olculemedi_neden?: string | null;
}

export interface InfraMakine {
  readonly hostname?: string | null;
  readonly platform?: {
    readonly sistem?: string | null;
    readonly surum?: string | null;
    readonly makine?: string | null;
    readonly python?: string | null;
    readonly tam?: string | null;
  };
  readonly cekirdek_n?: number | null;
  readonly cekirdek_n_neden?: string | null;
  /** os.getloadavg() — Linux+macOS'ta var, Windows'ta yok. */
  readonly yuk?: { readonly "1dk"?: number; readonly "5dk"?: number; readonly "15dk"?: number } | null;
  readonly yuk_neden?: string | null;
  /** `/proc/stat` jiffy FARKI — ilk örnekte ve `/proc` yokken None + neden. */
  readonly cpu_yuzde?: number | null;
  readonly cpu_yuzde_neden?: string | null;
  readonly bellek?: InfraBellek;
  readonly disk?: readonly InfraDisk[];
  readonly uptime_s?: number | null;
  readonly uptime_s_neden?: string | null;
}

/** BU API SÜRECİ — makine ile systemd birimleri arasındaki üçüncü kat (api.py:6322). */
export interface InfraSurec {
  readonly pid?: number | null;
  readonly uptime_s?: number | null;
  readonly baslangic_ts?: string | null;
  readonly cpu_yuzde?: number | null;
  readonly cpu_yuzde_neden?: string | null;
  readonly rss_bayt?: number | null;
  readonly rss_bayt_neden?: string | null;
}

export interface InfraBilesen {
  readonly ad?: string;
  readonly dosya?: string;
  readonly tur?: string;
  /** `meridian-sprint@.service` — düz adla sorgu SAHTE `inactive` verir; uç durumu UYDURMAZ. */
  readonly sablon?: boolean;
  readonly birim_dosyasi?: string;
  /**
   * `LoadState == 'loaded'`. `false` = birim dosyası DEPODA var ama BU MAKİNEYE kurulmamış —
   * "kurulu ama durmuş" ile AYNI ŞEY DEĞİL ve tabloda ayrı gösterilir (api.py:6478 şerhi).
   */
  readonly kurulu?: boolean | null;
  readonly kurulu_neden?: string | null;
  readonly durum?: string | null;
  readonly durum_neden?: string | null;
  readonly alt_durum?: string | null;
  readonly alt_durum_neden?: string | null;
  readonly cpu_yuzde?: number | null;
  readonly cpu_yuzde_neden?: string | null;
  readonly rss_bayt?: number | null;
  readonly rss_bayt_neden?: string | null;
  readonly uptime_s?: number | null;
  readonly uptime_s_neden?: string | null;
  readonly restart_n?: number | null;
  readonly restart_n_neden?: string | null;
  readonly pid?: number | null;
  readonly pid_neden?: string | null;
  readonly aciklama?: string | null;
  readonly aciklama_neden?: string | null;
}

export interface InfraGovdesi {
  readonly hesaplama_ts?: string;
  readonly onbellekten?: boolean;
  /** Önbellekten servis edilirken zarfın yaşı; `uptime_s` alanları bununla TOPLANIR (api.py:6536). */
  readonly zarf_yasi_s?: number;
  readonly ttl_s?: number;
  readonly makine?: InfraMakine;
  readonly surec?: InfraSurec;
  /** null = `systemctl` yok / ölçülemedi. BOŞ LİSTE DEĞİL — ikisi ayrı gerçek. */
  readonly bilesenler?: readonly InfraBilesen[] | null;
  readonly bilesenler_olculemedi_neden?: string | null;
  readonly bilesen_kaynagi?: {
    readonly dizin?: string;
    readonly birim_n?: number;
    readonly systemctl_yolu?: string | null;
    readonly systemctl_yolu_neden?: string | null;
    readonly olculemedi_neden?: string | null;
  };
  /** 'stdlib (psutil YOK; /proc + os + shutil.disk_usage + systemctl)'. */
  readonly olcum_yolu?: string;
}
