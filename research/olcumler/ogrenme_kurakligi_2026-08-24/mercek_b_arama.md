# MERCEK B · ARAMA UZAYI — AYNI 40 ADAY MI DÖNÜYOR?

Tarih: 2026-08-24 · Kapsam: SALT OKUMA teşhis (canlıya yazılmadı, kod değişmedi, git koşulmadı)
Ölçen: ajan (Mercek B) · Yazma alanı: `research/olcumler/ogrenme_kurakligi_2026-08-24/`

## HÜKÜM (tek cümle)

**Evet — ve hipotezden daha sert: her saat AYNI 40 aday, AYNI ÖNBELLEKLENMİŞ walk-forward
sonuçlarıyla yeniden kapıdan geçiriliyor; tek bir taze hesap bile yapılmıyor. `butce: 10`
(taze hesap kotası) HİÇ HARCANMIYOR. Döngü matematiksel bir SABİT NOKTA'da: girdilerinin
hiçbirini değiştiremediği için çıktısı da asla değişemez.**

Üstüne iki bağımsız kilit ölçüldü:
1. Oto-ölçekleme merdiveni `duvar: 1` ile KALICI olarak çivilenmiş — bütçe 10'dan, k_max 2'den
   asla çıkamaz (geri dönüşü olan hiçbir kod yolu yok).
2. Canlı öğrenme süreci 2026-08-16'dan beri yeniden başlatılmadı; 2026-08-23 21:06'da dağıtılan
   teşhis enstrümantasyonu (red-gerekçe dağılımı) DİSKTE VAR ama KOŞMUYOR.

---

## 1. `warmup_sprint` olayını üreten kod ve adayların kaynağı

* Üretici: `meridian/hermes_runtime.py:131 _warmup_sprint()` → log satırı `:219 obs.log("warmup_sprint", ...)`.
* Kadans: `hermes_runtime.py:32 WARMUP_EVERY_POLLS = 12` × `HERMES_POLL_SECONDS=300` = **saatte bir**
  (`:550 if _state["_warm_ticks"] % WARMUP_EVERY_POLLS == 0`). Ölçülen canlı aralık: 3678–3680 s.
* Adayları üreten yer: `meridian/reflect.py:1859 coordinate_descent_search`, satır 1993-2013.
  Kaynak **sabit liste DEĞİL, üreteç**; ve **rastgelelik YOK**:
  - arama uzayı = `config.bounds()` anahtarları, `hayalet_suzgeci` ile süzülmüş (`reflect.py:967`),
  - sıralama = `_ucb_rank` (`reflect.py:868`) — docstring'in kendi beyanı: *"Ties break by name so the
    same ledger always yields the same order (reproducible, testable — no wall-clock/random)"*,
  - aday üretimi = `for k in range(k_max,0,-1) → for var in ranked → for direction in (+1,-1)`,
    `bounds` adımıyla `cur ± k*step`, `seen`/`tried`/`_already_failed` süzgeçleri.
  Hiçbir `random`, hiçbir saat okuması yok.

## 2. Tohum/determinizm — KANIT

**Kodda tohum yok, çünkü rastgelelik yok.** Determinizm üç girdiye bağlı: `bounds.yaml`,
`strategy.yaml` (yürürlükteki paramlar), `hypotheses.jsonl` (UCB defteri) + `exit_efficiency.json`.

Canlı girdiler yerele kopyalanıp (salt okuma) aday üretimi **birebir yeniden üretildi**
(`scratchpad/repro_probes.py`, `MERIDIAN_ROOT`=scratch; hiçbir walk-forward koşulmadı):

```
bounds anahtar sayisi: 32 | hayalet suzgecinden gecen: 32 | hayalet: 0 | defter hipotez: 60
toplam uretilen aday (k_max=2): 76 | plan kapagi max(budget*4,40) = 40
iki cagri ayni mi: True | sha16: eea12681fa9ff699 eea12681fa9ff699
```

Girdilerin canlıdaki DONUKLUĞU (mtime, `ls -la --time-style=long-iso /opt/meridian/state/`):

| dosya | canlı mtime | yorum |
|---|---|---|
| `hypotheses.jsonl` | 2026-08-21 18:02 | UCB sıralamasının tek girdisi — 2+ gündür DEĞİŞMİYOR |
| `strategy.yaml` | 2026-08-12 20:13 | sondaların çıkış noktası (`cur`) — 12 gündür sabit |
| `exit_efficiency.json` | 2026-08-21 20:32 | sıralama bonusu — sabit |
| `bounds.yaml` | 2026-08-23 16:48 | **içerik değişmedi**: canlı sha256 = yerel depo sha256 `a001e4b3…c9e62` (mtime git trafiğinin içerik-aynı yeniden yazımı, CLAUDE.md §8 vakası) |

Ve KAPALI DÖNGÜ: ısınma `record_session=False` ile koşar, hiçbir şey ship etmez, deftere hipotez
yazmaz → **kendi girdilerinin hiçbirini değiştiremez**. Girdi sabit + fonksiyon deterministik ⇒
çıktı sabit. "Aynı 40" bir tesadüf değil, bir teoremdir.

### Planda gerçekten olan 40 aday (yeniden üretilmiş sıra)

```
 1 entry.w_turnover→0.1      11 exit.scale_out_r→1.0     21 entry.min_volume_ratio→1.3  31 portfolio.sector_cap→10.0
 2 exit.breakeven_r→2.0      12 exit.time_stop_days→17   22 entry.pivot_proximity_pct→2.5 32 position_size_r→0.7
 3 exit.breakeven_r→0.0      13 exit.time_stop_days→13   23 entry.pivot_proximity_pct→2.1 33 position_size_r→0.3
 4 stop_buffer_atr→0.3       14 exit.trail_atr_mult→2.7  24 entry.w_mom→0.1              34 regime.min_exposure_score→50
 5 stop_mode→1               15 exit.trail_atr_mult→2.3  25 entry.w_prox→0.25            35 regime.min_exposure_score→30
 6 exit.chandelier_lookback→10 16 entry.max_ext_atr→2.0  26 entry.w_prox→0.05            36 stop_loss_atr_mult→2.2
 7 exit.early_kill_bars→3    17 entry.min_rvol→0.2       27 entry.w_rvolband→0.1         37 stop_loss_atr_mult→1.8
 8 exit.early_kill_pivot→1   18 entry.min_score→62       28 entry.w_tight→0.15           38 exit.profit_target_r→3.5
 9 exit.giveback_pct→0.2     19 entry.min_score→58       29 entry.w_vol→0.15             39 entry.w_rs→0.2
10 exit.scale_out_r→3.0      20 entry.min_volume_ratio→1.7 30 portfolio.heat_cap→2.0     40 entry.rs_rating_min→72
```

**İlk 40'ın 40'ı da k=2 (EN BÜYÜK adım) hamlesidir; k=1 (ince ayar) katmanından TEK BİR aday bile
plana giremiyor.** Toplam 76 adayın 36'sı (%47) yapısal olarak erişilmez — plan kapağı
`probes[:max(budget*4, 40)]` (reflect.py:2022) bütçe 10'da 40'ta sabit.

## 3. Ardışık saatlerin gerçek aday kimlikleri — canlıdan DOĞRUDAN ÖLÇÜLEMEDİ (neden yazılı)

Denenen ve **başarısız** kanallar (UYDURMA YASAĞI: yokluk "aynı" diye yorumlanmadı, yeniden üretimle
kanıtlandı):

* `journalctl -u meridian-learn`: `warmup_sprint` satırı aday kimliği TAŞIMIYOR (yalnız sayılar).
  26 saatte 25 satır, hepsi birebir aynı; **başka hiçbir olay yok**:
  ```
  # journalctl … --since "26 hours ago" | grep -o '"event": "[a-z_]*"' | sort | uniq -c
       25 "event": "warmup_sprint"
  ```
* `state/search_progress.json` = `{}` (hem canlı hem sprint kum havuzu) — ilerleme kimliği tutmuyor.
* `improvement_proposals.jsonl` son yazım **2026-08-10 20:28** — ısınma zaten öneri üretmiyor.
* `probe_cache.json` anahtarları var ama tek girdi (aşağıda) — plan kimliğini vermiyor.
* Kesin kimlik LOG'a hiç girmiyor: `coordinate_descent_search` dönüşünde `trace` VAR, ama
  `hermes_runtime.py:219`'daki `obs.log` onu basmıyor; sprint tarafında `sprint_run._slim`
  (`sprint_run.py:110-118`) **yalnız `passes=True` iz satırlarını** saklıyor → `cleared=0` olan her
  koşumda `trace: []` yazılıyor. Yani "hiçbir aday geçemedi" hâli, tam da o hâlin kanıtını atıyor.

⇒ Kimlik eşitliği **kod + donuk girdi + yeniden üretim** ile kanıtlandı (§2), canlı log'dan
doğrudan okunamadı. Bu bir ölçüm borcudur, ölçülmüş bir eşitsizlik değil.

### Buna karşılık "taze hesap yok" DOĞRUDAN ölçüldü (dolaylı değil)

1. **Duvar saati.** Ardışık `warmup_sprint` log'ları arası 3679 s; 12 poll × 300 s = 3600 s uyku ⇒
   12 pollün TÜM işi + ısınmanın TAMAMI ≤ **79 saniye**. Bu süreye `dataset.load()` +
   `prefill_incumbents` + 1 incumbent + 40 sonda dahil. Koddaki kendi ölçümü: bir walk-forward
   "~a minute" (reflect.py:2100 yorumu), ısınmanın nominali "1-5 SAAT" (reflect.py:1876). 41 taze
   walk-forward 79 saniyeye SIĞMAZ ⇒ hepsi önbellekten.
2. **Havuz olayı hiç yok.** `MERIDIAN_PARALLEL_PROBES=1` birimde AÇIK (systemd `meridian-learn`),
   yani taze sonda VARSA `_parallel_prefill_probes` mutlaka `parallel_probes_prefilled` basar
   (`reflect.py:1771`). 26 saatte **0 kez** basıldı, `parallel_probes_failed` da yok ⇒ `jobs` her
   seferinde BOŞTU ⇒ 40 sondanın 40'ı da önbellek isabeti.
3. Pencereler DONMUŞ sabitler (`dataset.py:102-131`: IS 2022-01-01, OOS 2024-01-01→2026-04-30,
   HOLDOUT 2026-07-30) ve sonda önbellek anahtarı yalnız (pencere, tüm paramlar, var, değer)
   (`reflect.py:1583 _probe_key`) ⇒ **yeni piyasa verisi bu sondaların sonucunu DEĞİŞTİREMEZ.**

## 4. `evaluated: 40` (ısınma) ile `evaluated: 6` (sprint) — İKİ AYRI MEKANİZMA, evet

| | ısınma (`warmup_sprint`) | sprint (`meridian-sprint@<sid>`) |
|---|---|---|
| süreç | `meridian-learn` (PID 305928, canlı `state/`) | `python -m meridian.sprint_run`, KUM HAVUZU `state/sprint/<sid>/` |
| giriş noktası | `hermes_runtime._warmup_sprint` → `coordinate_descent_search(record_session=False)` | `reflect.search_and_submit` → aynı arama, `record_session=True` |
| pencere | üretim, DONMUŞ (`dataset` sabitleri) | `sprint.SELECT_WINDOWS` (2022-01-01…2024-06-30, CUTOFF 2024-06-30) — AYRIK |
| bütçe | `hermes.warmup_budget()` → 10 (taban 10 × çarpan 1) | `sprint.env`: `MERIDIAN_SPRINT_CONF={"k_max":2,"budget":6}` |
| ship | YOK ("Nothing ships") | VAR (kapıyı geçen olursa) |
| son sonuç | evaluated 40 / cleared 0 (saatlik) | evaluated 6 / cleared 0 (2026-08-21) |

`evaluated: 6` = kum havuzunda sonda önbelleği SOĞUK olduğu için plan taze bütçeyle sınırlandı:
6 taze hesap = 6 sonda. `evaluated: 40` = önbellek SICAK olduğu için plan kapağına (40) kadar
bedava sonda alındı. Yani iki sayı aynı formülün iki ucu: **soğuk önbellek → evaluated = bütçe;
tam sıcak önbellek → evaluated = plan kapağı.**

Kanıt (kum havuzu): `/opt/meridian/state/sprint/20260821-220656/sprint.env` →
`MERIDIAN_SPRINT_CONF='{"k_max":2,"budget":6}'`; `state/sprint_runs.jsonl` →
`{"status":"no_clearing_candidate","evaluated":6,"cleared":0,"incumbent_oos":0.409,"best":null,"trace":[]}`

## 5. `butce: 10` ama `evaluated: 40` — tutarsızlık DEĞİL, iki ayrı sayaç (ve asıl skandal burada)

`reflect.py:2014-2031` (kodun kendi beyanı): *"UYARLANABİLİR BÜTÇE: `budget` artık TAZE
(önbellek-ıskası) hesap sayısıdır. Önbellekte hazır duran sonda BEDAVA değerlendirilir (bütçe
yemez)"*.

* `butce = 10` → **taze walk-forward kotası** (yalnız önbellekte OLMAYAN sondalar yer).
* `evaluated = 40` → **kapıdan geçirilen toplam sonda** = plan kapağı `max(budget*4, 40)`.

Ölçülen hâl: 40 sondanın 40'ı önbellek isabeti (§3) ⇒ **`fresh = 0`, kotanın 10'unun 10'u
kullanılmadan duruyor.** Yani "bütçe her saat harcanıyor" hipotezi ÇÜRÜDÜ — bütçe hiç
harcanmıyor; harcanan tek şey ~1 dakikalık CPU ve bir log satırı.

**ÖLÇÜM BOŞLUĞU (kritik):** `coordinate_descent_search` dönüşünde bu ayrımı gösterecek alanlar
ZATEN VAR — `"fresh": _fresh_done, "cached_hits": evaluated - _fresh_done` (`reflect.py:2131`).
`hermes_runtime.py:219-224`'teki `obs.log` bu iki alanı BASMIYOR. Tek bir `fresh=0` alanı
loglansaydı, "öğrenme kuraklığı" haftalarca gizli kalmazdı.

---

## EK BULGU 1 — Oto-ölçekleme merdiveni KALICI OLARAK ÖLÜ (`duvar: 1`)

Canlı `state/warmup_scale.json`:
```json
{"carpan": 1, "duvar": 1,
 "son": {"evaluated": 40, "cleared": 0, "kesildi": false, "at": "2026-08-23T23:15:05+00:00"}}
```

Yasa (`hermes.py:1770-1814`): `cleared==0 → çarpan ×2` ama önce
`carpan = min(carpan, duvar, WARMUP_SCALE_MAX)` (`:1774`) ve büyüme dalı
`elif onceki["carpan"] < min(duvar, ...)` (`:1811`). `duvar=1` iken `1 < 1` **False** ⇒ çarpan
sonsuza dek 1, bütçe 10, k_max 2.

`duvar` yalnız TEK yerde yazılır (`:1807`, `kesildi=True` dalı) ve **hiçbir kod yolu onu
yükseltmez ya da temizlemez** — `cleared>0` dalı bile yalnız çarpanı tabana çeker (`:1810`).
Çarpan 1'ken bir kez süre tavanına takılan koşum `duvar = max(1, 1//2) = 1` yazar ve merdiveni
GERİ DÖNÜŞSÜZ kilitler. Kum havuzuna 2026-08-21 21:10'da kopyalanan durum da `duvar:1` — yani
kilit en az 3 gündür (muhtemelen çok daha uzun) yerinde. Son 7 günde tek bir
`warmup_budget_scaled` ya da `search_sure_tavani_kesildi` olayı yok (journalctl, 7 gün).

Sonuç: `cleared=0 → genişlet` kuralı KAĞITTA var, CANLIDA ölü. Ve genişleseydi bile bu, aynı 40'ın
üstüne 36 aday daha (k_max 3'te 110, k_max 4'te 141) açardı — yani kuraklığın çözümü değil ama
şu anki mutlak durgunluğun sebeplerinden biri.

## EK BULGU 2 — Canlı süreç 7 GÜNDÜR yeniden başlatılmadı: dağıtılan teşhis KOŞMUYOR

```
ExecMainStartTimestamp=Sun 2026-08-16 23:27:06 UTC        (ps ELAPSED 7-00:29:57)
/opt/meridian/meridian/hermes_runtime.py   mtime 2026-08-23 21:06
/opt/meridian/meridian/reflect.py          mtime 2026-08-23 21:06
sha256(canlı hermes_runtime.py) == sha256(depo) = 79575145…76d8
```

Diskteki (ve depodaki) kod `obs.log("warmup_sprint", …, neden_dagilim=_nd, …)` basıyor
(`hermes_runtime.py:218-220`), **canlı log satırlarında `neden_dagilim` alanı YOK** ve alan sırası
eski imzayla birebir uyuşuyor. `obs._emit` alan atmıyor (`obs.py:86-99`) ⇒ tek açıklama: süreç
16 Ağustos'tan kalma kodu bellekte koşuyor. Operatörün "cleared=0'ı neden teşhis edemiyoruz"
sorusunun cevabı da bu: teşhis 23 Ağustos'ta dağıtıldı, hiç yeniden başlatılmadı.

Yan etki: 40 sondalık sonuç önbelleği bu 7 günlük SÜREÇ BELLEĞİNDE yaşıyor. Diskteki
`probe_cache.json` yalnız **1** girdi taşıyor (rev 1787344310 = `wf_cache_rev.json` ile uyumlu,
mtime 2026-08-21 20:45). Yani bir yeniden başlatma bu sabit noktayı kırar (40 sonda taze
hesaplanır) — ama sonuç DEĞİŞMEZ, çünkü pencereler ve paramlar aynı; yalnız ~saatlerce CPU yanar.

---

## KÖK NEDEN ADAYI (bu mercekten)

Isınma sprinti bir **öğrenme mekanizması değil, sabit bir birim testidir**: donmuş pencerelerde,
donmuş paramlardan, donmuş bir defterle üretilen deterministik 40 adayı, önbellekten okuduğu
sonuçlarla her saat yeniden reddediyor. Kendi girdilerinin hiçbirini değiştiremediği için
(record_session=False, ship yok, hipotez yazımı yok) çıktısı da değişemez. `duvar:1` kilidi
arama uzayının %47'sini (ve k=1 ince-ayar katmanının TAMAMINI) yapısal olarak erişilmez tutuyor;
`fresh/cached_hits` loglanmadığı için bu durgunluk sayılarda "40 aday değerlendirildi" gibi
sağlıklı görünüyor.

## ÖLÇÜLEMEYENLER (borç listesi)

1. Ardışık iki saatin aday kimlikleri canlı log'dan **doğrudan** okunamadı (log/artefakt kimlik
   taşımıyor). Yeniden üretimle kanıtlandı; canlı doğrulama borcu duruyor.
2. Red gerekçelerinin dağılımı ölçülemedi — enstrümantasyon dağıtıldı ama süreç eski kodu koşuyor
   (EK BULGU 2). Yeniden başlatma olmadan ölçülemez.
3. `duvar: 1`'i yazan koşumun TARİHİ ölçülemedi: `warmup_scale.json` yalnız SON koşumu tutuyor ve
   ilgili `warmup_budget_scaled` olayı journalctl'in 7 günlük penceresinde yok.
4. Isınmanın beyan edilmiş tek faydası ("UCB önceliklerini ve sonda önbelleğini ısıtmak") bu turda
   ölçülmedi; kodun kendisi de bunu "açık ölçüm borcu" diye beyan ediyor (reflect.py:1931).
5. `evaluated=40` sondalarının kaçının önbellekten geldiği **doğrudan** sayılmadı (alan
   loglanmıyor); iki bağımsız dolaylı kanıtla (duvar saati + `parallel_probes_prefilled` yokluğu)
   gösterildi.
