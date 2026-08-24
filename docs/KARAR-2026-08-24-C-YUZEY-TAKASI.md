# KARAR — ① Bugün ↔ ② Karar yüzey takası

**Tarih:** 2026-08-24 · **Kaynak:** operatör talimatı (ekran görüntüsüyle netleştirildi)
**Rol:** Rol-1 uyguladı · **Durum:** uygulandı, kapsam testi + tarayıcı doğrulaması geçti

## 0 · Talimat

> "Bugün altındaki Toplulaştırma kısmı Karar altına taşınmalı, karar altındaki ne önerildi ne
> oldu kısmı ile BİR SONRAKİ AÇILIŞ İÇİN kısmı bugün altına taşınmalı"

"ne önerildi ne oldu kısmı" başta belirsizdi (panoda o adla bir bölüm başlığı YOK — yalnız
Karar alanının h1'i ve soru cümlesi). Operatör ekran görüntüsü gönderdi: kastedilen **başlık
bloğu + altındaki dört durum kartı** (SON DÖNGÜ · KİTAP · EMİRLER·AYNA · POZİSYONLAR).

## 1 · Yapılan üç taşıma

| ne | nereden | nereye |
|---|---|---|
| Dört durum kartı (`durumIzgarasi*`) | ② Karar alan başlığı | ① Bugün, sakinlik beyanının altı |
| «Bir sonraki açılış için» kartı | ② Karar → Adaylar | ① Bugün, huninin hemen altı |
| Toplulaştırma (`pv-top`) | ① Bugün | ② Karar → yeni `topviews` bölümü (EN SON) |

Başlıklar da taşındı, çünkü **h1 içeriğin ADIDIR**; içerik yer değiştirip ad yerinde kalsaydı
sayfa kendini yalanlardı:

* Bugün h1: ~~"Dün gece ve bugün."~~ → **"Ne önerildi ve ne oldu?"**
* Karar h1: ~~"Ne önerildi ve ne oldu?"~~ → **"Neden geçti ve ne birikti?"**
* Soru cümleleri de aynı yönde güncellendi (`EKRAN_SORUSU`).

## 2 · Taşıma sırasında ÖLÇÜLEN ve ÇÖZÜLEN üç sorun

**(a) Kopya üretme riski.** Kart iki sayfaya kopyalansaydı ilk düzenlemede ayrışırdı. Gövde
tek yerde (`sonrakiAcilisKartiHTML`), bağlam türetimi tek yerde (`adaySinyalBaglami`) —
`latestSignal` gibi bir tanımın iki ekranda FARKLI sayı üretmesi bu depoda tekrar eden kusur.

**(b) İki görsel dünya.** Taşınan kart emekli `card` gramerindeydi; Bugün yüzeyinin sözleşmesi
(`test_s2r1_kabuk_v155::test_genel_bakis_SINIRSIZ_detay_dokumu_tasimaz`) üç şeyi birden
yasaklıyor: `class="card"`, `trow` satırı ve **İKİNCİ bir `<table>`** (tek tablo açık
pozisyonlara ayrılmış, çünkü onun paydası maruziyet bütçesidir, sorgu değil).
Çivinin kendi şerhi *"bu sınırlardan biri düşerse doğru tepki testi gevşetmek DEĞİL"* diyor —
**test gevşetilmedi**: kart `pv-` gramerine çevrildi (`.pv-sonraki` / `.pv-psat`), satırlar
tablo değil ızgara-düğme oldu, ve payda `PV_SONRAKI_TAVAN = 12` ile **BEYAN EDİLDİ**
(aşan kısım sayısıyla birlikte tam listeye yönlendirilir — kırpıldı, gizlenmedi).

**(c) Öksüz beyan + ölü hesap.** «gece» kartı kaldırıldı (SON DÖNGÜ kartı aynı üç sayıyı
söylüyordu). Bu, `GENEL_KARTLARI`ndaki `["gece", …]` satırını okuyucusuz bıraktı ve
`geceGovde` hesabını öldürdü — **ikisi de kaldırıldı** (YASA 6). İlk yazımda "geceGovde hâlâ
okunuyor" diye yorum düşmüştüm; **yanlıştı ve ölçümle düzeltildi**.

## 3 · Gerileme ve düzeltmesi

Kart taşınınca **Adaylar bölümü kendi özet şeridini kaybetti** (v192 dört bölgede şerit ister;
`test_dort_bolumun_ozet_seridi_var_ve_TIKLANMAZ` yakaladı). Şerit geri kondu ama **PAYDASI
FARKLI ve bu bilinçli**: taşınan şerit SON SEANSI, Adaylar'ınki pencerenin TAMAMINI özetler.
Her yüzey KENDİ paydasını özetler; aynı etiketi iki farklı paydayla basmak v192'nin kapattığı
kusurdu. Dördüncü hücre ("Tarama → plan") paydası aday olduğu için ayrı çubukta durur.

## 4 · Tazelenen çiviler (SİLME YOK — hepsi tarihli gerekçeyle)

`test_ia_v199` (soru cümleleri · ızgara tek yüzeyde) · `test_pano_durum_kartlari_v191`
(ızgara konumu · yedinci şerit bölgesi) · `test_s2r2_goc_v156` (ADR haritası +`topviews`) ·
`test_s2r3_cila_v160` (palet 21→22) · `test_kart_sozlesmesi_v198` (karar 26→25, ratchet'in
İKİNCİ beyanlı düşüşü) · `palette.js` (yeni bölüm kaydı).

## 5 · Doğrulama

* Kapsam süpürmesi **887 passed, 0 failed** (pano · uiux · ia · kart · s2r · cila · kabuk · göç)
* `node --check` app.js + palette.js OK
* **Tarayıcı** (yerel statik fikstür sunucusu; canlı uygulama YÜKLENMEDİ): Bugün'de dört kart +
  taşınan bölüm (2 satır) çiziliyor, Toplulaştırma yok, «gece» kartı yok; Karar'da sıfır durum
  kartı, `topviews` gerçek facet verisiyle çiziliyor, bölüm sırası doğru; düşen bölüm YOK.
* **Gündüz + gece** ölçüldü: yeni CSS'in tamamı jeton üzerinden (`--card`/`--line`/`--tx*`),
  sert renk yok; gecede `.pv-psat` #262626 / #d4d4d4, `.pv-sonraki` kenarı #404040.

**RUNTIME KUSURU TARAYICI YAKALADI, TEST DEĞİL:** türetimi fonksiyona taşırken `rc`/`rcTop`/
`bySkill` hesaplanıyor ama döndürülmüyordu → `ReferenceError: bySkill is not defined` ve Adaylar
bölümü tamamen düşüyordu. Kaynağa bakan hiçbir test bunu göremezdi. Ders: yapısal taşımadan
sonra kapsam testi YETMEZ, sayfa çizdirilmeli.

---

# İKİNCİ TUR — palet, huni ve YEDİ YÜZEY (aynı gün, operatör geri bildirimiyle)

## 6 · Operatörün dört cümlesi

> "Dub renklerini kullanmamışsın" · "grafikler ve huni hala gri gözüküyor" ·
> "görsel uyumsuzluk var, ve kitap, sermaye aynı rakamı gösteriyor, bu gerçekten gerekli mi?" ·
> "mockup'daki sol sekmeler de daha uygun bir gruplama sunuyor... analiz sekmesi istemiştim...
> sen bir önceki tasarımı olduğu gibi taşımışsın, tasarım dilini de buna göre değiştirmen
> gerekiyordu, sadeleştirmek de görevindi"

Eleştiri haklıydı: içerik taşındı, dil taşınmadı.

## 7 · "Gri görünüyor" — kök neden ÖLÇÜLDÜ, ve ilk teşhisim YANLIŞTI

**İlk teşhisim:** "merdiven 196° teal hue'sunda, Dub'ınki 221°; hue yanlış." Maketin paletini
dört yüzeye birden taşıdım. **Yanlıştı ve iki ölçüm çürüttü:**

| çakışma | ölçüm |
|---|---|
| `--lavender` #7c3aed | `--mod-canli` ile **BİREBİR AYNI HEX** — "CANLI PARA" çipiyle bir grafik serisi aynı renk olurdu |
| `--blue` #2563eb · `--sapphire` #1e40af | `--nav` ve `--nav-2` bunları ZATEN kullanıyor (ROL 6 navigasyon) |
| `--vivid-green` | `--sev-3` ("ok") hue'su — bir VARIŞ işareti bir HÜKÜM gibi okunurdu |

`index.html`in kendi yorumu bunu zaten yazmıştı ("HUE NEDEN DUB'IN MAVİSİ DEĞİL — ÖLÇÜLDÜ VE
BEYANLI... hue bir sonraki SERBEST banda taşındı"). Okudum ve üstünden geçtim; teal rastgele
değil, **kaçıştı**.

**GERÇEK kök neden hue değil AÇIKLIKTI:** merdivenin ilk basamağı L\* 19,3'teydi ve beyaz kartta
neredeyse siyah okunuyordu. Tek-seri grafikler (sermaye eğrisi, alan dolgusu, kıvılcım) de tam
o en koyu basamağı kullanıyordu — kullanıcının "gri" dediği şey buydu.

**Çözüm:** merdiven serbest bantta KALDI, yukarı kaydırıldı ve kromatikleşti. Yeni üçlü her
kısıtı birden geçiyor (hepsi bu turda ölçüldü):

| ölçüt | gündüz | gece |
|---|---|---|
| üçlü | `#004860 · #006f94 · #0998c8` | `#d2e9fe · #7ac1ff · #4e96d4` |
| en koyu basamak L\* | 19,3 → **28,1** | — |
| ÇG1 komşu ΔL\* (≥15) | 15,4 / 15,2 | 15,5 / 15,7 |
| ÇG2 en kötü GERÇEK zemin (≥3) | **3,04** | 4,78 |
| kroma ≤ 0,75 × şiddet | 0,1253 ≤ 0,1253 | 0,1179 ≤ 0,1183 |
| tek hue ailesi (≤2°) | 1,5° | 1,0° |
| nav (255-272°) / MOD (285-335°) bandı | dışında | dışında |

`--violet`/`--violet2` adları DÜŞTÜ, yerlerine `--sapphire`/`--sky` geldi: eski adlar "tarihsel
ad, değişen değer" ikilemini taşıyordu ve `--violet` hiç mor değildi. Dört yüzey + `tokens.json`
+ `docs/kontrast-denetimi.md` birlikte güncellendi (v208 jeton birliği çivisi bunu zorluyor).

## 8 · Huni — maketten YAPI alındı, renk alınamadı

Maketin huni yapısı BİREBİR uygulandı: segment başına **üç katman** (hale 1,45×@.10 + 1,18×@.18
+ çekirdek 1,00×@.92 — katsayılar maketin kendi koordinatlarından geri-hesaplandı) ve hue
ilerlemesi. Maketin renkleri (mavi→lavanta→yeşil) §7'deki iki çakışma yüzünden alınamadı;
ilerleme seri ailesinin kendi merdiveninde çizilir (koyu → orta → açık).

Ayrıca: **varsayılan görünüm "kompakt zincir"den "huni"ye alındı.** Zincir SALT METİNDİ (ölçüldü:
içindeki her boya gri/siyah) — operatörün gördüğü ve "gri" dediği şey oydu. Zincir silinmedi,
düğmesi duruyor.

## 9 · Tekrar eden manşet — "bu gerçekten gerekli mi?" DEĞİLDİ

Dört durum kartı Bugün'e taşınınca metrik şeridinin ÜÇ sekmesi manşet rakamı tekrarlamaya
başladı (Sermaye ↔ KİTAP · Gün K/Z ↔ KİTAP'ın gün satırı · Açık risk ↔ POZİSYONLAR). Şerit
SİLİNMEDİ — altındaki grafiğin seri seçicisidir — rakamı **mertebe düşürdü** (`--t-num` →
`--t-lg`). Manşet kartlarda, şerit kendi işine döndü.

## 10 · YEDİ YÜZEY — maketin kenar çubuğu gruplaması + Analiz sekmesi

Eski tek "Karar" alanı SEKİZ bölümle şişmişti ve içinde **üç ayrı soru** vardı. Maket bunları
ayırıyor; ayrıldı:

| yüzey | bölümler | sorusu |
|---|---|---|
| ② Portföy | brifing · mutabakat · intraemir | kitap nerede duruyor? |
| ③ Karar zinciri | adaylar · kapilar · onaylar | neden geçti ya da geçmedi? |
| ④ **Analiz** *(operatörün adıyla istediği)* | topviews · performans | ne birikti ve nerede? |

`portfoy` ALIAS OLMAKTAN ÇIKTI: 2026-08-24'te kendi DOM kabına geri döndü, yani eski
`portfoy#mutabakat` bağlarının hedefi artık gerçekten orada. Kısayollar yediye çıktı
(`p`=Portföy, `a`=Analiz); `y`=Kilitler tarihsel olarak korundu.

**Kart bütçesi BÖLÜNDÜ, artmadı:** eski `karar: 25` → `portfoy 11 + karar 10 + analiz 4 = 25`.
Toplamın korunması, hiç kart eklenmediğinin/silinmediğinin kanıtıdır.

## 11 · Doğrulama

* UI süpürmesi **1336 passed, 0 failed** (pano · uiux · ia · kart · s2r · cila · kabuk · göç ·
  kontrast · tipografi · jeton · renk · token · palet · csp)
* Tarayıcı: yedi yüzey çiziliyor, üç yeni/yeniden düzenlenen sayfanın bölümlerinin hepsi dolu,
  **düşen bölüm YOK**; huni 12 path (4 segment × 3 katman) ile maketin yapısında; gündüz+gece
  ölçüldü ve tüm yeni CSS jeton üzerinden.
