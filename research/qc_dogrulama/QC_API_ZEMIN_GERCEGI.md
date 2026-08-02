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
