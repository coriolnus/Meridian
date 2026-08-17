# EXE-2026-006 — DUMAN TARAMASI (K=8) · 2026-08-17

## ⚠ BU BİR HÜKÜM DEĞİLDİR

Pencere 2022-01-01→2022-06-30 (6 ay), n=5-8 işlem. Kartın kill kriteri:
*"H1/H2 hükmü tek bir tavandan verilirse geçersiz."* Bu tarama **kablonun tuttuğunu** ve
**sinyalin var olduğunu** gösterir; hükmü TAM pencere verir.

## Kablo doğrulaması (hepsi geçti)

| kapı | sonuç |
|---|---|
| şasi bütünlüğü | `frame_miss=0 dup=0 scan!=plan=0` — her hücrede |
| kol kimliği damgası | 8/8 hücrede beklenene UYDU |
| referans dizine yazım | **hiç olmadı** (yapısal koruma) |
| `state/goal.yaml` | DEĞİŞMEDİ |

## Ölçülen sinyal

| tavan | `yalniz_acilis` kaçan | `dinlenen_limit` kaçan | n açılış | n dinlenen |
|---|---|---|---|---|
| 0,005 | 3 | 0 | 5 | 8 |
| 0,01 | 1 | 0 | 7 | 8 |
| 0,02 | 1 | 0 | 7 | 8 |
| 0,03 | 1 | 0 | 7 | 8 |

**Ö1 (duman) = %100** — "kaçtı" sayılan her işlem dinlenen limitle doluyor. Kartın eşiği %20'ydi;
duman penceresinde beşe katlanmış görünüyor. **ÖRNEKLEM ÇOK KÜÇÜK, hüküm bundan çıkmaz.**

Bacağın gerçekten silahlandığı da görünüyor: `cap=0.005`te açılış kolu 5 işlem yaparken dinlenen
kol 8 yapıyor — üç işlem tavan yüzünden kaçmış ve dinlenen limitle geri gelmiş.

## HENÜZ ÖLÇÜLMEYENLER

- **H1 (monotonluk)**: `net_pnl` bu blokta `None` geliyor; sonuç JSON'unun hangi alanından
  çıkarılacağı belirlenmeli. Monotonluk EĞRİ iddiasıdır, dört tavanın hepsinde P&L gerekir.
- **H2 (işaret)**: kaçanların ort-R'si + CI. Ayrı çıkarım gerekiyor.
- **H3**: Ö1'in TAM penceredeki değeri.

## Sıradaki adım

`olcum.py` (bayraksız) → tam pencere, 8 hücre × ~30 dk. Öncesinde `net_pnl`/R çıkarımı eklenmeli,
yoksa tam koşum da H1/H2'yi cevaplamaz.
