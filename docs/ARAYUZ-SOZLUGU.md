# Arayüz sözlüğü — iç terim → kullanıcı karşılığı

**Neden var (2026-08-26, operatör):** *"Uygulama içinde kullanılan dilde çok fazla internal
terim oldu ve uygulama çok büyüdüğü için ben bile anlamakta zorlanıyorum. Dışardan bir göz
sadece UI'ı göreceği için buradaki açıklamaların düzelmesi lazım."*

**Kapsam — ve sınırı:** bu sözlük **kullanıcının GÖRDÜĞÜ metni** bağlar: etiketler, başlıklar,
kart adları, boşluk mesajları. **Kod tanımlayıcılarını (değişken/fonksiyon/prop/alan adları)
BAĞLAMAZ** ve bu bilinçli bir karardır: dışarıdan gelen göz onları görmez, buna karşılık bu
depodaki kök-neden şerhleri eski adlara bağlıdır (`silahli`, `kadans`, `hermes` geçen yüzlerce
gerekçe satırı). Kodu yeniden adlandırmak o şerhleri öksüz bırakır — ölçülmüş bilgiyi yakar,
görünür hiçbir fayda üretmez.

## Değişenler

| iç terim | kullanıcı karşılığı | gerekçe |
|---|---|---|
| sprint | **antrenman turu** | yazılım jargonu; yüzeyin adı zaten "Antrenman" |
| hermes | **danışma** / **yapay zekâ danışmanı** | kod adı; hiçbir şey anlatmıyor |
| beyin · beyin zinciri | **model** · **model zinciri** | aynı ekranda "model" de kullanılıyordu, iki ad tek şey |
| yansıma | **değerlendirme** | sistemin kendi kararlarını gözden geçirmesi |
| kadans | **otomatik döngü** | |
| silahlı küme · silahlanma | **işleme hazır planlar** · **işleme hazırlık** | askerî çağrışım, karşılığı yok |
| kapı (kontrol anlamında) | **kontrol** | "Veri kapısı" → "Veri kalite kontrolü" |
| hüküm | **karar** | |
| gölge (yasa/test) | **deneme** | denenen ama uygulanmayan kural |
| kova (histogram) | **aralık** | Türkçe finans okuryazarı "getiri aralığı" bekler |
| ufuk · bacak | **değerlendirme koşulu** · **taraf** | kutunun kendi açıklaması zaten böyle diyor |
| tohum | **başlangıç verisi** | seed |
| ısınma | **hazırlık** | warmup |
| çırpınma | **bağlantı kopmaları** | flapping |
| karşı-olgusal | **alınmamış işlem** | akademik terim |
| kat kazanımı | **doğrulama dilimi kazancı** | `fold_wins`ın kelime kelime çevirisiydi, Türkçede hiçbir şey anlatmıyor |
| üçüncü hâl | *(kaldırıldı)* | ölçüm doktrininin iç adı; kullanıcı birinci/ikinciyi bilmiyor |
| açık kalem | **henüz eklenmedi** | proje yönetimi jargonu |
| eksen-2 | **beceri önerisi** | iç program adı |

## DEĞİŞMEYENLER — ve neden

Bunlar iç terim gibi görünür ama **sektörün ortak dilidir**; dışarıdan gelen finans okuryazarı
bir göz bunları bilir. Değiştirmek netlik değil, yabancılaşma üretirdi:

| terim | neden kalıyor |
|---|---|
| **defter** | gerçek muhasebe terimi — "Açık pozisyon defteri" doğru Türkçe |
| **rejim** | piyasa literatüründe standart (market regime) |
| **stop · limit · bracket** | emir tipleri; her broker arayüzünde aynı |
| **nabız** | sistem sağlığı bağlamında yaygın (heartbeat); yanında yaşı da yazıyor |
| **plan · kurulum · tetik** | alım-satım günlüğü dili |

## Terim kalıyor mu — BAĞLAMA göre, kelimeye göre değil

İkinci tur ölçümü (2026-08-26, cümle görünümlü her dize literali taranarak) 34 kalıntı
buldu. **Hepsi kusur değildi.** Aynı kelime iki ayrı bağlamda iki ayrı şeydir ve karar
bağlamla verilir — bu tablo o kararı kayda geçirir ki bir sonraki tur onları "unutulmuş"
sanıp yeniden çevirmesin:

| kelime | ÇEVRİLDİ | KALDI — ve neden |
|---|---|---|
| bacak | Hermes değerlendirme penceresi: "işlem bacağı" → **işlem tarafı** | emir yapısı: "stop/hedef bacakları", "koruma bacağı" — `bracket leg`in Türkçesi, her broker arayüzünde bu; yukarıdaki DEĞİŞMEYENLER tablosundaki `stop · limit · bracket` ile aynı aile |
| kova | histogram: "getiri kovası" → **getiri aralığı**; bekçi durumu: "`never` kovasında" → **`never` aralığında** | `r_kovasi` · `tutma_kovasi` — bunlar API FACET ADLARI, ekranda köken olarak gösteriliyor; çevirmek uçla bağı koparırdı |
| sprint · hermes | görünen etiketler | `` `sprint.should_run()` `` · `` `besleme.antrenman_sprinti` `` · `/api/hermes` — backtick/kod içindeki sembol ve uç yolu KÖKEN bilgisidir |
| hüküm · silahlanma · gölge | tüm kullanıcı cümleleri | `SilahlanmaOlcumu` · `HermesGovdesi` · `hukumTanindi` — kod tanımlayıcıları (kapsam kararı en üstte) |

**`teknik=` KATMANI BİLEREK SERBESTTİR.** Dürüst-boşluk sözleşmesi (v323) iki katmanlıdır:
`neden` insan cümlesidir ve görünür; `teknik` üstüne gelince çıkan iç ayrıntıdır. Oraya
alan adı, uç yolu ve iç terim YAZILIR — teşhis eden kişinin ihtiyacı odur. Sözlük birinci
katmanı bağlar, ikincisini değil.

## Çiviler — ve neyi BAĞLADIKLARI

| çivi | neyi bağlar |
|---|---|
| `tests/test_arayuz_dili_v323.py` | dürüst-boşluk sözleşmesi (`neden` insan cümlesi · `teknik` iç ayrıntı) **ve** yukarıdaki "değişenler" tablosunun gezinme kaydında (`ui/src/pano/alanlar.ts`) uygulanmış olması |
| `tests/test_capa_kimligi_slug_v324.py` | `kimlik` DEĞERİ slug kalır — çeviri DOM çapasına sızamaz |
| `tests/test_pano_yuzey_kaydi_v288.py` | kayıt ↔ ekran çapası paritesi (çeviri bir çapayı kaydırırsa öter) |

**Bu bölümün önceki hâli YANLIŞ BEYANDI ve kaydı burada duruyor.** İlk yazımda
"bu tablo tek kaynaktır ve testle bağlıdır" yazdım; bağlı DEĞİLDİ. Ölçülen sonuç
(2026-08-26, ikinci tur):

* v323'ün kapsamı `PANO.rglob("*.tsx")` idi; kenar çubuğu kaydı `alanlar.ts` bir `.ts`.
  **Tek bir uzantı filtresi hem çeviriyi hem çiviyi kör bıraktı:** A turu 102 etiket
  çevirdi, gezinme metnine hiç dokunmadı, ve suite bunu YEŞİL geçti. Gövde "Danışma"
  yazarken menü "Hermes" diyordu.
* Aynı turda ters yönde bir hasar da oluştu: kapsamı "çift tırnaklı dize" diye
  daraltmıştım, ama **çift tırnaklı bir dize kullanıcı metni olmak zorunda değildir.**
  `kimlik="sprint"` → `kimlik="antrenman turu"` oldu; bu bir DOM çapasıdır ve derin bağ
  sessizce kaymaya başladı. 26 dakikalık tam suite'in tek kırmızısı buydu (v288).
  Biçim denetimi artık v324'te.

**Ders, kuralın kendisinden daha genel:** ayrım dizenin TIRNAK BİÇİMİ değil, DOLDURDUĞU
ALANDIR. `baslik`/`soru`/`etiket`/`neden` kullanıcıya gider; `kimlik`/`ad`(alan anahtarı)/
backtick içindeki sembol gitmez. İkinci turda `` `sprint.should_run()` `` de birinci
tur tarafından `` `antrenman turu.should_run()` `` yapılmıştı — backtick içi kod adı
kullanıcı metni değildir.
