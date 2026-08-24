# D2 — "YARIM GÖÇ" TEŞHİSİ VE KAPATILMASI

**Tarih:** 2026-08-24 · **Tetikleyen:** operatör · **Yöntem:** altı boyutlu paralel denetim + çürütme

## Operatörün cümlesi

> "neden hala düzelmiyor anlamıyorum, hala consistent değil ve eski tasarım dili duruyor,
> çerçeveler birinde oval diğerinde birleşik kare, eski tasarım dilinin olduğu bileşenler var,
> çerçeveler birbiri ile alakasız, yazılar birbiri ile align olmamış"

Bundan önce beş tur boyunca aynı şeyi söylemek zorunda kalmıştı. Her turda bir kusur düzeldi,
bir sonraki sürüklenme yine **operatörün gözüyle** bulundu. Teşhis o tekrarın kendisindeydi.

## Teşhis: pano tutarsız değil, YARIM GÖÇ halinde

Denetim altı gramer boyutunu (kap · etiket · hizalama · veri kanalı · rozet · renk rolü)
ayrı ayrı taradı; her bulgu ayrıca çürütmeye sokuldu (34 bulgu ayakta, 45'i düştü — çoğu
"kodun kendi yorumu bunu gerekçelendiriyor" ya da "düzeltme bilgi siler" diye). Beş mekanizma:

**(a) Göç EKSEN bazlı yapıldı, BİLEŞEN bazlı değil.** `index.html:1653` "ÇİP İŞARETİ — DUB
FEATURE PILL GRAMERİ" ilan ediyor; **16 satır aşağıda** `:1697` hâlâ `never a soft pill`
diyordu ve `.tag`/`.st`/`.gc` düğme yarıçapında (`--r-ctl` 8px) kalmıştı. Operatörün
"çerçeveler birinde oval diğerinde birleşik kare" cümlesinin birebir kaynağı buydu.

**(b) Aynı iş ÜÇ paralel uygulamada yaşıyordu.** "Dört hücreli sayısal band" panoda üç ayrı
gramerde yazılmıştı: `.durum-izgara` (12px yuvarlak, 16px boşluk) · `.pv-sekmeler`
(yarıçapsız, paylaşılan kenar) · `.ozet-serit` (1px saç teli). Bir tur birini düzeltiyor,
diğer ikisi eski dili taşımaya devam ediyordu.

**(c) Aynı SINIF ADI iki yüzeyde iki reçete.** `.pm-cell`, `.pm-conf`, `.bar`, `.tag`, `.st`,
`.pillc` — index.html ve landing.html'de farklı. index.html landing'in çizdiği hâli
**kusur ilan ediyordu**, ama düzeltme tek yüzeye uygulanmıştı.

**(d) Emekli gerekçe ÇİZİLMEDEN bırakıldı.** Meridian geleneği emekli kararı `~~üstü çizili~~`
bırakır. Çizilmeyen gerekçe yürürlükte sayılır ve **bir sonraki tur düzeltmeyi geri alır**.

**(e) Hiçbiri teste mandallanmamıştı.** `--r-md` jetonu hiçbir yerde tanımlı değildi; CSS
geçersiz bildirimi yutar, yarıçap sessizce 0 olur, kimse görmez.

## Uygulananlar

| # | Düzeltme | Kaç yeri düzeltti | Kapattığı sahne |
|---|---|---|---|
| D1 | `.pm-cell`den `justify-content` kalktı (index + landing) | 12 şerit · ~30 hücre | başlık kayması |
| D2 | `.pm-cell`den `gap` kalktı, mesafe `.pm-n`in kendi marjına indi | aynı | mesafe çatalı |
| D3 | `--r-md` → `--r-card` (tanımsız jeton) | 1 kap | kare köşeli iç çerçeve |
| D4 | Dörtlü band maketin paylaşılan-kenar reçetesine geçti | 2 band, bitişik | "oval ↔ birleşik kare" |
| D5 | `font-weight:700` → `600` (maket: 0 adet 700) | 37 kural | "eski tasarım dili" |
| D6 | `.slab` / `.pd-sub`tan alt çizgi kalktı | 45 emisyon | altı çizili büyük-harf başlık |
| D7 | Çip katmanı: yarıçap `--r-tag`, ağırlık 500, aile açık sans | 303 çip | çip gramerinin çatalı |
| D8 | Matriste `"az örnek"` → `"AZ ÖRNEK"` | 1 (son çatal) | rozetin iki sesi |
| D9 | `never a soft pill` gerekçesi ÜSTÜ ÇİZİLDİ | — | göçün geri alınması |

## KUSUR OLMAYAN, BİLEREK KORUNANLAR

Çürütme turu bunları reddetti — düzeltilseydi **bilgi silinecekti**:

* **Matriste vurgusuz sütunun siyah sayıları.** `signClass` bilerek bir gürültü bandı uyguluyor:
  `|ortalama| > 1/√n` değilse renk verilmez. Ölçtüm ve doğru çalışıyor — +0,12R (n=38, bant
  0,162) nötr; −0,79R (n=5, bant 0,447) kırmızı. Operatörün "aynı anlam iki renkte" okuması
  ölçümle YANLIŞ: ikisi aynı anlam değil, biri bandın içinde biri dışında. **Ama şikâyet
  geçerli bir okunabilirlik kusuruna işaret ediyor** — kural ekranda açıklanmıyor, yalnız
  çekmece açılınca görünüyor. Kod düzeltmesi değil, LEJANT gerektirir. *(açık kalem)*
* **Seçili sekmenin altındaki kalın çizgi** — `.pv-sekme[aria-selected]` göstergesi ve maketin
  kendi grameri.
* **`.pm-cell.sel` / `.pm-cell.thin` inset halkaları** — seçim ve örneklem-yetersizliği kanalı.
* **`border-left:3px`** — anomali kanalının taşıyıcısı (karar §10.2).
* **`.mrow`un cetvel grameri** — kart gramerini AÇIKÇA reddeden yazılı karar.

## Kalıcılık: dokuz yeni mandal

Asıl mesele düzeltmek değil, **operatörün gözünü testle değiştirmekti**.
`tests/test_tasarim_dili_tutarliligi_v285.py` artık şunları da ölçüyor:

* **T1** `.pm-cell` dikey hizalama bildirmez (veri farkını hiza farkına çeviriyordu)
* **T2** etiket→değer mesafesi tek kanaldan gelir (`gap` + `margin` toplanıyordu)
* **T3** kullanılan her `var(--x)` tanımlıdır — yorumlar soyulur, JS'in `setProperty` ile
  yazdıkları tanınır (`--r-md` sınıfı sessiz düşüşü kapatır)
* **T4** dörtlü sayısal bandlar tek reçeteyi paylaşır (kapalı kap + paylaşılan kenar + `gap:0`)
* **T8** çip yarıçapı istisnasız `--r-tag`; `--r-ctl` yalnız kontrol katmanında
* **T9** çip ağırlığı tek (500) ve aile açık — miras yasak
* **(önceki turdan)** canlı renk literali yok · tek saç teli · kesik çerçeve yok · rampa dışı punto yok

## AÇIK KALEMLER (çivilenemeyenler — yalnız sayfa çizilince görülür)

1. Gürültü bandı lejantı (yukarıda)
2. `.bar` reçetesi maketten sapıyor (9 emisyon) — makete uyan taraf **landing**, sapan ana pano
3. `.pos/.neg` 81 sabit geçişte DURUM anlatıyor, oysa kanal YÖN'e ait (`.sev-*` yalnız 14 yerde)
4. Ölü `.hero` bloğu (`index.html`) — iç içe çerçeve grameri, 0 okuyucu, kopyalanmayı bekliyor
5. 32 ölü `--yon-*-t` / `--yon-*-h` jetonu — tüketici araması 0 eşleşme
6. Çip katmanında `text-transform` (kanon: harf düzeni kaynak metinden gelir)
