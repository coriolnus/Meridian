# HÜKÜM — "SİSTEM ÖĞRENMİYOR" TEŞHİSİ (Rol-1, 2026-08-24)

> **Manşet: TEŞHİS BÜYÜK ÖLÇÜDE ÇÜRÜDÜ. Sistem öğreniyor.**
> Karşıt doğrulama turu, üzerine hareket etseydim sistemi FİİLEN BOZACAK bir "düzeltmeden"
> kurtardı. Bu belge hem hükmü hem de dersi kaydeder.

## 0 · Nasıl başladı
Canlı triyajda `warmup_sprint` olayının her saat **birebir aynı** sayıları bastığı görüldü
(evaluated 40 · cleared 0 · best null). Buna üç mercekli bir teşhis + iki bağımsız şüpheci
akışı açıldı. Teşhis "kapı yapısal olarak erişilemez, `cleared:0` bir K ölçümüdür" dedi.

## 1 · ÇÜRÜYEN İDDİALAR (şüpheci-1, kanıtla)

### 1.1 ÖLDÜRÜCÜ: İKİ AYRI KAPI BİRBİRİNE KARIŞTIRILDI
| kapı | yer | K | eşik | ship yetkisi |
|---|---|---|---|---|
| **RESMÎ SHIP KAPISI** | `reflect.py:1325` | `proposal["probes_tested"]` → pratikte **1** | **0,80** | **EVET** (`record_erosion=True`, tek yol) |
| döngü-içi ÖN ELEME | `reflect.py:2078` | `total` (planlanan sonda = 40) | 0,995 | HAYIR (`record_erosion=False`) |

Teşhisin "gemi-yetkili kapı 0,995 istiyor" cümlesi **yanlıştır**. 0,995 yalnız hangi adayın
resmî kapıya taşınacağını seçen ön elemeye aittir. Doğrulandı: kaynaktan okundu.

### 1.2 "Ölçülen en yüksek P = 0,799" — YANLIŞ NÜFUS
Teşhis `arming_measured` olaylarını saydı; o, arama kapısı DEĞİL **canlı kurulum silahlandırma
organıdır** (`arming.py:374`). Arama kapısının kendi defteri `state/hypotheses.jsonl` →
`backtest.search_p` ve hiç okunmamış. Gerçek: 30 sayısal `search_p`, **maks 0,941**.

### 1.3 KAPI ON GÜN ÖNCE GEÇİLDİ — ve bağlayan terim K DEĞİLDİ
`H00057` (2026-08-14): `search_p 0,9295` vs gerekli `0,80`, `k_probes=1` → **olasılık kapısı
GEÇTİ**. Düştüğü yer başkaydı: _"aday/incumbent OOS skoru TANIMSIZ (min_sample altı)"_.
Ayrıca `H00029` (2026-07-20, p=0,941, gerekli 0,89, K=10) → **SHIP oldu, v2→v3.**

### 1.4 DÖNGÜ KAPANMIŞ — tarihsel kanıt var
`strategy.yaml` **version 5**; `state/history/` v0001…v0005. Incumbent OOS serisi
(`validation_ledger.jsonl`): 0,0853 → 0,0589 → 0,0845 → **0,2687** (08-13'te 3,2 katı).
"Sistem öğrenmiyor" cümlesi bu seriyle bağdaşmıyor.

### 1.5 BUGÜNKÜ SIKILIK BİR KAZA DEĞİL, ÖLÇÜLMÜŞ BİR KUSURUN ONARIMI
Eski formül (`min(0,95, p_base + 0,01·(K−1))`) K=16'da tavana çarpıp orada kalıyordu; kodun kendi
beyanı: 40 NULL adayda **aile-bazlı en az bir yanlış geçiş olasılığı %87**. O gevşek kapıdan
geçenlerin niteliği: `H00029` ship edildi ve `incumbent_oos = null`, `candidate_oos = null`,
tek fold, ortalama etki **0,0016**. Bugünkü yasa onu da düşürürdü.

**⇒ Bugünkü `cleared: 0`, amaçlanan sonuçtur. Kapı bozuk değil; kapı çalışıyor.**

### 1.6 Tek karşı-kanıt (aday +%5,1) gürültü bandında
`H00032` aynı kapıya **+%114**'lük bir nokta tahminiyle gelmiş, teyit diliminde `P=0,140` çıkmıştı.
Nokta tahmininde incumbent'ı geçmek "edge" değildir — kapının varlık nedeni tam olarak bu ayrımdır.

## 2 · AYAKTA KALANLAR (ikisi de gerçek, ikisi de TELEMETRİ kusuru — öğrenme kusuru DEĞİL)

**(A) Ön elemede K enflasyonu GERÇEK.** `k_probes = len(planned)` ve önbellekten BEDAVA gelen
sondalar da K'ya sayılıyor. Isınmanın beyan edilmiş görevi ("önbelleği ısıt") başarıldıkça K
10→20→30→40 tırmanıyor, ön eleme eşiği 0,980→0,995'e çıkıyor. Kanıt: aynı aday
(`exit.trail_atr_mult`) 08-08 ve 08-11'de K=10'da temizlendi, K=20/30/40'ta temizlenemedi —
iki bağımsız gece, arada başka değişiklik yok.
**Sonucu**: saatlik `cleared:0` satırı ön eleme istatistiği olarak bilgi taşımıyor.
**Sonucu DEĞİL**: öğrenmenin durması — ship kapısı ayrı ve 0,80.

**(B) `meridian-learn` YEDİ GÜNDÜR BAYAT BYTECODE KOŞUYORDU.** `ExecMainStartTimestamp`
2026-08-16 23:27; reddin gerekçesini basan kod (`neden_dagilim`/`why`) 2026-08-23'te dağıtıldı.
262 `warmup_sprint` olayının SIFIRI o alanı taşıyor. Düzeltme diskteydi, süreçte değildi.
**→ BU GECE DÜZELTİLDİ**: birim yeniden başlatıldı (2026-08-24T00:34:40Z, yeni PID 432366,
active/running; 7 günde 22s 23dk CPU yakmıştı). `learn_run` emir yolunda DEĞİL — saf hesap
süreci (Ö-50 yerleşim değişikliği), o yüzden restart güvenliydi.

**(C) `warmup_scale.json` ölü kilit.** `{carpan:1, duvar:1}`; büyüme dalı `carpan < min(duvar,8)`
→ `1 < 1` = False. Duvarı temizleyen yol YOK, 16 gündür `warmup_budget_scaled` hiç basılmadı.
Kilit şu an kapıyı GEVŞETEN yönde çalışıyor (K'yı 40'ta tutuyor, 80'e çıkarmıyor).

**(D) `sprint_run.py:118` reddin gerekçesini YAPISAL OLARAK siliyor:**
`"trace": [t for t in trace if t.get("passes")][:6]` — `cleared==0` iken tanım gereği `[]`.
Yani "kapı ölçemedi" / "aday kötü" / "aday atıl" hükümleri ayırt edilemiyor.

## 3 · NE YAPILMADI VE NEDEN
**Eşik İNDİRİLMEDİ.** Teşhis üzerine hareket etseydim `p_base`'i düşürecektim — ve §1.5'in
ölçtüğü **%87 aile-bazlı yanlış geçiş** oranını geri getirecektim. Yani "öğrenmeyi açan"
düzeltme, sistemi ölçülmüş biçimde bozacaktı. Karşıt doğrulama bunu durdurdu.

Eşikle ilgili herhangi bir değişiklik **strateji kimliğini** değiştirir; taban yeniden dondurma
ve ön-kayıt kartı gerektirir. Bu gece yapılmadı ve yapılmamalıydı.

## 4 · AÇIK KALEMLER (yeni)
| # | kalem | sınıf |
|---|---|---|
| L1 | (A) K enflasyonu: ön eleme istatistiği bilgisiz. Düzeltme adayı — önbellek isabetlerini K'ya saymamak. **Ön-kayıt kartı gerekir** (eşik davranışını değiştirir) | telemetri + eşik |
| L2 | (C) `warmup_scale` ölü kilidi (`1 < 1`). Saf mantık hatası, eşik değiştirmez | hata |
| L3 | (D) `sprint_run.py:118` iz süzgeci reddin gerekçesini siliyor. YASA 6 sınıfı | gözlemlenebilirlik |
| L4 | (B)'nin doğrulanması: restart sonrası ilk `warmup_sprint` olayı `neden_dagilim` taşıyor mu? | doğrulama |

## 5 · DERS (kaydedilsin)
1. **Bir sistemin iki kapısı varsa, hangisinin ship yetkisi olduğunu ÖNCE ölç.** Teşhisin
   tamamı bu tek karışıklığın üstüne kurulmuştu.
2. **"En yüksek ölçülen değer" iddiası, hangi defterden okunduğu söylenmeden yapılamaz.**
   Yanlış defter (`arming_measured`) 0,799 dedi; doğru defter (`hypotheses.jsonl`) 0,941.
3. **Sıkı bir kapı ile bozuk bir kapı aynı şey değildir.** `cleared:0` bir onarımın sonucu
   olabilir; kodun kendi beyanı bunu yazıyordu ve teşhis okumadı.
4. **Karşıt doğrulama bu gece kendini ödedi.** Tek bir "makul" teşhis üzerine hareket etmek,
   ölçülmüş bir kusuru geri getirecekti.
