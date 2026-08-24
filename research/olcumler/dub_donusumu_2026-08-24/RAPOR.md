# Dub dönüşümü · jeton katmanı ölçümü — 2026-08-24

_Üreten: `research/olcumler/dub_donusumu_2026-08-24/olc.py` · elle yazılmış tek bir oran YOK._
_Dub kaynağı: `/Users/erdemozturk/Downloads/tokens.json`._

## 0 · Dub'da karanlık tema YOK — doğrulandı

Karar §1.2 iddiası ölçüldü: dört Dub dosyası ikinci bir renk katmanını AÇAN mekanizma
için tarandı (`prefers-color-scheme`, `[data-theme`, `.dark`, `color-scheme:dark`).

| dosya | karanlık-tema mekanizması |
|---|---|
| `tokens.json` | YOK |
| `DESIGN.md` | YOK |
| `variables.css` | YOK |
| `theme.css` | YOK |

Yani GECE PALETİ TÜRETİLDİ ve tokens.json'da `$extensions.org.meridian.turetme`
damgasını taşır. Türetme TERS ÇEVİRME DEĞİLDİR (tint-yönü kuralı): kroma taşıyan her
jeton gece için AYRI ölçüldü ve gece para renkleri naif tersin vereceğinden AÇIKTIR.

## 1 · Ö1-Ö7 · eşikler ve sonuç

| Ö | soru | ölçülen | eşik | hüküm |
|---|---|---|---|---|
| Ö1 | `#fafafa` zemin parlama kısıtı | en büyük yüzey Y=0.956 (saf beyaz 1.0) · kart/zemin adımı 1.0438 | Y<1.0 · adım ≥1.02 | TUTTU |
| Ö2 | para renkleri kendi %10 tinti üstünde | en düşük 4.503 (iki tema, yedi yüzey) | ≥4.5 | TUTTU |
| Ö3 | gezinme kroması | mürekkep C(nav)=0.2152 / 0.1458 · min C(şiddet)=0.0921 / 0.0809 | C(nav) < min C(şiddet) | **TUTMADI** |
| Ö4 | `--nav` ↔ `--dv-n2` ayrımı | 3.655 / 3.41 | ≥3.0 | TUTTU |
| Ö5 | `--nav` mürekkebi kendi washı üstünde | 4.239 / 5.778 | ≥4.5 | **TUTMADI** |
| Ö6 | tip rampası adımları | karar rampası [1.2727, 1.1429, 1.25, 1.2, 1.25] | her adım ≥1.15, en az bir ≥1.25 | **TUTMADI** |
| Ö7 | odak halkası (`--sh-ring`) | 1.234-1.31 | ≥3.0 | **TUTMADI** |

### Tutmayanlar — DEĞER ZORLANMADI, KULLANIM YÜZEYİ DARALDI (karar §2.1)

**Ö3 · gezinme kroması.** Elektrik mavisi doygundur: C(--nav)=0.2152 > min C(şiddet)=0.0921 (gündüz). Jeton UYDURULMADI.
Daraltma: gezinmenin BÜYÜK YÜZEYİ washtır (`--nav-t`, C=0.0328) ve o tavanın çok altındadır — dolgu tavanı TUTAR. `--nav`/`--nav-2`
yalnız İNCE mürekkep (3px seçim çubuğu, sayaç hapı dolgusu, bağlantı metni) taşır;
bir para değeri, bir alarm, bir yön ASLA mavi olmaz (karar §2.1).

**Ö5 · wash üstünde mürekkep.** `--nav` (electric-blue) `--nav-t` üstünde 4.239 (gündüz) — AA ALTI.
Daraltma (karar §2.1'in kendi cümlesi: *dolgu washı kalır, mürekkep koyulaşır*):
wash üstündeki mürekkep `--nav-2` (deep-sapphire) olur — ölçüldü 7.155 / 8.871, AA. `.sitem.on` kuralı bu yüzden
`color:var(--nav-2)` okur, `var(--nav)` DEĞİL.

**Ö6 · tip rampası.** Karar §3'ün rampası [11, 14, 16, 20, 24, 30]: adımlar [1.2727, 1.1429, 1.25, 1.2, 1.25] — 16/14=1.1429 eşiğin (1.15) ALTINDA.
Daraltma (16 → 17 (16 ve 18 düşer, 17 rampaya girer)): kalan rampa [11, 14, 17, 20, 24, 30], adımlar [1.2727, 1.2143, 1.1765, 1.2, 1.25] — TUTTU.
  · aday *16 → 17 (16 ve 18 düşer, 17 rampaya girer)* → [11, 14, 17, 20, 24, 30] adımlar [1.2727, 1.2143, 1.1765, 1.2, 1.25] — TUTTU
  · aday *16 tamamen düşer* → [11, 14, 20, 24, 30] adımlar [1.2727, 1.4286, 1.2, 1.25] — TUTTU

**Ö7 · odak halkası.** Dub'ın `shadow-subtle-2` halkası (`rgba(0,0,0,.1) 0 0 0 4px`) her zeminde 3:1'in ALTINDA (ölçülen aralık 1.234-1.31).
Değer ZORLANMADI (Dub jetonu alfası kımıldatılmadı). Daraltma: `--sh-ring` bir ODAK
GÖSTERGESİ DEĞİLDİR, onu ÇEVRELEYEN yardımcı halkadır. G4'ü taşıyan gösterge
`:focus-visible` üzerindeki **2px `--accent` ana hattı**dır ve o ölçüldü: 10.78-19.798 — TUTTU.

## 2 · Türetilen jetonlar — hangi kural, kaç adım

| jeton | tema | kaynak | sonuç | L adımı | kroma | kural |
|---|---|---|---|---|---|---|
| `--green` | gunduz | Dub vivid-green `#16a34a` | `#1f7646` | 0 | 0.1114 (kaynak 0.1699) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 154.4° kroma 0.1111 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--amber` | gunduz | Dub tangerine `#ea580c` | `#77520e` | 0 | 0.0921 (kaynak 0.1943) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 76.9° kroma 0.0917 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--red` | gunduz | maket beyanlı türetmesi loss-red (Dub'da kayıp rengi YOK) `#c2410c` | `#9a0019` | 0 | 0.175 (kaynak 0.1739) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 24.1° kroma 0.1782 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--green` | gece | Dub vivid-green `#16a34a` | `#61b37f` | 0 | 0.1118 (kaynak 0.1699) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 154.4° kroma 0.1111 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--amber` | gece | Dub tangerine `#ea580c` | `#d8b072` | 0 | 0.0922 (kaynak 0.1943) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 76.9° kroma 0.0917 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--red` | gece | maket beyanlı türetmesi loss-red (Dub'da kayıp rengi YOK) `#c2410c` | `#ffbab4` | 0 | 0.0809 (kaynak 0.1739) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 24.1° kroma 0.1782 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--yon-arti` | gunduz | --green (gunduz) `#1f7646` | `#4a6e56` | 0 | 0.0563 (kaynak 0.1114) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.000; AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--yon-eksi` | gunduz | --red (gunduz) `#9a0019` | `#6c4442` | 0 | 0.0559 (kaynak 0.175) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.000; AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--yon-arti` | gece | --green (gece) `#61b37f` | `#8bab94` | 9 | 0.0484 (kaynak 0.1118) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.009; AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--yon-eksi` | gece | --red (gece) `#ffbab4` | `#edc3be` | 0 | 0.0487 (kaynak 0.0809) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.000; AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--mod-canli` | gunduz | Dub lavender `#7c3aed` | `#7c3aed` *(Dub jetonu AYNEN)* | 0 | 0.2466 (kaynak 0.2466) | AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--mod-kesif` | gunduz | --mod-canli (aynı hue, düşük kroma) `#7c3aed` | `#6c5e9e` | 16 | 0.0996 (kaynak 0.2466) | C = C(mod-canli) x 0.4; AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--mod-canli` | gece | Dub lavender `#7c3aed` | `#ab91ff` | 184 | 0.157 (kaynak 0.2466) | AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--mod-kesif` | gece | --mod-canli (aynı hue, düşük kroma) `#ab91ff` | `#a79fcb` | 0 | 0.0637 (kaynak 0.157) | C = C(mod-canli) x 0.4; AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--nav-t` | gece | onaylanan maket (scratch-panov2) gece washı `#172554` | `#1a274d` | 0 | 0.072 (kaynak 0.0874) | Ö3 DOLGU tavanı: C tohumda 0.0874 ≥ min C(şiddet) 0.0809; hue ve L sabit, kroma tavanın %90'ına indirildi |
| `--nav` | gece | Dub electric-blue `#2563eb` | `#72a2ff` | 172 | 0.1458 (kaynak 0.2152) | AA>=4.5 gece washı #1a274d + çıplak/tint #2e2e2e |
| `--nav-2` | gece | Dub deep-sapphire `#1e40af` | `#b2caff` | 122 | 0.0791 (kaynak 0.1809) | L = L(--nav gece) + 0.1217 (gündüzün nav↔nav-2 L farkı, yönü çevrilmiş); AA>=4.5 washı #1a274d + çıplak/tint #2e2e2e |
| `--field` | gunduz | Dub fog `#737373` | `#737373` *(Dub jetonu AYNEN)* | 0 | 0.0 (kaynak 0.0) | rampadan SEÇİM: her gerçek yüzeyde >=3:1 tutan ilk basamak |
| `--field` | gece | Dub silver `#a3a3a3` | `#a3a3a3` *(Dub jetonu AYNEN)* | 0 | 0.0 (kaynak 0.0) | rampadan SEÇİM: her gerçek yüzeyde >=3:1 tutan ilk basamak |
| `--band-2` | gunduz | Dub silver `#a3a3a3` | `#a3a3a3` *(Dub jetonu AYNEN)* | 0 | 0.0 (kaynak 0.0) | rampadan SEÇİM: card-2->band-2 2.42 · band-2->tx2 3.10 |
| `--band-2` | gece | Dub fog `#737373` | `#737373` *(Dub jetonu AYNEN)* | 0 | 0.0 (kaynak 0.0) | rampadan SEÇİM: card-2->band-2 2.86 · band-2->tx2 3.20 |
| `--violet` | gunduz | Dub slate `#404040` | `#404040` *(Dub jetonu AYNEN)* | 0 | 0.0 (kaynak 0.0) | rampadan SEÇİM: accent->violet 1.91 · violet->tx3 2.19 (v171 kısıtı: ayrım ≥1.35, kart üstünde AA) |
| `--violet` | gece | TÜRETİLDİ — Dub nötr rampasında geçerli basamak YOK `#e5e5e5` | `#c2c2c2` | 0 | 0.0 (kaynak 0.0) | accent↔tx3 merdiveninin GEOMETRİK ORTASI (eşit adım): accent->violet 1.41 · violet->tx3 1.42; akromatik |
| `--dv-n*` | gunduz | Dub deep-sapphire hue'su `#1e40af` | `#45526f` | 0 | 0.0509 (kaynak 0.1809) | L=L(--tx2)=0.4386 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |
| `--dv-p*` | gunduz | Dub tangerine hue'su `#ea580c` | `#6b493c` | 0 | 0.0513 (kaynak 0.1943) | L=L(--tx2)=0.4386 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |
| `--dv-n*` | gece | Dub deep-sapphire hue'su `#1e40af` | `#c6d4f2` | 0 | 0.0443 (kaynak 0.1809) | L=L(--tx2)=0.8699 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |
| `--dv-p*` | gece | Dub tangerine hue'su `#ea580c` | `#efcbbe` | 0 | 0.0446 (kaynak 0.1943) | L=L(--tx2)=0.8699 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |

## 2b · ÖE1 · ŞİDDET MERDİVENİ — HÜKÜM UYGULANDI (karar §9)

Karar §4 bir rolün ÜYELERİNİN ayrılabilirliğini sormuyordu; jeton turunun ilk koşumu
bunu bir KUSUR olarak buldu ve Rol-1 §9'da hükmü verdi. Eşikler ölçümden ÖNCE donduruldu
(§9.3) ve bu bölüm onları UYGULAR — sayıları yeniden yazar, değiştirmez.

| ÖE1 | eşik |
|---|---|
| a · komşu seviyelerin luminans oranı | ≥ 1.2 |
| b · komşu seviyelerin ΔE2000'i | ≥ 15.0 |
| c · her renk kendi %10 tinti üstünde | ≥ 4.5 |

### Kaynak üçlüler MERDİVENSİZ hâlleriyle (niye merdiven zorunlu)

| üçlü | çift | luminans oranı | ΔE2000 |
|---|---|---|---|
| Dub ataması (ortak ΔL, merdiven YOK) | --sev-1 ↔ --sev-2 | 1.471 | 9.44 |
| Dub ataması (ortak ΔL, merdiven YOK) | --sev-2 ↔ --sev-3 | 1.004 | 55.73 |
| Omega üçlüsü AYNEN (#0c6a3b/#6e4a00/#b3242c) | --sev-1 ↔ --sev-2 | 1.213 | 29.37 |
| Omega üçlüsü AYNEN (#0c6a3b/#6e4a00/#b3242c) | --sev-2 ↔ --sev-3 | 1.188 | 32.38 |

Yani **§9.4'ün işaret ettiği Omega üçlüsü bile, AYNEN alındığında ÖE1-a'yı tutmuyor**
(gündüz 1,188 · gece 1,035 / 1,093). Bu, hükmün ikinci yarısını zorunlu kıldı: hue ailesi
hangisi olursa olsun, üçlü bir LUMİNANS MERDİVENİNE oturmak zorunda.

### Adaylar — karar §9'un kendi sırasıyla (önce Dub içi, olmazsa §9.4)

| aday | tema | a (lum) | b (ΔE2000) | c | hüküm |
|---|---|---|---|---|---|
| A | gunduz | 1.251 / 1.253 | 5.39 / 54.18 | ✓ | **TUTMADI** |
| A | gece | 1.247 / 1.256 | 8.44 / 55.03 | ✓ | **TUTMADI** |
| B | gunduz | 1.242 / 1.253 | 13.53 / 54.18 | ✓ | **TUTMADI** |
| B | gece | 1.251 / 1.256 | 12.62 / 55.03 | ✓ | **TUTMADI** |
| C | gunduz | 1.255 / 1.247 | 28.47 / 32.43 | ✓ | TUTTU |
| C | gece | 1.247 / 1.255 | 22.75 / 30.1 | ✓ | TUTTU |

**SEÇİLEN: C · §9.4 geri çekilme · şiddet rolü Dub paletinden ÇIKAR, ölçülmüş Omega üçlüsünün hue/kroması kalır**

A ve B, ÖE1-b'de düştü: `loss-red` ile `tangerine` arasında yalnız 2,7° hue farkı var ve
Meridian'ın ölçülmüş alarm hue'suna (24,1°) çekmek bile ΔE2000'i 15'in altında bıraktı
(13,53 gündüz / 12,62 gece). **Dub'ın paleti üç seviyeli bir şiddet kanalı taşıyamıyor** —
kullanılabilir üç ayrık hue yok: `lavender` MOD'a, `electric-blue`/`deep-sapphire` ROL 6'ya
kalıcı olarak ayrılmış durumda; geriye `vivid-green` ve `tangerine` kalıyor, yani İKİ hue.
Karar §9.4'ün dediği tam da buydu ve ölçüm onu doğruladı.

### Uygulanan merdiven

| tema | jeton | değer | kroma | çift | luminans oranı | ΔE2000 | kendi tinti (`--card`) |
|---|---|---|---|---|---|---|---|
| gunduz | `--sev-1` (`--red`) | `#9a0019` | 0.1754 | --sev-1 ↔ --sev-2 | 1.255 | 28.47 | 7.272 |
| gunduz | `--sev-2` (`--amber`) | `#77520e` | 0.0917 | --sev-2 ↔ --sev-3 | 1.247 | 32.43 | 6.046 |
| gunduz | `--sev-3` (`--green`) | `#1f7646` | 0.1114 | — | — | — | 4.884 |
| gece | `--sev-1` (`--red`) | `#ffbab4` | 0.0815 | --sev-1 ↔ --sev-2 | 1.247 | 22.75 | 7.387 |
| gece | `--sev-2` (`--amber`) | `#d8b072` | 0.0917 | --sev-2 ↔ --sev-3 | 1.255 | 30.1 | 6.106 |
| gece | `--sev-3` (`--green`) | `#61b37f` | 0.1118 | — | — | — | 5.04 |

**MERDİVEN KURALI.** Şiddet arttıkça mürekkep zeminden UZAKLAŞIR (tint-yönü kuralının
şiddet hattındaki kardeşi): gündüz `--sev-1` en KOYU, gece en AÇIK; nominal (`--sev-3`)
zemine en yakın olandır. Basamak oranı **1.25**, eşik 1.2 DEĞİL —
8-bit yuvarlama ve alfa bileşimi sıfır paylı bir merdiveni aşağı itebilir. Eşik hâlâ
1.2 ve ölçüm ona karşı yapılır; pay yalnız İNŞADADIR.

**BEDELİ BEYANLI.** Gece `--sev-1` merdivenin en uzak basamağında oturuyor ve sRGB gamutu
orada kroma tutmuyor: 0,166 → 0,0809. Alarm gecede daha SOLUK bir mürekkeptir; ayrımı
luminans ve hue taşır, doygunluk değil. Bu ayrıca Ö3'ün DOLGU tavanını düşürdü ve gece
gezinme washı (`--nav-t`) o tavanın altına çekilerek yeniden türetildi (§2 tablosunda).

### ROL 2 DIŞI çift taraması (bilgi — eşiksiz)

| tema | a | b | kontrast | OKLab ΔE | hue farkı |
|---|---|---|---|---|---|
| gunduz | `--nav` #2563eb | `--nav-2` #1e40af | 1.688 | 0.1268 | 2.8° |
| gunduz | `--mod-canli` #7c3aed | `--mod-kesif` #6c5e9e | 1.013 | 0.1481 | 0.3° |
| gece | `--nav` #72a2ff | `--nav-2` #b2caff | 1.535 | 0.1381 | 3.1° |
| gece | `--mod-canli` #ab91ff | `--mod-kesif` #a79fcb | 1.029 | 0.0933 | 0.1° |

## 3 · Ö2 · para renkleri, her gerçek zeminde (iki tema)

| tema | jeton | zemin | kendi %10 tinti üstünde | çıplak |
|---|---|---|---|---|
| gunduz | `--green` | `bg` | 4.702 | 5.382 |
| gunduz | `--green` | `bg2` | 4.503 | 5.153 |
| gunduz | `--green` | `card` | 4.884 | 5.618 |
| gunduz | `--green` | `card-2` | 4.702 | 5.382 |
| gunduz | `--green` | `raise` | 4.884 | 5.618 |
| gunduz | `--green` | `slip` | 4.503 | 5.153 |
| gunduz | `--green` | `accent-tint` | 4.503 | 5.153 |
| gunduz | `--amber` | `bg` | 5.789 | 6.712 |
| gunduz | `--amber` | `bg2` | 5.569 | 6.426 |
| gunduz | `--amber` | `card` | 6.046 | 7.005 |
| gunduz | `--amber` | `card-2` | 5.789 | 6.712 |
| gunduz | `--amber` | `raise` | 6.046 | 7.005 |
| gunduz | `--amber` | `slip` | 5.569 | 6.426 |
| gunduz | `--amber` | `accent-tint` | 5.569 | 6.426 |
| gunduz | `--red` | `bg` | 6.949 | 8.425 |
| gunduz | `--red` | `bg2` | 6.645 | 8.066 |
| gunduz | `--red` | `card` | 7.272 | 8.794 |
| gunduz | `--red` | `card-2` | 6.949 | 8.425 |
| gunduz | `--red` | `raise` | 7.272 | 8.794 |
| gunduz | `--red` | `slip` | 6.645 | 8.066 |
| gunduz | `--red` | `accent-tint` | 6.645 | 8.066 |
| gece | `--green` | `bg` | 6.043 | 7.054 |
| gece | `--green` | `bg2` | 5.489 | 6.485 |
| gece | `--green` | `card` | 5.04 | 5.955 |
| gece | `--green` | `card-2` | 4.541 | 5.343 |
| gece | `--green` | `raise` | 5.04 | 5.955 |
| gece | `--green` | `slip` | 4.541 | 5.343 |
| gece | `--green` | `accent-tint` | 4.541 | 5.343 |
| gece | `--amber` | `bg` | 7.428 | 8.855 |
| gece | `--amber` | `bg2` | 6.668 | 8.142 |
| gece | `--amber` | `card` | 6.106 | 7.475 |
| gece | `--amber` | `card-2` | 5.493 | 6.708 |
| gece | `--amber` | `raise` | 6.106 | 7.475 |
| gece | `--amber` | `slip` | 5.493 | 6.708 |
| gece | `--amber` | `accent-tint` | 5.493 | 6.708 |
| gece | `--red` | `bg` | 9.009 | 11.042 |
| gece | `--red` | `bg2` | 8.178 | 10.152 |
| gece | `--red` | `card` | 7.387 | 9.321 |
| gece | `--red` | `card-2` | 6.639 | 8.364 |
| gece | `--red` | `raise` | 7.387 | 9.321 |
| gece | `--red` | `slip` | 6.639 | 8.364 |
| gece | `--red` | `accent-tint` | 6.639 | 8.364 |

## 4 · Ö7 · odak: yardımcı halka ve ana hat

| tema | zemin | oran |
|---|---|---|
| gunduz | bg | 1.241 |
| gunduz | bg2 | 1.234 |
| gunduz | card | 1.248 |
| gunduz | card-2 | 1.241 |
| gunduz | raise | 1.248 |
| gunduz | slip | 1.234 |
| gunduz | accent-tint | 1.234 |
| gunduz | bg (2px --accent ana hattı) | 18.968 |
| gunduz | bg2 (2px --accent ana hattı) | 18.16 |
| gunduz | card (2px --accent ana hattı) | 19.798 |
| gunduz | card-2 (2px --accent ana hattı) | 18.968 |
| gunduz | raise (2px --accent ana hattı) | 19.798 |
| gunduz | slip (2px --accent ana hattı) | 18.16 |
| gunduz | accent-tint (2px --accent ana hattı) | 18.16 |
| gece | bg | 1.284 |
| gece | bg2 | 1.305 |
| gece | card | 1.31 |
| gece | card-2 | 1.31 |
| gece | raise | 1.31 |
| gece | slip | 1.31 |
| gece | accent-tint | 1.31 |
| gece | bg (2px --accent ana hattı) | 14.232 |
| gece | bg2 (2px --accent ana hattı) | 13.085 |
| gece | card (2px --accent ana hattı) | 12.014 |
| gece | card-2 (2px --accent ana hattı) | 10.78 |
| gece | raise (2px --accent ana hattı) | 12.014 |
| gece | slip (2px --accent ana hattı) | 10.78 |
| gece | accent-tint (2px --accent ana hattı) | 10.78 |

## 5 · Çivi tablosu (docs/kontrast-denetimi.md §9 gövdesi)

| mürekkep | zemin yığını | tema | oran | eşik |
|---|---|---|---|---|
| --tx | --bg | gunduz | 18.97 | 4.5 |
| --tx | --bg | gece | 14.23 | 4.5 |
| --tx | --card | gunduz | 19.80 | 4.5 |
| --tx | --card | gece | 12.01 | 4.5 |
| --tx | --card-2 + --red-t | gunduz | 15.65 | 4.5 |
| --tx | --card-2 + --red-t | gece | 8.56 | 4.5 |
| --tx2 | --bg | gunduz | 7.49 | 4.5 |
| --tx2 | --bg | gece | 12.09 | 4.5 |
| --tx2 | --card | gunduz | 7.81 | 4.5 |
| --tx2 | --card | gece | 10.21 | 4.5 |
| --tx2 | --card-2 + --red-t | gunduz | 6.17 | 4.5 |
| --tx2 | --card-2 + --red-t | gece | 7.27 | 4.5 |
| --tx2 | --card-2 + --amber-t | gunduz | 6.46 | 4.5 |
| --tx2 | --card-2 + --amber-t | gece | 7.50 | 4.5 |
| --tx3 | --card | gunduz | 4.74 | 4.5 |
| --tx3 | --card | gece | 6.00 | 4.5 |
| --tx3 | --card-2 | gunduz | 4.54 | 4.5 |
| --tx3 | --card-2 | gece | 5.38 | 4.5 |
| --violet | --card | gunduz | 10.37 | 4.5 |
| --violet | --card | gece | 8.50 | 4.5 |
| --accent-2 | --accent-tint | gunduz | 16.44 | 4.5 |
| --accent-2 | --accent-tint | gece | 12.46 | 4.5 |
| --green | --card-2 + --green-t | gunduz | 4.70 | 4.5 |
| --green | --card-2 + --green-t | gece | 4.54 | 4.5 |
| --amber | --card-2 + --amber-t | gunduz | 5.79 | 4.5 |
| --amber | --card-2 + --amber-t | gece | 5.49 | 4.5 |
| --red | --card-2 + --red-t | gunduz | 6.95 | 4.5 |
| --red | --card-2 + --red-t | gece | 6.64 | 4.5 |
| --green | --bg | gunduz | 5.38 | 4.5 |
| --green | --bg | gece | 7.05 | 4.5 |
| --amber | --bg | gunduz | 6.71 | 4.5 |
| --amber | --bg | gece | 8.86 | 4.5 |
| --red | --bg | gunduz | 8.43 | 4.5 |
| --red | --bg | gece | 11.04 | 4.5 |
| --red | --bg + --nav-bg | gunduz | 8.43 | 4.5 |
| --red | --bg + --nav-bg | gece | 11.04 | 4.5 |
| --field | --card-2 | gunduz | 4.54 | 3.0 |
| --field | --card-2 | gece | 5.38 | 3.0 |
| --field | --bg | gunduz | 4.54 | 3.0 |
| --field | --bg | gece | 7.11 | 3.0 |
| --line | --card-2 | gunduz | 1.21 | 3.0 |
| --line | --card-2 | gece | 1.31 | 3.0 |
| --line-2 | --bg | gunduz | 1.42 | 3.0 |
| --line-2 | --bg | gece | 2.29 | 3.0 |
| --accent | --card | gunduz | 19.80 | 3.0 |
| --accent | --card | gece | 12.01 | 3.0 |
| --accent | --card-2 + --red-t | gunduz | 15.65 | 3.0 |
| --accent | --card-2 + --red-t | gece | 8.56 | 3.0 |
| --green-h | --card + --green-t | gunduz | 1.62 | 3.0 |
| --green-h | --card + --green-t | gece | 1.82 | 3.0 |
| --ink-h | --accent-tint | gunduz | 2.03 | 3.0 |
| --ink-h | --accent-tint | gece | 2.33 | 3.0 |
| --green-stamp | --bg | gunduz | 2.32 | 3.0 |
| --green-stamp | --bg | gece | 3.01 | 3.0 |
| --card-2 | --band-2 | gunduz | 2.42 | 3.0 |
| --card-2 | --band-2 | gece | 2.86 | 3.0 |
| --band-2 | --tx2 | gunduz | 3.10 | 3.0 |
| --band-2 | --tx2 | gece | 3.20 | 3.0 |
| --accent | --violet | gunduz | 1.91 | 3.0 |
| --accent | --violet | gece | 1.41 | 3.0 |
| --violet | --tx3 | gunduz | 2.19 | 4.5 |
| --violet | --tx3 | gece | 1.42 | 4.5 |
| --kap-4 | --card | gunduz | 2.03 | 3.0 |
| --kap-4 | --card | gece | 2.37 | 3.0 |
| --tx | --card + --kap-4 | gunduz | 9.76 | 4.5 |
| --tx | --card + --kap-4 | gece | 5.07 | 4.5 |
| --dv-n2 | --card | gunduz | 1.41 | 3.0 |
| --dv-n2 | --card | gece | 1.76 | 3.0 |
| --dv-p2 | --card | gunduz | 1.42 | 3.0 |
| --dv-p2 | --card | gece | 1.75 | 3.0 |
| --card | --bg + --scrim | gunduz | 3.00 | 3.0 |
| --card | --bg + --scrim | gece | 1.28 | 3.0 |
| --nav | --bg | gunduz | 4.95 | 3.0 |
| --nav | --bg | gece | 7.11 | 3.0 |
| --nav | --card | gunduz | 5.17 | 3.0 |
| --nav | --card | gece | 6.00 | 3.0 |
| --nav-2 | --nav-t | gunduz | 7.15 | 4.5 |
| --nav-2 | --nav-t | gece | 8.87 | 4.5 |
| --nav | --nav-t | gunduz | 4.24 | 4.5 |
| --nav | --nav-t | gece | 5.78 | 4.5 |
| --nav-h | --nav-t | gunduz | 1.59 | 3.0 |
| --nav-h | --nav-t | gece | 1.91 | 3.0 |
| --bg2 | --nav | gunduz | 4.74 | 4.5 |
| --bg2 | --nav | gece | 6.54 | 4.5 |
| --tx | --nav-t | gunduz | 16.24 | 4.5 |
| --tx | --nav-t | gece | 11.57 | 4.5 |
| --tx | --nav-t + --nav-h | gunduz | 10.24 | 4.5 |
| --tx | --nav-t + --nav-h | gece | 6.05 | 4.5 |
| --tx2 | --nav-t | gunduz | 6.41 | 4.5 |
| --tx2 | --nav-t | gece | 9.83 | 4.5 |
| --tx3 | --nav-t | gunduz | 3.89 | 4.5 |
| --tx3 | --nav-t | gece | 5.78 | 4.5 |
| --tx | --nav-t | gunduz | 16.24 | 4.5 |
| --tx | --nav-t | gece | 11.57 | 4.5 |
| --sh-ring | --bg | gunduz | 1.24 | 3.0 |
| --sh-ring | --bg | gece | 1.28 | 3.0 |
| --sh-ring | --card | gunduz | 1.25 | 3.0 |
| --sh-ring | --card | gece | 1.31 | 3.0 |

