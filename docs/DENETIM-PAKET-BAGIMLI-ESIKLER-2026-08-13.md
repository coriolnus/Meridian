# DENETİM — PAKET-BAĞIMLI EŞİK ENVANTERİ (2026-08-13)

**Sınıf:** ENVANTER + KANIT. Bu belge hiçbir eşiği DEĞİŞTİRMEZ, hiçbir hüküm vermez. Denetim ajanı
kod yazmadı; git/canlı/ssh yok; yalnız salt-okuma + kapsam testi (iki test, §0.1'de adıyla).

**Soru:** Sistemde hangi eşik/sabit/varsayım ESKİ dünyaya (slot 5 · 1,0R · rampa 3/8 · mb dormant ·
dd ~%8) göre ayarlanmış ve YENİ pakete (C+mb @5R, v237) göre gözden geçirilmesi gerekiyor?

---

## §0 — ÖLÇÜLEN DÜNYA (bu belgedeki her hüküm buradan türer)

| büyüklük | değer | kaynak |
|---|---|---|
| işlem | 885 | `research/cards/EDG-2026-032-final-paket-dogrulama.yaml` (hüküm bloğu) |
| net P&L | +20.684,69 $ | aynı kart + `research/olcumler/edg032_final_paket_2026-08-12/islemler_cmb.json` (yeniden toplandı) |
| max-dd | %12,68 | `.../sonuc.json` → `kapi_olcutleri.../maxdd_CMB` |
| sharpe | 0,521 | aynı (bu denetimde bağımsız yeniden hesap: 0,523) |
| işlem-R | +0,0763 | islemler_cmb.json üzerinden yeniden hesap |
| win | %36,3 | aynı |
| pencere | 2022-01-07 → 2026-07-24 = **1659 gün (4,54 yıl)**, 194,7 işlem/yıl | islemler_cmb.json |
| eşzamanlı pozisyon tepesi | 13 (<20) | `research/cards/EDG-2026-035-yerel-duyarlilik.yaml` |
| gerçekleşen ısı tepesi | tam **5,000R** | EDG-035 |
| nominal ısı (açılış fazı) | p50 1,5R · p90 5,5R · max 6,5R · 1147 seansın 528'i 0,0R | `.../sonuc_cmb.json` → `tepe_isi` |
| C tabanı (kıyas) | 772 işlem · +9.869$ · dd %12,35 · sharpe 0,285 · R 0,057 | `research/cards/EDG-2026-026-slot20-boyut05.yaml` |

**Bu denetimde ilk kez türetilen ölçümler** (hepsi yukarıdaki artefakttan, uydurma yok):

- **Profit factor = 1,1119** (brüt kazanç 205.552$ / brüt kayıp 184.868$)
- **realized_30d = +0,341 %** · yıllık bileşik **+4,22 %** (100k$ tabanda +%20,68 / 1659 gün)
- **CVaR5 (işlem-R) = −1,4736R** (`analytics._cvar` algoritmasıyla birebir: np.percentile lineer,
  q=−1,062 → kuyruk n=45) · en kötü işlem −4,294R · R ≤ −1,0 oranı %29,5
- kurulum kırılımı: mb n=339 R+0,083 CVaR5 −1,350 · vcp n=315 R+0,047 CVaR5 −1,469 ·
  **exhaustion_hammer n=225 R+0,131 CVaR5 −1,592** · pullback n=6 R−0,788
- rejim kırılımı: **trend_up n=790** R+0,084 · **chop n=95** R+0,012 · **trend_down n=0 · high_vol n=0**
- yıl deseni: 2022 n=39 R−0,333 · 2023 +0,142 · 2024 +0,062 · 2025 +0,113 · 2026 +0,075
- kapı defteri: NO_GO 607 → **heat_hard 607 · sector_cap 8** · REVIEW: sector_stacking 562 ·
  **heat_review 560** · leading_sector 527 · score_band 73 · rr_marginal 43 · correlation 12
- ima edilen risk_dollars (|pnl/R|): medyan **456,9 $** (nominal 0,5R = 500$), p05 331 · p95 573

### §0.1 — CANLI KIRMIZI (şu anda, bu makinede koşuldu)

`max_drawdown 0.08→0.16` yerel olarak uygulandı ama **iki test bunu takip etmedi ve ŞU AN KIRMIZI**:

```
FAILED tests/test_para_yasasi_v127.py::test_dusus_vetosu_MARJI_kendi_gurultusunun_DISINDA
        assert 0.04 == 0.5 * 0.16   → 0.04 != 0.08
FAILED tests/test_dalga_w1_v216.py::test_C5_dd_veto_margin_goalun_TAM_YARISIDIR
        Obtained: 0.04   Expected: 0.08 ± 8.0e-08
```

Yani karar "kapandı" sayılsa da **aşağı akışı kapanmadı**. Ayrıntı: K-01.

---

## §1 — ÖNCELİK SIRALI ÖZET

| # | kalem | dosya:satır | şimdi | durum | eylem |
|---|---|---|---|---|---|
| K-01 | `shadowlaw.DD_VETO_MARGIN` — türetimi "goal.max_drawdown'un YARISI"; goal 0,16 oldu, sabit 0,04 kaldı; **2 test kırmızı** | `meridian/shadowlaw.py:97` | 0.04 | **KIRMIZI** | değiştir/karar (0,08 mı, yoksa türetim mi terk edilecek) |
| K-02 | `analytics.RESULT_PF_MIN` — benimsenen paketin ÖLÇÜLEN PF'i **1,1119**; eşik 1,3. SONUÇ hükmü 4/4 ister → **Faz-6 `sonuc_hukmu` kilidi bu paketle yapısal olarak açılamaz** | `meridian/analytics.py:2089` | 1.3 | **KIRMIZI** | ölç + karar (eşik mi paket mi) |
| K-03 | `bounds.position_size_r` **0,5'i içeriyor AMA 1,0'a kadar açık** — paketin ayrılmaz ikizi `max_open=20` LIMIT_KEYS'te (Hermes öneremez), boyut ise kum havuzunda. Makine tek başına ikiliyi bozabilir | `state/bounds.yaml:15` ↔ `state/goal.yaml:124` ("İkisi AYRILMAZ") ↔ `meridian/guard.py:24` | {0.1, 1.0, 0.1} | **KIRMIZI** | karar (tavanı 0,5'e indir / LIMIT_KEYS'e taşı / bilinçli bırak+beyan) |
| K-04 | `analytics.EDGE_CVAR5_MIN_R` — ölçülen **−1,4736R**, eşik −1,5R → marj **0,026R (%1,8)**. Alt-kurulum `exhaustion_hammer` tek başına **−1,5916R** (eşiğin altında) | `meridian/analytics.py:1621` | −1.5 | **KIRMIZI (jilet ince)** | ölç (canlı defterde izle; eşiğe dokunma — türetimi boyuttan bağımsız) |
| K-05 | `limits.max_sector_exposure_pct` — paydası `max_open_positions` (guard.py:360). 5 slotta 2 isim/sektör bağlıyordu, 20 slotta **8 isim**. Ölçülen kitap tepesi 13 isim → kural fiilen ölü: **NO_GO'nun 607'sinden yalnız 8'i sector_cap** | `state/goal.yaml:133` · `meridian/guard.py:359-362` | 40.0 | **KIRMIZI** | karar (mutlak isim tavanı mı, yüzde mi; %40 artık farklı bir şey demek) |
| K-06 | `shadowlaw.MARGIN_MONEY_SCALE` / `MONEY_GATE_MARGIN` — σ(S_eski)=0,18644 dd paydası **0,08** iken ölçüldü. Varyansın **%82'si dd bacağıydı**; payda 2× açılınca σ(dd_c) ~yarıya iner → σ(S_eski) düşer → 0,02'nin σ-eşdeğeri BÜYÜR. Marj 0,004 artık gevşek taraftadır | `meridian/shadowlaw.py:83-84,103-116` | 0.1908 / 0.004 | **KIRMIZI (türev)** | ölç (`variance_attribution()` yeniden koş; σ yeniden ölçülmeden sayı yazılmaz) |
| K-07 | `goal.rollback_if_worse_by` — eski bileşik skor üzerinde çalışır (rollback.py:193/383 `score_mod.score`). Ölçülen dünyada bileşik ≈ **0,130** (ret_c 0,049 + dd_c 0,208 + sharpe_c 0,218 ağırlıklı). 0,10'luk eşik skorun neredeyse TAMAMI kadar; ayrıca dd paydası açılınca skorun oynaklığı da daraldı | `state/goal.yaml:47` · `meridian/rollback.py:206` | 0.10 | **GERİLİM (yüksek)** | ölç (skor dağılımını yeni paydayla yeniden ölç) |
| K-08 | `goal.min_sharpe` — ölçülen sharpe **0,521**, hedef 1,2 → `sharpe_c = 0,217`; hedefin %43'ü | `state/goal.yaml:17` · `meridian/score.py:121,125` | 1.2 | **GERİLİM** | karar (hedef mi iddialı, paket mi eksik — ikisi de meşru cevap) |
| K-09 | `goal.target_return_30d` — ölçülen realized_30d **+0,341%**; hedef %7 → `ret_c = 0,049`. Hedef yıllık %125'e denk; ölçülen %4,22. Deponun kendi modülü bu hedefi zaten "gerçekçi programın 2-3 katı" diye yazıyor | `state/goal.yaml:16` · `meridian/score.py:119,123` · şerh `meridian/shadowlaw.py:44` | 0.07 | **GERİLİM** | karar (skorun getiri bacağı fiilen ölü — 0,05/1,0) |
| K-10 | `limits.heat_review_r` 3,5R = **7 açık isim** (0,5R'de). Ölçülen kitap 13 isme çıkıyor → REVIEW varsayılan hâl: ölçümde **560 heat_review** bayrağı. L0'da davranış değişmez, **L1'de onay kuyruğu olur** | `state/goal.yaml:150` · `meridian/guard.py:384` | 3.5 | **GERİLİM** | karar (L1'e geçmeden önce; bayrak enflasyonu sinyali öldürür) |
| K-11 | `loop.EXPLORE_MAX_POS = 5` — **eski `max_open` ile aynı sayı**. `EXPLORE_MAX_R=0,25` eskiden normal pozisyonun ÇEYREĞİ, şimdi YARISI. `EXPLORE_TOTAL_R=1,25` = 5R zarfın %25'i, 20 slotla yarışıyor | `meridian/loop.py:22-24` | 0.25 / 5 / 1.25 | **GERİLİM** | ölç (keşif payı `hermes.exploration_share` ile) |
| K-12 | `limits.max_position_r = 1,0` — canlı `size_r` 0,5 → `guard.py:366` kontrolü hiçbir planda bağlayamaz (boş kısıt) | `state/goal.yaml:117` · `meridian/guard.py:366` | 1.0 | **GERİLİM (zararsız)** | dokunma + beyan (üst zarf olarak kalsın) |
| K-13 | `limits.derisk_full_dd/floor_dd` 0,15/0,36 — ölçülen dd tepesi %12,68 → rampa **hiç devreye girmedi** (EDG-026 kartı: "15/36 rampası C'de hiç kısmadı") | `state/goal.yaml:170-171` · `meridian/broker.py:31-32` | 0.15 / 0.36 | **GERİLİM (uyuyan)** | dokunma (uyuyan emniyet vanası ≠ yanlış eşik) |
| K-14 | `analytics.EDGE_IC_N_MIN=60`'ın **gerekçe metni bayat**: "gerçek işlemler ayda ~10-15 birikiyor; 60 ≈ altı aylık canlı defter". Yeni paket geri-testte 2,16× akış üretiyor | `meridian/analytics.py:1571-1575` | 60 | **GERİLİM (belge)** | belge güncelle (sayıya dokunma) |
| K-15 | `broker.MAX_NOTIONAL_PCT / ADV_CAP_PCT / IMPACT_COEF` — 0,5R'de yarı sıklıkta bağlar. Ölçülen kanıt: ima edilen risk_dollars medyanı **456,9$** (nominal 500$) → tavanlar hâlâ ~%9 tıraşlıyor | `meridian/broker.py:18-20` | 0.02 / 0.25 / 0.10 | **GERİLİM (bilgi)** | dokunma |
| K-16 | `counterfactual.MAX_OPEN=2500` — "250 evrene göre ~60 kayıt/gün" varsayımı. mb silahlandı, plan akışı arttı (mb planı 603) | `meridian/counterfactual.py:24` | 2500 | **GERİLİM (kapasite)** | ölç (doluluk panelde) |
| K-17 | `analytics.REGIME_N_MIN=30` — ölçülen 4,54 yılda **trend_down 0, high_vol 0 işlem**; chop 95, trend_up 790. Rejim ölçütü iki rejimde yapısal olarak ÖLÇÜLEMEDİ'de kalıyor | `meridian/analytics.py:1580` | 30 | **GERİLİM (yapısal)** | ölç/beyan (eşik hatası değil, evren gerçeği) |
| K-18 | `validation.DSR_*` — DSR/PSR Sharpe türevidir ve √n ile büyür. n 410→885 olunca **aynı işlem-Sharpe'ı daha yüksek DSR verir**. Bu bir kenar iyileşmesi DEĞİLDİR | `meridian/validation.py:94-118` | 0.95 / 0.20 | **GERİLİM (dürüstlük şerhi)** | belge/şerh (eşiğe dokunma) |
| K-19 | `skills` R-eşikleri (−0,15 / +0,30 / AUTO_AVG_R −0,30) — **R boyuttan bağımsız (§4 KANIT)**, eşikler kaymıyor. Değişen tek şey POPÜLASYON: mb gerçek katmanda n=0'dan çıktı | `meridian/skills.py:408,412,582` | −0.15/+0.30/−0.30 | **TUTARLI** | dokunma (popülasyonu izle) |
| K-20 | `goal.max_drawdown` + `EDGE_MAXDD_MAX` + `RESULT_MAXDD_MAX` üçlü eşitliği | `goal.yaml:20` · `analytics.py:1614,2094` | 0.16 | **KAPANDI** | dokunma (üç yer senkron; testler çiviliyor) |

---

## §2 — `state/goal.yaml` ALAN ALAN

### 2.1 Başarı/başarısızlık üçlüsü

**`target_return_30d: 0.07`** · `state/goal.yaml:16`
- ESKİ DÜNYA: 2026-07-14 intake yazımı; hiçbir ölçüme dayanmıyordu.
- YENİ DÜNYA: **GERİLİM**. Okuyan: `meridian/score.py:119` → `ret_c = realized_30d / 0.07`
  (score.py:123). Ölçülen realized_30d = **+0,341 %** → `ret_c = 0,049`. Yani skorun ağırlıkça
  en büyük bacağı (0,5) fiilen sıfıra çakılı: aday ile incumbent arasında bu terimden gelebilecek
  fark ihmal edilebilir. Deponun kendi modülü aynı teşhisi zaten yazıyor
  (`meridian/shadowlaw.py:44`: aylık %7 = yılda %125, "gerçekçi bir programın 2-3 katı").
- EYLEM: **karar** (eşik operatör kalemi; skorun getiri bacağının ölü olduğu ölçüldü).

**`min_sharpe: 1.2`** · `state/goal.yaml:17`
- YENİ DÜNYA: **GERİLİM**. `score.py:125` → `sharpe_c = sharpe / 2,4`. Ölçülen sharpe 0,521 →
  `sharpe_c = 0,217`. Benimsenen, altı komşusuna karşı yerel-optimum kanıtlanmış paket hedefin
  %43'ünde. EDG-035 komşuluk taraması hiçbir yönde CI-üstünlük bulamadı → bu paket sharpe'ı
  parametre oynatarak 1,2'ye çıkmıyor.
- EYLEM: **karar**.

**`max_drawdown: 0.16`** · `state/goal.yaml:20`
- **KAPANDI** (operatör kararı). Üç yer senkron: `analytics.EDGE_MAXDD_MAX` (1614),
  `analytics.RESULT_MAXDD_MAX` (2094); eşitlik `tests/test_dalga_w1_v216.py:481` ve
  `tests/test_hafta3a_v119.py:78` ile çivili. dd_c artık `1 − 0,1268/0,16 = 0,208` (eski paydayla
  −1,0'a kısılırdı).
- **AMA AŞAĞI AKIŞI KAPANMADI** → K-01 ve K-06.

**`failure_below: -0.04`** · `state/goal.yaml:29`
- Okuyan: `meridian/watchdog.py:1676` `goal_failure_report()` → `obs.ALARM_GOAL_FAILURE`.
- YENİ DÜNYA: **TUTARLI**. −%4/30g ≈ −%38,6/yıl; ölçülen +%0,34/30g. Eşik gerçek bir felaket
  sinyali olarak kalıyor ve paketin normal bölgesinde yanlış-alarm üretmiyor.
- EYLEM: **dokunma**.

### 2.2 Öğrenme parametreleri

**`reflection_every: 5`** · `state/goal.yaml:32` — okuyan `meridian/hermes_runtime.py:120,375,525`.
YENİ DÜNYA: **GERİLİM (bilgi)**. Geri-test akışı 2,16× (885 vs 410 aynı pencerede) → aynı takvimde
~2× daha sık düşünme turu. Bu bilgi kazancıdır; aşağıdaki kota ile birlikte okunmalı.

**`min_sample: 30`** · `state/goal.yaml:33` — okuyan `score.py:86`, `rollback.py:186,379`,
`analytics.RESULT_N_MIN` (2085, birebir aynı sayı, bilinçli). YENİ DÜNYA: **TUTARLI** — payda
2,16× hızlı doluyor. **dokunma**.

**`rollback_if_worse_by: 0.10`** · `state/goal.yaml:47` — okuyan `rollback.py:206`
(`karar["delta"] < -threshold`), karşılaştırılan büyüklük `score_mod.score` yani **ESKİ bileşik**.
YENİ DÜNYA: **GERİLİM (yüksek, K-07)**. İki ayrı etki üst üste biniyor:
1. Ölçülen dünyada bileşiğin kendisi ≈ 0,130 (0,5·0,049 + 0,3·0,208 + 0,2·0,217). 0,10 eşiği
   skorun neredeyse tamamı kadar → geri-alma pratikte yalnız felaket seviyesinde tetiklenir.
2. `max_drawdown` 0,08→0,16, `MEASURED_V3.eski_paylar.dusus = 0,8198` (shadowlaw.py:107) yani
   bileşik varyansının %82'si olan dd bacağının paydasını 2× açtı → σ(dd_c) ~yarıya, σ(S_eski)
   belirgin biçimde düşer. **σ(S_eski) YENİ DÜNYADA ÖLÇÜLMEDİ** — bu denetim ölçemez (
   `variance_attribution()` 2000 replikasyonluk bir yeniden koşum ister ve ölçüm ajanı değilim).
EYLEM: **ölç**.

**`max_accepted_changes_per_month: 8`** · `state/goal.yaml:54` — okuyan `guard.py:243`.
YENİ DÜNYA: **TUTARLI**. Öneri debisi 2× artarken kota sabit kalması anti-overfit kısmasının
AMACIDIR; kotayı akışla birlikte büyütmek düzeltme değil gevşetme olurdu. **dokunma**.

**`explore_rate: 0.15` · `backtest_gate` · `one_variable_only` · `schema_version` · `style` ·
`session_tz` · `kill_switch_file`** — dosyanın kendi yorumları bunların **hiçbir kod tarafından
okunmadığını** beyan ediyor (goal.yaml:3-9, 34-38, 40-46, 48-53, 172-175); tek eşleşme
`guard.GOAL_KEYS` üyelik seti (guard.py:15-23). Paket-bağımlı DEĞİLLER. **dokunma.**

### 2.3 `limits` bloğu

| anahtar | satır | değer | durum | not |
|---|---|---|---|---|
| `autonomy_level` | :116 | 0 | TUTARLI | paket-bağımsız |
| `max_position_r` | :117 | 1.0 | GERİLİM (K-12) | `guard.py:366` kontrolü 0,5R'de hiç bağlamaz |
| `max_open_positions` | :131 | 20 | TUTARLI | ölçülen tepe 13 → **fiilen ölü knob** (EDG-035); `sonuc_c.json` `tavan_sifir %0` |
| `max_daily_loss_pct` | :132 | 3.0 | TUTARLI | `guard.py:363`; ısı zarfı 5R = NAV %5 değişmedi, kesici ile ilişkisi aynı. `loop.py:1482` şerhi (canlı pencere yalnız gecelik boşluk) paketten ÖNCE de geçerliydi |
| `max_sector_exposure_pct` | :133 | 40.0 | **KIRMIZI (K-05)** | payda `max_open_positions`; 2 isim → 8 isim; ölçümde 607 NO_GO'nun 8'i |
| `no_trade_before_bars` | :134 | 3 | TUTARLI | günlük bar motoru; paket-bağımsız |
| `heat_hard_r` | :140 | 5.0 | **TUTARLI — DOKUNMA** | dört bağımsız ölçüm: EDG-026 (168/171 NO_GO heat_hard), EDG-028 (zarf-10 sharpe 0,285→0,037), EDG-032 (607 NO_GO), EDG-035 (gerçekleşen tepe tam 5,000R; zarf 6,5/8,0 kalite düşürüyor, monoton değil) |
| `heat_review_r` | :150 | 3.5 | GERİLİM (K-10) | 7 isim eşdeğeri; ölçümde 560 bayrak |
| `corr_review` | :151 | 0.85 | TUTARLI | ölçümde yalnız 12 bayrak; korelasyon ölçümü boyuttan bağımsız |
| `derisk_full_dd` | :170 | 0.15 | GERİLİM (K-13) | ölçülen dd tepesi %12,68 → hiç devreye girmedi |
| `derisk_floor_dd` | :171 | 0.36 | GERİLİM (K-13) | aynı |

---

## §3 — MODÜL SABİTLERİ

### 3.1 `meridian/analytics.py` — EDGE (kuzey yıldızı, 5 ölçüt)

| sabit | satır | değer | ölçülen | durum |
|---|---|---|---|---|
| `EDGE_IC_MIN` | 1566 | 0.03 | — (canlı defter gerekir) | TUTARLI — rank-IC boyuttan bağımsız |
| `EDGE_IC_N_MIN` | 1571 | 60 | gerekçe metni bayat (K-14) | GERİLİM (belge) |
| `PRED_HIT_N_MIN` / `PRED_HIT_RATE_MIN` | 1576/1579 | 10 / 0.6 | — | TUTARLI — işaret isabeti boyuttan bağımsız |
| `REGIME_N_MIN` | 1580 | 30 | trend_up 790 ✓ · chop 95 ✓ · trend_down 0 ✗ · high_vol 0 ✗ | GERİLİM (K-17) |
| `REGIME_AVG_R_MIN` | 1585 | 0.0 | trend_up +0,084 ✓ · chop +0,012 ✓ (kıl payı) | TUTARLI (R boyuttan bağımsız) |
| `EDGE_TAIL_N_MIN` | 1608 | 40 | 885 ≫ 40 | TUTARLI |
| `EDGE_MAXDD_MAX` | 1614 | 0.16 | 0,1268 ✓ | KAPANDI |
| `EDGE_CVAR5_MIN_R` | 1621 | −1.5 | **−1,4736** (marj 0,026R) | **KIRMIZI (K-04)** |

**K-04 ayrıntısı.** Sabitin gerekçesi (analytics.py:1622-1629) **yasadan** türetilir, ölçümden
değil: boyutlayıcı `qty = risk_dolar/(giriş−stop)` kurduğu için stopa uyulan çıkış tam −1,0R'dir;
−1,5R "risk biriminin yarısı kadar boşluk hasarına izin ver" demektir. Bu türetim **boyuttan
bağımsızdır ve hâlâ doğrudur** — sorun eşikte değil, benimsenen paketin eşiğin **üzerinde 0,026R**
oturmasında. Alt kırılım daha da keskin: `exhaustion_hammer` (n=225) tek başına **−1,5916R**, yani
eşiğin ALTINDA; `momentum_burst` −1,3503R ile en temiz kuyruğa sahip. Eşiğe dokunmak yanlış olur;
izlenmesi gereken şey canlı defterin kuyruğudur.

### 3.2 `meridian/analytics.py` — RESULT (dolar hükmü, 4 ölçüt)

| sabit | satır | değer | ölçülen | durum |
|---|---|---|---|---|
| `RESULT_N_MIN` | 2085 | 30 | 885 ✓ | TUTARLI (goal.min_sample ile birebir, bilinçli) |
| `RESULT_PF_MIN` | 2089 | 1.3 | **1,1119** ✗ | **KIRMIZI (K-02)** |
| `RESULT_MAXDD_MAX` | 2094 | 0.16 | 0,1268 ✓ | KAPANDI |
| `RESULT_NET_OVER_FRICTION` | 2098 | 1.0 | **ÖLÇÜLEMEDİ** | — |

**K-02 ayrıntısı.** Bu, envanterin en ağır maddesi. `health.faz6_kilitleri` (`health.py:109`
kilit listesi, `health.py:148` hüküm metni) `sonuc_hukmu` kilidini "dört DOLAR ölçütünün DÖRDÜ de
sağlandı" diye tanımlar. Ölçülen paketin
PF'i 1,1119'dur; eşik 1,3. Yani **operatörün benimsediği, yerel-optimum kanıtlanmış paket, kendi
Faz-6 kilidini geri-test kanıtıyla açamaz.** Eşiğin gerekçesi (analytics.py:2090-2093) açıkça
"**95 işlemlik** bir defterde 1,0-1,2 bandı örneklem gürültüsünün içindedir" der — 885 işlemde bu
gerekçe artık aynı biçimde geçerli değil (gürültü bandı çok daha dar). Eşik mi taşınmalı, paket mi
iyileşmeli — bu bir OPERATÖR kararıdır ve bu belge hüküm vermez.

**`RESULT_NET_OVER_FRICTION` neden ölçülemedi:** ölçüm artefaktı
`islemler_cmb.json` işlem satırlarında `costs` alanı taşımıyor (satır projeksiyonu
`ts_open/ts_close/ticker/r_multiple/pnl_dollars/exit_reason/bars_held/regime/setup/qty/
risk_dollars/size_r` ile sınırlı; son ikisi de **null**). Toplam friksiyon üretilmeden bu ölçüt
hesaplanamaz. **Not:** işlem sayısı 2,16× arttığı için ödenen toplam friksiyon da ~2× artmıştır;
`slippage_bps: 5` işlem BAŞINA sabit olduğundan bu ölçütün paydası pakete duyarlıdır. Ölçüm
gerekir — sayı uydurulamaz.

### 3.3 `meridian/guard.py`

`LIMIT_KEYS` (guard.py:24-40) = `{autonomy_level, max_position_r, max_open_positions,
max_daily_loss_pct, max_sector_exposure_pct, no_trade_before_bars, kill_switch_file, heat_hard_r,
heat_review_r, corr_review, derisk_full_dd, derisk_floor_dd}` — **paketin dört direğinden üçü
burada** (slot, ısı zarfı, rampa) ve doğru yerde. **Dördüncüsü — `position_size_r` — burada DEĞİL,
bounds.yaml'da** (K-03).

| sabit | satır | değer | durum |
|---|---|---|---|
| `DISCIPLINE_MIN_RR` | 289 | 2.0 | TUTARLI — plan başına geometri; boyuttan bağımsız. Ölçümde rr_floor hiç NO_GO üretmedi |
| `REVIEW_RR_BAND` | 290 | 0.3 | TUTARLI (43 bayrak) |
| `REVIEW_SCORE_BAND` | 291 | 10 | TUTARLI (73 bayrak) |
| `HEAT_REVIEW_R` / `HEAT_HARD_R` / `CORR_REVIEW` | 299-301 | 3.5 / 5.0 / 0.85 | fail-safe yedek; goal ile senkron (`tests/test_kovab_dalga3_v166.py:191`) |
| `SECTOR_CAP_DEFAULT_PCT` | 428 | 25.0 | GERİLİM (uyuyan) — Y3 knob varsayılan 0; açılırsa 13 isimlik kitapta %25 ≈ 3 isim |
| `HEAT_CAP_DEFAULT_PCT` | 429 | 6.0 | GERİLİM (uyuyan) — ölçülen gerçekleşen ısı tepesi NAV **%4,63** (EDG-026), yani knob 6,0'da açılsa **atıl doğar** |

`classify_gate` sektör kuralı (guard.py:359-362) matematiksel olarak:
`(sc[sec] + 1) / max(1, max_open) > max_sector_exposure_pct/100` → 5 slotta `sc+1 > 2`,
20 slotta `sc+1 > 8`. Ölçüm bunu doğruluyor: **sector_cap NO_GO = 8** (heat_hard 607'ye karşı).

### 3.4 `meridian/score.py` — hedef üçlüsü

`score_detail` (score.py:119-126) **üç goal alanını da PAYDA olarak** kullanır:
`ret_c = realized_30d/0.07` · `dd_c = 1 − dd/0.16` · `sharpe_c = sharpe/2.4` ·
`composite = kıs(0,5·ret_c + 0,3·dd_c + 0,2·sharpe_c)`.

Ölçülen dünyada: **0,5·0,049 + 0,3·0,208 + 0,2·0,217 = 0,130**. Üç bacağın üçü de paydalarının
çok altında; skor artık dar bir bantta yaşıyor ve `rollback_if_worse_by = 0.10` bu bandın
neredeyse tamamı kadar (K-07). `TAIL_MIN_SAMPLE=12`, `TAIL_SIMS=20000`, `kelly_fraction`,
`tail_risk` — hepsi R/oran birimli, **paket-bağımsız**.

### 3.5 `meridian/shadowlaw.py` — PARA-v3 (asıl ship yasası)

| sabit | satır | değer | durum |
|---|---|---|---|
| `ANNUAL_TARGET_RETURN` | 58 | 0.25 | TUTARLI — pencere-eşlenik hedef 1,179 (1659g); ölçülen +0,2068 → `ret_c_v3 ≈ 0,175`. goal'ın %7/30g bacağından çok daha sağlıklı bir ölçek |
| `MARGIN_MONEY_SCALE` | 83 | 0.1908 | **KIRMIZI (K-06)** — σ(S_eski)=0,18644 dd paydası 0,08 iken ölçüldü |
| `MONEY_GATE_MARGIN` | 84 | 0.004 | **KIRMIZI (K-06, türev)** |
| `DD_VETO_MARGIN` | 97 | 0.04 | **KIRMIZI (K-01) — 2 test kırmızı** |
| `MEASURED_V3` | 103-116 | n=95, span 1274g | GERİLİM — eski dünyanın ölçüm kaydı; 885 işlemli dünyada yeniden ölçülmedi |

**K-01 ayrıntısı.** `DD_VETO_MARGIN`'in iki bağımsız türetimi vardı (shadowlaw.py:90-96):
(1) kendi gürültüsünün dışında — σ(düşüş)=0,0343 < 0,04 ✓ (bu bacak **hâlâ ayakta**, ama σ eski
dünyada ölçüldü); (2) **`goal.max_drawdown` = %8 bütçesinin tam yarısı** — bu bacak **koptu**:
0,16'nın yarısı 0,08'dir. Kopuş sessiz kalmadı, iki test onu yakalıyor
(`tests/test_para_yasasi_v127.py:220`, `tests/test_dalga_w1_v216.py:519`) ve **şu anda kırmızı**.

Aynı kopuşun **belge izleri** (aynı turda ele alınmalı, hepsi hâlâ %8 yazıyor):
`shadowlaw.py:17`, `:41`, `:43`, `:95`, `:144`, `:147`.

**K-06 ayrıntısı.** `MEASURED_V3.eski_paylar` (shadowlaw.py:107): dd %81,98 · sharpe %17,72 ·
para %0,29. Yani σ(S_eski)=0,18644'ün ezici çoğunluğu `0,3·σ(dd_c)` teriminden geliyordu ve
`σ(dd_c)=0,41822` (shadowlaw.py:110), payda 0,08 iken. Payda 0,16'ya çıkınca `dd_c = 1 − dd/0,16`
aynı düşüş dağılımına yarı duyarlılık gösterir → σ(dd_c) ≈ 0,209 → σ(S_eski) düşer. `MONEY_GATE_MARGIN`
tanımı gereği `0,02 × σ(ΔS_v3)/σ(S_eski)` olduğundan **payda küçülünce marj BÜYÜMELİDİR**; 0,004
olduğu yerde kalırsa kapı ölçülmemiş biçimde GEVŞER. Yeni σ değerleri **ÖLÇÜLMEDİ** — bu belge
sayı yazmaz; `shadowlaw.variance_attribution()` yeniden koşulmalıdır.

### 3.6 `meridian/reflect.py` · `meridian/validation.py` · `meridian/probgate.py`

| sabit | dosya:satır | değer | durum |
|---|---|---|---|
| `GATE_MARGIN` | reflect.py:18 | 0.02 | TUTARLI — legacy yol; bileşik ölçekte tanımlı, para yolunda MONEY_GATE_MARGIN bağlar |
| `TAIL_MARGIN_R` | reflect.py:19 | 0.5 | **TUTARLI** — R birimli, boyuttan bağımsız (§4) |
| `HOLDOUT_DIVERGENCE` | reflect.py:32 | 0.10 | TUTARLI — oransal |
| `DSR_MIN_N` / `DSR_TRIAL_VAR_MIN_N` | validation.py:94/99 | 20 / 5 | TUTARLI |
| `PBO_MIN_ADAY` / `PBO_BLOCKS` / `LEDGER_CAP` | validation.py:104/110/81 | 8 / 8 / 200 | TUTARLI — aday sayısına bağlı, pakete değil |
| `DSR_HARD_MIN` / `PBO_HARD_MAX` | validation.py:117/118 | 0.95 / 0.20 | GERİLİM — dürüstlük şerhi (K-18) |
| `P_BASE` / `P_CONFIRM` / `META_MIN_N` | probgate.py:33/37/47 | 0.80 / 0.70 / 5 | TUTARLI — olasılık birimli |

**K-18 ayrıntısı.** DSR/PSR **Sharpe türevidir** ve Sharpe boyuttan bağımsızdır — ama PSR'nin
payında `√(n−1)` vardır. İşlem sayısı 410→885 olunca **aynı işlem-Sharpe'ı daha yüksek bir
DSR üretir** (√885/√410 ≈ 1,47). Bu, kenarın iyileştiği anlamına GELMEZ; yalnızca aynı kenarın
daha çok gözlemle ölçüldüğü anlamına gelir. `DSR_HARD_MIN=0,95` sert kapısı Faz-6'nın beşinci
kilidi olduğu için (health.py:100-105) bu ayrımın kayda geçmesi gerekir. Eşiğe dokunmak
gerekmez; şerhi yazmak gerekir.

### 3.7 `meridian/skills.py` — Eksen-2 öneri eşikleri (brief'in özel sorusu)

| eşik | satır | değer |
|---|---|---|
| shadow (advisory) | `skills.py:408` | `avg_r <= -0.15` |
| lean_in | `skills.py:412` | `avg_r >= 0.30` |
| `AUTO_CF_MIN_N` | `skills.py:581` | 20 |
| `AUTO_AVG_R` | `skills.py:582` | −0.30 (advisory eşiğinin iki katı sertlik) |

**HÜKÜM: bu eşikler 0,5R dünyasında KAYMAZ.** Kanıt §4'te. Değişen şey eşik değil **popülasyon**:
`skills.py:713`'ün ölçüm tablosu `stockbee-momentum-burst n=0 avg_r=None n_cf=1080 → GERÇEK katman
BOŞ` diyor. mb 2026-08-12'de silahlandı (`strategy.py:1029` `ARMED_SETUPS`) ve geri-testte
**339 işlem / +0,083R** üretiyor. Yani `recommend_from_attribution()`ın en büyük kör noktası
kapanıyor — ama mb'nin yıl deseni zayıf (kart şerhi: 2022 −0,296 / 2026 −0,042; bu denetimin
kendi ölçümü: 2022 toplam R −0,333 n=39). Eşik değil, **izleme** kalemi.

### 3.8 Diğer paket-duyarlı sabitler

| sabit | dosya:satır | değer | durum |
|---|---|---|---|
| `EXPLORE_MAX_R` / `EXPLORE_MAX_POS` / `EXPLORE_TOTAL_R` | loop.py:22-24 | 0.25 / 5 / 1.25 | **GERİLİM (K-11)** |
| `MAX_ENTRY_GAP_PCT` | broker.py:17 | 0.04 | TUTARLI — `execution_v2.limit_pct_cap` ile aynı (goal.yaml:80); dış zarf artık bağlayan taraf, bilinçli |
| `ADV_CAP_PCT` / `MAX_NOTIONAL_PCT` / `IMPACT_COEF` | broker.py:18-20 | 0.02 / 0.25 / 0.10 | GERİLİM (K-15) |
| `RISK_PCT_PER_R` | broker.py:16 | 0.01 | TUTARLI — R'nin TANIMI; buna dokunmak R birimini değiştirir |
| `MIN_CF_ENTERED` / `MIN_CF_AVG_R` | arming.py:27-28 | 30 / 0.0 | TUTARLI — cf R saf fiyat geometrisi (§4) |
| `MAX_OPEN` / `DEFAULT_TIME_STOP` | counterfactual.py:24-25 | 2500 / 15 | GERİLİM (K-16) / TUTARLI |
| `FOLD_TARGET_N` / `FOLD_MIN_N` / `FOLD_K_TRY` | backtest.py:745-749 | 25 / 15 / (3,2) | TUTARLI — 2,16× akışla daha kolay doluyor |
| `LLM_PROMOTE_MIN_PAIRS/BUCKET/R_GAP` | analytics.py:1069-1071 | 30 / 8 / 0.3 | TUTARLI — R farkı boyuttan bağımsız |
| `MAE_STOP_TIGHT_R` / `MAE_STOP_SLIP_R` | analytics.py:3138-3139 | 0.70 / 1.15 | TUTARLI — R birimli |
| `EXIT_NUDGE_LEFT_R` | analytics.py:1185 | 0.5 | TUTARLI — R birimli |
| `BAND_MIN_N` (E3 ampirik) | analytics.py:3848 | 20 | TUTARLI |
| `DO_NOT_LIST` | analytics.py:2806 | 5 madde | GERİLİM (belge) — hermes prompt'una giriyor, ROADMAP §5 ile senkron tutulmalı; C+mb turunun dersleri (zarf-10, scale-out, turnover-w, rejim-eşiği 20) **listede yok** |

---

## §4 — R-BİRİMLİ EŞİKLER BOYUT DEĞİŞİNCE KAYAR MI? (**KANIT**)

Brief'in hipotezi: *"0,5R dünyasında aynı $ farkı YARI R eder → eşikler kayar mı?"*

**CEVAP: HAYIR. Bu kod tabanında R, `position_size_r`'den YAPISAL OLARAK BAĞIMSIZDIR.**
Üç satırlık kanıt zinciri:

1. **`meridian/broker.py:439-445` — `size_position`:**
   ```
   risk_dollars = size_r * RISK_PCT_PER_R * equity      # 0,5R → risk_dollars YARIYA iner
   per_share    = entry_fill - stop
   qty          = int(math.floor(risk_dollars / per_share))   # adet de YARIYA iner
   ```
2. **`meridian/broker.py:684` — `close_position`:**
   ```
   r_multiple = pnl / pos.risk_dollars
   ```
   `pnl ≈ qty × (çıkış − giriş)` ve `qty ∝ risk_dollars` olduğundan **pay ve payda aynı çarpanla
   ölçeklenir → R sabit kalır.** Aynı fiyat hareketi 0,5R'de yarı dolar ve yarı risk_dollars üretir;
   oran değişmez.
3. **Tavanlar bile R'yi bozmuyor** — `broker.py:526` (ADV tavanı) ve `broker.py:535` (notional
   tavanı) `qty`yi kırptıklarında `risk_dollars`ı **yeniden türetiyor**:
   `risk_dollars = qty * (base_fill - stop)`. Yani R, *nominal* riske değil **fiilen alınan riske**
   normalize kalıyor.
4. **Karşı-olgusal defter zaten tamamen boyutsuz** — `meridian/counterfactual.py:220`:
   `r_multiple = (exit_fill - entry) / rps`, `rps = entry - stop`. cf R saf fiyat geometrisidir,
   içinde `size_r` hiç geçmez.

**SONUÇ.** Şu eşiklerin HİÇBİRİ boyut değişiminden etkilenmez ve **hiçbirine dokunulmamalıdır**:
`skills.py:408` (−0,15) · `skills.py:412` (+0,30) · `skills.py:582` `AUTO_AVG_R` (−0,30) ·
`analytics.REGIME_AVG_R_MIN` (0,0) · `analytics.EDGE_CVAR5_MIN_R` (−1,5) ·
`analytics.MAE_STOP_TIGHT_R/SLIP_R` (0,70/1,15) · `analytics.EXIT_NUDGE_LEFT_R` (0,5) ·
`analytics.LLM_PROMOTE_R_GAP` (0,3) · `reflect.TAIL_MARGIN_R` (0,5) · `arming.MIN_CF_AVG_R` (0,0) ·
`guard.DISCIPLINE_MIN_RR` (2,0).

### 4.1 İKİNCİ MERTEBE ETKİ (küçük ama gerçek, ve ÖLÇÜLEMEDİ)

`broker.py:444`'teki `int(math.floor(...))` **kesir hisseyi atar ve bu yolda `risk_dollars`
YENİDEN TÜRETİLMEZ** (yalnız iki tavan dalında türetilir). Yani gerçekleşen R, tam-hisse
yuvarlaması kadar seyreltilir; adet yarıya inince bu göreli seyrelme **iki katına** çıkar.

Ölçülen vekil: ima edilen `risk_dollars` (=|pnl/R|) medyanı **456,9 $**, nominal 0,5R = 500 $
(−%8,6); p05 331 $ · p95 573 $. **AMA bu sayı yuvarlamayı iki tavanla (ADV + notional) karıştırır
ve yalnız-yuvarlama payı bu artefakttan ÖLÇÜLEMEZ**: `islemler_cmb.json`'daki `risk_dollars` ve
`size_r` alanlarının **885 satırının tamamı `null`** (ölçüm betiğinin satır projeksiyonu bu iki
alanı taşımıyor). Ayrıştırmak için `qty` + `entry` + `stop` üçlüsünü taşıyan bir dökümle yeniden
ölçüm gerekir.

### 4.2 DOLAR BİRİMLİ EŞİKLER **KAYAR** — asıl bakılacak sınıf bu

Boyut değişimi R'yi değil **doları** taşır. Bu yüzden gözden geçirilecek olanlar:
`analytics.RESULT_PF_MIN` (K-02, ölçüldü: 1,11 < 1,3) · `analytics.RESULT_NET_OVER_FRICTION`
(ölçülemedi) · `score.py`nin üç paydası (K-07/08/09) · `shadowlaw`ın para ölçeği (K-06) ·
`goal.max_daily_loss_pct` (NAV yüzdesi — ısı zarfı sabit kaldığı için TUTARLI).

---

## §5 — `state/bounds.yaml` KAPSAMA DENETİMİ

**Yürürlükteki 21 parametrenin (`state/strategy.yaml:3-20`) TAMAMI aralık-içi ve adım-üstü.
Aralık dışı kalan tek bir canlı değer YOK.** Nokta kontrolü:

| knob | canlı | bounds | ✓ |
|---|---|---|---|
| `position_size_r` | 0.5 | {0.1, 1.0, 0.1} | ✓ aralık+adım (bounds.yaml:12-15 bunu açıkça beyan ediyor) |
| `regime.min_exposure_score` | 40 | {0, 80, 5} | ✓ (EDG-030: 40 KALIR hükmü) |
| `entry.rs_rating_min` | 70 | {60, 95, 1} | ✓ |
| `entry.pivot_proximity_pct` | 2.3 | {0.5, 8.0, 0.1} | ✓ |
| `entry.min_volume_ratio` | 1.5 | {1.0, 4.0, 0.1} | ✓ |
| `entry.min_score` | 60 | {40, 90, 1} | ✓ |
| `exit.profit_target_r` | 2.5 | {2.0, 6.0, 0.5} | ✓ |
| `exit.time_stop_days` | 15 | {3, 40, 1} | ✓ |
| `exit.trail_atr_mult` | 2.5 | {1.0, 5.0, 0.1} | ✓ |
| `exit.breakeven_r` | 1.0 | {0.0, 3.0, 0.5} | ✓ |
| `stop_loss_atr_mult` | 2.0 | {0.8, 4.0, 0.1} | ✓ |
| `entry.w_prox` | 0.15 | {0.00, 0.40, 0.05} | ✓ |
| `exit.scale_out_r` / `_frac` | 2.0 / 0.0 | ✓ / ✓ | ✓ (EDG-029: scale-out kavramen elendi) |
| `exit.giveback_pct` · `chandelier_lookback` · `entry.max_ext_atr` · `rs_dual_horizon` | 0 | ✓ | ✓ (varsayılan kapalı) |

`max_open_positions` (20), `heat_hard_r` (5,0), `derisk_*` (0,15/0,36) → **bounds.yaml'da satırı
YOK ve olmamalı**; `guard.LIMIT_KEYS` üyeleri. bounds.yaml:105-131 bu kararı iki yasayla
(iki-sahip yasağı + hükümsüz-eksen yasağı) gerekçelendiriyor. **TUTARLI, dokunma.**

### 5.1 **K-03 — TEK KIRMIZI: yönetişim asimetrisi**

`state/goal.yaml:124` paketin iki direği için şunu yazıyor: *"İkisi AYRILMAZ: slot 20 tek başına
ısı zarfını 5R'de bağlar ve boyut yarıya inmeden ölçülen davranışı vermez."*

Ama iki direk **farklı yetki rejimlerinde** yaşıyor:

| direk | yer | Hermes önerebilir mi? |
|---|---|---|
| `max_open_positions = 20` | `goal.yaml` limits + `guard.LIMIT_KEYS` (guard.py:24) | **HAYIR** (guard.py:174 reddi) |
| `position_size_r = 0.5` | `strategy.yaml` params + `bounds.yaml:15` | **EVET**, 0,1–1,0 arası |

Yani öğrenme döngüsü, operatörün "ayrılmaz" ilan ettiği ikilinin **bir yarısını tek başına geri
çekebilir**. `position_size_r → 1,0` önerisi guard'ın hiçbir kapısına takılmaz (aralık-içi,
adım-üstü, LIMIT_KEYS'te değil) ve kapıdan ΔS ile geçerse canlıya iner. O noktada 20 slot × 1,0R =
20R nominal, 5R sert tavana karşı: kitap yine korunur (`heat_hard` bağlar) ama **isim başına risk
iki katına çıkar** ve ölçülen 885-işlemlik davranış ortadan kalkar — EDG-026'nın B kolu (slot5+1,0R:
410 işlem, +775$, dd %17,8, sharpe 0,018) bu yönün ölçülmüş hâlidir.

Üç meşru çıkış (karar operatörün): (a) bounds tavanını 0,5'e indir; (b) adı `LIMIT_KEYS`e taşı
(bounds satırı düşer — iki-sahip yasağı); (c) bilinçli bırak ve gerekçeyi bounds.yaml'a yaz.
ROADMAP §2-10(3)'ün "rampa/slot/boyut/ısı = HEP-PENCEREYE sınıfı" politikası (bounds.yaml:127)
**boyutu adıyla sayıyor** — yani politika (b)'yi işaret ediyor ama uygulama (a/c) yönünde durmuş.

### 5.2 Y3 portföy tavanlarının bantları

`portfolio.sector_cap` {0–30 %} ve `portfolio.heat_cap` {0–8 % NAV} (bounds.yaml:103-104) bantları
**5 isimlik kitap** varsayımıyla seçilmişti (ROADMAP §3.1: sektör ≤ %25-30, ısı ≤ NAV %6-8).
Ölçülen dünyada gerçekleşen ısı tepesi **NAV %4,63** (EDG-026) → `heat_cap` bandının ALT ucu (6,0)
bile **açılır açılmaz atıl doğar**. İkisi de varsayılan 0 (kapalı) olduğu için bugün etkisiz;
açılmadan önce bant yeniden ölçülmeli. **ÖLÇ.**

---

## §6 — ÖRNEKLEM / n EŞİKLERİ

Yeni paket aynı pencerede 2,16× işlem üretiyor (885 vs 410) → **her n-eşiği ~2× hızlı doluyor**.
Bu bilgi kazancıdır, kusur değil. Tek tek:

| eşik | dosya:satır | değer | ölçülen dünyada | durum |
|---|---|---|---|---|
| `goal.min_sample` | goal.yaml:33 | 30 | 2× hızlı | TUTARLI |
| `analytics.RESULT_N_MIN` | 2085 | 30 | 885 ✓ | TUTARLI |
| `analytics.IC_MIN_SAMPLE` | 785 | 30 | — | TUTARLI |
| `analytics.EDGE_IC_N_MIN` | 1571 | 60 | gerekçe metni bayat | GERİLİM (belge, K-14) |
| `analytics.REGIME_N_MIN` | 1580 | 30 | 2/4 rejim yapısal olarak 0 | GERİLİM (K-17) |
| `analytics.EDGE_TAIL_N_MIN` | 1608 | 40 | 885 ✓ | TUTARLI |
| `analytics.PRED_HIT_N_MIN` | 1576 | 10 | — | TUTARLI |
| `skills.AUTO_CF_MIN_N` | 581 | 20 | cf akışı arttı | TUTARLI |
| `arming.MIN_CF_ENTERED` | 27 | 30 | — | TUTARLI |
| `validation.DSR_MIN_N` | 94 | 20 | 885 ✓ ama √n etkisi (K-18) | GERİLİM (şerh) |
| `score.TAIL_MIN_SAMPLE` | 146 | 12 | ✓ | TUTARLI |
| `backtest.FOLD_MIN_N` / `FOLD_TARGET_N` | 745/747 | 15 / 25 | 2× kolay doluyor | TUTARLI |
| `analytics.WATERFALL_MIN_N` · `A4_BAND_MIN_N` · `MAE_MIN_N` · `ALFA_HUCRE_MIN_N` | 1257/2622/3137/493 | 5/3/10/5 | — | TUTARLI |

**K-17 ayrıntısı (en önemli n bulgusu).** 4,54 yıllık ölçümde **trend_down ve high_vol
rejimlerinde SIFIR işlem** var (trend_up 790, chop 95). `REGIME_N_MIN=30` bir eşik sorunu değil;
motor bu iki rejimde ya hiç plan üretmiyor ya da `regime.min_exposure_score=40` kapısı bütçeyi
sıfırlıyor. EDGE'in 4. ölçütü ("hangi rejimde tutuyor") bu iki rejim için **yapısal olarak
ÖLÇÜLEMEDİ**'de kalır ve bu durum eşiği indirmekle çözülmez. Ayrıca `strategy.yaml:30-34`
`params_by_regime` dört rejimde de **boş** — yani rejim-koşullu öğrenme için de kanıt tabanı yok
(bu, `EDG-2026-033-rejim-kosullu-boyut` kartının konusuydu).

---

## §7 — HİÇ DOKUNULMAMASI GEREKENLER (yanlış-pozitif önleme)

Aşağıdakiler **paket değişse de anlamını korur**. Bu listede olmak "ölçüldü ve doğru" demek değil;
"paket-bağımlı DEĞİL, bu turda gözden geçirilmesi gereksiz" demektir.

1. **`limits.heat_hard_r = 5.0`** — dört bağımsız ölçüm (EDG-026/028/032/035) bunu sistemin gerçek
   bağlayıcı kısıtı olarak gösterdi; 6,5/8,0/10 yönleri **ölçüldü ve elendi** (EDG-035: n artıyor,
   sharpe 0,521→0,278→0,369, monoton değil). En yüksek kanıt yoğunluklu sabit.
2. **`broker.RISK_PCT_PER_R = 0.01`** — bu bir eşik değil, **R'nin tanımı**. Değiştirmek tüm
   R-birimli defteri ve tüm R-eşiklerini aynı anda kaydırır.
3. **§4'te sayılan 11 R-birimli eşik** — boyuttan yapısal olarak bağımsız (kanıt §4). Bunları
   "0,5R'ye göre ayarlayalım" diye oynatmak, olmayan bir kaymayı düzeltmek olur.
4. **`guard.DISCIPLINE_MIN_RR = 2.0` · `REVIEW_RR_BAND = 0.3` · `REVIEW_SCORE_BAND = 10`** —
   plan-başına geometri; ölçümde rr_floor hiç NO_GO üretmedi.
5. **`goal.failure_below = -0.04`** — ölçülen dünyada geniş marjla güvenli, gerçek felaket sinyali.
6. **`max_open_positions = 20`** — EDG-035 "fiilen ölü knob" dedi (tepe 13). Ölü olması KUSUR
   DEĞİL: bağlayan taraf bilinçli olarak ısı zarfı. 13'e indirmek ölçülmemiş bir daraltmadır.
7. **`bounds.yaml`da satırı olmayan operatör kalemleri** (slot / ısı / rampa) — bounds.yaml:105-131
   iki yasayla gerekçelendirilmiş; oraya satır eklemek `regime.spy_sma_gate` mezar taşının
   anlattığı zararı (etkisiz eksen = harcanan arama bütçesi) geri getirir.
8. **`goal.yaml`ın inert alanları** (`explore_rate`, `backtest_gate`, `one_variable_only`,
   `kill_switch_file`, `schema_version`, `style`, `session_tz`) — hiçbir kod okumuyor, dosyanın
   kendi yorumları bunu beyan ediyor. Paketle ilgisiz.
9. **`goal.max_accepted_changes_per_month = 8`** — öneri debisi 2× arttığı için kotayı büyütmek
   cazip görünür; kotanın AMACI tam olarak buna direnmektir (anti-overfit kısma).
10. **`execution_v2` bloğu (goal.yaml:67-93) ve `pessimistic_band_v2` (:106-112)** — E1/E3 icra
    yasası; boyut/slot değişiminden bağımsız, ayrı kart hattı (EXE-2026-001-R1).
11. **`validation.PBO_*` / `probgate.P_BASE`** — aday sayısına ve olasılığa bağlı, pakete değil.

---

## §8 — ÖLÇÜLEMEDİ (uydurma yasağı gereği açıkça beyan)

| # | soru | neden ölçülemedi |
|---|---|---|
| Ö-1 | `RESULT_NET_OVER_FRICTION` (net PnL ≥ 1,0 × friksiyon) ölçülen pakette sağlanıyor mu? | `islemler_cmb.json` satır projeksiyonunda `costs` alanı yok; toplam ödenen friksiyon artefakttan türetilemez |
| Ö-2 | Yeni dünyada σ(S_eski), σ(dd_c), σ(ΔS_v3) — yani `MARGIN_MONEY_SCALE`/`MONEY_GATE_MARGIN`'in doğru değeri | `shadowlaw.variance_attribution()` 2000 replikasyonluk yeniden ölçüm ister; denetim ajanı ölçüm koşmaz |
| Ö-3 | `floor()` yuvarlamasının tek başına R seyreltmesi | `risk_dollars` ve `size_r` alanlarının 885 satırının tamamı `null`; ADV/notional tavanı ile ayrıştırılamıyor |
| Ö-4 | `EDGE_IC_MIN`/`PRED_HIT_*` ölçütleri yeni pakette geçiyor mu? | CANLI defter ölçütleri; geri-test artefaktı bu iki ölçütün girdisini (skor↔sonuç çiftleri, tahmin defteri) taşımıyor |
| Ö-5 | `counterfactual.MAX_OPEN = 2500` doluluğu mb silahlandıktan sonra ne oldu? | Canlı `cf_open.json` okunmadı (canlı state A1'de; denetim yerel salt-okuma) |
| Ö-6 | `DSR`/`PBO` değerleri yeni pakette | Canlı `validation_ledger.jsonl` + aday sayısı gerekir |
| Ö-7 | Sektör kırılımı (K-05'i doğrudan ölçmek: 13-isimlik kitapta sektör yığılması ne kadar?) | `islemler_cmb.json`'da `sector` alanı yok; NO_GO sayacı (8) dolaylı kanıt olarak kullanıldı |

---

## §9 — KAYNAKÇA (bu belgede kullanılan her dosya)

**Yapılandırma:** `state/goal.yaml` · `state/bounds.yaml` · `state/strategy.yaml`
**Kod:** `meridian/score.py` · `guard.py` · `analytics.py` · `shadowlaw.py` · `broker.py` ·
`skills.py` · `reflect.py` · `rollback.py` · `validation.py` · `probgate.py` · `loop.py` ·
`counterfactual.py` · `cf_backfill.py` · `arming.py` · `watchdog.py` · `health.py` ·
`hermes_runtime.py` · `backtest.py` · `strategy.py`
**Kartlar:** `research/cards/EDG-2026-026-slot20-boyut05.yaml` ·
`EDG-2026-028-isi-kosul-ayari.yaml` · `EDG-2026-032-final-paket-dogrulama.yaml` ·
`EDG-2026-035-yerel-duyarlilik.yaml`
**Ölçüm artefaktı:** `research/olcumler/edg032_final_paket_2026-08-12/{sonuc.json, sonuc_cmb.json,
islemler_cmb.json}`
**Testler (koşuldu):** `tests/test_para_yasasi_v127.py::test_dusus_vetosu_MARJI_kendi_gurultusunun_DISINDA`
· `tests/test_dalga_w1_v216.py::test_C5_dd_veto_margin_goalun_TAM_YARISIDIR` — **ikisi de KIRMIZI**
