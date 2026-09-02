/* ============================================================================
   BANKA YAPILANDIRMA ALAN TABLOSU — üst yüzeyin formundan OKUNDU, uydurulmadı
   ----------------------------------------------------------------------------
   KAYNAK: Hindsight Control Plane, commit `ebad478240d3171bb88201ececda5e8d9883d22d`
   (v0.9.2) — `hindsight-control-plane/src/components/bank-config-view.tsx` +
   `src/messages/en.json` (`bankConfig` sözlüğü). ÖLÇÜM TARİHİ: 2026-09-02.
   Aşağıdaki sekiz bölüm ve her bölümün alan sırası o dosyadaki JSX sırasının
   birebir karşılığıdır.

   BU DOSYA BİR KOPYA ÖLÇÜMDÜR VE BAYATLAYABİLİR (inceleme, endişe 4): üst yüzey
   v0.9.3'te bir alan eklerse ya da bir bölümü yeniden sıralarsa bunu SÖYLEYEN
   hiçbir çivi yok. Yukarıdaki commit ve tarih bu yüzden burada: bayatlığı en
   azından OKUNABİLİR olsun. Tabloyu güncelleyen tur ikisini de yeniler. Etiketler ve açıklamalar
   Türkçedir; ALAN ADLARI çevrilmez — onlar üst servisin sözlüğüdür ve ekranda da
   teknik ayrıntı olarak durur.

   NEDEN AYRI BİR DOSYA: liste hem formu çiziyor hem de "bu alanı çizdik mi"
   sorusunun tek cevabı. Çizilen alanların listesi JSX'in içine gömülseydi, ham
   döküm (aşağıdaki `atla` listesi) elle ikinci kez yazılırdı ve iki liste
   sessizce ayrışırdı — çizdiğimiz bir alan ham dökümde İKİNCİ kez görünür, ya da
   çizmediğimiz bir alan ham dökümden de DÜŞERDİ (tek-kaynak yasası).

   ---------------------------------------------------------------------------
   İKİ KAYNAK, VE AYRIM ÜST YÜZEYİN KENDİ GEREKÇESİDİR
   ---------------------------------------------------------------------------
   `GET /config` iki blok döndürüyor (canlı ölçüm 2026-09-02): `config` ÇÖZÜLMÜŞ
   değerler (devralınanlar dahil), `overrides` yalnız bu bankaya ÖZGÜ olanlar.
   Üst yüzey her alanı bilerek birinden ya da ötekinden okuyor ve gerekçesini de
   yazıyor: "çözülmüş değer, devralınan `true` ile açıkça `true` yapılmışı ayırt
   edemez". Bir alanın hangi bloktan okunduğu bu yüzden tabloda YAZILI — ve
   `overrides`ta duran alanın yanında "bankaya özgü" rozeti çıkar.

   ---------------------------------------------------------------------------
   BİZDE OLMAYAN TEK KAYNAK: BANKA PROFİLİ
   ---------------------------------------------------------------------------
   Üst yüzey Reflect bölümünün görev tanımını AYRI bir uçtan (`GET /profile`)
   okuyor; vekilde o ucun karşılığı YOK. Alan tabloda DURUYOR ve ekranda "bu
   panoda okunmuyor" diye çizilir — silmek "böyle bir ayar yok" derdi, boş
   bırakmak "ayar boş" derdi; ikisi de yanlış.
   ============================================================================ */

/** Değerin ekranda nasıl okunacağı. Biçim ALANIN kendi tipidir, süs değil:
 *  bir sayıyı "açık/kapalı" diye basmak ölçülmemiş bir yorum olurdu. */
export type AlanBicimi =
  | "sayi"
  | "metin"
  | "uzun-metin"
  | "acik-kapali"
  | "liste"
  | "sozluk"
  | "olcek";

export interface CpAlan {
  /** Üst servisin alan adı — çevrilmez, ekranda teknik ayrıntı olarak durur. */
  readonly anahtar: string;
  readonly etiket: string;
  readonly aciklama: string;
  readonly bicim: AlanBicimi;
  /** Üst yüzeyin okuduğu blok. `overrides` = devralınan/açık ayrımı gerekiyor. */
  readonly kaynak: "config" | "overrides";
  /** Bu panoda okunmuyorsa NEDENİ — alan çizilir ama değeri aranmaz. */
  readonly okunmuyor?: string;
  /** Üst yüzeyde alan yalnız bu koşulda görünüyorsa: hangi alan, hangi değer. */
  readonly kosul?: { readonly anahtar: string; readonly deger: string };
}

export interface CpBolum {
  readonly kimlik: string;
  readonly baslik: string;
  readonly aciklama: string;
  readonly altBaslik?: string;
  readonly alanlar: readonly CpAlan[];
}

export const CP_YAPILANDIRMA: readonly CpBolum[] = [
  {
    kimlik: "retain",
    baslik: "Retain",
    aciklama:
      "Varsayılan çıkarım ayarları ve adlandırılmış stratejiler. Bir kayıt isteğine strateji adı verilirse varsayılanlar o istek için geçersiz kılınır.",
    alanlar: [
      {
        anahtar: "retain_default_strategy",
        etiket: "Varsayılan strateji",
        aciklama: "İstekte strateji belirtilmediğinde kendiliğinden uygulanır.",
        bicim: "metin",
        kaynak: "config",
      },
      {
        anahtar: "retain_extraction_mode",
        etiket: "Çıkarım kipi",
        aciklama:
          "Kayıt sırasında olgular nasıl çıkarılıyor: concise (varsayılan, seçici) · verbose (her şeyi yakala) · verbatim (yazıldığı gibi koru) · chunks (modeli hiç çağırma, parçayı olduğu gibi sakla) · custom (kendi çıkarım kuralını yaz).",
        bicim: "metin",
        kaynak: "config",
      },
      {
        anahtar: "retain_chunk_size",
        etiket: "Parça boyu",
        aciklama: "İşleme için metin parçalarının boyu (karakter).",
        bicim: "sayi",
        kaynak: "config",
      },
      {
        anahtar: "retain_structured_chunk_size",
        etiket: "Yapılı parça boyu",
        aciklama:
          "Bir JSONL satırının ya da konuşma sırasının bütün kalması için en çok kaç karakter. Boşsa parça boyu kullanılır.",
        bicim: "sayi",
        kaynak: "config",
      },
      {
        anahtar: "retain_mission",
        etiket: "Görev tanımı",
        aciklama:
          "Bu bankanın çıkarım sırasında neye dikkat edeceği. Çıkarım kurallarının yerini almaz, modeli yönlendirir — her çıkarım kipiyle birlikte çalışır.",
        bicim: "uzun-metin",
        kaynak: "config",
      },
      {
        anahtar: "retain_custom_instructions",
        etiket: "Özel çıkarım istemi",
        aciklama:
          "Yerleşik çıkarım kurallarının tamamının yerine geçer. Yalnız çıkarım kipi custom iken etkin.",
        bicim: "uzun-metin",
        kaynak: "config",
        kosul: { anahtar: "retain_extraction_mode", deger: "custom" },
      },
      {
        anahtar: "entities_allow_free_form",
        etiket: "Serbest biçimli varlıklar",
        aciklama:
          "Etiket gruplarının yanı sıra sıradan adlandırılmış varlıkları (kişi, yer, kavram) da çıkar. Kapatınca çıkarım yalnız etiket gruplarıyla sınırlanır.",
        bicim: "acik-kapali",
        kaynak: "config",
      },
      {
        anahtar: "entity_labels",
        etiket: "Varlık etiketleri",
        aciklama:
          "Anahtar:değer sınıflandırma etiketlerinden oluşan denetimli sözlük (örn. pedagogy:scaffolding).",
        bicim: "liste",
        kaynak: "config",
      },
      {
        anahtar: "retain_strategies",
        etiket: "Adlandırılmış stratejiler",
        aciklama: "İstek başına varsayılanları geçersiz kılan adlandırılmış ayar kümeleri.",
        bicim: "sozluk",
        kaynak: "config",
      },
    ],
  },
  {
    kimlik: "observations",
    baslik: "Gözlemler",
    aciklama: "Olguların kalıcı gözlemlere nasıl sentezlendiği.",
    alanlar: [
      {
        anahtar: "enable_observations",
        etiket: "Gözlemleri aç",
        aciklama: "Olguların gözlemlere kendiliğinden birleştirilmesini aç.",
        bicim: "acik-kapali",
        kaynak: "overrides",
      },
      {
        anahtar: "observations_mission",
        etiket: "Görev tanımı",
        aciklama:
          "Bu bankanın kalıcı gözlemlere neyi sentezleyeceği. Yerleşik birleştirme kurallarının yerine geçer — boş bırakılırsa sunucu varsayılanı.",
        bicim: "uzun-metin",
        kaynak: "config",
      },
      {
        anahtar: "consolidation_llm_batch_size",
        etiket: "Model yığın boyu",
        aciklama:
          "Tek bir birleştirme çağrısında modele gönderilen olgu sayısı. Yükseltmek çağrı sayısını düşürür, istemi büyütür.",
        bicim: "sayi",
        kaynak: "config",
      },
      {
        anahtar: "consolidation_source_facts_max_tokens",
        etiket: "Kaynak olgu jeton tavanı",
        aciklama:
          "Birleştirme istemine geçen kaynak olguların en çok kaç jeton tutacağı. Yükseltmek daha çok bağlam katar, çağrı başına maliyeti artırır.",
        bicim: "sayi",
        kaynak: "config",
      },
      {
        anahtar: "consolidation_source_facts_max_tokens_per_observation",
        etiket: "Gözlem başına kaynak olgu jeton tavanı",
        aciklama: "Tek bir gözlem üretilirken göz önüne alınan kaynak olguların jeton tavanı.",
        bicim: "sayi",
        kaynak: "config",
      },
      {
        anahtar: "max_observations_per_scope",
        etiket: "Kapsam başına gözlem tavanı",
        aciklama: "Birleştirmeden sonra kapsam başına saklanan gözlem sayısının tavanı.",
        bicim: "sayi",
        kaynak: "config",
      },
    ],
  },
  {
    kimlik: "reflect",
    baslik: "Reflect",
    aciklama: "Bankanın düşünme işlemlerinde nasıl akıl yürüttüğü ve cevap verdiği.",
    alanlar: [
      {
        anahtar: "reflect_mission",
        etiket: "Görev tanımı",
        aciklama: "Ajanın kimliği ve amacı. Düşünme işleminde çerçeve bağlamı olarak kullanılır.",
        bicim: "uzun-metin",
        kaynak: "config",
        okunmuyor:
          "üst yüzey bu değeri ayrı bir banka profili ucundan okuyor; o ucun vekilde karşılığı yok",
      },
      {
        anahtar: "disposition_skepticism",
        etiket: "Şüphecilik",
        aciklama: "İddiaları değerlendirirken ne kadar şüpheci, ne kadar güvenen (1 güvenen … 5 şüpheci).",
        bicim: "olcek",
        kaynak: "config",
      },
      {
        anahtar: "disposition_literalism",
        etiket: "Sözel bağlılık",
        aciklama: "Bilgiyi ne kadar birebir yorumlayacağı (1 esnek … 5 birebir).",
        bicim: "olcek",
        kaynak: "config",
      },
      {
        anahtar: "disposition_empathy",
        etiket: "Duygusal bağlam",
        aciklama: "Duygusal bağlama ne kadar ağırlık vereceği (1 mesafeli … 5 empatik).",
        bicim: "olcek",
        kaynak: "config",
      },
    ],
  },
  {
    kimlik: "mental-models",
    baslik: "Zihin modelleri ve bilgi sayfaları",
    aciklama:
      "Bu bankadaki zihin modelleri — ve onlara dayanan bilgi sayfaları — nasıl güncel tutuluyor.",
    alanlar: [
      {
        anahtar: "mental_model_min_refresh_interval_seconds",
        etiket: "En kısa tazeleme aralığı",
        aciklama:
          "Aynı zihin modelinin iki kendiliğinden tazelemesi arasındaki en az saniye. Daha erken tetiklenen tazeleme kuyruğa alınır ve pencereyi bekler; art arda gelen tetikler ona katlanır. Elle tazeleme her zaman hemen koşar. Boş = sunucu varsayılanı; 0 = sınır yok.",
        bicim: "sayi",
        kaynak: "overrides",
      },
    ],
  },
  {
    kimlik: "mcp",
    baslik: "MCP araçları",
    aciklama: "Bu bankanın ajanlara açtığı araçları sınırla.",
    alanlar: [
      {
        anahtar: "mcp_enabled_tools",
        etiket: "Araçları sınırla",
        aciklama:
          "Kapalıyken tüm araçlar açıktır. Açıkken yalnız seçili araçlar bu banka için çağrılabilir.",
        bicim: "liste",
        kaynak: "config",
      },
    ],
  },
  {
    kimlik: "guvenlik",
    baslik: "Güvenlik ve gizlilik",
    aciklama: "Bu banka için denetim kaydı ve ham kaynak metin saklama.",
    alanlar: [
      {
        anahtar: "audit_log_enabled",
        etiket: "Denetim kaydını aç",
        aciklama:
          "Bu banka için kayıt alma, geri çağırma ve düşünme işlemlerini kaydet. Yalnız bu banka için sunucu varsayılanını geçersiz kılar.",
        bicim: "acik-kapali",
        kaynak: "overrides",
      },
      {
        anahtar: "store_document_text",
        etiket: "Belge metnini sakla",
        aciklama:
          "Ham kaynak metni (belge asılları ve parçalar) sakla. Kapatınca yalnız türetilmiş olgular kalır.",
        bicim: "acik-kapali",
        kaynak: "overrides",
      },
    ],
  },
  {
    kimlik: "recall",
    baslik: "Recall hattı",
    aciklama: "Bu bankada geri çağırma sırasında hangi getirme adımlarının koştuğu.",
    alanlar: [
      {
        anahtar: "enable_temporal_retrieval",
        etiket: "Zamansal getirme",
        aciklama:
          "Tarih duyarlı sorgu çözümlemesi koşsun. Kapatmak zamansal getirme kolunu da atlar — bu bankanın içeriği anlamlı tarih taşımıyorsa işe yarar.",
        bicim: "acik-kapali",
        kaynak: "overrides",
      },
      {
        anahtar: "enable_graph_retrieval",
        etiket: "Graf getirme",
        aciklama:
          "Geri çağırma sırasında varlık ve bağ ilişkilerinde dolaş. Kapatmak ilişkisel geri çağırmayı düşük gecikmeye takas eder.",
        bicim: "acik-kapali",
        kaynak: "overrides",
      },
      {
        anahtar: "enable_reranking",
        etiket: "Yeniden sıralama",
        aciklama:
          "Birleştirilmiş adayları çapraz kodlayıcıyla yeniden sırala. Kapatmak doğrudan füzyon sırasını döndürür — hızlı ama daha az isabetli.",
        bicim: "acik-kapali",
        kaynak: "overrides",
      },
    ],
  },
  {
    kimlik: "modeller",
    baslik: "Modeller",
    aciklama: "Sağlayıcıya özgü model ayarları.",
    altBaslik: "Gemini / Vertex AI",
    alanlar: [
      {
        anahtar: "llm_gemini_safety_settings",
        etiket: "Güvenlik ayarları",
        aciklama:
          "Kapalıyken sağlayıcının kendi güvenlik eşikleri kullanılır. Açıkken zarar kategorisi başına eşik ayarlanır.",
        bicim: "liste",
        kaynak: "config",
      },
    ],
  },
];

/** Formda GERÇEKTEN DEĞER GÖSTEREN alan adları — ham dökümün `atla` listesi
 *  buradan TÜRER. Elle ikinci kez yazılsaydı iki liste sessizce ayrışırdı.
 *
 *  `okunmuyor` İŞARETLİ ALAN LİSTEYE GİRMEZ (inceleme M-5): o alan formda "bu
 *  panoda okunmuyor" diye çiziliyor, yani değeri GÖSTERİLMİYOR. Atla listesine
 *  koymak, gövde o anahtarı taşısa bile hiçbir yerde görünmemesi demekti —
 *  "çizdik" ile "çizmedik" arasındaki farkı ham döküm kapatmalı. */
export const CIZILEN_ALANLAR: readonly string[] = CP_YAPILANDIRMA.flatMap((b) =>
  b.alanlar.filter((a) => a.okunmuyor === undefined).map((a) => a.anahtar),
);
