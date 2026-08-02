# EDG-2026-021 · QC doğrulama defteri — ÇIKTI ŞEMASI (`sonuc_021.json`) · defter v3.0

Kart: `research/cards/EDG-2026-021-qc-delist-dogrulama.yaml`
Defter: **üç parça** — `qc_defter_021_a.py` · `_b.py` · `_c.py` (H11/JSON `_c`'dedir)

```python
for _p in ("a", "b", "c"):
    exec(open(f"qc_defter_021_{_p}.py").read(), globals())
```

`globals()` ŞART (parçalar tek `S` durumunu paylaşır). Sıra a → b → c; `_b`/`_c` önceki
parça yüklenmediyse hata verir. **`_c` DUR hâlinde de koşturulmalıdır** — JSON'u o basar.
Kaydedilecek yer: `research/olcumler/qc_dogrulama/sonuc_021.json`
Zemin gerçeği: `research/qc_dogrulama/QC_API_ZEMIN_GERCEGI.md`

> **Bu doküman defterin uzun gerekçesini de taşır.** QC dosya başına 64.000 karakter sınırı
> koyduğu için defterin içindeki açıklamalar tek cümleye indirildi; her `beyan`/`neden`
> alanının **tam gerekçesi burada** durur. Hüküm yazılırken ikisi birlikte okunur.

## 0. Sözleşme

- **Bu JSON'da HÜKÜM YOKTUR.** `SUCCESS`, `KILL`, `anlamlı`, `hüküm_önerisi` gibi alanlar
  BİLEREK yoktur. Defter sayı üretir; kartın `success_metric` ve `kill_criteria`
  maddelerini Rol-1 işler. (Yerel sınamada dört senaryoda da bu kelimelerin JSON'da
  geçmediği makine ile doğrulandı.)
- Tek istisna `pozitif_kontrol.GECTI`: kartın `guards` maddesinin AÇIKÇA emrettiği boru
  hattı kapısıdır (hüküm eşiği değil). Kapı tutmazsa `DUR` dolar ve ölçüm blokları `null`
  gelir — bu bir "kill" değil, "ölçüm koşmadı"dır.
- **Ölçülemeyen her şey `null` + `neden`.** Hiçbir alan varsayılanla doldurulmaz.
- Yüzde DEĞİL, ORAN: `0.00648` = %0,648.

## 0a. v2 → v3: TAZE-QB KURALI (canlı arızanın kök nedeni)

v2 canlıda H2'de DUR dedi ("hiçbir yıl diliminde satır dönmedi"). Kök neden **ölçüldü**
(`QC_API_ZEMIN_GERCEGI.md` → "EK ÖLÇÜM"): hata `universe_history` API'sinde değil,
**QuantBook örneğinin durumunda**. Defterin H1'de kurduğu `qb` (üzerinde
`set_start_date`/`set_end_date` çağrılmıştı) 0 satır döndürürken, **aynı hücrede** taze bir
`QuantBook()` + taze `add_universe` aynı pencerede 9 satır döndürdü.

**v3'ün kuralı: QuantBook örneği AMAÇ BAŞINA ayrıdır ve PAYLAŞILMAZ.**

| örnek | nerede kurulur | yalnız ne için |
|---|---|---|
| `QB_BAR` | H1 | `qb.history` bar çağrıları (H3 çapraz-kontrol + tamir) |
| `QB_PANEL` | H2, **taze** | `universe_history` (panel). Üzerinde başka çağrı YOK |
| `QB_SPX` | H2b, **taze** | SPX/ETF tanısı (`add_equity` örneği kirletir) |

Ayrıca `set_start_date`/`set_end_date` **bilerek çağrılmaz** (örnek durumunu değiştiriyor;
semboller `Fundamental`dan geldiği için ticker çözümüne gerek yok). `kosum.api_yolu`
içindeki `tarih_baglami` alanı bunu beyan eder.

**KENDİNİ-DOĞRULAYAN AÇILIŞ (`evren.mini_sonda`).** H2, 7 yıllık panel çekiminden ÖNCE aynı
örnek ve aynı seçiciyle `SONDA_GUN` (10) günlük bir mini-sonda koşar:

```
{ "pencere_gun": 10, "n_kayit": int|null, "neden": str|null, "beyan": str }
```

`n_kayit` 0/`null` ise defter **HEMEN DUR** der ve 7 yıllık boş çekimi hiç koşturmaz. DUR
metni: *"QuantBook örneği evren döndürmüyor — taze örnek kuralı ihlal/etkisiz"* + kontrol
listesi (QB_PANEL taze mi, üzerinde `add_equity`/`set_start_date` çağrıldı mı, seçici Symbol
listesi döndürüyor mu). **Hüküm okunurken `mini_sonda.n_kayit` ilk bakılacak sayılardandır:**
doluysa evren yolu canlıda çalışmış demektir.

## 0b. v1 → v2 mimari değişikliği (şemayı okurken bilinmesi gerekir)

v1 koşumu H2'de DUR dedi: FREE hesapta `history(Fundamental)` / `history(CoarseFundamental)`
**boş DataFrame** döndürüyor (ölçüldü). v2 **tek kaynağa** geçti:

```python
u = qb.add_universe(secici); seri = qb.universe_history(u, t0, t1)
# → Series · MultiIndex(evren-sembolü, zaman) · her değer list[Fundamental]
```

Evren seçimi, fiyat, hacim ve **as-of hisse sayısı** aynı çağrıdan gelir.

**Şemadan KALKAN alanlar (v1'de vardı):** `evren.ay_muhasebesi`, `evren.bar_muhasebesi`,
`kosum.api_yolu` içindeki merdiven kayıtları (`history_adjusted`, `history_raw`, `shares`,
`dolar_hacim_vekili`, `evren_cagri`, `DataNormalizationMode`), `pozitif_kontrol.ic_10_tani`,
`tanimlar.mom21`, `tanimlar.hacim_bazi`, `olcum.*.evren_fazlasi_ikincil_gun_serisi_CI`.

**v3'te GELEN alanlar:** `evren.mini_sonda`, `kosum.api_yolu.{qb_bar,qb_panel}`,
`evren.spx_uyelik_denemesi.qb`.

**v2'de GELEN alanlar:** `defter_mimarisi`, `kosum.fundamental_alan_sondasi`,
`evren.panel_muhasebesi`, **`fiyat_capraz_kontrol`** (yeni üst düzey blok),
`tanimlar.px_kaynagi`, `tanimlar.sureklilik_bekcisi`,
`olcum.*.evren_fazlasi_gun_agirlikli_CI`, `delist_muhasebesi.cikis_muhasebesi`,
`delist_muhasebesi.span_bekcisi_kapatti`.

## 1. Üst düzey alanlar

| alan | tip | anlamı |
|---|---|---|
| `kart` / `aile` | str | `"EDG-2026-021"` / `"qc_delist_dogrulama"` |
| `defter_surumu` | str | `"3.0"` |
| `defter_mimarisi` | str | tek-kaynak beyanı + v1'in ölü yollarının neden çıkarıldığı |
| `defter_sha256` | null | koşan defter kendi kaynağını okumaz; sha REPO tarafında alınır |
| `rol` | str | "sayı üretir, hüküm vermez" beyanı |
| `kosum` | obj | → §2 |
| `anahtarlar` | obj | H0'daki `ANAHTAR`ın KOŞUMDA KULLANILAN hâli → §3 |
| `DUR` | str \| null | doluysa defter erken durdu; metin nedeni taşır |
| `pozitif_kontrol` | obj | → §4 |
| `evren` | obj | → §5 (`mini_sonda` dahil) |
| `fiyat_capraz_kontrol` | obj | → §6 |
| `tanimlar` | obj | ölçülen büyüklüklerin sözlü tanımları + `K_beyani` |
| `tanim_sapmalari` | liste | → §7 · **hüküm okunurken İLK bakılacak yer** |
| `olcum` | obj | → §8 · kartın TEK kayıtlı hücresi |
| `maliyet` | obj | → §9 |
| `alt_donem_betimleyici` | obj | → §10 (CI YOK) |
| `delist_muhasebesi` | obj | → §11 (CI YOK) |
| `kiyas_notu` | obj | EDG-016 sayıları, yan yana okumak için taşındı (BURADA HESAPLANMADI) |
| `uyarilar` | liste[str] | koşum sırasında biriken uyarılar |
| `olculemedi` | liste[obj] | `{alan, neden}` |

## 2. `kosum`

```
{ "zaman_utc": str, "ortam": "QuantConnect Research (QuantBook)",
  "api_yolu": {"import","Resolution","qb_bar","tarih_baglami","evren","qb_panel"},
  "fundamental_alan_sondasi": { ... },      # ← YENİ, aşağıya bak
  "determinizm_sinamasi": bool,             # aynı girdi → aynı CI (H1b kendini sınar)
  "bellek_mb": {"H4_oznitelikli": float, "H6_turnoverli": float} }
```

**`fundamental_alan_sondasi` — v2'nin en önemli tanı alanı.** Defter, ilk `Fundamental`
üyesinde 13 alan yolunu **tek tek yoklar** ve sonucu buraya yazar. Değer varsa sayı/metin,
yoksa `"<yok: AttributeError>"`. Yoklanan yollar:

`price` · `value` · `adjusted_price` · `price_factor` · `split_factor` ·
`price_scale_factor` · `dollar_volume` · `volume` · `market_cap` · `has_fundamental_data` ·
`company_profile.shares_outstanding` · `earning_reports.basic_average_shares.value` ·
`security_reference.exchange_id`

**Neden önemli:** panelin fiyat alanı bu sondaya göre seçilir. `adjusted_price` **var ve
pozitif** ise panel onu kullanır (`panel_muhasebesi.fiyat_alani = "adjusted_price"`),
yoksa `price` (ham olabilir) kullanılır ve karar §6'daki çapraz-kontrole devredilir.
Bu bir VARSAYIM DEĞİL, koşum anında yapılan bir ÖLÇÜMDÜR.

## 3. `anahtarlar`

Hükümde kritik olanlar:

- `PENCERE_BAS`/`PENCERE_SON` = `2020-08-01` → `2026-07-28`; `EVREN_N` 250; `UST_PCT` 0.20;
  `UFUKLAR` (10, 20).
- `BLOK` 21 · `BOOT` 2000 · `BOOT_IC` 600 · `TOHUM` 20260801 · `MIN_KESIT` 50 · `MIN_DILIM` 30.
- `MALIYET_BPS` 10.0 · `MALIYET_BPS_DUYARLILIK` 20.0 · `PK_CIVI` 0.064 · `PK_MERTEBE` 5.0.
- **Boru hattı sabitleri (hüküm eşiği DEĞİL):** `PANEL_CARPANI` 2 · `SPAN_TOLERANS` 2.0 ·
  `SHARES_BAYAT_GUN` 200 · `TURNOVER_TAVAN` 1.0 · `CAPRAZ_SEMBOL` 6 · `CAPRAZ_TOL` 0.001 ·
  `CAPRAZ_MAKS_ORAN` 0.005 · `CAPRAZ_BUYUK_TOL` 0.02 · `DELIST_TAMPON_GUN` 10.
- **`YIL_LIMIT` null DEĞİLSE koşum DARALTILMIŞTIR** (kart penceresinin tamamı ölçülmedi);
  `tanim_sapmalari`na da kayıt düşer. `PANEL_CARPANI` 1'e indirildiyse tampon kalkmıştır →
  süreklilik bekçisi daha çok hücre kapatır, örneklem daralır.

## 4. `pozitif_kontrol`

```
{ "tanim","olcum","yerel_civi":0.064,"mertebe_carpani":5.0,"beyan","n","n_gun",
  "ic": float|null,                 # havuzlanmış Spearman(rvol20, fwd20)
  "ci": {lo,hi,seviye,n_gun,blok:21,B:600,B_gecerli,atlanan,tohum,sifir_disinda,neden},
  "bant": [civi/5, civi*5],         # [0.0128, 0.32]
  "GECTI": bool|null, "neden": str|null }
```

`GECTI=false` → `DUR` dolar; `olcum`/`maliyet`/`alt_donem_betimleyici`/`delist_muhasebesi`
`null` gelir. `ic` HER HÂLDE raporlanır — ham sayı Rol-1'in elinde olsun diye.

**Neden mertebe, nokta değil:** yerel çivi Meridian'ın karşı-olgusal katmanında ölçüldü;
buradaki kesit delist-dahil QC evrenidir. Kart "işaret/mertebe" diyor; uygulaması IC'nin
pozitif olması ve çivinin 1/5–5 katı bandında kalmasıdır. Bu bir hüküm eşiği değil, boru
hattı geçerlilik kapısıdır: tutmazsa H6–H8 (kartın kayıtlı hücresi) hiç koşmaz.

## 5. `evren`

### 5.1 `beyan` — evren tanımı ve PANEL TAMPONU

Evren **günlük** dolar-hacim üst-`EVREN_N` (250), delist DAHİL. Panel ise
üst-`EVREN_N × PANEL_CARPANI` (500) satır taşır.

**Tamponun tam gerekçesi (defterde tek cümleye indirildi):** ölçüm evreni günlük yeniden
seçildiği için 250. sıra civarındaki bir sembol günden güne listeye girip çıkar. Panel
yalnız üst-250'yi taşısaydı o sembolün satırları arasında boşluk olurdu ve satır-tabanlı
yuvarlanan pencereler (SMA20, medyan21) ile ileri getiri (t+10, t+20) **takvimde çok daha
uzun bir aralığı kaplayarak sessizce yanlış sayı üretirdi**. Tampon bu sembolleri panelde
tutar. **Tampon ölçüm evrenini GENİŞLETMEZ**: ölçüme giren satır yalnız `evren_uye`
olanlardır (gün içi dolar-hacim rütbesi ≤ 250). Tamponun yetmediği kalıntı boşlukları
süreklilik bekçisi kapatır ve `delist_muhasebesi.span_bekcisi_kapatti` altında **sayar**.

### 5.1b `mini_sonda`

Bkz. §0a. `{pencere_gun, n_kayit, neden, beyan}`. `n_kayit` boşsa `DUR` dolar, panel hiç
çekilmez ve `panel_muhasebesi` gelmez. Yerel sınamada mutlu yolda `n_kayit=490`,
evren-boş senaryosunda `0` → koşum 0,3 saniyede DUR dedi (dolu koşum 10,9 s).

### 5.2 `spx_uyelik_denemesi`

```
{ "denendi": true, "basarili": bool, "yol": str|null, "n_spx": int?,
  "n_kesisim": int?, "n_son_gun_evren": int?, "neden": str|null, "karar": str,
  "qb": "TAZE QuantBook() — QB_PANEL kirletilmesin diye ayrı örnek" }
```

Kart "birebir SPX üyeliği varsa kullanılır" diyor. v2'de bu blok **yalnız TANIDIR**: evren
her hâlükârda dolar-hacim üst-N süzgeç-vekilidir (kartın açıkça izin verdiği yol) ve
`tanim_sapmalari`nda `large_cap_suzgeci` olarak beyan edilir. `n_kesisim / n_son_gun_evren`
oranı vekilin SPX'e ne kadar yaklaştığını **ölçer** — hüküm yazılırken evren farkının
büyüklüğü buradan okunur.

### 5.3 `panel_muhasebesi` (v1'in `ay_muhasebesi` + `bar_muhasebesi` yerine)

```
{ "satir","gun","sembol","tarih_araligi":[str,str],
  "panel_ust_n": 500, "olcum_evreni_ust_n": 250, "evren_uye_satir": int,
  "gunluk_evren_buyuklugu": {"medyan","min","maks"},
  "fiyat_alani": "price"|"adjusted_price",
  "hacim_dolu_satir": int,
  "shares_kaynak_dagilimi": {"0":int,"1":int,"2":int},
  "shares_kaynak_kodlari": {"0":...,"1":...,"2":...},
  "dilim_muhasebesi": [ {"dilim":"YYYY-MM-DD/YYYY-MM-DD","n_gun","n_satir",
                         "n_ham_medyan": float|null, "neden": str|null}, ... ],
  "bellek_mb": float }
```

- **`gunluk_evren_buyuklugu.medyan` 250'nin belirgin altındaysa** o günlerde evren
  dolamamıştır (veri seyrek) — kesit muhasebesi ile birlikte okunur.
- **`dilim_muhasebesi[].n_ham_medyan`**: `universe_history`den dönen HAM liste uzunluğunun
  medyanı. **Tanısal değeri:** 500'e yakınsa QC seçiciyi uygulamış, binlerse uygulamamış ve
  kırpmayı defter yapmıştır. İkisi de doğrudur (defter üst-N'i iki yerde de kırpar), ama
  hangisinin olduğu buradan görülür.
- **`shares_kaynak_kodlari`** — as-of hisse sayısının hücre başına kaynağı:
  `0` = ölçülemedi (her iki alan da boş/0) → hücre `None`;
  `1` = `company_profile.shares_outstanding` (BİRİNCİL, nokta-zamanlı SEVİYE);
  `2` = `earning_reports.basic_average_shares.value` (VEKİL, AĞIRLIKLI ORTALAMA).
  **Kod 2'nin sayısı 0'dan büyükse** `tanim_sapmalari`na `shares_outstanding` kaydı düşer:
  EDG-016 ağırlıklı ortalama hisseyi SEVİYE olarak reddediyor, bu yüzden kod-2 payı
  büyükse turnover21 tanımı ikizden sapmış demektir. **Hükümde bu orana bakılır.**
  *(Uydurma yasağı: hücre başına ayrı `neden` dizgisi üretmek yüz binlerce satırda
  taşınamazdı; onun yerine kaynak KODLANIR ve kod sözlüğü JSON'un içinde taşınır — neden
  kaybolmaz, sıkıştırılır.)*

### 5.4 `kesit_muhasebesi`

```
{ "gozlem_gunu_toplam","kesit_yeterli_gun","min_kesit":50,
  "kesit_buyuklugu":{"medyan","min","maks"}, "tarih_araligi":[str,str],
  "n_satir","n_sembol", "turnover21_dagilimi":{"0.01","0.25","0.5","0.75","0.99"},
  "dilim_satir","dilim_sembol" }
```

### 5.5 `shares_muhasebesi`

```
{ "kaynak": str, "shares_ham_dolu_hucre": int,
  "shares_kaynak_dagilimi": {...}, "shares_kaynak_kodlari": {...},
  "ffill_sonrasi_dolu_hucre": int,
  "bayatlik_bekcisi_kapatti": int, "bayatlik_esik_gun": 200, "bayatlik_medyan_gun": float,
  "fiziksel_bekci_kapatti": int, "fiziksel_tavan": 1.0,
  "turnover21_dolu_hucre": int, "as_of_beyani": str }
```

- **AS-OF kuralı:** yalnız İLERİ doldurma (`ffill`) — son BİLİNEN değer taşınır, geriye
  bakış YOK. `bayatlik_medyan_gun` taşınan değerin tipik yaşını verir.
- **Bayatlık bekçisi** (EDG-016'nın SCHW dersi): son bilinen kayıt 200 günden eskiyse hücre
  ÖLÇÜLEMEZ. Bekçi olmasa boşluğun başındaki hisse sayımı boşluk boyunca taşınır ve uydurma
  turnover üretirdi.
- **Fiziksel bekçi:** ima edilen 21g devir > 1,0 fiziksel olarak imkânsızdır (ölçek hatası).
- İkisi de kapattıkları hücreyi **sayar** — sessiz yutma yoktur (YASA 4).
- `shares_ham_dolu_hucre == 0` → `DUR` + `olculemedi["shares_outstanding_as_of"]`
  (kartın `kill_criteria` maddesi: uydurma vekil YASAK).
  `turnover21_dolu_hucre < MIN_DILIM` → yine `DUR` + `olculemedi["turnover21"]`.

## 6. `fiyat_capraz_kontrol` — **YENİ, v2'ye özgü**

```
{ "ornek_sembol": [str,…], "fiyat_alani": str, "tol": 0.001, "maks_oran": 0.005, "beyan": str,
  "kosuldu": bool, "neden": str?,
  "kayma_taramasi": { "0": {...}, "1": {...}, "2": {...}, "-1": {...} },
  "en_iyi_kayma": int|null, "en_iyi": {...}, "yeter": bool,
  "tamir": {"parca","basarisiz_parca","eslesmeyen_panel_satiri","beyan"}? }
```

Her tarama hücresi: `{n, sapan_oran, n_sapan_buyuk, maks_fark, fark_medyan}`.

**Soru:** panelin fiyat serisi ileri getiri için yeterli mi? İki risk ölçülür:

- **(a) Zaman kayması.** Panel indeks zamanı ile barın seansı arasında k günlük kayma
  olabilir. **Tek başına ölçümü BOZMAZ:** öznitelik de ileri getiri de aynı indeksten
  kurulur, dolayısıyla kayma varsa ölçüm bir gün gecikmeli (muhafazakâr) okunmuş olur ve
  ileri-bakış doğmaz. `en_iyi_kayma != 0` ise `tanim_sapmalari`na `panel_zaman_kaymasi`
  kaydı düşer.
- **(b) Bölünme/temettü.** Panel fiyatı hamsa bölünme günü getiriyi kırar; bu ölçümü BOZAR.

**Yöntem:** en çok satırlı 6 sembol için `qb.history` düzeltilmiş kapanış çekilir ve
**günlük GETİRİLER** karşılaştırılır — seviyeler değil, çünkü `history` geri-düzeltmelidir
ve seviye çarpanı zaten farklıdır.

**İKİ KAPI (ikisi birden sağlanmalı):**

1. `sapan_oran ≤ CAPRAZ_MAKS_ORAN` (0,005) — küçük farkların oranı (temettü/yuvarlama), **ve**
2. `n_sapan_buyuk == 0` — `CAPRAZ_BUYUK_TOL` (0,02) üstü **tek bir fark bile olmamalı**.

> İkinci kapı neden ayrı: **bölünme seyrektir** (sembol başına bir gün) ve bir orana asla
> takılmaz — 6 sembolün 9.000 karşılaştırmasında iki bölünme günü %0,02'lik bir oran verir,
> yani ilk kapıdan rahatça geçer. Ama tek bir bölünme ileri getiriyi kırar. Bu kapı yerel
> sınamada gerçekten iş gördü: ham-fiyat senaryosunda `sapan_oran=0.00021` (kapı 1 geçiyor)
> iken `n_sapan_buyuk=2, maks_fark=0.5006` (kapı 2 düşürüyor) ölçüldü.

**Karar:**

| durum | sonuç |
|---|---|
| `yeter=true` | ek çağrı YOK; `tanimlar.px_kaynagi = "panel … (çapraz-kontrol GEÇTİ)"` |
| `yeter=false` ve `en_iyi_kayma == 0` | **tamir**: tüm evren için `qb.history` düzeltilmiş kapanış çekilir, `tanim_sapmalari`na `fiyat_serisi` yazılır, `tamir` bloğu doldurulur |
| `yeter=false` ve `en_iyi_kayma != 0` | **DUR** — kaymalı birleştirme bu defterde tanımlı değil; uydurma hizalama YASAK |
| `kosuldu=false` | çapraz-kontrol çağrısı işlemedi → panel serisi DOĞRULANMADI; `olculemedi` + `tanim_sapmalari` kaydı, koşum panel fiyatıyla sürer |

`tamir.eslesmeyen_panel_satiri` > 0 ise o satırlarda `px` `None` kalır ve ileri getirisi
ÖLÇÜLEMEZ (doldurulmaz).

## 7. `tanim_sapmalari` — **hükümde İLK OKUNACAK BLOK**

```
[ { "alan": str, "kullanilan": str, "neden": str }, ... ]
```

| `alan` | ne zaman doğar | hükme etkisi |
|---|---|---|
| `large_cap_suzgeci` | **HER KOŞUMDA** | evren SPX değil, dolar-hacim üst-N vekilidir; `spx_uyelik_denemesi.n_kesisim` farkın ölçüsüdür |
| `delist_tespiti` | **HER KOŞUMDA** | delist ayrımı vekildir (bkz. §11) |
| `shares_outstanding` | kod-2 (basic_average_shares) hücresi varsa | **kartın `features_asof` alanından sapma — ağır**; EDG-016 ağırlıklı ortalamayı SEVİYE olarak reddeder |
| `fiyat_serisi` | çapraz-kontrol paneli yetersiz buldu → history tamiri; ya da kontrol hiç koşamadı | ilk hâlde ileri getiri history'den, ikincisinde panel serisi DOĞRULANMAMIŞ |
| `panel_zaman_kaymasi` | `en_iyi_kayma != 0` | ölçüm o kadar GECİKMELİ okunmuş sayılır (muhafazakâr) |
| `panel_dilimleri` | `YIL_LIMIT` daraltıldı | **koşum kart penceresinin tamamı değildir** |

Boş liste beklenmemelidir: `large_cap_suzgeci` ve `delist_tespiti` tasarım gereği her
koşumda vardır (yerel sınamada mutlu yolda 2, tamir yolunda 3 sapma ölçüldü).

## 8. `olcum` — kartın TEK kayıtlı hücresi (K+=1)

```
"olcum": { "ust20_evren_fazlasi": { "10": {...}, "20": {...} } }
```

| alan | anlam |
|---|---|
| `tanim` | dilim + taban tanımı (metin) |
| `n_sembol_gun`, `n_gun`, `n_sembol` | örneklem muhasebesi |
| `dilim_turnover21_medyan` | dilimin turnover medyanı (betimleyici) |
| `ham_getiri` | dilimin HAM ileri getirisi + CI |
| **`evren_fazlasi`** | **HEADLINE** — dilim getirisi − aynı-gün evren ortalaması + CI |
| `evren_fazlasi_gun_agirlikli_CI` | aynı büyüklüğün GÜN-AĞIRLIKLI ikincil okuması |
| `taban_ort` | aynı-gün evren ortalamasının ortalaması |

Blok bootstrap sözleşmesi (`ham_getiri`, `evren_fazlasi`, `evren_fazlasi_gun_agirlikli_CI`):

```
{ "n","n_gun","ort":float|null,"medyan","std","pozitif_oran",
  "lo":float|null,"hi":float|null,"seviye":0.95,
  "sifir_disinda": bool|null,        # ARİTMETİK: aralık 0'ı kapsıyor mu — HÜKÜM DEĞİL
  "blok":21,"B":2000,"B_gecerli","atlanan","tohum","n_sayi_olmayan_dusen",
  "yontem","beyan","neden": str|null }
```

**İkincil CI hakkında beyan (v1'den değişti).** v1, `meridian/olcum_araclari.py ::
blok_bootstrap_ci`nin birebir kopyasını taşıyordu. v2'de o kopya **karakter sınırı
nedeniyle çıkarıldı**; gün-ağırlıklı okuma artık AYNI gün-blok aracına gün-ortalaması
serisi verilerek üretilir (satır = gün olduğu için sonuç gün-ağırlıklıdır). **Fark:** tohum
(20260801 yerine 11 değil) ve blok kuralı (sabit 21; kanonik araç `n^(1/3)` kullanırdı,
ama v1 zaten `blok=21` geçiyordu). İstatistiğin kendisi aynı ailedendir. **HEADLINE her
hâlükârda `evren_fazlasi`dır**, çünkü EDG-016'nın CI'sı o şemayla üretildi.

**Kartın `success_metric`i `@20` `evren_fazlasi` üzerinden okunur.**

## 9. `maliyet`

```
{ "10": {"kart_modeli_10bps": {...}, "duyarlilik_20bps": {...}}, "20": {...} }
```

Her satır: `{bps, brut, net, net_ci:{lo,hi,seviye,sifir_disinda}|null, beyan}`.
Maliyet SABİTTİR → CI aynı sabitle ötelenir, bootstrap yeniden koşulmaz (cebirsel özdeş;
EDG-016 ile aynı okuma). Kart modeli 10bps tek-yön; 20bps beyanlı duyarlılıktır.

## 10. `alt_donem_betimleyici` — **CI YOK**

```
{ "beyan": str, "ufuklar": { "10": {"2020": {...}, …}, "20": {...} } }
```

Yıl hücresi: `{n, n_gun, fazla_ort, fazla_medyan, pozitif_oran}`. Kart
`parameter_grid`'inde alt-dönem bacağı YOKTUR; CI **bilerek** hesaplanmadı (CI'lı sınansaydı
K çarpılırdı). Hüküm bacağı değildir — EDG-016'nın Ç2 çekincesine bilgi sağlar.

## 11. `delist_muhasebesi` — **CI YOK** (kartın survivorship sorusu burada görünür)

| alan | anlam |
|---|---|
| `yontem` | delist-vekilinin tam tanımı |
| `beyan` | "BETİMLEYİCİ, CI yok, hüküm bacağı değil" |
| `panel_sembol` | panelde görülen ayrık sembol sayısı |
| `cikis_muhasebesi` | `{erken_cikan, yuksek_rutbe_aday, dusuk_rutbe_cikis}` |
| `delist_vekili_sembol`, `delist_vekili_pay` | kaç isim sonradan delist sayıldı |
| `kesit_delist_satir` / `kesit_satir` | kesitte delist payı |
| `dilim_delist_satir` / `dilim_satir` / `dilim_delist_sembol` | DİLİMDE delist payı |
| `delist_fwd_olculemeyen_satir` | delist yüzünden fwd'si hiç ölçülemeyen satır (ufuk bazında) |
| `span_bekcisi_kapatti` | süreklilik bekçisinin kapattığı hücreler (öznitelik bazında) |
| `delist_dilime_yogunlasiyor_mu` | `{dilimdeki_delist_payi, kesitteki_delist_payi, okuma}` |

### 11.1 Delist vekilinin tam gerekçesi (defterde tek cümle)

QC'nin map-file / `Delisting` olayına erişim yolu **ölçülmedi**, bu yüzden delist tespiti
bir VEKİLDİR. v2'nin mimarisi v1'in "son-bar vekili"ni **doğrudan kullanamaz**: v1 fiyat
tarihinden okuduğu için son bar gerçekten borsadan çıkışı gösteriyordu; v2'de satırlar
evren üyeliğine bağlı olduğundan "son panel günü" hem delist'i hem de **dolar-hacim
sıralamasından düşmeyi** gösterebilir. Bu yüzden vekile bir **ayırt edici** eklendi:

> Sembolün son panel günü panel sonundan `DELIST_TAMPON_GUN` iş gününden erken bitiyor
> **VE** o gün dolar-hacim rütbesi üst-`EVREN_N` içinde ise "sonradan-delist" sayılır.

Rütbe şartı, kuyrukta solarak evrenden düşen isimleri eler: üst-250 içindeyken bir anda
kaybolan isim delist'e, panel kuyruğunda sönerek çıkandan çok daha yakındır.
`cikis_muhasebesi.dusuk_rutbe_cikis` elenen isim sayısını verir — **bu sayı büyükse vekil
çok iş yapıyor demektir ve hükümde ona göre okunmalıdır.**

**Vekilin sınırı (beyan):** gerçek delist'i (a) veri kesintisinden, (b) ani likidite
çöküşünden kesin AYIRAMAZ. Çıkış sonrası bar araması bu sürümde **koşmuyor**.

### 11.2 Ufuk bazında ayrıştırma

```
{ "tum":                     {n, n_sembol, ort, medyan, pozitif_oran},   # kayıtlı hücre
  "yalniz_hayatta_kalanlar": {...},     # EDG-016'nın gördüğü dünyanın karşılığı
  "yalniz_sonradan_delist":  {...},     # EDG-016'nın HİÇ göremediği kuyruk
  "survivorship_primi_vekili": float|null,   # hayatta_kalanlar.ort − tum.ort
  "okuma": str,
  "duyarlilik_delist_son_fiyattan_tasfiye": {n, ort, beyan} }
```

`survivorship_primi_vekili > 0` → delist isimleri dilimin fazlasını AŞAĞI çekiyor demektir,
yani sağkalan-evrende ölçülen sayı yukarı çarpıktı. **Bu bir sayıdır; yorum Rol-1'de.**

`duyarlilik_delist_son_fiyattan_tasfiye`: delist ismin son h gününde bar olmadığı için ileri
getiri ölçülemez ve o satırlar HEADLINE'dan düşer — delist-dahil evrende bile kalan bir
sınırdır. Bu satır o boşluğu "son kapanıştan tasfiye" VARSAYIMIYLA doldurur; gerçek tasfiye
fiyatı bu defterde bilinmiyor. CI yoktur, hüküm bacağı değildir.

### 11.3 `span_bekcisi_kapatti` nasıl okunur

`{rvol20_span_kapatti, med_hacim21_span_kapatti, fwd10_span_kapatti, fwd20_span_kapatti}`.
Süreklilik bekçisi, satır-tabanlı bir pencerenin takvimde `k × SPAN_TOLERANS` günü aşması
hâlinde hücreyi ÖLÇÜLEMEZ yapar (panelden düşüp dönen sembolün penceresi sessizce
uzamasın diye). **Sayılar büyükse** panel tamponu yetmemiş, örneklem daralmış demektir —
`PANEL_CARPANI` ile birlikte okunur.

## 12. `kiyas_notu`

EDG-016'nın sayıları (`@10 +0.0031`, `@20 +0.00648`, `net10bps@20 +0.00548`) kolaylık için
taşındı. **Bu defter onları HESAPLAMADI.** İki ölçüm farklı evrende yapıldı; fark yalnız
survivorship'e atfedilemez — `tanim_sapmalari` birlikte okunmalıdır.
