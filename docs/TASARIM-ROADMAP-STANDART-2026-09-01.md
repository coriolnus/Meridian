# TASARIM — ROADMAP Madde Standardı ve Dinamik Pano (2026-09-01)

Operatör kararı (2026-09-01 gece): "bütün kalemlerin isimlendirmesi, açıklaması, durumları
standardize olmalı; öneri havuzuna madde eklerken de korunmalı; bundan sonra yazılan her şey
bu standardı korumalı; pano dinamik olmalı" + "mevcut kimlikleri de uygun şekilde yeniden
adlandıralım; §7/§8 muaf; zorlama önerileri uygulansın; slot: akıbet-dalgası sonrası".

Ölçülen taban (2026-09-01): ROADMAP.md 5.222 satır · ~473 madde işareti + 226 tablo satırı ·
hiçbir iki madde aynı biçimde değil · İCRA SIRASI tek paragraf (~6.000 karakter) · pano
`/api/roadmap` ayrıştırması alan tanımıyor (yalnız madde/tablo sayıyor, v343).

## §1 Madde şeması (bağlayıcı)

Yaşayan her madde = başlık satırı (makine-ayrıştanır) + gövde (insan-okur):

```
- **[TSK-041] Yansıma mükerrerlik kapısı** — status: INTERIM · born: 2026-09-01 · owner: rol1 · size: S-M · trigger: —
  What: hermes_reflect öneri basmadan akıbet defterindeki açık+kararlı önerilere benzerlik kontrolü.
  Why: ilk karar turu %45 bellek-yokluğu israfı ölçtü (operatör 2026-09-01). Ref: N-defteri · cc5aba1.
```

Terimler İNGİLİZCE (operatör 2026-09-01: "türkçe olmasına gerek yok, ingilizce terimler
olsun") — açıklama düzyazısı Türkçe kalır, ŞEMANIN anahtar/değer seti İngilizce'dir.
Alan sözlükleri DONUKTUR (yeni değer = bu belgeye tarihli ek):
- status: `ACTIVE (uçuşta) · QUEUED (sırada) · INTERIM (araya-kalem) · GATED(trigger)
  (tetik bekliyor) · OPERATOR (operatör masasında) · DONE(date·ref) (kapandı) ·
  DROPPED(date·reason) (artık gereksiz — tarihli ek 2026-09-01, aşağıda)`
- Tarihli ek (operatör 2026-09-01 gece: "her kalem ne durumda, artık gerekli mi gereksiz mi
  yapıldı mı yapılmadı mı gibi kontrolleri de yap, sonrasında açık kapalı gibi sınıflandır"):
  göç sırasında her madde GERÇEKLİK KONTROLÜNDEN geçer — depo kanıtıyla (git log, dosya
  varlığı, günlük, kart hükmü) yapılmış olan DONE'a, geçersizleşmiş/aşılmış olan
  DROPPED(tarih·gerekçe)'e iner; kanıtsız hüküm verilmez (uydurma yasağı). Üst sınıflandırma:
  AÇIK = ACTIVE·QUEUED·INTERIM·GATED·OPERATOR, KAPALI = DONE·DROPPED. Ajan DROPPED'ı yalnız
  ÖNERİR (kanıtıyla); hükmü Rol-1 verir, kararsızlar operatör listesine düşer.
- owner: `operator · rol1 · agent` — size: `S · M · L` (ara değer `S-M` gibi tire ile)
- trigger: GATED ise zorunlu ve somut; değilse `—`

## §2 Kimlik politikası (operatör düzeltmesiyle)

- **ROADMAP-doğumlu kimlikler YENİDEN ADLANDIRILIR:** maddeler `TSK-###` (task; 3 harf İngilizce —
  operatör düzeltmeleri aynı gece). Numaralama DOĞUM/ATAMA sırasıyladır, belge sırasıyla değil:
  göçten önce doğan maddeler numarasını doğduğu an alır (TSK-001 dalganın kendisi), göç kalan
  maddeleri son atanan numaradan devam ettirir; numara KİMLİKTİR, yeniden kullanılmaz.
  Cepheler (eski WP1-11)
  `PRG-##` (program) + ad. Eski adlar SİLİNMEZ: §∞ EŞLEME TABLOSU'na ikinci dalga olarak eklenir
  (2026-08-13 yeniden-numaralandırma emsali) ve her maddenin gövdesinde `eski: WP7` düşülür.
- **DIŞ-SİSTEM kimlikleri DEĞİŞMEZ, `Ref` alanına iner:** `EDG-####` (kart dosyaları —
  card_id yasası v219), `N#####` (akıbet defteri satır kimliği), `vNNN` (test kimliği),
  `Yasa 4/6` (275+405 atıf). Bunları yeniden adlandırmak kendi sistemlerini kırar; madde
  kimliği TSK olur, dış kimlik referans olarak taşınır. Operatör 2026-09-01: "EDG değiştirmek
  çok zorsa kalsın" — kalıyor. Not: akıbet defterinin kendi sözlüğü rol1/operatör-doğumlu
  öneriler için zaten 3 harfli `AKB-####` biçimini tanıyor (ops/akibet.py) — düzen uyumlu.
- Atıf süpürmesi zorunlu: yeniden adlandırılan her kimliğin depodaki TÜM atıfları
  (testler, CLAUDE.md, docs, kod yorumları) aynı dalgada güncellenir — kırık çapa sessizdir
  (yeniden-adlandırma-kapsamı vakası).

## §3 Kapsam

- TAM GÖÇ: §0 (sıralama/İCRA SIRASI → sıralı standart-madde tablosu), §2 TAHTA, §3 cepheler
  (başlık + açık kalemler; kapanmış tarihçe blokları olduğu gibi kalır), §4 HAVUZ, §5 masa,
  §6 kart endeks satırları.
- MUAF (operatör onayı): §7 KARAR GÜNLÜĞÜ ve §8 ARŞİV geriye dönük DOKUNULMAZ (tarihçe-koru,
  silme-yok); bu bölümlere bundan sonra yazılan YENİ girişler ise standarda uyar.

## §4 Zorlama (üç katman, operatör onaylı)

1. Yeni çivi dosyası (vNNN — oluşturma anında grep ile boş numara): yaşayan bölümlerde
   (a) her madde başlık-regex'ine uyar, (b) durum/sahip/boyut sözlükten, (c) TSK/PRG kimlikleri
   tekil, (d) GATED trigger'sız olamaz. Uymayan madde suite'i kırmızı yapar.
2. CLAUDE.md §2 kapı tablosuna satır: "ROADMAP'e madde yazmak → şema (bu belge)".
3. Rol-1 hafıza kaydı `roadmap-madde-standardi` (yazıldı 2026-09-01).

## §5 Pano bacağı

`/api/roadmap` ayrıştırıcısı başlık-satırı alanlarını yapılandırılmış döndürür
(`maddeler[].{id, name, status, owner, size, trigger, section}`); `YolHaritasi` yüzeyi
durum/bölüm/sahip süzgeçli dinamik tahta çizer. v343 okuyucu-çivisi genişletilir (üretilen
her yeni alanın okuyucusu — Yasa 6). Ölçülemeyen alan None+neden (şemaya uymayan eski §7/§8
satırları "muaf-tarihçe" sınıfıyla ayrılır, uydurulmaz).

## §6 Göç yöntemi ve sıra

1. Çapa envanteri: ROADMAP metnine/kimliklerine bakan test+doc+kod atıfları listelenir (grep).
2. Bölüm başına dönüşüm (ajan + Rol-1 incelemesi): §4 havuz → §2 tahta → §0 İCRA SIRASI →
   §3 cepheler → §5 masa → §6 endeks (küçükten büyüğe, şema erken oturur).
3. Çivi + CLAUDE.md satırı + §∞ eşleme güncellemesi aynı dalgada; kırılan çapalar süpürülür.
4. API/pano bacağı son adım; tam suite (`-n 4`) + dağıtım penceresi operatörle.
Slot (onaylı): akıbet-dalgası kapanır kapanmaz, skill-görüşten önce. Boyut: büyük.
