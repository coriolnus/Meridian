# EDG-2026-017 — rvol FORM REVİZYONU · ÖLÇÜM RAPORU

* Kart: `research/cards/EDG-2026-017-rvol-form-revizyonu.yaml` · aile `rvol_form_revizyonu`
* Ölçüm zamanı: 2026-08-02T15:11:13.730063+00:00
* Kum havuzu: `/Users/erdemozturk/AI-Trading/research/olcumler/wp1_rvol_form` · çalışma dizini `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/wp1_rvol_form_calisma`
* Durum: **TAMAM**

> **SALT-ÖLÇÜM.** Repoya ve canlı `state/`e hiçbir yazım yapılmadı; barlar canlı önbellekten SALT-OKUNUR okundu, `config.STATE` kum havuzuna çevrildi. **KART DOSYASINA DOKUNULMADI.** Aşağıda hiçbir hüküm cümlesi yoktur: kill/success ölçütlerinin sayısal karşılıkları veri olarak verilir, hükmü Rol-1 işler.

## 0. BEKÇİLER — İLK KOŞAN İŞ

**Pozitif kontrol (kart guard'ı: tutmazsa ÖLÇÜM DURUR)** — ham `rvol20` @20 cf-katman IC: **0.0642** (hedef 0.0645, tolerans 0.005, sapma 0.0003) → **GEÇTİ=True**

* n=2087 · CI [+0.0074, +0.1106]
* @5 IC 0.0374 CI [-0.0231, +0.0807] · @10 IC 0.0516 CI [-0.0010, +0.1022]
* Katman: counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı)
* Defterdeki referans (`state/component_ic.json`, cf/rvol20): {'5': 0.032, '10': 0.0456, '20': 0.0604}
* Eşleşme muhasebesi: {'bar_yok_sembol': 45, 'bar_yok_tarih': 0, 'kabul': 7077}

**EDG-002'nin ölçülmüş nesnesinin yeniden üretimi** (yeni K DEĞİL — bekçi):

| nesne | n | ort (20 bar, HAM) | %95 CI |
|---|---|---|---|
| EDG-002 raporu (s1_retro §3) | 433 | +1.61% | [+0.64%, +2.54%] |
| bu tur, aynı katman ve tanım | 430 | +1.60% | [+0.78%, +2.93%] |

> cf katmanı, rvol20>=2.5, HAM 20-bar ileri getiri (taban DÜŞÜLMEDİ) — EDG-002 raporundaki nesnenin BİREBİR aynısı. Yeni K harcamaz: ölçülmüş bir nesnenin yeniden üretimidir, yeni bir deneme değil.

**PK4 (yol tutarlılığı)** — GEÇTİ=True. fwd5: n=1258029, maks|fark|=0.0 · fwd10: n=1256766, maks|fark|=0.0 · fwd20: n=1254248, maks|fark|=0.0

**PK5 (özdeşlikler)** — GEÇTİ=True

* `C_hizli_ortalama`: n=50, maks|fark|=0.0, geçti=True
* `E_hizli_spearman`: geçti=True — n=5000: |fark|=0.0 · n=50000: |fark|=0.0 · n=208032: |fark|=0.0
* `F_temiz_taban_ozdesligi` @10: alt örnek 120000/1252244 satır, ayrışan=0, geçti=True · kanonik `temiz_taban` raporu: kirlilik=0.2252, gün birimi='sira/bar indeksi', pencere={'once': 10, 'sonra': 10}, n_olay=16646, n_olaysiz_kimlik=0, çözülemeyen=0
* `F_temiz_taban_ozdesligi` @20: alt örnek 120000/1252244 satır, ayrışan=0, geçti=True · kanonik `temiz_taban` raporu: kirlilik=0.397, gün birimi='sira/bar indeksi', pencere={'once': 20, 'sonra': 20}, n_olay=16646, n_olaysiz_kimlik=0, çözülemeyen=0

> **PK5 KAPSAM BEYANI.** PK5 — bu KARTIN kullandığı özdeşlikler.

    KAPSAM BEYANI: WP2 dalgasının PK5-A (as-of geriye-bakışsızlık), PK5-B (split bazı) ve PK5-D
    (fundamentals as-of) bacakları BU KARTTA UYGULANMAZ — kart yalnız OHLCV kullanır, hiçbir
    as-of/fundamentals serisi okumaz (kart notu: "yeni as-of gerektirmez, yalnız OHLCV").
    Uygulanmayan bir bekçiyi "geçti" diye raporlamak UYDURMA olurdu. Bu kartın PK5'i üç bacaktır:
      C  — hızlı ortalama-bootstrap ≡ satır-toplayan kanonik yol
      E  — hızlı Spearman ≡ kanonik analytics.spearman_ic
      F  — vektörel temiz-taban maskesi ≡ kanonik meridian.olcum_araclari.temiz_taban

**Artık ortogonallik bekçisi** — geçti=True · maks desil-içi ortalama 0.0 · maks gün-içi ortalama 0.0 · tekil gün (sürekli yol) 0

**Kod damgası** — motor kopyalandı (93 dosya), repo↔kopya aynı: True. Ölçüm anında repo çalışma ağacı KİRLİYDİ (başka ajanlar uçuşta). Motor kum havuzuna KOPYALANDI ve tüm koşumlar kopyadan yapıldı; dosya bazında sha256 kod_damgasi_017.json'da.

## 1. YÖNTEM BEYANI (kartın harfiyen uygulanması)

* **`universe`** — full_251 — KAPSAM BEYANLI: bar önbelleğinde dosyası olan ve şablon asgari uzunluğunu (TREND_TEMPLATE_WARMUP+65) geçen semboller; düşenler bar_muhasebesi'nde sayılı.
* **`veri_yolu`** — state/bars (SALT-OKUNUR) → dat.sanitize_bars (takvim kapısı, hayalet seans + bölünme-karantinası) → dat.measurement_bars (bars_integrity defteri: GÜVENSİZ DÖNEM DIŞLANIR) → dat.integrity_safe_start (HESAPLANAN ikinci yol). wp2_olcum dalgasıyla BİREBİR aynı yol; ölçüm ÇİVİSİ bu yolda kalibre.
* **`rvol20_tanimi`** — ind.rvol20 = hacim(t) / SMA20(hacim) — CANLI TANIM (indicators.py), kartın 'canlı tanımla BİREBİR' niteleyicisi. KART METNİ AYNI SATIRDA 'medyan20(hacim)' yazıyor; iki tanım AYNI DEĞİL. Ders#2 (eşik dilbilgisi) gereği belirsizlik BEYAN EDİLİR ve muhafazakâr okunur: hüküm taşıyan sayılar canlı (SMA) tanımıyla üretildi — çünkü (a) kart o dalı 'canlı tanımla BİREBİR (indicators.py kaynak)' diye niteliyor, (b) EDG-002'nin 2.5 kenarı ve pozitif-kontrol çivisi O tanımla ölçüldü. MEDYAN varyantı TANI olarak ayrıca verilir (CI YOK → K harcamaz).
* **`bolge`** — rvol20 >= 2.5 — FORM ŞARTSIZ (üçgen/bant dönüşümü UYGULANMADI); strategy.rvol_band_score'un 0'ladığı sağ kol.
* **`kesit`** — gözlem günü, o gün rvol20 tanımlı sembol sayısı >= 50; TEK KURAL, iki katmana da aynı uygulanır (aksi hâlde artık-katkı farkı kapsam farkıyla karışırdı).
* **`taban`** — aynı-gün EVREN ortalaması (ders#3: ham-getiri YASAK). İKİ SÜRÜM: (a) TEMİZ taban — ders#4/temiz_taban: olay-penceresi (h, h) İÇİNDEKİ satırlar tabandan DÜŞÜRÜLÜR ve kirlilik oranı raporlanır; HÜKÜM TAŞIYAN sürüm budur (kart guard'ı zorunlu kılıyor). (b) HAM taban — EDG-013/016 ile kıyaslanabilirlik için, temizlik YOK.
* **`olay_tanimi_ders4`** — olay = o sembolde rvol20>=2.5 olan seans; pencere (h, h) SEANS ORDİNALİ birimindedir (takvim günü değil) — ileri getiri h BAR olduğu için kirlilik 'olayın h-barlık penceresi bu satırınkiyle örtüşüyor mu' sorusudur. rvol20'si TANIMSIZ satır (ilk 19 bar) olay SAYILMAZ (olay ölçülemedi) ve tabana temiz girer — beyanlı.
* **`katman_2_kontrol`** — gün bazlı kesitte sürekli rvol20'nin DESİLİ (10 kova). A1: bölgenin AYNI-GÜN AYNI-DESİL leave-one-out taban fazlası. A2 (EDG-007): desil İÇİNDE bölge vs bölge-dışı farkı. B: gün bazlı kesit artığı e = 1{rvol>=2.5} − desil-içi ortalaması (desil kuklalarına OLS ile ÖZDEŞ) → havuzlanmış Spearman(e, FAZLA).
* **`ci`** — 21 ardışık gözlem günü blok-bootstrap, %95; ortalama 2000 / IC 600 tekrar
* **`maliyet`** — kart cost_model: 10.0bps sabit + 20.0bps duyarlılık satırı. Kill#3 kartın modeliyle (10bps) okunur; 20bps BEYANLI duyarlılıktır.
* **`K_beyani`** — Kart grid'i 2 katman → K+=2 (ÇARPILARAK; grid ekseni tek: `katman`). Ufuk 10/20 `horizon` alanıdır. Alt-dönem, desil dağılımı, bölge-içi bant, medyan tanım varyantı ve HAM-taban okumaları TANI'dır (CI yok / kart bacağı değil).
* **`hayatta_kalma_serhi`** — Evren `data.REPLAY_UNIVERSE` = bugün yaşayan likit isimler; delist edilmiş adlar YOK ve tarihsel üyelik nokta-zamanlı DEĞİL. Kartın kalıcı şerhi (EDG-016 emsali): POZİTİF bir bulguyu YUKARI çarpıtır; büyüklüğü bu veriyle ölçülemez.

## 2. ÖRNEKLEM, KESİT ve KIYAS TEMİZLİĞİ

* Barlar: 248/251 sembol yüklendi (dosya yok 1, kısa 2: ['HON', 'DD'])
* Takvim kapısı: hayalet seans satırı **428**, karantina **13**, takvim reddedilen sembol 0
* **Güvensiz dönem dışlaması**: kanonik defter yolu (`measurement_bars`) 46256 satır / 57 sembol; HESAPLANAN yol (`integrity_safe_start`) ek 0 satır; iki yolun ayrıştığı sembol: []
* Gözlem günü 5678 → kesiti yeterli (>= 50) gün **5658**; kesit medyanı 229.0 (min 145, maks 248)
* Tarih aralığı 2004-01-30 → 2026-07-28 · kesit satırı **1247489** (248 sembol; panel toplamı 1252244)
* `rvol20` dağılımı (kesit): {'0.01': 0.38262, '0.25': 0.738893, '0.5': 0.918045, '0.75': 1.159753, '0.95': 1.767169, '0.99': 2.698842}
* **Bölge (rvol20 >= 2.5): n=16646 satır, kesitin %1.33436'i**

### Ders #4 — kıyas temizliği (zorunlu üç alan: kirlilik oranı · pencere+birim · n_temiz)

| ufuk | pencere | gün birimi | taban satırı | kirli | temiz | **kirlilik oranı** | temiz taban medyan üye | ham taban medyan üye | temiz tabanı OLMAYAN gün |
|---|---|---|---|---|---|---|---|---|---|
| @10 | (10, 10) | sira/bar indeksi (SEANS ORDİNALİ) | 1249764 | 279999 | 969765 | **0.224041** | 175.0 | 230.0 | 0 |
| @20 | (20, 20) | sira/bar indeksi (SEANS ORDİNALİ) | 1247284 | 494544 | 752740 | **0.396497** | 135.0 | 229.0 | 0 |

> kirlilik_orani = olay-penceresi-İÇİ taban satırı / ölçülebilir taban satırı. EAP dersi: temizlenmemiş kıyas etkiyi SIKIŞTIRIR (olayı olayla kıyaslar).

## 3. KATMAN 1 — `rvol25_bolge_fazlasi` (KAYITLI GRID HÜCRESİ 1/2)

Bölge: 16646 sembol-gün · 4642 gün · 248 sembol · bölge içi rvol20 medyanı 3.011925 (ort 3.42323, p95 5.734472)

| ufuk | ölçüt | n | ort | %95 CI (21g blok) | CI 0'ı dışlıyor mu |
|---|---|---|---|---|---|
| @10 | **TEMİZ evren-fazlası (HÜKÜM)** | 16633 | -0.028% | [-0.208%, +0.150%] | hayır |
| @10 | ham-taban evren-fazlası (kıyas) | 16633 | +0.025% | [-0.129%, +0.179%] | hayır |
| @10 | HAM getiri (ders#3: ölçüt DEĞİL) | 16633 | +0.455% | [+0.031%, +0.835%] | **EVET** |
| @20 | **TEMİZ evren-fazlası (HÜKÜM)** | 16627 | +0.050% | [-0.200%, +0.279%] | hayır |
| @20 | ham-taban evren-fazlası (kıyas) | 16627 | +0.099% | [-0.104%, +0.295%] | hayır |
| @20 | HAM getiri (ders#3: ölçüt DEĞİL) | 16627 | +1.121% | [+0.465%, +1.710%] | **EVET** |

Temiz taban bulunamadığı için düşen bölge satırı: @10: 0 · @20: 0

## 4. KATMAN 2 — `rvol25_artik_rvol_surekli_kontrollu` (KAYITLI GRID HÜCRESİ 2/2)

Kontrol: gün bazlı kesitte sürekli rvol20 DESİLİ (10 kova)

**Bölgenin kontrol desillerine dağılımı** — bölge (rvol>=2.5) satırlarının kontrol desillerine dağılımı — kontrolün GERÇEKTEN çalışıp çalışmadığının ön koşulu: bölge tek bir desilde toplanıyorsa kontrol o desilin İÇİNDE ayrım arıyor demektir (ve bunu söylemek zorundayız).

| desil | n | bölge n | bölge payı |
|---|---|---|---|
| 0 | 121496 | 0 | %0.0 |
| 1 | 124510 | 0 | %0.0 |
| 2 | 125296 | 0 | %0.0 |
| 3 | 124602 | 0 | %0.0 |
| 4 | 123387 | 0 | %0.0 |
| 5 | 125587 | 0 | %0.0 |
| 6 | 125321 | 16 | %0.012767 |
| 7 | 124577 | 93 | %0.074653 |
| 8 | 125229 | 526 | %0.420031 |
| 9 | 127484 | 16011 | %12.559223 |

### 4.1 A1 — kova (desil) tabanlı bölge fazlası

> KAYITLI dilim (rvol>=2.5 bölgesi) — taban EVREN yerine AYNI-GÜN AYNI-DESİL leave-one-out ortalaması (gözlemin kendisi tabana girmez). Katman 1 ile TEK farkı tabandır; aradaki düşüş doğrudan sürekli-rvol kontrolünün bedelidir.

| ufuk | n | LOO desil-fazlası | %95 CI | CI 0'ı dışlıyor mu | kendini-içeren varyant (CI YOK) | kova yetersiz düşen |
|---|---|---|---|---|---|---|
| @10 | 16633 | -0.006% | [-0.124%, +0.112%] | hayır | -0.006% | 0 |
| @20 | 16627 | +0.063% | [-0.086%, +0.218%] | hayır | +0.060% | 0 |

### 4.2 A2 — EDG-007 çift-sıralama (desil İÇİNDE bölge − bölge-dışı)

> EDG-007 çift-sıralama şablonu: her rvol DESİLİNDE bölge (rvol>=2.5) üyeleri vs aynı desilin bölge-dışı üyeleri; hücre farkları + desil-içi merkezlenmiş havuzlanmış yayılım.

**@10 havuzlanmış** (nA=16633, nB=1228418): fark -0.006% · CI [-0.123%, +0.107%] · CI 0-dışı hayır

| desil | n bölge | n bölge-dışı | ort bölge | ort bölge-dışı | fark | %95 CI | 0-dışı |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 121259 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 1 | 0 | 124260 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 2 | 0 | 125052 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 3 | 0 | 124355 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 4 | 0 | 123151 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 5 | 0 | 125340 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 6 | 16 | 125062 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 7 | 93 | 124240 | +1.534% | +0.564% | +0.970% | [+0.088%, +2.229%] | **EVET** |
| 8 | 526 | 124459 | +0.811% | +0.613% | +0.198% | [-1.342%, +1.519%] | hayır |
| 9 | 15998 | 111240 | +0.438% | +0.700% | -0.263% | [-0.551%, -0.010%] | **EVET** |

**@20 havuzlanmış** (nA=16627, nB=1225944): fark +0.064% · CI [-0.081%, +0.210%] · CI 0-dışı hayır

| desil | n bölge | n bölge-dışı | ort bölge | ort bölge-dışı | fark | %95 CI | 0-dışı |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 121020 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 1 | 0 | 124014 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 2 | 0 | 124798 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 3 | 0 | 124109 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 4 | 0 | 122911 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 5 | 0 | 125091 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 6 | 16 | 124811 | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _dilim < 30_ |
| 7 | 93 | 123984 | +2.684% | +1.121% | +1.562% | [-0.466%, +3.282%] | hayır |
| 8 | 526 | 124208 | +1.367% | +1.163% | +0.204% | [-1.858%, +1.846%] | hayır |
| 9 | 15992 | 110998 | +1.101% | +1.327% | -0.226% | [-0.609%, +0.143%] | hayır |

### 4.3 B — artık-IC (desil kuklası artığı ↔ TEMİZ-taban fazla getirisi)

> havuzlanmış Spearman IC. HEADLINE: DESİL artığı ↔ TEMİZ-taban FAZLA getirisi. Artık gün-içinde zaten merkezlidir; ham getiriyle havuzlanmış IC gün-düzeyi varyansla sulandırılırdı (ham okuma TANI olarak var).
>
> **Beraberlik şerhi.** Bölge üyesi OLMAYAN desillerde artık TAM SIFIRDIR (o desilde gösterge sabittir) → havuzlanmış Spearman'da büyük bir beraberlik kütlesi oluşur ve IC'yi SIFIRA doğru seyreltir. Bu yüzden aynı IC bir de YALNIZ bölge üyesi bulunan desillerde raporlanır.

| ufuk | okuma | IC | n | %95 CI | CI 0'ı dışlıyor mu |
|---|---|---|---|---|---|
| @10 | **desil-artık IC (HÜKÜM)** | -0.0030 | 1245052 | [-0.0054, -0.0005] | **EVET** |
| @10 | desil-artık IC · yalnız bölgeli desiller | -0.0047 | 501634 | [-0.0080, -0.0017] | **EVET** |
| @10 | sürekli pctrank artık IC (robustluk) | +0.0006 | 1245052 | [-0.0032, +0.0044] | hayır |
| @10 | ham rvol20 IC (TANI) | -0.0022 | 1245052 | [-0.0063, +0.0019] | hayır |
| @10 | desil-artık IC, HAM getiri (TANI, CI YOK) | -0.0028 | 1245052 | _ölçülemedi_ | _CI istenmedi (tanı okuması — kart bacağı değil)_ |
| @20 | **desil-artık IC (HÜKÜM)** | -0.0020 | 1242572 | [-0.0044, +0.0004] | hayır |
| @20 | desil-artık IC · yalnız bölgeli desiller | -0.0048 | 500629 | [-0.0084, -0.0017] | **EVET** |
| @20 | sürekli pctrank artık IC (robustluk) | +0.0052 | 1242572 | [+0.0011, +0.0088] | **EVET** |
| @20 | ham rvol20 IC (TANI) | -0.0054 | 1242572 | [-0.0099, -0.0008] | **EVET** |
| @20 | desil-artık IC, HAM getiri (TANI, CI YOK) | -0.0007 | 1242572 | _ölçülemedi_ | _CI istenmedi (tanı okuması — kart bacağı değil)_ |

## 5. MALİYET-SONRASI NET (kill#3'ün okunduğu yer)

> Maliyet SABİT olduğundan CI aynı sabitle ötelenir (cebirsel özdeş). Kart modeli 10.0bps; 20.0bps BEYANLI duyarlılıktır.

| ufuk | katman | model | brüt | maliyet | **net** | net CI | net CI 0-dışı pozitif |
|---|---|---|---|---|---|---|---|
| @10 | katman 1 (evren fazlası) | kart 10.0bps | -0.028% | +0.100% | **-0.128%** | [-0.308%, +0.050%] | False |
| @10 | katman 1 (evren fazlası) | duyarlılık 20.0bps | -0.028% | +0.200% | **-0.228%** | [-0.408%, -0.050%] | False |
| @10 | katman 2 A1 (desil fazlası) | kart 10.0bps | -0.006% | +0.100% | **-0.106%** | [-0.224%, +0.012%] | False |
| @10 | katman 2 A1 (desil fazlası) | duyarlılık 20.0bps | -0.006% | +0.200% | **-0.206%** | [-0.324%, -0.088%] | False |
| @20 | katman 1 (evren fazlası) | kart 10.0bps | +0.050% | +0.100% | **-0.050%** | [-0.300%, +0.179%] | False |
| @20 | katman 1 (evren fazlası) | duyarlılık 20.0bps | +0.050% | +0.200% | **-0.150%** | [-0.400%, +0.079%] | False |
| @20 | katman 2 A1 (desil fazlası) | kart 10.0bps | +0.063% | +0.100% | **-0.037%** | [-0.186%, +0.118%] | False |
| @20 | katman 2 A1 (desil fazlası) | duyarlılık 20.0bps | +0.063% | +0.200% | **-0.137%** | [-0.286%, +0.018%] | False |

**Spread daralması beyan notu** (kart metni: _cost_model: 'yüksek-rvol günü spread daralması beyan-notu'_)

> SABİT bps maliyet modeli, yüksek-rvol günlerinde gerçekleşen spread DARALMASINI taşımaz; yani net rakam bu yönde MUHAFAZAKÂRDIR. Bu depoda gerçek spread serisi YOK → daralmanın büyüklüğü ÖLÇÜLEMEDİ (uydurma yasağı). Aşağıdaki dolar-hacim kıyası yalnız BETİMLEYİCİ dolaylı kanıttır, CI yoktur ve kart bacağı DEĞİLDİR.

* gerçek spread serisi: **None** — depoda gün-içi kotasyon/spread verisi yok (yalnız günlük OHLCV)
* betimleyici dolaylı kanıt: bölge medyan dolar hacmi 732505804.35 vs evren 230233040.32 (oran 3.181584)

## 6. ALT-DÖNEM KARARLILIK (BETİMLEYİCİ — grid'e dahil DEĞİL)

> BETİMLEYİCİ — kart notu: 'alt-dönem kararlılık satırı rapora eklenir (grid'e dahil değil, betimleyici)'. CI blok-bootstrap ile verilir ama HÜKÜM TAŞIMAZ ve K harcamaz: dönem sınırları ölçümden ÖNCE sabitlendi ve hiçbir dönem 'seçilmedi'.
>
> **2018 hayaleti şerhi.** s1_retro (BT-2) tespiti: 2018-11-22 hayalet seansı ve genel olarak UZUN GEÇMİŞ artefaktları O turda AKLANMADI. Bu turda takvim kapısı (sanitize_bars) hayalet seansları düşürür — bar_muhasebesi.hayalet_dusen sayısı raporda durur — ama '2018 aklandı' DENMEZ; alt-dönem satırı tam da bu yüzden vardır.

| dönem | aralık | n | @10 fazla | @10 CI | @20 fazla | @20 CI |
|---|---|---|---|---|---|---|
| ...-2014 | … → 2014-12-31 | 7533 | +0.186% | [-0.085%, +0.459%] | +0.353% | [-0.064%, +0.729%] |
| 2015-2018 | 2015-01-01 → 2018-12-31 | 3168 | -0.030% | [-0.307%, +0.274%] | +0.116% | [-0.268%, +0.479%] |
| 2019-2022 | 2019-01-01 → 2022-12-31 | 2876 | -0.392% | [-0.985%, +0.040%] | -0.354% | [-1.037%, +0.177%] |
| 2023-... | 2023-01-01 → … | 3069 | -0.209% | [-0.548%, +0.147%] | -0.387% | [-0.906%, +0.136%] |
| **2018 HARİÇ** | tüm örneklem − 2018 | 15923 | -0.019% | [-0.205%, +0.156%] | +0.053% | [-0.198%, +0.292%] |

## 7. TANI (K harcanmaz — CI'sız okumalar hüküm taşımaz)

### 7.1 Bant tablosu — panel karşılığı

> EDG-002'nin cf-katman bant tablosunun PANEL karşılığı (temiz-taban fazlası ve ham). s1_retro'nun panel tanısı bant yapısının panelde DÜZLEŞTİĞİNİ söylüyordu; bu satır o okumayı bu turun verisiyle tekrarlar.

**@10**

| rvol bandı | n | temiz-taban fazlası | ham ort |
|---|---|---|---|
| 0.0-0.8 | 416903 | -0.027% | +0.611% |
| 0.8-1.5 | 709101 | -0.058% | +0.610% |
| 1.5-2.0 | 80416 | -0.025% | +0.457% |
| 2.0-2.5 | 21995 | -0.053% | +0.421% |
| 2.5-3.0 | 8190 | +0.021% | +0.528% |
| 3.0-4.0 | 5404 | -0.098% | +0.360% |
| 4.0-inf | 3039 | -0.034% | +0.427% |

**@20**

| rvol bandı | n | temiz-taban fazlası | ham ort |
|---|---|---|---|
| 0.0-0.8 | 415571 | -0.017% | +1.179% |
| 0.8-1.5 | 708023 | -0.121% | +1.203% |
| 1.5-2.0 | 80364 | -0.065% | +1.101% |
| 2.0-2.5 | 21983 | -0.012% | +1.129% |
| 2.5-3.0 | 8186 | +0.016% | +1.140% |
| 3.0-4.0 | 5403 | -0.020% | +1.060% |
| 4.0-inf | 3038 | +0.266% | +1.177% |

### 7.2 Kart metnindeki İKİNCİ rvol tanımı (medyan20)

> Kart METNİNİN yazdığı ikinci tanım: rvol = hacim/MEDYAN20(hacim). CI YOK → K harcamaz; hüküm taşıyan sayı SMA (canlı) tanımıyladır.

* Bölge n (medyan tanımı): 30126 · iki tanımın Spearman'ı: 0.966678

| ufuk | n | temiz-taban fazlası (CI YOK) |
|---|---|---|
| @10 | 30096 | -0.028% |
| @20 | 30085 | +0.049% |

### 7.3 cf katmanı ↔ panel popülasyon farkı

> EDG-002'nin +1.61% gözlemi cf (kırılım adayı) KATMANINDA ölçüldü; bu kart `universe: full_251` + `kesit dilim: günlük gözlem` diyor, yani PANEL. İki popülasyon aynı değildir ve s1_retro paneli ayrıca ölçüp 'pozitif hacim etkisi KIRILIM popülasyonuna koşulludur, evrensel değil' demişti. Bu turda cf-katman yeniden üretimi bekçiler bölümünde (EDG-002 nesnesinin birebir kopyası) durur; hüküm taşıyan hücreler PANELDEN gelir.

* cf katmanında bölge n = 430 · panelde bölge n = 16646

## 8. KILL / SUCCESS ÖLÇÜTLERİNİN SAYISAL KARŞILIKLARI

> **Bu blok VERİDİR, hüküm DEĞİLDİR. Kartın kill/success metinleri BİREBİR kopyalanmış ve her birinin sayısal karşılığı yanına yazılmıştır. Hangi dalın tetiklendiğine Rol-1 karar verir; bu ajan kart dosyasına DOKUNMADI.**

### 8.1 success_metric

Kart metni (birebir): _rvol>=2.5 bölge fazlası @20 anlamlı POZİTİF (CI 0-dışı) VE artık-katkı anlamlı: sürekli rvol20 (desil-kontrol, EDG-007/016 çift-sıralama şablonu) hesaba katıldıktan sonra >=2.5 bölgesi hâlâ bilgi taşıyor (kova-tabanı VE artık-IC iki yöntemde de aynı yön + en az birinde CI 0-dışı)._

| bileşen | nokta | %95 CI | CI 0'ı içeriyor mu |
|---|---|---|---|
| bölge fazlası @20 (katman 1, temiz taban) | +0.050% | [-0.200%, +0.279%] | True |
| kova-tabanı @20 (A1) | +0.063% | [-0.086%, +0.218%] | True |
| artık-IC @20 (B) | -0.0020 | [-0.0044, +0.0004] | True |

* iki yöntem (A1, B) aynı yön @20: **False**
* en az birinde CI 0-dışı @20: **False**

### 8.2 kill ölçütleri

| kill | kart metni (birebir) | sayısal karşılık | CI 0'ı içeriyor mu / net |
|---|---|---|---|
| #1 | bölge fazlası @20 CI-0-içi → bilgisiz, arşiv (EDG-002 yan gözlemi pencere-artefaktıydı — karta not düşer) | @20 fazla +0.050% CI [-0.200%, +0.279%] (bilgi: @10 -0.028% CI [-0.208%, +0.150%]) | **True** |
| #2 | artık yok (sürekli-rvol açıklıyor: kontrol sonrası CI-0-içi) → 'monoton devam' arşiv; canlı eşik yeterli, yeni mekanizma açılmaz | A1 @20 +0.063% CI [-0.086%, +0.218%] · B @20 IC -0.0020 CI [-0.0044, +0.0004] | A1: **True** · B: **True** |
| #3 | maliyet-sonrası net fazla <=0 (10bps) → 'brüt-var-net-yok' arşiv + not | @20 net -0.050% CI [-0.300%, +0.179%] (bilgi: @10 net -0.128%) | net ort > 0: **False** · net CI 0-dışı pozitif: **False** |

**@10 bilgi satırları (kart ölçütü @20'dir, @10 `horizon` alanının ikinci ufkudur):**

* kill#2 A1 @10: -0.006% CI [-0.124%, +0.112%] · B @10 IC -0.0030 CI [-0.0054, -0.0005]
* kill#3 @20 duyarlılık (20.0bps): net -0.150% CI [-0.400%, +0.079%]

### 8.3 guard karşılıkları

| guard | karşılık |
|---|---|
| pozitif kontrol (rvol20 @20 IC ≈0.0642) | çivi **0.0642** → GEÇTİ=True |
| PK4 yol tutarlılığı | True |
| PK5 özdeşlikler | True |
| temiz_taban (aynı-gün evren) zorunlu | True |
| eşik dilbilgisi (ders#2) belirsizliği | rvol20 tanımı: kart metni 'medyan20' der, aynı satırda 'canlı tanımla BİREBİR (indicators.py)' der; canlı tanım SMA20'dir. Muhafazakâr/beyanlı okuma uygulandı (bkz. kart_metni_uygulamasi.rvol20_tanimi); MEDYAN varyantı TANI olarak v_tani'de. |

---

Bu rapor `rapor_017.py` tarafından YALNIZ `sonuc_017.json`dan üretildi; hiçbir sayı elle taşınmadı. Kart dosyasına dokunulmadı ve hiçbir hüküm cümlesi kurulmadı.
