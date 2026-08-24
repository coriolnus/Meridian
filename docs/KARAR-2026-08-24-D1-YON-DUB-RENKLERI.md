# D1 — YÖN ROLÜ DUB RENKLERİNE GEÇTİ, KROMA TAVANI TAŞINDI

**Tarih:** 2026-08-24 · **Karar mercii:** operatör · **Uygulayan:** Rol-1

## Tetikleyici

Operatör kurulum×rejim matrisinin ekran görüntüsünü göndererek sordu:
> "bu renkler ne mesela, neden dub renkleri değil"

Öncesinde iki kez daha aynı şeyi söylemişti:
> "yahu dub renklerini istiyorum diyorum, neden her seferinde farklı birşey yapıyorsun,
> renk körü değilim, birşeyi de renkten dolayı karıştırmam"
> "operatör benim ve canlılık istiyorum"

## Düşen kural ve NEDEN düştüğü

`--yon-arti` / `--yon-eksi` bilerek soluklaştırılmıştı: **C = min C(şiddet) × 0,60**,
gerekçe *"kâr/zarar işareti bir alarmla dikkat için YARIŞAMAZ"*. Kural iki ayrı sebeple düştü:

1. **Operatör kararı.** Gerekçe karışma riskiydi; operatör karışmadığını adıyla söyledi ve
   canlılık istedi. Karışma gerekçesi operatörün kendisi tarafından geçersiz kılındı.
2. **Öncül ZATEN yanlıştı — ölçüldü.** Dub hunisi indiğinden beri şiddet ekranın en yüksek
   sesli mürekkebi değil: **gündüz `--huni-2` C=0,2466 ↔ şiddet-min C=0,1671.** "Şiddetin
   altında kal" kuralı "en sesli olma" anlamına gelmiyordu; sadece öyle sanılıyordu.

## Alınan değerler — Dub'ın hue'su korunarak, yalnız AA için koyulaştırılarak

| Jeton | Tema | Dub | Alınan | Dub'a ΔE2000 | Hue farkı | En kötü gerçek zemin |
|---|---|---|---|---|---|---|
| `--yon-arti` | gündüz | `#16a34a` | `#107636` | 16,1 | 0,5° | **4,58** |
| `--yon-eksi` | gündüz | `#c2410c` | `#b43c0b` | 3,3 | 0,0° | **4,63** |
| `--yon-arti` | gece | `#4ade80` | `#4ade80` | **0,0** | 0,0° | **6,32** |
| `--yon-eksi` | gece | `#f87171` | `#f98080` | 3,4 | 0,9° | **4,63** |

Üçü pratikte Dub'ın kendisi. Yalnız gündüz yeşili bir adım koyu, ve bunun ölçülmüş sebebi var:
**yön jetonlarını kullanan 17 öğenin hepsi WCAG'in büyük-metin eşiğinin altında — en küçüğü
11px.** Yani AA 4,5 uygulanır, 3,0 değil. Dub'ın `#16a34a`'sı gündüz 3,02 ölçüldü: bu bir
karışma değil **okunabilirlik** sorunuydu, o yüzden koyulaştırma operatör kararına aykırı değil.

## Yerine gelen canlı kural

Çivi (`tests/test_renk_rolleri_v197.py::test_yon_kromasi_siddetin_gorunur_altinda`) silinmedi;
tavanı taşındı:

> **Yön, ekrandaki ONAYLI mürekkeplerin en yükseğini AŞAMAZ.**

Tavan hâlâ var — yön *yeni bir kroma zirvesi açamaz*, yalnız mevcut zirveye kadar çıkabilir.
Ölçülen: gündüz yön-max 0,1641 ≤ tavan 0,2466 · gece 0,1821 ≤ 0,1821.

Gece sınırda eşit olması tesadüf değil: **gece `--yon-arti` ile `--huni-3` AYNI hex** (`#4ade80`).
Huni yeşilini onaylayıp yön yeşilini soluklaştırmak, operatörün turlardır işaret ettiği
tutarsızlığın ta kendisi olurdu.

## Yarım kalmış olabilecek yer — kapatıldı

Taban jeton değişince **türevleri kendiliğinden gelmiyor**. Saç teli (`-h` .35) ve tint
(.10 / .08) varyantları eski soluk rengin RGB'sini taşıyordu; dört yüzeyde 12'şer, `tokens.json`'da
36 türev tabandan yeniden türetildi. Ayrıca `tokens.json`'ın `hex` / `literal` / `cozulen-deger`
üç alanı ayrışmıştı — hepsi tek kaynaktan yeniden yazıldı.

**Ders:** bir rengi değiştirmek tek bir hex'i değiştirmek değildir; taban + türev + jeton kaydı +
belge tablosu dört katman. Kör `replace` bu turda `--huni-3`'ü de vurdu (aynı hex'i paylaşıyordu)
ve ancak çivi yakaladı.

## Tazelenen belgeler

`DESIGN.md` rol tablosu ve `docs/kontrast-denetimi.md` satır 1102-1105 bayat ölçüm taşıyordu —
ölçülmüş sayı bir iddiadır, bayat kalamaz. Eskiler üstü çizili olarak duruyor (SİLME YOK).
