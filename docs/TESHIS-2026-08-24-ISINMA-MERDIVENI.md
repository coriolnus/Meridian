# TEŞHİS — ısınma merdiveni tek yönlü kilitlendi (`warmup_scale`)

**Tarih:** 2026-08-24 · **Rol:** Rol-1 · **Durum:** kök neden BULUNDU, davranış değişikliği
YAPILMADI (gerekçe §4) · **Kaynak:** canlı `meridian-learn` journal'ı + `state/warmup_scale.json`

## 1 · Belirti

`warmup_sprint` yedi gündür sabit bir bütçeyle koşuyor. Canlı ölçüm (10 günlük journal):

```
154 koşum · butce=10 · butce_carpani=1 · k_max=2   ← ÇARPAN HİÇ DEĞİŞMEDİ
```

`state/warmup_scale.json` (canlı, salt okuma):

```json
{"carpan": 1, "duvar": 1, "son": {"evaluated": 4, "cleared": 0, "kesildi": false, ...}}
```

## 2 · Kök neden — duvar YALNIZ AŞAĞI iner ve 1'de yutucudur

`hermes.warmup_budget_feedback()` (`meridian/hermes.py:1790`) üç dallı bir merdiven:

| dal | koşul | etki |
|---|---|---|
| daralt | `kesildi` (H11 süre tavanı) | `carpan = max(1, carpan//2)` **ve** `duvar = max(1, carpan//2)` |
| tabana dön | `cleared > 0` | `carpan = 1` |
| genişlet | `carpan < min(duvar, 8)` | `carpan *= 2` |

İki gözlem birleşince kilit doğuyor:

1. **`duvar` yalnız daraltma dalında atanıyor** ve değeri `carpan//2`. `warmup_budget()`
   (`:1774`) `carpan`ı zaten `duvar` ile kırpıyor (`carpan ≤ duvar`), dolayısıyla
   `carpan//2 ≤ duvar`. Yani **`duvar` monoton azalır; onu yükselten HİÇBİR yol yok.**
2. `carpan` 1 iken bir `kesildi` yaşanırsa `duvar = max(1, 0) = **1**` olur. Bundan sonra
   genişletme koşulu `1 < min(1, 8)` → `1 < 1` → **daima False**. Merdiven ölür.

Docstring *"merdiven yalnız yukarı"* diyor (`:1762`); ölçülen davranış **yalnız aşağı**.
Çelişki beyanla kod arasında, ve kod kazanıyor.

## 3 · Duvarın BAYAT olduğunun kanıtı

Duvar "bu genişlik bu makinede pencereye sığmadı" ölçümüdür ve bu tasarım doğrudur —
tavan uydurulmaz, ölçülür. Kusur tavanın KONULMASI değil, **hiç yeniden sınanmaması**:

* 154 koşumun **hepsinde `kesildi: false`** — yani bugünkü genişlik pencereye rahat sığıyor.
* Duvarı koyan olay journal penceresinin (10 gün) DIŞINDA; yani en az 10 gündür geçerliliği
  sınanmadan yürürlükte.
* Süresi yok, yeniden deneme yok, "duvarı bir kez daha yokla" dalı yok.

## 4 · SESSİZLİK — ikinci kusur, ve bu tartışmasız

`warmup_budget_scaled` olayı yalnız **değişim anında** basılıyor (`:1827`, `if yeni != onceki...`).
Merdiven kilitliyken hiçbir şey değişmediği için **yedi gündür tek satır yok**. Yani mekanizma
durmuş durumda ve durduğunu söyleyen hiçbir kanal yok. Bekçi de bakmıyor.

## 5 · NEDEN BU GECE DAVRANIŞ DEĞİŞTİRMEDİM

Merdiveni açmak "öğrenmeyi açar" DEĞİLDİR ve bunu iddia etmek bu oturumda bir kez çürütülmüş
teşhisin aynısını tekrarlamak olurdu:

* Merdiven açılırsa `sonda_tavani = max(budget*4, 40)` büyür → o turda PLANLANAN sonda sayısı
  (K) artar → `p_req = 1 − (0,20 − extra_p)/K` gereği **ön eleme eşiği SIKILAŞIR**
  (EDG-2026-058'in ölçtüğü mekanizma).
* Yani kilidi açmanın `cleared`e etkisinin YÖNÜ belirsizdir; iyileştirmesi de kötüleştirmesi de
  mümkündür ve ikisi de ölçülmemiştir.
* `cleared=0`ın bugünkü gerekçesi bütçe DEĞİL: son iki koşumun `neden_dagilim`ı
  `{"KISMEN AYIRT EDİLEMEZ": 3, "AYIRT EDİLEMEZ": 1}` — adaylar değerlendirildi ve
  **ayırt edilemez bulundu**. Bu meşru bir red, kapı artefaktı değil.

Dolayısıyla §2'deki kilit bir **mekanizma arızası** olarak kayda geçer; onarımı bir ön-kayıt
kartı ister (soru: "duvarın süresi/yeniden-sınaması ne olmalı?"). Bu belge o kartı AÇMAZ.

## 6 · GÜVENLİ ONARIM — yalnız sessizlik (davranış DEĞİŞMEZ)

Tek tartışmasız kalem §4'tür: kilitli hâlin görünmezliği. Telemetri eklemek hiçbir bütçeyi,
eşiği ya da aday kararını değiştirmez. Bu kalem ayrı işlenir.

## 7 · YAN BULGU — bugünkü düşük verim RESTART kaynaklı, gerileme DEĞİL

`evaluated` bugün 40 → 2/4'e düştü ve `arama_havuzu_zaman_asimi` (`biten: 0`) 6 sessiz günün
ardından geri geldi. Bu **kod gerilemesi değil, soğuk önbellek**: aynı şekil önceki restart'ta
da yaşandı.

| pencere | havuz açlığı | koşum/gün | evaluated |
|---|---|---|---|
| Aug 16–17 (önceki restart sonrası) | 6 kez | — | 33→40'a tırmanıyor |
| Aug 18–23 (kararlı) | **0** | ~23 | hep 40 |
| Aug 24 (00:34 restart sonrası) | 3 kez | 3 (9 saatte) | 40 → 2 → 4 |

**SINANABİLİR ÖNGÖRÜ:** önbellek ısındıkça açlık kesilir ve koşum/gün ~23'e, `evaluated` 40'a
döner. Dönmezse bu açıklama DÜŞER ve gerçek bir gerileme aranmalıdır.

**EDG-2026-058 İÇİN DOĞAL DENEY:** restart önbelleği boşalttı; K şu anda 2-4, ısındıkça 40'a
tırmanacak. Kartın tezi (bedava önbellek isabetleri K'ya sayılıyor) tam da bu tırmanışta
gözlemlenebilir. Kartın eşikleri DONUK, bu not yalnız gözlem penceresini işaret eder.

---

## 8 · ARA GÖZLEM (2026-08-24 12:05Z) — §7'nin öngörüsü YÖNÜ doğru, henüz TAMAMLANMADI

§7 şunu yazmıştı: *"önbellek ısındıkça açlık kesilir ve koşum/gün ~23'e, `evaluated` 40'a
döner. Dönmezse bu açıklama DÜŞER."* Bugünkü seri:

```
evaluated: 40 → 2 → 4 → 6      (00:34 restart'tan sonra, ~11 saatte dört koşum)
arama_havuzu_zaman_asimi: 4    (kararlı Aug 18-23 penceresinde: 0)
```

**Tırmanış var ve yönü öngörülen yönde** — soğuk önbellek açıklamasıyla tutarlı. Ama hız
beklenenden düşük (11 saatte 2→6, 40 değil) ve havuz açlığı hâlâ sürüyor. **Açıklama
ÇÜRÜMEDİ ama DOĞRULANMADI da**; ikisini birbirine karıştırmamak için bu ara nokta yazıldı.

Bir sonraki kontrol için ölçüt AYNI kalır (koşum/gün ve `evaluated`); 24 saat sonra hâlâ
`evaluated < 20` ise soğuk-önbellek açıklaması düşer ve gerçek bir gerileme aranmalıdır.

**YAN NOT:** `warmup_scale.json`ın son yazımı 11:15Z, yani 11:48'deki dağıtımdan ÖNCE.
`warmup_merdiven_kilitli` telemetrisi henüz canlıda değil (commit edildi, dağıtılmadı) —
kilit sayacı ilk değerini dağıtımdan sonraki ilk ısınma koşumunda alacak.
