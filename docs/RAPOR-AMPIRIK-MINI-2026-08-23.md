# RAPOR — `ampirik_*` alanları: n / tazelik / debi (mini-ölçüm, 2026-08-23)

**Kalem:** operatör E-kod partisi [6]. **Tür:** SALT-OKUMA canlı ölçüm. **HÜKÜM YOK** — bu belge
bir karar önermez; yalnız üç soruyu sayıyla cevaplar: *kaç tane var, ne kadar taze, hangi hızda
doluyor?* Eşik değiştirme, band açma/kapatma ve `goal.yaml` yazımı bu belgenin KAPSAMI DIŞINDADIR
(değişmez-dosya sözleşmesi: `ampirik_bps` alanını doldurmak OPERATÖR eylemidir).

## 0. Ölçümün künyesi

| | |
|---|---|
| Kaynak | A1 canlı (`ubuntu@130.61.126.87`), `/opt/meridian/state/` |
| Yöntem | salt-okuma ssh + python3 (`goal.yaml` metin okuma · `entry_execution.jsonl` satır sayımı); SQLite `mode=ro` URI |
| Yazım | YOK — hiçbir dosyaya dokunulmadı (canlı worker koşarken state'e yazma yasağı) |
| Ölçüm anı | `2026-08-23T20:31:50+00:00` |
| Ölçülen alanlar | `goal.yaml → pessimistic_band_v2.{ampirik_bps, ampirik_n, ampirik_guncelleme}` ve onları BESLEYEN defter (`state/entry_execution.jsonl`, `analytics.pessimistic_band_update`) |

`ampirik_*` öneki canlı kod tabanında TEK bir yerde yaşıyor (tarama 2026-08-23:
`meridian/analytics.py` üreteci + `meridian/web/app.js` okuyucusu) — ikinci bir ampirik alan
ailesi YOK, yani bu rapor o ailenin tamamını kapsar.

## 1. Alanların BUGÜNKÜ hâli (canlı `goal.yaml`)

```
pessimistic_band_v2:
  acilis_spread_bps: 20.0        # literatür tabanı (Bogousslavsky-Muravyev 2023 JFM)
  mevcut_model_bps: 10.0         # yürürlükteki model: 5 bps × 2 bacak
  ampirik_bps: null              # ← DOLU DEĞİL
  ampirik_n: 0                   # ← SIFIR
  ampirik_guncelleme: null       # ← HİÇ YAZILMAMIŞ
```

Yürürlükteki band bu yüzden `taban: "literatur"` koluyla hesaplanıyor:
`ek_bps_giris = max(0, 20.0/2 − 5) = 5.0 bps` (yalnız giriş bacağına). Ampirik kol
(`taban: "ampirik"`) BUGÜNE KADAR HİÇ devreye girmedi.

## 2. n — kaç ölçülmüş dolum var?

`analytics.pessimistic_band_update` ampirik bandı `entry_execution.jsonl`in **ayna** motorundaki
`fill_vs_resmi_acilis_bps` alanından türetir. Sayım:

| Ölçü | Değer |
|---|---|
| Defterdeki toplam satır | 30 |
| — `motor="ayna"` (gerçek broker) | 15 |
| — `motor="ic"` (iç simülasyon) | 15 — **ampirik banda GİRMEZ** |
| Ayna satırlarından DOLAN | 13 |
| Ayna satırlarından **ÖLÇÜLEN** (`fill_vs_resmi_acilis_bps ≠ None`) | **13** |
| Resmî açılış okunamadığı için ölçülemeyen | 0 |
| Kısmi dolum (terminal olmayan) | 0 |
| Eşik (`analytics.BAND_MIN_N`) | **20** |
| **Eşiğe kalan** | **7** |

Dolmayan 2 ayna satırı: `2026-08-21` PANW ve DE — ikisi de `karar="submitted"`, red nedeni YOK
(emir gönderildi, o gün dolmadı; sonraki turda yamalanabilir).

`motor="ic"` satırlarının dışarıda kalması bir kayıp değil, defterin kendi beyanı: iç-motor dolumu
açılıştan SABİT slippage ile türetilir, yani "resmî açılışa göre bps" tanım gereği
`slippage_bps` sabitini yeniden üretirdi (satırın kendi alanı bunu yazıyor:
`fill_vs_resmi_acilis_beyan = "ÖLÇÜLEMEDİ: … totoloji, ölçüm değil"`).

## 3. Tazelik

| Ölçü | Değer |
|---|---|
| Defterdeki en yeni satır (`ts`) | `2026-08-21T20:32:22+00:00` |
| Ölçüm anına takvim mesafesi | 47 sa 59 dk |
| Ölçüm anına **işlem-günü** mesafesi | **0** (08-22 Cumartesi, 08-23 Pazar; son seans 08-21 Cuma) |
| En yeni ÖLÇÜLEN dolum (`ts`) | `2026-08-19` |
| En yeni yama damgası (`fill_kaydedildi`) | `2026-08-20` |
| `ampirik_guncelleme` | `null` — alan hiç yazılmadığı için "bayat mı?" sorusu henüz doğmadı |

**Hüküm değil, gözlem:** defter bayat DEĞİL; hafta sonu boşluğu dışında gecikme yok. Yama
zinciri de çalışıyor — dolum ile yamanın kaydedildiği gün arasında tipik olarak 1 iş günü var
(08-19 dolumları 08-20'de yamalanmış).

## 4. Debi — hangi hızda doluyor?

Ölçülen dolumların gün dağılımı (satırın `ts`i):

| Gün | 08-05 | 08-06 | 08-13 | 08-14 | 08-19 |
|---|---|---|---|---|---|
| Ölçülen dolum | 3 | 1 | 2 | 2 | 5 |

* Pencere: `2026-08-05` … `2026-08-21` = **13 işlem günü**.
* Toplam ölçülen: **13** → **ham debi ≈ 1,00 ölçülen dolum / işlem günü**.
* Ama debi DÜZ DEĞİL, **PATLAMALI**: 13 günün yalnız **5'inde** dolum var; 8 gün sıfır. Ortalama
  bir "günlük hız" gibi okunursa yanıltır — dolumlar giriş kadansına (silahlı plan + açılış
  penceresi) bağlı kümeler hâlinde geliyor.

**Projeksiyon (varsayımı BEYANLI):** bugünkü ham debi (1,00/işlem günü) aynen sürerse eşiğe kalan
7 dolum ≈ **7 işlem günü** → `n=20` yaklaşık **2026-09-01** civarında dolar. Bu bir tahmindir,
ölçüm değil: dayanağı 5 aktif günlük bir örneklemdir ve patlamalı dağılımda ±birkaç gün oynar.

## 5. Sayının KENDİSİ — eşik dolsa ne olurdu?

Eşik henüz dolmadığı için `pessimistic_band_update` bugün `ampirik_bps: None` +
`neden: "ölçülmüş dolum 13 < 20 — ampirik band HENÜZ YOK"` döndürüyor. Yine de mevcut 13 değerin
dağılımı, eşiğin **yeterliliği** hakkında bilgi taşıyor:

| Ölçü | Değer (bps) |
|---|---|
| n | 13 |
| Ortalama | **+18,76** |
| Medyan | +15,02 |
| En küçük / en büyük | **−130,74** / **+327,46** |
| Standart sapma | **118,18** |
| Ortalamanın standart hatası | **32,78** |

Ham değerler (gün · sembol · bps):

```
08-05 NUE  +16,13   08-05 EMR  +54,62   08-05 BKNG +134,49   08-06 AMGN +15,02
08-13 MRK  +40,84   08-13 CRM  −81,98   08-14 MRNA −130,74   08-14 HUM  −43,04
08-19 MRNA −122,08  08-19 MRK   −9,76   08-19 MRVL +327,46   08-19 LLY  +29,79
08-19 BDX  +13,18
```

**Beyanlı gözlem (hüküm değil, ama eşik tartışmasının girdisi):** SE 32,78 bps, ortalamanın
kendisinden (18,76) BÜYÜK — yani bugünkü örneklemde ampirik maliyetin **İŞARETİ bile
belirlenmemiş** (kabaca ±1,96·SE ⇒ [−45, +83] bps). Aynı dağılımla (sd ≈ 118) `n=20`'de SE
≈ 26 bps olur; yani eşik DOLDUĞUNDA da aralık geniş kalır. ±10 bps'lik bir yarı-aralık için
gereken örneklem, aynı sd varsayımıyla n ≈ 535'tir. Bu, "BAND_MIN_N=20 yanlış" demek DEĞİLDİR —
eşik bir ön-kayıt kararıdır ve bu rapor eşiğe dokunmaz; söylenen şudur: **eşik dolduğunda çıkacak
sayı, dar bir tahmin olmayacak** ve bandı "ampirik" koluna çevirme kararı bu aralıkla birlikte
tartılmalıdır.

## 6. Ölçüme takılan ikinci gözlem — `dolum_ts` henüz canlıda YOK

E-kod [5] ile giriş/çıkış yamalarına eklenen `dolum_ts` alanı canlı defterde **0/30 satırda**
görünüyor: kod bu turda yazıldı, A1'e HENÜZ DAĞITILMADI. Yani bugünkü ampirik band tartışması
"dolum ne zaman oldu" bilgisi olmadan yürüyor — bu boşluğun somut bedeli
`docs/RAPOR-HUM-NUE-2026-08-23.md` §2'de ölçülü hâlde duruyor.

## 7. Ne YAPILMADI (kapsam beyanı)

* `goal.yaml`a HİÇBİR ŞEY yazılmadı; `ampirik_bps` hâlâ `null`.
* `BAND_MIN_N` eşiğine dokunulmadı.
* Hüküm verilmedi: "band açılsın/açılmasın" bu belgenin işi değil.
* Canlıda hiçbir servis durdurulmadı/başlatılmadı, hiçbir dosya yazılmadı.
