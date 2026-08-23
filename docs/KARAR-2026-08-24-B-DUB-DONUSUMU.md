# KARAR-2026-08-24-B · PANO DUB DÖNÜŞÜMÜ (bağlayıcı)

_Operatör talimatı (2026-08-24): "tamam beğendim, önerilerin ile birlikte gerçeğe alalım" +
"bütün bileşenler için bu tasarım dillerini kullanabilirsin, birleştirilmesi gereken yerleri
birleştirip, sadeleştirmen gereken yerleri sadeleştirebilirsin, bütün hisseler için canlı
grafikler de olsun, karar verilen adaylar için üzerine tıklandığında neler olduğunu gösteren
bir kart açılsın"._

Onaylanan maket: `scratch-panov2/index.html` (Design projesi `86d04f07…`, "Meridian Pano —
Design System"). Bu belge o maketin ÜRETİME nasıl indiği ve hangi ölçülmüş kısıtın
neden kımıldamadığıdır. Yön sözleşmesi: `docs/TASARIM-YONU-2026-08-24-PANO-V2.md`
(GARANTİ ↔ KARAR ayrımı). Analitik kavram ayıklaması: `docs/AYIKLAMA-DUB-ANALYTICS-2026-08-24.md`.

---

## 0 · NE DEĞİŞMEZ (GARANTİ — tasarım kararı değil, dürüstlük kısıtı)

Bunlar Dub'a rağmen kalır; maket bunları zaten karşılıyor:

| # | Garanti | Nerede sınanır |
|---|---|---|
| G1 | Ölçülmeyen alan **None + neden**; `?? 0` / `\|\| 0` çırçırı tavanı aşamaz | v196 |
| G2 | Koşulsuz emisyon tavanı = 0 (bir değer yoksa satır BASILMAZ) | v197 |
| G3 | Her renk çifti **kendi gerçek zemininde** ölçülür; para renkleri AA | v153 |
| G4 | Odak halkası her zeminde ≥3:1; metin-dışı taşıyıcı ≥3:1 | v153, v197 |
| G5 | `font-src 'self'` — dış köken YOK (yasak font değil, **kendi sunmak** şart) | test_web_csp_uyum |
| G6 | Her renk jetonu İKİ temada da tam; tokens.json ile BİREBİR | v153, v208 |
| G7 | Her `font-size` rampada; başlık merdiveni ölçülmüş ayrımı korur | v209 |
| G8 | Rol ayrılığı: bir kural iki rol taşımaz, bileşen ham hue okumaz | v197 |

**Geri kalan her şey KARAR'dır ve bu turda değişir** — aksan rengi, zemin, yarıçap,
tipografi, yerleşim, bileşen dağarcığı dâhil.

---

## 1 · PALET — Dub DEĞER katmanı devralınır

Omega'nın sıcak-kemik rampası (`#fbf9f8 / #f2efed / #e2deda`, sıcak gri) **emekli edilir**;
yerine Dub'ın soğuk nötr rampası gelir. Ad = Dub'ın kendi adı (uydurma ad yok):

```
canvas-white #ffffff · paper-mist #f5f5f5 · ash #e5e5e5 · smoke #d4d4d4 · pebble #c8c8c8
midnight-ink #0a0a0a · charcoal #171717 · graphite #262626 · slate #404040
steel #525252 · fog #737373 · silver #a3a3a3
electric-blue #2563eb · deep-sapphire #1e40af · soft-mint #dcfce7
vivid-green #16a34a · tangerine #ea580c · lavender #7c3aed
```

### 1.1 İki SAF UÇ — Dub'ın kendi jetonuyla çözülür (uydurma yok)

Dub `--canvas #ffffff` ve birincil eylem dolgusu `#000000` kullanır. Meridian'ın **ölçülmüş**
parlama kısıtı (WP-P/P9, 2026-08-02: "gündüz temasında artık SIFIR saf beyaz var") ve
halation kısıtı bu iki ucu reddeder. Çözüm **Dub'ın kendi rampasından** gelir:

- **Sayfa zemini** = `#fafafa` — Dub uygulamasının kendi zemini (kartlar beyaz, zemin gri).
  Sayfanın en büyük yüzeyi saf beyaz olmaz; kartlar `#ffffff` kalır (P9 ölçümü `--bg`
  hakkındaydı, kart hakkında değil). **Ölçülecek ve beyan edilecek** (§4/Ö1).
- **Birincil eylem dolgusu** = `--midnight-ink #0a0a0a`, `#000000` DEĞİL. Siyah hap üstünde
  beyaz metin tam olarak halation vakasıdır; `#0a0a0a` Dub'ın kendi jetonu ve ayrımı
  ölçülemez düzeyde.

**Bu iki sapma dışında Dub değerleri BİREBİR alınır.** Maketteki tek türetme (`--loss-red
#c2410c`) korunur ve beyanlı kalır: Dub bir pazarlama sitesidir, kayıp rengi taşımaz;
Meridian'ın para kuralı zorunlu kılar.

### 1.2 GECE — Dub'da YOK, türetilir ve öyle DAMGALANIR

Dub'ın verdiği dört dosyada (`DESIGN.md`, `theme.css`, `variables.css`, `tokens.json`)
karanlık tema **yoktur** — arandı, bulunmadı. G6 iki tam palet ister. Gece paleti bu yüzden
**türetilir** ve tokens.json'da `$extensions` altında `"kaynak":"türetilmiş — Dub'da yok"`
damgası taşır.

Türetme yöntemi ters çevirme DEĞİLDİR (Omega'nın 2026-08-01 dersi: "DEĞERLER TERS
ÇEVİRİLEREK ÜRETİLMEDİ, ÖLÇÜLEREK ÜRETİLDİ"). Kural:
- Zemin `charcoal #171717`, yükseltiler `graphite #262626` — ikisi de Dub jetonu, saf siyah yok.
- Mürekkepler rampadan yukarı okunur (`ash`/`smoke`/`silver`), saf beyaz yok.
- Kroma taşıyan her jeton (mavi, yeşil, turuncu, lavanta, kırmızı) **kendi %10 tinti
  üzerinde yeniden ölçülür**; gece değerleri gündüzün açık karşılığından FARKLI olacaktır
  (tint yönü kuralı — koyu zeminde tint mürekkebe zarar verir).

---

## 2 · ROLLER — beş rol durur, ALTINCI eklenir

Rol katmanı (D1, 2026-08-07) **iptal edilmez**; Dub renkleri rollere bağlanır:

| Rol | Eski | Yeni (Dub) |
|---|---|---|
| 1 · YAPI | akromatik sıcak gri | akromatik **soğuk** gri (canvas/paper/ash/ink rampası) |
| 2 · ŞİDDET | green/amber/red | `vivid-green` / `tangerine` / `loss-red` — hepsi kendi tinti üstünde YENİDEN ölçülür |
| 3 · YÖN | `#40654c` / `#784e4b` | Dub yeşil/kırmızısının **kroması düşürülmüş** hâli; kroma tavanı şiddetin ALTINDA kalır (ölçülür) |
| 4 · MOD | hue 310° mor-macenta | `lavender #7c3aed` — Dub'ın kendi 310° bandı; kâğıt akromatik kalır |
| 5 · VERİ ÖLÇEKLERİ | tek-hue sequential + CVD-güvenli diverging | aynı yapı, Dub mürekkebiyle |
| **6 · GEZİNME/SEÇİM** | **YOK** | **`electric-blue #2563eb` + `--blue-wash #dbeaff`** |

### 2.1 ROL 6 gerekçesi ve kısıtı

Omega "yapı hue TAŞIMAZ" diyordu ve aksanı siyaha çekmişti ("renk yalnız ölçüme aittir").
Dub'ın dili gezinmeyi maviyle taşır (aktif menü dolgusu `#dbeaff`, sayaç hapları, bağlantılar).
Operatör kararı bu dili bağlayıcı kıldı. Çözüm rolü **kırmak değil, altıncı olarak açmak**:

- Mavi YALNIZ gezinme/seçim/sayaç taşır. Bir para değeri, bir alarm, bir yön ASLA mavi olmaz.
- **Birincil eylem dolgusu mavi DEĞİL, `midnight-ink`** — Dub da öyle yapar; "renk yalnız
  ölçüme aittir" kuralının çekirdeği böylece korunur.
- **Kroma tavanı**: gezinme kroması, şiddetin görünür altında kalır — yön (ROL 3) için zaten
  var olan ölçülmüş kısıtın aynısı. Ölçülür ve beyan edilir (§4/Ö3). Elektrik mavisi doygundur;
  tavan tutmazsa **kullanım yüzeyi daralır** (dolgu `#dbeaff` wash kalır, mürekkep koyulaşır) —
  jeton uydurulmaz.
- **Çarpışma beyanı**: ıraksayan veri ölçeğinin negatif kutbu 250° mavidir
  (`--dv-n2 rgba(46,82,122,.22)`). Gezinme mavisiyle aynı bantta. Ayrım alfa/bağlamla değil,
  **kutbun toprak-mavi çiftinin yeniden değerlenmesiyle** çözülür (§4/Ö4). Ölçülemezse
  ıraksayan ölçek moru-toprağa taşınır.

---

## 3 · GEOMETRİ, TİPOGRAFİ, YÜKSELTİ

- **Yarıçap** — Dub ölçeği devralınır: `6px` giriş · `8px` düğme · `12px` kart · `16px` büyük ·
  `9999px` hap. (`--r-bar:2px` grafik çubukları için kalır.)
- **Boşluk** — 4px tabanı zaten aynı; değişmez.
- **Yükselti** — Omega `--elev:none` diyordu (kenar-önce). Dub da kenar-öncedir ama İKİ gölge
  kullanır: `--sh-btn rgba(0,0,0,.05) 0 1px 2px` ve odak halkası `rgba(0,0,0,.1) 0 0 0 4px`.
  İkisi alınır; kartlarda gölge YOK, ayrım 1px `ash` saç teliyle.
- **Tipografi rampası** — `11 / 14 / 16 / 20 / 24 / 30`. 30px YENİ basamaktır (Dub Analytics'in
  büyük metrik rakamı) ve v209 rampasına eklenir; 13px ve 15px ara basamakları KALKAR
  (ölçülen sorun: 14→15 oranı 1.07, hiyerarşi değil gürültü).
- **YÜZ (font) — AÇIK BORÇ, OPERATÖRE**: Dub `Inter` + `Geist Mono` kullanır. `font-src 'self'`
  bunların depoya indirilmesini şart koşar; **dosya indirmek benim yetkimde değil**. Bu tur
  mevcut kendi-sunulan `Recursive Sans/Mono` yüzüyle çıkar (değişken grotesk, tonu yakın).
  Tek satırlık operatör işi: `woff2` dosyalarını `meridian/web/fonts/` altına koymak —
  jeton adı (`--sans`/`--mono`) değişmediği için yüz o an takas olur, ikinci tur gerekmez.

---

## 4 · ÖLÇÜLECEKLER (hüküm ÖNCE ölçüm — sonuç bu belgeye işlenir)

| Ö | Soru | Eşik (şimdi donduruldu) |
|---|---|---|
| Ö1 | `#fafafa` zemin, P9'un parlama kısıtını karşılıyor mu? | en büyük yüzey luminansı saf beyazın altında; kart/zemin adımı ≥1.02 |
| Ö2 | Dub para renkleri (`vivid-green`/`tangerine`/`loss-red`) kendi %10 tinti üstünde | her biri ≥4.5 (AA), iki temada |
| Ö3 | Gezinme mavisinin kroması | C(mavi) < min C(şiddet), iki temada |
| Ö4 | Gezinme mavisi ↔ ıraksayan negatif kutup ayrımı | ayırt edilebilir; değilse kutup taşınır |
| Ö5 | `--blue-wash #dbeaff` üstünde mavi mürekkep | ≥4.5 |
| Ö6 | Tip rampası adımları | ardışık adım ≥1.15, en az bir adım ≥1.25 |
| Ö7 | Odak halkası (`--sh-ring`) her zeminde | ≥3:1 |

**Ölçülemeyen değer jetona GİRMEZ** (uydurma yasağı). Bir eşik tutmazsa çözüm §2.1'deki
gibi kullanım yüzeyini daraltmaktır, değeri zorlamak değil.

---

## 5 · BİLEŞEN PROGRAMI

### 5.1 Devralınan (makette onaylı)
Kenar çubuğu (gruplu + sayaç hapları) · "Seni bekleyenler" görev kartı · kontrol satırı ·
metrik sekmeleri (nokta + büyük rakam + bağlam satırı) · çok serili alan grafiği (kesik
ızgara, seyrek eksen, çip tooltip) · yatay karar zinciri · **aday huni şeridi (Sankey)** +
"nerede, neden elendi" tablosu · rozet grameri · `ölçülemedi` için kesik alt çizgi.

### 5.2 Yeni — operatör talebi (2026-08-24)
- **Y1 · Her hisse için canlı grafik.** Evrendeki her sembolde satır-içi kıvılcım grafiği
  (sparkline); aday/pozisyon satırlarında giriş, stop ve hedef işaretli. **G1 bağlayıcı:**
  barı olmayan sembol düz çizgi çizmez — `ölçülemedi` yazar.
- **Y2 · Karar verilen aday kartı.** Aday satırına tıklayınca çekmece açılır ve **ne olduğunu**
  gösterir: hangi kurulum, hangi kapılardan geçti/takıldı, hangi eşik, plan → onay → gönderim
  → doldu zinciri hangi adımda ve **neden orada durdu**. Kayıt yoksa uydurulmaz.
- **Y3 · Top Views** (ayıklama A1): kurulum · çıkış nedeni · **kapı reddi** kırılımları.
- **Y4 · Huni üstünde % etiketleri** (ayıklama B4) — karekök ölçek beyanıyla.

### 5.3 Sadeleştirme yetkisi
Operatör "birleştirilmesi gerekenleri birleştir, sadeleştirilmesi gerekenleri sadeleştir"
dedi. **Kapsam**: aynı sayıyı iki kez gösteren yüzeyler tek yüzeye iner; ölü/okuyucusuz
alanlar kalkar (YASA 6 zaten bunu istiyor). **Kapsam DIŞI**: bir sayının tek okuyucusunu
kaldırmak, bir şerhi/beyanı kısaltmak, `ölçülemedi` hâlini gizlemek. Kaldırılan her yüzey
tur özetinde ADIYLA listelenir (SİLME YOK ilkesi belgeye taşınır).

---

## 6 · SIRA

1. **Jeton katmanı** (bu belge §1-3) + ölçümler (§4) + `tokens.json` + v208/v209/v153 referansları
2. **Bugün yerleşimi** — maketin üretime inişi
3. **Y1/Y2** (canlı grafik + aday kartı), **Y3/Y4** (Top Views + %)
4. Tam suite (Rol-1, tek-otoriter) → `dagit.sh` → canlı doğrulama

