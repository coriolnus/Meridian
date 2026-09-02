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
 * OKURU YOK — VE BU YAZILI DURMAK ZORUNDA (düzeltme turu 1, inceleme M-2).
 * Bu blok ve kardeşi `HafizaOperasyonKutusu` bugün HİÇBİR ekran tarafından
 * okunmuyor: eski sayfanın iki sayaç kutusu yeni bilgi mimarisinde Yapılandırma
 * görünümüne taşındı ve o görünüm bu turda çizilmedi. Tipler duruyor çünkü ZARF
 * gerçekten bu alanları taşıyor (tipten silmek zarfı yanlış anlatırdı) — ama
 * maliyet ödenmeye devam ediyor: `api.py::api_hindsight` banka başına bu iki
 * bacağı 30 sn'lik yoklamada okuyor ve sonucu kimse okumuyor. Bacakları
 * durdurmak `meridian/api.py` değişikliğidir ve bu turun dosya sahipliği
 * dışındadır; kayıt Görev 3 brief'ine düşürüldü.
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
