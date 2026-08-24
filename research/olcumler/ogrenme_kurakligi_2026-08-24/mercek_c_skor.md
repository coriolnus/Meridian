# MERCEK C · SKORLAMA — "v1 YEREL-OPTİMAL" İDDİASI DOĞRU MU?

Tarih: 2026-08-24 · Kapsam: SALT OKUMA (canlıya yazım yok, git yok, kod değişikliği yok)
Ölçüm konusu: `meridian-sprint@20260821-220656` koşumu · `status: "no_clearing_candidate"` ·
`note: "hiçbir aday OOS kapısını geçemedi — bu veri diliminde v1 yerel-optimal"`

---

## HÜKÜM (özet)

**"v1 yerel-optimal" iddiası YAZILDIĞI HÂLİYLE YANLIŞ — ve zaten bir ÖLÇÜM DEĞİL, SABİT BİR DİZGEDİR.**

1. Cümle `meridian/sprint_run.py:207`de **hardcoded string literal**dir. Kapının ürettiği ret
   gerekçesi (`_why`) o satıra HİÇ ULAŞMAZ. Arama ne söylerse söylesin, kapıyı geçen aday yoksa
   aynı cümle yazılır.
2. Ölçüldü: 6 sondanın **2'si** raporlanan `oos_score`ta incumbent'ı GEÇTİ, **2'si** kapının
   gerçekten karar verdiği `para` (PARA-v3 `ret_c_v3`) skorunda incumbent'ı GEÇTİ. Yani arama
   "daha iyi nokta bulamadı" DEĞİL; **buldu, kapı istatistiksel istikrar kanıtı yetmediği için
   reddetti**. Bu iki cümle aynı şey değildir ve ikincisi hiçbir kalıcı kayıtta yazmaz.
3. Alt-hipotez (a) — "skor hesaplanmıyor/bozuk" — **ÇÜRÜDÜ**: altı sondanın altısının da tam
   walk-forward sonucu diskte duruyor, skorlar dolu ve makul.
4. Alt-hipotez (b) — "karşılaştırma yanlış tarafa bakıyor" — **KISMEN DOĞRULANDI**: operatörün
   gördüğü sayı (`oos_score`, bileşik) ile kapının hüküm verdiği sayı (`para`) FARKLI sıralama
   üretiyor, ve oturum temsilcisi/`best` seçimi YANLIŞ OLANIYLA (bileşik) yapılıyor.

---

## Ö1 · `incumbent_oos` ile aday skorları AYNI İŞLEVLE, AYNI DİLİMDE Mİ HESAPLANIYOR?

**EVET — elmayla elma. Bu dalda kusur YOK.**

| | incumbent | aday |
|---|---|---|
| çağrı | `reflect._wf_cached` (`reflect.py:298`) | `reflect._probe_wf` (`reflect.py:1596`) |
| altındaki hesap | `backtest.walk_forward(params, bars, index, goal, w[0..3], oos_folds=w[4], embargo_days=w[5], ...)` | AYNI çağrı, aynı `w` |
| pencere | `sprint.SELECT_WINDOWS` (`sprint.py:49`) | AYNI (`w` tek değişken olarak taşınıyor) |
| `eval_regime` | `regime` (=None) | `_eval_regime_of(var)` (global düğmede None) |
| önbellek | `inc_cache.json` | `probe_cache.json` |
| bar revizyonu | `wf_cache_rev.json` rev **1787344310** | AYNI rev (ölçüldü, aşağıda) |

Ampirik teyit (varsayım değil): `entry.min_rvol=0.2` sondası incumbent ile **bit-bit aynı**
walk-forward üretti — `oos_score 0.409`, `n 297`, `total_return 0.2103`, `max_dd 0.0742`,
`sharpe 2.057`, `n_trades_search 187`. İki taraf farklı dilim görseydi bu eşitlik imkânsızdı.

Ortak dilim: `oos_split = {search 2023-01-11 → 2024-01-18 (372 gün), confirm 2024-01-18 → 2024-06-30}`.

---

## Ö2 · ADAYLARIN SKOR DAĞILIMI (asıl bulgu)

`search.trace` boş olduğu için dağılım durum dosyasından okunamıyor. Ham veriyi kum havuzunun
walk-forward önbelleğinden çıkardım (`state/sprint/20260821-220656/state/probe_cache.json`,
7 girdi — 6'sı SELECT penceresinde, 1'i canlı/ısınma penceresinde).

### Ölçülen tablo (incumbent: `oos_score 0.409` · `para 0.3681` · `n_search 187`)

| # | sonda | `oos_score` | Δoos | `para` (KARAR) | Δpara | `n_search` | **P(ΔS>0)** | hüküm |
|---|---|---|---|---|---|---|---|---|
| 1 | `entry.min_score` 60→**58** | **0.4247** | **+0.0157** | **0.4292** | **+0.0611 (+%16,6)** | 186 | **0.7555** | RET |
| 2 | `entry.min_volume_ratio` 1.5→**1.7** | **0.4108** | **+0.0018** | 0.3270 | −0.0411 (−%11,2) | 179 | 0.3260 | RET |
| 3 | `entry.min_rvol` →**0.2** | 0.4090 | ±0.0000 | 0.3681 | ±0.0000 | 187 | 0.0000 | RET (**ATIL DÜĞME**) |
| 4 | `entry.min_score` 60→**62** | 0.3752 | −0.0338 | 0.2831 | −0.0850 | 187 | 0.0700 | RET |
| 5 | `entry.min_volume_ratio` 1.5→**1.3** | 0.3526 | −0.0564 | **0.3955** | **+0.0274 (+%7,4)** | 207 | 0.5410 | RET |
| 6 | `entry.max_ext_atr` 0.0→**2.0** | 0.3412 | −0.0678 | 0.2855 | −0.0826 | 163 | 0.3200 | RET |

Gerekli eşik: **`p_required(K=6) = 1 − 0,20/6 = 0,96667`** (`probgate.p_required_for`,
`P_BASE=0.80`, `gate_calibration.extra_p = 0.0` — canlıda ve kum havuzunda ölçüldü).

### Cevap: "hepsi 0.409'un çok altında mı, hemen altında mı, skor hiç yok mu?"

**Hiçbiri değil — İKİSİ ÜSTÜNDE.** Skorlar var, dolu ve dağınık (0.3412 → 0.4247).
En iyi aday incumbent'ı **hem** bileşik skorda (+%3,8) **hem** karar skorunda (+%16,6) geçiyor,
düşüşü de daha sığ (`candidate_dd 0.0452` vs `incumbent_dd 0.0521`), fold çoğunluğunu
kazanıyor (**2/3**), kuyruk vetosunu geçiyor (`tail_ok true`), M2M düşüş bacağını geçiyor
(`dd_mtm_durum "gecti"`) — ve **yine de `passes: false`**.

Reddeden tek bacak: **olasılıksal büyüklük yasası.** Blok-bootstrap (2000 replikasyon,
`seed=42`, blok boyu medyan tutuş) replikasyonların yalnız **%75,6**'sında adayı önde buluyor.

### Bu K-cezasının (kazananın laneti) suçu MU? HAYIR — ölçüldü.

`p_required(K=1) = 0.80`. En iyi adayın P'si **0.7555 < 0.80**. Yani **tek aday denenmiş olsaydı
bile, hiç K cezası olmasaydı bile bu aday geçemezdi.** K=6 cezası (0.80 → 0.9667) bu koşumda
bağlayıcı kısıt DEĞİLDİR. "Kapı K yüzünden erişilemez" hipotezi bu koşum için ÇÜRÜR.

### AMA: raporlanan sıralama ile KARAR VEREN sıralama ÇAKIŞMIYOR (alt-hipotez b)

`oos_score` = bileşik (`0,5·ret + 0,3·dd + 0,2·sharpe`). Kapı ise `shadowlaw.ret_c_v3` yani
**yalnız para terimi** üzerinde hüküm veriyor (`probgate._score_pair`, PARA-v3 ters gölgeleme).
İki sıralama ölçülen biçimde ayrışıyor:

* `entry.min_volume_ratio=1.7` — raporlanan sırada **2.**, incumbent'ın ÜSTÜNDE (0.4108 > 0.409);
  karar skorunda **PARA KAYBETTİRİYOR** (0.327 < 0.3681, −%11,2).
* `entry.min_volume_ratio=1.3` — raporlanan sırada **5.**, incumbent'ın 0.056 ALTINDA;
  karar skorunda **2. EN İYİ ADAY** (0.3955 > 0.3681, +%7,4).

Sonuç: panoya/log'a basılan `incumbent_oos: 0.409` ve `candidate_oos` sayıları, hükmün
dayandığı sayılar DEĞİLDİR. Daha ağırı, kod da bu karışıklığın içinde:

* `reflect.py:2081-2083` — oturum temsilcisi `rep_cand` **`c_oos` (bileşik) ile** seçiliyor.
  O temsilci hem aşınma sayacına hem PBO/DSR popülasyonuna hem doğrulama defterine giren TEK
  resmî kayıttır. Bu koşumda tesadüfen doğru adayı seçti (min_score=58 her iki ölçekte de 1.);
  yapısal olarak seçmeyebilir.
* `reflect.py:2114-2118` — kapıyı geçenler arasından `best` de yine `candidate_oos` ile seçiliyor.

---

## Ö3 · `search.trace` NEDEN BOŞ? — KÖK NEDEN BULUNDU

**Kayıp yazımda değil, SÜZGEÇTE. Ve süzgeç ikili.**

```
meridian/sprint_run.py:110  def _slim(res: dict) -> dict:
meridian/sprint_run.py:117      "trace": [t for t in (s.get("trace") or []) if t.get("passes")][:6]
```

`_slim` yalnız **`passes=True`** satırlarını saklıyor. `cleared == 0` olan HER koşumda
`trace` TANIM GEREĞİ `[]` olur. "İz yazılmadı" değil — **iz yazıldı, sonra ret satırları atıldı.**

İkinci süzgeç, ilkini onarsanız bile önü kesiyor:

```
meridian/web/app.js:10986  const stepLog = ((search.trace) || []).filter(t => t.passes).map(...)
```

`_slim`in yazdığı yerler: `sprint_status.json` (`sprint_run.py:210,215,224,229`) ve
`sprint_runs.jsonl` (`:204`). Canlıda ikisini de doğruladım:

* `/opt/meridian/state/sprint_status.json` → `"trace": []`
* `/opt/meridian/state/sprint/20260821-220656/state/sprint_runs.jsonl` → `"trace": []`

### Bu, 2026-08-21'de yapılan düzeltmeyi ETKİSİZ BIRAKIYOR (YASA 6 ihlali, ikinci kez)

`reflect.py:2100-2106` yorumu aynen şunu diyor: `_why` üretilip ATILIYORDU, bu YASA 6'nın tam
tersidir, canlı belirti `warmup_sprint evaluated=40 cleared=0` ve operatör NEDEN'i okuyamıyor.
Düzeltme `trace.append({..., "why": ...})` ile **reflect katmanına** kondu. Ama tüketiciye giden
yol `_slim`den geçiyor ve `_slim` o satırları `passes` filtresiyle **aynı çöpe** atıyor.
Düzeltme bir kat aşağıda kaldı; belirti (okunamayan ret gerekçesi) hiç değişmedi.

### `_slim` iz dışında da 8 alan düşürüyor

`coordinate_descent_search` şunları döndürüyor: `incumbent_oos, evaluated, cleared, fresh,
cached_hits, skipped_wallclock, best, trace, regime, planlanan_sonda, hayalet_suzulen,
oturum_kaydi, kesildi(+sebep/tavan_dk/gecen_dk/kalan_sonda)`.
`_slim` yalnız 5'ini geçiriyor: `status, evaluated, cleared, incumbent_oos, best`.
Düşenler arasında **`hayalet_suzulen`** (Ö-48 iz alanı — "hangi düğmeler motor-okuyucusuz diye
elendi") ve **`kesildi`/`kalan_sonda`** (arama süre tavanına takıldı mı) var. Isınma yolu
(`hermes` `warmup_sprint` olayı) bu alanları BASIYOR; sprint yolu basmıyor — aynı fonksiyonun
iki okuyucusundan biri kör.

### Yan bulgu: bir sonda hiç soru sormadan K'yı büyütmüş

`entry.min_rvol=0.2` sondası 2000/2000 replikasyonda `|ΔS| ≤ 1 ULP` üretti — kapının kendi
sözcükleriyle **"ATIL DÜĞME ADAYI: değişikliğin FİİLEN HİÇBİR ŞEY YAPMADIĞININ ölçümü"**.
`entry.min_rvol` incumbent `strategy.yaml`ında **hiç yok** (varsayılan 0.0), motor okuyucusu var
(`strategy.py:426-427`) ama 0.2 eşiği bu evrende hiçbir işlemi elemiyor. Bedeli somut:
K 5'ten 6'ya çıktı, `p_required` 0.9600'den 0.9667'ye yükseldi — yani **hiçbir şey ölçmeyen bir
sonda, diğer beş adayın çıtasını yükseltti.** Bu gerekçe de `_slim` yüzünden hiçbir yere yazılmadı.

---

## Ö4 · `loop_closed: false` / `shipped: false` — KİM YAZAR, KİM OKUR?

**Yazan tek yer: `meridian/sprint_run.py`.**

| satır | yazım | koşul |
|---|---|---|
| `:177` | `loop_closed=False` | eval penceresinde seans yok |
| `:196` | `loop_closed=False, shipped=False` | Faz A `n_v1 < min_sample` |
| **`:208`** | `loop_closed=False, shipped=False` | **Faz B hiçbir aday geçmedi ← BU KOŞUM** |
| `:224,:228` | `loop_closed=bool(closed), shipped=True` | Faz C koştu |

Anlamı: `shipped` = Faz B'de bir aday **kum havuzunda** ship edildi mi (canlı defter DEĞİL).
`loop_closed` = ship edilen v2, Faz C ileri koşusunda `min_sample`a ulaşıp `realized_delta`
üretebildi mi (`_v2_realized`, `sprint_run.py:141`) — yani **öğrenme döngüsü kapandı mı**:
tahmin → uygulama → ölçülmüş sonuç. Faz B ship etmediği için Faz C hiç koşmadı; `loop_closed`
`:208`de **sabit False** olarak yazıldı, ölçülmedi.

**Okuyan (ölü alan mı?):** Ölü DEĞİL ama tüketici TEK ve yalnızca KOZMETİK.

* `sprint.status()` (`sprint.py:154`) dosyayı olduğu gibi geçiriyor (`{**st, ...}`).
* `/api/hermes` → `sprint` alanı (`api.py:4783`); `/api/sprint` (`api.py:4941`) EMEKLİ.
* Tek alan-düzeyi tüketici `meridian/web/app.js` `sprintCard`:
  * `:10969` `const closed = sp.loop_closed;` → `:11007`de yalnız nota `"✓ "` öneki ekliyor.
  * `:10982` `sp.shipped === false ? "yok"` → "Yayınlanan" kutucuğunun metni.

Kod tabanının geri kalanında **hiçbir kapı, bekçi, kadans ya da analitik bu iki alanı okumuyor**
(`grep -rn "loop_closed"` → yalnız `sprint_run.py` + `app.js`). Özellikle:
`sprint.should_run` `n_hyp_at_start`/`phase`/`pid` okur, `loop_closed`/`shipped` OKUMAZ — yani
"döngü aylardır kapanmadı" gerçeği **hiçbir tetikleyiciye bağlı değil**. Alarm yok, eskalasyon
yok, kadans değişikliği yok. Bir pano etiketi.

---

## KANIT

```
$ ssh ... 'cat /opt/meridian/state/sprint_status.json'
  "phase": "done", "loop_closed": false, "shipped": false, "n_v1": 566,
  "note": "hiçbir aday OOS kapısını geçemedi — bu veri diliminde v1 yerel-optimal",
  "search": {"status":"no_clearing_candidate","evaluated":6,"cleared":0,
             "incumbent_oos":0.409,"best":null,"trace":[]}

$ ssh ... 'md5sum /opt/meridian/meridian/{reflect,sprint_run}.py'  (yerel depo ile AYNI)
  bb2ffe9d67cb557ea60adc491cc20695  meridian/reflect.py     (mtime 2026-08-23 21:06)
  160b7d27a0839c11625e445de1188f67  meridian/sprint_run.py  (mtime 2026-08-16 20:13)

$ ssh ... 'tail -1 .../20260821-220656/state/validation_ledger.jsonl'   # oturumun TEK resmî kaydı
  ts=2026-08-22T06:00:40Z · etiket="entry.min_score=58" · oos_score=0.4247 · incumbent_oos=0.409
  · oos_para=0.4292 · incumbent_para=0.3681 · fold_wins="2/3" · tail_ok=true · dd_ok=true
  · dd_mtm_durum="gecti" · gate_law="probabilistic" · k_probes=6 · erosion_queries=1
  · n_trials=7 · dsr=0.450504 · passes=FALSE
  (NOT: `search_p` ve `search_p_required` bu deftere YAZILMIYOR — kapı sözlüğünde var,
   `validation.record_candidate` payload'ında yok. Hükmü veren sayı kalıcı kayıtta YOK.)

$ ssh ... 'cat .../gate_calibration.json'     → "extra_p": 0.0   (kum havuzu ve canlı, ikisi de)
$ ssh ... 'cat /opt/meridian/state/wf_cache_rev.json' → {"rev": 1787344310}   (kum havuzuyla AYNI)

# probe_cache.json + inc_cache.json'dan çıkarılan 6 sonda + incumbent (yukarıdaki tablo)
$ .venv/bin/python  → PairedProbabilisticGate(goal).evaluate(inc._trades_search,
                        cand._trades_search, "2023-01-11", "2024-01-18", k_probes=6)
  p_required(K=6) = 0.9666666666666667 · p_required(K=1) = 0.8
  entry.min_score=58.0        P=0.7555  why="KISMEN AYIRT EDİLEMEZ: 64/2000 ... P(ΔS>0)=0.755 < 0.97"
  entry.min_volume_ratio=1.7  P=0.3260
  entry.min_rvol=0.2          P=0.0000  why="AYIRT EDİLEMEZ: ... 2000/2000 replikasyonda |ΔS| ≤ 1 ULP
                                             ... atıl düğme adayı"
  entry.min_score=62.0        P=0.0700
  entry.min_volume_ratio=1.3  P=0.5410
  entry.max_ext_atr=2.0       P=0.3200
```

Yeniden üretim: `probgate` deterministiktir (`seed=42`, `n_boot=2000`, `PairedProbabilisticGate.
__init__` docstring: "Tohum sabittir — aynı girdi aynı kapı kararını verir"). Girdi olarak
kum havuzundaki DONMUŞ `_trades_search` dilimleri ve kum havuzunun `goal.yaml`ı kullanıldı.

---

## BU MERCEKTEN GÖRÜNEN KÖK NEDEN ADAYI

**Sistem "kapıyı geçen aday yok" ile "daha iyi aday yok"u aynı cümleye indiriyor, ve indirdiği
yerde ayrımı geri kurmaya yarayacak HER SAYIYI çöpe atıyor.**

Zincir, ölçülen hâliyle:

1. Kapı 6 aday için ret gerekçesi ÜRETİYOR (`_gate_eval` → `_why`; içinde `search_p`,
   `p_required`, atıl-düğme hükmü).
2. `validation.record_candidate` payload'ı `search_p`/`p_required`/`why` alanlarını TAŞIMIYOR →
   hükmü veren sayı hiçbir kalıcı deftere girmiyor.
3. `sprint_run._slim` `trace`i `passes` ile süzüyor → `cleared==0` iken ret gerekçelerinin
   tamamı SİLİNİYOR (`sprint_status.json` + `sprint_runs.jsonl`).
4. `app.js:10986` aynı süzgeci ikinci kez uyguluyor → onarım tek katta yapılırsa yine görünmez.
5. Geriye `sprint_run.py:207`deki **sabit dizge** kalıyor: "bu veri diliminde v1 yerel-optimal" —
   ölçüme dayanmayan, her ret koşumunda birebir aynı yazılan bir iddia.
6. `loop_closed: false` hiçbir tetikleyiciye bağlı olmadığı için bu döngü haftalarca kendini
   tekrar edebiliyor ve kimse uyanmıyor.

Ölçülen gerçek şu: **bu koşumda arama incumbent'ı para ölçeğinde %16,6 geçen bir nokta buldu
(`entry.min_score` 60→58), fold çoğunluğunu ve tüm veto bacaklarını geçti, ve yalnız
P(ΔS>0)=0,756 < 0,80 taban eşiği yüzünden reddedildi.** Kapı bu reddi savunulabilir biçimde
verdi (istikrar kanıtı gerçekten zayıf) — kusur kapıda değil, **bu cümlenin operatöre asla
ulaşmamasında**: sistem "yerel optimaldeyiz, aranacak bir şey yok" diyor; ölçüm ise
"yön doğru, örneklem ince, aynı yöne DAHA ÇOK kanıtla dön" diyor. İkinci cümle bir sonraki
turun ne yapacağını belirler; birincisi turu iptal ettirir.

İkincil kök neden adayı: **karar değişkeni ile raporlanan değişken ayrışmış durumda.** Kapı
`para` (`ret_c_v3`) ile hüküm veriyor, sistemin her yerinde `oos_score` (bileşik) basılıyor,
ve `rep_cand`/`best` seçimi de `oos_score` ile yapılıyor. Ölçülen ayrışma gerçek:
`min_volume_ratio=1.3` raporlanan sırada 5., karar sırasında 2.

---

## ÖLÇÜLEMEYENLER (UYDURMA YASAĞI)

* **Koşum anındaki `reflect.py` sürümü — ölçülemedi.** Canlı `reflect.py` mtime
  2026-08-23 21:06, koşum 2026-08-21 22:07. Yani dosya koşumdan SONRA değişti; koşan sürümün
  `trace`e `why` yazan hâli olup olmadığını git komutu koşmadan tarihleyemedim.
  **Hükmü etkilemez**: `sprint_run.py` mtime 2026-08-16 (koşumdan ÖNCE) ve md5'i yerel depoyla
  aynı — yani `trace`i süzen `_slim` KOŞAN sürümdür ve `cleared==0` iken çıktı her hâlde `[]`dir.
* **Koşum sırasında kaydedilmiş `search_p`/`p_required` — YOK.** Yukarıdaki P değerleri diskteki
  donmuş dilimlerden **YENİDEN ÜRETİLDİ** (deterministik tohum). Orijinal kayıt hiç yazılmadığı
  için "kaydedilen sayı buydu" diyemem; "aynı girdi + aynı kod bunu verir" diyebilirim.
* **`planlanan_sonda` (total) doğrudan okunamadı** — `_slim` düşürüyor. Dolaylı ölçüm:
  defterdeki `k_probes = 6` ve kod `k_probes=total` verdiği için total=6. Yani `budget=6`
  planlanan sonda sayısını tamamen belirlemiş; önbellek boştu (SELECT penceresinde 0 hazır girdi).
* **`n_v1: 566` ile `evaluated: 6` arasında bir ilişki YOKTUR** — brief'in "566 v1 üretilip 6
  değerlendirildi" ifadesi iki farklı birimi karşılaştırıyor: `n_v1` kum havuzundaki v1 **İŞLEM**
  sayısı (`sprint_run._count`), `evaluated` **ADAY PARAMETRE** sayısı. 566, aday havuzu değildir.
* **Isınma yolunun (`warmup_sprint`, saatlik, `evaluated: 40`) skor dağılımı — ÖLÇÜLEMEDİ.**
  O pencereye ait `probe_cache.json` canlıda **tek girdi** taşıyor ve dosya
  **2026-08-21 20:45'ten beri yeniden yazılmamış** (`PROBE_DISK_CAP=300`, yani kapasite sınırı
  değil). `_probe_disk_save` yalnız önbellek ıskasında koştuğuna göre 40 sondanın tamamı
  süreç-içi önbellekten karşılanıyor olmalı — ama bu bir ÇIKARIM; doğrulaması Mercek A/B'nin
  işi. Saatlik sayıların birebir aynı olması bu çıkarımla tutarlı.
* **`p_required`in bu adaylar için "doğru" seviyede olup olmadığı** — bu bir kalibrasyon sorusu
  ve bu turda ölçülmedi. Ölçülen tek şey `extra_p = 0.0` ve `gate_calibration.durum = "kurak"`
  ("1 çift var, eşik 5 ... extra_p=0,0 'düzeltme gerekmedi' DEĞİL 'henüz ölçülemedi' demektir").
