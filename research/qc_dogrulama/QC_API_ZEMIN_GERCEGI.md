# QC-API zemin gerçeği (canlı ölçüm, 2026-08-03, FREE hesap, Foundation-Py-Default)

Rol-1 tarayıcı oturumunda QuantBook üzerinde **ölçüldü** (tahmin değil). İki sonda hücresi koştu.

## Çalışmayan yollar (defterin H2'de DUR demesinin sebebi)
| çağrı | sonuç |
|---|---|
| `qb.history(Fundamental, B, S)` | **Empty DataFrame** (n=0, Columns=[], Index=[]) |
| `qb.history(CoarseFundamental, B, S)` | **Empty DataFrame** (n=0) |

## Çalışan yollar
| çağrı | dönüş |
|---|---|
| `qb.universe_history(qb.universe.etf("SPY"), B, S)` | `Series` n=3 · indeks `qc-universe-etf-constituents-...` |
| `qb.add_universe(selector)` + `qb.universe_history(u, B, S)` | **`Series`**, MultiIndex `(FUNDAMENTALUNIVERSE-USA-…, time)`, her değer **`list[Fundamental]`** |
| `qb.history(symbol, B, S, Resolution.DAILY)` | `DataFrame` (close/high/low/open) — normal |

## `Fundamental` üyesinin ÖLÇÜLEN alanları (AAPL, 2024-01-02)
```
symbol                                   = AAPL R735QTJ8XC9X
dollar_volume                            = 13861798761.0
volume                                   = 74670323
price                                    = 185.64
market_cap                               = 2994371342560
value                                    = 185.64
company_profile.shares_outstanding       = 15461896000
earning_reports.basic_average_shares.value = 15744231000.0
security_reference.exchange_id           = NAS
```

## Sonuç (mimari hüküm)
`universe_history` + `add_universe(selector)` **TEK kaynak** olarak yeterli: günlük evren seçimi
(dollar_volume sıralaması), fiyat, hacim ve **as-of hisse sayısı** aynı çağrıdan gelir — ayrı
fundamentals çağrısına gerek yok, look-ahead yok (her gün kendi kesiti). Delist-dahillik QC
evreninin doğal özelliğidir; sağkalan-süzgeci YOKTUR.

## EK ÖLÇÜM (2026-08-03, v2 koşumu) — QuantBook NESNE DURUMU KRİTİK

v2 defteri H2'de yine DUR verdi ("universe_history hiçbir yıl diliminde satır döndürmedi").
Sonda hücresi kök nedeni **aynı hücrede yan yana** ölçtü:

| çağıran | pencere | sonuç |
|---|---|---|
| defterin H1'de kurduğu `qb` + `u` | 2020-08-03→08-14 | **n_satir=0** |
| aynı `qb` + `u` | 2024-01-02→01-12 | **n_satir=0** |
| **taze `QuantBook()` + taze `add_universe(top500)`** | 2020-08-03→08-14 | **9 satır** |
| taze QuantBook (ayrı sonda) | 5g/30g/90g/365g, top50 | n=4/21/61/**252** |

**HÜKÜM:** `universe_history` API'si her pencere uzunluğunda ve 2020'de de çalışıyor; ARIZA
defterin H1'de kurduğu QuantBook örneğinin durumunda. Muhtemel sebep: H1'in API-keşfi/tarih-bağlamı
çağrıları (`set_start_date` vb.) ya da aynı `qb` üzerinde önceki `add_universe`/`add_equity`
birikimi. **KURAL (v3'e):** panel çekimi KENDİ TAZE `QuantBook()` örneğini kursun; keşif/sonda
çağrıları ayrı örnekte kalsın — QuantBook nesnesi paylaşılmaz.
