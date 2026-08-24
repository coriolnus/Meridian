# MERCEK A — KAPI ERİŞİLEBİLİR Mİ?

Tarih: 2026-08-24 · Kapsam: SALT OKUMA teşhis (kod okuma + canlı A1 state/defter okuması).
Bu turda hiçbir ölçüm kodu yazılmadı, hiçbir walk-forward yeniden koşulmadı (ön-kayıt kartı yok).
Bütün sayılar ya KAYNAK KODDAN türetilmiş aritmetik ya da CANLI DEFTERDEN okunmuş kayıtlardır.

---

## 0. TEK CÜMLELİK HÜKÜM

Kapının örneklem tarafı ERİŞİLEBİLİR (taban 21 işlem isteniyor, canlıda 348 var), **eşik tarafı
canlı ısınma rejiminde FİİLEN ERİŞİLEMEZ**: gerekli olasılık `p_req = 1 − 0,20/K` ve K, canlıda
**2026-08-17T15:14:58'den beri 40'a çivilenmiş** durumda → **0,995**. Üstelik K bir KARAR değil,
**sonda önbelleğinin sıcaklığının yan ürünü**: aynı sistem K=10'dayken (önbellek soğukken)
2026-08-08 ve 2026-08-11'de aday TEMİZLEDİ, aynı gecenin bir sonraki koşumunda K=20'ye çıkınca
temizleyemedi. Yani "hiçbir aday geçemedi" ifadesi bir edge hükmü değil, bir **K hükmüdür**.

---

## 1. "cleared" TAM OLARAK NE İSTİYOR (çağrı zinciri)

`meridian/hermes_runtime.py:190` `_warmup_sprint` → `reflect.coordinate_descent_search`
→ döngü içinde `reflect.py:2079` `_gate_eval(inc, cand, k_probes=total, record_erosion=False)`
→ `passes` True ise `reflect.py:2093` `cleared += 1`.

Ship yolunda ise `reflect.py:2160` yalnız SONUCU adlandırır:
```
best = res.get("best")
if not best:
    return {"status": "no_clearing_candidate", "search": res}
```
Yani `:2160` hüküm vermez — hükmü `_gate_eval` verir, `:2160` yalnız "kimse geçmedi" etiketini basar.

### `_gate_eval` (meridian/reflect.py:400-660) — BEŞ TERİMLİ BAĞLAÇ

`reflect.py:640` civarı:
```
passes = bool(magnitude_ok and majority and tail_ok and dd_ok and dd_mtm_ok)
```

| # | terim | şart | eşik / kaynak |
|---|---|---|---|
| 1 | `magnitude_ok` | olasılıksal yasa: `prob.passes` **VE** `not thin` **VE** `cand_oos/inc_oos != None` **VE** `erosion_ok` | `probgate.P_BASE=0.80` üzerinden `p_req=1−(0,20−extra_p)/K`; `thin` tabanı `max(10, 0.7·goal.min_sample)` = **21** |
| 2 | `majority` | `fold_total>=2` **ve** `fold_wins >= (fold_total+1)//2`, **ve** `itiraz_edilmemis == 0` | fold başına `n>=3` kanıt şartı (reflect.py:432-470) |
| 3 | `tail_ok` | aday VaR ve CVaR'ı incumbent'ınkini `TAIL_MARGIN_R` üstünde artıramaz (OR, tek metrik yeter) | `reflect.py:37 TAIL_MARGIN_R = 0.5` R |
| 4 | `dd_ok` | `cand_dd <= inc_dd + DD_VETO_MARGIN` (kapanmış-işlem sermaye eğrisi) | `shadowlaw.py:90 DD_VETO_MARGIN = 0.08` |
| 5 | `dd_mtm_ok` | M2M düşüş ikizi — **bayrak kapalıyken TANIM GEREĞİ True** (`MERIDIAN_DD_MTM_VETO`) | NO-OP |

### Eşik nereden geliyor, kim set ediyor

`probgate.py:348-367`:
```
alpha_family = max(1e-6, (1.0 - p_base) - _meta_extra_p())
return min(P_CEIL, 1.0 - alpha_family / k)
```
- `P_BASE = 0.80` (probgate.py:42) — sabit, kodda.
- `_meta_extra_p()` canlı `state/gate_calibration.json`dan okunur. **CANLI ÖLÇÜM: `extra_p: 0.0`,
  `n_measured: 1`, `durum: "kurak"`** — yani meta-kalibrasyon hiç devreye girmedi, eşik saf
  `1 − 0,20/K`.
- **`k` = `k_probes` = o oturumda PLANLANAN TOPLAM sonda sayısı** (`reflect.py:2079`,
  `k_probes=total`, `total = len(probes)`). Önbellekten bedava gelen sondalar da K'ya SAYILIR
  (reflect.py:2029 yorumunda açıkça beyan edilmiş).

**Yani eşiği kimse "set etmiyor" — eşiği o koşumda kaç sonda planlandığı belirliyor.**

| K | `p_req = 1 − 0,20/K` |
|---:|---:|
| 1 | 0,800 |
| 2 | 0,900 |
| 6 | **0,9667**  ← sprint 20260821-220656 |
| 10 | 0,980 |
| 20 | 0,990 |
| 30 | 0,9933 |
| 40 | **0,995**  ← canlı ısınma, 2026-08-17'den beri |

---

## 2. `PROMOTE_MIN_PAIRS/MIN_BUCKET/R_GAP` ve `PROMOTE_MIN_N` BU YOLDA **KULLANILMIYOR**

Tam grep (`--include="*.py"`, tests hariç):
```
meridian/analytics.py:1125:LLM_PROMOTE_MIN_PAIRS = 30
meridian/analytics.py:1126:LLM_PROMOTE_MIN_BUCKET = 8
meridian/analytics.py:1127:LLM_PROMOTE_R_GAP = 0.3
meridian/analytics.py:1171-1173:  promoted = bool(len(pairs) >= LLM_PROMOTE_MIN_PAIRS and ...)
meridian/shadow_model.py:295: PROMOTE_MIN_N = 30
meridian/shadow_model.py:322-333: pairs = pairs[-cls.PROMOTE_MIN_N:]; promoted = bool(n >= ...)
```

- Brief'teki adlar bir nüansla yanlış: analytics'teki üçlünün gerçek adı **`LLM_PROMOTE_*`**dır.
- Bu üçlü **LLM görüş-terfi kapısıdır** (bir danışmanın veto yetkisi açılsın mı) — `analytics.py`
  içinde başlar ve orada biter.
- `shadow_model.PROMOTE_MIN_N` **gölge işlem-sonucu modelinin terfi kapısıdır** (WP3'ün bulduğu
  yapısal erişilmezlik ORADA).
- **İkisi de `reflect._gate_eval` / `coordinate_descent_search` zincirinde HİÇ ÇAĞRILMIYOR.**
  `reflect.py`nin `analytics` ile tek teması `search_and_submit` içinde `analytics.calibration()`
  çağrısıdır ve o çağrı **`best` bulunduktan SONRA** (güven skoru için) koşar — `cleared`
  kararına hiç girmez.

**Sonuç: "cleared" kapısı bambaşka bir kapıdır. WP3'ün gölge-terfi bulgusu bu kapıyı açıklamaz;
buraya taşınamaz.**

---

## 3. YAPISAL ERİŞİLEBİLİRLİK — WP3 TARZI ARİTMETİK, BU KAPI İÇİN

Kaynak: canlı `state/inc_cache.json` (yürürlükteki incumbent'ın walk-forward'ı, kapının GERÇEK
girdisi; dosya mtime 2026-08-21 22:39).

```
oos_score:        0.2687          (None DEĞİL → "ölçülmemiş aday" dalı kapalı)
n_trades_graded:  886
oos_split:        search 2024-01-11 → 2025-08-18 · confirm 2025-08-18 → 2026-04-30
len(_trades_search):  348
len(_trades_confirm): 205
oos_folds (search dilimi): n=179 avg_r=0.0832 · n=111 avg_r=0.0742 · n=36 avg_r=-0.2221
oos_tail_risk:    var_r=8.877  cvar_r=10.993  n=348
```

### Terim terim: istenen vs. VAR olan

| terim | kapının istediği | canlıda VAR olan | erişilebilir mi |
|---|---|---|---|
| `thin` tabanı | her iki tarafta ≥ **21** arama-dilimi işlemi | **348** (16,6×) | ✅ **BAĞLAYICI DEĞİL** |
| `cand_oos/inc_oos` tanımlı | ≠ None | incumbent 0,2687 tanımlı | ✅ bağlayıcı değil |
| `majority` | ≥2 fold'da iki tarafta da `n>=3` kanıt, ve fold çoğunluğu | incumbent 3 fold'da 179/111/36 → hepsi ≥3 | ✅ **yapısal olarak açık** (adayın da 3'ünde görünmesi şartıyla) |
| `tail_ok` | VaR ve CVaR'ı +0,5R üstünde artırma | taban VaR 8,877R / CVaR 10,993R | ✅ açık (ama gerçek bir veto) |
| `dd_ok` | düşüşü +0,08 üstünde derinleştirme | ölçülüyor (dilim var) | ✅ açık |
| **`prob.passes`** | **P(ΔS>0) ≥ 0,995** (K=40) | **bu sistemde ÖLÇÜLEN en yüksek P = 0,799** | ❌ **BAĞLAYICI — ve gözlem aralığının DIŞINDA** |

### Bağlayıcı terimin sayısı: eşik, ölçülen dağılımın dışında

`docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md` §3'teki tam sayım (20 P-kapısı reddi, K=1,
`p_required` düz 0,80): en yüksek P = **0,799** (H00033), ikinci 0,709, kalan 18'in 14'ü P<0,50.

Canlı `state/events.jsonl` `arming_measured` defteri (bağımsız ikinci kanal, n=17 sayısal ölçüm):
en yüksek P = **0,5755**, hepsi `p_required: 0.8` altında `gate_rejected`.

Yani **canlı ısınmanın istediği 0,995, bu sistemde bugüne kadar ölçülmüş en yüksek kazanma
oranından 0,196 YUKARIDA.** Bu "hiçbiri geçemedi" değil, "çıta ölçüm aralığının dışında" hükmüdür.

---

## 4. ASIL BULGU — K'YI ÖNBELLEK BELİRLİYOR, VE ÖNBELLEK ISINDIKÇA KAPI KAPANIYOR

`reflect.py:2020-2035`: plan kapağı `probes[:max(budget*4, 40)]`; önbellekte HAZIR olan sonda
BEDAVA plana girer (bütçe yemez), taze olanlar `budget` kadar. Ama **`k_probes = total = len(planned)`**
— bedavalar dahil.

`hermes_runtime._warmup_sprint`in beyan edilmiş amacı zaten **"sonda önbelleğini ısıtmak"**tır
(fonksiyon docstring'i). Yani **ısınmanın BAŞARISI, bir sonraki koşumun kapısını mekanik olarak
sıkıyor.** Canlı defterden okunan `warmup_sprint` `evaluated` serisi bunu birebir gösteriyor —
her soğuk başlangıçtan sonra 10 → 20 → 30 → 40 tırmanışı, sonra 40'ta doyma:

```
2026-08-08T02:24:43  evaluated=10  cleared=1   best=exit.trail_atr_mult   (K=10 → p_req 0,980)
2026-08-08T06:45:11  evaluated=20  cleared=0   best=null                  (K=20 → p_req 0,990)
2026-08-08T18:36:33  evaluated=30  cleared=0                              (K=30 → p_req 0,9933)
2026-08-09T09:25:04  evaluated=40  cleared=0                              (K=40 → p_req 0,995)

2026-08-11T01:00:54  evaluated=10  cleared=1   best=exit.trail_atr_mult   (K=10 → p_req 0,980)
2026-08-11T05:20:42  evaluated=20  cleared=0
2026-08-11T09:37:06  evaluated=30  cleared=0
2026-08-11T13:46:48  evaluated=40  cleared=0
```

İki bağımsız gecede AYNI desen, AYNI aday (`exit.trail_atr_mult`).

**Neden bu K'ya atfedilebilir:** `planned` listesi sıralı önbellek-doldurmayla büyür — K=10'daki
ilk 10 sonda, K=20'de aynı sırayla plana yeniden girer (artık önbellekten bedava). Bootstrap
deterministiktir (`SEED_DEFAULT = 42`, `N_BOOT = 2000`), incumbent walk-forward önbellekte donmuş,
ve **her iki geçişte de aradaki pencere gece yarısı-sabah (piyasa kapalı)**: 02:24→06:45 arasındaki
tüm olayları saydım, `clear_wf_caches`/bar-tazeleme/`daily_cycle` YOK. Yani girdilerden değişen
tek DEKLARE edilmiş şey `k_probes`tir.
*(Kesinlik sınırı: `clear_wf_caches` sessiz de koşabilir; bunu doğrudan çürütemedim — bkz. §7.)*

**Bugünkü hâl:** `evaluated` 2026-08-17T15:14:58'de 40'a ulaştı ve **o tarihten beri 153 ısınma
koşumunun 149'u tam 40'ta** (diğer 4'ü 33/35/37/39). 153/153'ünde `cleared=0`, `best=null`.

### Bütçe merdiveni ayrıca ÖLÜ KİLİTLİ (yan bulgu, bu turda kapıyı GEVŞETEN yönde)

`state/warmup_scale.json`: `{"carpan": 1, "duvar": 1}`. Nasıl oldu:
```
2026-08-08T06:45:11 warmup_budget_scaled sebep=cleared=0  carpan 1→2  butce 10→20
2026-08-08T14:19:45 warmup_budget_scaled sebep=sure_tavani evaluated=0 kesildi=true
                    carpan 2→1, duvar=1
```
İkinci satırda koşum **SIFIR sonda** değerlendirmişti (`evaluated: 0`) — yani süre tavanını
sondalar değil, incumbent yürüyüşü yedi. `warmup_budget_feedback` bunu "bu genişlik bu makineye
sığmıyor" ÖLÇÜMÜ sayıp `duvar=1` çiviledi. `warmup_budget()` içinde
`carpan = min(carpan, duvar, WARMUP_SCALE_MAX)` ve büyüme dalı `onceki["carpan"] < min(duvar, 8)`
şartına bağlı → `1 < 1` = False. **Merdiven 2026-08-08'den beri kalıcı olarak ×1'de kilitli ve
duvarı temizleyen hiçbir yol yok.** (16 gündür `warmup_budget_scaled` olayı hiç basılmadı.)

---

## 5. TEŞHİS KANALI DEPLOY EDİLMİŞ AMA **KOŞMUYOR** — 7 GÜNLÜK BAYAT SÜREÇ

Bu, "neden görmüyoruz" sorusunun cevabı ve kendi başına bir bulgu.

```
$ ssh … 'systemctl show meridian-learn.service -p ExecMainStartTimestamp'
ExecMainStartTimestamp=Sun 2026-08-16 23:27:06 UTC          ← ısınmayı koşan süreç

$ ssh … 'stat -c "%y %n" meridian/hermes_runtime.py meridian/reflect.py'
2026-08-23 21:06:24 +0000 meridian/hermes_runtime.py        ← 7 GÜN DAHA YENİ
2026-08-23 21:06:24 +0000 meridian/reflect.py
```
Diskteki dosyalar depo HEAD'i ile **birebir aynı** (md5 karşılaştırıldı, 6/6 eşleşti). Diskteki
`hermes_runtime.py:218-220` `neden_dagilim=_nd` alanını basıyor ve `reflect.py:2088` iz satırına
`"why"` yazıyor (2026-08-21/23 düzeltmeleri, `tests/test_isinma_red_gerekcesi_v252.py` çivisi).

**Canlı defterde bu alanların İZİ YOK:**
```
262 warmup_sprint olayının 0 tanesi `neden_dagilim` taşıyor
en son olay: 2026-08-23T23:15:05 — dosya mtime'ından (21:06) SONRA, hâlâ alansız
```
(`meridian.service` 2026-08-23 22:03'te yeniden başlatıldı ve `.pyc`leri tazeledi;
`meridian-learn.service` başlatılmadı → bellekteki modül hâlâ 16 Ağustos derlemesi.)

**Sonuç: "cleared=0'ın nedeni" kanalı YAZILDI, DAĞITILDI, ama HİÇ KOŞMADI.** Operatörün
"öğrenme çalışmıyor" teşhisini yapamamasının doğrudan sebebi budur.

### İkinci teşhis boşluğu — sprint izi YAPISAL OLARAK BOŞ

`meridian/sprint_run.py:118`:
```python
"trace": [t for t in (s.get("trace") or []) if t.get("passes")][:6]
```
**`cleared == 0` olduğunda bu ifade TANIM GEREĞİ `[]` döner.** Canlı `sprint_status.json`da
`evaluated: 6, cleared: 0, "trace": []` — çelişki değil, tasarım. Reddin gerekçesi tam ihtiyaç
duyulduğu anda süzülüyor (`reflect.py:2081-2087`de 2026-08-21'de kapatılan kusurun aynısı,
sprint yazıcısında hâlâ açık). Sprint kum havuzunun kendi `events.jsonl`ında da o 6 sondaya ait
TEK bir `hermes_search_probe`/kapı olayı yok — yalnız `parallel_probes_prefilled n=6`.

---

## 6. HÜKÜM — "v1 YEREL-OPTİMAL" BEYANI GEÇERSİZDİR

Sprint `20260821-220656`nin notu:
> "hiçbir aday OOS kapısını geçemedi — bu veri diliminde v1 yerel-optimal"

Bu çıkarım **taşımadığı bir bilgiyi iddia ediyor**:

1. Sprint K=6 ile koştu → gerekli `p_req = 0,9667`. Bu sistemde bugüne kadar ölçülmüş **en yüksek**
   kazanma oranı 0,799'dur. Yani sprint, hiçbir adayın bugüne dek ulaşamadığı bir çıtayı
   6 adaya sordu ve "ulaşamadılar" dedi. Negatif sonuç, testin ayırt etme gücü sıfıra yakınken
   bilgi taşımaz.
2. Sprint reddin GEREKÇESİNİ kaydetmedi (`sprint_run.py:118` süzgeci). "Kapı ölçemedi" ile
   "aday kötü" ile "aday atıl düğme (`AYIRT EDİLEMEZ`)" bu kayıttan **ayırt edilemez** —
   `probgate` bu üç hükmü ayrı ayrı üretiyor ve üçü de çöpe gitti.
3. Canlı tarafta aynı kapının K=10'da (2026-08-08, 2026-08-11) aday TEMİZLEDİĞİ ölçülmüş durumda.
   "v1 yerel-optimal" olsaydı K=10'da da temizlenmemesi gerekirdi.

**Doğru okunuş:** `cleared: 0` bir edge ölçümü değil, bir **çoklu-test cezası ölçümüdür**.
Canlıda kapıyı bağlayan şey adayların kalitesi değil, o koşumda kaç sonda planlandığıdır — ve
o sayıyı hiç kimse seçmiyor; sonda önbelleğinin sıcaklığı seçiyor.

Aynı şey canlı ısınma için de geçerli: **2026-08-17'den beri hesaplanan 149 × `cleared: 0`,
tek bir bilgi taşımıyor** — aynı 40 sonda, aynı donmuş incumbent (son yansıma 2026-08-17T01:21),
aynı deterministik bootstrap, saatte bir yeniden soruluyor.

---

## 7. ÖLÇÜLEMEYENLER (UYDURMA YASAĞI)

1. **Canlı ısınmanın 40 sondasının GERÇEK P değerleri — ÖLÇÜLEMEDİ.** Neden: (a) ısınmanın
   `on_probe` geri-çağırması (`hermes_runtime._nabiz`) yalnız bekçi nabzı atıyor, sonda olayı
   BASMIYOR; (b) `neden_dagilim`/`why` kanalı deploy edilmiş ama koşan süreç 7 gün bayat (§5).
   Bu sayı, `meridian-learn` yeniden başlatılmadan ölçülemez.
2. **`exit.trail_atr_mult`in K=10'daki P değeri — ÖLÇÜLEMEDİ.** `cleared=1` kaydı P taşımıyor,
   ve o koşumun izi hiçbir yere yazılmadı. [0,98 , 0,99) aralığında olduğu ÇIKARIMI güçlüdür
   (K=10'da geçti, K=20'de geçmedi) ama **ölçülmedi**.
3. **`clear_wf_caches`in 08-08 02:24→06:45 arasında koşmadığı KESİN DEĞİL.** Olay defterinde bar
   tazeleme/`daily_cycle` izi yok ve pencere piyasa-kapalı; ama `clear_wf_caches` sessiz koşabilir.
   K atfı bu ölçüde şartlıdır.
4. **Yürürlükteki aşınma parmak izi ve `erosion_margin` — ÖLÇÜLEMEDİ.** `_gate_eval` parmak izini
   `backtest.balanced_fold_bounds(_its, …)`ten türetir; hangi satıra düştüğünü bulmak için o
   fonksiyonu koşturmam gerekirdi (ölçüm kodu → kart yok → koşmadım). `state/oos_erosion.json`da
   R1 penceresi için **6 ayrı parmak izi** var, sorgu sayıları **1 · 2 · 5 · 50 · 65 · 80**.
   `EROSION_QUERY_LIMIT = 20`. Yani aktif satır 50/65/80'lerden biriyse `erosion_margin = 0.01`
   YÜRÜRLÜKTEDİR ve `magnitude_ok`a **altıncı bir AND terimi** ekler
   (`cand_para > inc_para + 0,01 × 0,1908`). Bağlayıcı olup olmadığı ÖLÇÜLMEDİ.
5. **Bugünkü adayların `majority`/`tail_ok`/`dd_ok` hükümleri — ÖLÇÜLEMEDİ.** Incumbent tarafının
   yapısal olarak AÇIK olduğunu gösterdim (fold n=179/111/36); adayların bu üç vetoda ne yaptığı
   kayıtsız (aynı §5 boşluğu).
6. **`p_required_for`ın gerçek-Bonferroni'ye geçiş TARİHİ git ile doğrulanmadı** (git komutu
   yasaklı). Dolaylı kanıt: `docs/SISTEM-DENETIMI-2026-08-02.md:667` değişikliği 2026-08-02'de
   OLMUŞ olarak raporluyor, `docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md:201` formülü yürürlükte
   sayıyor. Buna göre 08-08/08-11 clearing'leri YENİ formül altındadır (K=10 → 0,980).

---

## 8. KANIT KOMUTLARI

```bash
# canlı ısınma serisi + tekdüzelik
ssh …@130.61.126.87 'cd /opt/meridian && python3 -c "…events.jsonl → warmup_sprint…"'
#  → 262 olay; 2026-08-16T23:27 sonrası 153 koşum: evaluated {40:149, 33:1, 35:1, 37:1, 39:1}
#    cleared {0:153} · best {None:153} · neden_dagilim taşıyan satır: 0
#  → tüm zamanlarda cleared>0 olan yalnız 4 koşum (07-20, 07-21, 08-08, 08-11)

# bayat süreç
ssh … 'systemctl show meridian-learn.service -p ExecMainStartTimestamp'
#  → 2026-08-16 23:27:06 UTC
ssh … 'stat -c "%y %n" meridian/hermes_runtime.py'
#  → 2026-08-23 21:06:24 +0000
ssh … 'ls -la meridian/__pycache__/hermes_runtime.cpython-312.pyc'
#  → 2026-08-23 22:06  (API restart'ının tazelediği .pyc; learn süreci görmüyor)

# kapının gerçek girdisi
ssh … 'cd /opt/meridian && python3 -c "…inc_cache.json…"'
#  → oos_score 0.2687 · len(_trades_search) 348 · len(_trades_confirm) 205
#    oos_folds n=179/111/36 · var_r 8.877 cvar_r 10.993

# meta kalibrasyon (extra_p)
ssh … 'cat state/gate_calibration.json'
#  → {"extra_p": 0.0, "n_measured": 1, "durum": "kurak"}

# bütçe merdiveni kilidi
ssh … 'cat state/warmup_scale.json'
#  → {"carpan": 1, "duvar": 1, "son": {"evaluated": 40, "cleared": 0, …}}

# sonda geçmişi (kapı geçiş oranı)
ssh … 'cd /opt/meridian && python3 -c "…hermes_search_probe…"'
#  → 999 sonda (2026-07-14 → 2026-08-21) · iki skoru da olan 387
#    aday>incumbent 141 (%36,4) · passes=True 6 (%0,6)
#    2026-08-01 SONRASI: 522 sonda, 0 passes

# arming defteri P dağılımı
#  → 17 sayısal ölçüm, max P = 0.5755, hepsi p_required 0.8 altında gate_rejected

# sprint izi
ssh … 'cat state/sprint_status.json'
#  → evaluated 6 · cleared 0 · "trace": []   (sprint_run.py:118 passes süzgeci)
```

## 9. İLGİLİ DOSYALAR (mutlak yol)

- `/Users/erdemozturk/AI-Trading/meridian/reflect.py` — `_gate_eval` (:400-660), `cleared` (:2093),
  `no_clearing_candidate` (:2160), K türetimi (:2020-2035, :2079)
- `/Users/erdemozturk/AI-Trading/meridian/probgate.py` — `p_required_for` (:348-367), `P_BASE` (:42)
- `/Users/erdemozturk/AI-Trading/meridian/oos_pipeline.py` — `evaluate_search` (:57), `SEARCH_FRACTION`
- `/Users/erdemozturk/AI-Trading/meridian/hermes_runtime.py` — `_warmup_sprint` (:131-224)
- `/Users/erdemozturk/AI-Trading/meridian/hermes.py` — `warmup_budget` (:1757), merdiven kilidi (:1791-1830)
- `/Users/erdemozturk/AI-Trading/meridian/sprint_run.py` — `_slim` iz süzgeci (:118)
- `/Users/erdemozturk/AI-Trading/docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md` — önceki P dağılımı
