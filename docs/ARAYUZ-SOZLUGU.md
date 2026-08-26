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

## Çivi

`tests/test_arayuz_dili_v323.py` — bu tablo tek kaynaktır ve testle bağlıdır: burada
"değişen" sayılan bir terim kullanıcıya görünen metinde yeniden belirirse suite kırmızı olur.
