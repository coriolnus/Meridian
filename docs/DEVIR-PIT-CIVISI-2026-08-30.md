# Devir notu — "PIT'siz fundamentals proxy YASAK" yasasının mekanik çivileri (2026-08-30/31)

> ## ✅ DEVİR TAMAMLANDI — 2026-08-31, Rol-1 (bu belge artık TARİHSEL KAYITTIR)
> Üç dosya main'e entegre edildi (`8ef0a41`; vNNN çakışması gerçekleşti, paket v341/v342'ye
> taşındı — kayıt dosya başlıklarında). Otoriter tam suite üçlü hükümle yeşil (8023 passed ·
> grep boş · PYTEST_EXIT=0 · SHA donuk) ve push atıldı (`origin/main` ucu `1766e1f`).
> CLAUDE.md metni operatör onayıyla uyarlanarak işlendi. §2.3'teki operatör kararı VERİLDİ:
> "(b) PIT arşivine bağla" → ön-kayıt kartı `EDG-2026-062`, uygulama planı
> `docs/superpowers/plans/2026-08-31-edg062-pit-arsiv-baglamasi.md`. §4 madde 7'nin kalemi
> `docs/KALEM-PIT-PARITY-BAGLAMASI-2026-08-31.md` olarak main'de. Aşağıdaki "seni bekleyenler"
> dili bu tarihten itibaren bayattır; belge zincirin gerekçe arşivi olarak yerinde.

**Oturum:** yan oturum (worktree `affectionate-pike-9248a8`). **Rol-1 DEĞİL.**
Hiçbir git komutu koşulmadı (salt-okunur dahil), `state/`e yazılmadı, tam suite koşulmadı,
dağıtım yapılmadı ve önerilmiyor. İş **commit'siz** bırakıldı.

**Altı tur, tek zincir.** Yasak 2026-08-30'a kadar tamamen ricaya dayalıydı (`guard.py`de kapı yok,
`codelaw.py`da denetçi yok, `tests/` altında çivi yok). Birinci tur yasağı mekanikleştirdi; sonraki
beş tur **yasanın kendi kaydını** mekanikleştirdi — her tur, bir öncekinin devir notuna "en zayıf
halka" diye yazdığı elle-kalmış parçayı bir sözleşmeden türetilmiş hâle getirdi (§5).

**Teslim edilen üç dosya (hepsi YENİ; `meridian/` altındaki mevcut hiçbir dosya düzenlenmedi):**
- `meridian/pitlaw.py` — yasanın statik denetçisi
- `tests/test_pit_yasasi_v341.py` — **26 çivi**: yasağın kendisi (tur 1)
- `tests/test_pit_sinif_turetimi_v342.py` — **37 çivi**: kaydın kendisinin denetimi (tur 2–6;
  sınıf türetimi, karar adları, üretici kümesi, iki sözleşmenin iki yönlü tamlığı)

**`rapor()["ok"]` bugün SEKİZ hükmün birleşimi:** tarihsel yolda beyansız ihlal yok · canlı borç
tabanı aşılmadı · beyanlar hâlâ gerçek · sınıf ataması kaynakla uyuşuyor · kapı sözleşmesi kaydı
çürük değil · kayıtsız kapı yüzeyi yok · sinyal sözleşmesi kaydı çürük değil · kayıtsız tarayıcı
yok. Taranamayan dosya da düşürür.

Mevcut hiçbir dosyaya satır eklenmedi; bu **bilinçli**: `codelaw.py`ye satır eklemek onu gösteren
`dosya.py:NNN` çapalarını kaydırır ve `stale_line_anchors` sıfır-tolerans hükmünü ilgisiz bir
sebeple kırardı (CLAUDE.md §2 kapısı).

---

## 0. MAIN OTURUMA (ROL-1) DEVİR — tek bakışta

Bu worktree'de **çalışan kod ve çiviler bitti ve yeşil**; kalan her şey Rol-1 yetkisi ya da
operatör kararı istiyor. Yan oturum git komutu koşmadı, CLAUDE.md'ye dokunmadı, tam suite
koşmadı, dağıtım önermiyor.

| # | Kalem | Ne bekliyor | Nerede |
|---|---|---|---|
| 1 | Üç yeni dosya + bu brief | **commit**; motor kaynağına dokunuldu → push TAM SUITE hükmünden ÖNCE atılmaz | §4 madde 1 |
| 2 | Otoriter tam suite | donmuş ağaçta, tek-otoriter, arka planda | §4 madde 2 |
| 3 | `v337`/`v338` numara çakışması | commit öncesi `main`de doğmuş mu diye bakılmalı | §4 madde 3 |
| 4 | **CLAUDE.md §4 + §2 metni** | **hazır yazıldı, uygulanmadı** — Rol-1 kopyalayıp işler | §4 madde 5 |
| 5 | **Tek gerçek ihlalin düzeltmesi** | **operatör kararı**: (a) replay'de çapayı kes, (b) PIT arşivine bağla — ikisi de ölçüm kartı ister | §2.3 · §4 madde 4 |
| 6 | ROADMAP §2 öneri havuzu | `earnings_8k_tarihleri.csv` motorda hiç okunmuyor | §1.4 · §4 madde 6 |
| 7 | Çalışma zamanı bağlama (opsiyonel) | `watchdog.parity_report`a `pit_yasasi` satırı | §4 madde 7 |
| 8 | Kalan kapsam sınırları | yeni vokabülerle konuşan kapı / yeni değerlendiricili tarayıcı görünmez | §6 |

**Yasanın bugünkü hükmü:** `pitlaw.rapor()["ok"] is True` — canlı ağaçta tarihsel yolda beyansız
ihlal yok, canlı borç tabanı aşılmadı, beyanlar gerçek, sınıf ataması kaynakla uyuşuyor, iki
sözleşme kaydı da tam. **Tek açık ihlal beyanlı** (`BILINEN_IHLALLER`, kalem 5).

> **CLAUDE.md hakkında bir dürüstlük notu — mtime DEĞİŞTİ, İÇERİK DEĞİŞMEDİ.** §4 metni bir ara
> bu oturumda uygulanmaya başlandı, operatör durdurdu ve **iki değişiklik de geri alındı**.
> Dosya orijinal hâlinde (224 satır; §4'teki satır yine tek satırlık
> `- **PIT'siz fundamentals proxy yasak.**`), ama **dosya yeniden yazıldığı için mtime bugüne
> kaydı.** `git diff CLAUDE.md` BOŞ çıkmalı — çıkmıyorsa geri alma eksik kalmış demektir, öyleyse
> bana değil diff'e güvenin. (Emsal: içerik-aynı yeniden yazımın mtime alarmı tetiklemesi —
> `bounds.yaml`/`goal.yaml` vakası.)

---

## 1. ÖLÇÜM — fundamentals verisi tüketen yollar

Ölçüm **yalnız kaynak koddan** yapıldı: ağ çağrısı yok, `python`/`pytest` dışı koşum yok,
`state/` okunmadı (bu worktree'de zaten yalnız `goal.yaml` + `bounds.yaml` var).

### 1.1 Adaptör katmanı — PIT durumu

| Akış | Sembol | As-of alanı | PIT hükmü |
|---|---|---|---|
| shares_outstanding | `adapters/edgar_shares.py::as_of_shares_series` | `filed` | **PIT** |
| insider Form-4 (ham defter) | `adapters/insider.py::fetch_delta` → `_kanonik` | `filingDate`→`filing_tarihi` | KISMİ |
| short_interest | `adapters/shortinterest.py::fetch` | `settlementDate` | KISMİ |
| index üyeliği | `adapters/constituents.py::as_of` | `changes[].date` | KISMİ (besleyeni kapalı) |
| earnings takvimi (Nasdaq) | `adapters/data.py::nasdaq_earnings_window` | **YOK** | PIT-DEĞİL |
| earnings takvimi (FMP) | `adapters/fmp.py::earnings_dates` | **YOK** | PIT-DEĞİL |
| insider özet skoru | `adapters/insider.py::ozet` | **YOK** (defterdeki as-of özete taşınmaz) | PIT-DEĞİL |
| float/shares (payda) | `adapters/shortinterest.py::float_cek` → `fmp.profile` | **YOK** | PIT-DEĞİL |
| profil | `adapters/fmp.py::profile` | **YOK** | PIT-DEĞİL |
| ekran evreni | `adapters/finviz.py::discover_universe` | **YOK** | PIT-DEĞİL |
| kazanç takvimi (tüketim) | `earnings.py::_load` → `state/earnings.csv` | **YOK** | PIT-DEĞİL |

**Deponun tek gerçek PIT temel-veri akışı `edgar_shares`tır.** Kendi başlığındaki hüküm:
t gününde bilinen küme `filed <= t`'dir; `end <= t` PIT DEĞİLDİR, geleceği sızdırır. Yazma yolu
yoktur, kaynak depo-içi statik dosyadır (`research/edgar_facts/shares_outstanding.csv.gz`).

**`earnings.csv` neden PIT değil (modülün kendi ölçümü, kart EDG-2026-060):** takvim bir
nokta-zaman arşivi değil, ileriye dönük tazeleme önbelleğidir; `refresh` geri çekilen GELECEK
tarihleri dosyadan **siler**, yani dünkü hüküm bugünkü dosyadan yeniden üretilemez.

**PIT birikim defteri VAR ama okuyucusu yok:** `earnings.py::_snapshot` →
`state/history/earnings_snapshots.jsonl`, `fetch_date` + `digest` ile gerçek PIT yapısı. Tek
tüketici `snapshot_stats` ve o yalnız sayar; `kayitlar` alanını döndürmez.

### 1.2 Karar yüzeyi — hangi PIT'siz kaynak neyi besliyor

**EVET, besliyor.** Tek akış: `earnings` (`state/earnings.csv`), dört yerden:

| Yer | Ne yapıyor | Yüzey |
|---|---|---|
| `loop.py::daily_cycle` → `earnings.in_blackout` | 5 gün içinde rapor varsa **sert `NO_GO`** | KARAR |
| `loop.py::daily_cycle` → `earnings.calendar_untrustworthy` | o turdaki **tüm `GO`→`REVIEW`** | KARAR |
| `strategy.py::evaluate_episodic_pivot` → `days_since_report` | zorunlu çapa; yoksa sinyal yok | KARAR |
| `strategy.py::evaluate_pead` → `days_since_report` | zorunlu çapa; yoksa sinyal yok | KARAR |

Dördü de **default açık** (bayrak yok). `episodic_pivot`/`pead` `ARMED_SETUPS` dışındadır ama
`loop.py`nin `dormant_setup` → `explore_pool` dalı onları ≤0.25R **gerçek emre** taşır.

**Karar yüzeyine GİRMEYEN akışlar** (ve kesildikleri yer): `insider` ve `short_interest` — karar
tüketicisi hiç yok, `codelaw` beyanlarında gerekçesi yazılı ("ölçülmeden kapıya bağlanırsa hiç
ölçülmemiş bir kısıt canlı stratejiyi daraltmış olur"); `fmp.profile` — tek tüketici
`shortinterest.float_cek`; `constituents` — yalnız `universe_drift` raporu; `finviz` — evreni
genişletir ama filtreleri tamamen teknik/likidite (`fa_*` alanı yok).

**`edgar_shares` karar yüzeyinde ama ağırlığı 0:** `strategy.py::_turnover_now` →
`turnover_score`, `entry.w_turnover` varsayılanı `0.0`. **Uyuyor, ölü değil:** `state/bounds.yaml`
bu düğmeyi `{min:0.00, max:0.40}` ile arama uzayına koymuş. Kaynağı PIT olduğu için terfi etse
bile yasayı ihlal etmez.

### 1.3 ÖLÇÜLEMEYENLER (None + neden)

- **Canlı `entry.w_turnover` değeri** — `state/strategy.yaml` bu worktree'de yok.
- **`state/earnings.csv`nin bugünkü kapsamı/ufku** — dosya bu worktree'de yok. Koddaki en son
  damgalar (251'in 194'ü / 250'nin 181'i) **alıntıdır, bugün doğrulanmadı**.
- **Sağlayıcı yanıtlarının gerçek alanları** — ağ çağrısı yapılmadı. Tüm as-of hükümleri kodun
  OKUDUĞU alanlara dayanır; kodun okumadığı bir alan yanıtta var olabilir (özellikle FMP
  `earnings` ucunda `updatedFromDate`, insider akışında `acceptedDate`).
- **`massive.py`de temel-veri ucu** — bu kapsamda bulunamadı (okunan kısım bar/agrega ve tek
  referans ucu gösterdi). "Yoktur" değil, "bu kapsamda bulunamadı".

### 1.4 Ölçüm sırasında çıkan, istenmeyen ama kayda değer bulgu

`research/edgar_facts/` altında **PIT'li veri hazır duruyor ve motor okumuyor**:
`fundamentals.csv.gz` ve `earnings_8k_tarihleri.csv` (`filed` + `acceptance` damgalı).
`meridian/` içinde bu iki dosyayı okuyan tek satır yok — `edgar_facts` eşleşmelerinin tamamı
`shares_outstanding.csv.gz`dir. Yani PIT'li kazanç duyuru tarihleri depoda dururken kazanç akışı
anahtarsız Nasdaq + FMP anlık takvimine bağlı.

---

## 2. ÇİVİ — `meridian/pitlaw.py`

### 2.1 Neyi kırmızı yapar (iki dünya, iki hüküm)

Geriye-dönük önyargı kaynağın kendisinden değil, **geçmiş bir tarihe sorulmasından** doğar.
Takvime "bugün önümüzdeki 5 gün rapor var mı" demek meşrudur; aynı takvime "2023-04-11'de var
mıydı" demek uydurmadır. Bu yüzden hüküm ikiye ayrıldı (emsal: `codelaw`ın `.py` sıfır-toleransı
vs `.tsx` çırçırı):

- **`TARIHSEL_YOL`** (`backtest.py`, `cf_backfill.py`, `component_ic.py`, `shadow_lifecycle.py`)
  → **SIFIR TOLERANS.** PIT'siz `karar_etkili` bir sembole doğrudan ya da modül-içi kapanımla
  ulaşan çağrı kırmızıdır.
- **`CANLI_KARAR_YOLU`** (`loop.py`, `strategy.py`, `guard.py`, `score.py`, `prescreen.py`,
  `sieve.py`, `probgate.py`, `shadow_variants.py`) → **ÇIRÇIR.** `CANLI_TABAN = 5`; borç
  büyüyemez, taban **düşer, yükselmez** (ayrı çiviyle bağlı).

**Sınıf ayrımı hükmü taşır:** kayıt her sembole `karar_etkili` / `bilgi` sınıfı verir. `bilgi`
sınıfı bir kaynağın tarihsel yolda okunması ihlal değildir — dönüşü bir hükme girmez. Ayrım
uydurulmadı, çağrı yerinden okundu: `earnings.known` dönüşü yalnız `gate_reasons`a metin ekler ve
`verdict` o satırda yeniden atanmaz; `in_blackout` dönüşü `verdict = "NO_GO"` yazar.

### 2.2 Kapsam beyanı — neyi GÖRÜR, neyi GÖREMEZ

**Görür:** doğrudan çağrı (`earnings.in_blackout(...)`), takma adlı import
(`from . import earnings as earn`), `meridian.x.y()`, `__import__(...).y()`, ve modül-içi
kapanımla kurulan dolaylı zincir — **fonksiyon referansı bacağı dahil**
(`for fn in (evaluate_pead,): fn(...)`).

**Göremez, ve `gorulmeyen` kovasında ADIYLA sayar:**
- `dinamik_erisim` — `getattr(modül, "ad")` biçimi,
- `kayitta_yok` — kaynak kaydında hiç geçmeyen bir `adapters/` modülü.

**Göremez ve beyanla çözülür:** bir çağrının hangi **koşul altında** koştuğu. Statik tarayıcı
`if pit:` bloğunu değerlendiremez → `PIT_KORUMALI_ZINCIRLER` kaydı.

**Sonraki turlarda eklenen kapsam sınırları** (hepsi ADIYLA raporlanır, ayrıntı §5'te):
- `kapi_sozlesmesi_okunamadi` / `sinyal_sozlesmesi_okunamadi` — iki sözleşmeden biri okunamazsa
  **hiçbir sembol için** sınıf hükmü verilmez (kısmi türetimle hüküm vermek, ölçemediğini
  "bilgi" saymakla aynı kapıya çıkardı).
- `sinif_olculemedi` — karar modüllerinde çağrısı olmayan semboller: beyanları bu kapsamda
  **çürütülemedi**, "doğrulandı" değil.
- Sentetik kökte sınıf ve kayıt hükümleri `None` döner (boş liste değil) — bir tmp ağacında
  kaydın tüm çağrı yerleri bulunmaz, orada hüküm kurmak **kategori hatası** olurdu.
- İki sözleşmenin ortak sınırı: tarama **bilinen** vokabüler / **bilinen** üreticilerle yapılır.
  Tamamen yeni sabitlerle konuşan bir kapı ya da tamamen yeni değerlendiriciler koşturan bir
  tarayıcı görünmez — ve bu sınırın kendisi çivili (`test_TAMAMEN_YENI_degerlendiricili_...`).

Görülmeyen ihlal **sayılmaz** (uydurma yasağı) ama **sayılır**: `ok`u etkilemez, rapora çıkar.
Sıfır sonuç "yok" değil, "bu kapsamda bulunamadı" demektir.

### 2.3 GERÇEK İHLAL BULUNDU — düzeltilmedi, beyan edildi

**`BILINEN_IHLALLER` (iki kayıt, aynı sınıf): BEYAN EDİLMEMİŞ ASİMETRİ.**

`backtest.replay` ve `cf_backfill._plans_for_session` `earnings.in_blackout`u **bilerek kesti** ve
yerine `olculemedi_replay` / `olculemedi_cf` sayacı koydu — gerekçesi kodda yazılı. Ama **aynı
dosyalardaki** `strat.scan_entry` / `strat.scan_all` çağrısı, `scan_all → evaluate_pead /
evaluate_episodic_pivot → earnings.days_since_report` zinciri üzerinden **aynı PIT'siz takvimi
tarihsel seansa sokuyor.**

- `backtest.py` → `strat.scan_entry` (replay döngüsü)
- `cf_backfill.py` → `strat.scan_all` (iki yerde: normal ve gevşetilmiş eşik)

**Bugün zararsız, ama beyansız:** yön sözleşmesi (`0 <= (d-e).days <= max_days`) ileri sızıntıyı
engeller ve `arming._kanit_durumu` bunun pratikte hep `False` döndüğünü ölçmüştür (takvim ufku
karşı-olgusal defterin başlangıcından sonra). Yani `in_blackout` ile **aynı beyan seviyesinde
değil**: biri kesilip gerekçesi yazılmış, öteki sessizce açık kalmış.

**Düzeltme YAPILMADI (görev gereği) ve AYRI KARARDIR.** İki yol: (a) çapayı replay bacağında da
kesip `olculemedi_*` sayacına eklemek — `in_blackout` emsalinin birebir uygulanması; (b) çapayı
PIT arşivine (`research/edgar_facts/earnings_8k_tarihleri.csv`, `filed`/`acceptance` damgalı)
bağlamak — bu ikincisi `episodic_pivot`/`pead` kurulumlarını gerçekten ölçülebilir yapar ve
`arming._kanit_durumu`nun `olculemez_pit_yok` cümlesini `insufficient_cf`e döndürür.

**`PIT_KORUMALI_ZINCIRLER` (bir kayıt): ihlal DEĞİL.** `shadow_lifecycle` → `shadow_variants._judge`
zinciri görünür, ama `_judge` çağrıyı `if pit:` ile korur (kardeş-PIT düzeltmesi): tarihsel turda
`in_blackout` hiç çağrılmaz, satır `olculemedi_seed` sayılır. Ayrı kovada tutuldu çünkü
`BILINEN_IHLALLER` **düzeltilmemiş borcun** defteridir; bunu oraya koymak düzeltilmiş işi borç
gibi göstermek olurdu. Koruma kalkarsa kayıt çürür ve çivi öter.

---

## 3. TDD ve kanıt

**Çivi önce kırmızı doğdu.** İlk koşum: **8 failed / 14 passed** — ve iki gerçek kusur gösterdi:

1. **Canlı kayıt sentetik testi kirletiyordu.** `BILINEN_IHLALLER` sentetik `tmp_path` ağacında da
   koşuyordu; tmp'de kurulan `backtest.py → days_since_report` zinciri "beyanlı" sayılıp pozitif
   kontrol sessizce yeşile döndü. Bu, `codelaw.declared_claims`in "ENJEKSİYON = YALITIM" dersinin
   birebir tekrarıydı. Kapatıldı: canlı defterler yalnız üretim kökünde (`VARSAYILAN_KOK`) koşar.
2. **Kapanım asıl zincirin geçtiği yerde kopuyordu.** `strategy.scan_all` değerlendiricileri bir
   demetten koşturur (`for fn in (…, evaluate_pead, …): fn(...)`) — `evaluate_pead` bir **çağrı
   değil ad**. Yalnız çağrılara bakan kapanım `backtest → scan_entry → scan_all → evaluate_pead`
   zincirini göremiyordu. `_dokunulan_adlar` referans bacağıyla kapatıldı.

**Sonra yeşil:** `26 passed`, `PYTEST_EXIT=0`, `grep -E "FAILED|ERROR"` boş (üçlü hüküm).

**Mutasyon — çivinin gerçekten ısırdığının kanıtı (5/5):**

| # | Mutasyon | Sonuç |
|---|---|---|
| M1 | kapanımdan referans bacağı kaldırıldı | 3 failed — ısırdı |
| M2 | `TARIHSEL_YOL`dan `backtest.py` çıkarıldı | 6 failed — ısırdı |
| M3 | `CANLI_TABAN` 5→6 yükseltildi | 1 failed — ısırdı |
| M4 | korumalı-zincir kaydı yanlış sembole bağlandı | 4 failed — ısırdı |
| M5 | `karar_etkili` süzgeci kaldırıldı | 5 failed — ısırdı |

**M2 ilk denemede "ısırmadı" göründü ve sebebi mutasyonun kendisiydi:** `sed` deseninde "geçmiş"
yerine ASCII "gecmis" yazılmıştı, satır hiç silinmemişti. Doğru desenle tekrarlandı → 6 failed.
Kayda geçiyor çünkü "mutasyon ısırmadı" hükmü, mutasyonun gerçekten uygulandığı doğrulanmadan
verilemez.

**Koşum biçimi ve bir tuzak:** worktree'de `.venv` **yok**; ana checkout'un venv'i kullanıldı ve
`_editable_impl_meridian.pth` `/Users/erdemozturk/AI-Trading`e (ana checkout) işaret ediyor —
yani `PYTHONPATH` verilmeseydi pytest **worktree'nin değil ana checkout'un** kaynağını ölçerdi.
Komut:

```bash
PYTHONPATH=$PWD /Users/erdemozturk/AI-Trading/.venv/bin/python -m pytest tests/test_pit_yasasi_v341.py
```

**Bir "yeşil ama yanlış" vakası daha yaşandı ve üçlü hüküm yakaladı:** etkilenen kümenin ilk
koşumunda harness "completed (exit code 0)" bildirdi; dosyadaki gerçek satır `PYTEST_EXIT=4`
(kullanım hatası) idi ve **hiçbir test koşmamıştı** (dosya listesi tek argüman olarak geçmişti).
Bildirim uyandırır, hüküm vermez.

### 3.1 Etkilenen test kümesi

Üretim `.py` kaynağına **yeni bir modül eklendi**, yani `codelaw`ın taradığı ağaç değişti. Bu
yüzden kapsam "yeni dosyanın kendisi" değil, **`codelaw`a atıf yapan tüm test dosyaları**
(`grep -rl codelaw tests/`, `conftest.py` hariç — v337 dahil **45 dosya**) olarak alındı. Tam
suite koşulmadı ve orantısız olurdu: mevcut hiçbir modül düzenlenmedi, yalnız taranan ağaca bir
dosya eklendi. Otoriter suite yine de Rol-1'in işidir (§4 madde 2).

**Küme her turda yeniden kuruldu** — çünkü `pitlaw` her turda yeni bir sözleşmeye bağlandı ve
"etkilenen" tanımı genişledi. Desenler sırayla: `codelaw` → `codelaw|pitlaw` →
`codelaw|pitlaw|classify_gate` → `codelaw|pitlaw|classify_gate|scan_all`.

**Hüküm (üçlü, 2026-08-30 — birinci tur):** 45 dosya · **1093 passed, 22 skipped** · 3 dk 38 sn ·
`PYTEST_EXIT=0` · `grep -E "FAILED|ERROR"` **boş**. Kırmızı yok.

**Hüküm (üçlü, 2026-08-31 — ikinci tur, v338 dahil):** 46 dosya · **1109 passed, 22 skipped** ·
3 dk 39 sn · `PYTEST_EXIT=0` · `grep -E "FAILED|ERROR"` **boş**. Fark tam olarak +16 = v338'in
çivi sayısı; mevcut çivilerde gerileme yok. Küme `grep -rl "codelaw\|pitlaw" tests/` ile kuruldu
(v338 `codelaw`ı doğrudan import etmez, yalnız `pitlaw`ı — ilk turun deseni onu kaçırırdı).

**Hüküm (üçlü, 2026-08-31 — üçüncü tur, karar adları türetildi):** 66 dosya ·
**1543 passed, 25 skipped** · 4 dk 20 sn · `PYTEST_EXIT=0` · grep **boş**. Küme
`classify_gate` tüketicileriyle genişletildi: `pitlaw` artık guard sözleşmesine bağlı, o
sözleşmeyi sınayan çiviler de etkilenen kümededir.

**Hüküm (üçlü, 2026-08-31 — dördüncü tur, erken `return` daraltıldı):** 75 dosya ·
**1641 passed, 36 skipped** · 8 dk 52 sn · `PYTEST_EXIT=0` · grep **boş**. Küme bu kez
`scan_all` tüketicilerini de kapsıyor (ikinci sözleşme oraya bağlandı).

**Hüküm (üçlü, 2026-08-31 — beşinci tur, kapı sözleşmesi listeye):** 75 dosya ·
**1646 passed, 36 skipped** · 8 dk 51 sn · `PYTEST_EXIT=0` · grep **boş**.

**Hüküm (üçlü, 2026-08-31 — altıncı tur, sinyal sözleşmesi simetrik):** 75 dosya ·
**1653 passed, 36 skipped** · 8 dk 54 sn · `PYTEST_EXIT=0` · grep **boş**. Fark +7 = altıncı
turun yeni çivileri; mevcut çivilerde gerileme yok. **Bu, teslim edilen hâlin ölçümüdür.**

Her turun koşumu, o turun **son düzenlemesinden SONRA** yapıldı; yani her yeşil, o turda teslim
edilen hâlin ölçümüdür. Kapsam turdan tura genişledi çünkü `pitlaw` yeni sözleşmelere bağlandı:
önce `codelaw`, sonra `pitlaw`, sonra `classify_gate`, sonra `scan_all` tüketicileri.

**Donmuş ağaç disiplini uygulandı:** arka planda kapsam koşumu sürerken dosya düzenlenmedi. Bir
turda kullanıcı isteği koşumun ortasına denk geldi ve düzenleme, koşum bitene kadar bekletildi —
koşan ağacı değiştirmek sonucu geçersiz kılardı (§6).

**Çivi dosyasında sahte satır çapası doğurulmadı — bilinçli.** Pozitif kontrollerin beklenen
değeri `"backtest.py:5"` biçiminde yazılsaydı, `codelaw`ın satır-çapası yasası (`_CAPA_DESENI`,
sıfır tolerans, `tests/` de taranır) bunu gerçek bir çapa sayar ve hükmü **depodaki**
`meridian/backtest.py`nin 5. satırına bağlardı — testin sentetik `tmp_path` ağacıyla hiç ilgisi
olmayan bir dosyaya. Bugün o satırlar tesadüfen çürük değil (ikisi de docstring metni), ama
`backtest.py`/`loop.py` başlığı değiştiği gün çivi ilgisiz bir sebeple kırmızıya dönerdi. Dosya
ve satır `_dosya()` / `_satir()` yardımcılarıyla AYRI sınanıyor.

---

## 4. Rol-1'e devredilenler

**Mekanik işler (karar gerektirmez):**

1. **Commit** — üç yeni dosya (`meridian/pitlaw.py`, `tests/test_pit_yasasi_v341.py`,
   `tests/test_pit_sinif_turetimi_v342.py`) + bu brief. Motor kaynağına dokunulduğu için
   (`meridian/` altına yeni modül) **push, tam suite hükmünden ÖNCE atılmamalı** (§8, üç ardışık
   CI kırmızısı vakası).
2. **Tam suite** — donmuş ağaçta, tek-otoriter, arka planda; HEAD başta/sonda karşılaştırılarak.
   Bu oturumda **koşulmadı** (yan oturum yetkisi yok); yerine altı turun her birinde etkilenen
   küme koşuldu (§3.1, en genişi 75 dosya / 1646 test).
3. **`v337` ve `v338` numaraları** — ölçümle boştular (en büyük `v336`). Rol-1 commit öncesi
   `main`de yeni bir `v337`/`v338` doğmadığını doğrulamalı (vaka v331×2). **Ayrıca kayda geçsin:
   `v325` iki dosya taşıyor** — kimlik kuralı orada zaten kırık; bu turlar onu ne büyüttü ne
   düzeltti.

**Operatör/Rol-1 kararı bekleyenler:**

4. **`BILINEN_IHLALLER`in düzeltmesi — TEK GERÇEK İHLAL.** `backtest.py` ve `cf_backfill.py`,
   `in_blackout`u bilerek kesmişken `scan_entry`/`scan_all` üzerinden aynı PIT'siz takvimi
   tarihsel seansa sokuyor (§2.3). Bugün zararsız ama beyansız. İki seçenek: (a) replay'de çapayı
   kesmek — `episodic_pivot`/`pead`ın karşı-olgusal ateşlemelerini sıfırlar; (b) PIT arşivine
   bağlamak — yeni bir okuma yolu açar ve `arming._kanit_durumu`nun `olculemez_pit_yok` cümlesini
   `insufficient_cf`e döndürür. İkisi de ölçüm kartı ister.
5. **CLAUDE.md güncellemesi — HAZIR METİN, UYGULAMA ROL-1'DE.** Yasa artık ricaya dayalı değil,
   ama **CLAUDE.md deponun yasasıdır ve yan oturum ona dokunmaz.** Bu turlarda dokunulmadı; metin
   aşağıda uygulanmaya hazır duruyor. (Bir ara yan oturumda düzenlenmeye başlandı, operatör
   durdurdu ve iki değişiklik de geri alındı — dosya orijinal 224 satırında.)

   **(a) §4'teki satırın yerine:**

   ```markdown
   - **PIT'siz fundamentals proxy yasak** — artık MEKANİK (2026-08-31): denetçi
     `meridian/pitlaw.py::rapor`, çiviler `tests/test_pit_yasasi_v341.py` +
     `tests/test_pit_sinif_turetimi_v342.py`. İki dünya, iki hüküm: **tarihsel yeniden yürütme**
     (replay/geri-dolum/tohum) SIFIR TOLERANS; **canlı karar yüzeyi** beyanlı taban (bugün 5 —
     düşer, YÜKSELMEZ). Kaydın kendisi de denetlenir: sınıf ataması, karar adları ve iki sözleşme
     (`guard.classify_gate` · `strategy.scan_all`) kaynaktan türetilir; kayıtsız bir kapı yüzeyi
     ya da tarayıcı doğduğu gün çivi öter. **Açık bilinen ihlal + düzeltme kararı operatörde:**
     `docs/DEVIR-PIT-CIVISI-2026-08-30.md`.
   ```

   **(b) §2 eylem-anı matrisine iki satır** (yasa §2'de tetiklenmezse eylem anında görünmez):

   ```markdown
   | Temel-veri (earnings/insider/short-interest/float/profil/ekran) okumak | Kaynak PIT mi (as-of alanı VAR ve KORUNUYOR mu)? Dönüşü bir hükme mi giriyor yoksa yalnız etikete mi? **Tarihsel yeniden yürütmede** (replay/geri-dolum/tohum) PIT'siz kaynak SIFIR TOLERANS'tır (§4). |
   | Yeni kapı yüzeyi (`"GO"/"NO_GO"/"REVIEW"` döndüren fn) ya da yeni tarayıcı (`scan_all` gibi) yazmak | `pitlaw.KAPI_SOZLESMELERI` / `SINYAL_SOZLESMELERI` kaydına eklendi mi? Eklenmezse yasa o yüzeyde KÖR kalır — çivi bilinen vokabülerle konuşuyorsan öter, konuşmuyorsan ÖTMEZ. |
   ```

   **Uygularken dikkat:** CLAUDE.md `.md`dir, `dosya.py:NNN` çapası oraya YAZILMAZ — hiçbir
   tarayıcı görmez, sessizce çürür (§2 kapısı). Yukarıdaki metinler bu yüzden yalnız SEMBOL ve
   dosya adı taşıyor, satır numarası taşımıyor.
6. **Öneri (ROADMAP §2 havuzuna):** `research/edgar_facts/earnings_8k_tarihleri.csv` motor
   tarafından hiç okunmuyor (§1.4). PIT'li kazanç duyuru tarihleri hazır dururken karar yüzeyi
   PIT'siz takvime bağlı — bu, 4(b) seçeneğinin veri tarafı.
7. **Çalışma zamanı bağlama (opsiyonel).** `watchdog.parity_report`a bir
   `{"check": "pit_yasasi", "ok": pitlaw.rapor()["ok"], ...}` satırı bağlanırsa yasa panoda da
   görünür. Bu turlarda yapılmadı — `watchdog.py` düzenlemek gerekirdi ve kapsam çivilerdi.

---

## 5. Sonraki turlar (2–6) — yasanın KENDİ KAYDI da mekanikleşti

Turlar aynı zinciri izliyor: her tur, bir önceki turun "elle kalan" parçasını bir **sözleşmeden
türetilmiş** hâle getiriyor. Sıra tesadüf değil — her seferinde çivinin en zayıf halkası
devir notuna yazıldı ve sonraki tur onu kapattı.

### 5.1 İkinci tur — sınıf ataması mekanikleşti

İlk turun devrettiği "en zayıf halka" kapatıldı: `karar_etkili` / `bilgi` ayrımı artık **kaynaktan
türetiliyor** ve beyanla karşılaştırılıyor.

#### Neden gerekliydi

Yanlış sınıf, **yasayı kapatan tek satırdır**: `pitlaw.karar_etkili()` süzgeci yalnız
`karar_etkili` sembolleri yasağın konusu sayar, dolayısıyla bir sembol yanlışlıkla `bilgi`
kalırsa v337'nin bütün hükümleri o kaynak için sessizce devre dışı kalır.

#### Türetim kuralı — ölçülen çağrı yerlerinden çıkarıldı

Bir sembol `karar_etkili`dir eğer **bir karar modülünde**, çağrısının sonucu (doğrudan ya da
atandığı ad üzerinden) bir `if`/`while` **testine** giriyorsa **ve** o dalın içinde bir **karar
eylemi** varsa. Karar eylemi iki biçimdir ve **iki ayrı kaynaktan gelir**: bir **karar adına**
atama (kapı hükmü — §5.2'te türetilir), ya da erken `return` (sinyal üretmeme kararı; bu guard'dan
gelmez ve gelemez — `evaluate_pead` kapıya hiç ulaşmadan `None` döner).

Üç gerçek biçim ve neden ayrıştıkları:

| Çağrı yeri | Biçim | Türetim |
|---|---|---|
| `strategy.evaluate_pead` | çağrı doğrudan `if` testinde, dalda `return None` | KARAR |
| `loop.daily_cycle` → `in_blackout` | `_bl = …`, `if … and _bl:` dalında `verdict = "NO_GO"` | KARAR |
| `loop.daily_cycle` → `calendar_untrustworthy` | karar eylemi **iki sıçrama** ötede (iç içe `if`) | KARAR |
| `loop.daily_cycle` → `known` | hiçbir `if` testine girmez; yalnız üçlü ifade + `_checks.append({…})` | BİLGİ |

`calendar_untrustworthy` yüzünden dal taraması **özyinelidir**: yalnız dalın ilk seviyesine bakan
bir tarayıcı onu `bilgi` sanardı (mutasyon N3 bunu çiviliyor).

#### Hüküm — iki yönlü, ve `ok`u düşürür

- `beyan_bilgi_gercek_karar` — **en tehlikeli yön**; PIT'siz veri sessizce karara girer.
- `beyan_karar_gercek_bilgi` — kayıt fazla katı; gereksiz kısıt da bir hatadır (arming v301'in
  ikinci yönü).

`sinif_celiskileri` artık `rapor()["ok"]`ın dördüncü bileşenidir.

**Kapsam dürüstlüğü:** türetim yalnız **karar modüllerinde** koşar — `api.py`deki bir
`if …: return` bir HTTP yanıtı döndürür, bir emri değil. Karar modüllerinde çağrısı olmayan
semboller `sinif_olculemedi` kovasında **adıyla** durur ve `ok`u etkilemez: beyanları bu kapsamda
**çürütülemedi**, "doğrulandı" değil. Bugün `insider.ozet`, `shortinterest.ozet`, `fmp.*`,
`finviz.*`, `constituents.current`, `data.nasdaq_earnings_window` bu kovadadır — karar yüzeyine
bağlandıkları gün türetim onları görmeye başlar.

**Canlı ağaç sonucu:** çelişki **yok**; `earnings.in_blackout`, `days_since_report`,
`calendar_untrustworthy` karar bağı **ölçümle doğrulandı**, `earnings.known`ın `bilgi` olduğu da
(çağrı yokluğundan değil, ölçümle) doğrulandı.

#### TDD ve ölçülen tuzak

Çivi yine **kırmızı doğdu**: v337'nin iki çivisi düştü ve sebep gerçek bir tasarım hatasıydı —
sınıf denetimini `rapor()`e bağlarken yalıtımı uygulamamıştım, sentetik `tmp_path` ağacında canlı
kayıtla sınıf hükmü veriliyordu. **Sınıf beyanı canlı ağaç hakkındadır**: kayıt, sembolün
üretimdeki TÜM çağrı yerlerine bakılarak yazılır; bir tmp ağacında o yerlerin ancak biri bulunur
ve "beyan karar diyor ama burada bağ yok" hükmü bir çelişki değil bir **kategori hatasıdır**.
Sentetik kökte üç sınıf alanı da artık `None` döner — boş liste "baktım, uyumlu" derdi
(`codelaw.report`un tsx alanlarıyla aynı disiplin). Tuzağın kendisi
`test_SENTETIK_kokte_sinif_hukmu_VERILMEZ_None_doner` ile çivilendi.

**Mutasyon (5/5 ısırdı, hepsinin uygulandığı doğrulandı):**

| # | Mutasyon | Sonuç |
|---|---|---|
| N1 | `KARAR_ADLARI`'ndan `verdict` çıkarıldı | 6 failed |
| N2 | erken `return` karar eylemi sayılmıyor | 3 failed |
| N3 | dal taraması özyinelemez yapıldı | 3 failed |
| N4 | tohum (atanan ad) bacağı kaldırıldı | 4 failed |
| N5 | sınıf kapsamı `api.py`ye açıldı | 1 failed |

N1–N4'te canlı-ağaç çivisi (`test_canli_agacta_SINIF_CELISKISI_YOK`) de kırmızıya döndü — yani
türetim gerçek kodda anlamlı ölçüm yapıyor, yalnız sentetik ağaçta değil. Mutasyon koşucusu bu
kez her mutasyonun **gerçekten uygulandığını** da doğruluyor (ilk turun M2 dersi: "mutasyon
ısırmadı" hükmü, mutasyonun uygulandığı doğrulanmadan verilemez).

### 5.2 Üçüncü tur — karar adları kapı sözleşmesinden türetildi

§6'nın "karar eylemi kümesi elle" kalemi kapatıldı. `KARAR_ADLARI` sabiti **kaldırıldı**;
karar adları artık `guard.classify_gate` sözleşmesinden türetiliyor.

**Neden guard:** `classify_gate` kendi beyanında "BU FONKSİYON SERT ZARFIN TEK KAYNAĞIDIR" diyor
ve `check_trade` bile kopya tutmayı bırakıp onu çağırıyor — "iki yüzeyin ayrışması yapısal olarak
imkânsız" olsun diye. Karar adlarını ayrı bir listede tutmak, tam da o kopyayı yasa katmanında
yeniden doğurmak olurdu.

**Türetim iki adımlı, ikisi de koddan:**
1. **Vokabüler** — `classify_gate` gövdesindeki her `return`ün **ilk** pozisyonundaki string sabit:
   `{"GO", "NO_GO", "REVIEW"}`. İkinci pozisyon gerekçedir ve karar taşımaz. Hüküm docstring'den
   değil `return`'lerden okunur: docstring bayatlar, `return` bayatlamaz.
2. **Karar adları** — karar modüllerinde bu vokabülerden bir sabite atanan adlar. Tuple açımı
   pozisyonel çözülür: `verdict, reasons = "NO_GO", list(...)` → yalnız `verdict`.

**ÖLÇÜM SONUCU — elle liste yanlıştı.** Türetim tek ad buldu: **`verdict`** (5 yer: `loop.py` ×4,
`shadow_variants.py` ×1). Elle yazdığım liste `score`, `score_num`, `size_r`'ı da taşıyordu ve
**hiçbiri tek bir kanıt bile üretmiyordu** — ölü kayıt. Bu deponun yasasına göre ölü muafiyet
çürüktür, dolayısıyla üçü de kaldırıldı; "ileride lazım olur" diye tutmak kaydı bir dilek
listesine çevirirdi.

**Sözleşme okunamazsa sınıf hükmü HİÇ verilmez.** `guard.py` yoksa ya da `classify_gate` adı
değişirse `karar_vokabuleri` `None` döner ve her sembol `kapi_sozlesmesi_okunamadi` nedeniyle
ölçülemedi sayılır. Boş ad kümesiyle devam etmek, kapı hükmüne bağlı **her** sembolü sessizce
`bilgi` ilan ederdi — yasayı kapatan tam da o satır olurdu.

**Yine kırmızı doğdu, yine gerçek bir ayrım hatası:** ilk yazımda `frozenset(adlar) or None`
yazmıştım, yani **boş küme ile ölçülemedi tek değere toplanıyordu**. Sözleşmesi sağlam ama kapı
hükmünü hiçbir ada akıtmayan meşru bir ağaç (yalnız erken-`return` ile karar veren alt küme)
"sözleşme okunamadı" hükmü alıyordu. İkisi ayrıldı: `None` = sözleşme okunamadı,
`frozenset()` = sözleşme okundu, bu ağaçta karar adı yok.

**Mutasyon (4/4 ısırdı, hepsinin uygulandığı doğrulandı):**

| # | Mutasyon | Sonuç |
|---|---|---|
| P1 | `KAPI_SOZLESMESI` fonksiyon adı bozuldu | 15 failed |
| P2 | vokabüler ilk yerine **son** tuple pozisyonundan okundu | 15 failed |
| P3 | tuple pozisyonel eşleştirme çarpıma çevrildi (`reasons` sızar) | 2 failed |
| P4 | boş ad kümesi yine `None`'a toplandı (eski hata geri kondu) | 3 failed |

P1/P2'nin 15 çiviyi birden düşürmesi beklenen ve istenen: sözleşme yanlış okunursa sınıf
katmanının **tamamı** hükümsüzdür, tek tek testler değil.

### 5.3 Dördüncü tur — erken `return` bacağı daraltıldı

§6'nın bıraktığı son kalem kapatıldı: karar eyleminin ikinci biçimi (erken `return`) artık **her**
dönüşü karar saymıyor.

**Sorun:** `if not veri: return` bir bakım/koruma dönüşüdür; `if not earn.days_since_report(...):
return None` ise "kurulum bugün ateşleyemez" hükmüdür. İkisi aynı AST biçimindedir ve daraltmadan
önce ayırt edilemiyordu.

**Ölçüt yine bir sözleşmeden geldi:** `strategy.scan_all`. Erken `return` yalnız kapsayan fonksiyon
`scan_all`ın koşturduğu değerlendiriciler arasındaysa karar sayılır. `scan_all` değerlendiricilerin
tek kaydıdır ve kendi docstring'i bunu söyler ("Her ekran BU ticker'da HER ZAMAN koşar →
{setup: EntrySignal}") — bir değerlendirici o demete girmeden sinyal üretemez.

Türetim `scan_all` gövdesindeki fonksiyon **adı referanslarını** alıp aynı modülde **tanımlı**
fonksiyonlarla kesiştiriyor; `by_setup`/`sig` gibi yerel adlar böyle eleniyor. Canlı ölçüm:
`evaluate_entry`, `evaluate_momentum_burst`, `evaluate_pullback`, `evaluate_episodic_pivot`,
`evaluate_exhaustion_hammer`, `evaluate_pead`, `evaluate_canslim`.

**İki sözleşme de gerekli.** Karar eyleminin iki biçimi iki ayrı kayıttan gelir; biri okunamazsa
türetim eksiktir ve hangi sembolün hangi bacağa bağlı olduğu önceden bilinemez. `guard.py` ya da
`strategy.scan_all` okunamazsa her sembol `kapi_sozlesmesi_okunamadi` /
`sinyal_sozlesmesi_okunamadi` nedeniyle ölçülemedi sayılır — kısmi türetimle hüküm verilmez.

**Canlı sonuç değişmedi:** `days_since_report`ın karar bağı `evaluate_pead` ve
`evaluate_episodic_pivot` içindedir, ikisi de üretici kümesinde. Yani daraltma yanlış pozitif
yüzeyini küçülttü, gerçek hükmü bozmadı.

**Ölçülen tuzak:** sözleşme yardımcısını her sentetik teste koşulsuz eklemek iki testin ölçtüğü
şeyi bozdu — `strategy.py`ye fazladan bir çağrı yeri giriyordu. Yardımcıya çağrısız varyant
(`cagri=False`) eklendi: sözleşme sağlanır, ağaca çağrı yeri girmez.

**Mutasyon (4/4 ısırdı):**

| # | Mutasyon | Sonuç |
|---|---|---|
| R1 | daraltma kaldırıldı (her erken `return` yine karar) | 1 failed — tam hedefinde |
| R2 | `SINYAL_SOZLESMESI` fonksiyon adı bozuldu | 14 failed |
| R3 | üretici kümesi tanımlı-fonksiyon kesişimi olmadan alındı | 2 failed |
| R4 | iki-sözleşme şartından sinyal bacağı çıkarıldı | 1 failed |

### 5.4 Beşinci tur — kapı sözleşmesi listeye çevrildi, iki yönlü tamlık

`KAPI_SOZLESMESI` (tek tuple) → `KAPI_SOZLESMELERI` (liste). **Bugün hâlâ tek eleman taşıyor** ve
bu bilinçli: ölçüm (`meridian/` ağacında karar sabiti döndüren fonksiyonlar) tek kapı yüzeyi
buldu — `guard.classify_gate`. Boş bir yer tutucu eklenmedi; ölü kayıt çürüktür.

**Asıl kazanç listede değil, `kapi_sozlesme_denetimi`nin iki yönlülüğünde** (yine
`arming.PIT_CAPALI_KURULUMLAR` / v301 deseni):

- `curuk` — kayıtta duran ama kodda bulunamayan sözleşme (modül yok ya da fonksiyon adı değişti).
- `kayitsiz` — **kayıtta olmayan ama karar sabiti döndüren fonksiyon.** İkinci bir kapı yüzeyi
  doğduğu gün buradan görünür. Bu olmadan yeni kapı, hükümleri sınıf türetimine hiç girmediği
  için yasanın **sessiz kör noktası** olurdu — kullanıcının işaret ettiği risk tam olarak buydu.

İkisi de `ok`u düşürür (yalnız üretim ağacında; sentetik köklerde kayıt sözleşmesi bulunamaz ve
orada "çürük" hükmü kurmak sınıf katmanındaki kategori hatasının aynısı olurdu).

**KAPSAM BEYANI — dürüst sınır:** `kayitsiz` taraması **bilinen vokabülerle** yapılır. Tamamen
yeni sabitlerle konuşan bir kapı (`"BLOCK"` gibi) bu tarayıcıya görünmez; o gün kayıt elle
açılmalıdır. Sıfır sonuç "başka kapı yok" değil, **"bilinen vokabülerle konuşan başka kapı
bulunamadı"**dır.

**Bir eksik mutasyonla açığa çıktı:** `ok` bileşenlerini sayan çivi kayıt denetimini içermiyordu.
Bugün ikisi de boş olduğu için formülden düşseler fark edilmezdi — S2/S4 mutasyonları bunu
gösterdi ve çivi altı bileşeni birden sayacak şekilde genişletildi.

**Mutasyon (5/5 ısırdı):**

| # | Mutasyon | Sonuç |
|---|---|---|
| S1 | kayıtsız kapı taraması kapatıldı | 1 failed — tam hedefinde |
| S2 | kayıtlı sözleşme muafiyeti kaldırıldı (kendi kaydını ihbar eder) | 6 failed |
| S3 | çürük sözleşme taraması boşaltıldı | 1 failed |
| S4 | kayda var olmayan bir sözleşme eklendi | 4 failed |
| S5 | `ok` formülünden `kayitsiz` çıkarıldı + sahte kayıt | 2 failed |

### 5.5 Altıncı tur — sinyal sözleşmesi de simetrik hale getirildi

§6'da beyan edilen asimetri kapatıldı: `SINYAL_SOZLESMESI` → `SINYAL_SOZLESMELERI` (liste) ve
`sinyal_sozlesme_denetimi` kapı tarafının birebir kardeşi olarak eklendi. Asimetri bırakmak, iki
sözleşmeden birini korumasız bırakmak olurdu.

- `curuk` — kayıtta duran ama kodda bulunamayan tarayıcı.
- `kayitsiz` — **kayıtta olmayan ama değerlendiricileri bir arada koşturan fonksiyon**: ikinci bir
  tarayıcı. Bulunmazsa onun koşturduğu değerlendiricilerin erken `return`leri karar sayılmaz ve
  PIT'siz bir kaynak sessizce `bilgi` sınıfına düşer.

**Ölçüt:** üretici kümesinden **≥2** adı `ast.Name` (Load) olarak anmak (`_TARAYICI_ESIGI = 2`).
Eşik 1 olsaydı tek değerlendiriciyi çağıran her sarmalayıcı tarayıcı sayılırdı; 2, "bir arada
koşturma"nın en küçük gözlemlenebilir biçimidir.

**AST şart, metin taraması değil:** depoda `evaluate_pead` gibi adlar `watchdog`, `indicators`,
`component_ic`, `reflect`, `ledgers`, `arming` içinde **yorum/docstring** olarak geçiyor. Ölçüm
(2026-08-31) `strategy.py` dışında tek bir gerçek kod referansı bulmadı — yani ikinci tarayıcı
bugün yok, tıpkı ikinci kapı yüzeyi gibi. Metin taraması bunların hepsini tarayıcı sanırdı.

**İki test kusuru ölçümle bulundu ve ikisi de kayda değer:**
1. İlk "ikinci tarayıcı" senaryom yalnız **bir** bilinen üreticiyi anıyordu (ikincisi kayıtlı
   demette değildi, dolayısıyla bilinen değildi) — yani testin kendisi kapsam sınırına düşmüştü.
   Sınır artık `test_TAMAMEN_YENI_degerlendiricili_tarayici_GORUNMEZ` ile **çivili**: kapsam
   beyanı gizlenmiyor, ölçülüyor.
2. **Mutasyon T3 ısırmadı** — `Name Load` filtresi kaldırıldığında hiçbir test düşmedi, yani
   savunma çivisizdi. Çivi eklendi; ilk hâli de yanlıştı (`return evaluate_pead, evaluate_ikinci`
   adları Load bağlamına sokuyordu), Store-only senaryoya çevrildi ve mutasyon artık ısırıyor.

**Mutasyon (4/4 ısırdı):**

| # | Mutasyon | Sonuç |
|---|---|---|
| T1 | `_TARAYICI_ESIGI` 2→1 (sarmalayıcı da tarayıcı) | 1 failed — tam hedefinde |
| T2 | kayıtsız tarayıcı taraması kapatıldı | 1 failed |
| T3c | `Name Load` filtresi kaldırıldı | 1 failed (çivi eklendikten sonra) |
| T4 | kayda var olmayan bir tarayıcı eklendi | 3 failed |

**KAPSAM BEYANI (iki sözleşme için de aynı sınır):** tarama BİLİNEN vokabüler / BİLİNEN
üreticilerle yapılır. Tamamen yeni sabitlerle konuşan bir kapı ya da tamamen yeni değerlendiriciler
koşturan bir tarayıcı görünmez. Sıfır sonuç "başka yok" değil, **"bilinenle konuşan başka bulunamadı"**.

---

## 6. Açık kalanlar (altı turun da KAPSAMADIĞI)

- **Çalışma zamanı kapısı yok.** Çivi statiktir; `watchdog.parity_report`a bir
  `{"check": "pit_yasasi", ...}` satırı bağlanmadı. Bağlanırsa yasa panoda da görünür.
- **`dataset.py` sınıf kapsamında değil.** `finviz.discover_universe` oradan çağrılıyor ve evren
  seçimi karar-bitişiktir; `CANLI_KARAR_YOLU`ya eklemek `CANLI_TABAN`ı da etkiler, o yüzden ayrı
  bir karar olarak bırakıldı.
- ~~Karar eylemi kümesi elle.~~ **KAPANDI (§5.2, 2026-08-31):** karar adları
  `guard.classify_gate` sözleşmesinden türetiliyor; elle liste kaldırıldı ve ölü üç kaydı
  (`score`, `score_num`, `size_r`) ölçüm düşürdü.
- ~~Erken `return` bacağı türetilmiyor.~~ **KAPANDI (§5.3, 2026-08-31):** `strategy.scan_all`
  sözleşmesinden türetiliyor; erken `return` yalnız bir sinyal üreticisinin içindeyse karar sayılır.
- ~~İkinci kapı yüzeyi çivisiz.~~ **KISMEN KAPANDI (§5.4, 2026-08-31):** `KAPI_SOZLESMELERI`
  liste oldu ve `kapi_sozlesme_denetimi` iki yönlü tamlık kuruyor — bilinen vokabülerle konuşan
  kayıtsız bir kapı yüzeyi artık çiviyi öttürür. **Kalan boşluk:** tamamen yeni sabitlerle
  (`"BLOCK"` gibi) konuşan bir kapı görünmez.
- ~~`SINYAL_SOZLESMESI` tamlık çivisi YOK.~~ **KAPANDI (§5.5, 2026-08-31):** liste oldu ve
  `sinyal_sozlesme_denetimi` kapı tarafının birebir kardeşi olarak eklendi; asimetri kalmadı.
- **İki sözleşmenin de kapsam sınırı aynı ve çivili:** bilinen vokabüler / bilinen üretici
  dışında konuşan bir kapı ya da tarayıcı görünmez. Bu bir kusur değil, ölçülmüş ve beyan
  edilmiş sınır — ama kapatmak isteyen tur, ölçütü "sabit döndürmek" / "≥2 ad anmak"tan daha
  yapısal bir şeye (ör. çağrı grafiğinde emre ulaşabilirlik) taşımak zorunda.
- **Üretici kümesi ad-tabanlı.** `scan_all` demetine giren adlar `strategy.py`de tanımlı
  fonksiyonlarla kesiştiriliyor; başka bir modülden ithal edilen bir değerlendirici kümeye girmez.
- **Etki izlemesi tek sıçramalık.** `x = f(); y = x; if y:` biçimi görülmez; tohum yalnız çağrının
  DOĞRUDAN atandığı addır. `_tohumlar` kimlikle (`is`) eşleşir — sarmalayıcıdan geçen değer tohum
  sayılmaz (çivili).
- **Hedef adlar nitelenmemiş.** `days_since_report` gibi adlar modül kökünden bağımsız eşleşir;
  bir karar modülü aynı adla yerel fonksiyon tanımlarsa yanlış pozitif olur. Bugün çakışma yok ve
  `test_kayittaki_ad_ara_modulde_YEREL_DEGIL` çakıştığı gün öter.
- **`insider` / `short_interest` karar yüzeyine bağlanırsa** kayıttaki sınıfları `bilgi`den
  `karar_etkili`ye çekilmelidir; çivi bunu kendiliğinden fark etmez.
- **Kapsam `meridian/` ile sınırlı.** `ops/` ve `research/` altındaki ölçüm betikleri taranmıyor.
