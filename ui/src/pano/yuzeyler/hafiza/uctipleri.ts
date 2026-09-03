/* ============================================================================
   HAFIZA YÜZEYİ — `/api/hindsight*` GÖVDE TİPLERİ
   ----------------------------------------------------------------------------
   Alan adları OKUNARAK yazıldı, tahminle DEĞİL. Kaynak SEMBOL ADIYLA çapalanır,
   satır numarasıyla DEĞİL (`dosya.py:NNN` çapası ilk düzenlemede bayatlar ve
   okuyucuyu yanlış yere gönderir — codelaw çapa yasası; `kapi/uctipleri.ts`
   emsali):

     · zarflar → `api.py::api_hindsight` · `::api_hindsight_liste` ·
       `::api_hindsight_detay` · `::api_hindsight_ozet` · `::_hafiza_zarf`
     · zarf tanıma kuralları (dizi/sürüm/kimlik/toplam adayları) →
       `api.py::_hafiza_dizi` · `::_hafiza_surum` · `::_hafiza_bank_kimligi` ·
       `::_hafiza_toplam`
     · sayfalama sınırları (istemci sayısı SUNUCUDA kırpılır) →
       `api.py::_hafiza_sayi` · `::_hafiza_sayfa_sorgusu` · `::_HAFIZA_UC_TAVANI`

   ÜÇ DURUM AYRI ÇİZİLİR (`kapi/uctipleri.ts` sözleşmesi birebir devralındı):
     `x?: T`        alan HİÇ gelmedi (eski gövde, kırpılmış yanıt)
     `x: T | null`  ölçüldü, sonuç yok
     `neden` dolu   ÖLÇÜLEMEDİ
   Üçünü tek kutuya koymak, ölçülmemiş bir hafızayı "boş" diye okutmak olurdu.
   Bugün canlıda bu ayrımın karşılığı GÖRÜNÜR: bu makinede Hindsight anahtarı yok,
   yani `bankalar: []` + dolu `bankalar_neden` gelir — ekran buna "banka yok"
   DEMEMEK zorunda.

   ---------------------------------------------------------------------------
   BU UCUN KENDİNE ÖZGÜ AYRIMI — VE BU DOSYANIN EN PAHALI CÜMLESİ
   ---------------------------------------------------------------------------
   İKİ KATMAN VAR VE İKİSİNİN GÜVENCESİ AYNI DEĞİL:

     (1) ZARF — `api.py` KURAR. Alan adları yukarıdaki sembollerden okundu; bu
         katman sözleşmedir ve değişirse depo içinde değişir.
     (2) GÖVDE — Hindsight'ın AYNEN GEÇEN cevabı (`stats` · `zaman_serisi` ·
         liste öğeleri · belge satırları · parçalar). Bu katmanı depo KURMAZ,
         yalnız TAŞIR. Şekli bir dış servisin sürümüne bağlıdır ve haber vermeden
         kayar.

   İkinci katman bu yüzden `HamGovde` (açık uçlu sözlük) olarak taşınır ve ekranda
   ANAHTARLARIYLA BİRLİKTE ham basılabilir durur. Buraya uydurma bir alan yazmak
   iki kez yalan söylerdi: ölçülmemiş bir adı ölçülmüş gibi gösterir, ve o ad
   kaydığı gün ekran SESSİZCE boş kalırdı (`api.py::_hafiza_surum` şerhindeki ders:
   `version` VARSAYILMIŞTI, canlıda alan `api_version`dı ve sürüm sonsuza dek boş
   kalacaktı — üstelik sessizce).

   ---------------------------------------------------------------------------
   ALAN ADLARININ ÜÇ KAYNAK SINIFI — HEPSİ AYNI GÜÇTE DEĞİL (TSK-108 Görev 2)
   ---------------------------------------------------------------------------
     (A) A1'DE ÖLÇÜLDÜ (2026-09-02, salt-okunur GET; kayıt:
         `tests/test_hafiza_yuzeyi_v375.py::BANKALAR_GOVDE`/`VERSION_GOVDE`/
         `AUDIT_GOVDE` ve turun canlı ölçüm dökümü). En güçlü sınıf.
     (B) UPSTREAM SÖZLEŞMESİNDEN TÜRETİLDİ — Hindsight `openapi.yaml`, tag
         v0.9.2 (commit çapası: `tests/test_hafiza_yuzeyi_v375.py` dosya başlığı;
         sha BURAYA KOPYALANMAZ — tek kaynak orası). Adlar uydurulmadı ama
         canlıda gerçekten öyle geldiği bu turda DOĞRULANMADI.
     (C) CP BİLEŞENİNİN OKUDUĞU AD — Hindsight Control Plane v0.9.2'nin kendi
         bileşenleri (`bank-stats-view.tsx::BankStats`, `data-view.tsx` tablosu,
         `memory-detail-panel.tsx`, `documents-view.tsx`). CP'nin okuduğu ad
         upstream şemasında ZORUNLU olmayabilir.

   Her alanın sınıfı satırında yazılıdır. Sınıfsız alan YOKTUR; yeni alan
   eklerken sınıfını yazmayan satır, bu dosyanın sözleşmesini deler.

   TİPLER ZORUNLU ALAN İLAN ETMEZ, BİLEREK: upstream'in `required` listesi bile
   bizim için bir güvence değildir — arada bir vekil var ve o vekil gövdeyi
   AYNEN geçiriyor, doğrulamıyor. Ekran her alanın yokluğunu ayrı çizer.
   ============================================================================ */

/**
 * Depo tarafından KURULMAYAN, yalnız TAŞINAN gövde: Hindsight ne döndürdüyse o.
 *
 * `unknown` değer tipi bilinçli — `string | number` yazmak, iç içe bir nesne
 * geldiğinde derleyiciyi susturup ekranı `[object Object]` bastırırdı. Çizen
 * taraf her değeri açıkça daraltmak ZORUNDA (`parcalar.tsx::HamDeger`).
 */
export type HamGovde = Readonly<Record<string, unknown>>;

/* ==========================================================================
   ZARF KALIPLARI — DÖRT TANE, VE DÖRDÜ DE BURADA
   --------------------------------------------------------------------------
   Vekil tarihî sebeplerle dört ayrı zarf şekli döndürüyor (gerekçe
   `api.py::_hafiza_zarf` şerhinde). Dördü tek dosyada tanımlı olmasaydı her
   görünüm kendi okumasını yazardı ve biri ötekinden sessizce ayrışırdı:

     1. `{ogeler, toplam, neden}`                  → `/liste`
     2. `{oge, neden, tarihce, tarihce_neden}`     → `/detay`
     3. `{stats, stats_neden, zaman_serisi, …}`    → `/ozet`
     4. `{govde, neden}`                           → CP görünüm uçlarının 19'u
   ========================================================================== */

/**
 * CP görünüm uçlarının ORTAK zarfı (`api.py::_hafiza_zarf`).
 *
 * `govde` DİZİ DEĞİL, upstream'in TAM cevabıdır: vekil diziyi zarftan SÖKMÜYOR,
 * çünkü sökmek `total`/`limit`/`offset`i düşürürdü ve ekran "50 belgeden 20'si"
 * diyemezdi. Sayfalama gerçeği burada yaşıyor.
 */
export interface HafizaZarfi<G = HamGovde> {
  /** `null` = ölçüm denendi ve düştü; `neden` o zaman DOLUdur. */
  readonly govde?: G | null;
  /** Dolu = ÖLÇÜLEMEDİ. Boş gövde + boş neden = ölçüldü, sonuç yok. */
  readonly neden?: string | null;
}

/**
 * Upstream'in SAYFALI liste gövdesi — sınıf (B), dört listeleyen uçta aynı
 * (`ListDocumentsResponse` · `ListChunksResponse` · `ListMemoryUnitsResponse` …).
 * `total`/`limit`/`offset` upstream şemasında zorunlu; burada yine de isteğe
 * bağlı, çünkü aradaki vekil doğrulama YAPMAZ (dosya başlığı).
 */
export interface SayfaliGovde<S = HamGovde> {
  readonly items?: readonly S[];
  readonly total?: number;
  readonly limit?: number;
  readonly offset?: number;
}

/* --- SAĞLIK (`api.py::api_hindsight`, `saglik` bloğu) --------------------- */

/**
 * Hindsight AYAKTA MI — banka okunabilirliğinden BAĞIMSIZ ölçülür.
 *
 * Ayrılığın gerekçesi ucun kendisinde yazılı ve tipte de görünür durmalı: anahtar
 * dosyası bu makinede olmayabilir ama servisin ayakta olup olmadığı hâlâ
 * ölçülebilir. İkisini tek alana indirmek, tek arızayı iki körlüğe çevirirdi.
 */
export interface HafizaSagligi {
  /** Anahtarsız sağlık ucu okunabildi mi. `false` iken `neden` DOLUdur. */
  readonly erisilebilir?: boolean;
  /**
   * Sürüm dizgesi — sınıf (A) (`api_version`, A1'de ölçüldü). `null` = uç okundu
   * ama sürüm alanı TANINMADI; bu bir şema sürüklenmesi işaretidir, "sürümsüz
   * servis" değil (`api.py::_hafiza_surum`).
   */
  readonly surum?: string | null;
  /** Sağlık ve sürüm bacaklarının gerekçeleri birleştirilmiş hâli. `null` = ikisi de sağlam. */
  readonly neden?: string | null;
}

/* --- BANKA (`api.py::api_hindsight`, `bankalar` listesi) ------------------ */

/**
 * BİR BANKA — ve ucun bu satırda GERÇEKTEN taşıdığı tek kimlik alanı.
 *
 * BEDEL BEYANI (bedel yasası), ÖLÇÜLDÜ 2026-09-02: banka LİSTESİ gövdesi
 * `fact_count` · `last_write_at` · `last_document_at` · `created_at` · `mission`
 * gibi alanlar taşıyor ve CP'nin banka seçicisi (`bank-selector.tsx`) tam da
 * onları çiziyor (satır sayacı çubuğu + son yazım zamanı). `api.py::api_hindsight`
 * listeden yalnız KİMLİĞİ alıp (`::_hafiza_bank_kimligi`) gerisini DÜŞÜRÜYOR ve
 * bankanın sayılarını ayrı bir `stats` çağrısından getiriyor.
 *
 * SONUÇ, EKRANDA YAZILI: bizim banka seçicimiz CP'ninkinin sayaç çubuğunu
 * ÇİZEMEZ. Seçici satırında görünen sayı `stats` geldiyse ondan gelir; gelmediyse
 * sayı UYDURULMAZ, boşluk nedeniyle birlikte çizilir.
 */
export interface HafizaBankasi {
  /** Banka kimliği — sınıf (A). Upstream'e giden yolda kaçırılarak kullanılır. */
  readonly bank_id?: string;
  /** Bankanın sayaç gövdesi, AYNEN GEÇER. `null` = ölçüm denendi, gövde gelmedi. */
  readonly stats?: BankaSayaclari | null;
  /** Bu bankanın sayaçları neden okunamadı. Kardeş gerekçe — boş gövdeyle ayrı hâl. */
  readonly stats_neden?: string | null;
}

/* --- KOTA VE OPERASYON (`api.py::api_hindsight`) -------------------------- */

/**
 * Banka başına model çağrısı sayaçları. Şekli sınıf (B).
 * Sözlüğün ANAHTARI banka kimliğidir; sabit bir banka listesi burada YAZILMAZ —
 * yeni banka doğduğu gün ekranda kendiliğinden görünsün diye (F9 sınıfı ayrışma).
 *
 * OKURU GERİ GELDİ (TSK-108 Görev 3) — VE BU DA YAZILI DURMAK ZORUNDA.
 * Görev 2'den sonra bu blok ve kardeşi `HafizaOperasyonKutusu` HİÇBİR ekran
 * tarafından okunmuyordu: eski sayfanın iki sayaç kutusu yeni bilgi mimarisinde
 * Yapılandırma görünümüne taşınmıştı ve o görünüm o turda çizilmemişti — yani
 * `api.py::api_hindsight` banka başına iki upstream bacağını 30 sn'de bir
 * okuyucusuz koşuyordu (inceleme M-2).
 *
 * Artık okuyucusu var ve tek: `Yapilandirma.tsx::SayacKutulari`. Gövde ORAYA
 * ÇEKİLMİYOR, kabuğun zaten yaptığı okumadan paylaşılıyor
 * (`gorunumler.ts::GorunumOzellikleri.toplu` şerhi) — ikinci bir çağrı aynı
 * gerçeğin iki kopyası olurdu ve ikisi farklı pencerelerle gelirdi.
 */
export interface HafizaKotaKutusu {
  readonly llm_stats?: HamGovde | null;
  readonly neden?: string | null;
}

/**
 * Banka başına denetim kaydı sayaçları — bu yüzeyin "ne işlendi" bacağı.
 *
 * A1'DE GÖRÜLEN ALANLAR (sınıf (A), ipucu): `bank_id` · `period` · `trunc` ·
 * `start` · `buckets`. Görüldüğü anda `buckets` BOŞTU, yani kova öğesinin şekli
 * ölçülemedi ve buraya yazılmadı — boş bir dizi gördüğümüzde onun içindeki
 * nesnenin alanlarını tahmin etmek, tam da bu dosyanın yasakladığı şey.
 */
export interface HafizaOperasyonKutusu {
  readonly audit_stats?: HamGovde | null;
  readonly neden?: string | null;
}

/* --- TOPLU GÖVDE (`api.py::api_hindsight`) — PANONUN YOKLADIĞI TEK UÇ ----- */

export interface HafizaGovdesi {
  readonly saglik?: HafizaSagligi;
  readonly bankalar?: readonly HafizaBankasi[];
  /**
   * Boş liste ile ÖLÇÜLEMEDİ'yi ayıran kardeş gerekçe (v287 `<alan>_neden` idiomu).
   * Bu alan bu yüzeyin EN ÇOK İŞ GÖREN alanı: bu makinede anahtar dosyası yok, yani
   * normal hâl `bankalar: []` + DOLU `bankalar_neden`dir. Boş listeyi tek başına
   * çizen bir ekran her gün "hafızada banka yok" diye yalan söylerdi.
   */
  readonly bankalar_neden?: string | null;
  /** Banka kimliği → kota kutusu. */
  readonly kota?: Readonly<Record<string, HafizaKotaKutusu>>;
  /** Banka kimliği → operasyon kutusu. */
  readonly operasyon?: Readonly<Record<string, HafizaOperasyonKutusu>>;
}

/* ==========================================================================
   ANA SAYFA — `api.py::api_hindsight_ozet` (CP `home-view`in vekili)
   ========================================================================== */

/**
 * BİR BANKANIN SAYAÇLARI — CP'nin `MemoryStoreCard`ının okuduğu gövde.
 *
 * Alan adları sınıf (B)+(C): upstream `BankStatsResponse` şeması ve CP'nin
 * `bank-stats-view.tsx::BankStats` arayüzü BİRLİKTE okundu; ikisi bir yerde
 * AYRILIYOR ve ayrım burada yazılı durmak zorunda:
 *
 *   · CP `nodes_by_fact_type`ı `{world?, experience?, opinion?}` diye DARALTIYOR.
 *   · Upstream şeması onu AÇIK bir sayı sözlüğü ilan ediyor (`additionalProperties:
 *     integer`) ve kendi örneğinde `fact`/`observation`/`preference` anahtarlarını
 *     kullanıyor — yani CP'nin üç adı bir ALT KÜMEDİR, sözleşme değil.
 *
 * Bu yüzden burada sözlükler AÇIK bırakıldı ve ekran anahtarları TELDEN alıyor.
 * CP'nin daralttığı yeri biz de daraltsaydık, `preference` adlı bir tür doğduğu
 * gün ekran onu SESSİZCE düşürürdü — ve toplam ile parçaların toplamı tutmazdı.
 */
export interface BankaSayaclari extends HamGovde {
  readonly bank_id?: unknown;
  /** Kayıt sayısı — CP "memories" diye çiziyor. */
  readonly total_nodes?: unknown;
  readonly total_links?: unknown;
  readonly total_documents?: unknown;
  /** Türe göre kayıt dağılımı. Anahtarları AÇIK (yukarıdaki şerh). */
  readonly nodes_by_fact_type?: unknown;
  /** Bağ türüne göre dağılım. Anahtarları AÇIK. */
  readonly links_by_link_type?: unknown;
  readonly total_observations?: unknown;
  readonly pending_operations?: unknown;
  readonly failed_operations?: unknown;
  readonly operations_by_status?: unknown;
  /** Son birleştirme damgası. `null` = hiç birleştirme yapılmamış (upstream `nullable`). */
  readonly last_consolidated_at?: unknown;
  /** Son yazım/düzenleme/birleştirme damgası. `null` = boş banka (CP'nin kendi şerhi). */
  readonly last_memory_write_at?: unknown;
  readonly pending_consolidation?: unknown;
  readonly failed_consolidation?: unknown;
}

/**
 * ZAMAN SERİSİ KOVASI — sınıf (B) (`MemoryTimeseriesBucket`).
 * `time` upstream'de ZORUNLU; üç sayaç `default: 0` taşıyor, yani gelmeyebilir.
 */
export interface SeriKovasi extends HamGovde {
  readonly time?: unknown;
  readonly world?: unknown;
  readonly experience?: unknown;
  readonly observation?: unknown;
}

/**
 * INGEST ZAMAN SERİSİ — sınıf (B) (`MemoriesTimeseriesResponse`).
 * `trunc` kovanın çözünürlüğüdür (minute/hour/day) ve ekranda etiket biçimini
 * belirler; UYDURULMAZ — gelmezse damga ham basılır.
 */
export interface ZamanSerisi extends HamGovde {
  readonly bank_id?: unknown;
  readonly period?: unknown;
  readonly trunc?: unknown;
  readonly time_field?: unknown;
  readonly buckets?: readonly SeriKovasi[];
}

/**
 * `/ozet` ZARFI — İKİ BACAK, İKİ GEREKÇE.
 *
 * Bacaklar birbirini DÜŞÜRMEZ (`api.py::api_hindsight_ozet`): sayaçlar okunamazsa
 * zaman serisi hâlâ çizilir. Tek `neden` alanına indirmek, tek arızayı iki
 * körlüğe çevirirdi.
 */
export interface HafizaOzeti {
  readonly stats?: BankaSayaclari | null;
  readonly stats_neden?: string | null;
  readonly zaman_serisi?: ZamanSerisi | null;
  readonly zaman_serisi_neden?: string | null;
}

/* ==========================================================================
   BELLEKLER — `api.py::api_hindsight_liste` + `::api_hindsight_detay`
   ========================================================================== */

/**
 * BİR HAFIZA KAYDI — alanların TAMAMI A1'DE ÖLÇÜLDÜ (düzeltme turu 1).
 *
 * KIYAS SATIR SATIR YAPILDI (canlı ölçüm, `memories/list?limit=1`, 2026-09-02 ~15:05).
 * Canlı öğe YİRMİ İKİ anahtar taşıyor ve hepsi aşağıda var. İlk yazımda beşi
 * EKSİKTİ (`consolidated_at` · `consolidation_failed_at` · `proof_count` ·
 * `source_memory_ids` · `updated_at`) ve biri UYDURULMUŞ bir addı — ayrıntısı
 * aşağıda. Eksik alanlar ekrandan tümüyle düşmüyordu (`parcalar.tsx::HamSatirlar`
 * gövdenin tamamını basıyor) ama tipte olmayan alan ADIYLA okunamaz, yani hiçbir
 * bölüm onları kendi biçiminde gösteremezdi.
 *
 * ÖLÇÜLEN AD `source_memory_ids`, `source_memories` DEĞİL. İlk yazım üst yüzeyin
 * detay panelinden okuduğu adı (sınıf (C)) buraya taşımıştı ve o ad canlı liste
 * gövdesinde YOKTUR: "Kaynak kayıtlar" bölümü canlıda hiç açılmazdı — üstelik
 * SESSİZCE, çünkü koşul `Array.isArray(undefined)` ile susardı. Bu, bu dosyanın
 * başlığındaki `_hafiza_surum` dersinin birebir tekrarıydı (`version` varsayılmış,
 * canlıda `api_version`dı). İKİ AD DA okunuyor artık: ölçülen ad birincil, üst
 * yüzeyin adı yedek — `fact_type`/`type` deseninin aynısı.
 *
 * `type` ÖLÇÜMDE GÖRÜLMEDİ ve yine de duruyor: canlı gövde `fact_type` veriyor,
 * upstream'in KENDİ `ListMemoryUnitsResponse` örneği ise `type` (openapi). İkisi
 * de okunuyor; ölçülen ad birincil.
 *
 * `entities` DİZGE OLABİLİR: upstream örneği virgüllü tek bir dizge veriyor
 * (`"Alice (PERSON), Google (ORGANIZATION)"`) ve üst yüzey de onu ", " ile
 * bölüyor. Dizi hâli de görülüyor — o yüzden `unknown`.
 *
 * Tipler yine de hiçbir alanı ZORUNLU kılmıyor: arada bir vekil var ve o vekil
 * gövdeyi aynen geçiriyor, doğrulamıyor (dosya başlığı).
 */
export interface HafizaKaydi extends HamGovde {
  /* --- canlı ölçümde görülen yirmi iki alan, hepsi sınıf (A) --- */
  readonly id?: unknown;
  /** Kaydın kendisi — insanın okuduğu metin. */
  readonly text?: unknown;
  /** Kaydın nereden geldiği (ölçümde: içe aktarım künyesi). */
  readonly context?: unknown;
  /** `mentioned_at` ile AYNI ŞEY DEĞİLDİR — ikisi de canlıda ayrı ayrı geliyor. */
  readonly date?: unknown;
  /** Ölçümde görülen değer: `world`. Türün BİRİNCİL adı. */
  readonly fact_type?: unknown;
  readonly document_id?: unknown;
  readonly mentioned_at?: unknown;
  readonly occurred_start?: unknown;
  readonly occurred_end?: unknown;
  readonly entities?: unknown;
  readonly tags?: unknown;
  /** `valid` / `invalidated` (`api.py::_HAFIZA_KAYIT_DURUMU`). */
  readonly state?: unknown;
  readonly invalidation_reason?: unknown;
  readonly invalidated_at?: unknown;
  readonly edited_at?: unknown;
  readonly updated_at?: unknown;
  /** Bu kaydın türetildiği kaynak kayıtların KİMLİKLERİ — nesneler değil, kimlikler. */
  readonly source_memory_ids?: unknown;
  readonly chunk_id?: unknown;
  readonly metadata?: unknown;
  readonly consolidated_at?: unknown;
  readonly consolidation_failed_at?: unknown;
  /** Gözlemin kaç kayda dayandığı — üst yüzeyin gözlem tablosundaki "kaynak" sütunu. */
  readonly proof_count?: unknown;

  /* --- ölçümde GÖRÜLMEYEN, yedek olarak okunan iki ad --- */
  /** Sınıf (B) — upstream örneğindeki tür adı. `fact_type` yoksa buna bakılır. */
  readonly type?: unknown;
  /** Sınıf (C) — üst yüzeyin detay panelinin okuduğu ad (kimlik değil, NESNE listesi).
   *  Canlı LİSTE gövdesinde yok; tek-kayıt gövdesinde olabilir, ölçülmedi. */
  readonly source_memories?: unknown;
}

/**
 * SAYFA GÖVDESİ — ve `toplam`ın NEDEN VAR OLDUĞU.
 *
 * DÜZELTİLMİŞ BEYAN (2026-09-02): bu şerh önce "toplam sayı YOKTUR, ekran
 * sayfa sayısı çizemez" diyordu ve o cümle ARTIK YANLIŞ — `api.py`nin düzeltme
 * turu `toplam`ı ek alan olarak ekledi (`::_hafiza_toplam`). Bayat bir beyan,
 * olmayan bir beyandan kötüdür: ekran neyi çizebileceğini şerhten öğreniyor.
 *
 * `toplam` UYDURULMAZ: upstream `total` alanını vermediyse, tipi kaydıysa ya da
 * zarf tanınmadıysa `null` gelir — `0` DEĞİL. `0` panoda "hiç kayıt yok" diye
 * okunurdu ve bu, ölçülmemiş bir boşluğu ölçülmüş göstermek olurdu.
 */
export interface HafizaListesi {
  readonly ogeler?: readonly HafizaKaydi[];
  /** `null` = kaç kayıt olduğu ÖLÇÜLEMEDİ; sıfır anlamına GELMEZ. */
  readonly toplam?: number | null;
  /** Dolu = ÖLÇÜLEMEDİ. Boş `ogeler` + boş `neden` = ölçüldü, bu sayfada kayıt yok. */
  readonly neden?: string | null;
}

/**
 * TEK KAYIT + TARİHÇESİ — `api.py::api_hindsight_detay`, İKİ BACAK.
 *
 * `oge: null` ucun BİLİNÇLİ tercihidir ve tipte korunur: bulunamayan kayıtta boş
 * sözlük dönmek "kayıt var ama içi boş" yalanı olurdu.
 *
 * TARİHÇE AYRI BACAKTIR VE BU BİR ÖLÇÜM SONUCUDUR: upstream `get_memory`
 * gövdesindeki `history` alanı "deprecated, her zaman boş liste" diye
 * belgeleniyor (Görev 1 ölçümü), yani kaydın İÇİNDEN tarihçe okumak sessizce
 * boş tarihçe gösterirdi. Vekil bu yüzden ayrı uca gidiyor.
 *
 * TARİHÇENİN ŞEKLİ ÖLÇÜLEMEDİ: upstream'de bu yanıtın şeması literal `{}` —
 * ne alan ne örnek (Görev 1, I-2). `HamGovde` olarak taşınır ve ekran onu
 * anahtarlarıyla ham basar; alan adı UYDURULMAZ.
 */
export interface HafizaDetayi {
  readonly oge?: HafizaKaydi | null;
  readonly neden?: string | null;
  readonly tarihce?: HamGovde | null;
  readonly tarihce_neden?: string | null;
}

/* ==========================================================================
   BELGELER — `api.py::api_hindsight_belgeler` + `::api_hindsight_belge_parcalari`
   ========================================================================== */

/**
 * BİR BELGE SATIRI — alan adlarının TAMAMI A1'DE ÖLÇÜLDÜ (sınıf (A),
 * 2026-09-02: `documents?limit=2` → `items[0]` anahtarları). Bu, bu dosyadaki
 * en güçlü kayıt: hem canlı hem upstream örneği aynı adları veriyor.
 *
 * BURADA OLMAYAN ŞEYİN ADI: `original_text`. Belgenin TAM METNİ bu uçtan
 * gelmiyor — upstream onu tek-belge ucunda veriyor ve o ucun vekili YOK
 * (Görev 1 kapsamı). Ekran bunu söyler; "belge boş" demez.
 */
export interface HafizaBelgesi extends HamGovde {
  readonly id?: unknown;
  readonly bank_id?: unknown;
  readonly created_at?: unknown;
  readonly updated_at?: unknown;
  /** Belgeden çıkarılan kayıt sayısı — CP tablosunun son sütunu. */
  readonly memory_unit_count?: unknown;
  /** Karakter uzunluğu; CP bunu bayta çevirip "boyut" diye gösteriyor. */
  readonly text_length?: unknown;
  readonly tags?: unknown;
  /** Serbest biçimli künye — kaynağa göre değişir, şeması YOKTUR. */
  readonly document_metadata?: unknown;
  /** İçe aktarımın parametreleri (`context`, `event_date`, `metadata`). */
  readonly retain_params?: unknown;
  readonly content_hash?: unknown;
}

/**
 * BELGE PARÇASI — sınıf (B), `ChunkResponse`; beş alanı da upstream'de ZORUNLU.
 * CP'nin çekmecesi (`documents-view.tsx::ChunkRow`) `chunk_index`, `chunk_text`
 * ve `chunk_id`yi okuyor.
 */
export interface BelgeParcasi extends HamGovde {
  readonly chunk_id?: unknown;
  readonly document_id?: unknown;
  readonly bank_id?: unknown;
  readonly chunk_index?: unknown;
  readonly chunk_text?: unknown;
  readonly created_at?: unknown;
}

/* ==========================================================================
   TSK-108 GÖREV 3 — KALAN BEŞ GÖRÜNÜMÜN GÖVDE TİPLERİ
   --------------------------------------------------------------------------
   Aynı sözleşme, aynı üç kaynak sınıfı (dosya başlığı). BU BLOKTA SINIF (C)
   AĞIR BASIYOR ve bu bir zayıflıktır, saklanmıyor: yukarıdaki üç görünümün
   alanları canlıda ölçülmüştü; buradaki yedi yüzeyin çoğu (bilgi ağacı, zihin
   modeli, işlem, denetim, model çağrısı, yapılandırma) canlıda ÖLÇÜLMEDİ —
   ölçüm dökümünde yalnız zarfları var (`.superpowers/sdd/2026-09-02-hafiza-cpui/
   canli-olcum-2026-09-02.md`). Ekran bu yüzden her alanın yokluğunu AYRI çizer
   ve gövdenin tamamını ham basar: yanlış bir ad SESSİZ kalmaz.
   ========================================================================== */

/* ==========================================================================
   BİLGİ TABANI — `api.py::api_hindsight_bilgi_tabani` · `::api_hindsight_bilgi_arama`
                  · `::api_hindsight_bilgi_sayfasi`
   ========================================================================== */

/**
 * AĞAÇ DÜĞÜMÜ — CP `knowledge-base-view.tsx::TreeNode`in okuduğu alanlar (sınıf (C)).
 *
 * `kind` KLASÖR İLE SAYFAYI AYIRIR ve ekran bu ayrımı UYDURMAZ: alan gelmezse
 * düğüm "türü bildirilmedi" diye çizilir, klasör VARSAYILMAZ. Klasör varsaymak
 * bir sayfayı açılamaz bir kutuya çevirirdi.
 */
export interface BilgiDugumu extends HamGovde {
  readonly id?: unknown;
  readonly name?: unknown;
  /** `"folder"` | `"page"` — sınıf (C). Başka bir değer gelirse ekran onu yazar. */
  readonly kind?: unknown;
  readonly children?: readonly BilgiDugumu[];
  /** Sayfanın kendi kapsamında yeni kayıt var mı — üç değerli (`null` = bilinmiyor). */
  readonly is_stale?: unknown;
  /** Zihin modelinin tetikleyicisi; "sonraki tazeleme" BURADAN türer. */
  readonly trigger?: unknown;
  /** Son güncelleme damgası (CP `node.timestamp`). */
  readonly timestamp?: unknown;
  readonly tags?: unknown;
  /** Sayfa bir zihin modeli tarafından mı yönetiliyor (CP `managed` rozeti). */
  readonly managed?: unknown;
  /** Sayfayı besleyen zihin modelinin kimliği. */
  readonly mental_model_id?: unknown;
}

/** `/knowledge-base/tree` gövdesi — canlıda ölçülen TEK anahtar `roots` (sınıf (A)). */
export interface BilgiAgaci extends HamGovde {
  readonly roots?: readonly BilgiDugumu[];
}

/**
 * TEK SAYFA — CP sayfa görüntüleyicisinin okuduğu alanlar (sınıf (C)).
 * `description` sayfanın KAYNAK SORGUSUdur (CP onu tırnak içinde çiziyor),
 * `body` sentezlenmiş metindir.
 */
export interface BilgiSayfasi extends HamGovde {
  readonly id?: unknown;
  readonly name?: unknown;
  readonly tags?: unknown;
  readonly description?: unknown;
  readonly body?: unknown;
  readonly timestamp?: unknown;
}

/** Arama vuruşu — CP `r.id/name/snippet/score` okuyor (sınıf (C)). */
export interface BilgiVurusu extends HamGovde {
  readonly id?: unknown;
  readonly name?: unknown;
  readonly snippet?: unknown;
  readonly score?: unknown;
}

/** `/knowledge-base/search` gövdesi — vekilin şerhi `{results, total}` diyor (sınıf (B)). */
export interface BilgiAramaGovdesi extends HamGovde {
  readonly results?: readonly BilgiVurusu[];
  readonly total?: unknown;
}

/* ==========================================================================
   ZİHİN MODELLERİ — `::api_hindsight_zihin_modelleri` · `::api_hindsight_zihin_modeli`
                     · `::api_hindsight_zihin_modeli_tarihce`
   ========================================================================== */

/**
 * TETİKLEYİCİ — ve bu bloğun NEDEN AYRI TİPİ VAR.
 *
 * Görev 2 "sonraki tazeleme"yi Ana Sayfa'da çizemedi ve gerekçesini yazdı: o
 * değer bir BANKA alanı değil, bir ZİHİN MODELİNİN tetikleyicisidir. Bu tur o
 * tetikleyiciyi ÖLÇTÜ (CP `mental-models-view.tsx::MentalModel.trigger`) ve
 * değerin evi burasıdır. Alanlar sınıf (C).
 */
export interface ZihinTetigi extends HamGovde {
  readonly mode?: unknown;
  readonly refresh_after_consolidation?: unknown;
  readonly refresh_cron?: unknown;
  readonly min_refresh_interval_seconds?: unknown;
  readonly fact_types?: unknown;
  readonly tags_match?: unknown;
  readonly include_chunks?: unknown;
  readonly recall_max_tokens?: unknown;
  readonly keep_trace?: unknown;
}

/** BİR ZİHİN MODELİ — CP `MentalModel` arayüzü (sınıf (C)); canlıda liste BOŞ geldi,
 *  yani öğe şekli ÖLÇÜLEMEDİ ve bu bilerek yazılı duruyor. */
export interface ZihinModeli extends HamGovde {
  readonly id?: unknown;
  readonly bank_id?: unknown;
  readonly name?: unknown;
  /** Modelin kapsamını belirleyen sorgu. */
  readonly source_query?: unknown;
  /** Sentezlenmiş metin — yalnız `detail=content|full` istendiğinde dolu gelir. */
  readonly content?: unknown;
  readonly tags?: unknown;
  readonly max_tokens?: unknown;
  readonly trigger?: ZihinTetigi;
  readonly last_refreshed_at?: unknown;
  /** Modelin OKUDUĞU en yeni kaydın damgası — tazelik bununla kıyaslanır. */
  readonly last_memory_seen_at?: unknown;
  /** Üç değerli: `true`/`false`/bilinmiyor. */
  readonly is_stale?: unknown;
  readonly created_at?: unknown;
  /** Son tazelemenin ham yanıtı (kaynaklar, iz). Şekli ölçülmedi. */
  readonly reflect_response?: unknown;
}

/* ==========================================================================
   VARLIKLAR — `::api_hindsight_varliklar` · `::api_hindsight_varlik_graf`
   ========================================================================== */

/** BİR VARLIK — alanların TAMAMI A1'DE ÖLÇÜLDÜ (sınıf (A), `entities?limit=2`). */
export interface VarlikKaydi extends HamGovde {
  readonly id?: unknown;
  readonly canonical_name?: unknown;
  readonly mention_count?: unknown;
  readonly first_seen?: unknown;
  readonly last_seen?: unknown;
  readonly metadata?: unknown;
}

/**
 * TEK VARLIĞIN KÜNYESİ — `api.py::api_hindsight_varlik`, zarf `{govde, neden}`.
 *
 * LİSTE SATIRININ TIPKISI DEĞİL, VE FARK ÖLÇÜLDÜ (12-A, upstream
 * `EntityDetailResponse` şeması): tek-varlık gövdesi liste satırının altı alanına
 * EK olarak bir `observations` dizisi taşıyor. `VarlikKaydi`yi burada yeniden
 * kullanmak o alanı tipten silmezdi ama GÖRÜNMEZ kılardı — ekranın ham blokta
 * bastığı şeyin tipte adı olmaması, "ölçtük ama yazmadık" hâlidir.
 *
 * ÜST YÜZEY BU GÖVDENİN TAMAMINI ÇİZMİYOR (`entities-view.tsx` künye paneli
 * yalnız ad + anılma + ilk görülme + kimlik basıyor); bizim panelimiz son görülme
 * ile kalan alanları da gösteriyor ve farkı ekranda yazıyor.
 */
export interface VarlikKunyesi extends HamGovde {
  readonly id?: unknown;
  readonly canonical_name?: unknown;
  readonly mention_count?: unknown;
  readonly first_seen?: unknown;
  readonly last_seen?: unknown;
  readonly metadata?: unknown;
  /** Üst yüzeyin künye panelinde ÇİZİLMEYEN alan; şemada zorunlu bir dizi. */
  readonly observations?: unknown;
}

/**
 * GRAF DÜĞÜMÜ/KENARI — CP `graph-data.ts::convertHindsightGraphData`ın okuduğu
 * biçim (sınıf (C)): gövde `{nodes:[{data:{…}}], edges:[{data:{…}}]}` şeklinde
 * İÇ İÇE bir `data` sarmalı taşıyor (Cytoscape mirası). Sarmalı düzleştirmiyoruz:
 * düzleştirmek, ölçülmemiş bir biçimi ölçülmüş gibi göstermek olurdu.
 */
export interface GrafDugumu extends HamGovde {
  readonly data?: {
    readonly id?: unknown;
    readonly label?: unknown;
    readonly color?: unknown;
    /* ---- BELLEK GRAFININ DÜĞÜM ALANLARI — A1'de ölçüldü (18:15 UTC eki) ----
       `graph` ucunun düğümleri `entities/graph`ınkinden ZENGİN geliyor: metin,
       bağlam, tarih ve varlık listesi düğümün kendisinde de var. KAYIT TÜRÜ
       BURADA YOK ve bu ölçülmüş bir eksikliktir — tür `table_rows` satırında
       yaşıyor (aşağıya bkz.). */
    readonly text?: unknown;
    readonly context?: unknown;
    readonly date?: unknown;
    readonly entities?: unknown;
  };
}

export interface GrafKenari extends HamGovde {
  readonly data?: {
    readonly source?: unknown;
    readonly target?: unknown;
    readonly weight?: unknown;
    readonly similarity?: unknown;
    readonly linkType?: unknown;
    readonly entityName?: unknown;
    /** Son birlikte geçiş damgası — CP ısı ölçeğini bundan kuruyor. */
    readonly lastCooccurred?: unknown;
    /** Kesikli çizgi işareti — CP tür gelmediğinde bundan zamansal bağ türetiyor. */
    readonly lineStyle?: unknown;
    readonly color?: unknown;
    readonly id?: unknown;
  };
}

/**
 * BELLEK GRAFININ TABLO SATIRI — düğümün KÜNYESİ.
 *
 * Anahtarların TAMAMI A1'de ölçüldü (2026-09-02 19:35 UTC eki). Buradaki tek
 * kritik alan kayıt türüdür: düğüm gövdesinde YOK, satırda VAR ve kimlikle
 * eşleşiyor. CP kümeyi düğümün tür alanından kuruyor; bizim ölçtüğümüz gövdede o
 * alan olmadığı için küme bu eşlemeyle kurulur (ölçülmüş sapma, çizim tarafında
 * da yazılı).
 */
export interface GrafSatiri extends HamGovde {
  readonly id?: unknown;
  readonly text?: unknown;
  readonly context?: unknown;
  readonly date?: unknown;
  readonly entities?: unknown;
  readonly fact_type?: unknown;
  readonly tags?: unknown;
  readonly document_id?: unknown;
  readonly chunk_id?: unknown;
  readonly occurred_start?: unknown;
  readonly occurred_end?: unknown;
  readonly mentioned_at?: unknown;
  readonly created_at?: unknown;
  readonly proof_count?: unknown;
}

/**
 * BELLEK GRAFI — `api.py::api_hindsight_bellek_graf` zarfı, AYNEN.
 *
 * Varlık grafından İKİ farkı var ve ikisi de ölçüldü: (1) tablo satırları,
 * (2) toplam sayacın adı tek ve `total_units`. Aynı tipi iki uç için kullanmak,
 * bir uçta olmayan bir alanı öteki uçta varmış gibi okutmak olurdu.
 */
export interface BellekGrafi extends HamGovde {
  readonly nodes?: readonly GrafDugumu[];
  readonly edges?: readonly GrafKenari[];
  readonly table_rows?: readonly GrafSatiri[];
  /** Bankadaki TOPLAM kayıt sayısı (kırpma öncesi). */
  readonly total_units?: unknown;
  /** Sunucunun UYGULADIĞI tavan — istemcinin sorduğu değil (vekil kırpar). */
  readonly limit?: unknown;
}

/* --------------------------------------------------------------------------
   ÇİZİLEBİLİR GRAF — telin İKİ biçiminin ORTAK karşılığı
   ---------------------------------------------------------------------------
   Tel iki ayrı zarf gönderiyor (bellek grafı ve varlık grafı) ve ikisi de aynı
   görsele akıyor. Çizim bileşeni HİÇBİRİNİ tanımaz: yalnız bu düz biçimi tanır.
   Ayrım bilinçli — çizim tel biçimini tanısaydı üçüncü bir graf ucu doğduğu gün
   çizim kodu da dallanırdı, ve iki dal sessizce ayrışırdı.
   -------------------------------------------------------------------------- */

export interface TakimyildiziDugumu {
  readonly kimlik: string;
  readonly etiket: string;
  /** Küme anahtarı — `null` = bu düğümün kümesi ÖLÇÜLEMEDİ, halkada kalır. */
  readonly kume: string | null;
  /** Üzerine gelince açılan künyenin kaynağı — `null` = künye yok. */
  readonly kunye: HamGovde | null;
}

export interface TakimyildiziBagi {
  readonly kaynak: string;
  readonly hedef: string;
  /** Bağ türü — `null` = bildirilmedi; çizim onu anlamsal sayar (CP kuralı). */
  readonly tur: string | null;
  readonly agirlik: number | null;
}

export interface TakimyildiziVerisi {
  readonly dugumler: readonly TakimyildiziDugumu[];
  readonly baglar: readonly TakimyildiziBagi[];
}

export interface VarlikGrafi extends HamGovde {
  readonly nodes?: readonly GrafDugumu[];
  readonly edges?: readonly GrafKenari[];
  /* ---- KIRPMANIN ÜÇ SAYISI — sınıf (A), A1'de ölçüldü (16:25 UTC eki) ----
     `entities/graph` zarfı `edges·limit·nodes·total_edges·total_entities` taşıyor.
     ÜÇÜ DE OKUNMAK ZORUNDA, çünkü bu uç SUNUCUDA kırpılıyor: vekil limiti kendi
     tavanına (200) indiriyor (`api.py::_hafiza_sayi` + `HAFIZA_LISTE_TAVANI`) ve
     canlı bankada isim sayısı bunun kat kat üstünde. Yalnız dönen diziyi sayan bir
     ekran, eksik bir grafiği TAM gösterirdi — kırpma zincirinin (`parcalar.tsx::
     KirpmaZinciri`) var olma sebebi budur. Sayılar telde duruyordu; okunmadıkları
     sürece yokluk ekranın körlüğüydü. */
  /** Bankadaki TOPLAM isim sayısı (kırpma öncesi). */
  readonly total_entities?: unknown;
  /** Bankadaki TOPLAM bağ sayısı (kırpma öncesi). */
  readonly total_edges?: unknown;
  /** Sunucunun UYGULADIĞI tavan — istemcinin sorduğu değil (vekil kırpar). */
  readonly limit?: unknown;
}

/* ==========================================================================
   RECALL — `::api_hindsight_recall` (POST, beyaz listeli gövde)
   ========================================================================== */

/** Bir recall vuruşunun skorları — CP tam duyarlıkta basıyor, YUVARLAMIYOR
 *  (`search-debug-view.tsx::fmtScore`: yuvarlamak anlamlı farkı gizler). */
export interface RecallSkorlari extends HamGovde {
  readonly final?: unknown;
  readonly reranker?: unknown;
  readonly semantic?: unknown;
  readonly keyword?: unknown;
}

/** BİR RECALL SONUCU — CP sonuç kartının okuduğu alanlar (sınıf (C)). */
export interface RecallSonucu extends HamGovde {
  readonly id?: unknown;
  readonly text?: unknown;
  readonly type?: unknown;
  readonly context?: unknown;
  readonly occurred_start?: unknown;
  readonly scores?: RecallSkorlari;
}

/** Recall'ın gözlem bölümü — `proof_count` ve `relevance` CP'de ayrı çiziliyor. */
export interface RecallGozlemi extends HamGovde {
  readonly id?: unknown;
  readonly text?: unknown;
  readonly proof_count?: unknown;
  readonly relevance?: unknown;
}

/**
 * RECALL GÖVDESİ — `{results, observations, entities, chunks, trace}` (sınıf (C)).
 * `entities`/`chunks` bu panoda HİÇ dolmaz ve nedeni ekranda yazılı: onları
 * isteyen `include` alanı vekilin beyaz listesinde YOKTUR
 * (`api.py::_HAFIZA_RECALL_ALANLARI`).
 */
export interface RecallGovdesi extends HamGovde {
  readonly results?: readonly RecallSonucu[];
  readonly observations?: readonly RecallGozlemi[];
  readonly entities?: unknown;
  readonly chunks?: unknown;
  readonly trace?: unknown;
}

/** POST `/api/hindsight/recall` zarfı — `{govde, neden}` (`api.py::_hafiza_recall`). */
export interface RecallZarfi {
  readonly govde?: RecallGovdesi | null;
  readonly neden?: string | null;
}

/* ==========================================================================
   GÖZLEMLER — `::api_hindsight_gozlem_kapsamlari`
   ========================================================================== */

/** BİR GÖZLEM KAPSAMI — CP `observation-scope-filter.tsx::ObservationScope`
 *  (sınıf (C)): bir ETİKET KÜMESİ ve o kümedeki gözlem sayısı. BOŞ etiket kümesi
 *  bir eksiklik değil, "küresel kapsam"tır — ekran ikisini ayırır. */
export interface GozlemKapsami extends HamGovde {
  readonly tags?: unknown;
  readonly count?: unknown;
}

export interface GozlemKapsamlari extends HamGovde {
  readonly scopes?: readonly GozlemKapsami[];
  readonly items?: readonly GozlemKapsami[];
}

/* ==========================================================================
   İŞLEMLER — `::api_hindsight_islemler`
   ========================================================================== */

/** İşlemin son ilerleme fotoğrafı — CP `OperationProgress` (sınıf (C)). */
export interface IslemIlerlemesi extends HamGovde {
  readonly stage?: unknown;
  readonly processed?: unknown;
  readonly total?: unknown;
  /** Son kalp atışı damgası. */
  readonly at?: unknown;
}

/** BİR İŞLEM — CP `bank-operations-view.tsx::Operation` (sınıf (C)); `filename`
 *  A1'de ölçüldü (sınıf (A)) ve CP'nin arayüzünde YOK — daraltmadık. */
export interface IslemKaydi extends HamGovde {
  readonly id?: unknown;
  readonly task_type?: unknown;
  readonly items_count?: unknown;
  readonly document_id?: unknown;
  readonly filename?: unknown;
  readonly created_at?: unknown;
  readonly updated_at?: unknown;
  readonly status?: unknown;
  readonly error_message?: unknown;
  readonly next_retry_at?: unknown;
  readonly progress?: IslemIlerlemesi;
}

/**
 * İŞLEM ZARFI — VE BU DOSYADAKİ EN PAHALI ÖLÇÜM.
 *
 * Bu uç `SayfaliGovde` DEĞİLDİR: diziyi `items` altında değil `operations`
 * altında veriyor (A1'de ölçüldü, sınıf (A): `operations?limit=100` →
 * `bank_id, total, limit, offset, operations`). `SayfaliGovde<IslemKaydi>`
 * yazsaydık ekran her zaman "işlem yok" derdi — üstelik SESSİZCE, çünkü
 * `items` gerçekten `undefined` olurdu ve hiçbir gerekçe doğmazdı.
 *
 * `items` YİNE DE OKUNUR: vekil zarfı aynen geçiriyor ve upstream bir gün adı
 * tekilleştirirse tek ada bağlı ekran sessizce boşalırdı (`_hafiza_surum` dersi).
 */
export interface IslemGovdesi extends HamGovde {
  readonly operations?: readonly IslemKaydi[];
  readonly items?: readonly IslemKaydi[];
  readonly total?: unknown;
  readonly limit?: unknown;
  readonly offset?: unknown;
  readonly bank_id?: unknown;
}

/* ==========================================================================
   DENETİM VE MODEL ÇAĞRILARI — `::api_hindsight_denetim` · `::api_hindsight_llm_istekleri`
                                 (+ iki istatistik ucu)
   ========================================================================== */

/** BİR DENETİM SATIRI — CP `audit-logs-view.tsx` tablosu ve detay kutusu (sınıf (C)). */
export interface DenetimKaydi extends HamGovde {
  readonly id?: unknown;
  readonly action?: unknown;
  readonly transport?: unknown;
  readonly started_at?: unknown;
  readonly ended_at?: unknown;
  readonly request?: unknown;
  readonly response?: unknown;
  readonly metadata?: unknown;
}

/** BİR MODEL ÇAĞRISI — CP `llm-requests-view.tsx::LLMRequestEntry` (sınıf (C)). */
export interface ModelCagrisi extends HamGovde {
  readonly id?: unknown;
  readonly operation?: unknown;
  readonly scope?: unknown;
  readonly status?: unknown;
  readonly provider?: unknown;
  readonly model?: unknown;
  readonly started_at?: unknown;
  readonly duration_ms?: unknown;
  readonly input_tokens?: unknown;
  readonly output_tokens?: unknown;
  readonly cached_tokens?: unknown;
  readonly total_tokens?: unknown;
  readonly span_id?: unknown;
  readonly parent_span_id?: unknown;
  readonly error?: unknown;
}

/** İSTATİSTİK KOVASI — iki istatistik ucu da `{time, total}` veriyor; model
 *  çağrısı ucu ayrıca `tokens{input,output,cached,total}` taşıyor (sınıf (C)). */
export interface IstatistikKovasi extends HamGovde {
  readonly time?: unknown;
  readonly total?: unknown;
  readonly tokens?: {
    readonly input?: unknown;
    readonly output?: unknown;
    readonly cached?: unknown;
    readonly total?: unknown;
  };
}

/** İSTATİSTİK GÖVDESİ — `trunc` kovanın çözünürlüğüdür ve UYDURULMAZ; gelmezse
 *  eksen etiketi ham damgadan çizilir. */
export interface IstatistikGovdesi extends HamGovde {
  readonly buckets?: readonly IstatistikKovasi[];
  readonly trunc?: unknown;
  readonly period?: unknown;
  readonly bank_id?: unknown;
}

/* ==========================================================================
   YAPILANDIRMA — `::api_hindsight_yapilandirma` (GET /config)
   ========================================================================== */

/**
 * BANKA YAPILANDIRMASI — İKİ KATMAN, VE CP İKİSİNİ AYIRIYOR.
 *
 * CP `bank-config-view.tsx` ÇÖZÜLMÜŞ değeri (`config`) ile BANKAYA ÖZGÜ
 * geçersiz kılmaları (`overrides`) ayrı okuyor ve gerekçesini yazıyor: çözülmüş
 * değer "devralınan true" ile "elle true yapılmış"ı ayırt edemez. Zarfın bu iki
 * alanı GERÇEKTEN taşıyıp taşımadığı BU TURDA ÖLÇÜLMEDİ (canlı ölçüm dökümünde
 * `/config` yok) — ikisi de isteğe bağlı ve ekran hangisinin gelmediğini yazar.
 */
export interface YapilandirmaGovdesi extends HamGovde {
  readonly config?: HamGovde | null;
  readonly overrides?: HamGovde | null;
  /** Bellek savunması politikası — CP `memory-defense-section.tsx::readPolicy`
   *  bunu `config.memory_defense` altında arıyor; kök düzeyde de okunur. */
  readonly memory_defense?: unknown;
}

/* ==========================================================================
   WEBHOOK LİSTESİ — `::api_hindsight_webhooklar` (GET /webhooks)  · TSK-109
   --------------------------------------------------------------------------
   BU ZARF KARDEŞLERİNDEN FARKLI, VE FARK ÖLÇÜLDÜ: `WebhookListResponse`in TEK
   alanı (ve tek `required`i) `items`tır — `total`/`limit`/`offset` YOKTUR. Yani
   burada `SayfaliGovde` KULLANILAMAZ: onu kullanmak, ekranın gelmeyecek bir
   `total`ı beklemesi ve sayfalama şeridini sonsuza dek "toplam gelmedi" diye
   çizmesi olurdu. Upstream bu uçta sorgu parametresi de tanımıyor
   (`api.py::api_hindsight_webhooklar` M şerhi) — sayfalama diye bir şey yok.

   `secret` BU TİPTE YOKTUR ÇÜNKÜ ZARFTA DA YOKTUR (Rol-1 hükmü 2026-09-03,
   TSK-109 düzeltme turu 1). Alan upstream'in liste yanıtında vardır ama vekil onu
   SÜZER (`api.py::_webhook_sirrini_suz`) ve yerine `secret_tanimli` yazar; gerekçe
   Yasa 6 — bu panonun webhook YAZMA yolu yok, yani imzalama sırrının tarayıcıda
   hiçbir okuyucusu yok. Tipe yine de yazmak, gelmeyecek bir alanı VAR gibi
   göstermek olurdu. `secret_tanimli` da ÜÇ HÂLLİDİR: upstream alanı hiç
   göndermediyse vekil bu anahtarı da yazmaz — `undefined` "ölçülemedi" demektir,
   `false` "ölçüldü, sır tanımsız".
   ========================================================================== */

/** WEBHOOK HTTP TESLİMAT AYARI — upstream `WebhookHttpConfig` (sınıf (B)).
 *  `method` şemada `default: POST` taşır; VARSAYILANI EKRAN UYDURMAZ — alan
 *  gelmediyse "gelmedi" yazılır (CP burada sessizce "POST" basıyor). */
export interface WebhookHttpAyari extends HamGovde {
  readonly method?: unknown;
  readonly timeout_seconds?: unknown;
  readonly headers?: unknown;
  readonly params?: unknown;
}

/** BİR WEBHOOK — upstream `WebhookResponse` (sınıf (B)); CP `webhooks-view.tsx`
 *  tablosu bu adların beşini okuyor: `url`·`http_config.method`·`event_types`·
 *  `enabled`·`created_at` (sınıf (C), aynı adlar). */
export interface WebhookKaydi extends HamGovde {
  readonly id?: unknown;
  readonly bank_id?: unknown;
  readonly url?: unknown;
  /** SIRRIN KENDİSİ DEĞİL, VARLIĞININ BEYANI — vekilin yazdığı alan
   *  (`api.py::_webhook_sirrini_suz`). Üç hâl: yok = upstream alanı hiç
   *  göndermedi · `false` = sır tanımsız · `true` = tanımlı. Ekran bugün hiçbirini
   *  ÇİZMİYOR; tipte durması, zarfın gerçeğini kaydeder. */
  readonly secret_tanimli?: boolean;
  readonly event_types?: unknown;
  readonly enabled?: unknown;
  readonly http_config?: unknown;
  readonly created_at?: unknown;
  readonly updated_at?: unknown;
}

/** WEBHOOK LİSTESİ — `SayfaliGovde` DEĞİL (yukarıdaki blok şerhi). */
export interface WebhookListesi extends HamGovde {
  readonly items?: readonly WebhookKaydi[];
}
