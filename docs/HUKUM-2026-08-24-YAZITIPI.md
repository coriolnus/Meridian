# HÜKÜM — YAZI TİPİ DEVRALMA (Rol-1, 2026-08-24)

## KARAR: **(b) KARMA — `--sans` Inter olur, `--mono` Recursive Mono KALIR.**

Operatör "yazı tiplerini internetten bul ve indir" dedi. İndirildi, lisansları metinden
doğrulandı, ve deponun KENDİ 2026-08-07 düzeneğiyle yeniden ölçüldü.

### Geçerlilik kapısı: **TABAN YENİDEN ÜRETİLDİ**
Donmuş sayılar birebir çıktı — Geist Mono `1`/`l` 0,92 @10px / 0,57 @28px · Recursive Mono
1,00 / 0,817. Düzenek geçerli, dolayısıyla YENİ sayılar da geçerli.

### Ölçüm (dpr=1, tabanın koşulları)
| ölçüt | **Inter** kesit | Inter + `ss02`/`cv01` | **Geist Mono** kesit | Recursive Sans | Recursive Mono |
|---|---|---|---|---|---|
| `1`/`l` @10px | 0,969 | **1,000** | 0,923 | 0,933 | **1,000** |
| `1`/`l` @28px | **0,968** | **0,988** | **0,570** | 0,931 | **0,817** |
| `0`/`O` @28px | **0,774** | 0,826 | 0,613 | 0,663 | 0,621 |
| gerçek monospace | hayır | hayır | evet | hayır | **evet** |

Cihazın gerçek dpr'ında (=2) fark büyüyor: Geist Mono `1`/`l` @28px **0,576**, Recursive Mono 0,708.

### Gerekçe — iki yönlü bir bulgu, iki yönü de alınır
Ölçüm **tek yönlü değil**: sans tarafında Inter kazanıyor, mono tarafında Recursive kazanıyor.
Aynı düzenek, aynı koşu, tabanı birebir yeniden üreten kalibrasyon.

- **Inter ALINIR**: her okunaklılık ölçütünde Recursive Sans'ı geçiyor (`1`/`l` 0,968 vs 0,931 ·
  `0`/`O` 0,774 vs 0,663). Ölçülmüş bir iyileşmeyi gerekçesiz reddetmek disipline aykırı olurdu.
- **Geist Mono ALINMAZ**: `1`/`l` ayrımı 0,817 → **0,570** (−%30). Bu, bir alım-satım panosunun
  **para taşıyan yüzeyidir** ve Geist'te telafi edecek hiçbir OpenType özelliği YOK (ölçüldü:
  `tnum` yok — gerekmiyor çünkü yapısal, ama `zero` da yok, `ss01`/`ss02` rakamlara atıl).
  Ayrıca kesitte **`₺` ve `✓` YOK** — pano işaretleri yedek yüze düşerdi.
  2026-08-07 hükmü **doğrulandı, çürütülmedi**; geri almak için sebep yok.
- Bütçe: 37,8 + 39,0 = **76,8 KB** (tavan 120 KB, 43,2 KB boşluk).
- Değişiklik **cerrahidir**: `--sans` ve onun `@font-face`i değişir, `--mono` satırına DOKUNULMAZ.

### Kabul edilen bedel (beyanlı)
Dub'la **birebir** aynı tipografi olmayacak — mono farklı kalıyor. İki aileden yüz taşımanın
tipografik tutarlılık bedeli **ölçülmedi** ve bu belge onu iddia etmiyor. Karar, ölçülen
okunaklılığı ölçülmemiş bir estetik tutarlılığa tercih etmektir.

### Açık kalem — kesit `ss02`/`cv01`'i BUDUYOR
Inter'in Il1 ayrım özellikleri kaynakta VAR ama üretilen kesitte budanmış. Kesitle 0,968,
tam dosyayla 0,988. **Kesit bu iki özelliği koruyacak biçimde yeniden üretilmeli** ve fark
yeniden ölçülmeli. Budanmış hâli bile Recursive Sans'ı geçtiği için bu bir BLOKE DEĞİL,
bir iyileştirmedir.

### Satoshi
Ayrı hüküm: `docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md` §8 — **alınmıyor** (kesit alma lisansla
yasak, panoda 36px+ başlık yok, ekranda sıfır karakter çizerdi).
