# G3b çıkış reformu — plan katmanı notları

**Kaynak:** 2026-07-30 skill denetimi, `breakout-trade-planner` kaleminin "birleştir" hükmü.
**Durum:** BELGE + UYGULAMA KAYDI. Belge kısmı (aşağıdaki "Katlanan sezgiler") hiçbir davranışı
değiştirmez. 2026-07-30 kod turunda hangi sezginin koda döndüğü ve hangisinin DÖNMEDİĞİ aşağıdaki
"Kod turu" bölümünde kayıtlıdır.

## Kod turu (2026-07-30) — ne uygulandı, ne uygulanmadı

Dört mekanizma, **hepsi default-off** (Batch L deseni: satır `state/bounds.yaml`'da, canlı
`state/strategy.yaml` onları TAŞIMIYOR → canlı davranış birebir eskisi; çivi testi
`tests/test_g3b_cikis_v124.py`).

| # | Mekanizma | Knob(lar) | Yer |
|---|---|---|---|
| ① | Erken itlaf, pivot-altı | `exit.early_kill_pivot` (0/1), `exit.early_kill_bars` (1-10) | `strategy.early_kill_pivot_exit` → `manage_position` |
| ② | Yapı-tabanlı stop | `stop_mode` (0=atr/1=pivot_alti), `stop_buffer_atr` (0.1-1.0) | `strategy.structural_stop` → `evaluate_entry` |
| ③ | Time-stop gün-gün R eğrisi | — (ölçüm, knob değil) | `backtest.holding_day_r_curve` |
| ④ | Rejim-koşullu çıkış altyapısı | — (çözümleyici izni) | `config.REGIME_EXIT_KEYS` + `resolve_params` |

**TEK YASA, İKİ TÜKETİCİ (çift uygulama yok):** erken itlaf `manage_position` içinden çağrılır ve
`manage_position`ı iki motor çağırır — `backtest.replay` (CLOSE(D)) ve `loop.daily_cycle` (canlı
CLOSE(D)), ikisi de aynı imza + aynı rejim-çözümlü `eff` ile. `loop.py`'a ikinci bir çıkış kuralı
YAZILMADI; yasa tek yerde yazılı olduğu için iki motorun ayrışması yapısal olarak imkânsız (§4).

**ÇÜRÜTÜLEN BİÇİM KODA GİRMEDİ:** ROADMAP §3.2 erken itlaf için iki biçim öneriyordu — "pivot altı"
ve "aralığın alt yarısı". G3b ön-ölçümü (2026-07-29, cf n≈2100) ikincisini çürüttü: kapanışın bar
aralığı içindeki KONUMU sürekli sinyal olarak sıfır bilgi taşıyor (IC ≈ 0, her iki katmanda). Ölçüm
yalnız pivot-altı kapanışı destekliyor (@5 bar −0.74% vs pivot-üstü +0.32%, n=302; @20'de kısmen
toparlıyor). Bu yüzden `early_kill_pivot_exit` TEK biçim uygular — çürütülmüş biçim knob olarak bile
bırakılmadı, çünkü bounds'a konsa arama döngüsü onu gürültüden ayırt edemez ve k_probes bütçesini
ölçülmüş bir hiçliğe harcardı.

**PİVOT NEDEN PLAN DEFTERİNDE DEĞİL:** ilk uygulama pivotu plan sözlüğüne alan olarak ekledi ve
`test_differential_v60.test_plan_dicts_have_the_same_field_set` bunu HAKLI OLARAK düşürdü. O test
CANLI-only alanlar için bir allowlist tutar ama REPLAY-only alanlar için **bilinçli olarak tutmaz**:
replay'in bilip canlının bilmediği bir alan tam olarak "backtest sayıları yalan olur" ayrışmasıdır
(§4). Testi gevşetmek yanlış yön olurdu. Doğru ayrım: pivot bir **defter alanı değil icra
girdisidir** → `broker.fill_entry(..., pivot=…)` argümanı olarak taşınır, `backtest.replay` onu
`armed` ile aynı ömre sahip bir yan haritada tutar. Plan şeması iki motorda birebir aynı kaldı.

**AÇIK DİKİŞLER (3b'ye devir, ikisi de bu turun yüzeyi DIŞINDA):**
1. Canlı yol (`loop.py`) `fill_entry`e `pivot` GEÇİRMİYOR → `Position.pivot` 0.0 kalır → erken itlaf
   canlıda ateşlemez. Yani knob canlıda açılsa bile **ölçüm yalnız replay'de mümkündür**. Canlıya
   alınması `loop.py`'da tek argümanlık bir ekleme gerektirir (kurulumun pivotu o yolda `sig.pivot`
   olarak zaten mevcut); §5'teki "emir şablonu sürüm izi" maddesiyle birlikte yapılmalı.
2. `guard.classify_proposal` hâlâ `base not in current_params` diye reddediyor, yani Hermes
   `exit.early_kill_pivot@chop` gibi bir hipotezi ÖNEREMEZ. Reddi bugüne kadar DÜRÜSTTÜ (override
   gerçekten sessizce düşüyordu); ④ o düşmeyi kapattı ama sevk yetkisi ayrı bir karardır.

**PANO BAĞI DEVREDİLDİ:** ③'ün eğrisi bugün yalnız kum havuzu raporuna (JSON) yazılıyor. Kalıcı pano
bağı `analytics.py` yüzeyini gerektirir ve o yüzey bu turda paralel bir ajanda — 3b'ye notla devir.

## Neden burada, neden `position-sizer/SKILL.md`'de değil

`breakout-trade-planner` işlevi motor tarafından soğurulduğu için arşive alındı
(`skills/_emekli/breakout-trade-planner/`, silinmedi). Doğal katlama hedefi plan katmanının
motor-uygulanmış skill'iydi (`position-sizer`) — ama o skill **PROTECTED** beşlisinde
(`skills.py:PROTECTED`) ve bu turda korumalı skill dosyalarına dokunulmadı. Bu yüzden sezgiler
korumalı yüzeye değil bu belgeye yazıldı.

## Motorun zaten sahip olduğu kısım (yeniden yazılmayacak)

- `strategy.py` `EntrySignal`: pivot, stop, hedef ve `size_r` hesabı.
- `loop.py` P3_PLAN yolu: `state/trade_plans.jsonl` üretimi.
- `position-sizer` + `pre-trade-discipline-gate`: `ENGINE_IMPLEMENTED`, her P3 koşusunda gerçekten
  çalışıyor (boyut + disiplin kapısı).

Yani arşivlenen skill'in vaat ettiği çıktı motorda mevcut. Aşağıdaki maddeler o çıktının **eksik**
kalan tarafına — G3b'nin çözmeyi hedeflediği kısma — ait.

## Katlanan sezgiler

### 1. En-kötü-durum girişiyle boyutlandır

Boyut, sinyal fiyatından değil **worst-case entry**'den hesaplanır; aksi hâlde kayma (slippage) riski
sessizce R'yi büyütür. Arşivlenen planlayıcı, kırılım durumundaki adayı `current_price <= worst_entry`
koşuluyla eliyordu — plan ile icra arasındaki farkı baştan riske yazan yaklaşım.

### 2. Kapı: tüm koşullar birlikte

| Koşul | Kırılım öncesi | Kırılım anı |
|---|---|---|
| geçerli VCP | evet | evet |
| derecelendirme bandı | good/strong/textbook | good/strong/textbook |
| `risk_pct_worst` | ≤ %8 | ≤ %8 |
| kırılım hacmi | — | evet |
| pivottan uzaklık | — | ≤ max chase |
| güncel fiyat | — | ≤ worst entry |

`risk_pct_worst ≤ %8` maddesi G3b için önemli: **yapı** kötüyse (stop çok uzaksa) işlem, boyut
küçültülerek kurtarılmaz — plan tamamen düşer.

### 3. Isı tavanları (arşivlenen varsayılanlar)

İşlem başına risk %0.5 · tek pozisyon ≤ %10 · sektör ≤ %30 · **toplam açık risk (portföy ısısı)
≤ %6** · hedef 2R · stop tamponu daralma dibinin %1 altı · pivot üstü kovalama ≤ %2 · buy-stop
tetiği için pivot tamponu %0.1. Bunlar Meridian'ın canlı yasası DEĞİL (motorun kendi bounds/ısı
tavanları geçerli); G3b kalibrasyonunda karşılaştırma noktası olarak duruyor.

### 4. İki icra kipi — G3b'nin asıl kancası

- `pre_place`: pivot üstüne **stop-limit bracket** önceden bırakılır (kırılımı kaçırmama).
- `post_confirm`: kırılımdan sonra ~5 dakikalık teyit beklenir, sonra **limit bracket** girilir
  (yanlış kırılımdan kaçınma).

İkisi arasındaki seçim ölçülebilir bir sorudur ve tam olarak G3b'nin sorduğu şeydir: pivot-altına
dönüş "erken itlaf" mı sayılacak, yoksa yapı-tabanlı stop mu beklenecek? Karar, gölge/karşı-olgusal
defterde iki kipin ayrı ayrı ölçülmesiyle verilmelidir — belge bir kip önermiyor.

### 5. Emir şablonu = denetlenebilirlik

Planın broker'a gidecek emir şablonunu (bracket bacakları, tetik, limit) plan anında yazması, sonradan
"neden bu fiyattan girildi" sorusunun cevabını bırakır. `state/trade_plans.jsonl` bu izi tutuyor;
G3b reformu bu alanları değiştirirse şablonun da sürüm izi bırakması gerekir.

## Sınır

Bu belge yeni bir yasa getirmez, hiçbir eşiği canlıya almaz ve motorun mevcut çıkış davranışını
tanımlamaz. G3b tasarımı yazıldığında buradaki maddeler ölçüm konusu olarak ele alınmalıdır.
