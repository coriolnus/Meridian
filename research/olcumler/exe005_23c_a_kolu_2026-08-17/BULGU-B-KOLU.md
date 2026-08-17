# 23c B KOLU — ÖLÇÜM BULGUSU (duman penceresi, 2026-08-17)

## Sonuç: kartın sorusu BU KONFİGÜRASYONDA CEVAPLANAMAZ (örneklem BOŞ)

| ölçüm | A kolu | B kolu |
|---|---|---|
| işlem n | 8 (mb=5) | 8 (mb=5) |
| net_pnl | −2163,48 | −2163,48 |
| `performans` bloğu | — | **A ile birebir** |
| `islem` bloğu | — | **A ile birebir** |
| `entry_rejects` | — | `{"open_below_stop": 1}` |
| **`entry_missed_limit`** | — | **SIFIR** |

`bar_low` B kolunda geçildi ve kural koştu; uygulanacak **tek bir vaka bulamadı**.

## Kök neden YAPISAL, örneklem küçüklüğü DEĞİL

`broker.py` giriş kapıları bu SIRAYLA sınanır ve ikisi AYNI eşiği taşır:

    1. max_chase        : next_open > trigger * (1 + MAX_ENTRY_GAP_PCT)   → 0.04
    2. limit (E1)       : next_open > entry_limit_price(trigger, atr, law)

Canlı yasa `E1-v2`: `limit_pct_cap = 0.04` · `limit_atr_mult = 100.0`.
`limit_atr_mult` çok büyük olduğu için ATR bacağı HİÇ bağlamaz; cap her zaman baskındır ve
limit fiyatı tam olarak `trigger * 1.04` olur — yani **`max_chase` tavanıyla BİREBİR AYNI**.
`max_chase` ÖNCE sınandığı için limit kapısının ateşleyebileceği aralık BOŞ KÜMEdir.

Ölçüldü (2026-08-17): `trigger=100` için atr ∈ {None, 1.0, 2.0, 4.0} → limit = 104,0000 ve
tavan = 104,00; dört durumda da "limit kapısı ULAŞILMAZ".

Duman penceresindeki sıfır red bu yapısal olgunun DOĞRULAMASIDIR, kendi başına kanıtı değil:
8 işlemlik bir pencerede sıfır görmek zayıf kanıt olurdu; eşik özdeşliği ise kesin.

## Kart üzerindeki etkisi

- **Ö1 (abartının büyüklüğü) TANIMSIZ**: "kaçtı denilenlerin yüzde kaçı doluyor" sorusunun
  paydası SIFIR. `0/0` bir oran değildir; UYDURMA YASAĞI gereği None kalır + neden yazılır.
- **Ö2 / Ö3 ÖLÇÜLEMEZ**: dönüşen işlem olmadığı için R dağılımı ve portföy etkisi de yok.
- **Kart ÇÜRÜMEDİ** — sorusu geçerli, ama sorulacağı KONFİGÜRASYON canlı yasa DEĞİL.

## Bunun kendisi bir bulgu (ve muhtemelen daha değerlisi)

`EXE-2026-001-R2`nin E1 grid hükmü **"limit bacağı MONOTON ZARARLI · kaçanlar sistematik
KAZANAN"** diyordu. Ama canlı yasada o bacak **HİÇ ATEŞLEMİYOR**. İki okuma mümkün ve ikisi de
ayrı bir kalem gerektiriyor:
  (a) E1 grid DAR tavanları (ör. 100 bps) süpürdü, hüküm oradan geldi; canlı yasa geniş tavana
      yerleşti ve bacak atıl kaldı → hüküm canlıyı BAĞLAMIYOR.
  (b) Ya da yasa/tavan bir noktada değişti ve hüküm bayatladı.
Hangisi olduğu ÖLÇÜLMEDİ — yeni bir `Ö-` kalemi.

## Sıradaki doğru adım

Kartın ölçümü DAR TAVANLI bir yasayla koşulmalı (E1 grid'in süpürdüğü bant; `limit_pct_cap`
`MAX_ENTRY_GAP_PCT`ten KÜÇÜK olmalı, yoksa kapı yapısal olarak ölü). Bu bir eşik değişikliği
DEĞİL, ölçümün geçerli olduğu bölgenin BEYANIdır — ama kart `parameter_grid`e dokunduğu için
Rol-1 hükmü ve K-defteri kaydı ister.
