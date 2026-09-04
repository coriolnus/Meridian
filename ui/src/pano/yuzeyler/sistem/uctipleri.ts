/* ============================================================================
   SİSTEM SAĞLIĞI — UÇ GÖVDE TİPLERİ
   ----------------------------------------------------------------------------
   HER ALAN İSTEĞE BAĞLI ve bu bilinçli (bkz. `pano/tipler.ts` başlığı): uçlar bir
   alanı ÖLÇEMEDİĞİNDE onu HİÇ YAZMIYOR. `x?: number` ile `x: number | null`
   arasındaki fark burada anlamlıdır — birincisi "alan yok, hiç ölçülmedi",
   ikincisi "ölçüldü, sonuç yok". Tipi zorunlu yapıp `0` varsaymak, ölçülmemiş bir
   CPU'yu boşta göstermek olurdu.

   TİPLER `meridian/api.py` OKUNARAK yazıldı, tahminle DEĞİL (brief'in açık şartı).
   Kaynak SEMBOL ADIYLA çapalanır (`api.py::api_infra`), satır numarasıyla DEĞİL:
   `dosya.py:NNN` çapası ilk düzenlemede bayatlar ve okuyucuyu yanlış yere gönderir
   (bu dosyada dört çapa tam olarak böyle çürümüştü — codelaw çapa yasası).
   ============================================================================ */

/* --- /api/alerts · `api.py::api_alerts` → `notify.inbox()` ---------------- */

export interface AlarmGrubu {
  readonly token?: string;
  readonly n?: number;
  readonly first_ts?: string | null;
  readonly last_ts?: string | null;
  readonly message?: string;
}

export interface AlarmGovdesi {
  /** TSK-137a: 10 sn mtime önbelleğinden mi (true) — ACK sonrası ≤10 sn bayat olabilir. */
  readonly onbellekten?: boolean;
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

/* --- /api/market · `api.py::api_market` → `marketview.build()` ----------- */

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

/* --- /api/diagnostics · `api.py::api_diagnostics` ------------------------ */

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
     * DEĞİL (`api.py::api_diagnostics` şerhi). `durum` üç arıza hâli taşıyabilir: seans_disi /
     * arsiv_yok / takvim_yok; o üçünde blok yalnız {durum, gun, olculdu} olur
     * (`scheduler.py::_intraday_gap_check`).
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

/* --- /api/infra?taze=0|1 · `api.py::api_infra` ----------------------------
   ÜÇ KAT, ÜÇÜ DE AYRI (ucun kendi ayrımı):
     · `makine`     — kutunun kendisi (hostname, çekirdek, yük, CPU, bellek, disk, uptime)
     · `surec`      — BU API sürecinin kendisi. systemd'nin `meridian.service` satırıyla AYNI ŞEY
                      DEĞİL (o birim compose'u sarar) — `api.py::_infra_surec` şerhi.
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

/** BU API SÜRECİ — makine ile systemd birimleri arasındaki üçüncü kat (`api.py::_infra_surec`). */
export interface InfraSurec {
  readonly pid?: number | null;
  readonly uptime_s?: number | null;
  readonly baslangic_ts?: string | null;
  readonly cpu_yuzde?: number | null;
  readonly cpu_yuzde_neden?: string | null;
  readonly rss_bayt?: number | null;
  readonly rss_bayt_neden?: string | null;
}

/**
 * BİR BİRİM SATIRININ TEK HÜKMÜ (`api.py::_infra_durum_sinifi`). Ham `ActiveState` yerine bu
 * okunur, çünkü `inactive` TEK BAŞINA bir hüküm değildir: `Type=oneshot` bir birim koşumlar
 * ARASINDA zaten `inactive`tir ve timer'ı aktifse bu SAĞLIKLI hâldir. Operatör 2026-08-25'te
 * tabloya bakıp "neden kurulu değil, inaktif ve ölçülemedi gözüküyor" diye sordu — üç ayrı dünya
 * tek kılıktaydı. Sınıflar operatörün İŞİNE karşılık gelir:
 *   · kosuyor                — `active`.
 *   · sirada_timer           — oneshot, tetikleyen timer AKTİF ölçüldü. Arıza değil.
 *   · ariza_yok_onfailure    — oneshot, `OnFailure` ile tetiklenir; `inactive` = hiçbir şey
 *                              arızalanmadı. Mümkün olan EN İYİ hâl.
 *   · tetikleyici_bozuk      — oneshot ama timer'ı ölü ölçüldü: birim HİÇ koşmuyor olabilir.
 *   · tetikleyici_olculemedi — tetikleyici bu istekte ölçülmedi; SAĞLIK İDDİA EDİLMİYOR.
 *   · tetikleyici_yok        — oneshot ama hiçbir bağ görülmedi; bağlanmayı bekliyor olabilir.
 *   · olu                    — oneshot OLDUĞU ölçülmemiş bir birim durmuş. DİKKAT ÇEKER.
 *   · arizali                — `failed`: koşmadı değil, KOŞTU VE DÜŞTÜ.
 *   · kurulmali              — kurulu değil ama `deploy/<host>/` altında var: operatör işi (sudo).
 *   · envanter_gurultusu     — kurulu değil ve kurulması BEKLENMİYOR (eski/genel kopya).
 *   · olculemedi             — şablon birim, bütçe aşımı, systemctl hatası.
 */
export type InfraDurumSinifi =
  | "kosuyor"
  | "sirada_timer"
  | "ariza_yok_onfailure"
  | "tetikleyici_bozuk"
  | "tetikleyici_olculemedi"
  | "tetikleyici_yok"
  | "olu"
  | "arizali"
  | "kurulmali"
  | "envanter_gurultusu"
  | "olculemedi";

export interface InfraBilesen {
  readonly ad?: string;
  readonly dosya?: string;
  readonly tur?: string;
  /** `meridian-sprint@.service` — düz adla sorgu SAHTE `inactive` verir; uç durumu UYDURMAZ. */
  readonly sablon?: boolean;
  readonly birim_dosyasi?: string;
  /**
   * `LoadState == 'loaded'`. `false` = birim dosyası DEPODA var ama BU MAKİNEYE kurulmamış —
   * "kurulu ama durmuş" ile AYNI ŞEY DEĞİL ve tabloda ayrı gösterilir
   * (`api.py::_infra_bilesenler` → `kurulu_neden` şerhi).
   */
  readonly kurulu?: boolean | null;
  readonly kurulu_neden?: string | null;
  /**
   * `deploy/<host>/` altında birim dosyası VAR mı — yani kurulu olması BEKLENİYOR mu.
   * Kaynağı systemd değil DİSK: systemd kurulmamış bir birim için yalnız `not-found` der,
   * "kurulmalı mıydı" sorusunun cevabı depodaki yoldadır (otorite `dagit.sh`).
   */
  readonly beklenen?: boolean | null;
  readonly beklenen_neden?: string | null;
  /** systemd `Type=` — `oneshot` ise duruş NORMAL olabilir. `.timer` birimlerinde YOKTUR. */
  readonly servis_turu?: string | null;
  readonly servis_turu_neden?: string | null;
  /** systemd `TriggeredBy` — bu birimi koşturan timer(lar). Boş liste "bağ görülmedi" demektir. */
  readonly tetikleyen_timerlar?: readonly string[];
  /** systemd `OnFailureOf` — bu birimi ARIZADA tetikleyen birim(ler). */
  readonly onfailure_kaynaklari?: readonly string[];
  /** Rozetin kaynağı. Ham `durum` yerine BU okunur (bkz. `InfraDurumSinifi`). */
  readonly durum_sinifi?: InfraDurumSinifi | null;
  readonly durum_sinifi_neden?: string | null;
  readonly durum?: string | null;
  readonly durum_neden?: string | null;
  readonly alt_durum?: string | null;
  readonly alt_durum_neden?: string | null;
  /**
   * İSTENEN DURUM — systemd `UnitFileState` (enabled/disabled/static/masked). `ActiveState` ile
   * AYNI ŞEY DEĞİL ve karıştırmak operatörün 2026-09-02 vakasının ta kendisidir: birim `disabled`
   * bırakılmıştı, dağıtım onu `enabled` yaptı — ikisi de `active` görünürken. Anahtarın "açık mı"
   * hükmü bu alan ile `durum`un BİRLİKTE okunmasından çıkar.
   * `null` = ölçülemedi (gerekçe kardeşinde) — `disabled` DEĞİL.
   */
  readonly etkin_durum?: string | null;
  readonly etkin_durum_neden?: string | null;
  /**
   * Bu satır panodan anahtarlanabilir mi (`api.py::BIRIM_ANAHTAR_BEYAZ`). Liste UÇTAN gelir ve
   * panoda İKİNCİ kez sabitlenmez: iki kopya ayrıştığı gün pano yetkisi olmayan bir satıra
   * anahtar çizer, tıklama reddedilir ve operatör panoyu bozuk sanar.
   * İKİ DEĞERLİ (alanın `null` hâli yok): liste bir ölçüm değil bir karardır, her zaman bilinir.
   */
  readonly anahtar_var?: boolean;
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

/**
 * TERS YÖN — makinede DURAN ama `deploy/` ağacında karşılığı OLMAYAN bir birim
 * (`api.py::_infra_beklenmedik`). `bilesenler` EKSİĞİ gösterir, bu satırlar FAZLAYI.
 *
 * `durum` systemd `UnitFileState`tir (enabled/disabled/static/masked), `ActiveState` DEĞİL:
 * birimin ŞU AN koşup koşmadığını SÖYLEMEZ. Ucun kendi beyanı `beklenmedik_olcum.durum_alani`
 * alanında gelir ve pano onu ekranda taşır — yoksa `disabled` gören operatör "duruyor" diye
 * okur ve ölçülmemiş bir hüküm kurar.
 */
export interface InfraBeklenmedikBirim {
  readonly birim?: string;
  /** null = STATE sütunu bu satırda gelmedi (gerekçe `durum_neden`) — "kapalı" DEĞİL. */
  readonly durum?: string | null;
  readonly durum_neden?: string | null;
}

/**
 * Bacağın ÖLÇÜM KÜNYESİ — kazanç kadar BEDEL de beyanlı (`api.py::_infra_beklenmedik`).
 * Sorgu DAR bir desenle sınırlıdır; desene uymayan birimler bu bacağa GÖRÜNMEZ ve bu körlük
 * ekranda söylenmeli (bedel yasası).
 */
export interface InfraBeklenmedikOlcum {
  readonly komut?: string;
  readonly durum_alani?: string;
  readonly kapsam_disi?: string;
  /** null = makinedeki birimler sayılamadı (gerekçe kardeşinde) — 0 DEĞİL. */
  readonly makinedeki_birim_n?: number | null;
  readonly makinedeki_birim_n_neden?: string | null;
  readonly repo_birim_n?: number;
}

export interface InfraGovdesi {
  readonly hesaplama_ts?: string;
  readonly onbellekten?: boolean;
  /** Önbellekten servis edilirken zarfın yaşı; `uptime_s` alanları bununla TOPLANIR
   *  (`api.py::_infra_yaslandir`). */
  readonly zarf_yasi_s?: number;
  readonly ttl_s?: number;
  readonly makine?: InfraMakine;
  readonly surec?: InfraSurec;
  /** null = `systemctl` yok / ölçülemedi. BOŞ LİSTE DEĞİL — ikisi ayrı gerçek. */
  readonly bilesenler?: readonly InfraBilesen[] | null;
  readonly bilesenler_olculemedi_neden?: string | null;
  /**
   * KEŞFİN İKİNCİ (TERS) BACAĞI. `null` = ölçülemedi (gerekçe `beklenmedik_birimler_neden`);
   * `[]` = ÖLÇÜLDÜ ve fazlalık yok. İkisi ASLA karışmaz — karıştıkları gün pano ölçülmemiş bir
   * TEMİZLİK beyan eder. Alanın hiç gelmemesi de üçüncü hâldir (eski gövde).
   */
  readonly beklenmedik_birimler?: readonly InfraBeklenmedikBirim[] | null;
  readonly beklenmedik_birimler_neden?: string | null;
  readonly beklenmedik_olcum?: InfraBeklenmedikOlcum;
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

/**
 * `POST /api/infra/birim/{ad}/istek` 200 gövdesi (`api.py::api_birim_istek`).
 *
 * `enabled`/`active` KOMUTUN DEĞİL MAKİNENİN cevabıdır: uç `enable --now` başarılı dönse bile
 * durumu `is-enabled` + `is-active` ÇIKTILARINDAN geri okur. Pano bu yüzden İYİMSER GÜNCELLEME
 * YAPMAZ — anahtarı isteğin hedefinden değil bu iki alandan çizer. İkisi de `null` olabilir
 * (ölçülemedi, gerekçe kardeşinde) ve o hâlde anahtar "bilinmiyor" der, kapalı DEĞİL.
 */
export interface BirimIstekSonucu {
  readonly birim?: string;
  /** İsteğin hedefi ('acik' | 'kapali') — SONUÇ DEĞİL, sonuç yukarıdaki iki alandadır. */
  readonly hedef?: string;
  /** Operatörün kendi eliyle koşabileceği biçimde komut — 'pano öyle diyor'un panzehiri. */
  readonly komut?: string;
  readonly komut_rc?: number | null;
  readonly enabled?: string | null;
  readonly enabled_neden?: string | null;
  readonly active?: string | null;
  readonly active_neden?: string | null;
}
