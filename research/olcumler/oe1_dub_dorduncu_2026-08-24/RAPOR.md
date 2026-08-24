# ÖE1 — DÖRDÜNCÜ VE BEŞİNCİ SEÇENEK (2026-08-24, operatör: "uygulamada renkleri kullanmamışsın")

Jeton turu üç aday ölçüp §9.4'e (Omega ailesi) çekilmişti. Operatör panonun renksiz olduğunu
söyledi ve haklıydı: `index.html`de altı Dub aksanından **üç hex** geçiyor, üçü de mavi.
`vivid-green`, `tangerine`, `soft-mint` HİÇ YOK; `lavender` tanımlı ama görünmez (kâğıt modu
akromatik ve sistem hep kâğıtta).

## ÖNCE TEŞHİS: sorun hue DEĞİL, KROMA
| | Dub | panoda | hue farkı | kroma |
|---|---|---|---|---|
| yeşil | `#16a34a` 146,4° | `#1f7646` 152,6° | 6,2° | **−%36** |
| kehribar | `#ea580c` 50,0° | `#77520e` 77,3° | **27,3°** | **−%48** |
| kırmızı | *(Dub'da yok)* | `#9a0019` 31,3° | — | — |

Yeşil zaten Dub'ın hue'sunda. Kehribar 27° kaymış. İkisi de yarı yarıya solmuş.
**Kök neden:** luminans merdiveni onları koyulaştırdı, sRGB'de koyulaşmak kromaya mal olur.

## DÖRDÜNCÜ SEÇENEK — Dub hue'ları + merdiven, renk METİN kalır
72 kombinasyon. **DÜŞTÜ** ama beklenmedik yerden: ÖE1-a ve ÖE1-b rahat geçiyor
(ΔE 41/63, lum 1,25), **ÖE1-c düşüyor** (4,38/3,62/2,91 — üçü de 4,5 altında). Dub'ın yeşili
doğası gereği açık; merdiveni ondan başlatınca üçü de yeterince koyulaşamıyor.

## BEŞİNCİ SEÇENEK — gramer değişmez, hue Dub'a çekilir  ✅ GEÇER, AMA PAYSIZ
| tema | | mevcut → yeni | hue | kroma |
|---|---|---|---|---|
| gündüz | sev-1 | `#9a0019` → `#90001d` | 31,3°→28,2° | −%7 |
| gündüz | sev-2 | `#77520e` → `#9b3400` | 77,3°→**49,7°** | **+%48** |
| gündüz | sev-3 | `#1f7646` → `#007c30` | 152,6°→**145,0°** | **+%36** |
| gece | sev-1 | `#ffbab4` → `#ffa5a0` | 28,1°→26,7° | +%34 |
| gece | sev-2 | `#d8b072` → `#ff874e` | 79,8°→**50,6°** | **+%72** |
| gece | sev-3 | `#61b37f` → `#00b048` | 152,8°→**145,1°** | **+%77** |

Üç donmuş eşik de tutuyor: gündüz lum 1,309/1,361 · ΔE **15,1**/55,5 · AA 7,86/6,21/4,65 ·
gece lum 1,262/1,209 · ΔE 16,6/59,3 · AA 6,51/5,36/4,59.

**⚠ PAY YOK.** ΔE 15,1'e karşı çıta 15. Paylı arama (ΔE≥18 · lum≥1,25 · AA≥4,7)
**iki temada da BOŞ döndü** — yani bu, Dub hue'larıyla metin-taşıyıcı altında ulaşılabilecek
sınırın kendisi. Eşiğin kıyısında sevk etmek, başka bir ΔE uygulamasının hükmü çevirmesi
demektir.

## ALTINCI SEÇENEK — TAŞIYICI DEĞİŞİMİ (payı olan tek yol)
Renk **metin olmaktan çıkar, işaret olur**; yazı nötr mürekkebe geçer. Bu Dub'ın KENDİ deseni
(feature pill: aksan yüzer, gövde nötr kalır) ve okunabilirliği **artırır** — nötr mürekkep
%10 tint üstünde ~18:1, renkli mürekkep 4,5:1.
Ölçüldü: **ΔE 17,9/64,8 · lum 1,21/1,27 · işaret 3:1 → 4,82/3,99/3,14**, ve kroma kazancı
**kehribar +%97 · yeşil +%70 · kırmızı +%28**.
**Bu bir GEVŞETME DEĞİL, taşıyıcı değişimidir:** ÖE1-c metne uygulanmaya devam eder — ama
metin artık nötr, yani şart daha kolay değil daha SIKI karşılanır.
**Bedeli ölçüldü:** `index.html`de şiddet rengini metin olarak kullanan **39 kural** +
`app.js`te çip işaretlemesi.

## AÇIK, BEDELSİZ KALEM (ölçüm gerektirmez)
`soft-mint #dcfce7` Dub'ın KENDİ yüzey jetonudur (`surface.tinted-accent`) ve bir durum rengi
değil, bir zemin tintidir — şiddet kanalıyla hiç ilgisi yok. Bugün HİÇ kullanılmıyor.
