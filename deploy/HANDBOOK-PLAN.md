# El kitabı → Meridian uygulama planı

> ## UYGULAMA DURUMU — 2026-08-01
>
> Belgeleme turu bitti, uygulama başladı. Bu blok neyin KAPANDIĞINI söyler; aşağıdaki analiz
> **belgeleme turunun** hâli olarak bırakıldı (tarihsel kayıt; "bu turda değişmedi" ifadeleri
> o tura aittir).
>
> **Kapandı — dört tur, dört commit:**
>
> | Madde | Ne yapıldı | Nerede |
> |---|---|---|
> | §0 P1 | 20 sabit `rgba()` → 11 jeton adı | `index/landing/workflow.html` |
> | §0 P2 | `theme.js`, `data-theme`, kalıcılık, ray sonunda anahtar | üç yüzey + `app.js` |
> | §0 P3 | `--r-pill` borcu: üç yüzeyde de sıfır kullanım ölçüldü → **iddia bırakıldı**, ölü jeton silindi | `DESIGN.md`, `landing.html` |
> | H6 | Gece değer takımı, üç yüzeyde birebir aynı; AA 0 ihlal (dosyadan yeniden ölçüldü) | üç yüzey |
> | §4.1 | `_donut` + `_ring` → `_bullet()` (Few'nun beş bileşeni); `.thermo` KALDI (lineer) | `app.js`, `index.html` |
> | H4 | `cv11`/`ss01` ölçüldü → **ölü**, üç yüzeyden silindi; `.tbl` ilk kez biçimlendirildi; sayı sütunları sağa hizalı | üç yüzey + `app.js` |
> | H13/H18 | Kazanca açık `+` işareti — renk artık tek kanal değil | `app.js` (9 okuma) |
> | H20 | `--field` jetonu: form kontrolü kenarı 3.12 (gündüz) / 3.18 (gece) → **1.4.11 geçti** | üç yüzey + `app.js` |
>
> **§7'nin "ölçülemedi" listesinden kapananlar:** §7.1 (`1`/`l` 10-11px'te — ayrık, ve
> `--label-size` mono zaten UPPERCASE olduğu için küçük `l` o boyutta hiç render edilmiyor) ·
> §7.2 (Google derlemesi — tarayıcıda, gerçek servis edilen dosyayla ölçüldü) · §7.3 (Geist
> Sans `ss01`/`cv11` — yok, etkisiz) · §7.6 (üç yanlış kontrast rakamı düzeltildi, `index.html`
> içindeki iki yanlış yorum da) · §7.7 (tarayıcı doğrulaması — artık yapılıyor).
> **Hâlâ açık:** §7.4 (panel sayımı), §7.5 (alarm oranı — eşleme hükmü verilmeden ölçülemez).
>
> **Bu tur ortaya çıkan, planda OLMAYAN üç kusur** (üçü de düzeltildi):
> 1. **CSP dağıtımı kırardı.** `deploy/Caddyfile` `script-src 'self'` diyor ama `landing.html`
>    ve `workflow.html` satır içi script taşıyordu — üretimde ikisi de ölü açılırdı
>    (workflow'un TÜM diyagramı o blokta üretiliyor). `landing.js` / `workflow.js` olarak
>    çıkarıldı.
> 2. **`.tbl` sınıfının hiç stili yoktu.** Dört tablo tarayıcı varsayılanıyla, hücreleri
>    bitişik çiziliyordu.
> 3. **Boş veride `undefined` sızıyordu** ("Lundefined", "strateji vundefined").
>
> **Sıradaki adaylar:** H12 (gömülü trendler) · H23 (satır-içi klavye gezinmesi) ·
> H3 (beklenen-aralık bandı — önce bandın İSTATİSTİKSEL tanımı gerekir, uydurulamaz) ·
> H2/H16/H17 (alarm bütçesi — önce EEMUA eşleme hükmü yazılmalı) · H5 (imputation işareti —
> okuma ucunun onarım bayrağı taşıması gerekiyor) · H7 (komut paleti, en büyük tek kalem).

**Ne bu:** operatörün verdiği UI/UX el kitabındaki HER maddenin mevcut kodla karşılaştırması.
**Ne değil:** kod. Bu tur belgeleme turudur; `meridian/web/*` bu turda DEĞİŞMEDİ.
**Yürürlükteki tasarım sözleşmesi:** `DESIGN.md` (bu turda iki-tema kararına göre yeniden yazıldı).
**Ürün gerçeği:** `PRODUCT.md`.

## Yöntem ve okuma kuralları

- El kitabı 35 ayrık uygulanabilir maddeye ayrıldı (H1–H35). Numaralandırma bu belgeye özgüdür.
- Her madde üç kovadan birine düşer: **ZATEN VAR** · **EKSİK** · **ÇELİŞİYOR**.
- Kısmen karşılanan maddeler **EKSİK**'e yazıldı ve mevcut kısmı satırında belirtildi — kovanın
  işi karar vermek, iltifat etmek değil. "Yarısı var" bir yapılacak iştir.
- Sıralama el kitabının kendi *staged recommendations* bölümünü izler: önce **ŞİMDİ** (5 madde),
  sonra **SONRA** (5 madde), sonra staged listede olmayan geri kalanlar.
- Dosya:satır referansları bu turda okunan ağaçtan alındı. Kod değiştikçe kayabilir; uygulama
  turunda satır değil **desen** aranmalı.

### Kanıt gücü etiketleri (el kitabının kendi değerlendirmesinden)

| Etiket | Anlamı |
|---|---|
| **[GÜÇLÜ]** | Nicel, adlı kaynak, yön ve mekanizma birlikte savunuluyor |
| **[ORTA]** | Sağlam kaynak var ama transferi yorum, ya da alan farkı var |
| **[ZAYIF]** | El kitabının KENDİSİ kanıtı zayıf/çekişmeli ilan ediyor — §5'te ayrıca listelendi |
| **[YORUM]** | Süreç-endüstrisi hedefinin yazılıma uyarlanması; el kitabı bunu açıkça "yorumdur" diyor |

**Uyarı — ölçek farkı gerçek:** el kitabının en yüksek kanıtlı maddesi (H1, ASM 5× tespit
iyileştirmesi) ile en zayıfı (H25 Doherty 400ms) aynı belgede yan yana duruyor ama aynı ağırlıkta
işlenemez. ASM rakamları process-control saha çalışmalarıdır; **yazılım panosuna transferi makul
ama birebir kanıtlanmış DEĞİL** (el kitabının kendi caveat'ı). Doherty'nin ise modern replikasyonu
yok. §5 zayıf-kanıtlı maddeleri tek yerde toplar; bir uygulama turu oraya sıra gelmeden bitebilir.

---

## §0 — ÖN KOŞUL: temalama borcu (her şeyden önce)

Bu, el kitabında bir madde değil; iki-tema kararının **teknik ön koşulu** ve bulunduğu için buraya
yazıldı. H6 (koyu tema) bu borç ödenmeden uygulanamaz.

**EKSİK — ön koşul P1: sabit renk sabitleri jeton değil.** `:root` dışında **12 ayrı `rgba()`
sabiti** var ve hiçbiri tema değişimine tepki vermez:

| Sabit | Yer | Ne kırılır |
|---|---|---|
| `rgba(255,255,255,.82)` | `meridian/web/index.html:160` (`nav`) | **En kritik.** Üst bar koyu temada BEYAZ kalır; HALT/KRİZ kırmızısı üstünde görünmez olur. Bu hatanın tersi zaten yaşandı ve kayıtlı: eski koyu bar açık zemine geçince kırmızı **1,27:1** ölçülmüştü (bu turda yeniden hesaplandı, doğrulandı). |
| `rgba(12,106,59,.35)` ×5 | `index.html` — `.s-ok`, `.t-go`, `.ds-chip-ok` vb. | Çip iç saç telleri açık-tema yeşiline çakılı |
| `rgba(179,36,44,.35)` ×3 | `index.html` | aynı, kırmızı |
| `rgba(110,74,0,.35)` ×3 | `index.html:352, 514, 599` | aynı, kehribar |
| `rgba(110,74,0,.40)` | `index.html:389` (`.pd-warn` kenarı) | aynı |
| `rgba(5,5,5,.30)` ×2 | `index.html:516, 552` | `.t-vi` / `.lv.on` kenarı — koyu temada görünmez |
| `rgba(5,5,5,.18)` | `index.html:278` (`.slabel`) | aynı |
| `rgba(5,5,5,.42)` | `index.html:646` (`.kbd-ov` perde) | koyu temada perde işlevini yitirir |
| `rgba(12,106,59,.55)` | `index.html:302` (`.spine.calm::before`) | sakin damga rengi |
| `rgba(12,106,59,.08)` / `rgba(179,36,44,.07)` | `index.html:348` (`.pm-cell.pos/.neg`) | matris hücre zeminleri |

→ **Yapılacak:** bu 12 sabiti `--*-h` (hairline), `--*-t2`, `--scrim`, `--pm-pos`, `--pm-neg`
jetonlarına çıkar ve iki değer takımında da tanımla. **Büyüklük:** yalnız `index.html` içinde
~15 satır; davranış değişmez. Bu adım tek başına test edilebilir (açık temada görsel çıktı
birebir aynı kalmalı — regresyon kapısı budur).

**EKSİK — ön koşul P2: tema anahtarı altyapısı yok.**
`grep -rn "prefers-color-scheme\|data-theme" meridian/web/` → **sıfır sonuç**. Ne medya sorgusu, ne
kök nitelik, ne kalıcılık. `app.js` CSS değişkenlerine yalnız `--navh` için dokunuyor
(`meridian/web/app.js:292` yazar, `app.js:390` okur) — yani JS'in mevcut jeton sözleşmesiyle işi
yok, bu iyi haber: değerleri değiştirmek app.js'i kırmaz.
→ **Yapılacak:** `<html data-theme="gunduz|gece">`, `:root[data-theme="gece"]{…}` bloğu,
`localStorage` kalıcılığı, ilk ziyarette `prefers-color-scheme` tohumu. **Dokunulacak:**
`meridian/web/index.html` (`:root` + yeni blok), `meridian/web/app.js` (anahtar + kalıcılık),
sonra aynı desen `landing.html` ve `workflow.html`. **Büyüklük:** index+app ~60 satır; üç yüzey
toplamı ~150 satır.

**EKSİK — ön koşul P3: `--r-pill` yok.** `DESIGN.md` "tam hap geometrisi" diyor; `index.html:83`
yorumunda `--r-pill` bilinçli KALDIRILMIŞ ("tanımlıydı ama hiçbir kural onu kullanmıyordu").
Belge ile artefakt burada çelişiyor. → Ya jeton geri gelir ve kullanılır, ya belge "tam hap"
iddiasını bırakır. Küçük ama sözleşme borcudur.

---

## §1 — ŞİMDİ (el kitabının kendi "kanıt en güçlü" listesi)

### H1 — Quiet Line'ı gerçek HP-HMI Level-1 yap; sağlıklı = collapsed, anormal = açılır **[GÜÇLÜ / transferi ORTA]**

*Kanıt:* Nova Chemicals & ASM (PAS/ISA-101, WEAO 2017): tespit %10 → %48 (5×), görev başarısı
%70 → %96, süre 18,1 → 10,6 dk. El kitabının en yüksek kanıtlı maddesi. **Caveat (el kitabından):**
process-control saha çalışması; yazılım panosuna transferi makul ama birebir kanıtlanmış değil.

- **ZATEN VAR — triyaj şeridi Level-1 okumasıdır.** `meridian/web/app.js:597` şeridi
  `role="status" aria-live="polite"` ile üretiyor; üç durum sınıfı (`calm` / `attn` / `act`)
  `meridian/web/index.html:294-306`. Sakin hâl bir cümle, eylem hâli sayfanın en yüksek sesli işareti.
- **ZATEN VAR — bastırma yasağı yazılı ve gerekçeli.** `meridian/web/app.js:585-595`: hiçbir uyarı
  başka bir uyarının varlığı yüzünden düşmez; iki gerçek arıza (varsayılan görünümün tüm sarıları
  atması; bir kırmızının tüm sarıları silmesi) yorumda kayıtlı. Bu, el kitabının H14
  (normalization of deviance) maddesinin yarısını zaten karşılıyor.
- **ZATEN VAR — bekçi collapse/expand tam olarak el kitabının istediği desen.**
  `meridian/web/app.js:1097-1099`: `stale` ve `never` boşken tek rozet — `bekçi <ok>/<total>`;
  biri doluyken `<n> geciken · <en kötü ad> <saat>sa`. El kitabının "17/17 OK'a collapse, yalnız
  sapmada segment aç" önerisi **uygulanmış durumda**.
- **EKSİK — Level-2/3/4 ayrımı adlandırılmamış.** Beş görünüm (`meridian/web/app.js:12-16`)
  fiilen Level-2; çekmece Level-3; teşhis panelleri Level-4. Hiyerarşi *var* ama isimlendirilmemiş
  ve "bir okuma tek basamakta yaşar" kuralı yazılı değil — `DESIGN.md` § Layout'a bu turda eklendi,
  koda karşılığı yok. **Büyüklük:** kod değişikliği yok; bir denetim + gerekirse okuma taşıma.
- **ÇELİŞİYOR → §4.6** el kitabının "~20 yeni display" reçetesi.

### H2 — Alarm bütçesini canlı KPI göster; flood-aggregation **[YORUM — el kitabının kendi etiketi]**

*Kanıt:* EEMUA 191 4. ed. / ISA-18.2 / IEC 62682 nicel hedefleri (~%80/15/5, <10 alarm/10 dk,
<10 standing). Joint Commission SEA 50 (2013): alarm sinyallerinin %85–99'u klinik müdahale
gerektirmiyor; 2009-01→2012-06 arası 98 olay, 80'i ölüm. **Caveat (el kitabından):** hedefler
process-industry kaynaklı; yazılım bildirimlerine uyarlanması YORUMDUR.

- **EKSİK — bütçe okuması hiç yok.** HUD altı rozet taşıyor (`meridian/web/app.js:1090-1101`:
  mod/broker · rejim+bütçe · döngü · WS · bekçi · IO p95) ama alarm oranı/dağılımı yok.
- **ZATEN VAR (tohum) — seviye taksonomisi mevcut.** `meridian/web/app.js:680` ve `app.js:3423`:
  olaylar `alarm` / `warn` / `info` seviyeleriyle geliyor. Yani %80/15/5 dağılımı **hesaplanabilir
  durumda** — üç seviyeli mevcut taksonomi EEMUA'nın low/high/emergency'sine eşlenebilir.
- **EKSİK — ön koşul: eşleme kararı verilmemiş.** `info→low`, `warn→high-medium`, `alarm→emergency`
  eşlemesi bir HÜKÜMDÜR ve kaydedilmeden sayılamaz. Uydurma yasağı gereği: eşleme kartta yazılı
  değilse yüzde de yazılmaz.
  **Dokunulacak:** yeni bir okuma ucu (`api.py`) + HUD rozeti veya Operasyon paneli bloğu
  (`app.js`). **Büyüklük:** eşleme kararı + ~40 satır sayaç + ~20 satır render.
- **EKSİK — shelving/suppression UX yok.** Standing alarm >10 durumunda devreye girecek arayüz yok.
- **EKSİK — flood detection yok.** >10/10dk tetikleyicisi ve rationalization çağrısı yok.

### H3 — Bullet graph + gömülü trend + beklenen-aralık bandı; gauge YASAK **[GÜÇLÜ]**

*Kanıt:* Few, *Bullet Graph Design Specification* (Perceptual Edge 2006, rev. 2013-10-10) — beş
bileşen, dik karşılaştırma çizgisi, 2–5 (ideal 3) nicel aralık, **tek hue'nun farklı yoğunlukları**
(farklı hue değil, CVD). Cleveland & McGill 1984 + Heer & Bostock 2010 doğruluk sıralaması.
**Nüans (el kitabından):** McColeman ve ark. sıralamanın göreve bağlı olduğunu gösterdi — evrensel değil.

- **ÇELİŞİYOR — üç radyal/analog gösterge canlıda. → §4.1** (planın en somut çelişkisi).
- **ZATEN VAR — lineer ölçek altyapısı hazır.** `.bar` (`meridian/web/index.html:522-524`) 5px
  cetvelli tüp; `.pm-conf` (`index.html:345-346`) 2px güven izi; `.regrow .bar` (`index.html:725`)
  rejim çubukları. Bullet graph bunların üstüne kurulur, sıfırdan değil.
- **EKSİK — beklenen-aralık bandı yok.** Sermaye mini-eğrisi (`meridian/web/app.js:750-756`,
  150×30 SVG) eksen, band, referans çizgisi taşımıyor — "bağlam veren tek çizgi" olarak bilinçli
  sade, ama el kitabının istediği bant yok.
- **ZATEN VAR (kısmi, ama iyi) — bir grafik zaten referans çizgili.** Bootstrap dağılım grafiği
  (`meridian/web/app.js:1174-1184`) Δ=0 çizgisi, ortalama çizgisi ve **eşik kuantili** çizgisini
  birlikte çiziyor ve altına "P(ΔS>0)=… · gerekli ≥… → GEÇER/GEÇMEZ" yazıyor. Bu, bullet graph'ın
  "featured measure + karşılaştırma ölçüsü + nitel aralık" mantığının hâlihazırdaki en yakın örneği.
  Bullet graph spesifikasyonu buradan genellenmeli.
- **EKSİK — bullet graph bileşeni yok.** Beş bileşenli (etiket · tek lineer eksen · belirgin bar ·
  dik karşılaştırma çizgisi · 2–5 aralık) yeniden kullanılabilir bir çizici yok.
  **Dokunulacak:** `app.js` (yeni `bullet()` fonksiyonu), `index.html` (sınıflar).
  **Büyüklük:** ~50 satır SVG üretici + ~20 satır CSS + çağrı yerleri.
- **EKSİK — horizon chart yok** (el kitabı yoğun çok-serili veri için öneriyor; Javed ve ark. 2010
  uyarısı: 8 seri bile sınırda). Meridian'da şu an 8+ serili bir görünüm YOK → **düşük öncelik**.

### H4 — `tabular-nums` + slashed-zero + sağa hizalı ondalıklar **[GÜÇLÜ — finansal konsensüs]**

- **ZATEN VAR — `tabular-nums` her yerde.** `meridian/web/index.html:108` (`.mono-num`) ve
  aynı dosyada ~20 ayrı kural; `landing.html` de aynı.
- **ZATEN VAR ama gerekçesi düzeltildi — slashed-zero'ya İHTİYAÇ YOK.** Bu turda font ikilisi
  ölçüldü (`GeistMono-Medium.ttf` v1.401, yerel kopya; ayrıntı `DESIGN.md` § Typography):
  - Geist Mono'nun GSUB özellik listesinde **`zero` YOK** → `font-variant-numeric: slashed-zero`
    bu fontta **hiçbir şey yapmaz**.
  - Ama `zero` glifi (gid 477) **3 kontur** taşıyor, `O` (gid 74) 2 kontur; fazladan kontur
    sayacın içinden geçen 4 noktalı bir paralelkenar — **eğik çizgi varsayılan glife gömülü**.
    Yani gereksinim ÖZELLİKLE değil, ÇİZİMLE karşılanıyor; bu daha güçlü bir garanti.
  - **`tnum` de YOK**, ama tüm rakamlar 600/1000 ilerleme genişliğinde → hizalama yapısal.
    CSS bildirimi `ui-monospace` yedeği için savunma olarak KALIR.
  → **Yapılacak yok. Yapılmayacak var:** `slashed-zero` bildirimi EKLENMEMELİ (etkisiz olduğu
  hâlde "yapıldı" izlenimi verir — uydurma yasağının tipografik hâli).
- **EKSİK — sağa hizalı ondalık sistematik değil.** `text-align:right` `app.js`'te 9,
  `index.html`'de 1 yerde. Sayı sütunlarının hepsi sağa hizalı değil. **Büyüklük:** tablo
  bazında denetim; ~10-20 satır.
- **EKSİK (küçük) — `font-feature-settings:'cv11','ss01'` doğrulanmamış.**
  `meridian/web/index.html:100` `body`'ye uyguluyor. Ölçüldü: **`cv11` Geist Mono'da yok** →
  orada kesin no-op. Geist SANS için ölçülemedi (yerel kopya yok). `cv11` bir Inter
  sözleşmesidir; büyük olasılıkla önceki dünyadan kalma ölü bildirim. → Doğrula ve ölü ise sil.

### H5 — Honesty-UI'yi imputation-uncertainty ile güçlendir **[GÜÇLÜ]**

*Kanıt:* Sarma ve ark. (IEEE TVCG 2023) — çoğu EDA sistemi yalnız complete-case gösterir, bias
yaratır; Padilla / Kay / Hullman (2020/2022) belirsizlik görselleştirmesi.

- **ZATEN VAR — None ≠ 0 kuralı motorda.** `meridian/web/app.js:94`: `trn()` null/NaN'da **"—"**
  döner, asla 0 değil. `.pm-unsown` / `.pm-none` (`index.html:356-357`) ekilmemiş hücreyi
  "çıplak toprak" olarak çizer, sıfır olarak değil. `app.js:990` "dürüst boşluk, uydurma yok";
  `app.js:219` "bar serisi yok (kaynak veri bulunamadı)"; `app.js:3779` "türetilemeyen alan cümleyi
  kısaltır, doldurmaz". **Bu madde Meridian'da el kitabından ÖNCE ve daha sıkı uygulanmış.**
- **ZATEN VAR — belirsizlik zaten gösteriliyor.** Güven aralıkları `app.js:1971` (`CI [lo, hi]`) —
  ve IC mini-trendi `app.js:1211+`,
  "aralık sıfırı kapsıyor" uyarısı `app.js:1912` ve `app.js:2049`, aralık yöntemi + varsayımı
  `app.js:1821` ve `app.js:1827`, güven izi `.pm-conf` `index.html:344`.
- **EKSİK — onarılmış/impute edilmiş veri panoda İŞARETLİ DEĞİL.** Arka uçta onarım geçidi ve
  karantina var (`MERIDIAN_ENGINEERING_LOG.md`), ama `app.js`'te onarılmış barı gözlemlenmiş
  bardan ayıran bir görsel kod bulunamadı (`grep -n "onarım\|repair\|imputed"` → yalnız ilgisiz
  eşleşmeler). Bu, el kitabının tam olarak uyardığı boşluktur: complete-case gibi görünen ama
  onarılmış veri. **Dokunulacak:** okuma ucu (kaynak damgası bar seviyesinde) + `app.js` seri
  çizicileri. **Büyüklük:** orta — ucun onarım bayrağını taşıması gerekiyorsa `api.py` de girer.
- **EKSİK — HOPs / quantile dotplot / gradient interval yok.** El kitabı öneriyor; mevcut CI
  metin+çizgi kodlaması AA-yeterli ama görsel belirsizlik dili yok. **Düşük öncelik** — tek uzman
  operatör için CI metni okunabiliyor (Kale ve ark. 2018 HOPs faydasını *eğitimsiz* gözlemcide buldu).

---

## §2 — SONRA (el kitabının "refine" listesi)

### H6 — Koyu paleti gri-öncelikliye kaydır; gerekçe 24/7 low-light; WCAG 2.2 AA standart kalır **[ZAYIF-ORTA — §5.2]**

- **EKSİK — koyu tema hiç yok.** Doğrulandı: `meridian/web/` altında `prefers-color-scheme`
  **sıfır** eşleşme. Tek dünya var ve o açık.
- **ZATEN VAR — karar ve değerler bu turda belgelendi.** İki temanın tam jeton tablosu ve
  **ölçülmüş** kontrast oranları `DESIGN.md` § Colors'ta. Gece zemini `#1c1a18`, mürekkep
  `#d4d0cb`, para renkleri `#4cc38a` / `#e0a82e` / `#f58b8f`. Her metin jetonu her gerçek bileşik
  zeminde AA geçiyor (en kötü: kırmızı **4,93**, `--tx2` **4,96**).
- **ÖLÇÜLMÜŞ TUZAK — naif ters çevirme çalışmaz.** Eski koyu dünyanın kırmızısı `#f2555a` gece
  zemininde kendi %10 tinti üzerinde **4,12** ölçtü (`--card`), `--card-2` üzerinde **3,72** —
  yani AA altı. `DESIGN.md`'de *The Tint-Direction Rule* olarak kayıtlı: açık zeminde tint
  mürekkebe YARDIM eder, koyu zeminde ZARAR verir.
- **EKSİK — uygulama:** §0'daki P1+P2 ön koşulları + `:root[data-theme="gece"]` değer takımı +
  üç yüzeye yayma. **Dokunulacak:** `index.html`, `app.js`, `landing.html`, `workflow.html`.
  **Büyüklük:** en büyük tek kalem; ön koşullarla birlikte ~250-300 satır, davranış değişikliği yok.
- **YAPILMAYACAK:** APCA'yı WCAG 2.2 AA yerine koymak. El kitabının kendi hükmü;
  `DESIGN.md`'de *The WCAG-Is-The-Standard Rule* olarak yazıldı. Repoda APCA kullanımı yok →
  bu bir yasak, bir iş değil.

### H7 — Komut paleti (⌘K) tek eylem yüzeyi; ⌘1-9 favoriler; her komutta kısayol ipucu **[ORTA]**

- **EKSİK — palet yok.** `meridian/web/app.js:4443-4459` klavye katmanı var ama **kasten
  modifier'sız**: `app.js:4444` `if (e.metaKey || e.ctrlKey || e.altKey) return;`. Yani ⌘K yolu
  şu an bilinçli olarak boş.
- **ZATEN VAR (tohum) — klavye altyapısı sağlam.** Görünüm tuşları `1`–`7` VIEWS dizisinden
  TÜRETİLİYOR (`app.js:4452-4455` — sabit "1234567" dizesi düzeltilmiş, liste ile kayamaz),
  `r` yeniden çizer, `?` yardım katmanı açar, `Escape` kapatır, çekmece açıkken arkadaki
  kısayollar ateşlenmez (`app.js:4451`).
- **EKSİK — kısayol ipucu görünmüyor.** Superhuman deseni (komutun yanında kısayol) yok;
  yalnız `?` katmanında toplu liste var.
  **Dokunulacak:** `app.js` (palet + fuzzy arama + kayıt), `index.html` (katman CSS'i).
  **Büyüklük:** büyük — ~200 satır, ve **her eylem paletten çağrılabilir olmalı** (VS Code kuralı),
  yani mevcut eylem fonksiyonlarının bir kayda bağlanması gerekir.
- **Not:** el kitabı "Cmd+K bazı, Cmd+P başka eylemler için KULLANILMAMALI" diyor — tek yüzey.

### H8 — Order/fill'de confirmed-state; reconciliation drift her zaman görünür **[GÜÇLÜ]**

*Kanıt:* Boeing 737 MAX — MCAS tek AoA sensöründen besleniyordu ve **AOA DISAGREE uyarısı çoğu
filoda opsiyonel bir ekstraydı**, etkin değildi; mürettebat veri sorununu hiç görmedi.

- **ZATEN VAR — ayna durumu confirmed-state olarak çiziliyor.** `meridian/web/app.js:611-615`:
  emir üç ayrı hâl taşıyor — `aynada` (onaylı) / `gönderilecek` (bekleyen) / `RET`
  (`failed_broker_rejection`). Optimistic "dolduruldu" hiçbir yerde bulunamadı.
- **ZATEN VAR — provenance HUD'da kalıcı.** `app.js:1090-1101` altı rozet; kaynak sağlayıcı
  `app.js:952` ve `app.js:1334`; rejim kaynağı `app.js:1840`; koruma kilidi `app.js:2585-2622`
  (uzlaştırma raporu). 737 MAX dersinin "her zaman görünür" kısmı **karşılanmış**.
- **EKSİK — sistem-geneli confirmed-state DENETİMİ yapılmadı.** Bir desen doğrulanmış olması tüm
  mutasyon yollarının doğru olduğunu göstermez; `apiFetch` mutasyonda önbelleği siliyor
  (`app.js:36-40`) ve render yeniden çağrılıyor — bu doğru yaklaşım ama her eylem için
  doğrulanmadı. **Büyüklük:** denetim turu, muhtemelen kod değişikliği az.

### H9 — Coverage matrix'te tek-hue sequential; drift için CVD-güvenli diverging **[ORTA]**

- **ÇELİŞİYOR (kısmen) — mevcut matris işaretle-diverging.** `.pm-cell.pos` /
  `.pm-cell.neg` (`meridian/web/index.html:348`) yeşil %8 / kırmızı %7 tint kullanıyor. Bu bir
  **coverage** değil bir **sonuç** matrisi; işaretin (kâr/zarar) iyi tanımlı bir referans değeri
  (sıfır) VAR, yani el kitabının "diverging yalnız iyi-tanımlı referans varsa" şartını
  **karşılıyor**. → Değiştirmeye gerek yok; el kitabının maddesi burada yanlış hedefe bakıyor.
- **EKSİK — asıl coverage yüzeyi (veri kapsaması / sembol kapsaması) için tek-hue sequential yok.**
  Kapsama okumaları şu an sayı+çip olarak veriliyor, ısı matrisi olarak değil.
- **EKSİK — viridis/mako gibi perceptually uniform ölçek repoda hiç yok.** Uygulanırsa
  **koyu temada üst-uç (sarı) yüksek luminance verir** ve anormallik sinyaliyle çakışır — el
  kitabının kendi "Refine" notu. Bu, `DESIGN.md`'nin Money Rule'uyla da gerilim yaratır (§4.2).

### H10 — Skeleton'ı yalnız öngörülebilir-yapı panellerine sınırla **[ZAYIF — §5.3]**

- **ZATEN VAR — ve zaten el kitabının istediğinden daha disiplinli.**
  `meridian/web/app.js:345-357`: iskelet **yalnız** görünüm tamamen boşken (ilk boyama) konur;
  daha önce render edilmiş sayfaya dönüşte **beklemek yok**, eldeki veri hemen gösterilir ve
  tazeleme arkada yürür. Ölçüm yorumda kayıtlı (`/api/diagnostics` 3,984 ms; ilk çağrı 11,130 ms).
  → **Yapılacak yok.** Bu madde kapalıdır.

---

## §3 — Staged listede olmayan maddeler

| # | Madde | Kova | Kanıt | Bulgu |
|---|---|---|---|---|
| H11 | Renk yalnız anormallik için (gri-öncelikli, Airbus light-out) | **ÇELİŞİYOR** | [GÜÇLÜ] | → §4.2 |
| H12 | Trend-first: gömülü trendler | **EKSİK** | [ORTA] | Yalnız iki mini seri: sermaye eğrisi `app.js:750`, IC mini-trendi `app.js:1211+`. Kart başına gömülü trend yaygın değil |
| H13 | Perceptual ranking + P&L üçlü kodlama (sign+arrow+hue) | **EKSİK (kısmi)** | [ORTA, evrensel değil] | Olay akışında ▲/△/· var (`app.js:681`), bir yerde daha (`app.js:729`). P&L satırlarında ok YOK — yalnız işaret + hue |
| H14 | Alert inhibition / normalization of deviance | **EKSİK (kısmi)** | [GÜÇLÜ] | Bastırma yasağı var (`app.js:585-595`) ama tersi — *kasıtlı* inhibition (ECAM T/O INHIBIT benzeri) ve "hep kırmızı panel" tespiti yok |
| H15 | HP-HMI 4 seviye + ~20 yeni display | **ÇELİŞİYOR** | [ORTA] | → §4.6 |
| H16 | Shelving/suppression UX | **EKSİK** | [YORUM] | H2 ile birlikte |
| H17 | Çoğu event alarm OLMAMALI → offline diagnostic | **EKSİK (kısmi)** | [GÜÇLÜ] | Seviye ayrımı var (`app.js:3423`) ama "yanıt gerekmiyorsa alarm değildir" testi kodlanmamış; olay akışı 12 satırla kırpılıyor (`app.js:679`) |
| H18 | Dual-encoding + CVD-güvenli / monokrom seçenek | **EKSİK** | [GÜÇLÜ] | Çipler kelime taşıyor (iyi), ama CVD-güvenli alternatif palet veya TradingView'in parlaklık-tabanlı monokrom modu yok |
| H19 | Gamification YOK (Robinhood anti-pattern) | **ZATEN VAR** | [GÜÇLÜ] | Konfeti/streak/leaderboard/rozet-ödülü aranıp bulunamadı. `DESIGN.md`'de *The No-Gamification Rule* olarak yazıya geçti |
| H20 | WCAG 2.2 AA: focus / target-size / non-text / text | **EKSİK (kısmi)** | [GÜÇLÜ] | Focus `index.html:105` (2px outline, 2px offset) ✔ · target 44px ≥ 24px şartı (`index.html:192`, `.dlbtn` `index.html:555`) ✔ · metin 4.5:1 iki temada da ✔ (ölçüldü) · **non-text 3:1 KALIYOR**: saç telleri 1,09–1,83 aralığında. `DESIGN.md`'de beyanlı sapma; tek gerçek maruziyet metin girişi kenarı |
| H21 | prefers-reduced-motion + hareket yalnız anormallik sinyali | **ZATEN VAR** | [ORTA] | `index.html:113, 437, 793`. Nabız animasyonu 2,6 sn (`index.html:182-183`) — el kitabının "≤300ms pulse yalnız anormallik" kuralına göre bu bir *canlılık* göstergesi, sapma değil; ayrımı `DESIGN.md`'ye yazmak gerekebilir |
| H22 | ARIA live yalnız kritik değişimlerde | **ZATEN VAR** | [ORTA] | Üç canlı bölge: `index.html:814` (giriş mesajı), `index.html:825` (durum hapı), `app.js:597` (triyaj). Hücre güncellemeleri duyurulmuyor — el kitabının istediği tam olarak bu |
| H23 | Klavye nav (j/k, roving tabindex, ARIA grid) | **EKSİK** | [ORTA] | Satır-içi j/k yok; kayıt açma Enter/Space ile çalışıyor (`app.js:241-246`), bu iyi ama liste gezinmesi değil |
| H24 | Yüksek-riskli eylemde iki adım + guarded switch | **ZATEN VAR** | [GÜÇLÜ] | Kapak deseni `app.js:312-327` (`kswrap`/`kscover`/`ksgroup`, dışarı tıklama + Esc kapatır); FLATTEN **iki kez** onaylatıyor (`app.js:1146` ve `app.js:1147` — ikincisi "geri alınamaz" diyor); `app.js:4180` aynı desen. Airbus guarded-switch mantığı karşılanmış |
| H25 | Yükleme eşikleri (Nielsen 0.1/1/10s; Doherty 400ms) | **ZATEN VAR (kısmi)** | [ZAYIF — §5.1] | Önbellek TTL 15 sn sunucunun 20 sn'lik bütünlük TTL'inin ALTINDA (`app.js:58-62`), boşta ön-yükleme sırayla (`app.js:46-62`). Nielsen eşikleri açıkça hedeflenmemiş ama davranış hizalı |
| H26 | Sayısal font gereksinimleri (0/O, 1/l/I, küçük punto) | **ZATEN VAR (bir uyarıyla)** | [GÜÇLÜ] | Ölçüldü — `DESIGN.md` § Typography. 0/O **ayrık** (eğik çizgi gömülü), 1/I **ayrık** (I'nin üst çizgisi var). **1/l ayrımı belgelenemedi**: iki glif de 2 kontur, 710 birim yükseklik, 488 birimlik ayak tırnağı; ölçülen fark gövde x-kayması 15 birim (**10px'te 0,15 px**) ve ayak yüksekliği 14 birim (**0,14 px**). Geometriyle karara bağlanamaz |
| H27 | OKLCH ile rampa üretimi; W3C DTCG jeton formatı | **EKSİK** | [ORTA] | `.impeccable/design.json` kendi şeması (schemaVersion 2), DTCG değil. Style Dictionary yok. **Tek geliştiricili, build-step'siz bir projede kazancı şüpheli** — düşük öncelik |
| H28 | 4px/8px grid + density modes (compact/comfortable) | **ÇELİŞİYOR (kısmen)** | [ORTA] | 4px tabanı ZATEN VAR (`index.html:62`, `--s1`…`--s12`). Density modes ise `DESIGN.md`'nin "tek yoğunluk" kararıyla çelişiyor → §4.5 |
| H29 | Grafana: RED / Four Golden Signals, drill-down, <20 panel | **EKSİK (kısmi)** | [ORTA] | Drill-down var (satır → çekmece, sistem geneli). RED/Golden Signals adlandırması yok. Panel sayısı sayılmadı |
| H30 | Bloomberg: yoğunluk + tutarlılık | **ZATEN VAR** | [ORTA] | Yoğunluk kararı `PRODUCT.md`'de bağlayıcı ("Density is not inherited" — Omega'nın ölçeği sıkıştırıldı). Tutarlılık: tek etkileşim (satır=kontrol) sistem geneli |
| H31 | Vigilance decrement → sağlıklı=görünmez | **ZATEN VAR** | [ORTA] | Triyaj şeridinin `calm` hâli tam olarak bu (`index.html:301-303`: şeffaf zemin, ince çizgi, 400 ağırlık) |
| H32 | Provenance/veri-sağlığı HER ZAMAN görünür | **ZATEN VAR** | [GÜÇLÜ] | H8'e bakınız |
| H33 | Belirsizlik görselleştirme (HOPs/quantile dotplot) | **EKSİK** | [ORTA] | H5'e bakınız — düşük öncelik |
| H34 | Renk ölçekleri: viridis ailesi; rainbow/jet yasak | **EKSİK** | [GÜÇLÜ] | Repoda hiç sürekli renk ölçeği yok → rainbow riski de yok. İhtiyaç doğarsa H9 ile birlikte |
| H35 | Uzman lehine yoğunluk / discoverability ödünü | **ZATEN VAR** | [ORTA] | Beş görünüme konsolidasyon (`app.js:4-11`), sekiz sayfa üç çift hâlinde aynı soruyu iki yerden cevaplıyordu |

---

## §4 — ÇELİŞENLER ve önerilen hükümler

### §4.1 — Gauge yasağı ↔ canlıdaki üç analog gösterge **[el kitabı GÜÇLÜ / karar operatörün]**

Mevcut:

| Gösterge | Tanım | Kullanım |
|---|---|---|
| `_donut(pct, label, color)` | 92×92 SVG halka, `stroke-dasharray` yayı | `meridian/web/app.js:1186-1198`; çağrı `app.js:1662` (deflasyon); sarmalayıcı `.gaugewrap` `index.html:707-713` |
| `_ring(step, total, label, danger)` | aynı geometri, adım/toplam | `app.js:1199-1210`; çağrı `app.js:2515` ("EOD sabır", refetch denemesi/8) |
| `.thermo` termometre | 14×86 dikey tüp, `--fill` ile `scaleY` | `index.html:714-720`; çağrı `app.js:1709-1710` (ısınma) |

Few'nun spesifikasyonu bunları doğrudan hedef alıyor: *"The bullet graph was developed to replace
the meters and gauges that are often used on dashboards."* Radyal kodlama açı/alan kullanır;
Cleveland & McGill sıralamasında bu, konum/uzunluğun altındadır.

**Nüans — üçü aynı değil.** `.thermo` zaten **lineer**dir; yalnızca dikeydir. Yasak radyal
kodlamayadır, dikey bara değil. Yani:

**Öneri:**
1. `_donut` ve `_ring` **kaldırılsın**, yerine yatay bullet graph gelsin. `_ring`'in
   "adım/toplam" anlamı zaten ayrık bir sayaçtır — `3/8` metni + bar, halkadan daha okunur.
2. `.thermo` **kalsın**, `DESIGN.md`'nin izin verdiği iki lineer metre formundan biri olarak
   yazıya geçsin (bu turda geçti).
3. **Kayıp uyarısı:** `_donut`'un `pct == null` hâli boş halka + "—" çiziyor (`app.js:1187`,
   "uydurma açı çizilmez"). Yeni bileşen bu dürüstlüğü **korumak zorunda** — bullet graph'ın boş
   hâli de bir sıfır barı DEĞİL, "ölçüm yok" olmalı.
   **Büyüklük:** ~60 satır silme + ~70 satır yeni bileşen + 3 çağrı yeri.

### §4.2 — "Renk yalnız anormallik için" ↔ Money Rule **[gerçek felsefi çatışma]**

- **El kitabı (ASM/ISA-101, Airbus light-out):** renk = **anormallik**. Normal durum renksizdir.
  Kokpit sistemler normalken karanlıktır. Anti-pattern: bir grafikte kırmızının 13 farklı şeyi
  kodlaması.
- **Meridian (`DESIGN.md`, operatörün bağlayıcı tercihi):** renk = **ölçüm/para**. Yeşil kâr
  demektir, ve kâr *normal* bir durumdur.

Çakışma noktaları somut: `.pos{color:var(--green)}` (`index.html:107`), sermaye eğrisi yükselirken
yeşil çizilir (`app.js:756`), nabız noktası sağlıklıyken yeşil yanar (`index.html:181`). Katı
light-out felsefesinde bunların üçü de renksiz olurdu.

**Önerilen hüküm (operatör onayına):** **Money Rule kazanır, ama iki kanal ayrılır ve bu yazıya
geçer.**
- Yeşil/kırmızı bir **ölçüm** kanalıdır — para. Sürekli görünür olmaları normaldir çünkü sürekli
  bir sayıyı bildiriyorlar, bir alarmı değil.
- Kehribar/kırmızı-durum bir **alarm** kanalıdır — insan gerekir. Bu kanal light-out'a TABİDİR:
  hiçbir şey beklemiyorsa hiçbir şey yanmaz (triyaj şeridinin `calm` hâli zaten böyle).
- **Yasak aynen geçerli:** aynı rengin 13 şeyi kodlaması. Meridian'da kırmızı yalnız iki iş yapar
  (negatif sonuç · para kaybettirebilecek kontrol) ve bu sayılabilir olmalı.
- **Yeşil nabız noktası tartışmalı kalıyor** — sağlıklı bir sistemi yeşille bildirmek ASM'nin tam
  olarak kaldırdığı şey. Karar operatörün: ya nötr renge iner, ya "ölçüm kanalı" sayılır. Bu
  belge kendi başına karar vermiyor.

### §4.3 — Font tablosu (Inter / IBM Plex) ↔ Geist **[çözüldü]**

El kitabının tablosu Inter/IBM Plex Mono/JetBrains Mono öneriyor; operatörün notu zaten
"kullanmak ZORUNDA DEĞİL — gereksinim fonta değil ÖZELLİĞE bağlıdır" diyor. Bu turda özellik
ölçüldü (H4/H26) ve **Geist Mono gereksinimi karşılıyor**. **Font göçü YOK.** Tek açık uç:
`1`/`l` çifti (§5.4).

### §4.4 — Bloomberg amber/siyah ↔ operatörün Omega açık zemini **[iki-tema kararıyla çözüldü]**

El kitabı Bloomberg'in korunmuş koyu zeminini ve yoğunluk dilini övüyor. `PRODUCT.md` açık Omega
zeminini bağlayıcı kılmıştı. İki-tema kararı bunu çözüyor: gece zemini düşük-ışık durumunu
karşılıyor, **Bloomberg'in amber/siyahını benimsemeden**. Bloomberg'den alınan tek ders, el
kitabının kendi vurguladığı ders: **tutarlılık** ("You changed perfection! I have a headache!").
→ Bu, tema anahtarının **düzen/geometri değiştirmemesi** kuralının gerekçesidir; `DESIGN.md`'ye
yazıldı.

### §4.5 — Density modes ↔ tek yoğunluk **[öneri: el kitabına uyma]**

El kitabı compact/comfortable ikilisi öneriyor ama "tek uzman operatör için compact varsayılan"
diyor. `PRODUCT.md` yoğunluğu zaten bağlayıcı kılmış (Omega'nın 20px dolgusu ve 21px yarıçapı
24px/12px'e sıkıştırıldı, sebebi yazılı: dört sütunlu matris dizüstünde kaymadan sığsın).
**Öneri: ikinci mod EKLENMESİN.** Tek operatörlü bir konsolda ikinci yoğunluk, kas hafızasını
ikiye bölmekten başka iş görmez ve §4.4'teki tutarlılık dersiyle çelişir.

### §4.6 — "~20 yeni display" ↔ beşe konsolidasyon **[öneri: el kitabına UYMA]**

Hollifield ~1 Level-1 + bir düzine Level-2 + birkaç abnormal-situation display öneriyor.
Meridian sekiz sayfadan **beşe indirildi** ve gerekçesi kodda yazılı (`app.js:4-11`: üç çift
aynı soruyu iki yerden cevaplıyordu). Yirmi display bu konsolidasyonu geri alır.

**Öneri:** display SAYISI değil, **seviye NETLİĞİ** benimsensin (H1'in üçüncü maddesi). Her
görünümün hangi seviyeye ait olduğu yazılsın, bir okuma iki seviyede tekrarlanmasın. Sayıyı
kopyalamak, süreç-endüstrisi ölçeğini (yüzlerce etiket, onlarca ünite) tek operatörlü bir
araştırma sistemine taşımak olur — el kitabının kendi transfer caveat'ının tam da uyardığı hata.

---

## §5 — ZAYIF KANITLI MADDELER (el kitabının kendi caveat'larıyla)

Bu maddeler uygulanabilir ama **kanıtları diğerleriyle aynı ağırlıkta değildir**. Bir uygulama
turu kapasitesi biterse önce burası düşer.

### §5.1 — Doherty threshold (400ms) **[ZAYIF]**
El kitabının kendi ifadesi: *"Doherty threshold (400ms) zayıf kanıt — modern replikasyonu yok."*
Yerine Nielsen'in 0.1 s / 1 s / 10 s eşikleri öneriliyor.
→ **Hüküm: 400ms'i bir hedef olarak yazmayın.** Mevcut önbellek/ön-yükleme davranışı
(`app.js:47-65`) zaten Nielsen'e hizalı. Yapılacak iş yok.

### §5.2 — Dark-mode okunabilirliği **[ZAYIF — ve yönü TERS]**
El kitabının kendi ifadesi: *"en çok alıntılanan halation kaynağı (Harrison, UBC) hakemli değil.
Piepenbrock sağlam ama positive-polarity lehine — dark tema okuma performansı için değil,
ortam/konfor için savunulmalı."* Sethi & Ziat (2023) dark mode'da daha düşük algılanan bilişsel
yük buldu, ama ortam- ve yaş-bağımlı.
→ **Hüküm:** koyu tema **eklenir** (operatör kararı, §H6) ama gerekçesi belgede **"24/7 düşük-ışık
ergonomisi"** olarak yazılır, "daha iyi okunur" olarak DEĞİL. `DESIGN.md`'de *The
Polarity-Honesty Rule* olarak yazıldı; astigmatizm ~%40-47 ve halation riski açıkça kaydedildi;
açık tema **varsayılan** kalır. Şikâyet gelirse tepki: metin luminance'ını `#cccccc`'ye indir,
ağırlığı artır — savunmaya geçme.

### §5.3 — Skeleton screen'ler **[ZAYIF — vendor-driven]**
El kitabının kendi ifadesi: *"'%20-30 daha hızlı' iddiaları vendor-driven, aynı Viget çalışmasına
atıfla, oysa Viget'in kendi bulgusu skeleton aleyhine."* Viget 2017: skeleton'lar spinner ve
blank'e göre algılanan sürede EN KÖTÜ.
→ **Hüküm: yapılacak iş yok** (H10). Mevcut kod zaten iskeleti yalnız ilk boyamaya sınırlıyor.
Skeleton'ı yaygınlaştıran hiçbir öneri kabul edilmemeli.

### §5.4 — APCA **[ÇEKİŞMELİ]**
El kitabının kendi ifadesi: *"APCA WCAG 3'ün onaylı metodu DEĞİL (Temmuz 2023'te Working Draft'tan
çıkarıldı; Nisan 2026'da TBD). 'WCAG 2'nin %49 yanlış-geçişi' iddiası Myndex/APCA-yanlısı
kaynaktan, bağımsız değil."*
→ **Hüküm:** WCAG 2.2 AA standart; APCA yalnız tasarım-zamanı yardımcı. `DESIGN.md`'de kural
olarak yazıldı. Repoda APCA kullanımı yok → uygulanacak iş yok, **korunacak yasak var**.

### §5.5 — HP-HMI 5× rakamları **[transferi kanıtlanmamış]**
El kitabının kendi ifadesi: *"process-control endüstri çalışmaları; yazılım dashboard'a transfer
makul ama birebir kanıtlanmış DEĞİL. Yön ve mekanizma (deviation-surfacing) sağlam."*
→ **Hüküm:** mekanizma (sapmayı yüzeye çıkarmak, sağlıklıyı gizlemek) benimsenir; **rakam
alıntılanmaz**. Meridian'ın hiçbir yüzeyinde "5× daha hızlı tespit" yazmaz.

### §5.6 — EEMUA 191 hedeflerinin yazılıma uyarlanması **[YORUM]**
El kitabının kendi ifadesi: *"process-industry kaynaklı, yazılım-bildirimlerine uyarlama YORUMDUR."*
→ **Hüküm:** %80/15/5 ve <10/10dk **hedef** olarak alınabilir ama **eşleme kararı önce yazılır**
(H2). Uydurma yasağı: eşleme kayıtlı değilse yüzde raporlanmaz.

### §5.7 — Cleveland/McGill sıralaması **[evrensel değil]**
El kitabının kendi ifadesi: *"McColeman ve ark. sıralamanın göreve bağlı olduğunu, cardinality
gibi faktörlerin encoding seçiminden daha etkili olabileceğini buldu."*
→ **Hüküm:** gauge yasağı (§4.1) yine de geçerli — orada sorun yalnız kodlama doğruluğu değil,
Tufte'nin data-ink argümanı (veri taşımayan piksel). Ama "konum her zaman en iyidir" diye bir
kural yazılmaz.

### §5.8 — ARIA live-region kapsamı **[over-engineering riski]**
El kitabının kendi ifadesi: *"tek görüşür operatör için tam WCAG kapsamı bazı yerlerde
over-engineering olabilir; focus/contrast/target-size hijyeni yine de herkese fayda sağlar."*
→ **Hüküm:** mevcut üç canlı bölge yeterli (H22). Genişletme önerisi gelirse reddedilir.
`PRODUCT.md` § Accessibility'ye beyanlı sapma olarak yazıldı.

---

## §6 — Sayım

| Kova | Adet | Maddeler |
|---|---|---|
| **ZATEN VAR** | **12** | H4 (tabular/slashed-zero kısmı) · H10 · H19 · H21 · H22 · H24 · H26 · H30 · H31 · H32 · H35 · H5'in None≠0 çekirdeği |
| **EKSİK** | **17** | H2 · H3 (bullet+band) · H5 (imputation) · H6 · H7 · H8 (denetim) · H9 · H12 · H13 · H14 · H16 · H17 · H18 · H20 (non-text 3:1) · H23 · H27 · H29 · H33 · H34 |
| **ÇELİŞİYOR** | **6** | §4.1 gauge · §4.2 renk felsefesi · §4.3 font (çözüldü) · §4.4 Bloomberg (çözüldü) · §4.5 density modes · §4.6 20 display |

**Not — sayım dürüstlüğü:** EKSİK kovasındaki 19 satır 17 maddeye denk geliyor çünkü H3 ve H5
hem ZATEN VAR hem EKSİK parça taşıyor; her ikisi de EKSİK'te sayıldı (yapılacak iş var). H4 ve
H20 de bölünmüş; ana hükümleri ZATEN VAR / EKSİK olarak tek yerde sayıldı. Toplam 35 maddenin
tamamı bir kovaya düştü.

Ayrıca kovalara ek olarak **3 ön koşul** (§0: P1 sabit renkler · P2 tema altyapısı · P3 `--r-pill`)
ve **8 zayıf-kanıtlı hüküm** (§5) var; bunlar el kitabı maddesi değil, uygulamanın önkoşulu ve
sınırıdır.

## §7 — Doğrulanamayanlar / ölçülmedi

Uydurma yasağı gereği açıkça: aşağıdakiler bu turda **ölçülemedi** ve varsayılmadı.

1. **`1` / `l` ayrımının 10–11px'te algısal yeterliliği — ÖLÇÜLMEDİ.** Geometri ölçüldü ve ayrımı
   0,15 px mertebesinde çıktı; algısal karar için render + gözlemci testi gerekir, bu tur onu
   yapamadı. → Uygulama turunda: iki glifi 10px ve 11px'te operatörün ekranında yan yana bas.
2. **Google Fonts'un servis ettiği Geist Mono derlemesinin özellik listesi — ÖLÇÜLMEDİ.**
   Ölçülen dosya yerel `GeistMono-Medium.ttf` v1.401 (Raycast paketi). Google `geistmono/v6`
   sunuyor ve unicode-range ile alt kümeliyor; alt kümeleme özellik düşürebilir. WOFF2 indirip
   açmak bu turun yetkisi dışında.
3. **Geist SANS'ta `ss01` ve `cv11` var mı — ÖLÇÜLMEDİ.** Makinede sans kopyası yok. Yalnız
   Geist MONO'da `cv11`'in bulunmadığı kesinleşti.
4. **Pano panel sayısı (<20 hedefi) — SAYILMADI.** Grafana'nın eşiği için görünüm başına panel
   sayımı yapılmadı.
5. **Mevcut sistemin gerçek alarm oranı — ÖLÇÜLEMEZ.** Seviye taksonomisi var ama EEMUA eşlemesi
   yapılmadığından %80/15/5'e karşı bir ölçüm yapılamaz. Eşleme bir hükümdür, ölçümden önce gelir.
6. **`DESIGN.md`'nin eski üç kontrast iddiası — YENİDEN ÜRETİLEMEDİ.** "ink-muted 4,63", "caution
   4,90", "Omega grisi 2,89" bu turda sırasıyla **5,93 / 6,29 / 3,12** ölçüldü. Eski sayıların
   hangi zemine karşı alındığı bilinmiyor. `DESIGN.md` § *Measurement provenance*'a düzeltme olarak
   işlendi; `meridian/web/index.html` içindeki iki yanlış yorum (`#585450 (4.51:1)` → gerçek
   **7,50**; üst bar `5.64` → gerçek **6,55**) **düzeltilmedi**, çünkü bu tur `meridian/web/*`
   dosyalarına dokunmuyor. Uygulama turunun ilk kalemi olabilir.
7. **Tarayıcıda görsel doğrulama — YAPILMADI.** Kontrast oranları WCAG 2.x formülüyle hesaplandı
   (alfa bileşimi 8-bit sRGB'de, tarayıcının yaptığı gibi), ama hiçbir sayı canlı bir sayfada
   DevTools ile karşılaştırılmadı. Bu belgedeki sayılar **hesaplanmış**tır, **gözlenmiş** değil.
