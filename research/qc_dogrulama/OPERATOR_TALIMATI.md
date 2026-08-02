# EDG-2026-021 · OPERATÖR TALİMATI — QC doğrulama defterini koşturma

Kart: `research/cards/EDG-2026-021-qc-delist-dogrulama.yaml`
Defter: `research/qc_dogrulama/qc_defter_021.py`
Şema: `research/qc_dogrulama/cikti_semasi.md`

Bu defter **QuantConnect Research'te operatörün kendi hesabında** koşar. Ölçüm motoru
dışarıdadır; ajanlar hesap açamaz, kimlik giremez. Aşağıdaki adımlar bunun içindir.

---

## 0. Kimlik/gizlilik notu (önce bu)

- **Bu defter hiçbir kimlik, API anahtarı, parola ya da hesap bilgisi İSTEMEZ ve TAŞIMAZ.**
  İçinde tek bir sır yoktur; ağa da çıkmaz (yalnız QC'nin kendi veri API'sini kullanır).
- Bana (ya da herhangi bir ajana) **QC hesap bilgisi, e-posta, parola, API token
  göndermeyin**. Gerekmiyor.
- Geri dönecek tek şey **son hücrenin JSON çıktısıdır**. O JSON'da da kimlik bilgisi yoktur;
  yalnız sayılar, sayım muhasebesi ve beyanlar bulunur. Yine de yapıştırmadan önce
  göz gezdirmeniz iyi olur.

---

## 1. Adım adım

1. **QuantConnect → Research** (sol menü "Research" / bir projenin içinden "Research" düğmesi).
2. **Yeni Python notebook** aç. (Notebook'un varsayılan ilk hücresinde
   `from AlgorithmImports import *` gibi bir satır olabilir — kalsın, zararı yok.)
3. **`research/qc_dogrulama/qc_defter_021.py` dosyasının TAMAMINI kopyala.**
4. Yapıştırma — iki seçenek, **ikisi de çalışır**:
   - **Kolay yol:** hepsini TEK hücreye yapıştır ve koş.
   - **Tercih edilen yol:** dosyadaki `# %%` satırları hücre sınırlarıdır; her `# %%`
     bloğunu ayrı bir hücreye koy ve sırayla koş. Böylece ilerlemeyi hücre hücre görürsün
     ve bir hücre çökerse öncekilerin sonucu bellekte kalır.
5. **Koş.** Her hücre ilerleme basar (`[H2] başlıyor...`, `evren 13/72 ...` gibi).
6. Koşum bitince **en sonda tek bir JSON bloğu** basılır. İki işaret arasındadır:

   ```
   <<<SONUC_021_JSON_BASLANGIC>>>
   { ... }
   <<<SONUC_021_JSON_SON>>>
   ```

   **İşaretlerin ARASINDAKİ metnin tamamını** kopyala (işaretler dahil değil).
7. Kaydet: repoda `research/olcumler/qc_dogrulama/sonuc_021.json`
   (klasör yoksa oluştur: `mkdir -p research/olcumler/qc_dogrulama`).
   **Ya da** JSON'u doğrudan sohbete yapıştır — Rol-1 kaydeder.
8. JSON'un yanında **konsol çıktısının son ~40 satırını** da iletmek faydalı olur
   (uyarılar ve hangi QC-API yolunun işlediği orada görünür).

---

## 2. Beklenen süre ve kaynak

| aşama | ne yapıyor | beklenen |
|---|---|---|
| H0–H1b | ayar + API keşfi + araç kopyaları | saniyeler |
| H2 | 72 aylık evren anlık görüntüsü | **1–6 dk** (ayda bir çağrı) |
| H3 | fiyat/hacim tarihi, 25'erli parçalar | **3–15 dk** (evren birleşimi 500–900 isim olabilir) |
| H4 | öznitelikler (rolling) | 1–3 dk |
| H5 | pozitif kontrol + IC blok bootstrap (600 tekrar) | **1–5 dk** |
| H6 | shares_outstanding as-of | 2–10 dk |
| H7–H8 | kesit + dilim + 2×2000 tekrar bootstrap | 1–4 dk |
| H9–H11 | betimleyici tablolar + JSON | saniyeler |

**Toplam beklenti: 10–45 dakika.** Yerel sahte-veri sınamasında (80 sembol) uçtan uca
14 saniye sürdü; gerçek koşum sembol sayısıyla ölçeklenir.

**Bellek.** Defter H3/H4/H6 sonunda panel bellek kullanımını basar
(`panel belleği ≈ ... MB`). Küçük bir research düğümünde 250–400 MB'ı aşarsa daralt.

### Çok uzun sürerse / bellek yetmezse — DARALTMA ANAHTARLARI

**H0 hücresinin en üstündeki `ANAHTAR` sözlüğünden başka HİÇBİR YERE dokunma.**

```python
"MAKS_SEMBOL": None,   # → örn. 300  : evren birleşimini en sık üye 300 sembolle sınırla
"AY_LIMIT":    None,   # → örn. 24   : yalnız ilk 24 ayı koş
"PARCA":       25,     # → örn. 10   : daha küçük parçalar (daha az bellek, daha çok çağrı)
```

Daraltılmış koşum JSON'a **kendini yazar** (`anahtarlar` bloğu + `tanim_sapmalari`), yani
Rol-1 farkı görür. **Daraltılmış koşum kart hükmünü taşımaz** — tanısaldır. Kart penceresi
sığmıyorsa bunu bildir, tam koşum ayrı planlanır.

> Pencere (`PENCERE_BAS`/`PENCERE_SON`), `EVREN_N`, `UST_PCT`, `UFUKLAR`, `BLOK`, `BOOT`,
> `TOHUM`, `MALIYET_BPS` **kartın beyanıdır — DEĞİŞTİRME.** Değişirse koşum kart dışı olur.

---

## 3. PK-DUR hâlinde ne yapılacak

Defterin içinde kartın emrettiği bir **pozitif kontrol kapısı** vardır (H5): `rvol20`'nin
20 günlük ileri getiriyle Spearman IC'si, yerel çivi ≈0,064'ün **işaret ve mertebesinde**
çıkmalıdır. Tutmazsa defter şunu basar:

```
PK-DUR: DEFTER DURDU. Son hücreyi (H11) yine de koş — ...
```

**Yapılacak:**

1. **Panik yok, tekrar tekrar koşma.** Bu bir "kill" değil; "boru hattı geçersiz" demektir.
2. Hücreleri ayrı ayrı koştuysan **son hücreyi (H11) yine de koş.** DUR hâlinde de JSON
   basar; içinde `DUR` nedeni ve ölçülen ham `ic` değeri vardır. Tek hücre olarak
   koştuysan JSON zaten en sonda basılmıştır.
3. **O JSON'u ve konsolun son ekranını bana ilet.** Rol-1 nedene bakar:
   - IC pozitif ama çok küçük/çok büyük → evren ya da tanım sapması (H2/H6 yolları)
   - IC negatif → veri yönü/tarih hizası sorunu
   - `ic: null` → kesit kurulamadı (`n`, `n_gun` alanları bunu söyler)
4. **Kartın eşiklerine, defterin sabitlerine ya da PK bandına DOKUNMA.** Eşik sonradan
   değişmez (ölçüm disiplini). Düzeltme gerekirse Rol-1 yeni bir defter sürümü verir.

Aynı şey **`shares_outstanding` alınamadığında** da geçerlidir: defter `DUR` yazar,
`olculemedi` alanına nedeni koyar ve **uydurma vekil üretmez** (kartın `kill_criteria`
maddesi bunu emrediyor). JSON'u aynen ilet.

---

## 4. Hata alırsan (çökme)

- **Hücreyi tek başına yeniden koşmak yeterlidir** — durum `S` sözlüğünde tutulur,
  önceki hücrelerin işi kaybolmaz (notebook çekirdeğini yeniden başlatmadığın sürece).
- Çekirdek yeniden başlarsa baştan koşmak gerekir.
- Hata metninin **tamamını** ilet: defterdeki savunmalı yollar hangi QC-API adlarını
  denediğini hata metnine yazar (`hiçbir QC-API yolu işlemedi → ... | ... | ...`) ve
  düzeltme tam olarak oradan çıkar.

---

## 5. Bu defterde QC-API'si SAVUNMALI yazıldı — beyan

Defteri yazan ajan **ağ çağrısı yapamadı**; QuantConnect'in çalışacağı LEAN sürümünü ve
Python yüzeyinin adlandırmasını (PascalCase mi snake_case mi) **doğrulayamadı**. Bu yüzden
her QC çağrısı "adlar listesi" üzerinden yapılır: **hangi ad varsa o kullanılır**, hangisinin
işlediği JSON'un `kosum.api_yolu` alanına yazılır. Hiçbir yol işlemezse defter **durur** —
sessizce vekil üretmez.

Savunmalı yazılan noktalar (JSON'da izlenebilir):

| nokta | denenen yollar |
|---|---|
| içe aktarma | `AlgorithmImports` → `QuantConnect.*` |
| metot adları | her çağrıda snake_case → PascalCase (`history`/`History` vb.) |
| `Resolution` | `DAILY` → `Daily` |
| `DataNormalizationMode` | `RAW`/`Raw`, `ADJUSTED`/`Adjusted` |
| tarih bağlamı | `set_start_date`/`SetStartDate` (yoksa uyarı, koşum sürer) |
| **evren verisi** | `add_universe`+`universe_history` → `history(Fundamental, t0, t1, res)` → `history(Fundamental, t0, t1)` → `history(CoarseFundamental, ...)` |
| evren dönüş şekli | DataFrame **ve** nesne-listesi, ikisi de normalize edilir |
| alan adları | `DollarVolume`/`dollar_volume`, `MarketCap`, `CompanyProfile.SharesOutstanding`, `HasFundamentalData` … |
| dolar hacim yoksa | `fiyat × hacim` vekili (beyanlı) |
| **SPX üyeliği** | `qb.universe.etf("SPY")` + `universe_history` denenir; olmazsa dolar-hacim üst-N **süzgeç-vekili** (kartın izin verdiği yol, beyanlı) |
| history normalizasyon | `data_normalization_mode=` → `dataNormalizationMode=` → kwarg'sız |
| history indeks düzeni | seviye adları okunur (`symbol`/`time`), varsayılmaz |
| **shares as-of** | `get_fundamental(CompanyProfile.SharesOutstanding)` → `history(Fundamental)` → `get_fundamental(MarketCap)/fiyat` → `get_fundamental(BasicAverageShares)` → hiçbiri yoksa **ölçülemedi + DUR** |
| pandas `stack()` | sürümler arası imza farkı (çıplak `stack()` + ayrı `dropna()`) |
| sembol kimliği | `symbol.ID`/`symbol.id` (ticker DEĞİL — ticker delist'te yeniden kullanılır) |

**Doğrulanamayan iki QC bilgisi (JSON'da beyan olarak duruyor):**

1. **Delist tespiti.** QC'nin map-file / `Delisting` olayına erişim yolu doğrulanamadı;
   defter **son-bar vekili** kullanır (sembolün son günlük barı pencere sonundan erken
   bitiyorsa "sonradan-delist"). Bu vekil, gerçek delist ile veri kesintisini ayıramaz.
   Her koşumda `tanim_sapmalari`na yazılır.
2. **Hacim bölünme bazı.** QC'nin `Adjusted` modunun hacmi ölçekleyip ölçeklemediği
   doğrulanamadı. Defter bu yüzden **Raw (ham) hacim** çeker ve turnover'ı ham hacim ÷
   as-of hisse sayımı olarak kurar (ikisi de aynı günün bazında → oran bölünmeden bağımsız).
   Raw çağrısı işlemezse düzeltilmiş hacme düşer ve **beyan eder**.

Ayrıca **QC fundamental verisinin gün-gün (point-in-time) teslim edildiği** QC'nin
belgelediği bir özelliktir; bu defter onu bağımsız doğrulamadı, `as_of_beyani` alanında
beyan olarak durur.

---

## 6. Defterin kendi güvenceleri (senin kontrol etmen gerekmez, ama bilmen iyi)

- **Deterministik**: sabit tohum; H1b kendi kendini sınar (`determinizm_sinamasi: true`).
  Aynı veriyle ikinci koşum aynı CI'yı verir.
- **Dış bağımlılıksız**: repo'dan hiçbir şey import etmez; bootstrap ve Spearman
  kopyaları defterin içindedir.
- **Eşik içermez**: JSON'da `SUCCESS`/`KILL`/`anlamlı` diye bir alan YOKTUR. Tek
  `GECTI` alanı kartın emrettiği PK kapısıdır. Hüküm Rol-1'dedir.
- **Uydurma yasağı**: ölçülemeyen her şey `null` + `neden`. Bayatlık (200 gün) ve
  fiziksel devir (>1.0) bekçileri EDG-016'dan taşındı ve kapattıkları hücreyi sayar.
- **Repoya hiçbir şey yazmaz**, hiçbir dosyayı değiştirmez, ağa çıkmaz.
