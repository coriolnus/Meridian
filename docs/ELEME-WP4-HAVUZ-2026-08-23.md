# ELEME — WP4 STOK + HAVUZ KART-ADAYI ÜÇLÜSÜ (2026-08-23)

**Ajan beyanı:** Salt-okuma eleme turu; tek yazım bu dosya. Kod/kart/state'e dokunulmadı, git
koşulmadı. Bu belge ÖNERİ üretir — hükmü Rol-1 işler (CLAUDE.md md.3).

**Ölçüm tabanı beyanı:**
- Yerel repo (main, a033256) + yerel `state/` (BAYAT ayna: çoğu dosya 2026-07-30; yalnız kod/kart/doc kanıtı için kullanıldı).
- Canlı A1 (`/opt/meridian`, ubuntu@130.61.126.87) SALT-OKUMA SSH: `ls`/`grep`/`awk`/`head` — tek bayt yazılmadı.
- ÖLÇÜLEMEYENLER (uydurma yasağı): (i) canlı `trades` damga sayımı = **None** — defter SQLite arka
  ucunda (`state/meridian.db`) ve canlıda `sqlite3` CLI yok; son ölçüm 2026-08-14: 887/887 damgalı
  (ROADMAP §4-37). (ii) `ledger_matches_bars` gece-deep güncel çıktısı = **None** — kalıcı artefakt
  dosyası bulunamadı (pano yolu yalnız canlı dilime bakar, `recompute.py:187-189`); tohum-dilimi
  kırmızılarının bugünkü hâli bu turda okunamadı.

---

## [A] WP4 STOK KALEMLERİ

### A1 · Türetilmiş artefaktların (component_ic / cf / eşik eğrileri) güvensiz-dönem-dışlamalı yeniden üretimi

**Bugünkü gerçek (ölçüldü):**
- Üretici üçlüsü dışlama kapısına KABLOLU: `component_ic.py:348,373` (`measurement_bars` — evrenle
  aynı kapı), `cf_backfill.py:178,191`, `threshold_curve.py` aynı popülasyon/çerçeveyi
  `cic._load_universe()` üzerinden tüketir (`threshold_curve.py:110-140`; DD 7-satır dışlaması
  `cic.eslesme_nedeni` ile sınıflı).
- Yeniden üretim GECELİK VE OTOMATİK: P5 döngüsü her gün `component_ic()` + `threshold_curve.build()`
  koşar (`loop.py:2156-2167`).
- Canlı artefaktlar TAZE: `component_ic.json` ve `threshold_curve.json` mtime **2026-08-21 20:33**
  (son seans kapanışı; 08-22/23 hafta sonu — kadans gereği koşum yok). `component_ic.json` içinde
  `bars_integrity` bar-taban damgası **VAR** (dışlama-sonrası üretim kanıtı; yerel bayat kopyada YOKTU).
- cf defteri (`counterfactuals.jsonl`, canlı mtime 2026-08-21 20:31): tarihçe satırları yerinde
  yeniden üretilmez AMA her kanonik tüketici okuma anında aynı kapıdan filtreler ve cf satırı depo
  yasası gereği hüküm taşımaz — defter-içi yeniden yazım gerektiren tüketici bulunamadı.

**ÖNERİ: KAPAT-BAYAT (kanıtlı).** Kalem "bir kez yeniden üret" diye doğmuştu; bugün yeniden üretim
yapısal (gecelik) ve damgalı. İki tek-satırlık kuyruk not olarak düşülebilir, kalemi açık tutmaz:
(a) `threshold_curve.json` KENDİ bar-taban damgasını taşımıyor (canlıda 0 eşleşme) — YASA-6
tamlığı için `component_ic`teki `_bars_taban()` deseninin tek satırlık kopyası; (b) cf tarihçe
satırlarının filtre-anında dışlandığı bu belgede beyanlı.

### A2 · Seans-içi boşluk dedektörü genişletmesi (eski "5.3 seans-içi kesinti/boşluk tespiti")

**Bugünkü gerçek (ölçüldü):**
- Dedektör SEVK EDİLMİŞ ve CANLIDA ÇALIŞIYOR: `scheduler._intraday_gap_check` (`scheduler.py:826`,
  her 5-dk poll) → `barsarchive.gap_scan` (60-dk kuyruk penceresi, gerçek-seans takvimi,
  takvim_yok fail-declared zinciri). Sevk: aaa7a40 (2026-08-01) + 58e4a82/8dc7c8b (2026-08-02, çivi v175).
- Canlı olay defteri (2026-07-14→bugün): **3.321 `intraday_gap_detected`**, 15 seans günü, SON
  ateşleme 2026-08-21 (son seans). Kırılım: **3.321/3.321 `sembol`**, **0 `akis`** (gerçek besleme
  kesintisi sınıfı hiç doğmadı).
- Sembol-boşluğu sınıfı ÖLÇÜLMÜŞ YAPISAL GÜRÜLTÜ: IEX tek borsa — 15 rastgele alarmın 15'i
  konsolide beslemede DOLU, 0 gerçek kesinti (`scheduler.py:803` notu); seviye bilerek info'ya
  indirilmiş, `akis` warn kalmış.

**ÖNERİ: KAPAT-BAYAT (kanıtlı).** ROADMAP WP4-B'deki "5.3 ... tespiti" satırı sevkten önce yazılmış
ve bayat. "Genişletme" (60-dk kuyruğun ötesine tam-seans tarama, sembol kapsamı vb.) için bugün
ölçülmüş bir tüketici yok; sembol tarafı zaten yapısal-gürültü damgalı — genişletme sinyal değil
alarm hacmi büyütür. Yeni bir kesinti sınıfı kanıtı doğarsa yeni kalem olarak açılmalı.

### A3 · Earnings kapsama + fail-open daraltma

**Bugünkü gerçek (ölçüldü):**
- Kapsam BUGÜN **216/251 (%86,1)** — canlı `earnings.csv` (son tazeleme 2026-08-17, haftalık kadans
  içinde) × `REPLAY_UNIVERSE` (251). ROADMAP'teki 194/251 sayısı eskimiş.
- Kapsam dışı **35 sembol**: ABT ADBE AZO BAC BKR BLK C CAG CCL COST DAL FDX GE GIS GS ISRG JNJ JPM
  KR MKC MS MU NFLX NKE ORCL PEP PGR PLD PNC STZ TRV UAL UNH USB WFC. Dikkat: kapsam MEVSİMSELDİR —
  tazeleme penceresi [bugün−7, bugün+21] olduğundan, penceresinde raporu olmayan sembolün CSV'de
  olmaması tek başına arıza değil (birikim geçmiş çapaları silmez; sayı rapor sezonuyla büyür).
- Tazeleme hattı SAĞLIKLI: canlı olay defterinde son arıza uyarısı 2026-07-19
  (`earnings_calendar_gave_up`); o günden beri partial/gave-up SIFIR. FMP yedeği (eşik 0,90),
  9-gün marj, hayalet-tarih temizliği kodda (`earnings.py`).
- Fail-open BEYANLI TASARIM: sembol kapsam dışıysa `in_blackout` False (fail-open, beyanlı not);
  takvim ufku taşıyamıyorsa fail-closed (`earnings.py` modül başlığı). "Daraltma" kararı hâlâ açık —
  ama fail-open'ın GERÇEKLEŞMİŞ bedeli hiç sayılmadı.

**ÖNERİ: ÖLÇ (K-tahminli + eşik-taslaklı).** Daraltma tasarımına girmeden önce bedel sayılmalı;
PIT birikimi (`state/history/earnings_snapshots.jsonl`, 2026-08-01'den beri) bunu retro ve
sızıntısız mümkün kılıyor.
- **Kart taslağı:** "fail-open gerçekleşmiş bedeli" — retro sayım: her CANLI giriş anında sembol
  kapsam-dışı mıydı × sonradan öğrenilen gerçek rapor tarihi girişten ≤5 gün sonra mıydı
  (PIT anlık görüntüsüyle, bugünkü takvimle DEĞİL).
- **K-tahmini: hükümlü hücre 1** (tek retro sayım, grid yok; kalan çıktı betimleyici).
- **Eşik taslağı (donuk):** vaka N≥1 → "daraltma tasarımı" WP4 iş kalemine döner (aday yollar:
  kapsam-dışı sembole FMP nokta-sorgu ya da kapsam-dışılık ≥X gün sürerse sembol-bazlı
  fail-closed); N=0 → fail-open beyanlı kalır, kalem ÖLÇÜLMÜŞ-RETLE kapanır.

### A4 · MNST split düzeltmesi (kart-önce)

**Bugünkü gerçek (ölçüldü):**
- Teşhis TAM (docs/TESHIS-MNST-SPLIT-2026-08-12.md): iki semptom tek kök — kaynak-kıyas kör-yüzde
  (`data.py:953-955` oran-imza tanımaz) × defter retro-değişmez; yön A1 (oran-imza) + A2
  (kümülatif-katsayı defteri), kart ön-kayıtlı ölçüm-değişikliği şartı yazılı.
- Kart YOK: `research/cards/` içinde split kartı bulunamadı. Kod YOK: `oran-imza`/`ratio_signature`
  için repo genelinde 0 eşleşme.
- Canlı semptom BUGÜN SESSİZ: `data_quality.json` (2026-08-21) `index_ok: true`,
  `tickers_failed: []`, `data_halt: false`, `crosscheck: source_lagging` (MNST vakası değil) —
  nasdaq tabanı yetişmiş, %50 yanlış-alarmı geçmiş. `ledger_matches_bars` tohum kırmızıları
  (T00020/T00095) pano yolunun kapsamı dışında (`recompute.py:187-189`); gece-deep güncel hâli
  ölçülemedi (yukarıdaki beyan).
- YAPISAL KÖRLÜK DURUYOR: bir sonraki split'te (evrende herhangi bir sembol) aynı yanlış-alarm +
  defter-bar kırmızı sınıfı yeniden doğar; MNST turnover ~2× şişme izlemede.

**ÖNERİ: ÖLÇ (K-tahminli + eşik-taslaklı)** — teşhisin kendi şartı zaten "kart-önce"; eleme turunun
katkısı kartın iskeletini hazırlamak:
- **Kart taslağı:** A1 oran-imza tanıma — `_massive_crosscheck` sapması `dev > MASSIVE_TOL` iken
  oran kümesi {1/4, 1/3, 1/2, 2, 3, 4} × tek tolerans ile "taban-farkı" sınıfına ayrılır;
  retro doğrulama penceresi 2026-07-14→bugün + Massive `/stocks/v1/splits` dış-takvimi (PIT).
- **K-tahmini: hükümlü hücre 1** (tek kural + tek tolerans; oran kümesi sabit, taranmaz).
- **Eşik taslağı (donuk):** retro pencerede bilinen split günlerinde (MNST 2026-08-11) yanlış-alarm
  1→0'a iner VE split-dışı günlerde sapma sayımı değişmez (yanlış-pozitif 0) → A1 sevk edilebilir;
  A2 katsayı defteri ayrı adım (tohum kırmızılarını "bilinen katsayı 2×" beyanlı-yeşile çevirir,
  retro-değişmezlik korunur).

**GÜNCELLEME 2026-08-24 — A4 ÖLÇÜLDÜ, KALEM KAPANDI (yukarıdaki "ÖNERİ: ÖLÇ" bloğu tarihiyle
kalır, silinmez).** Kart `research/cards/EDG-2026-056-split-oran-imzasi.yaml` ön-kayıtlandı ve
retro tarama koştu (K=1, hücre `oran_imza_retro`):
`research/olcumler/edg056_oran_imzasi_2026-08-24/` (`sonuc.json` + `RAPOR.md`).

- Donmuş yer gerçeği: `bilinen_split_donuk.json`
  sha256 `60177962804f9b0b63c446b0d80ac0e013c3ae0f8c81c9f6a41c605d6d48fbb7`
  (kaynak `state/bars_integrity.json` K1 `olcek_dikisi`, 92 olay; sha256
  `ab6b2e5995ba3084782cbcedc2982a7d56d0d16a6245cadff14e74e5edfdedcc`). `state/quarantine/`
  ÖLÇÜLDÜ: sıfır bölünme kaydı (yalnız constituents FIXTURE'ı).
- Tarama: 260 dosya · 1.349.764 bar çifti · SALT-OKUMA (motor import edilmedi).
- Sonuç: aday **55** · bilinen-split eşleşen **32** · eşleşmeyen aday **23** · yakalanmayan
  bilinen split **60/92** → yanlış-pozitif **%41,8** (eşik ≤%20) · yakalama **%34,8** (eşik ≥%80).
- **HÜKÜM (karar kuralı doğrudan okundu): "imza tek başına yetersiz."** Dedektör kablolaması
  YAPILMAZ; bölünme körlüğü BEYANLI kalır. Kartın kendi tanımladığı ikinci çıkış budur.
- Yan bulgu (RAPOR §3b): eşleşmeyen 23 adayın 5'i 2025-05-26 hayalet seansıdır (DD·HON·KLAC·
  NFLX·NOW, vr/r = 1,000) — `docs/RUNBOOK.md:1310` vakasının birebir kendisi; imza onları
  mükemmel yakalıyor ama o sınıf karantina hattınındır (`data.py:531`), bu kartın değil.

---

## [B] HAVUZ KART-ADAYI ÜÇLÜSÜ (ROADMAP §4 tam metinden)

### B1 · Ö-45 — "28d teşhisi: eşik düşürmek bu tıkanıklığı açmaz" (ROADMAP:1879-1896)

**Ne istiyor (tam metinden):** 28d'nin örtük çözümü olan eşik indirimi ölçümle KONUSUZ çıktı
(`chop` OOS'un %4,7'si, teyit diliminde 0 işlem, 2025-07-01'den beri 394 günde hiç chop; `max(10,…)`
tabanı yüzünden eşik 30→10 olsa bile @chop teyitte ölçülemez). Kalan gerçek iş: "sınıflayıcının
chop tanımını ölçmek — kart-önce" (dar kalibrasyon mu, gerçekten chop yok mu?).

**Bugünkü kodla/kartla çarpışma:** Bu ölçümün TÜKETİCİSİ bugün kapandı. `EDG-2026-048-chop-tabani`
(kart 2026-08-23 ön-kayıtlı, AYNI GÜN ölçüldü, status: measured) hükmü: **NO-GO — ölçülmüş ret**
(Δ(taban60−taban45) = −18.266$, CI95 [−47.734, +10.589]; chop açılımı 417 chop işlemi −26,3R üretti
VE +22,6R'lik 99 chop-dışı işlemi yerinden etti). Hüküm metni ayrıca: "chop kapalılığı artık
ÖLÇÜLMÜŞ POLİTİKA; @chop hipotez üretiminin duraklatılması (K1 paketi) daha da gerekçeli — 28d
kapısının @chop dilimi kapanır. Canlanma yalnız yeni dünya/yeni kartla."

**ÖNERİ: KAPAT-BAYAT (kanıtlı).** Ö-45'in istediği ölçümün karar-tüketicisi (@chop öğrenmesi/eşiği
açılsın mı) EDG-048 NO-GO'suyla kapandı; replay 417 chop işlemi "sınıflayıcı hiç chop üretmiyor"
endişesinin pencere-bağımlı olduğunu da gösterdi (chop var, para etmiyor). Sınıflayıcı tanımını
ölçmek artık sahipsiz bir ölçüm olur. Tek satır kalıntı: az-tespitin RİSK tarafı (gerçek chop'ta
bütçe kısılamaması) ayrı ve bugün kanıtsız bir soru — istenirse yeni, kendi gerekçeli kalem;
Ö-45'in metni onu içermiyor.

### B2 · Ö-47 — "28i: sapma tek fold'dan gelmiyor, gelemez" (ROADMAP:1912-1923)

**Ne istiyor (tam metinden):** fold3 = 38 günlük ARTIK (takvim sınırı 2025-07-01 × %70 kesimi
2025-08-18); kapı `n=36, avg_r=−0,2223` oylarken aynı dönem tam uzunlukta `n=249, +0,2140`;
0,772'lik holdout sapması 91-günlük ayrı pencerenin kendi getirisi. Gerekli iş: "artık-fold ve
91 günlük holdout penceresinin meşruiyeti — kart-önce."

**Bugünkü kodla çarpışma:**
- ARTIK-FOLD OYLAMASI YAPISAL OLARAK KAPANDI: kapı fold'ları artık N-DENGELİ kesiliyor —
  `reflect.py:411-430` sınırları incumbent Search-OOS işlem damgalarından türetir; `backtest.py`
  `FOLD_MIN_N = 15` SERT TABAN ("n<15 pencere oy kullanamaz"), `FOLD_K_TRY (3,2)`, taban tutmazsa
  takvime dönüş ADIYLA görünür. `fold_total == 1 → majority UNPROVABLE` yasası da yerinde
  (`reflect.py:374-377`).
- CANLIDA AKTİF (ölçüldü): kapı kayıtlarında `fold_law` = **23 × n_dengeli · 3 ×
  n_dengeli_taban_tutmadi · 0 × takvim**. 38-günlük artık dilim kapı oylamasına artık giremez
  (takvim fold'ları yalnız rapor katmanında, bilerek — önbellek anahtarı korunur).
- 91-GÜN HOLDOUT: hüküm-dışılık TASARIMLA garanti — "holdout never drives acceptance"
  (`reflect.py:1446`, `backtest.py:735-736,937`); sapma yalnız `overfit_suspect` bayrağı üretir
  (`HOLDOUT_DIVERGENCE = 0.10`). Pencerenin uzunluğu/rotasyonu ayrıca SAHİPLİ: WP5-A "2D R2
  holdout rotasyonu (zamanı gelince)" kalemi + `dataset.py` R1 blok (rotasyon disiplini yazılı).

**ÖNERİ: KAPAT-BAYAT (kanıtlı); holdout kuyruğu BİRLEŞTİR → WP5-A "2D R2 rotasyonu".** Artık-fold
yarısı mekanizmayla kapanmış ve canlıda ölçülmüş; 91-gün penceresinin "meşruiyeti" hükümsüz bir
rapor penceresinin uzunluk sorusudur ve zaten WP5-A'da bekleyen R2 kaleminin gövdesidir — ikinci
bir kart açmak çift-kayıt olur.

### B3 · Ö-37 — "`seed_boundary` iki yolu farklı şey ölçüyor — hangisi otorite?" (ROADMAP:1999-2013)

**Ne istiyor (tam metinden):** YOL-1 (reset işareti → 2026-07-20, donmuş) ile YOL-2 (`trades.kaynak`
damgası → 2026-07-24) ayrışıyor; dayatılan sıra (donmuşluk > tazelik) YOL-1'i seçiyor ve sınır
gerçek tohum penceresinden 4 gün geride. BUGÜN ETKİSİZ (887/887 damgalı → classify kural-0'da
durur). Gerekli iş: iki tanımdan hangisinin `classify` sözleşmesine uyduğunu ölçmek.

**Bugünkü kodla çarpışma:** v264 tekilleştirmesi yapılmış — sınır TEK hesapta
(`ledgerstamp.seed_boundary`, `api.py:2487` ona gider); sıra HÂLÂ YOL-1 > YOL-2 ve ayrışma
makine-okunur beyanlı (`yollar_ayrisik` + `neden`, `ledgerstamp.py:306-345`). Karar verilmemiş;
davranış-nötrlük bugün de geçerli görünüyor (sınır yalnız DAMGASIZ satırı etkiler; damgasız satır
son ölçümde 0 — canlı yeniden-sayım bu turda yapılamadı, beyan yukarıda).

**ÖNERİ: KAPAT-TASARIMDA (tek-paragraf taslak).** Ölçüm gerektirmiyor — soru tanımsal ve iki değer
zaten yan yana hesaplanıyor. Taslak: *Sınırın sözleşmedeki anlamı "tohum defteri nerede biter"dir;
bunun doğrudan ölçümü YOL-2'dir (`replay_seed` damgalı satırların en geç `ts_close`u) ve donmuşluk
şartını da sağlar — eğriye nokta eklemek işlem damgasını kaydırmaz, YOL-1'in korkusu YOL-2'de
yapısal olarak yoktur. Öneri: `seed_boundary` sırası YOL-2 > YOL-1'e çevrilir; YOL-1 çapraz-sağlama
olarak kalır, `yollar_ayrisik` bayrağı ve beyan aynen korunur; değişiklik davranış-nötrlüğü
(damgasız satır sayısı 0) tek satırlık ölçümle kayda geçirilerek sevk edilir. Damgasız satır >0
çıkarsa bu KAPAT geri açılır ve kalem ÖLÇ sınıfına döner (sınır o satırların sınıfını değiştirir).*

---

## TABLO + SAYIM

| # | Kalem | Bugünkü gerçek (ölçülmüş çekirdek) | Öneri | K |
|---|-------|-------------------------------------|-------|---|
| A1 | Türetilmiş artefakt yeniden üretimi | Gecelik otomatik + kablolu; canlı 2026-08-21 taze, damgalı | **KAPAT-BAYAT** | — |
| A2 | Seans-içi boşluk dedektörü | Sevk 08-01/02; canlıda 3.321 olay/15 gün; sembol=yapısal gürültü, akış=0 | **KAPAT-BAYAT** | — |
| A3 | Earnings kapsama + fail-open | 216/251 (%86,1; eski 194 bayat); 35 fail-open; bedel hiç sayılmadı | **ÖLÇ** (retro bedel sayımı) | 1 |
| A4 | MNST split (kart-önce) | Teşhis tam; kart YOK, kod YOK; canlı semptom sustu, körlük duruyor | **ÖLÇ** (A1 oran-imza kartı) | 1 |
| A4 · 2026-08-24 KAPANIŞ | (aynı kalem) | ÖLÇÜLDÜ: EDG-2026-056 koştu — YP %41,8 / yakalama %34,8 | **KAPANDI: imza tek başına yetersiz** | 1 (harcandı) |
| B1 | Ö-45 chop tanımı | EDG-048 NO-GO (aynı gün): @chop dilimi kapandı, tüketici yok | **KAPAT-BAYAT** | — |
| B2 | Ö-47 artık-fold + 91g holdout | n_dengeli canlıda 23/26; FOLD_MIN_N=15; holdout hükümsüz-by-design | **KAPAT-BAYAT** (+holdout kuyruğu → WP5-A 2D, BİRLEŞTİR) | — |
| B3 | Ö-37 seed_boundary otoritesi | Tek hesap (v264), ayrışma beyanlı, bugün davranış-nötr | **KAPAT-TASARIMDA** | — |

**SAYIM:** 7 kalem → **KAPAT-BAYAT 4** (A1, A2, B1, B2) · **KAPAT-TASARIMDA 1** (B3) ·
**ÖLÇ 2** (A3, A4; toplam K-tahmini 2 hükümlü hücre) · **BİRLEŞTİR-BEKLE 0** (yalnız B2'nin
holdout kuyruğu WP5-A 2D'ye devir notuyla).
