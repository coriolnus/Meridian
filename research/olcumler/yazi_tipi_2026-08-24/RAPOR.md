# YAZI TİPİ EDİNME + ÖLÇÜM TURU — 2026-08-24

**Kapsam.** Operatör 2026-08-24'te "yazı tiplerini internetten bul ve indir ilgili yere koy" dedi;
Dub tasarım sistemi **Inter + Geist Mono** kullanıyor. İndirme YAPILDI. Bu rapor indirilenin ne
olduğunu, aynı düzenekle ölçülen sayıları, 2026-08-07'nin donmuş kararıyla çatışmayı ve bağlanma
borcunu masaya koyar.

**Bu rapor hüküm vermez, sayı verir.** Hüküm operatörün.

> ### TABAN YENİDEN ÜRETİLDİ — ÖLÇÜM GEÇERLİ
> 2026-08-07'nin üç referans sayısı bu turun düzeneğinde **birebir** yeniden üretildi
> (Geist Mono 0,92 / 0,57 · Recursive Mono 1,00 / 0,817 · Recursive Sans 0/O 0,663).
> Ayrıntı ve şart: **§3**. Şüpheli ilan edilen bir sayı YOKTUR; ölçülemeyenler **§7**'de sayılıdır.

---

## 1 · NE İNDİRİLDİ

### 1.1 Kaynak paketler

| Ürün | Sürüm | Kaynak (resmî) | Paket sha256 | Paket bayt | Lisans | İndirilen yer |
|---|---|---|---|---|---|---|
| Inter | v4.1 (font içi 4.001, yayın 2024-11-16) | `github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip` | `9883fdd4…6b11e` | 33.707.794 | SIL OFL 1.1 | `edinme/inter/Inter-4.1.zip` |
| Geist Mono | v1.7.2 (font içi 1.700, yayın 2026-06-01) | `github.com/vercel/geist-font/releases/download/v1.7.2/geist-font-v1.7.2.zip` | `7fc800d2…b04e2` | 8.207.303 | SIL OFL 1.1 | `edinme/geist/geist-font-v1.7.2.zip` |
| *(ek keşif)* Satoshi | ITF/Fontshare paketi | fontshare.com | — | — | **ITF FFL v2.0 — kesit alma ADIYLA YASAK** | `satoshi/` (bkz. `satoshi/RAPOR.md`) |

Satoshi bu turun beş-yüz tablosunun dışındadır; buraya envanter dürüstlüğü için yazıldı.
FFL v2.0 subsetting'i yasakladığı için bu deponun kesit hattına **giremez**.

### 1.2 Ana dosyalar ve dağıtım adayı kesitler

| Rol | Dosya | sha256 | Bayt | Not |
|---|---|---|---|---|
| Inter kaynak | `fonts/Inter-VF.ttf` | `4989b125…0ccaf` | 879.708 | zip içi `InterVariable.ttf` ile bayt-aynı · upem 2048 · 2937 glif |
| Geist kaynak | `fonts/GeistMono-VF.ttf` | `0e1af3f5…d180d30` | 171.200 | zip içi `GeistMono/variable/GeistMono[wght].ttf` · upem 1000 · 1159 glif |
| **Inter kesit (aday)** | `woff2/inter-vf.woff2` | `465cab77…b9dab` | **38.720** (37,8 KB) | 644 glif · 278 kod noktası · `opsz` **14'e SABİT** · wght 400–700 |
| **Geist Mono kesit (aday)** | `woff2/geist-mono-vf.woff2` | `74200495…cc88a21` | **17.256** (16,9 KB) | 281 glif · 260 kod noktası · wght 400–700 |
| Inter lisansı | `lisans/Inter-OFL.txt` | `262481e8…4935a` | 4.380 | üst-kaynak `raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt` ile **bayt-aynı** |
| Geist lisansı | `lisans/GeistMono-OFL.txt` | `c683bfbc…c46c90` | 4.383 | üst-kaynak `…/vercel/geist-font/v1.7.2/OFL.txt` ile **bayt-aynı** |

**Bütçe.** Aday çift toplam **55.976 bayt = 54,7 KB**; kapı 120 KB
(`tests/test_yazitipi_v201.py::test_dagitim_boyutu_BUTCEDE`, satır 369-380).
Canlıdaki Recursive çifti 81.168 bayt = 79,3 KB. Fark **−25.192 bayt**.

### 1.3 Lisans hükmü (bağımsız doğrulandı)

| Soru | Inter | Geist Mono |
|---|---|---|
| Metinden OFL 1.1 mi (dosya adına dayanmadan) | EVET | EVET |
| Telif satırı | `Copyright (c) 2016 The Inter Project Authors` | `Copyright 2024 The Geist Project Authors` |
| Reserved Font Name ilan edilmiş mi | **HAYIR** → yeniden adlandırma kısıtı yok | **HAYIR** |
| `OS/2.fsType` | 0 = Installable Embedding | 0 |
| Kesitte makine-okunur lisans alanı (nameID 0/13/14) | KORUNDU | KORUNDU |
| Yayıncı sha256 / imza | **YOK** (v4.1, GitHub digest özelliğinden önce) — ölçülemedi, §7 | VAR: release digest `sha256:7fc800d2…b04e2`, indirilen baytla **EŞLEŞTİ** |

Karşıt doğrulama merceği-1 iki zip'i de **bağımsız yeniden indirdi** ve bayt-aynı buldu; iki OFL
gövdesi normalize edilip depodaki kabul edilmiş `meridian/web/fonts/OFL.txt` (Recursive) gövdesiyle
karşılaştırıldı — Geist'inki birebir aynı, Inter'inki yalnızca `PERMISSION AND CONDITIONS` /
`PERMISSION & CONDITIONS` dizgi varyantında ayrılıyor. Madde eklenmiş/çıkarılmış değil.

### 1.4 Geist Mono: yeni dosya eskisinden farklı mı?

`sha256` farklı (`d00e590b…` → `0e1af3f5…`, 748 bayt fark) ama **render farkı YOK**:
`glyf`, `gvar`, `loca`, `hmtx`, `cmap`, `fvar` tablolarının ham sha256'ları **bayt-aynı**, numGlyphs
her ikisinde 1159. Fark yalnız (a) sürüm dizgisi, (b) `head` zaman damgası, (c) hiçbir feature'ın
referans etmediği **öksüz** bir GSUB ligatür lookup'ının temizlenmesi. Bu ölçümle doğrulandı:
Geist v1.7.2 kesiti ile 08-07'nin ölçtüğü dosya **aynı mürekkep sayılarını** veriyor (§2).

Ayrıca çözüldü: 08-07'nin kullandığı dosya Vercel release'i **değil**, Google Fonts yeniden-paketiydi
(`raw.githubusercontent.com/google/fonts/main/ofl/geistmono/GeistMono[wght].ttf` ile bayt-aynı).
"Version 1.701" yüksek görünüyordu ama upstream ilerlemesi değildi.

---

## 2 · ÖLÇÜM TABLOSU

**Yöntem.** 08-07 turunun `olcum.js`'i, değiştirilmeden. Ölçülen şey **MÜREKKEP (alfa) farkı**,
advance genişliği DEĞİL — monospace bir yüzde advance hiçbir şeyi ayıramaz (her glif 600'dür).
Cihazın `devicePixelRatio`'su 2; hüküm sütunu 08-07 ile kıyaslanabilsin diye **dpr=1'e zorlandı**.
Gerçek dpr=2 karşılıkları ayrı sütunda (§2.2) — orası ayrı ve önemli bir bulgu taşıyor.

### 2.1 Ana tablo — dpr=1 (donmuş tabanın koşulları)

| Ölçüt | **A · Inter kesit** (aday, özellik kapalı) | **A‴ · Inter + özellik** (TAM dosya, `ss02`+`cv01`) | **B · Geist Mono kesit** (aday) | **C · Recursive Sans** (canlı) | **C · Recursive Mono** (canlı) | *DONMUŞ TABAN 08-07* |
|---|---|---|---|---|---|---|
| `1`/`l` fark oranı **@10px** | 0,969 | 1,000 | **0,923** | 0,933 | **1,000** | Rec.Mono **1,00** · Geist **0,92** |
| `1`/`l` fark oranı **@28px** | 0,968 | **0,988** | **0,570** | 0,931 | **0,817** | Rec.Mono **0,817** · Geist **0,57** |
| `0`/`O` fark oranı **@28px** | 0,774 | 0,826 | 0,613 | 0,663 | 0,621 | Rec.Sans **0,663** |
| `l`/`I` fark oranı @28px *(tabanda YOK)* | 0,500 | 0,944 | 0,523 | 0,939 | 0,723 | — |
| Monospace mi | HAYIR (oransal) | HAYIR | **EVET** (tüm latin advance 600, wght 100–900 boyunca) | HAYIR (oransal) | **EVET** | — |
| Rakamlar tabular mı | **HAYIR** varsayılan · `tnum` ile EVET (tüm rakam 1328) | `tnum` ile EVET | **EVET, YAPISAL** (advance 600, `tnum` gereksiz) | EVET, yapısal (60) | EVET, yapısal (60) | — |
| Türkçe 12 karakter | 12/12, konturlu, kesitte hayatta | 12/12 | 12/12, konturlu, advance 600 | 12/12 (08-07 çivisi) | 12/12 (08-07 çivisi) | — |
| Kabul çıtası (@10px `1`/`l` ≥ 0,75) | GEÇER | GEÇER | GEÇER | GEÇER | GEÇER | çıta 08-07'de donduruldu, **değiştirilmedi** |

**Tablonun okunması.**
- **Sans tarafında Inter, Recursive Sans'ı ölçülmüş biçimde geçiyor**: `1`/`l` @28 0,968 vs 0,931;
  `0`/`O` @28 0,774 vs 0,663. Inter 08-07 turunda **hiç ölçülmemişti**; bu sayıların "önce/sonra"sı yok.
- **Mono tarafında Geist Mono, Recursive Mono'ya kaybediyor** — üç ölçütte de:
  `1`/`l` @28 **0,570 vs 0,817**, `l`/`I` @28 **0,523 vs 0,723**, `0`/`O` @28 0,613 vs 0,621.
- **A‴ sütunu bir aday DEĞİL, bir tavan.** O sayılar Inter'in **352 KB'lik TAM dosyasından** ve
  `font-feature-settings:'ss02','cv01'` açıkken alındı. Dağıtım adayı kesitte bu özellikler
  **BUDANMIŞ** — ölçüldü: aynı descriptor kesite uygulandığında `l`, `0`, `1` üçünde de fark
  oranı **0** (hiçbir piksel değişmiyor), aynı descriptor tam dosyada çalışıyor. Yani A‴'ü
  almak istemek, **kesiti yeniden üretmek** demektir.

### 2.2 Aynı ölçüm, cihazın GERÇEK dpr'ında (=2) — çıtanın tanımlı olmadığı yer

| Ölçüt | Inter kesit | Geist Mono kesit | Recursive Sans | Recursive Mono |
|---|---|---|---|---|
| `1`/`l` @10px, dpr=2 | 0,989 | **0,696** | 0,964 | 0,793 |
| `1`/`l` @28px, dpr=2 | 0,957 | **0,576** | 0,901 | 0,708 |
| `0`/`O` @28px, dpr=2 | 0,717 | 0,499 | 0,567 | 0,471 |

**Bu satır önemli.** Kabul çıtası (0,75) dpr=1'de donduruldu ve dpr=2 için **hiç tanımlanmadı** —
dolayısıyla bu tablo bir hüküm değildir. Ama işaret açıktır: Retina bir ekranda, 10px'te,
Geist Mono'nun `1`/`l` ayrımı **0,696** ölçülüyor — çıtanın sayısal değerinin altında; Recursive
Mono aynı koşulda 0,793 ile üstünde. Çıtanın dpr=2 karşılığı **ölçülmedi** (§7).

### 2.3 Özellik ve kapsama farkları

| Kalem | Inter kesit | Geist Mono kesit | Recursive kesitleri (canlı) |
|---|---|---|---|
| Kesitte hayatta kalan özellikler | `calt case ccmp kern locl mark mkmk tnum zero` | `ccmp locl mark mkmk` | `ccmp locl kern mark mkmk rlig calt tnum zero case` istendi |
| `tnum` | VAR, çalışıyor (10 rakam → 1328) | **YOK — kaynakta da yok**, gerekmiyor (yapısal 600) | var |
| `zero` (eğik çizgili sıfır) | VAR, kesitte de **çalışıyor** (`0`/`O` @28 0,774 → 0,795) | Kesitte descriptor **hiçbir pikseli değiştirmedi** — AYIRT EDİLEMEDİ (§7) | var ama ATIL (DESIGN.md kaydı) |
| `ss02`/`cv01` (Il1 ayrımı) | Kaynakta VAR, **kesitte BUDANMIŞ** | Kaynakta ilgili karşılık YOK | — |
| cmap kod noktası | 278 | 260 | 260 |
| **Geist'te eksik ama Recursive'de VAR** | — | **`₺ U+20BA`** · **`✓ U+2713`** · `Δ U+0394` · `■ U+25A0` · `□ U+25A1` · `◆ U+25C6` · `◇ U+25C7` · `‐ U+2010` · `⟨⟩ U+27E8/9` · `▤ U+25A4` · `◤ U+25E4` · `U+00AD` | — |
| **Inter'de eksik ama Recursive'de VAR** | `─ U+2500` · `▤ U+25A4` · `◤ U+25E4` · `⟨⟩ U+27E8/9` · `˝ U+030B` · `U+00AD` | — | — |

Tarayıcıda doğrulandı (`karsit_dogrulama_mercek2/tarayici_advance.json`): Geist Mono yığınında
`0 M Ğ ≥ ≤ ± × − · →` **tam 60,00px** (Geist'in kendisi çiziyor), ama
`✓ ◆ ■ Δ ⚠ ✗ ⟨ ▤ ◤ Σ σ τ ⇒ ⌘ ∪ ▸ ▾ ✕` **60,21px** — yani macOS yedeği (Menlo) çiziyor;
`₺` **55,62px**, `ⓘ` **100px**. Türkçe 12 karakterin hepsi 60,00 — onları Geist'in kendisi çiziyor.
DOM 12px ızgarasında yedek yüz 10 karakterde 0,25px kaydırıyor: macOS'ta **görünmez**, yedek monosu
olmayan platformda kayma/tofu **büyür**.

---

## 3 · TABAN YENİDEN ÜRETİLDİ Mİ — **EVET**

Bu ölçümün geçerlilik kapısıdır: düzenek 08-07'nin sayılarını üretmiyorsa kıyas ölür.

| Referans | Bu tur | Donmuş taban | Tutuyor mu |
|---|---|---|---|
| Geist Mono (08-07'nin ta kendisi, `d00e590b…`) `1`/`l` @10px | 0,92 | 0,92 | **EVET** |
| Geist Mono `1`/`l` @28px | 0,57 | 0,57 | **EVET** |
| Recursive Mono `1`/`l` @10px | 1,00 | 1,00 | **EVET** |
| Recursive Mono `1`/`l` @28px | 0,817 | 0,817 | **EVET** |
| Recursive Sans `0`/`O` @28px | 0,663 | 0,663 | **EVET** |

Şartlar, kayda geçsin:
1. Kalibrasyon satırı **08-07'nin ölçtüğü fiziksel dosyanın kendisiyle** koşuldu
   (`GeistMono_ESKI_20260807.ttf`, sha256 `d00e590b…`), yeni sürümle değil.
2. Recursive satırları **canlıda bugün koşan dosyalarla** koşuldu
   (`meridian/web/fonts/recursive-{sans,mono}-vf.woff2`, sha256 `942b5aa4…` / `b4e57a7b…`).
3. Hüküm sütunu **dpr=1'e zorlandı**; zorlanmasaydı sayılar düşer ve kıyas ölürdü.
4. Negatif kontrol: aynı aile-aynı karakter farkı **0** (ölçüm gürültü üretmiyor).
   Descriptor kontrolü: tam dosyada `ss02` `I`'yı 0,806 oranında değiştiriyor — tarayıcı
   descriptor'ı gerçekten uyguluyor, "fark yok" sonuçları sessiz yutma değil.
5. Donmuş tur **yalnız okundu**; `yazi_tipi_2026-08-07` altında hiçbir dosya yazılmadı.

Ek olarak: **yeni Geist Mono v1.7.2 kesiti de aynı sayıları veriyor** (0,923 / 0,570 / 0,613).
Yani "yeni sürüm düzeltmiştir" savunması **ölçülerek düştü**.

---

## 4 · ÇATIŞMA — operatörün talimatı ile 2026-08-07 ölçümü

**Gerilim şudur.** Operatör Dub'ın yüzünü istedi: Inter + Geist Mono. Bu depo 2026-08-07'de
dokuz OFL çiftini ölçtü, Geist'i **emekli etti** ve yerine Recursive'i koydu; o hükmün gerekçesi
DESIGN.md satır 567'de, çivisi `tests/test_yazitipi_v201.py`'de duruyor. Bu turun ölçümü o hükmü
**doğruluyor**, çürütmüyor.

### 4.1 Sayı

| | Geist Mono (Dub'ın monosu) | Recursive Mono (canlı) | Fark |
|---|---|---|---|
| `1`/`l` @28px | **0,570** | **0,817** | −0,247 (−%30) |
| `l`/`I` @28px | 0,523 | 0,723 | −0,200 |
| `1`/`l` @10px | 0,923 | 1,000 | −0,077 |
| `1`/`l` @10px, gerçek dpr=2 | **0,696** | 0,793 | −0,097 · **çıtanın sayısal değerinin altında** |
| `0`/`O` @28px | 0,613 | 0,621 | −0,008 (ihmal) |

Sans tarafında çatışma **yok**: Inter, Recursive Sans'ı her ölçülen ölçütte geçiyor.
Çatışma **yalnız mono tarafındadır**.

### 4.2 Risk, adıyla

Bir alım-satım panosunda `1` ile `l` karışması soyut değildir:

- **Sembolde.** `CLF` / `C1F`, `PLTR` / `P1TR`, `SLB` / `S1B` — sembol alanı büyük punto ile
  yazılır ve tam olarak 28px, Geist'in en kötü ölçüldüğü boydur (0,570).
- **Rakamda.** Pozisyon boyutu, limit fiyatı, adet. `.gb-say` ve `.pd-stats .v` mono ve
  `clamp(...,28px)` — yine 28px ucu.
- **Etikette.** 10px etiketler (`.slab`, `.gate-l`, `.pm-thin`, `.km-head`) dpr=2 Retina'da
  0,696 ile ölçülüyor.
- **Kapsama.** Geist Mono kesitinde `₺` ve `✓` **yok**; macOS'ta yedek yüz kurtarıyor,
  yedek monosu olmayan platformda tofu/kayma büyüyor. Recursive Mono'nun kesitinde ikisi de var.

### 4.3 VARSA azaltıcı — ölçülen ve ölçülmeyen

| Azaltıcı | Durum | Kanıt |
|---|---|---|
| `font-feature-settings` ile Geist'te Il1 ayrımı açmak | **YOK.** Geist Mono'da böyle bir özellik kaynakta bile yok (`tnum`, `zero` yok; `ss01`/`ss02` rakamlara **atıl**) | `kanit/tnum_KAYNAK_kontrol.json`, `kanit/ozellik_budama.json` |
| Boyut eşiği (mono'yu yalnız ≤14px'te kullanmak) | **Mümkün ama işe yaramaz yönde.** Geist'in kötü olduğu yer 28px; 10px'te (dpr=1) 0,923 ile çıtayı geçiyor. Yani "büyük rakamı mono yazma" demek gerekir — ki `.gb-say`/`.pd-stats .v` tam olarak odur. Bu bir azaltıcı değil, bir **tasarım geri adımı** | §2.1 |
| **Yalnız-sans devralma** (Inter gelir, mono kalır) | **En güçlü azaltıcı, ölçülmüş.** Dub'ın sans dili gelir, rakam ayrımı hiç bozulmaz | §5 (b) |
| Inter'i mono yerine `tnum` ile kullanmak | Mümkün: `tnum` açıkken tüm rakam 1328 birim, hizalama tutar. Ama **oransal** yüz kalır; harfler hizalanmaz, `1`/`l` @28 0,968 ile Recursive Mono'dan **iyi** | `kanit/tnum.json` |
| Inter'de `ss02`+`cv01` açmak | **Kesitte imkânsız — budandı.** Kesit yeniden üretilirse `1`/`l` @28 0,968 → **0,988**, `l`/`I` @28 0,500 → **0,944** | §2.1, `probe` bloğu |

---

## 5 · ÜÇ SEÇENEK

### (a) TAM DEVRALMA — Inter + Geist Mono

| Kazanılan | Kaybedilen |
|---|---|
| Dub yüzüyle **birebir** aynı tipografi | Mono `1`/`l` @28: 0,817 → **0,570** (−%30) |
| Toplam **54,7 KB** (−25,2 KB, bütçede %54 boşluk) | Mono `l`/`I` @28: 0,723 → 0,523 |
| Sans tarafı ölçülmüş **iyileşme** (0,931→0,968; 0/O 0,663→0,774) | dpr=2 / 10px'te mono 0,696 — çıtanın sayısal değerinin altında |
| Geist gerçek monospace, rakam hizası **yapısal** (`tnum` gereksiz) | `₺` ve `✓` kesitte yok; yedek yüze düşüyor |
| İki lisans da OFL 1.1, RFN yok, fsType 0 | 2026-08-07 hükmünün **doğrudan geri alınması**; `test_bir_ile_l_TARAYICIDA_geistten_iyi` yeniden yazılmak zorunda |

### (b) KARMA — Inter sans + Recursive Mono kalır

| Kazanılan | Kaybedilen |
|---|---|
| Dub'ın **sans dili** gelir — ve bu taraf ölçülmüş bir iyileşme | Dub'la **birebir** aynı olmaz (mono farklı) |
| Rakam/sembol okunaklılığı **hiç bozulmaz** (Recursive Mono 0,817 kalır) | İki aileden yüz taşımanın tipografik tutarlılık bedeli — **ölçülmedi** (§7) |
| `₺`, `✓` ve pano işaretleri kesitte kalmaya devam eder | Inter kesiti `opsz`14'e sabit; başlık için Display kesimi alınamaz (§7) |
| Toplam **76,8 KB** (37,8 + 39,0), bütçede 43,2 KB boşluk | Geist Mono edinme emeği rafta kalır (dosyalar duruyor, kayıp yok) |
| 2026-08-07 hükmünün **ölçülen kısmı korunur**, çürütülen kısmı yok | |

### (c) DEVRALMA YOK

| Kazanılan | Kaybedilen |
|---|---|
| Sıfır değişiklik riski, sıfır dağıtım penceresi | Inter'in **ölçülmüş** sans üstünlüğü masada kalır (0,968 vs 0,931 · 0,774 vs 0,663) |
| Test/CSP/DESIGN.md hiç ellenmez | Operatörün açık talimatı karşılanmaz |
| | İki paket indirildi, ölçüldü, hiçbir yere bağlanmadı — emek atıl |

### ÖNERİ: **(b) KARMA**

**Gerekçe, sayıya bağlı.** Bu turda ölçülen tek **yönlü** bulgu şudur: sans tarafında Inter
kazanıyor, mono tarafında Recursive kazanıyor — ve ikisi de aynı düzenekte, aynı koşuda, tabanı
birebir yeniden üreten bir kalibrasyonla ölçüldü. (a) bu iki bulgunun **birini kazanıp ötekini
bilerek kaybetmek** demektir; kaybedilen taraf (mono `1`/`l`, 0,817→0,570) tam olarak bir alım-satım
panosunun para taşıyan yüzeyidir ve Geist'te bunu telafi edecek **hiçbir OpenType özelliği yok**
(ölçüldü: `tnum` yok, `zero` yok, `ss01`/`ss02` rakamlara atıl). (c) ise ölçülmüş bir iyileşmeyi
gerekçesiz reddeder. (b) her iki ölçümün de kazanan tarafını alır, 120 KB bütçesinde 43 KB boşluk
bırakır, ve `--sans`/`--mono` jetonları zaten ayrı olduğu için **cerrahi** bir değişikliktir:
`@font-face` ve `--sans` satırlarına dokunulur, `--mono` satırına dokunulmaz.

**(b)'nin ölçülmemiş bedelini de yazıyorum:** iki farklı aileden sans+mono taşımanın görsel
tutarlılığı bu turda ölçülmedi; Recursive Sans+Mono aynı üst-aileden geliyordu, Inter+Recursive Mono
gelmeyecek (x-yüksekliği 1118/2048 = 0,546 em vs 530/1000 = 0,530 em; cap 0,728 vs 0,710 em —
sayılar yakın ama "yakın" bir hüküm değil, ölçülmemiş bir izlenimdir).

---

## 6 · BAĞLANMA BORCU — dosyalar indi, HİÇBİR YERE BAĞLANMADI

Bugünkü durum ölçüldü: `meridian/web/fonts/` içinde **yalnız** `OFL.txt`,
`recursive-sans-vf.woff2`, `recursive-mono-vf.woff2` var. Inter ve Geist Mono kesitleri
**yalnızca** `research/olcumler/yazi_tipi_2026-08-24/woff2/` altında duruyor.

**Aşağıdakilere DOKUNULMADI — bu bir liste, bir değişiklik değil.** Başka ajanlar bu dosyalarda
çalışıyor.

### 6.1 Yüzeyler

| Dosya | Satır | Şu an ne diyor | Bağlanınca ne gerekir |
|---|---|---|---|
| `meridian/web/index.html` | 18-19 | `<link rel="preload" href="/fonts/recursive-{sans,mono}-vf.woff2" … crossorigin>` | preload hedefleri yeni dosya adlarına |
| | 103-112 | iki `@font-face` (`Recursive Sans` / `Recursive Mono`, `font-display:block`, `font-weight:400 700`) | aile adı + `src` yolu |
| | 114-117 | `--sans:'Recursive Sans',…` · `--display:var(--sans)` · `--mono:'Recursive Mono',…` | **(b)'de yalnız 114 değişir; 116 DURUR** |
| | 11-17 | CDN'in neden kaldırıldığını anlatan yorum bloğu | tarih/gerekçe güncellenir |
| | 542-549 | `zero` özelliğinin Recursive'de ATIL olduğu kaydı | yeni yüzde yeniden ölçülmeli (Inter'de `zero` **çalışıyor** — §2.3) |
| `meridian/web/landing.html` | 11-12 | preload | aynı |
| | 97-106 | iki `@font-face` | aynı |
| | 149-150 | `--sans` / `--display` / `--mono` / `--serif` | aynı |
| `meridian/web/workflow.html` | 11-12 | preload | aynı |
| | 87-96 | iki `@font-face` | aynı |
| | 129-130 | `--sans` / `--display` / `--mono` / `--serif` | aynı |
| `meridian/web/runbook.html` | — | **BİLEREK KAPSAM DIŞI** (kendi `ui-sans-serif` yığını; `tests` satır 44-48'de yazılı) | değişiklik yok |

Üç yüzeyin font bildirimleri **birebir aynı** olmak zorunda — çivi
`tests/test_yazitipi_v201.py::test_uc_yuzeyin_font_bildirimleri_BIREBIR_AYNI` (satır 239).

### 6.2 Sunum yolu ve dosyalar

| Dosya | Satır | Kalem |
|---|---|---|
| `meridian/api.py` | **711** | `_FONT_DOSYALARI = frozenset({"recursive-sans-vf.woff2", "recursive-mono-vf.woff2"})` — **izin listesi**; burada olmayan her ad 404 |
| | 714-726 | `@app.get("/fonts/{ad}")` rotası (montaj YOK, literal ad kapısı) |
| | 685-710 | rota gerekçesi + önbellek sözleşmesi (`no-cache` + içerik-sha256 ETag) yorumu |
| | 289-292 | `font-src 'self'` gerekçe yorumu (Recursive'i, 79,3 KB'ı adıyla anıyor) |
| `meridian/web/fonts/` | — | `inter-vf.woff2` + `geist-mono-vf.woff2` (ya da (b)'de yalnız `inter-vf.woff2`) **kopyalanacak** |
| `meridian/web/fonts/OFL.txt` | — | **LİSANS BORCU.** Şu an yalnız Recursive'in OFL nüshası. Yeni yüzün telif satırı + OFL metni de dağıtılmalı (OFL 1.1 şartı). Nüshalar hazır: `lisans/Inter-OFL.txt`, `lisans/GeistMono-OFL.txt` |

### 6.3 CSP

| Dosya | Satır | Durum |
|---|---|---|
| `meridian/api.py` | **305-310** | `CSP_POLITIKASI` — **canlı tek kaynak**; zaten `font-src 'self'`. Dosyalar aynı origin'den sunulduğu sürece **DEĞİŞİKLİK GEREKMEZ** |
| | 313-315 | `GUVENLIK_BASLIKLARI["Content-Security-Policy"]` |
| `deploy/Caddyfile` | 90-107 | **ATIL REFERANS** — CSP satırı yorumda (107). Yorum metni güncellenir, açılmaz |

CDN'e (`fonts.googleapis.com` / `fonts.gstatic.com`) dönüş **yasak** — üç ayrı yerde yazılı
(`index.html` 11-17, `api.py` 289-292, `Caddyfile` 94-105) ve
`test_caddyfile_CSP_dis_font_hostu_TASIMAZ` (satır 133) ile çivili. Zaten gerekmiyor: her iki
paket de self-host edilebilir (OFL 1.1).

### 6.4 Test sözleşmesi — `tests/test_yazitipi_v201.py` (674 satır)

| Satır | Kalem | Bağlanınca |
|---|---|---|
| **40-42** | `OLCUM = …/yazi_tipi_2026-08-07` · `BUILD_JSON` · `TARAYICI` | **yeni tura yönlendirilir** — ama `web_fonts_build.json` şeması bu turda sarmalandı (`yuzler[]` listesi); okuyucu buna göre güncellenmeli |
| **54-55** | `SANS_DOSYA = "recursive-sans-vf.woff2"` · `MONO_DOSYA = "recursive-mono-vf.woff2"` | yeni ad(lar) |
| 102-131 | dış-origin ve "Geist taşımaz" taramaları | **`test_hicbir_yuzey_CANLI_bildirimde_Geist_tasimaz` (120) — (a)'da doğrudan çelişir** |
| 133-158 | Caddyfile CSP dış-host taraması | değişmez |
| 189-206 | `@font-face` aile adı çivisi: `"Recursive Sans"` / `"Recursive Mono"` (195-196) | yeni aile adları |
| 208-223 | `font-display:block` | değişmez |
| 225-238 | değişken ağırlık aralığı bildirimi | değişmez (iki kesit de 400-700) |
| 239-257 | üç yüzeyin bildirimleri birebir aynı | değişmez |
| 258-273 | jeton çivisi: `--sans` → `'Recursive Sans'` (268), `--mono` → `'Recursive Mono'` (269) | **(b)'de yalnız 268 değişir** |
| 275-291 | `preload` + `crossorigin` + `type=font/woff2` | değişmez |
| 294-309 | disk ↔ üretim kaydı eşleşmesi | yeni kayıt |
| 310-330 | isim çakışması: `nameID1 == "Recursive Sans"` (320) / `"Recursive Mono"` (321) | yeni: `"Inter"` / `"Geist Mono"` (kesitlerin nameID1'i ölçüldü) |
| 331-341 | rakamlar YAPISAL tabular **HER İKİ KESİTTE** | **(a) ve (b)'de KIRILIR** — Inter'in rakamları varsayılan **tekdüze DEĞİL** (833…1323). `tnum` ile tekdüze; test bu ayrımı taşıyacak biçimde yeniden yazılmalı |
| 342-353 | ağırlık ekseni 400-700, varsayılan 400 | geçer (ölçüldü) |
| 354-368 | Türkçe glif çivisi + `cmap >= 250` | geçer (Inter 278, Geist 260) |
| **369-380** | bütçe `< 120 KB` | geçer: (a) 54,7 KB · (b) 76,8 KB |
| **382-395** | `OFL.txt` içinde `"The Recursive Project Authors"` (389) | **KIRILIR** — lisans borcu ödenmeden geçmez |
| 407-424 | tarayıcı kanıt dosyaları listesi (08-07'nin 13 dosyası) | bu turun dosya adları farklı (`01_ornek_uc_yuz.png`, `02_yakinlastirma_6x.png`, `03_olcum_ozet.png`, `yuzler.css`, `sunucu.py`) |
| 426-441 | mono gerçekten mono / sans oransal | geçer |
| **443-457** | `test_bir_ile_l_TARAYICIDA_geistten_iyi` — `yeni_mono_1l_* > geist_mono_1l_*` ve `≥ 0,75` | **(a)'da KIRILIR VE KIRILMALI**: yeni mono Geist'in kendisi olur. (b)'de geçer |
| 460-478 | isim çakışması bloke edici değildi | yeni tur kaydı |
| 480-499 | DESIGN.md ön-madde + `## Typography` `"Recursive …"` diyor (488, 493) | DESIGN.md ile birlikte |
| 501-509 | rampa dokuz basamak `[10,11,12,13,14,17,20,24,28]` | değişmez |
| 511-528 | Tabular Rule + `slashed-zero` yasağı, `"Recursive Mono"` (522) ve `"inert"` şartı | **gerekçe yeniden ölçülmeli**: Inter'de `zero` ATIL DEĞİL, çalışıyor (0,774→0,795) |
| **543-553** | `api.py` rotası testi — hata metninde literal `"recursive-sans-vf.woff2", "recursive-mono-vf.woff2"` (550) | metin güncellenir |
| 555-580 | `TestClient` ile iki kesitin gerçekten sunulduğu | yeni adlar |
| 625-673 | tip jetonu çözücü + clamp kapıları | değişmez |

### 6.5 DESIGN.md (1214 satır)

| Satır | Kalem |
|---|---|
| 17-80 | ön-madde `typography:` bloğu — on jeton, hepsi `'Recursive Sans'` (19,25,31,37,43,49,55) veya `'Recursive Mono'` (61,68,74) |
| **557-570** | `## Typography` bölümü: aile adları (559-560), self-host yolu + OFL + upstream `arrowtype/recursive` v1.085 (562-563), `font-src 'self'` (565), 2026-08-07 emeklilik gerekçesi (567+) |
| 549-551 | "`slashed-zero` is not declared … Re-verify if the typeface changes." — **bu cümle tam olarak bu turu çağırıyor**; Inter'de `zero` çalışıyor |
| 705-712 | The Ramp Rule (dokuz basamak) — değişmez |
| 834+ | The Tabular Rule — `"Recursive Mono"` adını anıyor |

Ayrıca DESIGN.md § Typography, testin (497-498) istediği **cap-height kayıp kalemini** (`−0.10 px`)
taşıyor; yeni yüzde bu muhasebe **yeniden ölçülmeli** (Inter cap 1490/2048 = 0,7275 em vs
Recursive 700/1000 = 0,700 em; Geist 710/1000 = 0,710 em — ham sayılar var, **piksel karşılığı
bu turda hesaplanmadı**).

---

## 7 · AÇIK KALANLAR (ölçülemeyenler ve nedenleri)

| # | Kalem | Durum | Neden |
|---|---|---|---|
| 1 | Inter zip'inin **yayıncı sha256'sı** | ÖLÇÜLEMEDİ | rsms/inter v4.1 (2024-11-16) GitHub'ın release-digest özelliğinden önce yayınlandı; API varlık kaydında `digest=None`, GPG/sigstore imzası yok. Elimizdeki hash **kendi indirdiğimiz baytların** kaydıdır; yalnızca API'nin bildirdiği bayt boyutuyla (33.707.794) eşleşti. Karşıt mercek bağımsız yeniden indirdi ve bayt-aynı buldu — bu bir tekrarlanabilirlik kanıtıdır, üst-kaynak imzası değil |
| 2 | Geist kesitinde **`zero` özelliği var mı** | AYIRT EDİLEMEDİ | `zero` descriptor'ı Geist kesitinde hiçbir pikseli değiştirmedi (fark oranı 0, 231 mürekkepli piksel). İki açıklama tarayıcıdan ayrılamıyor: (a) özellik dosyada yok, (b) var ama varsayılan sıfır zaten eğik çizgili. `kanit/tnum_KAYNAK_kontrol.json` (a)'yı destekliyor (`zero: null` kesilmemiş kaynakta da), 6× yakınlaştırma (b)'yi düşündürüyor. Font tablosundan kesin okuma bu tarayıcı ajanının ortamında yapılamadı |
| 3 | Inter'in **08-07 karşılığı** | YOK | Inter 2026-08-07 turunda hiç ölçülmedi. Inter için "önce/sonra" **yoktur**, yalnız bu turun sayısı vardır. Dokuz adaylık havuzda neden bulunmadığı bu turda araştırılmadı |
| 4 | `l`/`I` sütununun **tabana kıyası** | YOK | 08-07 turu `l`/`I` mürekkep farkını hiç ölçmedi; o turun kaydında böyle bir alan yok. Bu turun `l`/`I` sayıları **yalnız yüzler arası** kıyasta geçerli |
| 5 | Kabul çıtasının **dpr=2 karşılığı** | ÖLÇÜLMEDİ | Çıta (0,75) dpr=1'de donduruldu; dpr=2 için ne bir çıta ne bir dönüşüm tanımlandı. §2.2'deki dpr=2 sayıları bu yüzden **işaret**tir, hüküm değil |
| 6 | **İnsan okuma hatası/hızı** | ÖLÇÜLMEDİ | Mürekkep fark oranı bir **PROXY**'dir. Bu tur kişi denemesi içermiyor; "0,570 şu kadar okuma hatası demektir" cümlesi kurulamaz |
| 7 | Inter kesitinde **`ss02`/`cv01` yok**, nedeni | KISMEN | Yokluk ölçüldü (descriptor kesitte 3 karakterde de 0 fark, aynı descriptor tam dosyada çalışıyor → dosya eksik, descriptor değil). Nedeni `web_fonts_build.json`'un `yalin_ozellikler` listesinden **okundu**, kesiti üreten betik bu turda **yeniden koşulmadı** |
| 8 | Inter kesiti **`opsz`14'e sabitlendi** | ÖLÇÜLDÜ, SONUCU AÇIK | Kesit ile `opsz`14'e çivili tam dosya `l`/`1`/`0`/`M`'de **birebir aynı** (fark 0). `opsz` ekseni gerçekten biçim değiştiriyor (`M` @28 opsz14↔32 farkı 0,679). Yani başlıklar için **Display kesimi alınamaz**; bunun tasarım bedeli ölçülmedi |
| 9 | İki farklı aileden **sans+mono tutarlılığı** | ÖLÇÜLMEDİ | (b) seçeneğinin tek ölçülmemiş bedeli. x-yükseklik/cap oranları yakın (0,546/0,728 em vs 0,530/0,710 em) ama "yakın" bir hüküm değildir |
| 10 | **Cap-height kayıp muhasebesi** (DESIGN.md'nin istediği `−0.10 px` kalemi) | HESAPLANMADI | Ham `sCapHeight`/`sxHeight`/`unitsPerEm` üçlüsü üç yüz için de kayıtta var; piksel karşılığı bu turda türetilmedi |
| 11 | **Kod noktası kümesi 347 → 350** | AÇIKLANMADI, ZORLANMADI | Aynı güvenlik kümesi ve aynı kapsam fonksiyonu; fark taranan kaynak dosyaların 08-07'den beri değişmesinden. 347'ye **zorlanmadı** (uydurma yasağı) — 08-07'nin tam listesi kayda geçmemiş, git bu ajana yasak. Hangi 3 kod noktası eklendiği **bilinmiyor** |
| 12 | **Üçüncü karşıt doğrulama merceğinin hükmü** | ELİME ULAŞMADI | Görev üç mercek bildirdi. Mercek-1'in (özgünlük+lisans) tam metni geldi ama **son cümlesinin ortasında kesildi** — "testlerden biri bu turda KIRILACAK" dediği testi **adlandıramadan**. Mercek-2'nin hükmü metin olarak gelmedi; kanıt dosyalarından (`karsit_dogrulama_mercek2/`) okundu ve §2.3'e işlendi. Mercek-3'ün ne metni ne diskte bir çıktısı bulundu (`find` ile arandı). §6.4'te "kırılır" işaretlediğim testler **benim tests dosyasını okuyarak** çıkardığım tespitlerdir, mercek-1'in sözü değil |
| 13 | Satoshi'nin **depoya commit'lenebilirliği** | BELİRSİZ | `satoshi/RAPOR.md`: FFL v2.0 §02 ile §01/§42 arasında çelişki. Kesit alma ise **adıyla yasak** — bu deponun kesit hattına giremez |

---

## KANIT DOSYALARI

```
research/olcumler/yazi_tipi_2026-08-24/
├── edinme/inter/rapor.json            · edinme/geist/rapor.json
├── fonts/{Inter-VF.ttf, GeistMono-VF.ttf}
├── woff2/{inter-vf.woff2, geist-mono-vf.woff2}          ← dağıtım adayları
├── lisans/{Inter-OFL.txt, GeistMono-OFL.txt}
├── web_fonts_build.json
├── kanit/{tnum.json, tnum_KAYNAK_kontrol.json, ozellik_budama.json,
│          agirlik.json, kap_donusumu.json, turkce_glif.json, turkce/*.png}
├── tarayici/{olcum_sonucu.json, olcum.html, olcum.js, yuzler.css, 01-03*.png}
├── karsit_dogrulama_mercek2/{glif_kanit.json, tarayici_advance.json, kd_mercek2.html}
└── satoshi/RAPOR.md
```

Donmuş taban (**yalnız okundu, değiştirilmedi**):
`research/olcumler/yazi_tipi_2026-08-07/tarayici/olcum_sonucu.json`
