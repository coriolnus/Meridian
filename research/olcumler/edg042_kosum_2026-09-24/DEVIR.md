# DEVİR — EDG-2026-042 HAFTALIK KOŞUM #5 — TELAFİ (2026-09-24)

**Hüküm işleme Rol-1'dedir.** Bu koşum bir ÖLÇÜM OTURUMUdur (ajan, telafi): git komutu
koşulmadı (salt-okur dahil), karta ve ROADMAP'e YAZILMADI, dağıtım yapılmadı. Aşağıdaki metinler
HAZIR ÖNERİdir; işlenene kadar **açık kalem**dir (CLAUDE.md §5: işlenmemiş hüküm açık kalemdir).

**NEDEN TELAFİ:** zamanlanmış görev iki haftadır ölçüm üretmedi — 09-12 haftalık kullanım
limitine takıldı (10 s'de düştü), 09-19 Mac uykuya geçince yanıt ortasında öldü (görev listesi
"succeeded" diyor ama `research/olcumler/` altında 09-19 dizini YOK). Kıyas tabanı bu koşumda
**#4 (2026-09-05)** — aşağıdaki değişim tablosu **HAFTALIK DEĞİL, ÜÇ HAFTALIK** (19 takvim günü).

- Çalışma dizini: `.claude/worktrees/edg042` (ana checkout DEĞİL, aynı HEAD: main 101fa435)
- Artefakt dizini: `research/olcumler/edg042_kosum_2026-09-24/`
- Canlı snapshot: `canli_ham.json` sha256 `3cc2bfe1bc224b71b38ef171a75723b1e111d735bfba85c197dc9f96a0a1fe12`, çekim **2026-09-24T21:00:05Z**, A1
- Reçete: R3/AYRIK `edg042_recete_ayrik_2026-08-31/` (kart işaretçisi) — bayt-özdeş, sha ✓
- Hakem: H2 `edg042_hakem_2026-09-01/` (kart işaretçisi) — sha kıyaslandı, ayrışma YOK
- Doğrulama: **BU KOŞUMDA ATLANDI** (brief farkı #3 — telafi koşumu, kod/kart değişmedi;
  kapsam testleri + `codelaw` KOŞULMADI, `DOGRULAMA.txt` bu dizinde YOK — bkz. §5 açık kalem (b))

## 1. Kova tablosu

| Kova | n | seans | eşik (n/seans) | eşik dolu? | medyan bps | p25 / p75 | min / maks | en büyük seans payı | damga |
|---|---|---|---|---|---|---|---|---|---|
| `giris_once` (K1-önce) | 15 | 5 | 30 / 10 | **hayır — eşik BEKLEMEZ (kalıcı taban)** | +16,131 | −26,397 / +67,659 | −130,739 / +327,46 | %33,3 | ÖLÇÜLEMEDİ (n=15 < 30) — betimleyici |
| `giris_1345` (K1-1345) | 18 | 12 | 30 / 10 | hayır (**seans DOLDU**, n bağlayıcı) | +22,473 | −22,438 / +170,91 | −237,608 / +286,115 | %16,7 | ÖLÇÜLEMEDİ (n=18 < 30) — betimleyici |
| `cikis_hedef` (K2) | 14 | 5 | 15 / 6 | **hayır — EN YAKIN kova** (1 dolum + 1 seans eksik) | −4,21 | −36,282 / +108,299 | −538,4 / +824,164 | %35,7 (kill#7 şerhi artık gerekmiyor) | ÖLÇÜLEMEDİ (n=14 < 15) — betimleyici |
| `cikis_stop` (K3) | 11 | 8 | 15 / 6 | hayır (**seans DOLDU**, n bağlayıcı) | +2,496 | −4,365 / +13,444 | −120,812 / +125,739 | %27,3 | ÖLÇÜLEMEDİ (n=11 < 15) — betimleyici |

`olculemedi` her üç kovada **0**. Model varsayımı (goal.slippage_bps) = **5** — koşum günü künyesi.

**HÜKÜMLÜ KOŞUM TETİKLENMEDİ · CI HESAPLANMADI · KARAR KURALI UYGULANMADI · `status: measuring` KALIR.**

## 2. Önceki gerçek koşuma göre değişim (#4 2026-09-05 → #5 2026-09-24, **ÜÇ HAFTA**, telafi nedeniyle)

| Kova | n | seans | medyan bps |
|---|---|---|---|
| `giris_once` | 15 → **15** (donuk kol, beklenen) | 5 → 5 | +16,131 → **+16,131** (birebir) |
| `giris_1345` | 8 → **18** (+10) | 5 → 12 (+7) | +12,476 → **+22,473** |
| `cikis_hedef` | 6 → **14** (+8) | 2 → 5 (+3) | −4,21 → −4,21 (birebir — **yuvarlama tesadüfü**, aşağıda not) |
| `cikis_stop` | 7 → **11** (+4) | 6 → 8 (+2) | +2,496 → **+2,496** (birebir) |

`giris_once` yine BİREBİR sabit — P-3 hükmünün (kol 2026-08-23'te emekli oldu) üçüncü ardışık
doğrulaması.

**`giris_1345` medyanı +12,5 → +22,5 (yükseliş, hüküm DEĞİL).** On yeni satırın dağılımı vahşi
kalıyor: iki büyük pozitif uç (AMD 09-21 +158,3 · META 09-21 +217,4), bir büyük negatif (MU 09-04
−237,6), geri kalanı modele yakın/altında. Örneklem hâlâ eşiğin (30) altında; n=18/seans=12 —
**seans eşiği (10) bu koşumda ilk kez doldu**, bağlayıcı kısıt artık yalnız n (12 dolum eksik).

**`cikis_hedef` medyanı tesadüfen BİREBİR aynı (−4,21).** Doğrulandı (elle, uydurma değil): n=6
listesinde sıralı 3./4. (medyan çifti) değerler −4,728 ve −3,691 idi; n=14 listesinde sıralı 7./8.
değerler HÂLÂ aynı ikili — ortanca değişmedi. Bu kova **eşiğe en yakın**: yalnız 1 dolum + 1 seans
eksik; kill#7 tek-seans şerhi bu koşumda artık ZORUNLU DEĞİL (%66,7 → %35,7, örneklem büyüyünce
yoğunlaşma dağıldı — betimleyici gözlem, hüküm değil).

`cikis_stop`'ta seans eşiği (6) zaten #4'te dolmuştu, bu koşumda seans 6→8'e çıktı; medyan
BİREBİR sabit kaldı (+2,496), bağlayıcı kısıt hâlâ n (4 dolum eksik).

## 3. Eşiğe kalan mesafe (KABA İZDÜŞÜM — ÖLÇÜM DEĞİL, birikim hızı varsayımı; pencere 3 hafta)

| Kova | eksik n | eksik seans | bu 3-haftalık pencerenin hızı | izdüşüm |
|---|---|---|---|---|
| `giris_1345` | 12 | 0 (doldu) | 10 dolum / ~2,71 hafta ≈ 3,7 dolum/hafta (10/7 seans ≈ 1,43 dolum/seans) | bu hızla ~3,3 hafta (≈2026-10-18); kartın 08-31'de ölçtüğü DAHA YAVAŞ 0,40 dolum/seans tabanıyla ~12 hafta (≈2026-12-17) — bant İKİ UÇLU, tek pencereden hızlanma mı gürültü mü ayırt edilemez |
| `cikis_hedef` | **1** | **1** | 8 dolum / 2,71 hafta ≈ 3,0 dolum/hafta | **EN YAKIN** — bu hızla <1 hafta; ama tek-dolumluk mesafede bant hesabı anlamsız, sadece "sıradaki normal haftalık koşumda dolabilir" beyanı verilir (uydurma yasağı: kesin tarih İDDİA EDİLMEZ) |
| `cikis_stop` | 4 | 0 (doldu) | 4 dolum / 2,71 hafta ≈ 1,5 dolum/hafta | ~2,7 hafta (≈2026-10-15) |

UYARI: bu pencere İKİ ATLANMIŞ KOŞUMU KAPSIYOR — "hız" burada üç haftalık birikim/3 ile
yaklaşıklanmıştır, haftalık gerçek dağılım (hangi hafta ne kadar geldiği) bu ölçümle GÖRÜLEMEZ.
Bant bu yüzden geniş tutulmuştur.

## 4. Pencere hakem katmanı (EXE-2026-009 — bu kartın hükmü DEĞİL)

- Betikler işaretçi sha256'larıyla kıyaslandı: **ayrışma yok**, koşuldu (`pencere_ham.json`
  çekim 2026-09-24T21:01:00Z).
- **İLK KEZ HER İKİ KOL DA n≥10** (alt_bant_n_esik=10) — önceki dört koşumun hepsinde
  `giris_1345 < 10` olduğu için tetik hiç DEĞERLENDİRİLEMEMİŞTİ ("orneklem_birikimde"); bu
  koşumda gerçekten hesaplandı:
  - `giris_once` n=15 / 5 seans → CI **[−43,038 ; +80,699]**
  - `giris_1345` n=18 / 12 seans → CI **[−38,455 ; +175,107]**
  - (B=5000, seed=20260812, kümeleme=seans — kartın donuk künyesi)
- damga↔ts çaprazı: kıyaslanan **20** · damgasız 13 · damga_bilinmeyen **0** · AYRIŞAN **0**.
- `oneri_tetigi` = **`tetiklenmedi`** — iki kolun CI'ları yüksek yönde AYRIK değil, geniş
  örtüşüyorlar (`giris_1345` alt sınırı −38,455 < `giris_once` üst sınırı +80,699).
  **`geri_al_onerisi` beyanı YOKTUR.**

## 5. Açık kalemler

**(a) TAŞINAN (koşum #4'ten, operatör kararı bekliyor) — `giris_1345` VRTX çift-satır:**

```
P-2026-09-02-VRTX      ts=2026-09-03T13:45:01Z  fill=556,94  bps=−38,455
P-2026-09-02-VRTX-pead ts=2026-09-03T13:45:02Z  fill=556,94  bps=−38,455
```

İki AYRI plan (temel + `pead` ailesi), AYNI ticker, AYNI dolum fiyatı; ertesi gün ikincisi
`armed_dropped_already_open` ile düşüyor — pozisyon tekil, gönderim izi çift. Kartın kill#5'i
yalnız kovalar ARASI birleştirmeyi yasaklar, kova İÇİ bağımlı gözlemin kuralı YOKTUR. Reçete
AYNEN koşuldu, sayı DÜZELTİLMEDİ. ETKİ (beyan, hüküm değil): tekilleştirilseydi `giris_1345`
n=18→17; eşik hükmü DEĞİŞMEZ (17 de 30'un altında). Bu koşumda YENİ bir örneği doğmadı — aynı
2026-09-02 çifti hâlâ tekil kayıt.

**(b) YENİ — bu koşumda [6] atlandı, `DOGRULAMA.txt` YOK:** brief kararı (telafi koşumu, kod/kart
değişmedi) gereği kapsam testleri (`test_kart_kimlik_v219` · `test_kart_hukum_damgasi_v251` ·
`test_nous_eval_v131` · `test_wpm_sasi_v173`) ve `codelaw` raporu bu dizinde ÜRETİLMEDİ. Bu
KALICI bir emeklilik DEĞİLDİR — sıradaki NORMAL haftalık koşum [6]'yı normal şekilde çalıştırmalı.
Kayıt amaçlı; operatör/Rol-1 kararı gerektirmiyor.

## 6. Karta işlenmesi ÖNERİLEN blok (Rol-1 işler; ölçüm oturumu karta YAZMADI)

`research/cards/EDG-2026-042-gercek-friksiyon-tahmini.yaml` sonuna, yeni anahtar:

```yaml
hafta_kosum_5_2026_09_24_telafi: >
  HAFTALIK KOŞUM #5 — TELAFİ (zamanlanmış görev `edg042-friksiyon-haftalik`, ölçüm oturumu/ajan;
  Rol-1 işledi). NEDEN TELAFİ: görev iki hafta üst üste ölçüm üretemedi — 09-12 haftalık kullanım
  limitine takıldı, 09-19 Mac uykuya geçince yanıt ortasında öldü (görev listesi succeeded dedi,
  dizin YOK). Kıyas tabanı #4 (2026-09-05) — DEĞİŞİM ÜÇ HAFTALIK, haftalık değil.
  Artefakt: research/olcumler/edg042_kosum_2026-09-24/ (snapshot sha 3cc2bfe1…, çekim
  2026-09-24T21:00:05Z, goal.slippage_bps=5 künyeli). Reçete R3/AYRIK (kart işaretçisi), betikler
  bayt-özdeş (a846449e… / 1787a9ff…). Salt-okunur; canlıya ve state/'e tek bayt yazılmadı.
  SONUÇ — DÖRT KOVA DA EŞİK ALTINDA, BETİMLEYİCİ, CI yok, karar kuralı uygulanmadı, status
  measuring:
    giris_once  n=15 / 5 seans  · medyan +16,131 · seans payı %33,3 (KALICI TABAN — #4'e göre
                BİREBİR sabit, üçüncü ardışık doğrulama)
    giris_1345  n=18 / 12 seans · medyan +22,473 · p25/p75 −22,438/+170,91 · seans payı %16,7 ·
                SEANS EŞİĞİ (10) BU KOŞUMDA DOLDU, n bağlayıcı (12 dolum eksik)
    cikis_hedef n=14 / 5 seans  · medyan −4,21 (yuvarlama tesadüfü #4 ile — elle doğrulandı) ·
                seans payı %35,7 (kill#7 şerhi artık GEREKMİYOR, #4'te %66,7 idi) · EŞİĞE EN
                YAKIN kova: 1 dolum + 1 seans eksik
    cikis_stop  n=11 / 8 seans  · medyan +2,496 (birebir #4 ile) · seans payı %27,3 · seans
                eşiği zaten doluydu, n bağlayıcı (4 dolum eksik)
    olculemedi 0 (üç kovada da) · kill denetimi sekizde sekiz temiz (KOMUT.txt [4]).
  EK hakem (EXE-2026-009, H2/ts) — İLK KEZ HER İKİ KOL DA n≥10, öneri tetiği GERÇEKTEN
  DEĞERLENDİRİLDİ (önceki dört koşumda hep orneklem_birikimde idi): giris_once n=15 CI
  [−43,038 ; +80,699] · giris_1345 n=18 CI [−38,455 ; +175,107] · damga↔ts ayrışan 0 ·
  oneri_tetigi = tetiklenmedi (CI'lar yüksek yönde ayrık değil, geniş örtüşüyor) ·
  geri_al_onerisi YOK.
  TAŞINAN AÇIK KALEM (P-3 kardeşi, değişmedi): giris_1345'te 2026-09-02 VRTX iki satırla temsil
  ediliyor (temel + pead, aynı fill/bps) — kova İÇİ bağımlı gözlem kuralı kartta YOK, sayı
  düzeltilmedi, tekilleştirilseydi n=18→17 (eşik hükmü değişmez). OPERATÖR KALEMİ.
  YENİ KAYIT (kalıcı emeklilik DEĞİL): bu koşumda [6] doğrulama adımı (kapsam testleri +
  codelaw) brief kararıyla ATLANDI (telafi, kod/kart değişmedi) — sıradaki normal haftalık koşum
  bunu normal şekilde çalıştırmalı.
```

## 7. ROADMAP satır önerileri (Rol-1 işler)

**Ö-54 / TSK-071 satırının (`ROADMAP.md:498` — Ö-54 ana not bloğu, en son `KOŞUM #4` ile biten
cümlenin ardına) eklenecek:**

> → 🔁 **KOŞUM #5 — TELAFİ, 2026-09-24 21:00Z** (`edg042_kosum_2026-09-24/`, snapshot `3cc2bfe1…`,
> R3/AYRIK; iki hafta atlandı — 09-12 limit, 09-19 uyku; kıyas #4'e karşı ÜÇ HAFTALIK): dört kova
> da EŞİK ALTINDA → hükümlü koşum tetiklenmedi, CI yok, `status: measuring`.
> `giris_once` **n=15 BİREBİR sabit** (üçüncü ardışık doğrulama) ·
> **`giris_1345` n=8→18, seans 5→12 — SEANS EŞİĞİ DOLDU** (medyan +12,5→+22,5, yükseliş hüküm
> DEĞİL; bağlayıcı yalnız n, 12 eksik ≈3,3-12 hafta bandı) ·
> **`cikis_hedef` n=6→14, seans 2→5 — EŞİĞE EN YAKIN** (1 dolum + 1 seans eksik; kill#7 şerhi
> artık gerekmiyor, %66,7→%35,7) ·
> `cikis_stop` n=7→11, seans 6→8 (medyan birebir +2,496, bağlayıcı n, 4 eksik ≈2,7 hafta).
> Hakem (EXE-009/H2): **İLK KEZ HER İKİ KOL n≥10, tetik GERÇEKTEN değerlendirildi** →
> `tetiklenmedi` (CI'lar geniş örtüşüyor: giris_once [−43,0;+80,7], giris_1345 [−38,5;+175,1]),
> geri-al önerisi YOK, damga↔ts ayrışan 0.
> ⛔ **TAŞINAN AÇIK KALEM (P-3 kardeşi, değişmedi):** `giris_1345` 2026-09-02 VRTX'i hâlâ İKİ
> satır sayıyor (temel + `pead`) — operatör kararı bekliyor.
> **YENİ KAYIT:** bu telafi koşumunda [6] doğrulama (kapsam testleri + codelaw) brief kararıyla
> atlandı — kalıcı değil, sıradaki normal koşum çalıştırmalı.

**§7 (Ö-54 kronoloji defteri, `ROADMAP.md:3377` civarındaki `KOŞUM #4` satırının hemen ardına)
tek satırı:**

> - **2026-09-24 `EDG-2026-042` HAFTALIK KOŞUM #5 — TELAFİ (`Ö-54`):** iki atlanmış koşumdan
>   (09-12 limit, 09-19 uyku) sonraki ilk ölçüm; kıyas tabanı #4'e göre ÜÇ HAFTALIK. Dört kova da
>   eşik altında → hükümlü koşum TETİKLENMEDİ, `status: measuring` sürüyor. `giris_1345`
>   n=8→18 ve **seans eşiği (10) DOLDU** (bağlayıcı yalnız n, 12 eksik), `cikis_hedef` n=6→14
>   ile **eşiğe en yakın kova** (1+1 eksik, kill#7 şerhi artık gerekmiyor), `cikis_stop` n=7→11
>   (4 eksik), `giris_once` kalıcı taban üçüncü kez BİREBİR sabit. Hakem katmanı İLK KEZ her iki
>   kolda n≥10 ile GERÇEKTEN değerlendirildi: `tetiklenmedi`, geri-al önerisi yok. Taşınan açık
>   kalem (VRTX çift-satır, P-3 kardeşi) değişmedi. Bu koşumda [6] doğrulama adımı brief kararıyla
>   atlandı (kalıcı değil).

## 8. Görev durumu

Bitiş kontrolü (görev [1]): eşiğe ULAŞABİLEN üç kova (`giris_1345` · `cikis_hedef` ·
`cikis_stop`) **hükümlü verdict TAŞIMIYOR** → zamanlanmış görev **KAPANMAZ**. Normal haftalık
takvime dönülür (bir sonraki Cumartesi); bu koşum takvim-dışı bir telafiydi. `cikis_hedef`
eşiğe en yakın kova olduğu için sıradaki koşumda dolma ihtimali yüksektir (kesin tarih İDDİA
EDİLMEZ — uydurma yasağı).
