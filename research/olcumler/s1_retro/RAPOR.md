# S1 — 52WH + HACİM-ŞOKU RETROSPEKTİF KATKI ÖLÇÜMÜ
**Rol 2 · 2026-07-31 · SALT-ÖLÇÜM**

Sözleşme: `research/cards/EDG-2026-001-52wh-proximity.yaml` + `EDG-2026-002-volume-shock.yaml`.
Eşikler, grid ve kill kriterleri karttan alındı; **ölçümden sonra hiçbiri değiştirilmedi**.
Repo ve `state/` **yazılmadı** — her şey `scratchpad/s1_retro/sandbox` kopyasında koştu.
Kart dosyalarına **dokunulmadı**; §6'daki güncellemeleri Rol 1 işler.

Ham bloklar: `sonuc.json`. Ara çıktılar: `sonuc_raw.json`, `panel_diag.json`, `supp.json`,
`dirty_ab.json`, `obs_clean.csv`, `ghost_report.json`. Betikler: `scripts/`.

---

## 0. Üç cümlelik hüküm

1. **BT-2:** hayalet hasarı bu tabloda **küçük ama karar sınırında** — |ΔIC| medyanı 0.0037, ama
   63 hücrenin **5'i anlamlılık hükmünü değiştirdi**.
2. **EDG-2026-001 (52wh): KAPAT.** Large-cap alt-örnekte 9/9 hücre anlamsız; panel tanısı da boş →
   boş sonuç aralık kısıtının eseri değil. Çift-sayım kill'i tetiklenmedi (ρ=-0.036).
3. **EDG-2026-002 (volshock): BANT DOĞRULANDI, GRID BOŞ → ARŞİV.** Bant yapısı hayalet artefaktı
   **değil**; ama 18 hücrenin hiçbiri katkı vermedi ve her form ham `rvol20`'den kötü. Canlı eşik kalır.

---

## 1. BT-2 — temiz taban ve hayaletin hasar tespiti

**Yöntem.** Aynı kod iki kez: (a) mevcut `state/component_ic.json` (2026-07-30 00:10, kapı öncesi),
(b) sandbox'ta takvim-kapılı yeniden üretim. Yazılı sayıya değil, **kapı açık/kapalı A/B**'ye
dayandırıldı — böylece uygulama farkı sabit tutuldu.

**Kapıdan düşen:** 431 satır — `2025-05-26` (251), `2018-11-22` (179), + 3 karantina satırı
(`2012-01-20`, `2013-07-15`, `2013-12-18`). Reddedilen defter: 0.

**Örneklem değişmedi** (gerçek 95 · cf 2106 · havuz tekil 1952): **hiçbir gözlem satırı hayalet
tarihte değil** (5/5 tarih için doğrulandı).

| ölçü | değer |
|---|---|
| kıyaslanabilir hücre | 63 |
| max \|ΔIC\| | **0.0129** (cf · rs · @20) |
| ortalama / medyan \|ΔIC\| | 0.0040 / 0.0037 |
| **anlamlılık dönmesi** | **5 hücre** |
| anlamlı hücre sayımı | gerçek 2→2 · cf 8→8 · havuz 6→**7** |
| manşet | rvol20 @5 IC 0.2336 → 0.2341 (değişmedi) |

**Dönen 5 hücre:** cf·rs@20 (0.0338→0.0467 **anlamsız→anlamlı**), cf·tight@20 (**anlamlı→anlamsız**),
havuz·rs@10, havuz·rs@20 (ikisi de **anlamsız→anlamlı**), havuz·tight@20 (**anlamlı→anlamsız**).

**Hüküm.** Hasar gerçek ama **ortalamada değil, karar sınırında**: manşet bileşen ve katman
toplamları pratikte aynı kaldı, buna karşılık aralığı sıfıra yakın 5 hücre taraf değiştirdi.
"component_ic KİRLİ" tespiti doğru; büyüklüğü ~0.004 IC mertebesinde.

**Etki kanalı (neden bu kadar küçük).** Hayalet bar gözlemin kendisi değil; kirlilik yalnız
(a) yuvarlanan pencerelere (SMA20, 252-gün zirvesi) ve (b) hayalet barı aşan ileri-getiri
penceresine sızıyor. 2025-05-26'nın ±30 günü içinde yalnız **43 gözlem** var.

> **KAPSAM UYARISI — bu ölçüm bir aklama belgesi DEĞİL.** Gözlem penceresi 2022-2026 ve içindeki tek
> hayalet tarih 2025-05-26; **2018-11-22 bu tabloya hiç değmiyor**. 2018'i kapsayan artefaktlar
> (uzun geçmişli R-tabloları, eşik eğrileri, backtest çıktıları) burada **aklanmadı** ve ayrı
> yeniden üretim ister.

---

## 2. EDG-2026-001 — 52 hafta zirvesine yakınlık

`feat_52wh = close / rolling_max(high, 252)` · alt-örnek = **ADV(50g) o tarihte evren medyanının
üstünde** (nokta-zamanlı, nedensel, tek tanım — grid'e sayılmaz).
Alt-örnek payı: cf %56.2 (n=1184) · gerçek %49.5 (n=47) · havuz %55.6 (n=1086).

**Aralıklar iki yöntemle:** Fisher-z (component_ic ile kıyaslanabilirlik için) **ve tarih-kümeli
blok bootstrap** (B=2000). Hüküm **bootstrap**'a göre — cf satırları güne kümelenmiştir ve
`component_ic.ci_varsayim` notunun söylediği tam olarak budur.

### Large-cap alt-örnek IC (kartın hüküm popülasyonu)

| katman | @5 | @10 | @20 |
|---|---|---|---|
| gerçek (n=47) | 0.0105 | -0.0284 | 0.1038 · CI [-0.179, +0.373] |
| **cf (n≈1182)** | -0.0215 | -0.0158 | **0.0374 · CI [-0.030, +0.100]** |
| havuz (n≈1084) | -0.0213 | -0.0204 | 0.0276 |

**9/9 hücre anlamsız.** En iyi hücre cf@20: `|IC|>=0.03` eşiğini geçiyor ama **CI sıfırı kapsıyor**.
Kart iki şartı VE ile bağlamış → **başarı ölçütü karşılanmadı**.

### Çift-sayım kontrolü (kill #2)

ρ(feat_52wh, VCP skoru) = **-0.036** (cf) · -0.051 (havuz) · +0.166 (gerçek) → **0.8 eşiğinin çok
altında, kill #2 TETİKLENMEDİ.** Bileşen kırılımı: `s_tight` +0.47, `s_prox` -0.28, `rs` +0.08.
Yani 52wh mevcut maruziyetin yeni bir adı **değil** — bağımsız, ama **bilgisiz**.

### Tanı: boş sonuç aralık kısıtının eseri mi? (kart dışı, hüküm taşımaz)

Sinyal popülasyonu tasarımı gereği zirveye yakın: `feat_52wh`in **%77'si 0.95 üstü** (panelde %22).
Böyle bir örneklemde "IC sıfır" iki ayrı şeyi de gösterebilirdi. Ayırmak için tam panelde
(temiz barlar, günlük kesitsel IC + Newey-West) ölçüldü:

| pencere | @5 | @10 | @20 |
|---|---|---|---|
| tam geçmiş (large-cap, ~618k gözlem) | -0.0062 (t=-1.00) | -0.0103 (t=-1.20) | -0.0149 (t=-1.25) |
| cf penceresi (large-cap, ~142k) | +0.0042 (t=0.31) | +0.0036 (t=0.20) | +0.0096 (t=0.40) |

Hiçbiri anlamlı; tam geçmişte **işaret tez yönünde bile değil**. **Aralık açıldığında da edge yok** →
boş sonuç popülasyon körlüğü değil.

### HÜKÜM ÖNERİSİ: `registered → archived`

Kill #1 tetiklendi. Kill #2 tetiklenmedi — aile **çift-sayımdan değil, bilgisizlikten** kapanır.

> **Kart metnine düzeltme önerisi.** Kill #1 "Barroso-Wang doğrulanmış olur" diyor; bu ölçüm bunu
> **söyleyemez**: evrenin tamamı likit büyük/mega-cap, "alt-örnek" zaten büyük olan 250 ismin ADV
> üst yarısıdır ve karşı kutupta gerçek bir small-cap kolu **yok**. Önerilen ifade: *"bu (tamamı
> likit) evrende edge ölçülemedi"* — literatür hükmü değil.

---

## 3. EDG-2026-002 — hacim şoku

### Aşama 1 — bant tablosu hayalet artefaktı mı? (kill #1)

`strategy.py:26-33`'ün kaynağı `g2_olcum.py` depoda **yok**; bu yüzden hüküm "yazılı sayı vs benim
sayım" farkına değil, **kapı açık/kapalı A/B**'ye dayandırıldı.

| bant | yazılı (kirli) | temiz yeniden üretim | A/B izole hayalet etkisi | n (yazılı → temiz) |
|---|---|---|---|---|
| 0-0.8 | -0.80% | -0.799% | 0.000 pp | 12 → 12 |
| 0.8-1.5 | -0.52% | -0.634% | +0.047 pp | 269 → 271 |
| 1.5-2.0 | +1.84% | +1.800% | -0.019 pp | 955 → 955 |
| 2.0+ | +1.44% | +1.401% | -0.007 pp | 857 → 856 |

**KILL #1 TETİKLENMEDİ.** Hayaletin bant tablosuna saf etkisi en fazla **0.047 pp**. Yapı gerçek.

### Ama yapının iki iddiası aynı sağlamlıkta değil

Bant ortalamalarının aralıkları örtüşüyor; doğru sınav **farkın** aralığıdır (tarih-kümeli
bootstrap, B=4000):

| fark | nokta | CI | sıfırı dışlıyor mu |
|---|---|---|---|
| [1.5-2.0] − [0.8-1.5] | +2.43 pp | [+0.94, +3.93] | **EVET** |
| [2.0+] − [0.8-1.5] | +2.04 pp | [+0.47, +3.62] | **EVET** |
| [1.5-2.0] − [2.0+] | +0.40 pp | [-0.63, +1.40] | **HAYIR** |

Yani **"yüksek hacim > düşük hacim" adımı gerçek; "1.5-2.0 tatlı nokta / ilişki monoton değil"
iddiası ölçümle desteklenmiyor.** Üçgen formun tüm gerekçesi ikincisiydi.

Ek ölçüm: üçgenin **0 puan verdiği** `rvol>=2.5` bölgesi — n=433, ort. 20-bar getiri **+1.61%,
CI [+0.64, +2.54] (anlamlı POZİTİF)**. `strategy.py:36-40`'taki yazılı "sağ kol kanıttan sert"
muhafazakârlık notu ölçüldü ve **haklı çıktı**.

### Aşama 2 — grid (kill #2)

Kart grid'i: persentil eşiği **[80, 90, 95]** × form **["üçgen(1.75)", "persentil-doğrusal"]**.
Form tanımları ölçümden **önce** sabitlendi: doğrusal = eşik üstünde `(pct-p)/(100-p)` rampası;
üçgen = `strategy.rvol_band_score(rvol20)`, eşik altında 0.

**6 grid noktası × 3 ufuk = 18 hücre → anlamlı hücre: 0.**
En büyük |IC|: `p80|üçgen(1.75) @5` = 0.0373, CI [-0.013, +0.085].
Anlamlılığa en yakın: `p95|persentil-doğrusal @20` = 0.0354, CI [-0.010, +0.082].

Kıyas tabanı (yeni K yok — mevcut nesneler):

| nesne | @5 | @10 | @20 |
|---|---|---|---|
| **ham rvol20** (mevcut bileşen) | 0.0364 | **0.0499 · CI [+0.003,+0.097]** | **0.0645 · CI [+0.017,+0.111]** |
| kapısız üçgen (canlıdaki uyuyan düğme) | 0.0397 | 0.0388 | 0.0154 |
| en iyi grid noktası (18 hücrenin en büyüğü) | 0.0373 (anlamsız) | — | 0.0354 (anlamsız) |

**Her şekillendirilmiş/kapılı form, zaten ölçülmüş ham `rvol20`'den kötü.**

**Kapı neden boş çalışıyor:** cf defteri zaten kırılım/hacim-onaylı adaylardan oluşuyor →
p80 satırların **%98.5'ini**, p90 %93.4'ünü "şok" sayıyor (panelde bu oran %23.5). Hacim şoku bu
popülasyonda ayırt edici bir olay değil, **sabit**.

**Panel tanısı (kart dışı):** tam panelde rvol20 @20 ortalama günlük IC **-0.0059 (t=-2.68)** ve
bant yapısı **düzleşiyor** (0-0.8: +1.24% · 0.8-1.5: +1.28% · 1.5-2.0: +1.16% · 2.0+: +1.15%).
Yani pozitif hacim etkisi **kırılım popülasyonuna koşulludur**, evrensel değil.

### HÜKÜM ÖNERİSİ: `registered → archived`

Aşama-1 geçti, aşama-2 kaldı; kart aşama kapısını VE ile bağlamış.
**Canlı `min_volume_ratio=1.5` DEĞİŞMEZ** (kart: "mevcut sezgisel eşik KALIR"). **Gölge kolu açılmaz.**

> **Torun kart önerisi (bu turda UYGULANMAZ).** Kanıt **monoton** formu üçgene tercih ediyor:
> (1) tepe iddiası CI'siz, (2) üçgenin 0'ladığı bölge anlamlı pozitif, (3) ham monoton seri iki
> ufukta anlamlı. Bu **yeni bir kartın** konusudur (form revizyonu) — ön-kayıt önce, ölçüm sonra.
> Ölçümden sonra form seçmek yasak.

---

## 4. K muhasebesi

| kalem | kayıtlı K | ölçülen kombinasyon | hücre (×3 ufuk) |
|---|---|---|---|
| EDG-2026-001 | 1 | 1 | 9 |
| EDG-2026-002 | 5 | **6** | 18 |

> **Şema kusuru — Rol 1'e.** Kart `K+=5` diye kayıtlı (3 eşik + 2 form, **toplanarak**); ölçülen
> nesne ise **3×2 = 6 kombinasyondur**. Kart şeması grid eksenlerini topluyor, çarpmıyor →
> **K 1 birim eksik kayıtlı**. Önerilen düzeltme: `K+=5 → K+=6`.

**Ufuk çarpanı:** 5/10/20 kartlarda sözleşme olarak yazılı (mevcut `component_ic` ufukları) → yeni K
değil; ama çoklu-sınama okuması 9 ve 18 hücre üzerinden yapılmalı.

**Çoklu sınama:** 002'de 18 hücrede %95 seviyesinde şansla ~0.9 yanlış-pozitif beklenirdi; gözlenen
0. Boş sonuç **düzeltmeye ihtiyaç duymadan** boştur.

**K dışı tanılar** (hiçbiri eşik/form SEÇMEDİ, hiçbiri hüküm taşımaz): panel Fama-MacBeth tanısı ·
bant farklarının bootstrap aralığı · kapısız üçgen · kapı açık/kapalı hayalet A/B.

---

## 5. Zorunlu notlar

**SURVIVORSHIP (her iki kartı da etkiler).** Evren `data.REPLAY_UNIVERSE`: bugün yaşayan ~250 likit
isim. 2022-2025'te düşen bir avuç isim (INTC/PYPL/ENPH/MRNA/VFC…) **bilerek** eklenmiş, ama
delisted/iflas/satın alınmış adlar **yok** ve tarihsel üyelik nokta-zamanlı **değil**.
*Yön:* seviyeler yukarı yanlı (panelde her rvol bandının 20-bar ortalaması ~+1.2% → "bant farkı"
okunabilir, "bant seviyesi" okunamaz).
*Hükümlere etkisi:* **001 için yanlılık bulguyu GÜÇLENDİRİR** — hayatta kalanlar tam da zirveye
yakın kalmayı başaranlardır, 52wh bu evrende olduğundan **iyi** görünmeliydi; buna rağmen edge
çıkmadı. 002 için bant farkları yanlılığa görece dayanıklı, grid'in boş çıkması ise yanlılıktan
bağımsız (kapı zaten boş çalışıyor).
Ayrıca **cf katmanı alınmamış hipotetik girişlerdir** — seçim yanlılığı ayrı ve açık durur.

**EŞZAMANLI AJAN ETKİSİ (ölçüm anının fotoğrafı).** Ölçüm koşarken **başka ajanlar canlı repoyu
değiştiriyordu**: `meridian/adapters/data.py` (01:19), `meridian/analytics.py` (01:00),
`research/cards/README.md` (01:04) ve `state/events.jsonl`e düşen `bar_cache_repaired` (SPY) satırları.
Bunların **hiçbiri bu ajanın yazımı değil** — sandbox kopyası 00:57'de alındı ve tüm koşumlar
`MERIDIAN_ROOT=sandbox` ile döndü.
*Tutarlılık doğrulandı:* sandbox'ın bellek-içi kapılı SPY serisi ile repodaki disk serisi
karşılaştırıldı — **çakışan tüm barlar bit-birebir aynı** (5 sütunda max Δ = 0.0), tek fark
kapının düşürdüğü 2 hayalet tarih. Yani disk onarımı bu ölçümün tabanını değiştirmez; onarım
indiğinde bu sayılar **yeniden üretilebilir kalır**. (Not: ölçüm anında repo `spy.csv` hâlâ 5680
satırdı — `bar_cache_repaired` olayı düşmüş ama disk yazımı o an inmemişti.)

**ÖLÇÜLEMEYENLER (uydurma yasağı).**
- **Maliyet modeli:** `pessimistic_band_v2` inmedi (E3 bekleniyor). Hiçbir sayı maliyet düşülmüş
  değil; IC ham öngörü içeriğidir. Boş sonuçlar için sorun değil (maliyet yalnız kötüleştirirdi),
  ama **pozitif bir hüküm çıksaydı maliyetsiz verilemezdi**.
- **Gerçek katman gücü:** large-cap alt-örnekte n=47 → CI genişliği ±0.28. Bu katmandaki "anlamsız"
  bulgusu **örneklem kuraklığıdır, kanıt değil**; hüküm cf katmanından ve panel tanısından geliyor.
- **`g2_olcum.py` kaynağı depoda yok** → yazılı tabloya karşı fark uygulama farkını içerebilirdi;
  hayalet hükmü bu yüzden A/B'ye dayandırıldı.

---

## 6. Kart güncelleme önerileri — **ROL 1 İŞLER, BU AJAN YAZMADI**

**EDG-2026-001:** `status: registered → archived` · `trial_ids: [S1-retro-2026-07-31-52wh]`
Özet: large-cap alt-örnekte 9/9 hücre anlamsız (en iyi cf@20 IC=0.0374 CI[-0.030,+0.100]);
VCP korelasyonu ρ=-0.036 (çift-sayım yok); panel tanısı da boş → aile kapandı.
Metin düzeltmesi: kill #1'deki "Barroso-Wang doğrulanmış olur" → "bu evrende edge ölçülemedi".

**EDG-2026-002:** `status: registered → archived` · `trial_ids: [S1-retro-2026-07-31-volshock]`
Özet: bant yapısı temiz barlarda **doğrulandı** (hayalet A/B max 0.047 pp) → kill #1 tetiklenmedi;
18 hücrede 0 anlamlı katkı → **kill #2 tetiklendi**. Canlı `min_volume_ratio=1.5` kalır, gölge kolu
açılmaz. `k_registry`: **K+=5 → K+=6**. Torun kart önerisi: rvol form revizyonu (monoton vs üçgen).
