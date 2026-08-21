# BULGU — "açıklanamayan 2.623,34" SENTE KAPANDI (2026-08-22)

**Operatörün sorusu:** *"alpacadaki toplam para ile panodaki tutar birbirinden farklı."*
Köprü (`broker_mutabakati`, 2026-08-22'de canlıya çıktı) farkı terim terim açıyordu ama son bir
kalem **`aciklanamayan: 2623.34`** olarak duruyordu. Bu belge o kalemi **sıfıra indirir.**

## SONUÇ

```
2.623,34  =  2.615,96 (defter ayrışmaları)  +  7,38 (taban farkı)
```

Yuvarlama değil, SENTE kapanıyor. Kitap tarafı da bağımsız doğrulandı: ayrıştırmanın kitap
toplamı 6.350,23, `portfolio.json`daki `realized_pnl` 6.350,22314 — yani hiçbir işlem atlanmadı.

## TERİM TERİM

| sembol | broker gerçekleşen | kitap gerçekleşen | fark | sınıf |
|---|---:|---:|---:|---|
| **MRNA** | 9.152,40 | 6.436,17 | **+2.716,23** | kısmî — broker hâlâ 8 hisse tutuyor |
| VLO | 0,00 | 728,37 | −728,37 | 🔴 **karşılıksız** (broker'da hiç yok) |
| NUE | −429,70 | −884,15 | +454,45 | tam kapandı, ADET ayrıştı (25 vs 54) |
| ALL | 0,00 | −450,38 | +450,38 | 🔴 **karşılıksız** (broker'da hiç yok) |
| MRK | 1.060,03 | 1.373,76 | −313,73 | kısmî — broker 65 hisse tutuyor |
| MRVL | −289,57 | −4,27 | −285,30 | tam kapandı, ADET ayrıştı (37 vs 36) |
| HUM | −222,53 | −395,34 | +172,81 | tam kapandı, ADET ayrıştı (43 vs 57) |
| LLY | −303,24 | −453,93 | +150,69 | tam kapandı, ADET ayrıştı (9 vs 10) |
| FEE | −1,20 | — | −1,20 | broker ücreti, kitapta karşılığı yok |
| **toplam** | **8.967,39** | **6.350,23** | **+2.615,96** | |
| taban farkı | | | **+7,38** | broker reset günü equity **99.992,62** ≠ kitap tabanı **100.000,00** |
| | | | **= 2.623,34** | ✅ |

**YÖNTEM — VARSAYIMSIZ.** Kısmî pozisyonlarda broker'ın gerçekleşeni
`satış hasılatı − (toplam alım maliyeti − ELDE KALANIN broker cost_basis'i)` ile hesaplandı.
FIFO ya da ortalama-maliyet konvansiyonu VARSAYILMADI — broker'ın kendi `cost_basis` alanı
kullanıldı. Aktivite defteri tam sayfalandı (`page_size=100`; aşılırsa yanıt liste değil
SÖZLÜK döner — 2026-08-21 tuzağı).

## ÜÇ KÖK SINIF

**A · KARŞILIKSIZ İŞLEM** (ALL, VLO) — net **−277,99**. Kitap broker'da hiç var olmamış iki
işlemin P&L'ini yazdı. Zaten belgeli: `docs/BULGU-KARSILIKSIZ-CANLI-ISLEM-2026-08-21.md`,
kart `EXE-2026-007`, tahta kalemi `Ö-52`.

**B · ADET AYRIŞMASI** (diğer hepsi) — kalıntının **ezici çoğunluğu**. 🆕 **BU YENİ.** Açık
pozisyonların **YEDİSİNDE DE** kitap ile broker adet tutmuyor, üstelik broker'da kitabın hiç
bilmediği bir **NVDA** pozisyonu var:

| | AMGN | BDX | BKNG | CRM | EMR | MRK | MRNA | NVDA |
|---|---|---|---|---|---|---|---|---|
| kitap | 33 | 43 | 43 | 17 | 64 | 76 | 13 | — |
| broker | 22 | 40 | 22 | 19 | 37 | 65 | 8 | **1** |

Kitap 57.995,64 maliyet taşıyor, broker 42.334,42 — **15.661,22 fark.** Yön TEK YÖNLÜ DEĞİL
(CRM'de broker fazla), yani basit bir "kısmî dolum" hikâyesi değil.
**ÖNEMLİ:** bu semboller için broker satış defteri BOŞ (satılan = 0). Yani fark satıştan değil,
**girişten** geliyor — broker kitabın yazdığından farklı adet aldı.

**C · TABAN FARKI** (+7,38) — kitabın sermaye tabanı yuvarlak 100.000,00, broker'ın reset günü
equity'si 99.992,62. Zararsız ama köprüde sonsuza dek "açıklanamayan" olarak görünürdü.

## NE DEĞİŞTİ, NE DEĞİŞMEDİ

**DEĞİŞMEDİ:** canlı davranışa DOKUNULMADI. Bu bir ölçüm/teşhis çalışmasıdır; emir gönderimi,
onay kapısı, boyutlandırma ve iç motor aynen duruyor.

## B SINIFININ KÖK NEDENİ — BULUNDU (aynı gün, ölçümle)

**ÖNCE BİR HİPOTEZ ÇÜRÜTÜLDÜ.** "Kısmî dolum + gün sonu expiry" akla yatkındı (olay defterinde
`partially_filled` var). Emir kaydı bunu ÇÜRÜTTÜ: her giriş emri TAM doldu, kayıp sıfır —
AMGN 22→22, BDX 40→40, BKNG 22→22, CRM 19→19, EMR 37→37. `partially_filled` `filled`e giden
geçici bir durumdu. Yani broker'dan zaten 22 istenmişti; kitap 33 yazdı.

**KÖK NEDEN `loop.py`DE, TEK ANLAMLI:**

```python
eq_now = float(_hb["equity"])                       # KİTABIN sermayesi (nabız)
eq     = float(acct["equity"]) ...                  # BROKER'ın sermayesi (Alpaca hesabı)
_smult = derisk_mult(eq_now, _peak)                 # de-risk KİTABIN sermayesinden
meta["size_law"][plan] = {"eq_now": eq_now, ...}    # makbuz KİTABINKİNİ yazıyor
alpaca.submit_plan(pl, eq, size_mult=_smult, ...)   # ayna BROKER'ınkiyle boyutlanıyor
```

Aynı `1R = %1` kuralı, İKİ FARKLI sermaye tabanına uygulanıyor → iki farklı adet. Oranın sabit
olmaması da bundan (CRM'de broker fazla): iki taban birbirinden bağımsız hareket ediyor —
broker equity'si piyasaya göre değerlenir, kitap nakdi gerçekleşene göre.

**BU FARKIN KENDİSİ KUSUR DEĞİL.** Her defterin kendi parasına göre boyutlanması savunulabilir.
Kusur, farkın KAYITSIZ olmasıydı: makbuz aynanın FİİLEN kullandığı sayıyı hiç taşımıyordu, bu
yüzden makbuzu OLAN dört planda bile (CRM·BDX·MRK·MRNA) sapma açıklanamıyor ve `MIRROR_DRIFT`
"gönderim↔dolum kıyası kurulamaz" diyordu.

**KAPATILDI (2026-08-22):** makbuza `eq_ayna` eklendi ve sapma sınıfı tablosuna `ayna_taban`
sınıfı girdi. Artık teşhis şunu basıyor:

> `kitap 107288.55$ ile boyutlandı, AYNA 99800.00$ ile (fark +7488.55$) — iki defter FARKLI
> sermaye tabanına göre boyutlandı; adet sapmasının sebebi bu, icra değil`

Sınıf YALNIZ tablonun pes ettiği son dalda konuşur (önceki sınıflar kitabın iç tutarsızlığını
açıklar ve daha kesindir), ve `eq_ayna` TAŞIMAYAN eski makbuzları "ayrıştı" saymaz — alan
yokluğu ayrışma değildir.

**HÂLÂ AÇIK — POLİTİKA SORUSU (operatörde).** Teşhis kapandı, KARAR kapanmadı: iki defterin
farklı tabanlara göre boyutlanması SÜRSÜN MÜ. Sürerse adetler ayrışmaya devam eder ve köprüde
kalıcı bir kalıntı üretir; tek tabana geçmek ise hangi tabanın doğru olduğu sorusunu açar
(broker'ınki gerçek para, kitabınki stratejinin kendi muhasebesi). Bu bir ölçüm değil tercih
kalemidir ve bu belge onu VERMEZ.

**`mirror_divergence` BU İŞİ YAPMIYOR.** Tam da bunu yakalaması gereken alan, yedi pozisyonun
yedisinde de ayrışma varken `None` döndürüyor (`EXE-2026-007`in beyanlı sınırı: NUE'nin 7 fill'i
vardı, alan yine `None`). `None` "ayrışma yok" DEMEK DEĞİL — "ölçülmedi" demek, ve ikisi bugün
panoda aynı görünüyor.
