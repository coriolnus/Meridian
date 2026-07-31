# EDG-2026-004 — MAX / piyango filtresi ölçümü

**Kart:** `research/cards/EDG-2026-004-max-filter.yaml` · aile `max_lottery_avoid_filter` (WP1/1.3)
**Ölçüm:** 2026-07-31, salt-ölçüm sandbox'ı — repo'ya ve `state/`e **hiçbir bayt yazılmadı**
(`config.STATE` sandbox'a çevrildi; `sanitize_bars`ın ürettiği 10 uyarı olayı canlı `events.jsonl`
yerine `_state/events.jsonl`e düştü, doğrulandı).
**Çıktılar:** `sonuc.json` (tam tablo + hüküm), `eslesen_satirlar.csv` (7.122 satırlık ölçüm
tabanı), `robustluk.json`, `kuyruk.json`, `olcum.py` / `robustluk.py` / `kuyruk.py`.

---

## HÜKÜM: **ARŞİV**

Kartın başarı ölçütü iki koşullu bir VE'dir; **ikisi de karşılanmadı** ve iki kill kriterinin
**ikisi de tetiklendi**.

| Kartın istediği | Ölçülen |
|---|---|
| yüksek-MAX dilimin ileri getirisi **anlamlı DÜŞÜK** | **Hiçbir hücrede değil.** 5 ve 10 barda fark CI-0-içi (bilgisiz). 20 barda CI-0-dışı ama **TERS yönde**: yüksek-MAX dilimi **+1.46 puan DAHA İYİ** (p90; CI [+0.66, +2.27]) |
| eleme simülasyonu net beklentiyi **ARTIRIYOR** | **Düşürüyor.** Bar-türevli net beklenti (fwd20 − 10bps): 0.891% → **0.552%** (p90, delta −0.339 puan, CI [−0.527, −0.149], **anlamlı**) |

Kill kriteri #1 ("eleme net beklentiyi düşürüyorsa / kazananları da eliyorsa arşiv") ve
kill kriteri #2 ("dilim farkı CI-0-içi → bilgisiz, arşiv") — **ikisi de doğrulandı**.

**Tez bu popülasyonda yanlış yönde çalışıyor.** Piyango filtresi açılmamalıdır: açılırsa kazanan
adayları eler.

---

## 1. Ölçümün tabanı

| | |
|---|---|
| Popülasyon | cf defterinin **girilen** satırları (`entered=True`, **kılpayı/near_miss DAHİL**) + `cf_open` |
| Eşleşen gözlem | **7.122** (7.053 cf + 69 cf_open) · 1.014 gün · 250 sembol · 2022-01-03 → 2026-07-28 |
| Eleme muhasebesi | bar_yok_sembol 0 · bar_yok_tarih 0 · max21_NaN 0 · kesit_eşiği_yok 0 → **kayıp sıfır** |
| Barlar | `data.sanitize_bars` (takvim kapısı): **428 hayalet-seans satırı düştü**, 13 satır karantina, 0 seri takvim-reddi. 250/251 sembol (FISV'nin yerel önbelleği yok; cf defterinde hiç geçmiyor) |
| `feat_max21` | `max(close[t]/close[t−1]−1)`, pencere **[t−20, t]** — sinyal barı dahil, nedensel |
| `feat_max21_excl` | aynı büyüklük, pencere **[t−21, t−1]** — sinyal gününün kendi patlaması dışlanmış kontrol |
| İleri getiri | `close[t+h]/close[t]−1`, h ∈ {5,10,20} — `component_ic.forward_returns` ile **aynı tanım** |
| Eşik (birincil) | **gün-bazlı EVREN KESİTİ p90/p95** (as-of; o günün 250-sembollük kesitinin yüzdeliği) — canlıda uygulanabilir, ileri bakmaz. Medyan eşik: p90 = %6.58, p95 = %8.42 günlük getiri |
| Eşik (duyarlılık) | popülasyon-içi havuzlanmış p90/p95 — eşik tüm örneklemi gördüğü için **ileri bakar**, hüküm buna dayandırılmadı |
| CI | **tarih-kümeli blok bootstrap** (yeniden örnekleme birimi GÜN, 2.000 tekrar, %95 persentil) |
| Maliyet | 10bps gidiş-dönüş (`goal.yaml slippage_bps=5` × iki bacak) |

**Neden tarih-kümeli CI:** aynı günde onlarca aday satırı var ve bunlar bağımsız değil.
`component_ic`in Fisher-z aralığı bu yüzden kendi docstring'inde "bir ALT SINIR" olarak
etiketlenmişti; burada bootstrap'ın birimi satır değil **gün**.

---

## 2. POZİTİF KONTROL — boru hattı doğrulandı ✅

Aynı yükleyici, aynı eşleştirme, aynı ileri-getiri tanımı ile bilinen ilişki yeniden üretildi:

| Popülasyon | ufuk | IC | n | tarih-kümeli CI | anlamlı |
|---|---|---|---|---|---|
| component_ic'nin cf katmanı (near_miss hariç) | 20 | **0.0645** | 2.094 | [+0.019, +0.107] | ✅ |
| " | 10 | 0.0499 | 2.100 | [+0.002, +0.102] | ✅ |
| " | 5 | 0.0364 | 2.102 | [−0.009, +0.086] | ✗ |

Kart pozitif kontrolü **rvol20 @20 IC ≈ 0.065** bekliyordu → **0.0645**.
`state/component_ic.json`daki değer 0.0604 ve **n değerleri (2102/2100/2094) birebir aynı** — yani
popülasyon ve eşleştirme aynı, küçük IC farkı barların artık takvim-kapılı olmasından geliyor
(defterdeki artefakt 2026-07-30 00:10'da, kapının indiği gün üretilmiş). Boru hattı temiz.

---

## 3. (a) Dilim kıyası — yüksek-MAX vs kalan

**Evren kesiti eşiği (birincil).** Fark = yüksek-MAX dilimin ortalaması − kalan dilimin ortalaması.

| eşik | ufuk | n_yüksek | n_kalan | ort. yüksek | ort. kalan | **fark** | CI (tarih-kümeli) | anlamlı |
|---|---|---|---|---|---|---|---|---|
| p90 | 5 | 1.641 | 5.429 | +0.13% | +0.09% | +0.04 pp | [−0.32, +0.42] | ✗ |
| p90 | 10 | 1.635 | 5.412 | +0.69% | +0.35% | +0.34 pp | [−0.18, +0.89] | ✗ |
| p90 | **20** | 1.627 | 5.382 | **+2.11%** | **+0.65%** | **+1.46 pp** | **[+0.66, +2.27]** | ✅ **TERS YÖN** |
| p95 | 5 | 992 | 6.078 | +0.10% | +0.10% | +0.01 pp | [−0.45, +0.49] | ✗ |
| p95 | 10 | 990 | 6.057 | +0.57% | +0.40% | +0.17 pp | [−0.50, +0.85] | ✗ |
| p95 | **20** | 983 | 6.026 | **+2.12%** | **+0.81%** | **+1.31 pp** | **[+0.26, +2.40]** | ✅ **TERS YÖN** |

**Duyarlılık eşikleri.** Popülasyon-içi havuzlanmış eşikte **hiçbir hücre anlamlı değil**
(p90@20 +1.17 pp, CI [−0.22, +2.53]); sinyal gününü dışlayan `feat_max21_excl` tanımında da
**hiçbir hücre anlamlı değil** (p90@20 +0.71 pp, CI [−0.72, +2.14]). Üç eşik tanımının üçünde de
"anlamlı DÜŞÜK" hücre sayısı **sıfır**.

**Sürekli IC (tam popülasyon):**

| tanım | @5 | @10 | @20 |
|---|---|---|---|
| feat_max21 (t dahil) | −0.010 [−0.039, +0.019] | +0.018 [−0.015, +0.051] | **+0.047 [+0.012, +0.080]** ✅ |
| feat_max21_excl (t hariç) | −0.013 [−0.046, +0.016] | +0.021 [−0.013, +0.047] | +0.026 [−0.006, +0.059] ✗ |

**Beşlik tablosu (fwd20) — ortalama monoton değil, medyan hiç değil:**

| MAX beşliği | aralık | n | ort. fwd20 | medyan fwd20 |
|---|---|---|---|---|
| 1 (en düşük) | ≤2.81% | 1.402 | +0.21% | +0.30% |
| 2 | 2.81–3.92% | 1.403 | +0.70% | +0.82% |
| 3 | 3.92–5.16% | 1.402 | +0.20% | +0.46% |
| 4 | 5.16–7.42% | 1.400 | +1.92% | **+1.50%** |
| 5 (en yüksek) | ≥7.42% | 1.402 | **+1.93%** | +0.66% |

En yüksek beşliğin **ortalaması** 4. beşlikle aynı ama **medyanı yarısından az** — klasik piyango
dağılım şekli (kalın sağ kuyruk, düşük tipik sonuç). Kısa ufukta bu daha da net: fwd5'te 5. beşliğin
medyanı **−0.29%** iken 4. beşliğin +0.46%.

---

## 4. (b) Eleme simülasyonu

Popülasyon: **7.053 kapalı cf satırı** (çıkışlar: time_stop 3.194 · stop 2.674 · target 605 ·
stop_gap 437 · target_gap 143).

### Evren kesiti p90 (%23.2'yi eler, n=1.638)

| ölçüt | taban | **filtreli** | elenenler | delta | CI | anlamlı |
|---|---|---|---|---|---|---|
| **bar-türevli net beklenti (fwd20−10bps)** | +0.891% | **+0.552%** | +2.013% | **−0.339 pp** | [−0.527, −0.149] | ✅ **kötüleşme** |
| net R (r_multiple − maliyet) | +0.0205 | **+0.0012** | +0.0842 | −0.0193 | [−0.0402, +0.0006] | ✗ (yön aynı) |
| stop-ölüm oranı | 44.11% | 44.67% | 42.25% | +0.56 pp | [−0.17, +1.32] | ✗ |
| **false-breakout** (stop ∧ mfe<0.5R) | 29.12% | 29.51% | **27.84%** | +0.39 pp | [−0.28, +1.00] | ✗ |
| kazanan oranı | 44.22% | 43.93% | 45.18% | −0.29 pp | [−0.99, +0.45] | ✗ |

**Elenen dilim tüm kazananların %23.7'sini ve tüm hedef-çıkışlarının %27.9'unu içeriyor**, kendi
payı ise %23.2 — yani kazananlar arasında hafifçe **fazla** temsil ediliyor.

### Evren kesiti p95 (%14.0'ünü eler, n=990)

| ölçüt | taban | filtreli | delta | CI | anlamlı |
|---|---|---|---|---|---|
| bar-türevli net beklenti (fwd20−10bps) | +0.891% | **+0.707%** | **−0.184 pp** | [−0.332, −0.038] | ✅ **kötüleşme** |
| net R | +0.0205 | +0.0201 | −0.0005 | [−0.0143, +0.0131] | ✗ |
| false-breakout | 29.12% | 29.11% | −0.01 pp | [−0.47, +0.44] | ✗ |

### Popülasyon-havuzu eşiği (duyarlılık)
p90 ve p95'te **hiçbir ölçüt anlamlı değil**; fwd20 deltası yine negatif (−0.118 pp / −0.020 pp).

**Sonuç:** eleme, kartın istediği yönde **hiçbir şey** iyileştirmiyor. False-breakout oranını
düşürmüyor (elenen dilimin false-breakout oranı zaten **daha düşük**), net beklentiyi ise iki
eşikte de anlamlı biçimde **düşürüyor**.

---

## 5. Yan bulgu (tez-karşıtı) — torun-kart adayı, filtre adayı DEĞİL

`feat_max21` @20 barda **pozitif** ve zayıf bir sinyal taşıyor: IC **+0.047** (n=7.009,
CI [+0.012, +0.080]) — aynı popülasyondaki rvol20'nin IC'siyle (+0.041) aynı büyüklükte.

**rvol20'nin kılığı değil:** rvol20 beşliklerinin **beşinde de** max21 IC'si pozitif kalıyor
(rvol beşliği 1→5: +0.042 / +0.039 / +0.029 / +0.059 / +0.040; her biri tek başına n≈1.400'de
anlamlı değil ama işaret istikrarlı). ret1 (sinyal-günü getirisi) beşliklerinde de aynı: +0.005 … +0.059, hiçbiri
negatif değil.

**Ama dört ihtiyat kaydı, hepsi hükmü zayıflatıyor:**

1. **Medyanda yok.** @20 medyan farkı +0.63 pp, CI [−0.12, +1.40] — anlamsız. Etki ortalamada.
   Kuyruk kontrolü: %1 winsorize edilmiş ortalama farkı +1.15 pp (CI [+0.43, +1.82]) ve en büyük
   5 gözlem atıldığında +1.20 pp (CI [+0.42, +2.04]) — yani **birkaç aykırı değere yaslanmıyor**,
   ama dağılımın üst yarısında yaşıyor.
2. **Sinyal gününe bağımlı.** `feat_max21_excl` (t hariç) tanımında IC +0.026'ya iniyor ve CI
   sıfırı kapsıyor. `spearman(max21, ret1) = 0.53` — ölçtüğümüz şeyin yarısı "kırılma gününün
   kendisi büyüktü".
3. **Dönem kırılgan.** Yıl kesitinde yalnız **2023** tek başına anlamlı (+1.73 pp, CI [+0.65, +2.71]);
   2022 düz (−0.04 pp), 2024/2025/2026 pozitif ama CI-0-içi. Rejimde chop (+2.43 pp ✅) ve
   trend_up (+1.31 pp ✅) anlamlı, high_vol değil. Kurulumda breakout_vcp anlamlı, momentum_burst değil.
4. **Alt-popülasyonlarda tutarlı** (kılpayı +1.61 pp ✅ / girilen +1.21 pp ✅) — bu tek olumlu not.

Kısa ufukta ise tezin **medyan izi** var: p95 eşiğinde fwd5 **medyan** farkı −0.53 pp
(CI [−0.84, −0.16], **anlamlı negatif**) ama ortalama farkı sıfır. Yüksek-MAX adayın *tipik*
sonucu bir hafta içinde biraz daha kötü, sağ kuyruğu ise bunu fazlasıyla telafi ediyor — Bali'nin
mekanizmasının şekli görülüyor, ama **stop + 2.5R hedefli long-only bir kırılma stratejisi tam da
o sağ kuyruğu hasat ediyor**, bu yüzden kaçınma filtresi burada zarar veriyor.

---

## 6. Caveatlar

- **Survivorship (en ağırı).** `REPLAY_UNIVERSE` (251) BUGÜNÜN üyeliğidir ve 2022'ye geriye
  uygulanır; dönem içinde düşmüş isimler ne bar evreninde ne cf defterinde var. Hem günlük eşik
  kesiti hem popülasyon aynı hayatta-kalanlar kümesinden geliyor. Piyango etkisinin literatürde en
  güçlü olduğu dilim (küçük, oynak, ölen isimler) **burada yok**. Bu, "MAX filtresi bu evrende işe
  yaramıyor" hükmünü destekler; **"MAX etkisi yoktur" hükmüne izin vermez.**
- **Kıyas-kirlenmesi (EAP yan-bulgusu).** Evren-medyanı kıyası **kullanılmadı**; tüm
  karşılaştırmalar dilimler-arası (aynı popülasyon, aynı günler, aynı getiri tanımı). Eşik de gün
  bazlı evren kesitinden geldiği için rejim kayması (herkesin MAX'ının yükseldiği oynak dönemler)
  eşiğe zaten girmiş oluyor.
- **cf defterinin sınırları.** Satırlar alınmamış hipotetik girişlerdir (seçim yanlılığı açık) ve
  defter replay-tohumludur (AUDIT-2026-07-31 BT-1). (a) analizinin y ekseni **barlardan** gelir →
  `cf.advance`in çıkış-sadakati kusurundan (`analytics.CF_EXIT_FIDELITY_NOTE`) etkilenmez.
  (b) analizinin **R-tabanlı** kolu bu kusuru taşır; hüküm bu yüzden **bar-türevli** koldan verildi,
  R kolu yanında durur (ikisi aynı yönde).
- **Bar kapısı.** 428 hayalet satır düştü, 13 satır karantinada, 0 takvim-reddi. FISV (251. sembol,
  evrene 2026-07-30'da girdi) yerel önbellekte yok; cf defterinde hiç geçmiyor.
- **Çoklu test.** 2 eşik × 3 ufuk × 3 eşik-tanımı = 18 dilim hücresi + IC tabloları ölçüldü;
  kart K=2 beyan ediyor, düzeltme uygulanmadı. Anlamlı çıkan hücrelerin **hepsi** 20 barda ve
  **hepsi ters yönde** — bu yüzden pozitif yan-bulgu hüküm değil, torun-kart adayıdır.
- **Literatür.** Birinci-el Bali-Cakici-Whitelaw (2011) makalesi bu katalog turunda çekilmedi
  (kart caveat'i). Hüküm literatür-bağımsızdır, kendi verimizde ölçüldü. Ters işaret literatürü
  yanlışlamaz: oradaki etki **tüm evren** kesitinde ölçülür, buradaki popülasyon ise zaten
  "kırılma adayı olmak" üzerine koşullanmıştır.

---

## 7. Öneri

1. **EDG-2026-004 → `status: archived`.** Kart hükmü: kaçınma filtresi açılmaz.
   `kill_criteria`nın ikisi de tetiklendi; `success_metric`in iki bacağı da karşılanmadı.
2. **Torun-kart adayı (yeni kart olarak kaydedilebilir, bu turda ölçüm YOK):** "feat_max21 @20 bar
   POZİTİF yönde zayıf bir bileşen mi?" — ölçülmesi gereken şey, sinyal-günü getirisi ve rvol20
   kontrol edildikten sonra **artık bilgi** kalıp kalmadığıdır (buradaki tek-değişkenli beşlik
   kontrolleri bunun yerine geçmez) ve etki 2023-dışı yıllarda ayakta mı. Bu kart açılırsa
   **K-sayacına yazılmalıdır** — burada aynı veriye bakıldığı için yeni bir kartın örneklemi
   bağımsız değildir.
3. **`component_ic.json` yeniden üretilmeli.** Bu ölçüm, takvim-kapılı barlarla rvol20 cf@20
   IC'sinin 0.0604 → 0.0645 kaydığını gösterdi. Defterdeki artefakt kapının indiği gün üretilmiş;
   AUDIT-2026-07-31 BT-2'nin "türetilmiş artefaktlar yeniden üretilecek" maddesi hâlâ açık.
