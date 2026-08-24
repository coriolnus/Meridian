# TEŞHİS — ÖĞRENME KURAKLIĞI (2026-08-24)

Kapsam: `meridian-learn` ısınma sprinti + ship-yetkili yansıma araması + sprint 20260821-220656.
Bu tur **SALT OKUMA**: canlıda hiçbir şey değiştirilmedi, restart edilmedi, `state/` altına yazılmadı,
depoda kod değişmedi. Ölçüm zamanı: 2026-08-24T00:00–00:20Z.

## 0. DEVİR NOTU — GİRDİNİN KENDİSİNDE BİR BOŞLUK VAR (uydurulmadı, beyan ediliyor)

Bana "üç mercek" devredildi ama devir yükünde **yalnız A merceğinin gövdesi** var; JSON
`"olculemeyenler"` listesinin son maddesinin ortasında (`"\`p`) **kesilmiş**. B ve C merceklerinin
bulguları bana HİÇ ULAŞMADI. Bu belgede A merceğinin iddialarını yeniden ölçtüm/çürütmeye çalıştım
ve B/C'nin sorması gereken iki soruyu (arama kısırlığı · dürüst yerel-optimallik) **kendim ölçtüm**.
Aşağıda "A merceği" diye anılan satırlar devredilen bulgular, geri kalanı bu turun ölçümüdür.

---

## 1. TEK CÜMLELİK HÜKÜM

**Sistem öğrenmiyor, çünkü gemi-yetkili kapı `p_req = 1 − 0,20/K` ile K = *planlanan* sonda
sayısından türetilen bir güven düzeyi istiyor (canlı ısınmada K=40 → 0,995; son gerçek aramada K=8
→ 0,975) ve bu istek, sistemin bugüne kadar ÖLÇTÜĞÜ tüm güven değerlerinin (iki bağımsız kanalda 37
ölçüm, en yükseği 0,799) tamamının dışında kalıyor — dolayısıyla `cleared: 0` bir "edge yok"
ölçümü değil bir K ölçümüdür; üstelik arama yeni soru üretmeyi de bıraktığı için (son 50 ısınma
koşumunda SIFIR taze walk-forward, ship yolunda plan 40'tan 8'e düşmüş ve yalnız 2'si
değerlendirilmiş) aynı bilgisiz cevap saat başı yeniden hesaplanıyor.**

### ÇELİŞKİ (uzlaştırılmıyor, olduğu gibi bırakılıyor)

A merceği "kapı EŞİK tarafından erişilemez" diyor. Ama eşiğe en çok yaklaşmış tek ölçülmüş aday
(H00033, P=0,799, K=1'de gerekli 0,80 — kıl payı) **fold-çoğunluğunda 1/3 ile ayrıca düşüyor** ve
belgenin kendi cümlesi "eşik düşürülse bile ship etmezdi" diyor
(`docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md:294`). Yani elimizdeki TEK yakın vakada eşik
bağlayıcı terim DEĞİLDİ. "Eşik indirilse ship olurdu" iddiası bu veriyle **desteklenmiyor**;
desteklenen iddia daha zayıf ve daha kesin olanı: *bu eşik altında `cleared:0` hiçbir bilgi
taşımaz*. İkisi aynı şey değildir ve bu belge ikincisini savunur.

---

## 2. HANGİ SINIF

### **(a) YAPISAL ERİŞİLMEZLİK** — birincil ve bağlayıcı sınıf budur.

Gerekçe: canlı kapının istediği güven (0,975 / 0,995) bu sistemde ölçülmüş güven dağılımının
tamamının üstünde (n=37, maks 0,799). "Geçen yok" cümlesi bilgi taşımıyor.

### (b) ARAMA KISIRLIĞI da POZİTİF ölçüldü — ama türev

Ölçüm: son 50 ısınma koşumunda 0 taze walk-forward, 153/153 koşumda birebir aynı çıktı, hipotez
defteri 2026-08-21'den beri donuk, ship yolunda plan 8 sondaya çökmüş. Bunu (a)'nın **türevi**
sayıyorum çünkü zinciri ölçtüm: kapı geçirmiyor → incumbent 2026-08-17T01:21'den beri değişmiyor →
sonda anahtarları sabit → önbellek %100 isabet → yeni hesap yok → aynı 40 soru. Ve ters yönde:
plan 40 sonda sayıldığı için K=40, yani kısırlık kapıyı ayrıca SIKIYOR. Kilitli bir döngü, ama
kilidin dili (a) tarafında.

### (c) GERÇEKTEN YEREL-OPTİMAL — ÇÜRÜTÜLDÜ, kusur uydurulmuş değil

Ship-yetkili son aramada (2026-08-21) değerlendirilen 2 adaydan **biri incumbent'ı OOS'ta yendi**:
`entry.w_turnover → 0,15`, candidate_oos **0,2823** vs incumbent_oos **0,2687** (+0,0136, %+5,1) —
ve `passes=False`. Sonda defterinde iki skoru da olan 387 sondanın 141'inde (%36,4) aday incumbent'ı
geçiyor (A merceği ölçümü). "v1 yerel-optimal" hükmü bu veriyle **verilemez**; sprint
20260821-220656'nın `note` alanındaki "bu veri diliminde v1 yerel-optimal" cümlesi
kanıtlanmamış bir hükümdür.

---

## 3. KANIT ZİNCİRİ (komut + çıktı)

### 3.1 Eşik formülü ve K'nın kaynağı

```
$ sed -n '345,367p' meridian/probgate.py
    def p_required_for(k_probes: int, p_base: float = P_BASE) -> float:
        ...
        k = max(1, int(k_probes))
        alpha_family = max(1e-6, (1.0 - p_base) - _meta_extra_p())
        return min(P_CEIL, 1.0 - alpha_family / k)
$ grep -n "^P_BASE" meridian/probgate.py
42:P_BASE = 0.80
```
⇒ K=1→0,800 · K=2→0,900 · K=6→0,9667 · K=8→**0,975** · K=40→**0,995**

```
$ sed -n '2078' meridian/reflect.py
        passes, gate, _why = _gate_eval(inc, cand, k_probes=total, ...)   # FULL gate + K-aday cezası
$ sed -n '2020,2032p' meridian/reflect.py
    for sig in probes[:max(budget * 4, 40)]:
        ...
        cached = _probe_key(...) in _PROBE_CACHE
        if cached:            planned.append(sig)
        elif fresh_planned < budget:  planned.append(sig); fresh_planned += 1
    probes = planned
$ grep -n "total = len(probes)" meridian/reflect.py
2049:    total = len(probes)
```
⇒ **K = planlanan sonda sayısı**, değerlendirilen değil. Önbellekten bedava gelen sondalar da K'ya
sayılır (kodun kendi beyanı, reflect.py:2016-2019). Duvar-saati yüzünden ATLANAN taze sondalar da
K'da kalır (aynı yorum bloğu: "atlanan taze sonda değerlendirilmez ama K'da sayılmaya devam eder").

```
$ ssh … 'cat /opt/meridian/state/gate_calibration.json'
{"extra_p": 0.0, "median_ratio": -0.6138, "n_measured": 1, "durum": "kurak",
 "durum_beyan": "KURAK — 1 çift var, eşik 5 … extra_p=0,0 'düzeltme gerekmedi' DEĞİL 'henüz ölçülemedi' demektir"}
```
⇒ meta-ofset 0 → eşik saf `1 − 0,20/K`.

### 3.2 Ölçülmüş güven dağılımı — iki bağımsız kanal, hiçbiri 0,80'i geçmiyor

```
$ ssh … python3 (events.jsonl → arming_measured)
toplam arming_measured: 106 status: {'gate_rejected': 47, 'gate_undefined': 59}
sayisal search_p tasiyan: 17
en yuksek 5: [(0.5755,'2026-08-10T21:37:08',0.8,'2/3','momentum_burst'),
              (0.5755,'2026-08-04T21:27:46',0.8,'2/3','momentum_burst'),
              (0.5225,'2026-08-05T22:09:14',0.8,'1/3','momentum_burst'),
              (0.5225,'2026-08-04T01:13:21',0.8,'1/3','momentum_burst'),
              (0.5135,'2026-07-29T22:37:48',0.8,'2/3','momentum_burst')]
p>=0.90: 0   p>=0.975: 0   p>=0.995: 0
fold_wins dagilimi: {'2/3': 9, '0/0': 89, '1/3': 6, '0/3': 1, '0/1': 1}
```

```
$ grep -n "0,799" docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md
211:| **0,799** | H00033 | `entry.w_rs` | +0,0643 | **−0,001 (kıl payı)** |
233:**Dağılım hükmü:** eşiğe kıl payı yaklaşan **tek** aday var (H00033, 0,799). İkinci en yakın 0,091
294:| H00033 | … | **1/3** | P'ye kıl payı yaklaştı (0,799) ama **fold-çoğunluğu 1/3** … Eşik düşürülse bile ship etmezdi. |
```

⇒ İki kanalda toplam **37 sayısal P ölçümü**; maksimum **0,799**; canlı ısınmanın istediği 0,995
bu maksimumun **0,196 üstünde**, ship yolunun istediği 0,975 ise **0,176 üstünde**.

### 3.3 Isınma kanalı: 153 koşum, tek bir farklı cevap yok

```
$ ssh … python3 (events.jsonl → warmup_sprint)
toplam warmup_sprint: 262
surec baslangicindan beri: 153
neden_dagilim tasiyan: 0
evaluated: Counter({40: 149, 33: 1, 35: 1, 37: 1, 39: 1})
cleared: Counter({0: 153})
aralik medyan/min/max sn: 3679.0 3678.0 10575.0
ilk/son: 2026-08-17T04:16:53+00:00 2026-08-23T23:15:05+00:00
```
```
$ ssh … 'cat /opt/meridian/state/warmup_scale.json'
{"carpan": 1, "duvar": 1, "son": {"evaluated": 40, "cleared": 0, "kesildi": false, "at": "2026-08-23T23:15:05+00:00"}}
```
⇒ budget 10 × çarpan 1 → `sonda_tavani = max(10·4, 40) = 40` → **K=40 → p_req 0,995**, saat başı.
Merdiven ölü kilitli: `carpan=1, duvar=1` ve büyüme dalı `carpan < min(duvar,8)` yani `1 < 1` = False
(`meridian/hermes.py:1811`) → hiçbir yol duvarı temizlemiyor (A merceği bulgusu, doğrulandı).

### 3.4 Teşhis kanalı dağıtıldı ama KOŞMUYOR — 7 günlük bayat süreç (doğrulandı)

```
$ ssh … 'systemctl show meridian-learn.service -p ExecMainStartTimestamp -p ActiveState -p NRestarts'
ExecMainStartTimestamp=Sun 2026-08-16 23:27:06 UTC
ActiveState=active
NRestarts=0
$ ssh … 'grep -h "warmup_sprint" state/events.jsonl | tail -1'
{"ts": "2026-08-23T23:15:05+00:00", … "evaluated": 40, "cleared": 0, "best": null, "kesildi": false,
 "tavan_dk": 300.0, "kalan_sonda": null, "butce": 10, "butce_carpani": 1, "k_max": 2}
```
Diskteki kod bu olaya `neden_dagilim=` alanını basmak ZORUNDA:
```
$ sed -n '218,221p' meridian/hermes_runtime.py
        _nd = _red_neden_dagilimi(res.get("trace") or [])
        obs.log("warmup_sprint", evaluated=res.get("evaluated"), cleared=res.get("cleared"),
                neden_dagilim=_nd,
```
⇒ 153 olayın **hiçbirinde** `neden_dagilim` yok. Koşan süreç 2026-08-16 derlemesini tutuyor;
red gerekçesini basan kod (2026-08-21/23) diskte, **süreçte değil**. Teşhisi imkânsız kılan boşluk
budur ve **bu turda kapatılmadı** (restart yasak — operatör kararı).

### 3.5 (b) ARAMA KISIRLIĞI — doğrudan ölçüm

```
$ ssh … 'stat -c "%y %s %n" state/probe_cache.json state/hypotheses.jsonl state/inc_cache.json'
2026-08-21 20:45:32 506203 probe_cache.json
2026-08-21 18:02:05 128262 hypotheses.jsonl      (60 satır)
2026-08-21 22:39:32 531127 inc_cache.json
$ ssh … python3 (olay sayımı)
999 hermes_search_probe        son: 2026-08-21T20:45:34+00:00
94  parallel_probes_prefilled  son: 2026-08-12T07:40:47+00:00
1   search_sure_tavani_kesildi son: 2026-08-08T14:19:45+00:00
probe_cache son yazimindan beri warmup kosumu: 50
```
`_probe_disk_save()` her taze sonda hesabında çağrılır (reflect.py:1613, :1770, :1775) →
**probe_cache.json 2026-08-21 20:45'ten beri yazılmadı ⇒ o tarihten beri SIFIR taze walk-forward
hesaplandı.** `parallel_probes_prefilled` (yalnız `jobs` boş değilse basılır) 2026-08-12'den beri
hiç basılmadı ⇒ 12 gündür ısınmanın planladığı 40 sondanın **tamamı önbellekte hazır**. Isınma,
beyan edilmiş görevini ("önbelleği ısıt") 12 gün önce bitirmiş; o günden beri yaptığı tek iş
**bilinen 40 cevabı saat başı yeniden kapıya sokmak**.

### 3.6 Ship-yetkili kanal: plan çökmüş, 2 aday ölçülüyor, K 8 sayılıyor

```
$ ssh … python3 (hermes_search_start / hermes_search_done, son 14 satır)
2026-08-21T18:02:05 START budget= 8 k_max= 3 regime= global formul= operatör override — türetim devre dışı
2026-08-21T20:45:37 DONE  evaluated= 2 cleared= 0 status= no_clearing_candidate
… son 8 DONE evaluated/cleared:
[('2026-08-12T03:18:11',8,0), ('2026-08-12T13:10:53',10,0), ('2026-08-13T00:51:22',2,0),
 ('2026-08-13T04:08:19',4,0), ('2026-08-14T06:42:27',4,0), ('2026-08-14T10:35:10',2,0),
 ('2026-08-17T01:21:35',2,0), ('2026-08-21T20:45:37',2,0)]
toplam: hermes_search_start 179 · hermes_search_done 60
```
```
$ ssh … python3 (hermes_search_probe, son 3 satır)
2026-08-21T19:14:01 i=0 total=8 var=None  … inc_oos=0.2687                (plan yayını)
2026-08-21T19:57:21 i=1 total=8 var=entry.w_turnover new=0.15 cand_oos=0.2823 inc_oos=0.2687 passes=False
2026-08-21T20:45:34 i=2 total=8 var=exit.breakeven_r  new=2.5  cand_oos=0.2293 inc_oos=0.2687 passes=False
```
Üç ölçüm birden:
1. **K=8 (`total`) ama evaluated=2** → 6 sonda `MERIDIAN_SEARCH_MAX_MIN=60` yüzünden atlandı, hepsi
   K'da sayıldı ⇒ sistem **2 soru sordu, 8 sorunun çoklu-test cezasını ödedi** (0,90 yerine 0,975).
2. **Bir aday incumbent'ı yendi** (0,2823 > 0,2687) ve reddedildi ⇒ (c) sınıfı çürük.
3. Taze bir walk-forward **~43-48 dakika** sürüyor (19:14→19:57→20:45) ⇒ 60 dakikalık tavan yapısal
   olarak en fazla ~2 taze sondaya izin veriyor, plan ne olursa olsun.

Ayrıca: **179 START'a karşılık 60 DONE** — aramaların %66,5'i tamamlanma kaydı bırakmamış. Sebebi
bu turda ölçülmedi (§4).

### 3.7 Kapı beş terimli — hangi terimin bağladığı canlıda kayıtlı DEĞİL

```
$ grep -n "passes = " meridian/reflect.py
651:    passes = bool(magnitude_ok and majority and tail_ok and dd_ok and dd_mtm_ok)
$ grep -n "majority = \|tail_ok = \|dd_ok = \|dd_mtm_ok = " meridian/reflect.py
455:    majority = True if fold_total == 0 else (fold_wins >= (fold_total + 1) // 2 …
471/480: tail_ok …    511: dd_ok …    538: dd_mtm_ok  (bayrak kapalı → NO-OP)
$ sed -n '118p' meridian/sprint_run.py
            "trace": [t for t in (s.get("trace") or []) if t.get("passes")][:6]
$ ssh … 'cat state/sprint_status.json' (search bloğu)
{"status":"no_clearing_candidate","evaluated":6,"cleared":0,"incumbent_oos":0.409,"best":null,"trace":[]}
```
⇒ Sprint tarafında `cleared==0` iken iz **tanım gereği boş** — reddin gerekçesi yapısal olarak
siliniyor. Isınma tarafında gerekçe kodu var ama süreç bayat (§3.4). Ship tarafında
`hermes_search_probe` `why` alanı taşımıyor. **Üç kanalın üçünde de "hangi terim bağladı" sorusu
cevapsız.**

### 3.8 PROMOTE_* sabitleri bu yolda kullanılmıyor (A merceği doğrulandı)

```
$ grep -rn "PROMOTE_MIN_PAIRS|PROMOTE_MIN_BUCKET|PROMOTE_R_GAP|PROMOTE_MIN_N" --include="*.py" . | grep -v /tests/
meridian/analytics.py:1125-1127  (gerçek ad: LLM_PROMOTE_*, kullanım :1152,:1171-1173,:1214-1215 — LLM görüş terfisi)
meridian/shadow_model.py:295     (kullanım :322-333,:459 — gölge model terfisi)
```
`reflect.py`de sıfır eşleşme. Brief'teki "kapı sabitleri" satırı **yanlış hedefi işaret ediyordu**;
öğrenme kapısının sabiti `probgate.P_BASE=0.80` + K'dır. WP3'ün `PROMOTE_MIN_N=30` bulgusu geçerli
ama **başka bir kapıya** (gölge model) aittir.

---

## 4. ÖLÇÜLEMEYENLER (ve neden)

1. **Bugünkü 40 sondanın gerçek P(ΔS>0) değerleri — ÖLÇÜLEMEDİ.** Isınmanın `on_probe` geri-çağırması
   (`hermes_runtime._nabiz`) yalnız bekçi nabzı atıyor, sonda olayı basmıyor; gerekçe kanalı
   (`neden_dagilim`) diskte var ama süreç 7 gün bayat (§3.4). Bu sayı ya `meridian-learn` restart
   edilerek ya da çevrimdışı bir ölçüm kartıyla elde edilir. **Bu tur ikisini de yapmadı** (restart
   = canlı değişiklik, yasak; ölçüm kodu = ön-kayıt kartı yok, yasak).
2. **08-21'de incumbent'ı yenen `entry.w_turnover 0,15` adayının hangi terimden düştüğü — ÖLÇÜLEMEDİ.**
   `hermes_search_probe` `why`/`fold_wins`/`p` taşımıyor; yalnız `passes=False` var. P mi (0,975
   isteniyordu), fold-çoğunluğu mu, kuyruk mu bağladı — ayırt edilemiyor. Teşhisin **en pahalı**
   boşluğu bu: sınıf (a) ile "kapı doğru çalıştı, aday zayıftı" hükmünü ayıran tek sayı.
3. **179 START / 60 DONE farkı (119 tamamlanmamış arama) — ÖLÇÜLEMEDİ.** Süreç yeniden başlatma,
   istisna ya da olay adı değişikliği olabilir; ayırt etmek için süreç ömrü × arama penceresi
   kesişimini kurmak gerekirdi, bu turun kapsamı dışında.
4. **Isınmanın CPU payı — ÖLÇÜLEMEDİ (yalnız üst sınır var).** `CPUUsageNSec` birim geneli için
   ölçülüyor; ısınma ile diğer görevleri ayıran bir sayaç yok (§6'da üst sınır olarak verildi).
5. **Parasal maliyet — ÖLÇÜLEMEDİ.** Bu oturumun Oracle faturalama verisine erişimi yok; A1 kapasite
   kullanımının para karşılığı hakkında sayı yazmak uydurma olurdu.
6. **`erosion_margin`in bugün yürürlükte olup olmadığı — ÖLÇÜLEMEDİ** (A merceğinden devralındı,
   çürütülmedi): `state/oos_erosion.json` R1 penceresi için 6 parmak izi taşıyor (sorgu sayıları
   1·2·5·50·65·80), `EROSION_QUERY_LIMIT=20`. Aktif satırı bulmak `balanced_fold_bounds` koşturmayı
   gerektirir → ölçüm kodu → kart yok → koşulmadı. Aktifse `magnitude_ok`a altıncı bir AND terimi
   ekler.
7. **"Eşik indirilseydi ship olurdu" — ÖLÇÜLEMEDİ ve mevcut tek kanıt AKSİNİ söylüyor** (H00033,
   fold 1/3). §1'deki çelişki.
8. **Sprint 20260821-220656'nın 6 sondasının kimliği — ÖLÇÜLEMEDİ.** Kum havuzu `events.jsonl`ında
   o 6 sondaya ait kapı/probe olayı yok (yalnız `parallel_probes_prefilled n=6`), `trace` süzgeçle
   boşaltılmış (§3.7).

---

## 5. ÖNERİLEN SONRAKİ ADIM (değişiklik DEĞİL — kart + dondurma)

Öğrenme davranışını değiştirmek strateji kimliğini değiştirir; taban yeniden dondurulmadan
`P_BASE`, K tanımı, `sonda_tavani` ya da duvar mantığı **elleçlenmemelidir**. Bu yüzden öneri
üç kalemdir ve üçü de "ölç/dondur" biçimindedir:

**S1 — OPERATÖR KARARI (kod değil, ops).** `meridian-learn` bakım penceresinde yeniden başlatılsın
ki 2026-08-21/23'te dağıtılmış `neden_dagilim`/`why` teşhis kanalı fiilen koşsun. Bu bir davranış
değişikliği değil, **zaten onaylanmış kodun süreçte yürürlüğe girmesi**; ama canlı birime dokunduğu
için bu ajanın yetkisi dışında. Kazanç: bir saat sonra "hangi terim bağladı" sorusu defterden
okunabilir hâle gelir ve §4.1/§4.2 boşlukları ölçüm koşmadan kapanır.

**S2 — ÖN-KAYIT KARTI (taslak ekte).** `KART-TASLAGI.yaml` — canlıya dokunmadan, DONMUŞ veri
diliminde bugünkü 40 sondanın P(ΔS>0) dağılımını ve beş kapı teriminin her birinin veto sayısını
ölçer. Hüküm eşikleri **kart yazılırken** donar (H1–H4, aşağıda). Kart YALNIZ KANIT üretir, hiçbir
eşiği değiştirmez (EDG-2026-024 precedent'i).

**S3 — ÖNCEDEN DONDURULACAKLAR (kart koşmadan önce, Rol-1 tarafından yazıya geçirilsin).**
- `probgate.P_BASE = 0.80` bu ölçüm boyunca **DEĞİŞMEZ**.
- `p_req = 1 − (0,20 − extra_p)/K` formülü **DEĞİŞMEZ**; `extra_p = 0,0` çivilenir (canlı hâli).
- K ızgarası ölçümden ÖNCE ilan edilir: **K ∈ {1, 2, 8, 40}** — ve bu dört değer kart K-kaydında
  ÇARPILARAK sayılır.
- Hüküm eşikleri ölçümden ÖNCE: **H1** maks P < 0,90 ⇒ *yapısal erişilmezlik doğrulandı, `cleared:0`
  bilgi taşımıyor*. **H2** ≥1 sonda P ≥ 0,90 VE aynı sonda majority+tail+dd'yi geçiyor ⇒ *bağlayıcı
  terim K tanımıdır (planlanan vs değerlendirilen)*. **H3** en yüksek P'li sondalar majority/tail/dd'den
  düşüyor ⇒ *eşik bağlayıcı DEĞİL; indirmek hiçbir şeyi değiştirmez (H00033 tekrarı)*. **H4** tüm
  sondalarda cand_oos ≤ inc_oos VE maks P < 0,50 ⇒ *(c) sınıfı doğrulanır, v1 dürüstçe yerel-optimal*.
- Kill-list dokunulmazdır; ölçüm ajanı karta dokunmaz; hükmü Rol-1 işler.

**S4 — ÖNERİ HAVUZUNA (ROADMAP §2, bu tur uygulanmaz, karar Rol-1'de).**
(i) `sprint_run.py:118` iz süzgeci `cleared==0` iken gerekçeyi siliyor — okuyucusuz yazımın tersi,
YASA 6 ihlali adayı. (ii) `warmup_scale` duvar kilidi (`carpan=1, duvar=1`, temizleyen yol yok).
(iii) 60 dakikalık `MERIDIAN_SEARCH_MAX_MIN` ile ~45 dakikalık walk-forward yan yana durduğunda
plan ne olursa olsun en fazla ~2 taze sonda ölçülebiliyor, ama K planı sayıyor.

---

## 6. MALİYET — (b) doğruysa saat başına ne yanıyor

(b) bu turda **pozitif ölçüldü** (§3.5). Saatlik fatura:

| Kalem | Saat başına | Günlük (24 koşum) | 2026-08-17T04:16 → 08-23T23:15 (153 koşum) |
|---|---|---|---|
| Isınma koşumu | 1 | 24 | 153 |
| Kapı değerlendirmesi | 40 | 960 | **6.104** (149×40 + 33+35+37+39) |
| Blok-bootstrap replikasyonu (n_boot=2000) | 80.000 | 1.920.000 | **12.208.000** |
| TAZE walk-forward (yeni bilgi) | **0** | **0** | **0** (son 50 koşum; §3.5) |
| Farklı sonuç üretilen koşum | 0 | 0 | **0/153** |
| Duvar-saati | ~79 sn | ~31,6 dk | ~3,36 saat |

**~79 sn/koşum türetimi (ölçüm + çıkarım):** ardışık `warmup_sprint` olayları arasındaki medyan
aralık **3679 sn** (min 3678), uyku ise `HERMES_POLL_SECONDS=300 × WARMUP_EVERY_POLLS=12 = 3600 sn`
(`/etc/systemd/system/meridian-learn.service:39`, `hermes_runtime.py:32`). Fark = koşum süresi.
Bu bir **çıkarımdır**, doğrudan ölçüm değil (koşum süresi hiçbir olaya yazılmıyor).

**CPU üst sınırı (kesin pay ÖLÇÜLEMEDİ):** `CPUUsageNSec=80.519.387.200.000` ns = **80.519 CPU-sn
= 22,37 CPU-saat**, birimin 2026-08-16 23:27:06'dan bu yana (~7,03 gün) TOPLAM tüketimi; makine
4 çekirdek (`nproc`=4), yani ortalama bir çekirdeğin %13,3'ü. Isınmanın payı ayrı sayaçla ölçülmüyor;
üst sınır, 79 sn boyunca 4 çekirdeğin tamamı varsayımıyla 316 CPU-sn/koşum → 153 koşumda ≤48.348
CPU-sn, yani birim toplamının ≤%60'ı. **Bu bir sınırdır, ölçüm değildir.**

**Asıl maliyet CPU değil:** saat başına 40 kapı hükmü üretiliyor ve 153 koşumdur **sıfır bit** bilgi
taşıyor (aynı girdi, deterministik bootstrap `seed=42`, donmuş incumbent, %100 önbellek isabeti).
Buna karşılık ship-yetkili kanal aynı 7 günde **1 kez** koştu (2026-08-21) ve orada gerçekten yeni
iki ölçüm yapıldı — biri incumbent'ı yendi. Yani bütçe, bilgi üretmeyen kanalda saat başı,
bilgi üreten kanalda haftada bir harcanıyor. Oran: **168 ısınma penceresi : 1 gerçek arama.**

---

*Ölçen: ölçüm ajanı (salt okuma). Hükmü Rol-1 işler; bu belge karta ve kill-list'e dokunmaz.*
