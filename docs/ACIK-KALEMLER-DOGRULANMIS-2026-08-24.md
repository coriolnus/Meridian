# AÇIK KALEMLER — DOĞRULANMIŞ TEK LİSTE (2026-08-24)

**Operatörün sorusu:** "şu an bayat olmayan açık kalemler neler?"
**Yöntem:** her kalem önce doğrulandı, sonra ayrı bir ajanla KARŞIT doğrulandı (kapatmaya
çalışıldı). Bu belge yalnız **kanıtı yerinde duran** kalemleri açık sayar.
**Kapsam sınırı (önce oku):** bu sentez ajanına yalnız **WP1 (7 kalem)** ve **WP3 (3 kalem)**
cepheleri ulaştı; girdi paketi WP3'ün son kaleminin cümlesi ortasında **kesildi**. Kaç cephenin
daha koştuğu bu turda **ölçülemedi** (§5). Aşağıdaki sayımlar bu 10 kalem içindir, tahtanın
tamamı için değil.

> Bu belge **ROADMAP.md'ye dokunmaz.** §6 tahtaya işlenecek satırları hazır verir; tahtayı Rol-1 işler.

---

## 1 · TEK CÜMLE

Bana ulaşan **10 kalemin 8'i gerçekten açık** (biri — `13` — kısmen: A1 bacağı fiilen icrada,
A2/A3 açık), **2'si bayat-kapalı** çıktı (`B-PENCERE-KAYDIR`, `B-CHOP-BUTCE`), karşıt doğrulama
**hiçbirini çürütemedi (0)**, ve bugün **senden karar bekleyen kalem yok** — açık kalemlerin
dördü bugün başlanabilir HAZIR İŞ, üçü tek bir ölçüme (`EDG-042` K1 bandı) bağlı.

| sınıf | adet |
|---|---|
| gerçekten açık | 8 (biri kısmen) |
| bayat-kapalı (tahta yanlış gösteriyor) | 2 |
| karşıt doğrulamanın çürüttüğü | 0 |
| ölçülemeyen (girdi/erişim) | §5'te 6 madde |

---

## 2 · BAYAT OLMAYAN AÇIK KALEMLER — engele göre

### 2.0 · SENDE (operatör kararı) — **BOŞ**

Bu 10 kalem içinde bugün **hiçbir operatör kararı bekleyen kalem yok.** İki aday da düştü:
`B-PENCERE-KAYDIR` ve `B-CHOP-BUTCE` kararları **2026-08-23'te zaten verildi** (§3), `D5` ise
nominal olarak sende ama **kararı verdirecek kanıt henüz üretilmedi** — asıl engeli ölçüm, o
yüzden BLOKE grubunda (aşağıda). "Operatör bekliyor" diye bırakmak yanıltıcı olurdu.

### 2.1 · HAZIR İŞ — bugün başlanabilir, engeli yok  ← **en değerli grup**

> **GÜNCELLEME 2026-08-24 (Rol-1, ölçümle):** **H1 bir ARIZA DEĞİL — boyutu SIFIR.**
> `_defter_teyit_yamasi` ağaca 2026-08-22'de girdi (`55d72b3`); son reconcile turu
> **2026-08-21 20:32Z**, yani koddan BİR GÜN ÖNCE. Arada hafta sonu var, Pazartesi seansı da
> bu ölçüm yapılırken açılmamıştı. Damga hiç koşma fırsatı bulmamış. Üç rakip hipotez ölçümle
> elendi (yazım yolu DB'ye yönleniyor ✓ · sekiz satır `live_paper` damgalı ✓ · 7 günde sıfır
> `defter_teyit_yamasi_dusdu` ✓). Sekiz satırın hepsi `plan_id` taşıyor ve emir penceresinin
> (`en_eski 2026-07-14`, `kapsandi: True`) İÇİNDE — yani sonraki turda hepsi KESİN hüküm alır.
> **Yazılacak kod yok; bir reconcile turu bekliyor.** Sınanabilir öngörü + elenen hipotezler:
> `docs/TESHIS-2026-08-24-H1-BROKER-TEYIT.md`. Öngörü tutmazsa teşhis DÜŞER.
>
> Ayrıca bu tabloda **H2 · 20c · korunum-kovası-3 · K3 · K6 KAPANDI** (2026-08-24 turları):
> H2 short işaret sözleşmesi karta işlendi · 20c çift-bağ `goal.yaml`a girdi ve canlıya
> kopyalandı · korunum kovası `uyuyan_kurulum` ile kapandı (`unexplained` 6 → 0) · K3
> (EDG-055) ölçüldü ve HÜKÜM YOK ile kapandı · K6 (Ö-39) `plan_atif.jsonl` ile kapandı.
> Geriye **H3** (13-A2 kartı) ve **H4** (`propose_virgin_knob` süzgeci) kalıyor.

| # | kalem | WP | somut kalan iş | boyut | kanıt |
|---|---|---|---|---|---|
| H1 | **`broker_teyit` damgası basılmıyor** (`Ö-54`/K2-K3 önündeki tek engel) | WP1 | Teşhis: `EXE-2026-007`/`Ö-52` dağıtıldığı hâlde damga neden defterde yok? Reconcile yolunu izle, damgayı beş satıra bas → `EDG-042` K2/K3'ün n'i 0'dan çıkar | orta | CANLI (ssh, salt-okuma, 2026-08-24, benim koşumum): `state/meridian.db` `trades` → `tot 893 · alpaca_fill_price dolu 5 · broker_teyit dağılımı {'None': 5}` (T00099-T00103'ün beşi de damgasız). Kart kill#3: teyitsiz satır kıyasa giremez → K2/K3 ölçülebilen n = **0** |
| H2 | **`EDG-042` short işaret sözleşmesi** (`Ö-54-ek`) | WP1 | Karta ölçüm-öncesi R-revizyonu (eşiklere DOKUNMADAN): "short kapatmada YÜKSEK dolum aleyhte = +"; sonra `research/olcumler/edg042_kosum_*/olcum.py` K2/K3 dönüşümünü `side`a koşullu yap + sentetik short satırla sına. Kabul edilebilir alternatif: karta kalıcı kill-şerhi ("motor short açmıyor; satır çıkarsa kart genişletilir") | küçük | `research/cards/EDG-2026-042-…yaml:39` işaret cümlesi yalnız LONG · aynı kart `:148` **kendi açık kalemini beyan ediyor** ("short satır çıkarsa reçete KARTSIZ genişletilemez (yeni açık kalem)") ve kapatan revizyon eklenmemiş · `edg042_kosum_2026-08-22/olcum.py:205-208` işareti **koşulsuz** negatifliyor (`side` dalı yok) · `meridian/broker.py:693` (benim okumam): `side` alanı "gelecekteki SHORT desteğine ayrılmıştır" → tetikleyici bugün YOK, kalem **latent koruma** |
| H3 | **`13-A2` stop-tetik dakika-testi kartı** | WP1 | `docs/TASARIM-13-INTRADAY-DOLUM-SOZLESMESI-2026-08-23.md` §3'teki parametrelerle ön-kayıt kartı yaz. **Karta beyanlı-sınır olarak girmeli:** EDG-052 ilk koşumunun arşiv uyarısı — bant-içi **9/30 (%30)**, IEX-tek-kaynak deseni; bu A2/A3'ü bloklayan bir sinyaldir | orta | `research/cards/` içinde 13-A2/A3 kartı **yok** (`EDG-2026-05x` serisinde yalnız 052 `TASARIM-13`e atıf yapıyor) · `research/cards/EDG-2026-052-…yaml` ilk-koşum notu: "bant-içi 9/30 (%30) … 13-A2/A3 için ciddi sınır" |
| H4 | **`propose_virgin_knob` canlı-params süzgeci** | WP3 | Tasarım belgesi var (`docs/TASARIM-VIRGIN-KNOB-SUZGECI-2026-08-22.md`), **kart yok, kod yok**: kart-önce ön-kayıt + `Ö-48` süzgecinin üç tüketim yüzeyine bağlanması + çivi | orta | Benim greplerim (2026-08-24): `hayalet_suzgeci` YALNIZ arama tarafında kablolu — tanım `meridian/reflect.py:967`, çağrılar **sadece** `:1090` (`propose_deterministic.explore`) ve `:1990` (`coordinate_descent_search`); `grep -rn hayalet meridian/hermes.py meridian/analytics.py` → **0 eşleşme**. Süzgeçsiz üç yüzey: havuz `analytics.py:2871` (`hic_onerilmemis_dugmeler`) · köprü `hermes.py:1273-1280` (`virgin_knobs()`) · istem `hermes.py:1432` + kanıt paketi `hermes.py:1083`. Kart yok (`grep -rli 'virgin\|bakir' research/cards/` → yalnız EDG-041 ve EXE-008, ikisi de başka konu). Çivi yok: `tests/test_hayalet_dugme_v263.py` yalnız `reflect.hayalet_suzgeci`i ve arama yüzeyini sınıyor (N7/N8), öneri yüzeyini **değil**. Tahta zaten H1 diyor: `ROADMAP.md:212` |

**Sıra önerisi:** H1 → (H3 ‖ H4) → H2. H1 tek başına iki kalemin (`Ö-54` K2/K3 ve dolaylı
`EDG-040-a`) girdisini açar; H2 latent (motor short açmıyor), en sona kalabilir.

### 2.2 · TAKVİM — örneklem/seans bekliyor, bugün yapılacak iş yok

| # | kalem | WP | somut kalan iş | boyut | kanıt |
|---|---|---|---|---|---|
| T1 | **`Ö-54` / `EDG-2026-042` gerçek friksiyon bandı** | WP1 | Haftalık `edg042-friksiyon-haftalik` fire'ını bekle (ilk anlamlı tekrar **2026-08-29**); eşik dolan kovada donmuş `olcum.py`nin hükümlü kolu koşar, hüküm karta yazılır | orta | kart `status: measuring` (`…042…yaml:97`) · `research/olcumler/edg042_kosum_2026-08-22/sonuc.json`: giriş `n=13, seans=4, esik_dolu=false, ci=null, medyan_bps=15.017`; çıkış-hedef/çıkış-stop `n=0` · CANLI (2026-08-24): E2 defteri **30 satır, son satır 2026-08-21** → 08-22'den beri yeni dolum YOK, K1 örneklemi değişmedi (eşik n≥30 ∧ ≥10 seans) |
| T2 | **`EXE-2026-003` gölge planlı kol** | WP1/WP3 | Pencere (≥40 planlı dolum / 20 seans) dolunca `research/olcumler/exe003_golge_kapsam_2026-08-22/olcum.py` AYNI betikle yeniden koşulur; hüküm Rol-1'de. Bugün koşmak K harcamaz ama hüküm de üretmez | küçük | kart `status: measuring` (`EXE-2026-003-…yaml:60`) · CANLI (benim koşumum, 2026-08-24): `wc -l intraday_shadow_planli_orders.jsonl` → **5** (08-22'deki 5 ile aynı, artmamış); silahlı kol `intraday_shadow_orders.jsonl` → **11** (sızıntı yok). Tempo: ~6 günde 5 dolum → 40 dolum ≈ 8+ hafta |
| T3 | **`13-A1` E2 dakika doğrulaması** (`EDG-2026-052`) — *kalemin açık yarısı A2/A3'te (H3)* | WP1 | Örneklem birikimini bekle (n=18<30, seans 8<10); **ayrıca** canlıda `dolum_ts`in ilk dolu satırı henüz gelmedi | küçük | kart `status: measuring` (`…052…yaml:39`) · alan kod olarak İNDİ: `meridian/loop.py:2635-2640` ve `:3055-3061` (`dolum_ts` + `dolum_ts_neden`) · CANLI (2026-08-24): E2 son satırında `dolum_ts=None` (defterde henüz dolu satır yok — kablo var, sinyal yok) |

### 2.3 · BLOKE — başka bir kaleme bağlı (üçü de aynı zincirde: **T1**)

| # | kalem | WP | somut kalan iş | boyut | kanıt |
|---|---|---|---|---|---|
| B1 | **`Ö-55` / `EDG-2026-043` friksiyon-koşullu limit** | WP1 | T1 bandı gelince: banttaki slip hücresini (15/25/35) verdict'ten oku, karta "HÜKÜM (okuma günü)" bölümünü yaz, B4'ü ya yeniden aç ya kalıcı kapanış adayı olarak taşı. **Karşıt doğrulamanın kapsam düzeltmesi:** okuma artık tek başına 043 değil, **043 + `EXE-2026-008` ORTAK turu** (`docs/KARAR-2026-08-23-YEDI-KARAR.md` K3: "üçüncü tekrar YALNIZ 042 bandı gelince, 043 askısıyla TEK TURDA") | küçük | `…043…yaml:77` `status: measured … HÜKÜM ASKIDA (okuma kuralı: … 042'nin gerçek friksiyon bandı gelmeden B4 hükmü OKUNMAZ — kill'de)` · altı Δ CI'sı da 0-içi (A: −7.260 · −5.784 · −1.301 / B: +3.962 · +3.771 · +2.319) · kartta ayrı "HÜKÜM" bölümü YOK · `EXE-2026-008-…yaml:44` `status: measured` |
| B2 | **`EDG-040`-(a) ACİL kaleminin okuması** | WP1 | Bağımsız yeni ölçüm **GEREKMİYOR** — T1'in CI'ı çıkınca reçete zaten yazılı: CI-alt>15 → karta "ACİL rakamla doğrulandı"; CI bandı [5,15]'i kesiyorsa hüküm yok; CI-üst<5 → "model muhafazakâr" şerhi + `ROADMAP.md:213` 🔴 damgası yumuşar. **Kartın şerhi okumayı K1 + K3'e BİRLİKTE bağlıyor** → H1 damga işi buna da girdi | küçük | `…040…yaml:80` `status: measured` (08-22 hükmü) · aynı kartın 2026-08-23 şerhi: "Bant, 042-K1 (giriş) + 042-K3 (stop) gerçek bantları geldiğinde birlikte yeniden okunur" · `ROADMAP.md:213`: (b) bacağı kapandı (`EDG-2026-046` `status: measured`), (a) için kapanış cümlesi YOK — "(a) ✅ KARTI YAZILDI: `EDG-2026-042`" yani (a) = T1'in kendisi |
| B3 | **`D5` limit-tavanı kararı** (nominal engel: operatör) | WP1 | Zincir bağlayıcı: T1 → B1 (043+008 ortak okuma) → **ancak o zaman** D5 anlamlı. Karar günü ya `state/goal.yaml` execution_v2 altındaki `limit_pct_cap`/`limit_atr_mult` değişir (tavan adayı 0,01) ya da §7'ye "D5: tavan DEĞİŞMEZ" hükmü yazılır | küçük | `state/goal.yaml:88-89` `limit_atr_mult: 100.0` / `limit_pct_cap: 0.04` — 2026-08-03'ün "bağlamaz" değerleri **aynen** duruyor (karar goal'a hiç yansımamış) · §7'de D5'i karara bağlayan satır YOK; üç ayrı yerde "park"/"operatörde": `ROADMAP.md:2501`, `:2946`, `:2956` (+ `:203`, `:241`) · **Karıştırma uyarısı:** `ROADMAP.md:1768`'deki "D5 sertleştirme ✅ İNDİ" **başka** bir D5'tir (git jeton birliği, v208) · **Yeni kayıt:** operatör 08-23'te de masaya oturdu ve D5'i açıkça park etti (`docs/KARAR-MASASI-2026-08-23.md` #3 · `KARAR-2026-08-23-YEDI-KARAR.md` K3 · `docs/FRIKSIYON-PROGRAMI-HARITA-2026-08-23.md:49`) — yani "operatör hiç bakmadı" okuması YANLIŞ olurdu |

> **Tahta hijyeni (Rol-1'e):** B1/B2/B3'ün üçü de T1'in türevi. Tahtada üç ayrı 🔴 satır olarak
> durmaları Ö-49 sınıfı **mükerrer tur** açtırır. Ya T1 altında alt-madde yapılmalı ya da her
> birine "türev — engeli `EDG-042` K1/K3 bandı" şerhi düşülmeli.

---

## 3 · BAYAT ÇIKANLAR — tahta açık gösteriyordu, kanıtla kapalı

| kalem | WP | tahtadaki bayat satır | kapanış kanıtı | kalan iş |
|---|---|---|---|---|
| **`B-PENCERE-KAYDIR`** (pencere 13:45'e kaydırma) | WP1 | `ROADMAP.md:2372` hâlâ "operatör kararı — … EVET derse kart-önce uygulanır" | (a) **Karar verildi:** `docs/KARAR-2026-08-23-YEDI-KARAR.md` K2 "EVET, 042-HAKEMLİ SÜRESİZ" · (b) **kart-önce kuralı yerine geldi:** `EXE-2026-009-…yaml:34` `status: registered` · (c) **kod indi:** `meridian/barclock.py:144` `ENTRY_WINDOW_ET_MIN = 9*60+45`, `:147` `_PENCERE_REJIMLERI`, `:150-153` `pencere_rejimi()`; kablolu — `loop.py:698/700/1490/2619`, `intraday_cycle.py:175` · (d) **CANLI (benim koşumum, 2026-08-24):** `/opt/meridian/meridian/barclock.py:144` → `9 * 60 + 45` · (e) tahta kendi içinde çelişiyor: `ROADMAP.md:174` zaten "§5'teki operatör-bekliyor BAYAT" diyor | Ölçüm/kod işi **YOK**. Yalnız tahta bakımı (§6) |
| **`B-CHOP-BUTCE`** (chop bütçe-kapalılığı) | WP3 | `ROADMAP.md:210` 🟠 "OPERATÖR KARARI BEKLİYOR" · `ROADMAP.md:2373` "operatör kararı (A / B / üçüncü yol)" | (a) **Karar verildi:** `KARAR-2026-08-23-YEDI-KARAR.md` K1 "KANITA BAĞLI AÇILIM … *Durum: SONUÇLANDI — NO-GO (Δ −18.266$, CI 0-içi) … @chop duraklatması yürürlüğe girer, canlanma yalnız yeni kartla*" (üçüncü yol) · (b) **kart ölçüldü:** `research/cards/EDG-2026-048-chop-tabani.yaml:40` `status: measured` · (c) **kod indi:** `meridian/config.py:272` `URETIMI_DURAKLATILAN_REJIMLER: tuple[str, ...] = ("chop",)` + `hermes.py` şema/istem/fail-closed bacakları · (d) `ROADMAP.md:2926` §7 kaydı: "K1 kararının kanıt kapısı kapandı" | **YOK** — kalem fiilen kapalı. Yalnız tahta bakımı (§6) |

---

## 4 · KARŞIT DOĞRULAMANIN ÇÜRÜTTÜKLERİ

**Boş.** Karşıt doğrulayıcı WP1'in beş "açık" iddiasının hepsini kapatmaya çalıştı ve **hiçbirini
çürütemedi**; beşi de kanıtla ayakta kaldı. Doldurmak için uydurma yapılmadı.

Çürütme olmadı ama **iki kapsam düzeltmesi** geldi (yukarıda işlendi):
1. `Ö-55`'in okuması artık tek başına 043 değil, **043 + `EXE-2026-008` ortak turu** (K3 hükmü).
2. `EDG-040`-(a)'nın okuması **K1 + K3'e birlikte** bağlı (kartın 08-23 şerhi) — yani H1
   (`broker_teyit` damgası) yalnız `Ö-54`'ün değil, B2'nin de önkoşulu.

---

## 5 · ÖLÇÜLEMEYENLER — ve neden

| # | ölçülemeyen | neden |
|---|---|---|
| Ö1 | **Kaç cephe (WP) daha koştu ve ne buldu** | Girdi paketi bu ajana **kırpık** ulaştı: yalnız WP1 ve WP3 var, WP3'ün üçüncü kalemi cümle ortasında kesildi ("…motor-yüzeyi süzgecini sınam"). WP2/WP4-WP7 hiç gelmedi — koşup gelmediklerini mi yoksa hiç koşmadıklarını mı bilmiyorum. **Bu belgenin sayımları 10 kalem içindir.** |
| Ö2 | **WP3 kalemlerinin karşıt doğrulaması** | WP3 paketinde `curutulen` bloğu **yok** (WP1'de var). WP3'ün üç kalemi tek-taraflı doğrulanmış olarak geldi; `propose_virgin_knob`u bu turda **kendim** greple doğruladım (§2.1/H4), `EXE-2026-003`ü **canlıdan** saydım (§2.2/T2), `B-CHOP-BUTCE`yi kart+kod+karar belgesinden teyit ettim (§3) — yani üçü de yerinde, ama şüpheci tur koşmadı. |
| Ö3 | **`propose_virgin_knob` süzgeçsizliğinin BÜYÜKLÜĞÜ** | Kabloların yokluğu ölçüldü (grep, §2.1/H4); "bugün kaç öneri bu yüzden çöpe gidiyor" ölçülmedi — bu bir ölçüm işi ve **kart-önce** kuralına tabi, bu tur salt-okuma. |
| Ö4 | **`broker_teyit` damgasının NEDEN basılmadığı** | Damganın yokluğu canlıdan ölçüldü (5/5 `None`); kök neden reconcile yolunu koşturmayı/izlemeyi ister — bu tur canlıya yazma ve birim tetikleme yasak. H1 tam olarak bu teşhis. |
| Ö5 | **`EXE-2026-009` pencere damgasının gerçekten basıldığı** | Canlı E2 defterindeki **30/30 satırda `pencere` alanı yok/None** — ama defterin son satırı **2026-08-21**, damga ise 08-23'te dağıtıldı. Yani bu bir kusur DEĞİL, **sıralama**: ilk gerçek sınama **2026-08-25 seansı**. 08-25'te de basılmazsa bu bir Ö-49-TERSİ vaka olur (tahta kapalı der, gerçek açıktır) → §6'da bekçi satırı var. |
| Ö6 | **`13-A1`in arşiv sinyalinin bugünkü hâli** | EDG-052'nin bant-içi %30 / IEX-tek-kaynak uyarısını **karttan okudum**, bu turda yeniden ölçmedim (arşiv karşılaştırması ölçüm koşumudur, kart kadansı haftalıktır). |

**Ölçüm notu (sonraki ajanlara — "dosya yok → ölçülemedi" tuzağı):** canlıda `state/trades.jsonl`
**YOK**; işlem defteri `state/meridian.db` `trades` tablosundadır ve friksiyon alanları
(`alpaca_fill_price`, `broker_teyit`) `extra_json` sütununun **içindedir**. Okumalarım
`file:…?mode=ro` ile yapıldı, canlıya tek bayt yazılmadı.

---

## 6 · TAHTAYA İŞLENECEK (Rol-1 için hazır satırlar)

**A · Bayat satırların üstüne düşülecek notlar**

1. `ROADMAP.md:2372` (§5, `B-PENCERE-KAYDIR`) — engel sütunu şununla değiştirilsin:
   `✅ H6 KAPANDI — karar 2026-08-23 K2 (EVET, 042-hakemli); kart EXE-2026-009 ön-kayıtlı; kod canlıda (barclock.py:144 ENTRY_WINDOW_ET_MIN = 9*60+45, canlıdan doğrulandı 2026-08-24). BEKÇİ: pencere damgası ilk kez 2026-08-25 seansında sınanır — o gün de basılmazsa Ö-49-TERSİ vaka aç.`
2. `ROADMAP.md:2373` (§5, `B-CHOP-BUTCE`) — engel sütunu:
   `✅ H6 KAPANDI — karar 2026-08-23 K1 (üçüncü yol); EDG-2026-048 measured/NO-GO (Δ −18.266$, CI 0-içi); kod indi: config.py:272 URETIMI_DURAKLATILAN_REJIMLER=("chop",) + hermes fail-closed bacağı.`
3. `ROADMAP.md:210` (§2 H0, chop bütçe-kapalılığı 🟠 satırı) — `🟠 OPERATÖR KARARI BEKLİYOR` damgası
   `✅ H6 (2026-08-23 K1 · EDG-2026-048 NO-GO)`'ya çekilsin, metin tarihçe olarak yerinde kalsın.

**B · Sınıf geçişleri / şerhler**

4. `ROADMAP.md:190` (`Ö-55`) ve `:213` (`EDG-040` ACİL) ve `D5` satırları (`:203`/`:241`) →
   her birine şerh: `[2026-08-24 doğrulama: TÜREV KALEM — tek engeli EDG-2026-042 K1 (ve 040 için K3) bandı; bağımsız iş İÇERMEZ. Ö-55'in okuması EXE-2026-008 ile TEK TURDA yapılır (K3 hükmü).]`
5. `ROADMAP.md:216` ve `:348` (`13` satırları) → `[2026-08-24 doğrulama: satır İKİYE bölünmeli — 13-A1 kart YAZILDI ve ölçüm koştu (EDG-2026-052 measuring, research/olcumler/edg052_e2_dakika_2026-08-23) = TAKVİM; 13-A2/A3 kartı YOK = HAZIR İŞ. "kart adayları Rol-1'de" (§7:2923) ve "kalan tasarım işi yalnız 13" ifadeleri BAYAT.]`
6. `ROADMAP.md:212` (`propose_virgin_knob`) → `[2026-08-24 doğrulama: H1 DOĞRU ve HAZIR İŞ — süzgeç hâlâ yalnız arama tarafında (reflect.py:1090/1990), öneri yüzeylerinde 0 eşleşme (analytics.py:2871 · hermes.py:1083/1273/1432); kart ve çivi yok.]`
7. `Ö-54` satırına (`ROADMAP.md:193`) yeni alt-kalem: `[2026-08-24: K2/K3'ün ÖNÜNDEKİ TEK ENGEL broker_teyit damgası — canlıda afp-dolu 5 satırın 5'i de damgasız (2026-08-24 ölçümü). EXE-2026-007 dağıtıldı ama damga defterde YOK → bu bir TEŞHİS kalemidir (HAZIR İŞ), takvim değil.]`
8. `Ö-54-ek` (short işaret sözleşmesi) tahtada **adlı satır** olarak yoksa açılsın: `HAZIR İŞ · küçük · latent (motor short açmıyor) · kaynak: EDG-2026-042 kartının kendi beyanı (:148)`.

---

*Kanıt kuralı: bu belgedeki her hüküm dosya:satır ya da komut+çıktı ile desteklenmiştir. "CANLI
(benim koşumum)" etiketli satırlar 2026-08-24'te salt-okuma ssh ile yeniden ölçülmüştür; diğerleri
girdi paketindeki doğrulama/karşıt-doğrulama çiftlerinden alınıp yerelde dosya:satır düzeyinde
teyit edilmiştir.*

---

# EK · TAM SAYIM — Rol-1 tarafından günlükten kurtarıldı (2026-08-24)

**Yukarıdaki belge 59 adayın yalnız 10'unu görüyor ve bunu §0'da dürüstçe beyan ediyor.
Sebep bu belgede DEĞİL, iş akışımdaydı:** sentez ajanına giden girdi `JSON.stringify(...).slice()`
ile kırpıldı ve 19 cepheden 17'si düştü. Aynı sınıf bu turda ÜÇÜNCÜ kez oldu (öğrenme teşhisi
ve gece raporu turlarında da). Tam veri iş akışının `journal.jsonl`ında duruyordu ve oradan
kurtarıldı — aşağısı **19 cephenin hepsidir**.

## SAYIM
| hüküm | adet |
|---|---|
| **GERÇEKTEN AÇIK** | **25** |
| **BAYAT-KAPALI** (tahta açık gösteriyor, kalem kapalı) | **20** |
| KISMEN (bir bacağı kapalı) | 14 |
| toplam doğrulanan | 59 |

## AÇIK KALEMLER — engele göre

### HAZIR İŞ (4) — bugün başlanabilir, hiçbir şey beklemiyor
| kalem | boyut | kalan iş |
|---|---|---|
| `Ö-54-ek` | küçük | `EDG-042`ye short işaret sözleşmesi (R-revizyonu, eşiklere dokunmadan) |
| `20c` | küçük | `goal.yaml`a slot↔`position_size_r` çift-bağ kaydı + çivi |
| `korunum-kovası-3` | küçük | `watchdog.conservation_report`e `uyuyan_kurulum` terminal sınıfı (EDG-049 hükmü indi, engel kalktı) |
| `K3/K6` | büyük | dün gece dosya çakışmasından koşulamadılar; **çakışma artık yok** |

### OPERATÖR (11) — sende
`D5` (tavan; ama önce ölçüm) · `M11-Ö10` (alan taraması kapsamı) · `B-FMP-PLAN` ·
`B-DELIST-KAYNAK` · `U6` (kart-K ↔ DSR `n_trials`) · `bars_intraday` retention (öneri 180g) ·
`15d` · `15c` · `insider-A6` (beş soru) · **`B-AJAN-TAVAN`** (tek satır) · **`B-AJAN-GIT`**

### TAKVİM (5) — yapılacak iş yok, örneklem bekliyor
`Ö-55` · `Ö-54/EDG-042` (29 Ağustos) · `Faz-5` örneklem (11/20) · `EXE-2026-003` (~8 hafta) ·
`eq_ayna` kanıtı (bugünkü seans turundan sonra bakılır)

### BLOKE (5) — başka kaleme bağlı
`EDG-040-a` (→ EDG-042) · `EDG-2026-055` (PIT derinliği) · `M2` (Rol-1 şema kararı) ·
`propose_virgin_knob` (kart-önce) · `L2` (→ EDG-058 sırası)

## BAYAT-KAPALI 20 — TAHTANIN BAKIM LİSTESİ
`B-PENCERE-KAYDIR` · `24h` · `WP7-40 (K5)` · `B-NOUS-BEYIN` · `BT-2` · `M11-Ö1` · `kart-lint` ·
`ARSENAL` · `B-CHOP-BUTCE` · `L3` · `L4` · `sprint-inactive` · `GOAL_FAILURE` ·
`B-ORACLE-TASIMA` · `26-3cift` · `F9/H3` · `registry-budama` · `B-OCI-BUCKET` ·
`B-DASH-CRED` · `B-RUNBOOK-KAPSAM`

Dün gecenin yedi bayat satırıyla birlikte **tahtanın toplam bakım borcu 27 satır.** Ölçülmüş
maliyeti soyut değil: dün gece iki ajan turu zaten kapalı kalemlere gitti.

## KISMEN 14 — bir bacağı kapalı, biri açık
`F8-A1A8` · `EDG-2026-053` · `B-FINVIZ-TOKEN` · `13` · `24b` · `EDG-2026-056` · `2D` · `20d` ·
`B-QC-LOGIN` · `B-FAZ6-KILIT` · `L1` · `25a/25c/25d` · `Ö-49-kalan` · `zaman-varsayimi`
