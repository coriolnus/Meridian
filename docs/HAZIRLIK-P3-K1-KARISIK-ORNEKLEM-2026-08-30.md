# KARAR DOSYASI — EDG-2026-042 P-3: K1'in karışık örneklemi

**Hazırlayan:** `ai-trading-85` (yan oturum) · **2026-08-30** · **Karar mercii:** operatör
**Uygulayacak:** Rol-1 (`ai-trading-dc`) — bu belge karta YAZMAZ, kart metnini Rol-1 işler.
**Kaynak:** `research/olcumler/edg042_kosum_2026-08-29/` (snapshot sha `3a1f06bf…`, salt-okuma)
**Bu belge hüküm ÜRETMEZ.** Eşik, karar kuralı, kill kriteri hiçbir kartta değiştirilmedi.

---

## 1. Karar nedir

2026-08-23T14:53:43Z'de (canlı `barclock.py` mtime) giriş bacağının icra mekanizması DEĞİŞTİ:
EOD gönderilen GTC emrin açılışta dolması → 13:45 penceresinde gönderim. EDG-042'nin K1 kovası
ikisini AYIRMADAN tek medyanda topluyor. Kartın kendi kill#5'i kovalar ARASI karışımı yasaklar
("mekaniği ayrı, tek medyana ezilemez"); kova İÇİ karışımın kuralı YOK.

Karar eşik dolmadan verilmeli: sonra vermek, **sayıya bakarak kural seçmek** olur.

---

## 2. ÖNCE BİR DÜZELTME — verdiğim eşik tahmini yanlıştı

2026-08-29 raporunda ve o gün karta/ROADMAP'e işlenen metinde **"K1 eşiği ~3-4 hafta"** yazıyor.
O tahmin "bu hafta +4 satır geldi" gözlemine dayanıyordu. **Dördün ikisi (DE, PANW) kaydırma
ÖNCESİ gönderilmişti** (`ts=2026-08-21T20:32:22Z`) ve o yol artık YOK — bir daha o hızda satır
gelmeyecek. İleriye dönük hız yalnız 1345 yolunun hızıdır.

**Ölçüm (2026-08-30, snapshot `3a1f06bf…`):**

| | kaydırma öncesi | kaydırma sonrası (gerçek 1345) |
|---|---|---|
| dönem | 08-05…08-21 (13 seans) | 08-24…08-28 (5 seans) |
| dolum | 15 | 2 |
| **dolum/seans** | **1,15** | **0,40** |
| plan-günü | 5 | 2 |
| plan-günü/seans | 0,38 | **0,40 — AYNI** |
| **plan-günü başına dolum** | **3,0** | **1,0 — DÜŞEN BU** |

Ayrışma öğretici: plan üretim sıklığı DEĞİŞMEDİ; düşen, bir plan-gününün kaç doluma dönüştüğü.
Yani kaydırma plan üretmeyi değil, planların doluma dönüşmesini seyreltiyor.

**MEKANİZMA ÖLÇÜLMEDİ.** E2 defterinde 36 satırın tamamı `submitted`+dolu; reddedilen/veto edilen
ayna satırı HİÇ yok, yani "kaç plan gönderilemedi/dolmadı" defterden okunamıyor. Seyrelmenin
sebebi (09:45'te tetiğin geçmiş olması? veto? plan sayısı?) bu kartla ölçülmez — yalnız SONUCU
ölçüldü. Ayrı kalem adayı.

**ÖRNEKLEM UYARISI: hız tahmini n=2 dolum / 2 plan-günü üzerine kurulu.** Bu bir hız değil, bir
işarettir. Aşağıdaki takvimler bu yüzden BANT olarak verildi: alt sınır gözlenen 1345 hızı,
üst sınır kaydırma-öncesi hız (iyimser tavan — kaydırmanın hiçbir etkisi olmadığı varsayımı).

---

## 3. Üç yol aslında İKİ yol

Kartta sunduğum (a) "K1'i ikiye ayır" ve (c) "kaydırma-öncesini dondur" yolları, uygulamada
**aynı sonuca** çıkıyor: kaydırma-öncesi küme 15 satırda DONUK kalır (o yol artık üretmiyor),
n=15 < 30 — yani **hiçbir zaman hüküm üretemez**, betimleyici kalır. İkisi arasındaki tek fark,
o donuk kümenin haftalık raporda gösterilip gösterilmemesi. Karar bu yüzden ikili:

| | **POOLED** (yol b) | **AYRIK** (yol a ≡ c) |
|---|---|---|
| K1 neyi ölçer | dönemin friksiyonu (iki mekanizmanın karışımı) | yürürlükteki rejimin friksiyonu |
| bugünkü n | 17 (15 eski yol + 2 yeni) | 2 |
| eşiğe (n=30) | **~6,5 hafta** (bant: 2,3–6,5) → ~2026-10-15 | **~14 hafta** (bant: 4,9–14) → ~2026-12-06 |
| seans eşiği (≥10) | 7→10, bağlayıcı DEĞİL (~1,5 hafta) | 2→10, bağlayıcı değil (n bağlayıcı) |
| eski 15 satır | hükme KATILIR | donuk, kalıcı betimleyici taban |
| hükmün anlamı | hüküm indiğinde 30 satırın 15'i **artık kullanılmayan** bir icra yolundan | yalnız canlıda koşan yoldan |
| kartsal maliyet | yok — bugünkü hâl, üstüne zorunlu şerh | `ts` alanı donuk çekicide YOK (`canli_cek.py`), reçete revizyonu ister |

**Takas tek cümleyle: ~7,5 hafta hız, saflık karşılığında.**

---

## 4. (a)'nın gizli tuzağı — okunmadan seçilirse 13 satır yiter

"K1'i `pencere` DAMGASINA göre ayır" literal olarak uygulanırsa: 1330 kolu yalnız DE/PANW olur
(düzeltme sonrası n=2), 1345 kolu n=2, ve **kaydırma öncesi 13 satır damgasız oldukları için her
iki koldan da düşer** (EXE-009 kill#3 geriye dönük etiketlemeyi yasaklar). 17 satırlık örneklem
4'e iner.

**Doğru ayırma anahtarı damga değil `ts`dir.** Gönderim zaman damgası defterde ZATEN dolu ve
rejim sınırı ÖLÇÜLMÜŞ bir an: canlı `barclock.py` mtime `2026-08-23T14:53:43Z`. `ts` < o an →
eski yol; ≥ → 1345. Bu bir etiket YAZMAK değil, ölçülmüş iki olguyu karşılaştırmaktır; kill#3'e
girmez. **Bedeli:** `ts`, EDG-042'nin donuk çekicisinin (`canli_cek.py`) alan listesinde YOK —
AYRIK yolu seçilirse reçete revizyonu ve yeni bir donuk sha gerekir.

---

## 5. Yol DIŞI sayılan dördüncü seçenek (ve nedeni)

"1345 satırları için paydayı 09:45 referansına çevir, sürüklenmeyi friksiyondan ayır."
**YASAK — EDG-042 kill#1:** payda EDG-038'in ön-kayıtla donmuş D1 konsolide açılışıdır; koşum
günü tarihçe yeniden çekilip payda türetilirse PIT ihlali + yaltaklanan-ölçüt tuzağı. Ayrıca
EXE-009 sürüklenme bedelinin fiyata gömülü gelmesini BİLEREK seçti. Bu yol ancak yeni bir kartla
açılır ve bu kartın hükmünü taşımaz.

---

## 6. Hangi soruya cevap istiyoruz — asıl ayrım burada

İki farklı soru var ve karar hangisini sorduğumuza bağlı:

* **"Canlı paket başabaşı geçiyor mu?"** → yürürlükteki rejimin friksiyonu gerekir. Bugün canlıda
  YALNIZ 1345 koşuyor. POOLED hüküm bu soruya, yarısı emekli bir dünyayla cevap verir.
* **"Dönem boyunca friksiyon neydi?"** → POOLED doğru cevabı verir, ama bu soru canlı para kararı
  değil, tarihçedir.

EDG-042'nin karar kuralı EDG-040'ın başabaş bandına ([5-15] bps/bacak) karşı konumlanır ve o
band "friksiyon kenarı öldürür mü" sorusudur — yani **birinci soru**. Kartın kendi asimetri
beyanı da ("başabaşın üstünde = canlı para negatif beklentiyle dönüyor") birinci soruyu işaret
eder.

Not: her iki yolda da çıkan sayı `goal.slippage_bps` sabitini DEĞİŞTİRMEZ — kart bunu zaten
beyan ediyor. Yani bu karar "slipaj modelimiz doğru mu" sorusunu çözmez, çözmeyi de amaçlamaz.

---

## 7. Önerim (karar değil)

**AYRIK (yol a ≡ c), `ts` anahtarıyla** — çünkü kartın karar kuralının bağlandığı soru birinci
sorudur ve POOLED hüküm o soruya yarısı emekli bir örneklemle cevap verir. 15 satırlık
kaydırma-öncesi küme SİLİNMEZ: kalıcı, damgalı, betimleyici taban olarak her koşumda yayımlanır
(hüküm taşımaz — n=15 < 30 ve bir daha büyümeyecek).

**Bunun açık bedeli:** canlı para sorusuna hüküm ~14 haftaya (≈ Aralık başı) kayar; bant iyimser
uçta ~5 hafta. Operatörün bu bedeli görmeden seçmemesi için buraya yazıldı.

**Bedeli hafifletmek isteniyorsa** (ayrı ve ÖN-KAYIT gerektiren bir karar): 1345 kolu için
haftalık bir ARA İŞARET tanımlanabilir — ör. "1345 betimleyici medyanı K ardışık hafta boyunca
15 bps'in üstünde kalırsa operatöre bayrak" (hüküm değil, bakma daveti). **Eşiği ve K'yı
seçmenin tek dürüst anı ŞİMDİ**, veri gelmeden. Sonra koymak, yine sayıya bakarak kural
seçmektir. Bunu istemiyorsan hiç koymamak da tutarlı bir seçimdir — ama o zaman Aralık'a kadar
K1'den hüküm gelmeyeceği bilinerek seçilmiş olur.

---

## 8. Karar verilince yapılacaklar (Rol-1)

1. Seçilen yol EDG-042 kartına işlenir; `acik_kalem_p3_k1_karisik_ornekem_2026_08_29` bloğuna
   hüküm ve gerekçe yazılır (eşikler/karar kuralı DEĞİŞMEZ, kova tanımı netleşir).
2. AYRIK seçilirse: `canli_cek.py`ye `ts` eklenir, yeni donuk sha KOMUT.txt'e yazılır, önceki
   reçete dizini dokunulmadan kalır (emsal: `edg042_recete_short_2026-08-24/`).
3. **DÜZELTME:** kartın `haftalik_kosum_2026_08_29` bloğundaki ve ROADMAP §2 Ö-54 satırındaki
   "**~3-4 hafta**" izdüşümü BAYAT — §2'deki ölçümle değiştirilmeli (POOLED ~6,5 hafta bandı
   2,3–6,5; AYRIK ~14 hafta bandı 4,9–14).
4. Ara işaret seçilirse: eşiği ve K'sı karta ÖN-KAYITLA yazılır, veri gelmeden.
