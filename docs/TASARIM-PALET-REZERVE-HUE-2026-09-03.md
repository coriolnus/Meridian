# TASARIM — Palet turu: rezerve hue bantları + anlam jetonları (TSK-117, H1)

Yazan: Rol-1 (Fable), 2026-09-03 sabah · Tetik: operatör K7 ("rezerve hue bantlarıyla palet turu aç") ·
Kaynak vaka: nihai UI incelemesi K-5 + yeniden-inceleme Y-8 — "başarı" rengi yeşilden seri rampasının bir
durağına (`--color-seri-9`, camgöbeği) indi ve aynı jeton bir veri kümesini de boyuyor.
Bu belge KARAR belgesi değil, ÖLÇÜM + SEÇENEK belgesidir; §7'deki sorular operatör kararıdır. Kod yok.

## 0. Tek cümle

Panoda renk üç ayrı şeyi söylüyor — **rol** (şiddet/yön/mod/gezinme), **kimlik** (grafik serileri) ve
**ham Tailwind** (416 literal sınıf) — ve üçü aynı hue'ları paylaşıyor; bu tur hue uzayını rollere REZERVE
eder, serileri rezervin dışına taşır ve literal sınıfların yerine anlam jetonlarını kurar.

## 1. Ölçüm (2026-09-03, komutlar §1.3)

### 1.1 Rol jetonları — hue haritası (gündüz `ui/src/jetonlar.css`, üretilmiş; kaynak `meridian/web/tokens.json`)

| hue | jeton | değer | rol |
|---|---|---|---|
| 17° | `--yon-eksi` | #b43c0b | yön: negatif K/Z |
| 20° | `--amber` / `sev-2` | #c74300 | şiddet P2 (insan gerekiyor) |
| 142° | `--yon-arti` | #107636 | yön: pozitif K/Z |
| 145° | `--green` / `sev-3` | #00963e | şiddet P3 (nominal) |
| 195° | `--sky` `--blue` `--sapphire` | #0998c8 #006f94 #004860 | rol beyanı bu ölçümde okunmadı (§7 S3) |
| 215–226° | `--nav-t` `--nav` `--nav-2` | #dbeaff #2563eb #1e40af | ROL 6 gezinme/seçim |
| 253° | `--mod-kesif` | #6c5e9e | mod: keşif |
| 262° | `--mod-canli` | #7c3aed | mod: canlı (ayrılmış kroma) |
| 346° | `--red` / `sev-1` | #c3002d | şiddet P1 (şimdi müdahale) |

Gece (`.dark`) aynı hue'ları korur, ışıklılığı değiştirir — **bir istisnayla**: gece `--yon-eksi` #f98080 (0°) ile
gece `--red` #ff7e7c (1°) hue VE ışıklılıkta (l74/l74) çakışıyor. Gündüzde 17° ↔ 346° olan ayrım gecede
yok: negatif K/Z ile P1 alarmı aynı renk. Bu, bu turdan bağımsız bir kusur ve turun ilk kalemi (§4 K-0).

### 1.2 Seri rampası (`ui/src/tema.css`, `--seri-*` → `@theme inline` `--color-seri-*`)

1–5 akromatik (`--chart-*`, oklch C=0). 6–10 kromatik ve **beşi de rezerve edilmesi gereken bantlara düşüyor**:

| seri | gündüz kaynağı | hue | çakıştığı rol |
|---|---|---|---|
| 6 | `--color-blue-600` (#2563eb) | 221° | `--nav` ile AYNI hex |
| 7 | `--color-orange-600` | ~21° | `sev-2`/`--yon-eksi` bandı |
| 8 | `--color-violet-600` (#7c3aed) | 262° | `--mod-canli` ile AYNI hex |
| 9 | `--color-cyan-600` | ~192° | 195° ailesi |
| 10 | `--color-pink-600` | ~330° | `sev-1` (346°) komşusu |

Huni jetonları (`--huni-1/2/3` = #2563eb / #7c3aed / #16a34a) rol hex'lerinin kopyası: huni-1 = nav, huni-2 =
mod-canlı, huni-3 = yön-artı bandı. K-5/Y-8 vakası bu tablonun doğrudan sonucu: "başarı"yı seri-9'a bağlamak
bir VERİ KİMLİĞİNE anlam yüklemekti.

### 1.3 Literal Tailwind renk sınıfları (`ui/src`, 56 dosya, 416 kullanım)

| aile | sayı | fiilî anlam |
|---|---|---|
| amber-300…700 | 238 | uyarı |
| emerald-300…700 + green-600 | 135 | başarı/nominal |
| red-400…600 | 31 | kritik |
| sky-400…700 | 12 | bilgi |

Anlam jetonu olmadığı için yüzeyler ham palete uzanıyor; tokens.json'da `success`/`warning` adlı jeton YOK (yalnız
`sev-1/2/3` ve akromatik `accent`). Yani "başarı" bugün İKİ dilde konuşuluyor: rol dilinde `sev-3` (145°),
Tailwind dilinde `emerald-500` (~160°) — aynı anlam, iki hue.

Komutlar: hue haritası `python - <<EOF … colorsys.rgb_to_hls …` (jetonlar.css + tokens.json üzerinden; ölçüm
betiği bu turun H2'sinde `tests/` çivisine dönüşür, §5) · literal sayım
`grep -rhoE "\b(bg|text|border|ring|from|to|fill|stroke)-(amber|green|red|emerald|rose|yellow|blue|indigo|violet|purple|orange|sky|teal|lime|pink|fuchsia|cyan)-[0-9]{2,3}\b" ui/src | wc -l`.

## 2. Rezerve bantlar (öneri; sayılar §1'den, pay ±10°)

| bant | hue aralığı | sahibi | not |
|---|---|---|---|
| KRİTİK | 336°–6° | `sev-1` | gece `red` 1° içeride |
| UYARI + YÖN-EKSİ | 8°–30° | `sev-2`, `yon-eksi` | ikisi aynı bantta: bilinçli (turuncu-kırmızı ailesi), ışıklılıkla ayrılır |
| BAŞARI + YÖN-ARTI | 132°–155° | `sev-3`, `yon-arti` | emerald-500 (~160°) DIŞARIDA — literal sınıflar jetona taşınınca hizalanır |
| BİLGİ (195° ailesi) | 185°–210° | `sky/blue/sapphire` → `--bilgi` | **S3 KARAR (operatör 2026-09-03 ~10:50Z): BİLGİ rolü, REZERVE.** Bedel: `--color-seri-9` (camgöbeği, 192°) artık bantta — TSK-124 takımyıldızı düğümü GEÇİCİ BEYANLI İSTİSNA (K-4'e kadar) · **K-2d TAMAM (2026-09-04):** 3 dosyadaki 12 literal `sky-*` kullanımı `bilgi`/`bilgi-h`/`bilgi-t` utility'lerine göçtü (tavan v397'de 12→0); gezinme/veri serisi anlamı taşıyan kullanım YOK — 12'sinin tamamı bilgi rozeti/çağrı-kutusu (task-5-6-report.md) |
| GEZİNME | 210°–232° | `nav-*` | |
| MOD | 245°–270° | `mod-kesif`, `mod-canli` | gece 251–254° içeride |
| SERBEST (veri serileri) | 32°–130° · 156°–184° · 234°–244° · 272°–334° | seri rampası | fiilen dört kullanılabilir hue: ~60° (sarı — beyaz zeminde zayıf), ~95° (zeytin/lime), ~175° (teal), ~290° (mor) ve ~320° (macenta) |

Kural: **rol bandındaki bir hue, rol dışı hiçbir jetonda/kullanımda görünmez.** Bant rezervi hue'ya değil
hue×kromaya bağlanabilir (§3 B).

## 3. Seçenekler — seri rampası nereye gider

**A · Hue-rezervi, seriler serbest bantlara taşınır.** 6–10 → teal 175°, macenta 320°, mor 290°, zeytin 95°,
sarı 60° (sarı gündüzde 700, gecede 300 tonuyla). Bedel: beş serbest hue'nun ikisi (sarı, zeytin) beyaz
zeminde zayıf; gösterge ayırt edilebilirliği bugünkü beş "temiz" hue kadar iyi olmaz. Mekanik, tek dosya.

**B · Hue×kroma rezervi; seriler hue'larını korur, kromayı düşürür.** Rol jetonları yüksek kroma (oklch C≥0,15),
seri 6–10 aynı hue'larda C≤0,09. Bedel: soluk çizgiler; çok serili grafikte kimlik zayıflar — tam da rampanın
ona çıkarılma gerekçesiyle (tema.css şerhi: iki seri karışırsa gösterge susar) çelişir. RED önerisi.

**C · Seriler yalnız akromatik + desen (kesik/nokta çizgi, kalınlık).** Renk kimlik kanalı olmaktan çıkar. Bedel:
Recharts'ta desen kimliği gösterge ile eşlemek ek iş; 10 seriyi gri tonu+desenle ayırmak okunmaz. RED önerisi.

**A′ (öneri) · A + huni kopyaları kaldırılır.** `--huni-1/2/3` rol hex'lerinin kopyasıdır (tek-kaynak yasası):
huni üç durağı seri rampasının 6/7/8'ine (yeni serbest hue'larıyla) bağlanır ya da açıkça "huni-1 = nav" ROL
beyanı yapılır (o zaman huni bir rol jetonudur, seri değil). Öneri: seri'ye bağla — huni bir VERİ görselidir.

## 4. Anlam jetonları (uygulama sırası; H2'de plan)

- **K-0 (önce, bağımsız kusur):** gece `--yon-eksi` ↔ gece `--red` çakışması; gece yön-eksi 17°'ye
  (gündüzle aynı hue) taşınır, ışıklılık gece için ölçülür. Çivi: gece rol jetonları arasında hue farkı ≥8°.
- **K-1:** `--basari` `--uyari` `--kritik` `--bilgi` (+ `-t` tint, `-h` saç teli) = `sev-3/sev-2/sev-1/sky`
  ALIAS'ları tokens.json'da (üretici `ops/jeton_css_uret.py` → jetonlar.css), `@theme inline` ile
  `--color-basari` vb. Tailwind utility'leri (`bg-basari-t`, `text-uyari`). Yeni renk YOK; ad var.
- **K-2:** 416 literal sınıf → jeton, dosya dosya, dört aile için eşleme tablosu (amber→uyari, emerald/green→
  basari, red→kritik, sky→bilgi); tavan çivisi MONOTON: sayım 416'dan yalnız düşer (bedel yasası: her dilim
  öncesi/sonrası sayım raporda).
- **K-3:** K-5/Y-8 vakası: "başarı" `--color-seri-9`dan `--basari`ya.
- **K-4:** seri rampası A′ (operatör S1 kararından sonra).

## 5. Çivi ailesi (v286 ailesi genişler; ölçüm betiği testte YAŞAR, belgede değil)

1. `test_rol_hue_bantlari`: jetonlar.css (gündüz+gece) kromatik jetonların hue'su kendi bandında; seri-6…10 ve
   huni hiçbir rol bandında değil. Bant tablosu TEK kaynaktan (tests içinde sözlük; belge ondan türetilmez — belge
   ölçüm günü kopyasıdır ve tarih taşır).
2. `test_gece_rol_hue_ayrimi`: gece rol jetonları ikili hue farkı ≥8° (K-0 çivisi).
3. `test_literal_renk_sinifi_tavani`: `ui/src` literal sayımı ≤ tavan; tavan her dilimde düşürülür.
4. `test_anlam_jetonlari_alias`: `--basari` = `--green` (hex eşitliği, iki temada) — kopya değil alias.

## 6. Bedel

Renk kimliği (grafikler) A′ ile biraz zayıflar (iki zayıf hue); 56 dosyada literal→jeton göçü büyük diff, görsel
regresyon riski (ekran değişmez iddiası jeton eşitliğiyle çivilenir: `emerald-500`≠`sev-3` hex'i — göç bir
renk DEĞİŞİKLİĞİDİR, "aynı" değil; 160°→145°). Ölçülmeyen: colorblind-safe ayrım (deuteranopi'de 145° ↔ 20°
ayrımı ışıklılıkla taşınıyor mu) — palet turunda ölçülür, S4.

## 7. Operatör soruları — KARARLAR (2026-09-03 ~10:45–10:50Z)

- **S1 → A′** · **S2 → huni seriye bağlanır** (A′ ile kapandı) · **S3 → BİLGİ rolü, rezerve** · **S4 → renk körlüğü ölçümü BU TURDA** (H2 planına simülasyon + parlaklık farkı eşiği girer) · **S5 → dört dilim, aile başına** (uyarı 238 → başarı 135 → kritik 31 → bilgi 12).
- H2: writing-plans ile dört dilimlik plan; TSK-124'ün `DUGUM_STILI` istisnası K-4'te kapanır.

Sorulan hâlleri (kayıt):

- **S1** Seri rampası: A′ (öneri) · A · B · C?
- **S2** Huni: seri'ye bağlansın mı (öneri), yoksa "huni = rol kopyası" beyanıyla kalsın mı?
- **S3** 195° ailesi (`sky/blue/sapphire`) hangi rol? `--bilgi` olarak rezerve mi, serbest mi?
- **S4** Colorblind ölçümü bu turun kapsamına girsin mi (Ö-simülasyon + ışıklılık farkı ≥ eşik), yoksa ayrı kalem?
- **S5** K-2 göçü tek dilim mi (56 dosya, tek ajan), dört dilim mi (aile başına)?
