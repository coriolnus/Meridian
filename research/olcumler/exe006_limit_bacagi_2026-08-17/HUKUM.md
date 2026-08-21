# EXE-2026-006 — HÜKÜM (Rol-1, 2026-08-17)

Pencere 2022-01-01→2026-07-30 · evren 251 · K=8 (4 tavan × 2 dolum kuralı) · TAM koşum.

## KILL KRİTERLERİ — hepsi geçti

| kriter | sonuç |
|---|---|
| cap < `MAX_ENTRY_GAP_PCT` (ölü hücre yok) | ✅ 0,005/0,01/0,02/0,03 hepsi 0,04 altında |
| şasi kapısı yeniden koşuldu | ✅ her hücrede `frame_miss=0 dup=0 scan!=plan=0` |
| `state/goal.yaml` değişmedi | ✅ yasa yalnız süreç-içi yamayla |
| dolum kuralı tek yerde | ✅ `broker.fill_entry`; AST çivisi bekliyor |
| E1'in orijinal çıktısı ezilmedi | ✅ SANDBOX yönlendirmesi — yapısal |
| hüküm tek tavandan verilmedi | ✅ dört tavan |

## ÜÇ ÜRÜN

### Ö1 — ÖLÇÜLEMEDİ (kart tanımı bu veriyle hesaplanamıyor)

Kartın tanımı: *"kaçtı denilenlerin yüzde kaçı dinlenen limitle doluyor."* Hesap **birim
uyuşmazlığı** taşıyor: payda `entry_missed_limit` yani bir RED OLAYI sayacı (aynı plan günlerce
reddedilebilir), pay ise DİSTİNKT İŞLEM sayısı. Ham bölme %132 ve %141 verdi — bir oran %100'ü
aşamaz; bu bir sonuç değil, tanımın belirtisidir.
İKİNCİ KUSUR: yerinden-etme, HİÇ KAÇMAMIŞ işlemleri de içeri alıyor (aşağıya bak), yani pay saf
değil. Ö1 ancak kaçan PLANLARIN kimliği kaydedilirse hesaplanır — bugünkü ret sayacı kimlik
taşımıyor. **UYDURMA YASAĞI: None + neden.** Kartın "Ö1 > %20 ise K1 şerhi açılır" kuralı bu
turda İŞLETİLEMEZ.

### Ö2 — İŞARET ÖLÇÜLEMEDİ (CI sıfırı içeriyor)

Ay-kümeli bootstrap (B=5000, seed 20260812, yeniden örneklenen birim = AY):

| tavan | ort-R | CI95 | hüküm |
|---|---|---|---|
| 0,005 | −0,0436 | [−0,1870 · +0,0978] | 0 içinde |
| 0,01 | +0,0411 | [−0,1717 · +0,2788] | 0 içinde |
| 0,02 | +0,1007 | [−0,1977 · +0,3773] | 0 içinde |
| 0,03 | +0,1167 | [−0,1672 · +0,3839] | 0 içinde |

Nokta tahminleri pozitif ve tavanla ARTIYOR, ama dördü de sıfırdan ayrışmıyor.
**"Kaçanlar sistematik KAZANAN" da "sistematik KAYBEDEN" de SÖYLENEMEZ.** E1'in bu iddiası
DOĞRULANMADI ama ÇÜRÜTÜLMEDİ de — ölçüm ayırt edemiyor.
NOT: nokta tahminlerinin tavanla monoton artması bir DESEN'dir, hüküm değil; CI onu taşımıyor.

### Ö3 — ÖLÇÜLDÜ, SENTE KAPANDI

| tavan | YENİ | YERİNDEN | ORTAK Δ | TOPLAM ΔP&L | kapanış |
|---|---|---|---|---|---|
| 0,005 | −4.145 | +3.629 | +661 | **+146** | 0,00 |
| 0,01 | +3.127 | +2.202 | +1.834 | **+7.163** | −0,00 |
| 0,02 | +4.444 | +712 | +603 | **+5.759** | 0,00 |
| 0,03 | +5.931 | +1.694 | −269 | **+7.355** | −0,00 |

Üç bileşenin toplamı gerçek farkı SENTE kapatıyor (kartın Ö3 şartı).

**CI EKLENDİ (Ö-51c, 2026-08-21) ve HÜKMÜ SERTLEŞTİRDİ.** Eşlenik ay-kümeli bootstrap
(B=5000, seed 20260812, yeniden örneklenen birim = AY, 42 ay; iki kol AYNI ayı görür):

| tavan | ΔP&L | CI95 | hüküm |
|---|---|---|---|
| 0,005 | +146 | [−16.657 · +17.319] | 0 içinde |
| 0,01 | +7.163 | [−10.148 · +24.400] | 0 içinde |
| 0,02 | +5.759 | [−8.403 · +20.662] | 0 içinde |
| 0,03 | +7.355 | [−4.820 · +21.381] | 0 içinde |

**ΔP&L DE SIFIRDAN AYRIŞMIYOR.** Yukarıdaki "+7.163" bir NOKTA TAHMİNİDİR, kanıtlanmış para
DEĞİL. Bu satır, aşağıdaki hükmün ilk hâlinde eksikti ve düzeltildi: "ΔP&L dört tavanda da
POZİTİF" cümlesi anlamlılık İDDİA ETMİYOR ve etmemeli.
YAN KANAL BÜYÜK ve kartın "etki TOPLAMSAL DEĞİLDİR" beyanını doğruluyor: `cap=0,005`te 251 yeni
işleme karşı **154 işlem yerinden oldu**. Yerinden olanlar DÖRT TAVANDA DA kaybedendi
(ort-R −0,052 / −0,034 / −0,003 / −0,025), yani çıkmaları P&L'i İYİLEŞTİRDİ.
**ΔP&L dört tavanda da POZİTİF (nokta tahmini)** — CI 2026-08-21'de hesaplandı ve DÖRDÜ DE
sıfırı içeriyor; yukarıdaki tabloya bakın. İşaret tutarlı ama anlamlı DEĞİL.

## H1 — MONOTONLUK DÜŞTÜ

`dinlenen_limit` kolunda net P&L: 9.773 → **19.452** → 17.948 → 17.858. Tepe 0,01'de, sonra
azalıyor. E1'in "limit bacağı MONOTON zararlı" iddiasının monotonluk ayağı bu kolda AYAKTA DEĞİL.
(Not: bu tek başına E1'i çürütmez — E1 kendi penceresinde, kendi dolum kuralıyla koştu.)

## HÜKÜM

Kartın ölçümden ÖNCE yazdığı kural: *"H1 ve H2'nin İKİSİ de ayakta kalırsa E1 DOĞRULANIR;
biri düşerse hüküm YENİDEN AÇILIR."*

**H1 düştü** (monotonluk kırık). **H2 ölçülemedi** (CI sıfırı içeriyor) — yani "ayakta kaldı"
denemez. Kuralın şartı sağlanmadı.

→ **E1 HÜKMÜ YENİDEN AÇILIR.** Canlı yapılandırmanın (bacağın `limit_pct_cap=0.04` ile
etkisizleştirilmiş olması) gerekçesi ARTIK KANITLI DEĞİLDİR.

**BU KART BACAĞIN AÇILMASINI ÖNERMEZ** (kartın kendi sınırı). Açma kararı strateji kimliğine
dokunur ve §5 operatör bloğuna gider. Karara girmeden ÖNCE kapatılması gerekenler:
1. **Ö1 yeniden tanımlanmalı** — ret sayacı kimlik taşımalı, yoksa abartı oranı hiç ölçülemez.
2. ~~**ΔP&L için CI**~~ — ✅ KAPANDI (Ö-51c, 2026-08-21): dördü de sıfırı içeriyor. Sonuç
   hükmü DEĞİŞTİRMEZ ama GÜÇLENDİRİR: ne H2 ne Ö3 anlamlılığa ulaşıyor, yani "bacağı aç" kararı
   bu ölçümden TEK BAŞINA çıkarılamaz. Çıkaran tek ayak H1'in (monotonluk) kırılmasıdır.
3. Ö2'nin ölçülememesi bir SONUÇtur: örneklem bu soruyu ayırt edemiyor, daha fazla veri ya da
   farklı bir ölçüt gerekir.

## BU TURDA YAPILMAYANLAR (beyanlı)

- ΔP&L bootstrap CI'ı (kart istiyor, koşulmadı)
- Ö1'in kimlikli yeniden tanımı
- Duman penceresinin YANILTTIĞI kayda geçti: n=1..3'te Ö2 dört tavanda da NEGATİF görünüyordu;
  885 işlemlik dünyada işaret döndü ve CI'ya girince ÖLÇÜLEMEZ oldu. Küçük örneklem yalnız
  gürültülü değil, YÖN OLARAK YANILTICIYDI.
