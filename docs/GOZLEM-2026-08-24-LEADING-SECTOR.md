# GÖZLEM — `leading_sector` kapısı (2026-08-24) · **HÜKÜM DEĞİL**

> Bu belge bir GÖZLEMİ kayda geçirir. Hüküm taşımaz, karar bağlamaz, canlıya dokunmaz.
> Sınanması `research/cards/EDG-2026-057-leading-sector-kapisi.yaml` kartına bağlıdır.

## Nasıl ortaya çıktı
`/api/topviews` ucu yazılırken (commit b11fc97) planların kapı-reddi kırılımı İLK KEZ tek
paydadan ölçüldü: `trade_plans.jsonl` → `gate_checks[].passed == false`, 390 plan, 11 ölçüt,
pencere 2023-01-20 → 2026-07-28. Ucu yazan ajan, kart olmadığı için bunu **gözlem** diye
işaretledi ve doğru yaptı.

## Sayı
| kohort | n | sum_r | PF |
|---|---|---|---|
| `leading_sector` ölçütünde takılan plan | **217** | — | — |
| …REVIEW'a rağmen işleme dönen | 52 işlem | **+3,09R** | **1,16** |
| `GO` hükmü alan | 28 işlem | **−3,15R** | **0,77** |

Defterdeki tek pozitif kohort, kapının reddettiklerinden geçenler. En çok ateşleyen kapı da bu.

## NEDEN BU BİR KANIT DEĞİL — üç kusur, biri öldürücü
1. **Eşik-gözetleme.** Sayı, eşik donmadan önce görüldü. Bu deponun kart disiplini tam olarak
   bunu yasaklar; sonradan yazılan bir eşik, gördüğü sayıya göre şekillenir.
2. **SEÇİM YANLILIĞI — öldürücü olan.** O 52 plan REVIEW'dan **rastgele geçmedi**; bir seçici
   (insan ya da mekanizma) onları seçti. O hâlde ölçülen şey "kapı yanılıyor" olmayabilir —
   "seçici isabetli" de olabilir. İki hipotez bu veriyle **ayrılamaz**.
3. **Payda karışması.** 217 PLAN, 52 İŞLEM. Aynı satırda okunursa "217 planın PF'i 1,16" gibi
   okunur. Panoda bu yüzden `n` ve `r_n` AYRI sütun (ROADMAP'e işlendi).

## Nasıl sınanacak
Aynı defteri yeniden ölçmek DÖNGÜSELDİR. Kart (EDG-2026-057) dokunulmamış dilimi ölçer:
**`leading_sector`da takılmış ve HİÇBİR ZAMAN işleme dönmemiş planlar** (~165) donmuş edg032c
kasasında karşı-olgusal koşulur. O dilimi kimse seçmedi, yani seçim yanlılığı yok.
Karar kuralı ölçümden önce donduruldu ve gözlem sayısına bakılmadan türetildi: kapı ancak
reddettiklerinin beklentisi pozitif DEĞİLSE gerekçelidir → eşik **sıfır**.

## Ne YAPILMADI (bilinçli)
- Kapı gevşetilmedi, kaldırılmadı, eşiği oynatılmadı.
- Panoda bu satırlara vurgu/renk/sıralama ayrıcalığı VERİLMEDİ — Top Views yüzeyi
  "keşif görünümü · hüküm kart-önce" damgası taşıyor; bir sayıyı öne çıkarmak o damgayı
  boşa düşürürdü.
- ROADMAP'e "bulgu" olarak değil, **kart bekleyen gözlem** olarak işlenecek.
