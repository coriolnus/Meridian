# ROADMAP BAKIM TURU — DENETİM KAYDI (2026-08-30)

**Operatörün cümlesi:** *"Roadmap'te çok fazla madde birikti, kapananlar arşive alınmadı, ve
birçoğunun durumu belirsiz durumda, açık kalemlerden kapanmış olabilecekler var, bayat kalemler
de olabilir — burayı düzenlememiz lazım."*

**Tek cümle:** Şikâyetin dördü de ÖLÇÜLDÜ ve üçü kapatıldı — §2 TAHTA'nın açık bölümlerindeki
48 satırın **25'i kapalıydı, 18'i hiç işaret taşımıyordu**; 49 tablo satırı + iki bayat banner
bloğu + iki operatör kovası + üç kapanmış öneri **metni değiştirilmeden** `§8` arşivine taşındı,
yerinde kalan her satır rozet aldı, ve tekrarı `tests/test_tahta_hijyeni_v337.py` ile çivilendi.

---

## 1 · YÖNTEM — ölçüm aracı deponun kendi kodu

Sayılar `meridian/api.py::_roadmap_ayristir` ile üretildi; yani **panonun `/api/roadmap` ucunun
tükettiği ayrıştırıcının ta kendisi**. Bu bilinçliydi: ayrı bir sayaç yazmak aynı gerçeğin ikinci
kopyasını doğururdu (tek-kaynak yasası) ve iki sayım sessizce ayrışırdı. Ayrıştırıcının kendi
sözleşmesi de aynen kabul edildi — özellikle şu cümlesi: **`belirsiz` = kalem işaret TAŞIMIYOR,
"açık" DEĞİL.** Bu tur "işaretsiz"i "açık" saymadı.

Koşum pytest içinden yapıldı (repo kuralı: pytest dışı koşum `meridian.obs`'a ulaşırsa canlı yerel
deftere yazar). Dönüşüm elle değil **betikle** yapıldı ve betiğin kendi kapısı üç iddiayı
doğrulamadan dosyayı yazmıyor:

1. taşınan her satır çıktıda **bayt-özdeş** bulunur (kayıp 0);
2. yerinde kalan satırlarda yalnız **ilk hücreye rozet** eklenir — ilk hücre eski metnini alt dizge
   olarak taşır, diğer hücreler bayt-özdeştir;
3. çıktıda beliren her yeni satır **beyan edilmiş** listede olmalıdır.

Kapı düşerse dosya yazılmaz. (Emsal: 2026-08-17 §-numaralandırma turu da dönüşümü betikle yapıp
kayıpsızlığı hash ile kanıtlamıştı.)

## 2 · ÖLÇÜM — önce / sonra

| ölçüm | satır | kapalı | açık | bloke | askıda | işaretsiz | çok-işaretli |
|---|---|---|---|---|---|---|---|
| **§2 açık bölümler** (H0/H1/H2/DİK) — ÖNCE | 48 | 25 | 0 | 1 | 3 | 18 | 1 |
| **§2 açık bölümler** — SONRA | 25 | 0 | 15 | 5 | 4 | 0 | 1 |
| §2'nin tamamı (H6 dahil) — ÖNCE | 68 | 30 | 0 | 1 | 3 | 33 | 1 |
| §2'nin tamamı — SONRA | 25 | 0 | 15 | 5 | 4 | 0 | 1 |

Belgenin tamamı: tablo satırı **166 → 188**, işaretsiz tablo satırı **113 → 101**, işaretli-açık
**0 → 23**, düzyazı maddesi **421 → 425**, satır **4626 → 4793**.

**BEDEL (bedel yasası — kazanç ölçüldüyse kayıp da ölçülür):** bu tur belgeyi **kısaltmadı, 167
satır uzattı.** Taşınan metin tam korundu, üstüne rozetler + kanıt blokları eklendi. Kazanılan
uzunluk değil **okunabilirlik**: tahtaya bakan bir tur artık 25 satır okuyor, 68 değil — ve
okuduğu 25 satırın hiçbiri kapalı değil. Kaybedilen: kapanmış kalemin gerekçesi artık tahtada
değil `§8.T`'de — "neden kapandı" sorusu bir sıçrama uzakta. Bu bilinçli bir takas.

## 3 · NE NEREYE TAŞINDI

| kaynak | ne | hedef |
|---|---|---|
| §2 başlığı | 2026-08-24 DOĞRULAMA TURU banner'ı (43 satır) | `§8.T`/A |
| §2 H1 üstü | 2026-08-24 gece karşıt-doğrulama notu (12 satır) | `§8.T`/B |
| §2 H1 | 5 kapalı satır + `23e` (kartı `measured`) | `§8.T`/C, D |
| §2 H2 | 2 kapalı satır — **bölüm boşaldı** | `§8.T`/E |
| §2 H0 | 16 kapalı satır | `§8.T`/F |
| §2 DİK DURUM | 5 kapalı satır | `§8.T`/G |
| §2 H6 ✅ | alt bölümün tamamı (20 satır) — tahtada arşiv durmaz | `§8.T`/H |
| §5 KOVA 1 | A1 `[B-KORUMA-KUR]` + A2 `[B-BILDIRIM-N1]` gövdeleri | `§8.O`/A |
| §5 KOVA 2 | B1 · B2 · B4 · B3 gövdeleri | `§8.O`/B |
| §4 havuz | `Ö-45` · `Ö-47` · `Ö-39` gövdeleri (havuzda tek satır iz kaldı) | `§8.H`/A-C |

**Neden §3'e dokunulmadı:** §3'ün özet tablosu kendi yetkisini zaten daraltmış durumda
(*"aşama bu tabloda değil §2 TAHTA'dadır; çeliştiğinde TAHTA yetkilidir"*) ve WP2'yi "kapanmış
cephe", WP10'u "borç yok" diye zaten işaretliyor. Gövdeleri taşımak devasa bir diff üretir ve
`meridian/` içindeki satır çapalarını kaydırırdı; kazancı yoktu. Ayrı bir tur işidir.

**Neden §6'ya dokunulmadı:** §6 bir kart indeksidir ve üreticisi (`ops/kart_endeksi_uret.py`)
`research/cards/README.md`'ye yazar — §6 o gerçeğin elle tutulan ikinci kopyasıdır. Elle
düzeltmek kopyayı tazeler ama sınıfı kapatmaz; ayrışma ölçülüp açık kalem olarak tahtaya yazıldı.

## 4 · "KAPALI" HÜKMÜNÜN KANITI — kalem kalem

Taşınan satırların çoğu **kendi metninde** zaten `H6 ✅ KAPANDI` diyordu; onlar için yeni bir
hüküm verilmedi, kendi hükümleri uygulandı. Metni "operatör bekliyor" derken kapalı olan ve bu
turda **depoya karşı yeniden doğrulanan** kalemler:

| kalem | kanıt (2026-08-30'da okundu) |
|---|---|
| `B-CHOP-BUTCE` / chop bütçe-kapalılığı | `meridian/config.py` `URETIMI_DURAKLATILAN_REJIMLER = ("chop",)` + `hermes.py` fail-closed bacağı |
| `B-PENCERE-KAYDIR` / `23e` | `meridian/barclock.py` `ENTRY_WINDOW_ET_MIN = 9*60+45`, yorumu "EXE-2026-009 + K2"; kart `EDG-2026-047` `measured` |
| `B-RUNBOOK-KAPSAM` | `ops/runbook_uret.py` `BETIK_KUMESI` üçlüsünde `dagit.sh` var |
| `F9` (dagit kapsamı) | `dagit.sh` `F9_LISTE` içerik kapısı kablolu (2026-08-23) |
| `H3` tur-2 | `deploy/oracle-a1/*/10-sertlestirme-faz1.conf` + `20-sertlestirme-faz2.conf` (seccomp) |
| `EDG-2026-044` havuz tavanı | kart `measured`, §7 2026-08-23: "aşama-1 ölçüldü — KART KAPANDI" |
| `Ö-39` | §7 2026-08-24 + `state/plan_atif.jsonl` |

## 5 · ÖLÇÜLEMEYENLER — ve neden (uydurma yasağı)

Bu tur **cloud klonunda** koştu. `state/` yereldir ve canlı A1 defteri okunamaz; tam suite de
Rol-1 kapısıdır ve koşmadı. Dolayısıyla "canlıda etkin mi" sorusu taşıyan üç kalem **yalnız depo
tarafından** doğrulandı ve öyle işaretlendi:

- `B-DASH-CRED` faz-2 — betik ve faz-1 drop-in'i depoda VAR; canlıda etkin olduğu ölçülemedi.
- `B-OCI-BUCKET` — `litestream_kur.sh` + aylık bucket birimi depoda VAR; replica'nın aktığı ölçülemedi.
- `B-NOUS-BEYIN` — 2026-08-24 denetimi "bayat-kapalı" dedi ama kapanışı canlı danışma yolunun diri
  olmasına bağlı. **Bilerek kapalı sayılmadı.** Ölçmeden kapatmak, bu turun düzelttiği
  `bayat-beyan` sınıfını ters yönde üretirdi.

## 6 · TURUN KENDİ ÜRETTİĞİ AÇIK KALEMLER (tahtaya yazıldı)

1. **`EXE-2026-009` P-2 + `EDG-2026-042` P-3** — 2026-08-29/30'da doğan iki **operatör kararı**
   hiçbir bölüme işlenmemişti; §2 H1'e ve §5 KOVA 2'ye satır olarak açıldı. (Kalıcı `B-…` kimliğini
   Rol-1 atar; bu tur kimlik uydurmadı.) `P-1` 2026-08-30'da kapandı (`90f6cdc` · `dcef1c6` · `83bc47b`).
2. **§7'nin 2026-08-30 boşluğu** — §7'nin en yeni girişi 2026-08-29'du; o tarihten sonra dokuz
   commit indi. Neden-kaydını Rol-1 yazar; satır onu kaybolmaktan korur.
   **[GÜNCELLEME 2026-08-31 — KAPANDI, operatör istedi:]** boşluk dokuz commit değil **24 tur**
   çıktı (`2701cf4`…`6dd38b5`; ilk sayım yalnız `git log --since` kuyruğuna bakmıştı ve 08-29
   öğleden sonrasını kaçırmıştı — sayı tarihiyle düzeltildi, silinmedi). 24 giriş §7'ye yazıldı,
   hepsi commit gövdelerinden TÜRETİLDİ ve blok başında **köken notu** taşıyor: girişlerin turların
   kendi anında değil sonradan yazıldığı gizlenmiyor. Yeni hüküm verilmedi; zaten kayıtlı iki tur
   (`177a92b`, `6b9c6ad`) tekrarlanmadı. Tahta satırı `§8.T`/I'ya taşındı.
3. **Ayrıştırıcı kelime-içi eşliyor** — `_roadmap_madde_durumu` dört kapanış imini sözcük sınırı
   olmadan arıyor; "chop BÜTÇE-KAPALILIĞI" bu yüzden kapalı ayrıştırılıyordu. **Hüküm tesadüfen
   doğruydu, ayrıştırma değil.** `meridian/` dokunuşu tam-suite kapısı ister → Rol-1.
4. **§6 kart indeksi diskle ayrışmış** — diskte 73 kart var, §6'nın kendi toplamı 50 diyor.
5. **Üç ROADMAP satır çapası zaten çürümüştü** (bu turdan ÖNCE ölçüldü, bu tur kırmadı):
   `meridian/watchdog.py` "ROADMAP :503" → §7 düzyazısına, `meridian/config.py` "ROADMAP:1476" →
   runbook-sıralama kalemine, `tests/test_korunum_uyuyan_kurulum_v283.py` "ROADMAP :1164-1188" →
   PF tartışmasına düşüyor. Üçü de **sembol** çapasına çevrilmeli (CLAUDE.md kuralı).
6. **Bir satır hâlâ çok-işaretli** — `M2` (açık) ile `M7` (kapalı) aynı satırda; tahtanın kuralı
   *"iki aşamadaysa kalem İKİYE bölünür"* der. Bölmek satır metnini değiştirmek demekti; bu tur
   kendini taşımayla sınırladı.

## 7 · ÇİVİ — ve ısırdığının kanıtı

`tests/test_tahta_hijyeni_v337.py` beş ayak çiviler: (A) tahtada kapalı satır yok · (B) tahtada
işaretsiz satır yok · (C) kapı boşa düşmüyor (tahtanın var olduğu ÖNCE ölçülür — yoksa iki iddia
boş kümede sessizce geçerdi) · (D) taşınanlar `§8.T`'de duruyor · (E) sentetik negatif kontrol.

**Yeşil doğru sebeple mi yeşil — üç mutasyon:**

| mutasyon | beklenen | ölçülen |
|---|---|---|
| arşivden bir kapalı satırı tahtaya geri koy | A kırmızı | `test_a_tahtada_kapali_satir_yok` FAILED, diğer 4 yeşil |
| açık bir satırın rozetini sök | B kırmızı | `test_b_tahtada_isaretsiz_satir_yok` FAILED, diğer 4 yeşil |
| `§8.T` başlığını yeniden adlandır | D kırmızı | `test_d_tasinanlar_arsivde_duruyor` FAILED, diğer 4 yeşil |

Üçünde de **yalnız hedeflenen ayak** düştü; yani ayaklar birbirinin arkasına saklanmıyor.

## 8 · KOŞUM SINIRI

Bu tur cloud klonunda koştu: `.venv` yoktu, `uv sync --extra dev` ile kuruldu. **Tam suite
koşmadı** (Rol-1 kapısı, ~26 dk). Koşan tek şey bu turun kendi kapsam testidir
(`tests/test_tahta_hijyeni_v337.py` — 5 passed) ve dönüşüm betiğinin kendi kayıpsızlık kapısıdır.
`meridian/` ve `ops/` altına **hiç dokunulmadı**; değişen dosyalar `ROADMAP.md`, bu belge ve yeni
çivi dosyasıdır.

---

# EK · 2026-08-31 — TAM BELGE DURUM DENETİMİ (operatör: *"bütün hepsinin durumunu kontrol etmek lazımdı"*)

**Haklı itiraz:** ilk tur yalnız `§2 TAHTA`ya odaklandı. Diğer bölümlerin durumu ölçülmemişti.
Bu ek o boşluğu kapatır: **428 işaretsiz kalemin tamamı** tek tek geçildi.

## E.1 · Yöntem — üç kova, ve hiçbiri tahmin değil

| kova | ne demek | ne yapıldı |
|---|---|---|
| **KALEM** | açılıp kapanan iş | depo/disk kanıtıyla rozet: `AÇIK` · `BLOKE` · `ASKIDA` · `KAPALI` |
| **KAYIT** | olmuş bir şeyin kaydı (bulgu, ders, keşif, günlük girişi, arşiv) | bölüm başına **beyan** düşüldü: rozetsizliği DOĞRUdur |
| **DOĞRULANMADI** | kalem ama bu turda ölçülemedi | `🟡 DOĞRULANMADI` + satırın kendi gerekçesi |

Üçüncü kova bilinçlidir: rozeti tahminle doldurmak, bu turun düzelttiği `bayat-beyan` sınıfını
ters yönde üretirdi. Bu tur **cloud klonunda** koştu; canlı defter ve `state/` okunamaz.

## E.2 · Bölüm bölüm sonuç

| bölüm | işaretsiz (önce → sonra) | hüküm |
|---|---|---|
| `§∞` eşleme | 9 → 9 | **KAYIT** — adres defteri, iş listesi değil (beyan düşüldü) |
| `§0` sözleşme | 13 → 13 | **KAYIT** — anayasa (beyan düşüldü) |
| `§1` hat | 7 → 7 | **KAYIT** — yaşam döngüsü kapıları (beyan düşüldü) |
| `§2` tahta | 18 → **0** | ilk turda kapandı |
| `§3` aktif WP | 70 → 40 | **35 rozet** (25 kanıtlı + 10 `🟡`), **30 KAYIT** (beyan düşüldü); WP özet tablosunun 11 satırı da rozetlendi |
| `§4` havuz | 17 → **0** | 8 gövde + 9 taşıma izi, hepsi kendi sınıflandırma etiketinden |
| `§5` operatör | 29 → 14 | 14 kanıt satırı + 3 kalem rozetlendi; 13 satır **ENVANTER** (beyan düşüldü); 1 `🟡` |
| `§6` kartlar | 43 → 9 | 41 satır **diskten** rozetlendi + indeks↔disk mutabakatı |
| `§7` günlük | 165 → 165 | **KAYIT** — kronolojik defter (beyan düşüldü) |
| `§8` arşiv | 75 → 75 | **KAYIT** — tanımı gereği tarihçe (beyan düşüldü) |

## E.3 · En ağır bulgu — `§6` kart indeksi 22 kart geride

Diskte **73 kart** var; indeksin kendi toplamı **50** diyor. İndekste hiç geçmeyen 22 kart
`EDG-2026-042`…`061` + `EXE-2026-008/009`, yani **2026-08-22 sonrası ölçüm dalgasının tamamı.**
Ayrıca `measuring` (4 kart) ve `judged` (2 kart) kovaları indekste **hiç yok**.

Bu tekrarlanan bir sınıf: 2026-08-17'de aynı kalem üç kart için açılıp kapatılmıştı. Kök neden
kartlar değil, **indeksin elle tutulması** — `ops/kart_endeksi_uret.py` üretilmiş indeksi
`research/cards/README.md`'ye yazıyor, `§6` onun türetilmeyen ikinci kopyası (**tek-kaynak yasası**).
Bu tur 22 kartı diskten ölçüp bloğa yazdı ve her satırın rozetini **karttan** okudu; indeksin
gövdesini elle tazelemedi — tazelemek sınıfı kapatmaz, bir sonraki dalgada aynı ayrışma doğar.

## E.4 · İkinci bulgu — WP özet tablosunun 6 satırı panoda "KAPALI" okunuyordu

`WP1` · `WP4` · `WP5` · `WP7` · `WP8` — beşi de **aktif cephe** — ayrıştırıcıda `kapali`
çıkıyordu, çünkü hücrelerinin düzyazısında "KAPANDI"/"KAPALI" kelimeleri geçiyor ve ayrıştırıcı
onları **sözcük sınırı olmadan** arıyor (aynı kusur `§2 H0`'da açık kalem olarak duruyor).
Rozet eklendikten sonra bu satırlar `çok işaretli` okunuyor — *yanlış* değil, **eksik**: okuyucuyu
hücreye bakmaya çağırıyor. Gerçek düzeltme `meridian/api.py`dedir ve tam-suite kapısı ister.

## E.5 · Ölçüm — belgenin tamamı

| | HEAD `6dd38b5` (denetim öncesi) | 2026-08-31 |
|---|---|---|
| düzyazı maddesi — işaretsiz | **307 / 421** | **266 / 450** |
| düzyazı maddesi — kapalı · açık | 105 · 9 | 161 · 21 |
| tablo satırı — işaretsiz | **113 / 166** | **66 / 188** |
| tablo satırı — kapalı · açık | 48 · 0 | 79 · 25 |

**Kalan 332 işaretsizin 322'si BEYANLI KAYIT'tır** (§7 günlük 165 · §8 arşiv 75 · §3 kayıtları 30 ·
§5 envanteri 13 · §0/§1/§∞ 29 · §6 artığı 9 + 1); **10'u `🟡 DOĞRULANMADI`** ve her biri nedenini
kendi satırında taşıyor. Yani belgede artık **denetlenmemiş kalem yoktur** — ya rozetli, ya
kayıt olduğu beyanlı, ya da ölçülemediği adıyla yazılı.
