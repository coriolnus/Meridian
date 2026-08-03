# EDG-2026-021 · OPERATÖR TALİMATI — QC doğrulama defterini koşturma (defter v2)

## §0 — CANLI DURUM (2026-08-03 ~12:05 UTC, Rol-1 oturumu bıraktı)

**QC projesi:** `Fat Apricot Koala` (id 34763939), Research notebook `research.ipynb`, çekirdek
`Foundation-Py-Default` seçili ve çalışıyor.

**YÜKLENMİŞ:** `defter_021.py` = v3 **parça A** (327 satır, kaydedildi/derlendi).
**YÜKLENMEMİŞ:** parça B (`qc_defter_021_b.py`, 25.746 kr) ve parça C (`qc_defter_021_c.py`, 22.451 kr).
**KİRLİ:** notebook'ta v2 turundan kalma hücreler + 4 sonda hücresi var — koşumdan ÖNCE silinmeli
(ya da `Restart` + yalnız yeni hücreler koşulmalı).

### Kalan üç adım (~3 dakika)
1. QC IDE'de iki dosya oluştur (⌘⇧P → *Create: New File*): `defter_021b.py` ve `defter_021c.py`;
   her birine yereldeki `qc_defter_021_b.py` / `_c.py` içeriğini yapıştır + ⌘S.
   *(Dikkat: dosya-adı diyaloğu AÇIKKEN ⌘V basma — yapıştırma ad alanına gider. Önce OK'a bas.)*
2. Notebook'taki TÜM hücreleri sil, tek hücre bırak ve şunu koy:
   ```python
   for _p in ("", "b", "c"):
       exec(open(f"defter_021{_p}.py").read(), globals())
   ```
3. **Run All.** Beklenen: mini-sonda satır sayısı basar → panel dilimleri → PK → ölçüm → sonda
   JSON. Sonucu `<<<SONUC_021_JSON_BASLANGIC>>>` ve `<<<SONUC_021_JSON_SON>>>` işaretleri ARASINDAN
   kopyalayıp `research/olcumler/qc_dogrulama/sonuc_021.json` olarak kaydet (ya da sohbete yapıştır).

**Mini-sonda 0 satır derse:** DUR metnindeki kontrol listesini izle — `QB_PANEL` taze mi, üzerinde
`add_equity`/`set_start_date` çağrıldı mı. (Bu kural v2'nin canlı arızasının kök nedeniydi;
bkz. `QC_API_ZEMIN_GERCEGI.md` "EK ÖLÇÜM".)

> ⚠️ **v3 GÜNCELLEMESİ (2026-08-03) — bu belgenin §2/§3/§7 adımları BAYAT.**
> Defter artık TEK dosya değil ÜÇ dosya (QC `.py` başına 32.000 karakter sınırı — ölçüldü):
> `qc_defter_021_a.py` (15.708) · `_b.py` (25.746) · `_c.py` (22.451). Projeye üçü de yüklenir,
> notebook'ta TEK hücre şunu koşar:
> ```python
> for _p in ("a", "b", "c"):
>     exec(open(f"qc_defter_021_{_p}.py").read(), globals())
> ```
> Ayrıca: QuantBook örneği PAYLAŞILMAZ (QB_BAR/QB_PANEL/QB_SPX ayrı; canlı arızanın kök nedeni —
> bkz. QC_API_ZEMIN_GERCEGI.md "EK ÖLÇÜM"). H2'de 10-günlük mini-sonda kapısı vardır: evren boş
> dönerse koşum 0,3 sn'de DUR der, 7 yıllık boş çekim yapmaz.


Kart: `research/cards/EDG-2026-021-qc-delist-dogrulama.yaml`
Defter: `research/qc_dogrulama/qc_defter_021.py` (**sürüm 2.0**)
Şema: `research/qc_dogrulama/cikti_semasi.md`
Zemin gerçeği: `research/qc_dogrulama/QC_API_ZEMIN_GERCEGI.md`

Bu defter **QuantConnect Research'te operatörün kendi hesabında** koşar. Ölçüm motoru
dışarıdadır; ajanlar hesap açamaz, kimlik giremez.

---

## 0. Kimlik/gizlilik notu (önce bu)

- **Defter hiçbir kimlik, API anahtarı, parola ya da hesap bilgisi İSTEMEZ ve TAŞIMAZ.**
  İçinde tek bir sır yoktur; ağa çıkmaz (yalnız QC'nin kendi veri API'sini kullanır).
- Bana (ya da herhangi bir ajana) **QC hesap bilgisi, e-posta, parola, API token
  göndermeyin**. Gerekmiyor.
- Geri dönecek tek şey **son hücrenin JSON çıktısıdır**; içinde kimlik yoktur, yalnız
  sayılar, sayım muhasebesi ve beyanlar bulunur.
- **Defter repoya hiçbir şey yazmaz**, hiçbir dosyayı değiştirmez.

---

## 1. v1 neden durdu, v2'de ne değişti (bunu bilmen işine yarar)

v1 koşumu **H2'de DUR** dedi. Sebep tahmin değil, **ölçüldü** (`QC_API_ZEMIN_GERCEGI.md`):
FREE hesapta `qb.history(Fundamental, …)` ve `qb.history(CoarseFundamental, …)` **boş
DataFrame** döndürüyor. v1 evreni bu yollardan kurmaya çalışıyordu.

v2 **tek kaynağa** geçti:

```python
u = qb.add_universe(secici)
seri = qb.universe_history(u, t0, t1)     # Series · her değer list[Fundamental]
```

Evren seçimi, fiyat, hacim **ve as-of hisse sayısı** artık aynı çağrıdan geliyor. Bunun iki
sonucu var: (1) ölü yollar defterden çıktı, defter kısaldı ve hızlandı; (2) her gün kendi
evren kesitinden okunduğu için **ileri-bakış yok, sağkalan süzgeci yok** — kartın ölçmek
istediği delist-dahillik mimarinin doğal sonucu.

**v1'den çıkarılan ölü yollar:** `history(Fundamental)`, `history(CoarseFundamental)`,
`get_fundamental(...)` merdiveni (4 yol), PascalCase/snake_case "adlar merdiveni",
DataFrame+nesne çift normalizasyonu, aylık evren yeniden-örnekleme makinesi.

---

## 2. Adım adım — **yükleme yöntemi v1'den FARKLI**

QuantConnect **dosya başına 64.000 karakter** sınırı koyuyor ve bu sınır bir notebook
hücresine yapıştırılan metni de vuruyor (ipynb'de JSON şişmesiyle daha da kötü). Bu yüzden
defter artık **.py dosyası olarak yüklenir**, hücreye yapıştırılmaz.

1. **QuantConnect → bir projeye gir → Research.**
2. Sol paneldeki dosya listesine **`qc_defter_021.py` dosyasını YÜKLE**
   (proje dosya alanına sürükle-bırak ya da "Add File" → içeriğini yapıştır → aynı adla
   kaydet). Dosya, notebook ile **aynı klasörde** olmalı.
3. **Yeni Python notebook** aç.
4. **Tek bir hücreye** şunu yaz ve koş:

   ```python
   exec(open('qc_defter_021.py').read())
   ```

5. Hücre ilerleme basar (`[H2] başlıyor...`, `panel dilim 3/7 ...` gibi).
6. Koşum bitince **en sonda tek bir JSON bloğu** basılır:

   ```
   <<<SONUC_021_JSON_BASLANGIC>>>
   { ... }
   <<<SONUC_021_JSON_SON>>>
   ```

   **İşaretlerin ARASINDAKİ metnin tamamını** kopyala (işaretler dahil değil).
7. Kaydet: `research/olcumler/qc_dogrulama/sonuc_021.json`
   (klasör yoksa: `mkdir -p research/olcumler/qc_dogrulama`). **Ya da** JSON'u doğrudan
   sohbete yapıştır — Rol-1 kaydeder.
8. JSON'un yanında **konsol çıktısının son ~40 satırını** da iletmek faydalı olur.

> **Dosya yükleyemiyorsan** (arayüz izin vermiyorsa): defterdeki `# %%` satırları hücre
> sınırıdır; blokları ayrı hücrelere bölüp sırayla koşabilirsin. Durum tek bir `S`
> sözlüğünde taşındığı için sonuç aynıdır. Tek dosya ~59.000 karakterdir; tek hücreye
> sığar ama sınıra yakındır — bölerek koşmak daha güvenlidir.

---

## 3. Beklenen süre ve kaynak

| aşama | ne yapıyor | beklenen |
|---|---|---|
| H0–H1b | ayar + araç kopyaları + determinizm sınaması | saniyeler |
| **H2** | **panel: `universe_history` × 7 yıl dilimi** | **5–25 dk** (defterin en pahalı yeri) |
| H3 | fiyat çapraz-kontrolü (6 sembol) | 10–60 sn |
| H3 (tamir) | *yalnız gerekirse* tam `history` çekimi | +5–20 dk (bkz. §5) |
| H4 | öznitelikler + süreklilik bekçileri | 1–3 dk |
| H5 | pozitif kontrol + IC blok bootstrap (600 tekrar) | 1–5 dk |
| H6–H8 | turnover + kesit + dilim + 2×2000 tekrar bootstrap | 1–4 dk |
| H9–H11 | betimleyici tablolar + JSON | saniyeler |

**Toplam beklenti: 10–40 dakika** (tamir tetiklenirse 20–60 dk). Yerel sahte-veri
sınamasında (70 sembol, 6 yıl) uçtan uca **11 saniye** sürdü; gerçek koşum sembol sayısıyla
ölçeklenir.

**Bellek.** Defter H4/H6 sonunda panel bellek kullanımını basar (`bellek≈… MB`). Küçük bir
research düğümünde 400 MB'ı aşarsa daralt.

### Çok uzun sürerse / bellek yetmezse — DARALTMA ANAHTARLARI

**H0 hücresindeki `ANAHTAR` sözlüğünden başka HİÇBİR YERE dokunma.**

```python
"YIL_LIMIT":     None,   # → örn. 3  : yalnız ilk 3 yıl dilimini koş
"PANEL_CARPANI": 2,      # → 1       : paneli üst-250'ye indir (tampon kalkar, bkz. uyarı)
"PARCA":         50,     # → 25      : history çağrılarında daha küçük parçalar
```

> `PANEL_CARPANI: 1` yaparsan **tampon kalkar**: üst-250'den geçici olarak düşen isimlerin
> yuvarlanan ve ileri pencereleri kırılır, süreklilik bekçisi o hücreleri kapatır ve
> örneklem daralır. Sayı üretir ama **daha gürültülüdür** — son çare.

Daraltılmış koşum JSON'a **kendini yazar** (`anahtarlar` + `tanim_sapmalari`), Rol-1 farkı
görür. **Daraltılmış koşum kart hükmünü taşımaz** — tanısaldır.

> Pencere (`PENCERE_BAS`/`PENCERE_SON`), `EVREN_N`, `UST_PCT`, `UFUKLAR`, `BLOK`, `BOOT`,
> `TOHUM`, `MALIYET_BPS`, `PK_CIVI`, `PK_MERTEBE` **kartın beyanıdır — DEĞİŞTİRME.**

---

## 4. PK-DUR hâlinde ne yapılacak

Defterin içinde kartın emrettiği bir **pozitif kontrol kapısı** vardır (H5): `rvol20`'nin
20 günlük ileri getiriyle Spearman IC'si, yerel çivi ≈0,064'ün **işaret ve mertebesinde**
(0,0128 – 0,32 bandı) çıkmalıdır. Tutmazsa defter şunu basar:

```
PK-DUR: DEFTER DURDU. Son hücreyi (H11) yine de koş — ...
```

**Yapılacak:**

1. **Panik yok, tekrar tekrar koşma.** Bu bir "kill" değil; "boru hattı geçersiz" demektir.
2. Tek hücre olarak koştuysan **JSON zaten en sonda basılmıştır** (H11 DUR hâlinde de koşar).
   Hücrelere böldüysen son hücreyi ayrıca koş.
3. **O JSON'u ve konsolun son ekranını ilet.** Rol-1 nedene bakar:
   - IC pozitif ama çok küçük/çok büyük → evren ya da tanım sapması
   - IC negatif → veri yönü/tarih hizası sorunu
   - `ic: null` → kesit kurulamadı (`n`, `n_gun` bunu söyler)
4. **Kartın eşiklerine, defterin sabitlerine ya da PK bandına DOKUNMA.** Eşik sonradan
   değişmez. Düzeltme gerekirse Rol-1 yeni bir defter sürümü verir.

Aynısı **`shares_outstanding` alınamadığında** geçerlidir: defter `DUR` yazar, `olculemedi`
alanına nedeni koyar ve **uydurma vekil üretmez** (kartın `kill_criteria` maddesi).

---

## 5. Fiyat çapraz-kontrolü (H3) — koşumun pahalı olabilen tek dalı

Panelin fiyat serisinin ileri getiri için yeterli olup olmadığı **varsayılmaz, ÖLÇÜLÜR**.
Defter en çok satırı olan 6 sembol için `qb.history` düzeltilmiş kapanışı çeker ve **günlük
getirileri** karşılaştırır (seviyeleri değil — `history` geri-düzeltmelidir, seviye çarpanı
zaten farklıdır). İki kapı vardır:

- küçük farkların **oranı** `CAPRAZ_MAKS_ORAN`(0,005) altında kalmalı (temettü/yuvarlama), **ve**
- `CAPRAZ_BUYUK_TOL`(0,02) üstü **tek bir fark bile olmamalı** — bölünme seyrektir (sembol
  başına bir gün) ve orana asla takılmaz, ama tek bir bölünme ileri getiriyi kırar.

Konsolda şunu görürsün:

```
çapraz-kontrol · en iyi kayma=0 · n=9366 · sapan_oran=0.00000 · büyük sapan=0 (maks 0.0000) → panel yeter=True
```

- **`panel yeter=True`** → ek çağrı yok, koşum hızlı biter.
- **`panel yeter=False`** → panel fiyatı bölünme düzeltmesi taşımıyor demektir; defter
  **otomatik olarak** tüm evren için `qb.history` düzeltilmiş kapanışı çeker (`history
  tamiri k/N parça` basar), `tanim_sapmalari`na yazar ve ölçüme devam eder. **Bu normaldir,
  müdahale etme** — yalnız koşum uzar.
- **`en iyi kayma` 0 değilse** panel zaman indeksi ile bar seansı arasında kayma ölçülmüş
  demektir. Tek başına ölçümü bozmaz (öznitelik de ileri getiri de aynı indeksten kurulur,
  sinyal o kadar gecikmeli okunmuş olur) ve beyan edilir. Ama **kayma VE yetersiz fiyat**
  birlikte çıkarsa defter DUR der — o birleşim bu defterde tanımlı değildir.

---

## 6. Hata alırsan (çökme)

- Hata metninin **tamamını** ilet.
- `exec(...)` ile tek hücrede koştuysan çekirdek durumu korunur; hücreyi yeniden koşmak
  baştan başlatır (`S` sıfırlanır). Uzun bir H2'den sonra çökme olduysa hücrelere bölerek
  koşmak zaman kazandırır.
- `FileNotFoundError: qc_defter_021.py` → dosya notebook ile aynı klasörde değil.

---

## 7. Bu defterin API'si SAVUNMALI DEĞİL, ÖLÇÜLMÜŞ — beyan

v1'de her QC çağrısı bir "adlar merdiveni" üzerinden yapılıyordu, çünkü defteri yazan ajan
LEAN'in Python yüzeyini doğrulayamıyordu. **Artık doğrulandı**: Rol-1 tarayıcı oturumunda
canlı QuantBook'ta sonda koştu (`QC_API_ZEMIN_GERCEGI.md`). v2 ölçülen adları **doğrudan**
kullanır; merdiven ölü koddu ve karakter yiyordu.

Defterin **ölçüme dayanan** varsayımları:

| nokta | dayanak |
|---|---|
| `qb.universe_history(u, t0, t1)` → `Series`, değer `list[Fundamental]` | ölçüldü |
| `Fundamental.dollar_volume / volume / price / market_cap` | ölçüldü |
| `Fundamental.company_profile.shares_outstanding` | ölçüldü |
| `Fundamental.earning_reports.basic_average_shares.value` | ölçüldü |
| `qb.history(sembol, …, Resolution.DAILY)` → ohlc DataFrame | ölçüldü |
| `qb.universe.etf("SPY")` + `universe_history` | ölçüldü |

Defterin **koşumda kendisi ölçtüğü** (varsayılmayan) şeyler:

| nokta | nasıl ölçülür |
|---|---|
| `adjusted_price` / `price_factor` / `split_factor` alanları var mı | H2 **alan sondası** → `kosum.fundamental_alan_sondasi` |
| panel fiyatı bölünme düzeltmeli mi | H3 çapraz-kontrolü (§5) |
| panel zamanı ile bar seansı arasında kayma var mı | H3 kayma taraması (k = 0, 1, 2, −1) |
| `universe_history` seçiciyi uyguluyor mu | `panel_muhasebesi.dilim_muhasebesi.n_ham_medyan` |

**Doğrulanamayan iki QC bilgisi (JSON'da beyan olarak durur):**

1. **Delist tespiti.** QC'nin map-file / `Delisting` olayına erişim yolu ölçülmedi; defter
   **çıkış vekili** kullanır: sembolün son panel günü panel sonundan erken bitiyor **ve** o
   gün dolar-hacim rütbesi üst-250 içindeyse "sonradan-delist" sayılır (rütbe şartı,
   kuyrukta solarak evrenden düşenleri eler). Bu vekil gerçek delist'i veri kesintisinden
   ya da ani likidite çöküşünden **kesin ayıramaz**; her koşumda `tanim_sapmalari`na yazılır.
2. **As-of teslim.** QC evren verisinin gün-gün (point-in-time) teslim edildiği QC'nin
   belgelediği bir özelliktir; bu defter onu bağımsız doğrulamadı (`as_of_beyani`).

---

## 8. Defterin kendi güvenceleri

- **Deterministik**: sabit tohum; H1b kendi kendini sınar (`determinizm_sinamasi: true`).
- **Dış bağımlılıksız**: repo'dan hiçbir şey import etmez; bootstrap ve Spearman kopyaları
  defterin içindedir.
- **Eşik içermez**: JSON'da `SUCCESS`/`KILL`/`anlamlı` diye alan YOKTUR. Tek `GECTI` alanı
  kartın emrettiği PK kapısıdır. Hüküm Rol-1'dedir.
- **Uydurma yasağı**: ölçülemeyen her şey `null` + `neden`. Bayatlık (200 gün), fiziksel
  devir (>1,0) ve **süreklilik** (pencere takvimde k×2 günü aşamaz) bekçileri kapattıkları
  hücreyi **sayar**.
- **Yerel sınama**: defter, ölçülen API şekline göre kurulmuş sahte QC ortamında dört
  senaryoda uçtan uca koşturuldu (mutlu yol · hisse hiçbir yoldan gelmiyor → ölçülemedi+DUR ·
  PK düşük → H6+ koşmuyor · ham fiyat → çapraz-kontrol tamiri tetikleniyor).
