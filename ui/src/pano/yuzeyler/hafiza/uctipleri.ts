/* ============================================================================
   HAFIZA YÜZEYİ — `/api/hindsight` GÖVDE TİPLERİ
   ----------------------------------------------------------------------------
   Alan adları OKUNARAK yazıldı, tahminle DEĞİL. Kaynak SEMBOL ADIYLA çapalanır,
   satır numarasıyla DEĞİL (`dosya.py:NNN` çapası ilk düzenlemede bayatlar ve
   okuyucuyu yanlış yere gönderir — codelaw çapa yasası; `kapi/uctipleri.ts`
   emsali):

     · zarf (üç ucun döndürdüğü sözlükler) →
         `api.py::api_hindsight` · `api.py::api_hindsight_liste` ·
         `api.py::api_hindsight_detay`
     · zarf tanıma kuralları (dizi/sürüm/kimlik alanı adayları) →
         `api.py::_hafiza_dizi` · `api.py::_hafiza_surum` · `api.py::_hafiza_bank_kimligi`
     · sayfalama sınırları (istemci sayısı SUNUCUDA kırpılır) →
         `api.py::_hafiza_sayi`

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
     (2) GÖVDE — Hindsight'ın AYNEN GEÇEN cevabı (`stats` · `llm_stats` ·
         `audit_stats` · liste öğeleri · detay öğesi). Bu katmanı depo KURMAZ,
         yalnız TAŞIR. Şekli bir dış servisin sürümüne bağlıdır ve haber vermeden
         kayar.

   İkinci katman bu yüzden `HamGovde` (açık uçlu sözlük) olarak taşınır ve ekranda
   ANAHTARLARIYLA BİRLİKTE ham basılır. Buraya `memory_count: number` gibi uydurma
   bir alan yazmak iki kez yalan söylerdi: ölçülmemiş bir adı ölçülmüş gibi
   gösterir, ve o ad kaydığı gün ekran SESSİZCE boş kalırdı (`api.py::_hafiza_surum`
   şerhindeki ders: `version` VARSAYILMIŞTI, canlıda alan `api_version`dı ve sürüm
   sonsuza dek boş kalacaktı — üstelik sessizce).

   ÖLÇÜLEN GÖVDE ALANLARI AŞAĞIDA `ipucu` OLARAK DURUR, SÖZLEŞME OLARAK DEĞİL.
   Kaynak: `tests/test_hafiza_yuzeyi_v375.py` fixture'ları — `BANKALAR_GOVDE` ·
   `VERSION_GOVDE`/`SURUM_OLCULEN` · `STATS_GOVDE` · `LLM_GOVDE` · `AUDIT_GOVDE`
   (A1'de ölçüldü 2026-09-02).

   ÇAPA NEDEN BURASI, VE NEDEN DEĞİŞTİRİLDİ (düzeltme turu 1, inceleme bulgusu B-4):
   önce ölçümün ham dökümüne (`.superpowers/…` altındaki bir metin dosyası) atıf
   veriliyordu. O dizin VERSİYONLANMIYOR (`.gitignore`) — yani çapa cloud klonunda ve
   başka her checkout'ta ÖLÜdür: okuyucu gösterilen yere bakar ve hiçbir şey bulamaz.
   Kalıcı kaynaktan verilen atıf, KALICI bir hedefe gitmek zorundadır. Fixture'lar hem
   versiyonlu hem de çivilerle canlı tutuluyor: bayatladıklarında test kırmızıya döner,
   bir metin dosyası ise sessizce çürür.

   İKİ SINIFI KARIŞTIRMA — fixture'ların hepsi AYNI GÜÇTE DEĞİL:
     · `BANKALAR_GOVDE` ve `VERSION_GOVDE` A1'de GERÇEKTEN ölçülmüş gövdelerdir.
     · `STATS_GOVDE` · `LLM_GOVDE` · `AUDIT_GOVDE` zarfın AYNEN GEÇTİĞİNİ sınamak için
       yazılmış TEMSİLİ değerlerdir (`memory_count`/`request_count`/`event_count` adları
       ÖLÇÜLMEDİ, seçildi). Bir çivinin yeşili, o adların canlıda var olduğunu KANITLAMAZ.
   Bu yüzden `stats` ve `llm_stats` için aşağıda ipucu alan bile yazılmadı; ekran onları
   anahtarlarıyla ham basar.

   Ölçüm kayıtları KIRPILMIŞ gövdeler taşıyordu — yani listelenen alanlar "gördüğümüz"
   alanlardır, "hepsi" değildir. Bu yüzden hepsi isteğe bağlıdır ve ekran tanımadığı
   anahtarı ATMAZ, ham basar.
   ============================================================================ */

/**
 * Depo tarafından KURULMAYAN, yalnız TAŞINAN gövde: Hindsight ne döndürdüyse o.
 *
 * `unknown` değer tipi bilinçli — `string | number` yazmak, iç içe bir nesne
 * geldiğinde derleyiciyi susturup ekranı `[object Object]` bastırırdı. Çizen
 * taraf her değeri açıkça daraltmak ZORUNDA (`HafizaYuzey.tsx::hamMetin`).
 */
export type HamGovde = Readonly<Record<string, unknown>>;

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
   * Sürüm dizgesi. `null` = uç okundu ama sürüm alanı TANINMADI — bu bir şema
   * sürüklenmesi işaretidir, "sürümsüz servis" değil (`api.py::_hafiza_surum`).
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
 * gibi alanlar taşıyor (ölçüm kaydında görünür), ama `api.py::api_hindsight`
 * listeden yalnız KİMLİĞİ alıp (`api.py::_hafiza_bank_kimligi`) gerisini DÜŞÜRÜYOR
 * ve bankanın sayılarını ayrı bir `stats` çağrısından getiriyor. Yani bu yüzey
 * "bankada kaç kayıt var" sorusunu ancak `stats` cevaplarsa cevaplayabilir;
 * cevaplamazsa sayı UYDURULMAZ, boşluk nedeniyle birlikte çizilir.
 */
export interface HafizaBankasi {
  /** Banka kimliği — upstream'e giden yolda kaçırılarak kullanılır. */
  readonly bank_id?: string;
  /**
   * Bankanın sayaç gövdesi, AYNEN GEÇER. `null` = ölçüm denendi, gövde gelmedi.
   * Şekli ÖLÇÜLMEDİ (ölçüm kaydında bu uç yok) — ekran anahtarlarıyla ham basar.
   */
  readonly stats?: HamGovde | null;
  /** Bu bankanın sayaçları neden okunamadı. Kardeş gerekçe — boş gövdeyle ayrı hâl. */
  readonly stats_neden?: string | null;
}

/* --- KOTA VE OPERASYON (`api.py::api_hindsight`) -------------------------- */

/**
 * Banka başına model çağrısı sayaçları. Şekli ÖLÇÜLMEDİ.
 * Sözlüğün ANAHTARI banka kimliğidir; sabit bir banka listesi burada YAZILMAZ —
 * yeni banka doğduğu gün ekranda kendiliğinden görünsün diye (F9 sınıfı ayrışma).
 */
export interface HafizaKotaKutusu {
  readonly llm_stats?: HamGovde | null;
  readonly neden?: string | null;
}

/**
 * Banka başına denetim kaydı sayaçları — bu yüzeyin "ne işlendi" bacağı.
 *
 * A1'DE GÖRÜLEN ALANLAR (ipucu, sözleşme değil): `bank_id` · `period` · `trunc` ·
 * `start` · `buckets`. Görüldüğü anda `buckets` BOŞTU, yani kova öğesinin şekli
 * ölçülemedi ve buraya yazılmadı — boş bir dizi gördüğümüzde onun içindeki
 * nesnenin alanlarını tahmin etmek, tam da bu dosyanın yasakladığı şey.
 *
 * DİKKAT — FIXTURE BU GÖVDEYLE AYNI DEĞİL: `test_hafiza_yuzeyi_v375.py::AUDIT_GOVDE`
 * `{"event_count": …}` taşıyor, yani yukarıdaki beş alanı DOĞRULAMIYOR. Bu liste bu
 * yüzden bir ipucudur ve tip hiçbirini zorunlu kılmaz; ekran ne gelirse onu basar.
 */
export interface HafizaOperasyonKutusu {
  readonly audit_stats?: HamGovde | null;
  readonly neden?: string | null;
}

/* --- TOPLU GÖVDE (`api.py::api_hindsight`) -------------------------------- */

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

/* --- LİSTE (`api.py::api_hindsight_liste`) -------------------------------- */

/**
 * BİR HAFIZA KAYDI. Alanlar ÖLÇÜLDÜ ama ölçüm kaydı KIRPILMIŞ bir gövde taşıyor —
 * yani bunlar "görülen" alanlardır, "tüm" alanlar değil. Hepsi isteğe bağlı ve
 * çekmece gövdenin TAMAMINI ham basar: burada listelenmeyen bir alan ekrandan
 * sessizce düşmesin diye.
 *
 * `HamGovde` genişletilerek yazıldı, kapatılarak değil: tanınmayan anahtar hâlâ
 * tiplidir ve çizen taraf onu dolaşabilir.
 */
export interface HafizaKaydi extends HamGovde {
  readonly id?: unknown;
  /** Kaydın kendisi — insanın okuduğu metin. */
  readonly text?: unknown;
  /** Kaydın nereden geldiği (ölçümde: içe aktarım künyesi). */
  readonly context?: unknown;
  readonly date?: unknown;
  /** Ölçümde görülen değer: `world`. Sözlüğü ölçülmedi, ekran ham basar. */
  readonly fact_type?: unknown;
  readonly document_id?: unknown;
  readonly mentioned_at?: unknown;
}

/**
 * SAYFA GÖVDESİ — ve burada OLMAYAN şeyin adı: TOPLAM SAYI.
 *
 * `api.py::api_hindsight_liste` yalnız `{ogeler, neden}` döner; kaç kayıt olduğunu
 * söyleyen bir alan YOKTUR. Ekran bu yüzden "3 / 12 sayfa" gibi bir şey ÇİZEMEZ ve
 * çizmeye çalışmak sayfa sayısını uydurmak olurdu. Sayfalamanın dürüst hâli
 * "önceki / sonraki"dir ve sonrakinin varlığı da bir ÇIKARIMDIR (dolu sayfa),
 * bir ölçüm değil — `HafizaYuzey.tsx` bunu ekranda söyler.
 */
export interface HafizaListesi {
  readonly ogeler?: readonly HafizaKaydi[];
  /** Dolu = ÖLÇÜLEMEDİ. Boş `ogeler` + boş `neden` = ölçüldü, bu sayfada kayıt yok. */
  readonly neden?: string | null;
}

/* --- DETAY (`api.py::api_hindsight_detay`) -------------------------------- */

/**
 * TEK KAYIT. `oge: null` ucun BİLİNÇLİ tercihidir ve tipte korunur: bulunamayan
 * kayıtta boş sözlük dönmek "kayıt var ama içi boş" yalanı olurdu.
 */
export interface HafizaDetayi {
  readonly oge?: HafizaKaydi | null;
  readonly neden?: string | null;
}
