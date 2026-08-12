# TEŞHİS — §2-8 MNST BÖLÜNME (SPLIT) SINIFI (2026-08-12, SALT-TEŞHİS)

**Kapsam:** ROADMAP §2-8 — canlıda kayıtlı iki semptomun kök teşhisi: (1) `DATA_QUALITY` "BAR
KAYNAK UYUŞMAZLIĞI: MNST 2026-08-10 — nasdaq 91.43 vs massive 45.715 (%50.0)"; (2)
`MECHANISM_STALE` MAKULLÜK `ledger_matches_bars`: "T00020/MNST defter 59.44 ≠ bar 29.7,
T00095/MNST defter 100.07 ≠ bar 50.01". Bu tur KOD DEĞİŞTİRMEZ; her iddia dosya:satır ya da
veri kanıtlıdır; kanıtlanamayan yere DOĞRULANAMADI + neden yazılıdır.

**Ölçüm tabanı beyanı:** Yerel `state/` CANLI DEĞİL, donmuş fotoğraftır: `state/bars/mnst.csv`
son bar **2026-07-28** (dosya mtime 2026-07-30 02:52); `state/events.jsonl` penceresi
**2026-07-14T09:36 → 2026-08-09T15:01** (ilk/son satır ts). İki semptom olayı 2026-08-10
sonrasına ait olduğundan YEREL olay defterinde YOKTUR — görev tanımından "canlıdan kayıtlı"
veri olarak alındı. Canlıya/SSH'a dokunulmadı. Tek dış kaynak: Massive `/stocks/v1/splits`
takvimi (MCP, salt-okunur piyasa verisi) — bölünme tarih/oran doğrulaması ve evren taraması için.

---

## 0. HÜKÜM ÖZETİ

**MNST 2026-08-11'de 1→2 bölünme yaptı** (dış kanıt: Massive `/stocks/v1/splits` → MNST,
`execution_date=2026-08-11`, `split_from=1.0, split_to=2.0`, `adjustment_type=stock_dividend`,
`historical_adjustment_factor=0.5`; aynı takvimde 2023-03-28 1→2 ve 2016-11-10 1→3 geçmiş
bölünmeleri de kayıtlı). İki semptom aynı kökün iki yüzüdür:

| Katman | Taban (2026-08-11 sonrası) | Kanıt |
|---|---|---|
| massive (grouped/custom) | GÜNCEL bölünme-düzeltmeli (÷2) | `adjusted=true` sabit — `adapters/massive.py:371,396`; 45.715×2=91.43 birebir |
| fmp | GÜNCEL (÷2) | "YALNIZ split-adjusted" — `adapters/data.py:882-886` |
| cboe (MNST geçmişinin sabitlenmiş sahibi) | GÜNCEL (÷2) | "split-adjusted" — `data.py:2,1906`; sahiplik: `state/bars_source.json` MNST=cboe (2026-07-21) |
| nasdaq | Alarm anında ESKİ (bölünme-öncesi) satır verdi | alarm metnindeki 91.43; genel düzeltme semantiği repoda beyansız → **DOĞRULANAMADI** (aşağıda §2) |
| canlı bar zinciri (state/bars) | YENİ tabana çekilmiş (÷2) | semptom-2 bar değerleri: 29.7=59.41/2, 50.01=100.02/2 (§3) |
| trades.jsonl defteri | İŞLEM GÜNÜ tabanı (as-traded), DONUK | entry = o günün open'ı × 1.0005 (§3) — tasarım gereği retro değişmez |

- Semptom-1'in kökü: kaynak-kıyas **kör yüzde** hesaplıyor — taban farkını bölünme olarak
  TANIMIYOR (`data.py:953-955`); tam 2:1 taban farkı "%50.0 sapma" diye raporlanıyor.
- Semptom-2'nin kökü: defter-bar kıyası **bölünme katsayısı kavramı bilmiyor**
  (`recompute.py:185-188`) ve defter satırı meşru olarak değişmez — kırmızı, arızanın değil,
  iki meşru kuralın (kaynaklar güncel-baza yeniden yazar × defter retro değişmez) kesişiminin
  göstergesi. Birebir emsali 2026-07-23'te teşhis edilmiş: T00005/GE spin-off vakası
  (`recompute.py:157-163,190-205`).

---

## 1. SORU 1 — Split-ayar mekanizması nerede; MNST barları hangi tabana çekilmiş

### 1a. Mekanizma: corporate-action savunması (`load_bars` içinde)
- Görev metnindeki işaretçi düzeltmesi: **EDG-016 bölünme notu `adapters/data.py`'de değil** —
  EDG-016 turnover hükmüdür; onun "bölünme → güncel baz" çevrimi `adapters/edgar_shares.py:29-32`
  (kural 4: `shares(t) = val(f_t) × B_son / B(f_t)`, bölünme takvimi EDGAR'ın kendi geriye-dönük
  yeniden beyanından, `_split_olaylari`). Bar katmanındaki split→güncel-baz mekanizması ise:
- **`data.py:2252-2284`** — kaynak tam geçmişi güncel-baza yeniden ayarlamışsa
  (`_corporate_action` True) önbellek atılır (`cached=None`, dosya SİLİNMEZ — atomik değişim),
  `corporate_action_cache_reset` olayı yazılır ve **`_bump_wf_rev()`** ile önbelleklenmiş
  walk-forward'lar geçersiz kılınır (canlı emsal satırda: v4 incumbent 0.2043→0.1130→0.0988
  sürüklenmesi, `data.py:2277-2281`).
- **`_corporate_action` (`data.py:2383-2410`)**: örtüşen tarihlerin kapanış ORANI
  `1±CORP_ACTION_PCT` (%25, `data.py:24`) dışına çıkarsa True; örtüşme yoksa sınır-bar oranına
  çifte eşik (±%50, `2394-2403`). Meşru büyük hareket iki seride de aynı olduğundan tetiklemez.
- Yardımcı katmanlar: artımlı tek-bar şüphesi tam çekime YÜKSELTİLİR (`2234-2251`);
  `keep="last"` ile taze bar bayat barı ezer (`2324-2328`); reset sonrası sahiplik resetleyen
  kaynağa geçer (`2377-2378`). Tek-satırlık düzeltilmemiş hayalet ayrı mekanizmadır
  (`_unadjusted_mask`, `335-391` — yalnız sıçra-VE-geri-dön imzası; kalıcı taban adımını
  BİLEREK damgalamaz, `365-369`). Kalıcı tarihsel kırıklar ölçüm-dışlama defterindedir
  (`bars_integrity`, `394-417` + `integrity_breaks` K1/K2/K3 `449-522`) ve canlı karar yoluna
  BİLEREK bağlı değildir (`405-409`).

### 1b. MNST barlarının tabanı
- **Yerel fotoğraf (2026-07-28'de donuk): ESKİ tabanda.** `state/bars/mnst.csv` 5.679 satır,
  2004-01-02→2026-07-28; son kapanışlar 93-100 bandı (2026-07-28 close 97.74; 2026-07-17 open
  100.02). 2026 penceresinde süreklilik kırığı YOK (260 defterin 2026-05-01+ taramasında MNST
  çıkmadı, §5) — fotoğraf bölünmeden ÖNCE donduğu için kırığı hiç görmedi.
- **Canlı zincir: YENİ tabanda (÷2).** Semptom-2'nin bar değerleri, yereldeki eski-taban
  open'larının tam yarısı: 2023-05-08 open 59.41 → canlı 29.7 (59.41/2=29.705, panelde 2 haneye
  yuvarlanır `recompute.py:188`); 2026-07-17 open 100.02 → canlı 50.01 (birebir /2). Yani canlı
  önbellek bölünme sonrası güncel-baza yeniden yazılmış (cboe/fmp/massive'in tek verebildiği
  taban budur). Canlı csv'nin seri-İÇİ kırıksız olup olmadığı yerelden okunamaz →
  **DOĞRULANAMADI** (tam reset yaşandıysa kırıksızdır; kırık defter-bar ARASINDADIR).
- MNST'nin defterdeki tek tarihsel kırık kaydı ESKİ ve bağımsız bir vakadır:
  `state/bars_integrity.json` → MNST 2006-01-03 oran 0.2633 (K1 ölçek dikişi),
  `guvenli_baslangic=2006-01-04`, 505 bar ölçüm-dışı (2026-08-01 canlı olayı
  `bars_integrity_period_excluded` yerel events'te de görünüyor).

---

## 2. SORU 2 — Hangi kaynak hangi tabanda; DATA_QUALITY kıyası bölünmeyi tanıyor mu

### 2a. Kaynak tabanları
- **massive:** `adjusted=true` sabit parametre (grouped `massive.py:359-371`, custom-bars
  `384-396`; URL yorumunda `?adjusted=true` `massive.py:16`) → her sorguda sorgu-anının
  güncel bölünme-düzeltmeli tabanı. 2026-08-11+ çekilen snapshot'ta 2026-08-10 barı 45.715
  (=91.43/2).
- **nasdaq:** `_fetch_nasdaq` (`data.py:868-878`) ham `tradesTable` satırlarını çevirir;
  modülde nasdaq için HİÇBİR düzeltme beyanı yok (Cboe/FMP için açıkça "split-adjusted" yazar,
  nasdaq için yazmaz — `data.py:2,1906`). Canlı olay, alarm anında nasdaq çerçevesinin
  2026-08-10 için 91.43 (eski taban) taşıdığını KANITLAR; "hiç düzeltmez mi, gecikmeli mi
  düzeltir" genellemesi → **DOĞRULANAMADI**.
- **Zamanlama çıkarımı:** Massive split dokümantasyonuna göre düzeltme execution-date'te
  uygulanır; 2026-08-10, bölünme-öncesi fiyat gösteren SON seanstır. 08-10 akşamı massive de
  91.43 derdi; 45.715 ancak 08-11+ çekimli snapshot'ta mümkün. Dolayısıyla alarm **2026-08-11
  veya sonrası bir tazelemede** ateşlendi ve o an nasdaq çerçevesinin son satırı hâlâ eski-taban
  08-10 barıydı (olay satırı yerel pencere dışında → ateşlenme anı DOĞRULANAMADI).
- MNST'de zincirin nasdaq'a düşmesi bilinen bir örüntü: yerel events 2026-07-21/22'de MNST
  için `bar_source_seam_opened/blocked` (pinned=cboe, offered=nasdaq) altı kez kayıtlı.

### 2b. Kıyas KÖRDÜR — bölünme tanıma yok
- `_massive_crosscheck` (`data.py:932-978`): `dev = abs(mc - pc) / pc` (`:953`),
  eşik `MASSIVE_TOL=0.005` (`:58`), aşılırsa `obs.alarm(ALARM_DATA_QUALITY, "BAR KAYNAK
  UYUŞMAZLIĞI: ... (%{dev} > tol %{tol})", kind="bar_kaynak_uyusmazligi")` (`:963-976`).
  Oran sınıflaması, 2:1/3:1 imza testi, bölünme-takvimi danışması YOK. 2:1 taban farkı
  dev=0.5000 üretir → alarm metnindeki "%50.0" tam bunun imzasıdır ama kod imzayı tanımaz.
- Birikim de kör: `_record_xcheck` (`:981-995`) yalnız `n/mismatch/max_dev` sayar.
- Eşik yorumunun kendisi de (`data.py:51-58`) gürültü tabanı ↔ gerçek arıza ekseninde yazılmış;
  "taban farkı" diye üçüncü bir sınıf hiç modellenmemiş.

### 2c. Aynı körlüğün ikinci bedeli: corp-action FLAP (ölçülmüş)
Kaynaklar farklı tabanda ISRAR ederse savunma her el değiştirmede tam geçmişi öbür tabana çevirir
ve her seferinde wf_rev bump'lar. Yerel events penceresinde (07-14→08-09, ~26 gün)
`corporate_action_cache_reset` sayıları: **GE 34 · DD 28 · FDX 5 · BDX 4 · SPY 2 · GILD 2 ·
BX 1**. Sıra kanıtı: corp-action kontrolü, D1 kaynak-dikişi kırpmasından ÖNCE koşar
(`data.py:2260` vs `:2306`) — yani sahip-olmayan kaynağın TAM eski-taban cevabı, dikiş kuralı
onu "yalnız yeni tarih" diye kırpamadan reseti tetikleyebilir. **MNST, nasdaq eski tabanda
kaldığı sürece bu kulübe adaydır** (canlı sürüyor mu → pencere dışı, DOĞRULANAMADI).

---

## 3. SORU 3 — Defter tabanı; `ledger_matches_bars` beklentisi; retro-değişmezlik

### 3a. Defter entry'leri işlem-günü tabanında ve bar-open kimliğiyle birebir
`state/trades.jsonl` (MNST'nin tamamı bu iki satır):
- **T00020**: ts_open=2023-05-08, entry=59.4399, qty=99. Yerel bar 2023-05-08 open=59.41;
  59.41 × 1.0005 = 59.4397 ≈ entry (goal.yaml: `fill: next_bar_open`, `slippage_bps: 5`).
  Not: 2023-03-28'deki önceki 2:1'den SONRA açılmış — bugünkü bazla arasında yalnız 2026-08-11
  faktörü (÷2) var; gözlenen 59.44/29.7 = 2.0013 bununla tutarlı.
- **T00095**: ts_open=2026-07-17, entry=100.0701, qty=28. Yerel bar open=100.02;
  100.02 × 1.0005 = 100.0700 ✓.
Yani defter, işlem anının as-traded fiyatını taşıyor; canlı barlar ÷2 tabana geçince sapma tam
2:1 çıkıyor — semptom-2'deki 29.7 ve 50.01 değerleri yereldeki eski-taban open'larının yarısıdır.

### 3b. Kontrolün beklentisi ve alarm zinciri
- `recompute.py:157-208`: A yolu = `trades.jsonl entry`; B yolu = `adapters.data.load_bars`
  o günün open'ı, YALNIZ önbellekten (`:177-179`); kırmızı eşiği `|open-entry|/open > 0.005`
  (`:185-186`). **Bölünme katsayısı kavramı yok**; tek istisna elle yazılmış bilinen-hayalet
  T00005/GE (`:196`).
- Zincir: `recompute.report()` → watchdog bütünlük satırı `yeniden_hesap:ledger_matches_bars`
  (`watchdog.py:1066-1069`) → parity jetonu → `obs.alarm("MECHANISM_STALE", "MAKULLÜK: {check}
  — {detail}")` (`watchdog.py:1791-1795`). Semptom metni bu biçimle birebir.

### 3c. Retro-değişmezlikle çelişki: VAR, ama kontrol tarafında
Kontrolün örtük beklentisi "o günün bar açılışı sonsuza dek entry ile aynı kalır". Bu beklenti
iki MEŞRU kuralla aynı anda yaşayamaz:
1. Kaynaklar (fmp/cboe/massive) tarihsel seriyi bölünmede güncel-baza yeniden yazar ve sistemin
   KENDİ savunması bunu içselleştirir (`data.py:2252-2259`, `keep="last"` `:2324-2326`).
2. Defter satırı retro değiştirilmez: "retro damga yasağı" (`ledgers.py:131-133` — damgasız/eski
   satır doldurulmaz), bayt-değişmezlik beklentisi (`ledgers.py:327`), ve GE vakasındaki
   operatör kararı emsali (`recompute.py:190-205`: satır DEĞİŞMEZ, kırmızı teşhisiyle konuşur,
   düzeltme re-seed'e ertelenir).
Çelişkiyi çözen taraf ancak KIYAS olabilir (katsayı bilgisi kıyasa girer); defteri veya barları
diğerine boyamak iki yasadan birini kırar.

---

## 4. SORU 4 — DÜZELTME YÖNÜ ÖNERİSİ (uygulanmadı)

**Önerilen yön: (A) taban-farkı TANIMA + (B) ölçülmüş bölünme-katsayı defteri. Defter
retro-ayarı (C) REDDEDİLİR.**

- **A1 — kaynak-kıyasta oran tanıma (`_massive_crosscheck`):** `dev > MASSIVE_TOL` iken
  `m = mc/pc` hesapla; `m` ya da `1/m`, küçük tamsayı oran kümesine (2, 3, 4, 5, 10, 3/2, 10'a
  kadar q/p) ~%1 tolerans içinde oturuyorsa alarmın `kind`ı ayrışsın (örn.
  `bar_kaynak_taban_farki`, oran alanıyla) ve corp-action tam-çekim yoluna işaret etsin.
  Davranış (karantina yok) değişmez; değişen, alarmın teşhis taşımasıdır — bugünkü "%50.0"
  operatöre "hangi taraf bozuk?" sorusunu bırakıyor, oysa 2.0000 imzası cevabın kendisi.
  Oran kümesi/tolerans eşikleri ölçümle seçilmeli (ön-kayıt kartı disiplini, CLAUDE.md md.3;
  yöntem emsali: `_unadjusted_mask`ın 2026-07-31 ölçülerek yeniden tasarımı, `data.py:338-369`).
- **A2 — bölünme-katsayı defteri + `ledger_matches_bars` düzeltmesi:** Katsayının kaynağı
  UYDURMA değil ÖLÇÜM olmalı ve zaten elimizde: `_corporate_action` reset anında örtüşen-tarih
  oranını HESAPLAYIP ATIYOR (`data.py:2404-2408` — bool döner, oran kaybolur). Reset olayına
  `{ticker, tarih, medyan_oran}` yazılır ve kalıcı bir `state/` defterine düşerse (YASA 6:
  okuyucusu bu kontrol olur), `ledger_matches_bars` B yolu "bar_open × kümülatif katsayı
  (ts_open→bugün)" ile kurulur; defter satırına DOKUNULMAZ. Repo-içi ikinci emsal:
  `edgar_shares.py:29-32` aynı sınıf problemi (dosyalama-anı hisse ↔ güncel-baz hacim) tam bu
  yöntemle, kayıtlı bölünme olaylarıyla çözüyor. İstenirse Massive `/stocks/v1/splits` ile
  çapraz doğrulama eklenebilir — ama bu YENİ ağ bağımlılığıdır (açık-ağ kalemi disiplini;
  earnings.refresh→NASDAQ emsali) ve zorunlu değildir: oran, reset anında yerel olarak ölçülür.
  Oran-tabanlı olmayan corp-action'lar (spin-off: GE, HON, DD-2025-11) basit-oran imzası
  vermez — onlar için mevcut bilinen-hayalet/`bars_integrity` yolu aynen kalır.
- **C — defter retro-ayarı NEDEN RED:** (i) retro damga yasağı (`ledgers.py:131-133`);
  (ii) UYDURMA YASAĞI (CLAUDE.md md.4): entry'yi 29.72'ye, qty'yi 198'e çevirmek hiç
  yaşanmamış bir işlem imal eder; (iii) GE emsalindeki operatör kararı (`recompute.py:194-195`:
  doğru düzeltme çıkarmak/re-seed, satır boyamak değil); (iv) bayt-değişmezlik
  (`ledgers.py:327`); (v) K/ölçüm: defter geçmişi değişirse replay/karne/analitiğin tüm
  türevleri sessizce başka dünyaya kayar — `recompute.py:157-163`ün tarif ettiği sınıfın ta
  kendisi.
- **K/ölçüm etkisi (A yolu):** Bar verisine DOKUNULMAZ → K grid, kill-list, donmuş suite
  etkilenmez; wf_rev bump mekanizması aynen kalır. Yan kazanç: A1 corp-action'a taban kimliği
  kazandırırsa GE/DD sınıfı flap (34+28 reset/26 gün) ve onun ürettiği gereksiz wf_rev
  bump'ları/kapı-kıyas kaymaları azalır. Yeni eşikler (oran kümesi, tolerans) ölçüm koduna
  girmeden önce `research/cards/` ön-kayıt ister.
- **İzleme kalemi (bu turun kapsamı dışında, kayıt için):** bölünme, EDG-016 turnover
  paydasını da geçici büker — hacim ex-date'te ÷2→×2 güncel-baza geçer, EDGAR hisse yeniden
  beyanı ise medyan 7g (dei) / ~36g (us-gaap) gecikir (`edgar_shares.py:23-32`); aradaki
  pencerede MNST turnover'ı ~2× şişebilir. Fiziksel bekçi (devir>1) yalnız imkânsız hâli keser
  (`edgar_shares.py:38-45`).

---

## 5. BAŞKA SEMBOL TARAMASI

- **Yerel seri-içi kırık taraması** (260 defter × 2026-05-01 sonrası, |günlük oran−1|>0.35):
  TEK vaka **HON 2026-06-26→29** (464.42→227.80, oran 0.4905) — bu bölünme DEĞİL, ayrışma/spin
  adımı (split takviminde yok; `bars_integrity.json` K1 kaydı: safe_start 2026-06-30, 5.657 bar
  ölçüm-dışı; `data.py:400` sınıflaması "düzeltilmemiş spinoff adımları"). Split-only kaynaklar
  spin adımını yeniden-tabanlamaz; adım seride kalıcıdır ve defter-bar kırmızısı ÜRETMEZ
  (defter de bar da aynı tabanda kalır).
- **Dış bölünme takvimi ∩ evren** (Massive `/stocks/v1/splits`, 2026-06-01→2026-09-15,
  toplam 415 olay; evren = state/bars'taki 260 sembol): **KLAC 2026-06-12 (1→10) · DD
  2026-06-24 (3→1 reverse) · MNST 2026-08-11 (1→2)**. Başka evren bölünmesi yok; 2026-09-15'e
  kadar planlı başka vaka da görünmüyor.
- **KLAC/DD neden semptomsuz:** İkisinin yerel defteri kırıksız — yeniden-tabanlama tam emilmiş
  (KLAC 06-11 close 241.164 → 06-12 254.54 sürekli; kesirli kapanışlar ÷10'un izi. DD 06-23
  140.01 → 06-24 137.82 sürekli). Ve `trades.jsonl`'da KLAC/DD işlemi HİÇ YOK →
  `ledger_matches_bars` kırmızısı üretecek defter satırı yok. Haziran alarm/reset olayları
  yerel pencere (07-14 başlangıç) dışında → **DOĞRULANAMADI**. **MNST'yi farklı kılan:**
  denetimler canlıyken bölünme-öncesi DEFTER GİRİŞİ olan ilk evren bölünmesi (spin-off
  soyundan T00005/GE emsali hariç).
- **Kaynak-kıyas birikimi** (`state/massive_crosscheck.json`, 2026-07-30 fotoğrafı): MNST
  n=7, mismatch=0, max_dev=0.0; tüm evren en kötüsü 9e-05 (MRNA) — 07-30 itibarıyla başka
  taban ayrışması yoktu.
- **Süren flap riski:** GE 34 · DD 28 reset (07-14→08-09) — bu ikisi bölünme değil
  kaynak-taban savaşı; A1 tanıma bunu da teşhisli hâle getirir. Canlıda bugünkü durumu →
  pencere dışı, DOĞRULANAMADI.

---

## 6. DOSYA HARİTASI (hızlı erişim)

`meridian/adapters/data.py` — 24 CORP_ACTION_PCT · 58 MASSIVE_TOL · 868-878 nasdaq (beyansız) ·
882-886 fmp split-adj · 932-978 kör kaynak-kıyas + alarm · 1903-1942 zincir sırası ·
2234-2251 artımlı yükseltme · 2252-2284 corp-action reset + wf_rev · 2306-2321 D1 dikiş
(corp-action'dan SONRA) · 2383-2410 `_corporate_action` (oranı hesaplar, ATAR) ·
`meridian/adapters/massive.py` — 371,396 adjusted=true · 572-590 latest_bar/bar_for ·
`meridian/recompute.py` — 157-208 ledger_matches_bars (185-186 eşik; 190-205 GE emsali) ·
`meridian/watchdog.py` — 1066-1069 yeniden_hesap satırları · 1791-1795 MECHANISM_STALE MAKULLÜK ·
`meridian/ledgers.py` — 131-133 retro damga yasağı · 327 bayt-değişmezlik ·
`meridian/adapters/edgar_shares.py` — 29-32 bölünme→güncel-baz çevrim emsali ·
`state/`: bars/mnst.csv (donuk, eski taban) · bars_integrity.json (K1 kayıtları) ·
massive_crosscheck.json · bar_source_seams.json · trades.jsonl (T00020/T00095).
