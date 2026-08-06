# YAZI TİPİ ÖLÇÜMÜ — D4 aday seçimi (2026-08-07)

**Statü:** ölçüm + hüküm önerisi. **Bu turda kod/jeton DEĞİŞMEDİ** — uygulama D4 dalgasında, ayrı tur.
**Bağlam:** `docs/TASARIM-YONU-2026-08-07.md` §5 (çıta) · `DESIGN.md` §Typography (Geist için kurulan
BINARY-ÖLÇÜM standardı) · operatör kararı 3 (2026-08-07): **Geist EMEKLİ**, Impeccable'ın
"overused-font" bulgusu kabul edildi.

**Yöntem:** her sayı font ikilisinden okundu — `cmap` varlık kanıtı, `glyf` kontur dökümü, `hmtx`
advance genişlikleri, `GSUB` FeatureList + lookup çözümü, `OS/2` x-height/cap-height, `fvar`
eksenleri. Araç: fontTools 4.63.0. Render: Pillow 12.3.0 / FreeType 2.14.3, iki zeminde gerçek
piksel boyutlarında.

---

## 0. HÜKÜM (özet)

| | Aday | Gerekçe (tek cümle, ölçüme dayalı) |
|---|---|---|
| **KAZANAN** | **Recursive** (Sans Linear + Mono Linear, OFL 1.1, v1.085) | Tek değişken dosyada eşlenik mono (`MONO` ekseni) · sans VE mono **yapısal tabular** (600/1000, üç ağırlıkta da) · `0` varsayılan glifte eğik çizgili (sans'ta da) · `1/l/I` **2/1/3 kontur** ile üçü de yapısal ayrık · havuzun **en düşük gövde kontrastı (1,06)** → iki zeminde en kararlı · 10px'te Türkçe aksanların tamamı ayakta (render kanıtlı) |
| **İKİNCİ** | **Spline Sans + Spline Sans Mono** (OFL 1.1) | Havuzun **en büyük x-height'ı (0,545 → 5,46px@10)** ve cap'i (0,727 → 7,27px@10) — 10-11px'te en çok efektif piksel; tasarlanmış sans+mono çifti; ama `ğ/Ğ` brevesi 10-12px'te **düz çubuğa** iniyor ve sans yapısal tabular değil (`tnum` gerekiyor) |
| ÜÇÜNCÜ | Atkinson Hyperlegible Next + Mono | Ayırt edilebilirlik için tasarlanmış; ama 10-11px'te **ö/ü umlaut noktaları macron'a kaynıyor** ve x/cap havuzun altında (0,496 / 0,668) |

**Elenenler:** Chivo (çıta 4 + 6), Overpass (çıta 6), Source Sans 3 / Source Code Pro (çıta 6).
Gerekçeler §4'te.

**Geist'e göre net bilanço:** kaybedilen tek ölçülebilir şey **0,04px x-height ve 0,10px cap
(10px'te)** ile **+23,3 KB** dosya. Kazanılan: `1`≡`l` çakışmasının kapanması, sans'ta da eğik
çizgili sıfır, sans'ta da yapısal tabular, ve **CSP'nin daralması** (aşağıda). Ayrıntı §6.

---

## 1. Çıta ve nasıl sınandığı

`docs/TASARIM-YONU-2026-08-07.md` §5'teki yedi madde. Her madde için ne okunduğu:

| # | Çıta | Ölçüm yöntemi | Kanıt tablosu |
|---|---|---|---|
| 1 | Kendi-barındırma + açık lisans | `OFL.txt` başlığı + `name` ID 13/14 | §3.1 |
| 2 | Tam Türkçe (ı İ ş ğ ç ö ü + büyükleri) | `cmap` araması + glif kontur sayısı (boş glif ≠ var) | §3.2 |
| 3 | Gerçek tabular rakam | `hmtx` advance (yapısal) **ve** `GSUB` `tnum` lookup çözümü (özellik gerçekten iş yapıyor mu) | §3.3 |
| 4 | `0/O` ve `1/l/I` ayırt edilebilirliği | `glyf` kontur dökümü + bbox, DESIGN.md'nin Geist tablosuyla aynı biçim | §3.4 |
| 5 | Eşlenik mono | resmî kardeş ailenin varlığı + `hmtx`'ten gerçek monospace doğrulaması | §3.5 |
| 6 | Küçük punto + gece zemininde halation | `OS/2` sxHeight/sCapHeight → px; gövde kalınlığı ve gövde kontrastı rasterden; iki zeminde 10/11/12/13px render | §3.6 |
| 7 | Değişken ağırlık (tercih) | `fvar` eksenleri + gerçek dağıtım boyutu (subset + woff2) | §3.7 |

### Ölçümün sınırı — açıkça

- **Render tarayıcı DEĞİL.** Pillow/FreeType ile offline üretildi. Tarayıcı rasterleştirmesi
  (hinting, subpixel, macOS vs Linux) farklıdır. DESIGN.md'nin kendi dersi buydu: geometri
  `1`/`l`'yi karara bağlayamadı, tarayıcı bağladı. **Kazanan aday için D4'te tarayıcı teyit turu
  ZORUNLU** — bu rapor onun yerine geçmez.
- **Pillow'da raqm yok** → render sırasında OpenType özelliği (`tnum`, `zero`) uygulanamıyor.
  Bu yüzden `tnum` iddiası render'la değil, **GSUB lookup'ları çözülüp ikame edilen glifin
  `hmtx` advance'i okunarak** kanıtlandı (§3.3). Beyan değil, ölçüm.

---

## 2. Aday havuzu ve dışlananlar

### Dışlananlar (aday YAPILMADI)

| Aile | Dışlanma nedeni |
|---|---|
| Inter | Impeccable "aşırı kullanılan" listesi **+ operatör reddi (2026-08-01)** |
| Roboto, Fraunces, Plus Jakarta Sans, Space Grotesk | Impeccable "aşırı kullanılan" listesi |
| Geist | Aynı liste + **operatör kararı 3 ile emekli** (yalnız *karşılaştırma tabanı* olarak ölçüldü) |
| IBM Plex | Reddedilen **"CAM KOKPİT"** dünyasının parçası (`PRODUCT.md` brand block) |

### Havuz (9 çift, hepsi OFL 1.1, hepsi değişken)

Kaynak: `github.com/google/fonts` resmî deposu (`ofl/<aile>/`), ham dosya URL'i
`https://raw.githubusercontent.com/google/fonts/main/ofl/<aile>/<dosya>`.

| # | Sans | Mono | Sürüm (sans/mono) | Yukarı akış |
|---|---|---|---|---|
| 1 | Recursive Sans Linear | Recursive Mono Linear | 1.085 (tek dosya) | `github.com/arrowtype/recursive` |
| 2 | Atkinson Hyperlegible Next | Atkinson Hyperlegible Mono | 2.001 / 2.001 | `github.com/googlefonts/atkinson-hyperlegible-next` |
| 3 | Source Sans 3 | Source Code Pro | 3.052 / 1.026 | Adobe |
| 4 | Red Hat Text | Red Hat Mono | 1.030 / 1.030 | `github.com/RedHatOfficial/RedHatFont` |
| 5 | Spline Sans | Spline Sans Mono | 1.001 / 1.004 | `github.com/SorkinType/SplineSans(Mono)` |
| 6 | Noto Sans | Noto Sans Mono | 2.015 / 2.014 | `github.com/notofonts/latin-greek-cyrillic` |
| 7 | Chivo | Chivo Mono | 2.002 / 1.008 | `github.com/Omnibus-Type/Chivo` |
| 8 | Reddit Sans | Reddit Mono | 1.014 / 1.014 | Reddit, OFL |
| 9 | Overpass | Overpass Mono | 4.000 / 4.000 | `github.com/RedHatOfficial/Overpass` |
| — | *Geist* | *Geist Mono* | *1.800 / 1.701* | *taban, aday değil* |

İndirilen dosyalar: `research/olcumler/yazi_tipi_2026-08-07/fonts/` (21 `.ttf`, toplam ~9,4 MB).

---

## 3. Çıta maddesi maddesi ölçüm

### 3.1 Çıta 1 — kendi-barındırma ve lisans

**Dokuz adayın dokuzu da geçiyor.** Hepsi SIL Open Font License 1.1; ticari kısıt yok, dosya
depoya konabilir.

> **Ölçerken çıkan ve bildirilmesi gereken bulgu — çıta 1 bugün İHLAL EDİLİYOR.**
> `docs/TASARIM-YONU-2026-08-07.md` §5 "CSP dış font-host'a izin vermez" diyor. Ölçüldü: izin
> **veriyor**. `deploy/Caddyfile` CSP satırı:
> `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com`
> ve `meridian/web/index.html:11-13`, `landing.html:9-11`, `workflow.html:9-11` üç yüzeyde de
> Google Fonts CDN'ine `<link>` atıyor. Yani **mevcut yazı tipi kendi-barındırılmıyor**; CSP
> onu barındırmak için genişletilmiş. Herhangi bir adaya geçiş, bu iki dış host'u CSP'den
> **çıkarma** fırsatıdır — yani yazı tipi değişimi burada bir maliyet değil, bir **sertleştirme**.
>
> *Doğrulama anı: 2026-08-07 01:02. `index.html` ve `app.js` bu tur sırasında **paralel bir
> oturum tarafından** değiştirildi (mtime 00:57 / 01:02; bu tur o dosyalara dokunmadı). Satır
> numaraları o anda teyit edildi; D4'te uygulamadan önce yeniden bakılmalı.*

### 3.2 Çıta 2 — tam Türkçe

**Dokuz adayın dokuzu da geçiyor**, ve "muhtemelen vardır" yazılmadı: on iki karakterin her biri
`cmap`'te arandı, bulunan glifin konturu sayıldı (boş glif "var" sayılmaz).

| Ölçüm | Sonuç | Kanıt |
|---|---|---|
| ı İ ş Ş ğ Ğ ç Ç ö Ö ü Ü — `cmap`'te | **12/12, on dokuz yüzün hepsinde** | `cmap` best-table araması |
| Glif dolu mu (boş değil) | **hepsinde kontur > 0** | pen ile kontur sayımı (bileşik glifler çözülerek) |
| `ı` gerçekten noktasız mı | **evet** — `dotlessi` konturu `i`'den az | kontur sayısı karşılaştırması |
| `İ` gerçekten noktalı mı | **evet** — `Idotaccent` konturu `I`'den fazla | kontur sayısı karşılaştırması |

> Bu madde **varlık** testidir ve havuzu ayırmıyor. Aksanların 10-11px'te *hayatta kalması* ayrı
> bir sorudur ve havuzu ikiye bölüyor — çıta 6'da (§3.6).

### 3.3 Çıta 3 — gerçek tabular rakam

İki yoldan biri yeterli: **yapısal** (bütün rakamlar aynı advance) ya da **çalışan `tnum`**.
`tnum`'un varlığı yetmez — lookup çözülüp ikame edilen glifin advance'i okundu.

| Aday | Sans varsayılan | Sans `tnum` | Mono varsayılan | Mono gerçek monospace |
|---|---|---|---|---|
| **Recursive** | **yapısal, 600** | yok (gereksiz) | **yapısal, 600** | evet |
| Atkinson | değil | **10 ikame → tekdüze** | yapısal, 632 | evet |
| Source | yapısal, 472 | yok (gereksiz) | yapısal, 600 | evet |
| Red Hat | değil | **10 ikame → 600 tekdüze** | yapısal, 600 | evet |
| Spline | değil | **10 ikame → tekdüze** | yapısal, 1200 | evet |
| Noto | yapısal, 572 | **var ama ATIL** | yapısal, 600 | evet |
| Chivo | yapısal, 615 | **var ama ATIL** | yapısal, 600 | evet |
| Reddit | değil | **10 ikame → tekdüze** | yapısal, 1152 | evet |
| Overpass | değil | **10 ikame → tekdüze** | yapısal, 1232 | evet |
| *Geist (taban)* | *değil* | *10 ikame → tekdüze* | *yapısal, 600* | *evet* |

**Ağırlığa göre de doğrulandı:** advance'ler `HVAR` üzerinden değişebildiği için 400/500/700'de
ayrı ayrı örneklendi — **on dokuz yüzün hepsinde tabular tekdüzelik üç ağırlıkta da korunuyor.**

**Üç atıl-özellik bulgusu** (DESIGN.md'nin `cv11`/`ss01` dersinin aynısı — beyan iş yapmıyor):

- **Noto Sans ve Chivo'da `tnum` ATIL**: özellik var, ama varsayılan rakamlar zaten tabular
  olduğu için sıfır glif ikame ediyor.
- **Red Hat Text'te `slashed-zero` TEK BAŞINA ATIL**: `zero` özelliği yalnız `zero.tf →
  zero.tf.slash` eşlemesi taşıyor — yani **önce `tabular-nums` açılmazsa eğik çizgi hiç
  gelmiyor.** İkisi birlikte beyan edilmeli. (Aday sıralamasında bu bir tuzak kalemi.)

### 3.4 Çıta 4 — `0/O` ve `1/l/I` ayırt edilebilirliği

DESIGN.md'nin Geist tablosuyla **aynı biçim**: kontur sayısı / nokta sayısı / bbox / 10px'te px.

#### `0` vs `O` (mono yüzler)

| Aday | Varsayılan glifte işaret | İşaretin türü (kontur dökümü) | `0` ile `O` genişlik farkı |
|---|---|---|---|
| **Recursive** | **VAR** (3 kontur, `O` 2) | eğik çizgi, 22 nokta, bbox x[96,485] y[122,591] — köşeden köşeye | −0,16px@10 |
| Atkinson | VAR (3 kontur) | **bölünmüş sayaç**: iki 335×499 sayaç çapraz kaydırılmış → aradaki boşluk çizgiyi kuruyor | −0,46px@10 |
| Source | VAR (3 kontur) | **nokta**, 13 nokta, 104×116, merkezde | −0,56px@10 |
| Red Hat | VAR (3 kontur) | bölünmüş sayaç (2×281×499, çapraz) | −0,10px@10 |
| Spline | VAR (3 kontur) | **nokta**, 13 nokta, 196×275 | −0,12px@10 |
| Noto | VAR (3 kontur) | **eğik çizgi**, 4 nokta, 332×526 | −0,30px@10 |
| **Chivo** | **YOK (2 kontur)** | işaret yok — düz oval | −0,50px@10 |
| Reddit | VAR (3 kontur) | eğik çizgi, 4 nokta, 794×766 (≈45°) | −0,31px@10 |
| Overpass | VAR (3 kontur) | nokta, 13 nokta, 252×252 | +0,30px@10 |
| *Geist Mono* | *VAR (3 kontur)* | *eğik çizgi, 4 nokta, x[120,480] y[98,612]* | *−0,24px@10* |

> Geist Mono satırı DESIGN.md'nin kaydıyla (4 noktalı paralelkenar, x[124,476] y[101,609])
> uyuşuyor; küçük fark DESIGN.md'nin **Medium (500)** kesitini, buranın **VF varsayılanını (400)**
> ölçmesinden. **Ölçüm hattı bu uyumla doğrulanmış sayılır.**

#### `1` vs `l` vs `I` (mono yüzler) — DESIGN.md'nin "zayıf, sertifikalanamaz" dediği çift

| Aday | kontur `1`/`l`/`I` | nokta `1`/`l`/`I` | yükseklik `1`/`l`/`I` | `\|1w−lw\|` |
|---|---|---|---|---|
| **Recursive** | **2 / 1 / 3** | 93 / 60 / 60 | 710 / 750 / 700 | 0,10px@10 |
| **Reddit** | **2 / 1 / 3** | 12 / 18 / 12 | 1474 / 1556 / 1474 | **0,57px@10** |
| Spline | 3 / 1 / 1 | 25 / 23 / 18 | 1454 / **1571** / 1454 | 0,39px@10 |
| Overpass | 2 / 3 / 3 | 10 / 12 / 12 | 1408 / 1444 / 1400 | 0,49px@10 |
| Noto | 2 / 1 / 1 | 20 / 10 / 12 | 714 / 760 / 714 | 0,37px@10 |
| Source | 1 / 1 / 1 | 14 / 19 / 12 | 640 / 734 / 660 | 0,30px@10 |
| Red Hat | 1 / 1 / 1 | 11 / 19 / 12 | 700 / 737 / 700 | 0,03px@10 |
| Chivo | 1 / 2 / 1 | 14 / 10 / 12 | 696 / 721 / 686 | 0,04px@10 |
| Atkinson | 1 / 1 / 1 | 14 / 15 / 12 | 668 / 708 / 668 | 0,02px@10 |
| *Geist Mono* | *2 / **2** / 1* | *15 / 16 / 12* | ***710 / 710** / 710* | ***0,00px@10*** |

> **Geist Mono'nun ölçülmüş kusuru burada tekrar doğrulandı ve büyüdü:** `1` ile `l` **aynı
> genişlikte (480), aynı yükseklikte (710), aynı kontur sayısında (2)**. 28px render'da bile
> ayrılmıyorlar (`karsilastirma_mono_28px_w400_gece.png`, son satır: `0O1lI` → `0O11I` okunuyor).
> DESIGN.md bunu "etiketler UPPERCASE olduğu için `l` hiç render edilmiyor" diyerek yönetmişti;
> bu bir **kaçınma**, çözüm değil, ve `code`/tanımlayıcı yüzeylerinde açık kalıyor.

**Ayrıca ölçülen, DESIGN.md'de olmayan bulgu — Geist *Sans*'ın sıfırı işaretsiz.** Geist Sans
`zero` 2 kontur (çizgi yok), `zero` GSUB özelliği de **yok**; `0` ile `O` arası fark 86 birim
(0,86px@10). Yani `0/O` ayrımı bugün **yalnızca "her rakam mono" kuralı sayesinde** ayakta.
Recursive'de bu kural bozulsa bile sans'ın sıfırı eğik çizgili.

#### `slashed-zero` beyanı — hangi adayda iş yapıyor

| Aday (mono) | `zero` özelliği | Gerçekte ne yapıyor |
|---|---|---|
| **Recursive** | var | **ATIL** — `zero → zero.slash` eşliyor ama **iki glifin konturları birebir aynı**; varsayılan sıfır zaten çizgili |
| Spline | var | **iş yapıyor** — 13 noktalı **nokta**'yı 4 noktalı **eğik çizgi**yle değiştiriyor (gerçek bir seçim) |
| Red Hat | var | **yalnız `tnum` ile birlikte** (§3.3) |
| Geist Mono | **yok** | — (DESIGN.md zaten "beyan etme" diyor) |

> Recursive için sonuç **DESIGN.md'nin mevcut hükmüyle birebir aynı**: eğik çizgi opsiyonel
> değil, varsayılan glifte. "The Tabular Rule"un `slashed-zero`ya güvenme yasağı **olduğu gibi
> kalır** — gerekçesi de aynı kalır. Süreklilik açısından bu bir kolaylık.

### 3.5 Çıta 5 — eşlenik mono

**Dokuz adayın dokuzunda da resmî mono kardeş var** ve dokuzunun da monospace olduğu `hmtx`'ten
doğrulandı (0-9 + A-Z + a-z + noktalama örnekleminde tek advance değeri).

**Recursive burada nitelik olarak ayrışıyor:** kardeş ayrı bir aile değil, **aynı değişken
dosyadaki `MONO` ekseni** (0 = sans, 1 = mono). Yani "tasarım-uyumlu" bir eşlenik değil,
*aynı tasarımın* iki kesiti — çıta maddesinin verilebilecek en güçlü cevabı.

Eksenler: `MONO 0-1 · CASL 0-1 · wght 300-1000 · slnt −15-0 · CRSV 0-1`.
Ölçüm için `MONO/CASL/slnt/CRSV` sabitlenip `wght` canlı bırakıldı → iki dosya
(`RecursiveSansLinear-VF.ttf`, `RecursiveMonoLinear-VF.ttf`, ~500 KB ham TTF).

### 3.6 Çıta 6 — küçük punto ve gece zemini

#### Ölçülen metrikler

| Aday | x-height / em | **10px'te** | **11px'te** | cap / em | **10px** | **11px** | gövde (`l`, w400) | **gövde kontrastı** |
|---|---|---|---|---|---|---|---|---|
| **Spline** | **0,545** | **5,46px** | **6,00px** | **0,727** | **7,27px** | **8,00px** | 98/1000 | 1,16 |
| Noto | 0,536 | 5,36px | 5,90px | 0,714 | 7,14px | 7,85px | 90 | 1,25 |
| *Geist* | *0,530* | *5,30px* | *5,83px* | *0,710* | *7,10px* | *7,81px* | *85* | *1,10* |
| **Recursive** | **0,526** | **5,26px** | **5,79px** | **0,700** | **7,00px** | **7,70px** | 90 | **1,06** ← en düşük |
| Reddit | 0,518 | 5,18px | 5,69px | 0,720 | 7,20px | 7,92px | 85 | 1,09 |
| Chivo | 0,511 | 5,11px | 5,62px | 0,686 | 6,86px | 7,55px | **100** ← en ağır | **1,50** ← en yüksek |
| Overpass | 0,511 | 5,11px | 5,62px | 0,700 | 7,00px | 7,70px | 80 | 1,09 |
| Atkinson | 0,496 | 4,96px | 5,46px | 0,668 | 6,68px | 7,35px | 85 | 1,26 |
| Red Hat | 0,488 | 4,88px | 5,37px | 0,700 | 7,00px | 7,70px | **72** ← en ince | 1,11 |
| **Source** | **0,478** ← en küçük | **4,78px** | **5,26px** | **0,660** ← en küçük | **6,60px** | **7,26px** | 82 | 1,25 |

**Halation okuması.** Gece zemininde açık glif koyu zemine *taşar* (bloom); risk **toplam
mürekkeple** ve **gövde kontrastıyla** birlikte büyür. Kontrast ayrıca iki-zemin sistemini
doğrudan ilgilendirir: yüksek kontrastlı bir yüzde ince parçalar gündüz zemininde yenilir,
kalın parçalar gece zemininde taşar — yani **harf karakteri zemine göre değişir**, ki bu
"iki zemin, tek ürün, yeniden öğrenme yok" kuralının ihlalidir.
→ **Recursive (1,06) havuzun en monolineer yüzü**; Chivo (1,50) en riskli.

#### Türkçe aksanların 10-11px'te hayatta kalması — render kanıtı

`turkce_sans_w400_{gunduz,gece}.png` ve `etiket_idiomu_10px_w700_{gunduz,gece}.png`
(6× nearest-neighbour). `ö o ü u ğ g ş s ç c ı i İ I` dizisi, 10/11/12/13px.

| Aday | 10px'te `ö`/`ü` iki nokta | 10px'te `ğ` brevesi | Not |
|---|---|---|---|
| **Recursive** | **ayrık — ikisi de** | **kavisli, ayrık** | havuzun en temizi; her işaret 10px'te ayakta |
| Spline | ayrık | **düz çubuğa iniyor** (10-12px) | boyut avantajı büyük, breve zayıf |
| Chivo | ayrık | **koyu lekeye dönüyor** | en ağır gövde + en yüksek kontrast |
| Noto | **macron'a kaynıyor** | düz çubuk | 11px'te düzeliyor |
| Red Hat | **macron'a kaynıyor** | tamam | 11px'te düzeliyor |
| Atkinson | **macron'a kaynıyor (10 ve 11)** | tamam | ironik: okunabilirlik için tasarlanmış yüz |
| Reddit | **macron'a kaynıyor** | düz çubuk | ayrıca sönük |
| **Overpass** | **10 VE 11px'te kaynıyor** | — | etiket idiomunda `ÖLÇÜLEMEDİ` → `ŌLÇŪLEMEDİ` |
| Source | zayıf/sönük | tamam | havuzun en küçük x ve cap'i |
| *Geist* | *kısmen kaynıyor* | *10px'te zayıf* | — |

> **Sistemin imza idiomu mono 10px/700 UPPERCASE**'tir (`DESIGN.md` §Hierarchy). Yani sahaya
> çıkan asıl sınav büyük harfli `İ Ş Ğ Ç Ö Ü`'dür. `etiket_idiomu_10px_w700_gece.png`:
> Recursive'de `AÇIK RİSK · GÜNLÜK KÂR · ÖLÇÜLEMEDİ · SIĞ ÖRNEKLEM` altı etiketin tamamı
> temiz; Overpass'ta `Ö`/`Ü` düzleşiyor; Source görünür biçimde sönük.

### 3.7 Çıta 7 — değişken ağırlık ve gerçek dağıtım boyutu

**Dokuz adayın dokuzu da değişken.** Boyut iddiası varsayılmadı — Latin-1 + Türkçe + konsolun
kullandığı sembollere subset edilip woff2'ye çevrildi, **iki farklı özellik kümesiyle**:

| Çift | tüm özellikler (woff2) | **yalın** (yalnız kullanılan özellikler) | Geist'e fark |
|---|---|---|---|
| **Recursive** | 151,3 KB | **77,4 KB** | **+23,3 KB** |
| **Spline** | 84,0 KB | **64,6 KB** | +10,5 KB |
| Atkinson | 37,9 KB | — | −16,2 KB |
| *Geist (mevcut)* | *54,1 KB* | — | — |

> Yalın küme: `ccmp locl kern mark mkmk rlig calt tnum zero case`. Recursive'i iki katına
> çıkaran şey gövde değil, kullanılmayan alternatif kümeleri (`ss01…`, `afrc`, `pnum` varyantları).
>
> **Ve bu +23,3 KB'ın karşılığı sadece harf değil:** bugün fontlar `fonts.googleapis.com` +
> `fonts.gstatic.com`'dan geliyor — **iki ek DNS + iki TLS el sıkışması + render-blocking bir CSS
> isteği**. Aynı origin'den 77,4 KB, iki üçüncü-taraf origin'den 54,1 KB'tan büyük olasılıkla
> **daha hızlıdır**; üstelik CSP'den iki host düşer (§3.1).

---

## 4. Elenenler ve nedenleri

| Aday | Elendiği çıta | Ölçülmüş neden |
|---|---|---|
| **Chivo + Chivo Mono** | **4 ve 6** | (4) Mono'nun `0`'ı **varsayılan glifte işaretsiz** — `zero` 2 kontur, `O` 2 kontur; ayrım tamamen `slashed-zero` beyanına bağlı, yani bir CSS satırı silinirse `0/O` çöker. (6) Havuzun **en ağır gövdesi (100/1000)** ve **en yüksek gövde kontrastı (1,50)**; 10px'te `ğ` ve `ş` render'da lekeye dönüyor → gece zemininde halation profili en kötü. |
| **Overpass + Overpass Mono** | **6** | 10px **ve** 11px'te `ö`/`ü` umlaut noktaları macron'a kaynıyor; etiket idiomunda (mono 10px/700 UPPERCASE) `ÖLÇÜLEMEDİ` → `ŌLÇŪLEMEDİ` okunuyor. Türkçe bir ürün bunu sahaya süremez. |
| **Source Sans 3 + Source Code Pro** | **6** | Havuzun **en küçük x-height'ı (0,478 → 4,78px@10)** ve **en küçük cap'i (0,660 → 6,60px@10)**. 10px/700 gece etiket sayfasında görünür biçimde en sönük satır. Yoğun-veri arayüzünün tamamı 10-13px'te yaşıyor; %14 daha küçük efektif boy bedelsiz değil. |

**Çıtayı geçen ama sıralamada altta kalanlar** (elenmedi, ikinci turda gerekirse):

- **Noto Sans + Noto Sans Mono** — metrikler iyi (x 0,536), ama 10px'te umlaut kaynaması var,
  mono etiket boyunda geniş (satır taşıyor), ve dosyalar havuzun en büyüğü (2,0 + 1,7 MB ham).
  Ayrıca *seçilmiş* değil *varsayılan* okunur — Impeccable'ın itirazının ruhuna aykırı.
- **Reddit Sans + Reddit Mono** — `1/l/I` ayrımı havuzun en iyisi (0,57px@10, 2/1/3 kontur),
  ama 10px'te aksanlar kaynıyor ve sönük.
- **Red Hat Text + Red Hat Mono** — en ince gövde (72), düşük kontrast (1,11); ama x-height 0,488
  (sondan ikinci), 10px'te umlaut kaynaması, ve `slashed-zero`nun `tnum`'a zincirlenmiş olması
  bir tuzak.
- **Atkinson Hyperlegible Next + Mono** — üçüncü sıra; §0'da gerekçesi.

---

## 5. Kazanan — Recursive (Sans Linear + Mono Linear)

`gereksinim | bulgu | kanıt` biçiminde, DESIGN.md §Typography'nin Geist tablosuyla aynı standartta.

| Gereksinim | Bulgu | Kanıt |
|---|---|---|
| Kendi-barındırma, açık lisans | **Karşılanıyor.** SIL OFL 1.1, ticari kısıt yok. Yukarı akış `github.com/arrowtype/recursive`, Google Fonts `ofl/recursive`. | `OFL.txt` satır 3; `upstream_info.md` |
| Tam Türkçe | **Karşılanıyor, 12/12.** ı İ ş Ş ğ Ğ ç Ç ö Ö ü Ü hepsi `cmap`'te ve dolu. `ı` noktasız (kontur `i`'den az), `İ` noktalı (kontur `I`'den fazla) — yapısal olarak doğru, varsayım değil. | `cmap` + kontur sayımı |
| Rakamlar kaymıyor | **Karşılanıyor, yapısal — hem mono hem SANS.** Her rakamın advance'i **600/1000**; 400, 500 ve 700 ağırlıklarında da tekdüze. Sans'ta da 600 → sans rakam sütunu bile hizalı. | `hmtx` advance; `HVAR` üzerinden üç ağırlıkta örnekleme |
| `tabular-nums` özelliği | **Yok — ve gereksiz.** GSUB'da `tnum` yok, çünkü hizalama zaten yapısal. Beyan **atıl** kalır ve yalnız `ui-monospace` yedeği için savunma amaçlı tutulur. *(Geist Mono ile birebir aynı durum.)* | GSUB FeatureList |
| Ayrıştırılmış sıfır | **Karşılanıyor, varsayılan glifte, sans'ta da.** `zero` 3 kontur, `O` 2 kontur; fazlalık kontur bbox x[96,485] y[122,591] — kaseyi köşeden köşeye kesen eğik çizgi. | `glyf` kontur dökümü + render |
| `slashed-zero` özelliği | **Var ama ATIL.** `zero → zero.slash` eşlemesi var, ancak iki glifin konturları **birebir aynı**. Beyan etme — DESIGN.md'nin mevcut yasağı **değişmeden geçerli**. | GSUB lookup çözümü + iki glifin kontur karşılaştırması |
| `0` vs `O` | **Ayrık.** Çizgi var; `0` ayrıca 16 birim dar (0,16px@10). | kontur bbox |
| `1` vs `I` | **Ayrık.** `1` = 2 kontur (eğik bayrak, ayak tırnağı yok); `I` = **3 kontur** (üst ve alt tırnak). | kontur dökümü |
| **`1` vs `l`** | **AYRIK — ve bu Geist'e göre asıl kazanç.** `1` = 2 kontur / 93 nokta / 710 yüksek; `l` = **1 kontur** / 60 nokta / **750 yüksek** (kavisli sağ kuyruk). Kontur sayısı, yükseklik ve biçim üçü birden ayrışıyor. Geist Mono'da bu çift **birebir aynıydı**. | kontur dökümü + 28px render |
| Küçük punto metrikleri | x-height 526/1000 → **5,26px@10**, 5,79px@11. Cap 700/1000 → **7,00px@10**, 7,70px@11. | `OS/2` v4 `sxHeight`, `sCapHeight` |
| Gece zemini / halation | **Havuzun en iyisi.** Gövde kontrastı **1,06** — en monolineer yüz; gövde 90/1000 (orta). Harf karakteri iki zemin arasında değişmiyor. | raster gövde/kontrast ölçümü + iki zemin render |
| 10px'te Türkçe | **Havuzun en iyisi.** `ö`/`ü` noktaları ayrık, `ğ` brevesi kavisli ve ayrık, `ş`/`ç` sedilleri okunur — 10px'te, her iki zeminde. | 6× render sayfaları |
| Eşlenik mono | **En güçlü biçimde karşılanıyor.** Ayrı aile değil, **aynı değişken dosyanın `MONO` ekseni**. | `fvar`: `MONO 0-1` |
| Değişken ağırlık | **Var.** `wght 300-1000` (+ sabitlenen `CASL`, `slnt`, `CRSV`). Yalın woff2 çifti **77,4 KB**. | `fvar` + subset/woff2 ölçümü |

**Hüküm: Recursive önerilir.** Gerekçe ölçüye dayanıyor: (a) Geist'in tek ölçülmüş tipografik
kusurunu — `1`≡`l` — kapatan, (b) tabular ve eğik-çizgili-sıfır garantilerini **özellik bayrağıyla
değil yapıyla** veren (DESIGN.md'nin "daha güçlü garanti" ölçütünün ta kendisi), (c) iki zeminli
bir sistemde havuzun **en kararlı** yüzü (kontrast 1,06), (d) 10px Türkçe'de havuzun **en temizi**,
ve (e) eşlenik mono maddesini bir kardeş aileyle değil **aynı dosyayla** karşılayan tek aday.

**İkinci: Spline Sans + Spline Sans Mono.** Tek üstünlüğü ölçülebilir ve ciddi — havuzun en büyük
x-height/cap'i (10px'te %4 daha fazla efektif boy), ve daha küçük (64,6 KB). Kazanamamasının nedeni
de ölçülü: `ğ/Ğ` brevesi 10-12px'te düz çubuğa iniyor (Türkçe bir üründe `g`/`ğ` ayrımı taşıyan
işaret), sans'ta yapısal tabular yok, ve sans sıfırı varsayılan glifte işaretsiz.

---

## 6. Geist'e göre kaybedilen ve kazanılan — sayıyla

Operatörün istediği dürüst muhasebe. **Bedelsiz bir değişim değil.**

### Kaybedilenler

| Kalem | Geist | Recursive | Fark |
|---|---|---|---|
| x-height (10px'te) | 5,30px | 5,26px | **−0,04px** |
| x-height (11px'te) | 5,83px | 5,79px | −0,04px |
| Cap height (10px'te) | 7,10px | 7,00px | **−0,10px** |
| Cap height (11px'te) | 7,81px | 7,70px | −0,11px |
| Dağıtım boyutu (yalın woff2 çifti) | 54,1 KB | 77,4 KB | **+23,3 KB** |
| Ham TTF (sabitlenmiş kesitler) | 341 KB | 1000 KB | +659 KB (dağıtıma girmez) |

> Kayıp kalemi gerçek ama küçük: 10px'te **onda bir pikselden az** x-height, cap'te onda bir
> piksel. Boyut kalemi tek seferlik ve §3.7'deki CDN argümanıyla büyük olasılıkla net kazanç.

### Kazanılanlar

| Kalem | Geist | Recursive |
|---|---|---|
| **`1` vs `l` (mono)** | **çakışık** — aynı genişlik (480), aynı yükseklik (710), aynı kontur (2); 0,00px fark | **ayrık** — 2 vs 1 kontur, 710 vs 750 yükseklik, kavisli kuyruk |
| Sans'ta eğik çizgili `0` | **yok** (2 kontur, `zero` özelliği de yok) | **var** (3 kontur, varsayılan glifte) |
| Sans'ta yapısal tabular | **yok** (`tnum` gerekiyor) | **var** (600, üç ağırlıkta) |
| Gövde kontrastı (iki zemin kararlılığı) | 1,10 | **1,06** |
| 10px Türkçe aksan bütünlüğü | kısmen kaynıyor | **tamamı ayakta** |
| Eşlenik mono ilişkisi | ayrı aile (Geist / Geist Mono) | **aynı dosya, `MONO` ekseni** |
| Kendi-barındırma | **hayır** — CDN'den, CSP genişletilmiş | evet — CSP'den 2 dış host düşer |
| `slashed-zero` beyanının durumu | atıl (özellik yok) | atıl (özellik var ama aynı glif) — **hüküm değişmiyor** |

### Değişmeyenler (taşınan hükümler)

- **The Ramp Rule** (dokuz basamak) — dokunulmuyor.
- **The Tabular Rule** — metni bile değişmiyor: hizalama yine yapısal, `tabular-nums` yine
  savunma amaçlı, `slashed-zero`ya yine güvenilmiyor. Yalnız font adı değişir.
- **The Label-Above Rule** — dokunulmuyor.
- Ağırlık disiplini (başlık 500, rakam 400) — Recursive `wght 300-1000` bunu karşılıyor.

---

## 7. D4 uygulama turuna devredilen kalemler (bu turda YAPILMADI)

1. **İSİM ÇAKIŞMASI — bloke edici.** Sabitlenen iki kesit **aynı isim kaydını taşıyor**:
   her ikisinde de `nameID1 = "Recursive Sans Linear Light"`,
   `postscript = "Recursive-SansLinearLight"`. Bu hâliyle self-host edilirse `font-family`
   çözümü çakışır ve mono kaybolur. Kesitler `updateFontNames=True` ile ya da `name` tablosu
   elle düzenlenerek **"Recursive Sans" / "Recursive Mono"** olarak yeniden adlandırılmalı.
2. **Tarayıcı teyit turu — ZORUNLU.** Bu raporun render'ları Pillow/FreeType. DESIGN.md'nin
   kendi hükmü tarayıcıda kapandı; kazanan da tarayıcıda (10/11/12/13/28px, iki zemin)
   teyit edilmeli. Özellikle `1`/`l` ve 10px aksanlar.
3. **CSP daraltma:** `deploy/Caddyfile`'dan `https://fonts.googleapis.com` (style-src) ve
   `https://fonts.gstatic.com` (font-src) çıkarılır; `meridian/web/{index,landing,workflow}.html`
   içindeki üçer satırlık preconnect + stylesheet `<link>`'leri silinir; `@font-face` eklenir.
4. **Belge güncellemesi:** `DESIGN.md` §Typography (Geist tabloları → Recursive tabloları),
   `PRODUCT.md` brand block ("Geist + Geist Mono" incumbent ifadesi).
5. **Varsayılan ağırlık notu:** Recursive'in `wght` varsayılanı **300**'dür (400 değil).
   CSS her yerde ağırlığı açıkça verdiği için sorun yok, ama `@font-face` ve `font-weight`
   eşlemesi bu varsayımla sınanmalı.
6. Yalın subset kümesi (`ccmp locl kern mark mkmk rlig calt tnum zero case`) build adımına
   yazılmalı — aksi hâlde dosya iki katına çıkar.

---

## 8. Üretilen dosyalar

**Fontlar (indirilen + türetilen):** `research/olcumler/yazi_tipi_2026-08-07/fonts/`
21 `.ttf` — 19 indirilen (Google Fonts `ofl/`, OFL 1.1) + 2 türetilen
(`RecursiveSansLinear-VF.ttf`, `RecursiveMonoLinear-VF.ttf`; `MONO/CASL/slnt/CRSV` sabitlenmiş).

**Dağıtım denemesi:** `research/olcumler/yazi_tipi_2026-08-07/woff2/` — subset + woff2,
`.subset.woff2` (tüm özellikler) ve `.lean.woff2` (yalnız kullanılan özellikler).

**Render örnekleri:** `research/olcumler/yazi_tipi_2026-08-07/render/` (64 PNG)

| Dosya | Ne gösteriyor |
|---|---|
| `<Aday>_{gunduz,gece}.png` | 1:1 tam künye: etiket idiomu, 28px rakam, 12px hizalı sayı sütunu + hiza cetveli, 10/11/12/13px ayırt-etme dizisi, Türkçe, gövde metni, başlık |
| `<Aday>_{gunduz,gece}_zoom4x.png` | 4× yakınlaştırma: `0O 1lI Il1 O0` ve sayılar, 10/11px × 400/700 |
| `karsilastirma_{mono,sans}_{10,11}px_w{400,700}_{gunduz,gece}.png` | Tüm adaylar yan yana, aynı dizi, aynı boy |
| `karsilastirma_mono_28px_w400_{gunduz,gece}.png` | 28px'te ayırt-etme — Geist'in `1`≡`l` çakışması burada da görülüyor |
| `turkce_{sans,mono}_w{400,700}_{gunduz,gece}.png` | **6×** aksan sınavı: `ö o ü u ğ g ş s ç c ı i İ I`, 10/11/12/13px |
| `etiket_idiomu_10px_w700_{gunduz,gece}.png` | **6×** imza idiomu: mono 10px/700 UPPERCASE 0,16em, gerçek Türkçe etiketler |
| `sifir_isareti_sans_vs_mono_48px.png` | 48px'te `0O 1lI` — **Recursive'in sans'ında da çizgi var**; **Geist Sans'ta `0` ile `O` ayırt edilemiyor** ve `1`≡`l`; Spline sans'ında da sıfır işaretsiz |

**Zemin değerleri (render'da kullanılan):** gündüz `#ffffff` / ink `#050505` / mut `#8f8b86`;
gece `#1E1E1E` / ink `#D4D4D4` / mut `#8a8580` — `PRODUCT.md` brand block'tan.
