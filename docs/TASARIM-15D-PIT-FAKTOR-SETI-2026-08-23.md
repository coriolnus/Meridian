# TASARIM — WP11/15d: PIT-TEMİZ FAKTÖR SETİ (OPT Faz-2'nin ilk müşterisi)

*2026-08-23 · tasarım ajanı çıktısı — kod yok, kart yok, ölçüm yok; yalnız tasarım + öneri.
Ön-kayıt ve hüküm Rol-1'de. Dayanak: CLAUDE.md §4 (PIT'siz fundamentals proxy YASAK) ·
ROADMAP.md:1444-1448 (15d tanımı) · ROADMAP.md:649-652 (OPT Faz-2 "yeni ilk müşteri").*

## 0. Çerçeve — 15d'nin sözleşmesi

15d'nin ROADMAP'teki tanımı (ROADMAP.md:1444-1447): elle bileşik-ağırlık YOK (031 dersi); yeni
faktörler indicators'a **w=0 ile kablolanır**, hermes arama uzayına bırakılır, benimseme
OOS-kapılı. Entegrasyon deseni depoda üç kez kanıtlanmış (Batch L → G2 → EDG-016): bounds.yaml'a
default-0 satır iner (ör. `entry.w_turnover`, state/bounds.yaml:49), `state/strategy.yaml`
taşımadığı için canlı etki sıfırdır, bileşik skor bire bir eskisidir (strategy.py:445-501).
OPT Faz-2 ("kâğıt-OOS kapılı arama") bugün **28d'ye bağımlı** — kapı ölçemiyor (chop 27<30,
ROADMAP.md:333); 15d bu boru hattına *yakıt* hazırlar, benimseme takvimini hızlandırmaz.
Bu belge yeni ölçüm başlatmaz; K harcamaz.

## 1. Mevcut durum ölçümü

### 1.1 Bugün skor/seçilimde ne var (PIT sınıflamasıyla)

Ayarlanabilir bileşik skor yalnız `evaluate_entry` (breakout_vcp) yolundadır
(strategy.py:433-502); pullback yolu sabit-ağırlıklıdır (0.40/0.35/0.25, strategy.py:569).

| bileşen | canlı ağırlık | kaynak | tür |
|---|---|---|---|
| rs (63g kesitsel RS yüzdelik) | 0.35 (varsayılan, strategy.py:439) | indicators.py:303 | fiyat-türevi, PIT-doğal |
| tight (sıkılık) | 0.30 (strategy.py:439) | bar serisi | fiyat-türevi |
| vol (vr/3 hacim oranı) | 0.20 (strategy.py:440,438) | bar serisi | fiyat-türevi |
| prox (pivot yakınlığı) | 0.15 (state/strategy.yaml `entry.w_prox`) | bar serisi | fiyat-türevi |
| rvol bandı — UYKUDA | 0 (strategy.py:461) | bar serisi | fiyat-türevi |
| mom 12-1 rütbe — UYKUDA | 0 (strategy.py:462) | bar serisi | fiyat-türevi |
| turnover21 — UYKUDA | 0 (strategy.py:498; bounds.yaml:49) | **EDGAR filed as-of hisse** (indicators.py:189; strategy.py:132-133) | **fundamentals-türevi, PIT-TEMİZ** |

Kapılar (state/strategy.yaml): `rs_rating_min` 70 · `min_volume_ratio` 1.5 · `min_score` 60 —
hepsi fiyat-türevi. Kazanç karartması (earnings.py:32, BLACKOUT_DAYS=5) ileriye dönük canlı
takvimden çalışır; karar-yolu PIT riski taşımaz (PIT birikimi earnings_snapshots.jsonl'a ayrıca
yazılır). **Özet: karar veren yüzey bugün %100 fiyat-türevi; tek fundamentals kablosu (turnover)
PIT-temiz ama w=0 uykuda.** Ölçüm yolu hazır: component_ic.py 8 bileşeni (turnover21 dahil)
3 ufukta sıfır-yetkiyle raporluyor (component_ic.py:1-11).

### 1.2 EDGAR PIT altyapısı — ne kurulu

- **`research/edgar_facts/` (çekim 2026-08-01, DONUK):** shares 161.856 satır/258 sembol;
  fundamentals 142.499 satır/7 etiket (Revenues, RevenueFromContract±Tax, CostOfRevenue,
  CostOfGoodsAndServicesSold, GrossProfit, Assets — README §2). PIT tek kural: `filed <= t`
  (README §1; GOOGL split kanıtı). İlk-ifşa gecikmesi: kapak hisse **7 gün**, bilanço/gelir
  **33-37 gün**. Kapsam (evren 251): anlık hisse 246 · gelir 248 · Assets 250 · GP 184 (README §3).
- **`earnings_8k_tarihleri.csv`:** 17.535 satır · 258 sembol · 2010→2026-07; `filed==report_date`
  %90,8, ≤1 gün %96,3; **BMO/AMC türetilemez (hüküm — README "acceptance saat dilimi ÇÖZÜLEMEDİ")**;
  CIK-halefiyet kesiği (BLK ilk 2.02 = 2024-10-11 — "veri yok" ≠ "duyuru yok").
- **`research/pit_universe/sp500_uyelik_tarihi.csv` (fja05680, MIT):** 2.718 gün-satırı,
  1996-01-02 → 2026-06-30, günlük üye 487-507 (EDG-018 status bloğu). Salt-S&P500, boyut alanı yok.
- **Canlı kablo:** adapters/edgar_shares.py (as-of okuma + bekçiler) → indicators.turnover21
  (fiziksel devir>1 ve bayatlık bekçileri, indicators.py:189-215) → strateji (statik depo-içi
  dosyadan, saflık bozulmadan — strategy.py:119-133,482).

### 1.3 Kart hükümleri (dördü + robustluk kartı)

| kart | hüküm | 15d'ye dersi |
|---|---|---|
| EDG-2026-012 net-issuance | ARŞİV, kill#2: yön literatürün TERSİ ve anlamlı (@60 +1,04% CI[+0,33,+1,67]); beşli dilim U-eğrisi | bu evren sağ-kalan büyük-cap; kill-list gereği aynı evrende yeniden ölçüm YOK |
| EDG-2026-013 mom×turnover | ARŞİV: etkileşim tezi düştü, bulgu 016'ya devredildi | koşullama sinyali yarıya indirdi — ana-etki önce ölçülür |
| EDG-2026-014 gross profitability | ARŞİV, kill#1: bilgisiz (tüm CI-0-içi; 23.272 sembol-ay) | kârlılık-SEVİYESİ bu evrende fiyatlanmış; PIT yasası ilk kez meşru aşıldı |
| EDG-2026-016 turnover ana etkisi | **SUCCESS**: @20 +0,65% CI[+0,34,+1,01]; artık üç yöntemle sağ; maliyet-sonrası +0,55%; w=0 kablolandı | entegrasyon deseninin kendisi; çekince: survivorship yukarı-çarpıtır, büyüklüğü ölçülemez |
| EDG-2026-018 PIT midcap | askıya:veri-kapısı — kohort kurulamadı; endeksten çıkan 350 ismin 338'i (%96,57) arşivde SIFIR bar | delist-bar kilidi açılana dek her pozitif hüküm "ÜST-SINIR" şerhi taşır |

**Kurulu:** PIT veri katmanı + as-of disiplini + ölçüm şablonu (wp2_olcum) + w=0 entegrasyon
deseni + bileşen-IC raporu. **Eksik:** turnover dışında hiçbir fundamentals kablosu; arşiv tek-çekim
donuk (tazeleme kadansı karara bağlanmamış); tarihsel duyuru-saat bilgisi yok; delist-bar yok.

## 2. Aday seti (EDGAR'dan PIT-temiz türetilebilir)

Ortak zemin her adayda: as-of okuma `filed <= t` (end-tabanlı okuma YASAK); karşılaştırmalı-tekrar
tuzağına karşı İLK-İFŞA = `groupby(symbol,tag,start,end).filed.min()` (README §1); `val<=0` +
birim filtresi (README §5.3); survivorship üst-sınır şerhi zorunlu (EDG-018).

**A1 · 8-K duyuru-tepki sürüklenmesi (PEAD).** Tanım: t0 = 8-K Item-2.02 `filed` günü; tepki =
[t0−1, t0+1] getirisi − aynı-pencere evren ortalaması (BMO/AMC bilinmediği için ±1 pencere
ZORUNLU); faktör = tepkinin işaret/büyüklüğü → 20/60g sürüklenme. PIT: filed'dan itibaren
(gecikme 0-1 gün). Mekanizma: kazanç haberine eksik-tepki sonraki haftalara sızar. Maliyet:
**mevcut arşiv** + bar önbelleği; sıfır yeni çekim. Riskler: pencere bulanıklığı sinyali sulandırır;
CIK-halefiyet kesiği (41 sembolde ilk 2.02 geç — o sembol-dönemler None+neden); aynı-çeyrek çift
2.02 (14 gün kümeleme gerekli — README "sıklık sapmaları"); 2.02-işaretsiz duyurular kaçar.

**A2 · Temel-momentum: YoY çeyrek gelir büyümesi / ivmesi.** Tanım: ilk-ifşa filtreli çeyrek
`Revenues` YoY değişimi (ve ivme = Δbüyüme); yüzdelik puana oturur (016'nın sabit-kalibrasyon
deseni). PIT: filed as-of, medyan 33-37g gecikme. Mekanizma: temel iyileşmenin yavaş fiyatlanması
(014'ün ölen tezi kârlılık-SEVİYESİ idi; büyüme/değişim ayrı aile). Maliyet: **mevcut arşiv**
(248/251). Riskler: gelir-etiketi ikiliği (öncelik Revenues→contract; AVB/COP vakaları README §5.1);
restatement (ilk-ifşa filtresi bunun panzehiri); mali-yıl hizası (`frame` alanı).

**A3 · Varlık büyümesi.** Tanım: as-of `Assets` YoY değişimi; DÜŞÜK büyüme bilgi taşır (yatırım
faktörü ailesi — yön NEGATİF). PIT: filed as-of. Mekanizma: agresif bilanço büyütme → sonraki düşük
getiri. Maliyet: **mevcut arşiv** (250/251). Riskler: finansallarda varlık büyümesi farklı anlam
taşır (finans-dışı tanı dilimi şart); long-only sistemde negatif-yönlü faktör ancak KAÇINMA /
skor-cezası olarak kullanılır — kablolama deseni turnover'ın tersi, tasarımı karta yazılmalı;
012'nin U-eğrisi dersi (sağ-kalan büyük-cap'te "kötü" dilim tuhaf davranabilir).

**A4 · Dosyalama-gecikmesi işareti.** Tanım: ilk-ifşa `filed − end` gecikmesinin sembolün kendi
tarihçesine göre anormalliği; alışılmadık geç dosyalama = negatif işaret. PIT doğal (faktör zaten
filed'dan). Maliyet: **sıfıra yakın** (ilk_ifsa_gecikme.csv + satırlar). Riskler: büyük-cap
evrende varyans düşük — bilgi içeriği zayıf çıkabilir (ucuz ölür); NT 10-K/NT 10-Q bildirimleri
çekilmedi (kapsam boşluğu). Öneri: bağımsız kart yerine A2 kartına TANI sütunu olarak iliştirilip
K harcamadan keşfedilebilir (eşiksiz rapor — Rol-1 takdirinde).

**A5 · Brüt-marj trendi Δ(GP/Revenues).** 014 SEVİYEYİ öldürdü; trend ayrı tez ama KOMŞU — yeni
kartın 014'ten farkı gerekçelendirilmek zorunda. Kapsam 184/251 + sektör çarpıklığı (banka/REIT
yapısal dışarıda). Maliyet: mevcut arşiv. Ön-olasılık zayıf → sıralamada sona.

**A6 · Form-4 insider net-alımı (Y4; hedef sözleşmesi md.5 zaten "ilk vatandaş" ilan etti —
MERIDIAN_ENGINEERING_LOG.md HEDEF SÖZLEŞMESİ/5).** Tanım: CMP rutin/fırsatçı ayıklamalı net P−S
skoru (adapters/insider.py'de sınıflama hazır). PIT: Form 4 yasal ~2 iş günü içinde dosyalanır.
Maliyet: **yeni veri işi** — bugünkü FMP akışı yalnız artımlı/ileriye-dönük; tarihsel geri-doldurma
FMP 402-blokeli (adapters/insider.py:6-9,49); EDGAR'dan doğrudan Form-4 ingest ücretsiz ama orta boy iş.
Riskler: CMP 3 yıllık pencere ister — defter taze, tarihsel derinlik olmadan kesit ölçümü kurulamaz.

**A7 · Sektör-görece momentum (fiyat-türevi tamamlayıcı; ROADMAP.md:1445 adıyla sayıyor).**
Tanım: mom21/mom252'nin sektör-içi artığı (SECTORS haritası backtest.py:70). PIT: fiyat-doğal.
Maliyet: sıfır yeni veri. Riskler: SECTORS statik bugünün-sınıflamasıdır — sınıflamanın kendisi
PIT değil (beyan şart); fiyat ailesi skorda zaten kalabalık (rs, mom12_1, rvol, turnover) —
akrabalık/artık-katkı ölçümü zorunlu (016'nın çift-sıralama şablonu).

**Aday DEĞİL (kill-list):** net-ihraç (EDG-012) bu evrende "ters ve anlamlı" hükmüyle arşivde;
kill-list dokunulmaz (CLAUDE.md §3). Ancak delist-bar'lı ya da genişletilmiş YENİ evren gelirse
yeni-evren gerekçeli yeni kart meşru olur.

**fja05680 CSV'nin evren-PIT bağı:** her ölçüm gözlem gününde sembolün o gün S&P500 üyesi olup
olmadığı as-of süzülür (EDG-018 guard emsali: "look-ahead yasak"). Bu, look-ahead'in EVREN bacağını
kapatır; BAR bacağını kapatmaz (%96,57 sıfır-bar) — hükümler üst-sınır şerhli kalır. Ayrıca 15c
genişlemesi geldiğinde üyelik-tarihli robustluk kartlarının hazır çapasıdır.

## 3. Sıralama + kart taslak önerileri (ÖNERİ — ön-kayıt Rol-1'in)

Sıralama (ölçüm maliyeti × beklenen bilgi):
**1. A1 PEAD-8K** (veri hazır; sistemin PEAD/EP kurulumlarına — strategy.py:652,811 — doğrudan
besleme; en yüksek bilgi/maliyet) · **2. A2 gelir temel-momentumu** (veri hazır; 014'ten bağımsız
tez) · **3. A3 varlık büyümesi** (veri hazır, tek-eksen ucuz) · sonra A4 (tanı olarak bedava),
A6 (operatör veri-kararına bağlı), A7 (ucuz ama akrabalık riski), A5 (zayıf ön-olasılık).

**K1 taslağı (A1 PEAD):** evren full_251 kapsam-beyanlı (CIK-kesiği sembol-dönemleri None+neden);
gözlem olay-bazlı (8-K başına bir; 14g kümeleme sonrası ~16,8k olay); tepki = [t0−1,t0+1] getirisi
− aynı-pencere evren ortalaması; grid: `tepki_ust_20pct` / `tepki_alt_20pct` → **K+=2**; ufuk
20/60g, taban aynı-gün evren ortalaması, 21g blok-bootstrap CI; pozitif kontrol rvol20 @20 IC
≈0,064 + PK4/PK5 (wp2_olcum şablonu). Kill adayları: (i) iki uç @20+@60 CI-0-içi → bilgisiz,
arşiv; (ii) yön ters-anlamlı → arşiv+not; (iii) geçerli olay < 8.000 → askı (K harcanmaz).
Eşik önerisi: üst-dilim fazlası @60 anlamlı POZİTİF (CI 0-dışı) VE maliyet-sonrası net > 0
(10bps + 20bps duyarlılık). Guards: kümeleme beyanı, survivorship "üst-sınır" kelimesi hükümde
zorunlu, ±1g pencere gerekçesi (BMO/AMC hükmü) kartta.

**K2 taslağı (A2):** aylık gözlem; grid: `yoy_buyume_ust_30pct` / `ivme_ust_30pct` → **K+=2**;
20/60g; kill: CI-0-içi bilgisiz · ters-anlamlı arşiv · sembol-ay < 3.000 askı. Guards: İLK-İFŞA
filtresi zorunlu; etiket önceliği Revenues→contract yazılı; `frame` ile mali-yıl hizası; A4 gecikme
sütunu eşiksiz TANI olarak rapora.

**K3 taslağı (A3):** grid: `varlik_buyume_alt_30pct` (bilgi bacağı) + üst-dilim simetri TANI'sı →
**K+=1** (tek hüküm hücresi; tanı CI'sız). Kill: alt-dilim @60 CI-0-içi → bilgisiz; ters-anlamlı →
arşiv+not; sembol-ay < 2.500 askı. Guards: finans-dışı tanı dilimi; long-only kullanım biçimi
(skor-cezası/kaçınma) hükümden ÖNCE kartta yazılı olmalı — 016'daki "entegrasyon kararı" satırının
negatif-yön muadili.

## 4. Açık sorular (operatör kararı gerektirir)

1. **Delist-bar kaynağı (WP-U):** QuantConnect turu mu, Massive yükseltmesi mi, ücret ne? Tüm
   faktör hükümlerinin "üst-sınır" şerhini kaldıracak tek kalem; EDG-018'in yeniden-açılış şartı.
2. **Insider verisi yolu (A6):** FMP plan yükseltmesi (402'yi açar, ücretli) mi, EDGAR'dan doğrudan
   Form-4 ingest'i (ücretsiz, orta boy iş) mi, yoksa erteleme mi?
3. **15c sırası:** faktör seti önce mevcut 251 evrende mi ölçülsün (öneri: EVET — arşiv 251+8 için
   çekildi; genişleme sonrası üyelik-tarihli robustluk kartı ayrıca), yoksa genişleme mi beklensin?
   C6 çözüldü ve 15c askısı kalktı (ROADMAP.md:259) — genişleme takvimi operatörde.
4. **edgar_facts tazeleme kadansı ve sahibi:** arşiv 2026-08-01 tek-çekim donuk; canlı turnover
   kablosu "aylık tazelenir" beyanıyla statik dosyadan okuyor (strategy.py:482) ama tazeleme hiç
   koşulmadı; "son filed bayat" bekçisi (README §5.6 Citigroup vakası) ile birlikte karara bağlanmalı.
5. **Finans-kurum gelir etiketi mini-çekimi:** GS/SYF `RevenuesNetOfInterestExpense` bu turda
   çekilmedi (README §5.7); A2 kapsamını 248→~250 yapar — küçük ek çekim onayı?
