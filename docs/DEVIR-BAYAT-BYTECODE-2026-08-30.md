# Devir notu — `__pycache__`in kaynağın önüne geçmesi (2026-08-30)

> **ÖZET (tek paragraf).** `spec.loader.exec_module` yolu `__pycache__`e bakar ve zaman damgalı
> pyc'yi YALNIZ (tam-saniye mtime, bayt boyutu) çiftiyle doğrular; boyutu değiştirmeyen bir
> düzenleme aynı saniyede kalırsa BAYAT bytecode kaynağın yerine koşar. Depoda bu kalıbı taşıyan
> **37 çağrı yeri** vardı: 18 test + 19 üretim (18.'si rebase sırasında main'de DOĞDU — aşağı bak). Hepsi kaynaktan derlemeye çevrildi; gövde tek
> yerde (`ops/sasi_yukleyici.py`), iki bilinçli satır-içi istisnayla (taşınabilir skill betikleri).
> 12 çivi eklendi (`tests/test_bayat_bytecode_v334.py`), sürüklenme kapısı artık BOŞ cırcırdır.
> Üç provenans çapası ve iki kardeş özdeşliği bayt olarak korundu. Üretim DAVRANIŞI değişmedi
> (kod-nesnesi özdeşliği ölçüldü). **Açık borç: tam suite — Rol-1'de.**
>
> Bu not artımlı yazıldı (1.→8. kalem). Erken bölümlerdeki "üretim tarafı düzeltilmedi" ifadeleri
> 2026-08-30 kapanışında güncellendi; çelişki görürsen SONRAKİ bölüm geçerlidir.

**Dal:** `claude/happy-jones-f652d3` (worktree) · **DALINDA COMMIT'Lİ, main'e MERGE EDİLMEDİ** ·
**push YOK · dağıtım YOK, dağıtım önerisi YOK** (CLAUDE.md madde 2/5/8: merge+push Rol-1'in).
**VERSİYON:** çivi dosyası `v332` iken `v334`e alındı — main `test_bekci_brifingi_v332.py` ve
`test_bekci_tarama_v333.py` eklemişti, dizi çakışıyordu.

## Ne yapıldı — BİRİNCİ KALEM (test tarafı)
Faz 3 Görev 1 ajanının TEK dosyada bulduğu ölçüm-aracı kusuru, kalıbı taşıyan **15 test
dosyasında (17 çağrı yeri, 16 betik)** ölçüldü ve **tek paylaşılan yardımcıyla** kapatıldı.
Bu kalemde diff yalnız `tests/` altındaydı.

> Üretim tarafı O ANDA kapsam dışıydı; sonraki kalemlerde (3.-8.) operatör kararıyla o da
> düzeltildi. Aşağıdaki "yalnız tests/" ifadeleri BU kaleme aittir, turun tamamına değil.

**Kapsamın dürüst sınırı — 15 dosyanın 14'ü pozitif kontrolle ölçüldü.** Ölçülmeyen tek dosya
`test_replay_sweep_v277.py`: onun tek çağrı yeri `tmp_path` altında o test için üretilen geçici
bir dosyayı yükler. Orada bayatlık **yapısal olarak doğamaz** (her testin `tmp_path`i benzersizdir,
kalıcı bir `__pycache__` yoktur) — yani ölçüm atlanmadı, ölçülecek bir şey yoktu. Çağrı yeri yine
de yardımcıya çevrildi: kalıbın tek olması §B kapısının işleyebilmesinin önkoşuludur.

## Mekanizma (kök neden — tahmin değil, izole tekrarla doğrulandı)
`ops/` ve `research/olcumler/` betikleri paket olmadığı için testler onları dosya yolundan
yüklüyordu:

```python
spec = importlib.util.spec_from_file_location(ad, yol)
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)          # <-- KUSUR BURADA
```

`spec.loader` bir `SourceFileLoader`dır; `SourceLoader.get_code()` kaynağı derlemeden **önce**
`__pycache__/<ad>.cpython-3XX.pyc`e bakar. Zaman damgalı pyc'nin geçerlilik kontrolü **yalnız iki
alandır**: kaynağın **tam saniyeye kırpılmış** mtime'ı ve kaynağın **bayt boyutu**. Yani boyutu
değiştirmeyen bir düzenleme (`5`→`2`, `==`→`!=`, `<`→`>`) pyc'nin kaydettiği saniyenin içinde
kalırsa **bayat bytecode "geçerli" sayılır ve kaynak yerine o koşar**. Çakışma penceresi 1 sn'dir.

İzole tekrar (oyuncak modül, iki ayrı süreç): kaynak `VAL = 2` derken modül **`VAL == 5`**
raporladı. Bulgunun doğuş biçimi de tam budur — mutasyon boyutu değiştirmediği için geri yükleme
sonrası `diff` "özdeş" dedi, ama çivi mutasyonlu modülü ölçmeye devam etti.

## Ölçüm — kusur her dosyada gerçek mi? (pozitif kontrol, üç kollu)
16 `(betik, test dosyası)` çiftinin her birine **boyut-koruyan** bir mutasyon uygulandı: sütun-0'daki
bir `import` satırı, aynı uzunlukta `1/0` + boşluk ile değiştirildi. Bu mutasyon **yüksek seslidir ve
evrenseldir** — modülü kaynaktan çalıştıran her test `ZeroDivisionError` görür, o testin betiğin
hangi davranışını çivilediğinden bağımsız. Böylece *"test bunu zaten çivilemiyor"* ile *"test kaynağı
hiç görmedi"* karışmaz.

| kol | kurulum | beklenen |
|---|---|---|
| TABAN | dokunulmamış kaynak | yeşil; pyc başlığı (mtime0, boyut0) olur |
| **KONTROL** | mutasyon + mtime **ileri** | **kırmızı** olmalı — yoksa mutasyon o teste zaten görünmüyordur ve bayat kolun yeşili hiçbir şey kanıtlamaz |
| **BAYAT** | mutasyon + mtime0 **geri** | yeşil kalırsa **kaynak değil önbellek ölçülmüştür** |

mtime'ı geri vermek hile değildir: saniye çözünürlüğünün kendiliğinden ürettiği durumu
deterministik hâle getirir (yarış koşulunu ölçülebilir kılar).

**SONUÇ — ÖNCE:** kontrol kolunda **16/16 kırmızı** (mutasyon hepsine görünür). Bayat kolda
**15'i yeşil kaldı → KUSUR GERÇEK**.

| hüküm | n | betikler |
|---|---|---|
| **KUSUR GERÇEK** | **15** | `ops/`: `oneri_brifingi` · `alarm_backlog_digest` · `registry_olu_alan_budamasi` · `kart_endeksi_uret` · `olcum` · `plan_geri_doldur` · `runbook_uret` — `research/olcumler/`: `say_zincir` · `tara_emisyon` · `say_kart` · `pencere_altbant` · `korpus_uret` — ayrıca `deploy/oracle-a1/aylik_bucket_kopya` · `skills/…/recommend` · `skills/…/orchestrate_edge_pipeline` |
| **ÖLÇÜLEMEDİ** | 1 | `skills/trading-skills-navigator/scripts/build_retirement_digest.py` |

**ÖLÇÜLEMEDİ'nin nedeni (uydurma yasağı — "kusur yok" YAZILMADI):** onu koşturan testler bu ağaçta
artefakt kapısından atlanıyor (`1 passed, 22 skipped`), yani betik hiç yüklenmiyor — pyc dosyası bile
doğmadı. Kontrol kolu da yeşil olduğu için ölçüm ayırt edemez. Kalıbı taşıyan yardımcı (`_load`) aynı
dosyada `recommend.py` üzerinden zaten **KUSUR GERÇEK** hükmü almıştır; düzeltme ikisini de kapsar.

## Düzeltme — tek yardımcı, 15 yama değil
`tests/conftest.py::betikten_modul_yukle()` — kaynağı **`compile()` ile burada derler**, yani
`__pycache__`i **ne okur ne yazar**. Yazmaması da şart: yazsaydı, aynı betiği ham kalıpla okuyan bir
başkası için tuzağı düzeltmenin kendisi kurardı.

17 çağrı yeri (15 dosya) bu yardımcıya çevrildi. Korunan davranışlar:
- `spec_from_file_location` **kalır** — `__file__`/`__name__`/`__spec__` doğru olmalı (`ops/`
  betikleri yollarını `Path(__file__)`den türetir). Spec **kurmak** önbelleğe dokunmaz; dokunan
  `loader.exec_module`dur ve o artık çağrılmıyor.
- `sys.modules` kaydı **varsayılan kapalı**, açık isteyen iki çağrı yeri (v121, v126) açıkça açar.
  Bu bir tercih değil önkoşul: `ops/olcum.py`nin başlığı kayıtsız yüklemeye **ölçülerek** bağlıdır.
- `dont_inherit=True` — CPython'ın kendi yükleyicisiyle aynı
  (`_bootstrap_external.SourceLoader.source_to_code`, satır 1059-1060). **Bu bayrak ilk taslakta
  yoktu ve gözden geçirmede yakalandı:** varsayılan `False` ile derlenen betik `conftest.py`nin
  yürürlükteki `__future__` ifadelerini miras alır. Bugün conftest'te öyle bir ifade yok — yani
  davranışsal bir çivi bugün iki hâlde de yeşil olurdu, hiçbir şey ölçmezdi. Kırılma biri conftest'e
  `from __future__ import annotations` eklediği gün doğar ve 15 betiği birden sessizce vurur;
  üstelik hedeflerden biri (`ops/olcum.py`) ertelenmiş tiplerin kendisini ölçüp karşı karar
  vermiştir. Bu yüzden bayrak **sözleşme çivisiyle** (§A5) çakıldı.

## Çiviler — `tests/test_bayat_bytecode_v334.py` (§A/§B: 7 çivi; §C ile birlikte 12)
TDD sırası tutuldu: çivi **önce** yazıldı, yardımcı yokken kırmızıydı.

| çivi | ne diyor |
|---|---|
| §A1 | **pozitif kontrol** — bu yorumlayıcıda bayat bytecode gerçekten koşabiliyor mu? Kırmızıya dönerse §A2'nin yeşili boştur; ölü pozitif kontrol sessiz kalmaz |
| §A2 | **çekirdek** — tuzak kuruluyken yardımcı kaynağı görmeli ("bayat bytecode koşarsa bu test kırmızı olur") |
| §A3 | yardımcı pyc **yazmıyor** |
| §A4 | dunder'lar korunuyor; `sys.modules` sızmıyor |
| §A5 | `compile(..., dont_inherit=True)` sözleşmesi (AST ile okunur) |
| §B | **sürüklenme kapısı** — `tests/` altında ham `exec_module` **çağrısı** yasak |
| §B2 | §B'nin tarayıcısı çalışıyor mu (gerçek çağrıyı görür, düzyazıyı görmez) |

**§B neden AST, neden `grep` değil — ölçülmüş:** ilk hâli düz metin taramasıydı ve `conftest.py`de
kusuru **anlatan** iki düzyazı satırını suçlu saydı. Yasağı anlatan cümle yasağın kurbanı olur —
bu deponun tekrar eden tuzağı (`codelaw`'ın "çapa satır değil SEMBOL" notu; 2026-08-29 hayalet-çapa
vakası). Çağrı ile çağrıdan söz etmeyi yalnız ayrıştırıcı ayırır.

**Yeni çivilerin negatif kontrolü** (çivi yük taşıyor mu?): `dont_inherit=True` silindiğinde §A5
**kırmızı**; ham kalıp bir test dosyasına geri sokulduğunda §B **kırmızı**. İkisinde de dosyalar
sha256 ile geri yüklendi.

## Ölçüm — DÜZELTMEDEN SONRA (tuzak **elle kurulu** iken)
Düzeltmeden sonra yardımcı pyc üretmediği için "önce" yöntemi zayıflar: *"bayat bytecode koşmadı"*
ile *"ortada bayat bytecode yoktu"* aynı görünür. Bu yüzden ayrı bir ölçüm koşuldu: `py_compile` ile
**orijinal kaynaktan, (mtime0, boyut0) başlıklı, geçerli görünen bir pyc** diske yazıldı; sonra
kaynak boyut-koruyan biçimde mutasyona uğratılıp mtime0 geri verildi. Yani **diskte, mutasyonlu
kaynak için "geçerli" sayılacak bayat bir bytecode dururken** test koşuldu.

**SONUÇ — SONRA: 15 DÜZELDİ · 1 ÖLÇÜLEMEDİ (aynı betik, aynı neden).** Onbeşinde de test kırmızı
verdi ve kırmızının sebebi `ZeroDivisionError` idi — yani mutasyonu **kaynaktan** gördü.

İki vakada (`recommend.py`, `orchestrate_edge_pipeline.py`) ölçüm aracının *tuzak kanıtı* alt
süreci `AttributeError` verdiği için hüküm otomatik olarak "ÖLÇÜLEMEDİ"ye düşmüştü; elle
kapatıldı: mutasyon modülün **ilk yürütülebilir satırını** `1/0` yapar, dolayısıyla kaynak koşsaydı
istisna zorunlu olarak `ZeroDivisionError` olurdu — başka bir istisna orijinal bytecode'un koştuğunun
kanıtıdır (tuzak kuruluydu), ve testin kendisi `ZeroDivisionError` ile kırmızı verdi.

**Bir vaka önce "HÂLÂ KUSURLU" göründü ve bu ölçüm aracının yanılgısıydı** —
`build_retirement_digest.py`de bayat pyc kuruluyken test yeşil kaldı, ama "sonra" aracına kontrol
kolu koymamıştım. Kontrol kolu ayrıca koşuldu (mutasyon + mtime ileri + pyc silinmiş): **test yine
yeşil**. Yani yeşilliğin sebebi bayat bytecode değil, betiğin hiç koşturulmaması. Hüküm: regresyon
YOK, ÖLÇÜLEMEDİ.

## Test durumu

**(a) Etkilenen 15 dosya + yeni çivi dosyası** — sayılar tabanla birebir aynı (17·29·68·30·12·35·
1+22·24·16·59·20·85+23·16·17 ve çivi dosyası 7/7).

**(b) 98 dosyalık doğrulama kümesi** (conftest'i anan + `tests/` dizinini tarayan + codelaw +
etkilenenler birleşimi). İKİ KEZ koşuldu — ikincisi, `conftest.py` artık modül düzeyinde
`ops.sasi_yukleyici` ithal ettiği için (TÜM suite için yeni bir sert bağımlılık):

```
1. koşum (test tarafı düzeltmesi):   1 failed, 2193 passed, 69 skipped in 712.30s (0:11:52)
2. koşum (üretim tarafı + §C):       1 failed, 2198 passed, 69 skipped in 710.33s (0:11:50)
3. koşum (KAPANIŞ — 19/19 çevrildi): 1 failed, 2198 passed, 69 skipped in 715.21s (0:11:55)
```
1→2 farkı +5: yeni §C çivileri. 2→3 farkı YOK — beklenen, çünkü aradaki değişiklikler
(edg042 ×2, devam.py, replay_sweep, iki skill betiği) test sayısını değiştirmez.

**KIRMIZI LİSTESİ DÖRT ÖLÇÜMDE DE BİREBİR AYNI, TEK DÜĞÜM:**
`test_uiux_s1b_v154.py::test_t3_diskteki_belge_kaynakla_ayrismamis` — değişiklik ÖNCESİ tabanda,
1., 2. ve 3. koşumda. Yani bu turun eklediği kırmızı YOKTUR.

**TEK KIRMIZI — BU TURDAN ÖNCE DE KIRMIZIYDI:**
`test_uiux_s1b_v154.py::test_t3_diskteki_belge_kaynakla_ayrismamis` — üretilmiş `docs/RUNBOOK.md`
main'de bayat. Değişiklik yapılmadan ÖNCE alınan tabanda da aynı düğüm kırmızıydı; kırmızı listesi
öncesi ve sonrası **birebir aynıdır (1 = 1, aynı düğüm adı)**. Bu turun işi değil (başka bir dalda
`5d4e455` "Üretilmiş RUNBOOK tazelendi" ile ele alınmış görünüyor).

**Neden 83 dosya için ayrıca taban gerekmedi:** onlar ŞU AN yeşil. Yeşil bir test bu değişiklikle
bozulmuş olamaz; taban karşılaştırması yalnız KIRMIZILAR için gerekir ve tek kırmızının tabanı
ölçülmüştür.

## AÇIK KALAN — Rol-1'e
1. **TAM SUITE BORCU.** `ops/etkilenen_testler.sh` bu diff için **"TAM SUITE GEREKLİ"** diyor,
   gerekçesi `tests/conftest.py`nin küresel erişimli olması. Tam suite bu worktree'de koşulmadı ve
   koşulmamalıydı: CLAUDE.md madde 6 gereği tek-otoriter suite **Rol-1'in ana checkout'unda, donmuş
   ağaçta** koşar (worktree'de `state/` boş, ~65 kırmızı koddan bağımsız doğar).
   **Yerine ne koşuldu:** conftest'i anan + `tests/` dizinini tarayan + codelaw + etkilenen
   dosyaların birleşimi — **98 dosya / 2268 test, ÜÇ KEZ** (11:52 · 11:50 · 11:55), her üçünde de
   yeni kırmızı YOK (bkz. "Test durumu"). Bu bir ikame DEĞİL, kapsam daraltmasıdır; otoriter koşum
   hâlâ borçtur. Kapsanmayan yüzey: suite ~7180 test, yani bu küme yaklaşık **üçte biridir**.
   **Riskin gerçek büyüklüğü:** conftest değişikliği **tamamen eklemedir** (2 stdlib ithali + 1
   ithal-yeniden-dışavurumu; gövde `ops/sasi_yukleyici.py`de). Hiçbir fikstür, `addopts` ya da
   autouse davranışı değişmedi — seçicinin gerekçe olarak saydığı iki şey de bunlardır.
   **SEÇİCİ 2026-08-30'da İKİ KEZ SORULDU, hükmü değişmedi** (çıkış 1). `--yollar` ile conftest
   dışarıda bırakılınca bile ad-eşleşmeli küme ~150 dosyaya çıkıyor: `olcum.py` → `olcum` bu
   depoda JENERİK bir jetondur (tek başına 398 test dosyasının 79'unu çeker). Yani seçici burada
   anlamlı bir azaltma sunmuyor; kaçış yolu değildir.
2. ~~**ÜRETİM TARAFI — düzeltilmedi**~~ → **KAPANDI** (operatör kararıyla, 3.-8. kalemler):
   19 üretim çağrı yerinin **19'u** kaynaktan derlemeye çevrildi. Ayrıntı aşağıdaki bölümlerde.
3. **Önceden var olan ölü ithaller (bu turun ürünü DEĞİL, kapsam dışı bırakıldı).** Dokunduğum
   dosyalarda üç kullanılmayan ithal var ve üçü de `HEAD`de de kullanılmıyor:
   `test_brifing_kadansi_v327.py:28 pytest` · `test_triyaj_duzeltmeleri_v274.py:28 pytest` ·
   `test_uiux_s1b_v154.py:25 ast`. Silmek diffi bu turun konusunun dışına taşırdı.
4. **`__pycache__` artıkları — tehlike sınıfı KÜÇÜLDÜ ama sıfırlanmadı.** Bu turun koşumları
   `ops/`, `research/olcumler/*/`, `skills/*/`, `deploy/oracle-a1/` altında pyc üretmişti; ölçüm
   betiklerinin ürettikleri silindi, boş `__pycache__` dizinleri temizlendi (hepsi `.gitignore`da).
   Artık NE testler NE de düzeltilen 19 üretim çağrı yeri bu betikler için pyc okuyor/yazıyor.
   Diskte kalan eski pyc'ler ise ancak NORMAL `import` yoluyla yüklenen modüller için (ör.
   `ops.replay_sweep`) devrededir — bu, CPython'ın olağan davranışıdır ve bu turun kapsamı
   dışındadır.
5. **`check_pre_trade_discipline.py`'nin ÖLÜ HEDEF YOLU** (8. kalemde bulundu, bilerek
   dokunulmadı): hedefi `skills/trader-memory-core/…` diye hesaplıyor, dosya ise
   `skills/_emekli/trader-memory-core/…` altında. Yolu düzeltmek ŞU AN ölü olan bir kapıyı
   CANLIYA çevirir — davranış kararıdır, Rol-1'e aittir; yükleyici düzeltmesinin yan etkisi olamaz.

---

# ÜRETİM TARAFI — 19 ÇAĞRI YERİNİN ÖLÇÜMÜ (2026-08-30, ikinci kalem)

**Hüküm: 19 çağrı yerinin 17'si KUSUR GERÇEK · 2'si ÖLÇÜLEMEDİ · şu an CANLI bayat pyc YOK.**
BU ÖLÇÜMDE hiçbir üretim kodu değiştirilmedi ve hiçbir üretim betiği ÇALIŞTIRILMADI.
(Düzeltme sonraki kalemlerde geldi — o zaman da betikler koşturulmadı.)

## Önce bir düzeltme: 20 değil 19
Bu notun ilk hâli "20 çağrı yeri" diyordu. `grep` sayısıydı ve içine `ops/olcum.py:111`
girmişti — orada `exec_module` bir ÇAĞRI değil, kalıbı ANLATAN bir docstring cümlesidir.
Yani bu turun kendi §B çivisi için yazdığım tuzağa (düzyazıyı çağrı sanmak) devir notunu
yazarken ben düştüm. AST ile sayım: **19**.

## Yöntem — neden test tarafındaki probe kullanılamadı
Testlerde probe "testi koş, mutasyon yakalandı mı" idi. Burada koşum YASAK: bu betikler
`meridian`e ve `state/`e uzanır, depo yasası pytest dışında onları çalıştırmayı yasaklar.

Çözüm: kusurun yaşadığı adım `exec_module` değil, onun İÇİNDEKİ `SourceLoader.get_code()`tur —
`__pycache__`e bakan, geçerlilik kontrolünü yapan ve kod nesnesini döndüren adım budur.
`get_code()` kodu ÜRETİR ama ÇALIŞTIRMAZ. `exec_module` = `get_code()` + `exec()`; ilki ölçüldü,
ikincisi hiç yapılmadı. Yani tam olarak kusurlu adım, sıfır yan etkiyle ölçüldü.

Tuzak kuruldu (orijinalden `py_compile` + boyut-koruyan mutasyon + mtime0 geri), sonra
`get_code()`un döndürdüğü kod nesnesi `marshal` imzasıyla iki adaya karşı karşılaştırıldı.
**NEGATİF KONTROL her hedefte koşuldu:** pyc silinince aynı probe MUTASYONLU imzayı döndürdü —
yani probe kör değil. (Kör olsaydı hüküm ÖLÇÜLEMEDİ olurdu.)

## Sonuç

| hedef | çağrı yeri | hüküm |
|---|---|---|
| `research/olcumler/edg032b_tamsatir_2026-08-13/olcum.py` | **13** | **KUSUR GERÇEK** |
| `research/olcumler/edg042_kosum_2026-08-22/olcum.py` | 1 | **KUSUR GERÇEK** |
| `research/olcumler/edg042_kosum_2026-08-29/olcum.py` | 1 | **KUSUR GERÇEK** |
| `research/olcumler/edg043_friksiyon_limit_2026-08-22/olcum.py` | 1 | **KUSUR GERÇEK** |
| `skills/_emekli/edge-candidate-agent/scripts/candidate_contract.py` | 1 | **KUSUR GERÇEK** |
| `skills/trader-memory-core/scripts/thesis_store.py` | 1 | ÖLÇÜLEMEDİ — **hedef dosya YOK** |
| `<dinamik>` `enjeksiyon_modulu_yukle(yol)` | 1 | ÖLÇÜLEMEDİ — yol çağıranın parametresi |

**TEK NOKTADAN 13 ÖLÇÜM:** on üç çağrı yeri AYNI dosyayı yükler — donmuş referans şasi
`edg032b_tamsatir_2026-08-13/olcum.py`. O tek dosya için bir kez bayat pyc doğarsa **on üç ölçüm
betiği birden** yanlış referansla koşar ve `sonuc.json` doğru görünür. Test tarafındaki kusur
"yeşil test yalan söyler" idi; burada karşılığı **"ölçüm sayısı sessizce yanlış olur"**dur ve
onu yakalayacak bir çivi yoktur.

**YAN BULGU — ayrı bir kusur, bytecode ile ilgisiz:**
`check_pre_trade_discipline.py:394` hedefi `parents[2]/"trader-memory-core"/…` diye hesaplıyor,
yani `skills/trader-memory-core/scripts/thesis_store.py`. Dosya orada YOK; gerçek yeri
`skills/_emekli/trader-memory-core/…`. Yani **CANLI bir skill, emekliye ayrılmış bir skill'in
dosyasına, artık var olmayan bir yoldan** işaret ediyor — o yükleyici hiç başarılı olamaz.

## Şu anki maruziyet — tuzak kurulu mu?
Depodaki **505 `.pyc`** tarandı: 400'ü pytest'in assertion-rewrite ürünü (ayrı sınıf,
kıyaslanmaz), 105'i geçerli ve kaynağıyla aynı. **ŞU AN bayat servis edilen pyc YOK.**
Yani bu latent bir tehlikedir; bugün üretilmiş bir ölçüm sayısının yanlış olduğu iddiası
YAPILAMAZ ve yapılmıyor.

> ARACIN KENDİ HATASI, KAYDA GEÇİYOR: bu taramanın ilk sürümü **405 "CANLI BAYAT"** dedi ve
> hepsi uydurmaydı. İki sebep: (a) pytest'in yeniden yazdığı pyc'ler kaynağın düz derlemesinden
> TASARIM GEREĞİ farklıdır; (b) `co_filename` kod nesnesine gömülüdür, benim mutlak yolla
> derlemem diskteki ile bu tek alanda ayrışıyordu. Düzeltilip yeniden koşuldu. Bu turun teması
> aracın kendi bütünlüğüydü; araç iki kez beni de yanılttı (bu, ve "HÂLÂ KUSURLU" yanılgısı).

## Önkoşul gerçek mi? — boyut-koruyan düzenleme bu depoda oluyor mu
Kusur iki şart ister: (1) boyutu değiştirmeyen bir düzenleme, (2) pyc'nin kaydettiği saniyenin
içinde kalmak.

**(1) ÖLÇÜLDÜ — depo tarihindeki 1116 `.py` değişikliğinin 18'i (%1,6) BOYUT-KORUYANDIR.**
Ve rastgele dağılmıyorlar, TOPLU dönüşümlerde patlıyorlar: `a81a3dd7` ("§-atıf çevrimi") tek
commit'te **dokuz dosyayı** aynı uzunlukta ikamelerle değiştirmiş; `e992d43e` aynı işi
`meridian/` için yapmış. Aynı-uzunlukta toplu metin ikamesi bu deponun tanıdık bir işidir.
Bu 18'in hiçbiri henüz kırılgan 17 hedeften birine düşmedi — sınıf gerçek, o dosyalarda henüz
ateşlemedi.

**(2) Git'ten ölçülemez** (mtime çalışma-ağacı olgusudur, checkout onu yeniden yazar). Ama
ampirik kanıt zaten var: **Faz 3 Görev 1 bulgusunun kendisi**, iki şartın birlikte
gerçekleştiği ölçülmüş bir vakadır.

---

# ÜÇÜNCÜ KALEM — edg032b ŞASİSİ DÜZELTİLDİ (2026-08-30, operatör kararı: kapsam 1+2)

Operatör iki seçeneği birlikte seçti: **on üç çağrı yerinin tamamı** düzeltilsin **ve** koruma
kapısı eklensin. Şasi dosyasının kendisine DOKUNULMADI.

## Şasi neden düzenlenemez (ölçüldü, karar değil olgu)
`research/olcumler/edg032b_tamsatir_2026-08-13/olcum.py` sha256'sı
`75cef79215a7404f386517678df3d264d65d671ad23734a0b6559427177c85da` — ve bu bir PROVENANS
ÇAPASIDIR: `edg057_leading_sector_2026-08-24/RAPOR.md` "Kasa" satırında anılır,
`edg032c_kunye_tazeleme_2026-08-24/RAPOR.md` onu künyedeki `sasi.sha256` alanına karşı DOĞRULAR.
Diskteki değerle birebir tutuyor. Bir bayt değişirse iki rapor birden yalan söyler. Bu yüzden
düzeltme YÜKLEYİCİ tarafındadır; şasi `git status`ta YOKTUR.

Buna karşılık **on iki çağıran betiğin kendi sha256'sı hiçbir yerde anılmıyor** (arandı) — yani
onları düzenlemek hiçbir provenans zincirini kırmaz.

## Ne değişti
**YENİ:** `ops/sasi_yukleyici.py` — tek gövde. `kaynaktan_yukle()` (genel) +
`referans_sasi_yukle()` (şasi deyimi). `compile()` ile kaynaktan derler; `__pycache__` ne okunur
ne yazılır.

**TEK UYGULAMA:** `tests/conftest.py::betikten_modul_yukle` artık gövde TAŞIMIYOR — buradan ithal
ediyor. Test tarafı ve üretim tarafı aynı gövdeyi çağırır; iki kopya iki sürüklenme yüzeyi olurdu.

**13 ÇAĞRI YERİ** (`ops/replay_sweep.py` + 12 `research/olcumler/*`): 10 satırlık kalıp tek çağrıya
indi. **argv/SystemExit dansı AYNEN korundu** — süs değil: şasinin `__main__` bloğu `sys.argv`e
bakar, `raise SystemExit(main())` desenindedir, ve argv geri verilmezse çağıranın argümanları yok
olur. §C2 üçünü de çiviler.

## ÖLÇÜLMÜŞ TUZAK — `ops.` ön eki başka bir checkout'a düşüyordu
`ops/replay_sweep.py` DOĞRUDAN koşuluyor (`.venv/bin/python ops/replay_sweep.py --kart …`,
`docs/ARAC-REPLAY-SWEEP-2026-08-23.md`). O durumda `sys.path[0]` kök değil **`ops/` dizinidir**, ve
`ops` ad-alanı paketi editable-install `.pth`i üzerinden **ana checkout'a** çözülür. Worktree'den
denendi: `ModuleNotFoundError` (ölçüldü). Ana checkout'ta ise hata vermez — sessizce ORANIN
kopyasını yüklerdi, yani bu turun kovaladığı sınıfın aynısı. Düzeltme: `referans_modul()` içinde
kök `sys.path`e önden eklenir (on iki kardeş betik bunu modül başında zaten yapıyor). İki bağlamda
da doğrulandı: yükleyici artık KENDİ checkout'undan çözülüyor.

## Çiviler (§C, beş yeni — TDD: önce kırmızı)
| çivi | ne diyor |
|---|---|
| §C1 | üretim yardımcısı da bayat bytecode'a bağışık (§A2'nin eşi) |
| §C2 | `referans_sasi_yukle` argv'yi şasinin yoluna çevirir, GERİ VERİR, `SystemExit`i yutar, `sys.modules`e sızmaz |
| §C3 | **CIRCIR:** üretimde ham `exec_module` yalnız `BEYANLI_KALAN` kalemlerinde olabilir (aşağı bak) |
| §C4 | **KORUMA KAPISI:** şasi sha256'sı sabit + pyc'si varsa kaynakla aynı |
| §C5 | **DAVRANIŞ ÖZDEŞLİĞİ:** yükleyicinin ürettiği kod nesnesi, CPython'ın `SourceFileLoader.source_to_code`unun aynı kaynaktan ürettiğiyle BAYT OLARAK aynı |

**§C5 neden gerekli:** depo yasası ölçüm betiklerini pytest dışında koşturmayı yasaklar, yani
"eskisi gibi davranıyor" DOĞRUDAN gösterilemez. §C5 dolaylı ama kesin kanıttır: aynı kaynaktan
CPython'ın üreteceği kod nesnesinin AYNISI üretiliyor — ve `source_to_code` `__pycache__`e hiç
dokunmaz, yani kanıt şasiyi çalıştırmadan ve diske iz bırakmadan alınır.

**Negatif kontroller (çiviler yük taşıyor mu):** şasi 1 bayt değişince §C4 KIRMIZI · `optimize=2`
eklenince §C5 KIRMIZI · ham kalıp geri sızınca §C3 KIRMIZI. Her denemede dosya sha256 ile geri
yüklendi; şasi `75cef79215a7404f`e döndü.

---

# DÖRDÜNCÜ KALEM — `edg042_kosum_2026-08-29` DÜZELTİLDİ

Ölçümün işaret ettiği ikinci öncelik: hedefler arasında **aktif düzenlenen tek dosya**
(4 commit, sonuncusu 2026-08-29), yani boyut-koruyan düzenleme önkoşuluna en yakın olan.

**Yine hedef değil ÇAĞIRAN düzeltildi, ve yine ölçüyle:** `edg042_kosum_2026-08-29/olcum.py`nin
sha256'sı `1dcb7708e592…` ve `edg042_recete_short_2026-08-24/ozdeslik.json` bu değeri kayda
geçirmiş. İki dosya BİREBİR aynı (doğrulandı) — `ozdeslik` iddiasının kendisi budur. Hedefi
düzenlemek o özdeşliği bozardı. Değişen tek dosya `pencere_altbant.py` (sha'sı hiçbir yerde
anılmıyor).

**Bu vakanın ironisi kayda değer:** çağrı yerinin ÜSTÜNDEKİ kendi yorumu şunu diyor — *"aynı
formülün ikinci bir kopyası yazılmaz (EQUIVALENT_TRUTHS sınıfı: iki kopya sessizce ayrışır)"*.
Yani `yuzdelik` formülü tek kopya kalsın diye ithal ediliyordu; ama ithal yolu `__pycache__`e
baktığı için **sessizce ESKİ bir sürümü** verebilirdi. Ayrışma, tam da engellenmek istenen yerde
doğardı.

`sys.path` eki burada da gerekliydi (aynı ölçülmüş tuzak: doğrudan koşumda `sys.path[0]` betiğin
dizinidir, `ops.` başka checkout'a düşer). İki bağlamda da doğrulandı.

**DOĞRULAMANIN SINIRI, açıkça:** bu dosyayı içe aktaran HİÇBİR test yok (arandı) ve depo yasası
onu pytest dışında koşturmayı yasaklıyor. Yani kanıt dolaylıdır: sözdizimi ayrıştırması · ölü
ithalin kalkması · `ops` çözümünün iki bağlamda da doğrulanması · hedefin bayt-özdeşliğinin
korunması · §C3 cırcırı. "Koşturuldu ve çalıştı" DENMİYOR.

## §C3 artık dar bir kapı değil, CIRCIR
Önceki hâli yalnız `edg032b_ref` yükleyen dosyalara bakıyordu — yarın BAŞKA bir dosyaya eklenen
kalıbı görmezdi. Yeni hâli `ops/` + `research/` + `skills/` envanterini tutar ve **iki yönde**
öter: (a) beyan edilmemiş YENİ bir çağrı yeri, (b) düzeltilmiş ama listede KALMIŞ kalem (bayat
muafiyet listesi, bir gün gerçekten gereken kırmızıyı da yutar). İkisi de negatif kontrolle
sınandı: YÖN 1 KIRMIZI · YÖN 2 KIRMIZI.

---

# BEŞİNCİ KALEM — `edg042_kosum_2026-08-22` DÜZELTİLDİ (kardeş özdeşliği geri geldi)

Aynı desen, aynı kısıt: hedef `edg042_kosum_2026-08-22/olcum.py` (`6d33a58cde6b…`) da
`ozdeslik.json`da anılıyor → DOKUNULMADI; yalnız `pencere_altbant.py` değişti.

**KARDEŞ ÖZDEŞLİĞİ — bir önceki turda BEN bozmuşum, bu turda kapandı.** İki `pencere_altbant.py`
(08-22 ve 08-29) BAYT OLARAK aynıydı (`8e8321b50f07…`). Dördüncü kalemde yalnız 08-29'u
düzeltince ayrıştılar. Beşinci kalem ikisini yeniden özdeş yaptı: **`986c5d84eeda7e2e…` =
`986c5d84eeda7e2e…`** (doğrulandı). Kayıtlı bir özdeşlik iddiası yoktu, ama iki kopyayı sessizce
ayrıştırmak bu turun kovaladığı sınıfın ta kendisidir — kendi işimde de geçerli.

**DOĞRULAMA BURADA GERÇEKTEN KOŞUYOR — dördüncü kalemden farkı budur.**
`tests/test_pencere_kaydirma_v272.py::_altbant()` bu dosyayı YÜKLER ve modül gövdesi koşar; yani
`sys.path` eki, `ops.sasi_yukleyici` ithali ve `kaynaktan_yukle(DIZIN / "olcum.py", …)` çağrısı
GERÇEKTEN çalıştırılır (modül düzeyindeki `yuzdelik = _olcum.yuzdelik` satırı yolun üstündedir —
kırılsaydı test ERROR verirdi). **48 passed.**

Ve iki dosya artık bayt-özdeş olduğu için, bu koşum 08-29'un kod yolunu da kanıtlar (tek fark
`DIZIN`dir ve o her dosyanın kendi `__file__`ından çözülür). Yani dördüncü kalemin "hiçbir test
onu koşturmuyor" boşluğu, beşinci kalemle DOLAYLI ama gerçek biçimde kapandı.

---

# ALTINCI KALEM — `edg043_friksiyon_limit_2026-08-22/devam.py` DÜZELTİLDİ

En basit vaka: `devam.py` hash-çapalı DEĞİL ve `sys.path` ekini zaten kendisi yapıyor, yani tek
değişiklik yükleme satırıdır. Ölü `import importlib.util` de düştü (dosyada `importlib` geçişi
artık 0).

**Bedeli neden burada özellikle somut:** `devam.py` bir KESİNTİ TELAFİSİ koşumudur ve iddiası
"aynı ölçüm devam ediyor"dur — motor sha zinciriyle iki yakayı bağlar. Yüklediği `olcum.py`
sessizce eski bir sürümden gelseydi, `M.motor_sha()` ve bütün hücreler o eski sürümden üretilir,
`sonuc.json` yine doğru görünürdü. Yani bayat bytecode tam da bu betiğin ÇÖZMEK için var olduğu
sorunu, fark edilmeden geri getirebilirdi.

Doğrulama sınırı (dördüncü kalemdeki gibi): bu dosyayı içe aktaran test YOK ve pytest dışında
koşturulamaz. Kanıt dolaylıdır — ayrıştırma · ölü ithalin kalkması · `ops` çözümünün doğrudan-koşum
bağlamında doğrulanması · §C3 cırcırı.

## YAN DOĞRULAMA — değiştirdiğim HER üretim dosyası provenans için tarandı
Beşinci kalemden sonra fark ettim ki çağıran betiklerin hash-çapalılığını yalnız **5 örnekte**
kontrol etmiştim; 13'ünün hepsini kontrol etmemiştim. Kapatıldı: değiştirdiğim her üretim
dosyasının **düzenleme ÖNCESİ** sha256'sı depoda arandı. **Hiçbiri anılmıyor** — tek "eşleşme"
bu devir notunun kendisi (08-22/08-29 kardeşlerinin eski sha'sını ben yazmışım). Yani hiçbir
provenans zinciri kırılmadı.

Aynı tarama ikinci bir kardeş çifti ortaya çıkardı: `exe006_limit_bacagi_2026-08-17/olcum.py` ve
`exe006b_o1_kimlik_2026-08-22/olcum.py` de bayt-özdeşti (`6a889b5c6fbf…`). Mekanik dönüşüm
tekbiçim olduğu için **özdeşlikleri korundu** (`afec52b5f45b…` = `afec52b5f45b…`, doğrulandı) —
edg042 çiftinde elle düzelttiğim ayrışma burada hiç doğmadı.

---

# YEDİNCİ KALEM — `replay_sweep::enjeksiyon_modulu_yukle` DÜZELTİLDİ

Ölçümde "ÖLÇÜLEMEDİ" kalan iki kalemden biri buydu: yol ÇAĞIRANIN parametresidir, sabit hedefi
olmadığı için `get_code` probe'u uygulanamadı. Kalıp aynıydı, düzeltmesi de aynı.

**RİSKİ ASLINDA EN YÜKSEK OLAN YÜKLEYİCİ BUYDU — ve sebebi yapısal.** Şasi DONUKtur (edg032b
2026-08-13'ten beri değişmedi); enjeksiyon modülü ise ölçümün DEĞİŞKEN parçasıdır: her kart için
yazılır ve kolları ayarlanırken tekrar tekrar düzenlenir. Yani "aynı saniye içinde boyut-koruyan
düzenleme" önkoşulu tam da burada, **düzenle-koş-düzenle döngüsünde** doğar. Üstelik hemen
altındaki arayüz kapısı bunu YAKALAYAMAZDI: `ZORUNLU_ARAYUZ` yalnız AD varlığına bakar
(`oz_sinama`, `kol_kimligi`…), bayat bytecode'da o adlar yerinde durur — **davranış** eskir.
Kapı geçer, ölçüm yanlış kolu ölçer.

**İki yükleyici tek çözücüye toplandı.** `ops/replay_sweep.py` içine `_sasi_yukleyici()` eklendi:
`sys.path` ekini ve `ops.sasi_yukleyici` ithalini tek yerde yapar, gerekçe tek yerde durur. Hem
`referans_modul` hem `enjeksiyon_modulu_yukle` oradan geçiyor — aynı yorumu iki kez yazmak, bu
turun kovaladığı sınıfın küçük bir örneği olurdu.

**BAYATLAYAN ANLATI DA TAZELENDİ.** Dosyanın kendi başlığı hâlâ *"edg032b şasisi **importlib ile**
modül olarak yüklenir"* diyordu — düzeltmeden sonra bu YANLIŞTI. Bu deponun tekrar eden sınıfı
(belge kaynaktan geride kalır) tam buydu; cümle kaynağa uyduruldu, ve ölü `import importlib.util`
düştü (dosyada `importlib` geçişi artık 0).

**Doğrulama:** bu yükleyicinin GERÇEK test kapsamı var —
`tests/test_replay_sweep_v277.py` onu üç yerde çağırıyor (`arayüzü EKSİK` negatif vakası + iki
pozitif kontrol). **32 passed.**

---

# SEKİZİNCİ KALEM — `skills/` altındaki son iki çağrı yeri · **PAYLAŞILAN YARDIMCI BİLEREK KULLANILMADI**

Bu ikisinde kalıbı körü körüne uygulamak REGRESYON olurdu; ölçüm bunu gösterdi:

**İkisi de KENDİ KENDİNE YETERLİ.** İthalleri yalnız stdlib + `yaml`; ne `meridian` ne `ops`
ithal ediyorlar, `sys.path`e de dokunmuyorlar. Ve `check_pre_trade_discipline.py` SKILL.md'de
`python3 skills/pre-trade-discipline-gate/scripts/check_pre_trade_discipline.py …` diye,
DOĞRUDAN çağrılıyor — yani `sys.path[0]` kendi dizinidir ve `ops.` ön eki çözülmez.
`ops.sasi_yukleyici` ithal etseydim, taşınabilir bir skill betiğini depo yerleşimine bağlar ve
onu **düzelttiği kusurdan daha kötü** bir biçimde kırardım.

**Karar: yerinde, satır-içi kaynak derlemesi.** Aynı iki satır (`compile(...) + exec(...)`),
`ops` ithali YOK. Yani bu turda ilk kez "tek gövde" ilkesinden BİLEREK sapıldı — gerekçesi iki
dosyanın da içine yazıldı. İki satırlık kopya, taşınabilirliği kırmaktan ucuzdur.

**Davranış korunuyor, ölçüldü:**
- `candidate_contract.py` için satır-içi derleme, CPython'ın `source_to_code`unun ürettiğiyle
  **BAYT OLARAK özdeş** kod nesnesi veriyor (çalıştırılmadan doğrulandı — §C5 ile aynı yöntem).
- `thesis_store.py` hedefi zaten YOK; `read_text()` `FileNotFoundError` verir — `exec_module`un
  bugün verdiğinin **aynısı**, ve çağıran (`link_reports`) onu zaten `except Exception` ile
  yakalayıp "review-required" uyarısına çeviriyor. Yani bozuk-yol davranışı bir bayt değişmedi.

**Kapsam sınırı:** bu iki betiği koşturan test YOK (arandı) ve `strategy_exporter.py` emekli bir
skill'in içinde. Kanıt dolaylıdır; "koşturuldu ve çalıştı" DENMİYOR.

## Cırcır artık BOŞ
`BEYANLI_KALAN = {}` — üretim tarafındaki **19 çağrı yerinin 19'u** kaynaktan derlemeye çevrildi.
Kapı bundan sonra saf cırcırdır: `ops/`, `research/`, `skills/` altında ham `exec_module` geri
gelirse ADIYLA öter. Boş listeyle negatif kontrol koşuldu: kalıp geri sızınca **KIRMIZI**.

**AÇIK KALEM (bytecode'dan bağımsız, bu turda kasten dokunulmadı):**
`check_pre_trade_discipline.py` hedefini `skills/trader-memory-core/…` diye hesaplıyor, dosya ise
`skills/_emekli/trader-memory-core/…` altında. Yolu düzeltmek şu an ÖLÜ olan bir kapıyı
CANLIYA çevirirdi — bu bir davranış kararıdır ve Rol-1'e aittir, yükleyici düzeltmesinin yan
etkisi olamaz.

---

## Bu turda dokunulmayanlar (bilerek)
`state/` yazılmadı · pytest dışında hiçbir ÜRETİM/ÖLÇÜM betiği koşturulmadı (`meridian.obs`
kirletilmedi; koşturulan tek şeyler ithal-çözümü probe'ları ve stdlib oyuncak modülleridir) ·
`monkeypatch.undo()` kullanılmadı · `dagit.sh`/`serve.sh`/`systemctl` koşulmadı · commit atılmadı ·
`meridian/` (canlı işlem motoru) hiç değiştirilmedi.

**Üç PROVENANS ÇAPASI bayt olarak korundu** (sha'ları raporlarda/künyelerde anılıyor):
`edg032b_tamsatir_2026-08-13/olcum.py` = `75cef79215a7404f…` ·
`edg042_kosum_2026-08-22/olcum.py` = `6d33a58cde6b…` ·
`edg042_kosum_2026-08-29/olcum.py` = `1dcb7708e592…`.
Ölçüm sırasında geçici mutasyona uğratılan HER dosya sha256 doğrulamasıyla geri yüklendi.
Değiştirilen 18 üretim dosyasının **düzenleme öncesi** sha'ları da depoda arandı — hiçbiri
provenans olarak anılmıyor (tek "eşleşme" bu notun kendisi).

**İki KARDEŞ ÖZDEŞLİĞİ korundu:** `edg042 pencere_altbant` çifti (`986c5d84eeda…`) ve
`exe006/exe006b olcum.py` çifti (`afec52b5f45b…`).

## Değişen dosyalar (37)

**YENİ (3)**
```
ops/sasi_yukleyici.py                  tek gövde: kaynaktan_yukle + referans_sasi_yukle
tests/test_bayat_bytecode_v334.py      12 çivi (§A mekanizma · §B/§C sürüklenme cırcırı)
docs/DEVIR-BAYAT-BYTECODE-2026-08-30.md
```

**ÜRETİM — 18 dosya, 19 çağrı yeri**
```
ops/replay_sweep.py                                   (2: şasi + enjeksiyon; + _sasi_yukleyici)
research/olcumler/edg032c_kunye_tazeleme_2026-08-24/olcum.py   ┐
research/olcumler/edg032c_taban_2026-08-22/olcum.py            │
research/olcumler/edg040_friksiyon_2026-08-22/olcum.py         │
research/olcumler/edg043_friksiyon_limit_2026-08-22/olcum.py   │ edg032b ŞASİSİNİ
research/olcumler/edg045_stop_slip_2026-08-22/olcum.py         │ yükleyen 12 betik
research/olcumler/edg046_secilim_2026-08-23/olcum.py           │ (13. çağrı yeri
research/olcumler/edg048_chop_tabani_2026-08-23/olcum.py       │  replay_sweep'te)
research/olcumler/edg049_dormant_2026-08-23/olcum.py           │
research/olcumler/edg057_leading_sector_2026-08-24/olc.py      │
research/olcumler/exe006_limit_bacagi_2026-08-17/olcum.py      │
research/olcumler/exe006b_o1_kimlik_2026-08-22/olcum.py        │
research/olcumler/exe008_limit_yeni_dunya_2026-08-23/olcum.py  ┘
research/olcumler/edg042_kosum_2026-08-22/pencere_altbant.py   kardeş çift
research/olcumler/edg042_kosum_2026-08-29/pencere_altbant.py   (bayt-özdeş)
research/olcumler/edg043_friksiyon_limit_2026-08-22/devam.py   kesinti telafisi
skills/_emekli/…/strategy_exporter.py                 satır-içi (paylaşılan yardımcı YOK)
skills/pre-trade-discipline-gate/…/check_pre_trade_discipline.py   satır-içi (aynı gerekçe)
```

**TEST — 16 dosya, 17 çağrı yeri**
```
tests/conftest.py                             (gövde ARTIK YOK; ops.sasi_yukleyici'den ithal)
tests/test_brifing_kadansi_v327.py (2)        tests/test_pencere_kaydirma_v272.py
tests/test_e_partisi_v278.py                  tests/test_renk_rolleri_v197.py
tests/test_firsat_yuzeyleri_v200.py (2)       tests/test_replay_sweep_v277.py
tests/test_k5_paketi_v273.py                  tests/test_skill_cleanup_v121.py
tests/test_kart_hijyeni_v279.py               tests/test_tipografi_rampa_v209.py
tests/test_kart_sozlesmesi_v198.py            tests/test_triyaj_duzeltmeleri_v274.py
tests/test_navigator_retirement_gate_v126.py  tests/test_uiux_s1b_v154.py
tests/test_olcum_araci_v328.py
```


---

# DOKUZUNCU KALEM — CIRCIR İŞ BAŞINDA: main'de DOĞAN 18. ÇAĞRI YERİ

PR açıldıktan sonra dal `origin/main`e rebase edildi (gerekçe aşağıda) ve ağaç main'in beş
commit'ini aldı. **§B çivisi anında kırmızı verdi:** `tests/test_spend_defter_duzeltmesi_v331.py`
ham `exec_module` kullanıyordu — ben bu turu koşarken main'de doğmuş, kalıbın 18. örneği.

Bu, kapının değerinin ölçülmüş kanıtıdır: sürüklenme teorik değil, **aynı gün** gerçekleşti.
Dosya paylaşılan yardımcıya çevrildi, ölü `importlib.util` ithali düştü. Cırcır yeniden BOŞ.

## Rebase neden gerekliydi (ayrı bir merge kusuru)
Dalın tabanı `cb0966b`, `origin/main`de **YOKTU**: Rol-1 aynı işi `5449a83` olarak yeniden
commit'lemiş. Yani merge-base `de5de29`ye düşüyordu ve PR, bana ait olmayan bir commit'i —
`docs/superpowers/plans/2026-08-30-faz3-bekci-profili.md`'nin **ESKİ** sürümünü (+120 satır) —
taşıyordu. Blob'lar farklıydı (`bb98dfa7` vs `07336faa`), yani merge main'in daha yeni
sürümünü GERİLETİRDİ. `git rebase --onto origin/main cb0966b` ile düşürüldü; PR artık tek
commit, 37 dosya, yabancı içerik yok.
