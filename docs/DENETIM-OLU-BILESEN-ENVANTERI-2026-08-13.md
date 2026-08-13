# DENETİM — ÖLÜ BİLEŞEN ENVANTERİ (2026-08-13)

**Operatör gözlemi:** "sistemde çok fazla bileşen oldu ve bunların hepsinin birbiriyle uyumlu
çalışmadığını düşünüyorum."

**Rol-1 hipotezi (sınanan):** sistem çok BİLEŞENLİ olmaktan çok, çok ÖLÜ bileşenli — düğmeler
duruyor ama bir kısmı hiçbir şeye bağlı değil ya da başka bir şey onları eziyor.

**Kapsam:** salt-okuma. Repo kodu + canlı A1 (`ubuntu@130.61.126.87`, `/opt/meridian`) salt-okuma
sorguları. Repo koduna dokunulmadı, git koşulmadı, canlıya yazılmadı. Her satır `dosya:satır`
ya da canlı ölçüm çıktısıyla bağlıdır.

**Merkez soru — her bileşen için tek soru:** *"Bu değeri/bayrağı değiştirsem davranış DEĞİŞİR Mİ?"*
Dört kova: **CANLI** · **ÖLÜ** · **EZİLİYOR** · **ÖLÇÜLEMEDİ**.

---

## 0. HÜKÜM — hipotez DOĞRULANDI, ama ölümün şekli beklenenden farklı

**473 bileşen tarandı. 140 ÖLÜ + 56 EZİLİYOR = 196 (%41,4).** Operatörün "hepsi birbiriyle
uyumlu çalışmıyor" sezgisi sayıya çevrildiğinde: her 5 düğmeden 2'si ya hiçbir şeye bağlı değil
ya da başka bir kısıt tarafından her koşulda eziliyor.

**Ama 140 ölünün 105'i İKİ yapısal olgudan geliyor**, 105 ayrı hata değil:
93 skill bayrağı (motor registry'yi hiç okumuyor) + 12 okuyucusuz registry alanı.
Geri kalan **35 ölü bileşen** tek tek adlandırılmış ve §b'de kanıtlanmıştır.

**Modül sabitleri tarafında ölüm neredeyse YOK:** 172 sabitin yalnız **5**'inin üretim
okuyucusu yok. Yani kod tabanı "kullanılmayan sabit çöplüğü" DEĞİL. Ölüm iki yerde
yoğunlaşıyor: **yönetişim yüzeylerinde** (goal.yaml'ın 40 alanından 12'si ölü) ve
**skill katmanında** (93/93).

**Baskın patoloji ise ölüm değil EZİLME:** kod okuyor, operatör yürürlükte sanıyor, ama her
koşulda başka bir kısıt önce bağlıyor. On adet ezilme zinciri §c'de adıyla çıkarıldı.

**Ve en ağır bulgu hiçbir kovaya sığmıyor — ARAMA UZAYININ TAMAMI PRATİKTE ÖLÜ:**

> Canlı hipotez defterinde **52 hipotez var ve 52'si de reddedilmiş. Ship sayısı: 0.**
> (`state/hypotheses.jsonl` canlı: `rejected_by_backtest 27 · rejected_by_guard 22 ·
> superseded 2 · rejected_by_confirmation 1`.)
> `strategy.yaml` beş sürüm yaşadı ve bugünkü 18 parametreden **16'sı kodun tohum
> varsayılanıyla BİREBİR AYNI** (`config.default_strategy`, config.py:272-294). Farklı olan iki
> sayıdan biri operatör kalemi (`position_size_r` 1,0→0,5), diğeri öğrenme döngüsünün TEK hayatta
> kalan ürünü (`entry.pivot_proximity_pct` 2,0→2,3, v0002). Üçüncü bir sürüm (v0003,
> `entry.w_prox None→0,15`) **kodun varsayılanının aynısını yazdı** — defterin kendi notu
> "OOS None→None", yani ölçülemeyen bir değişiklik ship edildi ve davranış bit-bit aynı kaldı.
> Dördüncüsü (v0004, `regime.min_exposure_score` 40→20) geri alındı (v0005 parent=3).

Yani 32 eksenlik arama uzayı, 172 modül sabiti ve 75 ortam bayrağından oluşan bu makine, tüm
ömrü boyunca canlı davranışı **öğrenerek** tam **bir** sayı kadar değiştirdi. Operatörün
"birbiriyle uyumlu çalışmıyor" sezgisinin sayısal karşılığı budur.

---

## (a) SAYIM

| Tarama yüzeyi | Tarandı | CANLI | ÖLÜ | EZİLİYOR | ÖLÇÜLEMEDİ |
|---|---:|---:|---:|---:|---:|
| `state/goal.yaml` (18 üst + 4 `execution_v2` + 6 `pessimistic_band_v2` + 12 `limits`) | **40** | 18 | 12 | 7 | 3 |
| `state/bounds.yaml` arama eksenleri | **32** | 0 | 3 | 29 | 0 |
| `state/strategy.yaml` (18 param + 4 rejim haritası) | **22** | 18 | 4 | 0 | 0 |
| `strategy.py` paramları — yönetişim yüzeyi YOK (bounds'ta satırı yok) | **27** | 27 | 0 | 0 | 0 |
| Modül sabitleri (`analytics`/`guard`/`broker`/`shadowlaw`/`reflect`/`skills`/`loop`/`probgate`) | **172** | 150 | 5 | 17 | 0 |
| Ortam bayrakları (`MERIDIAN_*` / `HERMES_*`, Python'da okunan) | **75** | 57 | 11 | 3 | 4 |
| Skill registry bayrakları (31 etkin kayıt × `enabled`/`mode`/`shadow`) | **93** | 0 | 93 | 0 | 0 |
| Registry alanları — hiçbir okuyucusu olmayan | **12** | 0 | 12 | 0 | 0 |
| **TOPLAM** | **473** | **270** | **140** | **56** | **7** |

> **Sayım şerhi 1 — skill bayrakları.** 93'ü "ÖLÜ" sayıldı çünkü hiçbiri giriş/çıkış/boyut
> kararına dokunmuyor (§b-7). LLM istemine ve panoya etkileri VAR; o etki "trading davranışı"
> değildir ve budama önerisinde ayrı ele alınıyor (§d).
>
> **Sayım şerhi 2 — 172 modül sabitinin 150'si (uydurma yasağı).** Bu 150 için **üretim
> okuyucusunun VARLIĞI otomatik taramayla kanıtlandı** (kendi tanım satırı dışında en az bir
> kod referansı, yorum satırları elenerek). Her birinin ayrı ayrı BAĞLADIĞI ölçülmedi — yalnız
> brief'in adıyla saydığı alt kümede (§b-8) bağlayıcılık canlı defterden ölçüldü. "CANLI"
> sütunu bu 150 için "okuyucusu kanıtlı" demektir, "her koşulda bağlar" demez.
>
> **Sayım şerhi 3 — `strategy.yaml`ın 18 paramı.** Hepsi CANLI: değeri değiştirmek davranışı
> değiştirir (`strategy.py` `_f(params, …)` çağrıları, §b-6). Bunların 16'sının **kod tohumuyla
> aynı** olması bir "ölülük" değil, **öğrenme döngüsünün hiçbir şey hareket ettirmemiş olmasının**
> kanıtıdır — o ayrı ve daha ağır bir bulgudur (§0).

**ÖLÇÜM PENCERESİ ŞERHİ (uydurma yasağı):** kapı düşme oranları `state/meridian.db →
trade_plans` (409 plan, 2023-01-20 → 2026-08-07) üzerinden ölçüldü. Bu defter
**2026-08-12'nin slot20+0,5R paketinden ÖNCEDİR** — o dönemde `max_open_positions=5` ve
`heat_hard_r=4,5R` yürürlükteydi (ret metinleri "max 5 pozisyon dolu" / "%4.5R aşıyor" diyor).
Yeni zarf için bağlayıcılık kanıtı ayrı bir ölçümden gelir (EDG-2026-035, aşağıda).

---

## (b) TABLO — bileşen · dosya:satır · kova · KANIT

### b-1. `state/goal.yaml` — üst düzey (18)

| bileşen | dosya:satır | kova | KANIT | canlıysa etkisi |
|---|---|---|---|---|
| `schema_version: 1` | tek eşleşme `guard.py:15` (GOAL_KEYS üyeliği) | **ÖLÜ** | Üretimde okuyan kod yok. `storage.schema_version()` ayrı bir DB fonksiyonudur, bu anahtar değil (`storage.py:215,272`) | — |
| `universe: "S&P 500"` | tek eşleşme `guard.py:15` | **ÖLÜ** | `grep -E 'goal.*universe'` → 0 üretim okuyucusu. Evren gerçekte `state/finviz_universe.json` + `dataset.py`ten gelir | — |
| `style: "swing_momentum"` | tek eşleşme `guard.py:15` | **ÖLÜ** | `grep -E 'goal.*\bstyle\b'` → 0 sonuç | — |
| `session_tz` | tek eşleşme `guard.py:15` | **ÖLÜ** | Saat dilimi `barclock`/`exchange_calendars`tan gelir | — |
| `target_return_30d: 0.07` | `score.py:119` | **CANLI (yalnız rapor)** | `score.composite`in `ret_c` bileşenine girer; hiçbir emir yolunu kesmez | Karne sayısı değişir |
| `min_sharpe: 1.2` | `score.py:121,125` | **CANLI (yalnız rapor)** | Aynı; ayrıca `shadowlaw`ın payda türetiminde belgeli | Karne sayısı değişir |
| `max_drawdown: 0.16` | `score.py:120`, `analytics.py:171,3023` | **CANLI (yalnız rapor)** | Composite + `/api/diagnostics` kriter satırı | Rapor hükmü değişir |
| `failure_below: -0.04` | `watchdog.py:1697` | **CANLI** | `goal_failure_report()` → `GOAL_FAILURE` alarmı (`obs.py:47`) | Alarm eşiği kayar |
| `reflection_every: 5` | `hermes_runtime.py:120,375,525`, `hermes.py:4089` | **CANLI** | Yansıma kadansını belirler | Öğrenme turu sıklığı |
| `min_sample: 30` | `rollback.py:185,379`, `score.py:86`, `sprint_run.py:142`, +80 | **CANLI** | Ölçülebilirlik tabanı, her yerde | Hüküm ölçülebilirliği |
| `one_variable_only: true` | ad yalnız `guard.py:143` HATA METNİNDE | **ÖLÜ (düğme olarak)** | Kural KOŞULSUZ uygulanır (`len(changes)!=1` reddi); **değeri hiçbir kod okumaz**. `false` yazmak yasayı gevşetmez | — (yasa iyi, düğme yalan) |
| `backtest_gate: true` | tek eşleşme `guard.py:17` | **ÖLÜ** | Bir KAPI sözü verir, hiçbir davranışı yoktur. Gerçek kapılar `validation` DSR/PBO, `guard.classify_gate`, `health.faz6_kilitleri` — üçü de bu anahtara bakmaz | — |
| `rollback_if_worse_by: 0.10` | `rollback.py:207,401` | **CANLI** | Geri-alma eşiği | Rollback tetiklenmesi |
| `explore_rate: 0.15` | tek eşleşme `guard.py:17` | **ÖLÜ** | Keşif kararları `reflect --explore` CLI bayrağı + `loop` bütçe koşulundan gelir; ikisi de bu sayıyı okumaz | — |
| `max_accepted_changes_per_month: 8` | `guard.py:243` | **EZİLİYOR** | Kota kodu CANLI, ama **ship sayısı 0/52** → kota hiçbir zaman bağlamadı ve mevcut ret oranıyla bağlayamaz | Kota bağlasa ayda 8 ship sınırı |
| `commission_per_share: 0.0` | `backtest.py:154`, `loop.py:869`, `intraday_shadow.py:137` | **EZİLİYOR** | Okunuyor ama değer 0,0 → her çarpım 0. Değeri değiştirmek davranışı değiştirir, bugünkü değeri değiştirmiyor | Dolum maliyeti |
| `slippage_bps: 5` | `backtest.py:153`, `loop.py:868`, `counterfactual.py:30` | **CANLI** | `base_fill = açılış × (1+5/1e4)` — her dolum fiyatına giriyor | Her dolum fiyatı |
| `fill: next_bar_open` | tek eşleşme `guard.py:18` | **ÖLÜ** | `grep '"fill"\]\|get("fill"\|next_bar_open'` → hepsi defter satır alanı, bu anahtar değil. Dolum zamanlaması koda gömülü | — |

### b-2. `goal.yaml → execution_v2` (4) — E1 giriş icra yasası

| bileşen | dosya:satır | kova | KANIT |
|---|---|---|---|
| `limit_atr_mult: 100.0` | `broker.py:158` (`min(mult·ATR, pct_cap·t)`) | **EZİLİYOR** | 100·ATR her zaman %4·tetikten büyük (ATR/fiyat oranı ~%1) → `min()` **her zaman** `pct_cap`ı seçer. Bu eksen bilinçli olarak bağlamaz hâle getirildi (operatör kararı 2026-08-03) ama satır hâlâ ayarlanabilir bir düğme gibi duruyor |
| `limit_pct_cap: 0.04` | `broker.py:155,158` | **CANLI (henüz bağlamadı)** | Tek bağlayan taban. Canlı E2 defterinde 10 satır (`state/entry_execution.jsonl`): `fill_vs_limit_bps` hepsi tavanın 213–406 bps ALTINDA → tavan hiçbir emirde bağlamadı (`docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md:20`) |
| `gap_behavior: marketable_limit` | `broker.py:196` `gap = (rp is None) or (t>0 and rp>=t)` | **EZİLİYOR (koşul TOTOLOJİ)** | Yedi kurulumun **hepsinde** `entry_trigger = float(c)` = sinyal barı kapanışı (`strategy.py:509,571,623,678,784,862,989`); canlı yolda `ref_price` de aynı kapanış → `rp >= t` her zaman doğru. Canlı ölçüm: E2 defterinde **4/4 satırda `gap_at_submit: true`**. Yani bu bir "gap FİLTRESİ" değil, giriş motorunu tamamen kapatan bir anahtar |
| `tif: gtc` | `broker.py:102` `ENTRY_TIF_ALLOWED = ("gtc",)` | **ÖLÜ (düğme olarak)** | Beyaz-liste **tek uçlu**. Başka herhangi bir değer sessizce `gtc`ye düşer → bu alana ne yazılırsa yazılsın davranış aynı |

### b-3. `goal.yaml → pessimistic_band_v2` (6)

| bileşen | dosya:satır | kova | KANIT |
|---|---|---|---|
| `acilis_spread_bps: 20.0` | `analytics.py:4033` | **CANLI (yalnız rapor)** | `net_kotumser` ikiz sütunu; karar yüzeyine (probgate/prescreen) girmez — blok beyanı goal.yaml'da yazılı |
| `mevcut_model_bps: 10.0` | `analytics.py:4051` | **CANLI (yalnız rapor)** | Aynı |
| `ampirik_bps: null` | `analytics.py:4036` | **ÖLÇÜLEMEDİ** | E2 defteri 10 satır; kalibratör (`pessimistic_band_update`) henüz dolduramadı. Dürüst boş |
| `ampirik_n: 0` / `ampirik_guncelleme: null` | `analytics.py:4048` civarı | **ÖLÇÜLEMEDİ** | Aynı |
| `kaynak: "Bogousslavsky…"` | — | **ÖLÜ** | Belge dizisi; hiçbir kod okumaz (ve okumamalı) |

### b-4. `goal.yaml → limits` (12) — sert risk zarfı

| bileşen | dosya:satır | kova | KANIT (canlı defter: 409 plan) | etkisi |
|---|---|---|---|---|
| `autonomy_level: 0` | `guard.py:280`, `config.live_enabled` | **CANLI** | Canlı-para yolunu kapatan kilit; `adapters/alpaca.py:161` fırlatır | Gerçek para |
| `max_position_r: 1.0` | `guard.py:366` | **EZİLİYOR** | `position_size` kontrolü **0/409 düştü**. Plan `size_r` dağılımı 0,25–0,97 — tavan hiç görülmedi. `position_size_r=0,5` × rampa çarpanı ≤ 1,0 asla 1,0'ı geçemez | Bağlasa boyut tavanı |
| `max_open_positions: 20` | `guard.py:356` | **EZİLİYOR** | **EDG-2026-035 yapısal bulgusu:** eşzamanlı pozisyon tepesi **13 (<20)**, slot25 kolu tabanla **BAYT-ÖZDEŞ** (ΔCI=[0,0]). Bağlayan kaynak ısı zarfı (gerçekleşen tepe tam 5,000R) | Tek gerçek etkisi sektör tavanı paydası (§c-1) |
| `max_daily_loss_pct: 3.0` | `guard.py:363` | **EZİLİYOR** | `daily_loss_breaker` **0/409 düştü** — kâğıt defterinde hiçbir gün −%3'e inmedi | Bağlasa gün kapatır |
| `max_sector_exposure_pct: 40.0` | `guard.py:359-361` | **CANLI (zayıfladı)** | `sector_cap` 6/409 (%1,5) düştü — **ama o ölçüm `max_open=5` dönemine ait**. Payda 20 olunca isim tavanı 2→8'e çıktı; EDG-035 slot15 kolunda sector_cap NO_GO'nun 8→33'e fırladığını ölçtü | Sektör çeşitlendirme |
| `no_trade_before_bars: 3` | **tek okuyucu** `backtest.py:151` | **ÖLÜ (canlıda)** | `grep -rn no_trade_before_bars meridian/` → yalnız `guard.py:25` (LIMIT_KEYS üyeliği) + `backtest.py:151`. **Canlı `loop.py` bu limiti hiç okumuyor** — replay'de uygulanan, canlıda uygulanmayan bir kural | Motor ayrışması riski |
| `heat_hard_r: 5.0` | `guard.py:322,376` | **CANLI — BAĞLAYAN KISIT** | `heat_hard` 18/409 düştü; EDG-028/032/033/035 dördü de aynı yasayı ölçtü: gerçekleşen ısı tepesi **tam 5,000R** | Kitabın gerçek tavanı |
| `heat_review_r: 3.5` | `guard.py:323,384` | **CANLI (yumuşak)** | 47/409 (%11,5) düştü | REVIEW bayrağı |
| `corr_review: 0.85` | `guard.py:324,387` | **CANLI (yumuşak)** | 4/409 (%1,0) düştü | REVIEW bayrağı |
| `derisk_full_dd: 0.15` | `broker.py:286` | **CANLI (bugün atıl)** | Rampa 2026-08-12'de kablolandı ve üç motorda da uygulanıyor (`loop.py:705,1327`, `backtest.py:224`, `shadow_*`). Bugünkü çekilme < %15 → çarpan 1,0. Değer değişse davranış değişir | Emir boyu |
| `derisk_floor_dd: 0.36` | `broker.py:288` | **CANLI (bugün atıl)** | Aynı | Emir boyu |
| `kill_switch_file: "state/HALT"` | tek eşleşme `guard.py:25` | **ÖLÜ** | `health.py` yolu SABİT kodlar (`STATE/"HALT"`), bu anahtara hiç bakmaz. Yolu değiştirmek kill-switch'i TAŞIMAZ | — |

### b-5. `state/bounds.yaml` — 32 arama ekseni

Hermes'in bunları **denediği doğrulandı**: 32 eksenden 24'ü hipotez defterinde en az bir kez
görünüyor. Hiç önerilmemiş 8: `entry.w_turnover`, `exit.trail_atr_mult`, `portfolio.heat_cap`,
`portfolio.sector_cap`, `position_size_r`, `regime.vix_backwardation_gate`, `stop_buffer_atr`,
`stop_mode`.

**Ama denenen eksen davranışa DÖNÜŞMÜYOR:** 52 öneri, 0 ship. Kova hükmü bu yüzden
**EZİLİYOR (29 eksen)** — eksen okunuyor, örnekleniyor, ölçülüyor; ship kapısı (§c-3) her
seferinde önce bağlıyor.

| eksen sınıfı | n | kova | KANIT |
|---|---:|---|---|
| `strategy.yaml`da karşılığı OLAN eksenler | 18 | **EZİLİYOR** | Değiştirilebilirler ama 52/52 ret; canlı değerlerin 16'sı hâlâ kod tohumu |
| `strategy.yaml`da karşılığı OLMAYAN, motor varsayılana düşen eksenler | 11 | **EZİLİYOR** | `_f(params, key, default)` (`strategy.py:327`) → param yoksa kod varsayılanı. Ship edilirse etki DOĞAR (yol açık), bugün 0 |
| `regime.vix_backwardation_gate` | 1 | **ÖLÜ** | `regime.VIX_DATA_STATUS` = veri_yok (Massive 403 + FMP boş, 2026-07-30 doğrulandı) → knob 1 yapılsa bile hüküm üretemez |
| `portfolio.sector_cap`, `portfolio.heat_cap` | 2 | **ÖLÜ (bugün)** | `guard.py:550` `p.get("portfolio.sector_cap", 0)` → knob yok → 0 → blok tamamen atıl. Kablo 2026-08-02'de bağlandı, ama `strategy.yaml` bu iki adı taşımıyor |

**MEZAR TAŞI DOĞRULANDI:** `regime.spy_sma_gate` satırı bounds'tan düşürülmüş (8b6bbbc) ve
üç çivi testi geri gelmesini yasaklıyor. Emeklilik doğru yapılmış — bu, diğer ölü eksenler
için izlenecek emsaldir.

### b-6. `state/strategy.yaml` (22)

| bileşen | kova | KANIT |
|---|---|---|
| 18 paramın tamamı | **CANLI** | `strategy.py` `_f(params, …)` ile okuyor (satırlar §b-8 altındaki eşleme); değeri değiştirmek davranışı değiştirir |
| …ama **16'sının değeri kod tohumuyla BİREBİR AYNI** | *(ölülük değil, hareketsizlik)* | `config.default_strategy()` (config.py:276-293) ile karşılaştırıldı. Dosyayı bugün silsek davranış değişmezdi — bu, dosyanın ölü olduğunu değil **öğrenme döngüsünün hiçbir şey hareket ettirmediğini** söyler |
| `entry.pivot_proximity_pct: 2.3` (tohum 2,0) | **CANLI — döngünün TEK ürünü** | v0002, "coordinate-descent: entry.pivot_proximity_pct 2.0→2.3 (OOS 0.1963→…)". Sistemin ömrü boyunca öğrenerek değiştirdiği tek sayı |
| `position_size_r: 0.5` (tohum 1,0) | **CANLI — operatör kalemi** | v0005 (2026-08-12), `strategy.py:487` okuyor. Öğrenme döngüsü ürünü DEĞİL (notu bunu kendisi söylüyor) |
| `entry.w_prox: 0.15` | **CANLI (ama ship'i NO-OP'tu)** | v0003 notu: "coordinate-descent: entry.w_prox None→0.15 (**OOS None→None**)". 0,15 **kodun varsayılanının aynısı** (`strategy.py:419`) → ölçülemeyen bir değişiklik ship edildi, sürüm numarası arttı, davranış bit-bit aynı kaldı |
| `params_by_regime: {trend_up:{}, trend_down:{}, chop:{}, high_vol:{}}` | **ÖLÜ (4 harita)** | Dördü de BOŞ. `config.resolve_params` (config.py:264-269) boş haritada `dict(params)` kopyası döner → rejim çözümü kimlik fonksiyonu. Canlı doğrulandı (A1 `strategy.yaml`) |

### b-7. Skill registry (93 bayrak + 12 alan) — **TAMAMI KARAR YOLUNDA ÖLÜ**

| bulgu | KANIT |
|---|---|
| `strategy.py` skill registry'yi **hiç okumuyor** | `grep -c "skills" meridian/strategy.py` → **0**. `grep -in "skill"` → 2 hit, ikisi de yorum (`strategy.py:691,1001`) |
| Gerçek düğme registry değil, bir Python tuple'ı | `strategy.py:1029` `ARMED_SETUPS = ("breakout_vcp","pullback","exhaustion_hammer","momentum_burst")` |
| `shadow: true` bir skill'i durdurmuyor — **canlı vaka** | `pullback-screener` registry'de `enabled:true, mode:shadow, shadow:true` ve `skill_recommendations.jsonl` `applied:true`. Ama `pullback` **ARMED_SETUPS içinde** ve `scan_all` onu koşulsuz çağırıyor (`strategy.py:1052`) → gölgedeki skill **silahlı koşuyor** |
| Sistem bunu KENDİ ÖLÇTÜ ve söyledi | Canlı `state/skill_auto_shadow.json`: pullback-screener n_cf=21, cf_avg_r=−0,968 → "kanıt eşiği AŞILDI ama skill MOTOR-İÇİ: registry'ye `shadow` yazmak davranışı **DEĞİŞTİRMEZ**" |
| `mode` yalnız yazılıyor, hiç dallanmıyor | Yazım `skills.py:207,735,737`; tek okuma `skills.py:448` (pano geçişi). Hiçbir `mode == ...` dalı yok |
| `enabled:false` yalnız LLM yüzeyinde onurlandırılıyor | `hermes.py:2988` (symlink), `hermes.py:3084` (ön-yükleme). Motor kodunu durdurmaz: `vcp-screener.enabled=false` yapmak `evaluate_entry`i durdurmaz |
| `lean_in` eylemi **yapısal olarak uygulanamaz** | `skills.py:619` eşiği `lean_in` üretir; `apply_skill_action` (skills.py:716-722) onu reddeder çünkü `ONERILEBILIR_EYLEMLER`de var, `UYGULANABILIR_EYLEMLER`de yok |
| Hiçbir okuyucusu olmayan 12 registry alanı | `api_free`, `agent_authored`, `failure_count`, `engine`, `retired_at`, `retired_folder`, `retired_requires`, `retired_from_pipeline`, `merged_into`, `denetim_notu`, `aktivasyon_kosulu`, `stale_last_run_cleared` — her biri `grep` ile 0 hit |

### b-8. Modül sabitleri — 172 tarandı, 5'inin üretim okuyucusu YOK

| sabit | dosya:satır | kova | KANIT |
|---|---|---|---|
| `guard.SECTOR_CAP_DEFAULT_PCT = 25.0` | `guard.py:428` | **ÖLÜ** | `_y3_portfolio_caps` (guard.py:550) `p.get("portfolio.sector_cap", **0**)` yazıyor — bu sabite hiç düşmüyor. Yorumu bile itiraf ediyor: "kapı KAPALIYKEN hiç okunmaz" |
| `guard.HEAT_CAP_DEFAULT_PCT = 6.0` | `guard.py:429` | **ÖLÜ** | Aynı |
| `guard.Y3_PORTFOLIO_FIELDS` / `Y3_PLAN_FIELDS` | `guard.py:443-444` | **ÖLÜ (üretimde)** | Tek okuyucular test dosyası (`tests/test_kovab_dalga3_v166.py:105,106,382,400`) — üretim-sözleşmesi beyanı |
| `shadowlaw.E_REPORT_CANDIDATES` | `shadowlaw.py:573` | **ÖLÜ (üretimde)** | Tek okuyucu `tests/test_hafta3b_v125.py:267` |

**Brief'in adıyla sorduğu sabitler:**

| sabit | dosya:satır | kova | KANIT |
|---|---|---|---|
| `broker.ADV_CAP_PCT = 0.02` | `broker.py:18,521` | **EZİLİYOR** | Canlı iki-uçlu ölçüm: katılım 1e-5…8e-4, etki **≤0,8 bps**; %2×ADV = 1.419 hisse vs sipariş 25 → **hiçbir emirde bağlamadı** (`docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md:225-228`) |
| `broker.IMPACT_COEF = 0.10` | `broker.py:19,528` | **EZİLİYOR** | Aynı ölçüm: dolum etkisi 0,01–0,04 bps |
| `broker.MAX_NOTIONAL_PCT = 0.25` | `broker.py:20,532` | **CANLI** | Stop mesafesi fiyatın %4'ünden darsa bağlar (`strategy.py:200-202` cebri) — dar-stoplu isimlerde gerçek kısıt |
| `broker.DERISK_FULL_DD/FLOOR_DD` | `broker.py:31-32` | **EZİLİYOR (fail-safe)** | `derisk_ramp()` goal.yaml'ı okur; kod değerleri onunla AYNI (0,15/0,36) → asla görünmez. **Bilinçli** (§e) |
| `broker.ENTRY_LIMIT_ATR_MULT/PCT_CAP` | `broker.py:94-95` | **EZİLİYOR (fail-safe)** | goal.yaml `execution_v2` her zaman üstünde |
| `broker.ENTRY_TIF_ALLOWED = ("gtc",)` | `broker.py:102` | **CANLI ama tek-uçlu** | Tek-elemanlı beyaz-liste `goal.execution_v2.tif` alanını ölü düğmeye çeviriyor (§b-2) |
| `guard.DISCIPLINE_MIN_RR = 2.0` | `guard.py:289,372` | **EZİLİYOR** | `rr_floor` **0/409 düştü** — `exit.profit_target_r` alt sınırı (bounds 2,0) tavanı tabanın üstünde tuttuğu için taban yapısal olarak bağlayamıyor |
| `guard.LIVE_DEAD_KNOBS` | `guard.py:54` | **ÖLÜ (bilinçli boş)** | Sözlük bugün boş; ikinci savunma hattı. Yanlış-pozitif (§e) |
| `loop.EXPLORE_MAX_POS = 5` (+ `EXPLORE_MAX_R`, `EXPLORE_TOTAL_R`) | `loop.py:22-24,1859` | **EZİLİYOR** | Canlı olay defteri (2026-07-14→08-13): `explore_slot_llm_pick` **102**, `exploration_armed` **1**. Plan defterinde `exploration=1/409`. 5 slotluk bütçe bir ayda bir kez bile dolmadı — tavan değil ÜRETİCİ kurumuş |
| `analytics.EDGE_*` / `RESULT_*` / `PRED_*` / `REGIME_*` (12 eşik) | `analytics.py:1566-1621, 2085-2098` | **CANLI (yalnız rapor)** | `edge_verdict`/`result_verdict` → `health.faz6_kilitleri` + pano. Ama `health.py:107` beyanı: **"BU FONKSİYON HİÇBİR ŞEY SİLAHLAMAZ VE HİÇBİR DOSYAYA YAZMAZ"** — Faz 4b silahlama bacağı bu zincire bağlı değil |
| `probgate.P_BASE = 0.80` | `probgate.py:33` | **CANLI — BAĞLAYAN KAPI** | Hipotez defterindeki **16 ret** doğrudan bu eşikten: "P(ΔS>0)=… < gerekli 0.80" |
| `probgate.META_MIN_N = 5` / `META_LOOKBACK = 8` | `probgate.py:47-48` | **EZİLİYOR** | Canlı `gate_calibration.json`: `n_measured: 1`, `durum: "kurak"`, `extra_p: 0.0` → meta-ayar mekanizması canlı ama kanıt kuraklığından hiç ateşlemedi |
| `reflect.GATE_MARGIN = 0.02` | `reflect.py:18` | **CANLI (ikincil)** | 4 ret ("candidate OOS … did not beat incumbent + 0.02") — P_BASE'in 16'sının gölgesinde |
| `reflect.HOLDOUT_DIVERGENCE = 0.10` | `reflect.py:34` | **CANLI (bayrak)** | Kendi yorumu: "does NOT block the ship" — yalnız `overfit_suspect` etiketi |
| `skills.MIN_N = 8`, `AUTO_CF_MIN_N`, `AUTO_AVG_R`, `AUTO_MAX_PER_RUN` | `skills.py:487,809-811` | **CANLI (yalnız advisory)** | Registry'ye `shadow` yazar; registry karar yolunda ölü (§b-7) → hiçbir emri değiştiremez |
| `shadowlaw.MEASURED_V2` / `V2_WEIGHT_TRIALS` / `WHY_40_UNREACHABLE` / `OLD_LAW_*` | `shadowlaw.py:67,126-145` | **CANLI (yalnız rapor)** | Tek tüketici `analytics.py:3089-3111` → pano "yasa geçişi" paneli. Tarihî kayıt; hüküm üretmez |

### b-9. Ortam bayrakları (75)

Canlı A1 birim dosyasında (`/etc/systemd/system/meridian.service`) **11** bayrak set edilmiş;
repo `deploy/oracle-a1/meridian.service` ile bayt-özdeş. Diğer her şey kod varsayılanıyla koşuyor.

| sınıf | n | kova | not |
|---|---:|---|---|
| Canlıda set + varsayılandan FARKLI | 8 | **CANLI** | `MERIDIAN_BROKER=alpaca_paper`, `AUTOSTART_CYCLE/HERMES=1`, `SPRINT_SYSTEMCTL`, `PARALLEL_PROBES=1`, `SEARCH_MAX_MIN=60`, `HERMES_SEARCH_BUDGET=8`, `DASH_TOKEN` |
| Canlıda set ama varsayılana EŞİT | 3 | **EZİLİYOR (gereksiz)** | `CYCLE_POLL_SECONDS=300`, `HERMES_POLL_SECONDS=300`, `MERIDIAN_BIND_HOST=127.0.0.1` (bu üçüncüsü `ExecStart` interpolasyonu için yine de gerekli) |
| Hiç set edilmemiş, varsayılan GERÇEK bir dalı açıyor | 18 | **CANLI** | `MERIDIAN_MIRROR_STREAM`, `MARKET_STREAM`, `INTRADAY`, `BAR_ARCHIVE`, `TREND_SHADOW`, `SHADOW*`, `BG_REFLECT`, `WARMUP_SPRINTS`, `MODE`, `I_ACCEPT_RISK`… |
| Saf ayar sayıları (varsayılan koşuyor) | 31 | **CANLI** | `AGENT_RPM/RPD`, `HERMES_PRICE_*`, `BRAIN_COOLDOWN_*`, `BARS_MAXLEN`… |
| Hiç set edilmemiş, varsayılan dalı ATIL bırakıyor | 8 | **ÖLÜ (bugün) / silahlanabilir** | `MERIDIAN_CORS_ORIGINS`, `MERIDIAN_DB`, `DD_MTM_VETO`, `WS_DISCONNECT_CANCEL_ENTRIES`, `FINVIZ_PUBLIC`, `FORCE_RESEED`, `FORCE_BASELINE`, `STREAM_MAX_SYMBOLS` — hepsi **kill-switch/acil vana** (§e) |
| A1'de yapısal olarak ölü | 3 | **ÖLÜ** | `CREDENTIALS_DIRECTORY` (drop-in dizini A1'de YOK → token `.dash.env` üzerinden process env'de, yani drop-in'in önlemek için yazıldığı hâlde), `MERIDIAN_GCP_PROJECT` (canlı env'de yok), `MERIDIAN_SUPERVISED` (macOS-only) |
| Ölçülemedi (çağrı sıklığı kanıtlanmadı) | 4 | **ÖLÇÜLEMEDİ** | Statik çağrı zinciri izlendi, her döngüde ateşlediği kanıtlanmadı |

**Yan bulgu (dağıtım hijyeni):** `/opt/meridian/.env` yalnız `meridian-barsarchive.service`
tarafından yükleniyor ve içinde `MERIDIAN_DASH_TOKEN` var — `barsarchive.py` o anahtarı hiç
okumuyor. Arşivci, işine yaramayan bir pano sırrının kopyasını taşıyor.

---

## (c) EZİLME ZİNCİRLERİ — "A ayarı var ama B her zaman önce bağlıyor"

### c-1. SLOT SAYISI ← ISI ZARFI *(ölçülmüş, dört kez)*
`max_open_positions: 20` var; **bağlayan `heat_hard_r: 5,0R`**.
0,5R'lik pozisyonlarla 5R zarfı ~10 isimde dolar. EDG-2026-035 yapısal bulgusu: eşzamanlı
pozisyon tepesi **13 < 20**; **slot25 kolu tabanla BAYT-ÖZDEŞ** (ΔCI=[0,0]); gerçekleşen ısı
tepesi **tam 5,000R**. Slot knobu'nun tek kalan etkisi yan kanaldır: sektör tavanı paydası
`max_open`tır (`guard.py:356`) → isim tavanı 20'de 8, 15'te 6; slot15'te sector_cap NO_GO 8→33.
**"Slot" düğmesi fiilen "sektör çeşitlendirme" düğmesidir ve adı bunu söylemiyor.**

### c-2. GİRİŞ LİMİTİ: ATR BACAĞI ← YÜZDE TAVANI
`limit_atr_mult: 100,0` var; **bağlayan `limit_pct_cap: %4`**.
`min(100·ATR, 0,04·tetik)` — ATR/fiyat ~%1 olduğu için `min()` her zaman ikinciyi seçer
(`broker.py:158`). Bilinçli bir karardı, ama satır hâlâ ayarlanabilir bir eksen gibi duruyor.

### c-3. TÜM ARAMA UZAYI ← SHIP KAPISI
32 eksen + 172 sabit + Hermes'in tüm arama makinesi var; **bağlayan `probgate.P_BASE = 0,80`**.
52 hipotez → **0 ship**. Ret dağılımı: `P(ΔS>0) < 0,80` **16 kez**, "already tried and failed"
**22 kez** (bunun **20'si tek bir değer**: `stop_loss_atr_mult=2,1`), `GATE_MARGIN` 4 kez,
OOS-aşınması 2 kez, min_sample-altı 1 kez.
İkincil ezilme: `guard.max_accepted_changes_per_month=8` kotası, ship olmadığı için hiç bağlamadı.

### c-4. KEŞİF BÜTÇESİ ← ÜRETİCİ KURAKLIĞI
`EXPLORE_MAX_POS = 5` slot var; **bağlayan yukarı akış**.
Bir aylık canlı defterde `explore_slot_llm_pick` **102**, `exploration_armed` **1**.
Tavanı 50 yapsak hiçbir şey değişmezdi — tavan bağlamıyor, kaynak kurumuş.

### c-5. SKILL BAYRAKLARI ← `ARMED_SETUPS` TUPLE'I
31 skill × `enabled`/`mode`/`shadow` var; **bağlayan `strategy.py:1029`**.
`pullback-screener` gölgede (`shadow:true`, `applied:true`) ve **silahlı koşuyor**.
Sistem bunu kendi ölçtü ve `skill_auto_shadow.json`a yazdı — ama düğme panoda hâlâ
"gölge" diyor.

### c-6. R:R TABANI ← BOUNDS ALT SINIRI
`DISCIPLINE_MIN_RR = 2,0` sert veto var; **bağlayan `bounds: exit.profit_target_r.min = 2,0`**.
Hedef R'nin alt sınırı tabanın üstünde tutulduğu için taban yapısal olarak ateşleyemez:
`rr_floor` **0/409**.

### c-7. META-KALİBRASYON ← KANIT KURAKLIĞI
`probgate.META_MIN_N = 5` / `META_LOOKBACK = 8` var; **bağlayan ship kuraklığı** (c-3).
Canlı: `n_measured: 1`, `durum: "kurak"`. Kapı kendi eşiğini ayarlayamıyor çünkü ayarlayacak
kanıt hiç birikmiyor.

### c-8. LLM GÖRÜŞ KALİBRASYONU ← GÖRÜŞ KURAKLIĞI
`LLM_PROMOTE_MIN_PAIRS = 30` var; **bağlayan görüş yokluğu**.
Canlı `sieve.json`: 97 gerçek işlemin **93'ü** "llm_görüşü_yok" diye düşüyor →
`llm_calibration.json` `n_pairs: 4`, `promoted: false`. Eşik 30, ulaşılan 4.

### c-9. FAZ-6 KİLİTLERİ ← YAZILMAMIŞ SİLAHLANMA BACAĞI
5 kilit + 12 analytics eşiği var; **bağlayan tüketici yokluğu**.
`health.py:107`: *"BU FONKSİYON HİÇBİR ŞEY SİLAHLAMAZ… bugün hiçbir kod yolu otonom intraday
emir göndermiyor."* (Not: intraday 4b gönderim bacağı 2026-08-11'de yazıldı ve
`intraday_arm_flag_on_but_4b_not_built` olayı 08-11'den sonra sıfırlandı — 08-07/10/11'de
855/1213/1185, 08-12 ve 08-13'te **0**. Bu zincirin bir ucu KAPANDI; kilit fonksiyonunun
tüketicisi hâlâ bağlanmadı.)

### c-10. LİKİDİTE MODELİ ← EMİR BOYUTUNUN KÜÇÜKLÜĞÜ
`ADV_CAP_PCT %2` + `IMPACT_COEF 0,10` var; **bağlayan hiçbir şey**.
Katılım 1e-5…8e-4 → etki ≤0,8 bps; %2×ADV=1.419 hisse vs sipariş 25.

---

## (d) BUDAMA ÖNERİSİ

### D-1. KALDIR (koddan+config'ten sil, mezar taşıyla) — 14 kalem

Emsal hazır ve bu depoda çalışıyor: `regime.spy_sma_gate` mezar taşı (bounds.yaml, 8b6bbbc) —
düşen satır + neden + üç sessiz-diriliş çivisi. Aynı şablon uygulanmalı.

| kalem | gerekçe |
|---|---|
| `goal.yaml`: `schema_version`, `universe`, `style`, `session_tz`, `backtest_gate`, `explore_rate`, `kill_switch_file`, `fill` (8) | Tek eşleşmeleri `guard.GOAL_KEYS` üyeliği. `backtest_gate` ve `kill_switch_file` **en tehlikelileri**: biri "kapı", diğeri "kill-switch" sözü veriyor ve ikisi de hiçbir şey yapmıyor. Operatör bir acil durumda `kill_switch_file`ı değiştirip kill-switch'i taşıdığını sanabilir |
| `goal.yaml`: `execution_v2.tif` (1) | Beyaz-liste tek-uçlu; alan ne yazarsa yazsın `gtc` koşuyor. Ya alan kalkar ya beyaz-liste genişler — ikisinin arası yalan |
| `guard.SECTOR_CAP_DEFAULT_PCT`, `HEAT_CAP_DEFAULT_PCT` (2) | Üretimde sıfır okuyucu; `_y3_portfolio_caps` sabit `0`a düşüyor. Sabitler "açılırsa şu değerden açılır" diyor ama kod o yolu yazmamış |
| Registry: 12 sıfır-okuyuculu alan | YASA 6 (okuyucusuz yazım yok) doğrudan bunu yasaklıyor |
| `/opt/meridian/.env` içindeki `MERIDIAN_DASH_TOKEN` (dağıtım) | `barsarchive` o anahtarı okumuyor; sırrın gereksiz ikinci kopyası |

**KALDIRMA DEĞİL, TAMAMLAMA gereken sınır vaka:** `CREDENTIALS_DIRECTORY` — kod okuyor,
drop-in'ler repo'da yazılmış ama **A1'e kurulmamış**. Bu ölü kod değil, **yarım dağıtım**;
drop-in kurulursa bayrak canlanır ve token process env'den çıkar.

### D-2. DAMGALA (kalsın ama "ölü/atıl" diye AÇIKÇA işaretlensin — kodda ve PANODA) — 6 sınıf

| kalem | damga metni |
|---|---|
| `goal.yaml`: `one_variable_only` | "YASA BEYANI — düğme DEĞİL. Değeri hiçbir kod okumaz; kural koşulsuz uygulanır." (goal.yaml'da zaten yazılı; **panoda yok**) |
| `limits.max_position_r`, `max_daily_loss_pct` | "ÖLÇÜLEN DEFTERDE 0/409 KEZ BAĞLADI — zarf var, bağlayan değil." Fail-safe oldukları için kalmalı (§e) ama panoda "aktif kısıt" gibi görünmemeli |
| `limits.max_open_positions` | "FİİLEN SEKTÖR-ÇEŞİTLENDİRME DÜĞMESİ (EDG-035): eşzamanlı tepe 13<20; slot25 bayt-özdeş. Bağlayan `heat_hard_r`." |
| `execution_v2.limit_atr_mult` | "ATIL — `min()` her zaman `limit_pct_cap`ı seçer (100·ATR ≫ %4·tetik)." |
| `execution_v2.gap_behavior` | "KOŞULU TOTOLOJİ — `gap_at_submit` 4/4 true. Bu bir filtre değil, giriş motoru anahtarı." |
| Skill registry `enabled`/`mode`/`shadow` (93 bayrak) | **En acil damga.** Pano rozeti (`web/app.js:8416`) bugün "shadow" yazıyor ve skill silahlı koşuyor. Rozet "LLM-YÜZEYİ: bu bayrak trading davranışını DEĞİŞTİRMEZ" demeli; motor-içi skiller ayrı bir renkte gösterilmeli |

### D-3. DİRİLT (aslında bağlanmalıydı — iş kalemi) — 4 kalem

| kalem | neden diriltilmeli | iş |
|---|---|---|
| **`limits.no_trade_before_bars`** | **En yüksek öncelik.** Replay'de uygulanan (`backtest.py:151`) ama canlıda uygulanmayan bir kural, tam olarak "backtest sayıları yalan olur" ayrışmasıdır — bu deponun §4 motor-eşitliği yasasının ihlali | Ya `loop.py`ye kablo, ya `backtest.py`den kaldır + `limits`ten düşür. **Aradaki hâl en kötüsü** |
| `params_by_regime` (4 boş harita) | Rejim-koşullu ayar makinesi tam kablolu (`resolve_params`, `@regime` önerileri, guard doğrulaması) ve **hiç kullanılmıyor**. `exit.trail_atr_mult@chop` önerisi 2026-08-12'de min_sample-altı diye reddedildi — mekanizma canlı, yakıt yok | Ya rejim-örneklem birikimi bir iş kalemi olur, ya haritalar kaldırılıp `resolve_params` sadeleşir |
| `pessimistic_band_v2.ampirik_*` | E2 defteri 10 satır; kalibratör yazılı ve bekliyor. Bu **doğru şekilde boş** ama akışı besleyen bir kalem yok | E2 satır debisini artıran bir kalem (dolum sayısı) |
| Skill `shadow` bayrağı ↔ `ARMED_SETUPS` | Bayrağın anlamlı olabilmesi için `scan_entry`in registry'yi okuması gerekir. Bugün iki ayrı gerçek var: registry "gölge" diyor, motor silahlı koşuyor | Ya bayrak `ARMED_SETUPS`a bağlanır, ya bayrak D-2'deki gibi damgalanır. **İkisinden biri şart** |

---

## (e) YANLIŞ-POZİTİF LİSTESİ — "şimdilik etkisiz" ama ÖLÜ DEĞİL, kaldırılmamalı

1. **Fail-safe varsayılan çiftleri** — `broker.DERISK_FULL_DD/FLOOR_DD`, `ENTRY_LIMIT_ATR_MULT/PCT_CAP`,
   `guard.HEAT_HARD_R/HEAT_REVIEW_R/CORR_REVIEW`. Hepsi goal.yaml'daki kanonik değerle **aynı**
   olduğu için asla görünmezler. Bu bir kopya değil, **yapılandırma okunamazsa yasa yok olmasın**
   sigortasıdır (`broker.py:237-240`in kendi gerekçesi: "yarısı dosyadan yarısı koddan bir rampa,
   hiç olmayan rampadan tehlikelidir").

2. **Kill-switch / acil vana ortam bayrakları (8)** — `MERIDIAN_DB`, `DD_MTM_VETO`,
   `WS_DISCONNECT_CANCEL_ENTRIES` (RUNBOOK.md:575'te belgeli), `FORCE_RESEED`, `FORCE_BASELINE`,
   `FINVIZ_PUBLIC`, `CORS_ORIGINS`, `STREAM_MAX_SYMBOLS`. Bugün atıl olmaları **tasarım**: bir
   acil durumda çekilecek kol, normalde çekili olmaz.

3. **`guard.LIVE_DEAD_KNOBS = {}`** — bilinçli boş ikinci savunma hattı. Birinci hat motor-eşitliği
   çivisidir; o kırmızı yandığında bu sözlük dolar. Boş olması sağlığın kanıtıdır.

4. **`config.LIVE_EXPECTANCY_CAP_MULT` / `LIVE_SUSPEND_RATIO`** — hüküm verdirmeyen, yalnız
   ölçen kural (`analytics.live_expectancy_ceiling`in `hukme_girmez`i). Bilerek hükümsüz.

5. **`analytics.EDGE_*` / `RESULT_*` / `PRED_*` / `REGIME_*` (12)** — karar yolunda değiller ama
   **kanıt eşikleridir**: Faz-6 silahlanmanın ön koşulu. Kaldırılırsa silahlanma kapısı ölçüsüz
   kalır. Bunlar "gelecek faz kancası", ölü değil.

6. **`health.faz6_kilitleri` zinciri** — saf okuma, hiçbir şey silahlamaz. Bu **kasten** böyle:
   kilidin kapalı olması ile ölçümün olmaması arasındaki farkı koruyor (`durum: olculdu` vs
   `olculemedi`).

7. **`bounds.yaml`da varsayılan-kapalı satırlar (Batch L / G2 / G3b / turnover)** — canlı etkileri
   0 ama **arama uzayında olmaları gerekiyor**; kapalı doğmaları anti-overfit disiplinidir.
   *(Şerh: `regime.vix_backwardation_gate` bu sınıfa girmiyor — o, veri kaynağı doğrulanmış
   şekilde YOK olduğu için yapısal hükümsüzdür ve `spy_sma_gate` mezar taşının kendi gerekçesine
   göre — "etkisiz bir eksen tutmak kapsamayı değil bütçeyi büyütür" — düşürülmelidir.)*

8. **`shadowlaw.MEASURED_V2` / `V2_WEIGHT_TRIALS` / `WHY_40_UNREACHABLE`** — çürütülmüş bir
   yasanın kaydı. Panoda "neden v2 tutmadı" sorusunun tek dokümante cevabı; silinirse aynı
   deneme tekrar yapılır.

---

## EK — kapsam dışı ama triyaja gitmesi gereken canlı bulgu

Denetim sırasında canlı olay defterinde görüldü, **bu denetimin konusu değil**, Rol-1'in
triyaj kalemidir:

- `MIRROR_DRIFT KORUMASIZ POZİSYON` — AMGN/BKNG/EMR/NUE dördü de açık ve **broker'da canlı
  koruyucu stop YOK** (son 7 günde her biri 6 kez, `korumasiz_motor_disi_pozisyon` 26 kez).
- `finviz_unavailable` 1516 · `candidate_review_backlog` 1397 · `sprint_cadence_skip` 1885
  (son 7 gün).
- `DATA_QUALITY EVREN DENETİMİ ÖLÇÜLEMEDİ: ImportError: lxml` — evren denetimi ölçülemiyor.

---

## ÖLÇÜM KÜNYESİ

| ne | kaynak |
|---|---|
| Hipotez defteri (52 kayıt, 0 ship) | canlı `/opt/meridian/state/hypotheses.jsonl` |
| Kapı düşme oranları (409 plan × 16 kontrol) | canlı `state/meridian.db → trade_plans.gate_checks` |
| Olay histogramı (50.877 olay, 316 ayrık ad, 2026-07-14→08-13) | canlı `state/events.jsonl` |
| E2 icra defteri (10 satır) | canlı `state/entry_execution.jsonl` |
| Strateji sürüm tarihçesi (v0001–v0005) | canlı `state/history/v000*.yaml` |
| Kapı meta-kalibrasyonu / LLM kalibrasyonu / sieve | canlı `state/gate_calibration.json`, `llm_calibration.json`, `sieve.json` |
| Slot/ısı/zarf bağlayıcılığı | `research/cards/EDG-2026-035-yerel-duyarlilik.yaml` (verdict.yapisal_bulgu) |
| ADV/impact etkisi | `docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md:225-228` |
| Skill çağrı izi | `docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md` + `state/skills_registry.json`, `skill_auto_shadow.json` |
| Modül sabiti taraması (172 sabit, 8 modül) | repo `meridian/*.py`, otomatik okuyucu-sayımı |
| Ortam bayrağı envanteri (75) | repo `meridian/`, `deploy/oracle-a1/meridian.service`, canlı `/proc/<uvicorn>/environ` |

**ÖLÇÜLEMEDİ beyanı:** (1) yeni zarf (slot20+0,5R, 2026-08-12) altındaki kapı düşme oranları —
plan defteri 2026-08-07'de bitiyor, o pencerede yeni-zarf planı yok. (2) 4 ortam bayrağının
her döngüde ateşlediği — statik çağrı zinciri izlendi, çalışma-zamanı frekansı kanıtlanmadı.
(3) `pullback-screener` gölgelendikten sonraki aday satırları — `candidates.jsonl` 2026-07-28'de
bitiyor, gölge 07-29'da uygulandı.
