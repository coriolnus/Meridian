# GECE RAPORU — 2026-08-12/13 (tam otonom tur)

Operatör talimatı: "sabaha kadar bütün hepsinin düzelmiş olmasını istiyorum, full otonomi yetkin var."
Bu belge sabah okunacak tek özet. Ayrıntı: ROADMAP §2, kartlar, üç denetim dosyası.

## 1. CANLIYA İNEN (iki dağıtım, ikisi de otoriter-suite kapısından)

**Dağıtım #1 (20:13Z) — C+mb @5R paketi:** momentum_burst SİLAHLI · slot 20 · 0,5R (strategy v5) ·
rampa 15/36 goal-kablolu (TEK rampa, mod ayrımı yok — operatör kararı).
**Dağıtım #2 (01:26Z) — v238 + v239 + max_drawdown 0,16.** Canlı doğrulama (dağıtım sonrası okundu):

| yüzey | canlı değer |
|---|---|
| goal.max_drawdown | **0,16** (operatör kararı; ölçülen dd %12,7 × ~1,3 tampon) |
| max_open / position_size_r | 20 / 0,5 (strategy v5) |
| derisk rampası | 0,15 / 0,36 (goal-kablolu) |
| ARMED_SETUPS | 4'lü (mb dahil) |
| canonical_model("gemini-3.5-flash") | → **gemini-flash-latest** (ölü ad göçüyor) |
| divergence (8. desen) | 3 eşit / 0 ayrık / 1 beyanlı-ayrı |

## 2. KAPANAN ARIZALAR (hepsi kök-kanıtlı, hiçbiri "muhtemelen")

1. **KARNE SÜRÜM SPLIT'İ** — motor v5 ile karar verirken öğrenme/karne/rollback katmanı "v3" sanıyordu.
   Kök: mini-pencerede scp'lenen `scoreboard.json`'u bayat-defter migrasyonu `.migrated`'a taşıdı ve
   DB'ye yazmadı. Uygulamanın kendi yazım kapısından düzeltildi, v3/v4 tarihçesi korundu.
2. **EVREN DENETİMİ ÖLÜYDÜ (survivorship kanıtı üretmiyordu)** — pandas 3.0'da `read_html` ham HTML
   dizgesini DOSYA YOLU sanıyor. "lxml eksik" iddiası ESKİMİŞTİ ve gerçek kökü aylarca maskeledi.
   `io.StringIO` + `flavor="lxml"`. NOT: canlı `universe_drift.json` hâlâ 20:46Z'den kalma — denetim
   henüz yeniden koşmadı; **sabah ilk doğrulama kalemi bu**.
3. **"UYGULA" DÜĞMESİ SESSİZ ÖLÜYORDU** — öneri üreticisi 3 eylem tanırken uygulayıcı 2 tanıyordu ve
   ret HTTP 200 ile dönüyordu (pano yalnız hata kodunda mesaj yazar). Sözlük tek kaynağa indi; `lean_in`
   ölçüldü (registry'de karşılığı YOK, motor registry'yi hiç okumuyor) → düğme kaldırıldı, dürüst not
   kondu; her ret artık 400/409 + gerekçe.
4. **SPRINT YETİM-RESTART'I KALICI BLOKLUYDU** — beyin 5 dk'da bir tur açtığı için "meşgul" bayrağı
   asla bayatlamıyordu, v235'in tetiği ölü mekanizmaydı. `mesgul` YÜK/YETKİ diye ayrıldı. KANIT: yeni
   sprint doğdu, skip sebebi `tetik_yok(gun=0<7)` oldu.
5. **GEMİNİ ÇAĞRI-ANI ÖLÜ MODEL** — v235 göçü yalnız ajan config'ini onarıyordu; SIR yolu açıktı ve
   `GEMINI_MODEL` de ölüydü (doğrudan HTTP çağrısı da 404). Tek kapı (`canonical_model`).
6. **PANO AYNA ROZETİ YANLIŞ ALANI OKUYORDU** — "ayna uyumlu" derken 4/4 pozisyon ~2× ayrıktı
   (`mirror_drift` FİYAT, `position_drift` ADET; ikincisi nabızda hiç yoktu). Alan yayan tarafa kondu.
7. **C10 SUNUM BEKÇİSİ ÜÇ YOLDAN KAÇIRIYORDU** — README kapsam dışı, workflow.js hiç taranmıyor, regex
   araya giren tek sözcükle atlatılıyor. Kapsam artık AİLEDEN türüyor (landing.js'i anında buldu).

## 3. YENİ KALICI SAVUNMA — 8. BÜTÜNLÜK DESENİ (`divergence`)

Operatörün gözlemi ("sürekli bir yerlerde split çıkıyor") ölçüldü ve **yapısal boşluk doğrulandı**:
yedi dedektörün hiçbiri iki kaynağın DEĞERİNİ kıyaslamıyordu — `coherence_report` yalnız `mtime`
bakıyor, yani iki dosya aynı saniyede zıt değer taşısa "yeşil" derdi. Yeni desen gerçek üzerinden
kayıt tutuyor (`EQUIVALENT_TRUTHS`), her kaynak bir İLİŞKİ taşıyor (`esit`/`yarisi`/`beyanli-ayri`).
Split denetimi (54 çift, 26 kapısız) bu kapının genişleme listesidir.

## 4. ÖLÇÜMLER (5 kart, hepsi hükümlü)

- **EDG-032** — C+mb doğrulaması: kapı 3/3 GEÇTİ. Damga: 885 işlem, +20.685$, dd %12,7, sharpe 0,521.
  Şerh: ΔP&L CI 0-içi (bozulmama kapısı, iyileşme kanıtı değil).
- **EDG-033** — rejim-koşullu boyutlama: İKİ hücre de düştü → düz-0,5R kanıtla doğrulandı. Öğretici:
  saf boyut etkisi POZİTİFTİ ama 0,75R planlar 5R zarfını 2× hızla doldurup ~170 iyi işlemi dışladı.
- **EDG-034** — skor-sıralı kabul: İNERT (motor zaten skor-sıralı; backtest.py:332).
- **EDG-035** — komşuluk taraması (6 hücre): **C+mb @5R YEREL OPTİMUM KANITLA**. Yapısal: slot tavanı
  fiilen ÖLÜ knob (tepe 13<20; slot25 bayt-özdeş), bağlayıcı kaynak 5R zarfı. Yan kazanç: v237
  dağıtımının davranışı ZERRE değiştirmediği bayt-özdeşlikle kanıtlandı.
- **EDG-036** — tohum yenileme: **şu artefaktla YAPILAMAZ**. 032 defteri ölçüm için 12 alana kırpılmış
  slim projeksiyon; canlı şemanın 13 alanı uydurulamaz. Yüklenirse 7 tüketici körleşiyor, rollback
  kapısı açılıyor. Doğru yol: 032'yi TAM-SATIR çıktıyla yeniden koş.

## 5. EN ÖNEMLİ DÜZELTME — RAPORLAMA HATAM

"Canlı P&L −5.264$" dedim; **YANLIŞTI ve operatör itirazı haklıydı.** Ölçüm: 97 işlemin **95'i
`replay_seed`** (kâğıt hesapta İCRA EDİLMEDİ, sv=4 ESKİ paketten), yalnız **2'si `live_paper`**
(+277,99$). Bundan sonra "kâğıt-icra" ve "replay tohumu" ayrı adlandırılıyor. Bu düzeltme EDG-036'yı
doğurdu: defterin kendisi eski dünyadan ve 15 tüketicisinden 13'ü sim/gerçek ayrımı yapmıyor —
rollback defteri kanıtlıyor ki tohum ZATEN bir kez canlı sürüm geri aldırmış.

## 6. SABAH İLK BAKILACAKLAR

1. **Evren denetiminin ilk temiz koşumu** (düzeltme canlıda, dosya henüz eski).
2. **Sprint çocuk süreci neden ölüyor** — kilit açıldı, yeni sprint doğdu, çocuk 0,5 saatte öldü.
3. **`korumasiz_motor_disi_pozisyon: NVDA 1 adet`** (01:26Z) — motor-DIŞI pozisyonun broker'da stop'u yok.
4. **mb'nin ilk gerçek silahlı seansı** — bugünkü EOD'de (dün 0 aday çıktı; kuraklık ARIZA DEĞİL,
   ölçüldü: tarama sağlam, son 4-5 seans sinyalsiz).

## 7. OPERATÖR KALEMLERİ (Claude kapatamaz)

- **brain_chain_distinct TAM AÇIK** ve paylaşılan kimlik ölüydü: `NOUS_MODEL`/`GEMINI_MODEL` sırları —
  Claude anahtarı ekle ya da NOUS_MODEL'i Google dışına al.
- **N1 bildirim kanalı** (alarmlar yalnız panoda birikiyor; 12 teslim edilmemiş).
- **PF kapısı kararı:** `RESULT_PF_MIN=1.3` ↔ paketin PF'i 1,1119 → Faz-6 `sonuc_hukmu` kilidi bu
  paketle yapısal olarak AÇILAMAZ (eşik 95-işlemlik deftere göre yazılmıştı) — ROADMAP §2-20b.
- **Yönetişim asimetrisi:** slot LIMIT_KEYS'te kilitli ama `position_size_r` bounds'ta 1,0'a kadar açık
  → öğrenme "ayrılmaz ikili"nin yarısını tek başına geri çekebilir — §2-20c.
