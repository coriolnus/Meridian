# PANO v2 — TASARIM YÖNÜ SÖZLEŞMESİ (2026-08-24)
_Operate yüzeyi · redesign · dünya operatörce sabitlendi (Dub) · ikili tema_

## Brief (operatörden, 2026-08-24)
- **İlk 5 saniye iki soruyu cevaplar:** "Param ne durumda?" + "Sistem bugün ne yaptı?"
- **Dört dert (hepsi işaretli):** ① çok fazla kart, hangisine bakacağım belli değil · ② rozet/etiket
  dili tutarsız · ③ sayılar var ama anlamı yok · ④ acil olan öne çıkmıyor.
- **Sahne:** masaüstü, hem gündüz aydınlık oda hem akşam/gece. → İKİ TEMA fiziksel sahnenin
  dayattığı cevaptır (tercih değil). Mobil öncelik yok.
- **Ölçülmüş dert kanıtı:** bugünkü kart sayacı (v198 tabanı) **karar 27 · sağlık 24 · öğrenme 45 ·
  kilitler 5 = 101 kart yüzeyi**, hepsi eşit görsel ağırlıkta. F8 ölçümü 17 mekanizmada 16 adlandırma
  tutarsızlığı buldu. M11 taraması panonun YANLIŞ rozet bastığını ölçtü (veto edilmiş plan
  "gönderilecek" görünüyor; keşif çipi 41 gün sıfır üretimde yanıyor).

## THESIS (2026-08-24 düzeltmesiyle)
Bu bir DÜNYA DEĞİŞTİRME DEĞİL — yerleşik dünya (Omega/Linear-Vercel-Raycast register) Dub ile AYNI
ailede; iş **aynı dünyanın daha iyi icrası** ve asıl hedef BİLGİ MİMARİSİ.
Pano bir **kart tarlası** olmaktan çıkıp bir **enstrüman paneli** olur: üç katmanlı okuma —
*şu an* (5 saniye), *alanlar* (30 saniye), *kanıt* (dakikalar). Reddettiği kategori-varsayılanı:
"her ölçüm bir kart, tüm kartlar eşit" düzeni. Yoğunluk azalmaz, **hiyerarşi kazanır**;
bilgi silinmez, **katmana iner**.

## OWN-WORLD
Dub'ın yapısal grameri, kontrol yüzeyine uyarlanmış: elevasyon değil **hairline çizgi** (1px)
konteyner tanımlar · radius sözlüğü 9999/16/12/8/6px, dışı yok · 4px taban, kompakt yoğunluk ·
tek aksan (elektrik mavisi) yalnız *dikkat* ve *aktif durum* için — dekoratif kullanım yasak ·
rakamlar **mono** (tabular-nums, hizalı sütun) — sayı bir malzemedir, metin değil · tipografi
Inter/sistem yığını (Satoshi DÜŞÜRÜLDÜ: CSP harici font yasağı + panoda 36px+ display yok).
İki tema **ZATEN KURULU** (45 renk jetonu × 2 tam palet, `data-theme="gece"`; varsayılan AÇIK zemin —
Omega dönüşümü 2026-07-27). Bu redesign temayı KURMAZ, mevcut iki paleti Dub değerlerine göre
YENİDEN AYARLAR; jeton değişikliği `index.html` iki `:root` bloğu + `tokens.json`'da EŞ ZAMANLI
(v153 eşitlik çivisi) ve kontrast `docs/kontrast-denetimi.md` usulüyle (WCAG 2.2, en kötü GERÇEK
bileşke zemin) yeniden ölçülür.

## STORY
Operatör panoyu açar → bir bandda parasını ve günün karar zincirini görür → müdahale gereken bir
şey varsa o band kırmızıya/turuncuya döner ve **ne yapılacağını** söyler; yoksa "müdahale gerektiren
yok" diye AÇIKÇA yazar → merak ederse alanı açar → kanıt katmanında bugünkü yoğun kartları bulur.

## FIRST VIEWPORT (kompozisyon)
1. **DİKKAT ŞERİDİ** (koşullu, tam genişlik): yalnız eylem gerektiren durumlar. Boşsa açık beyanla
   ("müdahale gerektiren yok · N bekçi yeşil · son kontrol HH:MM") — sessiz boşluk yok.
2. **PARA BANDI** (sol 2/3): sermaye · gün P&L · açık risk (R) · pozisyon n — her sayı
   **MetricCell** bileşeniyle: değer + birim + bağlam (dün/tepe/eşik farkı) veya "ölçülemedi + neden".
3. **KARAR ZİNCİRİ** (sağ 1/3): tarandı → planlandı → onaylandı → gönderildi → doldu → çıktı;
   her adım sayı + zincirin NEREDE durduğu vurgulu. "Sistem bugün ne yaptı" tek bakışta.
4. Altında **dört alan sekmesi** (Karar · Sağlık · Öğrenme · Kilitler), her biri tek kanonik
   durum satırıyla kapalı gelir.

## FORM
Üç-katmanlı enstrüman paneli; sabitlenmiş dünya (Dub) + kontrol-odası doktrini (koyu varsayılan,
alarm ışıkla değil **renk+kontrast+ikon üçlüsüyle** taşınır — açık temada da geçerli).

## DÖRT DERDE KARŞILIK GELEN DÖRT MEKANİZMA
| dert | mekanizma |
|---|---|
| ① 101 eşit kart | üç katman + alan sekmeleri; kanıt kartları katman-3'e iner (silinmez) |
| ② tutarsız dil | **tek rozet grameri**: biçim=sınıf, renk=önem, metin=kanonik sözcük — kaynağı bugün kurulan `meridian/durum_sozlugu.py` (eşanlamlılar sayaçlı okunur) |
| ③ anlamsız sayı | **MetricCell**: her sayı bağlamıyla doğar (eşik/dün/n) ya da "ölçülemedi + neden" — dürüstlük yasası bileşene gömülür |
| ④ acil öne çıkmıyor | önem YALNIZ dikkat şeridi + rozet renginde ifade edilir; başka hiçbir yüzey "bağırmaz" |

## DEĞİŞMEZLER (kırılamaz)
None ≠ 0 · "ölçülemedi" ayrımı · provenance/kaynak rozetleri · nabız-bayat beyanı · sermaye-köken ·
v196 çırçır tavanı · v197 koşulsuz-emisyon kapısı · v198 kart tabanı (yeni sayı BEYANLI güncellenir) ·
v194/v205 yerleşim-taşma · CSP `script-src 'self'` (CDN/inline yok; font yerel ya da sistem yığını) ·
tabular-nums.

## FINISH
unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
