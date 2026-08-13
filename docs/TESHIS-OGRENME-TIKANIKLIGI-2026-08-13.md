# TEŞHİS — ÖĞRENME TIKANIKLIĞI (52 hipotez / 0 ship)

**Tarih:** 2026-08-13 · **Rol:** teşhis ajanı (kod yazılmadı, git kullanılmadı, canlıya yalnız SALT-OKUMA)
**Kaynak:** canlı A1 (`/opt/meridian`) — `state/hypotheses.jsonl` (52 satır, mtime 2026-08-12 11:10),
`state/events.jsonl` (50.939 satır), `state/inc_cache.json` (mtime 2026-08-13T07:09Z),
`state/meridian.db` (salt-okunur URI), `meridian/probgate.py`, `meridian/reflect.py`, `meridian/hermes.py`,
`state/bounds.yaml`, `state/goal.yaml`, `state/strategy.yaml`.
**Girdi belgesi:** `docs/DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13.md`.
**Kapsam dışı (bilinçli):** öneri yok — bu belge yalnız ölçer. Hüküm ve eylem Rol-1'in.

---

## 0. YÖNETİCİ ÖZETİ — CEVAP: **KARIŞIM, AMA EŞİT AĞIRLIKLI DEĞİL**

Merkez soru "(H1) kapı haklı mı, (H2) döngü tıkalı mı" idi. Ölçüm ikisini de kısmen doğruluyor,
ama **payları çok farklı ve ikisi farklı ZAMAN DİLİMLERİNDE hâkim.** Tek cümlelik hüküm:

> **Temmuz'da H1 hâkimdi (kapı çalıştı, adaylar gerçekten değersizdi). Ağustos'ta H2 hâkim oldu —
> ve tıkanıklık kapının SIKILIĞINDA değil, kapının ÖNÜNDE: hipotezler defterin dışında,
> ölçülmeden ölüyor.** 2026-08-02'den bu yana üretilen **47 öneri deftere hiç girmedi** ve
> Ağustos'un **500 arama sondasının 500'ü ölçülemedi** (`candidate_oos = NULL`, sıfır istisna).

### Kanıt-1 — 52 ret aslında 52 "ret" değil (`hypotheses.jsonl` tam sayım)

| sınıf | n | ne demek |
|---|---:|---|
| **TEKRAR** (`rejected_by_guard`) | **22** | Aynı (değişken, değer) çiftinin tekrarı. Yeni bilgi taşımaz; hafıza notu ("already tried") kesti. Hepsi **tek gün**: 2026-07-14. |
| **NO-OP** (ölçüldü ama Δ tam 0) | **4** | Aday, incumbent'la **bit-bit aynı** sonuç üretti (`mean_delta = 0.0`, `incumbent_oos == candidate_oos`). Bir değer yargısı DEĞİL. |
| **ÖLÇÜLEMEDİ** (OOS tanımsız) | **1** | `min_sample` altı — skor `None`. H00052 (2026-08-12, son satır). |
| **SHIP** (`superseded`) | **2** | v0002 (`pivot_proximity_pct`) ve v0003 (`w_prox` — kodun varsayılanının aynısı, no-op ship). |
| **GERÇEKTEN ÖLÇÜLDÜ ve REDDEDİLDİ** | **23** | Kapının hakkıyla hüküm verdiği tek küme. |

Yani "52 hipotez, 52 ret" cümlesi **23 gerçek ret** üstüne kuruludur; kalan 29 satır ya tekrar,
ya no-op, ya ölçülemeyen, ya da ship'tir.

### Kanıt-2 — 23 gerçek ölçümün 13'ü CANLIYA ZARAR VERİRDİ (H1 lehine, güçlü)

`search_mean_delta` (2000 blok-bootstrap replikasyonunun ortalama ΔS'i, PARA-v3 ölçeği):

- **negatif ortalama Δ: 13/23** — aday, incumbent'tan **daha kötü** ölçüldü. Uçlar: `entry.w_vol`
  −0,2019 · `entry.min_rvol` −0,1721 · `exit.time_stop_days` −0,1532 · `exit.giveback_pct` −0,1210.
- **pozitif ortalama Δ: 6/23** (H00032, H00033, H00036, H00038, H00039, H00048).
- **legacy yasa (probgate öncesi), p yok: 4/23** (H00001, H00002, H00008, H00027).

`P(ΔS>0)` bir p-değeri DEĞİL, bootstrap kazanma oranıdır: 0,50 = yazı-tura. **20 P-kapısı retinin
14'ü P < 0,50** — yani "iyi hipotez kapıda takıldı" değil, "**aday muhtemelen zararlıydı**".
Bu, H1'in en güçlü kanıtıdır ve tartışmasızdır.

### Kanıt-3 — ama kapının kendisi de üç yerde YANLIŞ CÜMLE kuruyor (H2 lehine)

1. **`P = 0,000` iki ayrı gerçeği aynı sayıyla söylüyor.** `probgate.evaluate` satırı
   `p = float(np.mean(arr > 0))` — **kesin eşitsizlik**. Aday incumbent'la aynıysa ΔS her
   replikasyonda tam 0 olur, `arr > 0` hep False, **p = 0,000**. Defterde `P=0,000` yazan 5 satırın
   **4'ü no-op** (H00046/49/50/51, `mean_delta = 0.0`), yalnız 1'i gerçek felaket
   (H00031, `mean_delta = −0,0921`). Defter ikisini ayırt edilemez yazıyor.
2. **Bu no-op'lar YAPISAL OLARAK ATIL düğmelerden geliyor** — `bounds.yaml`ın kendi mezar taşının
   ("etkisiz bir eksen tutmak kapsamayı değil yalnız bütçeyi büyütür", `regime.spy_sma_gate`,
   8b6bbbc) anlattığı zarar, bugün üç satırda tekrarlıyor:
   - `exit.early_kill_bars` → `bounds.yaml`ın kendi notu: "`early_kill_pivot=0` iken **ATIL**".
     `strategy.yaml` `early_kill_pivot` taşımıyor → varsayılan 0 → düğme atıl. (H00049)
   - `exit.scale_out_r` → `strategy.yaml`: `exit.scale_out_frac: 0.0` → scale-out KAPALI → atıl. (H00051)
   - `exit.early_kill_pivot` **None→0** → zaten 0 olan bir düğmeyi 0 yapma önerisi. (H00050)
   - `entry.w_tight` **None→0.3** → `strategy.py:418` `_f(params,"entry.w_tight", **0.30**)` —
     **kodun varsayılanının aynısı**. v0003'ün `w_prox` no-op ship'iyle **birebir aynı sınıf**;
     fark, o ship edilmişti, bu reddedildi.
3. **`regime.vix_backwardation_gate` bugün hâlâ örnekleniyor** — `bounds.yaml` onun için
   "`veri_yok` → **atıl**: knob 1 yapılsa bile karar üretmez" diyor. Buna rağmen arka-plan
   turlarında **8 kez** önerildi (aşağıda üretici karnesi).

### Kanıt-4 — ASIL TIKANIKLIK: defter-ÖNCESİ, görünmez bir süzgeç (H2, belirleyici)

`events.jsonl` tam taraması: **`hermes_bg_proposal_rejected` = 47**, ilk ateşleme
**2026-08-02T14:00**, son ateşleme **2026-08-13T17:26 (bugün, hâlâ akıyor)**. 47'sinin de nedeni
**tek ve aynı**, `bg_regime: chop`:

> "arka plan turunda GLOBAL ya da farklı-rejim öneri reddedildi — canlı olmayan rejimin kanıtı
> yalnız o rejimin `params_by_regime`ine girebilir"

Kod (`hermes.py:3889`):
`if background and (preg is None or (certified is not None and preg != certified)): reddet`
— yani **arka plan turu `chop` için sertifikalıysa, GLOBAL (`@`siz) her öneri atılır.**
Atılan 47 önerinin değişken dağılımı: `entry.w_turnover` ×21 · `exit.trail_atr_mult` ×16 ·
`regime.vix_backwardation_gate` ×8 · `exit.breakeven_r` ×1 · `exit.time_stop_days@trend_up` ×1.

**Aynı pencerede (2026-08-02 → 2026-08-13) deftere giren hipotez sayısı: 1** (H00052).
Yani 47 fikir üretildi, 1'i deftere ulaştı, o da ölçülemedi. **Defterdeki "52" sayısı hipotez
üretiminin değil, görünmez bir ön-elemenin hayatta kalanlarıdır.**

### Kanıt-5 — Ağustos'ta ÖLÇÜM TAMAMEN DURDU (H2, belirleyici)

`hermes_search_probe` olaylarının aylık sonuç dağılımı (tam `events.jsonl` taraması):

| ay | sonda | ölçüldü-geçmedi | **`candidate_oos = NULL`** | değişken NULL | **geçen** |
|---|---:|---:|---:|---:|---:|
| 2026-07 | 477 | 382 | 48 | 43 | **4** |
| 2026-08 | 500 | **0** | **450** | 50 | **0** |

Temmuz'da sondaların %80'i ölçülüyordu; **Ağustos'ta ölçülen sonda sayısı SIFIR.** Neden
`inc_cache.json`da açıkça yazıyor — Ağustos sondaları ezici çoğunlukla `@chop` hedefli
(`entry.w_prox@chop` 73 · `exit.breakeven_r@chop` 58 · `exit.trail_atr_mult@chop` 40 …) ve:

```
eval_regime='chop'  →  oos_detail: {"score": null, "n": 27, "min_sample": 30,
                        "reason": "27/30 closed trades — score undefined (None, not 0.0)"}
                        oos_folds n = [8, 18, 0]     _trades_confirm = 0
eval_regime=None    →  oos_score = 0.2354,  n = 560, _trades_search = 347
```

**`chop` diliminde 27 işlem var, eşik 30. Üçüncü fold'da SIFIR işlem, teyit diliminde SIFIR işlem.**
Canlı rejim `chop` → arka plan turları `chop` sertifikalı → üretici her şeyi `@chop`a hedefliyor →
`chop` dilimi eşiğin altında → **ölçüm imkânsız.** Kapı burada bir yargı vermiyor; **ölçemiyor.**

### Hüküm — payların ölçülmüş dağılımı

| iddia | kanıt | ağırlık |
|---|---|---|
| **H1 doğru** — adaylar gerçekten değersizdi | 23 gerçek ölçümün 13'ü negatif ort.Δ; 20 P-retinin 14'ü P<0,50; teyit yürüyüşü H00032'de kazananın-lanetini tam olarak yakaladı (arama +0,128 → teyit −0,080) | **Temmuz'un tamamı; bugün de geçerli** |
| **H2 doğru** — döngü tıkalı | 47 öneri defter-öncesi imha (2026-08-02→bugün, hâlâ akıyor); Ağustos'ta 500/500 sonda ölçülemedi; 4 no-op yapısal-atıl düğmeden; 22 tekrar üreticinin aynı yere çarpmasından | **2026-08-02'den bugüne, tam hâkim** |
| **Kapı fazla SIKI mı?** | Duyarlılık ölçümü (§4): eşik 0,80→0,70 olsaydı **tüm veto zinciri sonrası 1 ship** olurdu; 0,60'ta 2. Yani sıkılık **tek başına** 0 ship'i açıklamıyor — ama sıfırdan farklı da değil | **kısmen** |

**Kritik ayrım:** "0 ship" bugün kapının sıkılığından DEĞİL, kapıya aday ULAŞMAMASINDAN doğuyor.
Eşiği düşürmek Ağustos'ta hiçbir şeyi değiştirmezdi — çünkü Ağustos'ta ölçülmüş **hiçbir aday yok.**

---
## 1. RET ANATOMİSİ — 52 SATIRIN TAM DÖKÜMÜ (özet tablo §8'de)

Aşama dağılımı: `rejected_by_backtest` **27** · `rejected_by_guard` **22** · `superseded` **2** · `rejected_by_confirmation` **1**. Tam satır-satır tablo §8'dedir; bu bölüm desenleri, §8 ham veriyi taşır.

## 2. TEKRAR DESENİ — üreticinin aynı yere çarpması

**Ölçüm:** `(değişken, yeni değer)` çifti tekrar sayımı, `hypotheses.jsonl` tam sayım.

| çift | kez | dağılım |
|---|---:|---|
| `stop_loss_atr_mult = 2.1` | **21** | 1 backtest reti (H00001) + **20 guard reti** |
| `entry.rs_rating_min = 71` | **3** | 1 backtest reti (H00008) + 2 guard reti |
| diğer tüm çiftler | 1'er | — |

**Zaman:** 22 guard retinin **22'si de 2026-07-14** — tek gün, 11:15 ile 18:19 arası. 2026-07-14
18:44'ten (H00026) sonra **bir tane bile guard reti yok.** Yani bu bir "bugün akan" arıza değil,
**intake gününde kalmış bir yara izi**.

### Kök neden — brief'in sorduğu ikilemin cevabı

Brief iki şık sormuştu: (a) üretici aynı yere tekrar tekrar çarpıyor, (b) arama uzayı o değeri
defalarca örneklüyor. **Cevap kesin olarak (a) ve kod satırı belli:**

`reflect.propose_deterministic` (canlı `meridian/reflect.py:771`) iki moda sahiptir:

```python
if explore:
    for var in _ucb_rank(list(bounds.keys()), hyps):
        ...
        if guard._equalish(...) or already_failed(var + suffix, new):   # ← ATLAMA VAR
            continue
    ...
else:
    var = hvar          # ← exploit yolu
new = move(var, hdir)   # cur + 1 × step
return _proposal(var, new, params, hwhy, explore=False)
```

**`already_failed` kontrolü YALNIZCA `explore` dalının içindedir.** Varsayılan (exploit) yolda
hafıza kontrolü **hiç yoktur**. Exploit sezgiseli şudur:

```python
if reasons.get("stop",0) + reasons.get("stop_gap",0) > 0.4 * n:
    hvar, hdir = "stop_loss_atr_mult", +1   # "stop-outs dominate — give trades more room"
```

`move()` tek adım atar: `2.0 + 1 × 0.1 = 2.1`. Son 40 işlemde stop payı %40'ın üstünde kaldığı
sürece **aynı öneri sonsuza dek yeniden üretilir**. Döngüyü kıran şey üretici değil,
**`guard`ın "already tried and failed" hafızasıdır** — yani sistem kendini bir kapıyla kurtardı,
öğrenerek değil.

**Arama uzayı bu tekrarın nedeni DEĞİL:** `bounds.yaml` `stop_loss_atr_mult: {min:0.8, max:4.0,
step:0.1}` — 33 adım-üstü değer mevcut. Üretici bunların 32'sine hiç bakmadı; hatta ters yön
(1.9) bile denenmedi, çünkü `hdir` sezgiselce `+1`e sabitlenmiş.

**`explore_rate` KARŞILAŞTIRMASI YAPILAMAZ — ÖLÇÜLEMEDİ + NEDEN:** `goal.yaml`'da
`explore_rate: 0.15` yazılıdır, ama **hiçbir kod onu okumaz.** Tek eşleşmesi `guard.py:17`
`GOAL_KEYS` üyelik setidir (drift koruması; değeri değerlendirmez) ve `goal.yaml`ın kendi satır-içi
notu bunu zaten beyan ediyor: "BİLGİLENDİRİCİ — HİÇBİR KOD OKUMAZ (K1 denetimi, 2026-07-30)".
Yani "adım büyüklüğü + explore_rate ile kıyasla" isteminin `explore_rate` ayağının davranışsal
karşılığı yoktur; keşif payı fiilen `hermes.exploration_share()` ve UCB sıralamasından gelir.

---

## 3. KAPI SIKILIĞI — `probgate.P_BASE = 0,80` NE ÖLÇÜYOR

**Mekanizma (`meridian/probgate.py`, canlı):**

- `PairedProbabilisticGate.evaluate` incumbent ve adayı **AYNI yeniden-örneklenmiş takvim
  bloklarında** skorlar (blok-bootstrap, `N_BOOT_DEFAULT = 2000`, `SEED_DEFAULT = 42`).
- Blok boyu dinamik: birleşik kümenin **medyan tutuş süresi**, `[5, 21]` güne kıstırılır.
  Defterde gözlenen: 8–20 gün.
- `ΔS` = `shadowlaw.ret_c_v3` farkı — **PARA-v3 yasası: yalnız para terimi**. Düşüş ve Sharpe
  skordan ÇIKARILDI (çift-sayım kapatıldı), ayrı vetolarda duruyor.
- **`p = np.mean(ΔS > 0)`** — 2000 replikasyonun kaçında adayın kazandığı. **p-değeri DEĞİL**,
  kazanma oranıdır. Yorumu: `0,50` = yazı-tura · `0,80` = "20 turdan 16'sında aday önde".
- **Eşik K ile sıkışır (gerçek Bonferroni):** `p_req = 1 − (α_family − meta_ofset) / K`,
  `α_family = 1 − P_BASE = 0,20`. `K=1 → 0,80` · `K=10 → 0,98` · tavan `P_CEIL = 0,999`.
- **Meta-kalibrasyon ATIL:** canlı `gate_calibration.json` → `n_measured: 1`, `durum: "kurak"`,
  `extra_p: 0,0`. `META_MIN_N = 5` hiç karşılanmadı → eşik hiç oynamadı. Mekanizma canlı, kanıt yok.
- `P_CONFIRM = 0,70` teyit dilimi için.

### 20 P-kapısı retinin eşiğe uzaklığı (tam sayım)

| P(ΔS>0) | id | değişken | ort.Δ | eşiğe uzaklık |
|---|---|---|---|---|
| **0,799** | H00033 | `entry.w_rs` | +0,0643 | **−0,001 (kıl payı)** |
| **0,709** | H00039 | `entry.rs_rating_min@trend_up` | +0,0837 | −0,091 |
| 0,614 | H00048 | `exit.chandelier_lookback` | +0,0457 | −0,186 |
| 0,587 | H00038 | `exit.profit_target_r` | +0,0226 | −0,213 |
| 0,566 | H00036 | `exit.profit_target_r` | +0,0210 | −0,234 |
| 0,512 | H00030 | `regime.min_exposure_score` | −0,0026 | −0,288 |
| 0,428 | H00045 | `entry.w_rvolband` | −0,0152 | −0,372 |
| 0,364 | H00028 | `exit.scale_out_frac` | −0,0043 | −0,436 |
| 0,255 | H00035 | `entry.max_ext_atr` | −0,1185 | −0,545 |
| 0,229 | H00042 | `entry.min_rvol` | −0,1721 | −0,571 |
| 0,218 | H00037 | `exit.giveback_pct` | −0,1210 | −0,582 |
| 0,202 | H00040 | `exit.time_stop_days` | −0,1532 | −0,598 |
| 0,178 | H00044 | `entry.w_mom` | −0,1341 | −0,622 |
| 0,140 | H00032 | `exit.breakeven_r` *(teyit dilimi, gerekli 0,70)* | −0,0796 | −0,560 |
| 0,122 | H00034 | `entry.w_rs` | −0,0663 | −0,678 |
| 0,030 | H00047 | `entry.w_vol` | −0,2019 | −0,770 |
| 0,000 | H00031 | `entry.rs_rating_min` | −0,0921 | −0,800 *(gerçek ret)* |
| 0,000 | H00046 | `entry.w_tight` | **0,0** | **NO-OP — ret değil** |
| 0,000 | H00049 | `exit.early_kill_bars` | **0,0** | **NO-OP — ret değil** |
| 0,000 | H00050 | `exit.early_kill_pivot` | **0,0** | **NO-OP — ret değil** |
| 0,000 | H00051 | `exit.scale_out_r` | **0,0** | **NO-OP — ret değil** |

**Dağılım hükmü:** eşiğe kıl payı yaklaşan **tek** aday var (H00033, 0,799). İkinci en yakın 0,091
uzakta. Kalan 18'in 14'ü P < 0,50 — yani "iyi hipotez eşikte takıldı" tablosu **yok**;
tablo "çoğu aday zaten kaybediyordu" diyor.

---

## 4. EŞİK DUYARLILIĞI — 0,80 / 0,70 / 0,60'ta KAÇ TANESİ GEÇERDİ

> **BU BİR ÖNERİ DEĞİL, DUYARLILIK ÖLÇÜMÜDÜR.** Eşik değiştirme yetkisi bu turda yoktur ve
> bu belgede eşik değişikliği önerilmemektedir.

Ölçüm iki sütunda verilir, çünkü **P kapısı ship yolunun tek ayağı değil**: `reflect._gate_eval`
hükmü `passes = magnitude_ok AND majority AND tail_ok AND dd_ok AND dd_mtm_ok`. Yalnız P'ye bakmak
sistematik olarak fazla iyimser sayı üretir.

| `P_BASE` | P kapısını geçen | **tüm veto zinciri sonrası SHIP** | ship edecek adaylar |
|---|---:|---:|---|
| **0,80 (yürürlükte)** | 0 | **0** | — |
| 0,75 | 1 | **0** | H00033 P'yi geçer, **fold-çoğunluğunda düşer (1/3)** |
| **0,70** | 2 | **1** | `entry.rs_rating_min@trend_up` 70→65 (H00039) |
| 0,65 | 2 | **1** | aynı |
| **0,60** | 3 | **2** | + `exit.chandelier_lookback` 0→15 (H00048) |
| 0,55 | 5 | **3** | + `exit.profit_target_r` 2,5→3,0 (H00036) |
| 0,50 | 6 | **4** | + `regime.min_exposure_score` 20→40 (H00030, **ort.Δ −0,0026 — negatif**) |

**Okunuş:** eşiği 0,80'den 0,70'e indirmek geçmişte **1 ship** üretirdi, 0,60'a indirmek **2**.
0,50'ye inildiğinde ortalama Δ'sı **negatif** olan bir aday da geçmeye başlar — yani yazı-tura
sınırında kapı bilgi taşımayı bırakır. Ayrıca H00033 örneği önemlidir: **P'yi geçmek ship etmeye
yetmiyor**; fold-çoğunluğu vetosu bağımsız olarak bağlıyor.

**Bu ölçümün kapsamı (dürüstlük şartı):** sayılar **geçmiş 23 ölçümün donmuş kayıtları** üzerinden
hesaplandı. Bugünkü örneklem tabanı farklıdır (§6) ve **aynı adaylar bugün yeniden koşulsa
P değerleri değişir** — bu tablo "eşik şu olsaydı geçmişte ne olurdu" sorusunun cevabıdır,
"bugün ne olur"un değil.

---

## 4b. BAŞARI ÖRNEĞİ LİSTESİ — "OOS'u pozitifti ama başka bir ayakta düştü"

Brief'in en ayırt edici sorusu: 52'nin içinde **OOS'u pozitif olup başka bir ayakta düşen** var mı?
Varsa H2 ("kapı çok sıkı") lehine en güçlü kanıt olurdu. **Cevap: VAR, ama sadece iki tanesi
gerçek anlamda güçlü — ve ikisi de aynı ayakta düştü (P kapısı).**

### A. GÜÇLÜ ADAYLAR — her ayakta temiz, yalnız P kapısında düştüler

| id | değişken | değer | ort.Δ | OOS inc→cand | fold | tail | dd | düştüğü TEK ayak |
|---|---|---|---|---|---|---|---|---|
| **H00039** | `entry.rs_rating_min@trend_up` | 70→65 | **+0,0837** | 0,1327 → **0,2096** (+%58) | **3/3** | ✔ | — | `P=0,709 < 0,80` |
| **H00048** | `exit.chandelier_lookback` | 0→15 | **+0,0457** | 0,0845 → **0,0951** | **2/3** | ✔ | ✔ | `P=0,614 < 0,80` |

**H00039 bu defterin en iyi adayıdır:** üç fold'un **üçünde de** kazandı (`fold_wins: "3/3"`),
kuyruk vetosunu geçti (`tail_ok: true`), ortalama Δ'sı pozitif, nokta OOS'u %58 arttı, `k_probes=1`
olduğu için ek Bonferroni cezası da yemedi (`p_required` düz 0,80). Tek eksiği bootstrap kazanma
oranının 0,709 olmasıydı. **Bu tek satır, "kapı çok sıkı" iddiasının en somut kanıtıdır.**
(`dd_ok` bu kayıtta **yok** — düşüş vetosu H00042'den itibaren yazılmaya başladı, yani H00039
düşüş ayağından hiç geçmedi: ölçülmedi, geçti değil.)

### B. KARIŞIK ADAYLAR — bir ayakta iyi, başkasında zayıf

| id | değişken | ort.Δ | OOS inc→cand | fold | neden "başarı" sayılmaz |
|---|---|---|---|---|---|
| H00033 | `entry.w_rs` None→0,4 | +0,0643 | 0,1509 → 0,2186 | **1/3** | P'ye kıl payı yaklaştı (0,799) ama **fold-çoğunluğu 1/3** — üç pencereden ikisinde kaybetti. Eşik düşürülse bile ship etmezdi. |
| H00036 | `exit.profit_target_r` 2,5→3,0 | +0,0210 | 0,1284 → 0,1630 | 2/3 | Ort.Δ pozitif ama küçük; P=0,566 yazı-turaya yakın. |
| H00038 | `exit.profit_target_r` 2,5→2,0 | +0,0226 | 0,1309 → **0,1179** | 1/3 | Bootstrap ortalaması pozitif, **nokta OOS'u NEGATİF** — iki ölçüt ters yönde. |
| H00030 | `regime.min_exposure_score` 20→40 | −0,0026 | 0,2043 → 0,1951 | 2/3 | Fold çoğunluğunu aldı ama hem ort.Δ hem nokta OOS negatif. |

### C. KAPININ KENDİNİ HAKLI ÇIKARDIĞI VAKA (H1 lehine, önemli)

| id | değişken | arama dilimi | teyit dilimi | sonuç |
|---|---|---|---|---|
| **H00032** | `exit.breakeven_r` 1,0→0,0 | `P=0,909` (gerekli 0,89) **GEÇTİ**, ort.Δ **+0,1281** | `P=0,140` (gerekli 0,70) **DÜŞTÜ**, ort.Δ **−0,0796** | `rejected_by_confirmation` |

Arama diliminde +0,128'lik güçlü bir iyileşme gösteren aday, teyit diliminde **işareti tersine
döndü**. Bu tam olarak `probgate` modül beyanının kurumsallaştırmak için yazıldığı vakadır
("v2 dersi: arama +0,059 gösterip canlı −0,036 gerçekleşmişti"). **Kazananın-laneti bastırması
ölçülebilir biçimde çalıştı.** Eşik gevşetilseydi bu aday canlıya çıkardı ve zarar ederdi.

### D. TERS VAKA — ship kapısının açık kaldığı tek yer

| id | değişken | arama | teyit | sonuç |
|---|---|---|---|---|
| H00029 | `entry.w_prox` None→0,15 | `P=0,941` (gerekli 0,89) geçti, ort.Δ **+0,0016** | `confirm_p = null`, **`confirm_n_valid = 0`** | **SHIP (v0003)** |

`incumbent_oos` ve `candidate_oos` **ikisi de `None`**, teyit diliminde **sıfır geçerli
replikasyon** vardı — ve aday yine de ship edildi. Değeri (0,15) `strategy.py:419`'un varsayılanının
aynısıdır, yani davranış bit-bit değişmedi. **Döngünün "iki ship"inden biri, ölçülemeyen bir
no-op'tur.** (Diğeri H00026, `pivot_proximity_pct` 2,0→2,3 — döngünün tek gerçek ürünü.)

### Hüküm

**H2 lehine net kanıt: 1 satır (H00039), zayıf kanıt: 1 satır (H00048).**
**H1 lehine net kanıt: H00032'nin teyit dilimindeki işaret dönüşü + 13 negatif ort.Δ.**
Yani "iyi hipotezler kapıda boğuluyor" tablosu **var ama seyrek** — 23 gerçek ölçümde 1-2 vaka.
Bu, 0 ship'i tek başına açıklamaz; §0 Kanıt-4/5'teki defter-öncesi imha ve ölçüm kuraklığı açıklar.

---

## 5. ÜRETİCİ KARNESİ — kısır mı, bereketli mi?

**Hüküm: ÜRETİCİ BEREKETLİ; darboğaz üretimde değil, üretimle defter arasındaki iki süzgeçte.**

### 5.1 Üretim hatları (kim üretiyor)

| kaynak | deftere giren | not |
|---|---:|---|
| `deterministic` | 25 | `reflect.propose_deterministic` — exploit sezgiseli. **25'i de 2026-07-14.** Docstring'e göre canlı yolu YOK, tek çağıranı `reflect --auto` CLI'ı (operatör tetiği). |
| `deterministic:virgin` | 8 | `hermes.propose_virgin_knob` — bakir düğme keşfi (H00043–H00050). **3'ü no-op çıktı** (H00046/49/50) — yani bakir-düğme kolunun **%38'i ölçülemeyen bir hamleye gitti**. |
| `hermes:nous` | 7 | LLM bacağı. Son satır H00052 (2026-08-12) — ölçülemedi. |
| `hermes:gemini` | 7 | LLM bacağı. Dördüncü no-op buradan: H00051 `exit.scale_out_r` (scale-out `frac=0` iken atıl). |
| `coordinate_search` | 2 | 1 ship (v0003 no-op), 1 teyit reti |
| `cf_evidence` | 2 | karşı-olgusal kanıttan |
| `sprint_search` | 1 | 1 ship (v0002 — döngünün **tek gerçek ürünü**) |

### 5.2 Kadans ve debi (`events.jsonl` tam tarama, 2026-07-14 → 2026-08-13)

| olay | Temmuz | Ağustos | toplam | son ateşleme |
|---|---:|---:|---:|---|
| `bg_reflection_start` | 108 | 67 | **175** | 2026-08-13T17:25 |
| `hermes_search_start` | 115 | 55 | **170** | 2026-08-13T17:26 |
| `hermes_search_probe` | 477 | 500 | **977** | 2026-08-13T18:40 |
| `hermes_search_done` | 33 | 23 | **56** | 2026-08-13T04:08 |
| `hermes_virgin_proposal` | 1 | 37 | **38** | 2026-08-09T20:37 |
| **`hermes_bg_proposal_rejected`** | 0 | **47** | **47** | **2026-08-13T17:26** |
| `hermes_brain_unavailable` | 46 | 37 | **83** | 2026-08-09T20:37 |

`hermes_search_done` durum dağılımı: **`no_clearing_candidate` 50** · `shipped` 5 ·
`rejected_by_confirmation` 1. Toplam `evaluated` **768**, toplam `cleared` **6**.
Ağustos'un 23 turunun **23'ü de** `no_clearing_candidate`.

### 5.3 HUNİ — üretilen ile deftere gireni ayıran iki süzgeç

```
977 sonda değerlendirildi (768 "evaluated" beyanı)
   │
   ├─ SÜZGEÇ-1: ölçülebilirlik  →  Ağustos'ta 500/500 sonda `candidate_oos = NULL`
   │                                 (min_sample 30 > chop dilimi 27)
   │
   ├─ SÜZGEÇ-2: arka-plan rejim kapısı  →  47 öneri deftere HİÇ girmedi
   │                                          (hermes.py:3889, hepsi bg_regime=chop)
   │
   └─→ deftere giren: 52 satır (26'sı 2026-07-19 sonrası; 2026-08-02'den beri SADECE 1)
```

**Kısırlık testi:** üretici kısır değil — Ağustos'ta bile 500 sonda, 37 bakir-düğme önerisi,
67 arka-plan yansıması üretti. Ama **çeşitlilik zayıf**: 977 sondanın tepe değişkenleri
`entry.w_prox@chop` (73), `exit.breakeven_r@chop` (58), `entry.min_volume_ratio` (50),
`exit.breakeven_r` (41). Ve **8 sonda `regime.vix_backwardation_gate`e harcandı** — `bounds.yaml`ın
kendisi o düğme için "veri_yok → **atıl**, knob 1 yapılsa bile karar üretmez" diyor.

### 5.4 Beyin erişilebilirliği

`hermes_brain_unavailable` **83** kez, `hermes_brain_cooldown` **63** kez ateşledi;
**ikisi de 2026-08-09T20:37'de sustu** ve o tarihten beri hiç ateşlemedi. Aynı tarih
`hermes_virgin_proposal`ın da son ateşlemesi. **2026-08-09'dan sonra LLM bacağının hiç çağrılmadığı
mı yoksa sorunsuz çağrıldığı mı ÖLÇÜLEMEDİ** — `events.jsonl` bu ayrımı taşıyan bir olay yazmıyor
(başarılı çağrı için ayrı bir olay adı yok; `agent_call` genel sayaçtır ve bugün 11 kez ateşledi).

---

## 6. TOHUM YENİLEMESİNİN ETKİSİ — geçmiş retleri geçersiz kılar mı?

**Cevap iki parçalı ve brief'in varsayımından farklı bir yerde duruyor.**

### 6.1 Tohum, KAPININ örneklemini DEĞİŞTİRMEZ — çünkü kapı kendi örneklemini üretir

Ölçülmüş kanıt (`reflect._submit_locked`, canlı kod):

```python
bars, index = dataset.load()
inc  = _wf_cached(params_of(current), ..., bars, index, goal, ...)
cand = backtest.walk_forward(params_of(candidate), bars, index, goal, ...)
```

Kapı `state/meridian.db::trades` tablosunu **okumaz**; barlardan **yeniden simüle eder**
(`backtest.walk_forward`). Dolayısıyla 18:54Z'de defterin 97→887'ye çıkması, `backtest_gate`/OOS
örneklemine **doğrudan** bir şey eklemez.

**Ama tohumun kaynağı zaten kapının kendi çıktısıdır:** `inc_cache.json` (mtime 2026-08-13T07:09Z,
tohumdan ~12 saat ÖNCE) `n_trades_total: 885` diyor; DB'de `replay_seed` damgalı satır sayısı da
**tam 885**. Yani tohum işlemi, yürüyen walk-forward'ın ürettiği 885 simüle işlemi işlem defterine
**kalıcılaştırdı**. Defterdeki 887 satırın **885'i `replay_seed`, yalnız 2'si `live_paper`**
(T00096, T00097). `analytics` bu damgayı zaten "TRAINING sayılır, canlı kanıt DEĞİL" diye işliyor.

**Tohumun GERÇEKTEN etkilediği yer üreticidir:** `propose_deterministic` exploit sezgiseli
`store.read_jsonl("trades.jsonl", limit=40)` ile son 40 işlemi okur ve `store.read_jsonl` bu ad için
**DB-destekli**dir (`store.py:563`). Yani exit-reason karışımı ve `win_rate` artık simüle satırlardan
geliyor — tekrar desenini (§2) üreten sezgiselin girdisi değişti.

### 6.2 Asıl değişim: kapının örneklemi zaten ~10× büyümüştü — ve bu retleri GEÇERSİZ KILAR

| ölçüm anı | kaynak | OOS fold n | OOS toplam | OOS skoru |
|---|---|---|---|---|
| 2026-07-14 (H00001) | defter | **8 / 7 / 17** | ~32 | 0,178 |
| 2026-08-01 (H00044–H00051) | defter | **31 / 29 / 30** | ~90 | 0,0845 |
| **2026-08-13T07:09 (bugün)** | `inc_cache.json` | **178 / 111 / 36** | **560** (arama 347 + teyit 205) | **0,2354** |

**Kapının bugün gördüğü örneklem, Ağustos başındaki retlerin gördüğünün ~6×'ı, Temmuz
başındakilerin ~17×'ı.** `probgate`'in gücü doğrudan örneklem büyüklüğüne bağlıdır (blok-bootstrap
2000 replikasyon, ama bloklar 32 işlemlik bir havuzdan çekiliyorsa `P(ΔS>0)` gürültünün kendisidir).
**Bu, 30 backtest-değerlendirmesinin tamamını farklı bir tabana taşır** — özellikle §4'ün
"eşiğe yakın" adayları (H00033 P=0,799, H00039 P=0,709, H00048 P=0,614) tam olarak gücün
kritik olduğu banttadır.

**Büyümenin nedeni tohum DEĞİL, parametre değişimidir** — `inc_cache` anahtarı sürüm **5** ve
`position_size_r: 0.5` taşıyor; 2026-08-12 operatör penceresi `position_size_r 1,0→0,5` +
`limits.max_open_positions 5→20` ikilisini indirdi (`strategy.yaml` notu + `goal.yaml:131`).
**Hangi kalemin ne kadar katkı verdiği ÖLÇÜLMEDİ** — ayrıştırmak kontrollü bir yeniden koşum ister
ve bu turda yapılmadı.

### 6.3 Örneklem duyarlılığı olan kalemler — ADIYLA

| kalem | yer | duyarlılık |
|---|---|---|
| `goal.min_sample: 30` | `state/goal.yaml:33` | Dilim bunun altındaysa `oos_score = None` → **ship yapısal olarak imkânsız**. `chop` bugün 27. |
| dilim tabanı `max(10, int(min_sample × 0.7)) = 21` | `reflect.py:482` | İki taraftan biri 21 işlemin altındaysa `magnitude_ok` düşer. |
| `probgate` blok-bootstrap gücü | `probgate.py::evaluate` | Blok boyu = medyan tutuş süresi; havuz küçükse bloklar aynı işlemleri tekrar tekrar çeker → `P` gürültüye yaklaşır. |
| fold-çoğunluğu vetosu | `reflect.py:370` | Fold n'i küçüldükçe `avg_r` kıyası tek işlemle dönebilir. Bugün fold3 (arama dilimi) n=36. |
| `oos_erosion` marjı | `reflect.py:474` | Aynı pencereye sorulan soru sayısı >20 olunca ek marj biner. Defterde 3 ret **doğrudan bundan**: H00041 (144 sorgu), H00043 (21), H00051 (50). Pencere geometrisi değişirse parmak izi değişir ve **sayaç sıfırlanır**. |
| `@regime` dilimleme | `reflect._eval_regime_of` | Rejim-koşullu hipotez örneklemi paramparça eder. `chop` = 27/885 (%3). |

### 6.4 Tohum sonrası da ÇÖZÜLMEYEN: `chop`

DB'de tohum sonrası rejim dağılımı ve fold kırılımı:

| fold (ts_close) | toplam | trend_up | **chop** |
|---|---:|---:|---:|
| 2024-01-01 → 2024-10-01 | 189 | 181 | **8** |
| 2024-10-01 → 2025-07-01 | 128 | 109 | **19** |
| 2025-07-01 → 2026-04-30 | 255 | 255 | **0** |
| **OOS toplam** | **572** | **545** | **27** |

**`chop` OOS'ta 27 işlem — eşik 30.** Tohum yenilemesi bunu **çözmedi ve çözemez** (tohum zaten
walk-forward çıktısıdır). Canlı rejim `chop` olduğu ve arka-plan turları `chop` sertifikalı
üretim yaptığı sürece, **`@chop` hipotezleri ölçülemez kalır** — H00052'nin
"aday/incumbent OOS skoru TANIMSIZ (min_sample altı)" reti ve Ağustos'un 450 NULL sondası
aynı tek nedenin iki yüzüdür.

### 6.5 Yan bulgu — mevcut incumbent'ın kendisi `overfit_suspect` eşiğinin çok üstünde

`inc_cache.json`, `eval_regime=None`: **`oos_score = +0,2354` · `holdout_score = −0,5366`.**
Sapma **0,772**; `reflect.HOLDOUT_DIVERGENCE = 0,10`. Kod bu bayrağın "ship'i BLOKLAMADIĞINI"
açıkça yazıyor (`reflect.py:34`), yani bir kapı ihlali değil — ama **savunulan tabanın kendisi**
holdout'ta sert negatif. Aynı dosyada `oos_folds` (arama dilimi) üçüncü fold'u `2025-07-01 →
2025-08-18`, n=36, `avg_r = −0,2223`; `oos_folds_full` aynı fold'u `2025-07-01 → 2026-04-30`,
n=249, `avg_r = +0,2140` gösteriyor. Yani **fold-çoğunluğu vetosu, arama/teyit kesiminin
(2025-08-18) bıraktığı 36 işlemlik negatif kütükle karar veriyor.** Bu bir hüküm değil, ölçülmüş
bir gözlemdir; nedeni ve doğru davranışı bu turda **ÖLÇÜLMEDİ**.

---

## 7. ÖLÇÜLEMEYENLER (uydurma yasağı gereği açık liste)

| kalem | neden ölçülemedi |
|---|---|
| Aynı 52 hipotezin bugünkü tabanda yeniden koşulduğunda ne olacağı | `backtest.walk_forward` canlıda ölçülmüş 27–100 dk sürüyor (`arming.py` beyanı); 52 aday × 2 taraf bu turun kapsamına sığmaz. Yalnız **taban** (`inc_cache`) okundu. |
| Örneklem büyümesinin `position_size_r` / `max_open_positions` / `execution_v2` arasındaki payı | Kontrollü yeniden koşum gerekir; yapılmadı. |
| 2026-08-09 sonrası LLM bacağının çağrılıp çağrılmadığı | `events.jsonl` başarılı beyin çağrısı için ayrı olay yazmıyor; yalnız `unavailable`/`cooldown` yazıyor. Sessizlik iki şeyi de anlatabilir. |
| `hermes_search_done` içindeki `status: "shipped"` (5 kayıt) satırlarının `evaluated`/`best` alanlarının `null` olması | Alanlar kaynakta doldurulmuyor; ship'in hangi adaydan geldiği bu olaydan okunamıyor. Defterle çapraz eşleme yalnız 2 ship gösteriyor (v0002, v0003). |
| `entry.w_tight` no-op'unun (H00046) "atıl düğme" mi yoksa "varsayılanla aynı değer" mi olduğu | İkincisi kod okumasıyla doğrulandı (`strategy.py:418`, varsayılan **0.30**, önerilen **0.3**); atıllık ayrıca sınanmadı. |
| `guard.max_accepted_changes_per_month = 8` kotasının bağlayıcılığı | 0 ship olduğu için hiç ateşlemedi — ölçülecek bir davranış yok. |

---

## 8. EK — 52 RETİN TAM ANATOMİSİ

Sütunlar: `P(ΔS>0)` = blok-bootstrap kazanma oranı (probgate öncesi legacy satırlarda yok) ·
`ort.Δ` = `search_mean_delta` (PARA-v3) · `fold` = fold-çoğunluğu (`fold_wins`).
Sınıflar: **TEKRAR** = guard hafızası kesti · **NO-OP** = aday bit-bit aynı · **ÖLÇÜLEMEDİ** =
OOS tanımsız · **SHIP** = superseded · **ÖLÇÜLDÜ** = gerçek yargı.

| id | tarih | değişken | eski→yeni | üretici | aşama | sınıf | P(ΔS>0) | ort.Δ | OOS inc→cand | fold | gerekçe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H00001 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | backtest | ÖLÇÜLDÜ | — | — | 0.178→0.1885 | 1/3 | candidate OOS 0.1885 did not beat incumbent 0.178 + 0.02 |
| H00002 | 2026-07-14 | `entry.min_score` | 60→61 | deterministic | backtest | ÖLÇÜLDÜ | — | — | 0.178→0.1814 | 3/3 | candidate OOS 0.1814 did not beat incumbent 0.178 + 0.02 |
| H00003 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00004 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00005 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00006 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00007 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00008 | 2026-07-14 | `entry.rs_rating_min` | 70→71 | deterministic | backtest | ÖLÇÜLDÜ | — | — | 0.178→0.1813 | 2/3 | candidate OOS 0.1813 did not beat incumbent 0.178 + 0.02 |
| H00009 | 2026-07-14 | `entry.rs_rating_min` | 70→71 | deterministic | guard | TEKRAR | — | — | —→— | — | entry.rs_rating_min=71 already tried and failed (hyp H00008, rejected_by_backtest) |
| H00010 | 2026-07-14 | `entry.rs_rating_min` | 70→71 | deterministic | guard | TEKRAR | — | — | —→— | — | entry.rs_rating_min=71 already tried and failed (hyp H00008, rejected_by_backtest) |
| H00011 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00012 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00013 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00014 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00015 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00016 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00017 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00018 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00019 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00020 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00021 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00022 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00023 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00024 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00025 | 2026-07-14 | `stop_loss_atr_mult` | 2.0→2.1 | deterministic | guard | TEKRAR | — | — | —→— | — | stop_loss_atr_mult=2.1 already tried and failed (hyp H00001, rejected_by_backtest) |
| H00026 | 2026-07-14 | `entry.pivot_proximity_pct` | 2.0→2.3 | sprint_search | superseded | SHIP | — | — | 0.1963→0.2555 | 2/3 | — |
| H00027 | 2026-07-19 | `entry.pivot_proximity_pct` | 2.3→2.0 | hermes:nous | backtest | ÖLÇÜLDÜ | — | — | 0.1854→0.1463 | 1/3 | candidate OOS 0.1463 did not beat incumbent 0.1854 + 0.02 |
| H00028 | 2026-07-20 | `exit.scale_out_frac` | 0.0→0.5 | hermes:nous | backtest | ÖLÇÜLDÜ | 0.364 | -0.0043 | 0.1757→0.1796 | 0/3 | P(ΔS>0)=0.364 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00029 | 2026-07-20 | `entry.w_prox` | None→0.15 | coordinate_search | superseded | SHIP | 0.941 | 0.0016 | —→— | 1/1 | — |
| H00030 | 2026-07-21 | `regime.min_exposure_score` | 20→40 | cf_evidence | backtest | ÖLÇÜLDÜ | 0.512 | -0.0026 | 0.2043→0.1951 | 2/3 | P(ΔS>0)=0.512 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00031 | 2026-07-21 | `entry.rs_rating_min` | 70→60 | cf_evidence | backtest | ÖLÇÜLDÜ | 0.0 | -0.0921 | 0.2043→0.1077 | 0/3 | P(ΔS>0)=0.000 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00032 | 2026-07-21 | `exit.breakeven_r` | 1.0→0.0 | coordinate_search | confirm | ÖLÇÜLDÜ | 0.909 | 0.1281 | 0.0988→0.2119 | 2/3 | teyit dilimi: P(ΔS>0)=0.140 < gerekli 0.70 (K=1 aday cezası dahil) |
| H00033 | 2026-07-22 | `entry.w_rs` | None→0.4 | hermes:nous | backtest | ÖLÇÜLDÜ | 0.799 | 0.0643 | 0.1509→0.2186 | 1/3 | P(ΔS>0)=0.799 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00034 | 2026-07-22 | `entry.w_rs` | None→0.3 | hermes:gemini | backtest | ÖLÇÜLDÜ | 0.122 | -0.0663 | 0.1819→0.1107 | 0/3 | P(ΔS>0)=0.122 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00035 | 2026-07-23 | `entry.max_ext_atr` | 0.0→6.0 | hermes:nous | backtest | ÖLÇÜLDÜ | 0.2545 | -0.1185 | 0.1562→0.0028 | 2/3 | P(ΔS>0)=0.255 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00036 | 2026-07-27 | `exit.profit_target_r` | 2.5→3.0 | hermes:gemini | backtest | ÖLÇÜLDÜ | 0.566 | 0.021 | 0.1284→0.163 | 2/3 | P(ΔS>0)=0.566 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00037 | 2026-07-28 | `exit.giveback_pct` | 0.0→0.3 | hermes:nous | backtest | ÖLÇÜLDÜ | 0.218 | -0.121 | 0.122→-0.0062 | 1/3 | P(ΔS>0)=0.218 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00038 | 2026-07-28 | `exit.profit_target_r` | 2.5→2.0 | hermes:gemini | backtest | ÖLÇÜLDÜ | 0.587 | 0.0226 | 0.1309→0.1179 | 1/3 | P(ΔS>0)=0.587 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00039 | 2026-07-28 | `entry.rs_rating_min@trend_up` | 70→65 | hermes:nous | backtest | ÖLÇÜLDÜ | 0.709 | 0.0837 | 0.1327→0.2096 | 3/3 | P(ΔS>0)=0.709 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00040 | 2026-07-28 | `exit.time_stop_days` | 15→10 | hermes:gemini | backtest | ÖLÇÜLDÜ | 0.202 | -0.1532 | 0.1309→0.0011 | 1/3 | P(ΔS>0)=0.202 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00041 | 2026-07-29 | `entry.min_volume_ratio` | 1.5→1.8 | hermes:gemini | backtest | ÖLÇÜLDÜ | 0.2665 | -0.1196 | 0.0853→0.0151 | 0/3 | OOS aşınması: bu pencereye 144 sorgu soruldu (>20) — ek marj 0.01 karşılanmadı |
| H00042 | 2026-07-31 | `entry.min_rvol` | None→1.2 | hermes:gemini | backtest | ÖLÇÜLDÜ | 0.229 | -0.1721 | 0.0589→0.0107 | 1/3 | P(ΔS>0)=0.229 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00043 | 2026-07-31 | `entry.rs_dual_horizon` | 0→1 | deterministic:virgin | backtest | ÖLÇÜLDÜ | 0.456 | -0.03 | 0.0589→0.0697 | 2/3 | OOS aşınması: bu pencereye 21 sorgu soruldu (>20) — PARA ölçeğinde ek marj 0.001908 karşı… |
| H00044 | 2026-08-01 | `entry.w_mom` | None→0.2 | deterministic:virgin | backtest | ÖLÇÜLDÜ | 0.1785 | -0.1341 | 0.0845→0.0595 | 1/3 | P(ΔS>0)=0.178 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00045 | 2026-08-01 | `entry.w_rvolband` | None→0.2 | deterministic:virgin | backtest | ÖLÇÜLDÜ | 0.4285 | -0.0152 | 0.0845→0.087 | 1/3 | P(ΔS>0)=0.428 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00046 | 2026-08-01 | `entry.w_tight` | None→0.3 | deterministic:virgin | backtest | NO-OP | 0.0 | 0.0 | 0.0845→0.0845 | 0/3 | P(ΔS>0)=0.000 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00047 | 2026-08-01 | `entry.w_vol` | None→0.25 | deterministic:virgin | backtest | ÖLÇÜLDÜ | 0.03 | -0.2019 | 0.0845→0.0336 | 0/3 | P(ΔS>0)=0.030 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00048 | 2026-08-01 | `exit.chandelier_lookback` | 0→15 | deterministic:virgin | backtest | ÖLÇÜLDÜ | 0.6135 | 0.0457 | 0.0845→0.0951 | 2/3 | P(ΔS>0)=0.614 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00049 | 2026-08-01 | `exit.early_kill_bars` | None→5 | deterministic:virgin | backtest | NO-OP | 0.0 | 0.0 | 0.0845→0.0845 | 0/3 | P(ΔS>0)=0.000 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00050 | 2026-08-01 | `exit.early_kill_pivot` | None→0 | deterministic:virgin | backtest | NO-OP | 0.0 | 0.0 | 0.0845→0.0845 | 0/3 | P(ΔS>0)=0.000 < gerekli 0.80 (K=1 aday cezası dahil) |
| H00051 | 2026-08-02 | `exit.scale_out_r` | 2.0→1.5 | hermes:gemini | backtest | NO-OP | 0.0 | 0.0 | 0.0845→0.0845 | 0/3 | OOS aşınması: bu pencereye 50 sorgu soruldu (>20) — PARA ölçeğinde ek marj 0.001908 karşı… |
| H00052 | 2026-08-12 | `exit.trail_atr_mult@chop` | 2.5→1.5 | hermes:nous | backtest | ÖLÇÜLEMEDİ | 0.3959 | -0.0011 | —→— | 0/1 | aday/incumbent OOS skoru TANIMSIZ (min_sample altı) — ölçülmemiş aday ship edilemez |
