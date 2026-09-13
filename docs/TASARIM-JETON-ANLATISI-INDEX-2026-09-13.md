# Tasarım jeton anlatısı — `meridian/web/index.html` (TSK-132 dilim-3, 2026-09-13)

**BU METİN TARİHÇEDİR. HÜKÜM BURADA DEĞİL.** Yürürlükteki jeton adları ve değerleri
`meridian/web/tokens.json` (SSoT) içindedir; `index.html`in jeton bloğu artık
`ops/jeton_css_uret.py` tarafından ORADAN üretilir ve bayt-eşitliği
`tests/test_jeton_eski_sayfalar_v437.py` ile çivilidir. Aşağıdaki metin, üretime geçmeden
ÖNCE o bloğun içinde ve çevresinde duran tasarım gerekçesinin BİREBİR kopyasıdır — üretim
onu silerdi, silinmesin diye buraya alındı. Bir çelişki görürsen kod/`tokens.json` kazanır;
bu belge yalnız "niye böyle olmuştu"yu anlatır.

Belge TEK KEZ, göç anında yazıldı ve yeniden üretilemez (kaynağı artık yok): donmuş bir
kayıttır, üretilmiş bir dosya değildir. Elle düzeltme/genişletme de yapılmaz — düzeltilecek
bir hüküm varsa yeri `tokens.json` ya da yeni bir karar kaydıdır.

## Kaynak

| Alan | Değer |
|---|---|
| Dosya | `meridian/web/index.html` (`<style>` içindeki jeton bölgesi) |
| Bölge, O GÜNKÜ hâliyle | satır 126–733 — bir ÇAPA DEĞİL, göç anının kaydı (satır kayar, bu sayı bayatlar) |
| Kaynak commit (HEAD) | `8921102c27aaf9313bc01361e6cc9240d96e0e6f` |
| Anlatı bloğu | 56 |
| Anlatı satırı | 504 |
| ANLATI-SHA256 | `2258c5ce2b458e197c7653d26a840b06d50d3fad40e70c9a6eb327cc30e6efa8` |

`ANLATI-SHA256`, aşağıdaki ```` ```css ```` bloklarının gövdelerinin sırayla `\n` ile
birleştirilip UTF-8 olarak özetlenmesidir. Çivisi: `tests/test_jeton_eski_sayfalar_v437.py`
(bölüm (h)) — beyan ile içerik ayrışırsa kırmızı olur, yani bu belgenin metni sessizce
düzenlenemez.

## Bloklar

Bloklar `index.html`teki SIRALARIYLA verilmiştir. Gövdeler BİREBİRdir: CSS yorum işaretleri
(`/* … */`) ve girintiler dahil, düzeltilmeden. İki blokta metin `hue/L*/` dizgesiyle
karşılaşır ve CSS grameri orada yorumu ERKEN kapatırdı — kuyruk yine de anlatıya aittir ve
kendi bloğunda, kesilmeden durur.

### Blok 01

```css
  /* MONO ARTIK YALNIZ ÖLÇÜLEN DEĞERDE (2026-08-24, operatör: "yazı tipleri hala eski").
     `docs/HUKUM-2026-08-24-YAZITIPI.md`in gerekçesinin TAMAMI RAKAMLARLA ilgili — `1`/`l` ve
     `0`/`O` ayrımı. Yani mono'nun yerini hak ettiği yer bir ÖLÇÜMDÜR. Büyük-harf ETİKETLERDE
     mono kullanmak bir okunaklılık ihtiyacı değil, emekli Omega sesiydi ve ekranda "eski yazı
     tipi" diye okunan şey buydu. Yirmi sekiz etiket kuralı mono'yu bıraktı ve `--sans`a
     (Inter) kalıtıyor; SAYI taşıyan her kural (`.mono-num` · `.bignum` · `.km-cell` ·
     `.mcard .v` · `.srow b` · `.tbl .num` · `.evrow .etime` · `.twin .tb` · `.pm-yield` ·
     kod/kbd bağlamları) mono'da KALDI — hükmün koruduğu şey orası. */
```

### Blok 02

```css
  /* spacing — one 4px base */
```

### Blok 03

```css
  /* ==========================================================================
     DUB DÖNÜŞÜMÜ (KARAR-2026-08-24-B) — JETON ADLARI DEĞİŞMEDİ, DEĞERLERİ DEĞİŞTİ.
     --------------------------------------------------------------------------
     TOKEN ADLARI DEĞİŞMEZ: app.js DOM'u çalışma anında üretir, isim sözleşmesi
     bağlayıcıdır. Değişen YALNIZ değer katmanıdır: Omega'nın SICAK kemik rampası
     (#fbf9f8 / #f2efed / #e2deda) emekli edildi, yerine Dub'ın SOĞUK nötr rampası
     geldi. Ad = Dub'ın kendi adı; uydurma ad yok.

     ÖLÇÜM VE HÜKÜM: research/olcumler/dub_donusumu_2026-08-24/ (olc.py + RAPOR.md +
     sonuc.json) · docs/kontrast-denetimi.md §12. Aşağıdaki HER sayı o betikten gelir;
     elle yazılmış tek bir oran yoktur.

     ---- EMEKLİ EDİLEN ÖLÇÜMLER (TARİH — SİLİNMEZ, ÜSTÜ ÇİZİLİR) ----
     ~~WP-P/P6/P9 (2026-08-02): --bg:#fafafa;
       "sıcak kırık-beyaz" hükmü Dub dönüşümüyle DÜŞTÜ.~~
     ~~D1 (2026-08-07): yön-artı #40654c (C 0,0588) · yön-eksi #784e4b (C 0,0575) ·
       mod-canlı #723a96 (C 0,150) · mod-keşif #635071 (C 0,057).~~
     Eski YÜZEY değerleri artık yürürlükte DEĞİL; kayıt izlenebilirlik için burada duruyor.
     (Emekli listesinde jeton adları BİLEREK `--` öneksiz yazılıyor: bu blokta bir toplu
      düzenleme yapıldığında yorumdaki tarihsel kayıt bir BİLDİRİM sanılıp üzerine
      yazılabiliyor — 2026-08-24'te bir kez yaşandı ve blok bozuldu.)

     ---- ŞİDDET ÜÇLÜSÜ DUB'A GERİ DÖNDÜ — TAŞIYICI DEĞİŞTİĞİ İÇİN (karar §10.2) ----
     ~~Aynı günün sabahı: "ŞİDDET ÜÇLÜSÜ DUB'DAN ÇIKTI (§9.4)". Ölçüm doğruydu ama SORU
       yanlıştı: renk METİN kaldığı sürece Dub'ın yeşil/turuncu hue'ları AA'yı (4,5) tutacak
       kadar koyulaşamıyordu ve koyulaşırken kromalarının yarısını harcıyorlardı. Beşinci
       seçenek eşiği 0,1 payla geçti ve paylı arama İKİ TEMADA DA BOŞ döndü — o pay, rengin
       metin olmasının kendisiydi.~~
     ALTINCI SEÇENEK BU DUVARI KALDIRDI: renk metin olmaktan çıkıp İŞARET olunca tavan
     4,5'ten metin-dışı 3:1'e çıktı, ve Dub'ın KENDİ hue'ları geri kullanılabilir hâle geldi:
       yeşil  146,4° = `vivid-green`ın hue'su, AYNEN
       turuncu 50,0° = `tangerine`ın hue'su, AYNEN
       kırmızı 26,6° = TÜRETME, beyanlı (Dub'da kırmızı YOK; `tangerine`dan 23,4° uzakta bir
                       kızıl bandı, ΔE2000 16,81/19,05 ile ölçülmüş ayrımı taşıyor)
     Yani §9.4'ün "Dub üç ayrık hue taşımaz" teşhisi İKİ hue için düşmüştür, üçüncüsü için
     hâlâ geçerlidir ve orası türetme olarak damgalıdır. `lavender` MOD'a, `electric-blue`/
     `deep-sapphire` ROL 6'ya kalıcı ayrılmış olarak KALIR. Bkz. docs/kontrast-denetimi.md §12.7.
     ========================================================================== */
```

### Blok 04

```css
  /* ROL 1 · YAPI — akromatik SOĞUK gri (Dub nötr rampası). Yapı hue TAŞIMAZ.
     İKİ SAF UÇ karar §1.1'de çözüldü ve ÖLÇÜLDÜ (Ö1):
       · Sayfa zemini #fafafa — Dub uygulamasının kendi zemini. Y=0.956 < saf beyaz 1.0,
         yani P9'un parlama kısıtı KORUNUR. Kartlar #ffffff kalır (P9 ölçümü --bg
         hakkındaydı, kart hakkında değil) ve kart/zemin adımı 1.0438 ≥ 1.02 (Ö1 TUTTU).
       · Birincil eylem dolgusu --accent:#0a0a0a; emeklilikleri Rol-1'in hükmüdür (bkz. docs/kontrast-denetimi.md §12.6). */
```

### Blok 05

```css
  /* hairlines, not boxes — Dub `ash` / `smoke`. SOĞUK nötr, sıcak değil. */
```

### Blok 06

```css
  /* Mürekkep merdiveni: midnight-ink / steel / fog. ÜÇ GERÇEK BASAMAK (B1 hükmü korunur):
     kart üstünde 19.80 / 7.81 / 4.74 — tx2↔tx3 adımı 1.65, ikisi de AA. */
```

### Blok 07

```css
  /* AKSAN HÂLÂ KROMA TAŞIMAZ. "Renk yalnız ölçüme aittir" kuralının çekirdeği Dub'a
     rağmen durur: birincil eylem dolgusu mavi DEĞİL midnight-ink'tir (Dub da öyle yapar).
     Gezinme mavisi AYRI bir roldür (ROL 6, aşağıda) ve eylem dolgusuna girmez. */
```

### Blok 08

```css
  /* ROL 2 · ŞİDDET — TAŞIYICI DEĞİŞTİ (karar §10.2, 2026-08-24 · ALTINCI SEÇENEK).
     ŞİDDET RENGİ ARTIK METİN DEĞİL, İŞARETTİR. Çipin/satırın yazısı nötr mürekkebe
     (--tx) geçti; renk noktaya, sol şeride, kenara ve kalın alt çizgiye taşındı. Dub'ın
     kendi "feature pill" grameri budur: aksan yüzer, gövde nötr kalır.

     BU BİR GEVŞETME DEĞİL. ÖE1-c (%10 tint üstünde ≥4,5) metne uygulanmaya DEVAM ediyor —
     ama metin artık nötr, yani şart daha KOLAY değil daha SIKI karşılanıyor: ölçüldü,
     nötr yazı kendi tinti üstünde 15.11-17.46 (renkli mürekkep 4,5'in kıyısındaydı).
     Renge uygulanan şart metin-dışı 3:1'e döner (WCAG 2.2 1.4.11) çünkü renk artık
     metin değildir — ve 3:1 HER GERÇEK ZEMİNDE ölçülür, yalnız kartta değil.

     HUE KAPISI (bu turda üç ölçüm aracı hatası yakalandı; ikisi hue savrulmasıydı):
     üç hue ÖNCEDEN sabitlendi — yeşil 146,4° · turuncu 50,0° · kırmızı 26,6° (LAB) — ve
     üretilen her rengin hue'su GERİ ÖLÇÜLDÜ. Sapma ≤1,0°: 145,59 / 49,13 / 27,29.
     Gamut kırpması hue'yu savurursa aday REDDEDİLİR (kırpılmış aday kabul edilmez).

     MERDİVEN DURUYOR: şiddet arttıkça mürekkep zeminden UZAKLAŞIR — gündüz sev-1 en KOYU,
     gece en AÇIK; nominal (sev-3) zemine en yakın olandır. Basamak oranı 1,28'dir,
     eşik 1,20 DEĞİL: pay İNŞADADIR, ölçüm hâlâ 1,20'ye karşı yapılır.

     ÖLÇÜLDÜ (gündüz · research/olcumler/oe1_dub_dorduncu_2026-08-24/olc.py üreticisi,
     hue kapısı eklenmiş):
       ÖE1-a  sev-1↔sev-2 1.260 · sev-2↔sev-3 1.284            (eşik ≥1,20)
       ÖE1-b  ΔE2000 16.81 / 61.34                              (eşik ≥15)
       İŞARET kart üstünde 6.25 / 4.96 / 3.87 · en kötü gerçek zemin (--bg2) 5.74 / 4.55 /
              3.55 · KENDİ %10 tinti üstünde 5.22 / 4.29 / 3.16 (eşik ≥3, metin-dışı)
       ÖE1-c  ÇİP METNİ (--tx) kendi tinti üstünde 16.53 / 17.13 / 17.46 (eşik ≥4,5)
     KROMA KAZANCI (OKLCh): kehribar +%94 · yeşil +%50 · kırmızı +%19. Kök neden çözüldü:
     luminans merdiveni koyulaştırdığı için kroma harcıyordu; taşıyıcı metinden işarete
     geçince merdivenin tavanı 4,5'ten 3:1'e çıktı ve kroma serbest kaldı.
     ~~Emekli (2026-08-24 sabahı): yeşil #1f7646 · kehribar #77520e · kırmızı #9a0019;
       renk METİNDİ ve ΔE payı 0,1 idi.~~ Ayrıntı: docs/kontrast-denetimi.md §12.7. */
```

### Blok 09

```css
  /* ROL 5 · SERİ — MAKETİN HUE AİLESİNE GEÇTİ (2026-08-24 · operatör kararı).
     ~~ADLAR TARİHSELDİR: --violet / --violet2~~ İKİ AD DÜŞTÜ. Gerekçe: değerleri artık
     `--lavender` ve `--sky`nin birebir kopyasıydı ve bu deponun tekrar eden kusuru tam
     olarak "aynı rengin iki adı" — biri güncellenir, öteki bayatlar. Tüketiciler
     (`.pv-nk.s2/s3` · `.pv-seri-1/2` · `.pv-seri-uc-1/2` · `.pv-sw-1/2` · `IC_SERI`)
     doğrudan `--lavender`/`--sky` okuyor.

     ~~NİYE TEK HUE (eski §10.4 kuralı: aynı büyüklüğü ölçen seriler tek hue + farklı
     açıklık)~~ KURAL DEĞİŞTİ. Operatör: "hue kullanmak gerekiyorsa kullanabilirsin hatta
     güzel duruyor" (2026-08-24) ve üç kez "maketin renklerini kullan". Onaylanan maket
     serileri AÇIKLIKLA değil HUE ile ayırıyor. Eski kuralın koruduğu şey — "iyi/kötü diye
     okunmasın" — hâlâ korunuyor: seri ailesi mavi-mor bandında kaldı, YEŞİL ve TURUNCU
     bilerek DIŞARIDA bırakıldı (onlar şiddet/yön rolleri). Yani değişen ayrım KANALI
     (açıklık → hue), yasak hue'lar değil.

     ÖLÇÜLDÜ (ölçütler aşağıda, hepsi bu turda yeniden hesaplandı):
       seri üçlüsü = sapphire #1e40af · lavender #7c3aed · sky #3b82f6
                     (gece: #3b82f6 · #a78bfa · #93c5fd)
       ~~ÇG1 komşu ΔL* ≥15~~ → bu üçlüde 2.7/11.5; ayrım artık açıklıkta DEĞİL.
       ÇG1′ (yeni, ÖLÇÜLDÜ) ikili ΔE2000-min 15.3 (gündüz) / 17.6 (gece) — eşik ≥15,
             eski ÇG1'in sayısal sertliği korunarak doğru eksene taşındı.
       ÇG2  kart üstünde 8.72 / 5.70 / 3.68 (gece 4.11 / 5.56 / 6.9) — eşik ≥3 AYNEN.
       ÇG3  kesik-çizgi İKİNCİ KANAL AYNEN KORUNUR; hue onun ÜSTÜNE eklendi, yerine değil.
     `--blue` (#2563eb / #60a5fa) üçlünün parçası DEĞİL: TEK-SERİ grafiklerin (sermaye
     eğrisi, alan dolgusu, kıvılcım) ve huninin giriş basamağının rengi. Maketin grafiği de
     bunu kullanıyor (`stop-color="var(--blue)"`). */
```

### Blok 10

```css
  /* MAKETİN KENDİ JETONLARI (2026-08-24, operatör: "mockup'daki renkleri kullanman lazım",
     "grafik te aynı şekilde mockup'da daha güzel duruyor"). TÜRETMEK BIRAKILDI.
     ~~#003346·#005b79·#0086b1 (196° teal — gri okunuyordu)~~ ~~#00277a·#0044d6·#3374ff~~
     Kaynak: `scratch-panov2/index.html` (onaylanan maket) — electric-blue · lavender ·
     deep-sapphire, maketteki değerleriyle BİREBİR.
     `--blue` TEK-SERİ grafiklerin rengidir (sermaye eğrisi, alan dolgusu, kıvılcım) ve
     maketin grafiği de bunu kullanıyor (`stop-color="var(--blue)"`).
     ÜÇ-SERİ (IC) grafiği AYRI üçlü kullanır: sapphire · lavender · sky. Gerekçe ÖLÇÜLDÜ —
     blue+lavender+sapphire üçlüsünde UÇ İKİ seri ΔE2000 13.2 (gece 10.6) ile birbirine
     karışıyordu; sapphire+lavender+sky'da ΔE-min 15.3 (gece 17.6) ve kart-oranı min 3.68.
     Yeşil BİLEREK üçlüye alınmadı: ΔE'si bol ama şiddet ("ok") hue'suyla çakışırdı. */
```

### Blok 11

```css
  /* HUNİ BASAMAK RENKLERİ — AYRI JETON AİLESİ (2026-08-24, OPERATÖR KARARI: "canlılık istiyorum").
     NİYE SERİ JETONLARINDAN AYRI: `--sapphire/--blue/--sky` üçlüsü ÇG1'e (komşu ΔL* ≥15) ve
     kroma tavanına (≤0,75 × şiddet) çivili ve o üçlü IC grafiğini, seri lekelerini, efsaneyi
     besliyor. Huni ise KENDİ kartının içinde bir arka-plan bandıdır ve basamakları AYRICA
     metinle+sayıyla etiketli. İki işi tek jetonla yapmak, birinin kısıtını ötekine dayatıyordu —
     huninin "tek mavi" görünmesinin sebebi tam olarak buydu.
     MAKETİN ÜÇLÜSÜ ALINAMADI ve gerekçe ölçüldü: `#2563eb`→`--nav` · `#7c3aed`→`--mod-canli`
     (BİREBİR hex) · `#16a34a`→şiddet yeşilinin hue'su. Maketin üç rengi de bizim ÜÇ SİNYAL
     bandımızın içinde; kopyalamak canlı-para çipini bir dekorasyonla karıştırırdı.
     OPERATÖR KARARIYLA GEVŞETİLEN TEK ŞEY KROMA TAVANI (bir SES YÜKSEKLİĞİ kısıtıydı).
     GEVŞETİLMEYENLER — bunlar KARIŞMA kısıtları, gevşetmek rengi güzelleştirmez sinyali bozar:
       · mod bandı (OKLCh 285-335°) ve nav bandı (255-272°) — ikisine de 8° PAY bırakıldı
       · şiddet üçlüsü + yön çiftine ΔE2000 ≥ 15
       · renk körü LUMİNANS merdiveni: komşu ΔL* ≥ 15 (tek taşıyıcıları budur)
       · dört zeminde (bg·bg2·card·card-2) kontrast ≥ 3
     ÖLÇÜLDÜ (gündüz): hue 154→209→245 (dengeli adım 55°/36°) · L* 23,7→42,2→57,9 ·
     ΔL* 18,5/15,7 · ΔE2000-min 23,8 · kroma 0,083→0,159 (eski tavan 0,125 — kazanılan canlılık). */
```

### Blok 12

```css
  /* r3 (TSK-117 G1 r3, 2026-09-04): hex TSK-117 G7'nin seri-6/8/9'una ÇEKİLDİ (tokens.json
     ile eş-kayıt, ölçüldü — index.html hâlâ eski #2563eb/#7c3aed/#16a34a taşıyordu).
     YUKARIDAKİ hue/L*/ΔE ölçümü ESKİ paletin kaydıdır, TARİHÎ kalır — yeniden ölçülmedi. */
```

### Blok 13

```css
  /* SAKİNLİK YÜZEYİ — Dub'ın KENDİ `surface.tinted-accent` jetonu (soft-mint), AYNEN.
     Bir DURUM rengi değil bir ZEMİN tintidir ve şiddet kanalıyla ilgisi yoktur (karar §10.5).
     Metin taşımaz ama ÜSTÜNE metin düşer, o yüzden yine ölçüldü: --tx 18.03 · --tx2 7.11
     (ikisi de AA). --tx3 4.32 ile AA ALTIDIR ve bu yüzden mint yüzeylerde --tx3 OKUYUCUSU YOK.
     Kart ile farkı 1.098 — bir fısıltı, bir duyuru değil. */
```

### Blok 14

```css
  /* ==========================================================================
     ROL KATMANI — D1 (2026-08-07), ALTI ROL (ROL 6 · 2026-08-24'te eklendi).
     --------------------------------------------------------------------------
     İKİ KATMANLI JETON SİSTEMİ. Yukarıdakiler DEĞER jetonlarıdır (yeşil / kehribar /
     kırmızı: bir HUE'nun adı). Aşağıdakiler ROL jetonlarıdır (bir İŞİN adı). BİLEŞEN
     KURALLARI YALNIZ ROL JETONU OKUR. Bir kuralın içinde değer jetonu görmek, o kuralın
     hangi rolü taşıdığını SÖYLEMEDİĞİ anlamına gelir — ve ölçülen çürüme tam buradan
     geldi: 2026-08-06 denetiminde yeşil ≥4, kehribar ≥5, kırmızı ≥5 ayrı rol taşıyordu
     (docs/BASELINE-2026-08-06.md §C). Hue adıyla bağlanan bir kural, ikinci bir anlamı
     ödünç almayı ÜCRETSİZ kılar.
     (Bu blokta jeton adları BİLEREK `--` öneksiz anılıyor: 2026-08-24'te bir toplu
      düzenleme yorumdaki adları BİLDİRİM sanıp bloğu bozdu.)

     ROL 1 · YAPI — akromatik. Kendi jetonu yok, çünkü kendi kanalı zaten var:
       zemin/kart/mürekkep/çizgi. KURAL: yapı hue TAŞIMAZ. Bir etiket, bir kimlik
       dizesi ya da bir sayaç kromatik boyanıyorsa o bir sızıntıdır.
       İSTİSNA (2026-08-24): GEZİNME/SEÇİM artık ROL 6'dır ve mavidir. Yapının
       geri kalanı (etiket, kimlik, sayı) akromatik KALIR.

     ROL 2 · ŞİDDET — sev-1/2/3. YALNIZ alarm ve risk seviyesi.
       sev-1 = P1, şimdi müdahale (durduruldu, kopuk, ret, yıkıcı kontrol)
       sev-2 = P2, insan gerekiyor (bayat, aşım, REVIEW, silahlı)
       sev-3 = P3, nominal (sakin, geçti, bağlı)
       Kroma en yüksek burada. Başka HİÇBİR anlam bu kanalı kullanamaz.
       ÜÇ SEVİYE BİRBİRİNDEN AYRILABİLİR OLMAK ZORUNDA ve bu artık ÖLÇÜLÜYOR (ÖE1,
       karar §9.3): komşu seviyeler arasında luminans oranı ≥1,20 ve ΔE2000 ≥15,
       iki temada. Çivisi tests/test_renk_rolleri_v197.py §10'da.
       TAŞIYICI (2026-08-24, karar §10.2): şiddet rengi METİN DEĞİL İŞARETtir — nokta,
       sol şerit, kenar ya da kalın alt çizgi. Çipin/satırın YAZISI nötr mürekkeptir.
       Ölçüt buna göre BÖLÜNDÜ, GEVŞEMEDİ: işaret metin-dışı 3:1 · yazı ÖE1-c'nin
       kendi 4,5'i (ve nötr olduğu için fiilen 9-17 veriyor).
       TEK İSTİSNA ADIYLA YAZILIR: `aria-hidden` glifler (`.sev-N[aria-hidden]`) ve
       18px'lik ikon kutusu (`.ck.ok`/`.ck.man`) — ikisi de zaten metin değildir.

     ROL 3 · YÖN — yon-arti/yon-eksi. K/Z İŞARETİ, başka bir şey değil.
       ÜÇÜNCÜ SİNYAL: işaret (+/−) ve ok önce gelir, hue yalnız pekiştirir.
       KROMA ŞİDDETİN ALTINDA, ve bu ölçülmüş bir kısıttır (bkz. testler):
         gündüz  yön C≤0,0563  <  şiddet min C 0,1671 (sev-3)   [oran 0,34]
         gece    yön C≤0,0487  <  şiddet min C 0,1578 (sev-1)   [oran 0,31]
       Gerekçe: kârlı bir gün, bir risk ihlaliyle dikkat için YARIŞAMAZ.
       KURAL "≤" OLARAK OKUNUR, "=" OLARAK DEĞİL — ve bu bir gevşeme değil, ölçümün
       yönüdür: ÖE1 taşıyıcı turu (2026-08-24) şiddet kromasını yükseltti, yön ise
       DOKUNULMADAN kaldı, yani oran 0,60'tan 0,31-0,34'e DÜŞTÜ. Yön artık şiddetin
       daha da altında. Yönü de yükseltmek ayrı bir karardır ve bu turda alınmadı.

     ROL 4 · MOD — mod-kagit/mod-canli/mod-kesif. AYRILMIŞ KANAL.
       Hue 310° (mor-macenta) bandı bu kanala kalıcı olarak ayrıldı ve BAŞKA HİÇBİR
       ŞEY kullanamaz. Dub'ın kendi 293° bandı (`lavender #7c3aed`) bu kanala girer;
       şiddet hue'ları (OKLCh 21° / 40° / 149°), gezinme (263°) ve SERİ merdiveni (230°)
       bu bandın DIŞINDA — ve üçü de ölçülüyor.
       KÂĞIT AKROMATİKTİR: beklenen, güvenli durum kroma harcamaz.

     ROL 5 · VERİ ÖLÇEKLERİ — tek-hue sequential (--kap-*) + CVD-güvenli
       diverging (--dv-*) + SERİ MERDİVENİ (--blue/--violet/--violet2, OKLCh 230°,
       tek hue üç açıklık) + veri güveni (--olcek-guven, akromatik).
       SERİ RENKLENDİ AMA CVD KANALI KALKMADI (karar §10.3): ayrım hâlâ luminans
       (ΔL* ≥15) + kesik-çizgi desenidir; hue onların ÜSTÜNE eklendi.
       ATAMA KURALI (§10.4): aynı büyüklüğü ölçen seriler TEK hue farklı açıklık alır
       (`Sermaye` ↔ `Tepe` böyledir — Tepe Sermaye'den türetilir, merdiven o ilişkiyi
       kodlar); farklı büyüklükler ayrı hue ister ama Dub'ın kalan hue bütçesi BİRDİR
       ve dördüncü bir hue UYDURULMADI (`.pv-nk.s4` nötr kaldı, beyanlı).
       Bir seri çizgisi bir alarmla yarışamaz: max C(seri) < min C(şiddet) (×0,75).

     ROL 6 · GEZİNME/SEÇİM — --nav/--nav-2/--nav-t/--nav-h/--nav-bg. YENİ (2026-08-24).
       Dub'ın dili gezinmeyi maviyle taşır (aktif menü dolgusu, sayaç hapları,
       bağlantılar) ve operatör kararı bu dili bağlayıcı kıldı. Çözüm rolü KIRMAK
       değil, ALTINCI olarak açmak: mavi YALNIZ gezinme/seçim/sayaç taşır; bir para
       değeri, bir alarm, bir yön ASLA mavi olmaz.
       İKİ EŞİK TUTMADI VE DEĞER ZORLANMADI (karar §2.1: kullanım yüzeyi daralır):
         Ö3 — C(--nav)=0,2152 > min C(şiddet)=0,0921. Mürekkep tavanı TUTMADI.
              Daraltma: gezinmenin BÜYÜK YÜZEYİ washtır (--nav-t, C=0,0328 gündüz ·
              0,0720 gece) ve tavanın altındadır; --nav/--nav-2 yalnız İNCE mürekkep
              taşır (3px seçim çubuğu, sayaç hapı dolgusu). Gece washı bu tavana
              UYMAK İÇİN yeniden türetildi (ÖE1 merdiveni şiddet kromasının tabanını
              düşürünce maketin #172554'ü tavanın üstünde kaldı; hue ve L korunup
              kroma tavanın %90'ına indirildi → #1a274d).
         Ö5 — --nav, --nav-t üstünde 4.24 (AA ALTI). Daraltma karar §2.1'in kendi
              cümlesidir ("dolgu washı kalır, mürekkep koyulaşır"): wash üstündeki
              mürekkep --nav-2'dir ve ölçüldü 7.15 (AA). `.sitem.on` bu yüzden
              `color:var(--nav-2)` okur, `var(--nav)` DEĞİL.
     ========================================================================== */
```

### Blok 15

```css
  /* ROL 2 · ŞİDDET — değer katmanından devralınır; ölçümleri yukarıda ve §12'de. */
```

### Blok 16

```css
  /* ROL 3 · YÖN — ÖLÇÜLDÜ (research/olcumler/dub_donusumu_2026-08-24/):
     --yon-arti #4a6e56 C 0,0563 · --yon-eksi #6c4442 C 0,0559 — ikisi de kendi
     %10 tinti üstünde ve çıplak yüzeyde AA (en kötü gerçek zemin #f5f5f5).
     Hue'lar artık şiddet üçlüsününkilerdir (Omega ailesi, ÖE1 hükmü) ve kroma yine
     min C(şiddet) × 0,60'tır — kural DEĞİŞMEDİ, girdi değişti. */
```

### Blok 17

```css
    /* YÖN JETONLARI DUB'A GEÇTİ (2026-08-24, operatör kararı). ~~#4a6e56 / #6c4442~~ —
     bunlar kroması ×0,60 SOLUKLAŞTIRILMIŞ tonlardı ve gerekçeleri "kâr/zarar işareti bir
     alarmla dikkat için YARIŞAMAZ" kuralıydı. Operatör o gerekçeyi adıyla reddetti
     ("renk körü değilim, birşeyi de renkten dolayı karıştırmam") ve Dub renklerini istedi.
     Değerler maketten BİREBİR: vivid-green #16a34a · loss-red #c2410c (gece #4ade80 / #f87171).
     ROL DEĞİŞMEDİ — hâlâ YÖN kanalı; değişen yalnız doygunluk. */
```

### Blok 18

```css
/* yeşil Dub'ın #16a34a'sının BİR ADIM KOYUSU: aynı HSL hue (142,1°), aynı
     doygunluk (%76), OKLCh farkı 0,2°. Gerekçe OKUNABİLİRLİK, karışma değil —
     ölçüldü: yön rengini kullanan 17 öğenin HEPSİ WCAG büyük-metin eşiğinin
     altında (en küçüğü 11px) ve Dub'ın tam yeşili beyazda 3,02 veriyor; bunlar
     PARA rakamları. #117e39 min 4,74 ile AA'yı geçiyor. Kırmızı (#c2410c) zaten
     4,75 ile geçtiği için maketten BİREBİR alındı. */
```

### Blok 19

```css
  /* Matris hücre zemini: yönün ıraksayan ölçeği. Alfa .08/.07 KORUNDU (ölçülmüş sınır). */
```

### Blok 20

```css
  /* ROL 4 · MOD — ayrılmış hue bandı. Dub `lavender` AYNEN alındı (0 adım: kendi %10
     tinti üstünde zaten AA — 4.52). --mod-kesif aynı hue, kroması ×0,40 ve AA'ya kadar
     indirilmiş: C 0,0996. ÖLÇÜLDÜ (çıplak #f5f5f5): canlı 5.23 · keşif 5.16;
     kendi %10 tinti üstünde 4.52 / 4.54 — ikisi de AA. */
```

### Blok 21

```css
  /* ROL 5 · VERİ GÜVENİ — akromatik; ayrım ikinci kanaldan (kesik çizgi) gelir.
     HALKA KENDİ ALFASINI ALIR (.45), --ink-h'yi (.30) DEĞİL: bu kenar bir SÜS değil,
     "bu hücrenin örneklemi ince" bilgisinin taşıyıcısı — WCAG 2.2 1.4.11 metin-dışı 3:1
     tam olarak bunu ister. */
```

### Blok 22

```css
  /* ROL 6 · GEZİNME/SEÇİM (2026-08-24). Dub jetonları AYNEN: electric-blue /
     deep-sapphire / blue-wash. Ölçüldü: --nav çıplak zeminde 4.95 (bg) · 5.17 (card);
     --nav-2 washın üstünde 7.15 (AA); --nav washın üstünde 4.24 (AA ALTI → yukarıdaki
     daraltma). --nav-h yalnız SAÇ TELİdir (1.59, beyanlı sapma — dolgu tanıtıcıdır). */
```

### Blok 23

```css
  /* ÜST BAR PERDESİ de ROL 6'dır (gezinme yüzeyi) ve TEMAYLA DÖNER. Beyaz kalsaydı
     HALT/KRİZ kırmızısı üstünde kaybolurdu — Omega geçişinde yaşanan 1.27:1 arızasının
     aynadaki hâli. Ölçüldü: kırmızı bar üstünde gündüz 8.00. */
```

### Blok 24

```css
  /* NİTEL BANT MERDİVENİNİN ORTA BASAMAĞI (P3/B1 hükmü korunur). Dub `silver`;
     merdiven card-2 → band-2 → tx2 ve adımlar 2.42 / 3.10 (gündüz). Tek hue, soğuk
     nötr; temayla döner. ~~Eski değer #979491, adımlar 2.46 / 2.49.~~ */
```

### Blok 25

```css
  /* P9 · KAPSAMA ISI-MATRİSİ — TEK HUE SEQUENTIAL (koyu-uyumlu). Hue MÜREKKEBİN
     kendisidir: jeton temayla döndüğü için iki temada da "daha çok = daha yoğun" okunur.
     Tavan alfa .30'da SABİT ve bu ölçülmüş bir sınırdır: hücrenin rakamı (--tx) gece
     temasında en koyu bandın üstünde 5.07 verir. Bantlar arası adım ısı skalasıdır;
     hüküm hücrenin RAKAMINDAN gelir, dolgu tarama yardımıdır. */
```

### Blok 26

```css
  /* P9 · SAPMA (drift) — CVD-GÜVENLİ DIVERGING. Kutuplar MAVİ ↔ TOPRAK: renk körlüğünün
     baskın iki biçimi (protan/deutan) kırmızı-yeşil eksenini siler, mavi-sarı eksenini
     KORUR. Kutup mürekkebi --tx2'nin OKLCh-L'sinde durur (iki kutup AYNI L'de; işaret
     hücrenin RAKAMINDA yazılıdır, luminansta değil) ve kroması min C(şiddet)×0,55 —
     "sapma bir para hükmü DEĞİLDİR" kuralının sayısal karşılığı. Hue'lar Dub'ın kendi
     deep-sapphire ve tangerine hue'ları. Alfa merdiveni .22/.10 DEĞİŞMEDİ.
     Ö4 ÖLÇÜLDÜ: --nav ile karta binmiş --dv-n2 arasında 3.66 (gündüz) — ayırt edilebilir,
     yani ıraksayan kutbun mor-toprağa taşınmasına GEREK KALMADI. */
```

### Blok 27

```css
  /* SAÇ TELLERİ VE PERDELER JETONDUR (2026-08-01): renk taşıyan hiçbir değer kuralın
     içinde YAZILMAZ, jetondan gelir. Aksi hâlde ikinci tema sessizce kırılır. */
```

### Blok 28

```css
  /* PERDE İKİ TEMADA DA KOYU TABANLIDIR: perde bir mürekkep değil bir ENGELdir. */
```

### Blok 29

```css
  /* YARIÇAP — Dub ölçeği devralındı (karar §3). --r-ctl KALIR ama 8px olur: app.js onu
     okuyor (isim sözleşmesi bağlayıcı) ve Dub'ın düğme yarıçapıyla aynı basamağa oturur.
     ~~Eski --r-ctl:10px, Omega ölçümü.~~ --r-bar:2px grafik çubukları için değişmedi. */
```

### Blok 30

```css
  /* --r-pill KALDIRILDI (2026-07-27): tanımlıydı ama HİÇBİR kural onu kullanmıyordu.
     2026-08-24: hap geometrisi geri geldi ama ADI --r-tag ve OKUYUCUSU var (.pillc). */
```

### Blok 31

```css
  /* KARTLARDA GÖLGE YOK — Dub da kenar-öncedir, ayrım 1px `ash` saç teliyle kurulur.
     --elev:none KALIR. Dub'ın İKİ gölgesi alındı ve ikisi de KART DIŞI:
       --sh-btn  = OKLÜZYON (düğme). Işığın kesilmesidir, mürekkep değil — iki temada da
                   koyu kalır (precedent: --scrim gece de koyudur). Dub `shadow-subtle`.
       --sh-ring = MÜREKKEP HALKASI. Alfa Dub'ın (.10) KORUNUR, taban renk temayla DÖNER
                   (precedent: --ink-h / --kap-* / --olcek-guven-h).
     Ö7 TUTMADI VE DEĞER ZORLANMADI: --sh-ring her zeminde 1.23-1.31, yani 3:1'in ALTINDA.
     Daraltma: --sh-ring bir ODAK GÖSTERGESİ DEĞİLDİR, onu ÇEVRELEYEN yardımcı halkadır.
     G4'ü taşıyan gösterge `:focus-visible` üzerindeki 2px --accent ANA HATTIdır ve o
     ölçüldü: 10.78-19.80 (iki tema, yedi gerçek zemin) — GEÇTİ. */
```

### Blok 32

```css
  /* Omega imza etiketi: mono, 10px, BÜYÜK HARF, 0.16em — sayının üstünde duran mikro başlık */
```

### Blok 33

```css
    /* ETİKET JETONLARI DUB'A HİZALANDI (2026-08-24, operatör: "eski tasarım dili … bunlarla
     sınırlı değil"). Tek tek kural kovalamak yerine JETONUN KENDİSİ değişti — bir satır,
     yirmi kullanım. İkisi de emekli Omega'nın imzasıydı:
       --label-track  .16em → .04em   (maketin `.kart > h2` ve `.dbaslik` değeri; .16em dört katıydı
                                       ve "seyreltilmiş büyük harf" sesi eski dilin en görünür yeriydi)
       --label-size   10px  → 11px    (10px RAMPADA YOK; 11px `--t-cap`in ta kendisi. Mikro etiketler
                                       böylece ölçeğe oturdu — 23 kullanım tek satırdan düzeldi) */
```

### Blok 34

```css
  /* ==========================================================================
     TİP RAMPASI JETONLARI (2026-08-24) — İKİ KAYNAK KAPANDI.
     --------------------------------------------------------------------------
     Bu tura kadar rampanın TEK jetonu `--t-num` idi; geri kalan her boy kural
     gövdesinde sabit px olarak duruyordu. Yani rampa hakkında iki şey konuşuyordu
     ve ikisi ayrışabilirdi — v209'un savunduğu tam olarak bu.

     HANGİ BASAMAKLAR JETON? Ö6'nın ölçtüğü HİYERARŞİ rampası: 11 / 14 / 17 / 20 /
     24 / 30. Karar §3 bunu 11/14/16/20/24/30 diye beyan etmişti ve ÖLÇÜM O RAMPAYI
     DÜŞÜRDÜ: 16/14 = 1.1429, eşiğin (1.15) altında. Değer zorlanmadı; iki daraltma
     adayı ölçüldü ve az-kayıplı olan seçildi:
       aday A · 16 → 17 : [11,14,17,20,24,30] adımlar 1.2727/1.2143/1.1765/1.2/1.25 — TUTTU
       aday B · 16 düşer: [11,14,20,24,30]    adımlar 1.2727/1.4286/1.2/1.25       — TUTTU
     A seçildi çünkü 17px kaynakta ZATEN ÜÇ yerde vardı (`.hyp h3`, `.md h4`, dar
     ekran `.logo`) ve B onları komşu basamağa iterek `.md h3` ile `.md h4`'ü aynı
     ölçüye çökertirdi — bir hiyerarşi basamağını KORUMAK için ölçülmüş bir gerekçe.
     16px ve 18px ise yalnız clamp() SINIRLARINDA geçiyordu ve rampaya çekildi.

     10px VE 12px BİLEREK JETONSUZ. Onlar hiyerarşi rampasının basamağı DEĞİL, mikro
     etiket/yoğun meta bandıdır (10px'in zaten kendi jetonu var: `--label-size`).
     v209'un YÜZEY rampası (izinli tüm boylar: 10/11/12/14/17/20/24/28/30) ile bu
     hiyerarşi rampası AYRI şeylerdir ve karıştırılmamalıdır: biri "hangi ölçü yasal",
     öteki "hiyerarşi hangi basamaklardan okunuyor" sorusunu cevaplar.
     ÖLÇÜLDÜ (2026-08-24, index.html kural gövdeleri): 12px × 29 · 10px × 21.
     ========================================================================== */
```

### Blok 35

```css
  /* BÜYÜK METRİK RAKAMI — Dub Analytics'in 30px basamağı (karar §3). Rampanın en üst
     basamağı ve ilk okuyucusu `.mcard .v`. ~~Eski değer 28px, jetonsuz sabit.~~ */
```

### Blok 36

```css
  /* ALAN KENARI — WCAG 2.2 1.4.11 (metin dışı 3:1). Saç telleri bilerek 1.2-1.4 arasında
     (beyanlı sapma: kart ve çip DOLGUSUYLA tanınır, kenarıyla değil). Ama METİN GİRİŞİ öyle
     değil: kutunun nerede başladığını gösteren TEK şey kenarıdır. Bu yüzden form
     kontrolleri --line-2'yi DEĞİL bu jetonu kullanır. Değer TÜRETİLMEDİ, Dub'ın nötr
     rampasından SEÇİLDİ: her gerçek yüzeyde ≥3:1 tutan İLK basamak = `fog #737373`
     (ölçüldü: 4.54 en kötü gündüz zemininde). ~~Eski değer #86817d, 3.14.~~ */
```

### Blok 37

```css
  /* ANLAM JETONLARI (TSK-117 G1 r3, 2026-09-04): eski pano eş-kayıt kopyası, kaynak tokens.json */
```

### Blok 38

```css
/* ============================================================================
   GECE ZEMİNİ (2026-08-01) — GEREKÇE YÜRÜRLÜKTE, DEĞERLER EMEKLİ (2026-08-24)
   ----------------------------------------------------------------------------
   BU BLOK TARİHTİR VE SİLİNMEZ. Aşağıdaki İLKELER (aynı masa/ikinci ışık ·
   polarite dürüstlüğü · saf siyah-beyaz yasağı · tint-yönü kuralı) Dub
   dönüşümünden SONRA da yürürlüktedir. Metinde geçen DEĞERLER (#1c1a18,
   #d4d0cb, #f2555a, 0.9523 katsayısı, "sıcak ton") ise sıcak-kemik dünyaya
   aitti ve KARAR-2026-08-24-B ile emekli edildi; yürürlükteki gece rampası
   hemen aşağıdaki `:root[data-theme="gece"]` bloğunda ve ölçümü
   research/olcumler/dub_donusumu_2026-08-24/ + docs/kontrast-denetimi.md §12'de.
   ----------------------------------------------------------------------------
   AYNI MASA, İKİNCİ IŞIK. Değişen YALNIZ renktir: geometri, tipografi, boşluk
   ve yarıçap iki temada birebir aynıdır. Sebep Bloomberg dersidir — operatörün
   kas hafızası düzeni tanır, ışığı değil. Bir jetonun burada bir KONUM ya da
   ÖLÇÜ değeri varsa, o bir hatadır.

   NİYE VAR: 24/7 düşük-ışık ergonomisi. "Daha iyi okunur" DEĞİL — kanıt tersini
   söylüyor (Piepenbrock 2013/14 pozitif polarite lehine; en çok alıntılanan
   halation kaynağı hakemli değil). Gündüz varsayılan kalır.
   Bkz. DESIGN.md § The Polarity-Honesty Rule.

   SAF SİYAH VE SAF BEYAZ YASAK. #000 üzerinde açık metin halation üretir ve
   yetişkinlerin ~%40-47'sinde bir miktar astigmatizm var. Zemin #1c1a18,
   mürekkep #d4d0cb — sıcak tonu koruyor, yani iki tema aynı ürün.

   WP-P/P6 DENETİMİ (2026-08-01) — VE KAPANIŞI (2026-08-02).
   Denetim üç yüzeyi (index.html · app.js · theme.js) `#000/#fff/black/white` için
   taradı. BULGU: gece temasında SIFIR saf değer — zemin #1c1a18, mürekkep #d4d0cb,
   perde rgba(10,9,8,.66); app.js ve theme.js hiç renk DEĞERİ taşımıyor (jeton
   sözleşmesi tutuyor). Yani halation argümanının hedeflediği yüzey TEMİZ.
   AÇIK KALAN İDİ: gündüz temasında `--bg:#ffffff` ve `--raise:#ffffff` saf beyaz.
   O turda değiştirilmedi çünkü tek başına indirmek merdiveni çökertirdi ve
   "merdiveni korumak için DÖRT yüzey jetonunun birden yeniden değerlenmesi
   gerekir" diye yazıldı. WP-P/P9 turunda (2026-08-02) tam olarak o yapıldı:
   DOKUZ yüzey jetonu tek katsayıyla (0.9523) birlikte indi, adım oranları
   korundu, --bg sıcak kırık-beyaza (#fbf9f8) oturdu ve 148 çiftin tamamı
   yeniden ölçüldü (docs/kontrast-denetimi.md §11). Gündüz temasında artık SIFIR
   saf beyaz var. Dava, doğru adıyla PARLAMA idi ve ölçüldü: sayfanın en büyük
   yüzeyi %5 luminans indi; daha derinine gitmek para renklerini de yeniden
   değerlemeyi gerektiriyor (kırmızının payı 0.09'a inmiş durumda) ve o kendi
   turudur.

   DEĞERLER TERS ÇEVİRİLEREK ÜRETİLMEDİ, ÖLÇÜLEREK ÜRETİLDİ. Eski koyu dünyanın
   kırmızısı #f2555a burada kendi %10 tinti üzerinde 4.12 (--card) ve 3.72
   (--card-2) ölçtü — AA ALTI. Sebep: tint zemini KENDİ mürekkebine doğru taşır;
   açık zeminde bu mürekkebe yardım eder, koyu zeminde ZARAR verir. Bu yüzden
   gece para renkleri naif bir ters çevirmenin vereceğinden AÇIKTIR.
   Bkz. DESIGN.md § The Tint-Direction Rule.
   ============================================================================ */
```

### Blok 39

```css
  /* GECE PALETİ TÜRETİLDİ VE ÖYLE DAMGALANDI (karar §1.2). Dub'ın verdiği DÖRT dosyada
     (DESIGN.md · theme.css · variables.css · tokens.json) karanlık tema YOKTUR — arandı
     ve bulunmadı; tarama olc.py `dub_karanlik_tema_var_mi()` içinde yeniden koşar ve
     sonucu RAPOR.md §0'da durur. G6 iki tam palet ister, o yüzden gece TÜRETİLİR.

     TÜRETME TERS ÇEVİRME DEĞİLDİR. Kroma taşıyan HER jeton kendi %10 tinti üzerinde
     AYRI ölçüldü; gece para renkleri naif tersin vereceğinden AÇIKTIR (tint-yönü kuralı).

     YÜZEY RAMPASI 8/255 IZGARASINA OTURUR ve Dub'ın charcoal (0x17) ile graphite (0x26)
     jetonları o ızgaraya ÇİVİ olarak girer; aradaki 15 birim tek 7'lik adımı üretir:
       0x17 (charcoal, Dub) → 0x1f (türetildi) → 0x26 (graphite, Dub) → 0x2e (türetildi).
     Yükselti ARTAN kurulur (mevcut Meridian gece yapısı, 2026-08-01'den beri): koyu
     zeminde "gömülü"yü daha da koyultmak saç telini yutar.
     `--raise` AYRI BİR BASAMAK DEĞİL: gündüz `--raise:#ffffff` = `--card:#ffffff`, yani
     "yükseltilmiş yüzey" Omega'nın kenar-önce kararında zaten kartın kendisidir; gecede de
     öyle kalır. ~~İlk taslakta #363636 türetilmişti ve gündüzde OLMAYAN bir basamak icat
     ediyordu; pano v2 bileşenleri `--raise`i kart zemini olarak okuyunca "en kötü gerçek
     zemin" gereksiz yere yukarı çıktı ve gece kehribarının kroması 0,1054'ten 0,0829'a
     düşüp Ö3'ün dolgu tavanını da düşürüyordu. Ölçüm bunu yakaladı.~~
     SAF SİYAH VE SAF BEYAZ YOK — en koyu yüzey #171717, en açık mürekkep #e5e5e5.

     ~~Emekli (2026-08-01 → 2026-08-24): bg #1c1a18 · bg2 #232120 · card #262320 ·
       card-2 #2f2b27 · raise #38342f · tx #d4d0cb · tx2 #b0a9a0 · tx3 #95928f ·
       yeşil #4cc38a (5.31) · kehribar #e0a82e (5.39) · kırmızı #f58b8f (5.01) ·
       band-2 #676665 · field #7e776e · yön-artı #8ab59c · yön-eksi #d1a0a0 ·
       mod-canlı #c598e7 · mod-keşif #b9a4ca. Sıcak gri dünyaya aitti.~~
     (Adlar BİLEREK `--` öneksiz: yorumdaki tarihsel kayıt bir bildirim sanılıp toplu
      düzenlemede üzerine yazılabiliyor — 2026-08-24'te bir kez yaşandı.) */
```

### Blok 40

```css
  /* ŞİDDET · GECE — aynı taşıyıcı değişimi (karar §10.2), merdivenin yönü çevrilmiş:
     koyu zeminde şiddet ARTTIKÇA mürekkep AÇILIR, yani sev-1 en açık, nominal (sev-3)
     zemine en yakın. Hue kapısı gündüzle AYNI ve geri ölçüldü (LAB): 145,44 / 49,50 /
     26,48 — hedeflerden sapma ≤1,0°. "Gece kırmızısı pembeye kayar" arızası bu kapıyla
     kapandı: #ff7e7c hâlâ 26,5°'de, kızıl bandın içinde.
     ÖLÇÜLDÜ (gece):
       ÖE1-a  1.270 / 1.251                                     (eşik ≥1,20)
       ÖE1-b  ΔE2000 19.05 / 63.99                              (eşik ≥15)
       İŞARET kart üstünde 6.15 / 4.84 / 3.87 · en kötü gerçek zemin (--card-2) 5.51 /
              4.34 / 3.47 · kendi %10 tinti üstünde 4.69 / 3.89 / 3.15 (eşik ≥3)
       ÖE1-c  ÇİP METNİ (--tx) kendi tinti üstünde 9.16 / 9.65 / 9.79 (eşik ≥4,5)
     KROMA KAZANCI (OKLCh): kehribar +%132 · kırmızı +%95 · yeşil +%49. ESKİ KIRPMA
     BEYANI DÜŞTÜ: sev-1'in kroması 0,0809'dan 0,1578'e çıktı, çünkü artık 4,5:1'lik bir
     metin tavanına değil 3:1'lik bir işaret tavanına çarpıyor.
     BUNUN BİR YAN ETKİSİ VAR VE BEYANLIDIR: gece min C(şiddet) 0,0809 → 0,1578 yükseldi,
     yani Ö3'ün DOLGU tavanı da yükseldi ve gezinme MÜREKKEBİ (--nav, C 0,1458) artık o
     tavanın ALTINDA — gecede Ö3 sapması KAPANDI. Gündüzde sürüyor (C 0,2152 > 0,1671).
     Çivisi: test_renk_rolleri_v197::test_ROL6_MUREKKEP_tavan_asimi_BEYANLI_ve_MUREKKEP_KALIYOR.
     ~~Emekli: yeşil #61b37f · kehribar #d8b072 · kırmızı #ffbab4 (renk METİNDİ).~~ */
```

### Blok 41

```css
  /* ROL 5 · SERİ MERDİVENİ · gece — aynı hue (OKLCh 230°), yönü çevrilmiş: koyu zeminde
     1. basamak en AÇIK olandır. ÖLÇÜLDÜ: ÇG1 ΔL* 15.60 / 15.61 (eşik ≥15) · ÇG2 kart
     üstünde 9.46 / 5.92 / 3.50, en kötü gerçek zemin 8.49 / 5.31 / 3.14 (eşik ≥3) ·
     max C(seri) 0.1179 < min C(şiddet) 0.1578 · nav ailesine ΔE ≥13.9 · MOD bandına ≥28.2.
     ~~Emekli: --violet #c2c2c2 (akromatik geometrik orta), --violet2/--blue #e5e5e5.~~ */
```

### Blok 42

```css
  /* Maketin gece paleti, BİREBİR. ~~#83d7ff·#40addb·#0083ad~~ ~~#bdd2ff·#7aa4ff·#2e70ff~~
     ÖLÇÜLDÜ (gece kart zemininde): blue 5.95 · lavender 5.56 · sapphire 4.11 · sky 6.9 —
     dördü de ÇG2 (≥3) üstünde; üçlünün ΔE-min'i 17.6. */
```

### Blok 43

```css
  /* Huni, gece. Aynı yolculuk ters yönde (koyu zeminde en belirgin olan en AÇIK basamaktır).
     ÖLÇÜLDÜ: hue 162→206→247 · L* 91,7→75,5→60,1 · ΔL* 16,2/15,4 · ΔE2000-min 24,8 ·
     kroma 0,122→0,171 (eski tavan 0,118). */
```

### Blok 44

```css
  /* r3 (TSK-117 G1 r3, 2026-09-04): hex TSK-117 G7'nin seri-6/8/9'una ÇEKİLDİ (tokens.json
     ile eş-kayıt, ölçüldü — index.html hâlâ eski #60a5fa/#a78bfa/#4ade80 taşıyordu).
     YUKARIDAKİ hue/L*/ΔE ölçümü ESKİ paletin kaydıdır, TARİHÎ kalır — yeniden ölçülmedi. */
```

### Blok 45

```css
  /* SAKİNLİK YÜZEYİ · gece — TÜRETİLDİ (Dub'da karanlık tema YOK, §1.2 damgası geçerli).
     Yöntem ters çevirme DEĞİL: soft-mint'in OKLCh hue'su (156,7°) korundu, L gece yüzey
     bandına indirildi (0,299) ve kroma 0,0498'de tutuldu — gece min C(şiddet) 0,1578'in
     görünür altında, çünkü bu bir zemindir, bir hüküm değil. ÖLÇÜLDÜ: --tx 10.63 ·
     --tx2 9.04 · --tx3 5.31 (üçü de AA) · karttan farkı 1.130. */
```

### Blok 46

```css
  /* Gece merdiveni card-2 → band-2 → tx2: adımlar 2.86 / 3.20. Dub `fog`. */
```

### Blok 47

```css
  /* Kapsama rampası gecede AÇILARAK ilerler — mürekkep açık olduğu için aynı alfa
     merdiveni "daha çok mürekkep = daha yoğun" okumasını korur. Tavan .30: --tx bu
     bandın üstünde 5.07. */
```

### Blok 48

```css
  /* Sapma kutupları gecede AÇILIR (koyu zeminde soluk-koyu bir dolgu hiç görünmezdi);
     hue ekseni (mavi ↔ toprak) korunur, kutup L'si yine --tx2'nin L'sidir ve doygunluk
     para renklerinin ALTINDA. Ö4 gecede 3.41 ölçtü — ayırt edilebilir. */
```

### Blok 49

```css
  /* PERDE: mekanizma gece zeminine TAŞINMIYOR ve bu ölçüldü. Gündüz perde sayfayı karta
     karşı 3.00 ayırıyor; gece zemin zaten koyu olduğu için tavan 1.28. Yani gece ayrımı
     luminansla değil, perdenin backdrop-blur'u ve modal kartın kendi saç teliyle kurulur.
     Alfa yine de yüksek tutulur (.66): elde edilebilir ayrımın tamamı alınsın diye.
     Taban midnight-ink, saf siyah DEĞİL. */
```

### Blok 50

```css
  /* Gölge: OKLÜZYON iki temada da koyu (--sh-btn, Dub jetonu AYNEN); MÜREKKEP HALKASI
     temayla döner (--sh-ring, alfa .10 korunur). Ö7 gecede 1.28-1.31 — 3:1 ALTI;
     odak göstergesi yine 2px --accent ana hattıdır (10.78-14.23). */
```

### Blok 51

```css
  /* ==========================================================================
     ROL KATMANI · GECE — AD KÜMESİ GÜNDÜZLE BİREBİR AYNIDIR.
     Bir zeminde tanımlı olup diğerinde olmayan bir rol jetonu BUG'dır ve testle
     çivilenmiştir (tests/test_renk_rolleri_v197.py::test_iki_zeminde_ad_kumesi_esit).
     Sebep ölçülmüş bir arıza sınıfı: eksik jeton ikinci temada sessizce miras
     alınır, yani kural çalışır ama YANLIŞ zeminin rengiyle çalışır.
     DEĞERLER TERS ÇEVİRİLEREK DEĞİL ÖLÇÜLEREK üretildi (Tint-Direction Rule).
     ========================================================================== */
```

### Blok 52

```css
  /* YÖN · gece — D1 (2026-08-24): Dub renkleri. ~~#8aaa93 C 0,0484 · #edc3be C 0,0487,
     kroma = şiddet-min × 0,60~~ — soluklaştırma kuralı operatör kararıyla düştü.
     ÖLÇÜLDÜ: --yon-arti #4ade80 C 0,1821 (en kötü gerçek zemin 6,32) · --yon-eksi #f98080
     C 0,1482 (4,63). --yon-arti, --huni-3 ile BİLEREK aynı hex: aynı yeşil iki yerde iki
     türlü olamaz. Tavan artık şiddet değil ONAYLI PALET AZAMİSİ (0,1821) — çivi §5. */
```

### Blok 53

```css
  /* r3 (TSK-117 G1 r3, 2026-09-04): --yon-eksi TSK-117 G2'de #f98080'den #f6966f'e çekildi
     (gece kritik #ff7e7c ile 0° çakışıyordu) ama index.html'in eş-kaydı hiç güncellenmemişti
     (ölçüldü — v153::test_gece_blogu_BIRE_BIR). YUKARIDAKİ ÖLÇÜLDÜ satırı ESKİ hex'e (#f98080)
     aittir, TARİHÎ kalır. */
```

### Blok 54

```css
  /* MOD · gece — aynı ayrılmış hue bandı (lavender ailesi), gece mürekkep bandında.
     --mod-canli #ab91ff C 0,1570 · --mod-kesif #a79fcb C 0,0637. */
```

### Blok 55

```css
  /* ROL 6 · GEZİNME/SEÇİM · gece — TÜRETİLDİ. Wash, operatörün onayladığı maketin
     (scratch-panov2/index.html) gece bloğundan TOHUM olarak gelir (#172554) — ama tohum
     ölçülmeden alınmaz: kroması (0,0874) Ö3'ün DOLGU tavanının (min C(şiddet) gece =
     0,0809) ÜSTÜNDEYDİ, o yüzden hue ve L korunup kroma tavanın %90'ına indirildi
     (#1a274d, C 0,0720). Mürekkepler o washın üstünde AA'yı geçene kadar AÇILARAK
     türetildi. VURGU YÖNÜ ÇEVRİLİR: gündüz --nav-2
     --nav'dan KOYUdur (açık zeminde vurgu koyularak artar), gecede aynı L farkı
     (0,1217) büyüklüğüyle korunur ama yönü çevrilir — koyu zeminde vurgu AÇILARAK artar.
     Naif ters çevirme ikisini AYNI renge çökertiyordu (#82adff ↔ #87acff, 1.00:1).
     ÖLÇÜLDÜ: --nav washın üstünde 5.78 · --nav-2 8.87 (ikisi de AA, gecede Ö5 TUTAR). */
```

### Blok 56

```css
  /* ANLAM JETONLARI (TSK-117 G1 r3, 2026-09-04): eski pano eş-kayıt kopyası, kaynak tokens.json */
```
