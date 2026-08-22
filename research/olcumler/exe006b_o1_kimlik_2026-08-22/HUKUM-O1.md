# EXE-2026-006 · Ö-51b — Ö1 ÖLÇÜLDÜ (Rol-1 hükmü, 2026-08-22)

**Kart:** `research/cards/EXE-2026-006-limit-bacagi-hukum-sinamasi.yaml` (measured, K=8).
**K harcanmadı:** aynı 8 hücre, aynı tavanlar/kurallar/eşikler. Yeni olan KAYDEDİLEN alan
(`entry_reject_ids`), ölçülen uzay değil — `Ö-51c` için verilen hükmün aynısı.

## KAPI: A KOLU BAYT ÖZDEŞ (dört tavanda da)

Bu geceki `backtest.py` değişikliği (`entry_reject_ids` + `DINLENEN_LIMIT` bayrağı) A kolunu
BOZMADI: 2026-08-22 defterleri 2026-08-17'nin donmuş defterleriyle **bayt bayt aynı**. Yani
aşağıdaki sayılar 2026-08-17 hükmüyle doğrudan kıyaslanabilir. Bu kapı olmasaydı Ö1'in yeni
değeri "düzeltme mi, sapma mı" ayırt edilemezdi.

## Ö1 — ÖLÇÜLDÜ (2026-08-17'de ÖLÇÜLEMEZDİ)

| tavan | **Ö1** | pay (KURTARILAN) | payda (DİSTİNKT red) | yerinden (dışlandı) | kurtarılanların ort-R |
|---|---:|---:|---:|---:|---:|
| 0,005 | **%60,8** | 208 | 342 | 43 | −0,0789 |
| 0,01 | **%66,9** | 121 | 181 | 54 | +0,0016 |
| 0,02 | **%73,8** | 59 | 80 | 47 | −0,0050 |
| 0,03 | **%73,6** | 53 | 72 | 49 | +0,0725 |

**HÜKÜM: Ö1 dört tavanda da %20'nin ÇOK ÜSTÜNDE → `K1` şerhi AÇILIR.** Replay'in kaçan-işlem
maliyeti abartılmış değil, **kabaca üçte iki oranında** abartılmış: kalıcı kaçtı sayılan
planların %61–74'ü dinlenen limitle DOLUYOR.

## 2026-08-17'nin TEŞHİSİ KISMEN YANLIŞTI — ölçümle düzeltildi

O turda Ö1 `None` bırakılmış ve gerekçe şuydu: *"payda `entry_missed_limit` bir RED OLAYI
sayacı (aynı plan günlerce reddedilebilir), pay DİSTİNKT İŞLEM — birim uyuşmazlığı."*

**Kimlikli ölçüm bu gerekçenin BİRİNCİ YARISINI ÇÜRÜTTÜ.** Olay/plan çarpanı dört tavanda da
**tam ×1,0**: 342 red olayı = 342 distinkt plan, 181 = 181, 80 = 80, 72 = 72. **Hiçbir plan
birden fazla kez reddedilmemiş.** Payda hiç şişmemişti.

Demek ki %132/%141'lik imkânsız oranların TEK sebebi teşhisin İKİNCİ yarısıydı: **pay saf
değildi.** Her hücrede 43–54 işlem, limit kapısının kurtardığı için değil bir slot boşaldığı
için B kolunda görünüyordu. Kesişime indirince oran yapısal olarak ≤%100 oldu.

Ders (ölçüm-şablonu): iki aday sebep sıralandığında "ikisi de olabilir" demek ölçmemektir.
Kimlik kaydı birini çürüttü, diğerini doğruladı — ve düzeltme YÖNÜ değiştirmedi ama BÜYÜKLÜĞÜ
%132'den %61'e indirdi.

## B4 İÇİN ANLAMI — abartı BÜYÜK, ama para YOK

En önemli satır tablonun sağ sütunu: **gerçekten kurtarılan işlemlerin ort-R'si ~SIFIR**
(−0,079 · +0,002 · −0,005 · +0,073). Kirli payla ölçülen Ö2 değerleri (−0,044 · +0,041 ·
+0,101 · +0,117) DÖRT TAVANDA DA DAHA YÜKSEKTİ — yani pozitif işareti taşıyan şey kurtarılan
işlemler değil, **yerinden-etme** işlemleriydi.

Bu, `Ö-51c` ile aynı yöne bakıyor (ΔP&L CI dört tavanda da sıfırı içeriyor). İkisi birlikte:

- E1'in **GEREKÇESİ** çöktü: "monoton zararlı" düştü (H1), "kaçanlar sistematik kazanan"
  ölçülemedi (H2), ve maliyet modeli üçte iki abartıyormuş (Ö1).
- Ama E1'in **SONUCUNU** (bacak canlıda kapalı) ters çevirecek POZİTİF kanıt YOK: kurtarılan
  işlemler ~0R, ΔP&L sıfırdan ayrışmıyor.

**Yanlış gerekçeyle doğru yerde durmak, doğru durmak değildir — ama yanlış gerekçeyi düzeltmek
tek başına yer değiştirmeyi de gerektirmez.** `B4` operatör kararı bu iki cümlenin arasında
verilir; bu belge kararı VERMEZ (kartın kendi sınırı).

**`B4`ün İKİ ÖN-KOŞULU DA KAPANDI:** `Ö-51c` (2026-08-21) · `Ö-51b` (2026-08-22).

## BEYANLI SINIRLAR

1. Eşleşme kimliği `(ticker, tarih)`. Aynı sembolün aynı gün İKİ planı olsaydı ayrışmazlardı;
   bu veride öyle bir vaka olup olmadığı ÖLÇÜLMEDİ.
2. `yerinden` kovası Ö1'e girmiyor ama YOK sayılmıyor — sayısı tabloda. Yerinden-etmenin
   P&L etkisi `Ö3` yan-kanal ayrıştırmasında zaten ölçülü (2026-08-17).
3. Ö1 bir ORAN'dır, para değil. "%74'ü doluyor" cümlesi "%74 daha çok kazanırdık" DEMEK DEĞİL —
   sağ sütun tam da bunu gösteriyor.
4. Ölçüm dar tavanlı (0,005–0,03) ÖLÇÜM KOLUNDA koştu. Canlı yasada (`limit_pct_cap=0,04`,
   `limit_atr_mult=100,0`) kapı hâlâ yapısal olarak ulaşılmaz — `BULGU-B-KOLU.md`.
