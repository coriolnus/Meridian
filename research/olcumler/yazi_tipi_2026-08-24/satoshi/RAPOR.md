# SATOSHI — EDİNME + LİSANS HÜKMÜ (2026-08-24)

Kapsam: yalnız **Satoshi** (ITF / Fontshare). Inter ve Geist Mono paralel iş akışında.
Yazma alanı: `research/olcumler/yazi_tipi_2026-08-24/satoshi/`.

Bu rapordaki her lisans cümlesi **paketin içinden çıkan resmi nüshadan** alıntıdır:
`lisans/FFL.txt` (sha256 `145e7fe2…f554`, 12.734 bayt) — **ITF Free Font License (FFL),
Version 2.0, 17 Aug 2026**. Özetten değil metinden okundu.

> **DİKKAT — LİSANS BİR HAFTALIK.** Nüshanın kendi tarihi **17 Aug 2026**; bugün 2026-08-24.
> Bu FFL **v2.0**'dır. "Fontshare fontları serbesttir" biçimindeki eski bilgi/alışkanlık
> (v1.x dönemi) **geçersizdir**; aşağıdaki hükümler v2.0 metnine dayanır.

`https://www.fontshare.com/licenses/itf-ffl` sayfası **ölçülemedi**: HTTP 200 dönüyor ama
gövde JS ile çizilen bir SPA kabuğu — sunucudan gelen 1.744 baytın tamamı
`"Enable javascript to use this application."`, lisans metni yok (`kanit/ffl_page.html`).
Metin bu yüzden ikiliyle birlikte dağıtılan paket nüshasından alındı; o nüsha zaten
kullanıcıya teslim edilen sözleşmedir.

---

## 1 · LİSANS HÜKMÜ

### 1.1 Üç soru, üç hüküm

| # | Soru | HÜKÜM | Dayanak |
|---|------|-------|---------|
| **a** | Bu depo Satoshi'yi **self-host** edebilir mi? | **EVET** | FFL §01 |
| **b** | Bu depo Satoshi'den **kesit (subset)** alabilir mi? | **HAYIR** | FFL §02 + Definitions + §05 |
| **c** | Bu depo Satoshi'yi **depoya commit'leyebilir** mi? | **BELİRSİZ** | FFL §02 vs. §01/§42 |

### (a) SELF-HOST → **EVET**, açıkça ve isimle izinli

> §01 Grant of License: *"You may **self-host the Font Software on your own servers or
> infrastructure** for use on your own websites and applications, including through standard
> webfont technologies such as **CSS @font-face**. Self-hosting by end users is permitted and
> **recommended** for greater control, reliability and performance. **Use of the Fontshare API
> is optional and is not required for web use.**"*

Bu, sorulan sorunun tam karşılığı: CDN şartı **YOK**, `font-src 'self'` ile çatışma **YOK**.
İkinci bir teyit, §02'nin sonundaki şüphe-giderme cümlesi:

> §02: *"For the avoidance of doubt, **nothing in this Section 02 restricts the self-hosting**,
> embedding or other use of the Font Software by the Licensee for the Licensee's own websites,
> applications or other permitted uses under Section 01."*

API'nin isteğe bağlılığı ayrıca §06'da bir **uyarıya** dönüşüyor — yani ITF self-host'u
tercih ettiriyor:

> §06: *"THE FONTSHARE API IS PROVIDED AS A CONVENIENCE AND **DOES NOT FORM PART OF THE RIGHTS
> GRANTED** … INDIAN TYPE FOUNDRY MAY, AT ITS SOLE DISCRETION AND WITHOUT PRIOR NOTICE, MODIFY,
> RESTRICT, SUSPEND OR DISCONTINUE ACCESS TO THE FONTSHARE API"*

**Ticari kullanım** de aynı maddede serbest:

> §01: *"…a non-exclusive, non-assignable, non-transferable and terminable license to access,
> download, install, store and use the Font Software for **personal or commercial purposes,
> free of charge** and for an unlimited period of time"*
> ve *"You may use the Font Software in any media, including Print, **Websites**, Mobile or
> Desktop Applications … at any scale and in any location worldwide."*

### (b) KESİT ALMA → **HAYIR**, ADIYLA yasak

Bu, bu turun tek en sert bulgusu. `subsetting` kelimesi lisansta **iki ayrı yerde** geçiyor ve
ikisinde de yasak tarafında:

> §02 Limitations of Usage: *"You may not modify, edit, adapt, translate, reverse engineer,
> decompile, disassemble or otherwise alter the Font Software … This includes modifying or
> replacing glyphs, **subsetting, format conversion**, or altering font names, copyright
> information, ownership information or other metadata."*

> Definitions, "Derivative Work": *"…including modifications to font files (such as OTF, TTF,
> WOFF, WOFF2 or variable fonts), glyphs, characters, spacing, kerning, metrics, naming,
> **subsetting, format conversion** or other font data."*

> §05 Derivative Work: *"You may not create a Derivative Work from the Font Software
> **without the prior written consent of the Licensor**."*

Bu deponun kesit borusu (`yazi_tipi_2026-08-07/build_web_fonts.py`) tek koşumda **üç** yasak
işi birden yapar ve üçü de yukarıdaki cümlede adıyla sayılıdır:

1. `subsetter.subset(font)` → **subsetting**
2. `font.flavor = "woff2"` → **format conversion**
3. `yeniden_adlandir()` → **altering font names … or other metadata**

Recursive'de üçü de serbestti (SIL OFL 1.1 türetmeye açıkça izin verir, ve telifte Rezerve Font
Adı yoktu). **Lisans ailesi değişince boru geçersizleşir**: bir betiğin kopyalanabilir olması
lisansın devredilebilir olduğu anlamına gelmez.

**FİİLİ SONUÇ (ölçüldü, varsayılmadı):** `satoshi/kesit_uret.py` — borunun Satoshi'ye uyarlanmış
kopyası — yazıldı ve modül seviyesinde **sert bir lisans kapısıyla** kapatıldı. Koşuldu, çıkış
kodu **2**, hiçbir ikili üretmedi. Boru dosyada duruyor ki "denendi mi / unutuldu mu" sorusu bir
daha sorulmasın: **denenmedi, çünkü yasak.**

**KESİT GEREKMİYOR ZATEN:** ITF paketin içinde **kendi WOFF2'sini** veriyor
(`Fonts/WEB/fonts/Satoshi-Variable.woff2`, 42.588 bayt). O dosya "Official Version"ın parçası:

> Definitions: *"Font Software includes **all font formats** and bitmap or vector
> representations distributed by Indian Type Foundry under this License."*

Yani hiçbir dönüşüm yapmadan, olduğu gibi servis edilebilir. Bedeli: **kesit alınamadığı için
41,6 KB bir tabandır ve sıkıştırılamaz** (bkz. §5).

### (c) DEPOYA COMMIT → **BELİRSİZ**

İki cümle birbirini kesiyor ve metin bu kesişimi çözmüyor.

**Yasak tarafı — "repository" kelimesi lisansta ADIYLA geçiyor:**

> §02: *"The Font Software may not, beyond the permitted copies and uses defined herein, be
> distributed, duplicated, loaned, resold, sublicensed, transferred, donated, given away or
> otherwise **made available to any other person or entity**, whether for free or for a fee.
> This includes distributing the Font Software through another font website, font library,
> marketplace, **repository**, download service, application or platform, or by email,
> removable media, **publicly accessible servers**, file-sharing services, peer-to-peer
> networks or any other means."*

**İzin tarafı — iç kopyalar açıkça yeniden-dağıtım SAYILMIYOR:**

> §01: *"Where the Licensee is an organization, the Font Software may be **installed, stored,
> copied and shared internally** among its employees for the Licensee's own permitted uses under
> this License. **Such internal sharing does not constitute redistribution** under this License."*
> ve *"You may make a reasonable number of **backup copies**…"*

**Neden BELİRSİZ (ve neden "muhtemelen tamam" demiyorum):**

- Madde 02'nin fiili çekirdeği "**made available to any other person or entity**"dir. `coriolnus/Meridian`
  **özel** bir depodur; üçüncü bir kişiye erişim vermez. Bu okumaya göre §01'in "internal storage"
  izni yeter ve commit serbesttir.
- Ama §02 dağıtım kanalları listesinde **"repository"** kelimesi *aynen* geçiyor ve metin
  "public repository" demiyor — **nitelemesiz**. Metin özel/kamu ayrımını commit bağlamında
  hiçbir yerde yapmıyor; ayrımı ben yaptım, lisans yapmadı. Ölçülemeyeni hüküm diye yazamam.
- Bu depoya özgü üç ek gerçek belirsizliği **artırıyor**, azaltmıyor:
  1. **Git geçmişi kalıcıdır.** Bir kez commit'lenen ikili, sonradan silinse bile geçmişte durur;
     depo bir gün kamuya açılırsa ihlal **geriye dönük** olarak doğar.
  2. Depo **üçüncü taraf otomasyonu** tarafından klonlanıyor (CLAUDE.md md.8: cloud oturumları
     GitHub'daki hali klonlar; Claude GitHub App all-repos). Bunlar "employees" mi, yoksa
     §02'nin "made available to any other person or entity"si mi — metin söylemiyor.
  3. §08 Termination, ihlalde **derhal fesih** ve **silme kanıtı** öngörüyor:
     *"the Licensee must immediately cease all use … and delete the Font Software and all copies
     thereof in its possession or control. **Proof of deletion must be provided upon request**."*
     Git geçmişinden "silme kanıtı" üretmek pratikte `filter-repo` + force-push demektir.

**BELİRSİZLİĞİ SIFIRLAYAN YOL VAR ve maliyeti düşük:** fontu **hiç commit'lemeden** self-host
etmek. `meridian/web/fonts/satoshi-variable.woff2` `.gitignore`'a alınır, dosya sunucuya
`dagit.sh` dışı bir yolla (rsync/kurulum adımı) konur. Bu durumda §01'in self-host izni
tamamen geçerlidir ve §02'nin "repository" kelimesine hiç dokunulmaz. **Hüküm gerektirmeyen
tek yol budur** — ve operatör kararıdır, ajan kararı değil.

### 1.2 Atıf (attribution) — İKİ KAYNAK ÇELİŞİYOR

Lisans metni atfı **şart koşmuyor**:

> §01: *"You may, but are **not required to**, identify or credit Indian Type Foundry or
> Fontshare in works created using the Font Software."*

Ama **fontun kendi `nameID 13` (License Description) alanı** bunun tersini söylüyor (ölçüldü,
`kanit/satoshi_olcum.json`):

> *"This Font Software is protected under domestic and international trademark and copyright
> law. **You agree to identify the ITF fonts by name and credit the ITF's ownership** of the
> trademarks and copyrights in any design or production credits."*

`nameID 14` → `https://fontshare.com/terms` (FFL değil, genel şartlar).

**Değerlendirme:** İkilinin gömülü dizesi ITF'nin eski/genel standart metnidir ve **FFL v2.0'dan
7 gün önce basılmış bir ikilide duruyor** (telif dizesi "Copyright 2017-2021"). Sözleşme
FFL'dir ve FFL "not required" diyor; ama iki metin çelişince **maliyeti sıfır olan** taraf
seçilir: **atıf yaz.** Nereye: `meridian/web/fonts/` altına lisans metni (`FFL.txt`) + kaynak
kaydı; `DESIGN.md`'nin tipografi bölümüne bir satır. Bunu yaparken §02'nin *"altering …
copyright information, ownership information or other metadata"* yasağı gereği **ikilinin
kendi `name` tablosuna dokunulmaz** — ki zaten kesit alınmadığı için dokunulmuyor.

### 1.3 Yasaklananların tam listesi (§02, §03, §05)

| Yasak | Alıntı | Bu depo için |
|---|---|---|
| Değiştirme / kesit / format dönüşümü / ad-metadata değiştirme | §02 (yukarıda) | **VURUR** — kesit borusu kullanılamaz |
| Yeniden dağıtım (repository, publicly accessible servers dahil) | §02 (yukarıda) | **BELİRSİZ** — özel depo (bkz. c) |
| Dış tedarikçiye font dosyası verme | §02: *"You may not provide the Font Software directly to external designers, agencies, contractors, printers…"* | Vurmaz |
| Üçüncü taraflara **seçilebilir font** olarak sunma | §02: *"You may not host, serve, embed or otherwise make the Font Software available for use by third parties through any website, application, online service, SaaS platform, design tool, template editor… **even where such users cannot download or extract** the Font Software"* | **Vurmaz** ama sınır burada: pano ziyaretçisinin tarayıcısına woff2 servis etmek §01'in self-host'udur; ziyaretçiye "font seç" imkânı verilirse (ör. tema/tipografi seçici) bu madde **vurur** |
| Gömülü fontun belgeden çıkarılabilir olması | §03: *"provided that the embedded Font Software cannot be extracted or used independently"* / *"The extraction … for independent use is prohibited."* | Vurmaz (PDF üretmiyoruz) |
| Türetilmiş eseri dağıtma | §05: *"A Derivative Work may not be sublicensed, sold, leased, rented, loaned, distributed…"* | Kesit alınmadığı için konusuz |

Ek: yargı yeri **Ahmedabad, Gujarat, Hindistan**; uygulanacak hukuk **Hindistan** (§09).
Lisans **terminable** (§01) ve ihlalde derhal feshedilebilir (§08).

### 1.4 Deponun mevcut çivisi ne şart koşuyor — ve ne yapılmalı

`tests/test_yazitipi_v201.py::test_OFL_lisansi_FONTLARLA_BIRLIKTE_dagitiliyor` (OKUNDU,
değiştirilmedi) şunu şart koşuyor:

- `meridian/web/fonts/OFL.txt` **dosyası var olacak**;
- metninde `"The Recursive Project Authors"` geçecek;
- metninde `"SIL OPEN FONT LICENSE Version 1.1"` geçecek;
- metninde `"Reserved Font Name"` geçecek.

Yani çivi **tek bir dosyaya, tek bir lisans ailesine ve tek bir telif sahibine** çakılmış.
Docstring'i de niyetini söylüyor: *"OFL 1.1, telif kaydının ikili ile birlikte taşınmasını
İSTER."*

**HANGİSİ: kapsam genişletmesi mi, ayrı kural mı → AYRI KURAL.** (Uygulamadım, hüküm Rol-1'de.)

Gerekçe: bu testin dört iddiasının **hiçbiri** Satoshi için doğru değil ve doğru olamaz.
Satoshi OFL değil (FFL v2.0), telif sahibi ITF, "Reserved Font Name" kavramı FFL'de yok, ve
en önemlisi **OFL ile FFL'in lisans-dosyası mantığı zıt**: OFL, dağıtıma izin verir ve karşılığında
lisansın kopyayla birlikte taşınmasını **şart koşar**; FFL ise dağıtımı **hiç izinli kılmaz**, bu
yüzden "lisansı yanında taşı" diye bir şartı **yoktur**. Mevcut testi Satoshi'yi kapsayacak
şekilde genişletmek, iki zıt mantığı tek assert'te toplamak olur — ve genişletilmiş test
Satoshi'nin asıl riskini (kesit yasağı, dağıtım belirsizliği) hiç ölçmez.

Satoshi'nin ihtiyacı olan **ayrı** çiviler, ölçülebilir biçimde:

1. `meridian/web/fonts/FFL.txt` **var** ve içinde `"ITF Free Font License"` + `"Indian Type
   Foundry"` geçiyor (OFL.txt'ye dokunmadan, ayrı dosya).
2. Dağıtılan `satoshi*.woff2`'nin **sha256'sı ITF'nin verdiği dosyayla birebir aynı** —
   yani "kesit alınmamış" iddiası bir beyan değil, bir **ölçüm**. (Recursive'in
   `web_fonts_build.json` eşleşmesinin FFL karşılığı budur.) Beklenen değer:
   `e739aff9b4d02c264341d6d4872edcda28e79373aeda936f659566a1cd3eb47f`, 42.588 bayt.
3. Satoshi ikilisinin `nameID 0/13/14`'ü **değiştirilmemiş** (FFL §02 metadata yasağı).
4. `test_dagitim_boyutu_BUTCEDE`'nin bütçesi **üç yüzü** sayacak biçimde güncellenmeli
   (şu an yalnız `build_kaydi["kesitler"]`e bakıyor, Satoshi orada olmayacak — çünkü
   üretilmiyor, indiriliyor). Sayı için bkz. §5.

---

## 2 · NE İNDİRİLDİ

| Kalem | Değer |
|---|---|
| Kaynak sayfa | `https://www.fontshare.com/fonts/satoshi` |
| **İndirme URL'si** | `https://api.fontshare.com/v2/fonts/download/satoshi` (HTTP 200, `application/zip`) |
| `content-disposition` | `filename=Satoshi_Complete.zip` |
| Zip yolu | `research/olcumler/yazi_tipi_2026-08-24/satoshi/fonts/satoshi.zip` |
| Zip boyut | 2.168.134 bayt, 63 dosya |
| **Zip sha256** | `03ec52cf8d0b44628a3b8ce782ccbac13bc632017a6be8215a03322afa1a26ea` |
| Sürüm (ikiliden) | `nameID 5 = "Version 2.000"` |
| Telif (ikiliden) | `nameID 0 = "Copyright 2017-2021 Indian Type Foundry. All rights reserved."` |
| Aile (ikiliden) | `nameID 1 = "Satoshi Variable"`, `nameID 6 = "SatoshiVariable-Bold"` |
| Yayıncı | Indian Type Foundry · tasarımcı Deni Anggara (API metadata) |
| `license_type` (API) | `itf_ffl` |

**Değişken kesit tercih edildi** (brief gereği). İki dosya kritik:

| Dosya | Bayt | sha256 |
|---|---|---|
| `Fonts/TTF/Satoshi-Variable.ttf` | 127.420 | `02ad131926aa46d282b6af73ad2bcaecb0ec6ef3b830a2f08dcabef44f1140ff` |
| **`Fonts/WEB/fonts/Satoshi-Variable.woff2`** ← dağıtılacak olan | **42.588** | `e739aff9b4d02c264341d6d4872edcda28e79373aeda936f659566a1cd3eb47f` |
| `License/FFL.txt` | 12.734 | `145e7fe2429a3336ba215c070ef722000e01348a3e1baaa127e871bb5012f554` |

**ÇELİŞKİ KAYDA GEÇTİ:** Fontshare API metadata'sı `"version": "1.0"` ve `axes.range_default:
780.0` diyor; **ikilinin kendisi** `Version 2.000` ve `wght` varsayılanı **900** diyor. İkili
otoritedir; API metadata'sı bayat. (`kanit/edinme.json`)

Araç: fontTools 4.63.0 + brotli, **depoya kurulmadı** — scratchpad'de tek kullanımlık uv venv
(08-07 raporunun kendi reçetesi). Depo `.venv`'inde fontTools **yok** (ölçüldü).

---

## 3 · EKSENLER — ve ağırlık 500

`kanit/satoshi_olcum.json`, TTF ve WOFF2'de **birebir aynı**:

```
fvar wght : min 300 · VARSAYILAN 900 · max 900
adlandırılmış kesitler: Light 300 · Regular 400 · Medium 500 · Bold 700 · Black 900
unitsPerEm 1000 · glif 504 · cmap 431 · usWeightClass 900 · fsType 0 (gömme serbest)
```

**Dub'ın istediği ağırlık 500 aralıkta MI? → EVET.** 500 hem `[300, 900]` aralığının içinde,
hem de `Medium` adıyla ayrıca tanımlı bir kesit.

> **TUZAK — VARSAYILAN 900.** `wght` ekseninin varsayılanı 400 değil **900**'dür
> (`usWeightClass 900`, `nameID 6 = "SatoshiVariable-Bold"`). `@font-face` bildiriminde
> `font-weight: 300 900` **yazılmazsa** tarayıcı ekseni sürmez ve yüz **Black** açılır —
> Dub'ın "weight 500, never shout" imzasının tam tersi, hem de sessizce. Recursive'de aynı
> sınıf tuzak vardı (varsayılan 300) ve orada eksen 400 tabanına **daraltılarak** kapatılmıştı;
> **Satoshi'de bu çözüm YASAK** (daraltma = instancing = Derivative Work, FFL §02/§05).
> Tek savunma CSS bildirimidir, ve bu yüzden bir **test çivisi** hak ediyor.

ITF'nin kendi `satoshi.css`'i doğru bildirimi zaten veriyor (`font-weight: 300 900`) ama
`font-display: swap` kullanıyor — bu deponun `test_font_display_BLOCK_swap_DEGIL` çivisiyle
çelişir. Kendi stil dosyamızı yazmak lisans açısından serbesttir (CSS Font Software değildir);
vendor CSS'i olduğu gibi almak **olmaz**.

**Diğer ölçümler:** `tnum` özelliği **VAR** (`aalt ccmp case dlig dnom frac kern liga locl mark
numr ordn pnum salt sinf ss01..ss04 subs sups tnum`), `locl` **VAR** (Türkçe i-noktası
davranışı için gerekli).
**Ama rakamlar varsayılan olarak ORANSAL:** 0-9 advance kümesi
`[437, 559, 570, 605, 611, 630, 657, 659, 718]` — **dokuz farklı genişlik**.
Recursive'in yapısal `[600]`'ünün (bkz. `test_rakamlar_YAPISAL_tabular_HER_IKI_KESITTE` ve
envanter çivisi T1) karşılığı Satoshi'de **yok**; hizalama ancak CSS'te
`font-variant-numeric: tabular-nums` ile alınır. Display başlıkta sayı geçiyorsa (panoda geçiyor:
`.greet`, `.ph`) bu bir gerçek risktir.

---

## 4 · TÜRKÇE KAPSAMA

**Kesit ÖNCESİ (= tam dosya) — on iki karakterin ON İKİSİ de cmap'te, glif glif:**

| | | | | | | | | | | | |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ı U+0131 ✓ | İ U+0130 ✓ | ş U+015F ✓ | Ş U+015E ✓ | ğ U+011F ✓ | Ğ U+011E ✓ | ç U+00E7 ✓ | Ç U+00C7 ✓ | ö U+00F6 ✓ | Ö U+00D6 ✓ | ü U+00FC ✓ | Ü U+00DC ✓ |

Eksik: **YOK** (`turkce_eksik: []`). `locl` özelliği de var. Aynı sonuç hem `Satoshi-Variable.ttf`
hem `Satoshi-Variable.woff2` için ölçüldü.

**Kesit SONRASI → ÖLÇÜLEMEZ, ve bu bir eksiklik değil bir hüküm:** kesit **alınmıyor** (FFL §02,
bkz. §1.1b). Dağıtılacak dosya ITF'nin verdiği tam dosyanın **birebir kendisidir** — sha256'sı
kayıtlı. Dolayısıyla "subset düşürmüş olabilir" riski **yapısal olarak yok**: düşürecek bir
adım yok. Kesitin Türkçeyi düşürmesi Recursive'de gerçek bir risktir ve orada test ediliyor;
Satoshi'de risk **yerini** değiştiriyor — tehlike artık kesit değil, **yanlış dosyanın**
(ör. yalnız Latin `Satoshi-Regular.woff2`) dağıtılması. Çivi buna göre kurulmalı (§1.4/2).

**Borunun istediği güvenlik kümesinden Satoshi'de OLMAYANLAR** (315 istenen kod noktasından 67'si;
tam liste `kanit/satoshi_olcum.json:boru_kumesi_fontta_yok`). Kontrol karakterleri (U+007F-U+009F)
dışında panoyu ilgilendirenler:

- **U+00A0 kırılmaz boşluk — YOK.** Tarayıcı normal boşluğa/yedek yüze düşer.
- **U+20BA ₺ Türk lirası — YOK.** (Meridian USD hisse işliyor; şimdilik zararsız, ama kayda geçti.)
- U+2010/U+2011 tipografik tire — YOK (U+2013/U+2014 VAR).
- Δ Σ σ τ (U+0394, U+03A3, U+03C3, U+03C4) — YOK.
- Klavye işaretleri ⌘ ⇧ ⌥ ⏎ (U+2318, U+21E7, U+2325, U+23CE) — YOK.
- Geometrik işaretler ▪ ▫ ▶ ▸ ▼ ▾ ◆ ◇ ◈ ◐ ve ✕ ✗ ⟨ ⟩ — YOK. (✓ U+2713 **VAR**.)
- ⇒ U+21D2, ∪ U+222A — YOK.

Bunların hiçbiri Satoshi'nin **display başlık** rolünü bozmaz (hiçbiri başlıkta geçmez), ama
Satoshi'yi gövdeye/etikete taşıma fikri varsa **bozar** — ve zaten Dub da yasaklıyor.

---

## 5 · BOYUT ve ÜÇLÜ BÜTÇE

Bütçe kapısı `tests/test_yazitipi_v201.py::test_dagitim_boyutu_BUTCEDE` (OKUNDU):
`assert toplam < 120 * 1024` → **122.880 bayt**. Docstring'i eşiğin nereden geldiğini söylüyor:
tam eksenli Recursive çifti 117,9 KB veriyordu; kapı "sessizce iki katına çıkmasın" diye var.
Bugünkü canlı toplam: **81.168 bayt / 79,3 KB** (`web_fonts_build.json` + diskteki dosyalar).

**Üç yüzün toplamı — ölçüldü (`butce.py` → `kanit/butce.json`):**

| Yüz | Dosya | Bayt | KB | Kesildi mi? | cmap |
|---|---|---|---|---|---|
| Inter | `InterVariable.ttf` → kesit | 38.572 | 37,7 | evet | 278 |
| Geist Mono | `GeistMono[wght].ttf` → kesit | 17.204 | 16,8 | evet | 260 |
| **Satoshi** | **ITF'nin WOFF2'si, olduğu gibi** | **42.588** | **41,6** | **HAYIR — yasak** | **431** |
| **TOPLAM** | | **98.364** | **96,1** | | |

**→ SIĞIYOR.** 122.880 − 98.364 = **24.516 bayt (23,9 KB) pay kalıyor.** Kesit zorlanmadı.

Okuma notları, uydurmamak için:

- Inter/Geist sayıları **bu ajan tarafından**, 08-07 borusunun **birebir** parametreleriyle
  üretildi (`wght 400-700`, aynı `YALIN_OZELLIKLER`, aynı kod-noktası kümesi) ve depoya değil
  geçici dizine yazıldı. **Bunlar paralel iş akışının hükmü değildir**; o akış Dub'ın daha dar
  isteklerini kullanırsa (Inter 400/500/600, Geist Mono 400/500) sayı **düşer**. Yani 96,1 KB bir
  **TAVAN**dır.
- **Satoshi'nin 41,6 KB'ı sabittir ve toplamın %43'üdür.** Öteki iki yüz kesitle küçülür,
  Satoshi küçülmez. Bütçe bir gün zorlanırsa **ilk düşecek yüz Satoshi olmak zorundadır** —
  çünkü tek sıkıştırılamayan odur.
- Değişim: 79,3 KB → 96,1 KB, **+16,8 KB**. Kapı geçilmiyor ama pay 40,7 KB'dan 23,9 KB'a iniyor.
- Not: subset koşumunda fontTools `meta NOT subset; don't know how to subset; dropped` uyarısı
  verdi (Inter'in `meta` tablosu düşürüldü) — zararsız, dil-etiketi tablosudur.
- **Kaynak sürümler kaydedildi:** Inter `edinme/inter/acilmis/InterVariable.ttf` (Inter 4.1),
  Geist Mono `edinme/geist/extract/GeistMono[wght].ttf` (**v1.7.2**). Ölçüm sırasında paralel
  iş akışı aynı dizine `raw_1.8.0_var.ttf` düşürdü — yani Geist **1.8.0**'a taşınıyor. 16,8 KB'lık
  kesit bir nokta-sürümle anlamlı değişmez ama sayı **1.7.2'nindir**; nihai toplam o akışın
  kendi kaydından alınmalı.

---

## 6 · SATOSHI'NİN BU DEPODAKİ ROLÜ NE OLMALI

`meridian/web/index.html` **okundu, değiştirilmedi.** Tip rampası:

```
114  --sans   : 'Recursive Sans', system-ui, …
115  --display: var(--sans);          ← display yuvası VAR, ama sans'a takma ad
116  --mono   : 'Recursive Mono', ui-monospace, …
426  h1,h2,h3 { font-family:var(--display); font-weight:500; letter-spacing:-.02em; line-height:1.18 }
```

Boy dağılımı (sayım): 12px×29, 13px×28, 11px×27, 10px×21, 14px×14, 20px×5, 17px×3, 24px×1, 28px×1.

`--display` kullanan **tüm** kurallar — yani panonun display başlıklarının tamamı:

| Seçici | Boy | Ağırlık |
|---|---|---|
| `.gate-h` (giriş başlığı) | **24px** | 500 |
| `.greet` | `clamp(24px, 4.6vw, **28px**)` | 500 |
| `.ph` | `clamp(24px, 3.7vw, **28px**)` | 500 |

**Panonun en büyük başlığı 28px.** 28px'in üstünde tek bir metin yok; 28px'teki öteki üç kural
(`.mcard .v`, `.hstat .big`, `.bignum`) zaten `--mono` — başlık değil, **rakam**.

Dub'ın kendi kuralı, DESIGN.md'den, iki kez:

> *"Use Satoshi weight 500 at **36–48px** for display headlines; switch to Inter for everything
> 30px and below"*
> *"Don't use Satoshi at body sizes — Satoshi is **display-only (36px+)**; Inter handles
> everything below 30px"*

Token'lar da öyle: `typography/4xl` 36px, `4xl-2` 40px, `5xl` 48px — **Satoshi'ye bağlı tek tip
stili bunlar**, hepsi ≥36px.

**Yani: bu panoda Satoshi'nin meşru kullanım alanı BOŞ KÜME.** En büyük başlık 28px, Dub'ın
alt sınırı 36px. Aradaki 8px'i kapatmak için ya panonun başlıkları büyütülür (yoğun,
bilgi-yüklü bir işlem panosunda 48px hero başlık = yer israfı ve tasarım yönüne aykırı) ya da
Dub'ın kendi kuralı çiğnenerek Satoshi 24-28px'e indirilir — yani Satoshi'yi almanın gerekçesi
olan tasarım dili, Satoshi'yi o boyda kullanmayı **yasaklıyor**.

Bu depoda **bağımsız bir oturum aynı sonuca varmış**: `docs/TASARIM-YONU-2026-08-24-PANO-V2.md:28`
— *"(Satoshi DÜŞÜRÜLDÜ: CSP harici font yasağı + panoda 36px+ display yok)"*. CSP gerekçesi
bugün **yanlış çıktı** (self-host açıkça izinli, §1.1a), ama 36px gerekçesi **ölçümle doğrulandı**.

**Rol önerisi (uygulanmadı, hüküm operatörde) — üç seçenek, dürüst sırayla:**

1. **ALMA.** Dub'ın kendi ikamesini kullan: DESIGN.md, Satoshi için *"Substitute: Inter (weight
   500, letter-spacing -0.02em)"* diyor — ve `index.html:426` **şu anda tam olarak bunu yapıyor**
   (`font-weight:500; letter-spacing:-.02em`). `--display: var(--inter)` bırakılır, **0 KB**, 0
   lisans riski, 0 belirsizlik, tasarım dilinden **sapma yok** (ikame Dub'ın kendi reçetesi).
2. **AL, AMA YALNIZ LANDING'DE.** `landing.html` bir pazarlama yüzeyidir; 36-48px hero başlık
   orada **anlamlıdır**. Satoshi yalnız o yüzeye yüklenir, `index.html`/`workflow.html`
   dokunulmaz. Bedel 41,6 KB **tek yüzeyde**; belirsizlik (c) hâlâ karşılanmalı.
3. **AL VE HER YERE KOY.** 41,6 KB'ı üç yüzeye ödeyip, Dub'ın *"don't use Satoshi at body sizes"*
   kuralını çiğneyerek 24-28px'te kullanmak. **Önermiyorum.**

**Dürüst görüşüm: (1).** 36-48px başlığı olmayan bir panoya display yüz eklemek ölü ağırlıktır —
ve bu vakada ölü ağırlık ölçülü: **41,6 KB, sıkıştırılamaz, üçlü bütçenin %43'ü**, karşılığında
şu an ekranda **sıfır** karakter. Üstüne kesilemeyen, commit'lenmesi belirsiz, varsayılanı 900
açan, rakamları oransal bir yüz. Operatörün *"tiplerinde satoshi de olması lazım"* isteği
(`docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md:193`) kayıtlı ve meşru; bu yüzden (2) gerçek bir orta
yol — ama (3) savunulamaz. Karar operatörün.

---

## 7 · AÇIK KALANLAR

1. **HÜKÜM (c) OPERATÖRDE:** Satoshi ikilisi git'e commit'lenecek mi, yoksa `.gitignore` +
   depo-dışı dağıtım mı? Metin çözmüyor (§1.1c). Belirsizliği sıfırlayan yol ikincisi.
2. **ROL KARARI OPERATÖRDE:** §6'daki üç seçenek. Ölçüm hazır, hüküm değil.
3. **ITF'DEN YAZILI İZİN İSTENSİN Mİ?** FFL §09 açıkça davet ediyor: *"If a Licensee requires
   additional rights or permissions, **exceptions to any restrictions** under this License,
   modifications or customizations … they may contact Indian Type Foundry to discuss a separate
   custom license."* Kesit izni istenirse 41,6 KB muhtemelen ~15 KB'a iner. **Ajan yazışma
   yapmadı** — dış taraflarla iletişim operatör işidir.
4. **`nameID 13` vs §01 ÇELİŞKİSİ (§1.2)** hukuki olarak çözülmedi; ajan "atıf yaz" diyerek
   maliyetsiz tarafı seçti, ama bu bir yorum, hüküm değil.
5. **TARAYICI TEYİDİ YOK.** Bu turda hiçbir şey tarayıcıda çizilmedi (kapsam dışı; ayrıca
   `tarayici/` dizini paralel iş akışının). Recursive turunun kendi dersi buydu: *"render
   tarayıcı DEĞİL"*. Satoshi alınırsa 500 ağırlığın gerçekten 500 çizildiği, `font-weight:
   300 900` bildiriminin ekseni sürdüğü ve Türkçe aksanların düzgün oturduğu **tarayıcıda**
   ölçülmeli.
6. **`test_dagitim_boyutu_BUTCEDE` üç yüzü saymıyor** (§1.4/4) — bugün Recursive kaydına bakıyor.
   Dub geçişi olursa kapı yeniden kurulmalı, yoksa bütçe sessizce ölçümsüz kalır.
7. **Inter/Geist sayıları geçicidir** (§5): paralel iş akışının kendi kesit kaydı gelince toplam
   yeniden hesaplanmalı.
8. **FFL v2.0 BİR HAFTALIK.** ITF §07'de *"may, at its sole discretion, update, modify, replace
   or discontinue any Font Software"* diyor ve lisans metnini de değiştirebilir. Nüsha
   `lisans/FFL.txt` olarak sha256'sıyla donduruldu; ileride bir tur "lisans hâlâ aynı mı" diye
   bakmak zorunda.

---

## Bu dizinde ne var

```
satoshi/
├── RAPOR.md                     bu dosya
├── olcum.py                     Satoshi'yi OKUR, hiçbir şey üretmez
├── butce.py                     Inter+Geist kesiti + Satoshi tam dosyası → üçlü bütçe
├── kesit_uret.py                08-07 borusunun kopyası — LİSANS KAPISIYLA KAPALI (exit 2)
├── fonts/satoshi.zip            indirilen paket + açılmış Satoshi_Complete/
├── lisans/FFL.txt               ITF FFL v2.0 tam metin (paketten)
├── lisans/WEB-README.md         ITF'nin kendi web kurulum notu
├── woff2/                       BOŞ — kesit üretilmedi, üretilemez (FFL §02)
└── kanit/
    ├── edinme.json              URL + sha256 + API metadata + çelişki kaydı
    ├── satoshi_olcum.json       name/fvar/cmap/Türkçe/özellikler (TTF ve WOFF2)
    ├── butce.json               üçlü bütçe hesabı
    ├── api_list.json            Fontshare API ham cevabı
    └── ffl_page.html            lisans sayfasının ölçülemeyen SPA kabuğu (1744 bayt)
```
