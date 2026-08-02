# EDG-2026-020 — POST-EVENT in-play (PIT-temiz tek-yönlü) · ÖLÇÜM RAPORU

- Kart: `research/cards/EDG-2026-020-postevent-inplay.yaml` · aile `postevent_inplay`
- Ölçüm zamanı: `2026-08-02T20:18:26.168892+00:00` · sandbox: `research/olcumler/inplay_postevent/`
- Kod damgası: git `b8ed076` · kirli_ağaç **True** · olcum_araclari `2026-08-02` (temiz_taban:1.0, olay_disi_kiyas:1.0, blok_bootstrap_ci:1.0, eb_kucult:1.0)
- Mühür: `config.STATE` = `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/inplay_postevent_calisma/_state` — canlı `state/`e **hiçbir yazım yok**; barlar canlı önbellekten SALT-OKUNUR.

> Bu rapordaki her sayı `sonuc_020.json` / `pk_020.json`dan okunur (rapor elle yazılmaz).
> **Ölçüm ajanı karta DOKUNMADI ve HÜKÜM VERMEDİ.** §11 kill/success ölçütlerinin KARŞILIKLARINI tablo olarak verir; hükmü Rol-1 işler.

**KAPI SATIRI:** pozitif kontrol EVET · PIT-assert EVET · PK4 EVET · PK5 EVET

---

## 1 · Kart metninin uygulaması (ne ölçüldü)

| kalem | uygulama |
|---|---|
| popülasyon | cf-katmanlı **aday** havuzu: `counterfactuals.jsonl` entered=True (near_miss DÂHİL) + `cf_open.json`; TEKİL (ticker, date) — EDG-011 ile birebir |
| dilim | `in_play(0 <= t−e <= 3 takvim günü, YALNIZ e<=t) ∧ rvol20>=1.5` (P grid'den gelir) |
| in_play kapısı | **YAPISAL**: olay dizisi t'de kesilir (`ev[:j]`, searchsorted right); gelecek tarih okunmuyor değil — **okunamıyor** (§4) |
| rvol20 | `meridian.indicators.rvol20` — canlı tanımla BİREBİR (SMA20; EDG-017 dersi) |
| taban | **AYNI-GÜN aday havuzunun in_play-DIŞI satırlarının ortalaması** (kart horizon). Hedef satır yapısal olarak kendi tabanında DEĞİL (Ders #5 k.1 kendiliğinden sağlanır) |
| fazla | `fwd_h − o günün tabanı`. **HAM getiri hükme girmez** (Ders #3) — betimleyici sütun |
| ileri getiri | `close[t+h]/close[t] − 1`, takvim-kapılı + `bars_integrity` dışlamalı seri |
| CI | 21g **HAREKETLİ BLOK** bootstrap %95, 2000 tekrar (Ders #6 — IID YASAK) |
| maliyet | tek-yön bps, fazladan DÜŞÜLÜR. Kart cost_model: '10bps + 20bps duyarlılık; olay-sonrası spread-genişlemesi beyan-notu'. BEYAN-NOTU: kazanç sonrası ilk günlerde spread GENİŞLER ve gerçek maliyet 10bps'in ÜSTÜNDE olabilir; bu ölçümde spread verisi YOK, dolayısıyla 20bps satırı bir ÜST OKUMA değil yalnız bir duyarlılıktır. |
| K muhasebesi | grid `pencere_gun ∈ [3, 5]` → **K = 2**; kutup: FWER (kapı p_req = 1 − α_family/K, gerçek Bonferroni). Bu ölçüm kapıya DOKUNMAZ; kutbu yalnız beyan eder. |
| grid DIŞI satırlar (K harcamaz) | alt-dönem (betimleyici), @5 (betimleyici), min_taban=5 (duyarlılık), kirli-taban sıkışma (Ders #5 k.3), kontrolsüz artık-IC ikizi |
| min_taban | **ÖLÇÜM ÖNCESİ BEYAN**: birincil `1` (kartın harfi: 'havuz ortalaması'); `min_taban=5` yalnız DUYARLILIK satırıdır ve HÜKME GİRMEZ |

## 2 · Veri zemini

| kalem | değer |
|---|---|
| bar sembolü yüklendi | 248 / 251 |
| hayalet seans düşen satır | 428 |
| düzeltilmemiş karantina | 13 |
| `bars_integrity` **defter yolu** düşen satır | 46256 (57 sembol) |
| `bars_integrity` **hesaplanan yol** ek dışlanan satır | 0 |
| iki yolun ayrıştığı sembol | 0 |
| cf defteri satırı | 7161 (girilmemiş 108) · cf_open 69 |
| ham aday satırı | 7122 · tekilleştirmede düşen 315 |
| **tekil aday-gün** | 6807 · **bar eşleşen 6764** |
| havuz gün sayısı | 1014 · gün başına aday medyan 5.0 |
| rvol20 ölçülemeyen aday-gün | 0 |
| **geçmiş olayı olmayan** aday-gün (in_play tanım gereği False) | 183 |

## 3 · Olay takvimi — kanıt ARŞİVDE (EDG-016 dersi)

Kaynak: Nasdaq anahtarsız takvim (adapters.data.nasdaq_earnings_window) — kys_olcum/takvim_cek.py ile çekildi, bu klasöre ARŞİVLENDİ. Kanıt dosyaları **bu klasörde**: `takvim_kaniti/` (scratchpad'de bırakılmadı — kart guard'ı: 'olay-takvimi kanıtı ölçüm klasörüne arşivlenir').

| kalem | değer |
|---|---|
| sorulmuş iş günü (JSONL satırı) | 1198 · bozuk satır 0 |
| gün aralığı | 2022-01-03 … 2026-08-05 |
| sembol | 251 · olay-günü 4687 · sembol başına medyan 19.0 |
| saat (bmo/amc) alanı | YOK — takvim_cek.py:74 bmo/amc'yi süzüyor (keşif turu şerhi) |

**Arşiv dosyaları (sha256):**

| dosya | satır | sha256 |
|---|---|---|
| `takvim_kaniti/gunler.jsonl` | 43 | `ad27e737f3788953cf5684576bb3b2e2…` |
| `takvim_kaniti/gunler_a.jsonl` | 259 | `202445773ca4d9b3e050f9ea7f8bbfba…` |
| `takvim_kaniti/gunler_b.jsonl` | 305 | `baa9577f49bdf450a3f6f0f95e304a5d…` |
| `takvim_kaniti/gunler_c.jsonl` | 304 | `c2239b80c23a32d34873e305ba0f8597…` |
| `takvim_kaniti/gunler_d.jsonl` | 287 | `8f74bbafef52508e505b66a82c637063…` |

> **Kapsam şerhi (keşif turundan devralındı):** bu eksen **ex-post**tur — geçmiş bir kazanç
> günü kamusal bir olgudur ve `e ≤ t` dalında PIT-güvenlidir; kaynağın vermediği şey
> **duyuru-öncesi bilinirlik**tir ve bu kart onu ZATEN istemiyor (tek-yönlü form).
> Nasdaq önbelleğinin `bmo/amc` alanı `takvim_cek.py:74`te süzülmüştür; bu ölçüm saat
> bilgisi KULLANMAZ, dolayısıyla eksiklik hükme dokunmaz ama beyan edilir.

## 4 · PIT KANITI — kartın en sert guard'ı

> Kart guard'ı harfiyen: *"PIT: yalnız e≤t; gelecek-tarih okuyan tek satır bile ihlaldir
> (test/assert ile çivilenir)"*. Üç bağımsız bacak + bir negatif kontrol koşuldu.

| bacak | tanım | ölçü | geçti |
|---|---|---|---|
| 1 · YAPISAL | gecikme_gunu: searchsorted(side='right') → ev[:j] dilimi; yalnız o dilimin SON öğesi okunur. j==0 satırlarda diziye HİÇ dokunulmaz (maskeli indeksleme). | satır-başı assert tetiklenme: 0 | EVET |
| 2 · KESME-DEĞİŞMEZLİĞİ | Her satır için takvim O SATIRIN t'sinde KESİLİR (ev[ev<=t]) ve gecikme yeniden hesaplanır. Fark 0 ⇒ gelecek tarihlerin sonuca katkısı SIFIR. | n=6764 (**alt örnek DEĞİL**), ayrışan **0** | EVET |
| 3 · BAĞIMSIZ İKİZ | gecikme_gunu_saf (liste taraması, ayrı kod yolu) ile birebir aynı sayı. | n=6764, ayrışan **0** | EVET |
| NEGATİF KONTROL | İKİ YÖNLÜ (EDG-011'in \|t−e\| lafzı) hesap kaç satırda FARKLI sayı verirdi? 0 çıksaydı kapı hiçbir şeyi kesmiyor demekti ve 'PIT-temiz' beyanı boş olurdu. BU SAYI HÜKME GİRMEZ ve in_play hesabında KULLANILMAZ. | farklı sayı verecek satır: **2935** (havuzun %43.4'i) | kapı ETKİN: EVET |

**Okuma.** Bacak 2 asıl kanıttır: takvim her satırın kendi `t`'sinde fiziksel olarak kesildiğinde sonuç **0** satırda değişti — yani gelecek tarihlerin sonuca katkısı sıfırdır. Negatif kontrol bunun tavtoloji olmadığını gösterir: EDG-011'in iki-yönlü `|t−e|` lafzı uygulansaydı havuzun **%43.4**'inde farklı bir sayı çıkardı — kapı gerçekten bir şey kesiyor.

Kapsama: aday satırı 6764 · takvimde olmayan sembol satırı **0** (EDG-011'deki 1669 kapsam-dışı aday-gün sorunu bu kaynakla BİTTİ) · geçmiş olayı olmayan satır 183.

**PEAD tarafında aynı yön sözleşmesi:** `evaluate_pead`in çapası `earnings.days_since_report` ve o da yapısal olarak tek yönlüdür (`earnings.py:193` → `0 <= (d − e).days <= max_days`) — ölçümün iki bacağı da `e ≤ t` dalındadır.

## 5 · Pozitif kontrol + PK4 + PK5

**Çivi (kart guard'ı):** counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı)

| h | IC | n | CI | anlamlı |
|---|---|---|---|---|
| 5 | 0.0374 | 2095 | [-0.0178, +0.0847] | hayır |
| 10 | 0.0516 | 2093 | [-0.0089, +0.1011] | hayır |
| 20 | 0.0642 | 2087 | [+0.0146, +0.1135] | EVET |

**Çivi:** ölçülen `0.0642` · hedef `0.0645` · sapma `0.0003` · tolerans `0.005` → **GEÇTİ: EVET**

Defterdeki referans (`state/component_ic.json`, cf/rvol20): {'5': 0.032, '10': 0.0456, '20': 0.0604}

### 5.1 PK4 — yol tutarlılığı

> close[t+h]/close[t]-1 ile aradaki GÜNLÜK getirilerin bileşiği ÖZDEŞ olmalı. Takvim kapısı / integrity kırpması ufkun İÇİNDE bar düşürdüyse ya da kaydırma bir gün kaysaydı özdeşlik bozulurdu. · kapsam: pozitif kontrol satırları + TÜM bar paneli (her sembol, her bar)

| ufuk | n | maks mutlak fark | geçti |
|---|---|---|---|
| 5 | 1258029 | 0.0 | EVET |
| 10 | 1256766 | 0.0 | EVET |
| 20 | 1254248 | 0.0 | EVET |

### 5.2 PK5 — özdeşlikler

| sınama | ölçü | geçti |
|---|---|---|
| A · rvol20 geriye-bakışsız | n=32, maks fark 0.0 | EVET |
| C · hızlı ortalama-bootstrap özdeşliği | n=50, maks fark 0.0 | EVET |
| E · hızlı Spearman ≡ kanonik | 3 ölçüm, maks fark 0.0 | EVET |
| F · in_play ≡ `temiz_taban(pencere=(0,3))` tümleyeni | ayrışan 0; kanonik in_play 951 · birim `takvim gunu` | EVET |
| F · in_play ≡ `temiz_taban(pencere=(0,5))` tümleyeni | ayrışan 0; kanonik in_play 1137 · birim `takvim gunu` | EVET |
| G · takvim yükleyici ≡ `earnings._load()` | sembol 251/251, ayrışma 0+0 | EVET |
| **PK5 toplam** | — | **EVET** |

> **KAPSAM BEYANI (uygulanmayan bekçi 'geçti' diye yazılmaz):** WP2 dalgasının PK5-B (split bazı) ve PK5-D (fundamentals as-of) bacakları BU KARTTA UYGULANMADI — kart yalnız OHLCV + olay TARİHİ kullanır, hiçbir fundamentals/as-of serisi okumaz.

## 6 · Ders #4 — kıyas temizliği muhasebesi (`temiz_taban`, KANONİK)

| P | pencere | gün birimi | n_toplam | n_temiz | n_kirli | kirlilik_oranı | n_çözülemeyen | n_olaysız_kimlik | uyarı |
|---|---|---|---|---|---|---|---|---|---|
| 3 | (0, 3) | takvim gunu | 6764 | 5813 | 951 | 0.1406 | 0 | 0 | — |
| 5 | (0, 5) | takvim gunu | 6764 | 5627 | 1137 | 0.1681 | 0 | 0 | — |

> Pencere `(0, P)` KANONİK `olcum_araclari.temiz_taban` aritmetiğinde `0 ≤ (gün − olay) ≤ P` demektir — bu kartın `in_play` tanımının TA KENDİSİ. PK5-F bu özdeşliği sıfır ayrışmayla sınadı, yani taban tanımı deponun kanonik pencere aritmetiğinden SAPMIYOR.

## 7 · İKİ HÜCRE (K=2) — dilim sayıları

| P | in_play aday-gün | **dilim** (∧ rvol≥1.5) | havuz | tarih aralığı | gecikme dağılımı (t−e) |
|---|---|---|---|---|---|
| 3 | 951 | **729** | 6764 | 2022-01-14 … 2026-07-28 | 0g:390 · 1g:379 · 2g:119 · 3g:63 |
| 5 | 1137 | **791** | 6764 | 2022-01-14 … 2026-07-28 | 0g:390 · 1g:379 · 2g:119 · 3g:63 · 4g:77 · 5g:109 |

> **EDG-011 ile fark:** orada in-play dilimi 11-12 aday-gündü ve tamamı verinin son haftasındaydı (kill#3 askısı). Tarihsel takvimle dilim iki mertebe büyüdü ve **tüm defter penceresine yayıldı** — 011'in askı sebebi (örneklem kuraklığı) bu kartta YOK.

## 8 · FAZLA TABLOSU + CI

Fazla = aday getirisi − **aynı-gün aday-havuzu (in_play-DIŞI)** ortalaması. CI = 21g hareketli blok bootstrap %95.

### P = 3

| h | n | ham ort _(betimleyici)_ | **havuz fazlası** | **fazla CI** | CI 0'ı kapsıyor | poz. anlamlı | net@10bps | net@20bps | n_taban_yok |
|---|---|---|---|---|---|---|---|---|---|
| 5 _(betimleyici)_ | 649 | -0.099% | **-0.324%** | **[-0.808%, +0.130%]** | EVET | hayır | -0.424% | -0.524% | 70 |
| 10 **(hüküm ufku)** | 647 | +0.356% | **-0.482%** | **[-1.106%, +0.303%]** | EVET | hayır | -0.582% | -0.682% | 70 |
| 20 **(hüküm ufku)** | 646 | +1.122% | **-0.620%** | **[-1.300%, +0.512%]** | EVET | hayır | -0.720% | -0.820% | 70 |

**Duyarlılık ve muhasebe satırları (HÜKME GİRMEZ):**

| h | min_taban=5 fazla | min_taban=5 CI | n | sıkışma (temiz − kirli taban) | dilim günlerinin taban ort. | havuz geneli (in_play-dışı) |
|---|---|---|---|---|---|---|
| 5 | -0.090% | [-0.598%, +0.612%] | 370 | -0.127% | +0.226% | +0.097% |
| 10 | -0.180% | [-0.891%, +0.819%] | 370 | -0.237% | +0.838% | +0.442% |
| 20 | -0.315% | [-1.138%, +1.274%] | 370 | -0.293% | +1.742% | +0.954% |

### P = 5

| h | n | ham ort _(betimleyici)_ | **havuz fazlası** | **fazla CI** | CI 0'ı kapsıyor | poz. anlamlı | net@10bps | net@20bps | n_taban_yok |
|---|---|---|---|---|---|---|---|---|---|
| 5 _(betimleyici)_ | 696 | -0.030% | **-0.348%** | **[-0.681%, +0.057%]** | EVET | hayır | -0.448% | -0.548% | 84 |
| 10 **(hüküm ufku)** | 694 | +0.429% | **-0.532%** | **[-1.000%, +0.157%]** | EVET | hayır | -0.632% | -0.732% | 84 |
| 20 **(hüküm ufku)** | 693 | +1.193% | **-0.733%** | **[-1.232%, +0.299%]** | EVET | hayır | -0.833% | -0.933% | 84 |

**Duyarlılık ve muhasebe satırları (HÜKME GİRMEZ):**

| h | min_taban=5 fazla | min_taban=5 CI | n | sıkışma (temiz − kirli taban) | dilim günlerinin taban ort. | havuz geneli (in_play-dışı) |
|---|---|---|---|---|---|---|
| 5 | -0.086% | [-0.531%, +0.386%] | 400 | -0.178% | +0.318% | +0.095% |
| 10 | -0.188% | [-0.817%, +0.600%] | 400 | -0.310% | +0.961% | +0.446% |
| 20 | -0.149% | [-0.853%, +1.149%] | 400 | -0.460% | +1.926% | +0.964% |

> **Ders #3 okuması (sayı, hüküm değil).** İki pencerede de @20 **HAM** getiri POZİTİFtir (+1.122% / +1.193%) ama taban-fazlası NEGATİFtir. Sebep tabloda duruyor: dilim günlerinin AYNI-GÜN tabanı (+1.926%), havuzun genel ortalamasının (+0.964%) yaklaşık iki katıdır — kazanç-sonrası günler havuzun TAMAMININ iyi olduğu günlerdir. Ham getiriyle ölçen bir ölçüt burada 'kenar var' derdi.

> **Sıkışma (Ders #5 k.3).** Kirli tabanla (o günün TÜM satırları, in_play dâhil) kurulan kıyas fazlayı sistematik olarak **yukarı** kaydırıyor; fark sütunu düzeltmenin büyüklüğünü gösterir. Kirli taban HÜKME GİRMEZ.

## 9 · Alt-dönem satırı (BETİMLEYİCİ — grid'e dahil DEĞİL, K harcamaz)

**P = 3 · @20**

| yıl | aday-gün | n (dilim) | fazla | CI | gözlem günü | CI yoksa neden |
|---|---|---|---|---|---|---|
| 2022 | 1109 | 97 | -2.144% | — | 55 | gözlem günü sayısı < 63 (blok bootstrap için yetersiz) |
| 2023 | 1532 | 130 | +0.510% | [+0.235%, +1.620%] | 65 | — |
| 2024 | 1728 | 214 | -0.259% | [-0.800%, +0.894%] | 97 | — |
| 2025 | 1387 | 127 | +1.364% | [-0.380%, +1.913%] | 76 | — |
| 2026 | 1008 | 78 | -4.831% | — | 34 | gözlem günü sayısı < 63 (blok bootstrap için yetersiz) |

**P = 5 · @20**

| yıl | aday-gün | n (dilim) | fazla | CI | gözlem günü | CI yoksa neden |
|---|---|---|---|---|---|---|
| 2022 | 1109 | 110 | -1.827% | — | 59 | gözlem günü sayısı < 63 (blok bootstrap için yetersiz) |
| 2023 | 1532 | 137 | +0.049% | [-0.490%, +1.169%] | 70 | — |
| 2024 | 1728 | 220 | -0.683% | [-1.323%, +0.352%] | 101 | — |
| 2025 | 1387 | 143 | +1.295% | [-0.290%, +1.619%] | 84 | — |
| 2026 | 1008 | 83 | -4.196% | — | 35 | gözlem günü sayısı < 63 (blok bootstrap için yetersiz) |

> 2022 ve 2026 dilimlerinde CI **ölçülemedi** (gözlem günü < 63 = 3×blok); boş bırakılmadı, nedeni yazıldı. İşaret yıllar arasında **dönüyor** — kararlılık yok.

## 10 · PEAD-AYRIŞMASI (kartın varlık gerekçesi · kill#2 verisi)

> Kartın varlık gerekçesi: bu eksen evaluate_pead'den AYRIŞAN bilgi taşıyor mu? İki bacak: (1) küme ÖRTÜŞMESİ (Jaccard), (2) pead-KONTROLLÜ artık (çift-sıralama + artık-IC, EDG-016 şablonu).

**`evaluate_pead` SANDBOX'ta koşturuldu** (motorun kendi fonksiyonu ÇAĞRILDI, kopyalanmadı): 6764 aday-gün çağrısı, **104 ateşleme**, hata 0, bar-kısa 0. Bar dilimi motorla birebir (`backtest.py:320` `tail(340)`); RS çapraz-kesiti `indicators.rs_rating` ile 1014 günde kuruldu (kesit medyanı 248.0 sembol). Parametreler `state/strategy.yaml` v3 (18 anahtar); pead anahtarları dosyada yok → motor varsayılanları: {'pead.watch_days': 35, 'pead.min_gap_pct': 3.0, 'pead.min_volume_ratio': 1.2}.

> **NEDEN YENİDEN KOŞULDU.** Canlı cf defterinde `pead` satırı **SIFIRDIR** (setup dağılımı: breakout_vcp / momentum_burst / pullback / episodic_pivot). Sebep veri: replay sırasında `state/earnings.csv` yalnız ileriye-dönük tek anlık görüntüydü, dolayısıyla `days_since_report` daima False döndü ve pead hiç ateşlemedi. Örtüşme sorusu ancak değerlendiriciyi TARİHSEL takvimle yeniden koşturarak sorulabilirdi.

### 10.1 Küme örtüşmesi (Jaccard)

| P | küme A | n_A | n_B (pead) | kesişim | birleşim | **Jaccard** | A'nın B'de payı | B'nin A'da payı |
|---|---|---|---|---|---|---|---|---|
| 3 | dilim (in_play∧rvol) | 729 | 104 | 16 | 817 | **0.019584** | 0.021948 | 0.153846 |
| 3 | yalnız in_play | 951 | 104 | 17 | 1038 | **0.016378** | 0.017876 | 0.163462 |
| 5 | dilim (in_play∧rvol) | 791 | 104 | 20 | 875 | **0.022857** | 0.025284 | 0.192308 |
| 5 | yalnız in_play | 1137 | 104 | 23 | 1218 | **0.018883** | 0.020229 | 0.221154 |

### 10.2 Çift sıralama — pead kovası İÇİNDE dilim fazlası

> EDG-016/EDG-007 şablonu: kontrol kovası = pead∈{0,1}. Her kovada dilim satırlarının AYNI-GÜN in_play-dışı taban fazlası ayrı ayrı ölçülür. pead=False kovası ASIL artık okumasıdır: 'PEAD ateşlememiş satırlarda in_play hâlâ bilgi taşıyor mu?'

| P | h | kova | n | dilim ham n | fazla | CI | CI 0'ı kapsıyor | neden |
|---|---|---|---|---|---|---|---|---|
| 3 | 10 | `pead_yok` | 635 | 701 | -0.489% | [-1.137%, +0.313%] | EVET | — |
| 3 | 10 | `pead_var` | 0 | 16 | — | — | — | n<30 |
| 3 | 20 | `pead_yok` | 634 | 700 | -0.624% | [-1.297%, +0.533%] | EVET | — |
| 3 | 20 | `pead_var` | 0 | 16 | — | — | — | n<30 |
| 5 | 10 | `pead_yok` | 678 | 758 | -0.577% | [-1.111%, +0.143%] | EVET | — |
| 5 | 10 | `pead_var` | 1 | 20 | — | — | — | n<30 |
| 5 | 20 | `pead_yok` | 677 | 757 | -0.754% | [-1.264%, +0.306%] | EVET | — |
| 5 | 20 | `pead_var` | 1 | 20 | — | — | — | n<30 |

> `pead_var` kovası **ölçülemedi** (n < 30) — dilim ile pead'in kesişimi zaten 16-20 aday-gündür. Bu bir sonuç değil bir ÖRNEKLEM olgusudur ve doldurulmadı (uydurma yasağı).

### 10.3 Artık-IC (pead-kontrollü)

> GÜN BAZLI kesitte fwd getirinin YÜZDELİK RÜTBESİ, (gün × pead) kovası ortalamasından ARINDIRILIR (kova merkezleme = ikili regresörle gün-içi OLS'in cebirsel özdeşi). Artık ile dilim göstergesi arasındaki Spearman IC, pead-kontrollü artık katkıdır. Kova üyesi n=1 ise merkezleme artığı TANIM GEREĞİ 0'dır ve o satır DIŞLANIR (sayılır: n_tek_uyeli_kova_dusen).

| P | h | kontrol | IC | n | CI | anlamlı | n_dilim | tek-üyeli kova düşen |
|---|---|---|---|---|---|---|---|---|
| 3 | 10 | **pead-kontrollü** | -0.0207 | 6479 | [-0.0478, +0.0074] | hayır | 680 | 218 |
| 3 | 10 | kontrolsüz ikiz _(karşılaştırma)_ | -0.0193 | 6560 | [-0.0457, +0.0074] | hayır | — | — |
| 3 | 20 | **pead-kontrollü** | -0.0111 | 6442 | [-0.0332, +0.0142] | hayır | 679 | 218 |
| 3 | 20 | kontrolsüz ikiz _(karşılaştırma)_ | -0.0119 | 6523 | [-0.0373, +0.0124] | hayır | — | — |
| 5 | 10 | **pead-kontrollü** | -0.023 | 6479 | [-0.0499, +0.0058] | hayır | 738 | 218 |
| 5 | 10 | kontrolsüz ikiz _(karşılaştırma)_ | -0.0223 | 6560 | [-0.0488, +0.0038] | hayır | — | — |
| 5 | 20 | **pead-kontrollü** | -0.0097 | 6442 | [-0.0331, +0.0136] | hayır | 737 | 218 |
| 5 | 20 | kontrolsüz ikiz _(karşılaştırma)_ | -0.0112 | 6523 | [-0.0340, +0.0124] | hayır | — | — |

> **Okuma (sayı, hüküm değil).** Kontrollü ile kontrolsüz IC neredeyse aynı — pead kontrolü artıktan kayda değer bir şey ALMIYOR. Bu, §10.1'deki düşük örtüşmenin ikinci bir görünümüdür: iki sinyal aynı satırları seçmiyor.

## 11 · Ders #7 — en iyi hücre küçültülmeden yazılmaz

| hücre | ham | SE | küçültülmüş | ağırlık |
|---|---|---|---|---|
| P3@10 | -0.482% | +0.359% | -0.592% | 0.0 |
| P3@20 | -0.620% | +0.462% | -0.592% | 0.0 |
| P5@10 | -0.532% | +0.295% | -0.592% | 0.0 |
| P5@20 | -0.733% | +0.390% | -0.592% | 0.0 |

- en iyi HAM: `P3@10` -0.482% → küçültülmüş -0.592%
- sıra değişti mi: **hayır** · τ² = 0.0 · hedef -0.592%
- uyarı: τ²=0 — hücreler arasında ÖLÇÜLEBİLİR gerçek fark yok; her hücre ortak ortalamaya TAM küçültüldü (eksiklik değil, dürüst cevap)

> Küçültülmüş değer **eşiklere GİRMEZ** ve `success`/`kill` ölçütlerinde kullanılmaz.

## 12 · KILL / SUCCESS KARŞILIKLARI — **TABLO (hüküm Rol-1'de)**

> Aşağıdaki tablo kart metnindeki ölçütlerin **ÖLÇÜLEN KARŞILIKLARINI** verir. Bu rapor bir hüküm cümlesi TAŞIMAZ.

| # | kart metni (harfiyen) | ölçülen karşılık | ölçüt karşılandı mı |
|---|---|---|---|
| **success** | "in_play∧rvol>=1.5 diliminin @20 taban-fazlası anlamlı POZİTİF (CI 0-dışı) **VE** PEAD-ayrışması…" | @20 fazla: P3 -0.620% [-1.300%, +0.512%] · P5 -0.733% [-1.232%, +0.299%] — **ikisi de CI 0'ı KAPSIYOR**, poz-anlamlı hayır/hayır | **1. bacak KARŞILANMADI** (2. bacak koşullu olarak devreye girmiyor) |
| kill#1 | "iki pencerede de @20 fazla CI-0-içi → bilgisiz, arşiv (011'e de not düşer: tek-yönlü yarı da boş)" | P3 [-1.300%, +0.512%] → CI-0-içi EVET; P5 [-1.232%, +0.299%] → CI-0-içi EVET | **KARŞILIK TAM** (iki pencerede de) |
| kill#2 | "PEAD-örtüşmesi **yüksek** VE pead-kontrollü artık CI-0-içi → 'PEAD kopyası' arşiv" | örtüşme Jaccard P3 **0.019584** · P5 **0.022857** (dilimin %2.2/%2.5'i pead); artık-IC @20 P3 -0.0111 CI-0-içi EVET · P5 -0.0097 CI-0-içi EVET | **BİLEŞİK KARŞILANMADI** — 2. bileşen karşılık buluyor, 1. bileşen (**yüksek** örtüşme) BULMUYOR |
| kill#3 | "maliyet-sonrası net <=0 → arşiv + not" | @20 net 10bps: P3 -0.720% · P5 -0.833%; 20bps: P3 -0.820% · P5 -0.933%. @10 net 10bps: P3 -0.582% · P5 -0.632% | **KARŞILIK TAM** (dört hücrede de net ≤ 0) |

**§12 EK — ölçüm tarafından görülen EŞİK-DİLBİLGİSİ belirsizliği (Ders #2).**

kill#2'nin ilk bileşeni **"PEAD-örtüşmesi yüksek"** kartta SAYISAL bir eşikle yazılmamıştır; ölçüm bir eşik SEÇEMEZ (eşik ölçümden sonra belirlenemez). Bu yüzden tabloya ham örtüşme (0.019584 / 0.022857) ve iki okuma birlikte yazıldı. Not: **kill#1 ve kill#3 zaten belirsizlik taşımadan karşılık buluyor**, dolayısıyla bu belirsizlik hükmün yönünü değiştirebilecek bir yerde durmuyor — yine de kayda geçirildi (Ders #2: belirsizlik muhafazakâr okunur ve karta ders notu düşülür; not düşme işi Rol-1'dedir).

**§12 EK — EDG-011'e taşınacak veri (kart notes'u öyle diyor: 'hükmü 011'e not düşülür').**

- 011'in askı sebebi olan kill#3 (in-play aday-gün < 150) bu turda **YOK**: dilim 729 (P=3) / 791 (P=5) aday-gün ve tüm defter penceresine yayılmış durumda.
- 011'in kapsam sorunu (1669 kapsam-dışı aday-gün) bu kaynakla **bitti**: takvimde olmayan sembol satırı 0.
- 011'in iki-yönlü `|t−e|` lafzının PIT-ihlalli olduğu ve tek-yönlü daldan **ne kadar** ayrıldığı ölçüldü: havuzun %43.4'i.

## 13 · Beyanlı çekinceler ve sınırlar

1. **Ex-post olay ekseni.** Nasdaq-geçmişi revizyon-SONRASI nihai tarihleri verir. Bu kartın tek-yönlü formu (`e ≤ t`) bundan etkilenmez — geçmiş bir kazanç günü t'de kamusal olgudur — ama kaynağın **duyuru-öncesi bilinirlik** iddiası taşımadığı burada da beyan edilir.
2. **Kirli ağaç.** `kod_surumu.kirli_agac = True` → bu rapor `b8ed076` SHA'sından **yeniden üretilemez**; SHA o anki kodun değil ATASININ adıdır (ölçüm sırasında bu klasörün betikleri commit'lenmemişti).
3. **Hayatta-kalma yanlılığı.** Evren bugünkü 251 semboldür; delist olmuş isimler bar önbelleğinde yoktur. EDG-016 emsali kalıcı şerh: bu, POZİTİF bir bulguyu yukarı çarpıtır — bu turda bulgu pozitif değildir, dolayısıyla şerh hükmü gevşetme yönünde çalışmaz.
4. **Saat (BMO/AMC) yok.** Nasdaq önbelleği `bmo/amc` alanını süzmüş; `t−e = 0` günü (390 satır) rapor-öncesi mi sonrası mı ayrımı YAPILAMADI. AMC raporlarında `t−e=0` barı olayın **öncesindeki** seanstır; bu, dilimin bir kısmında olay-sonrası varsayımını zayıflatır. Ölçülemedi → düzeltilmedi, BEYAN EDİLDİ. (8-K `acceptance` damgası bu ayrımı birinci elden verebilir — keşif turu şerhi.)
5. **`pead_var` kovası ölçülemedi** (n<30): kesişim 16-20 aday-gün. Çift-sıralamanın `pead_var` bacağı bu turda boştur ve DOLDURULMADI.
6. **Maliyet modeli.** tek-yön bps, fazladan DÜŞÜLÜR. Kart cost_model: '10bps + 20bps duyarlılık; olay-sonrası spread-genişlemesi beyan-notu'. BEYAN-NOTU: kazanç sonrası ilk günlerde spread GENİŞLER ve gerçek maliyet 10bps'in ÜSTÜNDE olabilir; bu ölçümde spread verisi YOK, dolayısıyla 20bps satırı bir ÜST OKUMA değil yalnız bir duyarlılıktır.
7. **Sıralama overlay'i şerhi (011'den devralındı).** Bu eksen işlem ÜRETMEZ, mevcut adaylar arasında seçim değiştirir; maliyet satırı yine de kartın kill#3'ü gereği hesaplandı.

## 14 · KOD DAMGASI — bu sayılar hangi BAYTLARLA üretildi

`kod_surumu` git HEAD'i `b8ed076` diyor ama **`kirli_agac = True`** — yani SHA o anki kodun değil ATASININ adıdır ve tek başına bu raporu yeniden üretmeye YETMEZ. Üstelik bu depoda Rol-1 **ajan uçuştayken** commit atar (CLAUDE.md md.8) ve bu turda HEAD ölçüm ortasında GERÇEKTEN kaydı. Bu yüzden kimlik dosya-bazında sha256'dır:

| kalem | değer |
|---|---|
| motor dosyası (kum havuzu kopyası) | 93 |
| **tüm ağaç sha256** — `pk_020.json` | `93435534a3ed44cab6f3f5b128d6ea4c…` |
| **tüm ağaç sha256** — `sonuc_020.json` | `93435534a3ed44cab6f3f5b128d6ea4c…` |
| iki çıktı AYNI motordan mı | **EVET** |
| repo ↔ kum havuzu kopyası ayrışan dosya | 0 |
| kritik modül bulunamadı | 0 |

**Ölçüme GİREN modüllerin sha256'ları (ilk 16 hane):**

| modül | sha256 |
|---|---|
| `meridian/config.py` | `7be49132c6a1985c…` |
| `meridian/indicators.py` | `48f1a14ea15591e1…` |
| `meridian/strategy.py` | `6fb76448ac423ca5…` |
| `meridian/earnings.py` | `1776ed03b47a6d44…` |
| `meridian/analytics.py` | `f8e55c333eee74df…` |
| `meridian/olcum_araclari.py` | `bc80eac4538b2159…` |
| `meridian/adapters/data.py` | `5fe766f9b077dd5d…` |
| `meridian/obs.py` | `14b06e081bef46c9…` |
| `meridian/store.py` | `9181bafe1e91d61e…` |

> **Neden bu tablo var.** Bu turun ilk koşumu `a173586`, ikinci koşumu `2066b8b` HEAD'inde yakalandı (arada Rol-1 commit'leri düştü: `api.py`, `backtest.py`, `reflect.py`, `watchdog.py`). İkisi de ölçümün BAĞIMLILIK YOLUNDA DEĞİL — ve bunu iddia etmek yerine kanıtlamak için iki betik tek motor anlık görüntüsünden YENİDEN koşuldu; yukarıdaki iki ağaç sha256'sı artık AYNIDIR. Sayılar HEAD hareketinden önce ve sonra bit-bit değişmedi.

---

**KAPI SATIRI (tekrar):** pozitif kontrol EVET · PIT-assert EVET · PK4 EVET · PK5 EVET

**Kanıt dosyaları:** `sonuc_020.json` · `pk_020.json` · `RAPOR_020.md` · `takvim_kaniti/` (5 JSONL + 4 çekim özeti, sha256'lı) · betikler `ortak020.py` · `pk020.py` · `k020.py` · `rapor_020.py`

