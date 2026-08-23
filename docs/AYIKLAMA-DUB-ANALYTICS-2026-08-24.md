# DUB ANALYTICS → MERIDIAN AYIKLAMASI (2026-08-24)
_Kaynak: `https://dub.co/help/article/dub-analytics` · operatör talebi: "bütün sisteme uygulayabileceğimiz kısımlarını ayıkla"_

Dub'ın dokuz kavramı var. Üçü **doğrudan** alınır, dördü **uyarlanır**, ikisi **alınmaz** — her biri
gerekçesiyle. Sıralama değer/maliyet oranına göre.

---

## A. DOĞRUDAN ALINIR

### A1 · Üç görünüm modeli → Meridian'ın eksik iki görünümü
Dub: *zaman serisi · toplulaştırılmış facet'ler (Top Views) · gerçek-zamanlı olay akışı.*
Meridian'da **zaman serisi var** (sermaye eğrisi), diğer ikisi **yok**:
- **TOPLULAŞTIRMA (Top Views)** — en yüksek değerli eksik. Meridian karşılıkları:
  kurulum · çıkış nedeni · sektör · rejim · **kapı reddi** · sembol. Her biri için n · toplam R ·
  PF · kazanma. Bunlar bugün elle, ölçüm kartlarında hesaplanıyor; panoda olsalar "neyim
  çalışıyor" sorusu tek bakışta cevaplanır. **Kapı-reddi dökümü** ayrıca "neden az işlem
  açılıyor"un doğrudan cevabı.
- **OLAY AKIŞI** — `state/events.jsonl` zaten var, panoda düzgün yüzeyi yok. Filtreli canlı akış
  = "sistem şu an ne yapıyor".

### A2 · Filtre çubuğu (facet'li, klavye dostu)
Dub'ın facet'leri Meridian'a birebir çevrilir: **kurulum · sektör · rejim · çıkış nedeni ·
kapı hükmü (PASS/REVIEW/BLOCK) · kaynak (replay_seed/live_paper) · sembol · tarih aralığı**.
Değeri: bugün her dilim sorusu ölçüm kartı yazmayı gerektiriyor; filtre çubuğu keşif turunu
saniyelere indirir. **Şart:** filtreli görünüm bir HÜKÜM kaynağı değildir — yüzeyde
"keşif görünümü · hüküm kart-önce" damgası zorunlu (ölçüm-bağlamı tuzağı).

### A3 · Filtrelerin görünümler arasında taşınması
Dub'da "View Events" tıklanınca Analytics'teki filtreler Events'e taşınıyor. Meridian karşılığı
tasarımın omurgası olur: **huni aşamasına tıkla → o aşamanın olayları/planları filtrelenmiş
gelsin**; Top Views'ta bir kuruluma tıkla → tüm pano o kuruluma filtrelensin. Üç-katmanlı
mimarinin (şu an → alanlar → kanıt) "bağlamı kaybetmeyen iniş" mekanizması budur.

---

## B. UYARLANIR

### B1 · Tarih aralığı seçici + klavye kısayolları
Dub: D/W/T/3/L/M/Q/Y/A. Meridian'da takvim günü değil **SEANS** birimdir; uyarlama:
`B` bugün · `5` son 5 seans · `A` son ay · `Ç` çeyrek · `H` tüm zaman.
**Meridian'a özgü iki aralık** (Dub'da yok, bizde çok değerli): **"son dağıtımdan beri"**
(`dagitim.json`'daki `deployed_sha` damgasından) ve **"taban dondurulduğundan beri"**
(edg032c künyesi) — "değişiklik işe yaradı mı" sorusu bugün elle kuruluyor.

### B2 · Gelişmiş filtreler (IS ONE OF / IS NOT)
Çoklu ve olumsuz filtre Meridian'da doğrudan ölçüm dilinin karşılığı:
"pullback HARİÇ tüm kurulumlar" (B1 kararının görsel hâli) · "chop VE high_vol" ·
"stop_gap HARİÇ çıkışlar". Kart yazarken yaptığımız dilimlemenin tam kendisi.

### B3 · CSV dışa aktarma
Alınır ama **damgalı**: dışa aktarılan dosyanın başlığına filtre kümesi + koşum zamanı +
`deployed_sha` gömülür. Damgasız export, ölçüm dizinlerine karışıp "bu sayı nereden geldi"
sorusunu cevapsız bırakır (bu depoda o sınıfın adı var: bayat-artefakt).

### B4 · Huni üzerinde % etiketleri
Dub şeridin ÜSTÜNDE `100% / 63.52%` yazıyor. Bizde de eklenir — ama **karekök ölçek beyanıyla
birlikte** (genişlik oranı ≠ yüzde; Dub bunu söylemiyor, biz söylemek zorundayız).

---

## C. ALINMAZ

### C1 · Herkese açık paylaşılabilir pano — HAYIR
Dub'ın shareable link'i pazarlama/müşteri paylaşımı içindir. Meridian tek-operatörlü ÖZEL bir
alım-satım sistemi; pozisyon ve sermaye yüzeyi dışarı açılmaz. Zaten `/api/public/summary` +
landing sayfası kamuya dönük ölçülmüş özeti veriyor — ikinci bir kamu yüzeyi risk ekler, bilgi
eklemez.

### C2 · "Ask AI" doğal dil sorgusu — ŞİMDİLİK HAYIR (koşullu evet)
Cazip ama tehlikeli: LLM'in seçtiği filtreyle çıkan sayı, kart disiplininden geçmeden "kanıt"
gibi okunur — bu deponun `ölçüm-bağlamı tuzağı` dediği şeyin ta kendisi. **Koşullu kabul:**
yalnız keşif kipinde, çıktının üstünde sabit "KEŞİF — HÜKÜM DEĞİL" damgası ve seçilen filtrenin
açıkça yazılması şartıyla. Öncelik: düşük.

---

## ÖNERİLEN SIRA (değer/maliyet)
1. **A1-Top Views** (kurulum · çıkış nedeni · kapı reddi) — en yüksek bilgi, orta maliyet
2. **A2 filtre çubuğu** + **B2 IS ONE OF / IS NOT**
3. **A3 filtre taşıma** (huni→olaylar, Top View→pano)
4. **B1 seans-tabanlı aralıklar** + iki Meridian-özgü aralık
5. **A1-olay akışı** yüzeyi
6. **B3 damgalı export** · **B4 % etiketleri** (ikisi de küçük)
7. C2 ancak damgayla, en sonda

---

## EK · CANLI DEMODAN ÖLÇÜLEN YAPI (2026-08-24)
_Kaynak: operatörün paylaştığı `app.dub.co/share/dash_6NSA6vNm017MZwfzt8SubNSZ` — DOM'dan okundu,
ekran görüntüsünden tahmin edilmedi._

Yukarıdaki A1 "Top Views" soyut kalmıştı. Demo üç şeyi kesinleştirdi:

### E1 · Facet AİLESİ kartı — sekmeli, tek metrik sütunlu
Toplulaştırma tek bir liste değil, **üç panel kartı**; her kart bir AİLE, kartın üstündeki
sekmeler o ailenin boyutları, sağda tek metrik sütunu (`CLICKS`), satırlar azalan sırada,
kesildiğinde `View All`:

| Dub kartı | sekmeleri | **Meridian karşılığı** | sekmeleri |
|---|---|---|---|
| Referrers | Domain · URL | **KAYNAK** | Kurulum · Rejim · Sektör |
| Countries | Cities · Regions · Continents | **SONUÇ** | Çıkış nedeni · Tutma süresi · R kovası |
| Devices | Browsers · OS · Triggers | **KAPI** | Kapı reddi · Kapı hükmü · Kaynak (replay/canlı) |

Metrik sütunu Meridian'da `CLICKS` değil **n** (varsayılan) — sütun başlığı metriği ADIYLA yazar
ve değiştirilebilir (n · toplam R · PF · kazanma). Bu, "hangi metriğe bakıyorum" sorusunu
yüzeyde tutar; Dub tek metrikli olduğu için bu soruyu hiç sormuyor, biz sormak zorundayız.

### E2 · Oran çubuğu AYRI SÜTUN DEĞİL, SATIRIN ZEMİNİ
Ölçülen DOM: satırın içinde mutlak konumlu bir kutu, `width:40.8%`, `-z-10`, yumuşak mavi dolgu.
Yani sayı ve etiket çubuğun ÜSTÜNDE durur; tablo bir sütun genişliği kaybetmez.
Meridian'da bu dolgu **ROL 6** jetonudur (`--nav-t`) — gezinme/seçim kanalı. Bir para değeri
ya da şiddet ASLA bu çubuğa binmez; çubuk "bu satır kümenin ne kadarı" der, "iyi/kötü" demez.

### E3 · SATIRIN KENDİSİ BİR FİLTRE KONTROLÜ
Ölçülen DOM: `aria-label="Add filter: United States"`, `aria-pressed`. Satıra tıklamak o değeri
**filtreye ekler**; hover'da sol kenar 2px vurgulanır ve içerik sağa yer açacak şekilde daralır.
A3'ün ("filtrelerin görünümler arası taşınması") somut hâli budur ve **bizde daha değerlidir**:
"kapı reddi" listesinde `earnings_blackout` satırına tıklamak tüm panoyu o redde filtreler —
"neden az işlem açılıyor" sorusu tek tıkla cevaplanır.

**Erişilebilirlik borcu (Dub'da var, bizde olacak):** satır bir `button` ve `aria-pressed`
taşıyor. Tıklanabilir satırı `div` yapmak bu deponun civilerinden geçmez.
