# D3 — shadcn/React PİLOTU: ÜÇ KAPI ÖLÇÜLDÜ

**Tarih:** 2026-08-24 · **Öneren:** operatör · **Pilot yüzeyi:** `workflow.html` (canlı veri bağı sıfır)

## Operatörün önerisi ve gerekçesi

> "mimariyi buna çevirmenin ne gibi avantajı olur, shadcnblocks altında bütün ihtiyaçlarımızı
> karşılayan bileşenler mevcut, bu şekilde tutarlılığı çok daha rahat sağlayabileceğiz gibi geliyor"

**Argüman doğru bir mekanizmaya dayanıyordu ve küçültülmedi.** Panonun bütün gün uğraştığımız
hastalığı tam buydu: tek bir kavram (`rozet`) için beş CSS reçetesi yan yana yaşıyordu ve
**altıncısının doğmasını hiçbir şey engellemiyordu**. Çivi bir ihlali TESPİT eder; bileşen sınırı
onu YAZILAMAZ kılar. İkisi aynı şey değil ve operatörünki daha güçlü olan.

İki taraf da tahmin olduğu için ölçüldü. Kapılar pilottan **önce** yazıldı (TDD, kırmızı başladı):
`tests/test_ui_pilot_kapilari_v286.py` — 22 iddia.

**Neden `runbook.html` değil:** ilk önerim oydu ve sözleşmesini okumadan önermiştim. Sayfanın kendi
yazılı kararı *"sıfır sayfa mantığı, JS kapalıyken de eksiksiz okunur"* ve gövdesini
`meridian/api.py::runbook()` **sunucuda** dolduruyor — React'e taşımak sayfanın kendi kararını
çiğnerdi. `workflow.html` seçildi: canlı veri bağı sıfır (para yolunda değil), ama tam
jeton/kontrast sistemini, kendi-barındırdığımız yazı tiplerini ve tema anahtarını kullanıyor.

---

## SONUÇ: 22 kapının 22'si GEÇTİ

### G1 — JETON / KONTRAST DENKLİĞİ ✅ **ve beklenenden iyi**

Rol jetonlarının 12'si (`--sev-*`, `--yon-*`, `--mod-*`, `--nav*`, `--huni-*`) pilota **birebir**
taşındı. Ama asıl kazanç eşlemede değil, eşlemenin **yönteminde**:

Pilot jetonları **elle kopyalamıyor** — `ops/jeton_css_uret.py` onları `tokens.json`'dan üretiyor.
Bugün dört yüzey (index/landing/workflow/runbook) aynı bloğu elle kopyalıyor ve bu kopya bu oturumda
tam üç kez ayrıştı: `--yon-*` tabanı değişti türevleri eski RGB'de kaldı; `hex`/`literal`/
`cozulen-deger` alanları birbirinden ayrıştı; kör bir `replace` `--huni-3`'ü de vurdu.

Üretecin kendisi bir **gizli belirsizlik yakaladı**: bazı jetonlarda `$extensions.tema` yok, tema
yoldan (`tema/gunduz` ↔ `tema/gece`) geliyor. Yalnız birine bakan ilk sürüm `--accent`i `:root`'ta
iki kez üretti ve ikincisi birincisini eziyordu — gündüz teması gece rengine düşüyordu. **CSS çift
bildirimi yutar, son yazan kazanır**; hiçbir şey haber vermezdi.

### G2 — DAĞITIM BÜTÜNLÜĞÜ ✅

* **Sızıntı kapatıldı.** `npm install` 6.326 dosya / 122 MB yazıyor ve `node_modules` ne
  `.gitignore`'daydı ne rsync dışlama listesinde — kurulum canlıya sızacaktı. Bu, on gün önceki
  `scratch-panov2` vakasının aynı sınıfı: **`.gitignore` rsync'i etkilemez**, iki mekanizma ayrı.
  `dagit.sh`e `node_modules`, `ui/node_modules`, `/ui` eklendi; artefakt (`meridian/web/pilot-*`)
  bilerek dışlanmadı — dışlansaydı sayfa canlıda 404 olurdu ve kimse görmezdi.
* **`[5c] ARTEFAKT TAZELİĞİ` kapısı eklendi.** Derleme adımı `[5b]`'nin varsayımını kırıyor:
  `[5b]` "dağıtılan dosya = kaynak" varsayar ve Python için bu doğru, ama artefakt kaynaktan
  ÜRETİLİR. Kaynak değişip build koşmazsa canlı sessizce bayat kalır ve `[5b]` bunu **göremez**.
  Yeni kapı hem artefakt mtime'ını hem jeton köprüsünün tazeliğini ölçüyor.
* **CSP temiz.** Üretilen sayfada satır içi `<script>` ve satır içi işleyici **sıfır**
  (`modulePreload.polyfill:false` gerekti — varsayılan Vite satır içi polyfill enjekte eder ve
  `script-src 'self'` onu bloklardı; bu arıza bu depoda daha önce iki kez yaşandı).
* **Dış origin sıfır.** Yazı tipi bildirimi dört yüzeyle birebir aynı, `/fonts/*.woff2` kendi
  baytlarımız — "ağ yokken de açılır" sözleşmesi korundu.
* **Bir tuzak kapatıldı:** Vite'ın `emptyOutDir` varsayılanı çıktı klasörünü **temizler** ve
  buradaki çıktı klasörü `meridian/web/` — varsayılan davranış `index.html`, `app.js`,
  `tokens.json` ve `fonts/` dahil **panonun tamamını silerdi**. `emptyOutDir:false` yazılı gerekçesiyle.

### G3 — EPİSTEMİK DEĞİŞMEZLER ✅ **ve bu kapıda bileşen açık ara kazandı**

Bu kapı en önemlisiydi: Meridian'ın çivileri görsel değil, *"paydanı beyan et"* ve *"ölçülemedi ile
sıfır aynı kutuya girmez"* diyor. shadcn bunlar hakkında hiçbir şey bilmez.

| Kural | Bugün (`app.js`) | Pilotta | Hüküm |
|---|---|---|---|
| Payda beyanı zorunlu | yorum + çivi | `payda: string` (opsiyonel DEĞİL) | **güçlendi** |
| ölçülemedi ≠ sıfır | `deger == null ? …` — `neden`i unutmak sessizce mümkün | **ayrık birleşim**: `{deger:null}` tek başına YAZILAMAZ, `neden` eksik olur | **güçlendi** |
| `oran:0` ≠ `oran:null` | yorum + çivi | tipte ayrı | eşit |
| Rozet sözlüğü | 103 çağrıda 42 serbest dizge | `ROZET` sabiti, anahtar tipi | **güçlendi** |
| Gürültü bandı | `signClass` | aynı saf fonksiyon | eşit |
| Kanıt log ölçeği | `kanitOrani` | aynı | eşit |

**En net kazanç:** bugün `neden`i unutup "veri yok" basmak ve okurun onu "sıfır" sanması
**mümkündü**. Pilotta bu kod **derlenmiyor**. Operatörün argümanının doğrulandığı yer burası.

---

## TAŞINAMAYANLAR — taşımanın gerçek bedeli

Bu bölüm olmadan karar verilemez.

**1. Sayfa ağırlığı 3,7 katına çıktı — ve pilot DAHA AZ içerik gösteriyor.**

| | ham | gzip |
|---|---|---|
| Mevcut `workflow.html` + `workflow.js` | 43.974 B | **18.592 B** |
| Pilot (html + js + css) | 218.087 B | **68.219 B** |

Üstelik mevcut sayfa tam bir mimari şemayı çiziyor, pilot dört hücre ve bir lejant. React+shadcn
**içerikten önce ~63 kB gzip JS** demek. SSH tüneli arkasından ve ağ yokken açılması gereken bir
pano için bu ölçülmüş bir bedeldir, teorik değil.

**2. 129 kaynak-metin çivisi aynı biçimde yazılamaz.** Dört tasarım dosyasındaki çivilerin çoğu
CSS kural metnini okuyor (`.pm-cell` kuralında `justify-content` var mı, çip yarıçapı `--r-tag` mi).
Tailwind biçimi kuraldan alıp işaretlemedeki utility sınıflarına taşır. Bunların bir kısmı
**gereksizleşir** (bileşen zaten zorluyor), bir kısmı **yeniden enstrümanlanmalı** (TSX üstünde,
farklı bir mekanizmayla — pilotta `test_G1b` bunu yapıyor ve çalışıyor). Ama "otomatik taşınır"
değil: her biri elden geçmeli ve bu iş sayılmadı.

**3. İki ekosistem, göç boyunca ikisi de bakılır.** Bugünkü teşhisin adı **yarım göç**ti ve bütün
gün onu kapattık. Panoyu React'e taşımak, mimari ölçekte aynı hastalığı açar: bir yüzey vanilla,
bir yüzey React, ikisi de bakım ister ve aralarındaki ayrışmayı hiçbir çivi görmez. Bu risk
**yönetilebilir ama sayılmalı** — göç bir turda bitmezse maliyet iki kat.

**4. `app.js` 12.653 satır / 401 HTML emisyonu.** Pilot dört hücre çizdi. Panonun tamamı bir
sunum katmanı yeniden yazımıdır ve o katman canlı para yüzeyidir; yeniden yazım boyunca
operatörün pozisyon/risk görüşü daha az güvenilir olur.

**5. Küçük ama gerçek friksiyon:** `theme.js` bir `<script src>` olarak duruyor ve Vite
"type=module olmadan bundle edilemez" uyarısı veriyor. Çalışıyor, ama dört yüzeyin paylaştığı
tema sözleşmesi ile bundler'ın dünya görüşü tam örtüşmüyor.

---

## HÜKÜM

**Üç kapı da geçti; operatörün argümanı mekanizma düzeyinde DOĞRULANDI** — özellikle G3'te,
bileşen sınırı bizim en güçlü çivimizden daha güçlü çıktı.

Ama "geçti" ile "hemen taşıyalım" aynı şey değil. Ölçülen bedel şu üç sayıda: **3,7× sayfa
ağırlığı**, **129 çivi yeniden enstrümanlama**, **göç boyunca iki ekosistem**.

**Önerilen sıra (operatör kararı):**

1. **Pilot canlıya çıksın, yan yana dursun** (`/pilot-workflow.html`). Mevcut sayfa yerinde kalır;
   operatör ikisini aynı ekranda görür ve karar ölçümle değil sadece sayıyla değil **gözle de** verilir.
2. **Jeton üreteci PANOYA da bağlansın — taşımadan bağımsız olarak.** `ops/jeton_css_uret.py`
   bugünkü dört-yüzey elle-kopyasını bitirebilir ve bunun React'le ilgisi yok. Bu turun en ucuz
   ve en yüksek kaldıraçlı kazancı.
3. Karar verilirse göç **yüzey yüzey** yapılsın ve her yüzeyde bu üç kapı yeniden koşsun; pano
   (`index.html`) **en son**, çünkü para yüzeyi orası.

**Bu belge bir hüküm değil bir ölçümdür.** Taşıyıp taşımamak operatörün kararı; bu belgenin işi
kararı tahmin üstünde değil sayı üstünde verdirmek.

---

## EK (aynı gün) — CLI ÇIKTISI OLDUĞU GİBİ KABUL EDİLEMEZ

Pilot ilk turda kabuğu ELLE çizmişti. Operatör bloğun kendisini görmek isteyince resmî
bileşenler CLI ile çekildi (`npx shadcn add sidebar breadcrumb separator badge`) — ve
**araç, kapattığımız hastalığı kendi eliyle geri getirdi.**

**İhlal 1 — REZERVE HUE BANDI ÇİĞNENDİ.** CLI kendi paletini stil dosyasına enjekte etti:

| jeton | hex | OKLCh hue | `--nav`'a ΔE2000 | rezerve nav bandı (255-272°) |
|---|---|---|---|---|
| `--sidebar-ring` | `#3b82f6` | **259,8°** | 10,9 | **İÇİNDE** |
| `--sidebar-primary` (gece) | `#1d4ed8` | **264,4°** | 7,1 | **İÇİNDE** |

Meridian'da hue bir üslup değil **güvenlik kaydıdır**: gezinme, mod çipi (kâğıt ↔ canlı para)
ve şiddet ayrı bantlarda durur. Araç bunu bilmez, bilemez ve sessizce çakışır.

**İhlal 2 — TEMA MEKANİZMASI ÇATALLANDI.** CLI `@custom-variant dark (&:is(.dark *))` yazdı.
Bu depoda `.dark` sınıfını **hiç kimse yazmıyor**: `theme.js` `data-theme` niteliğini kurar ve
bu dört yüzeyin ortak sözleşmesidir (D5, 2026-08-07). Düzeltilmeseydi shadcn bileşenlerinin
gece hâli **sessizce hiç ateşlenmezdi** — hata vermez, yalnız yanlış temada çizerdi.

**Düzeltme:** enjekte edilen palet silindi (kalan `hsl(` = 0), `--sidebar-*` jetonları rol
katmanına bağlandı, dark varyantı `[data-theme="dark"]`e çevrildi. Kapılar sonrasında da 22/22.

**HÜKÜM:** *"shadcn kullanılabilir"* ile *"CLI çıktısı olduğu gibi kabul edilebilir"* aynı şey
değil. Her `shadcn add` sonrası palet ve tema mekanizması **yeniden bağlanmalı** ve bu bir
kerelik değil **süregelen** bir bakım kalemidir. Göç kararı verilirse bu adım bir çiviyle
korunmalı, yoksa bir sonraki bileşen eklemesi bandı yeniden çiğner ve kimse görmez.

**Ağırlık güncellendi:** resmî bileşenlerle 68,2 → **109,6 kB gzip** (mevcut sayfa 18,6 kB).
