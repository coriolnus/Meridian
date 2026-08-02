# EDG-2026-021 · QC doğrulama defteri — ÇIKTI ŞEMASI (`sonuc_021.json`)

Kart: `research/cards/EDG-2026-021-qc-delist-dogrulama.yaml`
Defter: `research/qc_dogrulama/qc_defter_021.py` (H11 tek JSON bloğu basar)
Kaydedilecek yer: `research/olcumler/qc_dogrulama/sonuc_021.json`

## 0. Sözleşme

- **Bu JSON'da HÜKÜM YOKTUR.** `SUCCESS`, `KILL`, `anlamlı`, `hüküm_önerisi` gibi alanlar
  BİLEREK yoktur. Defter sayı üretir; kartın `success_metric` ve `kill_criteria`
  maddelerini Rol-1 işler.
- Tek istisna `pozitif_kontrol.GECTI`: kartın `guards` maddesinin AÇIKÇA emrettiği boru
  hattı kapısıdır (hüküm eşiği değil). Kapı tutmazsa `DUR` dolar ve ölçüm blokları `null`
  gelir — bu bir "kill" değil, "ölçüm koşmadı"dır.
- **Ölçülemeyen her şey `null` + `neden`.** Hiçbir alan varsayılanla doldurulmaz.
- Yüzde DEĞİL, ORAN: `0.00648` = %0,648. (EDG-016 raporu yüzde yazıyordu; burada oran.)

## 1. Üst düzey alanlar

| alan | tip | anlamı |
|---|---|---|
| `kart` | str | `"EDG-2026-021"` |
| `aile` | str | `"qc_delist_dogrulama"` |
| `defter_surumu` | str | defterin sürümü (`"1.0"`) |
| `defter_sha256` | null | yapıştırılan defter kendi kaynağını okuyamaz; repo dosyasının sha'sı hüküm yazılırken repo tarafında alınır (`defter_sha256_neden` bunu söyler) |
| `rol` | str | "sayı üretir, hüküm vermez" beyanı |
| `kosum` | obj | → §2 |
| `anahtarlar` | obj | H0'daki `ANAHTAR` sözlüğünün KOŞUMDA KULLANILAN hâli → §3 |
| `DUR` | str \| null | doluysa defter erken durdu; metin nedeni taşır |
| `pozitif_kontrol` | obj | → §4 |
| `evren` | obj | → §5 |
| `tanimlar` | obj | ölçülen büyüklüklerin sözlü tanımları + `K_beyani` |
| `tanim_sapmalari` | liste | → §6 · **hüküm okunurken İLK bakılacak yer** |
| `olcum` | obj | → §7 · kartın TEK kayıtlı hücresi |
| `maliyet` | obj | → §8 |
| `alt_donem_betimleyici` | obj | → §9 (CI YOK) |
| `delist_muhasebesi` | obj | → §10 (CI YOK) |
| `kiyas_notu` | obj | EDG-016 sayıları, yan yana okumak için taşındı (BURADA HESAPLANMADI) |
| `uyarilar` | liste[str] | koşum sırasında biriken uyarılar |
| `olculemedi` | liste[obj] | `{alan, neden}` — ölçülemeyenlerin muhasebesi |

## 2. `kosum`

```
{ "zaman_utc": str, "ortam": "QuantConnect Research (QuantBook)",
  "api_yolu": { ... hangi QC-API adı işledi ... },
  "determinizm_sinamasi": bool,      # aynı girdi → aynı CI (H1b kendi kendini sınar)
  "bellek_mb": { "H3_barlar": float, "H4_oznitelikli": float, "H6_turnoverli": float } }
```

`api_yolu` alanı savunmalı keşfin kaydıdır: `import`, `quantbook`, `tarih_baglami`,
`Resolution.Daily`, `DataNormalizationMode`, `evren`, `evren_cagri`, `history_adjusted`,
`history_raw`, `shares`, (varsa) `dolar_hacim_vekili`, `add_universe`.
**Hüküm yazılırken buraya bakılır**: hangi yolun işlediği, sayının ne olduğunu belirler.

## 3. `anahtarlar`

H0'daki tüm sabitler. Hükümde kritik olanlar:

- `PENCERE_BAS` / `PENCERE_SON` — kart penceresi `2020-08-01` → `2026-07-28`.
- `EVREN_N` (250), `UST_PCT` (0.20), `UFUKLAR` (10, 20).
- `BLOK` 21 · `BOOT` 2000 · `BOOT_IC` 600 · `TOHUM` 20260801 · `MIN_KESIT` 50 · `MIN_DILIM` 30.
- `MALIYET_BPS` 10.0 · `MALIYET_BPS_DUYARLILIK` 20.0.
- **`MAKS_SEMBOL` / `AY_LIMIT` null DEĞİLSE koşum DARALTILMIŞTIR** ve kart penceresinin
  tamamı ölçülmemiştir. Bu durumda `tanim_sapmalari`na da bir kayıt düşer.

## 4. `pozitif_kontrol`

```
{ "tanim": str, "olcum": str, "yerel_civi": 0.064, "mertebe_carpani": 5.0,
  "beyan": str, "n": int, "n_gun": int,
  "ic": float|null,                 # havuzlanmış Spearman(rvol20, fwd20)
  "ic_10_tani": float|null,         # @10 okuması (TANI, kapı değil)
  "ci": { "lo": float|null, "hi": ..., "n_gun": int, "blok": 21, "B": 600,
          "B_gecerli": int, "sifir_disinda": bool, "neden": str|null },
  "bant": [alt, ust],               # [civi/5, civi*5]
  "GECTI": bool|null, "neden": str|null }
```

`GECTI=false` → `DUR` dolar, `olcum`/`maliyet`/`alt_donem`/`delist_muhasebesi` `null` gelir.
`ic` HER HÂLDE raporlanır (kapı geçmese de) — ham sayı Rol-1'in elinde olsun diye.

## 5. `evren`

```
{ "beyan": str,                       # aylık dolar-hacim üst-N, delist DAHİL
  "spx_uyelik_denemesi": { "denendi": true, "basarili": bool, "yol": str|null,
                           "n_spx": int?, "n_kesisim": int?, "neden": str|null,
                           "karar": str },
  "ay_muhasebesi": [ {"ay": "YYYY-MM-DD", "n_ham": int, "n_aday": int,
                      "n_secilen": int, "neden": str|null}, ... ],
  "bar_muhasebesi": { "istenen_sembol": int, "bar_donen_sembol": int, "satir": int,
                      "tarih_araligi": [str, str], "ham_hacim_dolu_satir": int,
                      "hacim_bazi": str },
  "kesit_muhasebesi": { "gozlem_gunu_toplam": int, "kesit_yeterli_gun": int,
                        "min_kesit": 50, "kesit_buyuklugu": {...},
                        "tarih_araligi": [...], "n_satir": int, "n_sembol": int,
                        "turnover21_dagilimi": {...}, "dilim_satir": int,
                        "dilim_sembol": int },
  "shares_muhasebesi": { "yol": str, "shares_kayit_satir": int,
                         "shares_dolu_hucre": int, "bayatlik_bekcisi_kapatti": int,
                         "bayatlik_esik_gun": 200, "fiziksel_bekci_kapatti": int,
                         "turnover21_dolu_hucre": int, "as_of_beyani": str } }
```

`spx_uyelik_denemesi.basarili=false` → süzgeç-vekili kullanıldı (kartın izin verdiği yol);
`tanim_sapmalari`nda karşılığı vardır.

`bayatlik_bekcisi_kapatti` ve `fiziksel_bekci_kapatti`, EDG-016'nın SCHW ve
"implied devir > 1" bekçilerinin QC karşılıklarıdır (kapatılan hücre = None + neden).

## 6. `tanim_sapmalari` — **hükümde İLK OKUNACAK BLOK**

```
[ { "alan": str, "kullanilan": str, "neden": str }, ... ]
```

Beklenebilecek kayıtlar:

| `alan` | ne zaman doğar | hükme etkisi |
|---|---|---|
| `large_cap_suzgeci` | SPX/ETF üyeliği alınamadı | evren SPX değil, dolar-hacim üst-N vekilidir |
| `dolar_hacim` | `DollarVolume` alanı yok → fiyat×hacim | süzgecin kendisi vekil |
| `turnover_hacim_bazi` | Raw hacim çağrısı işlemedi | turnover bölünme tarihlerinde sapabilir |
| `shares_outstanding` | 1./2. yol yok, 3./4. vekil kullanıldı | **kartın `features_asof` alanından sapma — ağır** |
| `delist_tespiti` | HER KOŞUMDA doğar (son-bar vekili) | delist ayrımı vekildir, veri kesintisiyle karışabilir |
| `evren_birlesimi` / `evren_aylari` | `MAKS_SEMBOL` / `AY_LIMIT` daraltıldı | **koşum kart penceresinin tamamı değildir** |

Boş liste beklenmemelidir: `delist_tespiti` sapması tasarım gereği her koşumda vardır.

## 7. `olcum` — kartın TEK kayıtlı hücresi (K+=1)

```
"olcum": { "ust20_evren_fazlasi": { "10": {...}, "20": {...} } }
```

Her ufuk için:

| alan | anlam |
|---|---|
| `tanim` | dilim + taban tanımı (metin) |
| `n_sembol_gun`, `n_gun`, `n_sembol` | örneklem muhasebesi |
| `dilim_turnover21_medyan` | dilimin turnover medyanı (betimleyici) |
| `ham_getiri` | dilimin HAM ileri getirisi + CI (blok bootstrap çıktısı) |
| **`evren_fazlasi`** | **HEADLINE** — dilim getirisi − aynı-gün evren ortalaması + CI |
| `evren_fazlasi_ikincil_gun_serisi_CI` | aynı büyüklüğün GÜN-AĞIRLIKLI ikincil okuması (kanonik `blok_bootstrap_ci`, tohum 11) |
| `taban_ort` | aynı-gün evren ortalamasının ortalaması |

`evren_fazlasi` (ve `ham_getiri`) blok bootstrap sözleşmesi:

```
{ "n": int, "n_gun": int, "ort": float|null, "medyan": float, "std": float,
  "pozitif_oran": float, "lo": float|null, "hi": float|null, "seviye": 0.95,
  "sifir_disinda": bool|null,        # ARİTMETİK: aralık 0'ı kapsıyor mu — HÜKÜM DEĞİL
  "blok": 21, "B": 2000, "B_gecerli": int, "atlanan": int, "tohum": int,
  "n_sayi_olmayan_dusen": int, "yontem": str, "beyan": str, "neden": str|null }
```

`evren_fazlasi_ikincil_gun_serisi_CI` şeması `meridian/olcum_araclari.py::blok_bootstrap_ci`
ile birebirdir (`ort/lo/hi/seviye/n/blok/blok_kaynagi/B/iid/sifiri_disliyor/n_cozulemeyen/
tohum/yontem/neden/beyan/uyari`). **İki CI'nın istatistiği farklıdır** (satır-ağırlıklı vs
gün-ağırlıklı); HEADLINE `evren_fazlasi`dır, çünkü EDG-016'nın CI'sı o şemayla üretildi.

**Kartın `success_metric`i `@20` `evren_fazlasi` üzerinden okunur.**

## 8. `maliyet`

```
{ "10": { "kart_modeli_10bps": {...}, "duyarlilik_20bps": {...} }, "20": { ... } }
```

Her satır: `{ "bps": float, "brut": float|null, "net": float|null,
`"net_ci": {"lo","hi","seviye","sifir_disinda"}|null, "beyan": str }`.

Maliyet SABİTTİR → CI aynı sabitle ötelenir, bootstrap yeniden koşulmaz (cebirsel özdeş;
EDG-016 ile aynı okuma). Kart modeli 10bps tek-yön; 20bps beyanlı duyarlılıktır.

## 9. `alt_donem_betimleyici` — **CI YOK**

```
{ "beyan": str, "ufuklar": { "10": { "2020": {...}, ..., "2026": {...} }, "20": {...} } }
```

Yıl hücresi: `{ "n", "n_gun", "fazla_ort", "fazla_medyan", "pozitif_oran" }`.

Kart `parameter_grid`'inde alt-dönem bacağı YOKTUR; CI **bilerek** hesaplanmadı (CI'lı
sınansaydı K çarpılırdı). Bu tablo hüküm bacağı değildir — EDG-016'nın Ç2 çekincesine
bilgi sağlar.

## 10. `delist_muhasebesi` — **CI YOK** (kartın survivorship sorusu burada görünür)

Üst düzey sayaçlar:

| alan | anlam |
|---|---|
| `yontem` | delist-vekilinin tam tanımı (son-bar kuralı) |
| `beyan` | "betimleyici, CI yok, hüküm bacağı değil" |
| `evren_birlesim_sembol`, `bar_donen_sembol` | evren büyüklüğü |
| `delist_vekili_sembol`, `delist_vekili_pay` | kaç isim sonradan delist |
| `kesit_delist_satir` / `kesit_satir` | kesitte delist isimlerinin payı |
| `dilim_delist_satir` / `dilim_satir` / `dilim_delist_sembol` | DİLİMDE delist payı |
| `delist_fwd_olculemeyen_satir` | delist yüzünden ileri getirisi hiç ölçülemeyen satır sayısı (ufuk bazında) |
| `delist_dilime_yogunlasiyor_mu` | `{dilimdeki_delist_payi, kesitteki_delist_payi, okuma}` |

Ufuk bazında ayrıştırma (`ufuklar["10"]`, `ufuklar["20"]`):

```
{ "tum":                     {n, n_sembol, ort, medyan, pozitif_oran},
  "yalniz_hayatta_kalanlar": {...},     # EDG-016'nın gördüğü dünyanın karşılığı
  "yalniz_sonradan_delist":  {...},     # EDG-016'nın HİÇ göremediği kuyruk
  "survivorship_primi_vekili": float|null,   # hayatta_kalanlar.ort − tum.ort
  "okuma": str,
  "duyarlilik_delist_son_fiyattan_tasfiye": { "n": int, "ort": float|null, "beyan": str } }
```

`survivorship_primi_vekili > 0` → delist isimleri dilimin fazlasını AŞAĞI çekiyor demektir,
yani sağkalan-evrende ölçülen sayı yukarı çarpıktı. **Bu bir sayıdır; yorum Rol-1'de.**

`duyarlilik_delist_son_fiyattan_tasfiye`: delist ismin son h gününde bar olmadığı için ileri
getiri ölçülemez ve o satırlar HEADLINE'dan düşer — bu, delist-dahil evrende bile kalan bir
sınırdır. Bu satır o boşluğu "son kapanıştan tasfiye" VARSAYIMIYLA doldurur; CI yoktur ve
hüküm bacağı değildir.

## 11. `kiyas_notu`

EDG-016'nın sayıları (`@10 +0.0031`, `@20 +0.00648`, `net10bps@20 +0.00548`) kolaylık için
taşındı. **Bu defter onları HESAPLAMADI.** İki ölçüm farklı evrende yapıldı; fark yalnız
survivorship'e atfedilemez — `tanim_sapmalari` birlikte okunmalıdır.
