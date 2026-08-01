# Ölçüm Standartları (WP-M)

> Bu dosya bir ANLATI değil, bir KONTROL LİSTESİDİR. Ölçüm kartı yazan ya da ölçüm kodu koşan
> herkes buradaki dört maddeyi kartın "yöntem" bölümünde AÇIKÇA karşılar. Karşılamayan bir ölçüm
> hüküm taşımaz.
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
