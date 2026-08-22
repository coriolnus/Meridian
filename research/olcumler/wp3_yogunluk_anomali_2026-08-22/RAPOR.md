# WP3 — YEREL↔CANLI REPLAY YOĞUNLUK ANOMALİSİ TEŞHİSİ (ölçüm kaydı, 2026-08-22)

Hüküm YOK — hüküm Rol-1'in. Bu dosya yalnız ölçümdür. (28g-i yan bulgusunun takibi;
ROADMAP:196 satırındaki "aynı holdout penceresi yerel n=21 / canlı n=249 — 12×" iddiası sınandı.)

## SONUÇ ÖNCE: elma-armut mu, gerçek anomali mi?

**İkisi de — iki ayrı katmanda:**

1. **PENCERE ETİKETİ YANLIŞ (elma-armut, kayıt düzeyinde):** 21 ve 249 sayılarının İKİSİ DE
   holdout penceresinin (2026-04-30→07-30) DEĞİL, **fold3-FULL penceresinin (2025-07-01→2026-04-30)**
   sayılarıdır. Kaynak zinciri: `docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md:476-477`
   (`oos_folds_full` fold3: n=249) → `ROADMAP.md:1780` (madde #47, pencereyi doğru anar) →
   `ROADMAP.md:196` (öneri-havuzu satırı pencereyi "holdout" diye ETİKETLEMİŞ — yanlış).
   Holdout penceresinin gerçek çifti: yerel **n=5** vs canlı **n=87** (17,4×).
2. **YOĞUNLUK FARKI GERÇEK ama YEREL↔CANLI FARKI DEĞİL, ESKİ-DÜNYA↔YENİ-DÜNYA FARKI
   (bağlam-tuzağı sınıfı, "bayat önbellek" alt türü):** iki sayı da REPLAY'dir (inc_cache
   walk_forward), fakat FARKLI KONFİGÜRASYON ÇAĞLARINDA koşulmuştur. Yerel inc_cache
   **2026-07-29T23:54Z**'de (rev=1785369283), incumbent **v3** (`position_size_r=1.0`) ve o günün
   yasasıyla (E1 limit bacağı BAĞLAR 0,5·ATR/%1 · derisk rampası 0,03/0,08 · slot 5) hesaplanmış
   ve **bir daha tazelenmemiş**. Canlı inc_cache **2026-08-21T20:31Z**'de, incumbent **v5**
   (`position_size_r=0.5`) ve 2026-08-03..08-12 operatör paketiyle (E1 serbest 100/%4 ·
   rampa 0,15/0,36 · slot 20 · gap `marketable_limit`) hesaplanmış. Fark VERİDEN GELMİYOR:
   barlar iki dünyada 2021-01-01→2026-07-28 bire bir aynı (wp3_28d ölçümü), evren iki tarafta
   251, goal/bounds/strategy.yaml sha'ları bugün BİREBİR eşit (aşağıda).
   **Kontrollü A/B (bu ölçüm): aynı barlar + aynı kod + aynı pencerede yalnız konfig çağını
   değiştirmek yoğunluğu 23↔90 (holdout, soğuk başlangıç) taşıyor** — yön ve büyüklük paketle
   açıklanıyor; kalan çarpan yürüyüş-mirası durumdur (aşağıda §4).

## 1. Girdi kıyası (ölçülen)

| girdi | yerel | canlı (A1) | fark? |
|---|---|---|---|
| `state/bars/` dosya sayısı | 260 | 260 | yok |
| bars son-bar | 2026-07-28 ×207 · 07-29 ×43 (mtime 07-29/30; spy 08-12) | 2026-08-21 ×249 | yalnız TAZELİK; kıyas pencereleri (≤2026-04-30) bire bir aynı seri (wp3_28d: 2021-01-01→2026-07-28 AYNI) |
| bars ilk-bar (CSV) | 2004-01-02 ×198 | — | replay tabanı FETCH_START=2021-01-01'e kırpar (dataset.py:40); A/B koşumu da kırptı |
| REPLAY_UNIVERSE | 251 | 251 (ssh ile canlı import) | yok |
| RETIRED_SYMBOLS | 8 | 8 | yok |
| `goal.yaml` sha256[:16] | 0f0a7b4bd912d6bd | 0f0a7b4bd912d6bd | yok (exe003 kopyasıyla diff de boş) |
| `bounds.yaml` | 3acb44b141e09227 | 3acb44b141e09227 | yok |
| `strategy.yaml` | 758d30c39c18c4fd (v5) | 758d30c39c18c4fd (v5) | yok |
| **`inc_cache.json`** | **rev 2026-07-29T23:54Z · 3 giriş · anahtar sv=3, psr=1.0 · hedef izi max_dd=0.08 (ESKİ goal)** | **rev 2026-08-21T20:31Z · 1 giriş · anahtar sv=5, psr=0.5** | **TEK GERÇEK FARK: önbellek ÇAĞI** |

Yerel↔canlı inc girişleri arasında parametre farkı YALNIZ `position_size_r` (1.0 vs 0.5; ölçüldü,
diğer 17 param birebir). Anahtar dışı girdiler (goal limits: max_open, derisk bandı, execution_v2)
koşum ANINDA `config.goal()`dan okunur — yani aynı anahtar biçimi farklı çağlarda farklı dünyalar ölçer.

## 2. İki dünyanın sayıları (inc_cache replay'leri; aynı geometri R1)

| dilim | yerel (07-29, v3+eski yasa) | canlı (08-21, v5+yeni yasa) | oran |
|---|---:|---:|---:|
| replay TOPLAM (2022-01-01→2026-07-30) | 163 | 886 | 5,4× |
| fold3-SEARCH (2025-07-01→2025-08-18) | 2 | 36 | 18× |
| **fold3-FULL (2025-07-01→2026-04-30)** — ROADMAP:196'nın penceresi | **21** | **249** | **11,9×** |
| holdout (2026-04-30→2026-07-30) | 5 (→ skor None, n<30) | 87 (skor −0,5537) | 17,4× |

## 3. "Canlının 249'u defter mi replay mi?" — NETLEŞTİRİLDİ

- 249 = canlı `inc_cache.oos_folds_full[2].n` → **REPLAY** (reflect'in incumbent walk'ı).
- Canlı İŞLEM DEFTERİ (exe003 DB kopyası, salt-okuma): aynı pencerede ts_close yasasıyla **255**,
  holdout'ta **97** (ts_open ile 265/87). Yani 249 ≠ defter satırı; ama...
- **Defterin kendisi de replay'dir:** `trades.kaynak` dağılımı **885 `replay_seed` + 8 `live_paper`**
  (canlı-kâğıt işlemler yalnız 2026-08-06'dan itibaren). 885 = `edg032_final_paket_2026-08-12`
  C+mb koşumunun satır sayısı (ROADMAP:1881) — defter 08-12'de o replay'le YENİDEN TOHUMLANDI.
  Canlı inc walk toplamı 886 ≈ tohum 885: canlı tarafta defter≈replay OLUŞUM GEREĞİ (28g-i'nin
  "vekil DB dilimi inc skorunu 0,0001 farkla üretti" bulgusunun mekanik açıklaması budur —
  mucizevi örtüşme değil, aynı motor+aynı konfig).

## 4. Kaynağın daraltılması — kontrollü A/B (yerel, dar pencere; `olcum_ab.py` → `sonuc_ab.json`)

Aynı barlar (yerel CSV, 2021-01-01'e kırpık) + aynı kod + soğuk başlangıç; yalnız konfig değişir.
Holdout penceresi (2026-04-30→07-30, 62 seans):

| kol | konfig | kapanan işlem | başat NO_GO nedenleri | dolum retleri |
|---|---|---:|---|---|
| A yeni dünya | v5 (0,5R) + bugünkü goal (slot 20 · rampa 15/36 · E1 serbest · mb) | **90** | ısı 5R tavanı 19 · sektör 1 | max_chase 14 |
| B eski dünya | v3 (1,0R) + eski yasa (slot 5 · rampa 3/8 · E1 bağlar 0,5·ATR/%1 · cancel) | **23** | sektör tavanı 38 (payda slot5→2 isim) · "max 5 pozisyon dolu" 16 · ısı 5 | **entry_missed_limit 9** · max_chase 6 |
| C eski + E1 serbest | tek düğme | 34 | sektör 47 · slot 24 | — |
| D eski + rampa 15/36 | tek düğme | 44 | sektör 43 · slot 42 | entry_missed_limit 13 |
| E eski + slot20/0,5R | tek düğme (paket yarısı) | 66 | ısı 10 · sektör 7 | entry_missed_limit 22 |

Okuma (ölçüm, hüküm değil): yeni dünya YEREL veriyle canlının holdout yoğunluğunu yeniden üretiyor
(90 ≈ canlı 87/97) → **yerel veri "kuru" DEĞİL**. Eski dünyada kesen kapılar sırayla:
slot5+1,0R paketi (sektör-tavanı paydası 2 isme iner + slot doluluğu + ısı) > rampa 3/8 >
E1 limit bacağı (dolan plan kaçırıyor). Soğuk başlangıçta 23'e iner; yürüyüşün kendi içinde 5'e
inmesinin kalan çarpanı YÜRÜYÜŞ-MİRASI durumdur: 2022'den gelen walk pencereye birikmiş dd
(yerel walk max_dd %5,2-6,9 → 3/8 rampasında boy çarpanı ~0,6→0,2 bandı) ve dolu slotlarla girer —
soğuk başlangıç bunu ölçemez (sınır BEYANLI, `olcum_ab.py` docstring).

fold3-FULL penceresi (2025-07-01→2026-04-30, ~210 seans — 21-vs-249'un ASIL penceresi) iki uç dünya:

| kol | kapanan işlem | kıyas | başat NO_GO |
|---|---:|---|---|
| F3_A yeni dünya (v5 + bugünkü goal) | **263** | canlı replay 249 · canlı defter 255 — YEREL VERİYLE YENİDEN ÜRETİLDİ | ısı 5R tavanı ~157 |
| F3_B eski dünya (v3 + eski yasa) | **57** | yerel walk'ın aynı penceredeki sayısı 21 | **"max 5 pozisyon dolu" 150** · ısı ~71 · sektör 27 · entry_missed_limit 10 |

Konfig çağı tek başına soğuk başlangıçta 263/57 = **4,6×** veriyor; 57→21 kalanı yürüyüş-mirası
(eski-dünya walk'ı pencereye 2022'den birikmiş dd + dolu slotlarla girer; 3/8 rampası + slot 5
bunu bileşik büyütür). Yani 11,9×'in kaynağı = konfig paketi × yürüyüş-mirası durumu; veri bacağı SIFIR.

## 5. Ölçülemeyenler (uydurma yasağı)

- Yerel 21/5 sayılarının BİREBİR yeniden üretimi: None — 2022'den tam yürüyüş gerektirir
  (yerelde ~27-100 dk sınıfı; 15 dk teşhis bütçesini aşar — koşulmadı, yukarıdaki soğuk-başlangıç
  A/B + izolasyon kollarıyla daraltıldı) ve eski-dünya yasası kod gövdesinden değil goal
  yamasıyla yeniden kurulur (gap_behavior'ın 07-29'daki fiili değeri git geçmişinden
  doğrulanamadı — git yasak; `cancel` varsayımı E1 "95/95 red" kaydına dayanır, beyanlıdır).
- 08-13 TESHIS anındaki canlı inc_cache'in kendisi: None — bugünkü canlı (08-21 rev) okundu;
  08-13 değerleri TESHIS belgesinden alıntıdır (oos +0,2354/holdout −0,5366 → bugün +0,2687/−0,5537;
  fark bar tazelenmesi/yeniden hesap, ölçülmedi).
