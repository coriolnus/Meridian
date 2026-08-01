# EDG-2026-015 — VCP-DECOMPOSE (WP-K çatı hipotezi) · ÖLÇÜM RAPORU

- Kart: `research/cards/EDG-2026-015-vcp-decompose.yaml` · aile `vcp_decompose`
- Durum: **OLCULDU** · ölçüm zamanı `2026-08-01T11:01:29.064023+00:00`
- Sandbox: `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/vcp_olcum` — repo/state'e **hiçbir yazım yok**

> Bu rapordaki her sayı `sonuc.json`dan okunur. Ölçüm ajanı **karta dokunmadı**; aşağıdaki
> hüküm bir **öneridir**, hükmü Rol-1 işler.

**TEK CÜMLE:** KILL#1 — kompozit üst-%20 dilimi aday havuzuna karşı POZİTİF FAZLA TAŞIMIYOR (@20 CI-0-içi · @10 CI TAMAMEN NEGATİF): ÇATI DA BİLGİSİZ. WP-K açık-hipotez listesi KAPANIR (arşiv). NOT: kill#1'in lafzı 'CI-0-içi'dir; anlamlı NEGATİF bulunan ufuk lafza uymaz ama hükmü A FORTIORI taşır — 'pozitif bilgi yok'un daha güçlü hâlidir ve sıralamanın o ufukta TERS işlediğini söyler.

## 1 · Skor fonksiyonu ve ağırlıklar — REPODAN ÇIKARILDI (kartın 1. şartı)

- **Fonksiyon:** meridian/strategy.py::evaluate_entry — 'composite score in [0,100]' bloğu (score_num/score_den). Kurulum adı: breakout_vcp. Bu, kartın 'canlı skor fonksiyonu'dur; ikinci bir kopya YAZILMADI.
- **Formül:** `kompozit = (w_rs·rs + w_tight·(tt·100) + w_vol·(100·min(vr/3,1)) + w_prox·(100·(1−min(prox_pct/prox_max,1)))) / (w_rs+w_tight+w_vol+w_prox)`
- **Bileşen kaynağı:** meridian/component_ic.py::_component_frame — bileşen serileri REPONUN kendi ölçüm fonksiyonundan alındı (tight/vol/prox), rs ise component_ic._rs_by_date (kesitsel, indicators.rs_rating). Yeniden icat YOK; component_ic'in COMPONENTS adları birebir kullanıldı.

| bileşen | `component_ic` ağırlık anahtarı | KULLANILAN ağırlık | kaynak |
|---|---|---:|---|
| `rs` | `entry.w_rs` | 0.35 | KOD varsayılanı |
| `tight` | `entry.w_tight` | 0.30 | KOD varsayılanı |
| `vol` | `entry.w_vol` | 0.20 | KOD varsayılanı |
| `prox` | `entry.w_prox` | 0.15 | state/strategy.yaml |

- Ağırlık dosyası: `/Users/erdemozturk/AI-Trading/state/strategy.yaml` (sürüm **3**) · dosyada yazılı: `{'entry.w_prox': 0.15}` · kod varsayılanından gelen: `{'entry.w_rs': 0.35, 'entry.w_tight': 0.3, 'entry.w_vol': 0.2}`
- Rejim çözümlemesi: params_by_regime'in DÖRT rejimi de BOŞ → config.resolve_params özdeşliktir; rejime göre ağırlık kayması YOK.
- **prox_max = 2.3** — entry.pivot_proximity_pct CANLIDA 2.3'tür (kod varsayılanı 2.0 DEĞİL). prox bileşeni bu eşiğe göre normalize edilir; 2.0 ile hesaplamak canlı olmayan bir skor üretirdi.
- Uyuyan bileşenler: `entry.w_rvolband=0.0`, `entry.w_mom=0.0` → ağırlık 0 → ne paya ne paydaya girer; kompozit DÖRT terimlidir (strategy.py'nin kendi çivi testi: test_score_rebuild_v115)
- rmom'un ağırlık DÜĞMESİ YOK (component_ic.COMPONENT_WEIGHT_KEY['rmom'] is None) → skora hiç girmez, bu ölçümün bileşen kümesine de girmez.
- Yuvarlama: canlı fonksiyon int(round(...)) uygular; SIRALAMA için SÜREKLİ değer kullanıldı (int yuvarlaması yapay beraberlik üretir ve üst-%20 dilimini keyfî böler). int hâli 'kompozit_int' olarak taşınır ve defter skoruyla sadakat tanısında kullanılır.

**Skor sadakat tanısı (hükme girmez).** defterdeki `score` O GÜNÜN parametreleriyle (sürüm geçmişi boyunca prox_max 2.0→2.3, w_prox None→0.15) hesaplanmıştı; bu ölçüm BUGÜNKÜ canlı ağırlıklarla TÜM geçmişi yeniden hesaplar (component_ic'in kendi deseni). Fark BEKLENİR ve hükme GİRMEZ — burada yalnız büyüklüğü görünür kılınır.

| kalem | değer |
|---|---|
| defter skoru taşıyan satır | 5957 |
| ortalama mutlak fark (yeniden kurulan − defter) | 1.825 puan |
| medyan fark | -1.000 puan |
| birebir eşit oran | 0.2647 |
| Spearman(kompozit, defter skoru) | 0.9829 |

## 2 · Kart metninin uygulaması

- **universe:** cf-katmanlı aday popülasyonu — counterfactuals.jsonl entered=True (near_miss DAHİL = 'girilen+kılpayı') + cf_open.json; TEKİL (ticker,date); setup='breakout_vcp' ile SINIRLI — kartın kendi niteleyicisi 'kompozit skorun GERÇEKTEN uygulandığı kesit'. Diğer kurulumların skoru BAŞKA bir formüldür (pullback 0.40/0.35/0.25 · momentum_burst 0.35/0.30/0.20/0.15 mom/vol üzerinden); üçünü tek ada toplamak üç farklı bileşiği tek bileşik gibi ölçmek olurdu.
- **kompozit:** strategy.evaluate_entry bileşik skoru, CANLI ağırlıklarla, SÜREKLİ
- **bilesen_toplami:** aynı dört bileşenin PANEL GENELİ z-skorlarının eşit-ağırlık ortalaması (form-suz taban: ağırlık ve ölçek farkı kaldırılır, bileşen kümesi AYNI kalır)
- **ust_dilim:** kompozit ≥ panel 80. yüzdeliği (havuzlanmış eşik; gün-içi üst-%20 DUYARLILIK olarak ayrıca verilir)
- **taban:** AYNI-GÜN ADAY HAVUZU (ders #3): o takvim gününde ileri getirisi tanımlı TÜM panel aday-günlerinin ortalaması. Birincil okuma havuza SATIRIN KENDİSİNİ dâhil eder (kartın harfi); LOO okuması duyarlılık olarak ayrıca verilir.
- **artik_katki:** İKİ YOL: (a) EDG-007 ÇİFT SIRALAMA — bilesen_toplami TERZİLLERİ İÇİNDE kompozit üst-%20 yayılımı, kova-içi n-ağırlıklı havuzlanmış fark; (b) ARTIK-IC — kompozit rütbesinin bilesen_toplami rütbesine OLS artığı ile ileri fazlanın Spearman IC'si
- **ileri_getiri:** close[t+h]/close[t]-1, TAM (takvim-kapılı + integrity-dışlamalı) bar serisinden; h ∈ 5/10/20 (karar ufukları 10/20)
- **ci:** 21-günlük HAREKETLİ BLOK bootstrap (%95 persentil, 2000 tekrar; IC'lerde 600)
- **maliyet:** 10.0bps tek-yön; sıralama overlay'i işlem üretmez → hüküm BRÜT üzerinden, net değer AYRICA verilir

## 3 · Veri zemini ve panel

| kalem | değer |
|---|---|
| bar sembolü yüklendi | 248 / 251 |
| hayalet seans düşen satır | 428 |
| karantinaya alınan satır | 13 |
| bars_integrity **defter yolu** düşen satır | 46256 (57 sembol) |
| bars_integrity **hesaplanan yol** dışlanan satır | 0 |
| iki yolun ayrıştığı sembol | 0 |
| cf defteri satırı (entered, tüm kurulumlar) | 7122 |
| setup dağılımı | `{'momentum_burst': 1087, 'breakout_vcp': 6000, 'pullback': 28, 'episodic_pivot': 1, 'exhaustion_hammer': 6}` |
| **kart kesiti** (`setup=breakout_vcp`) satır | 6000 |
| kesit dışı kalan satır | 1122 |
| tekil aday-gün | 5999 (düşen kopya 1) |
| bar/rs eşleşmesi kabul | 5957 · bar yok (sembol/tarih) 42/0 · rs kesiti yok 0 |
| bileşeni NaN olan satır | 0 |
| `prox` > 100 olan satır (kapanış pivotun ALTINDA) | 12 |
| **kompozit ölçülebilen aday-gün** | **5957** |

**KILL#3 örnek kapısı** — geçerli aday-gün = kompoziti ÖLÇÜLEBİLEN ve o ufukta ileri getirisi TANIMLI tekil (ticker,date) satır sayısı

| ufuk | ileri getirisi tanımlı aday-gün | eşik | yeterli |
|---|---:|---:|---|
| 5g | 5921 | — | (karar ufku değil) |
| 10g | 5901 | 2000 | **EVET** |
| 20g | 5866 | 2000 | **EVET** |

→ kill#3 **GEÇİLDİ**

**Aynı-gün aday havuzu (taban).**

| kalem | değer |
|---|---|
| gün sayısı | 962 |
| gün başına aday (ort / medyan / min / maks) | 6.097713 / 5.0 / 1 / 40 |
| tek adaylı gün | 148 |

> tek-adaylı günlerde birincil (kendisi-dahil) fazla TANIM GEREĞİ 0'dır; LOO okuması o günleri ölçemez (n<2) ve dışlar — iki okuma bu yüzden AYRI verilir

## 4 · Kompozit üst-%20 dilimi ve aynı-gün havuz fazlası (success bacağı 1)

| kalem | değer |
|---|---|
| havuzlanmış eşik (kompozit ≥) | 79.7933 |
| üst dilim n / kalan n | 1192 / 4765 (gerçek pay 0.2001) |
| kompozit dağılımı (min/p25/medyan/p75/p80/maks) | 39.76 / 64.65 / 72.55 / 78.52 / 79.79 / 208.03 |
| gün-içi üst-%20 dilimi n (duyarlılık) | 1648 |

### 4.1 Üst dilim — havuz fazlası (birincil: havuz ortalamasına satır DAHİL)

| ufuk | n | ham ort | **havuz fazlası** | %95 CI (21g blok) | poz. anlamlı | net (−10bps) |
|---|---:|---:|---:|---|---|---:|
| 5g | 1186 | -0.044% | **-0.088%** | [-0.234%, +0.107%] | hayır | -0.188% |
| 10g | 1185 | -0.009% | **-0.346%** | [-0.532%, -0.012%] | hayır | -0.446% |
| 20g | 1180 | +0.622% | **-0.255%** | [-0.624%, +0.209%] | hayır | -0.355% |

### 4.2 Karşılaştırma dilimleri (aynı panel, aynı taban)

| dilim | ufuk | n | havuz fazlası | %95 CI | anlamlı |
|---|---|---:|---:|---|---|
| kalan %80 | 5g | 4735 | +0.022% | [-0.025%, +0.059%] | hayır |
| kalan %80 | 10g | 4716 | +0.087% | [+0.005%, +0.136%] | **EVET** |
| kalan %80 | 20g | 4686 | +0.064% | [-0.064%, +0.155%] | hayır |
| gün-içi üst-%20 (duyarlılık) | 5g | 1637 | -0.027% | [-0.168%, +0.143%] | hayır |
| gün-içi üst-%20 (duyarlılık) | 10g | 1632 | -0.211% | [-0.422%, +0.042%] | hayır |
| gün-içi üst-%20 (duyarlılık) | 20g | 1621 | -0.063% | [-0.446%, +0.316%] | hayır |
| üst-%20 · LOO taban (duyarlılık) | 5g | 1138 | -0.092% | [-0.271%, +0.148%] | hayır |
| üst-%20 · LOO taban (duyarlılık) | 10g | 1137 | -0.408% | [-0.632%, +0.022%] | hayır |
| üst-%20 · LOO taban (duyarlılık) | 20g | 1131 | -0.249% | [-0.672%, +0.343%] | hayır |

### 4.3 Üst-%20 vs kalan — doğrudan yayılım (fazla üzerinden)

| ufuk | n üst / n kalan | ort üst | ort kalan | fark | %95 CI | anlamlı |
|---|---|---:|---:|---:|---|---|
| 5g | 1186 / 4735 | -0.088% | +0.022% | -0.110% | [-0.314%, +0.142%] | hayır |
| 10g | 1185 / 4716 | -0.346% | +0.087% | -0.433% | [-0.687%, -0.038%] | **EVET** |
| 20g | 1180 / 4686 | -0.255% | +0.064% | -0.320% | [-0.768%, +0.332%] | hayır |

## 5 · Artık katkı — kompozit, bileşen-toplamının ötesinde bilgi taşıyor mu? (bacak 2)

- kart success_metric İKİNCİ bacağı: kompozit, bilesen_toplami kontrol edildikten SONRA da bilgi taşıyor mu?
- **Örtüşme:** Spearman(kompozit, bilesen_toplami) = **0.9475** · Pearson = 0.9497
- İKİ BÜYÜKLÜK AYNI DÖRT BİLEŞENDEN kurulur; fark yalnız AĞIRLIK ve ÖLÇEKtedir. Örtüşme yüksekse bu bir kusur değil, kartın sorduğu şeyin TA KENDİSİDİR: form (ağırlık+ölçek) bileşen kümesinin ötesinde bilgi taşıyor mu?

- Terzil kesimleri (bilesen_toplami): 1/3 = -0.1954, 2/3 = 0.2095 · kova n = `{'1': 1986, '2': 1985, '3': 1986}` · birim: PANEL GENELİ (gün-içi DEĞİL) — gün başına aday sayısı medyanı çok küçük olduğu için gün-içi terzil gürültüdür

### 5.1 ÇİFT SIRALAMA (EDG-007 şablonu) — bilesen_toplami kovası İÇİNDE üst-%20 yayılımı

**Çapraz tablo — üst-%20 dilimi terzillere nasıl dağılıyor?**

| bilesen_toplami terzili | üst-%20 | kalan |
|---|---:|---:|
| kova 1 | 0 | 1986 |
| kova 2 | 2 | 1983 |
| kova 3 | 1190 | 796 |

> Üst-%20 dilimi bilesen_toplami'nın ÜST terziline yığılıyorsa iki sıralama üst uçta ÖRTÜŞÜYOR demektir: 'form' orada yeni bir sıralama üretmiyor. Bu durumda alt kovalarda çift sıralama ÖLÇÜLEMEZ (dilim boş) ve havuzlanmış fark fiilen TEK kovanın farkıdır — sayı okunurken bu sınır adıyla taşınmalıdır.

| ufuk | kova | n üst / n kalan | fark (fazla) | %95 CI | anlamlı |
|---|---|---|---:|---|---|
| 5g | 1 | 0 / 1974 | — | — | — |
| 5g | 2 | 2 / 1969 | — | — | — |
| 5g | 3 | 1184 / 792 | +0.147% | [-0.150%, +0.488%] | hayır |
| 10g | 1 | 0 / 1969 | — | — | — |
| 10g | 2 | 2 / 1958 | — | — | — |
| 10g | 3 | 1183 / 789 | +0.002% | [-0.330%, +0.498%] | hayır |
| 20g | 1 | 0 / 1954 | — | — | — |
| 20g | 2 | 2 / 1944 | — | — | — |
| 20g | 3 | 1178 / 788 | +0.088% | [-0.415%, +0.782%] | hayır |

| ufuk | **kova-içi havuzlanmış fark** | %95 CI | anlamlı | poz. anlamlı | n |
|---|---:|---|---|---|---:|
| 5g | **+0.147%** | [-0.734%, +0.471%] | hayır | hayır | 5921 |
| 10g | **+0.002%** | [-1.761%, +0.460%] | hayır | hayır | 5901 |
| 20g | **+0.088%** | [-3.489%, +0.800%] | hayır | hayır | 5866 |

### 5.2 ARTIK-IC — kompozitin bileşen-toplamıyla açıklanamayan sıralama bileşeni

- Yöntem: rütbe uzayında OLS: r_kompozit = α + β·r_bilesen_toplami + artık; artık = kompozitin bileşen-toplamıyla AÇIKLANAMAYAN sıralama bileşeni
- α = 0.0263, β = 0.9475, R² = 0.8977, artık std = 0.0924
- hüküm ölçütü Spearman IC ve rütbe-dilimidir; artığı seviye uzayında almak farklı bir büyüklüğün artığını ölçerdi

| ufuk | büyüklük | IC (fazla ile) | %95 CI | anlamlı | n |
|---|---|---:|---|---|---:|
| 5g | `kompozit` | -0.0105 | [-0.0346, +0.0195] | hayır | 5921 |
| 5g | `bilesen_toplami` | -0.0189 | [-0.0454, +0.0103] | hayır | 5921 |
| 5g | `kompozit_artik` | 0.0144 | [-0.0207, +0.0446] | hayır | 5921 |
| 10g | `kompozit` | -0.0351 | [-0.0651, -0.0019] | **EVET** | 5901 |
| 10g | `bilesen_toplami` | -0.0459 | [-0.0724, -0.0112] | **EVET** | 5901 |
| 10g | `kompozit_artik` | 0.0246 | [-0.0123, +0.0551] | hayır | 5901 |
| 20g | `kompozit` | -0.0271 | [-0.0662, +0.0090] | hayır | 5866 |
| 20g | `bilesen_toplami` | -0.0326 | [-0.0717, +0.0035] | hayır | 5866 |
| 20g | `kompozit_artik` | 0.0085 | [-0.0393, +0.0385] | hayır | 5866 |

**TANI (ders #3 gereği hükme GİRMEZ):** kompozitin HAM ileri getiriyle IC'si

| ufuk | IC | %95 CI | anlamlı | n |
|---|---:|---|---|---:|
| 5g | -0.0051 | [-0.0423, +0.0355] | hayır | 5921 |
| 10g | -0.0360 | [-0.0857, +0.0191] | hayır | 5901 |
| 20g | -0.0046 | [-0.0556, +0.0488] | hayır | 5866 |

## 6 · Kıyas temizliği (ders #4) — `olcum_araclari.temiz_taban` İLK SAHA KULLANIMI

- Araç: `meridian.olcum_araclari.temiz_taban (docs/olcum_standartlari.md ders #4) — İLK SAHA KULLANIMI`
- Taban serisi: aynı-gün aday-havuzunun KENDİSİ: panelin ileri getirisi tanımlı TÜM (ticker, tarih, fwd_h) satırları
- Pencere: olay günü −1 … +10
- Takvim: `/Users/erdemozturk/AI-Trading/state/earnings.csv` · yükleyici meridian.earnings._load() (DEPONUN kendi yükleyicisi; dosya sandbox'a kopyalandı, canlı dosyaya DOKUNULMADI)
- Takvim kapsamı: **193 sembol / 193 tarih**, aralık `['2025-06-24', '2026-08-13']`
- Takvim ay dağılımı: `{'2025-06': 1, '2026-07': 123, '2026-08': 69}`
- Panel tarih aralığı: `['2022-01-03', '2026-07-28']`

| ufuk | n_toplam | n_temiz | n_kirli | kirlilik oranı | gün birimi | olaysız kimlik | uyarı |
|---|---:|---:|---:|---:|---|---:|---|
| 5g | 5921 | 5920 | 1 | 0.00020 | takvim gunu | 58/248 | — |
| 10g | 5901 | 5901 | 0 | 0.00000 | takvim gunu | 58/248 | — |
| 20g | 5866 | 5866 | 0 | 0.00000 | takvim gunu | 58/248 | — |

**Takvimin gerçekten kapsadığı pencere** (`['2025-06-21', '2026-08-25']`, fwd20): n_toplam 1506 · n_kirli 0 · kirlilik 0.00000

**PIT birikim defteri (ölçüldü, varsayılmadı):** `/Users/erdemozturk/AI-Trading/state/history/earnings_snapshots.jsonl` · dayanak `meridian/earnings.py::SNAPSHOT_FILE + _snapshot() (2026-08-01 eklendi)` · dosya var mı: **False** · satır: None

> MEKANİZMA VAR, GEÇMİŞ YOK — defter bugün başlıyor; bu tur için kullanılabilir tek bir tarihsel anlık görüntü bile içermiyor. Kirlilik ölçümünün hükümsüz olması bir ARAÇ kusuru değil, VERİ kıtlığıdır ve tarihi bilinen bir kıtlıktır (EDG-011'in askı gerekçesiyle aynı kök).

### HÜKME GİREN KİRLİLİK: **None** (None)

> state/earnings.csv TEK BİR İLERİYE-DÖNÜK ANLIK GÖRÜNTÜdür (sembol başına yalnız SONRAKİ planlı rapor; dosya her tazelemede üzerine yazılır). Panel 2022-01..2026-07'yi kapsarken takvim yalnız 2026-07/08'i taşır. Bu yüzden 'panel geneli kirlilik oranı' HESAPLANABİLİR ama HÜKÜM TAŞIMAZ: sayı, kazanç olaylarının seyrekliğini değil TAKVİMİN YOKLUĞUNU ölçer ve olduğundan KÜÇÜK çıkar. UYDURMA YASAĞI gereği hükme giren kirlilik None + nedendir. Ders #4'ün gerçek uygulaması PIT kazanç arşivi gerektirir; arşivin MEKANİZMASI bugün eklendi (bkz. pit_birikim_defteri) ama GEÇMİŞİ yok — EDG-2026-011'in askı gerekçesiyle aynı kök.

**İlk saha kullanımı gözlemleri:**

- GİRDİ ŞEKLİ: uzun biçim [(kimlik, gün, değer)] sorunsuz kabul edildi; panelden ek dönüştürme gerekmedi.
- BİRİM ÇIKARIMI ÇALIŞTI: günler ISO metin olduğu için gun_birimi='takvim gunu' döndü ve çıktıda ADIYLA durdu — pencere aritmetiğinin hangi birimde koştuğu tahmine bırakılmadı.
- n_olaysiz_kimlik AYRIMI KRİTİK ÇIKTI: bu turda kirliliğin küçük görünmesinin sebebi olayların seyrekliği DEĞİL, sembollerin çoğunun takvimde HİÇ bulunmaması. Fonksiyon bu iki hâli ayırmasaydı 'taban temiz' diye okunurdu; ayırdığı için kirlilik oranının hükümsüz olduğu GÖRÜNÜR hâle geldi.
- SINIR (araç değil VERİ): kirlilik_orani=None yalnız HİÇ ölçülebilir satır yoksa döner. Takvimin panelin yalnız son iki haftasını kapsaması durumunda fonksiyon küçük ama SIFIR-OLMAYAN bir oran döndürür ve bu sayı tek başına yanıltıcıdır; 'takvim kapsamı' ölçümün KENDİ raporlaması olarak eklendi (n_olaysiz_kimlik + takvim aralığı).

## 7 · Pozitif kontrol ve özdeşlikler

- AYNI boru hattı, kart guards çivisi: ham rvol20 @20 cf-katman IC ≈0.0642 (pullback turu 0.0642; max_olcum 0.0645; resmom 0.0637 — hepsi bars_integrity dışlamalı yolda).
- Katman: counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı), ŞABLONLA AYNI SATIR DÜZEYİ ve AYNI setup kapsamı (tekilleştirme YOK, setup filtresi YOK) — çivi ancak aynı popülasyonda karşılaştırılabilir · n = 2099

| ufuk | IC | %95 CI | anlamlı | n |
|---|---:|---|---|---:|
| 5g | 0.0374 | [-0.0193, +0.0816] | hayır | 2095 |
| 10g | 0.0516 | [-0.0076, +0.1027] | hayır | 2093 |
| 20g | 0.0642 | [+0.0067, +0.1126] | **EVET** | 2087 |

→ **çivi:** ölçülen 0.0642 · hedef 0.0642 · sapma 0.0000 · tolerans 0.005 → **GEÇTİ = True**

- Tanı (hükme girmez) — kart kesitinde (breakout_vcp, tekil) aynı çivi @20: 0.0897 [+0.0245, +0.1541] (n=996)
- Canlı defterdeki `component_ic.cf.rvol20`: `{'5': {'ic': 0.032, 'n': 2102, 'neden': None, 'ci': {'lo': -0.0108, 'hi': 0.0747, 'seviye': 0.95}, 'anlamli': False}, '10': {'ic': 0.0456, 'n': 2100, 'neden': None, 'ci': {'lo': 0.0029, 'hi': 0.0882, 'seviye': 0.95}, 'anlamli': True}, '20': {'ic': 0.0604, 'n': 2094, 'neden': None, 'ci': {'lo': 0.0176, 'hi': 0.103, 'seviye': 0.95}, 'anlamli': True}}`

**PK4 — yol tutarlılığı.** YOL TUTARLILIĞI: close[t+h]/close[t]-1, aradaki GÜNLÜK getirilerin bileşiğine eşit olmalı. Takvim kapısı/integrity kırpması ufkun İÇİNDE bar düşürdüyse ya da kaydırma bir gün kaysaydı bu özdeşlik bozulurdu.

| ufuk | n | maks mutlak fark | geçti |
|---|---:|---:|---|
| 5g | 12946 | 0.0 | **EVET** |
| 10g | 12903 | 0.0 | **EVET** |
| 20g | 12830 | 0.0 | **EVET** |

**PK5 — özdeşlikler.** DÖRT ÖZDEŞLİK: (A) KOMPOZİT SKOR ÖZDEŞLİĞİ — yeniden kurulan kompozit, strategy.evaluate_entry'nin KENDİ döndürdüğü skorla birebir aynı; (B) bileşenler GERİYE-BAKIŞSIZ (tam seri ile df.iloc[:i+1] kesilmiş seri aynı değeri verir); (C) hızlı ortalama-bootstrap ile satır-toplayan bootstrap aynı gün dizisinde birebir aynı; (D) bilesen_toplami + üst-dilim maskesi bağımsız (vektörsüz, saf python) türetimle birebir aynı.

- **(A) kompozit skor özdeşliği:** panelden rastgele seçilen aday-günlerde strategy.evaluate_entry, o güne kadar KESİLMİŞ bar serisiyle ve CANLI params + o günün kesitsel rs değeriyle çağrıldı; dönen EntrySignal.score ile int(round(kompozit)) karşılaştırıldı. Fonksiyon None dönen satırlar (kılpayı adaylar bugünkü sıkı kapılardan geçmez) sınamaya GİRMEZ ve sayıları ayrıca durur.
  - denenen 400 · `evaluate_entry` None döndü 342 · **sınanan 58** · maks fark 0 · ayrışan 0 → **EVET**
- **(B) bileşen geriye-bakışsızlığı:** n_örnek 72 · maks fark 0.0 → **EVET**
- **(C) hızlı ortalama-bootstrap özdeşliği:** n_örnek 50 · maks fark 0.0 → **EVET**
- **(D) bağımsız türetim:** maks fark bilesen_toplami 0.0 · kompozit 0.0 · maske ayrışması 0 → **EVET**

→ **PK5 GEÇTİ = True**

### 7.1 Duyarlılık — geçerli kırılım satırları (HÜKME GİRMEZ)

- kapanışı pivotun ALTINDA olan (prox>100, canlı fonksiyonun ön koşulunu sağlamayan) satırlar DIŞLANIP tüm birincil okuma yeniden kuruldu
- dışlanan 12 · kalan 5945 · yeni eşik 79.7496 · üst dilim n 1189 · kalan panelin kompozit maks 96.081

| ufuk | havuz fazlası | %95 CI | poz. anlamlı | artık-IC | artık-IC CI | poz. anlamlı |
|---|---:|---|---|---:|---|---|
| 10g | -0.368% | [-0.552%, -0.025%] | hayır | 0.0243 | [-0.0122, +0.0598] | hayır |
| 20g | -0.256% | [-0.648%, +0.263%] | hayır | 0.0079 | [-0.0356, +0.0419] | hayır |

## 8 · Hüküm ÖNERİSİ (kart ölçütü, otomatik)

- **success_metric:** kompozit-üst-dilim aday-havuzu-fazlası @10 VEYA @20 anlamlı POZİTİF (CI 0-dışı) VE artık-katkı anlamlı (çift-sıralama VEYA artık-IC)
- **kill listesi:**
  - dilim fazlası CI-0-içi → çatı da bilgisiz; WP-K açık-hipotez listesi kapanır
  - dilim pozitif AMA artık yok → 'form katkısız: skor=bileşen toplamı' arşiv + skor-sadeleştirme notu operatöre
  - geçerli aday-gün < 2000 → askı (K harcanmaz)

| bacak | okuma | sonuç |
|---|---|---|
| 1 · dilim fazlası @10 | -0.346% [-0.532%, -0.012%] — CI TAMAMEN NEGATİF (anlamlı NEGATİF fazla) | poz. anlamlı: hayır |
| 1 · dilim fazlası @20 | -0.255% [-0.624%, +0.209%] — CI 0'ı kapsıyor (kill#1 lafzı) | poz. anlamlı: hayır |
| **1 · KARŞILANDI** | @10 VEYA @20 pozitif-anlamlı | hayır |
| 2 · çift sıralama @10 | kova-içi havuzlanmış fark | poz. anlamlı: hayır |
| 2 · çift sıralama @20 | kova-içi havuzlanmış fark | poz. anlamlı: hayır |
| 2 · artık-IC @10 | kompozit_artik IC | poz. anlamlı: hayır |
| 2 · artık-IC @20 | kompozit_artik IC | poz. anlamlı: hayır |
| **2 · KARŞILANDI** | çift-sıralama VEYA artık-IC | hayır |

| kapı | sonuç |
|---|---|
| pozitif kontrol | True |
| PK4 | True |
| PK5 | True |
| kill#3 (örnek) | True |
| dilim fazlası CI 0-içi mi | `{'10': False, '20': True}` |

### ÖNERİ: KILL#1 — kompozit üst-%20 dilimi aday havuzuna karşı POZİTİF FAZLA TAŞIMIYOR (@20 CI-0-içi · @10 CI TAMAMEN NEGATİF): ÇATI DA BİLGİSİZ. WP-K açık-hipotez listesi KAPANIR (arşiv). NOT: kill#1'in lafzı 'CI-0-içi'dir; anlamlı NEGATİF bulunan ufuk lafza uymaz ama hükmü A FORTIORI taşır — 'pozitif bilgi yok'un daha güçlü hâlidir ve sıralamanın o ufukta TERS işlediğini söyler.

> Hükmü **Rol-1 işler**. K kaydı: kart `parameter_grid` iki katman ilan etti (`kompozit_ust20`, `kompozit_artik`) → **K += 2**.

