# TASARIM-KANITI — `propose_virgin_knob` motor-yüzeyi süzgeci (Ö-48'in asıl tamiratı)

**Tarih:** 2026-08-22 · **WP:** 3 · **Aşama:** H0→H1 hazırlığı (kart-önce; KOD YOK, HÜKÜM YOK)
**Kaynak kalem:** ROADMAP §2 H0 satırı — "`propose_virgin_knob` canlı-params süzgeci (Ö-48'in asıl
tamiratı)" (ROADMAP.md:197). Ö-48'in kendisi 2026-08-22'de KAPANDI (ROADMAP.md:207): arama tarafı
`reflect.hayalet_suzgeci` ile kilitlendi; **öneri tarafı bu belgeye kadar AÇIK**.

Bu belge üç şeyi ölçer: (1) öneri katmanının bugünkü davranışı, satır satır; (2) Ö-48 süzgecinin
öneri katmanında YENİDEN KULLANILABİLİRLİĞİ (import yönü + döngü riski + lint sözleşmeleri —
ölçüldü, varsayılmadı); (3) tasarım seçenekleri + her birinin patlama yarıçapı (grep sayımlı) +
kartın karar vermesi gereken AÇIK SORULAR.

---

## 0. Vakanın kendisi (referans; bu belgede yeniden ölçülmedi)

- Keşif bütçesinin **%62'si (29/47 öneri)** o an canlıda taşınmayan iki düğmeye gitti:
  **21× `entry.w_turnover`**, **8× `regime.vix_backwardation_gate`** (ROADMAP §48 vakası).
- İki düğme de bounds.yaml'a **motor kablosundan GÜNLER ÖNCE** girmişti (2026-07-30/08-01;
  `tests/test_hayalet_dugme_v263.py` başlık ölçümü). Yani öneri anında ikisi de bugünkü katı
  tanımla HAYALETTİ; **bugün ikisi de kablolu** (bu turda yeniden doğrulandı:
  `meridian/strategy.py:498` → `_f(params, "entry.w_turnover", 0.0)`;
  `meridian/regime.py:298` → `params.get("regime.vix_backwardation_gate", 0)`).
- Bugünkü bounds: **32 anahtar / 32'si motor-okuyuculu — hayalet 0** (Ö-48 kapanış ölçümü,
  `meridian/reflect.py:909-911`). Yani tamirat bugün davranış DEĞİŞTİRMEZ; yarının regresyonunu
  keser — Ö-48 süzgecinin kendisiyle aynı konum.

---

## 1. BUGÜNKÜ DAVRANIŞ — öneri katmanı motor/params yüzeyine hiçbir noktada bakmıyor

### 1.1 Seçim havuzunun kaynağı: `analytics.dead_families()` (analytics.py:2826-2875)

```
hic = [k for k in sorted(config.bounds().keys()) if _knob_family(k) not in denenmis]
```

- `hic_onerilmemis_dugmeler` = **bounds anahtarları − defterde en az bir hipotez taşımış aileler**.
  Tek girdi `config.bounds()` ve `memory.all_hypotheses()`; **motor okuyucusu ya da canlı params
  kontrolü YOK** (analytics.py:2861-2863). %62 vakasının yapısal kökü bu satırdır: bounds'a giren
  her anahtar, hiçbir yüzey kontrolünden geçmeden "keşfedilecek bakir düğme" statüsü kazanır.
- `hic_onerilmemis_sayi` = `f"{len(hic)}/{len(tum)}"` — payda bounds'un tamamı (test çivisi var,
  bkz. §3 Seçenek B kısıtı).

### 1.2 Havuzun hermes'e taşınması: `_h2_families()` → `virgin_knobs()` (hermes.py:1240, 1262)

- `virgin_knobs()` adları H2'den alır ("YENİ SAYIM YOK" — hermes.py:1263-1264), her ada bounds
  SATIRINI (`min/max/step/type`) ve `strategy.yaml`'daki canlı değeri (`live`) iliştirir.
  Tek eleme: **ad bounds'ta yoksa** `hermes_virgin_knob_not_in_bounds` uyarısıyla düşer
  (hermes.py:1281-1289). Motor yüzeyi yine sorgulanmaz.

### 1.3 Deterministik öneri: `propose_virgin_knob()` (hermes.py:4331-4444)

Akış (ölçülen, satır satır):
1. `kn = virgin_knobs()` (4350) — boşsa `hermes_virgin_none` olayı + `None`.
2. State okunur (`load_strategy`/`bounds`/`goal`/hipotezler/aylık kota; 4356-4361) — okunamazsa
   `hermes_virgin_state_unreadable` + `None`.
3. H2 sırasıyla her bakir düğme için: bounds spec kontrolü → `_virgin_value` (aralığın orta
   noktası, adım ızgarasına oturtulmuş; orta nokta canlıyla no-op ise denenmemiş yarıya bir adım;
   o da no-op ise düğme `atlanan`a) → **`guard.validate_change` ÖN-DENETİMİ** (4373-4374; guard'a
   takılan ADIYLA atlanır — `rejected_by_guard` defter satırı üretmemek için, 4344-4348).
4. İlk geçen düğme öneri sözlüğü olur: `source="deterministic:virgin"`,
   `predicted_delta=reflect.GATE_MARGIN`, `confidence=0.35` sabit (4386-4416).
   Hiçbiri geçmezse `hermes_virgin_no_valid_candidate` + `None`.

**Süzgeç envanteri: bounds-üyeliği ✓ · no-op ✓ · guard ✓ · motor okuyucusu ✗ · canlı params ✗.**

### 1.4 Çağrı zinciri ve önerinin boru hattı

```
_reflect_once_govde (hermes.py:4556)
  → propose_with_llm() (4104) None dönerse
  → VIRGIN_FALLBACK (4301; env HERMES_VIRGIN_FALLBACK, varsayılan AÇIK)
  → propose_virgin_knob() (4586)
  → [bg turu ise D2 rejim-çivileme / ön-eleme; 4611-4643]
  → reflect.submit(proposal) (4646) → guard → OOS/probgate → versioning
```

Öneri bounds'a bir şey YAZMAZ — bounds'tan SEÇER; ship yolu `versioning.bump` üzerinden
`params`/`params_by_regime`'e yazar. Ship yetkisi değişmemiştir (h1b çivisi:
`test_hermes_audit_v28`; hermes reflect'i yalnız kapı yollarından çağırır — hermes.py:4383-4385).

### 1.5 KRİTİK ÖLÇÜM: süzülmemiş liste ÜÇ ayrı yüzeyden tüketiliyor — tamirat tek fonksiyon işi değil

| # | yüzey | yer | ne taşır |
|---|---|---|---|
| (a) | `propose_virgin_knob` havuzu | hermes.py:4350 | deterministik önerinin aday listesi |
| (b) | istem bölümü "(B) NEVER-PROPOSED KNOBS" | hermes.py:1421-1437 (`_exploration_sections`, `virgin_knobs()` çağrısı; `VIRGIN_IN_PROMPT=12`) | LLM'e bakir düğme ADLARI + ARALIKLARI + "prefer it" yönlendirmesi; **iki sağlayıcı yolunda da** user-prompt'a girer (1478, 1488) |
| (c) | kanıt paketi `dead_knob_families.never_proposed_knobs` | hermes.py:1072-1073 (`evidence_pack`) | LLM'e ham ad listesi (H2 karnesi) |

Üçü de aynı kaynağa iner: `analytics.dead_families()["hic_onerilmemis_dugmeler"]`.

**Vaka atfı için ölçülmüş çıkarım (sınırıyla):** bakir liste, aile İLK defter satırını aldığı an
o aileyi düşürür (analytics.py:2861-2862). Dolayısıyla **21× aynı düğme** deterministik bakir
yoldan tek başına ÇIKAMAZ (ilk kayıttan sonra düğme havuzdan düşer) — tekrar baskısının ana
taşıyıcısı (b)/(c) istem yüzeyleri ve/veya LLM'in serbest seçimi olmak zorundadır. SINIR: 47
önerinin üretici-başına dağılımı bu belgede yeniden ölçülmedi (kaynak damgası kırılımı ölçüm
kartının işi); "kaynak = yalnız `propose_virgin_knob`" cümlesi bu ölçümle kesinleşmemiştir.
Tamirat kapsamına (b)+(c)'nin girip girmeyeceği kartın sorusudur (§4 Q6).

---

## 2. Ö-48 SÜZGECİNİN YENİDEN KULLANILABİLİRLİĞİ — ölçüldü

### 2.1 Süzgecin parçaları (`meridian/reflect.py`)

| parça | satır | sözleşme |
|---|---|---|
| `MOTOR_ZINCIRI` | 916-917 | 10 modül: strategy, backtest, broker, guard, regime, loop, faz5_cikis, sieve, indicators, intraday_cycle |
| `_MOTOR_SABIT_CACHE` | 920 | `(dosya, mtime_ns)` demeti anahtarlı — kaynak değişmedikçe TEK AST taraması; hata asla önbelleklenmez |
| `_motor_sabitleri_olc()` | 923-957 | `(frozenset sabitler, None)` ya da `(None, neden)`; docstring'ler dışlanır |
| `motor_okunan_sabitler()` | 960-964 | rapor/teşhis yüzeyi (frozenset \| None) |
| `hayalet_suzgeci(bounds, kaynak)` | 967-1009 | `(temiz, hayalet)`; ÜÇ HÂL AYRIK: `[]`=temiz · `[..]`=süzüldü (+`reflect_hayalet_dugme_suzuldu` olayı, kümülatif sayaç) · `None`=ÖLÇÜLEMEDİ → **FAIL-OPEN** (+`reflect_hayalet_olculemedi`); bounds sözlüğüne/dosyasına dokunmaz |

İmza uyumu: `hayalet_suzgeci` herhangi bir `{anahtar: spec}` sözlüğü + serbest `kaynak` etiketi
alır — hermes'in `config.bounds()` çıktısıyla **değişiklik gerektirmeden** çağrılabilir. Mevcut
`kaynak` etiketleri: `"propose_deterministic.explore"` (reflect.py:1090),
`"coordinate_descent_search"` (reflect.py:1985).

### 2.2 Import yönü ve döngü riski — ÖLÇÜM

- **hermes → reflect kenarı ZATEN VAR ve modül-düzeyinde:** `meridian/hermes.py:38`
  (`from . import config, store, memory, reflect, ...`). `propose_virgin_knob` bugün bile
  `reflect.GATE_MARGIN` okuyor (hermes.py:4409). **hermes içinden `reflect.hayalet_suzgeci` /
  `reflect.motor_okunan_sabitler` çağrısı SIFIR yeni import kenarı demektir.**
- **reflect → hermes kenarı YOK:** reflect.py'de hermes import'u yalnız yorum/docstring'de geçer;
  tek yakın şey fonksiyon-içi `from . import hermes_composite` (reflect.py:1288) — ayrı modül.
  Döngü riski hermes tarafı için **ölçülüp sıfırlandı**.
- **analytics → reflect kenarı bugün YOK** (analytics.py:31 modül-düzeyi importlar: `store,
  config, score, health, memory`). Seçenek B bu kenarı YENİ açar. Ters yön `reflect → analytics`
  fonksiyon-içi olarak ZATEN VAR (reflect.py:1173, 1500) → yeni kenar, **zaten var olan 33 modüllük
  güçlü-bağlı bileşenin İÇİNDE** kalır (pyproject.toml sözleşme-4/5 notu, 2026-08-16 Tarjan ölçümü:
  analytics de reflect de listede). Modül-düzeyi zincir izlendi: analytics → reflect (modül-düzeyi
  importları reflect.py:34: config, store, guard, memory, versioning, backtest, dataset,
  oos_erosion, shadowlaw) → backtest → skills (backtest.py:53) → skills modül-düzeyi yalnız
  `config, store` (skills.py:38; analytics importu fonksiyon-içi, skills.py:460) — **bu yol
  üzerinde import-anı döngüsü ölçülmedi/bulunamadı**; yine de depo teamülü (reflect'in kendi
  deseni) fonksiyon-içi geç-import'tur ve o desen bu sınıfı tümden yok eder.
- **lint-imports sözleşmeleri (pyproject.toml:74-243, 5 sözleşme) tek tek okundu:**
  1. adapters yukarı-yön yasağı — ilgisiz (kaynak adapters değil).
  2. çekirdek-altyapı (store/storage/config/obs) yukarı yasağı — analytics/hermes kaynak listesinde
     DEĞİL; ilgisiz.
  3. saf yapraklar bağımsızlığı — ilgisiz.
  4. `api > scheduler > loop` katmanları — hermes/reflect/analytics bu katmanlarda değil; ilgisiz.
  5. `backtest > strategy > regime > guard > indicators` katmanları — hermes/reflect/analytics
     katman listesinde değil; **ANCAK bu sözleşme Seçenek D'yi öldürür** (aşağıda): guard →
     reflect kenarı, reflect'in modül-düzeyi `backtest` importu (reflect.py:34) üzerinden
     `guard → backtest` DOLAYLI zinciri kurar ve layers sözleşmesi dolaylıyı sayar
     (pyproject.toml:180-182 beyanı).
  **Beyan:** `lint-imports` KOŞULMADI (otoriter suite penceresi — koşum yasağına komşu alan;
  sözleşmeler statik okundu). Hüküm değil ölçüm-önizidir; kart H2'sinde temiz pencerede
  `lint-imports` koşumu doğrulama adımı olmalıdır.
- **Maliyet:** AST taraması `(dosya, mtime_ns)` önbellekli — aynı süreçte arama zaten koştuysa
  öneri katmanının çağrısı önbellekten döner (ek tarama 0). Öneri katmanı ayrı/taze süreçte ilk
  çağrı tek tam taramadır (10 dosya; arama tarafında halihazırda ödenen maliyetle aynı sınıf).

**Sonuç (ölçüm, hüküm değil):** aynı AST taraması öneri katmanından — hermes içinden — mevcut
import kenarıyla, sıfır yeni bağımlılıkla çağrılabilir. analytics içinden çağrı da mümkündür ama
YENİ (sözleşme-ihlalsiz, SCC-içi) bir kenar açar; teamül gereği fonksiyon-içi geç-import ister.

---

## 3. TASARIM SEÇENEKLERİ + PATLAMA YARIÇAPI (grep sayımlı)

Önce test yüzeyinin envanteri (grep, 2026-08-22):

| dosya | testteki `def test` sayısı | ilgili temas |
|---|---|---|
| `tests/test_hayalet_dugme_v263.py` | 10 | `reflect.hayalet_suzgeci`/`MOTOR_ZINCIRI`/`_motor_sabitleri_olc` adlarını çivileyen TEK dosya |
| `tests/test_uretec_kesif_dengesi_v135.py` | 27 | `propose_virgin_knob` 8 satır · `virgin_knobs` 1 · `dead_families` 4 · **kaynak-METNİ okuyan çivi** (l.395: `SRC.read_text().split("def propose_virgin_knob")` — yasak liste yalnız `versioning.bump`/`store.write_json`/`memory.record`/`walk_forward`) |
| `tests/test_hafta3b_v125.py` | 44 | `dead_families` 1 · **l.328 çivisi: `payda == len(config.bounds())`** (CANLI defter sınıfı, conftest.py:917-921 kayıtlı) · l.357 `never_proposed_knobs` paket zorunluluğu |
| `tests/test_gorunmez_suzgec_v247.py` | 19 | `propose_virgin_knob` yalnız monkeypatch→None (havuz değişikliğinden ETKİLENMEZ) |
| `tests/test_kovab_ogrenme_v162.py` | 24 | aynı — monkeypatch→None |
| `tests/test_ogrenme_otomasyonu_v136.py` | 28 | `exploration_share` teması |
| `reflect.submit` dokunan test dosyası | **17 dosya** | Seçenek F'nin yarıçapı |

Bugün hayalet=0/32 olduğundan **tüm seçenekler bugün davranış-nötrdür** — kırmızı riski davranış
değil ARAYÜZ değişikliklerinden gelir; sayılar buna göre okunmalı.

### Seçenek A — Tek boğaz: `hermes.virgin_knobs()` içinde süz (hermes.py:1262)

Bounds anahtarları listeye girmeden `reflect.hayalet_suzgeci(b, kaynak="hermes.virgin_knobs")`.
- **Kapsar:** yüzey (a) + (b) — ikisi de `virgin_knobs()`tan besleniyor. **(c)'yi KAPSAMAZ**
  (evidence_pack listesi `_h2_families`ten ham gelir; LLM hayalet ADLARINI paket üzerinden
  görmeye devam eder).
- **Import:** sıfır yeni kenar (§2.2).
- **Patlama:** v135 (27 test; havuz semantiği testleri — bugün hayalet 0 olduğundan sandbox
  fikstürleri hayalet içermedikçe yeşil kalır; l.395 metin-çivisi `virgin_knobs` gövdesini
  kapsamaz, güvenli). v247/v162 etkilenmez. v263'e dokunulmaz. v125 etkilenmez.
- **Karşı-ölçüm:** fail-open (`hayalet=None`) hâlinde `virgin_knobs`un dönüş sözleşmesine yeni
  bir beyan alanı gerekir mi (Q2)?

### Seçenek B — Kaynakta süz: `analytics.dead_families()` (analytics.py:2861-2863)

`hic` listesi kurulurken hayaletler ayrılır; üç yüzey (a)+(b)+(c) birden temizlenir.
- **SERT KISIT (ölçüldü):** `test_hafta3b_v125.py:328` paydayı `len(config.bounds())`e çiviler →
  `tum` bounds ile senkron KALMALI; süzüm yalnız `hic` listesine uygulanabilir ve dışlananlar
  **AYRI, BEYANLI bir alanda** taşınmalıdır (ör. `hayalet_dislanan: [...] | None`) — H2 bir
  KARNEDİR, sessizce küçültmek kendi başına bir bayat-beyan/uydurma sınıfı doğurur (Q4).
- **Import:** YENİ analytics→reflect kenarı (fonksiyon-içi geç-import; sözleşme ihlali ölçülmedi,
  SCC-içi — §2.2).
- **Patlama:** v125 (44 testlik dosyada 2 doğrudan H2 testi; alan EKLEME geriye-uyumluysa yeşil),
  v135 `dead_families` temasları (4), conftest kayıtları ad-değişmezse etkilenmez. Ayrıca
  `dead_families`in bu belgede sayılmayan DİĞER tüketicileri (api/selfreview/watchdog sınıfı —
  hermes.py:4426-4441 D1 gerekçesindeki envanter) alan ekleme karşısında taranmalıdır (Q4).

### Seçenek C — En dar: yalnız `propose_virgin_knob` döngüsünde atla (hermes.py:4363-4383)

Aday döngüsüne `motor_okunan_sabitler()` kontrolü; hayalet düğme `atlanan`a `"{var}:hayalet"`
etiketiyle düşer (guard ön-denetiminden ÖNCE — etiket taksonomisi bulanmasın, Q5).
- **Kapsar:** yalnız (a). §1.5 çıkarımı gereği tekrar baskısının ana taşıyıcısı büyük ihtimalle
  (b)/(c) olduğundan, tek başına vakanın gövdesini kapatmayabilir — bu bir hüküm değil, kartın
  ölçmesi gereken atıf sorusudur (Q6).
- **Import:** sıfır yeni kenar. **Patlama:** yalnız v135 (l.395 metin-çivisi yasak-listesi
  ihlal edilmiyor; `reflect.` çağrısı bloğa girse de yasak adlardan değil).

### Seçenek D — Guard kapısında reddet (`guard.validate_change`) — ÖLÇÜMLE ELENEN SINIF

- **Sözleşme-5 ihlali (ölçüldü):** guard → reflect kenarı, reflect.py:34'ün modül-düzeyi
  `backtest` importu üzerinden `guard → backtest` dolaylı zinciri kurar; layers sözleşmesi
  dolaylıyı sayar (pyproject.toml:180-182). AST çekirdeği yaprak modüle taşınmadan bu yol
  lint-imports'u kırar.
- **Yan etki (kodun kendi beyanı):** submit yolunda guard reddi deftere `rejected_by_guard`
  satırı yazar → düğme "denenmiş" olur ve bakir listesinden HİÇ ÖLÇÜLMEDEN düşer — tam olarak
  `propose_virgin_knob`un ön-denetim gerekçesinin uyardığı sınıf (hermes.py:4344-4348).
  Hayaleti guard'da reddetmek, hayaleti SESSİZCE "denenmiş"e çevirirdi.

### Seçenek E — AST çekirdeğini yaprak modüle çıkar; reflect/hermes/analytics oradan okusun

- Katmanlama en temiz uzun-vade biçim; D'nin sözleşme sorununu da çözer.
- **Patlama en büyük:** v263'ün 10 testi `reflect.hayalet_suzgeci`/`reflect.MOTOR_ZINCIRI`
  adlarını çivili tutuyor → re-export şimi şart; Ö-48 kapanış kaydının kimliği/atıfları
  (ROADMAP.md:207) taşınan adlara işaret etmeye başlar. Bugün (a)-(c) yüzeyleri A/B ile
  şimsiz kapanabildiği için bu seçenek "gerekmedikçe açılmaz" sınıfında not edilir.

### Seçenek F — Tüm kaynaklar için tek kapı: `reflect.submit` içinde kontrol

- Süzgeçle AYNI modülde (import maliyeti 0) ve LLM'in serbest seçimi dahil TÜM öneri
  kaynaklarını yakalar (istem süzgeci yönlendiricidir, bağlayıcı değildir — LLM süzülmüş isteme
  rağmen hayalet ad önerebilir).
- **Patlama en geniş ikinci:** `reflect.submit`/`search_and_submit`e dokunan **17 test dosyası**;
  ayrıca ret defter satırı üretme biçimi D'deki "denenmiş'e çevirme" tuzağına karşı ayrıca
  tasarlanmalı (ret sınıfı `rejected_by_guard`tan AYRI damga ister).

**Kapsam matrisi (özet):**

| seçenek | (a) havuz | (b) istem-B | (c) paket | LLM serbest seçim | yeni import kenarı | dokunan test dosyası (yaklaşık) |
|---|---|---|---|---|---|---|
| A | ✓ | ✓ | ✗ | ✗ | 0 | 1 (v135) |
| B | ✓ | ✓ | ✓ | ✗ | 1 (analytics→reflect, geç-import) | 2-3 (v125, v135) + tüketici taraması |
| C | ✓ | ✗ | ✗ | ✗ | 0 | 1 (v135) |
| D | — | — | — | ✓ | sözleşme-5 KIRAR | elenen sınıf |
| E | ✓ | ✓ | ✓ | (F ile birleşirse ✓) | yeni modül | 2+ (v263 şimli) |
| F | ✗* | ✗* | ✗* | ✓ | 0 | 17 |

*F üretimi değil kabulü süzer — istem/havuz kirliliği sürer; tek başına değil ancak A/B'nin
tamamlayıcısı olarak anlamlıdır.

---

## 4. AÇIK SORULAR (kartın cevaplaması gerekenler — burada HÜKÜM YOK)

- **Q1 — SINIF TANIMI (en kritik):** ROADMAP kalemi "canlı-params süzgeci" diyor; ölçülen tarihi
  mekanizma ise öneri anında "bounds-var/OKUYUCU-yok" idi (iki düğme kablodan önce bounds'a
  girmişti). Literal bir canlı-params süzgeci (`params.get(k) is None` → atla) **bakir yolun
  varlık amacını siler**: istem bölümü (B) `live=unset`'i açıkça ERDEM sayar ("wired but
  effectively off — proposing it turns a dormant mechanism ON", hermes.py:1431-1433) ve
  `entry.w_turnover` bugün bunun ders örneğidir (kablolu, varsayılan 0.0 = uyuyan terim;
  strategy.py:473-498). Kart tanımı seçmeli: okuyucu-tabanlı (Ö-48 AST — tarihi vakayı öneri
  anında yakalardı) mı, params-tabanlı mı, ikisinin bileşimi mi?
- **Q2 — FAIL-OPEN aktarımı:** arama tarafında `None`=ölçülemedi → süzme (fail-open). Öneri
  katmanında aynı hâl nasıl beyan edilir — `virgin_knobs`/öneri sözlüğü `hayalet=None` izini
  taşımalı mı (YASA 6: okuyucusu kim olur)?
- **Q3 — OLAY/SAYAÇ SAHİPLİĞİ:** `reflect_hayalet_dugme_suzuldu` adı ve süreç-içi kümülatif
  sayaç reflect'e aittir; öneri katmanı aynı olayı `kaynak="hermes.*"` etiketiyle mi kullanır,
  yoksa hermes-önekli ayrı olay mı? (Ortak sayaç katman ayrımını bulandırır mı?)
- **Q4 — KARNE DÜRÜSTLÜĞÜ (Seçenek B'nin şartı):** H2 karnesinden hayalet GİZLEMEK mi, İŞARETLEYİP
  göstermek mi? v125 l.328 payda çivisi + `never_proposed_knobs` paket zorunluluğu (l.357) beyanlı
  ayrı-alan biçimini işaret ediyor; `dead_families` tüketici envanteri (api/selfreview/watchdog
  sınıfı) alan-ekleme öncesi taranmalı.
- **Q5 — `atlanan` TAKSONOMİSİ:** hayalet atlaması guard ön-denetiminden ÖNCE ve AYRI etiketle
  (`{var}:hayalet`) mi? (Bugünkü etiketler: `bounds_yok`, `no_op`, guard nedenleri —
  hermes.py:4367-4378.)
- **Q6 — VAKA ATIFI ve (b)/(c)+LLM kapsamı:** 29/47'nin üretici-başına kırılımı (deterministik
  yol / LLM / arama) canlı defterden ölçülmeli (§1.5 sınırı). Kırılım LLM ağırlıklı çıkarsa
  tamirat A/B'siz C ile "yapılmış görünür ama vakayı kapatmaz" sınıfına düşer; LLM'in süzülmüş
  isteme rağmen hayalet önermesi ihtimali F'nin gerekip gerekmediğini belirler.
- **Q7 — KILL-LİSTE ADAYLARI (kart-önce):** (i) süzgeç bugünkü 32/32 kablolu evrende TEK bir
  gerçek düğmeyi süzerse tasarım geçersiz (yanlış-pozitif = aramadan düşürme; Ö-48'in kendi
  kuralı); (ii) fail-open hâli sessizleşirse geçersiz; (iii) H2 karnesi payda çivisi (v125:328)
  kırılırsa geçersiz.

---

## 5. Bu belgenin ölçüm sınırları (uydurma yasağı beyanı)

- `lint-imports` CANLI KOŞULMADI (otoriter suite penceresi); sözleşmeler pyproject.toml'dan statik
  okundu — koşum kartın H2 doğrulamasına bırakıldı.
- 29/47'nin üretici-başına kaynak kırılımı ÖLÇÜLMEDİ (canlı defter sorgusu ister; Q6'nın ölçüm
  kalemi). "Tekrar baskısı istem yüzeylerinden gelir" cümlesi yapısal çıkarımdır, defter sayımı
  değildir.
- Test sayıları `grep -c "def test"` iledir; hiçbir test KOŞULMADI (tek-otoriter suite kuralı).
