/* ============================================================================
   KAPI YÜZEYİ — `/api/gateway` GÖVDE TİPLERİ
   ----------------------------------------------------------------------------
   Alan adları `meridian/api.py::api_gateway` OKUNARAK yazıldı, tahminle DEĞİL.
   Kaynak SEMBOL ADIYLA çapalanır (`api.py::api_gateway`, `api.py::_kapi_fazlar`),
   satır numarasıyla DEĞİL: `dosya.py:NNN` çapası ilk düzenlemede bayatlar ve
   okuyucuyu yanlış yere gönderir (codelaw çapa yasası; `sistem/uctipleri.ts`te
   dört çapa tam olarak böyle çürümüştü).

   HER ALAN İSTEĞE BAĞLI, `sistem/uctipleri.ts` ile aynı gerekçeyle: `x?: T` "alan
   hiç gelmedi" (eski gövde, kırpılmış yanıt), `x: T | null` "ölçüldü, sonuç yok".
   İkisini tek kutuya koymak, ölçülmemiş bir kapıyı "kapalı" diye okutmak olurdu.

   BU UCUN KENDİNE ÖZGÜ ÜÇ AYRIMI — üçü de tipte GÖRÜNÜR durmak zorunda, çünkü
   üçü de ekranda AYRI çizilmeli:
     1. `rotalar: []` + `rotalar_neden: null`  = ölçüldü, kapıda rota yok
        `rotalar: []` + `rotalar_neden: "…"`   = ÖLÇÜLEMEDİ (admin API okunamadı)
     2. `metrikler.atlanan_satir`: `null` = prometheus hiç okunamadı ·
        `0` = okundu, bozuk satır yok · `n` = okundu, n satır ayrıştırılamadı.
        `null`ı `0` saymak "bozuk satır yok" yalanıdır (`api.py::api_gateway` şerhi).
     3. `fazlar` ÜÇ HÂLLİ: `canli` · `bekliyor` · `olculemedi`. Admin okunamazken
        "bekliyor" yazmak bir ÖLÇÜM İDDİASIDIR (`api.py::_kapi_fazlar`).
   ============================================================================ */

/* --- ROTA (`api.py::_kapi_rota_cevir`) ----------------------------------- */

/**
 * Zincirin BİR halkası — LLM sağlayıcı örneği.
 *
 * SIRA SUNUCUDA KURULUR (`_kapi_rota_cevir` `zincir.sort`, öncelik desc) ve UI onu
 * YENİDEN SIRALAMAZ: aynı gerçeğin ikinci kopyası sessizce ayrışır (tek-kaynak yasası).
 * Dizinin sırası ZATEN denenme sırasıdır; ekran onu okur, kurmaz.
 */
export interface KapiZincirHalkasi {
  /** APISIX `instances[].name`. */
  readonly ad?: string | null;
  /** `instances[].options.model` — hangi model çağrılıyor. */
  readonly model?: string | null;
  /** `instances[].priority`. `null` = öncelik yazılmamış; sunucu böyle halkayı EN SONA koyar. */
  readonly oncelik?: number | null;
  /**
   * `auth.header.Authorization`ın PANO HÂLİ (`api.py::_kapi_auth_referansi`).
   * `$env://…` referansı AYNEN geçer — referans sır DEĞİLDİR ve "hangi env okunuyor"
   * sorusu panodan cevaplanabilmeli. `$env://` ile BAŞLAMAYAN bir değer etcd'ye kazara
   * yazılmış GERÇEK bir anahtar demektir: uç onu göstermez ama SESSİZ de kalmaz —
   * alanda "(gizlendi: …)" beyanı gelir. `null` = rotada auth başlığı hiç yok.
   */
  readonly auth_referansi?: string | null;
}

export interface KapiRotasi {
  readonly id?: string | null;
  readonly uri?: string | null;
  readonly zincir?: readonly KapiZincirHalkasi[];
  /** `ai-proxy-multi.fallback_strategy` — hangi cevapta bir sonraki halkaya geçilir. */
  readonly fallback_tetikleri?: readonly string[];
  /** `proxy-rewrite.headers.remove` — istemciden gelip upstream'e GEÇMEYEN başlıklar. */
  readonly temizlenen_basliklar?: readonly string[];
}

/* --- SAĞLIK · METRİK · FAZ ------------------------------------------------ */

export interface KapiSagligi {
  /** Admin API (9180) okunabildi mi. `false` iken `neden` DOLUdur. */
  readonly admin_api?: boolean;
  /** Prometheus (9091) okunabildi mi — admin bacağından BAĞIMSIZ ölçülür. */
  readonly prometheus?: boolean;
  /** İki bacağın gerekçeleri `; ` ile birleştirilmiş hâli. `null` = ikisi de sağlam. */
  readonly neden?: string | null;
}

export interface KapiRotaMetrigi {
  readonly istek_n?: number;
  /** Durum kodu → sayaç. Anahtarlar prometheus etiketinden gelir (`"200"`, `"429"` …). */
  readonly durum_kirilimi?: Readonly<Record<string, number>>;
}

export interface KapiMetrikleri {
  /** Prometheus METNİ okunabildi mi. `false` iken `rota_basina` BOŞ ama bu bir ölçüm DEĞİL. */
  readonly kaynak_ok?: boolean;
  readonly rota_basina?: Readonly<Record<string, KapiRotaMetrigi>>;
  /**
   * `apisix_http_status` diye BAŞLAYIP rota/kod/sayı üçlüsünü veremeyen satır sayısı.
   * ÜÇ HÂL: `null` ölçülemedi · `0` okundu ve bozuk yok · `n` okundu, n satır düştü.
   * `# HELP`/`# TYPE`/başka metrikler bozuk DEĞİL, İLGİSİZdir — bu sayaca girmezler.
   */
  readonly atlanan_satir?: number | null;
  readonly neden?: string | null;
}

/** Bir fazın ÜÇ HÂLİ (`api.py::_kapi_fazlar`). Dördüncü bir dize gelirse ekran onu HAM basar. */
export type KapiFazHali = "canli" | "bekliyor" | "olculemedi";

/**
 * Faz anahtarları UCUN listesinden gelir (`api.py::_KAPI_FAZ_IMZALARI`) ve UI onları SAYMAZ:
 * dört faz burada sabit yazılsaydı beşincisi doğduğu gün ekranda hiç görünmezdi (F9 sınıfı
 * ayrışma). Değer tipi `string`tir — `KapiFazHali` bir DARALTMA hedefidir, bir vaat değil:
 * telden tanımayan bir hâl gelirse ekran onu "tanınmayan" işaretiyle ham basar (v280 disiplini).
 */
export type KapiFazlari = Readonly<Record<string, string>>;

/** Faz → o hükmün HANGİ plugin imzasından türediği. Rozet sihir olmasın diye taşınır. */
export type KapiFazKaniti = Readonly<Record<string, string>>;

/* --- KAYNAK KÜNYESİ ------------------------------------------------------ */

/**
 * Ucun OKUDUĞU yerler + repo kaynağı. Bu blok EKRANA BASILIR ve UI'da sabit yazılmaz:
 * portlar ya da repo yolu bir gün değişirse pano eski adresi göstermeye devam ederdi
 * (tek-kaynak yasası — aynı gerçeğin ikinci kopyası sessizce ayrışır).
 */
export interface KapiKaynagi {
  readonly admin_url?: string;
  readonly prometheus_url?: string;
  /** Konfigürasyonun TEK KAYNAĞI (`deploy/apisix/routes.yaml`). Pano onu SUNMAZ, ADRESİNİ söyler. */
  readonly rota_kaynagi_repo?: string;
  readonly zaman_asimi_s?: number;
}

/* --- GÖVDE --------------------------------------------------------------- */

export interface KapiGovdesi {
  readonly hesaplama_ts?: string;
  readonly saglik?: KapiSagligi;
  readonly rotalar?: readonly KapiRotasi[];
  /** Boş liste ile ÖLÇÜLEMEDİ'yi ayıran kardeş gerekçe (v287 `<alan>_neden` idiomu). */
  readonly rotalar_neden?: string | null;
  readonly metrikler?: KapiMetrikleri;
  readonly fazlar?: KapiFazlari;
  readonly fazlar_kanit?: KapiFazKaniti;
  /**
   * BEDEL BEYANI (bedel yasası): faz türetimi YALNIZ `/apisix/admin/routes` okur; rota DIŞINDA
   * yaşayan artefaktlar (consumer_groups, ssl) bu yüzeyden görünmez. Kazanç ölçülüp bedel
   * ölçülmezse körlüğün belirtisi hiçbir şeydir — bu yüzden metin EKRANA BASILIR.
   */
  readonly fazlar_kapsam_neden?: string;
  readonly kaynak?: KapiKaynagi;
}
