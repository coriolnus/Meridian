# ÇIKIŞ PAKETİ — PRESCREEN ÖLÇÜMÜ (denetim maddesi 1)

**Tarih:** 2026-07-31 · **Yasa:** PARA-v3 · **Pencere:** R1 (IS 2022-01-01 · OOS 2024-01-01→2026-04-30 ·
holdout 2026-07-30 · embargo 10g) · **k_probes = 3 (beyanlı, ölçülen 3)** · **Süre:** prescreen 3.125s +
atıf sondası 3.158s
**Beyan:** SALT-ÖLÇÜM. Canlı repo/state'e tek bayt yazılmadı; tüm iş `scratchpad/cikis_paketi/state`
kopyasında; `record_erosion=False` (aşınma defterine SAYIM yazılmadı, yalnız mevcut marj okundu).
**Çıktılar:** `sonuc.json` · `ham_islemler/*.json` (her paketin ham işlem satırları) ·
`throttle_sonuc.json` · `foldlar_kapi_yasasi.json` · `kosu.log` · `canli_fingerprint.json`

---

## 0. VERİ HİJYENİ — analizden ÖNCE, kopya üzerinde

`meridian.barrepair` (XNYS takvimi, `pandas_market_calendars` okundu = True) sandbox bar defterlerine
uygulandı. **259 defter / 1.344.334 satır tarandı, 445 satır düştü (%0,033):**

| tarih | dosya | sınıf kırılımı | tür |
|---|---|---|---|
| 2025-05-26 (Memorial Day) | 258 | 199 birebir kopya · 52 yakın kopya · 7 bölünmemiş ham fiyat | hayalet seans |
| 2018-11-22 (Thanksgiving) | 184 | 169 düz bar (hacim 0) · 15 bölünmemiş ham fiyat | hayalet seans |
| 2013-12-18 (CHD) | 1 | düzeltilmemiş fiyat | karantina |
| 2012-01-20 (EL) | 1 | düzeltilmemiş fiyat | karantina |
| 2013-07-15 (PINS) | 1 | düzeltilmemiş fiyat | karantina |

**442 hayalet + 3 karantina = 445.** 259 defterin tamamı yeniden yazıldı; kapının reddettiği (kitlesel
takvim uyuşmazlığı) defter yok; okunamayan defter yok. Yükleyici `dataset.load_cached`e çevrildi —
`dataset.load()` bayat önbellekte AĞA ÇIKAR ve corporate-action tespitinde CSV'leri silip yeniden yazar,
yani bu temizliği sessizce geri alırdı.

Evren: `REPLAY_UNIVERSE` 251 − FISV (CSV yok) = **250 sembol** (8 emekli sembol zaten evren dışı).

---

## 1. DÜĞME KEŞFİ — gerçek adlar, gerçek varsayılanlar (koda karşı doğrulandı)

| işlev | düğme | bounds | canlı v3 | okuma yeri |
|---|---|---|---|---|
| zaman stopu | `exit.time_stop_days` | 3–40, adım 1, int | **15** | `strategy.manage_position:1003` |
| breakeven taşıması | `exit.breakeven_r` | 0.0–3.0, adım 0.5 | **1.0** | `strategy.manage_position:962` |
| sabit hedef (R:R TAVANI) | `exit.profit_target_r` | **2.0**–6.0, adım 0.5 | **2.5** | `strategy.scan_entry` (6 kurulumda `pt_cap`) |
| ATR iz-süren stop | `exit.trail_atr_mult` | 1.0–5.0, adım 0.1 | **2.5** | `strategy.manage_position:953` |
| chandelier demiri | `exit.chandelier_lookback` | 0–30, adım 5 | **0 (kapalı)** | `strategy.manage_position:975` |
| erken itlaf | `exit.early_kill_pivot` | 0–1 | **yok → 0** | `strategy.early_kill_pivot_exit:183` |
| itlaf penceresi | `exit.early_kill_bars` | 1–10 | **yok → 1** | `strategy.early_kill_pivot_exit:185` |

**Çıkış sebebi değerleri (tam küme, koddan):** `stop`, `stop_gap`, `target`, `target_gap` (`broker._touch_exit`),
`time_stop`, `regime_flip`, `early_kill_pivot`, `giveback` (`strategy.manage_position`), `eod_markout`,
`delisted_markout` (`backtest.replay`).

### ÖLÇÜLEMEYEN İKİ ŞEY (uydurma yasağı — eksik düğme adıyla raporlanıyor)

1. **"Zaman stopunu KAPAT"** — `exit.time_stop_days` için kapatma/None değeri **YOK** (bounds 3–40).
   Ölçülen: tam 2× (15→30).
2. **"Sabit hedefi DEVRE DIŞI bırak"** — `exit.profit_target_r` için 0/kapalı değeri **YOK** (bounds min
   **2.0**). "Hedefsiz" rejim bounds'ta ifade EDİLEMİYOR. Ölçülen: bounds tavanı (6.0). Gerçek "hedef
   kapalı" ölçümü **bounds değişikliği ister (ayrı tur)**.

**`exit.chandelier_lookback` bilerek AÇILMADI:** kod `new_trail = max(close−k·ATR, hh−k·ATR)`, `hh ≥ close`
olduğu için chandelier trail'i her zaman **SIKILAŞTIRIR**. "Kazananı bırak" imzasının tam tersi yöne
iter; açılsaydı paketin ölçmek istediği imzayı maskelerdi.

---

## 2. PAKETLER (hepsi guard'dan GEÇTİ — aralık + adım, düğme düzeyinde)

| paket | düğmeler |
|---|---|
| **P1** takvimi sustur | `time_stop_days 15→30` · `breakeven_r 1.0→2.0` |
| **P2** hedefi bırak, iz sür | P1 + `profit_target_r 2.5→6.0` · `trail_atr_mult 2.5→3.5` |
| **P3** erken itlaf | P2 + `early_kill_pivot 0→1` |

**NO-OP DOĞRULAMASI (E4 tuzağı) — üç katman, üçü de temiz:**
1. *Statik:* her düğmenin replay motorunda gerçek okuma yeri var (yukarıdaki tablo).
2. *Etkin parametre:* `config.resolve_params` dört rejimin **hepsinde** her düğme için farklı değer
   döndürüyor (`params_by_regime` boş → maskeleme yok). `sonuc.json → noop_on_dogrulama`.
3. *Davranışsal:* prescreen'in `motor_isliyor` bayrağı **üçünde de True** (fold n/avg_r/skor değişti).

---

## 3. PAKET × METRİK TABLOSU (kapının kendi yasası, R1 Search-OOS)

| metrik | incumbent | P1 | P2 | P3 |
|---|---|---|---|---|
| **kapı hükmü** | — | **GEÇMEZ** | **GEÇMEZ** | **GEÇMEZ** |
| OOS skoru (rapor metriği) | 0,0699 | 0,0608 (−0,0091) | 0,2141 (+0,1442) | 0,3120 (+0,2421) |
| **PARA ölçeği (KARAR)** | **0,0856** | **0,0684 (−0,0172)** | **None (n<30)** | **None (n<30)** |
| P(ΔS>0) · gerekli (K=3) | — | 0,437 / 0,933 | 0,276 / 0,933 | 0,354 / 0,933 |
| bootstrap ort. Δ (para) | — | −0,0183 | −0,0905 | −0,0730 |
| fold çoğunluğu (n-dengeli) | — | 2/3 | **0/2** (bir fold n=2 → itiraz edilmemiş) | 2/3 |
| düşüş vetosu | 0,0457 | 0,0461 · geçti | 0,0190 · geçti | 0,0051 · geçti |
| kuyruk VaR/CVaR Δ | 6,375 / 8,123 | −0,059 / +0,308 · ok | **+1,213 / +0,949 · VETO** | −3,429 / −2,979 · ok |
| eski yasa da reddederdi mi | — | evet (P=0,626) | evet (P=0,786) | evet (P=0,910) |
| iki yasa aynı hüküm | — | evet | evet | evet |

**Hiçbir paket tek bir kapı bacağından değil, ANA bacaktan kaldı:** P(ΔS>0) çıtanın çok altında.
P2 ayrıca kuyruk vetosuna ve fold çoğunluğuna da takıldı.

### Fold kırılımı (kapı yasasıyla — sınırlar incumbent'ın işlemlerinden türetildi, iki tarafa aynen)
Sınırlar: `2024-01-01 | 2024-04-04 | 2024-11-22 | 2025-08-18` (n-dengeli, embargo 10g)

| fold | incumbent | P1 | P2 | P3 |
|---|---|---|---|---|
| 1 | n=20 · +0,356 | n=16 · **+0,384** | n=2 · (n<3, sayılmadı) | n=4 · **+0,994** |
| 2 | n=19 · +0,206 | n=8 · −0,045 | n=11 · −0,084 | n=13 · +0,068 |
| 3 | n=22 · −0,136 | n=9 · **+0,005** | n=10 · −0,380 | n=8 · **+0,299** |

---

## 4. İŞLEM İSTATİSTİKLERİ — mimari değişikliğin imzası (Search-OOS)

| metrik | incumbent | P1 | P2 | P3 |
|---|---|---|---|---|
| **n** | **71** | 37 (−48%) | 28 (−61%) | 28 (−61%) |
| kazanma oranı | 45,1% | 48,7% | 42,9% | **39,3%** |
| ödeme oranı (ort kaz / |ort kay|) | 1,53 | 1,35 | 1,62 | **2,84** |
| beklenti (ort R) | 0,104 | 0,141 | 0,089 | **0,287** |
| ort kazanan R | 1,141 | 1,321 | 1,162 | **1,602** |
| ort kaybeden R | −0,747 | −0,977 | −0,717 | **−0,564** |
| **maks R** | **2,864** | 2,864 | **3,502** | 3,022 |
| p95 R | 2,139 | 2,749 | 1,889 | 2,708 |
| ≥3R işlem payı | **0,0%** | 0,0% | 3,6% | 3,6% |
| ort tutuş (bar) | 8,97 | 12,51 | 14,64 | 9,79 |
| medyan tutuş | 9 | 9 | 14 | **7** |
| kâr faktörü | 1,25 | 1,28 | 1,22 | **1,84** |
| düşüş (kapanmış işlem eğrisi) | 4,57% | 4,61% | 1,90% | **0,51%** |
| kuyruk CVaR (R) | 8,12 | 8,43 | 9,07 | **5,14** |
| toplam R | 7,39 | 5,23 | 2,48 | **8,04** |

**Çıkış sebebi dağılımı (Search-OOS):**

| sebep | incumbent | P1 | P2 | P3 |
|---|---|---|---|---|
| time_stop | 22 (31%) | 7 (19%) | 8 (29%) | **3 (11%)** |
| stop + stop_gap | 27 (38%) | 14 (38%) | 10 (36%) | 7 (25%) |
| target + target_gap | 9 (13%) | 7 (19%) | **1 (4%)** | 4 (14%) |
| regime_flip | 13 (18%) | 9 (24%) | 9 (32%) | 5 (18%) |
| early_kill_pivot | 0 | 0 | 0 | **9 (32%)** |

> **Etiket sınırı (koda karşı doğrulandı):** iz-süren stop `eff_stop = max(stop, trail_stop)` üzerinden
> ateşler ve defterde **ayrı bir "trail" sebebi YOKTUR** — `stop`/`stop_gap` diye yazılır. Vekil olarak
> işaret ölçüldü: kârda kapanan "stop" (= trail/breakeven'a çekilmiş) incumbent'ta 2/27, P1'de 1/14,
> P2/P3'te 0/10 ve 0/7. Yani **iz-süren stop hiçbir pakette kârlı çıkışın taşıyıcısı olmadı.**

### İMZA ANALİZİ — beklenen trailing imzası ("kazanma düşer, kazanan büyür, beklenti artar") çıktı mı?

| imza öğesi | P1 | P2 | **P3** |
|---|---|---|---|
| kazanma oranı düştü | ✗ (+3,6p) | ✓ (−2,2p) | **✓ (−5,8p)** |
| kazanan büyüdü | ✓ (+0,18R) | ✓ (+0,02R) | **✓ (+0,46R)** |
| beklenti arttı | ✓ (+0,037R) | ✗ (−0,016R) | **✓ (+0,183R)** |
| sağ kuyruk açıldı (maks R) | ✗ (0,00) | ✓ (+0,64R) | **✓ (+0,16R)** |
| **4/4** | 2/4 | 3/4 | **4/4** |

**P3 imzayı TAM verdi** — üstelik ödeme oranı 1,53→2,84 (+%86), kâr faktörü 1,25→1,84, düşüş 4,57%→0,51%,
CVaR 8,12→5,14. **P2 imzayı yarım verdi ve beklenti düştü:** hedefi tavana itmek + trail'i gevşetmek tek
başına sağ kuyruğu açtı (maks 3,50R, ilk kez ≥3R işlem) ama parayı getirmedi.
**P1 trailing imzası ÜRETMEDİ** — zaten üretmesi beklenmezdi (iz-süren düğmeye dokunmuyor); ürettiği şey
"daha az, daha uzun, biraz daha iyi işlem".

---

## 5. NEDEN KAPI HEPSİNİ REDDETTİ — kök neden ÖLÇÜLDÜ (spekülasyon değil)

İmza tam çıkmışken (P3) kapının reddetmesinin tek sebebi **işlem sayısının çökmesi**: 71 → 28.
Üç hipotez ayırt edici biçimde sınandı:

**(a) Giriş seti değişti mi? → ÇÜRÜTÜLDÜ.** `exit.profit_target_r` `scan_entry` içinde `pt_cap` olarak
okunuyor, yani teorik olarak girişe dokunabilirdi. Ölçüldü (2024-01-11→2024-06-30, 39 tarama günü, 250
sembol): **pt_cap=2,5 → 47 sinyal · pt_cap=6,0 → 47 sinyal.** Değişen tek şey ortalama plan R:R'si
(2,46 → 3,75). Giriş seti birebir aynı.

**(b) 5 slotun dolması mı? → TUTMUYOR.** P2/P3 tüm OOS boyunca **hiçbir gün 3 eşzamanlı pozisyona bile
çıkmadı** (ort eşzamanlı 0,88 ve 0,65 / 5). Slot kıtlığı olsaydı doluluk tavana yapışırdı.

**(c) DE-RISK RAMPASI → DOĞRULANDI.** `broker.max_positions_at(equity, peak, 5)` → `derisk_mult`:
tepe-noktasından düşüş **%3'ü geçince eşzamanlı pozisyon SAYISI doğrusal olarak kısılır, %8'de 0'a iner**.
Tam replay (2022-01-01→2026-07-30, günlük `eff_max_open` serisi kaydedildi):

| | tam replay işlem | ort. izin verilen eşzamanlı poz. (2024+) | 5/5 izinli gün | 0-1 izinli gün | ort. tepe-düşüşü | düşüş >%3 olan gün |
|---|---|---|---|---|---|---|
| incumbent | **161** | 1,98 / 5 | 8,1% | 39,5% | 5,79% | **92,4%** |
| P1 | 115 | 1,50 / 5 | 7,5% | 72,7% | 6,29% | **92,9%** |
| P2 | 72 | 1,27 / 5 | 0,0% | 73,9% | 6,76% | **100%** |
| P3 | 87 | 1,08 / 5 | 0,0% | 92,1% | 6,92% | **100%** |

**Hüküm:** gerçek verim tavanı `max_open_positions: 5` DEĞİL, de-risk rampasıdır — ve rampa incumbent'ta
bile günlerin **%92'sinde açık**. Bu bir **geri besleme döngüsü**: yavaş çıkış → sermaye eğrisi daha uzun
süre eski tepenin altında → izin verilen pozisyon sayısı 1'e iner → daha az işlem → eğri daha da düz →
rampa hiç kapanmaz. P3 günlerin %92'sinde **tek pozisyona** mahkûm kaldı.

Bu yüzden P3'ün paradoksu gerçektir ve ölçülüdür: **Search diliminde düşüşü 0,51% (en iyi), ama tam
replay'de tepe-düşüşü ortalaması 6,92% (en kötü)** — rampa kaybı değil **DURGUNLUĞU** cezalandırıyor.
PARA-v3 para/zaman ölçtüğü için sonucu doğru okuyor: işlem başına kalite arttı, **birim zamandaki para
azaldı**, ve n<30 olduğu için PARA skoru dürüstçe **None** (ölçülemedi) döndü.

---

## 6. DENETİM KANITIYLA UYUM — payda farkı BEYAN EDİLİYOR

Denetim maddesi 1'in rakamları (**95 işlem** · maks 2,69R · 33/95 time_stop · 4/95 hedef · ödeme 0,97 ·
kazanma %36,8) **CANLI/KAĞIT defterden** gelir: `state/exit_efficiency.json → _kaynak.n_real = 95`
(n_cf = 2.106 simüle). Bu ölçümün paydası ise **R1 Search-OOS backtest dilimi, n=71**. İkisi aynı popülasyon
DEĞİL ve yan yana konmamalı:

| | denetim (canlı, n=95) | bu ölçüm (R1 Search-OOS, n=71) |
|---|---|---|
| maks R | 2,69 | 2,86 |
| time_stop payı | 34,7% | 31,0% |
| hedef payı | 4,2% | 12,7% |
| ödeme oranı | 0,97 | 1,53 |
| kazanma oranı | 36,8% | 45,1% |

**Teşhisin YAPISAL kısmı iki paydada da aynı:** sağ kuyruk hedefte kırpılı (backtest'te ≥3R işlem payı
**tam 0,0%**), sol/orta kütle takvimde kesiliyor (time_stop ~1/3). **Şiddeti aynı değil:** canlı defter
belirgin biçimde daha kötü (ödeme 0,97 vs 1,53). Yani canlı ile replay arasında ayrıca bir **icra/uyum
farkı** var; bu ölçüm onu açıklamıyor ve açıklamaya çalışmadı.

---

## 7. HÜKÜM ÖNERİSİ

### Ship adayı: **HİÇBİRİ.** Üçü de kapıdan geçmedi, üçü de eski yasayla da geçmezdi.

Ama "reddedildi" ile "çürütüldü" aynı şey değil ve bu ölçüm ikisini ayırıyor:

**1. P1 (takvimi sustur) — ÇÜRÜTÜLDÜ, kapatılabilir.**
Beklenen faydayı (beklenti +0,037R) verdi ama PARA'yı **düşürdü** (0,0856→0,0684), sağ kuyruğu hiç açmadı
(maks R değişmedi: 2,864), trailing imzası çıkmadı ve bootstrap ortalama Δ'sı negatif. Tek başına zaman
stopunu uzatmak bu sistemde **yalnızca verim maliyeti**dir. Bu düğmeye tek başına dönmeye gerek yok.

**2. P2 (hedefi tavana it + trail'i gevşet) — ZAYIF, ayrıca kuyruk vetosuna takıldı.**
Sağ kuyruğu açtı (ilk kez ≥3R, maks 3,50R) ama beklentiyi düşürdü, fold çoğunluğunu 0/2 kaybetti ve
VaR/CVaR'ı anlamlı biçimde kötüleştirdi (+1,21R/+0,95R). Bu bileşimde ship-adayı yok.

**3. P3 (erken itlaf) — REDDEDİLDİ AMA ÇÜRÜTÜLMEDİ. Sıradaki turun ODAK noktası budur.**
Aranan trailing imzasını **4/4 verdi**, ödeme oranını %86 artırdı, düşüşü %89 ve CVaR'ı %37 azalttı,
time_stop payını %31'den %11'e indirdi. Kapıdan kalmasının ölçülmüş sebebi edge yokluğu değil,
**de-risk rampasının verimi 1 pozisyona indirmesi** ve buna bağlı olarak PARA'nın n<30 yüzünden
**ölçülememesi** (None — "kötü" değil, "bilinmiyor").
**Dikkat:** P3'ün gücünün ne kadarı `early_kill_pivot`'a, ne kadarı P2 mirasına ait olduğu bu ölçümde
**AYRIŞMIYOR** (bileşik ölçüm bu soruyu sormadı — prescreen'in bileşik kuralı 3). sinav3'te (R0, K=4)
tek başına `exit.early_kill_pivot=1` ölçülmüştü: OOS 0,0853→0,1259, PARA 0,1311→0,1999, P=0,659 — aynı
yönde, yine geçmemiş. İki ölçüm birlikte "erken itlaf tekrarlanabilir biçimde iyi ama tek başına çıtayı
geçmiyor" diyor. **Pencereler farklı (R0 vs R1), sayılar yan yana konmamalı.**

### Sıradaki tur için ölçüm önerileri (operatör kararına)

- **A. Rampa ile çıkış birlikte ölçülmeli.** Bu ölçümün en güçlü bulgusu şu: `broker.DERISK_FLOOR_DD`
  (0,08) ve %3'lük rampa başlangıcı **bounds'ta değil, kodda sabit** — yani hipotez makinesi verimi
  belirleyen tek en güçlü parametreyi ne görebiliyor ne ölçebiliyor. Çıkış felsefesi sorusu, rampa
  günlerin %92'sinde açıkken **bağımsız olarak cevaplanamaz**. Öneri: rampa eşiklerini bounds'a taşıyıp
  (ya da en azından ölçüm için sabitleyip) çıkış paketini rampa-sabit koşulda yeniden ölçmek.
- **B. `exit.profit_target_r` alt sınırı.** "Hedefsiz" rejim bugün ölçülemiyor (min 2,0). Sağ kuyruğun
  tam 0,0% ≥3R olduğu bir sistemde bu, ölçülemeyen en pahalı hipotezlerden biri.
- **C. `exit.early_kill_pivot` + `exit.early_kill_bars` R1 penceresinde TEK BAŞINA.** P3'ün imzasını
  hangi düğmenin taşıdığını ayrıştıran tek yol; k_probes'u küçük tutar.

---

## 8. ÖLÇÜM HİJYENİ UYARILARI (iki tanesi bu turun yan bulgusu)

**(1) Canlı state parmak izinde `events.jsonl` "değişti" görünüyor — BENİM KOŞUM DEĞİL.** Kanıt zinciri:
(a) benim `barrepair` olayım SANDBOX `events.jsonl`'a düştü (19:53:34Z `bar_ghost_repair_applied`);
(b) canlıya düşen satırlar SPY için `bar_cache_repaired`/`bar_ghost_session_dropped` — bunlar
`data.load_bars` (fetch) yolundan gelir, benim koşum `dataset.load_cached` kullandığı için o yola **hiç
girmedi**; (c) canlı `state/bars` altında 2026-07-30 02:54'ten yeni **tek dosya yok**.
→ Eş zamanlı ikinci bir yerel süreç canlı state'e yazıyor. Doğrulayıcı: ölçüm bittikten SONRA
(00:39:30 `events.jsonl`, 00:39:38 `sieve.json`) canlı state yazılmaya devam etti; benim iki sürecim de o
saatte ya bitmişti ya yalnız sandbox'a yazıyordu. **prescreen'in "tek bayt yazmadım" kanıtı paralel
oturumlarda kirleniyor** — parmak izi "ben yazdım"ı değil "biri yazdı"yı ölçüyor.

**(2) Ölçüm sürerken repo kodu üçüncü bir oturum tarafından düzenlendi.** `broker.py` 00:34:15,
`adapters/data.py` 00:35:17, `loop.py` 00:33:46, `analytics.py` 00:39:22 — hepsi ölçüm süreçlerinin
**import anından SONRA** (prescreen 22:53:34, throttle sondası 00:01:58 import etti; Python modülleri o
anda dondurur). İki koşu da kendi içinde tutarlı. **Ama prescreen raporunda KOD SÜRÜMÜ DAMGASI YOK** —
pencere damgası (`pencere_id: R1`) var, kod damgası yok. Aynı pencerede iki farklı kod sürümüyle üretilmiş
iki satır bugün ayırt edilemez.

**(3) `sonuc.json → islem_istatistikleri.*.maks_dusus_r` alanının adı yanıltıcı:** değer R değil,
sermayenin **oranıdır** (`score.equity_curve` `pnl_dollars` toplar). Kapının `inc_dd=0,0457` sayısıyla
birebir aynıdır; tabloda "düşüş (kapanmış işlem eğrisi)" diye okundu.
