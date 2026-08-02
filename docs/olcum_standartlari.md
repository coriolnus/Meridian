# Ölçüm Standartları (WP-M)

> Bu dosya bir ANLATI değil, bir KONTROL LİSTESİDİR. Ölçüm kartı yazan ya da ölçüm kodu koşan
> herkes buradaki DERSLERİ ve "Ölçüm şablonu — zorunlu adımlar" bölümünü kartın "yöntem"
> bölümünde AÇIKÇA karşılar. Karşılamayan bir ölçüm hüküm taşımaz.
>
> Kaynak: ROADMAP §WP-M (Metodoloji/Yasa Borçları). Her ders bir ÖLÇÜLMÜŞ vakadan doğdu; vaka
> numarası (EDG-00x) yanında yazılıdır — ders bir tercih değil, bir hata kaydıdır.

---

## Ders #1 — "oosonly" kolu ZORUNLUDUR (WP-G tanısı, kanıt: EDG-005)

**Kural.** Bir düğmenin (knob/overlay) OOS etkisi ölçülecekse, o düğmeyi **`oos_start`'ta devreye
alan** bir kol ölçüme MUTLAKA girer. "Baştan açık" tek kol yeterli DEĞİLDİR.

**Neden.** `walk_forward` tek parça replay koşar. IS döneminde açık olan her overlay, OOS skorunu
**portföy-durumu kanalıyla** kirletir: `peak_equity`, de-risk rampası ve devreden açık pozisyonlar
OOS penceresine IS'in izleriyle girer. Yani "OOS'ta kazandı" cümlesi, IS'in yankısını ölçüyor
olabilir.

**Kanıt.** EDG-005 tanısı: temiz pencerede kol ile "kapalı" **bit-bit** aynı çıktı; fark tamamen
IS-yankısıydı ve kill#1 orada tetiklendi.

**Kartta ne yazar.** "kol: oosonly (düğme oos_start'ta açılır)" + baştan-açık kolla farkın raporu.

---

## Ders #2 — Eşik DİLBİLGİSİ: her dal KENDİ niteleyicisini taşır (kanıt: EDG-009)

**Kural.** `success` ve `kill` metinlerinde **her dal** kendi istatistiksel niteleyicisini açıkça
taşır: "artar (CI 0-dışı)", "düşer (t>2)", "değişmez (CI 0'ı kapsıyor)". Bir niteleyici cümlenin
sonuna asılıp hangi dala ait olduğu belirsiz bırakılamaz.

**Neden.** Belirsiz bir niteleyici, hükmü **ölçümden sonra** seçilebilir hâle getirir — kartın var
oluş sebebi tam olarak bunu engellemektir.

**Kanıt.** EDG-009'da "(P>=0.95)" hangi dala ait olduğu belirsizdi ve iki okuma iki farklı hüküm
veriyordu.

**Belirsizlik çıkarsa.** Muhafazakâr okuma uygulanır (aday aleyhine) **ve** karta ders notu düşülür.
Eşik sonradan değiştirilemez.

---

## Ders #3 — Ölçüt HAM getiri okuyamaz: TABAN-FAZLASI zorunlu (kanıt: EDG-010)

**Kural.** `success`/`kill` ölçütleri **her zaman** taban-fazlası üzerinden yazılır: aynı-gün evren
ya da açıkça tanımlı ilgili alt-evren. Ham pozitif getiri bir kenar kanıtı DEĞİLDİR.

**Neden.** Ham pozitiflik piyasa sürüklenmesidir. Bir kurulum "kazandı" görünür, evren tabanına
karşı ölçüldüğünde kenar kaybolur — hatta negatife döner.

**Kanıt.** EDG-010 (G4 pullback): bağımsızlık GERÇEKti (Jaccard ~0,02) ama ham pozitiflik evren
tabanında kayboldu; dip10 trend-evreninde anlamlı NEGATİFti. Kart lafzen "success", kanıten
kenarsızdı — kusur adayda değil ÖLÇÜTTEYDİ.

**Kartta ne yazar.** Taban serisinin tanımı (hangi evren, hangi gün, hangi alt-küme) ve
taban-fazlasının formülü.

---

## Ders #4 — KIYAS TEMİZLİĞİ: taban, olay penceresinin DIŞINDA olmalı (kanıt: EAP yan bulgusu)

**Kural.** Ders #3'ün tabanı hesaplanırken, **taban serisinden olay-penceresi-içi satırlar
düşürülür** ve **kirlilik oranı raporlanır**. Bunun için ileriye dönük tek yol:

```python
from meridian.olcum_araclari import temiz_taban

rapor = temiz_taban(getiriler, olay_gunleri, pencere=(1, 10))
taban = rapor["degerler"]                 # olay-penceresi DIŞI satırlar
assert rapor["kirlilik_orani"] is not None  # None = ÖLÇÜLEMEDİ, 0.0 değil
```

**Neden.** EAP ölçümünde taban serisinin kendisi kirliydi: olay penceresinin içindeki bir günde
evrenin **%64-74'ü** kendi olay penceresindeydi. "Olay − evren medyanı" farkı olayı olayla
kıyaslıyordu ve etki sistematik olarak **SIKIŞIYORDU**. Hiçbir test kırılmaz, hiçbir istisna
atılmaz; yalnız her etki olduğundan küçük görünür — "hata değil, miktar değişimi" sınıfı.

**Kartta ne yazar (üçü de zorunlu).**
1. `kirlilik_orani` (kaç satır olay-penceresi-içiydi),
2. `pencere` ve `gun_birimi` (takvim günü mü, bar indeksi mi — birim hükmü değiştirir),
3. `n_temiz` (temizlikten sonra kalan taban büyüklüğü). `n_temiz` çok düşükse ölçüm "temiz taban
   yok" der; temizlenmiş ama boş bir tabanla kurulan kıyas, kirli kıyastan daha kötüdür.

**Geriye dönük düzeltme YOK.** `research/` altındaki mevcut ölçüm betikleri TARİHE aittir ve kendi
kartlarının hükmünü taşırlar. Onları bu fonksiyonla yeniden yazmak, geçmiş hükümleri sessizce
değiştirmek olurdu. Bu standart **ileriye** dönüktür; eski bir hükmü tazelemek istiyorsan bu, yeni
bir kart ve yeni bir ön-kayıt gerektirir.

**Fonksiyonun beyan ettiği sınırlar.**
- Pencere birimi **girdinin birimidir**. Takvim tarihi verirsen takvim günü, bar indeksi verirsen
  bar penceresi elde edersin — fonksiyon hangisini gördüğünü `gun_birimi` alanında söyler. Karışık
  birim `ValueError`'dır (sessiz toplama YOK).
- Olay listesinde adı geçmeyen bir kimliğin satırları TEMİZ sayılır; kaç kimliğin öyle sayıldığı
  `n_olaysiz_kimlik` ile görünür. "Olay listesi eksik" ile "o sembolde olay yok" aynı şey değildir.
- Hiç ölçülebilir satır yoksa `kirlilik_orani` **None**'dır (0.0 değil).

---

## Ders #5 — Taban AYNI GÜNÜN temiz evrenidir (gün-bazlı kıyas, 2026-08-02)

**Kural.** Ders #3 tabanı "aynı-gün evren" der; Ders #4 o tabanın olay-penceresinden temizlenmesini
ister. İkisi birlikte tek bir çağrıdır:

```python
from meridian.olcum_araclari import olay_disi_kiyas

r = olay_disi_kiyas(evren_getirileri, olay_gunleri, pencere=(1, 10), min_taban=5)
fazlalar = r["fazlalar"]              # her hedefin AYNI GÜN temiz-evren medyanından fazlası
assert r["n_taban_yok"] == 0 or r["uyari"]   # tabansız hedefler SAYILIR, sessizce düşmez
```

**Neden `temiz_taban` yetmiyor.** `temiz_taban` tek bir HAVUZ döndürür — "olay penceresine hiç
değmemiş tüm satırlar". Havuz tabanı, olay gününün piyasa-genelinde nasıl bir gün olduğunu (rejim,
volatilite, endeks hareketi) düzeltmez. İki taban iki ayrı soruya cevaptır ve ikisi de meşrudur:
havuz "bu kurulum genel olarak evrenden farklı mı", gün tabanı "olay günü O GÜNÜN evreninden
farklı mı" (olay-çalışması sorusu). Kart hangisini kullandığını YAZAR.

**Fonksiyonun dört dürüstlük kuralı (çıktıda adıyla durur).**
1. Hedefin **kendi kimliği** o günün tabanından düşülür — yoksa ölçüm kendini kendine kıyaslar ve
   etkiyi 1/N kadar sistematik olarak küçültür.
2. `min_taban` altındaki günler kıyasa GİRMEZ ve `n_taban_yok` ile sayılır. Bu günler rastgele
   değildir (ince günler sistematik olarak seçilir) — sessiz düşürme burada seçim yanlılığıdır.
3. `sikisma` alanı, aynı hedeflerin KİRLİ tabanla (o günün tüm satırları) kıyasını da verir ve
   farkı yazar: temizliğin etkiyi ne kadar açtığı raporda görünür. **Kirli taban hükme girmez**,
   yalnız düzeltmenin büyüklüğünü gösterir.
4. `kirlilik_orani` hiç ölçülebilir satır yoksa **None**'dır (0.0 değil).

**Kartta ne yazar.** `ozet` (medyan mı ortalama mı), `min_taban`, `n_taban_yok`, `kirlilik_orani`,
`sikisma.fark`. `fazlalar` serisi zaman sıralıysa aralığı **Ders #6** ile kurulur.

---

## Ders #6 — Aralık BLOK bootstrap'la kurulur; IID bir tercih değil HATA SINIFIDIR (2026-08-02)

**Kural.** Seri zaman sıralıysa ve gözlemler arasında otokorelasyon olasıysa — günlük/bar
getirileri, işlem serileri, eşitlik eğrisi farkları, gün-bazlı taban-fazlası serileri — güven
aralığı **blok** bootstrap ile kurulur:

```python
from meridian.olcum_araclari import blok_bootstrap_ci

ci = blok_bootstrap_ci(fazlalar)                 # blok=None → n^(1/3) kuralı
assert ci["lo"] is not None                      # None = ÖLÇÜLEMEDİ (neden alanı dolu)
karar = ci["sifiri_disliyor"]                    # ölçülemediyse None — False DEĞİL
```

**IID bootstrap (`blok=1`) bu sınıfta YASAKTIR.** Bağımlılığı kırar, ortalamanın örnekleme
dağılımını olduğundan dar gösterir ve hükmü **tek yönde** kaydırır: IID daima "daha anlamlı"
görünür, hiçbir zaman daha az. Fonksiyon `blok=1`i reddetmez ama `iid: True` diye damgalar ve
uyarır — IID yalnız gözlemlerin gerçekten değiştirilebilir (exchangeable) olduğu kesitlerde
meşrudur ve o zaman bile kartta "neden IID meşru" cümlesi yazılır.

**Kanıt (bu depodan, ölçülmüş).** Dolar beklentisi, n=95: IID aralık [−116,86, −0,00] sıfırı kıl
payı dışarıda bırakıyordu — okuma: "kaybettiğimiz kanıtlandı". Blok aralık [−137,75, +14,53] sıfırı
içeriyor — okuma: "n=95'te henüz kanıtlanmadı". Aynı defter, iki hüküm.

**Beyan edilen sınırlar (çıktıda durur).** MOVING (örtüşen) bloktur, dizi sarılmaz; bedeli
uçlardaki gözlemlerin biraz az örneklenmesidir. Aralık ORTALAMA içindir (medyan/oran için yeniden
türetilir). Serinin ZAMAN SIRASINDA olduğu varsayılır — karıştırılmış bir seride blok yapısı
anlamsızdır ve fonksiyon bunu anlayamaz. `n < 4×blok` ise uyarı çıkar.

**Mevcut hesaplar değişmedi.** `analytics._blok_bootstrap_ci` (CIRCULAR blok, blok=5 **işlem**) ve
`score.tail_risk` kendi eksenlerinde aynen çalışır; onlar yayımlanmış hükümlerin tabanıdır ve bu
standart onları geriye dönük yeniden yazmaz.

---

## Ders #7 — Çok hücreli özette EN İYİ HÜCRE küçültülmeden yazılmaz (2026-08-02)

**Kural.** Bir kart K hücre ölçüyorsa (bileşen × ufuk, rejim × kurulum, eşik × pencere) ve özette
"en iyi hücre" rapor ediliyorsa, ham değerin YANINDA küçültülmüş değeri de yazılır:

```python
from meridian.olcum_araclari import eb_kucult

r = eb_kucult({"rs@10": 0.21, "rvol@10": 0.08, ...}, {"rs@10": 0.09, "rvol@10": 0.09, ...})
r["en_iyi_ham"]["ham"], r["en_iyi_ham"]["kucultulmus"], r["sira_degisti"]
```

**Neden.** En iyi hücre, en büyük GERÇEK etkiye sahip hücre değildir: en büyük (gerçek etki +
gürültü) toplamına sahip hücredir. Ham en-iyi bu yüzden **sistematik olarak yukarı yanlıdır** ve
yanlılık hücre sayısıyla büyür ("kazananın laneti"). Bu, K-cezasının kapıda çözdüğü sorunun ÖZET
tarafındaki ikizidir: kapı "kaç yoklama yaptın?" diye sorar, küçültme "kazananın ne kadarı
gürültüydü?" diye sorar. İkisi birbirinin yerine geçmez.

**Hüküm vermez.** Küçültülmüş değer eşiklere GİRMEZ ve `success`/`kill` ölçütlerinde kullanılmaz —
küçültme örneklemi büyütmez, yalnız gürültüyü geri alır. Kart eşiği neyse odur; bu araç eşiği ne
gevşetir ne sıkar (`analytics._empirical_bayes`in "verdict tabanlarına giremez" beyanının aynısı).

**Beyan edilen sınırlar.** τ² sıfıra kıstırılırsa ("hücreler arasında ölçülebilir gerçek fark YOK")
her hücre ortak ortalamaya TAM küçültülür — eksiklik değil, dürüst cevap. Hücreler **bağımsız
varsayılır**; aynı gözlemlerden türeyen hücrelerde (aynı bileşenin 5/10/20 bar ufukları) τ² bir
miktar küçük, küçültme bir miktar güçlü olur. SE'si olmayan hücre küçültülMEZ, atılmaz: ham hâliyle
durur ve `n_se_yok` ile sayılır.

**İKİZİ VAR, BİLEREK AYRI.** `analytics._empirical_bayes` aynı momentler yöntemini {mean, n, sd}
sözleşmesiyle ve n-ağırlıklı tabanla uygular; o, YAYIMLANMIŞ sayıların (`component_ic.json` `eb`
sütunu, pano) kaynağıdır. `eb_kucult` doğrudan SE ile ve düz-ortalama hedefiyle çalışır ve kart
özetlerinin standardıdır. İkisini tek gövdeye indirgemek yayımlanmış `eb_ic` değerlerini habersiz
oynatırdı.

---

## Ölçüm şablonu — ZORUNLU ADIMLAR (pozitif kontrol + PK4/PK5, 2026-08-02)

Bu bölüm yeni bir kural getirmiyor: **yapılmakta olanı yazıya geçiriyor.** trend-kolu, vcp, inplay,
pullback ve wp2 ölçümleri bu adımları zaten koştu ve raporlarında ayrı başlıklar altında yazdı;
yazılı olmadığı için her tur yeniden keşfediliyordu. Bundan böyle bir ölçüm raporu bu üç kapıyı
**adıyla ve sayısıyla** taşır. Taşımayan rapor eksiktir; hükmü askıdadır.

**(i) POZİTİF KONTROL — boru hattı bilinen bir etkiyi bulabiliyor mu?**
Kartta ÖNCEDEN yazılmış, bilinen bir büyüklük (ör. "cf katmanında ham rvol20 @20 IC ≈ 0,0645") aynı
boru hattından yeniden ölçülür; ölçülen değer, sapma ve **önceden yazılmış tolerans** rapora yazılır.
Sıfır bulan bir ölçüm, pozitif kontrolü olmadan "edge yok" diyemez — bulamayan bir boru hattı da
sıfır gösterir. Pozitif kontrolün kendisi ölçüm başlamadan karta yazılır (sonradan seçilen kontrol,
kontrol değildir).

> **UYARI (trend-kolu dersi, 2026-07-31): tek-enstrümanlı pozitif kontrol, portföy-yolu hatalarına
> karşı YAPISAL OLARAK KÖRDÜR.** SPY'ın kendisinde doğrulanan bir mantık, ağırlıklandırma/defter
> tarafındaki %27'lik bir sapmayı göstermedi. PK4/PK5 tam bu yüzden eklendi ve hatayı anında
> ayrıştırdı.

**(ii) PK4 — YOL TUTARLILIĞI.** İki farklı yoldan hesaplanan aynı büyüklük birebir tutmalıdır.
Kanonik biçimi: `close[t+h]/close[t] − 1`, aradaki GÜNLÜK getirilerin bileşiğine eşit olmalı.
Portföy tarafında: ağırlık serisinden türetilen eğri ile defterden türetilen eğri aynı olmalı.
Rapora **n** ve **maks mutlak/bağıl fark** yazılır (geçmiş turlar: 0,0 · 7,0e-14%). Bu kapı,
takvim kapısının/bütünlük kırpmasının ufkun İÇİNDE bar düşürmesini ve bir günlük kayma hatalarını
yakalar — ikisi de hiçbir istisna atmadan hükmü kaydırır.

**(iii) PK5 — ÖZDEŞLİKLER.** Ölçümün dayandığı cebirsel/mantıksal özdeşlikler tek tek sınanır ve
her biri ayrı satırda raporlanır. Bu depoda görülmüş özdeşlik aileleri:
- **geriye-bakışsızlık:** gösterge TAM seride ve `df.iloc[:i+1]` KESİLMİŞ seride aynı değeri vermeli
  (kart "yalnız t ve öncesi" diyorsa bu bir iddia değil, sınanabilir bir özdeşliktir);
- **bağımsız yeniden-türetim:** vektörize hesap, kaba/saf-python bir ikinci uygulamayla birebir aynı;
- **nakit-akışı özdeşliği:** friksiyon/boyutlandırma defteri kapanmalı (geçmiş tur: −1,9e-12%);
- **kaynak özdeşliği:** yeniden kurulan kompozit, motorun KENDİ döndürdüğü skorla birebir aynı.

**Rapor kapı satırı.** Üç kapı raporun sonunda tek satırda özetlenir:
`pozitif kontrol EVET/HAYIR · PK4 EVET/HAYIR · PK5 EVET/HAYIR`. **HAYIR bir başarısızlık değil, bir
DURDURMA sebebidir**: kapısı düşmüş bir ölçümün hükmü yazılmaz.

---

## Ek — KOD-SÜRÜMÜ DAMGASI (2026-08-02)

**Kural.** Ölçüm raporu, hangi kod hâliyle üretildiğini KENDİ İÇİNDE söyler:
`olcum_araclari.kod_surumu_damgasi()` → `git_head` + `kirli_agac` + `arac_surumleri`.
Bugün `prescreen` raporları (`prescreen_sonuc.json` ve kısmi `prescreen_kismi.json`) bu damgayı
`kod_surumu` alanında taşır; damga koşu BAŞINDA bir kez alınır (koşu ortasında checkout yapılırsa
iki rapor iki farklı SHA göstermesin).

**Neden.** "Bu sayı hangi kodla üretildi?" sorusunun cevabı raporun dışında arandığında (dosya
tarihi, oturum kaydı, hafıza) tahmine dönüşür; bir aracın davranışı değiştiğinde eski rapor
SESSİZCE yeni davranışla okunur.

**İki dürüstlük kuralı.** (1) git yoksa/başarısızsa `git_head` **None** ve `git_neden` doludur —
boş dizgi ya da tahmin yazılmaz. (2) `kirli_agac: True` ise rapor o SHA'dan **yeniden üretilemez**;
SHA o anki kodun değil, atasının adıdır. Damga bir ÖLÇÜM değil bir KİMLİKTİR: yokluğu ölçümü
geçersizleştirmez, ama sessizce yokluğu kabul edilemez.

---

## İLERİYE DÖNÜKLÜK ŞERHİ (bu dosyanın tamamı için)

**Bu dosyaya bir ders ya da araç eklenmesi, o araç olmadan verilmiş HİÇBİR kart hükmünü
geçersizleştirmez ve hiçbir eşiği geriye dönük değiştirmez.** `research/cards/` altındaki mevcut
hükümler, eşikler ve kill-list'ler oldukları gibi durur; `research/olcumler/` altındaki raporlar
tarihe aittir. Eski bir hükmü yeni bir araçla tazelemek istiyorsan bu, **yeni bir ön-kayıt kartı**
ve yeni bir ölçüm gerektirir — eski kartın üzerine yazılmaz.

Sebep, standartların kendisiyle aynı: hükmü ölçümden SONRA değiştirebilmek, kartın var oluş
sebebini ortadan kaldırır. Bir aracın "daha doğru" olması onu geçmişe uygulama yetkisi vermez;
verirse, hangi geçmiş hükmün hangi araçla yeniden okunacağını seçen kişi hükmü de seçmiş olur.

---

## Ek — CANLI-BEKLENTİ TAVANI (WP-M borç kalemi, bağlandı 2026-08-01)

**Kural (ROADMAP §WP-M).** Canlıdan beklenen tavan = backtest beklentisi × **0,5**; canlı/backtest
oranı **0,4**'ün altına düşerse **süspansiyon değerlendirmesi**.

**Nerede yaşıyor.**
- Katsayılar: `meridian/config.py` → `live_expectancy_rule()`. Varsayılanlar **KODDA**
  (`LIVE_EXPECTANCY_CAP_MULT=0.5`, `LIVE_SUSPEND_RATIO=0.4`), yani `state/goal.yaml`da alan
  olmasa da kural yürürlüktedir. Dosyada `live_expectancy_cap_mult` / `live_suspend_ratio`
  anahtarları varsa **dosya kazanır** ve her okumada kaynak (`goal.yaml` / `kod varsayilani`)
  adıyla raporlanır.
- Ölçüm: `meridian/analytics.py` → `live_expectancy_ceiling()`; yüzeyi
  `result_verdict()["tavan_durumu"]` (dolayısıyla `/api/diagnostics`).

**Hüküm VERMEZ.** `beta_duzeltilmis` / `net_kotumser` ile aynı sınıf: KOLON, ölçüt değil.
`criteria` sözlüğüne girmez, `passed/failed/unmeasured/zayif` sayaçlarına dokunmaz, hiçbir kapıyı
(probgate/guard/arming) kısmaz. Süspansiyon bir **operatör kararıdır**; bu alan onu yalnız görünür
kılar.

**Neden mevcut bir karar noktasına bağlanmadı.** Tarandı (probgate, reflect/rollback, guard,
arming, `autonomy_ladder`, `oos_erosion`, watchdog, versioning): depoda canlı ile backtest'i
kıyaslayan tek mekanizma `probgate.refresh_meta_calibration`dır ve o **beklenti seviyesini değil ΔS
farkını** kıyaslar (`predicted_delta` ↔ `realized_delta`) — üstelik kendi beyanıyla **ölçek borcu**
altındadır. Farklı bir soruyu ölçen bir mekanizmaya ikinci bir anlam yüklemek yerine, ölçüm canlı
beklentinin zaten yaşadığı yere (SONUÇ hükmü) kolon olarak konuldu.

**Ölçüm sınırları (çıktıda adıyla durur).**
- Oran yalnız **pozitif** bir backtest beklentisinde tanımlıdır: negatif bir beklentinin "yarısı"
  bir tavan değildir → `durum: olculemedi`.
- Canlı payda `learning_scorecard`ınkiyle aynıdır: `live_paper + belirsiz`; `replay_seed` satırları
  TRAINING'dir ve girmez.
- İki taraf da **aynı sürümden** okunur (`rollback.check_and_rollback` popülasyon yasası).
- `canli_n < min_sample` ise durum `olculemedi`dir — 0 değil, **BİLİNMİYOR**.

**Operatöre şerh.** Katsayılar bir gün `state/goal.yaml`a yazılırsa, aynı adlar
`guard.GOAL_KEYS`'e de eklenmelidir; aksi hâlde GU1 sürüklenme testi "tanınmayan anahtar" diye
kırmızı yanar.

---

## Ek — 2C EMPİRİK-BAYES SÜTUNU (bağlandı 2026-08-01)

`state/component_ic.json` artık `eb` adlı bir **paralel sütun** taşır: her hücrenin ham `ic`'sinin
yanında, o KATMANIN ortak ortalamasına küçültülmüş ikizi (`eb_ic`) ve küçültme katsayısı
(`shrink_katsayisi` = hücrenin kendi tahminine verilen ağırlık; 1 = hiç küçültme, 0 = tam küçültme).

- **`tablo` sözlüğü bit-bit aynı kalır.** Okuyucular (beyin `compact_lines`, pano, yeniden-üretim
  farkı) HAM `ic` okumaya devam eder. `eb` bugün yalnız görünürdür.
- **Katmanlar ayrı küçültülür.** `gercek` (alınmış işlemler) ve `cf` (alınmamış hipotetik girişler)
  farklı popülasyonlardır; tek ortalamaya çekmek iki farklı gerçeği eritirdi.
- **σ yasası:** küçültme HAM IC (r) ölçeğinde yapılır, orada σᵢ = 1/√(n−1). Hücrenin `ci` alanı ise
  Fisher-z ölçeğindedir ve orada SE = 1/√(n−3). İki farklı sabit, iki farklı **ölçek** — çelişki
  değil.
- **Beyan edilen sınır:** aynı bileşenin 5/10/20 bar hücreleri aynı gözlemlerden türer, bağımsız
  değildir → τ² bir miktar küçük, küçültme bir miktar güçlü olabilir.
- Dış okuyucu: `analytics.shrunk_component_ic()["tablo_ici_eb"]` (YASA 6).

---

## Ek — CHEN-2022 t-HURDLE DENGELEME NOTU (K-cezası kalibrasyon referansı, 2026-08-01)

**GEVŞETME DEĞİL, REFERANS.** Bu not `probgate.p_required_for`u değiştirmez; kapı bugün ne
yapıyorsa aynen onu yapmaya devam eder. Yazılma sebebi tek: kalibre edilmemiş bir ceza, gevşek bir
ceza kadar ölçülmemiştir — ve K-cezasının hangi kutupta durduğu hiçbir yerde yazılı değildi.

Kapımız çoklu-sınamanın **en muhafazakâr** ucundadır: `p_req = 1 − α_family/K` (gerçek Bonferroni,
2026-07-22'den beri; aile-bazlı hata oranını = FWER kontrol eder, tavan yok). Literatürün öteki
kutbu Harvey–Liu–Zhu (2016) tarafında değil karşısındadır: HLZ kesitsel tahminciler için t > 3,0
civarı bir çıta önerirken, **Chen (2022)** yayın yanlılığına FDR (yanlış keşif oranı) merceğinden
bakıp bu sertliğin **aşırı cezalandırdığını** savunur — gerçek bir kenarı reddetmenin (Tip-II)
maliyeti FWER hesabına hiç girmez.

**Bu depodaki hüküm — üç cümle.**
1. FWER kutbunda kalıyoruz, bilinçli: yanlış bir "ship" doğrudan para kaybettirir, kaçırılan bir
   aday ise yalnız fırsat maliyetidir ve **yeniden aranabilir**. Asimetri gerçek.
2. Ama sertlik ölçülmemiş bir erdemdir: K=40'ta p_req 0,995 olur ve *"kapı kaç GERÇEK kenarı
   reddetti?"* sorusu bu depoda ÖLÇÜLMEMİŞTİR (`oos_erosion` yıpranmayı, `deflate_why` huniyi sayar;
   ikisi de "reddedilen aday null mıydı" sorusunu cevaplamaz).
3. FDR tarafına geçmek (ör. Benjamini–Hochberg) bir **kapı gevşetmesidir** → ön-kayıtlı ölçüm kartı
   olmadan yapılmaz (`research/cards/`).

**Kartta ne yazar.** K-cezasına dokunan her ölçüm hangi kutupta ölçtüğünü (FWER mi FDR mi) ve
`k_probes` paydasının nasıl sayıldığını açıkça yazar. "Grid'de ÇARPILARAK sayılır" kuralı DEĞİŞMEZ.

---

## Ek — TIME_TIGHTEN KARAR KAYDI (2026-08-01)

**Karar: `earnings.TIME_TIGHTEN` KAPALI KALIR.** Açılması **blackout-etki ölçüm kartına** bağlıdır
— kapı gevşetmesi ölçümsüz yapılmaz.

Anahtar açılsaydı `in_blackout` BMO satırlarında karartmanın yakın ucunu bir gün daraltırdı (rapor
gününün kendisi karartmadan çıkardı). Veri gerçek: Nasdaq takvimi satırların ~%34'ünde BMO/AMC
söylüyor (ölçüm 2026-08-01, 6 iş günü / 1307 satır: time-not-supplied %65,7 · time-after-hours
%19,7 · time-pre-market %14,5). **Ama daraltmanın ETKİSİ ölçülmemiştir** — "BMO günü girmek AMC
günü girmekten ne kadar farklı?" sorusunun bu depoda tek satırlık bir ölçümü yok. Ölçülmemiş bir
gevşetme, kazandığı işlemleri gösterir ve kaybettirdiği gap'leri saymaz.

**Açılma şartı (tek yol).** Ön-kayıtlı bir kart (`research/cards/`): BMO/AMC ayrımının rapor-günü
girişlerindeki getiri dağılımına etkisi + kill kriteri. Kart hüküm verirse anahtar Rol-1 kararıyla
açılır. Bugünkü hâli: yol KURULU ve testte açılıp kapatılarak gerçekten çalıştığı kanıtlanıyor
(`tests/test_wpd_kalanlar_v147.py`), veri bugünden itibaren birikiyor (geçmiş takvim geriye doğru
zenginleşmez) ve birikimin sayacı `earnings.coverage()["saat_bilinen"]`dır — kart yazıldığı gün
ölçecek verisi hazır olur.
