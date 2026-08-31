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
- **[RM-041] Yansıma mükerrerlik kapısı** — durum: ARAYA-KALEM · doğum: 2026-09-01 · sahip: rol1 · boyut: küçük-orta · tetik: —
  Ne: hermes_reflect öneri basmadan akıbet defterindeki açık+kararlı önerilere benzerlik kontrolü.
  Neden: ilk karar turu %45 bellek-yokluğu israfı ölçtü (operatör 2026-09-01). Ref: N-defteri · cc5aba1.
```

Alan sözlükleri DONUKTUR (yeni değer = bu belgeye tarihli ek):
- durum: `UÇUŞTA · SIRADA · ARAYA-KALEM · BEKLEMEDE(tetik) · MASADA(operatör) · KAPANDI(tarih·ref)`
- sahip: `operatör · rol1 · ajan` — boyut: `küçük · orta · büyük` (ara değerler `küçük-orta` gibi tire ile)
- tetik: BEKLEMEDE ise zorunlu ve somut; değilse `—`

## §2 Kimlik politikası (operatör düzeltmesiyle)

- **ROADMAP-doğumlu kimlikler YENİDEN ADLANDIRILIR:** maddeler `RM-###` (göç sırasında
  belge-sırasıyla numaralanır; numara KİMLİKTİR, yeniden kullanılmaz); cepheler (eski WP1-11)
  `C-##` + ad. Eski adlar SİLİNMEZ: §∞ EŞLEME TABLOSU'na ikinci dalga olarak eklenir
  (2026-08-13 yeniden-numaralandırma emsali) ve her maddenin gövdesinde `eski: WP7` düşülür.
- **DIŞ-SİSTEM kimlikleri DEĞİŞMEZ, `Ref` alanına iner:** `EDG-####` (kart dosyaları —
  card_id yasası v219), `N#####` (akıbet defteri satır kimliği), `vNNN` (test kimliği),
  `Yasa 4/6` (275+405 atıf). Bunları yeniden adlandırmak kendi sistemlerini kırar; madde
  kimliği RM olur, dış kimlik referans olarak taşınır.
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
   (a) her madde başlık-regex'ine uyar, (b) durum/sahip/boyut sözlükten, (c) RM/C kimlikleri
   tekil, (d) BEKLEMEDE tetiksiz olamaz. Uymayan madde suite'i kırmızı yapar.
2. CLAUDE.md §2 kapı tablosuna satır: "ROADMAP'e madde yazmak → şema (bu belge)".
3. Rol-1 hafıza kaydı `roadmap-madde-standardi` (yazıldı 2026-09-01).

## §5 Pano bacağı

`/api/roadmap` ayrıştırıcısı başlık-satırı alanlarını yapılandırılmış döndürür
(`maddeler[].{kimlik, ad, durum, sahip, boyut, tetik, bolum}`); `YolHaritasi` yüzeyi
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
