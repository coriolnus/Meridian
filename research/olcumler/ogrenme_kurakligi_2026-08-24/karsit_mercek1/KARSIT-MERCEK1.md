# KARŞIT · MERCEK 1 — "KUSUR VAR" İDDİASININ ÇÜRÜTÜLMESİ (2026-08-24)

Kapsam: TESHIS.md'nin (a) YAPISAL ERİŞİLMEZLİK hükmü + (b) arama kısırlığı kanıt zinciri +
(c) sınıfının "çürütüldü" damgası. SALT OKUMA: canlıya/koda/git'e/state'e dokunulmadı.

## HÜKÜM

**Kusur DOĞRULANMADI.** Teşhisin birincil sınıfı (a) yanlış nüfus üzerinde ölçülmüş; kapı
erişilebilir, 2026-08-14'te fiilen GEÇİLDİ, ve `cleared: 0` bugün bir hatanın değil ölçülmüş bir
aşırı-ship kusurunun onarılmış hâlinin sonucudur.

---

## 1. "n=37, maks P=0,799" — YANLIŞ NÜFUS (kanıt)

Teşhis iki "bağımsız kanal" saydı: `arming_measured` olayları (106) + 2026-08-13 tarihli bir belge.
`arming_measured` **arama kapısı değildir** — `meridian/arming.py:374`, canlı KURULUM silahlandırma
organı (`advance_once` içinde, tur başına 27-100 dk; arming.py:41-45 ölçüm dökümü). Parametre
arama kapısının KENDİ defteri `state/hypotheses.jsonl`in `backtest.search_p` alanıdır ve hiç
okunmamış.

Canlı `state/hypotheses.jsonl` (60 satır) taraması:

```
toplam sayısal search_p: 30   maks: 0.941
p>=0.80: 3   p>=0.90: 3   p>=0.975: 0
0.941  gerekli 0.89  K=10  2026-07-20  entry.w_prox           status=superseded   (v2→v3 SHIP)
0.9295 gerekli 0.80  K=1   2026-08-14  position_size_r@chop   status=rejected_by_backtest
0.909  gerekli 0.89  K=10  2026-07-21  exit.breakeven_r       status=rejected_by_confirmation
0.799  gerekli 0.80  K=1   2026-07-22  entry.w_rs             status=rejected_by_backtest
```

⇒ "sistemin ölçtüğü tüm güven değerlerinin maksimumu 0,799" iddiası **FALS**. Doğrusu 0,941.

## 2. KAPI 10 GÜN ÖNCE GEÇİLDİ — VE BAĞLAYAN TERİM K DEĞİLDİ

`H00057`, 2026-08-14T08:40:11, `position_size_r@chop 0.5→0.6`:
```
search_p = 0.9295   search_p_required = 0.80   k_probes = 1   →  OLASILIK KAPISI GEÇTİ
fold_wins = "0/2"   tail_ok = true
reject_reasons = ["aday/incumbent OOS skoru TANIMSIZ (min_sample altı) —
                  ölçülmemiş aday ship edilemez"]
```
Aday, P eşiğini **0,13 farkla aşarak** geçti ve BAŞKA bir terimden (örneklem yeterliliği +
fold çoğunluğu) düştü. Bu, teşhisin kendi **H3** hipotezidir ("eşik bağlayıcı DEĞİL") ve teşhis
onu "ölçülemedi" diye kaydetmişti — defterde ölçülü duruyor.

## 3. SHIP YOLUNUN EŞİĞİ 0,975/0,995 DEĞİL, 0,80

`reflect.py:1325` (resmî ship kapısı, `record_erosion=True` olan TEK yol):
```
k_probes = int(proposal.get("probes_tested", 1) or 1)   # düşerse 1
passes, gate, why = _gate_eval(inc, cand, k_probes=k_probes, record_erosion=True)
```
Canlı defterde 2026-08 tarihli HER hipotezin kaydı `k_probes: 1, search_p_required: 0.8`.
0,975 (K=8) ve 0,995 (K=40) yalnız döngü-İÇİ ÖN ELEMEye (`reflect.py:2078`) aittir; hangi adayın
resmî kapıya taşınacağını seçer. "Gemi-yetkili kapı 0,995 istiyor" cümlesi iki ayrı kapıyı
birbirine karıştırıyor.

## 4. DÖNGÜ KAPANDI — TARİHSEL ÖRNEK VAR (soru b'nin cevabı)

- `state/strategy.yaml`: **version 5**. `state/history/`: v0001…v0005.
- `H00029` (`entry.w_prox None→0.15`) bu kapıdan geçti: `version_from 2 → version_to 3`, SHIP.
- R1 penceresinde incumbent OOS'un kendi serisi (`state/validation_ledger.jsonl`, 398 satır):
  `0.0853 (07-30) → 0.0589 (07-31) → 0.0845 (08-01) → 0.2687 (08-13) → 0.2687 (08-21)`.
  **08-13'te 3,2 katına çıktı.** "Sistem öğrenmiyor" cümlesi bu seriyle bağdaşmıyor.

## 5. ESKİ KAPI GEÇİRİYORDU — VE GEÇİRDİĞİ GÜRÜLTÜYDÜ

Bugünkü sıkılık bir kaza değil, ölçülmüş bir kusurun onarımı (`probgate.py:348-364`, kodun kendi
beyanı): eski formül `min(0.95, p_base + 0.01·(K−1))` K=16'da tavana çarpıp ORADA KALIYORDU;
"40 NULL adayda p neredeyse düzgün dağılıyor, %5'i 0.95'i geçiyor → aile-bazlı en az bir yanlış
geçiş olasılığı 1 − 0.95⁴⁰ = **%87**".

O gevşek kapıdan geçenlerin niteliği:
- `H00029` (SHIP oldu): `incumbent_oos = null`, `candidate_oos = null`, `fold_wins = "1/1"`,
  `search_mean_delta = **0.0016**`. Yani OOS skoru TANIMSIZ, tek fold, ortalama etki 0,0016 —
  ship edildi. Bugünkü yasada H00057'yi düşüren terim bunu da düşürürdü.
- `H00032` (0.909 ile ön elemeyi geçti): Search'te `0.0988 → 0.2119` (**+%114** nokta tahmini),
  sonra teyit diliminde `P(ΔS>0) = 0.140 < 0.70` ile REDDEDİLDİ.

⇒ Bugünkü `cleared: 0`, ölçülmüş bir aşırı-ship kusurunun onarılmasının DOĞRUDAN ve AMAÇLANAN
sonucudur. Kapı bozuk değil; kapı çalışıyor.

## 6. (c) SINIFI "ÇÜRÜTÜLDÜ" DEĞİL — AKSİNE DESTEKLENDİ (soru c)

Teşhisin tek karşı-kanıtı: 2026-08-21, `entry.w_turnover 0.15`, `cand_oos 0.2823 > inc_oos 0.2687`
(+%5,1), `passes=False`.

(i) **Ölçek**: H00032 aynı kapıda **+%114**'lük bir nokta tahminiyle geldi ve teyit diliminde
P=0,140 çıktı. +%5,1 bu gürültü bandının çok içindedir. Nokta tahmininde incumbent'ı geçmek
"edge" değildir — kapının var oluş sebebi tam olarak bu ayrımdır.

(ii) **Teşhisin kendi sayısı ters okunmuş**: "387 sondanın 141'i (%36,4) incumbent'ı geçiyor"
denilmiş ve bu (c)'yi çürüttüğü söylenmiş. Tersi: incumbent komşuluğunda RASTGELE bir noktada
olsaydı ~%50 beklenirdi. Binom sınaması: p̂ = 0,3644, n = 387, H0: p = 0,5 →
**z = −5,34, tek yönlü p ≈ 4,7 × 10⁻⁸**. Yani incumbent kendi komşuluğunun medyanının
İSTATİSTİKSEL OLARAK ANLAMLI biçimde ÜSTÜNDE. Bu sayı yerel-optimalliğin LEHİNE kanıttır.

(iii) **0,409 kötü bir sayı değil**: `score.score_detail` bileşiği
`clip(0.5·ret_c + 0.3·dd_c + 0.2·sharpe_c)`, aralık [−1, +1] (`score._clip` varsayılanı);
hedefler `target_return_30d 0.07 · max_drawdown 0.16 · min_sharpe 1.2`. Sistemin bugüne kadar
kaydettiği incumbent OOS değerleri: 0,0589 · 0,0845 · 0,0853 · 0,0988 · 0,1509 · 0,1963 · 0,2687.
Sprint'in 0,409'u (kendi kaydırılmış penceresinde) **kaydedilmiş en yüksek değerdir**. Üstelik R1
incumbent'ı 8 gün önce (08-13) 3,2 katına çıkarılmıştı — TAZE yükseltilmiş bir incumbent'ı tek
düğmelik ±k·adım komşulukla 8 gün sonra yenememek beklenen sonuçtur, arıza değil.

## 7. (a) "AYNI 40 ADAY" — İDDİA DOĞRU AMA TEŞHİSİN KANITI ÇÜRÜK (soru a)

Doğruluk tarafı: liste koddan TÜRETİLEBİLİR biçimde deterministiktir —
`_ucb_rank` ("no wall-clock/random", ad ile eşitlik bozma), `_default_windows()` DONMUŞ sabitler
(`dataset.IS_START 2022-01-01 · OOS_START 2024-01-01 · OOS_END 2026-04-30 · HOLDOUT_END 2026-07-30`),
ısınma `record_session=False` ile koştuğu için `hypotheses.jsonl`e YAZMAZ ⇒ `hyps` donuk ⇒ sıralama
donuk. Teşhis bu yolu HİÇ kullanmadı.

Kanıt tarafı ÇÜRÜK: teşhis "probe_cache.json 08-21'den beri yazılmadı ⇒ 40 sondanın TAMAMI
önbellekte" dedi. Dosya okundu:
```
state/probe_cache.json → {"rev": 1787344310, "entries": { … }}   entries UZUNLUĞU = 1
PROBE_DISK_CAP = 300 (reflect.py:1531)  → tavan bağlamıyor
state/wf_cache_rev.json rev = 1787344310 (EŞLEŞİYOR → dosya geçerli, yok sayılmıyor)
```
Diskteki sonda önbelleğinde **TEK** kayıt var. 40 sondanın "tamamı önbellekte hazır" iddiası bu
dosyadan çıkarılamaz; en fazla 1'i çıkar. Sonuç tesadüfen başka bir kanıtla ayakta duruyor
(79 sn/koşum × tek `walk_forward` = yerelde 12,1 dk / canlıda 27-100 dk, `arming.py:41-45`), ama
teşhisin YAZDIĞI zincir bu sonucu taşımıyor.

## 8. MALİYET ÇERÇEVESİ ABARTILI

Teşhisin kendi sayıları: `CPUUsageNSec` = 22,37 CPU-saat / 7,03 gün, makine 4 çekirdek
⇒ **makinenin %3,3'ü** (bir çekirdeğin %13,3'ü) ve bu BİRİMİN TAMAMI, yalnız ısınma değil.
Duvar-saati ~79 sn/saat = **%2,2 görev döngüsü**. Ayrıca ısınmanın sözleşmesi zaten
"Nothing ships" (`record_session=False`) — ship edemeyen bir işin `cleared` sayısına bakıp
"sistem öğrenmiyor" demek organ karışıklığıdır.

---

## ÇÜRÜTÜLEMEYENLER (dürüstlük şartı)

1. Yeni formül eski geçişleri geçirmezdi: 0,941 @ K=10 bugün 0,98 isterdi. Ön eleme GERÇEKTEN
   çok daha sıkı. Ama bu, ölçülmüş bir %87 yanlış-geçiş oranının onarımıdır — kusur değil.
2. `meridian-learn` süreci 2026-08-16 derlemesinde; `neden_dagilim`/`why` teşhis kanalı diskte
   var, süreçte yok. Bu bir DAĞITIM GECİKMESİdir, tasarım kusuru değil (S1 hâlâ geçerli).
3. `sprint_run.py:118` `cleared==0` iken izi boşaltıyor — gerçek bir gözlemlenebilirlik boşluğu,
   küçük ve yerel.
4. `warmup_scale` duvar kilidi (`carpan=1, duvar=1`) — davranışsal etkisi yalnız ship edemeyen
   bir ısınma işinin bütçesidir.
5. Sprint `note`'undaki "v1 yerel-optimal" cümlesi 6 sondaya dayanır; kapsamı ("bu veri diliminde")
   dürüst ama zayıf. Uydurma değil, az kanıtlı.

*Ölçen: karşıt mercek 1 (salt okuma). Hükmü Rol-1 işler; bu belge karta ve kill-list'e dokunmaz.*
